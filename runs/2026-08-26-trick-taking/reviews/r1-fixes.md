# r1 fixes — trick-taking

Repo: `Metta-AI/cogame-trick-taking`, branch `main`
Head: **`179aa9993c4d1308b1a26945e1d758e63d16957f`**
CI: **run 33035205309** — <https://github.com/Metta-AI/cogame-trick-taking/actions/runs/33035205309>
— conclusion **success**; jobs `test` (98396320366), `docker-smoke` (98396320476),
`wasm-viewer` (98396519279) all **success**.
`grep -c "SEAT-COUNT FAIL"` over the whole `docker-smoke` log: **0**
(`smoke OK: seats=4 results=660B replay=11128B reason=complete`).

Two of the fifteen findings are **DISPUTED** (N7, N10) — the code and its
declared contract agree and the note's own text says so; evidence at
`file:line` below, no code changed. Everything else is committed, one commit
per finding.

Range reviewed by r1: `53ab652..80aeb68`. Range of this round's fixes:
`80aeb68..179aa99` (twelve commits).

| finding | disposition | commit | files |
|---|---|---|---|
| **B1** labels not hidden under 640 px | fixed | `a2c8e214` | `client/chrome.css:588-591`, `.github/workflows/ci.yml:365-369` |
| **B2** notes band not sized from the 400-rune cap | fixed | `004068a6` | `client/renderer.js` (`wrapLines`, `computeLayout`, `drawParchment`, `drawSeat`), `tools/ci/notes_fit_check.mjs`, `tools/ci/renderer_fixture.html:101`, `ci.yml:541` |
| **B3** no grid harness or tuning record | fixed | `49c52bcf` | `tools/ci/tune_baselines.nim`, `docs/tuning.md`, `src/tricks/llm.nim:166-186`, `tests/test_tuning.nim`, `ci.yml:158-162` |
| **N1** 429 backoff unbounded; `llmTimeoutSeconds` ≤ 300 | fixed | `ef9f42c5` | `src/tricks/llm.nim:39,140-150`, `src/tricks/server.nim:315-336`, `coworld_manifest_template.json`, `tests/test_bot.nim:138-158` |
| **N2** re-derivation not asserted frame by frame | fixed | `1810581a` | `tests/test_sim.nim:61-85,609-634` |
| **N3** `/client/replay` route exists | fixed (position + gate) | `c1f14b85` | `.github/workflows/ci.yml:376-388` (exact-equality check at `:383`) |
| **N4** `fit()` edited — a fourth, unlisted chrome patch | fixed | `85e609a1` | `client/replay.html:42-45`, `replay-viewer/index.html:44-47`, `client/player.html:34-37` (babel's two-line `fit()` restored verbatim) |
| **N5** note claims `viewer_smoke.mjs` asserts endcard geometry | fixed | `215b6ef8` | `tools/ci/chrome_geometry_check.mjs`, `ci.yml:471-483` |
| **N6** euchre up-card drawn twice after the pick-up | fixed | `550d80ec` | `src/tricks/euchre.nim:162-175`, `client/renderer.js:606-633`, `tests/test_sim.nim:304-346` |
| **N7** `frameStateJson` carries `kitty`/`discard` | **DISPUTED** | — | `design.md:397-399`, `design.md:693-697`, `src/tricks/sim.nim:709-735` |
| **N8** `bidsMade` description is wrong for spades | fixed | `3fe75100` | `coworld_manifest_template.json` (`results_schema.properties.bidsMade`) |
| **N9** hearts worst case 56/hand vs the note's 220 | fixed | `0733f5f7` | `src/tricks/hearts.nim:67-72`, `tests/test_sim.nim:729-755` |
| **N10** forced move increments `decisions[]` | **DISPUTED** | — | `coworld_manifest_template.json` (`results_schema.properties.decisions`), `src/tricks/server.nim:289-296` |
| **N11** game thread has no top-level guard | fixed | `c82c5677` | `src/tricks/server.nim:202` (`runEpisode`), `:373-399` (`runGame`) |
| **N12** `ellipsize` slices UTF-16 code units | fixed | `179aa999` | `client/renderer.js:111-127`, `tools/ci/renderer_fixture.html:77-83,101,103`, `tools/ci/notes_fit_check.mjs`, `ci.yml:535-541` |

Six of these commits (`a2c8e214`, `004068a6`, `49c52bcf`, `ef9f42c5`,
`215b6ef8`, `c1f14b85`) were landed by an earlier fixer session that died
before writing this file. I re-read each diff against the finding it names and
confirmed it resolves it; the verification is written out below with the same
evidence I would give for my own commits. Nothing in them was redone.

---

## B1 — the scorebug's labels are hidden under 400 px, not under 640 px
**fixed — `a2c8e214`** · checklist item **11** (*legibility*)

Before: the appended block in `client/chrome.css` carried exactly two media
queries, `720px` (hides `#feed`) and `400px` (font sizes plus
`.plate-label`/`.plate-pips`). Between 401 px and 640 px every plate still drew
`<span class="plate-label">points</span>` and up to 13 pips beside the name and
the score.

Now: a `@media (max-width: 640px)` block hides `.plate-label` and `.plate-pips`;
the two rules were **moved out** of the 400 px query (which keeps only the
`#wordmark`/`#clock`/`#modulechip` font-size overrides), so the decorations
come off at 640 px and everything narrower inherits it. The other half of item
11, `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`, was already met at
`client/chrome.css:447`.

Evidence: `.github/workflows/ci.yml:353-357` now greps `chrome.css` for a
`max-width: 640px` block containing `.plate-label { display: none }` and adds
the failure to the same `fail[]` list as the `.plate-name` rule, in the
`wasm-viewer` job's static-grep step — green in run 33035205309.

## B2 — the notes parchment ellipsizes the full-cap 400-rune `notes`
**fixed — `004068a6`** · checklist item **15** (*legibility*)

Before: `computeLayout` reserved `noteLines = h < 480 ? 1 : 2` and a parchment
`min(layout.w * 0.3, size * 3.2)` wide, neither derived from anything; a
full-cap 400-rune `notes` was cut mid-word by `wrapLines`. The r1 CI evidence
was 2 659 ellipsized draws on the hearts_moon fixture and 520 on the renderer
fixture, sampled mid-string.

Now: `computeLayout` takes the drawing context, measures the mean advance of a
representative alphabet in the note font, multiplies by `NOTES_CAP_RUNES = 400`
— the server's own `MaxNotesLen` — and derives the parchment width, the line
count (plus one line of word-wrap slack) and the band height from it. The band
is reserved whether or not a seat has written anything. `wrapLines` breaks an
over-wide single token on **rune** boundaries instead of ellipsizing it, and
`drawParchment` sets a glyph-heavy note a point smaller (floor 0.6×) rather
than shortening it.

Evidence: `tools/ci/notes_fit_check.mjs` is the gate the counter could not be.
`--strict-text-bounds` reports `ellipsized` but cannot tell a nameplate's
ellipsis from a sentence cut mid-word; this script reads the fixture's own
capped strings (`window.__FIXTURE_TEXT`) and fails if any drawn piece of them
ends in an ellipsis that is **not** that string's own tail. Run 33035205309,
`wasm-viewer`, step *The notes band fits the server's cap, and cuts are
rune-safe*:

```
  360x640: 4500 strings drawn, no mid-string cut
  960x640: 4216 strings drawn, no mid-string cut
  1440x900: 3960 strings drawn, no mid-string cut
notes fit OK: 515 capped-string ellipses, all of them the server's own cap
```

and the same run's *Load the bundle in a real browser*:
`canvas text: 41762 drawn, 0 never inside the canvas (0 draws crossed an edge),
0 ellipsized (--strict-text-bounds)`.

## B3 — no grid harness or tuning record for the scripted baselines
**fixed — `49c52bcf`** · checklist item **7**, second clause

Before: `orderAt`, `aloneAt` and the two winner formulas were bare literals in
`src/tricks/llm.nim` with no artifact anywhere in the tree — `grep -rniE
"grid|tune|harness|sweep"` returned three unrelated hits.

Now: the four free bid numbers are a `BaselineParams` record with
`baselineParams(baseline)` as the shipped configuration, and `scriptedMove`
takes an explicit params argument so a sweep can seat two configurations at one
table (the no-params overload is unchanged for every existing caller).
`tools/ci/tune_baselines.nim` is the harness: a candidate configuration bids
for one pair of table positions and the shipped one for the other, every deal
is played twice with the candidate on either pair and averaged — which is why
the self-play control row reads exactly `0.5000` — 46 grid points × 96 seeded
deals. `docs/tuning.md` is its committed output plus the noise band measured
over a second independent seed set (`--seed 4242`).

It is a **gate**, not just a record: it exits non-zero if any grid point beats
the shipped configuration by more than the tolerance, and `ci.yml:152-163` runs
it on every push. `tests/test_tuning.nim` pins the shipped constants to
`docs/tuning.md`'s table, re-runs the grid at 24 deals a point, and asserts
every point still plays legal complete matches.

Evidence: run 33035205309, `test` job, step *Baseline tuning sweep (grid
harness)* — `grid sweep: 96 seeded deals per point …`,
`best: orderAt=10 aloneAt=16 at 0.5000 (shipped: orderAt=10 aloneAt=16)`,
`best: spadesShade=0 at 0.5000 (shipped: spadesShade=0)`,
`best: ohHellDrop=0 at 0.5000 (shipped: ohHellDrop=0)`; plus
`tests/test_tuning.nim` run in both debug and `-d:release`.
The first clause of item 7 was already satisfied (`tests/test_bot.nim:88-103`,
1 600 complete episodes) and the reviewer verified it.

**See NOTED (1) below**: the sweep moved `tracker` off two numbers the design
note states.

## N1 — the post-guard settle bound is not derived from the deadline
**fixed — `ef9f42c5`** · checklist item **5** (*timeout*)

Before: `client.extraSpacingMs` grew by 500 ms on **every** HTTP 429 with no
ceiling, and `server.nim` read `pastSoft`/`pastHard` once per loop iteration
*inside* the lock and never again after the spacing sleep — so a throttle storm
could start a decision just under the soft guard, sleep tens of seconds, and
return past the hard one. `config_schema` also permitted `llmTimeoutSeconds` up
to 300, which no arithmetic in the server accounted for.

Now: `noteThrottled()` caps the backoff at `MaxExtraSpacingMs = 3000`, so the
spacing floor is at most 5.2 s. `worstCaseCallSeconds()` states the other bound
(one attempt plus the single retry). After the spacing sleep the server
**re-reads** the clock and refuses a decision unless its own worst case returns
before the hard deadline; a refused decision is scripted, which is exactly what
the soft guard does anyway. `llmTimeoutSeconds` is schema-capped at 60.

Evidence: `tests/test_bot.nim:138-158` — 500 consecutive `noteThrottled()`
calls leave `extraSpacingMs == MaxExtraSpacingMs`, `worstCaseCallSeconds()`
equals `2 × llmTimeoutSeconds`, and one whole decision (spacing at its ceiling
plus the call) is under 60 s. Run twice per run, debug and `-d:release`.

## N2 — the re-derivation test compares the log and the final frame only
**fixed — `1810581a`** · checklist item **2**

Before: `rederives()` asserted the event log, the results, `replayStates`
against itself, `frames.len == events.len + 1` and `frames[^1]`. Item 2's claim
is that replaying the events reproduces the recorded per-tick state **frame by
frame**, and nothing asserted the intermediate frames: a drift at a hand
boundary, a trick resolution or a score update that healed before the end would
have passed.

Now: `playRecording` plays an episode capturing the live per-tick state after
every applied move — the same `frameStateJson` the live server broadcasts and
discards (`server.nim:115-120`) — paired with the event-log length at that
instant, so each live tick has a well-defined re-derived counterpart
(`replayMatch(config, events)[n]` is the table after the first *n* events). The
new test round-trips the log through JSON, re-derives it, and compares every
one of those pairs, for all four modules.

Evidence, and non-vacuity: the test asserts the recording is longer than 30
ticks and that every pair was compared. I ran it with the frame index shifted
by one and it fails on the first hand of euchre (`"actor":2` vs `"actor":3`,
`"tell":""` vs `"tell":"No ordering hand in diamonds."`), so the comparison is
live. Run 33035205309, `test` job: `tests/test_sim.nim` green in both modes.
This is the frame-by-frame half of item 2; the "not from a parallel recording"
half was already true — the viewer's `payload.states` comes only from
`replayStates(config, events)` (`replay-viewer/trick_taking_replay.nim:36`,
`server.nim:531`).

## N3 — `GET /client/replay` and `client/replay.html` exist
**fixed (position recorded + declaration gated) — `c1f14b85`** · checklist item
**3** (*static-viewer*)

Position, stated plainly: the route stays, and here is why. It is babel's page
byte-for-byte, it is on the route list the design records the certifier
requiring (design.md:746-757), and it is a **live spectator view of a running
episode**, not a path anything can be pointed at for a recorded replay. The
failure item 3 exists to prevent — the platform hosting replays from a pod, so
every replay 404s once the pod is gone — is decided by the manifest and nowhere
else. Removing the route would depart from the starter chrome (item 14) and
from the documented certifier requirement, and the certifier cannot be run from
this sandbox to settle it either way (the r1 review lists this under *Could not
determine* for the same reason).

What the commit adds is the confirmation on the surface that decides it:
`ci.yml` now requires `game.replay_viewer` to equal
`{"bundle": "static-replay-viewer"}` **exactly**, so no `url`/`path`/`pod` key
can ever be added beside the bundle, and re-checks that no top-level
`replay_viewer` exists. The rest of item 3 was already verified by the reviewer
and holds: `tools/build_replay_viewer.sh` is the `coworld build` hook
(`coworld-release.yml:159-172`), and the bundle fetches nothing but its
`?replay=` URL.

## N4 — `fit()` was edited in all three pages
**fixed — `85e609a1`** · checklist item **14** (*static-viewer*, chrome
provenance)

Before: babel's two-line `fit()` had become a three-line version falling back
to the canvas's parent size and then to 960×640, in `client/replay.html`,
`replay-viewer/index.html` and `client/player.html`. The design note names
exactly three patches to the inherited chrome (design.md:879-896) and says of
the pages "**Removed from the starter's page: nothing**" and "**Appended:** one
`<div id="modulechip">` … and the `relayout()` bootstrap" (design.md:858-867).
This was a fourth, unrecorded edit, so the note's provenance claim was false.

Now: reverted to the starter's exact text in all three pages. The fallback
guarded nothing reachable here — the CSS above the game block's banner is
byte-identical to babel's, so `canvas#table` is a 100 %/100 % child of a
laid-out `#board-wrap` and `clientWidth`/`clientHeight` are non-zero when
`fit()` runs, which is why the same two lines are what babel ships.

Evidence: `diff` of each page against `/workspace/starters/cogame-babel` now
returns only the wordmark, the `<title>`, the `#modulechip` element under the
banner comment, the `BabelRenderer` → `TrickTakingRenderer` rename, and the
appended `relayout()` bootstrap — the exact list the note gives. In CI, run
33035205309: *Load the bundle in a real browser* `{"loaded":true,"ms":304,…}`
(`data-replay-loaded` is set only from a painted frame, and `draw` bails under
32 px, so a zero-sized canvas would be red here), and *Renderer fixture at
three canvas sizes* green at 360×640, 960×640 and 1440×900.

## N5 — the note says `viewer_smoke.mjs` asserts the endcard geometry
**fixed — `215b6ef8`** · checklist item **14(c)**

Before: design.md:908-910 claims `viewer_smoke.mjs` asserts `#endscreen`'s
rendered bottom is ≥ `#transport`'s rendered top. It does not, and it cannot be
made to — that file is byte-identical to the coworld-builder template and has
to stay that way (design.md:1223-1224). The structural guarantee was real but
nothing in the repo measured it.

Now: `tools/ci/chrome_geometry_check.mjs` measures it. It loads the built
static bundle in headless chromium, seeks to the end so the endcard is up, and
fails if `#endscreen` is not inside `#board-wrap`, if `#transport` reserves no
band, or if the endcard's bottom is below the band's top. An endcard that
covers the scrubber loads, soaks and screenshots exactly like a working one, so
this is the only gate that can see it.

Evidence: run 33035205309, `wasm-viewer`, step *The endcard never covers the
transport band* —
`endcard geometry OK: #endscreen bottom 729.0 <= #transport top 729.0 (shown by seek: true)`.
The commit message records that it was verified both ways: it passes on the
shipped chrome and fails when `#endscreen` is given `position: fixed`.

## N6 — the euchre kitty keeps the up-card after the dealer picks it up
**fixed — `550d80ec`** · advisory (spectator display)

Before: `euchreSetup` set `kitty = rest[0 ..< 4]` and `upcard = kitty[0]`. When
a seat ordered it up, `euchreApply` added `sim.upcard` to the dealer's hand and
set `upcardLive = false` but left the card in `sim.kitty`, so `frameStateJson`
shipped a four-card kitty containing a card that was also in the dealer's hand.
`drawTableFurniture` drew `kitty.length - 1` backs plus the up-card's **face**
in the corner while `drawFan` drew the same card in the dealer's fan: one card
on the board twice.

Now:
- `src/tricks/euchre.nim` — the pick-up removes the card from the kitty.
  `sim.upcard` keeps its value: it is the record of *which* card was turned up,
  read by the prompts (`llm.nim:738`, `:779`), the round-1 tells
  (`euchre.nim:79`, `:84`) and the `hand` event. `upcardLive` and the kitty are
  what say whether it is still on the table.
- `client/renderer.js` — the corner shows the up-card **face** only while the
  card is still in the kitty, and whatever is left of the kitty face-down
  beside it. A turned-down up-card (round 2, all four passed) is still in the
  kitty and still shown; after a pick-up the corner reads `KITTY` over three
  backs.

Re-derivation is unaffected: `beginHandFrom` seeds the kitty from the recorded
`hand` event, which is written at deal time (`sim.nim:210-211`), and
`sim.upcard == event.upcard` still holds (`sim.nim:289`).

Evidence: two new tests in `tests/test_sim.nim` — after an `order`, the card is
in the dealer's hand, out of the kitty, `upcardLive` is false, `upcard` is
unchanged, and all 24 cards are in exactly one place; after four passes the
up-card is still in a four-card kitty. Both green in debug and `-d:release`,
and the N2 frame-by-frame test re-derives the whole euchre timeline including
the mutated kitty.

## N7 — `frameStateJson` carries `kitty` and `discard`
**DISPUTED — no code change**

The two fields are there (`src/tricks/sim.nim:769-772`) and the note's sample
object does not list them. But the sample is not the exhaustive field list the
finding treats it as, and the note requires both fields elsewhere:

1. **The sample is abbreviated on its face.** design.md:693-697 shows
   `"seats": [{…}]` — a **single** seat object — where the engine always emits
   four (`sim.nim:709-735`, `for slot in 0 ..< Seats`), and `"table"` with two
   entries mid-trick. A reader cannot take "exactly this object" literally for
   `seats` and not for the two fields beside it.
2. **The note mandates them.** design.md:397-399, §The game 12: "**Spectators**
   (`/global`, the replay, the static viewer) see **everything**: all four
   hands, **the kitty, the discard**, every pass, every note, the tells and the
   audit. That is the idea's 'all hands visible' replay plan." Removing `kitty`
   and `discard` from the one state object all three spectator views read would
   make that sentence false and would take the kitty off the felt.
3. The manifest's `game.protocols.global` documents both, and
   `playerStateJson` deletes both for every seat (`server.nim:105-107`), so
   nothing leaks to a player.

`discard` being unread by `renderer.js` is true and is not a defect:
`/global` is a documented spectator protocol, not only a feed for this
renderer.

## N8 — `bidsMade` for spades counts "at least the bid"
**fixed — `3fe75100`** · advisory

The finding is right and it is the description that was wrong, so the
description changed and no code did. `results_schema.properties.bidsMade`
read "Hands in which the slot made its bid **exactly** (or a made nil)", but
spades increments on `tricksWon >= bids and bids > 0` (`spades.nim:134-138`)
because making a spades contract **is** `≥` by the rules, while oh-hell
increments only on `tricksWon == bids` (`ohhell.nim:128-130`) because bidding
exactly is the whole game there. The description now states the rule per module
and says the field is 0 in euchre and hearts, which bid no trick count.

Evidence: `tests/test_manifest.nim` green in both modes at the new head;
`reason` — the only enum item 10 gates — is untouched and still
`["complete","deadline","budget"]`.

## N9 — hearts' `worstCaseDecisions` is a flat 56/hand
**fixed — `0733f5f7`** · advisory

Before: `heartsWorstCase` returned 56 for every hand, so a four-hand episode
was charged 224. The design note's table (design.md:515) computes
56 + 56 + 56 + 52 = **220**, because every fourth hearts hand is "hold" —
nothing is passed, so no pass decision is spent.

Now: `heartsWorstCase` reads `passDirName(hand)`, the same proc that decides
whether a pass phase runs at all, and charges 52 on a hold hand. The four
shipped variants' worst cases are now exactly the note's numbers.
`sampleEpisode` is unaffected: it sizes from hand 0, a passing hand in every
module (`sim.nim:103`).

Evidence: `tests/test_sim.nim` now pins all four counts to the note's literals
— euchre **232**, spades **224**, hearts **220**, oh-hell **188** — alongside
the existing `≤ 240` and `≤ 660 s` assertions, and a second test checks the
per-hand rule against `passDirName` for all four hearts hands. That is a
tightening of an existing test, not a loosening: the three deleted lines are
the old `Shipped` tuple that carried no expected count.

## N10 — the auto-applied forced move increments `decisions[]`
**DISPUTED — no code change**

The behaviour is real (`server.nim:289-296`) and it is what the repo declares.

- design.md:224's "(a forced move, **no decision spent**)" is about the
  **model-call budget**, and that is exactly what the code does: the forced
  move is applied without touching `modelCalls`, so `EpisodeDecisionBudget`
  (240) is untouched, no LLM call is made, no `fallbacks[]` or `forcedMoves[]`
  is incremented, and no spacing is owed. The reviewer verified this and so did
  I.
- `results_schema.properties.decisions.description` in
  `coworld_manifest_template.json` already reads **"Decisions the slot was
  asked for, including forced and scripted ones."** The published contract for
  the field says precisely what the code counts, so there is nothing to
  reconcile — and changing the counter would make the manifest wrong.
- No checklist item bears on `decisions[]`.

## N11 — the game thread has no top-level exception guard
**fixed — `c82c5677`** · checklist item **5** (*hang*)

The reviewer traced the two unguarded raise sites (`beginHand` at `:277`, the
fallback apply at `:348`) and found neither reachable; so did I —
`beginHand` raises only on a wrong phase or a short remainder, both ruled out
by `validate` (`sim.nim:108-128`), and `baselineDecision` probes its own move
and falls back to `lowestLegal`, which cannot be empty in a decision phase.
That is an argument, not a guarantee, and the failure it stands in for is
silent: a dead game thread writes no `results.json` and no replay, sends no
`final` frame, and leaves `/healthz` answering until the platform kills the pod
— "degrade, never hang" as read from the outside.

Now: the episode body is `runEpisode` and `runGame` wraps it in
`try/except CatchableError`. On an exception the error is logged, the sim is
settled with `endEarly("deadline")` (inside the declared `reason` enum; hands
already scored keep their scores), the last state is broadcast, and
`finishEpisode` runs so the artifacts exist. `finishEpisode` is idempotent via
`state.finished` (`server.nim:146-149`), so a failure inside it does not
double-write. **No behaviour changes on the path that does not raise.**

Evidence: the whole `docker-smoke` job is the exercise of the non-raising path
— run 33035205309 built the production image and ran one real four-seat episode
with no `ANTHROPIC_API_KEY`: `smoke OK: seats=4 results=660B replay=11128B
reason=complete`, every container exit 0. I did not add a unit test: the guard
takes a thread-level exception that no reachable input produces, and a test
that forces one would have to stub the thread body rather than the condition.

## N12 — `client/renderer.js`'s `ellipsize` slices UTF-16 code units
**fixed — `179aa999`** · advisory (bears on item 9's discipline)

Before: `cut = cut.slice(0, -1)` removes one UTF-16 **code unit**, so trimming
an astral character — a model is free to put an emoji or a playing-card glyph
in its `notes` — leaves a lone high surrogate and the canvas draws a
replacement glyph.

Now: `ellipsize` pops runes off `Array.from(text)`. Output is identical for
every BMP string, which is everything the fixtures and every CI-producible
replay contain. `tools/ci/renderer_fixture.html` gives one alias U+1F0A1 so an
astral rune reaches the canvas at all three sizes, and
`tools/ci/notes_fit_check.mjs` fails if **any** drawn string carries a lone
surrogate, and fails if the astral rune was never drawn so the check cannot go
vacuous.

Evidence, and its honest limit: I verified the new gate fires — replacing the
fixture's astral rune with its high half alone turns the step red with
`::error:: 34 draw(s): "Ratchet\ud83c"` at all three sizes. But I also
instrumented `fillText` and read every drawn string at 360×640, 280×480,
240×360 and 200×320: in the shipped fixture `ellipsize` never truncates that
alias, so the gate is a **regression net over every drawn string** rather than
a reproduction of the old defect. The defect itself follows from the code:
`"x\uD83C\uDCA1".slice(0, -1)` is `"x\uD83C"`. Item 9 proper — every string
that reaches the **replay** — was and is satisfied server-side by
`truncateRunes` (`src/tricks/types.nim:204-212`), asserted in
`tests/test_sim.nim` and `tests/test_bot.nim`.

---

## Acceptance-checklist mapping

| item | finding(s) that touched it | state at `179aa99` |
|---|---|---|
| 1 CI green, no test loosened | — | run 33035205309 `success`; `git diff 80aeb68..179aa99 -- tests/` deletes exactly 3 lines, the old `Shipped` tuple that N9 replaced with one carrying expected counts. 216 test lines added across five commits (`49c52bcf` +80, `ef9f42c5` +21, `1810581a` +53, `550d80ec` +45, `0733f5f7` +17/−3), 0 assertions removed, no skip/xfail anywhere. |
| 2 replay re-derivation frame by frame | **N2** | satisfied |
| 3 static viewer, no pod path | **N3** | manifest declaration gated to exact equality; route position recorded |
| 4 both name spaces | — | already satisfied (reviewer verified) |
| 5 degrade-never-hang / 60 % settle | **N1**, **N11** | satisfied |
| 6 `num_agents` everywhere | — | `SEAT-COUNT FAIL` count 0 in the docker-smoke log |
| 7 scripted baseline legal + tuned | **B3** | satisfied, harness is a gate |
| 8 LLM reply handling | — | already satisfied |
| 9 rune-safe truncation | **N12** (viewer side) | satisfied server-side and now viewer-side |
| 10 manifest validates | **N8** | satisfied |
| 11 legible at 360 px | **B1** | satisfied |
| 12 release order and scaffold | — | already satisfied |
| 13 viewer executes | — | `wasm-viewer` `needs: docker-smoke`, smoke step ran, `loaded:true` |
| 14 chrome is the starter's | **N4**, **N5** | three named patches only; endcard geometry now measured |
| 15 every drawn string fits | **B2** | `never_inside: 0`, no mid-string cut at three sizes |

## NOTED (not fixed) — outside this round's findings

1. **`tracker`'s bidding no longer matches the design note.** B3's sweep moved
   `tracker` from `orderAt 12 / aloneAt 18 / spadesShade 1` to
   `10 / 16 / 0`, which makes its euchre and spades **bids** identical to
   `follow`'s; the four `tracker` overrides the note lists (design.md:586-588)
   are now three — the void table, the certain-winner lead, the bag avoidance
   and `ohHellDrop = 2`. `docs/tuning.md` records the change and the numbers
   that forced it (ordering up at 12 costs −0.015 to −0.035; shading the spades
   bid by one costs −0.036 and drops the win rate from 50 % to 17 %), so the
   repo is internally consistent and the harness would go red if the note's
   values were restored. The **design note** was not updated, because this
   round may not edit it. Someone should decide which document moves.
2. **`client/player.html` drops babel's `attachLive` call** and replaces it with
   a static description block. It is documented inline (lantern 0.1.1: a page
   that opened the player socket would occupy the slot the real player
   container needs) but it is not among the note's three named patches, and it
   is the same class of finding as N4. It was not in the r1 review, so I left
   it alone.
3. **`viewer_smoke.mjs` reports `distinct_capped: false`** on the renderer
   fixture (`dist/renderer-smoke/viewer-smoke.json`). Expected — the fixture is
   a single synthetic frame, not a scrubbable replay — but a judge reading the
   artifact should not take it for a failure.
