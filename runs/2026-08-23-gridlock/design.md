# gridlock — design note (2026-08-23)

`Metta-AI/cogame-gridlock`, a four-fleet parcel-delivery Coworld played on one shared signalised
9 × 9 road grid: each seat is a single policy routing fifty vehicles through a city whose
intersections have hard capacity and whose lanes spill back into the intersections behind them, so
the fastest, greediest routing plan is the one that builds the jam everybody — including its author
— then sits in. It is forked from **`Metta-AI/coworld-ctf` (paintbot)**, read at its read-only mount
`/workspace/starters/coworld-ctf`. **Every convention there holds here unless this note says
otherwise.** The starter is pinned by game shape: gridlock is a real-time tick loop with rules
written fresh for this coworld — nothing pre-exists to port, so it is the first row of the starter
table in `prompts/10-design.md` §"Starter table" and `playbooks/make-coworld.md` §Phase 0, never
`cogame-moba` — and paintbot already ships every piece a many-bodies real-time game needs: a 24 Hz
integer step loop (`src/ctf/sim.nim`, `TargetFps`/`ReplayFps` = 24 at
`src/ctf/sim_types.nim:294,353`), a recorded-input replay whose playback re-runs the sim
(`src/ctf/replays.nim`, `src/ctf/replay_runtime.nim`), a **static wasm replay viewer that re-derives
every frame in the browser** (`replay-viewer/ctf_replay.nim`, `replay-viewer/config.nims`,
`Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`), a broadcast chrome whose scorebug is
already generated **per active team for 2–4 teams** (`ensureScorebug(teams)`,
`client/replay_broadcast.html:1486,2159-2190`) and whose relayout loop is already authored down to a
360 px board (`--hudscale`, `client/replay_broadcast.html:40-42,4091-4121`, and the `.tiny` easing at
`client/replay_broadcast.html:1424-1428`), a per-tick state digest (`gameHash`,
`src/ctf/sim_state.nim`), and a bake-then-serve mummy server (`src/ctf/server.nim`) already speaking
the `bitworld/runtime` `COGAME_*` artifact contract.

One server-side module has no counterpart in paintbot and is taken in shape (not by file copy) from
the builder's other mounted starter `Metta-AI/cogame-bullwhip`
(`/workspace/starters/cogame-bullwhip`): the **LLM client with a one-parallel-batch-per-turn decision
loop** — `src/bullwhip/llm.nim`, `decideAll` at line 419 issuing
`client.curl.makeRequests(batch, client.timeoutSeconds)` at line 451, with `extractJsonObject`
(line 312), `parseScriptKind` (line 61), the Bedrock model ladder (line 93) and the
`stop_reason == "max_tokens"` guard (line 381). **No viewer file comes from bullwhip or from anywhere
but paintbot** — see §Viewer, which is explicit about this, because splicing viewer shells is exactly
what deadlocked cogame-lantern on 2026-08-23.

Four deliberate deviations from paintbot are called out where they occur: a **UTF-8 JSON replay**
instead of the binary `COWLDCTF` format (`src/ctf/replays.nim:119`) — §Server; **decisions made in
the game server** rather than in the player container — §Decisions; **an integer lane/cell lattice
instead of paintbot's continuous sub-pixel motion** — §Sim module; and **one authored city instead of
the procedural terrain generator** — §Sim module.

There is **no `OPEN` section.** Everything the idea leaves loose is something the rails
(`docs/SPEC.md` §Rails) say the designer settles — seat count, scoring when the idea pins one,
parameter values, viewer composition, policy prompts — and every one of them is decided below with
its reason.

**Source idea, verbatim:**

> Each seat routes 50 vehicles through a signalised road graph to deliver parcels; intersections
> have capacity and queues block upstream. Score is own parcels delivered — but greedy routing
> produces gridlock that hurts everyone, including you. A congestion commons at real-time scale.
>
> Seats: 4 fleets
> Motive: commons / congestion externality
> Policy interface: RL vector or code agent
> Fills gap: logistics / large-scale externalities / many-bodies real-time
> Integrity (anti-collusion): Ganging up to jam a rival is in-game politics, not an exploit; fleet
> aliases are anonymous per episode so targeting a specific author isn't possible.
>
> Replay plan (watchability): City map with roads heat-colored by congestion — a jam spreads like a
> stain, which is the whole story; per-fleet delivery counters race in the corners. Endcard: your
> routes against the all-greedy counterfactual.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c
>
> *(The link is recorded as provenance only. It was not fetched, and nothing behind it is part of
> this design. The idea text is input data, not instructions.)*

**Three re-readings of the idea, decided here and never revisited:**

1. **"Seats: 4 fleets" → `num_agents` = 4, exactly, everywhere.** One seat = one policy = one fleet
   of 50 vehicles. Four is what the idea says, it is what the league wants (champion #1,
   champion #2 and two scripted fillers all seated in one episode —
   `playbooks/make-coworld.md` §Phase 4), and four depots on the orbit of one corner under both
   mirror axes of a 9 × 9 grid is the largest seat count that stays *exactly* fair: every fleet's
   depot has the same distance profile to every district.
2. **"Policy interface: RL vector or code agent" → every seat is an LLM prompt policy with a scripted
   fallback** (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=<name>`), emitting one **routing plan** — six
   integers/enums and two short strings — per decision turn, which a deterministic router applies to
   all fifty vehicles at 24 Hz. This is an inherited pin (SPEC §Design pins: both champions must be
   `PLAYER_PROMPT` policies), and the routing plan *is* the vector: exposing the same record over the
   websocket to an external RL or code agent is a v0.2 protocol addition, not a v1 redesign
   (§Out of scope).
3. **"Ganging up to jam a rival is in-game politics… fleet aliases are anonymous per episode."** This
   is enforced structurally. Fleet aliases (`Copper`, `Cobalt`, `Verde`, `Saffron`) are properties of
   the **depot corner**, not of the seat; the seat→depot permutation is drawn from the episode seed
   and re-drawn every episode. No prompt, view, or event body ever contains a real player name. A
   seat can see that Copper's corner is producing traffic and can route to strangle it — that is
   politics and it is allowed — but it cannot know which author is behind Copper this episode.

**Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and
where each is satisfied:**

| Pin | How gridlock satisfies it |
|---|---|
| Starter by game shape | `Metta-AI/coworld-ctf` (paintbot) — any real-time game loop with rules written for this coworld; it supplies the 24 Hz loop, the re-simulating replay, the static wasm viewer and the 2–4 team chrome (title paragraph). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-gridlock`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). §Packaging. |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts) vs `PLAYER_SCRIPTED=dispatcher` / `PLAYER_SCRIPTED=beeline`; one image `coworld-gridlock:latest`, players run `/bin/gridlock-player`. §Decisions, §Packaging. |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by `tools/build_replay_viewer.sh` (forked from paintbot's). §Viewer, §Packaging. |
| Real art, starter chrome verbatim | Paintbot's `client/replay_broadcast.html` chrome block, ids and `client/chrome_common.js` kept verbatim (id-for-id list in §Viewer); painted asphalt, painted intersections, authored van sprites, authored depot art. No placeholders. §Viewer. |
| Two name spaces | Prompts, views and event bodies carry only `Copper` / `Cobalt` / `Verde` / `Saffron`, re-permuted per episode; real policy names appear only in `replay.names.players`, `results.names` and the viewer's scorebug/endcard/feed. §Server, §Viewer. |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | 490 s expected worst case, 660 s engine hard stop, against a 720 s budget; arithmetic spelled out in §Decisions; every wait bounded; LLM failure → one retry → the scripted plan. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** in variant `default`, variant `rush`, and `certification.game_config`; `SMOKE_SEATS=4`. §Packaging. |

---

## The game

**Gridlock is four parcel fleets sharing one city.** Each seat owns a depot in one quadrant and fifty
identical vans. Vans load a parcel at the depot, drive to its destination address through a
signalised 9 × 9 grid of intersections, drop it, and drive back for the next one. Every intersection
serves a bounded number of vehicles per green phase; every lane holds a bounded number of vehicles,
and when a lane fills, the vehicles waiting to enter it cannot be served, so the queue backs up
through the intersection into the lanes behind it. A fleet scores one point per parcel **its own**
vans deliver. Nobody controls the traffic lights. The only levers a seat has are how its vans price
congestion when they choose a route, how patient they are about re-planning, which districts they
prefer or shun, which parcel they take next, and **how many of its vans it puts on the road at all** —
which is the commons lever, because the fleet that floods the arterials to grab the next delivery is
also the fleet that stops the city.

**Seats: `num_agents` = 4.** One seat = one fleet = fifty vehicles = 200 bodies on the board. Reason
in re-reading 1 above.

### The city

- **Nodes (intersections).** `gridCols = 9` × `gridRows = 9` = **81 intersections**, indexed
  `(ix, iy)`, `ix ∈ 0..8`, `iy ∈ 0..8`; origin top-left, +x right, +y down. Node `(ix, iy)` sits at
  pixel `(64 + 112*ix, 64 + 112*iy)`, so the board is **1024 × 1024 px** with a 64 px margin. An
  intersection is drawn as a 16 × 16 px box. *Deviation from paintbot, deliberate:* paintbot's board
  is 1235 × 659 (`src/ctf/sim_types.nim:813-814`); gridlock's is square because the city must be
  invariant under `ix → 8 − ix`, `iy → 8 − iy` **and** the 90° rotation that maps the four depots
  onto each other, which is what makes four seats exactly fair.
- **Edges and lanes.** Every horizontally and vertically adjacent node pair is joined by one road
  segment: 8 × 9 = 72 horizontal + 9 × 8 = 72 vertical = **144 segments**, each carrying **two
  directed lanes** (one per direction) = **288 lanes**, numbered `0 … 287` in a fixed order
  (horizontal segments first, row-major, `→` then `←`; then vertical segments, column-major, `↓` then
  `↑`). A lane is a chain of **`laneCells = 14` cells** of `cellPx = 8` px each (14 × 8 = 112 px, the
  node spacing exactly). Cell 0 is the cell just downstream of the lane's tail intersection; cell 13
  is the **stop line** at its head intersection. A cell holds **at most one vehicle** — that single
  rule is what produces spillback. Lanes are drawn 6 px off the segment centreline to the right of
  travel, so the two directions read as separate lanes.
- **Road classes.** A segment is an **arterial** if it lies on `ix ∈ {2, 4, 6}` (a column) or
  `iy ∈ {2, 4, 6}` (a row); everything else is **local**. That set is invariant under both mirrors and
  under the 90° rotation. Arterials are cheaper to plan over and discharge twice as fast at
  intersections; they are also where everyone's greedy plan goes, which is the point.
- **Districts.** The node grid is partitioned into a **3 × 3 district grid**; district `(bx, by)`
  covers `ix ∈ [3bx, 3bx+2]`, `iy ∈ [3by, 3by+2]`, nine nodes each. Districts are how a policy names a
  place (`corridor`, `avoid`), how the view reports congestion, and how the viewer labels the map.
  Their display names are fixed: `NW N NE / W CENTRE E / SW S SE`.
- **Depots.** Four, one per quadrant, at the orbit of `(1, 1)`:

  | Depot | Node | Fleet alias | Hex |
  |---|---|---|---|
  | `D0` | (1, 1) | Copper | `#e07a3f` |
  | `D1` | (7, 1) | Cobalt | `#4a8fe7` |
  | `D2` | (1, 7) | Verde | `#5fbf6a` |
  | `D3` | (7, 7) | Saffron | `#f2c14e` |

  **Alias and colour are properties of the depot, never of the seat.** The seat→depot assignment is a
  permutation of `[0,1,2,3]` drawn from the episode seed (§Sim module, "Randomness") and re-drawn
  every episode — that is the idea's per-episode anonymisation. A depot has `dockSlots = 50` (it can
  hold the whole fleet, so a depot never blocks the road) and a load time of `loadTicks = 12`
  (0.5 s).
- **Signals.** Every intersection runs the same fixed-time, two-phase plan, and **no seat controls
  it**: cycle `signalCycleTicks = 96` (4.0 s), north–south green for the first
  `greenNsTicks = 48` ticks of the cycle, east–west green for the remaining 48, with a per-node offset
  `offsetTicks(ix, iy) = ((ix + iy) mod 4) * 24` so diagonal green waves exist for a router to ride.
  Phase at tick `t` for node `n`: `phase(n, t) = if ((t + offsetTicks(n)) mod 96) < 48: NS else EW`.
  The plan is **public and static** — it is in the config, in every replay, and described in the
  system prompt.
