# cogame-lux-ai — design note (2026-08-27, paintbot lineage)

*Destination path in the new repo: `docs/plans/2026-08-27-lux-ai-design.md`. This file is the
run-directory copy (`runs/2026-08-27-lux-ai/design.md`); phase 20 places the identical bytes at the
destination path above.*

`Metta-AI/cogame-lux-ai` is a **two-seat, zero-sum economy RTS at board-game tempo**: a port of the
**Lux AI Challenge Season 1** rules onto a 16 × 16 mirrored grid. Two sides gather wood, coal and
uranium, spend research to unlock the better fuels, grow cities out of city tiles, and every ten
turns the sun goes down and each city must pay its light bill or die on the spot. Most city tiles
standing at turn 360 wins. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its
read-only mount `/workspace/starters/coworld-ctf`. **Every convention there holds here unless this
note says otherwise** — the tick loop and the `Lobby → Playing → GameOver` phase machine, the
`COWLDCTF` binary replay codec with its per-tick `gameHash` chain, `ReplayKeyframeTicks`, the lull
scan and the beat timeline, the whole server-side decision layer
(`src/ctf/{decide,directives,llm,baselines,control}.nim` — one parallel batch per turn, two bounded
whole-second deadlines, `turnSpacingMs` rate floor, budget guard, tolerant JSON parsing, rune caps,
scripted fallback), the mummy server and its `COGAME_*` runtime contract, the seat/cog split and the
`cogAlias` two-name-space rule, the broadcast chrome (`client/replay_broadcast.html` +
`client/chrome_common.js` + `client/broadcast_core.js`), the emscripten static replay bundle
(`replay-viewer/`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`) and the `GameVersion`
changelog discipline are all inherited.

**Starter choice, in one line:** coworld-ctf is the starter table's row for **any game loop whose
rules are written for this coworld** — Lux S1's rules are a public *specification*, not a C/RL
environment this repo must reproduce bit-for-bit, so the `cogame-moba` porting row does not apply —
and paintbot already ships, tested, every layer this game needs except the Lux rules themselves: a
tick loop with a per-tick hash chain, a server-side per-turn LLM directive layer with a deterministic
compiler and a scripted fallback beneath it, a binary replay the browser re-simulates, and a static
wasm viewer with real chrome.

**Source idea, verbatim:**

> LUX Lux AI — gather resources by day, survive the night, and every unit you own is one action per turn
>
> Port of the Lux AI Challenge (Kaggle, seasons 1-3). Season 1: two players build cities on a map of wood/coal/uranium; workers gather, carts haul, cities need fuel to survive each night cycle; research unlocks resource tiers; most city tiles at the end wins. Season 2: factories, heavy/light robots, ice and ore refining, lichen growth as score, a bidding phase for factory placement. Season 3: fog of war, relic nodes and energy fields. Turn-based with simultaneous orders for ALL your units, 1000 turns, strict per-turn compute budget. A full economy RTS at board-game tempo.
>
> Seats: 2
> Motive: zero-sum economy race
> Policy interface: one orders-bundle per turn; LLM + scripted unit micro is a proven pattern from the Kaggle leaderboard
> Fills gap: ProxyWar is our RTS, but Lux's day/night fuel loop and public, battle-tested rules + a huge open-source bot corpus make it the best-studied 1v1 economy game — fillers are free
> Integrity (anti-collusion): 2-player zero-sum; maps seeded.
> Replay plan (watchability): the official Lux visualiser (web) exists for every season — embed it.
> Source: github.com/Lux-AI-Challenge/Lux-Design-S1, -S2, -S3.

**Two coordinator rulings this note is written inside, and does not reopen.** (1) **Season 1 only.**
S2 and S3 are in `## Out of scope (v1)`. (2) **The idea's "embed the official Lux visualiser" is
overridden.** The viewer is coworld-ctf's static wasm bundle re-rendering the recorded per-turn state
in the browser. No external embed, no iframe to a third-party site, no pod. Watchability is delivered
by the chrome this repo owns, not by someone else's server.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How cogame-lux-ai satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a game loop with rules written for this coworld; the tick loop, decision layer, replay codec and wasm viewer fork rather than get rewritten. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-lux-ai`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=forester` / `PLAYER_SCRIPTED=prospector` (both fillers); one image `coworld-lux-ai`, player entrypoint `/bin/lux-ai-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`; ctf's `tools/build_replay_viewer.sh` and `Dockerfile.replay-viewer` kept; the **same Nim sim modules** compile into `replay-viewer/lux_replay.nim` under emscripten and re-simulate every turn in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` **byte-for-byte**; `client/replay_broadcast.html` = the starter's page **with one appended game block**; the board is baked from `data/arena_floor.png`, `client/art/walls/*.jpg` and `data/pallete.png`, units from `data/soldier_{red,blue}*.png`. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | In-game the sides are `RED-alpha` and `BLUE-alpha` (the starter's **unmodified** `cogAlias`); real policy names live only in `results.names`, the replay join records, the DOM scorebug and the endcard. Test-enforced from both sides. (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | typical 251 s / absolute worst 519 s against a 720 s budget; a 660 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 2** inside `game_config` of variants `duel`, `skirmish` and `scarcity` **and** inside `certification.game_config`; `<SEATS>` = 2 in `tools/ci/docker_smoke.sh`. Never at a variant's top level. (§Packaging) |

**There is no `OPEN` section.** Everything the idea leaves loose — which season, which map size, whether
roads and pillage survive, how a 360-turn game is priced against an LLM budget, how a zero-sum duel is
scored on the ladder — is either a coordinator rail already fixed above or a designer rail, and each
is decided below with its reason.

---

## The game

**Nine days and nine nights on a mirrored island.** Turn 0 is dawn. For thirty turns the sun is up:
workers walk to the wood, mine it, walk back to a city tile, drop the wood in as fuel, and — when one
of them is carrying a hundred units of anything — plant a new city tile on an empty square. On turn 30
the sun goes down, and for ten turns every city pays **23 fuel per tile per turn**, minus a discount
for tiles that touch each other, and every unit standing outside a city burns its own cargo to stay
alive. A city that cannot pay is **gone** — every tile of it, at once. Then dawn again. Nine times.
At turn 360 the side with more city tiles standing wins.

The second half of the game is the fuel ladder. Wood is worth 1 fuel a unit and grows back. Coal is
worth 10 and does not, and you cannot touch it until your cities have spent **50 research points** on
it. Uranium is worth 40 and costs **200**. Research points come from city tiles doing nothing else
that turn, so every research point is a worker or a cart you did not build. That trade — grow now on
cheap wood, or spend the daylight learning to burn rocks — is the whole game.

### Seats, sides, aliases

- **`num_agents` = 2.** Exactly two seats, always — in all three manifest variants and in the
  certification fixture. **One seat commands one entire side**: every unit and every city tile that
  side owns. This is the idea's own seat count and its own policy interface ("one orders-bundle per
  turn"), and it is what makes the game zero-sum and therefore collusion-proof by construction.
- **Two name spaces.** In-game, the sides are **`RED-alpha`** (seat 0) and **`BLUE-alpha`** (seat 1) —
  the starter's `cogAlias` (`teamText` + `-` + `IdentityNames[0]`) with `teams: 2`, `cogsPerTeam: 1`,
  so `roster.nim`'s alias machinery needs **no edit at all** and its inherited privacy test applies
  unchanged. Prompts, observations, the ASCII maps, the feed's in-board lines and every sprite label
  carry only those two strings (abbreviated `RED` / `BLUE` in the map legends and the feed). The
  seats' **real policy and player names** (`daveey`, `daveey-1`, `lux-ai-forester`,
  `lux-ai-prospector`) appear only in `results.names`, in the replay's join records, in the viewer's
  scorebug plates and on the endcard. `showPlayerLabels` is **false**. A seat can never learn who it
  is playing.
- Colours are fixed by seat: seat 0 red, seat 1 blue — the two soldier art families the starter ships
  and the two team colours its chrome already knows.

### The board

`mapSize` is **even** and is **16** in the default variant (12 in `skirmish`). Cells are `(x, y)`,
`x` rightwards from 0, `y` downwards from 0; the cell index is `y * mapSize + x` and every tie-break
in this note that says "lowest cell index" means that number.

The map is **generated from the episode seed and is perfectly mirror-symmetric** about the vertical
midline: cell `(x, y)` with `x < mapSize/2` is copied to `(mapSize-1-x, y)`. Seat 0 owns the left
half, seat 1 the right. Symmetry is not decoration — it is the integrity pin the idea asks for
("maps seeded"): neither side can be dealt a better island, and a spectator can see that at a glance.

Generation runs once, at reset, from a dedicated `mapRng` stream seeded by `seed`, over the **left
half only**, in this exact order:

1. Every cell starts `empty`, road level 0.
2. `place(wood, woodClusters, 6, 3)` — see the procedure below.
3. `place(coal, coalClusters, 3, 4)`.
4. `place(uranium, uraniumClusters, 2, 5)`.
5. **Start cell.** Scan the left half in ascending cell index for the first `empty` cell that has at
   least two `empty` orthogonal neighbours and whose Chebyshev distance from the half's centre
   `(mapSize div 4, mapSize div 2)` is minimal (ties by lowest cell index). Place seat 0's **first
   city tile** there (a new city, `fuel = 0`) and seat 0's **first worker** on the same cell.
6. **Mirror.** Every non-empty left-half cell — terrain kind, amount, city tile, unit — is written to
   its mirror cell as seat 1's.

```
place(kind, count, size, minSep):
  for i in 0 ..< count:
    sep = minSep; attempts = 0
    while true:
      cx = 1 + mapRng.rand(mapSize div 2 - 2)
      cy = 1 + mapRng.rand(mapSize - 3)
      inc attempts
      if (cx, cy) is empty and every already-placed centre is >= sep Chebyshev away: break
      if attempts mod 200 == 0: sep = max(2, sep - 1)        # always terminates
    cells = [(cx, cy)] + the first (size - 1) cells, in the fixed neighbour order
            [up, right, down, left, up-left, up-right, down-left, down-right] applied
            breadth-first from (cx, cy), that are inside the left half and still empty
    every chosen cell becomes `kind` with amount `startAmount(kind)`
```

| | `duel` (16 × 16) | `skirmish` (12 × 12) | `scarcity` (16 × 16) |
|---|---|---|---|
| `woodClusters` (per half) | 4 | 3 | **2** |
| `coalClusters` | 2 | 1 | **3** |
| `uraniumClusters` | 1 | 1 | **2** |
| wood cells / half | 24 | 18 | 12 |
| `woodStart` | 300 | 300 | **200** |
| `coalStart` | 400 | 400 | 400 |
| `uraniumStart` | 325 | 325 | 325 |

`woodClusters = mapSize div 4`, `coalClusters = mapSize div 8`, `uraniumClusters = max(1, mapSize div 16)`
are the formulas; `scarcity` overrides all three from config, which is the point of that variant —
with 12 wood cells a side the wood runs out around turn 200 and a side that never researched coal
loses its cities in the sixth night.

### The clock

- **One tick = one Lux turn.** `maxTurns` = **360** (`duel`, `scarcity`) / **200** (`skirmish`).
- **Cycle** = `cycleLength` **40** turns: `turn mod 40 < 30` is **day**, `turn mod 40 >= 30` is
  **night**. Nine full cycles in 360 turns; the last turn of the episode is a night turn.
- **Directive turn** = every `directiveEvery` = **10** turns, beginning at turn 0 before any turn is
  stepped: turns 0, 10, 20, …, 350. **36 directive turns per episode** (20 in `skirmish`). The cadence
  is 10 and not 12 or 20 because 10 divides the 30/10 cycle exactly, so a seat is always asked for a
  new directive **on the turn the sun sets** (turns 30, 70, 110, …) and on the turn it rises. That is
  the decision the game is about, and a cadence that straddles nightfall would hide it.
- One game per episode (`maxGames = 1`). The map is mirror-symmetric, so there is no side to swap.
- The **lobby** runs at the starter's real-time 24 Hz before `Playing` (`startWaitTicks` = 48,
  `lobbyJoinTimeoutTicks` = 2400 = 100 s). Lobby ticks are not Lux turns; `gameTurn =
  sim.gameTicksElapsed()`, the starter's existing split.

### Turn and tick structure — the exact resolution order

Everything below is one tick of `sim.step`. Steps run in this order and nothing else mutates the
world. "Ascending unit id" means the global creation counter; "ascending tile index" means the cell
index. **An action that is illegal at the moment it is evaluated is discarded and costs no cooldown**
— the starter's repair-don't-punish discipline, applied to the sim.

1. **Directive install (directive turns only).** If `turn mod directiveEvery == 0`, the two directives
   collected by the decision layer *before* this tick is stepped (§Decisions) become each seat's
   `activeDirective`. The 13 structured bytes are written to the replay as an **input record** — they
   are load-bearing input, re-applied at playback before this same turn is stepped — and the
   human-facing `note`, `source` and `latency_ms` go out separately as a presentation chat record.
   The structured directive **is** mixed into `gameHash`; the `note` is **not**.
2. **Order compilation.** `micro.compileTurn(sim, seat)` (§Decisions → "The micro layer") emits at
   most one action per unit whose `cooldownTenths == 0` and at most one action per city tile whose
   `cooldownTenths == 0`, for seat 0 then seat 1. This is a pure function of `(world state,
   activeDirective, seat)`; it is the determinism boundary, and the browser runs the identical code.
3. **City-tile actions**, ascending tile index, seat 0 then seat 1:
   - `research` → `researchPoints[team] += 1`.
   - `build_worker` / `build_cart` → allowed only if `unitCount[team] < cityTileCount[team]` (S1's
     unit cap). The new unit appears **on that tile** with empty cargo and `cooldownTenths = 0`, is
     appended to the unit list with the next global id, and **cannot act until the next turn** (this
     turn's action list was fixed in step 2).
   - Any accepted city-tile action sets that tile's `cooldownTenths += 100`.
4. **Transfers**, ascending giver unit id. A unit with a `transfer(receiver, kind, amount)` action
   gives `min(amount, giverStock(kind), receiverFreeCargo)` of one resource kind to an **orthogonally
   adjacent unit of the same team**, evaluated against the already-updated cargo state, then
   `cooldownTenths += baseCooldown(giver)`. A transfer to a non-adjacent or dead unit is discarded.
5. **City building**, ascending unit id. A **worker** with `build_city` builds if and only if: its
   cell is `empty` terrain (not a resource tile), holds no city tile, and its cargo totals
   `wood + coal + uranium >= cityCost (100)`. It spends exactly 100 **units of resource** taken
   cheapest-first (wood, then coal, then uranium) and a city tile of its team appears on that cell.
   `cooldownTenths += 20`.
   - **Contested build:** if workers of **both** teams build on the same cell this turn, **neither**
     builds and neither spends. If two workers of the **same** team do, the lower unit id builds and
     the other's action is discarded.
   - The new tile joins the union of orthogonally adjacent same-team city tiles: if it touches one or
     more existing cities they **merge** into the lowest city id, fuels summing; if it touches none it
     forms a new city with `fuel = 0`. The tile's road level becomes 6.
6. **Movement.** Each unit with `move(dir)`, `dir ∈ {north, east, south, west}`, proposes the adjacent
   cell (`center` is not a move and costs no cooldown). Resolution:
   - **a.** A target that is off the board, or holds an **opponent** city tile, is illegal → the move
     is discarded.
   - **b. Blocking fixed point.** Mark every remaining move tentatively successful, then repeat until
     nothing changes: a move is **blocked** if its target cell is *not* a friendly city tile of the
     mover and is currently occupied by a unit that is either stationary or itself blocked. (This is a
     monotone fixed point, so it is order-independent and deterministic; at most `unitCount`
     iterations. It lets a column of units step forward together behind one that has somewhere to go,
     and it lets two adjacent units swap, both of which S1 allows.)
   - **c. Contention.** Among the survivors, group by target cell. For any target cell that is **not**
     a friendly city tile of *all* the movers targeting it, if two or more units target it, **all** of
     those moves are cancelled. Friendly city tiles accept any number of units (stacking is allowed
     only there).
   - **d.** Apply the survivors simultaneously. Each mover's `cooldownTenths += baseCooldown`; a
     **cart** that lands on a cell whose terrain is `empty` raises `road[cell] = min(6, road[cell]+1)`
     (resource tiles never take road). Cancelled moves cost no cooldown and increment
     `blockedMoves[team]`.
7. **Resource collection.** Only **workers** collect; carts have no mining rate (S1). For each kind in
   the fixed order **wood → coal → uranium**, for each tile `R` of that kind with `amount > 0` in
   ascending tile index:
   - `M` = the workers whose cell is `R` **or orthogonally adjacent to** `R`, whose team has
     researched that kind, and whose free cargo space is > 0, in ascending unit id.
   - Each would take `rate(kind)`: **wood 20, coal 5, uranium 2**. If `|M| * rate > amount`, each takes
     `amount div |M|` and the first `amount mod |M|` workers in `M` take one extra.
   - Each take is then clamped to that worker's free cargo (`cargoCap - totalCargo`), and `R.amount`
     drops by the sum actually taken. Cargo caps: **worker 100, cart 2000** (`totalCargo` counts
     resource units, not fuel).
   - Research gates: coal needs `researchPoints[team] >= 50`, uranium `>= 200`. Wood is always open.
8. **Deposit.** Every unit standing on a **friendly city tile**, ascending unit id, empties its whole
   cargo into that tile's city: `city.fuel += wood*1 + coal*10 + uranium*40`, cargo → 0. This happens
   every turn, day and night. It is the only way fuel enters a city.
9. **Night burn** — only when `turn mod 40 >= 30`:
   - **a. Cities first**, ascending city id. `upkeep = 23 * tiles - 5 * adjacentPairs`, where
     `adjacentPairs` counts unordered orthogonally-adjacent pairs of tiles inside that city. If
     `fuel >= upkeep`, `fuel -= upkeep`. Otherwise the **whole city is destroyed**: every one of its
     tiles is removed from the board (the cells keep road level 6), `cityTilesLost[team] += tiles`, and
     a `citylost` event is emitted.
   - **b. Units second**, ascending unit id. A unit standing on a friendly city tile that still exists
     pays nothing. Every other unit pays `workerUpkeep = 4` / `cartUpkeep = 10` **fuel** from its own
     cargo, spending whole resource units cheapest-first (wood 1, coal 10, uranium 40) until the paid
     fuel is `>= upkeep`; overpay is lost. A unit that cannot cover it even by spending everything
     **dies** and is removed (`unitsLost[team] += 1`, a `unitlost` event). Cities are settled before
     units on purpose: a unit sheltering in a city that just burned down pays its own upkeep this turn.
10. **Cooldowns.** Every unit: `cooldownTenths = max(0, cooldownTenths - (10 + 2 * road[cell]))`.
    Every city tile: `cooldownTenths = max(0, cooldownTenths - 10)`. Cooldown is stored in **tenths of
    a turn**; base costs are worker **20**, cart **30**, city tile **100**; a unit or tile may act only
    at `cooldownTenths == 0`. A worker on a fully paved road (level 6) recovers 22 tenths a turn and so
    acts every turn instead of every second turn — that is what a cart is *for*, and it is an integer
    transcription of S1's `1 + 0.2 × road` recovery.
11. **Wood regrowth.** Every wood tile with `0 < amount < 500` grows by `max(1, amount div 50)`, capped
    at 500. A wood tile mined to exactly 0 **never comes back** — the integer transcription of S1's
    1.02 growth rate, and the reason over-harvesting is a real mistake.
12. **Sim guard** (§Sim module). A trip raises `LuxGuardError` → `fault` / `sim_fault`.
13. **Hash and end check.** `replayWriter.writeHash(tick, sim.gameHash())`, then §End conditions.

### Scoring formula and sign

Measured at the final turn:

```
cityTiles[s]  = number of city tiles seat s owns
units[s]      = number of living units seat s owns
fuel[s]       = sum of city.fuel over all of seat s's cities
```

The **winner ladder**, in order, first difference decides:

```
1. cityTiles[s]  >  cityTiles[o]   ->  s wins        (the idea's "most city tiles at the end wins")
2. units[s]      >  units[o]       ->  s wins        (S1's own first tiebreak)
3. fuel[s]       >  fuel[o]        ->  s wins        (S1's second tiebreak)
4. otherwise                       ->  a tie
```

**The score the league ranks by is the match point:**

```
scores[s] = 1.0  if s won
          = 0.5  on a tie
          = 0.0  if s lost

win[s]    = (scores[s] == 1.0)
winner    = the winning seat index, or null on a tie
```

**Sign: higher is better, and no term is ever negative.** `scores[0] + scores[1] == 1.0` on every
episode without exception — a strict zero-sum duel, which is exactly the integrity property the idea
asks for and is what the platform's Elo (1000 start, K 32) wants to eat. A blowout and a one-tile win
are worth the same point on purpose: Lux margins are dominated by map luck in the first two cycles,
and paying Elo for margin would reward the seed rather than the play. The margin is still recorded —
`cityTiles`, `units`, `fuel`, `research`, `unitsBuilt`, `unitsLost`, `cityTilesBuilt`,
`cityTilesLost`, `resourcesMined` are all in `results` (§Server) and all on the endcard.

A `deadline` episode is scored by the **same ladder at the turn the clock stopped**, never zeroed, so
it stays rankable.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values. `results.endRule` carries the detail
and is a closed enum of exactly **five**.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `full_time` | `turn == maxTurns` (360 / 200). The normal path. |
| `complete` | `eliminated` | At the end of step 13, one seat has **zero city tiles and zero units**. That seat loses immediately (the other seat wins on rule 1 of the ladder, or on rule 2 if both are wiped out in the same night, or ties if both are empty). Nine nights is long enough that a total wipe-out is a real outcome and watching an empty board for 200 more turns is not. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **660**) elapsed. The engine stops at the current turn, settles with the **real** ladder at that turn, writes `results.json` and the replay, and exits 0. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted model was slow, not that the game broke. The budget guard (§Decisions) exists so it should never fire. |
| `fault` | `sim_fault` | `checkLuxInvariants()` tripped. Settled from the last completed turn, `stopDetail` names it, artifacts still written, exit 0. A defect — `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment. |

**Nothing a player container does can stop the clock.** A seat that never connects does not end the
episode: `lobbyJoinTimeoutTicks` expires, the no-show is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload (exactly
`{"message", "failed_policy_index"}`, lowest missing slot only), its side plays the `forester`
baseline for the whole episode, `deadSeats[s] = true`, and all 360 turns run. A seat that drops
mid-episode keeps playing on `forester` and revives on reconnect.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {forester, prospector}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=forester` (the starter's "anything unrecognised is the published default" rule). A
scripted policy seated as a champion is a failure state.

### The split: a sparse strategy directive over dense deterministic micro

This is the coordinator's rail and the shape the idea itself names ("LLM + scripted unit micro is a
proven pattern from the Kaggle leaderboard"). **360 turns × 2 seats of per-turn LLM calls is 720
calls; at even 3 s a call that is 2160 s of wall clock against a 720 s budget — a factor of three
over, before a single retry.** So:

- The **LLM decides strategy**, once every `directiveEvery = 10` turns: 36 directives per seat per
  episode. One directive is a nine-field object (§Reply schema) — a stance, a mining priority, a
  research target, what city tiles should build, worker and cart targets, a focus cell, and a night
  policy.
- The **deterministic micro layer compiles that directive into per-unit and per-tile actions every
  single turn**, for every unit and every tile the seat owns. It is a pure function of
  `(world state, directive, seat)` with no randomness and no network, it runs in microseconds, and
  **the browser runs the identical Nim code** — which is why the replay only has to carry 72
  directives rather than a per-unit action log.

The LLM therefore plays the game the idea describes ("one orders-bundle per turn", at the strategic
layer) and the micro plays the layer that the Kaggle corpus proves is better done by code.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/lux-ai/anthropic_api_key` — the hive
2026-08-23 scar), phase 60 greps the **game** log for `falling back` / `LLM provider is unavailable`,
and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No `USE_BEDROCK` flag
on the policies: the player pod makes no LLM call.

`src/lux/llm.nim` is `src/ctf/llm.nim`, forked with **no behaviour change**:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every directive turn falls back instantly with no network wait, so
  offline certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900`. **No `output_config.effort`** when the model string contains `haiku` or
  `4-5`. Bedrock bodies carry `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, with the first-brace..last-brace rescue) and rune-boundary truncation
  (`runeLen` / `runeSubStr`) kept unchanged.

### Cadence, batching, and the wall-clock arithmetic

At each directive turn the server builds **both** seats' request bodies and issues them as **ONE
PARALLEL BATCH** — `client.curl.makeRequests(batch, deadlineMs div 1000)`, the shape of the starter's
`decide.turn`. Seats are **never** queried sequentially: this is a simultaneous-decision game and
serial calls would double the wall clock for nothing. At most 2 calls in flight; at most
`2 × 36 × 2 = 144` calls per episode including retries. Scripted seats compute locally, instantly, and
consume no request.

```
attempt1Ms                          7.0 s   (whole seconds: sim_config.validate rejects anything
retryMs                             3.0 s    else, because curl's CURLOPT_TIMEOUT is second-grained)
turnBudgetMs                       11.0 s   (monotonic deadline around the whole directive turn;
                                             attempt1Ms + retryMs = 10 s <= 11 s, which validate checks)
turnSpacingMs                       6.0 s   -> 2 seats x 60/6 = 20 req/min  (sidecar cap: 30)

36 directive turns x max(spacing 6 s, budget 11 s), absolute worst   = 396 s
   typical (haiku answers in ~3-4 s, so the spacing floor dominates) = 216 s
360 turns of integer sim + micro for both sides, fastMode            =   3 s
lobby / connect wait (typical 12 s; cap lobbyJoinTimeoutTicks 2400)  =  12 s   (cap: 100 s)
gameOverTicks hold + results + replay write (retrying uploader)      =  20 s
                                                                     -------
typical total                                                        = 251 s   < 720 s
absolute worst case (396 + 3 + 100 + 20)                             = 519 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                              = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                                = 1200 s
```

**720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_lux_manifest.nim` asserts it.**

**Rate guard.** `turnSpacingMs` pins the steady state at 20 req/min, but a directive turn in which
both seats retry issues 4 requests. The engine keeps a **rolling 60 s request counter**: if issuing the
next batch would push the trailing-60 s count above **28**, the seats that would exceed it skip the
call for that turn and take the `forester` directive with `cause = "rate_guard"`. Bounded, logged,
never a sleep on the critical path (the raid round 2 sidecar-throttle scar).

**Budget guard (settle early rather than overrun).** At the start of each directive turn, if
`elapsed + 2 * (turnSpacingSeconds + turnBudgetSeconds) > wallClockBudgetSeconds` (a 34 s reserve at
the shipped settings), the LLM is switched off for **every remaining directive turn**, both sides
finish on the scripted layer at microseconds per turn, and the episode ends `complete`/`full_time`
rather than `deadline`. A `budget_guard` record names the turn it fired.

`fastMode: true` in every variant: seats send no per-tick inputs (the server computes every action),
so the Sprite v1 Ready-packet dead-reckoning hazard `docs/PROTOCOL.md` warns about cannot arise here.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs` monotonic deadline, the rate
guard, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread (which
runs independently of the game loop, so an 11 s LLM stall can neither drop a connection nor stall
`/healthz`), the 660 s engine stop, and ctf's `gameOverTicks` hold before exit.

On a seat's **timeout, transport error or parse failure**: **retry once** in the next batch (a
`throttled` failure with no other candidate model **skips the retry outright** — it cannot land — and
fails fast to the scripted layer for that turn, the starter's behaviour, kept). On the second failure
that seat's directive for that turn becomes the **`forester`** scripted directive, computed inside the
game by **the same proc the `forester` baseline uses** — imported, never duplicated, so the fallback
and the filler cannot drift — and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns[s]` counts them.

**No failure mode leaves a unit unactuated.** The micro always has a directive: this turn's, else last
turn's, else `forester`'s (the starter's `repairMissingOrders` ladder, kept). Turn 0's default before
any reply lands is `forester`'s.

### Per-seat observation: exactly what is visible and what is hidden

**Lux Season 1 is a FULLY OBSERVABLE game, and this port is too — say it plainly: no fog of war, no
hidden units, no hidden resources, no hidden research counts.** Both seats see the entire board, both
sides' units and cities, both sides' fuel and research points, every resource tile's remaining amount
and every road level. Fog of war is Season 3 and is in §Out of scope. `fullyObservable: true` in every
variant, and `tests/test_lux_observation.nim` asserts that a seat's observation of the opponent's
public state is byte-identical to the opponent's own.

**Hidden from a seat — and this is the complete list:**

- The **opponent's directive** for the turn being decided (both are decided simultaneously) **and for
  every past turn**. A directive is a plan, not a game-state fact; the opponent's *actions* are fully
  visible on the board, its *reasoning* never is.
- The opponent's `note` — ever. `note` is spectator-only: it reaches the match feed and the replay and
  is never shown to the other seat.
- Every seat's `PLAYER_PROMPT`, and the identity of any policy: real player and policy names never
  reach a prompt or an observation. Only `RED-alpha` / `BLUE-alpha`.
- The episode **seed** and the `mapRng` state (the map is already fully revealed, so this hides
  nothing about the present — it only stops a seat from fingerprinting a map pool across episodes).
- Any seat's fallback/latency statistics.

**There is no inter-seat channel of any kind.** No chat, no radio, no `say`. Lux S1 has none, and in a
two-seat zero-sum duel a text channel is a collusion surface with no gameplay upside. The idea's
integrity note ("2-player zero-sum; maps seeded") is satisfied exactly.

The observation is built server-side, appended to the user message, and mirrored (verbatim) into the
replay's `directive` chat record, so the replay explains every decision. It is **bounded independently
of how many units are alive**, because the LLM commands a strategy and not individual units. Three
ASCII layers, `mapSize` lines each, plus bounded structured blocks:

```json
{
  "you": "RED-alpha", "side": "left", "opponent": "BLUE-alpha",
  "turn": 110, "of": 360, "directive_turn": 11, "of_directives": 36,
  "phase": "night", "cycle": 3, "turns_to_dawn": 0, "turns_to_dusk": 20,
  "map": {
    "size": 16,
    "terrain": [".....ww.........", "....www.........", "…16 lines…"],
    "cities":  ["................", "....RR..........", "…16 lines…"],
    "units":   ["................", "....r...........", "…16 lines…"],
    "legend": {"terrain": ". empty, w wood, c coal, u uranium",
               "cities":  ". none, R RED city tile, B BLUE city tile",
               "units":   ". none, r RED worker, R RED cart, b BLUE worker, B BLUE cart, * two or more"}
  },
  "resources": {
    "wood":    {"tiles_left": 31, "amount_left": 4820, "yours": 2110, "theirs": 2710, "researched": true},
    "coal":    {"tiles_left": 12, "amount_left": 3960, "yours": 2000, "theirs": 1960, "researched": true},
    "uranium": {"tiles_left":  4, "amount_left": 1300, "yours":  650, "theirs":  650, "researched": false},
    "richest": [{"kind": "coal", "cell": [3, 11], "amount": 400},
                {"kind": "wood", "cell": [5, 2],  "amount": 388},
                "… at most 6, richest first …"]
  },
  "yours": {
    "research": 118, "research_to_uranium": 82,
    "city_tiles": 7, "cities": 2, "workers": 5, "carts": 1,
    "unit_cap_headroom": 1,
    "cargo_carried": {"wood": 140, "coal": 55, "uranium": 0},
    "city_list": [
      {"id": 0, "tiles": 5, "fuel": 906, "upkeep_per_night_turn": 95,
       "survives_tonight": true,  "turns_of_fuel": 9, "cells": [[4,7],[5,7],[5,8],[6,8],[6,9]]},
      {"id": 3, "tiles": 2, "fuel":  61, "upkeep_per_night_turn": 41,
       "survives_tonight": false, "turns_of_fuel": 1, "cells": [[2,12],[2,13]]}
    ],
    "gathered_since_last_directive": {"wood": 410, "coal": 60, "uranium": 0},
    "built_since_last_directive": {"city_tiles": 2, "workers": 1, "carts": 0},
    "lost_since_last_directive": {"city_tiles": 0, "units": 1}
  },
  "theirs": {
    "research": 54, "city_tiles": 6, "cities": 1, "workers": 6, "carts": 0,
    "city_list": [{"id": 1, "tiles": 6, "fuel": 1402, "upkeep_per_night_turn": 113,
                   "survives_tonight": true, "turns_of_fuel": 12,
                   "cells": [[11,7],[10,7],[10,8],[9,8],[9,9],[11,6]]}]
  },
  "standing": {"city_tiles": [7, 6], "leader": "RED-alpha", "margin": 1},
  "your_last_directive": {"stance": "expand", "mine": ["wood","coal","uranium"],
                          "research": "coal", "build": "auto", "workers": 6, "carts": 1,
                          "focus": [3, 11], "night": "shelter"},
  "how_it_went": "5 workers mined 410 wood and 60 coal; 2 city tiles built; 1 worker died at (13,4) outside a city"
}
```

Field rules. `city_list` is capped at the **8 largest cities** per side (ties by lowest city id) with
`"cities_omitted": N` added when there are more; `cells` inside a city entry is capped at **12** cells
(`"cells_omitted": N`). `richest` is at most 6 entries. `how_it_went` is generated by the engine, never
by a model, and is capped at 240 runes. Every count is an integer; there are no floats anywhere in the
observation. At 16 × 16 the whole object is ≈ 2.6 KB.

### Reply schema and per-field caps

The LLM must return this object; **the scripted baselines produce the identical shape** through the
identical validator, which is what makes the bounded-orders test in §Tests meaningful.

```json
{"stance": "expand",
 "mine": ["wood", "coal", "uranium"],
 "research": "coal",
 "build": "auto",
 "workers": 6,
 "carts": 1,
 "focus": [3, 11],
 "night": "shelter",
 "note": "take the coal belt at column 3 before they research; two tiles on the wood edge"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `stance` | string | **≤ 10 runes**; enum `expand` \| `fuel` \| `research` \| `contest` \| `turtle` | lower-cased, `-`/space → `_`; still unknown → keep last turn's, else `expand` |
| `mine` | array | **≤ 3 entries**, each **≤ 8 runes**, from `wood` \| `coal` \| `uranium`; duplicates dropped; missing kinds appended in the order `wood, coal, uranium` | non-array or empty → `["wood","coal","uranium"]` |
| `research` | string | **≤ 8 runes**; enum `none` \| `coal` \| `uranium` \| `always` | unknown → `coal` |
| `build` | string | **≤ 8 runes**; enum `auto` \| `city` \| `worker` \| `cart` | unknown → `auto` |
| `workers` | integer | **0 … 40**, clamped; numeric strings accepted | missing / non-finite → keep last turn's, else 6 |
| `carts` | integer | **0 … 10**, clamped | missing / non-finite → keep last turn's, else 1 |
| `focus` | `[int,int]` or `null` | each clamped to `[0, mapSize-1]`; an `{"x":…,"y":…}` object accepted | missing / unparseable → `null` (the micro picks its own targets) |
| `night` | string | **≤ 8 runes**; enum `shelter` \| `mine` \| `haul` | unknown → `shelter` |
| `note` | string | **≤ 160 runes** (`MaxNoteRunes`), **spectator-only** — feed + replay, never shown to the other seat | truncated to 160 **runes**; newlines collapse to spaces (`sanitizeNote`) |
| whole reply | bytes | **≤ 4096** read from the provider before parsing | over-long is truncated then parsed |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration | truncated, never rejected; never written to the replay or results |

Two further caps on strings that reach the replay: `register.policy` **≤ 64 runes**
(`MaxPolicyLabelRunes`) and any recorded error text (`fallback.detail`, `results.stopDetail`)
**≤ 200 runes** (`MaxFallbackDetailRunes`).

**Truncation is on RUNE (Unicode codepoint) boundaries, never bytes** — the starter's `truncateRunes`
(`runeLen` / `runeSubStr`). Slicing a `string` by byte index on any path to the replay is forbidden. A
byte-truncated multi-byte character is exactly the bug that makes replay bytes render in a browser but
fail a strict parser; §Tests pins it with a 4-byte emoji sitting on every cap.

**Parsing is tolerant** (the starter's `parseSquadDirective`, retargeted): strip markdown fences; take
the outermost balanced `{…}` if the model prefixed prose; accept numeric strings; normalise enum case
and separators. **Unknown top-level keys are ignored. A reply with a valid `note` and no usable field
is usable** — the seat keeps its current directive and the note reaches the feed. Only when **no**
JSON object at all can be recovered do the retry and then the fallback fire. Every repaired field is
counted in `results.directivesRejected[s]` and reported nowhere to the model except through the effect
it has.

### System prompt (fixed; identical for both champions)

Sent as the system message.

```
You command ONE SIDE of a Lux AI Season 1 game on a 16 by 16 mirrored island. You
are RED or BLUE; the other side is played by someone you cannot talk to and whose
plans you cannot see. Everything else is public: the whole map, every unit, every
city, both research counts, every resource amount.

THE CLOCK
360 turns. Each 40-turn cycle is 30 turns of DAY then 10 turns of NIGHT.
Nine cycles. There are no surprises in the clock; plan around it.

THE RULES THAT DECIDE GAMES
- Workers mine 20 wood, 5 coal or 2 uranium per turn from any tile they stand on
  or stand next to. A worker carries 100 units total. A cart carries 2000 and
  cannot mine at all, but it paves roads where it drives and roads make everyone
  on them move twice as often.
- Fuel value: 1 wood = 1, 1 coal = 10, 1 uranium = 40. Coal needs 50 research
  points, uranium needs 200. A city tile spends its whole turn to earn ONE
  research point, so research costs you workers.
- A unit standing on your own city tile empties its cargo into that city as fuel,
  every turn, automatically.
- A worker holding 100 units of anything can BUILD A CITY TILE on an empty square
  (not on a resource square). That is how you score.
- You may never own more units than you own city tiles.
- EVERY NIGHT TURN each city pays 23 fuel per tile, minus 5 for each pair of its
  tiles that touch. A 6-tile blob in a line pays 113 a turn, 1130 for the night.
  A city that cannot pay is DESTROYED ENTIRELY, every tile, that instant.
  Units outside a city burn their own cargo at night: 4 fuel a worker, 10 a cart.
  A unit that cannot pay dies. Units inside your city pay nothing.
- Wood regrows about 2% a turn, but a wood tile mined to exactly zero is gone for
  good. Coal and uranium never regrow.

HOW YOU PLAY
You do NOT move units. Every 10 turns you send ONE strategy object, and a
deterministic controller executes it for the next 10 turns: it assigns every
worker to the best tile of your chosen resource, walks them home to deposit,
plants city tiles when they are full, drives your carts, and tells your city
tiles what to build. It never disobeys and it never improvises a strategy.

WINNING
Most city tiles standing at turn 360. Ties go to most units, then most fuel.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with { and end
with }. No prose, no markdown, no code fences.
{"stance":"expand|fuel|research|contest|turtle",
 "mine":["wood","coal","uranium"],          the order your workers prefer
 "research":"none|coal|uranium|always",     how far city tiles research first
 "build":"auto|city|worker|cart",           what an idle city tile does
 "workers":6, "carts":1,                    target counts, 0-40 and 0-10
 "focus":[x,y] or null,                     where the expansion effort aims
 "night":"shelter|mine|haul",               what units do during night turns
 "note":"<=160 chars, for the audience watching the replay - the other side
         never sees it"}

WHAT THE STANCES DO
expand  - workers that fill up plant city tiles near your cities and near `focus`.
fuel    - workers that fill up walk home and deposit instead of building.
research- as `fuel`, and city tiles keep researching past the target.
contest - as `expand`, but city tiles are planted next to the resource tiles
          NEAREST THE OPPONENT, to deny them.
turtle  - nobody builds; everything hauls into the largest city you own.
```

**User message** = the seat's `PLAYER_PROMPT` under the starter's "GUIDANCE FROM YOUR OPERATOR"
heading (`operatorBlock`), a blank line, then the observation JSON above.

### Champion #1 — `lux-ai-lumberjack` (owner **daveey**), `PLAYER_PROMPT`

```
Wood first, cities second, research only when the wood tells you to.
Cycle 1 (turns 0-39): stance "expand", mine ["wood","coal","uranium"], research
"coal", build "auto", workers 6, carts 0, night "shelter", focus on the richest
wood tile on YOUR half. Six workers on wood out-builds anything else in the first
cycle and city tiles are what you are scored on.
From cycle 2 on, look at "turns_of_fuel" for EVERY city in your city_list before
anything else. If any city shows survives_tonight false, switch stance to "fuel"
for that directive and set night "haul": losing a 5-tile city costs you five
points of score and it takes two cycles to rebuild them. Never let a city die to
save a worker.
Grow city tiles in a COMPACT BLOB, not a line: set focus to a cell orthogonally
adjacent to your largest city, because every touching pair takes 5 fuel a turn off
the bill and a 3x3 block of 9 tiles pays 147 a turn where 9 separate tiles pay 207.
Research target stays "coal" until research reaches 50, then set research "none"
and put every city tile on building workers up to the unit cap. Do not chase
uranium: 200 research points is six full cycles of a city tile doing nothing, and
the wood on a 16x16 map lasts about that long.
Keep carts at 0 until you own 8 city tiles, then exactly 1, and set focus to your
coal cluster so the cart paves the road between the coal and your blob.
If your wood "amount_left" on your side drops under 800, switch mine to
["coal","wood","uranium"] immediately - a wood tile mined to zero never comes back
and you want the last few hundred wood kept alive and regrowing.
```

### Champion #2 — `lux-ai-nightwatch` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win the second half. Cheap fuel loses to dense fuel, and coal is ten wood a unit.
Cycle 1: stance "research", mine ["wood","coal","uranium"], research "coal",
build "auto", workers 4, carts 1, night "shelter", focus on your start city. Four
workers is enough to keep one small city alive through night 1 while your city
tiles bank research points. Do not build a third city tile in cycle 1; you cannot
feed it yet.
The moment "researched" is true for coal, switch mine to ["coal","wood","uranium"]
and focus to the richest coal tile on your half. One worker on coal brings home 50
fuel a turn where a worker on wood brings 20 - after that, every night is cheap
and you spend the daylight planting tiles instead of hauling sticks.
Then set research "uranium" and leave it there. 200 points is affordable once your
cities are not starving, and a single uranium worker is 80 fuel a turn. If you get
uranium before turn 240, set stance "expand", workers 10, carts 2 and plant a tile
every time a worker fills.
Always keep carts >= 1 from cycle 2 on and set focus along the line between your
coal and your largest city: a paved road is a permanent doubling of everything
that walks on it, and it is the only compounding asset in this game.
On any directive turn where "turns_to_dusk" is 0 - you are being asked at
nightfall - set night "shelter" and stance "fuel" unless EVERY city shows
turns_of_fuel of 11 or more. Ten turns of night is the only thing that can kill
you; nothing on the board can.
If the standing shows you 3 or more city tiles behind after turn 240, switch
stance to "contest" and focus on the opponent's richest resource tile: at that
point denying their last wood belt is worth more than one more tile of your own.
```

### The micro layer (deterministic, shared by every policy)

`src/lux/micro.nim`, forked from `src/ctf/control.nim` (directive → per-tick actuation), retargeted
from pixel steering to Lux's discrete actions. It runs once per side per turn and is the **only**
producer of actions. **There is no randomness in it at all.**

`path(from, goal, unit)` is a breadth-first search, 4-connected, over the board: passable = every cell
except opponent city tiles; other units are **not** obstacles in the plan (they move). Neighbours are
expanded in the fixed order `north, east, south, west`, so the path is unique. Flow fields are cached
per `(goal cell, team)` and recomputed at most once per turn per distinct goal.

**Roles.** At each directive turn, units are sorted by unit id. The first
`min(directive.carts, cartsAlive)` carts are **haulers**; every other cart is a hauler too (there is
nothing else for a cart to do). Every worker is a **miner**; the role is re-derived every turn from the
world state, so a dead unit changes nothing.

**Per worker with `cooldownTenths == 0`, in ascending unit id:**

1. **Night policy.** If it is a night turn and `directive.night == "shelter"`: if the worker is on a
   friendly city tile, emit `center` (it deposits and pays nothing). Otherwise emit the first step of
   `path(cell, nearest friendly city tile)`, ties by lowest cell index; if there is no friendly city
   tile, fall through to step 2. `night == "mine"` falls through to step 2 unconditionally.
   `night == "haul"` treats the worker as if `stance == "fuel"` for the rest of this step list.
2. **Full or nearly full** (`totalCargo >= cityCost (100)`):
   - `stance ∈ {expand, contest}` (or `build == "city"`): compute the **build target**.
     - `expand`: the `empty`, city-tile-free cell minimising
       `bfs(worker, cell) + 2 * chebyshev(cell, focus)` (the `focus` term is dropped when `focus` is
       null) among cells that are orthogonally adjacent to one of this side's city tiles if any such
       cell lies within `buildRadius = 6` of the worker; otherwise among cells orthogonally adjacent
       to any resource tile; ties by lowest cell index. Preferring a cell that touches an existing
       tile is what makes the 5-fuel adjacency discount happen without the LLM having to micro it.
     - `contest`: the same, but the candidate set is cells orthogonally adjacent to the **resource
       tile nearest the opponent's nearest city tile**.
     - If the worker is standing on the target → `build_city`. Else → the first step of the path.
   - Otherwise (`stance ∈ {fuel, research, turtle}`) → path to the nearest friendly city tile
     (`turtle`: to the **largest** friendly city, ties by lowest city id) and, on arrival, `center`.
3. **Mining.** Choose the **target tile**: over the kinds in `directive.mine` order, the first kind the
   team has researched and that has a tile with `amount > 0`; among that kind's tiles, minimise
   `bfs(worker, tile) + 2 * (number of this side's workers already assigned to that tile this turn)`,
   ties by lowest cell index. The congestion term is what spreads six workers over a wood cluster
   instead of stacking them on one square. If the worker is already on or orthogonally adjacent to the
   target → `center` (collection is automatic in step 7). Else → the first step of the path.
4. **Transfer to a cart.** Before steps 2 and 3, if a friendly **cart** with free cargo is orthogonally
   adjacent and this worker's `totalCargo >= 40` and the nearest friendly city tile is more than 4
   cells away, the worker emits `transfer(cart, its largest resource kind, its whole stock of it)`
   instead. That is the cart's entire reason to exist and the micro, not the model, arranges it.
5. If BFS finds no path at all → `center`.

**Per cart with `cooldownTenths == 0`:** if `totalCargo > 0` → path to the nearest friendly city tile
and `center` on arrival (deposit is automatic). Else → path to the friendly worker with the largest
cargo whose distance to the nearest friendly city tile is ≥ 4, ties by lowest unit id; `center` when
orthogonally adjacent to it.

**Per city tile with `cooldownTenths == 0`, in ascending tile index:**

1. `researchTarget = 0 / 50 / 200 / 200` for `research ∈ {none, coal, uranium, always}`. If
   `researchPoints[team] < researchTarget`, or `research == "always"` → `research`.
2. Else if `build == "city"` → no action (the tile idles; workers do the building).
3. Else if `unitCount[team] < cityTileCount[team]` and `carts < directive.carts` → `build_cart`.
4. Else if `unitCount[team] < cityTileCount[team]` and `workers < directive.workers` → `build_worker`.
5. Else → no action.
   `build == "worker"` forces rules 3 and 4 to `build_worker`; `build == "cart"` forces them to
   `build_cart`.

**The micro never emits:** a move off the board, a move onto an opponent city tile, a `build_city` on a
resource tile or an occupied cell or with under 100 cargo, an action for a unit or tile with
`cooldownTenths > 0`, more than one action for any unit or tile in a turn, or a `pillage` (pillage does
not exist in v1 — §Out of scope). `tests/test_lux_micro.nim` asserts every one of those.

### Scripted baselines (both shipped as fillers; `forester` is also the server-side fallback)

`src/lux/baselines.nim`, the starter's module retargeted. Both emit the **same** directive object an
LLM does, through the same validator, and both are pure functions of the **public** world state, which
is what makes the bounded-orders test meaningful. Neither ever writes a `note` — they are the sides
that do not explain themselves. Both are documented in `docs/RULES.md`.

**`forester`** — `PLAYER_SCRIPTED=forester`, the certification player, the per-turn fallback, the
driver of a no-show or disconnected seat, and the default. The strong simple Lux opening, held all
game:

```
stance   = "fuel" if any city of mine has fuel < 11 * upkeepPerNightTurn, else "expand"
mine     = ["coal","wood","uranium"] if researchPoints >= 50 else ["wood","coal","uranium"]
research = "coal" if researchPoints < 50 else "none"
build    = "auto"
workers  = 8
carts    = 1 if cityTiles >= 8 else 0
focus    = the cell orthogonally adjacent to my largest city that is nearest a
           wood tile with amount > 0 (ties by lowest cell index), else null
night    = "shelter"
```

**`prospector`** — `PLAYER_SCRIPTED=prospector`, the second filler, deliberately different in
**shape** so the ladder gets a spread rather than two versions of one bot: it buys the fuel ladder
early and pays for it in tiles.

```
stance   = "research"  while researchPoints < 200
         = "expand"    once researchPoints >= 200
mine     = ["uranium","coal","wood"] if researchPoints >= 200
         = ["coal","wood","uranium"] if researchPoints >= 50
         = ["wood","coal","uranium"] otherwise
research = "uranium" while researchPoints < 200, else "none"
build    = "auto"
workers  = 5 while researchPoints < 200, else 10
carts    = 2
focus    = the richest tile of the highest researched kind on my half, else null
night    = "shelter"
```

`forester` beats `prospector` at the pinned seed on the `duel` variant — 200 research points is six
cycles of city tiles doing nothing — and `tests/test_lux_baselines.nim` asserts it. It is a real bar
for a champion to clear, and `prospector` is the control that answers "did the LLM actually adapt?".

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/lux/`. The fork is a rename sweep
(`ctf` → `lux`, `CtfError` → `LuxError`, `COWLDCTF` → `COWLDLUX`; a CI grep asserts no `ctf_`/`CTF_`
identifier survives outside comment history **and outside the two documented `CTF_WIRE` alias lines**
in §Viewer) plus the changes below. **The same modules compile twice**: natively into `/bin/lux-ai`
for the server, and to wasm through `replay-viewer/config.nims` (`switch("path", rootDir / "src")`)
for the viewer — which is the whole reason the game lives in the starter's language.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/lux/server.nim` | **fork**, four named edits below | mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, `/reward`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop, the bounded post-artifact shutdown grace |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/lux/` | **fork** (magic + game name only: `COWLDCTF` → **`COWLDLUX`**) | the whole replay codec, keyframes (`ReplayKeyframeTicks` 100), `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/lux/` (`control.nim` → `micro.nim`) | **fork**, retargeted not rewritten | the parallel batch, the two whole-second deadlines, `turnSpacingMs`, the budget guard, `throttled` fail-fast, tolerant parsing, rune caps, `repairMissingOrders`, the BFS/flow-field cache |
| `src/ctf/sim_state.nim` → `src/lux/sim_state.nim` | **fork** | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/lux/roster.nim` | **fork**, one named edit below | join/auth/identities/`IdentityNames`/**`cogAlias` untouched**/the results JSON builder |
| `src/ctf/events.nim` → `src/lux/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/lux/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline, the `lead` series — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/lux/global.nim` | **fork**, three named edits below | the sprite/object pools, the pixie compositor, the FX families, the baked-floor path |
| `src/ctf/sim_types.nim` → `src/lux/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), the flatty wire types (field order sacred), `MaxNoteRunes = 160`, `MaxPolicyLabelRunes = 64`, `MaxFallbackDetailRunes = 200`, `MaxPromptRunes = 4000`, `TargetFps`/`ReplayFps` |
| `src/ctf/sim_config.nim` → `src/lux/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, `validate` (incl. the whole-second and `attempt1Ms + retryMs <= turnBudgetMs` checks) |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf.nim` → `src/lux_ai.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so every seed-derived draw follows the final seed |
| `src/paintball_player.nim` → `src/lux_ai_player.nim` | **fork** | the thin seat registrar (§Server) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `client/replay_broadcast.html`, `client/league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/lux_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_{red,blue}.png`, `data/soldier_{red,blue}_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*,blue_*}.webp` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, fog-of-war
shadowcasting and the first-person PIP, spray cans, floor paint, the paint grid and the paint buff,
King of the Hill and `hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers,
grenades and the barrage, med kits, shields, cardboard barriers, puddles, trenches, perks, handicaps,
hit points, lives, respawns and kills (nothing in Lux can be shot), shouts-as-cog-speech, the
achievements catalog, campaign mode, `maxGames > 1` side-swapping, four-team play, and **all of the
pixel-space map machinery**: `arena.nim`'s per-pixel wall masks and pixel queries, `map_art.nim`'s
procedural arena bake, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`,
`docs/pool-review.html`. The board here is a 16 × 16 integer grid generated by the formula in §The
game; every one of those is a config surface the Lux rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `rig_real/`, and the green/yellow
soldier families — this game has exactly two sides).

