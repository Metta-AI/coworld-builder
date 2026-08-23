# Eleusis: a secret law of nature, costly experiments, and the choice to publish or hoard

Forked from **`Metta-AI/cogame-bullwhip`** (read at `/workspace/starters/cogame-bullwhip`,
commit as mounted) — the newest member of the parley → cosino → focus → babel → bullwhip
lineage, and the closest turn structure we have: N seats, one **simultaneous** decision per
turn, decisions made server-side from a per-seat prompt, one parallel LLM batch per turn,
scripted baselines in the same image, a pure `sim` module shared by server/tests/wasm viewer,
and the parley broadcast chrome around a canvas stage. **Every convention there holds here
unless this note says otherwise.**

> Source idea (verbatim):
>
> "14 Eleusis — science as a game: a secret law of nature, costly experiments, and the choice to publish or hoard
>
> The server holds a hidden rule over coloured token sequences (Eleusis/Zendo). Each turn an agent pays to run an experiment and sees the result privately; it may publish (everyone learns it, author gets citation credit) or hoard. Periodic prediction tests score everyone; citation credit pays too. Tune the ratio and watch open science or secrecy emerge.
>
> Seats: 4-6
> Motive: mixed: shared truth, private credit
> Policy interface: LLM prompt
> Fills gap: hypothesis discovery / epistemics / publish-or-hoard dilemma
> Integrity (anti-collusion): Citation rings don't pay: credit accrues only for published results later confirmed by OTHER seats' passing predictions, and accounts are capped at one seat per episode.
>
> Replay plan (watchability): Lab bench: token strips feed a black-box machine that stamps PASS or FAIL; published results pin to a shared corkboard, hoarded ones slide into a drawer only spectators can see (tagged secret). Endcard reveals the hidden rule and who got closest."

Nothing in this note is escalated: every open point the idea left (seat count inside 4–6, the
rule family, the publish/hoard payoff ratio) is a rail the designer decides. There is no `OPEN`
section.

## The game

**Seats: exactly 5 (`num_agents` = 5).** Reason: citation credit needs an author, a confirmer
and a market, so 4 is thin and 6 costs LLM throughput — at 5 seats one parallel batch every
12 s is 25 requests/minute, under the hosted Bedrock sidecar's 30 req/min per-episode cap
(6 seats at the same spacing sits exactly on it). 5 is also odd, so the knowledge pool rarely
splits into ties. Seats play under anonymous cog aliases (bullwhip's `CogNames`, seeded
shuffle); policy names are spectator-side only.

**Tokens and strips.** A token is one of four colours: `R` red, `B` blue, `G` green, `Y`
yellow. A **strip** is an ordered sequence of **exactly 4 tokens**, written as a 4-character
uppercase string, e.g. `"RBGY"`. The strip universe is `4^4 = 256` strips, enumerated in
lexicographic order over `R < B < G < Y` (index 0 = `"RRRR"`, index 255 = `"YYYY"`).

**The hidden rule.** The server draws one rule instance from a fixed, **public** catalogue of
parametrised templates. The catalogue is printed in every seat's prompt — the hypothesis space
is known, the instance is not. That is what makes the game a search rather than a guess.

Catalogue (`RuleKind`, parameters, and the enumeration order that fixes `ruleId`). Colours
iterate in the order `R, B, G, Y`; the enumeration runs template by template, and inside a
template over its parameter grid in the order written:

| # | kind | parameters | instances | PASS iff |
|---|---|---|---|---|
| 1 | `rkContains` | c | 4 | colour `c` appears at least once |
| 2 | `rkAtLeastTwo` | c | 4 | colour `c` appears 2 or more times |
| 3 | `rkParity` | c, `even`\|`odd` | 8 | the count of `c` is even (0 counts as even) / odd |
| 4 | `rkAdjacent` | c, d (all 16 ordered pairs, `c = d` allowed) | 16 | some position `i ∈ 1..3` has `t[i] = c` and `t[i+1] = d` |
| 5 | `rkBefore` | c, d (`c ≠ d`) | 12 | both appear and the first `c` is left of the first `d` |
| 6 | `rkStartsWith` | c | 4 | `t[1] = c` |
| 7 | `rkEndsWith` | c | 4 | `t[4] = c` |
| 8 | `rkEndsSame` | `same`\|`differ` | 2 | `t[1] = t[4]` / `t[1] ≠ t[4]` |
| 9 | `rkRepeat` | `none`\|`some` | 2 | no two adjacent tokens are equal / at least one pair is |
| 10 | `rkMoreThan` | c, d (`c ≠ d`) | 12 | `count(c) > count(d)` |

**68 instances, `ruleId` 0..67.** Selection is seeded and deterministic: `rng =
initRand(seed*7919 + 17)`; shuffle `[0..67]`; take the **first** instance whose PASS fraction
over all 256 strips lies in **[0.10, 0.90]** (degenerate rules like `rkAtLeastTwo` with a
near-empty PASS set are skipped). The PASS fraction is computed by enumeration — 68 × 256
predicate evaluations, microseconds. `ruleText(rule)` is the human line the endcard reveals,
e.g. `"ADJACENT R B — a RED token immediately followed by a BLUE token"`.

**The machine.** `evaluate(rule, strip) -> pass | fail` is a pure function. It is the only
oracle in the game; no seat ever sees `rule`.

**Turn structure.** The episode is `rounds` **research rounds** (default 24) with a
**prediction test** after every `testEvery` rounds (default 6 → tests after rounds 6, 12, 18,
24). Every research round and every test is **one simultaneous decision by all 5 seats**, so
each is exactly **one parallel LLM batch**. Total batches with the defaults: 24 + 4 = **28**.

Disclosure is pipelined by one turn, which is what makes the dilemma real: you pay, you look at
your private verdict, and you decide what to do with it on your *next* turn, by which time the
corkboard has moved. Each seat has at most one **pending** (undisclosed) result at a time.

### Resolution order — research round `r` (1-based), numbered

1. **Open the round.** The sim emits a `round` event and marks all 5 seats pending. The
   observation each seat receives (see below) is composed from the state at this instant.
2. **Collect decisions.** All 5 seats' requests go out as ONE parallel batch. Each reply is
   `{"experiment", "publish", "hypothesis", "notes"}` (schema and caps below). A reply that
   times out, fails to parse, or is illegal is retried once in a smaller batch with a hint,
   then replaced by the `openbook` scripted decision for that seat.
3. **Disclosure of the pending result** (applied per seat, in seat order 0..4, before this
   round's experiments so the corkboard a rival reads this round is last round's):
   - if the seat has no pending result, `publish` is ignored and nothing is recorded;
   - if `publish` is true and the strip is **not already on the corkboard**, the fact
     `(strip, verdict, author = seat, round = r)` is pinned to the corkboard and the seat
     becomes its **sole author**; event `disclose` with `mode: "publish"`;
   - if `publish` is true and the strip **is** already on the corkboard, the fact is recorded
     as a confirmation with **no authorship and no credit ever**; event `disclose` with
     `mode: "duplicate"`;
   - if `publish` is false, the result goes to the seat's private drawer (spectator-visible,
     rival-invisible); event `disclose` with `mode: "hoard"`.
   The seat's `hypothesis` (public) and `notes` (private) are stored on every reply.
