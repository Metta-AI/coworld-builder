# Garble — design note (2026-08-24)

Garble is forked from **`Metta-AI/cogame-babel`** (read at `/workspace/starters/cogame-babel`), the
parley-lineage template for turn-based talk games: five seats, one decision each per turn, a policy
that is *just a prompt*, a pure native `sim` module shared by the server / the tests / the wasm
viewer, and a static replay bundle. Garble is that shape exactly — a turn-based negotiation game
whose whole content is text crossing between seats and being scored by native rules — so babel is
the closest starter by game shape and no other starter is a candidate. **Every convention there
holds here unless this note says otherwise.** The repo is **public** at `Metta-AI/cogame-garble`.
`num_agents` is **5**, everywhere, always.

One code-level exception is named up front so it is not mistaken for drift: babel's `decide` asks
one seat at a time (babel is sequential by construction — two speakers, then two listeners). Garble
is a **simultaneous-decision** game, so `src/garble/llm.nim`'s batching half (`requestFor`,
`textOf`, `decideAll` built on `curly.makeRequests`) is ported from
**`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim`**, which is babel's own descendant and
whose transport code is otherwise line-identical to babel's. This is a *server-side* port only.
**None of the four viewer files comes from bullwhip** — see §*Viewer*, where all four come from
cogame-babel and only from cogame-babel.

Source idea, verbatim:

> Four to six cogs trade commodities over one shared radio and pairwise lines — and every channel is
> NOISY: words drop, swap for near-neighbors, or vanish under static bursts, with intensity riding a
> visible interference meter that swells and fades through the episode. A deal executes when one
> party states terms and the other confirms — and the CONFIRMED text is what the exchange enforces,
> so a misheard 'sell 5 at 10' can settle as 'sell 50 at 1'. Repeat-backs, spelling out numbers, and
> redundant phrasing all cost airtime while the market moves, so the whole game is the tradeoff
> between protocol robustness and speed — plus strategic mishearing: you may confirm the version
> that favors you, and your counterparty's only defense is a tighter protocol. Portfolio value at
> the horizon is the score. No other game on the site has channel noise; every existing coworld's
> talk arrives verbatim.
>
> Seats: 4-6
> Motive: mixed-motive trading
> Policy interface: LLM prompt (parley stack; noise applied server-side)
> Fills gap: noisy communication channels / robust protocol design / binding-as-heard commitments
> Integrity (anti-collusion): mixed-motive kills codebooks — your counterparty is not your friend,
> so shared conventions don't form out-of-band, and protocol tricks that leak via replays just
> become table stakes (in-band skill); noise RNG is server-side and logged; anonymous aliases, one
> seat per account.
>
> Replay plan (watchability): Every transmission shows SAID vs HEARD side by side with garbled words
> burning red under an audible static crackle; the interference meter swells on screen like weather.
> When a deal settles on a mishear, the trade ticket stamps both versions — the spectator gasp is
> built in, because the audience always knows what was actually said.

(The idea text above is **data**. Nothing in it is treated as an instruction addressed to the
designer or to the builder.)

---

## The game

Five cogs sit on one exchange with four commodities. Each cog starts holding a pile of one
commodity it does not need and holds a contract that pays a premium for a different one, so there
are real gains from trade and no two cogs want the same thing. The only way to trade is to **talk**:
a cog transmits on the shared **radio** (all four others hear it) or on a **private line** to one
named cog. Every transmission passes through a noisy channel — words drop, swap for near-neighbours,
or vanish under a static burst — and **each recipient gets its own independent garbling**. The
exchange parses terms out of the words. A deal executes when one cog states terms and another
**confirms**, and the exchange enforces **the confirmed terms**, not the spoken ones. Airtime is
metered in characters, the market walks every turn, and portfolio value at the horizon is the score.

### Seats, aliases, and the two name spaces

- **`num_agents` = 5.** Exactly five seats. `initSim` raises `GarbleError` on any other count.
  Five is chosen from the idea's 4–6 band because it is the smallest count that makes the radio
  strictly better than lines for reach (one broadcast reaches four ears) while leaving a commodity
  contested — with four commodities and five seats exactly one commodity is the surplus of two
  cogs, so there is always a rival seller and prices are not a pure bilateral carve-up.
