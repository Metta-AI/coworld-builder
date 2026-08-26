# cogame-atari-cabinet — design note (2026-08-26, paintbot lineage)

`Metta-AI/cogame-atari-cabinet` is **THE CABINET**: a four-seat, real-time retro arcade coworld
built on **one** paddle-and-ball engine and a **rotating ROM**. Four cabinets sit on the four sides
of a square CRT arena. Each one owns a **goal mouth** in its own wall, a **paddle** that slides in
front of it, and (ROM permitting) a **brick castle** in between. One or two balls rip around the
box at rising speed. Every ball that gets through your mouth costs you a life; the last cabinet
still holding lives wins. Which of the three ROMs is loaded — `warlords`, `quadrapong`,
`foozpong` — is a manifest variant, announced before the round, stamped into the replay, and
printed on the scorebug. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its
read-only mount `/workspace/starters/coworld-ctf`. **Every convention there holds here unless this
note says otherwise** — the 24 Hz wall-clock-paced game loop, the one-byte-per-seat-per-tick
recorded action log, the `COWLDCTF`-family replay codec with its per-tick `gameHash` chain,
keyframes and lull spans, the server-side decision layer
(`src/ctf/{decide,directives,control,baselines,llm}.nim`: **one parallel LLM batch per turn**, two
bounded deadlines, an inter-batch rate floor, a budget guard, tolerant parsing, rune caps, a
scripted fallback), the mummy server and its `COGAME_*` runtime contract, the seat/cog split and
the `cogAlias` two-name-space rule, the broadcast chrome (`client/replay_broadcast.html` +
`client/chrome_common.js` + `client/broadcast_core.js`), the emscripten static replay bundle
(`replay-viewer/`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`) and the
`GameVersion` prepend-only changelog discipline are all inherited.

**Starter choice, in one line:** the cabinet is a **real-time game loop with rules written fresh
for this coworld** — the **first** row of the starter table (`prompts/10-design.md`;
`playbooks/make-coworld.md` §Phase 0) — because paintbot already ships, tested, every layer this
game needs except the paddle rules: a wall-clock-paced integer tick loop, a per-tick per-seat
action-byte log inside a replay whose hash chain is re-checked in the browser, a server-side
low-rate LLM decision layer over a per-tick deterministic controller, published scripted baselines
that emit the identical decision object, a **native four-team** scorebug/momentum chrome
(ctf's `4ffa` variant already drives red/blue/green/yellow plates), and a static wasm viewer that
re-derives every frame. It is deliberately **not** the `cogame-moba` row: that row is for
**bit-exact** ports of an existing external C/RL environment, and **no Atari emulator and no ROM
can be hosted here** — the PettingZoo/ALE environment names in the idea are *provenance*, not a
specification. (Coordinator ruling, 2026-08-26. Operator ruling 2026-08-22, Cogball: a new
real-time game takes paintbot. Precedents on this starter, whose patterns are followed here
wherever they fit: `cogame-cogball`, `cogame-tandem`, `cogame-pistonball`
— `runs/2026-08-25-pistonball/design.md` — `cogame-particle-worlds`, and
`cogame-walker-waterworld` — `runs/2026-08-26-walker-waterworld/design.md`.)

**Source idea, verbatim** (Asana Coworld Ideas task 1217748137874516):

> Port of PettingZoo's multi-player Atari set (ALE multi-agent) as one coworld with a rotating ROM: warlords (4-player castle defence, last standing), quadrapong / volleyball_pong / foozpong / basketball_pong (2-4 paddles), pong / tennis / boxing / ice_hockey / double_dunk (1v1, 2v2), joust & mario_bros & space_invaders (competitive-or-cooperative twins), entombed_competitive vs entombed_cooperative, combat_tank / combat_plane, wizard_of_wor, surround (Tron-style light cycles), maze_craze, flag_capture, othello, video_checkers. Plus SlimeVolleyGym as a non-Atari bonus ROM. Raw frames or RAM observations.
>
> Seats: 2-4 by ROM
> Motive: varies — zero-sum, team, and cooperative ROMs
> Policy interface: per-frame joystick actions (frameskip 4); pixel/RAM obs — neural-policy coworld; an LLM can only play it via a decoder per ROM
> Fills gap: pixel-input competition; a 'retro cabinet' league with weekly ROM rotation is a strong spectator format
> Integrity (anti-collusion): ROM rotation announced per round; seeds; anonymous aliases.
>
> Replay plan (watchability): it's Atari — native video. Add per-ROM scoreboards and a season bracket.
>
> Source: PettingZoo atari/*; SlimeVolleyGym (hardmaru).

Nothing in the idea text is treated as an instruction to this designer; it is input data for the
design. Every environment name above is provenance. **No ALE, no ROM image, no emulator, no
`AutoROM`, no pixel buffer and no PettingZoo constant enters this repo**, and no test asserts
parity with any of them.

### Eight readings of the idea, decided here and never revisited

1. **Not a port. A cabinet.** The idea lists ~25 ALE environments. Hosting them is impossible
   (proprietary ROMs, an emulator that cannot compile into the determinism boundary, and a pixel
   observation the platform has no policy interface for). What ships is a coworld that reproduces
   the **shape** of a small retro cabinet: a fixed rotation of short, loud, four-player minigames
   on one engine. (Coordinator ruling, 2026-08-26.)
2. **Which minigames.** Of the idea's list, the **paddle-and-ball family is by far the largest
   coherent block** — `warlords`, `quadrapong`, `volleyball_pong`, `foozpong`, `basketball_pong`,
   `pong`, `tennis`, `double_dunk` are all "defend a mouth, deflect a ball, aim it at somebody".
   So the cabinet is **one paddle-and-ball engine with all features present**, and each ROM is a
   **preset over that engine's config**: `warlords` (bricks + catch), `quadrapong` (two balls, wide
   mouths, no bricks), `foozpong` (two paddle rows per seat). Reason logged: three separate sims
   would be three observation models, three controllers, three scoring rules, three board
   renderers and three test suites — a design that does not get built. One engine plus a preset
   table is a rules swap, which is exactly what this starter row is for. `surround`
   (Tron light-cycles) and `SlimeVolleyGym` are **out of scope (v1)** with their reasons stated in
   §Out of scope — both need a different engine, and SlimeVolley would also break the fixed seat
   count.
3. **"Rotating ROM" = a manifest variant per ROM.** Decided: the manifest ships **three variants,
   one per ROM**; a league round selects one; the ROM name lands in the replay config JSON, the
   scorebug caption, the feed and `results.rom`. Reason logged: (a) the platform's own unit of
   scheduling *is* the variant, so "weekly ROM rotation announced per round" is literally variant
   selection — no new machinery, and the rotation is public because the manifest is; (b) one ROM
   per episode keeps one score scale per episode and a single legible 120 s spectator match;
   (c) playing all three inside one episode would either triple the wall clock or cut each ROM to
   40 s, and would turn one replay into three unrelated boards — worse to watch and worse to score.
   **The ROM never changes the seat count:** `num_agents` is **4** in all three variants and in the
   cert fixture.
4. **"Seats: 2-4 by ROM"** is closed at **`num_agents` = 4**, everywhere, with no range and no
   variant that changes it (§Seats).
5. **"Motive: varies — zero-sum, team, and cooperative ROMs."** v1 is **one motive: four-way
   free-for-all**, every seat for itself, distinct per-seat scores. Reason: team and cooperative
   ROMs change the *scoring semantics* (shared score, pot payout) and therefore what the league
   ranks by, which cannot vary between variants of one coworld without making the board
   meaningless. Team ROMs are §Out of scope.
6. **"An LLM can only play it via a decoder per ROM"** is the idea's own diagnosis and it is
   exactly what ships — with one refinement: because all three ROMs run on one engine, **one
   decoder serves all three**. The LLM sets one closed-schema **stance** per seat every
   **K = 120 ticks (5.0 s)**; a deterministic autopilot turns the standing stance into a
   **per-tick command byte** at 24 Hz. The byte is the action, the byte is what the replay records,
   the byte is what the viewer replays. The scripted baselines are *the same autopilot* driven by
   a fixed heuristic stance policy, so the two policy kinds are strictly comparable and a baseline
   is legal by construction. The platform's LLM pin is not optional and is not skipped.
7. **"Integrity: ROM rotation announced per round; seeds; anonymous aliases"** is implemented as:
   the ROM is a public manifest variant (announced by construction); a **seeded** seat→side
   permutation drawn at `t = 0`; **seeded** serve directions; anonymous colour aliases in-game; and
   a game with **no notion of who holds any other seat**.
8. **"Replay plan: it's Atari — native video; per-ROM scoreboards"** becomes: a CRT-styled square
   board with scanlines and phosphor bloom, four coloured castles, chunky bricks, a trailing ball,
   **four** scorebug plates with lives pips and brick-integrity bars, and the ROM name in the clock
   caption (§Viewer). "Native video" is not literal — the replay is the starter's binary action log
   re-simulated in wasm, which is strictly better than a video (seek, speed, hash-checked). The
   "season bracket" is the platform league and is §Out of scope as repo work.

**There is no `OPEN` section.** Every reading the idea leaves loose — how many seats, which
minigames, what rotation means, what the score is, how a joystick becomes an LLM decision, what
ends the episode — is a rail the designer decides, and each is decided below with its reason.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How atari-cabinet satisfies it |
|---|---|
| Starter by game shape | **`Metta-AI/coworld-ctf` (paintbot)** — a real-time 24 Hz loop with new rules. The arena rules (teams, guns, flags, fog, paint) are replaced by the cabinet; the loop, action-log replay, decision layer, viewer, chrome and CI wiring stay. (§Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-atari-cabinet`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (champions `atari-cabinet-castellan`, `atari-cabinet-gunner`) vs `PLAYER_SCRIPTED=bulwark` / `PLAYER_SCRIPTED=spinner` (fillers). One image `coworld-atari-cabinet`, one player entrypoint `/bin/atari-cabinet-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`; ctf's `tools/build_replay_viewer.sh` kept (its ecos `mkdir -p` fix is already at line 22 of the starter's copy); the **same** `src/cabinet/sim.nim` compiles into `replay-viewer/cabinet_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is ctf's page with a game block **appended**; the CRT arena, castles, bricks, paddles and balls are baked at startup with pixie from ctf's shipped `data/font.ttf`, `data/arena_floor.png`, `data/darkbg.png`, `client/art/walls/wall_h.jpg`, `wall_v.jpg`, `client/art/lockerroom/bg.jpg` and the four `data/heart_<colour>.png`. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | In-game every cabinet is `RED`, `BLUE`, `GREEN`, `YELLOW` and nothing else; real policy names live only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (§Tests 11). |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | ≈329 s expected / ≈464 s absolute worst case against the 720 s budget; a **660 s** engine hard stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** in variant `warlords`, variant `quadrapong`, variant `foozpong`, **and** `certification.game_config`; `<SEATS>` = **4** in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Four cabinets, one square CRT, two balls, two minutes.** The arena is a 100 × 100 box. Each of
the four sides belongs to one cabinet. In the middle of your side is your **mouth** — a gap 36
units wide. In front of it, 14 units into the arena, is your **paddle**: a bar 14 units long that
slides left and right along your own side and nothing else. Between them, in the `warlords` ROM,
is your **castle**: nine bricks across the mouth. The ball bounces off the solid parts of every
wall, off every paddle, and off every brick — chipping the brick away. When a ball crosses your
mouth line inside the gap, you **lose a life** and the ball is re-served from the centre. Lose
your last life and your mouth is welded shut, your paddle and castle are removed, and the other
cabinets fight on in a smaller box. **The last cabinet with lives standing wins.**

Every deflection speeds the ball up. Where the ball leaves your paddle depends on **where on the
bar it landed** and **which way the bar was moving** — thirteen outgoing angles, 11.25° apart.
That is the whole strategy: a paddle is not only a shield, it is a **gun**, and every rally is a
choice about **whom to shoot at**. Three rivals; one of them is about to die; one of them has been
shooting at you.

### Seats

**`num_agents` = 4. One seat = one cabinet = one side of the box.** Reasons, in order: (a) four is
what the idea's headline ROM (`warlords`, "4-player castle defence, last standing") *is*, and it is
the only count at which "aim your return at a specific rival" is a real decision rather than a
tautology; (b) four parallel LLM calls per turn sit comfortably inside the Bedrock sidecar's
30-requests-per-minute-per-episode cap at a 12 s batch floor (§Decisions); (c) a four-seat episode
is exactly the platform's normal fill — two champions plus two fillers — so the cross-play mean the
ladder ranks by is meaningful from round one; (d) ctf's chrome is already four-team-native
(`chrome_common.js:49-68`, `TEAM_ORDER = ['red','blue','green','yellow']`), so the scorebug,
momentum graph and endcard need no structural change. The idea's 2–4 range is closed here at
**4** and is 4 in all three manifest variants, in the certification fixture and in `SMOKE_SEATS`.

Sides are numbered by the boundary walked **counter-clockwise** with y up:

| side `k` | wall | colour / alias | chrome `teams` key |
|---|---|---|---|
| 0 | SOUTH (`Y = 0`) | **`RED`** | `red` |
| 1 | EAST (`X = 100`) | **`BLUE`** | `blue` |
| 2 | NORTH (`Y = 100`) | **`GREEN`** | `green` |
| 3 | WEST (`X = 0`) | **`YELLOW`** | `yellow` |

Seat `s` (slot 0..3) drives cabinet `perm[s]`, where `perm` is a permutation of `0..3` drawn once
at `t = 0` from `config.seed` by Fisher–Yates over one dedicated integer draw stream. In-game the
cog driving cabinet `k` is called by its **colour alias** — an alias that names *a station on the
board*, which every seat legitimately knows, and never an entrant. Colour aliases rather than
`CAB-n` because a spectator reads "GREEN scores on RED" instantly and an LLM writes
`"aim_at": "GREEN"` without an index lookup — the legibility pin ("render 10, not T"). `perm` is
written into the replay config JSON (the viewer needs it to map real names onto sides) and into
`results.cabinets`, and is **never** visible to any seat.

Seats are symmetric in rules, scoring, observation shape and actuator. They are not symmetric in
which side they get — and that is re-dealt every episode by `perm`, which is the idea's
anti-collusion clause.

### World, units, and why they are integers

The whole sim runs in **integers**, for Cogball's, Tandem's, pistonball's and waterworld's reason:
replays are re-simulated by the **emscripten/wasm32** build of the same Nim module that the
**native amd64** server ran, and their per-tick `gameHash` chains must match bit-for-bit. Integers
make that true by construction rather than by an argument about two builds of libm agreeing.
`src/cabinet/{sim,arena,rom,trig}.nim` contain **no floating point at all** (grep-enforced in CI,
§Tests 2d).

| Quantity | Unit | Type |
|---|---|---|
| Position, length | **micro-units (µu)**, 1 cabinet unit (cu) = 10 000 µu | `int32` |
| Ball speed (scalar) | µu per tick | `int32` |
| Paddle velocity | µu per tick | `int32` |
| Ball direction index | 1/64 turn, `0..63`; index `d` = view bearing `5.625° · d` counter-clockwise from east | `uint8` |
| Unit vectors | Q12 (4096 = 1.0), from the committed `DirQ64` table | `int32` |
| Score accumulators | **micro-points** (1e-6 of a score point) | `int64` |
| Counters (lives, saves, chips, knockouts, concedes) | — | `int32` |

**Arena:** a square, `x, y ∈ [0, 1 000 000] µu` (100.00 cu on a side), origin top-left, **y down**
(ctf's screen convention). Board render scale **1 board pixel = 1 000 µu** → `MapWidth = 1000`,
`MapHeight = 1000`, board aspect **1:1**. That is 1 000 000 logical map pixels against ctf's
813 865, so `boardRenderScaleFor` still returns `RenderScale = 2` (`MaxSupersampledMapPixels` is
8 000 000, `src/ctf/global.nim:1095`) and
`predictedViewerRenderBytes(1000, 1000) = 1e6 · 4 · (4·2² + 6) = **88 000 000 bytes (88 MB)**`
against `WasmViewerBudgetBytes` 1 600 000 000 — the viewer's load-time capacity preflight
(`replay-viewer/ctf_replay.nim`) passes with 18× headroom and every one of those constants is
**kept unchanged**.

**Cabinet coordinates** — the only coordinates a policy, the chrome or this note ever quotes — are
`X, Y ∈ [0, 100]` with the **origin at the arena's bottom-left corner, x right, y up**:
`X = x_µu / 10 000`, `Y = (1 000 000 − y_µu) / 10 000`. Bearings reported to policies are degrees
counter-clockwise from east in that orientation (`0° = right`, `90° = up`). Every number shown to a
policy is rounded to 2 decimals.

**Side-local frame.** For side `k` a policy also gets `(along, depth)`, which is the frame a paddle
actually lives in: `depth` is the perpendicular distance from that side into the arena
(`0 … 100`), and `along` is the signed position along the side in `[−50, +50]`, oriented so that
**+along is counter-clockwise around the box**:

| side `k` | `along` | `depth` |
|---|---|---|
| 0 SOUTH | `X − 50` | `Y` |
| 1 EAST | `Y − 50` | `100 − X` |
| 2 NORTH | `50 − X` | `100 − Y` |
| 3 WEST | `50 − Y` | `X` |

The corner where side `k` ends at `along = +50` is the same corner where side `(k+1) mod 4` begins
at `along = −50`. So **your `+along` end touches the next cabinet counter-clockwise**
(`RED → BLUE → GREEN → YELLOW → RED`), which is stated in the system prompt and is the whole
geometric fact a policy needs.

`DirQ64*: array[64, tuple[x, y: int32]]` in `src/cabinet/trig.nim` is a **committed literal
table**, generated once by `tools/gen_trig_table.nim` and checked in, where entry `d` is
`(round(4096·cos(5.625°·d)), round(−4096·sin(5.625°·d)))` — i.e. the view bearing `5.625°·d`
expressed in **sim (y-down) components**, so the sim never negates anything at a call site. A test
re-derives every entry from `math.cos`/`math.sin` (§Tests 2e). Because 64 is divisible by 4, every
reflection and every side rotation is **exact index arithmetic** and the sim needs **no square root
and no trigonometry whatsoever**:

- off a **vertical** surface (x-component negated): `d' = (32 − d) mod 64`;
- off a **horizontal** surface (y-component negated): `d' = (64 − d) mod 64`;
- into side `k`'s local frame: `dl = (d − 16·k) mod 64`; back out: `d = (dl + 16·k) mod 64`.

