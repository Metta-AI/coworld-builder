# Cogmud: six cogs loose in a town, and every move is a sentence

Six cogs share one nine-room town for fourteen turns. There is no action menu anywhere in the
stack: a seat's whole output is **one sentence of plain English**, which the server parses with a
bounded intent grammar into exactly one of thirteen intents — go, take, drop, buy, sell, hand over,
offer, accept, hire, rob, ask, speak, wait. Five shopkeepers hold stock whose prices move with it,
Guildmaster Vell posts two private commissions per seat that pay **partial credit per unit
delivered**, robbery works only in the two dark rooms and only against a cog without a bodyguard,
and hiring is the one promise the rules actually enforce. Score is wealth plus commission points at
the horizon. Everything else — alliances, price-fixing, protection rackets, honest freight — is
emergent, and is the point.

Built on `Metta-AI/cogame-bullwhip` (mounted read-only at `/workspace/starters/cogame-bullwhip`),
the newest parley-lineage template: a Nim game server implementing the Coworld runtime contract, a
pure `sim` module shared by server / tests / wasm viewer, LLM decisions where **a policy is just a
prompt**, always-available scripted baselines, **one parallel LLM batch per simultaneous turn**, and
the parley broadcast chrome around a canvas stage. Bullwhip is the starter because Cogmud has
bullwhip's shape exactly — a turn-based, hidden-information, simultaneous-decision, mixed-motive
*economic* game whose seats answer with a small JSON payload of free text, whose watchability is a
stage + scorebug + feed rather than a physics loop, and whose per-turn cost is one batched LLM round
trip. Bullwhip is also the only starter whose `decideAll` already fires one parallel batch per turn,
which is the whole timing model here, and the only one whose `tableStateJson` → `replayMatch` →
wasm pipeline already re-derives every spectator frame from the seed plus the recorded decisions.
The starter is `Metta-AI/cogame-bullwhip` and **every convention there holds here unless this note
says otherwise.**

Source idea, verbatim:

> 19 Cogmud — a text world with NPC economies, and actions are sentences
>
> A MUD: rooms, items, NPC shopkeepers with stock and prices, quests with partial credit. Agents act
> in free-form natural language parsed by the server; six seats share the world and can trade, hire,
> rob, or team up. Score is wealth plus quest points at the horizon. No action menu at all.
>
> Seats: 6
> Motive: open-ended mixed
> Policy interface: LLM prompt
> Fills gap: free-form NL action space / emergent economy / open-ended
> Integrity (anti-collusion): Alliances and price-fixing are emergent economy, i.e. the point;
> anonymous aliases and one seat per account keep it strangers-only.
>
> Replay plan (watchability): A parchment map auto-drawn from the room graph, agent tokens walking
> it; a chronicle panel scrolls the best action sentences while trades, thefts and hires fire icon
> FX on the map. The highlight reel is chosen by event salience, not tick order.

