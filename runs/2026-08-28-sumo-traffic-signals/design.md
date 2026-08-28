# cogame-sumo-traffic-signals — design note (2026-08-28)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` importing and re-exporting the sim
modules, `sim_types.nim` owning `GameVersion` — `"44"` in the starter, restarting at `"1"` here — with
its prepend-only changelog-comment discipline, `TargetFps* = 24` (`sim_types.nim:376`), the flatty wire
types whose field order is sacred, and the rune caps `MaxNoteRunes`/`MaxSayRunes`/`MaxPromptRunes`
(`sim_types.nim:794-799`)); the mummy HTTP/websocket server implementing the Coworld contract; the
`decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` / `control.nim` commander layer with its
one-parallel-batch-per-turn shape (`decide.nim:427` `curl.makeRequests`), its `attempt1Ms` / `retryMs` /
`turnBudgetMs` / `turnSpacingMs` deadlines, its budget guard (`decide.nim:335-346`), its tolerant JSON
extraction, rune truncation (`directives.nim:61-90`) and fallback ladder; the binary `COWLDCTF` replay
of *inputs plus a per-tick `gameHash`* (`replays.nim:142`), re-simulated by **the same sim module**
compiled to wasm by `replay-viewer/config.nims`; the `client/` broadcast chrome (`chrome_common.js` +
`broadcast_core.js` + `replay_broadcast.html` with its `window.PaintballChrome.install(PB_CTX)` splice
hook at `replay_broadcast.html:4337`); nimby + `Dockerfile` + `Dockerfile.replay-viewer` +
`tools/build_replay_viewer.sh`; and the Nim test suite with its four shards (`tests/shard_1..4.nim`,
`tests/config.nims`).

