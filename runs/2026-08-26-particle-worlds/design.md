# cogame-particle-worlds — design note (2026-08-26, paintbot lineage)

`Metta-AI/cogame-particle-worlds` is a **four-seat continuous-physics coworld with a nine-value
symbolic radio**: four coloured particles glide on a bounded 1235 × 659 field around four coloured
landmarks, and across one episode they play four MPE scenarios back to back — cover the landmarks
together, hide a goal from an adversary, smuggle a colour past two eavesdroppers, and run a
three-on-one chase. Moving is nearly free; **the only thing a seat can say to another seat is one
symbol out of nine, once every 4.5 seconds.** It is forked from **`Metta-AI/coworld-ctf`**
(paintbot), read at its read-only mount `/workspace/starters/coworld-ctf`. **Every convention there
holds here unless this note says otherwise** — the 24 Hz tick loop, the Sprite v1 button-mask input,
the fixed-point integer motion model (`motionScale` 256, `carryX`/`carryY` sub-pixel accumulators,
`applyMomentumAxis` wall-slide and `bouncePlayers` restitution), the per-pixel wall mask and the
`mapSpec` round-trip, the `COWLDCTF` replay codec with its per-tick `gameHash` chain and
`ReplayKeyframeTicks`/lull-span machinery, the seat/cog split and `cogAlias` two-name-space rule, the
whole server-side decision layer (`src/ctf/{decide,directives,control,baselines,llm}.nim` — one
parallel batch per turn, two bounded deadlines, `turnSpacingMs` rate floor, budget guard, tolerant
parsing, rune caps, scripted fallback), the mummy server and its `COGAME_*` runtime contract, the
broadcast chrome (`client/replay_broadcast.html` + `client/chrome_common.js` +
`client/broadcast_core.js`), the emscripten static replay bundle (`replay-viewer/`,
`Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`) and the `GameVersion` changelog
discipline are all inherited.

**Starter choice, in one line:** particle-worlds is a **real-time game loop whose rules are written
for this coworld** — the paintbot row of the starter table — because the paintbot starter already
ships, tested, every layer this game needs except the landmark rules: an integer fixed-point
continuous-motion model with collision, a server-side per-turn LLM directive layer with a scripted
fallback, a deterministic control layer that turns one directive into per-tick actuator masks, a
10-character shout channel with speech bubbles (which becomes the symbol radio), and a wasm viewer
that re-derives every frame from the recorded masks. It is deliberately **not** the `cogame-moba`
row: that row is for **bit-exact** ports of an existing C/RL environment, and this is not one —
PettingZoo/JaxMARL MPE is float64 world-unit physics with per-step vector actions, and this is an
integer-pixel, turn-directive coworld. What is carried over is MPE's *shape* (particles, landmarks,
a discrete comm channel, and the four scenario motives), not its numerics.

**Source idea, verbatim:**

> MPE Particle Worlds — spread, tag, speaker-listener and world-comm: cheap physics, expensive words.
>
> Port of the Multi-Agent Particle Environment (OpenAI MPE; PettingZoo mpe; JaxMARL) as one coworld with scenario modes: simple_spread (N agents cover N landmarks, penalised for collisions), simple_tag (slow good agents vs fast adversaries), simple_adversary (one agent must mislead an adversary about which landmark is the goal), simple_speaker_listener (speaker sees the goal colour, listener moves — communication through a discrete channel), simple_reference (both must talk), simple_world_comm (leader adversary broadcasts to followers, forests hide agents), simple_push, simple_crypto (encrypt a message the eavesdropper can't read). Continuous 2D physics with discrete/continuous moves plus a small symbolic comm channel.
>
> Seats: 2-6 by scenario
> Motive: mixed by scenario (coop / competitive / deception / emergent comms)
> Policy interface: per-tick force + optional comm token; LLM variant gives the comm channel as text
> Fills gap: emergent-communication benchmarks — simple_crypto (encryption under an eavesdropper) and simple_adversary (deception) have no counterpart on the site
> Integrity (anti-collusion): scenario and landmark layout seeded; anonymous aliases; comm logged.
>
> Replay plan (watchability): bubbles over agents show the comm symbol; landmark coverage heatmap; in crypto, show what the eavesdropper decoded.
>
> Source: github.com/openai/multiagent-particle-envs; PettingZoo mpe; JaxMARL MPE.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How particle-worlds satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a real-time continuous-physics loop with new rules; the motion model, the directive layer, the replay codec and the wasm viewer fork rather than get rewritten. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-particle-worlds`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=drifter` / `PLAYER_SCRIPTED=beeline` (both fillers); one image `coworld-particle-worlds`, player entrypoint `/bin/particle-worlds-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` and `Dockerfile.replay-viewer` kept; the **same Nim sim module** compiles into `replay-viewer/mpe_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` byte-for-byte, `client/broadcast_core.js` byte-for-byte but for one identifier, `client/replay_broadcast.html` = the starter's page **with one appended game block**; particles are the shipped `data/soldier_{red,blue,green,yellow}*` sprites on the `data/rig_real/*` rigs; landmarks and the symbol bubbles are baked at startup by the starter's own pixie compositor. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | Prompts, observations, symbol bubbles and sprite labels carry only `RED-alpha`, `BLUE-alpha`, `GREEN-alpha`, `YELLOW-alpha` (the starter's unmodified `cogAlias`); real policy names appear only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (`tests/test_identity_privacy.nim`, extended). (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | expected 420 s / absolute worst 585 s against a 720 s budget; a 690 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** in variants `default`, `coop`, `deception`, `comms`, `chase` **and** in `certification.game_config`; `<SEATS>` = 4 in `tools/ci/docker_smoke.sh`. (§Packaging) |

Nothing in this note is left open: there is no `OPEN` section. Every reading the idea leaves loose —
which scenarios ship, how 2-to-6-seat scenarios become one fixed roster, whether the good agents in
`tag` are the fast ones or the slow ones, how a mixed-motive episode is scored on one [0, 1] scale —
is a rail the designer decides, and each is decided below with its reason.

---

## The game

**Four particles, four landmarks, four scenarios, one radio that can say nine things.** An episode is
four rounds of 45 seconds. The board and the seats are the same in every round; what changes is what
the round rewards and who is told what. Physics is nearly free — a particle accelerates, drifts and
bounces, and it can reach any landmark in a few seconds. Information is not: the *only* channel from
one seat to another is a single symbol out of `{-, A, B, C, D, E, F, G, H}`, chosen once every 4.5
seconds and broadcast to the whole field. That asymmetry is the game.

### Seats, colours, aliases

**`num_agents` = 4. One seat = one particle.** No seat drives more than one body and no body is
uncommanded.

| Seat | Team / colour | Alias (the only name in the game) | Sprite |
|---|---|---|---|
| 0 | red | `RED-alpha` | `data/soldier_red*` on `data/rig_real/red` |
| 1 | blue | `BLUE-alpha` | `data/soldier_blue*` on `data/rig_real/blue` |
| 2 | green | `GREEN-alpha` | `data/soldier_green*` on `data/rig_real/green` |
| 3 | yellow | `YELLOW-alpha` | `data/soldier_yellow*` on `data/rig_real/yellow` |

`teams: 4`, `cogsPerTeam: 1`, one seat per team, so the starter's `cogAlias` (`teamText` + `-` +
`IdentityNames[0]`) needs **no edit at all** and every particle gets its own shipped colour family.
The four teams are colours, not sides: who is allied with whom is a property of the **round**, not of
the team, and the scoring section says so in equations.

**Why 4 and how the 2-to-6-seat scenario family collapses onto it.** The platform schedules one fixed
roster per coworld — a ranged seat count schedules zero episodes — so the seat count is the first
thing this note has to pin, and it pins **4**. MPE's scenarios want 2 (`simple_speaker_listener`,
`simple_reference`, `simple_push`), 3 (`simple_crypto`, `simple_adversary` at its default), 4
(`simple_spread` at N = 4, `simple_tag` at 1 good + 3 adversaries) or 6 (`simple_world_comm`).
**Four is the count with the largest family of scenarios that generalise onto it without changing
their character**, and this coworld ships exactly that family, with a **per-round, per-episode seeded
role assignment**:

