# r1 fixes — atari-cabinet

Repo: `Metta-AI/cogame-atari-cabinet`, branch `main`.
Reviewed sha: `ac7eca8acfc2eadf316c5eb6eda9f84881a76fcf` → **final sha `405fa22891754177ee0482a8128ca77ce2bbcb0d`** (11 fix commits, one per finding).
CI: `ci.yml` on `main` at `405fa22` — run **32992534403** (`workflow_dispatch`) **success**, run **32992828625** (`push`) **success**, jobs `test` / `docker-smoke` / `wasm-viewer` all `success`. A third confirming dispatch at the same sha is cited at the end of this file.

Both blocking findings (r1-1, r1-2) are fixed. Nine advisory findings are fixed. Thirteen are recorded below with the reason they were left alone; none of them falsifies an acceptance-checklist item.

## Disposition table

| finding | category | disposition | commit | files | checklist item |
|---|---|---|---|---|---|
| r1-1 | legibility (**BLOCKING**) | fixed | `5620442` | `src/cabinet/global.nim:63-80,661-670`, `client/replay_broadcast.html:4175-4196,4391`, `tests/test_render_text.nim`, `tests/test_viewer.nim` | 15 (bullets 2 & 3) |
| r1-2 | legibility (**BLOCKING**) | fixed | `52104a2` | `tools/ci/renderer_fixture.html`, `tools/ci/worst_case_frame.nim`, `tools/ci/gen_render_fixture.nim`, `tests/test_render_text.nim`, `.github/workflows/ci.yml:152-175,239-243,313-319,360-380`, `src/cabinet/global.nim:56-61`, `tests/test_viewer.nim` | 15 (bullets 1 & 4) |
| r1-3 | timeout | fixed | `edaedfd` | `src/cabinet/decide.nim:345-355,416-434,497-500`, `tests/test_engine.nim` | 5 |
| r1-5 | correctness | fixed | `971134c` | `src/cabinet/sim.nim`, `src/cabinet/broadcast.nim:20-121`, `src/cabinet/sim_types.nim`, `client/replay_broadcast.html`, `tests/test_physics.nim` | — (design-note fidelity) |
| r1-7 | correctness | fixed | `37ebd6c` | `src/cabinet/control.nim:30-100,340-361`, `tests/test_control.nim`, `tests/data/golden_hashes.json` | — |
| r1-9 | correctness | fixed | `96dafca` | `src/cabinet/decide.nim:292-341`, `tests/test_engine.nim` | 8 |
| r1-14 | static-viewer | fixed | `d6a0e09` | `.github/workflows/ci.yml:350-364`, `tests/test_viewer.nim` | 13 |
| r1-15 | other | fixed | `0cf5ce8` | `.github/workflows/coworld-release.yml:176-190`, `tests/test_manifest.nim:237-248` | 12 |
| r1-18 | legibility | fixed | `2368858` | `client/replay_broadcast.html:4124-4134`, `tests/test_viewer.nim` | 14(b) |
| r1-19 | static-viewer | fixed | `f85ce99` | `client/replay_broadcast.html` (−98/+24), `tests/test_viewer.nim` | 14 (4th bullet) |
| r1-23 | other | fixed | `405fa22` | `src/cabinet/server.nim:518-525`, `src/cabinet/sim_state.nim:106-114`, `tests/test_server.nim` | 5 (indirect) |
| r1-4 | correctness | not fixed — needs a rule change | — | `src/cabinet/sim.nim:26,192-208,559` | — |
| r1-6 | correctness | not fixed — the note contradicts itself | — | `src/cabinet/control.nim:277-296` | — |
| r1-8 | correctness | not fixed — deliberate, documented | — | `src/cabinet/control.nim:300-331` | — |
| r1-10 | correctness | not fixed — documented additions | — | `src/cabinet/sim.nim:406-413,469-500` | — |
| r1-11 | correctness | not fixed — needs a hash/rule change | — | `src/cabinet/sim.nim:763-779` | 2 (unaffected) |
| r1-12 | correctness | not fixed — needs a new `endRule` value | — | `src/cabinet/sim.nim:771-773` | — |
| r1-13 | other | not fixed — code is right, note is stale | — | `src/cabinet/global.nim:28-34` | — |
| r1-16 | correctness | not fixed — physics/tuning work, not a fix | — | `tests/test_baselines.nim` | 7 (satisfied) |
| r1-17 | timeout | not fixed — the stronger assertion would be flaky | — | `tests/test_engine.nim:113-135` | addendum (satisfied) |
| r1-20 | other | no code change — note wording, not code | — | `client/replay_broadcast.html` | 14 (satisfied) |
| r1-21 | other | no code change — reviewer agrees the code is right | — | `src/cabinet/sim_types.nim:131` | — |
| r1-22 | other | no code change — reviewer records it as an observation | — | `src/cabinet/stances.nim:62-78` | 9 (satisfied) |
| r1-24 | manifest | no code change — reviewer confirms item 6 satisfied | — | `coworld_manifest_template.json` | 6 (satisfied) |

