blocking: 0

# r3 verdict — minigrid
Head: 85a2f68ce775aa441d4a633fdb672ff93b5e9140   Checklist: /workspace/coworld-builder/prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

No `r3-review.md` and no `r3-fixes.md` exist under `runs/2026-08-28-minigrid/reviews/` — this
round judged the v2.1 commit (`8a78a6bf..85a2f68c`, 27 paths) directly against the design note
(v1 + Addendum v2 at design.md:1975 + Addendum v2.1 at design.md:2853) and the checklist. The
builder's claims audited below are the commit message of 85a2f68c and the coordinator brief.
I did not read any prior-round review artifact before forming this read.

## Standing blocking findings

None.

## Refuted

No reviewer findings existed to refute (empty round — full independent checklist pass run
instead, below).

## v2.1 commitments, verified at head

1. **Ladder 18000/12000/30000/11000 everywhere.** `src/minigrid/sim_config.nim:86-89`
   (`attempt1Ms: 18000, retryMs: 12000, turnBudgetMs: 30000, turnSpacingMs: 11000`),
   `config.json:41-44`, both manifest variants (`coworld_manifest_template.json:689-693` and
   `:742-746`), and the cert fixture (`:807-810` — previously its own 2000/1000/3000/0 ladder,
   now the shipped one with `wallClockBudgetSeconds: 240` kept). The cert change is safe: the
   fixture is all-scripted, scripted seats never enter the batch (`decide.nim:222-228`), and
   the spacing sleep is only reached when `open.len > 0` (`decide.nim:255-268`), so an
   all-scripted or credential-less episode pays no 11 s floor; the guard bound holds at 240 s
   (158 + 30 + 21 = 209 ≤ 240). The divergence removal is documented in
   `docs/PORTING-MINIGRID.md:131-137`.
2. **Test 51 replacement is a legitimate spec change, not a loosening.** Old form
   `maxTurns × turnBudgetMs/1000 + 121 ≤ wallClockBudgetSeconds` is unsatisfiable by any ladder
   covering the measured three-seat p90 of 10.1 s (it needs `turnBudgetMs ≤ 17.9 s`, which is
   exactly the v2 ladder that failed VERIFY check 5 in production); the addendum withdraws the
   fits-always claim with stated reasoning — the 0.1.1 max is right-censored at the deadline
   itself and cannot size anything (design.md:2874-2879). The replacement is not weaker in
   substance: (a) the guard-bound form `(wcbs − 2×(spacing+budget)/1000) + budget/1000 + 21 ≤
   wcbs` (`tests/test_minigrid_decisions.nim:230-234`, `tests/test_minigrid_manifest.nim:40-44`)
   is tight against the *actual* guard, which trips at
   `elapsedSeconds + 2 × ceil((turnBudgetMs + turnSpacingMs)/1000) > wallClockBudgetSeconds`
   (`src/minigrid/decide.nim:204-212`) — 2 × 41 = 82, latest start 578, 578 + 30 + 21 = 629 ≤
   660, exactly the addendum's arithmetic; (b) the test *adds* equality pins the old test never
   had (`attempt1Ms == 18000`, `retryMs == 12000`, `turnSpacingMs == 11000`, `latest == 578`,
   `sum == 629`, per-episode call budget `== 240`, decisions.nim:228-260); (c) whole seconds and
   `attempt1Ms + retryMs ≤ turnBudgetMs` retained (manifest.nim:28-31); (d) asserted over both
   variants **and** the cert fixture (manifest.nim:15/26, plus the `configs.add(m["certification"])`
   loop at :138). Checklist item 5's own bound is untouched: engine stop 660 s + ~20 s artifacts
   < 720 s = 60 % of the 1200 s episode timeout.