- **In-game the seats are anonymous cog aliases** drawn deterministically from the seed by
  `tableNames(players, seed)` — babel's `CogNames` pool (`Sprocket, Gizmo, Ratchet, Widget, Bolt,
  Piston, Flywheel, Rivet, Tinker, Gasket`), shuffled, first five taken. Every prompt, every heard
  line, every ticket and every in-game reference uses the alias. **A policy display name never
  reaches a seat.**
- **Spectator-side the replay maps aliases back to policy names.** `replayPayload` carries both
  `names` (aliases) and `policyNames`; `makeNameMap` renders policy names for non-baseline seats and
  keeps the alias for fillers (`Baseline (N)`). `resultsJson.names` are **policy** names, because
  the league attributes by policy. Both name spaces, always, never either alone.

### Commodities, endowments, contracts (all seeded, all re-derivable)

- Four commodities, in this fixed index order: **`ORE` (0), `OAT` (1), `TIN` (2), `TAR` (3)**. The
  names are chosen so that a channel swap produces a *valid but wrong* commodity: `ORE`↔`OAT` and
  `TIN`↔`TAR` are the only confusable pairs (§*The wire*).
- **Prices.** `price[t][c]` for turn `t`, commodity `c`, is drawn in full at `initSim` so a replay
  re-derives it: `price[0][c] = 8 + rng.rand(6)` (8…14), then
  `price[t][c] = clamp(price[t-1][c] + (rng.rand(2) - 1), 3, 30)` (a −1/0/+1 walk). Prices are
  **public** to every seat and to spectators, current and previous turn.
- **Endowment.** A seeded shuffle `deal = rng.shuffle(@[0,1,2,3])` gives seat `s` its
  **surplus** `sur[s] = deal[s mod 4]`; its **demand** is `dem[s] = deal[(s + 1 + rng.rand(2)) mod 4]`
  redrawn until `dem[s] != sur[s]`. Seat `s` starts with `units[s][sur[s]] = 20`, `0` of everything
  else, and `cash[s] = 120` credits.
- **Contract.** Seat `s` is paid `premium[s] = 6 + rng.rand(3)` (6…9) credits for each unit of
  `dem[s]` it holds at the horizon, up to `quota[s] = 12 + rng.rand(7)` (12…19) units. Beyond the
  quota the units are worth only the market price. **A seat's own contract is private**; nobody else
  learns its demand commodity, its premium or its quota except by inference from what it says.
- Every draw above comes from the **seed**, through two seeded streams and nothing else: the
  aliases from `tableNames`' own stream (`initRand(seed * 6779 + 31)`, the starter's shape, because
  the aliases are drawn before a `Sim` exists), and everything else from one stream at `initSim`
  (`initRand(seed * 7919 + 17)`) in this order: prices, surplus/demand deal, premiums, quotas,
  interference phase, burst table. `seed` alone reproduces all of it.

### The wire — the exact scanner, lexicon and noise model

A **transmission** is one line of text. The exchange normalises it before anything else:
uppercase (`toUpperAscii` on ASCII; non-ASCII runes are left alone and are simply unrecognised
words), every character outside `[A-Z0-9]` replaced by a space, split on whitespace → `words[]`,
truncated to **32 words**.

**Lexicon.** Four word classes, everything else is chatter:

| class | members |
|---|---|
| verb | `SELL`, `BUY` |
| pivot | `AT` |
| commodity | `ORE`, `OAT`, `TIN`, `TAR` |
| number | any digit string of 1–2 digits (`0`…`99`), or one of `ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE THIRTEEN FOURTEEN FIFTEEN SIXTEEN SEVENTEEN EIGHTEEN NINETEEN TWENTY THIRTY FORTY FIFTY SIXTY SEVENTY EIGHTY NINETY` |

`wordValue(w)` maps a number word to `0..99`. There are **no compound spellings**: `TWENTY FIVE`
is two number words worth 20 and 5, not 25. Round numbers can be spoken; odd ones must be digits —
which is a real strategic wrinkle, because digits garble more widely than words.

**`scanTerms(words) -> Option[Terms]`**, run identically on the said text and on every heard text:

1. `v` = the smallest index with `words[v] ∈ {SELL, BUY}`. None ⇒ **no terms** (the transmission is
   chatter).
2. `a` = the smallest index `> v` with `words[a] == "AT"`. None ⇒ **no terms**.
3. `side` = `SELL` or `BUY` from `words[v]`, **stated from the transmitter's point of view**.
4. **qty** = the *modal* value among the number words in `words[v+1 .. a-1]`; ties in multiplicity
   break toward the **last** such word. No number word in that region ⇒ **no terms**.
   `kQty` = the multiplicity of that modal value.
5. **commodity** = the *modal* commodity word in `words[v+1 .. a-1]`; ties break toward the **last**.
   None ⇒ **no terms**. `kCom` = its multiplicity.
6. **price** = the *modal* value among the number words in `words[a+1 .. ]`; ties break toward the
   **first**. None ⇒ **no terms**. `kPrice` = its multiplicity.
7. `qty` and `price` are clamped to `0..99` by construction. `qty == 0` ⇒ **no terms**.

The modal rule is the whole robustness mechanic: `SELL 5 5 5 ORE ORE AT 12 12 12` survives one
garble per field by majority vote, and it costs 26 characters of airtime against the 20 of
`SELL 5 ORE AT 12`.

**Interference.** `interference[t] ∈ [0.05, 0.95]`, one value per turn, public:

```
P    = max(6, turns div 2)                  # swell period, in turns
phi  = rng.rand(P - 1)                      # drawn at initSim
base = 0.15 + 0.60 * (0.5 - 0.5*cos(2*PI*(t + phi)/P))
burst[t] = (rng.rand(1.0) < 0.12)           # drawn for every t at initSim
curve[t] = clamp(base * config.noiseScale, 0.05, 0.95)   # PUBLISHED, burst-free
raw  = (base + (if burst[t]: 0.35 else: 0.0)) * config.noiseScale
interference[t] = clamp(raw, 0.05, 0.95)    # rounded to 3 decimals
```

The **base curve for every turn of the episode is published** to all seats and to spectators from
turn 0 — a policy can plan to talk in the quiet. It carries `noiseScale`, exactly as
`interference[t]` does, so the forecast a seat reads is on the same scale as the meter it will
play into; the two differ only by the burst. The **bursts are not** published: they are the
surprise. The
meter therefore swells and fades on screen exactly as the idea asks, and it is derivable from
`seed` + `turns` + `noiseScale` alone.

**Delivery.** A transmission from `from` reaches recipients `to`: on `radio`, every other seat; on a
private line, only the addressed seat. Effective noise is `n = interference[t] * chanFactor`, with
`chanFactor = 1.0` on the radio and **`0.6` on a private line** — a directed line is cleaner but
reaches one ear, so reach-versus-fidelity is a live choice every turn.

Per delivery the RNG is `deliveryRng(seed, t, from, to) = initRand(int64(seed)*1_000_003 + t*997 +
from*31 + to*7 + 1)`; nothing about it depends on earlier transmissions, so a replay re-derives it
from the said text alone. For each word index `i`, draw `r = rng.rand(1.0)`:

1. `r < 0.45*n` → **DROP**: the word vanishes (flag `drop`).
2. `r < 0.85*n` → **SWAP**: the word is replaced by a uniform draw from `neighborsOf(word)`; if that
   set is empty the word **drops** instead (flag `swap`, carrying the substituted word).
3. otherwise → clean (flag `ok`).

Then, if `burst[t]`, a **static burst** blanks a contiguous run at positions
`s = int(burstFrac[t] * n_words)` … `s + burstLen[t] - 1` (clamped to the transmission), where
`burstFrac[t] ∈ [0,1)` and `burstLen[t] ∈ {2,3,4}` are drawn at `initSim` and are **shared by every
delivery in that turn** — the burst is weather, not per-listener luck. Blanked words carry flag
`static`.

**`neighborsOf(word)`** — fixed, published in the system prompt, and the *only* source of
admissible mishearings:

| word | neighbours |
|---|---|
| digit string `d`, value `x` | `d & "0"` when `x*10 ≤ 99`; `d[0..^2]` when `len(d) ≥ 2`; the two strings equal to `d` with its **last** digit replaced by `(last±1) mod 10`, when the result is `≤ 99` |
| spelled number | a fixed symmetric table, and it is a **matching** — every spelled word appears in at most one pair, so a spelled number has **at most one** neighbour: `FIVE↔NINE`, `FIFTY↔FIFTEEN`, `SIXTY↔SIXTEEN`, `SEVENTY↔SEVENTEEN`, `EIGHTY↔EIGHTEEN`, `NINETY↔NINETEEN`, `FORTY↔FOURTEEN`, `THIRTY↔THIRTEEN`, `TWENTY↔TWELVE`, `TEN↔TWO`, `THREE↔SIX`. The six spelled words in no pair — `ZERO`, `ONE`, `FOUR`, `SEVEN`, `EIGHT`, `ELEVEN` — have **no** neighbour at all and can only drop, never swap |
| commodity | `ORE↔OAT`, `TIN↔TAR` (one neighbour each) |
| verb `SELL` / `BUY`, pivot `AT` | **no neighbours** — they can drop, never swap |
| chatter (anything else) | no neighbours — swap degenerates to drop |

So `5` → `{50, 4, 6}` (three ways to be misheard) but `FIVE` → `{NINE}` (one). **Spelling a number
out narrows its mishearing surface at the cost of four extra characters of airtime** — that is the
idea's "spelling out numbers" defence, priced. Structure words (`SELL`, `BUY`, `AT`) never swap, so
a structural garble *voids* a reading rather than inverting it: you can lose a deal to noise, you
cannot be flipped from seller to buyer.

### Tickets — the exchange's clean channel

The **words** are noisy; the **exchange** is not. When a seat's *said* text parses to terms, the
exchange opens a **ticket**: a sequential integer id from 1, tagged with the offerer's alias, the
channel, the turn it opened, and the turn it expires. The ticket id, the offerer and the channel are
delivered **reliably** to every eligible recipient. Only the **terms** are what you heard.

- A ticket opened on turn `t` may be confirmed on turns `t+1` and `t+2` (`TicketLife = 2`). It
  cannot be confirmed on turn `t` — decisions are simultaneous. It expires at the open of turn
  `t+3`.
- A **radio** ticket may be confirmed by any seat except the offerer. A **line** ticket may be
  confirmed only by the addressed seat.
- If two seats confirm the same ticket in the same turn, they resolve in **seat index order**; the
  first admissible confirm settles the ticket and every later confirm that turn voids as
  `already-settled`.
- If the said text does **not** parse, no ticket exists — even if some listener's garbled version
  happens to parse. Listeners always know the real ticket ids, so this never bites an honest seat.

### Confirming — binding as heard, with the redundancy shield

A confirm names a ticket and asserts four fields: `side`, `qty`, `commodity`, `price`. **Those
asserted fields are what the exchange enforces** — not what the offerer said. That is the idea's
"the CONFIRMED text is what the exchange enforces", and it is where `sell 5 at 10` settles as
`sell 50 at 1`.

The offerer's only defence is a tighter protocol, and it is exact:

> For each of `qty`, `commodity`, `price`: the asserted value is admissible if it **equals** the
> said value. Otherwise it is admissible **only if** the said field was transmitted **once**
> (`k == 1`) **and** the asserted value is the value of a member of `neighborsOf(<the single said
> word>)`. If the offerer said the field **twice or more** with the same value (`k ≥ 2`), only the
> exact said value is admissible.

So **one repeat kills strategic mishearing on that field**, and it costs airtime. A cog that repeats
everything is unrobbable and runs out of meter; a cog that is terse is fast and steal-able. That is
the whole game, and it is a single rule.

The shield also converts *honest* mishearings into **voids** rather than bad settlements: if the
offerer repeated and the listener genuinely misheard the majority, the confirm voids and a turn is
burned — which is exactly what protocol robustness buys you in the real world.

`side` is never a near-neighbour of anything, so an asserted `side` must equal the said `side`.

### Turns and the exact resolution order

`turns` turns, `t = 0 … turns-1`. Every step is numbered and the order is load-bearing:

0. **Deadline check.** Before opening turn `t`, if `epochTime() > playDeadline` (§*Decisions* →
   *Episode budget*), call `endEarly()`: append the `end` event with `reason = "deadline"`, score on
   turns `0 .. t-1`, and stop. Nothing below runs.
1. **Open.** Expire every ticket whose expiry turn is `≤ t`. Set the live prices to `price[t]` and
   the live interference to `interference[t]`. Append a **`turn`** event carrying `t`,
   `interference[t]`, `burst[t]`, `price[t][0..3]`, and each seat's portfolio value marked at
   `price[t]`.
2. **Observe.** Build one observation per seat from the state at open (§*Server, player, protocol*
   → *Observation*). Every seat's observation is different: private inventory, private contract,
   and its **own** heard traffic only.
3. **Decide.** All non-scripted seats' LLM calls go out as **ONE parallel batch**
   (`curly.makeRequests`), one request per seat, timeout `llmTimeoutSeconds` (default **25 s**).
   Scripted seats decide locally with no network call. Batch **starts** are floored at
   `max(minTurnSpacingMs, callsIssuedLastTurn * 2400 ms)` apart (§*Episode budget*).
4. **Validate → retry → fall back.** A reply that times out, fails to parse, or is **ill-formed**
   (not: inadmissible — see below) is retried **once** in a smaller batch carrying an explicit hint;
   a seat still open after that plays the **`quoter`** scripted move, which is legal by
   construction. *Ill-formed* means the JSON is unreadable or a confirm's fields are missing or out
   of range. An **inadmissible** confirm is a perfectly legal move whose outcome is a `void`; it is
   never retried and never falls back.
5. **Transmit, in seat order 0, 1, 2, 3, 4.** For seat `s` with reply `{channel, text, confirm,
   notes}`:
   1. Normalise `channel`: `"radio"`, or the alias of another seat (case-insensitive, whitespace
      stripped). Anything else — including this seat's own alias — normalises to `"radio"`; this is
      a lenient normalisation, not an error.
   2. Rune-truncate `text` to **160 runes**, replace newlines with spaces, then drop words past the
      32nd.
   3. Charge airtime: `cost = runeLen(text)`. If `cost > airtime[s]`, cut `text` to `airtime[s]`
      runes **on a rune boundary** and flag the `say` event `clipped`. If `airtime[s] == 0`, the
      transmission is dropped entirely and the event is flagged `silent`. `airtime[s] -= cost`,
      floored at 0.
   4. `notes[s] := notes` when non-empty, rune-truncated to 400 runes. Notes are private in-game
      and **recorded in the event log for spectators**, as babel does.
   5. Append a **`say`** event: `turn`, `seat`, `channel`, `text` (the final said text), `cost`,
      `airtimeLeft`, `silent`, `clipped`, the scanned said `terms` with `kQty`/`kCom`/`kPrice`, the
      `ticket` id opened (or `-1`), `scripted`, and `notes`.
   6. If the said text parses, open the ticket.
6. **Confirms, in seat order 0, 1, 2, 3, 4**, after every transmission of the turn has landed — so
   simultaneity is fair and same-turn races break by seat index. For seat `s` with a `confirm`:
   1. Charge `ConfirmAirtime = 40` runes: `airtime[s] = max(0, airtime[s] - 40)`. **A confirm is
      never blocked by an empty meter** — a seat can always settle; only its *text* gets clipped.
   2. Append a **`confirm`** event: `turn`, `seat`, `ticket`, asserted `side`/`qty`/`commodity`/
      `price`, `scripted`.
   3. Resolve, in this order, appending exactly one **`deal`** or one **`void`** event immediately
      after the `confirm`:
      1. ticket unknown, expired, already settled, offered by this seat, or (line ticket) not
         addressed to this seat → `void`, reason `no-ticket` / `expired` / `already-settled` /
         `own-ticket` / `not-addressed`;
      2. asserted `side ≠ said side` → `void`, reason `side`;
      3. any of `qty` / `commodity` / `price` inadmissible under the redundancy shield → `void`,
         reason `inadmissible`;
      4. **coverage**: with `side = SELL` the offerer is the seller and the confirmer the buyer
         (`BUY` swaps them). `fill = min(qty, seller.units[commodity], (if price > 0:
         buyer.cash div price else: qty))`. `fill == 0` → `void`, reason `uncovered`;
      5. **settle**: `seller.units[commodity] -= fill`; `buyer.units[commodity] += fill`;
         `buyer.cash -= fill*price`; `seller.cash += fill*price`. Close the ticket. Append a `deal`
         event carrying the ticket, both parties, `commodity`, `qty` asked, `fill`, `price`, the
         **said terms** and the **confirmed terms** side by side, `partial = fill < qty`, and
         `misheard = (confirmed terms != said terms)`.
   4. Every settled deal is **published on the public tape**: both versions, to every seat and to
      spectators. A robbed offerer learns it was robbed the same turn — that is the in-episode
      feedback that makes a reputation possible across twelve turns.
7. **Pace.** Sleep `turnDelayMs` (default 400 ms) so a spectator can read the turn that just landed.
8. **Continue or settle.** If `t + 1 == turns`, append the `end` event with `reason = "complete"`.
   Otherwise `t += 1`, go to 0.

### Scoring — the formula and its sign

At the horizon, with `F[c] = price[turnsPlayed - 1][c]` (the last opened turn's prices; on a
`deadline` ending, the last turn actually opened):

```
portfolio[s] = cash[s]
             + sum over c of units[s][c] * F[c]
             + premium[s] * min(units[s][dem[s]], quota[s])

hold[s]      = the SAME formula applied to the seat's STARTING cash and inventory at the SAME F[c]
               (i.e. what the seat would be worth had it never traded)

