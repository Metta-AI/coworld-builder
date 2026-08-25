blocking: 0

# r1 verdict — 2026-08-25-paintball

Head: `44af4da75e82daa73717f036a7b06934515db022` (current `main` of `Metta-AI/cogame-paintball`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule)
Independent read written before reading fixes: **yes** — repo cloned fresh, checklist walked file
by file and against the head CI log (`gh run view 32843017748 --log`) before opening
`r1-review.md`, and `r1-fixes.md` was opened only after both.

CI evidence anchor: run **32843017748**, workflow `ci.yml`, branch `main`,
`headSha 44af4da…`, conclusion **success**; jobs `test`, `docker-smoke`, `wasm-viewer` all
success, every step success, `grep -c continue-on-error .github/workflows/ci.yml` → 0,
`grep -c "SEAT-COUNT FAIL"` over the full run log → **0**.

## Standing blocking findings

None.

## Refuted

The review was written at `27f3057`; 23 commits landed after it. All five of its blocking
findings are refuted **at the current head** — each was real when written and has since been
fixed, verified below from the tree and the head run, not from the fixer's table.

### B1 (reviewer F1) — "`data-replay-error` is never set" → REFUTED (fixed at head)
- Evidence: `replay-viewer/static_replay.js:15-21` at `44af4da` —
  `showFailure()` now opens with
  `document.documentElement.setAttribute('data-replay-error', error && error.message ? error.message : String(error));`
  before touching `#status`. `data-replay-loaded="true"` is still set in the `'loaded'` branch
  (`static_replay.js:151`), which the Worker posts only after `ingestPacket()` handed
  BroadcastCore the first frame (`static_replay_worker.js:127-131`). Fixed in `82a7395`;
  `tests/test_viewer.nim` "the shell sets BOTH load and failure markers on `<html>`" pins it.

### B2 (reviewer F2) — "two assertions deleted from tests/ during this run" → REFUTED (restored and strengthened at head)
- Evidence: `tests/test_control.nim:234-258` at `44af4da` — the test
  "holdline beats sprayer at seed 679961, and the hill changes hands twice" asserts
  `check single.holdline > single.sprayer` (holdline WINS), `check single.flips >= 2` (the hill
  changes hands twice) and `check single.endReason in ["", ReasonComplete]`; a second test
  (`:260-288`) asserts the same ordering over a 3-seed both-sides ladder. Restored in `e8b42cd`,
  made true (rather than the test bent) by `b2a6c3b`'s parameter sweep. I read every
  `git log -p --since=2026-08-25T06:00:00Z -- tests/` hunk: the mid-run deletions
  (`73aa441`, `cd402ea`) happened and were themselves superseded; the current tree's assertions
  meet design §Tests 6 verbatim, and every other test-file change in the window is a
  strengthening or an equivalent-strength rewrite with recorded rationale (e.g. the paint
  mirror-symmetry test now asserts the cone *predicate* is exactly symmetric,
  `tests/test_paint.nim`, because the 34 px grid does not divide 1235 and tile-count symmetry
  was testing quantisation). No skip/xfail, no widened tolerance, no removed file stands.

### B3 (reviewer F3) — "draws LLM text, text gate measured nothing, no worst-case fixture" → REFUTED (fixed at head)
- Evidence at `44af4da`:
  - `replay-viewer/text_fixture.html` (292 lines) loads the **real** `broadcast_core.js` from
    the built bundle, renders a frame with all 8 cogs shouting the full 10-rune cap at the worst
    positions vs the identical quiet frame at 360×640 / 720×480 / 1280×800, and asserts per
    bubble: rect inside board, rect inside canvas, pixels differ inside the rect
    (`drawn < need` throws), stray diff bounded, and its own strings are still exactly `cap`
    runes (`text_fixture.html:190-200`). Failure sets `data-replay-error`, success sets
    `data-replay-loaded`.
  - `ci.yml:410-423` drives it in its own step (`Render the worst-case text fixture`) with
    `viewer_smoke.mjs … --strict-text-bounds`; the head run's step log reads
    `{"loaded":true,…"360x640: scale 0.146, 8/8 bubbles in frame, weakest changed 86 px, 0/702
    changed px stray | 720x480: … | 1280x800: …"}` and
    `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)`.
  - The geometry defect itself is fixed: `global.shoutBubblePlacement` clamps/flips the bubble
    into the board and `shoutBubbleRectFor` (`global.nim:4922-4943`) exports the draw pass's own
    rect, with the reserved band measured from the server's `ShoutMaxChars` cap ("reserved band
    19 px" in the fixture log); `tests/test_shouts.nim` is the tree-level half.
