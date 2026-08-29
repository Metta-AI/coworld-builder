# cogame-continuous-control — design note (2026-08-29, paintbot lineage)

**Starter: `Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`
and read for this note. **Every convention there holds here unless this note says otherwise.** That
means: Nim throughout; the `src/ctf/` module split (`sim.nim` importing and re-exporting the sim
modules; `sim_types.nim` owning `GameVersion` (`src/ctf/sim_types.nim:21`), `TargetFps* = 24` and
`ReplayFps* = 24` (`:401`, `:342`) and the rune caps `ShoutMaxChars` / `MaxNoteRunes` / `MaxSayRunes` /
`MaxPolicyLabelRunes` / `MaxPromptRunes` (`:772`, `:819-824`), with its prepend-only changelog-comment
discipline and the flatty wire types whose field order is sacred); the mummy HTTP/websocket server
implementing the Coworld contract including its `wallClockBudgetSeconds` stop
(`src/ctf/server.nim:1438-1448`); the `decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim` /
`control.nim` commander layer with its one-batch-per-turn shape (`src/ctf/decide.nim:427`
`engine.client.curl.makeRequests`), its `attempt1Ms` / `retryMs` / `turnBudgetMs` / `turnSpacingMs`
deadlines (`src/ctf/decide.nim:386-389`, `:406`), its tolerant JSON extraction, its rune truncation
(`src/ctf/directives.nim:61-68`) and its fallback ladder with the exact two log phrasings
(`src/ctf/decide.nim:463` for attempt 1, `:491` "falling back" only on the second failure); the binary
`COWLDCTF` replay of *inputs plus a per-tick `gameHash`* (`src/ctf/replays.nim:142`), re-simulated by
**the same sim module** compiled to wasm by `replay-viewer/config.nims`; the `client/` broadcast chrome
(`chrome_common.js` + `broadcast_core.js` + `replay_broadcast.html` with its
`window.PaintballChrome.install(PB_CTX)` splice hook at `client/replay_broadcast.html:4341` / `:4348` and
the game-block banner at `:4355`); nimby + `Dockerfile` + `Dockerfile.replay-viewer` +
`tools/build_replay_viewer.sh`; and the Nim test suite with its four shards (`tests/shard_1..4.nim`,
`tests/config.nims`).

