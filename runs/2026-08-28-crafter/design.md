# cogame-crafter — design note (2026-08-28)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` importing and re-exporting the sim
modules, `sim_types.nim` owning `GameVersion` (`src/ctf/sim_types.nim:21`) and `TargetFps* = 24`
(`:376`) with its prepend-only changelog-comment discipline, the flatty wire types whose field order
is sacred, and the rune caps `MaxNoteRunes` / `MaxSayRunes` / `MaxPromptRunes` (`:794-799`)); the
mummy HTTP/websocket server implementing the Coworld contract, including its
`wallClockBudgetSeconds` stop at `src/ctf/server.nim:1407-1417`; the `decide.nim` / `directives.nim`
/ `llm.nim` / `baselines.nim` / `control.nim` commander layer with its one-batch-per-turn shape
(`src/ctf/decide.nim:427` `engine.client.curl.makeRequests`), its `attempt1Ms` / `retryMs` /
`turnBudgetMs` / `turnSpacingMs` deadlines (`decide.nim:384-389, 406, 421-427`), its budget guard
(`decide.nim:328-346`), its tolerant JSON extraction, its rune truncation, and its fallback ladder
with the exact log phrasing (`decide.nim:463` "failed, falling back if it fails again" for attempt 1;
`:491` "falling back" only on the second failure); the achievement ledger the starter already owns
(`recordAchievement` at `src/ctf/roster.nim:640-648`, `earnedAccounts[].earnedAchievements`
serialised at `roster.nim:828`); the binary `COWLDCTF` replay of *inputs plus a per-tick `gameHash`*
(`src/ctf/replays.nim:142`), re-simulated by **the same sim module** compiled to wasm by
`replay-viewer/config.nims`; the `client/` broadcast chrome (`chrome_common.js` +
`broadcast_core.js` + `replay_broadcast.html` with its `window.PaintballChrome.install(PB_CTX)`
splice hook at `client/replay_broadcast.html:4330-4337` and the appended-game-block banner at
`:4344`); nimby + `Dockerfile` + `Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh`; and the
Nim test suite with its four shards (`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **this is a single-agent real-time tick loop whose rules are written into
this repo — the first row of the starter table** (`prompts/10-design.md` §Starter table: "any
real-time game loop (grid OR continuous physics), new rules written for this coworld"). It is
deliberately **not** the `cogame-moba` bit-exact-port row, and that is a **rail the coordinator
already set and this note does not revisit**: the Crafter/Craftax family is **re-implemented as this
coworld's own deterministic seeded Nim sim on the paintbot stack, not ported**. Crafter is Python
(numpy + OpenSimplex + an `imageio` renderer) and Craftax is JAX; neither compiles into the Nim wasm
static replay viewer, and the static viewer is a non-optional pin. No upstream code is vendored, no
upstream number is claimed as reproduced, and no score from this coworld is comparable to a published
Crafter/Craftax figure — every divergence is enumerated in §Sim module → "Documented divergences" and
mirrored into `docs/PORTING-CRAFTER.md`. The precedent for forking paintbot for a single-agent grid
benchmark is four deep on this same day (cogame-nethack, cogame-minigrid, cogame-procgen,
cogame-atari-57) and ten deep overall (knights-archers, pistonball, atari-cabinet, walker-waterworld,
particle-worlds, smac-starcraft-micro, magent-battle, rware-warehouse, flatland,
sumo-traffic-signals).

Where this note departs from coworld-ctf it says so. The departures are: the rules are survival and
tech-tree rules, not paintbot's (§Sim module lists what is deleted); the board is a **64 × 64 integer
cell grid** built by a seeded integer-noise generator, so ctf's pixel arena, procedural map
generator, map pool, map editor and mapkit are deleted; there is **one seat, not eight**, and no
teams; the seat is **partially observed** through a 9 × 9 egocentric window, so ctf's raycast fog is
replaced by a plain rectangular visibility rule; the **world is much larger than the frame**, so —
unlike the fixed-arena forks — `#viewpanel` (zoom bar + minimap) is **kept** (§Viewer); and
`MaxSayRunes` / `MaxNoteRunes` are re-pinned (§Decisions → reply schema).

### Source idea (verbatim)

> SA Crafter / Craftax — a 2D Minecraft where the score is how many of 22 achievements you unlock before you starve
>
> Single-agent coworld over Crafter (Hafner 2021) and Craftax (Matthews et al. 2024, JAX, much larger: dungeons, bosses, spells, 65+ achievements). Procedural 64×64 world, day/night, hunger/thirst/fatigue, zombies at night; 17 actions; achievements (collect wood → place table → make pickaxe → … → collect diamond, eat cow, defeat zombie) define the score — a tech tree with survival pressure. Crafter's success-rate-per-achievement scoring is the standard.
>
> Seats: 1
> Motive: achievement-unlock score
> Policy interface: per-tick discrete over a 9×9 local view; symbolic obs option makes LLM play feasible (Craftax-Symbolic)
> Fills gap: open-ended tech-tree exploration; compare to NMMO (multi-agent, shallower tree) — this is the single-agent depth version
> Integrity: seeded worlds; geometric-mean-of-success-rates score as in the paper; replay verification.
>
> Replay plan (watchability): pixel render; achievement checklist lighting up; night-survival tension.
>
> Source: github.com/danijar/crafter; github.com/MichaelTMatthews/Craftax.

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time tick loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-crafter` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=forager\|wanderer`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance, byte-for-byte `chrome_common.js`, starter art + install-time bakes) |
| Two name spaces | §The game (in-game alias `Alpha`; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (typical 227 s, worst 654 s, engine stop 660 s, budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 1`, three times |
| Per-turn LLM call budget stated (single seat) | §Decisions (exactly one request per turn, two with the retry; ≤ 112 per episode) |
| Replay bytes self-sufficient | §Server (config JSON, joins, per-turn plans, chats, per-tick hashes, seed, variant) |
| Rune-boundary truncation on every free-text field | §Decisions (reply schema) |
| Seeded worlds + replay verification (the idea's integrity note) | §Sim module (world is a pure hash of `(seed, …)`; the seat never sees `seed` or an unexplored cell); §Server (per-tick `gameHash` chain re-checked in the browser) |
| Geometric-mean-of-success-rates (the idea's scoring note) | §The game → Scoring — reconciled: per-episode the league ranks `scores[0]`; the paper's aggregate is computed **cross-episode** from `results.achievementUnlocked[22]` |

---

## The game

One cog wakes at dawn in the middle of a 64 × 64 procedurally generated world it can see nine cells
of. It is hungry, thirsty and tired, and there is a list of **twenty-two things it has never done**:
chop wood, put down a crafting table, make a wooden pickaxe, mine stone, make a stone pickaxe, build
a furnace, smelt an iron pickaxe, and — at the bottom of the tech tree — cut a diamond out of the
rock. It also has to eat, drink, sleep, and survive the zombies that come out of the grass when the
sun goes down. Every tick it does one of seventeen things. The only number the league reads is **how
many of the twenty-two it unlocked before it died**.

The whole game is the tension between the tree and the clock: every step down the tech tree costs
ticks you needed for water, and every night you sleep through is a night you did not spend mining.

### Seats and aliases

- **`num_agents` = 1.** Exactly one seat, always — in both manifest variants and in the certification
  fixture. This is the idea's own "Seats: 1", and it is what the game is: Crafter and Craftax are
  single-agent benchmarks and a second cog would change the achievement semantics entirely. Every
  episode is a solo run; policies are compared across episodes, not within one.
- **Two name spaces.** In-game the seat is **`Alpha`** — `IdentityNames[0]`
  (`src/ctf/roster.nim:64-65`), title-cased by `seatAlias(slot)`. That alias is the only name that
  appears in an observation, in a prompt, in a `say`, or on the board. The seat's **real
  policy/player name** (`daveey`, `daveey-1`, `Baseline (1)`) lives only in `results.names`, in the
  replay's join record, and spectator-side in the viewer's scorebug plate and endcard.
  `showPlayerLabels` is **false**, as in the starter's paintball variant, so nothing drawn on the
  board leaks an identity. With one seat there is nobody to meta-game against, but the pin is
  satisfied both ways, not either way: the alias is what the model sees, the real name is what the
  spectator sees.

### The world

**`worldSize = 64`.** A 64 × 64 grid of cells indexed `(x, y)`, `x` the column `0 … 63` (west → east)
and `y` the row `0 … 63` (north → south); `(0, 0)` is the north-west corner. The outermost ring
(`x ∈ {0, 63}` or `y ∈ {0, 63}`) is **`bedrock`** — impassable, unmineable, unplaceable — so the cog
can never leave the world and no generator needs an out-of-bounds branch. The playable interior is
62 × 62 = 3844 cells; `cellsTotal` is the constant **4096** (the whole grid, bedrock included), which
is what `results.cellsSeen` is a fraction of.

**A cell holds exactly one terrain and at most one creature.** The closed terrain enum, its glyph,
and its rules:

| Terrain | Glyph | Walkable | Mined by `do` | Yields | Becomes |
|---|---|---|---|---|---|
| grass | `.` | yes | yes (1-in-10, see below) | 1 `sapling` | grass |
| sand | `,` | yes | no | — | — |
| water | `~` | no | yes | +1 drink | water |
| stone | `#` | no | needs `wood_pickaxe` | 1 `stone` | `path` |
| path | `=` | yes | no | — | — |
| tree | `T` | no | yes (bare hands) | 1 `wood` | tree (**infinite**) |
| coal | `c` | no | needs `wood_pickaxe` | 1 `coal` | `path` |
| iron | `i` | no | needs `stone_pickaxe` | 1 `iron` | `path` |
| diamond | `D` | no | needs `iron_pickaxe` | 1 `diamond` | `path` |
| lava | `!` | **yes** | no | — | stepping in is **instant death** |
| bedrock | `B` | no | no | — | — |
| table | `t` | no | no | — | — (placed) |
| furnace | `f` | no | no | — | — (placed) |
| sapling | `p` | no | no | — | ripens to `ripe_plant` after `plantRipenTicks = 120` |
| ripe plant | `Y` | no | yes | +6 food | `sapling` (re-ripens) |

Creature glyphs, drawn over the terrain in the view: **`U` cow, `Z` zombie, `K` skeleton, `^`
arrow**; **`@`** is the cog itself; **`?`** is a cell it has never seen. Those twenty glyphs are the
whole vocabulary the seat ever reads, and they are the whole vocabulary the viewer's inset ever
draws.

**The cog** has a position `(x, y)`, a `facing ∈ {up, down, left, right}` (world frame: `up` = −y,
`down` = +y, `left` = −x, `right` = +x), four vitals, an inventory and six tool flags:

- **Vitals**, each an integer `0 … 9`: `health`, `food`, `drink`, `energy`. All start at **9**.
- **Inventory**, each an integer `0 … 9`: `wood`, `stone`, `coal`, `iron`, `diamond`, `sapling`. All
  start at **0**. A collection that would exceed 9 is capped and still unlocks its achievement.
- **Tools**, each a boolean, all false at start: `wood_pickaxe`, `stone_pickaxe`, `iron_pickaxe`,
  `wood_sword`, `stone_sword`, `iron_sword`.

### World generation (seeded, integer-only, no floats)

Four **integer value-noise fields** — `mountain`, `water`, `tree`, `cave` — each built on a lattice
of stride 8 whose corner values are `mix64(seed, fieldSalt, gx, gy) mod 1024` and bilinearly
interpolated in 16-bit fixed point, yielding an integer `0 … 1023` per cell. `fieldSalt` is `1, 2, 3,
4` respectively. Nothing here is floating point (§Sim module → Integer arithmetic), so the field is
bit-identical native and in wasm.

For each interior cell, in ascending `(y, x)`, first match wins — `M`, `W`, `T`, `C` are the four
field values at that cell and `mountainThreshold` is a variant constant (**700** in `standard`,
**660** in `longnight`):

1. `M > mountainThreshold`:
   a. `C > 830 and M < 850` → **path** (a cave tunnel)
   b. `C < 60 and M > 780` → **lava**
   c. `M > 960 and C > 900 and mix64(seed, 13, x, y) mod 1000 < 60` → **diamond**
   d. `M > 800 and mix64(seed, 12, x, y) mod 1000 < 8` → **iron**
   e. `M > 760 and mix64(seed, 11, x, y) mod 1000 < 12` → **coal**
   f. else → **stone**
2. `W > 640` → **water**
3. `W > 590` → **sand**
4. `T > 700` → **tree**
5. else → **grass**

Then a **playability post-pass**, deterministic and in this order — without it a seed can be
unwinnable, and an unwinnable seed makes a benchmark meaningless:

1. The 3 × 3 block centred on **(32, 32)** is forced to `grass`; the cog spawns at **(32, 32)** facing
   **down**.
2. If no `tree` lies within Chebyshev radius 12 of spawn, the first `grass` cell (ascending `(y, x)`)
   at Chebyshev distance exactly 6 becomes `tree`.
3. If no `water` lies within radius 12, the first `grass` cell at Chebyshev distance exactly 8
   becomes `water`.
4. If no `stone` lies within radius 20, the first `grass` cell at Chebyshev distance exactly 14
   becomes `stone`.
5. Global minima: while `count(coal) < 5`, `count(iron) < 3` or `count(diamond) < 1`, convert the
   `stone` cell with the highest `M` (ties by ascending `(y, x)`) into the missing material, coal
   first, then iron, then diamond.

The result: **every seed is completable**, the world is a pure function of `(seed, variant)`, and the
seat is never told any of it (§Decisions → observation).

### Day, night, and the creatures

**`dayLength`** is a variant constant (`standard` **192**, `longnight` **160**). A tick is **day**
when `tick mod dayLength < dayFraction` and **night** otherwise, with `dayFraction` = 128 in
`standard` and 80 in `longnight`. `day = tick div dayLength + 1` is the day number shown on the
clock. `standard` therefore gives 128 ticks of light and 64 of dark; `longnight` gives 80 and 80.

Three creature kinds live in a single stable array ordered by `(spawnTick, spawnY, spawnX)`; that
order is the resolution order and it never changes for a living creature.

| Creature | HP | Spawns on | When | Cap | Moves | Hurts you |
|---|---|---|---|---|---|---|
| cow `U` | 3 | `grass` | day only | `maxCows` (12 / 8) | 1 step every 4th tick, random legal direction | never |
| zombie `Z` | 5 | `grass` or `sand` | night only | `maxZombies` (8 / 12) | 1 step every 2nd tick, greedily toward the cog | 2 damage awake, **5 asleep**, at most once per 5 ticks, from a 4-adjacent cell |
| skeleton `K` | 3 | `path` | any time | `maxSkeletons` (6) | 1 step every 3rd tick, greedily toward the cog, **only onto `path`** | shoots an `arrow` |
| arrow `^` | — | — | — | — | 1 cell per tick in its direction | 2 damage on entering the cog's cell, then vanishes |

**Spawning**, one attempt per kind per tick, in the order cow → zombie → skeleton: if that kind is
under its cap, take `cx = mix64(seed, 400 + kind, tick) mod 62 + 1`,
`cy = mix64(seed, 410 + kind, tick) mod 62 + 1`, and spawn iff the cell has the right terrain, holds
no creature, and its Chebyshev distance to the cog is **≥ 6** (so nothing ever pops into the 9 × 9
view). One attempt, never a retry loop — bounded work per tick, by construction.

**Zombies burn at dawn.** On the first tick of each day, every zombie whose cell is not `path` is
removed and one `burn` event is emitted with the count. That is what makes night, and only night,
dangerous, and it is what the viewer's night shading is about.

**Skeleton shooting.** A skeleton fires when the cog is within 6 cells on the same row or column,
every cell strictly between them is walkable, and `tick − lastShot ≥ 8`. The arrow spawns in the
adjacent cell toward the cog, moving in that direction. An arrow that enters a non-walkable cell or a
creature's cell is removed.

**Fighting.** `do` facing a creature deals **1** damage bare-handed, **2** with `wood_sword`, **3**
with `stone_sword`, **5** with `iron_sword`. A creature at 0 HP is removed: a cow gives **+6 food**
and unlocks `eat_cow`; a zombie unlocks `defeat_zombie`; a skeleton unlocks `defeat_skeleton`.

### The seventeen actions

Exactly Crafter's seventeen, by name, and nothing else is a primitive:

`noop`, `move_left`, `move_right`, `move_up`, `move_down`, `do`, `sleep`, `place_stone`,
`place_table`, `place_furnace`, `place_plant`, `make_wood_pickaxe`, `make_stone_pickaxe`,
`make_iron_pickaxe`, `make_wood_sword`, `make_stone_sword`, `make_iron_sword`.

- **`move_<dir>`** sets `facing = dir` **and** steps one cell in `dir` if that cell is walkable and
  holds no creature; if it is not, the cog only turns. (This is Crafter's semantics and it is the one
  an implementer guesses wrong.) Stepping into `lava` sets `health = 0` on that tick.
- **`do`** acts on the cell the cog faces, in this precedence: a **creature** there is attacked; else
  the terrain's "Mined by `do`" rule applies (a `grass` cell yields a `sapling` iff
  `mix64(seed, 600, x, y, tick) mod 10 == 0`, otherwise nothing); else nothing happens.
- **`sleep`** puts the cog asleep for that tick: `energy += 1` (capped at 9). It stays asleep only for
  consecutive `sleep` primitives; any other primitive wakes it, and so does taking creature/arrow
  damage (§ the flinch rule).
- **`place_stone`** costs 1 `stone` and turns the faced cell into `stone` if that cell is
  `grass | sand | path | water | lava` and holds no creature. Placing over lava is how you cross it.
- **`place_table`** costs 1 `wood`; **`place_furnace`** costs 1 `stone`; both require the faced cell
  to be `grass | sand | path` and creature-free, and turn it into `table` / `furnace`.
- **`place_plant`** costs 1 `sapling` and requires the faced cell to be `grass`; it becomes `sapling`
  and ripens `plantRipenTicks = 120` ticks later.
- **Crafting** requires a `table` within Chebyshev distance 1 of the cog (`near.table`), and the iron
  recipes additionally a `furnace` within Chebyshev distance 1 (`near.furnace`):

  | Recipe | Costs | Also needs |
  |---|---|---|
  | `make_wood_pickaxe` | 1 wood | table |
  | `make_wood_sword` | 1 wood | table |
  | `make_stone_pickaxe` | 1 wood + 1 stone | table |
  | `make_stone_sword` | 1 wood + 1 stone | table |
  | `make_iron_pickaxe` | 1 wood + 1 coal + 1 iron | table **and** furnace |
  | `make_iron_sword` | 1 wood + 1 coal + 1 iron | table **and** furnace |

  Crafting an already-owned tool is a no-op that costs nothing and still costs the tick.

An inapplicable primitive is a **no-op that still costs its tick**. There is no error, no repair and
no free retry: that is the whole cost model of the game.

### Vitals

Evaluated every tick, in this order:

1. `food -= 1` when `tick mod foodTicks == 0` (`foodTicks = 40`).
2. `drink -= 1` when `tick mod drinkTicks == 0` (`drinkTicks = 30`).
3. `energy -= 1` when awake and `tick mod energyTicks == 0` (`energyTicks = 50`); asleep, step 3 is
   skipped (the `sleep` primitive already added 1 in step 3 of the tick order).
4. **Regeneration**: if `food > 0 and drink > 0 and energy > 0` and `tick mod regenTicks == 0`
   (`regenTicks = 25`), `health += 1` (capped at 9).
5. **Starvation**: for each of `food`, `drink`, `energy` that is exactly 0, if
   `tick mod starveTicks == 0` (`starveTicks = 10`), `health -= 1`. Three zeroed vitals cost 3 health
   on the same tick.

Arithmetic worth checking: 9 drink lasts 270 ticks, 9 food 360, 9 energy 450. In a 1344-tick episode
the cog must drink about five times, eat about four times and sleep about three times — which is
exactly why `wake_up`, `eat_cow`, `eat_plant` and `collect_drink` are achievements and not
distractions.

### The twenty-two achievements

The canonical Crafter list, in the canonical order. This ordering is `achievementIds` in `results`,
the order of the viewer's checklist, and the order of the `locked` list in the observation. Each
unlocks **once**, permanently, the tick its predicate first becomes true, and is never revoked.

| # | id | Unlocks when |
|---|---|---|
| 1 | `collect_wood` | a `do` on a `tree` yields wood |
| 2 | `place_table` | a `table` is placed |
| 3 | `eat_cow` | a cow is reduced to 0 HP by the cog |
| 4 | `collect_sapling` | a `do` on `grass` yields a sapling |
| 5 | `collect_drink` | a `do` on `water` raises `drink` |
| 6 | `make_wood_pickaxe` | the recipe succeeds |
| 7 | `make_wood_sword` | the recipe succeeds |
| 8 | `place_plant` | a sapling is planted |
| 9 | `defeat_zombie` | a zombie is reduced to 0 HP by the cog |
| 10 | `collect_stone` | a `do` on `stone` yields stone |
| 11 | `place_stone` | a stone is placed |
| 12 | `eat_plant` | a `do` on a `ripe plant` raises `food` |
| 13 | `defeat_skeleton` | a skeleton is reduced to 0 HP by the cog |
| 14 | `make_stone_pickaxe` | the recipe succeeds |
| 15 | `make_stone_sword` | the recipe succeeds |
| 16 | `wake_up` | a run of ≥ 1 `sleep` ticks that began with `energy < 9` ends with `energy == 9` |
| 17 | `place_furnace` | a `furnace` is placed |
| 18 | `collect_coal` | a `do` on `coal` yields coal |
| 19 | `collect_iron` | a `do` on `iron` yields iron |
| 20 | `make_iron_pickaxe` | the recipe succeeds |
| 21 | `make_iron_sword` | the recipe succeeds |
| 22 | `collect_diamond` | a `do` on `diamond` yields a diamond |

They are recorded through the starter's own ledger — `sim.recordAchievement(0, id)`
(`src/ctf/roster.nim:640-648`), which already deduplicates — plus a parallel `achievementTick[22]`
array this fork adds so the viewer's checklist knows *when* each lit up.

### Turn and tick structure — the exact resolution order

Per **command turn** `T`, in this order:

1. If the episode has already ended, stop (§End conditions). Otherwise build the seat's observation
   from the current state (§Decisions → observation).
2. Issue the seat's LLM request. There is exactly **one** seat, so this is a batch of one through the
   starter's unchanged `engine.client.curl.makeRequests` path (`src/ctf/decide.nim:427`) — the code is
   the starter's batching code, carrying one request. Attempt-1 deadline `attempt1Ms = 6000`. A
   scripted seat computes locally, instantly, and consumes no request.
3. If the seat timed out, errored, returned non-JSON, or returned no usable `actions` array, it is
   retried **once**, `retryMs = 3000`.
4. Still no usable reply → the **`forager`** scripted plan is computed server-side (the same proc the
   `forager` baseline uses — imported, never duplicated) and a `fallback` record is written.
5. **Validate and expand the plan**, in the order the reply lists it:
   a. Entries past `maxActionsPerTurn = 12` are dropped and counted in `actionsDropped`.
   b. Each entry is validated against the reply schema; an entry that does not validate is
      **dropped** (never rewritten as a different action), counted in `repliesRepaired`, and reported
      back next turn.
   c. Macros are expanded against the **known map as of turn start**: `move` into up to `n` step
      primitives, `do`/`sleep` into up to `n` copies of themselves, `goto` into the BFS path
      (§Decisions → the driver). Each macro yields at most `macroPrimitiveCap = 24` primitives. A
      `goto` whose target is not reachable through known walkable cells yields **zero** primitives,
      counts in `macrosUnreachable`, and is reported next turn as `unreachable`.
   d. The whole expanded queue is truncated to `turnTicks = 24` primitives; the surplus is discarded
      and `planTruncated` is reported next turn. **Nothing carries over.**
6. `say` (≤ 160 runes) and `notes` (≤ 400 runes) are sanitised on rune boundaries and, with the
   accepted plan, written as the turn's `directive` replay record. `notes` is echoed back to this
   seat next turn and to nobody else; `say` is drawn in the spectator feed.
7. `turnSpacingMs = 2600` is a floor on the wall clock between consecutive request **starts** (the
   starter's mechanism at `src/ctf/decide.nim:384-389`, kept), pinning the steady state at 23 req/min
   against the sidecar's 30/min per-episode cap.

Then, for each of the next `turnTicks` ticks, in this order — **this is the whole physics of the game
and nothing else mutates the world**:

1. `tick += 1`.
2. Pop the next primitive from the queue. If the queue is empty the primitive is **`noop`** (a real
   cost: the tick is spent).
3. **Apply the primitive** exactly as §The seventeen actions specifies (movement/facing, `do`,
   placing, crafting, `sleep`'s `energy += 1`), recording `blocksMined`, `blocksPlaced`,
   `itemsCrafted`, `damageDealt` and any creature death.
4. **Vitals**, the five numbered steps of §Vitals.
5. **World tick**: saplings placed `plantRipenTicks` ticks ago become ripe plants; the day/night phase
   is recomputed; at the first tick of a new day, zombies above ground burn.
6. **Spawns**: one bounded attempt each for cow, zombie, skeleton, in that order.
7. **Creatures act**, in the stable creature order: arrows move first, then skeletons, then zombies,
   then cows. Each applies its damage to the cog immediately (`damageTaken` accrues, `hurt` is
   emitted).
8. **Achievements**: evaluate every not-yet-unlocked predicate; a newly true one is recorded with
   `achievementTick[i] = tick` and emits `achievement`.
9. **Death check**: `health <= 0` → the episode ends this tick with `endRule = death` and
   `deathCause ∈ {zombie, skeleton, arrow, lava, starvation, thirst, exhaustion}` (the cause of the
   damage that crossed zero; a simultaneous starvation of several vitals resolves in the order food →
   drink → energy).
10. **Visibility**: mark the 9 × 9 window centred on the cog as seen, merge it into the known map
    (last-seen terrain + `seen_tick`), and update the 16 × 16 region map and the landmark set.
11. Mix the tick into `gameHash` and append it to the replay's hash chain.
12. **Flinch / stop**: if the cog took damage from a **creature, an arrow or lava** this tick, or the
    episode ended, **break out of the tick loop** — the remaining primitives of the turn are discarded
    and the next turn begins. `results.interrupts` counts flinches. Starvation damage does **not**
    flinch (a zeroed vital would otherwise burn the entire turn budget two ticks at a time).

The flinch rule is the game's reactivity: a fight or an ambush costs you a whole turn of planning, and
a cog that sleeps in the open loses a turn every time something bites it.

### Visibility — the exact 9 × 9 rule

`viewSize = 9`. The view is the 9 × 9 square of world cells centred on the cog, **in world
orientation** (not rotated to the cog's heading — Crafter's own convention, and the one an LLM reads
without a coordinate transform, since `move_up` and the row above are then the same direction). Cells
outside the grid cannot occur, because the bedrock ring is inside the world. The cog's own cell reads
`@`; a cell holding a creature reads that creature's glyph; otherwise the terrain glyph.

**There is no occlusion.** Everything in the 9 × 9 box is visible, night or day. This is a documented
divergence from nothing — Crafter has no line-of-sight either — and it is what keeps the sim integer,
fast and hash-stable.

The **known map** is a 64 × 64 array of last-observed terrain plus the tick it was last observed. A
cell never in a view stays `?` forever. A cell observed and left behind keeps its last observed
terrain, which means a remembered cow is stale and a remembered `stone` may since have been mined by
nobody at all — the cog is told how stale (`seen_tick`) and the game does not hide it. **Creatures are
never remembered**: they appear only in `view` and in `threats`, both of which are current.

### Scoring formula and sign

At the end of the episode:

```
achievementsUnlocked = count(i in 0..21 where achievementUnlocked[i])     (0 .. 22)
survivalTicks        = finalTick                                          (1 .. 1344)

scores[0] = 10_000 * achievementsUnlocked + survivalTicks
```

**Sign: higher is better, and every term only ever adds.** `scores[0]` is never negative; the minimum
is `1` (a cog that died on tick 1 having done nothing) and the maximum is
`10_000 × 22 + 1344 = 221_344`. There is no death penalty term: dying stops the clock, which already
caps `survivalTicks`, and a second penalty would let a cog that hid under a stone slab all night
outrank one that opened the tech tree and got eaten on night four.

**The ordering is strictly lexicographic, by construction**: one more achievement is worth 10 000 and
the largest possible survival term is 1344 < 10 000, so **achievements always dominate** and survival
is purely the tie-break. That is the idea's own sentence — "how many of 22 achievements you unlock
before you starve" — as an integer.

**The league ranks by `results.scores[0]`.** With one seat, every episode is a solo run and the
platform's Elo is computed from these per-episode per-seat numbers; a policy climbs by unlocking more
achievements across more seeds. `results.win[0]` is `achievementsUnlocked >= parAchievements` (a
variant constant: 8 in `standard`, 6 in `longnight`) — a "did the cog clear the bar" flag, not a duel
— and **`results.winner` is `0` when `win[0]` is true and `null` otherwise** (there is no opponent, so
the only honest winner is the seat itself or nobody).

**Reconciling with the paper's geometric mean, explicitly.** Crafter's published score
`S = exp( (1/22) · Σ_i ln(1 + 100·p_i) ) − 1`, where `p_i` is the *success rate* of achievement `i`
across a run of episodes, is a **cross-episode aggregate**: a single episode has no success rate, only
a boolean per achievement. This coworld therefore does two things and conflates neither:

1. **Per episode** it reports the integer above, which is what a league round can rank. It also
   reports the raw material the aggregate needs: `achievementUnlocked[22]` (booleans, canonical order)
   and `achievementTick[22]`.
2. **Across episodes** the paper's formula is computed from those arrays — by the verifier at phase 60
   over a division's completed episodes, and by `tools/crafter_score.py` (Python 3 stdlib, shipped in
   the repo) over a directory of `results.json` files. `docs/RULES.md` states the formula, states that
   it needs ≥ 10 episodes to mean anything, and states that it is **not** what the ladder ranks.

**Measured but never scored:** `survivalTicks` beyond its tie-break role, `cellsSeen`, `damageTaken`,
`damageDealt`, `zombiesKilled`, `skeletonsKilled`, `cowsEaten`, `blocksMined`, `blocksPlaced`,
`itemsCrafted`, `ticksAsleep`, `interrupts`, `primitivesExecuted`, `actionsDropped`,
`macrosUnreachable`, `repliesRepaired`. All are in `results`, on the endcard and in the feed. Paying
for any of them directly would let a policy farm the metric (mine and re-place the same stone forever);
§Out of scope records the decision.

**Integrity (the idea's note), decided.** "Seeded worlds" is implemented as: the episode `seed` is
randomised by the runner, recorded in the replay and in `results.seed`, and **never appears in any
observation or prompt**. The seat never sees an unexplored cell, a noise-field value, a creature's HP,
a future spawn draw, its own score, or its own real player name. "Replay verification" is the
starter's per-tick `gameHash` chain, re-derived in the browser by the same sim module (§Server →
Determinism).

### Variants

Both are `num_agents: 1`, `maxTurns: 56`, `turnTicks: 24`, `maxTicks: 1344`.

| Variant | `dayLength` / `dayFraction` | `maxZombies` | `maxCows` | `mountainThreshold` | `parAchievements` |
|---|---|---|---|---|---|
| `standard` | 192 / 128 | 8 | 12 | 700 | 8 |
| `longnight` | 160 / 80 | 12 | 8 | 660 | 6 |

`standard` is the canonical Crafter world: seven day/night cycles, twice as much day as night, plenty
of cows. `longnight` is the survival-pressure variant the idea's "night-survival tension" asks for:
half the episode is dark, half again as many zombies, fewer cows — and, so the tech tree stays
reachable in the dark, a lower mountain threshold that pushes stone, coal and iron closer to the
surface. Nothing else differs; the achievement list, the recipes, the vitals and the action set are
identical, so the two variants are directly comparable.

### End conditions and legal `results.reason` values

The episode ends at the first of: **death**, **all twenty-two unlocked**, the **turn cap**, the **tick
cap**, or the **wall-clock stop**.

- **Death** — `health <= 0` at tick step 9. Settles immediately. `endRule = death`, `deathCause` set.
- **All unlocked** — `achievementsUnlocked == 22`. Settles immediately; there is nothing left to do
  and a triumphant early finish should read as one. `endRule = allUnlocked`.
- **Turn cap** — `turnsPlayed == maxTurns` (56). `endRule = turnCap`.
- **Tick cap** — `tick == maxTicks` (1344). Reachable only if no turn ever flinched, in which case it
  coincides with the turn cap; it is kept as an independent guard so no arithmetic error can produce
  an unbounded loop. `endRule = tickCap`.
- **Wall-clock stop** — the engine's `wallClockBudgetSeconds` guard, the starter's check at
  `src/ctf/server.nim:1407-1417`, kept. `endRule = wallClock`.
- **Fault** — an unrecoverable server-side error. `endRule = fault`.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the episode finished on its own terms: `death`, `allUnlocked`, `turnCap` or
  `tickCap`. The healthy value, and the one phase 60 check 4 requires. **A death is `complete`, not a
  failure**: dying of a zombie bite on night four having unlocked twelve achievements is the game
  working.
- **`deadline`** — the wall-clock stop fired (`endRule = wallClock`). Everything unlocked so far still
  scores and the results document is complete. **Declared acceptable** by this design note for phase
  60 check 4, but it should be unreachable in practice: the budget guard (§Decisions) drops the seat
  to scripted play two turns before the stop, and scripted turns cost microseconds.
- **`fault`** — `endRule = fault`. Always a defect; CI asserts it never occurs on the fixture seeds.

`endRule` is its own closed enum — `death | allUnlocked | turnCap | tickCap | wallClock | fault` —
declared in the manifest's `results_schema` and asserted by `tests/test_crafter_engine.nim`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes the seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {forager, wanderer}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=forager` (the starter's "anything unrecognised is the published default" rule,
`src/ctf/baselines.nim`). **A scripted policy seated as a champion is a failure state.**

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/crafter/anthropic_api_key` — the hive
2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/crafter_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"forager"|"wanderer"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at 64 runes, then acknowledge
frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3 close-frame race:
whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/crafter/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

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
- A system prompt demanding the reply **begins with `{`**, **plus the assistant-turn prefill of `{`**
  (both Anthropic Messages and Bedrock invoke accept it), the prefill re-prefixed before parsing and
  guarded against a provider that echoes it (the procgen 0.1.2 `cut off at max_tokens` scar — the fix
  is the prefill, never a bigger cap).
- `extractJsonObject` (`src/ctf/directives.nim` — outermost balanced `{…}`, fence-tolerant, tolerant
  of trailing prose) and `truncateRunes` / `sanitizeSay` / `sanitizeNote` unchanged.

### Cadence, the per-turn call budget, and the wall-clock arithmetic

One command turn every ≤ 24 ticks; **at most 56 turns per episode**. **The per-turn LLM call budget is
exactly ONE request, plus at most ONE retry** — there is a single seat, so the starter's
one-parallel-batch-per-turn machinery (`src/ctf/decide.nim:427`) carries a batch of one and is
otherwise untouched. **At most `56 × 2 = 112` provider calls per episode**, and never more than one in
flight.

```
attempt1Ms                          6.0 s   (whole seconds - sim_config.nim:696-706 rejects otherwise)
retryMs                             3.0 s   (whole seconds; attempt1Ms + retryMs <= turnBudgetMs - :691)
turnBudgetMs                        9.5 s   (monotonic deadline around the whole turn)
turnSpacingMs                       2.6 s   -> 1 seat x 60/2.6 = 23 req/min  (sidecar cap: 30)

56 turns x max(spacing 2.6 s, latency ~3.4 s)  typical            = 190 s
56 turns x turnBudgetMs 9.5 s, absolute worst                     = 532 s
1344 ticks, <= 26 creatures, 64x64 integer Nim, fastMode          =   2 s
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at       =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)     =  20 s
                                                                  -------
typical total                                                     = 227 s   < 720 s
absolute worst case (532 + 2 + 100 + 20)                          = 654 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                           = 660 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 660 and `tests/test_crafter_manifest.nim` asserts it. The typical figure
is conservative: a cog that dies on night two plays fewer than 56 turns.

**Rate guard.** `turnSpacingMs` pins the steady state at 23 req/min, but a run of retrying turns
issues two requests each. The engine therefore keeps a **rolling 60 s request counter**: if issuing the
next request would push the trailing-60 s count above **28**, that turn skips the call and takes the
`forager` plan with `cause = "rate_guard"`. Bounded, logged, never a sleep on the episode's critical
path (the raid round 2 sidecar-throttle scar).

`fastMode: true` in every variant, as in the starter's paintball variant: the seat sends no per-tick
inputs (the server computes every primitive), so the Sprite v1 Ready packet's dead-reckoning hazard
cannot arise.

### Degrade, never hang

Every wait is bounded: the two request deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 9.5 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop,
and ctf's `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On the seat's timeout or parse failure: **retry once**; on the second failure that turn's plan becomes
the **`forager`** scripted plan computed inside the game (the same proc the `forager` baseline uses —
imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns` counts them. The attempt-1 notice says **`will retry`**; only
a genuine second failure logs **`falling back`** (the pommerman 0.1.1 phase-60 grep scar; the
starter's two phrasings live at `src/ctf/decide.nim:463` and `:491`).

**No failure mode leaves the cog without an action.** The tick loop always has a primitive: the turn's
queue, else `noop`, which is a legal state that costs a tick and nothing else. A seat that never
connects is reported once to `COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload —
exactly `{"message", "failed_policy_index"}`, nothing else — and the episode plays out scripted.

**The episode settles early rather than overrunning**: death ends it on the tick it happens, the
twenty-second achievement ends it immediately, and the budget guard (`src/ctf/decide.nim:328-346`,
kept) switches the LLM off for the rest of the episode the moment two more full turns would not fit
inside `wallClockBudgetSeconds`, so the episode ends `complete`, not `deadline`.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **the cog knows what it has seen, what it is carrying, and what it has already
done.**

**Visible.**

- **The rules of the world, once, at registration** — `worldSize` 64, `viewSize` 9, the glyph legend,
  the seventeen actions and what each does, the six recipes and their costs, the vitals and their
  drain rates, `turnTicks`, `maxActionsPerTurn`, the fact that lava kills instantly, and the fact that
  taking a hit ends the turn. Static; afterwards referred to by id.
- **The 9 × 9 egocentric window**, `view`, as nine strings of nine glyphs, **world-oriented**, cog at
  the centre reading `@`. This is exactly the idea's "per-tick discrete over a 9×9 local view", and
  exactly what the viewer's inset draws.
- **A 16 × 16 region map**, `region` — the 64 × 64 known map downsampled 4 × 4, each region showing the
  single most *notable* terrain it is known to contain, by the priority
  `D > i > c > ! > ~ > T > # > t > f > p > Y > = > , > . > ?`. Sixteen strings of sixteen glyphs: 272
  characters instead of the 4160 a full known map would cost every turn. The seat therefore has a
  usable sense of "where the mountains are" without the prompt exploding.
- **`nearest`** — a fixed dictionary of the closest **known** cell of each of `tree`, `water`, `stone`,
  `coal`, `iron`, `diamond`, `lava`, `table`, `furnace`, `ripe_plant`, each `{x, y, d}` with `d` the
  Chebyshev distance, or `null` if never seen. This is what makes `goto` usable and it is the single
  most load-bearing field in the observation.
- **`landmarks`** — up to **24** other known notable cells, `{what, x, y, d, seen_tick}`, sorted
  ascending by `d` then `(y, x)`.
- **`threats`** — every creature **currently in the 9 × 9 view**, `{what, x, y, d}`. Creatures are
  never remembered outside the view.
- **The cog's own state** — `x`, `y`, `facing`, `asleep`, the four vitals, the six inventory counts,
  the six tool booleans, `near.table` / `near.furnace`, and `ahead`: the glyph, the name and the
  coordinates of the cell it faces.
- **Time** — `day`, `phase` (`day`|`night`), `ticks_to_phase_change`, `ticks_left`, `turns_left`.
- **Its own achievement state** — `achievements.unlocked` (ids, canonical order),
  `achievements.locked` (the rest, so the model knows what is left), `count`, `of`.
- **Its own last turn** — `last_plan.executed` (the primitives that actually ran), `truncated`,
  `dropped`, `unreachable`, `interrupted` (`""`, `hurt_by_zombie`, `hurt_by_skeleton`, `hurt_by_arrow`
  or `lava`), and `notes` echoed back.

**Hidden.** The episode **seed**; every cell never observed; every noise-field value and every
generator threshold; creature HP, spawn schedule and future moves; the `1-in-10` sapling draw; the
whole of the world outside the known map; the cog's own **score**; `parAchievements`; and its own real
player/policy name. Nothing about identity ever reaches a prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `notes`) into
the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "Alpha",
  "turn": 23, "tick": 541,
  "world": {"size": 64, "view": 9, "region": 16,
            "legend": {".": "grass", ",": "sand", "~": "water", "#": "stone",
                       "=": "path", "T": "tree", "c": "coal", "i": "iron",
                       "D": "diamond", "!": "LAVA (instant death)", "B": "bedrock",
                       "t": "table", "f": "furnace", "p": "sapling", "Y": "ripe plant",
                       "U": "cow", "Z": "zombie", "K": "skeleton", "^": "arrow",
                       "@": "you", "?": "never seen"}},
  "time": {"day": 3, "phase": "night", "ticks_to_phase_change": 37,
           "ticks_left": 803, "turns_left": 33},
  "agent": {"x": 30, "y": 27, "facing": "down", "asleep": false,
            "health": 6, "food": 4, "drink": 7, "energy": 3,
            "ahead": {"glyph": "T", "what": "tree", "x": 30, "y": 28}},
  "inventory": {"wood": 3, "stone": 5, "coal": 1, "iron": 0, "diamond": 0, "sapling": 1},
  "tools": {"wood_pickaxe": true, "stone_pickaxe": true, "iron_pickaxe": false,
            "wood_sword": true, "stone_sword": false, "iron_sword": false},
  "near": {"table": true, "furnace": false},
  "view": ["..T..#####",
           "..T...####",
           "....@.###",
           "..U....##",
           "........#",
           "...Z.....",
           ".........",
           "..~~.....",
           "..~~~...."],
  "region": ["????????????????",
             "????????????????",
             "????...TT???????",
             "????..t.#???????",
             "????.@..##??????",
             "????~~..#c??????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????",
             "????????????????"],
  "nearest": {"tree": {"x": 30, "y": 28, "d": 1},
              "water": {"x": 28, "y": 34, "d": 7},
              "stone": {"x": 35, "y": 25, "d": 5},
              "coal": {"x": 39, "y": 24, "d": 9},
              "iron": null, "diamond": null, "lava": null,
              "table": {"x": 29, "y": 26, "d": 1},
              "furnace": null, "ripe_plant": null},
  "landmarks": [{"what": "tree", "x": 30, "y": 26, "d": 1, "seen_tick": 512},
                {"what": "stone", "x": 35, "y": 25, "d": 5, "seen_tick": 498}],
  "threats": [{"what": "zombie", "x": 31, "y": 30, "d": 3},
              {"what": "cow", "x": 28, "y": 28, "d": 2}],
  "achievements": {"count": 11, "of": 22,
                   "unlocked": ["collect_wood", "place_table", "eat_cow", "collect_sapling",
                                "collect_drink", "make_wood_pickaxe", "make_wood_sword",
                                "place_plant", "collect_stone", "place_stone",
                                "make_stone_pickaxe"],
                   "locked": ["defeat_zombie", "eat_plant", "defeat_skeleton",
                              "make_stone_sword", "wake_up", "place_furnace", "collect_coal",
                              "collect_iron", "make_iron_pickaxe", "make_iron_sword",
                              "collect_diamond"]},
  "last_plan": {"executed": ["move_down", "do", "do", "do", "do"],
                "truncated": false, "dropped": 0, "unreachable": 0,
                "interrupted": "hurt_by_zombie"},
  "notes": "table at (29,26). stone ridge NE around (35,25), coal at (39,24). water S at (28,34). need furnace + iron."
}
```

Reading it: the cog stands at `(30, 27)` facing down at a tree; it has a table one cell away, so it
can craft; it is night, a zombie is three cells south, it has 6 health and a stone pickaxe, and its
last turn was cut short by a bite. Eleven of twenty-two are done and the eleven that are left are
listed for it.

Field rules. `view` is always **9 strings of 9 characters**; `region` is always **16 strings of 16
characters**; `nearest` always has all ten keys (value or `null`); the array shapes never change.
Glyphs are exactly the closed set in the legend. `agent.facing` is one of `up|down|left|right`.
`landmarks` is at most 24 entries and never repeats a cell already in `nearest`.
`last_plan.executed` lists the **primitives** that actually ran — macros already expanded — so the
seat can see a `goto` get cut off rather than guess.

### Reply schema and per-field caps

```json
{"actions": [{"act": "goto", "x": 35, "y": 25},
             {"act": "do", "n": 4},
             {"act": "make_stone_sword"}],
 "say": "stone ridge is five cells NE; mining it then arming up before the zombies find me",
 "notes": "table (29,26). coal (39,24). after stone sword: furnace, then hunt iron in the cave."}
```

| Field | Type | Cap / domain |
|---|---|---|
| `actions` | array | **≤ 12 entries** (`maxActionsPerTurn`). Entries past the cap are dropped and counted in `actionsDropped`. Absent or empty = the turn is 24 `noop` ticks, and the reply is still **usable** |
| `actions[].act` | string | **≤ 20 runes**; enum = the **17 primitives** by name (`noop`, `move_left`, `move_right`, `move_up`, `move_down`, `do`, `sleep`, `place_stone`, `place_table`, `place_furnace`, `place_plant`, `make_wood_pickaxe`, `make_stone_pickaxe`, `make_iron_pickaxe`, `make_wood_sword`, `make_stone_sword`, `make_iron_sword`) **plus 2 macros** (`goto`, `move`), lower-cased and `-`→`_` normalised before matching |
| `actions[].x`, `.y` | integer | required iff `act == "goto"`; **clamped to 0 … 63**; a non-integer or absent value **drops the entry** and counts in `repliesRepaired` |
| `actions[].dir` | string | required iff `act == "move"`; **≤ 5 runes**; matched case-insensitively against `up`, `down`, `left`, `right`, `u`, `d`, `l`, `r`, `n`, `s`, `w`, `e`; anything else drops the entry |
| `actions[].n` | integer | honoured **only** on `move` (1 … 12), `do` (1 … 12) and `sleep` (1 … 24); clamped into range; absent = 1; ignored on every other verb |
| `say` | string | **≤ 160 runes** (`MaxSayRunes`) — the cog thinking out loud; drawn in the spectator feed and in the replay, never fed back to the seat |
| `notes` | string | **≤ 400 runes** (`MaxNoteRunes`) — private scratchpad, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160` (`src/ctf/sim_types.nim:747, 794-795`),
which are a 10-character in-world shout and a short note. A cog narrating a survival run needs a
sentence, and a cog carrying its own map and tech plan between turns needs more than 160 runes, so
`MaxSayRunes = 160` and `MaxNoteRunes = 400` here, and `ShoutMaxChars` is deleted with the shout
mechanic (§Sim module → Deleted).

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded
error text — is truncated on RUNE boundaries** via the starter's `truncateRunes` / `runeSubStr`, never
by byte index. Byte truncation is what makes a replay that renders in a browser fail a strict UTF-8
parser; `tests/test_crafter_replay.nim` asserts it with 4-byte emoji sitting exactly on every cap.

Unknown top-level and per-action keys are ignored. A reply with a valid `say` but no `actions` is
**usable** (the turn is spent idling and the narration is delivered). A reply that is not a JSON object
is a parse failure. **Invalid actions are dropped, never rewritten**: turning a malformed `goto` into a
`move_down` could walk the cog into lava on the game's own initiative, so the entry is removed, counted
in `repliesRepaired`, and reported back as `dropped` next turn.

### System prompt (fixed, identical for both champions)

```
You are one cog alone in a 64x64 wilderness. You can see a 9x9 square around
yourself and nothing else. You are hungry, thirsty and tired, and monsters come
out at night. There are 22 things you have never done, and the ONLY thing that
is scored is how many of them you do before you die.

WHAT YOU GET EACH TURN
- "view": 9 rows of 9 characters, the world around you, NORTH UP. You are the @
  in the middle. Row 0 is north, the last row is south.
- "region": the whole 64x64 world you have explored, squashed 4x4 into 16x16.
  ? means you have never been there.
- "nearest": exact x,y of the closest thing of each kind you have SEEN. This is
  what you aim "goto" at.
- "agent": your x, y, facing, and your four bars: health, food, drink, energy,
  each 0 to 9. Any bar at 0 eats your health until you die.
- "achievements": what you have done and what is LEFT. The list of what is left
  is your to-do list. Work down it.

GLYPHS
  .  grass   ,  sand    ~  water    #  stone    =  cave floor   T  tree
  c  coal    i  iron    D  diamond  !  LAVA (walking into it kills you instantly)
  t  table   f  furnace p  sapling  Y  ripe plant  B  world edge
  U  cow     Z  zombie  K  skeleton ^  arrow    @  you    ?  never seen

THE TECH TREE (each step needs the one before it)
  chop a tree            -> wood
  place_table (1 wood)   -> you can now craft, but only while STANDING NEXT TO IT
  make_wood_pickaxe (1 wood)      make_wood_sword (1 wood)
  mine stone (needs wood pickaxe) -> stone
  make_stone_pickaxe (1 wood + 1 stone)   make_stone_sword (1 wood + 1 stone)
  place_furnace (1 stone)
  mine coal (wood pickaxe), mine iron (STONE pickaxe)
  make_iron_pickaxe / make_iron_sword (1 wood + 1 coal + 1 iron, needs table
    AND furnace both within one cell of you)
  mine diamond (needs IRON pickaxe)

STAYING ALIVE
  drink: face water, "do". food: kill a cow ("do" it 2-4 times) or eat a ripe
  plant. energy: "sleep". Sleeping outdoors is how cogs die - wall yourself in
  with place_stone first, or dig into a hillside and seal the hole.
  Zombies spawn at night on grass and burn up at dawn. Skeletons live in caves
  and shoot arrows down straight lines.

WHAT YOU SEND
One JSON object with up to 12 actions. They run one per tick, in order, up to 24
ticks, then you are asked again. ANY hit you take ENDS YOUR TURN EARLY and
throws away the rest of your plan - so do not plan 24 ticks of mining with a
zombie on screen.
  {"act":"goto","x":35,"y":25}   WALK THERE. Shortest path through ground you
      have already seen; it will not path through water, lava, rock or the
      unknown. It stops ON the target if you can stand there, otherwise NEXT TO
      it, FACING it - which is exactly what you want before "do".
  {"act":"move","dir":"up","n":4}  step up to 4 times north. "move" also TURNS
      you: moving into a wall just turns you to face it.
  {"act":"do","n":4}   use the cell you are FACING, 4 times: chop, mine, drink,
      or hit whatever is standing there.
  {"act":"sleep","n":12}  sleep 12 ticks. +1 energy a tick. A zombie that bites
      you while asleep does 5 damage, not 2.
  {"act":"place_stone"} {"act":"place_table"} {"act":"place_furnace"}
  {"act":"place_plant"} {"act":"make_wood_pickaxe"} ... all 17 by name.

HOW YOU ARE SCORED
Only the count of achievements. Surviving longer is the tie-break, and only the
tie-break. A cog that hides in a hole all episode scores almost nothing.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the
character { and end with }. No prose, no markdown, no code fences.
{"actions":[{"act":"goto","x":35,"y":25},{"act":"do","n":4}],"say":"<=160 chars","notes":"<=400 chars"}
```

### Champion #1 — `crafter-techtree` (owner **daveey**), `PLAYER_PROMPT`

```
Climb the tree. Everything else is logistics.
Your to-do list is "achievements.locked", top to bottom - it is already in
dependency order. Every turn, find the FIRST item on it you could make progress
on this turn, and spend the whole turn on that one item. Never spend a turn
"getting ready".
Turn 1: goto the nearest tree, do x5, place_table, make_wood_pickaxe,
make_wood_sword. That is one turn and it clears four achievements. Do it.
Then, in this order, and do not skip:
1. stone: goto "nearest.stone", do x3, then place_stone once (that is a free
   achievement you already have the material for).
2. table again: you will have walked away from the first one. Carry 2 spare wood
   and place_table WHERE YOU ARE MINING. A table costs one wood; walking back
   costs a whole turn.
3. make_stone_pickaxe, make_stone_sword, place_furnace - all next to that table.
4. coal, then iron. Both are in the grey "#" country in "region"; iron sits
   deeper, near "=" cave floor. If "nearest.iron" is null, goto the far edge of
   the stone you know and mine INTO it: mining stone makes cave floor you can
   walk on, so you tunnel with do x3, move, do x3, move.
5. make_iron_pickaxe and make_iron_sword next to table AND furnace - place a new
   pair down in the tunnel rather than walking home.
6. diamond. It is the deepest thing in the mountain. Once you own the iron
   pickaxe, tunnel toward the highest "#" region and keep going.
Keep bars off zero and nothing more: drink when drink <= 3, eat when food <= 3,
sleep ONLY when energy <= 2 and only after sealing yourself in with place_stone
on every open side. Any bar at 4 or more is a bar you are not allowed to spend a
turn on.
Never walk onto "!". Never plan more than 8 ticks when "threats" is non-empty -
you will just lose them to the interrupt.
Rewrite "notes" every turn as: table x,y - furnace x,y - the next item on the
list - the coordinates you are tunnelling toward.
```

### Champion #2 — `crafter-homesteader` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Build a base, then raid out of it. A dead cog unlocks nothing.
Turn 1-2: find the spot. You want a cell with a tree and water both inside 8,
and stone inside 12 if you can get it. Chop 4 wood, place_table, make both wood
tools. Say where the base is and never forget it.
Every turn, run this checklist IN ORDER and act on the first thing that is true:
- health <= 3, or a Z or K in "threats" within 2: fight or wall. If you have a
  sword and it is one zombie, face it and do x3 - a dead zombie is an
  achievement. If it is two, or you have no sword, place_stone into the gap and
  walk away.
- drink <= 4: goto nearest water, do until drink is 9. Water is free and never
  runs out; being at 4 is a bug in your plan.
- food <= 4: nearest U, goto it, do x4. If you have a ripe plant "Y", eat that
  instead - it is a whole achievement and it grows back.
- phase is "night" and you are not sealed: seal. place_stone on every open
  neighbour you can afford, then sleep n=16. Waking with energy 9 is the
  "wake_up" achievement and you will not get it any other way.
- sapling in inventory and you have never placed one: place_plant on grass right
  outside the door, then remember where - you are coming back for the fruit.
- otherwise: raid. One trip out, one objective, back before dark. The objectives
  in order are stone, then coal, then iron, then diamond, and you take the table
  with you (2 wood) so you can craft in the field.
Rules you never break: never step on "!"; never sleep in the open; never let two
bars sit under 3 at once; never spend the last three turns of the episode
walking - spend them doing anything at all that is still on the locked list,
because an achievement unlocked on the last tick counts exactly the same.
"notes" is your base: base x,y - what is stored - what is still locked - where
you were heading.
```

### The driver (deterministic, shared by every policy)

`src/crafter/driver.nim` — the starter's `src/ctf/control.nim` (directive → per-tick actuation),
retargeted from pixel steering to a **primitive queue**. It is the **only** producer of primitives,
and it contains no randomness.

| Action | Expands to |
|---|---|
| any of the 17 primitives | itself, once — or `n` times for `do` and `sleep` |
| `move dir n` | up to `n` copies of `move_<dir>` |
| `goto x y` | the `move_<dir>` primitives that walk the BFS path below |

**The `goto` BFS**, run against the **known map as of turn start**:

- Nodes are cells; edges are 4-adjacency in the fixed order **up, right, down, left**.
- A cell is **traversable** iff its known terrain is `grass`, `sand` or `path`, and it is not known to
  hold a hostile (a zombie or skeleton currently in `threats`). `?`, `water`, `lava`, `stone`, `tree`,
  `coal`, `iron`, `diamond`, `bedrock`, `table`, `furnace`, `sapling` and `ripe plant` are **not**
  traversable — in particular the driver **never** routes through lava and never routes through the
  unknown.
- Breadth-first from the cog's cell; ties broken by the neighbour order above, so the path is unique
  for a given known map.
- If the **target** is traversable, the path ends **on** it. If the target is not traversable but is
  4-adjacent to some reached cell, the path ends on the nearest such cell and a final `move_<dir>`
  toward the target is appended — which turns the cog to face it without moving (the target is not
  walkable), leaving it exactly positioned for `do`. If neither, the macro yields **zero** primitives
  and counts as `unreachable`.
- Bounded by `macroPrimitiveCap = 24` primitives; the whole turn's queue is then truncated to
  `turnTicks = 24`.

The driver never invents an action the schema does not express and never produces a step into a cell
it believes is lava — but it makes no promise about a cell the cog has never seen, which is why
walking into the unknown costs an explicit `move`.

### Scripted baselines (both shipped as league fillers; `forager` is also the server-side fallback)

`src/crafter/baselines.nim`, the starter's module retargeted. Both emit the **same** reply objects an
LLM does, through the same validator, which is what makes the bounded-orders test meaningful. Neither
ever emits `say` or `notes` — a baseline that narrated would make the feed lie about which seats are
LLMs.

**`forager`** — `PLAYER_SCRIPTED=forager`, and the fallback. A deterministic priority ladder. Every
turn, the **first** matching rule wins and emits at most 12 actions:

1. **Under attack.** A zombie or skeleton within Chebyshev 2. If the cog faces it: `{"act":"do","n":3}`.
   Else if `stone >= 1` and the cell between them is placeable: `move` to face it, `place_stone`.
   Else `goto` the known traversable cell that maximises the minimum distance to every entry in
   `threats` (ties by BFS distance, then `(y, x)`).
2. **Thirst.** `drink <= 3` and `nearest.water` is not null: `goto` it, then `{"act":"do","n":9-drink}`.
3. **Hunger.** `food <= 3`: if `nearest.ripe_plant` is known, `goto` it and `do`; else `goto` the
   nearest cow in `threats` (cows are creatures, so they are only targeted when in view) and
   `{"act":"do","n":4}`; else fall through.
4. **Night shelter.** `phase == "night"` and the cog has an open (traversable) neighbour: `place_stone`
   toward each open neighbour, up to `min(4, stone)` of them, then `{"act":"sleep","n":12}`.
5. **The tech ladder.** The first unmet step, exactly the order of §The twenty-two achievements:
   `wood < 1` → `goto nearest.tree`, `{"act":"do","n":5}`;
   no table and `wood >= 1` → `place_table`;
   no `wood_pickaxe` → `make_wood_pickaxe`; no `wood_sword` → `make_wood_sword`;
   `stone < 1` → `goto nearest.stone`, `{"act":"do","n":3}`;
   never placed a stone → `place_stone`;
   no `stone_pickaxe` / `stone_sword` → craft (walking to `nearest.table` first if `near.table` is
   false);
   no furnace and `stone >= 1` → `place_furnace`;
   `coal < 1` → `goto nearest.coal`; `iron < 1` → `goto nearest.iron`;
   no `iron_pickaxe` → craft; no `iron_sword` → craft;
   `diamond < 1` → `goto nearest.diamond`.
6. **Sapling.** `sapling >= 1` and `place_plant` never unlocked → `place_plant` (walking to the nearest
   known `grass` first if needed).
7. **Explore.** `goto` the known traversable cell adjacent to the most `?` regions (ties by BFS
   distance, then `(y, x)`), then `{"act":"move","dir":<outward>,"n":3}` so the plan actually crosses
   into the unknown.

`forager` never routes through lava (lava is not traversable to the BFS) and never sleeps with an open
neighbour it can afford to seal. It has no notion of the day/night clock beyond rule 4 and no notion of
the diamond except as the last rung — which is the point of shipping it as the floor.

**`wanderer`** — `PLAYER_SCRIPTED=wanderer`. The reactive control, four lines and no memory: every turn
emit twelve actions alternating `{"act":"move","dir":<facing>,"n":2}` and `{"act":"do"}`, rotating
`facing` clockwise (`up → right → down → left`) whenever the cell ahead is not traversable in the
current `view`. It has no BFS, no tech ladder, no vitals logic and no shelter. It chops a tree by
accident, occasionally drinks, and dies on the first or second night. It is the control that answers
"did the LLM actually play?"

Like the starter's `DefaultBaselineParams` (`src/ctf/baselines.nim:38`), `forager`'s tunables (the
thirst/hunger thresholds `3`, the shelter stone budget `4`, the sleep length `12`, the explore step
count `3`, and whether the frontier score breaks ties by distance or by `(y, x)`) are a parameter
object chosen by `tools/tune_baselines.nim`'s sweep, not guessed;
`tools/ci/baseline_tuning.json` records the sweep's pick and `tests/test_crafter_tuning.nim` asserts
the shipped defaults still equal it.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/crafter/`. The fork is a rename sweep
(`ctf` → `crafter`, `CTF_WIRE` → `CRAFTER_WIRE`; a CI grep asserts no `ctf_` / `CTF_` identifier
survives outside comment history) plus the changes below. **The same modules compile twice**: natively
into `/bin/crafter` for the server, and to wasm through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason a Python/JAX engine is not an option here.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/crafter/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1407-1417`, and the `Ping → Pong` branch in `websocketHandler` (kept verbatim — lux-ai 0.1.0 / snake-royale 0.1.0 both lost it; and **no** `kind != TextMessage` guard, which would drop the seat's binary registration frames) |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/crafter/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` (`replays.nim:142`) → **`CrafterReplayMagic = "COWLDCRF"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/crafter/` (`control.nim` → `driver.nim`) | **fork**, retargeted not rewritten | the per-turn batch (`decide.nim:427`), the two deadlines, `turnSpacingMs` (`decide.nim:384-389`), the budget guard (`decide.nim:328-346`), tolerant parsing, the rune caps, the fallback ladder and its two log phrasings (`decide.nim:463`, `:491`) |
| `src/ctf/sim_state.nim` → `src/crafter/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/crafter/roster.nim` | **fork**, three named edits below | join/auth/identities/`IdentityNames` (`roster.nim:64`), **`recordAchievement` (`:640-648`) and the `earnedAchievements` serialisation (`:828`) — kept and used as-is**, and the results JSON builder (`squadResultsJson`, `:650`) |
| `src/ctf/events.nim` → `src/crafter/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/crafter/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline — retargeted fields, same structure |
| `src/ctf/global.nim` → `src/crafter/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/crafter/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24` (`:376`), the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 160`, `MaxNoteRunes = 400`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/crafter/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, and the validators at `:688-713` (whole-second `attempt1Ms`/`retryMs`, `attempt1Ms + retryMs ≤ turnBudgetMs`, positive `wallClockBudgetSeconds`) — all kept, and §Decisions' numbers are chosen to satisfy them |
| `src/ctf.nim` → `src/crafter.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so the world generator follows the final seed |
| `src/paintball_player.nim` → `src/crafter_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** (40 022 bytes, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`) | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/crafter_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling, and its `docker cp` source path changes from `/workspace/ctf/replay-viewer/dist/.` to `/workspace/crafter/replay-viewer/dist/.` |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_red.png`, `data/soldier_red_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling and vision cones, **fog-of-war
raycasting and the first-person raycast pipeline** (replaced by the plain 9 × 9 window above and a 2-D
inset), spray cans, floor paint and the paint grid, the paint buff, King of the Hill and `hillTicks`,
the `resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the barrage, med kits,
shields, cardboard barriers, trenches, perks, handicaps, lives and respawns, **teams and four-team
free-for-all** (there is one seat), **shouts-as-cog-speech and `ShoutMaxChars`**, ctf's own fifteen
paintball achievements (`src/ctf/sim.nim:2900-2932` — the *ledger* survives, the *ids* do not), campaign
mode, `maxGames > 1` side-swapping, and **all of the pixel-space map machinery**: `arena.nim`'s wall
masks and pixel queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`,
`tools/mapkit.nim`, `tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`,
`docs/pool-review.html`, `docs/MAPKIT.md`. The world here is a 64 × 64 integer cell grid built by a
seeded noise generator in code; every one of those is a config surface the survival rules would
otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`,
`medkit`, `shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `*_front_gun`,
`soldier_{blue,green,yellow}*`, `rig_real/`) and the blue/green/yellow locker-room webps — there is one
cog and it is red.

### New modules

- `src/crafter/world.nim` — the terrain enum, the glyph/walkable/mineable tables, the **integer
  value-noise** generator and the four fields, the five-step playability post-pass, the 64 × 64 grid
  type, 4-adjacency in the fixed order up/right/down/left, the BFS used by `goto` and by `forager`,
  the 9 × 9 window, and the 16 × 16 region downsample with its priority order. Pure integer; no pixie,
  no pixel queries.
- `src/crafter/agent.nim` — the cog record (position, facing, asleep, vitals, inventory, tools), the
  seventeen primitives of tick step 3 with their exact effects, the six recipes with their adjacency
  requirements, and the vitals block of tick step 4.
- `src/crafter/creatures.nim` — the creature record and stable ordering, the bounded spawn attempts of
  tick step 6, the movement and attack rules of tick step 7, arrow flight, and the dawn burn.
- `src/crafter/achievements.nim` — the twenty-two ids in canonical order, their predicates, the
  `achievementTick[22]` array, and the bridge to the starter's `recordAchievement`.
- `src/crafter/sim.nim` — the step loop of §The game exactly as numbered, `gameHash`, end evaluation,
  scoring, and the seat's observation builder. Imports and re-exports the sim modules, as the starter's
  does, so `import crafter/sim` sees everything.

### Integer arithmetic and determinism

**All sim arithmetic is integer only** — cell coordinates, the noise lattice and its fixed-point
interpolation, vitals, tick counters, BFS distances, achievement ticks, scores. There is no floating
point anywhere in `sim.nim`, `world.nim`, `agent.nim`, `creatures.nim`, `achievements.nim`,
`driver.nim` or `baselines.nim`, and a test greps for it. That makes the native ↔ wasm hash chain
exact by construction — the reason the OpenSimplex noise Crafter uses is *not* what this game uses.

**One seeded source, and it is a hash, not a stream.** Every generated quantity — the four noise
fields, the ore draws, every spawn candidate, every creature step direction, and the 1-in-10 sapling
draw — is a read of the pure hash `mix64(seed, salt, …)` (splitmix64 over the mixed words), evaluated
independently. Nothing the policy does can shift a draw, reorder draws, or consume one out from under a
later tick: **the world of seed `s` is the same world no matter how the cog plays it**, which is the
strongest form of the idea's "seeded worlds" and what makes per-achievement success rates comparable
across policies. `tests/test_crafter_world.nim` asserts it by generating the same seed under three
different policy behaviours and comparing the full 64 × 64 grid byte for byte.

The seed is randomised in `src/crafter.nim` before `config.update` (the starter's rule), recorded in
the replay config and in `results.seed`. Two episodes with the same seed and the same plans are
byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDCRF`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, variant, `num_agents`, every rule constant, `players[].name`,
   `slots[]`, `fastMode`), then the record stream — the join record, **per-turn plan records** (the
   only inputs this game has), chat records (`register` / `directive` / `fallback` / `budget_guard` /
   `stop` / `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/crafter_replay.nim` — which imports the
   **same** `src/crafter/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `crafter_load_replay` runs `parseReplayBytes` + `initReplayRuntime`;
   `crafter_frame` re-steps the sim from the recorded plans and compares `sim.gameHash()` against the
   recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens
   and surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: `tick`; the cog's `(x, y, facing, asleep)`; `health`,
   `food`, `drink`, `energy`; the six inventory counts; the six tool bits; the 22-bit achievement mask;
   then every creature in stable order as `(kind, x, y, hp, lastAct)`; then a rolling terrain digest
   updated **incrementally** on every terrain mutation (mine, place, ripen) rather than by scanning
   4096 cells a tick — the digest is `terrainHash = mixHash(terrainHash, x, y, oldKind, newKind)`,
   seeded at generation by folding the whole grid once.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact cannot
   be re-derived from sim state, so the stop is written as one record applied by the *same proc* on
   record and on playback, and `tests/test_crafter_replay.nim` runs the record → re-derive check for
   **every** end reason (`death`, `allUnlocked`, `turnCap`, `tickCap`, `wallClock`, `fault`), not just
   the healthy one (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 1344 hashes + ≤ 56 plan records + ~70 chat records ≈ **26 KB**. Everything else — the
whole 64 × 64 world, every ore, every creature, every achievement tick — is re-generated in the browser
from the seed and the variant.

### Documented divergences (mirrored into `docs/PORTING-CRAFTER.md`)

1. **No `crafter` and no `craftax` dependency, and no bit-exactness with either.** Decided as a scoping
   rail before design. Crafter is Python (numpy, OpenSimplex, `imageio`); Craftax is JAX. Embedding
   either means a simulator that cannot compile to wasm, so the static replay viewer — a non-optional
   pin — would be impossible. No upstream code is vendored, no upstream numbers are claimed as
   reproduced, and no score from this coworld is comparable to a published Crafter or Craftax number.
   What is reproduced is the *problem*: a 64 × 64 procedural world, day/night, four vitals, the same
   seventeen actions by name, and **the same twenty-two achievements by name and in the same order**.
2. **Integer value noise, not OpenSimplex.** The generator is a hashed lattice with fixed-point
   bilinear interpolation, because a float noise field cannot be hashed identically native and in
   wasm. The resulting worlds are recognisably the same kind of world (grass plains, water, sand
   shores, forests, a mountain massif with caves, lava and ores at depth) and are not the same worlds.
3. **Episode length.** Crafter allows 10 000 steps; this game allows **1344**, because the seat is an
   LLM on a 720 s budget (§Decisions). The vitals drain rates, the day length and the ore depths are all
   scaled to that budget so the tech tree is genuinely completable — `tests/test_crafter_engine.nim`
   asserts a scripted solver reaches `collect_diamond` on at least one committed seed.
4. **Actions are batched under a driver, not stepped one per call.** The idea's "per-tick discrete"
   interface is preserved exactly as the seventeen primitives; what changed is *who calls it*. Up to
   twenty-four primitives per LLM turn under a deterministic driver, plus two macros (`goto`, `move`)
   and an `n` multiplier on `do`/`sleep`. One LLM call per primitive would be 1344 calls in a 720 s
   budget — impossible — and a policy that cannot express "walk over there" spends every turn walking.
   The **flinch rule** (tick step 12) is what keeps batching from removing reactivity.
5. **The symbolic observation.** The idea names "Craftax-Symbolic" as what makes LLM play feasible;
   this game's observation is a symbolic one (§Decisions), not a pixel array, and it adds a **region
   map** and a **`nearest` dictionary** that Crafter does not have — an LLM re-prompted fresh each turn
   has no hidden state, so the game keeps the memory for it. Partial observability is untouched: an
   unexplored cell stays `?` until the cog walks somewhere it can see it from, and creatures are never
   remembered.
6. **Reward shape.** Crafter's per-step reward is `+1` per new achievement with `±0.1` for health
   changes. The league needs one rankable integer, so §The game makes achievements the dominant term
   and survival the tie-break, and drops the health shaping entirely (it exists to shape RL gradients,
   not to rank policies).
7. **Trees are infinite; a key is not consumed by anything; mining stone leaves walkable `path`.**
   Crafter's semantics, stated because they are the ones an implementer guesses wrong.
8. **`maxGames = 1`** — the starter's multi-game episode is not used; a survival run has no side to
   swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with a variable turn length (the tick loop breaks early on a
   flinch or a death) and one seat in the batch.
2. **Registration interception** — the seat's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration, **not** applied as a shout and **not** written to the replay chat stream; the server
   writes a redacted `register` record instead (policy label and kind, never the prompt). The starter's
   "hold an unappliable registration and re-read it when the slot lands" behaviour is kept verbatim,
   and the server **logs loudly and refuses to start the game** when the joined seat has no register
   record (the grf-football 2026-08-27 silent-default scar). Any other chat text from the seat is
   dropped — the cog speaks through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop iteration
   (`server.nim:1407-1417`), kept, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wallClock`, and written as the load-bearing stop record of §Determinism point 5.

### The three named edits to `roster.nim`

1. **Alias.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → **`Alpha`** for the only
   seat. The `IdentityNames` array itself (`roster.nim:64-65`) is unchanged. Board labels and the label
   manifest inherit the two-name-space rule with no further change, and `showPlayerLabels` is false.
2. **Achievement ids.** `recordAchievement` (`:640-648`) is kept **verbatim**; only the id vocabulary
   changes, from ctf's fifteen paintball ids to the twenty-two of §The twenty-two achievements, plus
   the parallel `achievementTick[22]` array this fork adds beside `earnedAchievements`.
3. **`squadResultsJson` → `runResultsJson`** (`:650`) — one entry per seat, one entry in every
   seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a 64 × 64 cell grid, not a pixel arena.** `buildSpriteProtocolPlayerUpdates` emits
   cell-space coordinates; the raycast fov cache and shadowcasting are deleted and replaced by the
   9 × 9 window's boolean mask plus the known-map mask, which the viewer draws as the two-level fog
   wash. The board's **native size is 64 × 24 = 1536 × 1536 px**, one 24 px tile per cell.
2. **Terrain, creature and item pools.** New pools `TerrainBase` (a tile layer redrawn incrementally on
   mutation, never per-frame from scratch), `CreatureBase` (sized to 32) and `ArrowBase` (sized to 16),
   filled in the stable creature order and emitted incrementally like the starter's other object
   families.
3. **Baked terrain bed.** `arena_floor.png` is tiled and recoloured per terrain at install with pixie,
   exactly the way the starter bakes endzone paint, so the per-frame cost is the cog, ≤ 26 creatures,
   ≤ 16 arrows, the two fog masks and the overlays — never 4096 tile draws.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST` / `PORT`; the player
socket at `/player?slot=0&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset route:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for
the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). The player
websocket handler **closes unless the token matches the seat** (the certifier probes with a bad token —
cogame-flatland 0.1.1) and keeps the `Ping → Pong` branch. Global broadcasts are fire-and-forget so a
slow viewer can never stall the episode.

### Results document (closed schema; `runResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":                ["daveey"],
  "aliases":              ["Alpha"],
  "scores":               [120812],
  "win":                  [true],
  "winner":               0,
  "reason":               "complete",
  "endRule":              "death",
  "variant":              "standard",
  "seed":                 1734029581,
  "achievementIds":       ["collect_wood","place_table","eat_cow","collect_sapling",
                           "collect_drink","make_wood_pickaxe","make_wood_sword","place_plant",
                           "defeat_zombie","collect_stone","place_stone","eat_plant",
                           "defeat_skeleton","make_stone_pickaxe","make_stone_sword","wake_up",
                           "place_furnace","collect_coal","collect_iron","make_iron_pickaxe",
                           "make_iron_sword","collect_diamond"],
  "achievementUnlocked":  [true,true,true,true,true,true,true,true,false,true,true,false,
                           false,true,true,false,true,true,false,false,false,false],
  "achievementTick":      [14,19,88,131,52,20,21,140,-1,206,209,-1,-1,244,247,-1,262,318,-1,-1,-1,-1],
  "achievementsUnlocked": 12,
  "achievementsOf":       22,
  "parAchievements":      8,
  "survivalTicks":        812,
  "daysSurvived":         5,
  "nightsSurvived":       4,
  "deathCause":           "zombie",
  "finalHealth":          0,
  "finalFood":            4,
  "finalDrink":           6,
  "finalEnergy":          2,
  "invWood":              3,
  "invStone":             5,
  "invCoal":              1,
  "invIron":              0,
  "invDiamond":           0,
  "invSapling":           1,
  "toolsOwned":           ["wood_pickaxe","wood_sword","stone_pickaxe","stone_sword"],
  "cellsSeen":            1180,
  "cellsTotal":           4096,
  "damageTaken":          17,
  "damageDealt":          22,
  "zombiesKilled":        0,
  "skeletonsKilled":      0,
  "cowsEaten":            2,
  "blocksMined":          31,
  "blocksPlaced":         7,
  "itemsCrafted":         5,
  "ticksAsleep":          48,
  "interrupts":           6,
  "primitivesExecuted":   764,
  "actionsDropped":       3,
  "macrosUnreachable":    1,
  "repliesRepaired":      0,
  "finalTick":            812,
  "turnsPlayed":          41,
  "policyKinds":          ["llm"],
  "llmTurns":             40,
  "fallbackTurns":        1,
  "deadSeats":            [false],
  "stopDetail":           ""
}
```

`deathCause` is a closed enum: **`zombie` | `skeleton` | `arrow` | `lava` | `starvation` | `thirst` |
`exhaustion` | `none`** (`none` when the episode did not end in death). `toolsOwned` is a subset of the
six tool names in canonical order, `minItems: 0`, `maxItems: 6`. Six identities hold in every results
document and are asserted by `tests/test_crafter_engine.nim`:

1. `scores[0] == 10_000 × achievementsUnlocked + survivalTicks`;
2. `achievementsUnlocked == count(achievementUnlocked)` and `achievementsOf == 22`;
3. `achievementTick[i] >= 0` **iff** `achievementUnlocked[i]`, and `-1` otherwise;
4. `survivalTicks == finalTick` and `finalTick <= maxTicks`;
5. `endRule == "death"` **iff** `finalHealth == 0` **iff** `deathCause != "none"`;
6. `primitivesExecuted <= finalTick` and `turnsPlayed <= maxTurns`.

The example above satisfies all six: 12 unlocked ticks are non-negative, ten are `-1`,
`10_000 × 12 + 812 = 120_812`.

Adding a key means updating `runResultsJson`, the manifest's `results_schema` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas are closed and
undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDCRF`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (`SMOKE_REQUIRE_REPLAY_JSON`, template line 31).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"crafter/v1","gameVersion":"1","seed":…,"variant":"…","names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"plans":[…],"says":[…],"fallbacks":N,"achievements":[…],
  "results":{…}}` — by brace-matching the config JSON from the first `{` (the technique the starter's
  `AGENTS.md` documents for prod forensics) and decoding the chat records.
- **The phase-60 substitute for `docs/SPEC.md` §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule, .results.achievementsUnlocked' /tmp/ep.json
  jq -r '[.plans[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  ```
  Require `protocol == "crafter/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.achievementsUnlocked >= 3`, and the champion seat's plans with
  `source == "llm"`, real verbs (including at least one `goto` and at least one `make_*` or `place_*`)
  and non-empty `say` lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDCRF`, format version, `gameName` `crafter`, `gameVersion` `1` |
| config JSON | `seed`, `variant`, `num_agents`, `worldSize`, `viewSize`, `regionSize`, `turnTicks`, `maxTurns`, `maxTicks`, `dayLength`, `dayFraction`, `mountainThreshold`, `maxCows`, `maxZombies`, `maxSkeletons`, `foodTicks`, `drinkTicks`, `energyTicks`, `regenTicks`, `starveTicks`, `plantRipenTicks`, `parAchievements`, `maxActionsPerTurn`, `macroPrimitiveCap`, `players[].name` (real name), `slots[]`, `fastMode` |
| join | the seat's `name` (real policy name), `slot`, `token` |
| plans | per turn: the accepted action list — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

**The world generator is code, compiled into both the binary and the wasm module**, and the replay
carries the seed, the variant and every rule constant; the viewer therefore reconstructs the entire
64 × 64 world, every ore, every creature and every achievement tick from bytes it already has, with no
fetch. A generator change is a `GameVersion` bump, and the committed fixtures' version sweep makes an
unversioned change fail the build.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 64 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `tick`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `actions` (the accepted array), `executed` (the primitives that ran), `truncated`, `dropped`, `unreachable`, `interrupted`, `say` (≤ 160 runes), `view` (the observation minus `notes`) |
| `fallback` | `turn`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of twenty kinds, plus `end`:**

`turn` `{n, tick}`; `plan` `{n, verbs, truncated, dropped, interrupted}`; `say` `{text}`;
`fallback` `{cause}`; `achievement` `{id, index, n, of}`; `collect` `{what, x, y, count}`;
`craft` `{what}`; `place` `{what, x, y}`; `eat` `{what, food}`; `drink` `{drink}`;
`hurt` `{by, amount, hp}`; `heal` `{hp}`; `kill` `{what, x, y}`; `spawn` `{what, x, y}` (**only for a
hostile inside the 9 × 9 view**, so the feed never floods); `burn` `{n}`; `sleep` `{state}` (`start` |
`end`, `end` carrying `energy`); `nightfall` `{day}`; `daybreak` `{day}`; `starve` `{which, hp}`;
`death` `{by, tick}`; plus `end` `{reason, endRule, unlocked, of, score}`.

`tests/test_crafter_events.nim` asserts the emitted set equals exactly this list. `plan` fires once per
turn (≤ 56 an episode); `achievement` at most 22 times; `nightfall` / `daybreak` at most 8 each.
Nothing here fires unconditionally per tick, so the feed never floods.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`achievement`,
`nightfall`, `daybreak`, `kill`, `death`, `fallback`, `end`.** These are exactly the idea's watchability
asks ("achievement checklist lighting up; night-survival tension") plus the two the transport always
needs. `turn`, `plan`, `say`, `collect`, `craft`, `place`, `eat`, `drink`, `hurt`, `heal`, `spawn`,
`burn`, `sleep` and `starve` drive the feed, not the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `TurnStart, Directive, Fallback, Primitive, Collect, Craft, Place, Eat,
Drink, Hurt, Heal, Kill, Spawn, Burn, Sleep, Nightfall, Daybreak, Starve, Achievement, Death` and the
mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept. `Primitive` is the
per-tick row that makes this stream a full action trace for `cogamer-rl` — 1344 rows an episode, which
is what the idea's LLM-vs-RL ladder needs and what the replay deliberately does not carry.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`, and `tools/build_replay_viewer.sh`
is coworld-ctf's hook — kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/crafter/replay-viewer/dist/.`) — building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already
carries the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). No
`/client/replay` live-server viewer is ever declared to the platform; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/crafter_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
which is this repo's own starter. **Never a mixture.** Splicing one starter's shell onto another's
emscripten link flags (`MODULARIZE` / `EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks
the viewer silently (cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one
piece: the Worker sets `Module.onRuntimeInitialized` (`replay-viewer/static_replay_worker.js:188`), the
module is emitted **non-modularized** as `crafter_replay.js`, `config.nims` keeps
`--os:linux --cpu:wasm32 --cc:clang` through `emcc`,
`--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable: with
`-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals — the starter's
own comment at `replay-viewer/config.nims`), `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`,
`-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_crafter_load_replay,_crafter_frame,_crafter_input,
_crafter_packet_ptr,_crafter_packet_len,_crafter_mismatch_tick,_crafter_error_ptr,_crafter_error_len,
_crafter_stage_ptr,_crafter_stage_len`; and `static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './crafter_replay.js')` in that order (the
starter's line 239, renamed only).

`crafter_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress
buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and
the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `crafter_load_replay` re-simulates the whole episode once headlessly
  (1344 ticks over a 4096-cell grid — a few milliseconds in wasm), records the per-tick cumulative
  achievement count, the tick each achievement lit, the night spans, the beat ticks and the lull spans,
  then resets and renders frame 0. That is what lets the achievement sparkline, the night shading and
  the scrubber beats draw at **full width on the first frame** instead of growing in.
