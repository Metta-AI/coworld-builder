# grf-football — design note (2026-08-27, paintbot lineage)

`Metta-AI/cogame-grf-football` is **eleven-a-side 2D physics football with a gfootball-style
discrete action set**, forked from **`Metta-AI/coworld-ctf`** (paintbot / paintball), mounted
read-only at `/workspace/starters/coworld-ctf`. **Every convention there holds here unless this
note says otherwise.** The starter is the whole real-time stack: a 24 Hz tick loop, the Sprite v1
per-tick action log, the binary replay codec with a per-tick hash chain, the static wasm replay
viewer and its broadcast chrome, and — since paintball — a complete **squad-command LLM layer**
(`src/ctf/{decide,llm,directives,baselines,control}.nim`) that already does one parallel batch of
Claude calls per decision turn with a bounded retry and a scripted fallback. This coworld swaps
ctf's arena rules for a football sim and retargets that layer; it keeps the loop, the replay, the
viewer, the chrome and the CI wiring.

This is **not** a port of the gfootball C++ engine (it cannot be hosted here) and not a bit-exact
reproduction: it is a new physics game written for this coworld in the paintbot loop, reimplementing
gfootball's *spirit* — 11 v 11, the 19-action discrete vocabulary (directions, short/long/high pass,
shot, sprint, dribble, slide), and unseated players run by the built-in AI. (Operator ruling
2026-08-22, Cogball: new physics games are the ctf row, not the moba row.) It coexists with the
shipped 3v3 `cogball`; §The game states exactly how the two differ.

**Source idea, verbatim:**

> GRF Football — eleven cogs per side in Google Research Football, from 3v1 academy drills to full
> 11v11
>
> Port of Google Research Football (gfootball). A physics-based soccer sim with an 'academy' of
> drills (empty goal, run-to-score, 3v1 with keeper, pass-and-shoot, corner, counterattack) and full
> 11v11 matches; 19 discrete actions (directions, short/long/high pass, shot, sprint, dribble,
> slide). Multi-agent mode gives each seat one player (the rest run on the built-in AI). Team reward
> = goals, optional checkpoint shaping.
>
> Seats: 1-11 per team (fill unseated players with the built-in AI)
> Motive: team zero-sum
> Policy interface: per-tick discrete action; neural/scripted coworld; LLM as a tactics layer over
> scripted roles is the plausible variant
> Fills gap: 03 Cogball is 3v3 in a physics engine — GRF is the industrial-strength, 11-a-side,
> camera-ready version; decide whether Cogball becomes 'GRF-lite' or the two coexist
> Integrity (anti-collusion): team zero-sum; seeded kick-offs; anonymous aliases.
>
> Replay plan (watchability): gfootball renders broadcast-style 3D already; use it.
>
> Source: github.com/google-research/football.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How grf-football satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a real-time tick loop with new rules written for this coworld, RL-vector/discrete-action policies, and a squad-command LLM layer already in the server. Not moba: nothing pre-exists to port here. (§The game) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-grf-football`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT=<text>` (both champions) vs `PLAYER_SCRIPTED=zonal` / `PLAYER_SCRIPTED=gegenpress` (both fillers). One image `coworld-grf-football`, one player entrypoint `/bin/grf-football-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` kept from ctf; the **same Nim sim module** compiles into `replay-viewer/grf_football_replay.nim` under emscripten and re-simulates every frame in the browser. (§Viewer) |
| Real art, starter's chrome verbatim | Cogs are the shipped `data/rig_real/red` and `data/rig_real/blue` wheeled rigs composed by `rig_art.nim`; pitch, nets and ball baked with pixie. `client/chrome_common.js` copied **byte-for-byte**; `client/replay_broadcast.html` is the starter's page **with a game block appended**. (§Viewer) |
| Two name spaces | In-game everything is `RED-9`, `BLUE-10`, team `red`/`blue` — no policy name reaches a prompt, a seat view, a shout or a board label. Real policy names appear only in the replay config, `roster[].name`, `teams.<team>.policies`, `results.names` and the DOM scorebug. Test-enforced. (§Server, §Tests) |
| Degrade-never-hang inside 60 % of `episodeTimeoutSeconds` (1200 → 720 s) | Expected 492 s, engine hard stop at **690 s**; every wait bounded; budget guard settles early on the scripted layer. Arithmetic in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 8** in variant `match`, variant `half`, and `certification.game_config`; `<SEATS>` = 8 in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**grf-football is 11 v 11 association football on an 84 m × 54 m pitch in a continuous 2D
top-down physics world.** Twenty-two wheeled cogs and one ball; the ball can leave the pitch
(throw-ins, corners, goal kicks); goals win the match. Each cog's action for one tick is one byte
drawn from a **19-action gfootball vocabulary** — eight directions plus idle, short/long/high pass,
shot, sprint and release-sprint, dribble and release-dribble, slide, release-direction.

**How this differs from the shipped `cogball` (they coexist; neither becomes the other):**

| | cogball | grf-football |
|---|---|---|
| Bodies | 6 robots, 2 seats (one seat = a whole trio) | **22 cogs, 8 seats** (one seat = one shirt) |
| Pitch | 40 × 25 m, fully walled, no out of play | 84 × 54 m, **ball goes out**: throw-in, corner, goal kick |
| Actions | 8-bit thrust/turn/brake/kick actuators | **19 discrete gfootball actions**: 8 directions, short/long/high pass, shot, sprint, dribble, slide |
| Unseated players | none — every robot is commanded | **7 per side run the built-in AI**, incl. the keeper |
| Match | 3:20, 40 turns of 5 s | 4:00 in two halves, 24 turns of 10 s |

### Seats — `num_agents` = 8, fixed everywhere

**`num_agents` = 8. Four seats per team; each seat commands exactly one outfield shirt for the whole
match.** The other seven shirts on each side — including the keeper — are driven by the engine's
**built-in AI** (§Decisions), which is the idea's own "fill unseated players with the built-in AI".

Seat → team → shirt is fixed and derived from the seat index, so it needs no config and inherits
ctf's slot dealing (`teamForSlot` deals `slot mod teams`, so seat parity *is* the team):

| Seat | Team | Shirt (alias) | Role |
|---|---|---|---|
| 0 | red | `RED-10` | playmaker (attacking mid) |
| 1 | blue | `BLUE-10` | playmaker |
| 2 | red | `RED-9` | striker |
| 3 | blue | `BLUE-9` | striker |
| 4 | red | `RED-7` | winger (right) |
| 5 | blue | `BLUE-7` | winger |
| 6 | red | `RED-6` | anchor (holding mid) |
| 7 | blue | `BLUE-6` | anchor |

Why 8 and not 22, 6 or 2: an LLM seat costs one Claude call per turn and the hosted Bedrock sidecar
caps an episode at **30 requests/minute**, so seats × turns is the hard budget (§Decisions gives the
arithmetic — 8 seats × 24 turns = 192 calls is the largest grid that fits inside 690 s with a retry
and a rate floor). Four seats a side is also the smallest count that puts a *decision-maker in every
phase of play*: a striker, a creator, a wide runner and a defensive-midfield screen. The remaining
seven shirts a side are the idea's built-in AI, which keeps the game recognisably 11-a-side without
paying for 22 LLM calls a turn. `num_agents` is **8** in both manifest variants and in the
certification fixture; nothing in the repo offers another seat count.

The built-in AI is deliberately *disciplined but unimaginative* — it holds shape, tackles when the
ball is at its feet, and passes to the nearest better-placed teammate but never carries the ball
more than 8 m — and it **defers to a seated shirt**: when a seated cog and a built-in cog of the
same team are both within 3 m of a loose ball, the built-in cog yields (it steers to a support point
instead of the ball). That is what makes the eight seats, not the engine, decide matches.

### Pitch, units, and why they are integers

