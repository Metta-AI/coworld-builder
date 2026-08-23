blocking: 0

# r1 verdict — gridlock

Head: `0decf3220186f0ae07d7b03731624c07d1277847`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Clone: `/tmp/judge-gridlock` (fresh, from GitHub, verified at the head sha). Review read only
after my own pass over the tree, the CI logs and the test-file history; `r1-fixes.md` read last,
as a claim sheet to audit, and every disposition in it was re-verified from the tree or the logs
— none was taken on trust.

CI evidence at head: run **32646687184**, `headSha == 0decf32…`, conclusion `success`, jobs
`test` 97211916089 ✓, `docker-smoke` 97211916175 ✓, `wasm-viewer` 97212078642 ✓,
`viewer-native` 97212347499 ✓.

## Standing blocking findings

None. Every checklist item verified at head; no finding of the reviewer's stands as blocking,
and my independent pass surfaced nothing the reviewer missed that ties to a checklist item.

## Refuted / not reproducible at head

The review itself filed **0 blocking**. Its 24 advisory findings were accurate at the reviewed
sha `4b74806` (I spot-checked each against that sha's code paths where the fix diff made the
"before" state visible); 21 of them are **resolved by later commits** and no longer reproducible
at head, and 3 are deliberate no-changes that falsify no checklist item:

| finding | status at head | evidence at `0decf32` |
|---|---|---|
| F2 gridlock sampled every 24 ticks | resolved | `src/gridlock/sim.nim:461-462` — `jamWatch(sim)` / `gridlockWatch(sim)` run unconditionally every tick; only `recordKeyframe` (`:449,474`) keeps the mod-24 gate |
| F4 missing route-start guard | resolved | `routeStartFailure` exists and is applied where a replan lands; `tests/test_engine.nim:249` plants the broken route |
| F6 fallback dated one turn early | resolved | `applyDecision(appState, decision, turn)` takes the loop's index (`server.nim:265`); `tests/test_server.nim:77` pins `newEvent(seFallback, gs.game.tick, turn,` and the absence of `gs.game.turn` in that proc |
| F7 latency_ms always 0 | resolved | `llm.nim:338-348` — `attemptStart`/`epochTime` stamps `latencyMs` on parsed plans, `spentMs` on fallbacks; `tests/test_engine.nim:103` drives it to the `plan` event body |
| F8 no outer 22 s deadline | resolved | `llm.nim:316-332` — `turnBudgetSeconds` clamps each attempt to the remainder and drops a retry that cannot fit (`remaining < 1 → break`); `server.nim:221` sets it from `cfg` |
| F9 disconnect does not degrade | resolved | `roster.nim:77` `effectiveScriptNow` (connected-and-dropped ⇒ `skDispatcher`, registration untouched so reconnect revives); consumed at `server.nim:136` |
| F10 default prompt on empty env | resolved | `src/gridlock_player.nim:24-32` — neither var ⇒ `scripted: "dispatcher"`; `DefaultPrompt` gone (grep: 0 hits) |
| F11 register sent twice | resolved | one `socket.send(frame)` at `:64`, before the receive loop; `tests/test_startup.nim` counts sends |
| F12 no-credentials plan recorded scripted | resolved | `llm.nim:306-313` — `source = psFallback` + `fcNoCredentials` record; a seat that ASKED for a baseline stays `psScripted` (`tests/test_engine.nim:127`) |
| F13 no-float guard covered 3 modules | resolved | `tests/test_traffic.nim:180-192` walks `src/gridlock/*.nim` (`check scanned >= 19`) for the banned calls |
| F14 byte slice on model text | resolved | `plan.nim:44` `cleanLine(text, MaxErrorHeadRunes)`; the only remaining `[0 ..< text.high]` (`plan.nim:89`) strips a trailing ASCII `%` guarded by `endsWith("%")` — rune-safe; emoji test at `tests/test_plan.nim:106` |
| F15 inert visible controls | resolved | `chrome_common.js:483-487` wires `#btn-loop` (`looping = !looping`, restart at end `:411`); `#btn-skip,#btn-spoilers{display:none}` in the page CSS; test "no visible transport control is a no-op" |
| F16 btn-back/btn-fwd mis-wired | resolved | `chrome_common.js:467-471` — back = `core.seek(Math.max(0, lastTick - 1))`, fwd = +5 s via `5 * (meta.ticks_per_second || 24)`; test forbids `setSpeed(16)` in the fwd body |
| F17 #jamflash empty | resolved | `chrome_common.js:339` `el('jamflash')` + `.show` off the gridlock event branch; `#jamflash.show{opacity:1}` in the page; canvas rect (`drawFlash`) kept for the pan/zoom transform |
| F18 viewer_smoke.mjs behind template | resolved | `diff -q tools/ci/viewer_smoke.mjs /workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` → **identical** |
| F19 native viewer case skipped in CI | resolved | `tests/test_viewer.nim:248-262` — missing bundle is `fail()` under `GRIDLOCK_REQUIRE_BUNDLE`; new `viewer-native` job (`ci.yml:340-414`, `needs: wasm-viewer`) ran it green: job 97212347499 `[OK] the emitted module replays to the end when a bundle is present` |
| F20 nimby not sha256-checked | resolved | `Dockerfile:18-34` — per-arch sha256, `sha256sum -c -`; visible in the docker-smoke build log |
| F21 events_last_turn two turns wide | resolved | `view.nim` lower bound `sim.turn * turnTicks`; `tests/test_view.nim:25` plants one event inside and one just outside the window |
| F23 ±1 digest sensitivity | resolved (test added) | `tests/test_determinism.nim:61-87` — dispatch 20 vs 21 is one unit and one van of `activeCap`; digests diverge |
| F25 no tuning harness (the review's Could-not-determine on item 7) | resolved | `tools/tune_baselines.nim` + `tools/tuning/dispatcher_grid.{md,json}` committed; `tests/test_baselines.nim:124-166` asserts the shipped constants ARE the committed grid's winner, the sweep is ≥135 cells × ≥3 seeds × ≥3 loads with disjoint held-out seeds |
| F3 / F22 (doc drift) | resolved as docs | `docs/PROTOCOL.md` states the turn-so-far window; `docs/RULES.md` describes the arterial's stop-line promotion; manifest regenerated, `test_manifest` "inlined docs match" green |

Deliberate no-changes, checked and accepted — none falsifies a checklist item:

- **F1** (keyframe at top of tick): a labelling convention. Recorder, snapshot, re-deriver and
  wasm viewer all share the one convention (`sim.nim`, `replay.nim`, `gridlock_replay.nim`), and
  item 2's frame-by-frame property is asserted against it (`tests/test_replay.nim:111`).
- **F5** (shared destination cursor): the shared cursor is what keeps the four demand streams
  congruent, which the note's own fairness argument and `tests/test_parcels.nim` require. The
  note's step-3 phrasing is the outlier.
- **F24** (plazas moved): checked the arithmetic myself — the note's example disc (512,512, r 34)
  would straddle the grid line at 512; the shipped four discs span 426–486/538–598, clear of
  400±10 and 512±10 and mirror-invariant. The deviation is what makes the note's own
  scenery-never-overlaps-a-lane invariant achievable.

I found no finding in the review that was wrong at the sha it reviewed — nothing to dismiss as
mis-read; the table above is resolution, not refutation.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32646687184** at `0decf32…`, `success`, 4/4 jobs. `git log -p 4b74806..HEAD -- tests/`: 9 files, **356 insertions / 12 deletions**, every deletion an import line, a comment, or the F19 skip being *narrowed* into a conditional `fail()`; the F21 rename was restored under its own name in `0decf32` with no assertion lost. No skip/xfail added, no tolerance widened, no test removed; `tests/fixtures/golden_digests.json` untouched. Test job: 32 groups (16 files × debug+release), 428 `[OK]`, 0 failures; the only `[SKIPPED]` is the bundle case on the emsdk-less runner, which `viewer-native` executes for real in the same run |
| 2 replay re-derivation, viewer derives from it | PASS | `tests/test_replay.nim:111-123` — `rederive(data)` from seed+city+seat_depots+plans reproduces every keyframe `t` and digest `d` **and every byte of `vehicles_b64`**; the wasm entry (`replay-viewer/gridlock_replay.nim:1-12,52-60`) runs the same Nim sim via `initReplayRuntime`/`advanceOneTick`, so the drawn frame is the re-derivation; per-keyframe digest mismatch surfaces as `gridlock_mismatch_tick` → `#mmwarn` |
| 3 static viewer | PASS | Manifest `game.replay_viewer = {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` committed 100755, asserted executable in CI before use (`ci.yml:225-236`) and required by the release certify gate (`LIVENESS_MARKER` = "Replay liveness: skipped (static replay bundle declared"). The bundle's only network call is the worker's `fetch(message.replayUrl)` with a 20 s AbortController. No pod-served replay path in the manifest; the server's `/client/replay` is the starter's local-viewing route, not a declared viewer |
| 4 both name spaces | PASS | `tests/test_view.nim:157` runs a whole episode and asserts no view/event/prompt string contains any `results.names` entry; `:188` re-draws the seat→depot permutation per seed. Real names in `replay.names.players`/`results.names`/viewer meta only; the browser smoke's scorebug printed real names beside aliases (`"P1 Verde 0 P3 Copper 0 …"`) |
| 5 degrade-never-hang, ≤60 % of 1200 s | PASS | Bounds traced at head: connect wait ≤ `playerConnectTimeoutSeconds` (`server.nim:195-202`); LLM 14 s + one 6 s retry, both clamped to the 22 s outer turn budget which also drops an unfittable retry (`llm.nim:316-332`); spacing sleep ≤ `minTurnSpacingSeconds`; done-broadcast 3 s; shutdown grace 20 s; hard stop at `wallClockBudgetSeconds` 660 ≤ 720 (`server.nim:273-277`); budget guard flips all remaining turns to scripted (`server.nim:235-241`); replan FIFO capped at `routeBudgetPerTick`. No unbounded loop or blocking read found |
| 6 num_agents | PASS | 4 in `default`, `rush` and `certification.game_config`; cert `players` = 4 = `game_config.players`. `tools/ci/docker_smoke.sh:106-152` enforces all four invariants + the `SMOKE_SEATS` (=4) cross-check, each exiting via `SEAT-COUNT FAIL:`. **Grep of the full docker-smoke log at head (job 97211916175): 0 hits for `SEAT-COUNT`**; the job printed `game=gridlock seats=4 … "num_agents": 4` and `smoke OK: seats=4 … reason=complete` |
| 7 scripted baseline, full legal episodes, grid-tuned | PASS | `tests/test_perf.nim:33` and `tests/test_baselines.nim:178` assert `reason == "complete"` on full scripted runs; 500 random views × both baselines emit schema-legal plans with derived quantities in range (`test_baselines.nim:18-56`); tuning: `tools/tune_baselines.nim` + committed grid output, shipped constants pinned to the grid's winner (`test_baselines.nim:124-166`) — the review's one Could-not-determine, now settled in-tree |
| 8 LLM reply handling | PASS | `extractJsonObject` takes the outermost balanced object behind prose/fences (`plan.nim:38-71`); `"70%"`, numeric strings, district names accepted; exactly one retry with the invalid-reply hint (`llm.nim:317-361`); fallback = dispatcher plan with `source: psFallback` + `fallback` event (seat, attempt, cause, detail) + per-seat `fallback_turns`/`fallback_causes` — including the no-credentials case (F12 fix) |
| 9 rune-safe truncation | PASS | `clipRunes`/`cleanLine` in `types.nim` (rune-walking, never byte slices); applied to note ≤140, say ≤32, policy ≤48, detail ≤200, prompt ≤4000; `tests/test_plan.nim:132` puts a 4-byte emoji on the 32nd rune and asserts UTF-8 validity; `tests/test_replay.nim:38` validates the whole replay file as UTF-8 before parsing with a forced non-ASCII say; the F14 fix removed the last byte cut on a replay-reaching path |
| 10 manifest validates | PASS | `game.docs` = readme (text, 5336 B) + 2 pages (rules.md 8872 B, protocol.md 9040 B), all `{"type":"text","value":…}`; `game.protocols` carries both `player` and `global` as text; `results_schema` keys asserted equal to the results builder's key set (`test_manifest.nim:106`); reason enum 3, end_rule enum 4 |
| 11 viewer legible at 360 px | PASS | `client/replay_broadcast.html:64`: `.plate .team-name,.plate-name{flex:1 1 auto;min-width:3.2em;overflow:hidden;text-overflow:ellipsis;…}` — the checklist's `.plate-name` rule literally present; `@media (max-width: 640px)` at `:239` hides `.chiplabel`, `#planbar`, `#viewpanel`, aliases and the district grid; pinned by `tests/test_viewer.nim:192-208` |
| 12 release order and scaffold | PASS | `coworld-release.yml`: build (:153) → certify (:167) → upload-policies (:206, explicitly "BEFORE upload-coworld") → upload-coworld (:304) → secret put (:342, "AFTER"); all three workflows present; `docker_smoke.sh` 100755; `policies.json` = 4 distinct policies, 2 × `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the placeholder gate (`grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files) **exits 0 — run by me at head**; the four documented runtime angle-bracket names are present and expected |
| 13 viewer executes | PASS | (i) `wasm-viewer` green at head incl. `Load the bundle in a real browser` → `{"loaded":true,"ms":284,"clock":"00:40 TURN 0/4","scorebug":"P1 Verde 0 P3 Copper 0 P2 Saffron 0 P4 Cobalt 0","feed_lines":4}` against the same-run docker-smoke replay; `needs: docker-smoke` (`ci.yml:212`); no `continue-on-error` anywhere in the workflow. (ii) `data-replay-loaded` set in `markLoaded()` from both the `firstFrame` and `loaded` branches (`static_replay.js:44-45,184-196`); `data-replay-error` in `showFailure` (`:77`); both from the shell's own code, plus the `coworld-replay` bridge. (iii) Pairing: `config.nims` carries no `MODULARIZE`/`EXPORT_NAME` (`:28-34` says so, and the flag block `:46-54` confirms); the worker uses `Module.onRuntimeInitialized` + `importScripts` with the one-macrotask defer past `callMain()` (`static_replay_worker.js:202-216`) — one lineage, both halves, and the smoke's `loaded:true` is the executable proof |
| batching (simultaneous game) | PASS | `runBatch` issues one `client.curl.makeRequests(batch, timeout)` over all open seats (`llm.nim:275-294`); nothing loops seats over a per-seat call; `tests/test_engine.nim:32,67` assert all four in-flight windows intersect and every turn batches exactly 4 |

