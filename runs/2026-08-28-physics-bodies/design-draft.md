# cogame-physics-bodies — design note (2026-08-28, paintbot lineage)

`Metta-AI/cogame-physics-bodies` is a **two-seat, zero-sum continuous-control coworld**: two
four-legged physics bodies — "bugs" — stand in a circular clay ring 6.00 m across and try to put
each other **out of it**. Each bug is a torso disc on four legs; a leg that has floor under it can
push, a leg over the rim cannot; a shove that lands off-centre spins you; a body that is spun,
sprinting tall, or being levered under **tips over and goes down** for a second and a half, and
three knockdowns loses the round. The ring **shrinks** while the round runs, so there is nowhere to
hide. Best of five rounds. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its
read-only mount `/workspace/starters/coworld-ctf`. **Every convention there holds here unless this
note says otherwise** — the 24 Hz wall-clock-paced game loop, the one-byte-per-seat-per-tick recorded
action log, the `COWLDCTF`-family replay codec with its per-tick `gameHash` chain, keyframes and lull
spans, the server-side decision layer (`src/ctf/{decide,directives,control,baselines,llm}.nim`: **one
parallel LLM batch per turn**, two bounded deadlines, an inter-batch rate floor, a budget guard,
tolerant parsing, rune caps, a scripted fallback), the mummy server and its `COGAME_*` runtime
contract, the seat/cog split and the `cogAlias` two-name-space rule, the broadcast chrome
(`client/replay_broadcast.html` + `client/chrome_common.js` + `client/broadcast_core.js`), the
emscripten static replay bundle (`replay-viewer/`, `Dockerfile.replay-viewer`,
`tools/build_replay_viewer.sh`) and the `GameVersion` prepend-only changelog discipline are all
inherited.

**Starter choice, in one line:** sumo is a **real-time game loop with rules written fresh for this
coworld** — the first row of the starter table (`prompts/10-design.md`; `playbooks/make-coworld.md`
§Phase 0) — because paintbot already ships, tested, every layer this game needs except the ring
rules: a wall-clock-paced integer tick loop, a per-tick per-seat action log inside a replay whose
hash chain is re-checked in the browser, a server-side low-rate LLM decision layer over a per-tick
deterministic controller, published scripted baselines that emit the identical decision object, and a
static wasm viewer that re-derives every frame. It is deliberately **not** the `cogame-moba` row:
that row is for **bit-exact** ports of an existing external C/RL environment, and this is not one —
RoboSumo and MuJoCo Soccer are float64 MuJoCo with per-step continuous joint-torque vectors, and this
is an integer-micrometre, turn-intent coworld that reproduces sumo's *shape* (torque/thrust-driven
multi-limbed bodies, momentum, pushing, a ring boundary, falling over), not MuJoCo's numerics.
(Operator ruling 2026-08-22, Cogball: a new physics game takes paintbot. Precedents on this starter:
`cogame-cogball`, `cogame-tandem`, `cogame-pistonball` — `runs/2026-08-25-pistonball/design.md` —
`cogame-particle-worlds`, and directly `cogame-walker-waterworld`,
`runs/2026-08-26-walker-waterworld/design.md`, whose integer-micrometre turn-intent physics pattern is
followed here wherever it fits.)

