# cogball — design note (2026-08-22)

`Metta-AI/cogame-cogball`, a 3v3 robot-soccer Coworld in a continuous 2D physics world. It is
forked from **`Metta-AI/cogame-moba`** (mounted read-only at `/workspace/starters/cogame-moba`):
the same shape — a deterministic C sim compiled to wasm, hosted server-side by `wasmtime`, driven
by a lockstep Python `aiohttp` server over per-seat websockets, and re-simulated in the browser by
a static wasm replay viewer built from the *same* C source. **Every convention there holds here
unless this note says otherwise.** The starter was chosen because cogball's game shape is a
tick-driven continuous-physics sim whose replay is "seed + action log, re-simulated" — exactly the
moba/nmmo lineage, and the only starter of the six that already ships a wasm sim, a wasmtime host,
a deterministic re-simulating browser viewer, and a `tools/build_replay_viewer.sh` hook that
compiles the sim twice from one source. Four deliberate deviations from moba are listed and
justified in §Sim module and §Server, player, protocol (JSON replay instead of the binary `MOBA`
format; decisions made server-side rather than in the player container; a purpose-written physics
core instead of a vendored upstream; no `vendor/upstream` and therefore no fidelity gate — this is
a new game, not a port, so moba's two "inviolable rules" do not travel with it; the determinism
gate in §Tests replaces the fidelity gate as the inviolable test).

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

**Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits") and where each is satisfied:**

| Pin | How cogball satisfies it |
|---|---|
| Starter by game shape | `cogame-moba` — continuous tick sim, wasm module, seed + action-log replay (§The game, first paragraph above). |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-cogball`, public at creation (§Packaging). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | `PLAYER_PROMPT` (two champion prompts) vs `PLAYER_SCRIPTED=formation` / `PLAYER_SCRIPTED=swarm`, one image `coworld-cogball`, `run: /bin/cogball-player` (§Decisions, §Packaging). |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by `tools/build_replay_viewer.sh` (§Viewer, §Packaging). |
| Real art, starter chrome verbatim | moba's `viewer/index.html` chrome (CSS block, `#stage`/`#controls`/`#seek`/`#tickinfo`/`#endcard`/`#warn`) kept verbatim; all pitch/robot/ball art drawn as real raylib vector art, no placeholders (§Viewer). |
| Two name spaces | Prompts see `Azure`/`Magenta` and robot ids `AZ-1..3`/`MG-1..3` only; real player names appear only in `replay.names.players`, results, and the viewer scorebug (§Server, §Viewer). |
| Degrade-never-hang, play inside 60 % of `episodeTimeoutSeconds` 1200 | 629 s expected / 690 s hard stop against a 720 s budget, arithmetic spelled out in §Decisions; every wait bounded; LLM failure → retry once → scripted move (§Decisions). |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 2** in variant `default`, variant `sprint`, and `certification.game_config` (§Packaging). |

## The game

**Cogball is 3v3 robot soccer in a continuous 2D physics world.** Two teams of three wheeled
robots chase one ball on a walled indoor pitch and try to push it over the opponent's goal line.
Nothing is gridded: positions, velocities and headings are IEEE doubles; the only discrete things
in the world are the tick and the kick.

**Seats: `num_agents` = 2.** One seat = one full trio. Seat 0 is **Azure** (robots `AZ-1`, `AZ-2`,
`AZ-3`), defends the goal at x = −20 and attacks +x. Seat 1 is **Magenta** (`MG-1`, `MG-2`,
`MG-3`), defends x = +20 and attacks −x. The idea offered "6 or 2"; 2 is chosen because (a) the
motive is team zero-sum and with 2 seats the two seats' scores sum to exactly 1.0 with no
teammate-attribution problem, (b) both champions are LLM prompt policies and a 2-seat game puts
them head to head in every episode instead of scattering champions and fillers across the same
team, (c) the idea's own integrity note prefers the trio seat ("intra-team codebooks are
legitimate coordination"), and (d) 2 seats means 2 parallel LLM calls per decision turn instead
of 6, which is what makes the 720 s budget comfortable. The 6-seat hero-per-seat variant needs a
different `num_agents` and therefore goes to §Out of scope (v1).

**World.** Metres and seconds. Pitch interior x ∈ [−20, +20], y ∈ [−12.5, +12.5], origin at the
centre spot. Goal mouths are the segments x = ±20, |y| ≤ 3.5; behind each mouth is a 2 m-deep goal
box (|x| ≤ 22, |y| ≤ 3.5) closed by walls at x = ±22 and y = ±3.5. Everything else on the
boundary is a solid wall: the two touchlines y = ±12.5 and the goal-line segments x = ±20 with
|y| > 3.5. **There is no out of play** — no throw-ins, no corners, no offside. Goalposts are
static circles of radius 0.12 m centred at (±20, ±3.5). The penalty area of the goal at x = −20 is
{x ≤ −14, |y| ≤ 7} (mirrored at +20); it is used only for save attribution, it grants no special
powers.

**Bodies.** Six robots: radius 0.55 m, mass 6.0 kg, each with a position, a velocity, a unit
heading vector `h`, a scalar angular velocity ω, and a kick cooldown. One ball: radius 0.35 m,
mass 0.45 kg, position and velocity only (no spin, no Magnus). Robots are car-like: thrust acts
along `h`, lateral velocity is scrubbed off by grip, so *facing the right way is part of the
skill*.

**Time.** `dt = 1/30 s`; 30 ticks = 1 second of sim time. Each tick is integrated in **4 substeps
of `hs = 1/120 s`** so a 30 m/s ball moves at most 0.25 m per substep (< its 0.35 m radius) and
cannot tunnel. A full match is **7 200 ticks = 240 s = 4:00 of soccer**.

**Turns.** Play is divided into **48 decision turns of 150 ticks (5.0 s) each**. At the start of
turn *k* the server freezes the state at tick `k*150`, sends each seat its view, and collects one
**directive** per seat — a role, a target point, an intent and a kick policy for each of that
seat's three robots (§Server). A deterministic **control layer** then compiles that directive into
per-tick `(thrust, turn, kick)` triples for all 150 ticks of the turn. The LLM is the tactical
brain at 0.2 Hz; the control layer is the reflexes at 30 Hz.

### Resolution order (exact, per tick t)

Applied in this order, every tick, with no exceptions:

1. **Turn boundary.** If `t mod 150 == 0`, the directive collected for turn `t/150` becomes the
   active directive (see §Server for how it is collected and what happens if it is late).
2. **Freeze check.** If `t < freeze_until` (set to `goal_tick + 31` after a goal, i.e. a 1.0 s
   kickoff freeze), every robot's control is forced to `(0, 0, 0)`, all velocities and ω are held
   at 0, and steps 3, 5, 6 and 7 are skipped — the controls are still quantised and recorded
   (step 4), the keyframe is still written (step 9) and the turn boundary still fires (step 10).
   Physics resumes at `t == freeze_until`.
3. **Control compile.** For each robot in index order `AZ-1, AZ-2, AZ-3, MG-1, MG-2, MG-3`, the
   control layer reads the current world state and the active directive and produces
   `(u_thrust, u_turn, kick)` with `u_thrust, u_turn ∈ [−1, 1]` and `kick ∈ {0, 1}` (algorithm
   below).
4. **Quantise.** `u_thrust`, `u_turn` → `int8` = `round(clamp(u, −1, 1) * 100)`; `kick` → `uint8`
   0/1. The quantised bytes are what the sim consumes and what the replay records — the sim never
   sees an un-quantised control. (This is the determinism boundary; see §Sim module.)