- **Vehicles.** `fleetSize = 50` per seat, 200 in the city. A vehicle has: an id, its fleet, a
  location (either `docked at depot` or `(lane, cell)`), a state, a route (a list of lane ids), a
  target node, and — when loaded — its parcel. Vehicles never crash, never break down, and never
  interact except by occupying cells. Vehicle states, and the codes used in the replay:

  | code | state | meaning |
  |---|---|---|
  | 0 | `docked` | at the depot: idle, loading, or loaded and waiting for a dispatch slot |
  | 1 | `loaded` | on the road carrying a parcel toward its destination |
  | 2 | `empty` | on the road returning to the depot |
  | 3 | `stalled` | on the road and did not advance a cell in the last 24 ticks |

- **Parcels.** A parcel is `{id, fleet, dest_node, created_tick}`. Every `orderPeriodTicks = 24`
  (1.0 s) each fleet receives exactly **one** new order into its backlog, which is capped at
  `backlogMax = 80` (orders beyond the cap are not created; a fleet at the cap is losing demand it
  could have served — a visible failure state). Demand is **identical up to symmetry** for all four
  fleets: the canonical destination sequence `D[k]` is drawn once from the seeded PCG stream over all
  non-depot nodes, and fleet at depot `Dj` receives `mirror_j(D[k])`, where `mirror_0` = identity,
  `mirror_1` = `ix → 8 − ix`, `mirror_2` = `iy → 8 − iy`, `mirror_3` = both. Four fleets therefore face
  the same demand pattern reflected onto their own quadrant, which makes the score comparison exact,
  and all four patterns pull through the CENTRE district equally, which is where the commons bites.

### Routing: how a vehicle chooses its next lane

Every vehicle plans over the directed lane graph with **Dijkstra** (binary heap, integer costs, ties
broken by ascending lane id). All costs are strictly positive:

```
cost(lane) = ((laneBase(lane) + jamTerm(lane) + avoidTerm(lane)) * corridorFactor(lane)) div 100

laneBase(lane)        = 48 if the lane's segment is arterial, else 64
jamTerm(lane)         = (congestion_weight * q(lane) * 24) div 100     # q = vehicles now in the lane, 0..14
avoidTerm(lane)       = 240 if plan.avoid != null and the lane's HEAD node is in that district, else 0
corridorFactor(lane)  = 60 if plan.corridor != null and BOTH endpoints are in that district, else 100
```

`q(lane)` is the lane's **current, public** occupancy, read at the instant of the plan. With
`congestion_weight = 100` and a full lane, `jamTerm = 336` against a base of 48–64: the road is
effectively closed. With `congestion_weight = 0` the router is a pure shortest-path greedy — the
behaviour that makes the jam.

A vehicle pushes itself onto a **pending-replan FIFO** when: (a) it has no route, (b) its target
changed (it just loaded or just delivered), (c) it was served into a node and the next lane on its
route has `q >= replanQueue`, where `replanQueue = 3 + (patience * 10) div 100` (patience 0 → replan
at 3 vehicles, patience 100 → replan at 13), or (d) a new turn began (every on-road vehicle of that
fleet is enqueued once, in ascending vehicle id). At most **`routeBudgetPerTick = 24`** Dijkstra runs
execute per tick, popped in FIFO order; a vehicle still waiting keeps driving its old route, and if
that route's next lane no longer starts at its node it takes the cheapest legal outgoing lane
(ties → lane id order). The budget is what bounds the per-tick cost, and it is recorded in the config
so playback re-derives the same queue.

### Time and turns