### New modules

- `src/lux/board.nim` — the seeded symmetric generator of §The game, the terrain/amount/road arrays,
  cell↔index helpers, the mirror check, and BFS + the per-turn flow-field cache. Pure integer.
- `src/lux/units.nim` — the unit arrays (`id`, `team`, `kind`, `cell`, `wood`, `coal`, `uranium`,
  `cooldownTenths`), the global id counter, cargo helpers and the fuel-value table.
- `src/lux/cities.nim` — city tiles, the city union-find (build, merge, destroy), `upkeep`,
  `adjacentPairs`, fuel, and the per-city survival projection the observation reports.
- `src/lux/resolve.nim` — steps 3–11 of §Turn and tick structure, in that order, including the
  movement fixed point and the collection split.
- `src/lux/scoring.nim` — the winner ladder, `scores`, `win`, `winner`, and the per-seat counters.
- `src/lux/micro.nim` — the compiler of §Decisions.
- `src/lux/sim.nim` — the step loop; imports and re-exports the sim modules as the starter's does, so
  `import lux/sim` sees everything.

### The four named edits to `server.nim`

1. **Directive turn.** The starter's turn-boundary block, with `turnTicks` replaced by
   `directiveEvery` and two seats in the batch instead of the starter's squad count, plus the
   structured-directive input-record write.