Starter choice, one line: **this is a real-time tick loop whose rules are written into this repo and
whose seats are LLM dispatchers over a deterministic per-tick driver — the first row of the starter
table** (`prompts/10-design.md` §Starter table: "any real-time game loop (grid OR continuous physics),
new rules written for this coworld"). It is deliberately **not** the `cogame-moba` row, and that is a
**rail the coordinator already set and this note does not revisit**: this coworld does **not** embed or
port SUMO or CityFlow. SUMO is a C++ desktop simulator with XML networks, its own RNG and its own
car-following model; a bit-exact port is neither achievable nor compilable into the wasm replay this
platform requires. What this repo implements is the *control problem* the SUMO-RL / RESCO benchmarks
pose — per-seat intersection signal control, queue and waiting-time pressure, cooperative
network-throughput scoring, green waves as an emergent phenomenon — on its own deterministic, seeded,
integer, cell-based vehicle simulation written for this coworld. Every divergence from the source
benchmarks is named in §Sim module → "Documented divergences from the source benchmarks" and mirrored
into `docs/PORTING-SUMO-RL.md`. The precedent for forking paintbot for a grid game is nine deep
(knights-archers, pistonball, atari-cabinet, walker-waterworld, particle-worlds, smac-starcraft-micro,
magent-battle, rware-warehouse, flatland).

Where this note departs from coworld-ctf it says so. The departures are: the rules are traffic-signal
rules, not paintbot's (§Sim module lists what is deleted); the board is a small integer **cell grid**
with a static, code-authored road topology, so ctf's pixel arena, procedural map generator, map pool,
map editor and mapkit are deleted; the game is **fully cooperative** (one shared throughput number, no
teams); a seat commands **four intersections**, not one body; and `MaxSayRunes` / `MaxNoteRunes` are
re-pinned (§Decisions → reply schema).

### Source idea (verbatim)

> SUMO Traffic Signals — each intersection is a cog, the city is the reward, and your green is your neighbour's queue
>
> Port of SUMO-RL (Alegre) / CityFlow multi-agent traffic signal control. Each seat controls one intersection's signal phases; vehicles are simulated by SUMO on a real or grid road network; reward per intersection = −queue/−waiting time, with the global score being network throughput. Local greed (flush my queue) exports congestion downstream — coordination emerges as green waves. Networks: 4×4 grid, Cologne, Ingolstadt, Manhattan.
>
> Seats: 4-48 intersections
> Motive: cooperative with local-vs-global tension
> Policy interface: phase choice every 5-10 s — a slow cadence that suits LLM policies well
> Fills gap: 08 Gridlock is competing delivery fleets on the same roads; this is the *infrastructure* side — the signals cooperating — and could share a city with it
> Integrity (anti-collusion): cooperative cross-play scoring; demand seeded.
>
> Replay plan (watchability): SUMO-GUI top-down; queue-length heatmap; green-wave visualisation.
>
> Source: github.com/LucasAlegre/sumo-rl; CityFlow; RESCO benchmark.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time tick loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-sumo-traffic-signals` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=greedy\|fixedcycle`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art + install-time bakes) |
| Two name spaces | §The game (aliases `Alpha`/`Beta`/`Gamma`/`Delta` in-game; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 420 s, worst 569 s, engine stop 660 s, budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 4`, three times |
| Simultaneous decisions as one parallel batch | §Decisions (all four seats in one `curl.makeRequests` batch per turn) |
| Replay bytes self-sufficient | §Server (config JSON, joins, orders, chats, per-tick hashes, seed, variant) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Demand seeded and unsteerable (the idea's integrity note) | §Sim module (arrivals are a pure hash of `(seed, gate, tick)`, never a consumed stream) |

---

## The game

Sixteen signalised intersections on a 4 × 4 city grid. Cars enter from sixteen gates on the edges,
follow a fixed shortest route to their destination gate, and queue in single-lane approaches. **Four
signal controllers** each own one quadrant of four intersections. Every eight simulated seconds each
controller decides what its four signals do next: hold the current phase, switch to a named phase,
switch **after a delay** (which is how you build a green wave), or delegate to a greedy per-tick
actuator. The only number the league reads is **how many cars got all the way through the city**; the
number that separates near-equal networks is how long everybody waited. A controller that flushes its
own queues on every green sends platoons into a link that is already full, and a full link means the
car at the neighbour's stop line **cannot move even on green** — that is the whole game: your green is
your neighbour's queue. There is no central plan; the only channel between controllers is a
120-character radio call.

### Seats, quadrants, aliases

- **`num_agents` = 4.** Exactly four seats, always — in both manifest variants and in the certification
  fixture. **Each seat is a controller owning four intersections** (one quadrant). The reasoning,
  stated once:
  - Every seat is an **LLM policy**, and all seats' calls go out as **one parallel batch per turn**
    (§Decisions). Four calls per turn is one batch of four; at the starter's `turnSpacingMs` floor that
    is 20 requests/minute against the sidecar's 30/minute per-episode cap. One seat per intersection
    would be 16 seats — 80 req/min, nearly three times the cap, and a per-turn batch that cannot finish
    inside the wall clock. **The seat count is set by the wall clock, not by taste.**
  - Four seats is also the number that seats **both LLM champions and both scripted fillers in a single
    episode**, which makes the idea's "cooperative cross-play scoring" true by construction rather than
    by luck.
  - The idea's "4–48 intersections" is answered at **16 intersections**, inside the range, and sized so
    the whole city is legible at 360 px (§Viewer). Other intersection counts and other seat counts are
    §Out of scope.
  - "Each intersection is a cog" survives as **one order per intersection per turn**: a seat issues up
    to four independent orders, one per signal, and the observation is per-intersection. What it does
    not do is give each intersection its own network socket.
- **Two name spaces.** In-game the seats are **`Alpha`, `Beta`, `Gamma`, `Delta`** — the starter's
  `IdentityNames` (`src/ctf/roster.nim:64`), title-cased for display by `seatAlias(slot)`. Those aliases
  are the only names that appear in an observation, a prompt, an order, a `say`, a radio line or a board
  label. The seats' **real policy/player names** (`daveey`, `daveey-1`, `Baseline (1)`, `Baseline (2)`)
  live only in `results.names`, in the replay's join records, and spectator-side in the viewer's
  scorebug plates, pressure rail and endcard. `showPlayerLabels` is **false**, as in the starter's
  paintball variant, so nothing drawn on the board can leak an identity. A seat can never learn who it
  is controlling alongside — the idea's anti-collusion requirement.
- **Quadrants, by slot** (fixed, never randomised, so a replay is readable):

  | Slot | Alias | Colour | Quadrant | Intersections |
  |---|---|---|---|---|
  | 0 | Alpha | red | NW | `A1 A2 B1 B2` |
  | 1 | Beta | blue | NE | `A3 A4 B3 B4` |
  | 2 | Gamma | green | SW | `C1 C2 D1 D2` |
  | 3 | Delta | yellow | SE | `C3 C4 D3 D4` |

  Quadrants, not corridors, on purpose: **every one of the eight arterials is jointly owned** (row `B`
  is Alpha's `B1 B2` then Beta's `B3 B4`; column `2` is Alpha's `A2 B2` then Gamma's `C2 D2`), so a
  green wave along any arterial requires two controllers to agree on an offset over the radio, and
  every seat has two internal boundaries it can solve alone and two external ones it cannot. The board
  is symmetric under 180° rotation and the demand is uniform per gate, so all four quadrants are
  statistically equivalent — which is what makes the per-seat tie-break term in §Scoring comparable
  across seats.

### The city

The topology is **authored in code**, identical in every episode, and built by
`src/signals/city.nim` at load — not generated, not loaded from a file (a code-authored fixed graph is
what lets the wasm viewer reconstruct the city from the replay's variant name alone).

- **Intersections** are named `<row><col>`: rows `A` (north) … `D` (south), columns `1` (west) … `4`
  (east). `A1` is the north-west corner. Intersection index (used by every "ascending index" tie-break
  in this note) is `rowIndex * 4 + colIndex`, so `A1 = 0` … `D4 = 15`.
- **Approaches** are named by the direction traffic arrives **from**: `N`, `E`, `S`, `W`. Every
  intersection has exactly four approaches and four exits. Interior neighbours are the adjacent
  intersections; edge approaches/exits are **gates**.
- **Gates**, 16 of them, each simultaneously a source and a sink, named `<side><intersection>`:
  `nA1 nA2 nA3 nA4` (north side), `sD1 sD2 sD3 sD4` (south), `wA1 wB1 wC1 wD1` (west),
  `eA4 eB4 eC4 eD4` (east).
- **Links** are one-way, single-lane, and made of **cells**. A cell holds at most one car. Link ids are
  `<from>><to>`, e.g. `C2>C3`, `nA1>A1`, `A1>nA1`. Lengths:

  | Link | Cells |
  |---|---|
  | east–west between two intersections (`ewLinkCells`) | **6** |
  | north–south between two intersections (`nsLinkCells`) | **4** |
  | east/west gate link, either direction (`ewGateCells`) | **4** |
  | north/south gate link, either direction (`nsGateCells`) | **3** |

  80 directed links, 352 cells in all. East–west blocks are longer than north–south blocks on purpose:
  the avenues are the green-wave corridors and the cross streets spill back fast.
- **Gate queues.** Each of the 16 entry gates has a holding queue of capacity `gateQueueCap = 12` in
  front of its entry link. A car generated when that queue is full is **rejected** — permanently lost
  demand, counted in `results.rejected`, never scored.
- **Board size in cells** (this is the drawing surface, and the arithmetic the viewer's layout uses):
  an intersection box is 2 × 2 cells; each street carries its two directions as two adjacent lanes.
  Width `= 4 + 2 + 6 + 2 + 6 + 2 + 6 + 2 + 4 = 34`; height `= 3 + 2 + 4 + 2 + 4 + 2 + 4 + 2 + 3 = 26`.
  **34 × 26 cells, aspect 1.308.**
- **Cars.** A car occupies one cell of one link (or a slot in a gate queue). Free-flow speed is
  **one cell per tick**. `MaxVehicles = 1024` fixed slots; a car's slot is freed when it exits.

### The clock

- **Tick** = one simulated **second**. **`maxTicks = 256`.**
- **Command turn** = one order round, every **`turnTicks = 8`** ticks (the idea's "phase choice every
  5–10 s"), beginning with turn 1 at tick 0 before any stepping. **32 command turns per episode.** One
  game per episode (`maxGames = 1`): a cooperative game has no side to swap.
- Between turns the loop runs **uncapped** (`fastMode: true`), so all 256 ticks cost well under a
  second of CPU; the wall clock of an episode is the 32 LLM turns (§Decisions).
- **Demand runs to tick `demandEndTick = 208`**, then stops: the last 48 ticks are the clear-down, and
  a network that clears them all ends the episode early (§End conditions). Clearing the city is a
  visible, scoreable achievement.

### Signal phases

Four phases, fixed for every intersection, indices as given:

| Index | Id | Green approaches | Permitted movements |
|---|---|---|---|
| 0 | `NSG` | `N`, `S` | `through`, `right` |
| 1 | `NSL` | `N`, `S` | `left` |
| 2 | `EWG` | `E`, `W` | `through`, `right` |
| 3 | `EWL` | `E`, `W` | `left` |

Plus the non-selectable state `CLR` — the all-red clearance, `clearTicks = 2` ticks on **every** phase
change, during which no approach discharges. `minGreenTicks = 4`: a phase must have been current for
four ticks before a change executes; a change requested earlier is **deferred**, not dropped.
Approaches are single-lane, so a car whose movement the current phase forbids **blocks every car behind
it** — a left-turner at the head of the `E` approach under `EWG` stops the whole avenue. That is the
mechanic that makes phase choice, not just phase length, matter. `maxRedTicks = 60` is the safety
valve: a stop-line car whose movement has been forbidden for 60 consecutive ticks forces the phase that
serves it (§Resolution order, step 2d).

A car's movement class at an intersection is derived from its route: the next link's direction versus
its approach direction — same heading is `through`, 90° left is `left`, 90° right is `right`. U-turns do
not exist; the route builder asserts no route ever requires one.

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (at tick `8·(T−1)`), in this order:

1. The engine snapshots the world and builds all four seats' observation objects (§Decisions).
2. All four seats' LLM requests go out as **one parallel batch** (`curl.makeRequests`, the starter's
   `decideAll` shape), attempt-1 deadline `attempt1Ms = 9000`. Scripted seats compute locally,
   instantly, and consume no request.
3. Each seat that timed out, errored, returned non-JSON, or returned no usable `orders` array is retried
   **once**, again as a single batch, `retryMs = 4000`.
4. A seat still without a usable reply gets the **`greedy`** scripted orders computed server-side, and a
   `fallback` record is written (§Decisions).
5. Orders are applied, in ascending slot, then in ascending intersection index within a slot. An
   intersection named in the reply takes the new order; an intersection **not** named keeps the order it
   had (turn 1's default is `auto`); an order whose fields do not validate is **repaired to that
   intersection's previous order** — never dropped into "no order" — and counted in `ordersRejected`
   (the starter's `directives.nim` repair-don't-reject discipline). Orders naming an intersection the
   seat does not own are dropped and counted.
6. `say` (≤ 120 runes) and the accepted orders become replay chat records. `say` is the control-room
   radio: **every** seat hears **every** seat's last-turn `say` in its next observation. `notes`
   (≤ 240 runes) is private and echoed back to that seat only.
7. `turnSpacingMs = 12000` is a floor on the wall clock between consecutive **batch starts** (the
   starter's mechanism in `decide.nim:386-389`, kept), which is what keeps four seats under the
   sidecar's 30 req/min per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the game
and nothing else mutates the world**:

1. `tick += 1`. Snapshot cell occupancy (cell → car id, or none). Every rule below reads the snapshot
   for *reading* and writes through it as cars commit, in the order given.
2. **Signal machine**, for each intersection in ascending index:
   - **a.** `ticksInPhase += 1`. Ask the driver for this tick's **requested phase** from the
     intersection's current order (§Decisions → The driver).
   - **b.** If `clearLeft > 0` (in clearance): `clearLeft -= 1`; when it reaches 0 the requested phase
     becomes current, `ticksInPhase = 0`, `phaseChanges[owner] += 1`, and a `phasechange` event is
     emitted. No approach discharges this tick.
   - **c.** Else if the requested phase differs from the current phase and `ticksInPhase >=
     minGreenTicks`: enter clearance (`clearLeft = clearTicks`). No approach discharges this tick.
   - **d.** Else if the requested phase differs but `ticksInPhase < minGreenTicks`: the request is
     **deferred** — kept and retried next tick — and `deferredSwitches += 1`.
   - **e.** **Starvation override.** If any approach's stop-line car has `blockedByPhaseTicks >=
     maxRedTicks`, the requested phase is overridden to the phase permitting that car's movement (ties
     broken by lowest approach index in the fixed order `N, E, S, W`), a `starve` event is emitted,
     `starvations += 1`, and the override is latched for `minGreenTicks` ticks after it takes effect,
     after which the seat's own order resumes. The override is physics, not a penalty; the seat sees it
     next turn as `last_order_result: "overridden"`.
3. **Discharge at stop lines.** For each intersection in ascending index, for each approach in the fixed
   order `N, E, S, W`: if the intersection is **not** in clearance, the approach's stop-line cell holds a
   car, and the current phase permits that car's movement, then:
   - if the **entry cell (cell 0) of the receiving link** is free (an exit link's entry cell is always
     free — see step 5), the car moves to it; `crossings += 1`; `cleanCrossings` becomes
     `cleanCrossings + 1` if the car accrued **zero** wait ticks since its previous crossing, else `1`;
     `waitSinceLastCrossing = 0`; if `cleanCrossings` reaches `waveCrossings = 3` for the first time the
     car is credited as **progressed** for its corridor (step 11);
   - else the move is refused: `spillbackBlockedTicks += 1` for the car and the receiving link is marked
     as blocking.
   A car whose movement the phase forbids does not move and takes `blockedByPhaseTicks += 1`.
   **At most one car per approach per tick** (single lane, saturation flow 1 car/s/lane), and since a
   phase greens two approaches, **at most two cars cross an intersection per tick**.
4. **Link advance.** For each link in ascending link index, for `i` from `L−2` down to `0`: the car in
   cell `i` advances to cell `i+1` if cell `i+1` is free. Downstream-first iteration gives free-flow
   speed of exactly one cell per tick and lets a whole queue step forward in one tick once its head has
   discharged (no start-up lost time — a documented simplification, §Sim module).
5. **Exits.** For each **exit** link (a link whose head is a gate), in ascending index: the car in cell
   `L−1` leaves the network. `throughput += 1`, `served[ownerOfUpstreamIntersection] += 1`,
   `travelTicksTotal += tick − spawnTick`, `stopsTotal += stops`, an `exit` event is emitted, the slot is
   freed. Because this runs every tick, an exit link's last cell is always vacated, so **exit links never
   spill back** and a sink never becomes the bottleneck.
6. **Gate entries.** For each entry gate in ascending index: if its queue is non-empty and cell 0 of its
   entry link is free, the head car enters cell 0.
7. **Demand generation** (a pure hash — nothing above can influence it). For each entry gate `g` in
   ascending index, if `tick < demandEndTick`: `h = mix64(seed, g, tick)`; if `(h mod 1000) <
   permilleAt(tick)` a car is generated. `demandGenerated += 1`. Its destination gate is: the gate
   **opposite** `g` if `((h shr 10) mod 1000) < throughRunnerPermille`, else gate index
   `(h shr 24) mod 16`, and if that equals `g`, the opposite gate. Its route is looked up in the
   precomputed all-pairs table (§Sim module). The car joins `g`'s queue if `queue.len < gateQueueCap`,
   else `rejected += 1` and the car never exists. `permilleAt(tick)` is
   `demandWarmPermille` for `tick < demandPeakStart`, `demandPeakPermille` for
   `tick < demandPeakEnd`, `demandDeclinePermille` for `tick < demandEndTick`, else 0.
8. **Wait accounting.** For every car still on the network (link cell or gate queue) that did **not**
   change cell this tick: `waitTicks += 1`, `waitSinceLastCrossing += 1`, `networkWaitTicks += 1`, and
   `seatWaitTicks[s] += 1` where `s` owns the intersection at the **downstream end** of the link or the
   intersection the gate queue feeds — i.e. every waiting car is charged to the signal that is keeping
   it waiting. If the car moved on the previous tick and not on this one, `stops += 1`.
9. **Queue and spillback measurement.** For each link: `queueLen` = the number of consecutive stopped
   cars counted back from the stop line; `full` = every cell occupied. A link that becomes full emits
   `spillback {link, at, slot, t}` and `spillbacks += 1`; a full link that drops below full emits
   `spillclear {link, ticks}`; `spillbackTicks` counts every tick at least one link is full. A gate
   queue that reaches `gateQueueCap` emits `gatejam {gate, at, slot, t}`, and `gateclear` when it
   empties.
10. **Gridlock ring detection** (`src/signals/flow.nim`). Build the directed **blocked-by** graph over
    links: `L → M` when `L`'s stop-line car's next link is `M` and `M`'s entry cell is occupied. A
    **gridlock ring** is a directed cycle in that graph in which every link is full **and** has been
    full for `ringTicks = 20` consecutive ticks. Entering one emits `gridlock {links, ats, t}` and
    increments `gridlocks`; leaving emits `gridlockclear {links, ticks}`; `gridlockTicks` counts every
    tick at least one ring is active and `longestGridlockTicks` its longest run. The search is a DFS
    from the lowest link index, visiting successors in ascending link index, returning the first cycle
    found — pinned for determinism. A ring is re-evaluated every tick, never latched: it breaks the
    moment one of its links discharges, which is exactly the skill the game rewards.
11. **Green-wave detection.** Every "progressed" credit from step 3 is filed under its car's **corridor**
    — the row letter for an east/west-travelling car, the column digit for a north/south one — with the
    tick. When a corridor's credits inside the trailing `waveWindow = 16` ticks reach
    `waveVehicles = 4`, a `wave {corridor, dir, ats, vehicles, t}` event is emitted, `greenWaves += 1`,
    and that corridor's window is cleared, so one wave is one event.
12. Mix the tick into `gameHash` and append it to the replay's hash chain.
13. Evaluate the end conditions.

**Collisions cannot occur.** One car per cell and one discharge per approach per tick turn every
would-be conflict into a wait. `results` carries no `collisions` key and the viewer draws no crash; the
failure modes this game shows are **spillback** and the **gridlock ring**, exactly as the idea frames
it.

### Scoring formula and sign

At the end of the episode:

```
throughput      = cars that reached their destination gate                (0 .. demandGenerated)
networkWaitTicks= sum over all cars of ticks spent stopped anywhere       (0 .. 139_264)
seatWaitTicks[s]= the part of that charged to seat s's four intersections (step 8)

netWaitK        = min(999, networkWaitTicks  div 200)      # 0 .. 696 attainable
seatWaitK[s]    = min( 99, seatWaitTicks[s]  div 800)      # 0 ..  71 attainable

scores[s]       = 1_000_000 * throughput
                -     1_000 * netWaitK
                -        10 * seatWaitK[s]
```

**Sign: higher is better, and both waiting terms only ever subtract** — the idea's "reward per
intersection = −queue/−waiting time" is the negative sign on the two wait terms; "the global score being
network throughput" is the term that dominates. `scores[s]` is negative only in the degenerate case
`throughput == 0`.

**The ordering is strictly lexicographic, by construction:**

- one extra car through is worth `1_000_000`, and the largest possible total penalty is
  `1_000 × 999 + 10 × 99 = 999_990 < 1_000_000` — **throughput first, always**;
- one unit of network waiting (200 wait-ticks) is worth `1_000`, and the largest possible seat penalty is
  `10 × 99 = 990 < 1_000` — **network waiting second**;
- own-quadrant waiting is the last tie-break, worth `10` a unit.

The caps exist so the lexicography cannot invert even in a pathological episode, and the divisors are
chosen so the caps are never actually reached: `networkWaitTicks ≤ (352 link cells + 16 × 12 gate-queue
slots) × 256 = 139_264`, so `netWaitK ≤ 696 < 999`; a seat's charged cells are at most 224, so
`seatWaitTicks[s] ≤ 57_344` and `seatWaitK[s] ≤ 71 < 99`.
`tests/test_signals_scoring.nim` asserts both bounds analytically and over 500 randomised end states.

The first two terms are **identical for all four seats**: pure common interest, the idea's "cooperative"
motive. The third is the local `−queue/−waiting` signal, and it is deliberately an epsilon — a
controller that flushes its own queues to shave its own `seatWaitK` (worth at most 710 points) at the
cost of one car not getting through (worth 1 000 000) loses by three orders of magnitude. **The local
temptation is therefore in the *dynamics*, not in the arithmetic**: greedy local flushing genuinely
raises local throughput for a few turns before the downstream link fills, and the punishment arrives
later and network-wide. That is the tension the idea asks for, and it is a real one because the sim
makes spillback physical (tick step 3) rather than a scoring penalty.

**The league ranks by `results.scores[s]`** (the platform's Elo, 1000 start / K 32, is computed from
these per-episode per-seat numbers). `results.win[s]` is `throughput >= parThroughput` — the same
boolean for all four seats, a "did the city work" flag, not a duel — and `results.winner` is always
`null`, because a cooperative episode has no winner. `parThroughput` is a config field (**260** in
`grid4x4`, **380** in `rushhour`).

**Measured but never scored:** `rejected`, `travelTicksTotal`, `stopsTotal`, `greenWaves`, `spillbacks`,
`gridlocks`, `starvations`, `deferredSwitches`, `phaseChanges`. All are in `results`, on the endcard and
in the feed. Green waves in particular are a *means*, not a currency: paying for waves directly would
let a seat farm the metric on an empty corridor. §Out of scope records the decision.

**Cross-play (the idea's integrity note).** Scoring is cross-play, not self-copies: the certification
fixture seats **two `greedy` and two `fixedcycle`** controllers, and the league division runs **two
scripted fillers alongside the two prompt champions** (§Packaging), so a four-seat round robin seats each
champion with unfamiliar partners in essentially every episode. The game records what it was given:
`results.policyKinds = ["llm","llm","scripted","scripted"]` and `results.crossPlay = true` when at least
one LLM seat and at least one scripted seat sat together. And **demand is unsteerable**: whether gate
`g` produces a car at tick `t`, and where that car is going, is the pure hash `mix64(seed, g, tick)` —
not a consumed RNG stream, so no ordering of decisions by any seat can shift, reorder or consume another
seat's arrivals (§Sim module).

### End conditions and legal `results.reason` values

The episode ends at the first of: **cleared**, **gridlock stall**, the **tick cap**, or the **wall-clock
stop**.

- **Cleared** — `tick >= demandEndTick` **and** no car anywhere (every gate queue empty, every link
  empty). The city ran the whole peak and emptied. Settles immediately.
- **Gridlock stall** — `gridlockStallTicks = 40` consecutive ticks in which **no car exited and no car
  changed cell**. The city is dead; playing out the remaining ticks would add nothing but a frozen
  replay. Settles immediately, with the gridlock alarm lit.
- **Tick cap** — `tick == maxTicks` (256).
- **Wall-clock stop** — the engine's `wallClockBudgetSeconds` guard
  (`src/ctf/server.nim:1407-1417`, kept).

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the episode finished on its own terms: cleared, gridlock-stalled, or the tick cap.
  The healthy value. `results.endRule` says which: `cleared` | `gridlock` | `fullPeriod`.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine stops
  at the current tick, settles with the **real** throughput so far (never zeroed, so a deadline episode
  is still rankable), writes `results.json` and the replay, and exits 0.
  `results.endRule = "wallClock"`. **Declared acceptable** for SPEC §Definition of done check 4. The
  budget guard below exists so it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from the
  last completed tick, `results.endRule = "fault"`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0. A defect: `tools/ci/docker_smoke.sh` fails the
  build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum:
`cleared | gridlock | fullPeriod | wallClock | fault`.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining turn
(all seats fall to `greedy`, microseconds per turn), the remaining ticks run at full speed, and the
episode still ends `complete`. A `budget_guard` record names the turn it fired
(`src/ctf/decide.nim:263-264, 335-346`, kept).

A seat that never connects, disconnects mid-episode, or fails every decision **does not end the
episode**: its four signals are driven by `greedy` and the episode runs to its natural end with
`deadSeats[s] = true`. Nothing a player container does can stop the clock — the starter's
`lobbyJoinTimeoutTicks` bounds the lobby, and a silent seat cannot consume more than the per-turn
deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {greedy, fixedcycle}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=greedy` (the starter's "anything unrecognised is the published default" rule in
`baselines.nim`). **A scripted policy seated as a champion is a failure state.**

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/sumo-traffic-signals/anthropic_api_key` —
the hive 2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/sumo_traffic_signals_player.nim` is `src/paintball_player.nim` forked with no behaviour change:
read `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send —
and **re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"greedy"|"fixedcycle"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then acknowledge
frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3 close-frame race:
whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/signals/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

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
  `{…}`, fence-tolerant, tolerant of trailing prose) and `truncateRunes` / `sanitizeSay`
  (`directives.nim:61-90`) unchanged.

### Cadence, batching, and the wall-clock arithmetic

One command turn every **8 ticks**; **32 turns per episode**. At each turn the server builds all
**four** seats' request bodies and issues them as **one parallel batch** — never sequentially; this is a
simultaneous-decision game and serial calls would quadruple the wall clock for nothing. At most 4 calls
in flight; at most `4 × 32 × 2 = 256` calls per episode including retries.

```
attempt1Ms                          9.0 s
retryMs                             4.0 s
turnBudgetMs                       14.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                      12.0 s   -> 4 seats x 60/12 = 20 req/min  (sidecar cap: 30)

32 turns x max(spacing 12 s, budget 14 s), absolute worst          = 448 s
   typical (haiku answers in ~3-5 s, so spacing dominates)         = 384 s
256 ticks, <=544 cars, integer Nim only, fastMode                  =   1 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at        =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)     =  20 s
                                                                   -------
