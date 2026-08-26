# Liar's Dice: a bluffing coworld with cheap talk and a soft-play audit

Built on **`Metta-AI/cogame-babel`** (read at `/workspace/starters/cogame-babel`, version 0.1.4) —
the parley-stack template for turn-based hidden-information games where the game logic is native
Nim, decisions are made server-side by Claude, and **a policy is just a prompt**. Starter chosen by
game shape: the phase-10 starter table's first row is "turn-based / talk / cards / board / **dice /
bluff**; game logic native; policy = LLM prompt", and babel is the best current member of that
lineage — it already ships the exact machinery this game needs (a pure `sim` module shared by
server / tests / wasm viewer, per-seat hidden information with a redacted player socket, private
per-seat notes fed back verbatim, anonymous cog aliases with policy names spectator-side, a
retry-once-then-scripted decision path, an event-log replay the wasm viewer re-derives frames from,
and the parley broadcast chrome). **Every convention there holds here unless this note says
otherwise.** Fork of cogame-babel 0.1.4; the new repo is `Metta-AI/cogame-liars-dice`, public.

**Source idea, verbatim:**

```
ALREADY EXISTS as Metta-AI/coworld-liars-cog (Nim, headless JSON, Liar's Dice with bid/challenge, modelled on crewrift). This card is only the delta:
    Liar's Poker variant (OpenSpiel liars_poker): bid on digits of hidden serial numbers instead of dice faces.
    Talk-on mode: a short say channel between bids (cheap talk + bluffing is the LLM-interesting version).
    Soft-play audit for 3-6 seat tables: randomised seating, anonymous aliases, per-seat expected-loss-vs-opponent stats.
    Verify the repo's certification status and league wiring; if it isn't live, finishing it IS the task.

Source: OpenSpiel liars_dice, liars_poker; github.com/Metta-AI/coworld-liars-cog.
```

**Coordinator ruling this note implements (binding):** `Metta-AI/coworld-liars-cog` is private and
pre-dates the static-replay-viewer pipeline (WebSocket live viewer, its own league commissioner, no
static-replay bundle, no `coworld-release` chain), so it cannot be certified or league-wired as it
stands. This run therefore ships a **new public repo `Metta-AI/cogame-liars-dice` on cogame-babel
conventions**, implementing Liar's Dice core plus the card's three deltas: (1) a **Liar's Poker**
variant bidding on digit counts across hidden serial numbers; (2) **talk-on mode**, a short capped
`say` channel carried with each bid; (3) a **soft-play audit** — randomised seating, anonymous
aliases, per-seat expected-loss-vs-opponent statistics recorded into the replay and the results.
No code, prose or configuration is taken from the private repo; the rules below are the public game
(OpenSpiel `liars_dice` / `liars_poker`).

There is **no `OPEN` section**: every rule the card leaves loose is settled below by decision, with
the reason stated inline.

---

## The game

**Seats.** Exactly **4** (`num_agents: 4`) in every shipped variant and in the certification
fixture. Reason: the league seats two LLM champions plus two scripted fillers, four is inside the
card's "3–6 seat tables" range, and a single seat count keeps the `<SEATS>` cross-check in
`tools/ci/docker_smoke.sh` unambiguous against the manifest. The sim is written generic in
`S = config.players.len` and `tests/test_sim.nim` exercises S = 3, 4, 5 and 6, but v1 certifies and
ships **only S = 4** (see *Out of scope*).

**Modes.** One config field, `mode`:

| `mode` | symbol space | per-seat hand | table total at S=4 | symbol probability |
|---|---|---|---|---|
| `"dice"` (default) | faces **1..6** | `handSize` = **5** dice | 20 dice | 1/6 |
| `"poker"` | digits **0..9** | `handSize` = **8** digits of a hidden serial number | 32 digits | 1/10 |

`faces` is derived from the mode (6 or 10) and is never configured separately. Everything else —
bid ordering, challenge resolution, scoring, talk, the audit — is identical across modes. In
`poker` a "hand" is an 8-digit serial number drawn uniformly (leading zeros allowed) and is
rendered and spoken as digits, never as letters.

**Talk.** One config field, `talk` (bool, default `true`). When on, every action reply may carry a
`say` of at most **140 characters**; it is published to every seat the instant the action applies
and is recorded in the replay. When off, a `say` in a reply is discarded before the action applies,
never enters any prompt, and never reaches the event log. Talk is **cheap talk**: nothing said is
binding, and the rules never reference it.

**Episode shape.** An episode is `deals` independent deals (default **8**, min 2, max 9 after
budget fitting; certification fixture **3**). There is **no dice-loss elimination**: every deal
deals every seat a fresh full hand. Reason: elimination makes seat scores lopsided, makes episode
length unbounded, and gives eliminated seats nothing to do; a fixed number of independent deals is
what the league can rank fairly and what the budget can size.

**Seating.** At `initSim` the seed draws a permutation `order[0..S-1]`, table position → slot. The
table's turn order is that permutation; the opener of deal `d` (0-based) is table position
`d mod S`. Seats are addressed in every prompt and every rendered surface by **anonymous cog
alias** only. This is the "randomised seating" half of the soft-play audit: a given pair of
policies does not sit in the same relation every episode.

### Resolution rules, in order

1. **Deal opens.** `beginDeal()` draws every seat a fresh hidden hand from the seed
   (`hands[seat][0..handSize-1]`, sorted ascending for display), sets `standing = none`,
   `bidsThisDeal = 0`, and sets the turn to table position `d mod S`. A `deal` event is logged
   carrying `deal`, `opener` and all `hands`.
2. **A seat acts.** Exactly one seat acts at a time — this is a strictly sequential turn game. The
   acting seat plays either **BID** `(quantity, face)` or **CHALLENGE**, optionally attaching `say`
   (talk on) and `notes` (always private).
3. **Opening bid.** With no standing bid the acting seat **must** bid; a `challenge` reply is
   illegal and is handled by rule 11. A legal opening bid has `1 <= quantity <= totalSymbols`
   (`totalSymbols = S * handSize`) and `face` in the mode's range.
4. **Strict raise.** With a standing bid `(q0, f0)`, a bid `(q, f)` is legal iff
   `q > q0`, **or** `q == q0 and f > f0` — and `q <= totalSymbols` and `face` is in range.
   Equal-quantity-lower-face and equal bids are illegal. (Dice mode: ones are **not** wild; a
   symbol counts only for its own face. Stated because half the world plays with wild ones.)
5. **Turn advance.** After a legal bid the turn moves to the next table position (wrapping);
   `bidsThisDeal` increments.
6. **Challenge.** With a standing bid the acting seat may CHALLENGE instead of bidding. This
   reveals every hand: `actual = ` the number of symbols equal to `f0` across **all** hands.
   - If `actual >= q0` the **bidder** was truthful: bidder **+1**, challenger **−1**.
   - If `actual < q0` the bid was a lie: challenger **+1**, bidder **−1**.
   Nobody else scores. A `challenge` event is logged with `quantity`, `face`, `actual`, per-seat
   `counts[S]`, `bidderWins`, `forced`, the challenger (`seat`) and the bidder (`other`).
7. **Deal ends** the moment a challenge resolves. The audit counters (below) are updated, and
   `dealsPlayed` increments.
8. **Bid cap.** If `bidsThisDeal` has reached `maxBidsPerDeal` (default `3 * S` = **12**, schema
   3..30) the acting seat may not bid: the sim forces a challenge on its behalf, resolved exactly
   as rule 6 with `forced: true`. This bounds a deal to at most `maxBidsPerDeal + 1` = 13
   decisions and is what makes the episode budget provable.
