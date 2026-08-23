blocking: 0

# r2 verdict — raid
Head: dc8ef5d84dfe1214b0b3e67b83fd101edff2f689   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Fresh clone of `Metta-AI/cogame-raid` at `dc8ef5d` (verified `git rev-parse HEAD` = the brief's
sha = current `main` tip). Review adjudicated: `r2-review.md` (1 blocking B1 + 10 advisory
N1–N10, written against `6a8a68c`). Commits since the review sha
(`git log 6a8a68c..dc8ef5d`): `e0b84a1` (B1 — browser-load step, viewer_smoke.mjs,
`needs: docker-smoke`, smoke-replay artifact hand-off), `ed9650f` (B1 fix-forward — pipefail-safe
replay pick), `dc8ef5d` (N2 — RULES.md step 8(f) + manifest regen). Only
`.github/workflows/ci.yml`, `tools/ci/docker_smoke.sh`, `tools/ci/viewer_smoke.mjs` (new),
`docs/RULES.md` and `coworld_manifest_template.json` changed; `src/`, `tests/`,
`replay-viewer/` and `client/` are byte-identical to the reviewed sha.

CI evidence: run **32623861432**, `main`, sha `dc8ef5d`, conclusion `success`; jobs
`test` / `docker-smoke` / `wasm-viewer` all `success`, every step `success`, none skipped
(`gh run list`, `gh run view 32623861432 --json jobs` — checked myself, not taken from the
fixer's report).

## Blocking items (coordinator format)

None.

## Standing blocking findings

None. The reviewer's single blocking finding is refuted-as-fixed at head (below), and my
independent checklist pass found nothing the reviewer missed.

## Refuted

### B1 — "the `wasm-viewer` job never executes the viewer in a browser" → REFUTED (fixed since 6a8a68c, commits `e0b84a1` + `ed9650f`)
The finding was **correct at the reviewed sha** — r1's verdict carried the same item — and is
false at head on every one of its named conditions:
- **Step present and ran.** `.github/workflows/ci.yml:322-345` (`Load the bundle in a real
  browser`, a plain `run:`, no `if:`, no `continue-on-error` — `grep -n continue-on-error
  .github/workflows/*.yml` → no matches). In run 32623861432 the step's conclusion is
  `success` and its log shows the harness executing, not merely present:
  `loading dist/smoke/replay.json in dist/static-replay-viewer` then
  `{"loaded":true,"ms":309,"clock":"0:00 TURN 0/10","scorebug":"0:00 TURN 0/10","feed_lines":0}`
  and `scrub readouts: 0%="0:00 TURN 0/10"  50%="0:14 TURN 2/10"  100%="0:26 TURN 5/10"` —
  the item's required `loaded: true`, plus proof the replay advances.
- **Harness present and honest.** `tools/ci/viewer_smoke.mjs` (451 lines, mode 100755) is
  **byte-identical to the builder template** (`diff` against
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` → empty), so it was not
  weakened in the copy: it fails immediately on `data-replay-error` or a bridge `error`
  (`:344-345`), fails on silence at the timeout (`:350-351`), passes only on
  `data-replay-loaded="true"` or the bridge's `ready` (`:346-348`), and `process.exit(1)`s on
  failure.
- **`needs: docker-smoke` real, not cosmetic.** `ci.yml:212` `needs: docker-smoke`; in run
  32623861432 `docker-smoke` completed `06:48:56Z` and `wasm-viewer` started `06:48:58Z`
  (in the reviewed run 32621942459 they had started in parallel).
- **The replay hand-off exists.** `tools/ci/docker_smoke.sh:58` (`replay_out=…dist/smoke/
  replay.json`) and `:303-315` (the copy-out block); `ci.yml:184-191` uploads `smoke-replay`
  (`if-no-files-found: error`), `ci.yml:290-294` downloads it; docker-smoke's log:
  `replay saved for the viewer smoke: …/dist/smoke/replay.json (47263 bytes)`.
The intermediate run 32623414696 at `e0b84a1` failed exactly where the fixer says (the
template's pipefail glob), and `ed9650f` replaced it with a `for` loop
(`ci.yml:326-333`) that preserves the "docker-smoke uploaded no replay" hard failure.

### N2 — sixth ability phase undocumented → fixed at `dc8ef5d`
`docs/RULES.md:227-230` now lists `(f) heal cast starts (seat order)` with the aging rule
(`a cast begun on tick t first ages on t + 1 and lands exactly 24 ticks later`), matching
`src/raid/sim.nim:418-424` / `src/raid/abilities.nim:191-193`; the manifest was regenerated
(`game.docs` inlines RULES.md — the diff is the one changed line). Was advisory anyway.

### N1, N3–N10 — accurate as filed, all advisory, none falsifies a checklist item
Each re-verified at head from the code the reviewer cited:
- **N1** `baselines.nim:195-200,236-241` — tank `rxDodge`/`stPoint`, healer on `HealerStands`;
  departure argued in the comment ending "So the default reaction is `dodge`, not the note's
  `hold`." Item 7 asks only for a full legal episode (`tests/test_baselines.nim:154`
  `reason == "complete"`) and a tuning harness (`tools/tune_baselines.nim`, present). Advisory.
- **N3** `control.nim:147,157,356-358` — `HealWasteFloor`/`planted` gates exist, commented; no
  checklist item covers heal gating. Advisory.
- **N4** `types.nim:98,104` — `CleaveFirstTick = 96` armed pre-tick-0 → fires index 95;
  adjudicated in r1 (F7), doc+test pin it. Advisory.
- **N5** `telegraphs.nim:104-109` — crucible branch skips `avoidableHits` with the reason in a
  comment; a meter, not the score. Advisory.
- **N6** `server.nim:420` — `/client/replay` local route; adjudicated in r1 (F12). I checked the
  substance independently: the manifest declares `"replay_viewer": {"bundle":
  "static-replay-viewer"}`, `coworld-release.yml:195-201` hard-fails certification on a
  pod-served viewer, and the worker fetches only the `?replay=` URL + same-origin assets
  (`static_replay_worker.js:118`). I concur with the r1 adjudication; count zero.
- **N7** `server.nim:250-255` — one `epochTime()` around the single `decideAll`; batch-wide
  `latency_ms` confirmed. The per-seat shape is a consequence of the one-parallel-batch rule the
  checklist itself imposes. Advisory.
- **N8** — `grep -rn 'broadcastDone\|reconnect' tests/` → no test; the done-broadcast bound is
  *enforced* in code (`server.nim:129-149`, cumulative seats × 3.0 s, seat skipped past it),
  which is what item 5 asks. §Tests-list gaps are design-note items, not checklist items.
  Advisory, stands as recorded-open.
- **N9** `raid_player.nim:83-88` — blocking `receiveMessage()` loop confirmed; item 5 names the
  LLM call, seat reply and round barrier (all server-side, all bounded); starter convention
  (`cogame-bullwhip/src/bullwhip_player.nim:53-58` identical). Advisory.
- **N10** `llm.nim:187-188` — `output_config.effort` sent for non-Haiku models confirmed;
  identical lines ship in the babel and bullwhip starters; failure mode is a recorded fallback.
  Advisory.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run **32623861432** at `dc8ef5d`, conclusion `success`, all jobs/steps success (cited above). `git log -p --since="2026-08-22T23:59:00Z" -- tests/` read hunk by hunk: 9 commits, all additive except `501040d`'s `int`→`int64` digest widening (same assertions, same golden-fixture comparison — read in full) and the r1-noted removal of two never-read `FakeClient` fields. No assertion deleted, no tolerance widened, no skip/xfail added, no test file removed. `NIM_TESTS*` repo vars unset in the run log (env block empty); 17 files × 2 modes ran. |
| 2 Replay re-derivation | **pass** | `src/raid/replay.nim:148` `rederive` re-runs the sim from seed+map+config+recorded orders; `:190` `firstDigestMismatch` compares every keyframe digest; `:208` `controlsMatch` byte-compares controls. `tests/test_replay.nim:82-86` asserts both (`firstDigestMismatch == -1`, "byte for byte"). Viewer displays the re-derivation: `replay-viewer/raid_replay.nim:54-56` `rederive(payload, keyframeEvery = 1)` → `frames = rebuilt.keyframes`; recorded keyframes feed only the mismatch marker. |
| 3 Static viewer | **pass** | Manifest `game.replay_viewer = {"bundle": "static-replay-viewer"}` (parsed directly); `tools/build_replay_viewer.sh` present, mode 100755, wired as the build hook (asserted executable in ci.yml and required by `coworld build`); worker contacts only the `?replay=` URL + same-origin bundle assets (`static_replay_worker.js:118`, `credentials: 'omit'`). `/client/replay` is a local-debug game-server route, not a declared viewer path — adjudicated r1, concurred (N6 above). |
| 4 Both name spaces | **pass** | `broadcast.nim seatView` alias-only; `tests/test_view.nim:56-76` greps a serialised view for real names, the seed, other notes and prompt text; real names in `replay.names.players`, `results.names`, `/global`, and the viewer plates (`replay_broadcast.html:1836` plate-name from `meta.names.players`). |
| 5 Degrade-never-hang | **pass** | LLM: `curly.makeRequests(batch, timeout)` with `deadlineSeconds(llmAttempt/llmRetry)` (`llm.nim:281-283`), rounded sum ≤ `turnBudgetSeconds` enforced at `config.nim:88-94`; connect bounded by `playerConnectTimeoutSeconds` + 3 s register grace (`server.nim:196-215`); done broadcast enforced at seats × 3.0 s (`server.nim:129-149`); budget guard `engine.nim:87-99`; unconditional hard stop `engine.nim:113-118`. `wallClockBudgetSeconds = 660 ≤ 720 = 0.6 × 1200` (`config.nim:42,95-98`; `tests/test_manifest.nim` asserts per variant). Hung-client test drives 10 s stalls per turn and asserts complete-inside-budget (`tests/test_engine.nim:160-196`). |
| 6 num_agents | **pass** | `num_agents = 5` in both variants' `game_config` and `certification.game_config`; `len(certification.players) = 5 = len(certification.game_config.players)` (parsed directly). `tools/ci/docker_smoke.sh:98-143`: four invariants + independent `SMOKE_SEATS` cross-check, each `SEAT-COUNT FAIL:`-prefixed and fatal. **`grep -c 'SEAT-COUNT FAIL'` over run 32623861432's full log → 0**; smoke logged `game=raid seats=5` and `smoke OK: seats=5 results=1440B replay=47263B reason=complete`. |
| 7 Scripted baseline, tuned | **pass** | `tests/test_baselines.nim:154` `reason == "complete"` on the cert fixture; `:76-148` order legality, control-byte ranges, role-bit ownership, cooldown legality across 3 deals × 2 baselines; grid harness `tools/tune_baselines.nim` committed (135-point intdefine sweep). |
| 8 LLM reply handling | **pass** | `orders.nim:13-48` tolerant extraction (fences, prose, balanced-brace scan, truncated-reply fallback); exactly one retry (`llm.nim:269` `for attempt in 0 .. 1`, `RetryHint` appended); fallback = stalwart with `source: osFallback` + `cause` + rune-capped `detail` (`llm.nim:295-303`), recorded as a `fallback` event and per-seat `fallback_causes` in results (`engine.nim:34-48`, `scoring.nim:75-79`) — countable in phase 60. |
| 9 Rune-safe truncation | **pass** | `labels.nim:49` `runeCap` (utf8Only + runeSubStr) on every replay-bound string: say/note (`orders.nim:153-154,247-248`), policy label, fallback/fault detail, captured errors (`llm.nim:204,212,217,226,266,301`). Multi-byte-at-cap tests: `tests/test_orders.nim` (4-byte emoji astride the 400/300/300/160 caps, 200th detail rune, invalid-UTF-8 body) + `tests/test_replay.nim:36-40` whole-file `validateUtf8 == -1`. Green in 32623861432. |
| 10 Manifest validates | **pass** | `game.docs = {readme:{type:"text",value:…}, pages:[{id:"rules.md",…},{id:"protocol.md",…}]}` each `{"type":"text","value":…}`; `game.protocols` carries both `player` and `global` (parsed directly from `coworld_manifest_template.json` at head, i.e. post-`dc8ef5d` regen). |
| 11 Viewer legible at 360 px | **pass** | `client/replay_broadcast.html:1556` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`; `:1612` `@media (max-width: 640px)` hides labels. |
| 12 Release order and scaffold | **pass** | `coworld-release.yml`: build manifest (:153) → certify (:167) → upload policies (:206) → upload coworld (:304) → secret put (:342); docker-smoke builds the image in-job before smoking it; wasm-viewer builds the bundle it loads in-job. Three workflows present; `docker_smoke.sh` mode 100755. `policies.json`: 4 policies — `raid-anvil` (`PLAYER_PROMPT`), `raid-triage` (`PLAYER_PROMPT`, carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `raid-stalwart`/`raid-greenhorn` (`PLAYER_SCRIPTED`). Placeholder gate run verbatim over the five files: no `<slug>`/`<IMAGE>`/`<SEATS>` match → exits 0. |
| 13 Viewer executes | **pass** | Bullet 1: run 32623861432 `wasm-viewer` green **including** `Load the bundle in a real browser` (plain `run:`, ran, logged `{"loaded":true,"ms":309,…}` + differing scrub readouts); `needs: docker-smoke` at ci.yml:212, real in the timings (docker-smoke done 06:48:56Z, wasm-viewer start 06:48:58Z). Bullet 2: `static_replay.js:150` sets `data-replay-loaded="true"` on the worker's `loaded` (posted only after `core.ingest(first)`); `:40` sets `data-replay-error` in `showFailure`, reached from missing-`?replay=`, fetch-timeout, worker-error/crash and no-OffscreenCanvas paths. Bullet 3: `config.nims:45-46` `-s MODULARIZE=1 -s EXPORT_NAME=RaidReplayModule` ↔ worker factory `self.RaidReplayModule({...})` (`static_replay_worker.js:86`); `grep -rn onRuntimeInitialized` → no matches. No lantern deadlock, and this time the browser proved it. |
| One-parallel-batch | **pass** | `llm.nim:269-283`: one `RequestBatch` over every open seat, single `makeRequests` per attempt, no per-seat loop; `tests/test_engine.nim` asserts overlapping in-flight windows ("all living seats go out as one parallel batch" — in the run 32623861432 test log). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `e0b84a1`+`ed9650f`; harness byte-identical to template; loaded:true in 32623861432; needs-edge real in timings | all confirmed independently before reading the report: diff vs template empty; step ran with `{"loaded":true,"ms":309,…}`; job timings 06:48:56Z/06:48:58Z; artifact hand-off present both ends; no `continue-on-error`/`if:` | yes |
| N2 | fixed, `dc8ef5d`, doc + manifest regen, no code change | RULES.md:227-230 lists (f) with the aging rule; manifest diff is the one inlined line; sim.nim unchanged | yes |
| N1, N3–N7, N9, N10 | no change, evidence in place / adjudicated r1 | each re-verified at the cited lines (see Refuted §N-items); r1 adjudications (N4/N6) quoted accurately | yes |
| N8 | not fixed, recorded open | no `broadcastDone`/reconnect test in tree; bound itself enforced at server.nim:129-149; no checklist item requires the tests | yes |
| Runs table | 32623414696 failure (pipefail exit 2), 32623664165 first green, 32623861432 head green | matches `gh run list` exactly (failure at `e0b84a1`, successes at `ed9650f`/`dc8ef5d`) | yes |

## Non-blocking observations

- The fixer's NOTED item is real and worth the coordinator's attention: the **builder template**
  `templates/ci.yml` still carries the pipefail `ls` glob that made run 32623414696 fail; any
  future coworld scaffolding it will hit the same bare `exit code 2` on its first browser-smoke
  run. Outside this repo and this checklist; no count.
- The r2 reviewer's "could not determine" on the emsdk build being a full compile is moot at
  head: whatever the layer caching, the browser loaded and scrubbed the bundle that build
  produced, which is the evidence item 13 names.
- N8's two untested behaviours (done-broadcast bound under a stalled reader; no-show/reconnect
  e2e) remain honest residue for a later round; both behaviours exist in `server.nim` and no
  checklist item names the tests.

Count: reviewer blocking standing 0 (1 filed, 1 refuted-as-fixed at head); judge blocking 0.
Total **0**.

BLOCKING: 0
