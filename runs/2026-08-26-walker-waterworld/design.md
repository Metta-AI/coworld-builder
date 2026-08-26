# cogame-walker-waterworld — design note (2026-08-26, paintbot lineage)

`Metta-AI/cogame-walker-waterworld` is a **four-seat, fully cooperative continuous-control
coworld**: four thruster-driven skimmers patrol an 12.00 m × 8.00 m tank, feeling for drifting
plankton with sixteen short-range proximity sensors each. A plankton particle can only be taken by
**two skimmers touching it at the same instant** — one skimmer alone can nudge it and wait, nothing
more — and the same water carries eight drifting poison blooms that sting, stun and cost the whole
pod points. Nobody can talk. Every seat sees only what its own sensors reach. It is forked from
**`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount `/workspace/starters/coworld-ctf`.
**Every convention there holds here unless this note says otherwise** — the 24 Hz wall-clock-paced
game loop, the one-byte-per-seat-per-tick recorded action log, the `COWLDCTF`-family replay codec
with its per-tick `gameHash` chain, keyframes and lull spans, the server-side decision layer
(`src/ctf/{decide,directives,control,baselines,llm}.nim`: **one parallel LLM batch per turn**, two
bounded deadlines, an inter-batch rate floor, a budget guard, tolerant parsing, rune caps, a scripted
fallback), the mummy server and its `COGAME_*` runtime contract, the seat/cog split and the
`cogAlias` two-name-space rule, the broadcast chrome
(`client/replay_broadcast.html` + `client/chrome_common.js` + `client/broadcast_core.js`), the
emscripten static replay bundle (`replay-viewer/`, `Dockerfile.replay-viewer`,
`tools/build_replay_viewer.sh`) and the `GameVersion` prepend-only changelog discipline are all
inherited.

**Starter choice, in one line:** waterworld is a **real-time game loop with rules written fresh for
this coworld** — the first row of the starter table (`prompts/10-design.md`; `playbooks/make-coworld.md`
§Phase 0) — because paintbot already ships, tested, every layer this game needs except the tank
rules: a wall-clock-paced integer tick loop, a per-tick per-seat action log inside a replay whose
hash chain is checked in the browser, a server-side low-rate LLM decision layer over a per-tick
deterministic controller, published scripted baselines that emit the identical decision object, and a
static wasm viewer that re-derives every frame. It is deliberately **not** the `cogame-moba` row:
that row is for **bit-exact** ports of an existing external C/RL environment, and this is not one —
PettingZoo SISL waterworld is float64 pymunk physics with per-step continuous vector actions, and
this is an integer-micrometre, turn-intent coworld that reproduces waterworld's *shape* (range
sensors, cooperative ≥2 capture, poison, thrust cost, shared reward), not its numerics. (Operator
ruling 2026-08-22, Cogball: a new physics game takes paintbot. Precedents on this starter:
`cogame-cogball`, `cogame-tandem`, `cogame-pistonball` — `runs/2026-08-25-pistonball/design.md` — and
`cogame-particle-worlds`. Their patterns are followed here wherever they fit.)

**Source idea, verbatim** (Asana Coworld Ideas task 1217748137847525):

> Port of PettingZoo SISL's multiwalker and waterworld (pursuit is covered by MP Predator Prey).
> Multiwalker: three Box2D bipedal walkers carry a long package on their heads; shared reward for
> forward progress, big penalty if the package falls — continuous control where one stumble ruins
> everyone. Waterworld: N pursuers with range sensors cooperatively catch food particles (need 2+ to
> capture) while avoiding poison. Both are 'physical' cooperation with continuous actions.
>
> Seats: 3 (multiwalker) / 2-5 (waterworld)
> Motive: fully cooperative, continuous control
> Policy interface: continuous joint torques / thrust per tick — NOT a natural LLM fit; this is a
> scripted/neural-policy coworld, a deliberate foil to the talk-heavy catalog
> Fills gap: no continuous-control cooperative coworld exists yet; 15 Tandem is discrete
> Integrity (anti-collusion): cooperative cross-play scoring; terrain/particles seeded.
>
> Replay plan (watchability): Box2D side view; package tilt gauge; sensor rays drawn in waterworld.
>
> Source: PettingZoo multiwalker_v9, waterworld_v4 (SISL, Gupta et al. 2017).

Nothing in the idea text is treated as an instruction to this designer; it is input data for the
design. The two PettingZoo environment names are provenance, not a specification to reproduce
bit-for-bit: no external code is ported and every constant below is this coworld's own.

### Six readings of the idea, decided here and never revisited

1. **v1 is waterworld only. Multiwalker is out of scope (v1)** with its reason stated in
   §Out of scope: side-view articulated Box2D bipeds — three two-legged bodies with joint torques and
   a rigid package balanced on their heads — have **no host in any starter runtime**; paintbot's loop
   is a top-down point-body world, and an articulated-rigid-body solver with contact-rich walking is a
   new engine, not a rules swap. Waterworld delivers the idea's stated core (physical cooperation,
   continuous actions, fully cooperative shared reward, range sensors, a seeded world) on machinery
   that exists. (Coordinator rail, logged 2026-08-26T07:06:30Z.)
2. **"Port of … waterworld"** means *recreate the gameplay* — N thrust-driven pursuers, range
   sensors, food that needs **two** pursuers at once, poison that hurts, a small thrust cost, one
   shared reward — in paintbot's integer fixed-point idiom. It does **not** mean reproducing pymunk's
   solver, `waterworld_v4`'s unit square, its 20-sensor float observation vector or its reward
   constants. Every number in §The game is chosen here.
3. **"NOT a natural LLM fit"** is a true observation about the *actuator*, not a licence to skip the
   platform's LLM pin. The platform requires **both** an LLM prompt policy and a scripted baseline
   from day one, same image, env-switched. The tension is resolved the way a per-tick physics coworld
   must resolve it and the way pistonball and cogball already did: the LLM decides at a **coarse
   cadence** — one closed-schema **intent** per seat every **K = 72 ticks (3.0 s)** — and a
   deterministic controller turns the standing intent into a **per-tick thrust byte** at 24 Hz. The
   byte is the action; the byte is what the replay records; the byte is what the viewer replays. The
   scripted baseline is *the same controller* driven by a fixed heuristic intent policy, so the two
   policy kinds are strictly comparable and a baseline is legal by construction.
4. **"Seats: 2-5 (waterworld)"** is decided as **`num_agents` = 4**, everywhere, with no range and no
   variant that changes it (§Seats).
5. **"Integrity (anti-collusion): cooperative cross-play scoring; terrain/particles seeded"** is
   implemented as: one identical score for all four seats (so the ladder ranks a seat by the company
   it keeps), a **seeded** particle layout, a **seeded** seat→skimmer permutation drawn at `t = 0`,
   and a game that has **no notion of who holds any other seat**.
6. **"Replay plan: sensor rays drawn in waterworld"** is a hard requirement on the viewer, not
   flavour: the board draws all **sixteen rays per skimmer**, coloured by what the ray found
   (§Viewer readout 3). The multiwalker half of the replay plan (side view, package tilt gauge) goes
   out of scope with multiwalker.

**There is no `OPEN` section.** Every reading the idea leaves loose — how many seats, what the score
is, whether partners are visible to one another, how a continuous actuator becomes an LLM decision,
what ends the episode — is a rail the designer decides, and each is decided below with its reason.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How walker-waterworld satisfies it |
|---|---|
| Starter by game shape | **`Metta-AI/coworld-ctf` (paintbot)** — a real-time 24 Hz continuous-physics loop with new rules. The arena rules (teams, guns, flags, fog) are replaced by the tank; the loop, action-log replay, decision layer, viewer, chrome and CI wiring stay. (§Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-walker-waterworld`, **public at creation** — public is a certification prerequisite (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions: `walker-waterworld-tandemhunt`, `walker-waterworld-relay`) vs `PLAYER_SCRIPTED=shoal` / `PLAYER_SCRIPTED=drifter` (both fillers). One image `coworld-walker-waterworld`, one player entrypoint `/bin/walker-waterworld-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` under `game`; ctf's `tools/build_replay_viewer.sh` kept (its ecos `mkdir -p` fix is already at line 22 of the starter's copy); the **same** `src/waterworld/sim.nim` compiles into `replay-viewer/waterworld_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is ctf's page with a game block **appended**; the tank, skimmers, plankton, poison blooms and rock are baked at startup with pixie from ctf's shipped `data/font.ttf`, `data/arena_floor.png`, `client/art/walls/wall_h.jpg`, `wall_v.jpg`, `client/art/lockerroom/bg.jpg`. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | In-game every cog is `SKIM-1` … `SKIM-4` and nothing else; real policy names live only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (§Tests 11). |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | ≈329 s expected / ≈416 s absolute worst case against the 720 s budget; a **660 s** engine hard stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** in variant `default`, variant `sprint`, **and** `certification.game_config`; `<SEATS>` = **4** in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Four skimmers, five plankton, eight poison blooms, one rock, seventy-two seconds.** The skimmers
are little thruster drones in a shallow tank seen from above. Each one feels the water with sixteen
proximity sensors that reach 2.40 m — beyond that it is blind to plankton and to poison alike. A
plankton particle is **only** taken when **two** skimmers are touching it in the same instant, which
is worth **+10.000** to the whole pod; one skimmer alone gets **+0.050** for nudging it and nothing
else, so the whole game is *rendezvous*: find a drifting thing you can barely sense, and be on it at
the same moment as somebody else who cannot hear you. Poison blooms drift faster than plankton,
sting for **−2.000**, and stun the skimmer that touched one for half a second. Thrust costs a
little. The pod's score is one number and every seat gets it.

### Seats

**`num_agents` = 4. One seat = one skimmer.** Reasons, in order: (a) four is the smallest count that
supports **two independent capture pairs**, which makes the coordination problem a genuine choice
(who pairs with whom, and when to break a pair to cover a sighting) rather than the forced
2-of-2 rendezvous a 2-seat game would be; (b) four parallel LLM calls per turn sit comfortably inside
the Bedrock sidecar's 30-requests-per-minute-per-episode cap at a 12 s batch floor (§Decisions);
(c) a four-seat episode is exactly the platform's normal fill — two champions plus two fillers — so
the cross-play mean the ladder ranks by is meaningful from round one. The idea's 2–5 range is closed
here at **4** and is 4 in both manifest variants, in the certification fixture and in `SMOKE_SEATS`.

Seat `s` (slot 0..3) drives skimmer `perm[s]`, where `perm` is a permutation of `0..3` drawn once at
`t = 0` from `config.seed` by Fisher–Yates over one dedicated integer draw stream. Skimmer `i` always
spawns at the same point (below), so `perm` is what makes the spawn a seat gets — and therefore its
first neighbourhood of the tank — vary per episode. In-game the cog driving skimmer `i` is called
**`SKIM-<i+1>`** (`SKIM-1` … `SKIM-4`): an alias that names *a body on the board*, which every seat
legitimately knows, and never an entrant. `perm` is written into the replay config JSON (the viewer
needs it to map real names onto bodies) and into `results.skimmers`, and is **never** visible to any
seat.

Seats are symmetric in rules, scoring, observation shape and actuator. They are not symmetric in
where they start, and that asymmetry is re-dealt every episode by `perm` — the idea's anti-collusion
clause.

### World, units, and why they are integers

The whole sim runs in **integers**, for Cogball's, Tandem's and pistonball's reason: replays are
re-simulated by the **emscripten/wasm32** build of the same Nim module that the **native amd64**
server ran, and their per-tick `gameHash` chains must match bit-for-bit. Integers make that true by
construction rather than by an argument about two builds of libm agreeing.
`src/waterworld/{sim,tank,trig}.nim` contain **no floating point at all** (grep-enforced in CI,
§Tests 2d).

| Quantity | Unit | Type |
|---|---|---|
| Position, length, radius | micrometres (µm) | `int32` |
| Velocity | µm per tick | `int32` |
| Direction index (particles, thrust) | 1/32 turn, `0..31`, index `d` = bearing `11.25° · d` measured counter-clockwise from east in **view** orientation | `uint8` |
| Unit vectors | Q12 (4096 = 1.0), from the committed `DirQ12` table | `int32` |
| Score accumulators | **micro-points** (1e-6 of a score point) | `int64` |
| Counters (captures, nibbles, poison hits, draws) | — | `int32` |

**Tank:** `x ∈ [0, 12 000 000] µm` (12.00 m), `y ∈ [0, 8 000 000] µm` (8.00 m), origin top-left,
**y down** (ctf's screen convention). Board render scale **1 board pixel = 10 000 µm** →
`MapWidth = 1200`, `MapHeight = 800`, `BOARD_ASPECT = 1.5`. That is 960 000 logical map pixels
against ctf's 813 865, so `boardRenderScaleFor` still returns `RenderScale = 2`
(`MaxSupersampledMapPixels` is 8 000 000) and `predictedViewerRenderBytes(1200, 800)` is
**≈ 84 MB** against `WasmViewerBudgetBytes` 1 600 000 000 — the viewer's load-time capacity preflight
(`replay-viewer/ctf_replay.nim:74`) passes with three orders of magnitude of headroom and every one of
those constants is **kept unchanged**.

**View coordinates** — the only coordinates a policy or the chrome ever sees — are **metres with the
origin at the tank's bottom-left corner, x right, y up**: `X = x_µm / 1 000 000`,
`Y = (8 000 000 − y_µm) / 1 000 000`. Bearings reported to policies are **degrees counter-clockwise
from east in view orientation** (`0° = right`, `90° = up`), speeds are m/s, and every number shown to
a policy is rounded to 2 decimals.

`DirQ12*: array[32, tuple[x, y: int32]]` in `src/waterworld/trig.nim` is a **committed literal
table**, generated once by `tools/gen_trig_table.nim` and checked in, where entry `d` is
`(round(4096·cos(11.25°·d)), round(−4096·sin(11.25°·d)))` — i.e. the view bearing `11.25°·d` expressed
in **sim (y-down) components**, so the sim never negates anything at a call site. A test re-derives
every entry from `math.cos`/`math.sin` (§Tests 2e). Reflections are exact **index** arithmetic:

- off a **vertical** wall (x-component negated): `d' = (16 − d) mod 32`;
- off a **horizontal** wall (y-component negated): `d' = (32 − d) mod 32`;
- off the **rock**, about the outward normal index `n`: `d' = (2·n − d + 16) mod 32`.

