# r1 review — pommerman

Repo: `/workspace/cogame-pommerman` @ `25efdbb7ca079753d4ad47953fae205d41c6ce3e` (main)
Starter for provenance diffs: `/workspace/starters/coworld-ctf` (read-only mount)
Design note: `/workspace/coworld-builder/runs/2026-08-27-pommerman/design.md` (1730 lines)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files opened: 48 (all of `src/pommerman/*.nim`, `src/pommerman{,_player}.nim`,
`replay-viewer/*`, `client/*.js|html`, `tools/*`, `tests/*.nim`, the manifest, both
Dockerfiles, all three workflows) + CI logs for run `33103016744` (jobs `test`
98625424997, `docker-smoke` 98625424858, `wasm-viewer` 98626098377).

Evidence marking: **[observed]** = read at this sha; **[measured]** = I compiled/ran
something and am quoting its output; **[inferred]** = reasoned from code I read;
**[untested]** = would need a hosted run.

---

## Findings

### F1 — every `say` is stripped, and the observation `view` is always dropped, from every `directive` replay record

- Where: `src/pommerman/directives.nim:314-338` (`boundedDirectiveRecord`),
  `src/pommerman/episode.nim:119-120` (the only caller),
  `src/pommerman/decide.nim:229` (`lastView` is always a real observation),
  `src/pommerman/broadcast.nim:101-103` (the feed's `say` gate).
- What the code does. `episode.runTurnIfDue` writes one chat record per seat per turn:

  ```nim
  writer.writeChat(state.frame, seat, directive.boundedDirectiveRecord(
    turnIndex, seat, engine.lastRadioIn[seat], engine.lastView[seat]))
  ```

  `engine.lastView[seat]` is assigned unconditionally at the top of every turn
  (`decide.nim:229`), so the `view` argument is never `JNull` in production.
  `boundedDirectiveRecord` then shrinks to `MaxDirectiveRunes = 900` in this order:
  shrink `say` by 16 runes at a time until it is empty, *then* drop the view.
- **[measured]** I compiled a probe against the repo's own modules
  (`nim r --path:src`, seed 42, tick 0, `sapperDirective` + a 62-rune `say`):

  ```
  view runes: 1005
  raw record with view runes: 1235
  bounded runes: 172
  say in bounded: <>
  view kind: JNull
  ```

  The observation alone is 1005 runes, so no `say` length can make the record fit:
  `say` is emptied first and the view is dropped second, on **every** turn.
- Consequences traced: `broadcast.stepEvents` emits a `say` event only
  `if say.len > 0` (`broadcast.nim:101-103`), so no `say` line can ever reach
  `#killfeed` from a real replay; `tools/replay_summary.py`'s `directives[].say` is
  always `""`; the design's §Readouts 9 ("The `say` lines … are where a spectator sees
  the LLM playing") and §Decisions ("the observation … is mirrored (minus
  `your_notes`) into the replay's `directive` record so the replay explains every
  decision") are both unmet in the shipped path.
- What the note says: reply-schema table line 513 — "whole `directive` record ≤ 900
  runes (`MaxDirectiveRunes`); `notes` is not in it, `say` shrinks first"; §Record
  vocabulary line 1007 lists `say` **and** `view` as directive fields. The note is
  internally inconsistent (a 1005-rune view cannot fit a 900-rune record); the code
  resolves it by deleting both.
- Checklist relation: not a named checklist item, therefore **non-blocking** by the
  rules. It does bear on item 15's premise — the only place any LLM-authored string is
  ever rendered is `tools/ci/renderer_fixture.html`, which injects its own synthetic
  `say` event (F2).
- Not caught by any test: `tests/test_pom_control.nim:351-360`
  (`directiveRecordFitsWithAView`) asserts only that the record fits and parses;
  `tests/test_pom_replay.nim:309-311` reads `directives[].say` from a fixture written
  with `view = newJNull()` (line 286), i.e. the one call site that does not pass a view.

### F2 — `canvas_text` is `total: 0` in both viewer-smoke steps; the worst-case fixture measures DOM, not canvas

- Where: CI run 33103016744, job `wasm-viewer` (98626098377) — step
  `Load the bundle in a real browser`:
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`;
  step `Worst-case renderer fixture (full-cap seat lines)`:
  `{"loaded":true,"ms":1541,"clock":null,"scorebug":null,"feed_lines":0}` then the same
  `canvas text: 0 drawn, 0 …` line.
- Why **[inferred, from code]**: `replay-viewer/static_replay.js:91-95` transfers
  `#board` with `transferControlToOffscreen()` and all drawing happens in
  `static_replay_worker.js`, so `viewer_smoke.mjs`'s main-thread
  `CanvasRenderingContext2D.fillText` patch measures nothing. Checklist item 15 says
  in terms: "`total: 0` means the check covered nothing … and is not evidence of
  anything." `--strict-text-bounds` is present on both steps (`ci.yml`), so the flag
  requirement is met; the number it gates is vacuous.
- The fixture: `tools/ci/renderer_fixture.html:134-222` loads the shipped
  `index.html` in an iframe, drives `w.PommermanChrome.frame(...)` with a full-cap
  100-rune `say` on all four seats at 360/640/1280 px, and asserts on **DOM** nodes —
  `sayRow.getBoundingClientRect()` width/height/top/left (lines 185-192) and
  `sayText.indexOf(CAP_SAY) < 0` (line 198), plus its own strings are asserted to
  still be 100 runes and emoji-terminated (lines 67-79). Those are real assertions and
  they passed (the step set `data-replay-loaded`). But the note's §Tests item 40 says
  the fixture "installs the `fillText`/`strokeText` measurer on the **iframe's**
  `CanvasRenderingContext2D` and publishes the merged report as top-level
  `window.__coworldTextBounds`", and "re-points the iframe's `window.parent`".
  **None of those three things exist in the file** — `grep` for `fillText`,
  `__coworldTextBounds`, `window.parent` in `tools/ci/renderer_fixture.html` returns
  nothing.
- The only strings this game draws on canvas are digits: the bomb fuse
  (`client/broadcast_core.js:542-546`) and the radio pair
  (`broadcast_core.js:620-628`). All LLM-authored text (`say`) is DOM
  (`client/game_block.html:350-352`, `.pm-say` in `#killfeed`); there is **no canvas
  speech bubble** anywhere, contrary to the note's reply-schema line 507
  ("rendered in the feed and as a speech bubble").
- Checklist relation: item 15. The fixture required by the last bullet exists, runs in
  its own `ci.yml` step with `--strict-text-bounds`, and asserts full-length strings.
  The `canvas_text` line it produces is `total: 0`. I report both facts; the
  categorisation is the judge's.

### F3 — `kick` with nothing to kick behaves as `stay`, not as `hide`

- Where: `src/pommerman/control.nim:463-469` and `control.nim:431-432`.
- Traced: `chooseAction` emits the direction move only when
  `order.dir >= 0 and me.kick` **and** a bomb sits in that direction. Otherwise control
  falls through to `targetCell`, whose `okKick` branch is
  `result = (me.x, me.y, 0)` — the bomber's own cell. `bfsStep(me → me)` returns
  `(true, -1, 0)` (`control.nim:75-76`), `step.dir < 0`, so `chooseAction` returns
  `acStay` (`control.nim:479-480`).
- What the note says: §The controller, Step C table, line 668 — "`kick dir` … If it is
  not adjacent to a bomb in `dir`, or lacks `kick`, **it behaves as `hide`**."
- Practical delta: only when the bomber's own cell is safe (Step B already overrides
  when it is not). `hide` would walk to the safest reachable cell; the code stands
  still. Non-blocking (no checklist item names it). No test covers the degraded `kick`
  path — `tests/test_pom_control.nim:309-317` only exercises the validator.