- On the `canvas_text total: 0`: this engine rasterises every canvas string into a sprite in Nim
  (`grep -c 'fillText\|strokeText' client/broadcast_core.js client/chrome_common.js` → 0 and 0),
  so the fillText hook is structurally blind here; item 15's own last bullet prescribes exactly
  this fixture as the gate for that case, and it is present, real (it fails on pixels), and green.

### B4 (reviewer F4) — "a live `/client/replay` pod viewer route exists" → REFUTED (fixed at head)
- Evidence at `44af4da`: `src/paintball/server.nim` registers no `/client/replay`,
  `/clients/replay` or `/client/league` route and embeds neither page —
  `grep -n EmbeddedBroadcastReplayHtml\|EmbeddedLeagueReplayerHtml src/paintball/server.nim` → 0
  hits (only the explanatory comment at `:67-77` remains); the route dispatch (`:638-795`)
  serves `/healthz`, the four websocket paths, control paths and static art only.
  `docs/PROTOCOL.md:15` now lists only `/client/global` and `/client/player`, and none of the
  three manifest-inlined copies (`game.protocols.player/global`, `game.docs.pages[protocol]`)
  contains the string `/client/replay` (checked with json.load). Fixed in `716e1c7`;
  `tests/test_manifest.nim` pins it. Residual occurrences of the string are in starter chrome
  that item 14 requires byte-identical or inherited (`client/broadcast_core.js:196`,
  `client/league_replayer.html`'s native-mode branch) — client-side path derivation for a mode
  the pod no longer offers, not a pod path; filing them would contradict item 14.

### B5 (reviewer F5) — "no test asserts `reason == complete`; no grid harness" → REFUTED (fixed at head)
- Evidence at `44af4da`:
  - `tests/test_replay.nim:203-211` — `check results["reason"].getStr() == ReasonComplete`,
    `endRule in [full_time, mercy, wipe]`, `games == 2`, `finalTick > Ticks`, and
    `check written.violations == 0` where every order and every compiled mask of the real
    all-scripted two-game episode was validated against the legal bounds while it played
    (fixed in `3cc3726`).
  - `tools/tune_baselines.nim` + `tools/ci/baseline_tuning.json` (the 4×4 matrix, 3 seeds × both
    sides, chosen cell `huntRadiusHoldline=130 / guardStandoff=110`, 5/6 wins, margin +1762,
    with the note's own 200/250 guess recorded as the losing row) and `ci.yml:158-159` runs it
    as the `Baseline parameter grid harness` step with `--check`; that step is green in run
    32843017748 (fixed in `b2a6c3b`).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 32843017748 success at `44af4da` (all 3 jobs, no continue-on-error; all 15 test files ran, debug+release, `test_perf` release-only as the note sanctions). `git log -p --since=2026-08-25T06:00:00Z -- tests/` read hunk by hunk: mid-run deletions in `73aa441`/`cd402ea` were restored & strengthened by `e8b42cd`; current assertions meet §Tests (see B2). |
| 2 Replay re-derivation | PASS | `tests/test_replay.nim:213-231` — `initReplayRuntime(data, mismatchQuit = true)`, whole episode re-stepped, `hashMismatchTick == -1`; viewer runs the same module (`replay-viewer/paintball_replay.nim` imports `paintball/sim`, `advanceReplayFrame` at `:103`); CI `Native/wasm hash gate`: `ok: loaded replay.json, advanced 300 frames`. |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s` → 100755), builds via `Dockerfile.replay-viewer`; worker's only network call is `fetch(message.replayUrl)` (`static_replay_worker.js:113`); no pod replay route (see B4). |
| 4 Both name spaces | PASS | `tests/test_identity_privacy.nim` asserts both directions (`:26-56` no policy address in seat frames / LLM message / directive record; `:58-80` roster, `teams.<color>.policies`, `results.names` MUST carry it); viewer maps via `broadcast.nim:332-353` `teamPoliciesJson` ← `seatNames`. |
| 5 Degrade-never-hang | PASS | batch deadlines floored to curly seconds (`decide.nim:400-407`), one retry, per-turn monotonic `turnBudgetMs` bound (`decide.nim:315-316,382-387`), rate-floor sleep bounded ≤ `turnSpacingMs` (`decide.nim:369-372`), budget guard (`:323-330`), engine stop at `wallClockBudgetSeconds=690` top of every loop iteration (`server.nim:1356-1366`), `lobbyJoinTimeoutTicks` (`server.nim:1488-1509`), player receive loop exits 0 on dead socket; 690 ≤ 720 asserted in `tests/test_engine.nim:160` and `tests/test_manifest.nim`. |
| 6 num_agents | PASS | `num_agents: 2` in all 4 variants + `certification.game_config` (json-checked); `docker_smoke.sh:110-151` enforces all four invariants + `SMOKE_SEATS` cross-check with `SEAT-COUNT FAIL:` prefixes; head run log: 0 matches for `SEAT-COUNT`, `smoke OK: seats=2 … reason=complete`. |
| 7 Scripted baseline full episode, tuned | PASS | `tests/test_replay.nim:203-211` (`reason == "complete"`, `violations == 0` over the real episode); `tests/test_control.nim:40-62` (500 states × both baselines, legal orders/masks); grid harness `tools/tune_baselines.nim` + recorded `tools/ci/baseline_tuning.json`, CI step green (see B5). |
| 8 LLM reply handling | PASS | tolerant extraction `directives.nim:102-137` (fences, prose, first-{…last-}); one retry (`decide.nim:379` `attempt < 2`), then holdline fallback with recorded `fallback` record and cause enum incl. `no_credentials`/`budget_guard` (`decide.nim:338-356,442-456`); `tests/test_directives.nim`, `tests/test_engine.nim:53-96`. |
| 9 Rune-safe truncation | PASS | single primitive `directives.nim:61-68` (`runeLen`/`runeSubStr`) applied to note/say/policy/detail/record/prompt; provider bodies rune-cut too (`llm.nim:169-193`, F9 fix); `tests/test_directives.nim:89-163` — 4-byte emoji at the cap, `validateUtf8 == -1`. |
| 10 Manifest validates | PASS | `game.docs.readme {type:text, 4422 ch}` + 3 pages each `{id,title,content{type:text,value}}`; `game.protocols` both `player` and `global` in object form (json-checked); `tests/test_manifest.nim` pins it. |
| 11 Legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`client/replay_broadcast.html:3965-3970`); labels hidden under `.tiny` (`:4004-4006`), toggled at `boardW <= 620` (`:3910`, the starter's threshold the design note pins verbatim). |
| 12 Release order & scaffold | PASS | `coworld-release.yml`: Build manifest (`:153`) → Certify (`:167`, with `--timeout-seconds 300`) → Upload the policies (`:210`) → Upload the Coworld (`:308`) → Put the Coworld secret (`:346`); hosted smoke runs against the image built in the same run. 3 workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions (#2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) + 2 × `PLAYER_SCRIPTED` fillers; placeholder gate ran here and exits 0 (no `<slug>`/`<IMAGE>`/`<SEATS>` in the five files). |
| 13 Viewer executes | PASS | `wasm-viewer` `needs: [docker-smoke, test]` (`ci.yml:274`); `Load the bundle in a real browser` step ran in run 32843017748 and printed `{"loaded":true,"ms":1328,…}` plus scrub readouts reaching `GAME 2/2 · VISITOR`; both markers in the shell (B1); `config.nims` non-MODULARIZE ↔ worker `Module.onRuntimeInitialized` + `importScripts(wire_constants, broadcast_core, paintball_replay)` — one starter, internally consistent. |
| 14 Chrome is the starter's | PASS | `chrome_common.js` byte-identical (`diff` vs `/workspace/starters/coworld-ctf` → 0 lines); `broadcast_core.js` differs in exactly the wire identifier (line 49); `replay_broadcast.html` = starter (4165 lines) + appended game block under the banner (4256 lines; diff confined to title, plate contents, feed/beat routing, endcard, `#viewpanel` removal); `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:3908-3914`); no `position: fixed` anywhere in the page; `#endcard { bottom: var(--band, 0px) }` (`:917`), dismissed on every non-gameover frame (`:1901`); beats are labelled `<button>`s seeking via `CTX.send('s:'+tick)` (`:4071-4091`) with CSS for every emitted beat kind (gamestart, hillflip.red/.blue, tagout.red/.blue, gameover, `:4020-4043`; chrome's own `ingestBeats` only marks steal/return/capture, which never fire — flags retired); `#viewpanel`/minimap/zoombar removed, not hidden (`:705-712`, `:1372`) — fixed arena. |
| 15 Drawn strings fit | PASS | `--strict-text-bounds` on both browser steps; smoke `canvas_text` = `{total 0, never_inside 0}` — vacuous for a sprite-text engine, which is exactly the case item 15's last bullet covers: the worst-case renderer fixture exists, is real (per-bubble pixel assertions, full-cap-rune self-check, 3 canvas sizes incl. 360 px), runs in its own ci.yml step and passed 8/8 bubbles in frame at every size; reserved band measured from `ShoutMaxChars` in the drawing font (19 px); `tests/test_shouts.nim` gates the geometry in the tree. No ellipsis on sentences (bubbles clamp/flip, never shorten). |
| batch rule | PASS | one `RequestBatch` per attempt, both seats posted into it, single `makeRequests` call (`decide.nim:390-407`; the only `makeRequests` site in `src/`); `tests/test_engine.nim:9-26`. |

## Fixer report audit

Read only after the independent pass above. Spot-verified against the tree and the head run:

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed `82a7395` | `static_replay.js:15-21` sets the attribute; test present | yes |
| F2 | fixed `e8b42cd` | both assertions back and true (`test_control.nim:251-252`); hunks read | yes |
| F3 | fixed `1dddbb1`+`6cb57ad` | fixture + clamp + CI step + 8/8 in-frame log line | yes |
| F4 | fixed `716e1c7` | no route, no embedded pages, docs/manifest clean; residue is item-14 bytes | yes |
| F5 | fixed `b2a6c3b`+`3cc3726` | `reason == complete` + `violations == 0` asserted; harness in CI, record committed (`b2a6c3b` exists in history; the fixes table's per-finding shas all resolve) | yes |
| F11 | NEEDS-DESIGN, no change | the sleep is real (`decide.nim:369-372`) and bounded; no checklist item forbids a bounded wait; see observations | yes |
| F12 | fixed `fef02d9` | `no_credentials`/`budget_guard` fallbacks recorded (`decide.nim:338-356`); the two test assertions it replaced were strengthened, not loosened (hunks read) | yes |
| F14 | DISPUTED | reviewer's observation accurate, conclusion not: `farthestHillTile` is load-bearing for the anti-stalemate pin the design itself demands (`test_control.nim:119-232` proves 100% takeability); advisory anyway — no checklist item | yes |
| F19 | fixed `7cf6f0f` | the four `delete` calls removed (`git show 7cf6f0f`), comment explains | yes |
| F27 | fixed `b3bd645` | `checkPaintInvariants` raises `SimGuardError` (`paint.nim:208-234`), server maps to `sim_fault`/`host_error` (`server.nim:1956-1963`), artifacts still written | yes |
| F15/F22/F23/F25 | NOTED, not fixed | accurate observations, none tied to a checklist item | yes |

## Non-blocking observations

- **`turnSpacingMs` is a bounded blocking sleep on the loop thread** (`decide.nim:369-372`),
  where the design note says the loop keeps stepping. Bounded (≤ 5 s/turn, booked in the note's
  own 200 s line, covered by the 690 s stop), so item 5's letter holds; the note and the code
  should be reconciled (the fixer's NEEDS-DESIGN framing is right). Categories hang/timeout do
  **not** apply — every wait has an explicit bound.
- **`canvas_text.total` is 0 in both browser steps** — permanently, since this engine draws no
  canvas text via fillText. The strict flag is therefore vacuous on the main smoke; the pixel
  fixture is the real gate. If the renderer ever gains fillText text, the flag becomes live again.
- The checklist's "labels hidden under 640px" is implemented as the starter's `boardW <= 620`
  `.tiny` toggle (the design note pins 620 verbatim); substance satisfied.
- `client/league_replayer.html` is kept in the repo and built into the bundle as `league.html`
  while no pod route serves it; its `/client/replay` string lives only in its native-mode branch.
  Deleting it is a design-note decision, not a defect.
- Advisory residue the fixer left NOTED (F15, F22, F23, F25) is accurately characterised and
  none falsifies a checklist item.

BLOCKING: 0