2. **Registration interception.** A player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration and is **not** applied as a bubble and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim (the paintball round-3 scar, where a champion played the baseline for a whole episode).
   Any other chat text from a seat is dropped — this game has no inter-seat channel.
3. **Wall-clock stop.** The starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`, **and
   writing the load-bearing `stop` record** (the particle-worlds r2 scar: the stop is a wall-clock
   fact no re-simulation can derive, so it is recorded and applied on both sides by one proc,
   `sim.applyWallClockStop`).
4. **Elimination check.** After step 13, the `eliminated` end rule of §End conditions.

### The one named edit to `roster.nim`

`squadResultsJson` becomes `luxResultsJson` — two entries in every seat-indexed array, keys exactly as
§Server lists them. `cogAlias`, `slotIdentityIndex`, `shoutIdentityName` and `IdentityNames` are
**untouched**, so the two-name-space rule and its inherited test apply with no further change.

### The three named edits to `global.nim`

1. **The board is baked floor art, not sprites.** At reset, pixie composites one board bitmap: the
   tiled `data/arena_floor.png` darkened 18 %, a 1 px chalk grid, resource tiles as textured chips
   (wood = a green canopy cluster, coal = a dark faceted chip, uranium = a pale chip with a glow ring),
   and roads as lighter paving. Only the *amount* overlays and the mutable layers (city tiles, units,
   the night wash) are drawn per frame, so a 256-cell board is one blit plus a bounded number of
   chips. This is the same path the starter uses to bake endzone paint.
2. **Night is `#lightpool`.** The starter already ships a full-stage `#lightpool` element and its
   compositing rule; night turns drive its alpha from 0 (day) to 0.55 (deep night) over the two turns
   either side of the boundary, and city tiles get an additive warm glow whose radius scales with
   `min(6, fuel div (10 * upkeep))`. A spectator can see which cities will survive the night without
   reading a single number.