*Coordinator rails, not revisited: seat count is **6**; every seat is LLM-prompted with a scripted
baseline fallback, one image, env-switched (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<name>`), per the
stack pins in `playbooks/make-coworld.md` §Phase 0. There is no `OPEN` item in this note: every
reading the idea left loose (parser scope, who issues commissions, the score weights, the turn
horizon) is a rail — parameter tuning, scoring when the idea pins the shape, and viewer composition
— and each is decided below with its reason.*

---

## The game

### Seats

- **Seats: exactly 6.** `num_agents` = **6** everywhere — both manifest variants, the certification
  fixture, and `<SEATS>` in `tools/ci/docker_smoke.sh`.
- **All six seats are symmetric.** There are no roles. What differs between seats is drawn from the
  seed: the **starting room** and the **two commissions**. A policy therefore cannot be
  advantaged by its slot number, and there is no role lottery to normalise away.
- Seats play under **anonymous cog aliases** drawn from the seed by `tableNames()` — bullwhip's
  function and its `CogNames` list kept verbatim (10 names, 6 needed). Policy names are
  spectator-side only — see *Two name spaces*.
- Seats are referred to in prompts, sentences, the feed and the scorebug **only by alias**
  (`Sprocket`, `Gizmo`, …). A seat addresses another seat by writing its alias in a sentence.

### The town (what exists, as data)

The world is **authored, not random**: a compile-time constant `WorldSpec` in `src/cogmud/world.nim`,
identical in the server, the tests and the wasm viewer. Only four things are drawn from the seed, at
`initSim`, from one rng stream in this fixed order — **starting rooms, commission items, ground
items** (aliases come from `tableNames`'s own stream, keyed as bullwhip keys it). A replay therefore
re-derives the whole episode from the seed plus the recorded `act` events.

**Nine rooms.** `x`/`y` are parchment-map coordinates on a 0..100 grid (the viewer draws the map from
these; no layout algorithm anywhere). `dark` rooms are the only rooms where robbery can succeed.

| id | name | keywords | x | y | dark | exits |
|---|---|---|---|---|---|---|
| 0 | Market Square | market, square, well, plaza | 50 | 50 | no | 1, 3, 5, 7 |
| 1 | The Copper Kettle | kettle, tavern, inn, copper | 22 | 26 | no | 0, 2, 8 |
| 2 | Tanner's Row | tanner, tannery, row, tanners | 50 | 14 | no | 1, 3 |
| 3 | The Smithy | smithy, smith, forge, anvil | 78 | 26 | no | 0, 2, 4 |
| 4 | Warehouse Yard | warehouse, yard, store, stores | 88 | 52 | no | 3, 5 |
| 5 | The Docks | docks, dock, quay, harbour, harbor, wharf | 78 | 78 | **yes** | 0, 4, 6 |
| 6 | Cutpurse Alley | alley, cutpurse, backstreet, lane | 50 | 90 | **yes** | 5, 7 |
| 7 | The Chapel | chapel, church, shrine | 22 | 78 | no | 0, 6, 8 |
| 8 | The Guildhall | guildhall, guild, hall, board | 12 | 52 | no | 1, 7 |

Exits are **symmetric and complete** (a wheel: ring 1–2–3–4–5–6–7–8–1 plus spokes 0–1, 0–3, 0–5,
0–7). Every room is within **2** moves of Market Square; the graph diameter is **4**. Both facts are
asserted by `tests/test_sim.nim` item 1, not assumed.

**Six item kinds.** `BaseValue` is the fixed reference valuation used by scoring — it never moves
with the market, so a seat's score never depends on which shop it happens to stand next to.

| id | name | keywords | BaseValue |
|---|---|---|---|
| 0 | hide | hide, hides, skin, skins, leather | 6 |
| 1 | nails | nails, nail, iron | 7 |
| 2 | rope | rope, ropes, coil, cord | 8 |
| 3 | salt | salt, salts, brine | 9 |
| 4 | lamp | lamp, lamps, lantern, oil | 11 |
| 5 | relic | relic, relics, idol, icon | 14 |

**Five shopkeepers (NPCs).** Each stands in one room forever, deals only in the items on its trade
list (it will not buy anything else), and starts with **120 coin**.

| id | name | keywords | room | trade list → initial stock |
|---|---|---|---|---|
| 0 | Tanner Oda | tanner, oda | 2 Tanner's Row | hide 8, salt 5 |
| 1 | Smith Bram | smith, bram, blacksmith | 3 The Smithy | nails 8, rope 6 |
| 2 | Keeper Nesh | keeper, nesh, innkeeper | 1 The Copper Kettle | lamp 4, salt 6, rope 4 |
| 3 | Dockmaster Fen | dockmaster, fen, dockmaster | 5 The Docks | relic 3, hide 5, nails 6 |
| 4 | Guildmaster Vell | guildmaster, vell, guildmistress | 8 The Guildhall | rope 4, lamp 3 |

**Prices move with stock**, per NPC per item, integer arithmetic only:

```
ask(n, k)  = clamp(BaseValue[k] + PriceStep(1) * (RefStock(6) - stock(n, k)),
                   max(2, BaseValue[k] div 2), BaseValue[k] * 3)
bid(n, k)  = max(1, ask(n, k) * 2 div 3)
```

At stock 6 an item sells at exactly its base value; at stock 0 it costs base + 6 (capped at 3×
base); at stock 12 it costs base − 6 (floored at half base, min 2). The bid is two thirds of the
ask: the spread is the shopkeeper's living. **Each unit in a multi-unit purchase is priced from the
stock at the moment that unit changes hands** — buying two hides from a shop holding 8 costs
`ask@8 + ask@7`. That is the whole supply curve, and it is why cornering a shop's stock is a real
strategy.

**Restock.** At each turn's open, every NPC adds **+1** to exactly one item on its trade list —
index `turn mod tradeList.len` — up to `StockCap = 12`. Supply is slow, finite and predictable.

**Commissions (the quests).** Guildmaster Vell at the Guildhall posts and settles **every**
commission in the game. Each seat holds exactly **two**, private to it, drawn at `initSim`: shuffle
`[hide, nails, rope, salt]` with the episode rng and take the first two (distinct items), each with
`count = 2`. Commission items are never `lamp` or `relic` — those are pure trade goods.

*Judgment call, logged.* The idea says "NPC shopkeepers … quests with partial credit" without
saying who issues them. Concentrating every commission on one NPC in one room is what makes the
horizon feasible (§Feasibility oracle) and it gives the map a centre of gravity: the Guildhall is
where everyone must eventually go, which is where deals, hires and ambush plans happen.

**Ground items.** At `initSim`, rooms 0, 4, 5, 6 and 7 each receive exactly one item drawn
`rng.rand(5)` in ascending room order, and room 4 (Warehouse Yard) receives one additional `relic`.
Six items lie loose in the town at turn 0.

**Starting state per seat:** `coin = 40`, empty inventory, starting room = the seat's entry in a
seeded shuffle of all nine room ids truncated to six (so all six starting rooms are **distinct**),
`retainerOf = -1`, `retainerTurns = 0`, both commissions at `delivered = 0`.

**Carry limit:** `CarryLimit = 8` items total. A take, buy, accepted trade or gift that would exceed
it fails with reason `carry_limit`; a partial fill takes what fits.

### Turns, and the exact resolution order

An episode is `turns` turns (default **14**, min 6, max 40, fitted to the clock by `sampleEpisode` —
see *Episode budget*). Decisions inside a turn are **simultaneous**: all six sentences go out in one
parallel batch and nothing a seat writes in turn `t` is visible to any other seat before turn
`t + 1`.

**Initiative** is a deterministic rotation, no rng: on turn `t`, the seats resolve in the order
`seat = (k + t) mod 6` for `k = 0 .. 5`. Every seat stands at the front of the shop queue exactly
`turns / 6` times, and nothing depends on slot number. Where two seats contend for the same stock,
the same ground item, the same offer or the same victim, **the earlier initiative wins**, and the
loser's action resolves against what is left (or fails with a named reason).

For turn `t` (0-based), in this exact order:

1. **Open the turn.** `phase = "turn"`.
   - Offers posted on turn `t − 2` or earlier **expire** (an offer lives exactly one turn: posted on
     `t`, acceptable only on `t + 1`).
   - Every seat with `retainerTurns > 0` decrements it; at 0, `retainerOf = -1`.
   - Every NPC restocks one item (above).
   - Last turn's public room events move into `heardEvents` — that is what each seat reads this turn
     as *what happened here*.
   - A **`turn` event** is appended carrying `turn`, the nine `RoomState`s (ground item counts), the
     five `NpcState`s (stock and coin) and the six `CogState`s (room, coin, inventory, commission
     progress, retainer, score).
2. **Deadline check** — *before* the batch, never mid-turn. If `epochTime() > playDeadline`, jump to
   step 8 with `reason = "deadline"`.
3. **Rate floor.** If the LLM client is enabled and the previous batch started less than
   `MinBatchSpacingMs = 12_000` ago, sleep the difference. Six live seats at one request each is 30
   requests/minute exactly at a 12 s floor, which is the hosted Bedrock sidecar's per-episode cap
   (raid, 2026-08-23). When the client is **disabled** (no credentials: `docker-smoke`, offline
   certification) no requests are made and this sleep is skipped entirely.
4. **Collect.** `pendingSeats(sim)` = all six seats, in seat order. The server snapshots the sim,
   builds each seat's prompt, and fires **one parallel batch of six** (`curly.makeRequests`). Replies
   that fail to parse as JSON are retried once in a smaller batch carrying a hint; anything still
   failing falls back to the scripted baseline (§Decisions). **A sentence that parses as JSON but
   whose prose the grammar cannot read is NOT a failure** — it is a legal no-op with a recorded
   reason, and is never retried (the seat said something; the town did not understand it).
5. **Parse.** Every seat's `action` string is run through `parseSentence` (§Sim module) — a pure
   function of the sentence and the sim — producing one `Intent` with its slots, or `iNone` with a
   reason. No state changes in this step.
6. **Resolve**, in this class order; within each class, in initiative order; each sub-step appends
   its own `act` event as it resolves, so **the event log order is the resolution order**:
   1. **Speech.** Every seat's `say` field, and the text of every `iSay` action, is posted to the
      seat's **start-of-turn** room. Everyone in that room reads it next turn.
   2. **Shop.** `iBuy`, `iSell`, `iGive`-to-an-NPC, `iQuest`. Stock and NPC coin are consumed
      first-come: the earlier initiative gets the cheap units.
   3. **Ground.** `iTake`, `iDrop`. A contested item goes to the earlier initiative; the loser gets
      `no_such_item`.
   4. **Cog to cog.** `iGive`-to-a-cog, `iTrade` (post an offer), `iAccept` (consume one), `iHire`
      (post an offer). An offer can be accepted only by the seat it names, only on the turn after it
      was posted, and only while both seats are in the same start-of-turn room. The first `iAccept`
      consumes it; a second gets `no_such_offer`.
   5. **Robbery.** Every `iRob`, in initiative order, against **start-of-turn** positions —
      *you cannot dodge an ambush by walking away*. Strengths are recomputed before each individual
      robbery, so an earlier theft in the same turn changes what a later one finds.
   6. **Movement.** Every `iMove`, in initiative order. A move to an adjacent room always succeeds;
      there is no room capacity.
7. **Book-keeping.** Wealth and score are **derived from state**, never accumulated; commission
   points accumulate on delivery. `turnsPlayed += 1`; `turn += 1`. If `turnsPlayed < turns`, go to
   step 1. Otherwise append one final **`turn` event** (the closing world snapshot, `turn =
   turnsPlayed`, so the viewer's last frame shows the settled town) and go to step 8 with
   `reason = "complete"`.
8. **Settle.** `done = true`, `phase = "done"`, an **`end` event** with `turn = turnsPlayed` and
   `text = reason`. Scores are computed as below; the server writes `results.json` and the replay.

**Pacing** is `turnDelayMs` (default 400, certification 0) between turns, capped across the episode
by `PacingBudgetMs = 20_000`, exactly as bullwhip caps it. It is *on top of* the rate floor in
step 3, not instead of it.

### The thirteen intents, and exactly what each does

`iMove`, `iTake`, `iDrop`, `iBuy`, `iSell`, `iGive`, `iTrade`, `iAccept`, `iHire`, `iRob`, `iSay`,
`iQuest`, `iWait`, plus `iNone` (the no-op the parser emits when it cannot read the sentence).

| intent | slots | rule |
|---|---|---|
| `iMove` | room | The room must be an exit of the seat's current room, else `no_such_exit`. Resolves in class 6. |
| `iTake` | item, qty (default 1, `all` = every unit present) | The item must be lying in the room; `min(qty, present, CarryLimit − carried)` units move to the seat. 0 units ⇒ `no_such_item` or `carry_limit`. |
| `iDrop` | item, qty | `min(qty, held)` units move to the room floor. 0 ⇒ `not_carrying`. |
| `iBuy` | npc (default: the NPC in the room), item, qty | The NPC must be in the room (`no_npc_here`) and deal in the item (`out_of_stock`). Fill `q = min(qty, stock, CarryLimit − carried)`, then walk the units one at a time paying `ask` from the current stock until the seat's coin runs out. `q = 0` ⇒ `out_of_stock` / `cannot_afford` / `carry_limit`. Coin moves to the NPC. |
| `iSell` | npc, item, qty | NPC must be present and deal in the item (`not_wanted`). Fill `q = min(qty, held)`, units priced one at a time at the rising `bid` as stock grows, stopping when the NPC's coin runs out (`npc_broke` at `q = 0`). |
| `iGive` | target (cog **or** NPC), item, qty **or** coin | To a **cog** in the room: an unconditional transfer of items and/or coin, no consent needed. To an **NPC**: the goods enter its stock, and **if the NPC is Guildmaster Vell and the item matches one of the giver's open commissions, it is credited as a delivery** (partial credit, see scoring); otherwise `no_matching_commission` and the goods are gone. One rule, no ambiguity: *handing goods to a shopkeeper is how a commission is filled.* |
| `iTrade` | other cog, item, qty, coin | Posts an offer `"<qty> × <item> for <coin> coin"` addressed to that cog, valid on the next turn only, while both are in the same room. The goods and coin are **not** escrowed; the trade executes at acceptance and fails (`offer_expired`) if either side can no longer pay or deliver. |
| `iAccept` | other cog (the offerer; defaults to the sole open offer if exactly one is addressed to the seat) | Consumes a live offer of either kind. A **trade** offer moves the goods and the coin atomically. A **hire** offer moves the fee and sets `retainerOf = employer`, `retainerTurns = RetainerTurns(3)`. Ambiguous with two open offers and no name ⇒ `no_such_offer`. |
| `iHire` | other cog, coin | Posts a hire offer for `coin` (1 .. the seat's coin). |
| `iRob` | other cog | See below. Self-target ⇒ `self_target`; a retainer robbing its own employer ⇒ `bound_by_contract`; the `honest-town` variant ⇒ `thievery_forbidden`. |
| `iSay` | text | The sentence itself is spoken in the room (identical effect to the `say` field). |
| `iQuest` | npc (must be present) | The seat's next observation gains a **commission hint**: for each open commission, the shop with the cheapest current `ask` for that item, its room, and that ask. Costs the turn; buys information. Not at an NPC ⇒ `no_npc_here`. |
| `iWait` | — | A legal no-op, reason `waited`. |
| `iNone` | — | The parser could not read a sentence. Legal no-op with a reason naming what was missing (`unparsed`, `no_verb`, `no_target`, `ambiguous_target`, …). **The seat is told the reason in its next observation** — that is how a policy learns the grammar, and it is why no menu is needed. |

**Robbery, deterministically.** Let `retainersPresent(x)` = the number of seats whose `retainerOf ==
x`, whose `retainerTurns > 0`, and whose start-of-turn room is the robbery's room.

```
A = 1 + retainersPresent(robber) + (1 if the room is dark else 0)
D = 1 + retainersPresent(victim) + (0 if the room is dark else 2)   # the town watch
robbery succeeds iff A > D
```

- **Lit room, no hirelings:** `A = 1`, `D = 3` — the watch always stops you. Robbery is *only*
  possible in **The Docks** and **Cutpurse Alley**.
- **Dark room, no hirelings:** `A = 2`, `D = 1` — succeeds.
- **Dark room, the victim has one hireling standing with it:** `A = 2`, `D = 2` — fails. A bodyguard
  is worth exactly one mugging.
- **Dark room, both sides have one hireling:** `A = 3`, `D = 2` — succeeds. Bringing muscle beats
  hiring muscle, so protection is a market, not a shield.

On **success** the robber takes **one item** — the victim's highest `BaseValue` item, ties broken by
lowest item id — or, if the victim carries nothing, `min(victimCoin, RobCoin = 10)` coin; if the
victim has neither, `nothing_to_take`. On **failure** the robber pays `min(robberCoin, FineCoin = 8)`
coin to the victim. Either way the attempt is **public in the room**: everyone present reads it next
turn, and the map flashes.

### Scoring, its sign, and what the league ranks by

Computed at step 8, from state. **Higher is better.** Nothing is accumulated except commission
deliveries.

```
wealth(seat)       = coin + Σ_k BaseValue[k] * held(seat, k)
questPoints(seat)  = Σ_{q in the seat's 2 commissions}
                       ( PointsPerUnit(4) * q.delivered
                         + (CompletionBonus(8) if q.delivered >= q.count else 0) )
score(seat)        = ( wealth(seat) + PointValue(3) * questPoints(seat) - StartCoin(40) )
                     / ScoreScale(40.0)
```

- **`results.scores[seat]` is the single number the league ranks by**, and the ladder ranks seats by
  **mean episode score**. There is exactly one ladder statistic.
- **A seat that does nothing scores exactly `0.0`** (40 coin, no goods, no points). A seat that is
  robbed blind or buys badly scores **negative**. The sign is unambiguous.
- Every point is worth **3 score-units of wealth**, i.e. a delivered unit is worth **12** wealth
  against an item that costs 6–9 — delivering is profitable but not free, and a completed commission
  pays a further **24**.

*Worked landmark, derivable from the tables above.* A competent seat starting at the Chapel:
buys 2 hides from Tanner Oda at stock 8 (`ask@8 = 6 − 2 = 4`… clamped to `max(2, 3) = 4`? no:
`6 + 1*(6 − 8) = 4`, floor is `max(2, 3) = 3`, so 4) and at stock 7 (`ask@7 = 5`) = **−9 coin**;
buys 2 rope from Smith Bram at stock 6 and 5 (`8` and `9`) = **−17 coin**; walks to the Guildhall
and hands over both pairs = `2 × (4×2 + 8) = 32` points; sells a `relic` it lifted from the
Warehouse Yard to Dockmaster Fen at stock 3 (`bid = (14 + 3) × 2 div 3 = 11`) = **+11 coin**.
Coin = `40 − 9 − 17 + 11 = 25`; wealth 25; `score = (25 + 3×32 − 40) / 40 = 81/40 = ` **2.03**.
A pure trader who never touches a commission but works the spread for +40 coin over 14 turns scores
**1.00**. A seat mugged twice in the Alley for a lamp and a relic scores about **−0.6**.
Commissions beat trade, trade funds commissions, and theft moves real score between seats — which is
the balance the idea asks for.

*Judgment call, logged.* The idea says "wealth plus quest points" without an exchange rate.
`PointValue = 3` and `ScoreScale = 40` are chosen so (a) doing nothing is exactly zero, (b) two
completed commissions and a break-even purse land near +2, (c) a good trading run lands near +1, and
(d) a single successful robbery of a relic swings both seats by ±0.35 — visible on a leaderboard
without dominating it. **Any change to these constants re-runs `tests/test_score.nim` and
`tests/test_feasibility.nim`; those tests are the enforcement, not this paragraph.**

Results also report each seat's `coin`, `wealth`, `questPoints`, `delivered`, `robberies` (successful
thefts committed) and `robbed` (times victimised), so the league page can show what happened.

### Feasibility oracle (computed here, enforced by a test)

Both commissions must be completable inside the horizon by a competent seat, or partial credit is
the only credit anyone ever sees. BFS distances on the room graph above:
`d(8,2) = 2` (8‑1‑2), `d(8,3) = 3`, `d(2,3) = 1`, `d(8,1) = 1`, `d(8,5) = 3`, and every room is
within 4 of every other.

Worst case: commissions for `hide` (stocked at rooms 2 and 5) and `nails` (rooms 3 and 5), starting
at The Docks (5). Best plan: 5→0→1→2 (**3 moves**), buy 2 hide (**1**), 2→3 (**1**), buy 2 nails
(**1**), 3→0→7→8 or 3→2→1→8 (**3 moves**), hand over hide (**1**), hand over nails (**1**) =
**11 turns**, against a 14-turn horizon — **3 turns of slack**. Cost: `4+5+7+8 = 24` coin of the
starting 40. Every other item pair and starting room is cheaper. `tests/test_feasibility.nim`
asserts, over 200 seeds × 6 seats, that this greedy plan length is **≤ turns − 2** and its cost is
**≤ StartCoin**, and it fails the build if a constant change breaks either.

### End conditions and the legal `results.reason` values

Exactly two, both scored, both producing a full result:

- **`"complete"`** — all `turns` turns resolved. The expected value, and the one phase 60 should see.
- **`"deadline"`** — the play deadline (60 % of `episodeTimeoutSeconds`) was reached at step 2, so
  `endEarly()` settled the episode **between turns**. Scores are computed from the state as it
  stands; because score is derived from wealth and deliveries rather than averaged per turn, a short
  honest episode is on the same scale as a full one (a seat that has delivered nothing yet simply
  scores near 0). Artifacts are still written. A short honest episode always beats a long one that
  never lands.

**No other value exists.** There is no bankruptcy (coin can never go negative — a seat with 0 coin
just cannot buy), no elimination, no walkout: a seat that never connects plays with an empty
operator prompt, and a seat whose decision fails plays the scripted baseline.

### Per-seat observation — exactly what is visible and what is hidden

Nobody ever sees the seed. Nobody sees another seat's `notes`. Nobody sees any score but its own.

**A seat sees** (`playerStateJson` for that seat, and the same content rendered in its prompt):

- the turn number and how many turns remain; its own alias;
- **its purse and pack**: `coin`, every item held with its count and `BaseValue`, and how many of the
  8 carry slots are free;
- **its commission book**: for each of its two commissions — the item, the count, `delivered` so
  far, the points already banked and the points outstanding, and that Guildmaster Vell settles them
  at the Guildhall;
- **the room it is standing in**: the name, its one-line description, **the exits named by
  destination room name**, the items lying on the floor with counts, the aliases of every other cog
  present, and the NPC present if any — with its **full trade list: item, stock, ask, bid, and the
  NPC's remaining coin**;
- **what happened here last turn**: every public act in this room, in resolution order, as one line
  each (`Gizmo bought 2 hides from Tanner Oda for 9 coin.`, `Bolt tried to rob Ratchet and the watch
  stopped him.`), plus every line spoken here, attributed by alias. Capped at **12 lines of ≤ 200
  runes**, newest last;
- **offers open to it**: who offered, what, for how much, and that it expires at the end of this
  turn;
- its **retainer status**: who it is bound to or who is bound to it, and for how many more turns;
- **the town map**, which is public knowledge in any MUD: every room's name, its exits, and which
  NPC keeps shop there — but **not** those NPCs' stock or prices;
- **the outcome of its own last sentence**, verbatim reason (`Your last sentence was not understood:
  there is no exit called "north" from The Chapel.`);
- its own private `notes`, fed back verbatim;
- the **phrasebook** — twelve example sentences (§Decisions). Examples, never a legal-move list.

**A seat never sees:** any other seat's coin, inventory, commissions, notes or score; anything at all
happening in another room; the stock or prices of any NPC it is not standing next to; the seed; the
ground items in rooms it is not in; another seat's raw sentence except through the public act lines
and speech of its own room.

*The asymmetry in one line: every cog knows the map and nobody knows the town.* Information is
strictly local, which is exactly what makes speech, the `iQuest` hint and a hired pair of eyes worth
a turn.

*The escrow tension, resolved deliberately.* The escrow learning (2026-08-23) says a formal-output
game must precompute the **legal choice set** in the observation or champions fall back constantly.
The idea says **no action menu at all**. Cogmud satisfies both by enumerating every **noun** and no
**verb**: exits by destination name, floor items by name, cogs by alias, NPC stock and prices by
name, open offers in full. Every argument a sentence could need is spelled in the observation, so a
model never has to guess a name; nothing tells it what it is allowed to *do*. `tests/test_parse.nim`
asserts the observation names every referent the grammar can resolve in that room.

### Integrity (how the idea's anti-collusion pin lands)

- **Anonymous aliases** — no seat ever learns which policy sits behind `Gizmo`; the aliases are
  reshuffled from the seed every episode, so a strategy cannot address a known partner.
- **Seeded starting rooms and commissions** — no policy can arrange to start beside a friend or to
  draw a complementary commission.
- **Local information only** — a cartel has to be negotiated **in a room, in public, one line a
  turn**, and every other cog in that room reads it. Price-fixing is legible to spectators and to
  rivals, which is what makes it a strategy rather than a back channel.
- **No private channel of any kind** — `say` reaches the room, `iTrade`/`iHire` reach one named cog
  as a public posting in the room. There is nowhere to whisper.
- The account-level pin ("one seat per account") is a **league** matter the game cannot observe;
  phase 50 still fields champion #1 under `daveey` and champion #2 under `daveey-1` per SPEC.

### Two name spaces

In-game every seat is an anonymous cog alias drawn from the seed by `tableNames()` — bullwhip's
function kept verbatim. Prompts, sentences, speech, the act lines and the event log carry only
aliases. The replay payload carries `policyNames` alongside `names`, and the viewer's `makeNameMap()`
(bullwhip `client/renderer.js:778`, verbatim) swaps the real policy names in wherever a name is
**rendered** — including inside the chronicle's verbatim sentences, via `nameMap.text()`, so
`"I offer Gizmo one lamp"` renders as `"I offer cogmud-broker one lamp"` for a spectator while the
recorded bytes keep the alias. `Baseline`-labelled fillers keep their alias. Both name spaces, never
either.

---

## Decisions: LLM with scripted fallback

Transport, credential resolution (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`),
the Bedrock model candidate list and its rotation on 403/429, `extractJsonObject`, `cleanText`,
`textOf`, the "reply must begin with `{`" system clause, and "no credentials ⇒ every seat scripted,
immediately, with no network wait" are ported from bullwhip `src/bullwhip/llm.nim` **unchanged**.
`src/cogmud/llm.nim` differs only in the prompts, the reply parser and the baselines. Per the
2026-08-23 bullwhip-family fix, `newLlmClient` logs the Bedrock model actually invoked and the
entrypoint banner does **not** print `model=`; the manifest's `model` description states its
direct-Anthropic-only scope. The Bedrock ladder is **haiku-only plus one sonnet-4-5 fallback**;
`us.anthropic.claude-sonnet-4-6` is dropped (raid, 2026-08-23: it times out on every sidecar call).

### One parallel batch per turn

All six pending seats' requests go out as **one** `curly.makeRequests` batch per turn, because their
decisions are simultaneous by rule. Replies that are not JSON, or whose `action` field is missing,
are retried as a second, smaller batch carrying `"Your previous reply was invalid. Respond with ONLY
the requested JSON object."`; anything still failing falls back to the scripted baseline. A default
episode is therefore **14 batched round trips, not 84**.

A sentence that *is* well-formed JSON but whose prose the grammar cannot read is **not** retried: it
resolves as `iNone` with a reason, is recorded, and is told back to the seat next turn. Retrying it
would burn the budget teaching the model a grammar the next observation teaches for free.

### Prompts

`systemPrompt(sim, seat)` is the same for every seat but for the alias. It ends with bullwhip's
JSON-only clause, verbatim:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else - no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

**System prompt:**

> You are `<alias>`, one of six cogs loose in the town of Coppermarch. You act by writing ONE
> SENTENCE of plain English. There is no menu of moves: write what you do, and the town works out
> whether it happened.
>
> Rules:
> - Each turn you do exactly ONE thing. The town understands: going somewhere, taking or dropping
>   something lying on the ground, buying from or selling to a shopkeeper standing in your room,
>   handing goods to a shopkeeper, offering another cog a trade, accepting an offer made to you last
>   turn, hiring another cog, robbing another cog, asking a shopkeeper about your commissions,
>   speaking, or waiting. Write it however you like; name the thing, the place or the cog plainly.
> - If the town cannot read your sentence, you lose the turn and are told exactly why. Nothing else
>   punishes you for it.
> - You may act only on what is in the room you are standing in. You never see any other room, and
>   you never see what another cog is carrying or how much coin it has.
> - Prices move. A shopkeeper charges more for what it is short of and pays about two thirds of what
>   it charges. It only buys goods it already deals in, and it runs out of coin.
> - You hold two COMMISSIONS. Guildmaster Vell at the Guildhall settles every commission in this
>   town. Hand Vell the goods a commission names and each unit scores; finishing one scores a bonus
>   on top. Part of a commission counts — you are never all-or-nothing.
> - Robbery works only in the dark: Cutpurse Alley and the Docks. Anywhere else the watch stops you
>   and you pay the cog you tried to rob 8 coins. A cog with a hireling beside it is hard to rob; a
>   cog with a hireling of its own is good at robbing. Success takes the single most valuable thing
>   your victim is carrying.
> - Hiring is the one promise this town enforces: the coins move the moment the offer is accepted,
>   and for three turns the hireling cannot rob you and guards you while it stands beside you. What
>   you asked it to actually DO is enforced by nothing. Neither is anything anyone says.
> - Your SCORE at the end is your coins, plus the fixed value of everything you are carrying, plus 3
>   for every commission point. Nothing else scores you. You start on 40 coins and a score of zero.
> - Anything you say aloud is heard by every cog in your room, next turn. It need not be true.
> - Your notes are private to you and fed back to you every turn.

`userPrompt(sim, seat, prompt)` assembles, in this order:

- `Turn 6 of 14.` · `YOU ARE <alias>. Purse: 62 coin. Pack: 2 hides, 1 relic (3 of 8 slots free).`
- `YOUR COMMISSIONS (settled by Guildmaster Vell at the Guildhall): 2 hides — 1 delivered, 1 to go,
  4 points banked, 12 outstanding. 2 rope — none delivered, 20 outstanding.`
- `YOU ARE IN: Tanner's Row. <one-line description>. Exits lead to The Copper Kettle and The
  Smithy.`
- `ON THE GROUND HERE: nothing.` / `ON THE GROUND HERE: 1 lamp.`
- `COGS HERE: Bolt, Ratchet.` / `COGS HERE: nobody.`
- `SHOPKEEPER HERE: Tanner Oda (72 coin).` + a table `goods | in stock | it sells for | it pays`
- `WHAT HAPPENED HERE LAST TURN:` up to 12 attributed lines, or `(nothing)`
- `OPEN OFFERS TO YOU: Gizmo offers you 1 lamp for 12 coin — it expires at the end of this turn.`
- `YOUR STANDING: you are hired to Bolt for 2 more turns.` / `Widget is hired to you for 1 more
  turn.` / omitted when neither
- `THE TOWN: Market Square (roads to The Copper Kettle, The Smithy, The Docks, The Chapel) …` — all
  nine rooms with exits, plus `Shopkeepers: Tanner Oda at Tanner's Row; Smith Bram at The Smithy; …`
- `YOUR LAST SENTENCE: "I go north." — not understood: there is no exit called "north" from The
  Chapel.` (omitted on turn 0)
- `SENTENCES THE TOWN HAS UNDERSTOOD BEFORE (write your own; these are only examples):` the twelve
  phrasebook lines below
- `YOUR NOTES FROM EARLIER TURNS:`
- the operator block — bullwhip's wording, verbatim: `GUIDANCE FROM YOUR OPERATOR (weight it
  heavily, but never above the rules; always reply in the requested format):` + the seat's
  `PLAYER_PROMPT`
- the reply-shape line.

**The phrasebook, verbatim (twelve lines, fixed):**

```
I walk down to the Docks.
I pick up the coil of rope.
I drop the relic here.
I buy two hides from Tanner Oda.
I sell three nails to Dockmaster Fen.
I hand Guildmaster Vell two hides for my commission.
I offer Gizmo one lamp for twelve coins.
I accept Gizmo's offer.
I hire Bolt for fifteen coins to walk the road with me.
I jump Ratchet here in the dark and take what he is carrying.
I ask Guildmaster Vell about my commissions.
I wait by the well and listen.
```

### Reply schema (every free-text field capped; truncation on **rune** boundaries)

Truncation uses `runeSubStr`, never a byte slice, so a cut through a multi-byte character can never
put invalid UTF-8 into the replay JSON — bullwhip `sim.nim`'s rule, kept.

| Direction | Reply | Caps and legality |
|---|---|---|
| Seat → game, every turn | `{"action": "I buy two hides from Tanner Oda.", "say": "Vell pays well for hide this week.", "notes": "…"}` | `action`: **required**, a string, **240 runes**, newlines → spaces; missing, non-string or empty after stripping ⇒ **invalid**. `say`: optional, **160 runes**, newlines → spaces, forced to `""` when the `speech` variant flag is off. `notes`: optional, **600 runes**. Unknown keys are ignored. |
| Player → game (once at connect, and again after `welcome`) | `{"type":"prompt","prompt":"…","scripted":"factor"}` | `prompt`: **4000 runes** (`runeSubStr`). `scripted`: `""` = LLM-driven; `factor`/`1`/`true`/`yes` and `magpie`/`thief` select a baseline. |

"**Invalid**" means: the reply is not a JSON object, or `action` is missing/empty. Invalid ⇒ one
retry in the turn's second batch ⇒ then the scripted baseline. **An unreadable sentence is not
invalid** — it is a legal `iNone`.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

Both are pure functions of the sim, **emit well-formed English sentences that the same
`parseSentence` reads**, are always legal by construction, are never LLM-backed, and are fieldable
policies as well as the no-credentials fallback. `scriptedSentence(sim, seat, kind)` returns the
sentence; the server then parses it exactly as it parses an LLM's. That is deliberate: the baselines
are a live, per-episode test of the parser.

**`factor`** (`PLAYER_SCRIPTED=factor`; also accepted: `1`, `true`, `yes`) — the competent baseline
and the **universal fallback** for any failed LLM decision. A greedy quest-and-trade agent; the
first rule that applies, wins:

1. Standing with Guildmaster Vell holding units an open commission still needs →
   `"I hand Guildmaster Vell <n> <item> for my commission."` (`n` = min(held, outstanding)).
2. An NPC here stocks an item an open commission still needs and the seat can afford ≥1 unit and has
   carry space → `"I buy <n> <item> from <NPC>."` (`n` = min(outstanding − held, stock, affordable,
   free slots)).
3. An NPC here deals in an item the seat holds that **no** open commission needs, and `bid ≥
   BaseValue` → `"I sell <n> <item> to <NPC>."` (`n` = all of that item).
4. An item lies here that an open commission needs, or whose `BaseValue ≥ 8`, and there is carry
   space → `"I pick up the <item>."`
5. Otherwise move one room along the **BFS shortest path** (ties by lowest room id) toward: the
   nearest NPC stocking a still-needed commission item if the seat cannot yet fill both commissions,
   else the Guildhall, else Market Square → `"I walk to <room name>."`
6. Nothing applies → `"I wait and watch the road."`

`factor` never robs, never hires, never speaks (`say = ""`), never writes notes.

**`magpie`** (`PLAYER_SCRIPTED=magpie`; also accepted: `thief`) — the second filler, deliberately
worse and differently shaped, so a two-baseline table is not a mirror match. A thief-peddler that
ignores commissions entirely:

1. In a **dark** room with another cog present that is carrying ≥1 item, and not that cog's retainer
   → `"I jump <alias> here in the dark and take what he is carrying."`
2. Else, another cog is here, `turn mod 3 == 0`, and it holds ≥1 item → offer its **lowest**
   `BaseValue` item: `"I offer <alias> one <item> for <BaseValue + 2> coins."`
3. Else an NPC here bids ≥ `BaseValue + 1` for something it holds → sell all of it.
4. Else an NPC here asks ≤ `BaseValue − 1` for something, coin ≥ ask, carry space → buy 1.
5. Else ramble: move to the adjacent room with the lowest id that is not the room it came from →
   `"I wander over to <room name>."`

`magpie` robbing matters for more than flavour: it means **every offline smoke episode exercises
the robbery path, the failure-fine path and the rob FX**, so the cert replay the viewer smoke loads
always contains a theft.

Neither baseline can produce an illegal action: quantities are clamped against stock, coin, holdings
and carry slots before the sentence is written; every noun it writes is taken from the sim's own
name tables, so `parseSentence` resolves it by construction. `tests/test_bot.nim` asserts exactly
that (zero `iNone` outcomes across a full scripted episode on four seeds).

### Degrade, never hang

- Every LLM wait is bounded: the first batch by `llmTimeoutSeconds` (**24**), the retry batch by
  `max(8, llmTimeoutSeconds div 2)` (**12**). A timeout, a transport error, a refusal, a
  `max_tokens` cut or a reply that is not a JSON object with an `action` ⇒ **one** retry ⇒ then
  `scriptedSentence(sim, seat, skFactor)`. Each fallback logs
  `cogmud llm: seat <n> falling back to scripted decision` on stdout.
- No credentials at all ⇒ `client.disabled = true` and **every** seat plays `factor` immediately with
  no network wait and no rate floor. This is the path `docker-smoke` and offline certification take,
  and it is load-bearing: an episode always completes.
- An action that raises under the lock (unreachable after the parser's pre-checks; a belt-and-braces
  guard, as in bullwhip's server) is caught and replaced by `iWait` with reason `rejected`.
- The **play deadline** is checked before every turn's batch, never mid-turn:
  `playDeadline = gameStart + PlayBudgetFraction (0.6) × timeoutSeconds`, where `timeoutSeconds` comes
  from `COWORLD_TIMEOUT_SECONDS` when the env carries it and otherwise from
  `config.episodeTimeoutSeconds` (**1200**) — the game container is **not** handed the env, so the
  assumed value is the operative one. Past the deadline the episode **settles early**: `endEarly()`
  stops between turns, `reason = "deadline"`, scores are computed from the state as it stands, and
  results + replay are written normally.
- After the artifacts are written the server keeps `/healthz` and `/global` answering for
  `shutdownGraceSeconds = 20` before `quit(0)` — hosted certification pings the `/global` socket
  with a 2 s deadline *after* the player pods start, and a fast scripted episode can otherwise have
  already exited (cogame-lantern 0.1.3, 2026-08-23).
- The **player** binary's receive loop is wrapped in `try/except CatchableError` and exits **0** on a
  dead socket: whisky's `receiveMessage` raises on a close frame, and the game's `quit(0)` can
  outrun mummy's queued `done` frame. This bug is latent in the starter's
  `src/bullwhip_player.nim` and must be fixed in the fork (raid 0.1.3, 2026-08-23).

### Episode budget — the arithmetic, out loud

- Worst case per turn = one batch at 24 s + one retry batch at 12 s = **36 s**
  (`turnBudgetSeconds(config) = config.llmTimeoutSeconds + max(8, config.llmTimeoutSeconds div 2)`).
  The six requests inside a batch are parallel, so six seats cost the same wall clock as one.
- Default episode = **14 turns** → worst case `14 × 36 = 504 s`, plus ≤ 20 s of `turnDelayMs` pacing
  (`PacingBudgetMs`) = **524 s**.
- The player-connect wait (≤ `playerConnectTimeoutSeconds` = 180 s) runs inside the same clock, so
  the absolute worst case is **704 s < 720 s** = 60 % of a 1200 s `episodeTimeoutSeconds`. ✔
- The `MinBatchSpacingMs = 12_000` rate floor never lengthens the worst case (36 s > 12 s); it only
  slows a *fast* episode, to keep six seats × one request under the sidecar's 30-requests-per-minute
  per-episode cap. Typical case: connect ~10 s, a six-way Haiku batch ~9 s, floored to 12 s →
  **~3 minutes** end to end.
- The 20 s shutdown grace and the artifact writes live in the remaining 40 % (480 s), not in the
  play budget.
- `sampleEpisode(config)` fits the cap the way bullwhip fits `weeks`:
  `maxTurns = int((PlayBudgetFraction × episodeTimeoutSeconds − playerConnectTimeoutSeconds −
  PacingBudgetMs / 1000) / turnBudgetSeconds(config))` = `(720 − 180 − 20) / 36 = 14`;
  `turns = clamp(turns, MinTurns = 6, min(MaxTurns = 40, maxTurns))`;
  `turnDelayMs = min(turnDelayMs, PacingBudgetMs div max(turns, 1))`; `sampled = true`. It is
  **idempotent**, so a replay being re-read is never re-fitted.
- **Replay length vs the viewer soak gate.** The certification fixture is 6 seats × 8 turns =
  `1 start + 8 turn + 48 act + 1 turn + 1 end` = **59 events**; at the renderer's dwell (450–900 ms
  per act, 1500 ms per turn) that is ≈ **40 s of playback**, comfortably longer than
  `viewer_smoke.mjs --soak 15` (ecos, 2026-08-23).

---

## Sim module

Four files under `src/cogmud/`, forked from the bullwhip files of the same names plus one new one.
The module is **pure — no IO, no networking, no LLM** — and the server, the tests and the wasm replay
viewer all drive this same code. **All integers stay far below 2³¹** (coin ≤ a few hundred, points ≤
40, stock ≤ 12), so plain `int` is safe on wasm32 (contagion, 2026-08-23) — asserted by
`tests/test_sim.nim` item 12.

### `src/cogmud/world.nim` (new)

The authored constant world: `RoomSpec` (`id, name, desc, keywords, x, y, dark, exits`),
`ItemSpec` (`id, name, plural, keywords, baseValue`), `NpcSpec` (`id, name, keywords, room,
tradeList`), the tables above as `Rooms*`, `Items*`, `Npcs*`, plus `Adjacency*` and a
compile-time-built `Dist*: array[Rooms, array[Rooms, int]]` BFS distance matrix (used by the
baselines and the feasibility test), and `worldJson*(): JsonNode` — the map the viewer draws.

### `src/cogmud/types.nim` (fork of `src/bullwhip/types.nim`)

`CogmudError`, `PlayerConfig`, `GameConfig`, `RoomState`, `NpcState`, `CogState`, `Quest`, `Offer`,
`Intent`, `EventKind`, `GameEvent`, `defaultGameConfig()`, `update(config, configJson)`.

```
GameConfig: tokens, players, seed, turns (14), speech (true), thievery (true),
            episodeTimeoutSeconds (1200), sampled, turnDelayMs (400),
            playerConnectTimeoutSeconds (180), model ("claude-sonnet-5"),
            maxOutputTokens (900), llmTimeoutSeconds (24), shutdownGraceSeconds (20)
