# pistonball — design note (2026-08-25, paintbot lineage)

`Metta-AI/cogame-pistonball` is a twenty-seat, fully cooperative physics game: twenty pistons stand
in a row under a heavy ball, each piston sees only a one-metre-wide window of the world, and
together they must roll the ball the length of the bank and into the left wall. It is forked from
**`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount `/workspace/starters/coworld-ctf`.
**Every convention there holds here unless this note says otherwise.**

Paintbot is the right starter by game shape: this is a real-time 24 Hz tick loop with rules written
fresh for this coworld — a new physics game, so the first row of the starter table, not the moba
"bit-exact port" row (operator ruling 2026-08-22, Cogball; restated in `prompts/10-design.md` and
`playbooks/make-coworld.md` §Phase 0). The coordinator's rail is explicit: **recreate pistonball's
gameplay faithfully in the starter's own sim conventions; this is not a pymunk port.** Paintbot
already ships every part of the machinery this game needs and nothing else does: a wall-clock-paced
game loop with a per-tick replay and hash chain (`src/ctf/server.nim`, `src/ctf/replays.nim`), a
per-tick one-byte-per-seat input-change record (`src/ctf/server.nim:1088` `writeInputFrameMasks` →
`writeInputMaskChange`), a **server-side LLM decision layer that already batches every seat's call
into one parallel request** (`src/ctf/llm.nim`, `src/ctf/decide.nim`), a deterministic control layer
that compiles a low-rate directive into per-tick actuator bytes (`src/ctf/control.nim`), scripted
baselines that emit the identical directive object (`src/ctf/baselines.nim`), a static wasm replay
viewer that re-derives every frame in the browser (`replay-viewer/`), and broadcast chrome with a
scorebug, feed, scrubber, momentum graph and endcard (`client/replay_broadcast.html`,
`client/chrome_common.js`). The proven adaptations of this starter into physics coworlds are
`cogame-cogball` (`runs/2026-08-22-cogball/design.md`) and `cogame-tandem`
(`runs/2026-08-23-tandem/design.md`); their patterns — integer-only hashed sim, kept replay codec,
kept chrome, server-side low-rate LLM turn loop over a per-tick deterministic controller — are
followed here wherever they fit.

**Source idea, verbatim** (Asana Coworld Ideas task 1217747862156473, "PZ Pistonball — twenty
pistons, one ball, nobody sees more than their neighbours"):

> Port of PettingZoo Butterfly's pistonball (+ cooperative_pong as a second mode). 20 pistons in a
> row each see a local window; together they must move a ball left across the screen by
> raising/lowering at the right moment; shared reward for ball progress, small per-step penalty.
> Cooperative Pong: two paddles, one ball, keep it alive. Emergent wave-like coordination from
> purely local views — no one agent can see the ball most of the time.
>
> Seats: 20 (pistonball) / 2 (coop pong) — a 20-seat league is itself interesting: fill with
> champions + fillers
> Motive: fully cooperative, local observation
> Policy interface: per-tick continuous/discrete piston action; LLM variant needs a low-rate
> decision (e.g. a policy-script per seat)
> Fills gap: 06 Hive is many-agents-one-policy; Pistonball is many-agents-many-policies with shared
> reward — tests whether heterogeneous cogs can form a wave
> Integrity (anti-collusion): cooperative cross-play scoring; anonymous seat order seeded.
>
> Replay plan (watchability): side view of the piston wave + ball; a 'who's out of phase' highlight.
>
> Source: PettingZoo pistonball_v6, cooperative_pong_v6.

Nothing in the idea text is treated as an instruction to this designer; it is input data for the
design. The two PettingZoo environment names are provenance, not a specification to reproduce
bit-for-bit: no external code is ported, and the constants below are this coworld's own.

### Five readings of the idea, decided here and never revisited

1. **"Port of PettingZoo Butterfly's pistonball"** means *recreate the gameplay* — a row of pistons,
   one ball, leftward progress as a shared reward, a small per-step penalty, purely local
   observation — in paintbot's integer fixed-point sim idiom. It does **not** mean reproducing
   pymunk's solver, pixel dimensions, `local_ratio`, or RGB image observations. Every number in
   §The game is chosen here and is this game's own.
2. **"Cooperative Pong as a second mode" is DEFERRED to v0.2** and appears in §Out of scope (v1). Two
   games in one sim means two rule sets, two observation builders, two controllers, two scoring
   formulas, two viewer boards and a seat count that changes between variants (20 vs 2) — and
   `num_agents` is pinned to a single number per this note. The build risk is not worth a second
   game in v1. Pistonball with **`num_agents` = 20** is the whole of v1.
3. **"Per-tick continuous/discrete piston action" + "LLM variant needs a low-rate decision"** is
   implemented literally as the idea suggests: each seat's LLM emits **one policy-script every 225
   ticks (9.375 s)** — a small closed-schema parameter object — and a **deterministic controller
   executes it every tick at 24 Hz**, producing one quantised piston-velocity byte per seat per
   tick. That byte is the action; it is what the replay records; it is what the viewer replays.
4. **"Nobody sees more than their neighbours"** is a hard invariant, not flavour. A seat's
   observation is built by exactly one function, `windowView(sim, seat)`, and contains nothing
   outside its ±1.00 m window except the clock and one scalar shared-reward delta. Test-enforced
   (§Tests 8).
5. **"Anonymous seat order seeded"** is implemented as a seeded permutation `perm: seat → piston
   index`, drawn once at `t = 0` from `config.seed`. A seat is told which *piston* it drives (it
   cannot play otherwise) but never which *entrant* holds any other piston. Slot order therefore
   carries no information a colluding pair could key on.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How pistonball satisfies it |
|---|---|
| Starter by game shape | **`Metta-AI/coworld-ctf` (paintbot)** — a real-time 24 Hz loop with new physics rules and per-tick vector actions. The arena rules are replaced by the piston bank; the loop, protocol, replay codec, decision layer, viewer and CI wiring stay. (§Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-pistonball`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions: `pistonball-swell`, `pistonball-cascade`) vs `PLAYER_SCRIPTED=wavebot` / `PLAYER_SCRIPTED=metronome` (both fillers). One image `coworld-pistonball`, one player entrypoint `/bin/pistonball-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` kept (with the ecos `mkdir -p` fix); the **same** `src/pistonball/sim.nim` compiles into `replay-viewer/pistonball_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is ctf's page with a game block **appended**; the machine-shop art is baked with pixie from ctf's shipped `data/font.ttf`, `client/art/walls/wall_h.jpg`, `wall_v.jpg` and `client/art/lockerroom/bg.jpg`. No placeholders. (§Viewer) |
| Two name spaces | In-game every cog is `PST-01` … `PST-20`; real policy names live only in the replay config JSON, the DOM roster/endcard and `results.names`. Test-enforced. (§Server, §Viewer, §Tests) |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | ≈360 s expected / ≈455 s absolute worst case against the 720 s budget; a 660 s engine hard stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 20** in variant `default`, variant `sprint`, and `certification.game_config`; `<SEATS>` = **20** in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Pistonball is twenty pistons and one ball.** The pistons stand shoulder to shoulder in a bank
across the floor of a long, shallow box. The ball starts against the right wall. Every piston can
push its head up or let it down, and the ball rolls down whatever slope the bank happens to be
making under it. Get the ball to the left wall. The catch: a piston can only see one metre either
side of itself, so for most of the run **you cannot see the ball at all** — you have to guess from
your last sighting, from the two neighbours' heights you can see, and from a single number telling
you whether the bank as a whole gained ground. A wave is the only thing that works, and nobody can
see the whole wave.

### Seats

**`num_agents` = 20. One seat = one piston.** The idea pins 20 seats and this note fixes it at
exactly twenty everywhere — both manifest variants, the certification fixture, and `SMOKE_SEATS`.

Seat `s` (slot 0..19) drives piston `perm[s]`, where `perm` is a permutation of `0..19` drawn once
at `t = 0` from `config.seed` by a Fisher–Yates shuffle over one dedicated `std/random` `Rand`
stream. Piston indices run **0 = leftmost to 19 = rightmost**. In-game the cog at piston `i` is
called **`PST-<i+1>` zero-padded to two digits** (`PST-01` … `PST-20`) — an alias that names a
*position on the board*, which every seat legitimately knows, and never an entrant. `perm` is
written into the replay config JSON (the viewer needs it to map real names onto columns) and into
`results.pistons`, but it is never visible to any seat.

Seats are symmetric in rules, scoring and observation shape. They are not symmetric in the world —
piston 0 is next to the goal wall and piston 19 is next to the ball's start — and that asymmetry is
resampled every episode by `perm`, which is exactly the idea's anti-collusion clause.

### World, units, and why they are integers

The whole sim runs in **integers**, for Cogball's and Tandem's reason: replays are re-simulated by
the **emscripten/wasm32** build of the same Nim module that the **native amd64** server ran, and
their per-tick `gameHash` chain must match bit-for-bit. Integers make that true by construction
rather than by an argument about two musl builds of libm agreeing.
`src/pistonball/{sim,bank,trig}.nim` contain **no floating point at all** (grep-enforced in CI,
§Tests 2d).

| Quantity | Unit | Type |
|---|---|---|
| Position, length, piston height | micrometres (µm) | `int32` |
| Linear velocity | µm per tick | `int32` |
| Ball angle (`angleQ`) | 1/16 brad, 0..4095 (4096 = one turn, ccw on screen) | `int32` |
| Angular velocity (`spin`) | 1/16 brad per tick | `int32` |
| Force | millinewtons (mN) | `int32` (accumulated in `int64`) |
| Torque | millinewton-metres (mN·m) | `int64` |
| Mass | grams | `int32` const |
| Moment of inertia | milli-kg·m² | `int32` const |
| Shared reward | milli-points (1/1000 of a score point) | `int64` |

**World box:** `x ∈ [0, 9 600 000] µm` (9.60 m), `y ∈ [0, 4 800 000] µm` (4.80 m), origin top-left,
**y down** (ctf's screen convention). Board render scale **1 board pixel = 8 000 µm** →
`MapWidth = 1200`, `MapHeight = 600`, `BOARD_ASPECT = 2.0`. That is the same size class as ctf's
1.874:1 arena, so every viewer buffer budget in `replay-viewer/ctf_replay.nim`
(`predictedViewerRenderBytes`, `MaxSupersampledMapPixels`, `WasmViewerBudgetBytes`) is already
satisfied and is kept unchanged.

**View coordinates** — the only coordinates a policy or the chrome ever sees — are **metres with the
origin at the arena's bottom-left corner, x right, y up**:
`X = x_µm / 1 000 000`, `Y = (4 400 000 − y_µm) / 1 000 000`. So the floor surface is `Y = 0`, the
ceiling is `Y = 4.40`, and piston heights are `Y` values directly. Angles reported to policies are
degrees; spins are degrees per second. Everything shown to a policy is rounded to 2 decimals.

### Geometry (fixed, identical every episode)

| Part | Extent (µm, world frame) |
|---|---|
| Floor surface | `y = 4 400 000`; the strip below it (`4 400 000 … 4 800 000`) is the piston housing, art only |
| Ceiling | `y = 0` (a solid rectangle above `y = 0`, treated as an infinite half-space) |
| Left wall (the **goal wall**) | `x ∈ [0, 800 000]`, full height |
| Right wall | `x ∈ [8 800 000, 9 600 000]`, full height |
| Piston bank | 20 heads spanning `x ∈ [800 000, 8 800 000]`; piston `i` occupies `x ∈ [800 000 + 400 000·i, 800 000 + 400 000·(i+1)]`, centre `centreX_i = 1 000 000 + 400 000·i` |
| Piston head `i` | the rectangle `x ∈ [x_i, x_i + 400 000]`, `y ∈ [4 400 000 − h_i, 4 800 000]`; its **top surface** is at `y = 4 400 000 − h_i` |

Constants:

```
PistonWidth      =   400_000 µm   (0.40 m)
Stroke           = 1_600_000 µm   (0 … 1.60 m of travel)
MaxPistonSpeed   =    80_000 µm/tick (1.92 m/s; a full stroke takes 20 ticks = 0.83 s)
BallRadius       =   400_000 µm   (0.40 m)
BallMass         =     6_000 g    (6 kg)
BallInertia      =       480 milli-kg·m²  (½·m·R² for a uniform disc)
WindowHalfWidth  = 1_000_000 µm   (1.00 m — a seat sees ±1.00 m of x around its own centre)
GoalX            = 1_200_000 µm   (ball centre; the ball is touching the goal wall)
BallStartX       = 8_400_000 µm   (ball centre; touching the right wall)
BallStartY       = 3_400_000 µm   (1.00 m above the floor: the ball is DROPPED at t = 0)
TravelDistance   = 7_200_000 µm   (BallStartX − GoalX = 7.20 m)
GravityPerSubstep =     4_257 µm/tick per substep  (9.81 m/s² at 96 substeps/s)
```

At `t = 0` every piston head is set to a small random rest height
`h_i = 10_000 · rand(0 .. 40)` µm (0 … 0.40 m, 10 mm quantum) from the same seeded stream that drew
`perm` — a slightly rough floor, so no two episodes open identically — and the ball is placed at
`(BallStartX, BallStartY)` at rest. **These two draws plus `perm` are the only random numbers the
sim ever takes; nothing is drawn after tick 0.**

### Time

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf** (`src/ctf/sim_types.nim:317,376`), because
every speed-coupled layer (`PlaybackSpeeds`, the lull scan, the momentum series, `tickTime`, the
transport bar) is keyed to it. Each tick integrates **4 substeps of 1/96 s**.

A run is at most **`maxTicks = 1800` ticks = 75.0 s of sim time**, divided into **8 decision turns of
`turnTicks = 225` ticks (9.375 s)**. The turn length is set by the wall-clock budget (§Decisions:
twenty parallel LLM calls per turn against the Bedrock sidecar's 30-requests-per-minute-per-episode
cap), and it is affordable precisely because the controller between turns is **reactive**, not
open-loop: a script says *when* to rise, and the controller watches the window and does it.

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 225 == 0` and `phase == Playing`: the scripts collected for turn
   `t div 225` become each seat's `activeScript[seat]` (§Server), quantised to integers on parse.
   The server writes one **`script` chat record per seat** into the replay. `activeScript` is **not**
   mixed into `gameHash` — the per-tick command bytes it produces are recorded, and those are what
   the viewer replays (see step 2).