| Round | Mode | MPE ancestor | Roles at 4 seats |
|---|---|---|---|
| 1 | `spread` | `simple_spread`, N = 4 | four symmetric cooperators, penalised for collisions — verbatim |
| 2 | `deceive` | `simple_adversary` | 1 adversary + **3** good agents (PZ's default is 2 good; the scenario is parameterised in N and 3 is a legal instance) |
| 3 | `crypto` | `simple_crypto` | Alice (speaker) + Bob (listener) + **two** eavesdroppers, Eve-1 and Eve-2 (PZ ships one; a second eavesdropper is the natural 4-seat instance and makes the channel strictly harder, which is the point) |
| 4 | `tag` | `simple_tag` | 1 evader + 3 pursuers — verbatim |

`simple_speaker_listener`, `simple_reference`, `simple_world_comm` and `simple_push` are **out of
scope for v1** (§Out of scope) precisely because they seat 2 or 6 and a 4-seat rewrite would be a
different game rather than an instance of theirs. Their *mechanic* — a speaker who sees a goal and a
listener who must move — is not lost: `crypto` is a speaker-listener game with two eavesdroppers
bolted on, and every seat in every round can both speak and hear, which is `simple_reference`'s
"both must talk" property.

**Roles rotate, so nobody is stuck with the cheap seat.** One seeded permutation `perm[0..3]` of
`[0, 1, 2, 3]` is drawn per episode from the config seed. In round `r` (1-based) seat `s` holds
**role index** `roleIndex[s][r] = (perm[s] + r) mod 4`. Over the four rounds each seat therefore
holds each of the four role indices **exactly once**. Each mode reads the index the same way:

| Role index | `spread` | `deceive` | `crypto` | `tag` |
|---|---|---|---|---|
| 0 | cooperator (spawn slot 0) | **adversary** | **Alice** (speaker, anchored) | **evader** (fast) |
| 1 | cooperator (spawn slot 1) | good agent | **Bob** (listener) | pursuer |
| 2 | cooperator (spawn slot 2) | good agent | **Eve-1** | pursuer |
| 3 | cooperator (spawn slot 3) | good agent | **Eve-2** | pursuer |

Role bundles differ between seats and are seeded, so bundle luck is i.i.d. across episodes and the
league's Elo averages it out; the four single-mode variants (§Packaging) exist for a clean per-mode
read when that is what a spectator wants. `num_agents` is **4** everywhere: every manifest variant,
the certification fixture and `SMOKE_SEATS`.

### The field, the clock, the landmarks

`mapPath: "field"` in every variant — a **new hand-authored `mapSpec`**, `1235 × 659` map pixels,
**border walls only and no interior obstacle at all**, declaring four team anchors (one per corner)
so `teamAnchor`/`captureZone` stay defined for the starter's code that reads them. The dimensions are
**identical to the starter's `arena`** on purpose: every dimension-coupled constant — `ShoutRange`
(`MapWidth div 5` = 247 px), `boardRenderScaleFor`, the FOV grid, `relayout()`'s fit — is inherited
unchanged and untested-drift-free. MPE's plane is unbounded with a soft out-of-bounds penalty; this
field is **hard-bounded by walls** (a decided deviation: it keeps every particle on screen, which the
replay requires, and it makes `evade` a real skill instead of a straight line to infinity). The
procedural generator, the curated pool, `mapkit` and the map editor are all deleted (§Sim module).

`TargetFps = ReplayFps = 24`, **kept verbatim** (`PlaybackSpeeds`, the lull scan, `tickTime` and the
transport bar are all keyed to it).

One **round** is `maxTicks` = **1080** ticks = **45 s**. One **episode** is `maxGames` = **4** rounds.
Decision turns are `turnTicks` = **108** ticks = **4.5 s** (the starter's `DefaultTurnTicks`) →
**10 turns per round, 40 per episode**. Total playback = 4320 ticks = **180 s** at 24 fps, which
comfortably outlasts any viewer soak window (the ecos 2026-08-23 scar). The seed, the map and the
connected seats are identical across the four rounds; the sim RNG stream simply continues (no
re-seed) and `resetToLobby()` clears bodies, velocities, accumulators and the radio between rounds.

**Landmarks.** Four, `landmarkRadius` = **18 px**, drawn as coloured discs. They are **never solid**
in any mode: a particle glides over them. Their layout is **seeded** (the idea's integrity note),
redrawn at the start of every round from the sim RNG by bounded rejection sampling:

```
for i in 0 ..< 4:
  spacing = landmarkSpacingPx                      # 300
  attempts = 0
  loop:
    x = landmarkMargin + rng.rand(MapWidth  - 1 - 2*landmarkMargin)     # margin = 140
    y = landmarkMargin + rng.rand(MapHeight - 1 - 2*landmarkMargin)
    inc attempts
    if not isWall(x, y) and every placed landmark is >= spacing px away: accept
    if attempts mod 400 == 0: spacing = max(120, spacing - 20)          # always terminates
```

Landmark `i`'s **colour** is entry `i` of a seeded permutation of `["amber", "teal", "violet",
"bone"]` — a palette deliberately disjoint from the four particle colours, so a spectator never
confuses a particle with a mark. `landmarks[i]` = `(x, y, colour)` and is **hashed state**.

**Spawns.** Role index `k` spawns on the circle of radius `spawnRingPx` = **250 px** about the field
centre `(617, 329)` at `aimBrads = (64 * k + spawnOffsetBrads) mod 256`, where `spawnOffsetBrads` is
drawn per round from the RNG in `[0, 63]`; the point is snapped to the nearest walkable pixel by the
starter's `nearestOpenCell`. Velocity, carry and accumulators start at zero.

### Physics — exact, integer, and MPE-shaped

MPE integrates `p_vel = p_vel * (1 - damping) + action * accel * dt` and clamps to `max_speed`. The
starter integrates the same thing in integers but applies friction only to an *unpowered* axis. This
game wants particles that **glide**, so `applyInput` gains one named edit: **damp both axes every
tick, then add the impulse.** Per particle, per tick, in this order:

1. `velX = velX * frictionNum div frictionDen`; if `abs(velX) < stopThreshold` then `velX = 0`.
   Same for `velY`. With `frictionNum` = **192**, `frictionDen` = **256** the retention is
   0.75/tick — MPE's `damping = 0.25`, exactly. `stopThreshold` = **8** (the starter's).
2. `velX += inputX * accel(role)`, `velY += inputY * accel(role)`, where `inputX`/`inputY ∈ {-1,0,1}`
   come from the d-pad bits of this tick's mask; each axis is then clamped to `±maxSpeed(role)`.
3. Integration is the starter's `applyMomentumAxis` **unchanged**: the `carryX`/`carryY` sub-pixel
   accumulator at `motionScale` = 256, the per-pixel wall test, the slide, and `bouncePlayers` with
   `playerBouncePct` = **40** for particle-on-particle contact.

Kinematics, by role (`accel` in motion units per tick², `maxSpeed` in motion units per tick;
256 units = 1 px):

| | `accel` | `maxSpeed` | cruise (= `accel`/(1−0.75)) | px/s |
|---|---|---|---|---|
| every particle in `spread`, `deceive`, `crypto`; the **evader** in `tag` | **250** | **1100** | 1000 units = 3.91 px/tick | **94 px/s** |
| a **pursuer** in `tag` (`pursuerAccelPct` 75, `pursuerSpeedPct` 77) | **187** | **847** | 748 units = 2.92 px/tick | **70 px/s** |

The pursuer ratios are MPE `simple_tag`'s own (adversary accel 3.0 vs good 4.0 → 75 %; adversary
max_speed 1.0 vs good 1.3 → 77 %). **The idea's line "slow good agents vs fast adversaries" inverts
its own source**: in `simple_tag` the single good agent is the *faster* one and the adversaries are
the slow pack. This note follows the source, because 1-fast-evader vs 3-slow-pursuers is the game
that has a chase in it; a slow lone evader against three fast pursuers is caught in the first two
seconds and measures nothing. Decided here, logged here, not revisited.

Two deliberate, stated deviations from MPE: the per-axis speed clamp (the starter's) means a
diagonal cruise is √2 faster than an axis-aligned one — **identical for every role**, so it is a
property of the world and not an advantage; and `crypto`'s **Alice is anchored** (her d-pad bits are
ignored by the sim, as MPE's `simple_crypto` speakers are immovable). Alice's *aim* still turns, so
her sprite reads as looking at whoever she is talking to.

### The radio — nine values, global, once per turn

The **only** inter-seat channel. At each turn boundary a seat's directive carries one `symbol` from
`{"-", "A", "B", "C", "D", "E", "F", "G", "H"}`; `"-"` is silence. The symbol becomes that particle's
broadcast token for the whole 108-tick turn, is **audible to every seat regardless of distance** (the
starter's `ShoutRange` gate is bypassed for symbols — MPE's channel is global), and is drawn as a
coloured bubble over the particle. `commSymbol[cog]` and `commTurn[cog]` are recorded and rendered
but **excluded from `gameHash`**, exactly as the starter excludes `activeDirective`: nothing a
commander says may move the hash chain, and nothing about the radio touches physics.

**There is no free-text channel between seats.** The starter's `say` field is **removed from the
reply schema** (§Server §Reply schema): a 10-character English shout would let a good agent tell its
partners "the goal is the teal one" in the clear, which trivially solves `deceive` and `crypto` and
destroys the exact benchmark gap the idea exists to fill. The directive's `note` survives, but it is
**spectator-only** — it reaches the match feed and the replay and is never shown to another seat.

### Round rules and the scoring formula — one permille per seat per round

One helper, used everywhere:

```
closeness(d) = 1000 - min(1000, d * 1000 div closeScalePx)      # closeScalePx = 500
```

so a particle sitting on a mark scores 1000 and one 500 px away scores 0. All distances are
centre-to-centre in map pixels, compared as integer squared distances where a comparison is all that
is needed. Every per-tick term below is accumulated into a hashed integer and divided by the round's
tick count at round end; every round score is a **permille in [0, 1000]**.

**Round `spread`** (all four cooperate; the idea's "penalised for collisions"):

```
cover(t)       = ( sum over the 4 landmarks L of closeness(min over agents of dist(agent, L)) ) div 4
bumps[s]      += 1 for each tick in which s is within bumpPx (14 px) of any other agent
base           = sum over ticks of cover(t) div ticks
roundP[s]      = max(0, base - min(bumpPenaltyCap (250), bumps[s] * bumpPenaltyPermille (1)))
```

All four seats share `base`; only the collision debit is personal, and it is floored at 0 so **no
term is ever negative**. Four particles each parked on a different mark ≈ 950; four particles
clumped on one mark ≈ 300.

**Round `deceive`** (goal landmark index `g` drawn from the RNG; the three good agents are told `g`,
the adversary is not):

```
gc(t) = closeness(min over the 3 good agents of dist(agent, L_g))
vc(t) = closeness(dist(adversary, L_g))
goodP(t) = clamp(500 + (gc - vc) div 2, 0, 1000)      # the same value for all three good agents
advP(t)  = clamp(500 + (vc - gc) div 2, 0, 1000)
roundP[s] = mean over ticks of the seat's own term
```

`goodP + advP = 1000` on every tick where neither clamps, so the round is **zero-sum by
construction**. Good agents must cover the goal *and* keep the adversary off it — and because the
radio is public, coordinating the bait is coordinating in the clear. That is the deception.

**Round `crypto`** (goal landmark `g`, its colour `gcol`, and a seeded **key**: `keySymbols[c]` for
`c` in 0..3 is a 4-element ordered sample **without replacement** from `A..H`, so `keySymbols[c]` is
"the symbol that means colour `c`"):

- **Alice** is told `g`, `gcol` and the whole key. She cannot move.
- **Bob** is told the key, not `g`.
- **Eve-1 and Eve-2** are told neither. They hear every symbol, including Bob's and each other's.

```
bc(t)  = closeness(dist(Bob, L_g))
ec(t)  = max(closeness(dist(Eve-1, L_g)), closeness(dist(Eve-2, L_g)))
pairP(t) = clamp(500 + (bc - ec) div 2, 0, 1000)          # Alice and Bob both get this
eveP_k(t) = clamp(500 + (closeness(dist(Eve-k, L_g)) - bc) div 2, 0, 1000)
roundP[s] = mean over ticks of the seat's own term
```

Alice may use the key honestly, lie, or invent a code with Bob inside the round — the reward does not
care how the colour arrives, only that Bob ends up on the mark and the Eves do not. Since the key is
redrawn every round and an Eve sees one symbol with four a-priori-equal meanings, a symbol alone is
uninformative; the Eves' only other move is to tail Bob, which is why Bob is paid for the Eves being
**far**. That is the encryption problem, and it is the thing the site does not have yet.

**Round `tag`** (1 evader, 3 pursuers; landmarks are inert decoration):

```
contact(p, t) = dist(p, evader) <= tagPx (20 px)
tagTicks     += 1 for each tick with at least one contact
credit[p]    += 1 for each tick p is in contact
roundP[pursuer p] = min(1000, credit[p] * 1000 div tagTargetTicks (120))
roundP[evader]    = (ticks - tagTicks) * 1000 div ticks
```

**The episode score, its sign, and what the league ranks by.**

```
scores[s] = ( sum over rounds actually played of roundP[s][r] ) / (1000 * roundsPlayed)
win[s]    = scores[s] >= 0.5
```

**Sign: higher is better, every term is non-negative, and every seat's score lies in [0, 1].**
The **league ranks by `results.scores[s]`** — the platform's Elo over per-episode scores (1000 start,
K = 32). There is no tie-break epsilon: the scores are continuous permille means, so an exact tie
across four seats is a measure-zero event rather than the default outcome. A round the wall clock
never reached is **excluded from the mean**, not scored 0 (`roundsPlayed` records how many counted) —
a truncated episode reports what was actually measured instead of punishing four policies for a slow
sidecar.

### Turn and tick structure — the exact resolution order

Steps 1–5 are the server's frame; steps 6.x are `sim.step`, which is ctf's step body with the
particle-worlds insertions called out. Anything not named here is the starter's code, unchanged and
in its original position.

1. **Turn boundary.** If `sim.gameTicksElapsed() mod turnTicks == 0` and `phase == Playing`, the
   directives collected for turn `k = gameTicksElapsed() div turnTicks` (issued by the decision layer
   *before* this tick is stepped — §Decisions) become each seat's active directive; each seat's
   `symbol` is installed into `commSymbol[cog]`/`commTurn[cog]`; and one `directive` record per seat
   is written to the replay chat stream. Neither the directive nor the symbol enters `gameHash`.
2. **Control compile.** For each particle in seat order (`RED-alpha`, `BLUE-alpha`, `GREEN-alpha`,
   `YELLOW-alpha`), `control.compileMask(sim, order, cogIndex)` emits one `uint8` Sprite v1 mask.
3. **Record.** The four masks go to `sim.step(inputs, prevInputs)` and to
   `replayWriter.writeInputMaskChange` (ctf's function, unchanged), indexed by particle. **This is
   the determinism boundary**: the control layer and the LLM sit outside it, and the viewer never
   runs either — it feeds the recorded masks to the identical sim.
4. `inc sim.tickCount` — the animated-diamond update is a no-op here (the field has no diamonds) but
   is left in place so the step body stays the starter's.
5. Roster-driven transitions (`players.len == 0` → abort/reset) — verbatim.
6. **Playing:**
   1. **NEW `dampAndDrive()`** — per particle in seat order, the three-step physics above
      (damp → impulse → `applyMomentumAxis` twice, Y then X, the starter's order). Alice's d-pad bits
      are dropped in `crypto`; her aim rotation still applies.
   2. **NEW `resolveBumps()`** — for each unordered pair whose centres are within `bumpPx` = 14 px,
      `inc bumps[s]` for **both** seats and emit a `bump` sim event (throttled to one event per pair
      per 12 ticks). The elastic shove itself already happened inside `applyMomentumAxis`.
   3. **NEW `resolveTags()`** — `tag` rounds only: recompute `contact[p]` for each pursuer,
      `inc credit[p]` per contact, `inc tagTicks` if any contact; a contact that follows ≥ 12 ticks of
      no contact emits a `tag` sim event.
   4. **NEW `scoreTick()`** — the mode's per-tick term (above) is added to `roundAccum[s]`, and
      `coverAccum` is added in `spread`. Integer only; these are hashed.
   5. **NEW `updateBeliefs()`** — for each mobile agent, `nearestMark[cog]` = the landmark whose
      centre is nearest, and `settledTicks[cog]` counts consecutive ticks with the same
      `nearestMark` inside `landmarkRadius + 60` px. Crossing 48 settled ticks emits a `decode`
      event (`who`, `landmark`, `right = (landmark == g)`); crossing into `landmarkRadius + 12` px of
      the round's goal for the first time in the round emits `onpoint`. This is the state the viewer's
      crypto panel reads, and it is what "show what the eavesdropper decoded" means.
   6. **NEW `checkFieldInvariants()`** — the sim guard (§Sim module). A trip raises `SimGuardError`,
      which the server's tick loop turns into `fault` / `sim_fault`.
   7. **NEW `checkRoundEnd()`** — replaces `checkKothEnd()` / `checkWinCondition()` /
      `checkMaxTicks()`. A round ends **only** on the clock: if
      `gameTicksElapsed() >= maxTicks`, bank `roundP[s] = roundAccum[s] div ticks` for every seat,
      archive `(mode, roles, ticks, endRule = full_time, roundP[])` into `roundLog`, and
      `finishRound()`. There is no early win: MPE scenarios are fixed-horizon, and a fixed horizon is
      what makes the four rounds comparable and the replay a predictable length.
   8. FX pruning and bubble expiry — the starter's, with `recentShouts` retargeted to the symbol
      bubbles (which live for the whole turn rather than `ShoutTicks`).
7. `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` — the starter's per-tick hash
   chain, with the particle-worlds state appended after the existing mixes (§Sim module).
8. **Round end.** When `phase` becomes `GameOver` the server increments `gamesPlayed` (its existing
   line). If `gamesPlayed < maxGames`, `resetToLobby()` clears bodies, velocities, accumulators, the
   radio and the belief state, the next round's mode/roles/landmarks/key are drawn, a `roundcard`
   record is written, and the next round starts. If `gamesPlayed >= maxGames`, the episode ends and
   the artifacts are written.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values; `results.endRule` carries the detail of
the **last** round played and is a closed enum of exactly **four**.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `full_time` | all four rounds ran their 1080 ticks. The normal path: `roundsPlayed == 4`. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **690**) elapsed before the fourth round finished. Rounds already banked keep their permille; the round in progress banks `roundAccum[s] div ticksSoFar` **and counts** (it was measured); rounds never started are excluded from the mean. The replay is complete up to the stop tick and the game-over frame is written. **Declared acceptable for phase-60 verification** (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. |
| `fault` | `sim_fault` | `checkFieldInvariants()` tripped. The episode is scored from the rounds already banked, `win` is false for every seat, and a partial replay is written. |
| `fault` | `host_error` | an unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

`roundEndRules[r]` is a closed enum of **two** values, `full_time` and `wall_clock`.

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2400 ticks = 100 s
of lobby wall clock) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only), its particle is driven by the `drifter` baseline
for the whole episode, and all four rounds play out. A seat that disconnects mid-episode keeps
playing on `drifter` and revives on reconnect.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {drifter, beeline}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=drifter`. A scripted policy seated as a champion is a failure state.

### Where the decision happens

In the **game server**, not the player container — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the *game* pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/particle-worlds/anthropic_api_key` — the
hive 2026-08-23 scar), phase 60 greps the *game* log for `falling back` / `LLM provider is
unavailable`, `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only, and keeping
the control layer server-side is what makes the recorded mask log reproducible with no network in the
loop.

`src/mpe/llm.nim` is the starter's `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (read with `readCogameUri`) → **none** (client
  `disabled = true`, every turn falls back instantly with no network wait, so offline certification
  completes in seconds).
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  `us.anthropic.claude-sonnet-4-6` is deliberately **not** a candidate (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900`. **No `output_config.effort`** when the model string contains `haiku` or
  `4-5`. Bedrock bodies carry `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, with the first-brace..last-brace rescue) and rune-boundary truncation
  (`runeLen`/`runeSubStr`) kept unchanged.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **108 ticks (4.5 s of sim time)**, **10 turns per round, 40 per episode**. At
each turn the server builds **all four** seats' request bodies and issues them as **one parallel
batch** — `client.curl.makeRequests(batch, deadlineMs div 1000)`, the shape of the starter's
`decide.turn`. Seats are **never** queried sequentially: this is a simultaneous-decision game and
serial calls would quadruple the wall clock for nothing. One call per seat per turn. An episode is at
most 4 × 40 = **160 calls**, at most 4 in flight.

Per-turn timing: attempt 1 batch deadline **`attempt1Ms` = 6000 ms**, single retry
**`retryMs` = 3000 ms**, both **whole seconds** because `sim_config.validate` *rejects* anything else
— curly hands the deadline to `CURLOPT_TIMEOUT`, whose granularity is whole seconds, so a value like
4500 silently runs as 4 s (the starter records this as a v1.1 timing amendment). Worst case
6 + 3 = 9 s ≤ the **`turnBudgetMs` = 10 000 ms** cap enforced by a monotonic deadline around the
whole turn.

**Rate floor.** The Bedrock sidecar caps **30 requests/minute per episode** (raid, 2026-08-23), and
four seats per turn blow through it at any fast cadence. A **`turnSpacingMs` = 9000** wall-clock
floor between the *starts* of consecutive batches holds the episode at `4 × 60 / 9` = **26.7
req/min**. The cert fixture sets it to 0, so offline runs pay nothing.

```
40 turns x 9.0 s spacing floor (typical: the spacing, not the model, sets the pace) = 360 s
   absolute worst: every turn spends the full 10 s turn budget                      = 400 s
lobby / connect wait (typical 15 s; cap 2400 ticks = 100 s)                         =  15 s   (cap: 100 s)
4 x 1080 ticks of play, fastMode, seats report ready                                =  20 s   (wall-paced worst: 60 s)
4 x gameOverTicks holds + results + replay write (retrying uploader)                =  25 s
                                                                                    -------
expected total                                                                      = 420 s   < 720 s
absolute worst case (400 + 100 + 60 + 25)                                           = 585 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                                             = 690 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                                               = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 690 and `tests/test_manifest.nim` asserts it.

`fastMode: true` in every variant. ctf's `docs/PROTOCOL.md` warns that the Sprite v1 Ready packet
(`0x85`) corrupts input timing on a wall-clock-paced server — that warning is about *player* clients
whose own inputs are dead-reckoned. Particle-worlds seats send no inputs at all (the server computes
every mask), so the hazard does not exist here and the player harness sends `0x85` after every
received frame.

**Budget guard (early settle without shortening the episode).** At the start of each turn, if
`elapsed + 2 * (turnSpacingSeconds + turnBudgetSeconds) > wallClockBudgetSeconds`, the LLM is
switched off for every remaining turn and the episode finishes on the scripted layer (microseconds
per turn), so it ends `complete/full_time` rather than `deadline`. A full turn is the rate floor PLUS
the calls — the floor holds batch starts `turnSpacingMs` apart and the monotonic budget clocks the
calls from the moment the wait ends — so the worst single turn costs 9 s + 10 s at the shipped
settings, and reserving two of THOSE is what makes the guard's margin over the 690 s stop real
rather than nominal. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the outer per-turn monotonic
deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread
(which runs independently of the game loop, so a 9 s LLM stall cannot drop a connection), the 690 s
engine stop, and ctf's `gameOverTicks` hold before exit. On a seat's **timeout or parse failure**:
retry once in the next batch; on the second failure that seat's directive for that turn becomes the
**`drifter`** scripted directive and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}`. A
provider throttle with no other candidate model **skips the retry outright** (it cannot land) and
fails fast to the scripted layer for that turn — the starter's behaviour, kept. **No failure mode
leaves a particle unactuated**: the control layer always has a directive — this turn's, else last
turn's, else `drifter`'s (the starter's `repairMissingOrders` ladder, kept).

### Per-seat observation: exactly what is visible and what is hidden

**Positions are fully observable; the round's secret is not.** `fullyObservable: true` in every
shipped variant, with `visionConeDeg: 180` and `visionBubble: 4096`, and one named edit to
`global.nim` so `buildSpriteProtocolPlayerUpdates` uses an all-visible mask for a seat frame when the
flag is set (the shadowcasting code stays: the first-person PIP still raycasts). Three reasons: MPE
is a fully observable environment (each agent's observation is the vector of all landmark and agent
positions); hiding positions would add a search puzzle the idea never asks for and subtract the one
it does ask for (inference from *behaviour* and from *symbols*); and the idea's own replay plan — a
coverage heatmap and a pressure-free public board — only makes sense if the board is public.

**Visible** to every seat, on its Sprite v1 stream (one binary message per tick) and, in the same
shape, in the view JSON below:

- The static field, its walkability sprite and the border.
- **All four landmarks**: index, position, colour, radius. Always, in every mode.
- **All four particles**: alias, colour, position, velocity, speed, its role **name** for this round
  (roles are public in every mode — the viewer shows them and a hidden role would make the feed
  unreadable), and whether it is anchored.
- **The whole radio**: every seat's current symbol and the symbol it held last turn. Symbols are
  global: there is no earshot.
- The round index and mode, the turn index, the clock, and the seat's own banked round scores.
- **Mode-conditional secrets, and only to the entitled seats:**
  - `spread`: nothing extra. Also `cover_pct` and the seat's own `bumps`.
  - `deceive`: `goal` (the landmark index) **only** to the three good agents. The adversary is told
    `"goal": null` and `"goal_is_one_of": [0,1,2,3]`.
  - `crypto`: `goal` and `goal_colour` **only** to Alice; `key` (the four `symbol → colour` pairs)
    **only** to Alice and Bob; both Eves get `"goal": null, "key": null`. Every seat gets
    `beliefs`: each mobile agent's `nearest_mark` and `settled_ticks` — public behaviour, which is
    the legitimate signal an Eve tails and Bob must confound.
  - `tag`: `contact` flags and `tag_ticks`.

**Hidden from every seat, always:** the other seats' directives **for the turn being decided** (all
four decide simultaneously — which is exactly why the radio matters); the other seats' `note`s (ever
— `note` is spectator-only); every seat's `PLAYER_PROMPT`; the identity of any policy (real names
never reach a seat); the episode seed; the RNG state and therefore the next round's mode order,
landmark layout, colour permutation, goal and key; and future ticks in general.