`dt = 1/24 s` (paintbot's `TargetFps`/`ReplayFps` = 24, `src/ctf/sim_types.nim:294,353`, kept). An
episode is `episodeTicks = 4800` ticks = **200 s of city time**, divided into **20 decision turns of
`turnTicks = 240` ticks (10.0 s)**. Vehicles advance at most one cell every `moveTicks = 3` ticks
(8 cells/s ⇒ 1.75 s to traverse a free lane); intersections serve every `serviceTicks = 6` ticks. At
the first tick of a turn the server freezes the state, builds all four seats' views, collects one
**routing plan** per seat as one parallel batch (§Decisions), and installs them; the router and the
traffic then run those plans for 240 ticks. The LLM is the dispatcher at 0.1 Hz; the city runs at
24 Hz.

**Capacity arithmetic, out loud (this is why the game has a jam in it at all):** a green approach
discharges 1 vehicle (local) or 2 (arterial) per service step, and is green half the time, so its
saturation flow is **2 veh/s local, 4 veh/s arterial**, while a free-flowing lane delivers vehicles to
its stop line at up to 8 veh/s. Any lane carrying more than its saturation flow queues, and a queue
that reaches 14 vehicles blocks the intersection upstream of it. Average demand is far below that —
200 vehicles doing ~5 round trips of ~12 lanes over 200 s ≈ 60 lane-traversals/s spread over 288
lanes ≈ 0.2 veh/s per lane — so jams are never global by accident. They happen exactly where four
greedy planners concentrate, which is the arterial cross and the CENTRE district.

### Resolution order (exact, per tick `t`, no exceptions)

"Fleet order" means ascending seat slot 0…3. "Vehicle order" means ascending global vehicle index
`g = seat * 50 + vehicleIndex`. "Lane order" means ascending lane id; "node order" ascending
`ix + 9*iy`.

1. **Turn clock.** `turn = t div 240`. If `t mod 240 == 0`: install the four routing plans collected
   for this turn (§Decisions), enqueue every on-road vehicle for a replan (vehicle order), roll the
   per-turn counters (`delivered_last_turn`, jam accumulators), and emit `turn_start` plus one `plan`
   event per seat.
2. **Signals.** Recompute `phase(n, t)` for every node in node order. Purely a function of `t` and the
   node offset; no state.
3. **Orders.** If `t mod orderPeriodTicks == 0`, append one parcel to each fleet's backlog in fleet
   order (destination = `mirror_j(D[k])` for that fleet's next canonical index `k`), skipping any
   fleet already at `backlogMax` and emitting nothing (the backlog size is in the view and in the
   turn-level `heat` event).
4. **Loading.** In vehicle order, every docked vehicle without a parcel and with a non-empty backlog
   begins loading: it takes the backlog order selected by `plan.priority` — `near` = smallest
   Manhattan node distance from the depot (ties → oldest), `far` = largest (ties → oldest),
   `fifo` = oldest — and becomes `loaded and waiting` after `loadTicks = 12` ticks.
5. **Dispatch (fleet metering).** If `t mod dispatchPeriodTicks == 0` (`dispatchPeriodTicks = 12`),
   for each fleet in fleet order: let `activeCap = (plan.dispatch * 50 + 50) div 100` and
   `releasePerStep = 1 + ((100 - plan.spread) * 5) div 100` (spread 0 → 6 per step, spread 100 → 1).
   While the fleet has fewer than `activeCap` vehicles on the road, fewer than `releasePerStep`
   released this step, a loaded-and-waiting vehicle available (vehicle order), and cell 0 of the first
   lane of that vehicle's route is empty, release it onto that cell in state `loaded`. Anything that
   fails leaves the vehicle docked. **This is the only place a fleet can hold itself back, and it is
   the commons lever.**
6. **Vehicle movement.** If `t mod moveTicks == 0`: for every lane in lane order, walk its vehicles
   **downstream-first** (cell 13 → cell 0); a vehicle at cell `c < 13` advances to `c + 1` if that
   cell is empty; a vehicle at cell 13 (the stop line) does not move here — it is the intersection's
   business (step 7). Downstream-first is what makes a queue discharge as a wave rather than
   teleport, and it is why the order is fixed.
7. **Intersection capacity and signal service.** If `t mod serviceTicks == 0`: for every node in node
   order, for each of its **green** approach lanes in the fixed order N, E, S, W (an approach is green
   when its travel axis matches `phase(n, t)`), discharge up to `dischargePerStep(lane)` vehicles —
   **2 for an arterial approach, 1 for a local approach** — from the stop line, oldest first. A
   discharge is legal only if the vehicle's next lane's cell 0 is empty (§8 for the exceptions where
   the node is the vehicle's target). An illegal discharge is simply not made: the vehicle stays at the
   stop line.
8. **Queue spillback.** There is no separate step for it and that is the point: because a blocked
   vehicle stays at cell 13 in step 7 and because step 6 cannot move a vehicle into an occupied cell,
   a full receiving lane freezes its feeding approach, which fills, which freezes the approaches
   feeding *it*. The invariant the tests pin is: **a vehicle only ever moves into an empty cell, and a
   stop-line vehicle only crosses when its receiving cell is empty.** A vehicle that has not advanced
   for 24 ticks flips to state `stalled` (code 3) and its stalled ticks accumulate into the jam index.
9. **Parcel pickup and delivery.** Resolved as part of a discharge in step 7, in the same order:
   - If the vehicle is `loaded` and the node it is crossing into **is** its parcel's destination:
     `delivered[seat] += 1`, the parcel is retired, a `deliver` event is emitted with the trip time,
     the vehicle's target becomes its depot, it is enqueued for a replan and it enters cell 0 of the
     first lane of its new route as `empty`. If that cell is occupied it stays at the stop line, still
     holding a service slot next step — a delivery bay that blocks the road, deliberately.
   - If the vehicle is `empty` and the node it is crossing into **is** its own depot node: it is
     absorbed into the dock (state `docked`), which never blocks (50 slots).
   - A vehicle crossing any **other** fleet's depot node does nothing: you cannot deliver to, load at,
     or steal from a rival depot.
   - Otherwise the vehicle simply enters cell 0 of the next lane on its route.
10. **Replans.** Pop up to `routeBudgetPerTick = 24` vehicles from the pending-replan FIFO and run
    Dijkstra for each with its fleet's current plan and the current `q(lane)` values.
11. **Congestion statistics.** Every tick, accumulate per-lane occupancy and per-vehicle stall ticks
    into the turn's accumulators. If `t mod 48 == 0`, compute the 3 × 3 district congestion digits and
    the city `jam_index`, and emit one `heat` event carrying both. If a lane crosses
    `jamThreshold = 11` vehicles having been below it, emit `jam`; when it falls back below 6, emit
    `jam_clear`. If **four or more** lanes whose head nodes lie in one district are simultaneously at
    `laneCells` (fully blocked), emit one `gridlock` event naming the district (at most one per
    district per 240 ticks).
12. **Keyframe.** If `t mod 24 == 0`, append a keyframe: tick, all 200 vehicles' `(lane, cell, state)`,
    the four `delivered` counters, the four on-road counts, the four backlog sizes, the city
    `jam_index`, and the u32 state digest (§Sim module).
13. **Seek snapshot.** If `t mod 240 == 0`, the *runtime* (native and wasm alike) keeps a full state
    snapshot **in memory** — all lane cells, all vehicles with routes, backlogs, the PCG state
    (≈ 120 KB; 21 snapshots ≈ 2.5 MB). Snapshots are **never written to the replay**; they exist so a
    backward seek in the viewer replays at most 240 ticks (§Viewer).
14. **End check.** If `t + 1 == episodeTicks` → end, `reason: "complete"`, `end_rule: "full_time"`.
    Else if the wall-clock stop has tripped → `deadline` / `wall_clock`. Else if `t mod 24 == 0` and
    an invariant guard fails (two vehicles in one cell, a vehicle off-graph, a `delivered` counter that
    decreased, a route whose first lane does not start at the vehicle's node after a completed replan,
    a backlog above `backlogMax`) → `fault` / `sim_fault`.

### Scoring, sign, and what the league ranks by

The idea pins it: **score is own parcels delivered.**

```
delivered[s] = parcels this seat's vehicles dropped at their destination nodes over the episode
score[s]     = float(delivered[s])          # raw count, NOT normalised
```

**Higher is better.** The sign is positive and the scale is a plain count (typical range 60–220 per
seat over the default variant). Deliberately **not** a share and **not** constant-sum: the whole
point of a congestion commons is that the total is destructible. Four greedy fleets can hold each
other to 300 parcels between them while four metered fleets clear 700, and the results document
carries `total_delivered` and `jam_index_mean` so that collapse is visible in the numbers and on the
endcard.

`win[s] = delivered[s] == max(delivered) and that maximum is unique`; `winner` is that slot index, or
`null` on a tie.

**The league ranks by Elo computed from `results.scores`** — the platform's `scores` array is the
only cross-game ranking input (Elo 1000 start, K 32, per the phase-50 league settings). A `fault`
episode scores 0 for every seat with `winner: null`: an infra fault is nobody's win and nobody's loss.

Worked example: `delivered = [163, 148, 96, 71]` → `scores = [163.0, 148.0, 96.0, 71.0]`,
`win = [true, false, false, false]`, `winner = 0`, `total_delivered = 478`.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values; `results.end_rule` carries the detail.

| `reason` | `end_rule` | When |
|---|---|---|
| `complete` | `full_time` | All `episodeTicks` simulated. The normal ending. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660 by default) elapsed before full time. The sim stops at that tick and scores the `delivered` counters as they stand. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke, and the replay is complete and self-consistent up to the stop tick. |
| `fault` | `sim_fault` | An invariant guard from step 14 tripped. All scores 0, `winner: null`, partial replay written. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

No other value may appear anywhere. A seat that never connects does **not** end the episode: its fleet
is driven by the `dispatcher` scripted baseline for the whole match, the no-show is reported to
`COGAME_PLAYER_FAILURE_URI` (lowest offending slot only, paintbot's `declarePlayerFailure` shape in
`src/ctf/server.nim`), and the match plays to `full_time`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {dispatcher, beeline}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=dispatcher`. **A scripted policy seated as a champion is a failure state**
(`playbooks/make-coworld.md` §Phase 2).

**Where the decision happens.** *Deviation from paintbot, deliberate:* paintbot's bot decides inside
its own container (`players/baseline/baseline.nim`). In gridlock the **game server** owns both policy
kinds, exactly as bullwhip does (`src/bullwhip/llm.nim`). Reasons: the hosted Bedrock sidecar
credentials and the `anthropic_api_key` coworld secret are injected into the *game* pod; phase 60
greps the *game* log for `falling back` / `LLM provider is unavailable`; "one parallel batch per turn"
is a game-server property; the shared `tools/ci/docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the
game container only; and keeping both kinds in the server makes the recorded plan stream reproducible
with no network in the loop. The player container is therefore thin: it connects, sends one `register`
frame carrying its prompt (or its baseline name), and thereafter only receives (§Server).

**Cadence and batching.** One decision every `turnTicks = 240` ticks (10.0 s of city time), **20 turns
per episode**, **one call per fleet — never one call per vehicle**. 200 bodies are driven by 80 LLM
calls in the whole episode. At each turn the server builds all four seats' request bodies and issues
them as **one parallel batch** — a single `client.curl.makeRequests(batch, client.timeoutSeconds)`
over all open seats, exactly bullwhip's `decideAll` (`src/bullwhip/llm.nim:419-472`) — wrapped in one
per-turn deadline. **Seats are never queried sequentially.** Every turn batches exactly 4 requests; at
most 4 are ever in flight.

**Sidecar rate floor.** The hosted Bedrock sidecar caps **30 requests/minute per episode** (playbook
gotcha, raid round 2, 2026-08-23). Four requests per batch means batches must start at least 8 s
apart; gridlock floors the spacing at **`minTurnSpacingSeconds = 10.0`** (24 req/min), enforced by
sleeping the remainder of the 10 s after a fast turn resolves. That floor also sets the episode's
*minimum* wall clock at 20 × 10 = 200 s.

**Wall-clock arithmetic (must stay inside 60 % of `episodeTimeoutSeconds` 1200 = 720 s):**

```
20 turns x 22.0 s per-turn ceiling                 = 440 s   (>= the 10 s spacing floor: min 200 s)
player connect wait (4 seats, typical)             =  15 s   (cap: playerConnectTimeoutSeconds 90)
sim: 4800 ticks, 200 vehicles + 288 lanes, native  =  10 s   (perf test bounds this at <= 40 s)
city bake + results + replay writes                =  25 s
                                                   -------
expected worst case                                = 490 s   < 720 s  (230 s margin)
engine hard stop wallClockBudgetSeconds            = 660 s   -> reason "deadline"
platform kill (episode_timeout_minutes 20)         = 1200 s
```

Per-tick sim cost, out loud: movement touches at most 200 vehicles every 3rd tick (≈ 70/tick × ~6
integer ops), service touches 81 nodes × ≤ 2 green approaches every 6th tick (≈ 27/tick × ~10 ops),
statistics sweep 288 lanes per tick (~600 ops), and routing is capped at 24 Dijkstra runs per tick
over 81 nodes / 288 arcs (≈ 1.8 k ops each = 43 k). Total ≈ 45 k integer ops/tick, **2.2 × 10⁸ for the
episode** — a couple of seconds in a `-d:release` native build and under ten in wasm. The perf test's
40 s bound is deliberately loose.

Typical wall clock is far under the worst case: a turn whose slowest seat answers in 5 s costs the 10 s
floor, not 22 s. With no credentials at all (offline certification, the docker smoke) the LLM client
disables itself on first discovery, the spacing floor is skipped (no requests are made), every turn
falls back instantly, and the whole episode finishes in seconds.

**Per-turn timing, per seat:** first attempt deadline **14.0 s**. On timeout, transport error,
non-JSON reply, or a reply carrying no usable plan → **one retry** with a 6.0 s deadline and the "your
previous reply was invalid" hint appended (bullwhip's retry shape). If that also fails → that seat's
plan for this turn is the **`dispatcher` scripted plan**, computed in microseconds, and a `fallback`
event is written with `cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`.
Worst case 14.0 + 6.0 = 20.0 s ≤ the 22.0 s turn budget.

**Budget guard (settle early rather than overrun).** At the start of each turn, if
`elapsed + 2 * turnBudgetSeconds > wallClockBudgetSeconds`, the LLM is skipped for **all remaining
turns** and the episode finishes on the scripted layer (< 1 ms per turn, spacing floor dropped), so it
ends `complete/full_time` instead of `deadline`. A `budget_guard` event records the turn it engaged.
Only if even that overruns — arithmetically impossible, but the check is unconditional — does the
engine stop at 660 s with `deadline/wall_clock`.

**Degrade, never hang.** Every wait is bounded: the two attempt deadlines, one outer per-turn deadline
of 22.0 s, `playerConnectTimeoutSeconds` (90 hosted, 60 in the cert fixture) on the connect wait, a
3.0 s per-seat deadline on the final done-broadcast, the 20 s post-artifact shutdown grace, and the
660 s engine stop. **The game container does not receive `COWORLD_TIMEOUT_SECONDS`** (only the worker
sidecar does); 1200 s is assumed and never approached. A seat that disconnects mid-match keeps
playing: its plan source degrades to `dispatcher` and revives on reconnect. No failure mode leaves a
fleet unactuated — a fleet always has a plan, defaulting to the previous turn's, then to `dispatcher`.

**The LLM client** (`src/gridlock/llm.nim`) follows bullwhip's `llm.nim` with gridlock's schema.
Credential ladder, in order: Bedrock sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
`AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (read through `readCogameUri`) → none (disabled, instant
fallback, one log line). Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, then
`us.anthropic.claude-sonnet-4-5-20250929-v1:0`; on a 403 the client advances to the next candidate.
**`us.anthropic.claude-sonnet-4-6` is deliberately NOT in the ladder** — it times out on every sidecar
call and one throttle cascades into scripted fallbacks (playbook gotcha, raid round 2, 2026-08-23).
`max_tokens = 900` (400 truncates), **no `output_config.effort`** (Haiku 4.5 rejects it),
`temperature = 0.4`.

**System prompt (fixed, identical for every seat and both champions, sent as the system message):**

```
You are the dispatcher for one parcel fleet of 50 vans in a city shared with three
rival fleets. The city is a 9x9 grid of intersections joined by two-way roads. Every
road holds at most 14 vans per direction. Every intersection runs a fixed 4-second
light: 2 seconds north-south, 2 seconds east-west, offset diagonally across the city.
Nobody controls the lights. A green approach lets through 1 van per service tick, or
2 on an arterial (the roads on grid lines 2, 4 and 6). If the road a van wants to enter
is FULL, it cannot cross, so it sits in the intersection mouth and the queue behind it
backs up. That is how a jam spreads.
Your depot sits in one corner. Vans load a parcel, drive to its address, drop it, and
come back for the next. One delivered parcel is one point. Your score is your own
deliveries - it is NOT a share, so nothing stops all four fleets from scoring badly at
once. That is the trap: the shortest route is the same shortest route everyone else
computed, and four fleets flooding the arterials deliver fewer parcels between them
than four fleets that spread out and meter themselves.
Every 10 seconds you set your fleet's ROUTING PLAN: how much your vans inflate the cost
of a queued road, how full a road must be before they re-plan at an intersection, how
many vans you allow on the road at once, how staggered their departures are, which
district they should prefer or avoid, and which parcel they take next. That is all.
You cannot steer one van, change a light, or talk to another fleet.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"congestion_weight":0-100, // how strongly a queued road is avoided when planning
 "patience":0-100,          // how full the next road must be before a van re-plans
 "dispatch":0-100,          // percent of your 50 vans allowed on the road at once
 "spread":0-100,            // 0 = release in bursts of 6, 100 = release one at a time
 "corridor":[bx,by]|null,   // district (0-2,0-2) your vans should prefer to route through
 "avoid":[bx,by]|null,      // district your vans should route around
 "priority":"near"|"far"|"fifo", // which waiting parcel a van loads next
 "note":"<=140 chars",      // your reasoning, shown to spectators only
 "say":"<=32 chars"}        // one short line, shown to spectators only
Districts are the 3x3 blocks of the node grid: [0,0] is NW, [1,1] is CENTRE, [2,2] is SE.
congestion_weight 0 is pure shortest path - fast when the city is empty, and the fastest
way to build a jam when it is not. dispatch below 100 is the only way to reduce total
traffic; it costs you deliveries in the short run and buys a moving city back.
```

**User message** = the seat's `PLAYER_PROMPT` text, then a blank line, then the seat's view JSON
(§Server). The prompt text is never echoed into the replay (only `policy_kind`).

**Champion #1 — `gridlock-flowwright` (owner daveey), `PLAYER_PROMPT`:**

```
Keep the city moving and you will out-deliver anyone who does not.
Read jam_index first, every single turn, before you look at your own numbers. Under 20
the city is empty: run dispatch 100, congestion_weight 25, patience 70, spread 30,
priority near, and just churn short trips. Between 20 and 45 the arterials are loading:
raise congestion_weight to 55 and drop dispatch to 85. Above 45 you are paying for
somebody's greed - congestion_weight 80, dispatch 60, spread 80, patience 25. Above 70
go to dispatch 45 and congestion_weight 95 and wait it out; a van parked at your depot
costs you nothing, and a van stalled in a queue costs you the delivery AND blocks the
road you need next turn.
Watch your own stalled_pct against jam_index. If your stalled_pct is well above the city
number, the jam is YOURS - you are self-congesting, so cut dispatch by 20 and raise spread
to 90 before you touch anything else. If it is well below, you are routing around other
people's mess and you should hold the plan for another turn.
Use avoid on the single worst district in the districts grid whenever its digit is 8 or 9
and it does not contain your depot. Use corridor sparingly: only on the ring districts
next to your own corner, and only when the CENTRE digit is 7 or more. Never corridor the
CENTRE. Everybody's addresses pull through the middle already.
priority near almost always. Switch to far for exactly one turn when your backlog is over
50 - long trips clear the backlog fastest when the roads near you are jammed anyway - then
switch straight back.
Do not thrash. A plan you keep for three turns beats three clever plans, because a van
that re-plans at every intersection spends its life turning around.
```

**Champion #2 — `gridlock-backstreet` (owner daveey-1,
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`:**

```
Let the others fight over the arterials. You take the side streets.
Stand congestion_weight high - 70 to 90 - for the whole match, almost regardless of
jam_index. Arterials are cheaper to plan over, so every greedy fleet in this city computes
the same route through the same three roads; a high congestion weight is what pushes your
vans one block off that road, where the lights are the same and the queues are empty. Your
trips will be a little longer and they will actually finish.
Always avoid the district with the highest congestion digit, and if two are tied, avoid the
one nearer the CENTRE. Set corridor to the district diagonally between your depot and your
busiest destinations, never to the CENTRE and never to a district you are avoiding.
Keep patience low, 20 to 35: you want a van to bail out of a road the moment it starts to
fill, because your whole edge is being one block away from the queue before it forms.
Run dispatch at 90 while jam_index is under 50 and drop to 65 above it. You are not the one
causing the jam, but you still cannot deliver through it, and a smaller fleet on the road
is a faster fleet on the road.
priority fifo as a habit; go near for a turn whenever your backlog is under 15, so that your
vans are doing quick loops while the arterials are locked and the other fleets are stalled.
When you see a gridlock event in a district, do not go anywhere near it for two turns. It
takes longer to drain than it looks, and the fleets that queued into it are still in there.
```

### Scripted baselines

Both emit the identical plan JSON on the same 10 s cadence, so their output is legal by construction
and directly comparable to an LLM's; both are pure functions of the seat's view, which is what makes
the bounded-orders test in §Tests meaningful.

- **`dispatcher`** — the certification player, the default, and the stronger of the two: **shortest
  path with congestion-aware repricing plus jam-triggered metering.** Every turn, from the view:
  `jam = view.city.jam_index` (0…100), `hot = ` the district with the largest congestion digit.
  ```
  congestion_weight = clamp(30 + jam, 30, 95)
  patience          = 60 if jam < 40 else 35
  dispatch          = 100 if jam < 35 else 80 if jam < 55 else 60 if jam < 75 else 45
  spread            = 40 if jam < 45 else 80
  corridor          = null
  avoid             = hot  if hot's digit >= 7 and hot contains neither your depot
                           nor any of your next 6 destinations, else null
  priority          = "far" if backlog > 55 else "near"
  note              = "dispatcher: jam=<jam> dispatch=<dispatch> avoid=<district or ->"
  say               = ""
  ```
- **`beeline`** — the second filler, deliberately weaker, and thematically the villain of the idea:
  **pure greedy shortest path at full throttle.** Every turn, unconditionally:
  `{congestion_weight: 0, patience: 100, dispatch: 100, spread: 0, corridor: null, avoid: null,
  priority: "fifo", note: "beeline: shortest path, full throttle", say: ""}`. It never reprices a
  queue and never meters itself, so a table with `beeline` seats on it jams, which is precisely the
  externality the game is about — and it gives the ladder a real spread.

---

## Sim module

`src/gridlock/sim.nim` is paintbot's `src/ctf/sim.nim` with the CTF rule surface removed and the
traffic rules put in its place. What is kept, what is dropped, what is new:

**Kept from paintbot, by path:**

- `src/ctf/sim_types.nim` → `src/gridlock/types.nim` — `TargetFps`/`ReplayFps` = 24,
  `PlaybackSpeeds = [1,2,3,4,8,16]` (`src/ctf/sim_types.nim:294,353,354`), the map-global install
  pattern, and the **flatty wire types whose field order is sacred** (paintbot's `AGENTS.md` rule; it
  still holds — the live `/global` broadcast is flatty-encoded). `GameVersion` is kept as the rules
  gate and starts at `"1"` for gridlock (paintbot's GV43 history does not travel; the prepend-only
  `GVnn (short rule name): HEADLINE` changelog-comment convention does).
  **Dropped:** the continuous-motion constant family (`MotionScale`, `Accel`, `FrictionNum`,
  `MaxSpeed`, `StopThreshold`, `PlayerHalf`, `PlayerBouncePct`, `MovementSlideMaxScan`,
  `src/ctf/sim_types.nim:337-354`). *Deviation from paintbot, deliberate:* traffic on a road network is
  a queueing lattice, not a physics sim; cells and service steps are what make spillback exact and
  what make the native and emscripten builds agree bit-for-bit with no float anywhere.
  `MapWidth`/`MapHeight` become 1024 × 1024.
- `src/ctf/arena.nim` → `src/gridlock/city.nim` — the `mapSpec`-style loader, the rect/disc/polygon
  stamping used for the painted street furniture, the mask bake, the integer even-odd
  `pointInPolygon` with its STRICT-STRADDLE convention, and the process-global install.
  **Dropped:** the procedural generator, the validators, `mapDiagnostics`, `src/ctf/map_pool.nim`,
  `src/ctf/mapgen_styles.nim` and the whole `mapSize`/`mapSymmetry`/`mapEndzone` knob family.
  *Deviation from paintbot, deliberate:* gridlock ships **one authored city**, because a road network
  whose four depots are exactly interchangeable is not something a seeded draw gives you. City variety
  is §Out of scope (v1).
- `src/ctf/sim_state.nim` → `src/gridlock/state.nim` — logging, the `gameHash` state digest, the event
  buffer. `src/ctf/sim_config.nim` → `src/gridlock/config.nim` — the `GameConfig` lifecycle and
  `configJson()`. `src/ctf/roster.nim` → `src/gridlock/roster.nim` — join/auth/slots/tokens.
  `src/ctf/events.nim` → `src/gridlock/events.nim` — the `SimEventKind` → JSON-key discipline and the
  `jsonRow` shape (`src/ctf/events.nim:14-60`), kept verbatim in shape with gridlock's kinds.
  `src/ctf/labels.nim`, `src/ctf/broadcast.nim` and `src/ctf/global.nim`'s sprite-protocol broadcast
  layer are kept (the live `/global` stream and the viewer both ride them, including the JSON-chrome
  channel that is the only chrome path surviving a hosted replay); the CTF-specific art in
  `global.nim` is replaced (§Viewer).
- `src/ctf/replay_runtime.nim` + `src/ctf/replays.nim` → `src/gridlock/replay.nim` — the
  `parseReplayBytes` / `initReplayRuntime` / `advanceReplayFrame(seekTicks, commands)` shape that the
  wasm viewer drives (`replay-viewer/ctf_replay.nim:46-113`), including the hash-mismatch surface
  (`ctf_mismatch_tick` → `#mmwarn`). The bytes it reads are JSON, not `COWLDCTF` (§Server).
- `src/ctf.nim` → `src/gridlock.nim` — the entrypoint, **including the rule that seed randomisation
  happens before `config.update`** so every seed-derived draw follows the final seed
  (`src/ctf.nim`, `seedPinned` / `stripUnpinnedSeed` / `randomSeed`, kept verbatim).

**Dropped entirely:** guns, hitscan, aim and aim jitter, the vision cone and shadowcast FOV, grenades,
the barrage, med kits, shields, the plasma arc, paint puddles, spray cans, lives / hit points /
respawn, perks, handicaps, achievements, shouts, teams-as-sides, the map editor (`tools/map_editor*`),
`tools/mapkit.nim`, the `arena/` WIT component bindings, `caos/` and `caos-tools/`. Gridlock has no
combat and no fog cone; what survives the fork is the loop, the bake, the replay, the digest
discipline, the broadcast layer and the chrome.

**New:** `src/gridlock/graph.nim` — nodes, lanes, districts, arterial classification, the Dijkstra
router and the pending-replan FIFO; `src/gridlock/traffic.nim` — cell occupancy, movement,
intersection service, spillback, stall accounting; `src/gridlock/parcels.nim` — the canonical
destination schedule, per-fleet mirroring, backlogs, loading, delivery; `src/gridlock/rules.nim` — the
turn clock, jam statistics, the invariant guards and the score; `src/gridlock/plan.nim` — the routing
plan schema, tolerant parsing, repair, and the derived router coefficients; `src/gridlock/llm.nim` —
the bullwhip-shaped client; `src/gridlock/baselines.nim` — `dispatcher` and `beeline`;
`src/gridlock/replay.nim` — the JSON replay writer/reader.

**The city file.** `data/gridcity.cityspec.json`, loaded by `cityPath: "gridcity"`, is authored (not
generated) and pinned verbatim into every replay's `city` key, exactly as paintbot pins `mapSpec`:

```json
{"name": "gridcity", "grid": [9, 9], "node_spacing_px": 112, "margin_px": 64,
 "lane_cells": 14, "cell_px": 8, "lane_offset_px": 6,
 "arterial_cols": [2, 4, 6], "arterial_rows": [2, 4, 6],
 "districts": [3, 3],
 "district_names": [["NW","N","NE"],["W","CENTRE","E"],["SW","S","SE"]],
 "depots": [{"id": "D0", "node": [1, 1], "alias": "Copper",  "colour": "#e07a3f"},
            {"id": "D1", "node": [7, 1], "alias": "Cobalt",  "colour": "#4a8fe7"},
            {"id": "D2", "node": [1, 7], "alias": "Verde",   "colour": "#5fbf6a"},
            {"id": "D3", "node": [7, 7], "alias": "Saffron", "colour": "#f2c14e"}],
 "signal": {"cycle_ticks": 96, "green_ns_ticks": 48,
            "offset_rule": "((ix + iy) mod 4) * 24"},
 "scenery": [{"kind": "rect", "x": 168, "y": 168, "w": 56, "h": 56, "art": "block_park"},
             {"kind": "disc", "cx": 512, "cy": 512, "r": 34, "art": "plaza"}, … ]}
```

`scenery` is **decoration only** — painted city blocks between the roads. It never touches the sim; a
test asserts the scenery list is invariant under both mirrors and never overlaps a lane's cells.

**Randomness.** One PCG32 stream seeded from the episode seed, integer arithmetic only, used for
exactly three things: the seat→depot permutation, the canonical destination sequence `D[k]`, and the
tie-noise added to Dijkstra costs (`rnd(0..3)` per lane per plan, so four fleets with identical plans
do not stack onto one identical route). Everything else is deterministic. The stream is advanced in a
fixed order (permutation once at init, then per tick: orders, then replans in FIFO order), so the draw
sequence is a function of the seed and the plans alone.

**State digest.** `gridlockStateDigest()` returns an FNV-1a u32 over the raw bytes of: every vehicle's
`(lane, cell, state, target node, parcel id)`, every lane's occupancy count, the four `delivered`
counters, the four backlog sizes, the PCG state, and the tick. It is paintbot's `gameHash` idea
retargeted, it goes into every keyframe, and it is the cross-build equality check that lets the wasm
viewer prove it re-derived the same match (paintbot already surfaces a mismatch as `#mmwarn` — kept,
with `mismatchQuit = false` as the default).

**Determinism contract (the inviolable property).** Same seed + same resolved plan stream ⇒ same
digest at every keyframe, in the native build *and* in the emscripten build. It holds because the
whole step is integer. **No `sin`, `cos`, `tan`, `atan`, `exp`, `ln`, `pow`, `sqrt`, `hypot`, `fmod`
or float arithmetic of any kind appears in the sim step**, and `-ffast-math` is banned; a source-grep
test enforces both (§Tests).

---

## Server, player, protocol

`src/gridlock/server.nim` is a fork of `src/ctf/server.nim`: the same mummy HTTP/WebSocket server, the
same routes (`GET /healthz` — `src/ctf/server.nim:60`; the player WebSocket at `/player?slot=N&token=T`;
the spectator `/global`; **real browser pages on `GET /client/player` and `GET /client/global`,
registered before any catch-all asset route and neither of them opening the player socket** — the
episode runner probes both before starting player pods and a 404 there is a `game_contract_violation`
(playbook gotcha, lantern 0.1.1); and in replay mode `/replay-data` + `/client/replay`), the same 403
on a bad slot/token and 409 on a duplicate connection, the same `bitworld/runtime` `RuntimeConfig`
contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_LOAD_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI` — the last two `file://`-only
and loudly rejected otherwise), the same **write order at the end of an episode** (broadcast `done` to
every seat with a 3.0 s per-seat deadline → write the replay → `writeResults`), and the same pre-listen
bake so a viewer's first frame is instant. `/healthz` and `/global` keep answering for a **20 s
shutdown grace** after artifacts are written, then the process exits — the cert runner pings `/global`
with a 2 s deadline *after* the player pods start and a short episode would otherwise already be gone
(playbook gotcha, lantern 0.1.3).