typical total                                                      = 420 s   < 720 s
absolute worst case (448 + 1 + 100 + 20)                           = 569 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                            = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                              = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_signals_manifest.nim` asserts it.

**Rate guard.** `turnSpacingMs` pins the steady state at 20 req/min, but a turn in which every seat
retries issues 8 requests. The engine therefore keeps a **rolling 60 s request counter**: if issuing the
next batch would push the trailing-60 s count above **28**, the seats that would exceed it skip the call
for that turn and take the `greedy` orders with `cause = "rate_guard"`. Bounded, logged, never a sleep
on the episode's critical path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant: seats send no per-tick inputs
(the server computes every phase), so the Sprite v1 Ready packet's dead-reckoning hazard cannot arise.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 14 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop, and
ctf's `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a bounded
grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's orders for that turn become the **`greedy`** scripted orders computed inside the game (the same
proc the `greedy` baseline uses — imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns[s]` counts them. The attempt-1 notice says **`will retry`**; only
a genuine second failure logs **`falling back`** (the pommerman 0.1.1 phase-60 grep scar).

**No failure mode leaves a signal without a phase.** The driver always has an order: this turn's, else
last turn's, else `greedy`'s; and absent everything, the signal holds its current phase, which is a
legal state. A seat that never connects is reported once to `COGAME_PLAYER_FAILURE_URI` with the
platform's **closed** payload — exactly `{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: `cleared` and `gridlock` both end the episode
before `maxTicks` (§The game), and the budget guard drops every seat to scripted play the moment two
more full turns would not fit.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **detectors are public; plans are private.** A real traffic-management centre sees
every loop detector in the city and every signal's current state; it does not see another operator's
intended offsets. That is what makes the idea's "coordination emerges as green waves" the actual
problem, and what the radio is for.

**Visible.**

- **The city, once, at registration** — the 4 × 4 intersection grid, the 16 gate ids, the link lengths
  (`ewLinkCells`, `nsLinkCells`, `ewGateCells`, `nsGateCells`), `gateQueueCap`, the four phases and
  their permitted movements, `minGreenTicks`, `clearTicks`, `maxRedTicks`, `turnTicks`, `maxTicks`,
  `demandEndTick`, `parThroughput`, and the **quadrant map** (which alias owns which four
  intersections). Static; afterwards referred to by id.
- **Every detector, every turn** — for all **16** intersections: id, owner alias, current phase (or
  `CLR`), `ticks_in_phase`, and the queue length on each of its four approaches. This is the
  control-centre view and it is what makes another seat's congestion legible without exposing its plan.
- **Everything about the seat's own four intersections** — per intersection: current phase,
  `ticks_in_phase`, current order and its age in turns, `last_order_result`, and per approach: queue
  length, whether the approach link is full, the **stop-line movement** (`through` | `left` | `right` |
  `null`), how many ticks that stop-line car has been blocked and **why** (`phase` | `spillback` |
  `null`); per exit: the receiving link's occupancy, capacity, whether it is full, and **which seat owns
  the intersection at its far end**; and the **inbound platoons**: per approach, how many cars are on the
  link and how many ticks until the nearest reaches the stop line.
- **The radio** — every seat's `say` from the previous turn, tagged with the speaker's alias, most recent
  first, at most 3 lines, each already truncated to 120 runes.
- **Public network statistics** — `tick`, `turn`, `throughput`, `demand` generated so far, `rejected`,
  `wait_ticks` (network), `your_wait_ticks`, the active spillback link list, the active gridlock ring
  list, and `waves` so far.

**Hidden.** Every other seat's **orders, offsets, notes and intentions**; every other seat's **real
player name**, policy name and kind; **future demand** (the arrival hash is never exposed, and no seat
learns a car's destination, only its stop-line movement); other seats' fallback/decision statistics; and
`seatWaitTicks` of any other seat. Nothing about any seat's identity ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `your_notes`) into
the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "Gamma",
  "controllers": ["Alpha", "Beta", "Gamma", "Delta"],
  "your_quadrant": "SW",
  "turn": 9, "of": 32, "tick": 64, "turn_ticks": 8, "ticks_left": 192,
  "city": {"rows": ["A","B","C","D"], "cols": [1,2,3,4],
           "quadrants": {"Alpha": ["A1","A2","B1","B2"], "Beta": ["A3","A4","B3","B4"],
                         "Gamma": ["C1","C2","D1","D2"], "Delta": ["C3","C4","D3","D4"]},
           "link_cells": {"ew": 6, "ns": 4, "ew_gate": 4, "ns_gate": 3},
           "phases": {"NSG": "N,S through+right", "NSL": "N,S left",
                      "EWG": "E,W through+right", "EWL": "E,W left"},
           "min_green": 4, "clearance": 2, "max_red": 60, "demand_ends_tick": 208, "par": 260},
  "your_signals": [
    {"at": "C2", "phase": "EWG", "ticks_in_phase": 6,
     "order": "wave EWG +3", "order_age_turns": 2, "last_order_result": "ran",
     "approaches": [
       {"from": "N", "queue": 4, "link_full": false, "stop_line": "through", "blocked_ticks": 0, "cause": null},
       {"from": "E", "queue": 6, "link_full": true,  "stop_line": "left",    "blocked_ticks": 14, "cause": "phase"},
       {"from": "S", "queue": 0, "link_full": false, "stop_line": null,      "blocked_ticks": 0, "cause": null},
       {"from": "W", "queue": 2, "link_full": false, "stop_line": "through", "blocked_ticks": 1, "cause": "spillback"}],
     "exits": [
       {"to": "C3", "owner": "Delta", "occupancy": 6, "capacity": 6, "full": true},
       {"to": "C1", "owner": "Gamma", "occupancy": 1, "capacity": 6, "full": false},
       {"to": "B2", "owner": "Alpha", "occupancy": 3, "capacity": 4, "full": false},
       {"to": "D2", "owner": "Gamma", "occupancy": 0, "capacity": 4, "full": false}],
     "inbound": [{"from": "W", "cars": 3, "nearest_ticks": 2},
                 {"from": "N", "cars": 1, "nearest_ticks": 3}]}
  ],
  "detectors": [
    {"at": "A1", "by": "Alpha", "phase": "NSG", "ticks_in_phase": 3, "q": {"N": 2, "E": 0, "S": 5, "W": 1}},
    {"at": "A2", "by": "Alpha", "phase": "CLR", "ticks_in_phase": 0, "q": {"N": 1, "E": 4, "S": 0, "W": 6}}
  ],
  "radio": [
    {"from": "Alpha", "text": "B2 goes EWG at tick 66, eastbound platoon of 5 is yours at 72"},
    {"from": "Delta", "text": "C3>C4 is full, do not send me anything east for two turns"}
  ],
  "network_status": {"throughput": 96, "demand": 141, "rejected": 2,
                     "wait_ticks": 3120, "your_wait_ticks": 861,
                     "spillback": ["C2>C3", "B3>C3"], "gridlock": [], "waves": 3},
  "your_notes": "C1 offset +2 behind C2 for the eastbound wave; D2 stays NSG"
}
```

Field rules. `detectors` is always **16 entries**, ascending by intersection index. `your_signals` is
always **4 entries**, ascending by intersection index, so the array shape never changes. `phase` is one
of `NSG|NSL|EWG|EWL|CLR`. `stop_line` is one of `through|left|right|null`. `cause` is one of
`phase|spillback|null`. `last_order_result` is one of `ran|deferred|overridden|repaired|unknown` — the
driver's honest report of what actually happened to the previous order, which is what lets a seat notice
that its offsets are being eaten by `minGreenTicks` or by a starvation override.

### Reply schema and per-field caps

```json
{"orders": [{"at": "C2", "verb": "wave", "phase": "EWG", "delay": 3},
            {"at": "C1", "verb": "phase", "phase": "EWG"},
            {"at": "D1", "verb": "hold"},
            {"at": "D2", "verb": "auto"}],
 "say": "eastbound wave on row C: C1 at +0, C2 at +3, Delta take C3 at +6",
 "notes": "if C2>C3 is still full next turn, gate C1 with hold"}
```

| Field | Type | Cap / domain |
|---|---|---|
| `orders` | array | **≤ 4 entries** (= one per owned intersection). Entries past the cap are dropped and counted in `ordersRejected`. Absent or empty = "every signal keeps its order" and the reply is still **usable** |
| `orders[].at` | string | **≤ 2 runes**; must be one of **this seat's** four intersection ids, upper-cased before matching; at most once per reply (a repeat is dropped and counted) |
| `orders[].verb` | string | **≤ 6 runes**; enum `hold` \| `phase` \| `wave` \| `auto`, lower-cased before matching |
| `orders[].phase` | string | required iff `verb ∈ {phase, wave}`; **≤ 3 runes**; enum `NSG` \| `NSL` \| `EWG` \| `EWL`, upper-cased before matching (`CLR` is not selectable and is rejected) |
| `orders[].delay` | integer | required iff `verb == "wave"`; **clamped to 0 … 6** (`turnTicks − 2`); a non-integer or absent value is repaired to `0` and counted |
| `say` | string | **≤ 120 runes** (`MaxSayRunes`) — the control-room radio; heard by every seat next turn and drawn in the feed |
| `notes` | string | **≤ 240 runes** (`MaxNoteRunes`) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160` (`src/ctf/sim_types.nim:747, 794-795`),
which are a 10-character in-world shout and a short note. A signal offset call has to name an
intersection, a phase and a tick, so `MaxSayRunes = 120` and `MaxNoteRunes = 240` here, and
`ShoutMaxChars` is deleted with the shout mechanic (§Sim module → Deleted).

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded error
text — is truncated on RUNE boundaries** via the starter's `truncateRunes` / `runeSubStr`
(`directives.nim:61-90`), never by byte index. Byte truncation is what makes a replay that renders in a
browser fail a strict UTF-8 parser; `tests/test_signals_replay.nim` asserts it with 4-byte emoji sitting
exactly on every cap.

Unknown top-level and per-order keys are ignored. A reply with a valid `say` but no `orders` is
**usable** (every signal keeps its order and the radio line is delivered). A reply that is not a JSON
object is a parse failure. An order whose `verb` is valid but whose required argument is missing or
unknown is **repaired to that intersection's previous order**, counted in `ordersRejected`, and reported
back next turn as `last_order_result: "repaired"`.

### System prompt (fixed, identical for both champions)

```
You are the traffic-signal controller for FOUR intersections in one quadrant of a
4x4 city grid. Three other controllers run the other three quadrants. You do not
control their signals and you cannot see their plans. Every 8 simulated seconds you
issue orders and a deterministic actuator runs your signals until you change them.

THE CITY
- Intersections are named row+column: rows A (north) to D (south), columns 1 (west)
  to 4 (east). Cars enter from 16 gates on the edges and drive a fixed shortest
  route to their exit gate.
- Every approach is ONE LANE. A car that wants to turn left blocks every car behind
  it until you give it a left phase.
- Four phases: NSG (north+south, straight and right), NSL (north+south, left only),
  EWG (east+west, straight and right), EWL (east+west, left only). Every change costs
  2 ticks of all-red, and a phase must run 4 ticks before it can change.
- LINKS ARE SHORT AND THEY FILL UP. An east-west block holds 6 cars, a north-south
  block holds 4. When the block ahead is FULL, the car at your stop line CANNOT MOVE
  EVEN ON GREEN. Your green then buys nothing and costs you the cross street.
- If a stop-line car is blocked by the phase for 60 ticks the city forces the phase
  that serves it and your order is overridden.

WHAT SCORES
Only how many cars get all the way OUT of the city. Everyone gets the same number.
Total waiting across the whole city is the tie-break, and waiting at YOUR OWN four
intersections is a much smaller tie-break after that. Emptying your own queues into
somebody else's full block lowers the number everybody is scored on, including you.

YOUR ORDERS (one per intersection per turn; a signal keeps its order until you change it)
- {"at":"C2","verb":"hold"}                              keep the current phase
- {"at":"C2","verb":"phase","phase":"EWG"}               change to that phase now
- {"at":"C2","verb":"wave","phase":"EWG","delay":3}      change to it 3 ticks into the turn
- {"at":"C2","verb":"auto"}                              hand it to the greedy actuator,
                                                         which each tick serves whichever
                                                         phase has the longest movable queue

GREEN WAVES ARE BUILT WITH "delay"
A car covers one cell per tick; an east-west block is 6 cells, a north-south block 4.
So if C1 turns EWG at tick t, its platoon reaches C2 about 6 ticks later and C3 about
12. Give C2 "wave EWG delay 6" and the platoon never stops. Two of the four
intersections on any avenue belong to SOMEBODY ELSE, so say your offsets out loud.

TALKING
"say" is a radio call every other controller hears next turn. It is the ONLY way they
learn your offsets or that one of your links is full. "notes" comes back to you next
turn and to nobody else.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the character {
and end with }. No prose, no markdown, no code fences.
{"orders":[{"at":"C2","verb":"wave","phase":"EWG","delay":6}],"say":"<=120 chars","notes":"<=240 chars"}
```

### Champion #1 — `signals-greenwave` (owner **daveey**), `PLAYER_PROMPT`

```
Run the city as two avenues and publish your offsets. On turn 1, pick the avenue
through your quadrant with the most inbound cars and declare it your wave direction in
one radio line - "row C eastbound is my wave: C1 at +0, C2 at +6, Delta take C3 at
+12".
Every turn, walk your four intersections in this order: the two on your wave avenue
first, then the other two.
On the wave avenue, give the upstream intersection "phase" with the through phase for
that direction (EWG for east-west, NSG for north-south) and give the downstream one
"wave" with the SAME phase and delay equal to the block length in cells between them
(6 east-west, 4 north-south) minus one. Repeat the offsets on the radio every third
turn and whenever a neighbour's radio line names a different offset.
Before you issue a through phase, read that intersection's "exits" list. If the exit
you are about to feed is full, do NOT open it: issue "hold" instead, say "holding C2,
C2>C3 is full", and spend the green on the cross street with the longest queue.
Off the wave avenue, give the cross phase whenever the cross queues total 6 or more, or
whenever a stop-line movement is "left" with blocked_ticks over 20 - then give NSL or
EWL for one turn and go straight back.
If your own "inbound" shows a platoon of 4 or more arriving in 3 ticks or fewer, use
"wave" with a delay that matches it rather than opening early into an empty box.
Never use "auto" on the wave avenue; use it only on an intersection whose queues are
all under 2 so you can spend your attention elsewhere.
```

### Champion #2 — `signals-gatekeeper` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Protect the network from spillback and let throughput follow. Your rule, decided once
and never dropped: NEVER give a green whose exit link is full, and always give the
green whose exit link is emptiest.
Every turn, for each of your four intersections in this order - the ones with a full
exit first, then the rest:
1. Read "exits". Mark every exit with occupancy equal to capacity as closed.
2. Score each phase by the queue it would serve MINUS 4 for every closed exit it would
   feed. Issue "phase" for the best-scoring phase; if the current phase is the best,
   issue "hold".
3. If EVERY phase feeds a closed exit, issue "hold" and say which link is blocking you,
   naming the owner from the "exits" list - "Beta, B3>C3 is full, C3 is choking my B2".
Gate the edges. On any intersection with a gate approach, if your interior exits are
over two thirds full, hold the gate approach red - a car still outside the city costs
nothing and blocks nobody, and rejected demand is not what is scored.
Watch "blocked_ticks" with cause "phase". Any stop-line car over 30 ticks gets its
phase next turn, before the city forces it on you: a starvation override wastes your
whole turn.
When "spillback" in network_status names a link inside your quadrant, spend two turns
draining it: give the phases that empty it and hold the phases that feed it, and say
what you are doing so nobody refills it.
Answer every radio line that asks you to hold something. If you cannot, say so and say
why.
```

### The driver (deterministic, shared by every policy)

`src/signals/driver.nim` — the starter's `control.nim` (directive → per-tick actuation), retargeted from
pixel steering to a **requested phase per intersection per tick**. It is the **only** producer of phase
requests, and it contains no randomness.

| Order | Requested phase, per tick `k` of the turn (`k = 0 … turnTicks−1`) | Finishes with |
|---|---|---|
| `hold` | the current phase | `ran` |
| `phase P` | `P`, from `k = 0` | `ran`, or `deferred` while `minGreenTicks` blocks it |
| `wave P d` | the current phase for `k < d`, then `P` | `ran` |
| `auto` | `argmax_P served(P)`, recomputed every tick | `ran` |

`served(P)` — used by `auto` and by the `greedy` baseline, one implementation, imported by both:

```
served(P) = sum over approaches a greened by P of
              (if a's stop-line car exists and P permits its movement:
                 min(queueLen(a), greenCap = 6)
               else 0)
```

`auto` switches only if `served(best) >= served(current) + switchMargin = 2`, ties broken by keeping the
current phase, then by lowest phase index. `served` counts the whole queue behind a movable head car,
because that is the queue the green will actually discharge, and counts zero behind a head car the phase
cannot move — which is what makes a blocked left-turner visible to the actuator instead of invisible.

`minGreenTicks`, `clearTicks` and the starvation override are enforced by the **signal machine** (tick
step 2), never by the driver: no order can produce an illegal signal state.

### Scripted baselines (both shipped as fillers; `greedy` is also the server-side fallback)

`src/signals/baselines.nim`, the starter's module retargeted. Both emit the **same** order objects an LLM
does, through the same validator, which is what makes the bounded-orders test meaningful. Neither ever
emits `say` or `notes` — they are the controllers who will not talk to you, which is precisely the
"coordination emerges" problem the idea names.

**`fixedcycle`** — `PLAYER_SCRIPTED=fixedcycle`. The classic fixed-time plan, no sensing, no
coordination. Every turn, for each of its four intersections in ascending index:
`{"at": <id>, "verb": "phase", "phase": phaseCycle[(turn − 1) mod 4]}` with
`phaseCycle = [NSG, EWG, NSL, EWL]` — one phase per turn, a 32-tick cycle, identical at all four
intersections and therefore with **zero** offset between them. It is four lines, it is the control that
answers "did the LLM actually coordinate?", and its uncoordinated cycle is what a real city looks like
before anybody tunes it.

**`greedy`** — `PLAYER_SCRIPTED=greedy`, and the fallback. The standard longest-queue actuated
controller, and the idea's "local greed (flush my queue)". Every turn, for each of its four
intersections in ascending index, first matching rule wins:
1. If `served(current) >= max_P served(P) − switchMargin (2)` → `{"verb": "hold"}`.
2. Else → `{"verb": "phase", "phase": argmax_P served(P)}` (ties broken by lowest phase index).
It **never** looks at an exit link's occupancy, so it discharges into full links and exports congestion
downstream — the behaviour the idea says local greed produces, shipped as the thing to beat. It never
uses `wave`, so it can never build an offset.

Like the starter's `DefaultBaselineParams`, the three tunables (`switchMargin = 2`, `greenCap = 6`, and
whether `served` counts all queued cars or only stopped ones) are a parameter object chosen by
`tools/tune_baselines.nim`'s head-to-head sweep, not guessed; `tools/ci/baseline_tuning.json` records the
sweep's pick and `tests/test_signals_tuning.nim` asserts the shipped defaults still equal it.

**`auto` is the floor, not a strategy.** A seat may issue `auto` on all four signals and thereby match
`greedy`'s local behaviour. That is deliberate: it gives an LLM a safe default for a quiet corner and it
sets the bar the champions have to clear with offsets and spillback gating, which `auto` cannot express.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/signals/`. The fork is a rename sweep
(`ctf` → `signals`, `CTF_WIRE` → `SIGNALS_WIRE`; a CI grep asserts no `ctf_` / `CTF_` identifier survives
outside comment history) plus the changes below. **The same modules compile twice**: natively into
`/bin/sumo-traffic-signals` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason an external simulator is not an option here.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/signals/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417` |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/signals/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` (`replays.nim:142`) → **`SignalsReplayMagic = "COWLDSIG"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/signals/` (`control.nim` → `driver.nim`) | **fork**, retargeted not rewritten | the per-turn parallel batch (`decide.nim:427`), the two deadlines, `turnSpacingMs` (`decide.nim:386-389`), the budget guard (`decide.nim:335-346`), tolerant parsing, the rune caps, repair-don't-reject, the fallback ladder and its log phrasing |
| `src/ctf/sim_state.nim` → `src/signals/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/signals/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames` (`roster.nim:64`), the results JSON builder |
| `src/ctf/events.nim` → `src/signals/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/signals/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/signals/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/signals/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24`, the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 120`, `MaxNoteRunes = 240`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/signals/sim_config.nim` | **fork** | `GameConfig` lifecycle and `config.update` |
| `src/ctf.nim` → `src/sumo_traffic_signals.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/sumo_traffic_signals_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** (40 022 bytes, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`) | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/signals_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_{red,blue,green,yellow}.png`, `data/soldier_{red,blue,green,yellow}_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*,blue_*,green_*,yellow_*}.webp` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, fog-of-war raycasting and
the first-person PIP, spray cans, floor paint and the paint grid, the paint buff, King of the Hill and
`hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the barrage,
med kits, shields, cardboard barriers, trenches, perks, handicaps, lives and respawns, teams and
four-team free-for-all, **shouts-as-cog-speech and `ShoutMaxChars`**, achievements, campaign mode,
`maxGames > 1` side-swapping, and **all of the pixel-space map machinery**: `arena.nim`'s wall masks and
pixel queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`,
`docs/MAPKIT.md`. The board here is a fixed integer cell grid built in code; every one of those is a
config surface the traffic rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`, `medkit`,
`shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `rig_real/`) — cars are drawn as baked chips
(§Viewer → Art) and a 128 px rig is never used at 7.8 px per cell.

### New modules

- `src/signals/city.nim` — the code-authored topology: intersections, approaches, exits, gates, links,
  the cell layout and the cell ↔ (link, index) helpers, the board-size arithmetic, the movement-class
  table (`through`/`left`/`right` from approach + next link), and the **all-pairs route table**: Dijkstra
  over the 32-node graph (16 intersections + 16 gates) with edge cost = the link's cell count (i.e.
  free-flow travel ticks), tie-broken by fewer turns, then by lowest next-node index, computed once at
  load into a `[32][32]` next-hop table. Pure integer; no pixie, no pixel queries.
- `src/signals/vehicles.nim` — the car arrays (`spawnTick`, `originGate`, `destGate`, `link`, `cell`,
  `route` cursor, `waitTicks`, `waitSinceLastCrossing`, `stops`, `crossings`, `cleanCrossings`,
  `blockedByPhaseTicks`, `spillbackBlockedTicks`), the gate queues, the arrival hash of tick step 7, and
  the free-slot list.
- `src/signals/phases.nim` — the phase enum, the permitted-movement table, the per-intersection signal
  machine of tick step 2 (`ticksInPhase`, `clearLeft`, requested vs current, deferral, the starvation
  override).
- `src/signals/flow.nim` — queue measurement, the full/spillback spans, the blocked-by graph and the
  gridlock-ring cycle search of tick step 10, and the green-wave window of tick step 11, plus the span
  tables the viewer's scrubber, sparkline and lull scan read.
- `src/signals/sim.nim` — the step loop of §The game exactly as numbered, `gameHash`, end evaluation, and
  the per-seat observation builder. Imports and re-exports the sim modules, as the starter's does, so
  `import signals/sim` sees everything.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cells, ids, tick counters, queue lengths, route distances,
permille comparisons. There is no floating point anywhere in `sim.nim`, `city.nim`, `vehicles.nim`,
`phases.nim`, `flow.nim`, `driver.nim` or `baselines.nim`, and a test greps for it. Demand is a permille
integer compared against `hash mod 1000`; means (travel time, stops per car) are **not** computed in the
sim at all — `results` carries the integer totals `travelTicksTotal` and `stopsTotal` and the viewer
divides. That makes the native ↔ wasm hash chain exact by construction.

**One seeded source, and it is a hash, not a stream.** Whether gate `g` produces a car at tick `t`,
whether that car is a through-runner, and which gate it is bound for are all read out of the single pure
hash `mix64(seed, g, t)` (splitmix64 over `seed`, `g·1000003`, `t·6364136223846793005`), evaluated
independently for every `(g, t)`. Nothing a controller does can shift another gate's draws, change their
order, or consume them out from under it — the strongest form of the idea's "demand seeded".
A controller influences only *whether the city can absorb the demand when it arrives*, which is the
game. `tests/test_signals_demand.nim` asserts it by replaying one seed under different seat behaviour and
comparing the full `(gate, tick) → (generated, destination)` table.

There is no other random draw: the topology is fixed, the routes are deterministic, the phases start at
`NSG` with `ticksInPhase = 0` at every intersection, and every tie-break in the step loop is an explicit
index order. The seed is randomised in `src/sumo_traffic_signals.nim` before `config.update` (the
starter's rule), recorded in the replay config and in `results.seed`. Two episodes with the same seed and
the same orders are byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDSIG`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, variant, `num_agents`, every rule constant, `players[].name`,
   `slots[]`, `fastMode`), then the record stream — joins (name, slot, token), leaves, **per-turn order
   records** (the only inputs this game has), chat records (`register` / `directive` / `fallback` /
   `budget_guard` / `stop` / `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/signals_replay.nim` — which imports the **same**
   `src/signals/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `signals_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `signals_frame`
   re-steps the sim from the recorded orders and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and surfaced as
   `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: per intersection in ascending index
   `(phaseIndex, clearLeft, ticksInPhase, requestedPhase, orderKind, orderPhase, orderDelay)`; then per
   link in ascending index `(occupancy bitmask, queueLen)`; then per live car in ascending id
   `(link, cell, waitTicks, cleanCrossings, blockedByPhaseTicks)`; then `throughput`, `rejected`,
   `demandGenerated`, `networkWaitTicks`, the four `seatWaitTicks`, `greenWaves`; then the active
   spillback link set and the active gridlock-ring link set, each as sorted link indices; then `tick`.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact cannot be
   re-derived from sim state, so the stop is written as one record applied by the *same proc* on record
   and on playback, and `tests/test_signals_replay.nim` runs the record → re-derive check for **every**
   end reason (`cleared`, `gridlock`, `fullPeriod`, `wallClock`, `fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 256 hashes + ≤ 128 order records + ~40 chat records ≈ **20 KB**. Everything else is
re-derived in the browser.

### Documented divergences from the source benchmarks (mirrored into `docs/PORTING-SUMO-RL.md`)

1. **No SUMO, no CityFlow, no port.** This is a coworld-native reimplementation of the *control problem*
   the SUMO-RL / RESCO benchmarks pose, decided as a scoping rail before design. SUMO is a C++ desktop
   simulator with XML networks, its own RNG and its own car-following model; embedding it would mean a
   pod-side simulator that cannot compile to wasm, so the static replay viewer — a non-optional pin —
   would be impossible. Nothing in this repo claims bit-exactness with any upstream benchmark, no upstream
   numbers are cited as reproduced, and no upstream code is vendored.
2. **Vehicles are cellular, not car-following.** One car per cell, one cell per tick, no acceleration, no
   headway model, no lane changing, one lane per approach. This is the CityFlow-style discrete idiom
   rather than SUMO's continuous Krauss model, and it is what makes the native ↔ wasm hash chain exact.
3. **No start-up lost time and no yellow-interval discharge.** Clearance is a flat 2 ticks of all-red;
   a queue steps forward the same tick its head discharges (tick step 4's downstream-first order).
4. **Reward shape.** SUMO-RL's per-intersection reward is `−queue` or `−waiting`; the league needs one
   rankable per-seat integer, so §The game makes network throughput the dominant term, network waiting
   the second, and the seat's own waiting the third. All three underlying quantities are recorded in
   `results`, so the SUMO-RL-style local signal is still readable per seat.
5. **One network: the 4 × 4 grid.** Cologne, Ingolstadt and Manhattan are §Out of scope — they are OSM
   imports whose geometry cannot be re-derived in the viewer from a name and cannot be made legible at
   360 px.
6. **Who chooses the phase changed, not what the phases are.** Per-tick RL policies are replaced by four
   turn-level orders under a deterministic per-tick actuator — the idea's own "phase choice every 5–10 s
   … suits LLM policies well". The four-phase NEMA-style plan, minimum green, all-red clearance, maximum
   red and single-lane approaches are the benchmark idiom.
7. **`maxGames = 1`** — the starter's multi-game episode is not used; a cooperative game has no side to
   swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with `turnTicks = 8` and four seats in the batch.
2. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration, **not** applied as a shout and **not** written to the replay chat stream; the server
   writes a redacted `register` record instead (policy label and kind, never the prompt). The starter's
   "hold an unappliable registration and re-read it when the slot lands" behaviour is kept verbatim, and
   the server **logs loudly and refuses to start the game** when a joined seat has no register record
   (the grf-football 2026-08-27 silent-default scar). Any other chat text from a seat is dropped —
   controllers speak through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop iteration
   (`server.nim:1407-1417`), kept, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wallClock`, and written as the load-bearing stop record of point 5 above.

### The two named edits to `roster.nim`

1. **Aliases.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → `Alpha`, `Beta`, `Gamma`,
   `Delta`. The `IdentityNames` array itself (`roster.nim:64`) is unchanged. Board labels and the label
   manifest inherit the two-name-space rule with no further change, and `showPlayerLabels` is false.
2. **`squadResultsJson` → `cityResultsJson`** — one entry per seat, four entries in every seat-indexed
   array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a cell grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits cell-space
   coordinates; the fov cache and shadowcasting are deleted (spectators see the whole city, and so do the
   controllers — detectors are public by design, §Decisions).
2. **Car, signal and link pools.** New pools `CarSpriteBase`, `SignalHeadBase` and `LinkBandBase`, sized
   to `MaxVehicles = 1024`, `16 × 4` signal heads and `80` links, filled in id/index order and emitted
   incrementally like the starter's other object families.
3. **Baked city bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the way the
   starter bakes endzone paint, and the asphalt, kerbs, block interiors, lane markings, stop lines,
   crosswalks, gate arrows and intersection labels are baked onto it once (§Viewer → Art) — one static
   bake, so the per-frame cost is cars, signal lamps and overlays only.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI` in;
`COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI` out;
`COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST` / `PORT`; player sockets at
`/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset route:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for the
`gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). The player
websocket handler **closes unless the token matches the seat** (the certifier probes with a bad token —
cogame-flatland 0.1.1). Global broadcasts are fire-and-forget so a slow viewer can never stall the
episode.

### Results document (closed schema; `cityResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":              ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
  "aliases":            ["Alpha", "Beta", "Gamma", "Delta"],
  "quadrants":          ["NW", "NE", "SW", "SE"],
  "scores":             [371985000, 371984990, 371985000, 371985000],
  "win":                [true, true, true, true],
  "winner":             null,
  "reason":             "complete",
  "endRule":            "cleared",
  "throughput":         372,
  "parThroughput":      260,
  "demandGenerated":    386,
  "rejected":           14,
  "networkWaitTicks":   3142,
  "seatWaitTicks":      [742, 861, 799, 740],
  "netWaitK":           15,
  "seatWaitK":          [0, 1, 0, 0],
  "served":             [214, 231, 208, 226],
  "travelTicksTotal":   14880,
  "stopsTotal":         1104,
  "greenWaves":         11,
  "spillbacks":         26,
  "spillbackTicks":     188,
  "gridlocks":          1,
  "gridlockTicks":      34,
  "longestGridlockTicks": 34,
  "starvations":        3,
  "deferredSwitches":   61,
  "phaseChanges":       [38, 41, 36, 39],
  "finalTick":          241,
  "turnsPlayed":        31,
  "seed":               1734029581,
  "variant":            "grid4x4",
  "policyKinds":        ["llm", "llm", "scripted", "scripted"],
  "crossPlay":          true,
  "llmTurns":           [31, 30, 0, 0],
  "fallbackTurns":      [0, 1, 0, 0],
  "ordersRejected":     [0, 3, 0, 0],
  "deadSeats":          [false, false, false, false],
  "stopDetail":         ""
}
```

`winner` is always `null` (cooperative). Two identities hold in every results document and are asserted
by `tests/test_signals_engine.nim`: `Σ seatWaitTicks == networkWaitTicks`, and
`throughput + rejected == demandGenerated` **whenever `endRule == "cleared"`** (otherwise the difference
is the cars still on the network at the final tick). The example above satisfies both, and its `scores`
are exactly `1_000_000 × 372 − 1_000 × 15 − 10 × seatWaitK[s]`.

Adding a key means updating `cityResultsJson`, the manifest's `results_schema` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas are closed and
undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDSIG`** format — the static wasm viewer parses exactly this,
and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`, `static_replay_worker.js` and
`wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse (the knights-archers precedent).
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (`SMOKE_REQUIRE_REPLAY_JSON`, template line 31).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"signals/v1","gameVersion":"1","seed":…,"variant":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"orders":[…],"radio":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md` documents for
  prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.throughput, .results.greenWaves' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks, (.radio|length)' /tmp/ep.json
  ```
  Require `protocol == "signals/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.throughput > 0`, and the champion seats' orders with `source == "llm"`, real verbs
  (including at least one `wave`) and non-empty radio lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDSIG`, format version, `gameName` `sumo-traffic-signals`, `gameVersion` `1` |
| config JSON | `seed`, `variant`, `num_agents`, `turnTicks`, `maxTicks`, `ewLinkCells`, `nsLinkCells`, `ewGateCells`, `nsGateCells`, `gateQueueCap`, `minGreenTicks`, `clearTicks`, `maxRedTicks`, the six demand fields, `throughRunnerPermille`, `parThroughput`, `ringTicks`, `gridlockStallTicks`, `waveVehicles`, `waveWindow`, `waveCrossings`, `switchMargin`, `greenCap`, `players[].name` (real names), `slots[]`, `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| orders | per turn, per seat, per intersection: the accepted order — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The **city topology is code, compiled into both the binary and the wasm module**, and the replay carries
the variant name and every rule constant; the viewer therefore reconstructs the exact city and
re-simulates every car from bytes it already has, with no fetch. A topology change is a `GameVersion`
bump, and the committed fixtures' version sweep makes an unversioned change fail the build.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `quadrant`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `orders` (array of `{at, verb, phase, delay}`), `say` (≤ 120 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `turn`, `slot`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of fourteen kinds, plus `end`:**

