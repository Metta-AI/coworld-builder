# cogame-rware-warehouse — design note (2026-08-27)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` re-exporting the sim modules,
`sim_types.nim` owning `GameVersion`, the flatty wire types and the rune caps `MaxSayRunes` /
`MaxNoteRunes` / `MaxPromptRunes = 4000`); the mummy HTTP/websocket server implementing the Coworld
contract; the `decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` / `control.nim` commander
layer with its one-parallel-batch-per-turn, `attempt1Ms` / `retryMs` / `turnBudgetMs` /
`turnSpacingMs` deadlines, tolerant JSON extraction, rune truncation and fallback ladder; the binary
`COWLD…` replay of *inputs plus a per-tick `gameHash`*, re-simulated by **the same sim module**
compiled to wasm by `replay-viewer/config.nims`; the `client/` broadcast chrome
(`chrome_common.js` + `broadcast_core.js` + `replay_broadcast.html`); nimby + `Dockerfile` +
`Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the four-shard Nim test suite
(`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **this is a real-time grid loop whose rules are written into this repo and
whose seats are LLM commanders over a deterministic per-tick controller — the first row of the
starter table.** The precedent for forking paintbot for a grid port is seven deep (knights-archers,
pistonball, atari-cabinet, walker-waterworld, particle-worlds, smac-starcraft-micro, magent-battle).
The sim is **Nim inside this fork**, compiled twice — natively into the server binary and to wasm for
the viewer. There is no Python sim and no two-starter hybrid; that split is the documented recurring
failure (LEARNINGS babel/lantern, gridlock, magent round 1).

Where this note departs from coworld-ctf it says so. The departures are: the rules are RWARE's, not
paintbot's (§Sim module lists what is deleted); the arena is a small integer **grid** with static
geometry, so ctf's pixel arena, procedural map generator, map pool, map editor and mapkit are
deleted; the game is **fully cooperative** (one shared throughput number, no teams); and the port
carries three upstream-fidelity gates ctf has no equivalent of (§Sim module → "Proving the port").

### Source idea (verbatim)

> RWARE Robot Warehouse — pick up the requested shelves, deliver them, bring them back, don't
> deadlock in the aisle
>
> Port of Multi-Robot Warehouse (RWARE; Christianos et al., EPyMARL; Jumanji RobotWarehouse). Robots
> in a grid warehouse must deliver requested shelves to workstations and return them; loaded robots
> can't pass under other shelves; corridors are one robot wide; reward only on delivery (sparse).
> Tiny/small/medium/large layouts, 2-16 robots, 'hard' variants with fewer requests. It's cooperative
> logistics with collisions and deadlocks as the failure mode.
>
> Seats: 2-16
> Motive: fully cooperative, sparse reward
> Policy interface: per-tick move/turn/load; scripted/neural; LLM as a dispatcher over scripted robots
> is viable
> Fills gap: 08 Gridlock is competing fleets; RWARE is one cooperative fleet where *you don't control
> the other robots' policies* — ad-hoc coordination in corridors
> Integrity (anti-collusion): cooperative cross-play scoring; request stream seeded.
>
> Replay plan (watchability): top-down warehouse with request queue, delivered counter, and a deadlock
> detector that flags jams.
>
> Source: github.com/semitable/robotic-warehouse; Jumanji RobotWarehouse.

### Upstream, pinned

The rules reproduced here are **`semitable/robotic-warehouse` (`rware`) `rware/warehouse.py` +
`rware/__init__.py`**, fetched and read in full while writing this note. Every constant below is
quoted from those files; §Sim module records how the build pins them and how CI proves the port has
not drifted.

| Upstream fact | Value |
|---|---|
| Grid size from params | `height = (column_height + 1) × shelf_rows + 2`, `width = 3 × shelf_columns + 1` (`shelf_columns` must be odd) |
| Registered sizes | `tiny (rows 1, cols 3)`, `small (2,3)`, `medium (2,5)`, `large (3,5)`; `column_height = 8` everywhere |
| Difficulty | `request_queue_size = int(n_agents × d)`, `d ∈ {easy 2, normal 1, hard 0.5}` |
| Actions | `NOOP 0, FORWARD 1, LEFT 2, RIGHT 3, TOGGLE_LOAD 4` (`msg_bits = 0`, so the action is a plain `Discrete(5)`) |
| Directions | `UP 0, DOWN 1, LEFT 2, RIGHT 3`; `LEFT`/`RIGHT` rotate 90° through the wrap list `[UP, RIGHT, DOWN, LEFT]` |
| Highways (aisles) | `x % 3 == 0` **or** `y % (column_height+1) == 0` **or** `y == height-1` (delivery row) **or** the queue lane: `y > height − (column_height+3)` and `x ∈ {width//2 − 1, width//2}` |
| Shelves | one standing shelf on **every** non-highway cell at reset |
| Workstations (goals) | exactly two, `(width//2 − 1, height−1)` and `(width//2, height−1)` |
| Spawn | `n_agents` distinct uniformly random cells (any cell), uniformly random directions |
| Requests | `request_queue_size` distinct shelves drawn uniformly at reset |
| Loaded-move veto | a carrying robot may not enter a cell holding a **standing** shelf — unless that cell holds a robot that is itself carrying (then the shelf is not standing) |
| Collision resolution | one directed graph of `cell → requested cell`; per weakly-connected component: a cycle of length 2 (head-on swap) moves nobody, any longer cycle moves everybody on it, an acyclic component moves the robots on its longest path |
| Load | `TOGGLE_LOAD` while empty picks up the standing shelf on the robot's own cell, if any |
| Unload | `TOGGLE_LOAD` while carrying drops the shelf **only on a non-highway (storage) cell**; on a highway it is a no-op |
| Delivery | after moving, a shelf sitting on a workstation cell **and in the request queue** is delivered: reward, then that queue entry is replaced by a uniformly drawn shelf not currently in the queue |
| Reward | registered envs use `INDIVIDUAL` (+1 to the robot on the workstation cell); `GLOBAL` pays +1 to everyone; `TWO_STAGE` pays 0.5 + 0.5 |
| `max_steps` | 500 |
| `sensor_range` | 1 (a 3×3 window), `max_inactivity_steps = None` |

Two derived numbers this note relies on, both asserted by a test rather than trusted from this
paragraph:

- **`tiny` = 10 wide × 11 tall** (`3×3+1 = 10`, `9×1+2 = 11`). Highway `x ∈ {0,3,6,9}`,
  `y ∈ {0,9}`, `y = 10`, and the queue lane `x ∈ {4,5}` for `y ≥ 1` — which removes the whole middle
  shelf block, exactly as upstream's docstring says it should. **32 shelves** in two 2×8 blocks
  (`x ∈ {1,2,7,8} × y ∈ 1..8`). Workstations `(4,10)` and `(5,10)`.
- **`1×5` (rows 1, cols 5) = 16 wide × 11 tall.** Highway `x ∈ {0,3,6,9,12,15}`, `y ∈ {0,9}`,
  `y = 10`, queue lane `x ∈ {7,8}` for `y ≥ 1`. **64 shelves** in four 2×8 blocks
  (`x ∈ {1,2,4,5,10,11,13,14} × y ∈ 1..8`). Workstations `(7,10)` and `(8,10)`. This is upstream's
  own `full_registration` shape `rware-1x5-8h-4ag-2req-indiv-v2`, not an invention.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / SPEC §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time grid loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-rware-warehouse` | §Packaging |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=shuttle\|courteous`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art only) |