score[s]     = portfolio[s] / hold[s]                       # float, 1.0 = traded to no effect
```

**Higher is better** — the sign is positive, a bigger number is a better episode. `hold[s] ≥ 180`
always (120 cash + 20 units at a floor price of 3), so the division is total. `portfolio[s]` can
never be negative (cash and units never go negative — the coverage rule guarantees it), so
`score[s] ≥ 0`; the results schema bounds it `0 … 10`.

**The league ranks by mean episode `score`** — the ratio, not the raw credits, so episodes with
different seeded price levels are comparable. `resultsJson` also reports the raw `portfolio` for
readability.

Mixed-motive, exactly as the idea asks: a good trade lifts both sides' `score` above 1.0, a
mishearing lifts one and sinks the other, and nobody's score is anybody's mirror image — there is no
zero-sum to collude around.

### End conditions and `results.reason`

`results.reason` has **exactly two legal values**:

| value | when |
|---|---|
| `complete` | all `turns` turns were played |
| `deadline` | step 0's clock check fired; scores use `turnsPlayed` turns and the last opened turn's prices |

There is no third value, no forfeit, no early win. `sim.reason` is `""` until the episode settles;
`resultsJson.reason` is one of the two. A seat that never connects a player socket is *not* an
ending: after `player_connect_timeout_seconds` (180) the episode starts anyway and unprompted seats
play with an empty operator block.

### Integrity — how the idea's anti-collusion pins land

- **Mixed motive kills codebooks.** Your counterparty gains when you lose on a mishear, so an
  out-of-band shared convention is a gift to whoever defects from it first. There is nothing to
  collude *on*.
- **Server-side, logged noise.** All garbling happens in the game container. The RNG is seeded from
  `seed` and re-derived by the same `src/garble/wire.nim` in the wasm viewer, so anyone can audit
  every garble in the replay bytes. No seat can fake a mishear it did not get; and the admissibility
  rule makes the *set* of fakeable mishearings public and small.
- **Anonymous aliases, reshuffled per episode from the seed.** One seat per account is a platform
  property; the aliases make cross-episode identity useless inside a game.
- **Protocol tricks that leak via replays are table stakes**, not exploits: the scanner and the
  neighbour table are published in the system prompt and in `docs/pages/rules.md`, so any advantage
  is in-band skill.

---

## Decisions: LLM with scripted fallback

Credentials resolution (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the
"no credentials ⇒ every seat scripted, immediately, with no network wait" rule, the Bedrock model
candidate list with haiku first, `extractJsonObject`, `cleanText` rune truncation, and the
JSON-only output contract are ported from `src/babel/llm.nim` unchanged. The batching half
(`requestFor`, `textOf`, `decideAll` over `curly.makeRequests`) is ported from
`cogame-bullwhip/src/bullwhip/llm.nim` as stated at the top of this note.

### One parallel batch per turn

Garble is a simultaneous-decision game: **all five seats' LLM calls go out as ONE parallel batch per
turn** (`curly.makeRequests` on a `RequestBatch`), never sequentially. Sequential seats are exactly
how an LLM coworld blows the 720 s play budget. Scripted seats never enter the batch.

### Episode budget — the arithmetic, out loud

- `PlayBudgetFraction = 0.6`. The game container does **not** receive `COWORLD_TIMEOUT_SECONDS`
  (only the worker sidecar does), so when the env is silent the game assumes
  `config.episodeTimeoutSeconds` (default **1200 s**) and sets
  `playDeadline = gameStart + 1200 * 0.6 = gameStart + 720 s`.
- `turns` default **12**. Per turn: one batch of ≤ 5 calls at `llmTimeoutSeconds = 25 s`, at most
  one retry batch at the same timeout, plus `turnDelayMs = 400 ms` of pacing.
  **Worst case per turn = 25 + 25 + 0.4 ≈ 50.4 s; 12 × 50.4 ≈ 605 s < 720 s.**
  **Typical: batch p50 ≈ 7–9 s, and the spacing floor dominates at 12 s → 12 × 12 ≈ 144 s.**
- **Rate limiting.** The hosted Bedrock sidecar caps **30 requests/minute per episode**. Five calls
  per batch means batch starts must be ≥ 10 s apart; a turn that also retries issues 10. So the next
  batch start is floored at `max(minTurnSpacingMs, callsIssuedLastTurn * 2400 ms)` —
  `minTurnSpacingMs` defaults to **12 000 ms** (5 calls → 25 rpm; 10 calls → 24 000 ms → 25 rpm).
  Certification sets it to 0 because certification runs with no credentials.
- The batch timeout is additionally clamped to the remaining budget:
  `effective = min(llmTimeoutSeconds, max(5, int(playDeadline - epochTime())))`.
- `EpisodeCallBudget = 120` calls, `CallsPerTurn = 5`, so `sampleEpisode` caps `turns` at
  `120 div 5 = 24` = `MaxTurns`, floors at `MinTurns = 6`, and caps `turnDelayMs` at
  `PacingBudgetMs (60 000) div turns`. `sampleEpisode` is idempotent: a replay's config carries
  `sampled: true` and is never re-fitted.

### Degrade, never hang

- **Timeout / transport error / unparseable JSON / ill-formed reply** → the seat stays in `open`,
  gets **one** retry inside the next batch with an appended hint, and if it is still open plays the
  **`quoter`** baseline. Every fallback prints `garble llm: seat N falling back to scripted
  decision` so the hosted log is greppable.
- **Auth failure (401/403)** disables the client for the rest of the episode; every later turn is
  scripted with no network wait. **429** rotates the Bedrock model candidate for the next batch.
- **No credentials at all** ⇒ `client.disabled` at construction ⇒ every seat scripted from turn 0.
  This is what makes offline certification and `docker-smoke` complete.
- **Past the deadline** ⇒ the episode settles between turns with `reason = "deadline"`, having
  already written every event it played. The platform discards an episode that overruns and keeps
  nothing at all, so a short honest episode always beats a long one that never lands.
- Every wait in the game is bounded: the player-connect wait (180 s), the LLM batch (25 s), the
  artifact writes (60 s inside `writeArtifact`), and the pacing sleeps.
- The **player** binary wraps its receive loop in `try/except CatchableError` and exits **0** on a
  dead socket — whisky's `receiveMessage` *raises* on a close frame, and the game's `quit(0)` can
  outrun the flushed `final` frame (raid 0.1.3 → 0.1.4; the bug is latent in
  `cogame-bullwhip/src/bullwhip_player.nim` and in babel's player, and is fixed here).

### Prompts

**System prompt** (identical for every seat except the alias), delivered as `system`:

> You are `<alias>`, a cog trading commodities with four other cogs over a NOISY exchange.
>
> Rules:
> - Four commodities: ORE, OAT, TIN, TAR. Prices are public and move every turn.
> - You hold a surplus of one commodity and a private contract that pays you a premium for each unit
>   of a DIFFERENT commodity you hold at the end, up to your quota. Your score is your final
>   portfolio value divided by what you would have been worth if you never traded. Above 1.00 means
>   you traded well. Nobody else's score is the mirror of yours: good trades lift both sides.
> - Each turn you transmit ONE line, on the RADIO (all four others hear it) or on a PRIVATE LINE to
>   one named cog (cleaner channel, one listener).
> - EVERY channel is noisy. Words drop, swap for near-neighbours, or vanish under static bursts. The
>   interference meter is public and is printed every turn. Each listener hears its OWN garbling —
>   what you said is not what anyone heard.
> - The exchange reads terms out of your words: it finds SELL or BUY, then AT, then takes the most
>   frequently repeated number before AT as the quantity, the most frequently repeated commodity
>   before AT as the commodity, and the most frequently repeated number after AT as the price.
>   `SELL 5 ORE AT 12` is a valid offer. So is `SELL 5 5 ORE ORE AT 12 12`, which survives one
>   garble per field.
> - A deal executes when you CONFIRM someone's ticket. **The terms you confirm are what the exchange
>   enforces, not the terms they spoke.** You may confirm a value you did not hear — but the
>   exchange only accepts a value that the channel could have produced: it must equal what they
>   said, or be a near-neighbour of it AND they must have said that field exactly once. If they
>   repeated a field, only the exact value binds and anything else voids your confirm and wastes
>   your turn.
> - Near-neighbours are fixed and public. A digit string's neighbours are: append a 0 (5 → 50), drop
>   the last digit (50 → 5), and change the last digit by one (5 → 4, 5 → 6). Spelled numbers have
>   at most one neighbour (FIVE ↔ NINE, FIFTY ↔ FIFTEEN, …). ORE ↔ OAT and TIN ↔ TAR. SELL, BUY and
>   AT never swap — they only vanish.
> - AIRTIME is metered in characters. You have a fixed budget for the whole episode; a transmission
>   costs its length, a confirm costs a flat 40. Run out and your transmissions stop going out,
>   though you can always still confirm. Repeat-backs, spelled numbers and redundant phrasing all
>   cost airtime while the market moves.
> - Every settled deal is public and stamps BOTH the spoken terms and the confirmed terms. Everyone
>   sees who was robbed.
>
> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character `{`
> and end with `}`.

**User prompt** (the observation, rebuilt every turn, in this fixed block order):

```
Turn 4 of 12.

INTERFERENCE NOW: 62% (ROUGH).  FORECAST (base, bursts not shown):
  t0 18%  t1 34%  t2 57%  t3 71%  t4 62% ← now  t5 41% …
PRICES: ORE 12 (was 11)  OAT 9 (was 10)  TIN 11 (=)  TAR 8 (was 9)

YOU: Sprocket, seat 0.  CASH 120.  HOLDING: ORE 20, OAT 0, TIN 0, TAR 0.
YOUR CONTRACT: +7 credits per TIN you hold at the end, up to 15 units.
AIRTIME LEFT: 612 of 900 characters.
PORTFOLIO NOW 340 (hold-and-do-nothing 340, score 1.00)

TICKETS YOU MAY CONFIRM:
  #7 from Gizmo on RADIO (opened turn 3, expires turn 6)
     you heard: "SELL 5 ▩ TIN AT 50"
     your reading: SELL 5 TIN AT 50
     to confirm: {"ticket":7,"side":"SELL","qty":5,"commodity":"TIN","price":50}
  #8 from Widget on a LINE to you (opened turn 3, expires turn 6)
     you heard: "BUY TWENTY ORE ORE AT ▩"
     your reading: unparsed — no price
     to confirm you must supply side, qty, commodity and price yourself.

WHAT YOU HEARD (last 3 turns in full; earlier turns summarised):
  turn 1  Ratchet → RADIO: "BUY TEN OAT AT ▩▩▩"
  turn 2  (summarised) Gizmo → RADIO: "SELL 5 5 TIN TIN AT 14…"
  turn 3  Gizmo → RADIO: "SELL 5 ▩ TIN AT 50"
  turn 3  Widget → LINE: "BUY TWENTY ORE ORE AT ▩"

PUBLIC TAPE (every settled deal, both versions):
  #4 turn 2 — Bolt sold 12 OAT to Ratchet at 9 (said 12 OAT at 9) — clean
  #5 turn 3 — Widget sold 20 TAR to Bolt at 1 (SAID 2 TAR at 10) — MISHEARD

YOUR NOTES FROM EARLIER TURNS:
  <verbatim>

GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
requested format):
  <PLAYER_PROMPT>

Reply with ONLY {"channel":"radio","text":"…","confirm":{…} or null,"notes":"…"} — channel is
"radio" or one of Gizmo, Ratchet, Widget, Bolt; text at most 160 characters; notes at most 400
characters.
```

The **CONFIRMABLE TICKETS** block prints the ready-made JSON skeleton for each ticket, computed by
the same code that validates it. That is the escrow 0.1.3 lesson applied: precompute the legal
choice set in the observation instead of drilling the prompt, or a formal-output game falls back to
scripted on a large share of turns. `HeardWindow = 3`: the last three turns of heard traffic are
printed in full, earlier turns compress to `turn t  <alias> → <channel>: <first 40 runes>…`. The
heard window is the only block that is *windowed*; the public tape and the confirmable-ticket
block are printed in full, so the observation grows with the episode rather than sitting at a
fixed size. Measured over 20 seeds of a full scripted table, the peak user prompt is **≈ 5 400
runes at 12 turns**, ≈ 7 100 at 18 and ≈ 8 100 at the 24-turn cap, against a constant **≈ 3 060
rune** system prompt — about 3 000 tokens at the cap, comfortably inside one request and well
under `maxOutputTokens`' companion input limits, but not the "roughly 3 000 runes" this note first
estimated.

### Reply schema, and the caps

```json
{"channel": "radio",
 "text": "SELL 5 5 ORE ORE AT 12 12",
 "confirm": {"ticket": 7, "side": "SELL", "qty": 5, "commodity": "TIN", "price": 50},
 "notes": "Gizmo repeats prices; Widget is terse — steal-able."}