- `crafter_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (`replay-viewer/static_replay.js:158-161`) —
posted by the Worker only *after* `ingestPacket()` (`static_replay_worker.js:64`) has handed
BroadcastCore the first frame and it has drawn, so the attribute means "a frame is on the canvas", not
"a file was fetched". On failure it sets **`data-replay-error`** on `<html>` with the message, in
`showFailure()` (`static_replay.js:8-20`). Both are coworld-ctf's own signals, inherited unchanged —
this fork adds neither and removes neither. The `coworld-replay` postMessage bridge's `ready` is posted
**from a callback fired after** `data-replay-loaded="true"` is set, never on rAF timing at the call site
(chorus `3c11c953`, 2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes; sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`). Not edited, not reformatted;
  `tests/test_crafter_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in the
  appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats` ignores kinds it does
  not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (`client/replay_broadcast.html:4276-4325`), transport, endcard, locker-room loader, `?embed=1` mode
  and `.tiny` density system are untouched, and the block is installed through the starter's own splice
  hook: `window.PaintballChrome` (context built at `:4330`, installed at `:4337`, declared at `:4651`)
  is renamed `window.CrafterChrome` and its `install(PB_CTX)` / `frame(s, ctx, jumped)` (`:2075`) /
  `event(e, s, ctx)` (`:3480-3481`) entry points are kept with the same signatures. The appended block
  replaces only the *contents* of the scorebug plate, adds the achievement checklist, the vitals bars,
  the inventory strip and the two-level fog wash, retargets the agent-view inset, the feed rows, the
  beat rendering, the momentum series and the endcard columns. The block sits after the starter's banner
  comment at `:4344` and a test asserts the starter's byte prefix is intact up to that marker and that
  the file only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_crafter_viewer.nim`: the canvas/DPR sizing, `relayout()`, **the whole camera/zoom/minimap
  block (`clampView`, `computeFit`, `zoomAt`, `setZoom`, `panBy`, `panByMap`, `panTo`, `resetView`,
  `attachMinimap`, `broadcast_core.js:249-600`) — kept verbatim, because this game needs it**, the feed
  queue and `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the
  endcard builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` →
  `window.CRAFTER_WIRE` rename emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific
  draw call and the raycast FPV pipeline (the `#fpv` **canvas** is reused, the raycaster is not). Added:
  `drawTerrain`, `drawCreatures`, `drawCog`, `drawFog`, `drawAgentView`, `drawChecklist`, `drawVitals`,
  `drawInventory`, `drawNightWash`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#povBadge`** (`replay_broadcast.html:1525`) and the `togglePov` wiring — with one seat there is
    nothing to select.
  - Inside the kept `#fpv`: **`#fpv-hp`** (`:1537`), **`#fpv-gear`** (`:1538`), **`#fpv-map`** and
    **`#fpv-map-canvas`** (`:1542-1543`) — the vitals live on the scorebug plate where they belong, and
    an un-fogged tactical map is exactly what the kept `#minimap` already is.
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip` (`:300-330`), `.pb-tags`, `.squad` (`:2219-2244`), and the `.ec-heart` endcard glyphs
    (`:1221-1231`).
  - The `.beat-marker.kill` styling is **retargeted, not removed** (this game emits `kill`); the
    `.steal`, `.return`, `.capture` (`:919-934`) and `.gamestart`, `.hillflip`, `.tagout`, `.gameover`
    (`:4431-4443`) CSS rules are removed — those kinds are never emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS, `:245`).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with `#plates-l` / `#plates-r` /
    `#clock` / `#clock-time` / `#clock-caption` / `#ffwd-mini`, **`#fpv` with `#fpv-canvas`, `#fpv-hud`,
    `#fpv-name`, `#fpv-cap` and `#fpv-grip`** (repurposed: it becomes the cog's 9 × 9 window, caption
    `AGENT VIEW 9×9`, `#fpv-name` reading `ALPHA · FACING DOWN`, still draggable and resizable by the
    starter's own grip), `#bannerlane`, `#killfeed`, `#mmwarn`, **`#transport` in full** (`#btn-restart`,
    `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`,
    `#ffwd-chip`, `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub` with `#momentum` / `#scrub-fill` /
    `#lulls` / `#scrub-win` / `#scrub-head`, `#endcard` with `#ec-headline` / `#ec-wincond` / `#ec-how` /
    `#ec-teams` / `#ec-replay`, and `#status`. **`#plates-r` is kept but rendered empty** — it is one of
    the scorebug's three flex columns and removing it would un-centre `#clock`; with one seat the single
    plate lives in `#plates-l`.

**Zoom decision: `#viewpanel` is KEPT — zoom bar, minimap and all.** The pin says the zoom bar and
minimap exist only for boards larger than the frame, and here the board genuinely is: the world is
64 × 64 cells (1536 × 1536 native px) and the default view shows **15 cells**. That is the opposite of
the fixed-arena forks, and it is the right call for exactly the reason the starter's own comment gives
("classic boards can be colossal"). Concretely:

- `#viewpanel`, `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`,
  `#zoom-read` (`replay_broadcast.html:1510-1521`) and the page's
  `core.attachMinimap($('minimap-canvas'))` call (`:4200`) are **all kept, unmodified**.
- **Follow-cam.** Because `fitScale` and `zoom` are related by `zoom = worldSize / cellsAcross`
  independently of the container width (`fitScale = W/1536`, and showing `k` cells needs
  `scale = W/(24k)`, so `zoom = 1536/(24k) = 64/k`), the game block sets
  **`core.setZoom(64 / cameraCells)` with `cameraCells = 15` → `zoom = 4.267`** once per board, and
  calls `core.panTo(cogX·24 + 12, cogY·24 + 12)` on every frame while follow is armed. Follow is armed
  at load; a user `panBy` / `panByMap` / minimap drag disarms it; `resetView()` (the starter's own
  binding) re-arms it and restores `cameraCells = 15`. `broadcast_core.js:355-370` resets `zoom` to
  `minZoom` whenever the board's native size changes, which happens exactly once at the first frame, so
  the block re-applies `setZoom` whenever it observes `getTransform().zoom === 1` with follow armed.
- The minimap therefore always draws (it is suppressed only at `zoom <= minZoom`,
  `broadcast_core.js:561`), showing **the whole 64 × 64 world as the cog has explored it**, with the
  white view box marking the 15 × 15 window. `#zoom-read` is re-labelled to show the cells across
  (`15 CELLS`, `64 CELLS` at the fitted end) instead of `FIT`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here and
enforced by a test:

| Starter string (`client/replay_broadcast.html:line`) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`:3795`) | `<span>#</span><span>Achievement</span><span>Unlocked</span><span>Tick</span><span>Day</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` (`:3788`) | `<span>Cog</span><span>Unlocked</span><span>Survived</span><span>Score</span>` |
| `<span class="fl-cap">Lives left</span>` (`:3793`) | `<span class="fl-cap">Achievements</span>` |
| `<span class="fl-cap">Hill time</span>` (`:3786`) | `<span class="fl-cap">Ticks survived</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (`:1576`) | `<span class="momentum-label">ACHIEVEMENTS</span>` |
| `<span class="lives-label">Lives</span>` (`:2241`) | `<span class="vital-label">Health</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` (`:2224`) | `<span class="vital-label pb-lbl">Carrying</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (`:1480`, `:1842`) | "Generating the world…" |
| `#clock-caption` "In the locker room" (`:1499`) | "Waiting for the cog" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (`:1524`) | "Replay hash mismatch at tick N — showing recorded actions" |
| `#fpv-cap` "EYES" (`:1545`) | "AGENT VIEW 9×9" |
| `#btn-spoilers` title "Spoilers: kills / flag story / winner on the timeline ahead of the playhead (o)" (`:1564`) | "Spoilers: achievements and the death on the timeline ahead of the playhead (o)" |
| `#zoom-read` "FIT" (`:1520`) | the cells across: `15 CELLS` … `64 CELLS` |
| team words `RED` / `BLUE` in `.ec-tname` / plates (`:2222`, `:2239`, `:3783`, `:3790`, `:3836`) | the seat's **alias** (`ALPHA`) on the plate, and `THE RUN` as the endcard section head |

