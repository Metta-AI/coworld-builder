# r1 fixes — board-gauntlet

Repo: `Metta-AI/cogame-board-gauntlet`, worked in `/workspace/fix-board-gauntlet`
Base: `ad8054c3207ee0ff3c5ff5ec90185a57215d3f82` (CI green, run `33035395418`)
Head: `2390463b97d0bf07e93c95726a51873498404930`
CI: https://github.com/Metta-AI/cogame-board-gauntlet/actions/runs/33038495877 — **success**
(`ci.yml` on `main`, event `push`, head sha matches; jobs `test` ✓, `docker-smoke` ✓,
`wasm-viewer` ✓. No test file was touched this round: `git diff ad8054c3..HEAD -- tests/` is
empty.)

Every finding in `r1-review.md` is below: 2 blocking, 20 advisory, 4 could-not-determine.
Commit shas are the **remote** (API-mirrored) shas — one commit per finding, pushed one at a
time, in the order listed under "Commit order".

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `bde1d823` | `client/renderer.js:123-164,468-572` |
| B2 | fixed (note) | `0ab2f09b` | `docs/plans/…-design.md:929-941`, `client/chrome_common.js:19` |
| N1 | fixed | `bdd98253` | `tools/ci/renderer_fixture.html:82-110` |
| N2 | fixed (note) | `7c2962dd` | `docs/plans/…-design.md` §baselines, test-list item 15 |
| N3 | fixed (note) | `a135b9ed` | `docs/plans/…-design.md` test-list item 18 |
| N4 | fixed (note) | `f77adc19` | `docs/plans/…-design.md` §Chrome provenance |
| N5 | fixed (note) | `5cf2b9c0` | `docs/plans/…-design.md` §Readouts, §truncation |
| N6 | fixed (note) | `2e46827e` | `docs/plans/…-design.md` test-list item 28 |
| N7 | fixed (note) | `16eb147c` | `docs/plans/…-design.md` §Chrome provenance |
| N8 | fixed (note) | `098bd9f7` | `docs/plans/…-design.md` §cert path, §workflows |
| N9 | fixed (note) | `cd72c21a` | `docs/plans/…-design.md` §Art |
| N10 | fixed (note) | `cfb23a8e` | `docs/plans/…-design.md` §Chrome provenance |
| N11 | fixed (note) | `5f1d24f3` | `docs/plans/…-design.md` §inherited pages |
| N12 | fixed (note) | `c1bae927` | `docs/plans/…-design.md` §Reply schema |
| N13 | fixed | `5803396f` | `src/gauntlet/server.nim:273-283`, note ×2 |
| N14 | fixed (note) | `6b8b1940` | `docs/plans/…-design.md` §config knobs |
| N15 | fixed | `9badd91b` | `src/gauntlet/server.nim:329-331,484-485` |
| N16 | fixed (note) | `f669d235` | `docs/plans/…-design.md` §Readouts feed |
| N17 | fixed | `cf4505a9` | `client/renderer.js:645-652` |
| N18 | fixed | `e60ab80a` | `client/renderer.js:858-905` |
| N19 | no change — refuted | — | `src/gauntlet/server.nim:499` |
| N20 | fixed (note) | `2390463b` | `docs/plans/…-design.md` §baselines |
| CND-1 | resolved by B1 | `bde1d823` | — |
| CND-2/3/4 | no change — noted | — | — |

"fixed (note)" = the code was right and the design note was stale; the **in-repo** copy
`docs/plans/2026-08-27-board-gauntlet-design.md` was amended. See §Design-note edits to mirror
at the end — the coordinator must copy them into `runs/2026-08-27-board-gauntlet/design.md`,
which I did not touch.

---

## B1 — the say band ellipsized a full-cap remark (checklist 15, legibility)

**What the code did.** `layoutOf` reserved the band vertically at two lines
(`lineH * 2 + 12·scale`) and `drawSayBand` took the whole canvas as its horizontal budget
(`width = layout.w - pad*2`, `client/renderer.js:480`), then cut the assembled line to fit with
`C.ellipsize` (`:494`). A seat line is `clampName(name) + ": “" + say(80) + "”"` ≈ 92 runes, so
at every width in the fixture the sentence was truncated with `…` — 7106 ellipsized canvas draws
in run `33035395418`, all twelve samples remarks.

**What it does now.** The band is measured from the cap and the text **wraps**:

- `layoutOf(ctx, w, h, state)` now takes the 2d context. It computes the band's own pad and
  width, the render font (`sayFontOf(lineH)`), and `sayRowsOf(ctx, font, width, state)` — the
  number of wrapped rows a worst-case ruler needs (a 24-rune clamped name + `MAX_SAY_LEN`
  full-width runes + the quotes), never fewer than what either seat's current text needs. The
  band is `sayRows * 2 seats * lineH + 12·scale`, reserved whether or not anyone is speaking, so
  the board never reflows when a remark lands.
- `drawSayBand` wraps each seat's line over its reserved rows with `wrapRunes` — greedy, breaking
  at a space when there is one and between runes when there is not (CJK has none), dropping
  nothing — and no longer calls `C.ellipsize` at all. `client/renderer.js` no longer references
  `C.ellipsize`; the copied chrome still exports it for the DOM label paths.
- Wrapping is memoised on `font|width|text` (`wrapLines`), so the rAF loop does not re-measure
  ~90 runes per seat per frame.

**Evidence.** Reproduced and verified locally with the CI recipe — the fixture served out of a
bundle-shaped directory, `node tools/ci/viewer_smoke.mjs --url … --soak 16 --strict-text-bounds`,
Playwright chromium:

| | total drawn | never_inside | outside | ellipsized |
|---|---|---|---|---|
| `ad8054c` (before) | 49493 | 0 | 0 | **5718** |
| after B1 | 58854 | 0 | 0 | **0** |
| after B1+N18 (head) | 10451 | 0 | 0 | **0** |

(the drop in *total* at head is N18 — one draw loop instead of ~13 stacked ones.) The 360 px
screenshot shows both seats' full 80-rune remarks laid out over 3 and 2 lines inside the band,
nothing clipped. In CI, run `33038495877`, `wasm-viewer`:
*"Renderer fixture at 360 / 640 / 1280 px"* →
`canvas text: 10492 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`, and the bundle step *"Load the bundle in a real browser"* →
`5592 drawn, 0 never inside …, 0 ellipsized`. Was `7106 ellipsized` at `ad8054c3`.
Checklist item satisfied: **15** (third bullet: widen the band, do not shorten the text; and
second bullet: reserved band sized from the cap, measured in the render font).

## B2 — a seventh chrome edit the design note did not record (checklist 14, static-viewer)

The edit at `client/chrome_common.js:263-269` is real, named in place, six lines, asserted by
`tools/ci/chrome_scope_check.mjs:126-131` (which requires markers 1–7), and required by the
note's own §Readouts (`the verdict (SPROCKET WINS / DRAWN)`) — the ladder is two seats and zero
sum, so babel's "LEADS THE TABLE" / "ALL LEVEL" is wrong, and the endcard title counts plies
because `results` carries plies. What was missing was the register entry, which is exactly what
item 14 admits a chrome edit on ("a named, minimal patch **recorded in the design note**").

So the note is what changed: the in-repo copy's chrome-provenance table gains **row 7 (starter
lines 994–999)** and its count goes "exactly six" → "exactly seven"; the same count in the file
header (`client/chrome_common.js:19`) follows. No copied byte and no behaviour changed —
`chrome_scope_check.mjs` is green before and after (`{"ok":true,…,"copied_regions":10}`).
Checklist item satisfied: **14**.

---

## Advisories

### N1 — the fixture now asserts its own remarks are full-length — `bdd98253`
`tools/ci/renderer_fixture.html` builds its 80-rune strings by construction and nothing checked
the result. It now asserts, before it draws, that each `SAYS` entry is exactly `MaxSayLen = 80`
runes; a mismatch sets `data-replay-error` and throws.
Negative test (a copy with the pad loop cut to 40 runes):
`VIEWER SMOKE FAILED: data-replay-error: fixture say for seat 0 is 42 runes, not the full cap of 80`.
Unmodified, the step passes. Checklist item **15**, last bullet — previously unmet literally.

### N2 — Connect Four diversity floor 25 % — `7c2962dd` (note)
The code is right and the test is not loosened (`git log -p -- tests/` shows `>= 0.25` in the
original hunk of `cee5659`, never touched since). The measured rate for Connect Four is 28–30 %
however the ply population is drawn, so raising the threshold would pin a flake. The note now
records the exception (both where it states the rule and in test-list item 15). No test changed.

