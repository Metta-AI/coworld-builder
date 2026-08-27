# cogame-flatland — design note (2026-08-27)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` re-exporting the sim modules,
`sim_types.nim` owning `GameVersion`, `TargetFps = 24`, the flatty wire types and the rune caps
`MaxSayRunes` / `MaxNoteRunes` / `MaxPromptRunes = 4000`); the mummy HTTP/websocket server
implementing the Coworld contract; the `decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` /
`control.nim` commander layer with its one-parallel-batch-per-turn shape and its `attempt1Ms` /
`retryMs` / `turnBudgetMs` / `turnSpacingMs` deadlines, tolerant JSON extraction, rune truncation and
fallback ladder; the binary `COWLD…` replay of *inputs plus a per-tick `gameHash`*, re-simulated by
**the same sim module** compiled to wasm by `replay-viewer/config.nims`; the `client/` broadcast
chrome (`chrome_common.js` + `broadcast_core.js` + `replay_broadcast.html`, with the appended game
block spliced in through the `window.PaintballChrome.install(PB_CTX)` hook at
`client/replay_broadcast.html:4337`); nimby + `Dockerfile` + `Dockerfile.replay-viewer` +
`tools/build_replay_viewer.sh`; and the Nim test suite with its four shards
(`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **this is a real-time grid loop whose rules are written into this repo and
whose seats are LLM dispatchers over a deterministic per-tick driver — the first row of the starter
table** (`prompts/10-design.md` §Starter table: "any real-time game loop (grid OR continuous
physics), new rules written for this coworld"). It is deliberately **not** the `cogame-moba` row:
upstream `flatland-rl` is a Python/numpy environment whose rail generator, observation builders and
RNG consumption order are implementation-defined, so a bit-exact port is neither achievable nor
re-derivable in a wasm replay. What this repo reproduces is Flatland's **rules idiom** — the
transition-map grid, the five-action space, exclusive cells, speed classes as integer
ticks-per-cell, Poisson malfunctions, targets and on-time arrival — with every divergence named in
§Sim module → "Documented divergences from upstream". The sim is **Nim inside this fork**, compiled
twice: natively into the server binary and to wasm for the viewer. There is no Python sim and no
two-starter hybrid; that split is the documented recurring failure (LEARNINGS babel/lantern,
gridlock, magent round 1). The precedent for forking paintbot for a grid port is eight deep
(knights-archers, pistonball, atari-cabinet, walker-waterworld, particle-worlds,
smac-starcraft-micro, magent-battle, rware-warehouse).

Where this note departs from coworld-ctf it says so. The departures are: the rules are Flatland's,
not paintbot's (§Sim module lists what is deleted); the board is a small integer **grid** with a
static, file-authored rail topology, so ctf's pixel arena, procedural map generator, map pool, map
editor and mapkit are deleted; the game is **fully cooperative** (one shared on-time number, no
teams); a seat commands **six trains**, not one body; and `MaxSayRunes` / `MaxNoteRunes` are
re-pinned (§Decisions → reply schema).

### Source idea (verbatim)

> FLAT Flatland — hundreds of trains, one rail network, and every agent is its own dispatcher
>
> Port of Flatland (AIcrowd / SBB / Deutsche Bahn). A grid rail network with switches; each train has
> a start, a target station, a speed class, and can break down at random (malfunctions). Per tick
> each train chooses forward / left / right at a switch / stop. Reward: arrive on time; collisions
> and deadlocks are the failure. The real challenge is that the 'obvious' greedy path for each train
> jams the network — you need yielding conventions without a central scheduler.
>
> Seats: 10-200 trains (one cog per train, or one policy per fleet)
> Motive: fully cooperative (shared on-time score) with individual targets
> Policy interface: per-tick discrete; decisions only matter at switches, so an LLM can act on a
> switch-event cadence
> Fills gap: 08 Gridlock is competing road fleets; Flatland is *cooperative* rail with malfunctions
> and one-track sections — a deadlock game
> Integrity (anti-collusion): cooperative cross-play scoring; networks and malfunctions seeded.
>
> Replay plan (watchability): the Flatland renderer is already good — add a deadlock alarm and an
> on-time leaderboard.
>
> Source: github.com/flatland-association/flatland-rl; NeurIPS 2020 Flatland challenge.

### Upstream, consulted and pinned

The rules idiom reproduced here is `flatland-association/flatland-rl` (`flatland.envs.rail_env`).
The facts below were read from the published Flatland documentation while writing this note and are
the only upstream claims this note makes; each is transcribed into `src/flatland/upstream.nim` with
its citation comment beside it, and `tests/test_flatland_upstream.nim` asserts the shipped constants
still equal them.

| Upstream fact | Value used here | Source |
|---|---|---|
| Action space | `DO_NOTHING 0`, `MOVE_LEFT 1`, `MOVE_FORWARD 2`, `MOVE_RIGHT 3`, `STOP_MOVING 4` | flatland docs, "Observation and Action Spaces": 0 do nothing, 1 deviate left, 2 go forward, 3 deviate right |
| `DO_NOTHING` semantics | a moving train keeps moving, a stopped train stays stopped | same |
| `MOVE_LEFT` / `MOVE_RIGHT` semantics | takes the left/right transition **if one exists at this cell**, otherwise no effect; also restarts a stopped train if the transition allows | same |
| Orientation enum | `N 0, E 1, S 2, W 3` (North up, East right, South down, West left) | flatland specifications, "Railway Specifications" |
| Neighbourhood | 4-connected, grid does **not** wrap | same |
| Cell exclusivity | "each cell is exclusive and can only be occupied by one agent at any given time" | same |
| Dead end | moving forward in a dead-end cell turns the train 180° and steps back the way it came | `rail_env` module docs |
| Move order | "the actions of the agents are executed in order of their handle" | `rail_env` module docs |
| Malfunctions | a Poisson process parameterised by `malfunction_rate`, `min_duration`, `max_duration`; a malfunctioning train cannot act and **blocks the paths of others**; nothing can repair it early | flatland FAQ, "Flatland Environment"; flatland 2.0 tutorial |
| Speeds | fastest speed is 1, slower speeds lie in (0, 1); no more than 5 speed profiles | flatland 2.0 tutorial |
| Removal at target | `remove_agents_at_target = True` — an arrived train leaves the grid | `RailEnv` signature |
| Episode length | `max_time_steps = 4 * 2 * (width + height + 20)` | flatland FAQ, "Flatland Environment" |

Two derived numbers this note relies on, both asserted by a test rather than trusted from this
paragraph:

- **`maxTicks = 496`** for the shipped 28 × 14 board: `8 × (28 + 14 + 20) = 8 × 62 = 496`, upstream's
  own formula applied to this repo's grid. Both shipped variants use the same grid, so both use 496.
- **`turnTicks = 16` ⇒ 31 command turns**: turns fire at ticks `0, 16, 32, … 480`, i.e.
  `480 div 16 + 1 = 31`.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time grid loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-flatland` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=timetable\|yielder`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art + install-time bakes) |
| Two name spaces | §The game (aliases `Alpha`/`Beta`/`Gamma`/`Delta` in-game; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 408 s, worst 555 s, engine stop 660 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 4`, three times |
| Simultaneous decisions as one parallel batch | §Decisions (all four seats in one `curl.makeRequests` batch per turn) |
| Replay bytes self-sufficient | §Server (config JSON, joins, orders, chats, per-tick hashes, seed, network id) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Networks and malfunctions seeded and unsteerable (the idea's integrity note) | §Sim module (network chosen by `seed`; malfunctions are a pure hash of `(seed, trainId, tick)`) |

---

## The game

One rail network, 28 cells wide and 14 tall, drawn as track: straights, curves, three-way switches,
one flat crossing, eight stations and six passing sidings. **Twenty-four trains** run on it. Each
train has a start platform, a heading, a target station, a speed class and an earliest departure
tick, and each can break down at any moment for eight to twenty-four ticks and sit there blocking
the line. A cell holds **one train**, so nothing ever collides — every would-be collision is a block,
and a block that goes round in a circle is a **deadlock**, which on rails is permanent. The only
number the league reads is how many of the twenty-four trains reached their station **on time**, and
the only way to lose it is for the obvious greedy route of each train to jam the network. There is
no central scheduler: four dispatchers each command six trains, they cannot see each other's
timetables, and the only channel between them is a 120-character radio call.

### Seats, trains, aliases

- **`num_agents` = 4.** Exactly four seats, always — in both manifest variants and in the
  certification fixture. **Each seat is a dispatcher commanding a fleet of six trains** (four in the
  `branchline` variant), which is the idea's own second option, "one policy per fleet". The reasoning,
  stated once:
  - Every seat is an **LLM policy**, and all seats' calls go out as **one parallel batch per turn**
    (§Decisions). Four calls per turn is one batch of four; at the starter's `turnSpacingMs` floor
    that is 20 requests/minute against the sidecar's 30/minute per-episode cap. One seat per train
    would be 24 seats — 120 req/min, six times the cap, and a per-turn batch that cannot finish
    inside the budget. The seat count is set by the wall clock, not by taste.
  - Four seats is also the number that seats **both LLM champions and both scripted fillers in a
    single episode**, which makes the idea's "cooperative cross-play scoring" true by construction
    rather than by luck.
  - The idea's "10–200 trains" is answered at **24 trains** (`mainline`) and **16** (`branchline`) —
    both inside the range, both sized so the board is legible at 360 px (§Viewer). Other train counts
    and other seat counts are §Out of scope.
  - "Every agent is its own dispatcher" survives intact: there is no central scheduler, each seat
    plans only its own fleet, and no seat can see another's targets or orders.
- **Two name spaces.** In-game the seats are **`Alpha`, `Beta`, `Gamma`, `Delta`** — the starter's
  `IdentityNames` (`src/ctf/roster.nim:64`, `["alpha","beta","gamma","delta",…]`), title-cased for
  display by `seatAlias(slot)`. Those aliases are the only names that appear in an observation, a
  prompt, an order, a `say`, a radio line or a sprite label. The seats' **real policy/player names**
  (`daveey`, `daveey-1`, `Baseline (1)`, `Baseline (2)`) live only in `results.names`, in the replay's
  join records and in the viewer's scorebug. `showPlayerLabels` is **false**, as in the starter's
  paintball variant, so no in-board sprite can leak an identity. A seat can never learn who it is
  dispatching alongside — the idea's anti-collusion requirement.
- **Train ids** are `T01`…`T24`, allocated in seat order: seat 0 owns `T01`–`T06`, seat 1 `T07`–`T12`,
  seat 2 `T13`–`T18`, seat 3 `T19`–`T24`. In `branchline` each seat owns four and the ids run
  `T01`–`T16` in the same block order. A train's id is public; its **owner's alias** is public; its
  target and its orders are not.
- **Seat colours** are cosmetic and fixed by slot: Alpha red, Beta blue, Gamma green, Delta yellow
  (the four colours the starter's art ships in). Every train is drawn in its owner's colour.
- **Cells** are `(x, y)`, `x` rightwards from 0, `y` downwards from 0; cell index is `y·W + x`. Every
  tie-break in this note that says "lowest cell index" means that number.

### The network

The topology is **authored, not generated**, and lives in committed map files
`data/rail/<name>.rail`. Three files per pool; the **episode's network is chosen by the seed**
(`network = pool[seed mod 3]`), which is the idea's "networks … seeded" without the
implementation-defined behaviour of a procedural rail generator (§Sim module → divergences).

A `.rail` file is UTF-8 text with four sections:

```
# flatland rail map v1
name main_a
size 28 14
rail                       <- exactly 14 lines of exactly 28 tile chars
stations                   <- exactly 14 lines of exactly 28 chars: '.' or a station letter A..H
labels                     <- "<id> <x> <y>" lines: S1..S6 (sidings), J1..J9 (named junctions)
```

**The tile alphabet and the one transition rule.** Every tile is defined by its set of **ends**
(which of N/E/S/W the track leaves through). A train travelling in direction `d` entered the cell
through the `opposite(d)` end; it may leave through **any other end of the tile**, and its new
heading is that end's direction. That single rule generates straights, curves and switches uniformly.
Two exceptions: the flat crossing `+` allows only `N→N, E→E, S→S, W→W`; and a **dead end** (one end)
has an empty exit set, so the train reverses and leaves through the end it came in
(upstream's 180° dead-end rule).

| Char | Ends | What it is |
|---|---|---|
| `.` | — | no rail |
| `-` | E, W | straight |
| `\|` | N, S | straight |
| `L` | N, E | curve (└) |
| `J` | N, W | curve (┘) |
| `r` | S, E | curve (┌) |
| `7` | S, W | curve (┐) |
| `T` | E, W, S | three-way switch |
| `Y` | E, W, N | three-way switch |
| `>` | N, S, E | three-way switch |
| `<` | N, S, W | three-way switch |
| `X` | N, S, E, W | four-way junction, all turns legal |
| `+` | N, S, E, W | **flat crossing**: straight only, no turning |
| `u` `d` `e` `w` | N / S / E / W | dead-end stub facing that way |

Internally a tile is a `uint16` mask: bit `(3 - inDir) * 4 + (3 - outDir)` set means "a train
entering heading `inDir` may leave heading `outDir`", with `N=0, E=1, S=2, W=3` — the same 16-bit
per-cell shape upstream uses. `railmap.nim` builds the mask from the ends rule at load; the map file
is the authoring surface and the mask is the runtime representation.

**Validation at load** (`tests/test_flatland_railmap.nim` runs it over every committed map, and the
server refuses to start on a failure): every end of every rail tile must point at an in-grid rail
cell whose opposite end is present; every station letter must sit on a rail cell; every station must
have **exactly three platform cells**; every id in `labels` must sit on a rail cell; every station
must be reachable from every other station in the directed (cell, heading) graph; and the file's
sha256 must equal the literal pinned in the test.

**Nodes, edges and single-track sections.** A **node** is any rail cell with three or more ends, any
flat crossing, and any station platform cell. An **edge** is a maximal chain of two-end cells joining
two nodes. Because a cell holds one train, **no train can pass another inside an edge** — every edge
is a one-track section, which is the idea's "one-track sections", and the six labelled `S1`…`S6`
sidings are edges that run parallel to a main edge between the same two nodes so a train can be put
away there while another passes. `mainline` maps carry a double-track spine (two parallel edges
between each pair of spine junctions) with single-track branches; `branchline` maps are single-track
throughout with five passing loops.

### The clock

- **Tick** = one Flatland `step`. **`maxTicks = 496`** (upstream's formula for a 28 × 14 grid).
- **Command turn** = one order round, every **`turnTicks = 16`** ticks, beginning with turn 1 at tick
  0 before any stepping. **31 command turns per episode.** One game per episode (`maxGames = 1`): the
  game is cooperative, so there is no side to swap.
- Between turns the loop runs **uncapped** (`fastMode: true`), so the 496 ticks cost about a second of
  CPU in total; the wall clock of an episode is the 31 LLM turns (§Decisions).
- **Why a 16-tick cadence rather than a true per-switch interrupt.** The idea's "decisions only matter
  at switches" is honoured in the *content* of the turn, not by making the engine's schedule
  data-dependent: each observation flags, for every one of the seat's trains, the **next decision
  point** (the next node with more than one legal exit) and the **ETA in ticks** to it, and the driver
  handles everything in between. With 16 ticks per turn and a fastest speed of one cell per tick, no
  train can traverse more than 16 cells — shorter than any spine edge on the shipped maps — between
  consecutive turns, so a seat always gets at least one turn of notice before every switch its trains
  reach. A data-dependent cadence would make the number of LLM calls per episode unbounded, which the
  wall-clock budget forbids.

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (at tick `16·(T−1)`), in this order:

1. The engine snapshots the world and builds all four seats' observation objects (§Decisions).
2. All four seats' LLM requests go out as **one parallel batch** (`curl.makeRequests`, the starter's
   `decideAll` shape), attempt-1 deadline `attempt1Ms = 9000`. Scripted seats compute locally,
   instantly, and consume no request.
3. Each seat that timed out, errored, returned non-JSON or returned no usable `orders` array is
   retried **once**, again as a single batch, `retryMs = 4000`.
4. A seat still without a usable reply gets the **`yielder`** scripted orders computed server-side,
   and a `fallback` record is written (§Decisions).
5. Orders are applied, in ascending slot, then in ascending train id within a slot. A train named in
   the reply takes the new order; a train not named **keeps the order it had**; an order whose fields
   do not validate is **repaired to that train's previous order** (turn 1's default is `yielder`'s
   order), never dropped into "no order", and counted in `ordersRejected` — the starter's
   `directives.nim` repair-don't-reject discipline. Orders naming a train the seat does not own, or a
   train that has already arrived, are dropped and counted.
6. `say` (≤ 120 runes) and the accepted orders become replay chat records. `say` is the network
   radio: **every** seat hears **every** seat's last-turn `say` in its next observation. `notes`
   (≤ 240 runes) is private and echoed back to that seat only.
7. `turnSpacingMs = 12000` is a floor on the wall clock between consecutive **batch starts** (the
   starter's mechanism in `decide.nim`, kept), which is what keeps four seats under the sidecar's
   30 req/min per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the game
and nothing else mutates the world**:

1. `tick += 1`. Snapshot the occupancy layer (cell → train id, or none). Every rule below reads the
   snapshot for *reading*, and writes through it as trains commit, in the order given.
2. **Malfunction rolls.** For every train that is `running` and not already malfunctioning, in
   ascending train id, compute `h = mix64(seed, trainId, tick)` (§Sim module). If
   `h mod malfunctionRate == 0` the train breaks down: `malfunctionLeft = minDuration +
   ((h shr 32) mod (maxDuration - minDuration + 1))`, a `malfunction` event is emitted,
   `malfunctions += 1`. `minDuration = 8`, `maxDuration = 24`.
3. **Malfunction countdown.** Every malfunctioning train decrements `malfunctionLeft`;
   `malfunctionTicks += 1` for each. On reaching 0 it returns to `running` and emits `repaired`. A
   malfunctioning train takes no action and continues to occupy its cell.
4. **Departures.** For every `waiting` train, in ascending train id: if `tick >= earliestDeparture`
   **and** its order is not `hold` **and** its start platform cell is unoccupied, it becomes
   `running`, occupies that cell with its start heading, `progress = 0`, and emits `depart`. A waiting
   train is **off the board** and occupies nothing (upstream: an agent before entry has no position).
5. **Choose one action per running, non-malfunctioning train**, in ascending train id, from that
   train's current order via the driver (§Decisions → "The driver"). The action is one of
   `DoNothing 0, MoveLeft 1, MoveForward 2, MoveRight 3, Stop 4`.
6. **Progress.** A train whose action is `Stop` does not accrue progress and is marked `held`. Every
   other running, non-malfunctioning train increments `progress` by 1, capped at its speed class
   `ticksPerCell`. A train with `progress < ticksPerCell` is mid-cell and does nothing else this tick.
7. **Move resolution**, over the trains with `progress == ticksPerCell` and action ≠ `Stop`, **in
   ascending train id** (upstream: "the actions of the agents are executed in order of their handle").
   For each such train:
   - **a.** Resolve the requested exit end from the action: `MoveForward` → the end in direction
     `heading`; `MoveLeft` → `(heading + 3) mod 4`; `MoveRight` → `(heading + 1) mod 4`; `DoNothing` →
     same as `MoveForward`. If that end is not in the tile's legal exit set for this heading, **repair**
     in this fixed order: `MoveForward` if legal, else the single legal exit if there is exactly one,
     else the legal exit with the lowest direction index; and count it in `actionsRepaired`. On a dead
     end the exit set is empty and the train reverses (heading becomes `(heading + 2) mod 4`, target
     cell is the one it came from).
   - **b.** **Segment interlock.** If the target cell is the first cell of an **edge** the train is not
     already on, and any train currently on that edge is travelling in the **opposing** direction
     along it, the move is refused. (Trains travelling the same way may follow each other into an
     edge.) This is a divergence from upstream and is argued in §Sim module.
   - **c.** If the target cell is on rail and **currently unoccupied**, the train moves: it vacates its
     cell, occupies the target, `heading` becomes the exit direction, `progress = 0`. Because
     resolution is sequential in train id, a train can never swap cells with another in the same tick,
     and a queue advances in a single tick only when its leader has the lower id — the deterministic
     "relative priority by handle" upstream documents.
   - **d.** Otherwise the train does not move; `blockedTicks[train] += 1`.
8. **Arrivals.** After every move, in ascending train id: if a running train's cell is a platform cell
   of its **target** station, it **arrives** — it is removed from the grid (upstream
   `remove_agents_at_target = True`), `state = arrived`, `arrivalTick = tick`,
   `lateness = max(0, tick - scheduledArrival)`, `onTime = tick <= scheduledArrival`. `arrivedTotal`
   and the owner's `arrived[slot]` increment; if on time, `fleetOnTime` and `onTime[slot]` increment.
   An `arrive` event is emitted.
9. **Stall accounting.** `stalledTicks[t] += 1` for every running train that was at
   `progress == ticksPerCell`, was not `Stop`, was not malfunctioning, and did not move; otherwise
   `stalledTicks[t] = 0`.
10. **Jam and deadlock detection** (`deadlock.nim`). Build the directed **waits-for** graph over
    running trains: `A → B` when A is stalled and either the cell A wanted holds B, or A was refused
    by the interlock and B is the **lowest-id** opposing train on that edge.
    - A **jam** is a weakly-connected component of the waits-for graph with **≥ 2** members all of
      which have `stalledTicks ≥ jamTicks = 12`. Entering one emits `jam`; leaving emits `jamclear`;
      `jamTicksTotal` counts every tick at least one jam is active and `longestJamTicks` its longest
      run.
    - A **deadlock** is a directed **cycle** in the waits-for graph in which every member has
      `stalledTicks ≥ deadlockTicks = 24` and **no member is malfunctioning** (a queue behind a broken
      train is a delay, not a deadlock). Entering one emits `deadlock` and increments `deadlocks`;
      leaving emits `deadlockclear`; `deadlockTicks` counts every tick at least one is active. The
      cycle search is a DFS from the lowest-indexed member, visiting successors in ascending train id,
      returning the first cycle found — pinned for determinism. A deadlock is re-evaluated every tick,
      not latched: it breaks only if a member is re-routed before it commits to the contested edge,
      which is exactly the skill the game rewards. Any deadlock still active at the last tick makes
      its members `stranded` and is reported as `terminalDeadlock`.
11. Mix the tick into `gameHash` and append it to the replay's hash chain.
12. Evaluate the end conditions.

**Collisions cannot occur.** The exclusive-cell rule of step 7c turns every would-be collision into a
block. `results` carries no `collisions` key and the viewer draws no crash; the failure mode this game
shows is the deadlock, exactly as the idea frames it ("a deadlock game").

### Scoring formula and sign

Per train `t`, fixed at reset and never changed:

```
routeCells[t]        = BFS distance in cells from (start cell, start heading) to the nearest
                       platform cell of t's target station, over the directed (cell, heading)
                       transition graph, ignoring other trains
scheduledArrival[t]  = earliestDeparture[t] + ticksPerCell[t] * routeCells[t] + slackTicks   (slackTicks = 24)
```

At the end of the episode:

```
arrivedTotal   = number of trains that reached their target station          (0 .. trainCount)
fleetOnTime    = number of those whose arrivalTick <= scheduledArrival       (0 .. trainCount)
arrived[s]     = seat s's trains that arrived
onTime[s]      = seat s's trains that arrived on time
scores[s]      = 1000 * fleetOnTime  +  10 * arrivedTotal  +  onTime[s]
```

**Sign: higher is better; no term is ever negative.** Deadlocks, jams, malfunctions, blocked ticks and
lateness subtract nothing — they cost arrivals, which is the only currency, exactly as the idea's
"reward: arrive on time; collisions and deadlocks are the failure" pins it.

The first two terms are **identical for all four seats**: pure common interest, the idea's "fully
cooperative (shared on-time score)". The third is the individual target and is deliberately an
epsilon: `onTime[s] ≤ 6` and `10 * arrivedTotal ≤ 240 < 1000`, so the ordering is strictly
lexicographic — **network on-time count first, total arrivals second, own on-time trains only as a
tie-break** — and a dispatcher who shoves its own six through at the cost of one other seat's on-time
train loses 1000 to gain at most 6. `tests/test_flatland_scoring.nim` asserts the bound
(`onTime[s] < 10` and `10*arrivedTotal < 1000`) over randomised end states, so the lexicography can
never invert.

**The league ranks by `results.scores[s]`** (the platform's Elo, 1000 start / K 32, is computed from
these per-episode per-seat numbers). `results.win[s]` is `fleetOnTime >= parOnTime` — the same boolean
for all four seats, a "did the network run" flag, not a duel — and `results.winner` is always `null`,
because a cooperative episode has no winner. `parOnTime` is a config field (**15** of 24 in
`mainline`, **9** of 16 in `branchline`).

**Lateness is measured and shown, never scored.** `latenessTicks[s]` sums `lateness` over the seat's
arrived trains and is reported in `results`, on the endcard and in the on-time leaderboard, but does
not enter `scores`. Making it a scored term would need a magnitude choice the idea does not pin and
would risk inverting the lexicography; §Out of scope records the decision.

**Cross-play (the idea's integrity note).** Scoring is cross-play, not self-copies: the certification
fixture seats **two `yielder` and two `timetable`** scripted dispatchers, and the league division runs
**two scripted fillers alongside the two prompt champions** (§Packaging), so a four-seat round robin
seats each champion with unfamiliar partners in essentially every episode. The game records what it
was given: `results.policyKinds = ["llm","llm","scripted","scripted"]` and `results.crossPlay = true`
when at least one LLM seat and at least one scripted seat sat together. And **both seeded streams are
unsteerable**: the network is `pool[seed mod 3]`, and whether train `i` breaks at tick `t` is the pure
hash `mix64(seed, i, t)` — not a consumed RNG stream, so no ordering of decisions by any seat can
shift another train's draws (§Sim module).

### End conditions and legal `results.reason` values

The episode ends at the first of: **all trains resolved**, **quiescence**, the **tick cap**, or the
**wall-clock stop**.

- **All resolved** — every train has `state == arrived`. Settles immediately.
- **Quiescence** — `quiesceTicks = 120` consecutive ticks in which no train arrived, no train departed,
  no train entered a new cell and no train is malfunctioning. The network is dead; playing out the
  remaining ticks would add nothing but a flat replay. Settles immediately, with the deadlock alarm
  lit if a deadlock is active.
- **Tick cap** — `tick == maxTicks`.
- **Wall-clock stop** — the engine's `wallClockBudgetSeconds` guard.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the episode finished on its own terms: all resolved, quiescent, or the tick cap.
  The healthy value. `results.endRule` says which: `allArrived` | `quiescent` | `tickCap`.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine
  stops at the current tick, settles with the **real** arrivals so far (never zeroed, so a deadline
  episode is still rankable), writes `results.json` and the replay, and exits 0.
  `results.endRule = "wallClock"`. **Declared acceptable** for SPEC §Definition of done check 4. The
  budget guard below exists so it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from the
  last completed tick, `results.endRule = "fault"`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0. A defect:
  `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum: `allArrived | quiescent | tickCap | wallClock |
fault`.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn (all seats fall to `yielder`, microseconds per turn), the remaining ticks run at full speed, and
the episode still ends `complete`. A `budget_guard` record names the turn it fired.

A seat that never connects, disconnects mid-episode, or fails every decision **does not end the
episode**: its six trains are dispatched by `yielder` and the episode runs to its natural end with
`deadSeats[s] = true`. Nothing a player container does can stop the clock — the starter's
`lobbyJoinTimeoutTicks` bounds the lobby and its strike rule stops a silent seat from consuming the
per-turn deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {timetable, yielder}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=yielder` (the starter's "anything unrecognised is the published default" rule in
`baselines.nim`). A scripted policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/flatland/anthropic_api_key` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/flatland_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"timetable"|"yielder"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then acknowledge
frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3 close-frame race:
whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/flatland/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every turn falls back instantly with no network wait, so offline
  certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, tolerant of trailing prose) and `truncateRunes`/`sanitizeSay` unchanged.

### Cadence, batching, and the wall-clock arithmetic

One command turn every **16 ticks**; **31 turns per episode**. At each turn the server builds all
**four** seats' request bodies and issues them as **one parallel batch** — never sequentially; this is
a simultaneous-decision game and serial calls would quadruple the wall clock for nothing. At most 4
calls in flight; at most `4 × 31 × 2 = 248` calls per episode including retries.

```
attempt1Ms                          9.0 s
retryMs                             4.0 s
turnBudgetMs                       14.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                      12.0 s   -> 4 seats x 60/12 = 20 req/min  (sidecar cap: 30)

31 turns x max(spacing 12 s, budget 14 s), absolute worst          = 434 s
   typical (haiku answers in ~3-5 s, so spacing dominates)         = 372 s
496 ticks, 24 trains, integer Nim + BFS over <=392 cells, fastMode =   1 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at        =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)     =  20 s
                                                                   -------
typical total                                                      = 408 s   < 720 s
absolute worst case (434 + 1 + 100 + 20)                           = 555 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                            = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                              = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_flatland_manifest.nim` asserts it.

**Rate guard.** `turnSpacingMs` pins the steady state at 20 req/min, but a turn in which every seat
retries issues 8 requests. The engine therefore keeps a **rolling 60 s request counter**: if issuing
the next batch would push the trailing-60 s count above **28**, the seats that would exceed it skip
the call for that turn and take the `yielder` orders with `cause = "rate_guard"`. Bounded, logged,
never a sleep on the episode's critical path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant: seats send no per-tick
inputs (the server computes every action), so the Sprite v1 Ready packet's dead-reckoning hazard
cannot arise.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 14 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop,
and ctf's `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's orders for that turn become the **`yielder`** scripted orders computed inside the game (the
same proc the `yielder` baseline uses — imported, never duplicated), and a `fallback` record is
written with `cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard,
budget_guard, disconnected}`. `results.fallbackTurns[s]` counts them.

**No failure mode leaves a train without an order.** The driver always has one: this turn's, else last
turn's, else `yielder`'s. A seat that never connects is reported once to `COGAME_PLAYER_FAILURE_URI`
with the platform's **closed** payload — exactly `{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: `allArrived` and `quiescent` both end the
episode before `maxTicks` (§The game), and the budget guard drops every seat to scripted play the
moment two more full turns would not fit.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **infrastructure and block occupancy are public; intentions are private.** A real
signal box sees where every train is; it does not see another box's timetable. That is what makes the
idea's "yielding conventions without a central scheduler" the actual problem.

**Visible.**

- **The whole network, once, at registration** — the rail map as the same ASCII tile grid the file
  carries, the station letters and their platform cells, the six siding ids, the nine named junction
  ids, and a **junction graph**: for each edge, its two endpoint node ids, its length in cells, and
  whether a parallel edge exists between the same pair (i.e. whether that section is passable in both
  directions at once). Static for the whole episode; afterwards referred to by id.
- **Full block occupancy, every turn** — one compact line per train currently on the grid: train id,
  owner alias, cell, heading, speed class, and state (`running` | `held` | `malfunctioning`), plus
  `stalled` ticks if non-zero. All 24, not just the seat's own. This is the signal-box view.
- **Everything about the seat's own trains** — for each: id, state, cell, heading, speed class
  (`ticksPerCell`), **target station**, `earliestDeparture`, `scheduledArrival`, `ticksLate` so far
  (`max(0, tick - scheduledArrival)` for a train still running), current order and its age in turns,
  `last_order_result`, remaining route as the next **three** node ids, **next decision point** (node id
  and ETA in ticks), `blocked_ticks_last_turn`, and `malfunction_left`.
- **The network radio** — every seat's `say` from the previous turn, tagged with the speaker's alias,
  most recent first, at most 3 lines, each already truncated to 120 runes.
- **Public network statistics** — `tick`, `turn`, `arrivedTotal`, `fleetOnTime`, the active jam list
  (train ids) and the active **deadlock** list (train ids and the cells they are fighting over), and
  `malfunctions` so far.

**Hidden.** Every other seat's trains' **targets, scheduled arrivals, routes, orders and notes**;
every other seat's **real player name**, policy name and kind; the seat's own trains' future
malfunction draws and every other train's; the network pool entry not selected; and the other seats'
fallback/decision statistics. Nothing about any seat's identity ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `your_notes`)
into the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "Gamma",
  "dispatchers": ["Alpha", "Beta", "Gamma", "Delta"],
  "turn": 9, "of": 31, "tick": 128, "turn_ticks": 16, "ticks_left": 368,
  "network": {"name": "main_b", "width": 28, "height": 14,
              "stations": ["A","B","C","D","E","F","G","H"],
              "sidings": ["S1","S2","S3","S4","S5","S6"],
              "junctions": ["J1","J2","J3","J4","J5","J6","J7","J8","J9"]},
  "your_trains": [
    {"id": "T13", "state": "running", "cell": [12, 5], "heading": "E", "ticks_per_cell": 2,
     "target": "F", "scheduled_arrival": 210, "ticks_late": 0,
     "order": "run", "order_age_turns": 3, "last_order_result": "running",
     "route_next": ["J4", "S3", "F"], "next_decision": {"node": "J4", "eta_ticks": 6},
     "blocked_ticks_last_turn": 0, "malfunction_left": 0},
    {"id": "T14", "state": "malfunctioning", "cell": [19, 9], "heading": "N", "ticks_per_cell": 3,
     "target": "B", "scheduled_arrival": 188, "ticks_late": 0,
     "order": "run", "order_age_turns": 5, "last_order_result": "malfunction",
     "route_next": ["J7", "J8", "B"], "next_decision": {"node": "J7", "eta_ticks": 9},
     "blocked_ticks_last_turn": 16, "malfunction_left": 11},
    {"id": "T15", "state": "waiting", "cell": null, "heading": "W", "ticks_per_cell": 1,
     "target": "D", "earliest_departure": 144, "scheduled_arrival": 205, "ticks_late": 0,
     "order": "hold", "order_age_turns": 1, "last_order_result": "held",
     "route_next": ["J2", "J1", "D"], "next_decision": {"node": "J2", "eta_ticks": 22},
     "blocked_ticks_last_turn": 0, "malfunction_left": 0}
  ],
  "block_occupancy": [
    {"id": "T02", "by": "Alpha", "cell": [13, 5], "heading": "E", "ticks_per_cell": 1, "state": "running"},
    {"id": "T09", "by": "Beta",  "cell": [15, 5], "heading": "W", "ticks_per_cell": 2, "state": "held", "stalled": 7},
    {"id": "T21", "by": "Delta", "cell": [19, 8], "heading": "N", "ticks_per_cell": 4, "state": "running", "stalled": 14}
  ],
  "radio": [
    {"from": "Alpha", "text": "T02 has the down main to J5, hold westbounds at J4"},
    {"from": "Delta", "text": "T21 stalled behind your broken T14 - can you side it?"}
  ],
  "network_status": {"arrived": 7, "on_time": 6, "malfunctions": 11,
                     "jam": ["T09", "T21"], "deadlock": [], "deadlock_cells": []},
  "your_notes": "T13 via S3 so T02 keeps the main; release T15 after T02 clears J2"
}
```

Field rules. `heading` is one of `N|E|S|W`. `state` is one of
`waiting|running|held|malfunctioning|arrived`. `last_order_result` is one of
`running|arrived|held|parked|no_route|no_siding|unknown_train|deadlocked|malfunction` — the driver's
honest report of why the previous order ended, which is what lets a seat recover from a race with
another seat's train. `your_trains` is always exactly `trainsPerSeat` entries long (arrived trains stay
in the list with `state: "arrived"`) so the array shape never changes. `block_occupancy` lists every
train currently on the grid, ascending by id, and omits waiting and arrived trains.

### Reply schema and per-field caps

```json
{"orders": [{"train": "T13", "verb": "siding", "at": "S3"},
            {"train": "T15", "verb": "hold"}],
 "say": "T13 into S3, main is clear for Alpha's T02",
 "notes": "release T15 next turn"}
```

| Field | Type | Cap / domain |
|---|---|---|
| `orders` | array | **≤ 6 entries** (= `trainsPerSeat`; ≤ 4 in `branchline`). Entries past the cap are dropped and counted in `ordersRejected`. Absent or empty = "every train keeps its order" and the reply is still **usable** |
| `orders[].train` | string | **≤ 4 runes**; must be one of **this seat's** train ids and not already arrived |
| `orders[].verb` | string | **≤ 6 runes**; enum `run` \| `hold` \| `siding` \| `route`, lower-cased before matching |
| `orders[].at` | string | required iff `verb == "siding"`; **≤ 4 runes**; a siding id from the published list |
| `orders[].via` | string | required iff `verb == "route"`; **≤ 4 runes**; a station letter, siding id or junction id from the published lists |
| `say` | string | **≤ 120 runes** (`MaxSayRunes`) — the network radio; heard by every seat next turn and drawn in the feed |
| `notes` | string | **≤ 240 runes** (`MaxNoteRunes`) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160` (`src/ctf/sim_types.nim:747,794-795`),
which are a 10-character in-world shout and a short note. A dispatcher's radio call has to name a
train, a section and an intent, so `MaxSayRunes = 120` and `MaxNoteRunes = 240` here, and
`ShoutMaxChars` is deleted with the shout mechanic (§Sim module → Deleted).

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded
error text — is truncated on RUNE boundaries** via the starter's `truncateRunes`/`runeSubStr`, never by
byte index. Byte truncation is what makes a replay that renders in a browser fail a strict UTF-8
parser; `tests/test_flatland_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level and per-order keys are ignored. A reply with a valid `say` but no `orders` is
**usable** (every train keeps its order and the radio line is delivered). A reply that is not a JSON
object is a parse failure. An order whose `verb` is valid but whose required argument is missing,
unknown, or names an unreachable siding is **repaired to that train's previous order**, counted in
`ordersRejected`, and reported back next turn as `last_order_result` unchanged (or `no_siding`).

### System prompt (fixed, identical for both champions)

```
You are the dispatcher for SIX trains on a shared rail network. Three other dispatchers
run six trains each on the same rails. You do not control theirs and you cannot see
their targets or their orders. Every 16 simulation ticks you issue orders and a
deterministic driver runs every train until you change them.

THE NETWORK
- A grid of track: straights, curves, three-way switches, one flat crossing, eight
  stations A-H (three platforms each), six passing sidings S1-S6, nine named junctions
  J1-J9. Between two junctions the track is a SECTION and only one train fits per cell,
  so no train can overtake inside a section.
- Two trains may not enter the same section from opposite ends. The second one waits at
  the mouth - and while it waits it is standing ON the junction, blocking everyone
  behind it. That is how a network jams.
- Trains break down at random for 8 to 24 ticks. A broken train blocks its cell and
  nobody can repair it. Plan around it.
- Speed class is ticks_per_cell: 1 is an express, 4 is a freight. A freight on the main
  line behind an express is a whole timetable lost.

WHAT SCORES
Only how many of the TWENTY-FOUR trains reach their target station ON TIME. Everyone
gets the same number. Your own six are a tie-break worth almost nothing. Getting one of
your trains through by stalling two of somebody else's is a loss.

YOUR ORDERS (one per train per turn; a train keeps its order until you change it)
- {"train":"T13","verb":"run"}                 head for the target on the fast route
- {"train":"T13","verb":"route","via":"S3"}    head for the target THROUGH that point
- {"train":"T13","verb":"siding","at":"S3"}    pull into that siding and wait there
- {"train":"T13","verb":"hold"}                stop where it is (or do not depart yet)

A DEADLOCK IS PERMANENT
Trains cannot reverse. If your train is nose-to-nose with another across a section,
neither will ever move again and both are lost for the rest of the episode. The only
cure is prevention: side a train BEFORE it commits, or hold it before it departs.

TALKING
"say" is a radio call every other dispatcher hears next turn. It is the ONLY way they
learn what you intend. Use it to claim a section, to name which way you are running a
single-track, or to ask someone to side a train. "notes" comes back to you next turn and
to nobody else.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the character {
and end with }. No prose, no markdown, no code fences.
{"orders":[{"train":"T13","verb":"siding","at":"S3"}],"say":"<=120 chars","notes":"<=240 chars"}
```

### Champion #1 — `flatland-signalman` (owner **daveey**), `PLAYER_PROMPT`

```
Run a speed-priority railway and say so out loud. The rule you enforce is: the FASTER
train keeps the main, the SLOWER train sides. On turn 1 read your six trains' speeds and
broadcast which of yours are freights (ticks_per_cell 3 or 4) - "T14 and T17 are freight,
they will side for anything faster".
Every turn, for each of your trains, look at block_occupancy along its route_next. If a
train with a SMALLER ticks_per_cell is heading the other way into the same section, issue
"siding" at the nearest siding in your route_next and say which section you are clearing.
If YOUR train is the faster one, issue "run" and say "T13 has <section>, express".
Never let two of your own trains enter the same single-track section from opposite ends:
hold the later-numbered one.
Departures are a lever. If a train is still waiting and the first two nodes of its
route_next already hold two or more trains, keep it on "hold" and say you are holding it;
a train that has not departed costs nothing and blocks nobody.
When one of your trains is malfunctioning, immediately re-route every OTHER train of
yours that lists the broken train's cell in its route_next, using "route" via a different
junction, and say on the radio where the blockage is - the other dispatchers cannot see
your plan, only your words.
If the deadlock list ever names one of your trains, stop trying to move it, say
"T<nn> deadlocked at <cell>, route around it", and spend the rest of the episode getting
your other five through.
```

### Champion #2 — `flatland-pathfinder` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Run a directional railway. Decide once, on turn 1, and never drift: for every single-track
section in the junction graph, the direction with the LOWER junction number is the "up"
direction. Your trains only ever traverse a single-track section in the up direction; if a
train's fast route needs it the other way, use "route" via a junction that keeps it on
double track, even if that is longer. Broadcast the convention on turn 1 in one line -
"single track is up-only for me: J2->J5, J6->J8" - and repeat it whenever the radio shows
somebody running against it.
Order your six trains by scheduled_arrival, soonest first. The soonest-due train gets
"run" and the radio claim. Every train due later than a train it would meet head-on gets
"siding" at the nearest siding ahead of the meeting point, issued at least two turns
before next_decision.eta_ticks reaches zero - a siding order given after a train has
entered the section does nothing.
Stagger your own departures: never let two of your waiting trains be released in the same
turn. Hold the one with the later scheduled_arrival.
If ticks_late for one of your trains passes 40, stop protecting it - it will not be on
time and its only remaining value is 10 points for arriving, so it becomes the train that
sides for everyone else. Say so.
If the jam list names two of your trains, side the higher-numbered one and hold the other;
if it names one of yours and one of somebody else's, side yours and say "siding T<nn>,
you have the section".
```

### The driver (deterministic, shared by every policy)

`src/flatland/driver.nim` — the starter's `control.nim` (directive → per-tick actuation), retargeted
from pixel steering to Flatland's five discrete actions. It runs once per train per tick and is the
**only** producer of actions. There is no randomness in it at all.

**Routing.** `route(train, goalCells)` is a breadth-first search over **states `(cell, heading)`** in
the directed transition graph, from the train's current state to any cell in `goalCells`. Successors
are expanded in the fixed end order `N, E, S, W`; ties are broken by lowest `(cellIndex, heading)`, so
the route is unique. Other trains are **not** obstacles in the plan (they move); the interlock and the
occupancy check are enforced at commit time, in the tick loop, not in the plan. Every route is
recomputed only when the order changes, when the train is at a node whose next hop is no longer on the
route, or after a `no_route`; the cached route is a list of node ids and the cell path between them.

| Order | Goal cells | On arrival at the goal | Finishes with |
|---|---|---|---|
| `run` | the three platform cells of the target station | — the engine credits the arrival | `arrived`; `no_route` if BFS fails |
| `route via V` | the cell of `V`, then re-plan to the target | continues automatically to the target | `arrived`; `no_route` if either leg fails |
| `siding at S` | the cells of siding edge `S` | `Stop` every tick, parked | `parked` on arrival, then holds; `no_siding` if `S` is unreachable |
| `hold` | — | `Stop` every tick; a waiting train does not depart | `held`, never finishes |

Given a route, each tick:

1. If the train is malfunctioning, it produces no action (step 3 of the tick loop already handled it).
2. If the order is `hold`, or the order is `siding` and the train is already on that siding's edge,
   emit `Stop`.
3. If `progress < ticksPerCell`, emit `DoNothing` — the train is mid-cell.
4. Otherwise take the next cell of the route and emit the action whose exit end reaches it:
   `MoveForward` if that end equals the current heading, `MoveLeft` for `(heading+3) mod 4`,
   `MoveRight` for `(heading+1) mod 4`. **Emit it even if a train is standing there** — the leader may
   move first this tick and refusing to try would forfeit the advance.
5. If the route is empty or its next hop is not a legal exit, recompute once; if that fails, emit
   `Stop` and report `no_route` at the next turn boundary.
6. A train whose order has finished (`parked`) holds. An `arrived` train is off the grid and produces
   nothing.

### Scripted baselines (both shipped as fillers; `yielder` is also the server-side fallback)

`src/flatland/baselines.nim`, the starter's module retargeted. Both emit the **same** order objects an
LLM does, through the same validator, which is what makes the bounded-orders test meaningful. Neither
ever emits `say` or `notes` — they are the dispatchers who will not talk to you, which is precisely
the "yielding conventions without a central scheduler" problem the idea names.

**`timetable`** — `PLAYER_SCRIPTED=timetable`. Pure greed, no yielding. Every turn, for each of its
trains in ascending id:
1. `arrived` → no order.
2. `waiting` and `tick >= earliestDeparture` → `run` (release as early as possible).
3. Anything else → `run`.
It is three lines, it is the jam machine, and it is the control that answers "did the LLM actually
coordinate?".

**`yielder`** — `PLAYER_SCRIPTED=yielder`, and the fallback. Every turn, for each of its trains in
ascending id, first matching rule wins:
1. `arrived` → no order.
2. `state == waiting`: release with `run` only if the first `departLookahead = 2` nodes of its route
   hold **fewer than 2** trains in total; otherwise `hold`.
3. `stalledTicks >= yieldAfter (8)` **and** the blocking train (the one on the wanted cell, or the
   lowest-id opposing train on the contested edge) has a **lower global train id** → `siding` at the
   **nearest siding on the route ahead**, by route order; if no siding lies ahead within
   `sidingLookahead = 3` nodes, `hold` for this turn only.
4. The next single-track section on the route (an edge with no parallel partner) already holds a train
   travelling the **other** way → `siding` at the nearest siding **before** that section, else `hold`.
5. `order == siding` and the contested section is now clear of opposing traffic → `run`.
6. Otherwise → `run`.

The lower-id tie-break in rule 3 guarantees exactly one train of any opposing pair yields, which is
what actually clears a queue. Like the starter's `DefaultBaselineParams`, the four tunables
(`yieldAfter = 8`, `departLookahead = 2`, `sidingLookahead = 3`, and the rule-3 id-order direction) are
a parameter object chosen by `tools/tune_baselines.nim`'s head-to-head sweep, not guessed;
`tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_flatland_tuning.nim` asserts
the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/flatland/`. The fork is a rename sweep
(`ctf` → `flatland`, `CTF_WIRE` → `FLATLAND_WIRE`; a CI grep asserts no `ctf_`/`CTF_` identifier
survives outside comment history) plus the changes below. **The same modules compile twice**: natively
into `/bin/flatland` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason a Python sim is not an option here.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/flatland/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417` |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/flatland/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` → **`FlatlandReplayMagic = "COWLDFLT"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/flatland/` (`control.nim` → `driver.nim`) | **fork**, retargeted not rewritten | the per-turn parallel batch, the two deadlines, `turnSpacingMs`, the budget guard at `decide.nim:341-345`, tolerant parsing, the rune caps, repair-don't-reject, the fallback ladder |
| `src/ctf/sim_state.nim` → `src/flatland/sim_state.nim` | **fork** | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/flatland/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames`, the results JSON builder |
| `src/ctf/events.nim` → `src/flatland/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/flatland/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/flatland/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/flatland/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24`, the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 120`, `MaxNoteRunes = 240`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/flatland/sim_config.nim` | **fork** | `GameConfig` lifecycle and `config.update` |
| `src/ctf.nim` → `src/flatland.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/flatland_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/flatland_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx/`--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_{red,blue,green,yellow}.png`, `data/soldier_{red,blue,green,yellow}_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*,blue_*,green_*,yellow_*}.webp` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, fog-of-war raycasting
and the first-person PIP, spray cans, floor paint and the paint grid, the paint buff, King of the Hill
and `hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the
barrage, med kits, shields, cardboard barriers, trenches, perks, handicaps, lives and respawns, teams
and four-team free-for-all, **shouts-as-cog-speech and `ShoutMaxChars`**, achievements, campaign mode,
`maxGames > 1` side-swapping, and **all of the pixel-space map machinery**: `arena.nim`'s wall masks
and pixel queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`,
`docs/MAPKIT.md`. The board here is a small integer grid loaded from a committed file; every one of
those is a config surface the rail rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `rig_real/`) — trains are drawn as
baked chips (§Viewer → Art) and a 128 px rig is never used at 12.8 px per cell.

### New modules

- `src/flatland/railmap.nim` — the `.rail` file parser, the tile-alphabet table, the ends rule, the
  `uint16` transition masks, the node/edge decomposition, the station/siding/junction id tables, the
  load-time validator, the cell↔index helpers, and the `(cell, heading)` BFS. Pure integer; no pixie,
  no pixel queries.
- `src/flatland/trains.nim` — the train arrays (`owner`, `startCell`, `startHeading`, `target`,
  `ticksPerCell`, `earliestDeparture`, `scheduledArrival`, `state`, `cell`, `heading`, `progress`,
  `malfunctionLeft`, `stalledTicks`, `blockedTicks`, `arrivalTick`, `lateness`, `order`, `route`), the
  reset draw, and the per-seat observation builder.
- `src/flatland/sim.nim` — the step loop of §The game: malfunction rolls, countdown, departures, driver
  actions, progress, move resolution with the interlock, arrivals, stall accounting, jam/deadlock
  detection, `gameHash`, end evaluation. Imports and re-exports the sim modules, as the starter's does,
  so `import flatland/sim` sees everything.
- `src/flatland/deadlock.nim` — the waits-for graph, the jam components, the deadlock cycle search of
  tick step 10, and the jam/deadlock span tables the viewer's scrubber and sparkline read.
- `src/flatland/upstream.nim` — every borrowed upstream constant with its citation comment beside it,
  in the style the starter uses for derived config values. This is the one file
  `tests/test_flatland_upstream.nim` checks.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cells, ids, tick counters, BFS distances, `ticksPerCell`. There
is no floating point anywhere in `sim.nim`, `railmap.nim`, `trains.nim`, `deadlock.nim`, `driver.nim`
or `baselines.nim`, and a test greps for it. In particular **speed is an integer `ticksPerCell`
(1 = express, 2 = fast, 3 = local, 4 = freight), not a float fraction**: `1/speed` ticks per cell is
exactly upstream's fractional-position accumulator for reciprocal speeds, without the float. That
makes the native ↔ wasm hash chain below exact by construction.

**Two seeded sources, both independent of anything a policy does:**

1. `setupRng` — the reset draw, a splitmix64 stream seeded from `seed`, consumed in this fixed order:
   (a) the network, `pool[seed mod 3]`; (b) the **injection of trains onto start platform cells** — the
   24 platform cells (8 stations × 3) are shuffled and `trainCount` of them taken in order, each with
   the heading of the platform's single outbound end; (c) each train's **target station**, drawn
   uniformly from the seven stations that are not its start, rejected and re-drawn (bounded at 200
   attempts, then take the station with the largest `routeCells`) until `routeCells >= minJourneyCells
   = 12`; (d) the **speed classes**, a fixed multiset — for 24 trains exactly six each of
   `ticksPerCell ∈ {1,2,3,4}`, for 16 trains exactly four each — shuffled and dealt in train-id order,
   so the composition never varies between episodes, only the assignment; (e) the **departure order**,
   a shuffle of the trains, giving `earliestDeparture[t] = departStagger (4) × rank(t)`.
2. **Malfunctions are not a stream at all.** Whether train `i` breaks at tick `t` is the pure hash
   `mix64(seed, i, t)` (splitmix64 over `seed`, `i·1000003`, `t·6364136223846793005`), evaluated
   independently for every `(i, t)`. Nothing a dispatcher does can shift another train's draws, change
   their order, or consume them out from under it — the strongest form of the idea's "malfunctions
   seeded". A dispatcher influences only *whether a train is running when its number comes up*, which
   is a legitimate part of the game. `tests/test_flatland_malfunctions.nim` asserts it by replaying the
   same seed with different seat behaviour and comparing the full `(train, tick) → duration` table.

The seed is randomised in `src/flatland.nim` before `config.update` (the starter's rule), recorded in
the replay config and in `results.seed`; `results.network` records the chosen map name. Two episodes
with the same seed and the same orders are byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDFLT`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `network`, `num_agents`, `trainsPerSeat`, `maxTicks`, `turnTicks`,
   `parOnTime`, `slackTicks`, `malfunctionRate`, `minDuration`, `maxDuration`, `jamTicks`,
   `deadlockTicks`, `quiesceTicks`, `players[].name`, `slots[]`, `fastMode`), then the record stream —
   joins (name, slot, token), leaves, **per-turn order records** (the only inputs this game has), chat
   records (`register`/`directive`/`fallback`/`budget_guard`/`stop`/`result`) and **one `gameHash` per
   tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/flatland_replay.nim` — which imports the
   **same** `src/flatland/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `flatland_load_replay` runs `parseReplayBytes` + `initReplayRuntime`;
   `flatland_frame` re-steps the sim from the recorded orders and compares `sim.gameHash()` against the
   recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens
   and surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: per train `(id, state, cell, heading, progress,
   malfunctionLeft, stalledTicks, orderKind, orderArg)`; then `arrivedTotal`, `fleetOnTime`, per-seat
   `arrived` and `onTime`; then the active jam set and the active deadlock set, each as sorted train
   ids; then `tick`.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact cannot
   be re-derived from sim state, so the stop is written as one record applied by the *same proc* on
   record and on playback, and `tests/test_flatland_replay.nim` runs the record→re-derive check for
   **every** end reason (`allArrived`, `quiescent`, `tickCap`, `wallClock`, `fault`), not just the
   healthy one (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 496 hashes + ≤ 124 order records + ~30 chat records ≈ **24 KB**. Everything else is
re-derived in the browser.

### Documented divergences from upstream (mirrored into `docs/PORTING-FLATLAND.md`)

1. **This is a rules-idiom reimplementation, not a bit-exact port.** Named at the top of this note.
   Upstream's `sparse_rail_generator`, `line_generator`, observation builders and numpy RNG order are
   not reproduced; the constants in the table at the head of this note are.
2. **The network is authored and seed-selected, not procedurally generated.** Three committed `.rail`
   files per pool with pinned sha256s. This keeps every episode legible at 360 px, keeps the topology
   free of the degenerate cases a generator produces, and still satisfies the idea's "networks …
   seeded".
3. **Speeds are integer `ticksPerCell`, not float fractions** (above). Equivalent for reciprocal
   speeds and required for the exact native↔wasm hash chain.
4. **Malfunctions are a pure hash of `(seed, trainId, tick)`, not a consumed Poisson stream.** The
   marginal law per train-tick is the same geometric/Poisson draw; the difference is that the draws are
   independent of decision order, which is what makes them unsteerable.
5. **Segment interlock** (tick step 7b). Upstream has no interlocking: two trains may enter opposite
   ends of a single-track section and deadlock immediately. Kept out here because with 24 greedy trains
   that ends most episodes in the first thirty ticks and leaves 460 ticks of a static replay. The
   interlock removes only the **single-section head-on**; the deadlocks that matter — a train waiting
   at one section mouth while standing on the junction another train needs, closing a cycle across two
   or more sections — are fully reachable, are what the alarm shows, and are the deadlocks the idea's
   "yielding conventions" actually solve. `tests/test_flatland_deadlock.nim` constructs one and asserts
   it is permanent.
6. **Who chooses the action changed, not what the actions are.** Per-tick RL policies are replaced by
   four high-level orders under a deterministic driver — the idea's own "an LLM can act on a
   switch-event cadence". The five-action space, the direction enum, the transition rule, the dead-end
   reversal, the by-handle move order, cell exclusivity, malfunction blocking and removal-at-target are
   upstream's.
7. **Scoring is `1000 × fleetOnTime + 10 × arrivedTotal + onTime[s]`** rather than upstream's per-agent
   reward. The idea pins "fully cooperative (shared on-time score) with individual targets"; the league
   needs a rankable per-seat integer. All the underlying quantities are recorded in `results`.
8. **No reversing except at dead ends** (upstream-faithful), which is what makes a deadlock terminal —
   and terminal deadlock is the game. §Out of scope records that backing up is not added.
9. **`maxGames = 1`** — the starter's multi-game episode is not used; a cooperative game has no side to
   swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with `turnTicks = 16` and four seats in the batch.
2. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration, **not** applied as a shout and **not** written to the replay chat stream; the server
   writes a redacted `register` record instead (policy label and kind, never the prompt). The starter's
   "hold an unappliable registration and re-read it when the slot lands" behaviour is kept verbatim.
   Any other chat text from a seat is dropped — dispatchers speak through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop iteration
   (`server.nim:1407-1417`), kept, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wallClock`, and written as the load-bearing stop record of point 5 above.

### The two named edits to `roster.nim`

1. **Aliases.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → `Alpha`, `Beta`, `Gamma`,
   `Delta`. The `IdentityNames` array itself (`roster.nim:64`) is unchanged. Sprite labels and the label
   manifest inherit the two-name-space rule with no further change, and `showPlayerLabels` is false.
2. **`squadResultsJson` → `networkResultsJson`** — one entry per seat, four entries in every
   seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits cell-space
   coordinates; the fov cache and shadowcasting are deleted (spectators see the whole network, and so
   do the dispatchers — occupancy is public by design, §Decisions).
2. **Train and rail pools.** New pools `TrainSpriteBase` and `RailTileBase` sized to `MaxTrains = 32`
   and `MaxRailCells = 392` (28 × 14), filled in id/index order and emitted incrementally like the
   starter's other object families.
3. **Baked rail bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the way
   the starter bakes endzone paint, and the rail tile atlas, the station platforms and the siding
   markings are baked onto it once (§Viewer → Art) — one static bake, so the per-frame cost is trains
   and overlays only.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player sockets at
`/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset route:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for
the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). Global
broadcasts are fire-and-forget so a slow viewer can never stall the episode.