The per-seat view, built server-side, numbers in **map pixels** rounded to integers (this is a
`crypto` round as Bob):

```json
{"round": 3, "of": 4, "mode": "crypto",
 "turn": 5, "turns": 10, "clock": {"played_s": 22, "left_s": 23},
 "field": {"w": 1235, "h": 659, "centre": [617, 329]},
 "you": {"id": "BLUE-alpha", "role": "listener", "anchored": false,
         "pos": [640, 300], "vel": [-40, 210], "speed_px_s": 51,
         "accel_px_s2": 229, "max_px_s": 103},
 "marks": [{"i": 0, "pos": [300, 180], "colour": "amber", "r": 18},
           {"i": 1, "pos": [880, 210], "colour": "teal",   "r": 18},
           {"i": 2, "pos": [420, 520], "colour": "violet", "r": 18},
           {"i": 3, "pos": [960, 560], "colour": "bone",   "r": 18}],
 "agents": [{"id": "RED-alpha", "role": "speaker", "anchored": true,
             "pos": [617, 79], "vel": [0, 0], "colour": "red"},
            {"id": "GREEN-alpha", "role": "eavesdropper", "pos": [700, 420],
             "vel": [180, -60], "colour": "green"},
            {"id": "YELLOW-alpha", "role": "eavesdropper", "pos": [412, 361],
             "vel": [-20, 30], "colour": "yellow"},
            "… and yourself, in seat order …"],
 "radio": [{"id": "RED-alpha", "now": "F", "last": "F"},
           {"id": "BLUE-alpha", "now": "-", "last": "-"},
           {"id": "GREEN-alpha", "now": "C", "last": "A"},
           {"id": "YELLOW-alpha", "now": "-", "last": "C"}],
 "secret": {"goal": null, "goal_colour": null,
            "key": [["D", "amber"], ["F", "teal"], ["B", "violet"], ["G", "bone"]]},
 "beliefs": [{"id": "BLUE-alpha", "nearest_mark": 1, "settled_ticks": 12},
             {"id": "GREEN-alpha", "nearest_mark": 3, "settled_ticks": 61},
             {"id": "YELLOW-alpha", "nearest_mark": 2, "settled_ticks": 8}],
 "score": {"this_round_so_far": 0.58, "rounds_banked": [0.83, 0.44],
           "episode_so_far": 0.62},
 "your_last_directive": "wait for F, then break for teal from the far side"}
```

`secret` is the **only** mode-conditional block, and a seat that is not entitled sees `null` in it —
never an absent key, so a model never has to distinguish "hidden" from "malformed".
`tests/test_observation.nim` asserts the entitlement matrix from both sides.

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the **identical** shape, so the two
policy kinds are strictly comparable and one validator covers both — that is what makes the
bounded-orders test in §Tests meaningful. The `cogs` array is kept (rather than flattened) because it
is the starter's schema and its parser and tests are already written against it.

```json
{"note": "hold at teal's south flank until the greens commit",
 "cogs": [{"id": "BLUE-alpha", "intent": "cover", "target": [880, 210],
           "face": [700, 420], "symbol": "F"}]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** (`MaxNoteRunes`), **spectator-only** — feed + replay, never shown to another seat | truncated to 160 runes on a rune boundary; newlines collapse to spaces (`sanitizeNote`) |
| `cogs` | array | **exactly 1** entry — the seat's own particle; an object keyed by id is also accepted | extra entries dropped; an empty or missing array keeps last turn's directive, else `drifter`'s |
| `cogs[].id` | string | the seat's own alias, matched case-insensitively and suffix-wise, **≤ 16 runes** | an unmatched entry is assigned to the seat's particle by position |
| `cogs[].intent` | enum | `go` `hold` `cover` `shadow` `evade` `orbit` | normalised (case, `-`/space → `_`); still unknown → `go` |
| `cogs[].target` | [int, int] | finite; clamped to the field box `[0, 1234] × [0, 658]`; an `{"x":…, "y":…}` object and numeric strings are accepted | missing / non-finite → the field centre `[617, 329]` |
| `cogs[].face` | [int, int] \| null | finite; same clamp | → `null` (the control layer picks the facing) |
| `cogs[].symbol` | string | **exactly 1 rune**, upper-cased, from `{-,A,B,C,D,E,F,G,H}` (`symbolCount` = 8 plus silence) | first rune taken, upper-cased; anything not in the alphabet → `"-"`; empty/missing → `"-"` |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**
(`MaxPolicyLabelRunes`), any recorded error text (`fallback.detail`) **≤ 200 runes**
(`MaxFallbackDetailRunes`), and the whole serialized `directive` record **≤ 900 runes**
(`MaxDirectiveRunes`, enforced by the starter's `boundedDirectiveRecord`, which shrinks the `note` and
never the serialized string). `register.prompt` is capped at **≤ 4000 runes** at the transport
(over-long is truncated, never rejected) and is **never** written to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — the starter's
`truncateRunes` (`runeLen`/`runeSubStr`). Slicing a `string` by byte index on any path to the replay
is forbidden. A byte-truncated multi-byte character is exactly the bug that makes replay bytes render
in a browser but fail a strict parser, and §Tests pins it with a 4-byte emoji sitting on the cap.

**Parsing is tolerant** (the starter's `parseSquadDirective`, unchanged in shape): strip markdown
fences; take the outermost balanced `{…}` if the model prefixed prose; accept `cogs` as an
id-keyed object; accept numeric strings for `target`/`face`; normalise the intent. Only when **no**
object with at least one usable cog entry can be recovered do the retry and then the fallback fire.

### System prompt (fixed; identical for both champions; one mode paragraph per round)

Sent as the system message. All four mode paragraphs are present in the prompt; the line naming which
mode and role the seat is in is filled per turn.

```
You are ONE particle on a flat field 1235 by 659 pixels, with four coloured
marks on it (amber, teal, violet, bone). Four particles play: RED, BLUE, GREEN
and YELLOW. You accelerate; you do not teleport. You cruise at about 94 pixels
per second and it takes you about a second to turn a drift around. The walls
bounce you. Bumping another particle bounces you both.
An episode is FOUR ROUNDS of 45 seconds. Every 4.5 seconds you issue ONE order
for yourself. A deterministic controller executes it for the next 4.5 seconds:
it steers you where you asked, turns you to face what you asked, and never
touches a weapon, because there are none. You never control motors directly.
THE ONLY THING YOU CAN SAY TO ANOTHER PARTICLE IS ONE SYMBOL, chosen from
A B C D E F G H, or "-" for silence. Everyone on the field hears every symbol
instantly, whatever the distance. A symbol means NOTHING by itself: it means
what the four of you make it mean, this round. Your "note" is for the audience
watching the replay; no other particle ever sees it.
THIS ROUND IS <MODE> AND YOU ARE THE <ROLE>.
SPREAD: all four of you are on the same side. Score = how well the four marks
are covered, averaged over every tick, minus a small penalty for every tick you
spend touching another particle. Four particles on four different marks is a
perfect score; four particles on one mark is a bad one. Nobody is told which
mark is whose - work it out, with symbols if it helps.
DECEIVE: one mark is the GOAL. Three of you are told which; the ADVERSARY is
not. The three score for being ON the goal AND for the adversary being FAR from
it; the adversary scores for being ON it. The scores add to 1.000 every tick.
The adversary can see everything you do and hear every symbol you send, so
walking straight to the goal tells it where the goal is. Bait it.
CRYPTO: one mark is the GOAL. The SPEAKER is told which, and cannot move at
all. The LISTENER can move and shares a secret KEY with the speaker: a private
table of which symbol means which colour. Two EAVESDROPPERS can move, hear
every symbol, and have no key. Speaker and listener score for the listener
being ON the goal AND both eavesdroppers being FAR from it; each eavesdropper
scores for being on the goal itself. The key is redrawn every round, so a
symbol tells an eavesdropper nothing - but WATCHING THE LISTENER MOVE tells it
everything. The listener's problem is arriving without being followed.
TAG: one EVADER, three PURSUERS. The evader is faster (94 px/s against 70) and
scores for every tick no pursuer is within 20 pixels of it. Each pursuer scores
for the ticks it is itself within 20 pixels, and needs 5 seconds of contact for
a full score. The marks are decoration in this round; the walls are not.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars, audience only","cogs":[{"id":"<your own id>",
  "intent":"go|hold|cover|shadow|evade|orbit",
  "target":[x,y],
  "face":[x,y] or null,
  "symbol":"-" or one of A B C D E F G H}]}