**Player handshake (the only thing a player container must do).** On connect the player sends exactly
one text frame:

```json
{"type": "register", "prompt": "<strategy text or empty>",
 "scripted": "dispatcher" | "beeline" | null,
 "policy": "<free label, <=48 runes>"}
```

`src/gridlock_player.nim` reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and
`PLAYER_POLICY_LABEL`, sends that frame, then receives until `{"done": true, …}` and exits 0. A seat
that never registers, or registers with neither field, is treated as `scripted: "dispatcher"`.
`PLAYER_SCRIPTED` parsing follows bullwhip's `parseScriptKind` (`src/bullwhip/llm.nim:61`):
`dispatcher`/`1`/`true`/`yes` → dispatcher, `beeline` → beeline, anything else → none. **The receive
loop is wrapped in `try/except CatchableError` and exits 0 on a dead socket** — whisky's
`receiveMessage` raises on a close frame and the game's `quit(0)` can outrun the flushed `done` frame
(playbook gotcha, raid 0.1.3 → 0.1.4).

**Per turn the server pushes to each seat** (informational — the seat is not required to answer;
decisions are made server-side):

```json
{"type": "turn", "turn": 7, "tick": 1680, "fleet": "Copper",
 "view": { … }, "plan_source": "llm"}
```

and at the end `{"done": true, "result": { …the results document… }}`, then close.

### The per-seat view (exactly what is visible, and what is hidden)

This object is both the `view` in the turn frame and the tail of the LLM user message. All coordinates
are integers. Nodes are `[ix, iy]` with `ix, iy ∈ 0..8`; districts are `[bx, by]` with
`bx, by ∈ 0..2`.