3. **Unit chips.** `rig_art.nim`'s compositor bakes, at load, `data/soldier_{red,blue}.png` into unit
   chips at three sizes (10, 14, 20 px) × two kinds (worker, cart) × two cargo states (empty, laden) —
   24 pre-baked chips — plus a 3-segment cargo pip strip. Drawing sixty units a frame is sixty blits.
   No text is ever drawn at a negative coordinate: every label's reserved band is measured in the font
   it is drawn in (the cogchemists 2026-08-24 rule), which is why `--strict-text-bounds` stays on in CI.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cells, amounts, cargo, fuel, upkeep, cooldown tenths, BFS
distances, research points. There is no floating point anywhere in `board.nim`, `units.nim`,
`cities.nim`, `resolve.nim`, `scoring.nim`, `micro.nim`, `baselines.nim` or `sim.nim`, and a CI grep
over exactly those files for `float|sqrt|hypot|sin|cos|/ ` enforces it. Nothing in this game needs a
real number, which makes the native ↔ wasm hash chain exact by construction. `results.scores` (0.0 /
0.5 / 1.0) is produced at serialisation time from an integer `{0, 1, 2}` and never enters the sim.

Nim's `int` is 32-bit under `--cpu:wasm32`. City fuel is the one quantity that can grow: a cart of
uranium is 80 000 fuel and a long game can bank six figures, so **`city.fuel`, `resourcesMined` and
every episode total are `int64`**, while cell-scoped quantities stay `int32`. A guard asserts
`city.fuel >= 0` and `< 2^40` every turn.