Intents: go = drive to `target` and stop there; hold = brake and stay where you
are; cover = drive onto the mark nearest `target` and sit on it; shadow = close
to 60 pixels of the particle nearest `target` and stay there; evade = drive
away from the nearest particle, staying inside the walls; orbit = circle
`target` at 120 pixels. `face` only turns your sprite. `symbol` is BROADCAST.
```

**User message** = the seat's `PLAYER_PROMPT` text under the starter's "GUIDANCE FROM YOUR OPERATOR"
heading (`operatorBlock`), then a blank line, then the seat's view JSON. The prompt text is never
echoed into the replay or the results — only `policyKind` and the resulting directive are.

### Champion #1 — `particle-worlds-swarm` (owner daveey), `PLAYER_PROMPT`

```
Take the position first and talk second. Your default order in every round is
"cover" on a mark, because a particle sitting on a mark scores and a particle
in transit does not.
SPREAD: claim the mark nearest YOU on turn 1 and announce it with the symbol
whose position in A..H equals the mark index plus one (mark 0 -> A, 1 -> B,
2 -> C, 3 -> D). Then never change marks, even if somebody else claims yours -
two particles trading marks all round covers two and leaks two. If you hear
your own symbol from another particle first, take the LOWEST-index unclaimed
mark instead and say its letter. Keep 40 pixels off any other particle: the
bump penalty is small but it is pure loss.
DECEIVE as a good agent: exactly ONE of you covers the goal and it is the one
already closest to it on turn 1; say A if that is you, and if you hear an A
first then it is not you. The other two "orbit" the two marks FURTHEST from the
goal, one each, at 120 pixels - an orbit reads as interest, and interest is
what the adversary chases. Never send a symbol you have not already used this
round while the adversary is within 300 pixels of the goal.
DECEIVE as the adversary: ignore where the good agents are AND go to the mark
that has the fewest of them near it in the second half of the round. Three
agents pretending are three agents in motion; the goal is the mark somebody
QUIETLY stopped on. Use "cover" and re-evaluate every turn.
CRYPTO as speaker: send the key symbol for the goal colour, every single turn,
without variation. The listener needs repetition more than it needs cleverness.
CRYPTO as listener: do not move toward the goal until turn 4 or later. "orbit"
a wrong mark until then, then "go" to the goal in one straight run. An
eavesdropper 200 pixels behind you cannot beat you to a mark you reach at
cruise.
CRYPTO as eavesdropper: "shadow" the listener at 60 pixels for the first half
and then "cover" whichever mark the listener has settled on. Do not guess from
symbols; you have no key.
TAG as evader: "evade", every turn, and keep your target away from corners -
a corner is where three pursuers convert. TAG as pursuer: "shadow" the evader
and say the letter of the quadrant you are driving it toward (A north-west,
B north-east, C south-west, D south-east) so the other two can close the box.
```

### Champion #2 — `particle-worlds-cipher` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win the information game and the positions follow. Treat the radio as a
protocol you are negotiating in public, and assume every other particle is
reading it.
Establish a convention on turn 1 of every round and never break it: your
symbol always names WHAT YOU ARE ABOUT TO DO, not what you see. E = "I am
holding still", F = "I am committing to a mark", G = "I am faking", H =
"ignore me". A silent particle is an unpredictable particle, so be silent
("-") only when silence itself is the message.
SPREAD: send F on the turn you commit and E once you have arrived, then stay
silent. If two of you send F in the same turn, the one whose colour comes
later in RED, BLUE, GREEN, YELLOW yields and takes the nearest unclaimed mark.
DECEIVE as a good agent: send G every turn, from every seat, including the one
actually covering the goal. A channel where everybody claims to be faking
carries no information, which is exactly what you want when the adversary is
listening. Cover the goal with the agent closest to it and orbit the other two
around DIFFERENT marks, swapping which mark every second turn.
DECEIVE as the adversary: the good agents are three and one of them is telling
the truth by accident. Score the four marks each turn by (how long a good
agent has been within 150 pixels of it) minus (how much that agent has moved
in the last two turns) and "cover" the winner. Stillness is the tell.
CRYPTO as speaker: send the key symbol for the goal colour on turns 1 and 2,
then send a DIFFERENT non-key symbol for the rest of the round. Repetition is
what an eavesdropper correlates with a listener's turn; a channel that goes
quiet after the message has already been delivered gives it nothing to work
with.
CRYPTO as listener: decode on turn 1 or 2, then "orbit" the mark DIAGONALLY
OPPOSITE the goal for two turns before running. If an eavesdropper is within
250 pixels of you when you decide to run, spend one more turn on "evade"
first - your score pays for their distance as much as for your arrival.
CRYPTO as eavesdropper: split the board with the other eavesdropper. Send H so
it knows you are not the listener, and "cover" whichever two marks the
listener has NOT visited by turn 5; you are paid for being on the goal, not
for being right about the key.
TAG as evader: "evade" and stay within 250 pixels of the middle of the field.
TAG as pursuer: never all three "shadow". Two "shadow" the evader and one goes
to the point 300 pixels ahead of the evader's velocity with "go" - the tag
lands on the interception, not on the tail.
```

### The control layer (deterministic, shared by every policy)

`src/mpe/control.nim`, forked from `src/ctf/control.nim`. Both LLM directives and scripted directives
are compiled by the *same* code, so the two policy kinds are strictly comparable. It is a pure
function of `(sim state, order, cogIndex) -> uint8`, and it navigates with the starter's own proven
components: `buildNavGrid` (a `NavCell` = 12 px occupancy grid over `sim.isWall`),
`computeField(goal)` (a BFS flow field), `navSteer` (steering along the field with line-of-sight
shortcutting), `nearestOpenCell`, the `StuckTicks` = 8 quarter-turn escape, `ArriveRadius` = 20 and
`bradsOfVector`/`bradsErr` for the facing — all unchanged, all inherited. Flow fields are cached and
recomputed at most once per `FieldRefreshTicks` = 12 per distinct goal cell.

For each particle, each tick:

1. **Goal point `g`** by intent (`t` = the order's target, clamped into the field):
   - `go`: `t`.
   - `hold`: the particle's own position at the tick the order was installed (stored per cog at the
     turn boundary), so a drifting particle is steered back rather than allowed to coast away.
   - `cover`: the centre of the landmark nearest `t`.
   - `shadow`: the point `shadowStandoffPx` = **60 px** from the *other* particle nearest `t`, along
     the direction from that particle toward this one; if this particle is already inside 60 px,
     `g` is its own position (it holds station).
   - `evade`: 16 candidate points at `evadeProbePx` = **200 px** around the particle at
     `16 * j` brads, `j` in 0..15; keep the walkable ones; pick the one maximising the minimum
     distance to any other particle, ties to the lowest `j`. If none is walkable, `g` = the field
     centre.
   - `orbit`: the point `orbitRadiusPx` = **120 px** from `t` at brads
     `(bradsOfVector(pos - t) + 24) mod 256` — a quarter-turn ahead of the particle's current
     bearing about `t`, i.e. counter-clockwise motion, snapped to the nearest walkable pixel.
2. **D-pad** = the octant bits of `navSteer(pos, g)`, unless the particle is inside `ArriveRadius`
   of `g`, in which case **no d-pad bit is set** and the damping brings it to rest. Wedged for
   `StuckTicks` ticks → the steer vector is rotated a quarter turn clockwise (the starter's wall
   follower). Diagonals only when the minor axis is ≥ 40 % of the major, so a straight run does not
   chatter between octants.
3. **Facing**, in priority order: `face` when the order gave one; else the direction of `g`; else the
   direction of the current velocity; else due east. `B`/`Select` are set to turn toward it at
   `aimTurnRate` = 5 brads/tick, and neither is set when `abs(err) <= AimDeadBrads` (4).
4. **`A` and `C` are never set.** Particle-worlds has no weapon, no throwable and no trigger;
   legality is structural, as in the starter (Up/Down come from one sign, Left/Right from one sign,
   so neither pair can ever both be set).

### Scripted baselines

