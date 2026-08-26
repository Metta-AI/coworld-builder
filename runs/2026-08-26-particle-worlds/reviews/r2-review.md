# r2 review — particle-worlds

Repo: `Metta-AI/cogame-particle-worlds` at `/workspace/cogame-particle-worlds`, main
`b6b4401ad9db9973387ab011150a73f65ab6e69c` (working tree clean).
Range re-read for the r1 fixes: `99dcaab..b6b4401` (12 commits).
Design note: `runs/2026-08-26-particle-worlds/design.md`, including "## Amendment — r1 review".
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision clause).
Files opened: 41 (server.nim, sim.nim, sim_state.nim, sim_config.nim, sim_types.nim, scoring.nim,
field.nim, motion-adjacent call sites, control.nim, decide.nim, directives.nim, llm.nim,
baselines.nim, roster.nim, broadcast.nim, replays.nim, replay_runtime.nim, global.nim,
replay-viewer/{mpe_replay.nim,config.nims,static_replay.js,static_replay_worker.js},
client/{replay_broadcast.html,chrome_common.js,broadcast_core.js} + the starter's copies of the
same three, tools/ci/{renderer_fixture.html,viewer_smoke.mjs,docker_smoke.sh,policies.json},
tools/replay_summary.py, .github/workflows/{ci.yml,coworld-release.yml},
coworld_manifest_template.json, docs/{PROTOCOL.md,RULES.md}, AGENTS.md, tests/{endings, replay,
field, engine, observation, viewer, identity_privacy, manifest, control}.nim, and CI log
32961166140).
CI evidence pulled fresh: `gh run list`, `gh run view 32961166140 --log`.

Round-1 material read: `r1-verdict.md` only (for the two items round 2 was told to re-verify);
every claim below is re-derived from the tree at `b6b4401`, not carried forward.

---

## Blocking

### F1 — the wall-clock `deadline` stop mutates hashed state outside `sim.step`, and the same loop iteration records that state's `gameHash`; playback cannot re-derive it, and no test covers a deadline-ended replay

- Where: `src/mpe/server.nim:1409-1423` (the stop), `:2030-2070` (the step + `writeHash` in the
  same iteration), `:2240-2249` (`quitAfterFrame` is only consulted here); `src/mpe/scoring.nim:182-201`
  (`bankRound`); `src/mpe/sim.nim:2789-2802` (`finishGame`); `src/mpe/sim_state.nim:161-174,320-333`
  (what `gameHash` mixes); `src/mpe/replays.nim:457-488` (`checkReplayHash`), `:506-517`
  (`stepReplay`), `:261-265` (`replayMaxTick`).