**One RNG stream**, `mapRng`, derived from `seed`, consumed **only** by the map generator at reset and
never again — so nothing a policy does can steer a draw, and the map is a pure function of
`(seed, mapSize, cluster counts)`. That is the idea's "maps seeded" integrity pin, and
`tests/test_lux_board.nim` asserts it by generating from the same seed after different play.

The seed is randomised in `src/lux_ai.nim` **before** `config.update` (the starter's rule), recorded in
the replay config and in `results.seed`.

### Determinism, native ↔ wasm

The mechanism is ctf's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDLUX`** replay: magic + format version + game name/version header, the
   **resolved config JSON**, then the record stream — joins (name, slot, token), leaves, the
   **directive input records**, the presentation chat records, and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/lux_replay.nim` — which imports the **same**
   `src/lux/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `lux_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then `lux_frame`
   re-steps the sim — **re-running the micro layer from the recorded directives** — and compares
   `sim.gameHash()` against the recorded hash **every tick** (`checkReplayHash`). A single divergent
   bit is caught at the tick it happens and surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: `turn`; per unit in ascending id
   `(id, team, kind, x, y, wood, coal, uranium, cooldownTenths)`; per city tile in ascending cell index
   `(team, cellIndex, cityId, cooldownTenths)`; per city in ascending id `(id, team, fuel, tiles)`; per
   resource tile in ascending cell index `(kind, amount)`; every non-zero road cell `(cellIndex,
   level)`; `researchPoints[0..1]`; `unitsBuilt`, `unitsLost`, `cityTilesBuilt`, `cityTilesLost`,
   `blockedMoves` (both seats); and each seat's **structured directive** (the 13 bytes). The `note`,
   `source`, `latency_ms` and every policy label are **excluded** — the starter's rule that nothing a
   commander *says* may move the hash chain.

**The sim guard `checkLuxInvariants()`** (step 12), evaluated every turn: every unit is on the board
and not on an opponent city tile; no two units share a non-city-tile cell; every cargo component ≥ 0
and `totalCargo <= cargoCap`; every resource amount in `0 .. startAmount(kind) * 2`; every road level
in `0..6` and every city tile's road exactly 6; every city is a single orthogonally-connected component
of same-team tiles and every city tile belongs to exactly one city; `cityTileCount[s]` equals the sum
of its cities' tiles; `researchPoints[s] >= 0`; `unitCount[s] <= max(cityTileCount[s], 1)` at the
moment of a build; `turn <= maxTurns`; and the board is still mirror-symmetric in **terrain kind** (not
amounts — those diverge the moment anyone mines). A trip raises `LuxGuardError` → `fault`/`sim_fault`.

**Perf target:** 360 turns of both sides' micro plus resolution in under 3 s on a CI runner;
`tests/test_lux_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`,
`COGAME_METRICS_URI` out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode;
`COGAME_HOST`/`COGAME_PORT`; player sockets at `/player?slot=<i>&token=<t>` with a 403 on a bad
slot/token.

The certifier's browser probes are served **for real** and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket —
the lantern 0.1.1 cert probe), `GET /client/global`, the `/global` websocket's first message, and
`/healthz` — all kept answering for a bounded ~20 s grace after artifacts are written (lantern 0.1.3).
Global broadcasts are fire-and-forget so a slow spectator can never stall the episode.

### The player container

`src/lux_ai_player.nim` (built to `/bin/lux-ai-player`) is the starter's `src/paintball_player.nim`,
forked with the baseline names changed. It reads `COWORLD_PLAYER_WS_URL` (legacy alias
`COGAMES_ENGINE_WS_URL`), `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, dials with
bounded retries (240 × 500 ms), and sends **one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","policy":"<label, <=64 runes>",
 "prompt":"<PLAYER_PROMPT or empty, <=4000 runes>",
 "scripted":"forester"|"prospector"|null}
```

Registration is **re-sent** 10 times, ~1 s apart, over the first ~10 s of received frames, because
joins are slot-sequential and a seat whose slot is not the next open one is not admitted until the
lower slot has joined (the paintball round-3 scar). It then sends the Sprite v1 Ready packet (`0x85`)
after each received frame — legitimate here because it never sends inputs — and otherwise only
receives. A seat that never registers, or registers with neither field, is `scripted: "forester"`. The
receive loop is wrapped in `try/except CatchableError`, re-dials a dropped socket up to 6 times, and
**exits 0 on a dead socket** (the raid 0.1.3 scar: whisky's `receiveMessage` raises on a close frame
and the game's `quit(0)` can outrun the flushed `done` frame, so a naive player exits 1 and fails
certification intermittently).

### Results document

Written by `sim.luxResultsJson()` to `COGAME_RESULTS_URI`. It must equal the manifest's
`results_schema` key-for-key — that schema is `additionalProperties: false` and the certifier drops
unknown fields. Adding or removing a key means editing `coworld_manifest_template.json` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit. Exactly **27** keys:

```json
{"names":            ["daveey", "daveey-1"],
 "aliases":          ["RED-alpha", "BLUE-alpha"],
 "scores":           [1.0, 0.0],
 "win":              [true, false],
 "winner":           0,
 "reason":           "complete",
 "endRule":          "full_time",
 "cityTiles":        [9, 6],
 "units":            [7, 5],
 "fuel":             [1840, 905],
 "research":         [212, 54],
 "cityTilesBuilt":   [12, 9],
 "cityTilesLost":    [3, 3],
 "unitsBuilt":       [11, 8],
 "unitsLost":        [4, 3],
 "resourcesMined":   [[4210, 380, 86], [3980, 120, 0]],
 "nightsSurvived":   [9, 9],
 "blockedMoves":     [41, 66],
 "turnsPlayed":      360,
 "mapSize":          16,
 "seed":             1734029581,
 "policyKinds":      ["llm", "llm"],
 "llmTurns":         [36, 35],
 "fallbackTurns":    [0, 1],
 "directivesRejected":[0, 2],
 "deadSeats":        [false, false],
 "stopDetail":       ""}
```

`tests/test_lux_manifest.nim` asserts the exact key set in both directions. `names` are the **real
policy names** (spectator side); `aliases` carry the in-game names. **All twenty seat-indexed arrays**
(`names`, `aliases`, `scores`, `win`, `cityTiles`, `units`, `fuel`, `research`, `cityTilesBuilt`,
`cityTilesLost`, `unitsBuilt`, `unitsLost`, `resourcesMined`, `nightsSurvived`, `blockedMoves`,
`policyKinds`, `llmTurns`, `fallbackTurns`, `directivesRejected`, `deadSeats`) have exactly
`num_agents` = **2** entries — which is what `docker_smoke.sh` cross-checks against `SMOKE_SEATS`.
`resourcesMined[s]` is `[wood, coal, uranium]` in resource units. `winner` is an integer seat index or
`null` on a tie.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDLUX`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse.
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"lux-ai/v1","gameVersion":"1","seed":…,"mapSize":16,"names":[…],"aliases":[…],
  "policyKinds":[…],"turnCount":…,"directives":[…],"fallbacks":N,"results":{…}}` — by brace-matching
  the config JSON from the first `{` (the technique the starter's `AGENTS.md` documents for prod
  forensics) and decoding the record stream.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.cityTiles[]' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  jq -r '[.directives[]|select(.note!="")]|length' /tmp/ep.json
  ```
  Require `protocol == "lux-ai/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.cityTiles[0] + results.cityTiles[1] > 2` (somebody built something), the
  champion seats' directives with `source == "llm"` and non-empty `note`s — not all fallbacks —
  because a coworld about strategy whose replay contains no strategy is broken even if it is green.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDLUX`, format version, `gameName` `lux-ai`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `mapSize`, the three cluster counts and start amounts, `maxTurns`, `cycleLength`, `directiveEvery`, every rule constant (`cityCost`, rates, cargo caps, upkeeps, research thresholds, cooldowns, road cap), `players[].name` (**real** names), `slots[]`, `tokens[]`, `fastMode`, `fullyObservable` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| directive input records | per directive turn, per seat: the 13 structured bytes — **this game's entire input log**, load-bearing, applied before the turn is stepped |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The **map is re-derived** from the seed rather than being a load-bearing record (it is in `gameHash`
from turn 0, so a divergence surfaces immediately), which is why the file stays small: 360 hashes + 72
directive input records + 72 directive chat records + the config ≈ **60 KB**.

### Record and event vocabulary

**A. Replay records.** The directive's 13 structured bytes are an **input record** (load-bearing,
re-applied on playback). Everything below is a **chat record**: presentation-only, re-applied into
non-hashed fields, driving the feed and `replay_summary.py` — with the single documented exception of
`stop`.

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `seat`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, the nine directive fields, `note` (≤ 160 runes), `view` (the observation object verbatim) |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `turn`, `endRule` (`wall_clock`) — **the one load-bearing chat record**, applied on both sides by `sim.applyWallClockStop` before that turn's step (the particle-worlds r2 scar) |
| `result` | the full results document, written once at episode end — without it a spectator holding the file reads `results: {}` |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of eleven kinds:**

`phase` `{from,to}`; `dawn` `{cycle}`; `dusk` `{cycle, fuel:[2], cityTiles:[2]}`;
`citybuilt` `{seat, cell, cityId, tiles}`; `citylost` `{seat, cityId, tiles, cell}`;
`unitbuilt` `{seat, kind, cell}`; `unitlost` `{seat, kind, cell, cause}`;
`research` `{seat, kind, points}` (crossing 50 or 200); `depleted` `{kind, cell}` (a resource tile hits
0); `directive` `{seat, stance, note}`; `end` `{reason, endRule, cityTiles:[2], winner}`.

**Beats** — the scrubber markers, and the only kinds the appended game block emits, all bounded by
construction: **`dusk`** (≤ 9), **`research`** (≤ 4 — two thresholds × two seats), **`citylost`**
(throttled to one beat per seat per night, ≤ 18), **`end`** (1). At most 32 markers on a 360-turn
scrubber. `citybuilt`, `unitbuilt`, `unitlost`, `depleted`, `dawn` and `directive` drive the feed, not
the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `PhaseChange, Dawn, Dusk, CityBuilt, CityLost, UnitBuilt, UnitLost, Research,
Depleted, Directive, Fallback` and the mandatory trailing summary row (`type`, `ticks`, `events`,
`gameVersion`) kept.

### The state JSON a viewer reads

One object per presentation frame, from `buildStateJson` — identical live and in replay, and the
**only** thing the renderer reads. The inherited keys are unchanged: `t` (tick), `mt`, `ph`, `lob`,
`sp`, `mx`, `st`, `lp`, `sk`, `ff`, `en`, `mm` (mismatch tick), `bs` (board scale), `teams`, `roster`
(per seat: `s`, `team`, `name` — the **real** policy name, spectator side — `pol`, `col`, `alias`,
`seat`), `events`, `directives`, `lead` (sent once). lux-ai adds exactly these:

```json
{"turn": 214, "turns": 360, "cycle": 5, "night": true, "nightTurn": 4, "nightTurns": 10,
 "size": 16,
 "terrain": [{"i": 37, "k": "wood", "a": 288}, "… only tiles whose amount changed since the last frame …"],
 "roads":   [{"i": 84, "l": 3}, "… only cells whose road level changed …"],
 "cities":  [{"id": 0, "seat": 0, "fuel": 906, "upkeep": 95, "tiles": [71, 72, 88, 89, 105]},
             {"id": 1, "seat": 1, "fuel": 1402, "upkeep": 113, "tiles": [123, 122, 138, 137, 153, 107]}],
 "units":   [{"u": 3, "seat": 0, "k": "worker", "i": 70, "w": 60, "c": 0, "r": 0, "cd": 0},
             {"u": 9, "seat": 1, "k": "cart",   "i": 140, "w": 0, "c": 220, "r": 0, "cd": 10}],
 "res":     [212, 54],
 "score":   {"cityTiles": [7, 6], "units": [6, 7], "fuel": [967, 1402], "leader": 0},
 "dir":     [{"seat": 0, "turn": 210, "stance": "expand", "note": "coal belt at column 3"},
             {"seat": 1, "turn": 210, "stance": "fuel",   "note": ""}]}
```

`terrain` and `roads` are **deltas** (full arrays on the first frame and on every keyframe), which is
what keeps a 360-frame state stream small. `i` is always a cell index. `dir` carries the two most
recent directives, and is where the feed's commander lines come from.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` **under `game`**, and
`tools/build_replay_viewer.sh` is coworld-ctf's hook — kept, with the `image_tag` literal and the
`docker cp` source path (`/workspace/lux/replay-viewer/dist/.`) changed — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling, and it stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/lux_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks
the viewer silently (cogame-lantern, 2026-08-23). coworld-ctf's set is internally consistent and is
kept as one piece: the Worker sets `Module.onRuntimeInitialized`, the module is emitted
**non-modularized** as `lux_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang`
through `emcc`, `--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and silently corrupt the module's own globals),
`-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_lux_load_replay,_lux_frame,_lux_input,_lux_packet_ptr,
_lux_packet_len,_lux_mismatch_tick,_lux_error_ptr,_lux_error_len,_lux_stage_ptr,_lux_stage_len`; and
`static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './lux_replay.js')` in that order.

`lux_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `lux_load_replay` re-simulates the whole episode once headlessly (360
  turns of integer work — single-digit milliseconds in wasm), records the per-turn city-tile counts
  for both seats, the night spans, the lull spans and the beat turns, then resets and renders frame 0.
  That is what lets the city-tile lead graph and the scrubber beats draw at **full width on the first
  frame** instead of growing in.
