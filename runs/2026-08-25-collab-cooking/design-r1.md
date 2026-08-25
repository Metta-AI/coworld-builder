# Collaborative Cooking — design note (2026-08-25)

Repo: `Metta-AI/cogame-collab-cooking` (public). Coworld/game name `collab_cooking`, slug
`collab-cooking`, page `https://softmax.com/collab-cooking`. In the new repo this note lives at
`docs/plans/2026-08-25-collab-cooking-design.md`.

**Starter: `Metta-AI/coworld-overcogged`** (not mounted; fetched read-only with
`gh api repos/Metta-AI/coworld-overcogged/tarball/main` — the repo is **private**, so a plain
`git clone` with `GH_TOKEN` fails "Repository not found"; phase 20 must use the tarball or an
authenticated `gh repo clone` from a token with access. Read in full: `coworld_manifest.json`,
`Dockerfile`, `player/Dockerfile`, `pyproject.toml`, `README.md`, `AGENTS.md`,
`src/overcogged/game/game.py` (1474 lines), `src/overcogged/classic/{game,map,variants}.py`,
`src/overcogged/coworld/{server.py,live_episode.py,player.py}`, `src/overcogged/coworld/clients/*`,
`src/overcogged/coworld/docs/*`, `src/overcogged/variants/*`, `src/overcogged/missions/*`,
`src/overcogged/agent/overcogged_agent/{policy,obs_parser,entity_map,navigator}.py`,
`src/overcogged/defaults.py`, `tests/*`, `docs/mettagrid/simulator_api.md`.) It is the starter
because the idea pins it: the kitchen — fetch, chop, pot, plate, serve, wash, order tickets, burn
timers, counters you can put an item down on — already exists there as working mettagrid code that
this coworld finishes and extends, and the coworld server/player/protocol under
`src/overcogged/coworld/` is the "existing protocol" the idea names as the policy interface.
**Every convention there holds here unless this note says otherwise.**

Where overcogged is silent or wrong for us, this note names the replacement and the source, once:

- It has **no replay viewer** — no `replay-viewer/`, no wasm, no `static_replay*.js`, no bundle
  hook; its only replay path is a pod (`/client/replay` + `/replay` + `create_replay_app()`)
  serving a `<pre>` JSON dump. That path is **deleted**, and **`Metta-AI/coworld-ctf` (paintbot,
  `/workspace/starters/coworld-ctf`) is the SINGLE starter for all four viewer files** (§Viewer).
- It has **no LLM anything**. The game-side client is a port of
  `/workspace/starters/cogame-factorio/players/llm_player.py` (§Decisions). No *viewer* file comes
  from cogame-factorio; it is read as evidence (a Python coworld on the ctf viewer lineage whose
  wasm module renders a **recorded** replay with no sim in wasm) and as the source of one Python
  transport module.
- It has **no `compose.yaml`, no `coworld_manifest_template.json`, no `.github/workflows`, no
  `tools/ci/`** — those come from coworld-builder `templates/` (§Packaging, §Tests).
- Its manifest is unvalidated and uncertified (`coworld-incomplete`, the README badge says
  `coworld verify: failed`), its `results` are raw mettagrid rewards, its bundled "player" plays
  `noop` forever, and its roster wait is unbounded (`wait_for_all_players=True` with no deadline).
  All four are fixed here.

**Every non-optional pin from `playbooks/make-coworld.md` §Phase 0, and where it is satisfied:**

| pin | how |
|---|---|
| starter by game shape | `coworld-overcogged` — the idea pins it and the kitchen already exists there as code (above); the *viewer* files, which it does not have, come from `coworld-ctf` (§Viewer) |
| public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-collab-cooking`, created public by phase 20 (public is a certification prerequisite — `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` vs `PLAYER_SCRIPTED=brigade\|runner\|passer\|courier`, one image `{{COLLAB_COOKING_IMAGE}}`, one entrypoint `/bin/collab-cooking-player` (§Decisions, §Packaging) |
| static wasm replay viewer, never a pod | `"replay_viewer": {"bundle":"static-replay-viewer"}` + `tools/build_replay_viewer.sh`; `/client/replay`, `/replay` and `create_replay_app()` deleted (§Viewer) |
| real art, starter chrome verbatim | 24 px kitchen sprites baked with `pixie` at module start, no placeholders; `chrome_common.js` byte-for-byte and `replay_broadcast.html` plus an appended game block (§Viewer) |
| two name spaces | `Cog-A`…`Cog-D` in-game by seeded permutation; real policy names only in the replay, results and viewer (§Two name spaces) |
| degrade-never-hang, inside 60 % of 1200 s | worst case 325 s to written artifacts = 27 %; guard at 720 s anchored at process start; every wait bounded (§Decisions) |
| `num_agents` in every variant and the cert fixture | 4, in all eight variants, `certification.game_config`, `config_schema` (4..4), `len(certification.players)` and `SMOKE_SEATS` (§Packaging) |
| both champions `PLAYER_PROMPT`, ≥ 1 (normally 2) scripted fillers, filler versions ≠ champion versions | `tools/ci/policies.json`: `collab-cooking-expo` (daveey) and `collab-cooking-linecook` (daveey-1) are prompts; `collab-cooking-brigade` and `collab-cooking-passer` are the fillers (§Packaging) |

---

**Source idea (verbatim):**

```
EXTENSION of Metta-AI/coworld-overcogged — the standalone Overcooked-style kitchen-coordination game already exists but is marked incomplete (manifest not validated, not certified). Task = finish it, then add Melting Pot's layouts as map variants: asymmetric advantages, counter circuit, cramped room, crowded (9 cogs, one choke point), figure eight, forced, ring, plus the default. Fully cooperative: fetch, chop, pot, plate, deliver; team score = dishes served. Each layout isolates one coordination problem (task allocation, item handoff over counters, traffic discipline, 9-seat scale).

Seats: 2 (most layouts) / 9 (crowded)
Motive: pure common interest
Policy interface: Overcogged's existing protocol
Integrity (anti-collusion): cooperative — score by cross-play with scripted partners (Melting Pot style), not self-copies only.
Replay plan: dish ticker + collision heat-map.

Absorbed: the standalone MP Collaborative Cooking idea. Source: meltingpot collaborative_cooking__*; JaxMARL Overcooked/OvercookedV2; github.com/Metta-AI/coworld-overcogged.
```

---

## The game

Four cogs share one kitchen for 900 ticks. Tickets arrive on an order board every 18 ticks and
expire 50 ticks later. A dish is a chain of single-item errands: fetch a vegetable or a piece of
meat, chop it (3 ticks at the board), load a pot (10 ticks to cook, 14 more and it burns) or a
fryer (8 / 11), pick up a clean plate, plate the dish, walk it to the pass, and serve it against a
live ticket; the plate comes back dirty and somebody has to wash it (3 ticks at the sink). **A cog
can carry exactly one thing.** Counters are walls you can put your one thing down on and someone
else can pick it up — so the whole kitchen is a hand-off network, and in one of the eight rooms
that is the *only* way anything moves.

**Team score = dishes served.** Nothing else scores. Burning a pot, letting a ticket expire, or
standing in the doorway costs dishes and only dishes.

### Seats

**`num_agents` = 4. One number, everywhere: every manifest variant's `game_config`,
`certification.game_config`, `config_schema.properties.num_agents` (`minimum: 4, maximum: 4`),
`len(certification.players)`, and `SMOKE_SEATS=4` in `tools/ci/docker_smoke.sh`.**

The idea says 2 for most layouts and 9 for `crowded`; a coworld gets one number, so 4 is the
number and here is why:

1. **The starter is already authored at 4.** `missions/basic.py` is
   `OvercookedGame.create(num_agents=4, max_steps=300)`, and the shipped scripted brain deals
   exactly four roles at four cogs — `_assign_role` gives `prep`, `cook`, `server`, `all_rounder`
   for slots 0–3 (`agent/overcogged_agent/policy.py:871`). Task allocation, the first coordination
   problem the idea names, is a real four-way assignment at 4 and a coin flip at 2.
2. **The cert fixture needs one slot per declared bundled player.** A manifest that declares four
   runnables and seats only two fails `players_missing` (raid 0.1.2 → 0.1.3). Four seats seat all
   four bundled players exactly once.
3. **Rate discipline.** Four prompt seats at one batch per ≥ 10 s wall = ≤ 24 requests/minute,
   inside the Bedrock sidecar's 30 req/min-per-episode cap (raid, 2026-08-23). Nine would be 54.
4. **Nine does not fit the rooms.** Melting Pot's kitchens are 5–9 tiles across; `cramped_room`
   with nine cogs is not a coordination problem, it is a deadlock. The idea's "9-seat scale" claim
   is the one thing that does not survive at a single seat count, and it is deferred explicitly
   (§Out of scope, item 1) rather than half-built.

Every Melting Pot layout named in the idea still ships (§The eight kitchens): seven of them are
2-cog rooms widened by one aisle so four cogs fit and the room's *lesson* is unchanged, and
`crowded` ships as the 4-cog rendering of its one-choke-point idea — same finding (traffic through
a single tile), a quarter of the crowd.

### The eight kitchens

One `game_config.layout` value each, one manifest variant each, `num_agents: 4` in all of them.
Every kitchen is a fixed hand-authored ASCII grid — **not** a procedural hub — built with
`mettagrid.map_builder.ascii.AsciiMapBuilderConfig`, which the starter already uses in
`src/overcogged/classic/map.py`. That is deliberate: `CompoundConfig.layout` is a `Literal` in the
external `mettagrid` package (`"default" | "tight" | "cramped_room" | "service_pass_room"`) and we
are not going to add enum members to a dependency to draw a kitchen.

Character map (`CHAR_TO_MAP_NAME`, the only one):

| char | object | char | object |
|---|---|---|---|
| `#` | `wall` — a **counter**: `counter_config()` gives every wall deposit/withdraw handlers and a 1-item limit | `.` | `empty` |
| `V` | `veg_station` | `M` | `meat_station` |
| `L` | `plate_station` (clean plates) | `X` | `chopping_station` |
| `O` | `cooking_station` (the pot) | `F` | `fryer_station` |
| `S` | `serving_station` (the pass) | `W` | `wash_station` (the sink) |
| `B` | `order_board` | `@` | `agent.agent` (a spawn) |

**Every kitchen contains exactly one of each of the nine stations and exactly four spawns**, so
the only thing that differs between variants is geometry. A test asserts it (§Tests, 1).

**`open-kitchen`** — the idea's "default". 13×9, one counter island in the middle; everything is
reachable both ways round. The control case: no forced hand-off, no choke.

```
#####V#M#####
#...........#
#..@.....@..#
#B..#####..X#
#...#####...#
#L..#####..O#
#..@.....@..#
#...........#
#####W#S#F###
```

