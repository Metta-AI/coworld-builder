# r1 fixes — fog-of-war-boards

Head: `0e893df12ee180b31e95a5701a88c20a73e16745` (branch `main`)
CI: https://github.com/Metta-AI/cogame-fog-of-war-boards/actions/runs/33033443296 — **success**
(`test`, `docker-smoke`, `wasm-viewer` all `success`; `headSha 0e893df1…`; run id `33033443296`).
`grep "SEAT-COUNT FAIL"` over the full run log: no match.

Pushed through the GitHub Git Data API (blobs → tree with `base_tree` = the previous head's tree →
commit → PATCH `heads/main`); plain https push is rejected in this sandbox
(`remote: No anonymous write access`). `100755` survives on `tools/build_replay_viewer.sh` and
`tools/ci/docker_smoke.sh` — verified with `git ls-tree origin/main`.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `6d29819` | `tools/ci/renderer_fixture.html:59-65, 341-350` |
| B2 | fixed | `0d3679f` | `tools/ci/renderer_fixture.html:85-103, 351-359` |
| N1 | fixed | `8689e63` | `src/fogboards/sim.nim:425-437`, `tests/test_sim.nim:365-390` |
| N2 | fixed | `655dc61` | `src/fogboards/llm.nim:56, 325`, `src/fogboards/server.nim:320-326, 345` |
| N3 | rebutted | — | `src/fogboards/server.nim:216-217` |
| N4 | fixed | `b8cdac8` | `src/fogboards/llm.nim:289-304` |
| N5 | fixed | `c091f67` | `src/fogboards/llm.nim:653, 661, 666` |
| N6 | rebutted | — | `client/replay_broadcast.html:74-89` |
| N7 | rebutted | — | `replay-viewer/index.html:13` and the three client pages |
| N8 | fixed (first half) / rebutted (second half) | `e237df7` | `src/fogboards/sim.nim:646-651` |
| N9 | NEEDS-DESIGN | — | `client/chrome.css:534-548` |
| N10 | rebutted (documented behaviour) | — | `tools/ci/renderer_fixture.html:294-308` |
| N11 | fixed | `654dfc2` | `tools/ci/renderer_fixture.html:298-308` |
| N12 | fixed | `18fd340` | `client/renderer.js:642-650, 659, 685` |
| N13 | fixed (fourth bullet) `0e893df` / rebutted (the other five) | `0e893df` | `src/fogboards/server.nim:489-499` |

One commit per finding, in review order, each parented on the previous. No test was weakened,
skipped or deleted: the only test change this round is the **added** test 11b in
`tests/test_sim.nim` (`git diff 791cf71 0e893df -- tests/` is one added test block).

---

## B1 — the fixture asserted its remark was ≥ 20 runes, not full-length

**Commit `6d29819`** — `fix(fixture): r1-B1 — the say band must carry the whole 80-rune cap`.

Was: `if (Array.from(text).length < 20) problems.push(…)` — a floor at a quarter of the cap, so a
renderer that sliced `say` to 30 runes, or a `fullSay` quietly shortened to 30, left the fixture
green while testing nothing above 30 runes. Now: a named constant `SAY_RUNES = 80` (the same number
as `llm.nim MaxSayLen` and `renderer.js MAX_SAY_LEN`) both **builds** `fullSay` and is asserted
**exactly** against the band's `textContent` at every one of 360 / 640 / 1280 px:

```js
var runes = Array.from(node.textContent || "").length;
if (runes !== SAY_RUNES) { problems.push("the say band at " + width + "px carried " + runes +
  " runes, not the full " + SAY_RUNES); }
```

A shortened remark at either end — fixture or renderer — now fails the fixture instead of passing
it. `textContent` rather than `innerText` so the comparison is against the exact string the page
laid out rather than a whitespace-normalised rendering of it.

Evidence: run `33033443296`, job `wasm-viewer`, step **Load the worst-case renderer fixture** →
`{"loaded":true,"ms":3805,…}`, i.e. the exact-80 assertion held on all three widths against the
shipped `dist/static-replay-viewer/index.html`. (The B1-only push, sha `6d29819`, was also green on
its own run `33033196188`.)

**Checklist item satisfied:** 15, fourth bullet — "The fixture asserts its own strings are still
full-length — one quietly shortened remark leaves it passing while testing nothing."

## B2 — the fixture padded its own remark with U+2026, so `ellipsized` counted remarks forever

**Commit `0d3679f`** — `fix(fixture): r1-B2 — pad the worst-case remark with · , not U+2026`.

