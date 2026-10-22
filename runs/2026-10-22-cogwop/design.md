# cogwop — design note (phase 10)

Lands in the new repo as `docs/plans/2026-10-22-cogwop-design.md`. Repo `Metta-AI/cogame-cogwop`
(public), slug `cogwop`.

Forked from **`Metta-AI/coworld-ctf` (paintbot)**, read at `/workspace/starters/coworld-ctf`: the
starter for any real-time loop with rules written for this coworld (playbook §Phase 0 row 2), which
is exactly what a from-scratch ragdoll sprinter is. **Every convention there holds here unless this
note says otherwise.**

## Source idea (verbatim) — Asana 1219799551688527

> https://app.asana.com/1/1209016784099267/project/1217704774784096/task/1219799551688527
>
> ## Title
>
> 37 QWOP — four keys, two legs, one hundred metres; race solo, or share one body with a stranger
>
> ## Notes
>
> UPDATE 2026-10-22 (daveey): build on Metta-AI/polyworld and make it TRUE 3D. That means a 3D articulated runner on 3D terrain, a real race track through a designed landscape, and a broadcast camera director that flies around to show different angles and puts falls and near-falls first. The sections TRACK & TERRAIN, PHYSICS and BROADCAST COVERAGE below are the spec. They replace any 2D/Box2D wording in the rest of the card.
>
> Bennett Foddy's QWOP (2008, Flash; http://www.foddy.net/Athletics.html) as a coworld. An Olympic sprinter on a 100 m track, controlled only by four binary muscle keys: Q/W drive the thighs (Q = right thigh forward and left back, W = the reverse) and O/P drive the calves the same way. A fall (head, torso or hands touch the ground) ends the run at the distance reached. Deliberately awful controls are both the joke and the skill: an untrained human typically needs hours to reach 100 m (Mike Boyd took ~8 h), and the speedrun record is 45.53 s (kurodo1916, 2022). The 2012 sequel 2QWOP added head-to-head racing.
>
> Why it is a coworld and not just another locomotion env: the marquee mode splits ONE runner across TWO cogs. Seat A owns Q/W (thighs), seat B owns O/P (calves). Neither can run alone. The gait is a coordination equilibrium found through the body, not through words. This is the Tandem (card 15) idea in its purest physical form, with a far more legible spectator story.
>
> Modes (manifest variants):
> - `sprint`: 4 lanes, 4 cogs, each cog controls a whole runner, simultaneous race. Ranking league.
> - `tandem`: 2 lanes, 4 cogs. Each runner is a cross-author pair (thighs seat + calves seat). Score is shared per runner; ranked by cross-play mean over stranger partners.
> - `relay` (stretch): 4×25 m with a baton handoff when the next runner's hand passes the line; a fall costs only your leg.
> - Course variants (see TRACK & TERRAIN): `stadium` (flat, default and certification), `trail`, `alpine`.
>
> TRACK & TERRAIN (polyworld quadterrain + terrain tiles/stamps + props + water)
> - `stadium`: an 8-lane 100 m straight on a red tartan surface with lane lines, distance boards every 10 m, starting blocks, two hurdles (40 m and 70 m), and a finish gantry with a clock. Packed stands on one side; a crowd of animated low-poly spectators that rise and react on beats. The stadium sits in a valley at golden hour: mountains, pine forest, a lake behind the back straight. The far side is open so the scenery reads in wide shots.
> - `trail`: a 100 m cross-country course over polyworld heightfield terrain, with rolling rises and dips (±6% grade), a mud patch (low friction), a short timber bridge over a stream, and a gravel run-out. Same lane count, with lanes as painted tape.
> - `alpine`: a downhill-then-uphill course with one banked bend, snow (low friction) and a cliff-edge section where a sideways fall looks dangerous (it is cosmetic: a safety net catches the runner and the run ends).
> - Terrain is seeded per match within each course. Small height noise and prop placement change; lane lengths and grades stay identical across lanes, so no lane has an advantage.
>
> PHYSICS
> - Polyworld today has planar circle bodies (bodies.nim) and skinned characters (chargen); it has NO articulated rigid-body physics. Add a small deterministic 3D articulated-body sim. Roughly 12 bodies: pelvis, torso, head, upper/lower arms, thighs, shins, feet. Use hinge knees, ball-and-socket hips with motor torque only on flexion/extension, passive hip abduction and ankle springs, and foot–heightfield contact with friction from the terrain material.
> - True 3D means runners can fall sideways and twist as well as fall forward or back. That is good for drama. Expose a `lateral_stiffness` knob, tuned so that the `stadium` course is about as hard as the original and `alpine` is harder.
> - The server is authoritative at a fixed 60 Hz physics step and a 30 Hz policy tick. The replay records per-tick quantized body transforms, so the browser viewer renders them directly and never re-simulates. Cross-platform float determinism is then not required for replays, only for server reruns.
> - Drive the chargen skeleton from the physics bodies, so runners use polyworld's character art (lane colours, numbered bibs).
>
> Seats: 4 (sprint: 4 runners; tandem: 2 runners × 2 seats)
> Motive: sprint is a zero-sum race; tandem is cooperative within the runner and zero-sum between runners.
> Policy interface: RL. Obs = joint angles and angular velocities, torso orientation (pitch/roll/yaw) and height, foot contacts, local terrain slope and material under each foot, distance, and (tandem) the partner's last key state. Action = 2 binary keys per seat (sprint: 4).
> Fills gap: binary-action 3D physical locomotion with a famous human baseline; physical coordination through a shared body with no channel at all (no pings, no text); human-playable in the browser with the same four keys.
> Integrity (anti-collusion): tandem partners are cross-author strangers drawn per match. There is no message channel, so the only signal is the shared body's state. Thighs vs calves assignment is randomized per match. Sprint lanes cannot interact, so a cog cannot throw the race to a friend for gain. Report the cross-play vs self-play gap for tandem.
>
> Scripted baselines: `flail` (random keys), `scoot` (the classic knee-scoot: hold W+O and tap; slow but stable), `stride` (a hand-tuned open-loop gait cycle). Human leaderboard: humans play the same build in the browser and are seated against cogs.
>
> BROADCAST COVERAGE (polyworld actioncam.nim + directors.nim, extended)
> Model it on a TV athletics/F1 broadcast. Every camera is a named rig the director cuts between. The director runs on the full replay, so it can LOOK AHEAD: it knows every fall before it happens and cuts to that runner 1.5–2 s early, so the fall is always on screen. For live/human play, use the instability score below as the predictor instead.
>
> Camera rigs:
> 1. Rail cam: a low dolly on a rail beside the track that matches the leader's speed. This is the signature 100 m shot, all lanes in profile.
> 2. Head-on telephoto from behind the finish line: compresses the lanes so the race order and gaps read instantly.
> 3. Jib/crane: a sweeping high-to-low move at the start and finish.
> 4. Drone/aerial: a slow orbit over the stadium and terrain for the opening, the scenic establishing shot and transitions; it chases along the course on `trail`/`alpine`.
> 5. Spidercam: an overhead cable cam that tracks the pack from above and behind.
> 6. Hurdle cams: low ground cameras at each hurdle that fire as a runner approaches.
> 7. Runner cams: a chest-mounted POV per runner, plus a trailing steadicam behind and in front. Used for falls and tandem drama.
> 8. Iso cams: every runner is recorded from rail + head-on + POV for the replay package.
> 9. Photo-finish slit camera at the line (the classic slit-scan strip image) for close finishes.
> 10. Crowd cam: a reaction shot of the stands after big falls and the finish.
>
> Director priorities (strongest first; an interrupt can cut in while another shot is held):
> - FALL (critical, interrupts anything): cut 1.5–2 s before the fall to the runner cam or a tight rail shot, hold through the ragdoll and the dust, then a crowd groan.
> - NEAR-FALL / SAVE (major): the instability score crosses a threshold and the runner recovers. Hold a tight shot; label it "SAVE" on screen.
> - Hurdle approach and clip; overtake or lead change; two runners within 0.5 m ("battle" two-shot).
> - Finish: always locked to the head-on + slit cam in the last 10 m, whatever else is happening. Never miss the finish.
> - Leader cruise / scenic aerial when nothing is happening (overview at least every 30 s, as directors.nim already does).
>
> Instability score (per runner, per tick): torso tilt from vertical, angular velocity, centre of mass outside the foot support polygon, and head height falling. It drives the near-fall detection, the live pre-roll, a per-runner "wobble meter" on screen, and a subtle red rim light on runners about to go.
>
> Replay package: after every fall, run a 4–6 s slow-mo instant replay from 2–3 iso angles (runner cam, rail, aerial) while a picture-in-picture box keeps the live race on screen. If two falls overlap, use a split screen. At the end, a "fall of the race" highlight plays before the endcard.
>
> On-screen graphics: lane order ticker, distance and speed per runner, gap to the leader, split times at 25/50/75 m, the four lit key squares under each runner (tandem: thigh keys tinted in seat A's colour, calf keys in seat B's), the wobble meter, and the race clock. Endcard: distance, time, falls, saves, max speed, and (tandem) a blame bar showing which seat's key presses preceded each fall.
>
> New director events (add to EventKind alongside the combat events): FallEvent, NearFallEvent, SaveEvent, HurdleEvent, OvertakeEvent, FinishEvent.
>
> RL references: https://github.com/juanto121/qwop-ai (DQN/DDQN), https://github.com/drakesvoboda/RL-QWOP (game internals as a gym env, limb pos/angle state), https://github.com/yatshunlee/qwop_RL. Wesley Liao's agent ran 47.34 s, beating the 48.34 s human best at the time (2021).
> Licence note: QWOP is Foddy's. Do NOT ship his assets or code. Reimplement the physics and art from scratch and call the world `cogwop` (or similar).
>
> Build owner: CoMax Paperclip team ($1,000 budget granted by daveey, 2026-10-22; ask daveey for more if the 3D scope needs it).
>
> Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c