- `lux_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (line 161 of the starter's file) — posted by
the Worker only *after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so
the attribute means "a frame is on the canvas", not "a file was fetched". **On failure the shell sets
`data-replay-error` on `<html>`** with the message, in `showFailure()` (line 8). Both signals are
coworld-ctf's own and are inherited **unchanged** — this fork adds neither and removes neither. The
`coworld-replay` postMessage bridge's `ready` is posted from a callback fired **after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied BYTE-FOR-BYTE from coworld-ctf.** Not edited, not reformatted,
  not one identifier changed; `tests/test_lux_viewer.nim` pins its sha256 against the starter's file.
  Everything lux-ai adds lives in the appended game block. Its `markBeat` / `renderBeatMarkers` /
  `ingestBeats` / `renderClock` / `renderTransport` / `ingestLullSpans` / `setVerdict` all remain, and
  `ingestBeats` ignores kinds it does not know.
  - Its line 72 reads `var WIRE = window.CTF_WIRE || {}`. Rather than edit a file the pin says must be
    byte-identical, `tools/gen_wire_constants.nim` emits **`window.LUX_WIRE={…};window.CTF_WIRE=window.LUX_WIRE;`**
    — the game's own code reads `LUX_WIRE`, and the one aliasing line exists solely to keep
    `chrome_common.js` untouched. Those two lines (the emitter and chrome_common's reader) are the
    **only** places `CTF_WIRE` survives, each carries a comment naming this note, and the CI rename
    grep excludes exactly them.
- **`client/replay_broadcast.html` is the starter's page WITH A GAME BLOCK APPENDED** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`,
  transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched; the
  appended `lux-` block replaces only the *contents* of the scorebug plates, adds the cycle bar, the
  research rail and the fuel strip, and retargets the feed rows, the beat rendering, the momentum
  series and the endcard columns. A test asserts the starter's byte prefix is intact up to the
  documented splice marker and that the file only **grows**. The starter's own appended PAINTBALL block
  is removed with the paintball mechanics, so the page carries exactly one game block.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. It is pinned function-by-function against the starter's text by
  `tests/test_lux_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  **`pushFeed` including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.LUX_WIRE` read at
  line 49. Deleted: every ctf-specific draw call and the FPV pipeline. Added: `drawBoard`,
  `drawResources`, `drawCities`, `drawUnits`, `drawNight`, `drawCycleBar`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `attachMinimap(...)` call. **Zoom decision: DROPPED.**
    The board is a fixed 16 × 16 (or 12 × 12) grid with no off-frame area and `relayout()` fits it
    whole at every width including 360 px (see "Legible at 360 px"), so per the pin a fixed arena drops
    `#viewpanel` entirely. `broadcast_core.js` tolerates a missing minimap (`pendingMinimap` stays
    null).
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no
    per-unit point of view worth showing; the whole island is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.squad`, `.pb-tags`, `#pb-regime`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture`, `.hillflip`, `.hillhold`, `.tagout`,
    `.gamestart` and `.gameover` CSS rules — none of those kinds is emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, **`#lightpool`** (retargeted to the night wash),
    `#grain`, `#lockerroom` (`#lk-bg`, `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug`
    with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#bannerlane`, `#killfeed`,
    `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
    `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`,
    `#tick-clock`, `#speedchips`), `#scrub` with `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/
    `#scrub-head`, `#endcard` with `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`,
    and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings. The re-labelings are
therefore enumerated here and enforced by `tests/test_lux_endcard_labels.nim`:

| Starter string | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` | `<span>Side</span><span>City tiles</span><span>Units</span><span>Fuel</span><span>Research</span>` |
| `<span class="fl-cap">Lives left</span>` | `<span class="fl-cap">City tiles</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` | `<span class="momentum-label">CITY TILES</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate) | `<span class="tiles-label">City tiles</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" | "Waiting for first light…" |
| `#clock-caption` "In the locker room" | "Dawn of the first day" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" | "Replay hash mismatch at turn N — showing recorded directives" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline" | "nightfalls / cities lost / winner on the timeline" |

The test greps the built `index.html` and `broadcast_core.js` for a forbidden-vocabulary list —
`Lives`, `LIVES`, `Clstr`, `flag`, `heart`, `paint`, `hopper`, `hill`, `POV`, `spray`, `grenade`,
`med kit`, `kill` — outside comment blocks, and asserts **zero** matches, plus each replacement present
exactly once.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), **`--topband`** (the scorebug strip) and
**`--hudscale`** on `:root`, unchanged. **No overlay sits in the transport band**: the board is laid
out between the two bands, and every lux-ai addition (the cycle bar, the research rail, the fuel strip,
the feed, the banners) is positioned inside the board region or in the top band. The **endcard stops at
`var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept) so the scrubber
stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `luxBeat(turn, kind, seat, label)` — named with the `lux` prefix so it
can never be shadowed by the chrome alias block's hoisted `var markBeat` (the tandem 2026-08-23
hoisting trap) — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind lux-ai emits and no others**: `.beat-marker.dusk`,
`.beat-marker.research`, `.beat-marker.citylost`, `.beat-marker.end`. The game block never calls
`chrome_common.js`'s `markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: 15 turns per second** (speed chips `[0.5, 1, 2, 4, 8]`, default 1). A `duel` replay is
48 lobby ticks + 360 turns + 72 `gameOverTicks` = 480 ticks ⇒ **32 s of playback**; `skirmish` is 21 s.
Both comfortably outlast `viewer_smoke.mjs --soak 10`, which needs to observe real advancement rather
than a legitimately-finished replay (the ecos 2026-08-23 scar). Fifteen turns a second is also the
tempo at which a human can actually read a Lux board: a worker step is visible, a nightfall is an
event.

### Readouts

1. **The island**, drawn edge to edge: the baked floor with its chalk grid; wood as green canopy chips
   whose size shrinks with the remaining amount, coal as dark faceted chips, uranium as pale chips with
   a glow ring; roads as lighter paving that thickens with level; city tiles as team-coloured buildings
   with a roof glyph and a **fuel ring** around the rim (fill = `min(1, fuel / (10 * upkeep))`, so a
   city that cannot survive tonight has a visibly empty ring); units as the baked chips with a 3-pip
   cargo strip. A depleted resource tile fades to bare ground and stays visible as a stump, so a
   spectator can see a side that mined itself out.
2. **Day and night** (the idea's central loop) — `#lightpool` washes the whole board to 55 % blue over
   the two turns either side of dusk and back at dawn; city tiles cast a warm glow; and a **cycle bar**
   in the top band shows the nine cycles as nine segments, each 30 light + 10 dark, with the playhead
   on it. Nightfall banners in `#bannerlane`: `NIGHT 5 FALLS — RED 967 fuel / 7 tiles · BLUE 1402 / 6`.
3. **Scorebug** — two plates, `#plates-l` (red) and `#plates-r` (blue), each with the seat's **real
   policy name** (spectator side only), its in-game alias, its colour chip, **city tiles as the big
   numeral**, and beneath it `units · fuel · research`. A `↯` glyph lights on any seat that has taken a
   fallback.
4. **Research rail** — a labelled strip in the top band: two bars, 0→200, with the coal (50) and
   uranium (200) thresholds ticked; a bar that crosses a threshold flashes and fires a `research` beat.
   This is the fuel ladder made visible, and it is the single best predictor of the second half.
5. **Fuel strip** — one row per city (largest first, capped at 4 per side plus a `+N` chip), each a
   labelled bar reading `C0 906 / 950 tonight`, red when `fuel < upkeep * nightTurnsLeft`. During the
   day it reads how many nights of fuel the city holds.
6. **Clock** — `#clock-time` shows `TURN 214 / 360 · NIGHT 4/10`; `#clock-caption` shows
   `cycle 5 of 9 · directive 21/36 · RED 7 – 6 BLUE`.
7. **Match feed** (`#killfeed`) — plain language, never internal notation: `RED builds a city tile at
   (6,9) — 7 tiles`, `BLUE unlocks COAL (50 research)`, `RED's worker dies in the open at (13,4)`,
   **`BLUE LOSES THE CITY AT (2,12) — 2 tiles, out of fuel`**, `the wood at (5,2) runs out`, and the
   commander lines `RED-alpha: "coal belt at column 3 before they research"`. The directive `note`
   appears here and nowhere else; this is where a spectator sees the LLM playing.
8. **City-tile lead graph** — the starter's `#momentum` SVG retargeted to two cumulative series (city
   tiles per seat, in team colours) with the nine night spans shaded and the playhead marked. Filled
   from the load-time pre-scan, so it draws at full width on the first frame. A blue line that falls
   off a cliff inside a shaded band is the whole story of a lost city in one glance.
9. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
   40 consecutive turns with no `citybuilt`, `citylost`, `research` or `dusk` event, from the pre-scan),
   spoilers switch, tick readout, speed chips, the scrubber with its four beat kinds, and `#mmwarn` on
   a hash mismatch — all the starter's, verbatim.
10. **Endcard** — `LUX — daveey 9 CITY TILES TO 6`, the two-seat table under the re-mapped header
    (`Side | City tiles | Units | Fuel | Research`), a second row of `built / lost / mined
    (wood-coal-uranium)`, and the story line `RED never researched uranium and won anyway — BLUE lost
    two cities in night 6`. It stops at `var(--band)` and any seek dismisses it.

### Art

