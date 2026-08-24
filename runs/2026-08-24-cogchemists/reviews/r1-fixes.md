# r1 fixes — cogchemists

Head: `11aa1a1d819fdef2ddf110c0694818b0a3be17d8` (main)
CI: https://github.com/Metta-AI/cogame-cogchemists/actions/runs/32705845919 — **success**
(`test` success, `docker-smoke` success, `wasm-viewer` success including "Load the bundle in a real
browser": `{"loaded":true,"ms":277,…}`; `SEAT-COUNT FAIL` occurs 0 times in the full log; 142 `[OK]`
lines across the five test files × debug and `-d:release`).

Commits are one per finding, pushed in order through the GitHub Git Data API (plain `git push` has no
write credential in this sandbox); the pushed tree at head is byte-identical to the local tree
(`336a6f2c00ea4fa1fecd9797efc727b157f6e881` both sides), and the local checkout at
`/workspace/build/cogchemists` has been reset onto the pushed history, so the shas in the table are
the ones in `git log` on both sides.

| finding | disposition | commit (pushed) | files |
|---|---|---|---|
| B1 | fixed | `e916f30` | `src/cogchemists/llm.nim:735-800`, `src/cogchemists/server.nim:302-321`, `tests/test_bot.nim:133-206` |
| N1 | fixed | `2e48a55` | `src/cogchemists/llm.nim:650-720`, `tests/test_bot.nim:289-300` |
| N2 | fixed | `10cffb4` | `tools/ci/docker_smoke.sh:309-316` |
| N3 | fixed | `11aa1a1` | `src/cogchemists/chem.nim:283-318`, `tests/test_chem.nim:192-245` |
| N4 | REFUTED (no change) | — | `src/cogchemists/sim.nim:725-763` |
| N5 | fixed | `7184ee2` | `client/renderer.js:216`, `:513-576` (drawBoard + drawTruthRow), `:641-650` (drawSeal verdict tags) |
| N6 | fixed | `a5a7191` | `src/cogchemists/llm.nim:434-451` |
| N7 | REFUTED (no change) | — | `client/renderer.js:1482`, `:1496`; `tests/test_viewer.nim:130-142` |
| N8 | fixed | `f38bd37` | `tests/test_sim.nim:288-293`, `:419-442` |
| N9 | fixed | `ac6a1c1` | `tests/test_sim.nim:577-601` |
| N10 | fixed | `fe91cb5` | `tests/test_sim.nim:628-681` |
| N11 | REFUTED (no change) | — | `tests/test_chem.nim:9-10`; `.github/workflows/ci.yml:132-148` |
| N12 | REFUTED (no change) | — | `src/cogchemists/server.nim:286-296` |
| N13 | REFUTED (no change) | — | `src/cogchemists/sim.nim:995-1000`; note §Per-seat observation item 6 |

---

## B1 — an LLM decision that falls back to the scripted move was recorded `scripted: false`

**Was.** `decideAll` returned `seq[Action]` only. The server therefore computed the recorded flag from
what it knew *before* the batch: `let wasScripted = scripted[seat] != skNone or client.disabled`
(old `server.nim:316`). A seat on a working client whose reply failed twice (transport, parse, or a
probe rejection) took `scriptedAction(sim, seat, skAssayer)` inside `decideAll` and was recorded
`scripted: false`, indistinguishable from a real decision — phase 60's check 4 would read 0 fallbacks
on an episode where all four seats fell back.

**Is.** `decideAll` takes `fromScript: var seq[bool]`, indexed by position in `seats`, set `true` in
exactly the three places an action comes from the baseline: a configured scripted seat, a disabled
client (`llm.nim:754-761`), and the post-retry fallback loop (`llm.nim:795-799`). The server records
that flag verbatim (`server.nim:305-321`); there is no longer an independent computation that can
disagree, and `applyAct` → `event.scripted` → `eventToJson` carries it into the replay unchanged.

**Evidence.** New test `tests/test_bot.nim` "a seat whose reply fails twice is recorded as scripted"
builds a *live* (`client.disabled == false`) Bedrock client pointed at `http://127.0.0.1:1`, so both
attempts fail with a transport error and every seat falls back; it asserts
`fromScript == @[true, true, true, true]`, that each action is in `legalMoves`, and that every
recorded `evAct` carries `scripted == true`. The disabled-client test asserts the same recording. Both
ran green in CI (run 32705845919, `test` job, debug and release passes:
`[OK] a seat whose reply fails twice is recorded as scripted`).