Was: `while (runes.length < 80) runes.push("\u2026")`, so the two 70/72-rune base sentences shipped
with 10 and 8 trailing ellipses, and `viewer_smoke.mjs:368` (`/\u2026\s*$/`) classified each drawn
remark as `ellipsized` — six of the eight reported in run `33031534557` were remarks. Now the filler
is `\u00b7` (MIDDLE DOT, a non-ellipsis multi-byte rune, narrow enough that the line still lays out
on one row), with the reason written next to it. The same commit adds the gate the finding implies:
the fixture now **fails** if any `.plate-say` ends in an ellipsis, so the signal cannot be smothered
again from either side.

Evidence — same step, same run, the `canvas_text` line:

```
canvas text: 33 drawn, 0 never inside the canvas (0 draws crossed an edge), 2 ellipsized (--strict-text-bounds)
  ellipsized: "fog-of-war-boards-carto…"
  ellipsized: "fog-of-war-boards-carto…"
```

8 → 2, and both survivors are the nameplate `clampName` cut (`chrome_common.js:117-120`) — a
**label**, which is the design choice the checklist explicitly allows. Zero remarks are ellipsized,
so a real renderer ellipsis on a `say` is once again distinguishable in this repo's CI output. The
band itself was never the problem (`never_inside` 0, no `clipped` entry, the whole line on one row)
and was not widened — the finding's own reading.

**Checklist item satisfied:** 15, third bullet — "If `ellipsized` counts a remark rather than a
nameplate, the box is too small" — the counter now counts only nameplates.

## N1 — a cell filled by the opponent deleted the seat's own sensed-empty record

**Commit `8689e63`** — `fix(sim): r1-N1 — a fill no longer deletes the OPPONENT's sensed-empty record`.

Was (`sim.nim:425-431`): the placement branch looped `for other in 0 ..< Seats:
sim.sensedEmptyAt[other].del(cell)`. In `recon-hex-5` that meant seat 1's placement on `b3` silently
removed seat 0's `sensedEmptyAt[0][b3]`, so `b3` moved from `CELLS YOU SENSED EMPTY (may be stale)`
to `CELLS YOU HAVE NEVER TOUCHED` in seat 0's next prompt while the referee log in the same prompt
still said the referee had shown it empty — a seat diffing its own list across plies reads the
opponent's move out of it, which design.md:47-49 and :718-723 say is not a channel that exists. The
belief board's staleness dot (`client/renderer.js:516-529`) also vanished on the fill instead of
fading.

Now only the mover's own record is rewritten: `sim.sensedEmptyAt[seat].del(cell)`. Test **11b**
(added in the same commit) pins it: seat 0 senses `b3`, seat 1 senses the same block and then fills
`b4`; seat 1's own entry is gone, seat 0's entry **and its ply-0 timestamp** stand, and `b4` is
still legal for seat 0 and still `ocEmpty` on its believed board (sensed-empty is not occupancy
knowledge).

Evidence: run `33033443296`, job `test` —
`[OK] 11b. a fill by the opponent leaves the other seat's record alone` in both the debug and the
`-d:release` pass; test 12 (redaction) and test 14 (baseline blindness/legality) still green.

**Checklist item:** advisory — no checklist item is falsified either way (which is why the reviewer
filed it non-blocking). It restores design.md:47-49's single-channel rule and closes the "could not
determine" item on N1 with the test the reviewer named as what would settle it.

## N2 — an attempt decided by the baseline because the client was disabled was recorded `scripted: false`

**Commit `655dc61`** — `fix(server): r1-N2 — record the decision that actually decided the ply`.

`types.nim:57` documents `attempt.scripted` as "decided by a scripted baseline", but
`server.nim` passed `seatScripted` — the seat's *declared* `PLAYER_SCRIPTED` flag. With no
`ANTHROPIC_API_KEY` the client disables itself (`llm.nim:688`) and a prompt seat is decided by
`probe`, yet every attempt of the prompt seat in the smoke replay carried `"scripted": false`.
`Decision` now carries a `scripted` field set by `scriptedDecision` (and left false by a parsed LLM
reply), and both the normal path and the belt-and-braces exception path record that.

Evidence: `smoke-replay` artifact of run `33033443296` — the prompt seat's attempts now read
`"scripted": true, "fellBack": false`, and `results.fallbacks == [0, 0]` is unchanged, because the
disabled-client path is not the parse/transport fallback that checklist 8 counts.

