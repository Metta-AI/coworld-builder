# Source idea (verbatim) — Asana 1219799551688527

https://app.asana.com/1/1209016784099267/project/1217704774784096/task/1219799551688527

## Title

37 QWOP — four keys, two legs, one hundred metres; race solo, or share one body with a stranger

## Notes

UPDATE 2026-10-22 (daveey): build on Metta-AI/polyworld and make it TRUE 3D. That means a 3D articulated runner on 3D terrain, a real race track through a designed landscape, and a broadcast camera director that flies around to show different angles and puts falls and near-falls first. The sections TRACK & TERRAIN, PHYSICS and BROADCAST COVERAGE below are the spec. They replace any 2D/Box2D wording in the rest of the card.

Bennett Foddy's QWOP (2008, Flash; http://www.foddy.net/Athletics.html) as a coworld. An Olympic sprinter on a 100 m track, controlled only by four binary muscle keys: Q/W drive the thighs (Q = right thigh forward and left back, W = the reverse) and O/P drive the calves the same way. A fall (head, torso or hands touch the ground) ends the run at the distance reached. Deliberately awful controls are both the joke and the skill: an untrained human typically needs hours to reach 100 m (Mike Boyd took ~8 h), and the speedrun record is 45.53 s (kurodo1916, 2022). The 2012 sequel 2QWOP added head-to-head racing.

Why it is a coworld and not just another locomotion env: the marquee mode splits ONE runner across TWO cogs. Seat A owns Q/W (thighs), seat B owns O/P (calves). Neither can run alone. The gait is a coordination equilibrium found through the body, not through words. This is the Tandem (card 15) idea in its purest physical form, with a far more legible spectator story.

Modes (manifest variants):
- `sprint`: 4 lanes, 4 cogs, each cog controls a whole runner, simultaneous race. Ranking league.
- `tandem`: 2 lanes, 4 cogs. Each runner is a cross-author pair (thighs seat + calves seat). Score is shared per runner; ranked by cross-play mean over stranger partners.
- `relay` (stretch): 4×25 m with a baton handoff when the next runner's hand passes the line; a fall costs only your leg.
- Course variants (see TRACK & TERRAIN): `stadium` (flat, default and certification), `trail`, `alpine`.

TRACK & TERRAIN (polyworld quadterrain + terrain tiles/stamps + props + water)
- `stadium`: an 8-lane 100 m straight on a red tartan surface with lane lines, distance boards every 10 m, starting blocks, two hurdles (40 m and 70 m), and a finish gantry with a clock. Packed stands on one side; a crowd of animated low-poly spectators that rise and react on beats. The stadium sits in a valley at golden hour: mountains, pine forest, a lake behind the back straight. The far side is open so the scenery reads in wide shots.
- `trail`: a 100 m cross-country course over polyworld heightfield terrain, with rolling rises and dips (±6% grade), a mud patch (low friction), a short timber bridge over a stream, and a gravel run-out. Same lane count, with lanes as painted tape.
- `alpine`: a downhill-then-uphill course with one banked bend, snow (low friction) and a cliff-edge section where a sideways fall looks dangerous (it is cosmetic: a safety net catches the runner and the run ends).
- Terrain is seeded per match within each course. Small height noise and prop placement change; lane lengths and grades stay identical across lanes, so no lane has an advantage.

PHYSICS
- Polyworld today has planar circle bodies (bodies.nim) and skinned characters (chargen); it has NO articulated rigid-body physics. Add a small deterministic 3D articulated-body sim. Roughly 12 bodies: pelvis, torso, head, upper/lower arms, thighs, shins, feet. Use hinge knees, ball-and-socket hips with motor torque only on flexion/extension, passive hip abduction and ankle springs, and foot–heightfield contact with friction from the terrain material.
- True 3D means runners can fall sideways and twist as well as fall forward or back. That is good for drama. Expose a `lateral_stiffness` knob, tuned so that the `stadium` course is about as hard as the original and `alpine` is harder.
- The server is authoritative at a fixed 60 Hz physics step and a 30 Hz policy tick. The replay records per-tick quantized body transforms, so the browser viewer renders them directly and never re-simulates. Cross-platform float determinism is then not required for replays, only for server reruns.
- Drive the chargen skeleton from the physics bodies, so runners use polyworld's character art (lane colours, numbered bibs).