4. **Experiments** (applied per seat, in seat order 0..4). `experiment` is a strip or `""`:
   - `""` (or the scripted `skip`): nothing is charged; event `skip`.
   - a legal strip: the seat is charged `experimentCost` (default **$1.00**), the machine is
     consulted, `verdict = evaluate(rule, strip)`, the strip is added to the episode's
     **used-strip set** (which prediction tests hold out), and the result becomes the seat's
     pending result. Event `experiment` carries `seat`, `strip`, `verdict`, `cost`,
     `scripted`, `hypothesis`, `text` (the seat's notes). *The verdict is private to the seat
     at this moment; it is in the replay bytes because the replay is a spectator artifact.*
     A seat may re-test a strip it or anyone else already tested; it pays again and learns
     nothing new.
5. **Advance.** `round += 1`. If `round % testEvery == 0` (or `round > rounds`), the next turn
   is a prediction test; otherwise step 1 again.

### Resolution order — prediction test `k`, numbered

6. **Draw the test.** From the strips that (a) have never been the subject of any experiment in
   this episode and (b) have not appeared in an earlier test, the sim draws
   `testStrips` (default **6**) strips **balanced**: `testStrips/2` from the rule's PASS set
   and `testStrips/2` from its FAIL set, then shuffles them. Balance removes the base-rate
   exploit — answering all FAIL scores exactly 50 %. The draw uses the episode RNG stream, so
   `replayMatch` re-derives it exactly. Event `test` carries `test` (1-based), `round`,
   `strips[]` and `truth[]` (spectator-only; asserted against re-derivation the way bullwhip
   asserts its `week` event).
7. **Collect answers.** One parallel batch: reply
   `{"answers", "publish", "hypothesis", "notes"}`. Step 3's disclosure rules run first on the
   test reply's `publish` (so the last research round's result always gets a decision), then
   the answers are scored. `answers` must be exactly `testStrips` entries of `PASS`/`FAIL`.
   Invalid → one retry → `openbook`'s answer vector for that seat.
   Event `answer` per seat: `test`, `seat`, `answers[]`, `correct`, `scripted`, `hypothesis`,
   `text`.
8. **Knowledge pool.** Let `c_j` = seat `j`'s correct answers. Seat `j` earns
   `knowledgePool * c_j / max(1, Σ_k c_k)` (default pool **$20.00**). This is the rivalrous
   half of the dilemma: every rival you teach takes a slice of your pool.
9. **Citation settlement.** For each test strip `x` and each seat `j` that answered `x`
   **correctly**, let `A(x, j)` = the set of seats `a ≠ j` that are the **author** of a
   corkboard fact whose strip is at **Hamming distance exactly 1** from `x` (differs in exactly
   one of the four positions) and that was published **before this test opened**. If `A(x, j)`
   is non-empty, a pot of `citePot` (default **$0.50**) is split **equally** among its members.
   An author is paid at most once per `(strip x, seat j)` pair no matter how many of its facts
   support `x`. Self-citation is impossible by construction (`a ≠ j`), duplicates have no
   author, and payment requires a rival to be *actually right* about a strip nobody has ever
   tested — which is the anti-collusion pin, encoded: **a citation ring cannot manufacture a
   passing prediction.** Events: one `settle` event per test carrying `pool[5]`, `credit[5]`,
   `correct[5]`, running `scores[5]`, and `citations[]` (`{author, by, strip, amount}`) for the
   feed.
10. **Advance.** If this was the test following round `rounds`, the episode settles
    `complete`; otherwise the next turn is research round `round`.

### Scoring

```
score(seat) = knowledge(seat) + credit(seat) − experimentCost × experiments(seat)
```

**Higher is better** (unlike bullwhip, the sign is positive and scores may be negative — a seat
that experiments 24 times and never answers a test correctly finishes at −24). `results.scores`
carries this number per seat; **the league ranks by mean episode score**.

**The tuned publish/hoard ratio.** With the defaults (`experimentCost 1.0`,
`knowledgePool 20.0`, `citePot 0.5`, `testStrips 6`, 5 seats, 4 tests):

- Teaching one rival one extra correct answer costs you roughly
  `20/Σc − 20·c_you/(Σc)²` ≈ **$0.6–1.0** of pool share per test.
- One well-placed publication sits one token away from up to 12 strips; realistically it
  supports 1–2 of the 6 test strips, is confirmed by 2–4 rivals, and pays
  `0.5 × confirmers / authors` ≈ **$0.5–2.0** per test.

So publishing is worth it precisely when your result is *informative to others and near the
frontier* — which is what "open science emerges or it doesn't" should mean. The knife edge is
config, not code: the `open-science` variant raises `citePot` to 1.5 and the `closed-shop`
variant drops it to 0.1, so the league can watch the behaviour flip.

**Who got closest** (endcard, not scoring): the seat with the highest lifetime test accuracy
`correct/answered`, ties broken by higher score, then lower seat index. If no test was scored,
`closest = -1` and the endcard says "no test was scored".

### Per-seat observation — visible vs hidden

**Visible to a seat** (this is exactly what its prompt carries):

- its own alias, seat index, the round number and the round/test schedule;
- the **full rule catalogue** above (the hypothesis space is public);
- the economy constants in force (`experimentCost`, `knowledgePool`, `citePot`, `testStrips`);
- **its own experiment log**: every strip it tested, the verdict, and whether it published,
  hoarded or duplicated it;
- the **corkboard**: every published fact — author alias, strip, verdict, round published —
  in publication order;
- the **public scoreboard**: every seat's alias, current score, knowledge earned, citation
  credit earned, experiments run, publications, and each seat's **latest stated hypothesis**
  (hypotheses are public; they are talk, not evidence);