| Two name spaces | §The game (aliases `Alpha`/`Bravo`/`Charlie`/`Delta` in-game; real names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 337 s, worst 472 s, engine stop 660 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 4`, three times |
| Simultaneous decisions as one parallel batch | §Decisions (all four seats in one `curl.makeRequests` batch per turn) |
| Replay bytes self-sufficient | §Server (config JSON, joins, orders, chats, per-tick hashes, seed) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Request stream seeded and unsteerable (the idea's integrity note) | §Sim module (dedicated request RNG stream) |

---

## The game

A small warehouse. Shelves stand in blocks; the aisles between them are **one cell wide**. Two
workstations sit at the bottom of the middle lane. A station board shows the **requested shelves**;
a robot must drive to a requested shelf, drive **under** it, lift it, carry it to a workstation, and
then carry it back to an empty storage slot and put it down, because a loaded robot cannot pass
under another standing shelf and cannot pick anything else up until it has stowed what it holds.
Four robots share the aisles. **Nobody scores alone**: the number the league reads is the number of
shelves the fleet delivered, and the only way to lose it is to jam the aisles.

### Seats, robots, aliases

- **`num_agents` = 4.** Exactly four seats, always — in both manifest variants and in the
  certification fixture. One seat drives exactly one robot. Four is the number that makes the idea's
  gap real (you drive one robot and cannot control the other three) while seating **both LLM
  champions and both scripted fillers in a single episode**, which is what makes the "cross-play,
  not self-copies" integrity requirement true by construction rather than by luck. The idea's 2–16
  range is answered at 4; other counts are §Out of scope.
- **Two name spaces.** In-game, the seats are **`Alpha`, `Bravo`, `Charlie`, `Delta`** (the starter's
  `IdentityNames`, slot order). Those aliases are the only names that appear in an observation, a
  prompt, an order, a `say`, a radio line or a sprite label. The seats' **real policy/player names**
  (`daveey`, `daveey-1`, `Baseline (1)`, `Baseline (2)`) live only in `results.names`, in the
  replay's join records and in the viewer's scorebug. `showPlayerLabels` is **false**, as in the
  starter's paintball variant, so no in-board sprite can leak an identity. A seat can never learn who
  it is working with — the idea's anti-collusion requirement.
- **Robot colours** are cosmetic and fixed by slot: Alpha red, Bravo blue, Charlie green, Delta
  yellow (the starter ships soldier art in exactly those four colours).
- **Shelf ids** are `S01`…`S32` (tiny) / `S01`…`S64` (wide), assigned at reset in scan order
  (ascending `y`, then ascending `x`) over the non-highway cells. **Workstations** are `W1` (the
  left goal cell) and `W2` (the right one). Cells are `(x, y)`, `x` rightwards from 0, `y` downwards
  from 0.

### The clock

- **Tick** = one RWARE `step`. `maxTicks = 500` — upstream's own `max_steps`, kept.
- **Command turn** = one order round, every `turnTicks = 20` ticks, beginning with turn 1 at tick 0
  before any stepping. **25 command turns per episode.** One game per episode (`maxGames = 1`): the
  game is cooperative, so there is no side to swap.
- A seat's order stands until it changes it or the pilot finishes it; the pilot (§Decisions) emits
  one RWARE action per robot per tick in between.

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (at tick `20·(T−1)`), in this order:

1. The engine snapshots the world and builds all four seats' observation objects (§Decisions).
2. All four seats' LLM requests go out as **one parallel batch** (`curl.makeRequests`, the starter's
   `decideAll` shape), attempt-1 deadline `attempt1Ms = 9000`. Scripted seats compute locally,
   instantly, and consume no request.
3. Each seat that timed out, errored, returned non-JSON or returned no usable `verb` is retried
   **once**, again as a single batch, `retryMs = 4000`.
4. A seat still without a usable reply gets the **`courteous`** scripted order computed server-side,
   and a `fallback` record is written (§Decisions).
5. Orders are applied, in ascending slot. A seat that named a valid order takes it; a seat whose
   reply carried no `verb` keeps the order it had; an order whose fields do not validate is
   **repaired to that seat's previous order** (turn 1's default is `courteous`'s order), never
   dropped into "unactuated", and counted in `ordersRejected` — the starter's `directives.nim`
   repair-don't-reject discipline.
6. `say` (≤ 120 runes) and the accepted order become replay chat records. `say` is the fleet radio:
   **every** seat hears **every** seat's last-turn `say` in its next observation. `notes`
   (≤ 240 runes) is private and echoed back to that seat only.
7. `turnSpacingMs = 12000` is a floor on the wall clock between consecutive **batch starts** (the
   starter's mechanism, kept), which is what keeps four seats under the sidecar's 30 req/min
   per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the
game and nothing else mutates the world**:

1. `tick += 1`. Snapshot the two occupancy layers (robots, standing shelves). Every rule below reads
   the snapshot, never a partially updated world.
2. **Choose one action per robot**, in ascending slot, from that seat's current order via the pilot
   (§Decisions → "The pilot"). The action is one of `NOOP, FORWARD, LEFT, RIGHT, TOGGLE_LOAD`.
3. **Veto impossible loaded moves** (upstream verbatim): for each robot requesting `FORWARD` while
   carrying, if the target cell is on the board and holds a **standing** shelf, and the target does
   **not** hold a robot that is itself carrying, the action becomes `NOOP` and the robot is marked
   `blocked_by_shelf` for this tick.
4. **Build the move graph and commit movers.** Nodes are cells; each robot contributes one edge from
   its own cell to its requested target (a self-edge if it is not requesting `FORWARD`, or if the
   target would leave the board — upstream clamps the target to the board, which makes a wall bump a
   self-edge). Per weakly-connected component:
   - **a.** If the component contains a directed cycle: if the cycle has length **2** (a head-on
     swap) **nothing in that component moves**; otherwise **every robot standing on a node of that
     cycle moves** and nothing else in the component does. (A self-edge is a length-1 cycle: the
     stationary robot "moves" to its own cell, i.e. everyone queued behind a stationary robot stays.)
   - **b.** Otherwise the component is a DAG: take its **longest directed path**; every robot on that
     path moves, nothing else in the component does. This is what lets a queue of robots step forward
     together behind one that has somewhere to go.
   - **Determinism pin** (a divergence from networkx's implementation-defined choices, §Sim module):
     cells are ordered by index `y·W + x`; the cycle search is a DFS started from the
     lowest-indexed node of the component, visiting successors in ascending index order, returning
     the **first** cycle found; the longest path is the standard DAG dynamic program, ties broken
     toward the path whose **start node has the lowest index**.
5. **Apply**, ascending slot: a committed `FORWARD` moves the robot one cell in its facing direction
   and its carried shelf with it; `LEFT`/`RIGHT` rotate 90° through `[UP, RIGHT, DOWN, LEFT]`;
   `TOGGLE_LOAD` while empty lifts the standing shelf on the robot's own cell if there is one;
   `TOGGLE_LOAD` while carrying puts the shelf down **only if the robot's cell is not a highway
   cell** (on a highway it does nothing); `NOOP` does nothing. A robot that requested `FORWARD` and
   was not committed does not move and its `blockedMoves[slot]` counter increments.
6. **Rebuild the occupancy layers** from the robots' and shelves' new positions.
7. **Deliveries**, workstations in the fixed order `W1`, `W2`: if a shelf is on the cell **and** in
   the request queue, it is delivered — `delivered[slot] += 1` for the robot standing on that cell,
   `teamDelivered += 1`, a `deliver` event is emitted, the shelf is removed from the queue and that
   queue slot is refilled with a shelf drawn by the **request RNG** uniformly from the shelves not
   currently in the queue. The delivered shelf stays on the robot's forks; it must still be stowed.
8. **Jam detection.** `stuck[slot] += 1` for every robot that requested `FORWARD` this tick and did
   not move; otherwise `stuck[slot] = 0`. A **jam** is the set of robots with `stuck ≥ jamTicks = 8`
   that are linked by the blocking relation (robot A's target cell is occupied by robot B), closed
   transitively, with **at least 2 members**. Entering a jam emits `jam`; leaving it emits
   `jamclear`; `jamTicksTotal` counts every tick a jam is active and `longestJamTicks` its longest run.
9. Mix the tick into `gameHash` and append it to the replay's hash chain.
10. Evaluate the end conditions.

### Scoring formula and sign

```
delivered[s]   = requested shelves delivered by seat s's robot          (integer, >= 0)
teamDelivered  = sum over s of delivered[s]                             (the whole game)
scores[s]      = 100 * teamDelivered + delivered[s]
```

**Sign: higher is better; no term is ever negative.** Jams, blocked moves, wasted turns and dropped
shelves subtract nothing — they cost deliveries, which is the only currency, exactly as the idea's
"reward only on delivery (sparse)" pins it.

The first term is the whole game and is **identical for all four seats**: pure common interest, the
idea's "fully cooperative". The second term exists so the ladder is not a pure draw machine and is
deliberately an epsilon: a full round trip in the tiny layout is at least 12 ticks (lift → 8+ cells
to a workstation → back to a slot → drop), so `delivered[s] ≤ 500/12 = 41 < 100` and a test asserts
`delivered[s] < 100` over every recorded episode. The ordering is therefore strictly lexicographic —
**team throughput first, own deliveries only as a tie-break** — and a robot that hogs the workstation
lane to farm the epsilon loses whole deliveries of fleet throughput to gain one unit.

**The league ranks by `results.scores[s]`** (the platform's Elo, 1000 start / K 32, is computed from
these per-episode per-seat numbers). `results.win[s]` is `teamDelivered >= parDeliveries` — the same
boolean for all four seats, a "did the fleet do its job" flag, not a duel — and `results.winner` is
always `null`, because a cooperative episode has no winner. `parDeliveries` is a config field
(8 in `warehouse`, 5 in `wide-hard`).

**Cross-play (the idea's integrity note).** Scoring is cross-play, not self-copies: the certification
fixture seats **two `courteous` and two `shuttle`** scripted robots, and the league division runs
**two scripted fillers alongside the two prompt champions** (§Packaging), so a four-seat round robin
seats each champion with unfamiliar partners in essentially every episode. The game records what it
was given: `results.policyKinds = ["llm","llm","scripted","scripted"]` and `results.crossPlay = true`
when at least one LLM seat and at least one scripted seat sat together. And the **request stream is
seeded and unsteerable**: it is drawn from a dedicated RNG stream (§Sim module) whose draws depend
only on `seed` and the number of deliveries so far, never on which seat delivered, so no pair of
seats can arrange the queue between them.

### End conditions and legal `results.reason` values

The episode ends at the first of: **tick cap** (`tick == maxTicks`, the normal path) or the
**wall-clock stop**. There is no early win, no early loss and no inactivity termination —
`maxInactivityTicks` is deliberately **0 (disabled)**, diverging from upstream's optional
`max_inactivity_steps`, because ending a jammed episode early would hide the very failure the idea
asks the replay to show. A totally deadlocked fleet plays out its 500 ticks with the jam flag lit and
scores 0.

`results.reason` is the starter's closed enum; exactly these three values are legal and the game
emits nothing else:

- **`complete`** — 500 ticks ran. The healthy value.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine
  stops at the current tick, settles with the **real** deliveries so far (never zeroed, so a deadline
  episode is still rankable), writes `results.json` and the replay, and exits 0. **Declared
  acceptable** for SPEC §Definition of done check 4. The budget guard below exists so it should never
  fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from
  the last completed tick, `results.stopDetail` names it (≤ 200 runes, rune-truncated), artifacts are
  still written, exit 0. A defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode
  reports it.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn (all seats fall to `courteous`, microseconds per turn), the remaining ticks run at full speed,
and the episode still ends `complete`. A `budget_guard` record names the turn it fired.

A seat that never connects, disconnects mid-episode, or fails every decision **does not end the
episode**: its robot plays `courteous` and the episode runs to its natural end with
`deadSeats[s] = true`. Nothing a player container does can stop the clock — the starter's
`lobbyJoinTimeoutTicks` bounds the lobby and its strike rule stops a silent seat from consuming the
per-turn deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {shuttle, courteous}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=courteous` (the starter's "anything unrecognised is the published default" rule in
`baselines.nim`). A scripted policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/rware-warehouse/anthropic_api_key` — the
hive 2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` /
`LLM provider is unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game
container only. No `USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM
call.

`src/rware_warehouse_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"shuttle"|"courteous"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then acknowledge
frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3 close-frame race:
whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/rware/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

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

One command turn every **20 ticks**; **25 turns per episode**. At each turn the server builds all
**four** seats' request bodies and issues them as **one parallel batch** — never sequentially; this is
a simultaneous-decision game and serial calls would quadruple the wall clock for nothing. At most 4
calls in flight; at most `4 × 25 × 2 = 200` calls per episode including retries.

```
attempt1Ms                          9.0 s
retryMs                             4.0 s
turnBudgetMs                       14.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                      12.0 s   -> 4 seats x 60/12 = 20 req/min  (sidecar cap: 30)

25 turns x max(spacing 12 s, budget 14 s), absolute worst          = 350 s
   typical (haiku answers in ~3-4 s, so spacing dominates)         = 300 s
500 ticks, 4 robots, integer Nim + BFS over <=176 cells, fastMode  =   2 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400; typical 15 s)    =  15 s   (cap: 100 s)
gameOverTicks hold + results + replay write (retried uploader)     =  20 s
                                                                   -------