9. **Next deal.** If `dealsPlayed >= deals` the episode settles `complete`. Otherwise, if the play
   deadline has passed, it settles `deadline` (see *Decisions*). Otherwise the next deal opens at
   rule 1 after `turnDelayMs` of spectator pacing.
10. **Talk timing.** `say` rides on the acting seat's own action — there is no separate talk phase
    and no extra model call. It becomes visible to every other seat in the next prompt of the same
    deal (`TABLE TALK THIS DEAL`) and is drawn as a speech plate over the speaking cog. Talk does
    **not** carry across deals: each deal's prompt shows only that deal's talk, to bound prompt
    growth.
11. **Illegal actions never stall the table.** Any reply that is unparseable, out of range, not a
    strict raise, a challenge with no standing bid, or a bid when rule 8 forbids one is rejected;
    the server retries the model once with the reason, and on a second failure applies the scripted
    baseline's move for that seat (always legal by construction) with `scripted: true` and
    `fallback: true` on the event.

### The observation each seat gets

The seat's whole world is the prompt the server composes for it (the exact block layout is under
*Decisions*). Nothing else reaches it.

| **Visible to the acting seat** | **Hidden from every seat** |
|---|---|
| Its own alias and table position | Every other seat's current hand (dice faces / serial digits) |
| Every seat's alias, in table order, opener first | Every other seat's private `notes` |
| Deal number and total deals; mode, `handSize`, `faces`, `totalSymbols` | Policy display names (the alias is the only identity) |
| **Its own hand**, and how many symbols it cannot see (`(S-1) * handSize`) | The seed, `order` as a permutation of slots, and future deals |
| The full public bid history of the current deal, in order, with bidders | The soft-play audit matrices (`faced`, `challenged`, `net`, `expLoss`) and `bluffRate` — spectator- and results-side only, never in a prompt |
| The `say` history of the current deal (talk on only), attributed by alias | Which seats are scripted and which are LLM-piloted |
| **Every previous deal in full**: the challenged bid, who challenged, the real count, and **all revealed hands** | Anything the platform knows: player ids, elo, episode ids |
| The standings (`points`, `W`, `L`) of every seat | Whether a rival's earlier reply was a fallback |
| Its own private `notes`, fed back verbatim | — |
| Its operator prompt (`PLAYER_PROMPT`) | — |

### Scoring, sign, and what the league ranks

Per seat `s` over the deals actually played:

```
wins[s]   = deals s won as bidder-held or as successful challenger
losses[s] = deals s lost as caught bidder or as failed challenger
points[s] = wins[s] - losses[s]                      (integer, -dealsPlayed .. +dealsPlayed)
score[s]  = 0.5 + points[s] / (2 * dealsPlayed)      (float, 0.0 .. 1.0)
score[s]  = 0.5 when dealsPlayed == 0
```

**Higher is better. 0.5 is break even** (a seat that neither wins nor loses a challenge), 1.0 is
winning every deal, 0.0 is losing every one. The bounded, always-non-negative form is deliberate:
the leaderboard and elo read a plain 0..1 number, and a passive seat that never challenges and is
never challenged scores exactly break-even rather than the same as a seat that lost everything.
`sum(points) == 0` over any completed set of deals (each deal moves exactly +1 and −1), so the game
is zero-sum in points and mean `score` across the table is always 0.5.

**The league ranks by mean episode `score`** (round-robin, elo 1000/32, as in the playbook §Phase 3).

### Soft-play audit (the card's third delta)

Recorded server-side from full information, reported in `results.audit` and in the replay, and
**never shown to any seat in-game** (showing it would be a meta-gaming channel). For every ordered
pair of slots `(a, b)`, `a != b`:

- `faced[a][b]` — times `a` was on turn with `b`'s bid standing.
- `challenged[a][b]` — of those, how many `a` challenged.
- `net[a][b]` — points `a` took from `b` (`+1` per challenge between them that `a` won, `−1` per
  one it lost). `net[a][b] == -net[b][a]`.
- `expLoss[a][b]` — **expected value forgone by not challenging `b`**, the soft-play signal. For
  each facing where `a` did **not** challenge, compute from `a`'s own hand only
  `p = pTrue(a, q0, f0)` (below); the EV of challenging is `1 - 2p`. Sum `max(0, 1 - 2p)` over
  those facings and divide by `faced[a][b]` (0 when `faced[a][b] == 0`). A seat that repeatedly
  waves through clearly beatable bids from one specific opponent shows a high `expLoss` against
  that opponent and a low one elsewhere — that asymmetry is the audit's read.
- `bluffRate[s]` — fraction of `s`'s bids that were false at the moment they were made
  (`actualCount(face) < quantity` over the real hands of that deal). A spectator stat and an audit
  input.

`pTrue(seat, q, f)` is the exact tail of a binomial: with `U = (S - 1) * handSize` symbols unseen
by `seat`, `own = ` `seat`'s own count of `f`, `k = max(0, q - own)`, and `p1 = 1/faces`,

```
pTrue = P[ Binomial(U, p1) >= k ]   = sum_{i=k..U} C(U,i) p1^i (1-p1)^(U-i)
```

computed in `float64` with a precomputed log-factorial table. It is a pure function in `sim.nim`,
shared by the audit, the scripted baselines and the tests, so the three can never drift.

### End conditions and `results.reason`

Exactly two values are legal, and no others may ever be written:

- **`"complete"`** — `dealsPlayed == deals`.
- **`"deadline"`** — the play clock (60 % of `episodeTimeoutSeconds`; see *Decisions*) stopped play
  at a deal boundary. Scores use the deals actually played. `dealsPlayed == 0` is possible (all
  seats break even at 0.5) and is still a valid, uploadable episode.

A player container disconnecting does **not** end the episode: decisions are server-side, and a
seat with no delivered prompt plays the built-in default prompt. Certification and the docker smoke
both end `complete`.

---

## Decisions: LLM with scripted fallback

Transport, credential order (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the
Bedrock model candidate list with Haiku first, the `haiku`/`4-5` guard on `output_config.effort`,
`extractJsonObject`, `cleanNotes` rune-safe truncation, and the **no-credentials ⇒ every seat
scripted** rule are ported from `src/babel/llm.nim` unchanged into `src/liars_dice/llm.nim`.
`maxOutputTokens` default **900** (never 400 — `cut off at max_tokens`), `model` default
`claude-sonnet-5`, `llmTimeoutSeconds` default **30**.

### The one call per turn

The acting seat's decision is one model call. **System prompt** (dice mode; `poker` swaps the first
two bullets for serial digits, `talk` off drops the talk bullet):

```
You are <ALIAS>, a cog at a Liar's Dice table with three other cogs.

Rules:
- Every deal each cog is dealt 5 hidden dice, faces 1 to 6. You see only your
  own dice. There are 20 dice on the table in total.
- A bid is a claim about ALL the dice on the table: "6 x 2" claims that at
  least six of the 20 dice show a 2. Ones are NOT wild: a die counts only for
  its own face.
- On your turn you either raise the standing bid or challenge it. A raise must
  be strictly higher: a larger quantity, or the same quantity with a higher
  face. The cog who opens a deal must bid.
- A challenge reveals every hand. If the standing bid is TRUE (the real count
  is at least its quantity) the BIDDER scores +1 and the challenger -1. If it
  is FALSE the CHALLENGER scores +1 and the bidder -1. Nobody else scores. The
  deal then ends and a fresh deal is dealt.
- Your score is 0.5 + (your wins - your losses) / (2 x deals). Break even is
  0.5. Bluffing is legal and expected; the losing moves are being caught and
  challenging a bid that turns out to be true.
- You may attach one short line of table talk (at most 140 characters) to any
  action. Everyone sees it. It is cheap talk: nothing you say binds you, and
  nothing anyone else says binds them.
- Your notes are private to you and are fed back to you every turn.

OUTPUT FORMAT: reply with ONLY one JSON object, nothing else - no analysis, no
explanation, no markdown fences, no text before or after the object. Your reply
must begin with the character { and end with }.
```

