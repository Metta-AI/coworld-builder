# cogame-minigrid — design note (2026-08-28)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` importing and re-exporting the sim
modules, `sim_types.nim` owning `GameVersion` and `TargetFps* = 24` (`src/ctf/sim_types.nim:376`) with
its prepend-only changelog-comment discipline, the flatty wire types whose field order is sacred, and
the rune caps `MaxNoteRunes` / `MaxSayRunes` / `MaxPromptRunes`
(`src/ctf/sim_types.nim:747, 794-799`)); the mummy HTTP/websocket server implementing the Coworld
contract, including its `wallClockBudgetSeconds` stop at `src/ctf/server.nim:1407-1417`; the
`decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` / `control.nim` commander layer with its
one-batch-per-turn shape (`src/ctf/decide.nim:427` `engine.client.curl.makeRequests`), its
`attempt1Ms` / `retryMs` / `turnBudgetMs` / `turnSpacingMs` deadlines
(`src/ctf/decide.nim:386-389, 406, 421-427`), its budget guard (`src/ctf/decide.nim:328-346`), its
tolerant JSON extraction (`src/ctf/directives.nim:102`), its rune truncation
(`src/ctf/directives.nim:61-90`) and its fallback ladder with the exact log phrasing
(`src/ctf/decide.nim:463` "failed, falling back if it fails again" for attempt 1, `:491`
"falling back" only on the second failure); the binary `COWLDCTF` replay of *inputs plus a per-tick
`gameHash`* (`src/ctf/replays.nim:142`), re-simulated by **the same sim module** compiled to wasm by
`replay-viewer/config.nims`; the `client/` broadcast chrome (`chrome_common.js` + `broadcast_core.js`
+ `replay_broadcast.html` with its `window.PaintballChrome.install(PB_CTX)` splice hook at
`client/replay_broadcast.html:4330-4337` and the game-block banner at `:4344`); nimby + `Dockerfile` +
`Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the Nim test suite with its four
shards (`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **this is a real-time tick loop whose rules are written into this repo and
whose single seat is an LLM dispatcher over a deterministic per-tick driver — the first row of the
starter table** (`prompts/10-design.md` §Starter table: "any real-time game loop (grid OR continuous
physics), new rules written for this coworld"). It is deliberately **not** the `cogame-moba`
bit-exact-port row, and that is a **rail the coordinator already set and this note does not revisit**:
this coworld does **not** vendor, embed or bit-exactly port Farama MiniGrid, BabyAI or
XLand-MiniGrid. Those are Python/JAX packages with their own RNG streams and their own registry of
hundreds of registered environments; embedding one means a Python simulator that cannot compile to
wasm, which makes the static replay viewer — a non-optional pin — impossible. What this repo
implements is the *problem* those benchmarks pose — partially observed gridworlds with keys, doors,
lava and moving obstacles; a natural-language mission sentence; and hidden per-episode production
rules — on its own deterministic, seeded, integer Nim sim written for this coworld. Every divergence
from the source packages is named in §Sim module → "Documented divergences" and mirrored into
`docs/PORTING-MINIGRID.md`. The precedent for forking paintbot for a grid game is ten deep
(knights-archers, pistonball, atari-cabinet, walker-waterworld, particle-worlds,
smac-starcraft-micro, magent-battle, rware-warehouse, flatland, sumo-traffic-signals).

Where this note departs from coworld-ctf it says so. The departures are: the rules are gridworld
task rules, not paintbot's (§Sim module lists what is deleted); the board is a fixed 13 × 13 integer
**cell grid** authored by seeded generators, so ctf's pixel arena, procedural map generator, map
pool, map editor and mapkit are deleted; there is **one seat, not eight**, and no teams; the seat is
**partially observed** through a 7 × 7 egocentric window, so ctf's fog/vision machinery is replaced
by a much simpler exact-visibility rule; and `MaxSayRunes` / `MaxNoteRunes` are re-pinned
(§Decisions → reply schema).

### Source idea (verbatim)