`isqrt(v: int64): int64` (Newton's method, integer seed) is the only square root in the sim — contact
distances, speed clamps, sensor ranges — committed and unit-tested exhaustively below 2¹⁶ and on
perfect squares to 2⁴⁰.

### Geometry and constants (fixed; identical every episode)

```
ArenaW              = 12_000_000 µm   (12.00 m)
ArenaH              =  8_000_000 µm   ( 8.00 m)
SkimmerRadius       =    240_000 µm   (0.24 m)
FoodRadius          =    160_000 µm   (0.16 m)
PoisonRadius        =    160_000 µm   (0.16 m)
RockCentre          = (6_000_000, 4_000_000)
RockRadius          =    900_000 µm   (0.90 m)   -- one submerged rock, dead centre
SensorRange         =  2_400_000 µm   (2.40 m = 20 % of the tank's width, waterworld_v4's shape)
SensorCount         = 16                        -- world-fixed, 22.5 deg apart (even indices of DirQ12)
MaxThrustAccel      =      5_208 µm/tick^2      (3.00 m/s^2 at 24 Hz, at thrust level 7)
ThrustLevels        = 8                         -- level 0 = coast .. level 7 = full
DragNum/DragDen     = 39 / 1024 per tick        (~3.81 %/tick; terminal speed ~3.24 m/s)
MaxSkimmerSpeed     =    135_000 µm/tick        (3.24 m/s, magnitude clamp)
WallRestitutionNum/Den = 2 / 5                  (40 % rebound; a wall costs speed)
FoodCount           = 5    ids F1..F5
PoisonCount         = 8    ids P1..P8
FoodSpeedSet        = {28_000, 33_000, 38_000} µm/tick  (0.67 / 0.79 / 0.91 m/s)
PoisonSpeedSet      = {40_000, 46_000, 52_000} µm/tick  (0.96 / 1.10 / 1.25 m/s)
RespawnTicks        = 24                        -- 1.0 s after a particle is consumed
StunTicks           = 12                        -- 0.5 s of no thrust after a poison hit
CoopNeeded          = 2                         -- the whole point: 2+ skimmers, same tick
NibbleRearmUm       =    600_000 µm             -- separation that re-arms a (skimmer, food) nibble
CaptureMicro        = +10_000_000 micro-points  (+10.000)
NibbleMicro         =     +50_000 micro-points  (+0.050)
PoisonMicro         =  -2_000_000 micro-points  (-2.000)
ThrustMicroPerTick  = (level * level * 1000) div 49   -- level 7 = 1000 up (0.001 point/tick/seat)
CaptureTarget       = 20                        -- reaching it ends the episode `complete/target_met`
maxTicks            = 1728  (72.0 s)            -- 24 decision turns
turnTicks           =   72  ( 3.0 s)            -- K, the LLM decision cadence
```

**Skimmer spawns** (fixed, quadrant centres, at rest): skimmer 0 `(3.00, 2.00)`, 1 `(9.00, 2.00)`,
2 `(3.00, 6.00)`, 3 `(9.00, 6.00)` in **view** metres.

**Seeded draws.** Exactly three things are drawn at `t = 0`, in this fixed order, from one dedicated
stream seeded with `config.seed`: (1) `perm`; (2) the five plankton `(position, direction index,
speed)`; (3) the eight poison `(position, direction index, speed)`. Every particle spawn — at `t = 0`
and at every respawn — obeys the same acceptance predicate: at least **1.20 m** clear of the rock's
surface, **0.30 m** clear of every wall, and at least **2.00 m** from every *skimmer spawn point* at
`t = 0` (at a respawn, at least **1.50 m** from every *live skimmer*). Rejection sampling is bounded
at **64 attempts**, after which the spawn takes the first free point of a fixed 0.50 m lattice scanned
in raster order — degrade-never-hang applies to sampling too, and an unbounded rejection loop in a
hashed step function is exactly the hang this rule forbids.

Respawns draw **after** tick 0, so the sim keeps its stream live. Every draw goes through one helper,
`drawInt(lo, hi: int32): int32`, implemented as
`int32(lo + int32(rng.next() mod uint64(hi - lo + 1)))` — `rng.next()` is `std/random`'s
`uint64`-domain step, so **no draw ever touches `rand(int)`**, whose `int` is 32-bit under
`--cpu:wasm32` and 64-bit natively (ctf's documented hazard). A monotonic `rngDraws` counter is mixed
into `gameHash`, so a divergence in *how many* draws a build took is caught at the tick it happens
rather than as a mysterious position mismatch later.

### Time

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf** (`src/ctf/sim_types.nim:317,376`), because
every speed-coupled layer (`PlaybackSpeeds`, the lull scan, the momentum series, `tickTime`, the
transport bar) is keyed to it. There are **no substeps**: at 24 Hz a skimmer at full speed moves
135 000 µm (0.135 m) per tick against a 0.24 m radius and a 0.16 m particle, so the smallest body pair
overlaps for at least two consecutive ticks at closing speed and nothing tunnels. **The arithmetic
that makes that a guarantee rather than a hope:** the worst legal closing speed is a full-speed
skimmer meeting the fastest poison head-on, `135 000 + 52 000 = 187 000` µm per tick, against a
contact window of `SkimmerRadius + PoisonRadius = 400 000` µm — so the bodies overlap for at least
two consecutive end-of-tick positions in every legal configuration. The **swept-contact test** of
§Resolution order step 6 is nevertheless what ships, as belt and braces and because it makes the
guarantee testable (§Tests 1) rather than a comment.

An episode is **`maxTicks = 1728` ticks = 72.0 s of sim time**, divided into **24 decision turns of
`turnTicks = 72` ticks (3.0 s)**. The turn length is set by the wall-clock budget (§Decisions: four
parallel LLM calls per turn against the Bedrock sidecar's 30-rpm-per-episode cap), and 3.0 s of
open-loop intent is affordable because the controller between turns is **reactive** — an intent says
*what to go for*, and the controller watches the sensors and steers.

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 72 == 0` and `phase == Playing`: the intents collected for turn
   `t div 72` become each seat's `activeIntent[seat]` (§Server), quantised to integers on parse. The
   server writes one **`intent` chat record per seat** into the replay. `activeIntent` is **not**
   mixed into `gameHash` — the per-tick command bytes it produces are recorded, and those are what the
   viewer replays (step 2).
2. **Controller compile**, in **skimmer index order 0 … 3** (never seat order — seat order varies with
   `perm` and the loop must not). `control.thrustCommand(sim, i)` is a pure function of
   `(this skimmer's own state, its sensor frame, its seat's activeIntent, the tick)` returning a
   **command byte** `cmd ∈ 0 … 255`, where

   ```
   dir   = int(cmd) div 8      # 0..31, a DirQ12 index
   level = int(cmd) mod 8      # 0..7, thrust level; 0 = coast
   ```

   The byte uses the **whole** 0..255 range — 32 × 8 is exactly 256, so no value is reserved and no
   value needs repair (ctf's `ReplayInput.keys` is a plain `uint8`; nothing in the codec treats any
   value specially). The controller sits **outside** the determinism boundary, exactly as ctf's
   `control.nim` does, and may use floating point; the byte it produces is written to the replay with
   `replayWriter.writeInputMaskChange(tickTime(t), seat, cmd)`, which already writes **only on change**
   and updates `lastMasks[seat]` (`src/ctf/replays.nim:161`). Nothing else in the loop is re-derived at
   playback.
3. **Skimmer dynamics**, skimmer index order:
   1. If `stun[i] > 0`: `level := 0` (thrust ignored), `stun[i] -= 1`.
   2. `v += (DirQ12[dir] * MaxThrustAccel * level) div (7 * 4096)` — computed in `int64`, narrowed.
   3. Drag: `v -= (v * 39) div 1024` (truncating toward zero, so drag is symmetric under negation).
   4. Speed clamp: if `vx² + vy² > MaxSkimmerSpeed²` then `v := (v * MaxSkimmerSpeed) div isqrt(vx² + vy²)`.
   5. `pos += v`.
   6. **Walls**: if `x < SkimmerRadius` or `x > ArenaW − SkimmerRadius`, clamp `x` to the wall and set
      `vx := −(vx * 2) div 5`; same for `y`. Corners resolve x then y.
   7. **Rock**: with `dSq = (pos − RockCentre)²` and `R = RockRadius + SkimmerRadius`, if `dSq < R²`:
      let `d = isqrt(dSq)` (if `d == 0`, use normal index 0), `n̂ = ((pos − RockCentre) * 4096) div d`;
      push the centre out to exactly `R` along `n̂`; then with `vn = (v · n̂) div 4096`, set
      `v := v − (7 * vn * n̂) div (5 * 4096)` (remove the normal component and return 40 % of it).
4. **Particle motion**, plankton in id order then poison in id order. A live particle moves
   `pos += (speed * DirQ12[d]) div 4096`; a wall crossing clamps the centre inside and mirrors `d` by
   the index rule above; a rock overlap pushes the centre out to `RockRadius + ParticleRadius` and
   reflects `d` about the **nearest of the 32 outward normal indices**. **Particles therefore travel
   at exactly constant speed forever** — direction changes only at a bounce, and the whole motion is
   integer-exact with no energy drift to renormalise. A particle in `Respawning` state ticks its timer
   down; at zero it respawns from the seeded stream (spawn predicate above) in state `Live`.
5. **Sensor frames** are rebuilt for every skimmer (§The sensor frame). They are **derived state**: a
   pure integer function of hashed state, recomputed identically native and in wasm, and therefore
   **not** mixed into `gameHash` — its inputs already are.
6. **Contacts**, in this exact order. Every test is a **swept** overlap: a contact counts if the two
   bodies overlap at the tick's end position **or** if the segment travelled by their relative
   displacement this tick passes within `rA + rB` of each other (closest point of a segment to the
   origin — integer, `isqrt`-free until the final compare).
   1. **Poison**, skimmer index order then poison id order: a live poison overlapping skimmer `i`
      is **consumed** (state `Respawning`, timer `RespawnTicks`), `poisonHits += 1`,
      `poisonBySeat[i] += 1`, `scoreMicro += PoisonMicro`, `stun[i] := StunTicks`, and the skimmer's
      speed is halved (`v := v div 2`). A skimmer overlapping **two** poisons in one tick consumes
      both and pays both (stated so it is not a surprise).
   2. **Capture**, plankton id order: count the skimmers overlapping live plankton `f` (a **stunned**
      skimmer still counts — a body in the water still holds the plankton, and the alternative
      punishes the pod twice for one mistake). If `count ≥ CoopNeeded`: the plankton is **captured** —
      consumed, `captures += 1`, `scoreMicro += CaptureMicro`, `assists[j] += 1` for every
      participating skimmer's seat, and a `capture` event names every participant. Otherwise if
      `count == 1` and `nibbleArmed[i][f]`: `nibbles += 1`, `nibblesBySeat[i] += 1`,
      `scoreMicro += NibbleMicro`, `nibbleArmed[i][f] := false`. `nibbleArmed[i][f]` is re-armed the
      first tick their centres are more than `NibbleRearmUm` apart, and is forced true for every
      skimmer when plankton `f` respawns. (This is what stops a lone skimmer farming +0.050 a tick.)
7. **Thrust cost**, skimmer index order: `thrustMicro += (level * level * 1000) div 49` for the level
   *actually applied* this tick (a stunned skimmer pays nothing). At full throttle for the whole
   episode that is `1000 × 1728 × 4 = 6.912` points — real, small, and the reason a policy that
   flat-out sprints everywhere loses to one that coasts.
8. **Score.** `scoreMicro` is the single running total:
   `10 000 000·captures + 50 000·nibbles − 2 000 000·poisonHits − thrustMicro`.
9. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged. `gameHash` mixes `tick`, `phase`, every skimmer's `pos`, `v`, `stun`, every particle's
   `state`, `pos`, `dir`, `speed`, `timer`, all of `captures`, `nibbles`, `poisonHits`, `thrustMicro`,
   `scoreMicro`, `rngDraws`, and a digest of `perm`. It never mixes sensor frames, FX, notes, `say`,
   feed text or policy labels.
10. **End checks**, in this order: `captures ≥ CaptureTarget` → end `complete` / `target_met`;
    wall-clock stop tripped → end `deadline` / `wall_clock`; `t + 1 ≥ maxTicks` → end `complete` /
    `full_time`; an invariant guard failure (a body centre outside the tank, `|v|` above the clamp,
    a direction index outside `0..31`, a particle timer outside `0..RespawnTicks`, a spawn that fell
    through to the lattice more than 8 times in an episode, an `int32` overflow caught by the debug
    build's range checks) → end `fault` / `sim_fault`.

There is no rescue rule and no difficulty ramp. A pod that spends 72 s bumping into poison ends
`full_time` with a negative score — a legible, correctly scored failure.

### The sensor frame (what a skimmer can feel)

`sensors.frameFor(sim, i)` is the **one** function that builds a skimmer's percept; both the seat's
websocket frame filter and the LLM user message are built from it, and the viewer draws exactly what
it returns. There is no second path.

- **Detection is range-based, not ray-based**: a plankton or poison particle is detected by skimmer
  `i` iff the distance between centres is `≤ SensorRange` (2.40 m). This is a deliberate departure
  from `waterworld_v4`'s literal ray sensors, decided here: a 0.16 m particle at 2.40 m subtends 7.6°
  and would slip between 22.5° rays, producing a percept that is confusing to a spectator and
  arbitrary to a policy. Nothing hides between rays.
- **The sixteen rays are the presentation of that percept**, and they are what the viewer draws. Ray
  `n` (`n ∈ 0..15`) points along `DirQ12[2n]` — view bearing `22.5°·n` — and reports the **nearest**
  of: (a) any detected particle or skimmer whose bearing falls in the ray's ±11.25° sector, and
  (b) the geometric distance along the ray to the **rock** or the **tank wall** (a ray/circle and
  ray/rectangle cast, integer, capped at `SensorRange`). Each ray therefore reports exactly one
  `{k, d, closing}` where `k ∈ {food, poison, cog, rock, wall, clear}`, `d` is metres and `closing` is
  the radial closing speed `−(v_object − v_self) · r̂` in m/s (0 for rock and wall).
- **The other three skimmers are always detected, at any range.** Decided here, with the reason: the
  pod shares a transponder. Capture needs two bodies on one particle at one instant and there is **no
  communication channel of any kind**; with partners invisible beyond 2.40 m in a 12 × 8 m tank,
  rendezvous would be luck, not play. Prey stays hidden (that is the interesting locality); teammates
  do not. A partner beyond `SensorRange` appears in `partners[]` with position, velocity and stun
  state but occupies **no** ray (rays are the 2.40 m percept), which is exactly how the viewer draws
  it too.

### Scoring, sign, and what the league ranks by

The game is **fully cooperative**: every seat receives **the identical score**, computed once.

```
score = scoreMicro / 1_000_000
      = 10.000*captures + 0.050*nibbles - 2.000*poisonHits - thrustCost
results.scores = [score] * 4
results.win    = [captures >= CaptureTarget] * 4
```

**Higher is better. Captures are positive; poison and thrust are negative.** There is no time bonus
and no time penalty: the clock is fixed, so the only thing time does is limit how much a pod can take.
Reaching `CaptureTarget = 20` ends the episode immediately at **+200 and change**, which is the
scoring cap; below it is unbounded only in the negative direction (a pod that swims through poison for
72 s can in principle reach the low hundreds negative; realistically the floor is about −60).
Scores are emitted as doubles rounded to **3 decimals**, computed once and copied into all four slots
so the numbers are bit-identical.

Worked examples:

| Outcome | captures | nibbles | poison hits | thrust cost | **score** |
|---|---|---|---|---|---|
| Two disciplined pairs; target met at 58 s | 20 | 26 | 2 | 5.10 | **+192.200** |
| Good pod, full time | 13 | 31 | 3 | 6.40 | **+119.150** |
| One pair works, the other two drift | 7 | 22 | 5 | 5.80 | **+55.300** |
| Four `drifter`s: captures only by coincidence | 3 | 18 | 7 | 4.60 | **+12.300** |
| Everybody chases everything, poison included | 1 | 9 | 19 | 6.90 | **−34.450** |
| Nobody thrusts at all (plankton drifts in) | 0 | 2 | 0 | 0.00 | **+0.100** |

**What the league ranks by: the seat's mean `results.scores` value across its episodes — its
cross-play mean.** Elo is **wrong** for this coworld and phase 50 must not use it: with four
identical scores every episode is a four-way draw and Elo cannot separate anybody (the same ruling as
`cogame-raid`, `cogame-tandem` and `cogame-pistonball`). The cross-play mean is also the idea's
integrity clause: because the score is joint, the seat→skimmer map is re-dealt every episode, and a
four-seat episode is normally two champions plus two fillers, a policy that only performs alongside its
own twin shows up the moment its mean includes episodes seated beside `walker-waterworld-shoal` and
`walker-waterworld-drifter`. **v1 game code has no notion of who is in any other seat.**

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail. No
other value may appear in either field.

| `reason` | `endRule` | When | Scored |
|---|---|---|---|
| `complete` | `target_met` | `captures ≥ 20`. The good ending; `win` is true. | as at the capture tick |
| `complete` | `full_time` | `maxTicks` (1728) reached. The normal ending. | as at `maxTicks` |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed first. The sim stops at that tick, scores the state as it stands, writes the game-over frame and a complete replay up to that tick. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. | as at the stop tick |
| `fault` | `sim_fault` | A step-10 invariant guard tripped. Partial replay written. | as at the fault tick |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts written before re-raising. | as at the fault tick |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (1728 = 72 s of
lobby) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only, `src/ctf/server.nim`), its skimmer is driven by the
`shoal` baseline for the whole run, and the run plays to a normal ending. Three skimmers can still
capture, so the episode remains meaningful.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {shoal, drifter}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=shoal`. A scripted policy seated as a champion is a FAILURE state.

### Where the decision happens, and the LLM client

In the **game server**, not the player container — paintbot's own architecture
(`src/ctf/llm.nim`, `src/ctf/decide.nim`, `src/paintball_player.nim`), kept. The `anthropic_api_key`
coworld secret is injected into the *game* pod via
`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/walker-waterworld/anthropic_api_key`;
without that manifest env the hosted container never receives the secret and every league episode
plays scripted while local certify still passes (hive, 2026-08-23). Phase 60 greps the *game* log for
`falling back` / `LLM provider is unavailable`.

`src/waterworld/llm.nim` is `src/ctf/llm.nim` with the identifier rename only. Kept exactly:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (`readCogameUri`) → **none** (client
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

One decision turn every **K = 72 ticks (3.0 s of sim time)**, **24 turns** per episode. At each turn
the server builds all four seats' request bodies and issues them as **ONE parallel batch** —
`client.curl.makeRequests(@[req0 … req3], timeout)`, curly's batch API, which is exactly what
`src/ctf/decide.nim:427` already does. **Seats are never queried sequentially.** Four calls per turn ×
24 turns = **96 calls** per episode, at most 4 in flight.

The binding constraint is not latency, it is the **Bedrock sidecar's cap of 30 requests per minute per
episode** (playbook gotcha, raid round 2). Four requests per batch means a batch may start at most
every 8 s; the design uses **`minBatchSpacingMs` (ctf's `turnSpacingMs`) = 12 000** → 4 requests /
12 s = **20 rpm**, comfortably under. That, not the model, is why there are 24 turns and why a turn is
3.0 s of sim time.

Per-turn timing, all monotonic-deadline bounded, and every deadline a whole number of seconds because
curly hands it to `CURLOPT_TIMEOUT`, whose granularity is whole seconds and whose conversion **floors**
(`src/ctf/decide.nim:419-428`):

- attempt 1 batch deadline **`attempt1Ms = 9 000`** (four parallel haiku calls; ~3–6 s typical);
- every seat that timed out, errored, returned non-JSON or returned no usable intent is retried
  **once**, again as a single batch, deadline **`retryMs = 5 000`** — unless the client is `throttled`,
  in which case the retry is skipped outright;
- the whole turn is wrapped in **`turnBudgetMs = 16 000`** (`attempt1Ms + retryMs = 14 000 ≤ 16 000`,
  asserted by §Tests 12);
- the **inter-batch wall floor** of 12 000 ms is measured start-to-start and is a bounded,
  stop-interruptible `sleep`.

```
turn 0 batch starts at t = 0; turns 1..23 start 12 s apart      = 276 s
last turn's own LLM cost (<= 16 s hard cap)                     =  16 s
lobby / connect wait for 4 player pods (typical 15 s;
  cap lobbyJoinTimeoutTicks 1728 = 72 s)                        =  15 s   (typical)
1728 ticks of physics + 4 controllers + 4 sensor frames/tick    =   2 s
game-over hold + results + replay write (retrying uploader)     =  20 s
                                                                -------
expected total                                                  ~329 s   < 720 s budget
absolute worst case (72 lobby + 276 + 16 + 2 + 20 + 30 slack)    ~416 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                          = 660 s  -> reason "deadline"
platform kill (episodeTimeoutSeconds)                            = 1200 s
```

`fastMode: true` in every variant: the sim advances as soon as every player container has
acknowledged the frame, so sim time is not charged against the wall clock — the decision turns are the
pacing. The seats send no inputs at all (the server computes every command byte), so
`docs/PROTOCOL.md`'s warning about the Sprite v1 Ready packet (`0x85`) corrupting dead-reckoned input
timing does not apply, and the player harness sends `0x85` after every frame exactly as
`src/paintball_player.nim` does.

**Budget guard (settles early without shortening the run).** At the start of each turn, if
`elapsed + 2 × (minBatchSpacing + turnBudget) > wallClockBudgetSeconds`, the LLM is switched off for
every remaining turn and the run finishes on the scripted layer (microseconds per turn), so the episode
ends `complete/*` rather than `deadline`. A `budget_guard` record names the turn it fired. This is
ctf's own guard (`src/ctf/decide.nim:340`), retargeted to include the batch spacing.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the inter-batch floor, the
outer per-turn deadline, `lobbyJoinTimeoutTicks` on the connect wait, the bounded spawn rejection
sampler, mummy's socket timeouts on the serve thread (which runs independently of the game loop, so a
16 s LLM stall cannot drop four connections), the 660 s engine stop, and ctf's `gameOverTicks` hold
before exit. On **two** consecutive failures for a seat (attempt + retry, or one attempt when
`throttled`) that seat's intent for the turn is the **`shoal`** intent and a `fallback` record is
written with `cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}`.
A seat that disconnects mid-run keeps playing: its intent source degrades to `shoal` and revives on
reconnect. **No failure mode leaves a skimmer uncommanded** — the controller always has an intent:
this turn's, else last turn's, else `shoal`'s.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are ONE of four thruster drones ("skimmers") in a shallow tank seen from
above. The tank is 12.00 m wide and 8.00 m tall. Coordinates are metres from
the bottom-left corner; x runs right, y runs up. Bearings are degrees
counter-clockwise from east: 0 = right, 90 = up, 180 = left, 270 = down.
There is one round rock of radius 0.90 m dead centre at (6.00, 4.00).
THE POINT OF THE GAME: plankton drifts around the tank. A plankton particle is
only CAUGHT when TWO OR MORE skimmers are touching it AT THE SAME MOMENT. That
is worth +10 to everyone. One skimmer alone touching it is worth +0.05 and
nothing more, so the whole game is meeting a partner on a moving target.
Poison blooms also drift, faster. Touching one costs -2 and stuns you for half
a second. Thrusting costs a tiny amount, so full throttle everywhere loses to
coasting.
YOU FEEL THE WATER WITH 16 SENSORS THAT REACH ONLY 2.40 m. Beyond that you
cannot see plankton or poison at all. You CAN always see the other three
skimmers - position, velocity, stun - because the pod shares a transponder.
You CANNOT talk to anyone and nobody sees anything you write.
Everyone in the pod gets the SAME score. 20 catches ends the run early and
wins it.
Every 3 seconds you set your ORDER for the next 3 seconds. A deterministic
autopilot runs it 24 times a second: it steers, it leads a moving target, it
backs off poison for you. You choose WHAT to go for and HOW hard.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars, your reasoning",
 "mode":"hunt"|"escort"|"sweep"|"hold"|"avoid",
   // hunt   : drive at the plankton named in "target" (or, if you cannot
   //          sense it, the nearest plankton you CAN sense; if none, the
   //          waypoint), aiming where it will be in lead_ticks
   // escort : drive to the skimmer named in "partner", stopping 0.80 m short
   //          of it - unless you sense plankton within 1.50 m of that partner,
   //          in which case you go to the plankton instead. THIS is how two
   //          skimmers arrive together.
   // sweep  : drive to "waypoint" and hold there. Searching.
   // hold   : brake to a stop where you are. Waiting on a partner.
   // avoid  : run away from the nearest poison you sense (to the tank centre
   //          if you sense none)
 "target":"F1".."F5" or "none",     // a plankton id you have sensed
 "partner":"SKIM-1".."SKIM-4" or "none",
 "waypoint":[x,y],                  // metres, clamped into the tank
 "lead_ticks":0..24,                // aim where the target will be this many
                                    // ticks from now (24 ticks = 1 second)
 "standoff_m":0.0..2.5,             // how wide the autopilot swings around
                                    // poison. 0 = ignore it, 2.5 = paranoid
 "throttle":0.0..1.0,               // fraction of full speed you ask for
 "say":"<=48 chars"}                // spectators only; no skimmer ever sees it
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(paintbot's `operatorBlock`, kept), a blank line, then the seat's sensor-frame JSON (§Server). The
prompt text is never echoed into the replay — only `policyKind`, the label and the resulting intent.

### Champion #1 — `walker-waterworld-tandemhunt` (owner daveey), `PLAYER_PROMPT`

```
Hunt in a fixed pair and never break it. Your partner is the skimmer whose
number differs from yours only in the last bit: SKIM-1 pairs with SKIM-2, and
SKIM-3 pairs with SKIM-4. Read your own alias first, then work out your
partner's, then keep that partner within about 3 m for the whole episode -
two skimmers 6 m apart cannot catch anything, no matter how much plankton
either of them can smell.
Rules, in order. If you sense poison closer than 0.80 m, mode "avoid",
throttle 1.0, for one turn only. Otherwise, if you sense a plankton AND your
partner is within 3.20 m of it, mode "hunt" that plankton, lead_ticks 8,
throttle 1.0, standoff_m 1.2 - you are both going to arrive and that is the
+10. Otherwise, if you sense a plankton but your partner is far from it, still
"hunt" it with throttle 0.6 and lead_ticks 4 if you are already inside 1.20 m
of it (sit on it, take the +0.05, and wait - your partner is coming), but
"escort" your partner with throttle 1.0 if you are further away than that:
fetching your partner is worth more than being alone on food.
Otherwise "escort" your partner if you are more than 2.40 m apart. If you are
together and nobody smells anything, "sweep": pick the waypoint of the four
corners of the search box - [3,2], [9,2], [9,6], [3,6] - that is FURTHEST from
where you are now, so the pair sweeps the tank instead of orbiting one corner,
and set throttle 0.7 to keep the thrust bill down.
Keep standoff_m at 1.2 unless you have been stunned this episode, then 1.8.
Never set standoff_m above 2.0: a paranoid autopilot will not close on food.
```

### Champion #2 — `walker-waterworld-relay` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Play zones and relay, not fixed pairs. Split the tank at x = 6.00. SKIM-1 and
SKIM-3 own the LEFT half, SKIM-2 and SKIM-4 own the RIGHT half. Read your alias
and know which half is yours.
Inside your own half you are the finder: "sweep" between [2.0,2.0], [2.0,6.0],
[4.5,4.0] (left) or [10.0,2.0], [10.0,6.0], [7.5,4.0] (right), throttle 0.65,
picking whichever of your three points is furthest from you, standoff_m 1.4.
The moment you sense a plankton in your half, stop sweeping: "hunt" it with
lead_ticks 10 and throttle 1.0 if the nearest OTHER skimmer is within 3.50 m of
you, because that skimmer will follow you in; otherwise "hunt" it with throttle
0.5 and lead_ticks 2, which parks you on it and keeps it in your sensors while
somebody arrives.
You are the relay for your zone partner - the other skimmer whose home half is
yours. If your zone partner is inside 1.00 m of a plankton you can also sense,
"hunt" that plankton at throttle 1.0, lead_ticks 6. If your zone partner is
holding still in your half and you sense nothing yourself, "escort" it: it is
almost certainly sitting on food you cannot smell yet.
Cross the midline only to "escort" a skimmer that has been stationary for a
whole turn. Poison: if anything reads poison inside 1.00 m, "avoid" at throttle
1.0 for one turn, then go back to your zone with standoff_m 1.8.
```

### The controller (deterministic, one function, shared by every policy)

`src/waterworld/control.nim`, `thrustCommand(sim, i) -> uint8`, evaluated once per tick per skimmer in
index order. Both LLM intents and scripted-baseline intents are compiled by this same code, so the two
policy kinds are strictly comparable and a baseline is legal by construction. It sits **outside** the
determinism boundary (ctf's rule: recorded bytes, not re-run logic) and may use floats.

With `p` = my centre, `v` = my velocity, `S` = my sensor frame, `I` = my seat's active intent:

1. **Goal point `G`:**
   - `hold` → `G = p` (the servo then brakes).
   - `sweep` → `G = I.waypoint`.
   - `hunt` → the plankton named by `I.target` **if it is currently detected**; else the nearest
     detected plankton; else `I.waypoint`. `G = q + u·I.lead_ticks` where `q, u` are that particle's
     position and velocity (a straight-line lead, deliberately not a bounce-aware prediction — an
     agent that wants a bounce accounted for must ask for a shorter lead).
   - `escort` → let `m` be the skimmer named by `I.partner` (nearest other skimmer if the name is
     `none` or unrecognised) and `m*` its position led by `I.lead_ticks`. If a detected plankton lies
     within **1.50 m** of `m*`, `G` is that plankton's led position; otherwise `G` is the point
     **0.80 m short of `m*`** on the segment from `p` to `m*` (so two escorting skimmers converge to a
     rendezvous rather than colliding).
   - `avoid` → with `z` the nearest detected poison, `G = z + 2.50 m · (p − z)/|p − z|`; if no poison
     is detected, `G` = the tank centre offset 1.60 m along `(p − RockCentre)` (never *into* the rock).
2. **Poison repulsion (always, every mode).** For every detected poison within `I.standoff_m`, add
   `1.5 · (standoff − d)/standoff · (p − z)/|p − z|` to a repulsion accumulator. The steering direction
   is `normalise(normalise(G − p) + repulsion)`; if that sum is degenerate (|·| < 1e-6), keep last
   tick's steering direction, and on tick 0 use `(G − p)` unrepelled.
3. **Rock avoidance.** If the segment `p → G` passes within `RockRadius + SkimmerRadius + 0.20 m` of
   `RockCentre`, the steering direction is rotated to the tangent on the side that keeps `G` nearer —
   the only path-planning in the controller, and it is a single rotation, not a planner.
4. **Velocity servo.** `v* = steer · min(1, throttle) · MaxSkimmerSpeed`, except `hold` → `v* = 0`, and
   except that within **0.30 m** of `G` in `sweep`/`hold` the target speed tapers linearly to 0 (so a
   skimmer parks instead of orbiting). `a = v* − v`.
5. **Quantise.** `dir = ` the index of `DirQ12` nearest in angle to `a`;
   `level = clamp(round(|a| · 7 / MaxThrustAccel), 0, 7)`; `cmd = dir · 8 + level`.
6. **Phases other than `Playing`, and any tick with `stun[i] > 0`,** force `cmd = 0` (coast).

The controller contains **no memory across ticks except the last steering direction**, no knowledge of
any other seat's intent, and no access to any particle it has not detected — `tests/test_locality.nim`
asserts the signature cannot see more.

### Scripted baselines

Both emit the *same* intent object on the same 72-tick cadence, so their output is legal by
construction and directly comparable to an LLM's, and both are pure functions of the observation a
seat would receive.

- **`shoal`** — the certification player, the per-turn fallback, and the default for a seat that
  registers with neither env var. **Algorithm, evaluated once per turn for skimmer `i` with
  `mate = i xor 1`:**
  1. If `stun[i] > 0` → `{mode: hold, throttle: 0}`.
  2. Else if a poison is detected within **0.90 m** → `{mode: avoid, throttle: 1.0, standoff_m: 1.8}`.
  3. Else if a plankton `f` is detected **and** `dist(mate, f) ≤ pairJoinRadius` (default **3.20 m**) →
     `{mode: hunt, target: f, lead_ticks: 8, throttle: 1.0, standoff_m: 1.2}`, choosing the `f` with
     the smallest `dist(me, f) + dist(mate, f)`.
  4. Else if a plankton `f` is detected and `dist(me, f) ≤ 1.00 m` →
     `{mode: hunt, target: f, lead_ticks: 2, throttle: 0.5, standoff_m: 1.2}` (sit on it and wait).
  5. Else if a plankton is detected (mate far, me far) →
     `{mode: escort, partner: SKIM-<mate+1>, lead_ticks: 6, throttle: 1.0}`.
  6. Else if `dist(me, mate) > 2.40 m` → `{mode: escort, partner: SKIM-<mate+1>, throttle: 0.9}`.
  7. Else → `{mode: sweep, waypoint: patrol[(turn div 2) mod 4], throttle: 0.70}` where `patrol` is the
     fixed circuit `[(3,2), (9,2), (9,6), (3,6)]` **indexed identically for both members of the pair**,
     so a shoal pair sweeps the tank together (that shared index, and nothing else, is what makes two
     independent copies of this algorithm cooperate — no communication is used or needed).
  `say` is one of four fixed strings chosen by which branch fired. Four `shoal`s reliably capture
  without communicating, which is the behaviour the game is about — and the anti-regression pin of the
  whole physics tuning (§Tests 5).
- **`drifter`** — the second filler, deliberately different in shape and weaker: it never coordinates
  and never escorts. `{mode: hunt, target: nearest detected plankton, lead_ticks: 0, throttle: 0.70,
  standoff_m: 0.60}` whenever anything is detected, else `{mode: sweep, waypoint: L[(turn) mod 6],
  throttle: 0.70}` over a fixed six-point serpentine `[(1.5,1.5), (10.5,1.5), (1.5,4.0), (10.5,4.0),
  (1.5,6.5), (10.5,6.5)]`. Two drifters capture only when they happen to converge, which gives the
  ladder a spread and gives a champion a bad neighbour to cope with.

Three tunables — `pairJoinRadiusUm` (3 200 000), `standoffMilli` (1 200) and `leadTicks` (8) — are a
`BaselineParams` object, not literals, exactly as `src/ctf/baselines.nim` does it (its
`DefaultBaselineParams` comment is the template): `tools/tune_baselines.nim` sweeps them over a bounded
grid, `tools/ci/baseline_tuning.json` records the sweep's pick, and `tests/test_tuning.nim` asserts the
shipped defaults still equal it. **The physics constants in §The game are not swept and are not
tunable** — if four `shoal`s cannot capture, the sweep moves these three numbers, not the sim.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf/paintball arena rules go** (teams, guns, flags, fog cones, lives, respawn,
grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the hill, the
paint grid, the map pool and the map editor all leave the repo):

| ctf path | walker-waterworld |
|---|---|
| `src/ctf/sim.nim` (4102 lines: gameplay core, combat, vision, items) | `src/waterworld/sim.nim` — the skimmer/particle physics core and the step loop of §The game. |
| `src/ctf/arena.nim`, `paint.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `rig_art.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `tools/map_render.nim`, `docs/MAPKIT.md`, `docs/pool-review.html`, `scripts/` | `src/waterworld/tank.nim` — the fixed geometry of §The game, the seeded `perm`, the bounded seeded spawn sampler, the swept-contact tests, and the pixie tank bake. **Deleted, not ported**; there is no map generator, no `mapSpec`, no wall mask and no procedural terrain in this coworld. |
| `src/ctf/global.nim` (8070 lines) fog of war, vision cones, first-person raycast, killfeed art, item sprites | `src/waterworld/global.nim` — top-down sprite composition: water, rock, skimmers with thruster plumes, **sixteen sensor rays per skimmer**, plankton, poison, capture rings, bubbles, FX. Perfect information spectator-side; the per-seat stream is sensor-filtered. `boardRenderScaleFor`, `MaxSupersampledMapPixels`, `predictedViewerRenderBytes`, `WasmViewerBudgetBytes` and `shoutBubbleZoomFor` are **kept verbatim**. |
| `src/ctf/directives.nim` (`Intent`, `CogOrder`, `SquadDirective`) | `src/waterworld/intents.nim` — the `SkimmerIntent` object, the closed `Mode` enum, the tolerant parser and the repair table of §Server. Same file shape, same rune discipline (`truncateRunes`, `sanitizeSay`, the no-leading-brace rule for `say`). |
| `src/ctf/control.nim` (nav grid, flow fields, aim) | `src/waterworld/control.nim` — `thrustCommand` of §Decisions. ~180 lines instead of 536; no nav grid, no flow field, no cached fields. |
| `src/ctf/baselines.nim` (`holdline`, `sprayer`) | `src/waterworld/baselines.nim` — `shoal`, `drifter`, and `BaselineParams`. |
| `players/baseline/` (the CTF bot) | deleted; the only player binary is `src/walker_waterworld_player.nim`. |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/paintball/`, `docs/plans/*` | rewritten for waterworld; ctf's plans/designs deleted. |
| `arena/`, `caos/`, `caos-tools/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/render_map_pool.nim`, `tools/build_pool_review.py`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf`/`paintball` → `waterworld` rename sweep only, `CTF_WIRE` →
`WATERWORLD_WIRE`; a CI grep asserts no `ctf_`/`CTF_`/`paintball` identifier survives outside comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/waterworld/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `writeInputMaskChange` (used **as-is**, unlike pistonball, because our command byte is a value and `writeInputMaskChange` already writes change-only), `checkReplayHash`. Two named edits below. |
| `src/ctf/replay_runtime.nim` → `src/waterworld/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports. |
| `src/ctf/server.nim` → `src/waterworld/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the held-registration table, the frame limiter, the replay-switch path, the `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. Five named edits below. |
| `src/ctf/llm.nim` → `src/waterworld/llm.nim` | the credential ladder, the single-haiku model list, the `throttled` fast-fail, `curly.makeRequests` batching, `extractJsonObject`, rune truncation. Rename only. |
| `src/ctf/decide.nim` → `src/waterworld/decide.nim` | the turn loop, `SeatPolicy`, the two-deadline retry, the inter-batch floor, the budget guard, `repairMissingOrders` (retargeted: a missing field keeps last turn's value, else `shoal`'s), the `records` queue. It is already a loop over `sim.seatCount()` seats that batches them, so retargeting from 2 to 4 seats is a constant. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/sim_config.nim` | `GameConfig` lifecycle and `config.update`; waterworld's fields replace the arena's. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; waterworld result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim` | HUD label composition. |
| `src/ctf/broadcast.nim` | `stepEvents` / `BroadcastTracker` / `buildStateJson` — the state-delta → broadcast-event derivation, retargeted to waterworld's event kinds and state keys (§Viewer). |
| `replay-viewer/config.nims`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/chrome_common.js` | **byte-for-byte**, zero edits (§Viewer). |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome, with a game block appended (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/wasm_replay_smoke.cjs`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix`, `flake.lock`, `config.json` | build, bundle, tuning and forensics wiring. `tools/build_replay_viewer.sh` already carries the ecos `mkdir -p` fix at line 22 and keeps it; only `image_tag` and the `docker cp` source path `/workspace/waterworld/replay-viewer/dist/.` change. |
| `data/font.ttf`, `data/FONT_LICENSE.txt`, `data/arena_floor.png`, `data/darkbg.png`, `data/ascii.png`, `data/atlas/*`, `client/art/walls/*`, `client/art/lockerroom/bg.jpg` | real art, kept. Everything CTF-specific (`soldier_*`, `heart_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, `crew.png`, `rig_real/`, the coloured locker-room sprites) is deleted. |

**The five named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   waterworld calls `control.thrustCommand(sim, i)` for all four skimmers and passes the command-byte
   array into `sim.step`. **Player sockets contribute no input**: any input mask arriving on a player
   socket is discarded.
2. **Replay input write.** `writeInputFrameMasks` (the press/release wrapper at
   `src/ctf/server.nim:1088`) is **deleted** — its `repeatedPressedMask` logic is button semantics and
   would corrupt a value byte. Waterworld calls `replayWriter.writeInputMaskChange(tickTime(tick),
   seat, cmd)` directly (the codec's own change-only guard does the rest), and `decodeInputMask` is
   replaced by `decodeThrust(cmd: uint8): tuple[dir: int32, level: int32]`.
3. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop runs
   `decide.turn(sim, engine, …)`, which enforces the inter-batch floor, issues the one parallel
   four-request batch, applies the deadlines, installs the intents and writes the `intent`/`fallback`
   records — all inside a monotonic `turnBudgetMs` bound.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration forces
   `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.
5. **Shutdown grace.** `/healthz` and `/global` keep answering for a bounded ~20 s after the artifacts
   are written, then the process exits (lantern 0.1.3: the episode runner pings `/global` with a 2 s
   deadline *after* the player pods start, and a short episode can already be gone).

**The two named edits to `replays.nim`:**

1. **`serializeReplaySim`/`deserializeReplaySim` cover the new sim fields** — every skimmer's `pos`,
   `v`, `stun`, `nibbleArmed` row; every particle's `state`, `pos`, `dir`, `speed`, `timer`; `captures`,
   `nibbles`, `poisonHits`, `assists[]`, `poisonBySeat[]`, `nibblesBySeat[]`, `thrustTicks[]`,
   `thrustMicro`, `scoreMicro`, `rngDraws`, the RNG state, `phase`, `targetTick` — because keyframes are
   how the viewer seeks. The static geometry and `perm` are **excluded** from keyframes (they are
   already in the config JSON — ctf's own rule for static bakes).
2. **`CtfReplayMagic "COWLDCTF"` → `WaterworldReplayMagic "COWLDWWD"`**,
   `GameName* = "walker-waterworld"`, `GameVersion* = "1"`, with ctf's prepend-only changelog-comment
   discipline (`GV1 (tank rules): four skimmers, 2-of-4 plankton capture, poison, 16 sensors`) and
   `tools/ci/check_gameversion.sh` kept as is.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`; `tools/wasm_replay_smoke.cjs`). So:

- Every stored sim field is explicitly `int32` (positions, velocities, radii, counters), `int64` (the
  score accumulators), `uint8` (direction indices, command bytes) or `bool`/`enum`. **No bare `int` in
  a hashed field.**
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with an
  explicit truncating `div` (Nim's `div` truncates toward zero, so drag, reflection and lead arithmetic
  are all symmetric under negation).
- **No floating point anywhere under `src/waterworld/{sim,tank,trig,sensors,sim_types,sim_config,
  sim_state}.nim`.** No `sin`, `cos`, `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`.
  Grep-enforced in CI. Floats stay legal in `control.nim`, `global.nim` and the pixie bakes, because
  neither the controller (recorded, not re-run) nor rendering enters `gameHash` — exactly ctf's split.
- Trigonometry is the committed `DirQ12` table (32 entries) plus `isqrt`. Nothing else.
- Randomness: one seeded stream, every draw through `drawInt` on `rng.next()`'s `uint64` domain,
  `rngDraws` hashed.

### How the replay achieves server ↔ viewer determinism

The mechanism is ctf's, unchanged:

1. The server writes a `COWLDWWD` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `perm`, every geometry and physics constant, the seeded initial
   particle table, the roster with real names), then the record stream — joins, leaves, **per-tick
   command-byte change records**, chat records (`register`, `intent`, `fallback`, `budget_guard`,
   `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/waterworld_replay.nim` — which imports the
   **same** `src/waterworld/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + `nimby 2.2.4`
   container in `Dockerfile.replay-viewer`.
3. In the browser, `waterworld_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `waterworld_frame` re-steps the sim from the **recorded command bytes** and compares
   `sim.gameHash()` against the recorded hash **every tick** (`checkReplayHash`). One divergent bit is
   caught at the tick it happens, surfaced as `mismatchTick` in the chrome (`#mmwarn`) and, in CI, as a
   hard failure.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle and
   runs `tools/ci/viewer_smoke.mjs` against the replay `docker-smoke` produced (§Tests), which fails if
   the viewer errors, never draws, freezes, or reports a mismatch tick.

Perf target: 1728 ticks of physics + 6 912 controller evaluations + 6 912 sensor frames in under 5 s on
a CI runner; `tests/test_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

`src/waterworld/server.nim` is ctf's `server.nim` with the five edits above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`) — **both `/client/` routes serve real
pages, registered before any catch-all asset route, and neither opens the player socket** (lantern
0.1.1: the certifier probes them before starting player pods). Same `COGAME_*` runtime contract
(`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`,
`COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`, `COGAME_HOST`/`COGAME_PORT`), same
403 on a bad slot/token, same done-before-artifact-writes ordering, same entrypoint shape
(`src/walker_waterworld.nim`, where seed randomisation happens **before** `config.update` so every
seed-derived draw follows the final seed).

### The player container

`src/walker_waterworld_player.nim` (built to `/bin/walker-waterworld-player`) is
`src/paintball_player.nim` with the baseline names changed. It reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED`, `PLAYER_POLICY_LABEL`, dials with the starter's bounded retry
(240 × 500 ms), and sends **one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"shoal"|"drifter"|null,"policy":"<free label>"}
```

It re-sends the registration on the starter's `RegistrationResends`/`ResendEveryFrames` schedule (the
server's held-registration table, `src/ctf/server.nim:1730`, is kept — a seat's first registration can
arrive before its player index exists, and dropping it was a real paintball scar). It then sends the
Sprite v1 Ready packet (`0x85`) after each received frame and otherwise only receives. **The receive
loop is wrapped in `try/except CatchableError` and exits 0 on a dead socket** — whisky's
`receiveMessage` raises on a close frame and mummy's `send` only queues, so the game's `quit(0)` can
outrun the flushed `done` frame (raid 0.1.3 → 0.1.4). A seat that never registers, or registers with
neither field, is `scripted: "shoal"`.

Player container resources in the manifest: `requests {cpu: 100m, memory: 64Mi}`,
`limits {cpu: "1"}` — the bundled-player `limits.cpu` minimum is `"1"` and anything lower is a 400 at
upload (pistonball 0.1.1, 2026-08-26).

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates` and **filtered by the same predicate the sensor frame
uses**: the frame carries the tank, the rock, its own skimmer with its sixteen rays, the other three
skimmers (transponder), and **plankton/poison only while their centres are within 2.40 m of this
skimmer's centre**. Everything else is dark. Board labels carry only `SKIM-n`; `showPlayerLabels` is
forced false on the player stream.

### The per-seat view given to the LLM

Numbers rounded to 2 decimals, in **view coordinates** (metres, origin bottom-left, y up) and degrees
counter-clockwise from east. This object is the tail of the LLM user message; the scripted baselines
are pure functions of the identical object.

```json
{"turn": 9, "of": 24,
 "clock": {"tick": 648, "of": 1728, "left_s": 45.0},
 "you": {"alias": "SKIM-3", "skimmer": 2, "pos": [4.18, 5.02], "vel": [1.44, -0.62],
         "speed_m_s": 1.57, "stun_ticks": 0,
         "max_speed_m_s": 3.24, "radius_m": 0.24, "sensor_range_m": 2.40},
 "tank": {"w": 12.0, "h": 8.0, "rock": {"c": [6.0, 4.0], "r": 0.9}},
 "sensors": [{"n": 0, "deg": 0.0, "k": "clear", "d": null, "closing": null},
             {"n": 1, "deg": 22.5, "k": "food", "d": 1.62, "closing": 0.41},
             {"n": 2, "deg": 45.0, "k": "rock", "d": 2.05, "closing": 0.0},
             "… 16 entries, n ascending …"],
 "food_detected": [{"id": "F2", "deg": 24.1, "d": 1.62, "pos": [5.66, 5.68],
                    "vel": [-0.51, 0.36], "closing": 0.41}],
 "poison_detected": [{"id": "P5", "deg": 291.0, "d": 2.05, "pos": [4.92, 3.11],
                      "vel": [0.88, 0.62], "closing": -0.22}],
 "partners": [{"alias": "SKIM-1", "deg": 202.0, "d": 3.41, "pos": [1.02, 3.74],
               "vel": [0.90, 0.31], "stun_ticks": 0, "in_sensors": false},
              {"alias": "SKIM-2", "deg": 12.0, "d": 2.10, "pos": [6.24, 5.46],
               "vel": [-1.10, 0.05], "stun_ticks": 0, "in_sensors": true},
              {"alias": "SKIM-4", "deg": 318.0, "d": 6.05, "pos": [8.60, 1.20],
               "vel": [0.20, 0.80], "stun_ticks": 6, "in_sensors": false}],
 "pod": {"score": 61.35, "captures": 6, "target": 20, "nibbles": 14,
         "poison_hits": 2, "thrust_cost": 2.65},
 "rules": {"coop_needed": 2, "capture_points": 10.0, "nibble_points": 0.05,
           "poison_points": -2.0,
           "note": "two skimmers on one plankton AT THE SAME TICK is the only way to catch it"},
 "your_last_intent": {"mode": "escort", "partner": "SKIM-2", "target": "none",
                      "waypoint": [9.0, 6.0], "lead_ticks": 6, "standoff_m": 1.2,
                      "throttle": 1.0}}
```

`food_detected` and `poison_detected` are `[]` whenever nothing is inside 2.40 m — the common case
early in an episode. `partners` always has exactly three entries. `sensors` always has exactly sixteen.

**Hidden from every seat, with no exception:**

- Any plankton or poison particle whose centre is farther than **2.40 m** from this skimmer — its
  existence, id, position, velocity and even its count. `food_detected` never carries a total.
- Which entrant holds any other seat; any other seat's intent, `note`, `say`, prompt, latency,
  policy label, `policyKind` or fallback state.
- `perm`, `config.seed`, the initial particle table, the respawn queue, the RNG state, and the variant
  name.
- Real player names anywhere (board labels carry only `SKIM-n`; `showPlayerLabels` is forced false on
  the player stream).
- Future ticks, and any per-seat score decomposition (the score is shared, so `pod` is legitimately
  global; there is no per-seat credit assignment in the observation).

`tests/test_locality.nim` asserts all of it against the composed LLM user message over randomised
states (§Tests 8).

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "F2 is drifting into SKIM-2's lane; I take it, it will arrive",
 "mode": "hunt", "target": "F2", "partner": "SKIM-2",
 "waypoint": [9.0, 6.0], "lead_ticks": 8, "standoff_m": 1.2, "throttle": 1.0,
 "say": "on F2 with two"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `mode` | string | closed enum `hunt, escort, sweep, hold, avoid` | unrecognised / missing → last turn's `mode`, else `sweep` |
| `target` | string | **≤ 4 runes**, `F1`…`F5` or `none`, case-insensitive | an id outside the set, or an id not currently detected → treated as `none` (the controller then takes the nearest detected plankton) |
| `partner` | string | **≤ 8 runes**, `SKIM-1`…`SKIM-4` or `none`; must not be my own alias | unrecognised, missing, or self → `none` (the controller then takes the nearest other skimmer) |
| `waypoint` | array[2] number | finite, clamped to `x ∈ [0.30, 11.70]`, `y ∈ [0.30, 7.70]`, quantised to µm | non-finite / wrong shape / missing → last turn's waypoint, else the tank centre offset `(0, 1.60)` |
| `lead_ticks` | integer | finite, clamped `[0, 24]`, rounded | non-finite / missing → `6` |
| `standoff_m` | number | finite, clamped `[0.0, 2.5]`, quantised to mm | non-finite / missing → `1.2` |
| `throttle` | number | finite, clamped `[0.0, 1.0]`, quantised to `0..255` | non-finite / missing → `1.0` |
| `say` | string | **≤ 48 runes** | truncated to 48 runes, then ctf's printable-ASCII shout sanitiser (which also strips a leading `{`, since the replay chat stream distinguishes control records by it) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**
(`MaxPolicyLabelRunes`), any recorded error text (`fallback.detail`) **≤ 200 runes**
(`MaxFallbackDetailRunes`), and the whole serialized `intent` record **≤ 600 runes**, asserted in
`tests/test_replay.nim`. `register.prompt` is capped at **≤ 4000 runes** at the transport (over-long is
truncated, never rejected) and is **never** written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — in Nim, `runeLen` /
`runeSubStr` (ctf's `directives.nim` rune discipline, kept verbatim as `intents.nim`). Slicing a
`string` by byte index on any path to the replay is forbidden: a byte-truncated multi-byte character
renders in a browser and then fails a strict UTF-8 parser. §Tests 6 pins it with a 4-byte emoji sitting
on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model prefixed
prose (`extractJsonObject`); accept numeric strings; accept integer percentages for `throttle` and
divide by 100 when the value exceeds 1; accept centimetres for `standoff_m` and the waypoint when a
value exceeds 30 and divide by 100; accept `mode`, `target` and `partner` case-insensitively and with
surrounding whitespace; accept `waypoint` as `{"x":…,"y":…}` as well as `[x, y]`; accept `target` given
as `"plankton F2"` or `"2"`. Only when no object with at least one usable field can be recovered do the
retry and then the fallback fire.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, waterworld keys) to `COGAME_RESULTS_URI`. It must
equal the manifest's `results_schema` key-for-key — that schema is `additionalProperties: false` and the
certifier rejects any unknown field. Adding or removing a key here means editing
`coworld_manifest_template.json` in the same commit. **22 keys:**

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "Baseline (2)"],
 "aliases": ["SKIM-3", "SKIM-1", "SKIM-4", "SKIM-2"],
 "skimmers": [2, 0, 3, 1],
 "policyKinds": ["llm", "llm", "scripted", "scripted"],
 "scores": [119.15, 119.15, 119.15, 119.15],
 "win": [false, false, false, false],
 "sharedScore": 119.15,
 "captures": 13,
 "captureTarget": 20,
 "nibbles": 31,
 "poisonHits": 3,
 "thrustCost": 6.4,
 "assists": [9, 8, 5, 4],
 "nibblesBySeat": [9, 7, 8, 7],
 "poisonBySeat": [1, 0, 1, 1],
 "thrustMeanPct": [72, 68, 55, 90],
 "llmTurns": [24, 23, 0, 0],
 "fallbackTurns": [0, 1, 0, 0],
 "finalTick": 1728,
 "reason": "complete",
 "endRule": "full_time",
 "seed": 8821477}
```

`names` are the **real policy names** (spectator side). `aliases` are the in-game names. Every per-seat
array is in **seat order** and has exactly 4 entries. `scores` holds four copies of one number.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDWWD`** format: the static wasm viewer parses exactly this
format, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and the whole seek/keyframe machinery. Consequences handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design ("set 0 for a binary replay format").
- The repo keeps **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): given a
  `.replay` path it prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"walker-waterworld/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "skimmers":[…],"policyKinds":[…],"tickCount":…,"intents":[…],"fallbacks":N,"results":{…}}`. It
  brace-matches the config JSON from the first `{` (the technique ctf's `AGENTS.md` documents for prod
  forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule, .results.captures' /tmp/ep.json
  jq -r '[.intents[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "walker-waterworld/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.captures > 0`, and the champion seats' intents
  `source == "llm"` with varying `mode`/`target` values — not all fallbacks, and not a constant intent.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDWWD`, format version, `gameName` `walker-waterworld`, `gameVersion` `1` |
| config JSON | `seed`, `perm`, `num_agents`, `maxTicks`, `turnTicks`, the whole geometry table (tank box, rock, radii, sensor range/count, spawn points), every physics constant (thrust, drag, clamps, restitution, particle speed sets, respawn/stun ticks), the reward constants and `captureTarget`, the **seeded initial particle table** (5 + 8 rows of position/direction/speed), `players[].name` (**real names**), `slots[].alias`, `fastMode` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| inputs | **the action log**: one command byte per seat per tick, written on change only |
| chats | `register` / `intent` / `fallback` / `budget_guard` / `result` records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 1728 hashes (8 B) + ≤ 6 912 input-change records (≈ 4 B) + 96 intent records (≈ 260 B) + a ≈ 6 KB
config ≈ **70 KB** worst case, typically under 45 KB.

### Record and event vocabulary

**A. Replay chat records** (written by the server; re-applied at playback in order):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `skimmer`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `intent` | `turn`, `seat`, `alias`, `skimmer`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `mode`, `target`, `partner`, `waypoint`, `lead_ticks`, `standoff_m`, `throttle`, `say` |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at game over (ctf's `resultRecord`, kept — it is what makes the bytes self-sufficient) |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these from
state deltas during playback, so they cost no replay bytes and are identical live and in replay:
`phase`, `capture` (`{food, skimmers: [...], score}`), `nibble` (`{food, skimmer}`), `poison`
(`{poison, skimmer}`), `spawn` (`{kind, id}`), `stun_end` (`{skimmer}`), `near_miss` (two skimmers both
within 1.00 m of one plankton in the same tick without capturing it — the drama the game is made of),
`turn_end`, `target_met`, `gameover`, `say` (an `intent` record's non-empty `say`).
**Beats** (scrubber markers): `capture`, `poison`, `target_met`, `gameover`. `nibble`, `spawn`,
`near_miss` and `stun_end` are **not** beats — they fire dozens of times and would bury the scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Capture, Nibble, PoisonHit, Spawn, NearMiss, Intent, PhaseChange,
TargetMet`, and the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's
script, kept (with `image_tag` and the `docker cp` source path
`/workspace/waterworld/replay-viewer/dist/.` changed, and the ecos `mkdir -p` already present at line
22). `coworld build` invokes it with the absolute bundle directory; the script already refuses any
output path that is not a `static-replay-viewer` directory inside the repo, and it must stay committed
**executable** (`coworld build` hard-requires `os.X_OK`).

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter.** Splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently with every file present and 200
(cogame-lantern, 2026-08-23), so there is no mixture anywhere in this table:

| File | Source |
|---|---|
| `replay-viewer/config.nims` | **`coworld-ctf`**'s `replay-viewer/config.nims`, verbatim except `ctf_replay.js` → `waterworld_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_waterworld_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the flags stay exactly as ctf links them, including `-s ENVIRONMENT=web,worker,node`, `-s ABORTING_MALLOC=1`, `--preload-file data@data`, `--define:useMalloc`. |
| the wasm entry `.nim` | **`coworld-ctf`**'s `replay-viewer/ctf_replay.nim`, forked to `replay-viewer/waterworld_replay.nim` (stage-note buffer, `ABORTING_MALLOC` diagnostics, the `predictedViewerRenderBytes`/`WasmViewerBudgetBytes` capacity preflight, `emscripten_exit_with_live_runtime` lifetime — all kept), exporting `waterworld_load_replay`, `waterworld_frame`, `waterworld_input`, `waterworld_packet_ptr/len`, `waterworld_mismatch_tick`, `waterworld_error_ptr/len`, `waterworld_stage_ptr/len`. |
| `static_replay*.js` | **`coworld-ctf`**'s `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts('./wire_constants.js', './broadcast_core.js', './waterworld_replay.js')` form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Only two names change: the Worker name `ctf-static-replay` → `waterworld-static-replay`, and `window.CtfStaticReplay` → `window.WaterworldStaticReplay`. |
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
  CTF-specific paths (perks, handicaps, lives, flag story) stay in the file and are inert because the
  corresponding state fields are simply absent from waterworld's stream. Every waterworld-specific
  readout lives in the appended game block, and the state JSON **keeps ctf's key names**
  (`t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events, lead, beats,
  lulls, over, hold` — `src/ctf/broadcast.nim:861-975`) so chrome_common's plate rendering, feed rows,
  beat markers, momentum curve, spoilers switch and endcard run unmodified against waterworld values. A
  from-scratch page that reuses the starter's ids is explicitly **not** what happens here
  (cogame-gridlock, 2026-08-23). A test pins the file's sha256 against the starter's copy.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one `<style>`
  and one `<script>` block at the end of the file, injecting waterworld's readouts into the existing
  containers. Nothing above them is rewritten; the CSS variables, `relayout()`
  (`client/replay_broadcast.html:4276`), the transport, the endcard, the locker-room loader and the
  `?embed=1` mode are the starter's. The game block's own function names are prefixed `ww`
  (`wwMarkBeat`, `wwPushFeed`, …) so nothing shadows chrome_common's hoisted alias block
  (`var markBeat = C.markBeat` — the tandem 2026-08-23 scar), and a test asserts no game-block top-level
  name collides with the alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and its
  children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; and `#povBadge`.
  **Zoom decision: the tank is fixed and the board (1200 × 800 px) always fits the frame, so
  `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the rule that it exists only for
  boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap code stays in the file, verbatim,
  simply never driven.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned "Four
  skimmers, one tank, nothing catches alone", art from `client/art/lockerroom/bg.jpg`), `#chrome`,
  `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#mmwarn`,
  `#bannerlane`, `#killfeed`, `#transport` with every button (`#btn-play`, `#btn-back`, `#btn-fwd`,
  `#btn-end`, `#btn-restart`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`), `#speedchips`, `#scrub`,
  `#scrub-fill`, `#scrub-head`, `#scrub-win`, `#momentum`, `#lulls`, `#tick-clock`, `#ffwd-chip`,
  `#ffwd-mini`, `#win-chip`, `#endcard` with `#ec-headline`, `#ec-how`, `#ec-wincond`, `#ec-teams`,
  `#ec-replay`, and `#status`.

### The exact state JSON the viewer reads

`buildStateJson` (ctf's, retargeted) emits this object once per frame. Keys above the fold are ctf's and
are consumed by the byte-identical `chrome_common.js`; everything waterworld-specific is under `ww` and
`intents`, consumed only by the appended game block.

```json
{"t": 648, "mt": 1728, "ph": "playing", "lob": 0, "pl": true, "sp": 1, "mx": 1728,
 "st": 0, "lp": false, "sk": false, "ff": false, "en": true, "mm": -1, "bs": 2, "pov": -1,
 "teams": {"pod": {"score": 61.35, "captures": 6, "target": 20, "nibbles": 14,
                   "poison": 2, "thrust": 2.65, "policies": 4}},
 "roster": [{"s": 0, "name": "daveey", "team": "pod", "alias": "SKIM-3", "skimmer": 2,
             "kind": "llm", "assists": 4, "poison": 1, "thrustPct": 72}, "… 4 rows, seat order …"],
 "events": [{"k": "capture", "t": 641, "food": "F2", "skimmers": [2, 1], "score": 61.35}, "…"],
 "turn": 9, "turns": 24, "turnTicks": 72,
 "ww": {"tank": {"w": 12.0, "h": 8.0, "rock": {"c": [6.0, 4.0], "r": 0.9},
                 "sensorRange": 2.4, "sensors": 16, "coop": 2},
        "skimmers": [{"i": 0, "p": [1.02, 3.74], "v": [0.90, 0.31], "dir": 3, "level": 6,
                      "stun": 0, "mode": "escort", "partner": 1, "target": null,
                      "rays": [{"k": "clear", "d": 2.4}, {"k": "food", "d": 1.62}, "… 16 …"]},
                     "… 4, skimmer order …"],
        "food": [{"id": "F2", "p": [5.66, 5.68], "v": [-0.51, 0.36], "state": "live",
                  "held": [2]}, "… 5, id order …"],
        "poison": [{"id": "P5", "p": [4.92, 3.11], "v": [0.88, 0.62], "state": "live"},
                   "… 8, id order …"],
        "reward": {"captures": 60.0, "nibbles": 0.7, "poison": -4.0, "thrust": -2.65,
                   "score": 61.35},
        "bubbles": [{"skimmer": 2, "say": "on F2 with two", "until": 700}]},
 "intents": [{"turn": 9, "seat": 0, "alias": "SKIM-3", "skimmer": 2, "source": "llm",
              "mode": "hunt", "target": "F2", "partner": "SKIM-2", "note": "…",
              "say": "on F2 with two"}, "… 4 …"],
 "lead": {"teams": ["pod"], "pts": [[0, 0], [96, 10], "… change-points of score …"]},
 "beats": [{"t": 216, "k": "capture"}, {"t": 402, "k": "poison"}, "…"],
 "lulls": [[480, 601]],
 "over": {"winner": "pod", "draw": false, "timeLimit": true, "endRule": "full_time",
          "reason": "complete", "score": 119.15, "ticks": 1728,
          "teams": {"pod": {"captures": 13}}},
 "hold": 3}
```

There is exactly **one** `teams` key (`pod`) — this is a cooperative game with one side — so
chrome_common's plate loop renders one team plate; `#plates-r` is used by the game block for the
objective plate instead. `roster` carries the **real policy names** and is spectator-side only.

### Readouts

1. **Run bug** (top, always on). `#plates-l`: the one team plate — "THE POD · 4 skimmers" with the live
   **shared score** as its headline number (green above 0, red below). `#plates-r`: the objective plate
   — **`CAUGHT 6 / 20`** with a segmented progress bar, plus two small counters (`poison 2`,
   `thrust −2.65`). Centre column (`#clock`): `M:SS` from `tick div 24` with `of 1:12` in
   `#clock-caption`.
2. **The board** (the headline): a top-down tank — dark rippled water baked from `data/arena_floor.png`
   and `client/art/walls/wall_h.jpg`, the rock as a lit boulder with a soft shadow, four skimmers as
   baked drone hulls with a **thruster plume whose length and direction read the command byte** (that
   is what makes continuous control visible), plankton as pale-green glowing discs with a slow pulse,
   poison as dark magenta spiked discs.
3. **Sensor rays — the idea's explicit replay plan, and a first-class readout.** All **sixteen rays per
   skimmer** are drawn every frame as short 2.40 m spokes: dim slate when `clear`, **green** on `food`,
   **magenta** on `poison`, **white** on `cog`, **grey** on `rock`/`wall`; a ray's length is the hit
   distance, so the spoke set reads as a live outline of what that skimmer can feel. Under `.tiny`
   (≤ 620 px board) only the hit rays are drawn, at half opacity, so the 360 px frame stays legible.
   A legend chip in `#bannerlane` names the four colours once, for the first 5 s of playback.
4. **Rendezvous lines and capture rings**: a thin dashed line from a skimmer to its `escort` partner
   (from `intents`), a **pulsing double ring** on a plankton the instant two skimmers hold it, with a
   `+10` popping off it; a single thin ring for a lone holder (the nibble) so a spectator sees "one is
   not enough" without being told.
5. **Poison hit FX**: a magenta flash, a short screen shake, the stunned skimmer greys out for its 12
   ticks with a countdown pip, and a `−2` pops.
6. **Speech bubbles**: at most **three** at a time — the three skimmers nearest the pod's centroid that
   emitted a non-empty `say` this turn — drawn for 2.5 s in a **reserved band at the top of the tank**
   (`Y ∈ [7.10, 7.85] m`), never positioned relative to a skimmer. The band is sized from
   `MaxSayRunes = 48` measured in `data/font.ttf` at the current `--hudscale`, which is exactly the
   reservation the cogchemists 2026-08-24 scar demands; `viewer_smoke.mjs --strict-text-bounds` requires
   `canvas_text.never_inside == 0` for this fixed tank.
7. **Match feed** (`#killfeed`, renamed in copy only): plain language — "SKIM-3 + SKIM-2 take plankton
   F2 — +10", "SKIM-1 alone on F4 — waiting", "SKIM-4 hits poison P7 — −2, stunned", "SO CLOSE — F1
   slipped between SKIM-1 and SKIM-3", "TURN 10 — 4 new orders". Intent `note`/`say` strings appear
   here; this is where a spectator sees the LLM playing.
8. **Momentum graph** (`#momentum`): ctf's `lead` series repurposed to the **score curve** — the pod's
   cumulative score over the whole timeline, drawn from the first frame, with captures marked.
9. **Transport and integrity**: ctf's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls,
   spoilers, speeds `[1,2,3,4,8,16]`, scrubber with beat markers, tick readout, the end-hold countdown
   and `#mmwarn` — all verbatim.
10. **Endcard**: "13 CAUGHT · score 119.15" (or "TARGET MET in 58.2 s · score 192.20"), and
    chrome_common's `ec-*` table listing all four seats by **real policy name** with their skimmer
    number, assists, nibbles, poison hits, mean thrust % and LLM/fallback turn counts, sorted by
    assists.

### Transport rules

- `relayout()` is kept verbatim (`client/replay_broadcast.html:4276-4320`): it sets `--hudscale`,
  `--topband` and **`--band`** on `:root` by fixed-point iteration, so the board is letterboxed between
  the scorebug band and the transport band.
- **No overlay sits in the transport band.** Every waterworld overlay the game block adds — the
  objective plate, the ray legend, the score curve caption — is positioned inside `#chrome` with
  `bottom: calc(var(--band) + N * var(--u))`, never over it.
- The **endcard stops at `var(--band)`** (the starter's `#endcard { bottom: var(--band) }` rule at line
  1047 is kept) and is **dismissed by every seek** (the starter's behaviour, kept).
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">`** elements — the game
  block upgrades chrome_common's markers to buttons with `aria-label` and `title` (e.g. "Catch — 26.7 s
  — SKIM-3 + SKIM-2") and a click seeks to that tick. **CSS exists for every kind emitted**:
  `.beat-marker.capture`, `.beat-marker.poison`, `.beat-marker.target_met`, `.beat-marker.over` — one
  rule per kind, asserted by `tests/test_viewer.nim`.

### Art

Real, and mostly baked from what the repo already ships. The water, caustics, tank rim, rock, skimmer
hulls, thruster plumes, plankton and poison discs and the vignette are baked once at startup with
**pixie** (already a dependency, already how ctf bakes its board), using ctf's shipped
`data/arena_floor.png` and `client/art/walls/wall_h.jpg`/`wall_v.jpg` as the water/rim plate sources and
`data/font.ttf` for every label. The locker-room card reuses `client/art/lockerroom/bg.jpg`. No
solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`; kept verbatim.
At that width the scorebug shows the score, `CAUGHT n / 20`, and the clock; the four policy names live
in the endcard and in each roster row's `title`. Two further rules ship in the game block:
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (so the
team/objective plate captions never collapse to "…") and, under `.tiny`, the ray legend, the thrust
counter and the bubble text are hidden while the hit rays and the capture rings stay. The board aspect
is 1200:800, which the chrome derives from the stream. `tests/test_viewer.nim` asserts both rules are
present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-walker-waterworld`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `walker-waterworld`; `game.name` is also
  `walker-waterworld`, so the secret namespace
  `secret://coworld/walker-waterworld/anthropic_api_key` matches `game.name` **exactly**
  (cooperative-hunting, 2026-08-25: the namespace must equal `game.name`, not a differently-punctuated
  slug).
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{WALKER_WATERWORLD_IMAGE}}` (placeholders are derived from **compose service names** by uppercasing
  and replacing `-` with `_`; `{{GAME_IMAGE}}` is not a thing outside ctf's own two-service file —
  lantern 0.1.0). Phase 20's manifest generator derives it from `compose.yaml` and
  `tests/test_manifest.nim` asserts the derivation:

  ```yaml
  services:
    walker-waterworld:
      image: coworld-walker-waterworld:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure (nimby 0.1.26,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's
  package tree), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:walker-waterworld
  src/walker_waterworld.nim` → `/bin/walker-waterworld`, and the same for
  `src/walker_waterworld_player.nim` → `/bin/walker-waterworld-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/walker-waterworld"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby with its
  sha256 check, the marker splices, the `test -f`/`grep -q` assertion block) with the asset list swapped
  and the workspace path `/workspace/waterworld`.
- **`coworld_manifest_template.json`** (written against the `coworld` 0.1.42 upload contract — validate
  offline with the CLI's `validate_upload_manifest` and `_load_template_manifest` before dispatching):
  - top-level `$schema`, `episode_timeout_minutes: 20`, and top-level `tags` ≥ 3:
    `["physics","cooperative","continuous-control","partial-observation","llm"]`. **`game.tags` does not
    exist** — the validator forbids it and requires `game.description` (pistonball 0.1.0, 2026-08-26).
  - `game.name` `walker-waterworld`; `game.description` (one sentence: "Four thruster skimmers feel for
    drifting plankton with 2.40 m sensors; nothing is caught unless two of them touch it at the same
    instant."); `game.owner`; `game.runnable`
    `{"type":"game","image":"{{WALKER_WATERWORLD_IMAGE}}","run":["/bin/walker-waterworld"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/walker-waterworld/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-walker-waterworld/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}` (nested under `game`, not top-level;
    no top-level `version`, no `game.display_name`).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`; **every array property carries `minItems`/`maxItems`** (tandem 0.1.0 scar):
    `tokens` (1..4), `players` (1..4), `slots` (0..4), plus `closedRoster`, `seed`, **`num_agents`**
    (1..4), `minPlayers`, `maxTicks` (default 1728), `maxGames` (default 1), `turnTicks` (default 72),
    `turnBudgetMs` (default 16000), `attempt1Ms` (default 9000), `retryMs` (default 5000),
    `turnSpacingMs` (default 12000), `wallClockBudgetSeconds` (default 660), `lobbyJoinTimeoutTicks`
    (default 1728), `startWaitTicks`, `gameOverTicks`, `fastMode` (default true), `showPlayerLabels`,
    `model`, `maxOutputTokens` (default 900), `captureTarget` (default 20), `foodCount` (default 5),
    `poisonCount` (default 8), `sensorRangeUm` (default 2400000), `coopNeeded` (default 2),
    `stunTicks` (default 12), `respawnTicks` (default 24). The CLI validates every variant and the cert
    fixture against this schema (injecting `tokens`), so every key either appears here or is not
    settable — and `tests/test_manifest.nim` asserts it covers every field `sim_config.update` reads.
  - `game.results_schema`: exactly the 22 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","reason","endRule","sharedScore","captures"]`, `reason` enum
    `["complete","deadline","fault"]`, `endRule` enum
    `["target_met","full_time","wall_clock","sim_fault","host_error"]`, and every per-seat array
    `minItems: 4, maxItems: 4`.
  - `game.protocols`: **both `player` and `global`**, each `{"type":"text","value":"…"}` (objects, not
    bare strings — garble v0.1.0). `player` documents the registration chat frame, the sensor-filtered
    per-tick Sprite v1 frames, the fact that seats send **no** inputs, the sensor-frame JSON and the
    intent reply schema with its caps. `global` documents the `/global` spectator snapshot, the state
    JSON above, the `COWLDWWD` replay layout (config JSON, command-byte log, chat records, hash chain)
    and the static replay bundle.
  - `game.docs`: `readme` = `{"type":"text","value":"<the README body inlined>"}` and `pages` = three
    entries — `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined: every number in §The game>"}}`, `{"id":"protocol.md","title":"Wire protocol",…}`,
    `{"id":"orders.md","title":"Writing a skimmer order",…}`. A manifest test asserts all four values
    are non-empty text.
  - `player[0]` (the only top-level bundled player entry, with id/type/name/description) =
    `{"id":"baseline","type":"player","name":"Waterworld Shoal Baseline",
    "description":"Pair-and-hunt scripted skimmer: keep your partner close, take plankton together, back
    off poison. No LLM.","image":"{{WALKER_WATERWORLD_IMAGE}}","run":["/bin/walker-waterworld-player"],
    "env":{"PLAYER_SCRIPTED":"shoal"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}`. It occupies **all
    four** certification slots — every declared player entry must occupy at least one slot or cert fails
    `players_missing` (raid 0.1.2 → 0.1.3), and `limits.cpu` below `"1"` is a 400 at upload
    (pistonball 0.1.1).
  - **Variants — `num_agents` is 4 in both, and `description` is required on each:**

    | id | name | description | **`num_agents`** | `players`/`slots` | `minPlayers` | `maxTicks` | turns | `turnTicks` | `turnSpacingMs` | `turnBudgetMs` | `captureTarget` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|---|---|
    | `default` | The Tank (4 skimmers, 72 s) | Four skimmers, five plankton, eight poison blooms, 24 order turns. | **4** | 4 | 4 | 1728 | 24 | 72 | 12000 | 16000 | 20 | 660 |
    | `sprint` | Sprint (4 skimmers, 48 s) | Same tank, 16 order turns, for cheap ladder rounds. | **4** | 4 | 4 | 1152 | 16 | 72 | 12000 | 16000 | 14 | 480 |

    Both seat four players, `slots: [{"alias":"SKIM-1"}, …, {"alias":"SKIM-4"}]`, `fastMode: true`,
    `maxGames: 1`. `sprint` changes only run length and the target, **never** the seat count. `sprint`'s
    budget: 15 × 12 s + 16 s + 15 s lobby + 20 s write ≈ 231 s, inside 480 s.
  - **Certification fixture — `num_agents` is 4 here too:** `certification.players` = four
    `{"player_id":"baseline"}` entries; `certification.game_config` =
    `{"players":[{"name":"SKIM-1"}, …4…], "slots":[{"alias":"SKIM-1"}, …4…], "num_agents": 4,
    "minPlayers": 4, "seed": 8821477, "maxTicks": 720, "maxGames": 1, "turnTicks": 72,
    "turnBudgetMs": 16000, "turnSpacingMs": 0, "wallClockBudgetSeconds": 180,
    "lobbyJoinTimeoutTicks": 720, "captureTarget": 20, "fastMode": true}` — 10 turns, every seat
    scripted, no LLM client (no credentials offline, so the client disables itself and every turn falls
    back instantly). Wall cost ≈ 10 s connect + ~1 s of physics + the ~20 s shutdown grace ≈ 35 s. At
    720 ticks the fixture replay is **30.0 s of playback**, comfortably longer than the viewer smoke's
    12 s soak (ecos, 2026-08-23: a replay shorter than the soak reads as "frozen"). Because 35 s is
    close to `coworld certify`'s 60 s default, the release workflow's certify step passes
    **`--timeout-seconds 300`** (cooperative-hunting 0.1.2 → 0.1.3); the fixture is **not** shrunk.
    `captureTarget` stays 20 so the fixture cannot end early and the replay length is deterministic.
- **Scaffold from `templates/`** with `<slug>` = `walker-waterworld`, `<IMAGE>` =
  `coworld-walker-waterworld`, `<SEATS>` = **4**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`, `tools/ci/docker_smoke.sh`
  (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim, no substitutions),
  `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh` (**`chmod +x`**). Two additions to
  the template `ci.yml`: the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay
  format), and the `wasm-viewer` job gets the extra `renderer_fixture.html` step of §Tests. The
  `NIM_TESTS_RELEASE_ONLY` repo variable lists `tests/test_perf.nim` and `tests/test_baselines.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/walker-waterworld-player"`, one image,
  env-switched; each also sets `PLAYER_POLICY_LABEL`):

  | name | env | role |
  |---|---|---|
  | `walker-waterworld-tandemhunt` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `walker-waterworld-relay` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `walker-waterworld-shoal` | `PLAYER_SCRIPTED` = `shoal` | filler |
  | `walker-waterworld-drifter` | `PLAYER_SCRIPTED` = `drifter` | filler |

  A four-seat episode is filled by the platform with the two champions plus fillers — which is what
  makes the cross-play mean meaningful.
- **Repo layout**: `src/walker_waterworld.nim`, `src/walker_waterworld_player.nim`,
  `src/waterworld/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, tank.nim, sensors.nim,
  control.nim, intents.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim, replays.nim,
  replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, wire_constants.nim,
  server.nim}`, `replay-viewer/{waterworld_replay.nim, config.nims, static_replay.js,
  static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, ORDERS.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `walker_waterworld.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only harness;
the sandbox has no Nim, Docker, emsdk or browser. The **determinism gate** (test 2 plus the viewer
smoke) is inviolable: if it fails, the physics or a build flag changed — fix the code, never the test.

1. **`tests/test_physics.nim`** — sim unit tests: a skimmer at rest given `level 7` for 24 ticks reaches
   `2.6 … 3.3 m/s` and never exceeds `MaxSkimmerSpeed`; a coasting skimmer's speed decays by
   `3.5 … 4.2 %` per tick and reaches under 1 % of its initial speed within 120 ticks; a skimmer driven
   into a wall at full speed rebounds at `35 … 45 %` of its normal speed and its centre never leaves
   `[SkimmerRadius, ArenaW − SkimmerRadius] × [SkimmerRadius, ArenaH − SkimmerRadius]`; a skimmer driven
   into the rock ends exactly `RockRadius + SkimmerRadius` from `RockCentre`; a particle's speed is
   **exactly constant** over 5 000 ticks including 40+ bounces (the index-reflection property, asserted
   bit-exactly); a particle never ends inside the rock or outside the tank; the three index reflection
   rules are checked against a float reference to within one index; **the no-tunnelling bound is
   asserted directly** — `MaxSkimmerSpeed + max(PoisonSpeedSet) < SkimmerRadius + PoisonRadius`, so no
   legal closing speed can cross a contact window in one tick — and over 50 000 randomised legal
   states the swept-contact test and the end-position test return the **same** answer, which is what
   makes the sweep a guard rather than a behaviour change.
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same command-byte log ⇒ identical
   `gameHash` at every tick over a full 1728-tick run, twice in one process and once in a fresh sim;
   (b) a one-unit change in any command byte changes the final hash; (c) a committed golden fixture
   `tests/data/golden_hashes.json` pins the hash at every 48th tick for seed 8821477; (d) **a source
   guard** that greps `src/waterworld/{sim,tank,trig,sensors,sim_types,sim_config,sim_state}.nim` for
   `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts for `-ffast-math`,
   failing on any hit, plus a grep for `rand(` (only `drawInt` may draw); (e) `DirQ12` re-derived from
   `math.cos`/`math.sin` entry by entry, and `isqrt` checked exhaustively below 2¹⁶ and on perfect
   squares to 2⁴⁰; (f) `perm`, the initial particle table and the first 200 respawns are pure functions
   of `seed`, identical across two fresh sims, and `perm` is a permutation of `0..3`; (g) `rngDraws` is
   identical between two runs of the same command log.
3. **`tests/test_tank.nim`** — geometry and sensors: the spawn predicate is satisfied by every accepted
   spawn over 20 000 draws across 200 seeds, and the lattice fallback fires **zero** times on those
   seeds; sensor detection is exactly "centre distance ≤ 2 400 000" over 50 000 randomised pairs; every
   detected object lands in exactly one of the sixteen ray sectors and the sector index matches a float
   reference bearing to within one sector; a ray's `rock`/`wall` distance matches a float ray-cast to
   within 2 000 µm; the sixteen sectors tile 360° with no gap or overlap; `closing` has the sign of
   approach.
4. **`tests/test_control.nim`** — the controller: for 3 000 randomised (state, intent) pairs the command
   byte is in `0..255`, decodes to `dir ∈ 0..31`, `level ∈ 0..7`, and the implied acceleration magnitude
   is `≤ MaxThrustAccel + 1`; the same (state, intent) pair always yields the same byte; each of the five
   modes produces the documented goal point in its documented condition; `hold` brakes monotonically to
   `|v| = 0` within 96 ticks from full speed; a stunned skimmer and any non-`Playing` phase force
   `cmd = 0`; poison repulsion strictly increases the distance to a stationary poison over 48 ticks for
   every `standoff_m ≥ 0.5`; the rock-tangent rule never steers a skimmer into the rock over 10 000
   randomised goal points.
5. **`tests/test_baselines.nim`** (release-only) — **the bounded-orders / legality assertion on the
   scripted baselines**: for 500 pseudo-random world states × both baselines, the emitted intent
   validates against the reply schema — every numeric field finite and inside its range, `mode` in its
   enum, `target` either `none` or a **currently detected** plankton id, `partner` either `none` or
   another skimmer's alias (never its own), `waypoint` inside the tank, `note` ≤ 160 runes, `say` ≤ 48
   runes — and the compiled command byte is in range. Plus the tuning pin: **four `shoal`s reach at
   least 8 captures on at least 18 of 20 seeds** with a mean score above +70; four `drifter`s score
   strictly below four `shoal`s in mean; a 2-`shoal`/2-`drifter` mix still reaches at least 4 captures
   on at least 16 of 20 seeds. (This is the anti-regression pin for the whole physics tuning: if the
   baselines cannot capture, the three `BaselineParams` numbers are wrong — re-run
   `tools/tune_baselines.nim` and commit the sweep's pick to `tools/ci/baseline_tuning.json`, which
   `tests/test_tuning.nim` re-asserts. The physics constants do not move.)
6. **`tests/test_intents.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON, a
   percentage `throttle`, a centimetre `standoff_m` and waypoint, `waypoint` as `{"x":…,"y":…}`,
   `target` as `"plankton F2"`, an unknown `mode`, a `partner` equal to my own alias, a `target` that is
   not currently detected, NaN/absent fields, out-of-range values, a 300-character `note`, and a `say`
   whose 48th and 49th characters are a **4-byte emoji** — the truncation must land on the **rune**
   boundary and the result must still round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive
   failures ⇒ the `shoal` intent plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a
   `throttled` client ⇒ **zero** retries.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all four seats' calls go out
   in one parallel batch** (the fake records in-flight windows; the test asserts all four intersect);
   consecutive batches are ≥ `turnSpacingMs` apart; the per-turn budget is enforced with a hung client;
   the budget guard switches to scripted and the episode still ends `complete/*`; the 660 s stop yields
   `deadline/wall_clock`; a tripped invariant yields `fault/sim_fault` with a partial replay; a
   disconnected seat plays `shoal` and revives on reconnect; a never-connecting seat is reported to
   `COGAME_PLAYER_FAILURE_URI` and the run still reaches a normal ending; a registration that arrives
   before its player index exists is **held and applied**, not dropped.
8. **`tests/test_locality.nim`** — the sensor-locality invariant. Over 200 randomised states: seat `s`'s
   composed LLM user message and its Sprite frame contain a plankton or poison particle **iff** that
   particle's centre is within 2 400 000 µm of skimmer `perm[s]`'s centre; contain all three partners
   always; contain no other seat's `note`, `say`, `mode`, `target` or prompt; contain no `perm`, seed,
   RNG state, initial particle table, undetected particle count, or `sim.players[i].address`. Also:
   `control.thrustCommand`'s inputs are structurally limited to that skimmer's own state, its sensor
   frame and its seat's intent.
9. **`tests/test_scoring.nim`** — the formula and its sign: the six worked examples of §The game
   reproduce to 3 decimals; a capture requires **exactly** ≥ 2 overlapping skimmers (1 pays a nibble, 2
   and 3 both pay one capture, and 3 credits three assists); a lone skimmer parked on plankton for 480
   ticks collects **one** nibble, not 480 (the re-arm rule); a poison hit costs exactly −2.000, stuns for
   12 ticks and consumes the bloom; full throttle for the whole episode costs `6.912`; all four
   `results.scores` entries are bit-identical; `win` is true in all four slots iff
   `captures ≥ captureTarget`; reaching the target ends the episode on that tick.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full 4-seat scripted
    episode writes `results.json` and a `COWLDWWD` replay; `parseReplayBytes` accepts it;
    re-simulating from the config + recorded command bytes reproduces **every** recorded hash;
    **`tools/replay_summary.py` output parses under a strict UTF-8 JSON parser**
    (`json.loads(out.decode("utf-8"))`) with the fixture forced to carry a non-ASCII `say` and a
    non-ASCII policy label, so the UTF-8 path is real; the embedded config JSON decodes strictly and
    contains `seed`, `perm`, the geometry table and the initial particle table; every `intent` record is
    ≤ 600 runes; `results.reason`/`results.endRule` are in the legal enums; the stream contains exactly
    4 `register` records, 4 `intent` records per turn, at least one `capture` and one `nibble`, and
    exactly one `result` record.
11. **`tests/test_server.nim`** — websocket contract: registration chat accepted and **not** echoed into
    the replay chat stream; a prompt over 4000 runes truncated, not rejected; a non-registration chat
    from a player dropped; an input mask from a player ignored; bad token 403; `/healthz`; `/global`
    snapshot → ticks → game over; `/client/global` and `/client/player` serve real pages and neither
    opens the player socket; `/healthz` and `/global` still answer 15 s after the artifacts are written;
    artifact writes to `file://` URIs. **Two name spaces**: the composed LLM user message and the
    player-stream board labels contain no real name, while the chrome roster, `over` and `results.names`
    do.
12. **`tests/test_manifest.nim`** — **`num_agents == 4` in every variant *and* in
    `certification.game_config`**; `len(certification.players) == 4` and
    `len(certification.game_config.players) == 4`; every declared `player[]` id occupies at least one
    certification slot and its `resources.limits.cpu == "1"`; `results_schema` keys ==
    `playerResultsJson` keys with every per-seat array bounded `minItems: 4, maxItems: 4`; every array
    in `config_schema` declares `minItems`/`maxItems`; `game.protocols` has **both** `player` and
    `global` as `{"type":"text",…}`; `game.docs.readme` and all three pages are non-empty text;
    `game.description` present and `game.tags` **absent** (tags top-level, ≥ 3);
    `game.replay_viewer.bundle == "static-replay-viewer"` and there is no top-level `version` or
    `game.display_name`; `game.owner` present; every variant's `wallClockBudgetSeconds ≤ 0.6 × 1200`;
    `attempt1Ms + retryMs ≤ turnBudgetMs`; `maxTicks mod turnTicks == 0`; the compose service name
    uppercased with `-`→`_` equals the image placeholder and the image is `coworld-walker-waterworld`;
    the secret namespace equals `game.name`; `config_schema` covers every field `sim_config.update`
    reads.
13. **`tests/test_viewer.nim`** — static assertions over `client/replay_broadcast.html` and
    `client/chrome_common.js`: `chrome_common.js` is **byte-identical** to the starter's copy (sha256
    pinned); `replay_broadcast.html` still contains ctf's `relayout()` with `--band`, `--topband` and
    the `--hudscale` clamp on `:root`; `#endcard { bottom: var(--band) }`; `#scorebug`, `#bannerlane`,
    `#killfeed`, `#transport`, `#mmwarn`, `#endcard`, `#momentum` and the `.tiny` block are present;
    `#viewpanel`, `#fpv` and `#povBadge` are **absent**; a `.beat-marker` CSS rule exists for **every**
    beat kind the sim emits (`capture`, `poison`, `target_met`, `over`) and every marker is a
    `<button>`; no game-block top-level name collides with chrome_common's alias list; the
    `.plate-name { flex: 1 1 auto; min-width: 3.2em` rule is present; `broadcast_core.js` differs from
    the starter's copy in **exactly** the `WATERWORLD_WIRE` identifier; no `ctf_`/`CTF_`/`paintball`
    identifier survives in `client/`, `replay-viewer/` or `src/`; `static_replay.js` sets both
    `data-replay-loaded` and `data-replay-error`; and `config.nims` contains **no** `MODULARIZE` or
    `EXPORT_NAME`.
14. **`tests/test_startup.nim`** — `/bin/walker-waterworld` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when unpinned
    (before `config.update`) and honoured when pinned; both entrypoints exist and are executable in the
    image.
15. **`tests/test_perf.nim`** (release-only) — 1728 ticks of physics plus 6 912 controller evaluations
    plus 6 912 sensor frames complete in under 60 s.

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
  playback stop advancing, or if `canvas_text.never_inside` is non-zero (fixed tank). The 720-tick
  fixture is 30 s long, so a 12 s soak cannot end the replay. **This is the only gate that runs the
  viewer rather than checking that its files exist** (cogame-lantern, 2026-08-23).
- `wasm-viewer`, second step — **`tools/ci/renderer_fixture.html`**: `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so every seat plays scripted and the smoke replay carries only the baselines'
  fixed `say` strings; nothing in CI would otherwise exercise the bubble band or the feed at full cap.
  The fixture loads the real renderer with a **full-cap 48-rune `say` and 160-rune `note` on all four
  seats at once**, at 360, 620 and 1280 px, self-checks its own string lengths, and is run through
  `viewer_smoke.mjs --strict-text-bounds` in its own step (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Multiwalker.** The idea's first half is deliberately not built: **side-view articulated Box2D
  bipeds have no host in any starter runtime.** Three two-legged bodies with per-joint torques
  balancing a rigid package on their heads needs an articulated-rigid-body solver with contact-rich
  walking — a new engine, plus a second observation model, a second controller, a second scoring rule,
  a second board and a seat count of 3 instead of 4. Paintbot supplies a top-down point-body loop and
  nothing in the lineage supplies the other thing. It returns, if ever, as its own coworld
  (`cogame-multiwalker`) on an engine chosen for it, never as a variant of this one. The idea's
  multiwalker replay plan (Box2D side view, package tilt gauge) goes with it.
- **Pursuit.** Explicitly excluded by the idea itself ("pursuit is covered by MP Predator Prey"), and
  not built here.
- **A raw per-tick continuous-vector transport for policies.** The v1 control channel is one intent per
  72-tick turn plus the deterministic controller; the per-tick thrust byte is derived server-side,
  recorded, and replayed. Because the controller is already a pure function of
  `(intent, own state, sensor frame, tick)`, exposing a per-tick socket action is a protocol addition,
  not a redesign — but it is not in v1, and the LLM policy interface is the one the platform ranks.
- **pymunk / Box2D / any float solver, and bit-exact `waterworld_v4` parity.** Rejected for Cogball's
  reason: those solvers ride on `sinf`/`cosf`/`atan2f` and float accumulation order, which would make
  the native↔wasm hash chain depend on two builds agreeing. Nothing here reproduces `waterworld_v4`
  frame for frame, no test asserts it does, and no constant is copied from it.
- **`waterworld_v4`'s literal ray sensors** (a ray that can miss a particle between spokes), its
  per-sensor multi-channel float observation vector, its `n_coop` above 2, its obstacle count above 1,
  its `local_ratio` reward mixing and its per-agent (rather than shared) poison penalty. v1's percept is
  range-based detection presented as sixteen rays, and every reward is shared.
- **Image observations.** Seats get a structured JSON sensor frame, never an RGB crop. There is no pixel
  observation path and no CNN policy interface.
- **Any inter-seat communication, in any form, at any bandwidth** — including a symbol channel, a
  shared blackboard, or an emergent side channel through the observation. `say` and `note` are one-way
  to the spectator feed. This is not a v0.2 item; the whole game is coordinating without talking.
- **A variable seat count, a variable particle count as a *variant*, gaps in the pod, or teams.**
  `num_agents` is 4 in every variant and the cert fixture; the pod is one cooperative side. `foodCount`
  and `poisonCount` exist in `config_schema` for tuning and tests, and both shipped variants use the
  same values.
- **Skimmer-vs-skimmer collision, hull damage, energy budgets, refuelling, or a battery.** Skimmers pass
  through each other (which is what makes two-on-one-particle geometrically easy and the *timing* the
  hard part); the only running cost is thrust.
- **Currents, waves, procedurally generated tanks, multiple rocks, or moving obstacles.** One tank, one
  rock, dead centre, every episode. Procedural tanks are the obvious v0.2 variety and are not in v1.
- **Everything ctf's arena rules carried**: guns, flags, fog cones, first-person POV, lives, respawn,
  grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the barrage, the hill,
  the paint grid, procedural terrain, the map pool, the map editor and mapkit. Deleted, not disabled.
- **Player debug-sprite overlays** (ctf's `0x86` channel) and the zoom/minimap panel. The seats send no
  inputs and draw no overlays in v1; `#viewpanel` is removed because the board always fits the frame.
- **Audio, 3D, camera cuts, slow-motion replays**, and any downloaded art asset.
- **Persistent memory across episodes** (no notes carried between runs) and any tournament structure
  beyond the platform league.
