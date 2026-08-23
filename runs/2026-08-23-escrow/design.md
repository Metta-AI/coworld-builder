# Escrow: binding contracts as a coworld

Four cogs on a trading floor with three goods, private comparative advantage, and a contract
language the game itself executes. Built by forking **`cogame-bullwhip`** (the newest
parley-lineage starter: Nim game server on the Coworld runtime contract, a policy that is just a
prompt, an always-available scripted baseline, one pure `sim` module shared by server / tests /
wasm viewer, the parley broadcast chrome around a canvas stage) — chosen because Escrow has
exactly bullwhip's shape: a turn-based, simultaneous-decision, mixed-motive economic game whose
seats reason in text and answer with a small structured payload, and whose watchability comes
from a scorebug + feed + stage rather than from a physics loop. **Every convention in
`cogame-bullwhip` holds here unless this note says otherwise.** The §Phase 0 pins from
`playbooks/make-coworld.md` are answered throughout and tabulated at the end of `## Packaging`.

**Source idea, verbatim** (Asana idea task 1217704516772355 — "11 Escrow — cheap talk is free;
here you can also sign"):

> A trading economy (three goods, comparative advantage) where agents draft contracts in a tiny
> state-machine DSL — 'I deliver 5 ore by turn 8, you pay 12 hearts, else escrow forfeits to me' —
> that the game enforces. Breach is impossible; the skill is drafting, pricing, and spotting
> loopholes in other people's clauses. Most hearts at horizon.
>
> Seats: 4-6
> Motive: mixed-motive
> Policy interface: LLM prompt + DSL output
> Fills gap: binding commitments / contract design / mechanism literacy
> Integrity (anti-collusion): Naturally sturdy: commitments are in-band by design, so any side deal
> has to be written as an enforceable contract inside the game — there is nothing useful to agree
> out-of-band.
>
> Replay plan (watchability): A trading floor: goods crates move between booths, signed contracts
> pin to a central escrow board as sealed scrolls with countdown seals. A triggered contract pays
> out of an opening chest; an exploited loophole burns the scroll on stage.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

## The game

**Seats: exactly 4 (`num_agents` = 4).** The idea allows 4–6; 4 is chosen because (a) the starter
ships exactly four cog sprites (`soldier_{red,blue,green,yellow}_front.png`), so the floor is real
art with no placeholder seat, (b) four booths around a central escrow board stay legible at 360 px,
and (c) a four-call parallel batch per turn keeps the wall-clock arithmetic below comfortably
inside the 720 s play budget. Four seats already give twelve ordered counterparty pairs — plenty of
market.

Seats play under **anonymous cog aliases** drawn from the seed (`CogNames` in the starter's
`sim.nim`: Sprocket, Gizmo, Ratchet, Widget, …). Policy display names never enter a prompt; they
appear only in `results.names` and in the spectator/replay `policyNames` map.

### Goods, profiles, and where hearts come from

Three goods: **ORE, GRAIN, TIMBER**. One currency: **HEARTS** (integer, the score).

Each seat is dealt one of four **profiles** — a seeded permutation over seats, exactly as bullwhip
deals stages, so no slot is structurally stuck with one role:

| Profile | produces per turn (ore/grain/timber) | commission (consumes → pays) |
|---|---|---|
| `Mason` | 6 / 1 / 1 | 2 GRAIN + 2 TIMBER → **10 hearts** |
| `Farmer` | 1 / 6 / 1 | 2 TIMBER + 2 ORE → **10 hearts** |
| `Forester` | 1 / 1 / 6 | 2 ORE + 2 GRAIN → **10 hearts** |
| `Factor` | 2 / 2 / 2 | 2 ORE + 2 GRAIN + 2 TIMBER → **12 hearts** |

Production and commission-filling are **automatic** — no seat decides them. The only decisions are
transfers, contracts and talk, so the DSL is the whole action space that matters.

**A seat may fill at most `MaxFills` = 2 copies of its commission per turn**, greedily, from free
stock. This is the only source of new hearts in the game (`heartsMinted` in the results); every
other heart movement is a transfer between seats and is zero-sum.

Comparative advantage falls straight out of the table: a Mason's own 6 ore/turn is worthless to its
own commission and is exactly what the Farmer and Forester need; under autarky a Mason fills half a
commission a turn (5 hearts/turn) while a well-traded Mason fills two (20 hearts/turn, minus what
it paid). The implied price band is 2.0–2.5 hearts per unit (a Factor turns 6 bought units into 12
hearts; a specialist turns 4 bought units into 10), which is what makes pricing a clause a real
skill rather than a guess.

**Starting endowment (turn 0, before the first production):** every seat holds 3 ORE, 3 GRAIN,
3 TIMBER, **20 HEARTS**. Identical for all four seats.

### Turns

`turns` = number of decision turns (default **16**, min 4, max 40; certification fixture 6). Turn
`t` runs 0-based. Decisions within a turn are **simultaneous**: every seat sees the same public
floor and answers before anyone's answer is applied.

### Resolution order (total, numbered — the sim performs exactly these, in this order)

For turn `t`:

1. **Production.** Each seat's profile yield is added to its free stock.
2. **Observation and decision.** The public floor is snapshotted (post-production) and every seat's
   decision is obtained — one parallel LLM batch, or the scripted baseline (see
   `## Decisions`). A decision is `{give[≤2], offer[≤1], sign[≤2], say, notes}`.
3. **Signings**, applied in seat order 0,1,2,3, and within a seat in the order the reply listed
   them. A `SIGN Cn` is legal iff `Cn` is an offer that is still `offered`, was posted on turn
   `t−1`, is addressed to this seat, and this seat can pay the whole `ASK` bundle out of free
   stock. On success the acceptor's `ASK` bundle moves from free stock into the contract's escrow
   and the contract becomes `signed` (event `sign`, `ok:true`). On failure nothing moves; the
   contract stays `offered` (event `sign`, `ok:false`, with a reason) and will expire at step 6.
4. **Gives**, applied in seat order, then reply order. A `give` moves `n` units (1..99) of one good
   (or hearts) from the giver's free stock to another seat's free stock, immediately and with no
   strings. Illegal or unaffordable gives are **rejected and logged** (event `give`, `ok:false`,
   reason) — the rest of the seat's decision still applies. Every successful give is appended to
   `sim.transfers`, which is what the `PAID` condition reads.
5. **Offer registration**, in seat order. The offer's DSL is parsed and validated (see
   `## Sim module` → DSL). On success the contract is created with the next id `C1, C2, …`, the
   **proposer's `LOCK` bundle is moved from free stock into escrow immediately** (an offer on the
   board is always funded), status `offered` (event `offer`). On failure nothing moves (event
   `reject` with the reason).