> SA MiniGrid & XLand-MiniGrid — keys, doors, lava and a sentence telling you what to do
>
> Single-agent coworld over Farama MiniGrid / BabyAI / XLand-MiniGrid. Partially observed grid worlds (7×7 egocentric view): DoorKey, MultiRoom, KeyCorridor, ObstructedMaze, LavaGap, Dynamic-Obstacles; BabyAI adds a natural-language mission ("put the red ball next to the blue box"); XLand-MiniGrid adds hidden production rules (combine objects to make goals) sampled per episode — a meta-RL test. Sparse reward, 3 turn/move actions plus pickup/drop/toggle.
>
> Seats: 1
> Motive: task completion score across a task distribution
> Policy interface: per-tick discrete; the BabyAI mission string makes this the most LLM-friendly single-agent benchmark — LLM-vs-RL is the interesting ladder
> Fills gap: instruction-following gridworld; a natural home for LLM-RL (cogamer-rl) experiments
> Integrity: task seeds held out; per-task success rate over N episodes.
>
> Replay plan (watchability): top-down full view for spectators, agent's 7×7 window inset, mission text on screen.
>
> Source: github.com/Farama-Foundation/Minigrid; BabyAI; github.com/corl-team/xland-minigrid.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time tick loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-minigrid` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=scout\|bumper`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art + install-time bakes) |
| Two name spaces | §The game (in-game alias `Alpha`; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 223 s, worst 644 s, engine stop 660 s, budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 1`, three times |
| Per-turn LLM call budget stated (single seat) | §Decisions (exactly one request per turn, two with the retry; ≤ 110 per episode) |
| Replay bytes self-sufficient | §Server (config JSON, joins, per-turn plans, chats, per-tick hashes, seed, variant) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Task seeds held out (the idea's integrity note) | §Sim module (layouts and rule sets are a pure hash of `(seed, taskIndex, …)`; the seat never sees `seed`, unobserved cells, or a future task) |

---

## The game

One cog, alone, in a 13 × 13 walled gridworld it can only see 7 × 7 of. On the screen is a sentence:
*"use the yellow key to open the door and then get to the green goal square"*, or *"put the red ball
next to the blue box"*, or — in the XLand variant — *"make a purple box"* with **no** explanation of
how purple boxes come to exist. The cog turns, walks, picks things up, opens doors and pushes objects
together; lava kills it; grey obstacle balls kill it if it walks into one. An episode is a **gauntlet
of five tasks**, each on its own seeded layout with its own sentence and its own eleven-turn window.
The only number the league reads is **how many of the five it solved**. The tie-break is how much of
each unsolved task it got through, and after that, how fast it solved the ones it solved.

The whole game is the gap between the sentence and the 7 × 7 window: you are told what to do and
shown almost nothing, and every turn you spend looking is a turn you did not spend doing.

### Seats and aliases

- **`num_agents` = 1.** Exactly one seat, always — in both manifest variants and in the certification
  fixture. This is the idea's own "Seats: 1", and it is what the game is: MiniGrid/BabyAI/XLand are
  single-agent benchmarks and a second seat would have nothing to do. Every episode is a solo
  time-trial; policies are compared across episodes, not within one.
- **Two name spaces.** In-game the seat is **`Alpha`** — `IdentityNames[0]` from the starter's
  `src/ctf/roster.nim:64-65`, title-cased by `seatAlias(slot)`. That alias is the only name that
  appears in an observation, in a prompt, in a `say`, or on the board. The seat's **real
  policy/player name** (`daveey`, `daveey-1`, `Baseline (1)`) lives only in `results.names`, in the
  replay's join record, and spectator-side in the viewer's scorebug plate, agent-view caption and
  endcard. `showPlayerLabels` is **false**, as in the starter's paintball variant, so nothing drawn
  on the board leaks an identity. With one seat there is nobody to meta-game against, but the pin is
  satisfied both ways, not either way: the alias is what the model sees, the real name is what the
  spectator sees.

### The board

Every task in every variant is played on the **same board size**: a **13 × 13** grid of cells,
`gridSize = 13`, indexed `(x, y)` with `x` the column `0 … 12` (west → east) and `y` the row
`0 … 12` (north → south). `(0, 0)` is the north-west corner. **The entire border ring is `wall`**, so
the playable interior is 11 × 11 = 121 cells. One board size for every task family, in every variant,
forever: it is what lets the viewer letterbox a square board at any width (§Viewer → Legible at
360 px) and what makes `goto x y` a stable contract in the reply schema.

**A cell holds at most one thing.** The closed enum of cell contents:

| Content | Glyph | Passable | Sees behind | Notes |
|---|---|---|---|---|
| empty floor | `.` | yes | yes | |
| wall | `#` | no | no | |
| lava | `~` | **yes** | yes | entering it ends the task: `died` |
| goal square | `G` | yes | yes | |
| key | `k` | no | yes | has a colour; pickupable |
| ball | `o` | no | yes | has a colour; pickupable unless it is an obstacle |
| box | `b` | no | yes | has a colour; pickupable; `toggle` opens it into its contents |
| door, open | `D` | yes | yes | has a colour |
| door, closed | `d` | no | **no** | has a colour |
| door, locked | `L` | no | **no** | has a colour; needs a same-coloured key |

Colours are the six MiniGrid colours and nothing else: **`red`, `green`, `blue`, `purple`, `yellow`,
`grey`**.

**The agent** has a position `(x, y)`, a direction `dir ∈ {east, south, west, north}` (indices
0, 1, 2, 3 — the MiniGrid order, so "turn right" is `dir = (dir + 1) mod 4`), and carries **at most
one** object. A carried object is out of the world: it is not on any cell, cannot be seen by
production rules, and is drawn on the scorebug's inventory chip.

### The seven task families

Each is a generator `generate(seed, taskIndex) -> Task` plus a success predicate plus three named
subgoal credits. Every draw inside a generator is a read of the pure hash `mix64(seed, taskIndex, k)`
for an increasing salt `k` — never a consumed stream (§Sim module → determinism).

1. **`lavagap`** — mission: **"get to the green goal square"**. A vertical column of `lava` at
   `gapX ∈ 4 … 8`, filling the whole interior height except a single gap cell at `gapY ∈ 1 … 11`.
   Agent starts at `(1, 1)` facing east. `goal` at `(11, 11)`. Success: the agent stands on the goal.
   Subgoals: (a) the gap cell has entered the view; (b) `agent.x > gapX`; (c) success.
2. **`doorkey`** — mission: **"use the yellow key to open the door and then get to the green goal
   square"**. A full-height interior wall at `wallX ∈ 5 … 7` with one **locked yellow door** at
   `doorY ∈ 1 … 11`. A **yellow key** on a seeded free cell west of the wall. Agent starts on a
   seeded free cell west of the wall facing east; `goal` at a seeded free cell east of it. Success:
   on the goal. Subgoals: (a) carried the key; (b) the door became `open`; (c) success.
3. **`multiroom`** — mission: **"get to the green goal square"**. Interior walls at `x = 6` and
   `y = 6` cut four rooms (NW = 0, NE = 1, SE = 2, SW = 3). Three **closed, unlocked** doors pierce
   the walls, on the 0→1, 1→2 and 2→3 boundaries only; the 0↔3 boundary is solid wall. Door colours
   are `blue`, `green`, `purple` in that order; door positions are seeded within their wall segment.
   Agent starts in room 0, `goal` in room 3 — so the only route is 0 → 1 → 2 → 3 and the agent
   cannot see past a closed door. Success: on the goal. Subgoals: (a) entered room 1; (b) entered
   room 2; (c) success.
4. **`keycorridor`** — mission: **"pick up the blue ball"**. A vertical corridor at `x = 6`. Three
   side rooms east of it occupying rows `1-3`, `5-7`, `9-11`, each entered through one door on the
   corridor wall. One room, `lockedRoom ∈ 0 … 2`, has a **locked red door**; the other two have
   closed unlocked doors (`grey`). A **red key** lies in one of the two unlocked rooms; a **blue
   ball** lies in the locked one. Agent starts at `(2, 6)` facing east. Success: the agent is
   carrying the blue ball. Subgoals: (a) carried the red key; (b) the red door became `open`;
   (c) success.
5. **`dynamic`** — mission: **"get to the green goal square without touching a grey ball"**. An empty
   interior, `goal` at `(11, 11)`, agent at `(1, 1)` facing east, and `obstacleCount = 6` **grey
   balls** that move. Obstacles are not pickupable. Success: on the goal. Failure: a `forward` into a
   cell holding an obstacle — `crashed`. Subgoals: (a) the Manhattan distance to the goal has been
   ≤ 12; (b) ≤ 6; (c) success.
6. **`babyai`** — the natural-language family. An empty interior with **six** objects on seeded free
   cells, each a `(type, colour)` pair drawn without repetition from `{key, ball, box} × 6 colours`,
   so every referent is unique. Agent starts at a seeded free cell. The mission is drawn from a
   three-rule grammar (`instructionKind = mix64(seed, taskIndex, 40) mod 3`):
   - **0 — "go to the `<colour>` `<type>`"**; success: the agent is 4-adjacent to that object **and
     facing it**.
   - **1 — "pick up the `<colour>` `<type>`"**; success: the agent is carrying it.
   - **2 — "put the `<colour1>` `<type1>` next to the `<colour2>` `<type2>`"**; success: the two
     objects sit on 4-adjacent cells and **neither is carried**.

   Subgoals — kind 0: (a) the target has been in view; (b) the Manhattan distance to it has been ≤ 3;
   (c) success. Kind 1: (a) target in view; (b) adjacent and facing; (c) success. Kind 2: (a) carried
   object 1; (b) object 1 has rested within Manhattan distance 3 of object 2; (c) success.
7. **`xland`** — the hidden-production-rule family, mission: **"make a `<colour>` `<type>`"**. An
   empty interior with **six** objects placed as in `babyai`, plus a hidden table of exactly
   **three** production rules, sampled per task:
   - Rule 0: `(A) + (B) -> P0`, Rule 1: `(C) + (D) -> P1`, Rule 2: `(P0) + (P1) -> GOAL`, where
     `A, B, C, D` are four distinct objects present on the board and `P0`, `P1`, `GOAL` are three
     `(type, colour)` pairs **not** present at the start and distinct from each other.
   - A rule fires when its two inputs occupy 4-adjacent cells (§Resolution order, tick step 5).
     Both inputs vanish; the product appears in the input cell with the lower `(y, x)`.
   - Success: the `GOAL` object exists — on a cell or carried.
   - Subgoals: (a) any rule has fired; (b) both `P0` and `P1` have existed; (c) success.
   - **The rule table is never shown to the seat.** The only way to learn it is to push things
     together and read the `productions` list in the next observation. That is the idea's meta-RL
     test, and it is the one place in this game where the right play on turn 1 is a deliberate
     experiment.

### The gauntlet, and the clock

- **Tick** = one primitive action by the agent. **`turnTicks = 12`**: every command turn executes at
  most twelve primitives.
- **`taskTurnCap = 11`** turns per task ⇒ at most **132 ticks per task**.
- **`taskCount = 5`** tasks per episode ⇒ **`maxTurns = 55`**, **`maxTicks = 660`**.
- One game per episode (`maxGames = 1`): a gauntlet has no side to swap.
- Tasks run **strictly in the variant's declared order**, one at a time. The seat is told the family
  and the mission of the **current** task only; the ladder for the variant is public in
  `docs/RULES.md` but the *layouts* are seeded and never disclosed.
- A task that finishes (solved, died, crashed) **ends its turn immediately**: the remaining ticks of
  that turn are skipped and the next task begins on the next turn. Turns saved this way are **not**
  transferable to a later task — they simply shorten the episode, which is why a fast solver has a
  shorter wall clock as well as a higher `speedTotal`.
- Between turns the tick loop runs **uncapped** (`fastMode: true`); 660 ticks of integer grid work is
  well under a second of CPU. The wall clock of an episode is the ≤ 55 LLM turns (§Decisions).

**Variants and their ladders** (both are `num_agents: 1`):

| Variant | Ladder (in order) | `parTasks` |
|---|---|---|
| `gauntlet` | `lavagap`, `doorkey`, `multiroom`, `keycorridor`, `babyai` | 3 |
| `xland` | `dynamic`, `xland`, `xland`, `xland`, `babyai` | 2 |

`gauntlet` is the classic MiniGrid/BabyAI ladder in ascending difficulty and ends on the
instruction-following task the idea calls "the most LLM-friendly single-agent benchmark". `xland`
opens with `dynamic` as a moving-hazard warm-up, then puts **three independently sampled rule sets**
back to back — XLand-MiniGrid is a distribution over rule sets, and one sample is an anecdote — and
ends on the same `babyai` family so the two variants share a comparable final task.

### Turn and tick structure — the exact resolution order

Per **command turn** `T`, in this order:

1. If the current task has finished, record its result and start the next task (generate its layout
   from `mix64(seed, taskIndex, …)`, place the agent, emit `taskstart`). If there is no next task,
   end the episode (§End conditions).
2. Recompute the 7 × 7 visible set and merge it into the known map, then build the seat's observation
   object (§Decisions → observation).
3. Issue the seat's LLM request. There is exactly **one** seat, so this is a batch of one through the
   starter's unchanged `engine.client.curl.makeRequests` path (`src/ctf/decide.nim:427`) — the code
   is the starter's batching code, carrying one request. Attempt-1 deadline `attempt1Ms = 6000`. A
   scripted seat computes locally, instantly, and consumes no request.
4. If the seat timed out, errored, returned non-JSON, or returned no usable `actions` array, it is
   retried **once**, `retryMs = 3000`.
5. Still no usable reply → the **`scout`** scripted plan is computed server-side (the same proc the
   `scout` baseline uses — imported, never duplicated) and a `fallback` record is written.
6. **Validate and expand the plan**, in the order the reply lists it:
   a. Entries past `maxActionsPerTurn = 12` are dropped and counted in `actionsDropped`.
   b. Each entry is validated against the reply schema; an entry that does not validate is
      **dropped** (never turned into a different action), counted in `repliesRepaired`, and reported
      next turn.
   c. Macros are expanded against the **known map as of turn start**: `face` into 0, 1 or 2 turn
      primitives, `goto` into the BFS path (§Decisions → the driver), each macro yielding at most
      `macroPrimitiveCap = 40` primitives. A `goto` whose target is not reachable through known
      passable cells yields **zero** primitives, counts in `macrosUnreachable`, and is reported next
      turn as `unreachable`.
   d. The whole expanded queue is truncated to `turnTicks = 12` primitives; the surplus is discarded
      and `planTruncated` is reported next turn. Nothing carries over to the next turn.
7. `say` (≤ 140 runes) and `notes` (≤ 300 runes) are sanitised on rune boundaries and, with the
   accepted plan, written as the turn's `directive` replay record. `notes` is echoed back to the seat
   next turn and to nobody else; `say` is drawn in the spectator feed.
8. `turnSpacingMs = 2600` is a floor on the wall clock between consecutive request **starts** (the
   starter's mechanism at `src/ctf/decide.nim:386-389`, kept), which pins the steady state at
   23 req/min against the sidecar's 30/min per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the game
and nothing else mutates the world**:

1. `tick += 1`; `taskTick += 1`.
2. Pop the next primitive from the queue. If the queue is empty the primitive is **`wait`** (a real
   cost: the tick is spent).
3. **Apply the primitive**, exactly:
   - `left` — `dir = (dir + 3) mod 4`.
   - `right` — `dir = (dir + 1) mod 4`.
   - `forward` — let `C` be the cell ahead. If `C` holds an **obstacle** ball, the task ends
     `crashed` (emit `crash`) and no move happens. Else if `C` is passable (empty, goal, open door,
     lava) the agent moves into it. Else nothing happens.
   - `pickup` — if the agent carries nothing and the cell ahead holds a `key`, `ball` or `box` that
     is **not** an obstacle, the object is carried and the cell becomes empty (emit `pickup`).
     Otherwise nothing happens.
   - `drop` — if the agent carries an object and the cell ahead is **empty floor**, the object is
     placed there (emit `drop`). Otherwise nothing happens.
   - `toggle` — on the cell ahead: a `closed` door becomes `open` (emit `open`); an `open` door
     becomes `closed` (emit `close`); a `locked` door becomes `open` **iff** the agent carries a key
     of the same colour (emit `unlock`; **the key is not consumed**); a `box` is replaced by its
     contents, or by empty floor if it had none. Anything else: nothing happens.
   - `wait` — nothing happens.
4. **Obstacles move** (`dynamic` tasks only), for each obstacle in ascending index: direction
   `d = mix64(seed, taskIndex, 900 + obstacleIndex, tick) mod 4` in the order east, south, west,
   north; the obstacle moves one cell in `d` **iff** the target cell is empty floor and is not the
   agent's cell. An obstacle never moves into the agent — a cog is only ever killed by a `forward`
   it chose.
5. **Production rules fire** (`xland` tasks only). Scan cells in ascending `(y, x)`; for each cell
   holding an uncarried object, check its 4 neighbours in the fixed order east, south, west, north;
   for the first (cell, neighbour) pair matching any rule — rules checked in ascending rule index —
   fire it: both inputs are removed, the product is placed in the pair's lower-`(y, x)` cell, `produce`
   is emitted, `productionsFired += 1`. **At most one production per tick.** A carried object never
   participates.
6. **Task termination**, in this order: (a) the agent stands on `lava` → `died`, emit `lava`;
   (b) the task's success predicate holds → `solved`, emit `solved`; (c) `taskTick == taskTurnCap ×
   turnTicks` → `timeout`, emit `failed`.
7. **Visibility and subgoals.** Recompute the 7 × 7 visible set from the agent's new pose and merge
   it into the known map, stamping each newly or re-observed cell with `tick`. Then evaluate the
   task's three subgoal predicates; a predicate that first becomes true awards its credit
   permanently and emits `subgoal`. A solved task is awarded all three credits.
8. Mix the tick into `gameHash` and append it to the replay's hash chain.
9. If the task finished at step 6, **break out of the tick loop** — the turn ends early.

### Visibility — the exact 7 × 7 rule

`viewSize = 7`. The view box is the 7 × 7 square of world cells with the agent at view coordinate
`(3, 6)` looking toward decreasing `j`, where `(i, j)` are view coordinates, `i = 0 … 6` left to
right in the agent's frame and `j = 0 … 6` far to near. World cells outside the grid map to `#`.

A cell is **visible** iff the following flood, run once per tick, marks it — the restated MiniGrid
occlusion rule, and the only visibility rule in this game:

```
vis[i][j] = false for all i, j
vis[3][6] = true
for j from 6 down to 0:
  for i from 0 to 5:                       # sweep right
    if vis[i][j] and seesBehind(i, j):
      vis[i+1][j] = true
      if j > 0: vis[i+1][j-1] = true; vis[i][j-1] = true
  for i from 6 down to 1:                  # sweep left
    if vis[i][j] and seesBehind(i, j):
      vis[i-1][j] = true
      if j > 0: vis[i-1][j-1] = true; vis[i][j-1] = true
```

`seesBehind(i, j)` is false for `wall`, `closed door` and `locked door`, and true for everything
else (the "Sees behind" column of the cell table). Both sweeps run in the order given; the rule is
integer-only and has no ties to break.

The **known map** is a 13 × 13 array of the last-observed content of every cell plus the tick it was
last observed. A cell never in `vis` stays `?`. A cell observed and later left behind keeps its last
observed content — which means a remembered obstacle position **goes stale**, and the seat is told
how stale (`seen_tick`). That staleness is real information and the game does not hide it.

### Scoring formula and sign

At the end of the episode, over the five tasks `i = 0 … 4`:

```
solved[i]     = 1 if taskOutcome[i] == "solved" else 0
progress[i]   = subgoal credits earned on task i                    (0 .. 3; 3 if solved)
speed[i]      = (taskTurnCap - taskTurns[i]) if solved[i] else 0    (0 .. 10)

tasksSolved   = sum solved[i]                                       (0 ..  5)
progressTotal = sum progress[i]                                     (0 .. 15)
speedTotal    = sum speed[i]                                        (0 .. 50)

scores[0]     = 100_000 * tasksSolved
              +   1_000 * progressTotal
              +      10 * speedTotal
```

**Sign: higher is better, and every term only ever adds** — `scores[0]` is never negative, and the
minimum (0) is the honest score of a cog that solved nothing and reached no subgoal. There is no
death penalty term: dying fails the task, which already costs 100 000, and a second penalty would
make a cautious cog that never crosses the lava outrank a bold one that solved four tasks and died on
the fifth. `deaths` and `crashes` are recorded in `results` and shown, never scored.

**The ordering is strictly lexicographic, by construction:**

- one more task solved is worth `100_000`, and the largest possible total of the other two terms is
  `1_000 × 15 + 10 × 50 = 15_500 < 100_000` — **tasks solved first, always**;
- one more subgoal credit is worth `1_000`, and the largest possible speed total is
  `10 × 50 = 500 < 1_000` — **partial progress second**;
- speed is the last tie-break, worth 10 a turn saved.

Maximum attainable score: `100_000 × 5 + 1_000 × 15 + 10 × 50 = 515_500` — a perfect five-for-five in
one turn each. `tests/test_minigrid_scoring.nim` asserts the formula, the two dominance bounds and
the maximum, analytically and over 500 randomised end states.

**The league ranks by `results.scores[0]`.** With one seat, every episode is a solo run and the
platform's Elo (1000 start / K 32) is computed from these per-episode per-seat numbers; a policy
climbs by solving more tasks across more seeds, which is exactly the idea's "task completion score
across a task distribution". `results.win[0]` is `tasksSolved >= parTasks` — a "did the cog clear the
bar" flag, not a duel — and **`results.winner` is `0` when `win[0]` is true and `null` otherwise**
(there is no opponent to beat, so the only honest winner is the seat itself or nobody).

**Measured but never scored:** `deaths`, `crashes`, `taskCellsSeen`, `doorsOpened`,
`objectsPickedUp`, `productionsFired`, `primitivesExecuted`, `actionsDropped`, `macrosUnreachable`,
`repliesRepaired`. All are in `results`, on the endcard and in the feed. `taskCellsSeen` is a *means*, not a
currency: paying for exploration directly would let a policy farm the metric by spinning in an empty
room. §Out of scope records the decision.

**Integrity (the idea's note), decided.** "Task seeds held out" is implemented as: the episode `seed`
is randomised by the runner and **never appears in any observation or prompt**; the seat sees no
unobserved cell, no future task, no `xland` rule table, and no layout parameter (`gapX`, `wallX`,
`doorY`, `lockedRoom`, object placements). What *is* public — in `docs/RULES.md` and in the variant
description — is the **ladder of families**, because a benchmark whose task distribution is secret
cannot be reported on. "Per-task success rate over N episodes" is implemented as
`results.taskFamilies` + `results.taskSolved` + `results.taskOutcome`, three parallel five-element
arrays that let the platform aggregate a per-family success rate across a division's episodes without
parsing a replay.

### End conditions and legal `results.reason` values

The episode ends at the first of: **the gauntlet finishing**, the **turn cap**, or the **wall-clock
stop**.

- **Gauntlet complete** — all five tasks have resolved (`solved`, `timeout`, `died` or `crashed`).
  Settles immediately.
- **Turn cap** — `turnsPlayed == maxTurns` (55). Reachable only if every task ran its full
  eleven-turn window, in which case it coincides with the gauntlet finishing; it is kept as an
  independent guard so no arithmetic error can produce an unbounded loop.
- **Wall-clock stop** — the engine's `wallClockBudgetSeconds` guard, the starter's check at
  `src/ctf/server.nim:1407-1417`, kept.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the episode finished on its own terms: the gauntlet ran out of tasks, or the turn
  cap fired. The healthy value. `results.endRule` says which: `gauntletComplete` | `turnCap`.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (default **660 s**). The engine
  stops at the current tick, settles with the **real** tasks solved so far (never zeroed, so a
  deadline episode is still rankable), marks every unstarted task `taskOutcome = "unreached"` with
  `taskProgress = 0`, `taskTurns = 0`, `taskTicks = 0`, writes `results.json` and the replay, and
  exits 0. `results.endRule = "wallClock"`. **Declared acceptable** for `docs/SPEC.md` §Definition of
  done check 4. The budget guard below exists so it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop. Caught; the episode is settled from
  the last completed tick, `results.endRule = "fault"`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0. A defect:
  `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum:
`gauntletComplete | turnCap | wallClock | fault`.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × turnBudgetMs > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn (the seat falls to `scout`, microseconds per turn), the remaining tasks still play out at full
speed, and the episode still ends `complete`. A `budget_guard` record names the turn it fired
(`src/ctf/decide.nim:328-346`, kept).

**A silent seat does not end the episode.** A seat that never connects, disconnects mid-episode, or
fails every decision is driven by `scout` and the gauntlet runs to its natural end with
`deadSeats[0] = true`. Nothing a player container does can stop the clock: the starter's
`lobbyJoinTimeoutTicks` bounds the lobby, and a silent seat cannot consume more than the per-turn
deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes the seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {scout, bumper}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=scout` (the starter's "anything unrecognised is the published default" rule at
`src/ctf/baselines.nim:52-58`). **A scripted policy seated as a champion is a failure state.**

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/minigrid/anthropic_api_key` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/minigrid_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"scout"|"bumper"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then
acknowledge frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3
close-frame race: whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/minigrid/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION` / `AWS_DEFAULT_REGION`, default `us-west-2`) →
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
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject`
  (`src/ctf/directives.nim:102` — outermost balanced `{…}`, fence-tolerant, tolerant of trailing
  prose) and `truncateRunes` / `sanitizeSay` / `sanitizeNote` (`src/ctf/directives.nim:61-90`)
  unchanged.

### Cadence, the per-turn call budget, and the wall-clock arithmetic

One command turn every ≤ 12 ticks; **at most 55 turns per episode**. **The per-turn LLM call budget
is exactly ONE request, plus at most ONE retry** — there is a single seat, so the starter's
one-parallel-batch-per-turn machinery (`src/ctf/decide.nim:427`) carries a batch of one and is
otherwise untouched. **At most `55 × 2 = 110` provider calls per episode**, and never more than one
in flight.

```
attempt1Ms                          6.0 s   (whole seconds — sim_config.nim:696-706 rejects otherwise)
retryMs                             3.0 s   (whole seconds; attempt1Ms + retryMs <= turnBudgetMs — :691)
turnBudgetMs                        9.5 s   (monotonic deadline around the whole turn)
turnSpacingMs                       2.6 s   -> 1 seat x 60/2.6 = 23 req/min  (sidecar cap: 30)

55 turns x max(spacing 2.6 s, latency ~3.3 s)  typical            = 187 s
55 turns x turnBudgetMs 9.5 s, absolute worst                     = 523 s
660 ticks, <=6 obstacles + <=6 objects, integer Nim, fastMode     =   1 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at       =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)    =  20 s
                                                                  -------
typical total                                                     = 223 s   < 720 s
absolute worst case (523 + 1 + 100 + 20)                          = 644 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                           = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_minigrid_manifest.nim` asserts it. The typical
figure is conservative: a policy that solves tasks early uses fewer than 55 turns, and a
five-for-five run is nearer 120 s.

**Rate guard.** `turnSpacingMs` pins the steady state at 23 req/min, but a run of retrying turns
issues two requests each. The engine therefore keeps a **rolling 60 s request counter**: if issuing
the next request would push the trailing-60 s count above **28**, that turn skips the call and takes
the `scout` plan with `cause = "rate_guard"`. Bounded, logged, never a sleep on the episode's
critical path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant: the seat sends no per-tick
inputs (the server computes every primitive), so the Sprite v1 Ready packet's dead-reckoning hazard
cannot arise.

### Degrade, never hang

Every wait is bounded: the two request deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 9.5 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop,
and ctf's `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On the seat's timeout or parse failure: **retry once**; on the second failure that turn's plan
becomes the **`scout`** scripted plan computed inside the game (the same proc the `scout` baseline
uses — imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns` counts them. The attempt-1 notice says **`will retry`**; only
a genuine second failure logs **`falling back`** (the pommerman 0.1.1 phase-60 grep scar; the
starter's two phrasings live at `src/ctf/decide.nim:463` and `:491`).

**No failure mode leaves the agent without an action.** The tick loop always has a primitive: the
turn's queue, else `wait`, which is a legal state that costs a tick and nothing else. A seat that
never connects is reported once to `COGAME_PLAYER_FAILURE_URI` with the platform's **closed**
payload — exactly `{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: a task ends the moment it is solved or lost,
the gauntlet ends the moment its fifth task resolves, and the budget guard drops the seat to scripted
play the moment two more full turns would not fit.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **the cog knows what it has seen and nothing else.**

**Visible.**

- **The rules of the world, once, at registration** — `gridSize` 13, `viewSize` 7, the cell glyph
  legend, the colour list, the seven primitives and what each does, `turnTicks`, `taskTurnCap`,
  `taskCount`, `maxActionsPerTurn`, and the fact that lava and obstacle balls are fatal. Static;
  afterwards referred to by id.
- **The current task's mission sentence**, its index (`1 … 5`), its family name, and its remaining
  turns. **Not** future tasks' missions or families.
- **The 7 × 7 egocentric window**, `view`, as seven strings of seven glyphs, **agent-up**: row `j = 0`
  is the far row, row `j = 6` is the agent's own row, column `i = 0` is to the agent's left. The
  agent's own cell reads `A`. A cell in the box that the visibility flood did not mark reads `?`.
  This is exactly what a MiniGrid agent sees, and exactly what the viewer's inset draws.
- **The known map**, `known`, as thirteen strings of thirteen glyphs in **world orientation** — the
  last-observed content of every cell ever visible, `?` everywhere else. This is a **documented
  divergence** (§Sim module): MiniGrid gives the policy no memory, but an LLM re-prompted fresh each
  turn has no hidden state at all, so the game keeps the memory instead of forcing the model to
  re-derive it inside a 300-rune note. Partial observability is untouched — `?` cells stay `?` until
  the agent goes and looks.
- **Every observed object**, `objects`: `{type, color, x, y, state, seen_tick}` for every key, ball,
  box and door ever in view, with `state ∈ {open, closed, locked, ""}` and `seen_tick` saying how
  stale the sighting is. Obstacles appear here as grey balls with `moves: true`.
- **The agent's own state** — `x`, `y`, `dir` (`east|south|west|north`), `carrying` (an object or
  `null`), and `ahead`: the glyph and object in the cell it is facing.
- **Its own last turn** — `last_plan` (the primitives actually executed), `plan_truncated`,
  `dropped`, `unreachable`, and `notes` echoed back.
- **Its own production history** (`xland` only) — `productions`: every rule firing it has caused,
  `{a, b, out, x, y, tick}`. This is how the hidden table is learned and it is the only channel.
- **Its own progress** — `subgoals` (the three named credits and which are earned), `tasks_solved` so
  far, `ticks_left` in this task, `turns_left` in this task.

**Hidden.** The episode **seed**; every cell never observed; every layout parameter (`gapX`, `wallX`,
`doorY`, `lockedRoom`, object placements, obstacle spawn cells); the **contents of an unopened box**;
the **`xland` production rule table** and any rule the agent has not itself fired; **future obstacle
motion**; the missions, families and layouts of tasks not yet started; the agent's own **score**; and
its own real player/policy name. Nothing about identity ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `notes`) into
the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "Alpha",
  "task": {"index": 2, "of": 5, "family": "doorkey",
           "mission": "use the yellow key to open the door and then get to the green goal square",
           "turns_left": 8, "ticks_left": 105},
  "turn": 14, "tick": 159,
  "world": {"size": 13, "view": 7,
            "legend": {".": "floor", "#": "wall", "~": "lava (fatal)", "G": "goal",
                       "k": "key", "o": "ball", "b": "box",
                       "D": "open door", "d": "closed door", "L": "locked door",
                       "A": "you", "?": "not seen yet"}},
  "agent": {"x": 4, "y": 4, "dir": "east", "carrying": {"type": "key", "color": "yellow"},
            "ahead": {"glyph": ".", "object": null}},
  "view": ["???????",
           "???????",
           "???????",
           "???????",
           "##L####",
           ".......",
           "...A..."],
  "known": ["#############",
            "#?....#?????#",
            "#.....#?????#",
            "#.....L?????#",
            "#...A.#?????#",
            "#.....#?????#",
            "#.....#?????#",
            "#.....#?????#",
            "#.....#?????#",
            "#.....#?????#",
            "#..??.#?????#",
            "#??...#?????#",
            "#############"],
  "objects": [
    {"type": "door", "color": "yellow", "x": 6, "y": 3, "state": "locked", "seen_tick": 152}
  ],
  "productions": [],
  "last_plan": {"executed": ["right", "forward", "forward", "forward", "left",
                             "forward", "forward", "forward", "forward", "forward",
                             "forward", "forward"],
                "truncated": true, "dropped": 0, "unreachable": 0},
  "subgoals": [{"name": "has_key", "earned": true},
               {"name": "door_open", "earned": false},
               {"name": "on_goal", "earned": false}],
  "tasks_solved": 0,
  "notes": "yellow key was at (2,9), got it. locked door at (6,3). goal must be east of the wall."
}
```

Reading it: the cog stands at `(4, 4)` facing east, holding the yellow key. Its `view` is agent-up,
so `j = 6` (the bottom row) is its own column `x = 4`, `j = 5` is `x = 5`, and `j = 4` is the wall
column `x = 6` — where the locked door `L` sits two cells to its left, i.e. at `(6, 3)`. Rows
`j = 3 … 0` are all `?` because a locked door does not see behind, which is the whole reason the cog
has never seen the goal. `known` shows the same wall column running the height of the board with the
`L` in it, everything east of it unexplored, and the cell the key came from now plain floor —
**carried objects are not on cells and never appear in `objects`**.

Field rules. `view` is always **7 strings of 7 characters**; `known` is always **13 strings of 13
characters**; the array shapes never change. Glyphs are exactly the closed set in the legend.
`agent.dir` is one of `east|south|west|north`. `objects` is sorted ascending by `(y, x)` and lists
only uncarried objects. `last_plan.executed` lists the **primitives** that actually ran — macros are
already expanded — so the seat can see a `goto` get cut off rather than guess.

### Reply schema and per-field caps

```json
{"actions": [{"do": "goto", "x": 6, "y": 3},
             {"do": "toggle"},
             {"do": "forward"}],
 "say": "I have the yellow key; opening the door at (6,3) and heading east for the goal",
 "notes": "goal not seen yet. after the door, sweep east wall first."}