The whole sim is **integer** arithmetic. Positions are **micrometres (µm)** and velocities **µm per
tick**, both `int32`; ball height `z` is µm; angles are **brads** (256 per turn, 0 = east,
counter-clockwise on screen — ctf's `sim_types.nim` convention). This is ctf's own determinism
discipline, and it is load-bearing: the replay is re-simulated in the browser by the **wasm32**
build of the same Nim module the **native amd64** server ran, and the per-tick `gameHash` chain must
match bit for bit. Integers make that true by construction instead of by an argument about libm.

| Thing | Value |
|---|---|
| Map scale | 1 map pixel = **75 000 µm** (0.075 m) |
| Board (map) | `MapWidth = 1200`, `MapHeight = 800` → 90 m × 60 m including the surround |
| Pitch (in play) | x ∈ [3 000 000, 87 000 000], y ∈ [3 000 000, 57 000 000] µm — **84 m × 54 m** |
| Centre spot | (45 000 000, 30 000 000); centre circle r = 9 000 000 |
| Goal mouths | plane x = 3 000 000 (red defends) and x = 87 000 000 (blue defends), y ∈ [26 000 000, 34 000 000] — **8 m** wide |
| Goal boxes (netting) | x ∈ [600 000, 3 000 000] and [87 000 000, 89 400 000], same y band; posts are static circles r = 100 000 at the four mouth corners |
| Penalty areas | x ≤ 19 000 000 (red's) / x ≥ 71 000 000 (blue's), \|y − 30 000 000\| ≤ 20 000 000 — 16 m × 40 m |
| Six-yard boxes | x ≤ 8 500 000 / x ≥ 81 500 000, \|y − 30 000 000\| ≤ 10 000 000 |
| Surround | the 3 m band outside the pitch on every side; cogs may stand in it, the ball is out the moment its **centre** crosses the pitch edge |
| Cog radius | 500 000 µm; ball radius 220 000 µm |

**View coordinates** — the only coordinates a policy sees or sends — are metres with the origin at
the centre spot, x toward blue's goal: `X = (x_µm − 45 000 000)/1 000 000`,
`Y = (y_µm − 30 000 000)/1 000 000`. So the pitch is X ∈ [−42, +42], Y ∈ [−27, +27], red attacks
`+X` and defends `−42`, blue the mirror, and the goal mouths are |Y| ≤ 4.

### Time

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf**, because every speed-coupled layer
(`PlaybackSpeeds`, the lull scan, the momentum series, `tickTime`, the transport bar) is keyed to
it. Each tick integrates **4 substeps** of 1/96 s, so the fastest ball (32 m/s) moves 0.33 m per
substep, less than its 0.44 m diameter, and cannot tunnel through a cog or a post.

A match is **`maxTicks = 5760` ticks = 240 s = 4:00**, played as **two halves of 2880 ticks**
(half-time at tick 2880: the ball returns to the centre spot, every cog returns to its formation
anchor, and the team that did *not* kick off at 0 kicks off). **Ends are not swapped at half-time** —
red defends −42 for the whole match — so the scorebug, the feed and every recorded coordinate mean
one thing for the whole replay.

Decisions run on **`turnTicks = 240` ticks (10.0 s)** → **24 decision turns per match**, 12 per half.

### The 19 actions, and how they fit ctf's one-byte action log

A cog's action for one tick is exactly **one `uint8`** — the same byte ctf records with
`writeInputMaskChange`, the same byte `sim.step(inputs, prevInputs)` consumes, the same byte the
wasm viewer replays. Only the *interpretation* changes, so the whole replay codec is untouched:

| Bits | Field | Values |
|---|---|---|
| 0–3 (`b and 0x0F`) | direction | `0` = none (release_direction / idle), `1..8` = N, NE, E, SE, S, SW, W, NW (screen convention, y down). `9..15` are illegal → read as `0`. |
| 4–6 (`(b shr 4) and 0x07`) | one-shot action | `0` none, `1` short_pass, `2` long_pass, `3` high_pass, `4` shot, `5` slide, `6` dribble_on, `7` dribble_off |
| 7 (`b and 0x80`) | sprint | set = sprint held; clear = release_sprint |

That is gfootball's nineteen actions exactly: idle, 8 directions, short/long/high pass, shot,
sprint, release_direction, release_sprint, sliding, dribble, release_dribble. `sprint` and `dribble`
are **sticky modes** (dribble is toggled by codes 6/7, sprint by bit 7); the rest are one-shot and
cleared after resolution. A pass or shot code from a cog that does not control the ball is recorded
and ignored; `slide` is legal whenever the cog is not already sliding or grounded.

### Ball, movement and contact model (the numbers a builder types in)

- **Cog movement.** Target velocity = direction unit vector (Q12) × mode speed; velocity moves
  toward it by at most `Accel = 25 000` µm/tick² per tick, and decays by `v -= v·96 div 1024` when
  the direction is `0`. Mode speeds: base **250 000** µm/tick (6.0 m/s), sprint **337 500** (8.1
  m/s), dribble **200 000** (4.8 m/s), keeper base **229 000** (5.5 m/s). Sprint and dribble
  together take the dribble speed.
- **Stamina.** `stamina` 0..1000, starts 1000, `−6` per sprinting tick, `+2` per non-sprinting tick.
  Below 200 every mode speed is ×85 %; below 50 the sprint bit is ignored. Stamina is in `gameHash`.
- **Ball, on the ground.** `v -= v·7 div 1024` per tick (rolling friction), capped at
  `BallMaxSpeed = 1 333 333` µm/tick (32 m/s).
- **Ball, in the air** (high pass only). `z` follows an integer parabola: launch `vz` chosen so the
  apex is 4 000 000 µm and the flight lands on the target; `z` is decremented by
  `Gravity = 4 340` µm/tick² per tick. An airborne ball ignores cogs until `z ≤ 400 000`.
- **Passes.** Short: ground, speed **583 333** µm/tick (14 m/s), max range 25 m. Long: ground,
  **916 666** (22 m/s), max 45 m. High: airborne, ground speed **750 000** (18 m/s), max 40 m.
  The target is the teammate with the best `passScore` inside a **±50°** cone about the passer's
  direction bits (or `pass_to` when the directive named a legal teammate);
  `passScore = openness_mm − 2 × distance_to_own_goal_mm`, `openness` = distance to the nearest
  opponent. The ball is aimed at the teammate's position + its velocity × 12 ticks.
- **Shots.** Speed **1 083 333** µm/tick (26 m/s), aimed at the goal-mouth point furthest from the
  keeper. Aim error in brads = `rng.rand(2·E) − E` with `E = 2 + dist_m div 6 + (4 if an opponent is
  within 2 m else 0)`, drawn from ctf's existing seeded sim `Rand` (integer draws only, part of the
  recorded seed, so the wasm re-simulation reproduces it exactly — this is how ctf already fuzzes
  gun aim).
- **Control and interception.** After ball motion, the cog nearest the ball whose centre is within
  `ControlRadius = 1 100 000` µm takes possession **iff** the ball's ground speed ≤ **500 000**
  µm/tick (12 m/s) and it is not grounded/sliding; ties by ascending cog index. A faster ball
  deflects off the cog along the centre normal with restitution 45 % and is marked `deflected`.
  A cog in possession carries the ball at a **dribble offset** of 700 000 µm ahead of its velocity
  (900 000 µm with dribble mode off, 550 000 with it on — dribble mode keeps the ball closer).
- **Slide tackle.** `slide` gives the cog a 12-tick slide: velocity is set to its direction × 400 000
  µm/tick, it cannot change direction, and its collision radius grows to 900 000 µm. If the slide
  volume reaches the ball first, the ball is knocked loose at 250 000 µm/tick along the slide
  direction and possession clears (`tackle` event). If it reaches an **opponent** without having
  touched the ball on any tick of this slide, that is a **foul**: the tackler is *grounded* for 48
  ticks (no input honoured), and the opponent gets an indirect free kick at the contact point.
  After any slide the cog is grounded for 24 ticks. There are no cards and no penalties — a foul in
  the penalty area is a free kick on the 16 m line (stated so a builder does not invent one).
- **Keeper.** Shirt 1, always built-in AI. Inside its own penalty area it **catches** a ball whose
  centre is within 1 500 000 µm and whose speed ≤ 750 000 µm/tick (18 m/s) → dead ball, `save`
  event, goal-kick restart. A faster ball is **parried**: reflected off the keeper with restitution
  60 % and speed capped at 500 000. Outside its area the keeper is an ordinary cog.
- **Cog–cog contact.** Circle separation, each pushed half the penetration, normal impulse with
  restitution 20 % (equal masses). No fouls arise from this.
- **Cogs and the boundary.** A cog's centre is clamped inside the board box
  (x ∈ [300 000, 89 700 000], y ∈ [300 000, 59 700 000]) and its normal velocity zeroed. Cogs never
  leave the board; only the ball goes out of play.

### Out of play and restarts

The ball is **out** when its centre crosses a pitch edge (goal-mouth crossings are tested first).

| Trigger | Restart | Taker | Spot |
|---|---|---|---|
| Ball fully over a touchline (y < 3 000 000 or y > 57 000 000) | **throw-in** to the team that did *not* touch it last | nearest teammate to the spot | the crossing point on that touchline |
| Ball over a goal line outside the mouth, last touched by an **attacker** | **goal kick** | the defending keeper | the six-yard box corner nearest the crossing |
| Ball over a goal line outside the mouth, last touched by a **defender** | **corner** | nearest attacking teammate | the corner arc on that side |
| Ball fully inside a goal mouth | **goal** → kickoff by the conceding team | that team's shirt 10 | centre spot |
| Keeper catch | goal kick | keeper | six-yard box centre |
| Foul | **free kick** to the fouled team | nearest teammate to the spot | contact point, clamped to ≥ 16 m from the goal line inside a penalty area |
| Half-time / match start | **kickoff** | shirt 10 of the kicking team | centre spot |

Every restart is a **dead-ball phase** lasting `RestartTicks = 36` (1.5 s): the ball sits on the
spot and cannot be touched; the taker is snapped to 800 000 µm behind the spot; every opponent
inside 5 000 000 µm of the spot is pushed radially out to exactly 5 000 000 µm; all other cogs move
normally under their own control (they spread and mark). On the last tick the ball becomes live with
the taker in possession, and a `restart` event fires. There is **no offside** in v1 and no advantage
rule; both are named in §Out of scope.

**Stalemate guard (sim-level, so no policy can defeat it).** If the ball's centre stays inside a
2 000 000 µm box for **480 ticks (20 s)** with no possession change, the referee restarts play: the
ball is dropped at the nearest of four neutral spots ((±21 m, ±13.5 m) in view coordinates), every
cog within 5 m is pushed out to 5 m, a `drop` event fires and the counter resets. It is inside
`gameHash`, so it is part of the recorded truth.

### Resolution order — exact, every tick `t`, no exceptions