`turn` `{n}`; `order` `{slot, at, verb, phase, delay}`; `say` `{slot, text}`;
`fallback` `{slot, cause}`; `phasechange` `{at, slot, from, to, t}`;
`starve` `{at, slot, approach, t}`; `spillback` `{link, at, slot, t}`; `spillclear` `{link, ticks}`;
`gridlock` `{links, ats, t}`; `gridlockclear` `{links, ticks}`;
`wave` `{corridor, dir, ats, vehicles, t}`; `exit` `{gate, travel, stops, total, t}`;
`gatejam` `{gate, at, slot, t}`; `gateclear` `{gate, ticks}`;
plus `end` `{reason, endRule, throughput, par, demand}`.

`tests/test_signals_events.nim` asserts the emitted set equals exactly this list. `exit` fires per car
(~400 an episode) and drives the throughput clock and sparkline; **the feed prints an exit line only at
every 25th car**, so it never floods.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`wave`,
`spillback`, `gridlock`, `fallback`, `end`.** `turn`, `order`, `say`, `phasechange`, `starve`,
`spillclear`, `gridlockclear`, `exit`, `gatejam` and `gateclear` drive the feed, not the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Spawn, Enter, Reject, Cross, Exit, PhaseChange, Starve, Spillback, SpillClear,
Gridlock, GridlockClear, Wave, TurnStart, Directive, Fallback, PhaseChangeDeferred` and the mandatory
trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh` is
coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/signals/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already carries
the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling. It
stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No `/client/replay` live-server
viewer is ever declared to the platform; the game still serves `/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/signals_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE` / `EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the
viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one piece:
the Worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), the module is emitted
**non-modularized** as `signals_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang`
through `emcc`, `--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable: with
`-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals — the starter's
own comment at `config.nims:35-41`), `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`,
`-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_signals_load_replay,_signals_frame,_signals_input,
_signals_packet_ptr,_signals_packet_len,_signals_mismatch_tick,_signals_error_ptr,_signals_error_len,
_signals_stage_ptr,_signals_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './signals_replay.js')` in that order (the
starter's line 239, renamed only).

`signals_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `signals_load_replay` re-simulates the whole episode once headlessly (256
  ticks over ≤ 544 cars of integer work — single-digit milliseconds in wasm), records the per-tick
  cumulative exits, rejections and network wait, the spillback spans, the gridlock spans, the wave ticks,
  the lull spans and the beat ticks, then resets and renders frame 0. That is what lets the throughput
  sparkline and the scrubber beats draw at **full width on the first frame** instead of growing in.