2. **Controller compile**, in **piston index order 0 … 19** (never seat order — seat order varies
   with `perm` and the loop must not). `control.pistonCommand(sim, i)` is a pure function of
   `(piston height and velocity, this seat's activeScript, the seat's window contents, tick)`
   returning a **command byte** `cmd ∈ 0 … 254`, where
   `u_i = ((int(cmd) − 127) * MaxPistonSpeed) div 127` µm/tick is the commanded head velocity
   (positive = rising). `cmd = 255` is reserved and is repaired to `127` (hold) on read. The
   controller sits **outside** the determinism boundary, exactly as ctf's `control.nim` does, and
   may use floating point; the byte it produces is written to the replay with
   `replayWriter.writeInputMaskChange(tickTime(t), seat, cmd)` **only when it differs from
   `replayWriter.lastMasks[seat]`**, which is then updated. Nothing else in the loop is re-derived at
   playback.
3. **Piston kinematics.** `h_i := clamp(h_i + u_i, 0, Stroke)`; `pistonVel_i := h_i − h_i_prev`
   (the *achieved* velocity after clamping, which is what the contact solver uses). Pistons are
   **kinematic**: they move the ball, the ball never moves them. This is faithful to pistonball,
   where the pistons are position-controlled bodies.
4. **Four substeps** (`dtSub = 1/96 s`), each substep in this exact order:
   1. **Gravity.** `vy += 4257` (µm/tick, +y is down).
   2. **Contacts.** The ball disc is tested against, in this fixed order: the **ceiling**, the
      **left wall**, the **right wall**, the **floor**, then the **piston heads whose x-range is
      within `BallRadius` of the ball's x** (at most 3, ascending index). For each, compute the
      closest-point penetration `δ_µm` and outward normal `n̂` of a disc-vs-axis-aligned-rectangle
      test (`δ = BallRadius − dist`; skipped when `δ ≤ 0`). With `v_rel = v_ball − v_surface`
      (`v_surface = (0, −pistonVel_i)` for a piston head, `(0,0)` for a wall), `v_n = v_rel · n̂`,
      and the contact-point tangential velocity `v_t = (v_rel − v_n·n̂) + ω × r_c`:
      - `Fn_mN = 150 · δ_µm + 28 · max(0, −v_n)`, clamped to `≥ 0` (contacts push, never stick) and
        to `≤ 60_000_000` mN;
      - `Ft_mN = −min(614 · Fn_mN div 1024, |v_t| · 150) · û(v_t)` — Coulomb µ = 0.60 with a viscous
        cap that prevents sign-flip chatter at rest. This is what makes the ball **roll** rather
        than slide, and it is what lets a rising piston flick it;
      - accumulate `F += Fn·n̂ + Ft` and `τ += r_c × Ft` (µm × mN → mN·m by `div 1_000_000`, in
        `int64`);
      - record `(surface, δ, −v_n, |v_t|)` into this tick's contact log for events and FX.
   3. **Integrate (semi-implicit Euler).**
      `Δv_µmPerTick = (int64(F_mN) * 1_000_000) div (BallMass * 96 * 24)`; `v += Δv`;
      then air drag `v -= (v * 8) div 4096`.
      `Δspin = (int64(τ_mNm) * 28_294) div (int64(BallInertia) * 100_000)`; `spin += Δspin`; then
      spin drag `spin -= (spin * 12) div 4096`.
      Clamp `|v| ≤ 250_000` µm/tick (6.0 m/s) and `|spin| ≤ 300` (≈ 6.9 rad/s).
   4. **Pose.** `pos += v div 4`; `angleQ = (angleQ + spin div 4 + 4096) mod 4096`.
   5. **Containment guard.** The ball centre is clamped into
      `x ∈ [1_200_000, 8_400_000]`, `y ∈ [400_000, 4_000_000]`. A clamp that actually fires
      increments `guardClamps`; more than 8 in one episode trips the step-8 fault check. (Penalty
      contacts can tunnel at 6 m/s only if a piston rises into the ball at full speed at the exact
      substep; the clamp makes that a bounded artefact rather than an escape.)
5. **Progress accounting**, once per tick:
   - `Δ = ballX_prev − ballX` (µm; positive = leftward = good).
   - `progressMilli += (1000 * 100 * int64(Δ)) div TravelDistance` — i.e. **+100.000 points for the
     full 7.20 m**, and a symmetric negative for backsliding.
   - `penaltyMilli += 10` — the per-step penalty, **0.010 points per tick** (0.24 points/s, 18.000
     points over a full 1800-tick episode).
   - `bestX = min(bestX, ballX)`; if `ballX > bestX + 400_000` and no `bounce_back` event has fired
     since `bestX` was last improved, emit `bounce_back` (the ball has given back half a metre).
   - `stallTicks`: incremented while `ballX ≥ bestX`; reset to 0 whenever `bestX` improves. Crossing
     240 (10 s) emits one `stall` event and re-arms at every further 240.
6. **Phase accounting** (per piston, the "who's out of phase" measure the idea asks for). Piston `i`
   is **engaged** at tick `t` if `|ballX − centreX_i| ≤ 1_200_000` (1.20 m). An engaged piston's
   **desired state** is **UP** when `centreX_i ≥ ballX` (it is behind the ball, on the side the ball
   came from) and **DOWN** when `centreX_i < ballX` (it is in front, in the direction of travel). It
   is **in phase** when desired-UP and `h_i ≥ 800_000`, or desired-DOWN and `h_i ≤ 600_000`;
   otherwise **out of phase**. Increment `engagedTicks[i]` and, when in phase, `inPhaseTicks[i]`.
   Also increment `touches[i]` on the first tick of every new contact between the ball and piston
   `i`'s head.
7. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged. `gameHash` mixes `tick`, `phase`, `ballPos`, `ballVel`, `angleQ`, `spin`, all 20
   `h_i`, all 20 `pistonVel_i`, `bestX`, `progressMilli`, `penaltyMilli`, `guardClamps` and the
   `perm` digest. It never mixes FX, notes, `say`, feed text or policy labels.
