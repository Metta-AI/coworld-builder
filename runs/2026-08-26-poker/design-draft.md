# OS Poker — the imperfect-information ladder (Kuhn → Leduc → no-limit Hold'em)

**Starter: `Metta-AI/cogame-cosino`** (parley lineage: parley → cosino → focus → babel → bullwhip).
Cosino already is this game's bottom two thirds: no-limit Texas Hold'em for 2–6 cogs on the
parley stack, a pure `sim` module shared by server/tests/wasm viewer, prompt-is-the-policy
decisions with an always-legal scripted fallback, anonymous cog aliases, a felt-table canvas
renderer and all four static-replay-viewer files. **Every convention there holds here unless this
note says otherwise.** Cosino is not mounted in the sandbox; it was fetched read-only for this
note (`gh api repos/Metta-AI/cogame-cosino/tarball/main`) and every file named below was read at
commit `5b63443`. Where cosino's conventions lag the current template pins, **`cogame-babel`
(`/workspace/starters/cogame-babel`, 0.1.4) is the current standard** and this note names the
exact upgrade; babel supplies *no* viewer file, only the shape of three specific behaviours
(§Viewer, "Upgrades").

Why a new repo rather than a PR to cosino: established pipeline precedent — an EXTENSION idea
ships as a new `cogame-<slug>`, with the base repo as the scaffold and reference. Cosino keeps
running as the single-table Hold'em coworld; `cogame-poker` is the ladder.

**Source idea (verbatim, Asana idea task 1217747803484730):**

> OS Poker (mod of cogame-cosino) — add Kuhn/Leduc calibration tables and a 6-max collusion audit to the live Hold'em
>
> EXTENSION of Metta-AI/cogame-cosino — Cosino already ships no-limit Texas Hold'em for 2-6 cogs on the parley stack (fixed buy-in, blinds, side pots, scripted Chen-formula baseline; chip share is the score). Don't build a new poker coworld.
>
> Mods to add to Cosino:
>     Kuhn and Leduc tables as manifest variants (OpenSpiel kuhn_poker / leduc_poker rules): solvable games with known Nash strategies, so a cog's exploitability can be measured exactly — a calibration rung below Hold'em.
>     Duplicate decks: seed the same card sequence across mirrored seatings in a round to cut variance (bridge-style duplicate scoring).
>     6-max collusion audit: chip dumping / soft play between seats is the real league threat; compute per-seat equity-loss-vs-opponent stats and flag pairs; randomise seating each episode.
>     Optional heads-up mode as the clean ladder.
>
> Seats: 2 (HU) / 6 (6-max) — as Cosino
> Motive: zero-sum, imperfect information
> Policy interface: Cosino's prompt-is-the-policy protocol, unchanged
> Fills gap: turns Cosino into the imperfect-information *ladder* (Kuhn → Leduc → NLHE) rather than one table
>
> Source: OpenSpiel kuhn_poker / leduc_poker / universal_poker; PettingZoo texas_holdem_no_limit_v6; github.com/Metta-AI/cogame-cosino.

Operator note (data, binding intent): on the idea, the human commented *"This seems like it's
already partially done in Cosino, can we just extend it with other games?"* — so this design
reuses cosino's engine, protocol, chrome and viewer wholesale and adds the two lower rungs, the
duplicate deck, and the audit.

---

## The game

Three rungs of the same zero-sum imperfect-information game, one binary, one protocol, four
manifest variants. A cog climbs: Kuhn (12 information sets, exactly solvable) → Leduc (a few
hundred, exactly solvable) → no-limit Hold'em heads-up → no-limit Hold'em 6-max.

### 1. What is the same at every rung

1. **Hands, not a chip race.** Every hand starts with every seat holding exactly
   `startingStack` chips. There are no busts, no rebuys, no seats sitting out. A seat's result is
   its cumulative **net chips** across the hands it played. *Reason (this is the one rule change
   from cosino, which carried stacks and felted seats):* duplicate scoring requires that the two
   hands of a mirrored pair start from identical conditions, and the collusion audit needs all six
   seats live for the whole episode. Both die if stacks carry and seats bust out.
2. **Duplicate decks.** Hands are played in **pairs**. Hands `2k` and `2k+1` are dealt from the
   *same* shuffled deck; in the mirror hand the whole table rotates by half a table, so each seat
   gets the cards *and* the position its counterpart had. Deal luck cancels inside the pair.
3. **Randomised seating.** At match init a seed-derived permutation `seatOrder` maps table
   positions to slots. Slot `s` sits at position `p` where `seatOrder[p] == s`. A colluding pair
   cannot count on a fixed relative position.
4. **One actor at a time.** Poker is sequential: exactly one seat is on decision at any moment,
   and one decision costs one model call. Budgeting is therefore per-decision, not per-turn
   (§Decisions).
5. **Anonymous aliases in-game.** Seats play as Sprocket, Gizmo, Ratchet, Widget, Bolt, Piston …
   (cosino's `CogNames` pool, seed-shuffled). No policy name ever enters a prompt.
6. **Table talk.** Every decision may carry one short public line (`say`, ≤ 160 characters).
7. **Score.** See §Scoring below — one formula for all four variants.

### 2. Rung 1 — `kuhn` (2 seats)

OpenSpiel `kuhn_poker` rules, exactly.

1. Deck: three cards — J♠, Q♠, K♠ (card ints 39, 43, 47 in cosino's 0–51 encoding:
   `rank = card div 4` with 0 = deuce … 9 = J, 10 = Q, 11 = K; `suit = card mod 4`, 3 = spades).
2. Both seats ante **1**. Pot = 2. No blinds.
3. One private card each, dealt to position 0 then position 1 from the shuffled deck.
4. One betting round. **Bet size is fixed at 1. At most one wager per round** (a bet; no raise).
5. Acting order: **position 0 (the button) acts first** — OpenSpiel's `firstPlayer = 0`.
6. Legal sequences and payoffs (`p` = check/pass, `b` = bet 1):
   - `pp` → showdown for the 2-chip pot; higher card wins; net ±1.
   - `pbp` → the bettor wins the 2-chip pot uncontested; net ±1.
   - `pbb` → showdown for the 4-chip pot; net ±2.
   - `bp` → the bettor wins the 2-chip pot; net ±1.
   - `bb` → showdown for the 4-chip pot; net ±2.
7. There is no split: the three cards are distinct.
8. 60 hands (30 duplicate pairs) per episode.

### 3. Rung 2 — `leduc` (2 seats)

OpenSpiel `leduc_poker` defaults, exactly.

1. Deck: six cards — J, Q, K in two suits (spades and hearts): card ints 39, 43, 47 (spades) and
   38, 42, 46 (hearts).
2. Both seats ante **1**. Pot = 2.
3. One private card each (position 0 then position 1).
4. **Round 1**: fixed bet size **2**, **at most 2 wagers** (an opening bet and one raise; facing
   the raise a seat may only call or fold). Position 0 acts first (`firstPlayer = 0`).
5. If both seats are still in, one **public board card** is turned from the remaining deck.
6. **Round 2**: fixed bet size **4**, at most 2 wagers. Position 0 acts first again — this
   matches OpenSpiel's `leduc_poker`, which does not switch the first actor between rounds. (It
   differs from Hold'em convention; the calibration rungs follow OpenSpiel so exploitability
   numbers are comparable with published ones.)
7. Showdown: a private card of the same rank as the board card is a **pair** and beats any
   unpaired hand; between two unpaired hands the higher rank wins; identical ranks **split** the
   pot (odd chip to position 0).
8. A fold ends the hand; the folder forfeits everything it committed.
9. 36 hands (18 duplicate pairs) per episode.

### 4. Rung 3 — `holdem-hu` (2 seats) and `holdem-6max` (6 seats)

Cosino's no-limit Texas Hold'em, unchanged in every betting detail (`src/cosino/sim.nim`:
`initHand`, `applyAction`, `progress`, `resolveHand`, `refundUncalled`, side pots by commitment
level, split pots with the odd chip clockwise from the button, min-raise rules, a short all-in
that does not re-open betting unless short increments accumulate to a full raise), with exactly
three changes:

1. Stacks reset to `startingStack` (100) at the start of every hand; `isOut`/`bust` no longer
   remove a seat from the game (see §Sim module for the replacement `stackOff` event).