Seats: 4 (sprint: 4 runners; tandem: 2 runners × 2 seats)
Motive: sprint is a zero-sum race; tandem is cooperative within the runner and zero-sum between runners.
Policy interface: RL. Obs = joint angles and angular velocities, torso orientation (pitch/roll/yaw) and height, foot contacts, local terrain slope and material under each foot, distance, and (tandem) the partner's last key state. Action = 2 binary keys per seat (sprint: 4).
Fills gap: binary-action 3D physical locomotion with a famous human baseline; physical coordination through a shared body with no channel at all (no pings, no text); human-playable in the browser with the same four keys.
Integrity (anti-collusion): tandem partners are cross-author strangers drawn per match. There is no message channel, so the only signal is the shared body's state. Thighs vs calves assignment is randomized per match. Sprint lanes cannot interact, so a cog cannot throw the race to a friend for gain. Report the cross-play vs self-play gap for tandem.

Scripted baselines: `flail` (random keys), `scoot` (the classic knee-scoot: hold W+O and tap; slow but stable), `stride` (a hand-tuned open-loop gait cycle). Human leaderboard: humans play the same build in the browser and are seated against cogs.

BROADCAST COVERAGE (polyworld actioncam.nim + directors.nim, extended)
Model it on a TV athletics/F1 broadcast. Every camera is a named rig the director cuts between. The director runs on the full replay, so it can LOOK AHEAD: it knows every fall before it happens and cuts to that runner 1.5–2 s early, so the fall is always on screen. For live/human play, use the instability score below as the predictor instead.

Camera rigs:
1. Rail cam: a low dolly on a rail beside the track that matches the leader's speed. This is the signature 100 m shot, all lanes in profile.
2. Head-on telephoto from behind the finish line: compresses the lanes so the race order and gaps read instantly.
3. Jib/crane: a sweeping high-to-low move at the start and finish.
4. Drone/aerial: a slow orbit over the stadium and terrain for the opening, the scenic establishing shot and transitions; it chases along the course on `trail`/`alpine`.
5. Spidercam: an overhead cable cam that tracks the pack from above and behind.
6. Hurdle cams: low ground cameras at each hurdle that fire as a runner approaches.
7. Runner cams: a chest-mounted POV per runner, plus a trailing steadicam behind and in front. Used for falls and tandem drama.
8. Iso cams: every runner is recorded from rail + head-on + POV for the replay package.
9. Photo-finish slit camera at the line (the classic slit-scan strip image) for close finishes.
10. Crowd cam: a reaction shot of the stands after big falls and the finish.

Director priorities (strongest first; an interrupt can cut in while another shot is held):
- FALL (critical, interrupts anything): cut 1.5–2 s before the fall to the runner cam or a tight rail shot, hold through the ragdoll and the dust, then a crowd groan.
- NEAR-FALL / SAVE (major): the instability score crosses a threshold and the runner recovers. Hold a tight shot; label it "SAVE" on screen.
- Hurdle approach and clip; overtake or lead change; two runners within 0.5 m ("battle" two-shot).
- Finish: always locked to the head-on + slit cam in the last 10 m, whatever else is happening. Never miss the finish.
- Leader cruise / scenic aerial when nothing is happening (overview at least every 30 s, as directors.nim already does).

Instability score (per runner, per tick): torso tilt from vertical, angular velocity, centre of mass outside the foot support polygon, and head height falling. It drives the near-fall detection, the live pre-roll, a per-runner "wobble meter" on screen, and a subtle red rim light on runners about to go.

Replay package: after every fall, run a 4–6 s slow-mo instant replay from 2–3 iso angles (runner cam, rail, aerial) while a picture-in-picture box keeps the live race on screen. If two falls overlap, use a split screen. At the end, a "fall of the race" highlight plays before the endcard.

On-screen graphics: lane order ticker, distance and speed per runner, gap to the leader, split times at 25/50/75 m, the four lit key squares under each runner (tandem: thigh keys tinted in seat A's colour, calf keys in seat B's), the wobble meter, and the race clock. Endcard: distance, time, falls, saves, max speed, and (tandem) a blame bar showing which seat's key presses preceded each fall.

New director events (add to EventKind alongside the combat events): FallEvent, NearFallEvent, SaveEvent, HurdleEvent, OvertakeEvent, FinishEvent.

RL references: https://github.com/juanto121/qwop-ai (DQN/DDQN), https://github.com/drakesvoboda/RL-QWOP (game internals as a gym env, limb pos/angle state), https://github.com/yatshunlee/qwop_RL. Wesley Liao's agent ran 47.34 s, beating the 48.34 s human best at the time (2021).
Licence note: QWOP is Foddy's. Do NOT ship his assets or code. Reimplement the physics and art from scratch and call the world `cogwop` (or similar).

Build owner: CoMax Paperclip team ($1,000 budget granted by daveey, 2026-10-22; ask daveey for more if the 3D scope needs it).

Full report: https://claude.ai/code/artifact/e80f2ed8-d5a3-4fbb-b6c2-276d9cac133c