3. **`fallbackCauses` counts both attempts; `retriedTurns`; relaxed identity.**
   `directives.nim:39-47` (`causes`, `retried`, `firstCause`), `decide.nim:244/282/361`
   (accumulation at each failure point, max 2 per turn by construction),
   `decide.nim:415-433` (`for cause in directive.causes: inc fallbackCauses[cause]`; retried →
   `inc retriedTurns`), replay path re-derives both from the record with pre-v2.1 single-`cause`
   fallback (`replays.nim:170-186`). Identity `fallbackTurns ≤ Σ ≤ 2×fallbackTurns` asserted in
   test 50 (`test_minigrid_decisions.nim:157-160`, incl. the round-17 mixed-cause case recording
   both keys, and a same-cause double count of 2) and in the engine e2e
   (`test_minigrid_engine.nim:101-113`, plus `retriedTurns ≤ llmTurns`).
4. **Log line still greppable.** `decide.nim:390-394`:
   `"minigrid llm: seat N falling back to scout (<cause>; attempt 1: <cause>) on turn T"` —
   contains `falling back`; the enum stringifies as `transport_timeout` etc.
   (`sim_types.nim:185-193`). Attempt 1 still says `will retry` only (`decide.nim:367-369`).
5. **Goto Case C exactly per the addendum.** `driver.nim:96-123`: when no reached cell is
   4-adjacent to the target, pick the reached cell minimising (i) Manhattan distance to target,
   (ii) BFS distance from agent, (iii) cell index (`:110-116`); zero primitives and
   `unreachable` only when that cell is the agent's own (`:117-119`); facing at `:145-159` —
   `dirToward` for the 4-adjacent case, else axis of greatest offset with `abs(dx) >= abs(dy)`
   giving x on ties; walk confined to seen traversable cells (BFS domain unchanged). `partial`
   flows through `expandPlan` (`driver.nim:190-191`) → `installLanePlan`/`macrosPartial`
   (`sim_state.nim:590-596`) → `last_plan.partial` in the observation (`sim_state.nim:1026`) →
   the directive record (`directives.nim:211`) → replay re-derivation (`replays.nim:161-163`).
   Test 7 pins all three cases including the walled-room surviving-`unreachable` case and the
   half-seen-board sweep landing on (6,6) facing east (`test_minigrid_sim.nim:309-350`).
6. **GameVersion "3", prepend-only changelog, fixture re-recorded in the same commit.**
   `sim_types.nim:22-28` (GV3 block prepended above the GV2 block);
   `tests/replays/gauntlet-seed42.replay` re-recorded in 85a2f68c (Bin 199972 → 205536); the
   fixture sweep (test 32, `test_minigrid_replay.nim:245-256`) asserts every committed fixture
   carries the current GameVersion; `tools/ci/check_gameversion.sh 8a78a6bf 85a2f68c` passes
   ("OK: GV3 is above the base's GV2" — run locally).
7. **Record → re-derive for all four end reasons.** Test 28
   (`test_minigrid_replay.nim:71-95`): `allLanesComplete`, `turnCap`, `wallClock`, `fault`, each
   with per-tick hash (`mismatch == -1`), gameHash, endRule/endReason, per-lane scores and full
   `gauntletResultsJson` equality.
8. **Baselines measurably unaffected — verified, with one caveat noted below.** I compared the
   fixtures myself: `tools/replay_summary.py` on the GV2 fixture (at 8a78a6bf) vs the GV3 one at
   head gives identical `scores [414070, 3000, 414070, 3000]`, `tasksSolved [4,0,4,0]`,
   `progressTotal`, `speedTotal`, `macrosUnreachable [0,0,0,0]`, `reason complete`,
   `turnsPlayed 30`, `finalTick 720`, and the new `macrosPartial [0,0,0,0]` — and the fixture is
   recorded through the real `sim.applyDirective` path (`tools/record_fixture.nim:43`), which
   wires the `macrosPartial` counter, so that zero is genuine. CI additionally re-runs the
   480-episode baseline sweep (12 cells × 40 seeds, `tools/tune_baselines.nim`,
   `ci.yml:192-193 "Re-run the baseline sweep with --check"`) green at head — the winning cell
   is unchanged under GV3 — and test 23 (60 seeds × both baselines, scout > bumper, fairness)
   is green. The commit message's literal "480 episodes … report macrosPartial == 0" is **not**
   asserted by any test or CI step (see observations).
