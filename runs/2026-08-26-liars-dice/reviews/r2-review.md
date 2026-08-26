# r2 review — liars-dice

Range: `23da0888..8e74a8507cc36545686aea23a6ccdb8095a49eea` (head of `origin/main`, fetched and
checked out at review time; no commits landed after the expected sha, `git status --porcelain`
clean, `nim.cfg` is gitignored host residue per `.gitignore:6-7`)
Files read: 14 (`src/liars_dice/llm.nim`, `src/liars_dice/server.nim`, `src/liars_dice/sim.nim`
(constants + truncation), `tests/test_bot.nim`, `tests/test_sim.nim` (replay suite),
`client/renderer.js`, `client/chrome.css`, `client/fixtures/worst_case.html`,
`client/fixtures/worst_case.js`, `tools/ci/build_renderer_fixture.sh`,
`.github/workflows/ci.yml`, `liars_dice.nimble`, `README.md`, `coworld_manifest_template.json`
(grep-level), plus `/workspace/starters/cogame-babel/client/chrome.css` for the provenance diff)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 7, 15, 2, 5, 11, 14 touched
here; item 1 re-confirmed from CI)

Scope per the brief: the standing round-1 item-7 gap (baseline parameter provenance), plus a
regression re-check of every area the round-1 fixes touched. Everything below is *observed* from
the tree at the head sha or from the cited CI run unless it is explicitly labelled inferred.

---

## Blocking

### F1 — No grid/sweep harness for the scripted baselines' parameters exists anywhere in the tree; the only parameter evidence is a two-point head-to-head

- Where: `src/liars_dice/llm.nim:27-34`; `src/liars_dice/llm.nim:156-160`;
  `tests/test_bot.nim:132-151`; absence across the whole tree (evidence below).
- Observed:
  - The four numbers are plain compile-time constants with a prose label and no provenance:

    ```nim
    27  ## The calibrated baseline. Also the no-credentials fallback and the
    28  ## fallback for a rejected LLM reply, so it must always be legal.
    29  BayesChallenge = 0.40
    30  BayesSafe = 0.55
    31  ## The bluffier filler: challenges later, raises on thinner ice, and pads
    32  ## its chosen raise by one so the champions have something to catch.
    33  PressureChallenge = 0.25
    34  PressureSafe = 0.35
    ```

    They are consumed only through `baselineThresholds` (`llm.nim:156-160`) and applied at
    `llm.nim:181-182` (challenge below `chal`) and `llm.nim:208` (keep a raise only above `safe`).
  - The single test that exercises the numbers is `tests/test_bot.nim:132-151`
    (`"calibration: two bayes seats beat two pressure seats"`): four fixed seeds × 30 deals, one
    table seating `["bayes","pressure","bayes","pressure"]`, then `check bayesMean > 0.5` and
    `check pressureMean < 0.5`. That is a comparison of **exactly two parameter points**
    (0.40/0.55 vs 0.25/0.35), and the two points differ in three ways at once — `chal`, `safe`,
    and `pressure`'s `pad` flag (`llm.nim:158`, applied at `llm.nim:227-229`). Nothing varies
    `chal` or `safe` independently, and nothing compares 0.40/0.55 against a neighbouring point
    (e.g. 0.35/0.50 or 0.45/0.60), so the test cannot show the shipped values are a chosen point on
    a searched surface rather than a guess that happens to beat one looser guess.
  - Measured margin, from the head-sha CI run (job `test`, 98325857228):
    `bayes mean 0.5166666666666667 vs pressure mean 0.48333333333333334` — i.e. about +1 point per
    bayes seat per 30-deal episode. Deterministic (seeded), so the assertion is stable; it is the
    *breadth* of the evidence, not its flakiness, that is at issue.
  - No harness, no sweep, no recorded tuning output exists. Evidence:
    - `grep -rn -i 'grid|sweep|tune|tuned|tuning|harness' --exclude-dir=.git .` over the whole
      tree returns only: `ci.yml:297` (a comment about the *smoke* harness),
      `README.md:77` ("the CI harness"), `tests/test_bot.nim:111`
      (`echo "baseline sweep: ", elapsed, " ms"` — a wall-clock echo of the legality loop at
      `test_bot.nim:82-112`, not a parameter sweep), `viewer_smoke.mjs:81` (a comment), and three
      CSS `grid-template` hits. No other match.
    - `git log --all --pretty=format: --name-only | sort -u` lists 43 files ever committed on any
      ref; none is a tuning script, a sweep output, or a results table.
      `git log --all --diff-filter=D` is empty — nothing of the kind was committed and removed.
    - `liars_dice.nimble:1-12` declares no `task`, so there is no `nimble tune`/`nimble sweep`
      entry point.
    - `.github/workflows/ci.yml` defines exactly four jobs — `test:43`, `docker-smoke:156`,
      `wasm-viewer:207`, `renderer-fixture:363`. None runs a parameter search; there is no CI
      artifact carrying sweep output (the artifacts uploaded are `smoke-replay`, `viewer-smoke`,
      `renderer-fixture`, `static-replay-viewer`).
  - The design note does not close the gap either: `design.md:321-322` and `design.md:343` simply
    state the values (`bayes` "the calibrated one … with `chal = 0.40`, `safe = 0.55`";
    `pressure` "`chal = 0.25`, `safe = 0.35`"), and `design.md:829-831` asks only for "Calibration
    sanity: over 4 seeds × 30 deals … the `bayes` seats a mean score `> 0.5`" — which is exactly
    what `test_bot.nim:132-151` implements. Neither the note nor the code claims a search was run.
  - Nothing changed in this area since the round-1 review: `git diff 23da0888..HEAD --stat` touches
    eight files and neither `src/liars_dice/llm.nim` nor `tests/test_bot.nim` is among them.