```

| Field | Type | Cap / domain |
|---|---|---|
| `actions` | array | **≤ 12 entries** (`maxActionsPerTurn`). Entries past the cap are dropped and counted in `actionsDropped`. Absent or empty = the turn is twelve `wait` ticks, and the reply is still **usable** |
| `actions[].do` | string | **≤ 8 runes**; enum `left` \| `right` \| `forward` \| `pickup` \| `drop` \| `toggle` \| `wait` \| `goto` \| `face`, lower-cased before matching |
| `actions[].x`, `.y` | integer | required iff `do == "goto"`; **clamped to 0 … 12**; a non-integer or absent value **drops the entry** and counts in `repliesRepaired` |
| `actions[].dir` | string | required iff `do == "face"`; **≤ 5 runes**; matched case-insensitively against `N`, `E`, `S`, `W`, `north`, `east`, `south`, `west`; anything else drops the entry |
| `say` | string | **≤ 140 runes** (`MaxSayRunes`) — the cog thinking out loud; drawn in the spectator feed and in the replay, never fed back to the seat |
| `notes` | string | **≤ 300 runes** (`MaxNoteRunes`) — private scratchpad, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160`
(`src/ctf/sim_types.nim:747, 794-795`), which are a 10-character in-world shout and a short note. A
cog narrating a gridworld needs a sentence, and a cog carrying its own map between turns needs more
than 160 runes, so `MaxSayRunes = 140` and `MaxNoteRunes = 300` here, and `ShoutMaxChars` is deleted
with the shout mechanic (§Sim module → Deleted).

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded
error text — is truncated on RUNE boundaries** via the starter's `truncateRunes` / `runeSubStr`
(`src/ctf/directives.nim:61-68`), never by byte index. Byte truncation is what makes a replay that
renders in a browser fail a strict UTF-8 parser; `tests/test_minigrid_replay.nim` asserts it with
4-byte emoji sitting exactly on every cap.