**`tests/test_crafter_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `POV`, `EYES`, `spray`, `grenade`, `med kit`, `team` — outside comment blocks, and asserts
**zero** matches; and asserts each replacement string above is present exactly once. (`kill` is **not**
on the forbidden list here: this game emits a `kill` beat and says `KILLED A ZOMBIE` in the feed.) A
rename that reintroduces paintbot vocabulary fails the build.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (`client/replay_broadcast.html:4276-4325`). **No overlay sits in the transport
band**: the board is laid out between the two bands and every addition here (the achievement checklist,
the vitals column, the inventory strip, the agent-view inset, `#viewpanel`, the feed) is positioned
inside the board region, in the letterbox gutters beside it, or in the top band. The **endcard stops at
`var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, `:1047`, the starter's rule, kept) so the
scrubber stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `cfBeat(tick, kind, label)` — named with the `cf-` prefix so it can
never shadow `chrome_common.js`'s `markBeat` alias (`client/replay_broadcast.html:1635`; the tandem
2026-08-23 hoisting trap, and the same prefix discipline the starter's own `pbBeat` at `:4475` uses) —
appends `<button class="beat-marker <kind>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind emitted and no others**: `.beat-marker.achievement`,
`.beat-marker.nightfall`, `.beat-marker.daybreak`, `.beat-marker.kill`, `.beat-marker.death`,
`.beat-marker.fallback`, `.beat-marker.end`. The game block never calls `markBeat`, so an unlabelled div
marker cannot appear.

