blocking: 1

# r1 verdict — raid
Head: 6a8a68c23a606cf7c2046568800c753ecee3dd04   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Repo cloned fresh at 6a8a68c (main tip, verified `git rev-parse HEAD`). Review adjudicated:
`r1-review.md` (19 findings F1–F19, written against 501040d). Range `501040d..6a8a68c` is 16
fix commits. CI evidence: run **32621942459** on main at 6a8a68c, conclusion `success`, all
three jobs (`test`, `docker-smoke`, `wasm-viewer`) success — verified via
`gh run list`/`gh run view`, not taken from the fixer's report.

## Blocking items (coordinator format)

- [static-viewer] .github/workflows/ci.yml:190-319 the `wasm-viewer` job has no `Load the bundle in a real browser` step, no `tools/ci/viewer_smoke.mjs` in the tree, and no `needs: docker-smoke` — nothing ever executes the browser shell (index.html + static_replay.js + worker bootstrap); checklist item 13 declares a job green with the smoke step absent a blocking finding

## Standing blocking findings

### B1 — Item 13: the viewer is never executed in a real browser   (source: judge)
- Where: `.github/workflows/ci.yml:190-319` (the whole `wasm-viewer` job); `tools/ci/` contains
  only `docker_smoke.sh` and `policies.json` — no `viewer_smoke.mjs` anywhere in the tree
  (`find . -name '*viewer_smoke*' -o -name '*.mjs'` → empty).
- Verified at head: the job's steps are checkout → assert hook executable → build bundle →
  assert `index.html`/`.wasm` exist → upload artifact → stage bundle → toolchain → "Run the
  viewer tests against the built bundle" (`nim r … tests/test_viewer.nim`, gated on
  `grep -q 'WASM-SMOKE OK'`, ci.yml:309-319). There is **no** `Load the bundle in a real
  browser` step and **no** `needs: docker-smoke` (`grep -n "needs:" .github/workflows/*.yml`
  → no matches). The builder scaffold this run inherits has all three
  (`/workspace/coworld-builder/templates/ci.yml:212` `needs: docker-smoke`, `:293` step
  `Load the bundle in a real browser`, `templates/tools/ci/viewer_smoke.mjs` present).
- Checklist item: **13. Viewer executes** — "`ci.yml`'s `wasm-viewer` job is green … **including
  its `Load the bundle in a real browser` step** (`tools/ci/viewer_smoke.mjs`, headless chromium,
  loading the replay `docker-smoke` produced) … a job green because the smoke step is absent,
  commented out, or `continue-on-error` is a blocking finding, and so is a `wasm-viewer` that
  does not `needs: docker-smoke`. … **File presence is not evidence here; the smoke's
  `loaded: true` is.**"
- What mitigates it (and why it still counts): the node harness does execute the **exact emitted
  wasm module** in CI (run 32621942459 logged `WASM-SMOKE OK: 647 ticks, digest 925898626,
  112 events` — ticks/digest/seek/malformed-input all exercised), and I read the
  cogame-lantern deadlock condition directly: `replay-viewer/config.nims:45-46` links
  `-s MODULARIZE=1 -s EXPORT_NAME=RaidReplayModule` and `static_replay_worker.js:86` bootstraps
  via the factory `self.RaidReplayModule({...})` — they come from the same convention and agree;
  there is no `Module.onRuntimeInitialized` wait anywhere. Both markers exist and are set from
  the shell's own paths (`static_replay.js:150` `data-replay-loaded="true"` on the worker's
  `loaded` message; `:40` `data-replay-error` in `showFailure`). But the checklist is explicit
  that reading the files is not evidence for this item — only a browser load of the
  docker-smoke replay is — and no such step exists at head. What would settle it: copy
  `templates/tools/ci/viewer_smoke.mjs` into `tools/ci/`, add the template's
  `Load the bundle in a real browser` step and `needs: docker-smoke` (plus the replay-artifact
  upload from docker-smoke it consumes) to `ci.yml`'s `wasm-viewer` job, and get one green run
  on main.

## Refuted / dismissed

### B1 (reviewer's F1) — byte-index slices in `llm.nim` reach the replay → REFUTED (fixed since 501040d)
- Evidence: fixed at `6916ff9`. At head all four captured-error cuts go through `runeCap`:
  `src/raid/llm.nim:204` `runeCap(response.body, 400)`, `:212` `runeCap(response.body, 300)`,
  `:217` `runeCap(response.body, 300)`, `:226` `"JSON: " & runeCap(result, 160)`. `runeCap`
  itself is now a sanitiser (`src/raid/labels.nim:31-58`: `utf8Only` drops malformed bytes
  before the `runeSubStr` cut), which closes the reviewer's correct observation that the old
  `runeCap` passed an already-broken partial rune through. Tests added:
  `tests/test_orders.nim` `testCapturedErrorTextIsRuneSafe` (4-byte emoji astride the
  400/300/300/160 caps + an invalid-UTF-8 body) and `testDetailAtTheCapIsValidUtf8` (emoji as
  the 200th rune of `fallback.detail`, recorded through `applyTurn`, serialised, parsed). Both
  ran green in run 32621942459. The reviewer's "could not determine" item (no multi-byte test
  at the error-detail cap) is also closed by the same commit.