- Observed, traced step by step at `b6b4401` (`src/mpe/server.nim` is **untouched** by the 12 r1-fix
  commits — `git diff --stat 99dcaab..b6b4401` lists no `server.nim`):

  1. `server.nim:1409-1423`, at the **top** of a loop iteration, before anything else that iteration
     does:
     ```nim
     if squadMode and not deadlineHit and
         (getMonoTime() - episodeStart).inSeconds.int >= config.wallClockBudgetSeconds:
       deadlineHit = true
       sim.endReason = ReasonDeadline
       sim.endRule = EndRuleWallClock
       if sim.phase == Playing:
         sim.bankRound(sim.gameTicksElapsed(), EndRuleWallClock)
       ...
       sim.finishGame(Red, isDraw = true)
       quitAfterFrame = true
     ```
     `bankRound` (`scoring.nim:187-201`) does `sim.roundLog.add(entry)` and `inc sim.roundsPlayed`.
     `finishGame` (`sim.nim:2797-2802`) sets `phase = GameOver`, `winner = Red`, `isDraw = true`,
     `gameOverTimer = config.gameOverTicks`. All of it runs **outside** `sim.step`.
  2. All of those fields are hashed. `sim_state.nim:162-174` mixes `ord(sim.phase)`,
     `ord(sim.winner)`, `sim.gameOverTimer` and `mixHashBool(sim.isDraw)`; `:320-333` mixes
     `sim.roundsPlayed`, `sim.roundLog.len` and every field of every `roundLog` entry.
  3. The iteration continues. There is no early exit between `:1423` and the step block: the only
     `continue` in the span is inside `if shouldReset:` (`:1812…1922`), and the turn-boundary block
     at `:1931` is merely skipped because `sim.phase` is no longer `Playing`. Control reaches
     `:2004`, writes an all-zero mask change per cog (`:2011-2012`), then `:2030`
     `for _ in 0 ..< playbackSpeed(liveSpeedIndex)` — at the shipped `speed: 1` that is exactly one
     iteration — calls `sim.step` (`:2042`, GameOver branch: `sim.nim:4175-4179`) and then
     `:2070 replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())`.
     So **exactly one recorded hash** describes a state produced by an unrecorded, server-side
     mutation.
  4. Nothing in the record stream lets playback re-derive it. The stop writes no chat record
     (`:1409-1423` writes none), and chat records are re-applied at playback only into non-hashed
     fields — `replays.nim:402-416` routes any `{`-leading control record to `pushFeedDirective`,
     which `sim_state.nim:358-366` drops unless `k == "directive"`. At playback the sim reaches that
     tick still `Playing` (no banked entry, `roundsPlayed` one lower, `winner`/`isDraw`/
     `gameOverTimer` unset), steps the Playing branch on the recorded zero masks, and
     `checkReplayHash` (`replays.nim:477-486`) — an exact `hash != expected.hash` comparison — sets
     `hashValidationFailed` and `hashMismatchTick = sim.tickCount`.
  5. Refutation attempts, all failed: (a) no `writeHash` guard on phase — `:2070` is unconditional;
     (b) the `fault` path by contrast **breaks before** `writeHash` (`:2055-2060`
     `sim.phase = GameOver; quitAfterFrame = true; break`), so the very same file shows the invariant
     is intended and the deadline path is the one that misses it; (c) the `complete` path does all
     its mutation **inside** the step (`sim.nim:4136-4148` `checkRoundEnd` → `bankRound` +
     `finishGame`, called from `step` at `:4203`), so it re-derives; (d) `sim.gameIndex = gamesPlayed`
     at `server.nim:2086` is the only other out-of-step write on the complete path and `gameIndex`
     is **not** in `gameHash` (grep of `sim_state.nim:158-333`), with `replays.nim:490-504`
     mirroring it at playback.
- The three end paths, side by side (what each writes / what playback recomputes):

  | path | hashed state mutated outside `step`? | last hash written | playback at that tick | outcome |
  |---|---|---|---|---|
  | `complete` / `full_time` | no (`sim.nim:4146-4148`, inside `step`) | after the step (`server.nim:2070`), then `:2096` breaks | same code, same masks → identical | matches; `tests/test_replay.nim:134-161` asserts `hashMismatchTick == -1` |
  | `deadline` / `wall_clock` | **yes** (`server.nim:1418-1422`) | after the step, same iteration (`:2070`) | still `Playing`, no banked round | **mismatch at the stop tick** |
  | `fault` / `sim_fault`\|`host_error` | yes (`:2056-2058`) but **`break` before `:2070`** | the last *complete* tick | never reaches the mutated tick's hash | no recorded hash to mismatch |
- Test coverage: **none for a deadline-ended replay end to end.** `tests/test_endings.nim:71-98`
  reproduces the mutation sequence (`sim.bankRound(ranFor, EndRuleWallClock)` then
  `sim.finishGame(Red, isDraw = true)`) and asserts the *results document*, but never opens a replay
  writer and never compares a hash. The only hash-chain test, `tests/test_replay.nim:134-161`, runs
  `recordEpisode(@[spread,deceive,crypto,tag], 540)` — a four-round episode whose own assertion at
  `:352` is `results.reason == ReasonComplete`. `grep -rn "WallClock\|ReasonDeadline" tests/` returns
  only enum-membership and results-shape uses.
- Checklist item: **2** — "Replaying the recorded events through the sim reproduces the recorded
  per-tick state **frame by frame**, and the viewer derives its display from that same
  re-derivation … A test asserts it."