Unknown top-level and per-action keys are ignored. A reply with a valid `say` but no `actions` is
**usable** (the turn is spent waiting and the narration is delivered). A reply that is not a JSON
object is a parse failure. **Invalid actions are dropped, never rewritten**: unlike a
multi-intersection order set, a mis-specified movement has no meaningful repair — turning an invalid
`goto` into a `forward` would walk the cog into lava on the game's own initiative — so the entry is
removed, counted, and reported back as `dropped` next turn.

### System prompt (fixed, identical for both champions)

```
You are one cog alone in a 13x13 walled gridworld. You can only see a 7x7 window
around yourself. A sentence tells you what to do. You will be given five tasks in
a row; each has its own world and its own sentence and its own eleven turns.

WHAT YOU GET EACH TURN
- "view": seven rows of seven characters, YOUR OWN VIEW, rotated so you always
  face UP. The bottom middle character is A, that is you. Row 0 is farthest ahead.
- "known": the whole 13x13 board as you remember it. ? means you have never seen
  that cell. Closed and locked doors and walls block sight, so ? stays ? until you
  walk somewhere you can see it from.
- "objects": everything you have ever seen, with world x,y and how many ticks ago.
- "agent": your x, y, which way you face, and what you are carrying (at most one).

GLYPHS
  .  floor      #  wall        ~  LAVA - stepping on it ends the task
  G  goal       k  key         o  ball        b  box
  D  open door  d  closed door L  locked door (needs a key of the SAME COLOUR)
  A  you        ?  never seen

WHAT YOU SEND
One JSON object with up to 12 actions. They run one per tick, in order, and then
you are asked again. Anything past 12 ticks of movement is CUT OFF - re-issue it
next turn.
  {"do":"forward"}  step into the cell ahead (walls and closed doors stop you)
  {"do":"left"} {"do":"right"}   turn 90 degrees
  {"do":"pickup"}   take the object in the cell AHEAD (you must be empty-handed)
  {"do":"drop"}     put what you carry into the cell AHEAD (it must be floor)
  {"do":"toggle"}   open/close the door AHEAD; a LOCKED door opens only if you are
                    carrying a key of the same colour; a box opens into its contents
  {"do":"wait"}     waste a tick
  {"do":"face","dir":"E"}      turn to face east/south/west/north
  {"do":"goto","x":6,"y":3}    WALK THERE. This is your main action. It finds the
                    shortest path through cells you have ALREADY SEEN and stops
                    facing the target if the target is a door or an object, or
                    standing on it if it is floor or the goal. It refuses to path
                    through ? cells or lava. If it says "unreachable", you have not
                    seen a route yet - go and look.

RULES THAT KILL YOU
Stepping on ~ ends the task immediately. Walking into a grey ball that moves ends
the task immediately. Nothing else can kill you.

HOW YOU ARE SCORED
Only how many of the five tasks you SOLVE. Partial progress on a task you fail is
the tie-break, and solving fast is the tie-break after that. A task you never even
started scores nothing, so never stall.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the
character { and end with }. No prose, no markdown, no code fences.
{"actions":[{"do":"goto","x":6,"y":3},{"do":"toggle"}],"say":"<=140 chars","notes":"<=300 chars"}
```

### Champion #1 — `minigrid-cartographer` (owner **daveey**), `PLAYER_PROMPT`

```
Map first, then act, and never lose what you learned.
Turn 1 of every task: read the sentence and write down in "notes" exactly what
would count as solving it - the object, the colour, the cell, the door. Then spend
the turn walking to the middle of the largest ? region with one "goto" to the
nearest floor cell that touches ?, because a cell that touches ? is where new
information is.
Every turn after that, in this order:
1. If "objects" already contains everything the sentence names AND you can reach
   it, stop exploring and go finish: "goto" it, then "pickup" or "toggle" or step
   onto it. Finishing beats looking.
2. If the sentence names a locked door and you are not carrying its key, find the
   key first. A locked door is never worth a turn without the key in hand.
3. Otherwise explore: "goto" the known floor cell adjacent to the most ? cells,
   then add one or two "forward" so you actually cross into the unknown, then a
   "right" so the next view is a different heading.
Rewrite "notes" EVERY turn as a compact list: the goal, the key colour and where
it is, the door cells and their state, and which side of the board is still ?.
Notes are the only thing you keep; anything you leave out you have lost.
Never plan a path through ~ and never step forward onto a cell whose glyph you
cannot see - if "ahead" is ? or ~, turn instead.
If "last_plan" says truncated, re-issue the SAME goto: you were partway there.
If it says unreachable, the route is not discovered yet - explore toward the
target's side of the board instead.
```

### Champion #2 — `minigrid-missionfirst` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
The sentence is the whole plan. Parse it, then drive at it.
Split the mission into a verb and one or two referents, and say the parse out loud
on turn 1 - "pick up blue ball; not seen yet; sweeping east". Keep that sentence in
"say" every turn, updated, because it is how you check you are still solving the
right problem.
Then, every turn:
- "go to X"     : goto X, then "face" it. Done.
- "pick up X"   : goto X, then {"do":"pickup"}. If you already carry something
                  else, drop it first on a floor cell you can see.
- "put X next to Y": carry X, goto a floor cell 4-adjacent to Y, face away from Y,
                  and drop. If the cell next to Y is occupied, use the next one
                  round - never drop into the cell Y itself.
- "open the D door": if D is locked, carry its key first, goto the door, toggle.
- "make a Z"    : you are being told nothing about HOW. Experiment. Pick the two
                  objects you can reach fastest, carry one, drop it beside the
                  other, and read "productions" next turn. Every firing you see is
                  a rule you now own - write it in notes as "a + b -> c". When you
                  have two products, put THOSE two together. Never repeat a pair
                  that already fired to nothing.
- "get to the green goal square": if G is in "known", goto it. If not, sweep: the
  goal is almost always in the corner farthest from where you started.
Budget: you get eleven turns. If you have spent five and the target is still
unseen, stop being careful and cross the board in a straight line with goto plus
forwards - an unsolved task scores the same whether you were tidy about it or not.
Lava is the only thing worth being careful about: never goto through it, never
step forward onto ~.
```

### The driver (deterministic, shared by every policy)

`src/minigrid/driver.nim` — the starter's `src/ctf/control.nim` (directive → per-tick actuation),
retargeted from pixel steering to a **primitive queue**. It is the **only** producer of primitives,
and it contains no randomness.

| Action | Expands to |
|---|---|
| `left` `right` `forward` `pickup` `drop` `toggle` `wait` | itself, one primitive |
| `face D` | 0, 1 or 2 turn primitives — the shorter rotation; a 180° turn is `right, right` (never `left, left`), pinned for determinism |
| `goto x y` | the turn/step primitives that walk the BFS path below |

**The `goto` BFS**, run against the **known map as of turn start**:

- Nodes are cells; edges are 4-adjacency in the fixed order east, south, west, north.
- A cell is **traversable** iff its known glyph is `.`, `G`, or `D` (open door). `?`, `~` (lava),
  `#`, `d`, `L`, `k`, `o`, `b` are not. A cell known to hold an obstacle ball is not traversable
  either, even though the ball may have moved — the driver plans on what is known, not on hope.
- Breadth-first from the agent's cell; ties broken by the neighbour order above, so the path is
  unique for a given known map.
- If the **target** is traversable, the path ends **on** it. If the target is not traversable but is
  4-adjacent to some reached cell, the path ends on the nearest such cell and a final `face` toward
  the target is appended. If neither, the macro yields **zero** primitives and counts as
  `unreachable`.
- The path is rendered into primitives by walking it: at each step, `face` the next cell (0–2 turn
  primitives) then `forward`.
- Bounded by `macroPrimitiveCap = 40` primitives; the whole turn's queue is then truncated to
  `turnTicks = 12`.

The driver never invents an action the schema does not express, and it never produces a `forward`
into a cell it believes is lava or a wall — but it makes no promise about a cell it has never seen,
which is why walking into the unknown costs an explicit `forward` from the policy.

### Scripted baselines (both shipped as league fillers; `scout` is also the server-side fallback)

`src/minigrid/baselines.nim`, the starter's module retargeted. Both emit the **same** reply objects
an LLM does, through the same validator, which is what makes the bounded-orders test meaningful.
Neither ever emits `say` or `notes` — a baseline that narrated would make the feed lie about which
seats are LLMs.

**`scout`** — `PLAYER_SCRIPTED=scout`, and the fallback. A deterministic frontier explorer with a
goal check. Every turn, first matching rule wins, emitting at most 12 actions:

1. **Finish if you can.** If the current task's success is one primitive away — the cell ahead holds
   the object the mission names and the agent is empty-handed (`pickup`), or it is the locked door
   and the matching key is carried (`toggle`), or it is a closed door on the route (`toggle`), or the
   agent stands one `forward` from the goal square — emit that primitive.
2. **Go to the known target.** If the known map contains the object or cell the current subgoal
   names (the goal square; the key of the locked door's colour if not carried; the mission's referent
   for `babyai`; any object for `xland`), emit `{"do":"goto","x":…,"y":…}` for it, followed by the
   finishing primitive (`pickup` / `toggle` / nothing).
3. **Go to the nearest frontier.** Otherwise emit `goto` for the traversable known cell that is
   4-adjacent to the most `?` cells (ties broken by lowest BFS distance, then lowest `(y, x)`),
   followed by two `forward` and one `right`, so the plan actually crosses into the unknown and then
   changes heading.
4. **Spin.** If no frontier exists (the whole reachable region is mapped and the target is not in
   it), emit `spinTurns = 12` × `{"do":"right"}`.

`scout` never emits a path through lava (lava is not traversable to the BFS) and never `forward`s
into a known obstacle cell. It has no notion of production rules, so on `xland` it does rule 2 by
accident at best — which is the point of shipping it as the floor.

**`bumper`** — `PLAYER_SCRIPTED=bumper`. The reactive control, four lines: every turn emit twelve
actions, each `{"do":"forward"}` if the cell it expects to face is traversable in the known map and
not lava, else `{"do":"right"}`. It has no memory, no BFS and no mission parsing; it stumbles onto a
goal often enough to be a non-zero floor and never often enough to be a strategy. It is the control
that answers "did the LLM actually navigate?"

Like the starter's `DefaultBaselineParams` (`src/ctf/baselines.nim:38`), the tunables
(`frontierAdjacencyWeight`, `spinTurns = 12`, and whether the frontier score breaks ties by distance
or by `(y, x)`) are a parameter object chosen by `tools/tune_baselines.nim`'s sweep, not guessed;
`tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_minigrid_tuning.nim` asserts
the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/minigrid/`. The fork is a rename sweep
(`ctf` → `minigrid`, `CTF_WIRE` → `MINIGRID_WIRE`; a CI grep asserts no `ctf_` / `CTF_` identifier
survives outside comment history) plus the changes below. **The same modules compile twice**:
natively into `/bin/minigrid` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason an external Python engine is not an option here.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/minigrid/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417` |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/minigrid/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` (`replays.nim:142`) → **`MinigridReplayMagic = "COWLDMGD"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/minigrid/` (`control.nim` → `driver.nim`) | **fork**, retargeted not rewritten | the per-turn batch (`decide.nim:427`), the two deadlines, `turnSpacingMs` (`decide.nim:386-389`), the budget guard (`decide.nim:328-346`), tolerant parsing (`directives.nim:102`), the rune caps, the fallback ladder and its two log phrasings (`decide.nim:463`, `:491`) |
| `src/ctf/sim_state.nim` → `src/minigrid/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/minigrid/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames` (`roster.nim:64`), the results JSON builder (`squadResultsJson`, `roster.nim:650`) |
| `src/ctf/events.nim` → `src/minigrid/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/minigrid/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/minigrid/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/minigrid/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24` (`:376`), the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 140`, `MaxNoteRunes = 300`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/minigrid/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, and the validators at `:688-713` (whole-second `attempt1Ms`/`retryMs`, `attempt1Ms + retryMs ≤ turnBudgetMs`, positive `wallClockBudgetSeconds`) — all kept, and §Decisions' numbers are chosen to satisfy them |
| `src/ctf.nim` → `src/minigrid.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/minigrid_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** (40 022 bytes, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`) | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/minigrid_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling, and its `docker cp` source path changes from `/workspace/ctf/replay-viewer/dist/.` to `/workspace/minigrid/replay-viewer/dist/.` |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_red.png`, `data/soldier_red_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, **fog-of-war
raycasting and the first-person raycast pipeline** (replaced by the exact 7 × 7 flood above and a
2-D inset), spray cans, floor paint and the paint grid, the paint buff, King of the Hill and
`hillTicks`, the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the
barrage, med kits, shields, cardboard barriers, trenches, perks, handicaps, lives and respawns,
**teams and four-team free-for-all** (there is one seat), **shouts-as-cog-speech and
`ShoutMaxChars`**, achievements, campaign mode, `maxGames > 1` side-swapping, and **all of the
pixel-space map machinery**: `arena.nim`'s wall masks and pixel queries, `map_art.nim`,
`mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`, `tools/map_editor*.nim`,
`tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`, `docs/MAPKIT.md`. The
board here is a fixed 13 × 13 integer cell grid built by seeded generators in code; every one of
those is a config surface the task rules would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `*_front_gun`, `soldier_{blue,
green,yellow}*`, `rig_real/`) and the blue/green/yellow locker-room webps — there is one cog and it
is red.

