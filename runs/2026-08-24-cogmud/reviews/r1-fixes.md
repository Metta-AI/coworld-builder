# r1 fixes — cogmud

Repo: `Metta-AI/cogame-cogmud`, branch `main`.
Head: **`575c86bccd842d656a32fbc27039f51e4032167f`** (17 commits, one per finding, on top of
the reviewed `dd6f018d`).
CI: <https://github.com/Metta-AI/cogame-cogmud/actions/runs/32690212886> — **success**
(`test` success, `docker-smoke` success, `wasm-viewer` success, including
`Load the bundle in a real browser`). `grep -c "SEAT-COUNT FAIL"` over the whole run log:
**0**.

Every commit was pushed through the Git Data API (`gh api` blobs → tree → commit → PATCH ref),
because HTTPS `git push` in this sandbox is rejected with "No anonymous write access"; file
modes are preserved (`tools/build_replay_viewer.sh` and `tools/ci/docker_smoke.sh` are still
`100755`, asserted by `ci.yml` before either is invoked).

The whole suite was run locally, debug **and** `-d:release`, before every push
(nimby 0.1.26 / Nim 2.2.4, the pins `ci.yml` uses). No test was weakened, skipped or deleted:
every test change in this round either replaces an assertion that could not fail with one that
can (F7, F8), or adds assertions (F1, F2, F3, F5, F6, F9, F11, F12, F13, F16, F17).

| finding | commit | what changed |
|---|---|---|
| F1 (blocking) | `dfb740a` | grid harness `tests/test_tuning.nim` + committed surface `docs/tuning/baseline-grid.md`; the five thresholds become `BaselineParams`/`TunedParams` |
| F2 | `27fb13e` | `tableStateJson` emits `recentRobbed`; the ROBBED chip renders |
| F3 | `4135e22` | the amber employer↔hireling tether is drawn |
| F4 | `ec805ce` | an `iSay` act records the lifted spoken line in `say`, so salience reaches 30 |
| F5 | `8a0b41f` | the unreachable `npc >= 0 → 25` salience branch removed |
| F6 | `f3bfe9f` | the chart reads the payload's per-frame score and the world's `guild`/`pointsPerUnit` |
| F7 | `f8d1ea4` | the tautological observation-split assertion replaced with a structural one |
| F8 | `7e34493` | the restock test asserts the `expected` array it computes |
| F9 | `e8eca8b` | new suite drives a case for all 25 reachable outcomes; `oRejected` asserted absent, with the reason |
| F10 | `e55af65` | `rules.md` states the turn-0 restock exemption; manifest regenerated |
| F11 | `74fca20` | the hire clamp is documented in place and pinned by a test (no behaviour change) |
| F12 | `34ef456` | the same-turn bodyguard is pinned by a test (no behaviour change) |
| F13 | `9ed9e18` | goods handed to a keeper that does not trade them are pinned as inert (no behaviour change) |
| F14 | `e5d3096` | `global.html` / `player.html` banners describe the live pages |
| F15 | `dbb61e1` | `parse.nim`'s header lists every addition to the note's verb table; `sentences.md` gains the two missing offer words |
| F16 | `33b7d62` | the closing snapshot reads `SETTLED`; the remaining sub-items answered with evidence below |
| F17 | `575c86b` | a fallen-back LLM seat is recorded `scripted: true` on its act event |

---

## F1 (blocking) — checklist item 7's "tuned with a grid harness, not guessed"

**Fixed — `dfb740a`.** Checklist item **7**.

What existed: the five numbers lived as literals inside the two baselines' rules
(`llm.nim:236, 245, 295, 312, 320`), and nothing in the tree searched them.

What exists now:

- `src/cogmud/llm.nim` — the five thresholds are a `BaselineParams` object; the shipped point is
  `TunedParams` (`factorSellMargin 0`, `factorPickupValue 8`, `magpieHawkPeriod 3`,
  `magpieSellMargin 1`, `magpieBuyMargin -1` — exactly the design note's numbers, so no baseline
  behaviour changed). `scriptedSentence`/`scriptedAction` take the params, defaulted to
  `TunedParams`, which is how the sweep plays a candidate.