---

## The two blocking findings

### r1-1 — full-cap remarks were ellipsized (commit `5620442`)

**Before.** The only CI gate that drew model text at full cap laid the 160-rune stance `note` out as
a single-line row and cut it with `text.slice(0, text.length - 2)` until it fit, then appended `…`.
CI reported `12 ellipsized` — four seats × three widths, every one of them a sentence — and passed,
because the gated number (`never_inside`) was 0.

**After.** The measure-and-cut loop is gone with the re-implemented fixture (r1-2), and driving the
*shipped* path at full cap located the two places the shipped viewer really was too small. Both
bands widen; no string is shortened anywhere:

- **The board's bubble band.** `global.addBoard` stepped bubble rows a hard-coded 24 px apart while
  pixie baked a 29 px line at size 22 in `data/font.ttf` — three full-cap remarks overlapped each
  other by five pixels, drawn perfectly inside the board and unreadable. The row pitch is now
  `baked.height + BubbleGapPx` — the cap measured in the drawing font, which is exactly what item
  15's second bullet asks for — and `BubbleBandLoCu` widens `92 → 89` cu so the reserved band holds
  `MaxBubbles` rows at that pitch. The band is reserved whether or not anyone is speaking (it always
  was: it is a fixed `[BubbleBandLoCu, BubbleBandHiCu]` strip, never positioned relative to a
  paddle), so the scene does not jump when a remark lands.
- **The match feed.** `.feed-row` inherits `white-space: nowrap; max-width: none` from the starter
  (sized to content so a 10-char name never truncates) and `#killfeed` is right-anchored, so a
  160-rune note grew *leftward* off the stage — 366 px of row on a 360 px board. Note rows now get
  `.feed-row.cab-note-row { white-space: normal; max-width: 100% }` (applied by `cabStances` when it
  emits the row) and `#killfeed { min-height: calc(4 * 6 * 11 * var(--u)) }` reserves the height the
  wrapped column needs at the cap, at the 0.5 hudscale floor where the column is narrowest.

**Evidence.** CI run 32992828625, job `wasm-viewer`, step *"Render the worst-case text fixture at
360 / 620 / 1280 px"*:

```
canvas text: 102 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
```

102 drawn (was 22), **0 ellipsized** (was 12), `never_inside` still 0 — and the fixture fails hard if
any string arrives shorter than its cap (`renderer_fixture.html:255-262,310-316`). In the `test`
job, `tests/test_render_text.nim` proves the same geometry without a browser: *"the bubbles sit
inside the RESERVED band, at the baked line pitch"* and *"no two baked strings overlap"*, both `[OK]`
in debug and `-d:release` (test job log, 17:22:57 and 17:23:10).

### r1-2 — CI never probed the shipped renderer (commit `52104a2`)

**Before.** The board bakes every string into a pixie sprite server-side and composites it in a
Worker, so the real-bundle smoke reported `canvas text: 0 drawn` — "not evidence of anything" in the
checklist's words — and `tools/ci/renderer_fixture.html` was a 220-line page that re-derived the
layout by hand, importing nothing from `client/`, `replay-viewer/` or `src/`. A regression in
`global.nim`'s bubble or chip placement was invisible to every gate.

**After.** The fixture is a harness over the shipped path rather than a second implementation of it:

1. `tools/ci/worst_case_frame.nim` builds a real playing `SimServer` whose four seats have each just
   returned a worst-case model reply — a full-cap 48-rune `say` and 160-rune `note`, fenced in prose,
   carrying a 4-byte emoji — through the real
   `extractJsonObject` → `parseCabinetStance` → `boundedStanceRecord` → `applyStanceRecord` path, and
   returns the Sprite v1 packet **`global.addBoard` itself** emits for that frame.
