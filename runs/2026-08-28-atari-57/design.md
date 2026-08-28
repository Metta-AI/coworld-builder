# cogame-atari-57 — design note (2026-08-28, paintbot lineage)

`Metta-AI/cogame-atari-57` is **THE LEAGUE CABINET**: a four-seat, real-time **score-attack**
coworld in which four cogs play **the same game, from the same seed, at the same moment, in four
sealed lanes**, and the board is decided by one number — points on the screen when the credit runs
out. Nobody can touch anybody. There is no defence, no interference, no trade: there is only *how
good is your agent at this game*. Which game ("ROM") is loaded — `chomper`, `brickfall`,
`gallery` — is a manifest variant, announced before the round, stamped into the replay and printed
on the scorebug. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its read-only
mount `/workspace/starters/coworld-ctf`. **Every convention there holds here unless this note says
otherwise** — the 24 Hz wall-clock-paced game loop, the one-byte-per-seat-per-tick recorded action
log, the `COWLDCTF`-family replay codec with its per-tick `gameHash` chain, keyframes and lull
spans, the server-side decision layer (`src/ctf/{decide,directives,control,baselines,llm}.nim`:
**one parallel LLM batch per turn**, two bounded deadlines, an inter-batch rate floor, a budget
guard, tolerant parsing, rune caps, a scripted fallback), the mummy server and its `COGAME_*`
runtime contract, the seat/cog split and the `cogAlias` two-name-space rule, the broadcast chrome
(`client/replay_broadcast.html` + `client/chrome_common.js` + `client/broadcast_core.js`), the
emscripten static replay bundle (`replay-viewer/`, `Dockerfile.replay-viewer`,
`tools/build_replay_viewer.sh`) and the `GameVersion` prepend-only changelog discipline are all
inherited.

**Starter choice, in one line:** four lanes of a chunky 24 Hz arcade sim with **rules written fresh
for this coworld** is a **real-time game loop**, i.e. the **first** row of the starter table
(`prompts/10-design.md`; `playbooks/make-coworld.md` §Phase 0) — paintbot already ships, tested,
every layer this game needs except the arcade rules: an integer wall-clock-paced tick loop, a
per-tick per-seat action-byte log inside a replay whose hash chain is re-checked in the browser, a
server-side low-rate LLM decision layer over a per-tick deterministic controller, published scripted
baselines that emit the identical decision object, a **four-team-native** scorebug/momentum chrome
(`chrome_common.js:55`, `TEAM_ORDER = ['red','blue','green','yellow']`), and a static wasm viewer
that re-derives every frame. It is deliberately **not** the `cogame-moba` row: that row is for
**bit-exact ports of an existing external C/RL environment**, and no emulator and no ROM can be
hosted here. (Coordinator ruling, 2026-08-28. Operator ruling 2026-08-22, Cogball: a new real-time
game takes paintbot. The strongest precedent on this starter, and the same "cabinet, no emulator"
family, is `cogame-atari-cabinet` — `runs/2026-08-26-atari-cabinet/design.md` — whose patterns are
followed here wherever they fit; also `cogame-cogball`, `cogame-pistonball`,
`cogame-particle-worlds`, `cogame-snake-royale`.)