### New modules

- `src/minigrid/grid.nim` — the cell enum, the colour enum, the glyph table, the passability and
  see-behind tables, the 13 × 13 grid type, 4-adjacency in the fixed order east/south/west/north, the
  BFS used by `goto` and by `scout`, and the **7 × 7 visibility flood** exactly as written in §The
  game. Pure integer; no pixie, no pixel queries.
- `src/minigrid/tasks.nim` — the seven generators, their success predicates, their three named
  subgoal predicates each, the mission-sentence builders (including the BabyAI three-rule grammar),
  and the ladder tables for the two variants.
- `src/minigrid/agent.nim` — the agent record, the seven primitives of tick step 3 with their exact
  effects, the carry slot, and the known-map merge of tick step 7.
- `src/minigrid/xland.nim` — the rule-set sampler (three rules with the chained goal), the
  adjacency scan of tick step 5, and the production history the observation exposes.
- `src/minigrid/sim.nim` — the step loop of §The game exactly as numbered, `gameHash`, task and
  episode end evaluation, scoring, and the seat's observation builder. Imports and re-exports the sim
  modules, as the starter's does, so `import minigrid/sim` sees everything.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cell coordinates, directions, tick counters, BFS distances,
subgoal counters, scores. There is no floating point anywhere in `sim.nim`, `grid.nim`, `tasks.nim`,
`agent.nim`, `xland.nim`, `driver.nim` or `baselines.nim`, and a test greps for it. That makes the
native ↔ wasm hash chain exact by construction.

**One seeded source, and it is a hash, not a stream.** Every generated quantity — `gapX`, `gapY`,
`wallX`, `doorY`, key/goal/object cells, `instructionKind`, the six `(type, colour)` pairs, the three
`xland` rules, obstacle spawn cells, and every obstacle's per-tick direction — is a read of the pure
hash `mix64(seed, taskIndex, salt)` or `mix64(seed, taskIndex, salt, tick)` (splitmix64 over the
mixed words), evaluated independently. Nothing the policy does can shift a draw, reorder draws, or
consume one out from under a later task: **task `k`'s layout is identical no matter what happened in
task `k − 1`**, which is the strongest form of the idea's "task seeds held out" and what makes
per-task success rates comparable across policies.
`tests/test_minigrid_tasks.nim` asserts it by generating every task of every variant under three
different policy behaviours and comparing the full layouts byte for byte.

There is no other random draw. The seed is randomised in `src/minigrid.nim` before `config.update`
(the starter's rule), recorded in the replay config and in `results.seed`. Two episodes with the same
seed and the same plans are byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDMGD`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, variant, `num_agents`, every rule constant, the task ladder,
   `players[].name`, `slots[]`, `fastMode`), then the record stream — the join record, **per-turn
   plan records** (the only inputs this game has), chat records (`register` / `directive` /
   `fallback` / `budget_guard` / `stop` / `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/minigrid_replay.nim` — which imports the
   **same** `src/minigrid/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container
   in `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `minigrid_load_replay` runs `parseReplayBytes` + `initReplayRuntime`;
   `minigrid_frame` re-steps the sim from the recorded plans and compares `sim.gameHash()` against
   the recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it
   happens and surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: `taskIndex`, `taskTick`; the agent's
   `(x, y, dir, carriedType, carriedColour)`; then every cell of the 13 × 13 grid in ascending
   `(y, x)` as `(contentKind, colour, doorState)`; then, for `dynamic`, every obstacle in ascending
   index as `(x, y)`; then, for `xland`, the fired-rule bitmask and `productionsFired`; then the
   three subgoal credit bits of the current task; then the five `taskOutcome` codes and five
   `taskProgress` values; then `tick`.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact
   cannot be re-derived from sim state, so the stop is written as one record applied by the *same
   proc* on record and on playback, and `tests/test_minigrid_replay.nim` runs the record → re-derive
   check for **every** end reason (`gauntletComplete`, `turnCap`, `wallClock`, `fault`), not just the
   healthy one (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 660 hashes + ≤ 55 plan records + ~70 chat records ≈ **18 KB**. Everything else — every
layout, every mission sentence, every cell, every obstacle position, every production — is
re-generated in the browser from the seed and the variant.

### Documented divergences (mirrored into `docs/PORTING-MINIGRID.md`)

1. **No MiniGrid, no BabyAI, no XLand-MiniGrid dependency, and no bit-exactness.** Decided as a
   scoping rail before design. Those packages are Python/JAX with their own RNG and their own
   registries; embedding one means a simulator that cannot compile to wasm, so the static replay
   viewer — a non-optional pin — would be impossible. No upstream code is vendored, no upstream
   numbers are claimed as reproduced, and no benchmark score from this coworld is comparable to a
   published MiniGrid number. What is reproduced is the *problem*: 7 × 7 partial observability with
   the same occlusion rule, the same seven primitives, the same object vocabulary, and the same three
   task ideas (keys and doors, lava, a sentence, hidden rules).
2. **One board size, seven families.** 13 × 13 for everything, and the families are re-authored
   analogues, not registered environments: `multiroom` is a four-room quad rather than a chain of
   procedurally sized rooms, `keycorridor` is three side rooms rather than a scaling ladder, and
   **`ObstructedMaze` is not implemented at all** (§Out of scope).
3. **The agent gets world coordinates and a remembered map.** MiniGrid hands the policy an
   egocentric image and nothing else. An LLM re-prompted fresh each turn has no hidden state, so
   this game keeps the memory for it and reports `(x, y)` so `goto` has a frame. Unobserved cells
   stay unobserved — the partial observability the idea names is fully preserved; only the *memory
   burden* is lifted.
4. **Actions are batched under a driver, not stepped one per call.** The idea's "per-tick discrete"
   interface is preserved as the primitive set; what changed is *who calls it*. Twelve primitives per
   LLM turn under a deterministic driver, plus two macros (`goto`, `face`) that expand to primitives.
   One LLM call per primitive would be ~660 calls in a 720 s budget — impossible — and a policy that
   cannot express "walk over there" spends every turn turning.
5. **Reward shape.** MiniGrid's sparse reward is `1 − 0.9 · steps/maxSteps` on success, 0 otherwise.
   The league needs one rankable integer, so §The game makes tasks-solved the dominant term,
   subgoal progress the second and speed the third. All three underlying quantities are in `results`,
   so a MiniGrid-style per-task success rate is directly readable.
6. **Dynamic obstacles never kill passively.** In this sim an obstacle refuses to move into the
   agent's cell; only a `forward` the policy chose can end the task. That matches MiniGrid's own
   Dynamic-Obstacles termination and removes an unavoidable death.
7. **A key is not consumed by unlocking**, doors can be closed again, and a box opens into its
   contents — the MiniGrid semantics, stated because they are the ones an implementer guesses wrong.
8. **`maxGames = 1`** — the starter's multi-game episode is not used; a gauntlet has no side to swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with a variable turn length (the tick loop breaks early
   when a task finishes) and one seat in the batch.
2. **Registration interception** — the seat's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration, **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim, and the server **logs loudly and refuses to start the game** when the joined seat has no
   register record (the grf-football 2026-08-27 silent-default scar). Any other chat text from the
   seat is dropped — the cog speaks through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration (`server.nim:1407-1417`), kept, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wallClock`, and written as the load-bearing stop record of §Determinism point 5.

### The two named edits to `roster.nim`

1. **Alias.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → **`Alpha`** for the only
   seat. The `IdentityNames` array itself (`roster.nim:64-65`) is unchanged. Board labels and the
   label manifest inherit the two-name-space rule with no further change, and `showPlayerLabels` is
   false.
2. **`squadResultsJson` → `gauntletResultsJson`** (`roster.nim:650`) — one entry per seat, one entry
   in every seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a 13 × 13 cell grid, not a pixel arena.**
   `buildSpriteProtocolPlayerUpdates` emits cell-space coordinates; the raycast fov cache and
   shadowcasting are deleted and replaced by the exact visibility flood's boolean mask, which the
   viewer draws as the fog wash.
2. **Object, door and obstacle pools.** New pools `CellObjectBase` (sized to 121), `DoorBase` (sized
   to 8) and `ObstacleBase` (sized to 8), filled in ascending `(y, x)` and emitted incrementally like
   the starter's other object families.
3. **Baked room bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the way
   the starter bakes endzone paint, and the floor grain, the cell gridlines and the wall bevels are
   baked onto it once (§Viewer → Art) — one static bake per board size, so the per-frame cost is the
   agent, ≤ 12 objects, ≤ 8 doors, ≤ 6 obstacles, the fog mask and the overlays.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST` / `PORT`; the player
socket at `/player?slot=0&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset
route: `GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering
for the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). The
player websocket handler **closes unless the token matches the seat** (the certifier probes with a
bad token — cogame-flatland 0.1.1). Global broadcasts are fire-and-forget so a slow viewer can never
stall the episode.

### Results document (closed schema; `gauntletResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":              ["daveey"],
  "aliases":            ["Alpha"],
  "scores":             [311170],
  "win":                [true],
  "winner":             0,
  "reason":             "complete",
  "endRule":            "gauntletComplete",
  "variant":            "gauntlet",
  "seed":               1734029581,
  "taskCount":          5,
  "parTasks":           3,
  "tasksSolved":        3,
  "progressTotal":      11,
  "speedTotal":         17,
  "taskFamilies":       ["lavagap", "doorkey", "multiroom", "keycorridor", "babyai"],
  "taskMissions":       ["get to the green goal square",
                         "use the yellow key to open the door and then get to the green goal square",
                         "get to the green goal square",
                         "pick up the blue ball",
                         "put the red ball next to the blue box"],
  "taskSolved":         [true, true, false, false, true],
  "taskOutcome":        ["solved", "solved", "timeout", "died", "solved"],
  "taskTurns":          [4, 7, 11, 6, 5],
  "taskTicks":          [41, 79, 132, 68, 55],
  "taskProgress":       [3, 3, 2, 0, 3],
  "deaths":             1,
  "crashes":            0,
  "taskCellsSeen":      [63, 88, 71, 54, 97],
  "cellsTotal":         169,
  "doorsOpened":        4,
  "objectsPickedUp":    3,
  "productionsFired":   0,
  "primitivesExecuted": 341,
  "actionsDropped":     6,
  "macrosUnreachable":  2,
  "repliesRepaired":    1,
  "finalTick":          375,
  "turnsPlayed":        33,
  "policyKinds":        ["llm"],
  "llmTurns":           32,
  "fallbackTurns":      1,
  "deadSeats":          [false],
  "stopDetail":         ""
}
```

`taskOutcome` is a closed enum: **`solved` | `timeout` | `died` | `crashed` | `unreached`**, the last
being a task the episode never reached (the `deadline` case). `taskCellsSeen[i]` is the number of the
169 cells of task `i`'s board that entered its known map; `cellsTotal` is the per-board constant 169.
`primitivesExecuted` counts every primitive that was **not** `wait`, so `finalTick −
primitivesExecuted` is the number of ticks the cog stood still. Four identities hold in every results
document and are asserted by `tests/test_minigrid_engine.nim`:
`Σ taskTurns == turnsPlayed`; `Σ taskTicks == finalTick`;
`taskSolved[i] == (taskOutcome[i] == "solved")` and `taskSolved[i]` implies `taskProgress[i] == 3`;
and `scores[0] == 100_000 × tasksSolved + 1_000 × progressTotal + 10 × speedTotal`. The example above
satisfies all four: `tasksSolved = 3`, `progressTotal = 3+3+2+0+3 = 11`,
`speedTotal = (11−4)+(11−7)+(11−5) = 17`, `100_000×3 + 1_000×11 + 10×17 = 311_170`.

Adding a key means updating `gauntletResultsJson`, the manifest's `results_schema` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas are closed and
undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDMGD`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (`SMOKE_REQUIRE_REPLAY_JSON`, template line 31).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"minigrid/v1","gameVersion":"1","seed":…,"variant":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"plans":[…],"says":[…],"fallbacks":N,"results":{…}}` — by
  brace-matching the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for `docs/SPEC.md` §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.tasksSolved, .results.endRule' /tmp/ep.json
  jq -r '[.plans[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  ```
  Require `protocol == "minigrid/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.tasksSolved >= 1`, and the champion seat's plans with `source == "llm"`, real
  verbs (including at least one `goto`) and non-empty `say` lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDMGD`, format version, `gameName` `minigrid`, `gameVersion` `1` |
| config JSON | `seed`, `variant`, `num_agents`, `gridSize`, `viewSize`, `turnTicks`, `taskTurnCap`, `taskCount`, `taskLadder`, `maxTurns`, `maxTicks`, `parTasks`, `obstacleCount`, `xlandRules`, `xlandObjects`, `babyaiObjects`, `maxActionsPerTurn`, `macroPrimitiveCap`, `spinTurns`, `players[].name` (real name), `slots[]`, `fastMode` |
| join | the seat's `name` (real policy name), `slot`, `token` |
| plans | per turn: the accepted action list — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

**The task generators are code, compiled into both the binary and the wasm module**, and the replay
carries the seed, the variant and every rule constant; the viewer therefore reconstructs every
layout, every mission sentence and every hidden rule table from bytes it already has, with no fetch.
A generator change is a `GameVersion` bump, and the committed fixtures' version sweep makes an
unversioned change fail the build.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `task`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `actions` (the accepted array), `executed` (the primitives that ran), `truncated`, `dropped`, `unreachable`, `say` (≤ 140 runes), `view` (the observation minus `notes`) |
| `fallback` | `turn`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of seventeen kinds, plus `end`:**

`taskstart` `{i, family, mission, cap}`; `turn` `{n, task, taskTurn}`;
`plan` `{n, verbs, truncated, dropped}`; `say` `{text}`; `fallback` `{cause}`;
`pickup` `{type, color, x, y}`; `drop` `{type, color, x, y}`; `open` `{color, x, y}`;
`close` `{color, x, y}`; `unlock` `{color, x, y, key}`; `produce` `{a, b, out, x, y}`;
`subgoal` `{i, which, label}`; `lava` `{x, y}`; `crash` `{x, y}`;
`solved` `{i, turns, ticks}`; `failed` `{i, why}`; `budget` `{turn, remaining_s}`;
plus `end` `{reason, endRule, solved, of, score}`.

`tests/test_minigrid_events.nim` asserts the emitted set equals exactly this list. `plan` fires once
per turn (≤ 55 an episode) and drives the feed's action line; `subgoal` fires at most 15 times.
Nothing here fires per tick, so the feed never floods.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`taskstart`,
`solved`, `failed`, `unlock`, `produce`, `fallback`, `end`.** `turn`, `plan`, `say`, `pickup`,
`drop`, `open`, `close`, `subgoal`, `lava`, `crash` and `budget` drive the feed, not the scrubber
(`lava` and `crash` arrive one tick before the `failed` beat they cause, so beating both would draw
two markers on the same tick).

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `TaskStart, TurnStart, Directive, Fallback, Primitive, Pickup, Drop,
DoorOpen, DoorClose, DoorUnlock, Produce, Subgoal, Death, Crash, Solved, Failed` and the mandatory
trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept. `Primitive` is the per-tick row
that makes this stream a full action trace for `cogamer-rl` — 660 rows an episode, which is what the
idea's "natural home for LLM-RL experiments" needs and what the replay deliberately does not carry.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/minigrid/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/minigrid_replay.nim`, forked
from `replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` +
`static_replay_worker.js`, and `index.html` (built from `client/replay_broadcast.html`) ALL come from
ONE starter: `coworld-ctf`** — which is this repo's own starter. **Never a mixture.** Splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE` / `EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23). The set
is internally consistent and is kept as one piece: the Worker sets `Module.onRuntimeInitialized`
(`replay-viewer/static_replay_worker.js:188`), the module is emitted **non-modularized** as
`minigrid_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals — the
starter's own comment at `replay-viewer/config.nims:33-41`), `-s FILESYSTEM=1`,
`-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_minigrid_load_replay,_minigrid_frame,_minigrid_input,
_minigrid_packet_ptr,_minigrid_packet_len,_minigrid_mismatch_tick,_minigrid_error_ptr,
_minigrid_error_len,_minigrid_stage_ptr,_minigrid_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './minigrid_replay.js')` in that order
(the starter's line 239, renamed only).

`minigrid_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`,
and the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running
module destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `minigrid_load_replay` re-simulates the whole episode once headlessly
  (660 ticks over a 169-cell grid — sub-millisecond in wasm), records the per-tick cumulative
  subgoal credits and tasks solved, the task boundary ticks, the beat ticks and the lull spans, then
  resets and renders frame 0. That is what lets the progress sparkline and the scrubber beats draw at
  **full width on the first frame** instead of growing in.
- `minigrid_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (`replay-viewer/static_replay.js:158-161`) —
posted by the Worker only *after* `ingestPacket()` (`static_replay_worker.js:64`) has handed
BroadcastCore the first frame and it has drawn, so the attribute means "a frame is on the canvas",
not "a file was fetched". On failure it sets **`data-replay-error`** on `<html>` with the message, in
`showFailure()` (`static_replay.js:8-20`). Both are coworld-ctf's own signals, inherited unchanged —
this fork adds neither and removes neither. The `coworld-replay` postMessage bridge's `ready` is
posted **from a callback fired after** `data-replay-loaded="true"` is set, never on rAF timing at the
call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes; sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`). Not edited, not reformatted;
  `tests/test_minigrid_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in
  the appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats` ignores kinds it does
  not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (`client/replay_broadcast.html:4276-4325`), transport, endcard, locker-room loader, `?embed=1` mode
  and `.tiny` density system are untouched, and the block is installed through the starter's own
  splice hook: `window.PaintballChrome` (context built at `:4330`, installed at `:4337`, declared at
  `:4651`) is renamed `window.MinigridChrome` and its `install(PB_CTX)` / `frame(s, ctx, jumped)`
  (`:2075`) / `event(e, s, ctx)` (`:3480-3481`) entry points are kept with the same signatures. The
  appended block replaces only the *contents* of the scorebug plate, adds the mission ribbon, the
  task pips and the fog wash, retargets the agent-view inset, the feed rows, the beat rendering, the
  momentum series and the endcard columns. The block sits after the starter's banner comment at
  `:4344` and a test asserts the starter's byte prefix is intact up to that marker and that the file
  only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text
  by `tests/test_minigrid_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed
  queue and `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift
  threw mid-replay and latched `static_replay.js` into `failed`), `banner`, the beat and lull
  machinery, the endcard builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` →
  `window.MINIGRID_WIRE` rename emitted by `tools/gen_wire_constants.nim`. Deleted: every
  ctf-specific draw call, the raycast FPV pipeline (the `#fpv` **canvas** is reused, the raycaster is
  not), and `attachMinimap`'s call site. Added: `drawRoomBed`, `drawCells`, `drawObjects`,
  `drawAgent`, `drawFog`, `drawAgentView`, `drawMissionRibbon`, `drawTaskPips`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read` (`replay_broadcast.html:1510-1521`), and the page's
    `core.attachMinimap($('minimap-canvas'))` call (`:4200`). **Zoom decision: dropped.** The board is
    a fixed 13 × 13 cell grid with no off-frame area; `relayout()` letterboxes it whole at every width
    (see "Legible at 360 px"), so per the pin a fixed arena drops `#viewpanel` entirely.
    `broadcast_core.js` already tolerates never being attached: `minimapSurface` / `minimapCtx` stay
    null and `drawMinimap()` returns on its first guard.
  - **`#povBadge`** (`:1525`) and the `togglePov` wiring — with one seat there is nothing to select.
  - Inside the kept `#fpv`: **`#fpv-hp`** (`:1537`), **`#fpv-gear`** (`:1538`), **`#fpv-map`** and
    **`#fpv-map-canvas`** (`:1542-1543`) — the cog has no hit points, no gear, and an un-fogged
    tactical map is redundant when the main board *is* the un-fogged view.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip` (`:300-330`), `.pb-tags`, `.squad` (`:2219-2244`), and the `.ec-heart` endcard glyphs
    (`:1221-1231`).
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture` (`:919-934`) and `.gamestart`,
    `.hillflip`, `.tagout`, `.gameover` (`:4431-4443`) CSS rules — those kinds are never emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS, `:245`).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with `#plates-l` / `#plates-r` /
    `#clock` / `#clock-time` / `#clock-caption` / `#ffwd-mini`, **`#fpv` with `#fpv-canvas`,
    `#fpv-hud`, `#fpv-name`, `#fpv-cap` and `#fpv-grip`** (repurposed: it becomes the agent's 7 × 7
    window, caption `AGENT VIEW 7×7`, `#fpv-name` reading `ALPHA · FACING EAST`, still draggable and
    resizable by the starter's own grip), `#bannerlane`, `#killfeed`, `#mmwarn`, **`#transport` in
    full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`,
    `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub`
    with `#momentum` / `#scrub-fill` / `#lulls` / `#scrub-win` / `#scrub-head`, `#endcard` with
    `#ec-headline` / `#ec-wincond` / `#ec-how` / `#ec-teams` / `#ec-replay`, and `#status`.
    **`#plates-r` is kept but rendered empty** — it is one of the scorebug's three flex columns and
    removing it would un-centre `#clock`; with one seat the single plate lives in `#plates-l`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here
and enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`:3795`) | `<span>Task</span><span>Mission</span><span>Result</span><span>Turns</span><span>Credits</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` (`:3788`) | `<span>Cog</span><span>Solved</span><span>Seen</span><span>Score</span>` |
| `<span class="fl-cap">Lives left</span>` (`:3793`) | `<span class="fl-cap">Tasks solved</span>` |
| `<span class="fl-cap">Hill time</span>` (`:3786`) | `<span class="fl-cap">Cells seen</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (`:1576`) | `<span class="momentum-label">PROGRESS</span>` |
| `<span class="lives-label">Lives</span>` (`:2241`) | `<span class="solved-label">Solved</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (`:2224`) | `<span class="solved-label pb-lbl">Carrying</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (`:1480`, `:1842`) | "Reading the mission…" |
| `#clock-caption` "In the locker room" (`:1499`) | "Waiting for the cog" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (`:1524`) | "Replay hash mismatch at tick N — showing recorded actions" |
| `#fpv-cap` "EYES" (`:1545`) | "AGENT VIEW 7×7" |
| `#btn-spoilers` title "Spoilers: kills / flag story / winner on the timeline ahead of the playhead (o)" (`:1564`) | "Spoilers: solved / failed tasks on the timeline ahead of the playhead (o)" |
| team words `RED` / `BLUE` in `.ec-tname` / plates (`:2222`, `:2239`, `:3783`, `:3790`, `:3836`) | the seat's **alias** (`ALPHA`) on the plate, and the **task family name** (`LAVAGAP` … `BABYAI`) as the endcard section head |