typical total                                                      = 337 s   < 720 s
absolute worst case (350 + 2 + 100 + 20)                           = 472 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                            = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                              = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_rware_manifest.nim` asserts it.

**Rate guard.** `turnSpacingMs` pins the steady state at 20 req/min, but a turn in which every seat
retries issues 8 requests. The engine therefore keeps a **rolling 60 s request counter**: if issuing
the next batch would push the trailing-60 s count above **28**, the seats that would exceed it skip
the call for that turn and take the `courteous` order with `cause = "rate_guard"`. Bounded, logged,
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
seat's order for that turn becomes the **`courteous`** scripted order computed inside the game (the
same proc the `courteous` baseline uses — imported, never duplicated), and a `fallback` record is
written with `cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard,
budget_guard, disconnected}`. `results.fallbackTurns[s]` counts them.

**No failure mode leaves a robot unactuated.** The pilot always has an order: this turn's, else last
turn's, else `courteous`'s. A seat that never connects is reported once to
`COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload — exactly
`{"message", "failed_policy_index"}`, nothing else.

### Per-seat observation: exactly what is visible and what is hidden

**Visible.**

- **The floor plan, in full and always** — a warehouse robot knows its own building: grid size, every
  highway cell, every storage cell, both workstations. It is static for the whole episode and is sent
  once, at registration, as an ASCII map (`#` storage slot, `.` aisle, `W` workstation), then referred
  to by coordinates.
- **The request board, in full** — the `requestQueue` shelf ids with each shelf's **home cell** (the
  storage slot it was placed in at reset, which never changes). The station broadcasts what it wants;
  that is the premise of the game.
- **Everything about the seat's own robot** — cell, facing, loaded/empty, which shelf it holds, its
  current order, how the last order finished, and how many ticks it spent blocked since the last turn.
- **Other robots within Chebyshev radius `sensorRange = 3`** of the seat's own robot: alias, cell,
  facing, loaded or not. Upstream's `sensor_range` is 1; **widened to 3 here** because a seat plans 20
  ticks ahead and a 3×3 window cannot see a corridor conflict forming. Documented divergence.
- **Cell contents within the same radius 3**: whether each storage slot currently holds a standing
  shelf (so a seat can find a free slot to stow into) and whether that shelf is requested.
- **The fleet radio** — every seat's `say` from the previous turn, tagged with the speaker's alias.
  This is the only channel through which intentions travel, and it is what the idea's "ad-hoc
  coordination in corridors" is played through.
- **Public fleet statistics** — `teamDelivered`, the tick, the turn, and the jam flag with the aliases
  of the robots in it (a jam is audible: the floor supervisor calls it out).

**Hidden.** Every other seat's current **order** and `notes`; every other seat's **real player name**,
policy name and kind; robots and shelf-slot occupancy outside radius 3; which robot is carrying which
shelf unless that robot is inside radius 3 (so "I have S12" only travels by radio); the request RNG's
future draws; and the other seats' fallback/decision statistics. Nothing about any seat's identity
ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `your_notes`)
into the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "Charlie",
  "fleet": ["Alpha", "Bravo", "Charlie", "Delta"],
  "turn": 7, "of": 25, "tick": 120, "turn_ticks": 20, "ticks_left": 380,
  "warehouse": {"width": 10, "height": 11, "stations": {"W1": [4, 10], "W2": [5, 10]},
                "storage_slots": 32, "sensor_range": 3},
  "requests": [
    {"shelf": "S07", "home": [1, 3]},
    {"shelf": "S12", "home": [7, 4]},
    {"shelf": "S19", "home": [2, 6]},
    {"shelf": "S28", "home": [8, 8]}
  ],
  "you_are": {
    "cell": [3, 6], "facing": "down", "loaded": true, "carrying": "S19",
    "order": "deliver W1", "order_age_turns": 2,
    "last_order_result": "running",
    "blocked_ticks_last_turn": 6,
    "on_aisle": true
  },
  "seen": {
    "robots": [
      {"alias": "Alpha", "cell": [3, 4], "facing": "down", "loaded": false},
      {"alias": "Delta", "cell": [4, 7], "facing": "up",   "loaded": true}
    ],
    "free_slots": [[2, 5], [2, 7], [1, 8]],
    "shelves_here": [{"shelf": "S22", "cell": [2, 6], "requested": false}]
  },
  "radio": [
    {"from": "Alpha", "text": "taking S07, I'll come down column 3"},
    {"from": "Delta", "text": "W2 is mine, someone clear the queue lane"}
  ],
  "fleet_status": {"delivered": 9, "jam": true, "jam_robots": ["Charlie", "Delta"], "jam_ticks": 6},
  "your_notes": "after S19 stow at (2,7) and pick up S28"
}
```

Field rules. `facing` is one of `up|down|left|right`. `last_order_result` is one of
`running|done|shelf_gone|no_path|no_free_slot|not_loaded|already_loaded` — the pilot's honest report
of why the previous order ended, which is what lets a seat recover from a race with an unseen robot.
`free_slots` lists at most 8 visible empty storage cells, nearest first. `radio` carries at most 3
lines, the most recent first, each already truncated to 120 runes. `requests` is always exactly
`requestQueue` entries long so the array shape never changes.

### Reply schema and per-field caps

```json
{"verb": "fetch", "shelf": "S12", "say": "taking S12, keep column 7 clear", "notes": "then stow at (2,7)"}
```

| Field | Type | Cap / domain |
|---|---|---|
| `verb` | string | **≤ 8 runes**; enum `fetch` \| `deliver` \| `stow` \| `yield` \| `hold`, lower-cased before matching |
| `shelf` | string | required iff `verb == "fetch"`; **≤ 4 runes**; must be an id currently on the request board |
| `station` | string | optional when `verb == "deliver"`; **≤ 2 runes**; enum `W1` \| `W2`; default = the nearer station by path length, ties to `W1` |
| `x`, `y` | integer | optional when `verb == "stow"`; clamped into `[0,width)` × `[0,height)` (the starter's clamp-don't-reject rule); if the clamped cell is not a storage cell the order degrades to nearest-known-free-slot |
| `say` | string | **≤ 120 runes** (`MaxSayRunes`) — the fleet radio; heard by every seat next turn and drawn in the feed |
| `notes` | string | **≤ 240 runes** (`MaxNoteRunes`) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded
error text — is truncated on RUNE boundaries** via the starter's `truncateRunes`/`runeSubStr`, never
by byte index. Byte truncation is what makes a replay that renders in a browser fail a strict UTF-8
parser; `tests/test_rware_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level keys are ignored. A reply with a valid `say` but no `verb` is **usable** (the seat
keeps its current order and the radio line is delivered). A reply that is not a JSON object is a
parse failure. An order whose `verb` is valid but whose required argument is missing or unknown is
**repaired to the seat's previous order**, counted in `ordersRejected`, and reported back next turn
as `last_order_result` unchanged. `yield` is spelled `yield` on the wire and `okYield` in the Nim
enum, because `yield` is a Nim keyword.

### System prompt (fixed, identical for both champions)