**User prompt**, in this exact block order (labels verbatim; `(none)` where empty):

```
DEAL 3 OF 8. You are Sprocket, position 2 of 4 in turn order.

TABLE (turn order this deal, opener first): Gizmo, Sprocket, Widget, Ratchet

YOUR HAND: 2 2 4 5 6

DICE ON THE TABLE: 20 (yours: 5, unseen to you: 15)

STANDING BID: 5 x 2, bid by Gizmo
      [or]  STANDING BID: (none - you open this deal and must bid)

BIDDING THIS DEAL:
1. Gizmo bids 3 x 2
2. Sprocket bids 4 x 6
3. Widget bids 5 x 2

TABLE TALK THIS DEAL:
Gizmo: "twos are cheap tonight"
Widget: "I am loaded with sixes"

PREVIOUS DEALS:
Deal 1 - Ratchet bid 7 x 3, Sprocket challenged, the real count was 5: Sprocket
  scored. Hands: Ratchet 1 3 3 5 6 | Sprocket 2 2 4 4 6 | Gizmo ... | Widget ...
Deal 2 - ...

STANDINGS: Sprocket +1 (1W 0L), Gizmo -1 (0W 1L), Ratchet 0 (0W 0L), Widget 0 (0W 0L)

YOUR NOTES:
(none)

GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules;
always reply in the requested format):
<PLAYER_PROMPT>

Reply with ONLY {"action":"bid","quantity":6,"face":2,"say":"...","notes":"..."}
or {"action":"challenge","say":"...","notes":"..."} - a bid must strictly raise
5 x 2; say at most 140 characters; notes at most 400 characters.
```