- `signals_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (`static_replay.js:158-161`) — posted by the
Worker only *after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the
attribute means "a frame is on the canvas", not "a file was fetched". On failure it sets
**`data-replay-error`** on `<html>` with the message, in `showFailure()` (`static_replay.js:8-20`). Both
are coworld-ctf's own signals, inherited unchanged — this fork adds neither and removes neither. The
`coworld-replay` postMessage bridge's `ready` is posted **from a callback fired after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`, 2026-08-24),
or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes; sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`). Not edited, not reformatted;
  `tests/test_signals_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in the
  appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats` ignores kinds it does not
  know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (`replay_broadcast.html:4276-4325`), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny`
  density system are untouched, and the block is installed through the starter's own splice hook:
  `window.PaintballChrome` (declared at `replay_broadcast.html:4651`, installed at `:4337`) is renamed
  `window.SignalsChrome` and its `install(PB_CTX)` / `frame(s, ctx, jumped)` (`:2075`) /
  `event(e, s, ctx)` (`:3480-3481`) entry points are kept with the same signatures. The appended block
  replaces only the *contents* of the scorebug plates, adds the queue-pressure rail, the wave banner and
  the spillback/gridlock chips, and retargets the feed rows, the beat rendering, the momentum series and
  the endcard columns. A test asserts the starter's byte prefix is intact up to the documented splice
  marker and that the file only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_signals_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw mid-replay
  and latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.SIGNALS_WIRE` rename
  emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific draw call and the FPV pipeline.
  Added: `drawCityBed`, `drawQueueHeat`, `drawCars`, `drawSignalHeads`, `drawWave`, `drawGridlock`,
  `drawPressureRail`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`,
    `#zoom-read` (`replay_broadcast.html:1510-1521`), and the page's
    `core.attachMinimap($('minimap-canvas'))` call (`:4200`). **Zoom decision: dropped.** The board is a
    fixed 34 × 26 cell city with no off-frame area; `relayout()` letterboxes it whole at every width (see
    "Legible at 360 px"), so per the pin a fixed arena drops `#viewpanel` entirely. `broadcast_core.js`
    already tolerates never being attached: `minimapSurface` / `minimapCtx` stay null and `drawMinimap()`
    returns on its first guard.
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`, `:1532-1548`) and **`#povBadge`** (`:1525`) —
    there is no per-car point of view worth showing; the city is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad` (`:2219-2244`), and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture` (`:919-934`) and `.gamestart`, `.hillflip`,
    `.tagout`, `.gameover` (`:4431-4443`) CSS rules — those kinds are never emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`, `#lk-art`,
    `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with `#plates-l` / `#plates-r` / `#clock` /
    `#clock-time` / `#clock-caption` / `#ffwd-mini`, `#bannerlane`, `#killfeed`, `#mmwarn`,
    **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`,
    `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`, `#speedchips`),
    `#scrub` with `#momentum` / `#scrub-fill` / `#lulls` / `#scrub-win` / `#scrub-head`, `#endcard` with
    `#ec-headline` / `#ec-wincond` / `#ec-how` / `#ec-teams` / `#ec-replay`, and `#status`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here and
enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`:3795`) | `<span>Controller</span><span>Served</span><span>Waiting</span><span>Waves</span><span>Spillbacks</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` (`:3788`) | `<span>Signal</span><span>Served</span><span>Queue-s</span><span>Changes</span>` |
| `<span class="fl-cap">Lives left</span>` (`:3793`) | `<span class="fl-cap">Cars through</span>` |
| `<span class="fl-cap">Hill time</span>` (`:3786`) | `<span class="fl-cap">Waiting</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (`:1576`) | `<span class="momentum-label">THROUGHPUT</span>` |
| `<span class="lives-label">Lives</span>` (`:2241`) | `<span class="served-label">Served</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (`:2224`) | `<span class="served-label pb-lbl">Wait</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (`:1480`, `:1833`) | "Booting the signal controllers…" |
| `#clock-caption` "In the locker room" (`:1499`) | "Signals dark" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (`:1524`) | "Replay hash mismatch at tick N — showing recorded orders" |
| `#btn-spoilers` title "Spoilers: kills / flag story / winner on the timeline ahead of the playhead (o)" (`:1564`) | "Spoilers: green waves / spillbacks / gridlock on the timeline ahead of the playhead (o)" |
| team words `RED` / `BLUE` in `.ec-tname` / plates (`:2222`, `:2239`, `:3783`, `:3790`) | the seat's **alias** (`ALPHA`…`DELTA`) plus its quadrant and colour chip |

**`tests/test_signals_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`, `hill`,
`POV`, `spray`, `grenade`, `med kit`, `kill` — outside comment blocks, and asserts **zero** matches; and
asserts each replacement string above is present exactly once. A rename that reintroduces paintbot
vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (`replay_broadcast.html:4291-4318`). **No overlay sits in the transport band**: the
board is laid out between the two bands and every addition here (the queue-pressure rail, the wave
banner, the spillback/gridlock chips, the feed) is positioned inside the board region or in the top band.
The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, `:1047`, the starter's
rule, kept) so the scrubber stays clickable underneath, and it is **dismissed by every seek** (the
starter's `else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable,
labelled buttons**: the appended block's `cityBeat(tick, kind, slot, label)` — named so it can never
shadow `chrome_common.js`'s `markBeat` alias (`replay_broadcast.html:1635`; the tandem 2026-08-23
hoisting trap) — appends `<button class="beat-marker <kind> <colour>" title="…" aria-label="…">` to
`#scrub` and seeks on click. CSS exists for **every kind emitted and no others**: `.beat-marker.wave`,
`.beat-marker.spillback`, `.beat-marker.gridlock`, `.beat-marker.fallback`, `.beat-marker.end`. The game
block never calls `markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: one tick per two animation frames at 30 fps = 15 ticks/second** (speed chips
`[0.5, 1, 2, 4, 8]`, default 1), with car positions interpolated between cells across the two frames so
traffic flows instead of snapping. A 256-tick episode therefore plays for **17.1 s**, which is what lets
`viewer_smoke.mjs --soak 10` observe real advancement instead of a legitimately-finished replay (the ecos
2026-08-23 scar).

### Readouts

1. **The city**, drawn edge to edge: the baked asphalt bed with kerbs, block interiors, lane markings,
   stop lines, crosswalks and gate arrows; the 16 intersection boxes labelled `A1`…`D4`; each quadrant
   tinted faintly in its owner's colour with the owner's alias set at its outer corner; **signal heads**
   at all 64 approaches, three lamps each, showing red / amber (clearance) / green as the phase machine
   dictates; and **cars** as baked chips moving cell to cell, with a chevron on through-runners.
2. **Queue-length heatmap** (the idea's ask) — every link carries a translucent band along its lane whose
   colour ramps green → amber → red with `queueLen / capacity`, and a **full** link's band pulses red with
   a hard edge at the stop line. This is the readout that carries the whole story at small sizes, and it
   is drawn from the same `queueLen` the seats see in `detectors`.
3. **Green-wave visualisation** (the idea's ask) — on a `wave` event a bright band sweeps the corridor's
   lane in the direction of travel at the platoon's speed, the four stop lines on that corridor flash
   green in sequence, `#bannerlane` reads `ROW C EASTBOUND WAVE — 5 CARS, 4 SIGNALS CLEAN`, and a
   per-corridor tally (`8` tiny bars, one per arterial, labelled `A B C D 1 2 3 4`) in the top band
   increments. The tally bars also show each corridor's current phase pattern as four coloured pips, so a
   spectator can see an offset being set up before the wave happens — a miniature time-space diagram.
4. **Spillback and gridlock alarms** — an amber `SPILLBACK` chip while any link is full, listing up to
   three link ids; a red **`GRIDLOCK`** chip while a ring is active, with every ring link outlined in red,
   a red cross on each blocked stop line, and `#bannerlane` reading `GRIDLOCK — B3 · C3 · C2 · B2 RING,
   34 TICKS`. On clear: `GRIDLOCK BROKEN — C2 DRAINED`. A ring still active at the end turns the endcard
   headline red.
5. **Clock** — `#clock` shows the big numeral `THROUGH 372` with `/ 260 par` beneath it; `#clock-time`
   shows `tick 241/256 · turn 31/32`; `#clock-caption` shows
   `demand 386 · waiting 3142 · spillback 2 · gridlock 0 · waves 11`.
6. **Scorebug plates** — four plates (two in `#plates-l`, two in `#plates-r`): the seat's **real policy
   name** (spectator side only), its in-game alias, its quadrant (`NW`…`SE`), its colour chip, its
   `served` count as the numeral, its waiting figure, and a `↯` glyph on any seat that has taken a
   fallback.
7. **Queue-pressure rail** — a labelled rail in the **top** band, four rows, one per controller, sorted by
   waiting **ascending** (best first): alias, colour chip, real policy name, `served`, `waiting`, and a
   bar whose length is that seat's share of the network's waiting. It re-sorts live, so a controller
   losing control of its quadrant is visible as its bar overtaking.