**Checklist item 8** — "…then falls back to the scripted move — and the fallback is recorded so phase
60 can count it." Design note §Degrade, never hang: "recorded with `scripted: true`".

## N1 — error text quoted into the log was sliced on bytes

**Was.** Five byte slices of server-supplied bodies and model replies (`head[0 ..< 160]`,
`response.body[0 .. min(high, 400)]`, two 300-byte cuts, and the `max_tokens` head) fed
`CogchemistsError` messages that are echoed at `llm.nim:790-791` and `server.nim:329`. A multi-byte
character across the cut leaves invalid UTF-8 on stdout.

**Is.** All five go through `cleanText(text, limit)` — the same rune-safe helper (`runeSubStr`) the
reply fields already use. No behaviour change other than the cut boundary and the `…` marker.

**Evidence.** New test "error text quoted into the log is cut on a rune boundary" feeds
`extractJsonObject` 400 multi-byte runes and asserts `validateUtf8() == -1` on the captured message.
CI: `[OK] error text quoted into the log is cut on a rune boundary`, both modes.

**Checklist item 9** (the log half; the reviewer's trace that no LLM error text reaches an event still
holds — nothing about the event path changed).

## N2 — `docker_smoke.sh` printed the end reason but did not assert it

**Was.** `reason = results.get("reason") …; if reason is not None: print(...)` and nothing else, so a
smoke episode settling `deadline` would still print `smoke OK`.

**Is.** `if reason != "complete": raise SystemExit(f"results.reason is {reason!r}, expected
'complete'")`, immediately after the print, with a comment naming why the offline path must reach the
exhibition.

**Evidence.** CI `docker-smoke`, step "Raw-Docker episode smoke":
`episode end reason: complete` / `smoke OK: seats=4 results=281B replay=10742B reason=complete` — the
assertion is now on the path that produced that line. Design note test 25. **Checklist item 7.**

## N3 — the baselines' "guarantees" were claimed over a truncated sample

Kept as a finding rather than a builder decision, because the note's word is *guaranteed*, not
*likely*: §Scripted baselines pins "(b) … a reagent `y` whose demonstration is **guaranteed** to
expose it", "(c) … a pair **guaranteed** to produce this round's demand", and "(1) … `test_self` when
the pair's worst case **cannot** be a negative potion". `consistentSample` stops at
`BotSampleCap = 3000`, so early in an episode those three predicates were evaluated over a *prefix* of
the surviving set and could certify something a chemistry outside the prefix breaks — a failed debunk
(−2 reputation), a sell miss, a poisoning.

**Is.** `truncated(sample)` (`chem.nim:283-288`) is true when the sample sits on the cap, and the
three guarantee predicates answer conservatively then: `certainPotion` → `poNone`, `alwaysExposes` →
`false`, `canBeNegative` → `true`. `largestBucket` is left sampled **deliberately**: it *ranks*
experiments rather than certifying one, and the note's own reason for the cap (a bot decision runs 4×
per phase inside the episode clock) applies to it. The grid — which is what `publish` and the
prompt use — was and remains the exact 40 320-bijection solve.

**Evidence.** Behaviour is unchanged on every seed the baseline test measures: assayer means
11.9 / 10.95 / 10.95 / 10.6 before and after, quack 3.85 / 6.3 / 6.3 / 4.85 (test_bot echo lines,
identical in both runs), so no tuning drift. New test "a truncated sample certifies nothing, a full
one matches brute force": the wide sample refuses all three guarantees, and on a fact set small enough
to enumerate, all three predicates equal an independent lexicographic enumeration for all 28 pairs ×
8 claims. CI: `[OK] a truncated sample certifies nothing, a full one matches brute force`, both modes.

## N4 — `applyAct` does not advance the phase; a separate step machine does — REFUTED as a defect

The note's line is the API sketch `applyAct(…)` "(… the last act of a phase advances the phase, the
last phase of the last round runs `exhibition()` then `settle("complete")`)". What that sentence
constrains observably is the **event stream**, and the code produces exactly the note's stream:
`start, round, phase, act×4, phase, act×4, …, exhibition, end`, asserted at `tests/test_sim.nim` (the
opening-events test and the endings test). The split exists for a reason recorded in the code
(`sim.nim:734-736`): `advance` emits **exactly one** structural event per call so every recorded event
gets its own spectator frame — which is what checklist item 2 (frame-by-frame re-derivation) needs,
and what `replayMatch`'s `frames.len == events.len + 1` depends on. Folding the advance back into
`applyAct` would merge an act frame with the following phase/exhibition/end frame and break that
invariant. No checklist item is falsified; changing it would be a design change for a wording
difference, so the code stands.