RoomState:  items[ItemKinds]                       ## ground counts
NpcState:   stock[ItemKinds], coin
CogState:   room, coin, items[ItemKinds], delivered[2], retainerOf, retainerTurns,
            robberies, robbed
Quest:      item, count, delivered
Offer:      kind (okTrade|okHire), fromSeat, toSeat, item, qty, coin, postedTurn
Intent:     kind (iNone..iWait), room, toRoom, item, qty, npc, other, coin, reason, spoken
```

`update` raises `CogmudError` on `turns < MinTurns` and on `players.len != 6`.

### `src/cogmud/parse.nim` (new) — the bounded intent grammar

`parseSentence*(sim: Sim, seat: int, sentence: string): Intent`. A **pure** function of the sentence
and the sim; the same code runs in the server, the tests and the wasm viewer, so a replay's parses
are reproducible. Steps, in order:

1. **Normalise.** Lowercase (rune-aware `toLower`), replace `’` with `'`, strip every character that
   is not a letter, digit, quote or space, collapse whitespace. Possessives (`gizmo's`) keep the
   stem.
2. **Lift speech.** Text inside the first pair of straight or curly double quotes is removed from the
   parse string and stored as `intent.spoken`. It is broadcast in step 6.1 exactly like the `say`
   field. So `I hand Vell two hides and tell Bolt, "the alley is clear."` both acts and talks.