### F3 — grid harness not in the tree → REFUTED (fixed since 501040d)
- Evidence: `tools/tune_baselines.nim` committed at `046a140` (140 lines: 135-point sweep over
  four `{.intdefine.}` scalars, 6 seeds + the certification fixture, `arena.canOccupyCog`
  stand rejection, tie-break toward shipped values). `src/raid/baselines.nim` comments now
  describe what the sweep separates instead of citing a missing file. Item 7's tuning clause
  is now verifiable from the tree.

### F12 — `/client/replay` route vs item 3's literal wording → DISMISSED (adjudicated: does not falsify item 3)
- Evidence: `src/raid/server.nim:420` `result.get("/client/replay", replayPageHandler)` exists
  at head, exactly as the reviewer said. I rule it does not falsify item 3: (a) the manifest
  declares `"replay_viewer": {"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json`, verified) and never names a pod URL, so the *declared*
  viewer path is the static bundle; (b) `coworld-release.yml:167-204` hard-fails certification
  unless the CLI reports the **static** bundle (`LIVENESS_MARKER`), i.e. a pod-served viewer
  cannot ship; (c) both starter repos this checklist governs carry the identical local-debug
  route (`/workspace/starters/coworld-ctf/src/ctf/server.nim:627,642,840`;
  `/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:470`), so the literal reading
  would fail every starter; (d) the design note keeps the route explicitly (§Viewer). The
  hosted viewer contacts only the `?replay=` URL plus same-origin bundle assets
  (`static_replay_worker.js:118`, `:70-79`). Item 3's remaining clauses verified: manifest
  declaration present; `tools/build_replay_viewer.sh` present, mode 100755
  (`git ls-files -s` → `100755`). Advisory, count zero.