Sub-observation, confirmed and left alone: `stExhibition` (`sim.nim:72`, branch at `:757-759`) is
unreachable — `stActing` calls `runExhibition` directly at `:755`, and `grep` finds no other
reference. It is a dead branch in the step vocabulary, not a behaviour, and deleting it is outside
this round's findings. Recorded under NOTED below.

## N5 — the canvas endcard had no per-seal verdict and no truth row

**Was.** At the exhibition frame only the hole-cam cells resolved to the true signature
(`renderer.js:690-698` at the reviewed sha). `drawSeal` took no verdict and drew no tag; no truth row
existed anywhere. The verdicts appeared only in the feed and the endscreen table.

**Is.** `drawBoard` computes `revealed = view.chemistry.length === 8` and, for each **standing** seal,
`verdict = chemistry[seal.ingredient] === seal.claim`; `drawSeal` tags it amber `TRUE +5` or red
`FALSE −6` (burned seals keep `BURNED BY …` — they settled at the burn and are not re-scored).
`drawTruthRow` draws the eight true signatures once, large, in a row under the board, and `drawBoard`
reserves that band from the seal layout so no seal is covered. Both are gated on the same
`chemistry.length === 8` the grid strip already used, so nothing leaks mid-episode.

**Evidence.** A local harness drove the real `draw()` through a stub 2D context on an exhibition frame
carrying one true seal, one false seal and one burned seal: `TRUE +5` drawn, `FALSE −6` drawn,
`BURNED BY` drawn, eight signature strings in the truth row; at 360×640 the tags and all eight row
entries still render; on the same frame with `chemistry: []` no verdict tag is drawn at all. CI
`wasm-viewer` "Load the bundle in a real browser" is green on the pushed head with
`{"loaded":true,"ms":277,…}` and `data-replay-error` never set — the bundle ships this renderer and
the 47-event smoke replay plays through the exhibition frame during the 15 s soak. Design note §The
stage — "The endcard reveal". No checklist item covers stage decoration; item 13 (viewer executes)
stays green.

## N6 — the system prompt omitted the Press's royalty doubling

**Was.** `publish` named "+3 with the Printing Press" but the royalty line said "+1 coin every round
open" with no Press variant, and `buy mortar (-4 coin) or buy press (-5 coin), once each.` stated no
effect at all — a seat could not price either artifact.