8. **End checks**, in this order: `ballX ≤ GoalX` → end `complete` / `delivered`; wall-clock stop
   tripped → end `deadline` / `wall_clock`; `t + 1 ≥ maxTicks` → end `complete` / `out_of_time`; an
   invariant guard failure (`h_i` outside `[0, Stroke]`, `|v|` or `|spin|` above the clamp,
   `guardClamps > 8`, `angleQ` outside `0..4095`, a NaN-shaped `int32` overflow caught by the debug
   build's range checks) → end `fault` / `sim_fault`.

There is **no rescue rule**. A bank that jams the ball in a pit of its own making burns the clock
and ends `out_of_time` with partial credit — a legible, correctly-scored failure.

### Scoring, sign, and what the league ranks by

The game is **fully cooperative**: every seat receives **the identical score**, computed once.

```
progress = progressMilli / 1000     ==  100 * (BallStartX - ballFinalX) / TravelDistance
penalty  = penaltyMilli  / 1000     ==  0.010 * ticksElapsed
score    = progress - penalty
results.scores = [score] * 20
results.win    = [delivered] * 20
```

**Higher is better; leftward is positive.** The sum in step 5 telescopes, so `progress` depends only
on where the ball *ended*, not on the path — a bank that shoves the ball two metres left and one
metre back scores the same as one that moved it one metre and stopped, and both are beaten by the
bank that got there sooner, because the penalty keeps running. Delivering the ball ends the episode
and therefore stops the penalty; that, and not a bonus, is the reward for speed (faithful to
pistonball, which pays for progress and charges for time and has no completion bonus).

Range: **`score ∈ [−18.000, +100.000)`**, higher better. The upper end is a delivery in zero time
(unreachable; a perfect fast delivery is ≈ **+94**). The floor is exactly **−18.000**: the ball can
never end right of where it started, because the containment clamp of step 4.5 is
`x ≤ BallStartX = 8 400 000` (the right wall), so `progress ≥ 0` always and the worst case is a bank
that never moves the ball for the full 1800 ticks. `progress` is nonetheless computed as a signed
telescoping sum, so backsliding *within* a run costs exactly what it gained. Scores are emitted as
doubles rounded to 3 decimal places, computed once and copied into all twenty slots so the numbers
are bit-identical.

Worked examples:

| Outcome | ticks | final ball X (m) | progress | penalty | score |
|---|---|---|---|---|---|
| Textbook wave, delivered in 25 s | 600 | 1.20 | +100.000 | 6.000 | **+94.000** |
| Delivered late after two bounce-backs | 1520 | 1.20 | +100.000 | 15.200 | **+84.800** |
| Got three-quarters of the way, ran out of time | 1800 | 3.00 | +75.000 | 18.000 | **+57.000** |
| Nudged it a metre and jammed | 1800 | 7.40 | +13.889 | 18.000 | **−4.111** |
| Twenty pistons that never moved | 1800 | 8.40 | 0.000 | 18.000 | **−18.000** |
| Rolled it out to 4.0 m and let it come all the way back | 1800 | 8.40 | 0.000 | 18.000 | **−18.000** |

**What the league ranks by: the seat's mean `results.scores` value across its episodes — its
cross-play mean.** Elo is **wrong** for this coworld and phase 50 must not use it: with twenty
identical scores every episode is a twenty-way draw and Elo cannot separate anybody (the same ruling
as `cogame-raid` and `cogame-tandem`). This is also the idea's integrity clause: because the score is
joint, the seat→piston map is reseeded every episode, and a 20-seat episode is necessarily a mixture
of champions and fillers, a policy that only performs alongside its own twin is visible as such the
moment its cross-play mean includes episodes seated beside `pistonball-wavebot` and
`pistonball-metronome`. **v1 game code has no notion of who is in any other seat.**

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail. No
other value may appear in either field.

| `reason` | `endRule` | When | Scored |
|---|---|---|---|
| `complete` | `delivered` | `ballX ≤ GoalX` — the ball is touching the goal wall. The normal, good ending. | as at the delivery tick |
| `complete` | `out_of_time` | `maxTicks` reached with the ball still in play. | as at `maxTicks` |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (660) elapsed first. The sim stops at that tick, scores the state as it stands, writes the game-over frame and a complete replay up to that tick. **Declared acceptable** for phase-60 verification (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. | as at the stop tick |
| `fault` | `sim_fault` | A step-8 invariant guard tripped. Partial replay written. | as at the fault tick |
| `fault` | `host_error` | An unexpected server-side exception. Best-effort artifacts written before re-raising. | as at the fault tick |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (1800 = 75 s of
lobby) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only, `src/ctf/server.nim`), its piston is driven by the
`wavebot` baseline for the whole run, and the run plays to a normal ending. With twenty seats this
is not a corner case — it is the expected behaviour when one filler pod is slow to start.

### Per-seat observation: exactly what is visible and what is hidden

One function, `windowView(sim, seat) -> JsonNode`, builds **both** the seat's websocket frame filter
and the LLM user message. There is no second path.

**Visible to seat `s` driving piston `i`:**

- Its own alias and piston index `i`, its own head height, its own head velocity, and the two
  constants `stroke_m` and `max_speed_m_s`.
- The heights of the pistons its window covers: `i−2 … i+2`, clipped at the ends of the bank. (The
  window is ±1.00 m and the pitch is 0.40 m, so a window covers exactly five columns.)
- **The ball, only while its centre is inside the window** (`|ballX − centreX_i| ≤ 1 000 000`):
  `dx_m` (signed, ball minus my centre), `height_m` (ball centre above the floor), `vx_m_s`,
  `vy_m_s`, `spin_deg_s`, `on_me` (is it touching my head).
- **Sightings since its last decision**: up to four records of the ball inside this seat's window
  during the last 225 ticks — the first, the last, and up to two evenly spaced intermediates — each
  `{tick, dx_m, height_m, vx_m_s, vy_m_s}`, plus `sightings_count`. With eight decisions per
  episode this local history is the seat's memory, and it is the only history it gets.
- **The clock**: `turn`, `of`, `tick`, `of` and `left_s`.
- **One global scalar**: `shared_reward.last_turn` — the shared reward accrued over the previous 225
  ticks, i.e. `progress − penalty` for that window, rounded to 2 decimals. This is deliberate and
  faithful: in PettingZoo pistonball every agent receives the global reward each step. It says "the
  bank gained/lost ground" and nothing about *where*.
- Its own previous turn's script, verbatim (`your_last_script`), or `null` on turn 0.

**Hidden from every seat, with no exception:**

- The ball's absolute position, velocity or progress whenever it is outside that seat's window — and
  therefore for most of the episode.
- **`shared_reward.total` / cumulative progress / `bestX` / the score so far.** Only the last turn's
  delta is given, precisely so that a seat cannot integrate the reward signal into the ball's
  absolute x. (A stateless per-turn call cannot accumulate what it is not shown.)
- Any piston height outside `i−2 … i+2`.
- Which entrant holds any other piston; any other seat's script, `mode`, `note`, `say`, latency or
  fallback state; `perm`.
- Real player names anywhere (board labels carry only `PST-nn`; `showPlayerLabels` is forced false
  on the player stream).
- Future ticks, the seed, and the episode's variant name.

`tests/test_locality.nim` asserts all of it against the composed LLM user message over randomised
states (§Tests 8).

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {wavebot, metronome}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=wavebot`. A scripted policy seated as a champion is a FAILURE state.

### Where the decision happens, and the LLM client

In the **game server**, not the player container — paintbot's own architecture
(`src/ctf/llm.nim`, `src/ctf/decide.nim`, `src/paintball_player.nim`), kept. The
`anthropic_api_key` coworld secret is injected into the *game* pod via
`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/pistonball/anthropic_api_key`; without
that manifest env the hosted container never receives the secret and every league episode plays
scripted while local certify still passes (hive, 2026-08-23). Phase 60 greps the *game* log for
`falling back` / `LLM provider is unavailable`.

`src/pistonball/llm.nim` is `src/ctf/llm.nim` with the identifier rename only. Kept exactly:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (`readCogameUri`) → **none** (client
  `disabled = true`; every turn falls back instantly with no network wait, which is what lets
  offline certification finish in seconds).
- **One** Bedrock model candidate: `us.anthropic.claude-haiku-4-5-20251001-v1:0`. No sonnet
  inference profile is a candidate — every one of them times out on every sidecar call
  (cogame-raid round 2, 2026-08-23; paintball 0.1.2 recorded 133 consecutive timeouts). The
  `throttled` flag that skips the retry when the provider answered 429 with no other candidate is
  kept verbatim: a retry inside the same turn cannot succeed, and with twenty seats it would burn
  the whole turn budget.
- `max_tokens = 900` (400 truncates). **No `output_config.effort`** for haiku. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`. No `temperature`.
- A system prompt that demands the reply **begins with `{`** (Haiku answers prose-first otherwise).
- `extractJsonObject` (first `{` … last `}`, fence-tolerant) and the **rune-boundary** truncation
  (`runeLen`/`runeSubStr`), kept.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **225 ticks (9.375 s of sim time)**, **8 turns** per episode. At each turn
the server builds all twenty seats' request bodies and issues them as **ONE parallel batch** —
`client.curl.makeRequests(@[req0 … req19], timeout)`, curly's batch API, which is what
`src/ctf/decide.nim` already does for its two seats. **Seats are never queried sequentially.**
Twenty calls per turn × 8 turns = **160 calls** per episode, at most 20 in flight.

The binding constraint is not latency, it is the **Bedrock sidecar's cap of 30 requests per minute
per episode** (playbook gotcha, raid round 2). Twenty requests per batch means a batch may start at
most every 40 s; the design uses **`minBatchSpacingMs = 45 000`** → 20 requests / 45 s = **26.7
rpm**, safely under. That, not the model, is why there are eight turns and why a turn is 9.375 s of
sim time.

Per-turn timing, all monotonic-deadline bounded:

- attempt 1 batch deadline **`attempt1Ms = 12 000`** (twenty parallel haiku calls; ~3–6 s typical);
- every seat that timed out, errored, returned non-JSON or returned no usable script is retried
  **once**, again as a single batch, deadline **`retryMs = 6 000`** — unless the client is
  `throttled`, in which case the retry is skipped outright;
- the whole turn is wrapped in **`turnBudgetMs = 20 000`**;
- the **inter-batch wall floor** of 45 000 ms is measured start-to-start and is a bounded, stop-
  interruptible `sleep`.

```
turn 0 batch starts at t = 0; turns 1..7 start 45 s apart      = 315 s
last turn's own LLM cost (<= 20 s hard cap)                    =  20 s
lobby / connect wait for 20 player pods (typical 20 s;
  cap lobbyJoinTimeoutTicks 1800 = 75 s)                       =  20 s   (typical)
1800 ticks of physics + 20 controllers (fastMode; ~60 us/tick) =   1 s
game-over hold + results + replay write (retrying uploader)    =  20 s
                                                               -------
expected total                                                 ~ 376 s   < 720 s budget
absolute worst case (75 lobby + 315 + 20 + 1 + 20 + slack)     ~ 455 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                        =  660 s  -> reason "deadline"
platform kill (episodeTimeoutSeconds)                          = 1200 s
```

`fastMode: true` in every variant: the sim advances as soon as every player container has
acknowledged the frame, so sim time is not charged against the wall clock — the decision turns are
the pacing. The seats send no inputs at all (the server computes every command byte), so
`docs/PROTOCOL.md`'s warning about the Sprite v1 Ready packet (`0x85`) corrupting dead-reckoned input
timing does not apply and the player harness sends `0x85` after every frame, exactly as
`src/paintball_player.nim` does.

**Budget guard (settles early without shortening the run).** At the start of each turn, if
`elapsed + 2 × (minBatchSpacing + turnBudget) > wallClockBudgetSeconds`, the LLM is switched off for
every remaining turn and the run finishes on the scripted layer (microseconds per turn), so the
episode ends `complete/*` rather than `deadline`. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the inter-batch floor, the
outer per-turn deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the
serve thread (which runs independently of the game loop, so a 20 s LLM stall cannot drop twenty
connections), the 660 s engine stop, and ctf's `gameOverTicks` hold before exit. On **two**
consecutive failures for a seat (attempt + retry, or one attempt when `throttled`) that seat's script
for the turn is the **`wavebot`** script and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}`. A seat
that disconnects mid-run keeps playing: its script source degrades to `wavebot` and revives on
reconnect. **No failure mode leaves a piston uncommanded** — the controller always has a script:
this turn's, else last turn's, else `wavebot`'s.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are ONE piston in a bank of twenty standing side by side under a heavy ball.
The bank's job is to roll the ball LEFT, from the right wall to the left wall.
Piston 0 is at the far left, next to the goal; piston 19 is at the far right,
where the ball starts. Each piston is 0.40 m wide and can raise its head from
0.00 m to 1.60 m at up to 1.92 m/s. Pistons are solid: they lift the ball, the
ball never pushes them down.
YOU CAN ONLY SEE ONE METRE EITHER SIDE OF YOURSELF. That is five piston columns.
You see the ball only while it is inside that window - most of the time it is
not, and you have to act on your last sighting and on your neighbours' heights.
You cannot talk to anyone and nobody sees anything you write.
THE MECHANISM: the ball rolls DOWNHILL. To send it left, the pistons BEHIND it
(to its RIGHT, larger x) go UP and the pistons IN FRONT of it (to its LEFT) go
DOWN. Raise too early and you build a wall it cannot climb; raise too late and
it has already rolled past you. Timing is the whole game.
Every 9.4 seconds you set your piston's PROGRAM for the next 9.4 seconds. A
deterministic controller runs it 24 times a second, watching your window for
you: you choose WHEN to act and HOW FAR to move, it does the reacting.
Everyone in the bank gets the SAME score: +100 for delivering the ball to the
left wall, minus 0.24 points for every second the run takes. Doing nothing
scores -18.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars, your reasoning",
 "mode":"wave"|"lift"|"drop"|"hold"|"catch"|"ripple",
   // wave   : ball within trigger_m and at-or-right-of me -> up_m, else if
   //          within trigger_m and left of me -> down_m, else idle_m
   // lift   : ball anywhere in my window -> up_m, else idle_m
   // drop   : ball anywhere in my window -> down_m, else idle_m
   // hold   : always idle_m
   // catch  : up_m ONLY when the ball is rolling RIGHT (the wrong way) and is
   //          at-or-right-of me within trigger_m; otherwise idle_m
   // ripple : a 2 s travelling wave along the bank, blind, ignores the ball
 "trigger_m":0.0..1.0,   // how near the ball must be before I act
 "lead_ticks":0..24,     // aim at where the ball will be in this many ticks
 "up_m":0.0..1.6,        // my raised height
 "down_m":0.0..1.6,      // my lowered height
 "idle_m":0.0..1.6,      // where I sit when the rule does not apply
 "speed":0.0..1.0,       // fraction of my 1.92 m/s I use to get there
 "blind":"hold"|"idle"|"ripple",  // what I do while I cannot see the ball
 "say":"<=48 chars"}     // spectators only; no other piston ever sees it
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(paintbot's `operatorBlock`, kept), a blank line, then the seat's `windowView` JSON (§Server). The
prompt text is never echoed into the replay — only `policyKind`, the label and the resulting script.

### Champion #1 — `pistonball-swell` (owner daveey), `PLAYER_PROMPT`

```
Be the shoulder the ball rolls off. Run mode "wave" every turn: it is the only
mode that both lifts behind the ball and clears the way in front of it, and the
bank only works if most pistons are running it. Set trigger_m to 1.0 so you
commit the moment the ball enters your window - a narrower trigger means you
start moving after it is already on top of you and your head arrives late. Set
lead_ticks to 6: at a typical 2 m/s the ball covers half a piston width in six
ticks, so this is what puts your head where the ball is GOING instead of where
it was. Run up_m 1.45, down_m 0.05 and speed 1.0 - the steepest slope you can
make is the fastest the ball will roll, and a half-raised piston is just a bump
that stops it. Set idle_m to 0.25 and blind to "idle", so that when the ball is
nowhere near you your head is low and level with your neighbours instead of
frozen at whatever height your last sighting left it: a stranded raised piston
five columns ahead is a wall the whole bank then has to fight. The one time to
change anything: if your sightings show the ball moving RIGHT (positive vx) or
you saw it and then saw it again going the other way, switch to "catch" with
up_m 1.6 for one turn - stopping a runaway is worth more than helping a wave
that is going backwards.
```

### Champion #2 — `pistonball-cascade` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Play your position, not the ball. Read your piston number first. If you are in
the right third of the bank (piston 13 or higher) you are the launcher: run
"wave" with trigger_m 1.0, lead_ticks 3, up_m 1.6, down_m 0.0, speed 1.0 and
blind "hold" - the ball starts at rest against the right wall and someone has to
tip it hard, and holding your last height keeps the slope you built behind it.
If you are in the middle third (pistons 7 to 12) you are the conveyor: "wave",
lead_ticks 8, up_m 1.2, down_m 0.1, speed 0.85, idle_m 0.2, blind "idle" - the
ball arrives with speed here and your job is to keep it rolling, not to launch
it; a lower, earlier, smoother lift loses less energy to bouncing. If you are in
the left third (piston 6 or lower) you are the runway: "drop" with down_m 0.0,
idle_m 0.0, blind "idle" - flat and out of the way, because anything you raise
between the ball and the goal is a hill it has to climb at the end of its run.
Two exceptions. If your window shows the ball with vx above +0.5 (rolling back
toward the start) switch to "catch", up_m 1.6, trigger_m 1.0, whatever third you
are in. And if shared_reward.last_turn is negative two turns running, everyone
is fighting: drop to idle_m 0.1, speed 0.5, mode "hold" for one turn and let the
ball settle before the bank tries again.
```