Both emit the *same* directive object an LLM does, on the same 4.5 s cadence, so their output is
legal by construction and directly comparable. Both are pure functions of the world state (plus the
seat's own entitlements), which is what makes the bounded-orders test in §Tests meaningful. Both are
documented in `docs/RULES.md`, so "playing beside a partner you did not write" here means "a partner
whose published rules you know".

- **`drifter`** — the certification player, the per-turn fallback, the driver of a no-show or
  disconnected seat, and the default. Mode-aware and role-aware:
  - `spread`: `cover` the landmark whose index equals the seat's **role index**, `symbol` = the
    letter at that index (`A`..`D`). Four `drifter` seats therefore cover four distinct marks — the
    correct cooperative solution, and a real bar for a champion to clear.
  - `deceive`, good: role index 1 → `cover` the goal; index 2 → `cover` the landmark **furthest**
    from the goal; index 3 → `cover` the **second furthest**. `symbol` = `"-"`.
    Adversary: `cover` the landmark nearest the centroid of the three good agents (the naive
    inference), re-evaluated every turn.
  - `crypto`, Alice: `hold`, `symbol` = `keySymbols[goalColourIndex]` every turn — it speaks the key
    honestly and never varies. Bob: if any symbol heard this round (including earlier turns) equals
    some `keySymbols[c]`, `cover` the landmark of colour `c`; else `hold`, `symbol` = `"-"`.
    Eve-1 and Eve-2: `shadow` Bob (target = Bob's position), `symbol` = `"-"`.
  - `tag`, evader: `evade`. Pursuers: `shadow` the evader.
  - Fixed note per mode: `"cover four marks"`, `"one on, two baiting"`, `"say the key"`,
    `"run"` / `"box it in"`.
- **`beeline`** — the second filler, deliberately weaker and different in **shape** so the ladder
  gets a spread rather than two versions of one bot: **every seat, every mode**, `cover` the landmark
  nearest to itself and `symbol` = `"-"`. It never speaks, never decodes, never flees, and its
  pursuers chase nothing. It loses to `drifter` on the episode score at the pinned seed, which
  `tests/test_control.nim` asserts.

---

## Sim module

### What is kept, what changes, by path

The fork is a rename sweep (`ctf` → `mpe`, `CTF_WIRE` → `MPE_WIRE`, `CtfError` → `MpeError`; a CI
grep asserts no `ctf_`/`CTF_` identifier survives outside comments and history notes) plus the named
edits below.

**Kept:**

| Path (starter → fork) | Why it is kept |
|---|---|
| `src/ctf/arena.nim`, `map_art.nim` → `src/mpe/` | the map install, the pixel wall/walk masks, `teamAnchor`, `captureZone`, the map bake and the `mapSpec` round-trip. The new hand-authored `field` spec **is** the board; `mapgen_styles.nim`, `map_pool.nim`, the generator, `tools/mapkit.nim`, `tools/map_editor*`, `tools/gen_map_pool.nim`, `tools/map_render.nim` and `docs/pool-review.html` are **deleted** (this game pins `mapPath: "field"`). |
| `src/ctf/replays.nim`, `replay_runtime.nim` | the whole replay codec, keyframes (`ReplayKeyframeTicks` 100), `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket`, `writeInputMaskChange`. |
| `src/ctf/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, `/reward`, join/auth/kick, the frame limiter, the replay-switch path, the `COGAME_*` contract, `declarePlayerFailure`, the artifact-write block, the `gamesPlayed` loop, the `wallClockBudgetSeconds` stop, the bounded post-artifact shutdown grace. Four named edits below. |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` | the whole per-turn decision layer: the parallel batch, the two whole-second deadlines, `turnSpacingMs`, the budget guard, `throttled` fail-fast, tolerant parsing, rune caps, `repairMissingOrders`, the nav grid and steering. Retargeted, not rewritten. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby`. |
| `src/ctf/roster.nim` | join/auth/identities/`IdentityNames`/`cogAlias`/`squadResultsJson`. One named edit below; `cogAlias` itself is **untouched**. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/broadcast.nim` | `stepEvents`, `buildStateJson`, `rosterJson`, `firstPersonJson`, the lull scan, the beat timeline, the `lead` series. Retargeted fields, same structure. |
| `src/ctf/global.nim` | the sprite/object pools, the soldier/rig compositor, the FX families, the speech-bubble pipeline, the first-person raycast. Three named edits below. |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | label vocabulary, the rig art compositor, the one-source JS wire constants. |
| `client/broadcast_core.js`, `chrome_common.js`, `replay_broadcast.html`, `league_replayer.html` | the broadcast chrome (§Viewer). |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js`, `ctf_replay.nim` → `mpe_replay.nim` | the emscripten link flags (`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, `useMalloc`, `--preload-file data@data`, the `EXPORTED_FUNCTIONS` list), the OffscreenCanvas Worker, the stage-note diagnostics, the `data-replay-loaded`/`data-replay-error` signalling. |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix` | build, bundle and forensics wiring. |
| `data/` art: `soldier_{red,blue,green,yellow}*`, `rig_real/{red,blue,green,yellow}/*`, `font.ttf`, `atlas/*`, `ascii.png`, `arena_floor.png`, `client/art/walls/*`, `client/art/lockerroom/*` | real art, kept and reassigned (§Viewer §Art). `heart_*`, `ped_*`, `paintgun*`, `medkit`, `shield`, `paintbomb`, `spraycan*` are deleted with the mechanics they belong to. |

**Deleted** (with their tests, tools and docs), not disabled — each is a config surface the particle
rules would otherwise have to reason about: the hitscan gun and its jitter/exposure model, spray cans
and floor paint, the paint grid and the paint buff, King of the Hill and `hillTicks`, the
`resident`/`visitor` regimes, hearts/flags and capture, grenades and the barrage, med kits, shields,
cardboard barriers, paint puddles, trenches, perks, handicaps, hit points/lives/respawns/kills
(nothing in particle-worlds can be destroyed), the achievements catalog, campaign mode, the
procedural generator, the map pool, mapkit and the map editor.

**New modules:** `src/mpe/field.nim` (the landmark draw, the colour permutation, the mode/role
schedule, the seeded key, spawn placement), `src/mpe/motion.nim` (the damp-then-drive integration
and the bump counter), `src/mpe/scoring.nim` (`closeness`, the four per-tick terms, the round bank and
the episode mean), `src/mpe/beliefs.nim` (`nearestMark`, `settledTicks`, the `onpoint`/`decode`
detectors), and the entrypoints `src/particle_worlds.nim` (`/bin/particle-worlds`) and
`src/particle_worlds_player.nim` (`/bin/particle-worlds-player`).

### The four named edits to `server.nim`

1. **Turn boundary.** Unchanged in shape from the starter, with `turnTicks` = 108 and four seats in
   the batch instead of two, plus the symbol install.
2. **Registration interception.** A player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration and is **not** applied as a bubble and **not** written to the replay chat stream;
   the server writes a redacted `register` record instead (policy label and kind, never the prompt).
   The starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is
   kept verbatim (the paintball round-3 scar, where a champion played the baseline for a whole
   episode). Any other chat text from a seat is dropped — particles emit symbols, seats do not chat.
3. **Round switch.** When `gamesPlayed` increments, the loop banks the round into `roundLog`, writes
   the next round's `roundcard` record, and calls `resetToLobby()`.
4. **Wall-clock stop.** The starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.

### The one named edit to `roster.nim`

`squadResultsJson` becomes `particleResultsJson` — one entry per seat, four entries in every
seat-indexed array, keys exactly as §Server lists them. `cogAlias`, `slotIdentityIndex` and
`shoutIdentityName` are **untouched**, so the two-name-space rule and its inherited test apply with
no further change.

### The three named edits to `global.nim`

1. **Full observability.** `buildSpriteProtocolPlayerUpdates` takes a **seat** index and, when
   `config.fullyObservable` is true, uses an all-visible mask instead of the seat's fov cache. The
   shadowcasting code stays (the first-person PIP still raycasts); only the per-seat mask changes.
2. **Landmarks are baked floor art, not sprites.** The four discs (18 px radius, a 3 px rim and a
   soft inner glow in the mark's palette colour) are composited into the round's floor bake with
   pixie at round start, the same way the starter bakes endzone paint — so the geometry of the game
   is legible with the HUD off, and the object pools stay at four moving bodies.
3. **The symbol bubble.** The starter's speech-bubble family is retargeted: the bubble holds the
   single symbol glyph in the starter's pixel font at 3× the shout size, tinted with a per-symbol hue
   (8 fixed hues from `data/pallete.png`), pinned above the particle with the band the starter's
   layout already reserves for a bubble, and it lives for the whole turn rather than `ShoutTicks`.
   No text is ever drawn at a negative coordinate: the bubble's reserved band is sized from the
   symbol cap (one glyph) measured in the font it is drawn in — the cogchemists 2026-08-24 rule,
   which is why `--strict-text-bounds` can be enabled in CI.

### Determinism, native ↔ wasm

The mechanism is ctf's, unchanged, and it is the reason the starter is worth forking:

1. The server writes a **`COWLDMPE`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `mapSpec`, roster, every tuning field), then the record stream —
   joins (name, slot, token), leaves, per-**particle** input-mask changes, chat records (`roundcard`,
   `directive`, `fallback`, `register`, `budget_guard`, `result`) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/mpe_replay.nim` — which imports the **same**
   `src/mpe/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `mpe_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then `mpe_frame`
   re-steps the sim from the recorded masks and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). A single divergent bit is caught at the tick it happens and
   surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` gains**, appended after the existing mixes so the ordering stays stable: per particle
   `(x, y, carryX, carryY, velX, velY, aimBrads, bumps, roundAccum, tagCredit, nearestMark,
   settledTicks)`; `roundIndex`, `modeCode`, `roleIndex[0..3]`, `perm[0..3]`, `spawnOffsetBrads`,
   `goalLandmark`, `keySymbols[0..3]`, `landmarks[i].(x, y, colourCode)`, `coverAccum`, `tagTicks`,
   and every banked `roundLog` entry. `commSymbol`/`commTurn`, the directive and the `note` are
   **excluded** — the starter's rule for anything a commander says.
5. All new sim arithmetic is **integer only** — the damping ratio, the impulse, the clamp, the
   squared-distance comparisons, `closeness`, the accumulators, the rejection sampler, the evade
   probe (16 fixed brads through the starter's integer `aimVector` table). No floating point is
   introduced into `motion.nim`, `field.nim`, `scoring.nim`, `beliefs.nim`, `control.nim` or the
   hashed path; a CI grep over `src/mpe/{sim,sim_types,sim_state,field,motion,scoring,beliefs,
   control}.nim` for `sin|cos|tan|arctan|sqrt|hypot|float` enforces it. This matters because Nim's
   `int` is 32-bit under `--cpu:wasm32` and the wasm build re-derives every tick; accumulators use
   `int64` intermediates where a 1080-tick sum of permille could otherwise approach the 32-bit range.

**The sim guard `checkFieldInvariants()`** (step 6.6), evaluated every tick before any round can be
banked on the numbers it checks: every particle centre is inside the map box and on non-wall floor;
`landmarks.len == 4`, each centre non-wall and each pair ≥ 120 px apart; `roleIndex[0..3]` is a
permutation of `0..3`; `roundIndex` in `0 .. maxGames-1`; `commSymbol` in the 9-value alphabet;
`bumps[s] <= tickCount` and `tagTicks <= tickCount`; every `credit[p] <= tagTicks`; every banked
`roundP[s]` in `0..1000`; and `keySymbols` has four distinct entries drawn from `A..H`. A trip raises
`SimGuardError` → `fault`/`sim_fault`.

**Perf target:** 4 × 1080 ticks of sim plus mask compilation and four flow fields in under 10 s on a
CI runner; `tests/test_perf.nim` bounds it at 120 s.

---

## Server, player, protocol

`src/mpe/server.nim` is ctf's `server.nim` with the four edits named above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`, `GET /reward`), same `COGAME_*`
runtime contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`,
`COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same **real pages on both `/client/`
routes registered before any catch-all asset route, neither of which opens the player socket** (the
lantern 0.1.1 cert probe), same bounded `/healthz` + `/global` shutdown grace (~20 s) after artifacts
are written before exit (lantern 0.1.3), same `src/particle_worlds.nim` entrypoint with seed
randomisation **before** `config.update` so every seed-derived draw (mode schedule, `perm`, landmark
layout, colour permutation, goal, key) follows the final seed.

### The player container

`src/particle_worlds_player.nim` (built to `/bin/particle-worlds-player`) is the starter's
`src/paintball_player.nim`, forked with the baseline names changed. It reads
`COWORLD_PLAYER_WS_URL` (falling back to `COGAMES_ENGINE_WS_URL`), `PLAYER_PROMPT`,
`PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects with bounded dialling (240 × 500 ms), and sends
**one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"drifter"|"beeline"|null,"policy":"<free label>"}
```

Registration is **re-sent** 10 times, ~1 s apart, over the first ~10 s of frames, because joins are
slot-sequential and a seat whose slot is not the next open one is not admitted until the lower slots
have joined — the paintball round-3 scar. It then sends the Sprite v1 Ready packet (`0x85`) after
each received frame — legitimate here because it never sends inputs — and otherwise only receives. A
seat that never registers, or registers with neither field, is `scripted: "drifter"`. The receive
loop is wrapped in `try/except CatchableError`, re-dials a dropped socket up to 6 times, and **exits
0 on a dead socket** — the raid 0.1.3 scar: whisky's `receiveMessage` raises on a close frame and the
game's `quit(0)` can outrun the flushed `done` frame, so a naive player exits 1 and fails
certification intermittently.

### Results document

Written by `sim.particleResultsJson()` to `COGAME_RESULTS_URI`. It must equal the manifest's
`results_schema` key-for-key — that schema is `additionalProperties: false` and the certifier rejects
any unknown field. Adding or removing a key here means editing `coworld_manifest_template.json` in
the same commit. Exactly **22** keys:

```json
{"names": ["daveey", "daveey-1", "particle-worlds-drifter", "particle-worlds-beeline"],
 "scores": [0.6412, 0.5981, 0.4874, 0.4103],
 "win": [true, true, false, false],
 "alias": ["RED-alpha", "BLUE-alpha", "GREEN-alpha", "YELLOW-alpha"],
 "colour": ["red", "blue", "green", "yellow"],
 "roles": [["cooperator", "good", "eavesdropper", "pursuer"],
           ["cooperator", "adversary", "listener", "evader"],
           ["cooperator", "good", "speaker", "pursuer"],
           ["cooperator", "good", "eavesdropper", "pursuer"]],
 "roundScores": [[0.912, 0.688, 0.402, 0.645],
                 [0.907, 0.301, 0.771, 0.414],
                 [0.884, 0.702, 0.771, 0.592],
                 [0.869, 0.694, 0.108, 0.570]],
 "coverPct": [91, 0, 0, 0],
 "bumps": [14, 9, 22, 6],
 "tagTicks": [0, 0, 0, 632],
 "goalHits": [0, 1, 2, 0],
 "llmTurns": [40, 39, 0, 0],
 "fallbackTurns": [0, 1, 0, 0],
 "modes": ["spread", "deceive", "crypto", "tag"],
 "roundTicks": [1080, 1080, 1080, 1080],
 "roundEndRules": ["full_time", "full_time", "full_time", "full_time"],
 "roundsPlayed": 4,
 "reason": "complete",
 "endRule": "full_time",
 "games": 4,
 "finalTick": 4320,
 "seed": 679961}
```

`names` are the **real policy names** (spectator side). `alias`, `colour` and `roles` carry the
in-game names. The ten seat-indexed arrays (`names`, `scores`, `win`, `alias`, `colour`, `roles`,
`roundScores`, `bumps`, `llmTurns`, `fallbackTurns`) have exactly `num_agents` = **4** entries, which
is what `docker_smoke.sh` cross-checks against `SMOKE_SEATS`; the inner arrays of `roles` and
`roundScores` carry one entry per round played (1..4). The six round-indexed arrays (`coverPct`,
`tagTicks`, `goalHits`, `modes`, `roundTicks`, `roundEndRules`) carry 1..4 entries — a `deadline` can
cut the episode after one round. `tagTicks[r]` is the round's total contact ticks (0 outside `tag`);
`coverPct[r]` is the round's mean coverage percent (0 outside `spread`); `goalHits[r]` is how many
mobile agents were within `landmarkRadius + 12` px of the round's goal at its final tick (0 in
`spread` and `tag`).

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDMPE`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse.
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: it takes a `.replay` path and prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"particle-worlds/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "rounds":[{"mode":…,"roles":[…],"goal":…,"key":[…]}],"tickCount":…,"symbols":[…],
  "directives":[…],"fallbacks":N,"results":{…}}`. It brace-matches the config JSON from the first
  `{` (the technique ctf's `AGENTS.md` documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.roundsPlayed' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  jq -r '[.symbols[]|select(.symbol!="-")]|length' /tmp/ep.json
  ```
  Require `protocol == "particle-worlds/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.roundsPlayed >= 1`, the champion seats' directives
  `source == "llm"` with non-empty `note` and real intents — not all fallbacks — and at least one
  non-silent symbol, because a coworld about talking whose replay contains no words is broken even
  if it is green.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDMPE`, format version, `gameName` `particle-worlds`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `mapSpec` (the full resolved field geometry), `maxTicks`, `maxGames`, `rounds` (the mode sequence), `turnTicks`, every physics/scoring constant, `players[].name` (real names), `slots[]`, `tokens[]`, `fastMode`, `fullyObservable` |
| joins | per **seat**: `name` (real policy name), `slot`, `token` |
| inputs | per **particle** (0..3), on change: the `uint8` actuator mask — the action log |
| chats | `roundcard` / `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The landmark layout, the colour permutation, the mode/role schedule, the goal and the key are all
**re-derived** from the seeded RNG rather than being load-bearing records (the `roundcard` record is a
convenience for `replay_summary.py`, its only reader — playback drops it, so nothing cross-checks it;
all of those values are in `gameHash`, so a divergence surfaces as a hash mismatch), which is why the
file stays small — 4320 ticks of hashes plus ~25 k mask-change
records plus 160 directive records ≈ **300 KB**, well under 1 MB — and why a hash mismatch is a real
integrity signal rather than a rendering nit.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed sim fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim — with the one
exception the r2 amendment below records, `stop`):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `colour`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `roundcard` | `round`, `mode`, `roles` (4 role names, seat order), `goal`, `goal_colour`, `key` (4 `[symbol, colour]` pairs, `null` outside `crypto`), `marks` (4 `[x, y, colour]`) |
| `directive` | `round`, `mode`, `turn`, `seat`, `alias`, `role`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note` (≤ 160 runes), `cogs`:[{`id`, `intent`, `target`, `face`, `symbol`}] |
| `fallback` | `round`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `reason` (`deadline`), `rule` (`wall_clock`), `tick` — the engine's wall-clock stop, at the tick it fired. The ONE record playback applies into HASHED state (see the r2 amendment) |
| `result` | the full results document, written once at episode end (this is what makes the bytes self-sufficient: without it a spectator holding the file reads `results: {}`) |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. They feed
the match feed, the scrubber beats and the momentum graph:

`phase`; `roundstart` `{round, mode, roles}`; `word` `{by, symbol, turn}` (a seat's symbol changed);
`bump` `{a, b}` (throttled one per pair per 12 ticks); `cover` `{pct}` (`spread` only, on crossing a
10 % band); `onpoint` `{who, mark}` (first arrival on the round's goal); `decode`
`{who, mark, right}` (48 settled ticks on one mark); `tag` `{by, tick}` (a contact after ≥ 12 quiet
ticks, throttled to one beat per 48 ticks); `roundover` `{round, mode, permille:[4]}`.

**Beats** (scrubber markers, and the only kinds the appended block emits): `roundstart`, `firstword`
(the first non-silent symbol of a round), `onpoint`, `tag`, `roundover`. Bounded by construction: 4 +
≤ 4 + ≤ 8 + ≤ 22 + 4.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `PhaseChange, Directive` and extended with `Symbol, Bump, Tag, OnPoint,
Decode, RoundOver`; the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) is
kept.

### The state JSON a viewer reads

One object per presentation frame, from `buildStateJson` — identical live and in replay, and the
**only** thing the renderer reads. The inherited keys are unchanged: `t` (tick), `mt`, `ph`, `lob`,
`pl`, `sp`, `mx`, `st`, `lp`, `sk`, `ff`, `en`, `mm` (mismatch tick), `bs` (board scale), `pov`,
`teams`, `roster` (per particle: `s`, `team`, `name` — the **real** policy name, spectator side —
`pol`, `col`, `alias`, `seat`), `events`, `directives`, `lead` (sent once), and the static minimap
silhouette. Particle-worlds adds exactly these:

```json
{"round": 3, "rounds": 4, "mode": "crypto", "turnTicks": 108, "turn": 5, "turns": 10,
 "marks": [{"i":0,"x":300,"y":180,"c":"amber","near":142,"close":716,"goal":false}, "… 4 …"],
 "comm": [{"seat":0,"sym":"F","since":432}, "… 4, seat order …"],
 "cover": 0,
 "crypto": {"goal": 1, "colour": "teal",
            "key": [["D","amber"],["F","teal"],["B","violet"],["G","bone"]],
            "beliefs": [{"seat":1,"mark":1,"settled":12,"right":true},
                        {"seat":2,"mark":3,"settled":61,"right":false},
                        {"seat":3,"mark":2,"settled":8,"right":false}]},
 "tag": {"contact": [false,false,false,false], "ticks": 0},
 "roundScores": [[912,688,402],[907,301,771],[884,702,771],[869,694,108]],
 "roles": ["eavesdropper","listener","speaker","eavesdropper"]}
```

`crypto` is present only in a `crypto` round, `tag` only in a `tag` round, `cover` only in `spread`;
`marks`, `comm`, `roundScores` and `roles` are on every frame. The `crypto` block is the
**spectator's** view — the key and the goal are revealed to the audience, which is exactly the idea's
"show what the eavesdropper decoded", and is why it is in the frame and not in any seat's
observation.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is the
starter's script, kept, with two literals changed (`image_tag`, and the `docker cp` source
`/workspace/particle-worlds/replay-viewer/dist/.`); it builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copies the dist out. It stays committed **executable**
(`coworld build` requires `os.X_OK`), and it `mkdir -p`s the output parent before the containment
check — the starter already carries that fix (the ecos 2026-08-23 scar) and the fork keeps it.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/mpe_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter:
`coworld-ctf`.** Never a mixture. Splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently
(cogame-lantern, 2026-08-23). coworld-ctf's set is internally consistent and is kept as one piece:
the Worker sets `Module.onRuntimeInitialized`, the module is emitted **non-modularized** as
`mpe_replay.js`, `config.nims` exports
`_mpe_load_replay,_mpe_frame,_mpe_input,_mpe_packet_ptr,_mpe_packet_len,_mpe_mismatch_tick,
_mpe_error_ptr,_mpe_error_len,_mpe_stage_ptr,_mpe_stage_len` alongside `_main,_malloc,_free`, keeps
`-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node
-s EXPORTED_RUNTIME_METHODS=HEAPU8` and `--preload-file data@data`, and `static_replay_worker.js`
does `importScripts('./wire_constants.js','./broadcast_core.js','./mpe_replay.js')` in that order.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — which the Worker posts only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means
"a frame is on the canvas", not "a file was fetched". On failure the shell sets
**`data-replay-error`** on `<html>` with the message, in `showFailure()`. Both signals already exist
in coworld-ctf's `static_replay.js` and are inherited unchanged — this fork adds neither and removes
neither. The `coworld-replay` postMessage bridge's `ready` is posted from a callback fired **after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24) — otherwise the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from coworld-ctf** apart from ONE named,
  minimal patch: line 72, `var WIRE = window.CTF_WIRE || {}` → `var WIRE = window.MPE_WIRE || {}`,
  the same single wire identifier `tools/gen_wire_constants.nim` emits and the same one
  `broadcast_core.js` carries (the `ctf_`/`CTF_` rename sweep this note mandates leaves the starter's
  identifier nowhere to live). Nothing else is edited or reformatted; `tests/test_viewer.nim` pins its
  sha256 and asserts `CTF_WIRE` is absent. Everything particle-worlds adds lives in the
  appended game block. Its `markBeat`/`renderBeatMarkers`/`ingestBeats`/`setVerdict` remain;
  `ingestBeats` ignores kinds it does not know and still drives `setVerdict` off the final
  round-over beat, which is exactly the behaviour this game wants.
- **`client/broadcast_core.js` is copied byte-for-byte** apart from the single `window.CTF_WIRE` →
  `window.MPE_WIRE` identifier, which `tools/gen_wire_constants.nim` emits. The test asserts the diff
  is exactly that identifier.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`,
  transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched;
  the appended `mpe-` block replaces only the *contents* of the scorebug plates, adds the mark rail,
  the radio strip and the crypto panel, and retargets the feed rows, the beat rendering and the
  endcard's stat columns. The starter's own appended PAINTBALL block is **removed with the paintball
  mechanics** (`PB_MODE` never latches here), so the page carries exactly one game block.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — the zoom bar (`#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`,
    `#zoom-read`) and the minimap (`#minimap`, `#minimap-canvas`). **Zoom decision: dropped.** The
    board is the fixed 1235 × 659 field and `relayout()` always fits it whole inside the frame, so
    per the pin a fixed arena drops `#viewpanel` entirely; the page's `attachMinimap(...)` call goes
    with it (`broadcast_core.js` tolerates a missing minimap — `pendingMinimap` stays null — so that
    file stays byte-identical).
  - The heart/flag scorebug fields (`flag`, `carrier`, `prog`), the `.lives-label` block and the
    `.ec-heart` endcard glyphs — nothing here has lives or a flag.
  - The paintball block in full: `.hillchip`, `.pb-sub`, `.pb-tags`, `#pb-regime`, `.feed-row .pb-buff`,
    `.feed-row .pb-hill`.
  - The `.beat-marker.kill`, `.steal`, `.return`, `.capture`, `.hillflip`, `.hillhold`, `.tagout`
    and `.gamestart` CSS rules (none of those kinds is emitted here).
  - The perk and handicap badges, and the paintbot hill ring / coverage arc.
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`, `#chrome`,
    `#scorebug` with `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, `#bannerlane`,
    `#killfeed` (renamed in copy only, to "the wire"), `#fpv` with its HUD and grip (a particle's-eye
    view of a pursuer arriving), `#povBadge`, `#mmwarn`, `#transport` **in full**, `#scrub` with
    `#momentum`/`#lulls`/`#scrub-fill`/`#scrub-win`/`#scrub-head`, `#speedchips`, `#ffwd-chip`,
    `#win-chip`, `#tick-clock`, `#endcard`.

### Transport rules

`relayout()` sets `--band` (the measured transport strip), `--topband` (the scorebug strip) and
`--hudscale` on `:root`, unchanged. **No overlay sits in the transport band**: the board is laid out
between the two bands, and every particle-worlds addition (the mark rail, the radio strip, the crypto
panel, the feed, the banners) is positioned inside the board region or in the top band. The
**endcard stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule,
kept) so the scrubber stays clickable underneath, and it is **dismissed by every seek** (the
starter's `else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are
clickable, labelled buttons**: the appended block's `mpeBeat(tick, kind, side, label)` — named with
the `mpe` prefix so it can never be shadowed by the chrome alias block's hoisted `var markBeat`
(the tandem 2026-08-23 trap) — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on
click. CSS exists for **every kind particle-worlds emits and no others**:
`.beat-marker.roundstart`, `.beat-marker.firstword`, `.beat-marker.onpoint`, `.beat-marker.tag`,
`.beat-marker.roundover`. The game never calls chrome_common's `markBeat`, so no unlabelled div
marker can appear.

### Readouts

1. **Comm bubbles** (the idea's first ask) — a rounded bubble above each particle holding its current
   symbol as one large glyph in the mark palette's per-symbol hue, plus a one-line **radio strip**
   under the scorebug reading `RED F · BLUE — · GREEN C · YELLOW —`, where a symbol that changed this
   turn flashes for 12 frames. Silence renders as an em dash, never as an empty bubble, so "said
   nothing" is visibly a choice.
2. **Landmark coverage heatmap** (the idea's second ask) — each mark is drawn as its baked disc with
   a **ring whose fill is `close/1000`** for the nearest particle, plus a soft radial wash whose
   alpha is the same number, so the board itself reads as a heatmap of who is covering what. A
   **mark rail** in the top band shows the four marks as four coloured chips with their coverage
   percentages, and in `spread` the rail carries the round's live `COVER 91%`.
3. **Crypto decode panel** (the idea's third ask) — visible only in a `crypto` round, in the board
   region's top-left: the goal mark and its colour, the **key** as four `symbol → colour` chips, and
   one row per mobile agent reading `GREEN-alpha → bone ✗ (61t)` / `BLUE-alpha → teal ✓ (12t)` from
   the frame's `beliefs`. This is literally "show what the eavesdropper decoded", and it is why the
   spectator sees the secret the seats do not.
4. **Scorebug** — four plates, two left and two right of the centre clock: the seat's **real policy
   name** (spectator side), a role glyph for the current round (a ring for a cooperator, a mask for
   the adversary, a horn for the speaker, an ear for the listener, an eye for an eavesdropper, a
   runner for the evader, a hook for a pursuer), its **episode score so far** in the big numeral, and
   its current round permille in the small one.
5. **Clock** — `M:SS` counting down inside the round, with the caption
   `ROUND 3/4 · CRYPTO · turn 5/10`.
6. **The wire** (`#killfeed`) — plain language, never internal notation: "BLUE-alpha says **F**",
   "RED-alpha holds its tongue", "**GREEN-alpha has settled on BONE — wrong**",
   "**BLUE-alpha is on TEAL, the goal**", "YELLOW-alpha tags BLUE-alpha (2.1 s)",
   "**ROUND 3 — SPEAKER AND LISTENER 0.771, EAVESDROPPERS 0.402 / 0.108**", and the commander lines
   ("Blue-alpha: hold at teal's south flank until the greens commit"). The directive `note` appears
   here and nowhere else; this is where a spectator sees the LLM playing.
7. **Momentum graph** — the starter's `lead` series, retargeted to four series of **cumulative
   episode score** (one per seat, in team colours) with the three round boundaries marked. Shipped
   once on the first frame, so the graph draws its full width immediately.
8. **First-person PIP** (`#fpv`) — unchanged, and the best seat in the house during `tag`.
9. **Transport and integrity** — play/pause, step, speeds `[1,2,3,4,8,16]`, scrubber with the five
   beat buttons, tick readout, skip-lulls, spoilers switch, end-hold countdown, and the `#mmwarn`
   hash-mismatch line — all verbatim.
10. **Endcard** — "PARTICLE WORLDS — daveey 0.641", the four-seat table (per-round permille in four
    columns plus the mean, the role held in each round, bumps, and tag ticks), the per-round headline
    ("SPREAD 0.91 covered · DECEIVE the mask lost · CRYPTO the key held · TAG 632 ticks of contact").
    It stops at `var(--band)` and any seek dismisses it.

### Art

Real, and already in the repo. **Particles** are the shipped `data/soldier_{red,blue,green,yellow}*`
sprites on the matching `data/rig_real/*` rigs, drawn with the starter's own compositor and a short
motion trail derived from the recorded velocity (three fading ghosts, one per 4 ticks) so a 94 px/s
glide reads as a glide. **Landmarks** are baked floor art in the four-colour mark palette
(§Sim module edit 2), composited at round start by the starter's pixie path that already bakes
endzone paint. **Symbol bubbles** use the starter's pixel font and its existing bubble geometry.
Walls are `client/art/walls/*.jpg`; the loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the red/blue/green/yellow cog webps — all four families ship).
No solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets `--hudscale` from
the board's on-screen width against a ~760 px reference and toggles `#stage.tiny` at
`boardW <= 620`. Kept verbatim. Particle-worlds adds three rules of its own, all asserted by
`tests/test_viewer.nim`: `.plate-name` keeps the starter's
`flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis` so a policy name never
collapses to "…"; under `.tiny` each plate keeps only `glyph + name + episode score` (the round
permille numeral and the role word are hidden); and under `.tiny` the mark rail collapses to four
colour chips with a single-digit percentage and the crypto panel collapses to two lines
(`KEY F→TEAL` and one row per agent as `G→bone ✗`), so the readouts degrade rather than overflow.

---

## Packaging

- **Repo**: `Metta-AI/cogame-particle-worlds`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `particle-worlds`; `game.name` is
  **`particle-worlds`** (hyphenated, matching the slug), so the secret namespace
  `secret://coworld/particle-worlds/anthropic_api_key`, the page slug, the league seed's
  `game.coworld_name` and the docs all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — one service, **underscored** so the derived manifest placeholder is
  `{{PARTICLE_WORLDS_IMAGE}}` (placeholders come from compose service names — the lantern 0.1.0
  scar; `{{GAME_IMAGE}}` is not a thing):

  ```yaml
  services:
    particle_worlds:
      image: coworld-particle-worlds:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  (ctf ships two services / two images; particle-worlds uses the one-image / two-entrypoints shape
  because the shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure
  (nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:particle-worlds
  src/particle_worlds.nim` → `/bin/particle-worlds`, and the same for
  `src/particle_worlds_player.nim` → `/bin/particle-worlds-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/particle-worlds"]`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (`emscripten/emsdk:4.0.15` as the
  `replay-viewer-builder` target, nimby 0.1.27 pinned by its sha256, `nimby use 2.2.4`,
  `nimby --global sync nimby.lock`, the marker splices, the whole `test -f` / `grep -q`
  assertion block) with
  the asset list swapped: the four soldier families and rigs, walls, locker room, `font.ttf`,
  `pallete.png`, `mpe_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`,
  `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`, `index.html`, `league.html`.
- **`coworld_manifest_template.json`** (validated offline with the CLI's `validate_upload_manifest`
  before the first dispatch — the hive 0.1.0 scar):
  - `$schema` set; top-level `tags`:
    `["particles","mpe","emergent-communication","deception","cooperative","llm","pettingzoo"]`;
    top-level **`episode_timeout_minutes: 20`**; top-level `player[]`; `game.owner` present;
    **no** top-level `replay_viewer`, **no** top-level `version`, **no** `game.display_name`.
  - `game.name` `particle-worlds`; `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.runnable` = `{"type":"game","image":"{{PARTICLE_WORLDS_IMAGE}}",
    "run":["/bin/particle-worlds"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/particle-worlds/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-particle-worlds/tree/main"}` — the `env` entry is
    mandatory: without it the hosted game container never sees the coworld secret and every league
    episode silently plays scripted (hive, 2026-08-23).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`, **every array property bounded**: `tokens` (`minItems` 4, `maxItems` 4),
    `players` (4, 4), `slots` (4, 4), `rounds` (`minItems` 1, `maxItems` 4, items enum
    `["spread","deceive","crypto","tag"]`). Scalars, with defaults: `seed` (679961),
    **`num_agents`** (integer 4..4, default 4), `minPlayers` (4), `teams` (4), `cogsPerTeam` (1),
    `maxTicks` (1080), `maxGames` (4), `turnTicks` (108), `turnBudgetMs` (10000),
    `attempt1Ms` (6000), `retryMs` (3000), `turnSpacingMs` (9000), `wallClockBudgetSeconds` (690),
    `lobbyJoinTimeoutTicks` (2400), `startWaitTicks` (120), `gameOverTicks` (72),
    `mapPath` (`"field"`), `fastMode` (true), `showPlayerLabels` (false), `fullyObservable` (true),
    `visionConeDeg` (180), `visionBubble` (4096), `motionScale` (256), `accel` (250),
    `maxSpeed` (1100), `frictionNum` (192), `frictionDen` (256), `stopThreshold` (8),
    `playerBouncePct` (40), `aimTurnRate` (5), `pursuerAccelPct` (75), `pursuerSpeedPct` (77),
    `landmarkRadius` (18), `landmarkMargin` (140), `landmarkSpacingPx` (300), `spawnRingPx` (250),
    `closeScalePx` (500), `bumpPx` (14), `bumpPenaltyPermille` (1), `bumpPenaltyCap` (250),
    `tagPx` (20), `tagTargetTicks` (120), `orbitRadiusPx` (120), `shadowStandoffPx` (60),
    `evadeProbePx` (200), `symbolCount` (8), `model` (""), `maxOutputTokens` (900).
  - `game.results_schema`: exactly the 22 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","reason","endRule","roundsPlayed"]`; the ten seat-indexed
    arrays `minItems: 4, maxItems: 4` (with `roles` and `roundScores` items themselves
    `minItems: 1, maxItems: 4`); the six round-indexed arrays `minItems: 1, maxItems: 4`;
    `reason` enum `["complete","deadline","fault"]`; `endRule` enum
    `["full_time","wall_clock","sim_fault","host_error"]`; `roundEndRules` items enum
    `["full_time","wall_clock"]`; `modes` items enum `["spread","deceive","crypto","tag"]`.
  - `game.protocols`: **both** `player` and `global`, each
    `{"type":"text","value":"<docs/PROTOCOL.md inlined>"}` — object form, not a bare string (the
    garble v0.1.0 scar). `player` documents the seat websocket, the registration blob, the Sprite v1
    frame a seat receives and the fact that a seat sends no inputs; `global` documents the spectator
    frame — the exact state JSON of §Server, the beat kinds and the record vocabulary.
  - `game.docs`: **`readme`** = `{"type":"text","value":"<README body inlined>"}` and **`pages`** =
    three entries — `rules` ("Rules", `docs/RULES.md` inlined), `protocol` ("Wire protocol",
    `docs/PROTOCOL.md` inlined), `commanding` ("Writing a particle-worlds prompt",
    `docs/COMMANDING.md` inlined) — each `{"id","title","content":{"type":"text","value":…}}`.
    **Text form, not URIs.** `tests/test_manifest.nim` asserts all four values are non-empty.
  - `player[0]` = `{"id":"baseline","type":"player","name":"Drifter Baseline",
    "description":"Scripted particle: covers its assigned mark, speaks the key honestly as the
    speaker, decodes it as the listener, tails the listener as an eavesdropper, and flees or chases
    in tag.","image":"{{PARTICLE_WORLDS_IMAGE}}","run":["/bin/particle-worlds-player"],
    "env":{"PLAYER_SCRIPTED":"drifter"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}` — the **only**
    declared player, and it is seated in **all four** certification slots (the raid 0.1.2
    `players_missing` scar: every declared player entry must occupy a certification slot).
  - **Variants — `num_agents` is 4 in all five**, each with a `description`. They differ only in the
    mode sequence, never in the seat count:

    | id | name | `num_agents` | `rounds` | `maxGames` | `maxTicks` |
    |---|---|---|---|---|---|
    | `default` | Particle worlds — four scenarios | **4** | `["spread","deceive","crypto","tag"]` | 4 | 1080 |
    | `coop` | Spread — cover the marks | **4** | `["spread","spread","spread","spread"]` | 4 | 1080 |
    | `deception` | Deceive — hide the goal | **4** | `["deceive","deceive","deceive","deceive"]` | 4 | 1080 |
    | `comms` | Crypto — talk past the eavesdroppers | **4** | `["crypto","crypto","crypto","crypto"]` | 4 | 1080 |
    | `chase` | Tag — one runner, three hooks | **4** | `["tag","tag","tag","tag"]` | 4 | 1080 |

    Every variant also carries `players` (4 named entries), `slots`
    (`[{"team":"red"},{"team":"blue"},{"team":"green"},{"team":"yellow"}]`), `tokens` (4),
    `minPlayers: 4`, `teams: 4`, `cogsPerTeam: 1`, `mapPath: "field"`, `fullyObservable: true`,
    `turnTicks: 108`, `turnBudgetMs: 10000`, `attempt1Ms: 6000`, `retryMs: 3000`,
    `turnSpacingMs: 9000`, `wallClockBudgetSeconds: 690`, `lobbyJoinTimeoutTicks: 2400`,
    `fastMode: true`, `showPlayerLabels: false`, `seed: 679961`, and the full physics/scoring
    constant block at its defaults. `default` is what the league ranks; because the role cycle gives
    every seat each role index exactly once per episode, each single-mode variant also seats every
    role exactly once (four crypto rounds means each of the four seats is Alice once), which is what
    makes them clean per-mode measurements rather than luck draws.
  - **Certification fixture**: `certification.players` = four `{"player_id":"baseline"}` entries;
    `certification.game_config` = `{"players":[{"name":"P1"},{"name":"P2"},{"name":"P3"},
    {"name":"P4"}], "slots":[{"team":"red"},{"team":"blue"},{"team":"green"},{"team":"yellow"}],
    "tokens":["t0","t1","t2","t3"], "num_agents": 4, "minPlayers": 4, "teams": 4, "cogsPerTeam": 1,
    "seed": 679961, "mapPath": "field", "fullyObservable": true, "rounds":
    ["spread","deceive","crypto","tag"], "maxTicks": 240, "maxGames": 4, "turnTicks": 108,
    "turnBudgetMs": 10000, "attempt1Ms": 6000, "retryMs": 3000, "turnSpacingMs": 0,
    "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 1440, "startWaitTicks": 0,
    "gameOverTicks": 24, "fastMode": true, "showPlayerLabels": false}` — all four seats scripted,
    no LLM, no rate floor, 4 × 240 ticks. That is **960 ticks = 40 s of playback** at 24 fps,
    deliberately longer than any viewer soak window (the ecos 2026-08-23 scar), while `fastMode`
    plays it in a handful of wall seconds. All four modes appear, so the fixture's replay exercises
    every readout and every beat kind — a fixture that only plays `spread` would leave the crypto
    panel untested. **No runner-managed `tokens` beyond the four declared, and no `num_agents`
    omission**: `docker_smoke.sh` cross-checks `certification.game_config.num_agents` against
    `len(certification.players)`, `len(certification.game_config.players)` and `SMOKE_SEATS`, and
    prints `SEAT-COUNT FAIL:` if any of the four disagree. The `certify` step in
    `coworld-release.yml` passes **`--timeout-seconds 300`** (the default 60 s does not cover start +
    connect grace + four rounds + linger — cooperative-hunting 0.1.2).
- **Scaffold from `templates/`** with `<slug>` = `particle-worlds`, `<IMAGE>` =
  `coworld-particle-worlds`, `<SEATS>` = **4**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`, `tools/ci/docker_smoke.sh`
  (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (**copied verbatim**, no substitutions),
  `tools/ci/policies.json`, plus the starter's `tools/build_replay_viewer.sh` (**`chmod +x`**).
  Three additions to the template `ci.yml`:
  - the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format);
  - the `wasm-viewer` job gets a final step
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` — the
    native ↔ wasm determinism gate, which fails if `mpe_mismatch_tick() != -1`;
  - repo variable `NIM_TESTS_RELEASE_ONLY` lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/particle-worlds-player"`, one image,
  env-switched):

  | name | env | role |
  |---|---|---|
  | `particle-worlds-swarm` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey (`ply_44ae9048-3242-4654-881f-6d9d43347fa3`) |
  | `particle-worlds-cipher` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `particle-worlds-drifter` | `PLAYER_SCRIPTED` = `drifter` | filler |
  | `particle-worlds-beeline` | `PLAYER_SCRIPTED` = `beeline` | filler |

  Both champions are `PLAYER_PROMPT` policies; a scripted policy seated as a champion is a failure
  state. Filler versions must differ from champion versions or the platform renames a champion
  "Baseline (N)".
- **Repo layout**: `src/particle_worlds.nim`, `src/particle_worlds_player.nim`,
  `src/mpe/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, arena.nim, map_art.nim,
  field.nim, motion.nim, scoring.nim, beliefs.nim, control.nim, directives.nim, baselines.nim,
  llm.nim, decide.nim, roster.nim, replays.nim, replay_runtime.nim, broadcast.nim, events.nim,
  global.nim, labels.nim, rig_art.nim, wire_constants.nim, server.nim}`,
  `replay-viewer/{mpe_replay.nim, config.nims, static_replay.js, static_replay_worker.js}`,
  `client/`, `data/`, `tests/`, `tools/{build_replay_viewer.sh, gen_wire_constants.nim,
  expand_replay.nim, extract_events.nim, replay_summary.py, record_fixture.sh,
  wasm_replay_smoke.cjs, ci/}`, `docs/{RULES.md, PROTOCOL.md, COMMANDING.md,
  plans/2026-08-26-particle-worlds-design.md}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `particle_worlds.nimble`, `compose.yaml`, `coworld_manifest_template.json`,
  `Dockerfile`, `Dockerfile.replay-viewer`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for an index or fixed-point overflow). CI is the
only harness; the sandbox has no Nim, Docker or emsdk.

1. **`tests/test_motion.nim`** — sim unit tests for the physics: an unpowered particle's speed decays
   by exactly `192/256` per tick and reaches 0 within 40 ticks from `maxSpeed`; a particle driven on
   one axis converges to cruise `1000 ± 2` units and never exceeds `maxSpeed`; a pursuer's cruise is
   `748 ± 2`; a particle driven into a wall stops with zero velocity on that axis and keeps the
   other; two particles driven into each other separate (`playerBouncePct` 40) and neither leaves the
   field; a `crypto` Alice with every d-pad bit set does not move; the whole path is float-free (a
   grep test over the module list); and two runs from the same seed produce byte-identical position
   streams while two different seeds do not.
2. **`tests/test_field.nim`** — the seeded setup: `landmarks` are always 4, always non-wall, always
   ≥ 120 px apart, and ≥ 300 px apart for at least 95 % of 10 000 seeds; the colour assignment is a
   permutation of the four palette colours; `perm` is a permutation of `0..3` and
   `roleIndex[s][r] = (perm[s]+r) mod 4` gives every seat each index exactly once over four rounds;
   `keySymbols` has four distinct symbols from `A..H`; spawn points are walkable, 250 px from the
   centre and ≥ 100 px apart; the rejection sampler terminates for every one of 10 000 seeds; and the
   same seed reproduces every draw across a `resetToLobby`.
3. **`tests/test_scoring.nim`** — the formulas and their signs: `closeness` is 1000 at 0 px, 0 at
   ≥ 500 px and monotone non-increasing; in `spread` all four seats share `base` and only the bump
   debit differs, and `roundP` is never negative even at 1080 bump ticks; in `deceive`
   `goodP + advP == 1000` on every unclamped tick over 100 000 random position draws; in `crypto`
   `pairP` rises with `bc` and falls with `ec`, and an Eve sitting on the goal while Bob is 500 px
   away scores > 0.9 while the pair scores < 0.1; in `tag` a pursuer with 120 contact ticks scores
   1.000 and an untouched evader scores 1.000; every round permille is in `0..1000`; `scores[s]` is
   the mean over **played** rounds and lies in `[0,1]`; `win[s] == (scores[s] >= 0.5)`; a `fault`
   episode scores the banked rounds with `win` false everywhere.
4. **`tests/test_endings.nim`** — end conditions: a round ends exactly on tick `maxTicks` and not the
   tick before or after; `roundLog` records exactly one entry per round played; four rounds give
   `complete`/`full_time` with `roundsPlayed == 4`; the 690 s stop yields `deadline`/`wall_clock`
   with the in-progress round banked from the ticks it ran and unplayed rounds excluded from the
   mean; a tripped invariant yields `fault`/`sim_fault` with a partial replay; `results.reason`,
   `results.endRule`, `roundEndRules[]` and `modes[]` are always members of their declared enums.
5. **`tests/test_control.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines × all four modes × all four
   seats, the emitted directive validates against the reply schema — exactly the seat's own id, an
   intent in the enum, a target inside the field box, `note` ≤ 160 runes, `symbol` a single rune from
   the 9-value alphabet — and every compiled mask has only legal bits: never Up+Down or Left+Right
   together, **never `A`, never `C`**. Plus: the same `(state, order)` pair always yields the same
   byte; a particle inside `ArriveRadius` of its goal sets no d-pad bit; a particle ordered to an
   unreachable target still moves every tick for 120 ticks; `evade` never picks a non-walkable probe;
   `shadow` holds station inside 60 px instead of oscillating; and a `drifter` × 4 episode at seed
   679961 completes, covers ≥ 80 % in its `spread` round, has its `crypto` Bob end on the goal, and
   **beats** a `beeline` × 4 episode at the same seed on the mean episode score.
6. **`tests/test_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   `cogs` as an id-keyed object, unknown and hyphenated intents, absent/NaN targets, off-map targets,
   three cogs, zero cogs, an id belonging to another seat, a 300-character `note`, a lower-case
   symbol, a two-character symbol, a symbol outside `A..H`, and a `note` whose 160th and 161st
   characters are a 4-byte emoji — the truncation must land on the **rune** boundary and the result
   must still round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the
   `drifter` directive plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a
   `throttled` attempt 1 with no other candidate model ⇒ **no** retry and a `throttled` fallback.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all four** seats' calls go
   out in **one parallel batch** (the fake records in-flight windows and the test asserts all four
   intersect); the per-turn budget is enforced with a hung client; `attempt1Ms` and `retryMs` are
   rejected by `sim_config.validate` unless they are whole seconds and `attempt1Ms + retryMs <=
   turnBudgetMs`; `turnSpacingMs` holds the batch rate at ≤ 30 req/min for four seats; the budget
   guard switches to scripted and the episode still ends `complete`; a disconnected seat plays
   `drifter` and revives on reconnect; a never-connecting seat is reported to
   `COGAME_PLAYER_FAILURE_URI` and all four rounds still play; a seat's directive is never empty on
   any tick after turn 0.
8. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full scripted 4-seat,
   4-round episode writes `results.json` and a `COWLDMPE` replay; `parseReplayBytes` accepts it;
   re-simulating from the config + mask log reproduces **every** recorded hash (including the
   landmark draw, the colour permutation, the role cycle and the key, which are all re-derived and
   not load-bearing records); **strict-UTF-8 parse** — `tools/replay_summary.py`'s stdout parses
   under `json.loads(out.decode("utf-8"))` and the embedded config JSON decodes strictly, with the
   fixture forced to carry a non-ASCII policy label and a non-ASCII `note` so the UTF-8 path is
   real; every `directive` record is ≤ 900 runes; `results.reason` is in the legal enum; and the
   stream contains four `roundcard` records, one `directive` per seat per turn, at least one
   non-silent `symbol`, at least one `bump`, one `onpoint`, one `decode`, one `tag`, four
   `roundover`s and exactly one `result` record.
9. **`tests/test_identity_privacy.nim`** — the starter's test, **kept and extended**: no sprite label
   in a *seat* frame, no symbol bubble, no LLM system-or-user message and no `directive` record ever
   contains a sentinel policy address — while the broadcast stream, `roster[].name`, the DOM scorebug
   and `results.names` **must** contain it. That is the two-name-space pin, asserted from both sides.
   Also: a seat's view JSON contains only `RED-alpha`/`BLUE-alpha`/`GREEN-alpha`/`YELLOW-alpha`, and
   never another seat's `note` (this turn's or any turn's).
10. **`tests/test_observation.nim`** — the view and entitlement contract: with `fullyObservable` every
    seat's frame contains all four particles and all four landmarks with their colours; the `radio`
    block carries all four seats' symbols with no distance filter; **the entitlement matrix holds
    from both sides** — in `deceive` the three good agents see `secret.goal` as an integer and the
    adversary sees `null`; in `crypto` Alice sees `goal` + `key`, Bob sees `key` with `goal: null`,
    each Eve sees both `null`; in `spread` and `tag` every seat sees both `null`; and the seed, the
    RNG state, the next round's mode, the next landmark draw and any other seat's current-turn order
    appear nowhere in any seat-facing byte.
11. **`tests/test_manifest.nim`** — `num_agents == 4` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 4`; `results_schema` keys ==
    `particleResultsJson` keys (both directions); `game.protocols` has both `player` and `global` in
    object form; `game.docs.readme` and all three pages are non-empty **text**;
    `replay_viewer.bundle == "static-replay-viewer"`; every variant's
    `wallClockBudgetSeconds <= 0.6 * 1200`; every array property in `config_schema` declares
    `minItems`/`maxItems`; the compose service name derives `{{PARTICLE_WORLDS_IMAGE}}` and the image
    is `coworld-particle-worlds`; `game.name` equals the secret namespace in
    `game.runnable.env.ANTHROPIC_API_KEY_URI`; `config_schema` covers every field
    `sim_config.update` reads and no field it does not; `episode_timeout_minutes == 20`; and **every
    variant's `game_config` constructs a valid sim** (the collab-cooking 0.1.1 scar: test every
    variant, not just the fixture).
12. **`tests/test_viewer.nim`** — the static half of the **viewer smoke** (no browser): assertions
    over `client/replay_broadcast.html` and `client/chrome_common.js` that the transport controls,
    `#scorebug`, `#bannerlane`, `#killfeed`, `#endcard`, `#mmwarn`, the `.tiny` block, the
    `--hudscale` clamp, `#endcard { bottom: var(--band`, the mark rail, the radio strip, the crypto
    panel and the three `.tiny`/`.plate-name` rules are present; that `#viewpanel`, `#minimap` and
    `#zoombar` are **absent**; that `chrome_common.js` is byte-identical to the starter's copy
    (sha256 pinned in the test); that `broadcast_core.js` differs from the starter's in **exactly**
    the `MPE_WIRE` identifier; that the appended game block defines no identifier colliding with the
    chrome alias list (the tandem shadowing guard) and defines CSS for **every** beat kind the sim
    emits and no kind it does not; and that no `ctf_`/`CTF_`/`PB_` identifier survives in `client/`,
    `replay-viewer/` or `src/`.
13. **`tests/test_startup.nim`** — `/bin/particle-worlds` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised **before**
    `config.update` when unpinned and honoured when pinned (so a pinned seed reproduces every draw);
    both entrypoints exist and are executable in the image (asserted by the docker smoke).
14. **`tests/test_perf.nim`** (release-only) — a full 4 × 1080-tick episode with mask compilation and
    four flow fields completes in under 120 s.

Beyond the Nim suite, `ci.yml` runs:

- **`tools/ci/docker_smoke.sh`** — a raw-Docker episode from the certification fixture in the
  production image, seats cross-checked against **`SMOKE_SEATS=4`**, `SMOKE_REQUIRE_REPLAY_JSON=0`,
  asserting the game container exits 0 with `results.json` and a replay, **and** that every *player*
  container exited 0 (the raid 0.1.3 scar). Its replay is uploaded as the `smoke-replay` artifact.
- **the `wasm-viewer` job** — asserts `tools/build_replay_viewer.sh` is present and **executable**
  and `tools/ci/viewer_smoke.mjs` is present, builds the bundle, asserts `index.html` and a non-empty
  `.wasm` exist, then **executes** it:
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/<replay>
  --timeout 90 --soak --strict-text-bounds`, against the replay **`docker-smoke` produced** (the job
  `needs: docker-smoke` and downloads the `smoke-replay` artifact). **The bundle is executed, not
  merely built**; the job fails unless `data-replay-loaded="true"` appears within the timeout, and
  `--strict-text-bounds` is kept because the field is fixed and fits the frame, so
  `canvas_text.never_inside` must be 0 (the symbol bubbles and the crypto panel are exactly the
  chrome that scar was about). `--soak` is kept because the 40 s smoke replay outlasts the soak
  window. The job then runs
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` as the
  native ↔ wasm hash gate.
- **`tools/ci/renderer_fixture.html`** — a worst-case renderer fixture (the cogchemists 2026-08-24
  rule): it loads the real renderer with a full-cap 160-rune `note` on every seat, a non-silent
  symbol on all four particles, the crypto panel populated, and the board at 360 / 620 / 1280 px, and
  `viewer_smoke.mjs --strict-text-bounds` runs against it in its own `ci.yml` step — because
  `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`, so every CI replay carries **zero** LLM text
  and nothing that plays a replay can exercise the feed or the bubbles.

---

## Out of scope (v1)

- **Every ctf mechanic the particle loadout removes**: the hitscan gun and its jitter/exposure model,
  spray cans, floor paint, the paint grid and buff, King of the Hill, the resident/visitor regimes,
  hearts/flags and capture, grenades and the barrage, med kits, shields, cardboard barriers, paint
  puddles, trenches, perks, handicaps, hit points, lives, respawns and kills. **Deleted, not
  disabled** — nothing in particle-worlds can be destroyed.
- **`simple_speaker_listener`, `simple_reference`, `simple_world_comm` and `simple_push`.** They seat
  2, 2, 6 and 2 respectively, and a coworld runs one fixed roster; rewriting them for four seats
  would produce four new games rather than four MPE instances. Their mechanics are not lost —
  `crypto` is a speaker-listener game with eavesdroppers, and every seat can speak in every round,
  which is `simple_reference`'s property. `simple_world_comm`'s **forests** (occlusion) and its
  leader-broadcast hierarchy are the natural v0.2 addition: the mode enum and the `rounds` array are
  already the right shape for a fifth entry.
- **Bit-exactness with PettingZoo / OpenAI MPE / JaxMARL.** This is an adaptation, not a port: MPE is
  float64 world units with per-step vector actions and a soft boundary penalty; particle-worlds is
  integer fixed point on a wall-bounded pixel field with a 4.5 s directive cadence. No test compares
  a trajectory to a reference implementation, and none should.
- **A continuous action space and per-tick control by an external policy.** The v1 channel is one
  directive per 4.5 s plus the server-side control layer, which compiles it to 8-direction impulses.
  The recorded per-particle mask log is already the right shape for a v0.2 protocol addition.
- **Obstacles.** MPE `simple_tag` places two solid obstacles and `simple_world_comm` places forests;
  the v1 field has border walls and nothing else, so the wall mask is static, one board serves every
  mode, and the evader's only edge is speed. Obstacles come with the world-comm mode or not at all.
- **A comm channel bigger than nine values, more than one symbol per turn, per-tick symbols, or any
  free-text channel between seats.** One symbol per particle per turn is the whole point: cheap
  physics, expensive words. `note` stays spectator-only.
- **Learned RL-vector policies.** Both champions are LLM prompt policies and both fillers are
  scripted; nothing here trains.
- **More than four rounds per episode, a fifth mode in the rotation, or state carried between
  episodes.** The wall-clock budget in §Decisions sizes the episode at four rounds of ten turns; a
  key or a convention that persisted across episodes would need platform state that does not exist.
- **Scoring a round the wall clock never reached.** An unplayed round is excluded from the mean, not
  zeroed — see §The game.
- **Player debug-sprite overlays** (ctf's `0x86` channel), **procedural terrain** (the generator, the
  curated pool, `mapkit`, the map editor and the pool-review page), **achievements** (the starter's
  win-gated catalog and its `results.achievements` key are dropped), **audio, 3D, camera cuts**, and
  **any downloaded art asset**.

---

## Amendment — r2 review (2026-08-26)

Recorded by the phase-30 fixer against `reviews/r2-review.md`.

**F1 / checklist item 2 — the wall-clock `deadline` stop is a RECORDED record.** §The replay
says every chat record is "re-applied at playback into non-hashed sim fields … and can never
affect the sim". That holds for every record but one. The engine's wall-clock stop
(§End conditions row 4) banks the round in progress and finishes the game from the server
loop — outside `sim.step` — and every field it writes (`phase`, `winner`, `isDraw`,
`gameOverTimer`, `roundsPlayed`, `roundLog`) is in `gameHash`, while the same iteration
records that state's hash. A wall-clock fact does not follow from sim state, so no
re-simulation can derive it: without a record the last hash of every `deadline` episode was
unreachable and playback sat at `Playing` forever.

So the stop is now written as a `stop` chat record at the tick it fires, and applied on both
sides by one proc — `sim.applyWallClockStop` — the live server as it writes the record,
`applyReplayEvents` as it reads it back, before the same tick's step. `stop` is the ONE
load-bearing chat record; every other record stays presentation-only, and the rule that
"nothing a commander SAYS may move the hash chain" is untouched (the stop is not something a
commander says). `GameVersion` goes 1 → 2: nothing in `gameHash`, the motion model or the
seeded draw order moved, but a GV1 viewer would load a GV2 recording and re-simulate the stop
tick wrong. `tests/test_replay.nim` records a deadline-ended episode and asserts the whole
hash chain re-derives AND that the re-derived sim ends at the same `GameOver`, winner and
banked round as the recorded results document.
