# r1 fixes — poker

Repo: `Metta-AI/cogame-poker`, branch `main`.
Head: `bba6bffe83313b103f921346fe0d964cbb92725d`
CI: <https://github.com/Metta-AI/cogame-poker/actions/runs/32997839855> — **success**
(`push`, branch `main`, headSha `bba6bffe…`; jobs `test` ✅, `docker-smoke` ✅, `wasm-viewer` ✅).
Base reviewed by r1: `7c7e77b977a0256df4d0b78ce79fb35f3d6b1489`. Three commits — one per finding
plus one follow-up on B2 the coordinator asked for after reading this file — fast-forward only
(pushed through the GitHub Git Data API with the local→remote sha map seeded at `7c7e77b`, so no
history was replayed: `git log --oneline` at head is
`bba6bff, 73f2cb5, b6a8e9d, 7c7e77b, 94e5e00, …`).

Authority: `runs/2026-08-26-poker/design.md` **Addendum 3** (coordinator, phase 30 round 1), which
rules B1 and B2 valid and pins the new numbers, and **Addendum 4** (same phase), which nets one
worst-case decision off the hard guard. Where a pinned constant moved (`160 → 120`, `16 → 14`,
`0.60 → 0.56`), that is the ruling, not a loosened test.

The earlier green run on the two-commit head `73f2cb5` was
<https://github.com/Metta-AI/cogame-poker/actions/runs/32996855409> (also `success`, all three
jobs); every figure quoted below for B1 was re-confirmed on the final head — see "Evidence on the
final head" at the end.

| finding | disposition | commit | files |
|---|---|---|---|
| B2 [timeout] | fixed | `b6a8e9d1a65b7509c814ccd3d951e37f92b94f24` | `src/poker/sim.nim:21-32` (at that commit), `coworld_manifest_template.json:589,617` (+ ladder.md/audit.md doc values), `README.md:24`, `tests/test_sim.nim:834`, `tests/test_audit.nim:84,94,111` |
| B2 (Addendum 4 follow-up) | fixed | `bba6bffe83313b103f921346fe0d964cbb92725d` | `src/poker/sim.nim:27-36`, `coworld_manifest_template.json:451` (ladder.md) |
| B1 [legibility] | fixed | `73f2cb59bc53de73207e77074e5ef669da4f9dc2` | `src/poker/types.nim:11-15`, `client/renderer.js:130-138,662-720`, `tools/ci/fixtures/sixmax_audit.replay`, `tests/test_sim.nim:614-620`, `tests/test_bot.nim:137`, `coworld_manifest_template.json` (rules.md), `README.md:38,155`, `.github/workflows/ci.yml:419` |

---

## B2 — Settlement is bounded at 70 % of the episode timeout, not 60 %

**What the code did.** `src/poker/sim.nim:28-29` carried `PlayBudgetFraction = 0.60` /
`HardDeadlineFraction = 0.70`. `server.nim:252-253` anchors both at `gameStart`; the soft guard is
only evaluated at a duplicate-pair boundary (`server.nim:326-339`), so the guard that actually
stops a live hand is the hard one at `0.70·T` = **840 s** of 1200 — settle-and-score at ≈ 840 s =
**70 %**, past checklist item 5's 60 %.