**`tests/test_minigrid_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for
a forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `EYES`, `spray`, `grenade`, `med kit`, `kill`, `team` — outside comment blocks, and
asserts **zero** matches; and asserts each replacement string above is present exactly once. A rename
that reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (`client/replay_broadcast.html:4291-4317`). **No overlay sits in the transport
band**: the board is laid out between the two bands and every addition here (the mission ribbon, the
task pips, the agent-view inset, the feed) is positioned inside the board region, in the letterbox
gutters beside it, or in the top band. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, `:1047`, the starter's rule, kept) so the scrubber stays
clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `mgBeat(tick, kind, label)` — named with the `mg-` prefix so it can
never shadow `chrome_common.js`'s `markBeat` alias (`client/replay_broadcast.html:1635`; the tandem
2026-08-23 hoisting trap, and the same prefix discipline the starter's own `pbBeat` at `:4475` uses)
— appends `<button class="beat-marker <kind>" title="…" aria-label="…">` to `#scrub` and seeks on
click. CSS exists for **every kind emitted and no others**: `.beat-marker.taskstart`,
`.beat-marker.solved`, `.beat-marker.failed`, `.beat-marker.unlock`, `.beat-marker.produce`,
`.beat-marker.fallback`, `.beat-marker.end`. The game block never calls `markBeat`, so an unlabelled
div marker cannot appear.

**Playback rate: one tick per three animation frames at 30 fps = 10 ticks/second** (speed chips
`[0.5, 1, 2, 4, 8]`, default 1), with the agent's position and heading interpolated across the three
frames so a `forward` glides and a `left` swings rather than snapping. A 660-tick episode therefore
plays for **66 s**, and even a fast 200-tick episode plays for 20 s, which is what lets
`viewer_smoke.mjs --soak 10` observe real advancement instead of a legitimately-finished replay (the
ecos 2026-08-23 scar).

### Readouts

1. **The board**, drawn edge to edge: the baked floor bed with gridlines; walls as bevelled stone;
   lava as an animated two-frame bake; the goal square; doors as coloured panels (a keyhole when
   locked, swung open when open); keys, balls and boxes as coloured chips; and the **cog** as the
   composited soldier rig at its four facings with a direction wedge. This is the idea's "top-down
   full view for spectators".
2. **The fog wash** — every cell the agent has never seen is drawn under a heavy dark wash; a cell
   seen but not currently visible is drawn under a light wash with its remembered contents; a cell in
   the current 7 × 7 visible set is drawn clean and bright. The spectator therefore sees, at a
   glance, **the whole board and how much of it the cog knows** — which is what makes a wasted turn
   legible as a wasted turn. This is the single most important readout in this game.
3. **The agent's 7 × 7 window, inset** (the idea's ask) — the repurposed `#fpv` panel, bottom-right
   in the board's letterbox gutter, drawing exactly the `view` array the seat receives: agent-up,
   `?` cells blank, the cog at the bottom centre, captioned `AGENT VIEW 7×7` with
   `ALPHA · FACING EAST` beneath. Draggable and resizable by the starter's own `#fpv-grip`.
4. **Mission text on screen** (the idea's ask) — a mission ribbon in the board's left gutter reading
   `TASK 2/5 · DOORKEY` above the sentence itself in full, wrapped, in the starter's display face;
   and the sentence is re-announced in `#bannerlane` for two seconds at every `taskstart`.
5. **Task pips** — five pips under the mission ribbon, one per task in ladder order: pending (hollow),
   current (amber ring), solved (green fill), failed (red fill with a slash), unreached (grey). Each
   pip carries its family name at full width and a tooltip at `.tiny`.
6. **Clock** — `#clock` shows the big numeral `SOLVED 3/5`; `#clock-time` shows
   `task 4/5 · turn 6/11`; `#clock-caption` shows `tick 268/660 · seen 97/169 · score 311170`.
7. **Scorebug plate** — one plate in `#plates-l`: the seat's **real policy name** (spectator side
   only), its in-game alias `ALPHA`, the cog avatar from `data/soldier_red_front.png`, the running
   score as the numeral, a **carrying chip** showing the held object's colour and type (or `—`), and
   a `↯` glyph if the seat has taken a fallback.