**Playback rate: one tick per three animation frames at 30 fps = 10 ticks/second** (speed chips
`[0.5, 1, 2, 4, 8]`, default 1), with the cog's position interpolated across the three frames so a step
glides rather than snapping. A 1344-tick episode therefore plays for **134 s**, and even a short
400-tick episode plays for 40 s, which is what lets `viewer_smoke.mjs --soak 10` observe real
advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The board** — the 15 × 15 follow-cam window over the world, drawn from the baked terrain bed: grass
   and sand, water with a two-frame shimmer, forest, the grey mountain with coal, iron and diamond
   seams, cave floor, lava with a two-frame crust cycle, the placed table and furnace, saplings and
   ripe plants. Creatures are drawn over it: cows, zombies, skeletons, arrows in flight. This is the
   idea's "pixel render".
2. **The night wash** — at night the whole board is drawn under a deep blue wash that deepens toward
   midnight and lifts at dawn, with a warm radius around the cog. The spectator sees the sun go down
   before the zombies arrive, which is the whole of the idea's "night-survival tension".
3. **The fog wash** — a cell the cog has never seen is drawn black; a cell seen but outside the current
   9 × 9 is drawn under a light wash with its remembered terrain; a cell inside the 9 × 9 is drawn
   clean. The minimap inherits it, so the explored map grows visibly over the episode.