```

| field | type | cap | on violation |
|---|---|---|---|
| `channel` | string | **16 runes**, rune-truncated | unknown value normalises to `"radio"` |
| `text` | string | **160 runes**, rune-truncated, then 32 words | missing/`null` ⇒ empty transmission (legal: a silent turn) |
| `notes` | string | **400 runes**, rune-truncated | missing ⇒ previous notes kept, as babel does |
| `confirm` | object or `null` | — | missing/`null` ⇒ no confirm |
| `confirm.ticket` | int | `≥ 1` | out of range ⇒ ill-formed ⇒ retry ⇒ fallback |
| `confirm.side` | string | `SELL`/`BUY`, any case | anything else ⇒ ill-formed |
| `confirm.commodity` | string | `ORE`/`OAT`/`TIN`/`TAR`, any case | anything else ⇒ ill-formed |
| `confirm.qty`, `confirm.price` | int | `0…99`; a numeric string or a float is accepted and rounded; a spelled number word is accepted | out of range ⇒ ill-formed |

**Every truncation is on rune boundaries** (`runeSubStr`, with `…` marking the cut) — a string cut
on a **byte** boundary mid-UTF-8 renders in a browser but fails a strict JSON parser, and every
string here lands in the replay. The player-protocol `prompt` frame is likewise capped at **4000
runes**.

Trailing prose after the closing `}` is tolerated (`extractJsonObject` takes the first `{` to the
last `}`). A reply that parses but whose confirm is **inadmissible** is *not* an error: it is a legal
move that produces a `void` event.

### Scripted baselines (same image, env-switched)

Both baselines are fieldable policies **and** the fallback path, in the **same image**, selected by
env: `PLAYER_PROMPT="<strategy>"` for an LLM policy, `PLAYER_SCRIPTED=<baseline name>` for a
scripted one. Neither ever produces notes, and both are legal by construction (bounded qty/price,
bounded text, never raise).

**`quoter`** — the fallback baseline and filler #1.

1. If it holds ≥ 3 units of `sur[s]`, it broadcasts an offer on the **radio**:
   `SELL <q> <SUR> AT <p>` with `q = min(5, units[sur])` and
   `p = clamp(price[t][sur] + 3, 1, 99)`, written in digits.
   **When `interference[t] ≥ 0.5` it repeats every field once** (`SELL 5 5 ORE ORE AT 14 14`) —
   the redundancy shield, applied by rule.
2. Otherwise, if it holds < `quota` of `dem[s]`, it broadcasts
   `BUY <q> <DEM> AT <p>` with `q = min(5, quota - units[dem])` and
   `p = clamp(price[t][dem] + 1, 1, 99)`, doubled the same way when the meter is loud.
3. It confirms **honestly**: among the open tickets it may confirm, it takes the first (lowest id)
   whose *heard reading* parses and improves its portfolio — buying `dem` at
   `price ≤ price[t][dem] + premium - 1`, or selling `sur` at `price ≥ price[t][sur] + 1` — and
   asserts **exactly the fields it heard**.
4. It stops transmitting when `airtime < 30`, keeping the meter for confirms.

Those five numbers — the `min(5, …)` lot, the `+3` ask, the `+1` bid, the `0.5` loud band and the
`30`-rune floor — are `BaselineParams.DefaultBaseline` in `src/garble/llm.nim`, and they are swept,
not guessed: `scripts/tune_baselines.nim` plays the whole 576-point grid around them over 60 seeds
× four tables and scores every point against the four properties the baselines must hold (a deal
on every seed and ≥ 3 on the median seed; a shark-heavy table mishears more than an honest one;
the quiet band outscores the storm; the mean quoter score is above 1.0). The table it prints, and
the per-parameter reading of it, are committed at `docs/tuning/baseline-grid.md`.

**`shark`** — filler #2, the antagonist that makes the shield legible.

Same offers as `quoter` but **never repeated** (terse, fast, steal-able), and it confirms
**strategically**: for the ticket it picks it asserts, for `qty` and `price`, the most favourable
value in `{heard} ∪ neighborsOf(heard word)` — as a buyer the lowest price and highest quantity, as
a seller the reverse. It cannot see the said text, so it voids often against a repeating
counterparty and robs a terse one. That is the intended shape: **`shark` beats `quoter` when
`quoter` is quiet-cheap, and loses to it when the meter is loud and `quoter` repeats.**

---

## Sim module

Four files under `src/garble/`, all forked from babel by path, plus one new pure module. No IO, no
networking and no LLM anywhere in `sim.nim` or `wire.nim` — the server, the tests and the wasm
viewer drive the same code.

### `src/garble/types.nim` (fork of `src/babel/types.nim`)

`GarbleError`, `PlayerConfig`, `GameConfig`, `EventKind`, `GameEvent`, `defaultGameConfig`,
`update`. `GameConfig` is babel's with `turns` replacing `rounds`, plus `noiseScale: float`
(default 1.0) and `minTurnSpacingMs: int` (default 12 000). `update` validates
`turns ≥ MinTurns` and `noiseScale` in `0.0 … 2.0` and raises `GarbleError` otherwise.

### `src/garble/wire.nim` (new; pure)

The channel, in one auditable module:

- `Commodities = ["ORE", "OAT", "TIN", "TAR"]`, `Verbs`, `Pivot`, `SpelledNumbers`,
  `SpelledNeighbors`, `CommodityNeighbors`.
- `normaliseWords(text): seq[string]` — uppercase, punctuation → space, split, cap at `MaxWords`.
- `wordValue(w): int` / `isNumberWord(w): bool` / `commodityIndex(w): int`.
- `neighborsOf(word): seq[string]` — the table above; deterministic order (digit rules first, then
  the spelled/commodity table) so a swap draw is reproducible.
- `Terms = object {side: Side, qty, commodity, price: int, kQty, kCom, kPrice: int,
  qtyWord, comWord, priceWord: string}`.
- `scanTerms(words): Option[Terms]` — the seven numbered steps.
- `WordFlag = enum wfOk, wfDrop, wfSwap, wfStatic`;
  `HeardWord = object {said, heard: string, flag: WordFlag}`.
- `garble(words, seed, turn, fromSeat, toSeat, noise, burst, burstFrac, burstLen): seq[HeardWord]` —
  the delivery model, exactly as specified.
- `heardText(words: seq[HeardWord]): string` — the heard line, with `▩` for a dropped or blanked
  word.
- `admissible(said: Terms, asserted: Terms): bool` — the redundancy shield.

### `src/garble/sim.nim` (fork of `src/babel/sim.nim`)

- Constants: `Seats = 5`, `Commodities = 4`, `MinTurns = 6`, `MaxTurns = 24`,
  `EpisodeCallBudget = 120`, `CallsPerTurn = 5`, `PacingBudgetMs = 60_000`,
  `MaxTextRunes = 160`, `MaxWords = 32`, `MaxNotesRunes = 400`, `MaxChannelRunes = 16`,
  `AirtimeBudget = 900`, `ConfirmAirtime = 40`, `TicketLife = 2`, `MaxQty = 99`, `MaxPrice = 99`,
  `LineNoiseFactor = 0.6`, `HeardWindow = 3`, `CogNames` (babel's pool, verbatim).
- `Sim` fields: `config`, `names`, `sur`, `dem`, `premium`, `quota` (per seat), `prices:
  seq[array[4, int]]` (the whole path, drawn at init), `interference: seq[float]`,
  `burst: seq[bool]`, `burstFrac: seq[float]`, `burstLen: seq[int]`, `cash`, `units`,
  `airtime`, `notes` (per seat), `startCash`, `startUnits` (for `hold`), `tickets: seq[Ticket]`,
  `deals: seq[Deal]`, `turn`, `turnsPlayed`, `phase`, `done`, `reason`, `events`.
- `Ticket = object {id, offerer, turn, expiry: int, channel: int (-1 = radio, else the addressed
  seat), terms: Terms, said: string, settled: bool}`.
- API: `initSim`, `sampleEpisode`, `tableNames`, `beginTurn`, `applySay(sim, seat, channel, text,
  notes, scripted)`, `applyConfirm(sim, seat, ticket, side, qty, commodity, price, scripted)`,
  `endEarly`, `portfolio(sim, seat)`, `holdValue(sim, seat)`, `score(sim, seat)`,
  `heardFor(sim, seat, event): seq[HeardWord]`, `openTicketsFor(sim, seat): seq[Ticket]`,
  `resultsJson`, `tableStateJson`, `replayMatch(config, events)`, `eventToJson`, `eventFromJson`.
- **Illegal operations raise `GarbleError`** and leave the sim unchanged: a `say` out of turn, a
  second `say` from the same seat in one turn, a `confirm` before every `say` of the turn has
  landed, a qty or price outside `0..99`, an unknown commodity index, any call after `done`.
  An **inadmissible** or **uncovered** confirm is *not* illegal — it appends a `void` event.

### Event vocabulary — what the replay carries

Flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`, unset fields omitted. Seven kinds:

| kind | fields |
|---|---|
| `start` | — (everything else is derivable from `config.seed` + `turns` + `noiseScale`) |
| `turn` | `turn`, `interference` (float), `burst` (bool), `prices` (4 ints), `portfolios` (5 ints), `airtime` (5 ints) |
| `say` | `turn`, `seat`, `channel` (`-1` radio, else the addressed seat), `text` (said, ≤ 160 runes), `cost`, `airtimeLeft`, `silent`, `clipped`, `ticket` (id or `-1`), `terms` (`side`,`qty`,`commodity`,`price`,`kQty`,`kCom`,`kPrice`) or omitted when the text does not parse, `scripted`, `notes` (the seat's notes after this reply, ≤ 400 runes) |
| `confirm` | `turn`, `seat`, `ticket`, `side`, `qty`, `commodity`, `price`, `scripted` |
| `deal` | `turn`, `ticket`, `seller`, `buyer`, `commodity`, `qty` (asked), `fill`, `price`, `saidQty`, `saidCommodity`, `saidPrice`, `partial`, `misheard`, `cash` (credits moved) |
| `void` | `turn`, `seat`, `ticket`, `reason` (`no-ticket`\|`expired`\|`already-settled`\|`own-ticket`\|`not-addressed`\|`side`\|`inadmissible`\|`uncovered`) |
| `end` | `turn` = turns played, `text` = `reason`, `prices` (final 4), `portfolios` (5), `scores` (5 floats) |

`turn`, `deal`, `void` and `end` are **derived** facts that are nevertheless **recorded**, and
`replayMatch` re-derives them and raises `GarbleError` on any mismatch — babel's schedule-check
pattern, applied to settlement. `say` and `confirm` are the decisions; re-applying them through the
rules reproduces everything else, garbling included, because the delivery RNG depends only on
`(seed, turn, from, to)`.

**The heard text is never recorded.** It is re-derived by `wire.garble` in the viewer from the said
text and the seed — the same code the server ran. That keeps the replay small and makes the
spectator's "the audience always knows what was actually said" literally true: the bytes carry the
truth and the viewer computes the lie.

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"seats":[{"name":"Sprocket","portfolio":340,"hold":340,"score":1.0,
           "cash":120,"units":[20,0,0,0],"surplus":0,"demand":2,
           "airtime":612,"silent":false,"deals":1,"misheard":0,
           "channel":-1,"notes":"…"}, ×5],
 "turn":4,"turns":12,"turnsPlayed":4,
 "interference":0.62,"burst":false,"band":"ROUGH",
 "curve":[0.18,0.34,0.57,0.71,0.62,0.41,…12],
 "prices":[12,9,11,8],"prevPrices":[11,10,11,9],
 "commodities":["ORE","OAT","TIN","TAR"],
 "wire":[{"seat":1,"channel":-1,"said":"SELL 5 TIN AT 50","silent":false,"clipped":false,
          "ticket":7,
          "heard":[{"to":0,"words":[{"said":"SELL","heard":"SELL","flag":"ok"},
                                    {"said":"5","heard":"","flag":"drop"},
                                    {"said":"TIN","heard":"TIN","flag":"ok"},
                                    {"said":"AT","heard":"AT","flag":"ok"},
                                    {"said":"50","heard":"5","flag":"swap"}]}, …]}],
 "tickets":[{"id":7,"offerer":1,"channel":-1,"turn":3,"expiry":6,
             "side":"SELL","qty":5,"commodity":2,"price":50,
             "kQty":1,"kCom":1,"kPrice":1,"settled":false}],
 "tape":[{"ticket":4,"turn":2,"seller":4,"buyer":2,"commodity":1,"qty":12,"fill":12,
          "price":9,"saidQty":12,"saidCommodity":1,"saidPrice":9,
          "partial":false,"misheard":false}],
 "phase":"open|wire|settle|between|done",
 "gameDone":false,"reason":""}
```

`wire` holds the **live turn's** transmissions (or the last completed turn once `done`), each with
its per-recipient garbling, word by word — that is what the stage draws SAID over HEARD. `curve` is
the published interference base for every turn, on the `noiseScale` scale (§*The wire*). `band` is `CLEAR` (< 0.25), `HAZY` (< 0.50),
`ROUGH` (< 0.75) or `STORM`.

### `resultsJson` — platform-facing, policy names

```json
{"names":[5 policy names],
 "scores":[5 floats],          // portfolio / hold; higher is better
 "portfolio":[5 ints],"hold":[5 ints],"cash":[5 ints],
 "units":[[4 ints] ×5],
 "deals":[5 ints],"misheard":[5 ints],"voids":[5 ints],"airtimeUsed":[5 ints],
 "turns":<played>,"maxTurns":<cap>,"reason":"complete|deadline"}