**Source idea, verbatim** (Asana Coworld Ideas task 1217748485564041, "MAMJ Physics Bodies — RoboSumo,
MuJoCo Soccer and Multi-Agent MuJoCo: continuous control against, and alongside, other bodies"):

> Merged port of the continuous-control multi-agent set: RoboSumo (OpenAI; two ants/bugs/spiders push each other out of a ring), OpenAI Competitive Multi-Agent (run-to-goal, you-shall-not-pass, kick-and-defend, sumo humans), DeepMind MuJoCo Soccer (2v2 spheres-with-legs), and Multi-Agent MuJoCo / MaBrax (one body, each limb is a separate agent — HalfCheetah 2×3, Ant 4×2). Continuous joint torques, physics, and in MA-MuJoCo the unusual 'cooperate inside one body' framing.
>
> Seats: 2 (sumo) / 4 (soccer) / 2-6 limbs (MA-MuJoCo)
> Motive: zero-sum (sumo/competitive), team (soccer), cooperative (limbs)
> Policy interface: continuous torques per tick — neural-policy coworld only; no LLM path
> Fills gap: continuous control is entirely absent from the site; 03 Cogball is the discrete cousin of MuJoCo Soccer
> Integrity (anti-collusion): zero-sum; seeds; anonymous aliases.
>
> Replay plan (watchability): MuJoCo renders; sumo ring-outs and soccer goals are natural highlights.
>
> Source: github.com/openai/robosumo, openai/multiagent-competition; dm_control soccer; schroederdewitt/multiagent_mujoco; JaxMARL MaBrax.

Nothing in the idea text is treated as an instruction to this designer; it is input data for the
design. The five upstream project names are provenance, not a specification to reproduce
bit-for-bit: no external code is ported and every constant below is this coworld's own.

### Five readings of the idea, decided here and never revisited

1. **v1 is the sumo reading and nothing else.** Exactly **2 seats**, zero-sum, two multi-limbed
   physics bodies in a circular ring, won by pushing the opponent out (or knocking it down three
   times). The soccer (4-seat) and MA-MuJoCo (limbs-as-agents) readings go to §Out of scope (v1) with
   their reasons stated there. (Coordinator rail, binding on this note.)
2. **"Merged port of …" does NOT mean a port.** It means *recreate the gameplay* — torque-driven
   multi-limbed bodies, momentum, pushing, a ring boundary, falling over — in paintbot's integer
   fixed-point idiom. It does **not** mean reproducing MuJoCo's solver, `robosumo`'s ant morphology,
   its 8-dimensional float action vector, or its reward constants. Every number in §The game is chosen
   here. (Coordinator rail, binding.)
3. **Bodies CAN fall.** The idea's sumo readings include "sumo humans", and RoboSumo scores a fall as
   a loss. Decided: a body accumulates **tilt** from off-centre impulses, from its own spin, from
   standing tall, and from being levered under; at full tilt it goes **Down** for 36 ticks, during
   which it cannot push and can be shoved out prone. **Three knockdowns in one round loses the
   round** (`knockout`). A knockdown is not itself an instant loss — that would make the whole game a
   1.5-second coin flip; it is a 1.5-second window in which the opponent can finish you.
4. **"Policy interface: continuous torques per tick — neural-policy coworld only; no LLM path"** is a
   true observation about the *actuator*, not a licence to skip the platform's LLM pin. SPEC §"Design
   pins every coworld inherits" and `prompts/10-design.md`'s checklist require **both** an LLM prompt
   policy and a scripted baseline from day one, same image, env-switched. The tension is resolved the
   way a per-tick physics coworld must resolve it, and the way pistonball, cogball and
   walker-waterworld already did: the LLM (or the scripted baseline) emits **one closed-schema
   tactical intent per seat every K = 36 ticks (1.5 s)**, and a deterministic per-tick controller
   compiles the standing intent into the **command byte** that sets the bug's drive bearing, posture
   and leg effort at 24 Hz. The byte is the action; the byte is what the replay records; the byte is
   what the viewer replays. The scripted baseline is *the same controller* driven by a fixed heuristic
   intent policy, so the two policy kinds are strictly comparable and a baseline is legal by
   construction. (Coordinator rail, binding.)
5. **"Integrity (anti-collusion): zero-sum; seeds; anonymous aliases"** is implemented as: an exactly
   antisymmetric score (`score[0] = −score[1]`, §Scoring), a **seeded** seat→body permutation and a
   **seeded** start axis re-drawn every round, an **end swap** every round so neither seat owns a
   side, in-game aliases that name a body and never an entrant, and a game with **no notion of who
   holds the other seat**.

**There is no `OPEN` section.** Every reading the idea leaves loose — how many seats, what the score
is, whether bodies fall, how a continuous actuator becomes an LLM decision, what ends a round and
what ends the episode — is a rail the designer decides, and each is decided below with its reason.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How physics-bodies satisfies it |
|---|---|
| Starter by game shape | **`Metta-AI/coworld-ctf` (paintbot)** — a real-time 24 Hz continuous-physics loop with new rules. The arena rules (teams, guns, flags, fog) are replaced by the ring; the loop, action-log replay, decision layer, viewer, chrome and CI wiring stay. (§Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-physics-bodies`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions: `physics-bodies-ringcraft`, `physics-bodies-toppler`) vs `PLAYER_SCRIPTED=pusher` / `PLAYER_SCRIPTED=anchor` (both fillers). One image `coworld-physics-bodies`, one player entrypoint `/bin/physics-bodies-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `game.replay_viewer = {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` kept (its ecos `mkdir -p` fix is already at lines 20/30 of the starter's copy); the **same** `src/bodies/sim.nim` compiles into `replay-viewer/bodies_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is ctf's page with a game block **appended**; the clay ring, rim paint, bug hulls, legs, dust and tilt gauges are baked at startup with pixie from ctf's shipped `data/arena_floor.png`, `client/art/walls/wall_h.jpg`, `wall_v.jpg`, `client/art/lockerroom/bg.jpg` and `data/font.ttf`. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | In-game every cog is `BUG-1` or `BUG-2` and nothing else; real policy names live only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (§Tests 8, 11). |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | ≈403 s expected / ≈451 s absolute worst case against the 720 s budget; a **660 s** engine hard stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 2** in variant `default`, variant `blitz`, **and** `certification.game_config`; `<SEATS>` = **2** in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Two bugs, one shrinking ring, best of five.** Each bug is a 0.60 m torso disc walking on four legs.
It pushes by loading the leg behind it — a leg that has floor under it. It shoves the other bug by
driving a loaded foot into it. A shove that lands off the opponent's centre line **spins** the
opponent, and spin, height and being levered under all load **tilt**; at full tilt a bug **falls
over** and lies there for a second and a half. You lose the round the instant your torso centre
crosses the rim, or on your third knockdown, and the rim comes toward you as the round runs.

### Seats

**`num_agents` = 2. One seat = one bug.** Reasons, in order: (a) two is the sumo reading the
coordinator railed and the only seat count at which the game is what the idea's headline describes —
"two ants/bugs/spiders push each other out of a ring"; (b) two is the smallest count at which the
score can be **exactly zero-sum**, which is the idea's own integrity clause, and it makes **Elo**
the correct league metric (unlike the cooperative precedents on this starter, where Elo cannot
separate a four-way draw); (c) two parallel LLM calls per turn sit far inside the Bedrock sidecar's
30-requests-per-minute-per-episode cap at a 6 s batch floor (§Decisions), which buys **60** decision
turns — the highest turn count in the lineage, and what makes a 90-second physical duel readable as a
sequence of tactical choices. The idea's `2 / 4 / 2-6` range is closed here at **2** and is 2 in both
manifest variants, in the certification fixture and in `SMOKE_SEATS`.

Seat `s` (slot 0..1) drives bug `perm[s]`, where `perm` is a permutation of `0..1` drawn once at
`t = 0` from `config.seed` (one dedicated integer draw stream). In-game the cog driving bug `i` is
called **`BUG-<i+1>`** (`BUG-1`, `BUG-2`): an alias that names *a body on the board*, which both
seats legitimately know, and never an entrant. `perm` is written into the replay config JSON (the
viewer needs it to map real names onto bodies) and into `results.bodies`, and is **never** visible to
any seat.

Seats are symmetric in rules, scoring, observation shape and actuator. Where they start is re-drawn
every round and swapped every round (§Rounds), so no seat owns a side.

### World, units, and why they are integers

The whole sim runs in **integers**, for Cogball's, Tandem's, pistonball's and waterworld's reason:
replays are re-simulated by the **emscripten/wasm32** build of the same Nim module that the **native
amd64** server ran, and their per-tick `gameHash` chains must match bit-for-bit. Integers make that
true by construction rather than by an argument about two builds of libm agreeing.
`src/bodies/{sim,ring,body,trig}.nim` contain **no floating point at all** (grep-enforced in CI,
§Tests 2d).

| Quantity | Unit | Type |
|---|---|---|
| Position, length, radius | micrometres (µm) | `int32` |
| Velocity, per-tick impulse | µm per tick | `int32` |
| Direction index | 1/32 turn, `0..31`, index `d` = bearing `11.25° · d` counter-clockwise from east in **view** orientation | `uint8` |
| Heading | **milli-index**, `0 … 31999` (1000 = one direction index) | `int32` |
| Yaw rate | milli-index per tick | `int32` |
| Tilt | milli-tip, `0 … 1000` | `int32` |
| Unit vectors | Q12 (4096 = 1.0), from the committed `DirQ12` table | `int32` |
| Score accumulators | **micro-points** (1e-6 of a score point) | `int64` |
| Counters (rounds, knockdowns, ring-outs, contacts) | — | `int32` |

**Arena:** `x ∈ [0, 9 600 000] µm` (9.60 m), `y ∈ [0, 6 400 000] µm` (6.40 m), origin top-left,
**y down** (ctf's screen convention). Board render scale **1 board pixel = 5 000 µm** →
`MapWidth = 1920`, `MapHeight = 1280`, `BOARD_ASPECT = 1.5`. That is 2 457 600 logical map pixels
against `MaxSupersampledMapPixels` 8 000 000, so `boardRenderScaleFor` still returns
`RenderScale = 2` (`src/ctf/global.nim:1108`), and `predictedViewerRenderBytes(1920, 1280)` is
`2 457 600 · 4 · (4·2·2 + 6)` = **216 268 800 B ≈ 216 MB** against `WasmViewerBudgetBytes`
1 600 000 000 — the viewer's load-time capacity preflight passes with 7× headroom, and every one of
those constants is **kept unchanged**.

**View coordinates** — the only coordinates a policy or the chrome ever sees — are **metres with the
origin at the arena's bottom-left corner, x right, y up**: `X = x_µm / 1 000 000`,
`Y = (6 400 000 − y_µm) / 1 000 000`. Bearings reported to policies are **degrees counter-clockwise
from east in view orientation** (`0° = right`, `90° = up`), speeds are m/s, and every number shown to
a policy is rounded to 2 decimals.

`DirQ12*: array[32, tuple[x, y: int32]]` in `src/bodies/trig.nim` is a **committed literal table**,
generated once by `tools/gen_trig_table.nim` and checked in, where entry `d` is
`(round(4096·cos(11.25°·d)), round(−4096·sin(11.25°·d)))` — i.e. the view bearing `11.25°·d`
expressed in **sim (y-down) components**, so the sim never negates anything at a call site. A test
re-derives every entry from `math.cos`/`math.sin` (§Tests 2e). Reflections are exact **index**
arithmetic: about the outward normal index `n`, `d' = (2·n − d + 16) mod 32`.

`isqrt(v: int64): int64` (Newton's method, integer seed) is the only square root in the sim —
contact distances, speed clamps, rim distances — committed and unit-tested exhaustively below 2¹⁶ and
on perfect squares to 2⁴⁰.

### The body (the "bug")

A bug is **one rigid torso plus four legs**, and it is the whole of the multibody model. There is no
joint solver, no inverse kinematics and no ragdoll; there are five collision discs and one leg
kinematic that turns the command byte into forces. This is the reduction the coordinator railed and
it is stated as a reduction, not dressed up as MuJoCo.

- **Torso**: centre `p` (µm, `int32` pair), velocity `v` (µm/tick), heading `hMilli`
  (`0 … 31999`), yaw rate `omegaMilli`, tilt `tipMilli`, `downTicks`, radius
  `TorsoRadius = 300 000 µm` (0.30 m).
- **Four legs**, `k = 0..3`, mounted at torso-relative direction-index offsets
  `LegBaseIdx = [0, 8, 16, 24]` (0°, 90°, 180°, 270° of the torso's own frame). Leg `k`'s foot
  direction index is `fk = (hMilli div 1000 + LegBaseIdx[k]) mod 32`; its **reach** `r` is a pure
  function of the current posture (`ReachByPosture`, below); its foot centre is
  `foot[k] = p + (r · DirQ12[fk]) div 4096`, radius `FootRadius = 110 000 µm` (0.11 m).
- **Grounded**: leg `k` is grounded iff `|foot[k] − RingCentre| ≤ ringRadiusNow` **and**
  `downTicks == 0`. `groundedCount ∈ 1..4` while the bug is up (proved in §Tests 3: the torso centre
  is inside the ring by definition of "up", and the inward foot is therefore always inside too),
  and `0` while it is Down. A foot over the rim finds no floor — **standing near the edge costs you
  traction and stability**, which is the whole tactical spine of the game.

### Geometry and constants (fixed; identical every episode)

```
ArenaW              = 9_600_000 µm  (9.60 m)
ArenaH              = 6_400_000 µm  (6.40 m)
RingCentre          = (4_800_000, 3_200_000)     -- view (4.80, 3.20) m
RingRadius0         = 3_000_000 µm  (3.00 m)     -- ring diameter 6.00 m at round start
RingRadiusMin       = 1_800_000 µm  (1.80 m)     -- the shrink floor
ShrinkStartTick     = 144            (6.0 s into a round)
ShrinkPerTick       = 4_000 µm/tick  (0.096 m/s) -- reaches 1.992 m by the round clock
TorsoRadius         =   300_000 µm  (0.30 m)
FootRadius          =   110_000 µm  (0.11 m)
LegCount            = 4 ; LegBaseIdx = [0, 8, 16, 24]
ReachByPosture      = [620_000, 460_000, 300_000, 540_000] µm   -- low / even / high / lift
StartRadius         = 1_900_000 µm  (1.90 m from centre; the bugs start 3.80 m apart)
```

**Actuation and dynamics constants** (posture-indexed arrays are ordered `low, even, high, lift`):

```
ThrustUnit          =     3_600 µm/tick^2  -- at effort 3, 4 legs grounded, posture 'even'
TractionMulPct      = [130, 100,  70,  90]
FricNumPer1024      = [ 40,  26,  16,  32] -- v -= (v * FricNum) div 1024, every tick
MaxSpeedByPosture   = [ 95_000, 135_000, 165_000, 115_000] µm/tick (2.28/3.24/3.96/2.76 m/s)
MaxBodySpeedHard    =   260_000 µm/tick (6.24 m/s) -- the post-contact clamp and the fault guard
YawGainPct          = [ 70, 100, 130,  90]
YawAccelMilli       =       120 milli-index/tick^2
MaxYawMilli         =       900 milli-index/tick (10.125 deg/tick = 243 deg/s)
YawDragNumPer1024   =       180
Restitution         =     1_200 (Q12; 0.293 rebound on a body-body normal impulse)
ShoveUnit           =     6_200 µm/tick  -- velocity impulse at effort 3, posture 'even'
ShoveMulPct         = [110, 100,  80, 150]
TipImpulseThreshUm  =    26_000 µm/tick  -- normal impulse above this loads the receiver's tilt
TipPerUmDiv         =        40          -- tilt milli = excess impulse div 40
LiftTipMilli        =        60          -- per contact tick, a 'lift' pusher at effort 3
LiftSelfTipMilli    =        20          -- what the lifter loads onto ITSELF per contact tick
TipRecvMulPct       = [ 60, 100, 140, 100]  -- the RECEIVER's posture scales incoming tilt
SpinTipMilli        =       600          -- |omegaMilli| above this adds (|omega|-600) div 8
TipRecoverMilli     =        26          -- x groundedCount div 4, per tick
TipDown             =     1_000
DownTicks           =        36  (1.5 s)
KnockdownsToLose    =         3
```

**Terminal speeds are set by friction, not by the clamp.** `low` 3600·130/100 · 1024/40 = 119 808
(clamped to 95 000), `even` 141 784 (clamped to 135 000), `high` 161 280 (under its 165 000 clamp),
`lift` 103 680 (under its 115 000 clamp). The per-posture clamp is applied inside the dynamics step
every tick; **contact impulses are clamped separately** to `MaxBodySpeedHard`, and the §Resolution
step-11 fault guard is `|v| > MaxBodySpeedHard`, so a legal contact can never trip it.

**The command byte** — the recorded action, one `uint8` per seat per tick, exactly ctf's
`ReplayInput.keys` width (`src/ctf/replays.nim:161-182`; the whole action stream is that log):

```
drive   = int(cmd) div 16        # 0..15, a drive BEARING; direction index = 2*drive (22.5 deg apart)
posture = (int(cmd) div 4) mod 4 # 0 = low, 1 = even, 2 = high, 3 = lift
effort  = int(cmd) mod 4         # 0..3, leg load
```

16 × 4 × 4 is exactly 256, so **the byte uses its whole range, no value is reserved and no value
needs repair**. The three sub-fields are the three things the physics needs; everything else a
continuous actuator would carry is derived: the **torso heading follows a yaw servo toward the drive
bearing** (a bug turns to face where it pushes) and **leg reach is a pure function of posture**. The
controller reaches force magnitudes between the four effort levels by **duty-cycling** across ticks
with an error-diffusion accumulator (§The controller) — 24 bytes a second is where the continuity
lives, not in one byte's amplitude. §Tests 4 pins that the 24-tick mean applied thrust tracks the
requested continuous value within 8 %.

### Time, rounds, and the end swap

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf** (`src/ctf/sim_types.nim:317,376`), because
every speed-coupled layer (`PlaybackSpeeds`, the lull scan, the momentum series, `tickTime`, the
transport bar) is keyed to it. There are **no substeps**.

```
turnTicks       =   36   (1.5 s)   -- K, the decision cadence; 60 turns per episode at most
roundTicks      =  396   (16.5 s)  -- 11 turns of round clock
resetTicks      =   36   (1.5 s)   -- the hold between rounds; 1 turn
maxRounds       =    5
roundsToClinch  =    3   (best of five)
maxTicks        = 2160   (90.0 s)  = 5 x (396 + 36) = 60 x 36
```

Every one of those is a multiple of `turnTicks`, so a full-length episode is exactly **60 decision
turns**. Turn boundaries live on the **global** tick grid (`t mod 36 == 0`) and are *not* re-aligned
when a round ends early: a round that ends at tick 213 is followed by 36 reset ticks and the next
round starts at 249, mid-turn. That is deliberate — re-aligning would make the wall-clock budget a
function of how the rounds went, and the budget is what the platform kills you for.

**Round start.** At the first tick of round `n` (`n = 0..4`): `ringRadiusNow := RingRadius0`; both
bugs are placed at rest, `tipMilli = 0`, `omegaMilli = 0`, `downTicks = 0`, on a **seeded start
axis** — an index `a_n` drawn from `0..31` from the seeded stream — at `StartRadius` from
`RingCentre`. Bug `0` takes axis index `a_n` and bug `1` takes `(a_n + 16) mod 32` on **even** rounds;
on **odd** rounds the two swap (the **end swap**), so a seat that got the better half of a slightly
asymmetric draw gets the other half next round. Each bug's heading faces the other. `ringRadiusNow`
then shrinks by `ShrinkPerTick` per tick once the round's tick index passes `ShrinkStartTick`, floored
at `RingRadiusMin`.

**Ring shrink is a pure function of hashed state** (the round index and the round tick), so it
re-derives identically in the browser; it is not a wall-clock fact.

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 36 == 0` and `phase == Playing`: the intents collected for turn
   `t div 36` become each seat's `activeIntent[seat]` (§Server), quantised to integers on parse. The
   server writes one **`intent` chat record per seat** into the replay. `activeIntent` is **not**
   mixed into `gameHash` — the per-tick command bytes it produces are recorded, and those are what
   the viewer replays (step 2).
2. **Controller compile**, in **body index order 0, 1** (never seat order — seat order varies with
   `perm` and the loop must not). `control.driveCommand(sim, i)` is a pure function of
   `(the whole sim state, this body's index, its seat's activeIntent, the tick)` returning the
   command byte `cmd ∈ 0 … 255`. The controller sits **outside** the determinism boundary, exactly as
   ctf's `control.nim` does, and may use floating point; the byte it produces is written to the
   replay with `replayWriter.writeInputMaskChange(tickTime(t), seat, cmd)`, which already writes
   **only on change** and updates `lastMasks[seat]` (`src/ctf/replays.nim:161`). Nothing else in the
   loop is re-derived at playback.
3. **Ring geometry.** `ringRadiusNow := max(RingRadiusMin, RingRadius0 − max(0, roundTick −
   ShrinkStartTick) · ShrinkPerTick)`. Then, for both bodies in index order, the leg reach, the four
   foot positions and `groundedCount` are recomputed from `(p, hMilli, posture, downTicks,
   ringRadiusNow)`.
4. **Yaw**, body index order. Let `target = 2 · drive · 1000` and `dMilli` = the signed shortest
   difference `target − hMilli` wrapped into `(−16000, 16000]`.
   1. `omegaMilli += clamp(dMilli div 8, −YawAccelMilli, +YawAccelMilli) · YawGainPct[posture] div 100`
      (computed in `int64`, narrowed).
   2. `omegaMilli -= (omegaMilli · YawDragNumPer1024) div 1024` (Nim `div` truncates toward zero, so
      yaw drag is symmetric under negation).
   3. Clamp `|omegaMilli| ≤ MaxYawMilli`. `hMilli := (hMilli + omegaMilli + 32000) mod 32000`.
   4. A body with `downTicks > 0` skips 4.1 (no self-driven yaw while prone) but keeps 4.2–4.3.
5. **Traction and linear dynamics**, body index order.
   1. If `downTicks > 0`: `effort := 0` (no push), `downTicks -= 1`, and friction uses `FricNumPer1024`
      index `0` (a prone body scrubs off speed fast).
   2. `a = (ThrustUnit · effort · TractionMulPct[posture] · groundedCount) div (3 · 100 · 4)`;
      `v += (a · DirQ12[2·drive]) div 4096`.
   3. Friction: `v -= (v · FricNumPer1024[posture]) div 1024`.
   4. Speed clamp: if `vx² + vy² > MaxSpeedByPosture[posture]²` then
      `v := (v · MaxSpeedByPosture[posture]) div isqrt(vx² + vy²)`.
   5. `p += v`.
6. **Body–body contacts.** Ten disc pairs are tested in one fixed order — body 0's discs
   `[torso, foot0, foot1, foot2, foot3]` against body 1's, outer loop body 0's index, inner loop body
   1's, torso first — recomputing the foot positions from the *post-step-5* torso positions. Every
   test is a **swept** overlap: a contact counts if the discs overlap at the tick's end position
   **or** if the segment travelled by their relative displacement this tick passes within
   `rA + rB` of each other (closest point of a segment to the origin — integer, `isqrt`-free until
   the final compare). For each contacting pair, in order:
   1. `n̂` = the Q12 unit vector from B's disc centre to A's disc centre (if the centres coincide, use
      `DirQ12[0]`); `pen` = `rA + rB − dist`.
   2. **Positional split**: body A's torso moves `+pen/2 · n̂`, body B's `−pen/2 · n̂` (the feet are
      rigid, so moving a torso moves its feet); a body with `downTicks > 0` takes the **whole**
      `pen` and the upright one takes none.
   3. **Normal impulse**: `vn = ((vA − vB) · n̂) div 4096`; if `vn < 0`,
      `j = (−vn · (4096 + Restitution)) div (2 · 4096)`, then `vA += (j · n̂) div 4096` and
      `vB -= (j · n̂) div 4096`. Equal masses; hence the `/2`.
   4. **Shove** (the sumo core): if A's disc is a **foot**, that leg is grounded and
      `effortA > 0`, then `shove = (ShoveUnit · effortA · ShoveMulPct[postureA]) div (3 · 100)`;
      `vB -= (shove · n̂) div 4096` and `vA += (shove · (4 − groundedA) · n̂) div (8 · 4096)`. The
      momentum comes from the **floor**, not from B, so this is deliberately not a closed-system
      impulse — and a well-planted pusher (`groundedA = 4`) takes **zero** recoil, which is exactly
      why bracing on all four legs before you shove is the right play. The symmetric case (B's foot
      into A) is covered by the same loop with the roles read from the pair.
   5. **Contact torque**: with `rVec` = the contact point minus the *receiver's* torso centre, the
      receiver's `omegaMilli += (cross(rVec, (j + shove) · n̂) · 1000) div (4096 · TorsoRadius)`,
      clamped so one contact tick can add at most `MaxYawMilli div 2`. An off-centre hit spins you.
   6. **Tilt load**: the receiver's `tipMilli += (max(0, |j| + shove − TipImpulseThreshUm) div
      TipPerUmDiv) · TipRecvMulPct[postureReceiver] div 100`; and if the pusher's posture is `lift`
      with `effort > 0` and a grounded pushing leg, the receiver additionally takes
      `LiftTipMilli · effortPusher div 3 · TipRecvMulPct[postureReceiver] div 100` and the **pusher**
      takes `LiftSelfTipMilli · effortPusher div 3` on itself.
   7. **Counters**: `contacts[receiver] += 1`; `shoveImpulseUm[pusher] += shove`. A `contact` event
      is emitted when `|j| + shove ≥ TipImpulseThreshUm`.
   8. Both bodies' velocities are clamped to `MaxBodySpeedHard` after the pair loop finishes.
7. **Tilt and knockdown**, body index order.
   1. `tipMilli += max(0, (|omegaMilli| − SpinTipMilli) div 8)` — spinning erodes your own stability.
   2. `tipMilli -= (TipRecoverMilli · groundedCount) div 4`.
   3. Clamp `tipMilli` to `[0, TipDown]`.
   4. If `tipMilli == TipDown` and `downTicks == 0`: the bug **goes Down** — `downTicks := DownTicks`,
      `tipMilli := 0`, `omegaMilli := omegaMilli div 4`, `knockdowns[i] += 1`, and a `knockdown` event
      names it. While Down its collision set is **the torso disc only** (the legs fold in), so a prone
      bug is a smaller target that cannot push and cannot recover tilt.
8. **Arena box clamp.** A torso centre is clamped inside `[TorsoRadius, ArenaW − TorsoRadius] ×
   [TorsoRadius, ArenaH − TorsoRadius]`, and the crossed component of `v` is zeroed. This is only
   reachable *after* a ring-out, while the loser is still sliding through the reset hold; it exists so
   no coordinate can leave the world.
9. **Round end checks**, in this order — the first that fires ends the round at this tick:
   1. **Ring-out.** `|p_i − RingCentre| > ringRadiusNow` for exactly one body → the **other** body
      wins the round, `roundReason = ring_out`, `ringOuts[winner] += 1`. If **both** bodies are
      outside on the same tick, the one **farther** from the centre loses; if the two distances are
      within `CentreTieUm = 20 000 µm` the round is a **draw**.
   2. **Knockout.** `knockdowns[i] ≥ KnockdownsToLose` → the other body wins, `roundReason =
      knockout`.
   3. **Round clock.** `roundTick + 1 ≥ roundTicks` → a **decision**, resolved in this exact order:
      (a) the body with **fewer knockdowns suffered** this round wins; (b) else the body **closer to
      `RingCentre`** at this tick wins (in a shrinking ring, holding the middle is the virtue), and
      `roundReason = decision`; (c) if the two centre distances are within `CentreTieUm` the round is
      a **draw** (`roundReason = draw`), and neither body scores.
   A round that ends puts the sim in `phase = RoundReset` for `resetTicks` ticks, during which the
   command byte is forced to `0` for both bodies, physics still runs (the loser keeps sliding — this
   is the watchable moment), and then the next round starts per §Time.
10. **Score bank.** On a round end, `roundMicro[winner] += RoundWinMicro + bonusMicro(roundReason)`
    (§Scoring). A draw banks nothing. Applied by **one proc**, `bankRound`, that is the same on record
    and on playback (particle-worlds 13c66d7: a fact banked outside the hashed step function
    hash-mismatches at the stop tick).
11. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
    unchanged. `gameHash` mixes `tick`, `phase`, `roundIndex`, `roundTick`, `ringRadiusNow`, and for
    each body `p`, `v`, `hMilli`, `omegaMilli`, `tipMilli`, `downTicks`, `groundedCount`,
    `knockdowns`, `contacts`, `shoveImpulseUm`, plus `roundsWon[]`, `roundMicro[]`, `rngDraws` and a
    digest of `perm`. It never mixes FX, notes, `say`, feed text or policy labels.
12. **Episode end checks**, in this order: `max(roundsWon) ≥ roundsToClinch` → end `complete` /
    `match_won`; a wall-clock stop tripped → end `deadline` / `wall_clock`; `roundIndex + 1 ≥
    maxRounds` and the round just ended → end `complete` / `full_time`; `t + 1 ≥ maxTicks` → end
    `complete` / `full_time`; an invariant guard failure (a torso centre outside the arena box,
    `|v| > MaxBodySpeedHard`, `hMilli` outside `0..31999`, `tipMilli` outside `0..1000`,
    `groundedCount` outside `0..4`, a `roundTick` above `roundTicks`, an `int32` overflow caught by
    the debug build's range checks) → end `fault` / `sim_fault`.

There is no rescue rule, no difficulty ramp and no stalling timer beyond the shrinking ring. Two bugs
that circle each other for 16.5 seconds get a `decision` on centre distance — a legible, correctly
scored outcome.

### Scoring, sign, and what the league ranks by

The game is **zero-sum by construction**.

```
RoundWinMicro   = 1_000_000        (+1.000 for winning a round)
bonusMicro(ring_out) = 250_000     (+0.250 -- the clean win)
bonusMicro(knockout) = 250_000     (+0.250 -- three falls)
bonusMicro(decision) =       0
bonusMicro(draw)     =       0     (banked to nobody)

raw[s]   = roundMicro[perm[s]] / 1_000_000
score[s] = raw[s] - raw[1 - s]
results.scores = [score[0], score[1]]        # score[0] == -score[1], exactly
results.win    = [roundsWon[0] > roundsWon[1], roundsWon[1] > roundsWon[0]]
```

**Higher is better; the two scores sum to exactly 0.000.** There is no time bonus, no thrust cost and
no participation term: the only thing that scores is winning rounds, and the only thing the bonus does
is prefer a decisive win to a points decision. Scores are emitted as doubles rounded to **3 decimals**,
and the antisymmetry is asserted bit-exactly (§Tests 9).

The reachable range is `[−3.750, +3.750]` (a 3–0 sweep of ring-outs) and `0.000` on a level match.

Worked examples:

| Outcome | rounds | detail | raw[0] | raw[1] | **score** |
|---|---|---|---|---|---|
| 3–0 sweep, all ring-outs | 3 | clinch at round 3 | 3.750 | 0.000 | **+3.750 / −3.750** |
| 3–1, two ring-outs + one knockout, one round lost on decision | 4 | clinch at round 4 | 3.750 | 1.000 | **+2.750 / −2.750** |
| 3–2, mixed | 5 | one draw is impossible at 3–2 | 2.750 | 2.250 | **+0.500 / −0.500** |
| 2–2 with one draw, full time | 5 | nobody clinches | 2.500 | 2.500 | **0.000 / 0.000** |
| 2–3 the other way, all decisions | 5 | no bonuses | 2.000 | 3.000 | **−1.000 / +1.000** |
| Both bugs circle all five rounds; every round a draw | 5 | `full_time` | 0.000 | 0.000 | **0.000 / 0.000** |

**What the league ranks by: Elo (1000 / K 32), driven by `results.win`, tie-broken by mean
`results.scores`.** Elo is **correct** for this coworld — unlike the cooperative precedents on this
starter (`cogame-raid`, `cogame-tandem`, `cogame-pistonball`, `cogame-walker-waterworld`, where four
identical scores make every episode a draw) — because this is a strictly two-sided zero-sum
head-to-head with a decided winner in every non-drawn episode. Phase 50's `round_robin` +
`elo 1000/32` template settings are used **as they stand**. `results.win` is `[false, false]` only on
an exact round-win tie, which Elo reads as a draw, which it is.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail. No
other value may appear in either field.

| `reason` | `endRule` | When | Scored |
|---|---|---|---|
| `complete` | `match_won` | A body reaches `roundsToClinch` round wins. The normal good ending. | as at the clinching round |
| `complete` | `full_time` | `maxRounds` rounds played, or `maxTicks` (2160) reached, with no clinch. | as it stands |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed first. The sim stops at that tick, banks the round in progress as a **draw**, scores the state as it stands, writes the game-over frame and a complete replay up to that tick. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. | as at the stop tick |
| `fault` | `sim_fault` | A step-12 invariant guard tripped. Partial replay written. | as at the fault tick |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts written before re-raising. | as at the fault tick |

The wall-clock stop is recorded as **one load-bearing record** applied by the same proc on record and
on playback, and `GameVersion` is bumped whenever that record's shape changes — the particle-worlds
13c66d7 scar, whose symptom was a hash mismatch at the stop tick on every slow-LLM episode. §Tests 10
runs the record → re-derive check for **every** end reason, not just `complete`.

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (720 = 30 s of
lobby) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only, `src/ctf/server.nim:1199,1539`), its bug is driven
by the `pusher` baseline for the whole run, and the match plays to a normal ending. A one-sided match
against a baseline is still a scored, watchable match.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {pusher, anchor}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=pusher`. A scripted policy seated as a champion is a FAILURE state
(`playbooks/make-coworld.md` §Definition of done).

### Where the decision happens, and the LLM client

In the **game server**, not the player container — paintbot's own architecture
(`src/ctf/llm.nim`, `src/ctf/decide.nim`, `src/paintball_player.nim`), kept. The `anthropic_api_key`
coworld secret is injected into the *game* pod via
`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/physics-bodies/anthropic_api_key`;
without that manifest env the hosted container never receives the secret and every league episode
plays scripted while local certify still passes (hive, 2026-08-23). Phase 60 greps the *game* log for
`falling back` / `LLM provider is unavailable`.

`src/bodies/llm.nim` is `src/ctf/llm.nim` with the identifier rename only. Kept exactly:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (`readCogameUri`) → **none** (client
  `disabled = true`; every turn falls back instantly with no network wait, which is what lets offline
  certification finish in seconds).
- **One** Bedrock model candidate: `us.anthropic.claude-haiku-4-5-20251001-v1:0`
  (`src/ctf/llm.nim:87`). No sonnet inference profile is a candidate — every one of them times out on
  every sidecar call (cogame-raid round 2, 2026-08-23). The `throttled` fast-fail that skips the retry
  when the provider answered 429 with no other candidate is kept verbatim: a retry inside the same
  turn cannot succeed.
- `max_tokens = 900` (400 truncates). **No `output_config.effort`** for haiku. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`. No `temperature`.
- A system prompt that demands the reply **begins with `{`** (Haiku answers prose-first otherwise).
- `extractJsonObject` (first `{` … last `}`, fence-tolerant) and the **rune-boundary** truncation
  (`runeLen`/`runeSubStr`, `src/ctf/directives.nim:61-68`), kept.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **K = 36 ticks (1.5 s of sim time)**, **60 turns** per full-length episode. At
each turn the server builds **both** seats' request bodies and issues them as **ONE parallel batch** —
`client.curl.makeRequests(@[req0, req1], timeout)`, curly's batch API, which is exactly what
`src/ctf/decide.nim:427` already does. **Seats are never queried sequentially** (that is the documented
way to blow the 720 s budget). Two calls per turn × 60 turns = **120 calls** per episode, at most 2 in
flight.

The binding constraint is not latency, it is the **Bedrock sidecar's cap of 30 requests per minute per
episode** (playbook gotcha, raid round 2, whose rail is "≥ 4 s between batches for 2 seats"). Two
requests per batch at **`turnSpacingMs` (ctf's `turnSpacingMs`) = 6 000** is 2 requests / 6 s =
**20 rpm**, comfortably under the cap with a 50 % margin. That, not the model, is why there are 60
turns and why a turn is 1.5 s of sim time.

Per-turn timing, all monotonic-deadline bounded, and every deadline a whole number of seconds because
curly hands it to `CURLOPT_TIMEOUT`, whose granularity is whole seconds and whose conversion **floors**
(`src/ctf/decide.nim:399-428`):

- attempt 1 batch deadline **`attempt1Ms = 9 000`** (two parallel haiku calls; ~3–6 s typical);
- every seat that timed out, errored, returned non-JSON or returned no usable intent is retried
  **once**, again as a single batch, deadline **`retryMs = 5 000`** — unless the client is `throttled`,
  in which case the retry is skipped outright;
- the whole turn is wrapped in **`turnBudgetMs = 16 000`** (`attempt1Ms + retryMs = 14 000 ≤ 16 000`,
  asserted by §Tests 12);
- the **inter-batch wall floor** of 6 000 ms is measured start-to-start and is a bounded,
  stop-interruptible `sleep` (`src/ctf/decide.nim:386-389`).

```
turn 0 batch starts at t = 0; turns 1..59 start 6 s apart        = 354 s
last turn's own LLM cost (<= 16 s hard cap)                      =  16 s
lobby / connect wait for 2 player pods (typical 12 s;
  cap lobbyJoinTimeoutTicks 720 = 30 s)                          =  12 s   (typical)
2160 ticks of physics + 4320 controller evaluations              =   1 s
game-over hold + results + replay write (retrying uploader)      =  20 s
                                                                 -------
expected total                                                   ~403 s   < 720 s budget
absolute worst case (30 lobby + 354 + 16 + 1 + 20 + 30 slack)    ~451 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                          = 660 s  -> reason "deadline"
platform kill (episodeTimeoutSeconds)                            = 1200 s
```

`fastMode: true` in every variant: the sim advances as soon as every player container has
acknowledged the frame, so sim time is not charged against the wall clock — the decision turns are the
pacing. The seats send no inputs at all (the server computes every command byte), so
`docs/PROTOCOL.md`'s warning about the Sprite v1 Ready packet (`0x85`) corrupting dead-reckoned input
timing does not apply, and the player harness sends `0x85` after every frame exactly as
`src/paintball_player.nim` does.

**Budget guard (settles early without shortening the match).** At the start of each turn, if
`elapsed + 2 × (turnSpacingMs + turnBudgetMs) / 1000 > wallClockBudgetSeconds`, the LLM is switched
off for every remaining turn and the match finishes on the scripted layer (microseconds per turn), so
the episode ends `complete/*` rather than `deadline`. A `budget_guard` record names the turn it fired.
This is ctf's own guard (`src/ctf/decide.nim:335-346`), retargeted to include the batch spacing.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the inter-batch floor, the
outer per-turn deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the
serve thread (which runs independently of the game loop, so a 16 s LLM stall cannot drop two
connections), the 660 s engine stop, and ctf's `gameOverTicks` hold before exit. On **two**
consecutive failures for a seat (attempt + retry, or one attempt when `throttled`) that seat's intent
for the turn is the **`pusher`** intent and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}`. A seat
that disconnects mid-match keeps playing: its intent source degrades to `pusher` and revives on
reconnect. **No failure mode leaves a bug uncommanded** — the controller always has an intent: this
turn's, else last turn's, else `pusher`'s. There is no sampling loop, no unbounded search and no
retry-until-success anywhere in the sim.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are ONE of TWO four-legged robot bugs in a round sumo ring, seen from
above. Coordinates are metres from the arena's bottom-left corner; x runs
right, y runs up. Bearings are degrees counter-clockwise from east: 0 = right,
90 = up, 180 = left, 270 = down. The ring is a circle centred on (4.80, 3.20).
It starts 3.00 m in radius and SHRINKS from 6 seconds into every round, down to
1.80 m. There is nothing outside it.
HOW YOU WIN A ROUND: the other bug's body centre crosses the rim (a RING OUT),
or you knock it down THREE times. If the round clock runs out, the bug with
fewer knockdowns wins, and if that is level, the bug CLOSER TO THE CENTRE wins.
Best of five rounds wins the match. Every round you win is +1 to you and -1 to
the other bug: this is strictly zero sum.
HOW A BUG MOVES: you push with the leg that has floor under it. A leg whose
foot is over the rim finds NO FLOOR - standing near the edge costs you push and
costs you balance. Posture matters: LOW is wide, slow, hard to move and hard to
tip; HIGH is tall and fast but tips easily; LIFT gets under the other bug and
levers it over, at some risk to yourself.
TILT: off-centre hits, your own spin, standing tall and being levered all fill
your tilt gauge. Full tilt and you FALL DOWN for 1.5 seconds - you cannot push
and you can be shoved straight out while you lie there.
Every 1.5 seconds you set your ORDER for the next 1.5 seconds. A deterministic
autopilot runs it 24 times a second: it steers, it leads a moving target, it
keeps you off the rim unless you tell it not to. You choose WHAT to do and HOW
hard. You CANNOT talk to the other bug and it never sees anything you write.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars, your reasoning",
 "stance":"charge"|"brace"|"circle"|"lift"|"retreat"|"centre",
   // charge  : drive into the other bug where it WILL be in lead_ticks, and
   //           shove. The bread and butter.
   // brace   : plant LOW facing the other bug and absorb. You barely move,
   //           you take less tilt, and a bug that charges a brace bounces.
   // circle  : orbit the other bug at about 1.40 m in circle_dir, trying to
   //           end up with the rim behind IT and the centre behind YOU.
   // lift    : close and get under it - the knockdown attempt. Slow, and it
   //           loads tilt onto you too.
   // retreat : back toward the ring centre away from the other bug.
   // centre  : walk to the ring centre and hold it. Wins a decision.
 "aim":"foe"|"centre"|"bearing",   // what "charge"/"circle" point at
 "bearing_deg":0..359,             // only read when aim is "bearing"
 "aggression":0..10,               // 0 = coast, 10 = all in. At 10 the
                                   // autopilot's rim guard is HALVED: you may
                                   // push yourself out. That is the trade.
 "posture_bias":"low"|"even"|"high"|"auto",
 "lead_ticks":0..24,               // aim where it will be this many ticks from
                                   // now (24 ticks = 1 second)
 "circle_dir":-1 or 1,             // -1 = clockwise, 1 = counter-clockwise
 "say":"<=48 chars"}               // spectators only; the other bug never sees it
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(paintbot's `operatorBlock`, kept), a blank line, then the seat's observation JSON (§Server). The
prompt text is never echoed into the replay — only `policyKind`, the label and the resulting intent.

### Champion #1 — `physics-bodies-ringcraft` (owner daveey), `PLAYER_PROMPT`

```
Win on position, not on violence. Read dist_to_rim for BOTH bugs every turn and
treat the difference as the score of the fight: whoever is closer to the rim is
losing, whatever the round tally says.
Rules, in order. If YOUR dist_to_rim is under 0.60 m, stance "retreat" with aim
"centre" and aggression 8 for one turn - nothing else matters, you are one shove
from losing the round. Otherwise, if the other bug's dist_to_rim is under 0.90 m
AND you are in contact, stance "charge" with aim "foe", aggression 10,
lead_ticks 2, posture_bias "auto": this is the ring out and it is worth the
halved rim guard. Otherwise, if the other bug's dist_to_rim is under 1.40 m,
stance "charge", aggression 8, lead_ticks 4, posture_bias "even" - close the
distance but keep your feet.
Otherwise, if you are in contact and neither of you is near the rim, stance
"brace" with posture_bias "low" and aggression 6. A brace beats a charge: let
it spend itself on you, take the smaller tilt, and let the shrinking ring do
the work. Otherwise, if you are further than 1.60 m from the centre, stance
"centre" with aggression 6 - holding the middle wins every decision and every
shrink.
Otherwise stance "circle", circle_dir whichever sign puts the rim behind the
other bug (positive if it is above you in y, negative if below), aggression 4,
posture_bias "even".
Never set posture_bias "high" while in contact and never use "lift": a lift
loads tilt onto you too, and you do not need falls to win this way.
```

### Champion #2 — `physics-bodies-toppler` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win by putting it on its back. Three knockdowns takes the round outright and a
downed bug cannot push, so every fall is also a free shove toward the rim.
Rules, in order. If YOUR tilt_pct is above 55, stance "brace", posture_bias
"low", aggression 3 for one turn and let your legs recover it - a bug that
falls first gives the round away. If YOUR dist_to_rim is under 0.50 m, stance
"retreat", aim "centre", aggression 9.
Otherwise, if the other bug is DOWN (its down_ticks above 0), stance "charge",
aim "foe", aggression 10, lead_ticks 0, posture_bias "even": you have about a
second of free pushing, spend all of it driving it at the nearest rim.
Otherwise, if you are in contact, stance "lift" with aggression 9 and
lead_ticks 0. Stay in it: lift only works while you are touching, and the tilt
you load takes about a second and a quarter of continuous contact to land.
Otherwise, if the other bug's tilt_pct is above 40 OR its posture reads "high",
stance "charge", aggression 9, lead_ticks 4, posture_bias "high" - it is
already unstable, so hit it hard and off-centre rather than squarely.
Otherwise, if it is further than 1.80 m away, stance "charge", aim "foe",
aggression 7, lead_ticks 8, posture_bias "even".
Otherwise stance "circle", circle_dir 1, aggression 5, posture_bias "even",
waiting for it to commit so you can take the contact on your terms.
Never brace at aggression above 4 and never charge a bug that is bracing low at
aggression 10 - you will bounce and spin, and a spin fills your own tilt.
```

### The controller (deterministic, one function, shared by every policy)

`src/bodies/control.nim`, `driveCommand(sim, i) -> uint8`, evaluated once per tick per body in index
order. Both LLM intents and scripted-baseline intents are compiled by this same code, so the two
policy kinds are strictly comparable and a baseline is legal by construction. It sits **outside** the
determinism boundary (ctf's rule: recorded bytes, not re-run logic) and may use floats.

With `p` = my torso centre, `v` = my velocity, `q, u` = the other bug's centre and velocity,
`C = RingCentre`, `R = ringRadiusNow`, `I` = my seat's active intent:

1. **Aim point `A`.** `I.aim == "foe"` → `A = q + u · I.lead_ticks`; `"centre"` → `A = C`;
   `"bearing"` → `A = p + 4 m · unit(I.bearing_deg)`.
2. **Goal bearing `g` (a float bearing, quantised at step 6).**
   - `charge` → toward `A`.
   - `brace` → toward `A` (you face what you are absorbing); the *speed* target is 0 (step 5).
   - `circle` → the tangent at `p` around `q` in direction `I.circle_dir`, biased by
     `(1.40 m − |p − q|) / 1.40 m` radially so the orbit radius converges on `CircleRadiusUm =
     1 400 000`.
   - `lift` → toward `A` while `|p − q| > liftEngageUm`; once inside, toward `q`'s centre exactly
     (you need the contact, not the lead).
   - `retreat` → the normalised sum of `unit(p − q)` and `unit(C − p)`, so you back off *and* inward.
   - `centre` → toward `C`.
3. **Rim guard (always, every stance).** With `d = |p − C|` and
   `w = clamp((d − (R − rimGuardUm)) · 100 / rimGuardUm, 0, 100)`, and `w := w / 2` when
   `I.aggression == 10`: `g := bearing(unit(g) · (1 − w/100) + unit(C − p) · (w/100))`. This is the
   one thing that stops the controller walking a bug out of its own ring, and halving it at
   aggression 10 is the *only* way a policy can order an all-in push — stated in the system prompt so
   it is a choice, not a trap. §Tests 4 asserts a bug driven by any stance at aggression ≤ 9 from any
   legal state never crosses the rim under its own drive over 10 000 randomised starts.
4. **Posture.** `I.posture_bias ∈ {low, even, high}` is taken literally. `auto` resolves as: `lift`
   stance and in contact → `lift`; `brace` stance → `low`; `|p − q| > 1.20 m` → `high`; in contact →
   `low`; else `even`. The rim guard overrides to `low` whenever `w ≥ 60`. A body with
   `downTicks > 0`, or any phase other than `Playing`, forces `cmd = 0`.
5. **Effort (continuous, then duty-cycled).** Requested continuous effort
   `e = 3 · I.aggression / 10`, times `0.35` for `brace` when not in contact and `0` for `brace`
   within 0.05 m of a standstill, times `taper(|A − p|)` for `centre`/`retreat` (linear to 0 inside
   0.30 m of the goal so a bug parks instead of orbiting). The byte's `effort` is
   `floor(e + acc[i])` clamped to `0..3`, where `acc[i] ∈ [0,1)` is a per-body error-diffusion
   accumulator updated `acc[i] += e − effort`. That is how a 4-level byte at 24 Hz delivers a
   continuous force.
6. **Quantise.** `drive =` the index of the 16 drive bearings (`DirQ12[2·drive]`) nearest in angle to
   `g`; `cmd = drive · 16 + posture · 4 + effort`.

The controller keeps **no memory across ticks except `acc[i]` and the last drive bearing**, and no
knowledge of the other seat's intent, `note`, `say`, prompt or policy label —
`tests/test_observation.nim` asserts the signature cannot see them.

### Scripted baselines

Both emit the *same* intent object on the same 36-tick cadence, so their output is legal by
construction and directly comparable to an LLM's, and both are pure functions of the observation a
seat would receive.

- **`pusher`** — the certification player, the per-turn fallback, and the default for a seat that
  registers with neither env var. **Algorithm, evaluated once per turn:**
  1. If `downTicks > 0` or `tipMilli > 700` → `{stance: brace, posture_bias: low, aggression: 2}`.
  2. Else if `myDistToRim < rimGuardUm` → `{stance: retreat, aim: centre, aggression: 6}`.
  3. Else if in contact **and** the other bug is closer to the rim than I am →
     `{stance: charge, aim: foe, aggression: 10, posture_bias: auto, lead_ticks: 2}`.
  4. Else if in contact → `{stance: lift, aggression: 8, lead_ticks: 0}`.
  5. Else if `|p − q| > liftEngageUm × 2` →
     `{stance: charge, aim: foe, aggression: 8, lead_ticks: chargeLeadTicks}`.
  6. Else → `{stance: charge, aim: foe, aggression: 9, lead_ticks: 2}`.
- **`anchor`** — the second filler, deliberately different in shape and weaker: it never initiates.
  1. If `|p − C| > 500 000 µm` → `{stance: centre, aggression: 5}`.
  2. Else if in contact → `{stance: brace, posture_bias: low, aggression: 7}`.
  3. Else if `|p − q| < 1 500 000 µm` → `{stance: brace, posture_bias: low, aggression: 4}`.
  4. Else → `{stance: circle, circle_dir: (if roundIndex is odd: −1 else +1), aggression: 3}`.
  An `anchor` wins decisions and loses to sustained pressure, which gives the ladder a spread and
  gives a champion a stubborn opponent to solve.

`say` on each baseline is one of four fixed strings chosen by which branch fired.

Three tunables — `rimGuardUm` (600 000), `chargeLeadTicks` (6) and `liftEngageUm` (820 000) — are a
`BaselineParams` object, not literals, exactly as `src/ctf/baselines.nim` does it (its
`DefaultBaselineParams` comment is the template): `tools/tune_baselines.nim` sweeps them over a
bounded grid, `tools/ci/baseline_tuning.json` records the sweep's pick, and `tests/test_tuning.nim`
asserts the shipped defaults still equal it. **The physics constants in §The game are not swept and
are not tunable** — if `pusher` cannot beat `anchor`, the sweep moves these three numbers, not the
sim.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf/paintball arena rules go** (teams, guns, flags, fog cones, lives, respawn,
grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the hill, the
paint grid, the map pool and the map editor all leave the repo):

| ctf path | physics-bodies |
|---|---|
| `src/ctf/sim.nim` (4102 lines: gameplay core, combat, vision, items) | `src/bodies/sim.nim` — the body/ring physics core and the step loop of §Resolution order. |
| `src/ctf/sim_types.nim` | `src/bodies/sim_types.nim` — the constant tables of §The game, `Posture`, `RoundReason`, `Phase` (`Lobby, Playing, RoundReset, GameOver`), and the per-body record. `TargetFps`, `ReplayFps`, `PlaybackSpeeds`, `LullLeadTicks`, `MinLullTicks`, `MaxPolicyLabelRunes`, `MaxSayRunes`, `MaxNoteRunes` **kept verbatim**. |
| `src/ctf/arena.nim`, `paint.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `tools/map_render.nim`, `docs/MAPKIT.md`, `docs/pool-review.html`, `scripts/` | `src/bodies/ring.nim` — the fixed ring geometry, the shrink law, the seeded `perm`, the seeded per-round start axis and end swap, the swept disc-contact tests, and the pixie ring bake. **Deleted, not ported**; there is no map generator, no `mapSpec`, no wall mask and no procedural terrain in this coworld. |
| — (new) | `src/bodies/body.nim` — the leg kinematic: reach by posture, the four foot positions, `groundedCount`, the yaw servo, and the command-byte decode (`decodeCommand(cmd): tuple[drive, posture, effort: int32]`). |
| `src/ctf/global.nim` (8070 lines) fog of war, vision cones, first-person raycast, killfeed art, item sprites | `src/bodies/global.nim` — top-down sprite composition: clay ring, painted rim, the shrinking rim arc, two bug hulls with four **individually positioned** legs, dust puffs at loaded feet, tilt gauges, impulse bursts, FX. Perfect information both sides. `boardRenderScaleFor`, `MaxSupersampledMapPixels`, `predictedViewerRenderBytes`, `WasmViewerBudgetBytes` and `shoutBubbleZoomFor` are **kept verbatim**. |
| `src/ctf/directives.nim` (`Intent`, `CogOrder`, `SquadDirective`) | `src/bodies/intents.nim` — the `BugIntent` object, the closed `Stance`/`Aim`/`PostureBias` enums, the tolerant parser and the repair table of §Server. Same file shape, same rune discipline (`truncateRunes`, `sanitizeSay`, the no-leading-brace rule for `say`). |
| `src/ctf/control.nim` (nav grid, flow fields, aim) | `src/bodies/control.nim` — `driveCommand` of §Decisions. ~200 lines instead of 536; no nav grid, no flow field, no cached fields. |
| `src/ctf/baselines.nim` (`holdline`, `sprayer`) | `src/bodies/baselines.nim` — `pusher`, `anchor`, and `BaselineParams`. |
| `players/baseline/` (the CTF bot) | deleted; the only player binary is `src/physics_bodies_player.nim`. |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/paintball/`, `docs/plans/*` | rewritten for physics-bodies; ctf's plans/designs deleted. |
| `arena/`, `caos/`, `caos-tools/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/render_map_pool.nim`, `tools/build_pool_review.py`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf`/`paintball` → `bodies` rename sweep only, `CTF_WIRE` →
`BODIES_WIRE`; a CI grep asserts no `ctf_`/`CTF_`/`paintball` identifier survives outside comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/bodies/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `writeInputMaskChange` (used **as-is**: our command byte is a value and `writeInputMaskChange` already writes change-only), `checkReplayHash`. Two named edits below. |
| `src/ctf/replay_runtime.nim` → `src/bodies/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports. |
| `src/ctf/server.nim` → `src/bodies/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the **`Ping → Pong` branch** (`src/ctf/server.nim:895` — losing it is a cert `game_contract_violation`, seen twice: lux-ai 0.1.0, snake-royale 0.1.0; and **nothing else in `websocketHandler` is guarded** — a `kind != TextMessage` guard drops the player's binary registration frames), the held-registration table (`:1730`), the frame limiter, the replay-switch path, the `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. Five named edits below. |
| `src/ctf/llm.nim` → `src/bodies/llm.nim` | the credential ladder, the single-haiku model list, the `throttled` fast-fail, `curly.makeRequests` batching, `extractJsonObject`, rune truncation. Rename only. |
| `src/ctf/decide.nim` → `src/bodies/decide.nim` | the turn loop, `SeatPolicy`, the two-deadline retry, the inter-batch floor, the budget guard, `repairMissingOrders` (retargeted: a missing field keeps last turn's value, else `pusher`'s), the `records` queue. It is already a loop over `sim.seatCount()` seats that batches them, so retargeting from 2 to 2 seats is a no-op. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/sim_config.nim` | `GameConfig` lifecycle and `config.update`; physics-bodies' fields replace the arena's. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; physics-bodies result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim` | HUD label composition. |
| `src/ctf/broadcast.nim` | `stepEvents` / `BroadcastTracker` / `buildStateJson` — the state-delta → broadcast-event derivation, retargeted to physics-bodies' event kinds and state keys (§Viewer). |
| `replay-viewer/config.nims`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/chrome_common.js` | **byte-for-byte**, zero edits (§Viewer). |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome, with a game block appended (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/wasm_replay_smoke.cjs`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix`, `flake.lock`, `config.json` | build, bundle, tuning and forensics wiring. `tools/build_replay_viewer.sh` already carries the ecos `mkdir -p` fix at lines 20 and 30 and keeps it; only `image_tag` and the `docker cp` source path `/workspace/bodies/replay-viewer/dist/.` change. |
| `data/font.ttf`, `data/FONT_LICENSE.txt`, `data/arena_floor.png`, `data/darkbg.png`, `data/ascii.png`, `data/atlas/*`, `client/art/walls/*`, `client/art/lockerroom/bg.jpg` | real art, kept. Everything CTF-specific (`soldier_*`, `heart_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, `crew.png`, `rig_real/`, the coloured locker-room sprites) is deleted. |

**The five named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   physics-bodies calls `control.driveCommand(sim, i)` for both bodies and passes the command-byte
   array into `sim.step`. **Player sockets contribute no input**: any input mask arriving on a player
   socket is discarded.
2. **Replay input write.** `writeInputFrameMasks` (the press/release wrapper at
   `src/ctf/server.nim:1088`) is **deleted** — its `repeatedPressedMask` logic is button semantics and
   would corrupt a value byte. physics-bodies calls
   `replayWriter.writeInputMaskChange(tickTime(tick), seat, cmd)` directly (the codec's own
   change-only guard does the rest), and `decodeInputMask` is replaced by
   `body.decodeCommand(cmd: uint8)`.
3. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop
   runs `decide.turn(sim, engine, …)`, which enforces the inter-batch floor, issues the one parallel
   two-request batch, applies the deadlines, installs the intents and writes the `intent`/`fallback`
   records — all inside a monotonic `turnBudgetMs` bound.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration writes
   **one load-bearing `stop` record** and forces `phase = GameOver`, `reason = deadline`,
   `endRule = wall_clock`, applied by the same proc on record and playback (particle-worlds 13c66d7).
5. **Shutdown grace.** `/healthz` and `/global` keep answering for a bounded ~20 s after the artifacts
   are written, then the process exits (lantern 0.1.3: the episode runner pings `/global` with a 2 s
   deadline *after* the player pods start, and a short episode can already be gone).

**The two named edits to `replays.nim`:**

1. **`serializeReplaySim`/`deserializeReplaySim` cover the new sim fields** — for each body `p`, `v`,
   `hMilli`, `omegaMilli`, `tipMilli`, `downTicks`, `knockdowns`, `contacts`, `shoveImpulseUm`,
   `lastPosture`; plus `roundIndex`, `roundTick`, `ringRadiusNow`, `roundsWon[]`, `roundMicro[]`,
   `roundLog[]`, `rngDraws`, the RNG state, `phase`, `targetTick` — because keyframes are how the
   viewer seeks. The static geometry and `perm` are **excluded** from keyframes (they are already in
   the config JSON — ctf's own rule for static bakes).
2. **`CtfReplayMagic "COWLDCTF"` → `BodiesReplayMagic "COWLDPBD"`**, `GameName* = "physics-bodies"`,
   `GameVersion* = "1"`, with ctf's prepend-only changelog-comment discipline
   (`GV1 (ring rules): two four-legged bugs, ring-out, 3-knockdown knockout, shrinking ring`) and
   `tools/ci/check_gameversion.sh` kept as is.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`; `tools/wasm_replay_smoke.cjs`). So:

- Every stored sim field is explicitly `int32` (positions, velocities, headings, yaw, tilt, radii,
  counters), `int64` (the score accumulators), `uint8` (direction indices, command bytes) or
  `bool`/`enum`. **No bare `int` in a hashed field.**
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with an
  explicit truncating `div` (Nim's `div` truncates toward zero, so friction, yaw drag, reflection and
  lead arithmetic are all symmetric under negation).
- **No floating point anywhere under `src/bodies/{sim,ring,body,trig,sim_types,sim_config,
  sim_state}.nim`.** No `sin`, `cos`, `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`.
  Grep-enforced in CI. Floats stay legal in `control.nim`, `global.nim` and the pixie bakes, because
  neither the controller (recorded, not re-run) nor rendering enters `gameHash` — exactly ctf's split.
- Trigonometry is the committed `DirQ12` table (32 entries) plus `isqrt`. Nothing else.
- Randomness: one seeded stream, every draw through
  `drawInt(lo, hi: int32): int32 = int32(lo + int32(rng.next() mod uint64(hi - lo + 1)))` on
  `std/random`'s `uint64`-domain step, so **no draw ever touches `rand(int)`**, whose `int` is 32-bit
  under `--cpu:wasm32` and 64-bit natively (ctf's documented hazard). A monotonic `rngDraws` counter is
  mixed into `gameHash`, so a divergence in *how many* draws a build took is caught at the tick it
  happens. Exactly `1 + 5` draws happen per episode: `perm` at `t = 0`, then one start-axis index per
  round; there is no rejection sampling anywhere and therefore no unbounded loop in the step function.

### How the replay achieves server ↔ viewer determinism

The mechanism is ctf's, unchanged:

1. The server writes a `COWLDPBD` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `perm`, every geometry and physics constant, the roster with real
   names), then the record stream — joins, leaves, **per-tick command-byte change records**, chat
   records (`register`, `intent`, `fallback`, `budget_guard`, `stop`, `round`, `result`) and **one
   `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/bodies_replay.nim` — which imports the
   **same** `src/bodies/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + `nimby 2.2.4`
   container in `Dockerfile.replay-viewer`.
3. In the browser, `bodies_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `bodies_frame` re-steps the sim from the **recorded command bytes** and compares `sim.gameHash()`
   against the recorded hash **every tick** (`checkReplayHash`). One divergent bit is caught at the
   tick it happens, surfaced as `mismatchTick` in the chrome (`#mmwarn`) and, in CI, as a hard failure.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle and
   runs `tools/ci/viewer_smoke.mjs` against the replay `docker-smoke` produced (§Tests), which fails
   if the viewer errors, never draws, freezes, or reports a mismatch tick.

Perf target: 2160 ticks of physics + 4 320 controller evaluations in under 3 s on a CI runner;
`tests/test_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

`src/bodies/server.nim` is ctf's `server.nim` with the five edits above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`) — **both `/client/` routes serve real
pages, registered before any catch-all asset route, and neither opens the player socket** (lantern
0.1.1: the certifier probes them before starting player pods). **A player websocket whose token does
not match the seat is closed** (the certifier probes `?slot=0&token=bad` and a fresh-written server
that accepts it fails cert `smoke-episode` — cogame-flatland 0.1.1; ctf's handler already closes, and
that behaviour is kept). Same `COGAME_*` runtime contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`,
`COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`,
`COGAME_METRICS_URI`, `COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same
done-before-artifact-writes ordering, same entrypoint shape (`src/physics_bodies.nim`, where seed
randomisation happens **before** `config.update` so every seed-derived draw follows the final seed).

### The player container

`src/physics_bodies_player.nim` (built to `/bin/physics-bodies-player`) is
`src/paintball_player.nim` with the baseline names changed. It reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED`, `PLAYER_POLICY_LABEL`, dials with the starter's bounded retry
(240 × 500 ms), and sends **one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"pusher"|"anchor"|null,"policy":"<free label>"}
```

It re-sends the registration on the starter's `RegistrationResends`/`ResendEveryFrames` schedule (the
server's held-registration table, `src/ctf/server.nim:1730`, is kept — a seat's first registration can
arrive before its player index exists, and dropping it was a real paintball scar). The server
**logs loudly and refuses to treat a seat as scripted-by-default silently** when no register record
ever arrives: it prints `physics-bodies: seat N never registered; driving BUG-<i+1> with pusher` once
per seat, and `results.policyKinds[N]` records `scripted` with `results.llmTurns[N] == 0`, so a lost
register packet is auditable from the replay rather than invisible (grf-football round 2, 2026-08-27).
It then sends the Sprite v1 Ready packet (`0x85`) after each received frame and otherwise only
receives. **The receive loop is wrapped in `try/except CatchableError` and exits 0 on a dead socket** —
whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues, so the game's
`quit(0)` can outrun the flushed `done` frame (raid 0.1.3 → 0.1.4). A seat that never registers, or
registers with neither field, is `scripted: "pusher"`.

Player container resources in the manifest: `requests {cpu: 100m, memory: 64Mi}`,
`limits {cpu: "1"}` — the bundled-player `limits.cpu` minimum is `"1"` and anything lower is a 400 at
upload (pistonball 0.1.1, 2026-08-26).

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates`. **This game is perfect-information on the physics**: the
ring is lit and both bodies are in it, so the frame carries the ring, the current rim radius, both
bugs with all eight feet, both tilt gauges and both round tallies. Board labels carry only `BUG-1` /
`BUG-2`; `showPlayerLabels` is forced false on the player stream. What a seat does **not** get is
listed under §Hidden below — it is the *other seat's mind*, not the world.

### The per-seat view given to the LLM

Numbers rounded to 2 decimals, in **view coordinates** (metres, origin bottom-left, y up) and degrees
counter-clockwise from east. This object is the tail of the LLM user message; the scripted baselines
are pure functions of the identical object.

```json
{"turn": 24, "of": 60,
 "clock": {"tick": 864, "of": 2160, "round": 3, "of_rounds": 5,
           "round_tick": 0, "round_of": 396, "round_left_s": 16.5},
 "ring": {"centre": [4.80, 3.20], "radius_m": 3.00, "min_radius_m": 1.80,
          "shrink_starts_in_s": 6.0, "radius_at_round_end_m": 1.99},
 "you": {"alias": "BUG-1", "body": 0, "pos": [3.31, 4.28], "vel": [1.02, -0.41],
         "speed_m_s": 1.10, "heading_deg": 338.0, "spin_dps": -12.4,
         "posture": "even", "effort": 2, "reach_m": 0.46,
         "tilt_pct": 18, "grounded_legs": 4, "down_ticks": 0,
         "dist_from_centre_m": 1.85, "dist_to_rim_m": 1.15,
         "feet": [[3.77, 4.11], [3.14, 3.82], [2.85, 4.45], [3.48, 4.74]]},
 "foe": {"alias": "BUG-2", "body": 1, "pos": [5.94, 2.40], "vel": [-1.31, 0.52],
         "speed_m_s": 1.41, "heading_deg": 158.0, "spin_dps": 5.1,
         "posture": "low", "effort": 3, "reach_m": 0.62,
         "tilt_pct": 41, "grounded_legs": 4, "down_ticks": 0,
         "dist_from_centre_m": 1.42, "dist_to_rim_m": 1.58,
         "bearing_from_you_deg": 342.0, "range_m": 2.90,
         "closing_m_s": 2.31},
 "contact": {"in_contact": false, "normal_deg": null,
             "your_impulse_last_turn": 0.00, "their_impulse_last_turn": 0.00},
 "match": {"rounds_won": {"you": 1, "foe": 1}, "to_clinch": 3,
           "knockdowns_this_round": {"you": 0, "foe": 0},
           "ring_outs": {"you": 1, "foe": 0},
           "round_log": [{"round": 1, "winner": "BUG-1", "reason": "ring_out"},
                         {"round": 2, "winner": "BUG-2", "reason": "decision"}]},
 "rules": {"knockdowns_to_lose": 3, "round_win_points": 1.0,
           "ring_out_bonus": 0.25, "knockout_bonus": 0.25,
           "zero_sum": true,
           "note": "a leg whose foot is over the rim has no floor: no push, no balance recovery"},
 "your_last_intent": {"stance": "charge", "aim": "foe", "bearing_deg": 0,
                      "aggression": 8, "posture_bias": "auto", "lead_ticks": 6,
                      "circle_dir": 1}}
```

**Hidden from every seat, with no exception:**

- The other seat's **intent object, `note`, `say`, prompt text, latency, `policyKind`, policy label
  and fallback state.** A seat sees the other *body's* physical state and nothing about the *mind*
  driving it. (`foe.posture` and `foe.effort` are the physical consequences of last tick's byte, which
  are visible on the board and to any spectator, so withholding them would be a lie about the world.)
- Which entrant holds the other seat, and any real player name anywhere (board labels carry only
  `BUG-n`; `showPlayerLabels` is forced false on the player stream).
- `perm`, `config.seed`, the RNG state, the future start axes, and the variant name.
- Future ticks; the per-seat score decomposition beyond `match` (which is symmetric and legitimately
  public — this is a zero-sum game with an open score).

`tests/test_observation.nim` asserts all of it against the composed LLM user message over randomised
states (§Tests 8).

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "it is low and braced; circle to put the rim behind it before I commit",
 "stance": "circle", "aim": "foe", "bearing_deg": 0,
 "aggression": 5, "posture_bias": "even", "lead_ticks": 4, "circle_dir": 1,
 "say": "walking it to the edge"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `stance` | string | **≤ 8 runes**, closed enum `charge, brace, circle, lift, retreat, centre`, case-insensitive | unrecognised / missing → last turn's `stance`, else `charge` |
| `aim` | string | **≤ 8 runes**, closed enum `foe, centre, bearing`, case-insensitive | unrecognised / missing → `foe` |
| `bearing_deg` | integer | finite, taken `mod 360` into `0..359`, rounded | non-finite / missing → last turn's value, else `0` |
| `aggression` | integer | finite, clamped `[0, 10]`, rounded | non-finite / missing → last turn's value, else `7` |
| `posture_bias` | string | **≤ 5 runes**, closed enum `low, even, high, auto`, case-insensitive | unrecognised / missing → `auto` |
| `lead_ticks` | integer | finite, clamped `[0, 24]`, rounded | non-finite / missing → `4` |
| `circle_dir` | integer | `−1` or `+1`; any other value takes the sign (`0` → `+1`) | non-finite / missing → last turn's value, else `+1` |
| `say` | string | **≤ 48 runes** | truncated to 48 runes, then ctf's printable-ASCII shout sanitiser (which also strips a leading `{`, since the replay chat stream distinguishes control records by it) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**
(`MaxPolicyLabelRunes`, `src/ctf/sim_types.nim:796`), any recorded error text (`fallback.detail`)
**≤ 200 runes** (`MaxFallbackDetailRunes`), and the whole serialized `intent` record **≤ 480 runes**,
asserted in `tests/test_replay.nim`. `register.prompt` is capped at **≤ 4000 runes** at the transport
(over-long is truncated, never rejected) and is **never** written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — in Nim, `runeLen` /
`runeSubStr` (ctf's `directives.nim:61-68` rune discipline, kept verbatim as `intents.nim`). Slicing a
`string` by byte index on any path to the replay is forbidden: a byte-truncated multi-byte character
renders in a browser and then fails a strict UTF-8 parser. §Tests 6 pins it with a 4-byte emoji
sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose (`extractJsonObject`); accept numeric strings; accept `aggression` given as a
percentage (`0..100`) and divide by 10 when the value exceeds 10; accept `bearing_deg` in radians when
`|value| ≤ 6.3` and convert; accept `circle_dir` as `"cw"`/`"ccw"`/`"left"`/`"right"`; accept
`stance`, `aim` and `posture_bias` case-insensitively and with surrounding whitespace; accept
`lead_ticks` given in seconds when the value is a decimal below 2 and multiply by 24; accept
`stance: "push"` as `charge` and `"hold"` as `brace`. Only when no object with at least one usable
field can be recovered do the retry and then the fallback fire. **The observation already carries the
legal choice set** (`rules` plus the enum names in the system prompt), which is the escrow 0.1.3
remedy for formal-output fallback rates.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, physics-bodies keys) to `COGAME_RESULTS_URI`.
It must equal the manifest's `results_schema` key-for-key — that schema is
`additionalProperties: false` and the certifier rejects any unknown field. Adding or removing a key
here means editing `coworld_manifest_template.json` in the same commit. **21 keys:**

```json
{"names": ["daveey", "daveey-1"],
 "aliases": ["BUG-2", "BUG-1"],
 "bodies": [1, 0],
 "policyKinds": ["llm", "llm"],
 "scores": [2.75, -2.75],
 "win": [true, false],
 "roundsWon": [3, 1],
 "roundResults": [{"round": 1, "winner": 1, "reason": "ring_out", "ticks": 213, "knockdowns": [0, 1]},
                  {"round": 2, "winner": 0, "reason": "decision", "ticks": 396, "knockdowns": [0, 0]},
                  {"round": 3, "winner": 1, "reason": "knockout", "ticks": 288, "knockdowns": [3, 0]},
                  {"round": 4, "winner": 1, "reason": "ring_out", "ticks": 175, "knockdowns": [1, 1]}],
 "ringOuts": [2, 0],
 "knockouts": [1, 0],
 "knockdownsSuffered": [1, 4],
 "contacts": [37, 41],
 "shoveImpulse": [1.84, 1.21],
 "meanEffortPct": [71, 64],
 "llmTurns": [48, 47],
 "fallbackTurns": [0, 1],
 "rounds": 4,
 "finalTick": 1608,
 "reason": "complete",
 "endRule": "match_won",
 "seed": 5104773}
```

`names` are the **real policy names** (spectator side). `aliases` are the in-game names. Every
per-seat array is in **seat order** and has exactly 2 entries. `roundResults[].winner` is a **body
index**, never a seat; `-1` means a draw. `scores[0] + scores[1] == 0.000` exactly.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDPBD`** format: the static wasm viewer parses exactly
this format, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and the whole seek/keyframe machinery. Consequences handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (line 319: "set 0 for a binary replay format").
- The repo keeps **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): given a
  `.replay` path it prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"physics-bodies/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "bodies":[…],"policyKinds":[…],"tickCount":…,"rounds":[…],"intents":[…],"fallbacks":N,
  "results":{…}}`. It brace-matches the config JSON from the first `{` (the technique ctf's
  `AGENTS.md` documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule, .results.roundsWon' /tmp/ep.json
  jq -r '[.intents[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "physics-bodies/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.rounds > 0`, `results.contacts` non-zero on both seats,
  and the champion seats' intents `source == "llm"` with varying `stance`/`aggression` values — not
  all fallbacks, and not a constant intent.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDPBD`, format version, `gameName` `physics-bodies`, `gameVersion` `1` |
| config JSON | `seed`, `perm`, `num_agents`, `maxTicks`, `turnTicks`, `roundTicks`, `resetTicks`, `maxRounds`, `roundsToClinch`, the whole geometry table (arena box, ring centre/radii, shrink law, torso/foot radii, `ReachByPosture`, leg mounts, start radius), every actuation constant (thrust, traction, friction, clamps, yaw, restitution, shove, tilt), the scoring constants, `players[].name` (**real names**), `slots[].alias`, `fastMode` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| inputs | **the action log**: one command byte per seat per tick, written on change only |
| chats | `register` / `intent` / `fallback` / `budget_guard` / `round` / `stop` / `result` records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 2160 hashes (8 B) + ≤ 4 320 input-change records (≈ 4 B) + 120 intent records (≈ 220 B) + 5
`round` records + a ≈ 5 KB config ≈ **65 KB** worst case, typically under 45 KB.

### Record and event vocabulary

**A. Replay chat records** (written by the server; re-applied at playback in order):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `body`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `intent` | `turn`, `seat`, `alias`, `body`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `stance`, `aim`, `bearing_deg`, `aggression`, `posture_bias`, `lead_ticks`, `circle_dir`, `say` |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `round` | `round`, `winner` (body index, `-1` = draw), `reason` (`ring_out`\|`knockout`\|`decision`\|`draw`), `ticks`, `knockdowns` — **load-bearing**: `bankRound` applies it identically on record and playback |
| `stop` | `tick`, `cause` (`wall_clock`) — **load-bearing**, the particle-worlds 13c66d7 fix |
| `result` | the full results document, written once at game over (ctf's `resultRecord`, kept — it is what makes the bytes self-sufficient) |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these from
state deltas during playback, so they cost no replay bytes and are identical live and in replay:
`phase`, `round_start` (`{round, radius}`), `contact` (`{by, impulse, normal_deg}`), `shove`
(`{by, impulse}`), `stagger` (a body's `tipMilli` crossing 500 upward), `knockdown` (`{body, count}`),
`rim_slip` (`groundedCount` dropping below 4), `ring_out` (`{body, radius}`), `round_end`
(`{round, winner, reason, ticks}`), `match_point` (a body reaching `roundsToClinch − 1`), `turn_end`,
`gameover`, `say` (an `intent` record's non-empty `say`).
**Beats** (scrubber markers): `knockdown`, `ring_out`, `round_end`, `match_point`, `over`. `contact`,
`shove`, `stagger` and `rim_slip` are **not** beats — they fire dozens of times a round and would bury
the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Contact, Shove, Stagger, Knockdown, RimSlip, RingOut, RoundEnd, Intent,
PhaseChange`, and the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}` — i.e.
`replay_viewer.bundle = static-replay-viewer` — and there is no `/client/replay` live-server viewer
declaration anywhere. The build hook is `tools/build_replay_viewer.sh`, which is ctf's
script, kept (with `image_tag` and the `docker cp` source path
`/workspace/bodies/replay-viewer/dist/.` changed, and the ecos `mkdir -p` already present at lines 20
and 30). `coworld build` invokes it with the absolute bundle directory; the script already refuses any
output path that is not a `static-replay-viewer` directory inside the repo, and it must stay committed
**executable** (`coworld build` hard-requires `os.X_OK`).

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter.** Splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently with every file present and 200
(cogame-lantern, 2026-08-23), so there is no mixture anywhere in this table:

| File | Source |
|---|---|
| `replay-viewer/config.nims` | **`coworld-ctf`**'s `replay-viewer/config.nims`, verbatim except `ctf_replay.js` → `bodies_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_bodies_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the flags stay exactly as ctf links them, including `-s ENVIRONMENT=web,worker,node` (line 51), `-s ABORTING_MALLOC=1` (line 49), `--preload-file …/data@data` (line 46), `--define:useMalloc`. |
| the wasm entry `.nim` | **`coworld-ctf`**'s `replay-viewer/ctf_replay.nim`, forked to `replay-viewer/bodies_replay.nim` (stage-note buffer, `ABORTING_MALLOC` diagnostics, the `predictedViewerRenderBytes`/`WasmViewerBudgetBytes` capacity preflight, `emscripten_exit_with_live_runtime` lifetime — all kept), exporting `bodies_load_replay`, `bodies_frame`, `bodies_input`, `bodies_packet_ptr/len`, `bodies_mismatch_tick`, `bodies_error_ptr/len`, `bodies_stage_ptr/len`. |
| `static_replay*.js` | **`coworld-ctf`**'s `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts('./wire_constants.js', './broadcast_core.js', './bodies_replay.js')` form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Only two names change: the Worker name `ctf-static-replay` → `bodies-static-replay`, and `window.CtfStaticReplay` → `window.BodiesStaticReplay`. |
| `index.html` | built from **`coworld-ctf`**'s `client/replay_broadcast.html` (see below). |

`static_replay.js` **already sets both machine-readable markers and they are kept unchanged**: it sets
`document.documentElement.setAttribute('data-replay-loaded', 'true')` **on its first drawn frame**
(the Worker's `loaded` message, `replay-viewer/static_replay.js:161`), and `showFailure()` sets
`document.documentElement.setAttribute('data-replay-error', <message>)` **on failure** (line 20), plus
`data-replay-mismatch-tick` on a hash mismatch (line 32). Those attributes are what
`tools/ci/viewer_smoke.mjs` waits on. The `coworld-replay` bridge `ready` post is fired **from a
callback that runs after `data-replay-loaded="true"` has been set**, never on rAF timing at the call
site (chorus, 2026-08-24: the softmax.com embed otherwise samples an unpainted shell).

### Chrome provenance: what is copied, what is appended, what is removed

- **`client/chrome_common.js` is copied byte-for-byte from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, lives, flag story) stay in the file and are inert because the
  corresponding state fields are simply absent from physics-bodies' stream. Every
  physics-bodies-specific readout lives in the appended game block, and the state JSON **keeps ctf's
  key names** (`t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events,
  lead, beats, lulls, over, hold` — `src/ctf/broadcast.nim:860-975`) so chrome_common's plate
  rendering, feed rows, beat markers, momentum curve, spoilers switch and endcard run unmodified
  against physics-bodies values. A from-scratch page that reuses the starter's ids is explicitly
  **not** what happens here (cogame-gridlock, 2026-08-23). A test pins the file's sha256 against the
  starter's copy.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one `<style>`
  and one `<script>` block at the end of the file, injecting physics-bodies' readouts into the
  existing containers. Nothing above them is rewritten; the CSS variables, `relayout()`, the
  transport, the endcard, the locker-room loader and the `?embed=1` mode are the starter's. The game
  block's own function names are prefixed `pb` (`pbMarkBeat`, `pbPushFeed`, …) so nothing shadows
  chrome_common's hoisted alias block (`var markBeat = C.markBeat` — the tandem 2026-08-23 scar), and
  a test asserts no game-block top-level name collides with the alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and its
  children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; and `#povBadge`.
  **Zoom decision: a sumo ring is a fixed arena. The ring never moves, the board (1920 × 1280 px)
  always fits the frame, so `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the
  rule that it exists only for boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap
  code stays in the file, verbatim, simply never driven.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (with `#lk-art`,
  `#lk-bg`, `#lk-cap`, `#lk-sprites`; re-captioned "Two bugs, one shrinking ring, nowhere to hide",
  art from `client/art/lockerroom/bg.jpg`), `#chrome`, `#scorebug` with
  `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#mmwarn`, `#bannerlane`,
  `#killfeed`, `#transport` with every button (`#btn-play`, `#btn-back`, `#btn-fwd`, `#btn-end`,
  `#btn-restart`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`), `#speedchips`, `#scrub`, `#scrub-fill`,
  `#scrub-head`, `#scrub-win`, `#momentum`, `#lulls`, `#tick-clock`, `#ffwd-chip`, `#ffwd-mini`,
  `#win-chip`, `#endcard` with `#ec-headline`, `#ec-how`, `#ec-wincond`, `#ec-teams`, `#ec-replay`,
  and `#status`.

### The exact state JSON the viewer reads

`buildStateJson` (ctf's, retargeted) emits this object once per frame. Keys above the fold are ctf's
and are consumed by the byte-identical `chrome_common.js`; everything physics-bodies-specific is under
`pb` and `intents`, consumed only by the appended game block.

```json
{"t": 864, "mt": 2160, "ph": "playing", "lob": 0, "pl": true, "sp": 1, "mx": 2160,
 "st": 0, "lp": false, "sk": false, "ff": false, "en": true, "mm": -1, "bs": 2, "pov": -1,
 "teams": {"bug1": {"score": 2.75, "rounds": 2, "knockdowns": 1, "ringOuts": 1,
                    "distFromCentre": 1.85, "tilt": 18, "down": false},
           "bug2": {"score": -2.75, "rounds": 1, "knockdowns": 4, "ringOuts": 0,
                    "distFromCentre": 1.42, "tilt": 41, "down": false}},
 "roster": [{"s": 0, "name": "daveey", "team": "bug2", "alias": "BUG-2", "body": 1,
             "kind": "llm", "rounds": 1, "knockdowns": 4, "contacts": 41, "effortPct": 64},
            {"s": 1, "name": "daveey-1", "team": "bug1", "alias": "BUG-1", "body": 0,
             "kind": "llm", "rounds": 2, "knockdowns": 1, "contacts": 37, "effortPct": 71}],
 "events": [{"k": "knockdown", "t": 851, "body": 1, "count": 2}, "…"],
 "turn": 24, "turns": 60, "turnTicks": 36,
 "pb": {"ring": {"centre": [4.80, 3.20], "r": 2.31, "r0": 3.00, "rmin": 1.80},
        "round": {"index": 3, "of": 5, "tick": 0, "of_ticks": 396, "toClinch": 3,
                  "log": [{"round": 1, "winner": 0, "reason": "ring_out", "ticks": 213},
                          {"round": 2, "winner": 1, "reason": "decision", "ticks": 396}]},
        "bugs": [{"i": 0, "p": [3.31, 4.28], "v": [1.02, -0.41], "heading": 338.0,
                  "spin": -12.4, "posture": "even", "effort": 2, "drive": 11,
                  "tilt": 18, "down": 0, "grounded": 4,
                  "feet": [{"p": [3.77, 4.11], "g": true, "load": 0},
                           {"p": [3.14, 3.82], "g": true, "load": 2},
                           {"p": [2.85, 4.45], "g": true, "load": 0},
                           {"p": [3.48, 4.74], "g": true, "load": 0}],
                  "stance": "charge", "say": ""},
                 "… 2, body order …"],
        "contact": {"on": false, "point": null, "normal": null, "impulse": 0.0},
        "score": {"bug1": 2.75, "bug2": -2.75}},
 "intents": [{"turn": 24, "seat": 0, "alias": "BUG-2", "body": 1, "source": "llm",
              "stance": "lift", "aggression": 9, "note": "…", "say": "getting under it"},
             "… 2 …"],
 "lead": {"teams": ["bug1", "bug2"], "pts": [[0, 0], [213, 1250], "… change-points of the round differential …"]},
 "beats": [{"t": 213, "k": "ring_out"}, {"t": 851, "k": "knockdown"}, "…"],
 "lulls": [[430, 590]],
 "over": {"winner": "bug1", "draw": false, "timeLimit": false, "endRule": "match_won",
          "reason": "complete", "score": 2.75, "ticks": 1608,
          "teams": {"bug1": {"rounds": 3}, "bug2": {"rounds": 1}}},
 "hold": 3}
```

There are exactly **two** `teams` keys (`bug1`, `bug2`) — this is a two-sided zero-sum game — so
chrome_common's plate loop renders one plate per side, left and right. `roster` carries the **real
policy names** and is spectator-side only.

### Readouts

1. **Run bug** (top, always on). `#plates-l` = the amber **BUG-1** plate: real policy name, the live
   score, and **round wins as best-of-five pips** (three lit = match); under it two small counters
   (`knockdowns 1`, `ring-outs 1`). `#plates-r` = the same for teal **BUG-2**. Centre column
   (`#clock`): the **round clock** counting down `M:SS` from `roundTicks div 24`, with
   `#clock-caption` = `ROUND 3 of 5 · RING 2.31 m` — so the shrinking ring is a number, not just a
   picture.
2. **The board** (the headline): a top-down dohyō — sanded clay baked from `data/arena_floor.png`, a
   painted rim ring, and the **live shrinking rim drawn as a bright arc that visibly contracts**, with
   a faint ghost of the round-start radius behind it. Outside the rim is dark boards. The two bugs are
   baked hulls in amber and teal with **four legs drawn at their actual computed foot positions**, so
   the reader *sees* posture: `low` is a wide stable star, `high` is a tight tall cross, `lift` is
   lopsided forward. A leg carrying load glows and kicks a dust puff; a foot over the rim goes dark
   and draws no dust (that is "no floor", legible without a caption).
3. **Tilt gauges — the fall, made visible.** A small arc over each bug fills with `tilt`; it turns
   amber above 50 % and flashes above 80 %. A downed bug lies prone (hull rotated, legs folded) with a
   countdown pip for its 36 ticks, and the feed says so.
4. **Contact FX**: an impulse burst at the contact point sized by `|j| + shove`, a short shove arrow
   along the contact normal, and a `LIFT` chip when a `lift` posture is in contact. A shove that
   crosses `TipImpulseThreshUm` shakes the frame briefly.
5. **Rim danger and the ring-out**: the arc of the rim nearest a bug lights red once it is within
   0.45 m; a ring-out draws that bug tumbling past the rim with an `OUT` stamp and freezes the arc
   where it was crossed for the whole reset hold. This is the idea's stated highlight and it is a
   first-class readout, not flavour.
6. **Speech bubbles**: at most **two** at a time (one per bug) — drawn for 2.5 s in a **reserved band
   across the top of the arena** (`Y ∈ [5.70, 6.30] m`), never positioned relative to a bug. The band
   is sized from `MaxSayRunes = 48` measured in `data/font.ttf` at the current `--hudscale`, which is
   exactly the reservation the cogchemists 2026-08-24 scar demands (text laid out relative to a body
   near the top of the arena draws at a negative coordinate and a canvas accepts it silently);
   `viewer_smoke.mjs --strict-text-bounds` requires `canvas_text.never_inside == 0` for this fixed
   arena.
7. **Match feed** (`#killfeed`, renamed in copy only): plain language — "BUG-1 shoves BUG-2 to 2.6 m
   from centre — rim in 0.4 m", "KNOCKDOWN — BUG-2 is down (2 of 3)", "RING OUT — BUG-1 takes round
   2", "ROUND 3 — ring 3.00 m and closing", "DECISION — BUG-1 held the middle", "MATCH POINT BUG-1",
   "TURN 24 — 2 new orders". Intent `note`/`say` strings appear here; this is where a spectator sees
   the LLM playing.
8. **Momentum graph** (`#momentum`): ctf's `lead` series repurposed to the **round differential**
   (`roundMicro[0] − roundMicro[1]`) over the whole timeline, with a second thin trace of
   `distFromCentre[1] − distFromCentre[0]` — who is holding the middle — so the graph shows pressure
   between round wins, not just steps.
9. **Transport and integrity**: ctf's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls,
   spoilers, speeds `[1,2,3,4,8,16]`, scrubber with beat markers, tick readout, the end-hold countdown
   and `#mmwarn` — all verbatim.
10. **Endcard**: "BUG-1 WINS 3–1 · score +2.750" (or "DRAWN 2–2" / "BUG-2 WINS BY KNOCKOUT"), and
    chrome_common's `ec-*` table listing both seats by **real policy name** with body number, rounds
    won, ring-outs, knockouts, knockdowns suffered, contacts, mean effort % and LLM/fallback turn
    counts.

### Transport rules

- `relayout()` is kept verbatim: it sets `--hudscale`, `--topband` and **`--band`** on `:root` by
  fixed-point iteration, so the board is letterboxed between the scorebug band and the transport band.
- **No overlay sits in the transport band.** Every physics-bodies overlay the game block adds — the
  round pips, the ring-radius caption, the tilt legend — is positioned inside `#chrome` with
  `bottom: calc(var(--band) + N * var(--u))`, never over it.
- The **endcard stops at `var(--band)`** (the starter's `#endcard { bottom: var(--band) }` rule at
  line 1036 is kept) and is **dismissed by every seek** (the starter's behaviour, kept).
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">`** elements — the game
  block upgrades chrome_common's markers to buttons with `aria-label` and `title` (e.g. "Ring out —
  8.9 s — BUG-1 takes round 2") and a click seeks to that tick. **CSS exists for every kind
  emitted**: `.beat-marker.knockdown`, `.beat-marker.ring_out`, `.beat-marker.round_end`,
  `.beat-marker.match_point`, `.beat-marker.over` — one rule per kind, asserted by
  `tests/test_viewer.nim`.

### Art

Real, and mostly baked from what the repo already ships. The clay floor, the rim paint, the dark
boards outside, the two bug hulls and their leg segments, the dust puffs, the impulse bursts, the tilt
arcs and the vignette are baked once at startup with **pixie** (already a dependency, already how ctf
bakes its board), using ctf's shipped `data/arena_floor.png` as the clay plate and
`client/art/walls/wall_h.jpg`/`wall_v.jpg` as the boards/rim sources, and `data/font.ttf` for every
label. The locker-room card reuses `client/art/lockerroom/bg.jpg`. No solid-colour placeholders, no
TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`; kept verbatim.
At that width the scorebug shows both scores, both round-pip strips and the round clock; the two
policy names live in the endcard and in each roster row's `title`. Two further rules ship in the game
block: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`
(so the two policy names never collapse to "…" — the documented 360 px scorebug failure) and, under
`.tiny`, the tilt legend, the effort counters and the bubble text are hidden while the rim arc, the
tilt gauges, the dust and the round pips stay. The board aspect is 1920:1280 = 1.5, which the chrome
derives from the stream. `tests/test_viewer.nim` asserts both rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-physics-bodies`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `physics-bodies`; `game.name` is also
  `physics-bodies`, so the secret namespace
  `secret://coworld/physics-bodies/anthropic_api_key` matches `game.name` **exactly**
  (cooperative-hunting, 2026-08-25: the namespace must equal `game.name`, not a differently-punctuated
  slug; `POST /coworld-league-seeds` also wants `game.name`).
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{PHYSICS_BODIES_IMAGE}}` (placeholders are derived from **compose service names** by uppercasing
  and replacing `-` with `_`; `{{GAME_IMAGE}}` is not a thing outside ctf's own two-service file —
  lantern 0.1.0). Phase 20's manifest generator derives it from `compose.yaml` and
  `tests/test_manifest.nim` asserts the derivation:

  ```yaml
  services:
    physics-bodies:
      image: coworld-physics-bodies:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure (nimby 0.1.26,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's
  package tree), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:physics-bodies
  src/physics_bodies.nim` → `/bin/physics-bodies`, and the same for
  `src/physics_bodies_player.nim` → `/bin/physics-bodies-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/physics-bodies"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby with its
  sha256 check, the marker splices, the `test -f`/`grep -q` assertion block) with the asset list
  swapped and the workspace path `/workspace/bodies`.
- **`coworld_manifest_template.json`** (written against the `coworld` 0.1.42+ upload contract —
  validate offline with the CLI's `validate_upload_manifest` **and** `_load_template_manifest` as a CI
  step before dispatching):
  - top-level `$schema`, `episode_timeout_minutes: 20`, and top-level `tags` ≥ 3:
    `["physics","competitive","continuous-control","zero-sum","llm"]`. **`game.tags` does not exist** —
    the validator forbids it and requires `game.description` (pistonball 0.1.0, 2026-08-26).
  - `game.name` `physics-bodies`; `game.description` (one sentence: "Two four-legged robot bugs push
    each other out of a shrinking sumo ring; off-centre shoves spin you, and a bug that tips over
    cannot push for a second and a half."); `game.owner`; `game.runnable`
    `{"type":"game","image":"{{PHYSICS_BODIES_IMAGE}}","run":["/bin/physics-bodies"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/physics-bodies/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-physics-bodies/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}` (nested under `game`, not top-level;
    no top-level `version`, no `game.display_name`).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`; **every array property carries `minItems`/`maxItems`** (tandem 0.1.0 scar):
    `tokens` (1..2), `players` (1..2), `slots` (0..2), plus `closedRoster`, `seed`, **`num_agents`**
    (1..2), `minPlayers`, `maxTicks` (default 2160), `maxGames` (default 1), `turnTicks` (default 36),
    `roundTicks` (default 396), `resetTicks` (default 36), `maxRounds` (default 5), `roundsToClinch`
    (default 3), `ringRadiusUm` (default 3000000), `ringRadiusMinUm` (default 1800000),
    `ringShrinkPerTickUm` (default 4000), `shrinkStartTick` (default 144), `knockdownsToLose`
    (default 3), `downTicks` (default 36), `turnBudgetMs` (default 16000), `attempt1Ms` (default 9000),
    `retryMs` (default 5000), `turnSpacingMs` (default 6000), `wallClockBudgetSeconds` (default 660),
    `lobbyJoinTimeoutTicks` (default 720), `startWaitTicks`, `gameOverTicks`, `fastMode` (default
    true), `showPlayerLabels`, `model`, `maxOutputTokens` (default 900). The CLI validates every
    variant and the cert fixture against this schema (injecting `tokens`), so every key either appears
    here or is not settable — and `tests/test_manifest.nim` asserts it covers every field
    `sim_config.update` reads. **No `game_config` anywhere carries a literal `tokens: […]`** — the
    runner injects it and matriculate rejects it (knights-archers 0.1.0).
  - `game.results_schema`: exactly the 21 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","reason","endRule","roundsWon","rounds"]`, `reason` enum
    `["complete","deadline","fault"]`, `endRule` enum
    `["match_won","full_time","wall_clock","sim_fault","host_error"]`, every per-seat array
    `minItems: 2, maxItems: 2`, and `roundResults` `minItems: 0, maxItems: 5`.
  - `game.protocols`: **both `player` and `global`**, each `{"type":"text","value":"…"}` (objects, not
    bare strings — garble v0.1.0). `player` documents the registration chat frame, the per-tick Sprite
    v1 frames, the fact that seats send **no** inputs, the observation JSON and the intent reply schema
    with its caps. `global` documents the `/global` spectator snapshot, the state JSON above, the
    `COWLDPBD` replay layout (config JSON, command-byte log, chat records, hash chain) and the static
    replay bundle.
  - `game.docs`: `readme` = `{"type":"text","value":"<the README body inlined>"}` and `pages` = three
    entries — `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined: every number in §The game>"}}`, `{"id":"protocol.md","title":"Wire protocol",…}`,
    `{"id":"orders.md","title":"Writing a bug order",…}`. A manifest test asserts all four values are
    non-empty text.
  - `player[0]` (the only top-level bundled player entry, with id/type/name/description) =
    `{"id":"baseline","type":"player","name":"Ring Pusher Baseline",
    "description":"Scripted sumo bug: charge, shove whoever is nearer the rim, lift on contact, and
    back off the edge. No LLM.","image":"{{PHYSICS_BODIES_IMAGE}}",
    "run":["/bin/physics-bodies-player"],"env":{"PLAYER_SCRIPTED":"pusher"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}`. It occupies
    **both** certification slots — every declared player entry must occupy at least one slot or cert
    fails `players_missing` (raid 0.1.2 → 0.1.3), and `limits.cpu` below `"1"` is a 400 at upload
    (pistonball 0.1.1).
  - **Variants — `num_agents` is 2 in both (inside `game_config`, never at the variant's top level —
    `CoworldVariant` is `additionalProperties: false`, goofspiel-oshi-zumo 0.1.0), and `description`
    is required on each:**

    | id | name | description | **`num_agents`** | `players`/`slots` | `minPlayers` | `maxTicks` | `maxRounds` | `roundsToClinch` | turns | `turnTicks` | `turnSpacingMs` | `turnBudgetMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
    | `default` | The Ring (2 bugs, best of 5) | Two four-legged bugs, five rounds of 16.5 s in a shrinking 6 m ring, 60 order turns. | **2** | 2 | 2 | 2160 | 5 | 3 | 60 | 36 | 6000 | 16000 | 660 |
    | `blitz` | Blitz (2 bugs, best of 3) | Same ring and rules, three rounds, for cheap ladder rounds. | **2** | 2 | 2 | 1296 | 3 | 2 | 36 | 36 | 6000 | 16000 | 420 |

    Both seat two players, `slots: [{"alias":"BUG-1"}, {"alias":"BUG-2"}]`, `fastMode: true`,
    `maxGames: 1`. `blitz` changes only the match length, **never** the seat count. `blitz`'s budget:
    35 × 6 s + 16 s + 12 s lobby + 1 s physics + 20 s write ≈ 259 s, inside 420 s, inside 720 s.
  - **Certification fixture — `num_agents` is 2 here too:** `certification.players` = two
    `{"player_id":"baseline"}` entries; `certification.game_config` =
    `{"players":[{"name":"BUG-1"},{"name":"BUG-2"}], "slots":[{"alias":"BUG-1"},{"alias":"BUG-2"}],
    "num_agents": 2, "minPlayers": 2, "seed": 5104773, "maxTicks": 1728, "maxRounds": 4,
    "roundsToClinch": 4, "maxGames": 1, "turnTicks": 36, "turnBudgetMs": 16000, "turnSpacingMs": 0,
    "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 480, "ringShrinkPerTickUm": 0,
    "fastMode": true}` — both seats scripted, no LLM client (no credentials offline, so the client
    disables itself and every turn falls back instantly). `roundsToClinch == maxRounds == 4` means the
    match **cannot clinch early**, so all four rounds always play; with the shrink disabled the rounds
    are long and the replay is long. Wall cost ≈ 10 s connect + ~1 s of physics + the ~20 s shutdown
    grace ≈ 32 s. `tests/test_replay.nim` pins the fixture's tick count at this seed and asserts it is
    **≥ 480 ticks (20.0 s of playback)**, comfortably longer than the viewer smoke's 12 s soak (ecos,
    2026-08-23: a replay shorter than the soak reads as "frozen"). Because 32 s is close to
    `coworld certify`'s 60 s default, the release workflow's certify step passes
    **`--timeout-seconds 300`** (cooperative-hunting 0.1.2 → 0.1.3); the fixture is **not** shrunk.
- **Scaffold from `templates/`** with `<slug>` = `physics-bodies`, `<IMAGE>` =
  `coworld-physics-bodies`, `<SEATS>` = **2**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`, `tools/ci/docker_smoke.sh`
  (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim, no substitutions),
  `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh` (**`chmod +x`**). Two additions to
  the template `ci.yml`: the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay
  format), and the `wasm-viewer` job gets the extra `renderer_fixture.html` step of §Tests. The
  `NIM_TESTS_RELEASE_ONLY` repo variable lists `tests/test_perf.nim` and `tests/test_baselines.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/physics-bodies-player"`, one image,
  env-switched; each also sets `PLAYER_POLICY_LABEL`):

  | name | env | role |
  |---|---|---|
  | `physics-bodies-ringcraft` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey (`ply_44ae9048-3242-4654-881f-6d9d43347fa3`) |
  | `physics-bodies-toppler` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `physics-bodies-pusher` | `PLAYER_SCRIPTED` = `pusher` | filler |
  | `physics-bodies-anchor` | `PLAYER_SCRIPTED` = `anchor` | filler |

  A two-seat episode is filled by the platform with a champion against a champion or against a
  filler; filler versions must differ from champion versions or the platform renames a champion
  "Baseline (N)".
- **Repo layout**: `src/physics_bodies.nim`, `src/physics_bodies_player.nim`,
  `src/bodies/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, ring.nim, body.nim,
  control.nim, intents.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim, replays.nim,
  replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, wire_constants.nim,
  server.nim}`, `replay-viewer/{bodies_replay.nim, config.nims, static_replay.js,
  static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, ORDERS.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `physics_bodies.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only harness;
the sandbox has no Nim, Docker, emsdk or browser. The **determinism gate** (test 2 plus the viewer
smoke) is inviolable: if it fails, the physics or a build flag changed — fix the code, never the test.

1. **`tests/test_physics.nim`** — sim unit tests: a bug at rest given `effort 3, posture even, 4 legs
   grounded` for 48 ticks reaches `2.9 … 3.3 m/s` and never exceeds `MaxSpeedByPosture[even]`; each
   posture's coasting speed decays by its documented `FricNumPer1024/1024` per tick within 1 unit and
   reaches under 1 % of its initial speed within 240 ticks; each posture's measured terminal speed
   matches the `ThrustUnit · TractionMul · 1024 / FricNum` arithmetic in §The game within 2 %; the yaw
   servo settles a 180° heading error within 96 ticks with no overshoot beyond 1.5 direction indices
   and `|omegaMilli| ≤ MaxYawMilli` always; leg reach equals `ReachByPosture[posture]` exactly and the
   four foot positions are the documented `DirQ12` offsets; `groundedCount ∈ 1..4` for **every** legal
   up-state over 50 000 randomised `(p, hMilli, posture, ringRadiusNow)` tuples (the invariant §The
   body claims); a head-on contact conserves total normal momentum to within the restitution term; a
   grounded shove at `groundedA == 4` gives the pusher **exactly zero** recoil; the swept-contact test
   and the end-position test agree over 50 000 randomised legal states (so the sweep is a guard, not a
   behaviour change); `|v| ≤ MaxBodySpeedHard` after every contact tick over 20 000 randomised pairs.
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same command-byte log ⇒ identical
   `gameHash` at every tick over a full 2160-tick run, twice in one process and once in a fresh sim;
   (b) a one-unit change in any command byte changes the final hash; (c) a committed golden fixture
   `tests/data/golden_hashes.json` pins the hash at every 48th tick for seed 5104773; (d) **a source
   guard** that greps `src/bodies/{sim,ring,body,trig,sim_types,sim_config,sim_state}.nim` for
   `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts for `-ffast-math`,
   failing on any hit, plus a grep for `rand(` (only `drawInt` may draw); (e) `DirQ12` re-derived from
   `math.cos`/`math.sin` entry by entry, and `isqrt` checked exhaustively below 2¹⁶ and on perfect
   squares to 2⁴⁰; (f) `perm` and all five start axes are pure functions of `seed`, identical across
   two fresh sims, `perm` is a permutation of `0..1`, and `rngDraws == 6` at the end of every full
   episode; (g) `rngDraws` is identical between two runs of the same command log.
3. **`tests/test_ring.nim`** — ring geometry and rounds: the shrink law reproduces
   `max(RingRadiusMin, RingRadius0 − max(0, roundTick − 144)·4000)` at every tick of a round and is a
   pure function of `(roundIndex, roundTick)`; the radius at the round clock is exactly 1 992 000 µm;
   the seeded start axis places the two bugs `2 · StartRadius` apart facing each other, at
   `StartRadius` from the centre, with the **end swap** applied on odd rounds and asserted over 50
   seeds; a foot beyond `ringRadiusNow` is not grounded and one beyond it by 1 µm is not grounded
   either (the boundary is `≤`); the ring-out predicate fires on the exact tick the torso centre
   exceeds `ringRadiusNow`; the both-outside and the `CentreTieUm` draw branches are reached by
   constructed states; the round-clock tiebreak order (knockdowns, then centre distance, then draw) is
   exercised in all three branches.
4. **`tests/test_control.nim`** — the controller: for 5 000 randomised (state, intent) pairs the
   command byte is in `0..255`, decodes to `drive ∈ 0..15`, `posture ∈ 0..3`, `effort ∈ 0..3`, and the
   same pair always yields the same byte; each of the six stances produces the documented goal bearing
   in its documented condition; **the rim guard**: a bug driven by any stance at `aggression ≤ 9` from
   any legal state never crosses the rim under its own drive over 10 000 randomised 240-tick rollouts,
   and at `aggression == 10` it can (the guard is halved — the documented trade, asserted in both
   directions); `posture_bias: auto` resolves exactly as documented in all five branches; a bug with
   `downTicks > 0` and any non-`Playing` phase force `cmd = 0`; **the duty-cycle claim** — over 24
   ticks the mean applied thrust tracks the requested continuous effort within 8 % for every requested
   value in `0.0 … 3.0` at 0.1 steps; `brace` brakes monotonically to `|v| = 0` within 120 ticks from
   full speed.
5. **`tests/test_baselines.nim`** (release-only) — **the bounded-orders / legality assertion on the
   scripted baselines**: for 500 pseudo-random world states × both baselines, the emitted intent
   validates against the reply schema — `stance`, `aim` and `posture_bias` in their enums,
   `aggression ∈ 0..10`, `bearing_deg ∈ 0..359`, `lead_ticks ∈ 0..24`, `circle_dir ∈ {−1,+1}`,
   `note ≤ 160` runes, `say ≤ 48` runes — and the compiled command byte is in range. Plus the tuning
   pin: **`pusher` beats `anchor` on at least 14 of 20 seeds**; a ring-out decides at least **60 %** of
   all rounds across those 20 seeds (proof the ring-out mechanic is reachable and not a curiosity); at
   least one **knockdown** occurs across a `pusher` vs `pusher` sweep of 20 seeds (proof the fall
   mechanic is reachable); and no seed produces a `fault`. (This is the anti-regression pin for the
   whole physics tuning: if the baselines cannot ring each other out, the three `BaselineParams`
   numbers are wrong — re-run `tools/tune_baselines.nim` and commit the sweep's pick to
   `tools/ci/baseline_tuning.json`, which `tests/test_tuning.nim` re-asserts. The physics constants do
   not move.)
6. **`tests/test_intents.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON, an
   `aggression` given as `80`, a `bearing_deg` given as `2.4` radians, `circle_dir` as `"cw"`,
   `lead_ticks` as `0.5` seconds, `stance: "push"` and `"hold"`, an unknown `stance`, NaN/absent
   fields, out-of-range values, a 300-character `note`, and a `say` whose 48th and 49th characters are
   a **4-byte emoji** — the truncation must land on the **rune** boundary and the result must still
   round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the `pusher` intent
   plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a `throttled` client ⇒
   **zero** retries.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **both seats' calls go out in
   one parallel batch** (the fake records in-flight windows; the test asserts the two intersect);
   consecutive batches are ≥ `turnSpacingMs` apart; the per-turn budget is enforced with a hung
   client; the budget guard switches to scripted and the episode still ends `complete/*`; the 660 s
   stop yields `deadline/wall_clock` with the `stop` record written; a tripped invariant yields
   `fault/sim_fault` with a partial replay; a disconnected seat plays `pusher` and revives on
   reconnect; a never-connecting seat is reported to `COGAME_PLAYER_FAILURE_URI`, **logged loudly**,
   and the match still reaches a normal ending; a registration that arrives before its player index
   exists is **held and applied**, not dropped.
8. **`tests/test_observation.nim`** — the observation contract. Over 200 randomised states: seat `s`'s
   composed LLM user message contains the full physical state of **both** bodies and the ring, and
   contains **no** other seat's `note`, `say`, `stance`, `aggression`, prompt, latency, `policyKind`,
   policy label or fallback state; contains no `perm`, `seed`, RNG state, future start axis, variant
   name, or `sim.players[i].address`. **Two name spaces**: the composed LLM user message and the
   player-stream board labels contain no real player name, while the chrome roster, `over` and
   `results.names` do. Also: `control.driveCommand`'s inputs are structurally limited to the sim
   state, the body index, its seat's intent and the tick.
9. **`tests/test_scoring.nim`** — the formula and its sign: the six worked examples of §The game
   reproduce to 3 decimals; `results.scores[0] + results.scores[1] == 0.0` **bit-exactly** over 200
   randomised round logs (the zero-sum claim); a `ring_out` round banks 1.250 and a `decision` round
   banks 1.000; a `draw` banks nothing to either side; `roundsToClinch` reached ends the episode on
   that tick with `endRule = match_won`; `win` is `[false, false]` exactly when `roundsWon` ties;
   `bankRound` applied on record and on re-derivation produces identical `roundMicro[]`.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full 2-seat scripted
    episode writes `results.json` and a `COWLDPBD` replay; `parseReplayBytes` accepts it;
    re-simulating from the config + recorded command bytes reproduces **every** recorded hash;
    **the record → re-derive check runs for EVERY end reason** — `complete/match_won`,
    `complete/full_time`, `deadline/wall_clock`, `fault/sim_fault` — not just `complete`
    (particle-worlds 13c66d7); **`tools/replay_summary.py` output parses under a strict UTF-8 JSON
    parser** (`json.loads(out.decode("utf-8"))`) with the fixture forced to carry a non-ASCII `say`
    and a non-ASCII policy label, so the UTF-8 path is real; the embedded config JSON decodes strictly
    and contains `seed`, `perm` and the whole geometry table; every `intent` record is ≤ 480 runes;
    `results.reason`/`results.endRule` are in the legal enums; the stream contains exactly 2
    `register` records, 2 `intent` records per turn, one `round` record per completed round, at least
    one `contact` event, and exactly one `result` record; **the certification fixture at seed 5104773
    produces ≥ 480 ticks**.
11. **`tests/test_server.nim`** — websocket contract: registration chat accepted and **not** echoed
    into the replay chat stream; a prompt over 4000 runes truncated, not rejected; a non-registration
    chat from a player dropped; an input mask from a player ignored; **a bad token 403 and a
    bad-token player websocket closed** (flatland 0.1.1); a `Ping` answered with `Pong` and a binary
    registration frame **not** dropped by any message-kind guard (lux-ai/snake-royale); `/healthz`;
    `/global` snapshot → ticks → game over; `/client/global` and `/client/player` serve real pages,
    registered before any catch-all asset route, and neither opens the player socket; `/healthz` and
    `/global` still answer 15 s after the artifacts are written; artifact writes to `file://` URIs.
12. **`tests/test_manifest.nim`** — **`num_agents == 2` in every variant *and* in
    `certification.game_config`**, and **absent at every variant's top level**
    (goofspiel-oshi-zumo 0.1.0); `len(certification.players) == 2` and
    `len(certification.game_config.players) == 2`; every declared `player[]` id occupies at least one
    certification slot and its `resources.limits.cpu == "1"`; **no `game_config` carries a literal
    `tokens`**; `results_schema` keys == `playerResultsJson` keys with every per-seat array bounded
    `minItems: 2, maxItems: 2`; every array in `config_schema` declares `minItems`/`maxItems`;
    `game.protocols` has **both** `player` and `global` as `{"type":"text",…}`; `game.docs.readme` and
    all three pages are non-empty text; `game.description` present and `game.tags` **absent** (tags
    top-level, ≥ 3); `game.replay_viewer.bundle == "static-replay-viewer"` and there is no top-level
    `version` or `game.display_name`; `game.owner` present; every variant's
    `wallClockBudgetSeconds ≤ 0.6 × 1200`; `attempt1Ms + retryMs ≤ turnBudgetMs`;
    `maxTicks mod turnTicks == 0` and `(roundTicks + resetTicks) mod turnTicks == 0`;
    `maxRounds × (roundTicks + resetTicks) == maxTicks`; `roundsToClinch ≤ maxRounds`; the compose
    service name uppercased with `-`→`_` equals the image placeholder and the image is
    `coworld-physics-bodies`; the secret namespace equals `game.name`; `config_schema` covers every
    field `sim_config.update` reads; and the installed CLI's own `_load_template_manifest` +
    `validate_upload_manifest` accept the template (collab-cooking, 2026-08-25).
13. **`tests/test_viewer.nim`** — static assertions over `client/replay_broadcast.html` and
    `client/chrome_common.js`: `chrome_common.js` is **byte-identical** to the starter's copy (sha256
    pinned); `replay_broadcast.html` still contains ctf's `relayout()` with `--band`, `--topband` and
    the `--hudscale` clamp on `:root`; `#endcard { bottom: var(--band) }`; `#scorebug`, `#bannerlane`,
    `#killfeed`, `#transport`, `#mmwarn`, `#endcard`, `#momentum` and the `.tiny` block are present;
    `#viewpanel`, `#fpv` and `#povBadge` are **absent**; a `.beat-marker` CSS rule exists for
    **every** beat kind the sim emits (`knockdown`, `ring_out`, `round_end`, `match_point`, `over`) and
    every marker is a `<button>`; no game-block top-level name collides with chrome_common's alias
    list; the `.plate-name { flex: 1 1 auto; min-width: 3.2em` rule is present; `broadcast_core.js`
    differs from the starter's copy in **exactly** the `BODIES_WIRE` identifier; no
    `ctf_`/`CTF_`/`paintball` identifier survives in `client/`, `replay-viewer/` or `src/`;
    `static_replay.js` sets both `data-replay-loaded` and `data-replay-error`; and `config.nims`
    contains **no** `MODULARIZE` or `EXPORT_NAME`.
14. **`tests/test_startup.nim`** — `/bin/physics-bodies` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when unpinned
    (**before** `config.update`) and honoured when pinned; both entrypoints exist and are executable in
    the image.
15. **`tests/test_perf.nim`** (release-only) — 2160 ticks of physics plus 4 320 controller evaluations
    complete in under 60 s.

**CI jobs beyond the Nim tests:**

- `docker-smoke` — `tools/ci/docker_smoke.sh` runs a raw-Docker episode from the certification fixture
  with **`SMOKE_SEATS=2`** (an independent cross-check against `certification.game_config.num_agents`;
  a mismatch prints `SEAT-COUNT FAIL:` and names the manifest path) and
  `SMOKE_REQUIRE_REPLAY_JSON=0`, asserts **both player containers' exit codes** as well as the game's
  (raid 0.1.3 → 0.1.4), and uploads the replay it produced as the `smoke-replay` artifact.
- `wasm-viewer` (`needs: docker-smoke`) — asserts `tools/build_replay_viewer.sh` and
  `tools/ci/viewer_smoke.mjs` exist and the hook is executable, builds the bundle, asserts a non-empty
  `.wasm`, downloads the smoke replay, and then **EXECUTES the bundle in headless chromium**:
  ```
  node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer \
       --replay dist/smoke/<name>.replay --timeout 90 --soak 12 --strict-text-bounds
  ```
  The job fails if `data-replay-loaded` never arrives, if `data-replay-error` is set, if the soak sees
  playback stop advancing, or if `canvas_text.never_inside` is non-zero (fixed arena). The fixture
  replay is ≥ 480 ticks = ≥ 20 s long, so a 12 s soak cannot end the replay. **This is the only gate
  that runs the viewer rather than checking that its files exist** (cogame-lantern, 2026-08-23).
- `wasm-viewer`, second step — **`tools/ci/renderer_fixture.html`**: `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so both seats play scripted and the smoke replay carries only the baselines'
  fixed `say` strings; nothing in CI would otherwise exercise the bubble band or the feed at full cap.
  The fixture **loads the real `dist/static-replay-viewer/index.html` in an iframe** (never a
  re-implementation of the drawing — particle-worlds 46cf69d), shims only the wasm entry, drives the
  page's own text path with a **full-cap 48-rune `say` and 160-rune `note` on both seats at once**, at
  360, 620 and 1280 px, self-checks its own string lengths, and is run through
  `viewer_smoke.mjs --strict-text-bounds` in its own step (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **MuJoCo Soccer (the 4-seat reading).** 2v2 spheres-with-legs is a *different game* on the same
  physics idea: two teams, a ball with its own dynamics, goals, a team motive, a 4-seat observation
  model, a team score that is not zero-sum per seat, and a pitch instead of a ring. It is not a
  variant of sumo — it shares no win condition and no scoring rule with it — and mixing it in would
  give the ladder two incomparable games under one Elo. It returns, if ever, as its own coworld
  (`cogame-cogsoccer`), and the site already has its discrete cousin in `03 Cogball`. (Coordinator
  rail.)
- **Multi-Agent MuJoCo / MaBrax (limbs-as-agents).** "One body, each limb is a separate agent" is a
  fully **cooperative** game with 2–6 seats, a shared reward, per-limb partial observation and no
  opponent at all; nothing about the zero-sum ring survives the change. It also needs the one thing
  this design deliberately does not build: a genuine articulated-joint solver, because the whole
  interest of HalfCheetah 2×3 is the *joints*, not the pushing. Out. (Coordinator rail.)
- **A bit-exact port of RoboSumo, `multiagent-competition`, `dm_control` soccer, `multiagent_mujoco`
  or MaBrax.** No external code is ported, no constant is copied, and no test asserts parity with any
  of them. MuJoCo rides on `sinf`/`cosf`/`atan2f` and float accumulation order, which would make the
  native ↔ wasm hash chain depend on two builds of libm agreeing — the exact failure the integer sim
  exists to prevent (Cogball's ruling). The other competitive scenarios in that family —
  run-to-goal, you-shall-not-pass, kick-and-defend, sumo-humans — are separate games with separate
  win conditions and are not variants of this one.
- **A genuine articulated-joint solver, per-joint torque actuation, or a ragdoll.** v1's body is a
  rigid torso plus four kinematic legs with posture-driven reach; the "multi-limbed" part is the leg
  geometry, the grounded-foot traction and the rim-slip mechanic, not a joint chain. Every claim about
  the model is in §The body, stated as a reduction.
- **A raw per-tick continuous-vector transport for policies.** The v1 control channel is one intent
  per 36-tick turn plus the deterministic controller; the per-tick command byte is derived
  server-side, recorded, and replayed. Because the controller is already a pure function of
  `(intent, sim state, body index, tick)`, exposing a per-tick socket action is a protocol addition,
  not a redesign — but it is not in v1, and the LLM policy interface is the one the platform ranks.
- **Image observations.** Seats get a structured JSON observation, never an RGB crop. There is no
  pixel observation path and no CNN policy interface.
- **Any inter-seat communication, in any form, at any bandwidth.** `say` and `note` are one-way to the
  spectator feed; the other bug never sees either. This is not a v0.2 item — a zero-sum duel with a
  side channel is a different, worse game.
- **More than two seats, a variable seat count, teams, or a free-for-all with three bugs in the ring.**
  `num_agents` is 2 in every variant and the cert fixture.
- **Body variety** (ant vs bug vs spider vs humanoid, different masses, different leg counts,
  asymmetric matchups). Both bugs are identical in v1, which is what makes the score a clean measure
  of play. Per-body morphology is the obvious v0.2 variety and is not in v1.
- **Terrain, obstacles, ramps, a raised dohyō edge, multiple rings, or a moving ring centre.** One
  circular ring, centred, shrinking on a fixed law, every round.
- **Grappling, throws, joint locks, holding, or any contact model beyond disc impulses plus the
  grounded-leg shove.** No latching, no carrying, no lifting a body off the floor.
- **Stamina, energy budgets, damage, or a thrust cost.** The only running cost of effort is the tilt
  and traction it risks; scoring is round wins and nothing else.
- **Everything ctf's arena rules carried**: guns, flags, fog cones, first-person POV, lives, respawn,
  grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the barrage, the hill,
  the paint grid, procedural terrain, the map pool, the map editor and mapkit. Deleted, not disabled.
- **Player debug-sprite overlays** (ctf's `0x86` channel) and the zoom/minimap panel. The seats send
  no inputs and draw no overlays in v1; `#viewpanel` is removed because the ring is a fixed arena that
  always fits the frame.
- **Audio, 3D, camera cuts, slow-motion replays**, and any downloaded art asset.
- **Persistent memory across episodes** (no notes carried between matches) and any tournament
  structure beyond the platform league.