2. `tools/ci/gen_render_fixture.nim` writes those bytes out in the `test` job
   (`ci.yml` step *"Bake the worst-case text frame"*), uploads them as the `render-fixture` artifact,
   and `wasm-viewer` (now `needs: [test, docker-smoke]`) downloads them.
3. `tools/ci/renderer_fixture.html` loads the **bundle's own** `broadcast_core.js` and
   `wire_constants.js` out of `dist/static-replay-viewer/`, ingests the packet, and transcribes every
   baked string to the canvas at the rectangle the shipped board placed it at, at 360 / 620 / 1280 px.
   The 160-rune note is laid out by the **real chrome CSS**, fetched from the bundle's own
   `index.html` into the real `#stage > #chrome > #killfeed` chain, and every DOM line box is
   transcribed at its measured geometry. The page shortens nothing: it contains no ellipsis and no
   measure-and-cut loop (`tests/test_viewer.nim` asserts both), and it `fail()`s — setting
   `data-replay-error` — when a string is not at its cap, when a placement leaves the board, or when
   fewer than 12 strings are drawn.
4. `tests/test_render_text.nim` asserts the same geometry in Nim from the same bytes, so a placement
   regression is red in the `test` job too, with no browser and no Docker: every placement satisfies
   `0 ≤ x`, `0 ≤ y`, `x + w ≤ MapWidth`, `y + h ≤ MapHeight`, no two placements intersect, and the
   chrome JSON carries every seat's full-cap note.

This also settles the review's *"Could not determine"* item — whether a full-cap `say` bubble can
overflow the board's right edge past `global.nim:653`'s lower-bound-only clamp. It cannot: the
worst-case packet is measured, and `every baked string is inside the board` is `[OK]` in both build
modes.

**Evidence.** Step *"Render the worst-case text fixture at 360 / 620 / 1280 px"* in run 32992828625
prints `{"loaded":true,"ms":1024,…}` followed by the `canvas text: 102 drawn … 0 ellipsized
(--strict-text-bounds)` line quoted above; `test` job prints five `[OK]`s for `[Suite] board text`
twice (debug and release).

---

## The advisory findings that were fixed

- **r1-3 (`edaedfd`) — the per-turn budget times the calls, not the rate floor.** `turnStart` is now
  re-taken when the batch actually starts, so `turnBudgetMs = 16 000` wraps
  `attempt1Ms + retryMs = 14 000` and the 12 000 ms inter-batch floor is what it always was: a
  separate wait with its own explicit bound. The single retry is no longer available-or-not depending
  on how long the previous turn happened to take. The double-record side effect the review names is
  gone too: the pre-empt now sets the tail's cause (`budgetTimedOut → "timeout"`) instead of
  recording a second fallback, so phase 60 counts one fallback per seat per turn. New test: a turn
  whose floor (2 500 ms) exceeds its budget (2 000 ms) still makes both attempts; against the old
  code it made zero calls and recorded four timeouts. *(item 5 — every wait still explicitly
  bounded, and now the stated bound is the enforced one.)*
- **r1-5 (`971134c`) — `near_miss` is emitted.** A ball that crosses a bar's own depth plane further
  out than the bar can reach but by less than `NearMissUu` now increments `cabinets[k].nearMisses`;
  `broadcast.stepEvents` diffs that counter the way it already diffs saves and catches, and the
  chrome prints the design note's "SO CLOSE" row instead of suppressing the kind. Presentation only:
  the two new fields are never mixed into `gameHash` and never read by the resolution, and the
  committed golden hashes are unchanged. Test: a ball 0.4 cu outside the bar's end grazes it,
  concedes, is never touched, and reaches the broadcast as `{"k":"near_miss","ball":"B1"}`.
- **r1-7 (`37ebd6c`) — the far bar aims at `FarPaddleDepth`.** `predictBall` records both crossings
  (`perSide`, `perSideFar`) in one walk; foozpong's far branch reads its own line and falls back to
  the near arrival only when the far line is never crossed. The autopilot is outside the determinism
  boundary and its output is the recorded command byte, so no replay changes meaning and
  `GameVersion` does not move — but the golden fixture is a four-bulwark episode driven by this
  autopilot, so foozpong's 30 pinned hashes were regenerated with `tools/gen_golden_hashes.nim`
  (warlords and quadrapong have no far paddle and are byte-identical). New `tests/test_control.nim`
  case: over randomised foozpong states a far bar parked exactly on the near line's arrival is told
  to move.