### Results document (closed schema; `networkResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":            ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
  "aliases":          ["Alpha", "Beta", "Gamma", "Delta"],
  "scores":           [16247, 16246, 16245, 16245],
  "win":              [true, true, true, true],
  "winner":           null,
  "reason":           "complete",
  "endRule":          "tickCap",
  "fleetOnTime":      16,
  "parOnTime":        15,
  "arrivedTotal":     24,
  "onTime":           [5, 4, 3, 4],
  "arrived":          [6, 6, 6, 6],
  "latenessTicks":    [12, 41, 96, 33],
  "stranded":         0,
  "deadlockedTrains": 0,
  "deadlocks":        1,
  "deadlockTicks":    31,
  "jams":             7,
  "jamTicks":         104,
  "longestJamTicks":  38,
  "malfunctions":     29,
  "malfunctionTicks": 441,
  "finalTick":        496,
  "turnsPlayed":      31,
  "seed":             1734029581,
  "network":          "main_b",
  "policyKinds":      ["llm", "llm", "scripted", "scripted"],
  "crossPlay":        true,
  "llmTurns":         [31, 30, 0, 0],
  "fallbackTurns":    [0, 1, 0, 0],
  "ordersRejected":   [0, 3, 0, 0],
  "deadSeats":        [false, false, false, false],
  "stopDetail":       ""
}
```

`winner` is always `null` (cooperative). Adding a key means updating `networkResultsJson`, the
manifest's `results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit —
Coworld schemas are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDFLT`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (`SMOKE_REQUIRE_REPLAY_JSON`, template line 31).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"flatland/v1","gameVersion":"1","seed":…,"network":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"orders":[…],"radio":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md` documents
  for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.fleetOnTime, .results.arrivedTotal' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks, (.radio|length)' /tmp/ep.json
  ```
  Require `protocol == "flatland/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.arrivedTotal > 0`, and the champion seats' orders with `source == "llm"`, real
  verbs and non-empty radio lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDFLT`, format version, `gameName` `flatland`, `gameVersion` `1` |
| config JSON | `seed`, `network` (map name), `num_agents`, `trainsPerSeat`, `maxTicks`, `turnTicks`, `parOnTime`, `slackTicks`, `malfunctionRate`, `minDuration`, `maxDuration`, `jamTicks`, `deadlockTicks`, `quiesceTicks`, `players[].name` (real names), `slots[]`, `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| orders | per turn, per seat, per train: the accepted order — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The `.rail` map files are **compiled into the binary and into the wasm module** (a `const` table
generated at build time from `data/rail/*.rail`), and the replay carries the map **name**; the viewer
therefore reconstructs the exact network from bytes it already has, with no fetch. A map file change is
a `GameVersion` bump, and `tests/test_flatland_railmap.nim`'s pinned sha256s make an unversioned change
fail the build.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `orders` (array of `{train, verb, arg}`), `say` (≤ 120 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `turn`, `slot`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of twelve kinds:**

`turn` `{n}`; `order` `{slot, train, verb, arg}`; `say` `{slot, text}`; `fallback` `{slot, cause}`;
`depart` `{train, slot, cell, station}`; `arrive` `{train, slot, station, tick, onTime, lateness,
total}`; `malfunction` `{train, cell, duration}`; `repaired` `{train, cell}`;
`jam` `{trains, cells, tick}`; `jamclear` `{trains, ticks}`;
`deadlock` `{trains, cells, tick}`; `deadlockclear` `{trains, ticks}`;
plus `end` `{reason, endRule, fleetOnTime, arrivedTotal, par}`.

(That is twelve derived kinds plus `end`; `stepEvents` emits nothing else, and
`tests/test_flatland_events.nim` asserts the emitted set equals this list.)

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`arrival`,
`malfunction`, `deadlock`, `fallback`, `end`.** `turn`, `order`, `say`, `depart`, `repaired`, `jam` and
`jamclear` drive the feed, not the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Depart, Arrive, Malfunction, Repaired, Blocked, Jam, JamClear, Deadlock,
DeadlockClear, TurnStart, Directive, Fallback, PhaseChange` and the mandatory trailing summary row
(`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/flatland/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx/`--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/flatland_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the
viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one
piece: the Worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), the module is
emitted **non-modularized** as `flatland_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32
--cc:clang` through `emcc`, `--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`,
`-O2`, `--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`**
(non-negotiable: with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory
protection, so a failed allocation would write through nil into address 0 and corrupt the module's own
globals — the starter's own comment in `config.nims`), `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_flatland_load_replay,_flatland_frame,_flatland_input,
_flatland_packet_ptr,_flatland_packet_len,_flatland_mismatch_tick,_flatland_error_ptr,
_flatland_error_len,_flatland_stage_ptr,_flatland_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './flatland_replay.js')` in that order
(the starter's line 239, renamed only).

`flatland_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and
the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `flatland_load_replay` re-simulates the whole episode once headlessly (496
  ticks × 24 trains of integer work — single-digit milliseconds in wasm), records the per-tick
  cumulative arrivals and on-time count, the jam spans, the **deadlock spans**, the malfunction spans,
  the lull spans and the beat ticks, then resets and renders frame 0. That is what lets the on-time
  sparkline and the scrubber beats draw at **full width on the first frame** instead of growing in.