### F4 — `turnSpacingMs` is a blocking `sleep` inside the turn, and it is inside the `turnBudgetMs` window

- Where: `src/pommerman/decide.nim:205-207` (`turnStart = getMonoTime()`),
  `decide.nim:255-258` (the sleep), `decide.nim:268-273` (the budget check).
- Traced. `turnStart` is taken before the spacing wait; the wait is
  `sleep(min(turnSpacingMs, turnSpacingMs - since))`, i.e. up to 10 000 ms of blocking
  sleep on the game loop's own thread (`episode.runTurnIfDue` →
  `engine.turn` is synchronous inside `runEpisodeFrame`). The retry gate is
  `if getMonoTime() - turnStart >= budget` — so the sleep consumes the same 12 s
  window the two attempts are supposed to live in. Concretely: a 10 s spacing sleep
  plus an 8 s attempt-1 timeout is 18 s ≥ 12 s, so that turn gets **no retry**; the
  seats get a `timeout` fallback record (`decide.nim:269-272`) and then the sapper
  order.
- What the note says: §Turn and tick structure step 8, line 187-188 —
  "`turnSpacingMs = 10000` is a floor on the wall clock between consecutive **batch
  starts**, not a sleep on the critical path: the loop keeps stepping ticks while it
  waits." Ticks do not advance during this sleep.
- Bound check **[inferred]**: batch starts are still ≥ 10 s apart and each turn's calls
  are ≤ 8 + 3 = 11 s, so the per-turn period is `max(10 s, ~11 s)` and 36 turns is
  ≤ ~400 s — inside the note's 432 s worst case and well inside the 640 s stop. The
  wait is bounded (`turnSpacingMs` is clamped to ≤ 60 000 at
  `sim_config.nim:66`, and the shipped value is 10 000). So this is a deviation in
  mechanism, not an unbounded wait. Non-blocking against checklist item 5.
- Second-order: because the sleep blocks the loop, `/global` frames and the seat
  frame blob also pause for it. `/healthz` is unaffected — mummy serves on its own
  thread (`server.nim:365-371`).

### F5 — the committed design note carries no errata section, though three code comments cite one