1. **Turn boundary.** If `t mod 240 == 0` and the match is not over: each seat's directive collected
   for turn `t div 240` becomes its active directive; one `directive` record per seat is written to
   the replay chat stream. Active directives live in `sim.activeDirective[seat]`, which is
   **excluded from `gameHash`** (ctf's rule for `damagePops`/`skin`) — nothing a coach says can move
   the hash chain, only the action bytes it produces can.
2. **Timers.** Decrement, per cog: `slideTicks`, `groundedTicks`, `passCooldown` (12 ticks),
   `shotCooldown` (18 ticks); globally: `restartTicks`, `stalemateTicks` bookkeeping.
3. **Control compile.** For each cog in index order 0..21 (`RED-1..11` then `BLUE-1..11`), the
   deterministic control layer (§Decisions) reads the sim state plus — for the eight seated shirts —
   that seat's active directive, and emits one `uint8` action byte. Unseated shirts get the built-in
   AI's byte. During a restart the taker's byte is forced to `0x00` and every other cog's action
   nibble is forced to `0`.
4. **Record.** The 22 bytes go to `sim.step(inputs, prevInputs)` and to
   `replayWriter.writeInputFrameMasks` (ctf's function, unchanged). **This is the determinism
   boundary.** The control layer, the built-in AI and the LLM live *outside* it: the viewer never
   runs them, it feeds the recorded bytes to the identical physics core.
5. **Modes.** Apply the sprint bit and the dribble toggles; update `stamina`; start a slide for any
   cog whose action code is `5` and which is neither sliding nor grounded (emit `slide_start`).
6. **On-ball actions**, in cog index order, for the cog in possession only: action code `1/2/3`
   releases a pass (§Ball model), `4` a shot, and possession clears. A pass/shot from a cog with
   `passCooldown`/`shotCooldown` > 0 is dropped. Emit `pass` (with `kind`) or `shot` (with
   `on_target` computed from the goal-plane crossing).
7. **Four substeps** (`hs = 1/4 tick`), each in this exact order:
   1. **Cog integration**, index order: accelerate toward the target velocity, apply drag, cap to
      the mode speed, `pos += v div 4`.
   2. **Ball integration**: friction, cap, `ballPos += v div 4`; if airborne, `z += vz div 4` and
      `vz -= Gravity div 4`.
   3. **Cog–cog** contact, unordered pairs in ascending index order.
   4. **Cog boundary** clamp.
   5. **Slide volumes** vs ball, then vs opponents, in cog index order → tackle or foul.
   6. **Ball vs cogs**, index order → control, deflection, or (keeper, in area) catch/parry.
   7. **Ball vs posts** (restitution 70 %, emit `post`) and **ball vs netting**.
   8. **Goal test**: the ball centre crossing `x ≤ 3 000 000` or `x ≥ 87 000 000` inside
      `26 000 000 ≤ y ≤ 34 000 000`. On a goal: abandon the remaining substeps, increment the
      scorer's team, emit `goal` (`scorer` = last toucher, `assist` = the previous distinct
      same-team toucher within 144 ticks or `null`, `ballSpeed`, `scoreAfter`), and enter the
      kickoff restart.
8. **Out-of-play test** (only if no goal): touchline / goal line → the restart table above; emit
   `out` then the restart event.
9. **Possession bookkeeping.** `possessionTicks[team] += 1` for the team of the current controller
   (nothing before the first touch); `lastTouchCog`/`lastTouchTeam`/`lastTouchTick`; per-cog
   `passes`, `passesCompleted` (next touch is a same-team cog within 144 ticks), `interceptions`,
   `shots`, `shotsOnTarget`, `tackles`, `fouls`, `distance`.
10. **Stalemate counter** (§ above) and, at `480`, the neutral drop.
11. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's chain, unchanged.
    `gameHash` mixes tick, phase, restart state, score, and every cog's position, velocity,
    direction, modes, stamina and timers, plus the ball's position, velocity and `z`. It never
    mixes directives, notes, FX or trails.
12. **Boundaries.** If `t + 1 == 2880`: half-time (emit `halftime`, reset to formation anchors,
    kickoff for the other team). If `(t + 1) mod 240 == 0`: emit `turn_end`, and if
    `|goals[red] − goals[blue]| ≥ 5` end the match (`mercy`). If `t + 1 ≥ 5760`: end the match
    (`full_time`).

**Kickoff / formation reset (exact).** Ball on the centre spot, zero velocity, `z = 0`. Every cog is
placed at its shirt's formation anchor in its own half, all velocities, modes and timers zeroed,
stamina restored to `min(1000, stamina + 250)` at half-time and to 1000 at match start. The 4-3-3
anchors, in view coordinates for **red** (blue mirrors in X):

| Shirt | Role | Anchor (X, Y) m | Driver |
|---|---|---|---|
| 1 | keeper | (−39, 0) | built-in AI |
| 2 | right back | (−30, −16) | built-in AI |
| 5 | centre back | (−31, −6) | built-in AI |
| 4 | centre back | (−31, +6) | built-in AI |
| 3 | left back | (−30, +16) | built-in AI |
| **6** | anchor | (−22, 0) | **seat 6** |
| 8 | centre mid | (−14, +9) | built-in AI |
| **10** | playmaker | (−12, −5) | **seat 0** |
| **7** | right wing | (−6, −19) | **seat 4** |
| **9** | striker | (−4, 0) | **seat 2** |
| 11 | left wing | (−6, +19) | built-in AI |

The kicking team's shirt 10 stands 800 000 µm behind the ball; every cog of the other team is
outside the centre circle. Each cog gets a deterministic Y jitter of `rng.rand(600_000) − 300_000`
µm from the seeded sim RNG — the idea's "seeded kick-offs".

### Scoring, sign, and what the league ranks by

Team zero-sum and margin-sensitive; every seat on a team gets its team's score:

```
gd(team)    = goals[team] − goals[other]
score(seat) = 0.5 + 0.5 · clamp(gd(team of seat) / 3, −1, +1)
```

**Higher is better.** 3–0 or better = 1.000; 2–0 = 0.833; 1–0 = 0.667; any draw = 0.500; 0–1 =
0.333; 0–3 or worse = 0.000. The eight `scores` sum to exactly **4.000** in every legal outcome, and
the two team scores always sum to 1.000 — that is the zero-sum property the ladder needs.
`win[seat] = gd(team) > 0`. **The league ranks by Elo computed from `results.scores`** (Elo 1000
start, K 32, per the phase-50 league settings); `results.scores` is the only cross-game ranking
input. A `fault` episode scores 0.500 for all eight seats with `win` all false — an infra fault is
nobody's loss. Per-seat football statistics (goals, assists, passes, tackles) are reported for the
board and the feed but are **not** in the score: the idea's "optional checkpoint shaping" is
deliberately **off** in v1 (§Out of scope), because a shaped individual reward is exactly what makes
a team zero-sum game collusion-friendly.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `full_time` | 5760 ticks played. The normal ending. |
| `complete` | `mercy` | Goal difference ≥ 5 at a turn boundary. The rules ended the match; still a complete game. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (**690**) elapsed before full time. The score at that instant stands and is scored by the same formula, the replay is complete up to the stop tick, and the game-over frame is written. Declared acceptable for phase-60 verification: it means the hosted LLM was slow, not that the game broke. |
| `fault` | `sim_fault` | A physics invariant guard tripped (a body outside the board box, a non-representable velocity, a ball with no defined phase). Scores 0.500 × 8, `win` all false, partial replay written. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (1440 = 60 lobby
seconds) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only), that shirt is driven by the `zonal` baseline for
the whole match, and the match plays to `full_time`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {zonal, gegenpress}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=zonal`. A scripted policy seated as a champion is a failure state.

### Where the decision happens

In the **game server**, exactly as in the paintball starter: `src/grf_football/decide.nim` is ctf's
`src/ctf/decide.nim` retargeted, and `src/grf_football/llm.nim` is ctf's `llm.nim` kept as is —
credential ladder (Bedrock sidecar via `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
`AWS_BEARER_TOKEN_BEDROCK` → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` → **disabled**, which
makes offline certification finish in seconds), the single Bedrock candidate
`us.anthropic.claude-haiku-4-5-20251001-v1:0` with `BEDROCK_MODEL` pinning, the fail-fast on 429
with no second candidate, `max_tokens` from `maxOutputTokens` (default **900**), no
`output_config.effort`, the fence-tolerant `extractJsonObject`, and rune-boundary truncation. The
`anthropic_api_key` secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/grf-football/anthropic_api_key`);
phase 60 greps the **game** log for `falling back`.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **240 ticks (10.0 s of match time)**, **24 turns** per match. At each turn
the server builds **all eight** seats' request bodies and issues them as **one parallel batch** —
`client.curl.makeRequests(batch, deadlineSeconds)`, curly's batch API, the shape the playbook names
for Nim. Seats are never queried sequentially: this is a simultaneous-decision game. One call per
seat per turn covers that seat's whole shirt, so an episode is at most 8 × 24 × 2 = 384 requests and
normally 192.

