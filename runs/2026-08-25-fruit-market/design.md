# MP Fruit Market — apple farmers who crave bananas, banana farmers who crave apples, and offers that only clear when they match

**Starter: `Metta-AI/coworld-ctf` (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.**
Fruit Market is a real-time grid loop with rules written for this coworld — per-tick grid actions,
a per-tick replay, a fixed board, eight bodies walking around — which is the first row of the
starter table ("any real-time game loop, grid OR continuous physics, new rules written for this
coworld"). The Melting Pot substrate is the *inspiration*, not a binary we reproduce bit-exactly,
so this is paintbot and not `cogame-moba`. Paintbot supplies the tick loop, the sprite-protocol
board renderer, the broadcast chrome, the static wasm replay bundle, the `Dockerfile` pair and the
CI shape. **Every convention there holds here unless this note says otherwise.** Two things
paintbot does not have are ported from `Metta-AI/cogame-bullwhip`
(`/workspace/starters/cogame-bullwhip`, read and named where used): the *game-side* batched LLM
decision layer (`src/bullwhip/llm.nim`) and the thin prompt-carrying player process
(`src/bullwhip_player.nim`) — coworld-ctf has no LLM client at all (`grep -rl anthropic src/`
returns nothing). **All four viewer files come from coworld-ctf only** (see `## Viewer`).
There is no `OPEN` section: every rule the idea leaves loose is decided below, with the reason.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design), each answered:**

| pin | how Fruit Market satisfies it |
|---|---|
| starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — real-time grid loop, new rules; nothing external to port bit-exactly. |
| public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-fruit-market`, **public** — a certification prerequisite (`source-resolves` 404s on private). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | one image; `PLAYER_PROMPT="<strategy>"` vs `PLAYER_SCRIPTED=hauler\|homesteader` (`## Decisions`). Champions #1 `fruit-market-broker` (daveey) and #2 `fruit-market-ricardo` (daveey-1) are both prompt policies; the two fillers are the two scripted baselines. |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh`; no `/client/replay` viewer is declared (`## Viewer`, `## Packaging`). |
| real art, starter chrome verbatim | `scripts/art/gen_market_art.py` commits floor/water/tree/fruit/stall/cog art; `client/chrome_common.js` ships **byte-for-byte** and `client/replay_broadcast.html` is the starter's page with a game block appended (`## Viewer`). |
| legible to a casual spectator | `ROUND 4 / 12`, offer bubbles that read `3 🍎 → 2 🍌` in sprites, hunger bars over every cog, an `APPLES PER BANANA` rate chart; checked at 360 px. |
| two name spaces | anonymous cog aliases `Ash … Holt` in-game and in every prompt; policy names only spectator-side (`roster[].pol`, the roster strip, `results.names`) — `## The game` §Seats. |
| degrade, never hang; play inside 60 % of `episodeTimeoutSeconds` | ≤ 531 s worst case against a 720 s budget, deadline checked between rounds, retry-once-then-scripted, `shutdownGraceSeconds = 20` (`## Decisions`, `## Server`). |
| `num_agents` in every variant AND the cert fixture | **8**, in all four variants, in `certification.game_config`, and as `<SEATS>` in `tools/ci/docker_smoke.sh` (`## Packaging`, `## Tests`). |
| prove it in CI | sim tests, bounded-orders/legality test on both baselines, a feasibility oracle, an end-to-end episode writing a replay, a strict-UTF-8 parse, an **executed** viewer smoke (`## Tests`). |

**Source idea (verbatim, Asana idea task 1217747861534937):**

> MP Fruit Market — apple farmers who crave bananas, banana farmers who crave apples, and offers that only clear when they match
>
> Port of Melting Pot's fruit_market (+ concentric_rivers). Apple and banana trees; two farmer types — apple farmers harvest apples easily but get more reward from eating bananas, and vice versa. A hunger meter that costs stamina when empty; water crossings cost stamina too (concentric_rivers makes geography part of the bargain). Trades are posted offers — "X apples for Y bananas" — and execute automatically when two cogs within trading radius hold mirror-image offers and the inventory to cover them. Comparative advantage, bargaining, and price discovery with no words.
>
> Seats: 16 (original) — 8 for cogs
> Motive: mixed-motive trade
> Policy interface: per-tick grid actions + offer actions; LLM variant maps naturally onto a talk channel with structured offers
> Fills gap: 21 Garble is noisy-channel trade; this is clean, structured-offer trade with production roles and geography
> Integrity (anti-collusion): farmer types assigned by seed; anonymous aliases; all offers logged.
>
> Replay plan (watchability): floating offer bubbles over cogs, a live exchange-rate chart, and a hunger bar so the audience sees the stakes of a failed trade.
>
> Source: substrates fruit_market, fruit_market__concentric_rivers.

---

## The game

### Seats, aliases, names

**`num_agents = 8`.** One unambiguous number, in every manifest variant and in the certification
fixture. The idea offers "16 (original) — 8 for cogs" and **8 is the number taken**: it is the
figure the idea itself pins for cogs, it gives four apple farmers and four banana farmers (a
balanced two-sided market with real partner choice), and it keeps one decision turn at eight
parallel LLM calls, which fits inside the Bedrock sidecar's 30-requests-per-minute per-episode
ceiling with the pacing floor in `## Decisions`. Sixteen seats would double the call rate and
halve the per-seat share of the groves for no new mechanic. No variant changes `num_agents`.

| slot | in-game cog alias | body colour (paintbot `slots[].color`) |
|---|---|---|
| 0 | `Ash` | `red` |
| 1 | `Bram` | `orange` |
| 2 | `Cedar` | `yellow` |
| 3 | `Dune` | `lime` |
| 4 | `Elm` | `light blue` |
| 5 | `Fern` | `blue` |
| 6 | `Gale` | `pink` |
| 7 | `Holt` | `white` |

Aliases are fixed to slots and never rotate. They are deliberately fruit-neutral: nothing in an
alias hints at farm type.

**Farm types are assigned by seed** (the idea's anti-collusion clause). At init the sim shuffles
the fixed multiset `[apple, apple, apple, apple, banana, banana, banana, banana]` over slots 0..7
with the seeded RNG (Fisher–Yates, descending index, paintbot's `rand` stream). Every episode
therefore has exactly four of each type, and slot *n* is not a stable type across episodes. A cog
knows **its own** type and never any other cog's (`## Decisions` §observation) — another cog's
type can only be inferred from what it offers, which is the price-discovery surface.

**Two name spaces (pin).** A seat sees only aliases — its own and the others' — in every
observation and every prompt. No policy name, player name, account or model name ever reaches a
seat. The replay carries `policyNames[]` alongside `names[]`; the viewer's roster strip shows the
**policy** name for non-baseline seats (paintbot's `roster[].pol` path in
`client/chrome_common.js`), and `results.names[]` carries policy names for the platform. Both,
not either.

### The board (concentric rivers)

A **fixed** grid, `cols = 32` × `rows = 18`, cell size 48 board-px → a 1536 × 864 board. **The
whole board always fits the frame**, which is why the viewer drops `#viewpanel` (zoom bar +
minimap) entirely (`## Viewer`). Cells are `(col, row)` = `(x, y)`, origin top-left.

- **Wall**: the full border ring — `y == 0`, `y == 17`, `x == 0`, `x == 31`. Impassable.
- For every interior cell define the rectangular inset
  **`d(x,y) = min(x - 1, 30 - x, y - 1, 16 - y)`**, so `d ∈ 0..7`.
- **Water** (the two concentric rivers, each one cell wide): `d == 2` (the outer river, 72 cells)
  and `d == 5` (the inner river, 32 cells). Passable at a stamina cost; see the move rule.
- **Land zones**:
  | zone | cells | contents |
  |---|---|---|
  | `orchard` (outer) | `d ∈ {0, 1}` — 168 cells | the **apple grove**: 24 apple trees |
  | `market` (middle) | `d ∈ {3, 4}` — 120 cells | no trees; the four **stalls** |
  | `island` (inner) | `d ∈ {6, 7}` — 72 cells | the **banana grove**: 24 banana trees |

Each grove is separated from the market ring by exactly **one** river, and from the other grove
by **two**. That is the whole geography argument: meeting a counterparty costs one crossing each;
self-supplying the fruit you crave costs two each way. `concentric_rivers` is not decoration.

**Apple trees (24, all at `d == 1`, all fixed):**
`y = 2` at `x ∈ {3,6,9,12,15,18,21,24,27}` (9) · `y = 15` at `x ∈ {3,6,9,12,15,18,21,24,27}` (9) ·
`x = 2` at `y ∈ {5,8,11}` (3) · `x = 29` at `y ∈ {5,8,11}` (3).

**Banana trees (24, all in the island, all fixed):**
`y = 7` at `x ∈ {8,10,12,14,16,18,20,22}` (8) · `y = 10` at `x ∈ {8,10,12,14,16,18,20,22}` (8) ·
`x = 7` at `y ∈ {8,9}` (2) · `x = 24` at `y ∈ {8,9}` (2) · `y = 8` at `x ∈ {12,19}` (2) ·
`y = 9` at `x ∈ {12,19}` (2).

Tree cells are **impassable** (a cog harvests from an orthogonally adjacent cell). Both lists are
checked at init by `assert` (24 each, none on water, none on a wall, no duplicates) and by
`tests/test_map.nim`, which also asserts that every land cell of every zone is reachable from
every other land cell of the same zone without entering water.

**Stalls (4, fixed, in the market ring):** `north (16, 4)`, `south (16, 13)`, `west (4, 8)`,
`east (27, 8)`. A stall is a passable, drawn awning cell and has **no mechanical effect
whatsoever** — it is a Schelling point, the only way two wordless cogs can agree where to meet.
Naming a stall in an order is how a policy says "meet me there".

**Spawns.** Apple farmers spawn, in ascending slot order among apple-type seats, at
`(4,1), (11,1), (20,1), (27,1)`; banana farmers, in ascending slot order among banana-type seats,
at `(8,8), (14,8), (17,9), (23,9)`. All eight cells are land, tree-free and stall-free.

Every sim quantity is an **integer**; the RNG is paintbot's seeded stream and is used only for the
farm-type shuffle. No floats enter sim state, so a seed reproduces a replay bit-exactly (the
determinism test depends on it).

### Cogs: inventory, hunger, stamina

Every cog carries an inventory of two integers (`apples`, `bananas`), a `hunger`, a `stamina`, a
`farmType`, and at most one **posted offer**.

| constant | value | meaning |
|---|---|---|
| `invCap` | 12 | per fruit; a harvest or a trade that would exceed it is refused (`spill` event on harvest) |
| `hungerMax` / `hunger0` | 100 / 60 | hunger starts at 60 |
| `hungerDrainPeriod` | 4 | −1 hunger every 4 ticks → −180 over a 720-tick episode |
| `craveNutrition` / `ownNutrition` | 25 / 10 | hunger restored by eating the craved / own fruit; surplus above `hungerMax` is lost |
| `craveScore` / `ownScore` | **5** / **1** | points per fruit eaten (see §Scoring) |
| `eatCooldown` | 6 | a cog eats at most one fruit per 6 ticks (≤ 10 per round) |
| `staminaMax` / `stamina0` | 100 / 100 | |
| `staminaRegenPeriod` | 2 | +1 stamina every 2 ticks **while `hunger > 0`** |
| `starveDrain` | 2 | −2 stamina **per tick** while `hunger == 0`, and no regen — the idea's "hunger meter that costs stamina when empty" |
| `moveStaminaLand` | 1 | per land move |
| `moveStaminaWater` | 10 | per move that **enters** a water cell — the crossing toll |
| `harvestStamina` | 1 | per harvest |
| `moveCooldown` | 2 | ticks between moves onto land |
| `waterMoveCooldown` | 4 | ticks between moves that enter water (wading is slow) |
| `harvestCooldownOwn` | 12 | ticks between harvests of **your** fruit |
| `harvestCooldownOther` | 24 | ticks between harvests of the **other** fruit |
| `yieldOwn` / `yieldOther` | 3 / 1 | fruit per harvest — "apple farmers harvest apples easily" |
| `regrowTicks` | 60 | a harvested tree is bare for 60 ticks |
| `tradeRadius` | 3 | Chebyshev, cog-to-cog, for an offer to clear |
| `viewRadius` | 6 | Chebyshev, for what a seat observes |
| `offerMin` / `offerMax` | 1 / 6 | legal quantity on each side of an offer |

**Exhaustion.** At `stamina == 0` a cog is `exhausted`: `move` and `harvest` degrade to `wait`.
It can still **eat** and still **trade** — so a stranded, starving cog can be rescued by a
counterparty who walks to it, which is the best drama the feed produces and is deliberately kept.

### Offers, and how they clear

A cog's **posted offer** is `{give: {fruit, n}, want: {fruit, n}}` with `give.fruit != want.fruit`
(the schema admits only apple↔banana) and both `n ∈ 1..6`. It is posted at a round boundary
(`## Decisions`) and **persists across ticks and rounds** until it is replaced by a later order,
explicitly withdrawn (`"offer": null`), or executed.

An offer whose owner does not currently hold `give.n` of `give.fruit`, or whose owner would exceed
`invCap` on receipt, is **`unfunded`**: it stays visible in the book (marked `unfunded: true`,
drawn hollow in the viewer) but cannot clear. Bluffing is expressible and visible; it just does
not execute.

**Matching is exact mirror-image, as the idea states.** Offers `A` and `B` mirror iff
`A.give.fruit == B.want.fruit`, `A.give.n == B.want.n`, `A.want.fruit == B.give.fruit`, and
`A.want.n == B.give.n`. (Price-improvement matching — clearing a 3-for-2 ask against a
3-for-1 bid — was considered and rejected: it needs an arbitrary rule for splitting the surplus,
and the idea's text pins mirror-image clearing. Exact mirroring is also what makes the book worth
reading: to trade at all you must copy a counterparty's numbers, or get yours copied.)

**A cog executes at most one trade per tick and at most one trade per round**
(`tradesPerRound = 1`); an executed offer is **consumed** on both sides and the cog is offerless
until its next order. One posted price per round is therefore a real commitment, which is what
makes bargaining mean anything.

### The exact tick resolution order

One episode = `rounds = 12` × `ticksPerRound = 60` = **720 ticks**. Playback is 24 fps, so a full
replay is 30 s of video (comfortably longer than the viewer soak gate).

Every tick runs these **nine** steps in this order. Within a step, seats resolve in **ascending
slot order** unless the step names another order. All reads inside a step use the state as it
stood at the start of that step unless the step says otherwise.

1. **Regrow.** Every bare tree's `bareFor` counter decrements by 1; at 0 the tree is ripe again.
2. **Kernel intent.** Each cog's kernel (below) derives this tick's grid action —
   `move_n | move_s | move_e | move_w | harvest | wait` — from its standing order and the current
   state. A cog whose move or harvest cooldown is still running, or which is `exhausted`, emits
   `wait` instead.
3. **Harvest** (slot order). A `harvest` picks the first ripe adjacent tree in N, E, S, W order.
   Yield is `yieldOwn = 3` if the tree's fruit is the cog's farm type, else `yieldOther = 1`;
   the amount above `invCap` is dropped and emits `spill`. The tree becomes bare for
   `regrowTicks = 60`. The cog pays `harvestStamina = 1` and sets its harvest cooldown to
   `harvestCooldownOwn = 12` (own fruit) or `harvestCooldownOther = 24` (other fruit).
   No adjacent ripe tree → `wait`, no cost.
4. **Move** (slot order), against the *live* board. A move is legal into a non-wall, non-tree cell
   not occupied by another cog (a cell a lower-numbered seat already moved into this tick counts
   as occupied). **The water-crossing cost is charged here**: entering a water cell costs
   `moveStaminaWater = 10` stamina and sets the cooldown to `waterMoveCooldown = 4`; entering a
   land cell costs `moveStaminaLand = 1` and sets it to `moveCooldown = 2`. A move whose stamina
   cost exceeds the cog's current stamina is **refused** (degrades to `wait`) — you cannot enter
   the river on 6 stamina. Entering water emits `cross`.
5. **Offer book update.** On a round-boundary tick (`tick mod ticksPerRound == 0`) the round's new
   orders are applied: each seat's offer is replaced, withdrawn, or left standing per its order,
   emitting `offer` or `withdraw`. On every tick, each live offer's `unfunded` flag is
   recomputed from current inventories.
6. **Offer matching and execution** — the deterministic sweep:
   1. Build the candidate list: every unordered pair `{i, j}`, `i < j` by slot, where both offers
      are live and funded, the two offers mirror exactly, and `chebyshev(cell_i, cell_j) <= 3`,
      and neither side would exceed `invCap` on receipt.
   2. **Sort the candidates** by, in order: **(a)** total volume `give_i.n + give_j.n`
      **descending** (the biggest trade on the board clears first); **(b)** Chebyshev distance
      **ascending** (the closest pair next); **(c)** lower slot index ascending; **(d)** higher
      slot index ascending. Keys (c) and (d) identify a pair uniquely, so this is a **total
      order** and the tie-break is complete.
   3. Sweep in that order. Execute a pair iff neither cog has traded yet **this tick** and neither
      has traded yet **this round**. Executing swaps the goods, clears both offers, marks both
      cogs traded, emits `trade`, and appends a print to the public tape.
7. **Eat** (slot order). A cog eats one fruit if its `eatCooldown` has expired and its order's
   `eat` policy admits a fruit it holds: `crave` → only the craved fruit; `any` → the craved fruit
   if held, else its own; `none` → nothing. Eating adds `craveNutrition = 25` or
   `ownNutrition = 10` hunger (capped at 100), adds `craveScore = 5` or `ownScore = 1` to the
   score, and emits `eat`.
8. **Hunger and stamina.** On ticks where `tick mod hungerDrainPeriod == 0` and `tick > 0`,
   `hunger -= 1` (floored at 0; the 0 crossing emits `starve` once per cog per crossing). Then:
   if `hunger == 0`, `stamina -= starveDrain (2)` (floored at 0; reaching 0 emits `exhausted`);
   else on ticks where `tick mod staminaRegenPeriod == 0`, `stamina = min(staminaMax, stamina + 1)`.
9. **Record.** Append this tick's state frame, its events and the exchange-rate series row to the
   replay.

At a round boundary the sim additionally closes the round accounting, emits `round`, checks the
end conditions, and — if the episode continues — blocks for the next batched decision
(`## Decisions`).

### Where per-tick actions come from: the standing order and the courier kernel

The sim's policy interface is per-tick grid actions plus offer actions, exactly as the idea says.
No LLM can emit 720 actions per seat, so once per **round** (60 ticks) each seat submits a
**standing order** and a deterministic **kernel** turns it into the per-tick action stream for
that round. This is the batched cadence that worked in cogame-hive, cogame-ecos and
cogame-chemistry: 96 LLM calls per episode instead of 5 760.

An order is `{job, fruit, stall, eat, offer, say, notes}` (schema and caps in `## Decisions`).
Given the order and the current tick's state the kernel emits:

1. **`harvest`** — BFS to the nearest cell orthogonally adjacent to a **ripe** tree of `fruit`
   (default: the cog's own type), preferring land-only paths (see below), and `harvest` on
   arrival. If no tree of that fruit is ripe anywhere, walk to the nearest tree of that fruit and
   `wait` beside it.
2. **`market`** — BFS to the named `stall` cell (default: the stall with the shortest path) and
   `wait` within Chebyshev 1 of it, so the offer can clear against anyone who comes.
3. **`trek`** — BFS to the nearest cell adjacent to a ripe tree of `fruit` **in the far grove**
   (the grove that is not the cog's own), crossing water as needed, and `harvest` on arrival.
   This is the autarky move and it is what the rivers tax.
4. **`rest`** — `wait` in place (no move cost; stamina regenerates normally).

BFS is Dijkstra over passable cells with `cost(land) = 1` and `cost(water) = 8`, neighbour
expansion in N, E, S, W order, ties resolved by that expansion order — so paths are unique and
deterministic, and a route only crosses a river when the detour is genuinely longer (for `trek`
it always is). Other cogs are not obstacles for path *planning*, only for the move itself.

### Scoring — fruit eaten, weighted by craving, higher is better

- **Seat score `S_i` = 5 × (craved fruit eaten) + 1 × (own fruit eaten)**, an integer ≥ 0.
- **Sign: higher is better.** `results.win[i] = (S_i == max(S))`; ties mark multiple winners,
  which is correct for a mixed-motive market and needs no tiebreak.
- **The league ranks by `results.scores`** (the platform's mean over episodes). Nothing else is
  ranked; trades, volume, crossings and starvation ticks are reported for the viewer and for
  analysis and are **not** in the score.

The arithmetic that makes trade the dominant strategy, not a moral preference:

- Production: in your own grove, ~3 harvests per round (12-tick cooldown plus walking between
  trees at `regrowTicks = 60`) → **~9 of your own fruit per round**.
- Eating your own stock: capped by `eatCooldown` at 10 fruit/round → at most **10 points/round**.
- Trading: one cleared 6-for-4 mirror gives 4 craved fruit = **20 points**, plus the rest of the
  eat budget in your own fruit → **~24 points/round**. Even the baselines' canonical 3-for-2
  gives 2 craved (10) + 8 own (8) = 18.
- Autarky across the rivers (`trek`): the far grove pays `yieldOther = 1` on a
  `harvestCooldownOther = 24` cooldown — **six times less productive per tick** — and the round
  trip costs 40 stamina in tolls plus ~80 ticks of walking. It yields ~1.5 craved fruit per two
  rounds ≈ **4 points/round**.

So comparative advantage is priced into the constants, and the failure mode the audience should
see — a cog that hoards for a trade that never clears (`eat: none`), starves, drops to 0 stamina
and cannot walk home — is exactly the idea's "stakes of a failed trade".

The idea's integrity clause needs no extra machinery: farm types are assigned by seed, aliases are
anonymous and fruit-neutral, and **every offer, withdrawal and trade is an event in the replay**
(`## Sim module` §event vocabulary), so any price collusion is auditable after the fact and is
in-band skill during play.

### End conditions and `results.reason`

The episode ends at the FIRST of these, all checked at a **round boundary**:

| condition | `results.reason` | `results.ending` | scores |
|---|---|---|---|
| 12 rounds played | `complete` | `round_limit` | as computed |
| every seat has `hunger == 0` **and** `stamina == 0` at a round boundary | `complete` | `famine` | as computed; unplayed rounds add nothing |
| wall clock passes the play deadline (0.6 × `episodeTimeoutSeconds` = **720 s**) | `deadline` | `deadline` | rounds played are scored; the rest add nothing |
| no seat connected within `playerConnectTimeoutSeconds = 180` | `forfeit` | `forfeit` | all zero; results + replay are still written |

Those three — **`complete`, `deadline`, `forfeit`** — are the only legal `results.reason` values.
A market that starves itself is a *completed game of Fruit Market*, not an error, so it reports
`complete` and carries the detail in `results.ending`; phase 60's check 4 therefore passes on a
dead market, as it should. `deadline` is admissible (it means the LLM was slow, not that the game
broke), but the arithmetic in `## Decisions` is sized so it should not fire.

### Feasibility gates (the oracle, not this table)

The numbers above are **design targets derived from the constants, not measurements**. The
enforcement is `tests/test_feasibility.nim`, run over seeds 1..12 on all four variants:

- **(a) The baselines make a market.** All-`hauler`: ≥ 10/12 seeds end `complete`/`round_limit`,
  ≥ 24 trades execute, every seat scores ≥ 60, and no seat spends more than 120 ticks
  `exhausted`. This is what makes certification, `docker-smoke` and all-filler league episodes
  end `complete`.
- **(b) Trade beats autarky.** In a 4 × `hauler` + 4 × `homesteader` room, the haulers' mean score
  is ≥ 1.5 × the homesteaders' mean score.
- **(c) Geography bites.** On `deep-rivers`, the homesteaders' mean score is strictly below their
  `open-market` mean, and the haulers' lead over them is strictly larger than on `open-market`.
- **(d) Reading the book is viable.** In a 4 × `hauler` + 4 × test-only `mirror` room (a kernel
  that posts the exact mirror of the highest-volume funded offer within radius, else the canonical
  3-for-2), the `mirror` mean is ≥ the `hauler` mean. `mirror` lives only in the test; it is not a
  shipped policy.

**If a gate fails, repair constants in this order and re-run — no design bounce is needed:**
(a) `regrowTicks 60 → 40`, then `harvestCooldownOwn 12 → 8`; (b) `moveStaminaWater 10 → 14`, then
`harvestCooldownOther 24 → 32`; (c) `deep-rivers` `moveStaminaWater 18 → 24`;
(d) `tradeRadius 3 → 4`. Any change to a constant in this note re-runs the oracle.

---

## Decisions: LLM with scripted fallback

Both policies ship in the **same image** from day one, env-switched:
`PLAYER_PROMPT="<strategy text>"` makes a seat an LLM seat; `PLAYER_SCRIPTED=hauler|homesteader`
makes it a scripted seat; a seat that sets neither is `PLAYER_SCRIPTED=hauler`. A scripted policy
seated as a champion is a failure state. **A policy is a prompt.**
`src/fruit_market_player.nim` (a fork of `cogame-bullwhip/src/bullwhip_player.nim`) is one thin
process that connects, sends `{"type":"prompt","prompt":…,"scripted":…}` and then only listens.
All decision-making happens in the **game** container (`src/fruit_market/llm.nim`, forked from
`cogame-bullwhip/src/bullwhip/llm.nim`) — which is what makes one parallel batch per turn
possible, and is why the coworld secret must be on the *game* runnable (hive, 2026-08-23).

### Cadence, batching, and the wall-clock budget

One **turn = one round = 60 ticks**. At each round boundary the game issues **all eight seats'
requests as ONE parallel batch** (`curly.makeRequests`, bullwhip's `decideAll`) — never
sequentially, and never one seat at a time.

```
per round:     1 batch of 8 requests, llmTimeoutSeconds = 20
worst case:    20 s (batch) + 20 s (one retry batch)          = 40 s
12 rounds:     12 x 40 s                                      = 480 s
+ sim:         720 ticks x ~1 ms (8 Dijkstra/tick, 576 cells) ~   0.7 s
+ connect:     player connect grace (typical)                 <=  30 s
+ shutdown:    shutdownGraceSeconds                           =   20 s
total worst:   ~531 s   <   720 s  ( = 0.6 x episodeTimeoutSeconds 1200 )
typical:       max(minTurnSeconds 18, ~8 s batch) x 12         ~ 216 s
```

`minTurnSeconds = 18` floors the spacing between **batch starts**, so the episode issues at most
8 requests / 18 s = **26.7 requests per minute**, under the Bedrock sidecar's 30 rpm per-episode
ceiling that bit cogame-raid. Requests per episode: 96, plus ≤ 96 retries. It is a floor, not a
sleep on the critical path — the loop keeps stepping sim ticks while it waits. All LLM deadlines
are **whole seconds**: curly's `CURLOPT_TIMEOUT` floors sub-second deadlines to whole seconds
(paintball, 2026-08-25), and `sim_config` rejects a sub-second value. The play deadline
(0.6 × `episodeTimeoutSeconds`; the game container is **not** given `COWORLD_TIMEOUT_SECONDS`, so
1200 is assumed unless that env var is present) is tested **between rounds**; hitting it calls
`endEarly()` and settles with `reason: "deadline"`.

### The observation each seat gets

Sent as the `state` frame at every round boundary and rendered into the user prompt. Every number
below is visible to that seat; **nothing else is**. The split is: **static geography is public**
(the board never changes and is in the rules block), **dynamic state is local** (radius 6), and
**executed prices are global** (a market's prints are public).

```json
{"type":"state","protocol":"fruit-market.player.v1","slot":3,"name":"Dune",
 "round":4,"rounds":12,"ticksPerRound":60,"tick":180,
 "board":{"cols":32,"rows":18,"variant":"concentric-rivers"},
 "you":{"cell":[16,5],"zone":"market","farmType":"apple","craves":"banana",
        "apples":9,"bananas":1,"hunger":52,"stamina":74,"score":41,
        "exhausted":false,"tradesThisEpisode":3,
        "offer":{"give":{"fruit":"apple","n":3},"want":{"fruit":"banana","n":2},
                 "unfunded":false,"postedRound":3},
        "lastOrder":{"job":"market","stall":"north","eat":"crave","source":"llm"}},
 "view":{"radius":6,
         "map":["#####........","..~~~~~......","… 13 rows of 13 chars …"],
         "legend":{".":"land","~":"water","#":"wall","A":"apple tree (ripe)",
                   "a":"apple tree (bare)","B":"banana tree (ripe)",
                   "b":"banana tree (bare)","S":"stall","0-7":"a cog, by slot"},
         "cogs":[{"alias":"Ash","slot":0,"cell":[17,6],"dist":1,
                  "offer":{"give":{"fruit":"banana","n":2},"want":{"fruit":"apple","n":3},
                           "unfunded":false},
                  "mirrorsYou":true},
                 {"alias":"Gale","slot":6,"cell":[13,3],"dist":3,"offer":null,
                  "mirrorsYou":false}],
         "ripeTrees":[{"fruit":"apple","cell":[15,2],"dist":3}]},
 "stalls":[{"name":"north","cell":[16,4],"dist":1},{"name":"south","cell":[16,13],"dist":8},
           {"name":"west","cell":[4,8],"dist":12},{"name":"east","cell":[27,8],"dist":11}],
 "tape":[{"t":163,"give":"apple","giveN":3,"want":"banana","wantN":2,
          "applesPerBanana":150,"a":"Ash","b":"Cedar"},
         "… the last 8 executed trades, most recent last, whole map …"],
 "history":[{"round":3,"score":11,"hunger":58,"stamina":80,"trades":1,
             "harvested":8,"eaten":3,"crossings":1,"marketRate":150}, "…"],
 "notes":"…your own notes from last round…",
 "rules":{"scoring":"5 points per craved fruit you eat, 1 per own fruit; higher is better",
          "yourFruit":"apple","cravedFruit":"banana",
          "harvest":"3 apples per harvest every 12 ticks in your grove; 1 banana per harvest every 24 ticks in the island",
          "trade":"an offer clears only against its EXACT mirror (their give == your want, same numbers) within 3 cells, once per round per cog",
          "water":"entering a river cell costs 10 stamina and 4 ticks",
          "hunger":"-1 every 4 ticks; at 0 you lose 2 stamina per tick and cannot move or harvest at 0 stamina",
          "eat":"one fruit per 6 ticks; banana +25 hunger, apple +10 hunger",
          "geography":"your grove is the outer ring, bananas grow on the inner island, the market ring with the four stalls is one river from each",
          "caps":{"inventory":12,"offerN":[1,6],"tradeRadius":3,"viewRadius":6}}}
```

- **Visible:** your own cell, zone, farm type, craved fruit, both inventories, hunger, stamina,
  score, exhaustion, your standing offer and last order; a 13 × 13 local ASCII map centred on you
  (terrain, walls, ripe/bare trees, stalls, cog slots); for every cog within radius 6 its alias,
  slot, cell, distance, **posted offer** and a precomputed `mirrorsYou` flag; the ripe trees inside
  the view; the four stalls with your path distance to each; the global **tape** of the last 8
  executed trades (tick, both sides, `applesPerBanana` × 100); your own per-round history; your
  private notes; and the full rule/constant block for this variant.
- **Hidden:** every other cog's **farm type**, inventory, hunger, stamina, score, notes, prompt,
  policy name, player name and account; any cog or offer outside radius 6; the tree-ripeness state
  outside the view; the RNG seed; the farm-type shuffle; anything about the league.
- **There is no inter-cog talk channel.** The idea's line is "price discovery with **no words**",
  so the reply's `say` field is **spectator-only**: it is drawn in the viewer feed and recorded in
  the replay, and is *never* delivered to another seat. The offer *is* the message; the four
  named stalls are the only meeting protocol. (The idea's "LLM variant maps naturally onto a talk
  channel with structured offers" is satisfied by the structured-offer channel itself — the
  `offer` field is that channel, and it is visible to everyone within radius.)

### The reply schema

The model must answer with exactly one JSON object whose first character is `{`:

```json
{"job":"market","stall":"north","eat":"crave",
 "offer":{"give":{"fruit":"apple","n":3},"want":{"fruit":"banana","n":2}},
 "say":"mirroring Ash at the north stall - 3 apples for 2 bananas",
 "notes":"Ash is a banana farmer and posts 2-for-3 every round; Gale never funds its offer"}
```

| field | type | cap / range | on violation |
|---|---|---|---|
| `job` | string enum | `harvest` \| `market` \| `trek` \| `rest` | missing or not in the enum → **invalid reply** |
| `fruit` | string enum | `apple` \| `banana` | optional; used by `harvest` and `trek`. Absent → the cog's own fruit for `harvest`, the craved fruit for `trek`. Unknown value → **invalid reply** |
| `stall` | string enum | `north` \| `east` \| `south` \| `west` | optional; used by `market`. Absent → the stall with the shortest path. Unknown value → **invalid reply** |
| `eat` | string enum | `crave` \| `any` \| `none` | absent → `any`. Unknown value → **invalid reply** |
| `offer` | object or `null` | `{"give":{"fruit","n"},"want":{"fruit","n"}}`; both `fruit` in the enum, `give.fruit != want.fruit`, both `n` integers **1..6** | `null` withdraws the standing offer; the key being **absent** leaves the standing offer untouched. `n` outside 1..6 is **clamped** to the range and the `offer` event records `"clamped":true`. `give.fruit == want.fruit`, a non-integer `n`, or an unknown fruit → **invalid reply** |
| `say` | string | **80 characters** | truncated |
| `notes` | string | **320 characters** | truncated |

Extra keys are ignored. **Truncation is on rune boundaries**, never bytes: `cleanText(text, limit)`
= `strip` → if `runeLen > limit`, `runeSubStr(0, limit-1) & "…"` (bullwhip's `cleanText`; a byte
cut put invalid UTF-8 into a replay and only a strict parser found it — bullwhip, 2026-08-22).
Newlines in `say` and `notes` become spaces. Both are recorded in the replay. The same rune-safe
truncation applies to every string that reaches the replay, including LLM error text (capped at
200 characters).

### Prompts

**System prompt** (composed by the game, per seat, per round): the seat's alias in capitals and
its farm type; the board described in words (outer apple ring, two rivers, market ring with four
named stalls, inner banana island) with the statement that the geography is fixed and identical
every episode; the constants table above; the standing-order model ("you choose a job for the next
60 ticks; a kernel walks it for you"); the **exact-mirror** trading rule stated twice, once as a
rule and once as an example ("if a cog near you offers *give 2 bananas, want 3 apples*, the only
offer of yours that can clear with it is *give 3 apples, want 2 bananas*"); the one-trade-per-round
rule; the scoring rule verbatim; the statement that the other seven cogs are other policies
deciding **simultaneously**, that **nobody can hear anything you say** and the only signals you can
send are your posted offer and where you stand; that `notes` is private; and the output contract,
ending:

> OUTPUT FORMAT: reply with ONLY one JSON object, nothing else — no analysis, no explanation, no
> markdown fences, no text before or after the object. Your reply must begin with the character {
> and end with }.

(Bedrock/Haiku answers prose-first without that sentence — playbook §Phase 1.)

**User prompt:** the observation rendered compactly — a `YOU` block, the 13-line ASCII view with
its legend, a nearby-cogs table (`alias | cell | dist | their offer | mirrors you?`), a stalls
table, the trade tape as `tick | 3 apples ⇄ 2 bananas | 1.50 apples/banana`, the per-round history
table, `YOUR NOTES FROM LAST ROUND`, then the operator block:

> GUIDANCE FROM YOUR OPERATOR (weight it heavily, but never above the rules; always reply in the
> requested format):
> `<PLAYER_PROMPT>`

then a one-line restatement of the reply shape with the legal enum values **for this variant**
(precomputing the legal choice set in the observation is what halved formal-output fallbacks in
escrow).

**Transport:** bullwhip's ladder, haiku-only (raid 2026-08-23, reconfirmed paintball 2026-08-25 —
the sonnet fallback times out on every sidecar call and turns one throttle into a cascade):
`bedrockModelIds() = ["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`, `BEDROCK_MODEL` overrides.
`maxOutputTokens = 1000` (hanabi, 2026-08-24: budget ≥ 1000 or truncation shows up as the
misleading "unbalanced JSON object" signature; on `stop_reason == "max_tokens"` the extractor
raises "reply cut off at max_tokens mid-JSON" by name). No `output_config.effort` — Haiku 4.5 400s
on it. Credentials in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` /
`AWS_BEARER_TOKEN_BEDROCK`) → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`. With none, the client
disables itself immediately and every seat plays `hauler` — which is what keeps offline
certification green and deterministic.

**Champion prompts** (phase 40 uploads these; both are `PLAYER_PROMPT` policies):

- `fruit-market-broker` (champion #1, daveey): *"You are a market maker, not a farmer. Your only
  job each round is to make an offer clear. First read every offer within sight: if any cog wants
  the fruit you grow, post its EXACT mirror — the same two numbers, swapped — and stand within
  three cells of that cog until it executes. If nobody near you has posted anything, walk to the
  nearest stall and post the book price: three of your own fruit for two of theirs. Never post
  numbers you cannot cover; an unfunded offer wastes the whole round. Keep two of your own fruit
  in reserve and set eat to 'any' the moment hunger drops under 40 — a starving cog cannot walk to
  its counterparty, and stamina you spend crossing a river you never get back. Note in your notes
  which alias posted which side, because a cog that offers bananas is a banana farmer and will be
  there again next round."*
- `fruit-market-ricardo` (champion #2, daveey-1): *"You believe in comparative advantage and you
  never cross two rivers to pick a fruit you could buy. Your grove pays three fruit a harvest; the
  far grove pays one, at half speed, for twenty stamina of tolls — so trek only if two full rounds
  have passed with no trade and nobody near you holds a live offer. Build a stock of at least six
  of your own fruit, then go to the busiest stall you can see on the tape and post SIX for FOUR;
  big mirrors clear before small ones on the same tick, so size is an advantage when someone can
  match it. If two rounds pass without a fill, drop to the three-for-two book price that everyone
  else uses, and take it. Watch the tape: if apples per banana has been rising, hold your apples a
  round; if it is falling, sell now."*

### Scripted baselines (both fieldable, both league fillers)

`hauler` — the working baseline, the league's first filler, and the fallback every failed LLM
decision lands on. At each round boundary, purely from the observation:

1. `eat` = `"any"` if `hunger <= 45`, else `"crave"`.
2. If `inv[ownFruit] < 3` → `{"job":"harvest","fruit":<own>}`, `offer` = `null`.
3. Else → `{"job":"market","stall":<the stall with the shortest path; ties north, east, south,
   west>}` with the **canonical book offer**, which depends only on the cog's own farm type:
   an apple farmer posts `give 3 apple / want 2 banana`; a banana farmer posts
   `give 2 banana / want 3 apple`. These two are exact mirrors of each other by construction, so
   any two haulers of opposite type that meet within three cells always trade. The canonical price
   is therefore **1.50 apples per banana**, and it is the price an LLM seat must read off the book
   to trade with fillers at all.
4. `say` = `"3 apples for 2 bananas"` / `"2 bananas for 3 apples"`; `notes` = `""`.

`homesteader` — the autarky foil, the second filler, and the reason the rivers exist. It never
trades (`offer` is always `null`):

1. `eat` = `"crave"` if it holds craved fruit, else `"any"`.
2. If `stamina < 25` → `{"job":"rest","eat":"any"}`.
3. Else if `inv[ownFruit] < 4` → `{"job":"harvest","fruit":<own>}`.
4. Else → `{"job":"trek","fruit":<craved>}`.
5. `say` = `"I grow my own"`; `notes` = `""`.

Every field either baseline emits is inside its declared enum by construction, and every offer it
posts is funded at the moment of posting; both are asserted in `tests/test_baseline.nim`.

### Degrade, never hang

- Batch timeout `llmTimeoutSeconds = 20` (whole seconds). On transport error, non-2xx, refusal,
  `max_tokens` before any `{`, unparseable JSON, or any **invalid reply** in the table above, that
  seat alone is retried **once** in the same round's retry batch, with the appended hint *"Your
  previous reply was invalid. Respond with ONLY the requested JSON object, using one of the listed
  job, fruit, stall and eat values, and offer quantities between 1 and 6."*
- Still failing → that seat plays the **`hauler` order** for that round, logged as
  `fruit-market llm: seat N falling back to scripted order` and recorded on the `order` event as
  `"source":"fallback"`. `decideAll` never raises; the episode always advances.
- 401/403 disables the client for the rest of the episode (all seats scripted from then on); 429 is
  logged and the seat is retried in the next round's batch.
- A seat that never connected, or whose socket dies mid-episode, plays `hauler` for every remaining
  round. The episode never waits on a socket beyond `playerConnectTimeoutSeconds = 180` at the
  start and never blocks on one mid-episode. Registration is **adaptive**: the lobby returns as
  soon as every connected socket has registered (commons-family, 2026-08-24), and an
  unappliable registration is **held and re-sent by the player for ~10 s** rather than dropped
  (paintball, 2026-08-25 — a dropped registration silently made a champion seat play scripted).
- **How the episode settles early:** the play deadline is checked at every round boundary; hitting
  it calls `endEarly()`, which stops the round loop, scores the rounds actually played, emits
  `end` with `reason: "deadline"`, writes `results.json` and the replay, and then — as
  cogame-lantern taught — keeps `/healthz` and `/global` answering for `shutdownGraceSeconds = 20`
  before `quit(0)`, because hosted certification pings the global websocket **after** the player
  pods start.

---

## Sim module

New code lives in `src/fruit_market/`, mirroring paintbot's split (`src/ctf/`). What is forked,
what is kept, and what is deleted — by path:

| paintbot path | fruit-market | note |
|---|---|---|
| `src/ctf/sim_types.nim` | `src/fruit_market/sim_types.nim` | fork: `GameVersion`, the flatty wire types, the constants above. Field order is sacred, same as paintbot. |
| `src/ctf/sim.nim` | `src/fruit_market/sim.nim` | fork: the tick loop and the nine numbered steps replace the CTF gameplay core. |
| `src/ctf/sim_config.nim` | `src/fruit_market/sim_config.nim` | fork: `GameConfig` lifecycle + `config.update`; fields = the config schema in `## Packaging`; rejects sub-second LLM deadlines. |
| `src/ctf/sim_state.nim` | `src/fruit_market/sim_state.nim` | fork: logging, `gameHash`, event emission, spawn placement, the seeded farm-type shuffle. |
| `src/ctf/arena.nim` | `src/fruit_market/board.nim` | heavily reduced fork: the **fixed** 32×18 grid (walls, the two rivers by `d(x,y)`, the 48 trees, the 4 stalls, the 8 spawns) and the weighted Dijkstra the kernel uses. The terrain generator, `mapSpec`, symmetry, validators, pixel queries and `map_pool` are **deleted** — Fruit Market has one authored board per variant. |
| `src/ctf/global.nim` | `src/fruit_market/global.nim` | fork, heavily reduced: keep the sprite-protocol emitter, layer/object pooling, the chrome `TextMessage` smuggling and `boardRenderScaleFor`. **Delete** fog-of-war/FOV, first-person PiP, rig art, grenade/spray/shield/barrier families, endzone bakes, perks and handicaps. |
| `src/ctf/broadcast.nim` | `src/fruit_market/broadcast.nim` | fork: `BroadcastTracker` + `buildStateJson` keep their shape; `teams` becomes the two guilds, `roster` the eight cogs, `lead` the exchange-rate series. |
| `src/ctf/events.nim` | `src/fruit_market/events.nim` | fork: the event vocabulary below (same `jsonRow`/`eventsJsonl` shape and the same "live emission and re-simulation must be byte-identical" rule). |
| `src/ctf/replays.nim`, `src/ctf/replay_runtime.nim` | `src/fruit_market/replays.nim` | rewritten: Fruit Market records **state frames**, not inputs (below). |
| `src/ctf/server.nim` | `src/fruit_market/server.nim` | fork of the route/artifact/shutdown skeleton; the player protocol becomes bullwhip's JSON frames. |
| `src/ctf/labels.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `roster.nim` | — | deleted. No articulated rigs, no perk roster, no generated terrain. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | kept, forked | still emits `window.CTF_WIRE={…}`. **The global keeps its name**: `client/chrome_common.js` reads `window.CTF_WIRE` at its line 72 and that file ships byte-for-byte, so renaming the global would force a byte change in a file that must not change. `Dockerfile.replay-viewer`'s `grep -q '^window.CTF_WIRE={'` assertion is kept for the same reason. |
| `tools/` probes, `caos*`, `arena/` wit bindings, `client/league_replayer.html`, `tools/map_editor*`, `tools/record_*.sh` | — | deleted. Keep `tools/build_replay_viewer.sh` and add `tools/ci/`. |

New files: `src/fruit_market/kernel.nim` (the four jobs + weighted Dijkstra),
`src/fruit_market/market.nim` (the offer book, the funded check and the sorted matching sweep),
`src/fruit_market/llm.nim` (from `cogame-bullwhip/src/bullwhip/llm.nim`),
`src/fruit_market/scripted.nim` (the two baselines), `src/fruit_market.nim` (entrypoint, forked
from `src/ctf.nim`: seed randomisation **before** `config.update`, same sentinel handling),
`src/fruit_market_player.nim` (from `cogame-bullwhip/src/bullwhip_player.nim`).

`tools/build_replay_viewer.sh` is paintbot's with the image tag renamed
(`cogame-fruit-market-replay-viewer-build`), the `docker cp` source path changed to
`/workspace/fruit-market/replay-viewer/dist/.`, **and the inherited bug fixed**: `mkdir -p` the
output parent before the containment check, because the hook `cd`s into a parent that
`coworld build` pre-creates and CI does not (ecos, 2026-08-23).

**Emscripten guard (chemistry, 2026-08-25):** `os.getAppDir` has no emscripten implementation and
dies with `value out of range: -1` *before* any fallback runs. Every `gameDir()`-style lookup in
the forked code is wrapped in `when not defined(emscripten)` and tries the working directory
first.

### Event vocabulary (the replay's `events[]`)

One JSON row per event; `t` = tick, `seat` = slot, `fr` = fruit (`"apple"`/`"banana"`).

| `k` | fields | when |
|---|---|---|
| `harvest` | `t, seat, fr, n, x, y` | step 3, a successful harvest |
| `spill` | `t, seat, fr, lost` | step 3, the part of a yield above `invCap` |
| `cross` | `t, seat, x, y, stamina` | step 4, a move that entered water |
| `offer` | `t, seat, give, giveN, want, wantN, clamped` | step 5, an offer posted or replaced |
| `withdraw` | `t, seat` | step 5, an offer withdrawn |
| `unfunded` | `t, seat, reason ("stock"\|"full")` | step 5, a live offer became unfundable |
| `trade` | `t, a, b, aGive, aGiveN, bGive, bGiveN, applesPerBanana, x, y, dist` | step 6, an executed pair (`a` < `b` by slot) |
| `eat` | `t, seat, fr, craved (bool), hunger, points` | step 7 |
| `starve` | `t, seat` | step 8, hunger reached 0 |
| `exhausted` | `t, seat` | step 8, stamina reached 0 |
| `order` | `t, seat, round, job, fr, stall, eat, offer{…}, source (`llm`\|`retry`\|`fallback`\|`scripted`), say, notes, latencyMs` | one per seat per round boundary |
| `round` | `t, round, scores[8], hunger[8], stamina[8], trades, volume, rateX100` | at each round close |
| `famine` | `t` | the famine end condition latched |
| `end` | `t, reason, ending, scores[8]` | terminal |

Volume per episode: ~350 `harvest`, ~700 `eat`, ~96 `offer`, ≤ 96 `trade`, 96 `order`, 12 `round`,
plus incidentals — under 1 500 rows. `notes` is recorded (it makes an LLM seat's reasoning
auditable) and drawn only in the feed's expanded row; `say` is the headline. Both are already
rune-truncated. Every offer and every trade being an event is what discharges the idea's "all
offers logged" integrity clause.

### The replay file (`fruit-market.replay.v1`)

**Strict UTF-8 JSON, one document.** Fruit Market records *state*, not inputs, so playback never
re-simulates, a seek is an array index, and there is no native/wasm divergence to chase (which is
also why `#mmwarn` and `ctf_mismatch_tick` are dropped).

```json
{"protocol":"fruit-market.replay.v1","game":"fruit-market","gameVersion":"1",
 "seed":1234567,
 "names":["Ash","Bram","Cedar","Dune","Elm","Fern","Gale","Holt"],
 "policyNames":["fruit-market-broker","fruit-market-hauler","…8…"],
 "colors":["red","orange","yellow","lime","light blue","blue","pink","white"],
 "farmTypes":["apple","banana","banana","apple","apple","banana","apple","banana"],
 "config":{"variant":"concentric-rivers","cols":32,"rows":18,"cell":48,
           "rounds":12,"ticksPerRound":60,
           "water":[[3,3],[4,3],"…every river cell…"],
           "trees":[{"fr":"apple","x":3,"y":2},"…48…"],
           "stalls":[{"name":"north","x":16,"y":4},"…4…"],
           "spawns":[[4,1],[11,1],"…8, in slot order…"],
           "invCap":12,"hungerMax":100,"hunger0":60,"hungerDrainPeriod":4,
           "craveNutrition":25,"ownNutrition":10,"craveScore":5,"ownScore":1,
           "eatCooldown":6,"staminaMax":100,"staminaRegenPeriod":2,"starveDrain":2,
           "moveStaminaLand":1,"moveStaminaWater":10,"moveCooldown":2,
           "waterMoveCooldown":4,"harvestCooldownOwn":12,"harvestCooldownOther":24,
           "yieldOwn":3,"yieldOther":1,"regrowTicks":60,"tradeRadius":3,
           "viewRadius":6,"offerMin":1,"offerMax":6},
 "frames":[{"t":0,
            "c":[4,1,0,0,60,100,0,0, "…8 octets x,y,apples,bananas,hunger,stamina,score,flags…"],
            "o":[3,2,1,0, "…8 quads giveFruitId,giveN,wantN,unfunded; giveFruitId -1 = no offer…"],
            "r":[0,60,0, "…48 tree bareFor counters…"]}, "…720 frames…"],
 "series":{"rate":[[0,150],[1,150],"…one row per tick: tick, apples-per-banana x100…"]},
 "beats":[{"t":60,"k":"round","n":1},{"t":163,"k":"firsttrade"},
          {"t":402,"k":"starve","seat":6},{"t":720,"k":"gameover"}],
 "events":[ "… the rows above …" ],
 "results":{ "… the results.json object verbatim …" }}
```

- **Self-sufficient by construction.** Aliases, policy names, body colours, farm types, the full
  board geometry (water cells, tree cells, stalls, spawns), every rule constant, the seed, per-tick
  state, the exchange-rate series, the beat timeline, every event and the final results all live in
  these bytes. The viewer contacts **no** server except S3 for the `.replay` file, and
  `results.reason` is inside the replay as well as in the hosted artifact (paintball, 2026-08-25 —
  a replay that carries its own result is byte-reconcilable with the artifact).
- Fruit ids are the fixed order `0 apple, 1 banana`; `-1` = none. The `flags` byte packs
  `exhausted` (bit 0), `starving` (bit 1), `tradedThisRound` (bit 2).
- Size arithmetic: 720 frames × ~150 integers ≈ **0.5 MB**, plus ~1 500 events ≈ 0.3 MB.
  `tests/test_replay.nim` asserts `< 8 MiB`.

---

## Server, player, protocol

### Game container (`/bin/fruit-market`)

Routes, kept from paintbot's `src/ctf/server.nim` because hosted certification probes exactly
these **before** the player pods start (lantern, 2026-08-23):

| route | behaviour |
|---|---|
| `GET /healthz` | `200 ok`, from process start until `shutdownGraceSeconds` after the artifacts are written |
| `GET /client/player?slot=N&token=T` | the seat's HTML shell (paintbot's, trimmed); it never opens the player socket |
| `WS /player?slot=N&token=T` | the seat socket; a bad token is refused with a close, never a hang |
| `GET /client/global` | the broadcast client (`client/replay_broadcast.html`, embedded with `staticRead`) |
| `WS /global` | live spectator: paintbot's sprite protocol + the chrome `TextMessage` |

`fruit-market.player.v1` frames, JSON text, bullwhip shapes:

- game → player: `{"type":"welcome","protocol":"fruit-market.player.v1","slot":N,"name":"Dune","rounds":12,"ticksPerRound":60,"variant":"concentric-rivers"}` on connect; the `state` frame from `## Decisions` at every round boundary and at episode end; `{"type":"final","done":true,"slot":N,"scores":[…8…],"names":[…aliases…],"rounds":R,"reason":…,"ending":…}`, after which the player exits **0**.
- player → game: `{"type":"prompt","prompt":"<= 4000 chars","scripted":"hauler|homesteader|"}`,
  sent immediately on connect, again after `welcome`, and re-sent every 2 s for up to 10 s until
  the game acknowledges the registration (the paintball slot-admission race).
  Any other frame is ignored with a log line.

Startup: `src/fruit_market.nim` randomises the seed **before** `config.update` (paintbot's rule —
every seed-derived draw, including the farm-type shuffle, must follow the final seed), waits up to
`playerConnectTimeoutSeconds = 180` for eight sockets but returns as soon as every connected socket
has registered, starts with whoever is there (missing seats play `hauler`), then runs the round
loop.

Shutdown, in this order (bullwhip's `finishEpisode` plus lantern's grace): send `final` to every
player socket → broadcast the last global frame → `sleep 500 ms` → write `results.json`
(`COGAME_RESULTS_METHOD`, `application/json`) → write the replay (`COGAME_SAVE_REPLAY_METHOD`,
`application/json`) → keep `/healthz` and `/global` answering for `shutdownGraceSeconds = 20` →
`quit(0)`. The player's receive loop wraps `receiveMessage` in `try/except CatchableError` and
exits **0** on a closed or truncated frame (raid, 2026-08-23 — otherwise `docker_smoke` passes and
certification fails intermittently).

### `results.json`

```json
{"names":["fruit-market-broker","fruit-market-hauler","fruit-market-hauler","fruit-market-ricardo",
          "fruit-market-hauler","fruit-market-homesteader","fruit-market-hauler","fruit-market-homesteader"],
 "aliases":["Ash","Bram","Cedar","Dune","Elm","Fern","Gale","Holt"],
 "farm_types":["apple","banana","banana","apple","apple","banana","apple","banana"],
 "scores":[214,168,151,231,144,96,159,88],
 "win":[false,false,false,true,false,false,false,false],
 "craved_eaten":[38,30,27,42,25,16,28,14],
 "own_eaten":[24,18,16,21,19,16,19,18],
 "harvested":[62,55,49,64,58,71,57,69],
 "trades":[11,10,9,12,9,0,10,0],
 "volume":[54,30,27,60,27,0,30,0],
 "crossings":[8,7,6,9,7,14,7,13],
 "starving_ticks":[0,0,12,0,0,96,0,88],
 "mean_rate_x100":152,
 "total_trades":31,
 "rounds":12,
 "reason":"complete",
 "ending":"round_limit"}
```

`names` are **policy** names (platform side); aliases go to the players and into the replay's
`names[]`. Arrays indexed by slot, always length 8. Field definitions, so nothing is guessed:
`scores[i] == 5 × craved_eaten[i] + own_eaten[i]` (the score, higher better); `harvested[i]` =
fruit picked; `trades[i]` = executed trades; `volume[i]` = fruit units that seat gave away;
`crossings[i]` = water cells entered; `starving_ticks[i]` = ticks at `hunger == 0`;
`mean_rate_x100` = the volume-weighted mean apples-per-banana over all executed trades × 100
(0 if none); `rounds` = rounds completed.

---

## Viewer

**All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`.** Named explicitly, because
splicing two starters' halves (one's `MODULARIZE`/`EXPORT_NAME` link flags onto the other's
`onRuntimeInitialized` bootstrap) is what left cogame-lantern with a permanently blank theater:

| file | source (coworld-ctf, one starter for all four) | change |
|---|---|---|
| `replay-viewer/config.nims` | coworld-ctf `replay-viewer/config.nims` | verbatim except the emitted name (`fruit_market_replay.js`) and the export list renamed `_fm_*`. **Keep the non-`MODULARIZE` link flags exactly as they are** — no `-s MODULARIZE=1`, no `EXPORT_NAME` — because the worker bootstraps with `Module.onRuntimeInitialized`. Keep `-O2 -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file <root>/data@data`, `--mm:arc`, `--exceptions:goto`, `-d:noSignalHandler`, `-d:useMalloc`. |
| the wasm entry `.nim` | coworld-ctf `replay-viewer/ctf_replay.nim` → `replay-viewer/fruit_market_replay.nim` | same structure: `stampStage`, `fm_load_replay`, `fm_frame`, `fm_input`, `fm_packet_ptr/_len`, `fm_error_ptr/_len`, `fm_stage_ptr/_len`, and the `emscripten_exit_with_live_runtime()` epilogue (without it Nim's `main` destroys every global while JS keeps calling in). `fm_load_replay` parses the JSON replay and hydrates the frame array; `fm_frame` advances/seeks and rebuilds the viewer packet. `ctf_mismatch_tick` is **dropped** — there is no re-simulation to mismatch. **The packet built by `fm_load_replay` is the only one carrying `meta`**; read it directly and never re-derive it via `packetAt(0)` (matrix-games, 2026-08-24). A mid-seek click that arrives before the first chrome frame is **queued** and converged with a bounded per-frame tick walk (`SeekTicksPerFrame = 240`), never dropped (paintball, 2026-08-25). |
| `static_replay*.js` | coworld-ctf `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | verbatim apart from the `ctf_*` → `fm_*` export names, the worker name string (`fruit-market-static-replay`), and **one added line** in `showFailure`: `document.documentElement.setAttribute('data-replay-error', error.message || String(error))`. The worker keeps `importScripts('./wire_constants.js','./broadcast_core.js','./fruit_market_replay.js')` and `Module.onRuntimeInitialized` — the matched pair for the link flags above. |
| `index.html` | coworld-ctf `client/replay_broadcast.html`, spliced by `Dockerfile.replay-viewer`'s `sed` into `replay-viewer/dist/index.html` | the starter's page with a game block appended (below). |

`static_replay.js` already sets `data-replay-loaded="true"` on `<html>` when the worker reports
`loaded` (its `onWorkerMessage` `'loaded'` branch); with the added failure line it sets
**`data-replay-error`** on any failure. Those are the two signals `tools/ci/viewer_smoke.mjs` and
phase 60's `viewer-check.yml` read. If a `coworld-replay` bridge `ready` message is posted at all,
it is posted from a callback that fires **after** `data-replay-loaded="true"` is set, never on rAF
timing at the call site (chorus, 2026-08-24). The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and `tools/build_replay_viewer.sh` is the
`coworld build` hook that produces the bundle. **Never a `/client/replay` pod.**

### Chrome provenance (exact)

- `client/chrome_common.js` is copied **byte-for-byte**. Nothing in it is edited — which is why the
  wire-constants global keeps the name `window.CTF_WIRE` and why the two guild plates ride the
  starter's own `teams` / `roster` machinery rather than a new one.
- `client/broadcast_core.js` is **forked** (it is paintbot's renderer — the playbook's "treat the
  starter's renderer as the exact template"): the board draw becomes the tile grid, rivers, groves,
  stalls, fruit, cogs, offer bubbles and hunger bars. Its ingest/packet plumbing, letterboxing and
  layer pooling are untouched.
- `client/replay_broadcast.html` is **the starter's page with a game block appended**, never a
  rewrite that reuses its ids. The only edits inside the starter's own markup/script are these
  three, and no others:
  1. **Removed elements** (with their CSS blocks and the JS branches that touch them):
     `#viewpanel` and its children `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`,
     `#zoom-slider`, `#zoom-in`, `#zoom-read`; `#fpv` and its children `#fpv-canvas`, `#fpv-hud`,
     `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`;
     `#povBadge`; `#mmwarn`.
     **Zoom decision: `#viewpanel` is dropped entirely.** The 32 × 18 board is fixed and always
     fits the frame, so there is nothing to pan to and nothing a minimap could add; the zoom bar +
     minimap exist only for boards larger than the frame.
  2. **Two re-lettered literals**: the scorebug's `Lives` label becomes `Score`, and the momentum
     strip's label becomes `APPLES PER BANANA`.
  3. `#lockerroom` gains `pointer-events: none` so its ~1.5 s overlay stops swallowing transport
     clicks (ecos, 2026-08-23).
  Everything else — `#stage`, `#board`, `#chrome`, `#scorebug`, `#plates-l`, `#plates-r`, `#clock`,
  `#clock-time`, `#clock-caption`, `#bannerlane`, `#killfeed`, `#transport` and all its buttons
  plus `#btn-spoilers`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`, `#scrub-head`,
  `#endcard`, `#status` — is the starter's, unchanged.
- **The appended game block** owns: the two guild plates' totals, the roster strip, the order book
  panel, the feed row builders, the beat-marker CSS, and the plate colours
  (`.plate.apple{--tc:#d94f3d}`, `.plate.banana{--tc:#e8c33a}`, `.plate.rate{--tc:#4a7ad6}` —
  unknown team keys fall back to the starter's `AMBER` constant in `buildFlag`, so nothing breaks
  if a key is missed). Its beat builder is named **`buildMarketBeats`**, never `markBeat`: a
  game-block `function markBeat` is hoisted over the chrome alias block's `var markBeat =
  C.markBeat` and silently kills every scrubber beat (tandem, 2026-08-23). A scope-duplication test
  over the alias list enforces it. `pushFeed(row)` keeps the starter's **one-argument** signature
  (changing it is what broke cogball 0.1.4).

### Transport rules

`relayout()` sets `--band` and `--hudscale` on `:root` (and `--topband` for the scorebug strip);
every chrome measure derives from `--u = 1px * var(--hudscale)`. **No overlay sits in the transport
band**: the order-book panel, the roster strip, the feed and the banner lane are all clipped to the
board region between `var(--topband)` and `var(--band)`. The **endcard stops at `var(--band)`** (it
is `inset: var(--topband) 0 var(--band) 0`, the starter's own rule) and is **dismissed by every
seek**. Scrubber beats are clickable, **labelled buttons** — one per emitted kind, with CSS for
**every** kind the game emits: `round`, `firsttrade`, `starve`, `famine`, `gameover`. The whole
beat timeline ships on the first HUD frame (paintbot's `beats` field), so the scrubber is complete
before playback starts and `?spoilers=0` still holds beats back until the playhead reaches them.
The **last beat is `gameover` at the final tick**, so the rail's right edge always reaches the
endcard (territory, 2026-08-25).

### What it draws

- **Board.** Grass tiles for the three land zones, animated water tiles for the two rivers, the
  wall ring, 24 apple trees and 24 banana trees drawn ripe (fruited) or bare, four striped stall
  awnings with their names (`NORTH`, `EAST`, `SOUTH`, `WEST`), and eight cogs as 36 px bodies in
  their slot colour with a **fruit badge** (apple or banana) showing their farm type and the alias
  under the feet. A cog wading is drawn half-submerged with a splash and a `−10` stamina pip; an
  exhausted cog is drawn slumped and grey.
- **Offer bubbles (the idea's headline readout).** Every cog with a live offer carries a floating
  bubble above its head reading `3 🍎 → 2 🍌` in **sprites and digits**, tinted by the fruit it
  gives; an `unfunded` offer is drawn hollow with a dashed outline. When two bubbles within
  `tradeRadius` mirror, both bubbles pulse and a link line is drawn between the cogs the tick
  before they clear; on execution the bubbles burst into the two fruit sprites flying between the
  cogs and a feed row is pushed.
- **Hunger bars (the idea's headline readout).** A two-segment bar under every cog: the upper
  segment is hunger (green → amber → red), the lower is stamina (blue). At `hunger == 0` the bar
  flashes and the cog gets a `STARVING` tag; at `stamina == 0` the tag reads `EXHAUSTED`.
- **Exchange-rate chart (the idea's headline readout).** `#momentum`, the SVG under the scrub
  track, label `APPLES PER BANANA`: one stepped line from `series.rate`, on the same tick axis as
  the playhead, with the canonical 1.50 book price drawn as a dashed reference. Fed exactly like
  paintbot's lives series — `state.lead = {"teams":["rate"], "pts":[[t, rateX100], …]}` — so
  `ingestLeadSeries` / `renderMomentum` in `client/chrome_common.js` need **no change**.
- **Scorebug** (`#scorebug` / `#plates-l` / `#plates-r`, paintbot's plate machinery): two plates
  keyed `apple` and `banana` — `APPLE FARMERS` and `BANANA FARMERS`, headline via
  `teams[k].policies`, the big number = the guild's **total score** (`lives-<k>`, label re-lettered
  `Score`), and underneath the guild's trade count and mean rate.
- **Order book** (appended, right, above the feed): up to eight rows, one per live offer, sorted by
  volume then slot — `ASH  3 🍎 → 2 🍌  north` — hollow when unfunded, struck through when it
  clears. This is the "all offers logged" surface made visible.
- **Roster strip** (appended, under the scorebug): eight chips in score order —
  `DUNE · fruit-market-ricardo · 231` — tinted with the seat's body colour, with a fruit badge and
  a hunger pip. The **policy name** appears here and only here (plus `results.names`); the board
  and every prompt show the alias.
- **Clock** (`#clock-time`, `#clock-caption`): `ROUND 4 / 12`, caption `tick 214 of 720`. Spelled
  out, never `R4`.
- **Feed** (`#killfeed`, the starter's `pushFeed(row)`): one row per `trade`
  (`ASH 3 🍎 ⇄ 2 🍌 CEDAR · 1.50 · north stall`), per `offer`
  (`DUNE posts 6 🍎 for 4 🍌`, tagged `auto` when `source` is `fallback` or `scripted`), and per
  `starve` / `exhausted` (`GALE IS STARVING`, `HOLT COLLAPSED — 0 stamina`), plus the seat's `say`
  as the quoted tail of its `offer` row.
- **Endcard**: the ending in words (`ROUND LIMIT` / `FAMINE` / `TIME`), the winner's alias and
  policy, the eight scores, and the line `31 trades · mean 1.52 apples per banana · 2 cogs
  starved`.

**Legibility at 360 px is a requirement** — the featured-match iframe is ~360 px wide.
`#stage.tiny` (already switched on at `boardW <= 620`) shrinks the feed and pips; carry bullwhip's
`.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and hide chip labels under 640 px so the roster
chips degrade to `DUNE 231`. Offer bubbles drop the fruit *word* and keep digits + sprite. Check at
360 px: both guild plates with their totals, the `ROUND 4 / 12` clock, the rate chart, at least
three offer bubbles and the top three roster chips readable.

**Real art, not placeholders.** `scripts/art/gen_market_art.py` (Pillow, committed, deterministic)
renders and commits into `data/`: grass and orchard-floor tiles, two water tiles (still/rippled),
the wall ring, apple and banana trees in ripe and bare states, apple and banana fruit sprites at
two sizes (board and bubble), the four stall awnings, eight cog bodies
(`cog_<colour>_front.png`, `_wade.png`, `_slump.png`), the offer-bubble frame, the trade burst, and
the loading screens the `#lockerroom` markup expects (`client/art/lockerroom/bg.jpg` = a market at
dawn, plus eight portraits replacing the soldier `.webp`s). `Dockerfile.replay-viewer`'s copy list
and its `test -f` assertions are updated to those file names; the `league.html` sed step and
`client/league_replayer.html` are dropped with it.

---

## Packaging

**`compose.yaml`** — one service, one image (game + player binaries):

```yaml
services:
  fruit_market:
    image: coworld-fruit-market:latest
    platform: linux/amd64
    build: {context: ., dockerfile: Dockerfile, network: host}
```

The service name is the single source of the manifest placeholder: `services.fruit_market` →
**`{{FRUIT_MARKET_IMAGE}}`** (lantern, 2026-08-23 — `coworld build` hard-fails anything else and
`{{GAME_IMAGE}}` is not a thing; the underscored service name is the collab-cooking precedent that
released canonical). `tests/test_manifest.nim` asserts the derivation.

**Names.** `game.name` is **`fruit-market`** — identical to the repo slug, the softmax.com page
slug, the secret namespace and the league-seed key, so the three name spaces that bit
commons-family and cooperative-hunting cannot diverge here (grid-wars shipped a hyphenated
`game.name` canonically on 2026-08-24). The secret ref is
`secret://coworld/fruit-market/anthropic_api_key`, and the release workflow reads the namespace out
of `game.name` rather than hardcoding `$SLUG`.

**`coworld_manifest_template.json`** — bullwhip's shape with the 0.1.42 strictness hive and
collab-cooking found: top-level `$schema`, ≥ 3 `tags` (`fruit-market`, `trade`, `grid`,
`llm-driven`, `melting-pot`, `eight-player`), top-level `episode_timeout_minutes: 20`, top-level
`player[]`, `variants[].description` on every variant, `game.owner` present, **no** top-level
`replay_viewer` and **no** top-level `version`, and a real JSON-Schema `game.config_schema` with
`required: ["tokens"]` and `minItems`/`maxItems` on **every** array property (tandem, 2026-08-23).

- `game.name`: `fruit-market`; `game.replay_viewer.bundle`: `static-replay-viewer`.
- `game.runnable`: `{"type":"game","image":"{{FRUIT_MARKET_IMAGE}}","run":["/bin/fruit-market"],
  "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/fruit-market/anthropic_api_key"},
  "source_url":"https://github.com/Metta-AI/cogame-fruit-market/tree/main"}` — the `env` entry is
  mandatory: without it the hosted game container never sees the coworld secret and every league
  episode silently plays scripted (hive, 2026-08-23), which surfaces only at phase 60 check 4.
- `game.config_schema` properties: `tokens` (string array, `minItems 1`, `maxItems 8`, required),
  `players` (array of `{name}`, `minItems 1`, `maxItems 8`), **`num_agents` (integer, 1..8, default
  8)**, `seed`, `rivers` (integer 0..2, default 2), `rounds` (1..24, default 12), `ticksPerRound`
  (10..120, default 60), `moveCooldown` (1..8, default 2), `waterMoveCooldown` (1..12, default 4),
  `moveStaminaWater` (0..40, default 10), `moveStaminaLand` (0..4, default 1),
  `harvestCooldownOwn` (1..60, default 12), `harvestCooldownOther` (1..120, default 24),
  `yieldOwn` (1..8, default 3), `yieldOther` (0..8, default 1), `regrowTicks` (1..240, default 60),
  `invCap` (1..64, default 12), `hunger0` (0..100, default 60), `hungerDrainPeriod` (1..64,
  default 4), `craveNutrition` (0..100, default 25), `ownNutrition` (0..100, default 10),
  `craveScore` (0..20, default 5), `ownScore` (0..20, default 1), `eatCooldown` (1..60, default 6),
  `starveDrain` (0..10, default 2), `staminaRegenPeriod` (1..60, default 2), `tradeRadius` (1..12,
  default 3), `viewRadius` (1..32, default 6), `offerMax` (1..12, default 6),
  `llmTimeoutSeconds` (5..60, default 20), `minTurnSeconds` (0..60, default 18), `maxOutputTokens`
  (200..2000, default 1000), `model` (string), `episodeTimeoutSeconds` (default 1200),
  `playerConnectTimeoutSeconds` (default 180), `shutdownGraceSeconds` (default 20),
  `showPlayerLabels` (bool, default true). `additionalProperties: false`.
- `game.results_schema`: the `results.json` object above (slot arrays `minItems 1`, `maxItems 8`).
- `game.docs` (**text**, not uri — bullwhip's shape):
  `{"readme":{"type":"text","value":"<what it is: eight cogs, two fruits, two farmer types, two
  rivers; you score five times as much for eating the fruit you do not grow, and the only way to
  get it cheaply is a posted offer that exactly mirrors someone else's>"},
    "pages":[{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<the board, the
      nine-step tick order, harvest/hunger/stamina, the water toll, mirror-image matching and its
      tie-break, scoring, end conditions>"}},
             {"id":"policies.md","title":"Fielding a policy","content":{"type":"text","value":"<the
      standing-order schema, the caps, the observation, PLAYER_PROMPT / PLAYER_SCRIPTED
      how-to>"}}]}`.
- `game.protocols` — **both**, as `{"type":"text","value":…}` objects (the platform validator
  rejects bare strings): **`player`** (the `fruit-market.player.v1` frames, the observation, the
  reply schema and its caps, and the explicit note that `say` is spectator-only and never reaches
  another seat) and **`global`** (the `/global` sprite + chrome frame, and the static bundle's
  `index.html?replay=<url>`).
- `player[]` — three entries, all on `{{FRUIT_MARKET_IMAGE}}` with
  `run: ["/bin/fruit-market-player"]`: `fruit-market-player` (no env — a prompt policy;
  `PLAYER_PROMPT` is supplied at upload time), `fruit-market-hauler`
  (`env: {"PLAYER_SCRIPTED":"hauler"}`), `fruit-market-homesteader`
  (`env: {"PLAYER_SCRIPTED":"homesteader"}`).
- **`variants[]` — four; `num_agents: 8` in every one**, and `players` is the eight aliases in slot
  order in every one:

  | id | name | `rivers` | `moveStaminaWater` | `regrowTicks` | `num_agents` |
  |---|---|---|---|---|---|
  | `open-market` | Open market (no rivers) | 0 (river cells become land) | 0 | 60 | **8** |
  | `concentric-rivers` | Concentric rivers | 2 | 10 | 60 | **8** |
  | `deep-rivers` | Deep concentric rivers | 2 | 18 | 60 | **8** |
  | `lean-harvest` | Lean harvest | 2 | 10 | 90 | **8** |

  `open-market` and `concentric-rivers` map one-for-one onto the idea's two source substrates
  (`fruit_market`, `fruit_market__concentric_rivers`); `deep-rivers` and `lean-harvest` are the two
  tuning axes that make the geography and the scarcity bite harder, and they change nothing else.
  All four share `rounds: 12, ticksPerRound: 60` and the constants above. **The league default
  variant is `concentric-rivers`** — it is the config the idea names and the one where reading the
  book beats walking, i.e. where an LLM champion visibly outplays a filler; phase 50 passes it as
  `default_variant_id` at seed time (chemistry, 2026-08-25: the seed body accepts it at the top
  level, and gridlock's 409 shows it cannot be re-seeded later).
- `certification`:
  `game_config` = `{num_agents: 8, seed: 7, rivers: 2, rounds: 6, ticksPerRound: 60,
  minTurnSeconds: 0, playerConnectTimeoutSeconds: 180, players: [ …the eight aliases… ]}` — and
  **no runner-managed `tokens`** (collab-cooking, 2026-08-25: `manifest_invalid` otherwise) — with
  `players` = 2 × `fruit-market-player`, 4 × `fruit-market-hauler`,
  2 × `fruit-market-homesteader`: **every declared player entry seated at least once**, because
  `players-run` seats the whole roster and a `baseline × N` fixture fails `players_missing` (raid,
  2026-08-23). Offline the `fruit-market-player` seats fall back to `hauler`, so the fixture is
  deterministic. **6 × 60 = 360 ticks = 15 s of video**, which outlasts the 10 s viewer soak, and
  with `minTurnSeconds: 0` and no credentials it runs in a few seconds. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (cooperative-hunting, 2026-08-25) so the
  60 s default can never truncate it.

**Other packaging files:** `Dockerfile` (paintbot's two-stage nimby build; produces
`/bin/fruit-market` and `/bin/fruit-market-player`), `Dockerfile.replay-viewer` (paintbot's, with
the fruit-market file list and the same `test -f` / `grep -q` assertions, minus `league.html`),
`tools/build_replay_viewer.sh` (paintbot's, image tag renamed, `mkdir -p` fix),
`.github/workflows/ci.yml` and `coworld-release.yml` from `coworld-builder/templates/`,
`tools/ci/docker_smoke.sh` with `<SEATS>` substituted to **8** and `<slug>` to `fruit-market`,
`tools/ci/viewer_smoke.mjs` copied verbatim, `tools/ci/dom_text_smoke.mjs`,
`tools/ci/renderer_fixture.html`, `tools/ci/check_manifest_loads.py` (runs the installed coworld's
own `_load_template_manifest` — collab-cooking, 2026-08-25), and `tools/ci/policies.json` naming
`fruit-market-broker` and `fruit-market-ricardo` (both `PLAYER_PROMPT`, each with
`env: {"USE_BEDROCK":"true"}` — without it the platform gives the player pod no Bedrock sidecar and
the seat silently plays scripted, cogolf 2026-08-24) plus the fillers `fruit-market-hauler` and
`fruit-market-homesteader`.

---

## Tests

All run in `ci.yml`; the sandbox cannot run any of them locally.

1. **`tests/test_map.nim` — the board.** `d(x,y)` zoning; exactly 72 + 32 water cells; exactly 24
   apple and 24 banana trees at the listed cells, none on water, wall or a stall, no duplicates;
   the four stalls are land in the market ring; the eight spawn cells are free; every land cell of
   a zone is reachable from every other land cell of that zone without entering water; the market
   ring is exactly one river-crossing from each grove and the groves are two from each other;
   `rivers: 0` turns every water cell into land and leaves the tree lists unchanged.
2. **`tests/test_sim.nim` — sim units.** Harvest yields 3/1 and sets the 12/24 cooldowns; a bare
   tree yields nothing and regrows at exactly 60; `spill` above `invCap`; land vs water move costs
   and cooldowns; a move refused for insufficient stamina; two cogs cannot share a cell and the
   lower slot wins; hunger drain at `tick mod 4 == 0` and the `starve` event at the 0 crossing;
   `starveDrain` and `exhausted`; regen only while `hunger > 0`; eating gated by `eatCooldown`,
   nutrition capped at `hungerMax`, `craveScore`/`ownScore` applied to the right seat; an exhausted
   cog can still eat and trade; the farm-type shuffle yields exactly 4 + 4 for 100 seeds and is
   seed-stable; **determinism** — the same seed and the same order script produce an identical
   `gameHash` after 720 ticks, twice in one process and across a fresh server.
3. **`tests/test_market.nim` — the offer book.** Exact-mirror matching accepts only exact mirrors
   (each of the four fields perturbed in turn must fail); radius 3 boundary (dist 3 clears, dist 4
   does not); an unfunded offer never clears and emits `unfunded` with the right reason; receipt
   over `invCap` blocks the pair; the **tie-break** — a hand-built board with four simultaneously
   clearable pairs asserts the exact execution order under (volume desc, distance asc, low slot
   asc, high slot asc) and that a cog in two candidate pairs trades only in the first; one trade
   per cog per tick and per round; an executed offer is cleared on both sides; `n` outside 1..6 is
   clamped and flagged.
4. **`tests/test_baseline.nim` — bounded orders / legality.** For 12 seeds × 720 ticks on all four
   variants, with all-`hauler`, all-`homesteader` and a 4/4 mix: every emitted order's `job`,
   `fruit`, `stall` and `eat` is inside its enum, every offer has `1 <= n <= 6` and
   `give.fruit != want.fruit`; every per-tick action is one of the six vocabulary values; no cog is
   ever outside the board, in a wall, in a tree or sharing a cell; no inventory exceeds `invCap` or
   goes negative; hunger stays in 0..100 and stamina in 0..100; scores never decrease; two haulers
   of opposite type within radius always clear within 2 ticks; neither baseline raises, and neither
   takes more than 1 ms per round.
5. **`tests/test_feasibility.nim` — the oracle, as a CI precondition.** Gates (a)–(d) of
   `## The game`, over seeds 1..12 on all four variants, including the test-only `mirror` kernel
   for gate (d). Any constant change that breaks the economy fails here rather than in a dead
   replay.
6. **`tests/test_replay.nim` — end-to-end + strict UTF-8.** Plays a full scripted episode headless,
   writes `results.json` and the replay, then re-reads the replay **bytes**: `validateUtf8 == -1`
   (strict), parses as JSON, `protocol == "fruit-market.replay.v1"`, `frames.len == ticksPlayed`,
   `series.rate.len == ticksPlayed`, every event tick in `0..ticksPlayed`, at least one `harvest`,
   `offer`, `trade` and `eat`, exactly `rounds` `round` events and exactly one `end`,
   `results.scores.len == 8`, `results.reason` in `{complete, deadline, forfeit}`, `results.ending`
   in `{round_limit, famine, deadline, forfeit}`, `config` carries every constant the viewer reads,
   file size `< 8 MiB`. A seat is fed a `say`/`notes` of multi-byte runes exactly at the 80/320
   caps and the recorded strings are asserted valid UTF-8 and ≤ the cap (the bullwhip
   byte-truncation bug).
7. **`tests/test_llm.nim` — decision layer.** `extractJsonObject` on fenced and prose-prefixed
   replies; unknown `job` → invalid; `give.fruit == want.fruit` → invalid; `n = 9` → clamped to 6
   with `clamped: true`; a missing `offer` key leaves the standing offer, `null` withdraws it; a
   stubbed transport that times out, 429s, 403s or returns junk produces `hauler` orders for those
   seats, never raises, and marks `source: "fallback"`; a `max_tokens` stop raises the named
   "cut off at max_tokens" error; **one batch carries all open seats** (assert
   `RequestBatch.len == openSeats`, i.e. 8 on round 1); `minTurnSeconds` holds the request rate
   under 30/min.
8. **`tests/test_manifest.nim` — packaging.** `num_agents == 8` in **all four** variants and in
   `certification.game_config`; the image placeholder equals the one derived from `compose.yaml`'s
   service name (`{{FRUIT_MARKET_IMAGE}}`); `replay_viewer.bundle == "static-replay-viewer"`;
   `game.name == "fruit-market"` and the `secret://coworld/<ns>/…` namespace equals it;
   `game.docs.readme` + non-empty `pages`; `game.protocols.player` **and** `global` present and both
   `{"type":"text",…}` objects; `ANTHROPIC_API_KEY_URI` in `game.runnable.env`; every `player[]` id
   appears at least once in `certification.players`; the cert fixture declares no `tokens`;
   `episode_timeout_minutes` top-level; every array property in `config_schema` carries `minItems`
   and `maxItems`.
9. **`tests/test_broadcast.nim` — chrome frame.** `teams` keys are exactly `apple` and `banana`,
   each carrying `policies: [<guild name>]` and `lives` = the guild total; `roster[]` has 8 entries
   carrying alias in `name` and the **policy** name in `pol`; `lead.teams == ["rate"]` and
   `lead.pts` rows are `[t, rateX100]`, the shape `ingestLeadSeries` expects; `beats` carries only
   the five declared kinds and the last beat is `gameover` at the final tick; `over` is present on
   the terminal frame with the ending string; every feed row's text is ≤ the caps; and a
   **scope-duplication test** asserts no game-block function name collides with the chrome alias
   list (`markBeat` et al., tandem).
10. **`docker-smoke` (`tools/ci/docker_smoke.sh`, `<SEATS>` = 8).** Builds the image, runs a real
    8-seat episode in containers off the cert fixture, asserts the **player** containers each exit
    0 (raid, 2026-08-23) as well as the game, validates `results.json` against the results schema,
    and copies the replay to `SMOKE_REPLAY_OUT` (`dist/smoke/replay.json`), uploaded as the
    `smoke-replay` artifact.
11. **`wasm-viewer` job — the bundle is EXECUTED, not merely built.** `needs: docker-smoke`,
    downloads `smoke-replay`, builds the bundle via `tools/build_replay_viewer.sh`, installs
    Playwright pinned **1.55.0**, and runs **`tools/ci/viewer_smoke.mjs`** against that replay over
    local HTTP with `--strict-text-bounds` (fixed arena → `canvas_text.never_inside` must be 0) and
    `--soak 10` (the 15 s cert replay outlasts the window). Pass requires
    `data-replay-loaded="true"` **and** three different clock readouts at 0 %, 50 % and 100 %;
    `data-replay-error` or silence fails the job. Evidence (`viewer-smoke.png`,
    `viewer-smoke.json`) uploads on success and failure. Two further steps in the same job:
    `viewer_smoke.mjs --strict-text-bounds` against **`tools/ci/renderer_fixture.html`** (the real
    renderer with full-cap 80-char `say` strings and a live offer bubble on **every** seat at
    several canvas sizes, because `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY` and therefore
    produces a replay with zero LLM text — cogchemists, 2026-08-24), and
    **`tools/ci/dom_text_smoke.mjs`** over the real page at 13 viewports down to 360 px, asserting
    the feed rows, order-book rows and roster chips are not clipped and their strings are still
    full length (collab-cooking, 2026-08-25).
12. **`check_manifest_loads`** — a `ci.yml` step that runs the installed coworld package's own
    `_load_template_manifest` against `coworld_manifest_template.json`, so a template that phase 40
    would reject fails in repo CI instead.

---

## Out of scope (v1)

- **Per-tick policy sockets.** A seat submits one standing order per round; the kernel emits the
  per-tick grid and offer actions. A direct per-tick action channel for RL/vector policies is not
  shipped.
- **A talk channel between cogs.** The idea's "price discovery with no words" is taken literally:
  `say` is spectator-only, and the only signals a cog can send another are its posted offer and
  where it stands.
- **Price-improvement matching, partial fills and continuous market making.** Offers clear only as
  exact mirrors, at most one trade per cog per round, and an executed offer is consumed. No order
  book depth, no resting limit orders across rounds after a fill, no fees, no money.
- **More than two goods, or a third farmer type.** Two fruits, two types, one exchange rate — that
  is what makes the rate chart readable.
- **Theft, gifting, combat, blocking and doors.** A cog cannot take fruit from another cog, cannot
  give unilaterally (a gift is expressible only as an offer someone must mirror), and cannot damage
  anyone.
- **Sixteen seats.** Eight, in every variant. The 16-seat original is noted in the idea and
  deliberately not shipped (`## The game` §Seats).
- **Procedural boards, map generation, the map editor and the league replayer page** — inherited
  paintbot machinery, all deleted rather than carried dark. One authored board, four variants that
  only change constants.
- **Fog of war beyond the radius-6 view.** The static geography is public to every seat; paintbot's
  FOV, first-person PiP and POV lens are deleted, not repurposed.
- **Cross-episode persistence.** Every episode starts from the seeded opening state; nothing
  carries over except the league rating.
- **Re-simulating playback.** The viewer decodes recorded state; there is no replay-hash mismatch
  mode, no `--mismatch-quit`, and no `#mmwarn`.