**What it does now.** Per Addendum 3: `PlayBudgetFraction = 0.55` (soft guard at **660 s**, still
checked only at pair boundaries, so no duplicate pair is left half-played) and
`HardDeadlineFraction = 0.60` (hard guard at **720 s** — subsequently **0.56 / 672 s** under
Addendum 4, see the follow-up section below; still `voidLiveHand()` +
`endMatchEarly(erDeadline)`, so the abandoned hand is refunded in full and the nets still sum to
zero). `EpisodeDecisionBudget` stays 220 — 220 × 3.0 s = 660 s, now *exactly* the soft guard, and
the code comment says so. `holdem-6max` drops 16 → 14 hands (7 pairs, expected ≈ 546 s, ~114 s of
margin under the soft guard) in the manifest variant and its description, `README.md`'s rung
table, `ladder.md`'s budget paragraph, `audit.md`'s "a 14-hand episode's flags", and the two tests
that pin the shipped six-max size (`test_sim.nim`'s declared-hand-counts case,
`test_audit.nim`'s zero-false-positive and no-showdown-surrender cases).

**Why that resolves the finding.** The stop that fires on a live hand moved from 840 s to 720 s,
and then to 672 s with Addendum 4's netting, so the true worst-case settle is inside 60 % of the
platform's 1200 s. `handCap(holdem-6max)` is unchanged at 16, so 14 still fits the budget with
room, and `sampleEpisode` leaves it alone (even, ≥ `MinHands`).

**Evidence.** All six suites pass locally in debug *and* `-d:release`, including
`tests/test_sim.nim` "the declared variant hand counts all fit the budget" (now `(vHoldem, 6, 14)`)
and `tests/test_audit.nim` "honest scripted six-max episodes raise no flags at all" at 14 hands
(10 seeds × both baselines, `flagged.len == 0`, still ≥ 1 pair with `contested ≥ 4`). CI job
`test` on run 32996855409 runs every `tests/*.nim` twice and is green.

**Satisfies:** acceptance-checklist **item 5** ("the episode settles and scores inside 60 % of
`episodeTimeoutSeconds` (720 s of 1200)"), completed by the follow-up below.

### B2 follow-up — the hard guard nets off one worst-case decision

Commit `bba6bffe83313b103f921346fe0d964cbb92725d`, authority
`design.md` **Addendum 4** (coordinator ruling on the residual I recorded in the first version of
this file, reproduced under NOTED below).

**The residual.** The hard guard is checked *before* a decision (`server.nim:275`), so a decision
admitted at 719.9 s still runs to completion: `waitForSpacing` ≤ 2.1 s (`llm.nim:731-737`) + up to
two `curl.post` attempts at `llmTimeoutSeconds = 20` (`llm.nim:638`, retry loop `:755`) +
`turnDelayMs` + the ~0.5 s settle write (`server.nim:205`). With the guard at 0.60·T the *true*
worst-case settle was therefore ≈ 763 s (63.6 %), not 720 s.

**What it does now.** `HardDeadlineFraction 0.60 → 0.56` — the guard fires at **672 s**, and
672 s + one worst-case decision (≈ 45 s) = **717 s ≤ 720 s = 60 %** of 1200. `PlayBudgetFraction`
stays 0.55 (660 s, pair boundaries) and the guard's behaviour is unchanged: `voidLiveHand()` +
`endMatchEarly(erDeadline)`, so the abandoned hand is refunded in full and the nets still sum to
zero. The constant's comment (`src/poker/sim.nim:27-36`) spells the netting out, and `ladder.md`'s
budget paragraph now reads "the hard guard at 672 s (56 % of 1200 s) … nets off one worst-case
decision … which is what keeps the true worst-case settle inside 720 s, 60 % of the platform's
timeout". Nothing else moved: no test pins either fraction, and 14 hands at ≈ 546 s expected still
clears the unchanged 660 s soft guard.

**Evidence.** All six suites green locally in debug and `-d:release`; CI run 32997839855 (`test`,
`docker-smoke`, `wasm-viewer` all `success`) on head `bba6bff`, with `docker-smoke` logging
`smoke OK: seats=2 results=680B replay=16351B reason=complete`.

---

## B1 — A full-cap `say` does not fit the speech bubble

**What the code did.** `types.nim:11-12` capped `say` at 160 runes and *claimed* that was "what
the viewer's speech bubble can actually show (~4 wrapped lines)". The bubble was
`BUBBLE_MAX_W = 220, BUBBLE_LINES = 4` in a 13 px font (`client/renderer.js:130`), and
`drawBubble` hard-clipped at 4 lines and appended `…` (`:674-677`). The reviewed run's six-max
smoke reported `canvas_text.ellipsized = 537`, every sample the remark itself — a cut sentence,
which item 15 calls a defect.

**What it does now**, per Addendum 3 (both sides move until they agree):

1. **Server cap 160 → 120 runes** — `MaxSayLen` in `src/poker/types.nim`, whose comment now names
   the geometry it has to agree with. `llm.nim:582` (the prompt's "max N" line) and
   `llm.nim:665`/`sim.nim:648` (the two truncation sites) read the constant, so they moved with it.
   Prose that quoted the number moved too: `rules.md` in the manifest ("`say`, <= 120 runes"),
   `README.md:38`, `README.md:155` and the `ci.yml:419` comment describing the fixture, and the
   hostile-say test's title in `tests/test_bot.nim:137` (its assertions were already
   `runeLen == MaxSayLen`, so they now pin 120).
2. **Bubble geometry sized from that cap, measured in the drawing font** — `BUBBLE_MAX_W = 300`,
   `BUBBLE_LINES = 6` (`client/renderer.js:130-138`), with the arithmetic in a comment. Measured in
   headless chromium with the shipped `data/font.ttf` at 13 px 'rajdhani': the widest 120 runes the
   cap admits (all full-width CJK ≈ 1560 px, all playing-card emoji ≈ 1596 px) now wrap inside
   6 × 300 px; the fixture's mixed 120-rune remark uses **3 of the 6 lines** (widest line 286 px).
   `seatExtent` (`renderer.js:145-158`) is untouched and still reserves
   `bubbleHeight(BUBBLE_LINES) * scale` unconditionally, so the band is still reserved whether or
   not anyone is talking — it is simply 6 lines now, not 4, and the box provably cannot exceed it
   because `drawBubble` still clips at `BUBBLE_LINES`.
3. **`wrapBubble`** (`renderer.js:662-698`) replaces the inline whitespace-only wrap: a *word*
   wider than a whole line is split on rune (code point) boundaries. This is required by the wider
   box, not decoration — Chinese, Japanese and a wall of emoji carry no spaces at all, so the old
   wrap drew a spaceless 120-rune remark as one ~1600 px line running off the canvas
   (`never_inside`, the *gated* number). `drawBubble` also clamps its line width to the canvas
   (`Math.min(BUBBLE_MAX_W * s, canvasWidth - 12 - BUBBLE_PAD * 2 * s)`) so a 300 px box on a
   narrow embed shrinks instead of pushing its own text off the edge.
4. **Fixture regenerated** — `tools/ci/fixtures/sixmax_audit.replay` now carries an
   exactly-120-rune `say` on every one of the six seats. `fixtureSay`
   (`tests/test_sim.nim:614-620`) builds it with `$body.toRunes()[0 ..< MaxSayLen]` instead of
   `truncateRunes`: `truncateRunes` *itself* ends a capped string with `\u2026`, which the smoke
   would count as an ellipsized draw forever. A remark the server passed **whole** is the case the
   bubble must render whole, and it makes "zero ellipsized" a meaningful gate. The generator and
   the committed bytes stay in sync — `tests/test_sim.nim:862-885` rewrites the file and fails on
   drift, and it still asserts `runeLen == MaxSayLen` on every seat's say.

**Evidence — the number the finding was built on, on the pushed head.** CI run 32996855409, job
`wasm-viewer`, step "Load the six-max audit fixture in the same bundle":

```
canvas text: 26989 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
```

and the artifact `viewer-smoke-sixmax.json`:

```json
"canvas_text": {"total": 26989, "outside": 0, "ellipsized": 0, "never_inside": 0,
                "never_inside_samples": [], "distinct_capped": false, "samples": []}
```

**537 → 0.** No ellipsized sample remains, so there is nothing to classify as label-vs-remark. The
cert invocation is also clean (`8293 drawn, 0 never inside, 0 ellipsized`).

**Evidence — before pushing.** I reproduced the CI check locally rather than guessing: a stub
bundle (the shipped `client/renderer.js`, `chrome.css`, `data/*` assets and
`replay-viewer/index.html`, with the wasm module replaced by a payload generated from the fixture
by the *same* `statesFromEvents`/`auditFromEvents` code `replay-viewer/poker_replay.nim` calls),
driven by the repo's own `tools/ci/viewer_smoke.mjs` in headless chromium: `27081 drawn, 0 never
inside the canvas (0 draws crossed an edge), 0 ellipsized`. Screenshots at 1280 px and at **360 px**
(the `--hudscale` path) show the full 120-rune remark rendered in 3 wrapped lines inside the box at
every seat, nothing clipped. The same harness driving `drawBubble` directly at the three canvas
widths (1000/360/300 px) with six simultaneous speakers reports, for the fixture text, all-CJK,
all-emoji, a 120-character single word and an English sentence: `ell=0, offcanvas=0` in every
combination. All six Nim suites pass locally in debug and `-d:release`.

**Satisfies:** acceptance-checklist **item 15** — third bullet (no remark is ellipsized any more),
second bullet (the reserved band is sized from `MaxSayLen` *measured in the font it is drawn in*,
and is still reserved unconditionally), first bullet (`never_inside = 0` on both invocations with
`--strict-text-bounds` present), last bullet (the worst-case fixture still exists, still runs in
CI, and now carries a genuinely full-cap remark on every seat).

*On item 15's "widen the band, do not shorten the text":* the band **was** widened — 4 × 220 px →
6 × 300 px, a 1.9× capacity increase. The cap also moved 160 → 120 because Addendum 3 rules that
the two must be sized against each other and fixes the pair at those values; that is the
coordinator's design ruling, not the fixer choosing to shorten the text to dodge the finding.

---

## NOTED (not fixed)

- **~~The hard guard is checked *before* a decision, and a decision is not instantaneous.~~
  RESOLVED** — I recorded this as a residual rather than changing Addendum 3's pinned 720 s on my
  own authority; the coordinator issued **Addendum 4** and it is now fixed in commit `bba6bff`
  (see the B2 follow-up section). For the record, the residual as reported: with the guard at
  0.60·T it fires at 720 s, but a decision started at 719.9 s runs to completion —
  `waitForSpacing` ≤ 2.1 s plus up to two `curl.post` attempts at `llmTimeoutSeconds = 20`
  (`llm.nim:638,755`) plus `turnDelayMs` — so the true worst case was ≈ **763 s (63.6 %)** for
  settle-and-score, and ≈ 783 s to `quit(0)` after `ShutdownGraceSeconds = 20`. With the guard at
  0.56·T those become ≈ 717 s (59.8 %) and ≈ 737 s (61.4 % — the 20 s grace after the artifacts
  are written and scored, which item 5 does not bound).
- `tests/test_cards.nim:106-112` uses the literal `160` as an arbitrary `truncateRunes` cap in the
  generic truncation tests (alongside 2, 7, 16, 200). It does not pin `MaxSayLen`, so it was left
  alone.
- `audit.md`'s sentence "cleared the 2 bb bar on 3 of 30 honest **sixteen**-hand episodes" is a
  record of a measurement that was taken at 16 hands (Addendum 2). It is history, not the shipped
  size, so it was not rewritten; the shipped-size reference in the same page ("a 14-hand episode's
  flags") was.
- N1–N10 from the review were left untouched, as instructed.

---

## Evidence on the final head (`bba6bff`, CI run 32997839855)

Re-confirmed after the Addendum 4 follow-up, so nothing above rests on the intermediate head:

- `test`: every `tests/*.nim` twice (debug + `-d:release`) — `success`.
- `docker-smoke`: `smoke OK: seats=2 results=680B replay=16351B reason=complete`; no
  `SEAT-COUNT FAIL` in the log.
- `wasm-viewer`, cert replay: `canvas text: 8298 drawn, 0 never inside the canvas (0 draws crossed
  an edge), 0 ellipsized (--strict-text-bounds)`.
- `wasm-viewer`, six-max fixture: `canvas text: 27029 drawn, 0 never inside the canvas (0 draws
  crossed an edge), 0 ellipsized (--strict-text-bounds)` — artifact `viewer-smoke-sixmax.json`
  `"canvas_text": {"total": 27029, "outside": 0, "ellipsized": 0, "never_inside": 0,
  "never_inside_samples": [], "distinct_capped": false, "samples": []}`.