- `flatland_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (starter line 161) — posted by the Worker only
*after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute
means "a frame is on the canvas", not "a file was fetched". On failure it sets **`data-replay-error`**
on `<html>` with the message, in `showFailure()` (starter lines 8-20). Both are coworld-ctf's own
signals, inherited unchanged — this fork adds neither and removes neither. The `coworld-replay`
postMessage bridge's `ready` is posted **from a callback fired after** `data-replay-loaded="true"` is
set, never on rAF timing at the call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed
samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes in the starter). Not edited, not
  reformatted; `tests/test_flatland_viewer.nim` pins its sha256 against the starter's file. Everything
  this game adds lives in the appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats`
  / `renderClock` / `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats`
  ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (lines ~4281-4325), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density
  system are untouched, and the block is installed through the starter's own splice hook:
  `window.PaintballChrome` is renamed `window.FlatlandChrome` and its `install(PB_CTX)` /
  `frame(s, ctx, jumped)` / `event(e, s, ctx)` entry points (starter lines 4337, 2075, 3480-3481) are
  kept with the same signatures. The appended block replaces only the *contents* of the scorebug
  plates, adds the on-time leaderboard rail and the deadlock alarm chip, and retargets the feed rows,
  the beat rendering, the momentum series and the endcard columns. A test asserts the starter's byte
  prefix is intact up to the documented splice marker and that the file only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_flatland_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (`replay_broadcast.html:3558`; the cogball 0.1.4 latch scar: a
  signature drift threw mid-replay and latched `static_replay.js` into `failed`), `banner`, the beat and
  lull machinery, the endcard builder, the speed chips, the `?embed=1` path, and the
  `window.CTF_WIRE` → `window.FLATLAND_WIRE` rename emitted by `tools/gen_wire_constants.nim`. Deleted:
  every ctf-specific draw call and the FPV pipeline. Added: `drawRailBed`, `drawTrains`,
  `drawSignals`, `drawDeadlock`, `drawOnTimeRail`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `core.attachMinimap($('minimap-canvas'))` call
    (`replay_broadcast.html:4200`). **Zoom decision: dropped.**
    The board is a fixed 28 × 14 grid with no off-frame area; `relayout()` letterboxes it whole at every
    width (see "Legible at 360 px"), so per the pin a fixed arena drops `#viewpanel` entirely.
    `broadcast_core.js` already tolerates never being attached: `minimapSurface` and `minimapCtx`
    (`broadcast_core.js:540-541`) stay null and `drawMinimap()` returns on its first guard.
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no
    per-train point of view worth showing; the whole network is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.beat-marker.steal`, `.beat-marker.return`, `.beat-marker.capture`,
    `.beat-marker.hillflip`, `.beat-marker.tagout`, `.beat-marker.gamestart` and
    `.beat-marker.gameover` CSS rules (starter lines 919-934, 4431-4443) — those kinds are never
    emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with
    `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#bannerlane`, `#killfeed`,
    `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
    `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`,
    `#tick-clock`, `#speedchips`), `#scrub` with `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/
    `#scrub-head`, `#endcard` with `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`,
    and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract (its own header says so). The re-labelings are