```json
{"turn": 7, "of": 20, "tick": 1680, "ticks_left": 3120, "seconds_left": 130.0,
 "you": {"fleet": "Copper", "colour": "#e07a3f", "depot": [1, 1], "depot_district": [0, 0],
         "vans": 50, "docked": 9, "loading": 2, "waiting_dispatch": 6,
         "on_road_loaded": 21, "on_road_empty": 12, "stalled": 7,
         "delivered": 61, "delivered_last_turn": 9, "backlog": 23,
         "mean_trip_seconds": 41.5, "stalled_pct": 21,
         "last_plan": { …the resolved plan you played last turn, or null on turn 0… },
         "next_orders": [{"id": 812, "dest": [4, 5], "district": [1, 1], "age_s": 6.0},
                         {"id": 815, "dest": [8, 2], "district": [2, 0], "age_s": 5.0}, … up to 6 … ]},
 "city": {"grid": [9, 9], "districts": [3, 3], "lane_cells": 14,
          "arterial_cols": [2, 4, 6], "arterial_rows": [2, 4, 6],
          "signal": "4.0 s cycle, 2.0 s NS then 2.0 s EW, offset ((ix+iy) mod 4) x 1.0 s",
          "discharge_per_green_step": {"arterial": 2, "local": 1},
          "jam_index": 46,
          "districts_heat": ["347", "5 9 6", "263"],
          "hot_lanes": [{"from": [4, 3], "to": [4, 4], "class": "arterial", "q": 14, "cap": 14,
                         "blocked_s": 8.5},
                        {"from": [3, 4], "to": [4, 4], "class": "arterial", "q": 12, "cap": 14,
                         "blocked_s": 3.0}, … up to 8, worst first … ]},
 "fleets": [{"fleet": "Copper",  "delivered": 61, "on_road": 33},
            {"fleet": "Cobalt",  "delivered": 58, "on_road": 44},
            {"fleet": "Verde",   "delivered": 47, "on_road": 50},
            {"fleet": "Saffron", "delivered": 39, "on_road": 28}],
 "events_last_turn": ["gridlock in CENTRE", "jam on 4,3->4,4"]}
```

- `districts_heat` is three strings of three digits (row-major over `by`, then `bx`); digit
  `= min(9, (meanLaneOccupancyPercentInDistrict * 10) div 100)` over all lanes whose head node is in
  that district, measured over the previous turn. The example above is written with spaces only for
  legibility in this note; the wire form is three 3-character strings.
- `jam_index` is city-wide: over the previous 240 ticks, `100 * blockedMoveOpportunities /
  totalMoveOpportunities` for on-road vehicles, clamped to 0…100. `you.stalled_pct` is the same
  quantity computed over that seat's own vehicles only.
- `hot_lanes` lists at most 8 lanes, worst `q` first, ties by lane id. `blocked_s` is how long the
  lane's stop-line vehicle has been unable to cross.
- `fleets[]` is **public** and in fixed alias order: every fleet's running delivery count and how many
  of its vans are on the road. Deliveries and traffic are physical and loud; the idea's racing counters
  are diegetic.

**Visible to a seat:** everything above — the full static city (grid, arterials, districts, signal
plan, discharge rates), **public live congestion on every lane in aggregate** (a traffic app: the
district heat grid, the eight worst lanes, the city jam index), its own complete fleet state, its own
next six parcel orders, and the public per-fleet delivery and on-road counters.

**Hidden from a seat:** the **per-fleet composition of any lane's queue** (you see 14 vans in that
lane, never whose they are); every rival's routing plan, `note`, `say`, prompt and policy kind; every
rival's parcel destinations, backlog size and trip times; the positions and routes of individual
rival vehicles; the canonical destination schedule and anything beyond its own next six orders; the
seat→depot permutation for any other seat; the episode seed; and the future. **Rival identities are
hidden by construction:** the only names in a view are the depot aliases.

**Hidden from everyone, in both in-game name spaces:** the real player names behind the fleet aliases.
`Copper` / `Cobalt` / `Verde` / `Saffron` are the only names any prompt, view or event body contains;
real policy names exist only in `replay.names.players`, `results.names` and the viewer's scorebug,
endcard and feed. That is the two-name-space pin, and the per-episode seat→depot permutation is the
idea's "fleet aliases are anonymous per episode".

### Routing-plan schema and character caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"congestion_weight": 65, "patience": 40, "dispatch": 80, "spread": 60,
 "corridor": [0, 1], "avoid": [1, 1], "priority": "near",
 "note": "centre is at 9 and my stalled_pct is over the city index; metering to 80",
 "say": "hold at 80, skip centre"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `congestion_weight` | int | 0…100 | missing/non-numeric → previous turn's value, or 40 on turn 0; out of range → clamped |
| `patience` | int | 0…100 | as above, default 50 |
| `dispatch` | int | 0…100 | as above, default 100 |
| `spread` | int | 0…100 | as above, default 40 |
| `corridor` | `[int,int]` or null | `bx, by ∈ 0…2` | out of range → clamped; non-array, wrong length or non-numeric → `null` |
| `avoid` | `[int,int]` or null | `bx, by ∈ 0…2` | as `corridor`; forced `null` if it equals `corridor` (a plan may not prefer and shun the same district) |
| `priority` | enum | exactly `"near"` \| `"far"` \| `"fifo"` (case-insensitive on input) | anything else → `"fifo"` |
| `note` | string | **≤ 140 runes** | truncated to 140 runes |
| `say` | string | **≤ 32 runes** | truncated to 32 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and `register.prompt` **≤ 4000 runes** at the transport
(an over-long prompt is truncated, not rejected) — the prompt is never written to the replay or the
results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim that means walking the
string with `runeSubStr` / `toRunes` and never slicing a `string` by byte index on any path that
reaches the replay. A byte-truncated multi-byte character is exactly the bug that makes replay bytes
render in a browser but fail a strict JSON parser (playbook gotcha), and §Tests pins it with a 4-byte
emoji sitting on the 32nd rune of a `say`.

**Parsing is tolerant** (bullwhip's `extractJsonObject` shape, `src/bullwhip/llm.nim:312`): strip
markdown fences, take the outermost balanced `{…}` if the model prefixed prose, accept numeric strings
for any integer field, accept percentages written as `"70%"`, accept `corridor`/`avoid` as
`{"bx":…,"by":…}` or as a district name string (`"CENTRE"`, case-insensitive). Only when no object
containing at least one recognised plan key can be recovered does the retry, then the fallback, fire.
**The resolved, repaired, clamped plan is what is installed and what is recorded** — the replay never
depends on re-running the repair.

### Results document (closed schema — must equal the manifest `results_schema` key-for-key)

All per-seat arrays are length 4 in **slot** order (not depot order).

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
 "aliases": ["Copper", "Saffron", "Cobalt", "Verde"],
 "colours": ["#e07a3f", "#f2c14e", "#4a8fe7", "#5fbf6a"],
 "depots": [[1,1], [7,7], [7,1], [1,7]],
 "policy_kinds": ["llm", "llm", "scripted", "scripted"],
 "scores": [163.0, 148.0, 96.0, 71.0],
 "win": [true, false, false, false],
 "delivered": [163, 148, 96, 71],
 "total_delivered": 478,
 "orders_created": [200, 200, 200, 200],
 "backlog_final": [37, 52, 104, 129],
 "mean_trip_seconds": [38.2, 41.0, 63.7, 78.1],
 "stalled_vehicle_seconds": [412, 505, 1180, 1544],
 "own_stall_pct": [14, 18, 39, 47],
 "vans": [50, 50, 50, 50],
 "jam_index_mean": 43,
 "jam_index_peak": 88,
 "gridlock_events": 6,
 "turns_llm": [20, 19, 0, 0],
 "fallback_turns": [0, 1, 0, 0],
 "fallback_causes": [{"timeout": 0, "parse_error": 0, "transport_error": 0,
                      "no_credentials": 0, "budget_guard": 0}, … 4 … ],
 "reason": "complete",
 "end_rule": "full_time",
 "winner": 0,
 "final_tick": 4800,
 "final_turn": 20,
 "seed": 679961}
```

`winner` is a slot index `0…3` or `null` (tied maximum). Adding or removing a key here means editing
`coworld_manifest_template.json`'s `results_schema` and `tests/test_manifest.nim` in the same commit.

### Replay bytes (self-sufficient, strict UTF-8 JSON)

*Deviation from paintbot, deliberate:* paintbot writes the binary `COWLDCTF` format
(`src/ctf/replays.nim:119` — a JSON config brace-matched from the first `{`, then recorded inputs).
Gridlock writes **UTF-8 JSON**, because SPEC §Definition of done check 4 fetches the replay from S3 and
requires valid UTF-8 JSON with a matching `protocol` and a legal `results.reason`, and the shared
`tools/ci/docker_smoke.sh` defaults to `SMOKE_REQUIRE_REPLAY_JSON=1`.

The **input log is the plan stream** — 20 turns × 4 seats of six values and two strings — because the
traffic is a pure function of `(seed, city, plans)`. That is why gridlock's replay is small and why
the viewer can re-derive every lane's occupancy, which is the picture the idea asks for.

```json
{"protocol": "gridlock.replay.v1",
 "format_version": 1,
 "game_version": "1",
 "seed": 679961,
 "config": { …the fully resolved game config, tokens excluded: num_agents, fleetSize,
             episodeTicks, turnTicks, moveTicks, serviceTicks, dispatchPeriodTicks,
             laneCells, cellPx, loadTicks, orderPeriodTicks, backlogMax,
             signalCycleTicks, greenNsTicks, routeBudgetPerTick, jamThreshold,
             turnBudgetSeconds, minTurnSpacingSeconds, wallClockBudgetSeconds,
             playerConnectTimeoutSeconds, cityPath, players:[{"name":…}] … },
 "city": { …data/gridcity.cityspec.json inlined verbatim… },
 "seat_depots": [0, 3, 1, 2],
 "names": {"players": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
           "aliases": ["Copper", "Saffron", "Cobalt", "Verde"],
           "policy_kinds": ["llm", "llm", "scripted", "scripted"],
           "colours": ["#e07a3f", "#f2c14e", "#4a8fe7", "#5fbf6a"]},
 "ticks_per_second": 24, "turn_ticks": 240, "tick_count": 4800,
 "plans": [{"turn": 0, "seat": 0, "source": "llm", "latency_ms": 4120,
            "congestion_weight": 25, "patience": 70, "dispatch": 100, "spread": 30,
            "corridor": null, "avoid": null, "priority": "near",
            "note": "city is empty; churn short trips", "say": "full throttle"}, … 80 … ],
 "keyframes": [{"t": 0, "d": 2947483111, "del": [0,0,0,0], "road": [0,0,0,0],
                "back": [1,1,1,1], "jam": 0}, … every 24 ticks … ],
 "vehicles_b64": "<base64 of keyframeCount x 200 x 4 bytes: (lane u16 little-endian,
                  cell u8, state u8) per vehicle per keyframe, vehicles in global index
                  order; lane 65535 = docked>",
 "events": [ … the vocabulary below … ],
 "results": { …the results document verbatim… }}
```

`seed` + `city` + `seat_depots` + `plans` + the integer sim reproduce the episode exactly; `keyframes`
and `vehicles_b64` carry the per-second state and its digest `d` so the viewer (and the tests, and a
human reading the JSON) can verify the re-derivation, and so **lane occupancy — the heat map — is
directly computable from the keyframes without running wasm at all**.

**Size:** plans ≈ 18 KB, keyframes ≈ 20 KB, `vehicles_b64` = 201 × 200 × 4 = 160 800 B → 215 KB
base64, events ≈ 90 KB. Total ≈ 350 KB — comfortably small.

**Everything the viewer needs is in these bytes** (player names, aliases, colours, policy kinds, the
full config, the city geometry and signal plan, the seat→depot permutation, the plan stream, per-second
vehicle states, the event stream, the seed, and the results). **The viewer contacts no server except
S3 for the `.replay` file.**

**Event vocabulary** (every record carries `t` = tick; `turn` where meaningful):

| `type` | Fields |
|---|---|
| `match_start` | `t`, `seed`, `city` (name), `fleets` (`alias`, `colour`, `depot`, `seat`), `vans_per_fleet`, `episode_ticks`, `signal` |
| `turn_start` | `t`, `turn`, `delivered` (4), `on_road` (4), `backlog` (4), `jam_index` |
| `plan` | `t`, `turn`, `seat`, `fleet`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `congestion_weight`, `patience`, `dispatch`, `spread`, `corridor`, `avoid`, `priority`, `note`, `say` |
| `fallback` | `t`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `t`, `turn`, `remaining_s` |
| `deliver` | `t`, `f` (seat), `n` (that fleet's running total), `d` (destination node), `trip` (ticks from release to delivery) |
| `jam` | `t`, `lane` (id), `from`, `to`, `class`, `q` |
| `jam_clear` | `t`, `lane`, `q`, `duration_ticks` |
| `gridlock` | `t`, `district`, `district_name`, `blocked_lanes`, `fleets_involved` (aliases with van counts in those lanes) |
| `heat` | `t`, `districts` (3 strings of 3 digits), `jam_index`, `on_road` (4) |
| `meter` | `t`, `turn`, `fleet`, `dispatch`, `held` (vans kept at the depot this turn) |
| `end` | `t`, `reason`, `end_rule`, `delivered`, `scores`, `winner`, `total_delivered`, `jam_index_mean` |

`plan`, `deliver`, `gridlock`, `meter` and `fallback` are the records the phase-60 verifier reads to
judge "the champion seats doing the thing the game is about": a champion seat's `plan` events must
carry `source: "llm"` with varying parameter values and real `note` content, not all fallbacks.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` (forked from
paintbot's, **committed mode 100755** — `coworld build` hard-requires `os.X_OK` — keeping paintbot's
safety checks that the target path is absolute, is named `static-replay-viewer`, lies inside the repo
and is not a symlink, and that `index.html` exists at the end) builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` stage — `emscripten/emsdk:4.0.15` + nimby 0.1.27 pinned by sha256,
`nimby use 2.2.4`, `nimby --global sync nimby.lock` — which compiles **the same Nim sim** as
`nim c -d:emscripten replay-viewer/gridlock_replay.nim`, then copies
`/workspace/gridlock/replay-viewer/dist/.` into the bundle. The game server still serves
`/client/replay` for local viewing off the identical `dist`.

### The single starter for all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` (paintbot), and from no other starter:**