Every collidable in this game is **axis-aligned** (walls, mouth lines, bricks, paddles), and the
ball is treated as an **axis-aligned square of half-side `BallHalf`** — deliberately, because it is
both authentically Atari and completely root-free: every contact test is a box-vs-box overlap plus
a swept axis-crossing time computed by **integer cross-multiplication in `int64`** (compare
`Δa · db` against `Δb · da`; no division, no `isqrt`, no `float`).

### The ROM preset table (the rotation)

One engine; three presets. The preset is applied in this **exact order** by
`src/cabinet/rom.nim`: **schema defaults → the named `rom` preset → any explicitly supplied config
key**. So the certification fixture can override `startingLives` on top of `rom: "warlords"`
(§Packaging), and a test pins the order (§Tests 12).

| config key | `warlords` | `quadrapong` | `foozpong` | meaning |
|---|---|---|---|---|
| `rom` | `warlords` | `quadrapong` | `foozpong` | the ROM name, stamped everywhere |
| `startingLives` | **3** | **5** | **3** | lives per cabinet |
| `ballCount` | **2** | **2** | **2** | balls live at once |
| `brickRows` | **1** | **0** | **0** | rows of 9 bricks across each mouth |
| `catchEnabled` | **true** | false | false | a paddle may grip and hold a ball |
| `farPaddle` | false | false | **true** | a second paddle row per cabinet at depth 34 |
| `goalHalfCu` | **18** | **22** | **18** | half-width of the mouth |
| `paddleHalfCu` | **7** | **6** | **6** | half-length of the near paddle |
| `farPaddleHalfCu` | — | — | **5** | half-length of the far paddle |
| `ballSpeed0Milli` | **550** | **650** | **600** | serve speed, thousandths of a cu/tick |

Everything else (arena size, depths, brick geometry, speed ramp, timings, the decision cadence,
the wall-clock budget, `num_agents`) is **identical across all three ROMs**, which is what makes
one score scale and one wall-clock budget correct for all of them.

### Geometry and constants (fixed; identical in every ROM and every episode)

```
ArenaSide         = 1_000_000 µu   (100.00 cu)
BallHalf          =    12_000 µu   (  1.20 cu)   -- the ball is an axis-aligned square
PaddleDepth       =   140_000 µu   ( 14.00 cu)   -- centre-line depth of the near paddle
PaddleThickHalf   =     8_000 µu   (  0.80 cu)   -- so the bar is 1.60 cu thick
FarPaddleDepth    =   340_000 µu   ( 34.00 cu)   -- foozpong only
PaddleTravelHalf  =   430_000 µu   ( 43.00 cu)   -- |paddle centre along| <= 43.00
PaddleStepSpeed   =     4_000 µu/tick (0.40 cu/tick)  -- one drive level
PaddleMaxSpeed    =    16_000 µu/tick (1.60 cu/tick)  -- level 4, i.e. 38.4 cu/s
BrickRowDepthLo   =    80_000 µu   (  8.00 cu)   -- brick row 1 occupies depth 8.00..10.50
BrickRowDepthHi   =   105_000 µu   ( 10.50 cu)
BrickRow2DepthLo  =    40_000 µu   (  4.00 cu)   -- only if brickRows == 2 (not in v1's ROMs)
BrickRow2DepthHi  =    65_000 µu   (  6.50 cu)
BricksPerRow      = 9                            -- centres at along -16,-12,...,+16 cu
BrickHalfWidth    =    18_000 µu   (  1.80 cu)   -- 3.60 cu wide, 0.40 cu gaps
BallSpeedStep     =       350 µu/tick (0.035 cu/tick per deflection)
BallSpeedMax      =    13_000 µu/tick (1.30 cu/tick = 31.2 cu/s)
ServeDelayTicks   = 24                           -- 1.0 s of dead air after a concede
ServeSpawnDepth   = the arena centre (50.00, 50.00)
HoldTicksMax      = 48                           -- 2.0 s, the longest a catch may hold
OutfanAngles      = 13                           -- 22.5 deg .. 157.5 deg, 11.25 deg apart
maxTicks          = 2880  (120.0 s)              -- 24 decision turns
turnTicks         =  120  (  5.0 s)              -- K, the LLM decision cadence
```

**Serves.** All `ballCount` balls are served at `t = 0` from the arena centre, and a conceded ball
is re-served from the centre after `ServeDelayTicks`. A serve draws its direction index from the
seeded stream, **rejecting** any index whose local depth-component is within 8 indices of a wall
tangent (i.e. `d mod 16 ∈ {0, 1, 15}` is rejected) so no ball is served nearly parallel to a wall,
and rejecting any index that points at a cabinet that is already **out**. Rejection sampling is
bounded at **32 attempts**, after which the serve takes the first legal index of the fixed scan
`[6, 22, 38, 54, 10, 26, 42, 58]` — degrade-never-hang applies to sampling too, and an unbounded
rejection loop in a hashed step function is exactly the hang this rule forbids. When two balls are
served in the same tick the second is offset by `+7` indices from the first.

**Seeded draws.** Exactly two kinds of thing are drawn, in this fixed order, from one dedicated
stream seeded with `config.seed`: (1) `perm`, once at `t = 0`; (2) every serve direction, in serve
order. Every draw goes through one helper, `drawInt(lo, hi: int32): int32`, implemented as
`int32(lo + int32(rng.next() mod uint64(hi - lo + 1)))` — `rng.next()` is `std/random`'s
`uint64`-domain step, so **no draw ever touches `rand(int)`**, whose `int` is 32-bit under
`--cpu:wasm32` and 64-bit natively (ctf's documented hazard). A monotonic `rngDraws` counter is
mixed into `gameHash`, so a divergence in *how many* draws a build took is caught at the tick it
happens rather than as a mysterious position mismatch later.

### Time

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf** (`src/ctf/sim_types.nim:317,376`),
because every speed-coupled layer (`PlaybackSpeeds`, the lull scan, the momentum series,
`tickTime`, the transport bar) is keyed to it. There are **no substeps**, and the arithmetic that
makes that a guarantee rather than a hope:

- The ball's fastest legal speed is `BallSpeedMax = 13 000 µu/tick`.
- The **shallowest** contact window is the paddle: `PaddleThickHalf + BallHalf = 20 000 µu` of
  depth. A brick is `25 000 + 12 000 = 37 000 µu`. A wall is a half-plane. So the ball overlaps
  every collidable for at least **two** consecutive end-of-tick positions in every legal
  configuration.
- `PaddleMaxSpeed = 16 000 µu/tick` exceeds `BallSpeedMax`, so a paddle can always out-run the ball
  along its own side — a miss is a decision, never a physics limitation.

The **swept-contact test** of §Resolution order step 4 is nevertheless what ships, as belt and
braces and because it makes the guarantee testable (§Tests 1) rather than a comment.

An episode is **`maxTicks = 2880` ticks = 120.0 s of sim time**, divided into **24 decision turns
of `turnTicks = 120` ticks (5.0 s)**. The turn length is set by the wall-clock budget (§Decisions:
four parallel LLM calls per turn against the Bedrock sidecar's 30-rpm-per-episode cap), and 5.0 s
of open-loop stance is affordable because the autopilot between turns is **fully reactive** — a
stance says *whom to shoot and how far to stray*, and the autopilot tracks, intercepts and aims at
24 Hz.

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 120 == 0` and `phase == Playing`: the stances collected for turn
   `t div 120` become each seat's `activeStance[seat]` (§Server), quantised to integers on parse.
   The server writes one **`stance` chat record per seat** into the replay. `activeStance` is
   **not** mixed into `gameHash` — the per-tick command bytes it produces are recorded, and those
   are what the viewer replays (step 2).
2. **Autopilot compile**, in **cabinet index order 0 … 3** (never seat order — seat order varies
   with `perm` and the loop must not). `control.paddleCommand(sim, k)` is a pure function of
   `(cabinet k's own state, the full board state, its seat's activeStance, the tick)` returning a
   **command byte** `cmd ∈ 0 … 242`:

   ```
   near = int(cmd) mod 9              # 0..8, near-paddle drive
   far  = (int(cmd) div 9) mod 9      # 0..8, far-paddle drive (ignored unless farPaddle)
   grip = int(cmd) div 81             # 0 = none, 1 = catch, 2 = release
   paddle velocity = (level - 4) * PaddleStepSpeed, level in {near, far}
   ```

   243 of the 256 byte values are legal; **`cmd >= 243` is repaired to `40`** (`near = 4`,
   `far = 4`, `grip = 0`: both bars still, no grip) both in the server and in the replay runtime,
   so a corrupt byte can never desynchronise the two. The autopilot sits **outside** the
   determinism boundary, exactly as ctf's `control.nim` does, and may use floating point; the byte
   it produces is written to the replay with
   `replayWriter.writeInputMaskChange(tickTime(t), seat, cmd)`, which already writes **only on
   change** and updates `lastMasks[seat]` (`src/ctf/replays.nim:161`). Nothing else in the loop is
   re-derived at playback.
3. **Paddle motion**, cabinet index order, near paddle then far paddle: `alongCentre += velocity`,
   then clamp `|alongCentre| ≤ PaddleTravelHalf` (a paddle that hits its travel limit simply
   stops; there is no rebound). `paddleVel` is recorded as the *applied* delta, because the
   deflection fan reads it. A cabinet that is **out** has no paddles and its byte is ignored.
4. **Ball motion and contacts**, ball id order `B1 … B<ballCount>`. For each **live** ball:
   1. A **held** ball (grip in force) does not move: its centre is pinned to
      `(along = paddle centre, depth = PaddleDepth + PaddleThickHalf + BallHalf)`, its `holdTicks`
      increments, and if `holdTicks ≥ HoldTicksMax` it is force-released this tick as if
      `grip == 2`.
   2. Otherwise compute the tick's displacement `Δ = (speed · DirQ64[d]) div 4096` and find the
      **earliest** swept contact along the segment `pos → pos + Δ` against, in this priority order
      when two contacts share the same crossing time: **(a) paddles** (near then far, cabinet index
      order), **(b) bricks** (cabinet index order, row 1 then row 2, column −16 → +16),
      **(c) mouth lines**, **(d) solid walls**. Crossing times are compared by integer
      cross-multiplication; the priority order breaks exact ties deterministically.
   3. **No contact** → `pos += Δ`; done.
   4. **Paddle contact on cabinet `k`** → advance the ball to the contact point; `saves[k] += 1`;
      `lastTouch[ball] = k`; compute the outgoing direction from the **deflection fan** (below);
      `speed := min(speed + BallSpeedStep, BallSpeedMax)`; if `grip == 1` for cabinet `k`, the ROM
      has `catchEnabled`, and cabinet `k` holds no ball, the ball becomes **held**
      (`catches[k] += 1`, a `catch` event) instead of departing; otherwise it departs along the
      new index with the remaining fraction of `Δ`. **One ball takes at most one contact per
      tick** — the remaining displacement is applied without further contact resolution, which is
      safe because §Time proves no collidable is thinner than one tick of travel.
   5. **Brick contact on cabinet `k`, row `r`, column `c`** → the brick is destroyed
      (`bricks[k][r][c] = false`); `chipsBy[lastTouch[ball]] += 1` when `lastTouch` is a cabinet
      other than `k` (a cabinet chipping its **own** wall scores nothing — stated so it is not a
      loophole); the ball reflects off the face it crossed by the exact index rule; speed is
      **not** increased (only paddles accelerate the ball); a `chip` event is emitted, and a
      `breach` event when that column is now empty in every row.
   6. **Mouth-line contact on cabinet `k`** (crossing `depth = 0` with `|along| < goalHalf`) →
      **concede**: `lives[k] -= 1`, `concedes[k] += 1`; if `lastTouch[ball]` is a cabinet other
      than `k`, `knockouts[lastTouch[ball]] += 1`; the ball is removed (state `Serving`, timer
      `ServeDelayTicks`, `lastTouch` cleared); a `concede` event is emitted. If `lives[k]` reaches
      0, cabinet `k` is **out**: `outTick[k] = t`, its mouth becomes solid wall, its paddles and
      remaining bricks are removed, an `eliminated` event is emitted, and its seat is dropped from
      all later LLM batches.
   7. **Solid-wall contact** (the non-mouth part of any side, or the whole side of an out cabinet)
      → reflect by the exact index rule; no counters change; the remaining displacement is applied.
   8. A ball in state `Serving` ticks its timer down; at zero it is served from the centre with a
      seeded direction, `speed := ballSpeed0`, `lastTouch = none`, state `Live`.

   **The deflection fan.** Working in side `k`'s local direction frame
   (`dl = (d − 16·k) mod 64`), the outgoing local index is
   ```
   j    = clamp( round(offset * 6 / paddleHalf) + spin, -6, +6 )
   dl'  = 16 - 2*j                       # 4 .. 28, i.e. 22.5 deg .. 157.5 deg, 11.25 deg apart
   d'   = (dl' + 16*k) mod 64
   ```
   where `offset` is the signed contact offset from the bar's centre along `+along` (so a hit on
   the `+along` half sends the ball toward `+along` — the classic paddle behaviour), and
   `spin = sign(paddleVel) · (|paddleVel| ≥ 12 000 ? 2 : |paddleVel| ≥ 4 000 ? 1 : 0)`. Both
   `offset·6` and the `round` are integer (`round(a/b)` implemented as `(2a + b) div (2b)` for
   `a ≥ 0` and mirrored for `a < 0`, so it is symmetric under negation). `dl'` is always in
   `4 … 28`, so **the outgoing ball always travels away from the defender's side** — a paddle
   cannot deflect a ball into its own mouth, ever.
5. **Score.** Every counter that moved this tick is folded into `scoreMicro[k]` by the formula of
   §Scoring. It is a running total, recomputed nowhere else.
6. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged. `gameHash` mixes `tick`, `phase`, every cabinet's `lives`, `out`, `outTick`, near and
   far `alongCentre` and `paddleVel`, `heldBall`, every brick bit, every ball's `state`, `pos`,
   `dir`, `speed`, `holdTicks`, `lastTouch`, `serveTimer`, all of `saves`, `chips`, `knockouts`,
   `concedes`, `catches`, `scoreMicro`, `rngDraws`, and a digest of `perm`. It never mixes FX,
   notes, `say`, feed text, stances or policy labels.
7. **End checks**, in this order: exactly one cabinet with `lives > 0` → end `complete` /
   `last_standing`; wall-clock stop tripped → end `deadline` / `wall_clock`; `t + 1 ≥ maxTicks` →
   end `complete` / `full_time`; an invariant guard failure (a ball centre outside the arena, a
   `speed` above `BallSpeedMax` or below `ballSpeed0`, a direction index outside `0..63`, a paddle
   centre outside `±PaddleTravelHalf`, a `holdTicks` outside `0..HoldTicksMax`, a serve that fell
   through to the fixed scan more than 8 times in an episode, an `int32` overflow caught by the
   debug build's range checks) → end `fault` / `sim_fault`.

There is no rescue rule, no difficulty ramp and no mercy. A cabinet whose paddle never moves is
eliminated inside 30 s and finishes fourth with a score near zero — a legible, correctly scored
failure.

### Scoring, sign, and what the league ranks by

The game is a **four-way free-for-all** and every seat gets its **own** score. All five terms are
**non-negative**, so the minimum score is `0.000` and higher is always better; conceding is
punished by *not earning* the lives term rather than by a negative number, which keeps the whole
scale readable on a scorebug.

```
scoreMicro[k] = (60_000_000 * livesLeft[k]) div startingLives    # 0 .. 60.000, ROM-independent
              + 15_000_000 * (placement[k] == 1)                 # the crown
              +  2_000_000 * knockouts[k]                        # rival lives you took
              +    500_000 * chips[k]                            # rival bricks your ball broke
              +    250_000 * saves[k]                            # balls your paddles deflected

score[k]      = scoreMicro[k] / 1_000_000       # emitted as a double, 3 decimals
results.scores    = [score[0..3]] in SEAT order
results.placements= [1..4] in SEAT order, a permutation
results.win       = [placement == 1] in SEAT order
```

The lives term is **normalised by `startingLives`**, deliberately: `quadrapong` starts everyone on
5 lives and `warlords` on 3, and without the division the same performance would be worth 100
points in one ROM and 60 in another. With it, the achievable range is 0 … ≈122 in `warlords`,
0 … ≈118 in `quadrapong` and 0 … ≈120 in `foozpong` — within 4 % — so a league board that mixes
ROMs is still meaningful, even though (see below) a round normally does not mix them.

`chips` is structurally 0 in the two brick-free ROMs; its weight (0.5, capped at 27 available
bricks = 13.5 points) is chosen small enough that this cannot flip a ranking.

**Placement**, computed once at game over by this exact chain:

1. a cabinet with `lives > 0` outranks every cabinet with `lives == 0`;
2. among cabinets with lives: more `livesLeft`, then more `bricksLeft`, then more `saves`, then
   **lower cabinet index**;
3. among eliminated cabinets: **later** `outTick`, then more `knockouts`, then **lower cabinet
   index**.

The index tiebreak makes the chain total, so `placements` is always a strict permutation of
`1..4` and exactly one seat takes the crown. There are no shared places.

Worked examples (all `warlords`, `startingLives = 3`, 9 bricks per castle so 27 rival bricks are
available to each seat):

| Outcome | livesLeft | crown | knockouts | chips | saves | **score** |
|---|---|---|---|---|---|---|
| Wins on last standing, barely scratched | 2 | yes | 6 | 22 | 71 | **95.750** |
| 2nd at full time, solid defence | 2 | no | 3 | 9 | 58 | **65.000** |
| 3rd, eliminated at 104 s | 0 | no | 2 | 6 | 40 | **17.000** |
| 4th, eliminated at 41 s | 0 | no | 0 | 1 | 12 | **3.500** |
| Wins at full time, all four alive, 3 lives each | 3 | yes | 1 | 4 | 63 | **94.750** |
| Paddle never moves (every byte 40) | 0 | no | 0 | 0 | 4 | **1.000** |
| `spinner` in `quadrapong`: all attack, no defence | 0 | no | 4 | 0 | 21 | **13.250** |

**What the league ranks by: the seat's mean `results.scores` value across its episodes — its
cross-play mean.** Elo over `placements` is *also* legitimate for this coworld (unlike the
cooperative ones — raid, tandem, pistonball, walker-waterworld — the four scores are distinct and
one seat always wins), but the **primary and declared metric is the mean score**, because it
separates "won by one life" from "won without conceding" and because it is comparable across the
three ROMs by the normalisation above. Phase 50 ranks on mean score.

**The ROM and the league round.** A league round selects **one** variant, so a round does not mix
ROMs; this is the idea's "ROM rotation announced per round" and it is announced by construction
because the manifest is public. `results.rom` records which ROM an episode played, so a mixed
board can always be split per ROM afterwards ("per-ROM scoreboards", the idea's replay plan).
**v1 game code has no notion of who is in any other seat.**

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail. No
other value may appear in either field.

| `reason` | `endRule` | When | Scored |
|---|---|---|---|
| `complete` | `last_standing` | Exactly one cabinet still has `lives > 0`. The good ending. | as at the elimination tick |
| `complete` | `full_time` | `maxTicks` (2880) reached with two or more cabinets alive. The normal ending. | as at `maxTicks` |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed first. The sim stops at that tick, scores the state as it stands, writes the game-over frame and a complete replay up to that tick. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. | as at the stop tick |
| `fault` | `sim_fault` | A step-7 invariant guard tripped. Partial replay written. | as at the fault tick |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts written before re-raising. | as at the fault tick |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2880 = 120 s of
lobby) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only, `src/ctf/server.nim:1199`), its cabinet is driven
by the `bulwark` baseline for the whole run, and the run plays to a normal ending. Three live
cabinets against one baseline is still a game, so the episode remains meaningful.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {bulwark, spinner}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=bulwark`. A scripted policy seated as a champion is a FAILURE state.

### Where the decision happens, and the LLM client

In the **game server**, not the player container — paintbot's own architecture
(`src/ctf/llm.nim`, `src/ctf/decide.nim`, `src/paintball_player.nim`), kept. The
`anthropic_api_key` coworld secret is injected into the *game* pod via
`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/atari-cabinet/anthropic_api_key`;
without that manifest env the hosted container never receives the secret and every league episode
plays scripted while local certify still passes (hive, 2026-08-23). Phase 60 greps the *game* log
for `falling back` / `LLM provider is unavailable`.

`src/cabinet/llm.nim` is `src/ctf/llm.nim` with the identifier rename only. Kept exactly:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`)
  → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (`readCogameUri`) → **none** (client
  `disabled = true`; every turn falls back instantly with no network wait, which is what lets
  offline certification finish in seconds).