therefore enumerated here and enforced by a test:

| Starter string (file:where) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`replay_broadcast.html:3795`) | `<span>Dispatcher</span><span>On time</span><span>Arrived</span><span>Late by</span><span>Deadlocks</span>` |
| `<span class="fl-cap">Lives left</span>` (endcard team block, line 3793) | `<span class="fl-cap">Trains on time</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (scrub graph, line 1576) | `<span class="momentum-label">ON TIME</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate, line 2241) | `<span class="ontime-label">On time</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (locker room, lines 1480 / 1833) | "Signing on at the control desk…" |
| `#clock-caption` "In the locker room" (line 1499) | "Booking on" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (line 1524) | "Replay hash mismatch at tick N — showing recorded orders" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline ahead of the playhead (o)" (line 1564) | "arrivals / breakdowns / deadlocks on the timeline ahead of the playhead (o)" |
| team words `RED`/`BLUE` in `ec-tname`/plates | the seat's **alias** (`ALPHA`…`DELTA`) plus its colour chip |

**`tests/test_flatland_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit`, `kill` — outside comment blocks, and asserts **zero**
matches; and asserts each replacement string above is present exactly once. A rename that reintroduces
paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (starter lines 4291-4318). **No overlay sits in the transport band**: the board is
laid out between the two bands and every addition here (the on-time leaderboard rail, the deadlock
alarm chip, the feed, the banners) is positioned inside the board region or in the top band. The
**endcard stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept)
so the scrubber stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `railBeat(tick, kind, slot, label)` — named so it can never shadow
`chrome_common.js`'s `markBeat` alias (the tandem 2026-08-23 hoisting trap) — appends
`<button class="beat-marker <kind> <colour>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.arrival`,
`.beat-marker.malfunction`, `.beat-marker.deadlock`, `.beat-marker.fallback`, `.beat-marker.end`. The
game block never calls `markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: 1 tick per animation frame at 30 fps** (speed chips `[0.5, 1, 2, 4, 8]`, default 1). A
496-tick episode therefore plays for **16.5 s**, which is what lets `viewer_smoke.mjs --soak 10`
observe real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The network**, drawn edge to edge: the baked ballast bed with the rail tile atlas laid over it,
   the eight station platforms labelled `A`–`H`, the six sidings labelled `S1`–`S6`, the nine junctions
   labelled `J1`–`J9`, and the trains as coloured chips with a heading chevron and a **speed pip**
   (1–4 dots). A train's chip is its owner's colour. A **held** train is dimmed with a small red signal
   dot ahead of it; a **malfunctioning** train flashes amber with a spanner glyph and a countdown ring;
   a train that is **late** carries a thin red underline. A section currently locked by the interlock
   is tinted in the direction of travel, so a spectator sees *why* the second train is waiting.
2. **On-time leaderboard** (the idea's ask) — a labelled rail in the **top** band, four rows, one per
   dispatcher, sorted by on-time count descending: alias, colour chip, real policy name, `on-time /
   arrived / of 6`, and a small "late by N" figure. It re-sorts live, so overtaking is visible. This is
   the spectator's scoreboard and it is the only place real policy names appear on the board side.
3. **Deadlock alarm** (the idea's ask) — while any deadlock is active, a **`DEADLOCK`** chip lights red
   in the top band with the train ids and the tick count, every train in the cycle gets a pulsing red
   ring, the contested cells get a red cross, and `#bannerlane` reads `DEADLOCK — T09 vs T21 AT J6,
   31 TICKS`. A jam (no cycle) is the lesser amber `JAM` chip with the same treatment in amber and no
   banner. On clear: `DEADLOCK BROKEN — T21 SIDED AT S4`. A deadlock still active at the end turns the
   endcard headline red.
4. **Clock** — `#clock` shows the big numeral `ON TIME 16` with `/ 15 par` beneath it; `#clock-time`
   shows `tick 240/496 · turn 15/31`; `#clock-caption` shows `arrived 19 · late 3 · broken 2 ·
   deadlock 0`.