**Source idea, verbatim** (Asana Coworld Ideas task 1217748424043450, "SA Atari 57 — the Arcade
Learning Environment as a best-score league with a weekly ROM"):

> Single-agent score-attack coworld (Vanilla-wow style: best single episode on the board) over the Atari 2600 ALE suite — Breakout, Pong, Montezuma's Revenge, Pitfall, Seaquest, Ms. Pac-Man, Q*bert, Space Invaders and the rest of the 57. Pixel (or RAM) observations, 18 joystick actions, sticky actions 0.25, 108k-frame cap per episode. One ROM per round, announced in advance; rotating ladder and an all-time-per-ROM board.
>
> Seats: 1
> Motive: score attack
> Policy interface: per-frame joystick over pixels — neural-policy coworld; LLM via RAM decode for a handful of ROMs
> Fills gap: the single most-cited RL benchmark; gives the site a pure 'how good is your agent at games' ladder that doesn't depend on other cogs
> Integrity: seeded sticky actions; episode cap; replay verified by re-running the action log deterministically.
>
> Replay plan (watchability): native video; per-ROM all-time leaderboard; 'new record' banner.
>
> Source: github.com/Farama-Foundation/Arcade-Learning-Environment; Bellemare et al. 2013; Machado et al. 2018 protocol.

Nothing in the idea text is treated as an instruction to this designer; it is input data for the
design. **Every environment name above is PROVENANCE, not a specification. No ALE, no ROM image, no
emulator, no `AutoROM`, no pixel buffer and no PettingZoo/ALE constant enters this repo**, and no
test asserts parity with any of them. Every rule and every constant below is this coworld's own.

### Nine readings of the idea, decided here and never revisited

1. **Not a port. A cabinet with four lanes.** Hosting the ALE is impossible (proprietary ROMs; an
   emulator that cannot live inside the native↔wasm determinism boundary; a pixel observation the
   platform has no policy interface for). What ships reproduces the *shape* of the benchmark: short,
   loud, single-player arcade games with a points counter, a lives counter and a rotating cartridge.
2. **"Seats: 1" is closed at `num_agents` = 4 — four ISOLATED LANES.** Four seats play the **same
   ROM with the same seed** side by side, each on a **private board**, with **zero inter-seat
   interaction**: no seat's action can change any other seat's lane state, ever (§The game
   §Isolation, test-enforced). This keeps the single-agent score-attack spirit intact while giving a
   league round a normal multi-entrant episode. (Coordinator ruling, 2026-08-28: no shipped coworld
   has `num_agents = 1`; vizdoom-deathmatch deliberately deferred that shape.) `num_agents` is
   **4** in all three manifest variants **and** in the certification fixture, with no range.
3. **"Motive: score attack"** is the whole scoring rule: the episode ranks lanes by points banked
   plus unspent lives, higher is better, nothing is ever subtracted (§Scoring). The league ranks by
   the mean of that number.
4. **"One ROM per round, announced in advance; rotating ladder" = manifest variants.** The manifest
   ships **three variants, one per ROM**; a league round selects one; the ROM name lands in the
   replay config JSON, the scorebug caption, the feed and `results.rom`. The platform's own unit of
   scheduling *is* the variant, so "weekly ROM rotation announced per round" is literally variant
   selection, and it is public because the manifest is. **The ROM never changes the seat count.**
5. **Which three ROMs.** Three original mini-games, all on **one shared tile-grid engine**
   (§Sim module), each an archetype the idea's own list is built out of:
   **`chomper`** (maze-chomp — pellets, power pellets, four hunters), **`brickfall`**
   (brick-breaking — paddle, ball, a wall of bricks), **`gallery`** (shooter gallery — a marching
   formation, bolts, bunkers). Reason logged: three separate engines would be three observation
   models, three controllers, three renderers and three test suites — a design that does not get
   built. One engine (tile grid + avatar + sprites + a tile-effect table) plus three committed maps,
   sprite rosters and point tables is a **rules swap**, which is exactly what this starter row is
   for. All three are pure score-attack, all three fit one action byte, all three fit one 120 s
   clock.
6. **"18 joystick actions" → a 15-value action byte.** One byte per seat per tick, paintbot's own
   convention, decoded identically on the server and in the wasm replay runtime
   (§Resolution order step 2). It is *not* the ALE action set and is not claimed to be.
7. **"LLM via RAM decode"** is the idea's own diagnosis and it is what ships, with one refinement:
   because all three ROMs run on one engine, **one decoder serves all three**. The LLM sets one
   closed-schema **stance** per seat every **K = 120 ticks (5.0 s)**; a deterministic autopilot
   turns the standing stance into a **per-tick action byte** at 24 Hz. The byte is the action, the
   byte is what the replay records, the byte is what the viewer replays. The scripted baselines are
   *the same autopilot* driven by a fixed heuristic stance policy, so the two policy kinds are
   strictly comparable and a baseline is legal by construction.
8. **"Integrity: seeded sticky actions; episode cap; replay verified by re-running the action
   log"** ships as: one seeded stream **per lane, seeded identically**, so all four lanes face the
   *same* challenge; a hard **2880-tick episode cap**; anonymous colour aliases; and paintbot's
   per-tick `gameHash` chain re-checked in the browser against a re-simulation from the recorded
   action log — which is literally the idea's integrity clause, already built. **Stochastic sticky
   actions are replaced by deterministic turn latching** (§Resolution order step 3.2): same
   "you cannot turn on a dime" effect, no borrowed constant, no RNG in the control path.
9. **"Replay plan: native video; per-ROM all-time leaderboard; 'new record' banner."** "Native
   video" is not literal — the replay is the starter's binary action log re-simulated in wasm, which
   is strictly better than a video (seek, speed, hash-checked). The **new-record banner ships**: each
   ROM carries a committed **`parScore`** (the standing cabinet record) in the replay config, and a
   lane crossing it fires a `record` event, a scrubber beat and a full-width `NEW RECORD` banner in
   `#bannerlane` (§Viewer). The "all-time per-ROM board" is the platform league split by
   `results.rom`, and is §Out of scope as repo work.

**There is no `OPEN` section.** Every reading the idea leaves loose — seat count, which mini-games,
what rotation means, what the score is, how a joystick becomes an LLM decision, what ends the
episode — is a rail the designer decides, and each is decided below with its reason.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How atari-57 satisfies it |
|---|---|
| Starter by game shape | **`Metta-AI/coworld-ctf` (paintbot)** — a real-time 24 Hz loop with new rules. The arena rules (teams, guns, flags, fog, paint) are replaced by the lane engine; the loop, action-log replay, decision layer, viewer, chrome and CI wiring stay. (§Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-atari-57`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (champions `atari-57-highroller`, `atari-57-onecredit`) vs `PLAYER_SCRIPTED=arcader` / `PLAYER_SCRIPTED=hoover` (fillers). One image `coworld-atari-57`, one player entrypoint `/bin/atari-57-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`; ctf's `tools/build_replay_viewer.sh` kept (its ecos `mkdir -p` fix is already at line 22 of the starter's copy); the **same** `src/lane/sim.nim` compiles into `replay-viewer/atari57_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is ctf's page with a game block **appended**; the CRT quad-split, mazes, sprites and pips are baked at startup with pixie from ctf's shipped `data/font.ttf`, `data/darkbg.png`, `data/arena_floor.png`, `data/ascii.png`, `client/art/walls/wall_h.jpg`, `wall_v.jpg`, `client/art/lockerroom/bg.jpg` and the four `data/heart_<colour>.png`. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | In-game every lane is `RED`, `BLUE`, `GREEN`, `YELLOW` and nothing else; real policy names live only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (§Tests 8, 11). |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | ≈329 s expected / ≈464 s absolute worst case against the 720 s budget; a **660 s** engine hard stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** in variant `chomper`, variant `brickfall`, variant `gallery`, **and** `certification.game_config`; `<SEATS>` = **4** in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Four lanes. One cartridge. One credit. Two minutes.** Every seat gets its own **17 × 17 tile
screen**, its own avatar, its own sprites, its own three lives and its own points counter. All four
screens are loaded with the **same ROM** and the **same seed**, so the maze is the same maze, the
brick wall is the same wall, the invader formation is the same formation and the nth random draw in
lane 0 is the nth random draw in lane 3. When your lives run out your screen says `GAME OVER` and
your points freeze. When the clock runs out, or all four screens are over (and not before
`minTicks`), the credit is spent and **the highest score wins**.

That is the entire game. There is no way to attack, block, steal from or even reach another lane —
which is the point: this is the platform's one pure "how good is your agent at games" ladder.

### Seats, lanes, aliases

**`num_agents` = 4. One seat = one lane = one quadrant of the cabinet screen.** Reasons, in order:
(a) the platform's normal fill is two champions plus two fillers, so four seats make the cross-play
mean meaningful from round one; (b) no shipped coworld has `num_agents = 1` and the ladder needs a
normal multi-entrant episode; (c) four parallel LLM calls per turn sit inside the Bedrock sidecar's
30-requests-per-minute-per-episode cap at a 12 s batch floor (§Decisions); (d) ctf's chrome is
already four-team-native, so four plates, a four-curve momentum graph and a four-row endcard need no
structural change; (e) four lanes in a 2 × 2 quad-split is the one arrangement that keeps a square
board and stays legible in a 360 px iframe (§Viewer). The idea's "Seats: 1" is closed here at **4**
and is 4 in all three manifest variants, in the certification fixture and in `SMOKE_SEATS`.

**Seat `s` plays lane `s`.** There is deliberately **no seat→lane permutation**: the four lanes are
identical by construction (same map, same seed, same schedule), so a permutation would be pure
decoration and one more thing to get wrong. What *is* dealt is nothing at all; what is hidden is who
holds which seat (§Server).

| lane `s` | quadrant (tile origin in the 35 × 35 board) | colour / alias | chrome `teams` key |
|---|---|---|---|
| 0 | top-left `(0, 0)` | **`RED`** | `red` |
| 1 | top-right `(18, 0)` | **`BLUE`** | `blue` |
| 2 | bottom-left `(0, 18)` | **`GREEN`** | `green` |
| 3 | bottom-right `(18, 18)` | **`YELLOW`** | `yellow` |

Colour aliases rather than `LANE-n` because a spectator reads "GREEN clears the screen" instantly
and an LLM writes nothing about rivals at all (it has no lever over them) — the alias exists so the
scorebug, the feed and the endcard can name a lane without naming an entrant (the legibility pin:
"render 10, not T").

### Isolation — the invariant, stated once and tested

`stepLane(lane, cmd, laneRng)` is a **pure function of one lane's own state, that lane's own action
byte and that lane's own RNG stream.** It takes no `SimServer`, reads no other lane, and writes no
other lane. The tick loop calls it four times. Consequences, all pinned by `tests/test_isolation.nim`
(§Tests 3):

- Replacing lane `j`'s action byte stream with anything at all leaves lane `i ≠ j`'s per-tick state
  **bit-identical**.
- Running lane `i` alone in a one-lane sim reproduces its four-lane trajectory exactly.
- Four lanes given the identical action byte stream end with identical points, lives and sprite
  positions (the fairness proof: same seed really does mean same challenge).

**The one thing that crosses lanes is the scoreboard, and it crosses in the observation layer only.**
Each seat's observation carries every rival alias's **score, lives and screen number — nothing
else** (no rival board, no rival sprites, no rival stance). Decision, with its reason: an arcade
marquee shows the board, and score attack has exactly one strategic lever — *bank or push* — which
is unusable without knowing whether you are ahead. It is information, it is symmetric, it is
one-directional, and it cannot alter any lane's physics, because the scoreboard is composed
**outside** `stepLane` by `observation.nim` and never read by the sim. `tests/test_isolation.nim`
asserts the sim module never imports the scoreboard composer.

### World, units, and why they are integers

The whole sim runs in **integers**, for Cogball's, Tandem's, pistonball's and atari-cabinet's reason:
replays are re-simulated by the **emscripten/wasm32** build of the same Nim module that the **native
amd64** server ran, and their per-tick `gameHash` chains must match bit-for-bit. Integers make that
true by construction rather than by an argument about two builds of libm agreeing.
`src/lane/{sim,grid,rom,sprites,maps}.nim` contain **no floating point at all** (grep-enforced in
CI, §Tests 2d).

| Quantity | Unit | Type |
|---|---|---|
| Position, size | **micro-units (µu)**; **1 tile = `TileU` = 12 000 µu** | `int32` |
| Velocity | µu per tick | `int32` |
| Tile coordinate | `col, row ∈ 0 … 16` | `int8` |
| Direction | `0 = stay, 1 = up, 2 = down, 3 = left, 4 = right` | `uint8` |
| Points | whole arcade points | `int32` |
| Score accumulator | **micro-points** (1e-6 of a score point) | `int64` |
| Counters (lives, deaths, screens, chains, shots) | — | `int32` |

**Lane grid:** `GridW = GridH = 17` tiles, origin top-left, **x right, y down** (ctf's screen
convention). A lane spans `x, y ∈ [0, 204 000] µu`. Tile `(col, row)` covers
`x ∈ [col·12 000, (col+1)·12 000)`; its **centre** is `(col·12 000 + 6 000, row·12 000 + 6 000)`.

**Board:** the four lanes are drawn into one **35 × 35 tile** board — lane origins at tile
`(0,0)`, `(18,0)`, `(0,18)`, `(18,18)` with a **1-tile gutter** at column 17 and row 17. Board render
scale **40 board pixels per tile** → `MapWidth = MapHeight = 1400`, board aspect **1:1**. That is
1 960 000 logical map pixels, comfortably under ctf's `MaxSupersampledMapPixels = 8 000 000`
(`src/ctf/global.nim:1095`), so `boardRenderScaleFor` still returns `RenderScale = 2` and
`predictedViewerRenderBytes(1400, 1400) = 1 960 000 · 4 · (4·2² + 6) = **172 480 000 bytes
(172 MB)**` against `WasmViewerBudgetBytes = 1 600 000 000` — the viewer's load-time capacity
preflight (`replay-viewer/atari57_replay.nim`) passes with 9× headroom, and every one of those
constants is **kept unchanged**.

**Tile coordinates** are the only coordinates a policy, the chrome or this note ever quotes:
`col, row ∈ 0 … 16`, `(0,0)` top-left of **your own lane**. Sub-tile positions shown to a policy are
rounded to 2 decimals in tiles (`x_tiles = x_µu / 12 000`). A policy never sees board coordinates and
never sees another lane's coordinates at all.

**No trigonometry and no square roots anywhere in the sim.** Every collidable is a tile or an
axis-aligned box; every contact test is a box overlap or an integer axis crossing; the only
non-axis-aligned motion in the game is `brickfall`'s ball, whose velocity comes from a **committed
7-entry integer fan table** (§`brickfall`) and whose reflections negate one component.

### The three ROMs (the rotation)

One engine; three cartridges. A cartridge is: a committed **17 × 17 tile map**, an **avatar mode**, a
**sprite roster** over the three shared behaviours, a **point table**, a **life-loss rule**, a
**screen-clear rule** and a **difficulty ramp**. `src/lane/rom.nim` applies configuration in this
**exact order**: **schema defaults → the named `rom` preset → any explicitly supplied config key**,
so the certification fixture can override `livesPerLane` on top of `rom: "chomper"` (§Packaging), and
`tests/test_rom.nim` pins the order (§Tests 13).

| config key | `chomper` | `brickfall` | `gallery` | meaning |
|---|---|---|---|---|
| `rom` | `chomper` | `brickfall` | `gallery` | the ROM name, stamped everywhere |
| `livesPerLane` | **3** | **3** | **3** | credits per lane |
| `avatarMode` | `freeGrid` | `railBottom` | `railBottom` | how the avatar may move |
| `avatarSpeed` (µu/tick) | **1 500** | **2 200** | **1 900** | 8.0 / 5.5 / 6.3 ticks per tile |
| `parScore` | **2 600** | **1 800** | **2 000** | the standing record; crossing it fires the banner |
| `spriteRoster` | 4 × `Chaser` | 1 × `Ballistic` | 32 × `Marcher`, ≤ 1 `Saucer`, ≤ 3 bolts | which sprites exist |
| `fireEnabled` | false | false | **true** | whether action `fire` does anything |
| `brakeEnabled` | **true** | false | false | whether action `brake` does anything |
| `screenClearBonus` | **500** | **350** | **300** | points for clearing the screen |
| `rampPermille` | **1 060** | **1 150** | **1 200** | per-screen speed multiplier (×1.060 / ×1.150 / ×1.200) |

Everything else — grid size, tile size, tick rate, `maxTicks`, `minTicks`, the decision cadence, the
wall-clock budget, the action byte, the scoring formula and `num_agents` — is **identical across all
three ROMs**, which is what makes one score scale, one budget arithmetic and one test matrix correct
for all of them.

#### `chomper` — maze-chomp

The committed map `Maps.chomper` (`src/lane/maps.nim`, a 17-string literal, hash-pinned by
§Tests 4). `#` wall, `.` pellet, `o` power pellet, `P` the avatar's start tile, space = tunnel mouth:

```
#################
#o.............o#
#.##.###.###.##.#
#.##.###.###.##.#
#...............#
#.##.###.###.##.#
#.##.###.###.##.#
#.##.###.###.##.#
 ............... 
#.##.###.###.##.#
#.##.###.###.##.#
#.##.###.###.##.#
#.......P.......#
#.##.###.###.##.#
#.##.###.###.##.#
#o.............o#
#################
```

**120 pellets, 4 power pellets, 127 walkable tiles, one wrap tunnel across row 8** (leaving column 0
re-enters at column 16 and vice versa). Verified connected from `P` at `(col 8, row 12)`: all 127
walkable tiles reachable.

- **Avatar**: `freeGrid` — moves along corridors at `avatarSpeed`, turns only at tile centres, with
  the 6-tick turn latch of §Resolution order 3.2. `brake` halves speed for that tick (a real control
  affordance: it is how you let a hunter commit before you do).
- **Sprites**: four `Chaser`s (`H0…H3`) starting at tile centres `(8,4)`, `(4,8)`, `(12,8)`, `(8,1)`.
  A chaser moves at **1 250 µu/tick** (`Chasing`), **900 µu/tick** (`Fleeing`), **2 000 µu/tick**
  (`Returning`). At every tile centre it picks the legal direction (never a reverse unless it is the
  only legal one) minimising the tunnel-aware Manhattan distance to its **target tile**; ties break
  in the fixed order UP, LEFT, DOWN, RIGHT. Targets, one personality each, all deterministic:
  `H0` = the avatar's tile; `H1` = 2 tiles ahead of the avatar's facing; `H2` = 4 ahead; `H3` = 6
  ahead (clamped into the grid). Every `scatterTicks` the roster flips to `Scatter` for
  `scatterHoldTicks`, targeting the four corner tiles instead — `scatterTicks` is drawn per screen
  from the lane RNG in `[360, 600]` and `scatterHoldTicks` is fixed at 120.
- **Points**: pellet **10**, power pellet **50**, eating a `Fleeing` chaser **100 / 150 / 200 / 250**
  by chain position within one power window, screen clear **+500**.
- **Power window**: eating a power pellet puts every non-`Returning` chaser into `Fleeing` for
  **`powerTicks = 144`** ticks (6.0 s), reversing its direction once; the chain counter resets to 0.
  An eaten chaser becomes `Returning` and walks back to `(8,4)` before resuming.
- **Life lost**: the avatar's box overlaps a `Chasing`/`Scatter` chaser's box (both boxes are
  `8 000 µu` on a side, centred).
- **Screen clear**: every pellet and power pellet gone → `+500`, a fresh map, `screen += 1`, chaser
  speeds ×`rampPermille/1000`.

#### `brickfall` — brick-breaking

`Maps.brickfall`: walls on row 0 and columns 0 and 16; **row 16 is the drain** (open, no wall);
bricks `=` on rows 3–6, columns 1–15; the avatar (a 3-tile-wide paddle) rails along **row 15**.

```
#################
#...............#
#...............#
#===============#
#===============#
#===============#
#===============#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#......___......#
                 
```

- **Avatar**: `railBottom` — only `left`/`right` do anything; the paddle spans 36 000 µu (3 tiles)
  and its centre is clamped to `x ∈ [18 000, 186 000]`. `up`, `down`, `fire`, `brake` are no-ops.
- **Sprite**: one `Ballistic` ball, box half-side `3 000 µu`, served from tile centre `(8, 12)` after
  a **24-tick** serve delay with velocity `BallFan[j]` for `j` drawn from the lane RNG in `{1,2,4,5}`
  (never straight down, never a wall-grazer).
- **The fan** — `BallFan*: array[7, tuple[vx, vy: int32]]`, a **committed literal table** in
  `src/lane/sprites.nim`, indexed by which seventh of the paddle the ball struck (0 = far left,
  6 = far right); every entry has `vy < 0` (**a paddle can never send a ball back into the drain**)
  and a magnitude within ±5 % of 2 800 µu/tick, both asserted exhaustively by §Tests 1:

  ```
  BallFan = [(-2600,-1200), (-2100,-1900), (-1200,-2500), (0,-2800),
             (1200,-2500), (2100,-1900), (2600,-1200)]
  ```
- **Reflection**: off a vertical face `vx := -vx`; off a horizontal face `vy := -vy`. Off the paddle
  the velocity is replaced by `BallFan[j]` scaled by the current speed multiplier.
- **Speed ramp**: every 8 brick hits, `speedPermille := min(speedPermille + 50, 1 400)`; the applied
  velocity is `(v · speedPermille) div 1000`. `BallSpeedMax = 3 920 µu/tick` at the cap.
- **Points**: brick row 3 = **50**, row 4 = **30**, row 5 = **20**, row 6 = **10** (1 650 per screen);
  screen clear **+350**.
- **Life lost**: the ball's centre crosses `y = 192 000 µu` (the top of row 16) — the drain.
- **Screen clear**: no bricks left → `+350`, a fresh wall, `screen += 1`, `speedPermille` ×1.150.

#### `gallery` — shooter gallery

`Maps.gallery`: walls on row 0 and columns 0 and 16 and row 16; bunker tiles `X` on row 12 at columns
3, 4, 7, 8, 11, 12 (each takes 3 hits, then vanishes); the avatar rails along **row 14**.

```
#################
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#...............#
#..XX..XX..XX...#
#...............#
#.......___.....#
#...............#
#################
```

- **Avatar**: `railBottom`, 3 tiles wide, centre clamped to `x ∈ [18 000, 186 000]`. **`fire`** spawns
  a friendly bolt (`vy = -4 000 µu/tick`) from the paddle centre, at most **2 in flight**, with a
  **6-tick** reload.
- **Sprites**: **32 `Marcher`s** in a 4 × 8 formation, rows 2–5, columns 1, 3, 5, 7, 9, 11, 13, 15.
  The formation moves as one body: every `marchTicks` (screen 1: **20** ticks) it steps **one tile**
  horizontally; when any marcher would leave columns 1…15 the whole body steps **one tile down**
  and reverses. `marchTicks` shortens by `div 1000 · 1000/rampPermille` per 8 marchers destroyed
  (integer: `marchTicks := max(4, marchTicks * 1000 div rampPermille)`), so a thinning formation
  accelerates. A live marcher fires a hostile bolt (`vy = +2 600`) when the lane RNG's per-tick draw
  is below `fireChancePermille = 18` and fewer than 3 hostile bolts are in flight; the firing marcher
  is the lowest live one in a column drawn from the lane RNG.
- **`Saucer`**: with probability `12/1000` per tick, and never within 240 ticks of the last one, one
  `Marcher`-behaviour saucer crosses row 1 at 3 000 µu/tick from a drawn side. **100 points.**
- **Points**: marcher row 2 = **30**, row 3 = **20**, rows 4 and 5 = **10** (560 per wave); saucer
  **100**; wave clear **+300**.
- **Life lost**: a hostile bolt's box overlaps the avatar's box, **or** any marcher reaches row 13.
  (Reaching row 13 costs one life *and* resets the formation to rows 2–5, so it is a setback, not an
  instant game over.)
- **Screen clear**: all 32 marchers destroyed → `+300`, a fresh wave starting one row lower (rows
  3–6, then 4–7, capped at rows 5–8), `screen += 1`, `marchTicks` ×1000/1200, bunkers restored.

### Time, and the episode cap

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf** (`src/ctf/sim_types.nim:317,376`), because
every speed-coupled layer (`PlaybackSpeeds`, the lull scan, the momentum series, `tickTime`, the
transport bar) is keyed to it. There are **no substeps**, and the arithmetic that makes that a
guarantee rather than a hope:

- The fastest thing in the game is a `gallery` bolt at 4 000 µu/tick and a capped `brickfall` ball at
  3 920 µu/tick.
- The shallowest contact window is half a tile plus a box half-side: `6 000 + 3 000 = 9 000 µu`.
- `9 000 > 4 000`, so **every collidable is overlapped for at least two consecutive end-of-tick
  positions**, in every legal configuration. `tests/test_physics.nim` asserts the inequality directly
  *and* cross-checks the swept test against the end-position test over 50 000 randomised states
  (§Tests 1).

An episode is **`maxTicks` = 2880 ticks = 120.0 s of sim time** (the idea's "108k-frame cap",
rewritten at this game's own scale), with a floor of **`minTicks` = 1440 ticks = 60.0 s**: the
episode does **not** end early on "all four lanes over" before `minTicks` — over lanes simply sit on
their `GAME OVER` screen. Reason logged: a replay shorter than the viewer smoke's 12 s soak reads as
"frozen" (ecos, 2026-08-23), and a league round that ends at 20 s because four bots died fast is
unwatchable. 2880 ticks is **24 decision turns of `turnTicks` = 120 ticks (5.0 s)**.

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 120 == 0` and `phase == Playing`: the stances collected for turn
   `t div 120` become each seat's `activeStance[seat]` (§Server), quantised to integers on parse. The
   server writes one **`stance` chat record per seat** into the replay. `activeStance` is **not**
   mixed into `gameHash` — the per-tick action bytes it produces are recorded, and those are what the
   viewer replays (step 2).
2. **Autopilot compile**, in **lane index order 0 → 3**. `control.laneCommand(sim, s) -> uint8` is a
   pure function of `(lane s's own state, lane s's active stance, the tick)` returning an
   **action byte** `cmd ∈ 0 … 14`:

   ```
   dir = int(cmd) mod 5        # 0 stay, 1 up, 2 down, 3 left, 4 right
   act = int(cmd) div 5        # 0 none, 1 fire, 2 brake
   ```

   15 of the 256 byte values are legal; **`cmd >= 15` is repaired to `0`** (`dir = 0`, `act = 0`)
   both in the server and in the replay runtime, so a corrupt byte can never desynchronise the two.
   The autopilot sits **outside** the determinism boundary, exactly as ctf's `control.nim` does, and
   may use floating point; the byte it produces is written to the replay with
   `replayWriter.writeInputMaskChange(tickTime(t), seat, cmd)`, which already writes **only on
   change** and updates `lastMasks[seat]` (`src/ctf/replays.nim:161`). Nothing else in the loop is
   re-derived at playback.
3. **`stepLane(lane[s], cmd[s], laneRng[s])`**, for `s` in **0 → 3**, each call touching only its own
   lane. Inside one lane, in this order:
   1. **Lane phase.** `Over` → nothing happens for the rest of the episode (the screen is frozen and
      `GAME OVER` is drawn). `Dying` (24 ticks) and `Respawning` (24 ticks) → tick the timer, draw
      the death animation, and on the `Respawning` timer reaching 0 restore the avatar and every
      sprite to the ROM's respawn layout (pellets, bricks and destroyed marchers are **not**
      restored — only positions). Neither phase draws from the RNG.
   2. **Turn latch.** `dir` is written into `pendingDir` with `pendingAge = 0`. The avatar's
      `facing` becomes `pendingDir` at the first tick at which the avatar is within `640 µu` of a tile
      centre **and** that direction is legal for the ROM's `avatarMode`; a `pendingDir` older than
      **`latchTicks` = 6** ticks is discarded. (This is the deterministic replacement for the idea's
      stochastic sticky actions: you cannot turn on a dime, and no RNG is involved.) A reverse along
      the current axis is always legal and applies immediately.
   3. **Avatar motion.** `pos += facingVector · speed`, where `speed = avatarSpeed`, halved for this
      tick if `act == 2` and the ROM has `brakeEnabled`. `freeGrid` clamps to the corridor (a move
      into a wall tile stops the avatar at the tile centre); `railBottom` clamps the paddle centre to
      `[18 000, 186 000]` and ignores `up`/`down`. Tunnel wrap (`chomper`, row 8) applies here.
   4. **Avatar–tile effects.** The tile under the avatar's centre is resolved through the ROM's
      tile-effect table: `Pellet → +10`, tile becomes `Floor`; `Power → +50`, tile becomes `Floor`,
      the power window opens, the chain counter resets. `points` is a running total.
   5. **Fire.** If `act == 1`, the ROM has `fireEnabled`, fewer than 2 friendly bolts are live and the
      reload timer is 0 → spawn a bolt at the avatar's centre, set the reload timer to 6,
      `shotsFired += 1`.
   6. **Sprite motion and sprite–tile contacts**, in **sprite id order**. Each sprite advances by its
      behaviour (`Chaser`, `Ballistic`, `Marcher`) and resolves the **earliest** axis crossing along
      its swept segment against, in this priority order on an exact tie: **(a) the avatar box**,
      **(b) destructible tiles** (bricks, bunkers) in `row` then `col` order, **(c) other sprites
      that are legal targets for it** (a friendly bolt vs a marcher; nothing else), **(d) wall
      tiles**, **(e) the lane bounds**. Crossing times are compared by integer cross-multiplication
      in `int64`; no division, no `isqrt`, no `float`. **One sprite takes at most one contact per
      tick**; the remaining displacement is applied without further contact resolution, which is safe
      because §Time proves nothing is thinner than one tick of travel.
   7. **Contact effects.** Brick destroyed → its row's points, tile becomes `Floor`, ball reflects off
      the crossed face, `brickHits += 1`, a `chip` event. Bunker hit → `bunkerHp -= 1` (vanishes at 0),
      bolt consumed, **no points**. Friendly bolt vs marcher → marcher destroyed, its row's points,
      both consumed, `marchTicks` recomputed. Hostile bolt vs avatar → life lost. Chaser vs avatar →
      `Fleeing` chaser eaten (chain points, chaser becomes `Returning`, `chain += 1`,
      `bestChain = max(bestChain, chain)`) else life lost. Saucer leaving the lane → despawn.
   8. **Life loss.** `lives -= 1`, `deaths += 1`, phase `Dying` for 24 ticks, a `life_lost` event. If
      `lives == 0` → lane phase `Over`, `overTick = t`, a `lane_over` event, and this seat is dropped
      from every later LLM batch.
   9. **Wave / spawn schedule.** Advance the ROM's timers (chaser scatter flip, saucer spawn roll,
      marcher fire roll). **Every** RNG draw in the game happens here or at a serve/screen reset, in
      this fixed order, through one helper `drawInt(lane, lo, hi): int32` implemented as
      `int32(lo + int32(laneRng.next() mod uint64(hi - lo + 1)))` — `next()` is `std/random`'s
      `uint64`-domain step, so **no draw ever touches `rand(int)`**, whose `int` is 32-bit under
      `--cpu:wasm32` and 64-bit natively (ctf's documented hazard). A per-lane monotonic `rngDraws`
      counter is mixed into `gameHash`.
   10. **Screen clear.** If the ROM's clear predicate holds → `screenClearBonus` points,
       `screensCleared += 1`, rebuild the screen with the ramp applied, a `screen_clear` event.
   11. **Record check.** If `points > parScore` and `recordFlag` is false → `recordFlag = true`, a
       `record` event (the banner and a scrubber beat).
4. **Score fold.** `scoreMicro[s] = 10 000 · points[s] + 1 000 000 · lives[s]` (§Scoring). A running
   total, recomputed nowhere else.
5. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged. `gameHash` mixes `tick`, `phase`, and for **every lane**: `lanePhase`, `phaseTimer`,
   `lives`, `points`, `screen`, `overTick`, the avatar's `pos`, `facing`, `pendingDir`, `pendingAge`,
   the full tile bitmap (pellets/bricks/bunker HP), every sprite's `kind`, `state`, `pos`, `vel`,
   `timer`, the power window, the chain counter, `speedPermille`, `marchTicks`, `reload`, `rngDraws`
   and `scoreMicro`. It never mixes FX, notes, `say`, feed text, stances or policy labels.
6. **End checks**, in this order: wall-clock stop tripped → end `deadline` / `wall_clock` (recorded as
   a load-bearing `stopped` replay record, §Replay bytes); `t + 1 ≥ minTicks` **and** all four lanes
   `Over` → end `complete` / `all_lanes_over`; `t + 1 ≥ maxTicks` → end `complete` / `full_time`; an
   invariant guard failure (an avatar or sprite centre outside the lane, a velocity above
   `BallSpeedMax`, a `dir` outside `0..4`, `lives` outside `0..livesPerLane`, `points` negative, a
   tile index outside `0..288`, an `int32` overflow caught by the debug build's range checks) → end
   `fault` / `sim_fault`.

There is no rescue rule, no mercy and no difficulty *reduction*. A lane whose avatar never moves
loses three lives and finishes with a score near zero — a legible, correctly scored failure.

### Scoring, sign, and what the league ranks by

Score attack, and nothing else. Both terms are **non-negative**, so the minimum score is `0.000` and
**higher is always better**; dying is punished by *not keeping* the lives term rather than by a
negative number, which keeps the whole scale readable on a scorebug.

```
scoreMicro[s] = 10_000 * points[s]        # 100 arcade points = 1.000 score
              + 1_000_000 * lives[s]      # each unspent life = 1.000 score

score[s]       = scoreMicro[s] / 1_000_000     # emitted as a double, 3 decimals
results.scores = [score[0..3]] in SEAT order
results.placements = [1..4] in SEAT order, a permutation
results.win        = [placement == 1] in SEAT order
```

Because `points` and `lives` are both defined at **every** tick, the score is defined at every tick —
which is what makes the `deadline` ending scorable and the momentum graph honest (it dips 1.000 the
instant you die, then climbs as you bank).

The three `parScore` values (2 600 / 1 800 / 2 000, §The ROM table) were chosen so a strong run lands
in the same **18 … 30** score band in all three ROMs, so a league board that mixes ROMs stays
meaningful — even though (see below) a round normally does not mix them.

**Placement**, computed once at game over by this exact chain:

1. higher `score`;
2. then more `lives` left;
3. then **earlier `lastScoreTick`** (the tick of the seat's last scoring event — reaching the same
   total sooner is better play);
4. then **lower seat index**.

The index tiebreak makes the chain total, so `placements` is always a strict permutation of `1..4`
and exactly one seat wins. There are no shared places.

Worked examples (`chomper`, `livesPerLane = 3`, `parScore = 2 600`):

| Outcome | points | lives left | **score** |
|---|---|---|---|
| Cleared two screens, one death, banked a full power chain | 4 210 | 2 | **44.100** |
| Cleared one screen, two deaths | 2 480 | 1 | **25.800** |
| One screen minus 20 pellets, no deaths | 1 700 | 3 | **20.000** |
| Died three times before the first power pellet | 430 | 0 | **4.300** |
| Avatar never moves (every byte 0) | 0 | 0 | **0.000** |
| `hoover` — greedy, ignores hunters | 1 250 | 0 | **12.500** |
| `arcader` — risk-aware baseline, typical | 2 340 | 1 | **24.400** |

**What the league ranks by: the seat's mean `results.scores` value across its episodes — its
cross-play mean.** Elo over `placements` is also legitimate here (the four scores are distinct and
one seat always wins), but the **primary and declared metric is the mean score**, because score
attack *is* a cardinal metric and because the ROMs are tuned to one band. Phase 50 ranks on mean
score. `results.rom` records which ROM an episode played, so a board can always be split per ROM
afterwards — which is the idea's "all-time-per-ROM board".

**The ROM and the league round.** A league round selects **one** variant, so a round does not mix
ROMs; this is the idea's "one ROM per round, announced in advance", and it is announced by
construction because the manifest is public.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail. No
other value may appear in either field.

| `reason` | `endRule` | When | Scored |
|---|---|---|---|
| `complete` | `all_lanes_over` | `t ≥ minTicks` (1440) **and** all four lanes have spent their lives. | as at that tick |
| `complete` | `full_time` | `maxTicks` (2880) reached with at least one lane still alive. The normal ending. | as at `maxTicks` |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed first. The sim stops at that tick, scores the state as it stands, writes the game-over frame and a complete replay up to that tick. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. | as at the stop tick |
| `fault` | `sim_fault` | A step-6 invariant guard tripped. Partial replay written. | as at the fault tick |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts written before re-raising. | as at the fault tick |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2880 = 120 s of
lobby) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only, `src/ctf/server.nim:1199`), its lane is driven by
the `arcader` baseline for the whole run, and the run plays to a normal ending. Three live lanes
against one baseline is still a full score-attack board.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {arcader, hoover}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=arcader`. A scripted policy seated as a champion is a FAILURE state.

### Where the decision happens, and the LLM client

In the **game server**, not the player container — paintbot's own architecture (`src/ctf/llm.nim`,
`src/ctf/decide.nim`, `src/paintball_player.nim`), kept. The `anthropic_api_key` coworld secret is
injected into the *game* pod via
`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/atari-57/anthropic_api_key`; without that
manifest env the hosted container never receives the secret and every league episode plays scripted
while local certify still passes (hive, 2026-08-23). Phase 60 greps the *game* log for
`falling back` / `LLM provider is unavailable`.

`src/lane/llm.nim` is `src/ctf/llm.nim` with the identifier rename only. Kept exactly:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`)
  → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (`readCogameUri`) → **none** (client
  `disabled = true`; every turn falls back instantly with no network wait, which is what lets offline
  certification finish in seconds).
- **One** Bedrock model candidate: `us.anthropic.claude-haiku-4-5-20251001-v1:0`. No sonnet inference
  profile is a candidate — every one of them times out on every sidecar call (cogame-raid round 2,
  2026-08-23). The `throttled` fast-fail that skips the retry when the provider answered 429 with no
  other candidate is kept verbatim: a retry inside the same turn cannot succeed.
- `max_tokens = 900` (400 truncates). **No `output_config.effort`** for haiku. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`. No `temperature`.
- A system prompt that demands the reply **begins with `{`** (Haiku answers prose-first otherwise).
- `extractJsonObject` (first `{` … last `}`, fence-tolerant) and the **rune-boundary** truncation
  (`runeLen`/`runeSubStr`), kept.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **K = 120 ticks (5.0 s of sim time)**, **24 turns** per episode. At each turn
the server builds the request bodies for every seat **whose lane is not `Over`** and issues them as
**ONE parallel batch** — `client.curl.makeRequests(@[req0 … req3], timeout)`, curly's batch API, which
is exactly what `src/ctf/decide.nim:427` already does. **Seats are never queried sequentially.** At
most 4 calls per turn × 24 turns = **96 calls** per episode, at most 4 in flight, and fewer once lanes
end.

The binding constraint is not latency, it is the **Bedrock sidecar's cap of 30 requests per minute per
episode** (playbook gotcha, raid round 2). Four requests per batch means a batch may start at most
every 8 s; the design uses **`turnSpacingMs` = 12 000** → 4 requests / 12 s = **20 rpm**, comfortably
under. That, not the model, is why there are 24 turns and why a turn is 5.0 s of sim time.

Per-turn timing, all monotonic-deadline bounded, every deadline a whole number of seconds because
curly hands it to `CURLOPT_TIMEOUT`, whose granularity is whole seconds and whose conversion **floors**
(`src/ctf/decide.nim:419-428`):

- attempt 1 batch deadline **`attempt1Ms = 9 000`** (four parallel haiku calls; ~3–6 s typical);
- every seat that timed out, errored, returned non-JSON or returned no usable stance is retried
  **once**, again as a single batch, deadline **`retryMs = 5 000`** — unless the client is
  `throttled`, in which case the retry is skipped outright;
- the whole turn is wrapped in **`turnBudgetMs = 16 000`** (`attempt1Ms + retryMs = 14 000 ≤ 16 000`,
  asserted by §Tests 12);
- the **inter-batch wall floor** of 12 000 ms is measured start-to-start and is a bounded,
  stop-interruptible `sleep`.

```
turn 0 batch starts at t = 0; turns 1..23 start 12 s apart      = 276 s
last turn's own LLM cost (<= 16 s hard cap)                     =  16 s
lobby / connect wait for 4 player pods (typical 15 s;
  cap lobbyJoinTimeoutTicks 2880 = 120 s)                       =  15 s   (typical)
2880 ticks x 4 lanes of physics + 4 autopilots/tick             =   3 s
game-over hold + results + replay write (retrying uploader)     =  20 s
                                                                -------
expected total                                                  ~330 s   < 720 s budget
absolute worst case (120 lobby + 276 + 16 + 3 + 20 + 30 slack)  ~465 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                          = 660 s  -> reason "deadline"
platform kill (episodeTimeoutSeconds)                            = 1200 s
```

`fastMode: true` in every variant: the sim advances as soon as every player container has
acknowledged the frame, so sim time is not charged against the wall clock — the decision turns are the
pacing. The seats send no inputs at all (the server computes every action byte), so
`docs/PROTOCOL.md`'s warning about the Sprite v1 Ready packet (`0x85`) corrupting dead-reckoned input
timing does not apply, and the player harness sends `0x85` after every frame exactly as
`src/paintball_player.nim` does.

**Budget guard (settles early without shortening the run).** At the start of each turn, if
`elapsed + 2 × (turnSpacingMs + turnBudgetMs) > wallClockBudgetSeconds`, the LLM is switched off for
every remaining turn and the run finishes on the scripted layer (microseconds per turn), so the
episode ends `complete/*` rather than `deadline`. A `budget_guard` record names the turn it fired.
This is ctf's own guard (`src/ctf/decide.nim:340`), retargeted to include the batch spacing.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the inter-batch floor, the
outer per-turn deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the
serve thread (which runs independently of the game loop, so a 16 s LLM stall cannot drop four
connections), the 660 s engine stop, and ctf's `gameOverTicks` hold before exit. There is **no
unbounded loop anywhere in the sim**: no rejection sampling (every draw is a single `drawInt`), no
pathfinding without a node cap (the autopilot's BFS is bounded at 300 nodes), no while-loop whose
bound is not a constant. On **two** consecutive failures for a seat (attempt + retry, or one attempt
when `throttled`) that seat's stance for the turn is the **`arcader`** stance and a `fallback` record
is written with `cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials,
budget_guard}`. A seat that disconnects mid-run keeps playing: its stance source degrades to `arcader`
and revives on reconnect. **No failure mode leaves a lane uncommanded** — the autopilot always has a
stance: this turn's, else last turn's, else `arcader`'s.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are ONE cog at ONE cabinet in a four-cabinet arcade. All four cabinets are
running the SAME game from the SAME seed at the SAME moment, each on its own
private 17x17 screen. You cannot see, touch, help or hurt any other cabinet, and
nothing you do can change their screens. This is a SCORE ATTACK: the highest
score on the board when the credit runs out wins.
Your screen is 17 columns by 17 rows. (col 0, row 0) is the TOP-LEFT of YOUR
screen. col grows RIGHT, row grows DOWN.
You have 3 lives. Losing your last life ends YOUR game; your points freeze and
the other three play on. Points are never taken away.
SCORE = points / 100 + lives you still have. So one unspent life is worth 100
points, and dying to grab a 50-point pellet is a bad trade.
Three cartridges exist; "rom" in your view tells you which one is loaded.
 CHOMPER  - a maze. Eat all 120 pellets (10 each). Four HUNTERS chase you and
            cost a life on contact. The 4 power pellets (50) make hunters FLEE
            for 6 seconds; eating fleeing hunters pays 100, 150, 200, 250 in a
            chain. Clearing the maze pays 500. There is a wrap TUNNEL across
            row 8.
 BRICKFALL- a paddle on the bottom row and one ball. Bricks pay 50/30/20/10 by
            row, top row worth most. The ball leaves your paddle at an angle set
            by WHERE ON THE PADDLE it hit - the ends send it steeply sideways,
            the middle sends it straight up. Let the ball past you and you lose
            a life. Clearing the wall pays 350. Every 8 bricks the ball speeds
            up.
 GALLERY  - a formation of 32 marchers steps down toward you. Shoot them (30/20/
            10/10 by row, top row worth most); the saucer that crosses the top
            pays 100. Their bolts and any marcher reaching row 13 cost a life.
            Three bunkers absorb 3 hits each. Clearing the wave pays 300 and the
            next wave starts lower.
YOU CAN SEE YOUR WHOLE SCREEN: every tile, every sprite, your lives, your points.
Nothing on your own screen is hidden. You can also see the SCOREBOARD - the other
three cabinets' scores, lives and screen numbers - and nothing else about them.
You CANNOT talk to anyone and nobody sees anything you write.
Every 5 seconds you set your STANCE for the next 5 seconds. A deterministic
autopilot runs it 24 times a second: it does the pathfinding, the dodging, the
aiming and the firing. You choose WHAT to go for and HOW MUCH RISK to take.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars, your reasoning",
 "mode":"clear"|"hunt"|"strike"|"safe"|"bank",
   // clear  : take the nearest scoring thing, over and over. The default.
   // hunt   : go for the HIGHEST-VALUE thing reachable (a power pellet, the top
   //          brick row, the top marcher row, the saucer) even if it is far.
   // strike : cash in. In CHOMPER chase fleeing hunters for the chain; in
   //          BRICKFALL aim returns off the paddle ends at the top rows; in
   //          GALLERY push to the flank with the most marchers and fire flat
   //          out.
   // safe   : keep the largest distance from every threat that still scores.
   // bank   : refuse every trade. Never enter a tile a threat can reach before
   //          you leave it. You will score slowly and you will not die.
 "zone":"nw"|"ne"|"sw"|"se"|"centre"|"left"|"right"|"top"|"bottom"|"none",
                            // work in this part of YOUR screen; "none" = anywhere
 "risk":0.0..1.0,           // 0 = never let a threat within 4 tiles,
                            // 1 = ignore threats entirely
 "lead_ticks":0..48,        // how long the autopilot commits to a chosen route
                            // before re-deciding (24 ticks = 1 second)
 "fire":"auto"|"hold"|"never",   // GALLERY only; ignored by the other roms
 "say":"<=48 chars"}        // spectators only; no cabinet ever sees it
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(paintbot's `operatorBlock`, kept), a blank line, then the seat's board-view JSON (§Server). The
prompt text is never echoed into the replay — only `policyKind`, the label and the resulting stance.

### Champion #1 — `atari-57-highroller` (owner daveey), `PLAYER_PROMPT`

```
Points compound and lives do not. One life is worth exactly 100 points, and a
cleared screen is worth 300-500 plus everything on it - so the run that clears
screens beats the run that survives. Push, but never push into a coin flip.
Rules, in order.
1. Read "threats" first. If ANY threat's eta_ticks is under 20, mode "safe",
   risk 0.15, lead_ticks 8, zone "none". Survive the next second and re-decide.
   Nothing on the board is worth a life at 20 ticks.
2. Otherwise, if a power pellet is listed in "targets" and its dist_ticks is
   under 60, mode "hunt", zone = the zone that power pellet is in, risk 0.55,
   lead_ticks 16. In CHOMPER the power pellet is not 50 points, it is 750: the
   pellet plus a full 100/150/200/250 chain.
3. Immediately after eating one - "power_ticks_left" above 60 - mode "strike",
   risk 0.85, lead_ticks 10, zone "none". The chain is the single largest number
   on this cabinet. Take it.
4. In BRICKFALL, if "bricks_left_by_row" still shows the top row, mode "hunt"
   with zone "top": the 50s are five times the 10s and they open the tunnel that
   clears the wall for you.
5. In GALLERY, fire "auto" always, mode "hunt", zone = the flank with the most
   live marchers; switch to zone "top" whenever the saucer is listed.
6. Otherwise mode "clear", risk 0.5, lead_ticks 14, zone "none".
7. On your LAST life, halve every risk you would otherwise set and never set it
   above 0.35. A frozen counter scores nothing for the remaining minute.
Never set risk above 0.9. Never set lead_ticks above 24 - a long commitment in a
game where the threats move is how you die.
```

### Champion #2 — `atari-57-onecredit` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Three lives is three lives. The board is decided in the last thirty seconds, and
the cog that is still alive at 1:30 with two lives can spend them all in one
glorious minute. Survive first, cash late.
Read "clock.left_s" and "scoreboard" every turn before anything else.
1. While left_s is above 45: mode "bank" whenever any threat's eta_ticks is under
   45, otherwise mode "clear". risk = 0.25, lead_ticks 12, zone "none". You are
   farming, not gambling. Do not chase a power pellet across the maze in this
   window and do not chase the saucer.
2. While left_s is between 45 and 20: mode "clear", risk 0.5, zone = whichever
   zone "targets" says holds the most points. Start spending.
3. While left_s is under 20: mode "strike", risk 1.0, lead_ticks 6, fire "auto",
   zone "none". Lives are worth 1.0 each and you are about to lose them for free
   anyway. Empty the credit.
4. Override, any time: if you are more than 6.0 score BEHIND the leader in
   "scoreboard" and left_s is under 60, jump straight to rule 3's settings. A
   safe second place scores the same as a reckless second place.
5. Override, any time: if you are the LEADER and left_s is under 30, mode "safe",
   risk 0.1. Do not hand back a won board for 200 points.
6. In BRICKFALL never set risk below 0.3 - the paddle cannot die by moving, only
   by being late, and a timid paddle is a late paddle.
Never set lead_ticks above 20. Never set mode "hunt" while on your last life.
```

### The autopilot (deterministic, one function, shared by every policy and every ROM)

`src/lane/control.nim`, `laneCommand(sim, s) -> uint8`, evaluated once per tick per lane in lane index
order. Both LLM stances and scripted-baseline stances are compiled by this same code, so the two
policy kinds are strictly comparable and a baseline is legal by construction. It sits **outside** the
determinism boundary (ctf's rule: recorded bytes, not re-run logic) and may use floats.

With `S` = this lane's active stance:

1. **Threat field.** A breadth-first walk over the lane's walkable tiles, **bounded at 300 nodes**,
   from every hostile sprite, producing `threatEta[tile]` = the fewest ticks in which some hostile can
   occupy that tile. In `railBottom` ROMs the "walk" degenerates to a per-column arrival time
   (a hostile bolt's column and ETA; the ball's predicted paddle-row crossing column and ETA), which
   is the same array with `GridH = 1`.
2. **Target set.** Every scoring thing currently on the screen, each with `(value, distTicks, zone)`:
   pellets and power pellets (`chomper`), brick tiles by row (`brickfall`, valued at the row's points
   and reached by *aiming the ball*, i.e. by the paddle offset that sends the ball at that column),
   live marchers and the saucer (`gallery`). **This is exactly the array the observation publishes as
   `targets`** — the escrow 0.1.3 lesson: precompute the choice set in the observation with the same
   predicate the executor applies.
3. **Weights from the stance.**
   `clear` → `w = value / max(1, distTicks)`; `hunt` → `w = value^1.5 / max(1, distTicks)`;
   `strike` → `w` as `hunt` but fleeing chasers (`chomper`), the top two brick rows (`brickfall`) and
   the densest flank (`gallery`) get ×3; `safe` → `w = value / max(1, distTicks)` × the target's own
   `min(1, threatEta/48)`; `bank` → the same as `safe`, and any target whose route enters a tile with
   `threatEta < 24` is **removed** from the set. Targets outside `S.zone` (when `zone != "none"`) are
   multiplied by **0.35**.
4. **Danger gate.** A candidate move is rejected outright if it enters a tile whose
   `threatEta < (1 - S.risk) · 96 + 4` ticks. If every move is rejected, the least-dangerous one is
   taken (there is always a move; `dir = 0` is always a candidate).
5. **Route.** The best-weighted surviving target's first step, via the same bounded BFS. In
   `railBottom` ROMs the "route" is the sign of the difference between the paddle centre and the
   desired column, and the desired column is: the ball's predicted crossing column offset by the fan
   index that aims at the best target (`brickfall`), or the best target's column (`gallery`).
6. **Commit window.** The chosen route is held for `min(S.lead_ticks, 48)` ticks unless the danger
   gate rejects it earlier, in which case it is re-planned immediately.
7. **`act`.** `fire` when the ROM has `fireEnabled` and `S.fire == "auto"` (fire whenever a bolt slot
   and the reload allow) or `S.fire == "hold"` (fire only when the paddle centre is within 0.5 tiles of
   the lowest live marcher in its column); never when `S.fire == "never"`. `brake` when the ROM has
   `brakeEnabled`, `mode ∈ {safe, bank}` and the nearest threat's ETA is in `[8, 24]` — the "let it
   commit first" move. Otherwise 0.
8. **Lane `Over`, or any phase other than `Playing`** → `cmd = 0`.

The autopilot contains **no memory across ticks** beyond its own commit window, no knowledge of any
other lane, and no access to anything the seat's own observation does not carry —
`tests/test_isolation.nim` asserts the signature cannot see more.

### Scripted baselines

Both emit the *same* stance object on the same 120-tick cadence, so their output is legal by
construction and directly comparable to an LLM's, and both are pure functions of the observation a
seat would receive.

- **`arcader`** — the certification player, the per-turn fallback, and the default for a seat that
  registers with neither env var. **Algorithm, evaluated once per turn for lane `s`:**
  1. If the lane is `Over` → `{mode: "safe", zone: "none", risk: 0.0, lead_ticks: 12, fire: "never"}`.
  2. Else if `powerTicksLeft > 48` (only possible in `chomper`) →
     `{mode: "strike", zone: "none", risk: 0.85, lead_ticks: 10, fire: "auto"}`.
  3. Else if the nearest threat's `eta_ticks ≤ panicTicks` (default **28**) →
     `{mode: "safe", zone: "none", risk: 0.15, lead_ticks: 8, fire: "auto"}`.
  4. Else if a power pellet exists and its `dist_ticks ≤ 72` →
     `{mode: "hunt", zone: <that pellet's zone>, risk: riskMilli/1000, lead_ticks: 16,
     fire: "auto"}`.
  5. Else → `{mode: "clear", zone: <the zone with the most target value>, risk: riskMilli/1000,
     lead_ticks: 14, fire: "auto"}`.
  6. Override in every branch: if `lives == 1`, `risk := risk · 0.5` and `mode "hunt"` becomes
     `"clear"`.
  `say` is one of five fixed strings chosen by which branch fired. Four `arcader`s produce a real
  arcade run — screens cleared, chains cashed, at least one death on most seeds — which is the
  behaviour the cabinet is about and the anti-regression pin of the whole difficulty tuning
  (§Tests 5).
- **`hoover`** — the second filler, deliberately different in shape and weaker: it never dodges.
  `{mode: "clear", zone: "none", risk: 1.0, lead_ticks: 24, fire: "auto"}` every turn, unless the lane
  is `Over`. It banks points fast and dies fast, which gives the ladder a spread and gives a champion
  a visibly different neighbour on the momentum graph.

Three tunables — `panicTicks` (28), `riskMilli` (500) and `leadTicks` (14) — are a `BaselineParams`
object, not literals, exactly as `src/ctf/baselines.nim` does it (its `DefaultBaselineParams` comment
at lines 30-51 is the template): `tools/tune_baselines.nim` sweeps them over a bounded grid,
`tools/ci/baseline_tuning.json` records the sweep's pick, and `tests/test_tuning.nim` asserts the
shipped defaults still equal it. **The ROM constants in §The three ROMs are not swept and are not
tunable by the harness** — if the baselines cannot clear a screen, the sweep moves these three
numbers, not the game.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf/paintball arena rules go** (teams as sides of a fight, guns, flags, fog cones,
respawn, grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the
hill, the paint grid, the map pool and the map editor all leave the repo):

| ctf path | atari-57 |
|---|---|
| `src/ctf/sim.nim` (4102 lines: gameplay core, combat, vision, items) | `src/lane/sim.nim` — the four-lane container, the tick loop of §Resolution order, and `stepLane`. |
| `src/ctf/arena.nim`, `paint.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `tools/map_render.nim`, `docs/MAPKIT.md`, `docs/pool-review.html`, `scripts/` | `src/lane/grid.nim` — the 17 × 17 tile lattice, tile enums, the tunnel wrap, box-vs-tile and box-vs-box swept contact tests, and the quad-split board mapping. **Deleted, not ported**; there is no map generator, no `mapSpec`, no procedural terrain in this coworld. |
| — (new) | `src/lane/maps.nim` — the three committed 17-string map literals and their sha256 pins. |
| — (new) | `src/lane/rom.nim` — the three ROM presets, the tile-effect tables, the point tables and the strict `defaults → preset → explicit` application order. |
| — (new) | `src/lane/sprites.nim` — the three shared behaviours (`Chaser`, `Ballistic`, `Marcher`) and the committed `BallFan` table. |
| `src/ctf/global.nim` (8070 lines) fog of war, vision cones, first-person raycast, killfeed art, item sprites | `src/lane/global.nim` — top-down sprite composition: four CRT quadrants with scanlines and bloom, tinted lane frames, tiles, avatars, sprites, bolts, the points readout baked into each quadrant. Perfect information within a lane (§Server). `boardRenderScaleFor`, `MaxSupersampledMapPixels`, `predictedViewerRenderBytes`, `WasmViewerBudgetBytes` and `shoutBubbleZoomFor` are **kept verbatim**. |
| `src/ctf/directives.nim` (`Intent`, `CogOrder`, `SquadDirective`) | `src/lane/stances.nim` — the `LaneStance` object, the closed `Mode`/`Zone`/`Fire` enums, the tolerant parser and the repair table of §Server. Same file shape, same rune discipline (`truncateRunes`, `sanitizeSay`, the no-leading-brace rule for `say`). |
| `src/ctf/control.nim` (nav grid, flow fields, aim) | `src/lane/control.nim` — `laneCommand` of §Decisions. ~260 lines instead of 536; one bounded BFS, no flow field, no cached fields. |
| `src/ctf/baselines.nim` (`holdline`, `sprayer`) | `src/lane/baselines.nim` — `arcader`, `hoover`, and `BaselineParams`. |
| — (new) | `src/lane/observation.nim` — the per-seat board-view JSON of §Server, including the cross-lane **scoreboard** (the only place any cross-lane read happens, and it happens outside the sim). |
| `players/baseline/` (the CTF bot) | deleted; the only player binary is `src/atari57_player.nim`. |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/paintball/`, `docs/plans/*` | rewritten for the cabinet; ctf's plans/designs deleted. |
| `arena/`, `caos/`, `caos-tools/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/render_map_pool.nim`, `tools/build_pool_review.py`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf`/`paintball` → `lane`/`atari57` rename sweep only, `CTF_WIRE` →
`LANE_WIRE`; a CI grep asserts no `ctf_`/`CTF_`/`paintball` identifier survives outside comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/lane/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `writeInputMaskChange` (used **as-is**: our action byte is a value, and `writeInputMaskChange` already writes change-only), `checkReplayHash`. Three named edits below. |
| `src/ctf/replay_runtime.nim` → `src/lane/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports and the `cmd >= 15 → 0` repair, which is shared code with the server. |
| `src/ctf/server.nim` → `src/lane/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the held-registration table, the frame limiter, the replay-switch path, the `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. **The `Ping → Pong` branch in `websocketHandler` (`src/ctf/server.nim:896`) is kept exactly, and no `kind != TextMessage` guard is added** — dropping either is a certification failure that has now happened twice (lux-ai 0.1.0, snake-royale 0.1.0). Five further named edits below. |
| `src/ctf/llm.nim` → `src/lane/llm.nim` | the credential ladder, the single-haiku model list, the `throttled` fast-fail, `curly.makeRequests` batching, `extractJsonObject`, rune truncation. Rename only. |
| `src/ctf/decide.nim` → `src/lane/decide.nim` | the turn loop, `SeatPolicy`, the two-deadline retry, the inter-batch floor, the budget guard, `repairMissingOrders` (retargeted: a missing field keeps last turn's value, else `arcader`'s), the `records` queue. It is already a loop over `sim.seatCount()` seats that batches them, so retargeting to 4 seats and skipping `Over` lanes is a predicate. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/sim_config.nim` | `GameConfig` lifecycle and `config.update`; the lane's fields replace the arena's, with `rom.nim` applying the preset between defaults and explicit keys. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; lane result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim` | HUD label composition. |
| `src/ctf/broadcast.nim` | `stepEvents` / `BroadcastTracker` / `buildStateJson` — the state-delta → broadcast-event derivation, retargeted to the lane's event kinds and state keys (§Viewer). Its **four-team** paths (it already serves ctf's `4ffa`) are what make the scorebug work unchanged. |
| `replay-viewer/config.nims`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/chrome_common.js` | **byte-for-byte**, zero edits (§Viewer). |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome, with a game block appended (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/wasm_replay_smoke.cjs`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix`, `flake.lock`, `config.json` | build, bundle, tuning and forensics wiring. `tools/build_replay_viewer.sh` already carries the ecos `mkdir -p` fix at line 22 and keeps it; only `image_tag` and the `docker cp` source path `/workspace/atari57/replay-viewer/dist/.` change. |
| `data/font.ttf`, `data/FONT_LICENSE.txt`, `data/arena_floor.png`, `data/darkbg.png`, `data/ascii.png`, `data/atlas/*`, `data/heart_red.png`, `heart_blue.png`, `heart_green.png`, `heart_yellow.png`, `client/art/walls/*`, `client/art/lockerroom/bg.jpg` | real art, kept — the four `heart_<colour>.png` become the lives pips, which is exactly what they already are, and `data/ascii.png` is the points font baked into each quadrant. Everything CTF-specific (`soldier_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, `crew.png`, `rig_real/`) is deleted. |

**The six named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   the cabinet calls `control.laneCommand(sim, s)` for all four lanes and passes the action-byte array
   into `sim.step`. **Player sockets contribute no input**: any input mask arriving on a player socket
   is discarded.
2. **Replay input write.** `writeInputFrameMasks` (the press/release wrapper at
   `src/ctf/server.nim:1088`) is **deleted** — its `repeatedPressedMask` logic (line 1098) is button
   semantics and would corrupt a value byte. The cabinet calls
   `replayWriter.writeInputMaskChange(tickTime(tick), seat, cmd)` directly (the codec's own
   change-only guard does the rest), and `decodeInputMask` (lines 1707, 1991) is replaced by
   `decodeAction(cmd: uint8): tuple[dir, act: int32]` with the `cmd >= 15 → 0` repair.
3. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop runs
   `decide.turn(sim, engine, …)`, which enforces the inter-batch floor, issues the one parallel batch
   over the seats whose lanes are alive, applies the deadlines, installs the stances and writes the
   `stance`/`fallback` records — all inside a monotonic `turnBudgetMs` bound.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration writes a
   **`stopped` replay record** and then forces `phase = GameOver`, `reason = deadline`,
   `endRule = wall_clock`. The record is load-bearing: the *same* proc applies it on record and on
   playback, because a wall-clock fact cannot be re-derived from sim state and recording the hash of a
   state the playback cannot reproduce mismatches every deadline replay (particle-worlds 13c66d7,
   2026-08-26). §Tests 10 asserts record→re-derive for **every** end reason, not just `complete`.
5. **Shutdown grace.** `/healthz` and `/global` keep answering for a bounded ~20 s after the artifacts
   are written, then the process exits (lantern 0.1.3: the episode runner pings `/global` with a 2 s
   deadline *after* the player pods start, and a short episode can already be gone).
6. **Register loudness.** A seat that reaches the first turn with no `register` record makes the server
   log `SEAT <n> NEVER REGISTERED — playing arcader` at error level and sets `results.policyKinds[n]`
   to `scripted`, so a silently-lost register packet is visible in the hosted log and in the results
   rather than being mistaken for an LLM that chose badly (grf-football round 2, 2026-08-27).

**The three named edits to `replays.nim`:**

1. **`serializeReplaySim`/`deserializeReplaySim` cover the new sim fields** — for every lane:
   `lanePhase`, `phaseTimer`, `lives`, `points`, `screen`, `overTick`, `lastScoreTick`, `recordFlag`,
   the avatar's `pos`/`facing`/`pendingDir`/`pendingAge`/`reload`, the full tile bitmap (pellet bits,
   brick bits, bunker HP), every sprite's `kind`/`state`/`pos`/`vel`/`timer`, `powerTicksLeft`,
   `chain`, `bestChain`, `speedPermille`, `marchTicks`, `deaths`, `screensCleared`, `shotsFired`,
   `scoreMicro`, `rngDraws` and the lane's RNG state; plus `phase`, `targetTick`. Keyframes are how
   the viewer seeks. The static geometry, the ROM preset and the maps are **excluded** from keyframes
   (they are already in the config JSON — ctf's own rule for static bakes).
2. **`CtfReplayMagic "COWLDCTF"` → `Atari57ReplayMagic "COWLDA57"`**, `GameName* = "atari-57"`,
   `GameVersion* = "1"`, with ctf's prepend-only changelog-comment discipline
   (`GV1 (lane rules): four isolated lanes, one action byte, three roms`) and
   `tools/ci/check_gameversion.sh` kept as is.
3. **A `stopped` record kind** (edit 4 above), applied by one shared proc on both record and playback.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`; `tools/wasm_replay_smoke.cjs`). So:

- Every stored sim field is explicitly `int32` (positions, velocities, counters), `int64` (the score
  accumulators), `uint8`/`int8` (directions, tile coordinates, action bytes) or `bool`/`enum`. **No
  bare `int` in a hashed field.**
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with an
  explicit truncating `div` (Nim's `div` truncates toward zero, so every scaling is symmetric under
  negation).
- **No floating point anywhere under `src/lane/{sim,grid,rom,maps,sprites,sim_types,sim_config,
  sim_state}.nim`.** No `sin`, `cos`, `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`.
  Grep-enforced in CI. Floats stay legal in `control.nim`, `global.nim`, `observation.nim`,
  `stances.nim`'s numeric parsing and the pixie bakes, because neither the autopilot (recorded, not
  re-run) nor rendering enters `gameHash` — exactly ctf's split.
- **No square root and no trigonometry anywhere in the sim**: every collidable is a tile or an
  axis-aligned box, and the only oblique motion is `brickfall`'s ball, whose directions come from the
  committed `BallFan` table.
- Randomness: one seeded stream **per lane**, all four initialised identically from `config.seed`,
  every draw through `drawInt` on `next()`'s `uint64` domain, `rngDraws` hashed per lane.

### How the replay achieves server ↔ viewer determinism

The mechanism is ctf's, unchanged:

1. The server writes a `COWLDA57` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `rom`, every geometry and ROM constant, the three map literals'
   sha256, the resolved preset, `parScore`, the roster with real names), then the record stream —
   joins, leaves, **per-tick action-byte change records**, chat records (`register`, `stance`,
   `fallback`, `budget_guard`, `stopped`, `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/atari57_replay.nim` — which imports the
   **same** `src/lane/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + `nimby 2.2.4`
   container in `Dockerfile.replay-viewer`.
3. In the browser, `atari57_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `atari57_frame` re-steps the sim from the **recorded action bytes** and compares `sim.gameHash()`
   against the recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the
   tick it happens, surfaced as `mismatchTick` in the chrome (`#mmwarn`) and, in CI, as a hard failure.
   This is precisely the idea's "replay verified by re-running the action log deterministically",
   already built into the starter.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle and
   runs `tools/ci/viewer_smoke.mjs` against the replay `docker-smoke` produced (§Tests), which fails if
   the viewer errors, never draws, freezes, or reports a mismatch tick.

Perf target: 2880 ticks × 4 lanes of physics + 11 520 autopilot evaluations in under 5 s on a CI
runner; `tests/test_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

`src/lane/server.nim` is ctf's `server.nim` with the six edits above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`) — **both `/client/` routes serve real
pages, registered before any catch-all asset route, and neither opens the player socket** (lantern
0.1.1: the certifier probes them before starting player pods). The player websocket **closes on a
token that does not match the seat** (the certifier probes with a bad token — flatland 0.1.1) and
**answers `Ping` with `Pong`** (lux-ai / snake-royale). Same `COGAME_*` runtime contract
(`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`,
`COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`, `COGAME_HOST`/`COGAME_PORT`), same
403 on a bad slot/token, same done-before-artifact-writes ordering, same entrypoint shape
(`src/atari57.nim`, where seed randomisation happens **before** `config.update` so every seed-derived
draw follows the final seed, and where `rom.applyPreset` runs inside `config.update` between defaults
and explicit keys).

### The player container

`src/atari57_player.nim` (built to `/bin/atari-57-player`) is `src/paintball_player.nim` with the
baseline names changed. It reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED`,
`PLAYER_POLICY_LABEL`, dials with the starter's bounded retry (240 × 500 ms), and sends **one Sprite
v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"arcader"|"hoover"|null,"policy":"<free label>"}
```

It re-sends the registration on the starter's `RegistrationResends`/`ResendEveryFrames` schedule
(`src/paintball_player.nim:28-29`; the server's held-registration table, `src/ctf/server.nim:1730`, is
kept — a seat's first registration can arrive before its player index exists, and dropping it was a
real paintball scar). It then sends the Sprite v1 Ready packet (`0x85`) after each received frame and
otherwise only receives. **The receive loop is wrapped in `try/except CatchableError` and exits 0 on a
dead socket** — whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues, so
the game's `quit(0)` can outrun the flushed `done` frame (raid 0.1.3 → 0.1.4). A seat that never
registers, or registers with neither field, is `scripted: "arcader"` **and is logged loudly**
(server edit 6).

Player container resources in the manifest: `requests {cpu: 100m, memory: 64Mi}`, `limits {cpu: "1"}`
— the bundled-player `limits.cpu` minimum is `"1"` and anything lower is a 400 at upload (pistonball
0.1.1, 2026-08-26).

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates`. **A seat's frame carries ITS OWN LANE ONLY** — its full
17 × 17 screen, every tile, every sprite, its avatar, its lives and its points — plus the four-entry
scoreboard strip. The other three quadrants are **not** in a player frame at all (they are in the
spectator/global frame). Fog of war, vision cones and the first-person raycast are **deleted**, not
disabled: within your own lane nothing is hidden, because it is a CRT you are sitting at. Board labels
carry only the colour aliases; `showPlayerLabels` is forced false on the player stream.

### The per-seat view given to the LLM

Numbers are tile coordinates (`col, row ∈ 0..16`, origin top-left of **your own lane**), rounded to 2
decimals where sub-tile. This object is the tail of the LLM user message; the scripted baselines are
pure functions of the identical object. `src/lane/observation.nim` composes it.

```json
{"turn": 11, "of": 24,
 "clock": {"tick": 1320, "of": 2880, "left_s": 65.0},
 "rom": "chomper",
 "you": {"alias": "GREEN", "lives": 2, "points": 1780, "score": 19.800,
         "screen": 1, "state": "running",
         "avatar": {"col": 8, "row": 12, "x": 8.50, "y": 12.00, "facing": "right",
                    "speed_tiles_s": 3.00},
         "power_ticks_left": 0, "chain": 0, "best_chain": 3,
         "record": false, "par": 2600},
 "screen_map": ["#################",
                "#o.............o#",
                "#.##.###.###.##.#",
                "#.##.###.###.##.#",
                "#....,,,........#",
                "#.##.###.###.##.#",
                "#.##.###.###.##.#",
                "#.##.###.###.##.#",
                " ....,,,,,,,.... ",
                "#.##.###.###.##.#",
                "#.##.###.###.##.#",
                "#.##.###.###.##.#",
                "#.,,,,,@,,,,,,..#",
                "#.##.###.###.##.#",
                "#.##.###.###.##.#",
                "#o.............o#",
                "#################"],
 "legend": {"#": "wall", ".": "pellet", ",": "eaten floor", "o": "power pellet",
            "@": "you", "H": "hunter chasing", "h": "hunter fleeing",
            "r": "hunter returning", "=": "brick", "B": "ball", "_": "paddle",
            "A": "marcher", "S": "saucer", "X": "bunker", "^": "your bolt",
            "v": "enemy bolt", " ": "tunnel mouth"},
 "threats": [{"id": "H0", "kind": "hunter", "state": "chasing", "col": 8, "row": 8,
              "eta_ticks": 34, "dist_tiles": 4.00},
             {"id": "H1", "kind": "hunter", "state": "chasing", "col": 3, "row": 12,
              "eta_ticks": 48, "dist_tiles": 5.00}],
 "targets": [{"kind": "power", "col": 1, "row": 15, "value": 50, "dist_ticks": 62,
              "zone": "sw", "safe": true},
             {"kind": "pellet_cluster", "col": 13, "row": 12, "value": 90,
              "dist_ticks": 44, "zone": "se", "safe": true},
             {"kind": "pellet_cluster", "col": 3, "row": 4, "value": 70,
              "dist_ticks": 96, "zone": "nw", "safe": false}],
 "zones": {"nw": {"value": 310, "min_threat_eta": 60},
           "ne": {"value": 280, "min_threat_eta": 52},
           "sw": {"value": 240, "min_threat_eta": 34},
           "se": {"value": 300, "min_threat_eta": 88},
           "centre": {"value": 120, "min_threat_eta": 34}},
 "scoreboard": [{"alias": "RED", "score": 22.400, "lives": 2, "screen": 1},
                {"alias": "BLUE", "score": 12.100, "lives": 0, "screen": 1},
                {"alias": "GREEN", "score": 19.800, "lives": 2, "screen": 1},
                {"alias": "YELLOW", "score": 27.650, "lives": 3, "screen": 2}],
 "rules": {"lives_per_lane": 3, "grid": [17, 17], "par_score": 2600,
           "points": {"pellet": 10, "power": 50, "chain": [100, 150, 200, 250],
                      "screen_clear": 500},
           "score": "points / 100 + lives left; nothing is ever subtracted",
           "note": "your lane is sealed: nothing you do can affect any other lane, and nothing they do can affect yours"},
 "your_last_stance": {"mode": "clear", "zone": "se", "risk": 0.5,
                      "lead_ticks": 14, "fire": "auto"}}
```

`screen_map` is always exactly 17 strings of 17 characters. `threats` lists every hostile sprite in
the lane (at most 4 hunters, or 1 ball, or up to 3 hostile bolts + the lowest marcher per column),
sorted by `eta_ticks` ascending. `targets` is capped at **12 entries**, sorted by
`value / dist_ticks` descending, and is computed by **the same routine the autopilot uses**, so a
policy is never guessing at a quantity the engine already knows (escrow 0.1.3). `zones` partitions the
lane into five fixed regions: `nw` = cols 0–7 rows 0–7, `ne` = cols 9–16 rows 0–7, `sw` = cols 0–7
rows 9–16, `se` = cols 9–16 rows 9–16, `centre` = col 8 or row 8. `left`/`right`/`top`/`bottom` are
the unions a stance may also name.

In `brickfall` and `gallery` the same object is emitted with the ROM's own legend characters, `you`
gains `paddle_col` and (gallery) `bolts_ready`, and `targets` lists brick rows / marcher columns /
the saucer with the paddle column that reaches them.

**Hidden from every seat, with no exception:**

- Which entrant holds any seat, including its own.
- Any other lane's board, tiles, sprites, avatar, targets, threats, stance, `note`, `say`, prompt,
  latency, policy label, `policyKind` or fallback state. The scoreboard's four fields
  (`alias`, `score`, `lives`, `screen`) are the **entire** cross-lane surface.
- `config.seed`, any RNG state, `rngDraws`, and every **future** draw (the next scatter flip, the next
  saucer, the next marcher volley, the next serve angle).
- Real player names anywhere (board labels carry only `RED`/`BLUE`/`GREEN`/`YELLOW`;
  `showPlayerLabels` is forced false on the player stream).
- Any host or wall-clock fact (elapsed wall seconds, turn budgets, whether another seat fell back).
- Future ticks.

Everything **in your own lane** is visible. That is the decision, stated once so there is no
ambiguity: **your screen is public to you, the other screens are not, and the players are never.**
`tests/test_isolation.nim` asserts both halves against the composed LLM user message over randomised
states (§Tests 8).

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "power pellet 62 ticks away in sw and nothing is chasing me there; take it, then cash the chain",
 "mode": "hunt", "zone": "sw", "risk": 0.55, "lead_ticks": 16,
 "fire": "auto", "say": "going for the power"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `mode` | string | closed enum `clear, hunt, strike, safe, bank`; **≤ 8 runes** | unrecognised / missing → last turn's `mode`, else `clear` |
| `zone` | string | closed enum `nw, ne, sw, se, centre, left, right, top, bottom, none`; **≤ 8 runes** | unrecognised / missing → `none` |
| `risk` | number | finite, clamped `[0.0, 1.0]`, quantised to `0..255` | non-finite / missing → last turn's `risk`, else `0.5` |
| `lead_ticks` | integer | finite, clamped `[0, 48]`, rounded | non-finite / missing → `14` |
| `fire` | string | closed enum `auto, hold, never`; **≤ 6 runes**; ignored unless the ROM has `fireEnabled` | unrecognised / missing → `auto` |
| `say` | string | **≤ 48 runes** | truncated to 48 runes, then ctf's printable-ASCII shout sanitiser (which also strips a leading `{`, since the replay chat stream distinguishes control records by it) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**
(`MaxPolicyLabelRunes`), any recorded error text (`fallback.detail`) **≤ 200 runes**
(`MaxFallbackDetailRunes`), and the whole serialized `stance` record **≤ 600 runes**, asserted in
`tests/test_replay.nim`. `register.prompt` is capped at **≤ 4000 runes** at the transport (over-long is
truncated, never rejected) and is **never** written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — in Nim, `runeLen` /
`runeSubStr` (ctf's `directives.nim` rune discipline at lines 61-90, kept verbatim as `stances.nim`).
Slicing a `string` by byte index on any path to the replay is forbidden: a byte-truncated multi-byte
character renders in a browser and then fails a strict UTF-8 parser. §Tests 6 pins it with a 4-byte
emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose (`extractJsonObject`); accept numeric strings; accept integer percentages for `risk`
and divide by 100 when the value exceeds 1; accept `mode`, `zone` and `fire` case-insensitively and
with surrounding whitespace; accept `mode` synonyms `greedy`/`collect`→`clear`, `attack`→`strike`,
`chase`→`hunt`, `defend`/`dodge`→`safe`, `survive`/`turtle`→`bank`; accept `zone` given as
`"north-west"`, `"top left"` or `"upper left"`→`nw` (and the mirrors), `"middle"`→`centre`,
`"anywhere"`/`""`→`none`; accept `fire` given as `"always"`→`auto`, `"off"`→`never`. Only when no
object with at least one usable field can be recovered do the retry and then the fallback fire.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, lane keys) to `COGAME_RESULTS_URI`. It must
equal the manifest's `results_schema` key-for-key — that schema is `additionalProperties: false` and
the certifier rejects any unknown field. Adding or removing a key here means editing
`coworld_manifest_template.json` in the same commit. **24 keys:**

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
 "aliases": ["RED", "BLUE", "GREEN", "YELLOW"],
 "lanes": [0, 1, 2, 3],
 "policyKinds": ["llm", "llm", "scripted", "scripted"],
 "scores": [22.4, 12.1, 44.1, 27.65],
 "win": [false, false, true, false],
 "placements": [3, 4, 1, 2],
 "rom": "chomper",
 "parScore": 2600,
 "points": [2040, 1210, 4210, 2465],
 "livesLeft": [2, 0, 2, 3],
 "deaths": [1, 3, 1, 0],
 "screensCleared": [1, 0, 2, 1],
 "bestChain": [2, 0, 4, 1],
 "shotsFired": [0, 0, 0, 0],
 "records": [false, false, true, false],
 "lastScoreTick": [2874, 1902, 2861, 2879],
 "ticksAlive": [2880, 1902, 2880, 2880],
 "llmTurns": [24, 23, 0, 0],
 "fallbackTurns": [0, 1, 0, 0],
 "finalTick": 2880,
 "reason": "complete",
 "endRule": "full_time",
 "seed": 5140913}
```

`names` are the **real policy names** (spectator side). `aliases` are the in-game names. Every
per-seat array is in **seat order** and has exactly 4 entries. `records[s]` is true iff lane `s`
crossed `parScore`.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDA57`** format: the static wasm viewer parses exactly this
format, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and the whole seek/keyframe machinery. Consequences handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design ("set 0 for a binary replay format").
- The repo keeps **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): given a
  `.replay` path it prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"atari-57/v1","gameVersion":"1","rom":"chomper","seed":…,"parScore":…,"names":[…],
  "aliases":[…],"policyKinds":[…],"tickCount":…,"stances":[…],"fallbacks":N,"stopped":bool,
  "results":{…}}`. It brace-matches the config JSON from the first `{` (the technique ctf's `AGENTS.md`
  documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .rom, .results.reason, .results.endRule, .results.placements' /tmp/ep.json
  jq -r '[.stances[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  jq -r '[.stances[]|select(.source=="llm")|.mode]|unique' /tmp/ep.json
  ```
  Require `protocol == "atari-57/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), `results.points` summing above 0, and the champion seats' stances `source == "llm"`
  with **varying** `mode`/`zone` values — not all fallbacks, and not a constant stance.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDA57`, format version, `gameName` `atari-57`, `gameVersion` `1` |
| config JSON | `seed`, `rom`, the **fully resolved** ROM preset (every key of §The ROM table), `parScore`, the three map literals' sha256 **and** the loaded map's 17 strings verbatim, `num_agents`, `maxTicks`, `minTicks`, `turnTicks`, the whole geometry table (grid, tile size, avatar/sprite speeds, `BallFan`, box sizes, latch ticks, power ticks, march ticks, point tables), the scoring constants, `players[].name` (**real names**), `slots[].alias`, `fastMode` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| inputs | **the action log**: one action byte per seat per tick, written on change only |
| chats | `register` / `stance` / `fallback` / `budget_guard` / `stopped` / `result` records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 2880 hashes (8 B) + ≤ 11 520 input-change records (≈ 4 B) + ≤ 96 stance records (≈ 240 B) + a
≈ 8 KB config ≈ **100 KB** worst case, typically under 65 KB.

### Record and event vocabulary

**A. Replay chat records** (written by the server; re-applied at playback in order):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `lane`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `stance` | `turn`, `seat`, `alias`, `lane`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `mode`, `zone`, `risk`, `lead_ticks`, `fire`, `say` |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stopped` | `tick`, `reason` (`wall_clock`) — the load-bearing wall-clock stop (server edit 4) |
| `result` | the full results document, written once at game over (ctf's `resultRecord`, kept — it is what makes the bytes self-sufficient) |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these from
state deltas during playback, so they cost no replay bytes and are identical live and in replay:
`phase`, `pickup` (`{lane, kind: pellet|power, pts}`), `chip` (`{lane, row, col, pts}` — a brick or a
marcher destroyed), `bunker` (`{lane, col, hp}`), `chain` (`{lane, n, pts}`), `saucer`
(`{lane, pts}`), `near_miss` (`{lane, id}` — a hostile passed within 0.6 tiles of the avatar without
contact: the drama the game is made of), `life_lost` (`{lane, livesLeft, by}`), `screen_clear`
(`{lane, screen, bonus}`), `record` (`{lane, points, par}`), `lane_over` (`{lane, points, tick}`),
`turn_end`, `gameover`, `say` (a `stance` record's non-empty `say`).
**Beats** (scrubber markers): `life_lost`, `screen_clear`, `record`, `lane_over`, `over`. `pickup`,
`chip`, `bunker`, `chain`, `saucer`, `near_miss` and `say` are **not** beats — they fire hundreds of
times and would bury the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Pickup, Chip, Bunker, Chain, Saucer, NearMiss, LifeLost, ScreenClear,
Record, LaneOver, Stance, PhaseChange`, and the mandatory trailing summary row (`type`, `ticks`,
`events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's
script, kept (with `image_tag` and the `docker cp` source path
`/workspace/atari57/replay-viewer/dist/.` changed, and the ecos `mkdir -p` already present at line 22).
`coworld build` invokes it with the absolute bundle directory; the script already refuses any output
path that is not a `static-replay-viewer` directory inside the repo, and it must stay committed
**executable** (`coworld build` hard-requires `os.X_OK`).

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter.** Splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently with every file present and 200
(cogame-lantern, 2026-08-23), so there is no mixture anywhere in this table:

| File | Source |
|---|---|
| `replay-viewer/config.nims` | **`coworld-ctf`**'s `replay-viewer/config.nims`, verbatim except `ctf_replay.js` → `atari57_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_atari57_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the flags stay exactly as ctf links them, including `-s ENVIRONMENT=web,worker,node`, `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file data@data`, `--define:useMalloc`, `--mm:arc`, `--exceptions:goto`. |
| the wasm entry `.nim` | **`coworld-ctf`**'s `replay-viewer/ctf_replay.nim`, forked to `replay-viewer/atari57_replay.nim` (stage-note buffer, `ABORTING_MALLOC` diagnostics, the `predictedViewerRenderBytes`/`WasmViewerBudgetBytes` capacity preflight at lines 71-76, `emscripten_exit_with_live_runtime` lifetime — all kept), exporting `atari57_load_replay`, `atari57_frame`, `atari57_input`, `atari57_packet_ptr/len`, `atari57_mismatch_tick`, `atari57_error_ptr/len`, `atari57_stage_ptr/len`. |
| `static_replay*.js` | **`coworld-ctf`**'s `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts('./wire_constants.js', './broadcast_core.js', './atari57_replay.js')` form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Only two names change: the Worker name `ctf-static-replay` → `atari57-static-replay`, and `window.CtfStaticReplay` → `window.Atari57StaticReplay`. |
| `index.html` | built from **`coworld-ctf`**'s `client/replay_broadcast.html` (see below). |

`static_replay.js` **already sets both machine-readable markers and they are kept unchanged**: it sets
`document.documentElement.setAttribute('data-replay-loaded', 'true')` **on its first drawn frame** (the
Worker's `loaded` message, `replay-viewer/static_replay.js:161`), and `showFailure()` sets
`document.documentElement.setAttribute('data-replay-error', <message>)` **on failure** (line 20), plus
`data-replay-mismatch-tick` on a hash mismatch (line 32). Those attributes are what
`tools/ci/viewer_smoke.mjs` waits on. The `coworld-replay` bridge `ready` post is fired **from a
callback that runs after `data-replay-loaded="true"` has been set**, never on rAF timing at the call
site (chorus, 2026-08-24: the softmax.com embed otherwise samples an unpainted shell).

### Chrome provenance: what is copied, what is appended, what is removed

- **`client/chrome_common.js` is copied byte-for-byte from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, flag story) stay in the file and are inert because the
  corresponding state fields are simply absent from this stream. Every atari-57-specific readout lives
  in the appended game block, and the state JSON **keeps ctf's key names**
  (`t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events, lead, beats,
  lulls, over, hold` — `src/ctf/broadcast.nim:861-1017`) so chrome_common's plate rendering, feed rows,
  beat markers, momentum curve, spoilers switch and endcard run unmodified against lane values.
  **The `teams` keys are exactly `red`, `blue`, `green`, `yellow`**, because `chrome_common.js:55` pins
  `TEAM_ORDER = ['red','blue','green','yellow']` and orders index 0/2 to the left of the clock and 1/3
  to the right — so the four plates come out RED + GREEN | clock | BLUE + YELLOW with no edit at all,
  and the momentum graph takes its four-team branch. A from-scratch page that reuses the starter's ids
  is explicitly **not** what happens here (cogame-gridlock, 2026-08-23). A test pins the file's sha256
  against the starter's copy.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one `<style>`
  and one `<script>` block at the end of the file, injecting the lane readouts into the existing
  containers. Nothing above them is rewritten; the CSS variables, `relayout()`, the transport, the
  endcard, the locker-room loader and the `?embed=1` mode are the starter's. The game block's own
  function names are prefixed `a57` (`a57MarkBeat`, `a57PushFeed`, …) so nothing shadows
  chrome_common's hoisted alias block (`var markBeat = C.markBeat` — the tandem 2026-08-23 scar), and a
  test asserts no game-block top-level name collides with the alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and its
  children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; and `#povBadge`.
  **Zoom decision: the arena is fixed and the board (1400 × 1400 px, 1:1) always fits the frame, so
  `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the rule that it exists only for
  boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap code stays in the file,
  verbatim, simply never driven.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned
  "Same cartridge. Same seed. Four screens. One high score.", art from
  `client/art/lockerroom/bg.jpg`), `#lk-art`, `#lk-bg`, `#lk-cap`, `#lk-sprites`, `#chrome`,
  `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#mmwarn`,
  `#bannerlane` (this is where the **NEW RECORD** banner lands), `#killfeed`, `#transport` with every
  button (`#btn-play`, `#btn-back`, `#btn-fwd`, `#btn-end`, `#btn-restart`, `#btn-loop`, `#btn-skip`,
  `#btn-spoilers`), `#speedchips`, `#scrub`, `#scrub-fill`, `#scrub-head`, `#scrub-win`, `#momentum`,
  `#lulls`, `#tick-clock`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`, `#endcard` with `#ec-headline`,
  `#ec-how`, `#ec-wincond`, `#ec-teams`, `#ec-replay`, and `#status`.

### The exact state JSON the viewer reads

`buildStateJson` (ctf's, retargeted) emits this object once per frame. Keys above the fold are ctf's
and are consumed by the byte-identical `chrome_common.js`; everything atari-57-specific is under `a57`
and `stances`, consumed only by the appended game block.

```json
{"t": 1320, "mt": 2880, "ph": "playing", "lob": 0, "pl": true, "sp": 1, "mx": 2880,
 "st": 0, "lp": false, "sk": false, "ff": false, "en": true, "mm": -1, "bs": 2, "pov": -1,
 "teams": {"red":    {"score": 22.400, "points": 2040, "lives": 2, "livesPerLane": 3,
                      "screen": 1, "record": false, "over": false, "policies": 1},
           "blue":   {"score": 12.100, "points": 1210, "lives": 0, "livesPerLane": 3,
                      "screen": 1, "record": false, "over": true,  "policies": 1},
           "green":  {"score": 44.100, "points": 4210, "lives": 2, "livesPerLane": 3,
                      "screen": 2, "record": true,  "over": false, "policies": 1},
           "yellow": {"score": 27.650, "points": 2465, "lives": 3, "livesPerLane": 3,
                      "screen": 1, "record": false, "over": false, "policies": 1}},
 "roster": [{"s": 0, "name": "daveey", "team": "red", "alias": "RED", "lane": 0,
             "kind": "llm", "points": 2040, "lives": 2, "screen": 1, "deaths": 1},
            "… 4 rows, seat order …"],
 "events": [{"k": "record", "t": 1284, "lane": 2, "points": 2610, "par": 2600}, "…"],
 "turn": 11, "turns": 24, "turnTicks": 120,
 "a57": {"rom": "chomper", "par": 2600, "grid": [17, 17], "livesPerLane": 3,
         "lanes": [{"s": 0, "team": "red", "alias": "RED", "state": "running",
                    "avatar": {"x": 8.50, "y": 12.00, "facing": "right"},
                    "tiles": "…289-char run-length string, legend as in §Server…",
                    "sprites": [{"id": "H0", "kind": "hunter", "state": "chasing",
                                 "x": 8.00, "y": 8.00},
                                "…"],
                    "power": 0, "chain": 0, "points": 2040, "lives": 2,
                    "mode": "clear", "zone": "se"},
                   "… 4, lane order …"],
         "bubbles": [{"lane": 2, "say": "going for the power", "until": 1380}]},
 "stances": [{"turn": 11, "seat": 2, "alias": "GREEN", "lane": 2, "source": "llm",
              "mode": "hunt", "zone": "sw", "risk": 0.55, "leadTicks": 16,
              "fire": "auto", "note": "…", "say": "going for the power"}, "… 4 …"],
 "lead": {"teams": ["red", "blue", "green", "yellow"],
          "pts": [[0, 3, 3, 3, 3], [120, 5.1, 4.8, 6.2, 4.4], "… change-points of score …"]},
 "beats": [{"t": 432, "k": "life_lost"}, {"t": 968, "k": "screen_clear"},
           {"t": 1284, "k": "record"}, {"t": 1902, "k": "lane_over"}, "…"],
 "lulls": [[1512, 1670]],
 "over": {"winner": "green", "draw": false, "timeLimit": true,
          "endRule": "full_time", "reason": "complete", "ticks": 2880,
          "rom": "chomper", "par": 2600,
          "teams": {"green": {"placement": 1, "score": 44.100, "points": 4210}, "…": {}}},
 "hold": 3}
```

There are exactly **four** `teams` keys, and they are the four colour names chrome_common already
knows. `roster` carries the **real policy names** and is spectator-side only.

### Readouts

1. **Run bug** (top, always on). Four plates — `#plates-l` carries RED and GREEN, `#plates-r` carries
   BLUE and YELLOW (chrome_common's own ordering). Each plate: the colour alias, the live **score** as
   its headline number with the raw **points** beneath it in the arcade font, **lives as heart pips**
   baked from `data/heart_<colour>.png` (spent pips greyed), and a small `SCR 2` screen chip. A lane
   that is over dims and gains a struck-through `GAME OVER · 3rd` chip; a lane that has crossed par
   gains a flashing gold `REC` pip. Centre column (`#clock`): `M:SS` from `tick div 24` with `of 2:00`
   and **the ROM name — `CHOMPER` —** in `#clock-caption`. That caption is the "one ROM per round,
   announced" made visible.
2. **The board** (the headline): a 2 × 2 quad-split CRT. Each quadrant is one lane's 17 × 17 screen —
   a dark phosphor plate baked from `data/darkbg.png` and `data/arena_floor.png`, a bright scanline
   overlay, a **tinted 1-tile frame in that lane's colour** with the alias burned into the frame's top
   edge, then the tiles (maze walls as chunky tinted blocks, pellets as dots, power pellets as pulsing
   discs, bricks as tinted bars, bunkers as eroding blocks) and the sprites (avatar as a bright
   chevron pointing along `facing`, hunters as chunky eyes that go blue when fleeing, the ball as a
   bright square with a 6-frame trail, marchers as a rank of glyphs, bolts as short bright dashes).
   The lane's live **points** are baked into the bottom edge of its own frame in `data/ascii.png`, the
   way an arcade screen carries its own score. A lane that is `Over` desaturates to grey and shows a
   `GAME OVER` plate.
3. **Stance chips — where the LLM becomes visible.** Each quadrant carries, on its frame, a small chip
   reading the seat's current stance (`CLEAR`, `HUNT·SW`, `STRIKE`, `SAFE`, `BANK`) in the lane's
   colour, refreshed on each turn boundary, plus a thin **zone highlight** on the named quadrant of
   that lane's grid. Four chips at most.
4. **Contact FX**: a `+10` pip on every pellet, `+50` on a power, the chain values `+100 +150 +200
   +250` popping in sequence, `+30/20/10` on bricks and marchers, `+100` on the saucer; on a
   **life lost** a full-quadrant magenta flash, a short shake of that quadrant only, and `−1 LIFE`;
   on a **screen clear** the quadrant flashes white and `SCREEN 2` wipes across it.
5. **NEW RECORD banner**: when a lane crosses `parScore`, `#bannerlane` runs a full-width gold banner
   — `GREEN — NEW RECORD — 2 610 (par 2 600)` — for 3.0 s, and the beat lands on the scrubber. This is
   the idea's 'new record' banner.
6. **Speech bubbles**: at most **three** at a time — the three lanes with the most recent non-empty
   `say` — drawn for 2.5 s in a **reserved band across the top of the board** (`row ∈ [0, 2)` of the
   35-tile board, above both top quadrants), never positioned relative to an avatar. The band is sized
   from `MaxSayRunes = 48` measured in `data/font.ttf` at the current `--hudscale`, which is exactly
   the reservation the cogchemists 2026-08-24 scar demands; `viewer_smoke.mjs --strict-text-bounds`
   requires `canvas_text.never_inside == 0` for this fixed arena.
7. **Match feed** (`#killfeed`, renamed in copy only): plain language — "GREEN eats a power pellet",
   "GREEN chains 4 hunters — +700", "RED loses a life to H1 — 1 left", "YELLOW clears the wall —
   +350", "BLUE GAME OVER — 1 210", "GREEN passes the record — 2 610", "TURN 12 — 4 new stances".
   Stance `note`/`say` strings appear here; this is where a spectator sees the LLM playing.
8. **Momentum graph** (`#momentum`): ctf's `lead` series in its **four-team** branch — one
   colour-coded score curve per lane over the whole timeline, drawn from the first frame, with deaths
   as visible 1.0 dips and screen clears as steps. On a score-attack coworld this graph *is* the
   story, so it is never hidden.
9. **Transport and integrity**: ctf's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls,
   spoilers, speeds `[1,2,3,4,8,16]`, scrubber with beat markers, tick readout, the end-hold countdown
   and `#mmwarn` — all verbatim.
10. **Endcard**: "GREEN HIGH SCORE · CHOMPER · 44.100 (4 210)" and chrome_common's `ec-*` table listing
    all four seats by **real policy name** with their colour, placement, points, score, lives left,
    screens cleared, deaths, best chain, whether they beat par, and LLM/fallback turn counts, sorted by
    placement.

### Transport rules

- `relayout()` is kept verbatim (`client/replay_broadcast.html`, the `--hudscale` / `--topband` /
  `--band` fixed-point iteration at line 4276): it sets `--hudscale`, `--topband` and **`--band`** on
  `:root`, so the board is letterboxed between the scorebug band and the transport band.
- **No overlay sits in the transport band.** Every overlay the game block adds — the stance-chip
  legend, the ROM chip, the par readout — is positioned inside `#chrome` with
  `bottom: calc(var(--band) + N * var(--u))`, never over it.
- The **endcard stops at `var(--band)`** (the starter's `#endcard { bottom: var(--band) }` rule at line
  1047 is kept) and is **dismissed by every seek** (the starter's behaviour, kept).
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">`** elements — the game
  block upgrades chrome_common's markers to buttons with `aria-label` and `title` (e.g. "New record —
  53.5 s — GREEN passes 2 600") and a click seeks to that tick. **CSS exists for every kind emitted**:
  `.beat-marker.life_lost`, `.beat-marker.screen_clear`, `.beat-marker.record`,
  `.beat-marker.lane_over`, `.beat-marker.over` — one rule per kind, asserted by
  `tests/test_viewer.nim`.

### Art

Real, and baked from what the repo already ships. The CRT plates, scanlines, bloom, vignette, the four
tinted lane frames, maze walls, pellets, bricks, bunkers, avatars, hunters, marchers, balls, bolts and
trails are baked once at startup with **pixie** (already a dependency, already how ctf bakes its
board), using ctf's shipped `data/darkbg.png` and `data/arena_floor.png` as the screen plates,
`client/art/walls/wall_h.jpg` / `wall_v.jpg` as the maze wall plates, `data/ascii.png` as the arcade
points font baked into each quadrant, `data/heart_red.png` / `heart_blue.png` / `heart_green.png` /
`heart_yellow.png` as the lives pips, and `data/font.ttf` for every chrome label. The locker-room card
reuses `client/art/lockerroom/bg.jpg`. No solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`; kept verbatim.
The board is 35 tiles across, so at 360 px a tile is **10.3 screen pixels** and a lane is **175 px** —
the reason the grid is 17 × 17 and the layout is 2 × 2 rather than 4 × 1 (a 4 × 1 strip would give 4.3
px per tile, and a 21 × 21 grid would give 8.2 px; both were rejected for this). At 360 px each plate
shows the colour alias, the score and the lives pips; the ROM name stays in `#clock-caption`; the four
policy names live in the endcard and in each roster row's `title`. Four further rules ship in the game
block: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`
(so the plate captions never collapse to "…"), and under `.tiny` the per-plate raw-points line and the
screen chip collapse into one line, the stance chips and the zone highlights are hidden, and bubble
text is suppressed — while the tiles, sprites, avatars, quadrant frames, aliases and lives pips all
stay, and the NEW RECORD banner stays (it is the one thing a 360 px viewer must not miss). The board
aspect is 1:1, which the chrome derives from the stream. `tests/test_viewer.nim` asserts all four
rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-atari-57`, **public at creation** (public is a certification prerequisite
  — `source-resolves` 404s on private). Slug `atari-57`; `game.name` is also `atari-57`, so the secret
  namespace `secret://coworld/atari-57/anthropic_api_key` matches `game.name` **exactly**
  (cooperative-hunting, 2026-08-25: the namespace must equal `game.name`, not a differently-punctuated
  slug). **Nim module names may not contain `-`**, so on-disk Nim files are `src/atari57.nim`,
  `src/atari57_player.nim`, `src/lane/*.nim`, `replay-viewer/atari57_replay.nim`, while the built
  binaries are `/bin/atari-57` and `/bin/atari-57-player` and every manifest/compose/slug string is
  `atari-57`.
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{ATARI_57_IMAGE}}` (placeholders are derived from **compose service names** by uppercasing and
  replacing `-` with `_`; `{{GAME_IMAGE}}` is not a thing outside ctf's own two-service file — lantern
  0.1.0). Phase 20's manifest generator derives it from `compose.yaml` and `tests/test_manifest.nim`
  asserts the derivation:

  ```yaml
  services:
    atari-57:
      image: coworld-atari-57:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure (nimby 0.1.26,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's
  package tree), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:atari-57 src/atari57.nim` →
  `/bin/atari-57`, and the same for `src/atari57_player.nim` → `/bin/atari-57-player`. The runtime
  stage copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/atari-57"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby with its
  sha256 check, the marker splices, the `test -f`/`grep -q` assertion block) with the asset list
  swapped and the workspace path `/workspace/atari57`.
- **`coworld_manifest_template.json`** (written against the `coworld` 0.1.42 upload contract — validate
  offline with the CLI's `validate_upload_manifest` and `_load_template_manifest` before dispatching):
  - top-level `$schema`, `episode_timeout_minutes: 20`, and top-level `tags` ≥ 3:
    `["arcade","score-attack","single-player","real-time","llm"]`. **`game.tags` does not exist** — the
    validator forbids it and requires `game.description` (pistonball 0.1.0, 2026-08-26).
  - `game.name` `atari-57`; `game.description` (one sentence: "Four cogs play the same arcade
    cartridge from the same seed on four sealed screens at once — pellets, bricks or invaders — and the
    highest score when the credit runs out takes the board."); `game.owner`; `game.runnable`
    `{"type":"game","image":"{{ATARI_57_IMAGE}}","run":["/bin/atari-57"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/atari-57/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-atari-57/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}` (nested under `game`, not top-level; no
    top-level `version`, no `game.display_name`).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`; **every array property carries `minItems`/`maxItems`** (tandem 0.1.0 scar):
    `tokens` (1..4), `players` (1..4), `slots` (0..4), plus `closedRoster`, `seed`, **`num_agents`**
    (1..4), `minPlayers`, `maxTicks` (default 2880), `minTicks` (default 1440), `maxGames` (default 1),
    `turnTicks` (default 120), `turnBudgetMs` (default 16000), `attempt1Ms` (default 9000), `retryMs`
    (default 5000), `turnSpacingMs` (default 12000), `wallClockBudgetSeconds` (default 660),
    `lobbyJoinTimeoutTicks` (default 2880), `startWaitTicks`, `gameOverTicks`, `fastMode`
    (default true), `showPlayerLabels`, `model`, `maxOutputTokens` (default 900), and the ROM keys:
    `rom` (enum `["chomper","brickfall","gallery"]`, default `chomper`), `livesPerLane` (1..12),
    `parScore` (100..20000), `avatarSpeedMilli` (500..4000), `latchTicks` (0..24), `powerTicks`
    (0..480), `screenClearBonus` (0..2000), `rampPermille` (1000..1500), `fireEnabled`, `brakeEnabled`,
    `marchTicks0` (4..60), `fireChancePermille` (0..100), `ballSpeedMaxMilli` (2000..6000). The CLI
    validates every variant and the cert fixture against this schema (injecting `tokens`), so every key
    either appears here or is not settable — and `tests/test_manifest.nim` asserts it covers every field
    `sim_config.update` reads.
  - `game.results_schema`: exactly the 24 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","placements","rom","points","reason","endRule"]`, `reason` enum
    `["complete","deadline","fault"]`, `endRule` enum
    `["all_lanes_over","full_time","wall_clock","sim_fault","host_error"]`, `rom` enum
    `["chomper","brickfall","gallery"]`, and every per-seat array `minItems: 4, maxItems: 4`.
  - `game.protocols`: **both `player` and `global`**, each `{"type":"text","value":"…"}` (objects, not
    bare strings — garble v0.1.0). `player` documents the registration chat frame, the per-tick Sprite
    v1 frames (own lane only), the fact that seats send **no** inputs, the board-view JSON including
    the scoreboard strip, and the stance reply schema with its caps. `global` documents the `/global`
    spectator snapshot, the state JSON above, the `COWLDA57` replay layout (config JSON, action-byte
    log, chat records, hash chain) and the static replay bundle.
  - `game.docs`: `readme` = `{"type":"text","value":"<the README body inlined>"}` and `pages` = three
    entries — `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined: every number in §The game plus the three ROM tables and the three maps>"}}`,
    `{"id":"protocol.md","title":"Wire protocol",…}`,
    `{"id":"stances.md","title":"Writing a lane stance",…}`. A manifest test asserts all four values
    are non-empty text.
  - `player[0]` (the only top-level bundled player entry, with id/type/name/description) =
    `{"id":"baseline","type":"player","name":"Arcader Baseline",
    "description":"Scripted arcade player: take the nearest scoring thing, bail when a threat gets
    inside 28 ticks, cash the power chain when it opens. No LLM.",
    "image":"{{ATARI_57_IMAGE}}","run":["/bin/atari-57-player"],
    "env":{"PLAYER_SCRIPTED":"arcader"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}`. It occupies **all
    four** certification slots — every declared player entry must occupy at least one slot or cert
    fails `players_missing` (raid 0.1.2 → 0.1.3), and `limits.cpu` below `"1"` is a 400 at upload
    (pistonball 0.1.1).
  - **Variants — one per ROM, `num_agents` is 4 in all three, `num_agents` lives inside
    `game_config` (never at the variant's top level — goofspiel-oshi-zumo 0.1.0), and `description` is
    required on each:**

    | id | name | description | **`num_agents`** | `players`/`slots` | `minPlayers` | `rom` | `livesPerLane` | `parScore` | `maxTicks` | `minTicks` | turns | `turnTicks` | `turnSpacingMs` | `turnBudgetMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
    | `chomper` | ROM 1 — Chomper (maze) | 120 pellets, 4 power pellets, four hunters and a wrap tunnel. Eat the maze, cash the chain, do not get caught. | **4** | 4 | 4 | `chomper` | 3 | 2600 | 2880 | 1440 | 24 | 120 | 12000 | 16000 | 660 |
    | `brickfall` | ROM 2 — Brickfall (bricks) | A paddle, one ball and 60 bricks worth 50/30/20/10 by row. The angle comes off the paddle; the ball never slows down. | **4** | 4 | 4 | `brickfall` | 3 | 1800 | 2880 | 1440 | 24 | 120 | 12000 | 16000 | 660 |
    | `gallery` | ROM 3 — Gallery (invaders) | Thirty-two marchers step down, three bunkers erode, and the saucer pays 100. Clear the wave before it reaches row 13. | **4** | 4 | 4 | `gallery` | 3 | 2000 | 2880 | 1440 | 24 | 120 | 12000 | 16000 | 660 |

    All three seat four players, `slots: [{"alias":"RED"}, {"alias":"BLUE"}, {"alias":"GREEN"},
    {"alias":"YELLOW"}]`, `fastMode: true`, `maxGames: 1`, `lobbyJoinTimeoutTicks: 2880`,
    `attempt1Ms: 9000`, `retryMs: 5000`, and **no `tokens` key anywhere in any `game_config`** (the
    runner injects them; a literal `tokens` is rejected by matriculate — knights-archers 0.1.0).
    **A variant changes only the ROM preset — never the seat count, never the clock, never the decision
    cadence, never the wall-clock budget**, which is what makes one budget arithmetic (§Decisions) and
    one score scale (§Scoring) correct for all three. Every variant's `game_config` is constructed and
    stepped by `tests/test_manifest.nim` and `tests/test_rom.nim`, not just the fixture (collab-cooking
    0.1.1, 2026-08-25).
  - **Certification fixture — `num_agents` is 4 here too:** `certification.players` = four
    `{"player_id":"baseline"}` entries; `certification.game_config` =
    `{"players":[{"name":"P1"}, …4…], "slots":[{"alias":"RED"}, {"alias":"BLUE"}, {"alias":"GREEN"},
    {"alias":"YELLOW"}], "num_agents": 4, "minPlayers": 4, "seed": 5140913, "rom": "chomper",
    "livesPerLane": 9, "maxTicks": 1440, "minTicks": 1440, "maxGames": 1, "turnTicks": 120,
    "turnBudgetMs": 16000, "turnSpacingMs": 0, "wallClockBudgetSeconds": 180,
    "lobbyJoinTimeoutTicks": 720, "fastMode": true}` — 12 turns, every seat scripted, no LLM client (no
    credentials offline, so the client disables itself and every turn falls back instantly).
    `livesPerLane: 9` overrides the `chomper` preset's 3 **and** `minTicks == maxTicks == 1440`
    guarantees the episode runs the full 1440 ticks whatever the baselines do — the replay is exactly
    **60.0 s of playback**, comfortably longer than the viewer smoke's 12 s soak (ecos, 2026-08-23: a
    replay shorter than the soak reads as "frozen"). The override also exercises the
    `defaults → preset → explicit` order that `tests/test_rom.nim` pins. Wall cost ≈ 10 s connect + ~2 s
    of physics + the ~20 s shutdown grace ≈ 35 s. Because 35 s is close to `coworld certify`'s 60 s
    default, the release workflow's certify step passes **`--timeout-seconds 300`**
    (cooperative-hunting 0.1.2 → 0.1.3); the fixture is **not** shrunk.
- **Scaffold from `templates/`** with `<slug>` = `atari-57`, `<IMAGE>` = `coworld-atari-57`,
  `<SEATS>` = **4**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim, no
  substitutions), `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh` (**`chmod +x`**).
  Three additions to the template `ci.yml`: the `docker-smoke` step gets
  `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format), the `wasm-viewer` job gets the extra
  `renderer_fixture.html` step of §Tests, and any push-triggered `upload-coworld` job is gated on the
  **`UPLOAD_REQUIRED`** repo variable so it cannot publish an uncertified version that races
  `coworld-release.yml` (derks-gym 0.1.1, 2026-08-28). The `NIM_TESTS_RELEASE_ONLY` repo variable lists
  `tests/test_perf.nim` and `tests/test_baselines.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/atari-57-player"`, one image, env-switched; each
  also sets `PLAYER_POLICY_LABEL`):

  | name | env | role |
  |---|---|---|
  | `atari-57-highroller` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `atari-57-onecredit` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `atari-57-arcader` | `PLAYER_SCRIPTED` = `arcader` | filler |
  | `atari-57-hoover` | `PLAYER_SCRIPTED` = `hoover` | filler |

  A four-seat episode is filled by the platform with the two champions plus fillers — which is what
  makes the cross-play mean meaningful.
- **Repo layout**: `src/atari57.nim`, `src/atari57_player.nim`,
  `src/lane/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, grid.nim, maps.nim, rom.nim,
  sprites.nim, control.nim, stances.nim, baselines.nim, observation.nim, llm.nim, decide.nim,
  roster.nim, replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim,
  wire_constants.nim, server.nim}`, `replay-viewer/{atari57_replay.nim, config.nims, static_replay.js,
  static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, STANCES.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `atari57.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only harness;
the sandbox has no Nim, Docker, emsdk or browser. The **determinism gate** (test 2 plus the viewer
smoke) is inviolable: if it fails, the physics or a build flag changed — fix the code, never the test.

1. **`tests/test_physics.nim`** — sim unit tests: **the no-tunnelling bound is asserted directly** —
   `max(BallSpeedMax, BoltSpeed) = 4 000 < TileU/2 + BoxHalf = 9 000` — and over **50 000** randomised
   legal states the swept-contact test and the end-position test return the **same** answer; a ball's
   applied speed is exactly `(BallFan[j] · speedPermille) div 1000` and `speedPermille` rises by
   exactly 50 per 8 brick hits, capped at 1 400, over 5 000 ticks including 60+ wall bounces; **every
   `BallFan` entry has `vy < 0`** (a paddle can never send the ball into the drain) and a magnitude
   within ±5 % of 2 800, exhaustively over all 7 entries × 4 wall-reflection parities; an avatar or
   sprite centre never leaves its lane; `railBottom` paddles never leave `[18 000, 186 000]`; the turn
   latch applies a buffered direction only at a tile centre and discards it after exactly 6 ticks; a
   brick, bunker hit and marcher kill each resolve with exactly one contact; a `cmd` of 15..255 decodes
   identically to `0` in **both** the server path and the replay-runtime path.
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same ROM + same action-byte log ⇒
   identical `gameHash` at every tick over a full 2880-tick 4-lane run, twice in one process and once
   in a fresh sim; (b) a one-unit change in any action byte changes the final hash; (c) a committed
   golden fixture `tests/data/golden_hashes.json` pins the hash at every 48th tick for seed 5140913 in
   **each of the three ROMs**; (d) **a source guard** that greps
   `src/lane/{sim,grid,rom,maps,sprites,sim_types,sim_config,sim_state}.nim` for
   `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts for `-ffast-math`,
   failing on any hit, plus a grep for `rand(` (only `drawInt` may draw) and a grep for `while ` in the
   sim modules whose loop bound is not a compile-time constant; (e) the four lanes' RNG streams produce
   **identical** first-500 draw sequences from one seed; (f) `rngDraws` is identical between two runs of
   the same action log.
3. **`tests/test_isolation.nim`** (**the lane invariant**) — over 200 randomised episodes of 600 ticks:
   (a) replacing lane `j`'s entire action-byte stream with a different stream leaves every other lane's
   per-tick serialized state **byte-identical**; (b) lane `i` run alone in a one-lane sim reproduces its
   four-lane trajectory exactly; (c) four lanes fed the identical action-byte stream finish with
   identical `points`, `lives`, `screen`, sprite positions and `rngDraws` (the fairness proof);
   (d) a source guard that `stepLane`'s signature takes no `SimServer` and that `src/lane/sim.nim` does
   not import `observation.nim`; (e) the composed LLM user message for seat `s` contains no other
   lane's tiles, sprites, avatar, targets, threats, stance, `note`, `say` or prompt — only the four
   `{alias, score, lives, screen}` scoreboard rows.
4. **`tests/test_maps.nim`** — the three committed maps: each is exactly 17 strings of 17 characters;
   each string's sha256 matches the pin in `maps.nim`; `chomper` has exactly 120 pellets, 4 power
   pellets, 127 walkable tiles, **all reachable** from the start tile by a flood fill that honours the
   row-8 tunnel wrap, and its tunnel wraps col 0 ↔ col 16 in both directions; `brickfall` has exactly
   60 brick tiles on rows 3..6 and an open row 16; `gallery` has exactly 6 bunker tiles and 32 marcher
   spawn slots on rows 2..5; no map has a walkable tile on its outer border except the two `chomper`
   tunnel mouths.
5. **`tests/test_baselines.nim`** (release-only) — **the bounded-orders / legality assertion on the
   scripted baselines**: for 500 pseudo-random world states × both baselines × all three ROMs, the
   emitted stance validates against the reply schema — `mode`, `zone` and `fire` in their enums, `risk`
   finite in `[0,1]`, `lead_ticks` an integer in `[0,48]`, `note` ≤ 160 runes, `say` ≤ 48 runes — **and
   the compiled action byte is in `0..14`** and decodes to a legal `(dir, act)` for that ROM's
   `avatarMode` (no `up`/`down` byte is ever emitted in a `railBottom` ROM, no `fire` byte in a ROM
   without `fireEnabled`, no `brake` byte in a ROM without `brakeEnabled`). Plus the tuning pin: over
   20 seeds × 3 ROMs, four `arcader`s **clear at least one screen in at least 17 of 20 seeds** and end
   with mean points above 1 200; four `hoover`s score strictly fewer points and die strictly more often
   than four `arcader`s; a 2-`arcader`/2-`hoover` mix ends with an `arcader` seat in placement 1 on at
   least 15 of 20 seeds. (This is the anti-regression pin for the whole difficulty tuning: if the
   baselines cannot clear a screen, the three `BaselineParams` numbers are wrong — re-run
   `tools/tune_baselines.nim` and commit the sweep's pick to `tools/ci/baseline_tuning.json`, which
   `tests/test_tuning.nim` re-asserts. The ROM constants and the maps do not move.)
6. **`tests/test_stances.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON, a
   percentage `risk`, `mode` given as `"greedy"`/`"attack"`/`"turtle"`, `zone` given as
   `"top left"`/`"north-west"`/`"middle"`/`"anywhere"`, `fire` given as `"always"`/`"off"`, an unknown
   `mode`, a `zone` that does not exist, `lead_ticks` of `-5` and `999`, NaN/absent fields, a
   300-character `note`, and a `say` whose 48th and 49th characters are a **4-byte emoji** — the
   truncation must land on the **rune** boundary and the result must still round-trip `%$` →
   `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the `arcader` stance plus a `fallback`
   record; a timeout on attempt 1 ⇒ exactly one retry; a `throttled` client ⇒ **zero** retries.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all four seats' calls go out
   in one parallel batch** (the fake records in-flight windows; the test asserts all four intersect); a
   seat whose lane is `Over` is dropped from later batches; consecutive batches are ≥ `turnSpacingMs`
   apart; the per-turn budget is enforced with a hung client; the budget guard switches to scripted and
   the episode still ends `complete/*`; the 660 s stop yields `deadline/wall_clock` **and writes a
   `stopped` record**; a tripped invariant yields `fault/sim_fault` with a partial replay; a
   disconnected seat plays `arcader` and revives on reconnect; a never-connecting seat is reported to
   `COGAME_PLAYER_FAILURE_URI`, logged loudly, and the run still reaches a normal ending; a registration
   that arrives before its player index exists is **held and applied**, not dropped; `minTicks` prevents
   an all-lanes-over ending before tick 1440.
8. **`tests/test_locality.nim`** — the two-name-space and information invariants. Over 200 randomised
   states: seat `s`'s composed LLM user message and its Sprite frame contain **every** tile, sprite and
   counter of **its own** lane (the positive half of the assertion); and contain **no** real player
   name, no `seed`, no RNG state, no future draw, no wall-clock or budget fact, no other seat's
   `policyKind` or fallback state, and no `sim.players[i].address`. Also: `control.laneCommand`'s inputs
   are structurally limited to one lane's state, that lane's stance and the tick.
9. **`tests/test_scoring.nim`** — the formula and its sign: the seven worked examples of §Scoring
   reproduce to 3 decimals; `score == points/100 + lives` exactly for `points ∈ [0, 50 000]` and
   `lives ∈ [0, 12]` with no rounding drift; **no term is ever negative and no score is ever below
   0.000**; points never decrease within a lane; the placement chain is total (`placements` is a
   permutation of 1..4 over 20 000 randomised end states) and exactly one seat wins;
   `win[s] == (placements[s] == 1)`; `records[s] == (points[s] > parScore)`; `lastScoreTick` is the tick
   of the last positive point delta.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full 4-seat scripted
    episode in **each of the three ROMs** writes `results.json` and a `COWLDA57` replay;
    `parseReplayBytes` accepts it; re-simulating from the config + recorded action bytes reproduces
    **every** recorded hash — and this is asserted for **every end reason** (`full_time`,
    `all_lanes_over`, `wall_clock` via a forced short budget, `sim_fault` via an injected guard trip),
    not just `complete` (particle-worlds 13c66d7, 2026-08-26); **`tools/replay_summary.py` output parses
    under a strict UTF-8 JSON parser** (`json.loads(out.decode("utf-8"))`) with the fixture forced to
    carry a non-ASCII `say` and a non-ASCII policy label, so the UTF-8 path is real; the embedded config
    JSON decodes strictly and contains `seed`, `rom`, `parScore`, the fully resolved preset and the
    loaded map's 17 strings; every `stance` record is ≤ 600 runes;
    `results.reason`/`results.endRule`/`results.rom` are in the legal enums; the stream contains exactly
    4 `register` records, one `stance` record per alive seat per turn, at least one `pickup`, one
    `life_lost` and one `screen_clear`, and exactly one `result` record.
11. **`tests/test_server.nim`** — websocket contract: registration chat accepted and **not** echoed into
    the replay chat stream; a prompt over 4000 runes truncated, not rejected; a non-registration chat
    from a player dropped; an input mask from a player ignored; **a bad token is rejected and the socket
    closed** (flatland 0.1.1); **a `Ping` is answered with `Pong`** and a binary registration frame is
    **not** dropped by any `kind != TextMessage` guard (lux-ai / snake-royale); `/healthz`; `/global`
    snapshot → ticks → game over; `/client/global` and `/client/player` serve real pages and neither
    opens the player socket; `/healthz` and `/global` still answer 15 s after the artifacts are written;
    artifact writes to `file://` URIs. **Two name spaces**: the composed LLM user message and the
    player-stream board labels contain no real name, while the chrome roster, `over` and `results.names`
    do.
12. **`tests/test_manifest.nim`** — **`num_agents == 4` in every one of the three variants *and* in
    `certification.game_config`**, and **absent at every variant's top level**;
    `len(certification.players) == 4` and `len(certification.game_config.players) == 4`; no
    `game_config` anywhere carries a literal `tokens`; every declared `player[]` id occupies at least
    one certification slot and its `resources.limits.cpu == "1"`; `results_schema` keys ==
    `playerResultsJson` keys with every per-seat array bounded `minItems: 4, maxItems: 4`; every array
    in `config_schema` declares `minItems`/`maxItems`; `game.protocols` has **both** `player` and
    `global` as `{"type":"text",…}`; `game.docs.readme` and all three pages are non-empty text;
    `game.description` present and `game.tags` **absent** (tags top-level, ≥ 3);
    `game.replay_viewer.bundle == "static-replay-viewer"` and there is no top-level `version` or
    `game.display_name`; `game.owner` present; **every variant** has the same `maxTicks`, `minTicks`,
    `turnTicks`, `turnSpacingMs`, `turnBudgetMs` and `wallClockBudgetSeconds`; every variant's
    `wallClockBudgetSeconds ≤ 0.6 × 1200`; `attempt1Ms + retryMs ≤ turnBudgetMs`;
    `maxTicks mod turnTicks == 0`; `minTicks ≤ maxTicks`; the compose service name uppercased with
    `-`→`_` equals the image placeholder and the image is `coworld-atari-57`; the secret namespace
    equals `game.name`; `config_schema` covers every field `sim_config.update` reads.
13. **`tests/test_rom.nim`** — the preset machinery: `applyPreset` obeys **`defaults → named preset →
    explicit key`** in that order (the cert fixture's `rom: "chomper"` + `livesPerLane: 9` resolves to
    9, not 3); each of the three named ROMs resolves to exactly the row of §The ROM table; **each
    variant's `game_config` is constructed and stepped for 600 ticks with four `arcader`s without a
    fault** (collab-cooking 0.1.1, 2026-08-25: test every variant, not just the fixture);
    `fireEnabled: false` makes an `act == 1` byte a no-op with **no** observable effect on the hash;
    `brakeEnabled: false` makes `act == 2` a no-op; a `railBottom` ROM ignores `dir ∈ {1,2}`; the point
    tables in the observation's `rules` block equal the ones the sim actually pays.
14. **`tests/test_viewer.nim`** — static assertions over `client/replay_broadcast.html` and
    `client/chrome_common.js`: `chrome_common.js` is **byte-identical** to the starter's copy (sha256
    pinned); `replay_broadcast.html` still contains ctf's `relayout()` with `--band`, `--topband` and the
    `--hudscale` clamp on `:root`; `#endcard { bottom: var(--band) }`; `#scorebug`, `#bannerlane`,
    `#killfeed`, `#transport`, `#mmwarn`, `#endcard`, `#momentum` and the `.tiny` block are present;
    `#viewpanel`, `#minimap`, `#zoombar`, `#fpv` and `#povBadge` are **absent**; a `.beat-marker` CSS
    rule exists for **every** beat kind the sim emits (`life_lost`, `screen_clear`, `record`,
    `lane_over`, `over`) and every marker is a `<button>`; no game-block top-level name collides with
    chrome_common's alias list; the `.plate-name { flex: 1 1 auto; min-width: 3.2em` rule and the three
    `.tiny` rules of §Legible at 360 px are present; the state JSON's `teams` keys are exactly
    `red`/`blue`/`green`/`yellow`; `broadcast_core.js` differs from the starter's copy in **exactly** the
    `LANE_WIRE` identifier; no `ctf_`/`CTF_`/`paintball` identifier survives in `client/`,
    `replay-viewer/` or `src/`; `static_replay.js` sets both `data-replay-loaded` and
    `data-replay-error`; and `config.nims` contains **no** `MODULARIZE` or `EXPORT_NAME`.
15. **`tests/test_startup.nim`** — `/bin/atari-57` exits non-zero with a clean message and no traceback
    when `COGAME_CONFIG_URI` is missing or unparseable, or when `rom` is not one of the three; the seed
    is randomised when unpinned (before `config.update`) and honoured when pinned; both entrypoints
    exist and are executable in the image.
16. **`tests/test_perf.nim`** (release-only) — 2880 ticks × 4 lanes plus 11 520 autopilot evaluations
    complete in under 60 s.

**CI jobs beyond the Nim tests:**

- `docker-smoke` — `tools/ci/docker_smoke.sh` runs a raw-Docker episode from the certification fixture
  with **`SMOKE_SEATS=4`** (an independent cross-check against `certification.game_config.num_agents`;
  a mismatch prints `SEAT-COUNT FAIL:`) and `SMOKE_REQUIRE_REPLAY_JSON=0`, asserts **every one of the
  four player containers' exit codes** as well as the game's, and uploads the replay it produced as the
  `smoke-replay` artifact.
- `wasm-viewer` (`needs: docker-smoke`) — asserts `tools/build_replay_viewer.sh` and
  `tools/ci/viewer_smoke.mjs` exist and the hook is executable, builds the bundle, asserts a non-empty
  `.wasm`, downloads the smoke replay, and then **EXECUTES the bundle in headless chromium**:
  ```
  node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
       --replay dist/smoke/<name>.replay --timeout 90 --soak 12 --strict-text-bounds
  ```
  The job fails if `data-replay-loaded` never arrives, if `data-replay-error` is set, if the soak sees
  playback stop advancing, or if `canvas_text.never_inside` is non-zero (fixed arena). The 1440-tick
  fixture is 60 s long and `minTicks == maxTicks` guarantees it, so a 12 s soak cannot end the replay.
  **This is the only gate that runs the viewer rather than checking that its files exist**
  (cogame-lantern, 2026-08-23).
- `wasm-viewer`, second step — **`tools/ci/renderer_fixture.html`**: `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so every seat plays scripted and the smoke replay carries only the baselines'
  fixed `say` strings; nothing in CI would otherwise exercise the bubble band, the stance chips, the
  NEW RECORD banner or the feed at full cap. The fixture **loads the real shipped
  `dist/static-replay-viewer/index.html` in an iframe and shims only the wasm entry** (never a
  re-implementation of the drawing — particle-worlds 46cf69d, 2026-08-26), drives the page's own text
  path with a **full-cap 48-rune `say` and 160-rune `note` on all four seats at once**, all four stance
  chips live and the record banner firing, at 360, 620 and 1280 px, self-checks its own string lengths,
  and is run through `viewer_smoke.mjs --strict-text-bounds` in its own step (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Any Atari emulator, ROM image, ALE binding, `AutoROM` download or PettingZoo dependency, and any
  claim of parity with any of them.** The ROMs are proprietary, an emulator cannot live inside the
  native↔wasm determinism boundary, and bit-exact ALE parity is not a goal, not tested, and not claimed
  anywhere in the repo. Every constant in this note is this cabinet's own. The idea's game names are
  provenance.
- **Pixel and RAM observations, `frameskip`, the 18-action ALE joystick set, stochastic sticky actions,
  the 108k-frame cap, and any CNN/neural policy interface.** The idea's stated gap ("pixel-input
  competition") is **not** filled by v1: seats get a structured JSON board view plus a 17-line ASCII
  screen, and the platform's policy interface here is an LLM prompt or a scripted baseline. There is no
  RGB crop, no frame stack and no per-frame joystick socket. A raw per-tick action channel is a protocol
  addition, not a redesign — the autopilot is already a pure function of `(stance, lane state, tick)` —
  but it is not in v1.
- **`num_agents = 1`.** Four isolated lanes is the shape the platform can schedule; a genuine
  single-seat episode is a platform question, not a game question, and is deferred exactly as
  vizdoom-deathmatch deferred it.
- **Any inter-lane interaction whatsoever** — shared boards, sabotage, handicaps, item drops, co-op
  lanes, a shared hazard track, or a symbol channel between seats. The scoreboard strip (four aliases,
  scores, lives, screens) is the entire cross-lane surface and it is read-only, symmetric and outside
  the sim. `say` and `note` are one-way to the spectator feed.
- **More than three ROMs**, and any ROM that changes the seat count, the grid, the clock, the decision
  cadence or the wall-clock budget. Fresh cartridges (a climbing game, a river-crossing game, a
  digging game) are new presets on this engine and a `GameVersion` bump, not a redesign — but they are
  not in v1.
- **A persistent all-time-per-ROM leaderboard as repo work.** The platform league *is* the board, and
  `results.rom` lets it be split per ROM after the fact. The in-repo substitute is the committed
  per-ROM `parScore` and the NEW RECORD banner, which is self-sufficient inside one replay.
- **A season bracket, cross-episode memory, carry-over lives, continues, or any state that survives an
  episode.** Every episode starts on a fresh cartridge with three lives.
- **Two-player ROMs, team ROMs, cooperative motives and any non-score-attack scoring.** `num_agents` is
  4 in every variant and the cert fixture, and v1 has exactly one motive.
- **Diagonal movement, continuous analogue movement, a variable-length paddle, ball-ball collision,
  sprite-sprite collision other than bolt-vs-marcher, gravity, curved walls, moving walls, powerups
  beyond the power pellet, extra lives, bonus stages and brick rebuilding.**
- **Fog of war, vision cones, the first-person POV and any partial observation of your own lane.**
  Deleted from ctf, not disabled: your screen is a CRT you are sitting at. What is hidden is *the other
  screens* and *who is playing*, which is §Server's list.
- **Everything else ctf's arena rules carried**: teams, guns, flags, hearts-as-objectives, respawn,
  grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the barrage, the hill,
  the paint grid, procedural terrain, the map pool, the map editor and mapkit. Deleted, not disabled.
- **Player debug-sprite overlays** (ctf's `0x86` channel) and the zoom/minimap panel. The seats send no
  inputs and draw no overlays in v1; `#viewpanel` is removed because the board always fits the frame.
- **Audio, CRT curvature shaders, camera cuts, per-lane spotlight camera, slow-motion replays**, and any
  downloaded art asset.
