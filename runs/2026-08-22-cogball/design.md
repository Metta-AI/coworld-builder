# cogball — design note v2 (2026-08-22, paintbot lineage)

`Metta-AI/cogame-cogball` is 3v3 robot soccer in a continuous 2D physics world, forked from
**`Metta-AI/coworld-ctf`** (paintbot), mounted read-only at `/workspace/starters/coworld-ctf`.
**Every convention there holds here unless this note says otherwise.** This is round 2, an
operator-directed redo: round 1 designed and built cogball on `cogame-moba`, and the operator
(daveey) overruled it on the run task — "use coworld-ctf (paintbot) as the starter for Cogball,
NOT cogame-moba. Paintbot is the real-time/RL-vector lineage (game loop, per-tick replays, wasm
static viewer, broadcast chrome); moba is only for bit-exact ports of an EXISTING external env,
which Cogball is not. … the physics sim replaces ctf arena rules while the viewer chrome/replay/CI
wiring is kept verbatim." `playbooks/make-coworld.md` §Phase 0 now pins the same rule ("New physics
games (Cogball, Lantern, Tandem) take paintbot, not moba — operator ruling 2026-08-22"), and
`prompts/10-design.md`'s starter table puts "any real-time game loop (grid OR continuous physics,
new rules written for this coworld)" in the paintbot row. Cogball's game shape — a 24 Hz tick loop,
a per-tick recorded action log, a wasm re-simulating spectator viewer and a broadcast HUD — is that
row exactly. Round 1's note (`runs/2026-08-22-cogball/design.md`) survives as a source of already
settled **game** decisions (pitch geometry, kick model, scoring formula, end conditions, directive
schema, champion prompts, baseline algorithms, watchability plan); every place this note changes one
of them, it says so and why.