5. **Scorebug plates** — four plates (two in `#plates-l`, two in `#plates-r`): the seat's **real policy
   name** (spectator side only), its in-game alias, its colour chip, its own on-time count as the
   numeral, and a `↯` glyph on any seat that has taken a fallback.
6. **Match feed** (`#killfeed`) — plain language, never internal notation: `T13 departs A for F`,
   `T13 arrives F — ON TIME (16 on time)`, `T09 arrives C — 22 LATE`, `T14 BREAKS DOWN at (19,9) — 14
   ticks`, `T14 repaired`, `GAMMA sides T13 into S3`, `BETA holds T09 at J4`, **`DEADLOCK — T09 · T21
   at J6`**, **`DEADLOCK BROKEN AFTER 31 TICKS`**,
   `Alpha: "T02 has the down main to J5, hold westbounds at J4"`, and
   `DELTA MISSED THE CALL — scripted orders (timeout)`. The radio lines and the order lines are where a
   spectator sees the LLM playing.
7. **On-time sparkline** — the starter's `#momentum` SVG retargeted to two cumulative series (arrivals,
   and on-time arrivals) with the **deadlock spans shaded red** and the jam spans shaded amber behind
   them, and the playhead marked. Filled from the load-time pre-scan, so it draws at full width on the
   first frame. A flat stretch under a red shade is the whole story of a bad episode in one glance.