- **r1-9 (`96dafca`) — an illegal field is repaired, not the whole stance.** Caps and numeric bounds
  clamp (which is what `parseCabinetStance` already does with an out-of-range number, and it keeps
  "post hard right" meaning that); only a *reference* with no legal interpretation — a `target_ball`
  that is not live, an `aim_at` at my own cabinet or at one that is out — takes bulwark's value for
  that field alone. A final re-validation keeps the old wholesale substitution as a backstop if the
  enumeration ever drifts from `validateStance`. *(item 8: the fallback path stays recorded and
  legal; it no longer throws away four legal decisions to fix one.)*
- **r1-14 (`d6a0e09`) — the viewer smoke soaks.** `--soak 12` added to the real-bundle step, so the
  `frozen: playback stopped advancing` path is live. Log now prints
  `soak: 12s of playback kept advancing ("4 / 1488" -> "926 / 1488" -> "974 / 1488")`. This also
  settles the review's *"Could not determine"* item on whether `wasm-viewer` would catch a frozen
  replay. `tests/test_viewer.nim` asserts both smoke steps carry the flags the note names. *(item 13.)*
- **r1-15 (`0cf5ce8`) — certify gets `--timeout-seconds 300`.** Added to the certify invocation in
  `coworld-release.yml`, and `tests/test_manifest.nim` no longer matches the bare flag anywhere in the
  file (which `upload-coworld` satisfied vacuously): it locates
  `coworld certify dist/coworld_manifest.json` and requires `--timeout-seconds 300` inside *that*
  step. *(item 12.)*
- **r1-18 (`2368858`) — `#cab-legend` uses the `0px` fallback.** `bottom: calc(var(--band, 0px) + 6 *
  var(--u))`. `tests/test_viewer.nim` now walks every `var(--band` occurrence in the page and requires
  the fallback form, so the next overlay cannot reintroduce it. *(item 14(b).)*
- **r1-19 (`f85ce99`) — the zoom wiring is removed, not hidden.** Removed: the `z`/`x` keys, the
  ctrl+wheel handler, the three Safari gesture handlers, the pinch's zoom/pan calls (the gesture is
  still swallowed so a pinch cannot select a cabinet) and the whole dead
  `if (zoomSlider && minimapBox && …)` block, which is where `core.attachMinimap`, both button zooms,
  the slider's `setZoom` and the minimap `panTo` lived. `core.resetView()` on `0`/double-click stays —
  a no-op on a fitted board. `broadcast_core.js` is untouched: it still carries zoom, pan and minimap
  verbatim, and nothing drives them. `tests/test_viewer.nim` asserts the page contains no
  `core.zoomAt(`, `core.setZoom(` or `core.attachMinimap(` at all. *(item 14, fourth bullet.)*
- **r1-23 (`405fa22`) — the no-show report is tested, and it turned out never to fire.** Writing the
  first of the four named-but-untested assertions showed `declarePlayerFailure` was unreachable:
  `sim.step` increments `lobbyTicks` and force-starts inside one tick, while the server polls
  `lobbyJoinTimedOut()` once per frame, so the poll saw `budget − 1` and then a phase that had already
  moved on. `sim_state.lobbyBudgetSpent` is the same fact without the phase clause, and the server's
  check uses it; the rest of the path (report the lowest missing slot only, then force-start so the
  empty cabinet plays bulwark) is unchanged. `tests/test_server.nim` runs a second real server with
  `COGAME_PLAYER_FAILURE_URI` set and asserts the file lands with `failed_policy_index == 0`, the
  episode still reaches a normal ending with four scores and a replay on disk, and — §Tests 11's other
  missing assertion — `/healthz` and `/global` keep answering every second for 15 s **after** the
  artifacts are written.

## The advisory findings that were left alone, and why

- **r1-4 — the `+7` second-ball serve offset is never applied.** Applying it is a *rule* change: it
  moves serve directions, so `GameVersion` must be bumped and `tests/data/golden_hashes.json`
  regenerated (`AGENTS.md` § GameVersion), and it shifts every baseline statistic
  `tests/test_baselines.nim` pins. That is a design decision (either apply the offset and re-pin, or
  delete `SecondBallDirOffset` as dead), not a smallest-correct-fix, and this sandbox has no Nim
  toolchain to regenerate the golden fixture with. **NEEDS-DESIGN.** Consequence stands as recorded:
  two same-tick serves can draw adjacent directions; deterministic and hash-stable either way.