4. **The achievement checklist** (the idea's headline ask) — 22 chips in the left gutter, two columns ×
   eleven rows, in canonical order, each an icon plus its name. Locked chips are drawn at 25 % opacity
   with a hairline border; the tick one unlocks it **flashes** (the starter's banner flash reused),
   fills with the palette's gold, and stays lit. This is the single most important readout in this game
   and it is why the checklist gets a whole gutter.
5. **Vitals** — four bars on the scorebug plate: health (red), food (green), drink (blue), energy
   (violet), each nine pips. A pip drains visibly; a bar at zero pulses.
6. **Inventory strip** — six resource counts (wood, stone, coal, iron, diamond, sapling) and six tool
   chips (wood/stone/iron pickaxe and sword), the tool chips lit when owned, under the vitals on the
   plate.
7. **Clock** — `#clock` shows the big numeral **`12 / 22`**; `#clock-time` shows `DAY 5 · NIGHT`;
   `#clock-caption` shows `tick 812/1344 · hp 6 · score 120812`.
8. **Scorebug plate** — one plate in `#plates-l`: the seat's **real policy name** (spectator side only),
   its in-game alias `ALPHA`, the cog avatar from `data/soldier_red_front.png`, the running score as the
   numeral, the vitals and inventory above, and a `↯` glyph if the seat has taken a fallback.
9. **The cog's 9 × 9 window, inset** — the repurposed `#fpv` panel in the right gutter, drawing exactly
   the `view` array the seat receives, world-oriented, the cog at the centre, `?` cells black, captioned
   `AGENT VIEW 9×9` with `ALPHA · FACING DOWN` beneath. Draggable and resizable by the starter's own
   `#fpv-grip`. It is what shows a spectator how little the cog can see.
10. **Minimap and zoom** — `#viewpanel`, kept (above): the whole explored 64 × 64 world at a glance with
    the view box, and a zoom bar from `15 CELLS` to the whole world.
11. **Match feed** (`#killfeed`) — plain language, never internal notation: `CHOPPED WOOD (3)`,
    `PLACED A CRAFTING TABLE`, `★ ACHIEVEMENT 6/22 — MADE A WOOD PICKAXE`, `DRANK FROM THE LAKE (9/9)`,
    `ATE A COW (+6 FOOD)`, `NIGHT FALLS ON DAY 3`, `A ZOMBIE BIT ALPHA — 4 HEALTH LEFT`,
    `TURN CUT SHORT — HIT BY A ZOMBIE`, `SEALED IN AND SLEEPING`, `WOKE UP RESTED`,
    `KILLED A SKELETON`, `MINED IRON`, `SMELTED AN IRON PICKAXE`, `★ ACHIEVEMENT 22/22 — CUT A DIAMOND`,
    `ALPHA STARVED`, `Alpha: "stone ridge is five cells NE; mining it then arming up"`, and
    `MISSED THE CALL — forager plan (timeout)`. The `say` lines and the plan lines are where a
    spectator sees the LLM playing.
12. **Achievement sparkline** — the starter's `#momentum` SVG retargeted to one cumulative series
    (achievements unlocked, 0 … 22) with **night spans shaded** behind it and the playhead marked.
    Filled from the load-time pre-scan, so it draws at full width on the first frame. A staircase that
    goes flat halfway through a shaded band is the whole story of a bad night in one glance.
13. **Endcard** — `12 OF 22 UNLOCKED — KILLED BY A ZOMBIE ON NIGHT 4`, the 22-row checklist under the
    re-mapped header (`# | Achievement | Unlocked | Tick | Day`) with every row present and the ten
    unearned ones greyed, a summary line (`survived 812 ticks across 5 days, 1180 of 4096 cells seen,
    31 blocks mined, 5 items crafted, 2 cows eaten, 6 turns cut short, 1 fallback turn`), and
    `SCORE 120812`. It stops at `var(--band)` and any seek dismisses it.
14. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    40 consecutive ticks with no `achievement`, `collect`, `craft`, `place`, `kill`, `hurt` or
    `nightfall` event and no change in the cog's cell, from the pre-scan), spoilers switch, tick readout,
    speed chips, the scrubber with its seven beat kinds, and `#mmwarn` on a hash mismatch — all the
    starter's, verbatim.

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no
solid-colour squares, no downloads.** Every terrain is a **24 × 24 baked tile** in the palette from
`data/pallete.png`, produced by one pixie bake at install exactly the way the starter bakes endzone
paint: **grass** from `data/arena_floor.png` tiled and tinted green with a procedural blade fleck;
**sand** the same bed tinted ochre with a grain speckle; **water** two frames of the bed tinted blue
with an offset ripple, cycled at 2 Hz; **stone** and **bedrock** cut from `client/art/walls/wall_h.jpg`
and `wall_v.jpg` with a baked bevel, bedrock darker and flatter, so a rock face reads as masonry rather
than a grey bar; **path** the stone tile darkened and smoothed; **tree** a procedural canopy over the
grass tile; **coal**, **iron** and **diamond** the stone tile with a baked seam in black, rust and
cyan; **lava** two frames of orange with a black crust, cycled at 4 Hz; **table** and **furnace**
composed from the wall crops with a baked top; **sapling** and **ripe plant** procedural in the palette.
The **cog** is `data/soldier_red.png` composited by `rig_art.nim` into 4 facings × 2 sizes = **8
chips**, with a sleep pose; `data/soldier_red_front.png` is its avatar on the scorebug plate and in the
agent-view caption. **Cows**, **zombies** and **skeletons** are composited from the same rig with
per-kind palettes and silhouettes (a cow is wide and low, a zombie is the rig in sick green with a
lurch offset, a skeleton is the rig in bone white and thin); the **arrow** is a 3-px procedural dart.
The 22 achievement icons are baked once from the terrain/tool tiles they refer to (a tree for
`collect_wood`, a pickaxe for `make_wood_pickaxe`, a diamond for `collect_diamond`, …). Every chrome
numeral and every checklist caption is set in `data/font.ttf`. The loading screen is the starter's
locker room (`client/art/lockerroom/bg.jpg` plus the four red webps) with the caption re-labelled.

**No text is ever drawn onto the board layer.** Every string in this viewer is DOM chrome or is drawn
inside a fixed-size gutter panel (the checklist, the inset, the plate, the feed). That is a deliberate
rule for a **pannable** board: with a camera over a 1536 × 1536 surface, a string baked into board space
would legitimately sit off-frame and make `--strict-text-bounds` meaningless. Keeping the board
text-free is what lets the flag stay **on** (§Tests).

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (`client/replay_broadcast.html:4307-4312`). The board's aspect is **1536/1536 = 1.000**. In a
360 × 203 frame, `relayout()` reserves `--topband` and `--band`, leaving a play region roughly
360 × 120; since `360/120 = 3.0 > 1.000`, **height binds**: the board region renders **120 × 120**, and
at `cameraCells = 15` that is **8 px per cell** with the cog dead centre — a chunky pixel render, which
is exactly Crafter's own look. That letterbox leaves **two ~120 px gutters**, and this game uses both:
the **achievement checklist in the left gutter**, and the **`#viewpanel` minimap above the 9 × 9 inset
in the right**, so nothing ever overlaps the board and nothing ever enters the transport band. Six rules
are added and asserted by `tests/test_crafter_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, the single plate keeps only `alias + name + achievement count + health bar`; the
   avatar shrinks to 10 px, the food/drink/energy bars collapse into one three-segment strip, the
   inventory strip drops its resource numerals to icon-plus-count at 8 px, and the fallback glyph moves
   inline.
3. Under `.tiny`, the achievement checklist renders as **2 columns × 11 rows of 9 px icon chips** with
   no captions (captions move to `title` tooltips), a lit chip carrying a 1 px gold ring so the
   locked/unlocked distinction survives at 9 px; the full-width layout restores the captions above
   620 px.
4. Under `.tiny`, `#zoombar` is hidden and `#minimap` is pinned to 56 px square at the top of the right
   gutter; the 9 × 9 inset is pinned to 56 px square beneath it (56 + 56 + 8 px gap = 120 px, exactly
   the gutter height) and the `#fpv-grip` resize is disabled below 620 px so the inset can never be
   dragged over the board.
5. Under `.tiny`, the fog wash uses a **higher-contrast two-step** (unseen black / seen dim) instead of
   the three-step, and the night wash caps at 55 % opacity, because an 8 px cell cannot carry three wash
   levels and still show a zombie.
6. `#killfeed` shows **three** rows under `.tiny` instead of six, and every feed row is single-line with
   `text-overflow: ellipsis`; the `say` rows keep their full text in `title`.

---

## Packaging

- **Repo**: `Metta-AI/cogame-crafter`, **public at creation** (public is a certification prerequisite —
  `source-resolves` 404s on private). Slug `crafter`; **`game.name` is `crafter`** — identical to the
  slug, so the secret namespace `secret://coworld/crafter/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the commons-family 2026-08-24 scar, where
  `game.name` and the slug differed by an underscore).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name (`{{GAME_IMAGE}}` is not a thing — lantern 0.1.0). ctf ships two services/two
  images (`compose.yaml` `game` + `player`); this fork uses the one-image / two-entrypoints shape
  because the shared `docker_smoke.sh` and `policies.json` assume a single image (the knights-archers
  precedent):

  ```yaml
  services:
    crafter:
      image: coworld-crafter:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{CRAFTER_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:crafter src/crafter.nim` →
  `/bin/crafter`, and the same for `src/crafter_player.nim` → `/bin/crafter-player`. The runtime stage
  copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/crafter"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with
  the asset list swapped to `data/{arena_floor,ascii,pallete}.png`, `data/soldier_red{,_front}.png`,
  `data/font.ttf`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,red_*.webp}`,
  `crafter_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["survival", "single-agent", "crafting", "tech-tree",
    "open-ended", "crafter"]` (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0);
    **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "crafter"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/crafter"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/crafter/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 1/1, `players` 1/1, `slots` 0/1 — the tandem 0.1.0 scar; there are no other arrays).
    `tokens` is described as runner-injected; **no `game_config` anywhere in this manifest contains a
    literal `tokens` array** (matriculate rejects "game_config must not include runner-managed tokens"
    — knights-archers 0.1.0), while `config_schema` keeps *requiring* it because the runner injects it.
    Properties: `tokens`, `players`, `slots`, `seed`, `num_agents`, `minPlayers`, `worldSize`,
    `viewSize`, `regionSize`, `turnTicks`, `maxTurns`, `maxTicks`, `dayLength`, `dayFraction`,
    `mountainThreshold`, `maxCows`, `maxZombies`, `maxSkeletons`, `foodTicks`, `drinkTicks`,
    `energyTicks`, `regenTicks`, `starveTicks`, `plantRipenTicks`, `parAchievements`,
    `maxActionsPerTurn`, `macroPrimitiveCap`, `attempt1Ms`, `retryMs`, `turnBudgetMs`,
    `turnSpacingMs`, `wallClockBudgetSeconds`, `lobbyJoinTimeoutTicks`, `gameOverTicks`, `fastMode`,
    `showPlayerLabels`, `model`, `maxOutputTokens` — with `num_agents` an integer, `minimum: 1`,
    `maximum: 1`, default 1.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`,
    `endRule: {"type":"string","enum":["death","allUnlocked","turnCap","tickCap","wallClock","fault"]}`,
    `deathCause: {"type":"string","enum":["zombie","skeleton","arrow","lava","starvation","thirst","exhaustion","none"]}`,
    `achievementIds` / `achievementUnlocked` / `achievementTick` each `minItems: 22, maxItems: 22`, and
    `toolsOwned` `minItems: 0, maxItems: 6`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-crafter/blob/main/docs/PROTOCOL.md"}` —
    objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"actions.md","title":"Actions and the reply format","content":{"type":"uri","value":".../docs/ACTIONS.md"}},
    {"id":"achievements.md","title":"The 22 achievements","content":{"type":"uri","value":".../docs/ACHIEVEMENTS.md"}},
    {"id":"porting.md","title":"What this is and is not a port of","content":{"type":"uri","value":".../docs/PORTING-CRAFTER.md"}}]}`.
  - Top-level `player[]` with `id` / `type` / `name` / `description` / `image` / `run` / `source_url`
    and `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). **Exactly ONE entry, `forager`**: `num_agents = 1` leaves
    exactly one certification slot, and **every declared player must occupy a certification slot** (the
    raid 0.1.2 scar), so a second declared player could not be seated. `wanderer` still ships in the
    image, is exercised by `tests/test_crafter_driver.nim`, and is a league filler in
    `tools/ci/policies.json` — it is simply not a *declared manifest* player.

  **Variants — `num_agents: 1` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "standard", "name": "Standard world (1 cog, 22 achievements)",
     "description": "One cog alone in a procedurally generated 64x64 wilderness it can see nine cells of. Chop wood, place a table, make a pickaxe, mine stone, build a furnace, smelt iron, and cut a diamond out of the mountain - while keeping health, food, drink and energy off zero and staying alive through seven nights of zombies. Score is how many of Crafter's 22 achievements it unlocks before it dies.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "worldSize": 64, "viewSize": 9, "regionSize": 16,
                     "turnTicks": 24, "maxTurns": 56, "maxTicks": 1344,
                     "dayLength": 192, "dayFraction": 128, "mountainThreshold": 700,
                     "maxCows": 12, "maxZombies": 8, "maxSkeletons": 6,
                     "foodTicks": 40, "drinkTicks": 30, "energyTicks": 50,
                     "regenTicks": 25, "starveTicks": 10, "plantRipenTicks": 120,
                     "parAchievements": 8,
                     "maxActionsPerTurn": 12, "macroPrimitiveCap": 24,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9500, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "longnight", "name": "Long night (1 cog, half the episode in the dark)",
     "description": "The same world and the same 22 achievements, but the sun is up only half the time and there are half again as many zombies. Ore sits closer to the surface so the tech tree is still reachable in the dark - the question is whether a cog can climb it while something is hunting it. Score is how many achievements it unlocks before it dies.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "worldSize": 64, "viewSize": 9, "regionSize": 16,
                     "turnTicks": 24, "maxTurns": 56, "maxTicks": 1344,
                     "dayLength": 160, "dayFraction": 80, "mountainThreshold": 660,
                     "maxCows": 8, "maxZombies": 12, "maxSkeletons": 6,
                     "foodTicks": 40, "drinkTicks": 30, "energyTicks": 50,
                     "regenTicks": 25, "starveTicks": 10, "plantRipenTicks": 120,
                     "parAchievements": 6,
                     "maxActionsPerTurn": 12, "macroPrimitiveCap": 24,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9500, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 1` again, inside `certification.game_config`, and exactly one
  player so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 1`
  (the four `SEAT-COUNT` invariants `tools/ci/docker_smoke.sh` cross-checks at template lines 141-150),
  with the single declared player seated:

  ```json
  "certification": {
    "players": [{"player_id": "forager"}],
    "game_config": {"players": [{"name": "Alpha"}],
                    "num_agents": 1, "minPlayers": 1, "seed": 42,
                    "worldSize": 64, "viewSize": 9, "regionSize": 16,
                    "turnTicks": 24, "maxTurns": 56, "maxTicks": 1344,
                    "dayLength": 192, "dayFraction": 128, "mountainThreshold": 700,
                    "maxCows": 12, "maxZombies": 8, "maxSkeletons": 6,
                    "foodTicks": 40, "drinkTicks": 30, "energyTicks": 50,
                    "regenTicks": 25, "starveTicks": 10, "plantRipenTicks": 120,
                    "parAchievements": 8,
                    "maxActionsPerTurn": 12, "macroPrimitiveCap": 24,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  A `forager`-only episode is scripted throughout, so 1344 ticks is a couple of seconds of sim, but the
  replay is long ⇒ **up to 134 s of playback**, which the viewer soak needs. Seed 42 is asserted by
  `tests/test_crafter_engine.nim` to produce a fixture episode in which `forager` unlocks **at least
  six** achievements (including at least one `place_*`, one `make_*` and one `collect_*`), survives at
  least **900 ticks** (so the replay outlasts a 10 s soak by a wide margin), sees at least one night,
  and takes at least one hit — so the smoke replay always exercises the `achievement`, `nightfall`,
  `daybreak`, `hurt` and `kill`-or-`death` paths. The certify step in `coworld-release.yml` passes
  **`--timeout-seconds 300`** (the default 60 covers start + connect grace + play + linger —
  cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/crafter-player"`, following the
  starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"crafter-techtree","run":"/bin/crafter-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"techtree"}},
   {"name":"crafter-homesteader","run":"/bin/crafter-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"homesteader"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"crafter-forager","run":"/bin/crafter-player",
    "env":{"PLAYER_SCRIPTED":"forager","PLAYER_POLICY_LABEL":"forager"}},
   {"name":"crafter-wanderer","run":"/bin/crafter-player",
    "env":{"PLAYER_SCRIPTED":"wanderer","PLAYER_POLICY_LABEL":"wanderer"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1, uploaded
  while daveey-1 is the active player); the fillers are `forager` and `wanderer`, and their versions
  must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `crafter`, `<IMAGE>` →
  `coworld-crafter`, `<SEATS>` → **`1`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0` (§Server) and `--soak 10`
  added to the `viewer_smoke.mjs` invocation (which already passes `--strict-text-bounds`).
  `coworld-release.yml` and `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the
  certify step, and the push-triggered upload job gated on the `UPLOAD_REQUIRED` repo variable
  (derks-gym 0.1.1). `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed
  **executable** (mode 100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_crafter_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_crafter_world.nim`, `tests/test_crafter_sim.nim`)