- `tests/test_tuning.nim` — the harness, run by CI like any other test, twice (debug and
  release). It sweeps **30 factor points** (`sellMargin ∈ -2..2` × `pickupValue ∈` every item
  baseValue) and **64 magpie points** (`hawkPeriod ∈ 2..5` × `sellMargin ∈ 0..3` ×
  `buyMargin ∈ -3..0`), plays a full 14-turn all-scripted episode of the shipped mixed table
  (`magpie factor factor magpie factor magpie`) on eight seeds at every point — 752 episodes —
  scores the seats playing the baseline under test with the game's own score, applies a
  feasibility predicate drawn from what each baseline exists to do (factor: every seat fills a
  commission, never robs/hires/trades; magpie: a successful robbery every seed, an offer per
  episode on average, nothing ever delivered, a theft in the 8-turn certification fixture, and a
  mean below factor's), and re-derives the winner.
- `docs/tuning/baseline-grid.md` — the surface, committed. The same test regenerates it in memory
  and asserts it **byte-for-byte**, so the report cannot drift from the code; a judge reproduces
  it with `COGMUD_TUNING_WRITE=1 nim r --path:src tests/test_tuning.nim`.

What the sweep says, from the committed report:

- `factor`: shipped `sell 0 · pickup 8` scores **1.4417**, and it is the grid's best feasible
  point — **regret 0.0000** (two neighbours tie it exactly, which is why ties keep the incumbent
  rather than churning a threshold the sweep cannot separate). The test asserts *no* feasible
  point outscores it.
- `magpie`: shipped `period 3 · sell 1 · buy -1` scores **0.3729**; the best feasible point is
  `period 5 · sell 0 · buy -1` at **0.3750** — **regret 0.0021 against a standard error of
  0.0521**, i.e. the sweep cannot distinguish them. The test asserts the regret stays inside one
  standard error of the seed mean, and prints winner, shipped, regret and s.e. on failure.

Evidence it runs in CI: run 32690212886, job `test`, both modes —
`[Suite] baseline parameter sweep` → `[OK] the shipped point of each baseline is on the grid and
feasible`, `[OK] nothing on the factor grid outscores the shipped point`, `[OK] no grid point
beats magpie's shipped point by a standard error`, `[OK] the committed sweep report is the one
this harness just produced`.

Scope note, stated plainly: the design note *fixes* these five numbers (§Decisions, the two
baseline rule lists), so the harness's job is to search the neighbourhood and show the shipped
point survives the search — which it does, outright for `factor` and inside the noise for
`magpie`. Nothing was re-tuned away from the note.

## F2 — `.plate-robbed` could never render

**Fixed — `27fb13e`.** Not a checklist item (legibility of `#scorebug` content; item 11 covers
only `.plate-name`, still satisfied).

`tableStateJson` (sim.nim) now marks, in the same single pass that counts deals, every seat a
successful robbery took from on this turn or the one before, and emits `recentRobbed`. The
scorebug's existing condition therefore fires and `.plate-robbed` is live CSS again.
`tests/test_sim.nim` asserts the field is empty before the theft, names the victim after it, and
is clear a turn later; `scripts/manifest/protocol_global.txt` documents the key and the manifest
was regenerated from it.

Evidence beyond the unit test: run 32690212886, `wasm-viewer` → `Load the bundle in a real
browser` reports the scorebug as
`… Gizmo MARKET SQUARE -0.22 25C 1 item ROBBED Ratchet …` — the chip is on screen in headless
chromium against the replay `docker-smoke` produced.

## F3 — the amber tether

**Fixed — `4135e22`.** Not a checklist item.

`drawTokens` now computes every token's spot in a first pass, draws a dashed amber tether between
a hireling (`retainerTurns > 0`) and its employer (`retainerOf`) when both stand in the same
room, then draws the tokens over it. `tests/test_viewer.nim` asserts `drawTether` exists and that
it is gated on the shared room.

## F4 — `salienceOf(iSay)` measured the wrong string

**Fixed — `ec805ce`.** Not a checklist item.

The speech class lifts the spoken line out of the sentence and broadcasts it, but the event's
`say` field carried only the reply's separate `say` field, so a 100-rune spoken line scored 20
instead of the design's 30. The class now fills the act's `say` with the lifted line when the
reply carried none, and posts it to the room exactly once — the `spoken != acts[seat].say` guard
is what keeps re-derivation byte-identical, because on replay the field arrives already filled.

Evidence: `tests/test_sim.nim` asserts a long lifted line scores 30, a short one 20, and that the
room heard it once; the existing replay tests (`frames.len == events.len + 1`, final-frame
equality, the tamper check) still pass, and I additionally re-derived an all-`iSay` episode by
hand and compared `tableStateJson` — identical.

## F5 — the unreachable `iGive`→shop salience branch

**Fixed — `8a0b41f`.** Not a checklist item.

`resolveGiveNpc` sets `oNoMatchingCommission` for every keeper but Vell, so `reason == oOk and
npc >= 0` is always a Guildhall delivery and the `25` branch was dead. The Guild test is now the
`npc >= 0` test — identical behaviour, one branch shorter — with the reason recorded in place.
`tests/test_sim.nim` asserts a handover that banks no commission scores the failed-act 5.

## F6 — the chart re-computed the score in JS

**Fixed — `f3bfe9f`.** Not a checklist item (item 2 unaffected: the authoritative numbers always
came from the re-derivation).

`chartFrom` now reads the sim's own per-frame score out of `payload.states[i + 1]` for the turn
event at `i` — the same wasm re-derivation the rest of the viewer draws — instead of rebuilding
wealth and points from JS copies of the item values, `PointsPerUnit`, `CompletionBonus`, the
quest count, `PointValue`, `StartCoin` and `ScoreScale`. The live driver samples the seats' own
scores once per turn from the snapshots, for the same reason. Every remaining `event.npc === 4`
in the renderer (`beatKind`, `actLine`, the feed class, the commission FX) goes through
`guildOf(world)`, and the completion test through `pointsPerUnitOf(world)`; `worldJson` publishes
`guild` and `pointsPerUnit` (the two commission constants moved to `world.nim` beside `QuestItems`
and `GuildNpc` so it can), and the manifest's global protocol documents both keys.
`tests/test_viewer.nim` asserts the literals are gone; `tests/test_sim.nim` asserts the payload
carries them.

## F7 — the tautological observation-split assertion

**Fixed — `f8d1ea4`.** Not a checklist item.

The `"delivered":… == "delivered":…` comparison is replaced by a structural check: `questNodes`
walks the seat's whole `playerStateJson` for every object carrying a commission's shape, and the
test asserts there are exactly `Quests` of them and that each is this seat's own item, count and
delivered figure. That is the design's "no other seat's quests" clause, asserted rather than
assumed. (Note for the record: the redaction itself was already correct; only the assertion was
not.)

## F8 — the restock test's unused `expected`

**Fixed — `7e34493`.** Not a checklist item.

The computed array is now compared item by item against the shops' books, so the design's "each
NPC's items each gain exactly `12 div tradeList.len` (± the round-robin remainder)" is asserted
exactly, not merely bounded below. The cap and the outside-the-trade-list checks are kept.

## F9 — prose coverage vs production coverage

**Fixed — `e8eca8b`.** Not a checklist item.

`tests/test_sim.nim` gains a suite that drives a named case for **every** outcome the rules can
reach — the five parse failures, the six slot failures, the shop and commission failures, all
five robbery guards, an expired offer and an honest town — collects the reasons off the recorded
act events and asserts all 25 appear. The 26th, `oRejected`, is asserted **absent**, with the
reason recorded in place: nothing in `sim.nim` sets it; it exists for `server.nim`'s
belt-and-braces guard, which logs the refusal and plays a wait, so a seat reads `waited`. The
parse test is renamed to "every outcome reason has prose a seat can read", which is what it
proves.

So the design's claim is now true of 25 reasons and demonstrably false of one, in the tree, with
the exception documented at both ends rather than papered over.

## F10 — restock at turn 0

**Fixed in the prose — `e55af65`.** Not a checklist item.

The reviewer's reading is right and I did not touch the code: the guard is what makes the note's
own arithmetic work (`askAt(hide, 8) + askAt(hide, 7) = 9`, asserted at `test_score.nim:89`).
`scripts/manifest/rules.md` now states the exemption in the same words as the code comment, and
the manifest was regenerated. The design note itself is outside my scope to edit; the
contradiction is between the note and its own worked example, and the code follows the example.

## F11 — the hire clamp

**No behaviour change, by evidence — `74fca20`.** Not a checklist item.

The design contradicts itself: its intent table says "posts a hire offer for `coin` (1 .. the
seat's coin)" — a clamp — and its test list says such an offer is "never posted" — a refusal. The
code follows the intent table, which is the normative section, and the code's own comment
repeated the refusal wording, so the tree said both things too. The comment now states the clamp
and why; the test, which only ever exercised `coin == 0`, now also asserts that an employer
holding 10 who asks for 15 posts a **10-coin** hire (`reason == oOk`, `offers[0].coin == 10`).

## F12 — the same-turn bodyguard

**No behaviour change, by evidence — `34ef456`.** Not a checklist item.

It is exactly what the design's class order produces: cog-to-cog (class 4) resolves before
robbery (class 5) and `resolveAccept` binds the retainer immediately. Nothing asserted it, so a
test now drives the sequence (offer; then accept and mug in the same turn) and asserts the
mugging fails 2 against 2 and the loot stays put — the ordering cannot drift silently now.

## F13 — goods a keeper does not trade

**No behaviour change, by evidence — `9ed9e18`.** Not a checklist item.

The design says "the goods enter its stock" with no exception, which is literally what the code
does, and the entry is inert: `resolveBuy` checks the trade list before the shelf (so the goods
report `out_of_stock`), and `tableStateJson` prices a non-traded good at 0 on both sides. A test
now hands Vell two relics and asserts all four of those facts, so the restock test's "nothing
outside the trade list ever appears" is no longer the only word on the subject.

## F14 — the live pages' banner

**Fixed — `e5d3096`.** Not a checklist item (item 14 concerns the replay chrome, which is
correct).

Both live pages carried the replay page's banner verbatim, claiming a `.treel#reel` inside a
`#transport` neither page has, and the `relayout()` comment claimed `--band` included the reel
row. Both now describe a live page: one appended element (`#townbar`), the starter's live ids,
and `--band` measured as `0px` because there is nothing under the stage. Comments only.

## F15 — `wander` and the rest of the verb-table additions

**Fixed — `dbb61e1`.** Not a checklist item.

`parse.nim`'s header now lists every deliberate addition with its reason: `off`, **`wander`**
(load-bearing — it is the verb `magpie` writes on every ramble turn, and `test_bot` asserts zero
unreadable scripted sentences), `have`/`has`, `picks`, `asks`, the unguarded `put`/`read`, the
`bargain`/`proposal` offer words, and the verbless purchase. `sentences.md`'s accept row gains
the two offer words it was missing, and the manifest was regenerated. The table itself is
unchanged.

## F16 — the small prose gaps

**One fixed — `33b7d62`; the rest answered with evidence.** Not a checklist item.

- **`WAITING ON 6` on the closing frame — fixed.** `resolveTurn` resets `acts[]` before logging
  the final turn event, so every seat read `pending` on a turn nobody would act in.
  `matchHeader` now reads `SETTLED` once `turnsPlayed` has reached the episode's turn count;
  `tests/test_viewer.nim` asserts the guard. The CI readouts still give three distinct values
  (`0%="TURN 4 / 8 · WAITING ON 6"`, `50%="TURN 5 / 8 · WAITING ON 6"`,
  `100%="FINAL · RATCHET 1.73"`).
- **2.03 vs 2.025 — no change.** `81/40 = 2.025` exactly; `test_score.nim` asserts 2.025 to
  `1e-9`, which is the only assertion that can be true. The note's §Tests line asking for "2.03
  to 1e-9" is arithmetically impossible; 2.03 is the two-decimal display.
- **`/client/replay` in two places — no change.** The note's scope list and its §Server section
  disagree; the code follows §Server (the route exists, `client/replay.html` ships), and the
  **manifest** declares only the static bundle, which is what checklist item 3 tests.
- **`tools/make_cog_colors.py` vs `scripts/art/make_cog_colors.py` — no change.** `tools/` holds
  the hooks CI and `coworld build` invoke by path (`build_replay_viewer.sh`, `ci/docker_smoke.sh`,
  `ci/viewer_smoke.mjs`); `scripts/` holds dev helpers with their inputs (`scripts/art/source/`,
  `scripts/manifest/`). Moving the recolour script would separate it from its sources to satisfy
  a path in prose; the split is deliberate and the sprites it produced are committed.
- **`openTurn` in the server pseudocode — no change.** `openTurn` is driven from `initSim` and
  from `resolveTurn`; calling it in the server loop as well would double-open. Equivalent, and
  the reviewer traced it as such.
- **The extra `turnDelayMs` sleep after the loop — no change.** It is one pacing sleep so the
  last frame can be read before shutdown; 15 × 400 ms = 6 000 ms against
  `PacingBudgetMs = 20 000`, and `sampleEpisode` caps the whole thing. Checklist item 5 is
  unaffected (the 704 s < 720 s arithmetic does not include it).
- **Room descriptions under 560 px — no change.** `drawRoomCard` never draws a description at any
  width, so there is nothing for the compact rule to drop; the other half of the note's sentence
  (`compact: width < 560`, `rows.slice(0, 1)` on the awning) is implemented. Drawing descriptions
  on an 80–210 px card would cost legibility, which is the thing that sentence was protecting.

## F17 — the fallback left no trace on the event

**Fixed — `575c86b`.** Checklist item **8** (it was already satisfied by the stdout line; it is
now satisfied by the recorded bytes as well).

`decideAll` marks each seat it had to fall back for (`client.fellBack`, reset at the top of every
batch) and `server.nim` folds that into the `scripted` flag it stamps on the act event, so a
fallback is countable from the replay and the results, not only by grepping stdout. The
manifest's global protocol documents the widened meaning of `scripted`.

`tests/test_bot.nim` drives the real path without touching the network: a Bedrock endpoint
pointed at `127.0.0.1:9` (discard — refused instantly), both batches fail, and the test asserts
every seat played a legal scripted sentence and every seat is marked. It runs in ~1 s.

---

## NOTED (not fixed)

Things I saw while working that are **not** findings in this round and that I deliberately left
alone:

- `llm.nim`'s captured error strings are truncated on **bytes** (`head[0 ..< 160]`,
  `body[0 .. min(high, 400)]`). They reach `echo` only, never the replay, so checklist item 9 is
  unaffected — but a byte cut through a multi-byte rune would print mojibake in a pod log.
- `docs/tuning/baseline-grid.md` adds ~14 s to the debug test run and ~2 s to the release run
  (752 episodes). If CI time ever matters, the seed set is one constant at the top of
  `tests/test_tuning.nim`.
- `resolveBuy` reports `oOutOfStock` for a good the keeper does not deal in, where `oNotWanted`
  reads better and already exists for the sell side. Changing it would change a documented
  outcome, so I left it; F13's new test pins the current behaviour.