- Where: `src/pommerman/sim_types.nim:59-61` ("the design note's `[0.5, 1, 2, 4, 8]` is
  recorded as an errata in `docs/plans/2026-08-27-pommerman-design.md`"),
  `tests/test_pom_board.nim:41-44` (same file cited for the 57/28 → 56/29 slip),
  `src/pommerman/baselines.nim:46` ("Recorded as a design errata"),
  `tools/ci/baseline_tuning.json:3`.
- **[measured]** `diff docs/plans/2026-08-27-pommerman-design.md
  /workspace/coworld-builder/runs/2026-08-27-pommerman/design.md` → identical;
  `grep -i errata` in that file matches only line 719, which is the note's own generic
  sentence about retunes. The cited errata does not exist: the committed note still
  says 57 rigid / 28 passage (line 824), `dodgeHorizon = 6` (lines 643, 715, 1423,
  1437, 1466), `PlaybackSpeeds [0.5, 1, 2, 4, 8]` (line 1237) and
  `(2, 8, 6, 2)` tunables (line 714).
- Non-blocking (documentation provenance). The deltas themselves are consistently
  implemented — see "Verified" §D below.

### F6 — `--preload-file data@data` was dropped from the wasm link line

- Where: `replay-viewer/config.nims:47-58`; the starter has
  `--preload-file {rootDir / "data"}@data` at the equivalent line
  (`/workspace/starters/coworld-ctf/replay-viewer/config.nims:46`).
- What the note says: §Viewer line 1116 lists `--preload-file data@data` among the
  flags kept.
- Traced consistency: nothing in the wasm entry needs a virtual FS —
  `replay-viewer/pommerman_replay.nim:13` imports only
  `pommerman/[broadcast, replay_runtime, replays, roster, sim]`, none of which touch
  pixie or `readFile`. `Dockerfile.replay-viewer` correspondingly asserts
  `pommerman_replay.{wasm,js}` but **no** `.data` (lines 56-58) and copies the art as
  plain files the page fetches (lines 41-52), so the note's
  `pommerman_replay.{js,wasm,data}` asset list (line 1371) is also not matched.
  `-s FILESYSTEM=1` is kept (`config.nims:54`). Internally consistent; deviates from
  the note only. Non-blocking.

### F7 — five files the note lists as kept are absent

- `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`,
  `flake.nix` (note line 754) and `client/league_replayer.html` (note line 751) do not
  exist in the tree (`find . -type f` at this sha).
- Nothing references them: `grep -rn "expand_replay\|extract_events\|record_fixture\|
  league_replayer\|flake.nix"` across `.github/`, `tools/`, `tests/`, `docs/` returns
  nothing. Non-blocking; forensics tooling that the note promised and CI never uses.

### F8 — the state JSON the viewer reads is not the object the note prints

- Where: `src/pommerman/broadcast.nim:236-273` (`buildStateJson`).
- The emitted object is the starter's envelope —
  `{t, st, mx, mt, ph, lob, pl, lp, sk, ff, sp, en, pov, teams, roster, gv, pm:{…}}` —
  with every pommerman field nested under `pm` (`board`, `bombs`, `danger`, `bombers`,
  `deaths`, `scorch`, `seats`, `alive`, `kills`, `wood`, `collapse`, `mismatchTick`,
  `endcard`, `events`), plus `lulls`/`beats`/`lead` sent once.
- What the note says: §The state JSON the viewer reads, lines 1036-1080, prints a flat
  object (`tick`, `maxTicks`, `turn`, `turns`, `phase`, `board`, `bombs`, `danger`,
  `bombers`, `teams`, `collapse`, `events`, `feed`, `result`) and says
  `buildStateJson` "emits exactly this object once per drawn frame". There is no
  top-level `feed` key at all — the feed is derived client-side from the `events`
  array (`client/game_block.html:340-430`).
- Every field the note names has an equivalent in the shipped shape, the viewer reads
  the shipped shape, and `tests/test_pom_engine.nim:228-249` pins it. Deviation is in
  the note's illustration only. Non-blocking.

### F9 — `.tiny` toggles at `boardW < 640`, not the starter's 620

- Where: `client/page_script.js:601-605`
  (`stage.classList.toggle('tiny', boardW < 640);`), asserted at
  `tests/test_pom_viewer.nim:223`; the starter's page uses 620.
- What the note says: §Legible at 360 px line 1322 — "`toggles #stage.tiny` at
  `boardW <= 620`, both kept verbatim".
- The comment at `page_script.js:601-604` states the change and the reason. Checklist
  item 11 asks for "labels hidden under `640px`", so 640 is what the checklist wants.
  Non-blocking; flagged because the note says "verbatim".

### F10 — the tick-budget test asserts < 4000 ms where the note says < 1 s

- Where: `tests/test_pom_sim.nim:583-594` — `check elapsed < 4000`.
- What the note says: §Tests item 14 — "a full 144-tick episode completes in **< 1 s**
  in a release build". The test runs in both debug and release under `ci.yml`'s loop,
  which is presumably why the bound was widened. Not a loosening *during this run*
  (the assertion has been `4000` since the initial commit `8de16ac`). Non-blocking.

### F11 — the live `/global` feed never receives the directive-derived events

- Where: `src/pommerman/server.nim:454` (`var frameChats: seq[ChatRecord]`), assigned
  only in the replay branch at `server.nim:458`, then consumed at `server.nim:488`
  (`stepEvents(sim, tracker, frameChats)`).
- Traced: in live (non-replay) mode `frameChats` stays empty, so `stepEvents`
  (`broadcast.nim:76-108`) emits no `turn`, `order`, `radio`, `say` or `fallback`
  events to the live spectator packet. `episode.EpisodeState.turnRecords`
  (`episode.nim:22`, filled at `episode.nim:105`) is never handed to the server.
  The replay path is unaffected — `replay_runtime.runFrame:101-105` fills
  `player.pending` and `server.nim:458` passes it.
- The note puts live spectating out of scope (line 1724: "`/global` broadcasts a status
  feed … the hosted spectator experience is the static replay bundle only"), so this is
  a gap only in the developer-local live view. Non-blocking.

### F12 — `camper` reads `params.dodgeHorizon`; the controller reads `config.dodgeHorizon`

- Where: `src/pommerman/baselines.nim:209` (`sim.dangerNow(params.dodgeHorizon)`) vs
  `src/pommerman/sim_state.nim:196-201` / `control.nim:214-215`
  (`sim.config.dodgeHorizon`).
- Both are 8 by default and `tests/test_pom_tuning.nim:19-21` asserts
  `DefaultBaselineParams.dodgeHorizon == defaultGameConfig().dodgeHorizon`, so the
  shipped configs cannot disagree. A hosted `game_config` that set `dodgeHorizon` to
  anything else would silently split them. Non-blocking; noted because the note treats
  `dodgeHorizon` as one number.

### F13 — `docker_smoke.sh` does not fail on `reason == "fault"`

- Where: `tools/ci/docker_smoke.sh:306-308` — it only prints
  `episode end reason: {reason}`. (The file is the coworld-builder template with the
  three substitutions and nothing else — `diff` against
  `coworld-builder/templates/tools/ci/docker_smoke.sh` shows only `<slug>`/`<IMAGE>`/
  `<SEATS>` lines.)
- What the note says: §End conditions line 298 — "A defect: `tools/ci/docker_smoke.sh`
  fails the build if the smoke episode reports it."
- Compensated in the adjacent step: `ci.yml`'s `Replay summary parses as strict UTF-8
  JSON` asserts `summary['results']['reason'] in ('complete','deadline')` and
  `endRule in ('wipe','tickCap')`, so a fault is red in the same job. Non-blocking.

### F14 — a seat that never joins produces `fallbackTurns == 0`

- Where: `src/pommerman/decide.nim:242-249` (a non-LLM seat gets `installScripted`,
  which leaves `source = dsScripted`, and a `disconnected` fallback record with
  `attempt: 1`), `src/pommerman/episode.nim:110-116` (only `dsFallback` increments
  `fallbackTurns`), `src/pommerman/roster.nim:190-192` (playback only counts
  `attempt == 2`).
- What the note says: §Tests item 23 — a seat that never connects yields "a finished
  episode inside the wall-clock budget, with `fallbackTurns` counted, `deadSeats` set".
  `tests/test_pom_engine.nim:70-101` asserts `deadSeats[3]`, the closed failure payload
  and the `disconnected` records, but not `fallbackTurns[3]`, and the value is 0.
  Non-blocking (the fact is still visible in `deadSeats` and in the replay records).

### F15 — the strict-UTF-8 replay-summary test fills two capped fields, not "every" one

- Where: `tests/test_pom_replay.nim:266-290` — `say` (400 × U+1F525 → truncated to 100
  runes) and `notes` (600 × U+1F6E1 → 200 runes). The policy label
  (`MaxPolicyLabelRunes`), `stopDetail` (`MaxStopDetailRunes`) and `fallback.detail`
  (`MaxFallbackDetailRunes`) are filled with ASCII in that fixture.
- Note §Tests item 28: "a replay whose **every** capped field is filled to exactly its
  cap with 4-byte emoji". Note that `notes` never reaches the replay at all
  (`directives.nim:296` — it is deliberately excluded from the record), so the emoji
  `notes` in that test never crosses the UTF-8 boundary being tested. Checklist item 9
  ("a test feeds multi-byte input at the cap and asserts the output is valid UTF-8") is
  satisfied by `say` — `tests/test_pom_control.nim:330-349` and
  `test_pom_replay.nim:299-311`. Non-blocking.

### F16 — `game.docs` uses `"type":"uri"`, the checklist prints `"type":"text"`

- Where: `coworld_manifest_template.json:38-60`.
- The design note pins `uri` explicitly (lines 1401-1403), and the manifest matches the
  note. Checklist item 10 shows
  `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`.
  Both `readme` and `pages` are present as objects and
  `game.protocols` carries both `player` and `global` as `{type,value}` objects
  (`manifest:28-37`), which is the part of item 10 stated as a requirement. **[untested]**
  whether the platform validator accepts `uri`; `ci.yml`'s `manifest` job runs the
  installed `coworld==0.1.43` loader over the substituted manifest and it passed
  (job 98625424649, green). Reporting the mismatch for the judge; I did not classify it.

### F17 — the game server still serves `/client/replay`

- Where: `src/pommerman/server.nim:237-242`.
- The design sanctions it (line 1099: "No `/client/replay` live-server viewer is ever
  declared to the platform; the game still serves `/client/replay` locally for
  developers"), the starter has the same route, the manifest declares only
  `"replay_viewer": {"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json:15-17`), and `coworld-release.yml:206-213` hard-fails
  the release if certification does not report the static bundle. Checklist item 3
  says "No `/client/replay` pod path anywhere"; the route exists in the binary but is
  declared nowhere. Reporting the fact; classification is the judge's.

### F18 — `showPlayerLabels` is carried everywhere and read nowhere

- Where: `sim_types.nim:120`, `sim_config.nim:33,135-136,219`,
  `tests/test_pom_labels.nim:28-38`. `grep -rn showPlayerLabels src/ client/` finds no
  consumer: no renderer or label path branches on it. It is `false` in all three
  shipped `game_config`s and in the default, and the label vocabulary
  (`labels.nim:13-28`) contains only aliases, so behaviour matches the note; the flag is
  inert. Non-blocking.

### F19 — replay size is ~34 KB, not the note's ~20 KB, and hashes are per *frame*

- Where: `src/pommerman/episode.nim:140` (`writer.writeHash(state.frame, sim.gameHash())`
  is called on **every** frame, including Lobby and the 90-frame GameOver hold, not only
  on the 144 play ticks). CI's smoke replay: `replay=34102B`
  (docker-smoke log, job 98625424858).
- The note says "144 hashes + 144 order records + ~15 chat records ≈ **20 KB**"
  (line 859). The extra bytes are the 144 directive chat records (~190 B each) plus the
  non-play frames' hashes. Harmless; the hash chain is strictly-increasing-in-frame and
  the re-derivation aligns because playback runs the same `advanceFrame` per frame
  (`replay_runtime.nim:106`). Non-blocking.

---

## Verified — load-bearing behaviours traced and consistent

### A. Resolution rules (the note's 13-step tick order)

- `sim.nim:310-322` `step()`: `tick += 1` → collapse if due → `dangerNow()` snapshot →
  `resolveTick(chooseActions(danger))`. All actions are chosen from the snapshot
  (`chooseActions`, `sim.nim:42-48`) before any mutation. ✔ steps 1-3.
- **Collapse first** (`sim.nim:50-74`): the ring goes rigid, bombs on it are dropped
  *without detonating and without returning ammo*, items/flames cleared
  (`board.nim:205-220`), a living bomber there dies `cause: "crushed"` with
  `killer = -1` so no `kills` is credited. ✔ step 2. Tested
  `test_pom_sim.nim:418-443`, `test_pom_sim.nim:396-417` (ammo not returned on collapse).
- **Placement** (`sim.nim:82-101`), ascending seat: requires `ammo > 0` and no bomb on
  the cell, else degrades to stay; `fuse = bombFuse`, `blast` copied from the placer,
  `velocity = vNone`, next `id`; `placed[seat]` suppresses that seat's movement. ✔
  steps 4 and 6.1.
- **Kicked-bomb movement** (`sim.nim:104-123`), ascending index (== ascending id, since
  bombs are only appended and filtered in place): advances iff destination is passage,
  flame-free, bomb-free and living-bomber-free, else `velocity = vNone`. ✔ step 5.
- **Bomber movement** (`sim.nim:126-184`), ascending seat, from an `occupied` grid seeded
  with the snapshot positions and never cleared: rigid/wood fails; a bomb in the way
  triggers the kick check (`me.kick` and far cell passage + flame-free + bomb-free +
  bomber-free) and **the kicker does not move**; an occupied destination fails, so
  lower-seat-wins with no swaps; otherwise move and pick up. ✔ steps 6.2-6.6. Tested
  `test_pom_sim.nim:191-261` (contested cell, no-swap, into-wall, bombing-does-not-move)
  and `:262-335` (kick).
- **Fuse tick** (`sim.nim:187-189`): `if sim.bombs[index].placedTick != sim.tick`. This
  is builder delta #6 and it is consistent — a bomb laid at `t` reaches `fuse == 0` at
  `t + bombFuse` exactly; `docs/RULES.md:45` and `:103` state the same rule, and the
  system prompt (`llm.nim:212`) says "8-tick fuse".
- **Chain-reaction fixpoint** (`sim.nim:192-212`): iterate at most `bombs.len + 1`
  passes, adding any bomb standing on a blast cell with `fuse = 0`. Terminates. ✔
  step 8. `blastCells` (`bombs.nim:66-84`) stops *before* rigid, stops *at and
  including* wood, passes through everything else. Tested `test_pom_sim.nim:9-104`.
- **Flames, wood, power-ups** (`sim.nim:215-261`): `owner[cell]` is claimed by the
  **first** detonating bomb in ascending-id order, so wood is credited once to the
  lowest-id bomb's team; a revealed power-up is placed on the cell; a power-up already
  lying in a blast cell is destroyed; every detonating bomb returns `ammo` to its owner,
  capped at `maxAmmo`. ✔ step 9.
- **Simultaneous deaths** (`sim.nim:264-298`): the dying set is computed for all seats
  first, then applied — no ordering. `cause` is `suicide` when `killer == seat`,
  `friendlyfire` when `teamOfSeat(killer) == teamOfSeat(seat)`, else `bomb`;
  `teamKills`/`seatKills` increment **only** cross-team. ✔ step 10. Tested
  `test_pom_sim.nim:336-395`.
- **Flame decay** (`sim.nim:301-305`): `flameLife = 2` set at detonation, decremented at
  the end of the tick, so a flame kills on the tick it appears and on the next. ✔
  step 11. Tested `test_pom_sim.nim:105-137`.
- **`gameHash`** (`sim_state.nim:255-291`): per cell `(terrain, item, flameLife)`, per
  bomber `(seat, x, y, alive, ammo, blast, kick)`, per bomb
  `(id, x, y, fuse, blast, owner, velocity)`, per team `(alive, kills, wood)`, then
  `tick`, `collapsedRings`, and **the four seats' stored radio pairs**, exactly the
  order the note pins (lines 848-851). FNV-1a over the 64-bit two's-complement image
  (`mixHash`, `sim_state.nim:123-130`) — integer-only, so wasm32 and x86-64 agree.
  `flameOwner` is deliberately excluded and is re-derived identically. ✔ step 12.
- **End evaluation** (`sim.nim:16-31`): wipe first (both at once → `wipedTeam = 2`,
  draw), then `tick >= maxTicks`. ✔ step 13.

### B. Radio — one turn late, partner only, never cross-team

- `radio.nim:45-74`: `send`/`receive` both call `assertSeatOnTeam`, which raises
  `SimGuardError` on a team/seat mismatch. `deliver()` copies `pending[seat]` into
  `next[partnerOfSeat(seat)]` and nothing else, so there is **no code path from a seat
  index to a cross-team pending pair** through `receive`.
- Ordering: `decide.turn:212` calls `sim.mailbox.deliver()` before any observation is
  built (`decide.nim:228-229`); `sim.applyOrders` (`sim.nim:352-359`) stores the new
  pending pair. Turn 1 has `sentCount == 0` → `hasDelivery` false →
  `radio_from_teammate: null` (`decide.nim:63-71`). Exactly one turn late, always.
- A fallback still sends a pair: `fallbackDirective` (`baselines.nim:237-244`) is
  `sapperDirective` with the source relabelled, and `sapperRadio`
  (`baselines.nim:135-140`) is `[1+ammo, 1+enemiesWithin4]` clamped to `[1,8]`.
- The observation contains no other radio field (`decide.nim:116-143`); the *renderer*
  shows both teams' pairs (`global.nim:103`, `broadcast_core.js:610-628`), which is
  what the note asks for.
- Tested: `test_pom_sim.nim:444-486` — 500 randomised turns, cross-team `receive`
  raises, `send` under the wrong team raises, a fallback still increments `sentCount`.
- **Determinism corner that matters:** `gameHash` mixes `pending`, never `delivered`.
  Playback never calls `deliver()` (`replay_runtime.runFrame:86-96` applies orders
  directly), so `delivered` diverges between record and playback and it does not matter.
  ✔ this is the difference between a clean chain and a mismatch at every turn boundary.

### C. Decision path, and every wait with its bound

| Wait | Where | Bound |
|---|---|---|
| attempt 1 | `decide.nim:274-292` → `curl.makeRequests(batch, attempt1Ms div 1000)` | 8 s (`sim_config.nim:69` floors at 1000 ms so the whole-second floor is an identity) |
| retry (once) | same, `retryMs div 1000` | 3 s; `while … attempt < 2` (`decide.nim:265`) |
| per-turn deadline | `decide.nim:268` | 12 s, checked between attempts (see F4) |
| batch spacing | `decide.nim:255-258` | ≤ `turnSpacingMs`, clamped ≤ 60 000 (`sim_config.nim:66`) |
| budget guard | `decide.nim:216-223` — `elapsed + 2*ceil(turnBudgetMs/1000) > wallClockBudgetSeconds` → `elapsed > 616` | one-way latch `llmOff`; all remaining turns are scripted, episode still `complete` |
| engine stop | `episode.nim:36-53` — `elapsedSeconds >= wallClockBudgetSeconds` | 640 s (`sim_config.nim:71-72` caps at 640) → `reason = deadline`, load-bearing `stop` record |
| lobby | `sim_state.nim:193-194` + `episode.nim:61-69` | `lobbyJoinTimeoutTicks` (2400) |
| game-over hold | `episode.nim:148-149` | `gameOverTicks` (90) |
| shutdown grace | `server.nim:558-561` | fixed 20 s |
| frame limiter | `server.nim:519-527` | ≤ 1/6 s per frame; `sleep(1)` inner loop |
| headless driver | `episode.nim:209` | `state.frame < maxFrames` (20000) |
| chain fixpoints | `sim.nim:199`, `bombs.nim:119` | `bombs.len + 1` passes |
| record trimming | `directives.nim:328` | `guard < 24` |
| replay advance | `replay_runtime.nim:269,278` | `advanced < 8`, `skipped < 64` |
| player dial | `pommerman_player.nim:26-30,77-88` | 240 × 500 ms; `ReconnectAttempts = 6` |

- **One parallel batch per turn** ✔: `decide.nim:276-292` builds one `RequestBatch`
  containing every open seat and issues a single `curl.makeRequests`. There is no
  per-seat request loop anywhere. At most 4 in flight, at most 4 × 36 × 2 = 288 calls.
- **Tolerant parsing** ✔: `extractJsonObject` (`directives.nim:85-123`) scans for the
  outermost balanced `{…}` with string/escape awareness, falls back to
  first-brace..last-brace, and raises only when there is no object. Fence + prose
  tolerance tested at `test_pom_control.nim:373-378`.
- **Repair-don't-reject** ✔ (`directives.nim:173-269`): no `order` → keep last turn's
  and still take the radio; unknown verb → previous verb; `go` clamped then retargeted
  via `nearestPassable`; `hunt` on a non-living-enemy → `nearestEnemy`; bad `kick` dir
  → `-1`; bad/missing `radio` → the previous pair; each repair bumps `rejected`, summed
  into `results.ordersRejected` (`decide.nim:316`). Only a non-object raises.
- **Fallback is the same proc as the baseline** ✔: `decide.installFallback` →
  `baselines.fallbackDirective` → `baselines.sapperDirective`. Asserted field-for-field
  over 40 randomised states at `test_pom_control.nim:164-184`.
- **Fallback is recorded** ✔ so phase 60 can count it: `fallbackRecord`
  (`decide.nim:151-161`) with `cause ∈ {timeout, parse_error, transport_error,
  throttled, no_credentials, budget_guard, disconnected}` — all seven appear in
  `decide.nim` (lines 237, 248, 271, 320-323, 341-346). The game log prints
  "falling back" (`decide.nim:240,350`) and "the LLM provider is unavailable"
  (`llm.nim:125`), the two phrases phase 60 greps.
- **Throttle fail-fast** ✔: `llm.nim:174-178` sets `throttled` on a 429 when there is no
  second candidate model; `decide.nim:331-336` breaks out of the retry loop.
- **Credential ladder** ✔ Bedrock → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` →
  `disabled = true` (`llm.nim:93-126`); one Bedrock candidate,
  `us.anthropic.claude-haiku-4-5-20251001-v1:0` (`llm.nim:68-77`); `max_tokens = 900`
  (`sim_config.nim:35`); no `output_config.effort` for haiku/4-5 (`llm.nim:146-149`);
  `anthropic_version: bedrock-2023-05-31` (`llm.nim:140`).

### D. The ten declared deltas — each checked for cross-file consistency

1. **56 rigid, not 57** ✔ `board.nim:162-186` produces 40 border + 16 lattice = 56 rigid,
   36 wood, 29 passage; `tests/test_pom_board.nim:64` asserts exactly `56/36/29` over
   1000 seeds; `docs/RULES.md:34` says "56 rigid, 36 wood, 29 passage". The only place
   still saying 57/28 is the committed design note (F5).
2. **Swept tunables (3, 4, 8, 2), `dodgeHorizon = 8` everywhere** ✔
   `baselines.nim:36-39` = `tools/ci/baseline_tuning.json` = `sim_config.nim:23`
   (`dodgeHorizon: 8`) = manifest `config_schema.dodgeHorizon.default` (line 195) =
   all three shipped `game_config`s (lines 607, 667, 739). Asserted by
   `tests/test_pom_tuning.nim:9-21` (including `== defaultGameConfig().dodgeHorizon`)
   and `tests/test_pom_control.nim:387-393`; `ci.yml` re-runs
   `tools/tune_baselines.nim --check`.
3. **`PlaybackSpeeds` without 0.5** ✔ `sim_types.nim:56` `[1,2,4,8]`; the byte-identical
   `client/chrome_common.js:437` speed→command map is `{1,2,3,4,8,16}` with no 0.5
   entry, so a half-speed chip would indeed be inert. `wire_constants.nim:19` emits the
   array; `replay_runtime.applyCommand:245-248` maps `'1','2','4','8'` to indices 0-3.
4. **Art filenames renamed** ✔ `data/{bomber_red,bomber_blue,bomber_red_crown,
   bomber_blue_crown,bomb,powerup_range,powerup_kick,arena_floor}.png`, with the
   starter's `soldier_red.png`/`soldier_blue.png` kept as the fallback
   (`broadcast_core.js:195-198` `withFallback('bomber_red.png','soldier_red.png')`).
   No `paint*`/`spray*`/`shield*` filename survives, which is what lets
   `tests/test_pom_endcard_labels.nim:13-15`'s forbidden list (`paint`, `spray`, …)
   pass. Server asset table (`server.nim:78-89`) and
   `Dockerfile.replay-viewer:41-52,72-78` list the same set.
5. **`replay_broadcast.html` derived by a committed builder** ✔ **[measured]** I re-ran
   `python3 tools/build_broadcast_page.py --starter
   /workspace/starters/coworld-ctf/client/replay_broadcast.html --page-script
   client/page_script.js --game-block client/game_block.html --out /tmp/rebuilt.html`
   and `diff` against the committed file is **identical**. I also enumerated the CSS
   chunks the script drops (81 top-level rules): every one is `#viewpanel`/`#minimap`/
   `#zoombar`/`.zbtn`/`#zoom-*`, `#fpv*`/`.fpv-*`/`#povBadge`, `.lives-num`/
   `.lives-label`/`.squad*`/`.flagicon`/`.hcap`/`.perk-*`/`.ec-heart*`, or a
   `.beat-marker.{kill,steal,return,capture,gameover}` rule — i.e. exactly the note's
   removal list. No stage/scorebug/banner-lane/kill-feed/transport/scrubber/momentum/
   endcard/locker-room rule is touched. Size: starter 116 531 B above its PAINTBALL
   banner → fork 88 644 B above its POMMERMAN banner, and the 27 KB difference is the
   removed rules plus the swapped page IIFE (`page_script.js`, 27 811 B, replacing the
   starter's 23 185 B one). This is **not** the literal byte-identical prefix the note
   describes (note line 1157), which is the declared delta; the prefix that remains is
   byte-pinned by length + SHA-1 at `tests/test_pom_viewer.nim:109-123`.
6. **Fuse not ticking on the placing tick** ✔ — see §A above.
7. **`parseSeatDirective` takes values, not closures** ✔ `directives.nim:173-180`
   `livingEnemies: set[uint8]`, `nearestEnemy: int`; caller precomputes both
   (`decide.nim:298-305`) with the comment naming the reason (Nim cannot capture a
   `var` parameter). Tests updated in the same commit (`6eacb0a`) without weakening any
   assertion.
8. **Sapper's tick-88 threshold derived** ✔ `baselines.nim:65-69`
   `headInwardTick = collapseTicks[0] - 8` → 88 for the teams variant, 56 for blitz,
   `high(int)` when the table is empty (so `testConfig`'s empty-collapse tickCap case
   never triggers it). Used by both baselines (`baselines.nim:177`, `:221`).
9. **Bomber chips baked in the renderer** ✔ there is no `rig_art.nim` in the tree and no
   pixie import outside the server; the chips, the floor tiling + 18 % darken + 1 px
   gridlines, the `wall_h/wall_v` composite with the red-hot rim on collapsed rings and
   the seeded plank grain are all in `client/broadcast_core.js:288-368`.
   `global.nim:25-28` keeps `FloorDarkenPermille = 180` / `GridlineEvery = 1` as the
   descriptor the renderer reads (`boardJson`, `global.nim:66-67`).
10. **Starter soldier pngs kept as fallback** ✔ `data/soldier_{red,blue}{,_crown}.png`
    all present and byte-identical to the starter's; wired at
    `broadcast_core.js:195-198`; shipped by `Dockerfile.replay-viewer:45-46`.

### E. Replay writer, re-derivation and the viewer

- `COWLDPOM` header = magic + `u16` format + `gameName` + `gameVersion` + the resolved
  config JSON (`replays.nim:140-149`). Config JSON carries `seed`, `num_agents`, every
  rule constant, `radio {low, high, delayTurns: 1}`, `players[].name`, `slots[]`
  (`sim_config.nim:191-223`) — the note's list plus extras.
- Record kinds: join / leave / gameStart / **order** (`verb`, `x`, `y`, `target+1`,
  `dir+1`, **`radio.a`, `radio.b`**) / chat / hash / **stop**
  (`replays.nim:151-210`). Both radio integers are in the order record ✔.
- Chat record kinds actually written: `register` (`server.nim:447`), `directive`
  (`episode.nim:119`), `fallback` (`decide.nim:151`), `budget_guard`
  (`decide.nim:176`), `stop` (its own record kind, `episode.nim:50,136`), `result`
  (`episode.nim:189`, `roster.nim:144-149`). ✔ the note's six.
- **The stop is load-bearing and applied by one proc on both sides** ✔:
  `episode.maybeStop` writes `rkStop` then calls `sim.applyStop`
  (`sim.nim:33-40`); playback calls the *same* `sim.applyStop` from
  `replay_runtime.runFrame:97-100`. Asserted for all four end rules
  (`wipe`, `tickCap`, `wallClock`, `fault`) at `tests/test_pom_replay.nim:29-126`, each
  with `hashMismatchTick == -1` and identical banked end state.
- **Per-tick hash check** ✔ `replay_runtime.nim:107-118` compares
  `sim.gameHash()` against the recorded value for the frame just advanced and latches
  `hashMismatchTick`. A deliberately corrupted hash is caught at exactly its tick
  (`test_pom_replay.nim:128-155`). `pom_mismatch_tick`
  (`pommerman_replay.nim:110-112`) surfaces it; `#mmwarn` is fed from
  `pm.mismatchTick`.
- **The viewer re-derives from the same sim module** ✔
  `replay-viewer/pommerman_replay.nim:13` imports `pommerman/[…, sim]`;
  `config.nims:9` puts `src` on the path. Nothing parallel-records display state.
  Checklist item 2 satisfied.
- **`seekTo` identity re-seed** ✔ `replay_runtime.nim:204-222` resets to a fresh
  `SimServer` and calls `sim.applySeatIdentities(player.data)`
  (`roster.nim:203-213`), which re-applies join + `register`/`fallback`/`directive`
  chats so the scorebug and endcard keep the real policy names and the fallback glyph.
  `pom_load_replay` calls the same proc for frame 0 before the first render
  (`pommerman_replay.nim:70-77`). Tested `test_pom_replay.nim:215-250`.
- **Emscripten flags vs bootstrap agree** ✔ `config.nims` has **no** `MODULARIZE` and
  **no** `EXPORT_NAME`; the module is emitted as `pommerman_replay.js`;
  `static_replay_worker.js:188` sets `Module.onRuntimeInitialized`;
  `importScripts('./wire_constants.js','./broadcast_core.js','./pommerman_replay.js')`.
  All from coworld-ctf. `-s ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `FILESYSTEM=1`,
  `ENVIRONMENT=web,worker,node`, `EXPORTED_RUNTIME_METHODS=HEAPU8` and the thirteen
  `_pom_*` exports are present. Pinned at `test_pom_viewer.nim:276-314`.
- **Load/error signals** ✔ `static_replay.js:161-165` sets
  `data-replay-loaded="true"` in the `'loaded'` branch, which the Worker posts only
  after `ingestPacket()` has handed BroadcastCore the first frame
  (`static_replay_worker.js:127-131`); `showFailure` sets `data-replay-error`
  (`static_replay.js:14-20`). CI observed `{"loaded":true,"ms":293,…}` and a soak that
  advanced `"0 / 228" -> "24 / 228" -> "36 / 228"`.
- **`wasm-viewer` `needs: docker-smoke`** ✔ (`ci.yml`), it downloads the
  `smoke-replay` artifact and runs
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay … --timeout 90 --soak 10 --strict-text-bounds`.
  The step ran and passed at 18:25:51. `tools/ci/viewer_smoke.mjs` is **byte-identical**
  to `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff -q`, no output).
- `tools/wasm_replay_smoke.cjs` runs the exact emitted module headless under Node
  against the smoke replay (200 frames) — step green.

### F. Chrome provenance

- `client/chrome_common.js` **byte-identical** to the starter's — **[measured]**
  `sha256 7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` on both
  files. Also pinned by length + SHA-1 literal at `test_pom_viewer.nim:66-68` so a CI
  runner with no mount still catches an edit.
- Removed ids appear nowhere outside comments — **[measured]**
  `grep -n "viewpanel\|minimap\|zoombar\|fpv\|povBadge" client/replay_broadcast.html`
  returns 4 hits, all inside `//` or `<!-- -->` comments (lines 1256, 1703, 1705, 1706).
  Asserted with comments stripped at `test_pom_viewer.nim:125-141`.
- Beat kinds — **[measured]** the set of `.beat-marker.<kind>` rules in the page is
  exactly `{collapse, death, end, fallback, firstblood, kick}`
  (`game_block.html:132-159`), and those are exactly the kinds `pomBeat` is called with
  (`game_block.html:370,377,386,405,412,430` and the `end` beat from the pre-scan,
  `replay_runtime.nim:176-179`). Asserted `test_pom_viewer.nim:188-210`.
- Beats are labelled, clickable `<button>`s that seek
  (`game_block.html:255-275`: `createElement('button')`, `title`, `aria-label`,
  `CTX.send('s:' + tick)`), named `pomBeat` and never `markBeat`; the alias-shadowing
  test (`test_pom_viewer.nim:156-186`) walks the page's own `var` alias list and
  asserts no appended function collides, and that `markBeat` does not appear below the
  banner.
- Transport rules: `relayout()` sets `--hudscale`, `--topband` and `--band` on
  `document.documentElement` (`page_script.js:600,609-610`);
  `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px) }`
  (`replay_broadcast.html:560-576`); `#endcard.on` is the shown class
  (`:582`); a scrub click removes `.on` immediately (`page_script.js:524-525`) and
  every other seek removes it on the next frame because `renderEndcard` clears it
  whenever `s.ph !== 'gameover'` (`page_script.js:463-468`) — and the Worker runs and
  ingests one frame synchronously on every input command
  (`static_replay_worker.js:146-152`), so a paused seek still redraws.
  Nothing the game block adds sits in the transport band: `#dangerchip` is
  `position:absolute; top: calc(3*var(--u))` with no `bottom`
  (`game_block.html:106-120`), asserted at `test_pom_viewer.nim:227-231`.
- Endcard vocabulary: `Bomber | Kills | Bombs | Wood | Radio`
  (`page_script.js:456-457`), `Bombers left` (`:460`), `BOMBERS STANDING`,
  `Taking corners`, `Lighting the fuses`, `showing recorded orders`,
  `kills / collapses / winner` — each present, and
  `tests/test_pom_endcard_labels.nim:94-109` asserts the count is exactly 1 for the
  nine strings that must be unique. The forbidden list (`Lives`, `LIVES`, `Clstr`,
  `Cap<`, `flag`, `heart`, `paint`, `hopper`, `hill`, `POV`, `spray`, `grenade`,
  `med kit`, `trench`) is asserted to have zero matches outside comments across all
  four client files.
- The three 360 px rules: `.plate-name { flex: 1 1 auto; min-width: 3.2em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis }`
  (`game_block.html:23-29`); `.tiny` hides `.alive-label`, `.bchip i`, `.fb-glyph`
  from the plate (`:101-103`); `var digits = tiny ? 14 :` for the fuse
  (`broadcast_core.js:535`), `tiny ? 12 :` for the radio digits (`:610`) and
  `var alpha = tiny ? 0.22 :` for the flat danger tint (`:423`) — all three asserted
  at `test_pom_viewer.nim:232-245`. Checklist item 11 satisfied.

### G. Manifest / `num_agents` / packaging

- `num_agents: 4` inside **both** variants' `game_config` (lines 593, 653) and inside
  `certification.game_config` (line 725); absent at every variant top level; schema
  pins `minimum: maximum: 4` (lines 126-132). Asserted `test_pom_manifest.nim:9-24`.
- No literal `tokens` array in any `game_config`; `config_schema.required` still lists
  `tokens` (lines 65-68). Asserted `:26-35`.
- Every array property carries `minItems`/`maxItems`: `tokens` 4/4, `players` 4/4,
  `slots` 0/4, `collapseTicks` 0/3. Asserted `:37-49`.
- `replay_viewer.bundle = "static-replay-viewer"` under `game` (lines 15-17), no
  top-level `replay_viewer`; `tools/build_replay_viewer.sh` present and mode 100755
  (`ci.yml` asserts `test -x` in two jobs and `manifest` asserts both scripts).
- `protocols.player` **and** `.global`, both `{type, value}` objects (lines 28-37);
  `docs.readme` + two `pages` whose targets exist (`docs/RULES.md`, `docs/RADIO.md`).
- `results_schema` is closed and **[measured]** its 30 property names are exactly the
  30 keys `roster.bomberResultsJson` emits (set difference empty in both directions).
  Also asserted at runtime, `test_pom_engine.nim:40-44`.
- Two declared `player[]` entries (`sapper`, `camper`), both seated in the four-slot
  cert fixture, `limits.cpu == "1"`, `run = /bin/pommerman-player`.
- `SEAT-COUNT` — **[measured]** `grep -c "SEAT-COUNT FAIL"` over the full docker-smoke
  job log (98625424858) = **0**; the job printed
  `smoke OK: seats=4 results=756B replay=34102B reason=complete`.
  `SMOKE_SEATS` defaults to `4` (`docker_smoke.sh:54`) and `ci.yml` passes `SMOKE_SLUG`.
- Placeholder gate — **[measured]** `./tools/ci/check_placeholders.sh` exits 0
  ("no scaffold placeholders in 9 files"); it greps for `<slug>`/`<IMAGE>`/`<SEATS>`
  only, assembled from parts so it does not match itself.
- `coworld-release.yml` order: build manifest (:159) → certify (:173) → **upload the
  policies** (:217) → upload-coworld (:315) → confirm canonical (:353) → secret put
  (:393). `--timeout-seconds 300` on certify (:185). Certification is hard-gated on the
  static bundle marker (:206-213).
- `tools/ci/policies.json`: four policies, two `PLAYER_PROMPT` champions (the note's
  two texts verbatim) with `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` on
  champion #2, plus `sapper` and `camper` fillers; all `run: /bin/pommerman-player`.
- One compose service `pommerman` → `{{POMMERMAN_IMAGE}}`; `Dockerfile` builds both
  binaries from one image.

### H. Two name spaces

- Everything a seat can see is an alias: the observation's `you`/`teammate`/`enemies`/
  `bombers[].id`/`bombs[].owner` all go through `seatAliasName`
  (`decide.nim:88-137`); `parseSeatAlias` matches only `IdentityNames`
  (`directives.nim:76-83`); the label vocabulary is aliases + team words + verbs +
  directions + beat kinds + skins and nothing else (`labels.nim:13-28`,
  `tests/label_manifest.txt`), and `test_pom_viewer.nim:341-343` asserts no label is
  longer than 12 chars or contains `daveey`.
- Real names live only in `results.names` (`roster.nim:77`), the replay join records
  (`server.nim:410-412`), the scorebug (`broadcast.rosterJson`/`teamsJson`, drawn by
  `page_script.js` `.plate-name`) and the endcard (`page_script.js:449-451`).
  `test_pom_endcard_labels.nim:139-143` asserts the board renderer never reads
  `seat.name`, `roster` or `policies`. `test_pom_labels.nim:40-59` asserts no real name
  reaches an observation or the prompt.
- `showPlayerLabels: false` in the default and in all three shipped `game_config`s
  (see F18 for the caveat that nothing reads it).

### I. Scoring, end conditions, reason enum

- `teamScore` (`sim_state.nim:203-215`) = `100*sign(mine-theirs) + 20*(mine-theirs) +
  (wood[t]-wood[other])`, every term an antisymmetric difference. The note's four-case
  `outcome` definition collapses to `sign(alive[t]-alive[other])` in every case it
  lists, which is what the code computes. Both teammates get the identical value
  (`scoreOf`, `:217-229`), so the four seat scores sum to exactly zero with no
  tie-break. Range ±176. Asserted over 500 randomised end states
  (`test_pom_sim.nim:487-518`) and at the end of every e2e episode.
- `endRule ∈ {wipe, tickCap, wallClock, fault}`, `reason ∈ {complete, deadline, fault}`
  (`sim_types.nim:63-70`), and the manifest's `results_schema` declares exactly those
  two enums (lines 320-336). `reason` is only ever set to `deadline` by `maybeStop` and
  to `fault` by the `advanceEpisodeFrame` catch; everything else stays `complete`
  (`sim_state.nim:177`).

### J. Tests — the note's 41 items

All 66 `test` blocks across 10 files compile and pass in CI (job 98625424997, green;
every `tests/*.nim` runs in **both** debug and `-d:release`, which is stricter than the
note's four-shard plan). Item-by-item, the note's numbered list maps to real tests with
the asserted content, except where noted: 1-14 → `test_pom_sim.nim` (item 14's bound is
4000 ms, F10); 15-16 → `test_pom_board.nim` (item 15's counts are 56/36/29, F5/delta 1;
"5 per quadrant-orbit" is covered indirectly by the rot-invariance check rather than
counted); 17-21 → `test_pom_control.nim` (17 exercises both baselines over 200 states
across both variants' `maxTicks`; 18 compares fallback and sapper field-for-field; 19
runs 500 states plus the dead-end-still-kills block; 20 covers every repair rule, the
rune caps with emoji, the 8192-byte cap and never-unactuated; 21 pins the swept tunables);
22-25 → `test_pom_engine.nim` (item 23's `fallbackTurns` is not asserted, F14); 26-29 →
`test_pom_replay.nim` (item 28's emoji cover `say`/`notes` only, F15); 30-31 →
`test_pom_manifest.nim` + `ci.yml`'s `manifest` job running the installed
`coworld==0.1.43` loader; 32-38 → `test_pom_viewer.nim` + `test_pom_endcard_labels.nim`;
39-41 → the three `wasm-viewer` steps (`viewer_smoke.mjs` against the docker-smoke
replay with `--strict-text-bounds`, the renderer fixture, `wasm_replay_smoke.cjs`) — all
present and green, with the `canvas_text` caveat in F2 and the fixture-mechanism caveat
in F2.

**Checklist item 1, second half** — `git log -p -- tests/` over the whole repo history
(5 commits, all from this run): the only edits after the initial drop are `6eacb0a`
(closure→value API change in `test_pom_control.nim`, an added `import llm`, a
`RadioPair` scope fix, replacing a "no fixture yet" placeholder with
`check seen >= 1` + `check repoFileExists("tests/replays/pommerman.replay")` — a
**strengthening** — and re-pinning `inherited.len` 60619 → 60743 after the page changed),
`4dde363` (+37 lines, new seek test) and `4db09cd` (+6 lines, new `.plate-name`
assertions). **No assertion deleted, no tolerance widened, no skip added, no test file
removed.**

---

## Could not determine

- Whether the platform's `validate_upload_manifest` accepts `"type": "uri"` in
  `game.docs` (F16). The installed-CLI job passed at 0.1.43, which is the best evidence
  available from the sandbox; a hosted upload would settle it.
- Whether the `--strict-text-bounds` gate could ever fire for this viewer. It reports
  `total: 0` because the board canvas is an OffscreenCanvas in a Worker (F2). What would
  settle it: a run of `viewer_smoke.mjs` with the measurer installed inside the Worker
  (or a fixture that renders the same frame on a main-thread canvas) showing a non-zero
  `total`.
- The real-episode behaviour of the budget guard, the 640 s stop and the spacing sleep
  under a live Bedrock sidecar (F4's arithmetic is **inferred**, not measured). Every
  CI episode runs with the client `disabled`, so no episode in evidence made a network
  call. A phase-60 hosted episode with `results.llmTurns > 0` would settle it.
- Whether any hosted `game_config` will ever set `dodgeHorizon` away from 8 and split
  the controller from `camper` (F12). Nothing in the shipped manifest can.