- **per-test correct counts for every seat** from every settled test (so "who is winning the
  argument" is public);
- its own private notes, fed back verbatim.

**Hidden from every seat:** the rule (`ruleId`, `ruleText`), every other seat's **hoarded**
results, every other seat's notes, other seats' pending experiment choices for the current
turn, the test's `truth[]` before settlement, and which strips a future test will use.

**Spectator-only (replay/`/global` only, never on a player socket):** the hidden rule from
frame 0, every seat's drawer of hoarded results tagged `secret`, every seat's notes, and the
test truth.

### End conditions and `results.reason`

- `"complete"` — the test following research round `rounds` has settled. This is the normal
  ending.
- `"deadline"` — the play deadline (60 % of `episodeTimeoutSeconds`) was reached. The sim
  settles **between batches**: an open test that has not been fully answered is discarded
  unscored, pending undisclosed results stay hoarded, and scores use the tests already settled
  and the costs already charged. **This design declares `deadline` an acceptable
  `results.reason`** (phase 60 check 4), because a short honest episode that lands beats a long
  one the platform discards.

`results.reason` is one of exactly `"complete"` or `"deadline"`. No other value is legal.

## Decisions: LLM with scripted fallback

Transport, credential resolution (Bedrock sidecar → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI`), the Bedrock model candidate list with **haiku first and
`us.anthropic.claude-sonnet-4-6` removed** (raid, 2026-08-23: that profile times out on every
sidecar call), `extractJsonObject`, `cleanText` rune-safe truncation, and "no credentials ⇒
every seat scripted, immediately, with no network wait" are ported from
`src/bullwhip/llm.nim` unchanged in shape.

**One batch per turn.** All 5 seats decide simultaneously by rule, so the server fires 5
requests as one `curly.makeRequests` batch per turn (`decideAll`). Never sequentially — that is
the documented way to blow the 720 s budget.

**Wall-clock budget, stated out loud.** Assume `episodeTimeoutSeconds = 1200` (the game
container is not given `COWORLD_TIMEOUT_SECONDS`); `PlayBudgetFraction = 0.6` → **720 s of
play**.

- Batches per episode: `rounds + rounds/testEvery` = 24 + 4 = **28**.
- `minBatchSpacingMs` = **12 000**: the server floors the wall-clock gap between the *starts*
  of consecutive batches at 12 s. 5 requests / 12 s = **25 req/min**, under the sidecar's
  30 req/min per-episode cap.
- Typical batch latency on haiku with a ~2.5 k-token prompt: 6–12 s, absorbed by the spacing
  floor. Typical episode: **28 × 12 s ≈ 336 s** plus ≤ 30 s of connect/startup ≈ **370 s ≈
  51 % of the 720 s budget**.
- Worst case is bounded, not hoped for: `llmTimeoutSeconds` = **40**, so a pathological episode
  where every batch burns its full timeout reaches 720 s after ~18 batches and settles
  `deadline` with 14 rounds and 2 tests scored. The deadline is checked **before every batch**.
- `sampleEpisode(config)` fits the episode to the budget and is idempotent (guarded by
  `sampled`, exactly like bullwhip): `maxBatches = int(episodeTimeoutSeconds * 0.6 * 1000 /
  max(minBatchSpacingMs, 1)) - 2`; while `rounds + rounds div testEvery > maxBatches`, `rounds`
  is reduced (never below `MinRounds = 4`). With the defaults 28 ≤ 58, so nothing is trimmed.

**Degrade, never hang.** Per seat, per turn: parse/legality failure or transport timeout →
**one retry** in a smaller batch carrying `"Your previous reply was invalid…"` → still failing
→ the **`openbook` scripted decision** for that seat, logged
`eleusis llm: seat N falling back to scripted decision`. A legality check is run *before*
accepting a reply (a `probe` copy of the sim applies it), so an illegal move never reaches the
sim. A slot that never delivers a prompt (player pod never connected within
`player_connect_timeout_seconds = 180`) plays `openbook` for the whole episode. Any raise
anywhere in `decideAll` is caught; the episode always advances.

**Reply schema.** One JSON object, nothing else; the system prompt demands the reply *begins
with `{`* (Haiku answers prose-first otherwise). `maxOutputTokens = 900`.

Research turn:

```json
{"experiment": "RBGY", "publish": true, "hypothesis": "ADJACENT R B?", "notes": "..."}
```

Test turn:

```json
{"answers": ["PASS","FAIL","PASS","PASS","FAIL","FAIL"],
 "publish": false, "hypothesis": "ADJACENT R B?", "notes": "..."}
```

Field rules and **character caps** (every free-text field is capped, and **every truncation is
on a rune boundary** — `runeSubStr`, never a byte slice; a byte-boundary cut lands invalid
UTF-8 in the replay and fails the strict parse):

| field | type | cap / legality |
|---|---|---|
| `experiment` | string | normalised: uppercased, whitespace and separators (`-`, `_`, `,`, space) stripped; the first 4 characters must all be in `RBGY`; `""` = skip. Anything else → invalid. |
| `publish` | bool | also accepts `"true"`/`"false"`/`"yes"`/`"no"`/`1`/`0`; missing → `false`. |
| `hypothesis` | string | **≤ 120 runes**, newlines → spaces, truncated with `…` on a rune boundary. Public. |
| `notes` | string | **≤ 600 runes**, truncated on a rune boundary. Private, fed back verbatim next turn. |
| `answers` | array | exactly `testStrips` entries; each `PASS`/`FAIL` case-insensitively, or `P`/`F`, or `true`/`false`. Wrong length or an unrecognised entry → invalid. |

The player-delivered `PLAYER_PROMPT` is itself capped at **4000 runes** by the server
(`MaxPromptLen`, bullwhip's value) and is truncated on a rune boundary.

**System prompt** (composed per seat; `<…>` are substitutions):

```
You are <alias>, one of 5 rival scientists in the ELEUSIS laboratory.

A sealed machine holds ONE hidden rule. You feed it a STRIP of exactly 4
coloured tokens - each token is R (red), B (blue), G (green) or Y (yellow),
written as 4 letters, e.g. RBGY - and it stamps PASS (the strip obeys the
rule) or FAIL (it does not).

The hidden rule is exactly ONE entry of this public catalogue (68 in all):
  CONTAINS c        - c appears at least once                  (c in R,B,G,Y)
  AT-LEAST-2 c      - c appears two or more times
  PARITY c even/odd - the number of c's is even (0 is even) / odd
  ADJACENT c d      - somewhere c is immediately followed by d (d may equal c)
  BEFORE c d        - both appear, and the first c is left of the first d
  STARTS c          - the first token is c
  ENDS c            - the fourth token is c
  ENDS-SAME / ENDS-DIFFER - first token equals / differs from the fourth
  NO-REPEAT / HAS-REPEAT  - no two neighbouring tokens are equal / some are
  MORE c d          - c appears strictly more often than d
Every strip the machine PASSES obeys that one rule; every strip it FAILS
breaks it. Nothing else is random.

Each round you may run ONE experiment; it costs $<experimentCost>. ONLY YOU
see the verdict. On your NEXT turn you decide what to do with it:
 - PUBLISH: it is pinned to the shared corkboard. Every rival reads it, and
   you may earn citation credit later. Publishing a strip somebody already
   published earns nothing, ever.
 - HOARD: it stays yours alone.

Every <testEvery> rounds a PREDICTION TEST scores everyone: <testStrips>
strips nobody has ever tested, exactly half of which the machine passes. A
prize pool of $<knowledgePool> is split between the seats in proportion to
how many each got right - so every rival you teach takes a slice of your
pool. Citation credit pays the other way: when another seat answers a test
strip correctly and one of YOUR published results differs from that strip in
exactly one token, a $<citePot> pot for that strip is shared between the
seats whose published results do. You are never paid for your own answers.

Your score is prize money + citation credit - $<experimentCost> per
experiment. Highest score wins. Nothing else scores.

Your notes are private and are handed back to you every turn. Your
hypothesis line is PUBLIC - every rival reads it, and it is not binding.

OUTPUT FORMAT: reply with ONLY one JSON object, nothing else - no analysis,
no explanation, no markdown fences, no text before or after the object. Your
reply must begin with the character { and end with }.
```

**User prompt** (research turn), in this order: `ROUND r OF <rounds> — next prediction test
after round <next>`; `YOUR PENDING RESULT: RBGY -> PASS (publish it or hoard it now)` or
`(none)`; `YOUR EXPERIMENTS SO FAR` table (`round | strip | verdict | published?`); `THE
CORKBOARD (<n> published results)` table (`round | author | strip | verdict`); `SCOREBOARD`
table (`seat | score | prizes | credit | experiments | published | latest hypothesis`);
`TEST RESULTS SO FAR` (`test k: <alias> c/6, …`); `YOUR NOTES FROM EARLIER ROUNDS`; the
operator block (`GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules…)`
= `PLAYER_PROMPT`); then the reply template line naming every field and its cap. The test-turn
user prompt replaces the pending-result line with `PREDICTION TEST k — answer all
<testStrips> strips` and the strip list, and keeps everything else.

**Scripted baselines** (same image, env-switched: `PLAYER_SCRIPTED=openbook` /
`PLAYER_SCRIPTED=hoarder`; `PLAYER_SCRIPTED` also accepts `1`/`true`/`yes` = `openbook`).
Both share one engine and differ only in disclosure — which is exactly the axis the game is
about, so the two fillers are a live control experiment:

- **Version space.** `consistentRules(facts)` = every catalogue instance that agrees with every
  fact the seat knows (its own results ∪ the corkboard). 68 × |facts| evaluations.
- **Predict.** `predict(x)` = PASS iff `2 × |{r ∈ consistent : evaluate(r, x) = pass}| ≥
  |consistent|` (ties → PASS). If `consistent` is empty (only possible if the corkboard is
  corrupt), PASS.
- **Experiment.** Candidate strips are scanned in a **per-seat seeded order**
  (`initRand(seed*7919 + 101*seat + 3)` shuffle of 0..255, so the five baselines do not run the
  same sweep), skipping strips whose verdict the seat already knows; the chosen strip is the
  one whose PASS-split among `consistent` is closest to half (information-greedy), ties broken
  by sweep order. If every strip is known, the seat skips (`experiment: ""`, no cost).
- **Disclose.** `openbook` publishes every pending result. `hoarder` never publishes.
- **Hypothesis line.** `ruleText` of the first surviving instance in `consistent`, or
  `"no consistent rule"` — deterministic, ≤ 120 runes, and legible in the feed.
- Neither ever writes `notes`. Both are always legal by construction: a 4-token strip from the
  universe, and exactly `testStrips` `PASS`/`FAIL` answers.

`openbook` is also the **fallback** decision used for any seat whose LLM reply fails, and for
every seat when there are no credentials at all — so offline certification and the CI docker
smoke always complete a full episode with real, varied play.

## Sim module

`src/eleusis/types.nim` — `EleusisError`, `PlayerConfig`, `GameConfig`, `EventKind`,
`GameEvent`, `defaultGameConfig()`, `update(config, json)`. `GameConfig` fields (defaults in
brackets): `tokens`, `players`, `seed [0]`, `rounds [24]`, `testEvery [6]`, `testStrips [6]`,
`experimentCost [1.0]`, `knowledgePool [20.0]`, `citePot [0.5]`,
`episodeTimeoutSeconds [1200]`, `sampled [false]`, `minBatchSpacingMs [12000]`,
`turnDelayMs [0]`, `playerConnectTimeoutSeconds [180]`, `model ["claude-sonnet-5"]`,
`maxOutputTokens [900]`, `llmTimeoutSeconds [40]`. `update` validates `rounds ≥ 4`,
`testEvery ≥ 2`, `testStrips` even and in 2..12.

`src/eleusis/sim.nim` — pure rules, no IO, no networking; shared verbatim by the server, the
tests and the wasm viewer.

Constants: `Seats* = 5`, `StripLen* = 4`, `Colours* = ['R','B','G','Y']`,
`StripUniverse* = 256`, `RuleCount* = 68`, `MinRounds* = 4`, `MaxRounds* = 60`,
`MinPassFraction* = 0.10`, `MaxPassFraction* = 0.90`, `MaxHypothesisLen* = 120`,
`MaxNotesLen* = 600`, `CogNames*` (bullwhip's list, verbatim).

Types: `Rule` (`kind`, `a`, `b`, `flag`), `Verdict = enum vPass = "pass", vFail = "fail"`,
`Fact` (`strip: string`, `verdict: Verdict`, `author: int`, `round: int`, `duplicate: bool`),
`SeatState` (`score`, `knowledge`, `credit`, `spend`, `experiments`, `published`, `hoarded`,
`correct`, `answered`, `hypothesis`, `notes`, `pending: Option[(string, Verdict)]`,
`log: seq[Fact]`, `secrets: seq[Fact]`), `TestState` (`index`, `round`, `strips: seq[string]`,
`truth: seq[Verdict]`, `answers: seq[seq[Verdict]]`, `answered: seq[bool]`, `open: bool`),
`Phase = enum phResearch = "research", phTest = "test", phDone = "done"`, and `Sim`
(`config`, `names`, `rule`, `ruleId`, `round`, `phase`, `seats: array[5, SeatState]`,
`board: seq[Fact]`, `used: HashSet[string]`, `testsDone`, `test: TestState`,
`citations: seq[Citation]`, `roundsPlayed`, `done`, `reason`, `events`).

Pure API: `stripOfIndex(i)`, `indexOfStrip(s)`, `normaliseStrip(text)`, `catalogue()` (the 68
instances in enumeration order), `evaluate(rule, strip)`, `passFraction(rule)`,
`describeRule(rule)`, `pickRule(seed)`, `consistentRules(facts)`, `initSim(config)`,
`sampleEpisode(config)`, `tableNames(players, seed)`, `pendingSeats(sim)`,
`applyResearch(sim, seat, strip, publish, hypothesis, notes, scripted)`,
`applyAnswers(sim, seat, answers, publish, hypothesis, notes, scripted)`, `openTest(sim)`,
`settleTest(sim)`, `endEarly(sim)`, `score(sim, seat)`, `resultsJson(sim)`,
`benchStateJson(sim)`, `replayMatch(config, events)`, `eventToJson`, `eventFromJson`.
`applyResearch` / `applyAnswers` raise `EleusisError` on anything illegal (unknown seat, a seat
deciding twice in a turn, a malformed strip, a wrong-length answer vector, a decision after
`done`); the last seat's call resolves the turn.

**Event vocabulary** (flat `GameEvent`, JSON via `eventToJson`/`eventFromJson`; the replay's
`events[]` is the whole transcript and is what the wasm viewer re-derives from):

| kind | fields |
|---|---|
| `start` | — (`round: -1`) |
| `round` | `round` |
| `experiment` | `round`, `seat`, `strip`, `verdict`, `cost`, `scripted`, `hypothesis`, `text` (notes) |
| `skip` | `round`, `seat`, `scripted`, `hypothesis`, `text` |
| `disclose` | `round`, `seat`, `strip`, `verdict`, `mode` (`publish`\|`hoard`\|`duplicate`) |
| `test` | `test`, `round`, `strips[]`, `truth[]` (derived; asserted on re-derivation) |
| `answer` | `test`, `seat`, `answers[]`, `correct`, `scripted`, `hypothesis`, `text` |
| `settle` | `test`, `correct[5]`, `pool[5]`, `credit[5]`, `scores[5]`, `citations[]` = `[{author, by, strip, amount}]` |
| `end` | `round` = rounds played, `text` = reason, `rule` = `ruleText`, `ruleId`, `closest` |

**`benchStateJson(sim)`** — one frame; **this is exactly the JSON the viewer reads**, and the
wasm module emits one per event prefix:

```json
{"seats": [
   {"name":"Sprocket","score":6.5,"knowledge":4.0,"credit":3.5,"spend":6.0,
    "experiments":6,"published":4,"hoarded":2,"correct":9,"answered":12,
    "hypothesis":"ADJACENT R B?","notes":"...","pending":true,
    "last":{"strip":"RBGY","verdict":"pass","mode":"hoard"},
    "secrets":[{"strip":"RBGY","verdict":"fail","round":3}]}
 ],
 "board":[{"strip":"RBGY","verdict":"pass","author":2,"round":4,"cites":1.5,
           "duplicate":false}],
 "machine":{"seat":2,"round":7,"strip":"RBGY","verdict":"pass"},
 "test":{"index":2,"round":12,"strips":["RRBG","..."],"truth":["pass","..."],
         "answers":[["pass","fail","..."], null, "..."],
         "correct":[4,3,5,2,4],"open":false},
 "citations":[{"author":1,"by":3,"strip":"RBGY","amount":0.5,"test":2}],
 "round":7,"rounds":24,"testEvery":6,"testStrips":6,"testsDone":1,
 "phase":"research","rule":"ADJACENT R B — a RED token immediately followed by a BLUE token",
 "ruleId":37,"gameDone":false,"reason":""}
```

`seats[].secrets`, `test.truth` and `rule` are **spectator-only**: they appear in this frame
(the `/global` socket and the replay) and never on a player socket. `machine` is null outside
the moment an experiment is being stamped; `test` is null before the first test.

**`resultsJson(sim)`** — platform-facing, **policy** names:

```json
{"names":[5],"scores":[5],"knowledge":[5],"credit":[5],"spend":[5],
 "correct":[5],"answered":[5],"accuracy":[5],"published":[5],"hoarded":[5],
 "rounds":24,"maxRounds":24,"tests":4,"ruleId":37,"rule":"ADJACENT R B — ...",
 "closest":2,"closestName":"eleusis-empiricist:v1","reason":"complete"}
```

**Replay payload** (`eleusis.replay.v1`) — self-sufficient; the viewer contacts nothing but S3:

```json
{"protocol":"eleusis.replay.v1",
 "names":["Sprocket","Gizmo","Ratchet","Widget","Bolt"],
 "policyNames":["eleusis-empiricist:v1","...", "..."],
 "config":{"rounds":24,"testEvery":6,"testStrips":6,"seed":8123,
           "experimentCost":1.0,"knowledgePool":20.0,"citePot":0.5,
           "ruleId":37,"ruleText":"ADJACENT R B — ...","sampled":true},
 "events":[...],
 "results":{...}}
```

The viewer re-derives the rule from `config.seed` and **asserts it equals `config.ruleId`**;
a mismatch is a hard `data-replay-error` (the same contract bullwhip uses when a recorded
`week` event disagrees with the seeded re-derivation). `replayMatch(config, events)` returns
`events.len + 1` frames — `frames[i]` = state after `events[0..<i]` — by replaying the
`experiment` / `disclose` / `answer` events through the rules; `test` and `settle` events are
checked, not trusted, and a recorded `end` with `deadline` is applied directly (it is not
derivable from the decisions).

## Server, player, protocol

`src/eleusis.nim` — bullwhip's entrypoint verbatim in shape: read the runtime config, randomise
`seed` when it is not pinned, `sampleEpisode` **after** the seed is settled, then
`runReplayServer` or `runGameServer`.

`src/eleusis/server.nim` — bullwhip's `server.nim` with the loop replaced. Routes, registered
in this order and **before** any catch-all: `GET /healthz`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /client/renderer.js`,
`GET /client/chrome.css`, `GET /client/assets/@name`, `WS /global`, `WS /replay`, and
`WS /player?slot=N&token=T` in live mode only. Both `/client/` routes serve real pages and
neither opens the player socket (lantern 0.1.1). `mummy` hands Ping frames to the application:
answer every Ping with a Pong on `/global` (lantern 0.1.3).

Game loop, per turn: check the play deadline → snapshot the sim under the lock → run
`decideAll` for all pending seats **outside** the lock as one batch → apply each decision under
the lock (raising decisions are replaced by the `openbook` fallback and logged) → broadcast →
sleep until `minBatchSpacingMs` has elapsed since this batch started. On `done`, send the
`final` frame to the player sockets **before** writing artifacts, write `results.json` then the
replay, then keep `/healthz` and `/global` answering for a **20 s shutdown grace** before
`quit(0)` (lantern 0.1.3/0.1.4 — a short episode that exits instantly fails the certifier's
post-start `/global` ping).

**Protocol `eleusis.player.v1`** — JSON text frames, unchanged in shape from
`bullwhip.player.v1`:

- game → player: `{"type":"welcome","protocol":"eleusis.player.v1","slot":N,"name":"<alias>","rounds":R,"testEvery":T}` on connect;
  `{"type":"state","slot":N,"name":"<alias>","round":r,"rounds":R,"phase":"research|test|done","score":f,"knowledge":f,"credit":f,"spend":f,"experiments":n,"published":n,"hoarded":n,"correct":n,"answered":n,"pending":{"strip":"RBGY","verdict":"pass"}|null,"boardSize":n,"started":bool,"done":bool,"reason":str}`
  after every event — **redacted to the seat's own numbers**: it never carries `rule`,
  `ruleId`, `truth`, another seat's `secrets`, or another seat's notes. Decisions are
  server-side, so the redaction loses the policy nothing;
  `{"type":"final","done":true,"scores":[5],"names":[5 aliases],"rule":"...","closest":i,"reason":str}`
  at the end, after which the player exits.
- player → game: `{"type":"prompt","prompt":"<≤4000 runes>","scripted":"openbook|hoarder|"}`,
  sent on connect and again after `welcome`.

`src/eleusis_player.nim` — bullwhip's player with an Eleusis default prompt, plus **one fix the
starter needs** (raid 0.1.3, latent in `cogame-bullwhip/src/bullwhip_player.nim`): whisky's
`receiveMessage` **raises** on a close frame or a truncated read, and mummy's `send` only
queues, so the game's `quit(0)` can outrun the flushed `final` frame and the player container
exits 1. Wrap the receive loop in `try/except CatchableError` and **exit 0 on a dead socket**.

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/cogame-bullwhip`.** No mixing —
splicing one starter's shell onto another's emscripten link flags deadlocks the viewer silently
(cogame-lantern, 2026-08-23). Specifically, forked from bullwhip and from nothing else:

- `replay-viewer/config.nims` ← bullwhip's, with the output renamed to
  `eleusis_replay.js`, `-s EXPORT_NAME=EleusisReplayModule`, and
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_el_load_replay,_el_payload_ptr,_el_payload_len,_el_error_ptr,_el_error_len`.
  `MODULARIZE=1`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`,
  `EXPORTED_RUNTIME_METHODS=HEAPU8`, `-d:useMalloc`, `--mm:arc`, `--exceptions:goto` all kept
  verbatim.
- `replay-viewer/eleusis_replay.nim` ← bullwhip's `bullwhip_replay.nim`, exporting
  `el_load_replay` / `el_payload_ptr` / `el_payload_len` / `el_error_ptr` / `el_error_len`,
  parsing the replay with the **same `eleusis/sim`** the server runs, emitting
  `{"type":"replay","protocol","names","policyNames","config","events","results","states"}`
  where `states[i] = benchStateJson(frames[i])`. Keeps
  `emscripten_exit_with_live_runtime()`.
- `replay-viewer/static_replay.js` ← bullwhip's, renamed calls only
  (`EleusisReplayModule`, `_el_*`, `EleusisRenderer.attachReplay`). Its `MODULARIZE`/
  `EXPORT_NAME` bootstrap is paired with the `config.nims` above and must stay paired. Keeps
  the 20 s `AbortController` fetch bound, the Retry button, the `coworld-replay`
  `postMessage` bridge (`loading` → `ready` → `error`), and
  `document.documentElement.setAttribute("data-replay-error", message)` on failure.
- `replay-viewer/index.html` ← bullwhip's, with the wordmark text `BULL<span>WHIP</span>` →
  `ELEU<span>SIS</span>` and the script tag `bullwhip_replay.js` → `eleusis_replay.js`.
  Every id is kept: `#layout #stage #topband #wordmark #clock #topright #statuschip
  #feedtoggle #scorebug #board-wrap #table #lightpool #grain #endscreen #transport #scrub
  #play #pos #feed #loading`.

**Readiness signal.** The renderer sets `document.documentElement.setAttribute(
"data-replay-loaded", "true")` on its **first drawn frame** (bullwhip `renderer.js:1390`,
inside `attachReplay`'s `makeRenderer` callback after the first `draw`), and the shell sets
`data-replay-error` (plus a bridge `error`) on any failure. `tools/ci/viewer_smoke.mjs` and
phase 60 check 8 read exactly those.

**Chrome provenance.** The bullwhip lineage's shared chrome is `client/chrome.css` +
the chrome half of `client/renderer.js`; it has no `client/chrome_common.js` and no
`client/replay_broadcast.html` (those are the paintbot lineage's names for the same two
things, and none of paintbot's files are used here).

- `client/chrome.css` is **copied byte-for-byte** from bullwhip. Existing rules are never
  edited or deleted; the fork only **appends** one `/* ---- eleusis ---- */` block at the end
  (the corkboard/drawer/test-panel/beat-button rules and the 5-plate breakpoints).
- `client/replay.html` (and `client/global.html`) is **bullwhip's page with a game block
  appended** — never a rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The appended
  block is two absolutely-positioned children **inside `#board-wrap`**: `<div id="testpanel">`
  (the prediction-test strip row, HTML so it stays crisp at 360 px) and `<div id="drawer">`
  (the spectator-only hoard drawer). The only edits to existing markup are two text changes:
  the wordmark word and the `<title>`.
- The chrome half of `client/renderer.js` is kept verbatim: `makeNameMap` / `applyNames` /
  `clampName` / `isBaselineFiller` (the two name spaces), `renderFeed` / `blockHead` /
  `escapeHtml`, `bindFeedToggle`, `updateScorebug`, `updateEndscreen` / `reasonLine`,
  `buildScrub`, `attachLive` / `attachReplay` and their pacing loop, `makeEffects`,
  `ellipsize` / `roundRect` / `wrapLines` / `drawBubble`. Only the board-drawing half
  (`computeLayout`, `draw`, `drawBelt`, `drawStation`, the conveyor and seismograph helpers)
  is replaced by the lab bench, and `describeEvent` is rewritten for the new event kinds. The
  global export is renamed `EleusisRenderer`.
- **Elements removed from the starter:** none of the chrome. Bullwhip's replay page ships **no
  `#viewpanel`** (no zoom bar, no minimap) — and the fork **adds none**: the lab bench is a
  fixed composition drawn to fit the canvas at every size, so there is nothing larger than the
  frame to pan. The bullwhip-specific `.plate-backlog` rule is left in `chrome.css` unused
  (byte-for-byte means byte-for-byte); no element is deleted from `replay.html`.

**Transport rules.**

- `relayout()` is added to `renderer.js` and is the only thing that writes layout variables:
  it measures `#transport`'s height and sets `--band` on `:root`, and sets
  `--hudscale = clamp(0.75, stageWidth / 960, 1.25)`. It runs on `load`, on `resize`, and from
  a `ResizeObserver` on `#stage`.
- **Nothing is overlaid in the transport band.** `#testpanel`, `#drawer` and `#endscreen` all
  live inside `#board-wrap`, which is a flex sibling *above* `#transport`; `#endscreen` is
  given `inset: 0 0 var(--band) 0` so the **endcard stops at `var(--band)`** and the scrubber
  stays clickable while it is up.
- **Every seek dismisses the endcard**: `setIndex(next, jumped)` calls `updateEndscreen(…,
  show = index >= events.length && events.length > 0, …)`, so any seek that is not the final
  frame hides it. This is bullwhip's behaviour, kept.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` emits
  `<button type="button" class="beat-marker …" aria-label="…">` with an `onclick` that seeks to
  that event index (pointer drag-to-seek on the track is kept). Beats are emitted for exactly
  five event kinds, and `chrome.css`'s appended block carries a rule for **every one of them**:
  `.beat-experiment` (+ `.seat0….seat4` colours, violet already present),
  `.beat-publish` (paper, taller), `.beat-hoard` (dashed/ghost), `.beat-test` (amber flag) and
  `.beat-end` (`.death`, tallest). Labels read e.g. `round 7 — Gizmo tests RBGY`,
  `round 8 — Gizmo publishes RBGY (PASS)`, `prediction test 2`.

**What the viewer draws** (the lab bench of the idea's replay plan):

1. **Top band** — wordmark `ELEUSIS`, clock reading `ROUND 7 / 24` in research phase and
   `PREDICTION TEST 2 / 4` during a test, `replay` status chip, `LOG »` feed toggle.
2. **Scorebug** — five plates in seat colours: policy name (spectator-side names, aliases
   in-game), score to one decimal with a `$` label, and three chips: `PUB n` (publications),
   `SEC n` (hoarded — dashed border, the spectator-only tell), `+$c` (citation credit).
3. **Canvas centre — the black-box machine.** A squat housing with an intake slot. The strip
   under test slides in from the left as four coloured tokens (the token letters are drawn as
   well as the colour, so it is legible in greyscale), and a rubber stamp drops:
   **PASS** in green or **FAIL** in red, with the author's seat colour on the stamp's rim.
4. **Canvas right — the corkboard.** Published facts as pinned index cards: the four tokens,
   the stamp, a pin in the author's seat colour, and the round number. Newest first; at most
   24 cards visible, older ones fading into a stack labelled `+n earlier`.
5. **Canvas bottom-left — the drawer.** A filing drawer that slides open whenever a
   `disclose` event has `mode: "hoard"`, showing that card with a dashed border, the author's
   colour, and a `SECRET · SPECTATORS ONLY` tag. It closes again after the beat. Duplicated
   publications land on the corkboard with a `CONFIRMED` overprint and no pin.
6. **`#testpanel`** (HTML, over the board, above the band) — during and after a test: the six
   strips in a row, each with five answer pips underneath in seat colours (filled = correct,
   hollow = wrong, greyed until the test settles) and the machine's truth stamp revealed at
   settlement.
7. **Feed** — `ROUND 7` heads; `Gizmo tests RBGY` / `→ PASS (private)`;
   `Gizmo pins RBGY · PASS to the corkboard`; `Widget slides RRGY · FAIL into the drawer`;
   `Widget: "ADJACENT R B?"` (hypothesis, in the seat's colour);
   `PREDICTION TEST 2 — Sprocket 5/6, Gizmo 3/6, …`;
   `Gizmo's RBGY cited by Widget  +$0.50`; `THE RULE WAS ADJACENT R B`.
8. **Endcard** (`#endscreen`) — title `THE RULE WAS`, verdict = the full `ruleText`, then a
   row per seat sorted by score: rank, name, score, prizes, credit, spend, accuracy `9/12`,
   `PUB/SEC`. The winner's row is highlighted; the `.end-reason` line reads
   `closest: Widget — 11 of 12 predictions · ended complete`.

**Legibility at 360 px** (the featured-match iframe width — checked at 360, not at desktop):
`.plate-name` keeps `flex: 1 1 auto; min-width: 3.2em`; `#scorebug` goes to
`repeat(3, 1fr)` under 640 px and `repeat(2, 1fr)` under 420 px (5 plates wrap, none is
dropped); `.plate-label` hides under 640 px, the `SEC`/credit chips stay (they are the drama);
the corkboard drops to the 8 most recent cards and the drawer collapses to a
`SECRETS n` chip; `#testpanel` keeps the six strips and the pips and drops its captions.
Tokens are drawn as coloured chips **with their letter**, and verdicts are the words `PASS`
and `FAIL`, never `P`/`F` — a casual spectator must read it.

## Packaging

- `compose.yaml` — service `eleusis`, `image: coworld-eleusis:latest`,
  `platform: linux/amd64`, `build: {context: ., network: host}`. The manifest image
  placeholder is derived from the compose **service** name: `{{ELEUSIS_IMAGE}}` (lantern
  0.1.0 — `{{GAME_IMAGE}}` is not a thing).
- `Dockerfile` → `/bin/eleusis` and `/bin/eleusis-player`; `Dockerfile.replay-viewer` →
  pinned `emscripten/emsdk:4.0.15` + nimby 0.1.27 / Nim 2.2.4, exactly bullwhip's.
- `tools/build_replay_viewer.sh` — bullwhip's hook, committed **mode 100755**, with the
  ecos 2026-08-23 fix: `mkdir -p` the output dir's parent **before** the containment check
  (CI runs it on a fresh checkout where `coworld build`'s pre-created parent does not exist).
  It bundles `eleusis_replay.js`, `eleusis_replay.wasm`, `replay-viewer/index.html`,
  `replay-viewer/static_replay.js`, `client/renderer.js`, `client/chrome.css` and
  `data/*` into `assets/`.
- `coworld_manifest_template.json` — `$schema`, ≥3 `tags`
  (`science`, `hypothesis-discovery`, `mixed-motive`, `llm-driven`, `turn-based`,
  `five-player`, `epistemics`, `publish-or-hoard`), `episode_timeout_minutes: 20` top level,
  `game.name: "eleusis"`, `game.runnable.type: "game"`, `image {{ELEUSIS_IMAGE}}`,
  `run ["/bin/eleusis"]`,
  `env.ANTHROPIC_API_KEY_URI: "secret://coworld/eleusis/anthropic_api_key"` (hive,
  2026-08-23 — without it the hosted container never sees the secret and every league episode
  plays scripted), `source_url https://github.com/Metta-AI/cogame-eleusis/tree/main`, and
  `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- `game.config_schema` — a real JSON Schema: `tokens`/`players` `minItems: 5, maxItems: 5`;
  `num_agents` integer `minimum: 5, maximum: 5`; `seed`; `rounds` 4..60 default 24;
  `testEvery` 2..20 default 6; `testStrips` 2..12 default 6; `experimentCost` 0..10 default
  1.0; `knowledgePool` 0..200 default 20.0; `citePot` 0..10 default 0.5;
  `episodeTimeoutSeconds` 60..6000 default 1200; `minBatchSpacingMs` 0..60000 default 12000;
  `turnDelayMs` 0..10000 default 0; `model`; `maxOutputTokens` 64..2000 default 900;
  `llmTimeoutSeconds` 5..300 default 40; `player_connect_timeout_seconds` default 180.
  `additionalProperties: false`, and every variant + the cert fixture must validate against it.
- `game.results_schema` — the `resultsJson` shape above; `scores` unbounded numbers (this
  game's sign is positive-is-better and values may be negative), `reason` enum
  `["complete", "deadline"]`.
- `game.protocols` — **both** keys: `player` (the full `eleusis.player.v1` frame-by-frame text,
  including "a policy is just a prompt" and the `PLAYER_PROMPT`/`PLAYER_SCRIPTED` contract) and
  `global` (the `/global` snapshot shape = `benchStateJson` + `type`/`game`/`policyNames`/
  `events`/`started`/`done`/`connected`, and the note that `rule`, `truth` and `seats[].secrets`
  are spectator-only).
- `game.docs` — `readme` (`{"type":"text","value":…}`) plus `pages: [{"id":"rules.md",
  "title":"rules.md","content":{"type":"text","value":…}}, {"id":"economy.md","title":
  "economy.md","content":{…}}]`. `rules.md` carries the full catalogue table and the numbered
  resolution order; `economy.md` carries the scoring formula, the citation rule and the tuned
  ratio.
- `player[]` (top level, each with `id`/`type`/`name`/`description`/`image`/`run`/`resources`/
  `source_url`): `eleusis-player` (prompt player, no `PLAYER_SCRIPTED`),
  `eleusis-openbook` (`env.PLAYER_SCRIPTED=openbook`), `eleusis-hoarder`
  (`env.PLAYER_SCRIPTED=hoarder`). All three run `/bin/eleusis-player` from
  `{{ELEUSIS_IMAGE}}`.

**Variants — `num_agents: 5` in every one:**

| id | name | description | game_config |
|---|---|---|---|
| `standard` | Standard laboratory | Five cogs, 24 rounds, a prediction test every 6, citation pot $0.50. | `players: [5 named entries]`, **`num_agents: 5`**, `rounds: 24`, `testEvery: 6`, `testStrips: 6`, `experimentCost: 1.0`, `knowledgePool: 20.0`, `citePot: 0.5`, `minBatchSpacingMs: 12000`, `player_connect_timeout_seconds: 180` |
| `open-science` | Open science | Citation credit tripled to $1.50: publishing should dominate. | same, **`num_agents: 5`**, `citePot: 1.5` |
| `closed-shop` | Closed shop | Citation credit cut to $0.10: hoarding should dominate. | same, **`num_agents: 5`**, `citePot: 0.1` |

**Certification fixture** — `certification.game_config`: `players: [{"name":"Sprocket"},
{"name":"Gizmo"},{"name":"Ratchet"},{"name":"Widget"},{"name":"Bolt"}]`, **`num_agents: 5`**,
`seed: 11`, `rounds: 6`, `testEvery: 3`, `testStrips: 6`, `turnDelayMs: 0`,
`minBatchSpacingMs: 0`, `player_connect_timeout_seconds: 180`.
`certification.players`: `[{"player_id":"eleusis-player"},{"player_id":"eleusis-openbook"},
{"player_id":"eleusis-player"},{"player_id":"eleusis-hoarder"},{"player_id":"eleusis-player"}]`
— **every declared player runnable occupies at least one slot** (raid 0.1.2 → 0.1.3: a fixture
that seats only baselines fails `players-run` with `players_missing`). Six rounds × 5 seats +
2 tests ≈ 80 events ≈ 36 s of replay at the renderer's pacing, comfortably outlasting the
10 s `--soak` window (ecos, 2026-08-23). `<SEATS>` in `tools/ci/docker_smoke.sh` is **5**.

**Policies** (`tools/ci/policies.json`; both champions are `PLAYER_PROMPT`, both fillers are
`PLAYER_SCRIPTED`):

| role | name | env |
|---|---|---|
| champion #1 (daveey) | `eleusis-empiricist` | `PLAYER_PROMPT`: *"Treat the catalogue as a version space. Every turn, write in your notes the shortlist of catalogue entries still consistent with EVERY fact you know — your own results and the corkboard — and test the strip that would split that shortlist closest to in half. Publish a result when your shortlist is still long and the strip is far from anything on the board: early facts near unexplored strips earn citations for the rest of the game. Once your shortlist is down to two or three entries, hoard: you are about to out-score everyone on the test and you gain nothing by teaching them. Never re-publish something already on the board — it pays nothing."* |
| champion #2 (daveey-1, `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) | `eleusis-guarded` | `PLAYER_PROMPT`: *"Play secretive but not blind. Assume rivals publish honestly, and mine the corkboard hard: cross off every catalogue entry it contradicts before you spend a dollar. Spend on strips whose verdict the corkboard cannot already imply, and hoard by default. Publish only a FAIL you are confident is uninformative to a rival's shortlist but sits one token from many untested strips — that buys citations without buying them a prize share. State a deliberately vague hypothesis line; it is public and non-binding."* |
| filler | `eleusis-openbook` | `PLAYER_SCRIPTED=openbook` |
| filler | `eleusis-hoarder` | `PLAYER_SCRIPTED=hoarder` |

**Art (real, not placeholders).** `data/font.ttf` and the four cog sprites are copied from
bullwhip's `data/` (MIT, via coworld-ctf) as `cog_red_front.png`, `cog_blue_front.png`,
`cog_green_front.png`, `cog_yellow_front.png`. Two new pieces are generated with nano-banana
per `playbooks/art-nanobanana.md`, in the same ink-and-print palette
(`#f2e8d8` paper, `#2a1f16` ink, `#e8a33d` amber): `cog_violet_front.png` (the fifth seat —
`chrome.css` already defines `.seat4 { --tc: var(--violet); }`) and `bench_surface.png` (the
lab-bench worktop and the machine housing, replacing `arena_floor.png`).

### Phase 0 pins, and how each is satisfied

| pin (`playbooks/make-coworld.md` §Phase 0) | how this design satisfies it |
|---|---|
| Starter by game shape | Turn-based, native rules, policy = LLM prompt → the parley lineage's newest member, `cogame-bullwhip`; N simultaneous seats per turn is bullwhip's exact loop. |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-eleusis`, public (a private repo 404s `source-resolves` at certification). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (2 champions) vs `PLAYER_SCRIPTED=openbook|hoarder` (2 fillers), all four from `{{ELEUSIS_IMAGE}}` running `/bin/eleusis-player`. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; the bundle re-derives every frame in the browser from the replay bytes; no `/client/replay` pod viewer is ever declared. |
| Real art, starter chrome verbatim | `chrome.css` byte-for-byte + appended block; `replay.html` = starter page + appended game block; `renderer.js` chrome half verbatim; two nano-banana pieces + bullwhip's sprites. |
| Two name spaces | Seeded `CogNames` aliases in every prompt and every player frame; `policyNames` ride alongside in the replay and are what the scorebug, feed and endcard render; `resultsJson.names` are policy names. |
| Degrade-never-hang, play inside 60 % of 1200 s | 28 batches × 12 s ≈ 336 s ≈ 51 % of the 720 s play budget; deadline checked before every batch; `endEarly` settles `deadline`; retry-once-then-scripted on every decision. |
| `num_agents` in every variant and the cert fixture | `num_agents: 5` in `standard`, `open-science`, `closed-shop` **and** `certification.game_config`; `SMOKE_SEATS`/`<SEATS>` = 5 cross-checks it in `docker_smoke.sh`. |
| Legible to a casual spectator | Words, not notation: `PASS`/`FAIL` stamps, `ROUND 7 / 24`, `$6.50`, coloured tokens with letters; checked at 360 px. |

## Tests

`ci.yml` (from `templates/ci.yml`, `<slug>` = `eleusis`, `<IMAGE>` = `coworld-eleusis`,
`<SEATS>` = `5`) is the only harness — the sandbox has no Nim, no Docker, no browser. Every
`tests/*.nim` runs twice, debug and `-d:release`.

**`tests/test_sim.nim` (sim unit tests)**

1. `catalogue().len == 68`, the enumeration order is stable, and `describeRule` is unique per
   instance.
2. `evaluate` truth table: at least three hand-written strips per template family, PASS and
   FAIL, including the edge cases `rkAdjacent` with `c = d` (`"RRBG"` passes `ADJACENT R R`),
   `rkParity` with count 0 = even, `rkBefore` requiring both colours present, `rkMoreThan`
   ties failing.
3. `pickRule(seed)` is deterministic per seed, and for 200 seeds the chosen rule's
   `passFraction` is always within `[0.10, 0.90]`.
4. Turn resolution: an experiment charges exactly `experimentCost` once, records the verdict,
   and adds the strip to `used`; a skip charges nothing; a second decision by the same seat in
   the same turn raises `EleusisError`.
5. Disclosure: publish pins a fact with the author; publishing a strip already on the board
   records `mode: "duplicate"`, gives no authorship and pays no credit ever; hoard adds to
   `seats[].secrets` and never to `board`.
6. Test draw: strips are held out from `used` **and** from earlier tests, and are exactly
   `testStrips/2` PASS and `testStrips/2` FAIL.
7. Knowledge pool: shares sum to `knowledgePool` when anyone is correct and to 0 when nobody
   is; a hand-computed 5-seat case.
8. Citation credit: a hand-built board proves (a) Hamming-1-only support, (b) self-citation
   never pays, (c) an author paid once per (strip, confirmer) however many facts support it,
   (d) the pot splits equally among multiple authors, (e) a wrong answer pays nobody,
   (f) a fact published *after* the test opened pays nothing.
9. Scoring: `score = knowledge + credit − experimentCost × experiments`, sign checked against a
   hand-computed episode; a seat that only spends finishes negative.
10. Endings: `complete` after the final test; `endEarly` mid-turn settles `deadline`, discards
    an unfinished test unscored, and leaves earlier tests scored.
11. Replay: `replayMatch(config, events).len == events.len + 1`; the final frame equals the
    live `benchStateJson`; a tampered `test` event raises; `eventToJson`/`eventFromJson` round
    trip for all nine kinds.
12. Rune-safe truncation: a `hypothesis` of 200 multi-byte runes and `notes` of 900 truncate to
    120/600 **runes** and the resulting `$replayJson` decodes as strict UTF-8.

**`tests/test_bot.nim` (bounded-orders / legality assertion on the scripted baselines)**

13. For ≥ 5 seeds, five baseline seats (mixed `openbook`/`hoarder`) play a full episode to
    `reason == "complete"`, and **every** decision they emit is legal *before* the sim is asked
    to apply it: `experiment` is `""` or exactly 4 characters all in `RBGY`; `answers` has
    exactly `testStrips` entries, each `pass`/`fail`; `hypothesis` ≤ 120 runes; `notes` empty.
14. Learning sanity: with five `openbook` seats the version-space predictor scores ≥ 70 %
    correct on the final test, averaged over 10 seeds — proof the baseline is a real opponent,
    not a coin flip.
15. `hoarder` publishes exactly zero facts; `openbook` publishes every non-duplicate result.
16. `decideAll` with a disabled (credential-less) client returns a scripted decision for every
    seat, raises nothing, and makes no network call.
17. Reply parsing: `{"experiment":"rb gy"}` normalises to `RBGY`; `"RBG"`, `"RBGZ"`,
    `{"answers":[…5 entries]}` and a non-object reply are all rejected.

**`docker-smoke` job (end-to-end episode writing a replay + strict-UTF-8 parse)**

18. `tools/ci/docker_smoke.sh` (committed **mode 100755**) builds the image, reads the seat
    count solely from `certification.game_config.num_agents`, cross-checks it against
    `SMOKE_SEATS=5`, runs the fixture episode in raw docker with one player container per seat
    and **no** `ANTHROPIC_API_KEY` (so the scripted path is what must complete), asserts the
    game container exits 0, `results.json` is valid UTF-8 JSON with 5 `names`/`scores`,
    `reason ∈ {complete, deadline}`, and the replay **parses as strict UTF-8 JSON**
    (`json.loads(path.read_bytes().decode("utf-8"))`, already in the template).
19. Fork addition to the smoke script: assert **every player container's** exit code is 0, not
    just the game's (raid 0.1.4 — a player that dies on a closed socket is a real certification
    failure the starter's smoke does not catch).
20. The replay is uploaded as the `smoke-replay` artifact.

**`wasm-viewer` job (viewer smoke — the bundle is EXECUTED, not merely built)**

21. Asserts `tools/build_replay_viewer.sh` and `tools/ci/viewer_smoke.mjs` exist and the hook
    is executable, builds the bundle, asserts `index.html` + a non-empty `.wasm`, then
    `needs: docker-smoke` downloads that episode's replay and runs
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <the smoke
    replay> --timeout 90 --soak 10` in headless chromium (Playwright pinned 1.55.0). Green
    requires `data-replay-loaded="true"`, three differing clock readouts across the 0 %/50 %/
    100 % scrubs, and an un-frozen soak. `viewer-smoke.png` / `viewer-smoke.json` are uploaded
    always.

## Out of scope (v1)

- Multi-clause rules (conjunctions, disjunctions, negations of catalogue entries) and rules
  over variable-length strips — v1 is one catalogue entry over 4-token strips, so the search is
  hard but finite and the prompt can state the whole hypothesis space.
- Any seat-to-seat channel: no messages, no trades, no side payments, no contracts. The only
  communication is the corkboard and the public hypothesis line.
- Peer review, retraction, or *false* publication: a published fact is always the true machine
  verdict. Lying with evidence is a v2 game.
- Buying another seat's hoarded result, or any market in secrets.
- Grants, budgets or borrowing: experiments are charged against score with no cash constraint,
  so a seat can always afford to act.
- Cross-episode memory, ELO-aware play, or any persistence between episodes.
- Live spectator interaction and the `/client/global` live page beyond parity with bullwhip's
  (the static replay bundle is the product; the live page exists for certification and local
  debugging).