**`cramped`** — Melting Pot `cramped_room`. 9×7, a 7×5 interior for four cogs; every station is on
a wall and two cogs cannot pass without one giving way. Isolates: *personal space*, and it is the
certification/smoke fixture because it is the smallest.

```
###V#M###
#...@...#
#B.....X#
#.@...@.#
#L.....O#
#...@...#
###W#S#F#
```

**`forced`** — Melting Pot `forced` (forced coordination). 13×9, **two sealed halves**: the open
tiles form two components with no path between them (a test asserts exactly two). Left has veg,
meat, chopping board, plates and the sink; right has the pot, the fryer and the pass. Six divider
cells (`(1,6) (2,6) (3,6) (5,6) (6,6) (7,6)`) are counters with an open tile on both sides — the
**only** way an item crosses. The order board sits **in** the divider at `(4,6)`, adjacent to both
halves, so neither side is blind to the tickets. Isolates: *item hand-off over counters*.

```
##V#M########
#.....#.....#
#..@..#..@..#
#X....#....O#
#.....B.....#
#L....#....F#
#..@..#..@..#
#.....#.....#
####W####S###
```

**`crowded`** — Melting Pot `crowded`, rendered at four seats. 11×7, the same split as `forced`
except the divider has **exactly one gap**, the single cell `(3,5)`; prep is left, cooking and the
pass are right, so every ingredient and every plate goes through that one tile. Isolates: *traffic
through a choke point* (the idea's "one choke point").

```
##V#M##B###
#.@..#..@.#
#X...#...O#
#.........#
#L...#...F#
#.@..#..@.#
##W####S###
```

**`asymmetric`** — Melting Pot `asymmetric_advantages`. 15×9, a 3-wide central block with aisles
only along the top and bottom rows. The right half owns the pot, the fryer **and** the pass — it
can cook and serve without walking; the left half owns veg, meat, the board, the chopping board,
plates and the sink. The halves are connected, so this is not `forced`; it is unequal, which is the
point. Isolates: *task allocation under unequal access*.

```
###V#M#####B###
#.............#
#..@..###..@..#
#X....###....O#
#.....###....F#
#L....###....S#
#..@..###..@..#
#.............#
#####W#########
```

**`circuit`** — Melting Pot `counter_circuit`. 15×7, a 7-cell counter island down the middle of a
loop: walking round it is 12 steps, putting the item on it and letting the other side take it is 2.
Isolates: *when to hand off instead of walk*.

```
###V#M###B#####
#.............#
#..@.......@..#
#X..#######..O#
#..@.......@..#
#.............#
####L###W#S#F##
```

**`ring`** — Melting Pot `ring`. 11×9, a solid 7×5 block with a **one-tile-wide corridor** all the
way round. Two cogs meeting head-on cannot pass; one must back into a corner. Isolates: *traffic
discipline* (this is what the plan field `yield_to` exists for).

```
###V#M#B###
#..@...@..#
#.#######.#
X.#######.O
#.#######.#
L.#######.F
#.#######.#
#..@...@..#
###W#S#####
```

**`figure-eight`** — Melting Pot `figure_eight`. 15×9, two one-tile loops sharing the central
column 7 (rows 2–6). Everything crossing between loops fights for the same spine. Isolates:
*right of way on a shared spine*.

```
####V#M#B######
#.@.........@.#
#.#####.#####.#
X.#####.#####.O
#.#####.#####.#
L.#####.#####.F
#.#####.#####.#
#.@.........@.#
####W###S######
```

### Rules, complete

All of this is overcogged's `src/overcogged/game/game.py`, run with the `full` mechanics set
(`queue_orders` + `salad_recipe` + `soup_recipe` + `fries_recipe` + `dishwashing` + `soup_burn` +
`fries_burn` — `variants/mechanics.py:FullMechanicsVariant`). The numbers below are the shipped
defaults and are **not** retuned in v1; they are stated because a builder must be able to check
them without opening the starter.

**Carrying.** An agent's inventory is limited to **one** unit total across
`veg, meat, chopped_veg, chopped_meat, clean_plate, dirty_plate, dish_salad, dish_soup, dish_fries`
(`ResourceLimitsConfig(base=1, max=1)`). A counter (`wall`) has the same limit — one item per
counter cell. `deposit` fires when the actor holds something and the counter is empty; `withdraw`
fires when the actor is empty-handed and the counter holds something. Using a station is *moving
into it*: the move is blocked, and the object's `on_use_handler` runs `firstMatch` over its
handlers.

**Stations.**

- `veg_station` / `meat_station` / `plate_station`: an empty-handed cog gets 1 `veg` / `meat` /
  `clean_plate`.
- `chopping_station`: put `veg` in → `chop_veg_progress = 1`; each further use +1; at
  `chop_ticks - 1 = 2` the next use yields `chopped_veg` to the actor and clears the board
  (3 uses total). Same for `meat`. A cog holding `clean_plate` at a board holding `chopped_veg`
  makes `dish_salad`. Chopped items can be stashed on and taken from the board.
- `cooking_station` (pot): `chopped_veg` + `chopped_meat` in the pot (in either order, or one from
  the actor and one already loaded) starts a soup — `pot_timer = soup_cook_ticks = 10`, ticking
  down once per tick; at 0 the pot goes `ready`; `ready` ages, and at
  `soup_burn_ticks = 14` it becomes `burned` and must be cleared by one use. A cog holding
  `clean_plate` at a ready pot gets `dish_soup`.
- `fryer_station`: `chopped_veg` in → `fries_cook_ticks = 8` → ready → burns at
  `fries_burn_ticks = 11`; `clean_plate` at a ready fryer → `dish_fries`.
- `serving_station` (the pass): holding `dish_<recipe>` with a **live ticket** for that recipe on
  the board serves it — the dish becomes `dirty_plate` in the cog's hands, the ticket and its queue
  counter clear, and the actor's `orders_served` stat increments. With no live ticket for that
  recipe nothing happens.
- `wash_station` (sink): `dirty_plate` in → 3 uses → `clean_plate` to the third user.
- `order_board`: holds the ticket resources and the three queue counters
  (`queue_salad/queue_soup/queue_fries`, cap `order_queue_max = 8`). It has no handlers; it is
  read by looking at it.

**Tickets.** `build_ticket_specs` lays the whole episode's schedule down at config time:
first arrival at tick 0, then every `ticket_interarrival = 18` ticks, recipes cycling
`soup, salad, soup, fries, salad`, each expiring `ticket_deadline = 50` ticks after arrival (or at
`max_steps`). At `max_steps = 900` that is **50 tickets per episode**, of which at most 8 can be
live at once. An arrival is skipped if 8 are already live; an expiry writes `orders_expired`.

**Rewards.** `_agent_config()` is changed to exactly one term:
`{"served": reward(stat("orders_served"), weight=1.0)}`. The starter's soup/fries bonuses (0.2 /
0.15) and its shared expiry penalty (−0.05) are **deleted**, because the rankable quantity has to
*be* dishes and not a shaped proxy of dishes. Consequence, and this is the whole reason for the
change: `sim.episode_rewards[i]` is now exactly the integer count of dishes seat *i* carried to the
pass, and `sum(sim.episode_rewards)` is exactly the team's dish count — both read through the
existing `LiveMettaGridEpisode.scores()`, with no new engine API.

### Turn/tick structure — the exact resolution order

One tick = one simultaneous action from every seat. The server executes exactly this order; ties
everywhere resolve by ascending slot. Nothing in this list is order-independent, so this list is
the specification.

1. **Ingest.** For each slot take `latest_policy_actions[slot]`. A seat whose latest action does
   not carry `request_id == f"step-{step}"` contributes `noop`
   (`live_episode.py:_applied_action`, unchanged). A disconnected seat contributes `noop`.
2. **Apply.** `sim.agent(slot).set_action(name)` for all four slots, ascending slot.
3. **Step the engine.** `sim.step()`. Inside mettagrid, in its own fixed order: movement resolves
   (a move into a wall, a station or an occupied tile fails and the agent stays put), then the
   `on_use_handler` of the object a blocked mover walked into runs `firstMatch`, then the
   timestep's `EventConfig`s fire — ticket arrivals and expiries at their scheduled timesteps,
   `soup_cook_timer_tick` / `soup_finish_cook` / `soup_ready_age_tick` / `soup_burn`, the same four
   for the fryer, then `queue_pressure_tick`. This is the engine's order and we do not reorder it;
   we depend on it only through what step 4 reads.
4. **Read state.** `sim.grid_objects()` for every object's position and inventory,
   `sim.agent(i).inventory` for each cog's carried item, `sim.agent(i).last_action_success`,
   `sim.episode_rewards` for `delivered[]`. (`docs/mettagrid/simulator_api.md` — all four are
   documented public API.)
5. **Derive events** by diffing this state against the previous tick's, in the fixed order
   `order_arrive, order_expire, pickup, deposit, chop_start, chop_done, pot_load, pot_start,
   pot_ready, pot_burn, pot_clear, fry_start, fry_ready, fry_burn, fry_clear, plate_up, serve,
   wash_start, wash_done, blocked`. A `blocked` event is written for a seat whose action was a
   `move_*` and whose `last_action_success` is false; it carries `by: "cog"` when another agent
   occupies the target tile and `by: "wall"` otherwise, and increments `heat[tile]` — the collision
   heat-map the idea asks for.
6. **Record.** Append the tick record to the in-memory replay (§Replay bytes).
7. **Plan boundary.** If `step % plan_interval_steps == 0`, no batch is in flight, and at least
   `min_plan_interval_seconds` of wall clock has passed since the last batch went out, build one
   observation per prompt seat and dispatch **one parallel batch** (§Decisions). The tick loop does
   not wait for it.
8. **Deliver plans.** Any batch result that has landed since the last tick is sent to its seat as
   a `plan` message and written as a `plan` event.
9. **Observe.** Send every connected seat its `observation` message, then wait for all connected
   seats' actions for this step up to `policy_action_timeout_seconds = 0.30`, then sleep the
   remainder of `step_seconds`.
10. **Deadline guard.** If `monotonic() - PROCESS_START >= play_budget_fraction × episode_timeout_seconds`
    (0.6 × 1200 = **720 s**), settle immediately with `reason: "deadline"`.
11. **End.** If `step + 1 == max_steps` or `sim.is_done()`, settle with `reason: "complete"`.

### Scoring, sign, and what the league ranks by

```
delivered[i]      = sim.episode_rewards[i]              # integer: dishes seat i served
dishes            = Σ_i delivered[i]                    # the team score: dishes served
results.scores[i] = dishes + 0.01 × delivered[i]        # what the league ranks by
```

**Sign: higher is better; no term is ever negative.** Expired orders and burned pots subtract
nothing — they cost dishes, which is the only currency.