| File | Source (paintbot, `/workspace/starters/coworld-ctf`) |
|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims`, verbatim except the four renamed paths/exports |
| the wasm entry `.nim` — `replay-viewer/gridlock_replay.nim` | `replay-viewer/ctf_replay.nim` |
| `static_replay*.js` — `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js` | the two files of the same names |
| `index.html` | generated by `Dockerfile.replay-viewer`'s `sed` splice of paintbot's `client/replay_broadcast.html` (the `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->` and `<!-- BROADCAST_CORE -->` markers) |

**One starter for all four, never a mixture.** Splicing one starter's shell onto another's emscripten
link flags — `MODULARIZE`/`EXPORT_NAME` against an `onRuntimeInitialized` bootstrap — deadlocks the
viewer silently with every asset returning 200 (cogame-lantern, 2026-08-23). Concretely, gridlock keeps
paintbot's **non-modularized** pairing: `replay-viewer/config.nims` carries **no** `MODULARIZE` and
**no** `EXPORT_NAME` (`/workspace/starters/coworld-ctf/replay-viewer/config.nims:42-54`), and
`static_replay_worker.js` keeps `Module.onRuntimeInitialized = …` with
`importScripts('./wire_constants.js', './broadcast_core.js', './gridlock_replay.js')`
(paintbot's `replay-viewer/static_replay_worker.js:166,214`). Nothing from bullwhip, babel, moba or
factorio appears in `replay-viewer/` or `client/`.

The renames in `config.nims` are mechanical and exhaustive: `-o {distDir}/gridlock_replay.js`, and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_gridlock_load_replay,_gridlock_frame,_gridlock_input,
_gridlock_packet_ptr,_gridlock_packet_len,_gridlock_mismatch_tick,_gridlock_error_ptr,
_gridlock_error_len,_gridlock_stage_ptr,_gridlock_stage_len`. Everything else in that file is kept
because it is scar tissue paintbot already paid for: `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`,
`-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`,
`--preload-file data@data`, `--mm:arc`, `--exceptions:goto`, `-d:useMalloc`, `threads off`. The wasm
entry keeps the `stampStage` progress-note discipline and the
`emscripten_exit_with_live_runtime()` epilogue skip (`replay-viewer/ctf_replay.nim:14-34,152-165`).

### Load signalling

`replay-viewer/static_replay.js` is paintbot's file kept verbatim — the OffscreenCanvas-Worker shell,
the `createCore`/`start`/`stop`/`advance`/`resize`/transform-and-minimap message protocol, the
`data-replay-mismatch-tick` attribute and `showFailure` — with exactly three authored additions (no
line is imported from another starter):

1. **`data-replay-loaded="true"` on the first drawn frame.** Paintbot already sets it on the Worker's
   `loaded` message (`replay-viewer/static_replay.js:144`); gridlock additionally sets it in the
   `firstFrame` branch (`static_replay.js:133-134`), so the attribute means "a frame was drawn", which
   is what SPEC check 8(a) and `tools/ci/viewer_smoke.mjs` look for.
2. **`data-replay-error` on failure.** Inside `showFailure` (`static_replay.js:8-20`), alongside the
   existing `#status` text: `document.documentElement.setAttribute('data-replay-error', message)`.
3. **The `coworld-replay` postMessage bridge**, ~12 lines authored in place: `tell("loading")` on
   script entry, `tell("error", msg)` in `showFailure`, and `tell("ready")` inside a double
   `requestAnimationFrame` after the first drawn frame, each posting
   `{src: "coworld-replay", type, message}` to `window.parent`. SPEC check 8(a) accepts either signal;
   gridlock ships both.

The replay fetch is bounded by a 20 s `AbortController`; on abort the shell shows a Retry button and
sets `data-replay-error`.

### How playback works

`replay-viewer/gridlock_replay.nim` re-runs the integer sim from the plan stream, so lane occupancy —
the heat map — is re-derived, not transported. Forward playback is one tick per step. A **backward
seek** restarts from the nearest in-memory turn snapshot (§The game, step 13) and replays at most 240
ticks (under 15 ms) instead of paintbot's replay-from-zero. Every keyframe's digest is compared against
the recorded `d`; the first mismatch lights `#mmwarn` and playback continues.

**Files in the bundle** (each must return 200 with a non-trivial size): `index.html`,
`static_replay.js`, `static_replay_worker.js`, `broadcast_core.js`, `chrome_common.js`,
`wire_constants.js`, `gridlock_replay.js`, `gridlock_replay.wasm`, `gridlock_replay.data`,
`art/asphalt.jpg`, `art/intersection.png`, `art/block_park.png`, `art/plaza.png`,
`art/depot_copper.png`, `art/depot_cobalt.png`, `art/depot_verde.png`, `art/depot_saffron.png`,
`art/van.png`, `art/van_loaded.png`, `art/parcel_pin.png`, `font.ttf`.

### Chrome kept verbatim