```
You are the driver of ONE robot in a shared warehouse. Three other robots work the same
aisles. You do not control them and you cannot see their orders. Every 20 simulation ticks
you issue ONE order for your robot and a deterministic pilot drives it until you change it.

THE WAREHOUSE
- A grid. '#' cells are storage slots that hold shelves, '.' cells are aisles one robot
  wide, 'W' cells at the bottom are the two workstations W1 and W2.
- An EMPTY robot can drive under standing shelves. A LOADED robot CANNOT: it must stay on
  aisles and on empty storage slots. That is what causes jams.
- To score: drive to a requested shelf's home cell, lift it, carry it to W1 or W2. The
  moment it reaches a workstation the fleet is credited and a NEW shelf is requested.
- You are still carrying it. You cannot lift anything else until you put it down, and you
  can only put it down on an EMPTY storage slot ('#' with no shelf), never on an aisle.
- Two robots that meet head-on in a one-wide aisle BOTH stay put, forever, until one of
  them yields. A line of robots CAN move together if the one in front has somewhere to go.

YOUR ORDERS (one per turn; the pilot keeps executing it until it finishes or you change it)
- {"verb":"fetch","shelf":"S12"}          drive to S12's home cell and lift it
- {"verb":"deliver","station":"W1"}       carry what you hold to that workstation
- {"verb":"stow","x":2,"y":7}             put what you hold down on that empty slot
                                          (omit x,y for the nearest empty slot you can see)
- {"verb":"yield"}                        back out to the nearest aisle junction and wait
- {"verb":"hold"}                         stand still

SCORE
The only number that counts is how many requested shelves THE FLEET delivers. Everyone gets
the same score. A robot that sits in a jam costs the fleet more than it costs itself.

TALKING
"say" is a radio call every other robot hears next turn. It is the ONLY way they learn what
you are doing. Use it to claim a shelf, to claim a workstation, or to ask someone to back
off. "notes" comes back to you next turn and to nobody else.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the character {
and end with }. No prose, no markdown, no code fences.
{"verb":"fetch","shelf":"S12","say":"<=120 chars","notes":"<=240 chars"}
```

### Champion #1 — `rware-warehouse-picker` (owner **daveey**), `PLAYER_PROMPT`

```
Work the shelf that nobody else has claimed. On turn 1, read the request board, pick the
requested shelf whose home cell is CLOSEST to you, and say exactly which one you are taking
and which column you will use to come back down - e.g. "taking S12, returning down column 6".
Then never change your mind unless the radio tells you someone else already has it.
Before you commit to a shelf, read the radio: if another robot claimed it, take the next
nearest UNCLAIMED one instead and say so.
Loaded, go straight to a workstation and pick the one nobody has claimed on the radio; say
which one you took. The instant you are credited, stow: use "stow" with no coordinates so
the pilot picks the nearest empty slot, and get off the queue lane below the shelf blocks -
that lane is where every delivery jams.
If your observation says blocked_ticks_last_turn is 8 or more, or the jam flag names you,
issue "yield" for exactly one turn, say "yielding, come through", and then resume the order
you were on. Never issue "yield" twice in a row: two robots that both yield forever deliver
nothing.
If your last_order_result is shelf_gone, immediately fetch the nearest other requested shelf.
If it is no_free_slot, stow with explicit coordinates on a slot you saw earlier.
```

