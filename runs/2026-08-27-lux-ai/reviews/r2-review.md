# r2 review — lux-ai

Range: `1c36d56..66b5d3b` (the five r1 fix commits) read at head
`66b5d3bb2c5c88d9b947437c1194f180681bc702` (`main`, unchanged since the r1 verdict —
`git status` clean, no new commit exists yet for round 2).
Files read: 31 (`src/lux/{replays,replay_runtime,sim,server,sim_config,sim_types,sim_state,resolve,micro,llm,decide}.nim`,
`replay-viewer/lux_replay.nim`, `replay-viewer/static_replay{,_worker}.js`,
`tests/{helpers,test_lux_replay,test_lux_engine,test_lux_directives,test_lux_resolve,test_lux_viewer}.nim`,
`tools/{wasm_replay_smoke.cjs,ci/renderer_fixture.html,ci/docker_smoke.sh}`,
`client/replay_broadcast.html`, `.github/workflows/ci.yml`, the five commit diffs, and on the
starter side `/workspace/starters/coworld-ctf/src/ctf/{replays,replay_runtime,sim,server}.nim`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (item 2 is the one at issue; items
1, 13, 14, 15 re-checked around the r1 fixes).

CI evidence: `gh run view 33090975748 -R Metta-AI/cogame-lux-ai --json headSha,conclusion` →
`headSha 66b5d3bb…`, conclusion **success**. Full log pulled (5 660 lines);
`grep 'SEAT-COUNT FAIL'` returns nothing.

**Method note.** Unlike round 1, this sandbox has a Nim 2.2.4 toolchain
(`/tmp/nim-2.2.4/bin/nim`) and the pinned dependency tree (`/tmp/nimdeps/*`), so B1 below is
**observed by execution against the real `src/lux` modules at this sha**, not inferred. The
repro program lives outside the repo (`/tmp/lobbyrepro.nim`, reproduced in the appendix); the
working tree was not modified.

---

## Blocking

### B1 — playback ignores the recorded lobby length: an episode whose seats connect later than tick 48 re-derives a **different game** (unchanged at head; this is the judge's standing B-J1)

- Where (playback):
  - `src/lux/replays.nim:119-131` — `simFromReplay` walks `data.joins` and sets
    `result.seats[seat].joined = true` (`:130`) **without reading `join.time`**.
  - `src/lux/sim.nim:162-173` — `step()`'s `Lobby` branch:
    ```nim
    of Lobby:
      let joined = sim.seats[0].joined and sim.seats[1].joined
      if (joined and sim.tickCount >= sim.config.startWaitTicks) or
          sim.tickCount >= sim.config.lobbyJoinTimeoutTicks:
        sim.beginPlaying()
        sim.stepPlaying()
    ```
    Playback calls `sim.step()` on every tick (`replays.nim:220-229`), so with both seats
    pre-marked joined the re-simulation always enters `Playing` at `startWaitTicks` = 48
    (`sim_config.nim:122`).
  - `src/lux/sim.nim:103-105` — `beginPlaying` returns early once `phase != Lobby`, so the
    recorded `InputStart` record (applied at `replays.nim:187-189`) is a no-op on a playback
    that already started.
- Where (live): `src/lux/server.nim:484-502` — the live loop never calls `sim.step()` in
  `Lobby`. It writes a lobby hash per tick (`:499`, the `mixHash(-1, tickCount)` form from
  `sim.nim:188-194`), and only when `joined and sim.tickCount >= config.startWaitTicks` does it
  write `InputStart` (`:496`) and `beginPlaying()` (`:497`). Live start tick
  `T = max(48, tick at which the later seat's socket appeared)`; `syncSeats`
  (`server.nim:358-372`) writes each join record at that tick.
- Observed, traced: for `T > 48` the recorded chain is lobby hashes for ticks `0..T-1` and
  world hashes from `T`; the playback chain is lobby hashes for `0..47` and world hashes from
  48. Tick 48 still matches (the hash is compared *before* the step, `replays.nim:225-228`, and
  the phase is still `Lobby` at that instant); tick 49 is the first mismatch. From then the
  playback world is `T-48` ticks ahead, and because `applyRecordsAt` installs directives **by
  recorded tick** (`replays.nim:170-197`), every directive lands `T-48` turns late.
- **Reproduced (executed, not inferred).** Recording the episode exactly the way
  `server.nim`'s loop records one (same order: syncSeats → join records → lobby hash → tick;
  then `InputStart` → directives → hash → step) and re-deriving it through the *shipped*
  `initReplayRuntime`/`advanceReplayFrame`:

  | seats connect at tick | live `Playing` began | playback `startTick` | `hashMismatchTick` | final cityTiles live → playback |
  |---|---|---|---|---|
  | 0  | 48  | 48 | **-1** | [18, 1] → [18, 1] |
  | 10 | 48  | 48 | **-1** | [18, 1] → [18, 1] |
  | 47 | 48  | 48 | **-1** | — |
  | 48 | 48  | 48 | **-1** | — |
  | **49** | 49 | 48 | **49** | — |
  | **120** | 120 | 48 | **49** | **[18, 1] → [17, 3]** |
  | 288 (the note's "typical 12 s") | 288 | 48 | **49** | — |
  | 10, one seat only (no-show) | 2400 (lobby timeout) | 2400 | **-1** | — |

  (360-turn `duel`, seed 42; the 18–1 live result is the same board CI's docker-smoke records —
  log line 2026: `replay summary ok: complete full_time [18, 1] 360 turns`.)
  The exact boundary is the **later seat's connect tick > 48**, i.e. > 2.0 s at
  `TargetFps = 24`. The no-show/timeout path re-derives correctly, because with a seat missing
  playback also waits out `lobbyJoinTimeoutTicks`.
- **The consequence is not just a warning.** With a 120-tick lobby (5 s) the recorded episode
  ends 18–1 for RED and the re-derived one ends **17–3**: different city counts, different
  endcard numbers, different per-turn board. The viewer is that re-derivation
  (`replay-viewer/lux_replay.nim:69-83` → `replay_runtime.nim:23-29` → the same
  `simFromReplay`/`stepReplay`), so a spectator watches a game that was never played, under
  `#mmwarn` (`client/replay_broadcast.html:1090`).
- **The information needed is in the bytes and is thrown away.** Decoding the recorded replay
  from the 120-tick run: `join player=0 time=8000 -> tickOfTime=120`,
  `join player=1 time=8000 -> tickOfTime=120`, and an `InputStart` input record at tick 120.
  `tickTime`/`tickOfTime` round-trip exactly at `ReplayFps = 15`
  (`replays.nim:86-89`, bitworld `replays.nim:81-83`).
- **Starter comparison — the defect is introduced in the fork, not inherited.**
  - coworld-ctf builds the playback sim with **no seats seated**:
    `/workspace/starters/coworld-ctf/src/ctf/replay_runtime.nim:22`
    (`result.sim = initSimServer(result.config)`), then walks the lobby from the record stream
    (`:33-37`).
  - Joins are re-applied **at their recorded time**:
    `/workspace/starters/coworld-ctf/src/ctf/replays.nim:383-390`
    (`while … data.joins[joinIndex].time <= time: … sim.addPlayer(...)`), called from
    `applyReplayEvents` (`:353`) inside `stepReplay` (`:506-517`).
  - The lobby machine lives **inside the sim step**, so live and playback run the identical
    code: `/workspace/starters/coworld-ctf/src/ctf/sim.nim:3996-3998` dispatches to
    `stepLobby` (`:3884-3903`), and the live server steps the sim on every tick including the
    lobby (`/workspace/starters/coworld-ctf/src/ctf/server.nim:2033`), writing joins at the
    live tick (`:1627-1632`).
  - lux-ai duplicated that machine instead of forking it: `sim.step`'s `Lobby` branch
    (`src/lux/sim.nim:162-173`) is reachable **only** from playback and the tests, while the
    live path has its own copy at `server.nim:484-502`. The two copies agree on the rule and
    disagree on the input (`joined` at construction vs `joined` at the recorded tick), which is
    exactly the divergence.
- Checklist item: **2 — Replay re-derivation.** "Replaying the recorded events through the sim
  reproduces the recorded per-tick state **frame by frame**, and the viewer derives its display
  from that same re-derivation." At this sha that holds only when both seats connect inside
  48 ticks.
- Why blocking: for the design note's own typical timing (§Decisions line 410: "lobby / connect
  wait (typical 12 s; cap `lobbyJoinTimeoutTicks` 2400)" — 12 s = tick 288) the property is
  false, and the failure is silent-but-visible: the hosted viewer shows a different match with
  a mismatch banner.
- Why nothing catches it: `tests/helpers.nim:22-27` sets `startWaitTicks = 0` for every
  fixture; `tests/test_lux_replay.nim:20-33` marks both seats joined, writes `InputStart` at
  tick 0 and calls `beginPlaying()` before the loop, so **no test ever records a non-zero
  lobby** (grep over `tests/`: every `initSimServer` call site either uses `fixtureConfig` or
  sets `joined` directly). `tools/ci/docker_smoke.sh:201-222` launches the player containers
  immediately after the game container, so CI's seats connect inside 2 s and its replay passes
  the hash gate (`Native <-> wasm hash gate`, run log 5446: `ok: loaded episode.replay,
  advanced 300 frames`).
- Judge's fix direction, quoted from `r1-verdict.md:74-79` (not my proposal): "make playback
  honor the recorded start — e.g. gate the `Lobby` auto-start on join **ticks** (apply `joined`
  at the recorded join tick in `simFromReplay`/`applyRecordsAt`) or suppress the auto-start
  when an `InputStart` record exists and start only when it is applied — plus a test that
  records a fixture with `startWaitTicks = 48` and joins at tick > 48 and asserts
  `hashMismatchTick == -1`."

---

## Non-blocking

### N1 — the `.tiny` five-line commander band is inert: `--lux-say-band` is substituted at `:root` with `--lux-note-lines: 4`

- Where: `client/replay_broadcast.html:1845-1866` (the `:root` block opens at :1845) (identical in `scripts/lux_block.html`, added
  by `e673713`).
  ```css
  :root { --lux-note-lines: 4;
          --lux-say-band: calc(var(--lux-note-lines) * 1.35 * var(--lux-note-size) * var(--u) + 18 * var(--u)); }
  #stage.tiny { --lux-note-line: 168; --lux-note-lines: 5; }   /* :1862 */
  #killfeed, #stage.tiny #killfeed { min-height: calc(3 * 20 * var(--u) + var(--lux-say-band)); }
  ```
- Observed (measured, headless chromium via the installed Playwright): a custom property is
  substituted at the computed-value time of the element it is *declared* on, so
  `--lux-say-band` inherits already resolved with `lines = 4`. Reducing the rule set to those
  four declarations and reading it back on `#killfeed` inside `#stage.tiny` gives
  `--lux-note-lines: "5"`, `--lux-say-band: "calc(4 * 1.35 * 7 * calc(1px * 1) + 18 * calc(1px * 1))"`,
  `min-height: 115.8px` — the four-line value. The comment at `:1860-1861` ("the same cap needs
  one more line there") describes an effect the CSS does not produce.
- Consequence, and why it is advisory: `min-height` is a *reservation*, not a clamp — the row
  still wraps to five lines and still fits. The head run's gate measures it:
  `360px: stage [116, 0, 245, 203]  band [144, 27, 239, 165] … 160 runes each`, `short 0`,
  `clipped 0`, `outside 0` (run 33090975748, step `The commander line fits its band`, log
  5525-5529). What is lost is only item 15's "the band is reserved whether or not anything is
  speaking, so the scene does not jump" — at `.tiny` the feed jumps by about one wrapped line
  when a full-cap note lands. Item 15's gated requirements (band sized from the server cap,
  fixture asserting full-length strings, CI step citing the measurement) are all satisfied at
  head, so this does not falsify the item.

### N2 — the load-time pre-scan re-simulates and hash-checks the whole episode, then discards the result

- Where: `src/lux/replays.nim:270-296`. `runScan` builds a **separate** player
  (`:279`, `var scanner = ReplayPlayer(data: player.data, maxTick: player.maxTick)`) and steps
  the episode with `scanner.stepReplay(sim)` (`:289`). `checkReplayHash` writes
  `hashValidationFailed`/`hashMismatchTick` onto `scanner`; nothing copies them to `player`.
  `scanner.mismatchQuit` is false (default), and `initReplayRuntime` sets
  `player.mismatchQuit` only **after** `initReplayPlayer` has run
  (`replay_runtime.nim:23` then `:28`).
- Consequence: a whole-episode integrity walk already happens at load, but `#mmwarn` /
  `lux_mismatch_tick` only light up once presentation playback reaches the divergent tick. In
  B1's case that is tick 49, i.e. a second in, so the practical loss is small. Not a checklist
  item.

### N3 — the node and browser gates hash-check a prefix of the replay; the full span is covered only by the native test

- Where: `.github/workflows/ci.yml:365` (`node tools/wasm_replay_smoke.cjs … 300`);
  `tools/wasm_replay_smoke.cjs:94-106` (300 × `lux_frame`, then one `lux_mismatch_tick` read).
- Observed by execution on an equivalent locally recorded `duel` replay: `maxTick = 408`
  (48 lobby + 360 turns + the settle tick), `startTick = 48`, `lullSpans = 0`; after 300 frames
  the sim is at tick **348** (turn 300), `mismatch = -1`. So ticks 349-408, including the
  settle tick, are outside the node gate; the browser soak in the head run reached
  `TURN 243 / 360` (log 5427). The whole span **is** covered natively by
  `tests/test_lux_replay.nim:65-100` (`replayCleanly` runs `while game.tickCount <
  player.maxTick` with `mismatchQuit = true` and asserts `hashMismatchTick == -1`), which is
  what item 2's "a test asserts it" names. Advisory; this is r1's fourth "could not determine",
  now quantified.

### N4 — `db780f6` changes 429 behaviour as well as 403 behaviour (matches the note; recorded so it is not re-filed)

- Where: `src/lux/llm.nim:83-84` (two candidates), `:86-94` (`tryNextBedrockModel`),
  `:181-187` (429 path).
- Observed: with a second candidate present, the **first** 429 now rotates
  haiku-4-5 → sonnet-4-5 and only a 429 with nothing left to rotate to sets
  `client.throttled` (which `decide.nim:266-271` reads as "skip the retry"). That is what the
  design note asks for ("`tryNextBedrockModel` on 401/403 'Model access is denied' **and on
  429**"), and every wait is still bounded by `attempt1Ms`/`retryMs`, so the item-5 arithmetic
  is untouched. Effort suppression is unaffected: the `output_config` branch is on the
  direct-Anthropic path only (`:146-158`, the guard at `:155`), and both ids contain `4-5` anyway.

### N5 — r1's advisory findings that were declined are unchanged at head (re-verified, not carried on the fixer's word)

- `episodeFinished`/`gameOverTicks` still unreferenced by the server: `grep -n episodeFinished
  src/lux/*.nim` → `sim.nim:184` only (r1 N3).
- The cart hand-off still runs before the night policy: `micro.nim:300-336` (`block handoff`,
  comment "Rule 4, evaluated BEFORE rules 2 and 3") precedes `:339-349` ("Rule 1: the night
  policy") (r1 N5).
- `build: "city"` still `continue`s the tile before any research check:
  `micro.nim:406-407` (r1 N6).
- The whole-reply cap is still applied in runes: `llm.nim:201-202` (r1 N13).
None of these moved, and none is on the checklist.

---

## Traced and consistent

**The r1 fix commits, re-read at head**

- `e673713` (item 15). The page still regenerates **byte-identically** from the starter mount —
  I ran `python3 scripts/fork_broadcast_page.py /workspace/starters/coworld-ctf /tmp/regen.html
  && cmp /tmp/regen.html client/replay_broadcast.html` → identical; `diff` of
  `client/chrome_common.js` and `client/broadcast_core.js` against the starter's → empty, so
  item 14's provenance is intact. The fixture's shim now goes **after** the script that assigns
  `window.LuxStaticReplay` (`tools/ci/renderer_fixture.html:358-363`, with a throw if the
  anchor disappears), `__luxFixtureFeed` throws when the page never took the shim (`:197-201`),
  the second frame is fed at stride 1 inside a try/reject (`:381-390`), and the measurement
  asserts its own strings (`:266-283`: `seat: FED.indexOf(text)`, `entry.runes !== NOTE_RUNES →
  short`, box vs `#stage` and the viewport, `scrollWidth/scrollHeight` vs the client box). The
  CI step parses `LUX-TEXTFIT` and fails on a missing measurement, `note_runes != 160`,
  `widths != 3 or notes < 6`, any `short`/`outside`/`clipped`, any `chrome_off_stage`, or any
  `failures[]` (`.github/workflows/ci.yml:402-446`); the head run prints
  `text fit: {"chrome_off_stage": 0, "chrome_outside": 1, "clipped": 0, "failures": [],
  "measured": 48, "note_runes": 160, "notes": 12, "outside": 0, "short": 0, "widths": 3}` and
  `commander band OK: 48 boxes measured, 12 full-cap notes inside #stage at 360/620/1280 px`
  (log 5525-5529). `tests/test_lux_viewer.nim:227-263` pins `--lux-note-runes: 160` to
  `MaxNoteRunes`, the `.feed-row.lux-say` rule and the CI step's existence.
- `db780f6` (r1 N2). Two-entry ladder at `llm.nim:83-84`; `BEDROCK_MODEL` still pins one
  (`:80-82`); `sonnet-4-6` still excluded, with the reason in the docstring. See N4 above for
  the one behavioural consequence.
- `7e8a89e` (r1 N14). `tests/test_lux_directives.nim:84-105`: the tautology is gone; the test
  now asserts `capped.runeLen == MaxReplyBytes`, `reason.startsWith("no JSON object in
  reply")` and `parse(survivor).stance == stFuel`. Strictly stronger.
- `27d10f6` (r1 N16). `tests/test_lux_engine.nim:31-58`: asserts the code's worst turn
  (`turnSpacingMs + attempt1Ms == 13000`, `> turnBudgetMs`), `36 × 13 = 468 s`,
  `468 + 3 + 100 + 20 < 660`, and the new overshoot bound
  `wallClockBudgetSeconds + worstTurnMs div 1000 <= 720`. Matches `decide.nim:146-238` and the
  top-of-loop stop at `server.nim:475`.
- `66b5d3b` (r1 N4). Every rule site now reads the config: `grep -n 'cargoCap(\|baseCooldown('
  src/` returns only world-aware calls (`micro.nim:315`, `resolve.nim:122,129,169,269,300,323`,
  `sim_state.nim:191`); the const forms in `sim_types.nim:193-197` survive only for two test
  helpers (`test_lux_micro.nim:39`, `test_lux_baselines.nim:40`). Defaults are seeded from the
  same constants (`sim_config.nim:99-100`, `:110-111`), so behaviour at shipped defaults is
  unchanged — corroborated independently: my locally recorded fast-join `duel` at seed 42 ends
  **18–1 in 360 turns**, the same board CI's docker-smoke records. Two new regression tests at
  `tests/test_lux_resolve.nim:388-431`.
- Item 1's second half: `git log -p 1c36d56..HEAD -- tests/` removes exactly three
  assertion-bearing lines (the `<=720` check, the `(recovered or true)` tautology and its
  scaffolding, and a `check` moved intact), each replaced by a stronger assertion. No `skip`,
  no `xfail`, no widened tolerance, no deleted test file (`grep -iE '^[-+].*(skip|xfail|
  disable|when false)'` over the same range → nothing).

**Record/playback mechanics that do hold**

- `replays.nim:102-110` writes one logical packet as consecutive one-byte input records and
  `applyRecordsAt` (`:179-194`) re-reads them positionally in 14-byte strides; at the start
  tick seat 0's stream is `[InputStart, InputDirective, …13 bytes]` and parses correctly in
  that order (verified by decoding a recorded fixture).
- `checkReplayHash` (`:199-218`) compares **before** the step, matching the writer's order
  (`server.nim:510-515`), and latches the first divergent tick only.
- The wall-clock stop rides the input stream and is applied by the one proc on both sides
  (`server.nim:476-480`, `replays.nim:190-191`, `sim.nim:127-136`);
  `tests/test_lux_replay.nim:102-109` re-derives it including the stop turn.
- `simFromReplay` correctly restores `name`/`slot` from the join records
  (`replays.nim:126-129`) and the chat records are re-applied into non-hashed fields only
  (`:133-168`).
- The wasm path is the same code, not a parallel recording: `lux_replay.nim:69-83` →
  `replay_runtime.nim:15-31` → `initReplayPlayer`/`simFromReplay`/`stepReplay`, with
  `lux_mismatch_tick` (`:124-128`) surfaced through `static_replay_worker.js:130,152,169` and
  `static_replay.js:159-173` into `#mmwarn`.
- No-show handling is consistent across the two lobby copies for the outcome that matters here:
  the live copy additionally marks `seats[].dead` and declares the failure
  (`server.nim:488-494`), and `dead` is used only by `decide.nim:182,193` and
  `results.deadSeats` (`sim.nim:497`) — it is not hashed, so its absence at playback does not
  affect re-derivation.

---

## Could not determine

- **Whether the `.tiny` band shortfall (N1) is visible as a feed jump in the shipped page.** My
  measurement was of a reduced four-declaration document, which isolates the substitution rule
  but not the page's own layout. What would settle it: read `--lux-say-band` off `#killfeed` in
  the fixture's 360 px iframe and compare it against the height of a rendered five-line note.
- **Whether `#viewpanel`'s removal is right for the `skirmish` 12×12 board** (r1's third open
  item). Now partly settled from the code: `BOARD_ASPECT` is derived per frame from the
  packet's `boardW/boardH` (`client/replay_broadcast.html:1417-1422`) and `relayout` fits the
  board whole at that aspect (`:1702-1727`), so a 12×12 board fits wherever 16×16 does. Still
  unobserved in a browser at 12×12: CI only ever renders a `duel` replay.
- **Whether a hosted episode in fact connects later than tick 48.** B1 is established from the
  code and from execution at every relevant join tick, and the design note's own §Decisions
  timing calls 12 s typical, but I have no production replay to point at. What would settle it:
  the join times of any real hosted `.replay` (`tickOfTime(join.time)` — two lines of
  `replay_summary.py`), or a docker-smoke variant with a `sleep 5` before the player
  `docker run` loop.

---

## Appendix — the B1 repro (run outside the repo; the working tree was not modified)

```bash
cd /workspace/cogame-lux-ai
for d in /tmp/nimdeps/*; do printf -- "--path:%s/src " "$d"; done > /tmp/paths2.txt
/tmp/nim-2.2.4/bin/nim c -d:release --path:src $(cat /tmp/paths2.txt) \
    -o:/tmp/lobbyrepro /tmp/lobbyrepro.nim && /tmp/lobbyrepro
```

```nim
## /tmp/lobbyrepro.nim — record an episode the way src/lux/server.nim's loop
## records one, with the seats joining at tick `joinTick`, then re-derive it
## exactly the way the viewer does.
import std/[json, os, strutils]
import lux/[broadcast, global, replay_runtime, replays, sim]

proc recordEpisode(path: string, joinTick, maxTurns: int, seatsThatJoin = 2):
    tuple[startedAt, red, blue, turn: int] =
  var config = defaultGameConfig()
  config.seed = 42; config.mapSize = 16; config.maxTurns = maxTurns
  var writer = openReplayWriter(path, $config.configJson(), LuxReplaySpec)
  var sim = initSimServer(config)
  sim.seats[0].name = "daveey"; sim.seats[1].name = "daveey-1"
  var joinWritten: array[2, bool]
  var lastDirective = -1
  var startedAt = -1
  while true:
    if sim.tickCount >= joinTick:                       # syncSeats()
      for seat in 0 ..< seatsThatJoin:
        if not sim.seats[seat].joined:
          sim.seats[seat].joined = true
          sim.seats[seat].connected = true
        if not joinWritten[seat]:
          joinWritten[seat] = true
          writer.writeJoin(tickTime(sim.tickCount, ReplayFps), seat,
            sim.seats[seat].name, seat, "token-" & $seat)
    if sim.phase == Lobby:                              # server.nim:484-502
      let joined = sim.seats[0].joined and sim.seats[1].joined
      if (joined and sim.tickCount >= config.startWaitTicks) or
          sim.tickCount >= config.lobbyJoinTimeoutTicks:
        writer.writeInputPacket(sim.tickCount, 0, controlPacket(InputStart))
        sim.beginPlaying()
        startedAt = sim.tickCount
      else:
        writer.writeHash(uint32(sim.tickCount), sim.gameHash())
        inc sim.tickCount
        continue
    if sim.phase == Playing:                            # server.nim:504-515
      let turn = sim.world.turn
      if sim.isDirectiveTurn(turn) and turn != lastDirective:
        lastDirective = turn
        sim.setDirective(0, scriptedDirective(sim.world, blForester, 0))
        sim.setDirective(1, scriptedDirective(sim.world, blProspector, 1))
        for seat in 0 .. 1:
          writer.writeInputPacket(sim.tickCount, seat,
            directivePacket(sim.world.directiveBytes[seat]))
      writer.writeHash(uint32(sim.tickCount), sim.gameHash())
      sim.step()
    elif sim.phase == GameOver:
      writer.writeHash(uint32(sim.tickCount), sim.gameHash())
      inc sim.tickCount
      break
  writer.writeChat(tickTime(sim.tickCount, ReplayFps), 0, sim.resultRecord())
  writer.closeReplayWriter()
  (startedAt, sim.world.cities.tileCount(Red), sim.world.cities.tileCount(Blue),
   sim.world.turn)

proc rederive(path: string): tuple[mismatch, startTick, turn, red, blue: int] =
  let data = parseLuxReplay(readFile(path))
  var initialized = initReplayRuntime(data, mismatchQuit = false)
  var player = initialized.player
  var game = initialized.sim
  var tracker = initialized.tracker
  player.seekReplay(game, 0)
  while game.tickCount < player.maxTick:
    let before = game.tickCount
    discard advanceReplayFrame(player, game, tracker, [], [])
    if game.tickCount == before: break
  (player.hashMismatchTick, player.replayStartTick(), game.world.turn,
   game.world.cities.tileCount(Red), game.world.cities.tileCount(Blue))

when isMainModule:
  let dir = getTempDir() / "lux-lobby-repro"
  createDir(dir)
  for spec in [(0, 2), (47, 2), (48, 2), (49, 2), (120, 2), (288, 2), (10, 1)]:
    let (joinTick, seats) = spec
    let path = dir / ("join" & $joinTick & "-" & $seats & ".replay")
    let live = recordEpisode(path, joinTick, 360, seats)
    let got = rederive(path)
    echo "joinTick=", joinTick, " seatsJoining=", seats,
      " | live start tick ", live.startedAt,
      " cityTiles [", live.red, ", ", live.blue, "] turn ", live.turn,
      " || playback startTick ", got.startTick,
      " mismatchTick ", got.mismatch,
      " cityTiles [", got.red, ", ", got.blue, "] turn ", got.turn
```