Could not verify, judged non-blocking with reason: `curly.makeRequests` enforcing its timeout
internally (package not vendored in the sandbox). Item 5 asks that every wait carry an explicit
bound; the bound is explicitly passed at the call site (`llm.nim:294`), clamped by the outer turn
budget, and the checklist does not require auditing the pinned dependency's internals — the same
judgement the reviewer reached. What would settle it fully: reading `curly` at the `nimby.lock`
revision, or a hosted episode with a hung endpoint (phase 60).

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F2,F4,F6,F7,F8,F9,F10,F11,F12,F13,F14,F15,F16,F17,F18,F19,F20,F21,F23,F25 | fixed, per-commit | each re-read at head (table above); F18 additionally by byte-diff against the template; F19 additionally from the green `viewer-native` job log | yes |
| F1, F5, F24 | no change, with evidence | evidence re-derived independently (convention shared by all consumers; congruence requires the shared cursor; plaza arithmetic recomputed) | yes |
| F3, F22 | fixed as docs | `docs/PROTOCOL.md` / `docs/RULES.md` state the code's behaviour; manifest inlines match (test green) | yes |
| "no test disabled/skipped/weakened" | claimed | full `git log -p 4b74806..HEAD -- tests/` read hunk by hunk: additions only, one skip narrowed into a CI failure, one rename restored | yes |
| CI at head | run 32646687184 success | `gh run view --json headSha,conclusion` → headSha matches, `success`; all four job logs pulled | yes |

## Non-blocking observations

- The `test` job still prints two `[SKIPPED]` lines for the bundle case (no emsdk on that
  runner). The assertion executes in `viewer-native` against the real artifact in the same run,
  so nothing is unexecuted; noted so nobody later reads the skip as a gap.
- The design note says nimby "0.1.27" for the viewer image; both Dockerfiles and ci.yml now pin
  0.1.26 with sha256. Consistent across the tree; only the note is stale. No checklist item.
- `jam_index`'s first `heat` event after a turn boundary averages a one-tick window and reads
  low; documented in PROTOCOL.md rather than changed. Advisory, matches the shipped docs.

BLOCKING: 0