**Checklist item:** 8 was already met (`server.nim:312-313` + the greppable `falling back` line) and
still is; this makes the recorded audit field mean what `types.nim` says it means.

## N3 — the wall-clock guard's worst case lands ~2–3 s past 60 % — **rebutted**

Not changed, and deliberately. The guard is implemented **exactly** as the note specifies:
`worstPlySeconds = 2 * llmTimeoutSeconds + 2 = 62` (`server.nim:216-217`) against
`playDeadline = gameStart + 0.6 × episodeTimeoutSeconds`, which is design.md:154-156 and :388-392
verbatim, including the note's own decision not to fold the 4 s spacing floor into it. The finding
is the note's arithmetic, not a deviation from it: the reviewer's own trace lands the artifact write
at ≈ 723 s of 1200 (60.25 %), requires a fast ply followed by a double-timeout ply to reach, and
leaves ~450 s before the platform kill. Every wait in the path is explicitly bounded (the reviewer's
"Every wait and its bound" section lists all five). Widening `worstPlySeconds` here would put the
code at odds with the design note that defines it, which is the document the checklist measures
against. Checklist 5 is not falsified: no unbounded wait, no blocking read, and the expected path
finishes at 7–18 % of the budget.

## N4 — `sweep` restarted the corridor at offset 0 after a shift

**Commit `b8cdac8`** — `fix(bot): r1-N4 — sweep continues from the same corridor offset after a shift`.

design.md:345-349: "on `OCCUPIED`, shift the whole corridor one step … and **continue from the same
offset**". `sweepCell` shifted the lane correctly (`(n div 2 + probes[seat]) mod n`) but then walked
`for offset in 0 ..< n`, re-covering ground the corridor had already crossed. The walk now starts at
the offset the corridor has reached — which advances only when the seat actually takes a corridor
cell, i.e. the seat's own stone count — and still falls back to the lowest-index legal attempt when
the corridor is exhausted, so **every produced attempt is still legal by construction** (each
candidate is checked `in legal`, and the fallback is `legal[0]`).

Evidence: run `33033443296`, job `test` — `[OK] 14. 200 seeded episodes x 4 variants x 2 baselines
stay legal` (legality of every attempt and every anchor, plus the blindness check), and
`probe/sweep disagreement: 1800/2450 = 0.7347` (was `1750/2450 = 0.714`), still far above the
note's 30 % floor. Test 7 (termination bound) and test 13 (every variant constructs and completes)
green.

**Checklist item:** 7 — "Scripted baseline plays full episodes legally" — re-verified after the
change by tests 13, 14 and 7.

## N5 — two error slices were byte slices of an HTTP body

**Commit `c091f67`** — `fix(llm): r1-N5 — cut HTTP error bodies on runes, not bytes`.

`completeText` built its 401/403, 429 and other-status `FogError` messages from
`response.body[0 .. min(response.body.high, 400)]` and two 300-byte slices. A byte cut can land
inside a multi-byte rune, and that text reaches stdout: the outer echo
(`cleanText(error.msg…, MaxErrorLen)`) re-cuts only when the message exceeds 200 runes, so a shorter
one kept the broken tail byte. All three now go through the shared rune-safe `cleanText` at
`MaxErrorLen` — which is also the cap design.md:748-750 names for "any error text that reaches an
event or the log (200)", and which the finding correctly observed was previously referenced from
only one site.

The other half of N5 — the two `160` caps at `llm.nim:536-537` and `:664-666` — is **rebutted**: both
already cut on rune boundaries (`runeSubStr` and `cleanText` respectively), and they are *inner*
caps on a message that the 200-rune log cut then bounds again, i.e. stricter than the note, not
looser. No error text reaches an event or the replay in this repo (`GameEvent` has no error field),
as the reviewer establishes.

**Checklist item satisfied:** 9 — "Every string that reaches the replay (`say`, `notes`, prompts,
**captured errors**) is truncated on rune boundaries."

## N6 — the appended `<script>` block registers nothing — **rebutted**

The reviewer's own conclusion: "the note's placement is wrong, not the code." `setFeedText` /
`setEndColumns` are invoked from `attachLive` / `attachReplay` (`renderer.js:844-845`, `:926-927`),
which run before the first `renderFeed` / `updateEndscreen`, so the injection is in place whenever
it is read. Moving the registration into the four copied pages would add edits to pages that
checklist 14 wants byte-identical-plus-an-appended-block, for no behavioural change. Not changed.