- **r1-6 — `chase` picks `j = ±6` instead of running the 13-index search.** The review itself records
  that the note's two halves disagree (§autopilot step 3 vs §Decisions' stance glossary) and that the
  code follows the glossary, with the reason in the code's own comment at `control.nim:283-287`. There
  is no single correct target to fix towards. **NEEDS-DESIGN** (decide which half of the note is
  authoritative; the code is self-consistent and tested either way).
- **r1-8 — the "shadow vs committed" mode the note does not describe.** Deliberate and documented at
  `control.nim:303-308`: it is what makes `lead_ticks 0` (spinner) arrive late, which is the whole
  point of the spinner baseline and is what `tools/ci/baseline_tuning.json` was swept against.
  Removing it would change the baselines and the golden hashes to make the code match a note sentence
  that describes the same behaviour less completely. Left as a note-vs-code deviation.
- **r1-10 — `releaseIndex` and `containBall`.** Both are documented in the code with their reason
  (`sim.nim:470-476`), deterministic, identical on both builds, and the review states the invariant
  guard at `:704-707` still fires for a genuinely out-of-arena centre. Removing either would break
  the corner-remainder case they exist for. Documentation gap in the note, not a defect.
- **r1-11 — guard before the end checks, hash after them.** Changing the order changes what the final
  tick's `gameHash` mixes, i.e. every pinned hash, and needs a `GameVersion` bump and a golden
  regeneration (no Nim toolchain here). The review confirms server and viewer call `gameHash` at the
  same point, so **checklist item 2 (frame-by-frame re-derivation) is unaffected** — this is a
  note-ordering discrepancy with no behavioural consequence. **NEEDS-DESIGN.**
- **r1-12 — `last_standing` also fires when zero cabinets are alive.** Fixing it properly needs either
  a new `endRule` value for the mutual-destruction case (which is threaded through
  `results_schema`'s enum in the manifest, `roster.resultsKeys()`, the endcard copy and the manifest
  test) or a rule change that orders simultaneous eliminations (golden regeneration again). Both are
  design changes; the current behaviour still produces a total placement order and a well-formed
  `results`. **NEEDS-DESIGN.**
- **r1-13 — `RenderScale` is 1, not 2.** The code is deliberate and carries its reason at
  `global.nim:29-32`; the review confirms the wasm budget preflight passes either way
  (`tests/test_viewer.nim:190-196`). The mismatch is in the design note, which I am not permitted to
  edit. No code change: raising it to 2 would quadruple the bake for sharpness the note only asserts
  in passing.
- **r1-16 — the baseline pins are weaker than §Tests 5.** Strengthening them to the note's numbers
  ("at least one elimination on most seeds", "bulwark in placement 1 on 15/20") requires the shipped
  physics to eliminate cabinets more often, i.e. re-tuning or a rule change — not a test edit, and
  emphatically not a test loosening in the other direction. The review confirms **checklist item 7 is
  satisfied** (full-episode legality test with `results.reason == "complete"`, grid-tuned parameters)
  and that `git diff --stat c11a369 ac7eca8 -- tests/` is empty, so nothing was loosened.
  **NEEDS-DESIGN** for a later round.
- **r1-17 — the parallel-batch test asserts structure, not overlapping windows.** Asserting window
  intersection would be flaky on purpose-built grounds the test already documents at
  `test_engine.nim:119-122`: the fake provider is a loopback HTTP/1.1 stub and libcurl may serialise
  four plaintext connections to it even though the batch is genuinely one `makeRequests` call. Adding
  an intersection check would buy no coverage and could turn CI red at random — exactly what the
  "do not weaken a test to make it pass" rule exists to prevent, in reverse. The checklist addendum is
  satisfied by `decide.nim:319-337,431-432` (one `RequestBatch`, one `curly.makeRequests`, no per-seat
  loop) plus the structural assertion.
- **r1-20 — the region above the banner *is* edited.** The review's own analysis shows every edit is
  either a removal the note lists or a `PB_MODE → CAB_MODE` retarget plus null guards, and that
  **checklist item 14 is satisfied** (4 454 lines vs the starter's 4 660, `chrome_common.js`
  byte-identical, `broadcast_core.js` one line). Nothing to fix; the note's "nothing above them is
  rewritten" is the inaccurate half.