6. **Expiry.** Every contract still `offered` that was posted on turn `t−1` expires: its proposer's
   escrow is returned to the proposer, status `expired` (event `expire`). An offer therefore lives
   exactly one turn: posted on `t`, signable only on `t+1`.
7. **Settlement.** Every `signed` contract with `due == t`, in ascending contract id: evaluate the
   condition against the state **as it now stands** (i.e. after steps 3–6 of this turn), take the
   `THEN` branch if true and the `ELSE` branch if false, and pay the two escrows out per the branch
   (see payouts below). Status `settled` (event `settle` recording the condition's truth value, the
   branch taken, the payout enum and every transfer it caused).
8. **Commissions.** Each seat, in seat order, fills up to `MaxFills` = 2 copies of its commission
   from free stock: goods consumed, hearts credited (event `fill` with the fill count and hearts).
9. **Tally.** The turn record is appended (`turn` event with the full public per-seat state), `turn`
   advances. If `turnsPlayed >= turns`, run the **horizon closure** (below) and settle
   `reason = "complete"`.

**Horizon closure.** When the episode ends — for either reason — every contract still `offered` is
expired (proposer refunded) and every contract still `signed` (a deadline beyond the horizon, or
never reached) is closed as `KEEP`: each side's escrow returns to whoever locked it. Nothing is
stranded, so "hearts at the end" is unambiguous.

### Payouts (the only four; nothing can be paid that is not already in escrow)

| Payout | effect |
|---|---|
| `SWAP` | proposer's escrow → acceptor; acceptor's escrow → proposer |
| `KEEP` | each side's escrow returns to its owner |
| `PROPOSER` | both escrows → proposer |
| `ACCEPTOR` | both escrows → acceptor |

**This is what "breach is impossible" means mechanically.** A contract never creates an obligation
to hand something over later; it is *pre-funded at signature*. The proposer's stake leaves its free
stock when the offer is posted and the acceptor's when it signs, both into escrow the sim owns.
Settlement only redistributes what is already locked, so non-performance cannot be a refusal to
pay — it is simply the `ELSE` branch firing and the escrow forfeiting. Escrowed goods and hearts
are visible on the board but unusable: they cannot be given away, cannot fill a commission, and do
not count toward a `HOLDS` condition (which reads **free** stock only). That last rule is the
engine of the loophole game: locking your own stock in an unrelated contract is how you make
someone's `HOLDS you 6 TIMBER` clause read false.

### Scoring, sign, and what the league ranks by

```
score(seat) = hearts(seat) after the horizon closure      # an integer, ≥ 0, HIGHER IS BETTER
```

Precisely: after step 9 of the final turn and after the horizon closure has refunded every escrow,
a seat's score is its **free heart balance**. Escrow-locked hearts count for the seat that locked
them, because the closure returns them first. Leftover goods are worth **zero** hearts — a seat
holding a warehouse of ore at the horizon scores nothing for it, so the last turns are a genuine
scramble to convert. The league ranks by mean episode `score` (higher wins); the sign is positive,
unlike bullwhip's `−cost`.

Results also report, per seat: `hearts`, `fills` (commissions filled), `signed` (contracts this
seat was party to that reached `signed`), `forfeits` (settled contracts where the payout sent both
escrows to the *other* party), and `profiles`.

### End conditions

- `reason = "complete"` — all `turns` turns resolved.
- `reason = "deadline"` — the episode clock stopped play between turns (see `## Decisions` →
  budgeting). Scores use the turns actually played, after the same horizon closure.

**`complete` and `deadline` are the only legal values of `results.reason`** (the field is `""` only
while the episode is still running and is never written that way to `results.json`).

### Per-seat observation — exactly what is visible and what is hidden

The floor is **open outcry**. Visible to every seat, every turn:

- Its own alias, profile, production vector, commission bundle and payout, the turn number and the
  horizon (`Turn 5 of 16`).
- Its own free stock (ore/grain/timber/hearts) and its own escrowed totals, per contract.
- The **floor table**: for *all four* seats — alias, profile, production vector, commission bundle
  and payout, free stock of each good, free hearts, escrowed totals.
- The **escrow board**: every live contract — id, proposer, addressee/acceptor, status
  (`offered`/`signed`), the `LOCK` and `ASK` bundles, `DUE` turn and turns remaining, the condition
  and both branches, rendered as the normalized DSL text; plus contracts settled or expired in the
  last 3 turns with their outcomes.
- The **ledger**: the last 6 turns of public events — gives, signings (with failures and reasons),
  offers, expiries, settlements, commission fills.
- The **messages** every seat sent last turn (`say` is public; all three others read it).
- Its own private `notes`.

Hidden from a seat: **only** the other seats' private `notes` (and, obviously, the other seats'
undelivered reasoning and this turn's not-yet-applied decisions). There is deliberately no hidden
inventory and no hidden price: this game is about commitment and clause-drafting, not concealment,
and a public floor is also what lets a spectator judge whether a contract was a good deal. State
this explicitly in the rules page so nobody builds a "hidden stock" variant by accident.

## Decisions: LLM with scripted fallback

Transport, credentials, the JSON-only output contract, `extractJsonObject`, `cleanText`, the
Bedrock model list and rotation, and "no credentials ⇒ every seat scripted" are ported **verbatim**
from `src/bullwhip/llm.nim` into `src/escrow/llm.nim`. Changes:

- **One parallel batch per turn.** All four seats decide simultaneously by rule, so the four model
  requests go out as a single `curly.makeRequests` batch. Replies that fail to parse or fail the
  legality probe are retried as one smaller second batch carrying the specific error as a hint;
  anything still failing falls back to the scripted baseline. 16 turns ≈ 16 round trips, not 64.
- **`maxOutputTokens` default 1100** (bullwhip's 900 is too tight once a 240-char contract and
  600-char notes share the reply; Haiku cutting off at `max_tokens` before the JSON closes is a
  known failure mode). `output_config.effort` is still omitted for haiku / `4-5` models.

### Reply schema (every free-text field capped; truncation on **rune** boundaries)