- Checklist item: item 7, second sentence — "The baseline's parameters were tuned with a grid
  harness, not guessed."
- Why blocking: the item's second sentence cannot be verified from the tree or from cited CI
  evidence, and under the judge rule in `prompts/30-review-loop.md:59-61` ("A checklist item you
  cannot verify from the tree or from cited CI evidence counts as blocking") that is blocking on
  its own. Concretely: `bayes` is the no-credentials fallback (`llm.nim:11-13`, `llm.nim:144-147`),
  the fallback for a twice-rejected LLM reply (`server.nim:370-379`), the coerced baseline for a
  deadline-forced seat (`server.nim:345-349`) and a published league filler
  (`tools/ci/policies.json`), so its thresholds set the floor every champion is measured against —
  and the repo carries no record that the floor was placed by search rather than by choice.
  What would settle it: a committed harness that evaluates a grid of `(chal, safe)` points
  head-to-head over seeds and writes its table, plus that table (or a CI step that regenerates it)
  in the repo, with the shipped 0.40/0.55 identifiable as the grid's pick.

Item 7's **first** sentence is satisfied — see "Traced and consistent" below. The finding is
scoped to the second sentence only.

---

## Non-blocking

### F2 — The design note's fixed line counts for the speech plate and notes parchment are stale; the code now derives both bands from the server caps

- Where: `client/renderer.js:143-184` and `188-242` vs `design.md:675-676`, `design.md:679-680`,
  `design.md:702`.
- Observed: the note says the speech plate is "(2 lines, ellipsized…)" (design.md:675), the notes
  parchment "(3 lines, ellipsized)" (design.md:679-680), and that below 480 px "notes parchments
  drop to 1 line" (design.md:702). The code no longer has fixed line counts: `MAX_SAY_LEN = 140` /
  `MAX_NOTES_LEN = 400` (renderer.js:143-144) mirror `sim.nim:27-28`, `advance(ctx)`
  (renderer.js:165-172) measures the shipped face, `capLines(ctx, usableWidth, cap)`
  (renderer.js:176-180) converts a cap into the line count that holds it, and `seatBlock`
  (renderer.js:209-210) reserves `sayLines`/`noteLines` from those caps; the compact-mode
  `noteLines = compact ? 1 : NOTE_LINES` of the pre-fix tree is gone (visible in
  `git diff 23da0888..HEAD -- client/renderer.js`). Lines are handed back only when a frame is too
  short to hold both full bands (renderer.js:218-223).
- Checklist item: none violated. Checklist 15's second bullet *requires* the band to be "sized from
  the cap the server enforces on that string (`MaxSayLen` and its kin) and measured in the font it
  will be drawn in", and calls ellipsis on a sentence a defect — so the code is right and the note
  is what is out of date. The fixer's commit message on `e8d76ee` says the same thing explicitly.
- Note: this is a documentation-vs-code divergence, recorded so a later reader does not "restore"
  the note's numbers.

### F3 — The design's test-plan item 15 ("the raise enumeration never exceeds `3 * faces` candidates") is not asserted by any test; the bound is structural only

- Where: `design.md:826-828` (test-plan item 15) vs `src/liars_dice/llm.nim:36`, `llm.nim:198-223`,
  and `tests/test_bot.nim:53-76`.
- Observed: the enumeration ceiling is `min(sim.bidQuantity + RaiseQuantitySteps - 1, total)` with
  `RaiseQuantitySteps = 3` (llm.nim:36, llm.nim:202), so at most 3 quantities × `faces` faces are
  probed — the bound holds by construction. `test_bot.nim` asserts the *outputs* (exactly one
  action per turn, `decision.quantity` within `before .. before + 3`, `bidsThisDeal <=
  maxBidsPerDeal`, empty `say`/`notes`) but never counts candidates; there is no instrumentation
  to count them.
- Checklist item: none. Item 7 asks that "every order/action is inside its legal bounds", which
  `test_bot.nim:58-76` does assert. This is a design-note test-plan item, not a checklist item.

### F4 — The renderer's copies of the server caps are hand-mirrored literals with no build-time agreement check

- Where: `client/renderer.js:143-144` (`MAX_SAY_LEN = 140`, `MAX_NOTES_LEN = 400`, comment citing
  `sim.nim:27-28`), `client/fixtures/worst_case.js:14-15` (a second copy of the same two numbers),
  vs `src/liars_dice/sim.nim:27-28`.
- Observed: all three sites currently agree (140 / 400, verified by reading each). Nothing in
  `ci.yml` or the tests compares the JS literals against the Nim constants; raising `MaxSayLen` in
  `sim.nim` alone would silently under-reserve the band and the fixture would keep passing, since
  the fixture's own strings are built from its own copy of the cap (worst_case.js:86-92) rather
  than from the server's.
- Checklist item: none. Checklist 15 requires the band to be sized from the cap, which it is; it
  does not require the mirror to be machine-checked. Carried forward from the r1 verdict's
  non-blocking list and re-verified here at head rather than taken on report.

---

## Traced and consistent

Item 7, first sentence
- `tests/test_bot.nim:82-112` — `for baseline in ["bayes","pressure"]` × `seed in [1,7,42,1234]` ×
  `mode in [mDice,mPoker]` × `talk in [true,false]` × `seats in [3,4,6]`, each driven to the
  natural end by `playBaselines`; asserts `sim.done`, **`check sim.reason == "complete"`**
  (line 97), `dealsPlayed == 3`, one challenge per deal, and `sum(points) == 0`.
- `tests/test_bot.nim:36-79` — every emitted action is checked *before* it is applied:
  `sim.legalBid(q, f)` (60), `face` within `lowFace()..highFace()` (61-62), `1 <= quantity <=
  totalSymbols()` (63-64), the raise window `before .. before + 3` (66-68), `standing` required for
  a challenge (73), `bidsThisDeal <= maxBidsPerDeal` (76), and `applyBid`/`applyChallenge` raising
  anywhere would fail the test. Green in CI run 33013575662 in both debug and `-d:release`
  (`[OK] both baselines play legal episodes across seeds, modes, talk, seats`, twice).
- Baseline logic against `design.md:324-345`: rule 1 challenge-below-`chal` (llm.nim:180-184) is
  checked before rule 2's cap-forced challenge (llm.nim:185-188), matching the note's order; the
  opening bid is `own(f_best) + floor(unseen/faces)` clamped to `1..total`
  (llm.nim:190-197 = note line 337-339); the raise window is `q0 .. min(q0+2, total)`
  (llm.nim:202 = note line 335); tie-breaks are lower quantity → the face held most → the seeded
  RNG (llm.nim:210-219 = note lines 338-339); `pressure`'s `+1` pad is applied only when it stays
  `<= total` and still passes `legalBid` (llm.nim:227-229 = note line 343-344).

Renderer band derivation (round-1 B2 area — no regression)
- `client/renderer.js:143-144` mirror `src/liars_dice/sim.nim:27-28` (`MaxSayLen* = 140`,
  `MaxNotesLen* = 400`, both enforced through `cutRunes` at sim.nim:120-133).
- `advance()` (renderer.js:165-172) measures a capitals-and-digits reference in the current
  `ctx.font` and caches per font string; the cache is dropped on `document.fonts.ready`
  (renderer.js:160-163) so the bands are not sized off the fallback face.
- `capLines()` (renderer.js:176-180) → `seatBlock()` (renderer.js:209-210) reserves `sayLines` and
  `noteLines` from the caps at the band's real width, and the block widens into
  `Math.min(width/2 - 16, size*5.5)` (renderer.js:201-202) — the "widen the band" direction
  checklist 15 asks for.
- The bands are reserved whether or not a seat is speaking: `block.above`/`block.below`
  (renderer.js:239-240) always include `sayH`/`noteH`, so the scene does not jump when a remark
  lands. `drawSpeech` hangs the plate from the band's bottom edge (renderer.js:582-593) and
  `drawParchment` grows down from the band's top (renderer.js:612-627), both clamped inside the
  canvas.
- Over-wide tokens are broken, not ellipsized (`breakWord`, renderer.js:675-689, called from
  `wrapLines` renderer.js:695-701); `ellipsize` survives only as the last-resort cut when the
  reserved lines are exceeded (renderer.js:715-721).
- `git diff 23da0888..HEAD -- client/renderer.js` is +170/-38 and confined to these functions
  (`seatBlock`, `computeLayout`'s new `ctx` argument, `drawSeat`'s two call sites, `drawSpeech`,
  `drawParchment`, `inkWidth`, `breakWord`, `wrapLines`). No chrome machinery — drivers, scrub,
  feed, scorebug, endscreen, name map — appears in the diff.

Worst-case fixture (round-1 B1 area — no regression)
- `client/fixtures/worst_case.html:46-76` is a real chrome page (`#layout`/`#stage`/`#topband`/
  `#scorebug`/`#board-wrap`/`canvas#table`/`#endscreen`/`#transport`/`#feed`) loading the real
  `./chrome.css` (line 6), the real `./renderer.js` (line 74) and the driver (line 75).
- `client/fixtures/worst_case.js:377-389` drives the **real** `LiarsDiceRenderer.attachReplay`;
  `exact()` (lines 32-45) pads each seed to exactly 140 / 400 runes and throws rather than
  shortening; all four seats carry a full-cap `say` and full-cap `notes` on every frame
  (lines 129-131), including an unbreakable 44-character token (lines 65, 71, 76, 82).
- Seven canvas sizes down to 360×640 (lines 17-20), each sampled twice — mid-animation after four
  frames and again after a 2900 ms settle (lines 335-352).
- Per-size assertions (lines 255-286): the fixture's own strings are still exactly 140/400 runes;
  zero draws crossed a canvas edge (the `fillText`/`strokeText` hook, lines 195-233); every band's
  drawn fragments reconstruct the source string exactly (`reconstructs`, lines 244-253) — so a
  quietly ellipsized remark fails. `checkFeed` (288-305) additionally requires the full say and
  full notes to appear in `#feed`'s text.
- The renderer's own first-frame `data-replay-loaded` is intercepted and held
  (lines 181-190, 355-358); the attribute is only really set after all seven sizes pass
  (line 368), and any failure sets `data-replay-error` through the un-patched setter (line 324).
- `tools/ci/build_renderer_fixture.sh` (mode 100755, verified by `ls -l`) copies the real
  `renderer.js`, `chrome.css`, the fixture pair and the real `data/` assets including `font.ttf`
  (lines 18-25) and asserts the output is non-empty (31-32).
- `.github/workflows/ci.yml:363-419` — job `renderer-fixture`: asserts the hook is present and
  executable (378-385), assembles the fixture (387-388), pins Playwright 1.55.0 (394-399), and runs
  `node tools/ci/viewer_smoke.mjs --bundle dist/renderer-fixture --replay
  dist/renderer-fixture/fixture.json --timeout 120 --strict-text-bounds --out …` (410-415) as its
  own step, with no `continue-on-error`.
- CI evidence at the reviewed sha: run **33013575662** (`head_sha = 8e74a850…`, conclusion
  `success`); job **98325857248** `renderer-fixture` success, step 7 "Load the worst-case renderer
  fixture in a real browser" **success**, stdout
  `{"loaded":true,"ms":21463,…}` and
  `canvas text: 81665 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.

Frame-by-frame replay test (round-1 N8 area — no regression)
- `tests/test_sim.nim:522-568` snapshots `$sim.tableStateJson()` after **every** event the live sim
  logs (531-533, 549-551), replays the serialised events through `replayMatch` (552-555), then
  compares `$frames[index].tableStateJson()` with the live snapshot at that index for every
  observed index (559-565) and asserts `compared >= events.len` (567) — so the count is tight: only
  the single index between the closing `challenge` and the `end` event (never observed live,
  because both are logged inside one `applyChallenge`) may be skipped.
- The endpoint test at `tests/test_sim.nim:504-520` is unchanged and still present alongside it.
- `git diff 23da0888..HEAD --numstat -- tests/` = `48 0 tests/test_sim.nim` — purely additive, no
  deletion, no widened tolerance, no `skip`. (Item 1's "no test loosened", re-verified from the
  repo's own history rather than assumed.)

Mid-deal deadline baseline coercion (round-1 N2 area — no regression)
- `src/liars_dice/server.nim:345-349`:
  `let deadlineForced = playDeadline > 0.0 and now + callGuard > playDeadline`; if
  `deadlineForced and not state.scripted[turn.seat]` then `seatBaseline = "bayes"`; and
  `seatScripted = state.scripted[turn.seat] or deadlineForced`. That is `design.md:408`
  ("remaining decisions of that deal are `bayes` (instant) so the deal completes and the hands are
  revealed") — a seat registered `PLAYER_SCRIPTED=pressure` keeps its own baseline, an LLM seat is
  finished on the calibrated line.
- Surrounding bounds unchanged: `callGuard = 2 * llmTimeoutSeconds + 5` (server.nim:286), deal
  boundary past the deadline ⇒ `endEarly()` and break (server.nim:308-318), bid cap ⇒ forced
  challenge with no model call (server.nim:327-333), `LiarsDiceError` on apply ⇒ bayes fallback
  recorded with `fallback = true` (server.nim:370-380).

`--band` / `--hudscale` consumers (round-1 N3 area — no regression)
- Published on `:root`: `relayout()` at `client/renderer.js:1250-1261` takes
  `document.documentElement` and sets `--band` from `#transport`'s measured height (1253-1256) and
  `--hudscale = clamp(0.7, stageWidth/960, 1.4)` (1257-1260). Never on `#stage`.
- Consumed: `client/chrome.css:554-557` — `#loading { bottom: var(--band, 0px); }`,
  `#clock`, `.plate-name`, `.plate-score` font sizes `max(11px, calc(N px * var(--hudscale, 1)))`.
  `#loading`'s base rule is `position: absolute; inset: 0` (chrome.css:249-260), so the override
  lifts it off the transport band.
- Exported and called: `relayout` is on the public API (renderer.js:1588) and invoked by
  `client/replay.html:75`, `replay-viewer/index.html:54` and `bindFeedToggle`
  (renderer.js:1263-1270).

Other round-1 fixes, re-verified at head
- `.seat5 { --tc: #e08a3a; }` present at `client/chrome.css:494` with the reason recorded
  (490-493).
- `.plate-pip.hollow` declared **inside** the liars-dice block at `client/chrome.css:513-516` with
  its rationale (507-512), and removed from the inherited tail — confirmed by
  `git diff 23da0888..HEAD -- client/chrome.css` hunk 1.
- Endscreen at 360 px: `@media (max-width: 480px)` at `client/chrome.css:531-535` sets
  `.end-panel { min-width: 0; max-width: 96% }` and hides the two rate columns. Checklist 11's
  literal requirements still present: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`
  (chrome.css:506) and labels hidden under 640 px (chrome.css:521-524).

Chrome provenance (checklist 14 — unchanged by the round-1 fixes)
- `diff <(sed -n '1,430p' client/chrome.css) /workspace/starters/cogame-babel/client/chrome.css`
  reports only the starter's extra tail (starter lines 431-443: `.feed-speak`, `.feed-round`,
  `.feed-pick`, `.plate-pip.hollow`) — i.e. the repo's first 430 lines are byte-identical to the
  starter's first 430, and the only removal is exactly the babel tail block `design.md:618-620`
  names. The liars-dice banner starts at `client/chrome.css:435-437`, and **every** round-1 CSS
  hunk (`@@ -441`, `-491`, `-503`, `-511`, `-519`) is below it.

CI at the reviewed sha (checklist 1, 13, 15 evidence)
- `gh api repos/Metta-AI/cogame-liars-dice/actions/runs/33013575662` → `head_sha
  8e74a8507cc36545686aea23a6ccdb8095a49eea`, `status completed`, `conclusion success`.
- Jobs: `test` 98325857228 success, `docker-smoke` 98325856977 success, `renderer-fixture`
  98325857248 success, `wasm-viewer` 98326205123 success.
- `SEAT-COUNT FAIL` grep over the full `docker-smoke` job log: **0** occurrences.
- `test` job log shows every suite `[OK]` in both debug and release passes, including
  `[OK] calibration: two bayes seats beat two pressure seats`.

---

## Could not determine

- **Whether a grid search was actually performed off-tree.** Nothing in the coworld repo, its git
  history (43 files ever committed, no deletions), its four CI jobs, or its artifacts records one,
  and `liars_dice.nimble` defines no task that could run one. I did not read the builder run's
  narrative logs, and under the checklist the admissible evidence is the tree or cited CI anyway.
  What would settle it: a committed sweep harness plus its recorded output table (or a CI step that
  regenerates the table) showing 0.40/0.55 as the searched pick.
- **Whether the `bayes` > `pressure` margin (0.5167 vs 0.4833) would survive other seeds or seat
  counts.** The test pins four seeds at 4 seats, 30 deals. Untested: the same head-to-head at other
  seeds/seat counts. This is an observation about the breadth of the calibration evidence, not a
  claim that the assertion is flaky — it is deterministic and green in both CI passes.
- **Whether the JS caps and the Nim caps can drift undetected.** They agree today (F4); I could not
  find any mechanism that would catch a future divergence, but I did not attempt to run the fixture
  with a deliberately mismatched cap to confirm it would stay green.
