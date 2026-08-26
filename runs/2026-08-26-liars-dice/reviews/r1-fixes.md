# r1 fixes — liars-dice

Head: `8e74a8507cc36545686aea23a6ccdb8095a49eea` (main)
CI: https://github.com/Metta-AI/cogame-liars-dice/actions/runs/33013575662 — **success**
(all four jobs `success`: `test`, `docker-smoke`, `wasm-viewer`, and the new `renderer-fixture`;
`headSha` = `8e74a850…`, the head above)

Range fixed: `23da0888…` → `8e74a8507cc36545686aea23a6ccdb8095a49eea`, eight commits, one per
finding.

> **Push note.** `git push` to `Metta-AI/cogame-liars-dice` 401s in this sandbox
> (`git-credential-anthropic` authenticates fine against `Metta-AI/coworld-builder` but the same
> credential is rejected by `cogame-liars-dice`, as is `GH_TOKEN` over https — `gh api` is the only
> write path this repo has, which is how it was populated in the first place: see `80e72f5`,
> "the Git Data API cannot create a repo's first object"). The eight commits were therefore
> replayed through the Git Data API one commit at a time, preserving each message, each tree and
> the `100755` bit; `git diff HEAD origin/main` is empty and `git ls-tree` confirms
> `100755 tools/ci/build_renderer_fixture.sh`. The shas below are the pushed ones.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `03c5d61f` | `client/fixtures/worst_case.{html,js}`, `tools/ci/build_renderer_fixture.sh`, `.github/workflows/ci.yml:339-419` |
| B2 | fixed | `e8d76eee` | `client/renderer.js:130-247`, `:582-610` (`drawSpeech`), `:612-661` (`drawParchment`), `:663-720` (`inkWidth`/`breakWord`/`wrapLines`) |
| N1 | DISPUTED | — | `src/liars_dice/server.nim:538` |
| N2 | fixed | `9afcb37f` | `src/liars_dice/server.nim:337-349` |
| N3 | fixed | `3da045a9` | `client/chrome.css:544-557` |
| N4 | fixed in part / rest DISPUTED | `3da045a9` (DOM half) | `client/chrome.css:555-557` |
| N5 | fixed (the note, not the code) | `0c346d8b` | `client/chrome.css:507-517` |
| N6 | fixed | `61b58c17` | `client/chrome.css:490-494` |
| N7 | fixed | `834ee500` | `client/chrome.css:525-535` |
| N8 | fixed | `8e74a850` | `tests/test_sim.nim:522-568` |
| N9 | DISPUTED | — | `src/liars_dice/llm.nim:69-72` |

---

## B1 — the viewer draws LLM text and no gate ever draws it → **worst-case renderer fixture**