1. `world is a pure function of the seed` — the same `(seed, variant)` generates a byte-identical
   64 × 64 grid under three different policy behaviours, and two different seeds differ.
2. `generation invariants` — over 200 seeds and both variants: the bedrock ring is intact and unbroken;
   the 3 × 3 block at (32, 32) is grass; a tree exists within Chebyshev 12 of spawn; water within 12;
   stone within 20; `count(coal) >= 5`, `count(iron) >= 3`, `count(diamond) >= 1`; every cell holds
   exactly one terrain from the closed enum.
3. `the world is completable` — over 60 seeds of each variant, a search-based reference solver (test-only,
   not shipped in the image) that ignores the turn budget reaches `collect_diamond`; a seed where it
   cannot is a generator bug and fails the build.
4. `noise is integer` — a source grep over `src/crafter/{sim,world,agent,creatures,achievements,driver,
   baselines}.nim` finds no `float`, `/`, `sqrt` or float literal; and the four noise fields are
   recomputed in a second, independent implementation in the test and compared cell for cell.
5. `glyph, walkable and mineable tables are total` over the terrain enum and match §The game exactly;
   the 20 glyphs are pairwise distinct.
6. `the seventeen primitives` — each does exactly what §The seventeen actions says and nothing else:
   `move_<dir>` turns then steps only into a walkable, creature-free cell; `do` resolves creature before
   terrain; every recipe checks its costs and its table/furnace adjacency; every `place_*` checks its
   cost and its target terrain; `sleep` adds energy; `noop` mutates nothing; an inapplicable primitive
   is a no-op that still costs a tick.