## The game

A side-on 2D ragdoll sprinter on a 100 m track. Four binary muscle keys drive the whole body:
**Q** = right thigh forward / left thigh back, **W** = the reverse, **O** = right calf extends /
left calf flexes, **P** = the reverse; a key and its opposite in the same tick cancel. A fall (head,
chest, hips or a hand touching the ground) ends that runner's run at the distance reached. One
0.30 m hurdle sits at 50 m. In `sprint` one cog owns all four keys of a runner; in `tandem` a runner
is split across two cogs — a **thighs** seat (Q/W) and a **calves** seat (O/P) — with no channel
between them but the shared body.

**Scope rulings.** The idea's 2026-10-22 update asks for polyworld 3D, terrain courses and a camera
director; the coordinator ruled this run 2D on `coworld-ctf`, so all of that is in `## Out of scope
(v1)` and what survives is the *watchability spec* — tracking camera, lit key squares, splits,
wobble, falls, photo finish, endcard with blame bar — in 2D. The idea's two hurdles become **one at
50 m** (rail 10). "RL" becomes LLM-or-scripted decisions at a coarse cadence with tick-resolution
control through **key schedules** (below): this platform has no training loop.

**Licence.** `cogwop` is an original game. It ships no Bennett Foddy asset, art, code, string or
data, and **no code or data from `qwop-ai`, `RL-QWOP` or `qwop_RL` is vendored, copied or adapted**.
A sentence of provenance ships in `README.md` and the `rules` docs page ("inspired by Bennett
Foddy's QWOP (2008); no Foddy assets or code are used").

### Design pins (playbook §Phase 0), and how each is satisfied

| pin | satisfied by |
|---|---|
| starter by game shape | `coworld-ctf` (paintbot): real-time loop with new rules, per-tick replay, static viewer, chrome |
| public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-cogwop`, public at creation |
| LLM **and** scripted day one, same image, env-switched | `PLAYER_PROMPT` ⇒ LLM seat; `PLAYER_SCRIPTED=flail\|scoot\|stride` ⇒ scripted seat (§Decisions) |
| static wasm viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}` + `tools/build_replay_viewer.sh` |
| starter chrome verbatim | `chrome_common.js` byte-for-byte; `replay_broadcast.html` = starter page **+ appended game block** |
| real art, not placeholders | stadium, tartan lanes, hurdle, gantry, jointed runner with bib and singlet, dust, crowd |
| legible to a casual spectator | metres and seconds on screen, never ticks or fixed-point; 360 px check in §Viewer |
| two name spaces | aliases `LANE-1…LANE-4` (+`/THIGHS`,`/CALVES`) in-game; policy names spectator-side only |
| degrade, never hang | 690 s budget, every wait bounded, retry-once-then-scripted, budget guard |
| `num_agents` in every variant and the cert fixture | **4**, in both variants' `game_config`, in `certification.game_config`, and as `SMOKE_SEATS` |
| policies before `upload-coworld`; secret after | `templates/coworld-release.yml` used unmodified |

### Seats, variants, roles

`num_agents` = **4**, identical in both variants and in the certification fixture.

| variant | runners | seats/runner | seat → runner | roles |
|---|---|---|---|---|
| `sprint` | 4 | 1 | seat *i* → runner *i* | every seat owns Q W O P |
| `tandem` | 2 | 2 | runner 0 = seats 0 and 2; runner 1 = seats 1 and 3 | one seat `thighs` (Q W), one `calves` (O P), **drawn from the match seed** |

Pairing across the slot block (0+2, 1+3) maximises the chance the ladder's block seating puts two
different authors on one body; the role within a pair is bits 0/1 of the match PRNG, re-drawn every
match (the idea's integrity rule). Sprint lanes never interact — no inter-runner collision — so a
cog cannot throw a race for a friend.

### Turn structure and resolution order

Physics is a fixed **30 Hz** tick; decisions are **decoupled** from it — each turn a seat submits a
*key schedule* for the next window, so control keeps tick resolution while decisions stay coarse
enough for an LLM.

| quantity | value |
|---|---|
| physics tick | 1/30 s (`TickHz = 30`) |
| decision window | 60 ticks = **2.00 s** (`windowTicks`) |
| decision turns per episode | **60** (`maxTurns`) ⇒ 3600 ticks = **120.0 s of race** |
| segments per schedule | ≤ 12, each 1…60 ticks, summing to exactly 60 |
| minimum recorded episode | 900 ticks (30 s), `minEpisodeTicks` — the replay always outlasts a 10 s viewer soak |

Per turn, in this order:

1. The server builds each **live** seat's observation (§Observation); a seat whose runner has fallen
   or finished is not live and is never asked.
2. The batch start is held to the rate floor (§Decisions) and **all live LLM seats' calls go out as
   ONE parallel batch** (`curly.makeRequests`).
3. Replies are parsed and repaired into legal schedules (§Reply schema); still-failing seats get one
   retry batch, and a second failure falls back to that seat's scripted schedule.
4. Scripted seats compute their schedule locally (microseconds).
5. One `plan` record per seat is appended to the replay (`llm` / `scripted` / `fallback`).
6. The sim steps 60 ticks. Per tick, in this exact order: (1) resolve each runner's key mask —
   tandem: the thighs seat supplies the Q/W bits, the calves seat the O/P bits, and a seat can never
   set a bit it does not own; (2) muscle torques, thighs then calves, runners in lane order, left leg
   before right; (3) gravity; (4) Verlet integrate with air damping; (5) constraint solve, 8
   iterations in the fixed order of §Sim module; (6) ground projection + friction, then hurdle
   projection; (7) fall test, then distance/speed/wobble update and event emission; (8) state hash,
   recorded every 30th tick.
7. End-condition check (below).

### End conditions and `results.reason`

1. **`complete`** — every runner finished or fallen **and** `tick ≥ 900`, then a 90-tick (3 s) hold
   for the endcard beat (`endRule: "all_down"`).
2. **`complete`** — turn 60 finished (tick 3600); runners still upright score the distance reached
   (`endRule: "full_time"`).
3. **`deadline`** — at a turn boundary the monotonic wall clock reached
   `wallClockBudgetSeconds = 690`: the sim stops and every runner is scored at its current distance
   (`endRule: "wall_clock"`). The stop is written as **one load-bearing `stop` record applied by the
   same proc on record and on playback** — a wall-clock fact cannot be re-derived (particle-worlds
   2026-08-26). Rare: the budget guard (§Decisions) normally converts this into `complete`.
4. **`fault`** — internal error only, never written by a healthy episode; CI asserts
   `reason ∈ {complete, deadline}`.

### Scoring

One scalar per seat, **higher is better**, written to `results.scores[slot]`.

```
raw(runner) = distance_m                    if it fell or ran out of turns   (0 … 100)
            = 100 + (120 - finish_time_s)   if it crossed 100 m              (100 … 220)
score(seat) = raw(runner of this seat)
            + 2 × (number of OTHER runners with a strictly lower raw)
```

* `distance_m` is the hip particle's x, clamped to `[0, 100]`, rounded to 0.01; `finish_time_s` is
  `finish_tick / 30` and can never exceed 120, so a finisher always scores ≥ 100 and a non-finisher
  ≤ 100: **finishing always beats not finishing.** A fall needs no extra penalty — it freezes the
  distance. The placement term adds 0…6 in sprint, 0…2 in tandem; ties contribute nothing.
* **Tandem: both seats of a runner get the identical score and the identical `win`.** `win[slot]` is
  true for every seat of the runner(s) with the maximum `raw` (ties: all win). A seat that never
  registered still scores — its runner plays `stride` (§Decisions).
* The league ranks by Elo over these per-episode scores; for tandem the Observatory mean over
  stranger partners is the cross-play number, and `selfPlay[runner]` in the results (true when both
  seats' spectator-side labels match) makes the **cross-play vs self-play gap** computable from the
  bytes.

Examples: finishes at 48.20 s beating all three rivals → `177.80`; falls at 23.41 m beating one →
`25.41`; falls at the blocks, last → `0.00`.

### Observation (exactly what a seat sees, and what it does not)

One JSON object per seat per turn, built server-side, in metres / m/s / degrees / seconds — never
fixed-point, never ticks outside the schedule.

```json
{"variant":"tandem","turn":7,"turns":60,"tick":420,"window_ticks":60,"hz":30,
 "clock":{"race_s":14.00,"left_s":106.00},
 "you":{"alias":"LANE-2/THIGHS","role":"thighs","keys":["Q","W"]},
 "runner":{"alias":"LANE-2","distance_m":12.34,"speed_mps":1.42,"max_speed_mps":2.10,
   "torso_pitch_deg":7.2,"hip_height_m":0.86,"com_lead_m":0.11,"wobble":0.31,
   "thigh_deg":{"left":-18.0,"right":24.0},"knee_deg":{"left":31.0,"right":12.0},
   "thigh_rate_dps":{"left":-96.0,"right":120.0},"knee_rate_dps":{"left":44.0,"right":-20.0},
   "contact":{"left_foot":true,"right_foot":false,"hand":false,"head":false},
   "fallen":false,"finished":false,"falls":0,"saves":1,"splits_s":{"25":null,"50":null,"75":null}},
 "last_window":{"you_sent":[["QO",6],["WP",9]],"partner_keys":[["O",12],["",48]],
   "gained_m":1.08,"wobble_peak":0.62},
 "hurdle":{"at_m":50.0,"height_m":0.30,"distance_to_m":37.66},
 "field":[{"alias":"LANE-1","distance_m":15.20,"speed_mps":1.90,"fallen":false,"finished":false}],
 "rules":{"max_segments":12,"ticks_must_sum_to":60}}
```

Visible: everything above. In tandem both seats of a runner see the **same** `runner` block — the
shared body is the only channel — plus `last_window.partner_keys`, the key states the partner
actually realised last window (the idea's "partner's last key state"). Hidden, always: other
runners' poses, joint angles and key states (`field` carries distance, speed, status and nothing
else); the partner's `note`, `PLAYER_PROMPT`, policy name and *upcoming* schedule; any real player
name; the match seed; any other seat's observation. There is **no message channel of any kind** — a
seat's `note` goes to the replay and the spectator feed only, never into another seat's view.

### Reply schema and repairs

```json
{"note":"short line, what you are trying","plan":[{"keys":"QO","ticks":6},{"keys":"WP","ticks":9}]}
```

| field | type | cap | repair when wrong |
|---|---|---|---|
| `note` | string | **≤ 120 runes**, truncated on a **rune boundary** | missing ⇒ `""`; newlines ⇒ spaces |
| `plan` | array | **≤ 12 entries** | entries after the 12th dropped |
| `plan[].keys` | string | **≤ 4 runes** | case-folded; letters outside this seat's key set dropped; `""`, `"-"`, `"none"` ⇒ all released |
| `plan[].ticks` | int | 1…60 | float/string coerced; `< 1` ⇒ 1; `> 60` ⇒ 60 |

Repair order in the server: (1) extract the outermost balanced `{…}`, tolerating fences and prose
(port `extractJsonObject`, `src/ctf/directives.nim:102`); (2) truncate `note`; (3) walk `plan`,
coercing entries and dropping unowned key letters; (4) drop entries past 12; (5) if the durations
sum **< 60**, extend the last segment to 60 (empty plan ⇒ one 60-tick segment holding last window's
final key state, else all-released); (6) if they sum **> 60**, truncate the last admitted segment to
hit exactly 60 and drop the rest. The parser raises only when *no* segment survives step 3 — the one
condition the retry and the scripted fallback exist for. **Every string reaching the replay is
truncated on rune boundaries** (`truncateRunes`, `src/ctf/directives.nim:61`); byte slicing anywhere
on the path to the replay bytes is forbidden.

### Event vocabulary written to the replay

| kind | fields beyond `t` (tick) and `runner`/`seat` |
|---|---|
| `start` | `variant`, `seed`, `lanes` |
| `plan` | `turn`, `seat`, `src` (`llm`/`scripted`/`fallback`), `ms`, `note`, `seg` `[[keys,ticks],…]` |
| `register` | `seat`, `alias`, `policy` (≤ 48 runes), `kind` (`llm`/`scripted`/`unregistered`), `baseline` |
| `split` | `m` (25/50/75), `s` |
| `hurdle` | `cleared` (bool), `speed_mps` |
| `save` | `peak_wobble`, `ticks_held` |
| `fall` | `part` (`head`/`neck`/`hip`/`hand`), `distance_m`, `speed_mps`, `blame` (tandem `[thighs, calves]`) |
| `finish` | `time_s`, `max_speed_mps` |
| `overtake` | `passed` (alias), `distance_m` |
| `fallback` | `turn`, `attempt`, `cause` (`timeout`/`transport_error`/`throttled`/`parse_error`/`no_credentials`/`budget_guard`), `detail` ≤ 160 runes |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `reason`, `rule`, `tick` — the load-bearing wall-clock stop record |
| `result` | the whole results document, once, at the end |

## Decisions: LLM with scripted fallback

One image, two entrypoints, three env switches — the paintbot shape
(`src/paintball_player.nim:60-76`): `PLAYER_PROMPT` ⇒ **LLM seat**;
`PLAYER_SCRIPTED=flail|scoot|stride` ⇒ **scripted seat**; `PLAYER_POLICY_LABEL` ⇒ the spectator-side
label; neither ⇒ `stride`. Every decision happens **inside the game container** — the only one the
platform injects the coworld secret into; the player container is a thin registrar (§Server).

### Wall-clock arithmetic (must fit inside 60 % of `episodeTimeoutSeconds` = 720 s)

Knobs: `attempt1Ms` 6000, `retryMs` 4000, `turnBudgetMs` (whole turn) 11000,
`wallClockBudgetSeconds` 690, `joinTimeoutSeconds` 60, `shutdownGraceSeconds` 20,
`turnSpacingMsPerLlmSeat` 2500.

* Worst case: 60 turns × 11 s = **660 s**, + 20 s join grace + 20 s shutdown grace = **700 s ≤ 720 s**. ✅
  Typical hosted: 60 × ~2.6 s ≈ 156 s. Offline (no credentials) every turn falls back instantly with
  no network wait, so certification and `docker_smoke.sh` finish in ~25 s.
* **Rate floor.** The Bedrock sidecar caps **30 requests/minute per episode**. Batch starts are held
  `2500 ms × (live LLM seats)` apart: 4 LLM seats ⇒ 10 s spacing ⇒ 60 batches ≥ 600 s carrying
  4 × 60 = 240 requests = **24 req/min ≤ 30**; 2 LLM seats ⇒ 5 s spacing, 120 requests ≥ 300 s, the
  same 24 req/min. Spacing is recomputed each turn from the live seat count, so falls and finishes
  make an episode cheaper, never dearer.
* **Physics is free**: ≈ 1.5 k integer ops/tick for four runners, ≈ 20 ms of CPU per episode, so the
  budget is LLM latency only — which is why the server runs `fastMode` (nothing sleeps to real time
  but the rate floor).

### Degrade, never hang

1. Attempt 1: one parallel batch, `attempt1Ms` deadline. A failure logs **`will retry`** — never
   "falling back" (pommerman scar: phase 60 greps that phrase).
2. Attempt 2: one parallel batch of the still-open seats, `retryMs`. A 429 with no second candidate
   model skips this batch entirely (`throttled` fails fast — `src/ctf/llm.nim:201-207`).
3. Still open ⇒ that seat plays **its scripted baseline's schedule for this window** (an LLM seat's
   fallback baseline is `stride`), a `fallback` record names the cause, the log says `falling back`.
4. **Budget guard**: at the top of every turn, if `elapsed + 2 × turnBudget > 690 s` the LLM is
   switched off for the rest of the episode (`budget_guard` record) and the remaining turns play
   `stride` in microseconds, so the episode ends `complete`, not `deadline`
   (`src/ctf/decide.nim:335-348`).
5. A seat unregistered when `joinTimeoutSeconds` expires gets an **ERROR line**
   `seat_unregistered seat=<n>`, a `register` record with `kind:"unregistered"`, and plays `stride`;
   `docker_smoke.sh` greps that string and fails (grf-football 2026-08-27).
6. No path leaves a runner unactuated: this turn's schedule, else last turn's final key state
   held, else `stride`.

### The LLM call

Transport ladder, model rotation, fence-tolerant extraction and rune truncation are ported from
`src/ctf/llm.nim` behaviour-for-behaviour: `COWORLD_LLM_ENDPOINT` → Bedrock bearer →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`; with none, the client disables itself and logs `the
LLM provider is unavailable`. One candidate model (`us.anthropic.claude-haiku-4-5-20251001-v1:0`),
`maxOutputTokens` 900, assistant turn prefilled with `{` and the prefill re-prefixed before parsing
(procgen scar). System prompt, exact text, shipped as `SystemPrompt`:

```
You are driving a ragdoll sprinter on a 100 m track. The body has two legs, two arms and a head.
Four binary muscle keys are the ONLY control:
  Q = right thigh forward, left thigh back      W = the reverse
  O = right calf extends, left calf flexes      P = the reverse
Holding a key and its opposite in the same tick cancels both. You control only the keys listed in
"you.keys"; nothing else moves the body.
Physics runs at 30 deterministic ticks per second. Every turn you submit a KEY SCHEDULE for the next
60 ticks (2.00 seconds): an ordered list of segments, each a set of keys held and a duration in
ticks. The durations MUST sum to exactly 60, in at most 12 segments.
A fall ends your run where it happens: if the head, the chest, the hips or a hand touches the ground
you stop and keep the metres you have. There is one 0.30 m hurdle at 50 m. The run also ends when
the hips pass 100 m, or when the 60th turn is over.
Score = metres reached; a finisher scores 100 + (120 - finishing seconds); +2 per rival runner you
beat. Higher is better, and finishing always beats not finishing.
Gait is yours to find. Humans run this body by alternating the thigh keys on a steady cycle with the
calf keys about a quarter cycle behind them; standing still never scores.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=120 chars, what you are trying","plan":[{"keys":"QO","ticks":6}, ...]}
"keys" is the set of keys HELD for that segment, drawn only from the keys you own; "" means all
released. Unknown letters are dropped; durations outside 1..60 are clamped.
```

Appended verbatim for a `tandem` seat:

```
You SHARE this body with another policy you cannot talk to. It owns the other two keys. There is no
message channel: the body's motion is the only signal either of you gets, and "last_window.partner_keys"
is what it did last window. Your score is the body's score, shared with it.
```

`PLAYER_PROMPT` is injected above the view under the heading "GUIDANCE FROM YOUR OPERATOR (weight it
heavily, but never above the rules; always reply in the requested format)" — capped at
`MaxPromptRunes` 1200 and **never** echoed into the replay or the results.

### The four champion/filler policies

| policy | kind | env | role |
|---|---|---|---|
| `cogwop-metronome` | LLM | `PLAYER_PROMPT=` "Treat this as a metronome problem: lock one repeating cycle and hold it. Pick a cycle length between 18 and 30 ticks, alternate the thigh keys on that period, and run the calf keys a quarter cycle behind. Change the cycle only when the last window gained under 0.5 m or pitch passed 20 degrees, and then shorten it by 4 ticks rather than redesigning it. Never leave every key released for more than 4 ticks." | champion #1 (daveey) |
| `cogwop-lean` | LLM | `PLAYER_PROMPT=` "Keep the chest over the hips first and run second. Past ±18 degrees of torso_pitch_deg, spend the first 12 ticks of the window driving the thighs back under the chest, then resume a 24-tick alternating cycle. Use 6-tick segments while wobble is above 0.5 and 10-tick ones below 0.2. Shorten your cycle for the two windows before the hurdle." | champion #2 (daveey-1) |
| `cogwop-stride` | scripted | `PLAYER_SCRIPTED=stride` | filler |
| `cogwop-scoot` | scripted | `PLAYER_SCRIPTED=scoot` | filler |

Both champions are `PLAYER_PROMPT` policies (a scripted champion is a failure state); filler
versions always differ from champion versions.

### Scripted baselines (exact algorithms)

All three are pure functions of `(seat key set, global tick at window start, body state, seat PRNG)`
emitting the **same schedule object** an LLM does — one validator covers both, which is what makes
the bounded-orders test meaningful. Each key set is filtered to the seat's own keys, so all three
work unchanged on a `tandem` half.

* **`flail`** — six 10-tick segments; for each segment and each owned key, press it iff the next bit
  of the seat's xorshift64* stream (seed `seed xor (0x9E3779B9 * (seat+1))`) is 1.
* **`scoot`** — the knee-scoot: the 20-tick pattern `[("WO",16),("W",4)]` three times per window. A
  `thighs` seat emits `[("W",60)]`, a `calves` seat `[("O",16),("",4)] × 3`. Slow and very stable —
  the ladder's floor.
* **`stride`** — a hand-tuned **open-loop** gait, phase-locked to the global tick so it is continuous
  across windows: period `StridePeriodTicks = 24` (1.25 strides/s), calves lagging thighs by
  `StridePhaseOffsetTicks = 6` (a quarter cycle), quarter length `StrideDutyTicks = 6`. The cycle is
  `Q P` (phase 0–5), `Q O` (6–11), `W O` (12–17), `W P` (18–23), sampled from
  `phase = globalTick mod 24` and merged into 10 six-tick segments, inside the 12-segment cap.

`stride` is what the league leans on — LLM fallback, unregistered-seat default, certification
player — so its constants are **tuned, not guessed**: `tools/tune_baselines.nim` sweeps
`StridePeriodTicks ∈ {18…30 step 2}` × `StridePhaseOffsetTicks ∈ {4…8}` × `StrideDutyTicks ∈ {4…7}`
over 5 fixed seeds and writes the winner to `tools/ci/baseline_tuning.json`; `tests/test_tuning.nim`
asserts the shipped constants equal it, and `tests/test_baselines.nim` asserts the acceptance bar —
median distance `stride` > `scoot` > `flail` with `stride ≥ 20 m` (raise the torque constants of
§Sim module if the sweep cannot clear it).

### Two name spaces

In-game a seat sees only anonymous aliases: `LANE-1`…`LANE-4` in sprint, `LANE-1/THIGHS`,
`LANE-1/CALVES`, `LANE-2/THIGHS`, `LANE-2/CALVES` in tandem. Real policy names (`cogwop-metronome`,
`daveey`, `Baseline (1)`) exist **only** spectator-side: the `register` record's `policy` field,
`results.names[]`, and the viewer's nameplates. Nothing maps an alias to a policy name inside an
observation, and `PLAYER_PROMPT` text never leaves the game container.

## Sim module

### Files

Forked from the starter unless marked `new`: `src/cogwop.nim` (← `src/ctf.nim`; entrypoint, seed
randomisation **before** `config.update`), `src/cogwop/fixed.nim` (new; Q16.16 `fpMul`, `fpDiv`,
`fpSqrt`, `fpClamp`, `xorshift64s`), `sim_types.nim` (consts incl. `GameVersion`, body/track
constants, wire types), `body.nim` (new; particles, bones, joint limits, muscles, contacts),
`sim.nim` (step loop, events, distance, wobble, scoring), `sim_config.nim` (config lifecycle +
bounds validation), `schedule.nim` (← `directives.nim`; schedule type, tolerant parse, repairs, rune
caps), `baselines.nim`, `llm.nim`, `decide.nim`, `events.nim` (one serializer, live and replay),
`replay_json.nim` (← `replays.nim` in shape only — JSON, **not** the binary `COWLDCTF` codec),
`viewer_packet.nim` (← `broadcast.nim` in shape; the per-frame packet the renderer draws),
`server.nim` (routes, websockets, artifacts, shutdown grace), and `src/cogwop_player.nim`
(← `src/paintball_player.nim`; the thin seat registrar).

The sim module is imported unchanged by server, wasm entry and tests — which is what makes
"compiled twice, bit-identical" checkable.

### Arithmetic: deterministic by construction

**No floats anywhere in the sim module.** Every sim quantity is `int64` **Q16.16** fixed point
(1 unit = 1/65536 m, m/s or N). The rules are binding and each has a test:

1. `fpMul(a, b) = (a * b) div 65536` — **`div`, never `shr`**: truncation toward zero is identical
   on native x86-64 and wasm32, and the sign semantics of `shr` are not worth arguing about.
   `fpDiv(a, b) = (a * 65536) div b`, `b ≠ 0` asserted.
2. Roots use an integer Newton `fpSqrt` (24 iterations, exact). **No `math.sqrt`, `sin`, `cos`,
   `atan2`, `pow` or any libm call** — the ragdoll needs none: normals are the perpendicular
   `(-dy, dx)`, angle tests are cross/dot signs, and degrees exist only for the observation JSON and
   the viewer, outside the hash.
3. Magnitudes are clamped every tick (`|position| ≤ 150 m`, `|velocity·dt| ≤ 2 m/tick`,
   `|force| ≤ 4000 N`), so products stay below 2^52, decades inside `int64`.
4. Iteration order is fixed; it never depends on a hash table, a set, address order or wall time.
5. The only RNG is `xorshift64s` from `config.seed`; each consumer (start perturbation, role draw,
   `flail`) takes its own stream `seed xor <const>`, so adding a draw never shifts another's.

Floats are rejected because emscripten's `clang` takes a different code path than native and one
last-bit difference compounds over 3600 ticks into a different race. Integers make "native and wasm
agree" a property of the code rather than of the toolchain; `tests/test_wasm_parity` proves it.

### The body

Nine particles per runner (position, previous position, inverse mass), Verlet integrated, bones as
hard distance constraints. Start pose (metres, lane-local, x = 0 at the start line, mass in kg):
head `6 @ (0.02, 1.58)`, neck/chest `16 @ (0.00, 1.36)`, hip `32 @ (−0.03, 0.86)`,
knee L `7 @ (0.09, 0.45)`, foot L `4 @ (0.14, 0.00)`, knee R `7 @ (−0.12, 0.45)`,
foot R `4 @ (−0.18, 0.00)`, hand L `3 @ (0.22, 1.02)`, hand R `3 @ (−0.20, 1.02)`.

Bones (hard, solved in this order, 8 Gauss-Seidel iterations): head–neck 0.23, neck–hip 0.50,
hip–knee 0.45 ×2, knee–foot 0.45 ×2, neck–hand 0.62 ×2, plus a rigid head–hip brace 0.73 — that one
extra constraint is what makes the torso rigid with no rotational state. Joint limits, after the
bones each iteration: hip–foot clamped to `[0.30, 0.895]` (knee ≈ 0°…140°) and **anti-hyperextension**
— `cross(knee − hip, foot − knee)` must be ≤ 0 on the left leg and ≥ 0 on the right; on violation the
knee is reflected across the hip–foot line.

Muscles: `τ_thigh = (Q ? +1 : 0) + (W ? −1 : 0)`, `τ_calf = (O ? +1 : 0) + (P ? −1 : 0)`; both keys
⇒ 0. The drive is a **force couple** (momentum conserving): `F = τ · T / L` perpendicular to the
segment at the distal particle and `−F` at the proximal one — thighs at knee and hip, calves at foot
and knee. Right leg takes `+τ`, left leg `−τ`.

Constants: `ThighTorqueNm` 180, `CalfTorqueNm` 110, `JointDampingNmsPerRad` 8, `GravityMps2` 9.81,
`AirDampingPerTick` 0.998, `FootFrictionRetain` 0.10 (90 % of tangential slip killed),
`BodyFrictionRetain` 0.50 (head/hand/hip skid), `GroundY` 0.00 with restitution 0, `ContactEpsM`
0.02, `HurdleAtM`/`HurdleHeightM`/`HurdleWidthM` 50.00/0.30/0.08, `TrackLengthM` 100.00,
`StartJitterM` ±0.01 m of hip height and ±0.5° of lean, drawn per lane from the seeded PRNG.

Contact: a particle below `GroundY` is projected to it and its tangential displacement multiplied by
its retain factor; a particle inside the hurdle box is pushed out along the axis of least
penetration. **Fall** = any of {head, neck, hip, hand L, hand R} at `y ≤ ContactEpsM`; the runner's
distance freezes, its keys are ignored for the rest of the race, and the ragdoll keeps settling
(still drawn). Derived per tick: `distance_m` = hip x clamped to `[0,100]`; `speed_mps` = hip x
displacement × 30 smoothed over 6 ticks; `wobble` =
`clamp01(0.5·|pitch|/0.6rad + 0.3·|pitchRate|/4rad·s⁻¹ + 0.2·|com_lead|/0.25m)`. A **save** is
`wobble ≥ 0.75` held ≥ 5 ticks then under 0.45 within 45 ticks with no fall. Lanes are simulated
independently; there is no inter-runner collision.

Hash: FNV-1a over every particle's `(x, y, prevX, prevY)` plus every runner's fallen/finished flags,
recorded every 30th tick as 16 hex digits. Playback recomputes it and the viewer raises the
starter's mismatch banner (`ctf_mismatch_tick`, `replay-viewer/ctf_replay.nim:255`) on disagreement.
The start perturbation is the only seeded part of the body state and is identically distributed per
lane, so no lane has an advantage.

### Replay: inputs, not poses

The replay records **seed + config + rosters + per-turn accepted key schedules + events + periodic
hashes + results**, and the wasm viewer re-derives every pose with the same sim. Why: it is this
lineage's pattern (`replay-viewer/ctf_replay.nim:172` boots the real sim from recorded inputs); the
alternative is 3600 × 4 × 9 × 2 = 259 200 numbers, ~1.5 MB of JSON even quantised to centimetres,
against ~100 KB here; and integer physics makes re-derivation exact, with the hash chain proving it
every 30 ticks. Budget: plans ≈ 70 KB, events ≈ 18 KB, hashes ≈ 3 KB, config/rosters/results ≈ 8 KB
⇒ **≈ 100 KB typical**; `tests/test_replay_size.nim` fails over 512 KB. The bytes are plain **UTF-8
JSON** — `replay_compression` is deliberately **not** declared, so S3 bytes parse directly (SPEC
check 4) and `docker_smoke.sh`'s default `SMOKE_REQUIRE_REPLAY_JSON=1` holds.

```json
{"protocol":"cogwop/1","gameVersion":"1","seed":774411,"variant":"sprint",
 "config":{…the full resolved game config…},
 "runners":[{"lane":0,"alias":"LANE-1","color":"red","seats":[0],"selfPlay":false}],
 "seats":[{"seat":0,"alias":"LANE-1","role":"whole","runner":0,"policy":"cogwop-metronome","kind":"llm"}],
 "plans":[{"t":0,"turn":0,"seat":0,"src":"llm","ms":2412,"note":"24-tick cycle","seg":[["QP",6],["QO",6]]}],
 "events":[{"t":312,"kind":"split","runner":0,"m":25,"s":10.40}],
 "hashes":[[30,"9f3a1c7d4e55b012"]], "results":{…}}
```

Everything the viewer needs is in those bytes — names (both spaces), config, seed, per-tick inputs,
events, results — and it contacts no server except S3 for the file.

## Server, player, protocol

One image, two entrypoints: `/bin/cogwop` (the game server) and `/bin/cogwop-player` (the seat
registrar). Mummy HTTP + websockets on port 8080.

| route | behaviour (and why) |
|---|---|
| `GET /healthz` | 200 while serving **and for `shutdownGraceSeconds = 20` after artifacts are written** (lantern 0.1.3) |
| `GET /client/player?slot=&token=` | a real HTML page; **never opens the player websocket** (lantern 0.1.1) |
| `GET /client/global` | a real HTML page (the live broadcast view) |
| `WS /player?slot=N&token=T` | **closes immediately unless the token matches that seat** (flatland 0.1.1) |
| `WS /global` | spectator stream; answers `Ping` with `socket.send(message.data, Pong)` and guards nothing else — a `kind != TextMessage` guard drops the player's binary registration frames (lux-ai / snake-royale, `src/ctf/server.nim:3124`) |

Player protocol (binary frames, deliberately tiny):

* **registration** — `0x01` + UTF-8 JSON `{"type":"register","prompt":…,"scripted":…|null,"policy":…}`,
  sent on connect and **re-sent 10 times, one per ~24 received frames**: joins are slot-sequential,
  so the first registrations can land before the seat has an index (paintball round 3,
  `src/paintball_player.nim:115-130`). The same JSON is accepted as a text frame too.
* **server → player** — `0xA0` per tick (a heartbeat the registrar keys its re-sends on), `0xA1` +
  the seat's observation JSON at each turn boundary (informational; the server decides).
* **player → server** — `0x85` ready, after each received frame. The receive loop is wrapped in
  `try/except CatchableError` and **exits 0 on a dead socket** (raid 0.1.3); dialling (240 × 500 ms)
  and re-dialling (6) are bounded.

Artifacts (`bitworld/runtime` `RuntimeConfig`, as the starter): replay JSON to
`COGAME_SAVE_REPLAY_URI`, results to `COGAME_RESULTS_URI`, both before the shutdown grace starts.
The game container does **not** receive `COWORLD_TIMEOUT_SECONDS`; it assumes 1200 s and plays
inside 690 s. Results document (also embedded in the replay as the `result` record, which is what
makes the bytes self-sufficient):

```json
{"reason":"complete","endRule":"full_time","seed":774411,"finalTick":3600,"variant":"sprint",
 "names":["cogwop-metronome","cogwop-lean","cogwop-stride","cogwop-scoot"],
 "scores":[177.80,25.41,48.20,12.00],"win":[true,false,false,false],
 "distance_m":[100.0,23.41,46.2,12.0],"time_s":[48.20,null,null,null],"falls":[0,1,1,1],
 "saves":[2,0,1,0],"max_speed_mps":[3.1,1.9,2.4,1.1],"splits_s":[[9.9,23.4,36.1],[null,null,null],
 [null,null,null],[null,null,null]],"runner":[0,1,2,3],"role":["whole","whole","whole","whole"],
 "selfPlay":[false,false,false,false],"llmTurns":[60,60,0,0],"fallbackTurns":[0,2,0,0]}
```

`names` carries the spectator-side policy labels (never shown to a seat); every array is one entry
per slot, length `num_agents`, which `docker_smoke.sh` asserts.

## Viewer

**All four viewer files come from `Metta-AI/coworld-ctf` and nothing else** —
`replay-viewer/config.nims`, the wasm entry `.nim`, `static_replay*.js`, `index.html`. Splicing one
starter's emscripten bootstrap (`MODULARIZE`/`EXPORT_NAME`) onto another's `onRuntimeInitialized`
shell deadlocks the viewer silently with every asset at 200 (cogame-lantern, 2026-08-23).

| bundle file | source (all `coworld-ctf`) | change |
|---|---|---|
| `replay-viewer/config.nims` | `replay-viewer/config.nims` | exports renamed `_cogwop_*`; **`--preload-file` dropped** (the module reads no files ⇒ no `.data`, ~1 MB bundle not 22 MB); `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web,worker,node` kept verbatim, for the reasons its own comments give |
| `replay-viewer/cogwop_replay.nim` | `replay-viewer/ctf_replay.nim` | exports renamed: `cogwop_load_replay`, `cogwop_frame`, `cogwop_input`, `cogwop_packet_ptr/len`, `cogwop_mismatch_tick`, `cogwop_error_ptr/len`, `cogwop_stage_ptr/len`, `cogwop_game_version_ptr/len`; keeps the stage-note buffer and `emscripten_exit_with_live_runtime()` (`:361-374`), without which Nim's main frees every global and playback runs on freed memory |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `replay-viewer/*` | ids and `_ctf_*` renamed; `importScripts('./wire_constants.js','./cogwop_core.js','./cogwop_replay.js')`; factory `self.CogwopCore.create({…})`; `frameMs = 1000/30` (30 Hz sim ⇒ real-time playback) |
| `index.html` | `client/replay_broadcast.html` | built by the hook with the starter's three sed substitutions (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE -->` → `static_replay.js`), as `Dockerfile.replay-viewer` does today |

The shell sets **`data-replay-loaded="true"` on `<html>` at its first drawn frame**
(`static_replay.js:205`) and **`data-replay-error` on failure** (`:36`). One deviation: `markReady()`
runs **only** in the `loaded` branch, right after that attribute is set — the `firstFrame` branch's
`markReady()` (`:183`) is removed, so the `coworld-replay` bridge can never post `ready` before the
attribute exists (chorus `3c11c953`, 2026-08-24).

Build hook `tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, forked from the
starter's: keeps the `mkdir -p "$(dirname …)"` before the containment check (ecos 2026-08-23 —
`coworld build` pre-creates that parent, CI does not) and drops the sim-sources stamp, because **the
bundle is never committed** (`.gitignore`d; `coworld build` and `ci.yml` rebuild it), which removes
the committed-bundle staleness class.

### Chrome provenance

* `client/chrome_common.js` is **copied byte-for-byte**. Every id it touches stays in the page:
  `btn-play`, `btn-loop`, `btn-skip`, `btn-spoilers`, `clock`, `clock-caption`, `clock-time`,
  `ffwd-chip`, `ffwd-mini`, `lulls`, `momentum`, `scrub`, `scrub-fill`, `scrub-head`, `scrub-win`,
  `speedchips`, `tick-clock`, `transport`, `win-chip`.
* `client/replay_broadcast.html` is **the starter's page with a game block appended** — never a
  rewrite reusing its ids (cogame-gridlock, 2026-08-23). Also kept verbatim: `#chrome`, `#board`,
  `#viewport`, `#stage`, `#status`, `#endcard` and its layout, `#grain`, `#lightpool`,
  `#bannerlane`, `#lane-l`, `#lane-r`, `#minimap`, `#minimap-canvas`, `#viewpanel`, `#zoombar`,
  `#zoom-in/-out/-slider/-read`, `#mmwarn`, and `relayout()` (`replay_broadcast.html:8811-8896`).
* **Removed, with their dedicated inline blocks** (paintbot surfaces with no cogwop meaning):
  `#lockerroom`, `#lk-bg`, `#lk-art`, `#lk-sprites`, `#lk-cap`; `#fpv`, `#fpv-canvas`, `#fpv-hud`,
  `#fpv-hp`, `#fpv-cap`, `#fpv-name`, `#fpv-gear`, `#fpv-grip`, `#fpv-map`, `#fpv-map-canvas`;
  `#commsdock`, `#commsFeed`, `#commsLive`; `#huddleStage`, `#huddleStageClose`, `#huddlePanel`,
  `#huddleFeed`, `#huddleLines`, `#huddleHead`, `#huddleChip`, `#huddleClose`, `#huddleUnread`;
  `#voteStage`, `#voteGrid`, `#voteNote`; `#killfeed` (replaced by the game block's `#feed`);
  `#gloryPops`, `#mg-splash`, `#mg-num`, `#mg-line`, `#povBadge`, `#br-rail-head`, `#kickoffLine`,
  `#ec-glory-hero-num`, `#ec-hero-duo`, `#ec-hero-line`, `#ec-hero-name`, `#ec-mvp-line`,
  `#ec-splat`. Residual references must be null-guarded; the `wasm-viewer` job is the proof.
* Game-block functions are prefixed `cogwop…` (`cogwopMarkRaceBeat`, not `markBeat`): a game-block
  `function markBeat` hoists over the chrome alias `var markBeat = C.markBeat` and silently kills
  the scrubber beats (tandem, 2026-08-23); `tests/test_chrome_scope.nim` greps the alias list.
* Transport rules, inherited and asserted: `--band`/`--hudscale` set on `:root` by `relayout()`
  only; **no overlay in the transport band**; `#endcard` stops at `var(--band)` (`:2395`) and every
  seek dismisses it; scrubber beats are **clickable labelled `<button>`s** with a CSS class for
  **every** kind emitted: `start`, `split`, `hurdle`, `save`, `fall`, `finish`, `raceover`.

### `#viewpanel`: kept, and why

The board is 100 m and the frame shows ~14 m, so it is far larger than the frame — the condition
under which zoom bar and minimap stay. Both are repurposed: the **minimap becomes a track strip**
(the whole 100 m, one row per lane, a dot per runner, the hurdle tick at 50 m, split ticks at
25/50/75 m, the finish gantry — the only place the whole race reads at once), and the **zoom bar
drives the camera**, 0.6× (23 m in frame) … 2.0× (7 m), default 1.0× (14 m). The camera is a side-on
dolly locked to the leading live runner's hip x with a ±1.5 m dead zone, clamped to `[6 m, 100 m]`:
pull out to read the gaps, push in on a fall.

### What it draws

Lanes are a shallow receding stack — lane *k* offset `+0.55 m × k` vertically, scaled `1 − 0.05 k`,
lane 0 nearest and drawn last: the geometry of a telephoto side-on broadcast, so runners never
occupy the same pixels.

* **Track**: red tartan with white lane lines, 10 m distance boards, start blocks, the hurdle at
  50 m, the finish gantry and clock; parallax stands whose crowd rises on `fall` and `finish`;
  floodlight pylons; golden-hour sky.
* **Runner**: lane-coloured singlet, capsule limbs from the nine particles, head with a bib
  number, shoes, hip shadow, dust puff on a fall, red rim light at `wobble ≥ 0.75`.
* **Scorebug**, one plate per lane: bib colour, alias, policy name (spectator-side), `42.8 m`,
  `2.4 m/s`, status `RUN`/`FALL`/`FIN`, wobble bar, and **four lit key squares Q W O P** showing
  which muscles fired this tick — in tandem Q/W tinted the thighs seat's colour, O/P the calves':
  the whole tandem story in one widget.
* **Feed** (`#feed`, right rail): splits, hurdle clears/clips, saves, falls, overtakes, finishes
  and each seat's `note`, newest first; **splits table** below, 25/50/75 m per lane.
* **Clock**: race clock `0:14.2` from `tick/30` into `#clock-time`; `#tick-clock` keeps its tick
  readout. **Photo finish**: in the last 10 m the camera locks to the line and the winning crossing
  is held 1.0 s with the gap in metres.
* **Endcard**: per runner distance, time, falls, saves, max speed, splits; in tandem a **blame
  bar** per fall splitting the key-press *edges* of the 15 ticks before it between the seats.
  Headline into `#ec-headline`, rule into `#ec-wincond`.

Legibility at **360 px** wide (the featured-match iframe): at default zoom a 1.70 m runner is ~44 px
tall and lanes sit 14 px apart; `.plate-name` gets `flex: 1 1 auto; min-width: 3.2em`, labels hide
under 640 px, distances read `42.8 m` — never fixed-point units, never ticks. Every world-space
string (bib numbers, distance boards) is **culled when its anchor leaves the camera rect**, so
nothing is drawn off-canvas and `--strict-text-bounds` stays on with `canvas_text.never_inside` = 0.

## Packaging

| file | content |
|---|---|
| `compose.yaml` | one service **`cogwop`** (service name = coworld name ⇒ placeholder `{{COGWOP_IMAGE}}`; `{{GAME_IMAGE}}` is not a thing — lantern 0.1.0), `image: coworld-cogwop:latest`, `platform: linux/amd64`, `build: {context: ., dockerfile: Dockerfile, network: host}` |
| `Dockerfile` | one image, two binaries `/bin/cogwop`, `/bin/cogwop-player`; nimby-pinned Nim 2.2.4 + `nimby.lock`, as the starter's build stage |
| `Dockerfile.replay-viewer` | emscripten/emsdk 4.0.15 builder, forked from the starter's minus the paintbot asset copies |
| `coworld_manifest_template.json` | the manifest below: `{{COGWOP_IMAGE}}`, both variants, cert fixture, docs, protocols |
| `tools/build_replay_viewer.sh` | the `coworld build` hook (chmod +x) |
| `tools/ci/docker_smoke.sh` | template with `<slug>`=`cogwop`, `<IMAGE>`=`coworld-cogwop`, `<SEATS>`=**4** (chmod +x) |
| `tools/ci/viewer_smoke.mjs` | copied verbatim, no substitutions |
| `tools/ci/policies.json` | the four policies of §Decisions; champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` |
| `.github/workflows/{ci,coworld-release,coworld-submit}.yml` | from `templates/`; `ci.yml`'s viewer step gains `--soak 10`, the release certify step `--timeout-seconds 300` |

Manifest (coworld 0.1.42 upload contract): `$schema`, top-level `tags`
`["physics","locomotion","coordination","ragdoll","race"]`, `episode_timeout_minutes: 20`,
`game.name: "cogwop"`, `game.owner`, `game.description`; **no** `game.display_name`, **no** top-level
`version`. `game.runnable: {type:"game", image:"{{COGWOP_IMAGE}}", env:[{ANTHROPIC_API_KEY_URI:
"secret://coworld/cogwop/anthropic_api_key"}]}` with **no** `resources.limits` (continuous-control
0.1.1). `game.replay_viewer: {"bundle":"static-replay-viewer"}`, no `replay_compression`.
`game.docs = {"readme":{"type":"text","value":…},"pages":[{"id":"rules",…},{"id":"protocol",…}]}`;
**`game.protocols` carries both `player` and `global`**, each `{"type":"text","value":…}`.
`game.config_schema` is a real JSON Schema with **`minItems`/`maxItems` on every array property**
(`players` 2…8, `tokens` 2…8 — the runner injects `tokens`, so no `game_config` carries a literal
one); `game.results_schema` matches §Server's document. Bundled `player[]`: one entry
`{"id":"baseline","type":"player","name":"baseline","description":…,"image":"{{COGWOP_IMAGE}}",
"run":["/bin/cogwop-player"],"resources":{"requests":{"cpu":"100m","memory":"64Mi"},
"limits":{"cpu":"1"}}}` (cpu limit minimum `"1"` — pistonball 0.1.1); with no env it plays `stride`.

Variants — **`num_agents` is 4 inside each variant's `game_config`, never at the variant's top
level** (`CoworldVariant` is `additionalProperties: false`; goofspiel-oshi-zumo 0.1.0):

| variant | `description` | `game_config` |
|---|---|---|
| `sprint` | "Four ragdoll sprinters, one cog each, four keys, 100 m." | `{"num_agents": 4, "variantId":"sprint", "runners":4, "seatsPerRunner":1, "windowTicks":60, "maxTurns":60, "minEpisodeTicks":900, "trackLengthCm":10000, "hurdleAtCm":5000, "hurdleHeightCm":30, "attempt1Ms":6000, "retryMs":4000, "turnBudgetMs":11000, "turnSpacingMsPerLlmSeat":2500, "wallClockBudgetSeconds":690, "joinTimeoutSeconds":60, "maxOutputTokens":900, "seed":0, "players":[{…}×4]}` |
| `tandem` | "Two sprinters, four cogs: one owns the thighs, one the calves, and they cannot talk." | the same with `"variantId":"tandem"`, `"runners":2`, `"seatsPerRunner":2`, **`"num_agents": 4`** |

Certification fixture = **`sprint`** (no cross-seat coupling, so a cert failure can only be the
sim, the server or the manifest). `certification.game_config` is the `sprint` config with
`"num_agents": 4` and four `players`; `certification.players` is four `{"player_id":"baseline"}`
rows — equal lengths, `docker_smoke.sh` hard-checks both (`SEAT-COUNT FAIL:`). All four seats play
`stride` with no credentials: 3600 ticks of integer physics in ~2 s plus the 20 s shutdown grace
≈ 25 s, inside `coworld certify`'s 60 s default.

## Tests

Nim tests under `tests/`, run by `ci.yml`'s `test` job in debug **and** release.

| test | asserts |
|---|---|
| `test_fixed.nim` | `fpMul`/`fpDiv` truncation on negatives, `fpSqrt` against a fixed table, `xorshift64s` first 16 outputs pinned |
| `test_no_floats.nim` | no `float`/`sqrt(`/`sin(`/`cos(`/`atan2`/`pow(`/`shr ` token in `src/cogwop/{fixed,body,sim,sim_types}.nim` |
| `test_body.nim` | bone lengths within ±1 mm after 8 iterations; no knee hyperextension; hip–foot in `[0.30,0.895]`; magnitude clamps never bind over 3600 ticks of `flail` × 16 seeds |
| `test_contacts.nim` | fall fires for head/neck/hip/hand and nothing else; hurdle push-out per face; finish at hip ≥ 100 m; start-jitter bound |
| `test_determinism.nim` | same seed + schedules ⇒ identical hash chain over 3600 ticks, twice in-process and once after a config round-trip |
| `test_schedule.nim` | the §Reply-schema repair table row by row (short sum, long sum, 13 entries, unowned keys, junk ticks, empty plan, prose- and fence-wrapped JSON); rune-boundary `note` truncation at 120 |
| `test_baselines.nim` | **bounded-orders/legality**: 3 baselines × both roles × 64 windows — ≤ 12 segments, ticks 1…60 summing to exactly 60, only owned keys; plus the strength order and `stride ≥ 20 m` |
| `test_tuning.nim` | shipped `stride` constants equal `tools/ci/baseline_tuning.json` |
| `test_scoring.nim` | every outcome: finish, fall at 0 m, fall mid-track, full time, deadline stop, 4-way tie, tandem shared score and `win`, `selfPlay` detection |
| `test_episode_e2e.nim` | a full scripted episode writes replay + results; `reason ∈ {complete, deadline}`; every results array has length `num_agents` |
| `test_replay_roundtrip.nim` | record → re-derive parity **for every end reason** (`all_down`, `full_time`, `wall_clock`) with the stop record applied by the same proc on both paths (particle-worlds scar); fixtures carry the current `GameVersion` |
| `test_replay_utf8.nim` | replay bytes parse under a **strict** UTF-8 JSON parser, with a worst-case 120-rune multi-byte note and a 160-rune `fallback.detail`; size < 512 KB |
| `test_manifest.nim` | `num_agents` = 4 in both variants' `game_config` and in `certification.game_config`, absent at variant top level; `len(certification.players)` = 4; `minItems`/`maxItems` on every `config_schema` array; `protocols.player` + `.global`; `docs.readme` + pages; no `tokens` in any `game_config`; no `runnable.resources.limits`; player cpu limit `"1"`; `replay_viewer.bundle`; image placeholder matches the compose service |
| `test_cert_timing.nim` | fixture ticks ÷ 30 + grace < 50 s |
| `test_chrome_scope.nim` | no game-block function shadows a `chrome_common.js` alias; `chrome_common.js` sha256 equals the starter's |
| `test_wasm_parity` (`tools/wasm_replay_smoke.cjs`, `wasm-viewer` job) | the emitted `cogwop_replay.js`, run under **node**, re-derives a recorded episode to the **same hash chain** as the native sim — the proof they are bit-identical |

CI: `test` → `docker-smoke` (build image, `tools/ci/docker_smoke.sh coworld-cogwop:ci`, assert
`results.json`/`replay.json`, upload the `smoke-replay` artifact, grep the game log for
`seat_unregistered`) → `wasm-viewer` (`needs: docker-smoke`; build the bundle, then **execute** it:
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json
--timeout 90 --soak 10 --strict-text-bounds`, and run the same harness against
`tools/ci/renderer_fixture.html` — the shipped `index.html` in an iframe with the wasm entry shimmed
and full-cap notes on every seat at several canvas sizes, because a credential-free smoke replay
carries zero LLM text, cogchemists 2026-08-24).

## Out of scope (v1)

1. **The `relay` variant** (4 × 25 m with a baton handoff) — a third variant doubles the manifest,
   scoring and viewer work before `sprint` and `tandem` have ranked.
2. **Everything 3D**: polyworld, the 3D articulated body, lateral falls, `lateral_stiffness`, the
   chargen skeleton and its character art, 3D terrain.
3. **The `trail` and `alpine` courses**, all seeded terrain, grades, mud, snow, bridges, water.
4. **The broadcast camera director**: ten named rigs, look-ahead cutting, iso cams, spidercam,
   drone, crowd cam, slit-scan camera, slow-mo instant replays, PiP, split screen. v1 has one
   side-on tracking camera with zoom plus the photo-finish hold.
5. **The browser human-playable build and the human leaderboard.**
6. **Per-tick pose recording** — v1 records inputs and re-derives (§Sim module).
7. **Articulated arms** — one hand particle per arm; arms are a fall sensor and a counterweight.
8. **Inter-runner collision, drafting, lane interference** — lanes are independent by rule.
9. **A second hurdle** (the idea's 40 m / 70 m pair) — one at 50 m.
10. **Any RL training, gradient update or policy learning** — the platform asks a container for a
    decision; it does not train.
11. **Replay gzip** (`replay_compression`) — plain UTF-8 JSON keeps SPEC check 4 a one-line fetch.
12. **Any Foddy asset, string, sprite, sound or line of code, and any code or data from `qwop-ai`,
    `RL-QWOP` or `qwop_RL`** — permanent, not a v1 cut.