2. Duplicate pairing and `seatOrder` as above.
3. Blinds 1/2, never escalating. Heads-up: the button posts the small blind and acts first
   preflop, last postflop (cosino's rule, kept).

`holdem-hu`: 30 hands (15 pairs). `holdem-6max`: 16 hands (8 pairs).

### 5. Duplicate mirroring, exactly

- Deck for pair `k`: `initRand(seed*104729 + k*7919 + 13)` shuffled over the variant's deck
  (`shuffledDeck` for Hold'em; the 3-card and 6-card decks for Kuhn/Leduc).
- Base hand `2k`: positions are filled by `seatOrder`; the button sits at position 0; cards are
  dealt in cosino's order (Hold'em: two at a time clockwise from the small blind; Kuhn/Leduc: one
  each from position 0).
- Mirror hand `2k+1`: **the same deck, the same deal procedure, the same button position**, and
  the position map rotated by `n div 2`:
  `seatOrderMirror[p] = seatOrder[(p + n div 2) mod n]`. Heads-up (`n = 2`) this is an exact swap
  — each seat plays the other's cards from the other's seat. At `n = 6` it is a 3-position
  rotation: a partial but unbiased mirror (every seat trades cards and position with the seat
  across the table). *Reason for 2 mirrors and not `n`:* a full 6-mirror rotation would cost 6×
  the hands and blow the decision budget six ways; two mirrors already remove the dominant
  deal-luck term and keeps the hand count even.
- **The mirror is invisible to the seats.** A seat's observation carries only the *current*
  hand's history plus cumulative net standings — never a cross-hand card transcript (this is
  already how cosino builds prompts: `renderHistory(sim)` walks `sim.events`, which are per-hand).
  The server holds no per-seat memory between decisions, so a seat cannot recognise a repeated
  deck. The replay and the spectator feed *do* label mirror hands; that is a spectator affordance
  only.

### 6. Scoring — one formula, all variants

Let `n` = seats, `S` = `startingStack`, `H` = hands actually scored (completed hands; a hand
voided by the hard deadline is not scored and its chips are refunded), and `net[i]` = seat `i`'s
cumulative (chips won − chips committed) over those `H` hands. `Σ net[i] = 0` exactly (zero-sum;
a chip-conservation test enforces it).

```
scores[i] = 1/n + net[i] / (n * S * H)          # higher is better
win[i]    = (net[i] == max(net))                 # ties: every tied seat true
```

- The range is exactly `[0, 1]` with no clamping: the best possible net is `(n−1)·S·H` → 1, the
  worst is `−S·H` → 0. `Σ scores = 1`. At `H = 1` it degenerates to cosino's chip share, so the
  two coworlds' numbers are on the same axis.
- **Sign: positive is winning.** A seat that breaks even scores exactly `1/n`.
- Results also carry the legible raw figures: `net[]`, `netPerHand[]`, and
  `unitsPerHand[] = net[i] / (unit * H)` where `unit = bigBlind` for Hold'em and `unit = ante`
  (= 1) for Kuhn/Leduc.
- **What the league ranks by:** the platform's Elo over `scores`, in **one league across all four
  variants, equally weighted, scheduled round-robin.** *Reason:* the score is unit-free (a share
  of the same virtual bankroll whatever the rung), so a Kuhn episode and a 6-max episode
  contribute the same amount of Elo, and a single leaderboard is what makes this a *ladder*
  rather than three unrelated boards. Exploitability and the audit are recorded **diagnostics**
  in `results`, never inputs to the ranking — that keeps a noisy metric out of the Elo.

### 7. Exploitability (the calibration rungs)

Measured exactly, for `kuhn` and `leduc` only. For the Hold'em rungs `results.exploitability[i]`
is `null` — no exact best response exists at NLHE scale, and this note will not pretend otherwise.

1. **Empirical strategy.** Every decision a seat makes is tagged with its *information set* — the
   canonical `(position, private card(s), board card, betting history)` key of the variant's game
   tree. Over the episode this yields, per seat, observed action counts at each infoset, split by
   the position it played: `σ_i^0` (as position 0) and `σ_i^1` (as position 1). Frequencies are
   the empirical mixed strategy.
2. **Unvisited infosets are filled**, and the fill is recorded: Kuhn fills with the known Nash
   strategy at α = 1/6 (`exploitabilityFill: "nash"`); Leduc fills uniformly over legal actions
   (`exploitabilityFill: "uniform"`) — Leduc has no closed-form equilibrium to fill with.
   `exploitabilityCoverage[i]` reports the fraction of reachable infosets the seat actually
   visited, so a thin sample is visible rather than hidden.
3. **Exact best response.** `src/poker/solve.nim` enumerates the whole game tree (Kuhn: 6 deals,
   12 infosets; Leduc: 30 private deals × 4 board cards, a few hundred infosets) and computes the
   best-response value against a fixed opponent strategy by backward induction over reach
   probabilities. Cost: microseconds for Kuhn, < 50 ms for Leduc. No sampling, no CFR.
4. **The number.** Using the duplicate framing, define
   `v_i = ½·[ u0(σ_i^0, BR1(σ_i^0)) + u1(BR0(σ_i^1), σ_i^1) ]` — the seat's expected chips per
   hand when it plays both sides of the table against a perfect exploiter.
   **`exploitability[i] = −v_i`, in chips per hand, and it is ≥ 0 with equality iff the seat's
   empirical strategy is unexploitable at both positions.** The positional value of the game
   cancels in the average, so this needs no precomputed game value and works for Leduc, whose
   value is not a round number.
5. Reported per seat in `results.exploitability[]` and drawn on the endcard; also emitted as one
   `calib` event per seat at the tail of the event log so the replay viewer shows it without
   re-solving.

### 8. Collusion audit (6-max)

Runs when `n ≥ 3` — i.e. `holdem-6max`. For 2-seat variants `results.audit` is
`{"pairs": [], "flagged": [], "power": {...}}`. It is a **pure function of the event log plus the
seed**, so the server and the wasm viewer compute identical output (`auditFromEvents(config,
events)` lives in the sim module and is called by both; a test asserts byte-identical JSON).

**Equity.** For a pot slice, a seat's equity is its exact win-share probability given every live
seat's actual hole cards and the cards still to come, splits counted fractionally. With a
complete board it is a single exact evaluation. With cards to come it is Monte-Carlo with
**2000 runouts** drawn from `initRand(seed*1_000_003 + hand*97 + sliceIndex)` — deterministic and
re-derivable from the replay bytes (the deal events carry every hole card and the seed is in the
replay config).

**Per-hand surrender.** For every pot slice with contributor set `C` (seats whose chips are in
that slice) and contributions `contrib_c`:

- *Showdown slices.* Measure each contributor's equity `eq_a` at the instant the last betting
  action of the hand completed. `loss_a = eq_a · S_slice − actual_a`, where `actual_a` is the
  chips the slice actually paid `a` (0 for a seat that folded earlier).
- *Folds.* When seat `a` folds, measure `eqFold_a` against the hands still live at that moment
  with the then-unknown board sampled as above:
  `loss_a = max(0, eqFold_a · potAtFold − callCost_a)`, where `callCost_a` is the chips `a` would
  have had to put in to continue. Folding correctly scores ≈ 0; folding a hand that was worth
  more than the price scores the difference.
- *Attribution.* `surrender[a][b] += max(loss_a, 0) · contrib_b / Σ_{c∈C, c≠a} contrib_c`.
- `contested[a][b]` counts hands in which `a` and `b` both contributed to a common slice.
- `flow[a][b]` (reported, not used for flags) is the pro-rata directed chip flow: a slice of size
  `S` won by `b` credits `S · contrib_c / Σ contrib` to `flow[c][b]` for every other contributor
  `c`; `netFlow[a][b] = flow[a][b] − flow[b][a]`.

**Rates and the flag rule.**

```
rate[a][b]  = surrender[a][b] / max(contested[a][b], 1)          # chips per contested hand
field[a]    = Σ_{c≠a} surrender[a][c] / max(Σ_{c≠a} contested[a][c], 1)
bias[a][b]  = rate[a][b] − field[a]      # how much more of its equity a leaks to b than to the field
```

- **`soft-play`** on the unordered pair {a,b} when
  `contested[a][b] ≥ 4` **and** `min(bias[a][b], bias[b][a]) > 0.75 · bigBlind`
  (both directions leak — mutual soft play, not one seat running the other over).
- **`dump-a-to-b`** (directed) when `contested[a][b] ≥ 4` **and** `bias[a][b] > 2.0 · bigBlind`.
  Chip dumping is one-directional, so it gets its own, higher threshold.
- A pair may carry both flags; `flagged` lists each flag once with its numbers.

The audit is **reporting only** — it never alters scores, never disqualifies a seat. Every flagged
pair is written as one `audit` event at the tail of the event log (feed line, scrubber beat,
endcard row) and into `results.audit`. `results.audit.power` carries
`{hands, contestedMin, contestedMedian, equitySamples: 2000}` so a 16-hand episode's flags are
read as the weak evidence they are; the league aggregates across episodes, which is out of scope
for v1 (§Out of scope).