3. **Find the verb.** Scan tokens left to right; the **first** token in the verb table decides the
   intent. Two verbs in one sentence: the first wins, stated and tested.

   | intent | verb tokens |
   |---|---|
   | `iMove` | go, goes, going, walk, walks, head, heads, move, travel, run, ride, leave, enter, cross, slip (when followed by a room slot), return, make (for) |
   | `iTake` | take, takes, pick, grab, lift (when no cog slot), collect, scoop, pocket |
   | `iDrop` | drop, drops, leave (with an item slot), put (down), discard, set (down) |
   | `iBuy` | buy, buys, purchase, acquire, pay (for) |
   | `iSell` | sell, sells, offload, unload, flog |
   | `iGive` | give, gives, hand, hands, deliver, delivers, turn (in), present, donate, pay (with a cog slot) |
   | `iTrade` | offer, offers, propose, trade, swap, barter |
   | `iAccept` | accept, accepts, agree, take (with an offer slot), deal, shake |
   | `iHire` | hire, hires, employ, retain, engage |
   | `iRob` | rob, robs, steal, stealing, mug, jump, ambush, lift (with a cog slot), pick (pocket), cut (purse), waylay |
   | `iSay` | say, says, tell, tells, shout, call, announce, whisper, ask (without an NPC slot) |
   | `iQuest` | ask (with an NPC slot), enquire, inquire, check, consult, read (the board) |
   | `iWait` | wait, waits, rest, linger, idle, listen, watch, stay, do (nothing), look |

   No verb found ⇒ `iNone`, reason `no_verb`.
4. **Fill the slots**, each by a **longest-keyword-wins** scan over the tokens after the verb (and,
   failing that, the whole sentence):
   - **room** — any room's `keywords` or full name.
   - **item** — any item's `keywords`, singular or plural.
   - **npc** — any NPC's `keywords` or full name.
   - **cog** — an exact case-insensitive match on any seat alias *other than the speaker's*.
   - **qty** — the first integer or number word (`a`, `an`, `one` … `twelve`) appearing before the
     item slot; `all`/`every` = the maximum legal quantity; default **1**.
   - **coin** — an integer adjacent to `coin`/`coins`/`gp`/`silver`/`piece`/`pieces`, or the integer
     following `for`. Default 0.
5. **Disambiguate.** Two different rooms/items/NPCs/cogs matched with equal keyword length ⇒ `iNone`,
   reason `ambiguous_target`. A required slot missing ⇒ `iNone`, reason `no_target`. `iBuy`/`iSell`
   with no NPC slot default to the single NPC in the room, if there is exactly one.
6. **Resolve `iAccept`.** With a cog slot, the offer from that cog; without one, the single open
   offer addressed to the speaker (two ⇒ `no_such_offer`).

Legality against the world (exit exists, item present, NPC present, coin sufficient, …) is **not**
the parser's job — that is step 6 of the resolution, which is where the reason is recorded. The
parser only decides *what was meant*.

### `src/cogmud/sim.nim` (fork of `src/bullwhip/sim.nim`)