### N3 — `complete/no-moves` is not run through `replayMatch` — `a135b9ed` (note)
It cannot be: `replayMatch` re-runs `initSim(config)` from the standard opening and the ending is
unreachable from it, so there is no event list that reaches it; the test covers it from a
hand-built position on two copies of the sim. The note now records the exception, what the
substitute asserts, and that the path itself is re-derivable (`advance` emits the `win`;
`replayMatch`'s `evWin` branch checks seat/how/path). Item **2** was already satisfied by the
other eight endings and their `checkReDerives`.

### N4 — two unlisted copied regions — `f77adc19` (note)
`COLORS` (starter line 23) and `seatColor` (85–87) are byte-identical copies needed by the copied
`renderFeed`/`updateEndscreen`; `chrome_scope_check.mjs` already asserted all ten regions. The
note's list now names them. Item **14**.

### N5 — the `say` is drawn on the canvas, not in the scorebug plate — `5cf2b9c0` (note)
The canvas is the right place: `viewer_smoke.mjs` instruments canvas text, so a DOM remark would
be invisible to `--strict-text-bounds` and to the fixture — the gate that caught B1. §Readouts
now has its own "Say band" bullet describing the shipped band (both seats, height from the cap,
wrapped never ellipsized, on the canvas and why), and §truncation drops "on one line".

### N6 — the fixture is the main frame, not an iframe — `2e46827e` (note)
`viewer_smoke.mjs` reads its tally with `page.evaluate()`, which only runs in the main frame, so
an iframe fixture would report zero canvas text. The fixture does load the **shipped** code (it
is copied into `dist/static-replay-viewer/` first, so every relative path resolves to the
artifact) and retypes only the markup. Test-list item 28 now says that, and records N1's
assertion. Item **15** ("a page that loads the real `client/renderer.js`") holds either way.

### N7 — narrow-viewport rules written twice — `16eb147c` (note)
Both copies are below the game-block banner, so `head -443 client/chrome.css` is still
byte-identical to babel's. The duplication exists because a page cannot resize its own viewport;
without the `body.narrow-*` copy the narrow rules would ship untested. The note now records it
and that the two copies must be edited together. Items **11** and **14** hold.

### N8 — no `--timeout-seconds 300` on certify — `098bd9f7` (note)
The note claimed a flag the shared template never had:
`diff` of `templates/coworld-release.yml` (substituted) against the repo's copy is empty, and the
template's certify step carries only `--no-open-report`. Adding it would diverge the workflow
from the scaffold that item **12** rests on, so the **note** changed: the 60 s certify default is
the budget, and the under-50 s scripted-fixture test is what keeps the cert path inside it.

### N9 — the seat avatars are generated, not copied — `cd72c21a` (note)
`data/soldier_{red,blue}_front.png` are 192×192 and are produced by
`scripts/art/generate_cog_sheet.py` + `split_cog_sheet.py` from
`scripts/art/source/cog_seats_sheet.png`, so each cog holds this ladder's own pieces instead of
babel's spellcasting props. Deliberate art, kept; §Art now credits the scripts.
`arena_floor.png`, `font.ttf` and `FONT_LICENSE.txt` remain byte-identical copies.

### N10 — three appended helpers unlisted — `cfb23a8e` (note)
`setBeatNames`, `beatSeatName`, `beatLabel` are appended below the additions banner and are what
give a beat button its `aria-label`/`title`. The note's appended-list now names them.

### N11 — a fourth change to the inherited pages — `5f1d24f3` (note)
`<div id="clock">ROUND 0</div>` → `PLY 0` on all three pages (and the `BabelRenderer` →
`GauntletRenderer` bootstrap rename). Nothing is removed; the element and its id survive. The
note's "Changed:" list now names both.

### N12 — Connect Four normalisation is a token rule — `c1bae927` (note)
The note's literal "first character" wording contradicted its own `"column d — centre"` → `d`
example; the code implements the example (first standalone one-character file token, falling back
to the first character), and `tests/test_sim.nim:494-497` pins both readings. The note now states
the token rule.

### N13 — the play-deadline guard could be overshot — `5803396f` (code + note)
The guard refused to open a ply unless `now + 2·llmTimeout + 2 ≤ playDeadline`, but the spacing
sleep (≤ 4 s), the decide call and `turnDelayMs` (0.25 s) all run **after** it, so the worst-case
settle landed ≈ `playDeadline + 2.25 s` — 722 s of the 720 s play budget item **5** names.
`worstPlySeconds` now includes the spacing floor and the turn delay
(`2·30 + 2 + 4 + 0.25 = 66.25 s` with the shipped defaults), so the last ply the loop opens
cannot outrun the budget. No wait changed; the episode simply settles on the position one ply
earlier in the pathological case. The note's two statements of the arithmetic (resolution-order
step 2 and the budget table's paragraph) were updated in the same commit.

### N14 — `output_config: {"effort": "low"}` — `6b8b1940` (note)
Guarded off for Haiku and `4-5` tiers (which 400 on it) and never sent on Bedrock. The note's
config-knob paragraph now records it and the guard.

### N15 — two untruncated error strings in the log — `9badd91b` (code)
The note's rule covers "any error text that reaches an event **or the log** (200)". The two
`echo` sites (`server.nim:329` move-rejected, `:484` bad player frame) now use
`cleanText(error.msg, MaxErrorLen)`, the same call the file already makes at `:464`. Nothing that
reaches an event changed — those were already capped, so item **9** was satisfied before and
after.

### N16 — the `no-moves` feed line — `f669d235` (note)
The event's seat is the victor (`sim.nim:300`) and every other `win` line is phrased about the
seat it names, so the code's `"<name> wins: the opponent has no legal move"` is the factually
right phrasing. The note now matches.

### N17 — the clock's size word was gated on `window.innerWidth` — `cf4505a9` (code)
A page cannot resize its own viewport, so the fixture narrows `#layout`/`body` and
`window.innerWidth` stayed at the browser width: the note's "the clock drops the size word at
360 px" was in the code but exercised by no gate (and wrong for any embed that narrows the stage
rather than the window). `headerText` now measures `document.body.clientWidth`.
Evidence, headless chromium over the fixture's own cycle:
`360 :: "GAUNTLET → HEX · PLY 2 / 80 · …"` (no size word),
`640 / 1280 :: "GAUNTLET → HEX 7×7 · PLY 2 / 80 · …"`. Item **11**/**15** legibility.

### N18 — stacked `attachReplay` drivers — `e60ab80a` (code)
`attachReplay` started a self-scheduling rAF loop and never stopped it, so the fixture (which
re-attaches every 1200 ms) accumulated ~13 concurrent loops on one canvas and inflated the
fixture's tallies; two live drivers on one canvas is also wrong for a host that re-attaches. Each
call now takes a generation; a stale loop returns instead of rescheduling, and a `makeRenderer`
callback that lands after a later attach does not build a second scrub. Same fixture run: 57223
canvas draws → 10451, with `never_inside` 0 and `ellipsized` 0 in both. The fixture's numbers are
now a per-frame figure, which is what makes B1's evidence readable.

### N19 — `/client/replay` route — **no change, refuted**
Item **3**'s phrase is about a *pod path serving hosted replays*, and this route is not that:

- it is inherited verbatim — `/workspace/starters/cogame-babel/src/babel/server.nim:502` has the
  identical line, and item 14 forbids rewriting the inherited pages rather than serving them;
- the manifest declares the static bundle and nothing else:
  `coworld_manifest_template.json:18-20` `"replay_viewer": {"bundle": "static-replay-viewer"}`
  inside `game`, and the global protocol text ends "hosted replays are served by the STATIC wasm
  bundle (index.html?replay=<url>), **never by a pod**";
- `.github/workflows/coworld-release.yml:198-207` hard-fails if certification does not report the
  static bundle;
- the design note declares the route (`§Server, player, protocol`; §Chrome provenance "Served at
  `/client/replay`") — it is the *live* broadcast page a spectator opens while the episode is
  running, not a replay source.

Removing it would delete the live broadcast page and diverge the inherited server from the
starter, to satisfy a text match rather than the item. Left alone deliberately.

### N20 — no grid harness — `2390463b` (note)
There is nothing to sweep: `tacticianMove` and `hustlerMove` are pure one-ply lookahead over
`legalMoves`/`applyProbe`/`standing` with no thresholds, weights or depths, and the only numbers
in the loop are the four `standing` definitions the note fixes verbatim. The note now says so and
names the three tests that stand in for what a harness would establish (beats uniform-random,
disagrees with the other filler, never walks past a win or into a loss). Item **7**'s first
sentence was already satisfied by `tests/test_bot.nim:259-279`.

---

## Could not determine (the reviewer's four)

- **Which widths B1's ellipsized draws came from** — settled and moot: after B1 the fixture
  reports `ellipsized: 0` over a run that cycles all of 360 / 640 / 1280 px, so the count is zero
  at every width. I also measured the before-state locally at 5718 with the same aggregate
  counter; the per-width split of the *old* number was never needed once the new one is 0.
- **Whether `complete/no-moves` is genuinely unreachable from the standard Breakthrough
  opening** — not proved here; the exception is now *recorded* rather than assumed (N3), which is
  what the register needed. A long random sweep reporting an ending histogram would settle it.
- **Whether the hex 0–1 BFS deque can overrun its backing array** — not touched. The reviewer's
  reasoning (each cell front-pushed at most once, back-pushed at most once, so `head ≥ 0` and
  `tail ≤ 242`) matches mine, and the debug CI build would raise `IndexDefect` on an overrun
  across the seeded hex episodes. A bounds assertion would settle it; it is not a finding.
- **Whether `renderFeed`'s DOM say line is clipped at 360 px** — not touched. `#feed` is
  `display: none` under 360 px, so there is nothing to measure there; a DOM
  `scrollWidth > clientWidth` probe in the fixture would settle it at 640 px.

## NOTED (not fixed)

- The two narrow-viewport rule copies in `client/chrome.css` (N7) can still drift silently. A
  ~15-line assertion in `tools/ci/chrome_scope_check.mjs` that the `@media` block and the
  `body.narrow-*` block carry the same declarations would gate it. Out of scope for this round.
- `tools/ci/renderer_fixture.html` re-attaches on a 1200 ms `setTimeout` and never stops; with
  N18 that is one live loop at a time, but the page still runs forever by design (the soak needs
  it to).

## Design-note edits to mirror — for the coordinator

I amended **only** the in-repo copy `docs/plans/2026-08-27-board-gauntlet-design.md` and did not
touch `runs/2026-08-27-board-gauntlet/design.md`, which was byte-identical to it at
`ad8054c3`. To re-sync, copy the in-repo file over the run copy, or apply these edits:

| finding | section | edit |
|---|---|---|
| B2 | Chrome provenance | "Exactly six" → "Exactly seven"; new table row 7 (starter 994–999, endcard verdict + title) |
| N2 | The two scripted baselines; test-list 15 | 30 % floor gains the recorded Connect Four exception at 25 % |
| N3 | test-list 18 | records the `complete/no-moves` exception and its substitute test |
| N4 | Chrome provenance | copied-region list gains starter 23 (`COLORS`) and 85–87 (`seatColor`) |
| N5 | Readouts; Every truncation | `say` moves out of the scorebug bullet into its own "Say band" bullet (canvas, cap-sized, wrapped); "drawn on one line" → "wrapped over as many lines as the cap needs" |
| N6 | test-list 28 | iframe → top-level document, with the reason; adds the full-length assertion |
| N7 | Chrome provenance | records the duplicated `@media` / `body.narrow-*` blocks |
| N8 | Certification/smoke path; §workflows | drops the `--timeout-seconds 300` claim (the template has no such flag) |
| N9 | Art | seat avatars: "copied from babel" → generated by `scripts/art/*` at 192×192 |
| N10 | Chrome provenance | appended-list gains `setBeatNames`, `beatSeatName`, `beatLabel` |
| N11 | inherited pages | "Changed:" gains the `#clock` placeholder and the `BabelRenderer` rename |
| N12 | Reply schema | Connect Four "first character" → "first standalone one-character token" |
| N13 | resolution order step 2; wall-clock arithmetic | `worstPlySeconds` 62 → 66.25 (spacing + turn delay counted) |
| N14 | config knobs | records `output_config: {"effort": "low"}` and its guard |
| N16 | Readouts feed | `no-moves` win line phrased from the victor |
| N20 | The two scripted baselines | records that the baselines have no tunable parameters, hence no grid harness |

## Commit order (remote, one per finding)

`bde1d823` B1 → `0ab2f09b` B2 → `bdd98253` N1 → `e60ab80a` N18 → `cf4505a9` N17 →
`9badd91b` N15 → `5803396f` N13 → `7c2962dd` N2 → `a135b9ed` N3 → `f77adc19` N4 →
`cfb23a8e` N10 → `5cf2b9c0` N5 → `2e46827e` N6 → `16eb147c` N7 → `098bd9f7` N8 →
`cd72c21a` N9 → `5f1d24f3` N11 → `c1bae927` N12 → `6b8b1940` N14 → `f669d235` N16 →
`2390463b` N20