**Source idea, verbatim** (Asana idea task 1217704774927793, "03 Cogball — 3v3 soccer in a real
physics engine"):

> Box2D compiled to wasm: circular bodies with torque/thrust control, a ball with restitution,
> walls, goals. Seats are either one player or a full trio. Passing, positioning and role
> emergence are the whole game; nothing is gridded. Replays re-simulate from seed + action log
> like NMMO/Moba.
>
> Seats: 6 or 2
> Motive: team zero-sum
> Policy interface: RL continuous vector
> Fills gap: continuous physics / team sport
> Integrity (anti-collusion): Trio seat is one policy, so intra-team codebooks are legitimate
> coordination; the hero-per-seat variant seats cross-author and reports cross-play.
>
> Replay plan (watchability): Broadcast soccer: ball trails, kick impact FX, goal fireworks and an
> instant slow-mo goal replay; score bug in the corner. Position-history tinting shows roles
> emerging — who became the keeper, who the striker — without any labels.
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied

| Pin | How cogball satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a real-time game loop with new rules and RL-vector policies. Operator-directed; the physics sim replaces the arena rules, the loop/protocol/replay/viewer/CI stay. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-cogball`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=formation` / `PLAYER_SCRIPTED=swarm` (both fillers); one image `coworld-cogball`, entrypoint `/bin/cogball-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` kept from ctf; the **same Nim sim module** compiles into `replay-viewer/cogball_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/replay_broadcast.html` chrome and `client/broadcast_core.js` kept; robots are the shipped `data/rig_real/blue` and `data/rig_real/red` wheeled rigs; pitch/ball baked with pixie. No placeholders. (§Viewer) |
| Two name spaces | Prompts and board labels carry only `Azure` / `Crimson` and robot ids `AZ-1..3` / `CR-1..3`; real policy names appear only in the replay config JSON, the DOM scorebug/roster and `results.names`. Test-enforced. (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | 415 s expected / 680 s absolute worst case against a 720 s budget; a 690 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 2** in variant `default`, variant `sprint`, and `certification.game_config`; `<SEATS>` = 2 in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Cogball is 3v3 robot soccer on a walled indoor pitch in a continuous 2D physics world.** Two
teams of three wheeled robots chase one ball and try to put it through the opponent's goal mouth.
Nothing is gridded: positions and velocities are continuous fixed-point quantities; the only
discrete things in the world are the tick, the actuator bits and the kick.

### Seats

**`num_agents` = 2. One seat = one full trio.** Seat 0 is **Azure** (robots `AZ-1`, `AZ-2`, `AZ-3`),
defends the goal at view-x = −20 m and attacks +x. Seat 1 is **Crimson** (`CR-1`, `CR-2`, `CR-3`),
defends +20 m and attacks −x. The idea offered "6 or 2"; 2 is chosen because (a) the motive is team
zero-sum and with two seats the scores sum to exactly 1.0 with no teammate-attribution problem,
(b) both champions must be LLM prompt policies and a 2-seat game puts them head to head in every
episode rather than scattering champions and fillers across one team, (c) the idea's own integrity
note prefers the trio seat ("intra-team codebooks are legitimate coordination"), and (d) two seats
means **two** parallel LLM calls per decision turn instead of six, which is what makes the 720 s
budget comfortable. ctf's seat topology does not force otherwise: ctf already ships a 2-seat variant
(`ctf-1v1`, `num_agents: 2`), and cogball's split of 2 *connections* over 6 *robots* is handled by
the two small, named edits to `replays.nim`/`roster.nim` in §Sim module. Aliases changed from round
1's "Azure/Magenta" to **Azure/Crimson** so the two liveries are exactly the blue and red rigs the
starter already ships as real art — no recolouring work, no placeholder.

### World, units, and why they are integers

The whole sim runs in **integers**. Positions are **micrometres (µm)** and velocities are **µm per
tick**, both `int32`; angles are **brads** (256 per turn, 0 = east, counter-clockwise on screen —
ctf's convention, `sim_types.nim` `aimVector`) held at 1/16-brad resolution. This is not a stylistic
choice: it is *ctf's own determinism discipline* ("integer permille keeps every in-sim derivation
integer-only, so native and wasm agree", `sim_types.nim`; "snapped to map pixels at placement, so
every later coverage test is integer-only and native/wasm agree"). Replays here are re-simulated by
the **emscripten/wasm32** build of the same Nim module that the **native amd64** server ran, and
their per-tick `gameHash` chain must match exactly. Integers make that true by construction rather
than by an argument about libm. §Sim module states the arithmetic rules and the CI gate.

This **replaces round 1's** "IEEE double physics using only `+ − × ÷ √`" rule. The round-1 reasoning
(libm is the risk, not arithmetic) was right about the risk and wrong about the cheapest cure in
this lineage: paintbot already proves out integer state across the native/wasm boundary, and its
`wasm_replay_smoke.cjs` job already exists to catch the wasm32-only failure mode.

Layout (world coordinates, µm, origin top-left, y down — ctf's screen convention):

| Thing | Value |
|---|---|
| World box | x ∈ [0, 44 000 000], y ∈ [0, 25 000 000] (44 m × 25 m) |
| Map render scale | 1 map pixel = 40 000 µm → `MapWidth = 1100`, `MapHeight = 625` |
| Pitch interior (playing surface) | x ∈ [2 000 000, 42 000 000], y ∈ [0, 25 000 000] (40 m × 25 m) |
| Goal mouths | plane x = 2 000 000 (Azure's) and x = 42 000 000 (Crimson's), y ∈ [9 000 000, 16 000 000] (7 m) |
| Goal boxes | x ∈ [0, 2 000 000] and [42 000 000, 44 000 000], y ∈ [9 000 000, 16 000 000], closed by walls at x = 0 / 44 000 000 and y = 9 000 000 / 16 000 000 |
| Walls | the two touchlines y = 0 and y = 25 000 000, and the goal-line segments x = 2 000 000 / 42 000 000 outside the mouth |
| Goalposts | static circles, radius 120 000 µm, at (2 000 000 ‖ 42 000 000) × (9 000 000 ‖ 16 000 000) |
| Penalty areas | Azure's: x ≤ 8 000 000 and \|y − 12 500 000\| ≤ 7 000 000; Crimson's mirrored (x ≥ 36 000 000). Used only for save attribution — no special powers. |
| Centre spot / circle | (22 000 000, 12 500 000), r = 3 000 000 |
| Neutral drop spots | (11 000 000 ‖ 33 000 000) × (6 500 000 ‖ 18 500 000) |

**There is no out of play** — no throw-ins, no corners, no offside. The pitch is fully walled.

**View coordinates** (the only coordinates a policy ever sees or sends): metres, origin at the
centre spot, `X = (x_µm − 22 000 000) / 1 000 000`, `Y = (y_µm − 12 500 000) / 1 000 000`. So the
pitch is X ∈ [−20, +20], Y ∈ [−12.5, +12.5] and the goal mouths are |Y| ≤ 3.5 — round 1's geometry
exactly, now as a presentation transform over ctf's screen-space sim.

### Bodies

Six robots: radius 550 000 µm, mass 6000 g, each with position, velocity, `headingQ` (int32,
0..4095 = 1/16 brad; `headingBrads = headingQ div 16`), `spin` (int32, 1/16 brad **per tick**), and
`kickCooldown`. One ball: radius 350 000 µm, mass 450 g, position and velocity only (no spin, no
Magnus). Robots are car-like: thrust acts along the heading and lateral velocity is scrubbed off by
grip, so *facing the right way is part of the skill*.

### Time

`TargetFps = ReplayFps = 24` — **kept verbatim from ctf**, because every speed-coupled layer
(`PlaybackSpeeds`, the lull scan, the momentum series, `tickTime`, the transport bar) is keyed to
it. Round 1's 30 Hz is dropped for that reason. Each tick integrates **4 substeps** of 1/96 s, so a
25 m/s ball moves at most 0.26 m per substep (< its 0.70 m diameter) and cannot tunnel.

A match is **`maxTicks = 4800` ticks = 200 s = 3:20 of soccer**, divided into **40 decision turns of
`turnTicks = 120` ticks (5.0 s)**. Round 1's 7200-tick/4:00 match is shortened: on this lineage the
game loop can be wall-clock paced (ctf's `runFrameLimiter`), so match length is charged against the
same 720 s budget as the LLM turns — see the arithmetic in §Decisions.

### Actuators — the 8-bit input mask, kept verbatim

A robot's action for one tick is exactly one **Sprite v1 player-input bitmask** (`bitworld`'s
`ButtonUp`/`ButtonDown`/`ButtonLeft`/`ButtonRight`/`ButtonSelect`/`ButtonA`/`ButtonB`/`ButtonC`, the
same `uint8` ctf records with `writeInputMaskChange`). This is the single most load-bearing "kept"
decision in the note: the mask is what `sim.step(inputs, prevInputs)` consumes, what
`replayWriter.writeInput` records, and what the wasm viewer replays — so ctf's whole replay
pipeline works unmodified on a physics game.

| Button | cogball meaning |
|---|---|
| `ButtonUp` | thrust forward (`u_thrust = +1`) |
| `ButtonDown` | thrust reverse (`u_thrust = −1`) |
| `ButtonLeft` | torque counter-clockwise (`u_turn = +1`) |
| `ButtonRight` | torque clockwise (`u_turn = −1`) |
| `ButtonSelect` | brake (grip ×3 this tick, and `u_thrust` is forced to 0) |
| `ButtonA` | kick |
| `ButtonB`, `ButtonC` | reserved, must be 0 (rejected → treated as 0) |

Up+Down together ⇒ `u_thrust = 0`; Left+Right together ⇒ `u_turn = 0`. The idea's "RL continuous
vector" becomes **continuous observation, discrete actuators** — the honest model of a wheeled RC
robot, and the one that keeps the action log 6 bytes wide. Raw per-robot Sprite v1 control by an
external policy is a 1:1 fit only for the 6-seat hero variant and goes to §Out of scope (v1).

### Resolution order (exact, every tick `t`, no exceptions)

1. **Turn boundary.** If `t mod 120 == 0` and `phase == Playing`: the directive collected for turn
   `t div 120` becomes each seat's active directive (§Server). The server writes one **directive
   record** per seat into the replay's chat stream. Directives are stored in
   `sim.activeDirective[seat]`, which is **excluded from `gameHash`** (ctf's rule for
   `damagePops`/`skin`/`puddleTicks`) — nothing a coach says can move the hash chain.
2. **Kickoff freeze.** If `t < freezeUntil`: every robot's mask is forced to 0, every velocity and
   `spin` is set to 0, and steps 5 and 6 are skipped. Steps 3, 4, 7, 8, 9 and 10 still run (the
   zero masks are recorded, the hash is written, the turn boundary still fires). Physics resumes at
   `t == freezeUntil`.
3. **Control compile.** For each robot in index order `AZ-1, AZ-2, AZ-3, CR-1, CR-2, CR-3`, the
   deterministic control layer (§Decisions) reads the current sim state plus that seat's active
   directive and emits one `uint8` input mask.
4. **Record.** The six masks go to `sim.step(inputs, prevInputs)` and to
   `replayWriter.writeInputFrameMasks` (ctf's function, unchanged). **This is the determinism
   boundary.** The control layer is *outside* it: the viewer never runs the control layer, it feeds
   the recorded masks to the identical physics core.
5. **Kicks.** In robot index order, for each robot with `ButtonA` set, `kickCooldown == 0`,
   `dist(ball, robot) ≤ 550 000 + 350 000 + 450 000 = 1 350 000` µm, and the ball inside a ±60°
   frontal arc (integer test: `2·(dx·hx + dy·hy) ≥ d·4096`, where `(hx, hy)` is the Q12 heading unit
   vector and `d = isqrt(dx² + dy²)`):
   - `n = (hx, hy)` (Q12); `vpar = (vbx·nx + vby·ny) div 4096`; `vperp = vball − (vpar·n) div 4096`;
   - `vpar' = max(vpar, 0) + KickImpulse`, `KickImpulse = 375 000` µm/tick (= 9.0 m/s);
   - `vball = vperp div 2 + (vpar'·n) div 4096`, then clamped to `BallMaxSpeed`;
   - reaction: `vrobot -= (n · ((450 · (vpar' − vpar)) div 6000)) div 4096`;
   - `kickCooldown = 12` ticks (0.5 s); emit a `kick` event.
   Each kick sees the ball state left by the previous kick in the same tick.
6. **Four substeps** (`hs = 1/4 tick`), each substep in this exact order:
   1. **Robot integration**, index order:
      `spin = clamp(spin + 6·u_turn − (spin·64) div 1024, −96, +96)`;
      `headingQ = (headingQ + spin div 4 + 4096) mod 4096`;
      thrust `v += (7800·u_thrust · n) div 4096`;
      lateral grip: `vlat = v − ((v·n) div 4096)·n div 4096`; `v -= (vlat · (Select ? 255 : 85)) div 1024`;
      linear drag: `v -= (v·13) div 1024`;
      speed cap: if `|v| > RobotMaxSpeed = 291 600` then `v = (v · RobotMaxSpeed) div |v|`;
      `pos += v div 4`.
   2. **Ball integration**: `vball -= (vball·6) div 1024`; cap to `BallMaxSpeed = 1 041 600`;
      `ballPos += vball div 4`.
   3. **Robot–wall**: for each robot in index order, clamp the centre inside the arena polygon and
      reflect the normal velocity component with restitution 25 %.
   4. **Robot–robot**: for each unordered pair in ascending index order `(0,1),(0,2),…,(4,5)`, if
      the centres are closer than 1 100 000 µm, separate each by half the penetration along the
      normal and apply an equal-and-opposite normal impulse with restitution 35 % (equal masses).
   5. **Robot–ball**: for each robot in index order, if the centres are closer than 900 000 µm,
      separate along the normal in inverse-mass proportion (6000 g vs 450 g) and apply a normal
      impulse with restitution 55 %; multiply the ball's tangential relative velocity by 80 %
      (dribble friction). Record `lastTouchRobot`, `lastTouchSeat`, `lastTouchTick`.
   6. **Ball–post**: circle-circle against each of the four static posts, restitution 70 %; emit
      `post` on contact.
   7. **Ball–wall**: reflect with restitution 80 %, tangential factor 98 %.
   8. **Goal test**: a goal is scored the moment the ball **centre** satisfies
      `ballx ≤ 2 000 000 and 9 000 000 ≤ bally ≤ 16 000 000` (Crimson scores) or
      `ballx ≥ 42 000 000` with the same y band (Azure scores). On a goal: abandon the remaining
      substeps of this tick, increment the scorer's goal count, emit `goal` (with `scorer` =
      `lastTouchRobot`, `assist` = the previous distinct same-seat toucher within 96 ticks or
      `null`, `ballSpeed`, `scoreAfter`), perform the **kickoff reset**, and set
      `freezeUntil = t + 25`.
7. **Cooldowns.** Every robot with `kickCooldown > 0` decrements it by 1.
8. **Stats and stalemate counter.** `possessionTicks[lastTouchSeat] += 1` (nothing before the first
   touch); `distanceMm[robot] += |Δpos|`; shot/save/pass bookkeeping (below); and the stalemate
   counter: if the ball centre is still inside the 1 500 000 µm box anchored where the counter last
   reset, `stalemateTicks += 1`, else the box re-anchors and the counter resets. At
   `stalemateTicks == 240` (10 s) perform a **neutral drop** (below).
9. **Hash.** `replayWriter.writeHash(uint32(tick), sim.gameHash())` — ctf's per-tick hash chain,
   unchanged. `gameHash` mixes tick, phase, winner, score, and every robot's and the ball's
   position/velocity/heading/spin/cooldown. It never mixes directives, notes, FX, or trails.
10. **Turn end.** If `(t + 1) mod 120 == 0`: emit `turn_end`; if `|goals[0] − goals[1]| ≥ 5`, end
    the match (`mercy`); if `t + 1 ≥ maxTicks`, end the match (`full_time`).

**Kickoff reset (exact).** Ball at the centre spot with zero velocity. All spins, velocities and
cooldowns 0. Azure headings brad 0 (east), Crimson headings brad 128 (west). The **restarting**
seat (the conceding one; at match start, seat `config.seed and 1`) places its first robot 1.5 m from
the ball on its own side and the other seat's first robot 3.0 m away on the far side; the remaining
robots go to ±9.0 m on their own side at y = 12.5 m ± 4.5 m. Each of the four flank robots gets a
deterministic y jitter of `sim.rng.rand(500_000) − 250_000` µm drawn from ctf's existing seeded sim
RNG (`std/random` `Rand`, integer draws only — the same stream ctf uses for respawn placement).
Emit `kickoff` with `restartForSeat`.

**Neutral drop (the corner-stalemate cure, in the sim).** Round 1's build learned this the hard way:
with a fully walled pitch the corners are an absorbing state — a robot (radius 0.55 m) can never get
corner-side of the ball (radius 0.35 m), and every push drives it deeper; **6 of 20 scripted matches
ended 0–0 stuck in a corner** until a boards-escape rule was bolted onto the control layer. This
note keeps that control-layer rule (§Decisions) **and** adds a sim-level guarantee, because a
control-layer rule can be defeated by a policy while a sim rule cannot: when `stalemateTicks`
reaches 240, the ball teleports to the nearest of the four neutral drop spots with zero velocity,
every robot within 3 000 000 µm of that spot is pushed radially out to exactly 3 000 000 µm with
zero velocity, `stalemateTicks` resets, and a `drop` event is emitted. The drop is inside
`gameHash`, so it is part of the recorded, re-simulated truth. Goal-mouth exemption is not needed
here (the drop spots are never in front of a goal).

### Shots, saves, passes

A kick whose post-kick ball velocity ray reaches the opponent goal plane inside the mouth
(`t* = (xGoal − ballx) / vbx > 0` and the crossing y inside [9 m, 16 m], computed in `int64`) is a
**shot on target** (`shot`, `onTarget: true`); other kicks toward the opponent half whose crossing y
is within 4.5 m of the mouth are shots off target. A shot on target whose next ball touch is by a
defending robot inside its own penalty area, before any goal, is a **save**. A kick made under
intent `pass` whose next touch is a different robot of the same seat within 96 ticks is a
**completed pass**; if the next touch is an opponent it is an **interception**.

### Scoring, sign, and what the league ranks by

Team zero-sum, margin-sensitive, and the two seats' scores always sum to exactly 1.0:

```
gd(seat)    = goals[seat] − goals[1 − seat]
score(seat) = 0.5 + 0.5 · clamp(gd(seat) / 3, −1, +1)
```

**Higher is better.** 3–0 or better = 1.000; 2–0 = 0.833; 1–0 = 0.667; any draw = 0.500; 0–1 =
0.333; 0–3 or worse = 0.000. `score(0) + score(1) == 1.0` for every legal outcome.
`win[seat] = gd(seat) > 0`. **The league ranks by Elo computed from `results.scores`** (the
platform's `scores` array is the only cross-game ranking input; Elo 1000 start, K 32, per the phase
50 league settings). A `fault` episode scores 0.5 / 0.5 — an infra fault is nobody's loss. This
replaces ctf's sparse ±1 `ClassicScoring`; the reason is that a 3v3 soccer ladder needs a
margin-sensitive signal to separate two prompts that both win sometimes, and the formula is already
zero-sum so nothing about Elo changes.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `full_time` | `maxTicks` played. The normal ending. |
| `complete` | `mercy` | Goal difference ≥ 5 at a turn boundary. The rules ended the match; still a complete game. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **690**) elapsed before full time. The score at that instant stands and is scored with the same formula, the replay is complete up to the stop tick, and the game-over frame is written. **This is declared acceptable for phase-60 verification** (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. |
| `fault` | `sim_fault` | A physics invariant guard tripped (a non-finite/oversized state, an out-of-arena body). Scores 0.5 / 0.5, `win` both false, partial replay written. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2400 = 100 s)
expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's `declarePlayerFailure`
(lowest missing slot only), its trio is driven by the `formation` baseline for the whole match, and
the match plays to `full_time`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {formation, swarm}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=formation`. A scripted policy seated as a champion is a failure state.

### Where the decision happens, and the LLM client

**coworld-ctf has no LLM client in the episode server** (its "campaign strategist" is a platform-side
feature that ships with the `coworld` package in Metta-AI/metta, not in this repo — README §Campaign
mode). So cogball **ports the credential ladder and transport from
`/workspace/starters/cogame-babel/src/babel/llm.nim` into the ctf-lineage server** as
`src/cogball/llm.nim`. Ported verbatim in behaviour:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (read with `readCogameUri`) → **none** (client
  `disabled = true`, every turn falls back instantly with no network wait, so offline certification
  completes in seconds).
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, `us.anthropic.claude-sonnet-4-6`,
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; `tryNextBedrockModel` on 401/403 "Model access is
  denied" and on 429.
- `max_tokens = 900` (400 truncates — playbook gotcha). **No `output_config.effort`** when the model
  string contains `haiku` or `4-5` (Haiku 4.5 400s on it). Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`. **No `temperature`** — babel's body shape is copied as
  is; round 1's `temperature: 0.4` is dropped rather than add an untested field to a Bedrock body.
- `extractJsonObject` (first `{` … last `}`, fence-tolerant) and `cleanNotes`' **rune-boundary**
  truncation (`runeLen`/`runeSubStr`) are ported unchanged.

The decision happens in the **game server**, not the player container, exactly as in the
parley/babel lineage: the `anthropic_api_key` coworld secret and the Bedrock sidecar credential are
injected into the *game* pod (`game.runnable.env.ANTHROPIC_API_KEY_URI =
secret://coworld/cogball/anthropic_api_key`); phase 60 greps the *game* log for `falling back` /
`LLM provider is unavailable`; `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container
only; and keeping the control layer server-side is what makes the recorded action log reproducible
with no network in the loop.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **120 ticks (5.0 s of sim time)**, **40 turns** per match. At each turn the
server builds both seats' request bodies and issues them as **one parallel batch**:
`client.curl.makeRequests(@[req0, req1], timeout)` — curly's batch API, the shape the playbook names
for Nim ("issue all seats' LLM calls as one parallel batch per turn (`curly.makeRequests` in
Nim)"). Seats are **never** queried sequentially. One call per seat per turn covers all three of
that seat's robots, so a whole episode is 2 × 40 = **80 calls**, at most 2 in flight.

Per-turn timing: attempt 1 batch deadline **6.0 s**. Any seat that timed out, errored, returned
non-JSON, or returned no usable robot entry is retried **once**, again as a single batch, with a
**2.5 s** deadline. Worst case 8.5 s ≤ the **9.0 s** `turnBudgetMs = 9000` cap enforced by a
monotonic deadline around the whole turn.

```
40 turns × 9.0 s per-turn budget                            = 360 s
lobby / connect wait (typical 15 s; cap lobbyJoinTimeoutTicks 2400 = 100 s)
                                                     typical =  15 s
4800 ticks of play — fastMode, players report ready         =  20 s
                     (wall-clock-paced fallback worst case  = 200 s)
game-over hold + results + replay write (retrying uploader) =  20 s
                                                            -------
expected total                                              = 415 s   < 720 s
absolute worst case (100 + 360 + 200 + 20)                  = 680 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                     = 690 s   → reason "deadline"
platform kill (episodeTimeoutSeconds)                       = 1200 s
```

`fastMode: true` in every variant. ctf's `docs/PROTOCOL.md` warns that sending the Sprite v1 Ready
packet (`0x85`) corrupts input timing on a wall-clock-paced server — that warning is about *player*
clients whose own inputs are dead-reckoned. Cogball's seats send no inputs at all (the server
computes every mask), so the hazard does not exist here and the player harness sends `0x85` every
frame. The wall-clock-paced number above is the fallback if a player container dies mid-match.

**Budget guard (early settle without shortening the match).** At the start of each turn, if
`elapsed + 2 × turnBudget > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn and the match finishes on the scripted layer (microseconds per turn), so the episode ends
`complete/full_time` rather than `deadline`. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the outer per-turn
deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's own socket timeouts on the serve
thread (which runs independently of the game loop, so a 9 s LLM stall cannot drop a connection), the
690 s engine stop, and ctf's `gameOverTicks` hold before exit. On two consecutive LLM failures the
seat's directive for that turn is the **`formation`** scripted directive and a `fallback` record is
written with `cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. A seat
that disconnects mid-match keeps playing: its directive source degrades to `formation` and it
revives on reconnect. **No failure mode leaves a robot unactuated** — the control layer always has a
directive, defaulting to the previous turn's, then to `formation`.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You are the coach of a three-robot soccer team in a continuous 2D physics world.
Every 5 seconds of match time you issue ONE directive for all three of your robots.
A deterministic controller executes it for the next 5 seconds: it steers each robot
toward its target, turns it to face where it is going, and kicks when the ball is in
range and the intent allows it. You do not control motors directly.
The pitch is 40 by 25 metres and FULLY WALLED - there is no out of play, no corners,
no throw-ins and no offside. The controller will not let a robot bury the ball on the
boards: near a wall it aims its kick back toward the middle.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars","robots":[
  {"id":"<one of your three robot ids>",
   "role":"keeper|back|wing|striker",
   "intent":"chase|intercept|hold|shoot|pass|clear|press",
   "target":[x,y],            // metres, x in [-20,20], y in [-12.5,12.5]
   "pass_to":"<teammate id or null>",
   "kick":"auto|never",
   "say":"<=48 chars"} , ... exactly three, one per robot ]}
Intents: chase = drive at the ball; intercept = drive to where the ball will be;
hold = hold the target point and face the ball; shoot = line up behind the ball and
strike it at their goal; pass = same but aimed at pass_to; clear = hammer it away
from your own goal; press = shadow the nearest opponent. target is used directly by
hold and as a bias by the others. kick:"never" makes the robot shepherd the ball
instead of striking it.
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(babel's `operatorBlock`, ported), then a blank line, then the seat's view JSON (§Server). The
prompt text is never echoed into the replay — only `policyKind` and the resulting directive are.

### Champion #1 — `cogball-total` (owner daveey), `PLAYER_PROMPT`

```
Play total football: never leave your own goal empty and never leave the ball
unpressured. Every turn, assign exactly one robot as keeper with role "keeper" and
intent "hold" at a target on the arc 3 metres in front of your own goal, y matched to
about a third of the ball's y so it covers the near post. Send the robot closest to
the ball with intent "chase" or "shoot" - "shoot" whenever it is within 6 metres of
the ball and the ball is in their half. The third robot plays support: intent
"intercept" with a target roughly 8 metres up-field of the ball on the opposite
y-side, so it is already there when the ball squirts loose. Rotate the roles when the
distances say so - the nearest robot always attacks, the deepest always keeps. Prefer
"pass" to your support robot over a low-percentage shot from outside 12 metres. If the
ball is sitting on a touchline, send exactly one robot at it and keep the others in
open space to collect the clearance. If you are two goals up, drop the support robot
to "back" and hold the middle.
```

### Champion #2 — `cogball-counter` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Play the counter: sit deep, win the ball, then hit them fast in the space they left.
Default shape is two robots behind the ball line - one "keeper" holding the goal arc,
one "back" holding a target halfway between the ball and your own goal, both with
intent "hold" so they stay compact and do not chase. The third robot presses: intent
"press" on whichever opponent is nearest the ball. The moment your team is the last
toucher of the ball, switch: the presser takes intent "shoot", the back becomes a
"wing" with intent "intercept" targeting 10 metres up-field on the far side, and only
the keeper stays home. Use "pass" to the wing whenever an opponent is within 3 metres
of your ball carrier. Use "clear" with kick "auto" any time the ball is inside your own
penalty area with an opponent closer to it than you are. Never send all three robots
past the halfway line, and never send more than one robot into the same corner.
```

### The control layer (deterministic, integer-only, shared by every policy)

`src/cogball/control.nim`. Both LLM directives and scripted directives are compiled by the *same*
code, so the two policy kinds are strictly comparable. It is a pure function of
`(sim state, directive, robot index)` → `uint8`. For each robot, each tick:

1. **Steering point `p*`** by intent (`b` = ball, `vb` = ball velocity, `x` = robot position,
   `G` = opponent goal centre, `Gown` = own goal centre; all in µm):
   - `chase`: `p* = b`.
   - `intercept`: `τ = clamp(dist(b,x) div (RobotMaxSpeed + |vb|), 0, 36)` ticks; `p* = b + vb·τ`.
   - `hold`: `p* = directive.target` (clamped into the pitch on parse).
   - `shoot`: `p* = b − unit(G − b)·900 000`.
   - `pass`: `p* = b − unit(T − b)·900 000`, `T` = `pass_to`'s position + its velocity × 12 ticks
     (falls back to `shoot` when `pass_to` is missing, self, or an opponent).
   - `clear`: `p* = b − unit(C − b)·900 000`, `C = (22 000 000, b.y < 12 500 000 ? 2 500 000 : 22 500 000)`.
   - `press`: `p* = o + vo·12` for the opponent `o` nearest the ball.
   - Every intent except `hold` blends the directive target as a 20 % bias:
     `p* = (p*·4 + target) div 5`.
2. **Boards-escape override** (the round-1 learning, in the control layer). The ball is *on the
   boards* when `b.y < 2 000 000` or `b.y > 23 000 000` or `b.x < 4 000 000` or `b.x > 40 000 000`,
   **except** when `9 000 000 ≤ b.y ≤ 16 000 000` (the goal-mouth corridor is normal play, so a shot
   at goal is never redirected). When the ball is on the boards and this robot is the closest of its
   trio to the ball: the kick aim becomes the **escape point**
   `E = (22 000 000 + 6 000 000·attackDir, 12 500 000)`, the steering point becomes
   `p* = b − unit(E − b)·900 000`, and `kick` is forced to `auto` for this tick even if the
   directive said `never`. Robots that are not the closest of their trio are pushed 3 m off the
   boards toward the middle (their `p*` y is clamped to [3 000 000, 22 000 000]) so a whole trio
   cannot pile into one corner. The sim-level neutral drop (§The game) is the backstop.
3. **Turn command.** `want = bradsOfVectorI(p*.x − x.x, p*.y − x.y)`;
   `err = ((want − headingBrads + 128) mod 256) − 128`; PD term `e = err·16 − 2·spin`;
   `u_turn = +1 if e > 8`, `−1 if e < −8`, else `0`. (`bradsOfVectorI` is the integer atan2 in
   §Sim module; there is no `arctan2` anywhere in the sim or the control layer.)
4. **Thrust.** `d = dist(p*, x)`. `u_thrust = +1` when `|err| ≤ 48` brads and `d > 300 000`;
   `u_thrust = −1` (back out rather than pirouette) when `|err| > 96` and `d < 2 000 000`;
   otherwise 0. `ButtonSelect` (brake) is set when `d < 300 000` and the along-heading speed exceeds
   40 000 µm/tick. A `hold` robot whose `d < 400 000` re-runs step 3 with `p* = b` (hold the spot,
   face the ball).
5. **Kick.** `ButtonA` is set iff `directive.kick == "auto"` (or the boards override fired) **and**
   `kickCooldown == 0` **and** the ball is inside kick range **and** the aim error to the intent's
   kick target (opponent goal for `shoot`, `T` for `pass`, `C` for `clear`, `E` for the boards
   override, the ball-away-from-own-goal direction otherwise) is ≤ 32 brads. `kick: "never"` with no
   boards override forces the bit to 0. `hold` and `press` never kick unless the ball is between the
   robot and its own goal.

### Scripted baselines

Both emit the *same* directive object on the same 5 s cadence, so their output is legal by
construction and directly comparable to an LLM's. Both are pure functions of the world state, which
is what makes the bounded-orders test in §Tests meaningful.

- **`formation`** (the certification player, the fallback directive, and the default): the robot
  **nearest its own goal** (smallest `|x − xOwnGoal|`, ties by ascending robot index) is `keeper`,
  intent `hold`, target `(xOwnGoal + 3 m·attackDir, clamp(b.y/3, ±2.6 m))`. Of the remaining two, the
  one nearest the ball is `striker` — intent `shoot` if the ball is in the opponent half or within
  6 m, else `chase`, overridden to `clear` when the ball is inside its own penalty area. The third
  is `back` when the ball is in the own half (intent `hold`, target = midpoint of ball and own goal,
  pulled 1.5 m to the far y-side) and `wing` otherwise (intent `intercept`, target
  `(b.x + 7 m·attackDir, 12.5 m − sign(b.y − 12.5 m)·5 m)`). `kick: "auto"` for all; fixed short
  `note`/`say`.
- **`swarm`** (the second filler, deliberately weaker and different in shape): all three robots get
  intent `chase` with `kick: "auto"` and targets at the ball, except the robot nearest its own goal,
  which gets `hold` on the goal arc **only while the ball is in its own half**. Roles reported as
  `striker`/`striker`/`back`. The "everyone chases" baseline; it loses to `formation` and gives the
  ladder a spread.

---

## Sim module

### What is replaced and what is kept, by path

**Replaced — the ctf arena rules go** (teams/guns/flags/fog-of-war/lives/respawn/grenades/spray
cans/shields/barriers/puddles/trenches/perks/handicaps/barrage/procedural terrain all leave the
repo):

| ctf path | cogball |
|---|---|
| `src/ctf/sim.nim` (3540 lines: gameplay core, combat, vision, items) | `src/cogball/sim.nim` — the physics core and step loop (§The game resolution order). |
| `src/ctf/arena.nim`, `map_art.nim`, `map_pool.nim`, `mapgen_styles.nim`, `tools/map_editor*`, `tools/mapkit.nim`, `tools/gen_map_pool.nim`, `docs/pool-review.html`, `docs/MAPKIT.md` | `src/cogball/pitch.nim` — a fixed 44 m × 25 m pitch: geometry constants, the collision half-planes, and the pixie turf bake. No generator, no validators, no pool, no editor. **Deleted, not ported.** |
| `src/ctf/global.nim` fog-of-war, vision cones, first-person raycast, killfeed art, item sprites | `src/cogball/global.nim` — pitch/robot/ball/trail/FX sprite composition. Perfect information: no fog. |
| `players/baseline/baseline.nim` (3236-line CTF bot) | `src/cogball_player.nim` — a thin registrar (§Server). |
| `docs/RULES.md`, `docs/PROTOCOL.md`, `docs/ENV_VARIATION.md`, `docs/designs/`, `docs/ladder/`, `docs/plans/*` | rewritten for cogball; the ctf plans/designs are deleted. |
| `arena/` (wit component bindings), `caos/`, `caos-tools/`, `scripts/`, every `tools/*probe*.nim`, `tools/*spray*`, `tools/nade_probe.nim`, `tools/perk_check.nim`, `tools/four_team_map_probe.nim`, `tools/symnone_*`, `tools/render_replay_movie*`, `tests/*` | deleted. |

**Kept verbatim** (mechanical `ctf` → `cogball` / `CTF_WIRE` → `COGBALL_WIRE` rename sweep only; a
CI grep asserts no `ctf_`/`CTF_` identifier survives outside comments):

| Path | Why it is kept |
|---|---|
| `src/ctf/replays.nim` → `src/cogball/replays.nim` | the whole replay codec wrapper, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`. Two named edits below. |
| `src/ctf/replay_runtime.nim` → `src/cogball/replay_runtime.nim` | `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` — byte-identical apart from imports. |
| `src/ctf/server.nim` → `src/cogball/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, the replay-switch path, `COGAME_*` runtime contract, `declarePlayerFailure`, the artifact-write block. Four named edits below. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, lobby countdown. New fields, same machinery. |
| `src/ctf/roster.nim` | join/auth/rewards/`playerResultsJson`. Same shape; cogball result keys. |
| `src/ctf/events.nim` | the tier-2 event wire format and `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/wire_constants.nim`, `tools/gen_wire_constants.nim` | the one-source JS wire-constant block. |
| `src/ctf/labels.nim`, `src/ctf/rig_art.nim` | HUD labels and the wheeled-rig art compositor. |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | the emscripten link flags (`-s ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`), the OffscreenCanvas Worker, the stage-note diagnostics. |
| `client/broadcast_core.js` | game-agnostic sprite-protocol ingest, canvas blit, zoom/pan, minimap. Verbatim apart from the one `window.CTF_WIRE` identifier. |
| `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix` | build, bundle and forensics wiring. |
| `data/font.ttf`, `data/atlas/*`, `data/rig_real/blue/*`, `data/rig_real/red/*`, `data/ascii.png`, `data/darkbg.png` | real art, kept. Everything CTF-specific (`soldier_*`, `heart_*`, `paintgun*`, `medkit`, `shield`, `spraycan`, `paintbomb`, `ped_*`, `client/art/lockerroom/*` non-blue/red) is deleted. |

**The four named edits to `server.nim`:**

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   cogball calls `control.compileMasks(sim, directives)` and fills `inputs[robotIndex]` for the six
   robots. `writeInputFrameMasks` is called with the robot index. Player sockets no longer
   contribute input.
2. **Turn boundary.** Immediately before stepping a tick where `tick mod turnTicks == 0`, the loop
   runs `decide.turn(sim, llm, seats)`, which issues the one parallel batch, applies the deadlines,
   installs the directives and writes the directive/fallback records. All of it inside a monotonic
   `turnBudgetMs` bound.
3. **Registration interception.** A player's Sprite v1 chat message
   (`SpriteClientChatMessage`, already surfaced by `applyPlayerViewerMessage` as `chatText`) whose
   text parses as a registration object is consumed as registration and **is not written to the
   replay chat stream** — the server writes a redacted `register` record instead (policy label and
   kind, never the prompt). Any other chat text from a player is dropped.
4. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration forces
   `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.

**The two named edits to `replays.nim`:**

1. **Masks are indexed by robot, not by roster slot.** `replayPrevInputs`/`replayInputs` build
   `seq[InputState](RobotCount = 6)` instead of `sim.players.len`, and `replayWriter.lastMasks` is
   sized to 6. Joins/leaves still carry the two seats (names, tokens, rewards).
2. **A leave does not shift the mask arrays.** ctf deletes a leaving player's mask/overlay entries;
   cogball's robots are fixed for the whole match, so `applyReplayEvents` removes the roster entry
   and leaves the six mask slots alone. (This is exactly the bug class ctf's delete-on-leave exists
   to avoid *for a per-player game*; keeping it here would renumber robots mid-replay.)

Plus: `CtfReplayMagic "COWLDCTF"` → `CogballReplayMagic "COWLDBAL"`, `GameName* = "cogball"`,
`GameVersion* = "1"` with ctf's prepend-only changelog-comment discipline and
`tools/ci/check_gameversion.sh` kept as is.

### Integer arithmetic rules (the determinism contract)

Nim's `int` is 64-bit natively and **32-bit under `--cpu:wasm32`**, which is the exact hazard ctf
documents (`AGENTS.md`: "`int64` in the diagonal test for wasm"; `wasm_replay_smoke.cjs`: "overflow
checks trap on arithmetic that is silently fine natively"). So:

- Every stored sim field is explicitly `int32` (positions, velocities, `headingQ`, `spin`,
  cooldowns, counters) or `bool`/`enum`. No bare `int` in a hashed field.
- **Every product or quotient of two sim quantities is computed in `int64`** and narrowed back with
  an explicit truncating `div` (Nim's `div` truncates toward zero, so the arithmetic is symmetric
  under negation — which is what makes the two ends of the pitch exactly fair).
- **No floating point anywhere under `src/cogball/{sim,pitch,control}.nim`.** No `sin`, `cos`,
  `arctan2`, `sqrt`, `pow`, `float`, `float32`, `float64`. Grep-enforced in CI. (Floats remain legal
  in the *render* modules — `global.nim`, `rig_art.nim`, `map_art` — because rendering never enters
  `gameHash`, exactly as in ctf.)
- Trigonometry is a **committed literal table**: `SinQ12*: array[256, int32]` in
  `src/cogball/trig.nim`, where `SinQ12[b] = round(4096 · sin(2πb/256))`, generated once by
  `tools/gen_trig_table.nim` and checked into the repo. `cosQ12(b) = SinQ12[(b + 64) and 255]`. A
  test re-derives every entry from `math.sin` and asserts equality, so the table can never drift and
  the *sim* never calls libm. A compile-time `const` computed from `sin()` was rejected: the two
  builds are two separate compilations, and a committed table removes the question entirely.
- `isqrt(v: int64): int64` — Newton's method with an integer seed, committed and unit-tested against
  an exhaustive small-value table plus perfect squares up to 2⁴⁰. The only square root in the sim.
- `bradsOfVectorI(dx, dy: int32): int32` — the integer atan2. Folds `(dx, dy)` into the first octant
  by sign and swap, then a 5-step binary search over brads 0..31 comparing
  `int64(dy)·cosQ12(m) ≶ int64(dx)·SinQ12[m]`, then unfolds. Exact, branch-deterministic, no libm.
  ctf's float `bradsOfVector`/`aimVector` stay in the render modules only.
- Randomness: ctf's existing seeded sim RNG (`std/random` `Rand` from `config.seed`, integer draws
  only), used for exactly one thing — kickoff y-jitter.

### How the replay achieves server↔viewer determinism

The mechanism is ctf's, unchanged, and the reason the operator's "keep the replay infrastructure
verbatim" is the right call:

1. The server writes a `COWLDBAL` replay: an 8-byte magic + format version + game name/version
   header, the **resolved config JSON** (seed, pitch constants, roster, every tuning field), then
   the record stream — joins (name, slot, token), leaves, per-robot input-mask changes, chat records
   (directives, fallbacks, the final result record), and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/cogball_replay.nim` — which imports the
   **same** `src/cogball/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` +
   `nimby 2.2.4` container in `Dockerfile.replay-viewer`.
3. In the browser, `cogball_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `cogball_frame` re-steps the sim from the recorded masks and compares `sim.gameHash()` against
   the recorded hash **every tick** (`checkReplayHash`). A single divergent bit is caught at the tick
   it happens, surfaced as `mismatchTick` in the chrome ("Replay hash mismatch — showing recorded
   inputs") and, in CI, as a hard failure.
4. **CI proves the cross-build equality on every push**: the `wasm-viewer` job builds the bundle and
   runs `node tools/wasm_replay_smoke.cjs replay-viewer/dist tests/fixtures/cogball-<seed>.bitreplay
   300`, which fails if `cogball_mismatch_tick() != -1`. The fixture is recorded by the **native
   amd64** build. That single command is the native↔wasm determinism gate, and it already exists in
   the starter.

Because the recorded action log is the six input masks, the control layer, the LLM and the directive
records are all *outside* the determinism boundary — the entire class of "the control layer was
reimplemented in the viewer and drifted" bugs is structurally impossible. This is round 1's
conclusion, reached with paintbot's machinery instead of a new one.

Perf target: 4800 ticks of physics + serve in under 30 s on a CI runner; `tests/test_perf.nim`
bounds it at 120 s.

---

## Server, player, protocol

`src/cogball/server.nim` is ctf's `server.nim` with the four edits named above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`), same `COGAME_*` runtime contract
(`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`,
`COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`, `COGAME_HOST`/`COGAME_PORT`),
same 403 on a bad slot/token, same done-before-artifact-writes ordering, same
`src/cogball.nim` entrypoint (seed randomisation before `config.update`, kept verbatim).

### The player container

`src/cogball_player.nim` (built to `/bin/cogball-player`) reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects, and sends **one Sprite v1
chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"formation"|"swarm"|null,"policy":"<free label>"}
```

It then sends the Sprite v1 Ready packet (`0x85`) after each received frame — legitimate here
because it never sends inputs (see §Decisions) and it is what lets `fastMode` pace the match by
readiness — and otherwise only receives, until the socket closes. A seat that never registers, or
registers with neither field, is `scripted: "formation"`. Registration is re-sent once after the
first received frame, in case the first send raced the slot registration (babel's pattern).

### The per-seat stream (what a seat can see)

Each seat's websocket receives ctf's normal per-player Sprite v1 frame, one binary message per tick,
built by `buildSpriteProtocolPlayerUpdates`. **Visible**: the whole pitch and every body — soccer is
a perfect-information sport, so there is **no fog of war** (ctf's vision cone, bubble, window and
first-person modules are deleted); the score; the clock; its own robots marked with a self marker;
and an invisible `own seat <alias>` HUD marker naming the seat. **Hidden**: the opponent's
directives, roles, intents, `note`/`say` and prompt; the episode seed; **real player names** (board
labels carry only `Azure`/`Crimson` and `AZ-1..3`/`CR-1..3` — `showPlayerLabels` is forced false on
the player stream); and future ticks.

### The per-seat view given to the LLM

Numbers rounded to 2 decimals, in **view coordinates** (metres, centred). This object is the tail of
the LLM user message and is also mirrored into the `directive` record for the feed.

```json
{"turn": 7, "of": 40, "clock": {"played_s": 35.0, "left_s": 165.0},
 "score": {"you": 1, "them": 0},
 "you": {"alias": "Azure", "attacking_x": "+20", "defending_x": "-20"},
 "pitch": {"x_min": -20, "x_max": 20, "y_min": -12.5, "y_max": 12.5,
           "goal_half_width": 3.5, "your_penalty_area": "x <= -14, |y| <= 7",
           "walled": true},
 "ball": {"pos": [3.21, -1.04], "vel": [4.10, 0.62], "speed": 4.15,
          "possession": "AZ-2" | "CR-1" | "loose", "in_your_half": false,
          "on_boards": false},
 "your_robots": [{"id": "AZ-1", "pos": [-16.9, 0.4], "vel": [0.2, -0.1],
                  "facing": [1.0, 0.0], "speed": 0.22, "kick_ready": true,
                  "dist_to_ball": 20.1, "last_role": "keeper"}, "… 3 …"],
 "their_robots": [{"id": "CR-1", "pos": [7.7, 2.1], "vel": [-3.0, 0.4],
                   "facing": [-0.99, 0.13], "speed": 3.03,
                   "dist_to_ball": 5.6}, "… 3 …"],
 "last_turn": {"your_kicks": 2, "their_kicks": 1, "your_shots": 1,
               "their_shots": 0, "possession_pct_you": 63,
               "goals": [{"tick": 890, "by": "AZ-3", "for": "you"}]},
 "your_last_directive": "… the directive your seat played last turn, or null on turn 0 …"}
```

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape:

```json
{"note": "compact, keeper stays home",
 "robots": [{"id": "AZ-1", "role": "keeper", "intent": "hold", "target": [-17.0, 0.4],
             "pass_to": null, "kick": "auto", "say": "holding the arc"}, "… 3 …"]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `robots` | array | exactly the seat's 3 robots | extra entries dropped; missing ids filled from last turn's directive for that robot, else from `formation` |
| `robots[].id` | string | `AZ-1..3` / `CR-1..3`, case-insensitive, **≤ 8 runes** | unmatched entries assigned to the seat's robots by position |
| `robots[].role` | enum | `keeper` `back` `wing` `striker` | → `wing` |
| `robots[].intent` | enum | `chase` `intercept` `hold` `shoot` `pass` `clear` `press` | → `chase` |
| `robots[].target` | [num, num] | finite; clamped to x ∈ [−20, 20], y ∈ [−12.5, 12.5] | non-finite/missing → the robot's current position |
| `robots[].pass_to` | string \| null | a *teammate* id ≠ self | → `null` (and `pass` degrades to `shoot`) |
| `robots[].kick` | enum | `auto` `never` | → `auto` |
| `robots[].say` | string | **≤ 48 runes** | truncated to 48 runes |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized directive record **≤ 900
runes** (it is a replay chat record; ctf's 10-char shout cap is deliberately raised, and the new cap
is asserted in `test_replay.nim`). `register.prompt` is capped at **≤ 4000 runes** at the transport
(over-long is truncated, never rejected) and is **never** written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim that means
`runeLen`/`runeSubStr` (babel's `cleanNotes`, ported); slicing a `string` by byte index on any path
to the replay is forbidden. A byte-truncated multi-byte character is exactly the bug that makes
replay bytes render in a browser but fail a strict parser (playbook gotcha), and §Tests pins it with
a 4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose (babel's `extractJsonObject`); accept `robots` as an object keyed by id; accept
numeric strings for `target`. Only when no object with at least one usable robot entry can be
recovered do the retry and then the fallback fire.

### Results document

Written by `sim.playerResultsJson()` (ctf's function, cogball keys) to `COGAME_RESULTS_URI`. It must
equal the manifest's `results_schema` key-for-key — that schema is `additionalProperties: false` and
the certifier rejects any unknown field (`roster.nim` carries the scar: `shotsFired`/`shotsHit` were
pulled back out of the payload for exactly this reason). Adding or removing a key here means editing
`coworld_manifest_template.json` in the same commit.

```json
{"names": ["daveey", "daveey-1"],
 "scores": [0.667, 0.333],
 "win": [true, false],
 "team": ["azure", "crimson"],
 "goals": [2, 1],
 "shots": [9, 6],
 "shotsOnTarget": [4, 2],
 "saves": [1, 3],
 "possessionTicks": [2640, 2160],
 "llmTurns": [40, 0],
 "fallbackTurns": [0, 0],
 "reason": "complete",
 "endRule": "full_time",
 "finalTick": 4800,
 "seed": 679961}
```

`names` are the **real policy names** (spectator side). `team` carries the in-game aliases.

### Replay bytes (self-sufficient)

**Deliberate change from round 1:** the replay stays the starter's **binary `COWLDBAL`** format, not
JSON. The operator's ruling requires the replay infrastructure be kept verbatim, and the static wasm
viewer literally parses this format; a JSON replay would mean rewriting `replays.nim`,
`replay_runtime.nim`, `static_replay_worker.js` and `wasm_replay_smoke.cjs` — the exact machinery
the ruling protects. The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design ("set 0 for a binary replay format").
- The repo ships **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker) which takes
  a `.bitreplay` path and prints one strict-UTF-8 JSON object to stdout:
  `{"protocol":"cogball/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "policyKinds":[…],"tickCount":…,"directives":[…],"fallbacks":N,"results":{…}}`. It brace-matches
  the config JSON from the first `{` (the technique ctf's `AGENTS.md` documents for prod forensics)
  and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4** is therefore:
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                       # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "cogball/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), and the champion seats' directives `source == "llm"` with non-empty `note`/`intent`
  content — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDBAL`, format version, `gameName` `cogball`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `maxTicks`, `turnTicks`, every physics/tuning constant, `players[].name` (real names), `slots[].team`, `fastMode` |
| joins | per seat: `name` (real policy name), `slot`, `token` |
| inputs | per **robot** (0..5), on change: the `uint8` actuator mask — the action log |
| chats | the directive / fallback / register / result records (below) |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: a 4800-tick match writes ≈ 4800 hashes (8 B each), input changes on the order of 60 k records,
40 × 2 directive records ≈ 60 KB, well under 1 MB.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed sim
fields; they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `policy` (≤48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `turn`, `seat`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `robots`:[{`id`,`role`,`intent`,`target`,`pass_to`,`kick`,`say`}] |
| `fallback` | `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at game over |

**B. Derived broadcast events** — `stepEvents` (ctf's `broadcast.nim`, retargeted) derives these
from state deltas during playback, so they cost no replay bytes and are identical live and in
replay. They feed the match feed, the scrubber beat markers and the goal-difference momentum graph:
`phase`, `kick`, `touch`, `shot`, `save`, `pass`, `interception`, `post`, `goal`, `kickoff`, `drop`,
`turn_end`, `gameover`. `goal` and `drop` are **beats** (scrubber markers, and the trigger for the
slow-mo goal replay); `touch` is throttled to at most one per robot per 6 ticks.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets ctf's JSON-lines `eventsJsonl`, with
`SimEventKind` extended to `Kick, Touch, Shot, Save, Pass, Interception, Post, Goal, Kickoff, Drop,
PhaseChange, Directive`, and the mandatory trailing summary row (`type`, `ticks`, `events`,
`gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is ctf's
script, kept, with two literals changed (`image_tag`, and the `docker cp` source
`/workspace/cogball/replay-viewer/dist/.`); it builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copies the dist out. `coworld build` invokes it with the absolute
bundle directory; the script already refuses any output path that is not a `static-replay-viewer`
directory inside the repo. It must stay committed **executable** (`coworld build` requires
`os.X_OK`).

### Bundle contents

Built exactly as ctf builds its bundle, with the CTF-specific asset list swapped:
`index.html` (from `client/replay_broadcast.html` with the three marker splices),
`league.html`, `static_replay.js`, `static_replay_worker.js`, `chrome_common.js`,
`broadcast_core.js`, `wire_constants.js` (emitted by `tools/gen_wire_constants.nim`),
`cogball_replay.js` + `cogball_replay.wasm` + `cogball_replay.data`, `font.ttf`, and the two rig
sheets. The Dockerfile's `test -f` / `grep -q` assertion block is kept and retargeted, so a bundle
missing any of these fails the build rather than the browser.

### Chrome kept, readouts retargeted

`client/broadcast_core.js` (1407 lines: sprite-protocol ingest, layer compositing, zoom/pan,
minimap, playout) is **game-agnostic and kept verbatim** apart from the one `window.CTF_WIRE`
identifier. `client/replay_broadcast.html` (4141 lines) keeps its CSS, markup and behaviour
**verbatim**: the locker-room loading screen, `#stage`/`#board`, `#scorebug` with its plates and
clock column, `#minimap` + `#zoombar`, `#bannerlane`, `#killfeed` (the feed lane), `#transport`
(restart / step-back / play-pause / step / speed / scrubber / tick readout), `#endcard`, `#mmwarn`
(the hash-mismatch line), the `?embed=1` mode, and `relayout()`'s `--hudscale`/`.tiny` density
system. `client/chrome_common.js` keeps every mechanism — plate rendering, feed rows, beat markers,
the momentum curve, the spoilers switch, the end-card — and only its **field mapping** changes,
because the state JSON keys (`t`, `mt`, `ph`, `pl`, `sp`, `mx`, `st`, `lp`, `sk`, `ff`, `en`, `mm`,
`bs`, `pov`, `teams`, `roster`, `events`, `lead`, `beats`, `lulls`, `over`, `hold`) are kept and
`teamStateJson` is re-populated.

Readouts, all of them:

1. **Score bug** (top, always on): the two team plates — real policy name (spectator side), livery
   chip, **goals**, possession %, shots — around the centre clock column. `teams.<alias>` carries
   `{goals, poss, shots, sot, policies}` in place of ctf's `{lives, flag, carrier, prog}`.
2. **Clock**: `M:SS` from `tick div 24` plus `turn 22/40` in the clock caption.
3. **Match feed** (`#killfeed`, renamed in copy only): the last rows in plain language — "AZ-2
   shoots — saved by CR-1", "GOAL Azure — AZ-3 (assist AZ-1), 14.2 m/s", "Azure coach: keep CR-3
   pinned wide". Directive `note`/`say` strings appear here; this is where a spectator sees the LLM
   playing.
4. **Ball trail**: the last 45 tick positions as a tapering ribbon, tinted by the last toucher's
   livery — drawn Nim-side as sprite objects on ctf's existing FX layer (`ShotFxTicks`/`TrailFalloff`
   machinery reused).
5. **Kick FX**: on every kick, an expanding ring at the contact point (0.35 m → 1.6 m over 12
   frames) plus a one-frame white flash on the ball.
6. **Goal celebration**: full-canvas flash, 120 particles in the scoring livery for 45 frames, and a
   `GOAL!` chip in the existing `#bannerlane`.
7. **Instant slow-mo goal replay**: goals are `beats`, which the chrome already receives up front.
   On first reaching a goal tick, the transport pauses 0.5 s, seeks back 72 ticks, replays those
   3 seconds at the slowest `PlaybackSpeeds` step with a "GOAL REPLAY" banner and a vignette, then
   seeks forward to the goal tick and restores the previous speed. Implemented purely with the
   existing seek/speed commands (`applyReplayCommand`), one replay per goal (a `seen` set), and any
   manual scrub cancels it.
8. **Position-history tinting → paint**. This is where cogball is most literally paintbot: each
   robot has its own hue (Azure 190/202/214, Crimson 348/0/12) and **paints the turf it drives
   over**, accumulating into the board layer with the starter's existing paint-stain machinery. Over
   3:20 the keeper's arc, the back's shuttle and the striker's runs separate visually — roles
   emerging with no labels, exactly as the idea asks. Toggle key `h` (default on).
9. **Momentum graph**: ctf's `lead` series with **goal difference** in place of lives lead, drawn
   over the whole timeline from the first frame.
10. **Transport and integrity**: ctf's play/pause, step, speeds `[1,2,3,4,8,16]`, scrubber with beat
    markers, tick readout, skip-lulls, end-card ("Azure wins 2–1 · full time"), the end-hold
    countdown, and the `#mmwarn` hash-mismatch line — all verbatim.

### Art

Real, and mostly already in the repo. Robots are the shipped **`data/rig_real/blue/*`** (Azure) and
**`data/rig_real/red/*`** (Crimson) wheeled rigs composed by `rig_art.nim` — wheels, body, head,
per-heading rotation, drop shadow — which is why the alias changed from "Magenta" to "Crimson". The
pitch is baked once at startup with pixie (already a dependency, already how ctf bakes its board):
mown turf in two greens with 2.5 m stripes, painted white lines at 0.12 m stroke (touchlines,
halfway line, centre circle, penalty areas, goal arcs), hatched goal nets with depth, and a dark
vignette surround. The ball is a baked shaded sphere with a rolling seam. No solid-colour
placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked at 360 px, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW ≤ 620`, with the
CSS comment naming "the 640×360 floor". Kept verbatim. Cogball adds two rules of its own: the plate
policy name gets `flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis` so a
name never collapses to "…", and under `.tiny` the possession % and the shots figure are hidden so
the plates read `▮ daveey 2 — 1 daveey-1 ▮` plus the clock. The board aspect is 1100:625, which the
chrome derives from the stream (`BOARD_ASPECT` is recomputed from `s.boardW`/`s.boardH`).
`tests/test_viewer.nim` asserts the `.plate-name` rule and the `.tiny` block are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-cogball`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `cogball`.
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{COGBALL_IMAGE}}`:

  ```yaml
  services:
    cogball:
      image: coworld-cogball:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

  (ctf ships two services/two images; cogball uses babel's one-image/two-entrypoints shape because
  the shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — ctf's two-stage debian-slim + nimby layout verbatim in structure
  (nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from the
  container's package tree as babel does), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:cogball src/cogball.nim` →
  `/bin/cogball`, and the same for `src/cogball_player.nim` → `/bin/cogball-player`. Runtime stage
  copies `/bin/cogball`, `/bin/cogball-player`, `data/`, `client/`, `*.json`.
  `CMD ["/bin/cogball"]`.
- **`Dockerfile.replay-viewer`** — ctf's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby 0.1.27
  with its sha256 check, the marker splices, the assertion block) with the asset list swapped.
- **`coworld_manifest_template.json`**:
  - `game.name` `cogball`; `game.runnable` `{"type":"game","image":"{{COGBALL_IMAGE}}",
    "run":["/bin/cogball"],"env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/cogball/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-cogball/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema` (`additionalProperties: false`, required `["tokens","players"]`):
    `tokens`, `players`, `slots`, `closedRoster`, `seed`, **`num_agents`**, `minPlayers`,
    `maxTicks` (default 4800), `maxGames` (default 1), `turnTicks` (default 120),
    `turnBudgetMs` (default 9000), `attempt1Ms` (default 6000), `retryMs` (default 2500),
    `wallClockBudgetSeconds` (default 690), `lobbyJoinTimeoutTicks` (default 2400),
    `startWaitTicks` (default 24), `gameOverTicks`, `mercyGoalDiff` (default 5),
    `stalemateTicks` (default 240), `fastMode` (default true), `showPlayerLabels`,
    `model`, `maxOutputTokens` (default 900), `kickImpulse`, `robotMaxSpeed`, `ballMaxSpeed`.
  - `game.results_schema`: exactly the 15 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","team","goals","reason","endRule"]`, `reason` enum
    `["complete","deadline","fault"]`, `endRule` enum
    `["full_time","mercy","wall_clock","sim_fault","host_error"]`, every array `minItems: 2,
    maxItems: 2`.
  - `game.protocols`: **both** `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-cogball/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs`: `readme` = `{"type":"text","value":"<README body inlined>"}` and `pages` = three
    entries — `rules.md` ("Rules", `docs/RULES.md` inlined), `protocol.md` ("Wire protocol",
    `docs/PROTOCOL.md` inlined), `coaching.md` ("Writing a cogball prompt", `docs/COACHING.md`
    inlined), each `{"id","title","content":{"type":"text","value":…}}`. **Text form, not URIs**
    (playbook gotcha; ctf's URI form is not copied). A manifest test asserts all four values are
    non-empty.
  - `game.tags`: `["soccer","physics","team","continuous","llm"]`.
  - `player[0]` = `{"id":"baseline","name":"Cogball Formation Baseline","type":"player",
    "image":"{{COGBALL_IMAGE}}","run":["/bin/cogball-player"],
    "env":{"PLAYER_SCRIPTED":"formation"},"source_url":…,"resources":{"requests":{"cpu":"100m",
    "memory":"64Mi"},"limits":{"cpu":"1"}}}` — the bundled certification player, no LLM.
  - **Variants — `num_agents` is 2 in both:**

    | id | name | `num_agents` | `players`/`slots` | `minPlayers` | `maxTicks` | turns | `turnTicks` | `turnBudgetMs` | `wallClockBudgetSeconds` |
    |---|---|---|---|---|---|---|---|---|---|
    | `default` | Match (2 seats × 3 robots, 3:20) | **2** | 2 | 2 | 4800 | 40 | 120 | 9000 | 690 |
    | `sprint` | Sprint (2 seats × 3 robots, 1:40) | **2** | 2 | 2 | 2400 | 20 | 120 | 9000 | 400 |

    Both seat two players, `slots: [{"team":"azure"},{"team":"crimson"}]`, `fastMode: true`,
    `maxGames: 1`. `sprint` exists for cheap ladder rounds; it changes only match length, never the
    seat count.
  - **Certification fixture**: `certification.players` = `[{"player_id":"baseline"},
    {"player_id":"baseline"}]`; `certification.game_config` = `{"players":[{"name":"Azure"},
    {"name":"Crimson"}], "slots":[{"team":"azure"},{"team":"crimson"}], "num_agents": 2,
    "minPlayers": 2, "seed": 679961, "maxTicks": 1200, "maxGames": 1, "turnTicks": 120,
    "turnBudgetMs": 9000, "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 1440,
    "fastMode": true}` — 10 turns, both seats scripted, no LLM, a handful of wall-clock seconds.
- **Scaffold from `templates/`** with `<slug>` = `cogball`, `<IMAGE>` = `coworld-cogball`,
  `<SEATS>` = **2**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/ci/policies.json`, and ctf's
  `tools/build_replay_viewer.sh` (**`chmod +x`**). Two additions to the template `ci.yml`:
  - the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format, §Server);
  - the `wasm-viewer` job gets a final step
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer tests/fixtures/cogball-679961.bitreplay 300`
    — the native↔wasm determinism gate.
  `NIM_TESTS_RELEASE_ONLY` repo variable lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/cogball-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `cogball-total` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `cogball-counter` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `cogball-formation` | `PLAYER_SCRIPTED` = `formation` | filler |
  | `cogball-swarm` | `PLAYER_SCRIPTED` = `swarm` | filler |

- **Repo layout**: `src/cogball.nim`, `src/cogball_player.nim`,
  `src/cogball/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, pitch.nim, control.nim,
  directives.nim, baselines.nim, llm.nim, decide.nim, trig.nim, roster.nim, replays.nim,
  replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, rig_art.nim,
  wire_constants.nim, server.nim}`, `replay-viewer/{cogball_replay.nim, config.nims,
  static_replay.js, static_replay_worker.js}`, `client/`, `data/`, `tests/`, `tools/`,
  `docs/{RULES.md, PROTOCOL.md, COACHING.md, plans/}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `cogball.nimble`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for a fixed-point overflow). CI is the only
harness; the sandbox has no Nim, Docker or emsdk. The **determinism gate** (test 2 plus the wasm
smoke) is the inviolable test: if it fails, the physics or a build flag changed — fix the code,
never the test.

1. **`tests/test_physics.nim`** — sim unit tests: a ball fired at `BallMaxSpeed` into a wall for 600
   ticks never leaves the arena (no tunnelling); wall restitution reproduces the analytic bounce
   speed within the fixed-point quantum; robot–robot resolution is symmetric (swapping indices
   mirrors the outcome) and conserves momentum exactly; the kick sets the along-heading ball speed
   to exactly `max(vpar,0) + 375000` and applies the mass-ratio reaction; the goal test fires on the
   exact plane crossing and not one tick early or late; a ball rolled onto a post bounces and emits
   `post`; the kickoff reset places all seven bodies at the documented coordinates (jitter included,
   seed-pinned); the neutral drop fires at exactly 240 stalemate ticks and clears the 3 m radius.
2. **`tests/test_determinism.nim`** (**the gate**) — (a) same seed + same mask log ⇒ identical
   `gameHash` at every tick over a full 4800-tick match, run twice in one process and once in a
   fresh sim; (b) a one-bit change in any recorded mask changes the final hash; (c) a committed
   golden fixture `tests/data/golden_hashes.json` pins the hash at every 100th tick for seed 679961,
   so any physics change is visible in the diff; (d) **a source guard** that greps
   `src/cogball/{sim,sim_types,sim_config,sim_state,pitch,control,trig}.nim` for
   `sin|cos|tan|arctan|arcsin|exp|ln|pow|sqrt|hypot|float` and the build scripts for `-ffast-math`,
   failing on any hit; (e) `SinQ12` re-derived from `math.sin` entry by entry, and `isqrt` checked
   exhaustively below 2¹⁶ and on perfect squares to 2⁴⁰; (f) `bradsOfVectorI` agrees with a float
   `arctan2` reference to ±1 brad over 100 000 pseudo-random vectors, and is exactly antisymmetric
   under `(dx,dy) → (dx,−dy)`.
   The **cross-build half of the gate** runs in the `wasm-viewer` CI job:
   `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer tests/fixtures/cogball-679961.bitreplay 300`
   fails if `cogball_mismatch_tick() != -1`, i.e. if the emscripten wasm32 sim diverges by one bit
   from the native amd64 recording. This is also the only place a wasm32 32-bit `int` overflow can
   be caught.
3. **`tests/test_control.nim`** — the control layer: every intent produces a mask with only legal
   bits and never both Up+Down or Left+Right set with a non-zero effect; the same (state, directive)
   pair always yields the same byte; `kick: "never"` never sets `ButtonA` **unless** the boards
   override fired; the cooldown is respected; the boards-escape rule fires inside the band, does
   **not** fire inside the goal-mouth corridor, and aims the kick within 32 brads of the escape
   point; a ball parked in a corner with three robots on it is out of the corner within 120 ticks.
4. **`tests/test_baselines.nim`** — **bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines, the emitted directive validates
   against the reply schema — exactly three robots, ids exactly that seat's robots, all enums legal,
   targets finite and inside the pitch, `pass_to` a teammate or null, `note` ≤ 160 runes, `say` ≤ 48
   runes — and every compiled mask has only legal bits. Plus: a `formation` vs `swarm` match at seed
   679961 completes, ends `complete/full_time` or `complete/mercy`, `formation` wins, and **the
   match is not 0–0** (the round-1 corner regression, pinned).
5. **`tests/test_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   `robots` as an id-keyed object, unknown enums, NaN/absent targets, out-of-pitch targets, four
   robots, zero robots, an id from the other team, a 300-character `note`, and a `say` whose 48th and
   49th characters are a 4-byte emoji — the truncation must land on the **rune** boundary and the
   result must still round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒
   the `formation` directive plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry.
6. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: both seats' calls go out in
   **one parallel batch** (the fake records in-flight windows and the test asserts they intersect);
   the per-turn budget is enforced with a hung client; the budget guard switches to scripted and the
   episode still ends `complete/full_time`; the 690 s stop yields `deadline/wall_clock`; a raised
   physics guard yields `fault/sim_fault` with 0.5/0.5 scores and a partial replay; mercy fires at
   goal difference 5; a disconnected seat plays `formation` and revives on reconnect; a never-connecting
   seat is reported to `COGAME_PLAYER_FAILURE_URI` and the match still reaches `full_time`.
7. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full
   scripted-vs-scripted episode writes `results.json` and a `COWLDBAL` replay; `parseReplayBytes`
   accepts it; re-simulating from the config + mask log reproduces **every** recorded hash;
   `tools/replay_summary.py` output parses under a **strict UTF-8 JSON** parser
   (`json.loads(out.decode("utf-8"))`) with the fixture forced to carry a non-ASCII `say` and a
   non-ASCII policy label, so the UTF-8 path is real; the embedded config JSON decodes strictly;
   every directive record is ≤ 900 runes; `results.reason` is in the legal enum; the record stream
   contains at least one `kick`, one `shot`, one `directive` per seat per turn, and exactly one
   `result` record.
8. **`tests/test_server.nim`** — websocket contract: registration chat accepted and **not** echoed
   into the replay chat stream; a prompt over 4000 runes is truncated, not rejected; a non-registration
   chat from a player is dropped; bad token 403; `/healthz`; `/global` snapshot then ticks then
   game-over; `/client/global`, `/client/player`, `/client/replay`; artifact writes to `file://`
   URIs; **two-name-space enforcement** — the composed LLM user message and the player-stream board
   labels contain no `sim.players[i].address`, while the chrome roster and `results.names` do.
9. **`tests/test_manifest.nim`** — `num_agents == 2` in **every** variant *and* in
   `certification.game_config`; `len(certification.players) == 2`; results_schema keys ==
   `playerResultsJson` keys; `game.protocols` has both `player` and `global`; `game.docs.readme` and
   all three pages are non-empty **text**; `replay_viewer.bundle == "static-replay-viewer"`; every
   variant's `wallClockBudgetSeconds ≤ 0.6 × 1200`; the compose service name and image match
   `{{COGBALL_IMAGE}}` / `coworld-cogball`; `config_schema` covers every field
   `sim_config.update` reads.
10. **`tests/test_viewer.nim`** — **viewer smoke** (no browser): a static assertion over
    `client/replay_broadcast.html` and `client/chrome_common.js` that the transport controls,
    `#scorebug`, `#bannerlane`, `#killfeed`, `#endcard`, `#mmwarn`, the `.tiny` block, the
    `--hudscale` clamp and the `.plate-name { flex: 1 1 auto; min-width: 3.2em` rule are present;
    that `broadcast_core.js` differs from the starter's copy in **exactly** the `COGBALL_WIRE`
    identifier; that no `ctf_`/`CTF_` identifier survives anywhere in `client/`, `replay-viewer/` or
    `src/`; and that `wire_constants.js` renders `window.COGBALL_WIRE={speeds:[1,2,3,4,8,16],fps:24,…}`.
    The runtime half is the CI `wasm-viewer` job: the bundle builds, contains a non-empty `.wasm`,
    and `wasm_replay_smoke.cjs` loads a fixture and advances 300 frames with no mismatch and no
    abort.
11. **`tests/test_startup.nim`** — `/bin/cogball` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when
    unpinned and honoured when pinned; both entrypoints exist and are executable in the image
    (asserted by the docker smoke).
12. **`tests/test_perf.nim`** (release-only) — 4800 ticks of physics plus mask compilation complete
    in under 120 s.

CI additionally runs `tools/ci/docker_smoke.sh` (a raw-Docker episode from the certification
fixture, seats cross-checked against `SMOKE_SEATS=2`, `SMOKE_REQUIRE_REPLAY_JSON=0`) and
`tools/build_replay_viewer.sh` (bundle builds, `index.html` present, ≥1 non-empty `.wasm`).

---

## Out of scope (v1)

- **The 6-seat hero-per-seat variant** (one robot per seat, `num_agents` 6) and the cross-play report
  the idea mentions. It needs a different `num_agents`, which the seat-count pin forbids in v1. It
  is the first thing to add in v0.2 — and on this lineage it is nearly free, because at one robot per
  seat the Sprite v1 input mask maps 1:1 onto a connection and an external RL policy can drive a
  robot directly.
- **Raw per-tick actuator control by an external policy** in the 2-seat game. One 8-bit mask cannot
  address three robots; the v1 control channel is the directive + server-side control layer. The
  quantised action log is already shaped for the v0.2 protocol addition.
- **Box2D**, joints, polygons, friction cones, ball spin/Magnus, and any rigid-body feature beyond
  circles with headings. The idea proposed Box2D-to-wasm; it is rejected because its solver is built
  on `sinf`/`cosf`/`atan2f` and float32 accumulation orders, which would make the native↔wasm hash
  chain depend on two musl builds agreeing — untestable here and unfixable if it drifts. A 3v3 world
  needs only circle–circle and circle–halfplane contacts.
- **Soccer rules beyond the goal**: no out of play, throw-ins, corners, offside, fouls, cards,
  penalties, keeper handling or added time. The pitch is walled; the neutral drop is the only restart
  besides the kickoff.
- **Robot heterogeneity**: no per-robot stats, stamina, upgrades, damage or substitutions.
- **Everything ctf's arena rules carried**: guns, flags, fog of war, first-person POV, lives,
  respawn, grenades, spray cans, shields, barriers, puddles, trenches, perks, handicaps, the grenade
  barrage, procedural terrain, the map pool, the map editor and mapkit. Deleted, not disabled.
- **Mid-turn interruption**: directives are only replaced at 120-tick boundaries; there is no "coach
  shouts mid-play" channel.
- **Inter-seat chat.** The two seats never exchange messages; `note`/`say` are one-way to the feed.
- **Player debug-sprite overlays** (ctf's `0x86` channel). The seats send no inputs and draw no
  overlays in v1; the code path is deleted rather than left dangling.
- **Audio, 3D, camera cuts other than the slow-mo goal replay, and any downloaded art asset.**
- **Persistent memory across episodes** (no notes carried between matches) and any tournament
  structure beyond the platform league.
- **Campaign mode.** ctf's territory-campaign integration is a platform-side feature and is not
  wired up for cogball in v1.
