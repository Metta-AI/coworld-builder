blocking: 0

# r2 verdict — liars-dice

Head: `43159194d42cd46da491f74827bb7215f5168ec2` (main = origin/main, checked out at
/tmp/cogame-liars-dice)   Checklist: coordinator brief §ACCEPTANCE CHECKLIST (verbatim;
`prompts/30-review-loop.md` §Judge brief rule applied)   Independent read written before
reading fixes: **yes** (design note → full tree at head → CI run 33017451131 logs → then
r2-review.md → then r2-fixes.md, in that order; the fixer's report was consulted only for
attribution after my own pass was complete).

The review under judgment (`r2-review.md`) was written against `8e74a850`. Three commits landed
after it: `ae4b86e` (F1), `93648eb` (F3), `4315919` (F4, = head). Every claim below is verified
at the **current head**, not at the reviewed sha.

## Standing blocking findings

None.

## Refuted

None. Every finding in r2-review.md reproduced exactly at the sha it was written against
(checked from the `ae4b86e`/`93648eb`/`4315919` diffs, whose "before" side is `8e74a850`).
Nothing in the review was wrong or overstated — its findings are **resolved**, not refuted.

## Resolved since the review (true at 8e74a850, fixed at head)

### F1 — baseline thresholds had no tuning provenance (checklist 7, 2nd sentence) → RESOLVED
- Was true at `8e74a850`: `git show ae4b86e -- src/liars_dice/llm.nim` shows the before-state —
  `BayesChallenge = 0.40` / `BayesSafe = 0.55` as bare constants, no harness anywhere (the
  review's tree-wide absence evidence was accurate).
- Resolved at head by `ae4b86e`, and I verified each leg independently:
  - **The harness is real and sweeps a grid, not two points.** `tools/tune_baseline.nim:39-41`
    defines `ChalGrid` (11 values, 0.05..0.55) × `SafeGrid` (10 values, 0.25..0.70) = 110
    cells; `main()` (lines 170-186) plays a **full round robin** — every cell vs every other
    cell, two seats each at a 4-seat table, both seatings, seeds × 30 deals — through
    `scriptedActionWith` (`llm.nim:199-258`, the same decision body the shipped baseline runs,
    parameterised by `Thresholds`). `--check` (lines 292-306) exits 1 unless the shipped point
    is the grid optimum or paired-tied with it (paired by seed, 2 s.e.), and lines 216-223
    quit(2) if the shipped constants are not even on the lattice — so the gate reads the real
    `BayesChallenge`/`BayesSafe` (`tune_baseline.nim:43`) and hand-editing them fails CI.
  - **The committed table exists and is consistent with the shipped constants.**
    `data/tuning/threshold_sweep.tsv` (120 lines): header `# shipped point: 0.15/0.35
    (BayesChallenge/BayesSafe), rank 8 of 110`, `# grid optimum: 0.10/0.30 score 0.51884;
    shipped 0.51872; paired gap 0.00011 (2 s.e. band 0.00034) -> tied`; row 18 carries
    `8  0.15  0.35  0.51872 … <-- SHIPPED`; row 90 shows the old pair `80  0.40  0.55  0.49236`
    — matching `llm.nim:35-36` (`BayesChallenge* = 0.15`, `BayesSafe* = 0.35`) and the design
    errata (design.md §Errata, 2026-08-26 r2 F1, sanctioned per the coordinator).
  - **The CI step ran green at head.** Run 33017451131 (headSha `43159194…`, conclusion
    `success`), job `test`, step "Sweep the scripted baseline's thresholds" (ci.yml:161-164,
    `tune_baseline.nim --check`, whole 110-point lattice at 8 seeds) — success; log:
    `# grid optimum: 0.15/0.35 score 0.52114; shipped 0.52114; … -> shipped IS the optimum` and
    `OK: the shipped point 0.15/0.35 is the grid optimum over 110 points`.
- The review asked for "the shipped 0.40/0.55 identifiable as the grid's pick"; the sweep showed
  0.40/0.55 loses (rank 80, below break even), so the constants were reshipped to the plateau
  centre instead. That satisfies item 7's actual text ("tuned with a grid harness, not guessed")
  more honestly than defending the old pair would have.

### F3 (non-blocking) — raise-enumeration bound untested → RESOLVED
- `93648eb`: `iterator raiseCandidates*` (`llm.nim:187-197`) is now the single source of the
  window and the baseline iterates it (`llm.nim:230`); `tests/test_bot.nim:153-197` counts it on
  real mid-deal states in both modes, asserts every candidate inside
  `q0 .. q0 + RaiseQuantitySteps - 1` on a legal face, count ≤ `RaiseQuantitySteps * faces`,
  and `check widest == ceiling` so the bound is not vacuous. Green in run 33017451131 (both
  debug and `-d:release`).

### F4 (non-blocking) — hand-mirrored caps unchecked → RESOLVED
- `4315919`: `tools/ci/build_renderer_fixture.sh:21-45` `assert_cap` reads `MaxSayLen`/
  `MaxNotesLen` out of `src/liars_dice/sim.nim` and exits 1 unless `client/renderer.js` and
  `client/fixtures/worst_case.js` carry the same numbers; runs in the `renderer-fixture` job
  before assembly. Head log: `cap MaxSayLen = 140 agrees…` / `cap MaxNotesLen = 400 agrees…`.

### F2 (non-blocking) — design note's fixed line counts stale → RESOLVED by sanctioned errata
- design.md §Errata (two dated 2026-08-26 entries, both sanctioned per the coordinator's brief)
  records the checklist-15 band-spec override and the F1 retune; the tree is untouched by it.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run 33017451131, headSha `43159194…`, conclusion `success`, all 4 jobs + all steps success. `git log -p --since=2026-08-26T16:00:00Z -- tests/` shows exactly three commits: `0c5587c` (creation), `8e74a85` (+48 lines, new frame-by-frame test), `93648eb` (+46 lines, new enumeration test). **Every hunk is additive** — no deleted assertion, no widened tolerance, no skip, no file removed. On the flagged retune: the calibration test (`tests/test_bot.nim:132-151`) asserts `bayesMean > 0.5` / `pressureMean < 0.5` — threshold-independent — and was **not modified by any commit**; `ae4b86e` touched no test file (`git show ae4b86e --stat`). The brief's premise that the retune "changed expected values in an existing calibration test" is not borne out by the hunks: the test carried no numeric expected values to change, only the >0.5/<0.5 direction, which held before (0.5167/0.4833) and holds wider after (0.525/0.475). Not a loosening. |
| 2 replay re-derivation, viewer reads it | **pass** | `sim.nim:667-702` `replayMatch` re-derives frames through the same `applyBid`/`applyChallenge`, cross-checks recorded `deal` events against the seed (raises on mismatch, sim.nim:689-692). Tests: `tests/test_sim.nim:522-568` compares **every** live-observed frame's `tableStateJson` against the replay-derived frame at that index (`compared >= events.len`); `tests/test_sim.nim:570-589` doctored-hand and wrong-seed rejection; `tests/test_replay.nim:101-141` drives the wasm entry's own `buildReplayPayload`. Viewer: `replay-viewer/liars_dice_replay.nim:42-44` builds `states` from `replayMatch`; `renderer.js:1519-1521` draws `currentState()` from those states — not from a parallel recording. |
| 3 static viewer | **pass** | `coworld_manifest_template.json:14-16` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755 (git index), asserted executable in ci.yml:239-250 and invoked as the `coworld build` hook contract (one absolute output dir, emits index.html + wasm). `static_replay.js:76` fetches only the `?replay=` URL (AbortController-bounded, 20 s); no other network call in the bundle. The `/client/replay` HTTP route (`server.nim:547`) is the **starter's own live-server page** (byte-matched at `cogame-babel/src/babel/server.nim:502`), not a viewer pod path: no manifest or workflow declares a pod viewer, and `coworld-release.yml:207` actively rejects one. |
| 4 both name spaces | **pass** | Prompts and player frames use aliases only (`llm.nim:279`, `server.nim:465`, `sim.nim:137-148 tableNames`); `results.names` = policy names + `results.aliases` (`sim.nim:545-549`); viewer maps alias→policy for non-baseline seats: `renderer.js:871-879` `isBaselineFiller` / `makeNameMap`. |
| 5 degrade-never-hang | **pass** | Player connect bounded at `playerConnectTimeoutSeconds` (server.nim:251-259); LLM call bounded by `curl.post(…, client.timeoutSeconds)` (llm.nim:474), ≤ 2 attempts (llm.nim:557); `playDeadline = gameStart + 0.6 × timeout` (server.nim:281-283, `PlayBudgetFraction = 0.6` server.nim:235), `callGuard = 2×llmTimeout+5` checked before every call (server.nim:286, 345-349); deal boundary past deadline ⇒ `endEarly()` (server.nim:308-318); bid cap forces a challenge with no model call (server.nim:327-333, `sim.nim:262-264`); pacing capped by `PacingBudgetMs` at sample time (sim.nim:179-180). No unbounded loop or blocking read on the game path; player exits on `final` or socket close (liars_dice_player.nim:64-90). |
| 6 num_agents + seat invariants | **pass** | `num_agents: 4` in all three variants and the cert fixture (manifest, verified by JSON parse: variants standard/poker/silent all (4,4), cert 4/4/4). `docker_smoke.sh:110-151` enforces all four invariants (missing → `SEAT-COUNT FAIL`, positive-int, cert.players len, game_config.players len) plus the independent `SMOKE_SEATS` cross-check (lines 146-151), each exiting non-zero with the `SEAT-COUNT FAIL:` prefix. Head docker-smoke log grep for `SEAT-COUNT FAIL`: **0 occurrences**; positive path logged `game=liars-dice seats=4 …` and `smoke OK: seats=4 … reason=complete`. |
| 7 scripted baseline full legal episodes; grid-tuned | **pass** | `tests/test_bot.nim:82-112`: both baselines × 4 seeds × 2 modes × talk × seats {3,4,6} to natural end, `check sim.reason == "complete"` (line 97), every action legality-checked before apply (lines 53-76). Tuning: `tools/tune_baseline.nim` 110-point round robin + `data/tuning/threshold_sweep.tsv` (rank 8, `<-- SHIPPED`, tied with argmax) + ci.yml:161-164 `--check` gate, green at head ("shipped IS the optimum"). See F1 resolution above. |
| 8 LLM reply handling | **pass** | `extractJsonObject` (llm.nim:439-449) pulls the first `{…}` out of surrounding prose/fences; `decide` retries **once** with the reason (llm.nim:557-567) after probing the reply on a copy of the sim (llm.nim:571-578); second failure ⇒ scripted move with `fallback = true` (llm.nim:586-588), recorded on the event (`sim.nim:436, 491` — `event.fallback`) so phase 60 can count it. `tests/test_bot.nim:225-289` covers synonyms, numeric strings, rejects, probe rejection. |
| 9 rune-safe truncation | **pass** | `cutRunes`/`cleanSay`/`cleanNotes` (sim.nim:120-133, `runeSubStr`); prompt cap rune-safe (server.nim:513-516); diagnostics `clipText` rune-safe (llm.nim:84-87). Tests at the cap with multi-byte input asserting `validateUtf8 == -1`: tests/test_sim.nim:416-437, tests/test_bot.nim:253-265, tests/test_replay.nim:120-122 (whole payload). |
| 10 manifest validates | **pass** | `game.docs` = `readme {"type":"text","value":…}` (924 chars) + `pages [{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}}]`; `game.protocols` carries both `player` and `global` (verified by JSON parse of the template). |
| 11 viewer legible at 360 px | **pass** | `client/chrome.css:506` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; labels hidden under 640 px (chrome.css:521-524 `@media (max-width: 640px) { .plate-label { display: none; } … }`). Corroborated by the renderer fixture rendering down to 360×640 with 0 never-inside strings. |
| 12 release order & scaffold | **pass** | `coworld-release.yml` step order in one job: Build the Coworld manifest (159) → Certify locally (173) → Upload the policies (212, commented "BEFORE upload-coworld") → upload-coworld (315) → Put the Coworld secret (348, "AFTER upload-coworld"); certify runs against the manifest built in the same run. All three workflows present; `docker_smoke.sh` git mode 100755. `tools/ci/policies.json`: 4 distinct policies — 2 PLAYER_PROMPT champions (calibrator, needler) + 2 scripted fillers (bayes, pressure); champion #2 (needler, the second PLAYER_PROMPT entry) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The three-name placeholder grep gate exits 0 (run in the sandbox: no match in any of the five files). |
| 13 viewer executes | **pass** | Run 33017451131, job `wasm-viewer` (`needs: docker-smoke`, ci.yml:226), step "Load the bundle in a real browser" success, no `continue-on-error`, loading the docker-smoke replay: `{"loaded":true,"ms":292,…}` + moving scrub readouts (`DEAL 0 / 3` → `DEAL 2 / 3 · SPROCKET TO ACT` → `DEAL 3 / 3 · FINAL`). Markers: `renderer.js:1579` sets `data-replay-loaded="true"` after the first synchronous `renderer.draw` (frame IIFE runs before the setAttribute); `static_replay.js:56` sets `data-replay-error=<message>` on missing `?replay=`, fetch timeout (20 s), or wasm rejection, cleared on retry (107, 134). Link flags and bootstrap are a matched pair from one starter: `config.nims:43-46` `-s MODULARIZE=1 -s EXPORT_NAME=LiarsDiceReplayModule` + `_ld_*` exports; `static_replay.js:138` calls the factory `LiarsDiceReplayModule()`; zero `onRuntimeInitialized` anywhere. |
| 14 chrome is the starter's | **pass** | Babel lineage (design note's mapping table, §Viewer): `chrome.css` — starter lines 1-434 **byte-identical** (diff shows only `435,439c` and `443a`: the starter's game-tail block replaced under the banner `liars-dice additions to the inherited cogame-babel chrome` + appends, exactly the removal the note lists); `renderer.js` — all chrome machinery present and aligned (makeRenderer at line 89 both sides; makeEffects/buildScrub/renderFeed/updateScorebug/bindFeedToggle/attachLive/attachReplay/makeNameMap all preserved), diff confined to the sanctioned stage swap (drawCard/drawShape/SHAPES → drawFelt/drawDie/drawCup/drawBidPlate) + the two named patches the note records (relayout, labelled beat-marker buttons) + the r1/r2-fix band sizing; pages — `client/replay.html` and `replay-viewer/index.html` are the starter's pages with the rename + a game block appended under the banner comment (diff: title/wordmark/namespace rename + appended `relayout()` block only). Transport rules: (a) `relayout()` measures `#transport`, sets `--band`/`--hudscale` on `document.documentElement` (renderer.js:1250-1260); (b) nothing fixed-positioned in the band — the one viewport-anchored overlay rides it (`#loading { bottom: var(--band, 0px) }`, chrome.css:554); (c) endcard = `#endscreen` `inset:0` inside `#board-wrap` (the transport's sibling, so its floor is the band top), shown with `.show` matching its CSS rule `#endscreen.show` (chrome.css:381), and **every** seek takes it down — `updateEndscreen(…, index >= events.length, …)` runs on every `setIndex` (renderer.js:1546-1548), and beat-marker clicks route through the same `onSeek` (renderer.js:1454-1459); (d) beats are labelled `<button type="button">` with aria-label/title seeking to their tick (renderer.js:1448-1460), with CSS for every kind emitted — bid / challenge-hit / challenge-miss / forced / end (chrome.css game block 456-479). Zoom/minimap: no `#viewpanel` anywhere — fixed arena, babel ships none, none added. |
| 15 every drawn string fits | **pass** | `viewer_smoke.mjs` reports `canvas_text {total, outside, never_inside, ellipsized}` (lines 327-350) and `--strict-text-bounds` fails on `never_inside > 0` (lines 601-603). Head evidence: wasm-viewer step `canvas text: 2461 drawn, 0 never inside … 0 ellipsized (--strict-text-bounds)` — total nonzero, gate armed (ci.yml:328-332). The repo draws model text, and the required worst-case fixture exists and is gated: `renderer-fixture` job (ci.yml:377-422) builds `client/fixtures/worst_case.{html,js}` — real renderer.js via real attachReplay, full-cap 140-rune say on every seat + 400-rune notes with an unbreakable 44-char token, 7 canvas sizes down to 360×640, asserts its own strings stay full-length (`exact()` throws on shortening; drawn fragments must reconstruct the source) and intercepts/holds `data-replay-loaded` until every size passes — run with `--strict-text-bounds` in its own step. Head log: `{"loaded":true,…}` and `canvas text: 81758 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. Bands sized from the server caps in the drawn font (`capLines`/`advance`/`seatBlock`, renderer.js:143-244), and the mirror is now machine-checked against sim.nim (build_renderer_fixture.sh:21-45). |
| batch rule (simultaneous games) | **n/a — sequential** | The design note states the shape itself: "Sequential, not simultaneous. Exactly one seat decides at a time" (design.md:380-383); `decide` is one call per acting seat per turn (llm.nim:548-552, server.nim:353-354). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed in `ae4b86e`: harness + TSV + CI gate, constants retuned 0.40/0.55 → 0.15/0.35 | harness sweeps the full 110-cell lattice round-robin (not two points); TSV committed, `<-- SHIPPED` at rank 8 tied with argmax, old pair rank 80 @ 0.49236; CI step green at head with "shipped IS the optimum"; llm.nim constants = 0.15/0.35; mirrors (manifest rules text, calibrator prompt 15%/35%) updated | yes |
| F2 | fixed by errata, no code change; second errata entry self-flagged | design.md ends with both dated errata entries; coordinator's brief sanctions the errata; tree untouched | yes |
| F3 | fixed in `93648eb`: iterator + counting test, ceiling reached | `raiseCandidates` iterator is what the baseline iterates (llm.nim:230); test counts per-state, asserts `widest == ceiling` (18 dice / 30 poker) and `counted > 0`; green both modes | yes |
| F4 | fixed in `4315919`: assert_cap in the build hook | `build_renderer_fixture.sh:21-45` reads sim.nim, checks both JS files, exits 1 with the offender named; head log shows both `agrees` lines; hook still 100755 | yes |
| "no test loosened" | claimed | `git log -p --since=run-start -- tests/`: purely additive hunks in 8e74a85 and 93648eb; ae4b86e touched no test | yes |
| CI ids | run 33017451131 all green | `gh run list`/`gh run view`: headSha `43159194…`, conclusion success, all steps success (job ids differ from the fixer's — attempt-scoped ids — but the run id and conclusions match) | yes |

## Non-blocking observations

- `src/liars_dice_player.nim:20-31` `DefaultPrompt` still advises "Challenge when you judge the
  standing bid is under 40% likely" — the pre-retune heuristic. It is LLM strategy guidance, not
  a mirror of the constants (same rationale the fixer applied to the needler prompt), so it
  violates nothing; a later pass may want it aligned with the tuned 15%/35% line for coherence.
- The committed 24-seed × 2-mode sweep table is generated offline; CI regenerates only the
  8-seed dice slice (fixer's own NOTED list). The gate still re-searches the whole lattice on
  every push, so the constants cannot drift silently; regenerating the full table in CI would be
  the stronger claim if the runtime budget allows.
- `tests/test_replay.nim` still asserts only the last wasm-path state against the live sim; the
  frame-by-frame assertion lives in `tests/test_sim.nim:522-568` against `replayMatch` directly.
  Since `buildReplayPayload` calls the same `replayMatch` (liars_dice_replay.nim:43), item 2 is
  covered; noted only so nobody mistakes the replay suite for the frame-by-frame gate.

BLOCKING: 0