8. **Match feed** (`#killfeed`) — plain language, never internal notation: `TASK 2 — DOORKEY: "use
   the yellow key to open the door and then get to the green goal square"`,
   `PICKED UP THE YELLOW KEY`, `UNLOCKED THE YELLOW DOOR AT (6,3)`, `SUBGOAL — DOOR OPEN (2/3)`,
   `PLAN CUT OFF — 18 STEPS ASKED, 12 RUN`, `STEPPED INTO LAVA — TASK 1 LOST`,
   `WALKED INTO A GREY BALL — TASK 1 LOST`, `RULE FOUND: RED KEY + BLUE BALL → PURPLE BOX`,
   `TASK 4 SOLVED IN 5 TURNS`, `Alpha: "I have the yellow key; opening the door and heading east"`,
   and `MISSED THE CALL — scout plan (timeout)`. The `say` lines and the plan lines are where a
   spectator sees the LLM playing.
9. **Progress sparkline** — the starter's `#momentum` SVG retargeted to one cumulative series
   (subgoal credits earned, 0 … 15) with **task spans shaded** in the pip colours behind it, task
   boundaries as vertical ticks, and the playhead marked. Filled from the load-time pre-scan, so it
   draws at full width on the first frame. A flat stretch inside a red span is the whole story of a
   lost task in one glance.
10. **Endcard** — `3 OF 5 SOLVED — PAR 3 MET`, a five-row table under the re-mapped header
    (`Task | Mission | Result | Turns | Credits`) with each row's mission sentence in full, a summary
    line (`373 of 845 cells seen across the five boards, 4 doors opened, 1 death, 0 crashes, 1
    fallback turn`), and
    `SCORE 311170`. It stops at `var(--band)` and any seek dismisses it.
11. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull
    = 30 consecutive ticks with no `pickup`, `drop`, `open`, `unlock`, `produce`, `subgoal` or
    `solved` event and no change in the agent's cell, from the pre-scan), spoilers switch, tick
    readout, speed chips, the scrubber with its seven beat kinds, and `#mmwarn` on a hash mismatch —
    all the starter's, verbatim.

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no
solid-colour squares, no downloads.** The floor is `data/arena_floor.png`, tiled and darkened 30 %,
with baked gridlines in the palette from `data/pallete.png` — one pixie bake at install, exactly the
way the starter bakes endzone paint. **Walls** are cut from `client/art/walls/wall_h.jpg` and
`wall_v.jpg` at cell size with a baked bevel, so a wall run reads as masonry rather than a black bar.
**Lava** is a two-frame procedural bake in the palette's reds and oranges with a crust pattern, cycled
at 4 Hz. The **goal square** is a baked green tile with the starter's endzone hatch. **Doors** are
baked once: 6 colours × 3 states (closed panel, locked panel with a keyhole, open panel swung into
the jamb) = **18 chips**. **Keys**, **balls** and **boxes** are baked once at 6 colours each = **18
chips**, the box crate tinted from `wall_h.jpg`, the key and ball drawn in the palette with a
specular. The **cog** is `data/soldier_red.png` composited by `rig_art.nim` into 4 facings × 2 sizes
= **8 chips**, with a procedural direction wedge; `data/soldier_red_front.png` is its avatar on the
scorebug plate and in the agent-view caption. Intersection-free cell labels and every chrome numeral
are set in `data/font.ttf`. The fog wash, the task pips, the mission ribbon and the sparkline are
procedural in the bed bake's palette. The loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the four red webps) with the caption re-labelled.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (`client/replay_broadcast.html:4307-4312`). The board's aspect is **13/13 = 1.000**. In a
360 × 203 frame, `relayout()` reserves `--topband` and `--band`, leaving a play region roughly
360 × 120; since `360/120 = 3.0 > 1.000`, **height binds**: the board renders **120 × 120**, i.e.
**9.2 px per cell**, with the whole grid in frame — which is why `#viewpanel` is dropped. That
letterbox leaves **two ~120 px gutters**, and this game uses them: the **mission ribbon and the task
pips live in the left gutter**, the **7 × 7 agent-view inset in the right**, so neither ever overlaps
the board and neither ever enters the transport band. At 120 px the inset draws its 7 cells at
**12 px each** — larger than the main board's cells, which is correct, because the inset is what the
cog actually sees. Five rules are added and asserted by `tests/test_minigrid_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, the single plate keeps only `alias + name + solved + carrying chip`; the avatar
   shrinks to 10 px and the fallback glyph moves inline.
3. Under `.tiny`, the mission ribbon wraps to at most **three lines at 9 px**, ellipsising the fourth,
   and keeps `TASK n/5 · FAMILY` on its own line above; the full sentence stays in the `title`
   attribute and in `#bannerlane` at every `taskstart`.
4. Under `.tiny`, the task pips drop their family captions to tooltips and render as five 12 px pips
   in a row; the fog wash uses a **higher-contrast** two-step (unseen / seen) instead of the
   three-step, because a 9 px cell cannot carry three wash levels.