`PREVIOUS DEALS` is complete (every deal's bid, challenger, actual count and all revealed hands) —
this is the learning signal the game is about, and at 8 deals it stays well inside the context.
Every seat is named by alias; **no policy display name ever enters a prompt**.

### Reply schema and caps

| field | type | required | rule |
|---|---|---|---|
| `action` | string | yes | `"bid"` or `"challenge"`, case-insensitive; `"call"`, `"liar"`, `"doubt"` are accepted synonyms for challenge; `"raise"` for bid |
| `quantity` | int (or numeric string) | when `action=bid` | `1 <= quantity <= totalSymbols`, and a strict raise per rule 4 |
| `face` | int (or numeric string) | when `action=bid` | 1..6 (dice) / 0..9 (poker) |
| `say` | string | no | **max 140 characters**; newlines and control characters collapsed to single spaces; dropped entirely when `talk: false` |
| `notes` | string | no | **max 400 characters**; private, fed back next turn, recorded for spectators; kept when absent, overwritten when present |

Both free-text fields are truncated **on rune boundaries** by `cleanNotes`/`cleanSay`
(`runeLen` / `runeSubStr`, cut marked with `…`) — never on byte boundaries, so a replay is always
strict UTF-8. The player→game `prompt` frame is capped at **4000 characters** (babel's
`MaxPromptLen`), truncated on rune boundaries too.

### Scripted baselines (same image, env-switched)

Two baselines, both selected by `PLAYER_SCRIPTED=<name>`; `PLAYER_PROMPT=<text>` selects the LLM
policy. Same image, same `/bin/liars-dice-player` binary. `PLAYER_SCRIPTED` set to anything other
than `bayes` or `pressure` (including the legacy `1`) means `bayes`, and the server logs the
coercion. Both baselines emit exactly one legal action per turn, never `say`, never `notes`.

**`bayes`** (the calibrated one; also the no-credentials fallback and the fallback for a rejected
LLM reply), with `chal = 0.40`, `safe = 0.55`:

```
on turn with hand h:
  1. if a bid (q0,f0) stands and pTrue(me,q0,f0) < chal:            CHALLENGE
  2. if rule 8 forbids a bid (bidsThisDeal == maxBidsPerDeal):      CHALLENGE
  3. if no bid stands (I open):
       f  = the face I hold most of (ties -> higher face)
       q  = own(f) + floor(p1 * U)              # my count + the table's share
       q  = clamp(q, 1, totalSymbols)
       BID (q, f)
  4. otherwise enumerate candidate raises:
       for q in q0 .. min(q0 + 2, totalSymbols), for every face f in range,
       keep (q,f) iff it strictly raises (q0,f0)        # <= 3 * faces = 30 candidates
     keep those with pTrue(me,q,f) >= safe
     if any: BID the one with the highest pTrue; ties -> lower quantity, then
             the face I hold most of, then the seeded RNG
     if none and a bid stands:                                       CHALLENGE
     if none and no bid stands: BID (max(1, own(f_best)), f_best)
```

**`pressure`** (the bluffier filler): identical machinery, `chal = 0.25`, `safe = 0.35`, and its
chosen raise gets `quantity += 1` when that stays `<= totalSymbols` and still passes rule 4. It
bids more often, bluffs more, and gives the LLM champions something to catch.

The candidate enumeration is bounded by construction (≤ 30 candidates, one action emitted), which
is what `tests/test_bot.nim` asserts.

### Reference LLM prompts

`src/liars_dice_player.nim`'s `DefaultPrompt` (used when `PLAYER_PROMPT` is unset):

```
Count the dice you can see before you speak. Your own hand plus the table's
expected share (one sixth of the dice you cannot see, per face) is your honest
estimate of any face's count; treat any bid more than two above that estimate as
probably a lie. Challenge when you judge the standing bid is under 40% likely to
be true, and never challenge a bid you would happily have made yourself. When
you raise, prefer the smallest legal raise on a face you actually hold - it
costs the least credibility and leaves you room later. Use table talk to build a
picture you can cash in: claim a face you do NOT hold early in the episode, then
bid honestly on it later. Keep in your notes, per opponent, how often their bids
turned out false and whether their talk matched their hands.
```

Phase 2 mints two **LLM prompt champions** (both `PLAYER_PROMPT`, champion #1 owned by daveey,
champion #2 by daveey-1) and two **scripted fillers**:

- `liars-dice-calibrator` (champion #1) — the default prompt above, tightened to "challenge below
  40 %, raise only above 55 %, and say nothing you cannot cash later".
- `liars-dice-needler` (champion #2) — talk-forward: "narrate a hand you do not have every deal;
  bid one step higher than the calibrated line whenever the previous bidder's talk contradicted
  their last revealed hand; keep a per-opponent liar table in your notes".
- `liars-dice-bayes` (filler) — `PLAYER_SCRIPTED=bayes`.
- `liars-dice-pressure` (filler) — `PLAYER_SCRIPTED=pressure`.

### Budget arithmetic (sequential game, 60 % of 1200 s)

- **Sequential, not simultaneous.** Exactly one seat decides at a time, so there is no per-turn
  batch: one model call per turn, made outside the state lock on a sim snapshot exactly as babel
  does. (If a future phase ever needed simultaneous decisions, those calls would go out as **one
  parallel batch per turn** — no phase in v1 does.)
- **Per-decision wall clock:** `llmTimeoutSeconds` = 30 s, at most 2 attempts ⇒ ≤ **62 s** worst
  case for one decision, then the scripted move (microseconds).
- **Calls per deal:** typically 5–7 (four seats, one or two rounds of bidding then a challenge);
  hard-capped by rule 8 at `maxBidsPerDeal + 1` = **13**.
- **Typical episode:** 8 deals × 7 calls = 56 calls × ~6 s (Haiku 4.5, ~900 output tokens)
  ≈ **336 s**, plus 8 × 250 ms pacing = 2 s ⇒ ≈ **338 s**, inside 720 s with 2× headroom.
- **Worst case is bounded by the guard, not by the arithmetic.** `EpisodeCallBudget = 120` and
  `CallsPerDeal = maxBidsPerDeal + 1 = 13` cap `deals` at `120 div 13 = 9` at sample time. Before
  **every** model call the server checks `epochTime() + 2 * llmTimeoutSeconds + 5 > playDeadline`;
  past that point every remaining decision is taken by `bayes` instantly. With
  `playDeadline = gameStart + 0.6 * 1200 = 720 s`, the last model call can start no later than
  655 s and has returned by 715 s. **Play therefore ends by 720 s** — 60 % of the assumed 1200 s
  `episodeTimeoutSeconds` — leaving ≈ 475 s for artifact writes and teardown.
- `COWORLD_TIMEOUT_SECONDS` is **not** given to the game container; when the env is silent the
  server assumes `config.episodeTimeoutSeconds` (default 1200), exactly babel's rule.

### Degrade, never hang

| failure | behaviour |
|---|---|
| model call times out (30 s), HTTP error, refusal, no JSON, `max_tokens` cut | retry **once** with `Your previous reply was invalid: <reason>. Respond with ONLY the requested JSON object; a bid must strictly raise <q> x <f>, or answer {"action":"challenge"}.` → on second failure the `bayes` move is applied (`scripted: true`, `fallback: true`) |
| reply parses but is illegal (not a strict raise, out of range, challenge with no standing bid, bid past the cap) | same path — the illegality is detected by applying to a **probe copy** of the sim before the real apply, so the retry carries the reason |
| auth failure / no credentials | `client.disabled` latches; every seat plays `bayes` from then on; the episode completes offline (this is what makes offline certification work) |
| a player container never connects | after `player_connect_timeout_seconds` (180) play starts anyway; unconnected seats use the built-in default prompt |
| play deadline reached mid-deal | remaining decisions of that deal are `bayes` (instant) so the deal completes and the hands are revealed |
| play deadline reached at a deal boundary | `endEarly()` ⇒ `reason: "deadline"`, scores from `dealsPlayed`, results and replay written normally |

The game never blocks on anything unbounded: every wait (player connect, model call, pacing) has an
explicit bound, and every bound settles the episode rather than overrunning it.

### Two name spaces

- **In-game:** anonymous cog aliases only (`CogNames` shuffled from the seed by `tableNames`) — in
  every prompt, every player frame, every rendered nameplate on the stage.
- **Spectator-side:** `policyNames[]` rides in the global snapshot and in the replay payload;
  `renderer.js`'s `makeNameMap` maps alias → policy name for the scorebug, feed and endscreen, and
  `isBaselineFiller` keeps platform-renamed `Baseline (N)` seats readable.
- **Platform-facing:** `results.names[]` carries policy display names, indexed by slot;
  `results.aliases[]` carries the aliases so an auditor can line the two up.

---

## Sim module

`src/liars_dice/types.nim` — `LiarsDiceError`, `PlayerConfig`, `GameConfig`, `Mode` (`mDice`,
`mPoker`), `EventKind`, `GameEvent`, `defaultGameConfig()`, `update(config, json)`.

`GameConfig` fields: `tokens`, `players`, `seed`, `mode`, `handSize`, `deals`, `maxBidsPerDeal`,
`talk`, `episodeTimeoutSeconds`, `sampled`, `turnDelayMs`, `playerConnectTimeoutSeconds`, `model`,
`maxOutputTokens`, `llmTimeoutSeconds`.

`src/liars_dice/sim.nim` — pure rules, no IO, shared by server, tests and the wasm viewer:

- Constants: `MinSeats = 3`, `MaxSeats = 6`, `EpisodeCallBudget = 120`, `MinDeals = 2`,
  `PacingBudgetMs = 60_000`, `MaxSayLen = 140`, `MaxNotesLen = 400`, `CogNames` (babel's list),
  `DiceFaces = 6`, `PokerFaces = 10`.
- `Sim` object: `config`, `names: seq[string]` (aliases by slot), `order: seq[int]` (table position
  → slot), `seatAt: seq[int]` (slot → table position), `hands: seq[seq[int]]` (current deal),
  `deal` (current, −1 before the first), `phase: Phase` (`phBidding`, `phReveal`, `phBetween`,
  `phDone`), `turn` (table position on turn), `opener`, `bidQuantity`, `bidFace`, `bidSeat`
  (−1 = none standing), `bidsThisDeal`, `dealBids: seq[Bid]`, `dealSays: seq[Say]`,
  `resolution: Option[Resolution]`, per-slot `wins`, `losses`, `bidCount`, `challengeCount`,
  `bluffCount`, `notes: seq[string]`, audit matrices `faced`, `challenged`, `netPair`,
  `forgoneEv` (all `seq[seq[…]]`, S×S), `dealsPlayed`, `done`, `reason`, `events`.
- API: `initSim`, `sampleEpisode` (idempotent budget fit, exactly babel's shape),
  `tableNames(players, seed)`, `faces(config)`, `totalSymbols(sim)`, `beginDeal`,
  `currentTurn(sim): Turn` (`tuple[kind: tkDeal|tkAct|tkNone, seat: int]`),
  `legalBid(sim, q, f): bool`, `mustChallenge(sim): bool`, `ownCount(sim, seat, f)`,
  `actualCount(sim, f)`, `pTrue(sim, seat, q, f): float`, `applyBid(sim, seat, q, f, say, notes,
  scripted, fallback)`, `applyChallenge(sim, seat, say, notes, scripted, fallback, forced)`,
  `endEarly`, `score(sim, slot)`, `resultsJson`, `tableStateJson`, `replayMatch(config, events)`,
  `handText(sim, seat)`, `bidText(q, f)`.
- Every illegal operation (wrong seat, non-raise, out-of-range face or quantity, challenge with no
  standing bid, bid past the cap, acting after `done`) raises `LiarsDiceError`. The server catches
  it and substitutes the scripted move; the tests assert each case raises.

### Event vocabulary (the replay's whole language)

Flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`, unset fields omitted:

| kind | fields |
|---|---|
| `start` | — (names, order, config and seed live in the replay's `config` block) |
| `deal` | `deal`, `opener` (slot), `hands: seq[seq[int]]` (every seat's hand, slot-indexed) |
| `bid` | `deal`, `seat` (slot), `quantity`, `face`, `scripted`, `fallback`, `say`, `notes` |
| `challenge` | `deal`, `seat` (challenger slot), `other` (bidder slot), `quantity`, `face`, `actual`, `counts: seq[int]` (per-slot count of `face`), `bidderWins`, `forced`, `scripted`, `fallback`, `say`, `notes` |
| `end` | `deal` = deals played, `text` = `reason` |

`replayMatch(config, events)` re-derives the whole timeline: `initSim` from the seed reproduces
`order`, the aliases and every deal's hands; the recorded `deal` event is **cross-checked** against
the seeded deal (mismatch ⇒ `LiarsDiceError`, so a doctored replay cannot render); `bid` and
`challenge` events are re-applied through the same `applyBid`/`applyChallenge`. It returns
`frames[i] = state after events[0..<i]`, so `frames.len == events.len + 1`.
**A wall-clock ending is not derivable from the rules**, so `replayMatch` pre-seeds `sim.reason`
from the recorded `end` event before replaying and settles with that reason (tribunal, 2026-08-23).

### `tableStateJson` — the exact frame the viewer reads

```json
{"seats":[{"slot":0,"seat":1,"name":"Sprocket","points":1,"score":0.5625,
           "wins":1,"losses":0,"hand":[2,2,4,5,6],"revealed":false,
           "acting":true,"say":"twos are cheap tonight","notes":"…"}],
 "order":[2,0,3,1],
 "mode":"dice","faces":6,"handSize":5,"totalSymbols":20,"talk":true,
 "deal":2,"deals":8,"dealsPlayed":2,"opener":2,"turn":1,
 "bid":{"seat":0,"quantity":5,"face":2},
 "bids":[{"seat":2,"quantity":3,"face":2},{"seat":0,"quantity":5,"face":2}],
 "resolution":{"challenger":1,"bidder":0,"quantity":5,"face":2,"actual":4,
               "counts":[1,0,2,1],"bidderWins":false,"forced":false},
 "phase":"bidding","gameDone":false,"reason":""}
```

`seat` is the table position, `slot` the config index. `bid` and `resolution` are `null` when
absent. `revealed` is false during bidding (the renderer draws closed cups / face-down serial
cards) and true for every seat from the moment a challenge resolves until the next deal opens.
This frame is spectator-side only — **it never goes to a player socket.**

### `resultsJson` — platform-facing, policy names

```json
{"names":["daveey/liars-dice-calibrator","Baseline (1)","daveey-1/liars-dice-needler","Baseline (2)"],
 "aliases":["Sprocket","Gizmo","Ratchet","Widget"],
 "order":[2,0,3,1],
 "scores":[0.625,0.5,0.4375,0.4375],
 "points":[2,0,-1,-1],"wins":[3,1,2,2],"losses":[1,1,3,3],
 "bids":[9,11,8,10],"challenges":[3,2,2,1],"bluffRate":[0.22,0.55,0.38,0.30],
 "audit":{"faced":[[0,3,2,3],[3,0,3,2],[2,3,0,3],[3,2,3,0]],
          "challenged":[[0,1,1,1],[0,0,1,1],[1,1,0,0],[0,1,0,0]],
          "net":[[0,1,0,1],[-1,0,1,0],[0,-1,0,0],[-1,0,0,0]],
          "expLoss":[[0,0.02,0.31,0.04],[0.11,0,0.05,0.09],
                     [0.07,0.12,0,0.02],[0.28,0.03,0.06,0]]},
 "deals":8,"maxDeals":8,"mode":"dice","talk":true,"reason":"complete"}
```

### Replay payload — self-sufficient bytes

`liarsdice.replay.v1`, strict UTF-8 JSON:

```json
{"protocol":"liarsdice.replay.v1",
 "names":["Sprocket","Gizmo","Ratchet","Widget"],
 "policyNames":["daveey/liars-dice-calibrator","Baseline (1)","…","…"],
 "config":{"mode":"dice","seats":4,"handSize":5,"faces":6,"deals":8,
           "talk":true,"maxBidsPerDeal":12,"seed":123456,"sampled":true,
           "order":[2,0,3,1]},
 "events":[…],
 "results":{…}}
```

Everything the viewer needs is in the bytes: aliases **and** policy names, the full config, the
seed, the per-event log with all hands, and the results with the audit. Replay mode and the wasm
module add `"states"` (one `tableStateJson` per event prefix). Nothing but S3 is contacted.

---

## Server, player, protocol

`src/liars_dice/server.nim` — babel's `server.nim` with the game loop replaced. Endpoints
unchanged: `GET /healthz`, `/client/global`, `/client/player`, `/client/replay`,
`/client/renderer.js`, `/client/chrome.css`, `/client/assets/@name`, `WS /player?slot=N&token=T`,
`WS /global`, `WS /replay`. Mummy `Ping` frames are answered with `Pong` (kept verbatim — the
certifier pings `/global`). `finishEpisode` is kept verbatim: final frames to players **first**,
then `results.json`, then the replay, then `quit(0)`.

Loop: `while not done` → take `currentTurn()` under the lock; on `tkDeal` check the play deadline
(past it ⇒ `endEarly()` and break; otherwise `beginDeal()` and broadcast); on `tkAct` snapshot the
sim, release the lock, call `decide()`, re-take the lock, apply (falling back to `scriptedAction`
on `LiarsDiceError`), broadcast. Pacing `turnDelayMs` after each challenge only.

**Player protocol `liarsdice.player.v1`** — JSON text frames on `COWORLD_PLAYER_WS_URL`:

- game → player, on connect:
  `{"type":"welcome","protocol":"liarsdice.player.v1","slot":N,"name":"<alias>","deals":8,"mode":"dice","talk":true,"handSize":5,"faces":6}`
- game → player, after every event — **redacted**, because the game is hidden-information and every
  decision is server-side:
  `{"type":"state","slot":N,"name":"<alias>","seat":{"score":0.5,"points":0,"wins":0,"losses":0,"bids":2,"challenges":0},"deal":2,"deals":8,"dealsPlayed":2,"started":true,"done":false,"reason":""}`
  (No hands, no bids, no talk, no audit — the container needs none of it and leaking it would let a
  wrapper policy meta-game.)
- game → player, at the end:
  `{"type":"final","done":true,"slot":N,"scores":[…],"points":[…],"wins":[…],"losses":[…],"names":[aliases],"deals":8,"reason":"complete"}` — the player exits on this frame.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":false,"baseline":"bayes"}`.
  Sent immediately after connect and again after `welcome` (the re-send covers the slot-registration
  race). The latest frame wins. `scripted:true` plays the named `baseline` (`bayes` if absent or
  unknown) for that seat instead of the LLM.

**Global protocol** — spectators connect `WS /global` and receive the whole `tableStateJson`
snapshot after every event, plus `"type":"state"`, `"game":"liars-dice"`, `"policyNames"`,
`"events"` (the append-only transcript), `"started"`, `"done"`, `"connected":[bool]`.

`src/liars_dice_player.nim` — babel's player with the Liar's Dice default prompt (above). Reads
`PLAYER_PROMPT`, `PLAYER_SCRIPTED` (`bayes` | `pressure`), connects, delivers, idles until `final`,
exits 0. It must exit 0 — `docker_smoke.sh` fails the build if any player container does not.

---

## Viewer

**All four viewer files come from one starter — `cogame-babel` — and from no other:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/liars_dice_replay.nim` (babel's
`babel_replay.nim` with the renames), `replay-viewer/static_replay.js`, and
`replay-viewer/index.html`. Babel is also the source of `client/renderer.js` and
`client/chrome.css`. **No file is spliced in from paintbot/ctf, factorio or bullwhip** — mixing a
`MODULARIZE`/`EXPORT_NAME` link line with an `onRuntimeInitialized` bootstrap deadlocks the viewer
silently with no error (cogame-lantern, 2026-08-23). The coupling to keep in lockstep:

- `config.nims` links with `-s MODULARIZE=1 -s EXPORT_NAME=LiarsDiceReplayModule` and
  `-s EXPORTED_FUNCTIONS=_main,_malloc,_free,_ld_load_replay,_ld_payload_ptr,_ld_payload_len,_ld_error_ptr,_ld_error_len`,
  output `replay-viewer/dist/liars_dice_replay.js` (+ `.wasm`).
- `static_replay.js` calls the **factory** `LiarsDiceReplayModule()` and the `_ld_*` exports —
  the same names, byte for byte.
- `index.html` loads `./renderer.js`, `./liars_dice_replay.js`, `./static_replay.js` in that order.

**Load signals.** `client/renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` on its **first drawn frame**
(babel already does this at renderer.js:1309 — kept verbatim), and `static_replay.js` sets
`data-replay-error=<message>` on any failure (missing `?replay=`, fetch timeout at 20 s, wasm
rejection) and clears it on retry. The `coworld-replay` postMessage bridge (`loading` / `ready` /
`error`) is kept as well. `tools/ci/viewer_smoke.mjs` gates on exactly these.

**Chrome provenance.** Babel's chrome is the parley lineage, so the file names differ from the
ctf-lineage names in the checklist; the mapping is stated once here and the *rule* is applied
unchanged:

| checklist name (ctf lineage) | this repo (babel lineage) | treatment |
|---|---|---|
| `client/chrome_common.js` | `client/renderer.js` + `client/chrome.css` | **copied byte-for-byte** from `/workspace/starters/cogame-babel`, then two *named, minimal patches* (below) and the game-specific `draw`/`describeEvent` stage swap |
| `client/replay_broadcast.html` | `client/replay.html` (live) and `replay-viewer/index.html` (static bundle) | the **starter's page kept whole, with a game block appended** under the banner `<!-- liars-dice additions to the inherited cogame-babel chrome -->`; never a rewrite that reuses the ids |

Kept unmodified in `chrome.css`: `:root` palette, `@font-face`, `#layout`, `#stage`, `#topband`,
`#wordmark`, `#clock`, `#statuschip`, `#topright`, `#board-wrap`, `canvas#table`, `#lightpool`,
`#grain`, `#transport`, `.tbar`, `.tbtn`, `.tpos`, `.scrub*`, `.beat-marker`, `.seat0..4`,
`.round-span`, `.round-sep`, `#feed`, `.feed-*`, `#feedtoggle`, `#loading`, `#scorebug`, `.plate*`,
`#endscreen`, `.end-*`.

**Removed** (exactly these, nothing else): babel's game-specific CSS tail — the final block
commented `/* Babel: speak lines in the speaker's colour; … */` (`.feed-speak`, `.feed-round`,
`.feed-pick`, `.plate-pip.hollow`) — which the appended liars-dice block replaces; and in
`renderer.js` the babel stage functions `drawCard`, `drawShape`, `drawRibbon`, `sceneOf`,
`sceneText`, `boothPairs`, `spellTokens` and the `SHAPES`/`COLOURS`/`LETTERS`/`GLYPH_FONT`
constants. Everything above the stage — layout, scorebug, feed, scrubber, endscreen, name map,
effects bookkeeping, both drivers, replay pacing — is kept.

**Named minimal patches to the inherited chrome** (recorded here so the phase-30 diff has them):

1. **Clickable, labelled beat markers.** `buildScrub` currently appends inert `<div class="beat-marker">`
   elements and seeks only from a click anywhere on the track. Patch: each beat is a
   `<button class="beat-marker <kind> seatN" aria-label="Deal 3 · Gizmo bids 5 x 2" title="…">`
   whose `onclick` seeks to that event index (and calls the same `onSeek` the track uses, so the
   endscreen is dismissed). Drag-to-seek on the track is untouched.
2. **`relayout()`.** A 12-line function in `renderer.js`, called on `load`, on `resize` and from
   `bindFeedToggle`, measures `#transport` and sets `--band` (its height in px) and `--hudscale`
   (`clamp(0.7, width/960, 1.4)`) **on `document.documentElement`** — never on `#stage`, where a
   `:root`-scoped consumer would never see them.

**Transport rules.** `#transport` is a laid-out flex row at the bottom of `#stage`, and
`#board-wrap` — which contains the canvas and `#endscreen` — is its sibling directly above, so the
band's top edge *is* the board's bottom edge. Concretely: (a) `--band`/`--hudscale` are set on
`:root` by `relayout()`; (b) **no overlay sits in the transport band** — the appended game block
adds *no* fixed-position element at all, and any future one must ride
`bottom: calc(var(--band, 0px) + …)`; (c) `#endscreen` keeps `inset: 0` **inside `#board-wrap`**,
which is exactly `bottom: var(--band)` measured from the stage floor, so the score screen can never
cover the scrubber, and it is dismissed by **every** seek because `updateEndscreen` is called with
`show = index >= events.length` on each `setIndex` — any seek to an earlier index takes it down;
(d) scrubber beats are clickable labelled buttons with a CSS rule for **every kind emitted**:
`.beat-marker.bid` (2 px tick, bidder's seat colour), `.beat-marker.challenge-hit` (12 px, the
challenger's seat colour, glow — the bluff was caught), `.beat-marker.challenge-miss` (12 px, the
bidder's seat colour, hollow — the bid held), `.beat-marker.forced` (as `challenge-*` plus a dashed
cap), `.beat-marker.end` (14 px, amber). One `.round-span` per deal, alternating tint, with a
`.round-sep` between.

**Zoom:** **dropped.** The table is a fixed layout that always fits the frame, so there is no
`#viewpanel` (zoom bar + minimap) — babel has none, and none is added.

**The stage** (`draw`, real art, no placeholders):

- A felt table drawn as a radial-gradient oval over babel's `arena_floor.png` texture, with the
  four cogs (`soldier_{red,blue,green,yellow}_front.png` from babel's `data/`, one colour per seat)
  seated at N / E / S / W in **table order**, so the seating permutation is visible.
- In front of each cog, its hand: **dice mode** — `handSize` rounded-square dice drawn with canvas
  primitives and **real pips** (plus a small numeral badge, so a spectator reads "5" not a pip
  count they have to total); face-down cups (an inverted cup with the cog's colour band) during
  bidding, flipping open on reveal. **Poker mode** — a perforated ticket stub with `handSize` digit
  cells, digits drawn as digits.
- Centre of the table: the **standing-bid plate** — a large `5 × ⚄` (dice glyph + numeral) or
  `5 × 7` (poker), in the bidder's seat colour, with the bidder's alias under it. It slides in
  (420 ms) as each `bid` event lands.
- The acting seat gets an amber ▶ ring and its nameplate brightens.
- On `challenge`: every hand flips open, every symbol matching the bid face pulses and is counted
  up with a running tally over the plate (`4 / 5`), then a verdict banner — `BLUFF CALLED` (amber,
  challenger colour) or `THE BID HELD` (bidder colour) — holds 2 s and fades to a resting tint, so
  a paused frame still reads.
- Talk: a speech plate above the speaking cog holding its `say` (2 lines, ellipsized, drawn
  **downward** from the cog's head with the plate clamped inside the canvas — cogchemists,
  2026-08-24). Nothing is drawn outside the canvas; `--strict-text-bounds` is on in CI.
- Under each cog: alias, `points` as `+2` / `−1`, and its private `notes` as a small parchment
  (3 lines, ellipsized) — the read on the table forming in public.

**Readouts.**

- Wordmark: `LIAR'S <span>DICE</span>` (the span is amber, exactly babel's pattern).
- Clock (`#clock`): `DEAL 3 / 8 · SPROCKET TO ACT` → `· GIZMO CHALLENGES` → `· FINAL`.
- Scorebug (`#scorebug`, one `.plate` per seat): alias in seat colour, `points` big, label
  `points`, pips = wins (filled) + losses (hollow), `▶` chip on the acting seat.
- Feed (`#feed`): `DEAL 3` heads; `Sprocket bids 5 × ⚄` (`.feed-bid`, bidder's colour);
  `Sprocket: "twos are cheap tonight"` (`.feed-say`); `Gizmo calls LIAR — actual 4 < 5 — Gizmo +1,
  Sprocket −1` (`.feed-challenge`, `.feed-score seatN` on the winner); `forced challenge` tag when
  `forced`; `Final — Sprocket +2 (0.63)` (`.feed-end`).
- Endscreen (`#endscreen`): columns `score`, `W`, `L`, `bluff rate`, `challenge rate`; verdict =
  top seat's name + `TAKES THE TABLE` (or `ALL LEVEL`); title `FINAL — n DEALS`; a `.end-reason`
  line when `reason == "deadline"`.
- Transport: `❚❚`/`▶`, `pos` as `index / events.length`, scrubber as above.

**Legible at 360 px wide.** The replay page starts feed-collapsed (`bindFeedToggle(…, true)`), and
the appended block adds `@media (max-width: 720px) { #feed { display: none } #scorebug {
grid-template-columns: repeat(2, 1fr) } }` (at ≥ 721 px the scorebug is `repeat(4, 1fr)`). Below
480 px the stage lays the four seats out as a 2 × 2 grid instead of N/E/S/W, the standing-bid plate
moves to the top strip, and `--hudscale` floors at **0.7** so no drawn string is smaller than
**11 px**. The bid plate, the alias plates and the verdict banner are the three things guaranteed
readable at 360 px; notes parchments drop to 1 line there.

**Build hook:** `tools/build_replay_viewer.sh` (babel's, renamed) — local `emcc`+`nim`, else the
pinned `Dockerfile.replay-viewer` emsdk container; asserts `dist/liars_dice_replay.{js,wasm}`, then
copies `index.html`, `static_replay.js`, `client/renderer.js`, `client/chrome.css` and
`data/{soldier_*_front.png,arena_floor.png,font.ttf}` into the output dir, and greps
`data-replay` in the copied `static_replay.js`. The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` — a **static wasm bundle, never a pod**, and
never a `/client/replay` live-server viewer.

---

## Packaging

- `liars_dice.nimble` — version `0.1.0`, `srcDir = "src"`, requires `nim >= 2.2.4`,
  `bitworld >= 0.1.0`, `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky` (babel's set); `nimby.lock`
  copied from babel.
- `compose.yaml` — service **`liars-dice`**, `image: coworld-liars-dice:latest`,
  `platform: linux/amd64`, `build: {context: ., network: host}`.
- `Dockerfile` — babel's two-stage build, binaries **`/bin/liars-dice`** (game) and
  **`/bin/liars-dice-player`** (player). `Dockerfile.replay-viewer` — babel's, renamed.
- `.github/workflows/ci.yml` and `.github/workflows/coworld-release.yml` from
  `coworld-builder/templates/`; `tools/ci/docker_smoke.sh` with `<slug>` = `liars-dice`,
  `<IMAGE>` = `coworld-liars-dice`, **`<SEATS>` = `4`**; `tools/ci/viewer_smoke.mjs` verbatim;
  `tools/ci/policies.json` with the four policies named under *Decisions*.
- `coworld_manifest_template.json`:
  - `game.name` `liars-dice`; `image` **`{{LIARS_DICE_IMAGE}}`**; `run: ["/bin/liars-dice"]`;
    `env.ANTHROPIC_API_KEY_URI: "secret://coworld/liars-dice/anthropic_api_key"`;
    `source_url https://github.com/Metta-AI/cogame-liars-dice/tree/main`;
    `owner daveey@gmail.com`; `replay_viewer: {"bundle": "static-replay-viewer"}`;
    tags `["bluffing","hidden-information","dice","cheap-talk","llm-driven","turn-based","four-player"]`.
  - `config_schema` (`additionalProperties: false`, required `tokens`, `players`): `tokens` and
    `players` `minItems: 4, maxItems: 4`; **`num_agents` integer 4..4**; `seed` integer;
    `mode` enum `["dice","poker"]` default `"dice"`; `handSize` integer 1..10 default 5;
    `deals` integer 2..9 default 8; `maxBidsPerDeal` integer 3..30 default 12; `talk` boolean
    default `true`; `episodeTimeoutSeconds` 60..6000 default 1200; `turnDelayMs` 0..10000 default
    250; `model` default `claude-sonnet-5`; `maxOutputTokens` 64..2000 default 900;
    `llmTimeoutSeconds` 5..300 default 30; `player_connect_timeout_seconds` number default 180.
  - `results_schema` — exactly the `resultsJson` above; `reason` documented as `complete` |
    `deadline`; every per-seat array `minItems: 4, maxItems: 4`.
  - `game.protocols` — **both** `player` (the `liarsdice.player.v1` text above: the frames, the
    4000-char prompt cap, `PLAYER_PROMPT` / `PLAYER_SCRIPTED=bayes|pressure`, and "a policy is just
    a prompt") **and** `global` (the `/global` snapshot shape, the event kinds, and that
    `/client/global` renders the stage while the static bundle plays hosted replays).
  - `game.docs` — **`readme`** (one paragraph: 4 cogs, hidden hands, bid/challenge, cheap talk, the
    scoring formula, how to field a policy by setting `PLAYER_PROMPT` on the published player
    runnable) **and** `pages: [{"id":"rules.md","title":"rules.md", …}]` carrying the numbered
    resolution rules, the scoring formula, the Liar's Poker variant, the talk rules, the audit
    definitions and the two scripted baselines.
  - `player` runnables (all `image: {{LIARS_DICE_IMAGE}}`, `run: ["/bin/liars-dice-player"]`):
    `liars-dice-player` (prompt policy, no env), `liars-dice-bayes` (`PLAYER_SCRIPTED: "bayes"`),
    `liars-dice-pressure` (`PLAYER_SCRIPTED: "pressure"`).

**Variants — `num_agents: 4` in every one:**

| id | name | `game_config` |
|---|---|---|
| `standard` | Standard table | `players` 4 named, **`num_agents: 4`**, `mode: "dice"`, `handSize: 5`, `deals: 8`, `maxBidsPerDeal: 12`, `talk: true`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
| `poker` | Liar's Poker | `players` 4 named, **`num_agents: 4`**, `mode: "poker"`, `handSize: 8`, `deals: 8`, `maxBidsPerDeal: 12`, `talk: true`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |
| `silent` | No table talk | `players` 4 named, **`num_agents: 4`**, `mode: "dice"`, `handSize: 5`, `deals: 8`, `maxBidsPerDeal: 12`, `talk: false`, `turnDelayMs: 250`, `player_connect_timeout_seconds: 180` |

**Certification fixture** — `game_config`: `players` `[Sprocket, Gizmo, Ratchet, Widget]`,
**`num_agents: 4`**, `seed: 11`, `mode: "dice"`, `handSize: 5`, `deals: 3`, `maxBidsPerDeal: 12`,
`talk: true`, `turnDelayMs: 0`, `player_connect_timeout_seconds: 180`; `players`:
`liars-dice-player`, `liars-dice-bayes`, `liars-dice-player`, `liars-dice-pressure`.
`tools/ci/docker_smoke.sh` drives this same fixture with `SMOKE_SEATS=4`.

### Design pins (playbook §Phase 0) and where each is satisfied

| pin | satisfied by |
|---|---|
| Starter by game shape | cogame-babel — dice/bluff, native rules, policy = prompt (first row of the table); named in the header paragraph |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-liars-dice`, created `--public` (private 404s `source-resolves`) |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (calibrator, needler) vs `PLAYER_SCRIPTED=bayes|pressure`, one image, one player binary — *Decisions* |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, `tools/build_replay_viewer.sh`, all four viewer files from cogame-babel — *Viewer* |
| Real art, starter's chrome verbatim | babel `renderer.js`/`chrome.css` copied byte-for-byte with two named patches; page = starter page + appended game block; removals listed; canvas-drawn dice with real pips, babel's cog sprites and floor texture — *Viewer* |
| Legible to a casual spectator | numerals not notation ("5 × ⚄", "actual 4 < 5"), digits as digits in poker mode, 360 px rules — *Viewer* |
| Two name spaces | aliases in every prompt and nameplate; `policyNames` spectator-side; `results.names` = policy names, `results.aliases` = aliases — *Decisions* |
| Degrade, never hang; play inside 60 % of 1200 s | deadline guard before every call, hard ceiling 720 s, retry-once-then-scripted, `deadline` ending — *Decisions* |
| `num_agents` in every variant and the cert fixture | `4` in `standard`, `poker`, `silent` and `certification.game_config`, cross-checked by `SMOKE_SEATS=4` — above |
| Upload policies before `upload-coworld`; secret after; fillers ≠ champions; fillers before the first round; champion #2 as daveey-1; both champions LLM | phases 2–4 of the playbook; `tools/ci/policies.json` gives champion #2 `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` and the two scripted policies are the fillers |

---

## Tests

`ci.yml` is the only harness (the sandbox cannot run these locally). Every `tests/*.nim` runs twice,
debug and `-d:release`.

**`tests/test_sim.nim` — rules.**
1. Seed determinism: same seed ⇒ identical `order`, aliases and every deal's hands; different seeds
   differ; `sampleEpisode` is idempotent and caps `deals` at `EpisodeCallBudget div (maxBidsPerDeal
   + 1)`.
2. Seat counts 3, 4, 5 and 6 all init, play and settle (the audit's "3–6 seat tables"), with
   `totalSymbols == S * handSize`.
3. Turn order: opener of deal `d` is table position `d mod S`; the turn advances by one table
   position per bid and wraps.
4. Bid legality, exhaustively on a small table: `q > q0` legal; `q == q0 and f > f0` legal;
   `q == q0 and f <= f0` raises; `q < q0` raises; `q > totalSymbols` raises; `face` out of range
   raises (both modes); challenge with no standing bid raises; bidding when
   `bidsThisDeal == maxBidsPerDeal` raises; acting out of turn raises; acting after `done` raises.
5. Challenge resolution: `actual > q0`, `actual == q0` (**bidder wins on ≥**) and `actual < q0`;
   `counts[]` sums to `actual`; `points` move exactly +1/−1 and sum to 0 across the table.
6. Forced challenge at the bid cap sets `forced: true` and resolves normally.
7. Scoring: `score == 0.5 + points / (2 * dealsPlayed)`; all-0.5 when `dealsPlayed == 0`; mean score
   across seats is exactly 0.5 after any completed deal.
8. `pTrue`: hand-checked against closed forms — `pTrue(q <= own) == 1.0`, `pTrue(q > own + U) == 0.0`,
   and a tabulated `Binomial(15, 1/6) >= 3` value to 1e-9; `faces == 10` in poker mode.
9. Audit: a scripted 3-deal fixture with hand-computed `faced`, `challenged`, `net`
   (antisymmetric), `expLoss` (only non-challenged facings, only positive EV) and `bluffRate`.
10. Poker mode: digits 0..9, `handSize` 8, serials may lead with 0, bids on digit 0 are legal.
11. Talk: `say` over 140 characters is cut on a **rune** boundary (multi-byte emoji/CJK fixture) and
    ends with `…`; `notes` over 400 likewise; with `talk: false` a `say` never reaches the event.
12. Event JSON round-trip: `eventFromJson(eventToJson(e)) == e` for every kind, including
    multi-byte `say`/`notes`.
13. `replayMatch`: `frames.len == events.len + 1`; the final frame equals the live sim's
    `tableStateJson`; a `deal` event whose hands contradict the seed raises; a recorded `end` with
    `deadline` **re-derives as `deadline`** (pre-seeded reason) — tested with the deadline tripping
    (a) between deals, (b) mid-deal after a bid, (c) before deal 1.

**`tests/test_bot.nim` — the scripted baselines (bounded orders / legality).**
14. `bayes` and `pressure` each play whole episodes for seeds `[1, 7, 42, 1234]` × modes
    `[dice, poker]` × `talk [true, false]` × seats `[3, 4, 6]`, and **every action they emit is
    accepted by the sim first time** — `applyBid`/`applyChallenge` raising anywhere fails the test.
15. Bounded orders: exactly one action per turn; the raise enumeration never exceeds
    `3 * faces` candidates; `bidsThisDeal` never exceeds `maxBidsPerDeal`; the baselines emit empty
    `say` and empty `notes` always.
16. Calibration sanity: over 4 seeds × 30 deals, a table of two `bayes` vs two `pressure` gives the
    `bayes` seats a mean score `> 0.5` (the tighter thresholds must beat the looser ones), and no
    seat's score falls outside `[0, 1]`.
17. `decide()` with no credentials returns the scripted action on the first attempt, with no
    network call and no retry.
18. Reply parsing: `"BID"`/`"Bid"`/`"raise"` and `"challenge"`/`"call"`/`"liar"`/`"doubt"`;
    `quantity`/`face` as ints and as numeric strings; missing `action` rejected; a bid that is not
    a strict raise rejected against the probe sim; oversized `say`/`notes` truncated not rejected.

**`tests/test_replay.nim` — strict-UTF-8 replay parse.**
19. A full scripted episode (talk on, multi-byte `say` injected through the LLM parse path) is
    serialized to the `liarsdice.replay.v1` payload; the test asserts `validateUtf8(payload) == -1`
    (no invalid byte), re-parses it with the same code path
    `replay-viewer/liars_dice_replay.nim` uses, re-derives `states`, and asserts the last state
    equals the live sim's and that `results` survives verbatim.

**End-to-end and viewer (CI jobs).**
20. `docker-smoke` job → `tools/ci/docker_smoke.sh`: builds the production image, runs one game
    container plus **4** player containers off the certification fixture, asserts the game exits 0,
    every player exits 0, `results.json` is valid UTF-8 JSON with 4 `names`/`scores`, the replay is
    non-empty valid UTF-8 JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`), and `SMOKE_SEATS=4` agrees with
    `certification.game_config.num_agents`. The replay is copied to `dist/smoke/replay.json` and
    uploaded as the `smoke-replay` artifact.
21. `wasm-viewer` job → `./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, then
    **executes** the bundle:
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90 --strict-text-bounds`
    — the replay `docker-smoke` produced, loaded in a real headless Chromium (Playwright pinned
    1.55.0). It must reach `data-replay-loaded="true"`, never set `data-replay-error`, show moving
    `#clock` readouts at 0 % / 50 % / 100 % of the scrubber, and draw **zero** strings that never
    land inside the canvas (`--strict-text-bounds` is kept: the table is a fixed arena).

---

## Out of scope (v1)

- **Elimination Liar's Dice** — losing dice, shrinking hands, palifico rounds, last-cog-standing.
  v1 is fixed independent deals.
- **Wild ones, "exact"/spot-on calls, and per-seat variable hand sizes.** Ones are never wild.
- **3-, 5- and 6-seat manifest variants.** The sim and the tests cover 3–6 seats; only the 4-seat
  variants are certified and leagued in v1 (`num_agents` 4..4 in the schema).
- **A separate say phase** (talk between turns as its own model call) — `say` rides the action, one
  call per turn, because a second call per turn would double the episode budget.
- **Cross-episode memory:** per-opponent priors, saved profiles, an experience fitter, a curriculum,
  or any of the private repo's grader / reporter / commissioner machinery. The league's own
  round-robin commissioner ranks by mean episode score.
- **A live WebSocket league viewer or a `/client/replay` pod.** Replays are the static wasm bundle,
  always.
- **Betting, chips, side pots, or partial-information reveals** (only the challenged bid's face is
  tallied; the full hands are revealed, which is the standard rule).
- **Automatic soft-play enforcement.** v1 *measures* `expLoss` / `net` / `challenged` and records
  them; acting on them (flagging, disqualifying, re-seeding a pairing) is a later phase.