### Reviewer findings F2, F5–F11, F13–F19 — all advisory as filed; dispositions verified at head
None was a blocking claim; none stands as blocking now. See the fixer-audit table for
per-finding verification. F7 (first cleave/pour on tick index 95/191 vs the note's "tick 96/192")
was escalated to the judge as a design question: **adjudicated — keep the code, keep the
doc+test resolution.** The note's "at tick 96" is 1-based prose; the shipped behaviour ("the
96th tick of the encounter, index 95") is now stated in `docs/RULES.md:134,146`, rebuilt into
the manifest, and pinned both ways by `tests/test_boss.nim` `testFirstCleaveAndPourTicks`.
Re-arming at +1 is a measured retune (stalwart 0.7175→0.5895, loses Meltdown on the default
seed) for zero player-visible gain; no checklist item names the start tick. Non-blocking.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run 32621942459 at 6a8a68c, conclusion `success` (gh run list, cited above). `git log -p --since="2026-08-22T23:59:00Z" -- tests/` read hunk by hunk: every change adds assertions. Only removals: two never-read `FakeClient` fields (`hangSeconds`/`attemptSeconds`, test_engine.nim — dead code, replaced by a real hung-client test), a docstring, and `int`→`int64` digest widening at 501040d. No assertion deleted, no tolerance widened, no skip added, no test file removed. |
| 2 Replay re-derivation | **pass** | `src/raid/replay.nim:148-188` `rederive` re-runs the sim from seed+map+config+recorded orders; `firstDigestMismatch:190` compares every keyframe digest; `controlsMatch` compares control bytes. `tests/test_replay.nim:81-86` asserts both ("every keyframe digest re-derives", "byte for byte"). The viewer displays the **re-derived** frames: `replay-viewer/raid_replay.nim:54-56` (`rederive(payload, keyframeEvery=1)`, `frames = rebuilt.keyframes`), recorded keyframes used only for the mismatch check. |
| 3 Static viewer | **pass** (F12 adjudicated above) | Manifest `game.replay_viewer = {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755; worker fetches only `?replay=` + same-origin assets (`static_replay_worker.js:118`). |
| 4 Both name spaces | **pass** | Views/prompts alias-only (`tests/test_view.nim` greps a seat's view for real names/seed/notes/prompts); real names in `replay.names.players`, results, viewer plates (`client/replay_broadcast.html:1839` `meta.names.players[i]`; `broadcast_core.js:302` "the board NEVER shows a real player name"). |
| 5 Degrade-never-hang | **pass** | LLM: two curl deadlines (`llm.nim:277-286`), rounded sum ≤ turnBudget enforced (`config.nim:88-94` via `deadlineSeconds`); connect wait `server.nim:196-203` bounded by `playerConnectTimeoutSeconds`, register grace ≤ 3 s (`:205-215`); done broadcast enforced at seats × 3.0 s (`server.nim:129-149`, F5 fix); budget guard `engine.nim:87-99`; unconditional hard stop `engine.nim:113-118` → `deadline/wall_clock`; 660 ≤ 720 = 0.6 × 1200, asserted for every variant (`tests/test_manifest.nim:102-107`, `config.nim:96`). Hung-client test proves settle-inside-budget (`tests/test_engine.nim` `testHungClientKeepsTheEpisodeInsideItsBudget`). |
| 6 num_agents | **pass** | 5 in `variants[default]`, `variants[sprint]`, `certification.game_config`; cert players 5/5 (read from the manifest directly). `tools/ci/docker_smoke.sh:98-141`: all four invariants + independent `SMOKE_SEATS:-5`, each exiting `SEAT-COUNT FAIL:`. **`grep -c 'SEAT-COUNT FAIL'` on run 32621942459's full log → 0**; smoke logged `game=raid seats=5 …` and `smoke OK: seats=5 results=1440B replay=47263B reason=complete`. |
| 7 Scripted baseline full episodes, tuned | **pass** | `tests/test_baselines.nim:153-160` (`reason == "complete"`, `end_rule == "kill"` on the cert fixture), `:76-125` (500 states × 2 baselines × 3 deals: order legality + control bytes in range + role-bit ownership), `:127-148` (no ability on cooldown). Tuning harness committed: `tools/tune_baselines.nim` (F3 fix). |
| 8 LLM reply handling | **pass** | `orders.nim:13-48` tolerant extraction (fences, prose, balanced braces); retry exactly once (`llm.nim` `for attempt in 0 .. 1`); fallback = stalwart order with `source: osFallback` + recorded `fallback` event with closed cause enum (`engine.nim:34-48`) and per-seat `fallback_causes` in results. |
| 9 Rune-safe truncation | **pass** | `labels.runeCap:31-58` (utf8Only + runeSubStr) on every replay-bound string; `tests/test_orders.nim` feeds a 4-byte emoji at the `say` cap, at all four captured-error caps, and as the 200th detail rune; asserts valid UTF-8 + round-trip each time (green in 32621942459). |
| 10 Manifest validates | **pass** | `game.docs.readme` text (5327 chars) + 2 pages (`rules.md` 15605, `protocol.md` 15211), all `{"type":"text","value":…}`; `game.protocols` carries both `player` (2468) and `global` (1720). Parsed directly from `coworld_manifest_template.json`; asserted by `tests/test_manifest.nim`. |
| 11 Viewer legible at 360 px | **pass** | `client/replay_broadcast.html:1556` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; … }`; `:1612` `@media (max-width: 640px)` hides `#viewpanel` and chip labels. Statically asserted by `tests/test_viewer.nim`. |
| 12 Release order and scaffold | **pass** | `coworld-release.yml`: build manifest (:153) → certify (:167) → upload-policies (:206, comment pins the order) → upload-coworld (:304) → secret put (:342, "AFTER upload-coworld"). docker-smoke builds the image in the same job it smokes (ci.yml:172-181); wasm-viewer builds the bundle it tests in-job. All three workflows present; both hooks 100755 (`git ls-files -s`). `policies.json`: 4 policies, 2 × `PLAYER_PROMPT` champions + 2 × `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate run verbatim: no `<slug>`/`<IMAGE>`/`<SEATS>` match → gate exits 0. |
| 13 Viewer executes | **FAIL — blocking (B1 above)** | Bullet 1 fails: no browser-load step, no `tools/ci/viewer_smoke.mjs`, no `needs: docker-smoke` (ci.yml:190-319). Bullets 2 and 3 pass: markers at `static_replay.js:40,150`; `config.nims:45-46` MODULARIZE=1/`RaidReplayModule` ↔ worker factory call `static_replay_worker.js:86` agree (no lantern deadlock); node wasm smoke executed the emitted module (`WASM-SMOKE OK: 647 ticks…` in 32621942459). But per the item's own rule, file agreement and a node run are not the required evidence. |
| One-parallel-batch | **pass** | `llm.nim decideAll`: one `RequestBatch` over every open seat, single `curl.makeRequests(batch, timeout)` per attempt; no per-seat loop. `engine.nim:69-73` calls `decide` at most once per turn. `tests/test_engine.nim` `testOneParallelBatchPerTurn` asserts overlapping in-flight windows. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `6916ff9`, both tests fail against old code | all 4 slices now `runeCap` (llm.nim:204,212,217,226); `utf8Only` sanitiser (labels.nim:31-47); both tests present and green in 32621942459 | yes |
| F2 | fixed, `d613c40`, soak is last word; end-to-end spill==0 test | dodge default moved to constructor, soak assignment is the override (baselines.nim); `testStalwartSoaksCrucibles` asserts emitted reaction + every crucible `soakers >= 1` + `spillStacks == 0` | yes |
| F3 | fixed, `046a140`, harness committed, TankPriorityPct 45→35 | `tools/tune_baselines.nim` exists (140 lines, intdefine sweep); baselines comments amended; golden fixture unchanged at seed 42 (test_determinism green) | yes |
| F4 | no change, documented in place | gates commented at control.nim:147-157, 352-360; no checklist item touched | yes |
| F5 | fixed, `a6f7465`, enforced allowance | `broadcastDone` skips seats past a cumulative seats × 3.0 s allowance (server.nim:129-149) | yes |
| F6 | fixed, `0ecf68e`, replay before results | `writeArtifact(replayUri…)` precedes `writeArtifact(resultsUri…)` (server.nim:171-174), reason at the call site | yes |
| F7 | code unchanged; doc+test; retune measured and reverted; judge to decide | docs/RULES.md:134,146 states index 95/191; manifest rebuilt; `testFirstCleaveAndPourTicks` pins both. Adjudicated above: keep as shipped | yes |
| F8 | fixed, `40b7dc4` | `Add.killer` stamped by `damageAdd`, recorded in `add_death`; test asserts non-lethal/lethal/event | yes |
| F9 | fixed, `5578779`, dead branch deleted | branch gone; only whiff branch remains (boss.nim:202) with the reason commented | yes |
| F10 | fixed, `b9c62e8`, validate compares rounded sum | `config.deadlineSeconds` (config.nim:54) used by both client and `validate` (:88-94); `testEffectiveDeadlinesFitTheTurnBudget` covers 6.2+3.2 refusal | yes |
| F11 | no code change; comment at the call site | engine.nim:101-108 explains where the bound lives; F10+hung-client test make it real | yes |
| F12 | no change, deliberate; judge adjudicates | route at server.nim:420; adjudicated non-blocking above | yes |
| F13 | no change, documented | PROTOCOL.md + manifest `protocols.global` describe JSON `raid.global.v1` | yes |
| F14 | fixed, `f3d455f` | AGENTS.md layout names neither `roster.nim` nor `render.nim`; says where their duties live | yes |
| F15 | no code change; comment | raid_player.nim:44-56 records the deliberate departure; server default implemented (register-with-neither → stalwart) | yes |
| F16 | fixed (comment), `c6df382` | telegraphs.nim crucible branch carries the why-no-avoidable-hit comment | yes |
| F17 | fixed, `46283c9` | PROTOCOL.md boss_hit row documents the single `"raid"` aggregate; test pins 5 alias records + exactly 1 aggregate | yes |
| F18 | fixed in part (`0ea9001`, `6a8a68c`); two gaps recorded | wasm harness runs in CI gated on `WASM-SMOKE OK` (verified in the run log); hung-client and control-byte tests present; no-show/reconnect e2e still untested (recorded honestly — behaviours exist in server.nim, no checklist item requires those two tests) | yes |
| F19 | no change, measured | test pins greenhorn phase==1 on 4 seeds; ladder spread (>2×) asserted; note's floor description stale, repo says nothing false | yes |

One report discrepancy, immaterial: the fixes report says "35 `nim r --hints:off` invocations";
the workflow runs 17 files × 2 modes = 34 test invocations (the 35th match is the log's echo of
the loop). No effect on any disposition.

## Non-blocking observations

- `writeCogameUri`'s own timeout (bitworld/runtime, not in this tree) is unverifiable; the
  episode has settled and scored before the artifact writes, and item 5's named waits are all
  bounded in-tree, so this does not count against item 5. Same for mummy's `send` (inherited by
  every starter); the F5 allowance bounds the loop regardless.
- `raid_player.nim`'s receive loop waits on the server/socket with no timer of its own; bounded
  in practice by the server's own bounded lifetime and pod teardown, and identical to the
  starter convention. Not a checklist wait.
- The F7 design question is settled in this verdict (keep index 95/191 + doc + pinned test); no
  further action needed.

Count: reviewer blocking standing 0 (1 filed, 1 refuted-as-fixed); judge blocking 1 (item 13
browser smoke). Total **1**.

BLOCKING: 1