### 9. End conditions

The episode ends, always writing `results.json` and a replay, in exactly one of three ways.
`results.reason` is one of **`complete`**, **`deadline`**, **`budget`** — no other value is legal
and the results schema declares the enum.

1. **`complete`** — the variant's hand limit is reached (the last duplicate pair finished).
2. **`deadline`** — wall clock. Two guards, both derived from `episodeTimeoutSeconds` (assume
   1200 s; the game container is *not* given `COWORLD_TIMEOUT_SECONDS`, so 1200 is the assumption
   when the env var is absent):
   - *soft*, checked after every completed **pair**: if `now > gameStart + 0.60·T` (720 s), stop
     and score the completed pairs.
   - *hard*, checked before every decision: if `now > gameStart + 0.70·T` (840 s), abandon the
     hand in progress, refund every chip committed in it (that hand is not scored, `H` excludes
     it), record a `handVoid` event, stop. The refund keeps `Σ net = 0`.
3. **`budget`** — the decision budget (`EpisodeDecisionBudget = 220` model calls) is exhausted;
   same settle path as the soft deadline, at a pair boundary.

A seat that never connects is not an end condition: after `player_connect_timeout_seconds`
(180 s) the game starts anyway and every unconnected seat plays the scripted baseline
(cosino's behaviour, kept). `results.reason` is still one of the three above.

### 10. Per-seat observation — visible and hidden

Rebuilt fresh for each decision by `userPrompt` (cosino's shape, extended). **Visible to the
acting seat:**

- Its own private card(s), rendered as text (`As`, `Kh`; the *viewer* renders "10", the prompt uses
  poker shorthand).
- The public board (Leduc: the one board card once turned; Hold'em: the flop/turn/river so far).
- The pot, its own chips-in-front, and every seat's stack, chips-in-front, folded/all-in state,
  and which position holds the button.
- The complete public history of **the current hand** in reading order: antes/blinds, every
  action with its amount, every `say` line, board cards, reveals.
- Cumulative standings: every seat's net chips so far and hands won, by alias.
- Hand number, hand limit, variant name and the variant's rules, blinds/antes and (fixed-limit
  rungs) the exact wager size and the wager cap.
- **The precomputed legal action set with exact amounts** — `fold`, `check` or `call <price>`,
  `bet <min>..<max>` or `raise <minTo>..<maxTo>`, `allin` — computed by the same predicates
  `applyAction` validates with. (Escrow 2026-08-23: precomputing the legal set is what stops
  formal-output fallbacks; cosino already does this in `actionInstruction` and it is kept.)

**Hidden from the acting seat:** every other seat's private cards until a showdown reveals them
(cosino's `redactCards` on the player websocket, kept, and the prompt only ever renders the
viewer's own deal); folded hands, which are never revealed to anyone but the replay; the deck and
the undealt cards; the duplicate pairing and the mirror mapping; any transcript of previous
hands; every policy's real name; the audit and exploitability numbers.

Spectators (`/global`, the replay, the static viewer) see everything, including hole cards.

---

## Decisions: LLM with scripted fallback

Cosino's model, unchanged in shape: **the game server owns every decision; a policy is just a
prompt.** The player container's only job is to deliver its prompt over the websocket.

### 1. The LLM path

- One model call per decision, issued by `src/poker/llm.nim` (cosino's `llm.nim`, extended).
  Transports in cosino's order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` /
  `AWS_BEARER_TOKEN_BEDROCK`) first, then `ANTHROPIC_API_KEY`, then `ANTHROPIC_API_KEY_URI`.
  Bedrock model candidates: `us.anthropic.claude-haiku-4-5-20251001-v1:0` first, then
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. **`us.anthropic.claude-sonnet-4-6` is removed
  from cosino's candidate list** (raid 2026-08-23: it times out on every sidecar call).
- `maxOutputTokens: 900` (not cosino's 300 — babel 0.1.2's fix for "cut off at max_tokens"),
  `llmTimeoutSeconds: 20` (not 45: at 220 sequential decisions a 45 s stall is 6 % of the whole
  play budget), `output_config.effort` is **not** sent (Haiku 4.5 rejects it).
- **System prompt** (exact text; `<ALIAS>` and the variant block substituted):

  > You are `<ALIAS>`, a cog playing `<VARIANT NAME>` at the OS Poker ladder.
  >
  > `<VARIANT RULES BLOCK — the numbered rules for this rung from the design, 8–12 lines>`
  >
  > - Every hand starts with both/all seats on `<startingStack>` chips. Your score is your
  >   cumulative NET chips across the match, so a chip saved counts exactly as much as a chip won.
  > - Table talk is public and free. Bluff, needle and mislead — but your cards stay secret until
  >   showdown.
  > - Pick exactly one action from the legal list you are given, with an amount inside the stated
  >   range. An illegal answer is replaced by a house baseline move, which is never what you want.
  >
  > Reply with a single JSON object and NOTHING else. Your reply MUST begin with the character `{`.

- **User prompt**: standings → this hand's public history → your secret card(s) → board → pot and
  your stack → `GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always
  pick a legal action):\n<PLAYER_PROMPT>` → the legal-action instruction.
- **Reply schema** (the only fields read):

  | field | type | cap | notes |
  |---|---|---|---|
  | `say` | string | **≤ 160 characters**, truncated on **rune** boundaries with `…` appended | public table talk; may be empty |
  | `action` | string | one of `fold`, `check`, `call`, `bet`, `raise`, `allin` (also accepted: `all-in`, `all in`, `shove`) | anything else = parse failure |
  | `amount` | integer | 0 … the seat's max raise-to | **ignored in `kuhn` and `leduc`** — the wager size is fixed by the variant |

  Extraction tolerates fences and trailing prose (first `{` … last `}`, cosino's
  `extractJsonObject`). `call` with nothing to call is normalised to `check`; `allin` when the
  seat is covered or barred from raising is normalised to `call`/`check` (cosino's
  `parseDecision`, kept).

- **Every string that can reach the replay is truncated on rune boundaries** by one shared helper
  `truncateRunes(s, n)` in `src/poker/types.nim`: `say` (160), the operator prompt (4000), alias
  names (16), error text recorded on a fallback (200). Cosino's ad-hoc byte-cap-then-strip in
  `cleanSay` is replaced by this helper everywhere. (A byte-boundary truncation is how a replay
  renders in a browser but fails a strict JSON parser.)

### 2. Degrade, never hang

1. Decision times out (20 s), the transport errors, the JSON does not parse, or the action is
   illegal → **one retry**, same prompt plus
   `"\nYour previous reply was invalid. Respond with ONLY the requested JSON object and a legal
   action with a legal amount."`.
2. Retry fails → the seat's **scripted baseline** move for this variant is played, and
   `results.fallbacks[seat]` is incremented.
3. Baseline move somehow rejected by `applyAction` → **fold** (always legal), and
   `results.forcedFolds[seat]` is incremented. The hand always advances.
4. No credentials at all → `client.disabled` on construction; every seat plays scripted with no
   network wait, so offline certification and `docker_smoke.sh` (which runs with no
   `ANTHROPIC_API_KEY`) always complete.
5. HTTP 429 from the sidecar → no retry; scripted move immediately, and the inter-decision
   spacing floor is raised by 500 ms for the rest of the episode.
6. Episode settles early on either deadline guard or the decision budget (§The game 9); the
   partial hand is voided and refunded, results and replay are written, players get their `final`
   frame **before** the artifacts are written (cosino's ordering, kept — the worker tears player
   pods down as soon as `results.json` exists).

### 3. Wall-clock budget (sequential game)

Poker is a **sequential-decision** game: one seat is on decision at a time, so there is no
parallel batch to issue and the budget is per decision.

- Per decision: Haiku p95 ≈ 2.2 s at these prompt sizes, plus `turnDelayMs = 250` spectator
  pacing. A **spacing floor of 2100 ms from decision start to decision start** holds the episode
  under the Bedrock sidecar's 30-requests-per-minute-per-episode cap (raid 2026-08-23) at ≈ 28
  rpm worst case. **Budget 3.0 s per decision.**
- Play budget: `0.60 × 1200 s = 720 s` → **`EpisodeDecisionBudget = 220`** calls
  (220 × 3.0 s = 660 s, 8 % margin).
- Hands per variant are declared so that the expected cost fits, and are re-capped at sample time
  by `sampleEpisode` (cosino's idempotent budget fit, kept), rounded **down to an even number** so
  every duplicate pair is complete:

  | variant | seats | expected decisions/hand | hands | expected play | budget cap |
  |---|---|---|---|---|---|
  | `kuhn` | 2 | 2.6 | 60 | 60 × 2.6 × 3.0 = **468 s** | 220/2.6 = 84 ≥ 60 ✓ |
  | `leduc` | 2 | 5.4 | 36 | 36 × 5.4 × 3.0 = **583 s** | 220/5.4 = 40 ≥ 36 ✓ |
  | `holdem-hu` | 2 | 6.0 | 30 | 30 × 6.0 × 3.0 = **540 s** | 220/6 = 36 ≥ 30 ✓ |
  | `holdem-6max` | 6 | 13.0 | 16 | 16 × 13.0 × 3.0 = **624 s** | 220/13 = 16 ✓ |

  Every row is inside 720 s, and both deadline guards sit above them.
- Certification / docker smoke: no credentials → zero LLM latency, `turnDelayMs = 0`; the
  12-hand Kuhn fixture completes in ~2 s plus the connect grace, comfortably inside
  `coworld certify`'s default 60 s (no `--timeout-seconds` override needed).

### 4. Scripted baselines (same image, env-switched)

Two named baselines, both **always legal at every rung**, both fieldable policies:
`PLAYER_SCRIPTED=house` and `PLAYER_SCRIPTED=rock` (any other non-empty value means `house`).
LLM policies set `PLAYER_PROMPT` instead. One image, `/bin/poker-player`, chooses by env — never
two images.

**`house`** — the default, and the fallback move whenever an LLM decision fails.

- *Kuhn*: **exact Nash**, the α-family at **α = 1/6**, mixed with the seeded RNG:
  as position 0 — bet J with p = 1/6, never bet Q, bet K with p = 1/2; after checking and facing a
  bet — fold J, call Q with p = 1/2, always call K.
  As position 1 — facing a bet: fold J, call Q with p = 1/3, always call K; facing a check: bet J
  with p = 1/3, check Q, always bet K.
  (Measured exploitability of this table is exactly 0; a unit test asserts `< 1e-9`.)
- *Leduc*: rule table, seeded mixing.
  Round 1, no wager yet: bet with K always, with Q p = 1/3, never with J. Facing one wager: raise
  with K, call with Q, fold J. Facing two wagers: call with K, fold otherwise.
  Round 2, no wager yet: bet if paired with the board; with unpaired K bet p = 1/2; else check.
  Facing one wager: raise if paired, call with unpaired K, call unpaired Q only if the board is J,
  else fold. Facing two wagers: call if paired or K, else fold.
- *Hold'em (both variants)*: **cosino's Chen-formula bot verbatim** (`llm.nim scriptedAction`) —
  Chen preflop buckets with position- and price-aware raise/call/fold, postflop made-hand
  category from the shared evaluator plus flush-draw detection, pot-odds calling, seeded mixing
  for slowplays and bluffs.

**`rock`** — deterministic, no RNG, deliberately exploitable (a calibration reference and the
second filler).

- *Kuhn*: bet iff K; call a bet iff K; fold J and Q to a bet; as position 1 after a check, bet iff K.
- *Leduc*: never opens a wager unless paired with the board; facing any wager, call iff paired or
  holding K; fold otherwise.
- *Hold'em*: tight-passive Chen — preflop raise to 3 bb with Chen ≥ 12, call up to 4 bb with
  Chen ≥ 9, fold otherwise; postflop bet 2/3 pot only with two pair or better, call up to 1/3 pot
  with top pair or better, fold otherwise. Never bluffs.

Both are also the **fillers** in the league (§Packaging); both champions are `PLAYER_PROMPT`
policies.

---

## Sim module

Pure Nim, no IO, no networking — driven identically by the server, the tests, and the wasm replay
viewer. Forked from cosino's `src/cosino/*` and renamed to `src/poker/*`.

| file | provenance | change |
|---|---|---|
| `src/poker.nim` | cosino `src/cosino.nim` | rename only (entrypoint, live vs replay mode) |
| `src/poker/cards.nim` | cosino `src/cosino/cards.nim` | **kept verbatim** (0–51 encoding, seeded deck, `eval5`/`bestFive`/`evalBest`, `describeRank`, `cardText`) plus `kuhnDeck()`, `leducDeck()`, and `leducRank(private, board)` |
| `src/poker/types.nim` | cosino `types.nim` | + `Variant` enum, ante/bet-size/wager-cap config, `duplicate`, `seatOrder`, `truncateRunes` |
| `src/poker/sim.nim` | cosino `sim.nim` | + variant dispatch, per-hand stack reset, duplicate pairing, net accounting, new events, `auditFromEvents` |
| `src/poker/solve.nim` | **new** | exact best response + exploitability for Kuhn and Leduc |
| `src/poker/audit.nim` | **new** | equity, surrender, bias, pair flags (called by `sim.auditFromEvents`) |
| `src/poker/llm.nim` | cosino `llm.nim` | + variant prompts, the two named baselines, `truncateRunes`, model-list and token fixes |
| `src/poker/server.nim` | cosino `server.nim` | + reason/end-guard plumbing, new replay fields |
| `src/poker_player.nim` | cosino `src/cosino_player.nim` | + `PLAYER_SCRIPTED=<name>`, + the receive-loop fix (below) |

### Config (`GameConfig`)

`tokens[]`, `players[{name}]`, `num_agents`, `seed`, `variant` (`"kuhn"|"leduc"|"holdem"`),
`startingStack`, `ante`, `smallBlind`, `bigBlind`, `hands`, `duplicate` (default true),
`randomiseSeating` (default true), `sampled`, `turnDelayMs`, `player_connect_timeout_seconds`,
`model`, `maxOutputTokens`, `llmTimeoutSeconds`.
Validation is per variant: Kuhn/Leduc require `ante ≥ 1`, `smallBlind == bigBlind == 0`;
Hold'em requires `1 ≤ smallBlind < bigBlind`, `ante == 0`, `startingStack ≥ 2·bigBlind`.
Per-variant defaults: `kuhn` → stack 20, ante 1, bet 1, cap 1 wager, 1 round; `leduc` → stack 50,
ante 1, bets [2, 4], cap 2 wagers, 2 rounds; `holdem` → stack 100, blinds 1/2, no cap.

### Event vocabulary (the replay's whole language)

Every event carries `kind`, `hand`, `seat` (−1 for table events), `street`, and the optional
fields cosino already serialises (`cards`, `best`, `amount`, `action`, `allIn`, `stackAfter`,
`betAfter`, `potAfter`, `text`) plus three new ones: `net` (per-seat net after, on `handEnd`),
`pair` and `mirror` (on `handStart`), `data` (a small JSON object, on `audit`/`calib`/`matchEnd`).

| kind | when | payload |
|---|---|---|
| `handStart` | each hand | `seat` = button slot, `pair` = k, `mirror` = bool, `text` = `"1/2"` or `"ante 1"`, `data.positions` = slot per table position |
| `deal` | private card(s) | `seat`, `cards` (redacted per player socket, full in replay) |
| `ante` | Kuhn/Leduc | `seat`, `amount`, `stackAfter`, `betAfter`, `potAfter` |
| `blind` | Hold'em | as cosino (`text` = `"small"`/`"big"`) |
| `say` | any decision | `seat`, `text` (≤ 160 runes) |
| `action` | any decision | `action` ∈ fold/check/call/bet/raise, `amount`, `allIn`, `stackAfter`, `betAfter`, `potAfter` |
| `board` | Leduc board card, Hold'em flop/turn/river | `cards`, `street`, `potAfter` |
| `reveal` | showdown | `seat`, `cards`, `best`, `text` = `describeRank` |
| `award` | every pot slice and every uncalled refund | `seat`, `amount`, `stackAfter`, `potAfter`, `text` ∈ `"main"`,`"side N"`,`"sweep"`,`"returned"` |
| `stackOff` | Hold'em: a seat ends a hand having lost its entire hand-stack | `seat` — **cosmetic only**, replaces cosino's `bust`; no game effect (stacks reset next hand) |
| `handEnd` | end of a hand | `data.net` = net-after per slot, `potAfter` = 0 |
| `handVoid` | hard deadline abandoned a live hand | `data.refunds` per slot; the hand is not scored |
| `calib` | tail, `kuhn`/`leduc` only | `seat`, `data = {exploitability, coverage, fill, decisions}` |
| `audit` | tail, `n ≥ 3`, one per flagged pair | `data = {a, b, flag, biasAB, biasBA, surrenderAB, surrenderBA, contested, netFlow}` |
| `matchEnd` | always, last event | `data = {reason, handsScored, seed}` — the wall-clock stop is recorded as a **load-bearing event**, applied by the same proc on record and on playback, so a `deadline` replay re-derives bit-identically to a `complete` one (particle-worlds, 2026-08-26) |

`replayMatch(config, events)` re-derives one `ReplayFrame` per event prefix from these fields
alone; it never re-runs the betting engine (cosino's invariant, kept). `GameVersion = 1`.

### The exact state JSON the viewer reads

`replayMatch` produces one `ReplayFrame` per event prefix (`frames[i]` = the table after
`events[0..<i]`), and `frameStateJson(frame)` serialises each one into exactly this object — the
same shape the live `/global` snapshot carries, so `renderer.js` has one input format:

```json
{"seats": [{"name": "Sprocket", "stack": 46, "bet": 8, "net": 14,
            "cards": [39, 12], "revealed": false, "folded": false,
            "allIn": false, "acting": true, "handsWon": 3}],
 "board": [7, 23, 44], "pot": 26, "street": "flop",
 "hand": 6, "pair": 3, "mirror": true, "button": 1,
 "currentBet": 8, "handDone": false}
```

`cards` are ints 0–51 (`rank = card div 4`, 0 = deuce … 12 = ace; `suit = card mod 4` =
clubs/diamonds/hearts/spades); an empty `cards` array means "not dealt or redacted". `net` is the
seat's cumulative net **before** the current hand's chips move. The wasm module wraps the whole
timeline as `{"type":"replay","protocol":…,"names":…,"policyNames":…,"config":…,"events":…,
"results":…,"states":[<the objects above>]}` — byte-identical to what the live `/replay` websocket
sends, which is why one renderer drives all three views.

### Replay bytes are self-sufficient

```json
{"protocol": "poker.replay.v1",
 "names": ["Sprocket", ...],                 // anonymous aliases, by slot
 "policyNames": ["poker-scholar", ...],      // spectator-side only, by slot
 "config": {"variant": "leduc", "seats": 2, "startingStack": 50, "ante": 1,
            "smallBlind": 0, "bigBlind": 0, "bets": [2,4], "maxWagers": 2,
            "hands": 36, "duplicate": true, "seatOrder": [1,0],
            "seed": 12345, "sampled": true, "gameVersion": 1},
 "events": [...],
 "results": {...}}
```

Nothing else is ever fetched — no server, no API, only the `.replay` file from S3. The seed is in
the bytes, so the audit's Monte-Carlo equity re-derives identically in the browser.

### Results (`results.json`)

`names[]` (**policy** names, by slot), `scores[]`, `win[]`, `net[]`, `netPerHand[]`,
`unitsPerHand[]`, `handsWon[]`, `stackOffs[]`, `fallbacks[]`, `forcedFolds[]`, `decisions[]`,
`exploitability[]` (numbers or nulls), `exploitabilityCoverage[]`, `exploitabilityFill`,
`audit {pairs[], flagged[], power{}}`, `variant`, `seats`, `handsPlayed`, `handsScored`, `hands`,
`pairsComplete`, `unpairedHands`, `startingStack`, `ante`, `smallBlind`, `bigBlind`, `seed`,
`seatOrder[]`, `reason` (enum `complete|deadline|budget`).

---

## Server, player, protocol

Cosino's `server.nim` with the same routes, the same threading model (one game thread mutating
the match under `stateLock`, the slow model call made outside the lock on a snapshot), and the
same artifact ordering. Routes, unchanged and all required by the certifier:

```
GET /healthz                    GET /client/global    GET /client/player
GET /client/replay              GET /client/renderer.js  GET /client/chrome.css
GET /client/assets/<name>       WS  /player?slot=N&token=T
WS  /global                     WS  /replay
```

Both `/client/` routes must serve real pages, registered before any catch-all (lantern 0.1.1),
and neither opens the player socket. `/healthz` and `/global` keep answering (and answering
WebSocket **Ping** with **Pong**, which mummy hands to the application) for a bounded ~20 s
shutdown grace after the artifacts are written, then the process exits 0 (lantern 0.1.4).

**Player protocol `poker.player.v1`** — cosino's frames, unchanged in shape so a cosino prompt
ports verbatim:

- player → game: `{"type":"prompt","prompt":str,"scripted":bool,"baseline":"house"|"rock"}`.
  `prompt` is capped at **4000 characters, rune-truncated**, server-side. Sent on connect and
  again after `welcome` (the re-send covers a race with slot registration). The latest frame wins
  for all later decisions.
- game → player: `{"type":"welcome","protocol":"poker.player.v1","slot":N,"name":alias,
  "variant":str,"startingStack":int,"ante":int,"smallBlind":int,"bigBlind":int,"hands":int}`;
  `{"type":"state", ...}` after every event batch, with **hole cards other than the recipient's
  redacted** and `policyNames` deleted (cosino's `redactCards`, kept, extended to strip `calib`
  and `audit` events from player views); `{"type":"final","done":true,"scores":[…],"win":[…],
  "names":[aliases],"net":[…],"handsPlayed":N,"reason":str}` at the end, after which the player
  exits 0.

**Player runnable** `/bin/poker-player`: reads `PLAYER_PROMPT` (or a built-in default poker
personality) and `PLAYER_SCRIPTED`; delivers the prompt; idles until `final`. **Fix inherited
from raid 0.1.4 and not present in cosino:** the receive loop is wrapped in
`try/except CatchableError` and exits **0** on a dead socket — whisky's `receiveMessage` *raises*
on a close frame, and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed
`final` frame and the player container exits 1 intermittently.

**Two name spaces, both:** the table (canvas, prompts, `say` lines, feed event text, player
frames) uses anonymous aliases; the spectator layer (replay `policyNames`, the scorebug, the
endcard, `results.names`) maps back to policy names, except that a name matching
`/^baseline(\s*\(\d+\))?$/i` keeps its alias (`makeNameMap`/`isBaselineFiller` in `renderer.js`,
kept).

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/cogame-cosino`.** No mixing.

| file | from | into |
|---|---|---|
| `replay-viewer/config.nims` | cosino `replay-viewer/config.nims` | same emscripten link flags: `MODULARIZE=1`, `EXPORT_NAME=PokerReplayModule`, `EXPORTED_RUNTIME_METHODS=HEAPU8`, `EXPORTED_FUNCTIONS=_main,_malloc,_free,_pkr_load_replay,_pkr_payload_ptr,_pkr_payload_len,_pkr_error_ptr,_pkr_error_len`, `-O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s ENVIRONMENT=web`, `--mm:arc --exceptions:goto -d:useMalloc` |
| wasm entry `replay-viewer/poker_replay.nim` | cosino `replay-viewer/cosino_replay.nim` | same structure, `cos_*` → `pkr_*`, same `emscripten_exit_with_live_runtime` epilogue |
| `replay-viewer/static_replay.js` | cosino `replay-viewer/static_replay.js` | the **MODULARIZE factory bootstrap** (`PokerReplayModule()`), matching the link flags above |
| `replay-viewer/index.html` | cosino `replay-viewer/index.html` | same shell, ids unchanged |

Splicing one starter's shell onto another's link flags is what deadlocked cogame-lantern
(2026-08-23) — factory never called, no error, "Loading replay…" forever. Cosino's four files are
internally consistent (verified: `config.nims` emits `MODULARIZE=1 EXPORT_NAME=CosinoReplayModule`
and `static_replay.js` calls `CosinoReplayModule()`), so they move together and nothing else is
borrowed.

**Load signalling.** `client/renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` on its **first drawn frame**
(cosino already does this at the end of `attachReplay`, after `setIndex(0)` and the first
`frame()` draw — kept), and `static_replay.js` sets `data-replay-error="<message>"` on any
failure. Both are what `tools/ci/viewer_smoke.mjs` gates on.

### Upgrades taken from babel (cosino lags; babel is the current standard)

1. **Host bridge with the correct ordering.** Babel 0.1.4's `tell(type, message)` `coworld-replay`
   postMessage bridge (`loading` when the script runs, `ready`, `error`) is added to
   `static_replay.js` — cosino has no bridge at all. But babel posts `ready` on a bare rAF pair,
   which can beat the first painted frame (chorus `3c11c953`, 2026-08-24). So: `attachReplay`
   takes an `onFirstFrame` callback, invokes it **immediately after** setting
   `data-replay-loaded="true"`, and the shell posts `ready` **from that callback only**. The
   attribute and the bridge can then never disagree.
2. **Bounded fetch + Retry.** Babel 0.1.3's `FETCH_TIMEOUT_MS = 20000` `AbortController` fetch, the
   `RETRYING REPLAY… (attempt N)` caption, and the Retry button that refetches without reloading
   (reusing the compiled module) — cosino's shell waits forever on a dead CDN edge.
3. **CI shape.** `.github/workflows/ci.yml` and `coworld-release.yml` come from
   coworld-builder `templates/` (cosino predates them and ships neither), with
   `SLUG=poker`, `IMAGE=coworld-poker`, `SEATS=2`; `tools/ci/docker_smoke.sh` and
   `tools/ci/viewer_smoke.mjs` copied from the same templates (the smoke script substituted with
   the same three values; `viewer_smoke.mjs` byte-for-byte, no substitutions). Both committed
   mode 100755.

### Chrome provenance

The parley lineage names its chrome `client/chrome.css` + `client/renderer.js` (the ctf lineage's
`client/chrome_common.js` / `client/replay_broadcast.html` do not exist here). The same rule
applies to the files that do exist:

- **`client/chrome.css` is copied byte-for-byte from cosino** and extended **only by an appended
  game block** at the end of the file, fenced by
  `/* ==== poker game block (appended; nothing above this line is edited) ==== */`. Not one
  existing selector is rewritten. The appended block contains exactly:
  - `#scorebug { grid-template-columns: repeat(auto-fit, minmax(96px, 1fr)); }` — cosino hard-codes
    `repeat(5, 1fr)`, which wraps the sixth plate onto a second row at 6-max.
  - `.seat5 { --tc: var(--orange); }` and `:root { --orange: #e08a3a; }` — cosino defines seat
    colours only up to `.seat4` while `renderer.js`'s `COLORS` has six entries, so the sixth seat's
    plate and scrubber beats render colourless at 6-max.
  - `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (overriding cosino's `flex: 0 1 auto`) and
    `@media (max-width: 640px) { .plate-label, .plate-pips { display: none; } }` — the featured-match
    iframe on softmax.com is ~360 px wide and names otherwise collapse to "…".
  - `@media (max-width: 400px) { #wordmark { font-size: 15px } #clock { font-size: 12px }
    .plate-score { font-size: 15px } #feed { display: none } }` — **legibility at 360 px wide is a
    requirement**, checked at 360 px, not at desktop width.
  - The new scrubber-beat kinds and the audit/calibration rows (below).
- **`replay-viewer/index.html` and `client/replay.html` are cosino's pages with a game block
  appended** — never a rewrite that reuses the ids (cogame-gridlock, 2026-08-23). Kept verbatim:
  `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  trailing `fit()` + `bindFeedToggle` script.
  **Changed:** the wordmark text becomes `PO<span>KER</span>`, and the `<title>`.
  **Removed:** nothing — every element cosino ships is used by this game.
  **Appended:** one `<div id="rungchip">` in `#topright` (the variant badge: `KUHN`, `LEDUC`,
  `NLHE HU`, `NLHE 6-MAX`) and one `<div id="auditcard">` inside `#board-wrap` (the collusion
  panel, hidden unless the replay carries `audit` events).
- **Zoom: no `#viewpanel`.** Cosino has none and this game does not add one — the poker table is a
  fixed arena that always fits the frame. A zoom bar and minimap exist only for boards larger than
  the frame.
- **Real art, no placeholders:** cosino's `data/` ships verbatim (`arena_floor.png`, the four
  `soldier_*_front.png` cog sprites, `font.ttf` + `FONT_LICENSE.txt`); the fifth and sixth cogs are
  hue-rotated at load by `tintedSprite` (cosino's mechanism, kept). Cards are drawn as rounded
  rects with rank/suit glyphs by `drawCardFace`/`drawCardBack` — no card-art assets.

### Transport rules

- `#transport` is a **flex row of `#stage`**, not an overlay: the canvas lives in `#board-wrap`,
  which ends exactly where the transport band begins, so nothing can be drawn over the band by
  construction.
- A `relayout()` in the appended game block runs on `load`, on `resize`, and on every feed toggle,
  and publishes on `:root`: **`--band`** = the measured `#transport` `offsetHeight` in px, and
  **`--hudscale`** = `clamp(0.72, stageWidth / 960, 1)`. The appended CSS scales the top band, the
  scorebug and the rung chip by `--hudscale` (this is what makes the 360 px case legible), and
  **every absolutely positioned overlay this game adds is anchored `bottom: var(--band)`** — that
  is `#auditcard`, and `#endscreen`, which is additionally re-anchored
  `#endscreen { bottom: var(--band); top: 0; }` so the endcard **stops at `var(--band)`** and never
  covers the scrubber.
- **The endcard is dismissed by every seek**: `setIndex` calls
  `updateEndscreen(container, results, index >= events.length && events.length > 0, nameMap)` on
  *every* index change, so any scrub away from the end hides it (cosino's behaviour, kept, and now
  covered by a test).
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` emits
  `<button type="button" class="beat-marker <kind> seat<N>" aria-label="…" title="…">` whose
  `onclick` seeks to that event index (cosino emits inert `<div>`s). Kinds emitted, each with its
  own CSS in the appended block — **every kind emitted has CSS**:
  `award` (pot won; seat-coloured), `showdown` (reveal; paper), `stackoff` (tall, red),
  `mirror` (duplicate mirror hand start; amber flag above the track), `void` (hand voided by the
  deadline; grey X), `audit` (flagged pair; violet flag). Hand spans and separators
  (`.round-span`, `.round-span.alt`, `.round-sep`) are kept, one span per hand.
  The game block's builder is named `buildPokerBeats`, **not** `markBeat` — a game-block function
  named like a chrome alias gets shadowed by the hoisted `var markBeat = C.markBeat` (tandem,
  2026-08-23), and a scope-duplication test covers the alias list.

### What the viewer draws

- **Canvas** (cosino's `draw`, kept): felt table, cog sprites at their table positions, hole cards
  face-up for spectators and backs for the others until a reveal, community/board cards with the
  winning five highlighted at showdown, per-seat bet chips, the pot pile, the dealer button, the
  winner's scoop animation, speech bubbles (`say`), and a floating `+N` on an award.
  **Card ranks render as "10", never "T"** (`cardLabel` already does this) and suits as ♣ ♦ ♥ ♠ with
  red/black colouring. Kuhn/Leduc draw one private card per seat and (Leduc) one board card in the
  centre slot; the empty board outlines shrink to the variant's board size.
- **Top band**: wordmark `PO`+`KER`, the rung chip (`KUHN` / `LEDUC` / `NLHE HU` / `NLHE 6-MAX`),
  and `#clock` reading e.g. `HAND 7 / 36 · MIRROR · ROUND 2 · POT 12` (Hold'em:
  `HAND 3 / 30 · FLOP · POT 24 · BLINDS 1/2`).
- **Scorebug**: one plate per seat — display name (policy name spectator-side, alias for
  baselines), a `D` chip on the button, **signed net chips** (`+14`, `−6`) as the big number with
  the label `net`, the seat's chips in front this hand, and one pip per hand won.
- **Feed** (right rail, collapsible): per-hand blocks with a head line
  `HAND 8 — duplicate mirror of hand 7`, then the hand in words — `Bolt raises to 8`,
  `The turn: 10♥`, `Gizmo shows K♠ Q♦ — two pair, kings and queens`, `Gizmo wins 34 (main pot)` —
  plus `say` lines in quotes, and at the tail the calibration lines
  (`Sprocket exploitability 0.031 chips/hand (coverage 0.83)`) and the audit lines
  (`SOFT PLAY FLAG — Bolt ↔ Piston: 1.4 bb/hand of mutual equity surrender over 7 contested hands`).
- **Endcard** (`#endscreen`, stops at `var(--band)`): `FINAL — 36 HANDS`, the verdict line, then
  ranked rows with net, score share, hands won, exploitability (or `—`), and, at 6-max, a flagged
  pairs block.
- **Legible at 360 px wide** — the scorebug, the clock and the endcard are checked at 360 px, not
  at desktop width.

### Bundle and build hook

Manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}` — a **static wasm bundle,
never a pod**, and no `/client/replay` live-server viewer is ever declared. `tools/build_replay_viewer.sh`
(cosino's hook, renamed paths) is the `coworld build` hook: it compiles `replay-viewer/poker_replay.nim`
to wasm with the local `emcc` or, failing that, the pinned `Dockerfile.replay-viewer`
(`emscripten/emsdk:4.0.15` + nimby 0.1.27 + Nim 2.2.4), then copies `poker_replay.js`,
`poker_replay.wasm`, `replay-viewer/index.html`, `replay-viewer/static_replay.js`,
`client/renderer.js`, `client/chrome.css` and `data/*` (sprites + font) into the output dir.
`mkdir -p` the output's parent **before** the containment check (ecos, 2026-08-23: the parent does
not exist on a fresh CI checkout). Committed 100755.

---

## Packaging

- **`compose.yaml`** — one service, name = coworld name:

  ```yaml
  services:
    poker:
      image: coworld-poker:latest
      platform: linux/amd64
      build: {context: ., network: host}
  ```

  The service name derives the manifest placeholder: **`{{POKER_IMAGE}}`** (never `{{GAME_IMAGE}}`
  — lantern 0.1.0).
- **`Dockerfile`** — cosino's two-stage nimby build, one image with two entrypoints:
  `/bin/poker` (game, default) and `/bin/poker-player`. `nimby.lock` carried over
  (bitworld, mummy ≥ 0.4.7, curly ≥ 1.1.1, whisky), Nim 2.2.4 / nimby 0.1.26, `nim.cfg`
  regenerated inside the image.
- **`coworld_manifest_template.json`** — cosino's, with:
  `$schema`, ≥ 3 top-level `tags` (`poker`, `cards`, `imperfect-information`, `llm-driven`,
  `ladder`); `game.name: "poker"`; `game.description` (required) and **no** `game.tags`, **no**
  top-level `version`, **no** `game.display_name`; `game.owner: "daveey@gmail.com"`;
  `game.replay_viewer.bundle: "static-replay-viewer"` (nested under `game`, not top-level);
  `game.runnable {type: "game", image: "{{POKER_IMAGE}}", run: ["/bin/poker"],
  env: {ANTHROPIC_API_KEY_URI: "secret://coworld/poker/anthropic_api_key"}, source_url}` — the
  secret namespace is **`game.name`**, which here equals the slug (`poker`), and the release
  workflow's `secret put` reads it from `game.name`, not from the slug variable;
  `episode_timeout_minutes: 20` top-level; `game.config_schema` a real JSON Schema in which
  **every array property declares `minItems` and `maxItems`** (`tokens` and `players` bounded
  2…6, matching `num_agents`); `game.results_schema` covering every field in §Sim module with
  `reason` as `enum: ["complete","deadline","budget"]`.
- **`game.docs`** — `readme: {"type":"text","value":…}` plus
  `pages: [{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}},
  {"id":"ladder.md",…}, {"id":"audit.md",…}]` (the three rungs' rules; how the ladder and the score
  work; how exploitability and the collusion audit are computed and what a flag means).
- **`game.protocols`** — **both** `player` and `global`, each a `{"type":"text","value":…}` object
  (bare strings fail the platform validator): `player` = the `poker.player.v1` frames above with
  the 4000-char prompt cap and the `PLAYER_PROMPT` / `PLAYER_SCRIPTED` recipe; `global` = the
  `/global` snapshot shape, the event kinds, and the note that spectators see every hole card.
- **`player[]`** — exactly two declared runnables, so the 2-seat cert fixture can seat **both**
  (a declared player with no certification slot fails `players_missing`, raid 0.1.3):

  | id | name | run | env | resources |
  |---|---|---|---|---|
  | `poker-player` | OS Poker Prompt Player | `/bin/poker-player` | (PLAYER_PROMPT at policy-upload time) | requests 100m/64Mi, **limits.cpu "1"** |
  | `poker-baseline` | OS Poker House Baseline | `/bin/poker-player` | `PLAYER_SCRIPTED: "house"` | same |

  `limits.cpu` must be `"1"` — `500m` is below the platform minimum (pistonball 0.1.1).

### Variants — `num_agents` is stated for every one

| variant `id` | name | `num_agents` | `players[]` | config |
|---|---|---|---|---|
| `kuhn` | Kuhn table (calibration) | **2** | 2 entries | `variant: "kuhn"`, `startingStack: 20`, `ante: 1`, `smallBlind: 0`, `bigBlind: 0`, `hands: 60`, `duplicate: true`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
| `leduc` | Leduc table (calibration) | **2** | 2 entries | `variant: "leduc"`, `startingStack: 50`, `ante: 1`, `smallBlind: 0`, `bigBlind: 0`, `hands: 36`, `duplicate: true`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
| `holdem-hu` | No-limit Hold'em, heads-up | **2** | 2 entries | `variant: "holdem"`, `startingStack: 100`, `ante: 0`, `smallBlind: 1`, `bigBlind: 2`, `hands: 30`, `duplicate: true`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
| `holdem-6max` | No-limit Hold'em, six-max | **6** | 6 entries | `variant: "holdem"`, `startingStack: 100`, `ante: 0`, `smallBlind: 1`, `bigBlind: 2`, `hands: 16`, `duplicate: true`, `randomiseSeating: true`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |

Every variant carries `description` (required by the upload contract) and `num_agents` inside
`game_config`. The ladder schedules zero episodes for a variant missing `num_agents`.

### Certification fixture

```
certification.game_config: variant "kuhn", num_agents 2, players ["Sprocket","Gizmo"],
  seed 7, startingStack 20, ante 1, smallBlind 0, bigBlind 0, hands 12,
  duplicate true, turnDelayMs 0, player_connect_timeout_seconds 180
certification.players: [{"player_id": "poker-player"}, {"player_id": "poker-baseline"}]
```

**`num_agents` = 2**, `len(certification.players)` = 2, `len(game_config.players)` = 2, and
`SMOKE_SEATS`/`<SEATS>` in `ci.yml` = **2** — the four independent declarations `docker_smoke.sh`
cross-checks. No runner-managed `tokens` in the fixture. 12 scripted Kuhn hands finish in ~2 s, so
`coworld certify`'s default 60 s needs no override, while the ~130-event replay it produces plays
for ~100 s — comfortably longer than the viewer soak window.

### Policies (`tools/ci/policies.json`)

Four distinct versions; both champions are **LLM prompt** policies, both fillers are scripted.

```json
[{"name":"poker-scholar","run":"/bin/poker-player","env":{"PLAYER_PROMPT":
  "Play game-theoretically sound poker. On the calibration tables (Kuhn, Leduc) mix your actions at the frequencies balance demands — bluff your worst hand at a low rate, call just often enough that bluffing you is break-even, and never play a pure strategy an opponent could exploit. At no-limit, value-bet thin, respect big raises from tight seats, steal from late position, and size bets by pot fraction. Every chip is score. Talk at the table to mislead, never to inform."}},
 {"name":"poker-exploiter","run":"/bin/poker-player","player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","env":{"PLAYER_PROMPT":
  "Play maximally exploitative poker. Read every opponent from the hand history in front of you: who folds too much, who never bluffs, who calls anything. Attack the leak you find — bluff the folders relentlessly, never bluff the callers, and value-bet paper-thin against stations. On the calibration tables track how often each seat bets and calls and deviate hard from balance to punish it. Every chip is score. Use table talk as bait."}},
 {"name":"poker-house","run":"/bin/poker-player","env":{"PLAYER_SCRIPTED":"house"}},
 {"name":"poker-rock","run":"/bin/poker-player","env":{"PLAYER_SCRIPTED":"rock"}}]
```

Champion #1 (`poker-scholar`) is submitted for daveey; champion #2 (`poker-exploiter`) is uploaded
**while daveey-1 is the active player** (the `"player"` field above) and submitted for daveey-1.
`poker-house` and `poker-rock` are the fillers, registered **before** the first `trigger-round`,
with UUIDs resolved from `GET /policy-versions` filtered client-side. The LLM runs **game-side**,
so the *game* runnable needs `ANTHROPIC_API_KEY_URI` in its manifest `env` (above) and the player
policies need **no** `USE_BEDROCK` (that gate is for player-side-LLM lineages).

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

**`tests/test_cards.nim`** — cosino's hand-evaluator suite kept verbatim (category ladder,
kickers, the wheel, best-five-of-seven, card text round-trip) plus: the Kuhn and Leduc decks
contain exactly the right 3 / 6 card ints; `leducRank` ranks pair > high card, orders J < Q < K,
and reports equal ranks as a split.

**`tests/test_sim.nim`** — cosino's betting/pot/match suites kept (blind order, no check facing a
bet, min-raise, short all-in does not reopen, side pots by commitment level, split pots and the
odd chip clockwise of the button, uncalled-bet refund) plus, new:

1. *Kuhn rules*: all five legal action sequences produce the exact documented net (±1, ±1, ±2, ±1,
   ±2); the higher card always wins a showdown; the wager cap rejects a raise.
2. *Leduc rules*: the wager cap is 2 per round; bet sizes are 2 then 4; the board card comes only
   when both seats are live; a pair beats an unpaired K; equal ranks split with the odd chip to
   position 0; folding forfeits the commitment.
3. *Per-hand reset*: every hand begins with every seat on `startingStack`; no seat is ever `isOut`.
4. *Duplicate mirror*: hands `2k` and `2k+1` are dealt the identical card sequence; the position
   map of the mirror equals `seatOrder` rotated by `n div 2`; heads-up, each seat's card in the
   mirror equals its opponent's card in the base hand.
5. *Seat randomisation*: `seatOrder` is a permutation of `0..n−1`, deterministic in the seed, and
   every results array is indexed by **slot** regardless of it.
6. *Chip conservation fuzz*: 200 random legal matches per variant conserve chips exactly
   (`Σ net == 0`) and re-derive cleanly through `replayMatch`.
7. *Scoring*: `Σ scores == 1` to 1e-9; `scores` is in `[0,1]`; a seat that wins every chip in every
   hand scores 1.0 and its opponents 0.0; a break-even seat scores `1/n`.
8. *Record → re-derive, for EVERY end reason*: an episode ended `complete`, one ended `deadline`
   (hard guard, with a `handVoid`) and one ended `budget` each re-derive from their event log to a
   byte-identical state timeline and identical results (particle-worlds, 2026-08-26 — a wall-clock
   stop must be a recorded event, not an out-of-band fact).
9. *Events round-trip through JSON* for every kind in the vocabulary, including `calib`, `audit`,
   `handVoid` and `matchEnd`.
10. *Budget fit*: `sampleEpisode` is idempotent, never returns an odd hand count, and caps each
    variant's hands at `EpisodeDecisionBudget div expectedDecisionsPerHand`.
11. *Rune truncation*: `truncateRunes` never splits a multi-byte rune; a 160-cap applied to a
    string of 4-byte emoji yields valid UTF-8; `$` of the resulting replay JSON parses under a
    strict UTF-8 decoder.

**`tests/test_solve.nim`** — calibration:

1. Exact best response reproduces the known Kuhn game value: `u0(Nash, Nash) == −1/18` to 1e-12.
2. `exploitability(nashTable(α))` is `< 1e-9` for α ∈ {0, 1/6, 1/3}.
3. `exploitability(rockTable)` (Kuhn) is `> 0.05` chips/hand — an exploitable strategy measures as
   exploitable.
4. Leduc: best response against the always-fold strategy equals the trivially computable value;
   `exploitability` of the `house` Leduc table is finite, positive, and stable across two seeds.
5. Unvisited infosets fill as declared (`nash` for Kuhn, `uniform` for Leduc) and `coverage` is
   reported correctly for a strategy that visited exactly half the tree.

**`tests/test_audit.nim`** — collusion:

1. A scripted 6-max episode with no collusion produces **zero** flags (no false positive at
   `contested ≥ 4`).
2. A synthetic episode in which seat 2 folds every hand it is heads-up with seat 5 while holding
   the best hand raises `bias[2][5]` above the dump threshold and produces exactly one
   `dump-2-to-5` flag.
3. A synthetic mutual soft-play episode produces exactly one `soft-play` flag on that pair.
4. `auditFromEvents` is a pure function: called twice on the same events + seed it returns
   identical JSON; called on the *replay's* events (post round-trip) it matches the server's
   `results.audit` byte for byte.
5. Equity Monte-Carlo is deterministic for a pinned seed, and equals exact enumeration to within
   0.02 on a complete board (where it degenerates to exact).

**`tests/test_bot.nim`** — the bounded-orders / legality assertion:

1. `house` and `rock` each play 200 complete matches at **every variant and every seat count**
   (kuhn 2, leduc 2, holdem 2, holdem 6) without `applyAction` ever raising — the baseline is
   always legal, its amounts are always inside `[minRaiseTo, maxRaiseTo]` / the fixed wager, and
   it never acts out of turn.
2. `decide` with no credentials returns the scripted move immediately, with no network call.
3. An LLM reply that is unparseable, then unparseable again, yields the scripted move and
   increments `fallbacks`; a baseline move rejected by the engine yields a **fold** and increments
   `forcedFolds`.
4. `say` from a hostile reply (5 kB of emoji) is capped at 160 runes and the replay containing it
   parses as strict UTF-8.

**`tests/test_manifest.nim`** — the manifest is parsed and asserted in CI: `game.description`
present, `game.tags` absent, ≥ 3 top-level tags, `num_agents` present in **every** variant and in
the certification fixture and equal to that variant's `players` length,
`game.protocols.player`/`.global` and `game.docs.readme` are `{type,value}` objects,
`game.replay_viewer.bundle == "static-replay-viewer"`, every `config_schema` array property
declares `minItems`/`maxItems`, `player[].resources.limits.cpu == "1"`, and every declared
`player[]` id appears at least once in `certification.players`.

**End-to-end (`docker-smoke` job)** — `tools/ci/docker_smoke.sh` builds the production image and
runs one real episode of the certification fixture in raw docker (one game container + one player
container per seat, no `ANTHROPIC_API_KEY`, so both seats play scripted): the game must exit 0,
**every player container must exit 0**, `results.json` must be non-empty valid UTF-8 JSON with
`names`/`scores` of length 2, and the replay must be non-empty and parse as **strict UTF-8 JSON**
(`SMOKE_REQUIRE_REPLAY_JSON=1`). The replay is copied to `dist/smoke/` and uploaded as the
`smoke-replay` artifact.

**Viewer smoke (`wasm-viewer` job, `needs: docker-smoke`)** — the bundle is **executed**, not
merely built. After building it with `./tools/build_replay_viewer.sh` and asserting index.html +
a non-empty `.wasm`, the job downloads the `smoke-replay` artifact and runs, in headless Chromium
via Playwright 1.55.0 (pinned in both the npm install and the browser download):

```
node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
  --replay dist/smoke/replay.json --timeout 90 --soak 12 --strict-text-bounds
```

`--soak 12` (uninterrupted playback must still be advancing at the end — cogball 0.1.4 loaded,
drew one frame and froze) is affordable because the 12-hand fixture replay plays for ~100 s.
`--strict-text-bounds` is kept because the poker table is a **fixed arena**: `canvas_text.never_inside`
must be 0, which is the gate on speech bubbles, nameplates and hand tags having somewhere to go.
A **second** invocation in the same job runs the bundle against
`tools/ci/fixtures/sixmax_audit.replay` — a committed 6-max Hold'em replay with two flagged pairs
and a full-160-rune `say` on every seat, regenerated and diffed by `tests/test_sim.nim` so it can
never drift from the format — because the cert fixture is a 2-seat Kuhn episode and would
otherwise leave the sixth plate, the audit card and worst-case bubble text unexercised
(cogchemists, 2026-08-24: nothing in CI ever draws chrome the scripted smoke does not produce).
Both invocations must exit 0; `viewer-smoke.png` / `viewer-smoke.json` are uploaded always.

**Static greps in `ci.yml`** (cheap, catch the known silent failures): `tools/ci/docker_smoke.sh`
and `tools/build_replay_viewer.sh` are present and mode 100755; `tools/ci/viewer_smoke.mjs` is
non-empty; `static_replay.js` calls `PokerReplayModule(` and `config.nims` declares
`EXPORT_NAME=PokerReplayModule` (the lantern splice); no game-block function name collides with
the chrome alias list (the tandem shadowing); every beat kind emitted by `buildPokerBeats` has a
matching CSS rule in `chrome.css`.

---

## Out of scope (v1)

- Three-player Kuhn, and any exploitability number for the Hold'em rungs (no exact best response
  exists at NLHE scale; `results.exploitability` is `null` there and nothing pretends otherwise).
- A CFR/solver-based opponent, or any attempt to *train* toward equilibrium in-repo.
- ACPC / `universal_poker` gamedef import; PettingZoo action-space compatibility; any external
  library dependency — the rules are reimplemented natively in Nim per rung.
- League-level aggregation of audit flags across episodes, and any *enforcement*: the audit
  reports, it never penalises a score, disqualifies a seat, or feeds Elo.
- Duplicate mirroring beyond 2 mirrors (a full `n`-rotation at 6-max), and true duplicate *pairing*
  across separate episodes.
- Chip carry-over between hands, busts, rebuys, tournament placement scoring, blind escalation and
  antes-on-top at the Hold'em rungs.
- Multi-table play, per-seat time banks, separate table-talk turns (talk rides on the action
  reply), and any second model call per decision.
- Live `/client/replay` pod viewers, card-art image assets, and a `#viewpanel` zoom bar/minimap.
- Mixed-rung episodes (one episode is one variant), and per-rung leaderboards (one Elo ladder over
  all four variants).