## N7 — the `#clock` "ROUND 0" → "PLY 0" edit is unlisted — **rebutted**

design.md:604 requires that "everything human-facing renders it as **PLY n**". The `#clock`
placeholder is human-facing, so reverting it to `ROUND 0` would break the note; leaving it is what
the note's intent requires, and the reviewer verified that **nothing is removed** from any of the
four pages and that the diff against `cogame-babel@d55d999` is otherwise exactly the listed edits.
Not changed (and the design note, which the fixer may not edit, is where the enumeration lives).

## N8 — the `start` event omitted `round`

**Commit `e237df7`** — `fix(replay): r1-N8 — the start event carries round: -1, as the note specifies`.

`eventToJson` wrote `round` only when `>= 0`, so the opening event serialised as `{"kind": "start"}`
while design.md:594 gives it as `{kind, round: -1}`. The key is now always written. Every consumer
already treats a negative round as "no ply" — `eventFromJson` defaults to −1 (`sim.nim:681`),
`renderFeed` and `buildScrub` special-case `start`, and `markPlyBeat` guards on
`typeof event.round === "number" && event.round >= 0` — so the change is bytes-only.

Evidence: the `smoke-replay` artifact of run `33033443296` opens
`{"kind": "start", "round": -1}`; the `wasm-viewer` job replayed that same artifact (digest-matched
download) and reported `loaded: true`, three differing scrub readouts and a clean 10 s soak.

**Second half rebutted:** the `end` event's `round` (`plies − 1` for connection/line/board-full,
`plies` for ply-cap/deadline) is not pinned anywhere in the note, and the chrome renders the end
block against `lastBlock` rather than the field (`chrome_common.js:155-156`, `:329-330`). Changing
`settle`'s `event.round` would move a value no consumer reads and would alter the recorded bytes for
every ending. Not changed.

**Checklist item:** 2 — the replay bytes now carry the header field the note documents; frame-by-frame
re-derivation (tests 18, 19) is unaffected and still green.

## N9 — `.plate-say` is sized by constants, not by measuring the cap — **NEEDS-DESIGN**

Real, and not fixed here. design.md:941-943 asks for a band "sized from `MaxSayLen = 80` measured in
the render font at the current `--hudscale`"; `chrome.css:534-548` sizes it with
`min-height: calc(13px * var(--hudscale)); max-height: calc(40px * var(--hudscale))` and clips with
`overflow: hidden`. Making the band measure at runtime means the scorebug can no longer be a pure
CSS grid — it needs a measurement pass in `updateScorebug` (a hidden canvas `measureText` at the
computed font, feeding a `--sayband` custom property), which changes the layout contract the game
block and the media queries are built on. That is a design change, not a fix at the cited site, so I
have recorded it rather than made it.

What holds today, and what B1 strengthened: checklist 15's second bullet is met — the band is
emitted unconditionally, empty or not, so the scene does not jump — and the *measurement* is
performed in CI at the three widths against the real render font by the fixture's
`scrollHeight > clientHeight + 2 && overflow === "hidden"` check, which now runs against a remark
asserted to be exactly 80 runes. Run `33033443296` reports no `clipped` entry at 360 / 640 / 1280 px.

## N10 — the fixture clamps transcribed runs into its scratch canvas — **rebutted (documented)**

The clamp is deliberate and documented in the file (`renderer_fixture.html:294-300`): a run that
cannot fit at all is reported through the `clipped` array rather than smuggled in as a bounds miss.
The meaningful gates in that step are the two `clipped` checks and the iframe's **own** canvas
report, which the fixture reads and fails on (`never_inside > 0`). Nobody should read the fixture's
`never_inside: 0` as evidence about the scorebug or the feed — which is exactly what the finding
says, and it is now also what the reviewer's report records. No code change is available that would
improve the gate without re-implementing the drawing, which the note forbids (design.md:1238-1240).

## N11 — `transcribe`'s `var width` shadowed its parameter

**Commit `654dfc2`** — `fix(fixture): r1-N11 — transcribe's inner var no longer clobbers its parameter`.

`function transcribe(width)` declared `var width = ctx.measureText(text).width` inside itself, so the
parameter was reassigned on the first node: the "text is clipped by its own box" message read
`@undefined px` for the first entry and the previous node's measured text width for every entry
after. The measurement is now `textWidth`, and the message carries both numbers
(`"… @360px is 1412px wide"`). Pass/fail behaviour is unchanged — the entry was pushed and failed
the fixture before, and does now; this is the diagnostic, which is the entire value of the entry
when it fires.