**Real art, from the starter's shipped assets — no placeholders, no solid-colour squares, no
downloads.** The floor is `data/arena_floor.png`, tiled and darkened 18 % with a chalk grid, baked once
at reset by pixie (the path the starter uses for endzone paint). Resource chips and city buildings are
baked from `client/art/walls/wall_h.jpg` and `wall_v.jpg` tinted through `data/pallete.png`, at three
sizes (10, 14, 20 px) with a 1 px rim; the uranium glow and the city fuel ring are procedural in the
same palette. Units are baked at load by `rig_art.nim`'s compositor from `data/soldier_red.png` and
`data/soldier_blue.png` into the 24 chips of §Sim module edit 3. Numerals and labels use
`data/font.ttf`. The loading screen is the starter's locker room (`client/art/lockerroom/bg.jpg` plus
the red and blue cog webps) with the caption re-labelled "Waiting for first light…".

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim. The board is square and letterboxed to its native aspect, so the binding dimension in a
360 × 203 embed is the **height**: 16 × 16 renders at **12 px per cell** (192 × 192), 12 × 12 at
**16 px per cell** (192 × 192). At 12 px a city tile is a 12 px team-coloured building with a 2 px fuel
ring, a unit is a 10 px chip with a 3-pip cargo strip, and a resource tile is a 10 px chip — all
legible, and the whole island is in frame, which is why `#viewpanel` is dropped. Four rules are added
and asserted by `tests/test_lux_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `colour chip + name + city tiles`; `units · fuel · research`
   moves to a single line under the clock and the fallback glyph goes inline.
3. Under `.tiny`, the fuel strip collapses to one bar per **side** (the total across that side's
   cities) and the research rail to two 40 px bars with the threshold ticks only.
4. Under `.tiny`, the cycle bar keeps nine segments but drops the per-cycle numerals; the current
   cycle is marked by the playhead alone.

All four are sized from `--hudscale`, so nothing is ever drawn outside the canvas and
`--strict-text-bounds` stays on in CI.

---

## Packaging

- **Repo**: `Metta-AI/cogame-lux-ai`, **public at creation** (public is a certification prerequisite —
  `source-resolves` 404s on private). Slug `lux-ai`; **`game.name` is `lux-ai`** (hyphenated, matching
  the slug) so the secret namespace `secret://coworld/lux-ai/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, underscored, because the manifest image placeholder is derived
  from the compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two
  services / two images; this fork uses the one-image / two-entrypoints shape because the shared
  `docker_smoke.sh` and `policies.json` assume a single image:

  ```yaml
  services:
    lux_ai:
      image: coworld-lux-ai:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{LUX_AI_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:lux-ai src/lux_ai.nim` →
  `/bin/lux-ai`, and the same for `src/lux_ai_player.nim` → `/bin/lux-ai-player`. The runtime stage
  copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/lux-ai"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (`emscripten/emsdk` pinned, nimby 0.1.27
  pinned by its sha256, `nimby use 2.2.4`, `nimby --global sync nimby.lock`, the marker splices, the
  whole `test -f` / `grep -q` assertion block) with the asset list swapped to
  `data/{arena_floor,ascii,pallete}.png`, `data/soldier_{red,blue}*.png`, `data/font.ttf`,
  `data/atlas/*`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,red_*,blue_*}`,
  `lux_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`, `league.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  validated offline with the installed CLI's `validate_upload_manifest` before the first dispatch (the
  hive 0.1.0 scar), with these decisions:
  - `$schema` present; top-level `tags: ["lux", "rts", "economy", "zero-sum", "grid", "port"]` (≥ 3;
    **`game.tags` must not exist** — pistonball 0.1.0); top-level **`episode_timeout_minutes: 20`**,
    not under `game`; top-level `player[]`; **no** top-level `replay_viewer`, **no** top-level
    `version`, **no** `game.display_name`.
  - `game.name` `lux-ai`; `game.owner` `daveey@softmax.com`; `game.description` present (required);
    `game.runnable = {"type":"game","image":"{{LUX_AI_IMAGE}}","run":["/bin/lux-ai"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/lux-ai/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-lux-ai/tree/main"}` — the `env` entry is
    mandatory: without it the hosted game container never sees the coworld secret and every league
    episode silently plays scripted (hive, 2026-08-23).
  - `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`**, not top level.
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens","players"]`, **every array property carrying `minItems`/`maxItems`** (the
    tandem 0.1.0 scar): `tokens` 2/2, `players` 2/2, `slots` 0/2. `tokens` is described as
    runner-injected and **no `game_config` anywhere in this manifest contains a literal `tokens`
    array** (matriculate rejects "game_config must not include runner-managed tokens" —
    knights-archers 0.1.0), while `config_schema` keeps *requiring* it. Scalar properties, with
    defaults: **`num_agents`** (integer, `minimum: 2`, `maximum: 2`, default 2), `minPlayers` (2),
    `teams` (2), `cogsPerTeam` (1), `seed` (1734029581), `mapSize` (enum `[12, 16]`, default 16),
    `woodClusters` (4), `coalClusters` (2), `uraniumClusters` (1), `woodStart` (300), `coalStart`
    (400), `uraniumStart` (325), `maxTurns` (360), `cycleLength` (40), `dayLength` (30),
    `directiveEvery` (10), `cityCost` (100), `workerCargo` (100), `cartCargo` (2000),
    `woodRate` (20), `coalRate` (5), `uraniumRate` (2), `coalResearch` (50), `uraniumResearch` (200),
    `cityUpkeepPerTile` (23), `cityAdjacencyDiscount` (5), `workerUpkeep` (4), `cartUpkeep` (10),
    `workerCooldown` (20), `cartCooldown` (30), `cityCooldown` (100), `maxRoad` (6),
    `attempt1Ms` (7000), `retryMs` (3000), `turnBudgetMs` (11000), `turnSpacingMs` (6000),
    `wallClockBudgetSeconds` (660), `lobbyJoinTimeoutTicks` (2400), `startWaitTicks` (48),
    `gameOverTicks` (72), `fastMode` (true), `showPlayerLabels` (false), `fullyObservable` (true),
    `model` (""), `maxOutputTokens` (900).
  - `game.results_schema` — closed (`additionalProperties: false`), exactly the 27 keys of §Server,
    `required: ["names","scores","win","reason","endRule","cityTiles","turnsPlayed"]`; every
    seat-indexed array `minItems: 2, maxItems: 2`; `resourcesMined` items `minItems: 3, maxItems: 3`;
    `reason` enum `["complete","deadline","fault"]`; `endRule` enum
    `["full_time","eliminated","wall_clock","sim_fault","host_error"]`; `winner`
    `{"type":["integer","null"],"minimum":0,"maximum":1}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"text","value":"<docs/PROTOCOL.md section inlined>"}` — objects, never bare strings (the
    garble v0.1.0 scar). `player` documents the seat websocket, the registration blob, the Sprite v1
    frame a seat receives and the fact that a seat sends no inputs; `global` documents the spectator
    frame — the exact state JSON of §Server, the eleven event kinds, the four beat kinds and the record
    vocabulary.
  - **`game.docs`** = **`readme`** `{"type":"text","value":"<README body inlined>"}` and **`pages`** =
    three entries, each `{"id","title","content":{"type":"text","value":…}}`: `rules.md` / "Rules"
    (`docs/RULES.md`), `protocol.md` / "Wire protocol" (`docs/PROTOCOL.md`), `commanding.md` /
    "Writing a Lux directive prompt" (`docs/COMMANDING.md`). **Text form, not URIs.**
    `tests/test_lux_manifest.nim` asserts all four values are non-empty.
  - Top-level `player[]` — **two** entries, `forester` and `prospector`, each with
    `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "200m", memory: "128Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Both are seated in the certification fixture, because
    **every declared player entry must occupy a certification slot** (the raid 0.1.2 `players_missing`
    scar).

  **Variants — `num_agents: 2` inside each `game_config`, NEVER at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0). Three, differing in board and clock only:

  ```json
  "variants": [
    {"id": "duel", "name": "Lux duel (16x16, 360 turns)",
     "description": "Lux AI Season 1 on a seeded, mirror-symmetric 16x16 island: nine day/night cycles, wood-coal-uranium, research gates at 50 and 200, most city tiles standing at turn 360 wins.",
     "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}],
                     "num_agents": 2, "minPlayers": 2, "teams": 2, "cogsPerTeam": 1,
                     "mapSize": 16, "woodClusters": 4, "coalClusters": 2, "uraniumClusters": 1,
                     "woodStart": 300, "coalStart": 400, "uraniumStart": 325,
                     "maxTurns": 360, "cycleLength": 40, "dayLength": 30, "directiveEvery": 10,
                     "attempt1Ms": 7000, "retryMs": 3000, "turnBudgetMs": 11000,
                     "turnSpacingMs": 6000, "wallClockBudgetSeconds": 660,
                     "lobbyJoinTimeoutTicks": 2400, "startWaitTicks": 48, "gameOverTicks": 72,
                     "fastMode": true, "showPlayerLabels": false, "fullyObservable": true,
                     "seed": 1734029581}},
    {"id": "skirmish", "name": "Skirmish (12x12, 200 turns)",
     "description": "A tighter island and five cycles instead of nine: less room to expand, and every research point costs a worker you badly need.",
     "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}],
                     "num_agents": 2, "minPlayers": 2, "teams": 2, "cogsPerTeam": 1,
                     "mapSize": 12, "woodClusters": 3, "coalClusters": 1, "uraniumClusters": 1,
                     "woodStart": 300, "coalStart": 400, "uraniumStart": 325,
                     "maxTurns": 200, "cycleLength": 40, "dayLength": 30, "directiveEvery": 10,
                     "attempt1Ms": 7000, "retryMs": 3000, "turnBudgetMs": 11000,
                     "turnSpacingMs": 6000, "wallClockBudgetSeconds": 660,
                     "lobbyJoinTimeoutTicks": 2400, "startWaitTicks": 48, "gameOverTicks": 72,
                     "fastMode": true, "showPlayerLabels": false, "fullyObservable": true,
                     "seed": 1734029581}},
    {"id": "scarcity", "name": "Scarcity (16x16, thin wood, rich rock)",
     "description": "Half the wood, more coal and twice the uranium: the wood runs out around turn 200, so a side that never bought the research ladder loses its cities in the sixth night.",
     "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}],
                     "num_agents": 2, "minPlayers": 2, "teams": 2, "cogsPerTeam": 1,
                     "mapSize": 16, "woodClusters": 2, "coalClusters": 3, "uraniumClusters": 2,
                     "woodStart": 200, "coalStart": 400, "uraniumStart": 325,
                     "maxTurns": 360, "cycleLength": 40, "dayLength": 30, "directiveEvery": 10,
                     "attempt1Ms": 7000, "retryMs": 3000, "turnBudgetMs": 11000,
                     "turnSpacingMs": 6000, "wallClockBudgetSeconds": 660,
                     "lobbyJoinTimeoutTicks": 2400, "startWaitTicks": 48, "gameOverTicks": 72,
                     "fastMode": true, "showPlayerLabels": false, "fullyObservable": true,
                     "seed": 1734029581}}
  ]
  ```

  **`num_agents` is 2 in all three variants' `game_config` and in the certification fixture.** `duel`
  is what the league ranks.

  **Certification fixture** — `num_agents: 2` again, inside `certification.game_config`, exactly two
  players, and **both declared players seated**, so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS ==
  2` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks):

  ```json
  "certification": {
    "players": [{"player_id": "forester"}, {"player_id": "prospector"}],
    "game_config": {"players": [{"name": "Red"}, {"name": "Blue"}],
                    "num_agents": 2, "minPlayers": 2, "teams": 2, "cogsPerTeam": 1,
                    "mapSize": 16, "woodClusters": 4, "coalClusters": 2, "uraniumClusters": 1,
                    "woodStart": 300, "coalStart": 400, "uraniumStart": 325,
                    "maxTurns": 360, "cycleLength": 40, "dayLength": 30, "directiveEvery": 10,
                    "turnSpacingMs": 0, "wallClockBudgetSeconds": 240,
                    "lobbyJoinTimeoutTicks": 600, "startWaitTicks": 48, "gameOverTicks": 72,
                    "fastMode": true, "showPlayerLabels": false, "fullyObservable": true,
                    "seed": 42}
  }
  ```

  Both seats scripted, no LLM, no rate floor: 360 turns of integer play is ~2 s of wall clock, while
  the replay is 480 ticks ⇒ **32 s of playback**, deliberately longer than any viewer soak window (the
  ecos 2026-08-23 scar), and it crosses at least one research threshold and at least one nightfall, so
  the fixture's replay exercises every beat kind and every readout. The `certify` step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 s does not cover start +
  connect grace + play + linger — cooperative-hunting 0.1.2).
- **`tools/ci/policies.json`** — four policies, one image, all `"run": "/bin/lux-ai-player"`:

  ```json
  [{"name":"lux-ai-lumberjack","run":"/bin/lux-ai-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text in §Decisions>"}},
   {"name":"lux-ai-nightwatch","run":"/bin/lux-ai-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text in §Decisions>"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"lux-ai-forester","run":"/bin/lux-ai-player",
    "env":{"PLAYER_SCRIPTED":"forester"}},
   {"name":"lux-ai-prospector","run":"/bin/lux-ai-player",
    "env":{"PLAYER_SCRIPTED":"prospector"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `lux-ai-forester` and
  `lux-ai-prospector`, and their versions must differ from the champions' or the platform renames a
  champion "Baseline (N)". No `USE_BEDROCK` flag: the LLM call is made by the **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml` with `<slug>` →
  `lux-ai`, `<IMAGE>` → `coworld-lux-ai`, `<SEATS>` → **`2`**, plus `SMOKE_REQUIRE_REPLAY_JSON: "0"`
  on the `docker-smoke` step (binary replay format), `--soak 10` on the `viewer_smoke.mjs`
  invocation, and a final `wasm-viewer` step running
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` as the
  native ↔ wasm hash gate. `coworld-release.yml` and `coworld-submit.yml` are the templates, with
  `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh`,
  `tools/build_replay_viewer.sh` and `tools/ci/check_gameversion.sh` are committed **executable**
  (mode 100755) and CI asserts the bit. `tools/ci/viewer_smoke.mjs` is copied **verbatim** from
  `coworld-builder/templates/tools/ci/`, no substitutions.
- **Repo layout**: `src/lux_ai.nim`, `src/lux_ai_player.nim`,
  `src/lux/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, board.nim, units.nim, cities.nim,
  resolve.nim, scoring.nim, micro.nim, directives.nim, baselines.nim, llm.nim, decide.nim, roster.nim,
  replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, rig_art.nim,
  wire_constants.nim, server.nim}`,
  `replay-viewer/{lux_replay.nim, config.nims, static_replay.js, static_replay_worker.js}`, `client/`,
  `data/`, `tests/`, `tools/{build_replay_viewer.sh, gen_wire_constants.nim, expand_replay.nim,
  extract_events.nim, replay_summary.py, record_fixture.sh, tune_baselines.nim, wasm_replay_smoke.cjs,
  ci/}`, `docs/{RULES.md, PROTOCOL.md, COMMANDING.md, plans/2026-08-27-lux-ai-design.md}`, `AGENTS.md`,
  `README.md`, `config.json`, `nimby.lock`, `lux_ai.nimble`, `compose.yaml`,
  `coworld_manifest_template.json`, `Dockerfile`, `Dockerfile.replay-viewer`.

---

## Tests

Nim, in the starter's layout: `tests/test_lux_*.nim`, imported by four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** and as four shard
binaries in `ci.yml`'s `test` job, **in both debug and release** (debug enables Nim's range/overflow
checks — the cheapest catch for an index or accumulator overflow). `tests/config.nims`
(`--path:"../src"`) is the starter's, unchanged. The sandbox can run none of this: `ci.yml` is the
only harness.

**Sim unit tests**

1. **`tests/test_lux_board.nim`** — the seeded generator: the map is **exactly mirror-symmetric** in
   terrain kind and amount at reset, for 10 000 seeds and both map sizes; cluster counts and cell
   counts match the table in §The game; the rejection sampler terminates for every one of those seeds;
   both start cells are `empty`, mirror each other, and carry one city tile and one worker; the map is
   a pure function of `(seed, mapSize, cluster config)` and is **identical after different play** (the
   anti-collusion pin); and `mapRng` is consumed by nothing but the generator (a call-count assertion).
2. **`tests/test_lux_resolve.nim`** — the ordered rules, one case per numbered step:
   - `research gates`: a worker adjacent to coal collects 0 at 49 research points and 5 at 50; the same
     for uranium at 199 / 200.
   - `collection split`: three workers around one wood tile with 40 left take 14/13/13 by ascending
     unit id; a worker with 95/100 cargo takes 5 and the tile loses 5; a cart adjacent to wood takes 0.
   - `collection order`: a worker adjacent to wood, coal and uranium with 100 free space fills from
     wood first, then coal, then uranium, and never exceeds its cap.
   - `deposit`: a worker on a friendly city tile empties into the city at fuel value 1/10/40 every
     turn, day and night; a worker on an **enemy** city tile is impossible (the move is illegal).
   - `build city`: refused on a resource tile, on an occupied city tile, and at 99 cargo; accepted at
     exactly 100; spends wood before coal before uranium; two opposing workers building the same cell
     both fail and neither spends; two friendly workers → the lower id builds.
   - `merge`: a tile placed between two of the side's cities merges them into the lowest id with the
     fuels summed and the tile counts added.
   - `movement`: off-map and enemy-city-tile targets are discarded at no cooldown; a stationary unit
     blocks; a column of three behind a mover all advance; two units targeting the same empty cell both
     stay; two adjacent units swapping both move; any number of friendly units stack on a friendly city
     tile; the fixed point terminates within `unitCount` iterations and is order-independent (asserted
     by shuffling the evaluation order and comparing outcomes).
   - `night`: a 6-tile line city pays `23*6 - 5*5 = 113`; a 3×3 blob of 9 pays `23*9 - 5*12 = 147`; a
     city one fuel short is **destroyed entirely**, all nine tiles at once; a worker outside with 3 wood
     dies, with 4 wood lives, with 1 coal lives and loses the whole coal; a worker inside a surviving
     city pays nothing; a worker inside a city destroyed this turn pays its own upkeep.
   - `cooldown and roads`: a worker acting on road 0 acts every second turn and on road 6 every turn; a
     cart raises road by 1 per move to a cap of 6 and never on a resource tile; a city tile acts once
     per 10 turns.
   - `unit cap`: a city tile refuses to build when `units == cityTiles` and accepts on the turn a tile
     is added.
   - `wood regrowth`: 300 → 306 → 312…; a tile at exactly 0 stays 0 forever; nothing exceeds 500.
3. **`tests/test_lux_scoring.nim`** — the ladder and its sign: `scores[0] + scores[1] == 1.0` on 5 000
   randomised end states; the ladder resolves in order city tiles → units → fuel → tie; `win[s]` is
   exactly `scores[s] == 1.0`; `winner` is null exactly on a tie; no score is ever negative; a
   `deadline` episode is scored by the same ladder at the stop turn and is never zeroed.
4. **`tests/test_lux_endings.nim`** — `full_time` at exactly `maxTurns` and not the turn before or
   after; `eliminated` fires the turn a side reaches zero tiles and zero units, and not before;
   `wall_clock` at the 660 s stop with a rankable result and a complete replay up to that turn;
   `sim_fault` on a forced invariant trip with a partial replay; `results.reason` and `results.endRule`
   are always members of their declared enums and nothing else is ever emitted.
5. **`tests/test_lux_determinism.nim`** — no floating point in
   `src/lux/{sim,board,units,cities,resolve,scoring,micro,baselines}.nim` (a source grep); two runs
   from the same seed and the same directives produce byte-identical state streams and two different
   seeds do not; `city.fuel` stays in `int64` range under a 360-turn uranium economy.
6. **`tests/test_lux_perf.nim`** (release-only, listed in `NIM_TESTS_RELEASE_ONLY`) — a full 360-turn
   two-sided episode with both micros completes in under 60 s.

**Bounded orders / legality on the scripted baselines** — `tests/test_lux_baselines.nim` and
`tests/test_lux_micro.nim`

7. **`baselines are bounded`** — for 300 pseudo-random world states (varying research, city counts,
   fuel, resource depletion, day and night, both map sizes, both seats) × **both** `forester` and
   `prospector`: the emitted directive validates against the reply schema of §Decisions — `stance` in
   the enum, `mine` a permutation of the three kinds, `research` and `build` and `night` in their
   enums, `workers` in 0..40, `carts` in 0..10, `focus` null or inside the board, `note` empty — and the
   serialised directive is ≤ 512 bytes. A baseline that ever proposes an out-of-domain field fails the
   build.
8. **`the micro never emits an illegal action`** — over the same states, for both baselines and for 200
   randomly-generated *valid* directives: every emitted action is in
   `{center, move(n|e|s|w), transfer, build_city}` for units and `{research, build_worker, build_cart}`
   for city tiles; no action is ever emitted for a unit or tile with `cooldownTenths > 0`; no unit or
   tile receives two actions in a turn; no move targets an off-board cell or an opponent city tile; no
   `build_city` is emitted on a resource tile, an occupied cell, or under 100 cargo; `pillage` is never
   emitted; and no unit is ever left with no decision (every unit gets an action or an explicit
   `center`).
9. **`fallback is the forester proc`** — the decision engine's fallback path and the `forester`
   baseline resolve to the same proc, so they cannot drift.
10. **`the micro is a pure function`** — the same `(state, directive, seat)` triple yields the identical
    action list on every call and in both the native and the wasm build.
11. **`forester beats prospector`** — a scripted-vs-scripted `duel` episode at seed 1734029581 completes
    `complete`/`full_time` with `forester` ahead on city tiles, and both sides survive at least six
    nights (so the fixture is a real game, not two dead islands).
12. **`baseline tuning is the swept pick`** — `forester`'s `workers = 8`, its `11 * upkeep` fuel
    threshold and `prospector`'s `workers = 5 / 10` equal `tools/ci/baseline_tuning.json`, the pick from
    `tools/tune_baselines.nim`'s head-to-head sweep (the starter's `test_tuning` pattern; `ci.yml`
    re-runs the sweep with `--check`).

**Directives, observation and privacy**

13. **`tests/test_lux_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
    numeric strings, an unknown `stance`, a hyphenated enum, `mine` with duplicates and with one entry,
    `mine` empty, `workers: 999` and `workers: -3` (clamped), `focus` off the board (clamped),
    `focus` as `{"x":…,"y":…}`, a 300-character `note`, a reply with only a `note` (usable), a
    non-object reply (a parse failure), a 9 KB reply (capped at 4096 then parsed), **and a `note`
    whose 160th and 161st characters are a 4-byte emoji** — truncation must land on the **rune**
    boundary and the result must still round-trip `%$` → `parseJson` and decode as strict UTF-8. Two
    consecutive failures ⇒ the `forester` directive plus a `fallback` record; a timeout on attempt 1 ⇒
    exactly one retry; a `throttled` attempt 1 with no other candidate model ⇒ **no** retry and a
    `throttled` fallback.