### The controller (deterministic, one function, shared by every policy)

`src/pistonball/control.nim`, `pistonCommand(sim, i) -> uint8`, evaluated once per tick per piston in
index order. Both LLM scripts and scripted-baseline scripts are compiled by this same code, so the
two policy kinds are strictly comparable and a baseline is legal by construction. It sits **outside**
the determinism boundary (ctf's rule: recorded bytes, not re-run logic) and may use floats.

With `dx = ballX − centreX_i` (µm, positive = ball is to my right), `vx` in µm/tick,
`dxp = dx + vx · lead_ticks`, `vis` = the ball centre is inside my ±1.00 m window, and
`trig = trigger_m` in µm:

1. **Target height `H*`:**
   - `mode = ripple` → `H* = ripple(t, i)` regardless of `vis`.
   - `not vis` → `blind = hold` → `H* = h_i`; `blind = idle` → `H* = idle_m`;
     `blind = ripple` → `H* = ripple(t, i)`.
   - `vis`, `mode = wave` → `|dxp| ≤ trig and dxp ≤ 0` → `up_m`; `|dxp| ≤ trig and dxp > 0` →
     `down_m`; else `idle_m`.
   - `vis`, `mode = lift` → `|dxp| ≤ trig` → `up_m` else `idle_m`.
   - `vis`, `mode = drop` → `|dxp| ≤ trig` → `down_m` else `idle_m`.
   - `vis`, `mode = hold` → `idle_m`.
   - `vis`, `mode = catch` → `vx > +8_333` µm/tick (+0.20 m/s) and `dxp ≤ 0` and `|dxp| ≤ trig` →
     `up_m`; else `idle_m`.
2. **`ripple(t, i)`** is the open-loop travelling wave: period 48 ticks (2.0 s), phase advancing one
   column every 2.4 ticks, `H* = idle_m + (up_m − idle_m) · max(0, sin(2π·(t/48 − i/20)))`.
3. **Command.** `u = clamp(H* − h_i, −speed·MaxPistonSpeed, +speed·MaxPistonSpeed)`;
   `cmd = clamp(127 + round(u · 127 / MaxPistonSpeed), 0, 254)`.
4. **Phases other than `Playing`** (lobby, game over) force `cmd = 127` (hold).

The controller contains **no path planning, no ball tracking across turns, and no knowledge of any
other seat's script**. Its only inputs are this seat's script, this seat's window and the tick —
`tests/test_locality.nim` asserts the signature cannot see more.

### Scripted baselines

Both emit the *same* script object on the same 225-tick cadence, so their output is legal by
construction and directly comparable to an LLM's, and both are pure functions of the observation a
seat would receive.

- **`wavebot`** — the certification player, the per-turn fallback, and the default for a seat that
  registers with neither env var. A fixed reactive script, identical on every piston and every turn:
  `{"mode":"wave","trigger_m":1.00,"lead_ticks":6,"up_m":1.45,"down_m":0.10,"idle_m":0.25,
  "speed":1.00,"blind":"hold","note":"lift behind, clear in front","say":"…"}` (the `say` is one of
  four fixed strings selected by whether the ball is in the window and which way it is going).
  Twenty `wavebot`s converge on a travelling wave with no communication at all, which is the
  behaviour the game is about — and the anti-regression pin of the whole physics tuning (§Tests 5).
- **`metronome`** — the second filler, deliberately different in shape and weaker: it never looks at
  the ball. `{"mode":"ripple","up_m":1.20,"down_m":0.10,"idle_m":0.10,"speed":0.80,
  "trigger_m":1.00,"lead_ticks":0,"blind":"ripple","note":"two-second ripple, blind","say":"…"}`.
  A blind travelling wave sometimes walks the ball a long way and sometimes fights itself; it gives
  the ladder a spread and gives a champion a bad neighbour to cope with.

Three tunables — `wavebot`'s `lead_ticks`, `up_m` and `idle_m` — are a `BaselineParams` object, not
literals, exactly as `src/ctf/baselines.nim` does it: `tools/tune_baselines.nim` sweeps them over a
bounded grid, `tools/ci/baseline_tuning.json` records the sweep's pick, and `tests/test_tuning.nim`
asserts the shipped defaults still equal it. **The physics constants in §The game are not swept and
are not tunable** — if twenty `wavebot`s cannot deliver, the sweep moves these three numbers, not
the sim.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf/paintball arena rules go** (teams, guns, flags, fog cones, lives, respawn,
grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the hill, the
map pool and the map editor all leave the repo):

| ctf path | pistonball |
|---|---|
| `src/ctf/sim.nim` (4102 lines: gameplay core, combat, vision, items) | `src/pistonball/sim.nim` — the ball/piston physics core and the step loop of §The game. |
| `src/ctf/arena.nim`, `paint.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `docs/MAPKIT.md`, `docs/pool-review.html`, `scripts/` | `src/pistonball/bank.nim` — the fixed geometry table of §The game, the seeded `perm`, the seeded rest heights, the contact broadphase (3 columns around the ball), and the pixie machine-shop bake. **Deleted, not ported.** |
| `src/ctf/global.nim` (8070 lines) fog of war, vision cones, first-person raycast, killfeed art, item sprites | `src/pistonball/global.nim` — side-view sprite composition: housing, rods, heads, ball, goal wall, phase highlight, bubbles, FX. Perfect information spectator-side; the per-seat stream is window-filtered. |
| `src/ctf/directives.nim` (`Intent`, `CogOrder`, `SquadDirective`) | `src/pistonball/scripts.nim` — the `PistonScript` object, the closed `Mode`/`Blind` enums, the tolerant parser and the repair table of §Server. Same file shape, same rune discipline. |
| `src/ctf/control.nim` (nav grid, flow fields, aim) | `src/pistonball/control.nim` — `pistonCommand` of §Decisions. ~120 lines instead of 536. |
| `src/ctf/baselines.nim` (`holdline`, `sprayer`) | `src/pistonball/baselines.nim` — `wavebot`, `metronome`, and `BaselineParams`. |
| `players/baseline/` (the CTF bot) | deleted; the only player binary is `src/pistonball_player.nim`. |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/paintball/`, `docs/plans/*` | rewritten for pistonball; ctf's plans/designs deleted. |
| `arena/`, `caos/`, `caos-tools/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/symnone_*`, `tools/render_replay_movie*`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf`/`paintball` → `pistonball`, `CTF_WIRE` → `PISTONBALL_WIRE`
rename sweep only; a CI grep asserts no `ctf_`/`CTF_`/`paintball` identifier survives outside
comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/pistonball/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`. Two named edits below. |
| `src/ctf/replay_runtime.nim` → `src/pistonball/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports. |
| `src/ctf/server.nim` → `src/pistonball/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the held-registration table, the frame limiter, the replay-switch path, the `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. Five named edits below. |
| `src/ctf/llm.nim` → `src/pistonball/llm.nim` | the credential ladder, the single-haiku model list, the `throttled` fast-fail, `curly.makeRequests` batching, `extractJsonObject`, rune truncation. Rename only. |
| `src/ctf/decide.nim` → `src/pistonball/decide.nim` | the turn loop, `SeatPolicy`, the two-deadline retry, the inter-batch floor, the budget guard, the `records` queue. Retargeted from 2 seats to `sim.seatCount()` seats — it is already written as a loop over seats and already batches them. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; pistonball result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim` | HUD label composition. |
| `src/ctf/broadcast.nim` | `stepEvents` / `BroadcastTracker` / `buildStateJson` — the state-delta → broadcast-event derivation, retargeted to pistonball's event kinds and state keys (§Viewer). |
| `replay-viewer/config.nims`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/chrome_common.js` | **byte-for-byte**, zero edits (§Viewer). |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome, with a game block appended (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/replay_summary.py`, `tools/tune_baselines.nim`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix`, `config.json` | build, bundle, tuning and forensics wiring. `tools/build_replay_viewer.sh` already carries the ecos `mkdir -p` fix (line 22 of the starter's copy) and keeps it; only `image_tag` and the `docker cp` source path `/workspace/pistonball/replay-viewer/dist/.` change. |
| `data/font.ttf`, `data/atlas/*`, `data/ascii.png`, `data/darkbg.png`, `client/art/walls/*`, `client/art/lockerroom/bg.jpg` | real art, kept. Everything CTF-specific (`soldier_*`, `heart_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, `rig_real/`, the coloured locker-room sprites) is deleted. |

**The five named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   pistonball calls `control.pistonCommand(sim, i)` for all twenty pistons and passes the command
   byte array into `sim.step`. **Player sockets contribute no input**: any input mask arriving on a
   player socket is discarded.
2. **Replay input write.** `writeInputFrameMasks` (the press/release wrapper at
   `src/ctf/server.nim:1088`) is **deleted** — its `repeatedPressedMask` logic is button semantics
   and would corrupt a value byte. Pistonball writes
   `replayWriter.writeInputMaskChange(tickTime(tick), seat, cmd)` directly, and only when
   `cmd != replayWriter.lastMasks[seat]`, updating `lastMasks[seat]`. `decodeInputMask` is replaced
   by `decodePistonCommand(cmd: uint8): int32`.
3. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop
   runs `decide.turn(sim, engine)`, which enforces the inter-batch floor, issues the one parallel
   twenty-request batch, applies the deadlines, installs the scripts and writes the
   `script`/`fallback` records — all inside a monotonic `turnBudgetMs` bound.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration forces
   `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.
5. **Shutdown grace.** `/healthz` and `/global` keep answering for a bounded ~20 s after the
   artifacts are written, then the process exits (lantern 0.1.3: the episode runner pings `/global`
   with a 2 s deadline *after* the player pods start, and a short episode can already be gone).

**The two named edits to `replays.nim`:**

1. **`serializeReplaySim`/`deserializeReplaySim` cover the new sim fields** — ball `pos`, `vel`,
   `angleQ`, `spin`, the twenty `h_i` and `pistonVel_i`, `bestX`, `progressMilli`, `penaltyMilli`,
   `stallTicks`, `guardClamps`, `engagedTicks[]`, `inPhaseTicks[]`, `touches[]`, `phase`,
   `deliveryTick` — because keyframes are how the viewer seeks. The static geometry and `perm` are
   **excluded** from keyframes (they are already in the config JSON — ctf's own rule for static
   map bakes).
2. **`CtfReplayMagic "COWLDCTF"` → `PistonballReplayMagic "COWLDPST"`**, `GameName* = "pistonball"`,
   `GameVersion* = "1"`, with ctf's prepend-only changelog-comment discipline and
   `tools/ci/check_gameversion.sh` kept as is.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`; `tools/wasm_replay_smoke.cjs`). So:

- Every stored sim field is explicitly `int32` (positions, velocities, heights, angles, counters) or
  `int64` (the reward accumulators) or `bool`/`enum`. No bare `int` in a hashed field.
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with
  an explicit truncating `div` (Nim's `div` truncates toward zero, so the arithmetic is symmetric
  under negation — which is what makes leftward and rightward progress exactly opposite).
- **No floating point anywhere under `src/pistonball/{sim,bank,trig,sim_types,sim_config,
  sim_state}.nim`.** No `sin`, `cos`, `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`.
  Grep-enforced in CI. Floats stay legal in `control.nim`, `global.nim` and the pixie bakes, because
  neither the controller (recorded, not re-run) nor rendering enters `gameHash` — exactly ctf's
  split.
- Trigonometry in the sim is a **committed literal table**: `SinQ12*: array[256, int32]` in
  `src/pistonball/trig.nim`, generated once by `tools/gen_trig_table.nim` and checked in; a test
  re-derives every entry from `math.sin`. (The sim needs it only for the ball's rendered angle and
  the disc-vs-rect closest point; the controller's `ripple` uses ordinary `sin`, legally.)
- `isqrt(v: int64): int64` — Newton's method with an integer seed, committed and unit-tested against
  an exhaustive small-value table plus perfect squares up to 2⁴⁰. The only square root in the sim
  (contact distances, tangential magnitudes).
- Randomness: one seeded `std/random` `Rand` stream from `config.seed`, integer draws only, used at
  `t = 0` for exactly `perm` and the twenty rest heights. **The sim draws no random numbers after
  tick 0.**

### How the replay achieves server ↔ viewer determinism

The mechanism is ctf's, unchanged:

1. The server writes a `COWLDPST` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `perm`, every geometry and physics constant, the roster with real
   names), then the record stream — joins, leaves, **per-tick input-change records (the command
   bytes)**, chat records (`register`, `script`, `fallback`, `budget_guard`, `result`) and **one
   `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/pistonball_replay.nim` — which imports the
   **same** `src/pistonball/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + `nimby 2.2.4`
   container in `Dockerfile.replay-viewer`.
3. In the browser, `pistonball_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `pistonball_frame` re-steps the sim from the **recorded command bytes** and compares
   `sim.gameHash()` against the recorded hash **every tick** (`checkReplayHash`). One divergent bit
   is caught at the tick it happens, surfaced as `mismatchTick` in the chrome (`#mmwarn`) and, in
   CI, as a hard failure.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle and
   runs `tools/ci/viewer_smoke.mjs` against the replay `docker-smoke` produced (§Tests), which fails
   if the viewer errors, never draws, freezes, or reports a mismatch tick.

Perf target: 1800 ticks of physics plus 36 000 controller evaluations in under 5 s on a CI runner;
`tests/test_perf.nim` bounds it at 60 s.

---

## Server, player, protocol

`src/pistonball/server.nim` is ctf's `server.nim` with the five edits above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`) — **both `/client/` routes serve
real pages, registered before any catch-all asset route, and neither opens the player socket**
(lantern 0.1.1: the certifier probes them before starting player pods). Same `COGAME_*` runtime
contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`,
`COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same done-before-artifact-writes
ordering, same `src/pistonball.nim` entrypoint.

### The player container

`src/pistonball_player.nim` (built to `/bin/pistonball-player`) is `src/paintball_player.nim` with
the baseline names changed. It reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED`,
`PLAYER_POLICY_LABEL`, dials with the starter's bounded retry (240 × 500 ms), and sends **one
Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"wavebot"|"metronome"|null,"policy":"<free label>"}
```

It re-sends the registration on the starter's `RegistrationResends`/`ResendEveryFrames` schedule (the
server's held-registration table, `src/ctf/server.nim:1730`, is kept — with twenty seats joining
strictly slot-sequentially, a seat's first registration routinely arrives before its player index
exists, and dropping it was a real paintball scar). It then sends the Sprite v1 Ready packet
(`0x85`) after each received frame and otherwise only receives. **The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket** — whisky's `receiveMessage` raises on a
close frame and mummy's `send` only queues, so the game's `quit(0)` can outrun the flushed `done`
frame (raid 0.1.3 → 0.1.4). A seat that never registers, or registers with neither field, is
`scripted: "wavebot"`.

Player container resources in the manifest: `requests {cpu: 50m, memory: 48Mi}`, `limits {cpu: 500m}`
— twenty of these plus the game run on one CI runner in `docker_smoke.sh`.

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates` and **filtered by the same window predicate that
`windowView` uses**: the frame contains the housing and floor, the five piston heads `i−2 … i+2`,
this seat's own head highlighted, and **the ball only while its centre is inside the ±1.00 m
window**. Everything else is dark. Board labels carry only `PST-nn`; `showPlayerLabels` is forced
false on the player stream.

### The per-seat view given to the LLM

Numbers rounded to 2 decimals, in **view coordinates** (metres, origin bottom-left, y up) and
degrees per second. This object is the tail of the LLM user message; the scripted baselines are
pure functions of the identical object.

```json
{"turn": 3, "of": 8,
 "clock": {"tick": 675, "of": 1800, "left_s": 46.9},
 "you": {"alias": "PST-08", "piston": 7, "x_m": 3.80,
         "height_m": 0.92, "velocity_m_s": 0.00,
         "stroke_m": 1.60, "max_speed_m_s": 1.92, "width_m": 0.40},
 "window": {"half_width_m": 1.00, "covers_pistons": [5, 6, 7, 8, 9],
            "neighbour_heights_m": {"5": 0.10, "6": 1.44, "7": 0.92, "8": 0.31, "9": 0.00},
            "ball": {"dx_m": -0.34, "height_m": 1.31, "vx_m_s": -2.14,
                     "vy_m_s": 0.22, "spin_deg_s": -310.0, "on_me": true}},
 "sightings_count": 41,
 "sightings": [{"tick": 611, "dx_m": 0.98, "height_m": 0.55, "vx_m_s": -1.90, "vy_m_s": 0.05},
               {"tick": 632, "dx_m": 0.41, "height_m": 0.78, "vx_m_s": -2.02, "vy_m_s": 0.40},
               {"tick": 654, "dx_m": 0.02, "height_m": 1.20, "vx_m_s": -2.10, "vy_m_s": 0.30},
               {"tick": 675, "dx_m": -0.34, "height_m": 1.31, "vx_m_s": -2.14, "vy_m_s": 0.22}],
 "shared_reward": {"last_turn": 6.42,
                   "note": "the whole bank's points over the last 9.4 s; positive means the ball moved left"},
 "goal": {"direction": "left", "your_distance_to_goal_m": 2.60,
          "note": "pistons BEHIND the ball (to its right) go UP; pistons IN FRONT (to its left) go DOWN"},
 "your_last_script": {"mode": "wave", "trigger_m": 1.0, "lead_ticks": 6, "up_m": 1.45,
                      "down_m": 0.1, "idle_m": 0.25, "speed": 1.0, "blind": "hold"}}
```

`window.ball` is `null` whenever the ball is outside the window, and `sightings` is `[]` when the
seat saw nothing at all last turn — which is the common case. Nothing in this object is derived from
any other seat's script, and nothing reveals the ball's absolute position.

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "ball came through low and fast; lifting earlier next time",
 "mode": "wave", "trigger_m": 1.0, "lead_ticks": 6,
 "up_m": 1.45, "down_m": 0.05, "idle_m": 0.25, "speed": 1.0,
 "blind": "idle", "say": "up behind it"}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `mode` | string | closed enum `wave, lift, drop, hold, catch, ripple` | unrecognised / missing → last turn's `mode`, else `wave` |
| `trigger_m` | number | finite, clamped `[0.0, 1.0]`, quantised to µm | non-finite/missing → `1.0` |
| `lead_ticks` | integer | finite, clamped `[0, 24]`, rounded | non-finite/missing → `6` |
| `up_m` | number | finite, clamped `[0.0, 1.6]`, quantised to µm | non-finite/missing → `1.45` |
| `down_m` | number | finite, clamped `[0.0, 1.6]`, quantised to µm | non-finite/missing → `0.10` |
| `idle_m` | number | finite, clamped `[0.0, 1.6]`, quantised to µm | non-finite/missing → `0.25` |
| `speed` | number | finite, clamped `[0.0, 1.0]`, quantised to `0..255` | non-finite/missing → `1.0` |
| `blind` | string | closed enum `hold, idle, ripple` | unrecognised / missing → `hold` |
| `say` | string | **≤ 48 runes** | truncated to 48 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized `script` record **≤ 700
runes**, asserted in `tests/test_replay.nim`. `register.prompt` is capped at **≤ 4000 runes** at the
transport (over-long is truncated, never rejected) and is **never** written to the replay or the
results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — in Nim, `runeLen` /
`runeSubStr` (ctf's `directives.nim` rune discipline, kept). Slicing a `string` by byte index on any
path to the replay is forbidden: a byte-truncated multi-byte character renders in a browser and then
fails a strict UTF-8 parser. §Tests 6 pins it with a 4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose (`extractJsonObject`); accept numeric strings; accept integer percentages for the
`0..1` fields and divide by 100 when the value exceeds 1; accept centimetres for the `_m` fields when
the value exceeds 10 and divide by 100; accept `mode`/`blind` case-insensitively and with
surrounding whitespace. Only when no object with at least one usable field can be recovered do the
retry and then the fallback fire.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, pistonball keys) to `COGAME_RESULTS_URI`. It
must equal the manifest's `results_schema` key-for-key — that schema is
`additionalProperties: false` and the certifier rejects any unknown field. Adding or removing a key
here means editing `coworld_manifest_template.json` in the same commit.

```json
{"names": ["daveey", "daveey-1", "Baseline (1)", "…20 real policy names…"],
 "aliases": ["PST-14", "PST-03", "…20 in SEAT order…"],
 "pistons": [13, 2, "…perm, in seat order…"],
 "policyKinds": ["llm", "llm", "scripted", "…20…"],
 "scores": [84.8, 84.8, "…20 copies of one number…"],
 "win": [true, true, "…20 copies…"],
 "sharedScore": 84.8,
 "progress": 100.0,
 "timePenalty": 15.2,
 "delivered": true,
 "deliveryTicks": 1520,
 "finalTick": 1520,
 "ballStartX": 8.4,
 "ballFinalX": 1.2,
 "bestX": 1.2,
 "bounceBacks": 2,
 "stallTicks": 96,
 "phasePermille": 712,
 "inPhasePermille": ["…20, in seat order…"],
 "touches": ["…20, in seat order…"],
 "llmTurns": ["…20…"],
 "fallbackTurns": ["…20…"],
 "reason": "complete",
 "endRule": "delivered",
 "seed": 4417231}
```

`names` are the **real policy names** (spectator side). `aliases` are the in-game names. Every
per-seat array is in **seat order** and has exactly 20 entries. `scores` holds twenty copies of one
number.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDPST`** format: the static wasm viewer parses exactly
this format, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and the whole seek/keyframe machinery. Consequences handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design ("set 0 for a binary replay format").
- The repo keeps **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): given a
  `.replay` path it prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"pistonball/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],"pistons":[…],
  "policyKinds":[…],"tickCount":…,"scripts":[…],"fallbacks":N,"results":{…}}`. It brace-matches the
  config JSON from the first `{` (the technique ctf's `AGENTS.md` documents for prod forensics) and
  decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.endRule' /tmp/ep.json
  jq -r '[.scripts[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "pistonball/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), and the champion seats' scripts `source == "llm"` with varying `mode`/`up_m` values —
  not all fallbacks, and not a constant script.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDPST`, format version, `gameName` `pistonball`, `gameVersion` `1` |
| config JSON | `seed`, `perm`, `num_agents`, `maxTicks`, `turnTicks`, the whole geometry table (arena box, wall rects, piston pitch/width/stroke, ball radius/mass/inertia, `GoalX`, `BallStartX/Y`, `TravelDistance`), every physics constant (`kN`, `cN`, µ, drags, clamps, gravity), the twenty seeded rest heights, `stepPenaltyMilli`, `players[].name` (**real names**), `slots[].alias`, `fastMode` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| inputs | **the action log**: one command byte per seat per tick, written on change only |
| chats | `register` / `script` / `fallback` / `budget_guard` / `result` records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 1800 hashes (8 B each) + ≤ 36 000 input-change records (≈ 4 B each) + 160 script records
(≈ 260 B each) + a ≈ 8 KB config ≈ **190 KB** worst case, typically under 90 KB.

### Record and event vocabulary

**A. Replay chat records** (written by the server; re-applied at playback in order):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `piston`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `script` | `turn`, `seat`, `alias`, `piston`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `mode`, `trigger_m`, `lead_ticks`, `up_m`, `down_m`, `idle_m`, `speed`, `blind`, `say` |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at game over |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these from
state deltas during playback, so they cost no replay bytes and are identical live and in replay:
`phase`, `handoff` (the ball's supporting column changed), `launch` (a piston head hit the ball with
approach speed > 1.0 m/s), `bounce_back`, `stall`, `wall_touch` (ball touched the right wall after
tick 48), `turn_end`, `delivered`, `gameover`, `say` (a `script` record's non-empty `say`).
**Beats** (scrubber markers): `launch` (only the first per turn), `bounce_back`, `stall`,
`delivered`, `gameover`. `handoff` is *not* a beat — it fires up to twenty times and would bury the
scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Handoff, Launch, BounceBack, Stall, WallTouch, Script, PhaseChange,
Delivered`, and the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's
script, kept (with `image_tag` and the `docker cp` source path
`/workspace/pistonball/replay-viewer/dist/.` changed, and the ecos `mkdir -p` already present at line
22). `coworld build` invokes it with the absolute bundle directory; the script already refuses any
output path that is not a `static-replay-viewer` directory inside the repo, and it must stay
committed **executable** (`coworld build` hard-requires `os.X_OK`).

### One starter supplies all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and from no other starter:**

| File | Source |
|---|---|
| `replay-viewer/config.nims` | `coworld-ctf`'s `replay-viewer/config.nims`, verbatim except `ctf_replay.js` → `pistonball_replay.js` and the `EXPORTED_FUNCTIONS` list renamed `_ctf_*` → `_pistonball_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the flags stay exactly as ctf links them, including `-s ENVIRONMENT=web,worker,node`, `-s ABORTING_MALLOC=1`, `--preload-file data@data`, `-d:useMalloc`. |
| the wasm entry `.nim` | `replay-viewer/pistonball_replay.nim`, forked from `coworld-ctf`'s `replay-viewer/ctf_replay.nim` (stage-note buffer, `ABORTING_MALLOC` diagnostics, `predictedViewerRenderBytes` capacity check, `emscripten_exit_with_live_runtime` lifetime — all kept), exporting `pistonball_load_replay`, `pistonball_frame`, `pistonball_input`, `pistonball_packet_ptr/len`, `pistonball_mismatch_tick`, `pistonball_error_ptr/len`, `pistonball_stage_ptr/len`. |
| `static_replay*.js` | `coworld-ctf`'s `replay-viewer/static_replay.js` **and** `replay-viewer/static_replay_worker.js`, whose bootstrap is the **non-modularized** `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts` form — which is why `config.nims` must not gain `MODULARIZE`/`EXPORT_NAME`. Splicing one starter's shell onto another's link flags deadlocks the viewer silently with every file present and 200 (cogame-lantern, 2026-08-23). Only the Worker name changes: `ctf-static-replay` → `pistonball-static-replay`, and `window.CtfStaticReplay` → `window.PistonballStaticReplay`. |
| `index.html` | built from `coworld-ctf`'s `client/replay_broadcast.html` (see below). |

`static_replay.js` **already sets both machine-readable markers and they are kept unchanged**: it
sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` **on its first drawn
frame** (the Worker's `loaded` message), and `showFailure()` sets
`document.documentElement.setAttribute('data-replay-error', <message>)` **on failure**, plus
`data-replay-mismatch-tick` on a hash mismatch. Those attributes are what `tools/ci/viewer_smoke.mjs`
waits on. The `coworld-replay` bridge `ready` post is fired **from a callback that runs after
`data-replay-loaded="true"` has been set**, never on rAF timing at the call site (chorus, 2026-08-24:
the softmax.com embed otherwise samples an unpainted shell).

### Chrome provenance: what is copied, what is appended, what is removed

- **`client/chrome_common.js` is copied byte-for-byte from `coworld-ctf`. Zero edits.** Its
  CTF-specific paths (perks, handicaps, lives, flag story) stay in the file and are inert because the
  corresponding state fields are simply absent from pistonball's stream. Every pistonball-specific
  readout lives in the appended game block, and the state JSON **keeps ctf's key names**
  (`t, mt, ph, lob, pl, sp, mx, st, lp, sk, ff, en, mm, bs, pov, teams, roster, events, lead, beats,
  lulls, over, hold`) so chrome_common's plate rendering, feed rows, beat markers, momentum curve,
  spoilers switch and endcard run unmodified against pistonball values. A from-scratch page that
  reuses the starter's ids is explicitly **not** what happens here (cogame-gridlock, 2026-08-23).
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — one
  `<style>` and one `<script>` block at the end of the file, injecting pistonball's readouts into the
  existing containers. Nothing above them is rewritten; the CSS variables, `relayout()`
  (`client/replay_broadcast.html:4276`), the transport, the endcard, the locker-room loader and the
  `?embed=1` mode are the starter's. The game block's own function names are prefixed `pb`
  (`pbMarkBeat`, `pbPushFeed`, …) so nothing shadows chrome_common's hoisted alias block
  (`var markBeat = C.markBeat` — the tandem 2026-08-23 scar), and a test asserts no game-block
  top-level name collides with the alias list.
- **Removed starter elements (exactly these):** `#viewpanel` and its children `#minimap`,
  `#minimap-canvas`, `#zoombar`, `#zoom-out`, `#zoom-in`, `#zoom-slider`, `#zoom-read`; `#fpv` and
  its children `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`; and `#povBadge`.
  **Zoom decision: the arena is fixed and the board (1200 × 600 px) always fits the frame, so
  `#viewpanel` — the zoom bar and minimap — is dropped entirely**, per the rule that it exists only
  for boards larger than the frame. `broadcast_core.js`'s zoom/pan/minimap code stays in the file,
  verbatim, simply never driven.
- **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom` (re-captioned
  "Twenty pistons, one ball…", art from `client/art/lockerroom/bg.jpg`), `#chrome`, `#scorebug` with
  `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#mmwarn`, `#bannerlane`,
  `#killfeed`, `#transport` with every button (`#btn-play`, `#btn-back`, `#btn-fwd`, `#btn-end`,
  `#btn-restart`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`), `#speedchips`, `#scrub`, `#scrub-fill`,
  `#scrub-head`, `#scrub-win`, `#momentum`, `#lulls`, `#tick-clock`, `#ffwd-chip`, `#ffwd-mini`,
  `#win-chip`, `#endcard` with `#ec-headline`, `#ec-how`, `#ec-wincond`, `#ec-teams`, `#ec-replay`,
  and `#status`.

### The exact state JSON the viewer reads

`buildStateJson` (ctf's, retargeted) emits this object once per frame. Keys above the fold are ctf's
and are consumed by the byte-identical `chrome_common.js`; everything pistonball-specific is under
`pb` and `scripts`, consumed only by the appended game block.

```json
{"t": 812, "mt": 1800, "ph": "playing", "lob": 0, "pl": true, "sp": 1, "mx": 1800,
 "st": 0, "lp": false, "sk": false, "ff": false, "en": true, "mm": -1, "bs": 1, "pov": -1,
 "teams": {"bank": {"score": 41.6, "progress": 497, "phase": 712, "delivered": false,
                    "bounceBacks": 1, "policies": 20}},
 "roster": [{"s": 0, "name": "daveey", "team": "bank", "alias": "PST-14", "piston": 13,
             "kind": "llm", "inphase": 780, "touches": 6}, "…20 rows, seat order…"],
 "events": [{"k": "launch", "t": 806, "piston": 15, "speed": 1.8}, "…"],
 "turn": 3, "turns": 8, "turnTicks": 225,
 "pb": {"ball": {"x": 4.82, "y": 1.31, "vx": -2.14, "vy": 0.22, "spin": -310.0, "r": 0.40,
                 "column": 9},
        "pistons": [{"h": 0.10, "u": 0.00, "want": "down", "off": false}, "…20, piston order…"],
        "arena": {"w": 9.6, "h": 4.8, "floor": 0.0, "left": 0.8, "right": 8.8,
                  "goalx": 1.2, "startx": 8.4, "stroke": 1.6, "pitch": 0.4},
        "best": 3.90, "progressPct": 49.7, "phasePermille": 712,
        "reward": {"progress": 49.72, "penalty": -8.12, "score": 41.60},
        "bubbles": [{"piston": 9, "say": "up behind it", "until": 872}]},
 "scripts": [{"turn": 3, "seat": 4, "alias": "PST-10", "piston": 9, "source": "llm",
              "mode": "wave", "up_m": 1.45, "note": "…", "say": "up behind it"}, "…"],
 "lead": {"teams": ["ball"], "pts": [[0, 0], [24, 3], "…change-points of progressPct…"]},
 "beats": [{"t": 96, "k": "launch"}, {"t": 640, "k": "bounce_back"}, "…"],
 "lulls": [[240, 388]],
 "over": {"winner": "bank", "draw": false, "timeLimit": false, "endRule": "delivered",
          "reason": "complete", "score": 84.8, "ticks": 1520, "teams": {"bank": {"prog": 1000}}},
 "hold": 3}
```

There is exactly **one** `teams` key (`bank`) — this is a cooperative game with one side — so
chrome_common's plate loop renders one team plate; `#plates-r` is used by the game block for the
objective plate instead. `roster` carries the **real policy names** and is spectator-side only.

### Readouts

1. **Run bug** (top, always on). `#plates-l`: the one team plate — "THE BANK · 20 cogs" with the
   live **shared score** as its headline number (green above 0, red below) and the phase percentage
   under it. `#plates-r`: the objective plate — a horizontal **journey bar** from the right wall to
   the goal wall with the ball's marker, the best-x ghost marker, and `50%`. Centre column
   (`#clock`): `M:SS` from `tick div 24` with `of 1:15` in `#clock-caption`.
2. **The bank strip**: twenty cells under the scorebug, one per piston in board order, each filled
   to its head height and tinted by phase state — grey (not engaged), green (engaged, in phase),
   **red pulsing (engaged, out of phase)**. This is the idea's "who's out of phase" highlight in
   compact form and it is the readout that survives 360 px. Each cell's `title` carries the real
   policy name; a click selects that piston (highlighting it on the board).
3. **The board** (the headline): a side view of the machine shop — concrete floor, riveted housing,
   twenty polished rods with heads that move, the goal wall on the left painted with chevrons and a
   lamp that lights on delivery, the right wall, and the ball as a shaded steel sphere **that
   visibly rotates** (its `angleQ` drives a baked highlight, so rolling reads as rolling). Piston
   heads that are out of phase get a red rim light on the board too.
4. **Ball trail and best-x rail**: a short motion trail behind the ball, and a thin vertical
   dashed rail at `bestX` so a spectator can see instantly when the ball is giving ground.
5. **Launch and impact FX**: a dust puff and a spark ring when a head hits the ball above 1.0 m/s; a
   short screen shake on `bounce_back`.
6. **Speech bubbles**: at most **three** at a time — the three pistons nearest the ball that emitted
   a non-empty `say` this turn — drawn for 2.5 s in a **reserved band at the top of the arena**
   (`Y ∈ [3.55, 4.25] m`), never positioned relative to a piston head. The band is sized from
   `MaxSayRunes = 48` measured in `data/font.ttf` at the current `--hudscale`, which is exactly the
   reservation the cogchemists 2026-08-24 scar demands; `viewer_smoke.mjs --strict-text-bounds`
   requires `canvas_text.never_inside == 0` for this fixed arena.
7. **Match feed** (`#killfeed`, renamed in copy only): plain language — "PST-14 rises behind the
   ball", "PST-03: flat and out of the way", "HANDOFF — ball onto piston 9", "BOUNCE BACK — gave up
   0.6 m", "TURN 4 — 20 new programs". Script `note`/`say` strings appear here; this is where a
   spectator sees the LLM playing.
8. **Momentum graph** (`#momentum`): ctf's `lead` series repurposed to the **journey curve** —
   `progressPct` over the whole timeline, drawn from the first frame, with the delivery marked.
9. **Transport and integrity**: ctf's play/pause, step-back, +5 s, jump-to-end, loop, skip-lulls,
   spoilers, speeds `[1,2,3,4,8,16]`, scrubber with beat markers, tick readout, the end-hold
   countdown and `#mmwarn` — all verbatim.
10. **Endcard**: "DELIVERED in 63.3 s · score 84.8" (or "OUT OF TIME at 3.00 m · score 57.0"), and
    chrome_common's `ec-*` table listing all twenty seats by **real policy name** with their piston
    number, in-phase %, touches and LLM/fallback turn counts, sorted by in-phase %.

### Transport rules

- `relayout()` is kept verbatim (`client/replay_broadcast.html:4276-4320`): it sets `--hudscale`,
  `--topband` and **`--band`** on `:root` by fixed-point iteration, so the board is letterboxed
  between the scorebug band and the transport band.
- **No overlay sits in the transport band.** Every pistonball overlay the game block adds — the bank
  strip, the journey bar, the best-x legend — is positioned inside `#chrome` with
  `bottom: calc(var(--band) + N * var(--u))`, never over it.
- The **endcard stops at `var(--band)`** (the starter's `#endcard { bottom: var(--band) }` rule at
  line 1047 is kept) and is **dismissed by every seek** (the starter's behaviour, kept).
- **Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">`** elements — the
  game block upgrades chrome_common's markers to buttons with `aria-label` and `title` (e.g.
  "Bounce back — 26.7 s") and a click seeks to that tick. **CSS exists for every kind emitted**:
  `.beat-marker.launch`, `.bounce_back`, `.stall`, `.delivered`, `.over` — one rule per kind,
  asserted by `tests/test_viewer.nim`.

### Art

Real, and mostly baked from what the repo already ships. The floor, housing, rods, piston heads,
goal-wall chevrons, warning hatching and the vignette are baked once at startup with **pixie**
(already a dependency, already how ctf bakes its board), using ctf's shipped
`client/art/walls/wall_h.jpg` and `wall_v.jpg` as the concrete/steel plate source and
`data/font.ttf` for every label. The ball is a baked steel sphere sprite with a rotating specular
highlight and a rim-lit shadow. The locker-room card reuses `client/art/lockerroom/bg.jpg`. No
solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width. The starter already engineers this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`; kept
verbatim. Twenty policy names cannot be shown at that width and are **not attempted** — the scorebug
shows the score, the journey bar, the clock and the twenty-cell bank strip (18 px wide at 360 px,
3 px cells), and the names live in the endcard and in each cell's `title`. Two further rules ship in
the game block: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow:
ellipsis }` (so the team/objective plate captions never collapse to "…") and, under `.tiny`, the
phase percentage caption, the touches column and the bubble text are hidden. The board aspect is
1200:600, which the chrome derives from the stream. `tests/test_viewer.nim` asserts both rules are
present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-pistonball`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `pistonball`; `game.name` is also
  `pistonball`, so the secret namespace `secret://coworld/pistonball/anthropic_api_key` matches
  `game.name` exactly (cooperative-hunting, 2026-08-25).
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{PISTONBALL_IMAGE}}` (placeholders are derived from **compose service names**; `{{GAME_IMAGE}}`
  is not a thing outside ctf's own two-service file — lantern 0.1.0):

  ```yaml
  services:
    pistonball:
      image: coworld-pistonball:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

  (ctf ships two services/two images; pistonball uses the one-image/two-entrypoints shape because the
  shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure (nimby 0.1.26,
  `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's
  package tree), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:pistonball src/pistonball.nim` →
  `/bin/pistonball`, and the same for `src/pistonball_player.nim` → `/bin/pistonball-player`. The
  runtime stage copies `/bin/pistonball`, `/bin/pistonball-player`, `data/`, `client/`, `*.json`.
  `CMD ["/bin/pistonball"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby with its
  sha256 check, the marker splices, the `test -f`/`grep -q` assertion block) with the asset list
  swapped and the workspace path `/workspace/pistonball`.
- **`coworld_manifest_template.json`** (written against the `coworld` 0.1.42 upload contract —
  validate offline with the CLI's `validate_upload_manifest` before dispatching):
  - top-level `$schema`, `episode_timeout_minutes: 20`, and `tags` ≥ 3.
  - `game.name` `pistonball`; `game.owner`; `game.runnable`
    `{"type":"game","image":"{{PISTONBALL_IMAGE}}","run":["/bin/pistonball"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/pistonball/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-pistonball/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}` (nested under `game`, not
    top-level).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`; **every array property carries `minItems`/`maxItems`** (tandem 0.1.0
    scar): `tokens` (1..20), `players` (1..20), `slots` (0..20), plus `closedRoster`, `seed`,
    **`num_agents`** (1..20), `minPlayers`, `maxTicks` (default 1800), `maxGames` (default 1),
    `turnTicks` (default 225), `turnBudgetMs` (default 20000), `attempt1Ms` (default 12000),
    `retryMs` (default 6000), `minBatchSpacingMs` (default 45000), `wallClockBudgetSeconds`
    (default 660), `lobbyJoinTimeoutTicks` (default 1800), `startWaitTicks`, `gameOverTicks`,
    `fastMode` (default true), `showPlayerLabels`, `model`, `maxOutputTokens` (default 900),
    `windowHalfWidthUm`, `strokeUm`, `maxPistonSpeedUm`, `ballRadiusUm`, `ballMassGrams`,
    `stepPenaltyMilli` (default 10). The CLI validates every variant and the cert fixture against
    this schema (injecting `tokens`), so every key either appears here or is not settable.
  - `game.results_schema`: exactly the 25 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","reason","endRule","delivered","sharedScore","progress"]`,
    `reason` enum `["complete","deadline","fault"]`, `endRule` enum
    `["delivered","out_of_time","wall_clock","sim_fault","host_error"]`, and every per-seat array
    `minItems: 20, maxItems: 20`.
  - `game.protocols`: **both `player` and `global`**, each `{"type":"text","value":"…"}` (objects,
    not bare strings — garble v0.1.0). `player` describes the registration chat frame, the
    window-filtered per-tick Sprite v1 frames, the fact that seats send no inputs, and the script
    schema; `global` describes the `/global` spectator snapshot, the state JSON above and the static
    replay bundle.
  - `game.docs`: `readme` = `{"type":"text","value":"<the README body inlined>"}` and `pages` =
    three entries — `{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined: every number in §The game>"}}`, `{"id":"protocol.md","title":"Wire protocol",…}`,
    `{"id":"scripts.md","title":"Writing a piston program",…}`. A manifest test asserts all four
    values are non-empty text.
  - `game.tags`: `["physics","cooperative","local-observation","swarm","llm"]`.
  - `player[0]` (the only top-level bundled player entry, with id/type/name/description) =
    `{"id":"baseline","type":"player","name":"Pistonball Wavebot Baseline",
    "description":"Reactive scripted piston: lift behind the ball, clear in front. No LLM.",
    "image":"{{PISTONBALL_IMAGE}}","run":["/bin/pistonball-player"],
    "env":{"PLAYER_SCRIPTED":"wavebot"},"source_url":…,
    "resources":{"requests":{"cpu":"50m","memory":"48Mi"},"limits":{"cpu":"500m"}}}`.
    It occupies **all twenty** certification slots — every declared player entry must occupy at
    least one slot or cert fails `players_missing` (raid 0.1.2 → 0.1.3).
  - **Variants — `num_agents` is 20 in both, and `description` is required on each:**

    | id | name | description | **`num_agents`** | `players`/`slots` | `minPlayers` | `maxTicks` | turns | `turnTicks` | `minBatchSpacingMs` | `turnBudgetMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|---|---|
    | `default` | The Bank (20 pistons, 75 s) | Twenty pistons, one ball, eight decision turns. | **20** | 20 | 20 | 1800 | 8 | 225 | 45000 | 20000 | 660 |
    | `sprint` | Sprint (20 pistons, 50 s) | Same bank and ball, six decision turns, for cheap ladder rounds. | **20** | 20 | 20 | 1200 | 6 | 200 | 45000 | 20000 | 480 |

    Both seat twenty players, `slots: [{"alias":"PST-01"}, … {"alias":"PST-20"}]`, `fastMode: true`,
    `maxGames: 1`. `sprint` changes only run length, **never** the seat count. `sprint`'s budget:
    5 × 45 s + 20 s + 20 s lobby + 20 s write ≈ 285 s, inside 480 s.
  - **Certification fixture — `num_agents` is 20 here too:**
    `certification.players` = twenty `{"player_id":"baseline"}` entries;
    `certification.game_config` = `{"players":[{"name":"PST-01"}, …20…],
    "slots":[{"alias":"PST-01"}, …20…], "num_agents": 20, "minPlayers": 20, "seed": 4417231,
    "maxTicks": 900, "maxGames": 1, "turnTicks": 225, "turnBudgetMs": 20000,
    "minBatchSpacingMs": 0, "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 900,
    "fastMode": true}` — 4 turns, every seat scripted, no LLM client (no credentials offline, so the
    client disables itself and every turn falls back instantly). Wall cost ≈ 10 s connect + ~1 s of
    physics + the ~20 s shutdown grace ≈ 35 s. At 900 ticks the fixture replay is **37.5 s of
    playback**, comfortably longer than the viewer smoke's 12 s soak (ecos, 2026-08-23: a replay
    shorter than the soak reads as "frozen"). Because 35 s is close to `coworld certify`'s 60 s
    default, the release workflow's certify step passes **`--timeout-seconds 300`**
    (cooperative-hunting 0.1.2 → 0.1.3); the fixture is **not** shrunk.
- **Scaffold from `templates/`** with `<slug>` = `pistonball`, `<IMAGE>` = `coworld-pistonball`,
  `<SEATS>` = **20**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim, no
  substitutions), `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh`
  (**`chmod +x`**). Two additions to the template `ci.yml`: the `docker-smoke` step gets
  `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format), and the `wasm-viewer` job gets the extra
  `renderer_fixture.html` step of §Tests. The `NIM_TESTS_RELEASE_ONLY` repo variable lists
  `tests/test_perf.nim` and `tests/test_baselines.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/pistonball-player"`, one image,
  env-switched; each also sets `PLAYER_POLICY_LABEL`):

  | name | env | role |
  |---|---|---|
  | `pistonball-swell` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `pistonball-cascade` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `pistonball-wavebot` | `PLAYER_SCRIPTED` = `wavebot` | filler |
  | `pistonball-metronome` | `PLAYER_SCRIPTED` = `metronome` | filler |

  A 20-seat episode is filled by the platform with the two champions plus fillers — which is exactly
  the idea's "fill with champions + fillers" and the reason the cross-play mean is meaningful.
- **Repo layout**: `src/pistonball.nim`, `src/pistonball_player.nim`,
  `src/pistonball/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, bank.nim, control.nim,
  scripts.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim, replays.nim,
  replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, wire_constants.nim,
  server.nim}`, `replay-viewer/{pistonball_replay.nim, config.nims, static_replay.js,
  static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, SCRIPTS.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `pistonball.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only harness;
the sandbox has no Nim, Docker, emsdk or browser. The **determinism gate** (test 2 plus the viewer
smoke) is inviolable: if it fails, the physics or a build flag changed — fix the code, never the
test.

1. **`tests/test_physics.nim`** — sim unit tests: a ball dropped onto a flat bank settles within 24
   ticks and its resting penetration is between 200 and 600 µm; a ball at rest on a level bank does
   not drift (|v| stays under 1 000 µm/tick for 480 ticks); the same ball on a two-column step of
   0.60 m rolls **left** and its `spin` sign matches rolling-without-slipping to within 15 %; a
   piston rising at full speed under a resting ball imparts upward velocity within 10 % of the
   analytic `2·pistonVel`; contact normal force is never negative (contacts never stick); friction
   never reverses the slide direction within one substep; the ball never leaves
   `x ∈ [1 200 000, 8 400 000] ∪ y ∈ [400 000, 4 000 000]` over 1800 ticks of random command bytes,
   and `guardClamps` stays 0 for the twenty-`wavebot` run; `BallInertia` is re-derived from `½mR²`
   and asserted.
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same command-byte log ⇒
   identical `gameHash` at every tick over a full 1800-tick run, twice in one process and once in a
   fresh sim; (b) a one-unit change in any command byte changes the final hash; (c) a committed
   golden fixture `tests/data/golden_hashes.json` pins the hash at every 50th tick for seed 4417231;
   (d) **a source guard** that greps `src/pistonball/{sim,bank,trig,sim_types,sim_config,
   sim_state}.nim` for `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts
   for `-ffast-math`, failing on any hit; (e) `SinQ12` re-derived from `math.sin` entry by entry, and
   `isqrt` checked exhaustively below 2¹⁶ and on perfect squares to 2⁴⁰; (f) `perm` and the twenty
   rest heights are a pure function of `seed`, identical across two fresh sims, and `perm` is a
   permutation of `0..19`.
3. **`tests/test_bank.nim`** — geometry: the twenty piston x-ranges tile `[800 000, 8 800 000]`
   exactly with no gap or overlap; `centreX_i` matches the table; the window of piston `i` covers
   exactly `i−2 … i+2` clipped at the ends; the contact broadphase returns every head whose x-range
   is within `BallRadius` of the ball and no more, over 10 000 randomised ball positions; `GoalX`,
   `BallStartX` and `TravelDistance` are mutually consistent.
4. **`tests/test_control.nim`** — the controller: for 2 000 randomised (state, script) pairs the
   command byte is in `0..254` and the implied `|u| ≤ speed · MaxPistonSpeed + 1`; `h_i` never leaves
   `[0, Stroke]` after applying it; the same (state, script) pair always yields the same byte; each
   of the six modes produces the documented target in its documented condition; `blind = hold`
   yields `cmd = 127` exactly when the ball is invisible and `h_i` is already at target; `ripple` is
   periodic with period 48 and its per-column phase offset is monotone in `i`; a non-`Playing` phase
   forces `cmd = 127`.
5. **`tests/test_baselines.nim`** (release-only) — **the bounded-orders / legality assertion on the
   scripted baselines**: for 500 pseudo-random world states × both baselines, the emitted script
   validates against the reply schema — every numeric field finite and inside its range, `mode` and
   `blind` in their enums, `note` ≤ 160 runes, `say` ≤ 48 runes — and the compiled command byte is in
   range. Plus the tuning pin: **twenty `wavebot`s deliver on at least 18 of 20 seeds** within 1800
   ticks with a mean score above +60; twenty `metronome`s score strictly below twenty `wavebot`s in
   mean; a 10-`wavebot`/10-`metronome` mix still delivers on at least 12 of 20 seeds. (This is the
   anti-regression pin for the whole physics tuning: if the baselines cannot move the ball, the
   three `BaselineParams` numbers are wrong — re-run `tools/tune_baselines.nim` and commit the
   sweep's pick to `tools/ci/baseline_tuning.json`, which `tests/test_tuning.nim` re-asserts. The
   physics constants do not move.)
6. **`tests/test_scripts.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   percentages instead of 0..1, centimetres instead of metres, an unknown `mode`, an unknown `blind`,
   NaN/absent fields, out-of-range values, a 300-character `note`, and a `say` whose 48th and 49th
   characters are a **4-byte emoji** — the truncation must land on the **rune** boundary and the
   result must still round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒
   the `wavebot` script plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a
   `throttled` client ⇒ **zero** retries.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all twenty seats' calls
   go out in one parallel batch** (the fake records in-flight windows; the test asserts all twenty
   intersect); consecutive batches are ≥ `minBatchSpacingMs` apart; the per-turn budget is enforced
   with a hung client; the budget guard switches to scripted and the episode still ends `complete/*`;
   the 660 s stop yields `deadline/wall_clock`; a tripped invariant yields `fault/sim_fault` with a
   partial replay; a disconnected seat plays `wavebot` and revives on reconnect; a never-connecting
   seat is reported to `COGAME_PLAYER_FAILURE_URI` and the run still reaches a normal ending; a
   registration that arrives before its player index exists is **held and applied**, not dropped.
8. **`tests/test_locality.nim`** — the no-more-than-your-neighbours invariant. Over 200 randomised
   states: seat `s`'s composed LLM user message and its Sprite frame contain the ball **iff** the
   ball centre is within 1.00 m of `centreX_{perm[s]}`; contain heights for exactly the columns
   `perm[s]−2 … perm[s]+2` and no others; contain no substring of any other seat's `note`, `say`,
   `mode` or numeric fields; contain no cumulative reward, `bestX`, `progressMilli`, `perm` or seed;
   and contain no `sim.players[i].address`. Also: `control.pistonCommand`'s inputs are structurally
   limited to that seat's own window and script.
9. **`tests/test_scoring.nim`** — the formula and its sign: the six worked examples of §The game
   reproduce to 3 decimals; `progress` telescopes (a path with backtracking scores identically to the
   straight path ending at the same x); all twenty `results.scores` entries are bit-identical;
   `win` is `delivered` in all twenty slots; delivering stops the penalty at the delivery tick; the
   phase metric is 1000 permille for a hand-built perfect wave and 0 for its exact inverse.
10. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full 20-seat scripted
    episode writes `results.json` and a `COWLDPST` replay; `parseReplayBytes` accepts it;
    re-simulating from the config + recorded command bytes reproduces **every** recorded hash;
    `tools/replay_summary.py` output parses under a **strict UTF-8 JSON** parser
    (`json.loads(out.decode("utf-8"))`) with the fixture forced to carry a non-ASCII `say` and a
    non-ASCII policy label, so the UTF-8 path is real; the embedded config JSON decodes strictly and
    contains `seed`, `perm`, the geometry table and the twenty rest heights; every `script` record is
    ≤ 700 runes; `results.reason`/`results.endRule` are in the legal enums; the stream contains
    exactly 20 `register` records, 20 `script` records per turn, at least one `handoff` and one
    `launch`, and exactly one `result` record.
11. **`tests/test_server.nim`** — websocket contract: registration chat accepted and **not** echoed
    into the replay chat stream; a prompt over 4000 runes truncated, not rejected; a non-registration
    chat from a player dropped; an input mask from a player ignored; bad token 403; `/healthz`;
    `/global` snapshot → ticks → game over; `/client/global` and `/client/player` serve real pages and
    neither opens the player socket; `/healthz` and `/global` still answer 15 s after the artifacts
    are written; artifact writes to `file://` URIs. **Two name spaces**: the composed LLM user
    message and the player-stream board labels contain no real name, while the chrome roster,
    `over`, and `results.names` do.
12. **`tests/test_manifest.nim`** — **`num_agents == 20` in every variant *and* in
    `certification.game_config`**; `len(certification.players) == 20` and
    `len(certification.game_config.players) == 20`; every declared `player[]` id occupies at least
    one certification slot; `results_schema` keys == `playerResultsJson` keys with every per-seat
    array bounded `minItems: 20, maxItems: 20`; every array in `config_schema` declares
    `minItems`/`maxItems`; `game.protocols` has **both** `player` and `global` as
    `{"type":"text",…}`; `game.docs.readme` and all three pages are non-empty text;
    `game.replay_viewer.bundle == "static-replay-viewer"` and there is no top-level `version` or
    `game.display_name`; `game.owner` present; every variant's `wallClockBudgetSeconds ≤ 0.6 × 1200`;
    `attempt1Ms + retryMs ≤ turnBudgetMs`; `maxTicks mod turnTicks == 0`; the compose service name
    and image match `{{PISTONBALL_IMAGE}}` / `coworld-pistonball`; the secret namespace equals
    `game.name`; `config_schema` covers every field `sim_config.update` reads.
13. **`tests/test_viewer.nim`** — static assertions over `client/replay_broadcast.html` and
    `client/chrome_common.js`: `chrome_common.js` is **byte-identical** to the starter's copy (sha256
    pinned); `replay_broadcast.html` still contains ctf's `relayout()` with `--band`, `--topband` and
    the `--hudscale` clamp on `:root`; `#endcard { bottom: var(--band) }`; `#scorebug`,
    `#bannerlane`, `#killfeed`, `#transport`, `#mmwarn`, `#endcard`, `#momentum` and the `.tiny`
    block are present; `#viewpanel`, `#fpv` and `#povBadge` are **absent**; a `.beat-marker` CSS rule
    exists for **every** beat kind the sim emits (`launch`, `bounce_back`, `stall`, `delivered`,
    `over`) and every marker is a `<button>`; no game-block top-level name collides with
    chrome_common's alias list; the `.plate-name { flex: 1 1 auto; min-width: 3.2em` rule is present;
    `broadcast_core.js` differs from the starter's copy in **exactly** the `PISTONBALL_WIRE`
    identifier; no `ctf_`/`CTF_`/`paintball` identifier survives in `client/`, `replay-viewer/` or
    `src/`; `static_replay.js` sets both `data-replay-loaded` and `data-replay-error`; and
    `config.nims` contains **no** `MODULARIZE` or `EXPORT_NAME`.
14. **`tests/test_startup.nim`** — `/bin/pistonball` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when
    unpinned and honoured when pinned; both entrypoints exist and are executable in the image.
15. **`tests/test_perf.nim`** (release-only) — 1800 ticks of physics plus 36 000 controller
    evaluations complete in under 60 s.

**CI jobs beyond the Nim tests:**

- `docker-smoke` — `tools/ci/docker_smoke.sh` runs a raw-Docker episode from the certification
  fixture with **`SMOKE_SEATS=20`** (an independent cross-check against
  `certification.game_config.num_agents`; a mismatch prints `SEAT-COUNT FAIL:`) and
  `SMOKE_REQUIRE_REPLAY_JSON=0`, asserts **every one of the twenty player containers' exit codes** as
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
  900-tick fixture is 37.5 s long, so a 12 s soak cannot end the replay. **This is the only gate that
  runs the viewer rather than checking that its files exist** (cogame-lantern, 2026-08-23).
- `wasm-viewer`, second step — **`tools/ci/renderer_fixture.html`**: `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so every seat plays scripted and the smoke replay carries only the baselines'
  fixed `say` strings; nothing in CI would otherwise exercise the bubble band or the feed at full
  cap. The fixture loads the real renderer with a **full-cap 48-rune `say` and 160-rune `note` on all
  twenty seats at once**, at 360, 620 and 1280 px, self-checks its own string lengths, and is run
  through `viewer_smoke.mjs --strict-text-bounds` in its own step (cogchemists, 2026-08-24).

---

## Out of scope (v1)

- **Cooperative Pong.** The idea's second mode is deliberately deferred: two paddles, one ball, a
  different arena, a different scoring rule, a different observation and — fatally for the seat-count
  pin — `num_agents = 2` instead of 20. Two rule sets in one sim is the single biggest build risk in
  this note's neighbourhood, and v1 buys nothing with it. It returns as its own coworld
  (`cogame-coop-pong`) or as a v0.2 second board once pistonball is live and ranked.
- **A raw per-tick RL vector transport.** The v1 control channel is one policy-script per 225-tick
  turn plus the deterministic controller; the per-tick command byte is derived server-side, recorded,
  and replayed. Because the controller is already a pure function of `(script, window, tick)`,
  exposing a per-tick socket action is a protocol addition, not a redesign — but it is not in v1, and
  the LLM policy interface is the one the platform ranks.
- **pymunk / Box2D / any float solver, and bit-exact PettingZoo parity.** Rejected for Cogball's
  reason: those solvers ride on `sinf`/`cosf`/`atan2f` and float32 accumulation order, which would
  make the native↔wasm hash chain depend on two musl builds agreeing. Nothing here is expected to
  reproduce `pistonball_v6` frame for frame, and no test asserts it does.
- **`local_ratio` / per-piston local reward shaping.** PettingZoo mixes a local term into the global
  reward; v1 is purely global (`local_ratio = 0`), because the whole point of the coworld is a shared
  reward under local observation. A configurable local term is a v0.2 knob.
- **Image observations.** Seats get a structured JSON window, never an RGB crop. There is no pixel
  observation path and no CNN policy interface.
- **Any inter-seat communication, in any form, at any bandwidth** — including emergent side channels
  through the observation. `say` and `note` are one-way to the spectator feed. This is not a v0.2
  item; it is the point of the coworld.
- **A variable seat count, a variable piston count, gaps in the bank, or two balls.** `num_agents` is
  20 in every variant and the cert fixture; the bank is exactly twenty 0.40 m pistons; there is one
  ball. Every one of those is a different game.
- **Piston damage, stamina, breakage, energy budgets, or a cost for moving.** The only cost in the
  game is time.
- **Vertical walls, ceilings the ball must pass under, obstacles, or procedurally generated arenas.**
  The arena is one fixed box and its only moving parts are the pistons and the ball. Procedural
  arenas are the obvious v0.2 variety and are not in v1.
- **Everything ctf's arena rules carried**: guns, flags, fog cones, first-person POV, lives, respawn,
  grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the barrage, the
  hill, procedural terrain, the map pool, the map editor and mapkit. Deleted, not disabled.
- **Player debug-sprite overlays** (ctf's `0x86` channel) and the zoom/minimap panel. The seats send
  no inputs and draw no overlays in v1; `#viewpanel` is removed because the board always fits the
  frame.
- **Audio, 3D, camera cuts, slow-motion replays**, and any downloaded art asset.
- **Persistent memory across episodes** (no notes carried between runs) and any tournament structure
  beyond the platform league.
