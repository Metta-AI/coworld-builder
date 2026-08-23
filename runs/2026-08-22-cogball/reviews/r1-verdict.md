blocking: 0

# r1 verdict — cogball

Head: `e42bd4ed557c017dbec43808b516117a9341b8fc` (main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** — the repo, the design note, the
workflows, the manifest, the smoke script, the CI run and the test history were all read and my
own checklist pass was complete before `r1-review.md` was opened; `r1-fixes.md` was opened last,
only for the audit table at the bottom.

Judged clone: `/workspace/scratch/judge-cogball` at the head sha.
CI evidence: run **32618552227**, conclusion `success`, `headSha e42bd4ed…`, jobs
`test` / `docker-smoke` / `wasm-viewer` all `success`
(`gh run view 32618552227 -R Metta-AI/cogame-cogball --json conclusion,headSha,status,jobs`).
`grep -c "SEAT-COUNT FAIL"` over the full 4311-line run log → **0**.

## Standing blocking findings

None.

## Refuted / dismissed at head

The review was written at `812c661d`, 42 commits behind this head. The reviewer's own summary
said none of the 38 findings falsified a named checklist item; I re-checked each at the current
head anyway. **All 38 are dismissed**: every one is either fixed by a commit between the two
shas (`git log 812c661d..e42bd4e` names the finding in each subject line) or was a
note-vs-code description gap now recorded in `docs/plans/note-divergences.md` — either way, not
reproducible from the tree as it stands.

### Fixed in code/tests between 812c661d and head (cannot be reproduced now)

- **F6 → REFUTED at head** — `broadcast.nim:133-139` derives the `drop` beat from
  `sim.lastDropTick` (`sim.nim:225` sets it inside the hashed step), not from a counter
  transition; the spurious-beat path is gone (commit `0f59984`).
- **F7 → REFUTED at head** — `broadcast.nim:145-150` gates `kickoff` on `sim.lastKickoffTick`
  (`sim.nim:192`), which `kickoffReset` sets at match start too (commit `cf831ed`).
- **F9 → REFUTED at head** — `decide.nim:360-367`: the per-attempt allowance is **floored**
  (`max(1, allowedMs div 1000)`), realised worst case 6 s + 2 s = 8 s inside the 9 s cap
  (commit `48f9e3a`).
- **F10 → REFUTED at head** — `tools/replay_summary.py:228-234,256-257`: `fallbacks` counts
  TURNS (`source == "fallback"` directives); per-attempt records are reported separately as
  `fallbackAttempts` (commit `d96cd14`).
- **F11 → REFUTED at head** — `decide.nim:383-387`: lowercased match on both `"timeout"` and
  `"timed out"` (commit `8247b87`).
- **F13 → REFUTED at head** — `decide.nim:328-337`: a client that had credentials rejected
  records `cause: "transport_error"`, not `no_credentials` (commit `e241932`).
- **F14 → REFUTED at head** — `server.nim:820-842`: the whole loop is inside `try`; the handler
  calls `sim.hostErrorStop()`, writes the result record and the artifacts best-effort, and
  re-raises. `fault/host_error` is reachable (commit `ad5fe6c`; asserted in
  `tests/test_engine.nim`).
- **F15 → REFUTED at head** — `shouldAbortFiniteMatch` no longer exists
  (`grep -rn` over `src/ tests/ tools/ replay-viewer/` → no hits; commit `4741275`).
- **F16 → REFUTED at head** — `server.nim:448-452`: `episodeStart = getMonoTime()` is taken
  **before** the board bake; `server.nim:502-507` logs the bake as charged against the budget,
  and `docker_smoke.sh:236-242` surfaces the line on success — CI log:
  `board render caches baked in 104 ms (charged against wallClockBudgetSeconds=180)`
  (commit `5d1343a`). This also settles the reviewer's first "could not determine".
- **F17 → REFUTED at head** — `cogball_player.nim:33-40,112-116`: `ReceiveTimeoutMs = 120_000`
  bounds the receive; a silent dead pod ends the process cleanly (commit `ba7d9d3`).
- **F18 → REFUTED at head** — the wall-clock stop is inside the per-tick loop
  (`server.nim:698-707`), so a raised live speed cannot coarsen it (commit `e553b5c`).
- **F19 → REFUTED at head** — `directives.nim:175-209`: `capRecord` shrinks an over-long record
  **structurally** (parse, clip string values to a halving budget, re-serialize), so the result
  is always parseable JSON; the blind rune clip is only the non-JSON fallback (commit
  `de2fbd5`; escape-saturated case tested in `tests/test_directives.nim`).
- **F20 → REFUTED at head** — `server.nim:538-544`: `recordAndWrite` (the server's one write
  path, used for `register` and `result` too) caps via `capRecord` (commit `4778304`).
- **F21 → REFUTED at head** — `pitchRgba` no longer exists (grep → no hits; commit `11c31ff`);
  the fixture was re-recorded (`d775fbc`) and the wasm gate is green at head.
- **F22 (both halves) → REFUTED at head** — `replay_summary.py:69-70` decodes strictly first and
  counts repairs; `:149` carries the real FNV-1a 64-bit offset basis `14695981039346656037`
  (commits `a82357b`, `a52a5e2`).
- **F23 → REFUTED at head** — `sim_config.nim:145` reads only `"num_agents"`; the `numAgents`
  camelCase config alias and the test allow-list that hid it are gone (commit `89b4c9f`;
  `numAgents` surviving in `sim_types.nim:330` is the Nim field name, and in
  `replay_summary.py:244` an output key of the summary's own vocabulary — neither is a config
  key).
- **F24 → REFUTED at head** — `tests/test_server.nim:194-212` forces `showPlayerLabels = true`
  and asserts no board label carries a real name (commit `5a034f2`).
- **F25 → REFUTED at head** — `tests/test_engine.nim:436-497` drives `declarePlayerFailure`
  against a real `file://` target, asserts the failure JSON shape and plays the match to
  `full_time`; CI log: `ok  a never-connecting seat is declared and the match reaches
  full_time` (commit `ed00a56`).
- **F26 → REFUTED at head** — `tests/test_engine.nim:236-283` plays a budget-guarded episode
  out to `complete/full_time` (commit `bec93e1`).
- **F27 → REFUTED at head** — `tests/test_engine.nim:507-571` actually trips
  `physicsGuardTripped`, asserts `fault/sim_fault`, 0.5/0.5, and reads the partial replay back
  (commit `597d01c`).
- **F28 → REFUTED at head** — `tests/test_physics.nim`: the wall-bounce and kick assertions are
  now exact (`sim.ball.vy == v`, `sim.ball.vx == ball`, `sim.robots[0].vx == reaction`) — the
  tolerances were replaced by *stronger* assertions, not weakened (commit `01beeb8`).
- **F29 → REFUTED at head** — `tests/test_replay.nim` counts kicks/shots off the re-derived
  event stream and cross-checks them against `sim.stats` (commit `a243bd4`).
- **F30 → REFUTED at head** — `registrationOf`/`parseRegistration` are exported
  (`server.nim:377-436`) and `tests/test_server.nim` asserts the not-echoed / redacted-record /
  prompt-never-in-replay contract on the server's own functions (commit `ccc3093`). This also
  settles the reviewer's fourth "could not determine".
- **F31 → REFUTED at head** — the grid harness is committed and executable:
  `tools/tune_baselines.nim`, `tools/tune_baselines.sh`, results in
  `docs/tuning/baseline-grid.md` (48 matches per row, both sides played) (commit `ae14635`).
  This settles the reviewer's second "could not determine" and checklist item 7's
  "tuned, not guessed".
- **F33 → REFUTED at head** — `baselines.nim:186`: the deepest swarm robot reports `roleBack`
  in both halves; only the intent varies with `guard` (commit `21d79fd`).
- **F34 → REFUTED at head** — the computed-and-discarded `third` is gone (commit `fa978e5`).
- **F35 → REFUTED at head** — `control.nim:228-238`: `hold`/`press` clearances aim at
  `targetGoalX(seat)` (up-field), not the centre spot (commit `b4e1cf9`; fixture re-recorded in
  `d775fbc`).
- **F36 → REFUTED at head** — `client/replay_broadcast.html:2725`:
  `stage.classList.toggle('tiny', boardW <= 640)` — the toggle now sits exactly at the
  checklist's 640 px; `tests/test_viewer.nim:42-48` asserts it (commit `da3dfda`).
- **F37 → REFUTED at head** — `grep -n '/client/replay' client/broadcast_core.js
  client/league_replayer.html` → no hits; `tests/test_viewer.nim:207-232` asserts no
  static-bundle source names the pod route (commits `d2c5df7`, `7f58fd4`).
- **F38 → REFUTED at head** — `docs/plans/2026-08-22-cogball-design.md:1-12` opens with
  "SUPERSEDED, HISTORICAL" and points at the accepted v2 note (commit `049940f`).

### Note-vs-code description gaps, now recorded (no code defect existed)

- **F1, F2, F3, F4, F5, F8** — all six are documented with reasons (and for F2, measurements) in
  `docs/plans/note-divergences.md` (§"Pass and interception attribution…", §"The realised goal
  mouth…", §"StalemateBox is a HALF-width", §"kickoff freeze zeroes the BALL", §"jitter stream
  drawn twice", §"neutral drop clears more state"). None falsifies a checklist item: the sim
  cannot read a directive (F1) because pass/save counters are hashed — that is the determinism
  discipline item 2 depends on; the rest are geometry/bookkeeping descriptions. The v2 design
  note is frozen by policy (`AGENTS.md` §Divergences); the divergence file is the sanctioned
  mechanism, and a divergence not in it is defined as a bug.
- **F12** — `llm.nim:131-140`: the Bedrock body deliberately never carries
  `output_config.effort`, and the docstring now says why (strictly more conservative than the
  note's rule; the default Bedrock list leads with a haiku-4-5 profile where the field is
  forbidden anyway). Conservative-side divergence; no checklist item touches it.
- **F32** — the `back` target y divergence is recorded with its measurement in
  `docs/tuning/baseline-grid.md` §"The `back` target, measured" (midpoint-y loses the sweep:
  24-12-12/+17 for the shipped form vs 19-15-14/0 for the note's). The note's number was a
  design-time guess; the committed value has a run behind it, which is what item 7 asks.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run 32618552227 `success` at `e42bd4ed`, jobs test/docker-smoke/wasm-viewer all `success`. History: `433da18` deleted the round-1 moba-lineage tree wholesale (operator-directed starter switch recorded in the commit message — an implementation replacement, not a dodged test; the Nim suites in `tests/` replaced it in `51cd7ec`). Every test-touching commit since replaces assertions with **stronger** ones (F28: ±12.5%/±33% → exact equality; F29/F30: proxies → the real stream/functions). `git log -p 433da18..HEAD -- tests/` shows no added skip/xfail/`when false`, no widened tolerance, no removed file. |
| 2 Replay re-derivation | **pass** | `tests/test_replay.nim:209-238` re-simulates from config + mask log and asserts **every** recorded hash reproduces; `replays.nim` `stepReplay`/`checkReplayHash` compare per tick; the viewer (`replay-viewer/cogball_replay.nim`) imports the same `cogball/sim` and re-steps — no parallel recording. Cross-build half: wasm-viewer job, log `ok: loaded cogball-679961.bitreplay, advanced 300 frames`. |
| 3 Static viewer | **pass** | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 755, invoked by path in `ci.yml:260` with an explicit `test -x` gate (`:249-256`); the only network call in the bundle is `static_replay_worker.js:113` `fetch(message.replayUrl)` (the S3 object); no `/client/replay` in any bundle source (`tests/test_viewer.nim:207-232`; my grep confirms the string survives only in `server.nim`'s live-pod embed, a release-workflow *rejection* message, and docs). |
| 4 Both name spaces | **pass** | `tests/test_server.nim:153-227`: composed LLM message and player-stream labels carry no `player.address` even with `showPlayerLabels` forced true; chrome roster (`chrome_common.js:138-146` reads `state.teams[].policies`/roster) and `results.names` carry the real names. |
| 5 Degrade-never-hang | **pass** | Batch deadlines floored + outer monotonic `turnBudgetMs` (`decide.nim:290-293,352-367`); budget guard (`decide.nim:297-306`); wall-clock stop per tick (`server.nim:698-707`, default 690 ≤ 720 = 60% of 1200, asserted per variant in `tests/test_manifest.nim:41`); lobby wait bounded (`server.nim:677-686`); frame limiter sleeps 1–2 ms slices with exit conditions (`server.nim:340-360`); player connect bounded at 90 s and receive at 120 s (`cogball_player.nim:24,33,112`); host-error path still writes artifacts (`server.nim:820-842`). |
| 6 num_agents | **pass** | `num_agents: 2` in variants `default` and `sprint` and in `certification.game_config`; `len(certification.players) == len(certification.game_config.players) == 2` (read from the JSON). `docker_smoke.sh:102-143` enforces all four invariants + the independent `SMOKE_SEATS` cross-check (`:47,133-143`), each exiting with `SEAT-COUNT FAIL:`. Run log: 0 occurrences of `SEAT-COUNT FAIL`; `smoke OK: seats=2 … reason=complete`. |
| 7 Scripted baseline full episodes, tuned | **pass** | `tests/test_baselines.nim:125-142`: formation-vs-swarm at seed 679961 asserts `reason == reasonComplete`, `full_time`/`mercy`, formation wins, not 0–0; `:39-57`: 500 states × both baselines produce schema-legal bounded orders and legal mask bits. Grid harness committed: `tools/tune_baselines.{nim,sh}` + `docs/tuning/baseline-grid.md`. |
| 8 LLM reply handling | **pass** | `llm.nim:193-205` `extractJsonObject` (prose/fence tolerant); `decide.nim:349-414`: exactly one retry (`attempt <= 2`), then `formation` fallback with a `fallback` record (`cause`, capped `detail`) and `fallbackTurns` in results; `replay_summary.py` counts fallen-back turns for phase 60. |
| 9 Rune-safe truncation | **pass** | `directives.nim:50-64` `clipRunes` (runeLen/runeSubStr, no byte slicing) used on every replay-bound string (note 160 / say 48 / policy 48 / detail 200 / prompt 4000); `capRecord` structural ≤900; `tests/test_directives.nim:129-176` feeds a 4-byte emoji straddling the cap and asserts rune-boundary + strict round-trip; `tests/test_replay.nim:12,249,303` forces non-ASCII say/label through a real episode and asserts `isValidUtf8` and strict `json.loads`. |
| 10 Manifest validates | **pass** | `game.docs.readme == {"type":"text","value":…}` (5472 chars) + 3 pages each `{"id","title","content":{"type":"text","value":…}}` (9778/7545/6871 chars); `game.protocols` carries both `player` and `global`. |
| 11 Viewer legible at 360 px | **pass** | `client/replay_broadcast.html:152`: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden;` — the checklist's rule verbatim; `:2725` `.tiny` toggle at `boardW <= 640`; `:160-161` hides the plate stats under `.tiny`; all asserted in `tests/test_viewer.nim:37-51`. |
| 12 Release order and scaffold | **pass** | `coworld-release.yml` step order: build (`:159`) → certify (`:168-173`) → upload-policies (`:207-235`) → upload-coworld (`:309`) → secret put (`:343-358`); `ci.yml`'s docker-smoke builds the image in the same job (`:202`) before the smoke (`:213`); three workflows present; `docker_smoke.sh` mode 755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the placeholder gate run verbatim exits clean (grep for the three names → no hits). |
| Parallel batch (simultaneous-decision rule) | **pass** | `decide.nim:344-347` collects both seats into one `calls` seq, `:367` issues one `engine.batch(...)` per attempt, `curlyBatch` maps it onto a single `curl.makeRequests` (`:212-244`); `tests/test_engine.nim:45-66` asserts the two in-flight windows intersect; CI log: `ok  both seats go out in ONE parallel batch and both directives install`. |

## Fixer report audit

Read only after the pass above was written. Spot-audited against my own head verification:

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F9 | floored per-attempt deadline, `decide.nim:367` | floor at `decide.nim:367`, comment at `:360-366` | yes |
| F14 | host-error reachable, artifacts best-effort, `server.nim:820-842` | try/except wraps the loop, `hostErrorStop` called, artifacts written, re-raise | yes |
| F19 | structural cap, `directives.nim:158,175` | `clipJsonStrings` + halving-budget shrink, always-parseable | yes |
| F23 | alias deleted, `sim_config.nim:145` | only `"num_agents"` read; allow-list gone | yes |
| F25–F27 | end-to-end engine tests added | all three present and green in the CI log | yes |
| F31 | harness committed + sweep recorded | `tools/tune_baselines.{nim,sh}`, `docs/tuning/baseline-grid.md` | yes |
| F36 | toggle moved to 640 | `replay_broadcast.html:2725` | yes |
| F37 | pod route out of bundle sources | grep clean; `test_viewer.nim:207-232` | yes |
| F28 | assertions made exact, claimed under item 1 | deleted tolerances replaced by `==` assertions — a strengthening | yes |
| counts | 31 fixed + 8 evidence-only (39 rows, F22 split), 0 disputed | matches my per-finding disposition exactly | yes |

## Non-blocking observations (mine, not tied to a checklist item)

- The certification fixture's `wallClockBudgetSeconds` is 180 for a 1200-tick offline episode —
  generous but harmless; the smoke completed in ~60 s of container time with `reason=complete`.
- `results.json` in the smoke is 300 B against a schema of 15 keys — consistent with the compact
  serializer; nothing to act on.

## Verdict

The review register was accurate for the sha it examined and is fully discharged at this head:
38/38 findings dismissed (fixed or documented), no finding stands against a named checklist
item, and my independent pass verifies all twelve items plus the parallel-batch rule from the
tree and cited CI evidence. Nothing was unverifiable from the sandbox.

BLOCKING: 0