7. `lava kills` — a `move_<dir>` into lava sets health 0 on that tick with `deathCause == "lava"`,
   regardless of health; `place_stone` over lava makes it walkable and no longer fatal.
8. `vitals` — the five numbered steps in order, over a 1344-tick synthetic run: drain periods exactly
   40/30/50; regen only when all three are positive and only every 25 ticks; starvation exactly 1 health
   per zeroed vital per 10 ticks; every bar clamps to 0…9; the food/drink/energy → `deathCause` mapping
   is `starvation`/`thirst`/`exhaustion` in that resolution order.
9. `creatures` — spawn attempts are bounded to one per kind per tick, never inside Chebyshev 6 of the
   cog, never on the wrong terrain, never over a cap; zombies burn at dawn only when not on `path`;
   zombie damage is 2 awake and 5 asleep with a 5-tick cooldown; skeletons need a clear straight line
   within 6 and an 8-tick cooldown; arrows travel one cell a tick and vanish on any obstruction; the
   creature order is stable and identical under replay.
10. `the 9 × 9 window` — always 9 strings of 9, world-oriented, the cog at the centre, creature glyphs
    over terrain glyphs, and no cell outside the box ever leaks into `view`; the known map grows only
    from observed windows and a cell never observed stays `?` for the whole episode; creatures are never
    written into the known map.