**Is.** The royalty line reads "+1 coin every round open (+2 with the Printing Press)", and the buy
line now states both effects (the Mortar sparing the second card, the Press paying +3 and doubling
royalties to 2 coin a round). Prompt text only; the rule was already implemented
(`sim.nim:202-206`, `PressRoyaltyCoin`). Design note §MARKET menu and §Prompts ("every cost and
reward").

**Evidence.** `tests/test_sim.nim`'s observation-split test rebuilds the prompt for every seat on every
phase and still passes (no hidden value entered the text); CI green both modes.

## N7 — the two bootstrap variable renames — REFUTED

The renames are *required* by the note's own naming guard. `client/renderer.js` declares `var scheme`
at `:1482` and `var socket` at `:1496`; `tests/test_viewer.nim:54-67` collects every `function`/`var`
name renderer.js declares **at any depth** and `:141-142` asserts no page-level name collides with any
of them. Keeping the starter's `var scheme` / `var socket` in `replay.html` would fail that test — it
is exactly the shadowing the tandem 2026-08-23 rule forbids. The note's actual constraint,
"**Elements removed: none**", holds: `diff` against the starter shows only the title, the wordmark,
the `#clock` text, the appended `#labbar`, the `relayout()`/`buildLabBar()` bootstrap that §Transport
rules sanctions, the `labbar:` option, and these two renames — no removal, every starter id present.
No change made.

## N8 — two sub-assertions of note tests 10 and 12

**Added** (tests only, no production change):
- the endorse test now asserts a **burned** seal answers `no_such_theory` for the previous endorser
  and for a fresh seat (`sealIndex` filters on standing, `sim.nim:301-306`);
- a new same-phase-conflicts case endorses a seal in one round's market and again in the next, and
  asserts the **recorded event** carries `result: "rejected:already_endorsed"`, `action: "endorse"`,
  the +1 pass stipend, and an unchanged endorser list — the rejection shape note test 12 asks for,
  which previously existed only for `publish` and the burned-seal `debunk`.

**Evidence.** CI: `[OK] a second endorse of the same seal is a recorded rejection`,
`[OK] endorse moves a coin to the author and never repeats`, both modes.

## N9 — test 16's "no signature the seat's own facts do not imply"

**Added.** The observation-split test now recomputes `solveGrid(sim.knownFacts(seat))` independently of
the sim's memoised grid and asserts, per ingredient: the frame's `you.grid[x]` length equals that exact
solve, the sim's grid candidates equal it, the true signature is still among the candidates, and an
ingredient the seat's facts do **not** pin is never printed in the prompt with a single candidate.
That is the clause stated positively — every signature-to-ingredient binding the seat is shown is
exactly what its own facts imply, and the truth is singled out only where the facts single it out.

**Evidence.** CI: `[OK] no rival's private world reaches a seat's frame or its prompt`, both modes.

## N10 — replay grid equality was asserted for the final frame only

**Was.** `frames[^1]` only — and the test's episode was all `forage`/`pass`, so **no fact was ever
minted** and all four grids stayed wide open at 40 320 for the whole episode: even the final
comparison could not have caught a divergence.

**Is.** The episode plays `test_self` in the lab and `sell` in the market, so public `mixSign` /
`mixFull` facts land and the four grids diverge; the driver records the live grids after every single
event (with a `doAssert` that each step emits exactly one event, so index k really is "after k
events"), and the test compares **all four grids on every frame** against that recording, plus a
non-vacuity check that the grids actually narrowed and a final check that the last frame still matches
the live sim. `frames.len == events.len + 1` and the final `tableStateJson` equality are kept.

**Evidence.** CI: `[OK] the timeline re-derives frame for frame`, both modes. **Checklist item 2.**

## N11 — the performance budgets hold only under `-d:release` — REFUTED

The note's wording is "under 25 ms **native**" and the memoised refresh "under 400 ms"; `-d:release`
*is* the native build. `ci.yml:132-148` runs every `tests/*.nim` in both modes on every push, so the
25/400 ms bound is exercised on every commit — the debug constants only stop an unoptimised build
(≈10× slower: this sandbox measured 24 ms release-equivalent vs 1367 ms debug for the 80-refresh loop)
from failing a budget the note never applied to it. Loosening or removing the release bound would be
weakening a test; leaving a debug-only tolerance is not. The "84 vs 80 recomputes" difference is the
note's own upper bound (`4 × 2 × 10 + 4`) against the exact count the test loops (`2 × MaxRounds ×
Seats = 80`); 80 ≤ 84 and the note's ceiling is not falsified. No change made.

## N12 — the deadline is tested once per phase, not before the retry batch — REFUTED

The note says both things and the code implements the operative one: §End conditions —
"checked **before every LLM batch, i.e. only ever between phases**". `server.nim:286-296` tests it
immediately before `decideAll`, i.e. between phases, exactly as that sentence reads. The bound the
checklist actually constrains (item 5, settle inside 60 % of `episodeTimeoutSeconds`) holds with the
retry batch inside a phase: worst case one phase = spacing floor 10 s + 20 s + 20 s ≈ 50 s of overshoot
against ≈57 s of headroom in the note's own ceiling arithmetic (663 s vs 720 s) and ≈480 s on a
typical hosted episode; every wait in that path is explicitly bounded (`llm.nim` timeout,
`awaitBatchSlot`, `endEarly`). Threading a deadline into `decideAll` would change the decision API for
no bound that is not already met. No change made.

## N13 — `observationJson` carries `you.facts` — REFUTED

The note requires it. §Per-seat observation, item 6: "**Its own facts**: every `mixFull` it holds
privately, as a table" — that is the normative list ("Visible to seat `s` (its whole world; nothing
else reaches its prompt)"). §Player protocol's one-line frame sketch abbreviates it. The shipped
protocol description agrees with the code: `coworld_manifest_template.json`'s
`game.protocols.player` documents `"you":{…,grid[…],chemistries,facts[],notes}`. Removing `facts`
would delete an item the note names and desynchronise the code from the manifest. No change made.

---

## NOTED (not fixed)

- `stExhibition` (`sim.nim:72`, branch `:757-759`) is unreachable dead code in the step vocabulary
  (observed under N4). Not a finding of its own this round; deleting it touches the enum every
  `advance` branch switches on, so it is left for a round that scopes it.
- `BotSampleCap`'s doc comment (`chem.nim:258-262`) still describes only the ranking use of the
  sample; the new `truncated` doc carries the guarantee rule. Cosmetic, left alone.