**Checklist item:** 15 — the fixture's failure message is the evidence the checklist asks a reviewer
to cite.

## N12 — `updateScorebug` truncated `say` on UTF-16 code units

**Commit `18fd340`** — `fix(viewer): r1-N12 — cap the scorebug's say on runes, not UTF-16 units`.

`C.escapeHtml(say.slice(0, MAX_SAY_LEN))` cut on UTF-16 code units, so a rune-safe 80-rune `say`
containing an astral character (an emoji is two units) would be split mid-surrogate-pair and the
band would draw a lone half. The new `capSay` cuts on runes (`Array.from`) and is a no-op on every
string the server can send, since `llm.nim`'s `cleanText` already caps at 80 **runes**. Declared in
the game block, not the chrome; `tools/ci/chrome_scope_check.mjs` re-verified in CI —
`20 exported chrome names, 59 game-block declarations, no overlap, 8 copied regions intact`.

**Checklist item:** 9 — rune-safe truncation, extended to the one place in the viewer that re-applied
the cap on the wrong unit. (The replay-side strings were already rune-safe and pinned by
`tests/test_replay.nim:166-209`.)

## N13 — the six smaller deviations

**Fourth bullet, fixed — commit `0e893df`** (`fix(server): r1-N13 — an unknown baseline name no
longer drops the prompt`). A player frame carrying `{"scripted": "mirror"}` made `parseBaseline`
raise; the handler's outer `except CatchableError` swallowed it, so the slot lost the **prompt** it
had just delivered as well as the baseline. The parse is now guarded on its own: the slot keeps its
prompt, falls back to `probe`, and the reason goes to stdout through `cleanText(text, 40)`.
`parseBaseline` itself is unchanged, so `tests/test_bot.nim:217-218`'s expectation that it raises on
`"mirror"` still holds — and did, in run `33033443296`.

The other five are **rebutted**:

- **`coworld-release.yml` certify without `--timeout-seconds 300`.** The file is byte-identical to
  `templates/coworld-release.yml` after the `<slug>`/`<IMAGE>`/`<SEATS>` substitution — the
  reviewer verified this. Checklist 12 requires the template's step order and the placeholder gate,
  both of which hold; editing the workflow away from the template would destroy the provenance the
  checklist actually asks for. The note is describing something the template does not do.
- **`phaseText` returns `"sensing"` whenever `config.sense > 0`.** There is no separate sensing
  phase to report: step 6 and steps 7–12 are applied inside one atomic ply
  (`server.nim:315-321`), so a spectator snapshot can never be taken between them.
  design.md:673 only enumerates the legal set, which `phaseText` respects.
- **`newWebSocket(url)` outside the `try`.** design.md:420-422 asks for the **receive loop** to be
  wrapped so a close frame exits 0 (`fogboards_player.nim:64-90` does exactly that). A failure to
  connect at all is not a dead socket mid-episode; it should exit non-zero so the runner sees it.
- **75 seeds × 2 baselines × 4 variants in tests 10 and 12.** 600 episodes per test, i.e. more
  episodes than the note's "300 seeded episodes", over 75 distinct seeds. This is a test-strength
  observation, not a checklist item, and the only change available is *raising* the loop bound —
  which I have not made, because widening two 600-episode loops to 2400 each is a CI-time change
  that no finding in this round requires. Listed under NOTED below.
- **`guessAccuracy` of exactly 0 renders `"0%"`.** `"0%"` is the correct rendering of a zero
  accuracy; `"—"` is reserved for a value that is not a number at all (a seat that never guessed
  reports `guessesMade == 0` and the endcard says so in the neighbouring column).

---

## NOTED (not fixed)

- Tests 10 and 12 (`tests/test_sim.nim:296`, `:368`) use 75 distinct seeds; the note says 300. A
  future round could raise the seed count if CI time allows.
- The `.plate-say` band is still sized by constants (N9) — recorded above as NEEDS-DESIGN with the
  shape the change would take.
- No shipped CI path exercises `sense > 0` (the cert fixture is `dark-hex-5`, `sense: 0`), so the
  sense-window overlay and the belief board's fading dot — the thing N1 restores — are still not
  screenshotted anywhere. A `recon-hex-5` payload in `renderer_fixture.html` (or a second fixture
  run with `sense: 2` and a `lastSense`) would settle the reviewer's first "could not determine"
  item. Out of scope for this round: it is a new fixture, not a fix at a cited site.