```json
{"give": [{"to": "Gizmo", "n": 4, "good": "ORE"}],
 "offer": "OFFER Gizmo\nLOCK 5 ORE\nASK 12 HEARTS\nDUE 8\nIF ALWAYS\nTHEN SWAP\nELSE KEEP",
 "sign": ["C3"],
 "say": "Ore at 2.5 hearts a unit, first come.",
 "notes": "Gizmo is short timber until turn 9; C3 forfeits to me if it stays short."}
```

| field | type | cap | on violation |
|---|---|---|---|
| `give` | array of `{to, n, good}` | **≤ 2 entries**; `n` 1..99; `good` ∈ ORE/GRAIN/TIMBER/HEARTS; `to` an alias ≠ self | entries past the 2nd dropped; a malformed entry makes the whole reply invalid |
| `offer` | string (DSL) or `""`/absent | **≤ 240 characters** | truncated at a rune boundary, then parsed — a truncation almost always fails the parser, which makes the reply invalid |
| `sign` | array of contract ids | **≤ 2 entries** | entries past the 2nd dropped |
| `say` | string | **≤ 160 characters** | truncated at a rune boundary with `…`; newlines collapsed to spaces; dropped entirely when `talk: false` |
| `notes` | string | **≤ 600 characters** | truncated at a rune boundary with `…` |

Every truncation uses the starter's `cleanText` (`runeLen` / `runeSubStr`) — never a byte slice. A
byte cut through a multi-byte character would put invalid UTF-8 into the replay and break its JSON,
which the strict-UTF-8 replay test (see `## Tests`) exists to catch.

`give`/`sign` accept `n` as an integer, a numeric string or a float (rounded), following bullwhip's
`parseDecision` tolerance. Missing fields mean "no action"; a reply of `{}` is legal and means
"pass".

### Degrade, never hang

- **Attempt 0** — one batch, all pending seats. A reply is accepted iff the JSON envelope parses,
  every field is within its cap, and a **probe apply on a copy of the sim** succeeds under the
  strict validator (offer DSL parses and validates, sign ids exist and are addressed to this seat,
  gives are affordable at probe time). This is bullwhip's `probe.applyOrder` pattern.
- **Attempt 1** — one retry batch containing only the failed seats, with the exact parser/validator
  error appended: `Your previous reply was invalid: <error>. Respond with ONLY the requested JSON
  object.`
- **Still failing** → the seat plays `scriptedAction(sim, seat, skTrader)`, which is always legal by
  construction. Logged as `scripted: true` on the `move` event so the replay is honest about it.