9. **Prompt re-pins.** `llm.nim:230-232` (the new NEVER-goto-only line in WHAT YOU SEND) and
   `:244-250` (the goto bullet's partial/unreachable text) match the addendum verbatim;
   `tools/ci/policies.json` carries cartographer's two replaced sentences and missionfirst's
   goal bullet + the appended movement sentence, both champions still `PLAYER_PROMPT`, champion
   #2 still `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.
10. **`replay_summary.py` slot-ordering fix + regression test.** `by_slot()` builds
    `policyKinds`/`names`/`aliases` indexed by `register.slot`, sized to `num_agents`
    (`tools/replay_summary.py:161-201`); test 30b records registers in **reverse** slot order and
    asserts element-for-element equality with `results.*`
    (`test_minigrid_replay.nim:190-229`); test 55f pins the source
    (`test_minigrid_wire.nim:78-90`). Placement (30b/55f rather than "in test 55") is documented
    with sound reasoning in `docs/PORTING-MINIGRID.md:141-150`.
11. **New results fields through the triple.** `gauntletResultsJson`
    (`sim_state.nim:1098/1126-1131/1222-1229`: `macrosPartial`, `retriedTurns`), manifest
    `results_schema` (template `:532-537` `macrosPartial`, `:568-573` `retriedTurns`), and
    `tools/ci/docker_smoke.sh:298-311` whose expected-key set now includes both and **fails**
    (was: warned) on any missing per-seat key.

## Checklist pass (independent)

| item | status | evidence (path:line or run url) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 33229494065 (`.github/workflows/ci.yml`, branch main, head_sha 85a2f68c…, conclusion success; jobs test/docker-smoke/wasm-viewer all success). `git log -p --since=2026-08-28 -- tests/`: no skip/xfail/disabled added, no test file removed anywhere in the run; this round's replaced assertions (tests 7, 21, 50, 51) each track an addendum-pinned spec change and each gained equal-or-stronger replacements (test 51 gained `== 18000/12000` equality pins; test 50 gained mixed-cause both-keys assertions; test 7 gained a surviving-`unreachable` case). Verdict on the test-51 replacement: legitimate spec change, §2 above. |
| 2 Replay re-derivation | PASS | test 28 `tests/test_minigrid_replay.nim:71-95` (four end reasons, per-tick hash `mismatch == -1`, results-document equality); viewer uses the same runtime (`src/minigrrid` → `src/minigrid/replay_runtime.nim:16-37` shared native/wasm; seeks clamp to `replayStartTick`, `replays.nim:498`). |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer.bundle == "static-replay-viewer"`; `tools/build_replay_viewer.sh` mode 100755, presence enforced `ci.yml:302-303`; no `/client/replay` path in any manifest/workflow/script (grep clean). |
| 4 Both name spaces | PASS | Aliases Alpha/Beta/Gamma/Delta in observations (`sim_state.nim` observation `"you"`), register records assert alias == seatAlias (test 29 `test_minigrid_replay.nim:113-116`); real names only in `results.names`, joins, spectator chrome. |
| 5 Degrade-never-hang | PASS | Every wait bounded: batch deadlines via `CURLOPT_TIMEOUT` (`decide.nim:290-313`), monotonic 30 s `turnBudgetMs` wrap (`decide.nim:278-292`), spacing sleep bounded (`:263-266`), lobby capped (`lobbyJoinTimeoutTicks 2400`), budget guard `decide.nim:204-212` (last turn starts ≤ 578 s), engine stop 660 s (`server.nim:518`); 660 + ~20 s artifacts < 720 s = 60 % of 1200 s (`episode_timeout_minutes: 20`). |
| 6 num_agents | PASS | 4 in both variants' `game_config` and `certification.game_config` (template, verified by parse); four SEAT-COUNT invariants in `tools/ci/docker_smoke.sh:113-149`; docker-smoke log of run 33229494065 contains **no** `SEAT-COUNT FAIL` (grepped) and prints `smoke OK: seats=4 … reason=complete`. |
| 7 Scripted baseline | PASS | test 33 plays both variants + cert to `erComplete` (`test_minigrid_manifest.nim:162-165`); legality tests 17-19; tuning is the 480-episode grid harness, re-run in CI with `--check` (`ci.yml:192-193`, green) against `tools/ci/baseline_tuning.json`. |
| 8 LLM reply handling | PASS | `extractJsonObject` tolerant parse, exactly one retry batch (`decide.nim:274-275` `attempt < 2`), fallback recorded (fallback records per attempt, `fallbackTurns`/`fallbackCauses`, `falling back` log `decide.nim:393`). |
| 9 Rune-safe truncation | PASS | `truncateRunes` throughout (`directives.nim:227-241`); tests assert `validateUtf8() == -1` on multi-byte input at cap (`test_minigrid_driver.nim:199-200`, `test_minigrid_replay.nim:176`). |
| 10 Manifest validates | PASS | `game.docs` readme + 3 pages, every content a `{"type","value"}` object; `game.protocols` has both `player` and `global` as `{"type","value"}` objects (parsed from template). The `type` is `"uri"`, not the checklist example's `"text"` — this is the design note's own pin (design.md:1629), unchanged since 0.1.0, passed the CLI validator in two shipped releases (0.1.0, 0.1.1) and test 34 (`test_minigrid_manifest.nim:184+`) runs the shape the CLI requires. Not a falsification. |
| 11 Viewer legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` `client/replay_broadcast.html:4176-4181`; density lever `.tiny` at the 640×360 floor (`:1224-1228`); no client/ change in this diff; renderer fixture measures the 360 px layout (test 56 machinery, fixture step green). |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify locally (:173) → Upload the policies (:216) → Upload the Coworld (:314) → Put the Coworld secret (:410); three workflows present; `docker_smoke.sh` executable (100755); `policies.json` = 2 × `PLAYER_PROMPT` + 2 scripted, champion #2 carries `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`; placeholder gate run by me at head: clean (`<slug>/<IMAGE>/<SEATS>` absent from all five files). |
| 13 Viewer executes | PASS | Run 33229494065 `wasm-viewer` (job 99039795706) green **with** `Load the bundle in a real browser` step ran: `{"loaded":true,"ms":593,…,"feed_lines":9}`; scrub readouts at 0/50/100 % pairwise distinct (TURN 11 / TURN 16 / TURN 30); `needs: docker-smoke` (`ci.yml:286`); no `continue-on-error` anywhere in ci.yml; `data-replay-loaded`/`data-replay-error` set from the shell (`replay-viewer/static_replay.js:14-20,161`); playback opens at the game start (`replay_runtime.nim:34` `startTick = gameStartTick`, seeks clamped `replays.nim:498`); `replay-viewer/config.nims` byte-equivalent to the starter's (no MODULARIZE in either) and both workers bootstrap via `Module.onRuntimeInitialized` (`static_replay_worker.js:188` in both repos) — same lineage, no flag/bootstrap mismatch. |
| 14 Chrome is the starter's | PASS | `client/chrome_common.js` sha256-identical to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diffed); `replay_broadcast.html` is the starter page with the game block under the banner `MINIGRID additions to the inherited coworld-ctf chrome` (:4140), derived by `tools/build_broadcast_page.py` (never hand-edited, per AGENTS.md; `--check` in CI); no client/ file touched in this diff. |
| 15 Drawn strings fit | PASS | Browser smoke carries `--strict-text-bounds` (job log); board replay reports `canvas text: 0 drawn` (chrome text is DOM) but the dedicated `Worst-case renderer fixture (the LLM text path)` step ran: `174 drawn, 0 never inside, 0 ellipsized (--strict-text-bounds)`, with the full-length self-assertion (`tools/ci/renderer_fixture.html:188 assertFullLength`, 138-rune remarks). |
| Simultaneous batch | PASS | One `curl.makeRequests` batch per attempt per turn, one request per open seat (`decide.nim:293-313`); never sequential. |

## Fixer report audit

No `r3-fixes.md` exists; the audited claims are the builder's commit message at 85a2f68c.

| claim | builder said | I verified | agrees |
|---|---|---|---|
| Ladder re-derivation | 18000/12000/30000, spacing unchanged, everywhere | defaults + both variants + cert + config.json, all four values (§1 above) | yes |
| Guard bound replaces fits-always | proved, 578+30+21=629 ≤ 660, test 51 replaced for variants AND cert | guard code matches the formula exactly; test asserts it for both variants and the cert fixture; equality pins added | yes |
| fallbackCauses both attempts + retriedTurns + identity | as addendum §2 | code, record, replay re-derive, tests 50 + engine e2e, results triple (json/schema/smoke) | yes |
| Case C + GameVersion 3 + fixture re-record | as addendum §3a | code matches all three tie-breaks and the facing rule; GV3 prepend-only; fixture re-recorded in the same commit; test 7 pins three cases | yes |
| "480 episodes … macrosPartial == 0 for both" | claimed as evidence | **not asserted anywhere in tests/CI**; the sweep CI re-runs (480 episodes, `--check`) compares only the winning cell, and `tests/helpers.nim:40-42` `playScripted` / `tools/tune_baselines.nim:41-42` `playOne` do not pass `expansion.partial` to `installLanePlan`, so those harnesses could not have read a nonzero `macrosPartial` even if one occurred | partially — see observations |
| Fixture scores identical to GV2 | claimed | verified myself via `replay_summary.py` on both fixtures: scores/tasksSolved/progress/speed identical, `macrosPartial [0,0,0,0]` through the real `applyDirective` path | yes |
| Prompt re-pins mirrored | llm.nim + policies.json | verbatim (missionfirst's appended sentence sits at the prompt's end rather than inside the Budget paragraph — text verbatim, placement differs) | yes |
| replay_summary slot fix + regression test | test 30b + 55f | verified, incl. reverse-order register fixture | yes |

## Non-blocking observations

- **The "480-episode macrosPartial == 0" figure is unpinned.** The substantive commitment
  ("scout and bumper unaffected") is verified from tree + CI (sweep `--check` green, fixture
  equality, test 23), so nothing blocks — but the literal counter reading in the commit message
  cannot have come from `playScripted`/`playOne`, which drop `expansion.partial` on the floor
  (`tests/helpers.nim:40-42`, `tools/tune_baselines.nim:41-42`). What would pin it: pass
  `expansion.partial` through in both harnesses and assert `macrosPartial == 0` for scripted
  lanes in test 23 (or in the sweep's `--check`).
- `tools/ci/check_gameversion.sh` is present and passes on this diff (run locally,
  GV2 → GV3 OK) but is wired into no workflow in this repo (the starter runs it in a
  `build.yml` PR gate this fork does not have). The fixture sweep (test 32) covers the
  fixture-vs-code half in CI; the bump-on-rule-change half is convention-enforced only.
- Missionfirst's new sentence "Every turn must contain at least one movement primitive besides
  the goto." is appended to the prompt's end, not to the Budget paragraph as the addendum
  says. Text verbatim; placement divergence only, undocumented.
- `firstCause` (`directives.nim:47`) is documented "for the log line only" but the recovered-turn
  log line does not exist; the field is dead weight beyond the record. Cosmetic.
- An out-of-bounds `goto` target still returns bare `unreachable` (driver.nim:74-75) rather than
  Case C. Consistent with the addendum's in-grid framing and pre-existing; noting for
  completeness.

BLOCKING: 0