The first term is the whole game and it is identical for all four seats: **pure common interest**,
exactly as the idea pins it. The second term exists so the ladder is not a draw machine, and it is
deliberately an epsilon: the ticket schedule caps `delivered[i] ≤ 50`, so the epsilon term is
≤ 0.5 — **strictly less than one dish**. The ordering is therefore lexicographic (team dishes
first, own deliveries only as a tie-break), and a cog that hogs the walk to the pass to farm the
epsilon loses whole dishes of throughput to gain hundredths. A test asserts the bound
(§Tests, 3).

**How seats are filled (the idea's integrity note).** Scoring is Melting-Pot cross-play, not
self-copies: **the certification fixture is 1 prompt seat + 3 scripted partner seats**, and the
league division is configured with **two scripted fillers** alongside the two prompt champions
(§Packaging), so a round-robin at four seats seats a champion with at least one scripted partner in
the great majority of episodes and never seats four copies of the same policy. The game records
what it was given: `results.seat_kinds = ["prompt", "scripted:brigade", …]` and
`results.cross_play = true` when at least one prompt seat and at least one scripted seat sat
together. An episode in which both champions sit is a genuine draw on the first term and is
decided, if at all, by the epsilon.

### End conditions and the legal `results.reason` values

Exactly three values are legal and the game emits nothing else:

- **`complete`** — 900 ticks ran (or `sim.is_done()`). The normal path.
- **`deadline`** — the guard in step 10 fired. The episode is scored exactly as it stands at that
  tick, a `deadline` event is written, artifacts are written, and the process exits **0**. Scores
  are real, not zeroed, so a deadline episode is still rankable. With the arithmetic in §Decisions
  it should never fire.
- **`no_players`** — **zero** seats connected within `player_connect_timeout_seconds = 120`.
  `results.json` is written with all-zero scores and the process exits **0**. This is a change from
  the starter, whose `wait_for_all_players=True` with no deadline waits forever.

If *some* seats connect the episode runs with the seats it has: absent seats noop every tick, score
0, and are flagged `disconnected: true` in the replay and the results. If every seat disconnects
mid-episode the remaining ticks run out with all-noop actions at the pacing floor and the reason is
still `complete`. The game never exits non-zero on a player-side problem and never waits on a
player socket without a bound.

### Per-seat observation: exactly what is visible and what is hidden

Two layers, and the second is composed from the first so a prompt seat can never see further than
a scripted one.

**Wire layer (unchanged from the starter, this is the idea's "existing protocol").** Every tick
each seat gets `{"type":"observation","protocol":"collab-cooking.player.v1","slot":N,"step":T,
"observation":[[…],…],"scores":[…],"control_state":{…}}` — the raw mettagrid token array for that
agent, i.e. its `obs_width × obs_height` window (the engine default, 11×11) centred on the cog,
plus its own inventory tokens and the global tokens `local_position` and `last_action_move` that
`GlobalObsConfig` enables. `player_config` on connect carries `slot`, `num_agents`,
`action_names`, `observation_shape`, `policy_env` and the feature/tag tables.

**Visible:** terrain and objects inside the window (counters, each station **and its inventory** —
so a cog next to the pot sees `pot_soup_ready`, a cog next to the board reads the three queue
counters and the live ticket resources); other cogs inside the window as agents (position only);
its own inventory; its own local position; its own last move.

**Hidden:** everything outside the 11×11 window — which, on a 15×9 kitchen, is most of the far
half and, in `forced` and `crowded`, usually the whole other side; other cogs' inventories unless
their tile is in the window (mettagrid publishes an agent's inventory tokens only at its own
centre); the seed; the ticket schedule (a seat learns tickets only by looking at the board); other
seats' plans, prompts and private notes; and **every real policy name** (§Two name spaces).

**Prompt layer.** For a prompt seat the game renders that seat's *own* window into text using the
starter's own `ObsParser` + `EntityMap` (`agent/overcogged_agent/obs_parser.py`,
`entity_map.py` — kept byte-for-byte), i.e. the same world model the scripted brain builds for that
seat, including its staleness (`EntityMap` remembers the last time each object was seen and the
prompt prints `seen 42 ticks ago`). The only thing in the prompt that is not in the window is the
**team radio** — the other seats' `say` lines from the previous plan turn, which are broadcast by
construction — and the seat's own private `note`.

---

## Decisions: LLM with scripted fallback

### Where the LLM lives, and how an LLM plays a 0.2 s tick loop

The pin (SPEC §Design pins) is that both champions are LLM **prompt** policies env-switched against
a scripted baseline in the same image. overcogged's policy interface is a per-tick websocket that
wants an action every `step_seconds`. Both facts are real; here is how they hold together, and this
is a decision, not an option.

**Two clocks.** The LLM decides a **shift order** every `plan_interval_steps = 50` ticks
(≈ 10 s wall); a scripted **executor** in the player container turns that order into one legal
mettagrid action per tick. The plan chooses *which job, which recipe, which half of the room, who
to hand to, who to yield to*; the executor chooses *which tile next*. That is exactly the division
the four coordination problems live on.

**The LLM lives in the game container**, not the player container — bullwhip's/commons-family's
split, for four load-bearing reasons: (1) "all seats' calls go out as ONE parallel batch per turn"
is satisfiable only by the party that owns the turn boundary; (2) retry-once-then-fall-back must be
enforced by that same party or a hung player pod becomes a silently passing seat; (3) one container
needs the secret instead of four, which matches `ANTHROPIC_API_KEY_URI` on the game runnable
(hive, 2026-08-23); (4) the scripted baselines are pure `observation → action` functions that
already run in either process. Because the LLM is game-side, the policy entries in
`tools/ci/policies.json` deliberately **do not** set `USE_BEDROCK` — that flag gates the *player*
pod's Bedrock sidecar (cogolf, 2026-08-24) and buys a game-side client nothing; the game's own
transport ladder is §Transport below.

The player container is still the policy and still speaks the starter's protocol: it registers
`PLAYER_PROMPT` or `PLAYER_SCRIPTED=<name>`, receives the same per-tick `observation` messages as
before, and answers with the same `action` messages. One added server→client message (`plan`) and
one added client→server message (`register`) — nothing else changes on the wire.

### The LLM policy

**Transport.** `src/collab_cooking/coworld/llm.py` is a port of
`/workspace/starters/cogame-factorio/players/llm_player.py`, moved server-side, keeping its ladder
verbatim: `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `AWS_BEARER_TOKEN_BEDROCK` present → the minimal
Bedrock `InvokeModel` HTTP client; else `ANTHROPIC_API_KEY`; else read `ANTHROPIC_API_KEY_URI`
(the `secret://` URI the platform mounts) and use that; else **disabled — zero network calls for
the whole episode**. Model `claude-haiku-4-5-20251001` (Bedrock id
`us.anthropic.claude-haiku-4-5-20251001-v1:0`), `max_tokens = 900` (400 truncates — playbook
§Phase 1), `output_config.effort` never sent, and the system prompt demands a reply that **begins
with `{`** because Haiku answers prose-first otherwise.

**Batch.** On a plan boundary the game builds one observation per prompt seat and issues all of
them together on a `concurrent.futures.ThreadPoolExecutor(max_workers=4)` — **one parallel batch
per turn**. The tick loop never blocks on it: cogs keep executing their previous plan (or their
fallback baseline) while the batch is in flight, and a plan that lands late is delivered on the
next tick after it arrives. The batch deadline is `plan_timeout_seconds = 12`.

**Per-turn wall-clock budget, said out loud.**

- A tick costs `step_seconds = 0.20` plus the action wait (the executor answers in ~2–5 ms, and the
  loop stops waiting the moment all connected seats have answered), so ≈ **0.205 s/tick**.
- Play = 900 × 0.205 = **185 s**. Roster wait ≤ **120 s**. Shutdown grace **20 s**.
  Worst case to written artifacts = **325 s = 27 % of the 1200 s `episodeTimeoutSeconds`**, inside
  the 60 % (720 s) rule with room to spare. The guard at 720 s (anchored at **process start**, so
  the connect wait is inside the budget, not on top of it) is a backstop that should never fire.
- A plan turn is one batch of ≤ 4 requests every `max(plan_interval_steps × 0.205,
  min_plan_interval_seconds) = max(10.25, 10.0) = 10.25 s` → **18 plan turns per episode**,
  ≤ **23.4 requests/minute**, under the sidecar's 30 req/min-per-episode cap. On top of that the
  game enforces a rolling `llm_max_requests_per_minute = 26` budget shared by all seats; retries
  draw from it, and a request that would exceed it is not made — the seat plays its fallback for
  that turn with `cause: "rate_budget"`.

**System prompt** (constant per episode; the seat's `PLAYER_PROMPT` is appended verbatim as a
`STANDING ORDERS` block truncated to 1200 runes):

```
You are {alias}, one of 4 cogs running a kitchen together for {max_steps} ticks.
Orders arrive on the board every 18 ticks and expire 50 ticks later. A dish is a chain:
fetch veg or meat -> chop it (3 uses) -> pot it (soup: chopped veg + chopped meat, 10 ticks,
burns 14 ticks after it is ready) or fry it (chopped veg, 8 ticks, burns after 11) or plate
chopped veg as a salad -> carry it to the pass and serve it against a live ticket -> the plate
comes back dirty and needs 3 uses at the sink.
YOU CAN CARRY EXACTLY ONE THING. Counters (the walls) hold one item each: put your item down
and a team-mate can pick it up. That is often faster than walking round.
Your score and everyone else's is the same number: dishes the team serves. Nothing else scores.
Kitchen: {layout} - {layout_line}
You give one standing order; a controller walks you there tick by tick until your next order,
about 50 ticks from now.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with the character {.
Schema:
{"station":"<one of LEGAL STATIONS>","recipe":"salad|soup|fries|any","zone":"left|right|pass|any",
 "handoff":"<ally alias or none>","yield_to":"<ally alias or none>",
 "say":"<=120 chars","note":"<=200 chars"}
"say" is heard by your team-mates next turn and shown to spectators. "note" is private and is
handed back only to you.
```

`{layout_line}` is one fixed sentence per kitchen ("two sealed halves — nothing crosses except over
the six counter cells in the middle wall", "a one-tile corridor all the way round: two cogs cannot
pass", …).

**User message** — the observation, deterministic, ≤ 2000 characters, every list bounded:

```
TURN 7/18  TICK 350/900  KITCHEN forced  DISHES 9  TICKETS LIVE 3
YOU Cog-C at (5,3) carrying chopped_veg  served 2
TEAM (last seen)
  Cog-A (2,4) 6 ticks ago carrying clean_plate
  Cog-B not seen since tick 210
  Cog-D (3,9) 41 ticks ago carrying nothing
BOARD (seen 12 ticks ago): soup 2, salad 1, fries 0
STATIONS YOU KNOW
  chopping (3,1) 0 ticks ago: veg 2/3
  pot (3,11) 33 ticks ago: cooking, ready in ~4
  fryer (5,11) 33 ticks ago: idle
  pass (8,9) 60 ticks ago
  sink (8,4) 8 ticks ago: idle
COUNTERS HOLDING SOMETHING (<=6): (4,6) chopped_meat, (2,6) clean_plate
BLOCKED LAST TURN: 4 times, mostly at (3,5)
LEGAL STATIONS: veg, meat, chop, plate, sink, board, pass, hold
LAST ORDER: station=chop recipe=soup zone=left handoff=Cog-D -> you chopped 2, handed 1
TEAM RADIO (<=3 lines)
  Cog-A: I'll take the right side, put meat on the middle counter
  Cog-D: pot is ready, need a plate over here
YOUR NOTE: A keeps forgetting plates. Put one on the pass counter early.
STANDING ORDERS: <the seat's PLAYER_PROMPT, truncated to 1200 runes>
```

**`LEGAL STATIONS` is precomputed by the same predicate the validator applies** — the set of
stations reachable from this seat's current tile in this kitchen (BFS over open tiles, so in
`forced` a left-half cog is never offered `pot`, `fryer` or `pass`), plus `hold`. Shipping the
legal set in the observation is what actually stops formal-output fallbacks; prompt drills alone
only halve them (escrow, 2026-08-23).

### Reply schema and character caps

One JSON object. Unknown keys ignored. Extraction takes the first balanced `{…}` span, so leading
or trailing prose is tolerated.

| field | type | cap | invalid → |
|---|---|---|---|
| `station` | enum | **12 chars** | must be a member of `LEGAL STATIONS`; anything else is **illegal** → one retry → fallback |
| `recipe` | enum | **6 chars** | `salad\|soup\|fries\|any`; anything else → `any` |
| `zone` | enum | **6 chars** | `left\|right\|pass\|any`; anything else → `any` |
| `handoff` | string | **8 chars** | an ally alias or `none`; anything else → `none` |
| `yield_to` | string | **8 chars** | an ally alias or `none`; anything else → `none` |
| `say` | free text | **≤ 120 runes** | rune-boundary truncation; broadcast to the team next turn and to spectators |
| `note` | free text | **≤ 200 runes** | rune-boundary truncation; private, echoed back only to this seat, **never written to the replay** |

**Every free-text field is truncated on rune boundaries, never byte boundaries** — a byte-cut
multi-byte rune is exactly what makes replay bytes fail a strict JSON parser while still rendering
in a browser (playbook gotcha). In Python a `str` slice is already a code-point slice, so the
truncator is one helper `truncate_runes(text, cap)` in `coworld/plans.py`, applied to `say`,
`note`, the registered prompt (1200), policy names (48), the engine `talk` string (140, the
engine's own `TalkConfig.max_length`) and every error string that can reach the replay. Artifacts
are written with `ensure_ascii=False` and encoded UTF-8 exactly once.

### What the executor does with a plan

Deterministic, and this is the specification — two implementations must not differ.

1. `station` sets the seat's sub-goal, overriding the brain's own choice until the next plan:
   `veg`→`veg_station`, `meat`→`meat_station`, `chop`→`chopping_station`, `pot`→`cooking_station`,
   `fryer`→`fryer_station`, `plate`→`plate_station`, `pass`→`serving_station`,
   `sink`→`wash_station`, `board`→`order_board`, `hold`→ stand still (`noop`) unless carrying a
   dish, in which case route to the pass. The brain's existing `_route_to_station` does the
   walking (`Navigator` BFS, `reach_adjacent=True`), and its existing unstick rule (4 failed moves
   → explore) is kept unchanged.
2. `recipe` pins `state.recipe_preference` unless `any`, in which case the brain keeps deriving it
   from the board as it does today (`_active_recipe`).
3. `zone` filters target selection: `left` = tiles with `col < width // 2`, `right` =
   `col >= width // 2`, `pass` = counter cells with an open tile on both sides (in `forced`/
   `crowded` the divider; elsewhere the central island), `any` = unrestricted. A goal outside the
   zone is replaced by the nearest in-zone counter, i.e. the cog stages the item instead of
   crossing.
4. `handoff = <alias>`: while carrying, if the named ally is within Chebyshev 3 and a free counter
   cell is cardinally adjacent to both the cog's reachable area and the ally's, deposit there
   instead of walking the item onward.
5. `yield_to = <alias>`: if the named ally is cardinally adjacent and the cog's next step is onto
   the ally's tile, step to the first free perpendicular tile (north, then south, then east, then
   west), else `noop` for that tick. This is the traffic rule `ring` and `figure-eight` exist to
   test.

An unparsed or absent plan means the seat runs its fallback baseline; the executor is never left
without a legal action.

### Scripted baselines (same image, env-switched)

`PLAYER_SCRIPTED=<name>` — four names, all of them the starter's `OvercookedBrain`
(`agent/overcogged_agent/policy.py`) with one parameter changed. They are the starter's code and
their behaviour is not retuned in v1.

- **`brigade` — the default and the fallback** (`fallback_scripted`, default `brigade`). Role =
  `_assign_role(slot, 4)` → slot 0 `prep`, 1 `cook`, 2 `server`, 3 `all_rounder`. Its algorithm,
  as read from the starter: parse the window (`ObsParser`) → update the remembered `EntityMap` →
  if the last 4 moves all failed, run the unstick rule → if holding a dirty plate, commit to the
  sink → if holding a servable dish, go to the pass (via the board if that recipe has no live
  ticket) → otherwise run the role branch (`_server_action` / `_cook_action` / `_prep_action` /
  `_all_rounder_action`), which prioritises: ready-or-burned pot/fryer first, then the queued
  recipe with the deepest queue, then fetching the next missing ingredient → otherwise
  `_recipe_action` for the active recipe → route with `Navigator`, one action per tick, `talk` set
  to the current task label.
- **`runner`** — every seat `all_rounder`: no roles, everyone takes the nearest useful job. The
  no-task-allocation control.
- **`passer`** — `brigade` with `zone` permanently pinned to its own half and `handoff` always on:
  it never crosses the midline and always stages items on the nearest pass counter. The pure
  hand-off partner, and the only baseline that scores well in `forced`.
- **`courier`** — every seat `server`: grab a plate, serve whatever is ready, prep only when
  nothing is. The greedy-serve control; it starves the prep chain, which is the point of having it
  on the ladder.

### Degrade, never hang

| failure | response |
|---|---|
| a seat's LLM call times out (12 s) | **retry once**, that seat only, with the hint `Your last reply was not usable. Reply with ONE JSON object beginning with { and a station from LEGAL STATIONS.` |
| reply is not JSON / has no balanced object | same single retry |
| `station` not in `LEGAL STATIONS` | same single retry |
| retry also fails | that seat plays `fallback_scripted` (`brigade`) until the next plan turn; a `fallback` event with `cause ∈ {timeout, parse, illegal_station, rate_budget, transport, disabled}`; counted in `results.fallbacks[slot]` |
| an unclassified transport failure | logged with its traceback, then the same retry-once-then-fall-back path with `cause: "transport"`. It never escapes the batch: an exception unwinding the tick loop would strand the episode |
| no credentials at all (offline CI, cert without a key) | the client marks itself **disabled at startup and makes zero network calls**; every prompt seat plays `brigade` all episode with `cause: "disabled"`; the episode still finishes `reason: "complete"` |
| the rolling 26 req/min budget is exhausted | the turn is skipped for the seats that cannot be called; `cause: "rate_budget"` |
| a player socket never connects | that seat noops all episode, scores 0, `disconnected: true` in replay and results |
| every seat disconnects mid-episode | remaining ticks run out at the pacing floor with all-noop actions; `reason: "complete"` |
| zero seats connect within 120 s | `reason: "no_players"`, artifacts written, exit **0** |
| the wall-clock guard fires | `reason: "deadline"`, artifacts written, exit **0** |
| the episode ends | artifacts are written, then `/healthz` and `/global` keep answering for a **20 s shutdown grace** before `quit(0)` — the certification runner pings `/global` *after* the player pods start and a fast exit fails the episode (lantern 0.1.3) |
| the player's socket dies | the player's receive loop catches `CatchableError`/`ConnectionClosed` and **exits 0** (raid 0.1.3 → 0.1.4: the starter's smoke only checks the game's exit code; ours checks every player's) |

Nothing in the tick loop blocks on an unbounded read. The LLM batch lives on a thread pool with a
deadline; the loop only polls a result slot.

### Two name spaces

- **In-game:** seats are `Cog-A` … `Cog-D`, assigned once per episode by a seeded permutation of
  slots (`random.Random(seed)`), so a policy cannot infer "slot 0 is always the strongest entrant".
  Aliases are the only identifiers in prompts, plans, `handoff`, `yield_to`, the team radio and
  every event. The wire observation carries no names at all, so scripted seats are anonymous by
  construction.
- **Spectator-side only:** the real policy name arrives in `game_config.players[].name` and appears
  **only** in the replay's `seats[].name`, in `results.names[]`, and therefore in the viewer, which
  renders `Cog-C · collab-cooking-expo`. The cogs never see the right-hand half.

---

## Sim module

The Python package is renamed `overcogged` → `collab_cooking` (one image, one entrypoint pair, one
name in the manifest, and `game.name` = `collab_cooking` is what the `secret put` step must use —
the namespace is `game.name`, not the slug, and they differ here (cogame-commons-family 0.1.1)).

| new path | from | change |
|---|---|---|
| `src/collab_cooking/game/game.py` | `src/overcogged/game/game.py` | map builder swapped from `MapGenConfig`/`CompoundConfig` to the ASCII kitchens; `_agent_config()` rewards reduced to `orders_served` only; `hub_*`/`station_offsets`/`station_order` fields and `validate_station_*` deleted with them; `full` mechanics forced on; everything else (station handlers, ticket specs, events, render config) unchanged |
| `src/collab_cooking/kitchens/layouts.py` | new; shape taken from `src/overcogged/classic/map.py`, which already builds `AsciiMapBuilderConfig` | the eight grids above, `CHAR_TO_MAP_NAME`, `kitchen(layout) -> AsciiMapBuilderConfig`, and `reachable_stations(layout, tile)` — the predicate that builds `LEGAL STATIONS` and enforces `zone` |
| `src/collab_cooking/missions/kitchen.py` | `src/overcogged/missions/basic.py` | `make_kitchen_mission(layout, max_steps)` at `num_agents=4` |
| `src/collab_cooking/agent/brain/{policy,obs_parser,entity_map,navigator}.py` | `src/overcogged/agent/overcogged_agent/*` | `obs_parser.py`, `entity_map.py`, `navigator.py` **byte-for-byte** (import paths only); `policy.py` gains the plan directive (station / recipe / zone / handoff / yield_to) and the four baseline names |
| `src/collab_cooking/coworld/server.py` | `src/overcogged/coworld/server.py` | bounded roster; per-tick state capture and event diffing; plan batch + delivery; the new results and replay writers; `/client/replay`, `/replay`, `create_replay_app()` and `clients/replay.html` **deleted**; 20 s shutdown grace before `quit(0)` |
| `src/collab_cooking/coworld/live_episode.py` | `src/overcogged/coworld/live_episode.py` | `PlayerClientMessage.type` gains `"register"`; `connect_player` records the seat's kind; `_start_when_ready` gets `player_connect_timeout_seconds` and starts with whoever is there; `run()` gains steps 4–8 and 10 of the resolution order; artifact writing moves to `replay.py`/`results.py` |
| `src/collab_cooking/coworld/llm.py` | port of `/workspace/starters/cogame-factorio/players/llm_player.py` | game-side; one parallel batch per turn; per-call deadline; retry-once; rolling rate budget; disabled-without-credentials |
| `src/collab_cooking/coworld/plans.py` | new | the reply schema, the caps, `truncate_runes`, plan → executor directive |
| `src/collab_cooking/coworld/replay.py` | new (replaces the two-line writer in `live_episode.run`) | the replay document below |
| `src/collab_cooking/coworld/player.py` | `src/overcogged/coworld/player.py` | the real player: registers from `PLAYER_PROMPT`/`PLAYER_SCRIPTED`, runs the executor, exits 0 on a dead socket. The starter's version (which sends `noop` forever) is not kept |
| `src/collab_cooking/coworld/clients/{player,global}.html` | overcogged's | kept, made layout-aware; they exist because certification probes both routes, not because we invest in them |

**Deleted, not adapted:** `src/overcogged/classic/` (the classic mission and its variants),
`src/overcogged/variants/{difficulty,layout,timing}.py` (the launch/curriculum variant graph —
kitchens are the variants now; the `mechanics.py` set is kept because `full` is what turns the game
on), `src/overcogged/recipe.py`, `tools/run.py`, `install.sh`, `.repo-root`, `reporter/`,
`src/overcogged/rendering.py` and the `overcogged` console script (§Out of scope).

**Config**, fully (`config_schema` mirrors it with `additionalProperties: false` and
`minItems`/`maxItems` on every array):

```
tokens: list[str]                          # 4, minItems 4, maxItems 4
players: list[{name: str}]                 # 4, real policy names, spectator-side only
num_agents: int = 4                        # minimum 4, maximum 4
layout: str = "open-kitchen"               # enum of the eight kitchens
seed: int = 20260825
max_steps: int = 900                       # 1..2000
step_seconds: float = 0.20                 # 0.01..1.0
policy_action_timeout_seconds: float = 0.30
player_connect_timeout_seconds: float = 120
plan_interval_steps: int = 50              # 1..1000
min_plan_interval_seconds: float = 10.0
plan_timeout_seconds: float = 12.0
llm_max_requests_per_minute: int = 26
fallback_scripted: str = "brigade"         # brigade | runner | passer | courier
play_budget_fraction: float = 0.6
episode_timeout_seconds: float = 1200
shutdown_grace_seconds: float = 20
ticket_interarrival: int = 18
ticket_deadline: int = 50
order_queue_max: int = 8
chop_ticks: int = 3        wash_ticks: int = 3
soup_cook_ticks: int = 10  soup_burn_ticks: int = 14
fries_cook_ticks: int = 8  fries_burn_ticks: int = 11
model: str = "claude-haiku-4-5-20251001"
max_output_tokens: int = 900
```

**Determinism.** `Simulator().new_simulation(env, seed=seed)` seeds the engine; the kitchens are
fixed ASCII with fixed spawns (`randomize_spawn_positions` is gone with the hub builder);
`random.Random(seed)` is drawn from exactly once, for the alias permutation. Nothing else in the
server is stochastic, so an all-scripted episode is byte-reproducible modulo `generated_at` —
asserted by a test.

---

## Server, player, protocol

### Game server

`/bin/collab-cooking` (a two-line `exec python -m collab_cooking.coworld.server` shim so
`tools/ci/docker_smoke.sh` works unmodified). FastAPI/uvicorn, the starter's routing kept:

- `GET /healthz` → `{"ok": true}`.
- `GET /client/player`, `GET /client/global` → real static pages, registered before any catch-all,
  neither of which opens a player socket (lantern 0.1.1: the certification runner probes both
  **before** starting player pods, and a 404 or a socket side effect fails the episode).
- `WS /player?slot=N&token=T` → seat N, token checked against `config.tokens[N]`, else close 1008.
- `WS /global` → the spectator state stream, and the runner's ping target; it keeps answering for
  the 20 s shutdown grace after artifacts are written.
- **`GET /client/replay` and `WS /replay` are deleted**, along with `create_replay_app()` and
  `COGAME_REPLAY_SERVER`. Replays are the static wasm bundle, never a pod.

Config in via `COGAME_CONFIG_URI`; results to `COGAME_RESULTS_URI`; replay to
`COGAME_SAVE_REPLAY_URI` (both through the starter's `write_uri`, unchanged).

### Player protocol (`game.protocols.player`)

`collab-cooking.player.v1`, JSON text frames, the starter's shape plus two messages.

**game → player, on connect:** `player_config` — unchanged
(`slot, connection_id, num_agents, action_names, observation_shape, policy_env, observation,
control_state`), plus `"alias": "Cog-C"`, `"layout": "forced"`, `"max_steps": 900`.

**player → game, once immediately after connect (new):**
`{"type":"register","kind":"prompt","prompt":"<≤1200 runes>"}` or
`{"type":"register","kind":"scripted","baseline":"brigade"}`. An unknown baseline, a malformed
frame, or no registration within 5 s of connect is treated as
`{"kind":"scripted","baseline":"brigade"}` — never a disconnect.

**game → player, every tick:** `observation` — unchanged (§Per-seat observation).

**game → player, at most once per plan turn, prompt seats only (new):**

```json
{"type":"plan","protocol":"collab-cooking.player.v1","turn":7,"step":350,
 "station":"chop","recipe":"soup","zone":"left","handoff":"Cog-D","yield_to":"none",
 "say":"I'll keep the board fed, D takes the middle counter","src":"llm"}
```

`src ∈ {"llm", "fallback:<cause>"}`. Scripted seats never receive it.

**player → game, every tick:** `{"type":"action","action_name":"move_north",
"policy_infos":{"policy_name":"<alias>","task":"chop veg"},"request_id":"step-350"}` — unchanged;
an action whose `request_id` is not this step is treated as `noop`.

**game → player, once at the end:** `final` — the snapshot plus
`{"done":true,"reason":"complete","scores":[…],"dishes":37,"names":[…],"aliases":[…]}`, after
which the player exits 0.

### Global protocol (`game.protocols.global`)

`collab-cooking.global.v1` on `/global`: the starter's coalesced snapshot sender, extended to carry
what a live spectator and the certifier need — `step`, `max_steps`, `layout`, `dishes`,
`scores`, `delivered`, `aliases`, `player_names`, `connected`, `paused`, `done`, `reason`, the
current station states, the four cogs' positions and carried items, and the last 8 feed lines. It
accepts the starter's control messages (`play`/`pause`/`speed`).

### Replay bytes (self-sufficient, strict UTF-8 JSON)

One UTF-8 JSON document written to `COGAME_SAVE_REPLAY_URI`. `docker_smoke.sh` parses it
(`SMOKE_REQUIRE_REPLAY_JSON=1`), the wasm module parses it in the browser, and **nothing else is
ever contacted** — no server, no config lookup, no name service.

```json
{"format":"collab-cooking/1","protocol":"collab-cooking.replay.v1","version":"0.1.0",
 "coworld":"collab_cooking","layout":"forced","generated_at":"2026-08-25T12:00:00Z",
 "seed":20260825,
 "config":{ "…every resolved config field except tokens, defaults expanded…" },
 "kitchen":{"w":13,"h":9,"tile":24,
            "rows":["##V#M########","#.....#.....#","…"],
            "stations":[{"kind":"chopping_station","x":1,"y":3},
                        {"kind":"order_board","x":6,"y":4}, "…"]},
 "seats":[{"slot":0,"alias":"Cog-A","name":"collab-cooking-expo","kind":"prompt",
           "baseline":"","color":0,"disconnected":false}],
 "ticks":[{"t":350,
           "c":[[3,5,"chopped_veg","move_east",0],[9,2,"clean_plate","noop",0]],
           "st":{"chop":{"veg":2,"meat":0},"pot":{"state":"cooking","timer":4},
                 "fryer":{"state":"idle","timer":0},"sink":{"wash":1},
                 "board":{"salad":1,"soup":2,"fries":0,
                          "tickets":[{"i":19,"recipe":"soup","expires":392}]},
                 "counters":[[6,4,"chopped_meat"],[6,2,"clean_plate"]]},
           "sc":[4,3,1,1],
           "ev":[{"ev":"serve","slot":2,"alias":"Cog-C","recipe":"soup","dish":9,"x":9,"y":8},
                 {"ev":"blocked","slot":0,"alias":"Cog-A","x":5,"y":3,"by":"cog"}]}],
 "heat":[[5,3,14],[6,4,9]],
 "results":{ "…exactly the results.json below…" }}
```

`c` (cogs: `x, y, carried, last_action, flags`) is present on **every** tick, always four entries
in slot order. **`st` and `ev` are omitted when unchanged / empty; an absent field means
"identical to the previous tick".** `flags` bits: 1 = last move blocked, 2 = plan just delivered,
4 = disconnected. `heat` is the cumulative per-tile blocked-move count, written once at the end
(the viewer also accumulates it live from `blocked` events so the overlay tracks the playhead).
At 900 ticks this is ≈ 300 KB.

**Event vocabulary — the complete list the replay may carry and the only names the viewer must
know:** `episode_start`, `order_arrive`, `order_expire`, `pickup`, `deposit`, `chop_start`,
`chop_done`, `pot_load`, `pot_start`, `pot_ready`, `pot_burn`, `pot_clear`, `fry_start`,
`fry_ready`, `fry_burn`, `fry_clear`, `plate_up`, `serve`, `wash_start`, `wash_done`, `blocked`,
`plan`, `fallback`, `deadline`, `episode_end`. Per-tick movement is **not** an event — it is in
`c`. `plan` carries `{slot, alias, turn, station, recipe, zone, handoff, yield_to, say, src}`
(never `note`); `fallback` carries `{slot, alias, cause}`. A test asserts the engine can emit
nothing else.

**`results.json`** (`results_schema` in the manifest matches it exactly):

```json
{"game":"collab_cooking","protocol":"collab-cooking.results.v1","reason":"complete",
 "layout":"forced","steps":900,"dishes":37,
 "scores":[37.12,37.10,37.09,37.06],"delivered":[12,10,9,6],
 "served_by_recipe":{"salad":14,"soup":15,"fries":8},
 "orders_arrived":50,"orders_expired":13,"burned":{"pot":2,"fryer":1},
 "blocked_moves":[41,33,58,29],"handoffs":[9,7,12,4],
 "names":["collab-cooking-expo","collab-cooking-linecook","Baseline (1)","Baseline (2)"],
 "aliases":["Cog-A","Cog-B","Cog-C","Cog-D"],
 "seat_kinds":["prompt","prompt","scripted:brigade","scripted:passer"],
 "cross_play":true,"disconnected":[false,false,false,false],
 "fallbacks":[0,1,0,0],"llm_requests":68}
```

Everything the viewer needs is in the replay bytes: aliases and real names (`seats[]`), the resolved
config, the seed, the kitchen grid and station positions, every tick's cog and station state, every
event, the heat map and the results.

---

## Viewer

**A static wasm bundle, never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` (the
`coworld build` hook, committed mode 100755) builds it; the platform serves it from
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`. overcogged's
`/client/replay` live-server path is deleted, not adapted.

### All four viewer files come from ONE starter: `Metta-AI/coworld-ctf`

coworld-overcogged has **no** replay viewer — no `replay-viewer/`, no `config.nims`, no wasm entry,
no `static_replay*.js`, no `index.html` (verified by `find` over the whole tarball). So the viewer
starter is **`Metta-AI/coworld-ctf` (paintbot)**, mounted at `/workspace/starters/coworld-ctf`, and
**all four files come from there and only there** — never a mixture, because splicing one starter's
shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` versus an
`onRuntimeInitialized`/worker bootstrap) deadlocks the viewer silently (cogame-lantern,
2026-08-23). ctf is also the right lineage on the merits: this is a tick-based grid, and ctf's
`broadcast_core.js` is a grid sprite compositor that draws exactly this shape of thing, and its
page is the one whose transport contract (`--band`, `--hudscale`, `relayout()`) the design pins
name.

| file | copied from `coworld-ctf` | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | paths and `EXPORTED_FUNCTIONS` renamed `ctf_*` → `cc_*`; `--preload-file <root>/data@data` kept (our generated art needs no preload, the font does). **No `MODULARIZE`, no `EXPORT_NAME`** — keep the plain `-o …/collab_cooking_replay.js` link, `-O2`, `-s ALLOW_MEMORY_GROWTH`, `-s ABORTING_MALLOC=1`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--mm:arc`, `--exceptions:goto`, `-d:useMalloc`, `-d:noSignalHandler` |
| wasm entry `replay-viewer/collab_cooking_replay.nim` | `replay-viewer/ctf_replay.nim` | same skeleton, same `exportc` pattern, same `emscripten_exit_with_live_runtime` epilogue; exports `cc_load_replay, cc_frame, cc_input, cc_packet_ptr, cc_packet_len, cc_error_ptr, cc_error_len, cc_stage_ptr, cc_stage_len`; imports `bitworld/spriteprotocol` and `pixie` and **no sim** (see the pipeline below) |
| `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | the same two files | `ctf_*` → `cc_*` in the worker's `Module._…` calls **and** in `importScripts` — renamed together, never one side; worker name `collab-cooking-static-replay`. Two deltas, both required: (a) `showFailure()` additionally sets `document.documentElement.setAttribute('data-replay-error', message)` — ctf only writes `#status`; (b) the `coworld-replay` bridge `ready` is posted from **inside** the branch that sets `data-replay-loaded="true"`, never on rAF at the call site (chorus `3c11c953`, 2026-08-24) |
| `index.html` | `client/replay_broadcast.html`, copied and sed-substituted at bundle time exactly as ctf's `Dockerfile.replay-viewer` does | see chrome provenance |

The bundle also carries `client/broadcast_core.js` and `client/chrome_common.js` from the same
starter. `tools/build_replay_viewer.sh` is ctf's hook with the file list retargeted, and it
`mkdir -p`s the output parent **before** the containment check (ecos, 2026-08-23: ctf's hook `cd`s
into a parent that does not exist on a fresh CI checkout) and asserts every file the page loads —
`index.html chrome_common.js broadcast_core.js static_replay.js static_replay_worker.js
collab_cooking_replay.js collab_cooking_replay.wasm collab_cooking_replay.data` — not a sample.

**The shell sets `data-replay-loaded="true"` on its first drawn frame and `data-replay-error` on
failure.** Both are load-bearing: `tools/ci/viewer_smoke.mjs` fails on silence and on the error
attribute.

**Pipeline.** The sim is Python on a C++ mettagrid core and does not compile to wasm — and it must
not be reimplemented in Nim, which would be a second source of truth for the rules. It does not
need to be: the replay records every tick's fully settled state, so every frame is **recorded, not
derived**. `cc_load_replay` parses the replay JSON, validates the required keys and the event
vocabulary, and builds the frame table; `cc_frame(i)` composes tick *i* into a bitworld sprite_v1
packet — the kitchen tiles from `kitchen.rows`, one sprite per station with its state, one per
counter holding an item, one per cog with its carried item and its alias letter, the heat overlay
when it is on — which `broadcast_core.js` draws unchanged. Chrome JSON rides the reserved sprite
**4090**'s label, ctf's convention, which `broadcast_core.js` already routes to `onText` without
registering it as drawable. A malformed replay sets `lastError`, returns 0, and the shell turns
that into `data-replay-error`. **cogame-factorio's `replay-viewer/factorio_replay.nim` is the
worked example of exactly this arrangement** (a Python coworld rendering a recorded replay through
the ctf shell); we read it, and we copy **no file** from it.

**The exact state JSON the viewer reads.** Every frame, the module re-emits sprite **4090**'s label:
one UTF-8 JSON object, ≤ 4 KB, every free-text field rune-truncated. This object *is* the viewer's
state contract — the page reads nothing else, and a test asserts the server can produce nothing
outside it:

```json
{"tick":350,"ticks":900,"layout":"forced","phase":"play","reason":null,
 "dishes":9,"live":3,"expiring":1,"expired":4,"burned":{"pot":1,"fryer":0},
 "seats":[{"slot":0,"alias":"Cog-A","name":"collab-cooking-expo","kind":"prompt",
           "color":0,"delivered":4,"carrying":"chopped_veg","job":"chopping",
           "pending":false,"say":"I'll keep the board fed","dc":false}],
 "ticker":[{"t":118,"recipe":"soup","alias":"Cog-C"},{"t":204,"recipe":"salad","alias":"Cog-A"}],
 "heat":[[5,3,14],[6,4,9]],
 "feed":[{"t":349,"kind":"serve","text":"Cog-C serves soup — dish 9"}],
 "beats":[{"t":118,"k":"serve","label":"Dish 1 — Cog-C serves soup"},
          {"t":260,"k":"burn","label":"Pot burns"},
          {"t":300,"k":"jam","label":"Jam at the doorway"}],
 "final":null}
```

`beats` is shipped **complete on the first frame** (ctf's `ingestBeats` pattern) so the scrubber
tells the story before playback reaches it; `feed` carries only lines new since the previous frame;
`ticker` and `heat` are cumulative to the playhead; `final` is null until the last tick, then
`{"reason":"complete","dishes":37,"order":[{"alias":"Cog-A","name":"…","delivered":12}, …]}`.

**Real art, not placeholders.** The repo ships no PNGs and mettagrid's asset pack is not ours to
depend on, so the sprites are authored as pixel-art patterns and baked with `pixie` at module
startup into a 24 px tile set: floor tile, counter (butcher-block top with an edge highlight), veg
crate, meat rail, plate stack, chopping board (with a knife and the 0–3 progress notch), pot (idle
/ bubbling / ready with steam / burned and black), fryer (same four states), pass hatch with a
ticket rail, sink (with the 0–3 suds level), order board (three ticket rows with countdown pips),
the cog (four facings, an alias letter, and the carried item drawn in its hands) and item icons
for the nine carryables. No placeholder box is acceptable and none is used.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** from `coworld-ctf`. Nothing in it is
  edited. It owns the clock, the transport bar, the scrubber, the beat markers, the lull spans and
  the spoiler toggle, and it resolves these ids by `getElementById`, every one of which the page
  must therefore keep: `btn-loop, btn-play, btn-skip, btn-spoilers, clock, clock-caption,
  clock-time, ffwd-chip, ffwd-mini, lulls, momentum, scrub, scrub-fill, scrub-head, scrub-win,
  speedchips, tick-clock, transport, win-chip`.
- **`client/replay_broadcast.html` is ctf's page with a game block appended** — not a rewrite that
  reuses its ids (cogame-gridlock, 2026-08-23). The starter's `<head>`, CSS custom properties,
  `relayout()`, `#chrome`, `#stage`, `#board`, `#viewport`, `#bannerlane`, the transport markup,
  the endcard skeleton and the bridge stay exactly as they are.
- **Removed** starter elements (ctf-specific, replaced by the appended game block): `#fpv,
  #fpv-canvas, #fpv-cap, #fpv-gear, #fpv-grip, #fpv-hp, #fpv-hud, #fpv-map, #fpv-map-canvas,
  #fpv-name`; `#lockerroom, #lk-art, #lk-bg, #lk-cap, #lk-sprites`; `#killfeed` (replaced by
  `#feed`); `#povBadge`; `#mmwarn`; and — per the zoom decision — `#viewpanel, #zoombar, #zoom-in,
  #zoom-out, #zoom-read, #zoom-slider, #minimap, #minimap-canvas`. **Kept as empty nodes**
  because `chrome_common.js` resolves them: `#momentum`, `#lulls`, `#win-chip`. **Kept and
  reused as they are:** `#scorebug` with `#plates-l` and `#plates-r` — ctf's two team columns
  become two columns of the same brigade, two cog plates each, so no id is invented and no id is
  repurposed silently (the game block says so in a comment).
- **Zoom decision: dropped entirely.** The biggest kitchen is 15×9 tiles = 360×216 px at 24 px per
  tile, always drawn in full and scaled to the frame; nothing is ever off-screen, so the zoom bar
  and the minimap have no job. `#viewpanel` and its children are removed and
  `static_replay.js`'s `attachMinimap` is never called.
- The appended game block must **not** declare a `function` with any name in the ChromeCommon alias
  list — hoisting shadows the alias and the beats render as unlabeled dead divs (tandem,
  2026-08-23). Ours are `ccDishTicker`, `ccHeatToggle`, `ccSayBar`, `ccSeatPlates`; a test reads
  the file and asserts it.

### Transport rules

1. **`--band` and `--hudscale` are set on `:root` by the starter's `relayout()`**; the game block
   reads them and never writes them.
2. **Nothing is overlaid inside the transport band.** The endcard keeps ctf's
   `bottom: var(--band, 0px)` so it stops above the bar, and the appended `#dishticker` /
   `#saybar` sit above `#board`, outside `#transport`.
3. **Every seek dismisses the endcard** — the seek handler hides `#endcard` before issuing the
   seek.
4. **Scrubber beats are clickable labelled `<button>` elements** that seek to their tick, with
   `aria-label`/`title` in spectator English ("Dish 9 — Cog-C serves soup", "Pot burns",
   "Ticket 12 expires", "Jam at the doorway", "New orders from Cog-A"), and CSS for **every kind
   emitted** — `.beat-marker.serve`, `.burn`, `.expire`, `.jam`, `.plan`, `.end`. No other kind is
   ever put on the scrubber.

### Readouts

- **Dish ticker** (`#dishticker`, the idea's first ask): a big `DISHES 37` readout plus a
  horizontal strip of dish chips in serve order — recipe icon, the tick, and the serving cog's
  alias — that advances with the playhead and highlights the newest chip for 24 frames.
- **Collision heat-map** (`#heatbtn`, the idea's second ask): a chip that toggles a per-tile tint
  over the floor, alpha ∝ `blocked` count at that tile cumulative to the playhead, normalised to
  the busiest tile. On `crowded` and `ring` it paints the choke bright red, which is precisely the
  finding those layouts exist to produce.
- **Scorebug** (`#scorebug` / `#plates-l` / `#plates-r`, four plates in slot order): seat colour
  chip, `Cog-C`, the real policy name underneath, dishes served by that cog, its current job
  (`chopping`, `to the pass`, `waiting`), and a `▶` while a plan is in flight. Plate CSS keeps
  `.plate-name { flex: 1 1 auto; min-width: 3.2em }` and hides secondary labels under `640px`.
- **Clock** (`#clock-caption` / `#clock-time` / `#tick-clock`): `TICK 350 OF 900` and
  `3 ORDERS LIVE · 1 EXPIRING` — real numbers, never internal notation.
- **Feed** (`#feed`): one line per serve ("Cog-C serves soup — dish 9"), per burn ("the pot burns —
  nobody plated it"), per expiry, per hand-off ("Cog-A leaves chopped meat on the middle counter"),
  per plan `say` ("Cog-A: I'll take the right side"), and a muted line per fallback ("Cog-B fell
  back to brigade — timeout").
- **Say band** (`#saybar`): the four seats' latest `say` lines as DOM chips in a band reserved
  above the board, sized from the 120-rune cap so the board never jumps when a line lands.
  **Model-authored text is drawn in the DOM, never on the canvas** — the canvas draws only alias
  letters and counts — which is why `viewer_smoke.mjs --strict-text-bounds` can hold
  `canvas_text.never_inside == 0` on a fixed arena without a separate worst-case renderer fixture
  (cogchemists, 2026-08-24).
- **Endcard**: final standings — alias, policy name, dishes served — plus the team total, orders
  expired, pots burned, and the end reason when it is not `complete`.
- **Legible at 360 px wide.** The softmax.com featured-match iframe is about that wide, so the
  scorebug, clock, dish ticker and feed are checked at 360 px, not at desktop width, and
  `viewer-smoke.png` is the evidence.

---

## Packaging

**`compose.yaml`** — one service, one image (the starter's two images collapse into one so the
player and the game share the brain code and the smoke script's `/bin/<slug>` /
`/bin/<slug>-player` convention holds):

```yaml
services:
  collab_cooking:
    image: coworld-collab-cooking:latest
    platform: linux/amd64
    build:
      context: .
      network: host
```

The manifest image placeholder is derived from the **compose service name**, so it is
`{{COLLAB_COOKING_IMAGE}}` (lantern 0.1.0 — `{{GAME_IMAGE}}` is not a thing).

**`Dockerfile`** — overcogged's (`python:3.12-slim`, `pip install --no-cache-dir .`), plus the two
shims `/bin/collab-cooking` and `/bin/collab-cooking-player` (`chmod +x`), plus the wasm-builder
stage taken from ctf's `Dockerfile.replay-viewer` (emsdk 4.0.15, nimby 0.1.27, Nim 2.2.4,
`nimby --global sync nimby.lock`) so `tools/build_replay_viewer.sh` can build the bundle from a
target of the same Dockerfile.

**`coworld_manifest_template.json`** — `$schema` set; tags
`["cooperation","melting-pot","grid","kitchen","multi-agent","llm"]` (≥ 3);
`game.name: "collab_cooking"`; `game.runnable` `{type:"game", image:"{{COLLAB_COOKING_IMAGE}}",
run:["/bin/collab-cooking"], env:{"ANTHROPIC_API_KEY_URI":
"secret://coworld/collab_cooking/anthropic_api_key"}}` — **the namespace is `game.name`, not the
slug** (cogame-commons-family 0.1.1), and without that env the hosted game container never receives
the secret and every league episode silently plays scripted (hive, 2026-08-23);
`episode_timeout_minutes: 20` top-level; `"replay_viewer": {"bundle": "static-replay-viewer"}`;
`game.config_schema` a real JSON Schema with `additionalProperties: false`, `num_agents`
`minimum: 4, maximum: 4`, and `minItems: 4, maxItems: 4` on `tokens` and `players` (every array
property needs both — tandem 0.1.0); `game.results_schema` covering every key of `results.json`
with `reason` an enum of exactly `["complete","deadline","no_players"]` and every array bounded
4/4.

**Variants — eight, `num_agents: 4` in every one.** Each also carries `max_steps: 900`,
`step_seconds: 0.20`, `plan_interval_steps: 50`, `player_connect_timeout_seconds: 120`, four
`players[]` display names, and a required `description`:

| id | name | distinguishing `game_config` | the coordination problem |
|---|---|---|---|
| `open-kitchen` | Open Kitchen | `layout:"open-kitchen"`, `num_agents:4`, `seed:20260825` | the control: no forced hand-off, no choke |
| `cramped` | Cramped Room | `layout:"cramped"`, `num_agents:4`, `seed:20260826` | four cogs in a 7×5 room |
| `forced` | Forced Coordination | `layout:"forced"`, `num_agents:4`, `seed:20260827` | two sealed halves; items only over the counter |
| `crowded` | Crowded | `layout:"crowded"`, `num_agents:4`, `seed:20260828` | one choke tile between prep and service |
| `asymmetric` | Asymmetric Advantages | `layout:"asymmetric"`, `num_agents:4`, `seed:20260829` | unequal station access → task allocation |
| `circuit` | Counter Circuit | `layout:"circuit"`, `num_agents:4`, `seed:20260830` | hand off over the island or walk 12 tiles |
| `ring` | Ring | `layout:"ring"`, `num_agents:4`, `seed:20260831` | a one-tile corridor: right of way |
| `figure-eight` | Figure Eight | `layout:"figure-eight"`, `num_agents:4`, `seed:20260832` | two loops, one shared spine |

**Certification fixture** — `certification.game_config`:
`{"num_agents": 4, "layout": "cramped", "max_steps": 480, "step_seconds": 0.02,
"policy_action_timeout_seconds": 0.30, "plan_interval_steps": 240,
"player_connect_timeout_seconds": 90, "seed": 20260826, "players": [four names],
"tokens": [four]}`, and `certification.players` seats **all four declared bundled players, one
each**: `[collab-prompt, brigade, passer, courier]`. Every declared runnable occupies a slot (a
fixture that omits one fails `players_missing` — raid 0.1.2 → 0.1.3), and
`len(certification.players) == num_agents == 4 == SMOKE_SEATS`.
Duration: 480 × (0.02 + ~0.005) ≈ **12 s** of play, plus the connect grace and the 20 s
shutdown grace ≈ **40 s** — inside `coworld certify`'s 60 s default (cogame-commons-family 0.1.0:
size the fixture to `grace + play + linger < 50 s`, and a test pins it). The replay is 480 frames
≈ **20 s of playback** at the viewer's 24 fps, comfortably longer than the 10 s soak window (ecos,
2026-08-23). It is also **cross-play by construction**: one prompt seat, three scripted partners.

**Bundled players** (`player[]`, all four on `{{COLLAB_COOKING_IMAGE}}` running
`["/bin/collab-cooking-player"]`, each with `id`/`type`/`name`/`description`):

| id | env | description |
|---|---|---|
| `collab-prompt` | `PLAYER_PROMPT: "<the reference kitchen strategy in words>"` | the reference prompt policy |
| `brigade` | `PLAYER_SCRIPTED: "brigade"` | prep / cook / server / all-rounder roles, the shipped brain |
| `passer` | `PLAYER_SCRIPTED: "passer"` | never crosses the midline; always stages on the pass counter |
| `courier` | `PLAYER_SCRIPTED: "courier"` | every seat serves; the greedy-service control |

**`game.docs`** — `readme` `{"type":"text","value":"<the whole of README.md, inline>"}` (inline
text, not a `uri`; a test asserts it is byte-identical to the README), plus `pages[]`: `rules.md`
(the dish chain, the tick order and the scoring formula), `kitchens.md` (the eight grids and what
each isolates), `policies.md` (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED`, the reply schema and its
caps, how the executor reads a plan), `protocol.md` (the wire messages). **`game.protocols` carries
BOTH `player` and `global`**, each as a `{"type":"text","value":"…"}` object — never a bare string
(cogame-garble 0.1.0, 2026-08-24).

**`tools/ci/policies.json`** (phase 40 mints these; **both champions are `PLAYER_PROMPT`**, the
fillers are scripted baselines and are distinct versions from the champions):

```json
[{"name":"collab-cooking-expo","run":"/bin/collab-cooking-player",
  "env":{"PLAYER_PROMPT":"Read the board first and name the recipe you are working. Do one job at a time and say which job you have taken so nobody duplicates it. If your item's next station is on the other side of a counter, put it on the counter and say so rather than walking round."}},
 {"name":"collab-cooking-linecook","run":"/bin/collab-cooking-player",
  "env":{"PLAYER_PROMPT":"Keep the pot and the fryer busy: nothing else scores as fast as a cooker that is never idle. Take the station nearest you that unblocks the next dish, yield to the cog carrying a finished dish, and never let a ready pot sit long enough to burn."},
  "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
 {"name":"collab-cooking-brigade","run":"/bin/collab-cooking-player",
  "env":{"PLAYER_SCRIPTED":"brigade"}},
 {"name":"collab-cooking-passer","run":"/bin/collab-cooking-player",
  "env":{"PLAYER_SCRIPTED":"passer"}}]
```

Champion #1 (`expo`) is owned by daveey, champion #2 (`linecook`) by daveey-1 via the `player`
field; the two scripted entries are the league fillers, and keeping **two** of them is what makes
the round-robin cross-play (§Scoring). Neither champion sets `USE_BEDROCK`: the LLM is game-side
and reaches the model through the game runnable's `ANTHROPIC_API_KEY_URI`.

**Workflows** — `.github/workflows/ci.yml` and `coworld-release.yml` from coworld-builder
`templates/`, with `<slug>` = `collab-cooking`, `<IMAGE>` = `coworld-collab-cooking`,
`<SEATS>` = `4`. `tools/ci/docker_smoke.sh` (mode 100755) and `tools/ci/viewer_smoke.mjs`
(verbatim, no substitutions) copied from the same templates. **One substitution the template does
not anticipate:** its `test` job is Nim; this game is Python, so that job becomes
`actions/setup-python@v5` (3.12) → `pip install -e ".[standalone]" pytest` →
`python -m pytest tests/ -v`. `docker-smoke` and `wasm-viewer` are taken unchanged (the wasm job's
Nim/emsdk toolchain is for `replay-viewer/`, which *is* Nim). The release workflow's `secret put`
step reads `game.name` from the manifest (`collab_cooking`), not the slug.

---

## Tests

`ci.yml`'s `test` job runs `pytest` over `tests/`:

1. **`tests/test_kitchens.py`** — the eight grids: every row the same width; a solid border; exactly
   one of each of the nine stations and exactly four `@`; every station cardinally adjacent to at
   least one open tile; BFS over open tiles gives **one** component for six kitchens and **exactly
   two** for `forced`, with ≥ 4 divider cells open on both sides; `crowded` has **exactly one**
   passage cell; `ring` and `figure-eight` have no 2×2 block of open tiles (the corridor really is
   one tile wide); every kitchen loads through `AsciiMapBuilderConfig` and produces a
   `MettaGridConfig` with `num_agents == 4`.
2. **`tests/test_rules.py`** — sim unit tests, one exact case per numbered rule: the 1-item carry
   limit; counter deposit then withdraw round-trips the item; chopping takes exactly 3 uses and
   yields to the third user; the salad plating rule; the pot starting only with both chopped
   ingredients, `pot_timer` reaching ready at 10 and burning at ready-age 14; the fryer at 8/11;
   serving with a live ticket incrementing that actor's `orders_served` and clearing the ticket;
   serving with no live ticket doing nothing; washing taking 3 uses; a ticket expiring at
   `arrival + 50`; and the arrival skip at `order_queue_max`.
3. **`tests/test_scoring.py`** — the formula and the sign: `scores[i] == dishes + 0.01×delivered[i]`
   with `dishes == Σ delivered`; every score non-negative and non-decreasing over the episode; the
   epsilon bound (`0.01 × max_tickets(900) = 0.5 < 1`) so the tie-break can never reorder two
   seats with different team totals; `results.json` shape — `scores`, `delivered`, `names`,
   `aliases`, `seat_kinds`, `disconnected`, `fallbacks` all length 4, `reason` inside the enum;
   `cross_play` true only when a prompt seat and a scripted seat sat together.
4. **`tests/test_baselines.py`** — the **bounded-orders / legality assertion on the scripted
   baselines**: all four baselines × all eight kitchens × 600 ticks. Assert every emitted action
   name is a member of `action_names`; exactly one action per seat per tick and never before that
   tick's observation; every `request_id == f"step-{step}"`; every `talk` string ≤ 140 runes and
   valid UTF-8; no baseline ever deadlocks a seat (each seat changes tile at least once per 60
   ticks in the connected kitchens); plus a fuzz pass of 400 randomly-generated plan objects
   (including illegal stations, wrong types, missing keys, 10 KB strings) through the executor,
   asserting it still emits exactly one legal action per tick. A baseline that produces an illegal
   or unbounded order fails CI.
5. **`tests/test_episode.py`** — an **end-to-end episode writing a replay**: four scripted seats,
   `cramped`, 480 ticks, in-process, writing `results.json` and `replay.json` to a temp dir.
   Assert `reason == "complete"`, exit 0, `len(replay["ticks"]) == 480`, dishes recomputed
   independently from the `serve` events equals `results.dishes`, and two runs with the same seed
   produce byte-identical replays modulo `generated_at`. A second case drives the deadline path
   with `play_budget_fraction` set tiny → `reason == "deadline"`, partial dishes scored rather than
   zeroed, exit 0. A third asserts `no_players`. A fourth pins the certification fixture's wall
   clock under 50 s.
6. **`tests/test_replay_parse.py`** — a **strict-UTF-8 replay parse** of the artifact test 5 wrote:
   `data.decode("utf-8")` with no error handler, then `json.loads`; every required key present
   (`format, protocol, config, seed, kitchen, seats, ticks, heat, results`);
   `len(seats) == 4` with both `alias` and `name` populated on each; every event `ev` inside the
   documented vocabulary; a `say` seeded with a multi-byte rune exactly at the 120-rune cap
   surviving as valid UTF-8; and `note` absent from the replay entirely.
7. **`tests/test_llm.py`** — reply handling against a stubbed transport: clean JSON; JSON with
   trailing prose; prose before `{`; missing fields defaulted; a `station` outside
   `LEGAL STATIONS` triggering **exactly one** retry and then the `brigade` fallback with
   `cause: "illegal_station"`; over-long `say`/`note` truncated on rune boundaries; the batch
   issuing all prompt seats' calls concurrently (asserted with a barrier in the stub); the rolling
   26 req/min budget refusing the call that would exceed it; and the **no-credentials path making
   zero network calls** and returning fallbacks immediately.
8. **`tests/test_viewer_contract.py`** — the payload contract without a browser: the event kinds the
   server can emit equal the documented vocabulary; every scrubber beat kind has a
   `.beat-marker.<kind>` rule in the page; the appended game block declares no top-level `function`
   colliding with the ChromeCommon alias list; and `config.nims`, the wasm entry,
   `static_replay.js` and `static_replay_worker.js` all name the same symbols (`_cc_*`) — the
   static check that would have caught cogame-lantern's split bootstrap.
9. **`tests/test_manifest.py`** — `num_agents == 4` in **every** variant and in
   `certification.game_config`; `len(certification.players) == 4` and every declared bundled player
   seated at least once; every array property in `config_schema` carrying `minItems`/`maxItems`;
   `game.protocols` carrying both `player` and `global` as objects; `game.docs.readme` inline and
   byte-identical to `README.md`; `replay_viewer.bundle == "static-replay-viewer"`; the runnable
   env carrying `ANTHROPIC_API_KEY_URI` with the `game.name` namespace.

**`docker-smoke` job:** builds the image and runs `tools/ci/docker_smoke.sh` with `SMOKE_SEATS=4`,
`SMOKE_GAME_BIN=/bin/collab-cooking`, `SMOKE_PLAYER_BIN=/bin/collab-cooking-player`,
`SMOKE_REQUIRE_REPLAY_JSON=1` — one game container plus four player containers on a per-run
network, driven by the certification fixture, with **no** `ANTHROPIC_API_KEY` (so every seat plays
scripted, which is the point of the fallback path). Asserts the game exits 0 having written
`results.json` and a replay that parses as UTF-8 JSON, and that **every player container exited 0**
(raid 0.1.4). Uploads `dist/smoke/replay.json` as the `smoke-replay` artifact.

**`wasm-viewer` job (`needs: docker-smoke`):** asserts `tools/build_replay_viewer.sh` and
`tools/ci/viewer_smoke.mjs` exist and the hook is executable; builds the bundle; asserts
`index.html` and a non-empty `.wasm`; then **executes** it —

```
node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
  --replay dist/smoke/replay.json --timeout 90 --soak 10 --strict-text-bounds
```

— in headless chromium against the replay `docker-smoke` just produced. The bundle is **run, not
merely built**: it must set `data-replay-loaded="true"`, never set `data-replay-error`, keep the
clock, tick counter, dish ticker and scorebug advancing through the uninterrupted 10 s soak with no
uncaught page error (cogball 0.1.4), answer the 0 % / 50 % / 100 % scrub probes with three
different clocks, and draw no canvas text outside the frame (`canvas_text.never_inside == 0` — a
fixed arena). The 20 s cert replay outlasts the 10 s soak by design.

---

## Out of scope (v1)

1. **Nine seats, and the 9-cog `crowded` room.** v1 pins `num_agents: 4` in the schema
   (`minimum: 4, maximum: 4`), every variant, the cert fixture and `SMOKE_SEATS`, so the four
   declarations cannot drift apart; `crowded` ships as the 4-cog rendering of the same choke-point
   finding. A 9-seat kitchen needs bigger rooms, a different rate budget (9 seats/batch is 54
   req/min against a 30 req/min cap) and its own balance pass; it is a later variant set with its
   own seat count, not a v1 knob.
2. **overcogged's `classic` mission** (`src/overcogged/classic/*`, the `mission` config key and its
   `basic`/`classic` enum). It is a different game — miners, scramblers, chests — preserved in the
   starter for history. The coworld runs the kitchen only.
3. **The variant graph's difficulty and timing knobs** (`easy`, `hard`, `rush_hour`, `tutorial`,
   `short_cook`, `long_cook`, `fast_burn`, and the five `layout_*` hub variants). The kitchens are
   the variants now; the mechanics variants stay only because `full` is what turns the recipes on.
   Difficulty tiers are a second variant axis once the eight kitchens have ranked episodes.
4. **The `overcogged` CLI, the `metta play` recipe, the GUI/unicode renderers and `install.sh`**
   (`cli.py`, `recipe.py`, `rendering.py`, `tools/run.py`, `.repo-root`). They pull the whole Metta
   stack into an image that only needs `mettagrid`, and the coworld is driven by the server, not a
   console script.
5. **The reporter runnable** (`reporter/default` + `reporter/reporter_sdk`). Not required for
   certification, it adds a second image and a second toolchain to the release, and its narration
   duplicates the viewer feed. Dropped from the fork; the code stays in `coworld-overcogged`.
6. **The live replay pod** (`/client/replay`, `WS /replay`, `create_replay_app`,
   `clients/replay.html`, `COGAME_LOAD_REPLAY_URI`). Deleted, not maintained alongside the wasm
   bundle. There is one viewer.
7. **Human playability.** `/client/player`, `/client/global` and the `/global` socket are served
   because certification probes them, and the starter's takeover/`tick_when_act` path is left in
   place, but no work goes into making either pleasant.
8. **Retuning the kitchen's balance constants.** Ticket cadence, deadlines, chop/wash/cook/burn
   timers and the queue cap are carried over from the starter unchanged so the eight kitchens are
   compared against one economy. A balance sweep across layouts is the obvious follow-up once the
   ladder has episodes.
9. **RL training.** No PettingZoo/curriculum entry points, no policy checkpoints, no `eval_missions`
   — the seats are LLM prompt policies and scripted baselines.