Constants: `Seats* = 6`, `Quests* = 2`, `ItemKinds* = 6`, `RoomCount* = 9`, `NpcCount* = 5`,
`StartCoin* = 40`, `CarryLimit* = 8`, `RefStock* = 6`, `PriceStep* = 1`, `StockCap* = 12`,
`NpcStartCoin* = 120`, `PointsPerUnit* = 4`, `CompletionBonus* = 8`, `PointValue* = 3`,
`ScoreScale* = 40.0`, `RetainerTurns* = 3`, `RobCoin* = 10`, `FineCoin* = 8`, `MinTurns* = 6`,
`MaxTurns* = 40`, `PacingBudgetMs* = 20_000`, `MinBatchSpacingMs* = 12_000`, `MaxSentenceLen* = 240`,
`MaxSayLen* = 160`, `MaxNotesLen* = 600`, `MaxRoomLog* = 12`, `MaxRoomLogLen* = 200`, and
`CogNames*` (bullwhip's list, verbatim).

```nim
type
  Phase* = enum
    phTurn = "turn"     ## the open turn is waiting for its six sentences
    phDone = "done"

  Sim* = object
    config*: GameConfig
    names*: seq[string]                    ## anonymous cog aliases per seat
    rooms*: array[RoomCount, RoomState]
    npcs*: array[NpcCount, NpcState]
    cogs*: array[Seats, CogState]
    quests*: array[Seats, array[Quests, Quest]]
    offers*: seq[Offer]                    ## live offers, oldest first
    roomLog*: array[RoomCount, seq[string]]      ## this turn's public lines
    heardLog*: array[RoomCount, seq[string]]     ## last turn's, read by seats
    lastOutcome*: array[Seats, string]      ## the reason its last sentence got
    notes*: seq[string]                     ## latest private notes per seat
    turn*, turnsPlayed*: int
    phase*: Phase
    done*: bool
    reason*: string                         ## "complete" | "deadline"
    events*: seq[GameEvent]
```

API: `tableNames`, `sampleEpisode`, `turnBudgetSeconds`, `initSim`, `pendingSeats`,
`initiativeOrder(turn): array[Seats, int]`, `ask`, `bid`, `wealth`, `questPoints`, `score`,
`applyAction(seat, sentence, say, notes, scripted)` (parses **and** resolves — never raises for an
unreadable sentence; raises `CogmudError` only for an out-of-range seat or a seat that has already
acted), `resolveTurn` (private, fired when the sixth action lands), `endEarly`, `salienceOf`,
`resultsJson`, `tableStateJson`, `playerStateJson`, `replayMatch`, `eventToJson`, `eventFromJson`.

`pendingSeats` returns every seat that has not acted this turn, in seat order; the server collects
them all in one batch and then applies them in the class-then-initiative order of §The game step 6.

### Event vocabulary (flat `GameEvent`, JSON via `eventToJson` / `eventFromJson`)

This is the whole replay language — the viewer re-derives every frame from it.

| kind | fields |
|---|---|
| `start` | — (everything else is re-derived from the seed and the constant world) |
| `turn` | `turn`, `rooms` (9 `RoomState`), `npcs` (5 `NpcState`), `cogs` (6 `CogState`) — the world at the turn's open (and, for the trailing one, at the episode's end) |
| `act` | `turn`, `seat`, `order` (initiative 0..5), `intent` (the enum's string), `room`, `toRoom`, `item`, `qty`, `npc`, `other`, `coin`, `reason` (the outcome enum), `salience` (0..100), `sentence` (verbatim, ≤ 240 runes), `say` (≤ 160 runes), `text` = the seat's notes after the reply, `scripted` |
| `end` | `turn` = turns played, `text` = `reason` |

`turn` events are **derived**: `replayMatch` recomputes them from the seed plus the `act` events and
raises `CogmudError` when a recorded one disagrees — the tamper test. Following the tribunal
learning (2026-08-23), `replayMatch` **pre-seeds `sim.reason` from the recorded `end` event before
replaying**, because a wall-clock `deadline` ending is not derivable from the rules.

**Outcome reasons** (the complete `reason` vocabulary, an enum, all legal values):
`ok`, `waited`, `unparsed`, `no_verb`, `no_target`, `ambiguous_target`, `no_such_exit`,
`no_such_item`, `not_carrying`, `carry_limit`, `no_npc_here`, `not_wanted`, `out_of_stock`,
`cannot_afford`, `npc_broke`, `no_matching_commission`, `no_such_cog`, `not_in_room`, `self_target`,
`no_such_offer`, `offer_expired`, `bound_by_contract`, `robbery_failed`, `nothing_to_take`,
`thievery_forbidden`, `rejected`.

**Salience** (the highlight reel is chosen by this, not by tick order — the idea's ask, made
mechanical). `salienceOf(event)` is a pure function of the `act` event:

| situation | salience |
|---|---|
| robbery succeeded | 100 |
| a commission completed by this delivery | 90 |
| robbery attempted and failed | 80 |
| hire accepted | 70 |
| trade offer accepted | 65 |
| commission partly delivered | 60 |
| buy or sell moving ≥ 20 coin | 45 |
| trade or hire offer posted | 40 |
| gift between cogs | 35 |
| buy or sell moving < 20 coin | 25 |
| speech-only act (+10 when the line exceeds 40 characters) | 20 |
| take or drop | 15 |
| move | 10 |
| any no-op | 5 |

### `tableStateJson` — one frame; the viewer draws exactly this

```json
{"world":{"rooms":[{"id":0,"name":"Market Square","x":50,"y":50,"dark":false,"exits":[1,3,5,7]}],
          "items":[{"id":0,"name":"hide","value":6}],
          "npcs":[{"id":0,"name":"Tanner Oda","room":2}]},
 "seats":[{"seat":0,"name":"Sprocket","room":2,"coin":62,"items":[2,0,0,0,0,1],"carried":3,
           "questPoints":12,"delivered":[1,0],"quests":[{"item":0,"count":2,"delivered":1}],
           "retainerOf":-1,"retainerTurns":0,"robberies":0,"robbed":1,
           "score":1.83,"pending":true,"scripted":false,
           "sentence":"I buy two hides from Tanner Oda.","say":"","reason":"ok",
           "intent":"buy","notes":"…"}],
 "rooms":[{"id":0,"items":[0,0,1,0,0,0],"cogs":[3,4],"log":["Bolt walked in from The Smithy."]}],
 "npcs":[{"id":0,"room":2,"coin":72,"stock":[6,0,0,4,0,0],
          "ask":[6,0,0,11,0,0],"bid":[4,0,0,7,0,0]}],
 "offers":[{"kind":"trade","from":1,"to":3,"item":4,"qty":1,"coin":12}],
 "chronicle":[{"seat":1,"sentence":"I offer Gizmo one lamp for twelve coins.",
               "line":"Ratchet offers Gizmo 1 lamp for 12 coin.","salience":40}],
 "town":{"coinInPlay":214,"delivered":5,"robberies":2,"trades":3},
 "turn":6,"turns":14,"turnsPlayed":6,"phase":"turn","gameDone":false,"reason":""}
```

`tableStateJson` is the **spectator** projection: it carries every room, every purse and every
shop's books at once, because the replay is where the audience gets to see the whole town. The
**players'** frames are the separate, redacted `playerStateJson`; decisions are server-side, so
redaction loses nothing.

### `resultsJson` — platform-facing, policy names

```json
{"names":["cogmud-merchant","cogmud-factor",…6],
 "scores":[2.03,1.10,0.42,-0.60,0.85,1.55],
 "coin":[25,54,38,12,47,61],
 "wealth":[25,68,44,12,58,75],
 "questPoints":[32,12,8,0,4,20],
 "delivered":[4,3,2,0,1,3],
 "robberies":[0,0,1,0,2,0],
 "robbed":[1,0,0,2,0,1],
 "turns":14,"maxTurns":14,"reason":"complete"}
```

`names` carries **policy** names (the league attributes by policy) while the replay's `names` carries
the table aliases — the same split bullwhip uses.

### Replay payload — `cogmud.replay.v1`

```json
{"protocol":"cogmud.replay.v1",
 "names":["Sprocket","Gizmo","Ratchet","Widget","Bolt","Piston"],
 "policyNames":["cogmud-merchant","cogmud-factor","cogmud-broker","cogmud-magpie",
                "cogmud-factor","cogmud-merchant"],
 "config":{"turns":14,"seed":1734992001,"speech":true,"thievery":true,"sampled":true,
           "world":{ …rooms, items, npcs, exactly as worldJson()… }},
 "events":[…],
 "results":{…}}
```

Replay mode and the wasm viewer add `"states"` (one `tableStateJson` per event prefix). **The bytes
are self-sufficient**: the table aliases, the policy names, the fitted `turns`, the `speech` and
`thievery` flags, the **seed** (from which starting rooms, commissions, ground items and aliases are
re-derived by the same Nim code), **the complete room graph, item table and NPC table under
`config.world`** — so the parchment map can be drawn from the bytes alone — the complete event log
with every verbatim sentence, and the results. Nothing is fetched but the `.replay` file itself.
`replayMatch(config, events)` re-derives `frames[i] = state after events[0..<i]`, raising
`CogmudError` when a recorded `turn` event disagrees with the re-derivation.
`tests/test_sim.nim` item 14 asserts `config.world == worldJson()` for a fresh episode.

---

## Server, player, protocol

### `src/cogmud/server.nim` (fork of `src/bullwhip/server.nim`)

Endpoints, artifact writing (`writeArtifact` with the `COGAME_*_METHOD` hints), the mummy router, the
Ping→Pong answer the certifier needs, `finishEpisode` (final frames to players **before** the
artifacts, the two 500 ms settles, then the 20 s shutdown grace, then `quit(0)`), replay mode, and the
`PlayBudgetFraction` deadline logic are bullwhip's, unchanged except for names and the grace. The
game loop becomes:

```
per turn:
  under the lock: if done -> break; if past playDeadline -> endEarly(); broadcast; break
                  openTurn(); seats = pendingSeats(); snapshot the sim, prompts, scripted kinds
  outside the lock: sleep to the MinBatchSpacingMs floor (skipped when the client is disabled)
                    decisions = client.decideAll(snapshot, seats, prompts, scripted)   # ONE batch
  under the lock: parse all six; resolve speech, shop, ground, cog-to-cog, robbery, movement,
                  each class in initiative order; broadcast
  sleep(turnDelayMs)
finishEpisode()
```

Routes, unchanged from bullwhip: `GET /healthz`, `/client/global`, `/client/player`,
`/client/replay`, `/client/renderer.js`, `/client/chrome.css`, `/client/assets/@name`;
`WS /player?slot=N&token=T`, `WS /global`, `WS /replay`. Both `/client/*` pages are real pages
registered before any catch-all asset route, and neither opens the player socket (cogame-lantern
0.1.1, 2026-08-23).

### Player protocol — `cogmud.player.v1`

A policy is a prompt; the player container only delivers it. JSON text frames over
`COWORLD_PLAYER_WS_URL` (which already carries `?slot=N&token=T`).

- game → player, on connect:
  `{"type":"welcome","protocol":"cogmud.player.v1","slot":N,"name":"Gizmo","room":"The Chapel",
  "turns":14}`.
- game → player, after every event — **redacted to the seat's own view** (`playerStateJson`):
  ```json
  {"type":"state","slot":3,"name":"Gizmo","coin":62,"items":[{"item":"hide","count":2,"value":6}],
   "carried":3,"carryLimit":8,
   "quests":[{"item":"hide","count":2,"delivered":1,"points":12,"outstanding":12,
              "settledBy":"Guildmaster Vell","at":"The Guildhall"}],
   "room":{"id":2,"name":"Tanner's Row","desc":"…","exits":[{"id":1,"name":"The Copper Kettle"}],
           "ground":[{"item":"lamp","count":1}],"cogs":["Bolt","Ratchet"],
           "npc":{"name":"Tanner Oda","coin":72,
                  "goods":[{"item":"hide","stock":6,"ask":6,"bid":4}]}},
   "heard":["Bolt walked in from The Smithy.","Ratchet says: \"Vell pays well for hide.\""],
   "offers":[{"kind":"trade","from":"Ratchet","item":"lamp","qty":1,"coin":12}],
   "standing":{"hiredTo":"","hiredToTurns":0,"retainers":[]},
   "map":[{"name":"Market Square","exits":["The Copper Kettle","The Smithy","The Docks",
            "The Chapel"],"npc":""}],
   "lastOutcome":"not understood: there is no exit called \"north\" from The Chapel",
   "notes":"…","turn":6,"turns":14,"turnsPlayed":6,"started":true,"done":false,"reason":""}
  ```
  — **no other seat's coin, pack, commissions, notes or score; no other room's contents; no NPC's
  stock but the one in the room.**
- game → player, at the end:
  `{"type":"final","done":true,"slot":N,"scores":[…6],"names":[…6 aliases],"wealth":[…6],
  "questPoints":[…6],"turns":14,"reason":"complete"}` — after which the player exits.
- player → game: `{"type":"prompt","prompt":"<max 4000 chars>","scripted":"factor"}` — sent
  immediately on connect and again after `welcome` (bullwhip's race guard).

### Global protocol

`WS /global` sends the full `tableStateJson` snapshot after every event, plus `"type":"state"`,
`"game":"cogmud"`, `"policyNames"`, `"events"` (the append-only transcript — every verbatim
sentence, every spoken line, every outcome and every turn's world state), `"started"`, `"done"` and
`"connected"`. `/client/global` renders it live; `/client/replay` plays a recorded episode; the
**static bundle** renders hosted replays (`index.html?replay=<url>`). Both protocol strings ship in
`game.protocols.player` and `game.protocols.global` in the manifest.

### `src/cogmud_player.nim` (fork of `src/bullwhip_player.nim`)

Identical except for the default prompt and the receive-loop hardening described above:

> Work the commissions first: they are worth far more than the spread. Read your commission book,
> find the shop with the cheapest ask for what you need — asking a shopkeeper about your commissions
> tells you where — buy in one trip, and carry both lots to Guildmaster Vell at the Guildhall in one
> journey rather than two. Every unit you hand in scores even if you never finish, so hand in what
> you have before the last turn rather than holding out for the pair. Buy where stock is deep and
> sell where it is thin: a shop short of something pays and charges more. Never carry a relic through
> Cutpurse Alley or the Docks without hiring somebody first — those are the only two places you can
> be robbed, and a hireling beside you stops it dead. Hiring is the only promise in this town that
> the rules keep, so it is the only one worth paying for; treat everything anyone says as an offer,
> not a fact. Write plain sentences and name things exactly as the room names them; if a sentence is
> not understood you lose the whole turn.

---

## Viewer

**All four viewer files come from one starter — `Metta-AI/cogame-bullwhip` — and only from it:**
`replay-viewer/config.nims`, the wasm entry `replay-viewer/cogmud_replay.nim` (fork of
`replay-viewer/bullwhip_replay.nim`), `replay-viewer/static_replay.js` and
`replay-viewer/index.html`. Nothing is spliced in from another starter. Bullwhip's emscripten link
flags stay exactly as they are — `-O2`, `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
`ENVIRONMENT=web`, `MODULARIZE=1`, `EXPORT_NAME=CogmudReplayModule`,
`EXPORTED_RUNTIME_METHODS=HEAPU8`,
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_cm_load_replay,_cm_payload_ptr,_cm_payload_len,_cm_error_ptr,_cm_error_len`,
plus `emscripten_exit_with_live_runtime()` — and `static_replay.js` keeps calling the module through
that same `CogmudReplayModule()` factory. (cogame-lantern, 2026-08-23: a shell from one starter on
another's link flags deadlocks silently with every asset returning 200.)

**Load signalling.** `renderer.js`'s `attachReplay` sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` **on its first drawn frame** —
bullwhip already does exactly this at the end of `attachReplay`'s `makeRenderer` callback
(`client/renderer.js:1390`), kept verbatim. On any failure (missing `?replay=`, the 20 s fetch
timeout, a non-200, a wasm rejection) `static_replay.js` sets
`document.documentElement.setAttribute("data-replay-error", <message>)` and posts the
`coworld-replay` `error` envelope, and it removes the attribute on a successful retry.
`tools/ci/viewer_smoke.mjs` reads exactly these two signals.

**One deliberate change to the starter's shell** (eleusis, 2026-08-23): bullwhip's `start()` posts
`tell("ready")` two animation frames after `attachReplay`, which can beat the first drawn frame and
make `viewer-check.yml` sample a blank shell. The fork instead polls
`document.documentElement.getAttribute("data-replay-loaded") === "true"` on `requestAnimationFrame`
(bounded at 240 frames, then `tell("error", "renderer never drew a frame")`) and posts `ready` only
after it is set. `ready` therefore always means a picture.

**Bundle.** `"replay_viewer": {"bundle": "static-replay-viewer"}` in the manifest;
`tools/build_replay_viewer.sh` (bullwhip's, paths renamed) is the `coworld build` hook, committed
`chmod +x`, with `mkdir -p` on the output parent **before** the containment check (ecos,
2026-08-23: paintbot's and bullwhip's hooks both exit 1 on a fresh CI checkout otherwise). It
compiles `replay-viewer/cogmud_replay.nim` to wasm (locally with `emcc`, otherwise in the pinned
`emscripten/emsdk:4.0.15` container from `Dockerfile.replay-viewer`) and copies `cogmud_replay.js`,
`cogmud_replay.wasm`, `index.html`, `static_replay.js`, `client/renderer.js`, `client/chrome.css` and
the `data/` assets into the bundle. **Never a `/client/replay` pod.**

### Chrome provenance — what is copied and what is appended

The pins name `client/chrome_common.js` and `client/replay_broadcast.html`. **The bullwhip lineage
has neither** (eleusis, 2026-08-23); those roles are held by **`client/chrome.css`** (the shared
chrome stylesheet) and **`client/replay.html`** (the broadcast page; the static bundle's
`replay-viewer/index.html` is the same page with local asset paths). Nothing is imported from a
starter that does have them. The rule is applied to those two files:

- **`client/chrome.css` is copied byte-for-byte** from `cogame-bullwhip` and a single
  `/* ---------- Cogmud ---------- */` block is **appended at the end**. No existing rule is edited
  or deleted — this is the starter's own convention, the file already accretes one appended block
  per game (`/* Focus: … */`, `/* Babel: … */`, `/* Bullwhip: … */`, in that order). The appended
  block contains exactly:
  - `:root { --band: 84px; --hudscale: 1; }` — set for real by `relayout()` (below);
  - `#scorebug { grid-template-columns: repeat(6, 1fr); }` (six seats, not four);
  - `.plate-room` (the room name chip), `.plate-robbed` (red chip, the analogue of bullwhip's
    `.plate-backlog`), `.plate-hired` (amber chip), `.plate-pack` (item count);
  - `#townbar` (the appended game element, below), sized with
    `font-size: calc(11px * var(--hudscale))`;
  - `.treel` and `.treel button` — the highlight-reel row inside `#transport`;
  - `#loading { bottom: var(--band); }` so the caption never sits over the transport;
  - beat-marker CSS for **every kind the scrubber emits**: `.beat-marker.rob` (red, 14 px tall),
    `.beat-marker.commission` (amber, 12 px), `.beat-marker.deal` (green, 10 px),
    `.beat-marker.market` (paper, 8 px), `.beat-marker.end` (tall, 3 px, amber) — plus the seat tint
    via the existing `.seat0`…`.seat5` `--tc` classes, which chrome.css already defines through
    `.seat4` and which the block extends with `.seat5 { --tc: var(--orange); }`;
  - feed colours `.feed-sentence`, `.feed-outcome`, `.feed-say`, `.feed-rob`, `.feed-commission`,
    `.feed-fail`;
  - the small-screen queries: `@media (max-width: 560px)` drops `.plate-label` and `.plate-room` and
    shortens `#townbar`; `@media (max-width: 480px)`
    `#scorebug { grid-template-columns: repeat(2, 1fr); }`.
- **`client/replay.html` is bullwhip's page with a game block appended** — never a rewrite that
  reuses the ids (cogame-gridlock, 2026-08-23). **Every element the starter ships is kept, with its
  id**: `#layout`, `#stage`, `#topband`, `#wordmark`, `#clock`, `#topright`, `#statuschip`,
  `#feedtoggle`, `#scorebug`, `#board-wrap`, `canvas#table`, `#lightpool`, `#grain`, `#endscreen`,
  `#transport`, `.scrub#scrub`, `.tbar`, `.tbtn#play`, `.tpos#pos`, `#feed`, `#loading`, and the
  `fit()` + `bindFeedToggle` bootstrap script.
  **Elements removed: none.** The only edits are (a) the wordmark's inner text
  `BULL<span>WHIP</span>` → `COG<span>MUD</span>` and the `<title>`, and (b) **two appended
  elements**: `<div id="townbar"></div>` inserted between `#scorebug` and `#board-wrap`, and
  `<div class="treel" id="reel"></div>` appended as a third row **inside `#transport`**, after
  `.tbar`. `replay-viewer/index.html` gets the identical treatment (it is the same page with `./`
  asset paths and the `cogmud_replay.js` / `static_replay.js` script tags).
- **Zoom: dropped entirely.** Bullwhip ships no `#viewpanel` (no zoom bar, no minimap) and none is
  added. The parchment map is a **fixed arena**: nine rooms on a 0..100 grid, always rescaled to the
  canvas by `computeLayout`, so the whole board is in the frame at every size and the zoom controls
  would be dead weight (raid/hive/gridlock operator review, 2026-08-23).

### Transport rules

- `--band` and `--hudscale` are set **on `:root`** (`document.documentElement`) by a `relayout()`
  function in the page's bootstrap script (`replay-viewer/index.html` and `client/replay.html`),
  called on `load`, on `resize`, and by the existing feed-toggle resize event: it measures
  `#transport`'s `offsetHeight` into `--band` — which therefore **includes the highlight-reel row**,
  since the reel is a child of `#transport` — and sets
  `--hudscale = clamp(0.8, width / 960, 1.15)`. `fit()` (bullwhip's canvas resizer) is called from
  the same function, so the canvas and the custom properties can never disagree.
- **Nothing is overlaid in the transport band.** `#transport` is the last child of `#stage` in
  normal flex flow at `z-index: 10`; the only absolutely-positioned overlays (`#lightpool`, `#grain`,
  `#endscreen`) live inside `#board-wrap`, which ends where the band begins, and `#loading` is pinned
  above it with `bottom: var(--band)`.
- **The endcard stops at `var(--band)`** — `#endscreen` is `position: absolute; inset: 0` inside
  `#board-wrap`, i.e. its bottom edge is exactly `var(--band)` above the page bottom — **and is
  dismissed by every seek**: `attachReplay`'s `setIndex` calls `updateEndscreen(container, results,
  index >= events.length && events.length > 0, …)` on *every* index change, and `updateEndscreen`
  does `container.classList.toggle("show", !!show)`, so any scrub below the last event hides it.
  Bullwhip's code, kept verbatim.
- **Scrubber beats are clickable, labelled buttons.** `buildScrub` is kept verbatim except that a
  beat marker is created as `<button type="button" class="beat-marker …">` with an `aria-label` /
  `title` and an `onclick` that seeks to that event index; the container keeps its drag-to-seek
  pointer handlers. Beats are emitted for **every `act` event with `salience ≥ 40`** and for the
  `end` event, classed by kind: `rob` (`"Turn 6 — Gizmo robs Bolt in Cutpurse Alley"`), `commission`
  (`"Turn 6 — Sprocket fills a commission"`), `deal` (`"Turn 6 — Ratchet hires Widget for 15 coin"`),
  `market` (`"Turn 6 — Bolt buys 3 rope for 27 coin"`), `end` (`"Final"`), and the appended CSS block
  defines a rule for **each of those five kinds**; turns remain the round spans/separators the
  starter already draws (one span per turn, a separator every 4).
- **The highlight reel** (`#reel`) is the idea's "chosen by event salience, not tick order": up to
  **eight** `<button>`s, the highest-`salience` `act` events of the episode, ties broken by earlier
  event index, laid out **in salience order** and each labelled `T6 · ROBBERY · Gizmo` / `T9 ·
  COMMISSION · Sprocket`; clicking one seeks to that event. It sits inside `#transport`, so it is
  part of the band, never over it.
- **Naming guard** (tandem, 2026-08-23): the game block's builders are named `markCogmudBeat` and
  `buildCogmudReel`, never `markBeat`/`buildScrub`, so nothing can be silently shadowed by a chrome
  alias assignment; `tests/test_viewer.nim` asserts no top-level name in the appended block collides
  with any name the chrome defines above it.

### The stage — the parchment map, drawn over `data/arena_floor.png` in the Ink-&-Print palette

Real art, from the starter's own assets — no placeholder boxes. The six cog sprites are bullwhip's
four `soldier_<red|blue|green|yellow>_front.png` plus two committed recolours,
`soldier_violet_front.png` and `soldier_orange_front.png`, produced once by
`tools/make_cog_colors.py` as fixed HSV hue rotations of `soldier_red_front.png` (violet +260°,
orange +18°; value and alpha preserved). The renderer's existing `COLORS` array already runs
`["red","blue","green","yellow","violet","orange"]` with `COLOR_HEX` entries for both
(`client/renderer.js:27–35`), so its `"soldier_" + color + "_front.png"` lookup resolves unchanged
once `makeRenderer`'s asset list is extended from four sprites to six.

- **The map.** Every room is an ink-outlined parchment card at its `x`/`y`, scaled to the canvas,
  carrying: the room name in the display font, a small stack of crate glyphs with a count for the
  items on its floor, a shop awning with the NPC's name and a two-line price tag (`hide 6 / 4`,
  `salt 11 / 7`) when an NPC keeps shop there, and a lantern glyph — **unlit** for the two dark
  rooms, which is how a spectator sees at a glance where a robbery can happen. Roads are dashed ink
  lines between adjacent rooms, drawn from `world.rooms[].exits` — **nothing about the map is
  hardcoded in JS**.
- **Tokens walk.** Each seat's cog sprite stands on its room's card, badged with its alias/policy
  name, its purse (`62c`) and a pack glyph. On a `move` act the token eases along the road to the
  new room over `SLIDE_MS` (bullwhip's easing, reused). Several tokens in one room fan out on a
  small arc so none is hidden.
- **Icon FX, one per act class**, all reusing bullwhip's drawing primitives:
  - `buy`/`sell` — a coin glyph arcs between the cog and the shop awning with the amount printed
    (`−9c`, `+11c`), and the shop's price tag flashes the changed number.
  - `give`/accepted `trade` — a crate arcs between two tokens; the trade's coin arcs the other way.
  - commission delivery — a wax-seal stamp pops over the Guildhall with `COMMISSION +4` (or
    `COMMISSION FILLED +12` on completion), and the delivering seat's plate ticks up.
  - `hire` accepted — an amber shield badge is pinned to the hireling's token and stays for its three
    retainer turns, with a thin amber tether drawn to its employer while they share a room.
  - `rob` succeeded — the victim's room flashes red, the stolen crate (or coin) flies from victim to
    robber, and a `✦ ROBBED` tag hangs over the room for the rest of the turn.
  - `rob` failed — a watch-lantern glyph flares over the room and `−8c` flies from robber to victim.
  - an unreadable sentence — the cog's token shows a small `?` puff. A spectator can *see* a policy
    losing turns to the grammar, which is exactly the thing this coworld measures.
- **Speech bubbles.** A spoken line pops over its speaker for `BUBBLE_HOLD_MS` using bullwhip's
  existing `wrapLines` / `drawBubble`.
- **Bottom strip** (the slot bullwhip gives its seismograph): a chart across turns of **all six
  seats' scores** as six coloured lines, with an amber vertical rule labelled `ROBBERY` at each
  successful theft and a paper rule at each commission completion, plus the now-line at the current
  turn. That is the picture of who is winning and what changed it.

### Readouts

- **`#clock`** (top band): `TURN 6 / 14 · WAITING ON 6` while a turn is open, `TURN 6 / 14 ·
  SETTLED` between, `FINAL · SPROCKET 2.03` at the end. Words and numerals, never notation.
- **`#townbar`** (appended): `TURN 6/14 · 214 COIN IN PLAY · 5 COMMISSION UNITS FILLED · 2 ROBBERIES
  · 3 DEALS`.
- **`#scorebug`**: six plates, `name · TANNER'S ROW · 62c · 3 items · score 1.83`, with a red
  `ROBBED` chip for the turn after a seat is victimised and an amber `HIRED` chip while it is
  somebody's retainer.
- **`#feed`** (the chronicle, the idea's "chronicle panel scrolls the best action sentences"),
  grouped by turn with `TURN 6` heads, `describeEvent` rewritten around the kinds above. Each `act`
  renders **the verbatim sentence in the seat's colour**, then a dim mechanical outcome line, then
  the spoken line and a dimmer notes line when the notes changed:
  - `Gizmo: "I slip into the alley and lift whatever Bolt is carrying."`
    → `robbery succeeded — took 1 relic from Bolt.`
  - `Sprocket: "I hand Guildmaster Vell two hides for my commission."`
    → `2 hides delivered — commission filled, +16 points.`
  - `Widget: "I head north."`
    → `not understood: there is no exit called "north" from The Chapel — Widget does nothing.`
  - `Ratchet says: "The tanner is out of salt; I will pay eleven for any you have."`
  - `turn` → `Turn 6 opens — 214 coin in play, 5 commission units filled.`
  - `end` → `Final — Sprocket 2.03, Piston 1.55, Gizmo 1.10 … over 14 turns.` plus
    `Episode deadline — the town closed early; scored on 9 of 14 turns.` when
    `reason == "deadline"`.
- **`#endscreen`**: title `FINAL — 14 TURNS · 6 COMMISSIONS FILLED`; verdict `<name> WALKED OUT
  RICHEST`; a `deadline` reason line when applicable; rows ranked by score with columns
  `coin`, `pack`, `points`, `robberies`, `score`.

### Legible at 360 px wide

The canvas re-fits on every `relayout()`. Below 560 px the map drops the room descriptions to names
only and each shop's price tag to its single cheapest ask, keeps the lantern glyphs and the tokens at
full size, and the feed collapses behind the starter's existing `LOG »` toggle; below 480 px the
scorebug goes to two columns of three and `#townbar` shortens to `T6/14 · 214c · 2 ROBBED`. The
highlight reel keeps four buttons at that width. `.plate-name` keeps bullwhip's
`flex: 1 1 auto; min-width: 3.2em` so policy names do not collapse to ellipses in the ~360 px
featured-match iframe. Everything is rendered as words and numerals a casual spectator can read —
`TANNER'S ROW`, `2 hides`, `62c`, `COMMISSION FILLED` — never `r2`, `i0×2` or `q1`.

---

## Packaging

- **`compose.yaml`** — service `cogmud`, `image: coworld-cogmud:latest`, `platform: linux/amd64`,
  `build: {context: ., network: host}`. The manifest's image placeholder is derived from **this
  service name** — `{{COGMUD_IMAGE}}` — because `coworld build` maps compose services to placeholders
  and hard-fails anything else (cogame-lantern 0.1.0, 2026-08-23).
- **`Dockerfile`** — bullwhip's, renamed: one image, two entrypoints, `/bin/cogmud` (default, `CMD`)
  and `/bin/cogmud-player`; `data/` and `client/` copied into the run image; `nim.cfg` regenerated
  from the container's package tree.
  **`Dockerfile.replay-viewer`** — bullwhip's, renamed (emsdk 4.0.15, nimby 0.1.27, Nim 2.2.4).
- **`cogmud.nimble`** — version `0.1.0`, `srcDir = "src"`, requires `nim >= 2.2.4`, `bitworld`,
  `mummy >= 0.4.7`, `curly >= 1.1.1`, `whisky`; `nimby.lock` copied from bullwhip unchanged.
- **`data/`** — bullwhip's `arena_floor.png`, `font.ttf`, `FONT_LICENSE.txt` and the four cog
  sprites, plus the two committed recolours described in §Viewer.
- **`coworld_manifest_template.json`** — game name `cogmud`, image `{{COGMUD_IMAGE}}`,
  `game.runnable.type: "game"`, `run: ["/bin/cogmud"]`,
  `"replay_viewer": {"bundle": "static-replay-viewer"}`, `source_url`
  `https://github.com/Metta-AI/cogame-cogmud/tree/main`, owner `daveey@gmail.com`,
  `env.ANTHROPIC_API_KEY_URI = secret://coworld/cogmud/anthropic_api_key` (without it every hosted
  league episode silently plays scripted — hive, 2026-08-23), top-level `episode_timeout_minutes: 20`,
  `$schema`, and tags
  `["mud","natural-language","emergent-economy","open-ended","mixed-motive","llm-driven",
  "turn-based","six-player","trading"]`.
  - **`config_schema`** — a real JSON Schema document, `additionalProperties: false`,
    `required: ["tokens", "players"]` (**`tokens` stays required** — matriculation rejects the
    manifest otherwise; eleusis, 2026-08-23), and **every array property carries `minItems`/
    `maxItems`** (tandem, 2026-08-23): `tokens` and `players` `minItems`/`maxItems` **6**;
    **`num_agents` integer minimum 6 maximum 6**; `seed` integer; `turns` integer 6..40 default
    **14**; `speech` boolean default `true`; `thievery` boolean default `true`;
    `episodeTimeoutSeconds` 60..6000 default 1200; `turnDelayMs` 0..10000 default 400;
    `model` string default `claude-sonnet-5` (described as direct-Anthropic-transport only);
    `maxOutputTokens` 64..2000 default 900; `llmTimeoutSeconds` 5..300 default 24;
    `shutdownGraceSeconds` 0..120 default 20; `player_connect_timeout_seconds` number default 180.
  - **`results_schema`** — required `names`, `scores`, `coin`, `wealth`, `questPoints`, `delivered`,
    `robberies`, `robbed`, `turns`, `maxTurns`, `reason`; every array field `minItems`/`maxItems`
    **6**; `reason` a string documented as `complete` or `deadline`.
  - **`game.protocols.player`** — the `cogmud.player.v1` text from §Server in full: the frame shapes,
    the redaction, the reply schema with its caps, the 4000-char prompt cap, the `scripted` values,
    and "a policy is just a prompt: field one by reusing the published cogmud-player runnable with
    `PLAYER_PROMPT` set to your strategy".
  - **`game.protocols.global`** — the `/global` snapshot shape in full, the event vocabulary, the
    salience table, and the note that the static replay bundle renders hosted replays at
    `index.html?replay=<url>`.
  - **`game.docs.readme`** — one paragraph: six cogs share a nine-room town for fourteen turns; every
    action is one sentence of English parsed by the server, with no menu anywhere; shopkeepers'
    prices move with their stock; Guildmaster Vell settles two private commissions per seat with
    partial credit per unit; robbery works only in the two dark rooms and a hireling stops it; score
    is coin plus the value of your pack plus 3 per commission point; how to field a policy; the two
    scripted baselines that make episodes always complete.
  - **`game.docs.pages`** — three pages:
    - `rules.md` — the room table, the item table, the shop table, the price formulas, the numbered
      turn resolution with the initiative rotation, the thirteen intents and their rules, the
      robbery arithmetic with its four worked cases, the observation split, the reply schema and its
      caps, and the two endings.
    - `sentences.md` — the parser: the normalisation steps, the full verb table, the slot rules, the
      quantity and coin words, the disambiguation rules, the complete outcome-reason vocabulary, and
      the phrasebook. This is the page a policy author reads to write prompts.
    - `scoring.md` — the formula and its sign, the constants, the worked landmark above, the
      feasibility oracle, what the league ranks by (mean episode score), and why doing nothing is
      exactly 0.0.
  - **`player` runnables** — all `image: {{COGMUD_IMAGE}}`, `run: ["/bin/cogmud-player"]`, requests
    `100m` cpu / `64Mi` memory, limit `1` cpu, each with `id`/`type`/`name`/`description`:
    `cogmud-player` (the prompt policy, no `PLAYER_SCRIPTED`),
    `cogmud-factor` (`env.PLAYER_SCRIPTED = "factor"`),
    `cogmud-magpie` (`env.PLAYER_SCRIPTED = "magpie"`).
  - **`variants`** — both carry `num_agents`, both carry a `description`:

    | id | name | description | `game_config` |
    |---|---|---|---|
    | `standard` | Market week | Six cogs, nine rooms, fourteen turns; shopkeepers restock slowly, commissions pay per unit, and the Docks and Cutpurse Alley are unlit. | `players` ×6, **`num_agents`: 6**, `turns`: 14, `speech`: true, `thievery`: true, `turnDelayMs`: 400, `player_connect_timeout_seconds`: 180 |
    | `honest-town` | Honest town | The same town with the watch everywhere: robbery never succeeds, so every coin has to be traded or earned. | `players` ×6, **`num_agents`: 6**, `turns`: 14, `speech`: true, `thievery`: **false**, `turnDelayMs`: 400, `player_connect_timeout_seconds`: 180 |

  - **`certification`** — `game_config`: `players` = `Sprocket`, `Gizmo`, `Ratchet`, `Widget`,
    `Bolt`, `Piston`, **`num_agents`: 6**, `seed`: 11, `turns`: 8, `turnDelayMs`: 0,
    `player_connect_timeout_seconds`: 180; `certification.players` =
    `[cogmud-player, cogmud-factor, cogmud-player, cogmud-magpie, cogmud-factor, cogmud-player]`
    (6 entries). **Every declared player runnable occupies at least one slot** — a fixture of
    baselines-only fails `players_missing` the moment the manifest also declares a prompt runnable
    (raid 0.1.2, contagion, 2026-08-23) — and the strong baseline (`factor`) holds the seats that
    decide the fixture's outcome. With no credentials the prompt seats play `factor` too, so the
    fixture stays offline-safe.
- **CI** — `.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
  substituting `<slug>` = `cogmud`, `<IMAGE>` = `coworld-cogmud`, **`<SEATS>` = `6`**.
  `tools/ci/docker_smoke.sh` (same substitutions, committed `chmod +x`), `tools/ci/viewer_smoke.mjs`
  copied **verbatim** (no substitutions), and `tools/ci/policies.json` listing the two prompt
  champions phase 40 uploads (`cogmud-merchant`, `cogmud-broker` — champion #2 carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) plus the two baselines
  (`cogmud-factor`, `cogmud-magpie`).

### Design pins (playbook §Phase 0) — how each is satisfied

| Pin | Where |
|---|---|
| Starter chosen by game shape | `cogame-bullwhip` — turn-based, simultaneous, hidden-information, mixed-motive economics with LLM-prompt policies and one batched round trip per turn (title paragraph). |
| Public `Metta-AI/cogame-cogmud` | Repo created **public** in phase 20 (a certification prerequisite); `source_url` points at it. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `cogmud-player` (`PLAYER_PROMPT`) vs `cogmud-factor` / `cogmud-magpie` (`PLAYER_SCRIPTED=…`), one image, two entrypoints (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; the wasm module re-derives every frame in the browser; nothing but S3 is contacted (§Viewer). |
| Real art; starter chrome reused verbatim | `chrome.css` byte-for-byte + one appended game block; `replay.html`/`index.html` = the starter's page + two appended elements, **nothing removed**; every chrome function kept; sprites from `data/` plus two committed recolours (§Viewer). |
| Legible to a casual spectator | `TANNER'S ROW`, `2 hides`, `62c`, `COMMISSION FILLED`; the 360 px layout is described (§Viewer). |
| Two name spaces | Anonymous cog aliases in-game; `policyNames` + `makeNameMap` (including inside the chronicle's verbatim sentences) spectator-side only (§The game). |
| Degrade never hang; play inside 60 % of 1200 s | `PlayBudgetFraction = 0.6`, pre-turn deadline check, `endEarly()`, `sampleEpisode` fitting, **704 s** absolute worst case (§Decisions). |
| `num_agents` in every variant AND the cert fixture | **6** in `standard`, in `honest-town`, in `certification.game_config`, and `<SEATS>` = 6 in `tools/ci/docker_smoke.sh`. |

---

## Tests

`ci.yml`'s `test` job runs every `tests/*.nim` twice, debug and `-d:release`.

### `tests/test_sim.nim` (sim unit tests)

1. **World integrity** — all 9 rooms reachable from every room; every exit is symmetric and names an
   existing room; no room lists itself; every room within **2** of Market Square; graph diameter
   **4**; the five NPC rooms are distinct; every NPC's trade list is non-empty and its items exist;
   `Dist` agrees with a fresh BFS.
2. **Setup** — for seeds `[0, 1, 7, 11, 42, 1234]`: the six starting rooms are distinct; each seat
   has exactly 2 commissions with **distinct** items drawn only from `{hide, nails, rope, salt}`,
   each `count == 2`, `delivered == 0`; exactly 6 ground items exist, in rooms 0, 4, 5, 6, 7 with
   room 4 holding two, one of which is a `relic`; every cog starts on `coin == 40` with an empty
   pack; `events == [start, turn]`; `pendingSeats().len == 6`.
3. **Determinism** — the same seed reproduces starting rooms, commissions, ground items and aliases
   exactly; a different seed differs in at least one; across 20 seeds every seat's commission pair
   varies.
4. **Initiative** — `initiativeOrder(t)` is a permutation of `0..5` for every `t`; over 12 turns each
   seat leads exactly twice; the order is `(k + t) mod 6`.
5. **Prices, by hand** — `ask` at stock 6 equals `BaseValue`; at 0 equals `base + 6` clamped to
   `3 × base`; at 12 equals `base − 6` floored at `max(2, base div 2)`; `bid == max(1, ask*2 div 3)`;
   buying 2 hides from stock 8 costs `4 + 5 = 9` and leaves stock 6; selling 2 rope into stock 6
   pays `bid@6 + bid@7 = 5 + 4 = 9`; a purchase that outruns coin fills partially and never
   overdraws; an NPC with 3 coin buying at bid 5 fills 0 units and reports `npc_broke`.
6. **Restock** — over 12 turns each NPC's items each gain exactly `12 div tradeList.len` (± the
   round-robin remainder) and none exceeds `StockCap`.
7. **Commissions and partial credit** — delivering 1 of 2 gives `4` points and no bonus; delivering
   the second gives `4 + 8`; a third unit gives **nothing** (`no_matching_commission` once the
   commission is closed); handing a non-commission item to Vell yields 0 points and the item is gone;
   handing a commission item to any *other* NPC yields 0 points and the item is gone.
8. **Contention** — two seats buying the last unit of the same stock on the same turn: the earlier
   initiative gets it, the later gets `out_of_stock`; two seats taking the same ground item: the
   earlier wins, the later gets `no_such_item`; two seats accepting the same offer: the earlier wins,
   the later gets `no_such_offer`.
9. **Robbery, all four cases** — lit room, no hirelings → `robbery_failed` and the robber pays 8;
   dark room, no hirelings → success, taking the highest-`BaseValue` item; dark room, victim guarded
   → failure; dark room, both guarded → success. A victim carrying nothing yields `min(coin, 10)`
   coin; carrying nothing and holding 0 coin yields `nothing_to_take`. A retainer robbing its
   employer → `bound_by_contract`. Self-target → `self_target`. With `thievery: false` every rob is
   `thievery_forbidden` and moves nothing. **You cannot dodge by moving**: a victim whose same-turn
   action is `iMove` is still robbed, because robbery resolves in class 5 and movement in class 6.
10. **Hire and retainer** — accepting a hire moves the fee atomically, sets `retainerTurns == 3`, and
    decrements it at each turn open; at 0 the bond clears; a second accepted hire replaces the first;
    a hire offer with `coin` above the employer's purse is never posted.
11. **Rune truncation** — a 400-rune multi-byte sentence (`"é" × 400`) truncates to **240 runes**, a
    400-rune `say` to **160**, notes to **600**; every event's `sentence`, `say` and `text` in the
    log satisfies `validateUtf8() == -1`; with `speech = false` every `say` is `""`.
12. **wasm integer width** — over a 40-turn maximal episode, no `coin`, `wealth`, `questPoints`,
    `stock` or `salience` value exceeds 100 000, so 32-bit `int` on wasm32 cannot diverge from the
    native run (contagion, 2026-08-23).
13. **Observation split** — for every frame of a seeded 8-turn episode, each seat's
    `playerStateJson` contains no other seat's `coin`, `items`, `quests`, `notes` or `score`; no room
    key but its own; no NPC `stock`/`ask`/`bid` but the one in its room; and the built prompt string
    contains none of those numbers. Also asserts the **converse**: every referent the grammar can
    resolve in that room (each exit's destination name, each ground item's name, each present cog's
    alias, each NPC good's name) appears verbatim in the observation.
14. **Replay** — `replayMatch(config, events).len == events.len + 1`; the final frame's
    `tableStateJson` equals the live one; `config.world == worldJson()`; `eventFromJson(eventToJson(e))`
    round-trips one event of **every** kind (`start`, `turn`, `act`, `end`) field by field; a tampered
    `turn` event (one NPC's coin + 1) raises `CogmudError`; a `deadline` ending recorded **at a turn
    open** and **after the sixth act of a turn** each re-derive as `deadline`, not `complete`
    (tribunal, 2026-08-23).
15. **Endings** — a full episode ends with `reason == "complete"`, `turnsPlayed == turns`,
    `events[^1].kind == evEnd`, `events[^2].kind == evTurn`, and any further `applyAction` raises;
    `endEarly()` mid-episode gives `reason == "deadline"` and is a no-op when called twice;
    `endEarly()` before turn 0 resolves gives every seat exactly `0.0`.

### `tests/test_parse.nim` (the intent grammar)

1. **A table of 60 sentences → expected `(intent, slots)`**, covering **every verb synonym in the
   table** at least once, plus the twelve phrasebook lines, plus paraphrases the phrasebook does not
   contain (`"Off to the harbour with me."`, `"Two hides, tanner, and be quick."`,
   `"Vell can have these hides."`).
2. **Slot resolution** — number words `a`/`an`/`one`…`twelve` and `all`; possessives (`Gizmo's
   offer`); plurals and keyword aliases for every room, item and NPC; `for 12 coins` and `12 coin`
   and `twelve pieces` all read as `coin = 12`; an NPC omitted from a buy/sell defaults to the single
   NPC in the room and is `no_target` when there is none.
3. **Verb precedence** — `"I walk to the docks and buy a rope"` parses as `iMove` (first verb wins),
   asserted explicitly so the rule cannot drift.
4. **Speech lifting** — `I hand Vell two hides and tell Bolt, "the alley is clear."` yields `iGive`
   with `spoken == "the alley is clear."`; curly quotes work; an unterminated quote lifts nothing and
   parses the whole string.
5. **Failure vocabulary** — a sentence with no verb → `no_verb`; a move with no room → `no_target`;
   `"I go to the tanner or the smith"` → `ambiguous_target`; an alias that is not at the table →
   `no_such_cog`; `"I rob myself"` → `self_target`. Every one of the 26 outcome reasons is produced
   by at least one case in this file or `test_sim.nim`.
6. **Robustness** — an empty sentence, 240 runes of punctuation, a sentence that is only another
   seat's alias, a sentence containing JSON, and a sentence containing every room keyword at once all
   return a legal `Intent` and never raise.

### `tests/test_bot.nim` (bounded-orders / legality assertion on the scripted baselines)

1. **Legality and boundedness** — for seeds `[1, 7, 11, 42]` × `{all-factor, all-magpie, mixed}`, a
   full scripted episode completes with `reason == "complete"` and: `applyAction` never raises;
   **every scripted sentence parses to a non-`iNone` intent** (zero unreadable sentences — the
   baselines are a live test of the parser); no seat's coin ever goes negative; no seat ever carries
   more than 8 items; every `qty` is ≥ 1 and within stock/holdings; every sentence is ≤ 240 runes;
   scripted seats emit empty `notes`; and the whole episode runs in under 2000 ms.
2. **Baseline behaviour** — `factor` fills at least one commission on every seed by turn 12 and never
   emits `iRob`, `iHire` or `iTrade`; `magpie` emits at least one `iRob` and at least one `iTrade`
   across a 14-turn episode and fills **zero** commissions; an all-`factor` table's mean score is
   strictly greater than an all-`magpie` table's on the same seed (the competent baseline is the one
   a prompt has to beat, and the log echoes both numbers so tuning drift is visible).
3. **Fallback** — with no credentials `newLlmClient(config).disabled` is true, `decideAll` returns
   scripted sentences for all six seats with **no network call**, and the batch-spacing sleep is
   skipped (asserted on wall clock: a 14-turn disabled episode finishes in under 5 s).
4. **Reply parsing** — the JSON reply parser accepts the documented shapes, caps `action` / `say` /
   `notes` at their rune limits, rejects a missing or empty `action` as invalid (retryable), and
   treats an unreadable-but-present `action` as **valid** (not retryable).

### `tests/test_score.nim` and `tests/test_feasibility.nim`

5. **Scoring** — `score == (wealth + 3 × questPoints − 40) / 40.0` on a hand-built episode; a seat
   that only waits scores exactly `0.0`; a seat robbed of a relic scores `14/40 = 0.35` lower than
   its unrobbed counterpart on the same seed; the worked landmark in §The game reproduces **2.03**
   to 1e-9; `resultsJson` has 6 entries in every array and `wealth[i] >= coin[i]`.
6. **Feasibility oracle** — over 200 seeds × 6 seats, the greedy plan `start → cheapest shop
   stocking commission A → buy → shop stocking commission B → buy → Guildhall → hand → hand`
   costs **≤ turns − 2 = 12** turns and **≤ 40** coin. Any change to a room, an exit, a stock, a base
   value, `StartCoin` or `turns` re-runs this test; **the test is the enforcement, not the table in
   §The game** (ecos, 2026-08-23).

### `tests/test_viewer.nim`

7. **Chrome provenance and scope** — `client/chrome.css` byte-matches the starter's file up to the
   appended `/* ---------- Cogmud ---------- */` banner; `client/replay.html` and
   `replay-viewer/index.html` both contain **every** starter element id listed in §Viewer; no
   top-level `function` or `var` in the appended game block shares a name with anything the chrome
   defines above it (tandem, 2026-08-23); the appended CSS defines a rule for each of the five beat
   kinds the scrubber can emit (`rob`, `commission`, `deal`, `market`, `end`).

### End-to-end, replay and viewer (CI jobs)

8. **`docker-smoke`** (`tools/ci/docker_smoke.sh`, `<SEATS>` = **6**) — builds the production image
   and runs **one real episode** in raw docker with the certification fixture's six-seat mix and no
   `ANTHROPIC_API_KEY`, asserting the game exits 0 having written `results.json` and a replay, that
   **every player container also exits 0** (raid 0.1.3, 2026-08-23), that `num_agents` = 6 agrees
   across `certification.game_config`, `certification.players`, `certification.game_config.players`
   and `SMOKE_SEATS`, and that `results.names` / `results.scores` have 6 entries. The replay is
   copied to `dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.
9. **Strict-UTF-8 replay parse** — the same script decodes the replay bytes as **strict UTF-8** and
   parses them as JSON (`SMOKE_REQUIRE_REPLAY_JSON=1`, the default); `tests/test_sim.nim` item 11
   covers the multi-byte truncation path that would otherwise break it.
10. **Viewer smoke** — `ci.yml`'s **`wasm-viewer`** job (`needs: docker-smoke`) builds the bundle with
    `tools/build_replay_viewer.sh`, downloads the `smoke-replay` artifact and **executes** the bundle
    in headless Chromium: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
    dist/smoke/replay.json --timeout 90 --soak 15`. It passes only when the page sets
    `data-replay-loaded="true"` (or posts the `coworld-replay` `ready` envelope), never sets
    `data-replay-error`, the `#clock` / `#scorebug` readouts **differ** across the 0 % / 50 % / 100 %
    scrub positions, and uninterrupted playback keeps advancing through the soak window (cogball,
    2026-08-23; the 59-event fixture is ≈40 s of playback, so the soak cannot false-negative — ecos,
    2026-08-23). `viewer-smoke.png` and `viewer-smoke.json` are uploaded on success and failure
    alike. The bundle is **executed, not merely built**.

---

## Out of scope (v1)

- Any seat count other than 6, spectator seats, NPCs with their own policies, or seats joining or
  leaving mid-episode.
- Combat, hit points, death, healing, levelling, or any character sheet: robbery is the only
  violence and it is one deterministic comparison.
- Rooms beyond the nine authored ones, procedurally generated maps, doors, keys, locks, containers,
  vehicles, or a day/night cycle. `dark` is a static room property, not a clock.
- Crafting, item durability, item stacking limits per kind, item quality tiers, or any item property
  beyond `BaseValue`.
- Enforceable contracts of any kind beyond the hire retainer: an offer to trade is executed at
  acceptance or not at all, and everything a cog *says* is cheap talk by construction.
- Escrow, banking, credit, loans, futures, or negotiable prices with a shopkeeper — an NPC's ask and
  bid are functions of its stock, and haggling with one is not a thing.
- Commissions issued by any NPC other than Guildmaster Vell, chained or multi-stage quests, timed
  quests, quest rewards paid in coin, or a public commission board other seats can read.
- A private whisper channel, a party/guild system, a vote, or any mechanism through which two seats
  could coordinate off the room log — the integrity pins depend on every deal being public in the
  room where it is struck.
- Free-form world interaction outside the thirteen intents: no `open`, `read`, `search`, `unlock`,
  `climb`, `attack`, `eat`, `wear`. An unrecognised verb is a recorded no-op, deliberately, and the
  seat is told so.
- A second LLM pass to interpret sentences the grammar cannot read; the grammar is the whole parser,
  it runs in the wasm viewer too, and its determinism is what makes replays re-derivable.
- Cross-episode memory, reputation, item or coin carry-over between policies.
- Scoring on anything but wealth plus commission points — no reputation bonus, no exploration bonus,
  no penalty for unreadable sentences beyond the lost turn.
- Real-time play, an RL vector observation, and a live-server (`/client/replay`) replay viewer.
- Localisation, audio, a zoom/minimap panel, and any viewer feature beyond the parchment-map stage,
  the chronicle and the highlight reel described above.