- Concrete consequence: every `deadline` episode — the ending the design note declares acceptable
  for phase 60 (`design.md:389`, and `results.reason == "deadline"` is accepted by the phase-60
  recipe at `design.md:1064`) — ships a replay whose final recorded hash the viewer cannot
  reproduce, so `#mmwarn` fires (`replay_runtime.nim:101,125` feed `hashMismatchTick` into the
  packet and the state JSON's `mm`) and `tools/wasm_replay_smoke.cjs`'s gate
  (`mpe_mismatch_tick() != -1`, `ci.yml` "Native-to-wasm determinism gate") would fail on such a
  file. That inverts the design's own claim that "a hash mismatch is a real integrity signal rather
  than a rendering nit" (`design.md:1085-1086`).
  *Inferred (not run):* because playback never reaches `GameOver` on such a replay, the end-segment
  chrome that is driven off `ph`/`en` (the endcard, the end-hold) will also not appear on a
  deadline replay's final frame.
- What would settle it: record an episode with `wallClockBudgetSeconds` short enough to stop
  mid-round through the real `openReplayWriter` path (the shape `tests/test_replay.nim:20-114`
  already has), then run `parseReplayBytes` + `initReplayRuntime` + `advanceReplayFrame` to the last
  hash and assert `hashMismatchTick == -1`.

---

## Non-blocking

### F2 — `hold` steers to the round's spawn point, not to where the particle was when the order landed; the shipped prompt, the design note, `docs/RULES.md` and the code's own comment all say otherwise

- Where: `src/mpe/control.nim:376-380`; `src/mpe/field.nim:211-240` (the only writers);
  `src/mpe/sim_types.nim:1926`; `src/mpe/baselines.nim:97-107`; `src/mpe/llm.nim:252-253`;
  `docs/RULES.md:192`; `design.md:771-774`.
- Observed:
  - `control.nim:376-380`:
    ```nim
    of intHold:
      ## The particle's own position at the tick the order was installed, so a
      ## DRIFTING particle is steered back rather than allowed to coast away.
      if seat >= 0 and seat < 4: (sim.holdX[seat], sim.holdY[seat])
      else: (px, py)
    ```
  - `grep -rn "holdX\|holdY" src/ tests/ replay-viewer/` returns exactly four sites: the field
    declaration (`sim_types.nim:1926`), the read above, and the two writes at
    `field.nim:239-240` — inside `placeParticles`, which runs **once per round** from
    `beginRound` (`field.nim:277`), i.e. at spawn on the `spawnRingPx` = 250 px ring
    (`field.nim:216-231`). Nothing writes them at a turn boundary; `server.nim:1943-1975` (the turn
    install) does not mention them.
  - Therefore a particle that has moved and is then ordered `hold` is navigated **back to its round
    spawn point**, up to ~500 px away, at cruise — not braked in place. The shipped system prompt
    says the opposite (`llm.nim:252-253`: "hold = brake and stay where you\nare"), as do
    `docs/RULES.md:192` ("brake and stay where you were when the order was installed") and
    `design.md:772-774`.
  - `baselines.nim:97-107` builds every scripted order from a `baseOrder` whose `intent` is
    `intHold` and whose `targetX/targetY` are the particle's **current** centre — and
    `control.nim:376-380` discards that target for `intHold`. Neither baseline is affected in
    practice: drifter's Alice is anchored (`design.md:218`, `sim.isAnchored`), and drifter's Bob
    holds only before it decodes (`baselines.nim:159-172`), i.e. while still at spawn — which is
    why no test caught it (`grep -rn "intHold" tests/` finds only
    `test_identity_privacy.nim:54`, a fixture order).
- Why non-blocking: the behaviour is legal, bounded and deterministic, and `holdX/holdY` are written
  inside the step path (`sim.nim:3953/3959` → `startGame` → `beginRound`), so the replayed sim
  re-derives them; it falsifies no named checklist item. It is a code-vs-prompt/note divergence of
  the same class as the r1 `shadow`/tag item that was fixed in `llm.nim:254-256`, and it misleads
  every LLM seat that uses `hold` in any mode.

### F3 — the docs claim the viewer cross-checks the `roundcard` record against its own re-derivation; playback discards `roundcard` records entirely

- Where: `src/mpe/replays.nim:402-416`; `src/mpe/sim_state.nim:353-366`; `docs/PROTOCOL.md` §The
  replay ("the viewer cross-checks it against its own re-derivation"); `design.md:1082-1085`;
  `src/mpe/decide.nim:258-263` (the same claim in the record builder's docstring).
- Observed: at playback every `{`-leading chat record is handed to `pushFeedDirective`
  (`replays.nim:412`), which returns immediately unless `node{"k"}.getStr() == "directive"`
  (`sim_state.nim:363-364`). So `roundcard`, `register`, `budget_guard` and `result` records are
  dropped: nothing compares the recorded mark layout / key / roles against the re-derived ones.
  `grep -rn "roundcard" client/ src/mpe/replays.nim src/mpe/broadcast.nim` finds no consumer; the
  only reader in the tree is `tools/replay_summary.py:131-132,170`.
- Why non-blocking: the viewer's *display* already comes from the re-derivation (`broadcast.nim`
  builds the mark/crypto blocks from sim state), which is what item 2 asks for; the missing
  cross-check is a documented-but-absent extra, not a parallel recording. Documentation claim only.

### F4 — after the r1 budget-clock fix, one turn's wall cost can reach `turnSpacingMs + turnBudgetMs`, which the budget guard's headroom covers only by ~2 s

- Where: `src/mpe/decide.nim:365-374, 381-388, 428-447, 458-473`; `src/mpe/sim_config.nim:737-757`;
  `design.md:452-471`.
- Observed / traced at the shipped settings (`turnSpacingMs` 9000, `turnBudgetMs` 10000,
  `attempt1Ms` 6000, `retryMs` 3000 — `coworld_manifest_template.json` variants and schema default
  all 9000/10000/6000/3000):
  - the rate floor sleeps at most `turnSpacingMs` (`:428-431`, `sleep(min(turnSpacingMs,
    turnSpacingMs - since))`), then `turnStart = engine.lastBatchStart` (`:447`) restarts the
    monotonic budget **after** the wait;
  - attempt 1: the budget check at `:466` passes at t=0, one batch with a 6 s transport deadline
    (`:472-495`); attempt 2: the check passes at t≈6000 < 10000, one batch with a 3 s deadline. So
    the **retry is issuable at the shipped settings** — which is the r1 finding's substance — and
    the calls cost ≤ 9 s;
  - worst single turn = 9 s of floor (only when the previous turn's batch finished early) + 9 s of
    calls ≈ 18 s. Because the floor is measured **batch-start to batch-start**, the steady-state
    turn period is `max(9 s, call time) ≈ 9 s`, so 40 turns ≈ 360–400 s — exactly the note's
    arithmetic (`design.md:461-468`), and the note's own worst case treats spacing and budget as
    alternatives rather than additive;
  - the budget guard (`:381-388`) fires when `elapsed + 2 * 10 > 690`, i.e. at `elapsed ≥ 671`, and
    it sets `llmOff` **before** `open` is computed (`:392-395`), so the guard's own turn is already
    scripted. The last turn that can still call therefore starts at `elapsed ≤ 670` and ends by
    ≈ 688 s, inside the 690 s stop (`server.nim:1409-1411`).
- Why non-blocking: item 5 holds — every wait is bounded (two whole-second transport deadlines
  validated at `sim_config.nim:739-757`, the monotonic `turnBudgetMs`, the bounded floor sleep,
  `lobbyJoinTimeoutTicks`, the 690 s stop, the bounded shutdown grace at `server.nim:2309-2312`)
  and the episode settles inside 690 ≤ 720 = 60 % of 1200. Reported because the guard's margin over
  the new worst-case turn is ~2 s rather than the ~10 s the `2 * turnBudgetSeconds` expression
  implies.

### F5 — the new `landmarkMargin` validator is a necessary condition on the larger axis only

- Where: `src/mpe/sim_config.nim:791-812`.
- Observed: `landmarkBox = max(MapWidth - 1 - 2*margin, MapHeight - 1 - 2*margin)` compared against
  `(LandmarkCount - 1) * MinLandmarkSpacingPx` = 360. It rejects `margin = 600` (box 34) and admits
  the shipped `margin = 140` (box 954). A config whose *short* axis is degenerate but whose long axis
  is ≥ 360 still validates and reaches the sampler; that is a bounded outcome now
  (`field.nim:155` cap + `:170-195` lattice sweep, then the sim guard's 120 px assertion at
  `sim.nim:4130-4134` faults), so nothing hangs.
- Why non-blocking: item 5 asks for a bound, and the bound exists; this is a looseness in the
  early-rejection convenience, not an unbounded wait.

### F6 — residue: `DefaultTurnSpacingMs = 5000` is still the in-code default

- Where: `src/mpe/sim_types.nim:516`, consumed by `sim_config.nim:75`; the particle-worlds value
  lives at `sim_types.nim:642` (`DefaultParticleTurnSpacingMs = 9000`).
- Observed: every shipped variant and the `config_schema` default carry 9000
  (`coworld_manifest_template.json` — five variants at 9000, schema
  `{"minimum":0,"maximum":120000,"default":9000}`), and the cert fixture carries 0, so no hosted
  episode can pick up 5000; `tests/test_engine.nim:249-255` pins the shipped value against the
  30 req/min cap. Carried forward from r1 as an observation only; unchanged at head.

---

## Traced and consistent

**Item 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-particle-worlds --branch main -w ci.yml`: run **32961166140**,
  `headSha b6b4401…`, `conclusion success`. All three jobs green with every step `success`,
  including `wasm-viewer`'s "Load the bundle in a real browser", "Worst-case renderer fixture at
  360 / 620 / 1280 px" and "Native-to-wasm determinism gate" (no `continue-on-error` in `ci.yml`).
- `git log -p 99dcaab..b6b4401 -- tests/` read hunk by hunk: five test files touched, all additive
  except three changes I checked individually —
  (a) `tests/test_engine.nim:169-179` `check fallbacks >= 4` → `== 4` plus per-seat uniqueness and
      `attempt == 2`: a **tightening**;
  (b) `:201-207` `check throttled >= 4` → `== 4` plus `attempt == 1`: a tightening;
  (c) `b6b4401` replaces `check recordedWindows().len == 8` inside the *newly added* rate-floor test
      with record-stream assertions (`attempt: 2`, `cause: "timeout"`, no budget-exhausted detail,
      ×4) while keeping both timing bounds. I verified the replacement is not weaker at the source:
      `decide.nim:529` sets `attemptsSpent[seat] = attempt + 1` **only inside the per-attempt
      `except` branch**, which is reachable only after `makeRequests` (`:494`) has run for that
      attempt; the budget-exhaustion break at `:466-471` deliberately leaves `attemptsSpent` at 0 →
      `max(1, …)` = 1 (`:563-564`). So `attempt: 2` is proof the retry batch was issued — a
      client-side fact, where the deleted assertion counted server-side handler windows that curl
      can abandon.
  No `skip`/`xfail` added, no test file deleted, no tolerance widened.

**Item 2 (the parts that hold).** `tests/test_replay.nim:134-161` records a real four-round episode
through `openReplayWriter`, re-parses it with `parseReplayBytes`, drives `initReplayRuntime` +
`advanceReplayFrame` and asserts `player.hashMismatchTick == -1`; the viewer runs the *same*
module (`replay-viewer/mpe_replay.nim:1-4` imports `mpe/[…, replay_runtime, replays, sim]`) and
builds its packet from the re-simulated sim (`replay_runtime.nim:83-138`). The chat stream cannot
move the chain (`replays.nim:402-416` + `sim_state.nim:340-351`, `installSymbol` explicitly
non-hashed). The `complete` and `fault` paths re-derive (F1's table). CI's determinism gate printed
`ok: loaded replay.json, advanced 300 frames`.

**Item 3 — static viewer.** `coworld_manifest_template.json` `game.replay_viewer ==
{"bundle": "static-replay-viewer"}` (parsed, not grepped); `tools/build_replay_viewer.sh` present,
mode `100755`, and `ci.yml:236-248` asserts both `-f` and `-x` before invoking it **by path**; the
bundle's only network call is `fetch(message.replayUrl, {credentials:'omit', mode:'cors'})`
(`static_replay_worker.js:113-116`). The inherited `/client/replay` dev route in `server.nim` is
unchanged from the starter and is not the platform's viewer path.

**Item 4 — both name spaces.** `tests/test_identity_privacy.nim:16-66` asserts a sentinel policy
address is absent from every seat view and both LLM messages while all four aliases are present, and
that no seat sees another seat's `note` or prompt. Spectator side: the CI smoke's scorebug readout
carries the real names (`{"loaded":true,…,"scorebug":"○ P1 GOOD 0.649 … ○ P4 GOOD 0.649 …"}`).
`decide.nim:130-158` builds `agents`/`radio` from `sim.cogAlias(i)` only.

**Item 5 — degrade-never-hang.** See F4 for the arithmetic. Additionally: the landmark sampler is
now bounded in form (`field.nim:119-131` `MaxLandmarkDraws = 4000`, `:155` `while attempts <
MaxLandmarkDraws`, `:170-195` RNG-free lattice sweep). Determinism of the change: the loop body and
its RNG consumption are byte-identical to the previous `while true` up to the cap, so any seed that
previously settled in < 4000 draws draws the same numbers in the same order;
`tests/test_field.nim:12-42` runs 10 000 seeds asserting four marks, all non-wall, all in the margin
box and all ≥ `MinLandmarkSpacingPx` apart — which the lattice fallback would not reliably satisfy —
and `tests/test_field.nim:167-186` re-checks that one seed reproduces every draw across four
`reseat`s and a different seed does not. Residual (disclosed): a seed needing > 4000 draws would now
produce a *different* layout than the old unbounded loop; unreachable on the shipped board, where
the previous behaviour was a spin.

**Item 6 — `num_agents`.** 4 in all five variants and in `certification.game_config`
(`len(certification.players) == 4`, `len(game_config.players) == 4`); `config_schema.num_agents`
is `integer 4..4, default 4`. `tools/ci/docker_smoke.sh:106-152` enforces all four invariants plus
the independent `SMOKE_SEATS` cross-check, each with a `SEAT-COUNT FAIL:` prefix.
`grep -c "SEAT-COUNT FAIL" ` over the **full** log of run 32961166140 = **0**; the smoke printed
`game=particle-worlds seats=4 …` and `smoke OK: seats=4 results=882B replay=31136B reason=complete`.

**Item 7 — scripted baseline plays a legal full episode.** `tests/test_control.nim` (legality sweep
and the all-scripted four-round episode) and `tests/test_endings.nim:50-63`
(`reason == complete`, `endRule == full_time`, `roundsPlayed == 4`) are unchanged in this range and
green.

**Item 8 — LLM reply handling.** One `RequestBatch` per turn built for all open seats and issued via
`client.curl.makeRequests(batch, deadlineMs div 1000)` (`decide.nim:474-495`) — no per-seat call
site anywhere; `tests/test_engine.nim:118` ("all four seats' calls go out in ONE parallel batch")
covers the simultaneous-decision clause. Retry exactly once (`while … attempt < 2`, `:463`), the
throttle fail-fast skips it (`:535-542`), and the tail block writes **one** authoritative record per
seat-turn (`:545-564`) stamped with the attempts actually spent. Countability re-derived: the
`no_credentials`/`budget_guard` record at `:406-414` and the tail record at `:563` are mutually
exclusive (the former is in the `elif isLlm` branch that never joins `open`), every seat's directive
is re-assigned every turn, and `server.nim:1950-1957` increments `fallbackTurns` once per
`dsFallback` seat-turn — so record count == `sum(results.fallbackTurns)`, the invariant
`docs/PROTOCOL.md:194` now states.

**Item 9 — rune-safe truncation.** `directives.nim:63-70` is the single shortening primitive
(`runeLen`/`runeSubStr`); every cap routes through it (`:114` note 160, `decide.nim:239` detail 200,
`:253` policy 48, `directives.nim:355` the 900-rune record shrink, `llm.nim:267` prompt 4000).
`parseSymbol` (`directives.nim:72-91`) takes the first **rune**. Unchanged in this range.

**Item 10 — manifest.** Parsed: `game.docs.readme = {"type":"text","value":…}` (7 207 chars) and
three pages each `{id,title,content:{type:"text",value}}` (rules 12 036, protocol 12 946,
commanding 6 595); `game.protocols` carries both `player` and `global` in object form. (Both
protocol values are the same inlined `docs/PROTOCOL.md`; item 10 asks for both keys in object form,
which is satisfied.) `results_schema` has exactly 22 properties matching `design.md:998-1027`,
`additionalProperties: false`; `config_schema` is `additionalProperties: false` with every array
property bounded; `episode_timeout_minutes: 20`; `game.runnable.env.ANTHROPIC_API_KEY_URI ==
secret://coworld/particle-worlds/anthropic_api_key`.

**Item 11 — legible at 360 px.** `client/replay_broadcast.html:4152-4157`
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` —
byte-for-byte the rule the starter carried in its own appended block
(`/workspace/starters/coworld-ctf/client/replay_broadcast.html:4369-4374`), which the fork removed
with the paintball block and re-declared. Labels hidden under `.tiny` at `:4196-4198`; the
breakpoint `stage.classList.toggle('tiny', boardW <= 620)` (`:4093`) is the starter's line verbatim.
The r1 note-wrap fix reads
`.feed-row.mpe-note-row { white-space: normal; max-width: calc(228 * var(--u)); … }` (`:4377-4382`)
with `#stage.tiny …{ max-width: calc(190 * var(--u)); }` (`:4383`) and
`overflow-wrap: anywhere` (`:4384`) — and 228u / 190u are exactly `#killfeed`'s own reserved widths
(`:481` and `:1261`), i.e. the note wraps **inside the band the layout already reserves** rather
than being shortened, which is what item 15's second bullet asks for. The class actually lands:
`mpeDirectives` passes `'mpe-note-row'` to `feedRow` (`:4547-4550`), and `feedRow` puts it on the
row (`:4444-4449`).

**Item 12 — release order and scaffold.** `coworld-release.yml`: "Build the Coworld manifest"
(:153) → "Certify locally" (:167, now with `--timeout-seconds 300` at :178) → "Upload the policies"
(:210) → "Upload the Coworld" (:308) → "Put the Coworld secret" (:346). All three workflows present;
`tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` both mode `100755`.
`tools/ci/policies.json` declares four policies, two `PLAYER_PROMPT` champions (cipher carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) and two `PLAYER_SCRIPTED` fillers. The
three-name placeholder grep over the five files returns nothing → the gate exits 0.

**Item 13 — viewer executes.** Run 32961166140 `wasm-viewer` is green **including** the browser
step, which printed `{"loaded":true,"ms":1606,…}` and `soak: 12s of playback kept advancing
("0 / 1035" -> "241 / 1035" -> "289 / 1035")`; the job declares `needs: docker-smoke` (`ci.yml:224`)
and downloads the `smoke-replay` artifact. `data-replay-loaded` is set in the `'loaded'` branch of
the shell's own `onWorkerMessage` (`static_replay.js:161`), `data-replay-error` in `showFailure()`
(`:14-20`). Link flags and bootstrap are one starter's: `replay-viewer/config.nims:48-53` has
`ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, the `_mpe_*` `EXPORTED_FUNCTIONS` list and
**no** `MODULARIZE`/`EXPORT_NAME`, while the worker uses `var Module = {}` +
`Module.onRuntimeInitialized` (`static_replay_worker.js:8,188`) and
`importScripts('./wire_constants.js','./broadcast_core.js','./mpe_replay.js')` (`:239`) — the
matched non-modularized pair.

**Item 14 — chrome provenance.** `diff` against `/workspace/starters/coworld-ctf`:
`client/chrome_common.js` differs in exactly one line (`:72`, `window.CTF_WIRE` →
`window.MPE_WIRE`) — the patch now recorded in `design.md`'s "Amendment — r1 review" and in
`docs/plans/2026-08-26-particle-worlds-design.md`; `client/broadcast_core.js` differs in exactly one
line (`:49`). The page is the starter's plus one appended block under
`particle-worlds additions to the inherited coworld-ctf chrome` (`:4125`). I diffed the CSS above
the banner (`lines 7-1286` vs the starter's `7-1460`): **172 removed lines, 1 added line**, and the
single addition is a comment word ("MPE-Doubles"). The removals are exactly the note's list —
`#viewpanel`, `#zoombar`/`#zoom-*`/`.zbtn`, `#minimap*`, `body[data-noviewpanel] #viewpanel`,
`.ec-heart*`, and the `.beat-marker.kill/.steal/.return/.capture` rules — with the paintball block
removed wholesale (it was the starter's own appended `<style>`). Beat CSS in the new block covers
exactly the five emitted kinds (`roundstart`, `firstword`, `onpoint`, `tag`, `roundover`) and
`button.beat-marker` is re-declared, so markers stay labelled buttons. `#endcard { bottom:
var(--band, 0px) }` and `relayout()`'s `:root` writes (`--hudscale`, `--topband`, `--band`,
`:4091-4097`) are the starter's, unmodified.

**Item 15 — every drawn string fits its frame.** `--strict-text-bounds` is on both smoke steps
(`ci.yml`, "Load the bundle…" and the fixture step). No client-side code draws canvas text at all:
`grep -rn "fillText" client/ replay-viewer/` returns **nothing** — the board is sprite pixels
composited server-side and all chrome text is DOM, which is why the real replay's smoke printed
`canvas text: 0 drawn` and why the fixture exists.
I re-read `tools/ci/renderer_fixture.html` end to end against the claim that it executes the shipped
page:
  - it `fetch('./index.html', {cache:'no-store'})` (`:246`), refuses a page without the
    particle-worlds banner or the `chrome_common.js` splice (`:251-257`), splices one `<script>`
    after `<head>` and loads the result via `iframe.srcdoc` (`:510`). CI copies the fixture **into**
    `dist/static-replay-viewer/` and serves that directory (`ci.yml`, the `cp` + `python3 -m
    http.server 8731` lines), so `./index.html` is the shipped page and the srcdoc document's
    relative `<script src="./wire_constants.js|./chrome_common.js|./static_replay.js">` (spliced by
    `Dockerfile.replay-viewer:31-34`) resolve against the same directory.
  - the only stub is the transport: the hook defines a `window.MpeStaticReplay` **getter** returning
    `{createCore}` and a setter that captures the real assignment (`:122-127`), so
    `replay_broadcast.html:1802-1815`'s `replayAdapter.createCore(coreConfig)` gets the stub and the
    page's own `coreConfig` is captured (`:119`). The worst-case frame is then delivered through
    `config.onText(...)` (`:420,423,427`) — the identical entry point the real worker uses
    (`static_replay.js:147` → `coreConfig.onText` → `onFrame` at `replay_broadcast.html:1852`). So
    the frame is fake and the layout, CSS, feed insertion, plate/rail/radio/crypto rendering and
    `relayout()` are all the shipped page's.
  - self-checks hold: `selfCheckInputs` (`:462-473`) fails unless the note is exactly 160 runes and
    every symbol exactly one rune — and the literal at `:139-142` is **160 runes** ending in a
    4-byte emoji (verified by counting). At each width it requires **four** `#killfeed .mpe-note`
    nodes whose `textContent === NOTE` (`:433-445`) — the page's `MAX_FEED` is 4
    (`replay_broadcast.html:3402`), so four full-cap notes is the feed's tallest possible state —
    plus `scrollWidth > clientWidth` clipping detection on each, plus a floor of 8 laid-out text
    runs. Widths are `[360, 620, 1280]` (`:143`) with a different `turn` per width so the page's
    `seenDirective` dedup (`:4537-4545`) does not swallow the later rows. Any violation sets
    `data-replay-error`, which `viewer_smoke.mjs:503` fails on immediately.
  - CI printed `fixture canvas_text: total=302 never_inside=0 outside=0`, and `ci.yml` **asserts**
    `total > 0` and `never_inside == 0` in a python block rather than merely printing them.
  - the board-sprite side of item 15 is separately guarded in the sim:
    `global.nim:3965-3987` (`shoutBubblePlacement`) flips the bubble below the particle when it does
    not fit above and clamps both axes into the board rect, and `addSeatSymbolBubbles`
    (`:5381-5434`) renders silence as an em dash rather than an empty bubble.

**Other spot-checks with no regression found.**
- `decide.nim:163-173` computes `this_round_so_far` with `sim.tagRoundPermille(scoreSeat, elapsed)`
  in a `tag` round, matching `broadcast.nim:1049-1055`'s live term exactly; pinned from both sides
  by `tests/test_observation.nim:182-203`.
- `tests/test_replay.nim:359-368` asserts one directive per seat per `(round, turn)` group
  (`count == FixtureSeats`), and `:276-311` exercises the `onpoint` detector and its derived event.
- `grep -rn "CTF_\|ctf_" src/ client/ replay-viewer/` (excluding the string `coworld-ctf`) returns
  nothing.
- `results.bumps`' last-round scope is now stated in code (`roster.nim:711-717`) and in
  `docs/PROTOCOL.md`; the manifest is regenerated from the docs and `ci.yml` runs the generator with
  `--check` ("Assert the manifest is regenerated from the docs", green).

---

## Could not determine

- Whether a `deadline`-ended replay's mismatch is the *only* consequence, or whether the wasm shell
  additionally degrades: F1's re-derivation trace is from the code, and the sandbox has no Nim,
  Docker or emsdk, so I could not record a short-`wallClockBudgetSeconds` episode and run
  `mpe_frame` over it. What would settle it: the test described at the end of F1, plus one
  `tools/wasm_replay_smoke.cjs` run over such a file.
- Whether a `fault`-ended replay plays cleanly. *Inferred, untested:* playback steps one tick past
  the last recorded hash inside the same frame budget (`replays.nim:940-944`, then `:463-465` only
  stops playback on the *following* call), so on a `sim_fault` replay the guard should raise
  `SimGuardError` out of `stepReplay` → `advanceReplayFrame` → `mpe_frame`, which catches
  `Exception` and returns `-1` (`mpe_replay.nim:95-112`) → `data-replay-error`. No test or CI
  evidence exercises a fault replay; a recorded fault fixture run through `advanceReplayFrame` would
  settle it. Not a checklist violation on its own reading (item 2 concerns re-derivation of recorded
  state; the fault path records no unre-derivable hash).
- Whether any hosted `deadline` episode has occurred: no Observatory/league evidence was consulted
  (out of scope for this brief), so F1's impact is argued from the code and the design's declaration
  that `deadline` is an accepted phase-60 outcome, not from an observed hosted replay.