```

### Replay payload — `garble.replay.v1`

```json
{"protocol":"garble.replay.v1",
 "names":[5 aliases],"policyNames":[5 policy names],
 "config":{"turns":12,"seed":8123,"noiseScale":1.0,"sampled":true,
           "commodities":["ORE","OAT","TIN","TAR"],"airtimeBudget":900},
 "events":[…],"results":{…}}
```

Replay mode and the wasm viewer add `"states"` — one `tableStateJson` per event prefix — exactly as
babel does. **The bytes are self-sufficient**: names, policy names, the whole config, the seed, every
decision event, and the results. The viewer contacts nothing but S3 for the `.replay` file; prices,
contracts, interference, bursts and every garble are re-derived from `seed` by the same Nim module
the server ran.

---

## Server, player, protocol

### `src/garble/server.nim` (fork of `src/babel/server.nim`)

Endpoints are babel's, unchanged in shape and in registration order (the certifier probes
`/healthz`, `GET /client/player?slot=0&token=…`, a bad-token player websocket, and
`GET /client/global` **before** any player pod starts, so both `/client/` routes must serve real
pages and neither may open the player socket — lantern 0.1.1):

```
GET /healthz            GET /client/global      GET /client/player
GET /client/replay      GET /client/renderer.js GET /client/chrome_common.js
GET /client/chrome.css  GET /client/assets/<name>
WS  /player?slot=N&token=T   WS /global   WS /replay
```

`/client/chrome_common.js` is the one added route (a `serveFile` of `client/chrome_common.js` with
`application/javascript; charset=utf-8`). `/healthz` and `/global` keep answering — including
answering a websocket **Ping with a Pong**, which mummy hands to the application — for a bounded
~20 s shutdown grace after the artifacts are written, then the process exits (lantern 0.1.3 → 0.1.4).

The game loop is replaced by the numbered turn order of §*The game*: snapshot the sim under the
lock; build every observation; issue **one batch** outside the lock; apply `say` then `confirm`
under the lock; broadcast; pace. `finishEpisode` is babel's, unchanged: final frames to the player
sockets **first** (with table aliases, not policy names), then `results.json`, then the replay, then
`quit(0)`.

### Observation — exactly what each seat sees, and what is hidden

| visible to seat `s` | hidden from seat `s` |
|---|---|
| turn index and `turns` | every other seat's cash, units, surplus, demand, premium, quota |
| `interference[t]`, its band, and the published base **curve for the whole episode** | `burst[t]` for any future turn |
| all four prices, current and previous | future price draws |
| its own cash, units, surplus, demand, premium, quota, portfolio, `hold`, score | every other seat's notes |
| its own airtime remaining | the **said** text of any transmission it did not send |
| its own **heard** traffic (last 3 turns in full, earlier summarised) | any other listener's heard version |
| open tickets it may confirm: id, offerer alias, channel, open/expiry turn, its own heard text and its own parse | the said terms behind a ticket, and the `k` counts |
| the **public tape**: every settled deal, both versions, with parties | which seats are scripted |
| its own notes, verbatim | policy display names (aliases only) |
| its operator prompt (`PLAYER_PROMPT`) | other seats' operator prompts |

The hidden column is why the **player websocket gets a redacted state**: Garble has real hidden
information, and decisions are made server-side, so a player frame carries only that seat's own
public tallies. Nothing is lost.

### Player protocol — `garble.player.v1`

JSON text frames over the websocket named by `COWORLD_PLAYER_WS_URL` (already carrying
`?slot=N&token=T`). **A Garble policy is a prompt**: the player container's only job is to deliver
it.

- game → player, on connect:
  `{"type":"welcome","protocol":"garble.player.v1","slot":N,"name":"<alias>","turns":12}`
- game → player, after every event (redacted):
  `{"type":"state","slot":N,"name":"<alias>","seat":{"portfolio":int,"hold":int,"score":float,
  "cash":int,"units":[4],"airtime":int,"deals":int,"misheard":int},"turn":int,"turns":int,
  "turnsPlayed":int,"interference":float,"prices":[4],"started":bool,"done":bool,"reason":str}`
- game → player, at the end:
  `{"type":"final","done":true,"slot":N,"scores":[5],"portfolio":[5],"names":[5 aliases],
  "turns":int,"reason":str}` — after which the player exits 0.
- player → game:
  `{"type":"prompt","prompt":str,"scripted":bool,"baseline":str}`, with `prompt` capped at **4000
  runes** (rune-truncated by the server on receipt). `scripted: true` plays the
  built-in baseline named by `baseline` (`quoter` or `shark`; anything else ⇒ `quoter`). The latest
  frame applies to every later turn; the player re-sends after `welcome` in case the first send
  raced slot registration.

### Global protocol

Spectators connect to `/global` and receive the full `tableStateJson` snapshot after every event,
plus `"type":"state"`, `"game":"garble"`, `"policyNames"`, the append-only `events` array,
`"started"`, `"done"` and `"connected"`. The global protocol text states the commodity indexing
(`0 ORE, 1 OAT, 2 TIN, 3 TAR`), that `channel: -1` means the radio, that the `events` array is the
complete transcript including every seat's notes and every said text, that **heard text is derived,
not transported**, and that the static bundle renders hosted replays at `index.html?replay=<url>`.

### `src/garble_player.nim` (fork of `src/babel_player.nim`)

Reads `PLAYER_PROMPT` (or a sound default Garble strategy), `PLAYER_SCRIPTED` (`quoter` / `shark` /
`1` ⇒ `quoter`), delivers the prompt frame, re-delivers after `welcome`, then idles until `final`.
The receive loop is wrapped in `try/except CatchableError` and **exits 0** on a dead socket.

Default prompt (used when `PLAYER_PROMPT` is empty):

> Trade toward your contract commodity and out of your surplus. Price your offers between the market
> price and the market price plus your premium — anything inside that band is profitable. Watch the
> interference meter before you speak: when it is under 25% be terse and fast, and when it is over
> 50% repeat every number and every commodity once, because a repeated field cannot be confirmed
> against you. Spell numbers out when they are round; a spelled number has one near-neighbour and a
> digit has three. Confirm the reading you actually heard when the counterparty repeated, and when
> they did not, weigh whether the favourable neighbour is worth the ticket. Keep a note of who
> repeats and who is terse — the terse ones can be taken and will take you. Airtime is the budget
> that decides how much protocol you can afford: do not spend it on chatter.

---

## Viewer

### The four viewer files — one starter, no splicing

**All four viewer files come from one starter, `Metta-AI/cogame-babel`, and only from it:**

| file | source |
|---|---|
| `replay-viewer/config.nims` | `cogame-babel/replay-viewer/config.nims` |
| `replay-viewer/garble_replay.nim` (the wasm entry) | `cogame-babel/replay-viewer/babel_replay.nim` |
| `replay-viewer/static_replay.js` | `cogame-babel/replay-viewer/static_replay.js` |
| `replay-viewer/index.html` | `cogame-babel/replay-viewer/index.html` |

Nothing is spliced in from another starter — **not from bullwhip, not from parley, not from ctf.**
Babel's emscripten link flags are kept exactly, with only the names substituted: `-O2`,
`ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`, `MODULARIZE=1`,
**`EXPORT_NAME=GarbleReplayModule`**, `EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_gar_load_replay,_gar_payload_ptr,_gar_payload_len,_gar_error_ptr,_gar_error_len`,
plus `--mm:arc`, `--exceptions:goto`, `--define:useMalloc`, `--define:noSignalHandler`,
`--define:release`, and `emscripten_exit_with_live_runtime()` in `isMainModule` (without it Nim's
generated main runs the module-global destructors and frees `payload` while JS is still reading it).
`static_replay.js` keeps calling the module through that same `GarbleReplayModule()` **factory**:
the `MODULARIZE`/`EXPORT_NAME` contract and the JS bootstrap must come from the same starter —
splicing one starter's shell onto another's link flags deadlocks the viewer silently, with every
asset returning 200 (cogame-lantern, 2026-08-23).

The wasm module parses the replay bytes with the **same `src/garble/sim.nim` + `src/garble/wire.nim`**
the game server runs, re-derives every frame with `replayMatch`, and exposes the enriched payload
(identical shape to the `/replay` websocket message) for `renderer.js` to draw. Exported symbols are
babel's with the `bab_` prefix renamed to `gar_`.

### Load signalling

- `renderer.js`'s `attachReplay` sets
  `document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame**
  — babel already does exactly this at the end of `attachReplay`'s `makeRenderer` callback, and it
  is kept verbatim. `static_replay.js` additionally posts the `coworld-replay` `{type:"ready"}`
  envelope one animation frame later.
- `static_replay.js` sets **`data-replay-error="<message>"`** on `<html>` and posts `{type:"error"}`
  on any failure — a missing `?replay=`, the 20 s fetch timeout, a non-200, a wasm rejection — and
  removes the attribute on a successful retry. The Retry button re-fetches without a page reload.
- **Nothing about audio ever gates these signals.**
- `tools/ci/viewer_smoke.mjs` reads exactly these two signals.

### Bundle and build hook

`"replay_viewer": {"bundle": "static-replay-viewer"}` in the manifest — a **static wasm bundle,
never a `/client/replay` pod URL**. `tools/build_replay_viewer.sh` (babel's hook, paths renamed,
committed **`chmod +x`**) is the `coworld build` hook: it compiles
`replay-viewer/garble_replay.nim` to wasm with local `emcc`+`nim` when both exist, otherwise inside
the pinned `emscripten/emsdk` container from `Dockerfile.replay-viewer`, then copies
`garble_replay.js`, `garble_replay.wasm`, `replay-viewer/index.html`,
`replay-viewer/static_replay.js`, **`client/chrome_common.js`**, `client/renderer.js`,
`client/chrome.css` and the seven `data/` assets (the five cog sprites, `arena_floor.png`,
`font.ttf`) into the bundle. It **`mkdir -p`s the output parent
before the containment check** (ecos, 2026-08-23: the inherited hook exits 1 on a fresh CI checkout
because `coworld build` pre-creates that directory and CI does not). The final `grep -q 'data-replay'`
assertion on the copied `static_replay.js` is kept.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from the starter.** Every function in it is
  `cogame-babel/client/renderer.js`'s function, character for character, with no edits:
  `assetUrl`, `loadImages`, `seatColor`, `ellipsize`, `hexToRgb`, `shade`, `rgba`, `roundRect`,
  `wrapLines`, `escapeHtml`, `clampName`, `isBaselineFiller`, `makeNameMap`, `applyNames`,
  `bindFeedToggle`, and the palette constants `COLORS`, `COLOR_HEX`, `PAPER`, `INK`, `AMBER`,
  `GHOST`, `CARD_EDGE`, `STRIP`. The only non-copied lines are the IIFE wrapper, the
  `window.GarbleChrome = {…}` export, and **one clearly-marked added function**, `relayout()`
  (below). `makeNameMap` is copied *including* its third `glyphs` parameter and its unused `.glyph`
  accessor; Garble calls it with two arguments and the parameter defaults to `[]`. Babel's
  `makeEffects` is **not** chrome — it is per-pair and game-specific — so it is forked into the game
  block as `makeGarbleEffects` and is not part of `chrome_common.js`.
- **`client/chrome.css` is copied unchanged** from `cogame-babel/client/chrome.css`. Garble's
  additions live in one appended block at the end of the file, marked
  `/* ---------- garble additions ---------- */`; no existing rule is edited.
- **`client/replay_broadcast.html` is the starter's page with a game block appended.** It *is*
  `cogame-babel/client/replay.html`, with (a) the identifier renames a fork requires —
  `BabelRenderer` → `GarbleRenderer`, the `<title>`, the `#wordmark` text `BA<span>BEL` →
  `GAR<span>BLE`, and the `#clock` placeholder `ROUND 0` → `TURN 0` (Garble counts turns, and the
  renderer overwrites it on the first frame anyway) — (b) **one inserted line**,
  `<script src="/client/chrome_common.js"></script>` immediately *before* the starter's
  `<script src="/client/renderer.js">` (the game block reads `window.GarbleChrome` lazily inside
  functions, but the chrome module must exist before the inline bootstrap calls `bindFeedToggle`),
  and (c) the Garble **game block appended before `</body>`** — the `♪ STATIC` button inside the
  existing `.tbar`, and the commodity legend strip. It is **not** a from-scratch page that reuses
  the starter's ids (cogame-gridlock, 2026-08-23). `client/global.html` and `client/player.html`
  are forked the same way. The server route `/client/replay` serves
  `client/replay_broadcast.html`.