8. **Match feed** (`#killfeed`) — plain language, never internal notation: `C2 → EWG (eastbound green)`,
   `GAMMA sets C2 to EWG at +6 — offset behind C1`, `ROW C EASTBOUND WAVE — 5 CARS`,
   `SPILLBACK C2→C3 — DELTA'S BLOCK IS FULL`, `GRIDLOCK — B3 · C3 · C2 · B2 RING`,
   `A2 STARVED — LEFT LANE BLOCKED 60s, CITY FORCED NSL`, `nA3 GATE QUEUE FULL — TURNING CARS AWAY`,
   `300 CARS THROUGH`, `Alpha: "B2 goes EWG at tick 66, eastbound platoon of 5 is yours at 72"`, and
   `BETA MISSED THE CALL — greedy phases (timeout)`. The radio lines and the order lines are where a
   spectator sees the LLM playing.
9. **Throughput sparkline** — the starter's `#momentum` SVG retargeted to two cumulative series (cars out,
   and cars rejected at the gates) with the **gridlock spans shaded red** and the spillback spans shaded
   amber behind them, and the playhead marked. Filled from the load-time pre-scan, so it draws at full
   width on the first frame. A flat stretch under a red shade is the whole story of a bad episode in one
   glance.
10. **Endcard** — `372 OF 386 CARS THROUGH — PAR 260 MET`, the four-seat table under the re-mapped header
    (`Controller | Served | Waiting | Waves | Spillbacks`), a city summary line (`11 green waves, 26
    spillbacks, 1 gridlock, 3142 car-seconds lost, 14 turned away`), and `CITY SCORE 371985000`. It stops
    at `var(--band)` and any seek dismisses it.
11. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull = 40
    consecutive ticks with no `wave`, `spillback`, `gridlock`, `starve` or `gatejam` event and fewer than
    two `exit` events, from the pre-scan), spoilers switch, tick readout, speed chips, the scrubber with
    its five beat kinds, and `#mmwarn` on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no solid-colour