Per turn: attempt-1 batch deadline **`attempt1Ms = 6000`**; every seat that timed out, errored,
returned non-JSON or returned no usable order is retried **once** as a single batch with
**`retryMs = 3000`**; the whole turn is wrapped in a monotonic **`turnBudgetMs = 10000`** cap. (Both
deadlines are whole seconds because curl's `CURLOPT_TIMEOUT` granularity is whole seconds — the
starter's scar; `sim_config` rejects a sub-second value.) A **rate floor** holds consecutive batch
*starts* `turnSpacingMs = 18000` apart, which pins the episode at 8 × 60/18 ≈ **26.7 requests/minute**,
inside the sidecar's 30/min episode cap. The cert fixture sets `turnSpacingMs = 0`, so offline runs
pay nothing.

```
24 turns × 18 s (the rate floor dominates the 10 s turn cap)   = 432 s
lobby / connect wait (typical 15 s; cap 1440 lobby ticks = 60 s)
                                                       typical =  15 s
5760 ticks of play — fastMode, all seats report ready          =  25 s
                     (24 fps wall-clock-paced worst case       = 240 s)
game-over hold + results + replay write                        =  20 s
                                                               -------
expected total                                                 = 492 s   < 720 s (60 % of 1200)
engine hard stop wallClockBudgetSeconds                        = 690 s   → reason "deadline"
platform kill (episodeTimeoutSeconds)                          = 1200 s
```

**Budget guard (settle early, never overrun).** At the start of each turn, if
`elapsed + 2 × turnSpacingSeconds > wallClockBudgetSeconds`, the LLM is switched off for every
remaining turn and the match finishes on the scripted layer (microseconds per turn), so the episode
ends `complete/full_time` rather than `deadline`; a `budget_guard` record names the turn it fired.
The pathological case — a dead player container forcing the frame limiter to pace at 24 fps — is
therefore caught at ~654 s elapsed, and only if the remaining sim still cannot finish by 690 s does
the engine stop and report `deadline` with the score standing.

**Degrade, never hang.** Every wait is bounded: two batch deadlines, the outer per-turn deadline,
`lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread (which runs
independently of the game loop, so a 9 s LLM stall cannot drop a connection), the 690 s engine stop,
and ctf's `gameOverTicks` hold before exit. **Decision timeout or parse failure → retry once →
scripted fallback:** on the second failure the seat plays the **`zonal`** directive for that turn and
a `fallback` record is written with `cause ∈ {timeout, parse_error, transport_error, throttled,
no_credentials, budget_guard}`. A seat that disconnects mid-match keeps playing (its shirt degrades
to `zonal` and revives on reconnect). **No failure mode leaves a cog unactuated** — the control layer
always has a directive: this turn's, else last turn's, else `zonal`'s.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are one footballer in an 11-a-side match, played in a top-down 2D physics world.
You control ONE shirt. Your other ten teammates are run by the engine's built-in AI:
they hold a 4-3-3 shape, tackle when the ball is at their feet, pass to the nearest
better-placed teammate, and never dribble far. Three other shirts on your team are
controlled by other policies you cannot talk to.
Every 10 seconds of match time you issue ONE order for your shirt. A deterministic
controller executes it for the next 10 seconds: it steers your cog, sprints, tackles
and plays the ball for you according to your order.
The pitch is 84 by 54 metres. You attack toward the goal named in "attacking_goal".
The ball goes OUT: throw-ins, corners and goal kicks are real. There is no offside.
A slide tackle that misses the ball and hits the opponent is a foul: you lose the
ball and lie grounded for two seconds. Sprinting drains stamina; low stamina makes
you slow for the rest of the match.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars",
 "cogs":[{"id":"<your shirt id>",
          "role":"striker|winger|playmaker|anchor",
          "intent":"press|hold_shape|make_run|support|drop_deep|carry|switch_play|shadow",
          "target":[x,y],
          "on_ball":"shoot|pass_short|pass_long|pass_high|dribble|hold",
          "pass_to":"<teammate shirt id or null>",
          "sprint":"auto|always|never",
          "tackle":"auto|never",
          "say":"<=48 chars"}]}
Exactly one entry, for the shirt you control.
Intents: press = close down whoever has the ball; hold_shape = hold your target and
face the ball; make_run = run into space ahead of the ball on your side; support =
offer a short passing option beside the ball; drop_deep = come back toward your own
goal to receive; carry = go get the ball and run with it; switch_play = move to the
far side of the pitch; shadow = mark the nearest opponent.
target is metres: x in [-42,42], y in [-27,27]. It is used directly by hold_shape and
as a bias by everything else.
on_ball is what you do when the ball is at YOUR feet; the controller ignores an
illegal choice (a shot from 60 metres, a pass to nobody) and plays the safe option.
```

**User message** = the seat's `PLAYER_PROMPT` under a "GUIDANCE FROM YOUR OPERATOR" heading (the
starter's `operatorBlock`), a blank line, then the seat view JSON below. The prompt text is never
echoed into the replay — only `policyKind` and the resulting order are.

### Champion #1 — `grf-football-tiki` (owner daveey), `PLAYER_PROMPT`

```
Play possession football and make the pitch big. When your team has the ball, never
stand still: use "support" and put your target 8-12 metres to the side of the ball,
in space, so the built-in AI always has a short pass on. When you are the striker,
use "make_run" the moment a teammate carries the ball past the halfway line, with a
target between the two centre backs. On the ball, prefer "pass_short" to the shirt
named in pass_to unless you are inside 20 metres of their goal, where you use
"shoot". Never use "pass_long" from your own half; use "pass_high" only to switch the
ball to the far wing when your target is more than 25 metres away. Set sprint to
"auto" - you must still have legs in the last minute. When you lose the ball inside
their half, "press" the ball for one turn, then "hold_shape" and reset. As the anchor
shirt, stay between the ball and your own goal: "shadow" their most advanced player
whenever the ball is in your own half, tackle "auto", and never go past the halfway
line while you are level or ahead.
```

### Champion #2 — `grf-football-counter` (owner daveey-1), `PLAYER_PROMPT`

```
Play the counter: sit deep, win the ball, then hit them in the space they left.
While they have the ball, hold a compact shape - "hold_shape" with a target on your
own side, roughly halfway between the ball and your own goal, and "shadow" instead of
chasing. Do not press high; only the shirt closest to the ball presses, and only when
the ball is inside your own half. The moment your team wins the ball, switch for one
turn: the striker takes "make_run" with a target 15 metres behind their back line,
the winger takes "carry" down the touchline with sprint "always", and the playmaker
takes "support" beside the ball. On the ball, "pass_long" to the runner whenever an
opponent is within 3 metres of you, otherwise "carry" while the way forward is open,
and "shoot" from anywhere inside 26 metres of their goal. Use tackle "auto" always,
but never slide when you are the last defender - use "shadow" instead. If you are two
goals ahead, drop everything back: "drop_deep" targets in your own half for the rest
of the match.
```

### The control layer (deterministic, integer-only, shared by every policy)

`src/grf_football/control.nim`, the starter's `control.nim` retargeted. Both LLM orders and scripted
orders are compiled by the *same* code, so the two policy kinds are strictly comparable. Pure
function of `(sim state, order, cog index)` → `uint8`, evaluated every tick:

1. **Steering point `p*`** (µm; `b` = ball, `vb` = ball velocity, `G` = opponent goal centre,
   `Gown` = own goal centre, `A` = the shirt's formation anchor translated by
   `(b − centre) × 30 %` and clamped to the shirt's zone band):
   - `press`: the opponent controlling the ball, + its velocity × 8 ticks; if the ball is loose,
     `b + vb·τ` with `τ = clamp(dist div (250 000 + |vb|), 0, 48)`.
   - `hold_shape`: `order.target` (clamped into the pitch on parse), blended 50 % with `A`.
   - `make_run`: `(b.x + 12 m·attackDir, order.target.y)`, clamped to the pitch.
   - `support`: the point 9 m from the ball, on the own-goal side, on the free flank.
   - `drop_deep`: the midpoint of `b` and `Gown`.
   - `carry` / when this cog controls the ball: `G` (with dribble mode on).
   - `switch_play`: `(A.x, −sign(b.y) · 18 m)`.
   - `shadow`: the nearest opponent + its velocity × 12 ticks.
   - Every intent except `hold_shape` blends `order.target` as a 25 % bias:
     `p* = (p*·3 + target) div 4`.
   - **Override, always**: if the ball is loose and this cog is the closest of its team to it, `p*`
     becomes the interception point regardless of intent. A footballer who can win the ball, wins it.
2. **Direction bits** = the 8-way quantisation of `p* − pos` (nearest of the 8 compass brads);
   `0` when `dist(p*, pos) < 400 000` and the cog is not chasing the ball.
3. **Sprint bit**: `always` → set while `stamina > 100`; `never` → clear; `auto` → set when chasing
   a loose ball more than 6 m away, on a `make_run`, or carrying with an opponent within 4 m.
4. **On-ball code** (only when this cog controls the ball, cooldowns clear):
   `shoot` → code 4 if inside 30 m of `G` and no teammate is inside the shooting lane, else the safe
   option; `pass_short`/`pass_long`/`pass_high` → codes 1/2/3 if a legal receiver exists in range
   (`pass_to` first, else the best `passScore`), else the safe option; `dribble` → code 6 once then
   direction toward `G`; `hold` → shield (direction away from the nearest opponent).
   **The safe option** is the built-in AI's on-ball rule (§next).
5. **Tackle**: code 5 when `order.tackle != "never"`, an opponent controls the ball within
   1 600 000 µm, the closing angle is ≤ 45°, and this cog is not grounded.
6. **Dribble mode** is turned on when carrying with an opponent within 5 m and off otherwise
   (codes 6/7), so the sticky mode is always in a defined state.

### The built-in AI (the engine-side "rest of the team")

`src/grf_football/builtin_ai.nim`. Drives the 14 unseated shirts, is the "safe option" above, and is
a pure function of `(sim, cogIndex)` with **no RNG**. Per tick:

1. **Keeper (shirt 1):** hold the arc 2 m in front of the goal at `y = clamp(b.y/2, ±3.5 m)`; come
   off the line toward the ball when the ball is inside the six-yard box and no defender is closer;
   catch/parry per the ball model; on possession, goal-kick `pass_long` to the most open teammate
   beyond the halfway line, else `pass_short` to the nearest full back.
2. **Off the ball, own team in possession:** move to the translated anchor `A`; the two forwards
   push 8 m further up-field; the nearest teammate to the ball's forward channel takes a support
   point 9 m beside the ball. **A built-in cog within 3 m of a loose ball yields to a seated
   teammate within 3 m** (it takes the support point instead).
3. **Off the ball, ball loose or opponent in possession:** the nearest own cog chases (sprint beyond
   6 m); the second nearest covers the lane between the ball and the nearest opposing forward; every
   other cog holds `A` and shadows the opponent nearest its zone.
4. **On the ball (the safe option):** an opponent within 2.5 m → `pass_short` to the best
   `passScore` teammate; else inside 20 m of `G` with a clear cone → `shot`; else the nearest
   opponent beyond 6 m and the lane forward clear → carry at most 8 m, then re-evaluate; else
   `pass_long` to the most advanced open teammate; `pass_high` when the direct lane is blocked and
   the target is beyond 25 m.
5. **Tackle:** slide only when an opponent controls the ball within 1 600 000 µm and this cog's
   velocity is within 45° of the ball — deterministic, never probabilistic.

### Scripted baselines (`PLAYER_SCRIPTED`)

Both emit the *same* order object an LLM does, on the same 10 s cadence, so their output is legal by
construction and directly comparable — that is what makes the bounded-orders test in §Tests
meaningful. Both are pure functions of the world state.

- **`zonal`** — the certification player, the per-turn fallback, the driver for a no-show seat, and
  the default. Role = the shirt's role. `intent`: own team in possession → `support` (forwards:
  `make_run` once the ball is past the halfway line); opponent in possession and the ball within
  15 m → `press`; ball loose → `carry`; otherwise `hold_shape`. `target` = the shirt's translated
  anchor `A`. `on_ball` = `shoot` inside 20 m of the goal, `pass_short` with an opponent within
  2.5 m, else `carry`. `sprint: auto`, `tackle: auto`. Fixed short `note`/`say`.
- **`gegenpress`** — the second filler, deliberately different in shape and weaker over 4:00:
  `intent = press` whenever the opponent has the ball anywhere in the attacking two-thirds,
  `make_run` when its own team has it, `shadow` only inside its own penalty area. `target` = 6 m
  ahead of the ball toward the opponent goal. `on_ball` = `shoot` inside 26 m, else `pass_short`.
  `sprint: always` — which is exactly why it fades: stamina bottoms out around the 3rd minute and its
  cogs run at 85 % while `zonal` still has legs. Gives the ladder a spread.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf/paintball arena rules go** (guns, hearts, fog of war, lives, respawn, grenades,
spray cans, shields, barriers, puddles, trenches, perks, handicaps, barrage, the hill, floor paint
and the procedural map generator all leave the repo):

| ctf path | grf-football |
|---|---|
| `src/ctf/sim.nim` (4102 lines: combat, vision, items, hill, paint) | `src/grf_football/sim.nim` — the football core and the step loop of §The game. |
| `src/ctf/arena.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `paint.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `docs/MAPKIT.md`, `docs/pool-review.html` | `src/grf_football/pitch.nim` — one fixed 1200 × 800 board: geometry constants, the boundary/goal half-planes, and the pixie turf bake. No generator, no pool, no editor. **Deleted, not ported.** |
| `src/ctf/global.nim` fog of war, vision cones, first-person raycast, killfeed art, weapon sprites | `src/grf_football/global.nim` — pitch/cog/ball/trail/FX sprite composition. Perfect information: no fog. |
| `players/baseline/baseline.nim` (the 3236-line CTF bot) | `src/grf_football_player.nim` — a thin registrar (§Server). |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/plans/*`, `client/league_replayer.html` | rewritten (or deleted, for `league_replayer.html` — §Viewer). |
| `arena/`, `caos/`, `caos-tools/`, `scripts/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/symnone_*`, `tools/render_replay_movie*`, ctf's `tests/*` | deleted. |

**Kept** (mechanical `ctf` → `grf_football` / `CTF_WIRE` → `GRF_WIRE` rename sweep only; a CI grep
asserts no `ctf`/`CTF` identifier survives outside comments):

| Path | Why |
|---|---|
| `src/ctf/replays.nim` | the whole replay codec: header, resolved-config JSON, joins, per-cog input-byte changes, chat records, keyframes, per-tick hashes, lull spans, beats, seek/speed commands, `checkReplayHash`. |
| `src/ctf/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports. |
| `src/ctf/server.nim` | mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, the `COGAME_*` contract, `declarePlayerFailure`, the artifact-write block. |
| `src/ctf/decide.nim`, `llm.nim`, `directives.nim`, `baselines.nim`, `control.nim` | the squad-command LLM layer: one parallel batch per turn, one bounded retry, the budget guard, the record vocabulary, tolerant parsing, rune truncation. Retargeted intents/roles, same machinery. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/broadcast.nim`, `labels.nim`, `rig_art.nim` | the state-JSON builder, HUD labels, the wheeled-rig art compositor. |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | the emscripten link flags and the OffscreenCanvas Worker (§Viewer). |
| `client/broadcast_core.js`, `client/chrome_common.js`, `client/replay_broadcast.html`, `client/art/` | the broadcast chrome (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `config.json` | the build, the fixture recorder, the forensics tools, the pinned toolchain. |

### Arithmetic rules (the determinism contract)

- **No floating point anywhere under `src/grf_football/{sim,pitch,control,builtin_ai}.nim`** — no
  `sin`, `cos`, `arctan2`, `sqrt`, `pow`, `float*`. Grep-enforced in CI. Floats stay legal in the
  *render* modules (`global.nim`, `rig_art.nim`), which never enter `gameHash`, exactly as in ctf.
- Trigonometry is a **committed literal table** `SinQ12*: array[256, int32]` in
  `src/grf_football/trig.nim`, generated once by `tools/gen_trig_table.nim` and checked in;
  `cosQ12(b) = SinQ12[(b + 64) and 255]`. A test re-derives every entry from `math.sin`.
- `isqrt(v: int64): int64` (Newton, integer seed) is the only square root; `bradsOfVectorI(dx, dy)`
  is the integer atan2 (octant fold + 5-step binary search on `dy·cosQ12 ≶ dx·SinQ12`).
- Every division is an explicit truncating `div`, so the arithmetic is symmetric under negation and
  the two ends of the pitch are exactly fair.
- Randomness: ctf's seeded sim `Rand` from `config.seed`, integer draws only, used for exactly two
  things — kickoff Y jitter and shot aim error.

### How the replay achieves server ↔ viewer determinism

1. The server writes the starter's binary replay: magic + format version + game name/version header,
   the **resolved config JSON** (seed, every pitch and tuning constant, roster with real names), then
   the record stream — joins, leaves, per-cog input-byte changes, chat records (register, directive,
   fallback, budget_guard, result) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/grf_football_replay.nim` — which imports the
   **same** `src/grf_football/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` container.
3. In the browser the module re-steps the sim from the recorded bytes and compares `sim.gameHash()`
   with the recorded hash every tick; a divergence surfaces as `mismatchTick` in `#mmwarn`.
4. CI proves the cross-build equality on every push: `wasm-viewer` runs
   `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer tests/fixtures/grf-679961.replay 300`,
   which fails if `mismatch_tick() != -1`, against a fixture recorded by the **native amd64** build.

Because the recorded action log is the 22 action bytes, the control layer, the built-in AI and the
LLM are all *outside* the determinism boundary — "the controller was reimplemented in the viewer and
drifted" is structurally impossible.

Perf target: 5760 ticks of physics plus serve in under 30 s on a CI runner; `tests/test_perf.nim`
bounds it at 120 s.

---

## Server, player, protocol

`src/grf_football/server.nim` is ctf's `server.nim` retargeted: same routes (`GET /healthz`,
`GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`, `GET /client/player`,
`GET /client/replay`, `GET /replay-data`), same `COGAME_*` runtime contract (`COGAME_CONFIG_URI`,
`COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`,
`COGAME_EVENTS_URI`, `COGAME_METRICS_URI`, `COGAME_HOST`/`COGAME_PORT`), same 403 on a bad
slot/token, same done-before-artifact-writes ordering, and `src/grf_football.nim` as the entrypoint
(seed randomisation before `config.update`, kept verbatim).

### The player container

`src/grf_football_player.nim` (built to `/bin/grf-football-player`) reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects, and sends **one Sprite v1
chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"zonal"|"gegenpress"|null,"policy":"<free label>"}
```

It then sends the Sprite v1 Ready packet (`0x85`) after each received frame — legitimate here
because it never sends inputs (the server computes every action byte) and it is what lets `fastMode`
pace the match by readiness — and otherwise only receives. Registration is re-sent once after the
first received frame in case the first send raced slot registration. A seat that never registers, or
registers with neither field, is `scripted: "zonal"`.

### Per-seat observation — exactly what is visible and what is hidden

Football is a perfect-information sport, so ctf's fog of war, vision cones, windows and first-person
raycast are **deleted**. Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one
binary message per tick.

**Visible to a seat:** the whole pitch and every one of the 22 cogs (position, velocity, facing,
sprint/dribble/slide state, stamina); the ball (position, velocity, height, controller); the score;
the clock, half and turn index; the current restart phase and taker; which shirt it commands; its own
last directive; and the last turn's own statistics. **Hidden from a seat:** every other seat's
directive, prompt, note, `say` and view; the episode seed; the built-in AI's internal target points;
**real policy names** (board labels carry only `RED-9`-style aliases — `showPlayerLabels` is forced
false on the player stream); and every future tick.

### The per-seat view given to the LLM

View coordinates (metres, centred), rounded to 1 decimal. This object is the tail of the LLM user
message and is mirrored into the `directive` record for the feed.

```json
{"turn": 7, "of": 24, "half": 1,
 "clock": {"played_s": 70.0, "left_s": 170.0},
 "score": {"you": 1, "them": 0},
 "you": {"id": "RED-9", "role": "striker", "team": "RED",
         "attacking_goal": [42.0, 0.0], "defending_goal": [-42.0, 0.0]},
 "pitch": {"x_min": -42, "x_max": 42, "y_min": -27, "y_max": 27,
           "goal_half_width": 4.0, "your_penalty_area": "x <= -26, |y| <= 20",
           "offside": false},
 "phase": "playing" | "throw_in" | "corner" | "goal_kick" | "free_kick" | "kickoff",
 "restart": {"kind": "corner", "team": "RED", "taker": "RED-7", "ticks_left": 24},
 "ball": {"pos": [3.2, -1.0], "vel": [4.1, 0.6], "speed": 4.2, "height": 0.0,
          "controller": "BLUE-4" | null, "in_your_half": false},
 "your_cog": {"id": "RED-9", "pos": [6.1, -2.4], "vel": [2.0, -0.4], "speed": 2.0,
              "stamina": 780, "sprinting": false, "dribbling": false,
              "grounded": false, "dist_to_ball": 3.4, "has_ball": false,
              "nearest_opponent": {"id": "BLUE-5", "dist": 2.1}},
 "your_team": [{"id": "RED-10", "pos": [-1.2, 4.0], "role": "playmaker",
                "driver": "seat" | "builtin", "dist_to_ball": 5.5}, "… 10 …"],
 "their_team": [{"id": "BLUE-4", "pos": [4.0, -1.0], "dist_to_ball": 1.1,
                 "has_ball": true}, "… 10 …"],
 "last_turn": {"your_passes": 3, "your_passes_completed": 2, "your_shots": 1,
               "your_tackles": 0, "team_possession_pct": 58,
               "goals": [{"tick": 1440, "by": "RED-9", "for": "you"}]},
 "your_last_directive": "… your seat's note last turn, or null on turn 0 …"}
```

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape. `cogs` is an
array because the starter's parser (`parseSquadDirective`) takes one, but a seat commands exactly one
shirt, so it has exactly one entry.

```json
{"note": "sitting on their last man",
 "cogs": [{"id": "RED-9", "role": "striker", "intent": "make_run",
           "target": [24.0, -6.0], "on_ball": "shoot", "pass_to": "RED-10",
           "sprint": "auto", "tackle": "auto", "say": "in behind"}]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `cogs` | array | exactly 1 entry, the seat's shirt | extra entries dropped; a missing entry is filled from **last turn's directive**, else from `zonal` |
| `cogs[].id` | string | the seat's own shirt alias, case-insensitive, **≤ 8 runes** | an unmatched id is assigned to the seat's shirt by position |
| `cogs[].role` | enum | `striker` `winger` `playmaker` `anchor` | → the shirt's table role |
| `cogs[].intent` | enum | `press` `hold_shape` `make_run` `support` `drop_deep` `carry` `switch_play` `shadow` | → `support` |
| `cogs[].target` | [num, num] | finite; clamped to x ∈ [−42, 42], y ∈ [−27, 27] | non-finite/missing → the cog's current position |
| `cogs[].on_ball` | enum | `shoot` `pass_short` `pass_long` `pass_high` `dribble` `hold` | → `pass_short` |
| `cogs[].pass_to` | string \| null | a **teammate** shirt id ≠ self | → `null` (and the controller picks the best `passScore` receiver) |
| `cogs[].sprint` | enum | `auto` `always` `never` | → `auto` |
| `cogs[].tackle` | enum | `auto` `never` | → `auto` |
| `cogs[].say` | string | **≤ 48 runes** | truncated to 48 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized `directive` record
**≤ 900 runes** (asserted in `tests/test_replay.nim`). `register.prompt` is capped at **≤ 4000
runes** at the transport (over-long is truncated, never rejected) and is **never** written to the
replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — `runeLen`/`runeSubStr`, the
starter's `truncateRunes`. Slicing a string by byte index on any path to the replay is forbidden: a
byte-truncated multi-byte character renders fine in a browser and then fails a strict UTF-8 parser.
§Tests pins it with a 4-byte emoji sitting exactly on the cap.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose; accept `cogs` as a bare object or as an object keyed by id; accept numeric strings in
`target`. Only when no object with a usable entry can be recovered do the retry and then the fallback
fire.

### Results document

Written by `sim.playerResultsJson()` to `COGAME_RESULTS_URI`; it must equal the manifest's
`results_schema` key for key (that schema is `additionalProperties: false` and the certifier rejects
any unknown field). Adding or removing a key here means editing `coworld_manifest_template.json` in
the same commit.

```json
{"names": ["daveey", "daveey-1", "grf-football-zonal", "…8…"],
 "scores": [0.667, 0.333, 0.667, 0.333, 0.667, 0.333, 0.667, 0.333],
 "win": [true, false, true, false, true, false, true, false],
 "team": ["red", "blue", "red", "blue", "red", "blue", "red", "blue"],
 "shirt": [10, 10, 9, 9, 7, 7, 6, 6],
 "goals": [0, 1, 2, 0, 0, 0, 0, 0],
 "assists": [1, 0, 0, 0, 1, 0, 0, 0],
 "passes": [14, 11, 9, 8, 12, 10, 16, 15],
 "passesCompleted": [11, 7, 6, 5, 8, 6, 14, 12],
 "shots": [2, 1, 5, 2, 1, 0, 0, 0],
 "tackles": [1, 2, 0, 1, 2, 3, 5, 4],
 "fouls": [0, 0, 0, 1, 0, 0, 1, 0],
 "llmTurns": [24, 24, 24, 24, 0, 0, 0, 0],
 "fallbackTurns": [0, 0, 0, 0, 0, 0, 0, 0],
 "teamGoals": [2, 1],
 "teamShots": [11, 6],
 "teamShotsOnTarget": [5, 2],
 "teamPossessionTicks": [3100, 2660],
 "reason": "complete",
 "endRule": "full_time",
 "finalTick": 5760,
 "seed": 679961}
```

`names` are the **real policy names** (spectator side). `team` and `shirt` carry the in-game
identity. Team arrays are `[red, blue]`.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary** format, not JSON: the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs` — the machinery this fork exists to reuse. The
consequences are handled explicitly:

- CI's `docker-smoke` sets **`SMOKE_REQUIRE_REPLAY_JSON=0`** (the shared script supports it by design).
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only), retargeted, which
  prints one strict-UTF-8 JSON object for a `.replay` path:
  `{"protocol":"grf-football/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"directives":[…],"fallbacks":N,"results":{…}}`.
- **Phase-60 definition-of-done check 4** therefore reads:
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "grf-football/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), and the champion seats' directives `source == "llm"` with non-empty `note`/`intent`
  — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic, format version, `gameName` `grf-football`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents` (8), `maxTicks`, `turnTicks`, every pitch/physics/tuning constant, `players[].name` (real names), `slots[].team`, `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| inputs | per **cog** (0..21), on change: the `uint8` action byte — the action log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 5760 hashes (8 B each) + on the order of 90 k input-change records + 24 × 8 directive records
(≈ 45 KB) — comfortably under 1.5 MB.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields;
they drive the feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `team`, `shirt`, `policy` (≤48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `half`, `seat`, `id`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `cogs`:[{`id`,`role`,`intent`,`target`,`on_ball`,`pass_to`,`sprint`,`tackle`,`say`}] |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at game over |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay:
`phase`, `kickoff`, `touch`, `pass` (`kind`: `short`\|`long`\|`high`; `outcome`:
`complete`\|`intercepted`\|`out`), `shot` (`on_target`), `save`, `goal`, `post`, `tackle`, `foul`,
`out`, `throw_in`, `corner`, `goal_kick`, `free_kick`, `drop`, `halftime`, `turn_end`, `gameover`.
`touch` is throttled to at most one per cog per 8 ticks.

**Scrubber beats** (the subset that gets a marker, and every one has CSS — §Viewer):
`gamestart`, `goal`, `shot` (on target only), `save`, `foul`, `halftime`, `gameover`.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Touch, Pass, Shot, Save, Goal, Post, Tackle, Foul, Out, Restart, Drop,
HalfTime, PhaseChange, Directive`, and the mandatory trailing summary row (`type`, `ticks`, `events`,
`gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's script
with two literals changed (`image_tag`, and the `docker cp` source
`/workspace/grf-football/replay-viewer/dist/.`); it builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copies the dist out. It stays committed **executable** — `coworld
build` hard-requires `os.X_OK` on the hook.

### One starter for all four viewer files

**All four viewer files come from `Metta-AI/coworld-ctf` and only from it:**

| File | Provenance |
|---|---|
| `replay-viewer/config.nims` | ctf's, verbatim apart from the emitted module name |
| `replay-viewer/grf_football_replay.nim` (the wasm entry) | ctf's `replay-viewer/ctf_replay.nim` |
| `replay-viewer/static_replay.js` + `replay-viewer/static_replay_worker.js` | ctf's, verbatim apart from the exported-symbol prefix |
| `index.html` | ctf's `client/replay_broadcast.html`, spliced by ctf's `Dockerfile.replay-viewer` over the `<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->` and `<!-- BROADCAST_CORE -->` markers |

**No file from any other starter is used anywhere in the bundle.** The only edit across the four is
one mechanical rename applied consistently *in the same commit*: `ctf_` → `grf_` in the `exportc`
names (`grf_load_replay`, `grf_frame`, `grf_input`, `grf_packet_ptr`, `grf_packet_len`,
`grf_mismatch_tick`, `grf_error_ptr`, `grf_error_len`, `grf_stage_ptr`, `grf_stage_len`), in
`config.nims`'s `-o` target and `EXPORTED_FUNCTIONS`, in the worker's `Module._…` calls and its
`importScripts('./wire_constants.js', './broadcast_core.js', './grf_replay.js')`, and in
`Dockerfile.replay-viewer`'s `test -f` assertions. The emscripten link flags are **untouched**:
non-`MODULARIZE`, no `EXPORT_NAME`, `-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1
-s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8`, matched by the worker's
`onRuntimeInitialized` bootstrap. Splicing one starter's shell onto another's link flags is what
deadlocked cogame-lantern (2026-08-23) silently; nothing here mixes the two.

`static_replay.js` (kept) is what sets **`data-replay-loaded="true"` on `document.documentElement`
on its first drawn frame** (the Worker's `loaded` message, after the first frame packet is
rendered) and **`data-replay-error` on any failure path** (`showFailure`). Those two attributes are
the signals `tools/ci/viewer_smoke.mjs` waits on; neither is removed or renamed.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte.** Not one character changes. It is
  game-agnostic (team naming from the frame's `teams`/`roster`, the clock, the transport bar and
  speed chips, the scrubber, beat markers, lull shading, the up-front beat timeline, the verdict and
  the momentum curve), which is why the in-game team keys here are **`red` and `blue`** — the keys,
  palette and CSS utility classes it already knows.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The file keeps its CSS, markup,
  `relayout()` and behaviour; football-specific chrome is a single appended `<style>` + `<script>`
  block at the end of the page whose **new nodes are all `fb-`-prefixed** (`#fb-shirtbar`,
  `#fb-possbar`, `#fb-statline`) so nothing can collide with a starter id.
- **Removed from the starter's page, exactly these elements:** the first-person picture-in-picture
  block `#fpv` with `#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`, `#fpv-map`,
  `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip` (no raycast view in football; `pov` stays in the state
  JSON, always `-1`); `#viewpanel` with `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-out`,
  `#zoom-slider`, `#zoom-in`, `#zoom-read`; and inside the score plates the ctf life pips, perk icons
  and handicap chips. **Everything else stays**: `#viewport`, `#stage`, `#board`, `#lightpool`,
  `#grain`, `#lockerroom` (loading screen — only its caption string and sprite sheet change),
  `#chrome`, `#scorebug`, `#plates-l`/`#plates-r`, `#clock`/`#clock-time`/`#clock-caption`,
  `#mmwarn`, `#bannerlane`, `#killfeed`, `#transport` with all its buttons, `#scrub` with `#momentum`
  / `#scrub-fill` / `#lulls` / `#scrub-win` / `#scrub-head`, `#endcard` with `#ec-headline`,
  `#ec-wincond`, `#ec-how`, `#ec-teams`, `#ec-replay`, `#status`, and the `?embed=1` mode.
- **Zoom: dropped.** The pitch is a **fixed arena** — the whole 1200 × 800 board is always letterboxed
  into the frame — so `#viewpanel` (zoom bar + minimap) is removed entirely, per the rule that it
  exists only for boards larger than the frame. `viewer_smoke.mjs` therefore runs with
  `--strict-text-bounds`.
- `client/league_replayer.html` is **deleted** from the repo and from the bundle (its `league.html`
  copy and its `Dockerfile.replay-viewer` assertions go with it): the static bundle's entry is
  `index.html`, and the league shell is a ctf product surface this coworld does not ship.

### Transport rules (kept, and stated so they cannot be lost)

`relayout()` remains the sole owner of `--hudscale`, `--topband` and `--band` on `:root`, and it
still measures the transport strip's natural height into `--band`. **No overlay is ever placed in the
transport band** — the appended game block draws only inside `#stage`'s play area and inside the
existing scorebug/feed lanes. The **endcard stops at `bottom: var(--band, 0px)`** and is **dismissed
by every seek**, exactly as in the starter. **Scrubber beats are clickable, labelled buttons**
(`button.beat-marker`, `aria-label` giving the event and the clock time, click = seek to that tick),
and the appended CSS block defines a rule for **every kind emitted**: `.beat-marker.gamestart`,
`.beat-marker.goal.red` / `.goal.blue`, `.beat-marker.shot`, `.beat-marker.save`, `.beat-marker.foul`,
`.beat-marker.halftime`, `.beat-marker.gameover` (the first and last are the starter's own).

### Readouts (all of them)

1. **Score bug** (top, always on): two plates — real policy names (spectator side; a plate with four
   distinct seat policies lists them comma-joined and ellipsised), team chip, **goals**, shots and
   possession % around the centre clock column. `teams.red`/`teams.blue` carry
   `{goals, shots, sot, poss, passes, tackles, policies}`.
2. **Clock**: `M:SS` from `tick div 24` in `#clock-time`, and `#clock-caption` reading
   `1st half · turn 7/24` (`HALF-TIME` during the half-time restart, `FULL TIME` after).
3. **Match feed** (`#killfeed`): the last rows in plain language — "GOAL RED — RED-9 (assist RED-10),
   24.1 m/s", "BLUE-4 slides in — foul, free kick RED", "RED-7 crosses — headed clear", "corner,
   BLUE". Directive `note` and `say` strings appear here tagged with the shirt; this is where a
   spectator sees the LLM playing.
4. **Ball trail**: the last 40 tick positions as a tapering ribbon tinted by the last toucher's team,
   plus a shadow-and-scale treatment while the ball is airborne (a high pass visibly leaves the
   ground). Drawn Nim-side on ctf's existing FX layer.
5. **Pass and shot arcs**: a 12-frame arc from passer to receiver on every completed pass (team
   colour), a fading straight streak on a shot, and a white burst on a save or a post.
6. **Seated-shirt rings and shirt numbers**: every cog is drawn as the shipped wheeled rig in its
   team's livery with its **shirt number** on a chip; the eight seated shirts additionally carry a
   bright ring, so a spectator can see at a glance which four cogs a side are being played by a
   policy and which seven are the built-in AI.
7. **Goal celebration**: full-canvas flash, 120 particles in the scoring livery for 45 frames, and a
   `GOAL!` chip in the existing `#bannerlane`.
8. **Instant slow-mo goal replay**: goals are beats, which the chrome receives up front. On first
   reaching a goal tick the transport pauses 0.5 s, seeks back 96 ticks, replays those 4 seconds at
   the slowest `PlaybackSpeeds` step under a "GOAL REPLAY" banner, then seeks forward and restores
   the speed. Built purely from the existing seek/speed commands, once per goal, cancelled by any
   manual scrub.
9. **Possession bar** (`#fb-possbar`): a thin two-colour bar under the scorebug, cumulative
   possession, updated per frame.
10. **Momentum graph**: the starter's `lead` series carrying **goal difference** over the whole
    timeline.
11. **Transport and integrity**: play/pause, step, speeds, scrubber with beat markers, tick readout,
    skip-lulls, spoilers switch, end-card ("RED wins 2–1 · full time"), the end-hold countdown, and
    the `#mmwarn` hash-mismatch line — all the starter's.

### The exact state JSON the viewer reads

Built by `broadcast.nim`'s state builder; the starter's keys are kept so `chrome_common.js` stays
byte-for-byte:

```json
{"t": 1440, "mt": 5760, "ph": "playing", "lob": 0, "pl": true, "sp": 1,
 "mx": 5760, "st": 0, "lp": false, "sk": false, "ff": false, "en": true,
 "mm": -1, "bs": 1.0, "pov": -1,
 "teams": {"red": {"goals": 2, "shots": 11, "sot": 5, "poss": 538,
                   "passes": 51, "tackles": 8,
                   "policies": ["daveey", "grf-football-zonal"]},
           "blue": {"…": "…"}},
 "roster": [{"s": 0, "name": "daveey", "team": "red", "shirt": 10}, "… 8 …"],
 "events": [{"t": 1438, "k": "goal", "team": "red", "by": "RED-9",
             "assist": "RED-10", "speed": 241}],
 "beats": [{"t": 1438, "k": "goal", "team": "red"}, "…"],
 "lead": [0, 0, 1, 1, 2, "…"],
 "lulls": [[600, 720]],
 "half": 1, "turn": 6, "turnTicks": 240, "game": 1, "games": 1,
 "restart": {"kind": "kickoff", "team": "blue", "taker": "BLUE-10", "ticks": 24},
 "ball": {"x": 600, "y": 400, "z": 0, "ctrl": 9},
 "directives": [{"k": "directive", "turn": 6, "seat": 2, "id": "RED-9",
                 "source": "llm", "note": "sitting on their last man",
                 "cogs": [{"id": "RED-9", "intent": "make_run", "say": "in behind"}]}],
 "over": false, "hold": 0}
```

### Art

Real, and mostly already in the repo. Cogs are the shipped **`data/rig_real/red/*`** and
**`data/rig_real/blue/*`** wheeled rigs composed by `rig_art.nim` (body, head, arms, wheels,
per-heading rotation, drop shadow), with a baked shirt-number chip and a seat ring. The pitch is
baked once at startup with pixie (already a dependency, already how ctf bakes its board): mown turf
in two greens with 4 m stripes, painted white lines at 0.12 m stroke (touchlines, goal lines, halfway
line, centre circle, penalty and six-yard boxes, penalty spots, corner arcs), hatched goal nets with
depth, advertising boards around the surround, and a dark vignette. The ball is a baked shaded sphere
with a rolling seam and a separate drop shadow used while airborne. No solid-colour placeholders, no
TODO assets.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked at 360 px, not at
desktop width. The starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`. Kept
verbatim, plus three rules of this coworld's own, in the appended block:

- Cogs are drawn **larger than life**: a 11-map-px disc for a 6.7-map-px body (1.65×), so at 360 px
  (0.30 screen px per map px) a cog is a ~6.6 px disc in its team colour and the ball never renders
  below 5 px across.
- Under `.tiny` the shirt-number chips, the possession bar and the shots figure are hidden; the
  plates read `▮ daveey 2 — 1 daveey-1 ▮` plus the clock, and the seated-shirt rings stay (they are
  the only per-cog information that still reads at that size).
- `.plate-name` gets `flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis`
  so a policy name never collapses to "…".

`tests/test_viewer.nim` asserts the `.tiny` block, the `.plate-name` rule and a CSS rule for every
emitted beat kind are present in `client/replay_broadcast.html`.

---

## Packaging

- **Repo**: `Metta-AI/cogame-grf-football`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `grf-football`.
- **`compose.yaml`** — one service named for the coworld, so the manifest placeholder is
  `{{GRF_FOOTBALL_IMAGE}}`:

  ```yaml
  services:
    grf-football:
      image: coworld-grf-football:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

  (ctf ships two services/two images; this coworld uses the one-image/two-entrypoints shape because
  the shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout (nimby 0.1.26, `nimby use 2.2.4`,
  `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the container's package tree),
  building two binaries: `/bin/grf-football` from `src/grf_football.nim` and
  `/bin/grf-football-player` from `src/grf_football_player.nim`; runtime stage copies both, `data/`,
  `client/`, `*.json`. `CMD ["/bin/grf-football"]`.
- **`Dockerfile.replay-viewer`** — ctf's, with the asset list swapped (rig sheets and lockerroom art
  in, soldier/gun PNGs and `league.html` out) and the `test -f`/`grep -q` assertion block retargeted
  to `grf_replay.wasm` / `grf_replay.data` / `index.html` / `wire_constants.js` / `chrome_common.js`.
- **`coworld_manifest_template.json`**:
  - `game.name` `grf-football`; `game.runnable` =
    `{"type":"game","image":"{{GRF_FOOTBALL_IMAGE}}","run":["/bin/grf-football"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/grf-football/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-grf-football/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.tags` = `["football","soccer","physics","team","gfootball","llm"]`.
  - `game.config_schema` (`additionalProperties: false`, required `["tokens","players"]`):
    `tokens`, `players`, `slots`, `closedRoster`, `seed`, **`num_agents`**, `minPlayers`,
    `maxTicks` (default 5760), `halfTicks` (2880), `maxGames` (1), `turnTicks` (240),
    `turnBudgetMs` (10000), `attempt1Ms` (6000), `retryMs` (3000), `turnSpacingMs` (18000),
    `wallClockBudgetSeconds` (690), `lobbyJoinTimeoutTicks` (1440), `startWaitTicks` (24),
    `gameOverTicks` (360), `mercyGoalDiff` (5), `restartTicks` (36), `stalemateTicks` (480),
    `fastMode` (true), `showPlayerLabels`, `model`, `maxOutputTokens` (900), `sprintSpeed`,
    `baseSpeed`, `shotSpeed`, `shortPassSpeed`, `longPassSpeed`.
  - `game.results_schema`: exactly the keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","team","reason","endRule"]`, per-seat arrays
    `minItems: 8, maxItems: 8`, team arrays `minItems: 2, maxItems: 2`, `reason` enum
    `["complete","deadline","fault"]`, `endRule` enum
    `["full_time","mercy","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both** `player` **and** `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-grf-football/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs`: `readme` = `{"type":"text","value":"<README body inlined>"}` and `pages` = three
    entries — `rules.md` ("Rules", `docs/RULES.md` inlined), `protocol.md` ("Wire protocol",
    `docs/PROTOCOL.md` inlined), `coaching.md` ("Writing a grf-football prompt", `docs/COACHING.md`
    inlined) — each `{"id","title","content":{"type":"text","value":…}}`. **Text form, not URIs**
    (playbook gotcha). `tests/test_manifest.nim` asserts all four values are non-empty.
  - `player[0]` = `{"id":"baseline","name":"GRF Football Zonal Baseline","type":"player",
    "image":"{{GRF_FOOTBALL_IMAGE}}","run":["/bin/grf-football-player"],
    "env":{"PLAYER_SCRIPTED":"zonal"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}`.
  - **Variants — `num_agents` is 8 in both** (it lives inside each variant's `game_config`; a
    variant-level `num_agents` is rejected by `CoworldVariant`):

    | id | name | `num_agents` | `players`/`slots` | `minPlayers` | `maxTicks` | turns | `turnTicks` | `turnSpacingMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|
    | `match` | Match (8 seats, 11 v 11, 4:00) | **8** | 8 | 8 | 5760 | 24 | 240 | 18000 | 690 |
    | `half` | Half (8 seats, 11 v 11, 2:00) | **8** | 8 | 8 | 2880 | 12 | 240 | 18000 | 400 |

    Both seat eight players with
    `slots: [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}]`,
    `fastMode: true`, `maxGames: 1`. `half` exists for cheap ladder rounds; it changes only match
    length, never the seat count.
  - **Certification fixture**: `certification.players` = eight `{"player_id":"baseline"}` entries;
    `certification.game_config` = `{"players":[{"name":"Zonal 1"}, … 8 …],
    "slots":[…the same eight…], "num_agents": 8, "minPlayers": 8, "seed": 679961,
    "maxTicks": 1440, "halfTicks": 720, "maxGames": 1, "turnTicks": 240, "turnBudgetMs": 10000,
    "turnSpacingMs": 0, "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 720,
    "fastMode": true}` — 6 turns, all eight seats scripted, no LLM, a handful of wall-clock seconds.
- **Scaffold from `coworld-builder/templates/`** with `<slug>` = `grf-football`,
  `<IMAGE>` = `coworld-grf-football`, `<SEATS>` = **8**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (**verbatim, no
  substitutions**), `tools/ci/policies.json`, and ctf's `tools/build_replay_viewer.sh`
  (**`chmod +x`**). Three additions to the template `ci.yml`:
  - `docker-smoke` gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format);
  - `wasm-viewer` gets a final step
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer tests/fixtures/grf-679961.replay 300`
    — the native ↔ wasm determinism gate;
  - the `test` job's `NIM_TESTS_RELEASE_ONLY` repo variable lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": ["/bin/grf-football-player"]`, one image,
  env-switched):

  | name | env | role |
  |---|---|---|
  | `grf-football-tiki` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `grf-football-counter` | `PLAYER_PROMPT` = champion #2 prompt | champion #2, owner daveey-1 |
  | `grf-football-zonal` | `PLAYER_SCRIPTED=zonal` | filler |
  | `grf-football-gegenpress` | `PLAYER_SCRIPTED=gegenpress` | filler |

- **Repo layout**: `src/grf_football.nim`, `src/grf_football_player.nim`,
  `src/grf_football/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, pitch.nim, control.nim,
  builtin_ai.nim, directives.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim,
  replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, rig_art.nim,
  wire_constants.nim, server.nim}`, `replay-viewer/{grf_football_replay.nim, config.nims,
  static_replay.js, static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, COACHING.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `grf_football.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only harness;
the sandbox has no Nim, Docker or emsdk. Tests 2 and 10 are the determinism gate: if either fails,
the physics or a build flag changed — fix the code, never the test.

1. **`tests/test_physics.nim`** — sim unit tests. A ball fired at `BallMaxSpeed` at a post for 600
   ticks never leaves the board (no tunnelling); the goal test fires on the exact plane crossing and
   not a tick early or late; a ball crossing a touchline yields a throw-in to the other team at the
   crossing point; attacker-last-touch over the goal line is a goal kick and defender-last-touch a
   corner; a keeper catch inside the area at ≤ 18 m/s is a catch and at 25 m/s a parry; cog–cog
   resolution is symmetric under index swap and conserves momentum exactly; a short pass reaches the
   named teammate within the modelled time; a slide that reaches the ball first is a tackle and one
   that reaches the opponent first is a foul with 48 grounded ticks; stamina drains and caps speed at
   the stated thresholds; the stalemate drop fires at exactly 480 ticks.
2. **`tests/test_determinism.nim`** — two native runs from the same seed and the same recorded action
   bytes produce identical `gameHash` chains; re-simulating a recorded replay reproduces every tick
   hash; no `float` symbol is reachable from `sim`/`pitch`/`control`/`builtin_ai` (source grep);
   `SinQ12` matches `math.sin` entry for entry; `isqrt` matches an exhaustive small table and perfect
   squares to 2⁴⁰.
3. **`tests/test_actions.nim`** — the 19-action encoding round-trips: every legal byte decodes to
   exactly one gfootball action and back; illegal direction nibbles `9..15` decode as `0`; a
   pass/shot code from a cog with no ball is a no-op; sprint and dribble are sticky and always in a
   defined state.
4. **`tests/test_control.nim`** — **the bounded-orders/legality assertion on the scripted baselines.**
   Over a 1440-tick scripted match, for every tick and every cog: the emitted byte is a legal
   encoding, both baselines emit exactly one order per turn for their own shirt and no other, every
   field is inside its enum/clamp, `note` ≤ 160 runes and `say` ≤ 48 runes, `pass_to` is always a
   teammate or null, and no order names a cog the seat does not command. Also: `zonal` beats
   `gegenpress` over the head-to-head fixture (the ladder needs a spread).
5. **`tests/test_directives.nim`** — tolerant parsing and repair: fenced JSON, prose-wrapped JSON, a
   bare `cogs` object, numeric strings in `target`, an unknown intent (→ `support`), an out-of-range
   target (clamped), a `pass_to` naming an opponent (→ null), an extra entry (dropped), a missing
   entry (last turn's, else `zonal`'s). **Rune truncation**: a `note` whose 160th rune is a 4-byte
   emoji truncates on the rune boundary and the result is valid UTF-8.
6. **`tests/test_scoring.nim`** — the formula and its sign at 0–0, 1–0, 2–0, 3–0, 5–0 (mercy), 0–2;
   the eight scores always sum to 4.000 and the two team scores to 1.000; `win` follows goal
   difference; `fault` gives 0.500 × 8 with `win` all false; every `results.reason`/`endRule` pair in
   §End conditions is reachable and no other pair is emitted.
7. **`tests/test_identity_privacy.nim`** — **two name spaces.** No real policy name appears in any
   seat view, any prompt, any board label, any `say`, or any replay record other than the config
   JSON, `roster[].name`, `teams.*.policies` and `results.names`; every in-game id matches
   `^(RED|BLUE)-([1-9]|1[01])$`.
8. **`tests/test_engine.nim`** — the decision loop: all seats' calls go out in **one** batch per turn
   (a stub transport asserts one `makeRequests` call with 8 entries); a timeout retries exactly once
   then falls back to `zonal` with a `fallback` record naming the cause; a seat with no credentials
   records `no_credentials` and never blocks; the budget guard fires when two turns no longer fit and
   the match finishes `complete/full_time`; a per-turn wall clock never exceeds `turnBudgetMs`.
9. **`tests/test_replay.nim`** — **end-to-end episode writing a replay**: a full scripted episode
   through the server writes results + a replay, the replay re-simulates to an identical hash chain,
   every `directive` record is ≤ 900 runes, and the `result` record equals `playerResultsJson()`.
10. **`tests/test_replay_utf8.nim`** — **strict-UTF-8 replay parse**: `tools/replay_summary.py` run
    over the episode's bytes emits a document that `json.loads(..., strict=True)` accepts and whose
    `protocol` is `grf-football/v1`; every recorded string decodes as UTF-8 with `errors="strict"`,
    including one seeded with a 4-byte emoji at a cap boundary.
11. **`tests/test_broadcast_state.nim`** — the state JSON carries every key §Viewer lists, `teams` is
    keyed `red`/`blue`, `beats` contains only kinds with CSS, and a seek hydrates the scorebug and
    end-card with no events.
12. **`tests/test_viewer.nim`** — the chrome contract: `client/chrome_common.js` is byte-identical to
    the starter's (sha256 pinned in the test), `client/replay_broadcast.html` contains no `#fpv`/
    `#viewpanel` id and still contains every kept id, the appended block's ids are all `fb-`-prefixed,
    a CSS rule exists for every emitted beat kind, and the `.tiny` and `.plate-name` rules are present.
13. **`tests/test_manifest.nim`** — `num_agents == 8` in **every** variant's `game_config` and in
    `certification.game_config`; no variant-level `num_agents`; `replay_viewer.bundle ==
    "static-replay-viewer"`; `protocols.player` and `protocols.global` both present;
    `docs.readme` and all three `docs.pages` non-empty; `results_schema` keys equal
    `playerResultsJson()`'s keys exactly.
14. **`tests/test_perf.nim`** (release-only) — 5760 ticks of physics plus serve inside 120 s.

**CI jobs** (template `ci.yml`): `test` (the above, debug + release) → `docker-smoke` (builds the
image, runs one real episode in raw docker with the certification fixture's eight seats via
`tools/ci/docker_smoke.sh`, uploads the replay as `smoke-replay`) → **`wasm-viewer`**, which builds
the bundle with `tools/build_replay_viewer.sh`, asserts `index.html` and a non-empty `.wasm` exist,
and then **executes** it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
dist/smoke/*.replay --timeout 90 --strict-text-bounds`, waiting on `data-replay-loaded="true"` — the
bundle is run against the replay `docker-smoke` just produced, not merely compiled — followed by the
`wasm_replay_smoke.cjs` determinism gate.

---

## Out of scope (v1)

- **The academy drills.** Empty goal, run-to-score, 3v1 with keeper, pass-and-shoot, corner and
  counterattack are the obvious v2: each is a `scenario` config value that swaps the kickoff reset and
  the end condition, reusing this sim unchanged. v1 ships exactly one match format so there is one
  thing to certify, one thing to rank and one thing to watch.
- **Checkpoint / any individual reward shaping.** The idea's "optional checkpoint shaping" is off:
  the score is team goal difference only. Per-seat statistics are reported but never scored.
- **Offside, cards, penalties, advantage, injury time, substitutions, and a referee that is anything
  more than the restart table above.**
- **Ends swapped at half-time** and any camera that is not the fixed whole-pitch view.
- **Seats commanding more than one shirt**, and seat counts other than 8. A "coach" variant that
  seats one policy per whole team is a plausible v2 but would be a different game and a different
  `num_agents`.
- **Any 3D or broadcast-camera rendering.** The idea's "gfootball renders 3D already; use it" cannot
  apply: the gfootball renderer is not hostable here and the replay must be a static wasm bundle.
  The 2D top-down broadcast view is the shipped plan.
- **Raw per-tick action control by an external policy** (the idea's "per-tick discrete action"
  interface). v1's policies are prompts and scripted baselines that speak the directive schema; the
  action bytes are produced server-side. A per-tick socket policy is a v2 protocol addition and would
  need its own latency budget.
- **`cogball` changes.** The two coexist unchanged; nothing here modifies or deprecates it.