- **Elements removed from the starter page: none.** `#layout`, `#stage`, `#topband`, `#wordmark`,
  `#clock`, `#topright`, `#statuschip`, `#feedtoggle`, `#scorebug`, `#board-wrap`, `#table`,
  `#lightpool`, `#grain`, `#endscreen`, `#transport`, `#scrub`, `.tbar`, `#play`, `#pos`, `#feed`
  and `#loading` are all kept, with their ids and their CSS. `#lightpool` and `#grain` are pure
  atmosphere and stay — `#grain` is doubly apt here and is driven harder during a static burst.
- **Zoom: dropped entirely.** There is no `#viewpanel`, no zoom bar and no minimap. The Garble stage
  is a fixed arena always rendered to fit the frame — it is never larger than the frame, so the zoom
  chrome would be dead weight. (Babel ships none either; none is added.)

### Transport rules

- **`--band` and `--hudscale` are set on `:root` by `relayout()`** — the one added function in
  `chrome_common.js`. It measures `#topband` and `#transport` with `getBoundingClientRect()` and
  writes `--topband`, `--band` and `--hudscale` (`clamp(0.7, stageWidth / 960, 1.6)`) on
  `document.documentElement`. It runs on `load`, on every `resize`, and after every `bindFeedToggle`
  toggle. Every Garble-added chrome measure derives from `--hudscale`, never from the raw viewport.
- **No overlay sits in the transport band.** `#transport` is the last flex row of `#stage`;
  `#endscreen` is `position: absolute; inset: 0` **inside `#board-wrap`**, which is a *sibling
  above* `#transport`, so it structurally cannot cover the band. The appended CSS block additionally
  pins `#endscreen { bottom: var(--band, 0px); }` so the rule still holds if the endcard is ever
  repositioned against `#stage`. `#loading` is the only full-frame overlay and it is `display:
  none`d the instant the payload attaches, before playback starts.
- **The endcard is dismissed by every seek.** `attachReplay`'s `setIndex` calls
  `updateEndscreen(container, results, index >= events.length && events.length > 0, nameMap)` on
  **every** index change, and `updateEndscreen`'s first statement is
  `container.classList.toggle("show", !!show)` — so any seek below the last event hides it
  immediately. This is babel's behaviour, kept.