14. **`tests/test_lux_observation.nim`** — the observation contract: the three ASCII layers are exactly
    `mapSize` lines of exactly `mapSize` characters drawn only from their declared legends; a seat's
    view of the opponent's public state is **byte-identical to the opponent's own** (full
    observability, asserted from both sides); `city_list` is capped at 8 with `cities_omitted` correct,
    `cells` at 12, `richest` at 6; `how_it_went` is ≤ 240 runes; and the seed, the `mapRng` state, the
    other seat's directive (this turn's **or any past turn's**), the other seat's `note`, and any real
    policy name appear **nowhere** in any seat-facing byte.
15. **`tests/test_lux_identity_privacy.nim`** — the starter's test, kept and extended: no seat frame, no
    LLM system-or-user message and no `directive` record's `view` ever contains a sentinel policy
    address — while the broadcast stream, `roster[].name`, the DOM scorebug and `results.names` **must**
    contain it. That is the two-name-space pin, asserted from both sides.

**Engine and end-to-end**

16. **`tests/test_lux_engine.nim`** — the directive loop against a fake LLM client: **both** seats' calls
    go out in **one parallel batch** (the fake records in-flight windows and the test asserts they
    intersect); the per-turn budget is enforced with a hung client; `sim_config.validate` rejects
    `attempt1Ms`/`retryMs` that are not whole seconds and rejects `attempt1Ms + retryMs > turnBudgetMs`;
    `turnSpacingMs` holds the batch rate at ≤ 30 req/min for two seats and the rolling counter caps a
    double-retry turn at 28; the budget guard switches to scripted and the episode still ends
    `complete`; a disconnected seat plays `forester` and revives on reconnect; a never-connecting seat is
    reported **once** to `COGAME_PLAYER_FAILURE_URI` with exactly the closed
    `{"message","failed_policy_index"}` payload and all 360 turns still play; and no unit is ever
    unactuated on any turn after turn 0.
17. **`tests/test_lux_replay.nim`** — **an end-to-end episode writing a replay**: a full two-seat,
    360-turn scripted episode against a temp-dir `COGAME_*` URI set writes `results.json` and a
    `COWLDLUX` replay; `parseReplayBytes` accepts it; **re-simulating from the config + the directive
    input records alone reproduces every recorded `gameHash`**, for all three end reasons — `full_time`,
    `wall_clock` **including the stop turn** (the particle-worlds r2 scar) and `sim_fault`; the bytes
    alone yield seat names, aliases, policy kinds, the full config, the seed, every directive and the
    result; the results key set equals the manifest's `results_schema` key set exactly; every
    `directive` record is within its caps; and the stream contains ≥ 1 `citybuilt`, ≥ 1 `dusk`, ≥ 1
    `research`, ≥ 1 `unitbuilt` and exactly one `result` record.
18. **`strict-UTF-8 replay parse`** (in the same file) — `tools/replay_summary.py` is run over a replay
    whose every capped field is filled to **exactly** its cap with 4-byte emoji and whose policy labels
    are non-ASCII; its stdout must parse under `json.loads(out.decode("utf-8"))` with **strict** UTF-8,
    contain no lone surrogates, and report `protocol == "lux-ai/v1"`. The embedded config JSON must
    decode strictly too.
19. **`every committed fixture carries the current GameVersion`** — the starter's sweep over `tests/`,
    kept, with `tools/ci/check_gameversion.sh`.

**Manifest**

20. **`tests/test_lux_manifest.nim`** — `num_agents == 2` in **all three** variants' `game_config`
    **and** in `certification.game_config`; `num_agents` **absent at every variant top level**; no
    literal `tokens` array in any `game_config`; `len(player) == 2` and **both** declared players seated
    in `certification.players`; `len(certification.players) ==
    len(certification.game_config.players) == 2`; every array in `config_schema` declares
    `minItems`/`maxItems`; `episode_timeout_minutes` at the top level and equal to 20; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme`
    and all three `pages` non-empty **text**; `game.description` present and `game.tags` **absent**;
    ≥ 3 top-level tags; `game.replay_viewer.bundle == "static-replay-viewer"` under `game`;
    `player[].resources.limits.cpu >= "1"`; every variant's `wallClockBudgetSeconds <= 660`
    (≤ 60 % of 1200); `game.name` equals the secret namespace in
    `game.runnable.env.ANTHROPIC_API_KEY_URI`; `results_schema` keys == `luxResultsJson` keys in both
    directions; `config_schema` covers every field `sim_config.update` reads and no field it does not;
    the compose service name derives `{{LUX_AI_IMAGE}}` and the image is `coworld-lux-ai`; and **every
    variant's `game_config` actually constructs a valid `GameConfig` and generates the board and
    cluster counts this note claims** (the collab-cooking 0.1.1 scar: test every variant, not just the
    fixture).
21. **`manifest loads under the installed CLI`** — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest`.

**Viewer**

22. **`tests/test_lux_viewer.nim`** (static assertions in the `test` job) — `chrome_common.js` is
    **byte-identical** to the starter's (sha256 pinned as a literal) and contains no lux edit;
    `replay_broadcast.html` begins with the starter's bytes up to the documented splice marker and only
    appends after it; `broadcast_core.js`'s kept procs are byte-identical to the starter's, `pushFeed`'s
    signature included; no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap) and the beat builder is `luxBeat`, never
    `markBeat`; the set of `.beat-marker.<kind>` CSS rules equals **exactly** `{dusk, research,
    citylost, end}`; `#endcard { bottom: var(--band` is present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the
    transport band; the four 360 px rules exist; `#viewpanel`, `#minimap`, `#zoombar`, `#fpv*` and
    `#povBadge` appear nowhere; and no `ctf_`/`CTF_`/`PB_` identifier survives in `client/`,
    `replay-viewer/` or `src/` **except** the two documented `CTF_WIRE` alias lines.
23. **`tests/test_lux_endcard_labels.nim`** — the forbidden-vocabulary grep of §Viewer, zero matches,
    and each re-mapped string present exactly once.
24. **`tests/test_lux_label_contract.nim`** — the starter's `test_label_contract` pattern: the emitted
    sprite-label vocabulary equals `tests/label_manifest.txt`, regenerated in the same commit as any
    label change.

**Viewer smoke — the bundle is EXECUTED, not merely built**

25. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`, no substitutions) is run by **`ci.yml`'s
    `wasm-viewer` job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned
    1.55.0 in both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. The job fails unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives inside the timeout, the clock and tick readouts **advance** across
    the soak, and `canvas_text.never_inside == 0`. `--strict-text-bounds` stays on: the board is fixed
    and fits the frame, so any text drawn outside the canvas is a bug. The job also asserts
    `tools/build_replay_viewer.sh` is present and **executable** and that `index.html` and a non-empty
    `.wasm` exist before running.
26. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module, kept: `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300`
    fails if `lux_mismatch_tick() != -1`. wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.
27. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `note` at all**, so
    the smoke replay can never exercise the feed's commander-line path (the cogchemists 2026-08-24
    scar). The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and
    shims only the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26
    scar) — driving the real page with a full-cap 160-rune `note` on both seats, a full fuel strip, a
    research rail crossing 200, a deep-night frame and a `citylost` banner, at 360 / 620 / 1280 px.

**Docker smoke**

28. **`tools/ci/docker_smoke.sh`** — a raw-Docker episode from the certification fixture in the
    production image, seats cross-checked against **`SMOKE_SEATS=2`**, `SMOKE_REQUIRE_REPLAY_JSON=0`,
    asserting the game container exits 0 with `results.json` and a replay, that `results.reason` is not
    `fault`, and that **every player container exited 0** (the raid 0.1.3 scar). Its replay is uploaded
    as the `smoke-replay` artifact and is the input to the `wasm-viewer` job.

---

## Out of scope (v1)

- **Lux Season 2 in its entirety**: factories, heavy and light robots, ice and ore, water and metal
  refining, lichen growth as the score, robot power, the bidding phase for factory placement, and the
  early-phase factory-placement turn structure. S2 is a different game with a different scoring
  substance, not a parameter of S1.
- **Lux Season 3 in its entirety**: fog of war, relic nodes, energy fields, the match-of-games
  structure. In particular **fog of war is out**: this port is fully observable (§Decisions), and the
  observation, the viewer and the privacy tests all assume it. Partial observability would change the
  observation schema, the micro's planning and half the tests at once.
- **1000-turn episodes.** S3's length against a 720 s budget is arithmetic that does not close even
  with a sparse directive cadence. 360 turns is S1's own number and is what §Decisions is sized for.
- **Per-turn LLM control of individual units.** The idea's "one orders-bundle per turn" is honoured at
  the strategic layer; the unit layer is the deterministic micro. A per-unit protocol is a v0.2
  addition — the action stream already exists and is already re-derived by the viewer — but it does not
  fit 360 turns inside 720 s and it is not shipped.
- **Pillage.** S1's road-destroying worker action is in the rule set of the real game and is **not
  implemented here**: nothing in the v1 micro would ever issue it, and an unreachable rule is a test
  surface and a config knob with no gameplay. Roads themselves stay (carts build them, they halve
  cooldowns), and they are permanent.
- **Bit-exactness with `Lux-Design-S1`.** This is an adaptation of a public specification, not a
  reproduction of the JavaScript engine. The documented divergences are: a **new seeded mirror-symmetric
  map generator** (S1's procedural generator is not transcribed); **integer wood regrowth**
  (`+max(1, amount div 50)` in place of ×1.02); **cooldown in tenths** with recovery `10 + 2×road` in
  place of S1's fractional road formula; **map sizes restricted to 12 and 16** (S1 also rolls 24 and
  32); and **no pillage**. Each divergence is listed with its S1 counterpart in `docs/RULES.md`. No test
  compares a trajectory to a reference implementation, and none should.
- **24 × 24 and 32 × 32 maps.** Letterboxed into a ~360 × 203 embed they fall to 8 px and 6 px per cell,
  where a unit chip, a cargo pip and a city fuel ring stop reading. `board.nim` generates them and
  `tests/test_lux_board.nim` covers them; shipping one is a new variant plus a legibility pass, not a
  rules change.
- **Seat counts other than 2.** The idea pins 2, the game is a zero-sum duel, and `num_agents` is 2 in
  every variant and in the cert fixture. S1's rarely-used 4-player mode is not shipped.
- **Any inter-seat channel** — chat, radio, `say`, emotes. Lux S1 has none, and in a two-seat zero-sum
  game a text channel is a collusion surface. `note` stays spectator-only.
- **An embedded third-party visualiser.** The idea proposed embedding the official Lux web visualiser;
  the coordinator overrode it. The replay is this repo's own static wasm bundle, so it works offline,
  it works from S3 alone, and it never depends on someone else's server staying up.
- **Learned RL-vector policies and the open-source Kaggle bot corpus.** Both champions are LLM prompt
  policies and both fillers are scripted; nothing here trains, and no third-party bot is vendored or
  run.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, fog rendering, the
  first-person PIP, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, respawns, kills, four-team play, achievements, campaign mode, multi-game
  episodes, the procedural map generator, the map pool, mapkit and the map editor — all deleted, not
  disabled (§Sim module), and none of them return in v1.
- **Live spectating.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is ever declared.