- **One** Bedrock model candidate: `us.anthropic.claude-haiku-4-5-20251001-v1:0`. No sonnet
  inference profile is a candidate — every one of them times out on every sidecar call
  (cogame-raid round 2, 2026-08-23). The `throttled` fast-fail that skips the retry when the
  provider answered 429 with no other candidate is kept verbatim: a retry inside the same turn
  cannot succeed.
- `max_tokens = 900` (400 truncates). **No `output_config.effort`** for haiku. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`. No `temperature`.
- A system prompt that demands the reply **begins with `{`** (Haiku answers prose-first otherwise).
- `extractJsonObject` (first `{` … last `}`, fence-tolerant) and the **rune-boundary** truncation
  (`runeLen`/`runeSubStr`), kept.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **K = 120 ticks (5.0 s of sim time)**, **24 turns** per episode. At each
turn the server builds the request bodies for every seat **that is still alive** and issues them as
**ONE parallel batch** — `client.curl.makeRequests(@[req0 … req3], timeout)`, curly's batch API,
which is exactly what `src/ctf/decide.nim:427` already does. **Seats are never queried
sequentially.** At most 4 calls per turn × 24 turns = **96 calls** per episode, at most 4 in
flight, and fewer once cabinets are eliminated.

The binding constraint is not latency, it is the **Bedrock sidecar's cap of 30 requests per minute
per episode** (playbook gotcha, raid round 2). Four requests per batch means a batch may start at
most every 8 s; the design uses **`turnSpacingMs` = 12 000** → 4 requests / 12 s = **20 rpm**,
comfortably under. That, not the model, is why there are 24 turns and why a turn is 5.0 s of sim
time.

Per-turn timing, all monotonic-deadline bounded, and every deadline a whole number of seconds
because curly hands it to `CURLOPT_TIMEOUT`, whose granularity is whole seconds and whose
conversion **floors** (`src/ctf/decide.nim:419-428`):

- attempt 1 batch deadline **`attempt1Ms = 9 000`** (four parallel haiku calls; ~3–6 s typical);
- every seat that timed out, errored, returned non-JSON or returned no usable stance is retried
  **once**, again as a single batch, deadline **`retryMs = 5 000`** — unless the client is
  `throttled`, in which case the retry is skipped outright;
- the whole turn is wrapped in **`turnBudgetMs = 16 000`** (`attempt1Ms + retryMs = 14 000 ≤
  16 000`, asserted by §Tests 12);
- the **inter-batch wall floor** of 12 000 ms is measured start-to-start and is a bounded,
  stop-interruptible `sleep`.

```
turn 0 batch starts at t = 0; turns 1..23 start 12 s apart      = 276 s
last turn's own LLM cost (<= 16 s hard cap)                     =  16 s
lobby / connect wait for 4 player pods (typical 15 s;
  cap lobbyJoinTimeoutTicks 2880 = 120 s)                       =  15 s   (typical)
2880 ticks of physics + 4 autopilots/tick + 2 balls             =   2 s
game-over hold + results + replay write (retrying uploader)     =  20 s
                                                                -------
expected total                                                  ~329 s   < 720 s budget
absolute worst case (120 lobby + 276 + 16 + 2 + 20 + 30 slack)  ~464 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                          = 660 s  -> reason "deadline"
platform kill (episodeTimeoutSeconds)                            = 1200 s
```

`fastMode: true` in every variant: the sim advances as soon as every player container has
acknowledged the frame, so sim time is not charged against the wall clock — the decision turns are
the pacing. The seats send no inputs at all (the server computes every command byte), so
`docs/PROTOCOL.md`'s warning about the Sprite v1 Ready packet (`0x85`) corrupting dead-reckoned
input timing does not apply, and the player harness sends `0x85` after every frame exactly as
`src/paintball_player.nim` does.

**Budget guard (settles early without shortening the run).** At the start of each turn, if
`elapsed + 2 × (turnSpacingMs + turnBudgetMs) > wallClockBudgetSeconds`, the LLM is switched off
for every remaining turn and the run finishes on the scripted layer (microseconds per turn), so
the episode ends `complete/*` rather than `deadline`. A `budget_guard` record names the turn it
fired. This is ctf's own guard (`src/ctf/decide.nim:340`), retargeted to include the batch spacing.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the inter-batch floor, the
outer per-turn deadline, `lobbyJoinTimeoutTicks` on the connect wait, the bounded serve rejection
sampler, mummy's socket timeouts on the serve thread (which runs independently of the game loop, so
a 16 s LLM stall cannot drop four connections), the 660 s engine stop, and ctf's `gameOverTicks`
hold before exit. On **two** consecutive failures for a seat (attempt + retry, or one attempt when
`throttled`) that seat's stance for the turn is the **`bulwark`** stance and a `fallback` record is
written with `cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials,
budget_guard}`. A seat that disconnects mid-run keeps playing: its stance source degrades to
`bulwark` and revives on reconnect. **No failure mode leaves a paddle uncommanded** — the autopilot
always has a stance: this turn's, else last turn's, else `bulwark`'s.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are ONE of four arcade cabinets around a square CRT arena, 100 x 100 units.
Coordinates are units from the bottom-left corner; x runs right, y runs up.
Each cabinet owns one side: RED owns the bottom (y=0), BLUE the right (x=100),
GREEN the top (y=100), YELLOW the left (x=0). Your "+along" end touches the
next cabinet counter-clockwise: RED -> BLUE -> GREEN -> YELLOW -> RED.
In the middle of your own side is your MOUTH, a gap in the wall. 14 units in
front of it slides your PADDLE, a bar you move left and right along your own
side only. In the WARLORDS rom a row of 9 BRICKS sits between them.
THE POINT OF THE GAME: every ball that crosses your mouth costs you a LIFE.
Run out of lives and you are OUT - your mouth is welded shut and you are done.
The last cabinet with lives standing WINS.
YOUR PADDLE IS ALSO A GUN. Where the ball leaves it depends on WHERE ON THE BAR
it lands and WHICH WAY the bar was moving: hit it on your +along half and the
ball goes toward +along; sweep the bar as you hit and the angle steepens.
Thirteen outgoing angles. Every deflection makes the ball FASTER.
You score for: lives you still have at the end (this is the big one), winning,
each rival life you take with a ball you touched last, each rival brick your
ball breaks, and each ball your paddle deflects. Nothing is ever subtracted.
YOU CAN SEE THE WHOLE SCREEN - every ball, every paddle, every brick, everyone's
lives. It is a CRT; nothing is hidden. What you CANNOT see is who is playing the
other cabinets or what they are planning. You CANNOT talk to anyone and nobody
sees anything you write.
Every 5 seconds you set your STANCE for the next 5 seconds. A deterministic
autopilot runs it 24 times a second: it predicts where each ball will reach your
paddle line, gets the bar there, and picks the contact offset that aims your
return where you told it to. You choose WHAT to defend and WHOM to shoot.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars, your reasoning",
 "stance":"guard"|"aim"|"camp"|"catch"|"chase",
   // guard : intercept the ball named in "target_ball" (or, if it will not
   //         reach you, the ball that reaches you soonest) and return it
   //         straight back off the middle of the bar. Safest.
   // aim   : same interception, but choose the contact offset that sends the
   //         ball at "aim_at"'s mouth. If that offset cannot be reached in
   //         time the autopilot takes whatever offset it can - it never
   //         misses on purpose.
   // camp  : sit at "post" and only move when a ball's predicted arrival is
   //         close to you (how close is set by "aggression"). Cheap, safe,
   //         and it concedes anything wide.
   // chase : go for whichever ball arrives soonest, at full bar speed, with
   //         the most aggressive aim at "aim_at" available. Maximum damage,
   //         and it is how you end up out of position for the second ball.
   // catch : as "guard", but GRIP the ball on contact and hold it up to 2 s,
   //         then release it aimed at "aim_at". Only the WARLORDS rom allows
   //         this; elsewhere it behaves as "guard". While you hold a ball you
   //         cannot defend the other one.
 "target_ball":"B1"|"B2"|"any",
 "aim_at":"RED"|"BLUE"|"GREEN"|"YELLOW"|"none",   // never yourself
 "post":-43.0..43.0,        // where "camp" idles, in along-units on your side
                            // (0 = the centre of your mouth)
 "lead_ticks":0..48,        // how far ahead the autopilot commits the bar
                            // (24 ticks = 1 second)
 "aggression":0.0..1.0,     // 0 = never leave the post, 1 = chase everything
 "say":"<=48 chars"}        // spectators only; no cabinet ever sees it
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(paintbot's `operatorBlock`, kept), a blank line, then the seat's board-view JSON (§Server). The
prompt text is never echoed into the replay — only `policyKind`, the label and the resulting
stance.

### Champion #1 — `atari-cabinet-castellan` (owner daveey), `PLAYER_PROMPT`

```
Lives are worth 20 points each and nothing else on the board comes close. You
are a goalkeeper who shoots when it is free, never a duellist.
Rules, in order.
1. If ANY ball's arrival on your line is inside 48 ticks, you are defending:
   stance "guard" on that ball, lead_ticks 16, aggression 0.9. Do not try to
   aim while a ball is inbound and close - a missed aim costs 20, a boring
   return costs 0.
2. If a ball is inbound but further than 48 ticks away, aim: stance "aim",
   target_ball that ball, aim_at the ALIVE rival with the FEWEST lives left,
   lead_ticks 12, aggression 0.8. Killing a wounded cabinet is worth 2 points
   now and removes a gun that is pointed at you for the rest of the game.
3. If the rom is WARLORDS, only ONE ball is live, and at least two rivals still
   have bricks, use "catch" instead of "aim": hold it, then release aimed at the
   fewest-lives rival. A held ball cannot score on you, and 2 seconds of holding
   is 2 seconds nobody else can hurt you either.
4. If no ball will reach your line at all, stance "camp", post 0.0,
   aggression 0.45. Sit in the middle of your own mouth. Never post wider than
   +/-12: the middle of the gap is the only place that covers both halves.
5. If you have exactly one life left, drop every aim: "guard" or "camp" only,
   aggression 1.0, post 0.0, for the rest of the game.
Keep lead_ticks between 8 and 20. Never set aggression below 0.3 - a bar that
will not move is a bar that concedes.
```

### Champion #2 — `atari-cabinet-gunner` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
You win by being the last one standing, and the fastest route there is to make
the other three shoot each other while you take the free shots. Play the table,
not the ball.
Read the scoreboard first. Name the LEADER (most lives; on a tie, the one with
the most bricks) and the WEAKEST alive rival (fewest lives).
1. If a ball is inbound inside 36 ticks: "guard" it, lead_ticks 14,
   aggression 1.0. Defence first, always - but only inside 36 ticks, because
   sitting on your post all game wins nothing.
2. Otherwise, if YOU are not the leader: "aim" at the LEADER, target_ball the
   ball that reaches you soonest, lead_ticks 10, aggression 0.85. Every life you
   take off the leader is a life you do not have to out-survive.
3. Otherwise (you ARE the leader): "aim" at the WEAKEST rival, lead_ticks 10,
   aggression 0.7. Finish the cripple and get the board down to three.
4. If two balls are live and both will reach your line inside 72 ticks, forget
   aiming entirely: "camp", post = the midpoint of the two predicted arrivals
   clamped to +/-20, aggression 0.75. One bar cannot aim twice.
5. If you are OUT of bricks and every rival still has some, switch to "chase"
   for one turn with aim_at the nearest rival by side (your +along neighbour):
   a naked mouth needs the ball kept far away, and the fastest way to do that is
   to keep hitting it.
Never aim_at yourself. Never set post beyond +/-25 - past that you have left
your mouth open and someone will notice.
```

### The autopilot (deterministic, one function, shared by every policy)

`src/cabinet/control.nim`, `paddleCommand(sim, k) -> uint8`, evaluated once per tick per cabinet in
index order. Both LLM stances and scripted-baseline stances are compiled by this same code, so the
two policy kinds are strictly comparable and a baseline is legal by construction. It sits
**outside** the determinism boundary (ctf's rule: recorded bytes, not re-run logic) and may use
floats.

With `S` = my seat's active stance, `c` = my near bar's centre in along-units:

1. **Arrival prediction.** For every live, unheld ball, straight-line-propagate it with exact wall
   reflections — **bounded at 4 reflections and 240 ticks**, and deliberately **ignoring bricks and
   every other paddle** (a prediction that modelled other paddles would be modelling other
   policies) — and record `(arriveTick, arriveAlong)` for the first crossing of `depth =
   PaddleDepth` on **my** side, or "never". The same walk records which cabinet's line each ball
   reaches first; that is what the observation's `arrive_at` reports.
2. **Ball choice.** `S.target_ball` if it is live and arrives; else the ball with the smallest
   `arriveTick`; else none.
3. **Desired contact offset `off`.**
   - `guard`, `camp`, `catch` → `off = 0` (dead centre: the safest, straightest return).
   - `aim`, `chase` → for each of the 13 outgoing indices `j = −6 … +6`, walk the outgoing ray
     with up to **2** wall reflections and test whether it crosses `aim_at`'s mouth segment; take
     the **smallest |j|** that does (a shallower deflection is a smaller demand on the bar); if
     none does, take `j = ±6` toward `aim_at`'s side by the counter-clockwise index difference.
     Then `off = j · paddleHalf / 6`. If `aim_at` is `none`, out, or my own alias, behave as
     `guard`.
4. **Desired bar centre.** `c* = arriveAlong − off`, clamped to `±PaddleTravelHalf`. In `camp`,
   `c*` is `S.post` unless `|arriveAlong − S.post| ≤ S.aggression · 43 + 8`, in which case it is
   the intercept. In `chase`, `c*` is the intercept with `S.lead_ticks` forced to 0. With no ball
   at all, `c* = S.post` (`camp`) or `0` (every other stance).
5. **Drive.** `want = (c* − c) / max(1, min(S.lead_ticks, arriveTick))` in µu/tick;
   `near = 4 + clamp(round(want / PaddleStepSpeed), −4, +4)`; deadband: if `|c* − c| < 1 500 µu`
   then `near = 4`.
6. **Grip.** `grip = 1` when `S.stance == catch`, the ROM has `catchEnabled`, I hold no ball, and a
   contact is predicted this tick. `grip = 2` when I hold a ball and either
   `holdTicks ≥ 24 + round(S.aggression · 24)` or a second ball's `arriveTick ≤ 24`. Else 0.
7. **Far paddle** (`foozpong`): the same steps 1–5 against the **second**-smallest `arriveTick`
   ball at `FarPaddleDepth`, with `off = 0` always and `c* = S.post · 0.5` when no ball will reach
   it.
8. **Out cabinet, or any phase other than `Playing`** → `cmd = 40`.

The autopilot contains **no memory across ticks**, no knowledge of any other seat's stance, and no
access to anything the seat's own observation does not carry —
`tests/test_locality.nim` asserts the signature cannot see more.

### Scripted baselines

Both emit the *same* stance object on the same 120-tick cadence, so their output is legal by
construction and directly comparable to an LLM's, and both are pure functions of the observation a
seat would receive.

- **`bulwark`** — the certification player, the per-turn fallback, and the default for a seat that
  registers with neither env var. **Algorithm, evaluated once per turn for cabinet `k`:**
  1. If cabinet `k` is out → `{stance: camp, post: 0.0, aggression: 0.0}`.
  2. Else if some ball's `arriveTick` on my line is `≤ reactTicks` (default **56**): let `b` be the
     soonest such ball and `w` the alive rival with the fewest lives (ties → fewest bricks left,
     then lowest cabinet index).
     - if the ROM has `catchEnabled`, exactly one ball is live, and I hold none →
       `{stance: catch, target_ball: b, aim_at: w, lead_ticks: 14, aggression: aggressionMilli/1000}`;
     - else if `arriveTick > 24` →
       `{stance: aim, target_ball: b, aim_at: w, lead_ticks: 12, aggression: aggressionMilli/1000}`;
     - else → `{stance: guard, target_ball: b, lead_ticks: 16, aggression: 0.95}` (close ball, no
       aiming).
  3. Else if any ball is live → `{stance: camp, post: campPostCu, aggression: 0.45}`.
  4. Else (every ball is mid-serve) → `{stance: camp, post: 0.0, aggression: 0.40}`.
  5. Override in every branch: if `livesLeft == 1`, the stance is forced to `guard` (or `camp` when
     nothing is inbound) with `aim_at: none` and `aggression: 1.0`.
  `say` is one of five fixed strings chosen by which branch fired. Four `bulwark`s produce a real
  game — rallies, breaches, at least one elimination on most seeds — which is the behaviour the
  cabinet is about and the anti-regression pin of the whole physics tuning (§Tests 5).
- **`spinner`** — the second filler, deliberately different in shape and weaker: it never defends
  on purpose and never camps.
  `{stance: chase, target_ball: "any", aim_at: <the alive rival at index (k + 1 + (turn mod 3)) mod 4>,
  lead_ticks: 0, aggression: 1.0}` every turn, unless out (then `camp, post 0`). It hits hard, takes
  a lot of `saves` and `knockouts`, and gets eliminated because chasing with `lead_ticks 0` means
  arriving late. This gives the ladder a spread and gives a champion a chaotic neighbour to cope
  with.

Three tunables — `reactTicks` (56), `campPostCu` (0) and `aggressionMilli` (800) — are a
`BaselineParams` object, not literals, exactly as `src/ctf/baselines.nim` does it (its
`DefaultBaselineParams` comment at lines 30-51 is the template): `tools/tune_baselines.nim` sweeps
them over a bounded grid, `tools/ci/baseline_tuning.json` records the sweep's pick, and
`tests/test_tuning.nim` asserts the shipped defaults still equal it. **The physics constants in
§The game and the ROM presets are not swept and are not tunable by the harness** — if the baselines
cannot hold a rally, the sweep moves these three numbers, not the sim.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf/paintball arena rules go** (teams as sides of a fight, guns, flags, fog cones,
respawn, grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the
hill, the paint grid, the map pool and the map editor all leave the repo):

| ctf path | atari-cabinet |
|---|---|
| `src/ctf/sim.nim` (4102 lines: gameplay core, combat, vision, items) | `src/cabinet/sim.nim` — the paddle/ball/brick core and the step loop of §The game. |
| `src/ctf/arena.nim`, `paint.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `tools/map_render.nim`, `docs/MAPKIT.md`, `docs/pool-review.html`, `scripts/` | `src/cabinet/arena.nim` — the fixed square geometry of §The game, the four side-local frames, the brick lattice, the swept box-contact tests, the bounded seeded serve sampler, the seeded `perm`, and the pixie CRT bake. **Deleted, not ported**; there is no map generator, no `mapSpec`, no wall mask and no procedural terrain in this coworld. |
| — (new) | `src/cabinet/rom.nim` — the three ROM presets and the strict `defaults → preset → explicit` application order. |
| `src/ctf/global.nim` (8070 lines) fog of war, vision cones, first-person raycast, killfeed art, item sprites | `src/cabinet/global.nim` — top-down sprite composition: the CRT box with scanlines and bloom, four coloured mouths, brick rows, near/far paddles, balls with motion trails, aim rays, hit FX. Perfect information both spectator-side and seat-side (§Server). `boardRenderScaleFor`, `MaxSupersampledMapPixels`, `predictedViewerRenderBytes`, `WasmViewerBudgetBytes` and `shoutBubbleZoomFor` are **kept verbatim**. |
| `src/ctf/directives.nim` (`Intent`, `CogOrder`, `SquadDirective`) | `src/cabinet/stances.nim` — the `CabinetStance` object, the closed `Stance` enum, the tolerant parser and the repair table of §Server. Same file shape, same rune discipline (`truncateRunes`, `sanitizeSay`, the no-leading-brace rule for `say`). |
| `src/ctf/control.nim` (nav grid, flow fields, aim) | `src/cabinet/control.nim` — `paddleCommand` of §Decisions. ~220 lines instead of 536; no nav grid, no flow field, no cached fields. |
| `src/ctf/baselines.nim` (`holdline`, `sprayer`) | `src/cabinet/baselines.nim` — `bulwark`, `spinner`, and `BaselineParams`. |
| `players/baseline/` (the CTF bot) | deleted; the only player binary is `src/atari_cabinet_player.nim`. |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/paintball/`, `docs/plans/*` | rewritten for the cabinet; ctf's plans/designs deleted. |
| `arena/`, `caos/`, `caos-tools/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/render_map_pool.nim`, `tools/build_pool_review.py`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf`/`paintball` → `cabinet` rename sweep only, `CTF_WIRE` →
`CABINET_WIRE`; a CI grep asserts no `ctf_`/`CTF_`/`paintball` identifier survives outside
comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/cabinet/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `writeInputMaskChange` (used **as-is**: our command byte is a value, and `writeInputMaskChange` already writes change-only), `checkReplayHash`. Two named edits below. |
| `src/ctf/replay_runtime.nim` → `src/cabinet/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports and the `cmd >= 243 → 40` repair, which is shared code with the server. |
| `src/ctf/server.nim` → `src/cabinet/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the held-registration table, the frame limiter, the replay-switch path, the `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. Five named edits below. |
| `src/ctf/llm.nim` → `src/cabinet/llm.nim` | the credential ladder, the single-haiku model list, the `throttled` fast-fail, `curly.makeRequests` batching, `extractJsonObject`, rune truncation. Rename only. |
| `src/ctf/decide.nim` → `src/cabinet/decide.nim` | the turn loop, `SeatPolicy`, the two-deadline retry, the inter-batch floor, the budget guard, `repairMissingOrders` (retargeted: a missing field keeps last turn's value, else `bulwark`'s), the `records` queue. It is already a loop over `sim.seatCount()` seats that batches them, so retargeting to 4 seats and skipping out cabinets is a predicate. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/sim_config.nim` | `GameConfig` lifecycle and `config.update`; the cabinet's fields replace the arena's, with `rom.nim` applying the preset between defaults and explicit keys. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; cabinet result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim` | HUD label composition. |
| `src/ctf/broadcast.nim` | `stepEvents` / `BroadcastTracker` / `buildStateJson` — the state-delta → broadcast-event derivation, retargeted to the cabinet's event kinds and state keys (§Viewer). Its **four-team** paths (it already serves ctf's `4ffa`) are what make the scorebug work unchanged. |
| `replay-viewer/config.nims`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/chrome_common.js` | **byte-for-byte**, zero edits (§Viewer). |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome, with a game block appended (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/wasm_replay_smoke.cjs`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix`, `flake.lock`, `config.json` | build, bundle, tuning and forensics wiring. `tools/build_replay_viewer.sh` already carries the ecos `mkdir -p` fix at line 22 and keeps it; only `image_tag` and the `docker cp` source path `/workspace/cabinet/replay-viewer/dist/.` change. |
| `data/font.ttf`, `data/FONT_LICENSE.txt`, `data/arena_floor.png`, `data/darkbg.png`, `data/ascii.png`, `data/atlas/*`, `data/heart_red.png`, `heart_blue.png`, `heart_green.png`, `heart_yellow.png`, `client/art/walls/*`, `client/art/lockerroom/bg.jpg` | real art, kept — the four `heart_<colour>.png` become the lives pips, which is exactly what they already are. Everything CTF-specific (`soldier_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, `crew.png`, `rig_real/`) is deleted. |

**The five named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   the cabinet calls `control.paddleCommand(sim, k)` for all four cabinets and passes the
   command-byte array into `sim.step`. **Player sockets contribute no input**: any input mask
   arriving on a player socket is discarded.
2. **Replay input write.** `writeInputFrameMasks` (the press/release wrapper at
   `src/ctf/server.nim:1088`) is **deleted** — its `repeatedPressedMask` logic (line 1098) is
   button semantics and would corrupt a value byte. The cabinet calls
   `replayWriter.writeInputMaskChange(tickTime(tick), seat, cmd)` directly (the codec's own
   change-only guard does the rest), and `decodeInputMask` (lines 1707, 1991) is replaced by
   `decodePaddle(cmd: uint8): tuple[near, far, grip: int32]` with the `cmd >= 243 → 40` repair.
3. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop
   runs `decide.turn(sim, engine, …)`, which enforces the inter-batch floor, issues the one
   parallel batch over the **alive** seats, applies the deadlines, installs the stances and writes
   the `stance`/`fallback` records — all inside a monotonic `turnBudgetMs` bound.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration forces
   `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.
5. **Shutdown grace.** `/healthz` and `/global` keep answering for a bounded ~20 s after the
   artifacts are written, then the process exits (lantern 0.1.3: the episode runner pings `/global`
   with a 2 s deadline *after* the player pods start, and a short episode can already be gone).

**The two named edits to `replays.nim`:**

1. **`serializeReplaySim`/`deserializeReplaySim` cover the new sim fields** — every cabinet's
   `lives`, `out`, `outTick`, near/far `alongCentre` and `paddleVel`, `heldBall`, its brick bitset,
   `saves`, `chips`, `knockouts`, `concedes`, `catches`, `scoreMicro`; every ball's `state`, `pos`,
   `dir`, `speed`, `lastTouch`, `holdTicks`, `serveTimer`; `rngDraws`, the RNG state, `phase`,
   `targetTick` — because keyframes are how the viewer seeks. The static geometry, the ROM preset
   and `perm` are **excluded** from keyframes (they are already in the config JSON — ctf's own rule
   for static bakes).
2. **`CtfReplayMagic "COWLDCTF"` → `CabinetReplayMagic "COWLDCAB"`**,
   `GameName* = "atari-cabinet"`, `GameVersion* = "1"`, with ctf's prepend-only changelog-comment
   discipline (`GV1 (cabinet rules): four sides, mouths, paddles as guns, three ROM presets`) and
   `tools/ci/check_gameversion.sh` kept as is.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`; `tools/wasm_replay_smoke.cjs`). So:

- Every stored sim field is explicitly `int32` (positions, speeds, counters), `int64` (the score
  accumulators), `uint8` (direction indices, command bytes) or `bool`/`enum`. **No bare `int` in a
  hashed field.**
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with
  an explicit truncating `div` (Nim's `div` truncates toward zero, so the fan's `round`, the
  displacement scaling and the crossing comparisons are all symmetric under negation).
- **No floating point anywhere under `src/cabinet/{sim,arena,rom,trig,sim_types,sim_config,
  sim_state}.nim`.** No `sin`, `cos`, `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`.
  Grep-enforced in CI. Floats stay legal in `control.nim`, `global.nim`, `stances.nim`'s numeric
  parsing and the pixie bakes, because neither the autopilot (recorded, not re-run) nor rendering
  enters `gameHash` — exactly ctf's split.
- Trigonometry is the committed `DirQ64` table (64 entries). **There is no square root anywhere in
  the sim**: every collidable is axis-aligned, so every contact test is an integer
  cross-multiplied comparison.
- Randomness: one seeded stream, every draw through `drawInt` on `rng.next()`'s `uint64` domain,
  `rngDraws` hashed.

### How the replay achieves server ↔ viewer determinism

The mechanism is ctf's, unchanged:

1. The server writes a `COWLDCAB` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `rom`, `perm`, every geometry and physics constant, the resolved
   ROM preset, the roster with real names), then the record stream — joins, leaves, **per-tick
   command-byte change records**, chat records (`register`, `stance`, `fallback`, `budget_guard`,
   `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/cabinet_replay.nim` — which imports the
   **same** `src/cabinet/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + `nimby 2.2.4`
   container in `Dockerfile.replay-viewer`.
3. In the browser, `cabinet_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `cabinet_frame` re-steps the sim from the **recorded command bytes** and compares
   `sim.gameHash()` against the recorded hash **every tick** (`checkReplayHash`). One divergent bit
   is caught at the tick it happens, surfaced as `mismatchTick` in the chrome (`#mmwarn`) and, in
   CI, as a hard failure.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle
   and runs `tools/ci/viewer_smoke.mjs` against the replay `docker-smoke` produced (§Tests), which
   fails if the viewer errors, never draws, freezes, or reports a mismatch tick.

Perf target: 2880 ticks of physics + 11 520 autopilot evaluations + up to 5 760 ball-contact scans
in under 4 s on a CI runner; `tests/test_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

`src/cabinet/server.nim` is ctf's `server.nim` with the five edits above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`) — **both `/client/` routes serve
real pages, registered before any catch-all asset route, and neither opens the player socket**
(lantern 0.1.1: the certifier probes them before starting player pods). Same `COGAME_*` runtime
contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`,
`COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same done-before-artifact-writes
ordering, same entrypoint shape (`src/atari_cabinet.nim`, where seed randomisation happens
**before** `config.update` so every seed-derived draw follows the final seed, and where
`rom.applyPreset` runs inside `config.update` between defaults and explicit keys).

### The player container

`src/atari_cabinet_player.nim` (built to `/bin/atari-cabinet-player`) is
`src/paintball_player.nim` with the baseline names changed. It reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED`, `PLAYER_POLICY_LABEL`, dials with the starter's bounded retry
(240 × 500 ms), and sends **one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"bulwark"|"spinner"|null,"policy":"<free label>"}
```

It re-sends the registration on the starter's `RegistrationResends`/`ResendEveryFrames` schedule
(`src/paintball_player.nim:28-29`; the server's held-registration table,
`src/ctf/server.nim:1730`, is kept — a seat's first registration can arrive before its player index
exists, and dropping it was a real paintball scar). It then sends the Sprite v1 Ready packet
(`0x85`) after each received frame and otherwise only receives. **The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket** — whisky's `receiveMessage` raises on a
close frame and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed `done`
frame (raid 0.1.3 → 0.1.4). A seat that never registers, or registers with neither field, is
`scripted: "bulwark"`.

Player container resources in the manifest: `requests {cpu: 100m, memory: 64Mi}`,
`limits {cpu: "1"}` — the bundled-player `limits.cpu` minimum is `"1"` and anything lower is a 400
at upload (pistonball 0.1.1, 2026-08-26).

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per
tick, built by `buildSpriteProtocolPlayerUpdates`. **The cabinet is a CRT and the board is
perfect-information**: the frame carries the whole arena, all four mouths (open or welded), all
paddles, every brick, every ball with its trail, and every cabinet's lives. Fog of war, vision
cones and the first-person raycast are **deleted**, not disabled — a decision, with its reason:
hiding part of a 100 × 100 arcade screen from the player sitting at it would be arbitrary, would
make the deflection fan unlearnable, and would fight the idea's own framing ("raw frames"). Board
labels carry only the colour aliases; `showPlayerLabels` is forced false on the player stream.

### The per-seat view given to the LLM

Numbers rounded to 2 decimals, in **cabinet coordinates** (0..100, origin bottom-left, y up) with
`along`/`depth` in this seat's own side-local frame, and degrees counter-clockwise from east. This
object is the tail of the LLM user message; the scripted baselines are pure functions of the
identical object.

```json
{"turn": 11, "of": 24,
 "clock": {"tick": 1320, "of": 2880, "left_s": 65.0},
 "rom": "warlords",
 "you": {"alias": "GREEN", "side": "NORTH", "lives": 2, "out": false,
         "paddle": {"along": -6.40, "vel": 0.80, "half": 7.00, "depth": 14.00,
                    "travel_half": 43.00},
         "far_paddle": null,
         "holding": null,
         "mouth": {"half": 18.00, "open": true},
         "bricks": {"left": 5, "of": 9,
                    "cols": [false, true, true, false, true, false, true, true, false]},
         "score": 41.750},
 "balls": [{"id": "B1", "pos": [62.10, 71.44], "vel": [0.61, -0.42], "speed": 0.74,
            "deg": 325.4, "last_touch": "BLUE", "held_by": null,
            "arrive_at": "GREEN", "arrive_in_ticks": 31, "arrive_along": 3.20},
           {"id": "B2", "pos": [18.02, 22.75], "vel": [-0.30, 0.55], "speed": 0.63,
            "deg": 118.6, "last_touch": "RED", "held_by": null,
            "arrive_at": "YELLOW", "arrive_in_ticks": 44, "arrive_along": null}],
 "rivals": [{"alias": "RED", "side": "SOUTH", "lives": 3, "out": false,
             "bricks_left": 8, "paddle_along": 11.20, "score": 58.500},
            {"alias": "BLUE", "side": "EAST", "lives": 1, "out": false,
             "bricks_left": 2, "paddle_along": -20.40, "score": 33.250},
            {"alias": "YELLOW", "side": "WEST", "lives": 0, "out": true,
             "bricks_left": 0, "paddle_along": null, "score": 9.750}],
 "neighbours": {"plus_along": "YELLOW", "minus_along": "BLUE"},
 "rules": {"starting_lives": 3, "ball_count": 2, "brick_rows": 1,
           "catch_enabled": true, "far_paddle": false,
           "points": {"per_life_kept": 20.0, "crown": 15.0, "knockout": 2.0,
                      "chip": 0.5, "save": 0.25},
           "note": "the last cabinet with lives standing wins; nothing is ever subtracted"},
 "your_last_stance": {"stance": "aim", "target_ball": "B1", "aim_at": "BLUE",
                      "post": 0.0, "lead_ticks": 12, "aggression": 0.8}}
```

`arrive_along` is `null` when that ball will not reach **this** seat's line inside the prediction
bound; `arrive_at` names whichever cabinet's line it reaches first (`null` if none inside the
bound). `balls` always has exactly `ballCount` entries — a ball mid-serve carries
`"state": "serving"` with `pos` at the centre and `arrive_*` null. `rivals` always has exactly
three entries. `you.far_paddle` is an object only when the ROM has `farPaddle`.

The `arrive_*` triple is deliberate decision support: it is computed by **the same walk the
autopilot uses**, so a policy is never guessing at a quantity the engine already knows (the escrow
0.1.3 lesson — precompute the choice set in the observation with the same predicate the executor
applies).

**Hidden from every seat, with no exception:**

- Which entrant holds any other seat; any other seat's stance, `note`, `say`, prompt, latency,
  policy label, `policyKind` or fallback state.
- `perm`, `config.seed`, the RNG state, `rngDraws`, and every **future** serve direction.
- Real player names anywhere (board labels carry only `RED`/`BLUE`/`GREEN`/`YELLOW`;
  `showPlayerLabels` is forced false on the player stream).
- The variant name beyond the `rom` string, and any host/wall-clock fact (elapsed wall seconds,
  turn budgets, whether another seat fell back).
- Future ticks.

Everything **on the board** is visible: all ball positions/velocities/speeds/`last_touch`, all
paddle positions, every brick bit, every cabinet's lives, out-flag and live score. That is the
decision, stated once so there is no ambiguity: **the physics is public, the players are not.**
`tests/test_locality.nim` asserts both halves against the composed LLM user message over
randomised states (§Tests 8).

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "BLUE is on 1 life and its wall is down to 2; take the free shot",
 "stance": "aim", "target_ball": "B1", "aim_at": "BLUE",
 "post": 0.0, "lead_ticks": 12, "aggression": 0.8,
 "say": "BLUE first"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `stance` | string | closed enum `guard, aim, camp, catch, chase` | unrecognised / missing → last turn's `stance`, else `guard`. `catch` in a ROM without `catchEnabled` → `guard`. |
| `target_ball` | string | **≤ 4 runes**, `B1`…`B<ballCount>` or `any`, case-insensitive | an id outside the set, or a ball not currently live → `any` (the autopilot then takes the soonest-arriving ball) |
| `aim_at` | string | **≤ 8 runes**, `RED`/`BLUE`/`GREEN`/`YELLOW` or `none`; must not be my own alias and must not be an **out** cabinet | unrecognised, missing, self, or out → `none` (the autopilot then behaves as `guard`) |
| `post` | number | finite, clamped `[-43.0, 43.0]`, quantised to µu | non-finite / missing → last turn's `post`, else `0.0` |
| `lead_ticks` | integer | finite, clamped `[0, 48]`, rounded | non-finite / missing → `12` |
| `aggression` | number | finite, clamped `[0.0, 1.0]`, quantised to `0..255` | non-finite / missing → `0.8` |
| `say` | string | **≤ 48 runes** | truncated to 48 runes, then ctf's printable-ASCII shout sanitiser (which also strips a leading `{`, since the replay chat stream distinguishes control records by it) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**
(`MaxPolicyLabelRunes`), any recorded error text (`fallback.detail`) **≤ 200 runes**
(`MaxFallbackDetailRunes`), and the whole serialized `stance` record **≤ 600 runes**, asserted in
`tests/test_replay.nim`. `register.prompt` is capped at **≤ 4000 runes** at the transport
(over-long is truncated, never rejected) and is **never** written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — in Nim, `runeLen` /
`runeSubStr` (ctf's `directives.nim` rune discipline, kept verbatim as `stances.nim`). Slicing a
`string` by byte index on any path to the replay is forbidden: a byte-truncated multi-byte
character renders in a browser and then fails a strict UTF-8 parser. §Tests 6 pins it with a 4-byte
emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose (`extractJsonObject`); accept numeric strings; accept integer percentages for
`aggression` and divide by 100 when the value exceeds 1; accept `stance`, `target_ball` and
`aim_at` case-insensitively and with surrounding whitespace; accept `aim_at` given as `"the red
cabinet"` or `"red"`; accept `target_ball` given as `"ball 1"` or `"1"`; accept `stance` synonyms
`defend`→`guard`, `shoot`/`attack`→`aim`, `hold`/`sit`→`camp`, `grab`→`catch`, `rush`→`chase`;
accept `post` given in percent-of-side and rescale when `|post| > 43`. Only when no object with at
least one usable field can be recovered do the retry and then the fallback fire.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, cabinet keys) to `COGAME_RESULTS_URI`. It
must equal the manifest's `results_schema` key-for-key — that schema is
`additionalProperties: false` and the certifier rejects any unknown field. Adding or removing a key
here means editing `coworld_manifest_template.json` in the same commit. **22 keys:**

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
 "aliases": ["GREEN", "RED", "YELLOW", "BLUE"],
 "cabinets": [2, 0, 3, 1],
 "policyKinds": ["llm", "llm", "scripted", "scripted"],
 "scores": [95.75, 65.0, 17.0, 3.5],
 "win": [true, false, false, false],
 "placements": [1, 2, 3, 4],
 "rom": "warlords",
 "startingLives": 3,
 "livesLeft": [2, 2, 0, 0],
 "concedes": [1, 1, 3, 3],
 "knockouts": [6, 3, 2, 0],
 "chips": [22, 9, 6, 1],
 "saves": [71, 58, 40, 12],
 "catches": [4, 1, 0, 0],
 "bricksLeft": [5, 3, 0, 0],
 "llmTurns": [24, 23, 0, 0],
 "fallbackTurns": [0, 1, 0, 0],
 "finalTick": 2604,
 "reason": "complete",
 "endRule": "last_standing",
 "seed": 5140913}
```

`names` are the **real policy names** (spectator side). `aliases` are the in-game names. Every
per-seat array is in **seat order** and has exactly 4 entries. `cabinets` is `perm`.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDCAB`** format: the static wasm viewer parses exactly
this format, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and the whole seek/keyframe machinery. Consequences handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design ("set 0 for a binary replay format").
- The repo keeps **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): given a
  `.replay` path it prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"atari-cabinet/v1","gameVersion":"1","rom":"warlords","seed":…,"names":[…],
  "aliases":[…],"cabinets":[…],"policyKinds":[…],"tickCount":…,"stances":[…],"fallbacks":N,
  "results":{…}}`. It brace-matches the config JSON from the first `{` (the technique ctf's
  `AGENTS.md` documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .rom, .results.reason, .results.endRule, .results.placements' /tmp/ep.json
  jq -r '[.stances[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  jq -r '[.stances[]|select(.source=="llm")|.aim_at]|unique' /tmp/ep.json
  ```
  Require `protocol == "atari-cabinet/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.saves` summing above 0, and the champion seats' stances
  `source == "llm"` with **varying** `stance`/`aim_at` values — not all fallbacks, and not a
  constant stance.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDCAB`, format version, `gameName` `atari-cabinet`, `gameVersion` `1` |
| config JSON | `seed`, `rom`, the **fully resolved** ROM preset (every key of §The ROM preset table), `perm`, `num_agents`, `maxTicks`, `turnTicks`, the whole geometry table (arena side, mouth half-width, paddle depths/halves/travel/step, brick lattice, ball half-size, speed ramp, serve delay, hold cap, the 13-angle fan), the reward constants, `players[].name` (**real names**), `slots[].alias`, `fastMode` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| inputs | **the action log**: one command byte per seat per tick, written on change only |
| chats | `register` / `stance` / `fallback` / `budget_guard` / `result` records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 2880 hashes (8 B) + ≤ 11 520 input-change records (≈ 4 B) + ≤ 96 stance records (≈ 240 B) +
a ≈ 6 KB config ≈ **95 KB** worst case, typically under 60 KB.

### Record and event vocabulary

**A. Replay chat records** (written by the server; re-applied at playback in order):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `cabinet`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `stance` | `turn`, `seat`, `alias`, `cabinet`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `stance`, `target_ball`, `aim_at`, `post`, `lead_ticks`, `aggression`, `say` |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at game over (ctf's `resultRecord`, kept — it is what makes the bytes self-sufficient) |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these
from state deltas during playback, so they cost no replay bytes and are identical live and in
replay: `phase`, `serve` (`{ball, dir}`), `save` (`{cabinet, ball, j, speed}`), `chip`
(`{cabinet, col, by}`), `breach` (`{cabinet, col}` — a column is now empty in every row),
`wall_down` (`{cabinet}` — every brick gone), `catch` (`{cabinet, ball}`), `release`
(`{cabinet, ball, aim_at}`), `concede` (`{cabinet, ball, by, livesLeft}`), `eliminated`
(`{cabinet, placement, tick}`), `near_miss` (a ball crossed a paddle's depth line within 1.20 cu of
the bar's end without contact — the drama the game is made of), `turn_end`, `last_standing`,
`gameover`, `say` (a `stance` record's non-empty `say`).
**Beats** (scrubber markers): `concede`, `breach`, `eliminated`, `last_standing`, `over`. `save`,
`chip`, `serve`, `catch`, `release`, `near_miss` and `say` are **not** beats — they fire dozens to
hundreds of times and would bury the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Serve, Save, Chip, Breach, WallDown, Catch, Release, Concede,
Eliminated, NearMiss, Stance, PhaseChange, LastStanding`, and the mandatory trailing summary row
(`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's
script, kept (with `image_tag` and the `docker cp` source path
`/workspace/cabinet/replay-viewer/dist/.` changed, and the ecos `mkdir -p` already present at line
22). `coworld build` invokes it with the absolute bundle directory; the script already refuses any
output path that is not a `static-replay-viewer` directory inside the repo, and it must stay
committed **executable** (`coworld build` hard-requires `os.X_OK`).

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter.** Splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently with every file present and 200
(cogame-lantern, 2026-08-23), so there is no mixture anywhere in this table:

| File | Source |
|---|---|
| `replay-viewer/config.nims` | **`coworld-ctf`**'s `replay-viewer/config.nims`, verbatim except `ctf_replay.js` → `cabinet_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_cabinet_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the flags stay exactly as ctf links them, including `-s ENVIRONMENT=web,worker,node`, `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file data@data`, `--define:useMalloc`, `--mm:arc`, `--exceptions:goto`. |
| the wasm entry `.nim` | **`coworld-ctf`**'s `replay-viewer/ctf_replay.nim`, forked to `replay-viewer/cabinet_replay.nim` (stage-note buffer, `ABORTING_MALLOC` diagnostics, the `predictedViewerRenderBytes`/`WasmViewerBudgetBytes` capacity preflight, `emscripten_exit_with_live_runtime` lifetime — all kept), exporting `cabinet_load_replay`, `cabinet_frame`, `cabinet_input`, `cabinet_packet_ptr/len`, `cabinet_mismatch_tick`, `cabinet_error_ptr/len`, `cabinet_stage_ptr/len`. |
| `static_replay*.js` | **`coworld-ctf`**'s `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts('./wire_constants.js', './broadcast_core.js', './cabinet_replay.js')` form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Only two names change: the Worker name `ctf-static-replay` → `cabinet-static-replay`, and `window.CtfStaticReplay` → `window.CabinetStaticReplay`. |
| `index.html` | built from **`coworld-ctf`**'s `client/replay_broadcast.html` (see below). |

`static_replay.js` **already sets both machine-readable markers and they are kept unchanged**: it
sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` **on its first drawn
frame** (the Worker's `loaded` message, `replay-viewer/static_replay.js:161`), and `showFailure()`
sets `document.documentElement.setAttribute('data-replay-error', <message>)` **on failure**
(line 20), plus `data-replay-mismatch-tick` on a hash mismatch (line 32). Those attributes are
what `tools/ci/viewer_smoke.mjs` waits on. The `coworld-replay` bridge `ready` post is fired **from
a callback that runs after `data-replay-loaded="true"` has been set**, never on rAF timing at the
call site (chorus, 2026-08-24: the softmax.com embed otherwise samples an unpainted shell).

### Chrome provenance: what is copied, what is appended, what is removed

- **`client/chrome_common.js` is copied byte-for-byte from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, flag story) stay in the file and are inert because the
  corresponding state fields are simply absent from the cabinet's stream. Every cabinet-specific
  readout lives in the appended game block, and the state JSON **keeps ctf's key names**
  (`t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events, lead,
  beats, lulls, over, hold` — `src/ctf/broadcast.nim:861-975`) so chrome_common's plate rendering,
  feed rows, beat markers, momentum curve, spoilers switch and endcard run unmodified against
  cabinet values. **The `teams` keys are exactly `red`, `blue`, `green`, `yellow`**, because
  `chrome_common.js:55` pins `TEAM_ORDER = ['red','blue','green','yellow']` and orders index 0/2
  to the left of the clock and 1/3 to the right — so the cabinet's four plates come out
  RED + GREEN | clock | BLUE + YELLOW with no edit at all, and the momentum graph takes its
  four-team branch (`chrome_common.js:793-806`). A from-scratch page that reuses the starter's ids
  is explicitly **not** what happens here (cogame-gridlock, 2026-08-23). A test pins the file's
  sha256 against the starter's copy.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one
  `<style>` and one `<script>` block at the end of the file, injecting the cabinet's readouts into
  the existing containers. Nothing above them is rewritten; the CSS variables, `relayout()`, the
  transport, the endcard, the locker-room loader and the `?embed=1` mode are the starter's. The
  game block's own function names are prefixed `cab` (`cabMarkBeat`, `cabPushFeed`, …) so nothing
  shadows chrome_common's hoisted alias block (`var markBeat = C.markBeat` — the tandem 2026-08-23
  scar), and a test asserts no game-block top-level name collides with the alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and
  its children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; and `#povBadge`.
  **Zoom decision: the arena is fixed and the board (1000 × 1000 px) always fits the frame, so
  `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the rule that it exists only
  for boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap code stays in the file,
  verbatim, simply never driven.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned
  "Four cabinets, one screen, and your paddle is a gun", art from
  `client/art/lockerroom/bg.jpg`), `#lk-art`, `#lk-bg`, `#lk-cap`, `#lk-sprites`, `#chrome`,
  `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#mmwarn`,
  `#bannerlane`, `#killfeed`, `#transport` with every button (`#btn-play`, `#btn-back`, `#btn-fwd`,
  `#btn-end`, `#btn-restart`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`), `#speedchips`, `#scrub`,
  `#scrub-fill`, `#scrub-head`, `#scrub-win`, `#momentum`, `#lulls`, `#tick-clock`, `#ffwd-chip`,
  `#ffwd-mini`, `#win-chip`, `#endcard` with `#ec-headline`, `#ec-how`, `#ec-wincond`, `#ec-teams`,
  `#ec-replay`, and `#status`.

### The exact state JSON the viewer reads

`buildStateJson` (ctf's, retargeted) emits this object once per frame. Keys above the fold are
ctf's and are consumed by the byte-identical `chrome_common.js`; everything cabinet-specific is
under `cab` and `stances`, consumed only by the appended game block.

```json
{"t": 1320, "mt": 2880, "ph": "playing", "lob": 0, "pl": true, "sp": 1, "mx": 2880,
 "st": 0, "lp": false, "sk": false, "ff": false, "en": true, "mm": -1, "bs": 2, "pov": -1,
 "teams": {"red":    {"score": 58.50, "lives": 3, "startingLives": 3, "bricks": 8,
                      "knockouts": 3, "chips": 9,  "saves": 58, "out": false, "policies": 1},
           "blue":   {"score": 33.25, "lives": 1, "startingLives": 3, "bricks": 2,
                      "knockouts": 2, "chips": 6,  "saves": 40, "out": false, "policies": 1},
           "green":  {"score": 41.75, "lives": 2, "startingLives": 3, "bricks": 5,
                      "knockouts": 6, "chips": 22, "saves": 71, "out": false, "policies": 1},
           "yellow": {"score":  9.75, "lives": 0, "startingLives": 3, "bricks": 0,
                      "knockouts": 0, "chips": 1,  "saves": 12, "out": true,  "policies": 1}},
 "roster": [{"s": 0, "name": "daveey", "team": "green", "alias": "GREEN", "cabinet": 2,
             "kind": "llm", "lives": 2, "knockouts": 6, "saves": 71, "chips": 22},
            "… 4 rows, seat order …"],
 "events": [{"k": "concede", "t": 1284, "cabinet": 3, "by": 2, "ball": "B1",
             "livesLeft": 0}, "…"],
 "turn": 11, "turns": 24, "turnTicks": 120,
 "cab": {"rom": "warlords",
         "arena": {"side": 100.0, "goalHalf": 18.0, "paddleDepth": 14.0,
                   "farPaddleDepth": null, "paddleHalf": 7.0, "brickRows": 1,
                   "bricksPerRow": 9, "catchEnabled": true},
         "cabinets": [{"k": 0, "team": "red", "alias": "RED", "side": "SOUTH",
                       "lives": 3, "out": false, "paddle": -11.20, "paddleVel": 0.4,
                       "far": null, "held": null, "mouthOpen": true,
                       "bricks": [true,true,false,true,true,true,true,true,true],
                       "stance": "guard", "aimAt": null},
                      "… 4, cabinet order …"],
         "balls": [{"id": "B1", "p": [62.10, 71.44], "v": [0.61, -0.42], "speed": 0.74,
                    "dir": 58, "state": "live", "lastTouch": 1, "heldBy": null,
                    "trail": [[63.5, 72.5], [64.9, 73.5]]},
                   {"id": "B2", "p": [18.02, 22.75], "v": [-0.30, 0.55], "speed": 0.63,
                    "dir": 21, "state": "live", "lastTouch": 0, "heldBy": null,
                    "trail": [[18.6, 21.7], [19.2, 20.6]]}],
         "bubbles": [{"cabinet": 2, "say": "BLUE first", "until": 1380}]},
 "stances": [{"turn": 11, "seat": 0, "alias": "GREEN", "cabinet": 2, "source": "llm",
              "stance": "aim", "targetBall": "B1", "aimAt": "BLUE", "post": 0.0,
              "note": "…", "say": "BLUE first"}, "… 4 …"],
 "lead": {"teams": ["red", "blue", "green", "yellow"],
          "pts": [[0, 0, 0, 0, 0], [120, 4.25, 3.0, 6.5, 2.0], "… change-points of score …"]},
 "beats": [{"t": 432, "k": "concede"}, {"t": 968, "k": "breach"},
           {"t": 1284, "k": "eliminated"}, "…"],
 "lulls": [[1512, 1670]],
 "over": {"winner": "green", "draw": false, "timeLimit": false,
          "endRule": "last_standing", "reason": "complete", "ticks": 2604,
          "rom": "warlords",
          "teams": {"green": {"placement": 1, "score": 95.75}, "…": {}}},
 "hold": 3}
```

There are exactly **four** `teams` keys, and they are the four colour names chrome_common already
knows. `roster` carries the **real policy names** and is spectator-side only.

### Readouts

1. **Run bug** (top, always on). Four plates — `#plates-l` carries RED and GREEN, `#plates-r`
   carries BLUE and YELLOW (chrome_common's own ordering). Each plate: the colour alias, the live
   **score** as its headline number, **lives as heart pips** baked from `data/heart_<colour>.png`
   (spent pips greyed), and a thin **brick-integrity bar** (9 segments, one per column). An
   eliminated cabinet's plate dims and gains a struck-through `OUT · 3rd` chip. Centre column
   (`#clock`): `M:SS` from `tick div 24` with `of 2:00` and **the ROM name — `WARLORDS` —** in
   `#clock-caption`. That caption is the "per-ROM scoreboard" the idea asks for.
2. **The board** (the headline): a square CRT — dark phosphor plate baked from `data/darkbg.png`
   and `data/arena_floor.png`, a bright scanline overlay and a corner vignette, the four walls
   baked from `client/art/walls/wall_h.jpg`/`wall_v.jpg` in each cabinet's tint, each **mouth** a
   dark gap with a glowing lip (welded shut with an X-hatched plate when the cabinet is out),
   **bricks** as chunky tinted blocks that flash white and shatter into four sparks when chipped,
   **paddles** as thick tinted bars with a bright leading edge whose length reads the drive level
   (that is what makes the joystick visible), and **balls** as small bright squares with a 6-frame
   motion trail whose brightness reads `speed`.
3. **Aim rays — where the LLM becomes visible.** From `stances`, each cabinet with
   `stance ∈ {aim, chase, catch}` and a live `aimAt` draws a thin dashed ray from its bar toward
   that rival's mouth, in the *shooter's* colour, plus a small stance chip beside the bar
   (`GUARD` / `AIM→BLUE` / `CAMP` / `CATCH` / `CHASE`). Four rays at most, redrawn each turn.
4. **Contact FX**: a white flash and a `+0.25` pip on every save; a `+0.5` on every chip; on a
   **concede** a full-board magenta flash, a short screen shake, `−1 LIFE` popping off the
   conceding mouth and `+2` popping off the shooter's bar; on an **elimination** the mouth welds
   shut with a slam and a `4th` / `3rd` / `2nd` ribbon.
5. **Held-ball indicator**: a pulsing ring on a gripped ball with a shrinking 2 s timer arc, so
   `catch` reads as a deliberate act rather than a stuck ball.
6. **Speech bubbles**: at most **three** at a time — the three cabinets with the most recent
   non-empty `say` — drawn for 2.5 s in a **reserved band across the top of the board**
   (`Y ∈ [92.0, 99.0] cu`), never positioned relative to a paddle. The band is sized from
   `MaxSayRunes = 48` measured in `data/font.ttf` at the current `--hudscale`, which is exactly the
   reservation the cogchemists 2026-08-24 scar demands; `viewer_smoke.mjs --strict-text-bounds`
   requires `canvas_text.never_inside == 0` for this fixed arena.
7. **Match feed** (`#killfeed`, renamed in copy only): plain language — "GREEN scores on YELLOW —
   YELLOW has 1 life left", "BLUE breaks GREEN's wall — 5 bricks left", "RED's wall is DOWN",
   "YELLOW is OUT — 4th", "GREEN catches B1 and holds…", "SO CLOSE — B2 grazed RED's bar",
   "TURN 12 — 4 new stances". Stance `note`/`say` strings appear here; this is where a spectator
   sees the LLM playing.
8. **Momentum graph** (`#momentum`): ctf's `lead` series in its **four-team** branch — one
   colour-coded score curve per cabinet over the whole timeline, drawn from the first frame, with
   concedes marked.
9. **Transport and integrity**: ctf's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls,
   spoilers, speeds `[1,2,3,4,8,16]`, scrubber with beat markers, tick readout, the end-hold
   countdown and `#mmwarn` — all verbatim.
10. **Endcard**: "GREEN LAST STANDING · WARLORDS · 95.75" (or "FULL TIME · GREEN ON TOP ·
    WARLORDS"), and chrome_common's `ec-*` table listing all four seats by **real policy name**
    with their colour, side, placement, lives left, knockouts, chips, saves, catches and
    LLM/fallback turn counts, sorted by placement.

### Transport rules

- `relayout()` is kept verbatim (`client/replay_broadcast.html`, the `--hudscale` / `--topband` /
  `--band` fixed-point iteration): it sets `--hudscale`, `--topband` and **`--band`** on `:root`,
  so the board is letterboxed between the scorebug band and the transport band.
- **No overlay sits in the transport band.** Every cabinet overlay the game block adds — the stance
  chips' legend, the ROM chip, the score-curve caption — is positioned inside `#chrome` with
  `bottom: calc(var(--band) + N * var(--u))`, never over it.
- The **endcard stops at `var(--band)`** (the starter's `#endcard { bottom: var(--band) }` rule at
  line 1047 is kept) and is **dismissed by every seek** (the starter's behaviour, kept).
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">`** elements — the
  game block upgrades chrome_common's markers to buttons with `aria-label` and `title` (e.g.
  "Goal — 53.5 s — GREEN scores on YELLOW") and a click seeks to that tick. **CSS exists for every
  kind emitted**: `.beat-marker.concede`, `.beat-marker.breach`, `.beat-marker.eliminated`,
  `.beat-marker.last_standing`, `.beat-marker.over` — one rule per kind, asserted by
  `tests/test_viewer.nim`.

### Art

Real, and baked from what the repo already ships. The CRT plate, scanlines, bloom, vignette, the
four tinted walls, mouth lips, brick blocks, paddle bars, ball sprites and trails are baked once at
startup with **pixie** (already a dependency, already how ctf bakes its board), using ctf's shipped
`data/darkbg.png` and `data/arena_floor.png` as the screen plate, `client/art/walls/wall_h.jpg`
/`wall_v.jpg` as the wall plates, `data/heart_red.png`/`heart_blue.png`/`heart_green.png`
/`heart_yellow.png` as the lives pips, and `data/font.ttf` for every label. The locker-room card
reuses `client/art/lockerroom/bg.jpg`. No solid-colour placeholders, no TODO assets, no downloaded
art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`; kept
verbatim. At that width each plate shows the colour alias, the score and the lives pips; the ROM
name stays in `#clock-caption`; the four policy names live in the endcard and in each roster row's
`title`. Three further rules ship in the game block: `.plate-name { flex: 1 1 auto; min-width:
3.2em; overflow: hidden; text-overflow: ellipsis }` (so the plate captions never collapse to "…"),
and under `.tiny` the brick-integrity bars collapse to a single numeral, the stance chips and the
aim-ray legend are hidden, and bubble text is suppressed — while the balls, paddles, bricks, mouths
and lives pips all stay. The board aspect is 1:1, which the chrome derives from the stream.
`tests/test_viewer.nim` asserts all three rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-atari-cabinet`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `atari-cabinet`; `game.name` is also
  `atari-cabinet`, so the secret namespace
  `secret://coworld/atari-cabinet/anthropic_api_key` matches `game.name` **exactly**
  (cooperative-hunting, 2026-08-25: the namespace must equal `game.name`, not a
  differently-punctuated slug).
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{ATARI_CABINET_IMAGE}}` (placeholders are derived from **compose service names** by uppercasing
  and replacing `-` with `_`; `{{GAME_IMAGE}}` is not a thing outside ctf's own two-service file —
  lantern 0.1.0). Phase 20's manifest generator derives it from `compose.yaml` and
  `tests/test_manifest.nim` asserts the derivation:

  ```yaml
  services:
    atari-cabinet:
      image: coworld-atari-cabinet:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure (nimby 0.1.26,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's
  package tree), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:atari-cabinet
  src/atari_cabinet.nim` → `/bin/atari-cabinet`, and the same for
  `src/atari_cabinet_player.nim` → `/bin/atari-cabinet-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/atari-cabinet"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby with its
  sha256 check, the marker splices, the `test -f`/`grep -q` assertion block) with the asset list
  swapped and the workspace path `/workspace/cabinet`.
- **`coworld_manifest_template.json`** (written against the `coworld` 0.1.42 upload contract —
  validate offline with the CLI's `validate_upload_manifest` and `_load_template_manifest` before
  dispatching):
  - top-level `$schema`, `episode_timeout_minutes: 20`, and top-level `tags` ≥ 3:
    `["retro","arcade","free-for-all","real-time","llm"]`. **`game.tags` does not exist** — the
    validator forbids it and requires `game.description` (pistonball 0.1.0, 2026-08-26).
  - `game.name` `atari-cabinet`; `game.description` (one sentence: "Four arcade cabinets ring a
    square CRT, each defending a gap in its own wall with a paddle that is also a gun; the last
    cabinet with lives standing wins, and the ROM rotates."); `game.owner`; `game.runnable`
    `{"type":"game","image":"{{ATARI_CABINET_IMAGE}}","run":["/bin/atari-cabinet"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/atari-cabinet/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-atari-cabinet/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}` (nested under `game`, not
    top-level; no top-level `version`, no `game.display_name`).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`; **every array property carries `minItems`/`maxItems`** (tandem 0.1.0
    scar): `tokens` (1..4), `players` (1..4), `slots` (0..4), plus `closedRoster`, `seed`,
    **`num_agents`** (1..4), `minPlayers`, `maxTicks` (default 2880), `maxGames` (default 1),
    `turnTicks` (default 120), `turnBudgetMs` (default 16000), `attempt1Ms` (default 9000),
    `retryMs` (default 5000), `turnSpacingMs` (default 12000), `wallClockBudgetSeconds`
    (default 660), `lobbyJoinTimeoutTicks` (default 2880), `startWaitTicks`, `gameOverTicks`,
    `fastMode` (default true), `showPlayerLabels`, `model`, `maxOutputTokens` (default 900), and
    the ROM keys: `rom` (enum `["warlords","quadrapong","foozpong"]`, default `warlords`),
    `startingLives` (1..12), `ballCount` (1..3), `brickRows` (0..3), `catchEnabled`, `farPaddle`,
    `goalHalfCu` (8..30), `paddleHalfCu` (3..12), `farPaddleHalfCu` (3..12), `ballSpeed0Milli`
    (300..900), `ballSpeedStepMilli` (0..120), `ballSpeedMaxMilli` (500..1600), `holdTicksMax`
    (0..96), `serveDelayTicks` (0..120). The CLI validates every variant and the cert fixture
    against this schema (injecting `tokens`), so every key either appears here or is not settable —
    and `tests/test_manifest.nim` asserts it covers every field `sim_config.update` reads.
  - `game.results_schema`: exactly the 22 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","placements","rom","reason","endRule"]`, `reason` enum
    `["complete","deadline","fault"]`, `endRule` enum
    `["last_standing","full_time","wall_clock","sim_fault","host_error"]`, `rom` enum
    `["warlords","quadrapong","foozpong"]`, and every per-seat array
    `minItems: 4, maxItems: 4`.
  - `game.protocols`: **both `player` and `global`**, each `{"type":"text","value":"…"}` (objects,
    not bare strings — garble v0.1.0). `player` documents the registration chat frame, the
    per-tick Sprite v1 frames, the fact that seats send **no** inputs, the board-view JSON and the
    stance reply schema with its caps. `global` documents the `/global` spectator snapshot, the
    state JSON above, the `COWLDCAB` replay layout (config JSON, command-byte log, chat records,
    hash chain) and the static replay bundle.
  - `game.docs`: `readme` = `{"type":"text","value":"<the README body inlined>"}` and `pages` =
    three entries — `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/
    RULES.md inlined: every number in §The game plus the ROM preset table>"}}`,
    `{"id":"protocol.md","title":"Wire protocol",…}`,
    `{"id":"stances.md","title":"Writing a cabinet stance",…}`. A manifest test asserts all four
    values are non-empty text.
  - `player[0]` (the only top-level bundled player entry, with id/type/name/description) =
    `{"id":"baseline","type":"player","name":"Cabinet Bulwark Baseline",
    "description":"Scripted arcade paddle: intercept the soonest ball, aim returns at the weakest
    rival, camp the middle when nothing is inbound. No LLM.",
    "image":"{{ATARI_CABINET_IMAGE}}","run":["/bin/atari-cabinet-player"],
    "env":{"PLAYER_SCRIPTED":"bulwark"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}`. It occupies
    **all four** certification slots — every declared player entry must occupy at least one slot or
    cert fails `players_missing` (raid 0.1.2 → 0.1.3), and `limits.cpu` below `"1"` is a 400 at
    upload (pistonball 0.1.1).
  - **Variants — one per ROM, `num_agents` is 4 in all three, and `description` is required on
    each:**

    | id | name | description | **`num_agents`** | `players`/`slots` | `minPlayers` | `rom` | `startingLives` | `ballCount` | `brickRows` | `catchEnabled` | `farPaddle` | `goalHalfCu` | `paddleHalfCu` | `ballSpeed0Milli` | `maxTicks` | turns | `turnTicks` | `turnSpacingMs` | `turnBudgetMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
    | `warlords` | ROM 1 — Warlords (4 castles) | Four brick castles, two balls, catch-and-throw enabled, three lives each. Last castle standing. | **4** | 4 | 4 | `warlords` | 3 | 2 | 1 | true | false | 18 | 7 | 550 | 2880 | 24 | 120 | 12000 | 16000 | 660 |
    | `quadrapong` | ROM 2 — Quadrapong (four goals) | No bricks, no catching, wide mouths, a faster ball and five lives. Pure four-way pong. | **4** | 4 | 4 | `quadrapong` | 5 | 2 | 0 | false | false | 22 | 6 | 650 | 2880 | 24 | 120 | 12000 | 16000 | 660 |
    | `foozpong` | ROM 3 — Foozpong (two rows) | Every cabinet gets a second paddle row 34 units out, like a foosball table. No bricks, three lives. | **4** | 4 | 4 | `foozpong` | 3 | 2 | 0 | false | true | 18 | 6 | 600 | 2880 | 24 | 120 | 12000 | 16000 | 660 |

    All three seat four players, `slots: [{"alias":"RED"}, {"alias":"BLUE"}, {"alias":"GREEN"},
    {"alias":"YELLOW"}]` (the alias a **slot** carries is cosmetic — the alias a seat actually
    plays under is `perm`-dealt at `t = 0`), `fastMode: true`, `maxGames: 1`,
    `lobbyJoinTimeoutTicks: 2880`, `attempt1Ms: 9000`, `retryMs: 5000`. **A variant changes only
    the ROM preset — never the seat count, never the clock, never the decision cadence, never the
    wall-clock budget**, which is what makes one budget arithmetic (§Decisions) and one score scale
    (§Scoring) correct for all three. Every variant's `game_config` is constructed and stepped by
    `tests/test_manifest.nim` and `tests/test_rom.nim`, not just the fixture (collab-cooking 0.1.1,
    2026-08-25).
  - **Certification fixture — `num_agents` is 4 here too:** `certification.players` = four
    `{"player_id":"baseline"}` entries; `certification.game_config` =
    `{"players":[{"name":"P1"}, …4…], "slots":[{"alias":"RED"}, {"alias":"BLUE"},
    {"alias":"GREEN"}, {"alias":"YELLOW"}], "num_agents": 4, "minPlayers": 4, "seed": 5140913,
    "rom": "warlords", "startingLives": 9, "maxTicks": 1440, "maxGames": 1, "turnTicks": 120,
    "turnBudgetMs": 16000, "turnSpacingMs": 0, "wallClockBudgetSeconds": 180,
    "lobbyJoinTimeoutTicks": 720, "fastMode": true}` — 12 turns, every seat scripted, no LLM client
    (no credentials offline, so the client disables itself and every turn falls back instantly).
    `startingLives: 9` overrides the `warlords` preset's 3 **precisely so the fixture cannot end
    early** and the replay length is deterministic — and it exercises the
    `defaults → preset → explicit` order that `tests/test_rom.nim` pins. Wall cost ≈ 10 s connect +
    ~1 s of physics + the ~20 s shutdown grace ≈ 35 s. At 1440 ticks the fixture replay is
    **60.0 s of playback**, comfortably longer than the viewer smoke's 12 s soak (ecos, 2026-08-23:
    a replay shorter than the soak reads as "frozen"). Because 35 s is close to
    `coworld certify`'s 60 s default, the release workflow's certify step passes
    **`--timeout-seconds 300`** (cooperative-hunting 0.1.2 → 0.1.3); the fixture is **not** shrunk.
- **Scaffold from `templates/`** with `<slug>` = `atari-cabinet`, `<IMAGE>` =
  `coworld-atari-cabinet`, `<SEATS>` = **4**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`, `tools/ci/docker_smoke.sh`
  (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim, no substitutions),
  `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh` (**`chmod +x`**). Two
  additions to the template `ci.yml`: the `docker-smoke` step gets
  `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format), and the `wasm-viewer` job gets the extra
  `renderer_fixture.html` step of §Tests. The `NIM_TESTS_RELEASE_ONLY` repo variable lists
  `tests/test_perf.nim` and `tests/test_baselines.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/atari-cabinet-player"`, one image,
  env-switched; each also sets `PLAYER_POLICY_LABEL`):

  | name | env | role |
  |---|---|---|
  | `atari-cabinet-castellan` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `atari-cabinet-gunner` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `atari-cabinet-bulwark` | `PLAYER_SCRIPTED` = `bulwark` | filler |
  | `atari-cabinet-spinner` | `PLAYER_SCRIPTED` = `spinner` | filler |

  A four-seat episode is filled by the platform with the two champions plus fillers — which is what
  makes the cross-play mean meaningful.
- **Repo layout**: `src/atari_cabinet.nim`, `src/atari_cabinet_player.nim`,
  `src/cabinet/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, arena.nim, rom.nim,
  control.nim, stances.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim, replays.nim,
  replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, wire_constants.nim,
  server.nim}`, `replay-viewer/{cabinet_replay.nim, config.nims, static_replay.js,
  static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, STANCES.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `atari_cabinet.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only
harness; the sandbox has no Nim, Docker, emsdk or browser. The **determinism gate** (test 2 plus
the viewer smoke) is inviolable: if it fails, the physics or a build flag changed — fix the code,
never the test.

1. **`tests/test_physics.nim`** — sim unit tests: a ball's speed is **exactly** `ballSpeed0` until
   its first paddle contact and rises by exactly `BallSpeedStep` per contact, capped at
   `BallSpeedMax`, over 5 000 ticks including 60+ wall bounces (the index-reflection property,
   asserted bit-exactly); a ball's centre never leaves `[0, ArenaSide]²`; the two index reflection
   rules are checked against a float reference to within one index; a paddle centre never leaves
   `±PaddleTravelHalf` and never moves more than `PaddleMaxSpeed` in a tick; the deflection fan
   always returns a local index in `4 … 28`, i.e. **a paddle can never send a ball into its own
   mouth**, over all 13 offsets × 3 spins × 64 incoming indices × 4 sides (9 984 cases,
   exhaustive); a brick is destroyed by exactly one contact and reflects the ball on the crossed
   face; **the no-tunnelling bound is asserted directly** —
   `BallSpeedMax < PaddleThickHalf + BallHalf`, so no legal ball speed can cross the thinnest
   contact window in one tick — and over 50 000 randomised legal states the swept-contact test and
   the end-position test return the **same** answer, which is what makes the sweep a guard rather
   than a behaviour change; a `cmd` of 243..255 decodes identically to 40 in both the server path
   and the replay-runtime path.
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same ROM + same command-byte
   log ⇒ identical `gameHash` at every tick over a full 2880-tick run, twice in one process and
   once in a fresh sim; (b) a one-unit change in any command byte changes the final hash; (c) a
   committed golden fixture `tests/data/golden_hashes.json` pins the hash at every 48th tick for
   seed 5140913 in **each of the three ROMs**; (d) **a source guard** that greps
   `src/cabinet/{sim,arena,rom,trig,sim_types,sim_config,sim_state}.nim` for
   `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts for
   `-ffast-math`, failing on any hit, plus a grep for `rand(` (only `drawInt` may draw);
   (e) `DirQ64` re-derived from `math.cos`/`math.sin` entry by entry; (f) `perm` and the first 200
   serve directions are pure functions of `seed`, identical across two fresh sims, and `perm` is a
   permutation of `0..3`; (g) `rngDraws` is identical between two runs of the same command log.
3. **`tests/test_arena.nim`** — geometry: the four side-local frames round-trip
   (`localOf(k, worldOf(k, along, depth)) == (along, depth)`) over 100 000 randomised points and
   all four sides; side `k`'s `along = +50` and side `(k+1) mod 4`'s `along = −50` are the **same
   world point** for all four `k`; the 9 brick columns tile `along ∈ [−18, +18]` with the declared
   3.60/0.40 pattern and no overlap; a mouth crossing is detected iff `depth` crosses 0 with
   `|along| < goalHalf`, over 50 000 randomised segments; an **out** cabinet's whole side reflects
   and never concedes; the bounded serve sampler never returns a rejected index, and the fixed
   fallback scan fires **zero** times over 200 seeds × 3 ROMs.
4. **`tests/test_control.nim`** — the autopilot: for 5 000 randomised (state, stance) pairs the
   command byte is in `0..242`, decodes to `near, far ∈ 0..8` and `grip ∈ 0..2`, and the implied
   paddle velocity is `≤ PaddleMaxSpeed`; the same (state, stance) pair always yields the same
   byte; each of the five stances produces the documented bar target in its documented condition;
   `camp` never leaves `post` when `aggression == 0` and a ball's arrival is more than 8 cu away;
   `catch` in a ROM without `catchEnabled` behaves bit-identically to `guard`; the arrival
   prediction agrees with a brute-force per-tick float propagation to within 2 ticks and 1.0 cu
   over 10 000 randomised balls; the aim search never selects a `j` whose ray leaves the arena
   before reaching any mouth; an out cabinet and any non-`Playing` phase force `cmd = 40`.
5. **`tests/test_baselines.nim`** (release-only) — **the bounded-orders / legality assertion on the
   scripted baselines**: for 500 pseudo-random world states × both baselines × all three ROMs, the
   emitted stance validates against the reply schema — every numeric field finite and inside its
   range, `stance` in its enum, `target_ball` either `any` or a **currently live** ball id,
   `aim_at` either `none` or an **alive** cabinet's alias (never its own), `post` inside
   `±43`, `note` ≤ 160 runes, `say` ≤ 48 runes — and the compiled command byte is in `0..242`.
   Plus the tuning pin: **four `bulwark`s in `warlords` produce at least 6 concedes and at least
   one elimination on at least 17 of 20 seeds**, with total `saves` above 120; four `spinner`s
   produce strictly more concedes and a strictly lower mean score than four `bulwark`s; a
   2-`bulwark`/2-`spinner` mix ends with a `bulwark` seat in placement 1 on at least 15 of 20
   seeds. (This is the anti-regression pin for the whole physics tuning: if the baselines cannot
   hold a rally, the three `BaselineParams` numbers are wrong — re-run `tools/tune_baselines.nim`
   and commit the sweep's pick to `tools/ci/baseline_tuning.json`, which `tests/test_tuning.nim`
   re-asserts. The physics constants and the ROM presets do not move.)
6. **`tests/test_stances.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON, a
   percentage `aggression`, an out-of-range `post` given in percent, `aim_at` as `"the red
   cabinet"`, `target_ball` as `"ball 2"`, each `stance` synonym, an unknown `stance`, an `aim_at`
   equal to my own alias, an `aim_at` naming an **out** cabinet, a `target_ball` that is
   mid-serve, NaN/absent fields, a 300-character `note`, and a `say` whose 48th and 49th characters
   are a **4-byte emoji** — the truncation must land on the **rune** boundary and the result must
   still round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the
   `bulwark` stance plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a
   `throttled` client ⇒ **zero** retries.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all four seats' calls
   go out in one parallel batch** (the fake records in-flight windows; the test asserts all four
   intersect); an **eliminated** seat is dropped from later batches; consecutive batches are ≥
   `turnSpacingMs` apart; the per-turn budget is enforced with a hung client; the budget guard
   switches to scripted and the episode still ends `complete/*`; the 660 s stop yields
   `deadline/wall_clock`; a tripped invariant yields `fault/sim_fault` with a partial replay; a
   disconnected seat plays `bulwark` and revives on reconnect; a never-connecting seat is reported
   to `COGAME_PLAYER_FAILURE_URI` and the run still reaches a normal ending; a registration that
   arrives before its player index exists is **held and applied**, not dropped.
8. **`tests/test_locality.nim`** — the two-name-space and information invariants. Over 200
   randomised states: seat `s`'s composed LLM user message and its Sprite frame contain **every**
   live ball, **every** paddle, **every** brick bit and **every** cabinet's lives (the board is
   public — the positive half of the assertion); and contain **no** other seat's `note`, `say`,
   `stance`, `aim_at` or prompt, no `perm`, no `seed`, no RNG state, no future serve direction, no
   wall-clock or budget fact, and no `sim.players[i].address`. Also:
   `control.paddleCommand`'s inputs are structurally limited to the sim state, the cabinet index
   and that cabinet's seat's stance.
9. **`tests/test_scoring.nim`** — the formula and its sign: the seven worked examples of §The game
   reproduce to 3 decimals; the lives term is exactly `60·livesLeft/startingLives` for
   `startingLives ∈ {3, 5, 9}` with no rounding drift; **no term is ever negative and no score is
   ever below 0.000**; a knockout is credited to `lastTouch` and never to the conceder; a cabinet
   chipping its **own** brick scores nothing; the placement chain is total (`placements` is a
   permutation of 1..4 over 20 000 randomised end states) and exactly one seat carries the crown;
   `win[s] == (placements[s] == 1)`; an elimination at tick `t` ends the episode iff exactly one
   cabinet still has lives.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full 4-seat
    scripted episode in **each of the three ROMs** writes `results.json` and a `COWLDCAB` replay;
    `parseReplayBytes` accepts it; re-simulating from the config + recorded command bytes
    reproduces **every** recorded hash; **`tools/replay_summary.py` output parses under a strict
    UTF-8 JSON parser** (`json.loads(out.decode("utf-8"))`) with the fixture forced to carry a
    non-ASCII `say` and a non-ASCII policy label, so the UTF-8 path is real; the embedded config
    JSON decodes strictly and contains `seed`, `rom`, the fully resolved preset, `perm` and the
    geometry table; every `stance` record is ≤ 600 runes;
    `results.reason`/`results.endRule`/`results.rom` are in the legal enums; the stream contains
    exactly 4 `register` records, one `stance` record per alive seat per turn, at least one `save`
    and one `concede`, and exactly one `result` record.
11. **`tests/test_server.nim`** — websocket contract: registration chat accepted and **not** echoed
    into the replay chat stream; a prompt over 4000 runes truncated, not rejected; a
    non-registration chat from a player dropped; an input mask from a player ignored; bad token
    403; `/healthz`; `/global` snapshot → ticks → game over; `/client/global` and `/client/player`
    serve real pages and neither opens the player socket; `/healthz` and `/global` still answer
    15 s after the artifacts are written; artifact writes to `file://` URIs. **Two name spaces**:
    the composed LLM user message and the player-stream board labels contain no real name, while
    the chrome roster, `over` and `results.names` do.
12. **`tests/test_manifest.nim`** — **`num_agents == 4` in every one of the three variants *and* in
    `certification.game_config`**; `len(certification.players) == 4` and
    `len(certification.game_config.players) == 4`; every declared `player[]` id occupies at least
    one certification slot and its `resources.limits.cpu == "1"`; `results_schema` keys ==
    `playerResultsJson` keys with every per-seat array bounded `minItems: 4, maxItems: 4`; every
    array in `config_schema` declares `minItems`/`maxItems`; `game.protocols` has **both** `player`
    and `global` as `{"type":"text",…}`; `game.docs.readme` and all three pages are non-empty text;
    `game.description` present and `game.tags` **absent** (tags top-level, ≥ 3);
    `game.replay_viewer.bundle == "static-replay-viewer"` and there is no top-level `version` or
    `game.display_name`; `game.owner` present; **every variant** has the same `maxTicks`,
    `turnTicks`, `turnSpacingMs`, `turnBudgetMs` and `wallClockBudgetSeconds`; every variant's
    `wallClockBudgetSeconds ≤ 0.6 × 1200`; `attempt1Ms + retryMs ≤ turnBudgetMs`;
    `maxTicks mod turnTicks == 0`; the compose service name uppercased with `-`→`_` equals the
    image placeholder and the image is `coworld-atari-cabinet`; the secret namespace equals
    `game.name`; `config_schema` covers every field `sim_config.update` reads.
13. **`tests/test_rom.nim`** — the preset machinery: `applyPreset` obeys
    **`defaults → named preset → explicit key`** in that order (the cert fixture's
    `rom: "warlords"` + `startingLives: 9` resolves to 9, not 3); each of the three named ROMs
    resolves to exactly the row of §The ROM preset table; **each variant's `game_config` is
    constructed and stepped for 600 ticks with four `bulwark`s without a fault** (collab-cooking
    0.1.1, 2026-08-25: test every variant, not just the fixture); `farPaddle: false` leaves the
    `far` nibble with **no** observable effect on the hash; `catchEnabled: false` makes `grip == 1`
    a no-op; `brickRows: 0` removes every brick from the hash and from the state JSON.
14. **`tests/test_viewer.nim`** — static assertions over `client/replay_broadcast.html` and
    `client/chrome_common.js`: `chrome_common.js` is **byte-identical** to the starter's copy
    (sha256 pinned); `replay_broadcast.html` still contains ctf's `relayout()` with `--band`,
    `--topband` and the `--hudscale` clamp on `:root`; `#endcard { bottom: var(--band) }`;
    `#scorebug`, `#bannerlane`, `#killfeed`, `#transport`, `#mmwarn`, `#endcard`, `#momentum` and
    the `.tiny` block are present; `#viewpanel`, `#minimap`, `#zoombar`, `#fpv` and `#povBadge` are
    **absent**; a `.beat-marker` CSS rule exists for **every** beat kind the sim emits (`concede`,
    `breach`, `eliminated`, `last_standing`, `over`) and every marker is a `<button>`; no
    game-block top-level name collides with chrome_common's alias list; the `.plate-name { flex: 1
    1 auto; min-width: 3.2em` rule is present; the state JSON's `teams` keys are exactly
    `red`/`blue`/`green`/`yellow`; `broadcast_core.js` differs from the starter's copy in
    **exactly** the `CABINET_WIRE` identifier; no `ctf_`/`CTF_`/`paintball` identifier survives in
    `client/`, `replay-viewer/` or `src/`; `static_replay.js` sets both `data-replay-loaded` and
    `data-replay-error`; and `config.nims` contains **no** `MODULARIZE` or `EXPORT_NAME`.
15. **`tests/test_startup.nim`** — `/bin/atari-cabinet` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable, or when `rom` is not one of the
    three; the seed is randomised when unpinned (before `config.update`) and honoured when pinned;
    both entrypoints exist and are executable in the image.
16. **`tests/test_perf.nim`** (release-only) — 2880 ticks of physics plus 11 520 autopilot
    evaluations complete in under 60 s.

**CI jobs beyond the Nim tests:**

- `docker-smoke` — `tools/ci/docker_smoke.sh` runs a raw-Docker episode from the certification
  fixture with **`SMOKE_SEATS=4`** (an independent cross-check against
  `certification.game_config.num_agents`; a mismatch prints `SEAT-COUNT FAIL:`) and
  `SMOKE_REQUIRE_REPLAY_JSON=0`, asserts **every one of the four player containers' exit codes** as
  well as the game's, and uploads the replay it produced as the `smoke-replay` artifact.
- `wasm-viewer` (`needs: docker-smoke`) — asserts `tools/build_replay_viewer.sh` and
  `tools/ci/viewer_smoke.mjs` exist and the hook is executable, builds the bundle, asserts a
  non-empty `.wasm`, downloads the smoke replay, and then **EXECUTES the bundle in headless
  chromium**:
  ```
  node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
       --replay dist/smoke/<name>.replay --timeout 90 --soak 12 --strict-text-bounds
  ```
  The job fails if `data-replay-loaded` never arrives, if `data-replay-error` is set, if the soak
  sees playback stop advancing, or if `canvas_text.never_inside` is non-zero (fixed arena). The
  1440-tick fixture is 60 s long, so a 12 s soak cannot end the replay. **This is the only gate
  that runs the viewer rather than checking that its files exist** (cogame-lantern, 2026-08-23).
- `wasm-viewer`, second step — **`tools/ci/renderer_fixture.html`**: `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so every seat plays scripted and the smoke replay carries only the
  baselines' fixed `say` strings; nothing in CI would otherwise exercise the bubble band, the aim
  rays or the feed at full cap. The fixture loads the real renderer with a **full-cap 48-rune `say`
  and 160-rune `note` on all four seats at once**, all four aim rays live, at 360, 620 and 1280 px,
  self-checks its own string lengths, and is run through `viewer_smoke.mjs --strict-text-bounds` in
  its own step (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Any Atari emulator, ROM image, ALE binding, `AutoROM` download or PettingZoo dependency.** The
  ROMs are proprietary, an emulator cannot live inside the native↔wasm determinism boundary, and
  bit-exact ALE parity is not a goal, not tested, and not claimed anywhere in the repo. Every
  constant in this note is the cabinet's own.
- **Pixel and RAM observations, and any CNN/neural policy interface.** The idea's stated gap
  ("pixel-input competition") is **not** filled by v1: seats get a structured JSON board view, and
  the platform's policy interface here is an LLM prompt or a scripted baseline. There is no RGB
  crop, no frame stack, no `frameskip` knob and no per-frame joystick socket. A raw per-tick action
  channel is a protocol addition, not a redesign — the autopilot is already a pure function of
  `(stance, sim state, cabinet index, tick)` — but it is not in v1.
- **`surround` / Tron light-cycles, `maze_craze`, `wizard_of_wor`, `combat_tank`/`combat_plane`,
  `joust`, `mario_bros`, `space_invaders`, `entombed`, `flag_capture`, `othello`,
  `video_checkers`.** None of them is a paddle-and-ball game, so none of them is a preset on this
  engine; each would be a second sim, a second observation model, a second controller and a second
  board. `surround` in particular (a growing-trail grid game) and `othello`/`video_checkers`
  (turn-based board games, which belong on the babel/parley row entirely) are separate coworlds if
  they are ever built.
- **SlimeVolleyGym.** Gravity, a net, and **two** seats — it would break the fixed `num_agents = 4`
  and needs a different engine. Not a "bonus ROM" here.
- **1v1 and 2v2 ROMs (`pong`, `tennis`, `boxing`, `ice_hockey`, `double_dunk`) and team or
  cooperative motives.** `num_agents` is 4 in every variant and the cert fixture, and v1 has one
  motive: four-way free-for-all with four distinct scores. A team ROM would change what the league
  ranks by, which cannot vary between variants of one coworld.
- **A "season bracket" as repo work.** The platform league *is* the bracket. `results.rom` lets a
  board be split per ROM after the fact ("per-ROM scoreboards"), and that is the whole of the
  idea's replay plan that lands in v1.
- **More than three ROMs, and any ROM that changes the seat count, the clock, the decision cadence
  or the wall-clock budget.** `brickRows: 2` and the second brick-row geometry exist in the schema
  and the sim for a future preset, but no shipped variant uses them.
- **Ball–ball collision, paddle–paddle collision, spin decay, ball gravity, curved walls, moving
  walls, powerups, extra lives and brick rebuilding.** Balls pass through each other; a paddle
  passes through nothing because paddles never meet. The only state that decays is a brick.
- **Inter-seat communication of any kind, at any bandwidth** — including a symbol channel, a shared
  blackboard, or an emergent side channel through the observation. `say` and `note` are one-way to
  the spectator feed. Four cabinets in an arcade do not chat.
- **Fog of war, vision cones, the first-person POV and any partial observation of the board.**
  Deleted from ctf, not disabled: the cabinet is a CRT and the physics is public. What is hidden is
  *who is playing*, which is §Server's list.
- **Everything else ctf's arena rules carried**: guns, flags, hearts-as-objectives, lives-as-hp,
  respawn, grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the
  barrage, the hill, the paint grid, procedural terrain, the map pool, the map editor and mapkit.
  Deleted, not disabled.
- **Player debug-sprite overlays** (ctf's `0x86` channel) and the zoom/minimap panel. The seats
  send no inputs and draw no overlays in v1; `#viewpanel` is removed because the board always fits
  the frame.
- **Audio, CRT curvature shaders, camera cuts, slow-motion replays**, and any downloaded art asset.
- **Persistent memory across episodes** (no notes carried between runs) and any tournament
  structure beyond the platform league.