5. **Kicks.** In robot index order, for each robot with `kick == 1` and `cooldown == 0` and
   `|b − x| ≤ 0.55 + 0.35 + 0.45 = 1.35` and `dot(h, unit(b − x)) ≥ 0.5`: let `n = h`,
   `v∥ = dot(v_ball, n)`, `v⊥ = v_ball − v∥·n`; set `v∥' = max(v∥, 0) + 9.0`; set
   `v_ball = 0.5·v⊥ + v∥'·n`, clamped to |v_ball| ≤ 30; apply the reaction
   `v_robot −= n · (0.45 · (v∥' − v∥) / 6.0)`; set `cooldown = 12` ticks. Emit a `kick` event.
   Each kick sees the ball state left by the previous kick in the same tick.
6. **Substeps ×4** (`hs = 1/120 s`; `h` always means the robot's unit heading vector), each
   substep in this order:
   1. *Robot integration*, per robot in index order:
      `ω ← clamp(ω + (24.0·u_turn − 6.0·ω)·hs, −6.0, 6.0)`;
      `δ = ω·hs`; `h' = (hx − δ·hy, hy + δ·hx)`; `h ← h'/|h'|` (first-order rotation +
      renormalisation — deliberately defined this way, see §Sim module: it uses only `+ − × ÷ √`);
      `a = 18.0·u_thrust·h − 8.0·(v − dot(v,h)·h)`;
      `v ← v + a·hs`; `v ← v·(1 − 1.2·hs)`; if `|v| > 7.0` then `v ← v·7.0/|v|`;
      `x ← x + v·hs`.
   2. *Ball integration*: `v_ball ← v_ball·(1 − 0.6·hs)`; if `|v_ball| > 30` scale to 30;
      `b ← b + v_ball·hs`.
   3. *Robot–wall*: for each robot in index order, clamp the centre inside the arena polygon and
      reflect the normal velocity component with restitution 0.25.
   4. *Robot–robot*: for each unordered pair in ascending index order `(0,1),(0,2),…,(4,5)`, if
      `|xi − xj| < 1.10`, separate each by half the penetration along the normal and apply an
      equal-and-opposite normal impulse with restitution 0.35 (equal masses).
   5. *Robot–ball*: for each robot in index order, if `|b − x| < 0.90`, separate along the normal
      in inverse-mass proportion and apply a normal impulse with restitution 0.55 and masses
      (6.0, 0.45); multiply the ball's tangential relative velocity by 0.80 (dribble friction).
      Record the toucher: `last_touch_robot`, `last_touch_seat`, `last_touch_tick`.
   6. *Ball–post*: for each of the four posts, circle-circle against a static body with restitution
      0.70; on contact emit a `post` event.
   7. *Ball–wall*: reflect with restitution 0.80 and tangential factor 0.98.
   8. *Goal test*: a goal is scored the moment the ball **centre** satisfies `b.x ≤ −20 and
      |b.y| ≤ 3.5` (Magenta scores) or `b.x ≥ +20 and |b.y| ≤ 3.5` (Azure scores). On a goal:
      stop the remaining substeps of this tick, increment the scorer's goal count, emit a `goal`
      event (with `scorer` = `last_touch_robot`, `assist` = the previous distinct-robot same-seat
      toucher within 120 ticks or `null`, `ball_speed`, `score_after`), then perform the **kickoff
      reset** and set `freeze_until = t + 31` (the rest of tick `t` plus 30 frozen ticks).
7. **Cooldowns.** Every robot with `cooldown > 0` decrements it by 1.
8. **Stats.** `possession_ticks[last_touch_seat] += 1` (no increment before the first touch);
   `distance_m[robot] += |Δx|` for this tick; shot/save bookkeeping (below).
9. **Keyframe.** If `t mod 30 == 0`, append a keyframe: tick, ball `(x, y)`, each robot
   `(x, y, hx, hy)` rounded to 0.001, and the u32 state digest (§Sim module).
10. **Turn end.** If `(t + 1) mod 150 == 0`: emit `turn_end`; if `|goals[0] − goals[1]| ≥ 5`, end
    the match (`end_rule = mercy`); if `t + 1 ≥ max_ticks`, end the match (`end_rule = full_time`).

**Kickoff reset (exact).** Ball at (0, 0), `v_ball = 0`. All ω = 0, all velocities 0, all cooldowns
0. Azure headings `(1, 0)`, Magenta headings `(−1, 0)`. The **restarting** seat (the conceding one;
at match start, seat `seed & 1`) places its first robot at `(∓1.5, 0)` — 1.5 m from the ball on its
own side — and the other seat's first robot at `(±3.0, 0)`. The remaining robots go to
`(∓9.0, +4.5 + j1)` and `(∓9.0, −4.5 + j2)` for the restarting seat and `(±9.0, +4.5 + j3)`,
`(±9.0, −4.5 + j4)` for the other, where each `j` is drawn from the episode's PCG32 stream as
`(next_u32() / 2^32) * 0.5 − 0.25` (±0.25 m of deterministic y-jitter so kickoffs are not
identical). Emit a `kickoff` event with `restart_for_seat`.

**Shots and saves.** A `kick` whose post-kick ball velocity ray reaches the opponent goal plane
inside the mouth — `t* = (x_goal − b.x)/v.x > 0` and `|b.y + v.y·t*| ≤ 3.5` — is a **shot on
target** (`shot` event, `on_target: true`); other kicks toward the opponent half with
`|b.y + v.y·t*| ≤ 8.0` are shots off target. A shot on target whose next ball touch is by a
defending robot inside its own penalty area, before any goal, is a **save** (`save` event,
credited to that robot). A `kick` with `intent: "pass"` whose next touch is a different robot of
the same seat within 120 ticks is a **completed pass** (`pass_completed`); if the next touch is an
opponent it is an **interception** (`interception`).

### Scoring, sign, and what the league ranks by

Team zero-sum, margin-sensitive, and the two seats' scores always sum to exactly 1.0:

```
gd(seat)    = goals[seat] − goals[1 − seat]
score(seat) = 0.5 + 0.5 · clamp(gd(seat) / 3, −1, +1)
```

**Higher is better.** 3–0 or better = 1.000; 2–0 = 0.833; 1–0 = 0.667; a draw of any scoreline =
0.500; 0–1 = 0.333; 0–3 or worse = 0.000. `score(0) + score(1) == 1.0` for every legal outcome, so
the game is exactly zero-sum. `win[seat] = gd(seat) > 0`. **The league ranks by Elo computed from
`results.scores`** (the platform's `scores` array is the only cross-game ranking input; Elo 1000
start, K 32, per the league settings in phase 50). A `fault` episode scores 0.5/0.5 — an infra
fault is nobody's loss.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.end_rule` carries the detail.

| `reason` | `end_rule` | When |
|---|---|---|
| `complete` | `full_time` | 7 200 ticks (or the variant's `max_ticks`) played. The normal ending. |
| `complete` | `mercy` | Goal difference ≥ 5 at a turn boundary. The rules ended the match; still a complete game. |
| `deadline` | `wall_clock` | The engine's `wall_clock_budget_seconds` (default 690 s) elapsed before full time. The score at that instant stands and is scored with the same formula. **This is declared acceptable** for phase-60 verification: it means the hosted LLM was slow, not that the game broke, and the replay is complete up to the stop tick. |
| `fault` | `sim_fault` | The wasm sim trapped or a physics invariant guard tripped. Scores 0.5/0.5, `winner: null`, partial replay written. |
| `fault` | `host_error` | An unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

A seat that never connects does **not** end the episode: its robots are driven by the `formation`
scripted baseline for the whole match, the no-show is reported to `COGAME_PLAYER_FAILURE_URI`
(lowest slot only, moba's rule), and the match plays to `full_time`.

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {formation, swarm}` makes it a scripted seat. A seat that sets neither defaults to
`PLAYER_SCRIPTED=formation`. A scripted policy seated as a champion is a failure state.

**Where the decision happens.** *Deviation from moba, deliberate:* moba's players decide inside
their own container. In cogball the **game server** owns the LLM client, exactly as the
parley/babel lineage does (`cogame-babel/src/babel/llm.nim`). Reasons: the hosted Bedrock sidecar
credential and the `anthropic_api_key` coworld secret are injected into the *game* pod; phase 60
greps the *game* log for `falling back` / `LLM provider is unavailable`; the "one parallel batch
per turn" pin is a game-server property; `templates/tools/ci/docker_smoke.sh` forwards
`ANTHROPIC_API_KEY` to the game container; and keeping the scripted layer inside the server makes
the recorded action log reproducible with no network in the loop. The player container is
therefore thin: it connects, sends one handshake frame carrying its prompt (or its baseline name),
and then only receives.

**Cadence and batching.** One decision turn every **150 ticks (5.0 s of sim time)**, 48 turns per
match. At each turn the server builds both seats' request bodies and issues them as **one parallel
batch**: a single `asyncio.gather(call(seat0), call(seat1))` wrapped in one
`asyncio.wait_for(..., turn_budget_seconds)`. Seats are never queried sequentially. Each seat costs
exactly **one** LLM call per turn covering all three of its robots, so the whole episode is
2 × 48 = 96 calls, at most 2 in flight at once.

**Wall-clock arithmetic (must stay inside 60 % of `episodeTimeoutSeconds` 1200 = 720 s):**

```
48 turns × 12.0 s per-turn budget           = 576 s
player connect wait (both seats, typical)   =  20 s   (cap: player_connect_timeout_seconds 90)
physics: 7200 ticks × 4 substeps, wasmtime  =   3 s   (perf test bounds this at ≤ 20 s)
results + replay writes (retrying uploader) =  30 s
                                            -------
expected total                              = 629 s   < 720 s  (91 s margin)
engine hard stop wall_clock_budget_seconds  = 690 s   → reason "deadline"
platform kill (manifest 20 min)             = 1200 s
```

**Per-turn timing, per seat:** first LLM attempt deadline **8.0 s**. On timeout, transport error,
non-JSON reply, or a reply that carries no usable robot entry → **one retry** with a 3.5 s
deadline. If that also fails → the seat's directive for this turn is the **`formation` scripted
directive**, computed in microseconds, and a `fallback` event is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. Worst case
8.0 + 3.5 = 11.5 s ≤ the 12.0 s turn budget. With no credentials at all the client is disabled on
first discovery and every turn falls back instantly with no network wait (offline certification
completes in seconds).

**Budget guard (early settle without shortening the match).** At the start of each turn, if
`elapsed + 2 × turn_budget > wall_clock_budget_seconds`, the LLM is skipped for all remaining
turns and the match finishes on the scripted layer (< 1 s per turn), so the episode ends
`complete/full_time` rather than `deadline`. A `budget_guard` event records the turn it kicked in.
Only if even that overruns (it cannot, arithmetically, but the check is unconditional) does the
engine stop at 690 s with `deadline`.

**Degrade, never hang.** Every wait is bounded: LLM attempt deadlines above, one outer
`wait_for` per turn, `player_connect_timeout_seconds` on the connect wait, moba's per-seat
`DONE_SEND_TIMEOUT_SECONDS = 3.0` on the final broadcast, and the 690 s engine stop. A seat that
disconnects mid-match keeps playing: its directive source degrades to `formation` and the seat
revives on reconnect (moba's strike rule, kept, with `STRIKE_LIMIT = 3` *turns* instead of ticks
since turns are the unit here). No failure mode leaves a robot unactuated — the control layer
always has a directive, defaulting to the previous turn's, then to `formation`.

**The LLM client** (`server/cogball/llm.py`) copies babel's credential ladder verbatim in order:
Bedrock sidecar (endpoint + bearer token from the pod env) → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI` → none (disabled, instant fallback). Model candidates in order:
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, `us.anthropic.claude-sonnet-4-6`,
`us.anthropic.claude-sonnet-4-5-20250929-v1:0`; `BEDROCK_MODEL` pins one.
`maxOutputTokens = 900` (400 truncates — playbook gotcha). **No `output_config.effort`** (Haiku 4.5
rejects it). `temperature = 0.4`.

**System prompt (fixed, identical for both champions, sent as the system message):**

```
You are the coach of a three-robot soccer team in a continuous 2D physics world.
Every 5 seconds of match time you issue ONE directive for all three of your robots.
A deterministic controller executes your directive for the next 5 seconds: it steers
each robot toward its target, turns it to face where it is going, and kicks when the
ball is in range and the intent allows it. You do not control motors directly.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars","robots":[
  {"id":"<one of your three robot ids>",
   "role":"keeper|back|wing|striker",
   "intent":"chase|intercept|hold|shoot|pass|clear|press",
   "target":[x,y],            // metres, pitch is x in [-20,20], y in [-12.5,12.5]
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

**User message** = the seat's `PLAYER_PROMPT` text, then a blank line, then the seat's view JSON
(§Server). The prompt text is never echoed into the replay (only `policy_kind`).

**Champion #1 — `cogball-total` (owner daveey), `PLAYER_PROMPT`:**

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
"pass" to your support robot over a low-percentage shot from outside 12 metres. If you
are two goals up, drop the support robot to "back" and hold the middle.
```

**Champion #2 — `cogball-counter` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`:**

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
past the halfway line.
```

### The control layer (deterministic; shared by every policy)

Both LLM directives and scripted directives are compiled by the *same* code, so the two policy
kinds are strictly comparable. For each robot each tick:

1. **Steering point `p*`** by intent (`b` = ball position, `v_b` = ball velocity, `x` = robot
   position, `G` = opponent goal centre `(±20, 0)`, `Gown` = own goal centre):
   - `chase`: `p* = b`.
   - `intercept`: `τ = clamp(|b − x| / (7.0 + |v_b|), 0, 1.5)`; `p* = b + v_b·τ`.
   - `hold`: `p* = directive.target`.
   - `shoot`: `p* = b − unit(G − b)·0.90`.
   - `pass`: `p* = b − unit(T − b)·0.90` where `T` = `pass_to`'s position + its velocity × 0.5
     (falls back to `shoot` if `pass_to` is missing or is the robot itself).
   - `clear`: `p* = b − unit(C − b)·0.90` where `C = (0, sign(b.y)·10.0)` — up the touchline away
     from own goal; if `|b.y| < 0.5`, `C = (0, 10.0)`.
   - `press`: `p* = o + v_o·0.5` for the opponent `o` nearest the ball.
   - All intents except `hold` blend the directive target as a 20 % bias:
     `p* ← 0.8·p* + 0.2·target`. `target` is clamped into the pitch on parse.
2. **Turn command.** `d = p* − x`; if `|d| < 1e−6`, `u_turn = 0`; else `d̂ = d/|d|`,
   `s = hx·d̂y − hy·d̂x`, `c = hx·d̂x + hy·d̂y`; `u_turn = clamp(3.0·s, −1, 1)` when `c ≥ 0`,
   otherwise `u_turn = (s ≥ 0 ? 1 : −1)` (turn the short way through the back hemisphere). No
   `atan2`.
3. **Thrust.** `u_thrust = clamp(c, 0, 1) · min(1, |d| / 1.0)`; if `|d| < 0.25` and
   `dot(v, d̂) > 0.5` then `u_thrust = −0.3` (brake onto the spot). `hold` robots additionally face
   the ball instead of `p*` once `|d| < 0.4` (recompute step 2 with `d = b − x`).
4. **Kick.** `kick = 1` iff `directive.kick == "auto"` **and** `cooldown == 0` **and**
   `|b − x| ≤ 1.35` **and** `dot(h, unit(b − x)) ≥ 0.5` **and** the intent is not `hold` or
   `press` with the ball behind the robot relative to the target. `kick == "never"` forces 0.

**Scripted baselines** (both emit the *same* directive JSON on the same 5 s cadence, so their
output is legal by construction and directly comparable to an LLM's):

- **`formation`** (the certification player and the default): compute each robot's distance to the
  ball. The robot **nearest its own goal** (smallest `|x − x_own_goal|`, ties broken by ascending
  robot index) is `keeper`, intent
  `hold`, target `(x_own_goal + 3.0·attack_dir, clamp(b.y/3, −2.6, 2.6))`. The nearest to the ball
  (excluding the keeper) is
  `striker`, intent `shoot` if the ball is in the opponent half or within 6 m, else `chase`. The
  third is `back` if the ball is in the own half (intent `hold`, target = midpoint of ball and own
  goal, pulled 1.5 m to the far y-side) and `wing` otherwise (intent `intercept`, target
  `(b.x + 7·attack_dir, −sign(b.y)·5)`). `clear` overrides the striker's intent when the ball is
  inside its own penalty area. `kick: "auto"` for all, `note`/`say` are fixed short strings.
- **`swarm`** (the second filler, deliberately weaker and different in shape): all three robots get
  intent `chase` with `kick: "auto"`, targets at the ball, except the robot nearest its own goal
  which gets `hold` at the goal arc **only** when the ball is inside its own half. Roles reported
  as `striker`/`striker`/`back`. This is the "everyone chases" baseline; it loses to `formation`
  and gives the ladder a spread.

Both are pure functions of the world state (no randomness), which is what makes the
bounded-orders test in §Tests meaningful.

## Sim module

**Decision: a purpose-written deterministic physics core, not vendored Box2D.** The idea proposed
Box2D-to-wasm; that is rejected, and here is the reason, which is the single most load-bearing
choice in this note. **Replays re-simulate from seed + action log, so the physics must be
bit-identical between the server build (wasmtime, standalone/WASI wasm) and the viewer build
(emscripten, browser wasm).** WebAssembly guarantees exact IEEE-754 results for `f64.add`,
`sub`, `mul`, `div`, `sqrt`, `min`, `max` and comparisons, and forbids fused/contracted forms — so
any physics written with *only those operations* is bit-identical across the two toolchains by
specification. What is **not** guaranteed is libm: `sinf`, `cosf`, `atan2f`, `powf` are library
code, and emscripten's musl and the WASI SDK's musl are different builds at different versions.
Box2D's rotation, joints and solver are built on exactly those transcendentals (and on float32
accumulation orders that change with optimisation level), so vendoring it would make the
determinism guarantee depend on two toolchains agreeing about `sinf` — untestable in the sandbox
and unfixable if it drifts. A 3v3 soccer world needs only circle-circle and circle-wall contacts:
~400 lines of C. So:

- **`sim/cogball_core.c` + `sim/cogball_core.h`** — the whole physics world, written in C99,
  `double` throughout, using **only `+ − × ÷ √`, comparisons and integer ops**. Explicitly banned
  and enforced by a test (§Tests): `sin cos tan asin acos atan atan2 exp log pow fmod hypot` and
  any `float`-typed accumulation. Heading rotation is defined as first-order rotate +
  renormalise (§The game, step 6.1) — that is the *definition* of the sim's rotation, not an
  approximation of a trig call, so there is nothing to drift. `-ffast-math` is banned in both
  build scripts and the ban is grepped in CI.
- **Randomness**: one PCG32 stream seeded from the u32 episode seed; used only for kickoff
  y-jitter. Integer arithmetic only.
- **State digest**: `cogball_state_digest()` returns an FNV-1a u32 over the raw bytes of ball
  position/velocity and every robot's position/velocity/heading/ω/cooldown, plus the score and
  tick. It is the cross-build equality check (moba's `state_digest` idea, kept, widened to the
  full state).
- **Exports** (WASI reactor, `--no-entry`, mirroring moba's `sim/shim.c`):
  `cogball_init(u32 seed, u32 first_kickoff_seat)`, `ctl_ptr()` (6×3 byte control buffer),
  `cogball_step()` (one tick = the 4 substeps and everything in the resolution order),
  `cogball_tick()`, `cogball_goals(seat)`, `cogball_state_ptr()` (packed doubles for the host to
  read: ball + 6 robots), `cogball_event_count()` / `cogball_event_ptr()` (a fixed-capacity ring of
  packed per-tick physics events — kick, touch, post, goal, kickoff — drained by the host each
  tick), `cogball_state_digest()`, `cogball_fault()`.
- **Host**: `server/cogball/sim.py`, a straight fork of moba's `server/cogame_moba/sim.py` —
  `wasmtime` `Engine`/`Module` cached per path, WASI stdout/stderr inherited, `_initialize()`
  called before anything, memory read/write for the control and state buffers. Default wasm path
  `build/cogball_sim.wasm`.
- **Builds** (three artefacts from one source, moba's script layout kept):
  - `sim/build_sim.sh` → `build/cogball_sim.wasm` (emscripten `STANDALONE_WASM --no-entry`, `-O2`,
    no `-ffast-math`), the module `wasmtime` hosts.
  - `sim/build_viewer.sh` → `viewer/dist/cogball_viewer.{js,wasm}` (render build, `-DCOGBALL_RENDER`,
    raylib 5.5 web — **same pinned URL and sha256 `798b6bea650e78a60fe49f106a15d92ea4e33efd3aa1b3efa34b0438a14bbf2c` as the starter**, same
    `MEM_FLAGS`/cache-stamp logic, `-sENVIRONMENT=web`) plus `build/viewer_core.js|wasm`
    (headless `-sENVIRONMENT=node -sMODULARIZE=1 -sEXPORT_NAME=createViewerCore`) for the
    node determinism/viewer tests. `sim/viewer_main.c` wraps `cogball_core.c` with the replay
    loader, the transport state machine (play/pause/seek/speed — moba's `viewer_*` export set kept
    name-for-name) and, under `-DCOGBALL_RENDER`, the raylib renderer.
  - `sim/build_sim.sh` also writes `build/sim_sha.js` equivalent: `sim/build_viewer.sh` embeds the
    sha of `build/cogball_sim.wasm` into `viewer/dist/sim_sha.js` exactly as moba does, and the
    viewer warns on screen when a replay's `sim_core_sha256` differs.
- **The control layer lives in Python** (`server/cogball/control.py`), not in C. It is *not* part
  of the determinism boundary because its output is quantised to bytes (§The game, step 4) before
  it reaches the sim, and those bytes are what the replay stores. The viewer therefore never runs
  the control layer at all — it feeds recorded bytes to the identical physics core. This removes
  the entire class of "the control layer was reimplemented in the viewer and drifted" bugs, and it
  is why the action log is the replay's ground truth.
- Perf target: ≥ 5 000 ticks/s in wasmtime (a full match ≈ 1.5 s of CPU). Tested with a generous
  20 s bound.

Physics constants live in one place, `sim/cogball_config.h`, shared by the sim build and the viewer
build so they can never drift (moba's `sim/shim_common.h` rule). Server-contract defaults
(`max_ticks`, `turn_ticks`, deadlines, seat topology) live in `server/cogball/defaults.py`.

## Server, player, protocol

`server/cogball/server.py` is a fork of moba's `server.py`: same aiohttp app, same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, and in replay mode `GET /replay-data` + `GET /client/replay`), same
`COGAME_*` runtime contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_HOST`/`COGAME_PORT`), same 403 on a
bad slot/token and 409 on a duplicate connection, same `PLAYER_WS_HEARTBEAT_SECONDS = 20`, same
done-broadcast-before-artifact-writes ordering, same player-failure reporting.
`server/cogball/uris.py` is copied verbatim (package rename only).
`server/cogball/engine.py` is moba's `LockstepEngine` reshaped from ticks to turns.

**Player handshake (the only thing a player container must do).** On connect the player sends
exactly one frame:

```json
{"type": "register", "prompt": "<strategy text or empty>", "scripted": "formation"|"swarm"|null,
 "policy": "<free label, <=48 runes>"}
```

`players/cogball_player.py` reads `COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and
`PLAYER_POLICY_LABEL`, sends that frame, then receives until `{"done": true, ...}`. A seat that
never registers, or registers with neither field, is treated as `scripted: "formation"`.

**Per turn the server pushes to each seat** (informational — the seat is not required to answer;
decisions are made server-side, see §Decisions):

```json
{"type": "turn", "turn": 7, "tick": 1050, "view": { … }, "directive_source": "llm"}
```

and at the end `{"done": true, "result": { …results doc… }}` followed by close.

### The per-seat view (exactly what is visible, and what is hidden)

Numbers are rounded to 2 decimals. This object is both the `view` in the turn frame and the tail of
the LLM user message.

```json
{"turn": 7, "of": 48, "clock": {"played_s": 35.0, "left_s": 205.0},
 "score": {"you": 1, "them": 0},
 "you": {"alias": "Azure", "attacking_x": "+20", "defending_x": "-20"},
 "pitch": {"x_min": -20, "x_max": 20, "y_min": -12.5, "y_max": 12.5,
           "goal_half_width": 3.5, "your_penalty_area": "x <= -14, |y| <= 7"},
 "ball": {"pos": [3.21, -1.04], "vel": [4.10, 0.62], "speed": 4.15,
          "possession": "AZ-2" | "MG-1" | "loose", "in_your_half": false},
 "your_robots": [{"id": "AZ-1", "pos": [-16.9, 0.4], "vel": [0.2, -0.1],
                  "facing": [1.0, 0.0], "speed": 0.22, "kick_ready": true,
                  "dist_to_ball": 20.1, "last_role": "keeper"}, … 3 …],
 "their_robots": [{"id": "MG-1", "pos": [7.7, 2.1], "vel": [-3.0, 0.4],
                   "facing": [-0.99, 0.13], "speed": 3.03,
                   "dist_to_ball": 5.6}, … 3 …],
 "last_turn": {"your_kicks": 2, "their_kicks": 1, "your_shots": 1, "their_shots": 0,
               "goals": [{"tick": 890, "by": "AZ-3", "for": "you"}],
               "possession_pct_you": 63},
 "your_last_directive": { …the directive played by your seat last turn, or null on turn 0… }}
```

**Visible:** the complete physical state of the world (soccer is a perfect-information sport), the
score, the clock, the turn index, the seat's own previous directive, and last-turn event counts.
**Hidden:** the opponent's directives, roles, intents, `note`/`say` text and prompt (never shown,
not even after the fact); the episode seed; real player names (the seat sees only `Azure` /
`Magenta` and robot ids); anything about the opponent's policy kind; and future ticks. Spectators
see all of it in the replay — that asymmetry is the two-name-space pin.

### Reply schema and character caps

The LLM must return this object (the scripted baselines produce the identical shape):

```json
{"note": "compact, keeper stays home",
 "robots": [{"id": "AZ-1", "role": "keeper", "intent": "hold", "target": [-17.0, 0.4],
             "pass_to": null, "kick": "auto", "say": "holding the arc"}, … 3 … ]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes |
| `robots` | array | exactly the seat's 3 robots | extra entries dropped; missing ids filled from last turn's directive for that robot, else from `formation` |
| `robots[].id` | string | `AZ-1..3` / `MG-1..3`, case-insensitive, **≤ 8 runes** | unmatched entries assigned to the seat's robots by position |
| `robots[].role` | enum | `keeper` `back` `wing` `striker` | → `wing` |
| `robots[].intent` | enum | `chase` `intercept` `hold` `shoot` `pass` `clear` `press` | → `chase` |
| `robots[].target` | [num, num] | finite; clamped to x ∈ [−20, 20], y ∈ [−12.5, 12.5] | non-finite/missing → the robot's current position |
| `robots[].pass_to` | string/null | a *teammate* id ≠ self | → `null` (and `pass` degrades to `shoot`) |
| `robots[].kick` | enum | `auto` `never` | → `auto` |
| `robots[].say` | string | **≤ 48 runes** | truncated to 48 runes |

Two further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, and any
recorded error text (`fallback.detail`) **≤ 200 runes**. `register.prompt` is capped at
**≤ 4 000 runes** at the transport (an over-long prompt is truncated, not rejected) and is never
written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Python this means
slicing the decoded `str` (`s[:160]`) and only then encoding; slicing `bytes` is forbidden
anywhere on the path to the replay. A byte-truncated multi-byte character is exactly the bug that
makes replay bytes render in a browser but fail a strict JSON parser (playbook gotcha), and
§Tests pins it with a 4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences, take the outermost balanced `{…}` if the model
prefixed prose, accept `robots` as an object keyed by id, accept numeric strings for `target`.
Only if no object with at least one usable robot entry can be recovered does the retry, then the
fallback, fire.

### Results document (closed schema — must equal the manifest `results_schema` key-for-key)

```json
{"names": ["daveey", "daveey-1"],
 "aliases": ["Azure", "Magenta"],
 "policy_kinds": ["llm", "scripted"],
 "scores": [0.667, 0.333],
 "win": [true, false],
 "goals": [1, 0],
 "reason": "complete",
 "end_rule": "full_time",
 "winner": 0,
 "final_tick": 7200,
 "final_turn": 48,
 "seed": 2864434397,
 "shots": [7, 4],
 "shots_on_target": [3, 1],
 "saves": [1, 3],
 "passes_completed": [9, 5],
 "interceptions": [4, 6],
 "possession_ticks": [4120, 3080],
 "distance_m": [211.4, 340.2, 298.7, 205.9, 318.0, 331.6],
 "llm_turns": [48, 0],
 "fallback_turns": [0, 0],
 "fallback_causes": [{"timeout": 0, "parse_error": 0, "transport_error": 0,
                      "no_credentials": 0, "budget_guard": 0}, {...}]}
```

`winner` is `0`, `1`, or `null` (draw). Adding or removing a key here means editing
`coworld_manifest_template.json`'s `results_schema` and `tools/ci/docker_smoke.sh`'s expectations
in the same commit (moba's triple-sync rule, kept).

### Replay bytes (self-sufficient, strict UTF-8 JSON)

*Deviation from moba, deliberate:* moba writes a binary `MOBA`-magic file. cogball writes **UTF-8
JSON**, because SPEC §Definition of done check 4 fetches the replay from S3 and requires valid
UTF-8 JSON with a matching `protocol` and a `results.reason`, and the shared
`tools/ci/docker_smoke.sh` defaults to `SMOKE_REQUIRE_REPLAY_JSON=1`. The bulk payload (the action
log) rides as one base64 string, so the file stays small and parseable.

```json
{"protocol": "cogball/v1",
 "format_version": 1,
 "sim_core_sha256": "<sha256 of build/cogball_sim.wasm>",
 "seed": 2864434397,
 "first_kickoff_seat": 1,
 "config": { …fully resolved game config, tokens excluded: max_ticks, turn_ticks,
             turn_budget_seconds, tick_deadline_ms, wall_clock_budget_seconds,
             player_connect_timeout_seconds, players:[{"name":…}] … },
 "names": {"players": ["daveey", "daveey-1"],
           "aliases": ["Azure", "Magenta"],
           "policy_kinds": ["llm", "scripted"],
           "robots": [{"id": "AZ-1", "seat": 0, "hue": 196}, … 6 …]},
 "ticks_per_second": 30, "turn_ticks": 150, "tick_count": 7200,
 "controls_b64": "<base64 of tick_count × 6 × 3 bytes: (thrust i8, turn i8, kick u8) per robot>",
 "keyframes": [{"t": 0, "d": 2947483111, "b": [0.0, 0.0],
                "r": [[-1.5, 0.0, 1.0, 0.0], … 6 …]}, … every 30 ticks …],
 "events": [ … see the vocabulary below … ],
 "results": { …the results document verbatim… }}
```

`seed` + `first_kickoff_seat` + `controls_b64` + the pinned physics core reproduce the episode
exactly; `keyframes` carry the per-30-tick state digest `d` so the viewer (and the tests, and a
human reading the JSON) can verify the re-simulation and see the game without running wasm at all.
Size: 7 200 × 18 B → 173 KB of base64, 240 keyframes ≈ 55 KB, events ≈ 60 KB — well under 400 KB.

**Event vocabulary** (every record has `t` = tick; `turn` where meaningful):

| `type` | Fields |
|---|---|
| `match_start` | `t`, `kickoff_seat`, `aliases` |
| `turn_start` | `t`, `turn`, `score`, `possession` |
| `directive` | `t`, `turn`, `seat`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note`, `robots`:[{`id`,`role`,`intent`,`target`,`pass_to`,`kick`,`say`}] |
| `fallback` | `t`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤200 runes) |
| `budget_guard` | `t`, `turn`, `remaining_s` |
| `kick` | `t`, `robot`, `seat`, `pos`, `intent`, `ball_speed_after` |
| `touch` | `t`, `robot`, `seat` (emitted at most once per robot per 6 ticks, to bound volume) |
| `shot` | `t`, `robot`, `seat`, `on_target`, `predicted_y` |
| `save` | `t`, `robot`, `seat`, `shot_tick` |
| `pass_completed` | `t`, `from`, `to`, `seat`, `kick_tick` |
| `interception` | `t`, `robot`, `seat`, `kick_tick` |
| `post` | `t`, `post` (`[±20, ±3.5]`) |
| `goal` | `t`, `turn`, `seat`, `scorer`, `assist`, `ball_speed`, `score_after` |
| `kickoff` | `t`, `restart_for_seat` |
| `turn_end` | `t`, `turn`, `score` |
| `end` | `t`, `reason`, `end_rule`, `score` |

`directive`, `goal`, `save`, `pass_completed` and `fallback` are the records the phase-60 verifier
reads to judge "the champion seats doing the thing the game is about": a champion seat's
`directive` events must carry `source: "llm"` with real `note`/`intent` content, not all
fallbacks.

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` (copied from
moba verbatim apart from the image tag string, `chmod +x`, invoked by `coworld build` with the
absolute bundle directory) builds the Dockerfile's `wasm-builder` stage and copies
`/src/viewer/dist/.` into it. The game server still serves `/client/replay` for local viewing, and
`sim/build_viewer.sh` produces the same `viewer/dist` the bundle ships. Nothing but S3 is
contacted at view time.

**Files.**

- `viewer/index.html` — moba's chrome **verbatim**: the `:root { color-scheme: dark }` /
  `body` / `header` / `#stage` / `canvas` / `#status` / `#controls` / `button, select` / `#seek` /
  `#tickinfo` / `#endcard` / `#warn` CSS block and the corresponding markup (canvas in `#stage`,
  the play/pause button, the 1x/4x/16x/64x speed select, the range scrubber, the tick readout, the
  endcard, the sim-sha warning line). Added markup: `#scorebug`, `#feed`, `#heat` toggle button,
  `#goalbanner`.
- `viewer/static_replay.js` — the shell. **The `tell()` host bridge is copied verbatim from
  `cogame-babel/replay-viewer/static_replay.js`**, including `tell("loading")` on script entry,
  `tell("error", …)` on failure, and `tell("ready")` fired inside a double
  `requestAnimationFrame` after the first drawn frame — SPEC §Definition of done check 8(c) greps
  the served JS for exactly that bridge. The shell reads `?replay=<url>` (falling back to
  `/replay-data` for local mode), fetches with a 20 s `AbortController` timeout and a Retry
  button, parses the JSON, hands `controls_b64` + `seed` to the wasm core, verifies
  `sim_core_sha256`, and drives the transport.
- `viewer/dist/cogball_viewer.{js,wasm}` + `viewer/dist/sim_sha.js` — the raylib render build.
- No `--preload-file` data blob: see "art" below. Bundle assets are therefore exactly
  `index.html`, `static_replay.js`, `sim_sha.js`, `cogball_viewer.js`, `cogball_viewer.wasm`
  (each must return 200 with non-trivial size for phase-60 check 8(b)).

**Split of responsibilities.** The wasm canvas draws the world (pitch, robots, ball, trails, FX);
the DOM chrome draws the scorebug, clock, event feed, transport bar and warnings. Text in DOM is
set with `textContent` only (names are player-controlled data) and stays crisp at any zoom — this
is what makes 360 px legibility achievable.

**Readouts.**

1. **Score bug** (top-left overlay, always on): `▮ daveey 2 — 1 daveey-1 ▮` with the two team
   colour chips, plus `02:15 / 04:00` sim clock and a possession dot. Real player names here
   (spectator side); the pitch labels show aliases/robot ids only.
2. **Clock**: `MM:SS / MM:SS` from `tick / 30`, plus `turn 22/48`.
3. **Event feed**: the last 6 events rendered in plain language — "AZ-2 shoots — saved by MG-1",
   "GOAL Azure — AZ-3 (assist AZ-1), 14.2 m/s", "Azure coach: keep MG-3 pinned wide". Directive
   `note`/`say` strings appear here; this is where a spectator sees the LLM playing.
4. **Ball trail**: the last 45 tick positions as a tapering ribbon (6 px → 1 px), tinted by the
   last toucher's team colour.
5. **Kick FX**: on every `kick` event, an expanding ring at the contact point (0.35 m → 1.6 m over
   12 frames) plus a one-frame white flash on the ball.
6. **Goal celebration**: on a `goal`, a full-canvas flash, 120 particle fireworks in the scoring
   team's colour for 45 frames, and a `GOAL!` banner over the scorebug.
7. **Instant slow-mo goal replay**: when playback reaches a `goal` tick for the first time, the
   shell pauses 0.5 s, seeks back 90 ticks, replays those 3 seconds at 0.25× with a "GOAL REPLAY"
   banner and a vignette, then seeks forward to the goal tick and resumes at the previous speed.
   Implemented purely with the existing `viewer_seek` / `viewer_set_speed` exports; each goal
   replays once (a `seen` set), and any manual scrub cancels it.
8. **Position-history tinting**: each robot has its own hue (Azure 190/202/214, Magenta 330/342/354)
   and accumulates a persistent low-alpha heat trail of every position it has occupied, drawn under
   the bodies. Over four minutes the keeper's arc, the back's shuttle and the striker's runs
   separate visually — roles emerging with no labels, exactly as the idea asks. Toggle button
   `heat` (default on).
9. **Transport**: moba's play/pause, 1x/4x/16x/64x, scrubber (re-simulates from tick 0 on release,
   using the recorded keyframe digests to assert it landed correctly), tick readout, endcard
   ("Azure wins 2–1 (full_time)"), and the sim-sha mismatch warning line.

**Art is real, not placeholder.** Everything is drawn with raylib primitives at high quality: mown
turf bands (two greens, 2.5 m pitch stripes), painted white lines (touchlines, halfway line, centre
circle r = 3 m, penalty areas, goal arcs) with 0.12 m stroke, goal nets as hatched quads with
depth, robots as bevelled discs with a livery ring, a heading wedge, a drop shadow and a small
alias caption, the ball as a shaded sphere with a rolling seam, and a dark vignette surround
matching the starter's `#0b1414`. No solid-colour rectangles standing in for anything, no TODO
assets, no downloaded art (which also keeps the bundle to five files and the build hermetic).

**Legible at 360 px** — the embedded featured-match iframe is ~360 px wide, so this is checked at
360 px, not at desktop width: the canvas is `max-width: 100vw; height: auto`; the scorebug uses
`font-size: clamp(10px, 3.2vw, 15px)`; `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow:
hidden; text-overflow: ellipsis; }` so names never collapse to "…"; a
`@media (max-width: 640px)` rule hides the secondary labels (possession word, turn counter, speed
select label) and collapses the feed to a two-line ticker beneath the canvas; the scorebug never
overlaps the pitch's centre third.

## Packaging

- **Repo**: `Metta-AI/cogame-cogball`, **public** at creation (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `cogball`.
- **`compose.yaml`** — the starter's two-service shape (game and player ship in one image; the
  manifest `run` command selects the role), both services `platform: linux/amd64`,
  `build: {context: ., dockerfile: Dockerfile, network: host}`. **Both services use the same image
  name `coworld-cogball:latest`**, so `{{GAME_IMAGE}}` and `{{PLAYER_IMAGE}}` resolve to one image
  and the scaffold's single `<IMAGE>` placeholder is `coworld-cogball` (moba used two names; one is
  required for the shared `docker_smoke.sh`).
- **`Dockerfile`** — moba's two-stage layout verbatim in structure: stage 1
  `FROM --platform=$BUILDPLATFORM emscripten/emsdk:6.0.5 AS wasm-builder` with the pinned raylib
  prefetch layer, running `sim/build_sim.sh` then `sim/build_viewer.sh`; stage 2 `python:3.12-slim`
  with `uv sync --frozen --no-dev --no-install-project` via the bind-mounted uv image,
  `PYTHONPATH=/workspace/server:/workspace`, copying `build/cogball_sim.wasm` and `viewer/dist/`.
  Adds two one-line shims so the shared scaffold and `policies.json` work:
  `/bin/cogball` → `exec python -m cogball.server` and `/bin/cogball-player` →
  `exec python -m players.cogball_player`, both `chmod +x`. `CMD ["/bin/cogball"]`.
- **`coworld_manifest_template.json`**:
  - `game.name` `cogball`; `episode_timeout_minutes` **20** (matches the assumed platform
    `episodeTimeoutSeconds` 1200 and the 690 s engine stop);
    `game.runnable.image` `{{GAME_IMAGE}}`, `run` `["/bin/cogball"]`,
    `source_url` `https://github.com/Metta-AI/cogame-cogball/tree/main`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema`: `tokens`, `players` (2), `seed`, `max_ticks` (default 7200),
    `turn_ticks` (default 150), `turn_budget_seconds` (default 12), `tick_deadline_ms`
    (default 1000), `player_connect_timeout_seconds` (default 90),
    `wall_clock_budget_seconds` (default 690), `num_agents` (integer, default **2**).
  - `game.results_schema`: exactly the closed key set in §Server, with `reason` enum
    `["complete","deadline","fault"]` and `end_rule` enum
    `["full_time","mercy","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both** `player` and `global`, each
    `{"type": "uri", "value": "https://github.com/Metta-AI/cogame-cogball/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs`: `readme` = `{"type": "text", "value": "<the README body, inlined>"}` and `pages` =
    two entries — `{"id": "protocol.md", "title": "Wire protocol", "content": {"type": "text",
    "value": "<docs/PROTOCOL.md inlined>"}}` and `{"id": "coaching.md", "title": "Writing a cogball
    prompt", "content": {"type": "text", "value": "<docs/COACHING.md inlined>"}}`. Text form, not
    URIs, per the playbook gotcha; a manifest test asserts all three values are non-empty.
  - `game.player[0]` = `{"id": "baseline", "name": "formation", "image": "{{PLAYER_IMAGE}}",
    "run": ["/bin/cogball-player"], "env": {"PLAYER_SCRIPTED": "formation"}}` — the bundled
    certification player, no LLM.
  - **Variants (both carry `num_agents`; the number is 2 everywhere):**

    | id | name | `num_agents` | `max_ticks` | turns | `turn_ticks` | `turn_budget_seconds` | `wall_clock_budget_seconds` |
    |---|---|---|---|---|---|---|---|
    | `default` | Match (2 seats × 3 robots, 4:00) | **2** | 7200 | 48 | 150 | 12 | 690 |
    | `sprint` | Sprint (2 seats × 3 robots, 2:00) | **2** | 3600 | 24 | 150 | 12 | 400 |

    Both variants seat two players named `Azure` and `Magenta`. `sprint` exists for cheap ladder
    rounds; it changes only the match length, never the seat count.
  - **Certification fixture** (`certification`): `players` = `[{"player_id": "baseline"},
    {"player_id": "baseline"}]`; `game_config` = `{"players": [{"name": "Azure"}, {"name":
    "Magenta"}], "num_agents": 2, "seed": 42, "max_ticks": 900, "turn_ticks": 150,
    "turn_budget_seconds": 12, "tick_deadline_ms": 1000, "player_connect_timeout_seconds": 60,
    "wall_clock_budget_seconds": 180}` — 6 turns, both seats scripted, no LLM, wall clock ≈ 5 s.
- **Scaffold from `templates/`** with `<slug>` = `cogball`, `<IMAGE>` = `coworld-cogball`,
  `<SEATS>` = **2**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/build_replay_viewer.sh` (**`chmod +x`** — 
  `coworld build` requires `os.X_OK`), `tools/ci/policies.json`. `ci.yml`'s `test` job comes from
  moba (emsdk + raylib cache + `uv sync` + `uv run pytest` with
  `COGBALL_REQUIRE_WASM_BUILD=1` so a missing wasm artefact fails instead of skipping); the
  `docker-smoke` and `wasm-viewer` jobs keep the template shape (each behind a `test -x`
  assertion, `docker-smoke` `needs:` the image build in the same run so no stale binary can be
  smoked, `wasm-viewer` uploads the `static-replay-viewer` artifact).
  `SMOKE_REQUIRE_REPLAY_JSON` stays at its default `1`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/cogball-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `cogball-total` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `cogball-counter` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `cogball-formation` | `PLAYER_SCRIPTED` = `formation` | filler |
  | `cogball-swarm` | `PLAYER_SCRIPTED` = `swarm` | filler |

- **Repo layout**: `sim/` (`cogball_core.{c,h}`, `cogball_config.h`, `viewer_main.c`,
  `build_sim.sh`, `build_viewer.sh`), `server/cogball/` (`server.py`, `engine.py`, `sim.py`,
  `control.py`, `directives.py`, `baselines.py`, `llm.py`, `replay.py`, `config.py`,
  `defaults.py`, `uris.py`), `players/cogball_player.py`, `viewer/`, `tests/`, `docs/`
  (`PROTOCOL.md`, `COACHING.md`, `plans/`), `tools/`, `AGENTS.md`, `README.md`.

## Tests

`uv run pytest` is the suite; CI is the only harness (the sandbox has no Docker/emsdk). The
determinism gate replaces moba's fidelity gate as **the inviolable test**: if it fails, the physics
or a build flag changed — fix the code, never the test.

1. **`tests/test_physics.py`** — sim unit tests against the wasmtime-hosted core: a ball fired at
   30 m/s into a wall for 600 ticks never leaves the arena (no tunnelling); wall restitution
   reproduces the analytic bounce speed; robot–robot resolution is symmetric (swapping indices
   mirrors the outcome) and conserves momentum to 1e−12; the kick sets the ball's along-heading
   speed to exactly `max(v∥,0)+9.0` and applies the mass-ratio reaction; goal detection fires on
   the exact plane crossing and not one tick early or late; a ball rolled onto a post bounces and
   emits `post`; the kickoff reset places all seven bodies at the documented coordinates (jitter
   included, seed-pinned).
2. **`tests/test_determinism.py`** (**the gate**) — (a) same seed + same control bytes → identical
   digest at every keyframe over a full 7 200-tick match, run twice in one process and once in a
   fresh instance; (b) a one-bit change in any control byte changes the final digest; (c) a
   committed golden fixture `tests/data/golden_digests.json` pins the digests for seed 42 over
   3 000 ticks, so any physics change is visible in the diff; (d) **cross-build**: the same replay
   re-simulated by `build/viewer_core.js` under node (emscripten build) and by
   `build/cogball_sim.wasm` under wasmtime (standalone build) yields **equal digests at every
   30-tick keyframe** — this is the guarantee the whole replay design rests on; (e) a source guard
   that greps `sim/*.c`/`*.h` for `sin|cos|tan|atan|exp|log|pow|fmod|hypot` and `float ` and the
   build scripts for `-ffast-math`, failing on any hit.
3. **`tests/test_control.py`** — the control layer: every intent produces finite commands in
   `[−1, 1]`; quantisation round-trips to the documented byte ranges; the same
   (state, directive) pair always yields the same bytes; `kick: "never"` never emits a kick; the
   cooldown is respected.
4. **`tests/test_baselines.py`** — **bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines, the emitted directive
   validates against the reply schema — exactly three robots, ids exactly that seat's robots, all
   enums legal, targets finite and inside the pitch, `pass_to` a teammate or null, `note` ≤ 160
   runes and `say` ≤ 48 runes — and the compiled controls are within range for every robot. Plus:
   a `formation` vs `swarm` match at seed 42 completes and `formation` wins (the baselines are
   ordered, so the ladder has a spread).
5. **`tests/test_llm_parse.py`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   `robots` as an id-keyed object, unknown enums, NaN/absent targets, out-of-pitch targets, four
   robots, zero robots, an id from the other team, a 300-character `note`, and a `say` whose 48th
   and 49th characters are a 4-byte emoji — the truncation must land on the rune boundary and the
   result must still `json.dumps`/`encode("utf-8")`/`json.loads` cleanly. Two consecutive failures
   → the `formation` directive with a `fallback` event; a timeout on attempt 1 → exactly one retry.
6. **`tests/test_engine.py`** — turn loop: both seats' LLM calls are issued in **one parallel
   batch** (a fake client records overlapping in-flight windows and the test asserts the windows
   intersect); the per-turn budget is enforced with a hung client; the budget guard switches to
   scripted and the episode still ends `complete/full_time`; the 690 s stop yields
   `deadline/wall_clock`; a raised sim fault yields `fault/sim_fault` with 0.5/0.5 scores and a
   partial replay; mercy fires at goal difference 5; a disconnected seat plays `formation` and
   revives on reconnect.
7. **`tests/test_replay.py`** — **end-to-end episode writing a replay**: a full scripted-vs-scripted
   episode over the wasm sim writes `results.json` and the replay; the replay is parsed **strictly**
   (`json.loads(path.read_bytes().decode("utf-8"))`, and the fixture forces a non-ASCII `say` into
   the events so the UTF-8 path is real); `protocol == "cogball/v1"`; `controls_b64` decodes to
   exactly `tick_count × 18` bytes; every documented top-level key is present; `results.reason` is
   in the legal enum; the event stream contains at least one `kick`, one `shot` and one
   `directive` per seat per turn; and re-simulating from `seed` + `controls_b64` reproduces **every
   keyframe digest**.
8. **`tests/test_server.py`** — websocket contract: register frame accepted, bad token 403,
   duplicate connection 409, `/healthz`, `/global` status snapshot then throttled ticks then done,
   `/client/global` and `/client/player`, artifact writes to `file://` URIs, no-show seat reported
   to `COGAME_PLAYER_FAILURE_URI` and played scripted, replay mode serving `/replay-data` and
   `/client/replay`.
9. **`tests/test_manifest.py`** — `num_agents == 2` in **every** variant *and* in
   `certification.game_config`; `len(certification.players) == 2`; results_schema keys ==
   `server/cogball/server.py::_results_doc` keys; `game.protocols` has both `player` and `global`;
   `game.docs.readme` and both pages are non-empty text; `replay_viewer.bundle ==
   "static-replay-viewer"`; `episode_timeout_minutes == 20`; every variant's
   `wall_clock_budget_seconds ≤ 0.6 × 1200`; compose image name matches the `<IMAGE>` used in the
   scaffold.
10. **`tests/test_viewer.py`** — **viewer smoke** (no browser): the node harness
    (`tests/viewer_core_harness.js`, forked from moba) loads `build/viewer_core.js` with a recorded
    replay, re-simulates to the end, and asserts `viewer_total_ticks == tick_count`, the final
    digest matches, seek-to-mid/seek-to-end land exactly, and malformed inputs (bad protocol, bad
    base64 length, truncated JSON, tick_count/body mismatch) are all rejected; plus a static
    assertion over `viewer/index.html` + `viewer/static_replay.js` that they contain the
    `coworld-replay` postMessage bridge **including `tell("ready")`**, the `#scorebug`, `#feed`,
    `#goalbanner` and `#heat` nodes, `.plate-name { flex: 1 1 auto; min-width: 3.2em`, and a
    `@media (max-width: 640px)` block; and that `viewer/dist/` contains
    `index.html`, `static_replay.js`, `sim_sha.js`, `cogball_viewer.js`, `cogball_viewer.wasm`.
11. **`tests/test_startup.py`** — `python -m cogball.server` exits 2 with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing/invalid; `/bin/cogball` and
    `/bin/cogball-player` exist and are executable in the image (asserted in the docker smoke).
12. **`tests/test_perf.py`** (marked slow) — 7 200 ticks of physics in wasmtime complete in under
    20 s.

CI additionally runs `tools/ci/docker_smoke.sh` (raw-Docker episode from the certification
fixture, seats cross-checked against `SMOKE_SEATS=2`, replay must be valid UTF-8 JSON) and
`tools/build_replay_viewer.sh` (bundle builds and contains `index.html`).

## Out of scope (v1)

- **The 6-seat hero-per-seat variant** (one robot per seat, `num_agents` 6) and the cross-play
  report the idea mentions. It requires a different `num_agents`, which the seat-count pin forbids
  in v1; it is the first thing to add in v0.2 as a separate manifest once the ladder is healthy.
- **Box2D**, joints, polygons, friction cones, spin/Magnus on the ball, and any rigid-body feature
  beyond circles with headings.
- **Soccer rules beyond the goal**: no out of play, throw-ins, corners, offside, fouls, cards,
  penalties, keeper handling, or added time. The pitch is walled.
- **Robot heterogeneity**: no per-robot stats, stamina, upgrades, damage, or substitutions.
- **A continuous RL-vector policy interface.** The idea's "RL continuous vector" is reinterpreted
  as the LLM-directive + deterministic-control-layer stack (an inherited pin: both champions must
  be `PLAYER_PROMPT` policies). Exposing the raw per-tick `(thrust, turn, kick)` vector to external
  policies over the websocket is a v0.2 protocol addition; the control layer and quantised action
  log are already shaped for it.
- **Mid-turn interruption**: directives are only replaced at 150-tick boundaries; there is no
  "coach shouts mid-play" channel.
- **Inter-seat chat.** The two seats never exchange messages; `note`/`say` are one-way to the
  replay feed.
- **Audio, 3D, camera cuts other than the slow-mo goal replay, and any downloaded art asset.**
- **Persistent memory across episodes** (no notes carried between matches) and any tournament
  structure beyond the platform league.