### Champion #2 — `rware-warehouse-router` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Run a lane discipline and hold it. Decide once, on turn 1, from your starting cell: if your
x is left of the workstations you are a LEFT-SIDE robot, otherwise a RIGHT-SIDE robot. Say
which you are. Only ever fetch requested shelves whose home cell is on your side, and only
ever deliver to the workstation on your side (left -> W1, right -> W2). Say your side and
your station on turn 1 and repeat it whenever the radio shows someone drifting into it.
Within your side, always take the requested shelf with the SMALLEST y (highest up the
board) first, so loaded robots come down the aisles and empty robots go up under the
shelves - the two flows never meet head-on in the same lane.
Stow every delivered shelf on the FIRST empty slot on your own side, using explicit x,y from
the free_slots list, and prefer a slot high up rather than one next to the workstation lane.
If the jam flag names you and the other jammed robot is on your side, "hold" and say
"holding, you go"; if it is not on your side, "yield" and say which lane you are freeing.
Only one of you should move: use your alias order (Alpha, Bravo, Charlie, Delta) - the
earlier alias holds, the later one yields.
If there are no requested shelves on your side at all, and only then, cross over, say
"crossing to the other side", and work the nearest requested shelf.
```

### The pilot (deterministic, shared by every policy)

`src/rware/pilot.nim` — the starter's `control.nim` (directive → per-tick actuation), retargeted from
pixel steering to RWARE's five discrete actions. It runs once per robot per tick and is the **only**
producer of actions. There is no randomness in it at all. `path(u, goal)` is a breadth-first search,
4-connected, over the robot's *believed* grid: every cell for an empty robot; for a loaded robot only
highway cells, the destination cell, and storage cells the robot has **seen** to be empty this
episode (unseen storage cells are assumed to hold a shelf — conservative, so loaded robots plan along
the aisles). Neighbours are expanded in the fixed order `up, right, down, left`, so the path is
unique; other robots are **not** obstacles in the plan (they move).

| Order | Goal cell | Terminal action | Finishes with |
|---|---|---|---|
| `fetch S` | `S`'s home cell | on arrival, `TOGGLE_LOAD` | `done` when loaded; `shelf_gone` if the cell holds no shelf on arrival; `already_loaded` if issued while carrying; `no_path` if BFS fails |
| `deliver W` | that workstation cell | none — the engine credits the delivery when the shelf arrives | `done` on credit; `not_loaded` if issued while empty; `no_path` if BFS fails |
| `stow [x y]` | the named storage cell, else the nearest **seen-empty** storage cell (ties by lowest cell index) | on arrival, `TOGGLE_LOAD` | `done` when unloaded; `no_free_slot` if none is known; `not_loaded` if issued while empty |
| `yield` | the nearest **passing place** — a highway cell with ≥ 3 free orthogonal neighbours, i.e. an aisle junction (ties by lowest cell index) | none; `NOOP` on arrival | `done` on arrival, then holds |
| `hold` | — | `NOOP` every tick | never finishes |

Given a goal cell, each tick:

1. If the robot is already on the goal cell, emit the order's terminal action (or `NOOP`).
2. Otherwise take the first cell of `path`. If the robot faces it, emit `FORWARD` — **even if a robot
   is standing there**, because RWARE's chain rule lets a queue advance behind a mover, and refusing
   to try would forfeit that. If it does not face it, emit `LEFT` or `RIGHT`, whichever is the shorter
   rotation; a 180° turn emits `RIGHT` twice (deterministic).
3. If the path is empty (no route), emit `NOOP` and report `no_path` at the next turn boundary.
4. An order that has finished leaves the robot **idle**, and an idle robot executes the fixed **park
   rule**: drive to the nearest highway cell that is *not* in the workstation queue lane and `NOOP`
   there. Without it, a robot that finished a delivery mid-turn would stand on the workstation and
   wall off the only lane to it.

### Scripted baselines (both shipped as fillers; `courteous` is also the server-side fallback)

`src/rware/baselines.nim`, the starter's module retargeted. Both emit the **same** order object an LLM
does, through the same validator, which is what makes the bounded-orders test meaningful. Neither
ever emits `say` or `notes` — they are the robots whose policies you do not control and who will not
talk to you, which is precisely the ad-hoc coordination problem the idea names.

**`shuttle`** — `PLAYER_SCRIPTED=shuttle`. Pure greed, no jam handling. Each turn, in order:
1. Carrying a delivered shelf → `stow` (nearest seen-empty slot).
2. Carrying an undelivered requested shelf → `deliver` to the nearer workstation, ties to `W1`.
3. Empty → `fetch` the requested shelf whose home cell has the shortest BFS path from the robot; ties
   by lowest shelf id.
It is short, it is a real opponent to jam against, and it is the control that answers "did the LLM
actually coordinate?".

**`courteous`** — `PLAYER_SCRIPTED=courteous`, and the fallback. Each turn, in order:
1. `blockedTicksLastTurn ≥ yieldAfter (6)` **and** at least one visible robot with a lower slot index
   is also blocked → `yield` (this turn only; the tie-break by slot index means exactly one robot in
   any pair yields, which is what actually clears a jam).
2. Carrying a delivered shelf → `stow`, preferring a free slot at least 2 cells away from the
   workstation queue lane.
3. Carrying an undelivered requested shelf → `deliver` to the workstation with fewer visible robots
   within radius 3, ties to the nearer one, then to `W1`.
4. Empty → `fetch` the requested shelf minimising `path(me, home) − contentionPenalty`, where
   `contentionPenalty = penalty (4)` if a visible other robot is strictly closer to that shelf than
   this robot is; ties by lowest shelf id.

Like the starter's `DefaultBaselineParams`, the three tunables (`yieldAfter = 6`, `penalty = 4`,
`stowClearance = 2`) are a parameter object chosen by `tools/tune_baselines.nim`'s head-to-head sweep,
not guessed; `tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_rware_tuning.nim`
asserts the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/rware/`. The fork is a rename sweep
(`ctf` → `rware`, `CTF_WIRE` → `RWARE_WIRE`; a CI grep asserts no `ctf_`/`CTF_` identifier survives
outside comment history) plus the changes below. **The same modules compile twice**: natively into
`/bin/rware-warehouse` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason a Python sim is not an option here.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/rware/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/rware/` | **fork** (magic + game name only: `COWLDCTF` → **`COWLDRWH`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/rware/` (`control.nim` → `pilot.nim`) | **fork**, retargeted not rewritten | the per-turn parallel batch, the two deadlines, `turnSpacingMs`, the budget guard, tolerant parsing, the rune caps, repair-don't-reject, the fallback ladder |
| `src/ctf/sim_state.nim` → `src/rware/sim_state.nim` | **fork** | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/rware/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames`, the results JSON builder |
| `src/ctf/events.nim` → `src/rware/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/rware/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/rware/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/rware/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), the flatty wire types (field order sacred), `MaxSayRunes = 120`, `MaxNoteRunes = 240`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/rware/sim_config.nim` | **fork** | `GameConfig` lifecycle and `config.update` |
| `src/ctf.nim` → `src/rware_warehouse.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/rware_warehouse_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/rware_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p` fix and the buildx/`--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_{red,blue,green,yellow}.png`, `data/soldier_{red,blue,green,yellow}_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*,blue_*,green_*,yellow_*}.webp` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, fog-of-war
raycasting and the first-person PIP, spray cans, floor paint and the paint grid, the paint buff,
King of the Hill and `hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers,
grenades and the barrage, med kits, shields, cardboard barriers, trenches, perks, handicaps, lives
and respawns, teams and four-team free-for-all, shouts-as-cog-speech, achievements, campaign mode,
`maxGames > 1` side-swapping, and **all of the pixel-space map machinery**: `arena.nim`'s wall masks
and pixel queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`.
The board here is a small integer grid generated by a formula; every one of those is a config surface
the RWARE rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `rig_real/`) — robots are drawn as
baked chips (§Viewer → Art) and a 128 px rig is never used at 18 px per cell.

### New modules

- `src/rware/warehouse.nim` — the static world: the **transcription of upstream's
  `_make_layout_from_params`** (grid size, `highway_func`, the two goal cells), the shelf placement
  over non-highway cells, shelf-id assignment in scan order, cell↔index helpers, the passing-place
  table used by `yield`, and BFS. Pure integer; no pixie, no pixel queries.
- `src/rware/sim.nim` — the step loop of §The game: pilot actions, the loaded-move veto, the move
  graph and its deterministic commit, application, delivery and request refill, jam detection,
  `gameHash`, end evaluation. Imports and re-exports the sim modules, as the starter's does, so
  `import rware/sim` sees everything.
- `src/rware/robots.nim` — the robot arrays (`cell`, `facing`, `carrying`, `stuck`, `blockedMoves`,
  `delivered`, `stowed`), the shelf array (`home`, `cell`, `carrier`), the request queue, per-seat
  visibility (`Chebyshev ≤ 3`) and the per-seat "seen empty slot" memory the pilot plans on.
- `src/rware/jam.nim` — the deadlock detector of tick step 8, and the jam-span table the viewer's
  scrubber and sparkline read.
- `src/rware/upstream.nim` — every ported constant with its upstream citation comment beside it, in
  the style the starter uses for derived config values. This is the one file
  `tests/test_rware_upstream.nim` regex-checks against `vendor/upstream/warehouse.py`.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cells, ids, counts, BFS distances. There is no floating point
anywhere in `sim.nim`, `warehouse.nim`, `robots.nim`, `jam.nim`, `pilot.nim` or `baselines.nim`, and a
test greps for it. Nothing in this game needs a real number, which makes the native ↔ wasm hash chain
below exact by construction.

**Two RNG streams, both derived from `seed`, both independent of anything a policy does:**

1. `setupRng` — the reset draw: `n_agents` distinct cells and four directions (upstream's spawn), and
   the initial request queue.
2. `requestRng` — **the request stream**. Its `k`-th draw is a pure function of `(seed, k)`, where `k`
   is the number of deliveries so far. It is never consumed by anything else, so which shelf is
   requested next cannot be steered by which seat delivered, in what order, or at which workstation.
   That is the idea's "request stream seeded" integrity pin, and `tests/test_rware_requests.nim`
   asserts it by replaying the same seed with different seat behaviour and comparing the two request
   sequences.

The seed is randomised in `src/rware_warehouse.nim` before `config.update` (the starter's rule),
recorded in the replay config and in `results.seed`. Two episodes with the same seed and the same
orders are byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDRWH`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `num_agents`, `shelfColumns`, `shelfRows`, `columnHeight`,
   `requestQueue`, `maxTicks`, `turnTicks`, `parDeliveries`, `sensorRange`, `jamTicks`,
   `players[].name`, `slots[]`, `fastMode`), then the record stream — joins (name, slot, token),
   leaves, **per-turn order records** (the only inputs this game has), chat records
   (`register`/`directive`/`fallback`/`budget_guard`/`stop`/`result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/rware_replay.nim` — which imports the **same**
   `src/rware/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `rware_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `rware_frame`
   re-steps the sim from the recorded orders and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and surfaced
   as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: per robot `(slot, x, y, facing, carryingShelfId, stuck)`;
   per shelf `(id, x, y, carrier)`; the request queue in order; `teamDelivered`, per-seat `delivered`
   and `stowed`; the active jam set; then `tick`.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact
   cannot be re-derived from sim state, so the stop is written as one record applied by the *same
   proc* on record and on playback, and `tests/test_rware_replay.nim` runs the record→re-derive check
   for **every** end reason (`tickCap`, `wallClock`, `fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 500 hashes + 100 order records + ~20 chat records ≈ **20 KB**. Everything else is
re-derived in the browser.

### Documented divergences from upstream (mirrored into `vendor/PATCHES.md`)

1. **Deterministic collision tie-breaks.** Upstream delegates the cycle search and the longest path to
   networkx, whose choice among several cycles or several longest paths is implementation-defined. The
   port pins both (tick step 4). Required for a re-derivable replay; the *rules* — 2-cycles fail,
   longer cycles rotate, DAG longest path advances — are upstream's exactly.
2. **Who chooses the action changed, not what the actions are.** Per-tick RL policies are replaced by
   five high-level orders under a deterministic pilot — the idea's own "LLM as a dispatcher over
   scripted robots". The five-action space, the direction wrap list, the loaded-move veto, the
   load/unload rules, the delivery rule and the request refill are upstream's.
3. **`sensor_range` 1 → 3** (§Decisions → observation), because a seat plans 20 ticks ahead.
4. **Scoring is `100 × GLOBAL + INDIVIDUAL`** rather than upstream's registered `INDIVIDUAL`. The idea
   pins "fully cooperative"; the league needs a rankable per-seat integer. Both upstream quantities
   are recorded in `results` (`teamDelivered`, `delivered[]`).
5. **`max_inactivity_steps` disabled** (§The game → end conditions), so a jam is watched, not hidden.
6. **The request board shows home cells.** Upstream marks requested shelves only inside the sensor
   window; a dispatcher that cannot be told where a shelf lives cannot issue `fetch`. Home cells are
   static warehouse knowledge; *dynamic* facts (who is carrying what, which slots are free) stay
   radius-limited.
7. **`maxGames = 1`** — the starter's multi-game episode is not used; a cooperative game has no side
   to swap.

### Proving the port (the three fidelity gates)

- `vendor/upstream/warehouse.py` and `vendor/upstream/__init__.py` — **byte-pristine** copies from
  `semitable/robotic-warehouse` at a pinned commit, never edited. `vendor/UPSTREAM.md` records the
  repo, commit hash, fetch URL and each file's sha256; `vendor/LICENSE-rware` carries the upstream
  licence.
- `tests/test_rware_upstream.nim` — the **tripwire**: regex-parse the vendored files and assert
  byte-equality against every constant in `src/rware/upstream.nim` — the two grid-size formulas, the
  four `highway_func` clauses, the goal-cell formula, the action enum and its integer values, the
  direction wrap list, `column_height = 8`, the size table `{tiny (1,3), small (2,3), medium (2,5),
  large (3,5)}`, the difficulty table `{easy 2, normal 1, hard 0.5}`, `max_steps = 500` and
  `request_queue_size = int(agents × d)`. A re-vendor that changes a number **fails tests** instead of
  silently desyncing the game.
- `tests/test_rware_layout.nim` — a direct transcription of upstream's layout loop is run for
  `(rows, cols) ∈ {(1,3), (2,3), (2,5), (3,5), (1,5)}` and asserted equal, cell for cell, to
  `warehouse.nim`'s generator; `(1,3)` is asserted to yield exactly **10×11, 32 shelves, goals (4,10)
  and (5,10)**, and `(1,5)` exactly **16×11, 64 shelves, goals (7,10) and (8,10)**; and every vertical
  aisle is asserted to be exactly one cell wide.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with `turnTicks = 20` and four seats in the batch.
2. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration, **not** applied as a shout and **not** written to the replay chat stream; the server
   writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim. Any other chat text from a seat is dropped — drivers speak through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wallClock`, and
   written as the load-bearing stop record of point 5 above.

### The two named edits to `roster.nim`

1. **Aliases.** `seatAlias(slot)` returns `IdentityNames[slot]` → `Alpha`, `Bravo`, `Charlie`, `Delta`.
   Sprite labels and the label manifest inherit the two-name-space rule with no further change, and
   `showPlayerLabels` is false.
2. **`squadResultsJson` → `fleetResultsJson`** — one entry per seat, four entries in every seat-indexed
   array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits cell-space
   coordinates; the fov cache and shadowcasting are deleted (spectators see the whole warehouse; the
   *drivers'* radius-3 limit lives in the observation builder, not the renderer).
2. **Robot and shelf pools.** New pools `RobotSpriteBase` / `ShelfObjectBase` sized to
   `MaxRobots = 16` and `MaxShelves = 128`, filled in id order and emitted incrementally like the
   starter's other object families.
3. **Baked warehouse floor.** `arena_floor.png` is tiled and darkened at install with pixie, exactly
   the way the starter bakes endzone paint, plus aisle chalk lines, the two workstation pads and the
   shelf-block shadow — one static bake, so the per-frame cost is robots, shelves and overlays only.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player sockets
at `/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for
the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). Global
broadcasts are fire-and-forget so a slow viewer can never stall the episode.

### Results document (closed schema; `fleetResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":          ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
  "aliases":        ["Alpha", "Bravo", "Charlie", "Delta"],
  "scores":         [1405, 1403, 1403, 1403],
  "win":            [true, true, true, true],
  "winner":         null,
  "reason":         "complete",
  "teamDelivered":  14,
  "parDeliveries":  8,
  "delivered":      [5, 3, 3, 3],
  "stowed":         [5, 3, 2, 3],
  "blockedMoves":   [22, 61, 18, 40],
  "jams":           3,
  "jamTicks":       47,
  "longestJamTicks":21,
  "finalTick":      500,
  "turnsPlayed":    25,
  "seed":           1734029581,
  "policyKinds":    ["llm", "llm", "scripted", "scripted"],
  "crossPlay":      true,
  "llmTurns":       [25, 24, 0, 0],
  "fallbackTurns":  [0, 1, 0, 0],
  "ordersRejected": [0, 2, 0, 0],
  "deadSeats":      [false, false, false, false],
  "stopDetail":     ""
}
```

`winner` is always `null` (cooperative). Adding a key means updating `fleetResultsJson`, the
manifest's `results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit —
Coworld schemas are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDRWH`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"rware-warehouse/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"orders":[…],"radio":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.teamDelivered' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks, (.radio|length)' /tmp/ep.json
  ```
  Require `protocol == "rware-warehouse/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.teamDelivered > 0`, and the champion seats' orders with
  `source == "llm"`, real verbs and non-empty radio lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDRWH`, format version, `gameName` `rware-warehouse`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `shelfColumns`, `shelfRows`, `columnHeight`, `requestQueue`, `maxTicks`, `turnTicks`, `parDeliveries`, `sensorRange`, `jamTicks`, `players[].name` (real names), `slots[]`, `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| orders | per turn, per seat: the accepted order — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `verb`, `arg` (shelf id, station or cell), `say` (≤ 120 runes), `view` (the observation minus `your_notes`) |
| `fallback` | `turn`, `slot`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of ten kinds:**

`turn` `{n}`; `order` `{slot, verb, arg}`; `say` `{slot, text}`; `fallback` `{slot, cause}`;
`load` `{slot, shelf, cell}`; `deliver` `{slot, shelf, station, total}`; `stow` `{slot, shelf, cell}`;
`jam` `{slots, cells, tick}`; `jamclear` `{slots, ticks}`; `end` `{reason, teamDelivered, par}`.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`delivery`,
`jam`, `fallback`, `end`.** `turn`, `order`, `say`, `load` and `stow` drive the feed, not the
scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Load, Deliver, Stow, Blocked, Jam, JamClear, TurnStart, Directive,
Fallback, PhaseChange` and the mandatory trailing summary row (`type`, `ticks`, `events`,
`gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx/`--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/rware_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks
the viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one
piece: the Worker sets `Module.onRuntimeInitialized`, the module is emitted **non-modularized** as
`rware_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals),
`-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_rware_load_replay,_rware_frame,_rware_input,
_rware_packet_ptr,_rware_packet_len,_rware_mismatch_tick,_rware_error_ptr,_rware_error_len,
_rware_stage_ptr,_rware_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './rware_replay.js')` in that order.

`rware_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `rware_load_replay` re-simulates the whole episode once headlessly (500
  ticks × 4 robots of integer work — single-digit milliseconds in wasm), records the per-tick
  cumulative deliveries, the jam spans, the lull spans and the beat ticks, then resets and renders
  frame 0. That is what lets the deliveries sparkline and the scrubber beats draw at **full width on
  the first frame** instead of growing in.
- `rware_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — posted by the Worker only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means "a
frame is on the canvas", not "a file was fetched". On failure it sets **`data-replay-error`** on
`<html>` with the message, in `showFailure()`. Both are coworld-ctf's own signals, inherited
unchanged — this fork adds neither and removes neither. The `coworld-replay` postMessage bridge's
`ready` is posted **from a callback fired after** `data-replay-loaded="true"` is set, never on rAF
timing at the call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted
shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte.** Not edited, not reformatted;
  `tests/test_rware_viewer.nim` pins its sha256 against the starter's file. Everything this game adds
  lives in the appended game block. Its `markBeat`/`renderBeatMarkers`/`ingestBeats`/`renderClock`/
  `renderTransport`/`ingestLullSpans` remain; `ingestBeats` ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`,
  transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched;
  the appended block replaces only the *contents* of the scorebug plates, adds the request rail and
  the jam chip, and retargets the feed rows, the beat rendering, the momentum series and the endcard
  columns. A test asserts the starter's byte prefix is intact up to the documented splice marker and
  that the file only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_rware_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), the beat and lull machinery, the endcard
  builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.RWARE_WIRE`
  rename emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific draw call and the FPV
  pipeline. Added: `drawWarehouse`, `drawRobots`, `drawShelves`, `drawJam`, `drawRequestRail`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `attachMinimap(...)` call. **Zoom decision: dropped.**
    The board is a fixed 10×11 (or 16×11) grid with no off-frame area; `relayout()` fits it whole at
    every width (see "Legible at 360 px"), so per the pin a fixed arena drops `#viewpanel` entirely.
    `broadcast_core.js` tolerates a missing minimap (`pendingMinimap` stays null).
  - **`#fpv`** and all its children (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) and **`#povBadge`** — there is no
    per-robot point of view worth showing; the whole warehouse is the shot.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.beat-marker.steal`, `.beat-marker.return`, `.beat-marker.capture`,
    `.beat-marker.hillflip`, `.beat-marker.tagout`, `.beat-marker.gamestart` and
    `.beat-marker.gameover` CSS rules — those kinds are never emitted here.
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
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test:

| Starter string (file:where) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` | `<span>Robot</span><span>Delivered</span><span>Stowed</span><span>Blocked</span><span>Jams</span>` |
| `<span class="fl-cap">Lives left</span>` (endcard team block) | `<span class="fl-cap">Shelves delivered</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (scrub graph) | `<span class="momentum-label">DELIVERIES</span>` |
| `<span class="lives-label">Lives</span>` (scorebug plate) | `<span class="deliv-label">Delivered</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (locker room) | "Charging the robots…" |
| `#clock-caption` "In the locker room" | "Powering up" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" | "Replay hash mismatch at tick N — showing recorded orders" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline" | "deliveries / jams / result on the timeline" |
| team words `RED`/`BLUE` in `ec-tname`/plates | the seat's **alias** (`ALPHA`…`DELTA`) plus its colour chip |

**`tests/test_rware_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `spray`, `grenade`, `med kit`, `kill` — outside comment blocks, and asserts **zero**
matches; and asserts each replacement string above is present exactly once. A rename that
reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged. **No overlay sits in the transport band**: the board is laid out between the two
bands and every addition here (the request rail, the jam chip, the feed, the banners) is positioned
inside the board region or in the top band. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept) so the scrubber stays clickable
underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `warehouseBeat(tick, kind, slot, label)` — named so it can never
shadow `chrome_common.js`'s `markBeat` alias (the tandem 2026-08-23 hoisting trap) — appends
`<button class="beat-marker <kind> <colour>" title="…" aria-label="…">` to `#scrub` and seeks on
click. CSS exists for **every kind emitted and no others**: `.beat-marker.delivery`,
`.beat-marker.jam`, `.beat-marker.fallback`, `.beat-marker.end`. The game block never calls
`markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: 1 tick per animation frame at 30 fps** (speed chips `[0.5, 1, 2, 4, 8]`, default 1).
A 500-tick episode therefore plays for **16.7 s**, which is what lets `viewer_smoke.mjs --soak 10`
observe real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The warehouse**, drawn edge to edge: the baked floor with its aisle chalk, the shelf blocks as
   crate tiles, the two workstation pads labelled `W1`/`W2`, and the four robots as coloured chips
   with a facing chevron. A **requested** shelf wears a 2 px amber outline and its id; a **carried**
   shelf rides on its robot as a raised crate with a drop shadow, so "who is loaded" reads at a glance
   — and a loaded robot is why the aisle it is in is blocked.
2. **Request queue rail** (the idea's first ask) — a labelled strip in the **top** band, one chip per
   queue entry: the shelf id, its block coordinates, and the alias of the robot carrying it if that is
   publicly known. On delivery the chip flashes green, is struck through, and the new request slides
   in — so a spectator sees the board turn over.
3. **Delivered counter** (the idea's second ask) — the big numeral in `#clock`: `DELIVERED 14`, with
   `/ 8 par` beneath it, plus each seat's own count on its plate.
4. **Jam flag** (the idea's third ask — the deadlock detector) — while a jam is active, every robot in
   it gets a pulsing red ring, the contested cells get a red cross, a labelled `JAM` chip lights in
   the **top** band with the aliases and the tick count, and `#bannerlane` reads
   `JAM — CHARLIE · DELTA, 14 TICKS`. Clearing it banners `JAM CLEARED — DELTA BACKED OFF`.
5. **Clock** — `#clock-time` shows `tick 240/500 · turn 12/25`; `#clock-caption` shows
   `delivered 14 · jam 2 · blocked 61`.
6. **Scorebug plates** — four plates (two in `#plates-l`, two in `#plates-r`): the seat's **real policy
   name** (spectator side only), its in-game alias, its colour chip, its own delivered count as the
   numeral, and a `↯` glyph on any seat that has taken a fallback.
7. **Match feed** (`#killfeed`) — plain language, never internal notation: `ALPHA lifts S12 at (7,4)`,
   `ALPHA delivers S12 to W1 — 14 delivered`, `BRAVO stows S07 at (2,5)`, `CHARLIE yields at the
   junction`, **`JAM — CHARLIE · DELTA`**, **`JAM CLEARED AFTER 21 TICKS`**,
   `Alpha: "taking S12, keep column 7 clear"`, and
   `DELTA MISSED THE CALL — scripted order (timeout)`. The radio lines and the order lines are where a
   spectator sees the LLM playing.
8. **Deliveries sparkline** — the starter's `#momentum` SVG retargeted to one cumulative series
   (team deliveries over the episode) with the jam spans shaded red behind it and the playhead marked.
   Filled from the load-time pre-scan, so it draws at full width on the first frame. A flat stretch
   under a red shade is the whole story of a bad episode in one glance.
9. **Endcard** — `14 SHELVES DELIVERED — PAR 8 MET`, the four-seat table under the re-mapped header
   (`Robot | Delivered | Stowed | Blocked | Jams`), a jam summary line (`3 jams, 47 ticks lost, longest
   21`), and `TEAM SCORE 1403`. It stops at `var(--band)` and any seek dismisses it.
10. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    40 consecutive ticks with no `load`, `deliver`, `stow` or `jam` event, from the pre-scan), spoilers
    switch, tick readout, speed chips, the scrubber with its four beat kinds, and `#mmwarn` on a hash
    mismatch — all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets — no placeholders, no solid-colour squares, no
downloads.** The floor is `data/arena_floor.png`, tiled and darkened 18 % with chalk aisle lines,
baked once at install by pixie (the way the starter bakes endzone paint). Shelf crates are baked from
`client/art/walls/wall_h.jpg` and `wall_v.jpg` (the starter's crate/wall texture), tinted through
`data/pallete.png`, at three sizes (12, 18, 28 px) with a 1 px rim. Robots are **baked at load** by
`rig_art.nim`'s compositor from `data/soldier_{red,blue,green,yellow}.png` into three chip sizes
(12, 18, 28 px) × four facings × loaded/empty — 96 pre-baked chips — so drawing four robots a frame is
four blits. Workstation pads are procedural amber chalk boxes on the baked floor with `W1`/`W2` set in
`data/font.ttf`. The loading screen is the starter's locker room (`client/art/lockerroom/bg.jpg` plus
the four colour webps) with the caption re-labelled. The jam ring, the contested-cell cross and the
sparkline are procedural in the floor bake's palette.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim. The board is letterboxed to its native aspect, so the binding dimension in a 360 × 203
embed is the height: the 10 × 11 board renders at **18 px per cell** (164 × 203 px), the 16 × 11 board
at **18 px per cell** (288 × 203 px) — in both cases a 14 px robot chip with a 3 px chevron and a
2 px amber outline on requested shelves, which is legible, and in both cases the whole warehouse is in
frame, which is why `#viewpanel` is dropped. Three rules are added and asserted by
`tests/test_rware_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, each plate keeps only `alias + name + delivered`; the colour chip shrinks to 6 px
   and the fallback glyph moves inline.
3. Under `.tiny`, the request rail shows shelf ids only (no coordinates) and the jam chip becomes the
   `JAM` word plus its tick count, both at `--hudscale`-derived sizes so nothing is drawn outside the
   canvas (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-rware-warehouse`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `rware-warehouse`; **`game.name` is
  `rware-warehouse`** (hyphenated, matching the slug) so the secret namespace
  `secret://coworld/rware-warehouse/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, underscored, because the manifest image placeholder is derived
  from the compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two
  services/two images; this fork uses the one-image / two-entrypoints shape because the shared
  `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers precedent):

  ```yaml
  services:
    rware_warehouse:
      image: coworld-rware-warehouse:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{RWARE_WAREHOUSE_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:rware-warehouse
  src/rware_warehouse.nim` → `/bin/rware-warehouse`, and the same for
  `src/rware_warehouse_player.nim` → `/bin/rware-warehouse-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/rware-warehouse"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk`, pinned nimby with
  its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with the
  asset list swapped to `data/{arena_floor,ascii,pallete}.png`, `data/soldier_{red,blue,green,yellow}.png`,
  `data/font.ttf`, `client/art/walls/*`, `client/art/lockerroom/*`, `rware_replay.{js,wasm,data}`,
  `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`, `static_replay.js`,
  `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["rware", "warehouse", "cooperative", "logistics", "port"]`
    (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0); **`episode_timeout_minutes: 20` at the
    top level**, not under `game`.
  - `game.name = "rware-warehouse"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/rware-warehouse"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/rware-warehouse/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 4/4, `players` 4/4, `slots` 0/4 — the tandem 0.1.0 scar). `tokens` is described as
    runner-injected; **no `game_config` anywhere in this manifest contains a literal `tokens` array**
    (matriculate rejects "game_config must not include runner-managed tokens" — knights-archers
    0.1.0), while `config_schema` keeps *requiring* it because the runner injects it. Properties:
    `tokens`, `players`, `slots`, `seed`, `shelfColumns` (enum `[3, 5]`, default 3), `shelfRows`
    (enum `[1]`, default 1), `columnHeight` (default 8), `requestQueue`, `maxTicks`, `turnTicks`,
    `parDeliveries`, `sensorRange`, `jamTicks`, `attempt1Ms`, `retryMs`, `turnBudgetMs`,
    `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`,
    `minPlayers`, `fastMode`, `showPlayerLabels`, and `num_agents` (integer, `minimum: 4`,
    `maximum: 4`, default 4).
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-rware-warehouse/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"porting.md","title":"Porting RWARE","content":{"type":"uri","value":".../docs/PORTING-RWARE.md"}}]}`.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Two entries, `shuttle` and `courteous`, so **every
    declared player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 4` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "warehouse", "name": "Warehouse (tiny, 4 robots, 4 requests)",
     "description": "RWARE rware-tiny-4ag-v2 scale: a 10x11 warehouse with 32 shelves, two workstations and four robots, one per seat, working a four-shelf request board over 500 ticks and 25 command turns.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}, {"name": "Charlie"}, {"name": "Delta"}],
                     "num_agents": 4, "minPlayers": 4,
                     "shelfColumns": 3, "shelfRows": 1, "columnHeight": 8,
                     "requestQueue": 4, "parDeliveries": 8,
                     "maxTicks": 500, "turnTicks": 20, "sensorRange": 3, "jamTicks": 8,
                     "attempt1Ms": 9000, "retryMs": 4000,
                     "turnBudgetMs": 14000, "turnSpacingMs": 12000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "wide-hard", "name": "Wide floor, hard (16x11, 4 robots, 2 requests)",
     "description": "Upstream's rware-1x5-8h-4ag-2req shape: a 16x11 warehouse with 64 shelves and four robots sharing only TWO open requests, so the fleet must decide who works and who keeps the aisles clear.",
     "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}, {"name": "Charlie"}, {"name": "Delta"}],
                     "num_agents": 4, "minPlayers": 4,
                     "shelfColumns": 5, "shelfRows": 1, "columnHeight": 8,
                     "requestQueue": 2, "parDeliveries": 5,
                     "maxTicks": 500, "turnTicks": 20, "sensorRange": 3, "jamTicks": 8,
                     "attempt1Ms": 9000, "retryMs": 4000,
                     "turnBudgetMs": 14000, "turnSpacingMs": 12000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 4` again, inside `certification.game_config`, and exactly
  four players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS
  == 4` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with **both** declared
  players seated:

  ```json
  "certification": {
    "players": [{"player_id": "courteous"}, {"player_id": "shuttle"},
                {"player_id": "courteous"}, {"player_id": "shuttle"}],
    "game_config": {"players": [{"name": "Alpha"}, {"name": "Bravo"}, {"name": "Charlie"}, {"name": "Delta"}],
                    "num_agents": 4, "minPlayers": 4, "seed": 42,
                    "shelfColumns": 3, "shelfRows": 1, "columnHeight": 8,
                    "requestQueue": 4, "parDeliveries": 8,
                    "maxTicks": 500, "turnTicks": 20, "sensorRange": 3, "jamTicks": 8,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  500 ticks of scripted play is ~2 s of sim, but the replay is 500 ticks ⇒ **16.7 s of playback**,
  which the viewer soak needs. The certify step in `coworld-release.yml` passes
  **`--timeout-seconds 300`** (the default 60 covers start + connect grace + play + linger —
  cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/rware-warehouse-player"`:

  ```json
  [{"name":"rware-warehouse-picker","run":"/bin/rware-warehouse-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>"}},
   {"name":"rware-warehouse-router","run":"/bin/rware-warehouse-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"rware-warehouse-shuttle","run":"/bin/rware-warehouse-player",
    "env":{"PLAYER_SCRIPTED":"shuttle"}},
   {"name":"rware-warehouse-courteous","run":"/bin/rware-warehouse-player",
    "env":{"PLAYER_SCRIPTED":"courteous"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `shuttle` and `courteous`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the **game**
  pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs the four shards, and the `docker-smoke` and `wasm-viewer`
  jobs are taken **unchanged** with `<slug>` → `rware-warehouse`, `<IMAGE>` →
  `coworld-rware-warehouse`, `<SEATS>` → **`4`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server) and
  `--soak 10` added to the `viewer_smoke.mjs` invocation. `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable** (mode
  100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_rware_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and as four shard binaries in `ci.yml`'s `test` job.
`tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_rware_sim.nim`)
1. `layout formula` — grid size, highway mask, workstation cells and shelf count for both shipped
   variants, against the formulas (and cross-checked by `test_rware_layout.nim`, below).
2. `empty robots walk under shelves` — an unloaded robot enters a storage cell holding a shelf and
   the shelf is untouched.
3. `loaded veto` — a carrying robot's `FORWARD` into a standing shelf is cancelled to `NOOP` and
   counted in `blockedMoves`; the same move **is** allowed when the target holds a robot that is
   itself carrying; the same move is allowed onto an empty storage cell and onto any aisle cell.
4. `head-on` — two robots facing each other one cell apart both request `FORWARD`: **neither moves**,
   on this tick and on every later tick, until one turns away.
5. `rotation` — three robots in a 3-cycle all move; four in a 4-cycle all move; a robot pointing into
   a cycle from outside does not.
6. `chain` — a queue of three robots behind one with somewhere to go all advance in the same tick;
   the same queue behind a stationary robot does not move at all.
7. `contention tie-break` — two robots requesting the same empty cell from different branches: the
   deterministic longest-path rule commits exactly one, the same one on every run and in both the
   native and the wasm build.
8. `turning` — `LEFT`/`RIGHT` walk the wrap list `[UP, RIGHT, DOWN, LEFT]`; a wall-facing `FORWARD`
   clamps to the robot's own cell and counts as blocked.
9. `load and unload` — `TOGGLE_LOAD` lifts only from the robot's own cell and only when empty;
   unloading is refused on every highway cell (including the delivery row and the queue lane) and
   accepted on an empty storage cell; unloading onto a storage cell that already holds a shelf is
   impossible because the loaded robot could not have entered it.
10. `delivery and refill` — a requested shelf reaching `W1` credits exactly the robot standing there,
    increments `teamDelivered` once, replaces that queue entry with a shelf **not already in the
    queue**, and leaves the shelf on the robot's forks; an unrequested shelf on a workstation credits
    nothing.
11. `jam detector` — two robots deadlocked head-on raise `jam` at exactly `stuck == 8`, name both
    aliases, keep `jamTicksTotal` counting, and raise `jamclear` on the tick one of them turns; a
    single robot stuck against a wall is **not** a jam.
12. `scoring` — `scores[s] == 100*teamDelivered + delivered[s]` for 500 randomised end states, always
    ≥ 0, `delivered[s] < 100` always (the lexicographic bound), all four `win[s]` equal, `winner` null.
13. `end conditions` — tick cap, the wall-clock stop and a forced fault each produce the right
    `endRule` and the right episode `reason`; an all-jammed episode still ends `complete` with
    `teamDelivered == 0`.
14. `no floating point in the sim` — a source grep over
    `src/rware/{sim,warehouse,robots,jam,pilot,baselines}.nim` finds no `float`, `/`, `sqrt` or float
    literal.
15. `tick budget` — 500 ticks of a full four-robot episode complete in < 2 s in a release build.

**Port fidelity** — `tests/test_rware_upstream.nim` (the regex tripwire over
`vendor/upstream/warehouse.py` and `__init__.py`), `tests/test_rware_layout.nim` (cell-for-cell layout
equality for five `(rows, cols)` shapes, the 32/64 shelf counts, one-cell aisles),
`tests/test_rware_requests.nim` (the request stream is a pure function of `(seed, k)` and is identical
under different seat behaviour — the anti-collusion pin), `tests/test_rware_determinism.nim`
(re-simulate from the replay's seed and order records alone on a fresh sim; identical final tick,
deliveries and per-tick `gameHash`).

**Bounded orders / legality on the scripted baselines** (`tests/test_rware_pilot.nim`)
16. `baselines are bounded` — for 200 pseudo-random world states (varying loads, jam states, empty
    request boards, both layouts, every slot) and for **both** `shuttle` and `courteous`: the returned
    order carries a `verb` from the enum, a `shelf` that is **currently on the request board**, a
    `station` in `{W1, W2}`, `stow` coordinates that are a **storage** cell the seat has seen empty,
    empty `say`/`notes`, and a serialised directive ≤ 1024 bytes. A baseline that ever proposes an
    illegal or unbounded order fails the build.
17. `pilot never emits an illegal action` — over the same states, every emitted action is in
    `{NOOP, FORWARD, LEFT, RIGHT, TOGGLE_LOAD}`, `TOGGLE_LOAD` is never emitted while carrying on a
    highway cell, and no order can leave a robot with no action.
18. `fallback is the courteous proc` — the decision engine's fallback path and the `courteous`
    baseline resolve to the same proc, so they cannot drift.
19. `reply validation` — the validator accepts the schema, **repairs** an invalid order to the seat's
    previous order, accepts a `say`-only reply, rejects a non-object, truncates `say`/`notes` on
    **rune** boundaries at 120/240 with 4-byte emoji sitting on the boundary, caps the read at 4096
    bytes, clamps out-of-range `stow` coordinates, and never leaves a robot unactuated.
20. `baseline tuning is the swept pick` — the shipped `yieldAfter`/`penalty`/`stowClearance` equal
    `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep
    with `--check`).

**End-to-end episode writing a replay** (`tests/test_rware_engine.nim`)
21. `episode writes artifacts` — run a real four-seat episode (tiny layout, `maxTicks 200`, all seats
    scripted, no API key so the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set;
    assert `results.json` and the `.replay` are written, `reason == "complete"`,
    `teamDelivered > 0`, `scores` agree with the formula, and the results key set equals the
    manifest's `results_schema` key set **exactly**.
22. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure
    payload.
23. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete`, not `deadline`, and the matching record names the turn.

**Replay** (`tests/test_rware_replay.nim`)
24. `record then re-derive, every end reason` — for `tickCap`, `wallClock` **and** `fault`, record an
    episode and re-derive it from the bytes; assert identical hashes at every tick **including the
    stop tick** (the particle-worlds scar).
25. `replay is self-sufficient` — the bytes alone yield seat names, aliases, policy kinds, the full
    config, the seed, every order record, every chat record and the result.
26. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "rware-warehouse/v1"`.
27. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept.

**Manifest** (`tests/test_rware_manifest.nim`)
28. `manifest pins` — `num_agents == 4` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens`
    in any `game_config`; `len(player) == 2` and every declared player seated in
    `certification.players`; `len(certification.players) ==
    len(certification.game_config.players) == 4`; every array in `config_schema` has
    `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both `game.protocols.player` and
    `.global` present as `{"type","value"}` objects; `game.docs.readme` + `pages`;
    `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 660`; **and every
    variant's `game_config` actually constructs a valid `GameConfig` and generates the layout and
    shelf count this note claims** (the collab-cooking 0.1.1 scar: test every variant, not just the
    fixture).
29. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_rware_viewer.nim`, static assertions in the `test` job)
30. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals the starter's,
    pinned as a literal.
31. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it; `broadcast_core.js`'s kept procs are
    byte-identical to the starter's, `pushFeed`'s signature included.
32. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `warehouseBeat`,
    never `markBeat`.
33. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{delivery, jam, fallback, end}`.
34. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the three 360 px rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#fpv*`,
    `#povBadge`, …) appear nowhere.
35. `endcard labels` — `tests/test_rware_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
36. `label manifest` — the starter's `test_label_contract` pattern: the emitted sprite-label
    vocabulary equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.

**Viewer smoke — the bundle is EXECUTED, not merely built**
37. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded
    as the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm
    module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the
    bridge `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
38. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `say` at all**, so
    the smoke replay can never exercise the feed's radio text path (the cogchemists 2026-08-24 scar).
    The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims
    only the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) —
    driving the real page with a full-cap 120-rune `say` on all four seats, a full request rail and an
    active jam banner, at several canvas widths including 360 px.
39. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **The other upstream layouts.** `small (2,3)`, `medium (2,5)` and `large (3,5)` are 20 and 29 cells
  tall against 10–16 wide; letterboxed into a ~360 × 203 embed they fall to 10 px per cell, where a
  robot's facing and a shelf's request outline stop reading. v1 ships the two 11-tall shapes. Adding
  a taller floor later is a variant plus a legibility pass, not a rules change — `warehouse.nim`
  already generates them and `test_rware_layout.nim` already covers `(2,3)`, `(2,5)` and `(3,5)`.
- **Seat counts other than 4.** The idea's 2–16 range is answered at exactly 4 in every variant and in
  the cert fixture. 2- and 8-seat variants are new manifest entries with a new `num_agents`, not a
  change to these rules.
- **More than one robot per seat.** A seat drives one robot. A fleet-dispatcher seating (one policy,
  four robots, one order per robot per turn) would remove the idea's central "you don't control the
  other robots" property and is not shipped.
- **Per-tick policy control and RL observation tensors.** No seat receives the flattened
  `(1+2·sensor_range)²` upstream observation vector, no `msg_bits` communication channel is exposed
  (the radio replaces it), and no pretrained EPyMARL weights are vendored or run. Orders are the
  interface.
- **Upstream's `TWO_STAGE` and `GLOBAL` reward modes as the score.** Both quantities are recorded;
  the scoring formula is the one in §The game and does not change per variant.
- **`max_inactivity_steps` termination** — deliberately disabled so a jam is watched rather than
  hidden (§The game).
- **Jumanji's `RobotWarehouse`.** The port target is `semitable/robotic-warehouse`; Jumanji's JAX
  reimplementation is a cross-check reference in `vendor/UPSTREAM.md`, not a second set of rules.
- **Live spectating.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, fog-of-war rendering, the
  first-person PIP, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, teams, four-team play, achievements, campaign mode, multi-game episodes,
  the procedural map generator, the map pool, the map editor and mapkit — all deleted, not disabled
  (§Sim module), and none of them return in v1.
- **Human-facing extras**: shelf priorities, deadlines per request, robot battery/charging, variable
  robot speeds, multi-cell shelves and pickers at the workstations. None exist upstream and none are
  invented here.