- **Scrubber beats are clickable, labelled buttons.** `buildGarbleScrub` (in the game block, *not*
  in `chrome_common.js`) builds one `<button class="beat-marker …">` per emitted beat, each with
  `type="button"`, an `aria-label` and a `title` (`"Turn 4 — Gizmo confirms #7 as SELL 50 TIN at 1
  — MISHEARD"`), and an `onclick` that seeks to that event index. Drag-to-seek on the track is kept
  alongside, and one `.round-span` per turn is kept from babel's `buildScrub`. **CSS for every kind
  emitted**, in the appended block:

  | kind emitted | class | CSS |
  |---|---|---|
  | `start` | `.beat-marker.start` | 2 px ghost tick |
  | `turn` | `.beat-marker.turn` | 1 px amber hairline, full height; `.burst` adds a jagged amber cap |
  | `say` | `.beat-marker.say.seat<i>` | 2 px tick in the seat colour; `.silent` renders hollow |
  | `confirm` | `.beat-marker.confirm.seat<i>` | 3 px tick with a notch, seat colour |
  | `deal` | `.beat-marker.deal.seat<i>` | 4 px block, seat colour; `.misheard` overprints a red slash |
  | `void` | `.beat-marker.void` | 2 px ghost tick with a cross |
  | `end` | `.beat-marker.end` | 3 px × 14 px amber block (reuses babel's `.death` geometry) |

  The builder is named `buildGarbleScrub` and the marker helper `garbleMarkBeat` — **no game-block
  function may share a name with any key of `GarbleChrome`**, because a `var markBeat = C.markBeat`
  alias block plus a hoisted `function markBeat` silently shadows the chrome one and every static
  grep stays green (tandem, 2026-08-23). A CI check asserts the disjointness (§*Tests*).

### The stage — what the viewer draws

Canvas scene over `data/arena_floor.png` in babel's Ink & Print palette; seat colours are
`COLORS[0..4]` = red, blue, green, yellow, **violet**.

- **The interference meter** runs across the top of the stage: the published base `curve` as a
  paper sparkline over all `turns` turns, the live turn's value as a filled amber column, the band
  word (`CLEAR / HAZY / ROUGH / STORM`) beside it. On a **burst turn** the whole stage takes a
  static wash (a seeded scanline overlay plus `#grain` at double opacity for ~700 ms) and an amber
  `STATIC BURST` tag stamps the meter. The meter is weather and it visibly swells and fades.
- **The transmission card** is the centrepiece, and it is what the idea asks for: for the `say`
  event being played, the **SAID** line across the top in the speaker's colour, in a monospaced
  word-spaced setting; beneath it one **HEARD** line per recipient, labelled with the listener's
  name in the listener's colour. A dropped or blanked word renders as `▩` **in red**; a swapped
  word renders the *heard* word **in red with a red underline** and the said word ghosted above it
  at 60 % size. A clean word is ink. This is SAID vs HEARD side by side, word for word, and the
  audience always knows what was actually said.
- **The five cogs** ring the card. Each seat has its **own** finished sprite —
  `data/cog_<red|blue|green|yellow|violet>_front.png`, 128×128 RGBA, one radio kit per seat (whip
  antenna, dish, headset-and-key, crank set, rabbit ears) — generated for this game with
  nano-banana from the Softmax cog reference (§*Packaging*) and loaded by name in
  `client/renderer.js`. **There is no tint path**: the fifth cog is real art in its own colour, not
  the red sprite recoloured at draw time. Under each cog: name, portfolio in credits, score as `1.42×`,
  and an **airtime meter** (a small bar, `airtime / 900`) that visibly drains; a `SILENT` tag when
  it is empty, a `RADIO` or `LINE → Gizmo` tag for what the cog transmitted this turn.
- **The tape** runs along the bottom: settled deals as trade tickets. A clean deal prints one line.
  A **misheard** deal stamps **both versions** — the said terms ghosted and struck through, the
  confirmed terms in red under a `MISHEARD` stamp, with `partial 20/50` when the fill was short.
  New tickets slide in and hold, using babel's eased-timer effect bookkeeping.
- **The price ticker** sits above the tape: four commodity chips with price and a ▲/▼/= delta.
- **`#lightpool`** sweeps to the leading seat on the final frame.

### Audio — what v1 actually ships

The idea's "audible static crackle" ships, in the smallest honest form, following the precedent set
by cogame-chorus:

- **WebAudio synthesis, in-bundle, no assets.** One `AudioBufferSourceNode` of seeded white noise
  through a `BiquadFilterNode` (bandpass ~1.8 kHz) and a `GainNode` whose level tracks
  `interference[t]` (0.0 at `CLEAR`, 0.18 at `STORM`), plus a short crackle burst on every garbled
  word as it is drawn. Master gain 0.2 into a `DynamicsCompressorNode`.
- **Off by default, behind one `♪ STATIC` button** in the transport bar (`.tbtn`, inside the band,
  never overlaid on it). The `AudioContext` is constructed only on that button's first click, which
  is the user gesture browser autoplay policy requires.
- **Fully fenced.** Every AudioContext call is inside `try/catch`; on any failure the button becomes
  `♪ STATIC N/A`, is disabled, and the viewer continues visual-only. **Audio never gates
  `data-replay-loaded` and never touches the render loop**, so the headless CI smoke is unaffected.
  A seek cancels every scheduled node.

### Readouts

- **`#clock`** — `TURN 4 / 12 · ROUGH 62%` while playing, with `· STATIC BURST` appended on a burst
  turn and `· WAITING ON 3` while a turn's transmissions are still landing;
  `FINAL — SPROCKET 1.42×` once done; `FINAL — SPROCKET 1.18× · DEADLINE` on a deadline ending.
- **`#scorebug`** — one plate per seat: name (policy name spectator-side, alias for fillers),
  **portfolio in credits** as the big number, label `credits`, the score ratio to two decimals, an
  airtime pip strip (12 pips, filled proportionally), and `▶` while the seat's decision is pending.
  `.plate-name` keeps babel's `flex: 1 1 auto; min-width: 3.2em`.
- **`#feed`** (side panel, babel's `LOG »` toggle, one section per turn under a
  `TURN 4 · INTERFERENCE 62% ROUGH` head):
  - `Sprocket ▸ RADIO: "SELL 5 5 ORE ORE AT 12 12"` (said, seat colour; `▸ LINE→Gizmo` for a line;
    `·` marks a scripted decision, as babel does; `— SILENT (no airtime)` when out of meter)
  - `Gizmo hears: "SELL 5 ▩ ORE ORE AT 12 12"` — **printed only when the heard line differs from
    the said line**, with the garbled words in red
  - `Ratchet confirms #7 — SELL 50 ORE at 1`
  - `DEAL #7 — Sprocket sells 20 ORE to Ratchet at 1 · said 5 at 12 · MISHEARD · partial 20/50`
  - `VOID #7 — Ratchet's confirm was inadmissible (qty was said twice)`
  - `PRICES ORE 12 ▲ · OAT 9 ▼ · TIN 11 = · TAR 8 ▼`
  - `Sprocket notes: "…"` (dim, only when a seat's notes change)
  - `FINAL — Sprocket 1.42× (312 cr)` / `Episode deadline — scored on 7 of 12 turns.`
- **`#pos`** — `31 / 96` (event index), babel's, unchanged.
- **`#endscreen`** — title `FINAL — 12 TURNS`; verdict `SPROCKET LEADS THE TABLE` (or `ALL LEVEL`);
  a `deadline` sub-line when applicable; ranked rows by score with columns `rank`, `name`, `score`
  (`1.42×`), `credits`, `deals`, `misheard`, `airtime used`.

### Legible at 360 px wide

The featured-match iframe on softmax.com is about **360 px** wide, and the viewer is checked there,
not at desktop width.

- The canvas re-fits on `resize` (`fit()` in `index.html` and in `replay_broadcast.html`, kept
  verbatim) and `relayout()` re-derives `--hudscale`.
- **Below 560 px** the stage switches to a compact composition: the transmission card takes the full
  width with the SAID line and **at most two** HEARD lines (the recipients whose hearing differs
  most, then the addressed seat on a line); the cog ring collapses to a single row of five portraits
  with credits under them; the tape shows the last two tickets; the interference sparkline drops to
  the live column plus the band word.
- **Below 640 px** the scorebug hides the `.plate-label` `credits` captions and keeps name +
  credits + ratio; `.plate-name` shrinks last and never below 3.2 em (a `.plate-name` without
  `flex: 1 1 auto; min-width: 3.2em` collapses every player name to `…` in the featured match).
- The feed collapses behind the existing `LOG »` toggle.
- Words are words and numbers are numerals: `ORE`, not `c0`; `SELL 50 at 1`, not `S/50@1`;
  `1.42×`, not `+42%`; `MISHEARD`, not a red dot.

---

## Packaging

- **`compose.yaml`** — one service named **`garble`** (the manifest image placeholder is derived
  from the compose service name, so it must be `{{GARBLE_IMAGE}}`; `{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0), `image: coworld-garble:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`.
- **`Dockerfile`** — babel's, renamed: one image, two entrypoints `/bin/garble` (default `CMD`) and
  `/bin/garble-player`; `data/` and `client/` copied into the run image.
  **`Dockerfile.replay-viewer`** — babel's, renamed.
- **`garble.nimble`** — version `0.1.0`, `srcDir = "src"`, `requires "nim >= 2.2.4"`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from babel.
- **`data/`** — babel's `arena_floor.png`, `font.ttf` and `FONT_LICENSE.txt`, unchanged, plus the
  five generated cog sprites `cog_<red|blue|green|yellow|violet>_front.png` (128×128 RGBA). The
  starter's four `soldier_*_front.png` sprites are **not** shipped: nothing references them.
  Real art, not placeholders, per `playbooks/make-coworld.md` §Phase 0 and
  `playbooks/art-nanobanana.md` — a deviation from this note's original violet-tint plan, accepted
  by the coordinator on 2026-08-24.
- **`scripts/art/`** — how that art was made, committed so it is reproducible:
  `gen_cog_sheet.py` (one nano-banana / Gemini render of five cogs in a row from
  `scripts/art/source/cog_reference.png`, written to `scripts/art/source/cogs_sheet.png`) and
  `split_cog_sheet.py` (backdrop key-out, split, crop, pad, resize → the five `data/cog_*.png`).
  The derived PNGs are committed; CI never regenerates art and never needs an image-model key.
- **`README.md`** — the game in a paragraph, the layout list, the local loop, how to field a policy.

### `coworld_manifest_template.json`

Top level: `$schema`, **≥3 `tags`**
(`trading`, `negotiation`, `noisy-channel`, `mixed-motive`, `llm-driven`, `turn-based`,
`five-player`, `market`), `game`, top-level `player[]`, `variants[]`, `certification`,
`episode_timeout_minutes: 20`.

`game`: `name: "garble"`, `runnable.type: "game"`, `image: "{{GARBLE_IMAGE}}"`,
`run: ["/bin/garble"]`,
`env.ANTHROPIC_API_KEY_URI: "secret://coworld/garble/anthropic_api_key"` (**without this the hosted
container never receives the secret and every league episode plays scripted while local certify
still passes** — hive, 2026-08-23), `source_url:
"https://github.com/Metta-AI/cogame-garble/tree/main"`, `owner: "daveey@gmail.com"`, and
`"replay_viewer": {"bundle": "static-replay-viewer"}`.

**`game.config_schema`** — a real JSON Schema, `additionalProperties: false`,
`required: ["tokens","players"]`. **Every array property carries `minItems` and `maxItems`**
(tandem 0.1.0, 2026-08-23):

| property | type | bounds |
|---|---|---|
| `tokens` | array of non-empty strings | `minItems: 5`, `maxItems: 5` |
| `players` | array of `{name}` objects | `minItems: 5`, `maxItems: 5` |
| `num_agents` | integer | `minimum: 5`, `maximum: 5` |
| `seed` | integer | — |
| `turns` | integer | `6..24`, default `12` |
| `noiseScale` | number | `0.0..2.0`, default `1.0` |
| `episodeTimeoutSeconds` | integer | `60..6000`, default `1200` |
| `turnDelayMs` | integer | `0..10000`, default `400` |
| `minTurnSpacingMs` | integer | `0..60000`, default `12000` |
| `model` | string | default `claude-sonnet-5` |
| `maxOutputTokens` | integer | `64..2000`, default `900` |
| `llmTimeoutSeconds` | integer | `5..300`, default `25` |
| `player_connect_timeout_seconds` | number | `minimum: 0`, default `180` |

**`game.results_schema`** — `additionalProperties: false`; required `names`, `scores`, `portfolio`,
`hold`, `cash`, `units`, `deals`, `misheard`, `voids`, `airtimeUsed`, `turns`, `maxTurns`, `reason`.
`names` / `scores` / `portfolio` / `hold` / `cash` / `units` / `deals` / `misheard` / `voids` /
`airtimeUsed` all `minItems: 5, maxItems: 5`; `scores` items `minimum: 0, maximum: 10`; `units`
items are arrays with `minItems: 4, maxItems: 4` of integers `≥ 0`; `turns` integer `≥ 0`;
`maxTurns` integer `≥ 6`; `reason` a string.

**`game.protocols`** — **both** keys:

- **`player`**: the full `garble.player.v1` text of §*Server, player, protocol* — every frame shape,
  the 4000-rune prompt cap, `scripted` + `baseline`, the redaction rationale, and "a Garble policy
  is a prompt: the player container's only job is to deliver it; field one by uploading this same
  image with `PLAYER_PROMPT` set to your strategy".
- **`global`**: the full `/global` snapshot shape, the commodity indexing (`0 ORE, 1 OAT, 2 TIN,
  3 TAR`), `channel: -1` = radio, the note that the `events` array is the complete append-only
  transcript including said text and notes, the note that **heard text is derived from the seed and
  never transported**, and the static-bundle note (`index.html?replay=<url>`).

**`game.docs`** — **both** keys:

- **`readme`**: one paragraph — five cogs, four commodities, a noisy radio and noisy lines, terms
  and confirms, the confirmed text binds, the redundancy shield, metered airtime, portfolio ratio at
  the horizon; how to field a policy (`PLAYER_PROMPT`); the two scripted baselines.
- **`pages`**: two entries.
  - `rules.md` — commodities and contracts, the numbered turn order, the **complete scanner spec**,
    the **complete neighbour table**, the admissibility rule with worked examples, the airtime
    meter, the caps, the observation split, the two `reason` values.
  - `scoring.md` — the portfolio and `hold` formulas, the sign, a worked mishearing
    (`SELL 5 ORE AT 12` confirmed as `SELL 50 ORE AT 1`: the seller loses 50 units and receives 50
    credits instead of 60 for 5), the statement that scores are ratios and are **not** zero-sum, and
    what the league ranks by.

**`player[]`** — three runnables, all `image: {{GARBLE_IMAGE}}`, `run: ["/bin/garble-player"]`,
`resources.requests {cpu: "100m", memory: "64Mi"}`, `resources.limits {cpu: "1"}`, `source_url` the
repo:

| id | name | env |
|---|---|---|
| `garble-player` | Garble Prompt Player | *(none — LLM; `PLAYER_PROMPT` is set at upload time)* |
| `garble-quoter` | Garble Quoter Baseline | `PLAYER_SCRIPTED: "quoter"` |
| `garble-shark` | Garble Shark Baseline | `PLAYER_SCRIPTED: "shark"` |

**`variants[]`** — every variant carries `players` ×5 **and `num_agents: 5`**, and every variant has
a `description`:

| id | description | `game_config` |
|---|---|---|
| `standard` | Five cogs, twelve turns, weather as it comes. | `players` ×5, **`num_agents`: 5**, `turns`: 12, `noiseScale`: 1.0, `turnDelayMs`: 400, `minTurnSpacingMs`: 12000, `player_connect_timeout_seconds`: 180 |
| `storm` | Half again the interference — protocol or perish. | `players` ×5, **`num_agents`: 5**, `turns`: 12, `noiseScale`: 1.5, `turnDelayMs`: 400, `minTurnSpacingMs`: 12000, `player_connect_timeout_seconds`: 180 |
| `long-session` | Eighteen turns — room to build a reputation. | `players` ×5, **`num_agents`: 5**, `turns`: 18, `noiseScale`: 1.0, `turnDelayMs`: 400, `minTurnSpacingMs`: 12000, `player_connect_timeout_seconds`: 180 |

`long-session` worst case: 18 × 50.4 ≈ 907 s, which exceeds the 720 s play budget, so a fully
LLM-driven `long-session` may legitimately end `deadline`. That is by design and is why `deadline`
is a declared, acceptable ending; the deadline check makes it a clean, scored, replayed episode
rather than a discarded one. The league runs `standard`.

**`certification`** —
`game_config`: `players` = `[{"name":"Sprocket"},{"name":"Gizmo"},{"name":"Ratchet"},
{"name":"Widget"},{"name":"Bolt"}]`, **`num_agents`: 5**, `seed`: 11, `turns`: **8**,
`noiseScale`: 1.0, `turnDelayMs`: 0, `minTurnSpacingMs`: 0,
`player_connect_timeout_seconds`: 180.
`certification.players` = `[{"player_id":"garble-player"}, {"player_id":"garble-quoter"},
{"player_id":"garble-player"}, {"player_id":"garble-shark"}, {"player_id":"garble-player"}]` — five
slots, and **every declared player runnable occupies at least one** (raid 0.1.2 → 0.1.3: a fixture
of `baseline × N` fails `players_missing` the moment the manifest declares other runnables).

`turns: 8` is chosen for the fixture so the smoke replay **outlasts the viewer soak window**: eight
turns produce `1 + 8*(1 + 5) + confirms/deals + 1 ≈ 70–85` events, and the game block's dwell times
(start 600 ms, `turn` 1200 ms, `say` 900 ms, `confirm` 700 ms, `deal` 1600 ms, `void` 900 ms, `end`
1500 ms) give **≥ 60 s** of playback against a 10 s soak (ecos, 2026-08-23).

### CI files

- `.github/workflows/ci.yml` and `.github/workflows/coworld-release.yml` from
  `coworld-builder/templates/`, substituting `<slug>` = **`garble`**, `<IMAGE>` =
  **`coworld-garble`**, **`<SEATS>` = `5`**. The `wasm-viewer` job's browser step gets
  **`--soak 10`** added to the pinned command.
- `tools/ci/docker_smoke.sh` from the template with the same substitutions, committed **`chmod +x`**,
  plus one appended assertion: **every player container's exit code must be 0**, not just the
  game's (raid 0.1.3 → 0.1.4; the template checks only `${prefix}-game`).
- `tools/ci/viewer_smoke.mjs` copied **verbatim**, no substitutions.
- `tools/ci/policies.json`:

  | name | run | env | owner |
  |---|---|---|---|
  | `garble-signal` | `/bin/garble-player` | `PLAYER_PROMPT` = a protocol-discipline strategy: read the meter, repeat every field above 50 %, spell round numbers, confirm honestly, price inside the premium band | champion #1 (daveey, the CI token's own player) |
  | `garble-shortwave` | `/bin/garble-player` | `PLAYER_PROMPT` = a **materially different** strategy: stay terse and fast in the quiet, prefer private lines for the real terms and use the radio only to bait, take the favourable neighbour whenever the counterparty was terse | champion #2, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` |
  | `garble-quoter` | `/bin/garble-player` | `PLAYER_SCRIPTED=quoter` | filler |
  | `garble-shark` | `/bin/garble-player` | `PLAYER_SCRIPTED=shark` | filler |

  Both champions are `PLAYER_PROMPT` policies and the two fillers are the scripted baselines — a
  scripted policy seated as a champion is a failure state. The two champion prompts differ
  materially: identical content dedupes to the same policy version.

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter by game shape | `cogame-babel` — turn-based, talk-driven, native rules, LLM-prompt policies, static wasm viewer (title paragraph). |
| Public `Metta-AI/cogame-garble` | Created public in phase 20; `source_url` points at it. |
| LLM policy **and** scripted baseline, day one, same image, env-switched | `garble-player` (`PLAYER_PROMPT`) vs `garble-quoter` / `garble-shark` (`PLAYER_SCRIPTED=…`), one image (§*Decisions*, §*Packaging*). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh` (§*Viewer*). |
| Real art, starter chrome verbatim | `chrome.css` unchanged plus one appended block, `chrome_common.js` byte-for-byte, `replay_broadcast.html` = babel's page with a block appended, sprites and floor from `data/` (§*Viewer*, §*Packaging*). |
| Two name spaces | Cog aliases in-game and in every prompt; `policyNames` + `makeNameMap` spectator-side; `results.names` are policy names (§*The game*). |
| Degrade, never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`; deadline checked before every turn; retry-once-then-scripted; 605 s worst case at `turns = 12` (§*Decisions*). |
| `num_agents` in every variant and the cert fixture | **5** in `standard`, `storm`, `long-session` and `certification.game_config`; `<SEATS>` = 5 in `docker_smoke.sh` as the independent cross-check. |
| Upload policies before `upload-coworld`; secret put after | The release workflow template's step order, unchanged. |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

### `tests/test_wire.nim` — the channel, in isolation

1. **Normalisation** — punctuation becomes separators, case folds, a 40-word line caps at 32 words,
   an empty line yields an empty word list, a multi-byte rune survives as one unrecognised word.
2. **Lexicon** — `wordValue` maps every digit string `0..99` and every spelled word in the table to
   the right integer; `isNumberWord` is false for `HUNDRED`, `TWENTY-FIVE` (post-normalisation two
   words) and `ORE`.
3. **Scanner** — `SELL 5 ORE AT 12` parses to `(SELL, 5, ORE, 12, k=1,1,1)`;
   `SELL 5 5 ORE ORE AT 12 12` gives `k = (2,2,2)`; `SELL 5 5 9 ORE AT 12` takes qty 5 with `k = 2`;
   a tie `SELL 5 9 ORE AT 12` takes the **last** (9) with `k = 1`; a price tie takes the **first**;
   missing verb, missing `AT`, missing number before `AT`, missing commodity, missing number after
   `AT`, and `qty = 0` each give **no terms**; a second `SELL` after the first is ignored.
4. **Neighbours** — `neighborsOf("5") == {"50","4","6"}`; `neighborsOf("50") == {"5","51","59"}`
   (append-0 is suppressed above 99); `neighborsOf("FIVE") == {"NINE"}`;
   `neighborsOf("ORE") == {"OAT"}`; `SELL`, `BUY`, `AT` and chatter have **none**; the spelled table is
   **symmetric and a matching** — every spelled word has 0 or 1 neighbours and `w ∈ N(x) ⇔
   x ∈ N(w)` — and the commodity table likewise (both asserted by iterating the whole lexicon).
5. **Garbling** — with `noise = 0.0` every word is `wfOk` and the heard text equals the said text;
   with `noise = 0.95` over 500 deliveries the drop rate is within ±0.05 of `0.45*n` and the swap
   rate within ±0.05 of `0.40*n`; every swapped word is a member of the said word's neighbour set;
   a word with no neighbours is never `wfSwap`; a burst blanks a contiguous run of `burstLen` words
   at the same positions for **every** recipient of that turn; the same
   `(seed, turn, from, to, noise)` reproduces the identical `seq[HeardWord]` and a different `to`
   produces a different one for at least one of 20 seeds.
6. **Admissibility** — equal fields are always admissible; with `k = 1`, `5 → 50` is admissible and
   `5 → 93` is not; with `k = 2`, `5 → 50` is **not** admissible; a spelled `FIVE` admits only `9`;
   `side` never admits a change; the function is total over 1 000 random `(said, asserted)` pairs
   and never raises.

### `tests/test_sim.nim` — sim unit tests

1. **Seeded setup** — for seeds `[0,1,11,42,1234]`: five aliases, all distinct;
   `sur[s] != dem[s]` for every seat; all four commodities appear as somebody's surplus; every
   `price[t][c] ∈ 3..30` and every step is in `{-1,0,1}`; `premium ∈ 6..9`, `quota ∈ 12..19`;
   `interference[t] ∈ [0.05, 0.95]` and the base curve has at least one local maximum and one local
   minimum over 12 turns (it swells *and* fades); the same seed reproduces everything and a
   different seed differs. `noiseScale = 2.0` clamps at `0.95`, `noiseScale = 0.0` pins `0.05`.
2. **Seat count** — `initSim` raises `GarbleError` for 4 and for 6 players and succeeds for 5.
3. **Airtime** — a 160-rune text costs 160; a 300-rune text truncates to 160 **runes** (checked with
   `"音"` ×300) and costs 160; with 30 left, a 100-rune text is clipped to 30 runes on a rune
   boundary and the event is flagged `clipped`; at 0 the transmission is `silent` and no ticket
   opens; a confirm always costs 40 and floors the meter at 0, never below, and is never blocked.
4. **Tickets** — a parsing say opens exactly one ticket with a fresh id; a non-parsing say opens
   none; a ticket is not confirmable on its own turn, is confirmable on the next two, and expires at
   the open of the third; a radio ticket is confirmable by any non-offerer; a line ticket only by
   the addressee (`not-addressed` otherwise); the offerer confirming its own ticket gives
   `own-ticket`; two confirms of one ticket in one turn give one `deal` then one
   `already-settled` `void`, in seat order.
5. **Settlement** — a clean confirm moves goods and cash exactly; a `BUY` ticket reverses the roles;
   an over-quantity confirm partial-fills to the seller's units with `partial: true`; a buyer with
   too little cash fills to `cash div price` and `fill == 0` gives `uncovered`; `price = 0` skips
   the cash constraint; units and cash are **never negative** over 500 random confirm sequences;
   the `deal` event carries both the said and the confirmed terms and `misheard` is true exactly
   when they differ.
6. **The shield end to end** — the idea's headline case: seat 0 says `SELL 5 ORE AT 12`
   (`k = 1,1,1`), seat 1 confirms `SELL 50 ORE AT 1`, the deal settles for 20 units (the seller's
   whole holding) at 1 with `misheard: true` and `partial: true`; the same offer written
   `SELL 5 5 ORE ORE AT 12 12` makes the same confirm a `void` with reason `inadmissible`.
7. **Scoring** — `score = portfolio / hold` exactly; a seat that never trades scores exactly `1.0`
   at any price path; buying its demand commodity below `price + premium` raises the score above
   1.0; selling its demand commodity below price lowers it; `hold ≥ 180` for every seed;
   `portfolio ≥ 0` always; premium is credited only up to `quota`.
8. **Legality** — `applySay` / `applyConfirm` raise `GarbleError` **and leave the sim unchanged**
   for: a second say from one seat in a turn, a confirm before every say of the turn has landed,
   `qty = 100`, `price = -1`, an unknown commodity index, and any call after `done`. An
   inadmissible or uncovered confirm does **not** raise.
9. **Rune truncation** — a 400-rune multi-byte `text` truncates to ≤ 160 **runes**; a 900-rune
   `notes` to ≤ 400; the resulting event JSON round-trips and its bytes decode as **strict UTF-8**.
10. **Replay derivation** — `replayMatch(config, events).len == events.len + 1`; the final frame
    equals the live sim's `tableStateJson`; `eventFromJson(eventToJson(e)) == e` for one event of
    every one of the seven kinds; a **tampered** `deal` event (fill moved by 1, or a price changed)
    raises `GarbleError`; a tampered `turn` event (interference or a price changed) raises; a
    `deadline` `end` event settles the replayed sim; the heard words re-derived in the replay are
    identical to the live ones for every delivery of a 12-turn episode.
11. **Endings** — a full run gives `reason == "complete"` and `turnsPlayed == turns`; `endEarly()`
    mid-episode gives `reason == "deadline"`, scores on `turnsPlayed` turns at the last opened
    turn's prices, `done == true`, and a second `endEarly()` is a no-op; `reason` is always one of
    exactly `{"complete","deadline"}`.
12. **Results shape** — five names / scores / portfolio / hold / cash / units / deals / misheard /
    voids / airtimeUsed; `units[i].len == 4`; `turns ≤ maxTurns`; `airtimeUsed[i] ≤ 900`.
13. **Name spaces** — for every seat, `systemPrompt` and `userPrompt` contain that seat's alias and
    contain **none** of the five policy display names; the observation never contains another
    seat's said text, cash, contract or notes (asserted by substring search against the other
    seats' private strings); `tableNames` is deterministic in the seed.

### `tests/test_bot.nim` — bounded-orders / legality on the scripted baselines

1. **Legality and boundedness** — for seeds `[1,11,42,1234]` × every mix of `quoter` and `shark` in
   all five seats, a full scripted episode completes with `reason == "complete"`: nothing raises,
   every transmitted text is ≤ 160 runes and ≤ 32 words, every asserted `qty` and `price` is in
   `0..99`, every asserted commodity is a real index, airtime never goes negative and never exceeds
   900 used, no baseline ever writes notes, and the whole episode runs in **< 2000 ms**.
2. **The game actually happens** — an all-`quoter` table over 50 seeds settles **≥ 1 deal per
   episode** in every seed and **≥ 3 on the median seed** (without this the smoke replay has no
   `deal` beats and CI would go green on a game where nobody trades).
3. **The shield is load-bearing** — over 200 seeds a `shark`-heavy table (3 sharks, 2 quoters)
   produces **more** `misheard` deals than an all-`quoter` table, and the mean `quoter` score in the
   quiet-band (`noiseScale = 0.5`) run **exceeds** its mean score at `noiseScale = 1.5`, with both
   means echoed to the log so a tuning drift is visible.
4. **Fallback path** — with no credentials, `newLlmClient(config).disabled` is true and `decideAll`
   returns scripted decisions for all five seats **with no network call**; every returned decision
   is legal.
5. **Reply parsing** — `parseDecision` accepts a missing `confirm`, a `null` confirm, integer /
   numeric-string / float / spelled-word `qty` and `price`, lower-case `side` and `commodity`, an
   unknown `channel` (normalised to `radio`), this seat's own alias as `channel` (normalised to
   `radio`), and trailing prose after `}`; it **rejects** `qty = 100`, `price = -1`, a missing
   `ticket`, an unknown commodity, and a non-object `confirm`; `text`, `notes` and `channel` are
   capped at their rune limits.

### End-to-end, replay and viewer (CI jobs)

6. **`docker-smoke`** (`tools/ci/docker_smoke.sh`, `SMOKE_SEATS = 5`) — builds the production image
   and runs **one real episode** in raw docker with the certification fixture's five-seat mix and no
   `ANTHROPIC_API_KEY`, asserting the game container exits 0 having written `results.json` and a
   replay, that **every player container also exits 0**, that `num_agents` = 5 agrees across
   `certification.game_config`, `len(certification.players)`, `len(game_config.players)` and
   `SMOKE_SEATS`, and that `results.names` / `results.scores` have 5 entries. The replay is copied
   to `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.
7. **Strict-UTF-8 replay parse** — the same script decodes the replay bytes as UTF-8 and parses them
   as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`, the default). Sim test 9 covers the multi-byte truncation
   path that would otherwise break it.
8. **Viewer smoke — the bundle is EXECUTED, not merely built.** `ci.yml`'s **`wasm-viewer`** job
   (`needs: docker-smoke`) builds the bundle with `tools/build_replay_viewer.sh`, downloads the
   `smoke-replay` artifact, and runs
   `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
   dist/smoke/replay.json --timeout 90 --soak 10` in headless chromium (Playwright pinned 1.55.0).
   It passes only when the page sets `data-replay-loaded="true"` (or posts the `coworld-replay`
   `ready` envelope), **never** sets `data-replay-error`, keeps advancing through the uninterrupted
   10 s soak, and shows differing `#clock` / `#scorebug` readouts at the 0 % / 50 % / 100 % scrub
   positions. `viewer-smoke.png` and `viewer-smoke.json` are uploaded on success and on failure
   alike.
9. **Chrome scope-duplication check** — a step in the `wasm-viewer` job asserts that no identifier
   exported by `window.GarbleChrome` is re-declared as a top-level `function` or `var` in
   `client/renderer.js`, and that `client/chrome.css` is byte-identical to
   `cogame-babel/client/chrome.css` outside the single appended `garble additions` block (tandem,
   2026-08-23: a hoisted game-block `markBeat` silently shadowed the chrome alias and every static
   grep stayed green).

---

## Out of scope (v1)

- Any seat count other than five, any commodity count other than four, and any commodity other than
  ORE / OAT / TIN / TAR.
- Compound spelled numbers (`TWENTY FIVE`), negative prices, fractional prices or quantities, and
  quantities or prices above 99.
- Short selling, borrowing, margin, credit, futures, options, escrow, and any deal that settles on a
  later turn than the confirm.
- Multi-leg deals (two commodities in one ticket), package deals, and auctions.
- Amending, cancelling, vetoing or repudiating a ticket after it is confirmed. The confirm binds;
  the offerer's only defence is the redundancy shield.
- Per-seat noise profiles, seat-chosen transmit power, error-correcting codes supplied by the
  engine, and any channel the game provides that is not noisy (the exchange's ticket board is
  reliable *by design* and carries no terms).
- Cross-episode memory, standing reputations, and any out-of-band signalling between policies.
- Speech audio, voice synthesis, or any audio asset file — v1 synthesises static in WebAudio, in
  bundle, behind a button.
- Live-server replay pods, `#viewpanel` zoom chrome, and a minimap.