**Starter choice, one line: this is a real-time physics loop whose rules are written into this repo —
the first row of the starter table** (`prompts/10-design.md` §Starter table: "any real-time game loop
(grid OR continuous physics), new rules written for this coworld"; the operator ruling of 2026-08-22
puts new physics games on paintbot, not on `cogame-moba`). It is deliberately **not** a bit-exact port
of Gymnasium MuJoCo or of `dm_control`: MuJoCo is a C solver with a float state vector and `dm_control`
is a Python package on top of it, and neither can be embedded in a Nim sim module that must **also**
compile to wasm32 for the static replay viewer — which is a non-optional pin
(`playbooks/make-coworld.md` §Phase 0: "Replays are a static file + a browser wasm viewer — NEVER a
pod"). What this repo implements is the *problem*: a **locomotion ladder of planar articulated bodies**
— hopper, cheetah, walker — on its own deterministic, seeded, fixed-point/integer-safe 2D physics sim
written in Nim. Every divergence from the MuJoCo / DMC sources is named in §Sim module → "Documented
divergences" and mirrored into `docs/PHYSICS.md`. The precedents for forking paintbot for a physics
game are `cogame-cogball` (2026-08-22), `cogame-pistonball` (2026-08-25),
`cogame-walker-waterworld` (2026-08-26) and `cogame-physics-bodies` (2026-08-28); the precedent for a
**single-seat LLM-dispatcher-over-a-deterministic-driver** coworld on this same starter is
`cogame-sokoban` (2026-08-29).

Where this note departs from coworld-ctf it says so. The departures are: the rules are a planar
multibody sim's, not paintbot's (§Sim module lists what is deleted); the world is a **side-on 60-metre
track**, not a top-down pixel arena, so ctf's arena masks, procedural map generator, map pool, map
editor and mapkit are deleted; the game is **perfect information with one body**, so ctf's fog, vision
cones and raycasting are deleted outright rather than replaced; there is **one seat, not eight**, and
no teams; `MaxSayRunes` / `MaxNoteRunes` are re-pinned (§Decisions → reply schema); and — the one
structural change to ctf's determinism architecture — **the driver is integer-only and sits INSIDE the
hash boundary** (§Sim module → determinism), because the recorded action here is one order per turn,
not one byte per tick.

### Source idea (verbatim)

> SA Continuous Control — MuJoCo Gym and DeepMind Control: Humanoid, Ant, Cheetah as a locomotion ladder
>
> Single-agent coworld over the locomotion standards: Gymnasium MuJoCo (HalfCheetah, Hopper, Walker2d, Ant, Humanoid, Swimmer) and DeepMind Control Suite (cartpole, reacher, cheetah-run, walker-walk, quadruped, humanoid, dog, manipulation), plus Brax/MJX for cheap vectorised versions. Continuous joint torques from proprioceptive state (or pixels in DMC); fixed-length episodes; return is the score.
>
> Seats: 1
> Motive: return maximisation
> Policy interface: continuous torques per step — neural-policy coworld only; no LLM path (deliberately)
> Fills gap: the other half of the RL canon; gives neural-policy teams a place on the site. Lowest 'watchability per episode' of the catalog — pair with a highlight reel (falls, gaits).
> Integrity: seeded initial states; replay verification by deterministic re-simulation.
>
> Replay plan (watchability): MuJoCo render; gait gallery; 'fastest Humanoid' board.
>
> Source: Gymnasium mujoco; github.com/google-deepmind/dm_control; Brax.

### The idea's "no LLM path", resolved

The idea says "neural-policy coworld only; no LLM path (deliberately)". **The platform pin overrides
it** (`docs/SPEC.md` §Design pins; `playbooks/make-coworld.md` §Phase 0: "Build **both** an LLM/strategy
policy and a scripted baseline from day one (same image, env-switched)"). The tension is resolved the
way the recent single-agent runs on this starter resolved it (`cogame-sokoban`, 2026-08-29;
`cogame-minigrid` and `cogame-crafter`, 2026-08-28): **the seat is an LLM dispatcher/controller over a
deterministic per-tick physics driver.** The LLM does not emit joint torques — nobody can emit 6
torques 24 times a second over an HTTP round trip. It emits a **gait order** at bounded decision points
(one order every 36 ticks = 1.5 s), and a deterministic, integer-only, in-repo **central pattern
generator + PD servo** turns that order into per-joint target angles and torques **every substep**, 240
times a second. The scripted baselines drive **the identical order interface** with a fixed algorithm,
so the two policy kinds are strictly comparable and a baseline is legal by construction. The
continuous-torque actuator the idea asks for is real and is what the physics actually integrates; what
the note reinterprets is *who chooses its parameters and how often*. This is stated again, in the same
words, in `docs/RULES.md`.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins) and where each is satisfied

| Pin | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time physics loop, rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-continuous-control` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=trotter\|plodder`) |
| Static wasm replay viewer, never a pod | §Viewer (`replay_viewer.bundle = static-replay-viewer`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim (page + appended block, byte-identical `chrome_common.js`), real art | §Viewer → Chrome provenance, §Viewer → Art |
| Two name spaces | §The game → Seats and aliases (in-game alias `Alpha`; real policy names spectator-side only) |
| Degrade never hang; play inside 60 % of 1200 s | §Decisions → Cadence (typical 179 s, worst 501 s, engine stop 690 s, budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 1`, three times |
| Per-turn LLM call budget stated (single seat, one parallel batch) | §Decisions (exactly one request per turn, two with the retry; ≤ 84 per episode) |
| Replay bytes self-sufficient | §Server → Replay bytes (names, config, morphology + gait tables, per-turn orders, per-tick hashes, state keyframes, seed) |
| Rune-boundary truncation on every free-text field | §Decisions → Reply schema and per-field caps |
| Seeded initial states; replay verification by deterministic re-simulation (the idea's integrity note) | §Sim module → Start pose and seeding; §Sim module → Determinism, native ↔ wasm |

---

## The game

**One cog, three bodies, sixty metres of track, three times.** The cog is handed a **hopper** — a
single-legged pogo of four links and three powered joints — and told to cover ground. Then a
**cheetah**: seven links, six joints, two legs, no way to fall over and every reason to go fast. Then a
**walker**: seven links, six joints, two legs, and a torso that tips over if it gets ahead of its feet.
Each body starts at the same line, on flat ground, under gravity, with a small seeded wobble in its
joints. Each has **19.5 seconds** and a **60-metre line**. The score is the **return**: metres covered,
plus a small bonus for every tick spent upright, minus a small cost for slamming the actuators.

Nothing about the bodies changes between episodes. What changes is the **order**: every 1.5 seconds the
cog names a **gait** (`stand`, `crouch`, `walk`, `run`, `bound`, `brake`) and five numbers — cadence,
power, lean, stride bias, phase shift — and a deterministic pattern generator in this repo executes it,
240 times a second, until the next order. A hopper that runs a gallop cadence face-plants in two
strides. A walker that leans +40 into a fast cadence out-runs its own feet and pitches over at 8 m. A
cheetah that never leans and never raises power crawls. The whole game is: **read the body you have
been given, and tune the gait it needs before it falls over.**

### Seats and aliases

- **`num_agents` = 1.** Exactly one seat, always — in both manifest variants and in the certification
  fixture, always inside `game_config`. This is the idea's own "Seats: 1", and it is what continuous
  control is: a solitary return-maximisation problem. Every episode is a solo run; policies are
  compared across episodes, never within one.
- **Two name spaces.** In-game the seat is **`Alpha`** — `IdentityNames[0]` from the starter's
  `src/ctf/roster.nim:64-65` (`"alpha"`), title-cased by `seatAlias(slot)`. That alias is the only name
  that appears in an observation, in a prompt, in a `say`, or drawn on the board. The seat's **real
  policy/player name** (`daveey`, `daveey-1`, `Baseline (1)`) lives only in `results.names`, in the
  replay's join record, and spectator-side in the viewer's scorebug plate, roster row and endcard.
  `showPlayerLabels` is **false**, as in the starter's paintball variant, so nothing drawn on the board
  leaks an identity. With one seat there is nobody to meta-game against, but the pin is satisfied both
  ways, not either way: the alias is what the model sees, the real name is what the spectator sees.

### The world, the units, and why they are integers

The whole sim runs in **fixed-point integers**, for Cogball's, tandem's, pistonball's,
walker-waterworld's and physics-bodies' reason: replays are re-simulated by the **emscripten/wasm32**
build of the same Nim module that the **native amd64** server ran, and their per-tick `gameHash` chains
must match bit-for-bit. Integers make that true by construction rather than by an argument about two
builds of libm agreeing. `src/cc/{sim,solver,body,driver,gaits,trig}.nim` contain **no floating point
at all**, and a CI grep enforces it (§Tests 13).

**Everything dynamical is one type: `int64` holding a Q16 fixed-point SI value** (65 536 = 1.0), in
metres, seconds, kilograms, radians and their derived units.

| Quantity | Unit | Representation |
|---|---|---|
| Position `x`, `y` | metres | Q16 `int64` (resolution 15.3 µm; envelope ±100 m) |
| Linear velocity `vx`, `vy` | metres/second | Q16 `int64` (envelope ±12 m/s) |
| Angle `a` | radians, wrapped to `(−π, +π]` | Q16 `int64` (resolution 15.3 µrad) |
| Angular velocity `w` | radians/second | Q16 `int64` (envelope ±40 rad/s) |
| Mass, inverse mass | kg, 1/kg | Q16 `int64` |
| Inertia, inverse inertia | kg·m², 1/(kg·m²) | Q16 `int64` |
| Torque, impulse | N·m, N·s | Q16 `int64` |
| Stride phase `cyclePos` | micro-cycles, `0 … 999_999` | `int32` |
| Return accumulators | **micro-points** (1e-6 of a point) | `int64` |
| Counters (ticks, strides, falls, saturated ticks) | — | `int32` |

Two arithmetic rules, both grep-enforced:

1. **`mulQ(a, b) = (a * b) div 65_536`, using `div`, never `shr`.** Nim's `shr` on signed integers is a
   portability trap; `div` truncates toward zero on every backend, is symmetric under negation, and is
   what makes native and wasm32 agree. There is **no** `shr` on a signed value anywhere in the sim.
2. **Every Q16 quantity is range-checked into its declared envelope once per tick** (resolution step 8
   below). That bounds every product in the solver under 2⁶² with three orders of magnitude of
   headroom, so no intermediate can overflow `int64`, and a bug that would have overflowed becomes a
   `fault` end instead of a silent wrap.

**Trigonometry is a committed table.** `src/cc/trig.nim` holds `SinQ16Table*: array[1025, int32]`,
entry `k` = `round(65536 · sin(k · π / 2048))`, generated once by `tools/gen_trig_table.nim` and checked
in. `sinQ16(aQ16)` reduces the angle to a quadrant by integer arithmetic and interpolates linearly
between two table entries; `cosQ16(a) = sinQ16(a + π/2)`. A test re-derives every entry from
`math.sin` and asserts `|err| ≤ 2` in Q16 (§Tests 3). **There is no square root in the solver at all**:
the ground is a single horizontal line so every contact normal is exactly `(0, 1)`, and every joint
constraint is a 2×2 linear solve. `isqrtQ16` exists in one place only — `src/cc/report.nim`, which
builds the observation and the viewer packet — and never touches hashed state.

**View coordinates** — the only coordinates a policy or the chrome ever sees — are **metres, x forward
(right), y up, origin at the start line on the ground**. That is also the sim's own frame: unlike the
top-down ctf games this one is a **side elevation** with y up, so there is no y-flip anywhere. Angles
reported to policies are **degrees, positive counter-clockwise**, and every number shown to a policy is
rounded to 2 decimals.

**The track.** Flat ground at `y = 0`, running from `x = −6.00 m` to `x = +60.00 m`. `x = 0` is the
start line, `x = 60` is the **finish line**. There are no obstacles, no slopes and no walls — flatness
is what makes the solver sqrt-free and it is what every one of the source environments actually uses.
The board render scale is **1 board pixel = 6 250 µm**, and the board is a **camera viewport** of
`MapWidth = 1440`, `MapHeight = 960` board pixels — i.e. **9.00 m × 6.00 m of world**, `BOARD_ASPECT`
1.5, the same aspect the starter's chrome was authored against. The camera tracks the torso in x
(clamped to `[−6, 60] m`) and is fixed in y. Logical map pixels are `1 440 × 960 = 1 382 400`, under
`MaxSupersampledMapPixels` 8 000 000 (`src/ctf/global.nim:1095`), so `boardRenderScaleFor` still returns
`RenderScale = 2` (`:1108`) and `predictedViewerRenderBytes(1440, 960)` is
`1 382 400 · 4 · (4·2·2 + 6)` = **121 651 200 B ≈ 122 MB** against `WasmViewerBudgetBytes`
1 600 000 000 (`:1129`) — the viewer's load-time capacity preflight
(`replay-viewer/ctf_replay.nim:71-76`) passes with 13× headroom, and every one of those constants is
**kept unchanged**.

### The three bodies

A body is a set of **capsule links** (a segment of half-length `hl` with radius `r`) connected by
**hinge joints**, all in the plane. There is no self-collision, no joint friction beyond the servo's
damping, and no aerodynamic drag. Contact with the ground happens only at the **two end caps of each
foot link**; every other link may pass through the ground plane and is stopped by the same contact rule
if it does (a belly-flopping cheetah scrapes, it does not sink).

**HOPPER** — 4 links, 3 joints, 2 contact points. Total mass 15.49 kg. Neutral standing torso height
1.25 m.

| i | link | `hl` (m) | `r` (m) | `m` (kg) |
|---|---|---|---|---|
| 0 | `torso` | 0.200 | 0.050 | 3.53 |
| 1 | `thigh` | 0.225 | 0.050 | 3.93 |
| 2 | `shin` | 0.250 | 0.040 | 2.71 |
| 3 | `foot` | 0.195 | 0.060 | 5.32 |

| j | joint | parent → child | limits (deg) | `τmax` (N·m) |
|---|---|---|---|---|
| 0 | `hip` | torso → thigh | −150 … 0 | 200 |
| 1 | `knee` | thigh → shin | −150 … 0 | 200 |
| 2 | `ankle` | shin → foot | −45 … +45 | 200 |

**CHEETAH** — 7 links, 6 joints, 4 contact points. Total mass 14.11 kg.

| i | link | `hl` (m) | `r` (m) | `m` (kg) |
|---|---|---|---|---|
| 0 | `torso` | 0.500 | 0.046 | 6.36 |
| 1 | `bthigh` | 0.145 | 0.046 | 1.54 |
| 2 | `bshin` | 0.150 | 0.046 | 1.59 |
| 3 | `bfoot` | 0.094 | 0.046 | 1.10 |
| 4 | `fthigh` | 0.133 | 0.046 | 1.44 |
| 5 | `fshin` | 0.106 | 0.046 | 1.20 |
| 6 | `ffoot` | 0.070 | 0.046 | 0.88 |

| j | joint | parent → child | limits (deg) | `τmax` (N·m) |
|---|---|---|---|---|
| 0 | `back_hip` | torso → bthigh | −30 … +60 | 120 |
| 1 | `back_knee` | bthigh → bshin | −45 … +45 | 90 |
| 2 | `back_ankle` | bshin → bfoot | −23 … +45 | 60 |
| 3 | `front_hip` | torso → fthigh | −57 … +40 | 120 |
| 4 | `front_knee` | fthigh → fshin | −69 … +50 | 60 |
| 5 | `front_ankle` | fshin → ffoot | −29 … +29 | 30 |

**WALKER** — 7 links, 6 joints, 4 contact points. Total mass 23.15 kg. Neutral standing torso height
1.25 m.

| i | link | `hl` (m) | `r` (m) | `m` (kg) |
|---|---|---|---|---|
| 0 | `torso` | 0.200 | 0.050 | 3.53 |
| 1 | `r_thigh` | 0.225 | 0.050 | 3.93 |
| 2 | `r_shin` | 0.250 | 0.040 | 2.71 |
| 3 | `r_foot` | 0.100 | 0.060 | 3.17 |
| 4 | `l_thigh` | 0.225 | 0.050 | 3.93 |
| 5 | `l_shin` | 0.250 | 0.040 | 2.71 |
| 6 | `l_foot` | 0.100 | 0.060 | 3.17 |

| j | joint | parent → child | limits (deg) | `τmax` (N·m) |
|---|---|---|---|---|
| 0 | `r_hip` | torso → r_thigh | −150 … 0 | 100 |
| 1 | `r_knee` | r_thigh → r_shin | −150 … 0 | 100 |
| 2 | `r_ankle` | r_shin → r_foot | −45 … +45 | 100 |
| 3 | `l_hip` | torso → l_thigh | −150 … 0 | 100 |
| 4 | `l_knee` | l_thigh → l_shin | −150 … 0 | 100 |
| 5 | `l_ankle` | l_shin → l_foot | −45 … +45 | 100 |

Link inertia is `I = m · (hl² / 3 + r² / 4)` about the link centre, computed once at stage start in Q16
and stored with `invM` and `invI`. Every one of these numbers lives in one committed table,
`MorphTable*` in `src/cc/body.nim`, and is written into the replay config JSON so a viewer never has to
know them a priori.

**Falling.** Only the two bodies that can fall, do:

| morph | unhealthy when | ends the stage |
|---|---|---|
| `hopper` | torso centre `y < 0.70 m` **or** `\|pitch\| > 20°` | yes |
| `cheetah` | never | **no** |
| `walker` | torso centre `y < 0.80 m` or `y > 2.00 m` **or** `\|pitch\| > 57°` | yes |

Cheetah has no termination for the same reason Gymnasium's `HalfCheetah-v5` has none: it has no
upright posture to lose. A cheetah on its back simply scores badly.

### Solver constants (fixed; identical every episode, in every variant)

```
Gravity                 = 9.81 m/s^2          (Q16   642_908, applied to every link's vy)
TargetFps               = 24                   (ctf's, kept verbatim - sim_types.nim:401)
SubstepsPerTick         = 10                   -> substep dt = 1/240 s
SolverIterations        = 12                   (per substep)
BaumgarteNum / Den      = 1 / 5                (positional bias beta = 0.20)
PenetrationSlop         = 0.0005 m             (0.5 mm; no bias inside the slop)
GroundFriction          = 0.90                 (Q16 58_982; Coulomb, clamped to mu * normal impulse)
GroundRestitution       = 0                    (feet do not bounce)
JointLimitBiasNum / Den = 1 / 4
ServoKp[m][j], Kd[m][j] = the swept table (§Decisions -> the driver)
MaxLinSpeed             = 12.0 m/s             (per component clamp, sqrt-free)
MaxAngSpeed             = 40.0 rad/s
GroundY                 = 0.0 m
TrackStartX             = 0.0 m ; TrackLineX = 60.0 m ; TrackBackX = -6.0 m
InitPerturb             = 0.05 rad             (seeded per-joint start offset)
StateKeyframeTicks      = 48
```

**No warm starting.** Accumulated constraint impulses are zeroed at the top of every substep, so the
sim state is exactly the link states plus the stride phase and nothing carried in solver internals.
That costs a little stability and buys an exactly-defined, exactly-hashable state — which is the whole
reason this repo can ship a wasm re-simulating viewer.

### Time, stages, turns

```
turnTicks       =   36   (1.5 s)   -- the decision cadence
stageTicks      =  468   (19.5 s)  -- 13 turns of running per stage
resetTicks      =   36   (1.5 s)   -- the hold after a stage resolves; 1 turn
stagesPerEpisode=    3
maxTurns        =   42   = 3 x (13 + 1)
maxTicks        = 1512   (63.0 s)  = 3 x (468 + 36) = 42 x 36
maxGames        =    1               -- a ladder has no side to swap
```

Turn boundaries live on the **global** tick grid (`t mod 36 == 0`) and are **never** re-aligned when a
stage ends early. A hopper that falls at tick 213 is followed by 36 reset ticks and the next stage
starts at tick 249, mid-turn. That is deliberate: re-aligning would make the wall-clock budget a
function of how the run went, and the wall clock is what the platform kills you for. **A fall therefore
shortens the episode** in both ticks and LLM turns — the episode settles early rather than overruns.

`fastMode: true` in every variant, as in the starter's paintball variant: the seat sends no per-tick
inputs (the server computes every joint target), so the Sprite v1 Ready packet's dead-reckoning hazard
cannot arise.

**Variants** (both `num_agents: 1`, both the same constants above):

| Variant | Ladder (in order) | `par` | `maxReturn` |
|---|---|---|---|
| `ladder` | `hopper`, `cheetah`, `walker` | **40.0** | 240.000 + 3.744 = **243.744** |
| `bipeds` | `hopper`, `walker`, `walker` | **30.0** | 300.000 + 5.616 = **305.616** |

`ladder` is the reporting variant: it is the idea's own "Humanoid, Ant, Cheetah as a locomotion ladder",
reduced to the three morphologies that are genuinely planar. `bipeds` drops the cheetah, which is the
only body that cannot fall, so falling dominates and a policy that only knows how to go fast collapses;
the second `walker` gets a different seeded perturbation from the first because the draw is keyed on the
stage index (§Sim module → Start pose and seeding).

### Turn and tick structure — the exact resolution order

Per **command turn** `T` (`t mod 36 == 0`, `phase == Playing`), in this order:

1. If the current stage has resolved and its reset hold has elapsed, write its stage result, emit
   `stageend`, and start the next stage: build the body from `MorphTable`, place it in the neutral pose
   with the seeded perturbation, zero every velocity, reset `cyclePos` to 0, `xStart := 0`, emit
   `stagestart`. If there is no next stage, end the episode (§End conditions).
2. Build the seat's observation object (§Decisions → observation) from the **current** state.
3. Issue the seat's LLM request. There is exactly **one** seat, so this is a **batch of one** through
   the starter's unchanged `engine.client.curl.makeRequests` path (`src/ctf/decide.nim:427`) — the code
   is the starter's one-parallel-batch-per-turn code carrying one request. Attempt-1 deadline
   `attempt1Ms = 6000`. A scripted seat computes locally, instantly, and consumes no request.
4. If the seat timed out, errored, returned non-JSON, or returned no object with at least one usable
   field, it is retried **once**, `retryMs = 3000`.
5. Still no usable reply → the **`trotter`** scripted order is computed server-side (the same proc the
   `trotter` baseline uses — imported, never duplicated) and a `fallback` record is written.
6. **Validate and clamp the order**, field by field, in the schema's order (§Decisions → reply schema).
   A field that is missing or unusable inherits **last turn's value**, and on turn 1 of a stage the
   gait's declared default. An out-of-range number is **clamped, never dropped** — unlike Sokoban there
   is no irreversible move here, so a clamped `power: 140 → 100` is the honest reading of the intent.
   Every clamp increments `ordersRepaired` and is reported back next turn.
7. The clamped order becomes `activeOrder` and is written as the turn's `order` replay record — **this
   is the game's entire input log**. `say` (≤ 140 runes) and `notes` (≤ 320 runes) are sanitised on rune
   boundaries; `notes` is echoed back to this seat next turn and to nobody else; `say` is drawn in the
   spectator feed.
8. `turnSpacingMs = 2600` is a floor on the wall clock between consecutive request **starts** (the
   starter's mechanism at `src/ctf/decide.nim:386-389`, kept), which pins the steady state at
   23 req/min against the sidecar's 30/min per-episode cap.

Then, for each of the next 36 ticks, in this order — **this is the whole physics of the game and
nothing else mutates the world**:

1. `tick += 1`; `stageTick += 1` (or `resetTick += 1` when `phase == StageReset`).
2. **Advance the stride phase.**
   `strideMilliHz = FreqMin[m] + (FreqMax[m] − FreqMin[m]) · cadence div 100`;
   `cyclePos := (cyclePos + strideMilliHz · 1000 div TargetFps) mod 1_000_000`.
   Integer division truncates; the advance is therefore a pure function of `cadence` and the morphology.
3. **Driver.** For every joint `j`, compute the tick's target angle (integer only, §Decisions → the
   driver). While `phase == StageReset` the order is forced to `{gait: brake, power: 0}` — the body
   flops and settles, which is the watchable half of a wipeout.
4. **Physics: `SubstepsPerTick = 10` substeps.** Each substep, in this exact order:
   1. **Gravity** — every link, in link index order: `vy -= mulQ(Gravity, dt)`.
   2. **Servo torques** — every joint, in joint index order. `relAngle = wrap(child.a − parent.a)`,
      `relRate = child.w − parent.w`, `err = wrap(target[j] − relAngle)`;
      `tau = clamp(mulQ(Kp[m][j], err) − mulQ(Kd[m][j], relRate), −τcap[j], +τcap[j])` where
      `τcap[j] = τmax[m][j] · (40 + 60 · power div 100) div 100`. Apply
      `child.w += mulQ(child.invI, mulQ(tau, dt))` and `parent.w -= mulQ(parent.invI, mulQ(tau, dt))`.
   3. **`SolverIterations = 12` passes**, each pass running, in this exact order:
      a. **Joint point constraints**, joint index order. For joint `j` with world anchors `pA`, `pB` and
         arms `rA`, `rB`: the 2×2 effective-mass matrix
         `K = (invMA + invMB)·I₂ + invIA·skew(rA)ᵀskew(rA) + invIB·skew(rB)ᵀskew(rB)`, inverted in Q16
         with a guarded determinant (a determinant below `DetEpsQ16 = 4` skips the constraint this pass
         and is counted; §Tests 5 asserts it never fires on any legal state). Solve for the relative
         anchor velocity plus the Baumgarte bias `−(1/5)·positionError/dt`, apply the impulse equal and
         opposite.
      b. **Joint limit constraints**, joint index order. Inequality on `relAngle` against `[low, high]`
         with accumulated impulse clamped to the correct sign, bias `(1/4)·overshoot/dt`.
      c. **Ground contacts**, in (link index, contact-point index) order. A contact exists when the
         point's world `y ≤ r + PenetrationSlop`. Normal `(0, 1)`: non-penetration impulse with
         restitution 0 and a Baumgarte bias outside the slop; then a **tangential (x) friction impulse**
         clamped to `±GroundFriction · accumulatedNormalImpulse` (Coulomb, accumulated-impulse
         clamping). Feet do not stick and do not bounce.
   4. **Integrate**: for every link in index order, `x += mulQ(vx, dt)`, `y += mulQ(vy, dt)`,
      `a = wrap(a + mulQ(w, dt))`.
   5. **Clamp**: `vx`, `vy` to `±MaxLinSpeed` per component; `w` to `±MaxAngSpeed`.
5. **Accounting.** `distance := torso.x − xStart` (net displacement — it may be negative);
   `bestX := max(bestX, torso.x)`; `uprightTicks += 1` when the morph has a health test and passes it;
   `ctrlCostAccum += Σ_j e_j²` with `e_j = |tau_j| · 100 div τcap[j]` sampled at the **first substep**
   of the tick (one sample per tick per joint — cheap, and the mean of ten substeps buys nothing the
   sweep cannot absorb); `saturatedTicks += 1` when any `e_j == 100`; `strideCount` is advanced by
   `cyclePos` wrapping past zero; a foot going from off-ground to on-ground is a **footstrike** (a pure
   renderer FX, not an event, §Server → event vocabulary).
6. **Stage termination**, evaluated in this order; the first that fires resolves the stage at this tick:
   a. `torso.x ≥ TrackLineX` (60.00 m) → **`lined`**. `distance := 60.000`, `uprightTicks := stageTicks`
      (crossing the line is not punished for the ticks it saves), emit `stageend`.
   b. the morph terminates on falls **and** it is unhealthy → **`fell`**; emit `fall` carrying
      `why ∈ {low, high, pitched}` and the x at which it happened.
   c. `stageTick == stageTicks` (468) → **`ran`**; emit `stageend`.
7. **Milestones.** When `distance div 5 m` increases, emit `milestone {stage, metres}`.
8. **Invariant guard.** Any link position outside `[−20, 80] × [−2, 20] m`, `|v| > MaxLinSpeed`,
   `|w| > MaxAngSpeed`, `a` outside `(−π, π]`, or an `int64` range check tripped in the debug build →
   the episode ends `fault` / `simFault` (§End conditions).
9. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged (§Sim module → determinism lists what it mixes). If `tick mod StateKeyframeTicks == 0` or
   the stage just started, a **state keyframe** is written too.
10. If the stage resolved at step 6, `phase := StageReset` for exactly `resetTicks = 36` ticks, then the
    next stage starts on the following tick (or the episode ends).

There is no rescue rule, no difficulty ramp, no re-try and no restart. A hopper that falls at 2 m keeps
that 2 m and moves on.

### Scoring, sign, and what the league ranks by

Per stage `k` with morphology `m`, all in **micro-points** (`int64`):

```
distanceMicro[k]  = (torso.x - xStart) in micro-metres           # may be NEGATIVE
distTermMicro[k]  = distanceMicro[k] * DistNum[m] div DistDen[m]
uprightMicro[k]   = UprightPerTick[m] * uprightTicks[k]
ctrlMicro[k]      = ctrlCostAccum[k] div 64
stageReturn[k]    = distTermMicro[k] + uprightMicro[k] - ctrlMicro[k]

totalReturnMicro  = sum over k of stageReturn[k]
scores[0]         = totalReturnMicro / 1_000_000, emitted as a double rounded to 3 decimals
```

| `m` | `DistNum/DistDen` (points per metre) | `UprightPerTick` (µpts) | max distance term | max upright | competent run |
|---|---|---|---|---|---|
| `hopper` | 2 / 1 = **2.00** | 4 000 (1.872 pts/stage) | 120.000 | 1.872 | ~9 m → 18.0 |
| `cheetah` | 1 / 2 = **0.50** | 0 (no health test) | 30.000 | 0.000 | ~45 m → 22.5 |
| `walker` | 3 / 2 = **1.50** | 4 000 (1.872 pts/stage) | 90.000 | 1.872 | ~16 m → 24.0 |

The three points-per-metre numbers are the **inverse of how far each body can go**, chosen so that a
competent run is worth roughly **twenty points on every stage** and no single morphology decides the
episode. They are constants of the game, printed in the observation and in `docs/RULES.md`.

**The control cost is deliberately small.** At full saturation a 6-joint stage accrues
`468 · 6 · 100² = 28 080 000` cost units → `28 080 000 div 64 = 438 750 µpts = 0.439 points`, against a
twenty-point stage. That is the same ratio Gymnasium's `ctrl_cost_weight` has against its forward
reward. It exists so that two policies that cover the same ground are separated by the one that does it
without slamming every actuator into its stop, and for no other reason.

**Sign: higher is better, and the score CAN be negative.** A cog that drives its cheetah backwards for
19.5 s and saturates every joint scores `−0.5 · 12 · 19.5 … − 0.44` — a large negative number. There is
no floor clamp and no participation term. Clamping at zero would make "fell over immediately" and
"sprinted the wrong way for a minute" indistinguishable, and the league needs them distinguishable. The
theoretical maximum is **243.744** on `ladder` and **305.616** on `bipeds`; the practical ceiling is far
lower and is the point of the ladder.

**The league ranks by `results.scores[0]`** — the episode return, exactly as the idea asks ("return is
the score", "Motive: return maximisation"). With one seat every episode is a solo run, so phase 50 uses
the platform's Elo (1000 start / K 32) over per-episode per-seat scores; a policy climbs by returning
more across more seeds. `results.win[0]` is `totalReturn >= par` — a "did the cog clear the bar" flag,
not a duel — and **`results.winner` is `0` when `win[0]` is true and `null` otherwise**: there is no
opponent, so the only honest winner is the seat itself or nobody.

**Measured but never scored:** `bestX`, `stagePeakSpeed`, `stageStrides`, `saturatedTicks`,
`airborneTicks`, `footstrikes`, `ordersRepaired`, `fallbackTurns`. All are in `results`, on the endcard
and in the feed.

**Integrity (the idea's note), decided.** *Seeded initial states*: the episode `seed` is randomised by
the runner, **never appears in any observation or prompt**, and every start pose is a pure hash of
`(seed, stageIndex, jointIndex)` over a 2⁶⁴ seed space (§Sim module → Start pose and seeding).
*Replay verification by deterministic re-simulation*: the replay records only the per-turn orders, and
the viewer re-derives every tick by re-running the identical Nim sim compiled to wasm, checking the
per-tick `gameHash` and the per-48-tick state keyframe (§Sim module → Determinism, native ↔ wasm).

### End conditions and legal `results.reason` values

The episode ends at the first of: **the ladder finishing**, the **turn cap**, the **wall-clock stop**, or
a **fault**.

`results.reason` is the starter's closed enum; **exactly these three values are legal** and the game
emits nothing else:

- **`complete`** — the episode finished on its own terms. `results.endRule` says which:
  - `ladderComplete` — all three stages resolved (`lined`, `ran` or `fell`) and the last reset hold
    elapsed. The healthy value.
  - `turnCap` — `turnsPlayed == maxTurns` (42). Reachable only when every stage ran its full window, in
    which case it coincides with `ladderComplete`; it is kept as an independent guard so no arithmetic
    error can produce an unbounded loop.
- **`deadline`** — the wall clock reached `wallClockBudgetSeconds` (**690 s**). The engine stops at the
  current tick, settles with the **real** return so far (never zeroed, so a deadline episode is still
  rankable), marks every unstarted stage `stageOutcome = "unreached"` with zero distance, zero return
  and zero ticks, writes `results.json` and the replay, and exits 0. `results.endRule = "wallClock"`.
  **Declared acceptable** for `docs/SPEC.md` §Definition of done check 4 — it means the hosted LLM was
  slow, not that the game broke. The budget guard below exists so it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop, or the step-8 invariant guard tripping.
  Caught; the episode is settled from the last completed tick, `results.endRule = "fault"`,
  `results.stopDetail` names it (≤ 200 runes, rune-truncated), artifacts are still written, exit 0. A
  defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

`results.endRule` is therefore a closed enum: **`ladderComplete | turnCap | wallClock | fault`**.
`results.stageOutcome[i]` is a closed enum: **`lined | ran | fell | unreached`**.

**Budget guard.** At the start of each command turn, if
`elapsed + 2 × (turnSpacingMs + turnBudgetMs) / 1000 > wallClockBudgetSeconds`, the LLM is switched off
for every remaining turn (the seat falls to `trotter`, microseconds per turn), the remaining stages
still play out at full speed, and the episode still ends `complete`. A `budget_guard` record names the
turn it fired (the starter's guard at `src/ctf/decide.nim:328-346`, kept).

**A silent seat does not end the episode.** A seat that never connects, disconnects mid-episode, or
fails every decision is driven by `trotter` and the ladder runs to its natural end with
`deadSeats[0] = true`. Nothing a player container does can stop the clock: the starter's
`lobbyJoinTimeoutTicks` bounds the lobby, and a silent seat cannot consume more than the per-turn
deadline.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes the seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {trotter, plodder}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=trotter` (the starter's "anything unrecognised is the published default" rule at
`src/ctf/baselines.nim`). **A scripted policy seated as a champion is a failure state**
(`playbooks/make-coworld.md` §Definition of done).

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/continuous-control/anthropic_api_key` — the
hive 2026-08-23 gotcha), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/continuous_control_player.nim` is `src/paintball_player.nim` forked with no behaviour change: read
`COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send — and
**re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join scar)
— the registration blob

```json
{"policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"trotter"|"plodder"|null}
```

with `prompt` rune-truncated at **`MaxPromptRunes` = 4000** and `policy` at **`MaxPolicyLabelRunes` =
48**, then acknowledge frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3
close-frame race: whisky's `receiveMessage` raises on a close frame and mummy's `send` only queues).

`src/cc/llm.nim` is `src/ctf/llm.nim`, forked with the identifier rename only:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION` / `AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (via `readCogameUri`) → **none**, in which case the
  client is `disabled = true` and every turn falls back instantly with no network wait, so offline
  certification finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429. The `throttled` fast-fail that
  skips the retry when the provider answered 429 with no other candidate is kept verbatim.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900` (not 400 — "cut off at max_tokens"). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`. No `temperature`.
- A system prompt demanding the reply **begins with `{`**, and the assistant turn is **prefilled with
  `{`** (both Anthropic Messages and Bedrock invoke accept it; the prefill is re-prefixed before parsing
  and a provider that echoes it is guarded) — the procgen 0.1.2 `cut off at max_tokens` fix, taken from
  day one rather than after the fact.
- `extractJsonObject` (`src/ctf/directives.nim:102` — outermost balanced `{…}`, fence-tolerant, tolerant
  of trailing prose) and `truncateRunes` / `sanitizeSay` / `sanitizeNote`
  (`src/ctf/directives.nim:61-90`) unchanged.

### Cadence, the per-turn call budget, and the wall-clock arithmetic

One command turn every 36 ticks; **at most 42 turns per episode**. **The per-turn LLM call budget is
exactly ONE request, plus at most ONE retry** — there is a single seat, so the starter's
**one-parallel-batch-per-turn** machinery (`src/ctf/decide.nim:427`) carries a batch of one and is
otherwise untouched; seats are never queried sequentially because there is only one. **At most
`42 × 2 = 84` provider calls per episode**, never more than one in flight.

```
attempt1Ms                          6.0 s   (whole seconds - sim_config.nim:696-706 rejects otherwise)
retryMs                             3.0 s   (whole seconds; attempt1Ms + retryMs <= turnBudgetMs - :691)
turnBudgetMs                        9.0 s   (monotonic deadline around the whole turn)
turnSpacingMs                       2.6 s   -> 1 seat x 60/2.6 = 23 req/min  (sidecar cap: 30)

42 turns x max(spacing 2.6 s, latency ~3.4 s)  typical            = 143 s
42 turns x turnBudgetMs 9.0 s, absolute worst                     = 378 s
1512 ticks x 10 substeps x 12 iterations of integer solver        =   3 s   (worst; ~0.6 s typical)
lobby / connect wait (lobbyJoinTimeoutTicks 2400 = 100 s at       =  15 s   (cap: 100 s)
   TargetFps 24; typical 15 s)
gameOverTicks hold + results + replay write (retried uploader)    =  20 s
                                                                  -------
typical total                                                     = 179 s   < 720 s
absolute worst case (378 + 3 + 100 + 20)                          = 501 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                           = 690 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                             = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 690 and `tests/test_cc_manifest.nim` asserts it. The typical figure is
conservative: a stage that falls early ends the episode sooner, and a fall costs turns.

**Rate guard.** `turnSpacingMs` pins the steady state at 23 req/min, but a run of retrying turns issues
two requests each. The engine therefore keeps a **rolling 60 s request counter**: if issuing the next
request would push the trailing-60 s count above **28**, that turn skips the call and takes the
`trotter` order with `cause = "rate_guard"`. Bounded, logged, never a sleep on the episode's critical
path (the raid round 2 sidecar-throttle scar).

### Degrade, never hang

Every wait is bounded: the two request deadlines, the outer `turnBudgetMs`, the rate guard, the fixed
`SubstepsPerTick × SolverIterations` (there is no convergence loop anywhere in the solver — it is a
fixed 120 passes per tick and it terminates whether or not it has converged), `lobbyJoinTimeoutTicks`,
mummy's socket timeouts on the serve thread (which runs independently of the game loop, so a 9 s LLM
stall cannot drop a connection or stall `/healthz`), the 690 s engine stop, and ctf's `gameOverTicks`
hold before exit — kept so `/healthz` and `/global` keep answering for a bounded grace after artifacts
are written (the lantern 0.1.3 `/global` ping scar).

On the seat's timeout or parse failure: **retry once**; on the second failure that turn's order becomes
the **`trotter`** scripted order computed inside the game (the same proc the `trotter` baseline uses —
imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns` counts them. The attempt-1 notice says **`will retry`**; only a
genuine second failure logs **`falling back`** (the pommerman 0.1.1 phase-60 grep scar; the starter's
two phrasings live at `src/ctf/decide.nim:463` and `:491`).

**No failure mode leaves the body uncommanded.** The driver always has an order: this turn's, else last
turn's, else `trotter`'s. **The episode settles early rather than overrunning**: a stage ends the moment
it falls or crosses the line, the ladder ends the moment its third stage's reset elapses, and the budget
guard drops the seat to scripted play the moment two more full turns would not fit. A seat that never
connects is reported once to `COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload —
exactly `{"message", "failed_policy_index"}`, nothing else.

### Per-seat observation: exactly what is visible and what is hidden

**This is a proprioceptive, perfect-information control problem and the note keeps it that way.** The
cog sees its whole body, its whole track position and its own return. There is no fog, no partial view
and no hidden dynamical state; the difficulty is entirely *tuning a gait under a body it did not
choose*, which is what the idea's "continuous joint torques from proprioceptive state" describes.
Hiding the reward would make this the only reinforcement-learning environment on the site that does not
tell the agent its reward.

**Visible.**

- **The rules of the world, once, at registration**: `turnTicks`, `stageTicks`, the track length, the
  six gait names, the five order knobs and their ranges, the scoring constants for each morphology, and
  the fall test for the current body. Static; afterwards referred to by id.
- **The body**: `links` and `joints` counts, and per joint its name, current angle, angular rate, its
  limits, the percentage of its torque cap the servo used last tick, and whether it saturated. Per foot:
  whether it is on the ground, its x, and its slip speed.
- **The torso**: height, pitch, forward and vertical velocity, spin rate.
- **The track**: length, current x, best x this stage, distance to the line.
- **The order in force**, with the resolved stride frequency and the current stride phase percent — so a
  policy can time a `phase_shift`.
- **Its own last turn**: distance gained, mean forward speed, strides completed, peak torque percent,
  saturated ticks, airborne ticks, whether it fell, the return delta, and `notes` echoed back.
- **Its own progress**: the whole ladder with each resolved stage's morph, outcome, distance and return;
  the running total return; and `par`.

**Hidden.** The episode **seed**; the per-joint start perturbation of any stage that has not started;
the **gait table's raw amplitude / phase / trim constants** (a policy learns what `run` at cadence 70
does by doing it, not by reciting a table — reciting it would make the game a memorisation exercise);
the servo gains; and the agent's own **real player/policy name**. Nothing about identity ever reaches a
prompt.

The observation is a JSON object appended to the user message, and is mirrored (minus `notes`) into the
replay's `order` record, so the replay explains every decision.

```json
{
  "you": "Alpha",
  "turn": 10, "of": 42, "tick": 357,
  "stage": {"index": 2, "of": 3, "morph": "cheetah",
            "tick": 108, "of_ticks": 468, "turns_left": 10,
            "terminates_on_fall": false,
            "points_per_metre": 0.5, "upright_points_per_second": 0.0},
  "track": {"length_m": 60.0, "x_m": 14.82, "best_x_m": 14.82, "to_line_m": 45.18},
  "body": {"links": 7, "joints": 6,
           "torso": {"height_m": 0.63, "pitch_deg": -8.4,
                     "vx_m_s": 5.31, "vy_m_s": 0.12, "spin_dps": -31.0},
           "joints": [{"j": 0, "name": "back_hip",   "angle_deg": -22.4, "rate_dps": -190.0,
                       "limit_deg": [-30.0, 60.0], "torque_pct": 74, "saturated": false},
                      {"j": 1, "name": "back_knee",  "angle_deg":  11.9, "rate_dps":  242.0,
                       "limit_deg": [-45.0, 45.0], "torque_pct": 88, "saturated": false},
                      {"j": 2, "name": "back_ankle", "angle_deg":  -6.2, "rate_dps":  -41.0,
                       "limit_deg": [-23.0, 45.0], "torque_pct": 31, "saturated": false},
                      {"j": 3, "name": "front_hip",  "angle_deg":  18.0, "rate_dps":  155.0,
                       "limit_deg": [-57.0, 40.0], "torque_pct": 61, "saturated": false},
                      {"j": 4, "name": "front_knee", "angle_deg": -30.7, "rate_dps": -118.0,
                       "limit_deg": [-69.0, 50.0], "torque_pct": 100, "saturated": true},
                      {"j": 5, "name": "front_ankle","angle_deg":   2.1, "rate_dps":   12.0,
                       "limit_deg": [-29.0, 29.0], "torque_pct": 19, "saturated": false}],
           "feet": [{"f": 0, "name": "back_foot",  "on_ground": true,  "x_m": 14.35, "slip_m_s": 0.08},
                    {"f": 1, "name": "front_foot", "on_ground": false, "x_m": 15.44, "slip_m_s": 0.00}]},
  "gait_now": {"gait": "run", "cadence": 68, "power": 80, "lean": 10,
               "stride_bias": 0, "phase_shift": 0,
               "stride_hz": 2.36, "cycle_pct": 41, "source": "llm"},
  "last_turn": {"distance_m": 7.62, "mean_vx_m_s": 5.08, "strides": 3.5,
                "peak_torque_pct": 100, "saturated_ticks": 11, "airborne_ticks": 6,
                "fell": false, "return_delta": 3.81, "repaired": 0,
                "notes": "cadence 68 is holding the gallop; front knee is pegged - try power 72"},
  "gaits": ["stand", "crouch", "walk", "run", "bound", "brake"],
  "ladder": [{"i": 0, "morph": "hopper",  "outcome": "fell",    "distance_m": 6.11, "return": 12.99},
             {"i": 1, "morph": "cheetah", "outcome": "running"},
             {"i": 2, "morph": "walker",  "outcome": "pending"}],
  "totals": {"return": 20.35, "par": 40.0, "max": 243.744},
  "rules": {"cadence": "0-100 -> stride frequency 0.80-4.00 Hz for this body",
            "power": "0-100 -> joint amplitude and torque ceiling (ceiling = 40% + 60% x power)",
            "lean": "-50..+50 -> pitch the whole body back / forward",
            "stride_bias": "-50..+50 -> shift amplitude from the back leg to the front leg",
            "phase_shift": "-50..+50 -> advance / retard the stride phase, in percent of one cycle",
            "fall": "this body cannot fall; it just scores badly on its back",
            "order_lasts": "36 ticks (1.5 s), executed 240 times a second by the driver"}
}
```

Field shapes never change: `joints` and `feet` always have exactly the current morphology's counts,
`gaits` is always the six names in that order, `ladder` always has exactly three entries.
`tests/test_cc_obs.nim` asserts the observation reconstructs from the sim state and that nothing hidden
appears in it (§Tests 26-28).

### Reply schema and per-field caps

```json
{"gait": "run", "cadence": 72, "power": 85, "lean": 12, "stride_bias": -6, "phase_shift": 0,
 "say": "lengthening the stride now the cheetah is up to speed",
 "notes": "run/72/85/+12 holds the gallop. front knee saturates above power 88 - do not go there. on the walker start at walk/45/60 and only ramp once both feet have struck."}
```

| Field | Type | Cap / domain | When violated |
|---|---|---|---|
| `gait` | string | **≤ 8 runes**; closed enum `stand`, `crouch`, `walk`, `run`, `bound`, `brake`, matched case-insensitively and whitespace-trimmed; synonyms accepted: `sprint`/`gallop`/`trot` → `run`, `hop`/`leap` → `bound`, `stop`/`halt` → `brake`, `idle`/`hold` → `stand` | unrecognised or missing → **last turn's gait**, else `walk` on the stage's first turn |
| `cadence` | integer | **clamped 0 … 100**; numeric strings accepted | missing/non-finite → last turn's value, else 50 |
| `power` | integer | **clamped 0 … 100** | missing/non-finite → last turn's value, else 60 |
| `lean` | integer | **clamped −50 … +50** | missing/non-finite → last turn's value, else 0 |
| `stride_bias` | integer | **clamped −50 … +50** | missing/non-finite → last turn's value, else 0 |
| `phase_shift` | integer | **clamped −50 … +50** (percent of one stride cycle) | missing/non-finite → 0 (it is a one-shot nudge, never inherited) |
| `say` | string | **≤ 140 runes** (`MaxSayRunes`) — the cog thinking out loud; drawn in the spectator feed and in the replay, never fed back to the seat | truncated on rune boundaries |
| `notes` | string | **≤ 320 runes** (`MaxNoteRunes`) — private scratchpad, echoed to this seat only next turn | truncated on rune boundaries |
| whole reply | bytes | **≤ 4096** read from the provider before parsing | over-long → parse failure → retry |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration | truncated, never rejected |
| `register.policy` | string | **≤ 48 runes** (`MaxPolicyLabelRunes`) | truncated |
| `fallback.detail`, `results.stopDetail` | string | **≤ 200 runes** | truncated |

`MaxSayRunes` and `MaxNoteRunes` are **re-pinned in this fork**: the starter has
`MaxSayRunes = ShoutMaxChars = 10` and `MaxNoteRunes = 160` (`src/ctf/sim_types.nim:772`, `:819-820`), a
10-character in-world shout and a short note. A cog narrating a gait needs a sentence and a cog carrying
"do not exceed power 88 on this body" between turns needs more than 160 runes, so `MaxSayRunes = 140`
and `MaxNoteRunes = 320` here, and `ShoutMaxChars` is deleted with the shout mechanic (§Sim module →
Deleted).

**Every string that lands in the replay — `say`, `notes`, the policy label, `stopDetail`, recorded error
text — is truncated on RUNE boundaries** via the starter's `truncateRunes` / `runeSubStr`
(`src/ctf/directives.nim:61-68`), never by byte index. Byte truncation is what makes a replay that
renders in a browser fail a strict UTF-8 parser; `tests/test_cc_replay.nim` asserts it with 4-byte emoji
sitting exactly on every cap.

**Parsing is tolerant**, and every repair is counted in `ordersRepaired` and reported back next turn:
strip markdown fences; take the outermost balanced `{…}`; accept numeric strings; accept a percentage
`0..100` for `lean`/`stride_bias`/`phase_shift` given as `-1.0..1.0` and multiply by 50; accept
`cadence` given in Hz when the value is a decimal below 6 and map it onto the morphology's range; accept
unknown top-level keys by ignoring them. A reply with a valid `say` but no usable order field is
**usable** — last turn's order continues and the narration is delivered. A reply that is not a JSON
object is a parse failure. **Out-of-range numbers are clamped, never dropped**: unlike an irreversible
push in Sokoban, a clamped `power` is a faithful reading of "as hard as possible".

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are ONE cog driving ONE machine down a flat 60-metre track, seen from the
side. x runs right (forward), y runs up. You get THREE machines in one episode,
one after the other, 19.5 seconds each, and your score is the RETURN: metres
covered, plus a small bonus per second upright, minus a small cost for slamming
the joints. Higher is better. It can go negative.

THE MACHINES
  HOPPER  4 links, 3 joints, ONE leg. Falls if the torso drops below 0.70 m or
          pitches past 20 degrees. Worth 2.00 points per metre.
  CHEETAH 7 links, 6 joints, two legs, long body. CANNOT fall - there is no
          upright to lose. Worth 0.50 points per metre, so it has to go far.
  WALKER  7 links, 6 joints, two legs, upright torso. Falls below 0.80 m or
          past 57 degrees of pitch. Worth 1.50 points per metre.
Each machine is worth about twenty points to a competent run. None of them
dominates the episode.

WHAT YOU SEND, EVERY 1.5 SECONDS
One JSON object: a GAIT and five numbers. A deterministic pattern generator in
the game runs your order 240 times a second on every joint until your next
order. You are not sending torques; you are tuning the machine that sends them.
  "gait"         stand | crouch | walk | run | bound | brake
                 stand  = neutral pose, no stride. Settle here.
                 crouch = low pose, no stride. Plant the feet before you move.
                 walk   = long slow stride, both feet down often. Stable.
                 run    = short fast stride. The workhorse.
                 bound  = big amplitude, big air, big risk. Hoppers live here.
                 brake  = amplitude zero and heavy damping. Kills speed and
                          usually saves a fall.
  "cadence"      0-100. Stride frequency. High cadence with a heavy machine
                 means the feet never load; low cadence means you never move.
  "power"        0-100. Scales BOTH the joint amplitude and the torque ceiling.
                 Power costs score, and a saturated joint tracks nothing.
  "lean"         -50..+50. Pitch the whole body. Positive is forward. Forward
                 lean is how you accelerate and how you fall over.
  "stride_bias"  -50..+50. Shifts amplitude from the back leg to the front leg.
                 0 on a hopper. Small values on a walker fix a limp.
  "phase_shift"  -50..+50. Percent of one stride cycle. A ONE-OFF nudge so a
                 new gait starts on the correct foot instead of mid-air.
  "say"          <=140 chars, spectators only.
  "notes"        <=320 chars, echoed back to you next turn. Nobody else sees it.

WHAT YOU GET BACK
Every joint's angle, rate, limits and how much of its torque ceiling the servo
just used ("torque_pct", and "saturated" when it is pegged). Every foot's
ground contact and slip. Torso height, pitch, forward speed. Your x on the
track. What your LAST order actually achieved: distance, mean speed, strides,
peak torque, saturated ticks, airborne ticks, and whether you fell.

READ THOSE NUMBERS. They are the whole game:
  saturated joints          -> your power is too high for this cadence.
  slip above ~0.5 m/s       -> the foot is skating; lower cadence or power.
  airborne_ticks near 36    -> you are launching, not running.
  distance_m near zero with -> you are marching on the spot; add lean.
    high strides
  pitch heading toward the fall limit -> brake for one turn, then resume.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the
character { and end with }. No prose, no markdown, no code fences.
{"gait":"run","cadence":72,"power":85,"lean":12,"stride_bias":0,"phase_shift":0,"say":"<=140 chars","notes":"<=320 chars"}
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(paintbot's `operatorBlock`, kept), a blank line, then the observation JSON above. The prompt text is
never echoed into the replay — only `policyKind`, the label and the resulting order.

### Champion #1 — `continuous-control-gaitsmith` (owner **daveey**), `PLAYER_PROMPT`

```
Tune, do not thrash. Every machine has one cadence/power pair that works, and
your job is to find it in two turns and then hold it.
TURN 1 OF EVERY STAGE, always the same: {"gait":"crouch","cadence":0,
"power":45,"lean":0}. You get the feet planted, you see the joint limits and
the real torque numbers, and you lose at most one and a half seconds. A machine
that starts running before it has stood up falls before it moves.
TURN 2: start conservative and identical for every body -
{"gait":"walk","cadence":45,"power":60,"lean":6}. Read what comes back.
THEN, every turn, apply these corrections IN THIS ORDER and change ONE thing:
1. If last_turn.fell is impossible for this body, skip to 3. Otherwise, if
   torso pitch_deg is within 6 degrees of the fall limit, send
   {"gait":"brake","cadence":30,"power":50,"lean":-10} for exactly one turn.
   Nothing else. Then resume the gait you had, minus 10 lean.
2. If any joint reports saturated true, drop power by 12. A pegged joint is not
   producing more force, it is producing more cost.
3. If a foot reports slip_m_s above 0.5, drop cadence by 8. The foot is
   skating and every skating stride is distance you did not get.
4. If distance_m for the last turn is under 0.6 m and strides is above 2, you
   are running on the spot: add 8 lean, up to +30.
5. Otherwise, if nothing above fired, add 5 cadence, up to the point where rule
   3 fires. Then stop and hold.
Gait selection: hopper -> bound once cadence is above 55, walk below it.
Cheetah -> run always, and stride_bias +6 (its front leg is the weak one).
Walker -> walk until mean_vx_m_s passes 1.2, then run.
Never send power above 90 on any body. Never send lean above +30 on a walker.
Use phase_shift only on the turn you change gait, and only 25 or -25.
When to_line_m is under 4 m, add 10 lean and 10 power and take the line.
```

### Champion #2 — `continuous-control-throttle` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Distance is the only thing that pays. Upright bonus is under two points a
stage and control cost is under half a point; metres are twenty. So the plan is
always: reach the fastest gait this body will survive, as early as possible,
and stay in it.
Open every stage with {"gait":"walk","cadence":55,"power":75,"lean":10} - one
turn, not two. On the cheetah open with {"gait":"run","cadence":65,"power":85,
"lean":14} instead, because the cheetah cannot fall and every cautious turn on
it is two metres thrown away.
Then RAMP. Each turn add 6 cadence and 5 power, up to cadence 88 and power 88,
until one of these three stops you:
  - a joint reports saturated: hold power where it is and keep ramping cadence.
  - a foot slips above 0.7 m/s: hold cadence where it is and keep ramping power.
  - the last turn's distance went DOWN: you have passed the peak. Step both
    back to the previous turn's values and hold them for the rest of the stage.
Falls: on the hopper and the walker only, if pitch_deg is within 4 degrees of
the limit OR torso height is within 0.05 m of the floor, send exactly
{"gait":"brake","cadence":20,"power":40,"lean":-15} once, then come back at the
values you had minus 6 cadence. Do not brake twice in a row - two brakes in a
row is a policy that has stopped racing.
Say the numbers out loud in "say" so a spectator can follow the ramp, e.g.
"cadence 74 power 83, front foot holding". Keep the last working pair in
"notes" so a fallback turn does not lose it.
Never send stand. Never send crouch after the first turn of a stage. Never let
power exceed cadence by more than 25 - that combination saturates every joint
on every body in this game.
```

### The driver (deterministic, integer-only, shared by every policy)

`src/cc/driver.nim`. **Unlike the starter's `src/ctf/control.nim`, this driver sits INSIDE the
determinism boundary**: it is integer-only, it is hashed, and it is re-run identically in the browser.
That is the one structural change this fork makes to ctf's architecture, and the reason is arithmetic —
the action here is one order per 36 ticks (42 records, ~8 KB) rather than one byte per tick, so
re-deriving the per-tick targets is what keeps the replay at 30 KB instead of 1 MB.

Per tick, for every joint `j` of the current morphology `m`, with `g` = the order's gait row from
`GaitTable[m][gait]`:

```
1.  cycle  = (cyclePos + phase_shift * 10_000 + g.phaseMicro[j]) mod 1_000_000
2.  sideScale[j] = 100 + stride_bias * sideSign[m][j]        # sideSign is -1 on the
                                                              # back/right leg, +1 on the
                                                              # front/left leg, 0 on the torso
3.  ampNow[j]    = g.ampQ16[j] * power div 100 * sideScale[j] div 100
4.  leanNow[j]   = g.leanQ16[j] * lean div 50
5.  target[j]    = g.trimQ16[j] + leanNow[j]
                 + mulQ(ampNow[j], sinQ16(cycle * TwoPiQ16 div 1_000_000))
6.  target[j]    = clamp(target[j], limitLo[m][j], limitHi[m][j])
```

`sinQ16` is the committed table. Every operation is `int64` with `div`, never `shr`. The PD servo of
resolution step 4.2 then tracks `target[j]` at 240 Hz with the swept gains — **that** is where the
continuous torque lives.

`GaitTable` is `array[3, array[6, GaitRow]]` where a `GaitRow` is `(ampQ16, phaseMicro, trimQ16,
leanQ16: array[MaxJoints, int32])` — 3 morphologies × 6 gaits × 4 arrays. `stand` and `crouch` have all
amplitudes zero and differ only in trim; `brake` has all amplitudes zero, a `crouch` trim, and sets
`Kp := 0`, `Kd := KdBrake[m]` so the servo is pure damping. **The table's numbers are a swept parameter
set, not literals guessed in a design note**: `tools/tune_gaits.nim` sweeps `(amp, phase, trim, lean,
Kp, Kd)` per morphology over a bounded grid, scoring each candidate by the distance the *driver alone*
covers in one stage at cadence 60 / power 70 with no policy input; `tools/ci/gait_tuning.json` records
the sweep's pick; `tests/test_cc_tuning.nim` asserts the shipped `GaitTable` and gains still equal it,
and `ci.yml` re-runs the sweep with `--check`. This is exactly the starter's `DefaultBaselineParams`
discipline (`src/ctf/baselines.nim`) applied to a bigger table. **The morphology, solver and scoring
constants in §The game are NOT swept and are NOT tunable** — if the sweep cannot make a body walk, the
sweep changes the gait table, never the physics.

The driver never invents a value the schema does not express and holds **no memory across ticks except
`cyclePos`**, which is hashed.

### Scripted baselines (both shipped as league fillers; `trotter` is also the server-side fallback)

`src/cc/baselines.nim`, the starter's module retargeted. Both emit the **same** order objects an LLM
does, through the same validator, which is what makes the bounded-orders test meaningful. Neither ever
emits `say` or `notes` — a baseline that narrated would make the feed lie about which seats are LLMs.

**`trotter`** — `PLAYER_SCRIPTED=trotter`, the certification player, and the server-side fallback.
Evaluated once per turn from the same observation an LLM would receive:

1. If `stageTick < settleTicks` (**24**) → `{gait: crouch, cadence: 0, power: 40, lean: 0, stride_bias: 0, phase_shift: 0}`.
2. Else if the morph can fall **and** `|pitch|` is above `0.6 ×` the fall limit, or the torso height is
   within 0.06 m of the low limit → `{gait: brake, cadence: 25, power: 45, lean: −12}` for one turn.
3. Else if `mean_vx` is below `0.5 × targetVx[m]` → `{gait: run, cadence: rampCadence[m], power: 90,
   lean: 14, stride_bias: biasFor[m]}`.
4. Else → `{gait: run, cadence: cruiseCadence[m], power: cruisePower[m], lean: 8, stride_bias:
   biasFor[m]}`.
5. `phase_shift` is 0 except on the turn the gait changes, where it is `25`.

**`plodder`** — `PLAYER_SCRIPTED=plodder`. The floor, and the answer to "did the champion actually
tune?": `{gait: walk, cadence: 40, power: 55, lean: 4, stride_bias: 0, phase_shift: 0}` every turn, with
rule 2 above at a wider threshold (`0.8 ×` the limit) and **no ramp and no cruise**. It almost never
falls and it almost never gets anywhere, which is exactly the floor this benchmark needs.

The six tunables — `settleTicks`, `targetVx[m]`, `rampCadence[m]`, `cruiseCadence[m]`, `cruisePower[m]`,
`biasFor[m]` — are a `BaselineParams` object, not literals, swept by `tools/tune_baselines.nim` and
pinned in `tools/ci/baseline_tuning.json` (§Tests 25).

**Baseline strength, pinned as a band** by `tests/test_cc_baselines.nim` over 100 seeds, so that neither
a zero floor nor a superhuman filler can ship: `trotter` covers **6–14 m** on the hopper, **30–58 m** on
the cheetah and **11–24 m** on the walker, and falls on **at most one** of the three stages on ≥ 80 % of
seeds; `plodder` is strictly shorter than `trotter` on every morphology on ≥ 90 % of seeds and still
returns a non-negative episode total. `trotter` therefore scores roughly 30–55 on `ladder`, straddling
`par = 40`, which is what makes `par` a meaningful bar rather than a rubber stamp.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/cc/`. The fork is a rename sweep
(`ctf` → `cc`, `CTF_WIRE` → `CC_WIRE`; a CI grep asserts no `ctf_` / `CTF_` identifier survives outside
comment history) plus the changes below. **The same modules compile twice**: natively into
`/bin/continuous-control` for the server, and to wasm32 through `replay-viewer/config.nims`
(`switch("path", rootDir / "src")`) for the viewer — which is the whole reason the game lives in the
starter's language and the whole reason vendoring MuJoCo, `dm_control` or Brax is not an option here.

### Start pose and seeding

At the first tick of stage `k` with morphology `m`:

1. Every link is placed from `NeutralPose[m]` — a committed table of per-joint angles that puts the body
   standing (hopper and walker) or lying prone on all four feet (cheetah), with the lowest contact point
   exactly on `y = 0` and `torso.x = 0`.
2. Every joint angle is offset by
   `perturb(j) = (mix64(seed, k, j) mod (2 · InitPerturb + 1)) − InitPerturb`, with
   `InitPerturb = 0.05 rad` in Q16 and `mix64` a splitmix64 over the mixed words — **a pure hash, never a
   consumed stream**. The link positions are then re-derived forward down the kinematic chain from the
   torso so the joints are exactly satisfied at `t = 0` (the solver never has to fix a broken start
   state).
3. The body is dropped: every velocity is zero and gravity does the rest.
4. `cyclePos := 0`; `xStart := torso.x`; `bestX := torso.x`; the per-stage counters are zeroed.

**Every start pose is therefore a pure function of `(seed, stageIndex)`.** Nothing the policy does can
shift a draw, reorder draws, or consume one out from under a later stage: **stage `k`'s start is
identical no matter what happened in stage `k − 1`**, which is what makes per-morphology distances
comparable across policies, and it is what the idea's "seeded initial states" asks for. The seed is
randomised by the runner in `src/continuous_control.nim` **before `config.update`** (the starter's rule),
recorded in the replay config and in `results.seed`, and **never disclosed to the seat**.
`tests/test_cc_seeding.nim` asserts it by starting every stage of every variant under three different
policy behaviours and comparing the poses Q16 word for word.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/cc/server.nim` | **fork**, three named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the `wallClockBudgetSeconds` stop at `server.nim:1438-1448`, and the `Ping → Pong` branch in `websocketHandler` (lost twice in this fleet — lux-ai 0.1.0, snake-royale 0.1.0 — and guarded by nothing else) |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/cc/` | **fork** (magic + game name + one new record kind: `CtfReplayMagic = "COWLDCTF"` (`replays.nim:142`) → **`CcReplayMagic = "COWLDCCL"`**, plus the state-keyframe record) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim` → `src/cc/` | **fork**, retargeted not rewritten | the per-turn batch (`decide.nim:427`), the two deadlines, `turnSpacingMs` (`:386-389`), the budget guard (`:328-346`), tolerant parsing (`directives.nim:102`), the rune caps, the fallback ladder and its two log phrasings (`decide.nim:463`, `:491`) |
| `src/ctf/control.nim` → `src/cc/driver.nim` | **fork, and moved INSIDE the hash boundary** | directive → per-tick actuation; rewritten in integers (§Decisions → the driver) |
| `src/ctf/sim_state.nim` → `src/cc/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby` |
| `src/ctf/roster.nim` → `src/cc/roster.nim` | **fork**, two named edits below | join/auth/identities/`IdentityNames` (`roster.nim:64-65`), the results JSON builder (`squadResultsJson`, `roster.nim:672`) |
| `src/ctf/events.nim` → `src/cc/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; new `SimEventKind` values only |
| `src/ctf/broadcast.nim` → `src/cc/broadcast.nim` | **fork** | `stepEvents`, `buildStateJson` (`broadcast.nim:838`, whose ctf key names `t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events` at `:866-892` are **kept exactly** so the byte-identical `chrome_common.js` runs unmodified), `rosterJson`, the lull scan, the beat timeline |
| `src/ctf/global.nim` → `src/cc/global.nim` | **fork**, three named edits below | the sprite/object pools, the compositor, the FX families, `boardRenderScaleFor` / `predictedViewerRenderBytes` / `MaxSupersampledMapPixels` / `WasmViewerBudgetBytes` (`:1095-1151`) all **unchanged** |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/cc/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"`, with the prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps = 24` (`:401`), `ReplayFps = 24` (`:342`), the flatty wire types (field order sacred), and the re-pinned `MaxSayRunes = 140`, `MaxNoteRunes = 320`, `MaxPolicyLabelRunes = 48`, `MaxPromptRunes = 4000` |
| `src/ctf/sim_config.nim` → `src/cc/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, and the validators at `:688-713` (whole-second `attempt1Ms`/`retryMs`, `attempt1Ms + retryMs ≤ turnBudgetMs`, positive `wallClockBudgetSeconds`) — all kept, and §Decisions' numbers satisfy them |
| `src/ctf.nim` → `src/continuous_control.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws follow the final seed |
| `src/paintball_player.nim` → `src/continuous_control_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte** (40 022 bytes, sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`) | §Viewer |
| `client/broadcast_core.js`, `replay_broadcast.html`, `league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/cc_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/tune_baselines.nim`, `nimby.lock`, `flake.nix`, `tests/config.nims` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix (line 21) and the safety check that refuses any output path that is not a `static-replay-viewer` directory inside the repo (lines 12-27); its `docker cp` source path changes from `/workspace/ctf/replay-viewer/dist/.` to `/workspace/cc/replay-viewer/dist/.` and `image_tag` is renamed |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/soldier_red.png`, `data/soldier_red_front.png`, `client/art/walls/{wall_h,wall_v}.jpg`, `client/art/lockerroom/{bg.jpg,red_*.webp}` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The hitscan gun and its jitter/exposure model, aim decoupling, vision cones, **fog-of-war raycasting and
the entire first-person raycast pipeline** (one body, side elevation, nothing to occlude), spray cans,
floor paint and the paint grid, the paint buff, King of the Hill and `hillTicks`, the
`resident`/`visitor` regimes, hearts/flags/capture/carriers, grenades and the barrage, med kits,
shields, cardboard barriers, trenches, perks, handicaps, lives and respawns, **teams and four-team
free-for-all** (there is one seat), **shouts-as-cog-speech and `ShoutMaxChars`**, achievements, campaign
mode, `maxGames > 1` side-swapping, and **all of the top-down map machinery**: `arena.nim`'s wall masks
and pixel queries, `map_art.nim`, `mapgen_styles.nim`, `map_pool.nim`, `paint.nim`, `tools/mapkit.nim`,
`tools/map_editor*.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim`, `docs/pool-review.html`,
`docs/MAPKIT.md`. The world here is a flat line and a camera; every one of those is a config surface the
physics would otherwise have to reason about.

Also deleted: the `data/` art belonging to deleted mechanics (`heart_*`, `ped_*`, `paintgun*`, `medkit`,
`shield`, `paintbomb`, `spraycan*`, `crew`, `*_crown`, `*_front_gun`, `soldier_{blue,green,yellow}*`,
`rig_real/`) and the blue/green/yellow locker-room webps — there is one machine and it is red.

### New modules

- `src/cc/trig.nim` — the committed `SinQ16Table`, `sinQ16` / `cosQ16` with integer quadrant reduction
  and linear interpolation, `wrapAngle`, and `mulQ` / `divQ`. No floats, no `shr`.
- `src/cc/body.nim` — the `Link` and `Joint` types, `MorphTable` (the three tables of §The game),
  `NeutralPose`, the inertia derivation, forward kinematics down the chain, the foot contact-point list,
  and the health test per morphology.
- `src/cc/solver.nim` — gravity, the servo, the three constraint families and the fixed
  `SubstepsPerTick × SolverIterations` loop of resolution step 4, plus the per-component clamps. This is
  the only file that touches constraint arithmetic.
- `src/cc/gaits.nim` — `GaitTable`, the six gait names as a closed enum, `sideSign`, `FreqMin`/`FreqMax`
  per morphology, and the loader for `tools/ci/gait_tuning.json`'s pinned values.
- `src/cc/driver.nim` — the six-step order → per-joint-target formula of §Decisions, integer only.
- `src/cc/report.nim` — the observation builder and the viewer packet builder. **The only module allowed
  to use `isqrtQ16` and the only module allowed to produce a decimal string**; it never writes hashed
  state, and a test asserts the sim compiles with it excluded.
- `src/cc/sim.nim` — the tick loop of §The game exactly as numbered, `gameHash`, stage and episode end
  evaluation, scoring, and the state-keyframe writer. Imports and re-exports the sim modules, as the
  starter's does, so `import cc/sim` sees everything.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDCCL`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, variant, `num_agents`, every rule constant, the full `MorphTable`,
   the full `GaitTable`, the solver constants, the scoring constants, `players[].name`, `slots[]`,
   `fastMode`), then the record stream — the join record, **one `stage` record per stage** carrying its
   morphology name and its seeded per-joint perturbation, **one `order` record per turn** (the only
   inputs this game has), **one `keyframe` record every 48 ticks and at every stage start**, chat records
   (`register` / `order` / `fallback` / `budget_guard` / `stop` / `result`) and **one `gameHash` per
   tick**.
2. **The physics is re-derived, not recorded.** The viewer re-runs the identical `src/cc/sim.nim` from
   the recorded orders. This is exactly the idea's own integrity clause — "replay verification by
   deterministic re-simulation" — implemented as the *only* way the viewer works, so a divergence cannot
   go unnoticed.
3. **State keyframes are both a seek index and a cross-check.** Every 48 ticks the full link state
   (`x, y, a, vx, vy, w` per link, Q16 `int32`-narrowed with a range assert) is recorded: 32 keyframes ×
   7 links × 6 × 4 B = **5.4 KB**. Seeking is then O(48 ticks) instead of O(t). At each keyframe the
   re-simulated state must equal the recorded one; if it does not, the viewer publishes `mismatchTick`,
   shows `#mmwarn`, and **resyncs from the recorded keyframe**, so a spectator always sees the run that
   actually happened rather than a divergent one.
4. `tools/build_replay_viewer.sh` builds `replay-viewer/cc_replay.nim` — which imports the **same**
   `src/cc/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
5. In the browser, `cc_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `cc_frame` re-steps
   the sim from the recorded orders and compares `sim.gameHash()` against the recorded hash **every
   tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and surfaced as
   `mismatchTick` in `#mmwarn`.
6. **`gameHash` mixes**, in this fixed order: `tick`, `phase`, `stageIndex`, `stageTick`, `resetTick`,
   `cyclePos`; then for every link in **link index order** its `x, y, a, vx, vy, w` as Q16 `int64`; then
   `xStart`, `bestX`, `uprightTicks`, `ctrlCostAccum`, `saturatedTicks`, `strideCount`; then the three
   `stageOutcome` codes and the three `stageReturnMicro` values; then `totalReturnMicro` and `falls`. It
   never mixes FX, feed text, `say`, `notes` or policy labels.
7. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact cannot
   be re-derived from sim state, so the stop is written as one record applied by the *same proc* on
   record and on playback, and `tests/test_cc_replay.nim` runs the record → re-derive check for **every**
   end reason (`ladderComplete`, `turnCap`, `wallClock`, `fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 1512 hashes + 3 stage records + ≤ 42 order records + 32 keyframes (5.4 KB) + ~60 chat
records + a ~9 KB config ≈ **32 KB**.

### Documented divergences (mirrored into `docs/PHYSICS.md`)

1. **No MuJoCo, no `dm_control`, no Brax/MJX, and no bit-exactness with any of them.** Decided as a
   scoping rail: MuJoCo is a C solver over a float state vector, `dm_control` is Python on top of it, and
   Brax/MJX is JAX. Embedding any of them means a simulator that cannot compile to wasm32, so the static
   replay viewer — a non-optional pin — would be impossible. No upstream code is vendored, no upstream
   numbers are claimed as reproduced, and **no score from this coworld is comparable to a published
   HalfCheetah, Hopper or Walker2d return.** What is reproduced is the *problem*: planar articulated
   locomotion from proprioceptive state, fixed-length stages, return as the score.
2. **A sequential-impulse solver with no warm starting, not MuJoCo's convex soft-contact solver.** 10
   substeps of 12 Gauss-Seidel iterations at 240 Hz, Baumgarte position bias, Coulomb friction with
   accumulated-impulse clamping, restitution 0. MuJoCo's contact model (soft, with a solver reference
   and impedance) is a different model and produces different gaits. Stated here so a reviewer does not
   read a difference as a bug.
3. **Three planar morphologies, not eight environments.** Hopper, HalfCheetah and Walker2d are the three
   Gymnasium MuJoCo tasks that are genuinely planar, and this repo implements that family. **Ant,
   Humanoid, Swimmer, quadruped, dog and every manipulation task are 3-D and are out of scope** (§Out of
   scope). The idea's headline names Humanoid and Ant; the ladder shipped here is the planar half of the
   same ladder, and `docs/PHYSICS.md` says so in the first paragraph.
4. **Masses, lengths, joint limits and torque caps are in the same structural family as the Gymnasium
   XMLs but are this repo's numbers.** They are printed in `docs/PHYSICS.md` and written into every
   replay's config JSON, so they are auditable; they are not claimed to be MuJoCo's.
5. **The action is a gait order every 36 ticks, not a torque vector every step.** The reason is the
   platform pin (§The idea's "no LLM path", resolved) and the arithmetic: 6 torques × 1512 ticks over an
   HTTP round trip is impossible inside a 720 s budget. The continuous torque is real — the PD servo
   produces one per joint per substep, 240 times a second — and its *parameters* are what the policy
   sets. `COGAME_EVENTS_URI`'s per-tick `Servo` rows carry the full torque trace for anyone who wants
   the RL-style action stream.
6. **Proprioception only; no pixel observations.** The DMC pixel variants are out of scope: a policy
   that receives frames needs a frame encoder in the player container, which is a different coworld.
7. **Reward shape.** Gymnasium's reward is `forward_reward_weight · ẋ + healthy_reward −
   ctrl_cost_weight · Σa²` per step. This repo uses the same three terms with the same signs and the same
   relative magnitudes, integrated over the stage, plus a per-morphology points-per-metre so that no one
   body dominates a three-body episode. All three underlying quantities are in `results`, so a
   per-morphology distance table is directly readable.
8. **Terminating stages: hopper and walker yes, cheetah no** — matching `Hopper-v5`, `Walker2d-v5` and
   `HalfCheetah-v5` respectively. The idea's "fixed-length episodes" is preserved as a fixed 42-turn
   *cap*; a fall shortens the episode because an episode that keeps paying for LLM turns after the body
   is on the floor wastes the wall-clock budget the platform kills you for.
9. **A 60 m finish line.** No Gymnasium locomotion task has one. It is added because it gives the
   spectator a goal line and the scoreboard a bounded maximum, and because "the cheetah lined out in
   17.4 s" is a headline. It is recorded in `stageOutcome` as `lined` and never confused with `ran`.
10. **`maxGames = 1`** — the starter's multi-game episode is not used; a ladder has no side to swap.

### The three named edits to `server.nim`

1. **Turn boundary** — unchanged in shape, with one seat in the batch and the stage lifecycle of
   resolution step 1.
2. **Registration interception** — the seat's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration, **not** applied as a shout and **not** written to the replay chat stream; the server
   writes a redacted `register` record instead (policy label and kind, never the prompt). The starter's
   "hold an unappliable registration and re-read it when the slot lands" behaviour is kept verbatim, and
   the server **logs loudly and refuses to start the game** when the joined seat has no register record
   (the grf-football 2026-08-27 silent-default scar). Any other chat text from the seat is dropped — the
   cog speaks through `say`.
3. **Wall-clock stop** — the starter's `wallClockBudgetSeconds` check at the top of every loop iteration
   (`server.nim:1438-1448`), kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wallClock`,
   and written as the load-bearing stop record of §Determinism point 7.

### The two named edits to `roster.nim`

1. **Alias.** `seatAlias(slot)` returns `IdentityNames[slot]` title-cased → **`Alpha`** for the only
   seat. The `IdentityNames` array itself (`roster.nim:64-65`) is unchanged. Board labels and the label
   manifest inherit the two-name-space rule with no further change, and `showPlayerLabels` is false.
2. **`squadResultsJson` → `ladderResultsJson`** (`roster.nim:672`) — one entry per seat, one entry in
   every seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **The board is a side-elevation camera viewport, not a top-down pixel arena.** The board bed is baked
   **once** at `MapWidth × MapHeight` covering 9.00 m of track, seamlessly tileable on a 1.50 m period,
   and the renderer draws it offset by `camX mod 1.50 m` — so the bake never changes, only its draw
   offset, and there is no per-frame map cost. The raycast fov cache and shadowcasting are **deleted
   outright** (perfect information; there is no fog layer at all).
2. **Link, foot and footprint pools.** New pools `LinkBase` (sized to 8 — the largest morphology plus
   one), `FootBase` (4), `FootprintBase` (64, a ring buffer of ground marks) and `DustBase`, filled in
   link index order and emitted incrementally like the starter's other object families, plus a per-stage
   static `MorphDef` packet sent once at `stagestart` carrying every link's `hl`, `r` and name.
3. **Baked track bed.** `arena_floor.png` is tiled and darkened at install with pixie, exactly the way
   the starter bakes endzone paint, and the dirt grain, the metre ticks and the 5-metre numerals are
   baked onto it once (§Viewer → Art) — one bake per episode, so the per-frame cost is the machine's 7
   links, 4 feet, the dust and the overlays.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST` / `PORT`; the player
socket at `/player?slot=0&token=<t>`. Protocol name **`continuous-control/v1`**.

The certifier's browser probes are served for real and registered **before** any catch-all asset route:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for
the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). The player
websocket handler **closes unless the token matches the seat** (the certifier probes with a bad token —
cogame-flatland 0.1.1), and `websocketHandler` keeps the starter's
`Ping → socket.send(message.data, Pong)` branch with **no** additional `kind` guard (a
`kind != TextMessage` guard drops the player's binary registration frames — lux-ai 0.1.0,
snake-royale 0.1.0). Global broadcasts are fire-and-forget so a slow viewer can never stall the episode.

### The per-seat stream

The seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates` — the machine, its links, its feet and the track. It carries
no board labels other than `ALPHA`, and `showPlayerLabels` is forced false on the player stream. The
seat sends **no inputs**: `fastMode: true` and the server computes every joint target, so the player
harness only acknowledges frames (`0x85` after every frame, exactly as `src/paintball_player.nim` does)
and the Sprite v1 Ready packet's dead-reckoning hazard cannot arise.

### Results document (closed schema; `ladderResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":             ["daveey"],
  "aliases":           ["Alpha"],
  "scores":            [61.948],
  "win":               [true],
  "winner":            0,
  "reason":            "complete",
  "endRule":           "ladderComplete",
  "variant":           "ladder",
  "seed":              1734029581,
  "stageCount":        3,
  "stageTicks":        468,
  "par":               40.0,
  "maxReturn":         243.744,
  "totalReturn":       61.948,
  "stageMorph":        ["hopper", "cheetah", "walker"],
  "stageOutcome":      ["fell", "ran", "ran"],
  "stageDistance":     [6.110, 45.281, 16.402],
  "stageReturn":       [12.994, 22.503, 26.451],
  "stageTicksRun":     [213, 468, 468],
  "stageTurns":        [7, 14, 14],
  "stageUprightTicks": [213, 0, 468],
  "stageCtrlCost":     [0.078, 0.138, 0.024],
  "stagePeakSpeed":    [3.42, 6.18, 2.77],
  "stageStrides":      [7, 41, 22],
  "stagesLined":       0,
  "distanceTotal":     67.793,
  "uprightTicksTotal": 681,
  "ctrlCostTotal":     0.240,
  "falls":             1,
  "saturatedTicks":    214,
  "finalTick":         1257,
  "turnsPlayed":       35,
  "ordersRepaired":    3,
  "policyKinds":       ["llm"],
  "llmTurns":          34,
  "fallbackTurns":     1,
  "deadSeats":         [false],
  "stopDetail":        ""
}
```

Seven identities hold in every results document and are asserted by `tests/test_cc_engine.nim`. The
worked numbers below are the example above, checked end to end.

1. **`finalTick == Σ (stageTicksRun[i] + resetTicks)`** over the stages that started —
   `(213 + 36) + (468 + 36) + (468 + 36) = 249 + 504 + 504 = 1257` ✓. Independently,
   `Σ stageTicksRun ≤ stageCount × stageTicks` (`1149 ≤ 1404`) ✓.
2. **`Σ stageTurns == turnsPlayed`** — turn boundaries are the global grid `t mod 36 == 0`, so stage 0
   owns the turns starting at ticks 0…216 (**7**), stage 1 those at 252…720 (**14**) and stage 2 those
   at 756…1224 (**14**): `7 + 14 + 14 = 35 == ceil(1257 / 36)` ✓.
3. **`stageOutcome[i] == "lined"` ⇔ `stageDistance[i] == 60.000`**, and
   `stageOutcome[i] == "unreached"` ⇔ `stageTicksRun[i] == 0 and stageReturn[i] == 0.0` ✓.
4. **`falls == count(stageOutcome[i] == "fell")`** — 1 ✓; `stagesLined == count(== "lined")` — 0 ✓.
5. **`distanceTotal == Σ stageDistance`** — `6.110 + 45.281 + 16.402 = 67.793` ✓;
   `uprightTicksTotal == Σ stageUprightTicks` — `213 + 0 + 468 = 681` ✓;
   `ctrlCostTotal == Σ stageCtrlCost` — `0.078 + 0.138 + 0.024 = 0.240` ✓.
6. **Every `stageReturn[i]` re-derives from the morphology's constants** —
   hopper: `2.00 × 6.110 + 0.004 × 213 − 0.078 = 12.220 + 0.852 − 0.078 = 12.994` ✓;
   cheetah: `0.50 × 45.281 + 0.000 × 0 − 0.138 = 22.641 − 0.138 = 22.503` ✓;
   walker: `1.50 × 16.402 + 0.004 × 468 − 0.024 = 24.603 + 1.872 − 0.024 = 26.451` ✓.
   And `totalReturn == Σ stageReturn` — `12.994 + 22.503 + 26.451 = 61.948` ✓.
   `tests/test_cc_scoring.nim` runs this re-derivation on every recorded episode.
7. **`scores[0] == round(totalReturn, 3)`** — `61.948` ✓; `win[0] == (totalReturn >= par)` —
   `61.948 ≥ 40.0` ✓; `winner == 0` when `win[0]` and `null` otherwise ✓.

`stageOutcome` is the closed enum `lined | ran | fell | unreached`; `stageMorph` is
`hopper | cheetah | walker`. Adding a key means updating `ladderResultsJson`, the manifest's
`results_schema` and `tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas
are closed and undeclared keys are dropped.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDCCL`** format — the static wasm viewer parses exactly this,
and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`, `static_replay_worker.js` and
`wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse (the knights-archers precedent).
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design (template line 31 / 319).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"continuous-control/v1","gameVersion":"1","seed":…,"variant":"…","names":[…],
  "aliases":[…],"policyKinds":[…],"tickCount":…,"stages":[…],"orders":[…],"says":[…],
  "fallbacks":N,"results":{…}}` — by brace-matching the config JSON from the first `{` (the technique the
  starter's `AGENTS.md` documents for prod forensics) and decoding the stage, order and chat records.
- **The phase-60 substitute for `docs/SPEC.md` §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule, .results.totalReturn' /tmp/ep.json
  jq -r '[.orders[]|select(.source=="llm")]|length, .fallbacks, (.says|length)' /tmp/ep.json
  jq -r '[.orders[]|.gait]|unique|length, ([.orders[]|.cadence]|unique|length)' /tmp/ep.json
  ```
  Require `protocol == "continuous-control/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.distanceTotal > 5`, and the champion seat's orders with
  `source == "llm"`, **more than one distinct `gait` and more than three distinct `cadence` values**
  (a constant order is a policy that is not playing), and non-empty `say` lines — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDCCL`, format version, `gameName` `continuous-control`, `gameVersion` `1` |
| config JSON | `seed`, `variant`, `num_agents`, `stagesPerEpisode`, `stageLadder`, `stageTicks`, `resetTicks`, `turnTicks`, `maxTurns`, `maxTicks`, `par`, `maxReturn`, the whole `MorphTable` (every link's `hl`/`r`/`m`/name and every joint's parent/child/limits/`τmax`/name), the whole `GaitTable`, `FreqMin`/`FreqMax`, the servo gains, every solver constant of §Solver constants, the scoring constants (`DistNum`/`DistDen`/`UprightPerTick` per morphology, the control-cost divisor), `TrackLineX`, `StateKeyframeTicks`, `players[].name` (**real name**), `slots[]`, `fastMode` |
| join | the seat's `name` (real policy name), `slot`, `token` |
| stages | per stage: `morph`, the seeded per-joint perturbation, the start tick |
| orders | per turn: the **clamped** order — this game's entire input log |
| keyframes | every 48 ticks and at every stage start: the full link state |
| chats | `register` / `order` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `slot`, `alias`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `order` | `turn`, `stage`, `slot`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `gait`, `cadence`, `power`, `lean`, `stride_bias`, `phase_shift`, `repaired`, `say` (≤ 140 runes), `view` (the observation minus `notes`) |
| `fallback` | `turn`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. **A closed
enum of ten kinds, plus `end`:**

`stagestart` `{i, morph, links, joints, terminatesOnFall}`; `turn` `{n, stage, stageTurn}`;
`order` `{n, gait, cadence, power, lean, stride_bias, phase_shift, source, repaired}`;
`say` `{text}`; `fallback` `{cause}`;
`stride` `{turn, distance, meanVx, strides, peakTorquePct, saturatedTicks, airborneTicks}` — once per
turn, the summary of what the order actually did;
`milestone` `{stage, metres}` — every 5 m of new stage distance;
`fall` `{stage, why, x}` with `why ∈ {low, high, pitched}`;
`stageend` `{i, outcome, distance, return, ticks, peakSpeed}`;
`budget` `{turn, remaining_s}`; plus `end` `{reason, endRule, total, score, stagesLined, falls}`.

`tests/test_cc_events.nim` asserts the emitted set equals exactly this list. **Nothing fires per tick**:
individual footstrikes, dust and torque flashes are *renderer FX derived from state deltas*, never
events, so the feed cannot flood at 24 Hz. `stride` and `order` fire ≤ 42 times an episode;
`milestone` is bounded by `60/5 × 3 = 36`.

**Beats** — the scrubber markers, and the only kinds the appended game block emits: **`stagestart`,
`milestone`, `fall`, `stageend`, `fallback`, `end`.** `turn`, `order`, `say`, `stride` and `budget` drive
the feed, not the scrubber. **`fall` is the idea's own highlight** (`Replay plan … falls`) and it is a
first-class beat kind with its own CSS and its own label (`DOWN — HOPPER PITCHED PAST 20° AT 6.1 M`).

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `StageStart, TurnStart, Order, Fallback, Servo, Footstrike, Milestone, Fall,
StageEnd` and the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.
**`Servo` is the per-tick row carrying every joint's target angle and applied torque** — this is the
full continuous-control action trace the idea's neural-policy teams want, up to 1 512 rows an episode,
which the replay deliberately does not carry.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}` under `game` — i.e.
`replay_viewer.bundle = static-replay-viewer` — and `tools/build_replay_viewer.sh` is coworld-ctf's hook,
kept, with the image tag and the `docker cp` source path changed
(`/workspace/ctf/replay-viewer/dist/.` → `/workspace/cc/replay-viewer/dist/.`), building
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and copying the dist out. It already carries
the ecos 2026-08-23 `mkdir -p "$(dirname …)"` fix (line 21) and the buildx / `--platform linux/amd64`
handling. It stays committed **executable** (`coworld build` hard-requires `os.X_OK`). **No
`/client/replay` live-server viewer is ever declared to the platform**; the game still serves
`/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/cc_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`** —
this repo's own starter. **None of the four comes from `cogame-babel`, `cogame-bullwhip`,
`cogame-parley`, `cogame-moba` or `cogame-factorio`, and none is written fresh. Never a mixture.**
Splicing one starter's shell onto another's emscripten link flags (`MODULARIZE` / `EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently with every file present and 200
(cogame-lantern, 2026-08-23).

| File | Source |
|---|---|
| `replay-viewer/config.nims` | **`coworld-ctf`**'s, verbatim except the output name `ctf_replay.js` → `cc_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_cc_*`. **No `MODULARIZE`, no `EXPORT_NAME`.** The flags stay exactly as ctf links them: `--os:linux --cpu:wasm32 --cc:clang` through `emcc`, `--mm:arc --exceptions:goto --define:noSignalHandler --define:release --define:useMalloc`, `-O2`, `--preload-file <root>/data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable: with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed allocation would write the seq header through nil into address 0 and corrupt the module's own globals — the starter's own comment at `replay-viewer/config.nims:33-41`), `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, and `EXPORTED_FUNCTIONS=_main,_malloc,_free,_cc_load_replay,_cc_frame,_cc_input,_cc_packet_ptr,_cc_packet_len,_cc_mismatch_tick,_cc_error_ptr,_cc_error_len,_cc_stage_ptr,_cc_stage_len` |
| the wasm entry `.nim` | **`coworld-ctf`**'s `replay-viewer/ctf_replay.nim`, forked to `replay-viewer/cc_replay.nim`. Kept: the `stampStage` fixed progress buffer that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, the `predictedViewerRenderBytes` / `WasmViewerBudgetBytes` capacity preflight (`ctf_replay.nim:71-76`), and the `emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module destructors while JS keeps calling in. |
| `static_replay*.js` | **`coworld-ctf`**'s `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) + `importScripts('./wire_constants.js', './broadcast_core.js', './cc_replay.js')` (`:239`, renamed only) form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Two other names change: the Worker name `ctf-static-replay` → `cc-static-replay`, and `window.CtfStaticReplay` → `window.CcStaticReplay`. |
| `index.html` | built from **`coworld-ctf`**'s `client/replay_broadcast.html` (below). |

Two additions to `cc_replay.nim`, and no others:

- **A load-time pre-scan.** `cc_load_replay` walks the recorded **state keyframes and per-turn `stride`
  summaries** — not a full re-simulation — to build the cumulative-return series, the stage boundary
  ticks, the beat ticks and the lull spans, then renders frame 0. Reading 32 keyframes and 42 summaries
  is microseconds, which is what lets the progress sparkline and the scrubber beats draw at **full width
  on the first frame** instead of growing in. (This is the one place the keyframes earn their 5.4 KB
  twice over; re-simulating 1 512 ticks × 120 solver passes at load would delay the first frame by
  seconds.)
- `cc_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `-1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (`replay-viewer/static_replay.js:161`) — posted
by the Worker only *after* `ingestPacket()` (`static_replay_worker.js:64`) has handed BroadcastCore the
first frame and it has drawn, so the attribute means "a frame is on the canvas", not "a file was
fetched". **On failure it sets `data-replay-error`** on `<html>` with the message, in `showFailure()`
(`static_replay.js:14-20`), and `data-replay-mismatch-tick` on a hash mismatch (`:32`). All three are
coworld-ctf's own signals, inherited unchanged — this fork adds none and removes none. The
`coworld-replay` postMessage bridge's `ready` is posted **from a callback fired after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24), or the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte** (40 022 bytes; sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`). Not edited, not reformatted;
  `tests/test_cc_viewer.nim` pins that sha256 as a literal. Everything this game adds lives in the
  appended game block. Its `markBeat` / `renderBeatMarkers` / `ingestBeats` / `renderClock` /
  `renderTransport` / `ingestLullSpans` / `renderMomentum` remain; `ingestBeats` ignores kinds it does
  not know. The state JSON keeps ctf's key names above the fold (§The exact state JSON) so chrome_common
  runs unmodified.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one `<style>`
  and one `<script>` block after the starter's banner comment at `client/replay_broadcast.html:4355`,
  never a rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup,
  `relayout()` (`:4287-4332`), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny`
  density system are untouched, and the block is installed through the starter's own splice hook:
  `window.PaintballChrome` (context `PB_CTX` built at `:4341`, installed at `:4348`, declared at
  `:4662`) is renamed `window.CcChrome` and its `install(PB_CTX)` / `frame(s, ctx, jumped)` (`:2085`) /
  `event(e, s, ctx)` (`:3490-3491`) entry points are kept with the same signatures. The appended block
  replaces only the *contents* of the scorebug plate, adds the stage ribbon, the three stage pips, the
  track ruler and the gait card, and retargets the feed rows, the beat rendering, the momentum series and
  the endcard columns. A test asserts the starter's byte prefix is intact up to `:4355` and that the file
  only grows.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_cc_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (the cogball 0.1.4 latch scar: a signature drift threw
  mid-replay and latched `static_replay.js` into `failed`), `banner`, the beat and lull machinery, the
  endcard builder, the speed chips, the `?embed=1` path, and the `window.CTF_WIRE` → `window.CC_WIRE`
  rename emitted by `tools/gen_wire_constants.nim`. Deleted: every ctf-specific draw call, the raycast
  FPV pipeline (the `#fpv` **panel** is reused, the raycaster is not), and `attachMinimap`'s call site.
  Added: `drawTrackBed`, `drawRuler`, `drawFootprints`, `drawLink`, `drawJointHub`, `drawFoot`,
  `drawDust`, `drawTorqueGlow`, `drawFallFlash`, `drawStageRibbon`, `drawStagePips`, `drawGaitCard`,
  `drawTrackStrip`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read` (`replay_broadcast.html:1520-1531`), and the page's
    `core.attachMinimap($('minimap-canvas'))` call. **Zoom decision: dropped entirely.** The board is a
    **fixed 1440 × 960 camera viewport** — the bitmap the chrome receives is always exactly the frame,
    never larger — so per the pin (`#viewpanel` exists only for boards larger than the frame) a fixed
    board drops it. The world *is* longer than the frame, and that job is done properly by the **track
    strip** readout (below), which shows the whole 60 m at a glance instead of a thumbnail of a board
    that does not exist. `broadcast_core.js` already tolerates never being attached: `minimapSurface` /
    `minimapCtx` stay null and `drawMinimap()` returns on its first guard.
  - **`#povBadge`** (`:1535`) and the `togglePov` wiring — with one seat there is nothing to select.
  - Inside the kept `#fpv`: **`#fpv-hp`** (`:1547`), **`#fpv-gear`** (`:1548`), **`#fpv-map`** and
    **`#fpv-map-canvas`** (`:1552-1554`) — the machine has no hit points and no gear, and the panel is
    repurposed wholesale as the **gait card** (below).
  - The ctf scorebug internals `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`, `.lives-label`,
    `.squad-pip`, `.pb-tags`, `.squad`, and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture` and `.gamestart`, `.hillflip`, `.tagout`,
    `.gameover` CSS rules — those kinds are never emitted here.
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (`#lk-bg`,
    `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with `#plates-l` / `#plates-r` /
    `#clock` / `#clock-time` / `#clock-caption` / `#ffwd-mini`, **`#fpv` with `#fpv-canvas`, `#fpv-hud`,
    `#fpv-name`, `#fpv-cap` and `#fpv-grip`** (repurposed as the **gait card**, caption `GAIT ORDER`,
    `#fpv-name` reading `ALPHA · CHEETAH`, still draggable and resizable by the starter's own grip),
    `#bannerlane`, `#killfeed`, `#mmwarn`, **`#transport` in full** (`#btn-restart`, `#btn-back`,
    `#btn-play`, `#btn-fwd`, `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`,
    `#win-chip`, `#tick-clock`, `#speedchips`), `#scrub` with `#momentum` / `#scrub-fill` / `#lulls` /
    `#scrub-win` / `#scrub-head`, `#endcard` with `#ec-headline` / `#ec-wincond` / `#ec-how` /
    `#ec-teams` / `#ec-replay`, and `#status`.
    **`#plates-r` is kept but rendered empty** — it is one of the scorebug's three flex columns
    (`:1502-1513`) and removing it would un-centre `#clock`; with one seat the single plate lives in
    `#plates-l`.

### Endcard and chrome label re-mapping

A forked ctf endcard silently ships paintbot's vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings, because `labels.nim`
deliberately scopes itself to the *policy* contract. The re-labelings are therefore enumerated here and
enforced by a test:

| Starter string | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` | `<span>Stage</span><span>Body</span><span>Result</span><span>Distance</span><span>Return</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` | `<span>Cog</span><span>Metres</span><span>Falls</span><span>Return</span>` |
| `<span class="fl-cap">Lives left</span>` | `<span class="fl-cap">Stages standing</span>` |
| `<span class="fl-cap">Hill time</span>` | `<span class="fl-cap">Metres covered</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (`:1586`) | `<span class="momentum-label">RETURN</span>` |
| `<span class="lives-label">Lives</span>` | `<span class="stage-label">Stage</span>` |
| `<span class="lives-label pb-lbl">Hill</span>` | `<span class="stage-label pb-lbl">Body</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" | "Wheeling the first machine onto the track…" |
| `#clock-caption` "In the locker room" (`:1509`) | "Waiting for the cog" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (`:1534`) | "Replay hash mismatch at tick N — resynced from the recorded pose" |
| `#fpv-cap` "EYES" (`:1555`) | "GAIT ORDER" |
| `#btn-spoilers` title "Spoilers: kills / flag story / winner on the timeline ahead of the playhead (o)" (`:1574`) | "Spoilers: falls and stage results on the timeline ahead of the playhead (o)" |
| team words `RED` / `BLUE` in `.ec-tname` / plates | the seat's **alias** (`ALPHA`) on the plate, and the **morphology name** (`HOPPER` / `CHEETAH` / `WALKER`) as the endcard section head |

**`tests/test_cc_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper` (in
chrome copy: the machine is `HOPPER`, the *paint* hopper is banned, so the grep is case-sensitive on
`hoppers`), `hill`, `POV`, `EYES`, `spray`, `grenade`, `med kit`, `kill`, `team` — outside comment
blocks, and asserts **zero** matches; and asserts each replacement string above is present exactly once.
A rename that reintroduces paintbot vocabulary fails the build.

### The exact state JSON the viewer reads

`buildStateJson` (ctf's `broadcast.nim:838`, retargeted) emits this object once per frame. Keys above
the fold are ctf's own (`:866-892`) and are consumed by the byte-identical `chrome_common.js`;
everything this game adds lives under `cc` and `orders`, consumed only by the appended game block.

```json
{"t": 357, "mt": 1512, "ph": "playing", "lob": 0, "pl": true, "sp": 1, "mx": 1512,
 "st": 0, "lp": false, "sk": false, "ff": false, "en": true, "mm": -1, "bs": 2, "pov": -1,
 "turnTicks": 36, "turn": 10, "turns": 42,
 "teams": {"alpha": {"score": 20.35, "stagesDone": 1, "stagesLined": 0,
                     "distance": 14.82, "speed": 5.31, "falls": 1, "down": false}},
 "roster": [{"s": 0, "name": "daveey", "team": "alpha", "alias": "ALPHA",
             "kind": "llm", "score": 20.35, "distance": 14.82,
             "llmTurns": 9, "fallbacks": 1, "repaired": 0}],
 "events": [{"t": 342, "k": "milestone", "stage": 1, "metres": 10}, "…"],
 "cc": {"stage": {"index": 1, "of": 3, "morph": "cheetah", "tick": 108, "of_ticks": 468,
                  "terminatesOnFall": false, "phase": "playing",
                  "log": [{"i": 0, "morph": "hopper", "outcome": "fell",
                           "distance": 6.11, "return": 12.99, "ticks": 213, "peak": 3.42}]},
        "track": {"length": 60.0, "x": 14.82, "best": 14.82, "cam": 12.60, "back": -6.0,
                  "marks": [{"i": 0, "x": 6.11, "outcome": "fell"}]},
        "body": {"morph": "cheetah",
                 "links": [{"i": 0, "name": "torso",  "x": 14.82, "y": 0.63, "a": -8.4,
                            "hl": 0.500, "r": 0.046},
                           {"i": 1, "name": "bthigh", "x": 14.41, "y": 0.49, "a": 41.2,
                            "hl": 0.145, "r": 0.046},
                           "… 7 entries, link index order, ALWAYS the morphology's count …"],
                 "joints": [{"j": 0, "name": "back_hip", "a": -22.4, "tq": 74, "sat": false},
                            "… 6 entries, joint index order …"],
                 "feet": [{"f": 0, "name": "back_foot",  "g": true,  "x": 14.35, "y": 0.05, "slip": 0.08},
                          {"f": 1, "name": "front_foot", "g": false, "x": 15.44, "y": 0.31, "slip": 0.00}],
                 "vx": 5.31, "vy": 0.12, "spin": -31.0, "pitch": -8.4, "height": 0.63,
                 "airborne": false},
        "order": {"gait": "run", "cadence": 68, "power": 80, "lean": 10,
                  "stride_bias": 0, "phase_shift": 0,
                  "stride_hz": 2.36, "cycle_pct": 41, "source": "llm", "say": ""},
        "score": {"return": 20.35, "par": 40.0, "max": 243.744,
                  "dist_pts": 19.63, "upright_pts": 0.85, "ctrl_pts": -0.13}},
 "orders": [{"turn": 10, "source": "llm", "gait": "run", "cadence": 68, "power": 80,
             "lean": 10, "say": "lengthening the stride now the cheetah is up to speed"}],
 "lead": {"teams": ["alpha"], "pts": [[0, 0], [213, 12994], "… change-points of the running return …"]},
 "beats": [{"t": 213, "k": "fall"}, {"t": 249, "k": "stagestart"}, "…"],
 "lulls": [[430, 470]],
 "over": {"winner": "alpha", "draw": false, "timeLimit": false,
          "endRule": "ladderComplete", "reason": "complete",
          "score": 61.948, "ticks": 1257,
          "teams": {"alpha": {"stagesLined": 0, "falls": 1}}},
 "hold": 3}
```

There is exactly **one** `teams` key (`alpha`), so chrome_common's plate loop renders one plate, in
`#plates-l`, and `#plates-r` stays empty. `roster` carries the **real policy name** and is spectator-side
only; `cc.body`, `cc.order` and the board carry only the alias.

### Readouts

1. **The track**, drawn edge to edge in side elevation: the baked dirt bed with grain, a horizon of
   darkened parallax blocks, metre ticks and a numeral every 5 m, the start line at 0 and a **red-and-
   white finish gate at 60 m**. The camera follows the torso and the ruler slides under it, so speed is
   legible as motion, not as a number.
2. **The machine**, drawn from the actual link poses: each link a composited capsule hull at its real
   `hl` and `r`, joint hubs at the anchors, feet drawn dark when airborne and bright with a **dust puff**
   when they strike, and a **footprint** left in the dirt at each strike (a 64-entry ring). A joint at
   ≥ 90 % of its torque cap glows amber; at 100 % it flashes red. A spectator can therefore *see which
   joint is pegged*, which is the single most informative thing about a bad gait.
3. **The fall** (the idea's own highlight ask) — on a `fall` event the torso is ringed red, the frame
   shakes briefly, `#bannerlane` reads **`DOWN — HOPPER PITCHED PAST 20° AT 6.1 M`** for two seconds,
   the reset hold plays the body flopping at **half speed**, and the scrubber gets its tall red `.fall`
   beat. This is the whole answer to the idea's "lowest watchability per episode" worry: the fall is the
   moment, and the viewer stops on it.
4. **The gait card** — the repurposed `#fpv` panel, bottom-right in the board's letterbox gutter: the
   gait name in large type, five labelled horizontal bars for cadence / power / lean / stride bias /
   phase shift, and a **phase wheel** showing `cycle_pct` ticking round once per stride so the order is
   visibly *running*, not just displayed. This is the idea's "gait gallery", per episode. Captioned
   `GAIT ORDER`, with `ALPHA · CHEETAH` beneath. Draggable and resizable by the starter's own
   `#fpv-grip`.
5. **Track strip** — a 60 m horizontal strip pinned inside the board region at its top edge (never in
   the transport band): the whole track at a glance, with the runner's marker, the finish gate, and a
   **ghost marker for each resolved stage's final distance** so the ladder's progress is one picture.
   This is what replaces the dropped minimap.
6. **Stage ribbon** — in the board's left gutter: `STAGE 2/3 · CHEETAH · 0.50 PTS/M`, with
   `14.8 m · 5.31 m/s · TICK 108/468` under it.
7. **Stage pips** — three pips under the ribbon, one per stage in ladder order, each carrying its
   morphology name: pending (hollow), current (amber ring), ran (green fill), lined (green fill with a
   gate glyph), fell (red fill with a slash), unreached (grey outline).
8. **Clock** — `#clock` shows the big numeral `RETURN 20.4`; `#clock-time` shows `14.8 m · 5.31 m/s`;
   `#clock-caption` shows `STAGE 2/3 · CHEETAH · TICK 108/468`.
9. **Scorebug plate** — one plate in `#plates-l`: the seat's **real policy name** (spectator side only),
   its in-game alias `ALPHA`, the cog avatar from `data/soldier_red_front.png`, the running return as the
   numeral, three small **stage chips** filled as stages resolve, and a `↯` glyph if the seat has taken a
   fallback.
10. **Match feed** (`#killfeed`) — plain language, never internal notation: `STAGE 2 OF 3 — CHEETAH,
    60 M OF TRACK`, `ORDER — RUN, CADENCE 68, POWER 80, LEAN +10`, `10 METRES — 4.9 S, TOP SPEED
    6.2 M/S`, `FRONT KNEE PEGGED — 11 TICKS AT FULL TORQUE`, `BACK FOOT SLIPPING — 0.8 M/S`, `DOWN —
    HOPPER PITCHED PAST 20° AT 6.1 M`, `STAGE 2 DONE — 45.3 M, RETURN 22.5`, `LINED OUT — 60 M IN
    17.4 S`, `Alpha: "lengthening the stride now the cheetah is up to speed"`, and `MISSED THE CALL —
    trotter order (timeout)`. The `say` lines and the order lines are where a spectator sees the LLM
    playing.
11. **Progress sparkline** — the starter's `#momentum` SVG retargeted to one cumulative series (the
    running return) with **stage spans shaded** in the pip colours behind it, stage boundaries as
    vertical ticks, and the playhead marked. Filled from the load-time pre-scan, so it draws at full
    width on the first frame. A flat line inside a red span is the whole story of a fallen stage in one
    glance.
12. **Endcard** — `RETURN 61.9 — 0 OF 3 LINED OUT, 1 FALL, PAR 40 MET`, a three-row table under the
    re-mapped header (`Stage | Body | Result | Distance | Return`), a summary line (`67.8 m covered,
    681 upright ticks, 214 saturated ticks, 1 fallback turn`), and `SCORE 61.948`. It stops at
    `var(--band)` and any seek dismisses it.
13. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    48 consecutive ticks with the torso moving under 0.15 m and no stage change, from the pre-scan),
    spoilers switch, tick readout, speed chips, the scrubber with its six beat kinds, and `#mmwarn` on a
    hash mismatch — all the starter's, verbatim.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (`client/replay_broadcast.html:4300-4328`). **No overlay sits in the transport
band**: the board is laid out between the two bands, and every addition here (the track strip, the stage
ribbon, the stage pips, the gait card, the feed) is positioned inside the board region, in the letterbox
gutters beside it, or in the top band — every game-block element is `bottom: calc(var(--band) + N *
var(--u))` or higher, never over it. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, `:1047`, the starter's rule, kept) so the scrubber stays
clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `ccBeat(tick, kind, label)` — named with the `cc-` prefix so it can never
shadow `chrome_common.js`'s `markBeat` alias (`client/replay_broadcast.html:1645`; the tandem 2026-08-23
hoisting trap, and the same prefix discipline the starter's own `pbBeat` uses) — appends
`<button class="beat-marker <kind>" title="…" aria-label="…">` to `#scrub` and seeks on click. CSS exists
for **every kind emitted and no others**: `.beat-marker.stagestart`, `.beat-marker.milestone`,
`.beat-marker.fall`, `.beat-marker.stageend`, `.beat-marker.fallback`, `.beat-marker.end`. `.fall` is the
tallest, reddest marker on the bar — it is the moment the spectator came for. The game block never calls
`markBeat`, so an unlabelled div marker cannot appear.

**Playback rate: one tick per animation frame at 24 ticks/second = real time** (speed chips
`[0.5, 1, 2, 4, 8]`, default 1), with link poses interpolated between recorded ticks when the frame rate
exceeds 24 Hz. A full 1 512-tick episode plays for **63 s**, and even a triple-fall episode (three stages
of ~60 ticks plus three 36-tick holds ≈ 288 ticks) plays for **12 s** — enough for
`viewer_smoke.mjs --soak 10` to observe real advancement rather than a legitimately-finished replay (the
ecos 2026-08-23 scar), and the cert fixture is additionally pinned at ≥ 400 ticks (§Tests 30).

### Art

**Real art, from the starter's shipped assets plus install-time bakes — no placeholders, no
solid-colour rectangles, no downloads.** The dirt bed is `data/arena_floor.png`, tiled on a 1.50 m period
and darkened 25 %, with baked grain, metre ticks and 5-metre numerals set in `data/font.ttf` — one pixie
bake per episode, exactly the way the starter bakes endzone paint. The **horizon** is
`client/art/lockerroom/bg.jpg` darkened and blurred, with a parallax band of blocks cut from
`client/art/walls/wall_h.jpg` and `wall_v.jpg` scrolling at 0.35× the camera. **Link hulls** are baked
once per morphology by `rig_art.nim` from the palette in `data/pallete.png` and the red plating of
`data/soldier_red.png`: a capsule with a bevelled edge, a rivet line and an amber servo band at each end
= 8 hull chips per morphology in two states (nominal, glowing) = **48 chips** total, baked at install.
**Feet** are two chips each (planted, airborne). **Footprints, dust puffs, the torque glow, the fall
flash, the phase wheel, the stage pips and the track strip** are procedural in the bed bake's palette.
The **finish gate** is baked from `wall_v.jpg` with red-and-white banding. The avatar on the scorebug
plate is `data/soldier_red_front.png`. The loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the four red webps) with the caption re-labelled.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (`client/replay_broadcast.html:4318-4324`). The board's aspect is **1440/960 = 1.500**. In a
360 × 203 frame, `relayout()` reserves `--topband` and `--band`, leaving a play region roughly
360 × 120; since `360/120 = 3.0 > 1.5`, **height binds**: the board renders **180 × 120**, i.e. 20 board
pixels per metre of world — a 0.5 m link is 10 px, which is legible as a limb. That letterbox leaves
**two ~90 px gutters**, and this game uses them: the **stage ribbon and the three pips live in the left
gutter**, the **gait card in the right**, so neither ever overlaps the board and neither ever enters the
transport band. Five rules are added and asserted by `tests/test_cc_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…".
2. Under `.tiny`, the single plate keeps only `alias + name + return + the three stage chips`; the avatar
   shrinks to 10 px and the fallback glyph moves inline.
3. Under `.tiny`, the stage ribbon wraps to at most **two lines at 9 px** (`STAGE 2/3 · CHEETAH` /
   `14.8 M · 5.31 M/S`), with the full string in the `title` attribute and re-announced in `#bannerlane`
   at every `stagestart`.
4. Under `.tiny`, the gait card drops the five bars' captions to tooltips and keeps the gait name, the
   bars and the phase wheel; it is pinned to 84 px square in the right gutter and the `#fpv-grip` resize
   is disabled below 620 px so it cannot be dragged over the board.
5. Under `.tiny`, the track ruler drops its metre ticks and keeps only the 10-metre numerals and the
   finish gate; the track strip keeps its full 60 m at 6 px tall. **Every glyph either panel draws is a
   baked chip, never live text**, at `--hudscale`-derived sizes so nothing is drawn outside the canvas
   (`--strict-text-bounds` stays on).

---

## Packaging

- **Repo**: `Metta-AI/cogame-continuous-control`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `continuous-control`; **`game.name` is
  `continuous-control`** — identical to the slug, so the secret namespace
  `secret://coworld/continuous-control/anthropic_api_key`, the page slug, the
  `POST /coworld-league-seeds` body and the docs all agree (the commons-family 2026-08-24 scar, where
  `game.name` and the slug differed by an underscore).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name by uppercasing and replacing `-` with `_` (`{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0). ctf ships two services/two images; this fork uses the one-image / two-entrypoints
  shape because the shared `docker_smoke.sh` and `policies.json` assume a single image (the
  knights-archers precedent):

  ```yaml
  services:
    continuous-control:
      image: coworld-continuous-control:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder `{{CONTINUOUS_CONTROL_IMAGE}}`.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:continuous-control
  src/continuous_control.nim` → `/bin/continuous-control`, and the same for
  `src/continuous_control_player.nim` → `/bin/continuous-control-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/continuous-control"]`, runtime
  `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk:4.0.15`, pinned
  nimby with its sha256 check, the marker splices, the whole `test -f` / `grep -q` assertion block) with
  the asset list swapped to `data/{arena_floor,ascii,pallete}.png`, `data/soldier_red{,_front}.png`,
  `data/font.ttf`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,red_*.webp}`,
  `cc_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["continuous-control", "single-agent", "physics", "locomotion",
    "mujoco-family"]` (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0);
    **`episode_timeout_minutes: 20` at the top level**, not under `game`.
  - `game.name = "continuous-control"`, `game.owner = "daveey@softmax.com"`, `game.description` present
    (required), `game.runnable.type = "game"`, `game.runnable.run = ["/bin/continuous-control"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/continuous-control/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 1/1, `players` 1/1, `slots` 0/1, `stageLadder` 3/3 — the tandem 0.1.0 scar). `tokens` is
    described as runner-injected; **no `game_config` anywhere in this manifest contains a literal
    `tokens` array** (matriculate rejects "game_config must not include runner-managed tokens" —
    knights-archers 0.1.0), while `config_schema` keeps *requiring* it because the runner injects it.
    Properties: `tokens`, `players`, `slots`, `seed`, **`num_agents`** (integer, `minimum: 1`,
    `maximum: 1`, default 1), `minPlayers`, `stageLadder`, `stagesPerEpisode`, `stageTicks`,
    `resetTicks`, `turnTicks`, `maxTurns`, `maxTicks`, `par`, `substepsPerTick`, `solverIterations`,
    `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`, `wallClockBudgetSeconds`,
    `lobbyJoinTimeoutTicks`, `gameOverTicks`, `stateKeyframeTicks`, `fastMode`, `showPlayerLabels`,
    `model`, `maxOutputTokens`.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}`,
    `endRule: {"type":"string","enum":["ladderComplete","turnCap","wallClock","fault"]}`,
    `stageOutcome` items `{"enum":["lined","ran","fell","unreached"]}` and `stageMorph` items
    `{"enum":["hopper","cheetah","walker"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-continuous-control/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar).
  - **`game.docs`** = `{"readme": {"type":"uri","value":".../README.md"}, "pages": [
    {"id":"rules.md","title":"Rules","content":{"type":"uri","value":".../docs/RULES.md"}},
    {"id":"actions.md","title":"Gait orders and the reply format","content":{"type":"uri","value":".../docs/ACTIONS.md"}},
    {"id":"physics.md","title":"The physics, and how it differs from MuJoCo","content":{"type":"uri","value":".../docs/PHYSICS.md"}}]}`.
  - Top-level `player[]` with `id` / `type` / `name` / `description` / `image` / `run` / `source_url` and
    `resources: {requests: {cpu: "100m", memory: "64Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must be
    at least `"1"`** (pistonball 0.1.1). **Exactly ONE entry, `trotter`**: `num_agents = 1` leaves
    exactly one certification slot, and **every declared player must occupy a certification slot** (the
    raid 0.1.2 scar), so a second declared player could not be seated. `plodder` still ships in the
    image, is exercised by `tests/test_cc_baselines.nim`, and is a league filler in
    `tools/ci/policies.json` — it is simply not a *declared manifest* player.

  **Variants — `num_agents: 1` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0):

  ```json
  "variants": [
    {"id": "ladder", "name": "Locomotion ladder (1 cog, 3 machines)",
     "description": "One cog drives three planar machines down a flat 60-metre track, 19.5 seconds each: a one-legged hopper, a long-bodied cheetah that cannot fall, and an upright walker that can. Every 1.5 seconds the cog names a gait and tunes five numbers; a deterministic pattern generator and PD servos run that order on every joint 240 times a second. The score is the return: metres covered, plus a bonus per second upright, minus the cost of slamming the actuators.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "stageLadder": ["hopper", "cheetah", "walker"],
                     "stagesPerEpisode": 3, "stageTicks": 468, "resetTicks": 36,
                     "turnTicks": 36, "maxTurns": 42, "maxTicks": 1512, "par": 40.0,
                     "substepsPerTick": 10, "solverIterations": 12,
                     "stateKeyframeTicks": 48,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9000, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 690, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "bipeds", "name": "Bipeds only (1 cog, 3 machines that fall over)",
     "description": "The same three-stage format with the cheetah removed: a hopper and then two walkers, each with a different seeded start wobble. Both of these machines end their stage the instant the torso drops or pitches too far, so falling — not top speed — is what decides the episode. This is where a policy that only knows how to go fast stops scoring.",
     "game_config": {"players": [{"name": "Alpha"}],
                     "num_agents": 1, "minPlayers": 1,
                     "stageLadder": ["hopper", "walker", "walker"],
                     "stagesPerEpisode": 3, "stageTicks": 468, "resetTicks": 36,
                     "turnTicks": 36, "maxTurns": 42, "maxTicks": 1512, "par": 30.0,
                     "substepsPerTick": 10, "solverIterations": 12,
                     "stateKeyframeTicks": 48,
                     "attempt1Ms": 6000, "retryMs": 3000,
                     "turnBudgetMs": 9000, "turnSpacingMs": 2600,
                     "wallClockBudgetSeconds": 690, "lobbyJoinTimeoutTicks": 2400,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 1` again, inside `certification.game_config`, and exactly one
  player so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS == 1`
  (the four `SEAT-COUNT` invariants `tools/ci/docker_smoke.sh` cross-checks at template lines 113-150),
  with the single declared player seated:

  ```json
  "certification": {
    "players": [{"player_id": "trotter"}],
    "game_config": {"players": [{"name": "Alpha"}],
                    "num_agents": 1, "minPlayers": 1, "seed": 42,
                    "stageLadder": ["hopper", "cheetah", "walker"],
                    "stagesPerEpisode": 3, "stageTicks": 468, "resetTicks": 36,
                    "turnTicks": 36, "maxTurns": 42, "maxTicks": 1512, "par": 40.0,
                    "substepsPerTick": 10, "solverIterations": 12,
                    "stateKeyframeTicks": 48,
                    "wallClockBudgetSeconds": 240, "lobbyJoinTimeoutTicks": 600,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  A `trotter`-only episode is scripted throughout, so the whole ladder is a few seconds of CPU, but the
  replay is over a thousand ticks ⇒ **tens of seconds of playback**, which the viewer soak needs. Seed 42
  is asserted by `tests/test_cc_engine.nim` to produce a fixture episode with **at least 900 recorded
  ticks, at least one stage with `distance ≥ 10 m`, and at least one `fall` event**, so the smoke replay
  always exercises the `stagestart`, `milestone`, `fall` and `stageend` beat paths. The certify step in
  `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 covers start + connect grace
  + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/continuous-control-player"`,
  following the starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"continuous-control-gaitsmith","run":"/bin/continuous-control-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"gaitsmith"}},
   {"name":"continuous-control-throttle","run":"/bin/continuous-control-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"throttle"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"continuous-control-trotter","run":"/bin/continuous-control-player",
    "env":{"PLAYER_SCRIPTED":"trotter","PLAYER_POLICY_LABEL":"trotter"}},
   {"name":"continuous-control-plodder","run":"/bin/continuous-control-player",
    "env":{"PLAYER_SCRIPTED":"plodder","PLAYER_POLICY_LABEL":"plodder"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1, uploaded
  while daveey-1 is the active player); the fillers are `trotter` and `plodder`, and their versions must
  differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `continuous-control`,
  `<IMAGE>` → `coworld-continuous-control`, **`<SEATS>` → `1`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0`
  (§Server) and `--soak 10` added to the `viewer_smoke.mjs` invocation (which already passes
  `--strict-text-bounds`, `templates/ci.yml:314-318`). The push-triggered `upload-coworld` job is gated
  on the `UPLOAD_REQUIRED` repo variable (derks-gym 0.1.1). `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable** (mode
  100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_cc_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) is the starter's, unchanged.

**Sim unit tests** (`tests/test_cc_sim.nim`)

1. `fixed-point arithmetic` — `mulQ` is exact against `int128` reference products over 10 000 random
   pairs inside the declared envelopes; `mulQ(a, −b) == −mulQ(a, b)` for every pair (symmetry under
   negation, which `shr` would break); `wrapAngle` is idempotent and maps `(−3π, 3π]` into `(−π, π]`.
2. `no `shr` on a signed value` — a source grep over `src/cc/*.nim` finds no `shr` outside
   `wire_constants.nim`'s byte packing.
3. `trig table` — every one of the 1 025 committed entries is re-derived from `math.sin` with
   `|err| ≤ 2` in Q16; `sinQ16` is odd, `sinQ16(a + 2π) == sinQ16(a)`, `sin² + cos²` is within 40 of
   65536² / 65536 over 4 096 angles.
4. `forward kinematics` — for all three morphologies, the neutral pose and 500 random joint sets satisfy
   every joint's anchor coincidence to within 2 Q16 units, and the lowest contact point of the neutral
   pose is exactly on `y = 0`.
5. `solver invariants` — over 2 000 random states of each morphology: the 2×2 joint determinant never
   falls below `DetEpsQ16`; no constraint impulse exceeds `MaxImpulseQ16`; after a substep, every joint's
   anchor separation is under 2 mm and every foot's penetration is under `PenetrationSlop + 1 mm`; the
   friction impulse never exceeds `GroundFriction ×` the normal impulse.
6. `energy sanity` — with all servo torques forced to zero and the body dropped from the neutral pose,
   total mechanical energy is non-increasing over 480 ticks for each morphology (restitution 0, friction
   dissipative), to within a 1 % per-second numerical allowance. A solver that pumps energy fails here.
7. `no body escapes` — 5 000 random legal states stepped 480 ticks each: no link leaves
   `[−20, 80] × [−2, 20] m`, `|v| ≤ MaxLinSpeed`, `|w| ≤ MaxAngSpeed`, and the invariant guard never
   fires.
8. `the driver is a pure integer function` — `driverTargets(order, cyclePos, morph)` is deterministic,
   respects every joint limit, and produces identical output on two independent evaluations; `stand`,
   `crouch` and `brake` produce a constant target; `brake` sets `Kp = 0`.
9. `stride phase` — `cyclePos` advances by exactly `strideMilliHz · 1000 div 24` per tick, wraps at
   1 000 000, and `phase_shift = ±50` moves the phase by exactly half a cycle on the tick it is applied
   and never again.
10. `turn and tick order` — the numbered resolution order of §The game end to end: a stage that resolves
    breaks to `StageReset` for exactly 36 ticks; turn boundaries stay on the global grid and are never
    re-aligned; a stage that never starts is `unreached` with zero everything.
11. `fall detection` — over hand-built fixtures and 2 000 random states: the hopper falls exactly when
    `y < 0.70` or `|pitch| > 20°`; the walker exactly when `y ∉ (0.80, 2.00)` or `|pitch| > 57°`; the
    **cheetah never falls**, in any state, ever.
12. `the line` — a body driven past `x = 60 m` resolves `lined` on that tick, `distance` is exactly
    60.000, `uprightTicks` is set to `stageTicks`, and no further ticks are credited.
13. `no floating point in the sim` — a source grep over
    `src/cc/{sim,solver,body,driver,gaits,trig}.nim` finds no `float`, `/`, `sqrt`, `math.sin` or float
    literal. `src/cc/report.nim` is excluded by name and the sim is asserted to compile without it.
14. `tick budget` — a full 1 512-tick episode (10 substeps × 12 iterations) completes in **< 3 s** in a
    release build and **< 200 ms** for the cheetah stage alone, which is the §Decisions arithmetic.

**Scoring** (`tests/test_cc_scoring.nim`)

15. `the formula` — `stageReturn == DistNum/DistDen × distance + UprightPerTick × uprightTicks −
    ctrlCostAccum/64` over 500 randomised end states for each morphology, in micro-points, exactly;
    `totalReturn == Σ stageReturn`; `scores[0] == round(totalReturn, 3)`.
16. `sign and bounds` — a backwards run produces a **negative** score and it is not clamped; the maxima
    are `243.744` (`ladder`) and `305.616` (`bipeds`); the control cost never exceeds 0.439 points per
    6-joint stage; `win[0] == (totalReturn >= par)`; `winner == 0` when `win[0]` and `null` otherwise.
17. `no stage dominates` — at the pinned baseline distances (§Decisions → baseline strength) the three
    stages' returns are within a factor of 1.6 of each other on `ladder`.

**Seeding and determinism** (`tests/test_cc_seeding.nim`)

18. `start poses are pure` — every stage of every variant starts identically under three different policy
    behaviours, Q16 word for word, including the per-joint perturbation.
19. `stage independence` — stage `k`'s start pose is bit-identical whether stage `k − 1` fell at tick 20
    or ran to 468.
20. `the seed spans the space` — over 5 000 seeds the perturbation draws are uniform over
    `[−InitPerturb, +InitPerturb]` within a chi-squared bound, and no two seeds in the sweep produce the
    same three-stage pose set.
21. `two episodes, same seed, same orders, byte-identical` — including the hash chain and every state
    keyframe.

**Bounded orders / legality on the scripted baselines** (`tests/test_cc_baselines.nim`)

22. `baselines are bounded` — for 300 pseudo-random states (all three morphologies, all three stage
    phases, mid-stage and fresh, upright and falling) and for **both** `trotter` and `plodder`: `gait` is
    in the closed enum, `cadence` and `power` are 0…100, `lean`, `stride_bias` and `phase_shift` are
    −50…+50, `say` and `notes` are empty, and the serialised order is ≤ 512 bytes. A baseline that ever
    proposes an out-of-range or unbounded order fails the build.
23. `fallback is the trotter proc` — the decision engine's fallback path and the `trotter` baseline
    resolve to the same proc, so they cannot drift.
24. `order validation` — the validator accepts the schema, **clamps** (never drops) an out-of-range
    number, inherits a missing field from last turn and then from the gait default, lower-cases and maps
    the gait synonyms, accepts a `say`-only reply as usable, rejects a non-object, truncates `say`/`notes`
    on **rune** boundaries at 140/320 with 4-byte emoji sitting exactly on the boundary, caps the read at
    4096 bytes, and reports `repaired` back accurately.
25. `baseline strength is in range and tuning is the swept pick` — over 100 seeds of `ladder`, `trotter`
    covers 6–14 m (hopper), 30–58 m (cheetah), 11–24 m (walker) and falls on ≤ 1 stage on ≥ 80 % of
    seeds; `plodder` is strictly shorter on every morphology on ≥ 90 % of seeds and still returns a
    non-negative total. Neither a zero floor nor a superhuman filler can ship. The shipped
    `BaselineParams` equal `tools/ci/baseline_tuning.json` and the shipped `GaitTable` and servo gains
    equal `tools/ci/gait_tuning.json` (`ci.yml` re-runs both sweeps with `--check`).

**Observation** (`tests/test_cc_obs.nim`)

26. `observation reconstructs the state` — over 1 000 states, every reported joint angle, rate, limit,
    torque percent, foot contact, torso height, pitch and velocity round-trips against the sim's own
    values within the 2-decimal rounding; `joints` and `feet` always have the morphology's exact counts;
    `gaits` is always the six names in that order.
27. `torque_pct and saturated agree` — `saturated` is true exactly when `torque_pct == 100`, and
    `torque_pct` is `|tau| · 100 div τcap` at the tick's first substep.
28. `nothing hidden leaks` — the serialised observation and the composed prompt contain no `seed`, no
    unstarted stage's perturbation, no raw gait-table constant, no servo gain, and no real policy name; a
    grep test over a full recorded episode.

**End-to-end episode writing a replay** (`tests/test_cc_engine.nim`)

29. `episode writes artifacts` — run a real one-seat episode (`ladder`, scripted, no API key so the LLM
    client is `disabled`) against a temp-dir `COGAME_*` URI set; assert `results.json` and the `.replay`
    are written, `reason == "complete"`, `endRule == "ladderComplete"`, `scores` agree with the formula,
    all seven results identities of §Server hold, and the results key set equals the manifest's
    `results_schema` key set **exactly**.
30. `the cert seed is interesting` — seed 42 on `ladder` yields ≥ 900 recorded ticks, at least one stage
    with `distance ≥ 10 m` and at least one `fall` event, so the CI smoke replay always exercises those
    paths and always outlasts the 10 s viewer soak.
31. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure payload;
    the server refuses to start the game (loudly) when the joined seat has no register record.
32. `budget guard and rate guard settle early` — with each guard forced, the episode finishes `complete`,
    not `deadline`, and the matching record names the turn.
33. `end conditions` — `ladderComplete`, `turnCap`, a forced wall-clock stop and a forced fault each
    produce the right `endRule` and the right episode `reason`; a wall-clock stop mid-ladder marks every
    unstarted stage `unreached` with zero distance, zero return and zero ticks, and still scores the
    stages that ran.

**Replay** (`tests/test_cc_replay.nim`)

34. `record then re-derive, every end reason` — for `ladderComplete`, `turnCap`, `wallClock` **and**
    `fault`, record an episode and re-derive it from the bytes; assert identical hashes at every tick
    **including the stop tick** (the particle-worlds scar), and identical state at every keyframe.
35. `replay is self-sufficient` — the bytes alone yield the seat's real name, its alias, the policy kind,
    the full config (every constant in §Server's config-JSON row, including the whole `MorphTable` and
    `GaitTable`), the seed, the variant, all three stage records with their perturbations, every order
    record, every keyframe, every chat record and the result; and re-simulating from them reproduces
    every frame with **no fetch**.
36. `keyframes are a cross-check, not a crutch` — a deliberately corrupted keyframe is detected, sets
    `mismatchTick`, and the viewer resyncs; a corrupted **hash** is detected at the exact tick.
37. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "continuous-control/v1"`.
38. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`, kept.

**Manifest** (`tests/test_cc_manifest.nim`)

39. `manifest pins` — **`num_agents == 1` in both variants' `game_config` AND in
    `certification.game_config`**; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; `len(player) == 1` and that player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 1`; every array in
    `config_schema` has `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both
    `game.protocols.player` and `.global` present as `{"type","value"}` objects; `game.docs.readme` +
    `pages`; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds ≤ 690`;
    `attempt1Ms + retryMs ≤ turnBudgetMs` and both whole seconds;
    `maxTicks == stagesPerEpisode × (stageTicks + resetTicks)`, `maxTurns == maxTicks div turnTicks`,
    `stageTicks mod turnTicks == 0`, `len(stageLadder) == stagesPerEpisode`; `game.name` equals the slug
    and the secret URI's namespace; **and every variant's `game_config` actually constructs a valid
    `GameConfig`, builds all three of its bodies, and produces the ladder and the 42-turn schedule this
    note claims** (the collab-cooking 0.1.1 scar: test every variant, not just the fixture).
40. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` — the
    collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_cc_viewer.nim`, static assertions in the `test` job)

41. `chrome_common is byte-identical` — sha256 of `client/chrome_common.js` equals
    `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, pinned as a literal, and the file
    is 40 022 bytes.
42. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker (`replay_broadcast.html:4353`) and only appends after it;
    `broadcast_core.js`'s kept procs are byte-identical to the starter's, `pushFeed`'s signature
    included.
43. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (`replay_broadcast.html:1646`, the tandem hoisting trap); the beat
    builder is `ccBeat`, never `markBeat`.
44. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{stagestart, milestone, fall, stageend, fallback, end}`.
45. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the five `.tiny` rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#zoom-*`,
    `#povBadge`, `#fpv-hp`, `#fpv-gear`, `#fpv-map*`) appear nowhere, while the kept `#fpv`,
    `#fpv-canvas`, `#fpv-name`, `#fpv-cap` and `#fpv-grip` are all present.
46. `state JSON keeps ctf's keys` — the emitted state object contains every key
    `chrome_common.js` reads (`t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams,
    roster, events, lead, beats, lulls, over, hold`) with ctf's own names and types, and exactly one
    `teams` entry.
47. `endcard labels` — `tests/test_cc_endcard_labels.nim`: zero matches for the forbidden paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
48. `label manifest` — the starter's `test_label_contract` pattern: the emitted board-label vocabulary
    equals `tests/label_manifest.txt`, regenerated in the same commit as any label change.
49. `events are the closed enum` — `tests/test_cc_events.nim`: the set of kinds `stepEvents` can emit
    equals exactly the eleven listed in §Server, every kind used by the appended game block is in that
    set, and **no kind fires per tick**.

**Viewer smoke — the bundle is EXECUTED, not merely built**

50. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`) is run by **`ci.yml`'s `wasm-viewer` job**,
    which `needs: docker-smoke` (`templates/ci.yml:212`) and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned
    1.55.0 in both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay" --timeout 90
    --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"` (or the bridge
    `ready` posted after it) arrives, the clock/tick readouts **advance** across the soak, and
    `canvas_text.never_inside == 0` — this is a fixed-size board, so `--strict-text-bounds` stays on.
51. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, the CI replay's seat plays scripted and emits **no `say` at all**, so the smoke
    replay can never exercise the feed's narration path (the cogchemists 2026-08-24 scar). The fixture
    **loads the shipped `dist/static-replay-viewer/index.html` in an iframe** and shims only the wasm
    entry — it does not re-implement the drawing (the particle-worlds 2026-08-26 scar) — driving the real
    page with a full-cap 140-rune `say`, all three morphologies, all four stage-pip states, a `DOWN`
    banner, a `LINED OUT` endcard and a fallback glyph, at several canvas widths including 360 px.
52. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards, **and this repo is the one where they matter most**,
    because every frame of playback is a full 120-pass integer solver step re-run in wasm32.

---

## Out of scope (v1)

- **Any MuJoCo, `dm_control`, Gymnasium or Brax/MJX dependency, and bit-exactness with any of them.**
  Decided as a scoping rail and recorded in `docs/PHYSICS.md`: no upstream code is vendored, no upstream
  model XML is shipped or fetched, no upstream numbers are claimed as reproduced, and **no score from
  this coworld is comparable to a published HalfCheetah, Hopper or Walker2d return**. This coworld
  implements the problem, not the package.
- **Every 3-D morphology: Ant, Humanoid, Swimmer, quadruped, dog, and all of DMC's manipulation tasks.**
  The three shipped bodies are the planar half of the ladder. A 3-D body needs a quaternion state, a 3-D
  contact manifold and a 3-D renderer — three separate pieces of work, each of which would fork the
  determinism argument, the viewer's whole projection and the 360 px legibility story. "Fastest
  Humanoid" is not a v1 board; "fastest cheetah" is, and it is `stagePeakSpeed` plus the `lined`
  outcome.
- **Pixel observations.** DMC's pixel variants need a frame encoder in the player container; a
  proprioceptive coworld and a pixels coworld are different games with different policy interfaces.
- **A per-step continuous torque interface for RL policies.** The seat sends one gait order every 36
  ticks under a deterministic driver (§Sim module, divergence 5). A per-tick socket that accepts a raw
  6-vector of torques, and the numeric tensor observation to go with it, are exactly what
  `COGAME_EVENTS_URI`'s `Servo` rows exist to make possible **later**; they are not a v1 interface, and
  shipping one now would mean shipping a coworld with no LLM path, which the platform pin forbids.
- **Terrain, obstacles, wind, slopes and variable gravity.** The ground is one flat horizontal line, and
  that is what keeps the solver square-root-free and the determinism argument short. A rough-terrain
  variant is a good second coworld and is not this one.
- **Self-collision, joint friction beyond the servo's damping, actuator dynamics and motor delay.** All
  four are real in MuJoCo and none of them ships. Each adds constraint families whose integer behaviour
  would need its own soundness test, for gait realism that the readouts already convey.
- **A cross-episode highlight reel.** The idea asks for one; the falls are first-class beats, the fall
  hold plays at half speed and the gait card is the per-episode gait gallery, but stitching the best
  falls of a division into one video is a **site** feature over many replays, not a coworld feature, and
  it is not v1.
- **Tuning the physics from the league.** `tools/tune_gaits.nim` and `tools/tune_baselines.nim` sweep the
  gait table, the servo gains and the six baseline knobs; the morphology, solver and scoring constants
  are fixed and are asserted to equal the committed table. If a body cannot walk, the sweep moves, not
  the physics.
- **Scoring speed, strides, saturation or falls directly.** `stagePeakSpeed`, `stageStrides`,
  `saturatedTicks` and `falls` are measured, recorded in `results`, shown on the endcard and drawn in the
  feed, and deliberately **not** in `scores`. Paying for falls avoided would reward a cog that stands
  still for 19.5 seconds.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the hosted
  spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Guns, aim, vision cones, raycast fog, the
  first-person renderer, paint, hills, hearts, flags, grenades, med kits, shields, barriers, trenches,
  perks, handicaps, lives, teams, four-team play, shouts, achievements, campaign mode, multi-game
  episodes, the procedural map generator, the map pool, the map editor and mapkit — all deleted, not
  disabled (§Sim module), and none of them return in v1.