squares, no downloads.** The road surface is `data/arena_floor.png`, tiled and darkened 30 %, with the
block interiors (the sixteen city blocks between the streets) textured from `client/art/walls/wall_h.jpg`
and `wall_v.jpg` and edged with a baked kerb — one pixie bake at install, exactly the way the starter
bakes endzone paint. Lane markings, stop lines, zebra crossings, turn arrows, gate arrows and the
intersection labels (`A1`…`D4`, set in `data/font.ttf`) are baked onto the same bed in the palette from
`data/pallete.png`. **Signal heads** are baked once: 4 facings × 3 lamp states (red / amber / green) = 12
chips, a three-lamp housing with a visor. **Cars** are baked at load by `rig_art.nim`'s compositor: 4
facings × 5 body colours (drawn from `data/pallete.png`) × 3 sizes, plus a chevron variant for
through-runners = **120 chips**, so drawing 500 cars a frame is 500 blits. Quadrant tints and the
controller-alias corner labels use the four `data/soldier_{red,blue,green,yellow}.png` palette entries;
the four `data/soldier_*_front.png` sprites are the controllers' avatars on the scorebug plates. The
loading screen is the starter's locker room (`client/art/lockerroom/bg.jpg` plus the four colour webps)
with the caption re-labelled. The queue heatmap, the wave sweep, the gridlock outline and the sparkline
are procedural in the bed bake's palette.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at desktop
width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (`replay_broadcast.html:4307-4312`). The board's aspect is `34/26 = 1.308`; in a 360 × 203 frame
`boxW / availH = 1.77 > 1.308`, so **height binds**: the board renders at 265 × 203, i.e. **7.8 px per
cell**, and the whole city is in frame — which is why `#viewpanel` is dropped. A car chip is 6 px, a
signal lamp 2 px in a 6 px housing, an intersection label 7 px, a heatmap band 2 px along the lane. Five
rules are added and asserted by `tests/test_signals_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `alias + name + served`; the colour chip shrinks to 6 px, the
   quadrant tag drops, and the fallback glyph moves inline.
3. Under `.tiny`, **intersection labels are drawn only on the four corner intersections** and the
   **queue heatmap becomes the primary readout** — car chips drop their chevrons and render as 4 px
   dashes, at `--hudscale`-derived sizes so nothing is drawn outside the canvas
   (`--strict-text-bounds` stays on).
4. Under `.tiny`, the corridor tally shows 8 bars with no letters (the row/column labels move to a
   tooltip), and the pressure rail drops the `waiting` figure, keeping alias + name + `served` + bar.
5. Under `.tiny`, the gridlock chip is the word `GRIDLOCK` plus its tick count only, and the banner
   truncates the ring list to the first two intersection ids plus `+N`.

---

## Packaging

- **Repo**: `Metta-AI/cogame-sumo-traffic-signals`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `sumo-traffic-signals`; **`game.name` is
  `sumo-traffic-signals`** — identical to the slug, so the secret namespace
  `secret://coworld/sumo-traffic-signals/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the commons-family 2026-08-24 scar, where
  `game.name` and the slug differed by an underscore).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the compose
  service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services/two images; this
  fork uses the one-image / two-entrypoints shape because the shared `docker_smoke.sh` and
  `policies.json` assume a single image (the knights-archers precedent):

  ```yaml
  services:
    sumo-traffic-signals:
      image: coworld-sumo-traffic-signals:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{SUMO_TRAFFIC_SIGNALS_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:sumo-traffic-signals
  src/sumo_traffic_signals.nim` → `/bin/sumo-traffic-signals`, and the same for
  `src/sumo_traffic_signals_player.nim` → `/bin/sumo-traffic-signals-player`. The runtime stage copies
  both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/sumo-traffic-signals"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned nimby
  with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with the
  asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/soldier_{red,blue,green,yellow}{,_front}.png`, `data/font.ttf`, `client/art/walls/*`,
  `client/art/lockerroom/*`, `signals_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`,
  `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape, with
  these decisions:
  - `$schema` present; top-level `tags: ["traffic", "signals", "cooperative", "city", "coordination"]`
    (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0); **`episode_timeout_minutes: 20` at the top
    level**, not under `game`.
  - `game.name = "sumo-traffic-signals"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`,
    `game.runnable.run = ["/bin/sumo-traffic-signals"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/sumo-traffic-signals/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 4/4, `players` 4/4, `slots` 0/4 — the tandem 0.1.0 scar). `tokens` is described as
    runner-injected; **no `game_config` anywhere in this manifest contains a literal `tokens` array**
    (matriculate rejects "game_config must not include runner-managed tokens" — knights-archers 0.1.0),
    while `config_schema` keeps *requiring* it because the runner injects it. Properties: `tokens`,
    `players`, `slots`, `seed`, `turnTicks`, `maxTicks`, `ewLinkCells`, `nsLinkCells`, `ewGateCells`,
    `nsGateCells`, `gateQueueCap`, `minGreenTicks`, `clearTicks`, `maxRedTicks`, `demandWarmPermille`,
    `demandPeakStart`, `demandPeakPermille`, `demandPeakEnd`, `demandDeclinePermille`, `demandEndTick`,
    `throughRunnerPermille`, `parThroughput`, `ringTicks`, `gridlockStallTicks`, `waveVehicles`,
    `waveWindow`, `waveCrossings`, `switchMargin`, `greenCap`, `attempt1Ms`, `retryMs`, `turnBudgetMs`,
    `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`, `minPlayers`,
    `fastMode`, `showPlayerLabels`, `model`, `maxOutputTokens`, and `num_agents`
    (integer, `minimum: 4`, `maximum: 4`, default 4).
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` and
    `endRule: {"type":"string","enum":["cleared","gridlock","fullPeriod","wallClock","fault"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-sumo-traffic-signals/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"signals.md","title":"Controlling the signals","content":{"type":"uri","value":".../docs/SIGNALS.md"}},
    {"id":"porting.md","title":"What this is and is not a port of","content":{"type":"uri","value":".../docs/PORTING-SUMO-RL.md"}}]}`.
  - Top-level `player[]` with `id` / `type` / `name` / `description` / `image` / `run` / `source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must be at
    least `"1"`** (pistonball 0.1.1). Two entries, `greedy` and `fixedcycle`, so **every declared player
    occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 4` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "grid4x4", "name": "4x4 grid (4 controllers, 16 signals)",
     "description": "Sixteen signalised intersections on a 4x4 city grid, four controllers with a quadrant each. Cars enter from sixteen edge gates over a 208-second peak and drive fixed shortest routes; approaches are single-lane and blocks hold four to six cars, so a green into a full block moves nobody. Everyone is scored on the same number: how many cars got out of the city.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Gamma"}, {"name": "Delta"}],
                     "num_agents": 4, "minPlayers": 4,
                     "turnTicks": 8, "maxTicks": 256,
                     "ewLinkCells": 6, "nsLinkCells": 4, "ewGateCells": 4, "nsGateCells": 3,
                     "gateQueueCap": 12,
                     "minGreenTicks": 4, "clearTicks": 2, "maxRedTicks": 60,
                     "demandWarmPermille": 60, "demandPeakStart": 32,
                     "demandPeakPermille": 180, "demandPeakEnd": 144,
                     "demandDeclinePermille": 80, "demandEndTick": 208,
                     "throughRunnerPermille": 450, "parThroughput": 260,
                     "ringTicks": 20, "gridlockStallTicks": 40,
                     "waveVehicles": 4, "waveWindow": 16, "waveCrossings": 3,
                     "switchMargin": 2, "greenCap": 6,
                     "attempt1Ms": 9000, "retryMs": 4000,
                     "turnBudgetMs": 14000, "turnSpacingMs": 12000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "rushhour", "name": "Rush hour (4x4, 4 controllers, heavy arterial demand)",
     "description": "The same city under a demand peak a third higher and two thirds of it running the full length of an avenue. Gate queues overflow, blocks fill in seconds and one badly timed green closes a ring: the hard version, where holding a green you cannot use is the difference between four hundred cars through and a frozen city.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Gamma"}, {"name": "Delta"}],
                     "num_agents": 4, "minPlayers": 4,
                     "turnTicks": 8, "maxTicks": 256,
                     "ewLinkCells": 6, "nsLinkCells": 4, "ewGateCells": 4, "nsGateCells": 3,
                     "gateQueueCap": 12,
                     "minGreenTicks": 4, "clearTicks": 2, "maxRedTicks": 60,
                     "demandWarmPermille": 80, "demandPeakStart": 24,
                     "demandPeakPermille": 240, "demandPeakEnd": 160,
                     "demandDeclinePermille": 120, "demandEndTick": 208,
                     "throughRunnerPermille": 650, "parThroughput": 380,
                     "ringTicks": 20, "gridlockStallTicks": 40,
                     "waveVehicles": 4, "waveWindow": 16, "waveCrossings": 3,
                     "switchMargin": 2, "greenCap": 6,
                     "attempt1Ms": 9000, "retryMs": 4000,
                     "turnBudgetMs": 14000, "turnSpacingMs": 12000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 4` again, inside `certification.game_config`, and exactly four
  players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 4`
  (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with **both** declared players
  seated:

  ```json
  "certification": {
    "players": [{"player_id": "greedy"}, {"player_id": "fixedcycle"},
                {"player_id": "greedy"}, {"player_id": "fixedcycle"}],
    "game_config": {"players": [{"name": "Alpha"}, {"name": "Beta"}, {"name": "Gamma"}, {"name": "Delta"}],
                    "num_agents": 4, "minPlayers": 4, "seed": 42,
                    "turnTicks": 8, "maxTicks": 256,
                    "ewLinkCells": 6, "nsLinkCells": 4, "ewGateCells": 4, "nsGateCells": 3,
                    "gateQueueCap": 12,
                    "minGreenTicks": 4, "clearTicks": 2, "maxRedTicks": 60,
                    "demandWarmPermille": 60, "demandPeakStart": 32,
                    "demandPeakPermille": 180, "demandPeakEnd": 144,
                    "demandDeclinePermille": 80, "demandEndTick": 208,
                    "throughRunnerPermille": 450, "parThroughput": 260,
                    "ringTicks": 20, "gridlockStallTicks": 40,
                    "waveVehicles": 4, "waveWindow": 16, "waveCrossings": 3,
                    "switchMargin": 2, "greenCap": 6,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  256 ticks of scripted play is well under a second of sim, but the replay is 256 ticks ⇒ **17.1 s of
  playback**, which the viewer soak needs. Seed 42 is asserted by `tests/test_signals_engine.nim` to
  produce a fixture episode with `throughput > 0`, at least one `spillback` event and at least one `wave`
  event, so the smoke replay always exercises the congestion and the wave paths. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 covers start + connect grace +
  play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/sumo-traffic-signals-player"`,
  following the starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"signals-greenwave","run":"/bin/sumo-traffic-signals-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"greenwave"}},
   {"name":"signals-gatekeeper","run":"/bin/sumo-traffic-signals-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"gatekeeper"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"signals-greedy","run":"/bin/sumo-traffic-signals-player",
    "env":{"PLAYER_SCRIPTED":"greedy","PLAYER_POLICY_LABEL":"greedy"}},
   {"name":"signals-fixedcycle","run":"/bin/sumo-traffic-signals-player",
    "env":{"PLAYER_SCRIPTED":"fixedcycle","PLAYER_POLICY_LABEL":"fixedcycle"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1, uploaded
  while daveey-1 is the active player); the fillers are `greedy` and `fixedcycle`, and their versions must
  differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `sumo-traffic-signals`,
  `<IMAGE>` → `coworld-sumo-traffic-signals`, `<SEATS>` → **`4`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0`
  (§Server) and `--soak 10` added to the `viewer_smoke.mjs` invocation (which already passes
  `--strict-text-bounds`). `coworld-release.yml` and `coworld-submit.yml` are the templates, with
  `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh` and
  `tools/build_replay_viewer.sh` are committed **executable** (mode 100755) — CI asserts the bit and
  invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_signals_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_signals_sim.nim`)
1. `city topology` — 16 intersections, 16 gates, 80 directed links, 352 cells; every intersection has
   exactly four approaches and four exits; every gate is both a source and a sink; the board is 34 × 26
   cells; the quadrant map is exactly the table in §The game.
2. `routes` — every (gate, gate) pair has a route; no route requires a U-turn; every route's cost equals
   the sum of its links' cell counts; the route table is byte-identical across two builds (the tie-break
   is total).
3. `free flow` — a single car on an empty network covers one cell per tick and its travel time equals its
   route cost plus its stop-line waits; with all signals green for it, zero waits.
4. `single lane, one discharge per approach per tick` — an approach never discharges two cars in one tick;
   an intersection never discharges more than two.
5. `left-turn blocking` — a left-turner at the head of an approach under `NSG`/`EWG` blocks every car
   behind it, takes `blockedByPhaseTicks`, and is released exactly on the first tick of the matching left
   phase.
6. `spillback` — a car on green whose receiving link's entry cell is occupied does **not** move, takes
   `spillbackBlockedTicks` and a wait tick; the link's `full` flag raises `spillback` and clears
   `spillclear`; an exit link never blocks.
7. `phase machine` — `minGreenTicks` defers a change (counted, retried, never dropped); every change costs
   exactly `clearTicks` of all-red with no discharge; `phasechange` fires when clearance ends, not when it
   starts.
8. `starvation override` — a stop-line car blocked by the phase for exactly `maxRedTicks` forces the
   serving phase, emits `starve`, latches for `minGreenTicks`, and then returns control to the seat's
   order with `last_order_result == "overridden"`; a car blocked by **spillback** never triggers it.
9. `demand is a pure hash` — the `(gate, tick) → (generated, throughRunner, destination)` table for a seed
   is identical under two completely different seat behaviours; a full gate queue rejects and counts
   without disturbing the hash; `demandGenerated` counts rejections.
10. `gate queues` — capacity 12; the head enters only when cell 0 is free; a queued car accrues wait ticks
    charged to the seat owning the intersection the gate feeds.
11. `wait accounting` — a car that advances accrues no wait tick; a car that does not, accrues exactly
    one, charged to the downstream intersection's owner; `Σ seatWaitTicks == networkWaitTicks` for every
    tick of a 256-tick episode.
12. `gridlock ring` — a constructed four-link ring of full links raises `gridlock` at exactly `ringTicks`,
    names all four links and their intersections, and clears the tick one link discharges; a queue behind
    a starved-but-serviceable approach is **not** a ring; the DFS returns the same cycle on every run.
13. `green wave` — four cars crossing three consecutive intersections with zero waits inside `waveWindow`
    raises exactly one `wave` on the right corridor and direction; a fifth car does not raise a second
    inside the same window; a car that stops once resets its `cleanCrossings` to 1.
14. `scoring` — `scores[s] == 1_000_000*throughput − 1_000*netWaitK − 10*seatWaitK[s]` over 500 randomised
    end states; the analytic bounds `netWaitK ≤ 696 < 999` and `seatWaitK ≤ 71 < 99` hold; the
    lexicographic dominance holds (one more car beats any penalty difference; one network wait unit beats
    any seat penalty); all four `win[s]` equal; `winner` null.
15. `end conditions` — `cleared`, `gridlock`, `fullPeriod`, a forced wall-clock stop and a forced fault
    each produce the right `endRule` and the right episode `reason`; a wholly frozen city settles on
    `gridlock` with the alarm recorded; a city that empties before `maxTicks` settles on `cleared`.
16. `no floating point in the sim` — a source grep over
    `src/signals/{sim,city,vehicles,phases,flow,driver,baselines}.nim` finds no `float`, `/`, `sqrt` or
    float literal.
17. `tick budget` — 256 ticks of a full `rushhour` episode complete in < 2 s in a release build.

**Bounded orders / legality on the scripted baselines** (`tests/test_signals_driver.nim`)
18. `baselines are bounded` — for 200 pseudo-random world states (varying demand phases, queue patterns,
    spillback and gridlock states, both variants, every slot) and for **both** `greedy` and `fixedcycle`:
    the returned reply has at most 4 orders, every `at` is one of that seat's four intersections and
    appears at most once, every `verb` is in the enum, every `phase` is in the enum and never `CLR`, every
    `delay` is 0…6, `say` and `notes` are empty, and the serialised directive is ≤ 1024 bytes. A baseline
    that ever proposes an illegal or unbounded order fails the build.
19. `driver never requests an illegal state` — over the same states, every requested phase is one of the
    four, no order can produce a discharge during clearance, and no order can leave a signal without a
    phase.
20. `fallback is the greedy proc` — the decision engine's fallback path and the `greedy` baseline resolve
    to the same proc, so they cannot drift; `auto` and `greedy` share one `served()` implementation.
21. `reply validation` — the validator accepts the schema, **repairs** an invalid order to that
    intersection's previous order, drops orders for intersections the seat does not own and duplicate
    `at`s, clamps `delay`, rejects `CLR`, accepts a `say`-only reply, rejects a non-object, truncates
    `say`/`notes` on **rune** boundaries at 120/240 with 4-byte emoji sitting on the boundary, caps the
    read at 4096 bytes, caps `orders` at 4, and never leaves a signal without an order.
22. `baseline tuning is the swept pick` — the shipped `switchMargin` / `greenCap` / queue-counting rule
    equal `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep
    with `--check`).
23. `greedy exports congestion` — a scripted-only episode with all four seats on `greedy` produces at
    least one `spillback` event on the shipped `rushhour` demand, and `fixedcycle` produces strictly more
    `networkWaitTicks` than `greedy` on seed 42 — the two controls are actually different controllers, not
    the same one twice.

**End-to-end episode writing a replay** (`tests/test_signals_engine.nim`)
24. `episode writes artifacts` — run a real four-seat episode (`grid4x4`, all seats scripted, no API key so
    the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the
    `.replay` are written, `reason == "complete"`, `throughput > 0`, `scores` agree with the formula, and
    the results key set equals the manifest's `results_schema` key set **exactly**.
25. `the cert seed is interesting` — seed 42 on `grid4x4` yields `throughput > 0`, at least one
    `spillback` and at least one `wave` inside 256 ticks, so the CI smoke replay always exercises both
    paths.
26. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at all,
    both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure payload;
    the server refuses to start the game (loudly) when a joined seat has no register record.
27. `budget guard and rate guard settle early` — with each guard forced, the episode finishes `complete`,
    not `deadline`, and the matching record names the turn.

**Replay** (`tests/test_signals_replay.nim`)
28. `record then re-derive, every end reason` — for `cleared`, `gridlock`, `fullPeriod`, `wallClock` **and**
    `fault`, record an episode and re-derive it from the bytes; assert identical hashes at every tick
    **including the stop tick** (the particle-worlds scar).
29. `replay is self-sufficient` — the bytes alone yield seat names, aliases, quadrants, policy kinds, the
    full config (every constant in §Server's config-JSON row), the seed, the variant, every order record,
    every chat record and the result.
30. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every capped
    field is filled to exactly its cap with 4-byte emoji; assert the output parses under a **strict**
    UTF-8 JSON parser, contains no lone surrogates, and reports `protocol == "signals/v1"`.
31. `determinism from the replay alone` — re-simulate from the replay's seed and order records on a fresh
    sim; identical final tick, throughput, wait totals and per-tick `gameHash`.
32. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_signals_manifest.nim`)
33. `manifest pins` — `num_agents == 4` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; `len(player) == 2` and every declared player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 4`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 660`; `game.name` equals the
    slug and the secret URI's namespace; **and every variant's `game_config` actually constructs a valid
    `GameConfig`, builds the city, and produces the link lengths, `parThroughput ≤` the expected demand,
    and the 32-turn schedule this note claims** (the collab-cooking 0.1.1 scar: test every variant, not
    just the fixture).
34. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_signals_viewer.nim`, static assertions in the `test` job)
35. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, pinned as a literal.
36. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the documented
    splice marker and only appends after it; `broadcast_core.js`'s kept procs are byte-identical to the
    starter's, `pushFeed`'s signature included.
37. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (`replay_broadcast.html:1635`, the tandem hoisting trap); the beat
    builder is `cityBeat`, never `markBeat`.
38. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{wave, spillback, gridlock, fallback, end}`.
39. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band; the
    five `.tiny` rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#zoom-*`, `#fpv*`,
    `#povBadge`) appear nowhere.
40. `endcard labels` — `tests/test_signals_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
41. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
42. `events are the closed enum` — `tests/test_signals_events.nim`: the set of kinds `stepEvents` can emit
    equals exactly the fifteen listed in §Server, and every kind used by the appended game block is in
    that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**
43. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded as
    the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm module
    and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
44. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the feed's radio text path (the cogchemists 2026-08-24 scar). The
    fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only the
    wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) — driving the
    real page with a full-cap 120-rune `say` on all four seats, a fully populated pressure rail, an active
    gridlock ring across four links, two full gate queues and a green-wave banner, at several canvas
    widths including 360 px.
45. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm module
    against the committed fixtures, kept: wasm32-only failures (integer traps, address-space exhaustion)
    are invisible to the native shards.

---

## Out of scope (v1)

- **Real-city networks: Cologne, Ingolstadt, Manhattan.** v1 ships one topology, the 4 × 4 grid, in both
  variants. An OSM/SUMO net import would bring XML parsing, irregular geometry that cannot be re-derived
  in the viewer from a variant name, and intersections with five or six approaches whose phase plans the
  reply schema does not express — and none of it is legible at 360 px.
- **Any SUMO or CityFlow dependency, and bit-exactness with SUMO-RL or RESCO.** Decided as a scoping rail
  before design and recorded in `docs/PORTING-SUMO-RL.md`: no upstream code is vendored, no upstream
  numbers are claimed as reproduced, and no benchmark score is comparable. This coworld implements the
  control problem, not the simulator.
- **Seat counts other than 4, and intersection counts other than 16.** The idea's "4–48 intersections" is
  answered at 16 with **`num_agents` fixed at 4** in every variant and in the cert fixture. More seats is
  a wall-clock and sidecar-rate problem (§The game → seats), not a design one; more intersections is a
  legibility pass at 360 px.
- **One seat per intersection.** The batch-size arithmetic in §The game forbids 16 seats. A
  one-intersection-per-seat variant would need a different cadence and a different manifest.
- **Continuous vehicle dynamics.** No car-following model, no acceleration, no lane changing, no
  multi-lane approaches, no turning-lane geometry, no start-up lost time, no pedestrians, no transit
  priority, no emergency-vehicle pre-emption. Cars are one per cell at one cell per tick.
- **Actuated detection loops, adaptive plans and cycle-length control as first-class orders.** A seat sets
  a phase, an offset, a hold, or delegates to `auto`; it cannot set a cycle length, a split table, or a
  detector rule. Those are §Out of scope precisely because `wave` already expresses the coordination the
  idea is about with one integer.
- **Scoring green waves, or scoring lateness/travel time directly.** `greenWaves`, `travelTicksTotal`,
  `stopsTotal` and `rejected` are measured, recorded in `results`, shown on the endcard and drawn in the
  feed, and deliberately **not** in `scores` (§The game). Paying for waves would let a seat farm the
  metric on an empty corridor; paying for travel time would need a magnitude the idea does not pin and
  would risk inverting the lexicography.
- **Sharing a city with coworld 08 Gridlock.** The idea suggests the two could share a map. That is a
  cross-coworld integration with a shared network format and a shared tick contract; v1 ships
  standalone.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, fog-of-war rendering, the
  first-person PIP, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches, perks,
  handicaps, lives, teams, four-team play, shouts, achievements, campaign mode, multi-game episodes, the
  procedural map generator, the map pool, the map editor and mapkit — all deleted, not disabled
  (§Sim module), and none of them return in v1.