- **Execution-time rejection is not a hang either.** An action that was legal at probe time but
  became illegal by the time it applies (an earlier seat's signing consumed the goods) is rejected
  individually and logged (`ok:false` + reason); the rest of that seat's decision still applies.
- **A seat whose player container never connects** keeps an empty operator prompt and is played
  LLM-driven with the house rules only (bullwhip's behaviour, unchanged).
- **No credentials at all** ⇒ `client.disabled`, every seat immediately scripted, zero network
  waits. This is the path offline certification and `docker_smoke.sh` take, and it is load-bearing.

### Episode budgeting (the arithmetic, out loud)

`PlayBudgetFraction = 0.6`. `COWORLD_TIMEOUT_SECONDS` is **not** given to the game container, so
when the env is silent the game assumes `episodeTimeoutSeconds` (default 1200) ⇒ **play budget
720 s**.

- Per-turn wall clock is bounded by `MaxTurnSeconds = 2 × llmTimeoutSeconds + 5` = **125 s** with
  the default `llmTimeoutSeconds` 60 (attempt 0 + one retry + apply).
- Typical measured cost of one 4-call Haiku batch at 1100 max tokens: **15–25 s**. With
  `turnDelayMs` 400 pacing between turns, 16 turns × (20 + 0.4) ≈ **330 s** — well inside 720 s.
  Even a pessimistic 40 s/turn lands at 640 s.
- **The check before every turn's batch** is `epochTime() + MaxTurnSeconds > playDeadline` ⇒ stop
  now: `sim.endEarly()` (horizon closure, `reason = "deadline"`), broadcast, write results and the
  replay. A short honest episode always beats a long one the platform discards.
- `turnDelayMs` (default 400, cert 0) is clamped by `PacingBudgetMs` = 120 000 ms total, exactly as
  `sampleEpisode` does in the starter.

### Scripted baselines (same image, env-switched, fieldable policies)

`PLAYER_SCRIPTED=<name>` selects one; `PLAYER_PROMPT=<text>` is the LLM policy. Both run
`/bin/escrow-player` out of the **same image** — the difference is one environment variable.
`parseScriptKind`: `"1"/"true"/"yes"/"trader"` → `skTrader`; `"hoarder"/"autarky"` → `skHoarder`;
anything else `skNone`.

- **`trader`** (the sensible partner, and the universal fallback). Per turn, deterministically:
  1. Value everything at the house price table `ORE = GRAIN = TIMBER = 3 hearts`, `HEARTS = 1`.
  2. **Sign**: among offers addressed to it and still `offered`, take those it can afford whose
     `THEN` branch is `SWAP` or `ACCEPTOR`, valuing what it receives against what it locks; sign the
     best-valued one, then the next, up to 2, skipping any it cannot afford.
  3. **Offer**: let `surplus` be the good with the largest free stock above what two commission
     fills need, `deficit` the good it is shortest of for two fills, and `target` the seat with the
     largest free stock of `deficit`. Post
     `OFFER <target> / LOCK <min(4, surplus)> <SURPLUS> / ASK <same count> <DEFICIT> / DUE <t+1> /
     IF ALWAYS / THEN SWAP / ELSE KEEP`. Skip if it has no surplus, no deficit, or is at the live
     contract cap.
  4. Never gives unilaterally, never says, never writes notes.
- **`hoarder`** (the foil, bullwhip's `mirror` in spirit). Produces, fills commissions, and does
  nothing else: no offers, no signings, no gives, no talk. It is the autarky floor that any trading
  policy has to beat, and it makes "what is a contract worth?" measurable.

## Sim module

Fork `src/bullwhip/*` → `src/escrow/*`, keeping the module split and the "pure rules, no IO" rule:
the server, the tests and the wasm viewer all drive this same code.

### `src/escrow/types.nim`

`EscrowError`; `PlayerConfig`; `GameConfig` (bullwhip's, with `turns` replacing `weeks`, keeping
`talk`, `seed`, `episodeTimeoutSeconds`, `sampled`, `turnDelayMs`,
`playerConnectTimeoutSeconds`, `model`, `maxOutputTokens`, `llmTimeoutSeconds`);
`Good = enum gOre = "ORE", gGrain = "GRAIN", gTimber = "TIMBER", gHearts = "HEARTS"`;
`Bundle = array[Good, int]`; `Profile = enum pMason, pFarmer, pForester, pFactor`;
`SeatState` (`stock: Bundle` — free, hearts included; `escrowed: Bundle`; `fills`, `heartsEarned`,
`signedCount`, `forfeits`); `Payout = enum poSwap = "SWAP", poKeep = "KEEP",
poProposer = "PROPOSER", poAcceptor = "ACCEPTOR"`; `CondKind = enum ckAlways, ckHolds, ckPaid`;
`Condition` (`kind`, `negated: bool`, `who: int` seat, `n: int`, `good: Good`);
`ContractStatus = enum csOffered = "offered", csSigned = "signed", csSettled = "settled",
csExpired = "expired", csVoid = "void"`; `Contract` (`id`, `proposer`, `acceptor`, `lock`, `ask`,
`due`, `cond`, `thenPay`, `elsePay`, `status`, `postedTurn`, `signedTurn`, `text` — the normalized
DSL); `Transfer` (`turn`, `from`, `to`, `good`, `n`); `EventKind`; `GameEvent`;
`defaultGameConfig()`; `update()`.

### `src/escrow/dsl.nim` (new — the contract language)

**Grammar.** Exactly seven lines, in this order, keywords uppercase, one statement per line,
whitespace runs collapsed, the whole text ≤ 240 characters. The parser upper-cases the input before
matching, so a model that writes `offer gizmo` is still understood; the normalized upper-case form
is what goes on the board and into the replay.

```
OFFER <cog>
LOCK  <bundle>
ASK   <bundle>
DUE   <turn>
IF    <condition>
THEN  <payout>
ELSE  <payout>

<cog>       := one of the four table aliases
<bundle>    := NOTHING | <term> ( "+" <term> ){0,2}
<term>      := <n> <good>            ; n an integer 1..99
<good>      := ORE | GRAIN | TIMBER | HEARTS
<turn>      := integer
<condition> := ALWAYS | [NOT] HOLDS <cog> <n> <good> | [NOT] PAID <cog> <n> <good>
<payout>    := SWAP | KEEP | PROPOSER | ACCEPTOR
```

**Condition semantics**, evaluated at settlement (step 7), against the state as of that moment:

- `ALWAYS` — true.
- `HOLDS <cog> <n> <good>` — that cog's **free** (unescrowed) stock of `<good>` is ≥ `n`.
  `HEARTS` is a legal `<good>` here.
- `PAID <cog> <n> <good>` — `<cog>` must be one of the two parties; true iff the cumulative units
  of `<good>` that `<cog>` has transferred by open `give` **to the other party** since this
  contract was signed (inclusive of this turn's step 4) is ≥ `n`. Computed by summing
  `sim.transfers` with `turn >= contract.signedTurn`.
- `NOT` negates either of the two atoms.

**Validation rules** (all checked at registration, step 5; each failure produces a `reject` event
carrying the reason string, and nothing moves):

| # | rule | reason code |
|---|---|---|
| 1 | text ≤ 240 chars and exactly the seven keyword lines in order | `syntax` / `too_long` |
| 2 | `OFFER` names a table alias other than the proposer | `bad_target` |
| 3 | each bundle is `NOTHING` or 1–3 terms, each good at most once, each `n` in 1..99 | `bad_bundle` |
| 4 | `LOCK` and `ASK` are not both `NOTHING` | `bad_bundle` |
| 5 | `turn + 1 ≤ DUE ≤ min(turn + 6, turns − 1)` | `bad_due` |
| 6 | condition parses; every named cog is a table alias; a `PAID` cog is one of the two parties | `bad_condition` |
| 7 | `THEN` and `ELSE` are payout keywords | `bad_payout` |
| 8 | the proposer can pay the whole `LOCK` bundle from free stock right now | `unfunded` |
| 9 | neither proposer nor addressee is at the cap of `MaxLive` = 4 live contracts (offered + signed, either role) | `contract_cap` |

**Malformed DSL is never fatal and never silent.** During decision-making it makes the reply
invalid, which buys the seat one retry with the exact reason text; if the retry also fails the seat
plays the `trader` baseline for the turn. If a *scripted* or *replayed* offer somehow fails
validation the offer is dropped with a `reject` event and the turn continues.

**API:** `parseContract(text: string, sim: Sim, proposer: int): ParseResult` (either a `Contract`
with `status = csOffered` and `text` normalized, or a reason code + human message),
`renderContract(c: Contract): string` (the normalized seven lines, used by the board, the prompt
and the viewer), `evalCondition(sim: Sim, c: Contract): bool`.

**Worked examples** (these belong verbatim in the system prompt and in `docs` → `dsl.md`):

```
# the idea's example: a funded sale, settled next turn
OFFER Gizmo / LOCK 5 ORE / ASK 12 HEARTS / DUE 8 / IF ALWAYS / THEN SWAP / ELSE KEEP

# a performance bond: Gizmo only gets my ore if it has actually shipped me timber
OFFER Gizmo / LOCK 5 ORE / ASK 4 TIMBER / DUE 9 / IF PAID Gizmo 4 TIMBER / THEN SWAP / ELSE PROPOSER

# an insurance clause: if Ratchet is still short of grain at turn 11, the escrow is mine
OFFER Ratchet / LOCK 6 HEARTS / ASK 6 HEARTS / DUE 11 / IF NOT HOLDS Ratchet 4 GRAIN / THEN PROPOSER / ELSE KEEP
```

(The `/` is presentation only — the real text has one statement per line.)

### `src/escrow/sim.nim`

Constants: `Seats = 4`, `MinTurns = 4`, `MaxTurns = 40`, `MaxFills = 2`, `MaxGives = 2`,
`MaxSigns = 2`, `MaxLive = 4`, `MaxOfferChars = 240`, `MaxSayLen = 160`, `MaxNotesLen = 600`,
`MaxUnits = 99`, `DueWindow = 6`, `StartStock = 3`, `StartHearts = 20`, `PacingBudgetMs = 120_000`,
`ProfileNames`, `Production`, `Commission`, `CommissionPay`, `CogNames` (kept from the starter).

`Sim` = `config`, `names` (aliases), `profileOf[seat]`, `seatOfProfile[profile]`, `turn`,
`seats: array[4, SeatState]`, `contracts: seq[Contract]`, `nextId`, `transfers: seq[Transfer]`,
`moves: array[4, Move]` (live turn; `pending` until filled), `says[4]`, `heard[4]`,
`notes: seq[string]`, `history: seq[TurnRecord]`, `turnsPlayed`, `phase`, `done`, `reason`,
`events`.

API mirroring the starter one-for-one: `initSim`, `sampleEpisode`, `tableNames` (unchanged),
`pendingSeats`, `applyMove(sim, seat, decision, scripted)` (records the seat's move; **the fourth
move triggers `resolveTurn`**, which performs steps 3–9 and appends every derived event),
`endEarly` (horizon closure + `reason = "deadline"`), `resultsJson`, `tableStateJson`,
`replayMatch(config, events)`, `eventToJson`, `eventFromJson`, `score(sim, seat)`.

Everything random is drawn once in `initSim` from the seed: the profile permutation and the
aliases. Nothing else in the game is random, so a replay re-derives the whole episode from the
recorded `move` events alone.

### Event vocabulary (what the replay carries)

`move` events are **ground truth**; everything else is **derived by the rules and re-derived on
replay** (the `turn` event is additionally *checked* against the re-derivation, exactly as
bullwhip checks its `week` event).

| kind | fields |
|---|---|
| `start` | — |
| `turn` | `turn`, `seats: [{stock:{ore,grain,timber,hearts}, escrowed:{…}, fills, profile} ×4 by seat]`, `board: [contract summaries]` |
| `move` | `turn`, `seat`, `scripted`, `offer` (raw DSL text or `""`), `gives: [{to,n,good}]`, `signs: ["C3"]`, `say`, `text` (the seat's notes after this reply) |
| `offer` | `turn`, `seat`, `target`, `id`, `dsl` (normalized), `lock`, `ask`, `due`, `cond`, `then`, `else` |
| `sign` | `turn`, `seat`, `id`, `ok`, `text` (reason when `ok:false`) |
| `give` | `turn`, `seat`, `to`, `n`, `good`, `ok`, `text` |
| `reject` | `turn`, `seat`, `text` (reason code + message; a refused offer or an over-cap action) |
| `expire` | `turn`, `id`, `seat` (proposer refunded) |
| `settle` | `turn`, `id`, `cond` (rendered), `held` (bool), `branch` (`"then"`/`"else"`/`"horizon"`), `payout`, `transfers: [{to,n,good}]` |
| `fill` | `turn`, `seat`, `n` (copies filled), `hearts` |
| `end` | `turn` = turns played, `text` = reason |

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats":[{"name":"Sprocket","profile":"Mason","score":148,"hearts":148,
           "stock":{"ORE":7,"GRAIN":2,"TIMBER":0,"HEARTS":148},
           "escrowed":{"ORE":5,"GRAIN":0,"TIMBER":0,"HEARTS":0},
           "production":{"ORE":6,"GRAIN":1,"TIMBER":1},
           "commission":{"ORE":0,"GRAIN":2,"TIMBER":2},"commissionPay":10,
           "fills":9,"signed":4,"forfeits":1,
           "say":"Ore at 2.5.","heard":["…","…","…"],"notes":"…","pending":true} , ×4 by seat],
 "board":[{"id":"C7","proposer":0,"acceptor":2,"status":"signed",
           "lock":{"ORE":5},"ask":{"HEARTS":12},"due":8,"turnsLeft":3,
           "cond":"ALWAYS","then":"SWAP","else":"KEEP",
           "dsl":"OFFER Ratchet\nLOCK 5 ORE\nASK 12 HEARTS\nDUE 8\nIF ALWAYS\nTHEN SWAP\nELSE KEEP"}],
 "recent":[{"id":"C4","turn":6,"held":false,"branch":"else","payout":"ACCEPTOR",
            "transfers":[{"to":2,"n":5,"good":"ORE"},{"to":2,"n":8,"good":"HEARTS"}]}],
 "hearts":[148,131,96,120],
 "turn":7,"turns":16,"turnsPlayed":7,
 "phase":"moves|done","gameDone":false,"reason":""}
```

### `resultsJson` (platform-facing, **policy** names)

```json
{"names":["p1","p2","p3","p4"],"scores":[148,131,96,120],"hearts":[148,131,96,120],
 "fills":[9,8,5,7],"signed":[4,4,2,3],"forfeits":[1,0,0,1],
 "profiles":["Mason","Farmer","Forester","Factor"],
 "turns":16,"maxTurns":16,"heartsMinted":404,"reason":"complete"}
```

### Replay payload — self-sufficient bytes

`escrow.replay.v1`:
`{"protocol","names" (aliases, 4), "policyNames" (4), "config":{"turns","seed","talk",
"sampled":true}, "events", "results"}`. Replay mode and the wasm viewer add `"states"` (one
`tableStateJson` per event prefix). Everything the viewer needs — seat aliases, the policy-name map
for the spectator side, the turn count, **the seed** (from which profiles and aliases are
re-derived), the full event log and the final results — is in those bytes. The viewer contacts
nothing but S3 for the `.replay` file.

## Server, player, protocol

`src/escrow/server.nim` — the starter's `server.nim` with the game loop swapped: per turn, check
the play deadline, snapshot the sim, decide all pending seats in one batch **outside** the lock,
apply each move under the lock (the fourth apply resolves the turn), broadcast, pace by
`turnDelayMs`. Route table, `writeArtifact`, `finishEpisode` (final frames to players **before**
writing artifacts), the mummy Ping→Pong answer on `/global`, and the static-file handlers are kept
verbatim.

Endpoints unchanged: `GET /healthz`, `/client/global`, `/client/player`, `/client/replay`,
`/client/renderer.js`, `/client/chrome.css`, `/client/assets/<name>`, `WS /player?slot=N&token=T`,
`WS /global`, `WS /replay`.

**Protocol `escrow.player.v1`** (JSON text frames):

- game → player: `{"type":"welcome","protocol":"escrow.player.v1","slot":N,"name":"<alias>",
  "profile":"Mason","turns":16}` on connect;
  `{"type":"state","slot":N,"name":"<alias>","seat":{profile,score,hearts,stock,escrowed,
  production,commission,commissionPay,fills},"turn":int,"turns":int,"turnsPlayed":int,
  "board":[…],"started":bool,"done":bool,"reason":str}` after every event; and
  `{"type":"final","done":true,"slot":N,"scores":[…],"hearts":[…],"fills":[…],
  "profiles":[…],"names":[aliases],"turns":int,"reason":str}` at the end, after which the player
  exits.
- player → game: `{"type":"prompt","prompt":"…","scripted":"trader"}` — the prompt (**max 4000
  characters**, truncated on rune boundaries) is the policy; `scripted` selects a baseline.

The player frame carries the seat's own numbers and the public board — nothing is redacted because
nothing is secret except other seats' notes, which are never sent to a player socket. Decisions are
server-side, so the player socket is informational either way.

`src/escrow_player.nim` — the starter's player with an Escrow default prompt (in words: price goods
at 2–2.5 hearts a unit; never lock more than you can replace; put a `PAID` or `HOLDS` condition on
anything you cannot verify at signature; read the other side's `ELSE` branch first).

**Global protocol** (`/global` and the manifest's `game.protocols.global`): the full snapshot after
every event — `tableStateJson` plus `{"type":"state","game":"escrow","policyNames":[…],
"events":[…],"started":bool,"done":bool,"connected":[bool ×4]}`. The `events` array is append-only
and is the complete transcript.

**Two name spaces, restated where it bites:** prompts and player frames carry only aliases;
`policyNames` rides on the `/global` snapshot and in the replay for the **spectator side only**;
`results.names` is policy names because that is how the league attributes score.

## Viewer

**All four viewer files come from `cogame-bullwhip` and from nowhere else** —
`replay-viewer/config.nims`, the wasm entry `replay-viewer/escrow_replay.nim` (fork of
`replay-viewer/bullwhip_replay.nim`), `replay-viewer/static_replay.js`, and
`replay-viewer/index.html` are all forked from `cogame-bullwhip`, as a set. Do **not** splice a
shell, a bootstrap or link flags from any other starter: bullwhip's `config.nims` links with
`-s MODULARIZE=1 -s EXPORT_NAME=<Name>ReplayModule` and its `static_replay.js` calls that factory
(`EscrowReplayModule().then(…)`); pairing those flags with a paintbot-style
`Module.onRuntimeInitialized` bootstrap deadlocks the viewer silently with every file present and
200 (cogame-lantern, 2026-08-23).

Renames inside the fork: output `escrow_replay.js` / `.wasm`, `EXPORT_NAME=EscrowReplayModule`,
exported functions `_esc_load_replay, _esc_payload_ptr, _esc_payload_len, _esc_error_ptr,
_esc_error_len`, and the matching `exportc` names in `escrow_replay.nim`. The wasm module parses
the replay with the **same** `src/escrow/sim.nim` the server runs and re-derives every frame in the
browser.

**Readiness markers.** `static_replay.js` sets `document.documentElement.setAttribute(
"data-replay-loaded", "true")` on the **first drawn frame** (inside the same double
`requestAnimationFrame` that posts the `{src:"coworld-replay", type:"ready"}` bridge message), and
sets `data-replay-error="<message>"` on any failure (fetch timeout, wasm rejection, missing
`?replay=`), removing it on a retry. The starter's renderer also sets `data-replay-loaded`; the
shell setting it too is deliberate — it is the signal `tools/ci/viewer_smoke.mjs` waits for and it
must survive being loaded top-level with the postMessage bridge inert.

**Packaging:** static wasm bundle, never a pod. The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` (the
`coworld build` hook, committed **executable**, mode 100755) compiles the sim to wasm — locally via
`nim c -d:emscripten`, otherwise via the pinned `Dockerfile.replay-viewer` emsdk container — and
copies `escrow_replay.js`, `escrow_replay.wasm`, `replay-viewer/index.html`,
`replay-viewer/static_replay.js`, `client/renderer.js`, `client/chrome.css` and `data/` assets
(`soldier_{red,blue,green,yellow}_front.png`, `arena_floor.png`, `heart_red.png`, `font.ttf`) into
the bundle directory, then asserts `index.html` exists and `static_replay.js` still contains
`data-replay`.

**Chrome: bullwhip's, verbatim.** `client/chrome.css`, `client/{global,player,replay}.html` and the
whole chrome half of `client/renderer.js` — topband, wordmark, clock, status chip, scorebug, feed +
`bindFeedToggle`, scrubber and transport bar, endscreen, name map (alias → policy name for
spectators), effects timing, both drivers (`attachLive` / `attachReplay`) and the replay pacing —
are kept as they are. Only the wordmark text changes (`ES<span>CROW</span>`) and the **stage** is
replaced.

**The stage: the trading floor.** Four booths, one per seat, at the four corners of the canvas
around a **central escrow board**:

- **Booth**: the cog sprite in its seat colour (the starter's four soldier sprites — real art),
  profile tag (`MASON`), alias (spectator view: the policy name), a big heart count, and its stock
  as the starter's crate clusters (`drawCrateCluster` / `drawCrate`, kept, recoloured per good:
  ore slate `#8d97a3`, grain wheat `#d9b04a`, timber the starter's `CRATE` brown), with escrowed
  stock drawn greyed behind a small padlock. Its `say` appears in the starter's speech bubble.
- **Gives** animate as a crate stack sliding booth → booth along the floor (the starter's
  `SLIDE_MS` easing), hearts as a small coin puck.
- **Escrow board (centre)**: one **sealed scroll** per live contract, showing `C7`, the two locked
  bundles as tiny crate icons on either side of the seal, the two parties' colour chips, the
  condition in one legible line (`IF Ratchet HOLDS 4 GRAIN`), and a **countdown seal** reading
  `DUE IN 3`. An `offered` scroll is unsealed with a dashed edge; `signed` is wax-sealed.
- **Settlement**: the scroll unrolls, the chest under the board opens, and the escrow's crates fly
  to whoever the branch names. A branch that sends both escrows to one party (`PROPOSER` /
  `ACCEPTOR` — the forfeit / "exploited loophole") **burns the scroll on stage**: it chars and
  falls away while the crates leave, with the condition line struck through.
- **Commission fills** pop a small `+10 ♥` over the booth.

**Feed lines** (legible, not notation): `TURN 5` heads; `Sprocket offers C7 to Ratchet — 5 ore for
12 hearts, due turn 8`; `Ratchet signs C7 — escrow sealed`; `Sprocket gives Gizmo 4 ore`;
`C7 settles: ALWAYS → SWAP. Sprocket +12 hearts, Ratchet +5 ore`; `C4 settles: Ratchet holds
4 grain? NO → ACCEPTOR. Gizmo takes the whole escrow (5 ore + 8 hearts)`; `C2 expires unsigned —
3 grain back to Widget`; `Widget fills 2 commissions +20 hearts`; `Sprocket says: …`;
`Final — Gizmo 148 hearts`.

**Readouts:** scorebug (per seat: colour chip, name, hearts, the three stock counts, an escrow
badge), clock (`TURN 7 / 16`), status chip (`live` / `replay`), feed, scrubber + transport, and the
endscreen table with columns `hearts`, `fills`, `signed`, `forfeits`, verdict = the highest heart
count + `MOST HEARTS AT HORIZON`.

**Legible at 360 px wide:** at that width the booths drop their production/commission tags and keep
sprite + alias + hearts; the escrow board collapses to a single stack of scrolls with a count badge
and only the soonest-due scroll expanded; the feed is off by default behind the starter's `LOG »`
toggle; every number is rendered as a numeral (`12`, `+10 ♥`), never as an abbreviation or internal
enum.

## Packaging

- `escrow.nimble` — version, `srcDir = "src"`, the starter's `requires` set (`nim >= 2.2.4`,
  `bitworld`, `mummy`, `curly`, `whisky`), plus `nimby.lock` copied from the starter.
- `compose.yaml` — service **`escrow`**, `image: coworld-escrow:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- `Dockerfile` — the starter's, producing `/bin/escrow` and `/bin/escrow-player`;
  `Dockerfile.replay-viewer` — the starter's pinned emsdk image, building
  `replay-viewer/escrow_replay.nim`.
- `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`, with
  `<slug>` = `escrow`, `<IMAGE>` = `coworld-escrow`, **`<SEATS>` = 4**.
- `tools/ci/docker_smoke.sh` (mode 100755, `<slug>`/`<IMAGE>`/`<SEATS>` substituted, `<SEATS>` = 4),
  `tools/ci/viewer_smoke.mjs` (copied verbatim, no substitutions), `tools/ci/policies.json`.

### `coworld_manifest_template.json`

- `game.name` = `escrow`; `runnable.image` = `{{ESCROW_IMAGE}}`, `run` = `["/bin/escrow"]`,
  `env.ANTHROPIC_API_KEY_URI` = `secret://coworld/escrow/anthropic_api_key`;
  `source_url` = `https://github.com/Metta-AI/cogame-escrow/tree/main` (repo **public** — a private
  repo 404s `source-resolves` and fails certification).
- `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
- `config_schema`: `tokens` (4/4), `players` (4/4), **`num_agents` integer, min 4, max 4**, `seed`,
  `turns` (4..40, default 16), `talk` (bool, default true), `episodeTimeoutSeconds`
  (60..6000, default 1200), `turnDelayMs` (0..10000, default 400), `model`
  (default `claude-sonnet-5`), `maxOutputTokens` (64..2000, default **1100**), `llmTimeoutSeconds`
  (5..300, default 60), `player_connect_timeout_seconds` (default 180).
- `results_schema`: exactly the `resultsJson` fields above; `scores` items are integers with
  `minimum: 0`; `reason` documented as `complete | deadline`.
- `game.docs.readme` — one paragraph: three goods, four cogs, comparative advantage, contracts the
  game executes, escrow pre-funded so breach is impossible, most hearts at horizon, "a policy is
  just a prompt", the two baselines.
- `game.docs.pages` — **two pages**: `rules.md` (profiles table, the nine-step resolution order,
  scoring and sign, end conditions, what is public) and `dsl.md` (the grammar, the validation
  table, the condition semantics, the three worked examples, and the loophole note that `HOLDS`
  reads free stock only).
- `game.protocols` — **both** `player` (the `escrow.player.v1` text above, including the frame
  shapes and `PLAYER_PROMPT` / `PLAYER_SCRIPTED`) and `global` (the `/global` snapshot shape and
  the `/client/*` pages, including that the static bundle renders hosted replays at
  `index.html?replay=<url>`).
- `player` runnables, all three on the **same image** `{{ESCROW_IMAGE}}` running
  `/bin/escrow-player`:
  | id | env |
  |---|---|
  | `escrow-player` | none (uses `PLAYER_PROMPT`; the LLM policy) |
  | `escrow-trader` | `PLAYER_SCRIPTED=trader` |
  | `escrow-hoarder` | `PLAYER_SCRIPTED=hoarder` |
- **`variants` — `num_agents: 4` in both:**
  | id | game_config |
  |---|---|
  | `standard` | `players` ×4, **`num_agents: 4`**, `turns: 16`, `talk: true`, `turnDelayMs: 400`, `player_connect_timeout_seconds: 180` |
  | `sprint` | `players` ×4, **`num_agents: 4`**, `turns: 8`, `talk: true`, `turnDelayMs: 200`, `player_connect_timeout_seconds: 180` |
- **`certification.game_config`**: `players` = four named entries, **`num_agents: 4`**, `seed: 11`,
  `turns: 6`, `turnDelayMs: 0`, `player_connect_timeout_seconds: 180`.
  `certification.players` = `[escrow-player, escrow-trader, escrow-player, escrow-hoarder]`.

### Design pins (`playbooks/make-coworld.md` §Phase 0) and where each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape — never green-field | `cogame-bullwhip` (turn-based, simultaneous, LLM-prompt policies); named in the title paragraph with the reason |
| Repo `Metta-AI/cogame-<slug>`, **public** | `Metta-AI/cogame-escrow`, public; `source_url` points at it (private ⇒ `source-resolves` 404 ⇒ certification fails) |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `escrow-player` (`PLAYER_PROMPT`) vs `escrow-trader` / `escrow-hoarder` (`PLAYER_SCRIPTED=…`), all `/bin/escrow-player` on `{{ESCROW_IMAGE}}` — `## Decisions` |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`, no `/client/replay` live-server viewer declared — `## Viewer` |
| Real art; the starter's chrome verbatim | four soldier sprites + `arena_floor.png` + `heart_red.png` (MIT, from coworld-ctf) + `font.ttf`; chrome half of `renderer.js`, `chrome.css` and the HTML pages kept — `## Viewer` |
| Legible to a casual spectator | numerals not notation, named feed lines, 360 px rules — `## Viewer` |
| Two name spaces | aliases in prompts/player frames; `policyNames` spectator-side; `results.names` = policy names — `## The game`, `## Server, player, protocol` |
| Degrade, never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6` ⇒ 720 s; `MaxTurnSeconds` = 125 s pre-turn check ⇒ `endEarly()` + `reason = "deadline"`; retry-once-then-scripted; the 16 × 20 s ≈ 330 s arithmetic — `## Decisions` |
| `num_agents` in every variant **and** the cert fixture | `standard`, `sprint`, and `certification.game_config` all carry `num_agents: 4`; `<SEATS>` = 4 in `docker_smoke.sh` cross-checks it |
| Prove it in CI: sim tests, scripted-bot test, e2e episode writing a replay, viewer smoke | `## Tests` |

## Tests

**`tests/test_sim.nim`** (pure rules; runs in both debug and `-d:release`):

1. Profile permutation and aliases are seed-determined and stable; the same seed yields an
   identical event log and identical results.
2. Production + commission arithmetic on a hand-computed two-turn fixture for all four profiles,
   including the `MaxFills = 2` cap and the "no partial fill" rule.
3. DSL parser table: every valid form (both bundle shapes, `NOTHING`, all four payouts, `ALWAYS`,
   `HOLDS`, `PAID`, `NOT`), and one case per rejection reason (`syntax`, `too_long`, `bad_target`,
   `bad_bundle`, `bad_due`, `bad_condition`, `bad_payout`, `unfunded`, `contract_cap`).
4. `renderContract(parseContract(x)) == renderContract(parseContract(renderContract(…)))` —
   normalization is idempotent.
5. Escrow mechanics: posting locks the proposer's bundle; signing locks the acceptor's; escrowed
   stock is invisible to `HOLDS`, cannot be given and cannot fill a commission; an unaffordable
   sign leaves the contract `offered` and moves nothing.
6. Settlement: all four payouts × both condition outcomes; `PAID` counts only transfers at or after
   `signedTurn` and only between the two parties; `NOT` inverts.
7. Expiry after exactly one turn refunds the proposer; the horizon closure refunds every live
   contract as `KEEP`; `score(seat)` then equals free hearts.
8. **Conservation invariants at the end of every turn:** total hearts across seats + escrow ==
   `4 × StartHearts + heartsMinted`; total goods across seats + escrow == produced − consumed by
   commissions. These catch any payout that mints or loses value.
9. `endEarly()` runs the horizon closure and sets `reason == "deadline"`; results are well-formed
   after it.
10. Replay re-derivation: `replayMatch` gives `frames.len == events.len + 1`, the final frame equals
    the live `tableStateJson`, and each recorded `turn` event matches the seeded re-derivation.
11. Event JSON round-trip (`eventToJson`/`eventFromJson`) for every event kind.
12. **Strict-UTF-8 replay parse:** an episode whose `say`, `notes` and `offer` carry multi-byte
    runes and an emoji at the truncation boundary produces replay bytes for which
    `validateUtf8(bytes) == -1` and `parseJson(bytes)` succeeds, and the round-tripped strings are
    still valid UTF-8 (proof that truncation is on rune boundaries).

**`tests/test_bot.nim`** (the completion path and the bounded-orders/legality assertion):

13. Four `trader` seats, and the mixes `3×trader + 1×hoarder` and `2×trader + 2×hoarder`, play full
    episodes for seeds `[1, 7, 42, 1234]` with **every scripted action legal**: `applyMove` never
    raises, no `reject`/`ok:false` event is ever attributed to a scripted seat, every DSL string the
    bot emits parses, no seat exceeds `MaxLive` live contracts, every offer's `DUE` is inside the
    window, every `n` is within `1..MaxUnits`, gives ≤ 2 and signs ≤ 2 per seat per turn, and the
    bots emit no `say`/`notes`. The whole set runs in well under 2 s (the starter's timing check).
14. Trading beats autarky: on the same seeds, the all-`trader` episode's `heartsMinted` is at least
    1.3× the all-`hoarder` episode's — the baseline is a partner worth beating, and the number is a
    canary for a broken price band.
15. `decideAll` with no credentials falls back to the scripted decision for every seat, immediately
    and with no network wait, and the episode completes with `reason == "complete"`.
16. Reply parsing table: valid replies; missing fields (`{}` = pass); over-cap `say`/`notes`/`offer`
    truncated on rune boundaries; a third `give`/`sign` dropped; non-numeric `n` rejected; prose
    replies rejected by `extractJsonObject`.

**CI (`.github/workflows/ci.yml`, the only harness — the sandbox has no docker/nim/emsdk/browser):**

17. `test` job — every `tests/*.nim` in debug **and** `-d:release`.
18. `docker-smoke` job — builds the production image and runs **one real end-to-end episode** in raw
    docker via `tools/ci/docker_smoke.sh` with the certification fixture's seat mix (4 seats,
    cross-checked against `certification.game_config.num_agents` = 4), no `ANTHROPIC_API_KEY` (so
    the scripted path is exercised), asserting the game exits 0 having written `results.json` and a
    replay; `SMOKE_REQUIRE_REPLAY_JSON=1` so the replay must parse as JSON. The replay is uploaded
    as the `smoke-replay` artifact.
19. `wasm-viewer` job — `needs: docker-smoke`. Asserts `tools/build_replay_viewer.sh` is present and
    **executable**, builds the bundle, asserts `index.html` + a non-empty `.wasm`, then **executes**
    it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
    dist/smoke/<replay> --timeout 90` opens the bundle in headless Chromium (Playwright pinned
    1.55.0 in both places) against the replay `docker-smoke` just produced and fails unless
    `data-replay-loaded="true"` (or the `ready` bridge message) arrives. Building is not enough;
    the lantern deadlock passed every file-presence check.

## Out of scope (v1)

- More than four seats (the idea's 4–6 upper end), variable seat counts, and any variant with
  hidden inventories or hidden commissions.
- Multi-clause contracts, nested conditions, more than one `IF`, contracts with more than two
  parties, assignment/resale of a contract, renegotiation or mutual cancellation.
- Conditions beyond `ALWAYS` / `HOLDS` / `PAID` (no price oracles, no time-series conditions, no
  conditions on another contract's outcome).
- Partial or streaming performance (deliver 1 ore a turn), interest, loans that are not just a
  `HEARTS`-for-`HEARTS` contract, and any currency other than hearts.
- An order book, an auction house, or any market-clearing mechanism the game runs on the seats'
  behalf — all price discovery happens in contracts and public talk.
- Private messaging (all `say` is public), cross-episode memory or reputation, and league-level
  contract history.
- Goods having any terminal value at the horizon.