**Satisfies acceptance-checklist item 15**, final bullet ("The CI replay cannot talk … a repo that
draws model text and has no such fixture is a blocking `legibility` finding").

**What the repo did:** `renderer.js` drew `seat.say` (speech plate), `seat.notes` (parchment) and
`.feed-say` lines, while `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`, every seat falls back
to `scriptedAction`, and that never sets `say`/`notes`. The only replay CI ever loaded carried 13
events, 0 with `say`, 0 with `notes`. `ls client/` had no `fixtures/`.

**What it does now** (`03c5d61f`):

- `client/fixtures/worst_case.html` + `worst_case.js` — a page that loads the **real**
  `client/renderer.js` and drives it through its **real** `attachReplay` entry point with a frame
  built to hurt:
  - a **full-cap 140-rune remark on every one of the four seats at once**, in capitals (the widest
    run of glyphs a model can send);
  - a **full-cap 400-rune `notes` payload on every seat**, each containing an unbreakable
    44-character token (`COUNTERBLUFF-LEDGER-DEAL-03-SEAT-2-ROLLING`);
  - the tallest stage state — four revealed hands, the standing-bid plate and the challenge
    verdict banner up together;
  - the entrance animations (bid slide-in `BID_SLIDE_MS`, verdict tally `TALLY_MS` and the
    `VERDICT_HOLD_MS`+`VERDICT_FADE_MS` fade) sampled both mid-animation and **played through to
    settle** — each size is checked twice, a few frames after the resize and again 2.9 s later;
  - at **seven canvas sizes**: 1280×800, 1000×560, 960×640, 720×480, 640×360, 480×720 and the
    360×640 featured-match width.
- **It asserts its own strings are still full-length.** At every size it re-checks
  `Array.from(say).length === 140` and `Array.from(notes).length === 400` (rune counts, matching
  the server's cap), and then walks the drawn `fillText` fragments in draw order and requires them
  to **reconstruct each source string exactly** — an ellipsis, a dropped line or a clipped tail
  leaves the walk short and fails. It also fails on any draw whose measured box crossed a canvas
  edge, and requires `#feed` to carry both full strings as text (the `.feed-say` path).
- **It cannot pass on frame one.** `renderer.js` sets `data-replay-loaded` on its first drawn
  frame; the fixture intercepts `documentElement.setAttribute`, holds that signal, and only emits
  it (through the saved real setter) after all seven sizes have passed — and it *requires* the
  interception to have fired, so a fixture that failed to drive the real renderer fails.
  Any problem sets `data-replay-error=<first problem>`.
- `tools/ci/build_renderer_fixture.sh` (mode `100755`) assembles the page with the real
  `renderer.js`, the real `chrome.css` and the real `data/` assets — including `font.ttf`, because
  the bands are measured in the face they are drawn in.
- `.github/workflows/ci.yml` gains a **`renderer-fixture` job with its own step**,
  `Load the worst-case renderer fixture in a real browser`, running
  `node tools/ci/viewer_smoke.mjs --bundle dist/renderer-fixture --replay … --timeout 120
  --strict-text-bounds`, with the png+json uploaded as evidence. It needs no replay and no wasm,
  so it does not `needs:` anything.

**Evidence.** Run 33013575662, job **98325857248** (`renderer-fixture`), step
`Load the worst-case renderer fixture in a real browser`, conclusion `success`, not
`continue-on-error`:

```
{"loaded":true,"ms":21463,"clock":"DEAL 1 / 3 · FINAL","scorebug":"liars-dice-calibrator 0 POINTS …"}
canvas text: 81665 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
```

81 665 drawn strings against 2 474 in the replay smoke — that gap is the model text nothing used
to draw. **The fixture is not vacuous:** run locally against the pre-B2 renderer (`git show
HEAD~1:client/renderer.js` swapped into the bundle, pinned Playwright 1.55.0 chromium) it exits 1
with `data-replay-error: 1280x800 entering: the full-cap say of seat 0 was not drawn whole
(ellipsized or clipped by the band)`.

## B2 — bands sized by eye → sized from `MaxSayLen` / `MaxNotesLen`, measured in the real face

**Satisfies acceptance-checklist item 15**, bullets 2 and 3 (reserved band "sized from the cap the
server enforces on that string … and measured in the font it will be drawn in"; "Ellipsis is …
a defect for sentences … widen the band, do not shorten the text").

**What the code did:** `SAY_LINES = 2`, `NOTE_LINES = 3` (1 below 480 px), line height a constant
`12 * scale` independent of the font floor, and band width `max(size * 1.9, handW)` — none of it
derived from `MaxSayLen = 140` / `MaxNotesLen = 400` (`sim.nim:27-28`). Measured in the shipped
`rajdhani` face with the pinned chromium, the mixed-case advance is **0.43 em** and the
capitals advance **0.54 em**, so the reviewer's arithmetic was right: at 960×640 the old two-line
plate held ~70 of 140 characters and the parchment ~105 of 400, and `wrapLines` ellipsized the
rest — an ellipsis on a **sentence**.

**What it does now** (`e8d76eee`):

- `MAX_SAY_LEN` / `MAX_NOTES_LEN` mirror the server's caps, with the `sim.nim` line cited.
- `capLines(ctx, usableWidth, cap)` turns a cap into a **line count** by `measureText`-ing a
  capitals-and-digits reference in the font the band will actually be drawn in, dividing the band's
  real width by that advance and applying `WRAP_FILL = 0.92` for the ragged right edge a greedy
  wrap leaves. Capitals, not mixed case, because a model that SHOUTS must get the same room.
- The **line box comes from the font size actually used** (`LINE_SPACING = 1.22` × the drawn px),
  so the 9 px floor can no longer put 11 px text into a 9 px line.
- The block **widens into the room the seat has** — `min(width / 2 - 16, size * 5.5)`, the width of
  the pair of seats that shares a row — because a wider band is a shorter band, and widening is
  precisely what the checklist asks for.
- A token wider than the line is **broken**, not ellipsized (`breakWord`).
- Both bands stay **reserved whether or not a seat is talking** (`seatBlock` adds them to
  `above`/`below` unconditionally, and `computeLayout` clamps every block inside the frame), while
  the drawn plate/sheet **hugs its own text inside that reservation** — so a silent table is not
  four blank sheets of paper and a remark landing still moves nothing.
- If a frame is too short to hold both full bands, the reservation is handed back a line at a time
  rather than drawing past the bottom edge. Not reached at any size the fixture renders.
- The ellipsis path in `wrapLines` survives only for that degenerate case and for **labels**
  (nameplates, `bid by …`, the verdict line), which is where the checklist wants it.

**Evidence.** The B1 fixture with `--strict-text-bounds` is the proof: with four 140-rune remarks
and four 400-rune notes up at once, at seven sizes,
`canvas text: 81665 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`, and
the fixture's own reconstruction check passes for all eight strings at all seven sizes. The same
harness on the **old** renderer fails at the first size. The silent case (the CI replay's shape)
was checked locally too: same seven sizes with empty `say`/`notes` → `37383 drawn, 0 never inside,
0 outside, 0 ellipsized`, and `wasm-viewer` on the real replay is still
`2474 drawn, 0 never inside …, 0 ellipsized`.

**The design note is what was wrong here.** design.md:677 ("2 lines, ellipsized"), :680 ("3 lines,
ellipsized") and :702 ("notes parchments drop to 1 line there") specify the behaviour the checklist
calls a defect. Checklist item 15 overrides the note on this point; the note was not treated as
licence, and the commit message says so.

## N1 — the literal string `/client/replay` — **DISPUTED**

No change. Checklist 3's "No `/client/replay` pod path anywhere" is about a hosted replay pointed
at a **pod**. This repo has none: `coworld_manifest_template.json:14-16` declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and nothing else, no workflow or viewer file
points a hosted replay at a container, and `tools/build_replay_viewer.sh` builds the static wasm
bundle that `wasm-viewer` then loads. `server.nim:538` is the **live game server's** debug page,
inherited byte-for-byte from the starter (`/workspace/starters/cogame-babel/src/babel/server.nim:502`
has the identical route), and the manifest sentence at line 383 is the starter's (its line 211).
design.md:874-875 puts a `/client/replay` pod explicitly out of scope. Deleting the live route
would diverge from the starter's chrome (checklist 14) to satisfy a grep, so it stays and the
reviewer's own reading is recorded here rather than acted on.

## N2 — mid-deal deadline baseline — fixed (`9afcb37f`)

design.md:408: "play deadline reached mid-deal | remaining decisions of that deal are `bayes`
(instant) so the deal completes". The guard set `scripted = true` but left `baseline` at whatever
the seat registered. Now the coercion to `bayes` applies to seats that would otherwise have called
the model; a seat registered `PLAYER_SCRIPTED=pressure` keeps `pressure`, because that is its
**policy**, not a deadline substitution — the note's sentence is about finishing an interrupted
deal, not about overriding a scripted filler's line. No behaviour change ships today
(`liars_dice_player.nim:44-45` sends `baseline: "bayes"` whenever `PLAYER_SCRIPTED` is unset), but
the server no longer depends on the player to hold the invariant. Checklist 5's bound is
unaffected: both baselines are instant. `nim check src/liars_dice/server.nim` clean locally with
Nim 2.2.4 and the synced package tree; `docker-smoke` green in the run above.

## N3 — `--band` / `--hudscale` published, never consumed — fixed (`3da045a9`)

**Satisfies checklist 14(a)/(b).** `relayout()` set both on `document.documentElement` and nothing
read either, so `replay.html`'s own comment ("every drawn HUD measure scales with the container
rather than the viewport") described nothing.

- `#loading` is the one overlay positioned against the **viewport** rather than against
  `#board-wrap`, so it is the one box that covers the transport: it now rides
  `bottom: var(--band, 0px)` — 14(b)'s rule applied to the only element it can apply to here.
- `#clock`, `.plate-name` and `.plate-score` size from `--hudscale`, floored at 11 px with
  `max()`.

Measured with the pinned chromium: at a 360 px page `--hudscale` computes to `0.700`, `--band` to
`71px`, `.plate-name` and `#clock` to `11px`, and all four names still render in the scorebug; at
1280 px, `14px` / `15px`.

## N4 — "no drawn string smaller than 11 px" — fixed for the DOM, **DISPUTED** for the canvas

The note's sentence (design.md:700-701) is about **`--hudscale`**, which is a DOM variable; N3 now
makes that sentence true of the strings it governs (`#clock`, `.plate-name`, `.plate-score` floor
at 11 px). The canvas floors (8–11 px, driven by `layout.scale`) are left as they are, and
deliberately: raising the band font floor to 11 px would multiply the cap-derived line counts of
B2 by ~1.2 and, at 360 px wide, push a full-cap 400-rune payload past what the frame can hold —
i.e. it would buy 11 px glyphs by re-introducing the ellipsis on sentences that checklist 15 calls
a defect. Checklist 11, which is the gated one, concerns the DOM scorebug and is satisfied
(`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under 640 px, and now an 11 px
floor). The residue is a **note-vs-code wording mismatch**, not a code defect.

## N5 — `.plate-pip.hollow` — fixed in the direction the *game* needs (`0c346d8b`)

The design's removal list (design.md:619-621) names `.plate-pip.hollow` among babel's tail rules,
and the rule survived the diff byte-for-byte, so it read as a leftover. It is not one: this
scorebug draws one filled pip per deal **won** and one hollow pip per deal **lost** — design.md's
own "Readouts" section says "pips = wins (filled) + losses (hollow)", and `renderer.js:1015-1017`
emits `<span class="plate-pip hollow">` per loss. Deleting it would render every loss as a win, so
the *removal list* is what is wrong. The rule is now declared next to the other scorebug rules
inside the `liars-dice additions to the inherited cogame-babel chrome` block with the reason
recorded, so it is unambiguously a liars-dice rule rather than an inherited leftover. No rendered
change.

## N6 — `.seat5` — fixed (`61b58c17`)

**Checklist 14(d)** ("a kind with no rule is an invisible marker"), applied to the seat-colour
classes. `renderer.js:28` carries six `COLORS` and stamps `seat<i % 6>` on beat markers and feed
lines while the inherited chrome stopped at `.seat4`. One rule (`.seat5 { --tc: #e08a3a }`, the
orange the renderer already uses) closes the trap. No shipped variant seats more than four.

## N7 — `.end-panel { min-width: 380px }` in a 360 px frame — fixed (`834ee500`)

**Checklist 11** (legible at 360 px), extended past the scorebug it gates. Below 480 px the panel
sizes to the frame and the two rate columns step aside. Measured at a 360 px viewport with the
pinned chromium: the panel is **323 px wide at x = 18** and all four seat names render in full,
where before the fix it was 346 px wide with every name collapsed to a single letter ("W.", "l.",
"R."). Additive — the inherited rule above the banner is untouched.

## N8 — replay asserted only the final frame — fixed (`8e74a850`)

**Satisfies checklist 2** ("Replaying the recorded events through the sim reproduces the recorded
per-tick state **frame by frame** … A test asserts it"). The suite pinned the endpoint plus the
first two frames' event counts, so the middle of the timeline could drift and stay green. The new
case in `tests/test_sim.nim` snapshots the live sim's `tableStateJson()` after **every event it
logs**, indexed by log length, and compares each snapshot with the frame `replayMatch` derives at
that index — every frame of a 3-deal episode except the one state between the closing challenge
and the `end` event, which the live sim never occupies because `applyChallenge` settles in the same
call (the test asserts the count of frames actually compared, so the skip cannot silently grow).
Ran locally with Nim 2.2.4 in debug and `-d:release`; green in the `test` job of run 33013575662.

## N9 — `clipText` vs babel's byte slice — **DISPUTED**

No change. design.md:214-215's "ported unchanged" is about the parsing behaviour of
`extractJsonObject`; the one deviation (`clipText(text.strip(), 160)` with `runeSubStr` instead of
babel's `head[0 ..< 160]` byte slice) is exactly what **checklist 9** requires — "Every string that
reaches the replay (`say`, `notes`, prompts, captured errors) is truncated on **rune** boundaries".
Reverting it to be byte-identical to the starter would falsify a gated item to satisfy an ungated
sentence in the note. The reviewer says as much ("the deviation is in the direction checklist 9
asks for"); recorded, not acted on.

---

## NOTED (not fixed)

- **Worst-case crowding.** Four 400-rune notes payloads and four 140-rune remarks up at once is
  ~2 160 characters of model text on one canvas; at 960×640 and below the seat blocks are adjacent
  and, at 640×480, they overlap each other. Nothing is drawn outside the frame and nothing is
  ellipsized (that is what the fixture gates), but the extreme frame is dense. The alternative —
  a smaller band — is the ellipsis checklist 15 forbids. Worth revisiting only with a design
  decision about how much of a seat's notes the felt should show at once.
- **The north seat's alias sits under the standing-bid plate** at some sizes now that the reserved
  bands are taller (the ring's vertical radius shrinks by ~30 px). The plate is drawn after the
  seats, so the alias is dimmed rather than lost, and the scorebug carries every seat's name and
  points. Fixing it properly means moving the plate off the felt centre, which is a design change.
- `sim.nim`'s caps are mirrored as literals in `renderer.js` (`MAX_SAY_LEN`, `MAX_NOTES_LEN`) with
  the source line cited in a comment; nothing in the build asserts they agree. A generated
  constant, or an assertion in the fixture against a value the server emits in the replay
  `config`, would close that.
- Checklist 7's second sentence ("tuned with a grid harness, not guessed") is still unsupported in
  the tree — the reviewer's "Could not determine" item. Out of scope for this round: no finding
  was filed on it.