8. **Endcard** — `16 OF 24 TRAINS ON TIME — PAR 15 MET`, the four-seat table under the re-mapped header
   (`Dispatcher | On time | Arrived | Late by | Deadlocks`), a network summary line (`29 breakdowns,
   7 jams, 1 deadlock, 104 ticks lost`), and `NETWORK SCORE 16245`. It stops at `var(--band)` and any
   seek dismisses it.
9. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
   40 consecutive ticks with no `depart`, `arrive`, `malfunction`, `jam` or `deadlock` event, from the
   pre-scan), spoilers switch, tick readout, speed chips, the scrubber with its five beat kinds, and
   `#mmwarn` on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no
solid-colour squares, no downloads.** The ballast bed is `data/arena_floor.png`, tiled and darkened
22 %, with the gravel shoulder textured from `client/art/walls/wall_h.jpg` — baked once at install by
pixie, exactly the way the starter bakes endzone paint. The **rail tile atlas** (14 tiles: two
straights, four curves, four three-way switches, the four-way junction, the flat crossing, the dead-end
stub, plus a platform tile and a siding tile) is baked at the same time from the same textures with the
palette in `data/pallete.png` — two steel rails, sleepers, and a check-rail on the curves — at three
sizes (10, 13, 20 px). Trains are **baked at load** by `rig_art.nim`'s compositor into locomotive chips:
four facings × four speed classes × three sizes × the four seat colours drawn from
`data/soldier_{red,blue,green,yellow}.png`'s palette entries, each with a lit headlamp, a body of length
proportional to its speed class, and its number set in `data/font.ttf` — 192 pre-baked chips, so drawing
24 trains a frame is 24 blits. Station letters, siding ids and junction ids are set in `data/font.ttf`
on the baked bed. The four `data/soldier_*_front.png` sprites are the dispatchers' avatars on the
scorebug plates. The loading screen is the starter's locker room (`client/art/lockerroom/bg.jpg` plus
the four colour webps) with the caption re-labelled. The deadlock ring, the contested-cell cross, the
interlock tint and the sparkline are procedural in the bed bake's palette.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (starter lines 4310-4312). The board's `BOARD_ASPECT` is `28/14 = 2.0`; in a 360 × 203 frame
`boxW / availH = 1.77 < 2.0`, so **width binds**: the board renders at 360 × 180, i.e. **12.8 px per
cell**, and the whole network is in frame — which is why `#viewpanel` is dropped. A train chip is 10 px
with a 3 px chevron; the interlock tint is a 2 px edge wash; station letters are 8 px. Four rules are
added and asserted by `tests/test_flatland_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `alias + name + on-time`; the colour chip shrinks to 6 px and
   the fallback glyph moves inline.
3. Under `.tiny`, **train numbers are not drawn on the chips** (colour + chevron + speed pip only) and
   the leaderboard rail drops the "late by" figure; both at `--hudscale`-derived sizes so nothing is
   drawn outside the canvas (`--strict-text-bounds` stays on).
4. Under `.tiny`, the deadlock chip is the word `DEADLOCK` plus its tick count only, and the banner
   truncates the train list to the first two ids plus `+N`.

---

## Packaging

- **Repo**: `Metta-AI/cogame-flatland`, **public at creation** (public is a certification prerequisite —
  `source-resolves` 404s on private). Slug `flatland`; **`game.name` is `flatland`** so the secret
  namespace `secret://coworld/flatland/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services/two
  images; this fork uses the one-image / two-entrypoints shape because the shared `docker_smoke.sh` and
  `policies.json` assume a single image (the knights-archers precedent):

  ```yaml
  services:
    flatland:
      image: coworld-flatland:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{FLATLAND_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:flatland src/flatland.nim` →
  `/bin/flatland`, and the same for `src/flatland_player.nim` → `/bin/flatland-player`. The runtime
  stage copies both binaries, `data/` (including `data/rail/`), `client/`, `*.json`.
  `CMD ["/bin/flatland"]`, runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with
  the asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/soldier_{red,blue,green,yellow}{,_front}.png`, `data/font.ttf`, `data/rail/*.rail`,
  `client/art/walls/*`, `client/art/lockerroom/*`, `flatland_replay.{js,wasm,data}`,
  `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`, `static_replay.js`,
  `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["flatland", "rail", "cooperative", "logistics", "deadlock"]`
    (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0); **`episode_timeout_minutes: 20` at the top
    level**, not under `game`.
  - `game.name = "flatland"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/flatland"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/flatland/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 4/4, `players` 4/4, `slots` 0/4 — the tandem 0.1.0 scar). `tokens` is described as
    runner-injected; **no `game_config` anywhere in this manifest contains a literal `tokens` array**
    (matriculate rejects "game_config must not include runner-managed tokens" — knights-archers 0.1.0),
    while `config_schema` keeps *requiring* it because the runner injects it. Properties: `tokens`,
    `players`, `slots`, `seed`, `networkPool` (enum `["mainline", "branchline"]`, default `"mainline"`),
    `trainsPerSeat` (integer 3–8, default 6), `maxTicks`, `turnTicks`, `parOnTime`, `slackTicks`,
    `minJourneyCells`, `departStagger`, `malfunctionRate`, `malfunctionMinDuration`,
    `malfunctionMaxDuration`, `jamTicks`, `deadlockTicks`, `quiesceTicks`, `attempt1Ms`, `retryMs`,
    `turnBudgetMs`, `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`,
    `minPlayers`, `fastMode`, `showPlayerLabels`, and `num_agents` (integer, `minimum: 4`,
    `maximum: 4`, default 4).
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` and
    `endRule: {"type":"string","enum":["allArrived","quiescent","tickCap","wallClock","fault"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-flatland/blob/main/docs/PROTOCOL.md"}` —
    objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"dispatching.md","title":"Dispatching and the network","content":{"type":"uri","value":".../docs/DISPATCHING.md"}},
    {"id":"porting.md","title":"Porting Flatland","content":{"type":"uri","value":".../docs/PORTING-FLATLAND.md"}}]}`.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must be
    at least `"1"`** (pistonball 0.1.1). Two entries, `timetable` and `yielder`, so **every declared
    player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 4` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "mainline", "name": "Main line (28x14, 4 dispatchers, 24 trains)",
     "description": "A double-track spine with single-track branches, eight stations and six passing sidings. Four dispatchers run six trains each - 24 trains, four speed classes, random breakdowns - over 496 ticks and 31 command turns. Everyone scores the same number: how many of the 24 arrive on time.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Gamma"}, {"name": "Delta"}],
                     "num_agents": 4, "minPlayers": 4,
                     "networkPool": "mainline", "trainsPerSeat": 6,
                     "maxTicks": 496, "turnTicks": 16, "parOnTime": 15, "slackTicks": 24,
                     "minJourneyCells": 12, "departStagger": 4,
                     "malfunctionRate": 300, "malfunctionMinDuration": 8, "malfunctionMaxDuration": 24,
                     "jamTicks": 12, "deadlockTicks": 24, "quiesceTicks": 120,
                     "attempt1Ms": 9000, "retryMs": 4000,
                     "turnBudgetMs": 14000, "turnSpacingMs": 12000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "branchline", "name": "Branch line, single track (28x14, 4 dispatchers, 16 trains)",
     "description": "The hard one: single track everywhere with only five passing loops, sixteen trains and a breakdown rate half again as high. Fewer trains, far less room - every meeting has to be planned two turns ahead or the section deadlocks for good.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Gamma"}, {"name": "Delta"}],
                     "num_agents": 4, "minPlayers": 4,
                     "networkPool": "branchline", "trainsPerSeat": 4,
                     "maxTicks": 496, "turnTicks": 16, "parOnTime": 9, "slackTicks": 24,
                     "minJourneyCells": 12, "departStagger": 4,
                     "malfunctionRate": 200, "malfunctionMinDuration": 8, "malfunctionMaxDuration": 24,
                     "jamTicks": 12, "deadlockTicks": 24, "quiesceTicks": 120,
                     "attempt1Ms": 9000, "retryMs": 4000,
                     "turnBudgetMs": 14000, "turnSpacingMs": 12000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 4` again, inside `certification.game_config`, and exactly
  four players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS
  == 4` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with **both** declared players
  seated:

  ```json
  "certification": {
    "players": [{"player_id": "yielder"}, {"player_id": "timetable"},
                {"player_id": "yielder"}, {"player_id": "timetable"}],
    "game_config": {"players": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Gamma"}, {"name": "Delta"}],
                    "num_agents": 4, "minPlayers": 4, "seed": 42,
                    "networkPool": "mainline", "trainsPerSeat": 6,
                    "maxTicks": 496, "turnTicks": 16, "parOnTime": 15, "slackTicks": 24,
                    "minJourneyCells": 12, "departStagger": 4,
                    "malfunctionRate": 300, "malfunctionMinDuration": 8, "malfunctionMaxDuration": 24,
                    "jamTicks": 12, "deadlockTicks": 24, "quiesceTicks": 120,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  496 ticks of scripted play is about a second of sim, but the replay is 496 ticks ⇒ **16.5 s of
  playback**, which the viewer soak needs. Seed 42 is asserted by `tests/test_flatland_engine.nim` to
  produce a fixture episode with `arrivedTotal > 0` and at least one `malfunction` event, so the smoke
  replay always exercises the breakdown path. The certify step in `coworld-release.yml` passes
  **`--timeout-seconds 300`** (the default 60 covers start + connect grace + play + linger —
  cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/flatland-player"`, following the
  starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"flatland-signalman","run":"/bin/flatland-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"signalman"}},
   {"name":"flatland-pathfinder","run":"/bin/flatland-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"pathfinder"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"flatland-timetable","run":"/bin/flatland-player",
    "env":{"PLAYER_SCRIPTED":"timetable","PLAYER_POLICY_LABEL":"timetable"}},
   {"name":"flatland-yielder","run":"/bin/flatland-player",
    "env":{"PLAYER_SCRIPTED":"yielder","PLAYER_POLICY_LABEL":"yielder"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `timetable` and `yielder`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the **game**
  pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `flatland`, `<IMAGE>` →
  `coworld-flatland`, `<SEATS>` → **`4`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server) and `--soak 10`
  added to the `viewer_smoke.mjs` invocation. `coworld-release.yml` and `coworld-submit.yml` are the
  templates, with `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh` and
  `tools/build_replay_viewer.sh` are committed **executable** (mode 100755) — CI asserts the bit and
  invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_flatland_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_flatland_sim.nim`)
1. `transition rule` — for every tile in the alphabet and every entry heading, the legal exit set is
   exactly "every end but the one entered"; `+` allows only straight-through; a one-end tile reverses;
   an entry heading with no matching end is impossible because the loader validates connectivity.
2. `left/right/forward mapping` — `MoveLeft` picks `(heading+3) mod 4`, `MoveRight` `(heading+1) mod 4`,
   `MoveForward` `heading`; an action naming an illegal exit is repaired in the documented order and
   counted in `actionsRepaired`; `DoNothing` behaves as `MoveForward` for a moving train and leaves a
   stopped train stopped.
3. `speed classes` — a train with `ticksPerCell = k` occupies each cell for exactly `k` ticks and covers
   `n` cells in `k·n` ticks on clear track, for `k ∈ {1,2,3,4}`.
4. `exclusive cells` — two trains never occupy one cell; a train whose target cell is occupied does not
   move and increments `blockedTicks`.
5. `no swaps, chains by handle` — two trains nose-to-nose across two cells never exchange cells; a queue
   of three advances in one tick when its leader has the lowest id, and over three ticks when the order
   is reversed.
6. `dead end` — a train entering a one-end tile reverses heading and steps back the way it came.
7. `segment interlock` — a train is refused entry to an edge holding an opposing train, is admitted to
   an edge holding a same-direction train, and is always admitted to an edge with a parallel partner
   when the partner is used for the other direction.
8. `malfunctions are a pure hash` — the `(train, tick) → duration` table for a seed is identical under
   two different order sequences; a malfunctioning train never moves, blocks its cell, cannot be
   repaired early, and emits `malfunction` then `repaired`.
9. `departures` — a waiting train is off the grid, occupies nothing, enters only at or after
   `earliestDeparture`, only when its platform cell is free, and never while its order is `hold`.
10. `arrival and removal` — a train reaching any platform cell of its target arrives, leaves the grid,
    frees the cell, and sets `onTime` iff `arrivalTick <= scheduledArrival`; reaching a platform of the
    *wrong* station does nothing.
11. `jam vs deadlock` — two trains stalled behind a broken train raise `jam` at exactly
    `stalledTicks == 12` and **never** raise `deadlock`; a constructed two-section cycle raises
    `deadlock` at exactly `stalledTicks == 24`, names both trains, and is still active at `maxTicks`
    (permanent); re-routing one member before it commits clears it and emits `deadlockclear`; a single
    train stalled alone is neither.
12. `scoring` — `scores[s] == 1000*fleetOnTime + 10*arrivedTotal + onTime[s]` for 500 randomised end
    states, always ≥ 0, `onTime[s] < 10` and `10*arrivedTotal < 1000` always (the lexicographic bound),
    all four `win[s]` equal, `winner` null.
13. `end conditions` — `allArrived`, `quiescent`, `tickCap`, a forced wall-clock stop and a forced fault
    each produce the right `endRule` and the right episode `reason`; a wholly deadlocked network still
    settles (`quiescent`) with the deadlock alarm recorded and `stranded > 0`.
14. `no floating point in the sim` — a source grep over
    `src/flatland/{sim,railmap,trains,deadlock,driver,baselines}.nim` finds no `float`, `/`, `sqrt` or
    float literal.
15. `tick budget` — 496 ticks of a full 24-train episode complete in < 2 s in a release build.

**Network and upstream fidelity**
16. `tests/test_flatland_railmap.nim` — for each of the six committed `.rail` files: the sha256 equals
    the pinned literal; the file parses; every end connects; every station has exactly three platform
    cells; every id in `labels` is on rail; the station-to-station reachability matrix is complete in
    the directed `(cell, heading)` graph; the node/edge decomposition round-trips (every non-node rail
    cell belongs to exactly one edge); `mainline` maps have at least four double-track pairs and
    `branchline` maps exactly five passing loops.
17. `tests/test_flatland_upstream.nim` — the shipped constants in `src/flatland/upstream.nim` equal the
    table at the head of this note: the five action values, the four direction values, the dead-end
    reversal, by-handle move order, cell exclusivity, `remove_agents_at_target`, and
    `maxTicks == 8*(W+H+20) == 496` for a 28 × 14 board. A constant edited without editing the citation
    fails the test.
18. `tests/test_flatland_seeding.nim` — the network is `pool[seed mod 3]`; start platforms are distinct;
    every target differs from its start and has `routeCells >= 12`; the speed multiset is exactly
    `{1,2,3,4}` × `trainCount/4`; `earliestDeparture` is `4 × rank`; and **none** of these change when
    seat behaviour changes (the anti-collusion pin).
19. `tests/test_flatland_determinism.nim` — re-simulate from the replay's seed and order records alone
    on a fresh sim; identical final tick, arrivals, on-time count and per-tick `gameHash`.

**Bounded orders / legality on the scripted baselines** (`tests/test_flatland_driver.nim`)
20. `baselines are bounded` — for 200 pseudo-random world states (varying departures, malfunctions, jam
    and deadlock states, both networks, every slot) and for **both** `timetable` and `yielder`: the
    returned reply has at most `trainsPerSeat` orders, every `train` is one of that seat's un-arrived
    trains and appears at most once, every `verb` is in the enum, every `at` is a real siding id, every
    `via` is a real node id, `say` and `notes` are empty, and the serialised directive is ≤ 1024 bytes.
    A baseline that ever proposes an illegal or unbounded order fails the build.
21. `driver never emits an illegal action` — over the same states, every emitted action is in
    `{DoNothing, MoveLeft, MoveForward, MoveRight, Stop}`, every committed move uses a legal transition
    for the train's heading, and no order can leave a running train with no action.
22. `fallback is the yielder proc` — the decision engine's fallback path and the `yielder` baseline
    resolve to the same proc, so they cannot drift.
23. `reply validation` — the validator accepts the schema, **repairs** an invalid order to that train's
    previous order, drops orders for trains the seat does not own and for arrived trains, accepts a
    `say`-only reply, rejects a non-object, truncates `say`/`notes` on **rune** boundaries at 120/240
    with 4-byte emoji sitting on the boundary, caps the read at 4096 bytes, caps `orders` at
    `trainsPerSeat`, and never leaves a train without an order.
24. `baseline tuning is the swept pick` — the shipped `yieldAfter`/`departLookahead`/`sidingLookahead`
    equal `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the
    sweep with `--check`).

**End-to-end episode writing a replay** (`tests/test_flatland_engine.nim`)
25. `episode writes artifacts` — run a real four-seat episode (`mainline`, `maxTicks 200`, all seats
    scripted, no API key so the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert
    `results.json` and the `.replay` are written, `reason == "complete"`, `arrivedTotal > 0`, `scores`
    agree with the formula, and the results key set equals the manifest's `results_schema` key set
    **exactly**.
26. `the cert seed is interesting` — seed 42 on `mainline` yields `arrivedTotal > 0` and at least one
    `malfunction` event within 200 ticks, so the CI smoke replay always exercises the breakdown path.
27. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure payload.
28. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete`, not `deadline`, and the matching record names the turn.

**Replay** (`tests/test_flatland_replay.nim`)
29. `record then re-derive, every end reason` — for `allArrived`, `quiescent`, `tickCap`, `wallClock`
    **and** `fault`, record an episode and re-derive it from the bytes; assert identical hashes at every
    tick **including the stop tick** (the particle-worlds scar).
30. `replay is self-sufficient` — the bytes alone yield seat names, aliases, policy kinds, the full
    config, the seed, the network name, every order record, every chat record and the result.
31. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports `protocol == "flatland/v1"`.
32. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_flatland_manifest.nim`)
33. `manifest pins` — `num_agents == 4` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; `len(player) == 2` and every declared player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 4`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 660`; **and every variant's
    `game_config` actually constructs a valid `GameConfig`, loads its network pool, and produces the
    train count, speed multiset and `parOnTime` this note claims** (the collab-cooking 0.1.1 scar: test
    every variant, not just the fixture).
34. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_flatland_viewer.nim`, static assertions in the `test` job)
35. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals the starter's, pinned
    as a literal.
36. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it; `broadcast_core.js`'s kept procs are
    byte-identical to the starter's, `pushFeed`'s signature included.
37. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `railBeat`, never
    `markBeat`.
38. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{arrival, malfunction, deadlock, fallback, end}`.
39. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the four 360 px rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#fpv*`,
    `#povBadge`, …) appear nowhere.
40. `endcard labels` — `tests/test_flatland_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
41. `label manifest` — the starter's `test_label_contract` pattern: the emitted sprite-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
42. `events are the closed enum` — `tests/test_flatland_events.nim`: the set of kinds `stepEvents` can
    emit equals exactly the thirteen listed in §Server, and every kind used by the appended game block
    is in that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**
43. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded
    as the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm
    module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
44. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the feed's radio text path (the cogchemists 2026-08-24 scar). The
    fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only the
    wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) — driving
    the real page with a full-cap 120-rune `say` on all four seats, a fully populated on-time
    leaderboard, an active deadlock alarm with a four-train cycle, and two malfunctioning trains, at
    several canvas widths including 360 px.
45. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **Hundreds of trains, and seat counts other than 4.** The idea's 10–200 range is answered at 24
  trains (`mainline`) and 16 (`branchline`), with **`num_agents` fixed at 4** in every variant and in
  the cert fixture. More trains is a bigger board and a legibility pass at 360 px, not a rules change;
  more seats is a wall-clock problem (§The game → seats), not a design one.
- **One seat per train.** The idea offers "one cog per train, or one policy per fleet"; v1 ships the
  fleet form, for the batch-size reason given in §The game. A one-train-per-seat variant would need a
  different decision cadence and a different manifest and is not shipped.
- **A procedural rail generator.** Networks are three committed `.rail` files per pool, chosen by seed.
  Porting upstream's `sparse_rail_generator` would reintroduce numpy RNG ordering, degenerate layouts
  and a topology nobody can pin a sha256 on.
- **Reversing / backing up.** Trains cannot reverse except at a dead end (upstream-faithful). That is
  precisely what makes a deadlock terminal and the yielding conventions worth having. Adding a reverse
  action would be a different game.
- **Scoring lateness.** `latenessTicks` is measured, recorded in `results`, shown on the endcard and in
  the leaderboard, and deliberately **not** in `scores` (§The game). Weighting it would need a
  magnitude the idea does not pin and would risk inverting the lexicographic ordering.
- **Upstream's observation builders and RL interface.** No seat receives `TreeObsForRailEnv`,
  `GlobalObsForRailEnv` or `LocalObsForRailEnv`, no predictor is exposed, no `msg_bits`-style channel
  exists (the radio replaces it), and no pretrained NeurIPS-2020 solution is vendored or run. Orders are
  the interface.
- **Infrastructure malfunctions, variable-speed-during-episode trains, station dwell times, train
  length (multi-cell trains), and passenger connections.** None of them are in the upstream rules this
  note reproduces and none are invented here.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, fog-of-war rendering, the
  first-person PIP, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches, perks,
  handicaps, lives, teams, four-team play, shouts, achievements, campaign mode, multi-game episodes, the
  procedural map generator, the map pool, the map editor and mapkit — all deleted, not disabled
  (§Sim module), and none of them return in v1.