11. `the 16 × 16 region map` — always 16 strings of 16; each region's glyph is the highest-priority
    terrain that region is *known* to contain, by the exact priority order; a region with no observed
    cell is `?`.
12. `goto BFS` — the path is unique for a given known map (neighbour order up/right/down/left), never
    traverses `?`, water, lava, rock, a tree, a table, a furnace, a plant or a known hostile; it ends
    **on** a traversable target and **facing** a non-traversable one; an unreachable target yields zero
    primitives; the path never exceeds `macroPrimitiveCap`.
13. `the twenty-two achievements` — for each, a scripted sequence that unlocks it and a deliberate near
    miss that does not (crafting with no table nearby; iron tools with a table but no furnace; mining
    iron with only a wooden pickaxe; eating an unripe sapling; `wake_up` after a sleep run that started
    at full energy; `defeat_zombie` when the zombie is killed by lava rather than the cog). Each unlocks
    at most once, is never revoked, and stamps `achievementTick` exactly once.
14. `turn and tick order` — the numbered resolution order of §The game is exercised end to end: the queue
    empties into `noop`; a creature hit breaks the tick loop and starvation damage does **not**; a death
    ends the episode on its tick; the twenty-second achievement ends it immediately; skipped ticks are
    never counted in `finalTick`.
15. `scoring` — `scores[0] == 10_000 × achievementsUnlocked + survivalTicks` over 500 randomised end
    states; the dominance bound holds (`maxTicks 1344 < 10_000`); the maximum is `221_344`; the minimum
    is `1`; `win[0]` is `achievementsUnlocked >= parAchievements`; `winner` is `0` when `win[0]` and
    `null` otherwise.
16. `end conditions` — `death`, `allUnlocked`, `turnCap`, `tickCap`, a forced wall-clock stop and a
    forced fault each produce the right `endRule` and the right episode `reason`; a wall-clock stop
    mid-run still scores every achievement already unlocked.
17. `the geometric-mean aggregate` — `tools/crafter_score.py` over a synthetic set of 50 results
    documents reproduces `exp(mean(ln(1 + 100·p_i))) − 1` to within 1e-9 of a reference computed in the
    test, is 0 when nothing ever unlocks, and is 100 when everything always does.
18. `tick budget` — 1344 ticks of a full `longnight` episode with every creature cap saturated complete
    in < 2 s in a release build.

**Bounded orders / legality on the scripted baselines** (`tests/test_crafter_driver.nim`)

19. `baselines are bounded` — for 300 pseudo-random world states (both variants, day and night, every
    vitals combination, empty and full inventories, adjacent to lava, water and hostiles) and for
    **both** `forager` and `wanderer`: the reply has at most 12 actions, every `act` is in the enum,
    `goto` targets are inside 0…63, `move` dirs are in the enum, every `n` is inside its range, `say` and
    `notes` are empty, and the serialised directive is ≤ 1024 bytes. A baseline that ever proposes an
    illegal or unbounded action fails the build.
20. `baselines never suicide` — over the same states, neither baseline ever emits a plan whose
    deterministic expansion steps onto a **known** lava cell; `forager`'s BFS never routes through `?`.
21. `driver never produces an illegal primitive` — over the same states, every expanded queue is ≤ 24
    primitives, every entry is one of the seventeen, macros expand to at most `macroPrimitiveCap`, and an
    empty queue yields `noop`, never nothing.
22. `fallback is the forager proc` — the decision engine's fallback path and the `forager` baseline
    resolve to the same proc, so they cannot drift.
23. `reply validation` — the validator accepts the schema, **drops** (never rewrites) an invalid action,
    clamps `goto` coordinates and every `n`, lower-cases and `-`→`_` normalises `act`, case-folds `dir`,
    accepts a `say`-only reply, rejects a non-object, truncates `say`/`notes` on **rune** boundaries at
    160/400 with 4-byte emoji sitting exactly on the boundary, caps the read at 4096 bytes, caps
    `actions` at 12, and reports `truncated` / `dropped` / `unreachable` / `interrupted` back accurately.
24. `baseline tuning is the swept pick` — the shipped thresholds equal `tools/ci/baseline_tuning.json`
    (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep with `--check`).
25. `forager beats wanderer` — over 100 seeds of each variant, `forager` unlocks strictly more
    achievements in total than `wanderer`, and `wanderer` unlocks at least one — the two controls are
    genuinely different controllers and neither is a zero.

**End-to-end episode writing a replay** (`tests/test_crafter_engine.nim`)

26. `episode writes artifacts` — run a real one-seat episode (`standard`, scripted, no API key so the LLM
    client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the `.replay`
    are written, `reason == "complete"`, `scores` agree with the formula, the six results identities of
    §Server hold, and the results key set equals the manifest's `results_schema` key set **exactly**.
27. `the cert seed is interesting` — seed 42 on `standard` yields ≥ 6 achievements including at least one
    `place_*`, one `make_*` and one `collect_*`, survives ≥ 900 ticks, crosses at least one nightfall and
    one daybreak, and takes at least one hit — so the CI smoke replay always exercises those paths and
    always outlasts the soak.
28. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at all,
    both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure payload;
    the server refuses to start the game (loudly) when the joined seat has no register record.
29. `budget guard and rate guard settle early` — with each guard forced, the episode finishes `complete`,
    not `deadline`, and the matching record names the turn.
30. `flinch accounting` — a forced zombie attack mid-turn discards the rest of the queue, increments
    `interrupts`, sets `last_plan.interrupted`, and does **not** consume the discarded ticks; forced
    starvation damage does none of those things.

**Replay** (`tests/test_crafter_replay.nim`)

31. `record then re-derive, every end reason` — for `death`, `allUnlocked`, `turnCap`, `tickCap`,
    `wallClock` **and** `fault`, record an episode and re-derive it from the bytes; assert identical
    hashes at every tick **including the stop tick** (the particle-worlds scar).
32. `replay is self-sufficient` — the bytes alone yield the seat's real name, its alias, the policy kind,
    the full config (every constant in §Server's config-JSON row), the seed, the variant, every plan
    record, every chat record and the result; and re-simulating from them reproduces the entire 64 × 64
    world, every creature and every achievement tick with no fetch.
33. `the incremental terrain digest equals a full fold` — after 1344 ticks of mining and placing, the
    incrementally maintained `terrainHash` equals a fresh fold over all 4096 cells. (The optimisation of
    §Determinism point 4 is only safe if this holds.)
34. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every capped
    field is filled to exactly its cap with 4-byte emoji; assert the output parses under a **strict**
    UTF-8 JSON parser, contains no lone surrogates, and reports `protocol == "crafter/v1"`.
35. `determinism from the replay alone` — re-simulate from the replay's seed and plan records on a fresh
    sim; identical final tick, achievement mask, achievement ticks and per-tick `gameHash`.
36. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_crafter_manifest.nim`)

37. `manifest pins` — `num_agents == 1` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; `len(player) == 1` and that player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 1`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds <= 660`;
    `attempt1Ms + retryMs <= turnBudgetMs` and both are whole seconds; `maxTicks == maxTurns × turnTicks`;
    `dayFraction < dayLength`; `game.name` equals the slug and the secret URI's namespace; the
    `results_schema` achievement arrays are pinned at 22; **and every variant's `game_config` actually
    constructs a valid `GameConfig`, generates its world, passes the generation invariants and produces
    the 56-turn schedule this note claims** (the collab-cooking 0.1.1 scar: test every variant, not just
    the fixture).
38. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_crafter_viewer.nim`, static assertions in the `test` job)

39. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, pinned as a literal.
40. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the documented
    splice marker (`replay_broadcast.html:4344`) and only appends after it; `broadcast_core.js`'s kept
    procs are byte-identical to the starter's, `pushFeed`'s signature and the whole camera/zoom/minimap
    block included.
41. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (`replay_broadcast.html:1635`, the tandem hoisting trap); the beat
    builder is `cfBeat`, never `markBeat`.
42. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{achievement, nightfall, daybreak, kill, death, fallback, end}`.
43. `viewpanel is kept and wired` — `#viewpanel`, `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`,
    `#zoom-out`, `#zoom-slider`, `#zoom-read` and the `core.attachMinimap($('minimap-canvas'))` call are
    all present; the game block calls `core.setZoom(64 / cameraCells)` with `cameraCells == 15` and calls
    `core.panTo` on every frame while follow is armed; the removed ids (`#povBadge`, `#fpv-hp`,
    `#fpv-gear`, `#fpv-map*`) appear nowhere, while the kept `#fpv`, `#fpv-canvas`, `#fpv-name`,
    `#fpv-cap` and `#fpv-grip` are all present.
44. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the six `.tiny` rules exist and the right-gutter arithmetic (56 + 8 + 56 = 120) is asserted against
    the CSS.
45. `no canvas text on the board layer` — a grep over the appended block and `broadcast_core.js` finds no
    `fillText` / `strokeText` inside the board draw path (§Viewer → Art); every string is DOM or is drawn
    inside the gutter panels.
46. `endcard labels` — `tests/test_crafter_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
47. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
48. `events are the closed enum` — `tests/test_crafter_events.nim`: the set of kinds `stepEvents` can emit
    equals exactly the twenty-one listed in §Server, and every kind used by the appended game block is in
    that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**

49. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` and runs it against **the replay `docker-smoke` produced** (downloaded as
    the `smoke-replay` artifact), in headless chromium (Playwright pinned 1.55.0 in both the npm module
    and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0`. **`--strict-text-bounds` stays on even though the board is
    pannable**, because §Viewer → Art forbids any canvas text on the board layer: every string this
    viewer draws lives in a fixed-size gutter panel or in the DOM, so a text run outside its canvas is
    always a bug here.
50. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, the CI replay's seat plays scripted and emits **no `say` at all**, so the smoke
    replay can never exercise the feed's narration path (the cogchemists 2026-08-24 scar). The fixture
    **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only the wasm
    entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) — driving the real
    page with a full-cap 160-rune `say`, all 22 checklist chips in both states, four zeroed vitals, a
    full inventory, a deep-night wash, a `death` endcard and a `22 OF 22` endcard, at several canvas
    widths including 360 px.
51. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm module
    against the committed fixtures, kept: wasm32-only failures (integer traps, address-space exhaustion)
    are invisible to the native shards, and this game's 1344-tick, 4096-cell replays are the biggest
    thing the module has to hold.

---

## Out of scope (v1)

- **Craftax's depth — all of it.** v1 ships **Crafter's 22-achievement scope** and nothing beyond it
  (the coordinator's steer, restated). Explicitly out: the dungeon floors and the ladder-descent
  mechanic, the bosses, spells and the mana/enchantment system, ranged weapons and potions, the
  attribute/level-up system, the extra creature roster (orcs, knights, trolls, pigmen), the extra
  materials (sapphire, ruby, chests), and the 65+ achievement set. Every one of them multiplies the
  world generator, the achievement predicate table and the viewer's checklist, and none of them changes
  what the LLM ladder measures until a policy can reliably reach a diamond in the flat world. When one
  can, Craftax depth is the obvious v2 and the achievement ledger already generalises to it.
- **Any `crafter` or `craftax` dependency, and bit-exactness with either.** Decided as a scoping rail
  before design and recorded in `docs/PORTING-CRAFTER.md`: no upstream code is vendored, no upstream
  numbers are claimed as reproduced, and no score from this coworld is comparable to a published
  benchmark number. This coworld implements the problem, not the package.
- **Pixel observations and a tensor interface.** The seat gets the symbolic observation of §Decisions.
  Crafter's 64 × 64 × 3 image observation, Craftax-Symbolic's flat float vector, and a per-tick RL socket
  are what `COGAME_EVENTS_URI`'s `Primitive` rows exist to make possible **later**; they are not a v1
  interface.
- **Per-primitive LLM stepping.** The seat batches up to twenty-four primitives a turn under a
  deterministic driver (§Decisions, divergence 4). One call per tick would be 1344 calls in a 720 s
  budget.
- **Seat counts other than 1, and world sizes other than 64 × 64.** `num_agents` is fixed at 1 in every
  variant and in the cert fixture; a multi-agent survival world is a different coworld (NMMO, which the
  idea itself names as the contrast). A second world size would fork the viewer's camera arithmetic and
  the generator's thresholds for no gain the idea asks for.
- **OpenSimplex noise, and terrain features it would buy** (rivers with flow, biome boundaries, caves as
  connected tunnels rather than noise pockets). The integer value-noise generator of §Sim module is what
  makes the wasm hash chain exact; a float noise field would not survive it.
- **Scoring survival, exploration, damage or crafting throughput directly.** `survivalTicks` is the
  tie-break and nothing more; `cellsSeen`, `blocksMined`, `blocksPlaced`, `itemsCrafted`, `damageDealt`
  and the kill counts are measured, recorded in `results`, shown on the endcard and drawn in the feed,
  and deliberately **not** in `scores` (§The game). Paying for blocks mined would let a policy farm the
  metric by mining and re-placing the same stone forever.
- **Computing the geometric-mean aggregate inside the game.** It is a cross-episode statistic; the game
  reports the per-episode booleans and `tools/crafter_score.py` / the phase-60 verifier does the
  aggregation (§The game → Scoring). A per-episode "score" that pretended to be the paper's number would
  be wrong on every episode.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, raycast fog, the
  first-person renderer, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, teams, four-team play, shouts, the fifteen paintball achievement ids, campaign
  mode, multi-game episodes, the procedural map generator, the map pool, the map editor and mapkit — all
  deleted, not disabled (§Sim module), and none of them return in v1.