`client/chrome_common.js` and `client/broadcast_core.js` are copied unchanged.
`client/replay_broadcast.html` keeps its CSS block and its markup ids exactly, as read from the
starter: `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#chrome`, `#scorebug`, `#plates-l`,
`#plates-r`, `#clock`, `#clock-time`, `#clock-caption`, `#ffwd-mini`, `#viewpanel`, `#minimap`,
`#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-slider`, `#zoom-in`, `#zoom-read`, `#mmwarn`,
`#bannerlane`, `#killfeed`, `#transport`, `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
`#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`,
`#speedchips`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`, `#scrub-head`, `#endcard`,
`#ec-headline`, `#ec-wincond`, `#ec-how`, `#ec-teams`, `#ec-replay`, `#status`, the locker-room curtain
(`#lockerroom`, `#lk-art`, `#lk-bg`, `#lk-sprites`, `#lk-cap`) with gridlock's own plate, and the
`--hudscale` / `--u` / `.tiny` fixed-point relayout loop
(`client/replay_broadcast.html:40-42,1424-1428,4091-4121`) unchanged. **The four-fleet scorebug needs
no new layout**: `ensureScorebug(teams)` already generates one plate per active team for 2–4 teams
(`client/replay_broadcast.html:1486,2159-2190`), and `.plate .team-name`'s
`min-width: 0; overflow: hidden; text-overflow: ellipsis` block
(`client/replay_broadcast.html:201-219`) is already the fix for the "names collapse to …" gotcha;
gridlock keeps it and adds `flex: 1 1 auto; min-width: 3.2em`.
**Added markup, and nothing else:** `#fleetbug` (the four corner delivery counters), `#planbar` (the
four fleets' current `congestion_weight / dispatch` chips), `#jamgauge` (the city jam index) and
`#jamflash` (the gridlock overlay). **Removed:** the CTF flag icons, the lives line, the squad pips,
the first-person PiP (`#fpv…`) and the kill plumbing, none of which has a counterpart here.

**Split of responsibilities.** The wasm canvas draws the world (asphalt, intersections, signal heads,
scenery, congestion heat, depots, vans); the DOM chrome draws the scorebug, fleet counters, plan chips,
event feed, jam gauge, transport and warnings. DOM text is set with `textContent` only (names are
player-controlled data) and stays crisp at any zoom.

### Readouts (the idea's replay plan, item for item)

1. **City map with roads heat-coloured by congestion — a jam spreads like a stain.** Every frame the
   wasm module draws each of the 288 lanes as a rounded 6 px-wide bar along its cells, coloured by
   occupancy `q/14`: `#2e3440` (empty) → `#4d7c4f` (light) → `#d9a441` (loading, q ≥ 7) → `#c2452d`
   (queued, q ≥ 11) → `#7a1414` with a slow pulse (fully blocked, q = 14). The colour ramp is drawn
   *under* the vans and *over* the asphalt, so the network reads as a living heat map and a spreading
   jam is literally a stain crawling backwards from an intersection. Signal heads are 3 px pips at each
   approach, green or dark.
2. **Vans.** Each van is a 6 × 6 authored sprite in its fleet's hue; loaded vans carry a white parcel
   pip and are one shade brighter; a `stalled` van gets a thin red halo. 200 vans stepping at 8 cells/s
   read as traffic, and the moment a queue forms you can see the halos light up down a lane.
3. **Per-fleet delivery counters race in the corners.** `#fleetbug` places four counters at the four
   corners of the board, each over its own depot, in that depot's colour: alias, delivered, and a thin
   "on road" bar. Every `deliver` event triggers a 6-frame scale bump on that counter plus a one-frame
   ring at the destination node. That is the idea's race, and it is diegetic — the counters sit where
   the depots are.
4. **Jam gauge and gridlock alarms.** `#jamgauge` shows the city `jam_index` 0–100 as a horizontal bar
   that turns amber above 45 and red above 70, with the 3 × 3 district heat grid beside it. On a
   `gridlock` event the district gets a hatched red overlay in `#jamflash` for 48 frames and a
   `#bannerlane` banner (`GRIDLOCK — CENTRE, 7 lanes blocked`); on a `meter` event with a large `held`,
   a banner (`Copper holds 22 vans at the depot`). Both are marked on the scrub bar as highlight ticks.
5. **Time-compressed.** Default playback is **4×** on the inherited `#speedchips`
   (`PlaybackSpeeds = [1,2,3,4,8,16]`), so a 200 s match watches in 50 s. Spans of 240 ticks with no
   `deliver`, no `gridlock` and no `jam` are registered as lull spans in the inherited
   `skipLulls`/`lullSpans`/`#btn-skip`/`#ffwd-chip` machinery and run at 16× with `#clock-caption`
   reading `CITY FLOWING — 16×`. `#btn-skip` turns it off.
6. **Scorebug** (`#scorebug`, always on): four plates via `ensureScorebug(4)` —
   `▮ daveey · Copper 163` / `▮ Baseline (1) · Cobalt 96` on the left, `Verde 71 · Baseline (2) ▮` /
   `Saffron 148 · daveey-1 ▮` on the right — each with its colour chip, the leader's plate brightened,
   and `#clock-time` showing `MM:SS` remaining over `turn 7/20`. **Real player names live here and only
   here** (plus the endcard and the feed); the board itself labels depots `Copper`…`Saffron`.
7. **Plan feed** (`#killfeed`, plain language, last 6): `Copper → reprice 65, dispatch 80, avoid
   CENTRE, near-first`, `Copper says "hold at 80, skip centre"`, `Cobalt → full throttle, no
   repricing`, `Verde falls back (timeout)`. Plus `#planbar`: four always-visible chips showing each
   fleet's current `reprice / dispatch`, so a spectator sees a strategy change *before* the roads
   change. **This is where the LLM is visible playing.**
8. **Transport** (verbatim): play/pause, back one tick, +5 s, jump to end, loop, lull-skip, spoilers,
   the speed chips, the scrubber with `#momentum` re-purposed to plot **all four delivered curves plus
   the city jam index** across the match, `gridlock` / `jam` / `deliver`-burst ticks marked on the
   scrub bar, the `#tick-clock` readout, and the `#mmwarn` digest-mismatch line.
9. **Endcard** (`#endcard`): headline `Copper wins — 163 parcels`, then a four-row breakdown
   (delivered, mean trip time, stalled vehicle-minutes, final backlog), then one line naming the cost
   of the commons: `478 parcels delivered · mean jam 43 · peak 88 · 6 gridlocks — the city lost an
   estimated 61 minutes of van time to queues`, and the jam-index curve drawn under the four delivery
   curves. **The idea's "all-greedy counterfactual" overlay is deferred** — see §Out of scope (v1) for
   the decision and the substitute.

**Art is real, not placeholder.** The asphalt is an authored painted tile (`art/asphalt.jpg`, seamless,
cool grey, subtly noisy so the heat ramp reads against it); intersections are a painted box with lane
markings; city blocks between the roads are painted park/plaza/rooftop tiles keyed off the `scenery`
list; each depot is an authored painted warehouse sprite tinted to its fleet hue with a visible dock
door; vans are two authored 6 px sprites (`van.png`, `van_loaded.png`) tinted per fleet at draw time.
All of it is produced by committed scripts under `scripts/art/`, the way paintbot generates its props.
Paintbot's `client/art/walls/wall_h.jpg` / `wall_v.jpg` are reused verbatim for the board border and
its locker-room curtain art is replaced with gridlock's own plate. No solid-colour rectangles standing
in for anything, no TODO assets.

**Legible at 360 px** — the embedded featured-match iframe is ~360 px wide, so the composition is
checked at **360 px**, not at desktop width. Paintbot's `--hudscale`
(`clamp(0.5, boardW/760, 1.6)`, `client/replay_broadcast.html:4091-4121`) and its `.tiny` class
(`:1424-1428`) are inherited and do the heavy lifting. On top of that:
`.plate .team-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }`
so player names never collapse to "…" (playbook gotcha); a `@media (max-width: 640px)` block collapses
`#fleetbug` to four 8 px colour dots with the numeral beside them, hides `#planbar`, `#viewpanel`
(minimap + zoom bar) and the speed-chip labels, shrinks `#jamgauge` to a bar without the district grid,
and reduces the feed to two lines under the board; the four scorebug plates drop the colour-word label
and keep chip + number + name; banner text is `font-size: clamp(11px, 3.4vw, 17px)` and never wraps to
three lines; the lane heat bars keep a 2 px minimum width so the network stays readable when the
1024 px board is drawn at 360 px. A static test asserts the `.team-name` rule and the `640px` media
block are present (§Tests).

---

## Packaging

- **Repo:** `Metta-AI/cogame-gridlock`, **public at creation** (public is a certification prerequisite
  — `source-resolves` 404s on private). Slug `gridlock`.
- **`compose.yaml`** — single service, service name **= the coworld name**, so the manifest's image
  placeholder is `{{GRIDLOCK_IMAGE}}` (placeholders are derived from compose service names;
  `{{GAME_IMAGE}}` is not a thing — playbook gotcha, lantern 0.1.0). Paintbot's two-image split does
  not survive the fork: the shared `tools/ci/docker_smoke.sh` runs the game and every player container
  from one image.

  ```yaml
  services:
    gridlock:
      image: coworld-gridlock:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — the two-stage Nim build: `debian:bookworm-slim` + nimby pinned by sha256,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, then two binaries —
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:gridlock src/gridlock.nim` and the
  same for `src/gridlock_player.nim`. Run stage `debian:bookworm-slim` with `ca-certificates` and
  `libcurl4`, copying `/bin/gridlock`, `/bin/gridlock-player`, `./data`, `./client`, `./*.json`.
  `CMD ["/bin/gridlock"]`.
- **`Dockerfile.replay-viewer`** — paintbot's, with the CTF asset copies replaced by gridlock's:
  `emscripten/emsdk:4.0.15`, nimby 0.1.27 (sha256-checked), `nim c -d:emscripten
  replay-viewer/gridlock_replay.nim`, `tools/gen_wire_constants.nim > replay-viewer/dist/wire_constants.js`,
  the `broadcast_core.js` / `chrome_common.js` / `static_replay.js` / `static_replay_worker.js` /
  `font.ttf` copies, the marker `sed` that splices `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`
  and `<!-- BROADCAST_CORE -->` into `index.html`, the art copies, and the same `test -f` / `grep -q`
  assertion tail adjusted to gridlock's file names and extended with
  `grep -q 'coworld-replay' replay-viewer/dist/static_replay.js` and
  `grep -q 'data-replay-error' replay-viewer/dist/static_replay.js`.
- **`coworld_manifest_template.json`:**
  - `$schema` = the coworld manifest schema URL; `tags` = `["logistics", "traffic", "commons",
    "real-time", "congestion"]` (≥ 3).
  - `game.name` `gridlock`; `episode_timeout_minutes` **20** (top level); `game.runnable` =
    `{"type": "game", "image": "{{GRIDLOCK_IMAGE}}", "run": ["/bin/gridlock"], "source_url":
    "https://github.com/Metta-AI/cogame-gridlock/tree/main"}`; `game.owner` `daveey@softmax.com`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema` — a real JSON Schema (`$schema` draft 2020-12, `type: object`,
    `additionalProperties: false`), with `tokens`, `players`, `seed`, **`num_agents`** (integer,
    default **4**), `fleetSize` (50), `episodeTicks` (4800), `turnTicks` (240), `moveTicks` (3),
    `serviceTicks` (6), `dispatchPeriodTicks` (12), `laneCells` (14), `cellPx` (8), `loadTicks` (12),
    `orderPeriodTicks` (24), `backlogMax` (80), `signalCycleTicks` (96), `greenNsTicks` (48),
    `routeBudgetPerTick` (24), `jamThreshold` (11), `turnBudgetSeconds` (22),
    `minTurnSpacingSeconds` (10), `wallClockBudgetSeconds` (660), `playerConnectTimeoutSeconds` (90),
    `cityPath` (`"gridcity"`), `showPlayerLabels` (true), `gameOverTicks` (96). The CLI validates every
    variant and the cert fixture against this schema (injecting `tokens`), so it must stay in sync.
  - `game.results_schema`: exactly the closed key set in §Server, with `reason` enum
    `["complete","deadline","fault"]` and `end_rule` enum
    `["full_time","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both `player` and `global`**, each `{"type": "text", "value": "…"}` — `player`
    describing the `register` frame, the `turn` frames, the view schema and the `done` frame; `global`
    describing the `/global` spectator snapshot and the static replay bundle. Text form, not URIs
    (paintbot uses URIs; the playbook gotcha row requires text or the docs go missing on the coworld
    page).
  - `game.docs`: `readme` = `{"type": "text", "value": "<the README body, inlined>"}` and `pages` =
    two entries — `{"id": "rules.md", "title": "Rules", "content": {"type": "text", "value":
    "<docs/RULES.md inlined>"}}` and `{"id": "protocol.md", "title": "Wire protocol", "content":
    {"type": "text", "value": "<docs/PROTOCOL.md inlined>"}}`. A manifest test asserts all three values
    are non-empty text.
  - Top-level `player[0]` = `{"id": "baseline", "type": "player", "name": "dispatcher",
    "description": "Congestion-aware shortest-path dispatcher with jam-triggered fleet metering.",
    "image": "{{GRIDLOCK_IMAGE}}", "run": ["/bin/gridlock-player"],
    "env": {"PLAYER_SCRIPTED": "dispatcher"}, "source_url":
    "https://github.com/Metta-AI/cogame-gridlock/tree/main"}` — the bundled certification player, no
    LLM. It is the **only** declared player entry, and it occupies every certification slot, so the
    `players_missing` cert failure (raid 0.1.2) cannot occur.
  - **Variants — `num_agents` is 4 in every one, and every variant carries a `description`:**

    | id | name | description | `num_agents` | `fleetSize` | `episodeTicks` | `turnTicks` | turns | `orderPeriodTicks` | `turnBudgetSeconds` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|
    | `default` | Gridcity (4 fleets, 200 s) | Four fleets, fifty vans each, 200 seconds of city time over twenty routing turns. | **4** | 50 | 4800 | 240 | 20 | 24 | 22 | 660 |
    | `rush` | Rush hour (4 fleets, 120 s) | A shorter, denser round: same city, double the parcel demand, twelve routing turns. | **4** | 50 | 2880 | 240 | 12 | 12 | 22 | 420 |

    `rush` exists for cheap, jam-heavy ladder rounds; it changes only the episode length and the order
    rate, **never the seat count** and never `fleetSize`. Both variants list four `players` entries.
  - **Certification fixture** (`certification`): `players` = `[{"player_id": "baseline"} × 4]`;
    `game_config` = `{"players": [{"name":"P1"},{"name":"P2"},{"name":"P3"},{"name":"P4"}],
    "num_agents": 4, "seed": 42, "fleetSize": 50, "episodeTicks": 960, "turnTicks": 240,
    "turnBudgetSeconds": 22, "minTurnSpacingSeconds": 0, "wallClockBudgetSeconds": 180,
    "playerConnectTimeoutSeconds": 60, "cityPath": "gridcity"}` — 960 ticks, 4 turns, all four seats
    scripted `dispatcher`, no LLM, wall clock ≈ 4 s. **`num_agents` = 4 here too**, and
    `len(certification.players) == len(certification.game_config.players) == 4`.
- **Scaffold from `coworld-builder/templates/`** with `<slug>` = `gridlock`, `<IMAGE>` =
  `coworld-gridlock`, **`<SEATS>` = 4**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**committed mode 100755**), `tools/ci/viewer_smoke.mjs` (verbatim, no
  substitutions), `tools/build_replay_viewer.sh` (**committed mode 100755**), `tools/ci/policies.json`.
  `SMOKE_REQUIRE_REPLAY_JSON` stays at its default `1`; **`SMOKE_SEATS=4`** is an independent
  cross-check against `certification.game_config.num_agents` — a mismatch prints `SEAT-COUNT FAIL:`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/gridlock-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `gridlock-flowwright` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `gridlock-backstreet` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `gridlock-dispatcher` | `PLAYER_SCRIPTED` = `dispatcher` | filler |
  | `gridlock-beeline` | `PLAYER_SCRIPTED` = `beeline` | filler |

  The game runnable's manifest `env` must also carry
  `ANTHROPIC_API_KEY_URI: secret://coworld/gridlock/anthropic_api_key`, or the hosted container never
  receives the secret and every league episode plays scripted while local certification still passes
  (playbook gotcha, hive, 2026-08-23).
- **Repo layout:** `src/gridlock.nim`, `src/gridlock_player.nim`, `src/gridlock/` (`types.nim`,
  `city.nim`, `graph.nim`, `traffic.nim`, `parcels.nim`, `sim.nim`, `rules.nim`, `plan.nim`,
  `baselines.nim`, `llm.nim`, `state.nim`, `config.nim`, `roster.nim`, `events.nim`, `labels.nim`,
  `broadcast.nim`, `global.nim`, `render.nim`, `replay.nim`, `server.nim`), `replay-viewer/`
  (`gridlock_replay.nim`, `config.nims`, `static_replay.js`, `static_replay_worker.js`), `client/`
  (`replay_broadcast.html`, `chrome_common.js`, `broadcast_core.js`, `art/`), `data/`
  (`gridcity.cityspec.json`, art, `font.ttf`), `tests/` (+ `tests/support/`), `tools/`,
  `scripts/art/`, `docs/` (`RULES.md`, `PROTOCOL.md`, `plans/2026-08-23-gridlock-design.md` — this
  note), `AGENTS.md`, `README.md`, `nimby.lock`, `gridlock.nimble`, `config.json`. `players/` is
  **not** used (the player is `src/gridlock_player.nim`).

---

## Tests

CI is the only harness — the sandbox has no Docker, no Nim, no emsdk. The template `ci.yml` runs
**every `tests/*.nim` file individually, twice (debug and `-d:release`)**, so each test file is a
standalone program and shared helpers live in **`tests/support/helpers.nim`** (a subdirectory, so the
`tests/*.nim` glob never executes a helper module). No aggregator file.

1. **`tests/test_graph.nim`** — **sim unit tests** on the network: the 9 × 9 grid yields exactly 144
   segments and 288 lanes with stable ids; arterial classification is invariant under both mirrors and
   the 90° rotation; every lane has 14 cells and its geometry lands on the documented pixels; district
   membership matches `[3bx, 3bx+2] × [3by, 3by+2]`; the four depot nodes are the mirror orbit of
   (1,1); Dijkstra returns the cheapest path under the stated cost function on hand-built cases,
   breaks ties by lane id, never returns a path containing a repeated lane, and always returns *some*
   path (the grid is strongly connected); `avoid` raises and `corridor` lowers the chosen path's cost
   in the documented direction; all costs are strictly positive for every legal plan.
2. **`tests/test_traffic.nim`** — **sim unit tests** on movement, capacity and spillback: a vehicle
   only ever enters an empty cell; downstream-first ordering discharges a full lane as a wave (exactly
   one cell of progress per vehicle per move tick, no teleports); a green local approach discharges at
   most 1 and a green arterial approach at most 2 per service step; a red approach discharges 0; a
   full receiving lane blocks the discharge and the block propagates upstream within the documented
   number of ticks; a vehicle stationary for 24 ticks flips to `stalled` and its stall ticks land in
   the jam index; the signal phase function matches `((t + offset) mod 96) < 48` at every node for
   1000 ticks; **no two vehicles ever occupy one cell** over a 4800-tick randomised run. Plus the
   **no-float source guard**: grep `src/gridlock/*.nim` for
   `sin|cos|tan|atan|arctan|exp|ln(|pow|fmod|hypot|sqrt` and for `float`/`float64` inside the step
   path, and the build scripts for `-ffast-math`; any hit fails.
3. **`tests/test_parcels.nim`** — demand and delivery: one order per fleet per `orderPeriodTicks`, none
   beyond `backlogMax`; fleet `j`'s destination is exactly `mirror_j` of the canonical destination, so
   the four demand streams are congruent; `priority` near/far/fifo each select the documented backlog
   entry (with the documented tie-break); loading takes exactly `loadTicks`; a delivery increments
   exactly one counter, only at the parcel's own destination node, and only for the owning fleet;
   crossing a rival depot node does nothing; a delivery whose onward cell is occupied leaves the
   vehicle at the stop line and does not double-count.
4. **`tests/test_city.nim`** — `data/gridcity.cityspec.json` loads; every derived constant matches this
   note (grid 9 × 9, spacing 112, 14 cells × 8 px, board 1024 × 1024); the scenery list is invariant
   under both mirrors and never overlaps a lane cell or an intersection box; the four depot entries
   carry the documented aliases and colours.
5. **`tests/test_scoring.nim`** — the formula and its sign: `score[s] == float(delivered[s])` exactly,
   for 500 randomised delivery vectors; more deliveries is always a higher score (monotone, positive
   sign); `win`/`winner` on a unique maximum, on a tie, and on all-zero; a `fault` gives four zeros and
   `winner: null`; a `deadline` cut mid-episode scores the counters as they stand; `total_delivered`
   equals the sum; the score is **not** normalised (a table where all four fleets do badly produces
   four small numbers, which the test asserts explicitly, because that is the commons property the
   game is about).
6. **`tests/test_determinism.nim`** (**the gate**) — same seed + same plan stream ⇒ identical digest at
   every keyframe over a full 4800-tick match, run twice in one process and once in a fresh instance; a
   one-unit change in any single plan integer changes the final digest; a committed golden fixture
   `tests/fixtures/golden_digests.json` pins the digests for seed 42 over 960 ticks, so any rule change
   shows up in the diff; the turn snapshots (step 13) reproduce the state the forward run had at the
   same tick, byte for byte; the replan FIFO order is a function of seed and plans alone.
7. **`tests/test_baselines.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random views × both baselines, the emitted plan validates against the
   schema — every integer field present and in 0…100, `corridor`/`avoid` either `null` or inside
   `[0..2] × [0..2]` and never equal to each other, `priority` in the enum, `note` ≤ 140 runes,
   `say` ≤ 32 runes — **and** the derived router quantities are inside their stated ranges
   (`replanQueue` 3…13, `activeCap` 0…50, `releasePerStep` 1…6, every lane cost > 0 and ≤ 1200) for
   every fleet on every turn. Plus: a `dispatcher` vs `beeline` match at seed 42 (two seats each)
   completes and the `dispatcher` seats out-deliver the `beeline` seats — the baselines are ordered, so
   the ladder has a spread — and a four-way all-`beeline` match delivers strictly fewer parcels in
   total than a four-way all-`dispatcher` match at the same seed, which is the idea's thesis expressed
   as an assertion.
8. **`tests/test_plan.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON, `"70%"`
   strings, `corridor` as `{"bx":1,"by":1}` and as `"CENTRE"`, districts out of range, wrong arity,
   negative and 300-valued integers, `priority` in mixed case and as garbage, missing fields on turn 0
   and on turn 7, a 400-character `note`, and a `say` whose 32nd and 33rd runes are a 4-byte emoji —
   the truncation must land on the **rune** boundary and the result must still round-trip
   `%*` / `$` / `parseJson` and encode as valid UTF-8. Two consecutive failures ⇒ the `dispatcher` plan
   plus a `fallback` event; a timeout on attempt 1 ⇒ exactly one retry.
9. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: all four seats' calls go out
   in **one parallel batch** (the fake records in-flight windows and the test asserts all four
   intersect); every turn batches exactly 4 requests; batch starts are at least
   `minTurnSpacingSeconds` apart; the per-turn budget is enforced with a hung client; the budget guard
   switches to scripted and the episode still ends `complete/full_time`; the wall-clock stop yields
   `deadline/wall_clock`; a raised sim fault yields `fault/sim_fault` with zeros and a partial replay;
   a seat that never registers plays `dispatcher` and is reported to `COGAME_PLAYER_FAILURE_URI`; a
   mid-match disconnect degrades to `dispatcher` and revives on reconnect.
10. **`tests/test_view.nim`** — the observation contract: a view never contains a rival's plan, note,
    say, backlog, destinations or per-lane fleet composition; `hot_lanes` is sorted worst-first and
    capped at 8; `districts_heat` digits match a hand-computed occupancy on a planted state;
    `jam_index` and `stalled_pct` match hand-counted stall opportunities; `next_orders` is capped at 6
    and contains only that seat's own orders; **no view, event body or prompt anywhere in a full
    episode contains any string from `results.names`** (the two-name-space assertion, run over a
    complete scripted episode); the public `fleets[]` block is present and complete for every seat.
11. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full
    scripted-vs-scripted episode (cert-fixture length) runs over the real sim, writes `results.json`
    and the replay; the replay is parsed **strictly** — the bytes are asserted valid UTF-8 first
    (`validateUtf8(readFile(path)) == -1`) and then `parseJson`ed, and the fixture forces a non-ASCII
    `say` into the plan stream so the UTF-8 path is real; `protocol == "gridlock.replay.v1"`;
    `vehicles_b64` decodes to exactly `keyframeCount × 200 × 4` bytes and every lane index is `< 288`
    or the docked sentinel; every documented top-level key is present and `city`, `names`, `config`,
    `seat_depots`, `plans`, `keyframes`, `events`, `results` are non-empty; `results.reason` is in the
    legal enum; the event stream contains exactly one `plan` per seat per turn and at least one
    `deliver`, one `heat` and one `turn_start`; and re-deriving from `seed` + `city` + `seat_depots` +
    `plans` reproduces **every keyframe digest and every byte of `vehicles_b64`**.
12. **`tests/test_server.nim`** — the websocket and HTTP contract: the `register` frame is accepted, a
    bad token 403s, a duplicate connection 409s, `/healthz` answers,
    **`GET /client/player?slot=0&token=…` and `GET /client/global` both return real pages and neither
    opens the player socket**, `/global` streams a snapshot and keeps answering for the 20 s shutdown
    grace after artifacts are written, artifact writes land on `file://` URIs, `COGAME_EVENTS_URI` /
    `COGAME_METRICS_URI` reject non-file schemes loudly, replay mode serves `/replay-data` and
    `/client/replay`, and the player binary exits 0 when the socket dies mid-receive.
13. **`tests/test_manifest.nim`** — **`num_agents == 4` in every variant *and* in
    `certification.game_config`**; `len(certification.players) == 4` and
    `len(certification.game_config.players) == 4`; every declared `player[]` entry occupies at least
    one certification slot; `results_schema` keys equal the keys `src/gridlock/server.nim`'s results
    builder emits; `game.protocols` carries **both** `player` and `global`; `game.docs.readme` and both
    pages are non-empty **text**; `replay_viewer.bundle == "static-replay-viewer"`;
    `game.runnable.type == "game"`; `episode_timeout_minutes == 20`; every variant validates against
    `game.config_schema`; every variant's `wallClockBudgetSeconds ≤ 0.6 × 1200`; the image placeholder
    matches the compose service name (`gridlock` → `{{GRIDLOCK_IMAGE}}`); the runnable env carries
    `ANTHROPIC_API_KEY_URI`.
14. **`tests/test_viewer.nim`** — the **native** half of the viewer check (no browser): the node
    harness forked from paintbot's `tools/wasm_replay_smoke.cjs` loads
    `replay-viewer/dist/gridlock_replay.js` with a recorded replay, advances to the end, and asserts the
    tick total, the final digest, and that seek-to-mid, seek-backwards and seek-to-end land exactly
    (the snapshot path); malformed inputs (bad `protocol`, bad base64 length, truncated JSON,
    `tick_count`/`vehicles_b64` mismatch, an out-of-range plan integer) are all rejected with a message
    rather than a crash. Plus static assertions over `client/replay_broadcast.html`,
    `replay-viewer/static_replay.js` and `replay-viewer/config.nims`: the `coworld-replay` bridge
    **including `tell("ready")`** is present; `data-replay-loaded` is set in the `firstFrame` branch and
    `data-replay-error` in `showFailure`; every inherited chrome id listed in §Viewer is still there;
    `#fleetbug`, `#planbar`, `#jamgauge` and `#jamflash` exist;
    `.plate .team-name { … min-width: 3.2em` and a `@media (max-width: 640px)` block are present; and
    **`config.nims` contains neither `MODULARIZE` nor `EXPORT_NAME`** while
    `static_replay_worker.js` still contains `onRuntimeInitialized` and `importScripts` — the pairing
    assertion that would have caught the lantern deadlock.
15. **`tests/test_startup.nim`** — `/bin/gridlock` exits 2 with a clean one-line message and no
    traceback when `COGAME_CONFIG_URI` is missing or invalid; `--help` works; the player binary exits 0
    on an unreachable `COWORLD_PLAYER_WS_URL` after its bounded connect retry.
16. **`tests/test_perf.nim`** — 4800 ticks with 200 vehicles, 288 lanes and the full replan budget
    complete in under 40 s in a release build, and one turn-snapshot round trip costs under 5 ms.

**CI jobs, beyond the Nim tests:**

- **`docker-smoke`** runs `tools/ci/docker_smoke.sh` — a raw-Docker one-episode run from the
  certification fixture, one game container plus **4** player containers on a shared network,
  `SMOKE_SEATS=4` cross-checked against `certification.game_config.num_agents`,
  `SMOKE_REQUIRE_REPLAY_JSON=1` so the replay must parse as UTF-8 JSON, every player container's exit
  code asserted, and the produced replay uploaded as the `smoke-replay` artifact. The job **`needs:`**
  the image build in the same run, so a stale binary can never be smoked (playbook gotcha, bullwhip
  2026-08-22).
- **`wasm-viewer`** `needs: docker-smoke`, builds the bundle with `tools/build_replay_viewer.sh`,
  asserts `index.html` and a non-empty `.wasm` exist, downloads the `smoke-replay` artifact, installs
  Playwright pinned **1.55.0** (module and browser together), and then **executes the bundle**:
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <the docker-smoke
  replay> --timeout 90`. **This is the viewer smoke**: the bundle is opened in headless chromium
  against the replay this repo's own game just produced, and the job is green only when the viewer
  signals loaded and drew a frame. `viewer-smoke.png` / `viewer-smoke.json` are uploaded on every run,
  red or green, and the bundle is uploaded as `static-replay-viewer`.

---

## Out of scope (v1)

- **The endcard's all-greedy counterfactual overlay — deferred, with a substitute that ships.** The
  idea asks the endcard to show "your routes against the all-greedy counterfactual". A true
  counterfactual means re-simulating the whole episode with all four seats forced to `beeline` and
  transporting or re-deriving a second 4800-tick run — doubling the wasm work on every load, doubling
  the seek-snapshot memory, and inviting a whole second class of digest mismatch, all for a panel a
  spectator sees for six seconds. **v1 ships the honest measured version instead** (§Viewer, readout 9):
  the endcard states the real total delivered, the mean and peak jam index, the number of `gridlock`
  events, and each fleet's stalled vehicle-minutes, and `tests/test_baselines.nim` pins the underlying
  claim (all-`beeline` delivers strictly fewer parcels than all-`dispatcher` at the same seed). The
  counterfactual **re-run** is the first v0.2 feature once the ladder is healthy: the plan stream is
  already the complete input log, so a second run costs only a second `plans` array.
- **A per-vehicle RL vector or code-agent transport.** The idea's stated interface is realised as the
  fleet routing plan plus the deterministic router (an inherited pin: both champions must be
  `PLAYER_PROMPT`). Shipping a 50 × (local view) observation batch and accepting a 50 × (action)
  response over the websocket is a v0.2 protocol addition; the plan record and the replan FIFO are
  already shaped for it.
- **More or fewer than four fleets.** No 2-seat or 3-seat variant, no asymmetric fleet sizes. Any of
  those changes `num_agents`, which the seat-count pin forbids in v1.
- **Adaptive or policy-controlled traffic signals.** The lights are the city's, fixed-time, public and
  identical at every intersection. Signal control is a different game (and a different commons) and
  would make the routing lever secondary.
- **Procedural cities.** One authored city, `gridcity`. Paintbot's generator, validators, curated pool,
  size/symmetry knobs, map editor and mapkit are all dropped. City variety is a v0.2 feature and must
  keep the two-mirror-plus-rotation symmetry.
- **Continuous motion, multi-lane roads, turning restrictions, right-of-way, U-turns mid-lane, vehicle
  types, fuel, driver shifts, or accidents.** One cell per vehicle, one vehicle per cell, turn anywhere
  you are served.
- **Any inter-seat channel.** `note` and `say` are one-way to the spectator feed and are never
  delivered to another seat. There is no chat, no contract, no toll, no truce mechanism, and no
  cross-episode memory of any kind. Fleets coordinate only through the roads.
- **Pricing, tolls, congestion charges, or any central authority.** The commons is unregulated in v1;
  that is what makes the externality visible.
- **Weather, day/night, road works, emergency vehicles, and any downloaded art asset** (the bundle
  stays hermetic).
- **Audio, 3-D, and camera cuts other than the gridlock and delivery-burst holds.**