5. Under `.tiny`, the agent-view inset is pinned to 84 px square in the right gutter (the `#fpv-grip`
   resize is disabled below 620 px so it cannot be dragged over the board), and every glyph it draws
   is a chip, never text, at `--hudscale`-derived sizes so nothing is drawn outside the canvas
   (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-minigrid`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `minigrid`; **`game.name` is `minigrid`** —
  identical to the slug, so the secret namespace `secret://coworld/minigrid/anthropic_api_key`, the
  page slug, the `POST /coworld-league-seeds` body and the docs all agree (the commons-family
  2026-08-24 scar, where `game.name` and the slug differed by an underscore).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services/two
  images (`compose.yaml` `game` + `player`); this fork uses the one-image / two-entrypoints shape
  because the shared `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers
  precedent):

  ```yaml
  services:
    minigrid:
      image: coworld-minigrid:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{MINIGRID_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:minigrid src/minigrid.nim` →
  `/bin/minigrid`, and the same for `src/minigrid_player.nim` → `/bin/minigrid-player`. The runtime
  stage copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/minigrid"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block)
  with the asset list swapped to `data/{arena_floor,ascii,pallete}.png`,
  `data/soldier_red{,_front}.png`, `data/font.ttf`, `client/art/walls/*`,
  `client/art/lockerroom/{bg.jpg,red_*.webp}`, `minigrid_replay.{js,wasm,data}`, `wire_constants.js`,
  `broadcast_core.js`, `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`,
  `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["gridworld", "single-agent", "instruction-following",
    "exploration", "minigrid"]` (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0);
    **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "minigrid"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/minigrid"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/minigrid/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 1/1, `players` 1/1, `slots` 0/1, `taskLadder` 5/5 — the tandem 0.1.0 scar). `tokens` is
    described as runner-injected; **no `game_config` anywhere in this manifest contains a literal
    `tokens` array** (matriculate rejects "game_config must not include runner-managed tokens" —
    knights-archers 0.1.0), while `config_schema` keeps *requiring* it because the runner injects it.
    Properties: `tokens`, `players`, `slots`, `seed`, `num_agents`, `minPlayers`, `gridSize`,
    `viewSize`, `turnTicks`, `taskTurnCap`, `taskCount`, `taskLadder`, `maxTurns`, `maxTicks`,
    `parTasks`, `obstacleCount`, `xlandRules`, `xlandObjects`, `babyaiObjects`, `maxActionsPerTurn`,
    `macroPrimitiveCap`, `spinTurns`, `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`,
    `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`, `fastMode`,
    `showPlayerLabels`, `model`, `maxOutputTokens`, and `num_agents`
    (integer, `minimum: 1`, `maximum: 1`, default 1).
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`,
    `endRule: {"type":"string","enum":["gauntletComplete","turnCap","wallClock","fault"]}` and
    `taskOutcome` items `{"enum":["solved","timeout","died","crashed","unreached"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-minigrid/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"actions.md","title":"Actions and the reply format","content":{"type":"uri","value":".../docs/ACTIONS.md"}},
    {"id":"porting.md","title":"What this is and is not a port of","content":{"type":"uri","value":".../docs/PORTING-MINIGRID.md"}}]}`.
  - Top-level `player[]` with `id` / `type` / `name` / `description` / `image` / `run` /
    `source_url` and `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` —
    **`limits.cpu` must be at least `"1"`** (pistonball 0.1.1). **Exactly ONE entry, `scout`**:
    `num_agents = 1` leaves exactly one certification slot, and **every declared player must occupy a
    certification slot** (the raid 0.1.2 scar), so a second declared player could not be seated.
    `bumper` still ships in the image, is exercised by `tests/test_minigrid_driver.nim`, and is a
    league filler in `tools/ci/policies.json` — it is simply not a *declared manifest* player.

  **Variants — `num_agents: 1` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "gauntlet", "name": "Gauntlet (1 cog, 5 MiniGrid tasks)",
     "description": "Five partially observed 13x13 gridworlds, one after another, each with a sentence telling the cog what to do: cross the lava gap, find the yellow key and unlock the door, thread four rooms behind closed doors, fetch the blue ball from a locked side room, and follow one BabyAI instruction. The cog sees only a 7x7 window and gets eleven turns a task. Score is how many of the five it solved.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "gridSize": 13, "viewSize": 7,
                     "turnTicks": 12, "taskTurnCap": 11, "taskCount": 5,
                     "taskLadder": ["lavagap", "doorkey", "multiroom", "keycorridor", "babyai"],
                     "maxTurns": 55, "maxTicks": 660, "parTasks": 3,
                     "obstacleCount": 6, "xlandRules": 3, "xlandObjects": 6, "babyaiObjects": 6,
                     "maxActionsPerTurn": 12, "macroPrimitiveCap": 40, "spinTurns": 12,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9500, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "xland", "name": "XLand rules (1 cog, hidden production rules)",
     "description": "A moving-obstacle warm-up, then three worlds whose rules are secret: six objects, a sentence naming a thing that does not exist yet, and a hidden table of three recipes that turn objects pushed together into new ones. The only way to learn a recipe is to try it, and each of the three worlds resamples the table. Ends on one BabyAI instruction so the two variants share a final task.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "gridSize": 13, "viewSize": 7,
                     "turnTicks": 12, "taskTurnCap": 11, "taskCount": 5,
                     "taskLadder": ["dynamic", "xland", "xland", "xland", "babyai"],
                     "maxTurns": 55, "maxTicks": 660, "parTasks": 2,
                     "obstacleCount": 6, "xlandRules": 3, "xlandObjects": 6, "babyaiObjects": 6,
                     "maxActionsPerTurn": 12, "macroPrimitiveCap": 40, "spinTurns": 12,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9500, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 1` again, inside `certification.game_config`, and exactly
  one player so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 1`
  (the four `SEAT-COUNT` invariants `tools/ci/docker_smoke.sh` cross-checks at template lines 141-150),
  with the single declared player seated:

  ```json
  "certification": {
    "players": [{"player_id": "scout"}],
    "game_config": {"players": [{"name": "Alpha"}],
                    "num_agents": 1, "minPlayers": 1, "seed": 42,
                    "gridSize": 13, "viewSize": 7,
                    "turnTicks": 12, "taskTurnCap": 11, "taskCount": 5,
                    "taskLadder": ["lavagap", "doorkey", "multiroom", "keycorridor", "babyai"],
                    "maxTurns": 55, "maxTicks": 660, "parTasks": 3,
                    "obstacleCount": 6, "xlandRules": 3, "xlandObjects": 6, "babyaiObjects": 6,
                    "maxActionsPerTurn": 12, "macroPrimitiveCap": 40, "spinTurns": 12,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  A `scout`-only episode is scripted throughout, so 660 ticks is well under a second of sim, but the
  replay is up to 660 ticks ⇒ **up to 66 s of playback**, which the viewer soak needs. Seed 42 is
  asserted by `tests/test_minigrid_engine.nim` to produce a fixture episode in which `scout` solves at
  least one task, opens at least one door and picks up at least one key inside the gauntlet, so the
  smoke replay always exercises the `solved`, `unlock` and `pickup` paths. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 covers start + connect
  grace + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/minigrid-player"`, following
  the starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"minigrid-cartographer","run":"/bin/minigrid-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"cartographer"}},
   {"name":"minigrid-missionfirst","run":"/bin/minigrid-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"missionfirst"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"minigrid-scout","run":"/bin/minigrid-player",
    "env":{"PLAYER_SCRIPTED":"scout","PLAYER_POLICY_LABEL":"scout"}},
   {"name":"minigrid-bumper","run":"/bin/minigrid-player",
    "env":{"PLAYER_SCRIPTED":"bumper","PLAYER_POLICY_LABEL":"bumper"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `scout` and `bumper`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the
  **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps
  the template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `minigrid`,
  `<IMAGE>` → `coworld-minigrid`, `<SEATS>` → **`1`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server)
  and `--soak 10` added to the `viewer_smoke.mjs` invocation (which already passes
  `--strict-text-bounds`). `coworld-release.yml` and `coworld-submit.yml` are the templates, with
  `--timeout-seconds 300` on the certify step. `tools/ci/docker_smoke.sh` and
  `tools/build_replay_viewer.sh` are committed **executable** (mode 100755) — CI asserts the bit and
  invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_minigrid_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in
both debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_minigrid_sim.nim`)
1. `grid and glyphs` — 13 × 13; the whole border ring is `wall`; the glyph table, passability table
   and see-behind table are total over the cell enum and match §The game exactly; the six colours are
   the only colours.
2. `primitives` — each of the seven primitives does exactly what the table says and nothing else:
   `left`/`right` rotate in the MiniGrid order; `forward` moves only into a passable cell; `pickup`
   only when empty-handed and the cell ahead is a non-obstacle key/ball/box; `drop` only into empty
   floor; `toggle` opens/closes/unlocks/opens-a-box per the table; `wait` mutates nothing; an
   inapplicable primitive is a no-op that still costs a tick.
3. `locked doors` — a locked door opens only with a carried key of the **same colour**, the key is
   **not** consumed, and the door thereafter behaves as an ordinary door (can be closed and reopened).
4. `lava and obstacles` — stepping onto lava ends the task `died` on that tick; a `forward` into an
   obstacle ends it `crashed` and the agent does not move; an obstacle never moves into the agent's
   cell; obstacle motion is identical for a given `(seed, taskIndex, tick)` under any agent
   behaviour.
5. `visibility flood` — the 7 × 7 rule of §The game, cell for cell, against a hand-built table of
   twelve fixtures (open room, wall corner, closed door, open door, agent in a corridor, agent facing
   each of the four directions); a closed door blocks, an open door does not; `?` cells never leak
   content into `view`.
6. `known map and staleness` — a cell observed then left keeps its last content and its `seen_tick`;
   a moved obstacle leaves a stale entry; a cell never in `vis` stays `?` for the whole task.
7. `goto BFS` — the path is unique for a given known map (neighbour order east/south/west/north),
   never traverses `?`, lava, a wall, a closed or locked door, an object cell or a known obstacle
   cell; it ends **on** a passable target and **facing** an impassable one; an unreachable target
   yields zero primitives; a 180° `face` is always `right, right`.
8. `task generators` — each of the seven families, over 200 seeds: the layout is well-formed (border
   intact, agent on a free cell, no object on the agent, all required objects present), the mission
   sentence is grammatical and names existing referents, and **the layout is a pure function of
   `(seed, taskIndex)`** — identical under three different agent behaviours.
9. `success predicates` — for each family, a scripted solution reaches `solved` and a deliberate near
   miss does not: `lavagap` off by one cell; `doorkey` at the door without the key; `multiroom` in
   room 2; `keycorridor` holding the key but not the ball; `dynamic` one cell short; `babyai` all
   three instruction kinds including "next to" with the object still carried (must NOT count);
   `xland` with only `P0` made.
10. `subgoals` — each family awards its three named credits exactly once, in order, never revoked;
    a solved task ends with all three; `progressTotal ≤ 15`.
11. `xland rules` — the sampler always produces a chained triple (`P0 + P1 -> GOAL`) with distinct
    products absent at the start; at most one production fires per tick; the scan order
    `(y, x)` then east/south/west/north is deterministic; a carried object never fires a rule; the
    product lands in the lower-`(y, x)` cell.
12. `turn and tick order` — the numbered resolution order of §The game is exercised end to end: the
    queue empties into `wait`; a finished task breaks the tick loop; the next task starts on the next
    turn; skipped ticks are never counted in `taskTicks`.
13. `scoring` — `scores[0] == 100_000×tasksSolved + 1_000×progressTotal + 10×speedTotal` over 500
    randomised end states; the two lexicographic dominance bounds hold (`15_500 < 100_000` and
    `500 < 1_000`); the maximum is `515_500`; the minimum is `0`; `win[0]` is
    `tasksSolved >= parTasks`; `winner` is `0` when `win[0]` and `null` otherwise.
14. `end conditions` — `gauntletComplete`, `turnCap`, a forced wall-clock stop and a forced fault each
    produce the right `endRule` and the right episode `reason`; a wall-clock stop mid-gauntlet marks
    every unstarted task `unreached` with zero turns, zero ticks and zero progress, and still scores
    the tasks that ran.
15. `no floating point in the sim` — a source grep over
    `src/minigrid/{sim,grid,tasks,agent,xland,driver,baselines}.nim` finds no `float`, `/`, `sqrt` or
    float literal.
16. `tick budget` — 660 ticks of a full `xland` episode complete in < 1 s in a release build.

**Bounded orders / legality on the scripted baselines** (`tests/test_minigrid_driver.nim`)
17. `baselines are bounded` — for 300 pseudo-random world states (every family, every variant, varied
    known maps, carried and empty-handed, adjacent to lava and to obstacles) and for **both** `scout`
    and `bumper`: the reply has at most 12 actions, every `do` is in the enum, `goto` targets are
    inside 0…12, `face` dirs are in the enum, `say` and `notes` are empty, and the serialised
    directive is ≤ 1024 bytes. A baseline that ever proposes an illegal or unbounded action fails the
    build.
18. `baselines never suicide` — over the same states, neither baseline ever emits a plan whose
    deterministic expansion steps onto a **known** lava cell or `forward`s into a **known** obstacle
    cell; `scout`'s BFS never routes through `?`.
19. `driver never produces an illegal primitive` — over the same states, every expanded queue is ≤ 12
    primitives, every entry is one of the seven, macros expand to at most `macroPrimitiveCap`, and an
    empty queue yields `wait`, never nothing.
20. `fallback is the scout proc` — the decision engine's fallback path and the `scout` baseline
    resolve to the same proc, so they cannot drift.
21. `reply validation` — the validator accepts the schema, **drops** (never rewrites) an invalid
    action, clamps `goto` coordinates, lower-cases `do`, case-folds `dir`, accepts a `say`-only reply,
    rejects a non-object, truncates `say`/`notes` on **rune** boundaries at 140/300 with 4-byte emoji
    sitting exactly on the boundary, caps the read at 4096 bytes, caps `actions` at 12, and reports
    `truncated` / `dropped` / `unreachable` back accurately.
22. `baseline tuning is the swept pick` — the shipped `frontierAdjacencyWeight` / `spinTurns` /
    tie-break rule equal `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern;
    `ci.yml` re-runs the sweep with `--check`).
23. `scout beats bumper` — over 100 seeds of `gauntlet`, `scout` solves strictly more tasks in total
    than `bumper`, and `bumper` solves at least one — the two controls are genuinely different
    controllers and neither is a zero.

**End-to-end episode writing a replay** (`tests/test_minigrid_engine.nim`)
24. `episode writes artifacts` — run a real one-seat episode (`gauntlet`, scripted, no API key so the
    LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the
    `.replay` are written, `reason == "complete"`, `scores` agree with the formula, the four results
    identities of §Server hold, and the results key set equals the manifest's `results_schema` key set
    **exactly**.
25. `the cert seed is interesting` — seed 42 on `gauntlet` yields at least one solved task, at least
    one `unlock` and at least one `pickup` inside 660 ticks, so the CI smoke replay always exercises
    those paths.
26. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure
    payload; the server refuses to start the game (loudly) when the joined seat has no register
    record.
27. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete`, not `deadline`, and the matching record names the turn.

**Replay** (`tests/test_minigrid_replay.nim`)
28. `record then re-derive, every end reason` — for `gauntletComplete`, `turnCap`, `wallClock` **and**
    `fault`, record an episode and re-derive it from the bytes; assert identical hashes at every tick
    **including the stop tick** (the particle-worlds scar).
29. `replay is self-sufficient` — the bytes alone yield the seat's real name, its alias, the policy
    kind, the full config (every constant in §Server's config-JSON row), the seed, the variant, the
    task ladder, every plan record, every chat record and the result; and re-simulating from them
    reproduces every layout and every mission sentence with no fetch.
30. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports `protocol ==
    "minigrid/v1"`.
31. `determinism from the replay alone` — re-simulate from the replay's seed and plan records on a
    fresh sim; identical final tick, tasks solved, progress totals and per-tick `gameHash`.
32. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept.

**Manifest** (`tests/test_minigrid_manifest.nim`)
33. `manifest pins` — `num_agents == 1` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens`
    in any `game_config`; `len(player) == 1` and that player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 1`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 660`;
    `attempt1Ms + retryMs ≤ turnBudgetMs` and both are whole seconds; `maxTurns ==
    taskCount × taskTurnCap` and `maxTicks == maxTurns × turnTicks`; `game.name` equals the slug and
    the secret URI's namespace; **and every variant's `game_config` actually constructs a valid
    `GameConfig`, generates all five of its tasks, and produces the ladder, the missions and the
    55-turn schedule this note claims** (the collab-cooking 0.1.1 scar: test every variant, not just
    the fixture).
34. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_minigrid_viewer.nim`, static assertions in the `test` job)
35. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, pinned as a literal.
36. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker (`replay_broadcast.html:4344`) and only appends after it;
    `broadcast_core.js`'s kept procs are byte-identical to the starter's, `pushFeed`'s signature
    included.
37. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (`replay_broadcast.html:1635`, the tandem hoisting trap); the beat
    builder is `mgBeat`, never `markBeat`.
38. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{taskstart, solved, failed, unlock, produce, fallback, end}`.
39. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()`
    sets `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the
    band; the five `.tiny` rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`,
    `#zoom-*`, `#povBadge`, `#fpv-hp`, `#fpv-gear`, `#fpv-map*`) appear nowhere, while the kept
    `#fpv`, `#fpv-canvas`, `#fpv-name`, `#fpv-cap` and `#fpv-grip` are all present.
40. `endcard labels` — `tests/test_minigrid_endcard_labels.nim`: zero matches for the forbidden
    paintbot vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
41. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
42. `events are the closed enum` — `tests/test_minigrid_events.nim`: the set of kinds `stepEvents` can
    emit equals exactly the eighteen listed in §Server, and every kind used by the appended game block
    is in that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**
43. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded
    as the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm
    module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the
    bridge `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays on.
44. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, the CI replay's seat plays scripted and emits **no `say` at all**, so the
    smoke replay can never exercise the feed's narration path (the cogchemists 2026-08-24 scar). The
    fixture **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only
    the wasm entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) —
    driving the real page with a full-cap 140-rune `say`, a full-cap mission sentence, a fully fogged
    board, an `xland` `produce` banner, all five task-pip states and a failed-by-lava endcard, at
    several canvas widths including 360 px.
45. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **Any MiniGrid, BabyAI or XLand-MiniGrid dependency, and bit-exactness with any of them.** Decided
  as a scoping rail before design and recorded in `docs/PORTING-MINIGRID.md`: no upstream code is
  vendored, no upstream numbers are claimed as reproduced, and no score from this coworld is
  comparable to a published benchmark number. This coworld implements the problem, not the package.
- **`ObstructedMaze`, and the rest of the MiniGrid registry.** The idea names six families and v1
  ships five of them plus BabyAI and XLand; `ObstructedMaze` — keys hidden inside boxes behind
  blocked doors — is the one that needs a maze generator with a solvability proof and more than 132
  ticks to solve, so it waits. Also out: `Empty`, `FourRooms`, `Fetch`, `GoToDoor`, `RedBlueDoors`,
  `Memory`, `Unlock`, `BlockedUnlockPickup`, `Playground`, and every `-16x16`/`-N6` size class.
- **Seat counts other than 1, and board sizes other than 13 × 13.** `num_agents` is fixed at 1 in
  every variant and in the cert fixture; a multi-agent gridworld is a different coworld (and the
  fleet already has several). A second board size would fork the viewer's layout arithmetic and every
  generator's bounds for no gain the idea asks for.
- **The full BabyAI instruction grammar.** v1 ships three instruction kinds (`go to`, `pick up`, `put
  next to`) over unique referents. BabyAI's `and`/`then` compositions, `open the door after you`,
  relative descriptors ("the ball on your left"), and ambiguous referents needing disambiguation are
  all out — each multiplies the success predicate, and none of them changes what the LLM ladder
  measures at this stage.
- **XLand's full rule DSL.** v1 ships three chained two-input production rules per task. XLand's
  larger grammar (n-ary rules, rules conditioned on the agent's inventory or position, "near"/"on"
  predicates, rule sets of tens of rules, and its benchmark's ruleset trees) is out; three chained
  rules is the smallest thing that is genuinely a meta-task rather than a lookup.
- **Per-primitive LLM stepping, and an RL-vector observation.** The seat batches up to twelve
  primitives a turn under a deterministic driver (§Decisions, divergence 4). A per-tick socket
  interface for an RL policy, and a numeric tensor observation to go with it, are what
  `COGAME_EVENTS_URI`'s `Primitive` rows exist to make possible **later**; they are not a v1
  interface.
- **Scoring exploration, travel efficiency or mission-parse accuracy directly.** `taskCellsSeen`,
  `primitivesExecuted`, `doorsOpened`, `objectsPickedUp` and `productionsFired` are measured, recorded
  in `results`, shown on the endcard and drawn in the feed, and deliberately **not** in `scores`
  (§The game). Paying for cells seen would let a policy farm the metric by spinning in an empty room.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, raycast fog, the
  first-person renderer, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, teams, four-team play, shouts, achievements, campaign mode, multi-game
  episodes, the procedural map generator, the map pool, the map editor and mapkit — all deleted, not
  disabled (§Sim module), and none of them return in v1.