- **r1-21 — `darkbg.png` vs `darkbg.aseprite`.** The review states outright that the code is right and
  the note is wrong. No code change. I am not permitted to edit the design note.
- **r1-22 — `sanitizeSay` strips non-ASCII.** Recorded by the reviewer as an observation, matching the
  note's §Reply schema, with **checklist item 9 satisfied** (`tests/test_stances.nim:94-119`). The
  `note` path — which is not ASCII-filtered and is therefore the real UTF-8 risk — is exactly what
  `tests/test_replay.nim:99-157` and now `tests/test_render_text.nim` exercise at full cap with a
  4-byte emoji. No change.
- **r1-24 — `num_agents` inside `variants[].game_config`.** The reviewer verified every clause of
  **checklist item 6** against the shipped smoke, including `grep -c 'SEAT-COUNT FAIL'` returning 0.
  Moving the key would break the manifest schema the platform validates. No change. Re-verified at the
  final sha: `grep -c "SEAT-COUNT FAIL"` over the `docker-smoke` job log of run 32992828625 is **0**,
  and the job prints `smoke OK: seats=4 results=552B replay=41416B reason=complete`.

## DISPUTED

None. Every finding in the review reproduced at the cited `file:line`.

## NOTED (not fixed, not a finding in this review)

- `GameVersion` stays `"1"` across these commits. r1-7 changes the autopilot, which sits outside the
  determinism boundary and whose output is the recorded command byte, so previously recorded replays
  still re-derive bit-for-bit; r1-5 adds only unhashed presentation counters. The golden fixture was
  regenerated for foozpong because it is an autopilot-driven episode. Worth a second opinion from the
  judge on whether `AGENTS.md`'s "bump on any rule change" should have been read more literally here.
- `tests/test_server.nim`'s new grace-period case adds ~15 s of wall clock to the `test` job (twice,
  debug and release). The job is well inside its 45-minute timeout, but it is the slowest test in the
  file now.

## Verification of item 1 (CI green, no test loosened)

`git diff ac7eca8..405fa22 -- tests/` is +464 / −43 across eight files. Every deletion is a
replacement by something stronger, not a loosening:

- `tests/data/golden_hashes.json` — 30 foozpong hashes regenerated for r1-7 (the rule the autopilot
  applies changed); warlords and quadrapong byte-identical.
- `tests/test_manifest.nim` — the vacuous `"--timeout-seconds" in <whole file>` check replaced by one
  that reads the certify invocation itself (r1-15).
- `tests/test_viewer.nim` — the fixture test that asserted re-typed literals
  (`"BUBBLE_BAND_LO_CU = 92" in fixture`) replaced by assertions that the fixture loads the bundle's
  own `broadcast_core.js`/`wire_constants.js`, ingests `board_packet.bin`, fetches the real chrome CSS,
  and contains **no** ellipsis and no measure-and-cut loop; plus new tests for the `--band` fallback,
  the absent zoom wiring, `--soak 12`, and the wrapping note band.
- `tests/test_server.nim`, `tests/test_engine.nim`, `tests/test_control.nim`, `tests/test_physics.nim`,
  `tests/test_render_text.nim` — additions only.

No `skip`, no `xfail`, no widened tolerance, no removed test file.

---

**Final main sha:** `405fa22891754177ee0482a8128ca77ce2bbcb0d`
**Green `ci.yml` runs at that sha:** **32992534403** (`workflow_dispatch`, `success`), **32992828625**
(`push`, `success`) — jobs `test`, `docker-smoke`, `wasm-viewer` all `success` in both.
**Confirming re-dispatch (run by this fixer, at the final sha):** run **33001674720**
(`workflow_dispatch`, `main`, headSha `405fa22…`) — conclusion **success**, jobs `test`,
`docker-smoke`, `wasm-viewer` all `success`. Its `wasm-viewer` log reproduces both gates:

```
soak: 12s of playback kept advancing ("0 / 1488" -> "922 / 1488" -> "970 / 1488")
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)     # the shipped bundle: it composites in a Worker
canvas text: 102 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)   # the worst-case fixture over the shipped text path
```

URL: https://github.com/Metta-AI/cogame-atari-cabinet/actions/runs/33001674720
