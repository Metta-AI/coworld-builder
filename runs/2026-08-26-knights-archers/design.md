# cogame-knights-archers — design note (2026-08-26, paintbot lineage)

`Metta-AI/cogame-knights-archers` is a four-seat **cooperative horde-defence** coworld: two knights
and two archers hold a gate against a marching horde of the dead, and one breach — or one dead hero —
ends the wave. It is forked from **`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount
`/workspace/starters/coworld-ctf`. **Every convention there holds here unless this note says
otherwise** — the 24 Hz tick loop, the Sprite v1 button-mask input, the continuous integer movement
with per-pixel wall masks and slide collision, the arc-cone attack machinery, the shout channel, the
`COWLDxxx` replay codec with its per-tick `gameHash` chain, the seat/cog split and the directive
decision layer (`src/ctf/{decide,directives,control,baselines,llm}.nim`), the mummy server and its
`COGAME_*` runtime contract, the broadcast chrome (`client/replay_broadcast.html` +
`client/chrome_common.js` + `client/broadcast_core.js`), the emscripten static replay bundle
(`replay-viewer/`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`) and the `GameVersion`
changelog discipline are all inherited. **The starter is chosen by game shape:** knights-archers is a
**real-time game loop with rules written for this coworld** — the paintbot row of the starter table —
and the starter already ships, tested, every layer this game needs except the horde itself: a
server-side per-turn LLM directive layer with a scripted fallback, a deterministic control layer that
turns one directive into per-tick actuator masks, a forward attack cone with reach/half-angle/line of
sight/cooldown (the knight's mace, retuned), a hashed in-flight projectile list (the archer's arrows,
retuned), and a wasm viewer that re-derives every frame from the recorded masks.

**Source idea, verbatim:**

> PZ Knights Archers Zombies (variant of coworld-big-adventure) — a horde mode with knight/archer roles and one-death-ends-it for the existing co-op adventure
>
> Candidate EXTENSION of Metta-AI/coworld-big-adventure — a cooperative explore-fight-collect adventure coworld (incomplete; manifest exists, needs certification). KAZ is a horde mode on top of it: zombies spawn at one edge and march; two knights (melee) and two archers (ranged) kill for reward; a zombie reaching the far edge or killing any player ends the round. Shared failure + role asymmetry. Finish big-adventure's certification first, then add 'horde' as a mode. Also a natural fit for 05 Raid's boss if that card is built here.
>
> Seats: 4 (2 knights + 2 archers)
> Motive: fully cooperative survival
> Integrity: cooperative cross-play scoring; spawns seeded.
> Replay plan: horde pressure bar, kill credits, 'closest call' marker.
>
> Source: PettingZoo knights_archers_zombies_v11; github.com/Metta-AI/coworld-big-adventure.

**Repo shape and the EXTENSION reading.** The idea names an extension of
`Metta-AI/coworld-big-adventure`. The deliverable here is a **new public repo**,
`Metta-AI/cogame-knights-archers`, on the coworld-ctf (paintbot) starter — the paintball /
hidden-agenda precedent for EXTENSION ideas, ruled by the coordinator before this note was written
and not revisited in it. `coworld-big-adventure` is **not** the scaffold and none of its engineering
is inherited; the rules source of truth is PettingZoo `knights_archers_zombies_v11` **semantics**,
adapted into a coworld by this note. The adaptation is not bit-exact to PettingZoo and does not try
to be: PZ KAZ is a pixel-space Pygame environment with per-frame vector actions, and this is a
turn-directive coworld on a 1235 × 659 integer arena. What is carried over verbatim is the *shape* of
the game — a marching horde entering at one edge, a gate at the far edge, melee knights and ranged
archers, kill reward, and the round ending on a breach — plus the idea's own two additions:
**one-death-ends-it** and **fully cooperative shared scoring**.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How knights-archers satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a real-time game loop with new rules; the arc cone, the projectile list, the directive layer and the wasm replay all fork rather than get rewritten. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-knights-archers`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=phalanx` / `PLAYER_SCRIPTED=stand` (both fillers); one image `coworld-knights-archers`, player entrypoint `/bin/knights-archers-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` and `Dockerfile.replay-viewer` kept; the **same Nim sim module** compiles into `replay-viewer/kaz_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` byte-for-byte, `client/broadcast_core.js` byte-for-byte but for one identifier, `client/replay_broadcast.html` = the starter's page **with one appended game block**; heroes are the shipped `data/soldier_red*` / `data/rig_real/red` and `data/soldier_blue*` / `data/rig_real/blue` rigs, zombies the shipped **green** rig family recoloured by the starter's own pixie compositor. No placeholders, no downloads. (§Viewer) |
| Two name spaces | Prompts, in-game labels and shouts carry only `KNIGHT-alpha`, `KNIGHT-beta`, `ARCHER-alpha`, `ARCHER-beta`; real policy names appear only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (`tests/test_identity_privacy.nim`, extended). (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | expected 271 s / absolute worst 612 s against a 720 s budget; a 690 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 4** (2 knights + 2 archers) in variants `default`, `horde-short`, `horde-hard`, `horde-tough` **and** in `certification.game_config`; `<SEATS>` = 4 in `tools/ci/docker_smoke.sh`. (§Packaging) |

Nothing in this note is left open: there is no `OPEN` section, because every reading the idea leaves
loose (how many waves, how fast a zombie walks, whether zombies chase heroes, what "reward" is worth
on a [0,1] league scale) is a rail the designer decides, and each one is decided below with its
reason.

---

## The game

**Knights Archers Zombies is four heroes holding one gate against a rising horde, where a single
mistake ends the wave for everybody.** The dead walk in at the arena's east edge and march west
toward the gate on the west edge. Two knights kill in one blow but must stand inside a zombie's
reach to do it; two archers kill in two arrows from six body-lengths away but walk slower than a
knight and die exactly as fast. A zombie that touches **any** hero kills that hero, and the wave ends
that instant. A zombie that reaches the gate ends it too. Survive the whole wave and the squad banks
a large bonus. Everybody's score is the same score.

### Seats, heroes, roles, aliases

**`num_agents` = 4. One seat = one hero.** No seat commands more than one body, and no body is
uncommanded.

| Seat | Alias (the only name in the game) | Role | Sprite |
|---|---|---|---|
| 0 | `KNIGHT-alpha` | knight (melee) | red rig, mace |
| 1 | `KNIGHT-beta` | knight (melee) | red rig, mace |
| 2 | `ARCHER-alpha` | archer (ranged) | blue rig, bow |
| 3 | `ARCHER-beta` | archer (ranged) | blue rig, bow |

Four seats, not two, because the idea pins the seat count at 4 and because **role asymmetry is only
real when a knight and an archer are two different policies making two different decisions at the
same instant**. It also makes the cooperative claim honest: a squad of four separately-reasoning
seats that share one score is a common-interest game; one commander driving four bodies is a
single-agent game with four avatars.

Four seats means **four parallel LLM calls per turn**, which sets the rate floor in §Decisions.

All four heroes are on the starter's **Red** team; there is no second team of players. The starter's
map keeps `teamCount() == 2` so the arena's two anchors and two capture zones stay defined, and the
game reads them as **furniture, not opponents**:

- `captureZone(Red)` — Red's home column on the arena's **west** edge (`teamAnchor(Red)` seeds the
  west anchor; `CaptureZoneWidth` = 40) — is **the gate**. Its threshold is `gateX` = 40.
- `captureZone(Blue)` — the east column — is **the breach**, where the dead walk in.
- `teamAnchor(Red)` is where the four heroes spawn at the start of every wave, 120 px apart in y.

`num_agents` is **4** everywhere: every manifest variant, the certification fixture and
`SMOKE_SEATS`.

### Map, tick, clock

`mapPath: "arena"` in every variant — the starter's hand-tuned symmetric arena, **1235 × 659** map
pixels, fixed geometry, pinned into the replay's config as usual. No procedural terrain: a fixed
board makes the zombies' flow field, the gate line, the closest-call scale and the viewer's zoom
decision all constant, and the arena is guaranteed traversable west-to-east because that is what CTF
requires of it. Its walls become the horde's chokepoints, which is exactly what a defence needs.

`TargetFps = ReplayFps = 24`, **kept verbatim** (every speed-coupled layer — `PlaybackSpeeds`, the
lull scan, `tickTime`, the transport bar — is keyed to it).

One **wave** is `maxTicks` = **2304** ticks = **96 s**. One **episode** is `maxGames` = **2** waves.
The map, the seed and the connected seats are identical across the two waves; the sim RNG stream
simply continues (no re-seed), and the horde, the arrows, the hero bodies and the wave counters reset
via `resetToLobby()` between waves. Two waves rather than one because a wave can end in eight seconds
to a single careless knight, and one sample of that is noise; two waves is the cheapest average that
still fits the wall-clock budget with room to spare.

Decision turns: `turnTicks` = **96** ticks = **4.0 s** → **24 turns per wave, 48 per episode**.

### The horde

**Spawning.** Zombies enter at `zombieSpawnX` = **1178** (56 px inside the east edge, inside the
breach column). The `y` of each spawn is drawn from the deterministic sim RNG
(`sim.rng.rand(spawnRows.len - 1)`) over **`spawnRows`** — the list of every `y` in
`[ArenaBorder + PlayerHalf, MapHeight - 1 - ArenaBorder - PlayerHalf]` at which the 13 px body box at
`(1178, y)` is clear floor with the spinning diamonds at **spin frame 0**. `spawnRows` is computed
**once at map install**, exactly the way the starter computes a static floor mask, so the native
server and the wasm viewer install the same list from the same `mapSpec`. A map-install assertion
requires `spawnRows.len >= 120`. **Spawns are seeded** (the idea's integrity note): the seed is in the
config, the config is in the replay, and a replay re-derives every spawn.

**The rate ramps.** In integer per-mille-of-a-zombie-per-tick:

```
rate(t) = spawnStartPerMille
        + (spawnMaxPerMille - spawnStartPerMille) * min(t, spawnSaturateTicks) div spawnSaturateTicks
spawnAcc += rate(t);   while spawnAcc >= 1000: spawnAcc -= 1000; spawnOne()
```

with `spawnStartPerMille` = **12** (0.29 zombies/s), `spawnMaxPerMille` = **50** (1.20/s) and
`spawnSaturateTicks` = **1920** (80 s). Over a full 2304-tick wave that integrates to **≈ 79 zombies**.
No spawn fires while `aliveZombies >= spawnCapAlive` = **40** (the accumulator still runs, so pressure
is deferred, not lost), and the hard array cap is `MaxZombies` = **64**.

**Marching.** Each zombie moves once per tick at `zombieSpeed` = **384** motion units
(`MotionScale` = 256) = **1.5 px/tick = 36 px/s**. Unopposed, crossing 1178 → 40 takes
**759 ticks = 31.6 s**, so a zombie that nobody touches for half a minute ends the wave.

Direction comes from **`zombieField`** — an integer BFS distance field, in cells of
`NavCell` = 34 px, computed **once at map install** from every walkable cell inside `captureZone(Red)`
outward across the whole board (diamonds at spin frame 0 treated as wall, 8-connected, unit cost).
A zombie steps toward the neighbouring cell with the lowest field value; ties break to the lowest
neighbour index (N, NE, E, SE, S, SW, W, NW), so the choice is total and deterministic. Movement uses
the starter's own wall-slide collision, so a zombie pressed into a diamond that has rotated into its
lane slides along it. If a zombie is blocked for `zombieStuckTicks` = **24** consecutive ticks, its
step vector is rotated a quarter turn clockwise for the next **12** ticks — the same wall-follower
trick `control.nim` uses on wedged cogs, and for the same reason.

**Lunging.** A zombie with a **living hero within `zombieLungePx` = 90 px** ignores the field and
steps straight at that hero (nearest hero; ties to the lowest seat index) for as long as the hero
stays inside 90 px. This is what makes standing in front of the horde lethal and what gives an archer
a reason to keep its distance. `lungeTarget` (a seat index, or −1) is hashed state.

**Zombies do not collide with each other** — they overlap, and a lane of dead reads as a mass rather
than a queue. They *do* collide with walls, and they never push a hero (contact is fatal anyway).

**Health.** `zombieHp` = **2**. A knight's mace does 2 (one blow), an archer's arrow does 1 (two
arrows). That single number is the whole role asymmetry: the knight trades range for a one-shot, the
archer trades the one-shot for range.

**Killing a hero.** At the end of every tick, if a live zombie's body centre is within
`zombieReach` = **26 px** (Euclidean, integer squared comparison) of a living hero's body centre,
that hero **dies**. There is no hit-point pool: `hitPoints` = 1, `lives` = 1, no respawns.

### The heroes

Common: body 34 px, `hitPoints` 1, `lives` 1, aim decoupled from movement in 256 brads/turn at
`aimTurnRate` = 5 brads/tick (the starter's), the starter's acceleration/friction/collision model
unchanged.

| | **Knight** | **Archer** |
|---|---|---|
| max speed | `MaxSpeed` = 704 units = **2.75 px/tick = 66 px/s** | `archerSpeedPct` = 85 → 598 units = **2.34 px/tick = 56 px/s** |
| attack | mace swing | arrow |
| trigger | button **A** | button **A** |
| reach | `knightReach` = **52 px**, half-angle `knightArcBrads` = **32** (±45°), line of sight required | `arrowRange` = **528 px** (12 px/tick × 44 ticks) |
| damage | `knightDamage` = **2** — one blow kills | `arrowDamage` = **1** — two arrows kill |
| active | swing lit `swingTicks` = **4** ticks, holding the aim it was thrown at | projectile, `arrowSpeed` = 3072 units = **12 px/tick = 288 px/s** |
| cooldown | `knightCooldown` = **18** ticks (0.75 s) | `arrowCooldown` = **12** ticks (0.5 s) |
| hits | every zombie whose centre is inside the wedge, **each at most once per swing** | the **first** zombie whose centre is within `arrowHitRadius` = 14 px of the arrow's swept segment this tick; the arrow is then consumed |

The knight's swing **is** the starter's arc-cone machinery (`canFireArc` / `startArcFire` /
`resolveActiveArcCones` / `selectArcVictims`) with four constants retuned and the victim set changed
from enemy cogs to zombies. The archer's arrow **is** the shape of the starter's hashed in-flight
projectile list (`AirborneGrenade` / `updateGrenades`): a `seq` of integer-positioned objects
advanced once per tick, hashed, replayed, and pruned — flying straight instead of lobbed, and hitting
a body instead of exploding on landing. `MaxArrows` = **64**; the oldest is dropped if a 65th is
fired (unreachable at a 12-tick cooldown and a 44-tick life: 4 archers × 4 live arrows max).

**There is no friendly fire.** Arrows pass through heroes. PettingZoo's KAZ has none, and with
one-death-ends-it a stray arrow would turn every episode into a coin flip on an archer's aim — which
is not the skill the idea wants measured.

### The wave clock, the gate, and the pressure metric

One number is used everywhere the game talks about danger: **`gateDist(z)`**, a zombie's distance to
the gate **along the flow field**, in pixels — `zombieField[cellOf(z)] * NavCell`. A zombie behind a
wall is not "close" just because its `x` is small. `spawnGateDist` is the field distance at the spawn
column (a constant of the installed map, ≈ 1190 px on the arena).

- **Leader** = the live zombie with the smallest `gateDist`. There is always at most one; ties break
  to the lowest zombie id.
- **Pressure %** = `100 - clamp(100 * leaderGateDist div spawnGateDist, 0, 100)`.
- **Closest call** = per wave, `minGateDist` — the smallest `gateDist` any live zombie ever reached —
  and `minGateTick`, the tick it happened. Reset at the start of each wave. This is the idea's
  "closest call" marker, and it is the one statistic that says how nearly the squad lost a wave it
  actually won.

### Scoring, sign, and what the league ranks by

**Fully cooperative: the score is the squad's, and every seat gets it.**

```
kills[s]   = zombies whose LAST damage came from seat s, over the whole episode   (integer, >= 0)
kills      = sum over s of kills[s]                                               = zombiesKilled
cleared    = waves that ended `full_time`                                         (0, 1 or 2)
teamValue  = kills + clearBonus * cleared                    # clearBonus  = 20
teamScore  = min(teamValue, maxGames * roundTarget) / (maxGames * roundTarget)    # roundTarget = 90
credit[s]  = creditEpsilon * kills[s] / max(1, kills)        # creditEpsilon = 0.004
scores[s]  = teamScore + credit[s]
win[s]     = (teamScore >= 0.5)          -- the same boolean for all four seats
```

**Sign: higher is better, and no term is ever negative.** A death costs nothing directly; it costs
the rest of the wave, which is the only currency. `teamScore` lies in [0, 1] and is **identical for
all four seats** — that is the cooperative pin, stated as an equation.

**The league ranks by `results.scores[s]`** (the platform's Elo over per-episode scores; 1000 start,
K = 32). The epsilon exists so a four-way ladder is not a pure draw machine, and it is deliberately
smaller than the smallest team term: one extra team kill is worth `1/180 = 0.005556` to **every**
seat, while the entire epsilon range is **0.004**. The ordering is therefore lexicographic — squad
kills first, personal credit only as a tie-break — so a knight that ignores the line to farm credit
loses whole kills to gain thousandths. `tests/test_scoring.nim` asserts the bound.

**Calibration.** A full wave spawns ≈ 79 zombies. Two waves cleared with 70 kills each is
`(70 + 20) × 2 = 180` → **1.000**. One wave cleared at 70 kills and one lost early at 20 is
`90 + 20 = 110` → **0.611**. Two waves lost inside 40 s at 25 kills each is `50` → **0.278**. The
threshold `teamScore >= 0.5` (= `teamValue >= 90`) means "the squad cleared a wave, or killed as many
as a cleared wave is worth".

**How seats are filled (the idea's cross-play note).** Scoring is cross-play, not self-copies: the
**certification fixture seats four scripted `phalanx` heroes**, and the league division ships **two
scripted fillers** (`phalanx`, `stand`) alongside the two prompt champions (§Packaging), so a
round-robin at four seats normally seats a champion beside at least one scripted partner and never
seats four copies of one policy. The game records what it was given:
`results.role` names each seat's role and the `register` replay record names each seat's policy kind.

### Turn and tick structure — the exact resolution order

Steps 1–5 are the server's frame; steps 6.x are `sim.step`, which is ctf's step body with the
knights-archers insertions called out. Anything not named here is the starter's code, unchanged and
in its original position.

1. **Turn boundary.** If `sim.gameTicksElapsed() mod turnTicks == 0` and `phase == Playing`, the
   directives collected for turn `k = gameTicksElapsed() div turnTicks` (issued by the decision layer
   *before* this tick is stepped — §Decisions) become each seat's active directive, and one
   `directive` record per seat is written to the replay chat stream. `sim.activeDirective[seat]` is
   **excluded from `gameHash`** (the starter's rule for `damagePops`/`skin`): nothing a commander
   says can move the hash chain.
2. **Control compile.** For each hero in seat order (`KNIGHT-alpha, KNIGHT-beta, ARCHER-alpha,
   ARCHER-beta`), `control.compileMask(sim, order, cogIndex)` emits one `uint8` Sprite v1 input mask.
3. **Record.** The four masks go to `sim.step(inputs, prevInputs)` and to
   `replayWriter.writeInputMaskChange` (ctf's function, unchanged), indexed by **hero**. **This is
   the determinism boundary.** The control layer and the LLM are outside it: the viewer never runs
   either, it feeds the recorded masks to the identical sim.
4. `inc sim.tickCount`; `updateAnimatedDiamonds()` — verbatim, so movement, swings, arrows and the
   zombie field's live wall test all resolve against the geometry this tick draws.
5. Roster-driven transitions (`players.len == 0` → abort/reset) — verbatim.
6. **Playing:**
   1. Per hero, in seat order: decrement `fireCooldown` and `arcTicksLeft`; `applyInput` (movement
      and aim rotation, reading the role's max speed); `applyGrenadeInput` / `applyBarrierInput` are
      **deleted**; a fresh **A** press with the weapon ready queues a swing (knight) or an arrow
      (archer).
   2. **NEW `startHeroAttacks()`.** Queued knights call `startArcFire` (the swing lights for 4 ticks
      at the aim it was thrown at); queued archers push one `Arrow` at the archer's centre with
      velocity = the aim unit vector × `arrowSpeed`, `ticksLeft = 44`, and `fireCooldown` is set.
   3. **NEW `resolveSwings()`** — the starter's `resolveActiveArcCones`, retargeted: every lit swing,
      resolved against **one snapshot** taken before any of them apply (no seat-order advantage),
      damages every live zombie whose centre is inside the 52 px ±45° wedge with `paintPathClear`
      line of sight, at most once per activation, `knightDamage` = 2 each. Kills are credited to the
      swinging seat.
   4. **NEW `updateArrows()`.** In arrow-creation order, each arrow advances one step; the swept
      segment from its old to its new centre is tested against the wall mask first (a wall hit
      consumes the arrow and leaves a cosmetic thunk), then against every live zombie's centre with
      `arrowHitRadius` = 14 px, nearest along the segment first. A hit applies `arrowDamage` = 1,
      credits the archer, and consumes the arrow. `ticksLeft` decrements; at 0 the arrow is dropped.
   5. **NEW `updateZombies()`.** In zombie-id order: pick `lungeTarget` (a living hero within 90 px,
      else −1); step 1.5 px along the lunge vector or the flow field as above, with slide collision
      and the stuck rotation; recompute `gateDist`.
   6. **NEW `spawnZombies()`.** Advance `spawnAcc` by `rate(t)`; while it crosses 1000 and
      `aliveZombies < 40`, push one zombie at `(1178, spawnRows[rng.rand(...)])` with `hp = 2`,
      `id = zombieNextId++`.
   7. **NEW `resolveContacts()`.** For each living hero in seat order, if any live zombie's centre is
      within 26 px, the hero dies (`alive = false`, `deathTick = tickCount`), a `casualty` sim event
      is emitted, and `waveCasualty` is set to that seat.
   8. **NEW `updatePressure()`.** Recompute `aliveZombies`, the leader and `leaderGateDist`; if
      `leaderGateDist < minGateDist`, update `minGateDist`/`minGateTick`, and if it is also
      `< closeCallPx` = **200** and at least 48 ticks have passed since the last one, emit a
      `closecall` event (a scrubber beat).
   9. **NEW `checkHordeInvariants()`** — the sim guard (§Sim module). A trip raises `SimGuardError`,
      which the server's tick loop turns into `fault` / `sim_fault`.
   10. **NEW `checkHordeEnd()`** — replaces `checkKothEnd()` / `checkWinCondition()` /
       `checkMaxTicks()`, evaluated **in this order**, so a tick in which both happen is a `breach`:
       1. If any live zombie's `x <= gateX` (40): `finishWave(endRule = breach)`.
       2. Else if `waveCasualty >= 0`: `finishWave(endRule = casualty)`.
       3. Else if `gameTicksElapsed() >= maxTicks`: `inc wavesCleared`;
          `finishWave(endRule = full_time)`.
   11. FX pruning and shout expiry — verbatim (`recentShots`, `hitFlashes`, `bubbleImpacts`,
       `sprayPaintFlashes` cosmetic; `recentShouts` and `splatters` as in the starter).
7. `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` — the starter's per-tick hash
   chain, with the knights-archers state appended after the existing mixes (§Sim module).
8. **Wave end.** When `phase` becomes `GameOver` the server increments `gamesPlayed` (its existing
   line). If `gamesPlayed < maxGames`, the wave's `(ticks, endRule, kills, minGateDist)` are archived
   into `waveLog`, `resetToLobby()` clears the horde, the arrows, the counters and the hero bodies,
   and the next wave starts. If `gamesPlayed >= maxGames`, the episode ends and the artifacts are
   written.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values; `results.endRule` carries the detail of
the **last** wave played and is a closed enum of exactly **six**.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `full_time` | the last wave ran its 2304 ticks with the line intact. The wave is **cleared** and banks `clearBonus`. |
| `complete` | `breach` | a zombie's centre reached `x <= 40`. The wave ends that tick; no clear bonus; kills banked. |
| `complete` | `casualty` | a zombie touched a hero. The wave ends that tick; no clear bonus; kills banked. **This is the idea's one-death-ends-it, and it applies to a death in any seat.** |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **690**) elapsed before the second wave finished. Waves already finished keep their value; the wave in progress banks its kills with no clear bonus; the replay is complete up to the stop tick and the game-over frame is written. **Declared acceptable for phase-60 verification** (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. |
| `fault` | `sim_fault` | `checkHordeInvariants()` tripped. The episode is scored from what was actually banked, `win` is false for every seat, a partial replay is written. |
| `fault` | `host_error` | an unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

A `fault` scores what the squad actually earned rather than a neutral 0.5: in a cooperative game
there is no opponent to be unfair to, and zeroing a real 70-kill wave would be the bigger distortion.

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2400 ticks = 100 s
of lobby wall clock) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only), its hero is driven by the `phalanx` baseline for
the whole episode, and both waves play out.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {phalanx, stand}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=phalanx`. A scripted policy seated as a champion is a failure state.

### Where the decision happens

In the **game server**, not the player container — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the *game* pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/knights-archers/anthropic_api_key` — the
hive gotcha), phase 60 greps the *game* log for `falling back` / `LLM provider is unavailable`,
`docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only, and keeping the control
layer server-side is what makes the recorded mask log reproducible with no network in the loop.

`src/kaz/llm.nim` is the starter's `src/ctf/llm.nim`, forked with no behaviour change:

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
  `{…}`, fence-tolerant) and rune-boundary truncation (`runeLen`/`runeSubStr`) kept unchanged.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **96 ticks (4.0 s of sim time)**, **24 turns per wave, 48 per episode**. At
each turn the server builds **all four** seats' request bodies and issues them as **one parallel
batch** — `client.curl.makeRequests(batch, timeout)`, the shape of the starter's `decideAll`. Seats
are **never** queried sequentially: this is a simultaneous-decision game and serial calls would
quadruple the wall clock for nothing. One call per seat per turn. An episode is at most
4 × 48 = **192 calls**, at most 4 in flight.

Per-turn timing: attempt 1 batch deadline **`attempt1Ms` = 4500 ms**. Any seat that timed out,
errored, returned non-JSON or returned no usable cog entry is retried **once**, again as a single
batch, with a **`retryMs` = 2000 ms** deadline. Worst case 6.5 s ≤ the **`turnBudgetMs` = 7000 ms**
cap enforced by a monotonic deadline around the whole turn.

**Rate floor.** The Bedrock sidecar caps **30 requests/minute per episode** (raid, 2026-08-23), and
four seats per turn would blow straight through it at any fast cadence. A **`turnSpacingMs` = 9000**
wall-clock floor between the *starts* of consecutive batches holds the episode at
`4 × 60 / 9 =` **26.7 req/min**. It is a floor, not a sleep on the critical path: the loop keeps
stepping sim ticks while it waits, and because `turnSpacingMs` (9.0 s) exceeds `turnBudgetMs` (7.0 s),
the spacing — not the model — is what sets the episode's length.

```
48 turns x 9.0 s spacing floor (absolute worst: every wave full length) = 432 s
   typical: waves end early (breach/casualty), ~24 turns                = 216 s
lobby / connect wait (typical 15 s; cap 2400 ticks = 100 s)             =  15 s   (cap: 100 s)
2 x 2304 ticks of play, fastMode, seats report ready                    =  20 s   (wall-paced worst: 60 s)
game-over holds + results + replay write (retrying uploader)            =  20 s
                                                                        -------
expected total                                                          = 271 s   < 720 s
absolute worst case (432 + 100 + 60 + 20)                               = 612 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                                 = 690 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                                   = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 690 and `tests/test_manifest.nim` asserts it.

`fastMode: true` in every variant. ctf's `docs/PROTOCOL.md` warns that the Sprite v1 Ready packet
(`0x85`) corrupts input timing on a wall-clock-paced server — that warning is about *player* clients
whose own inputs are dead-reckoned. Knights-archers' seats send no inputs at all (the server computes
every mask), so the hazard does not exist here and the player harness sends `0x85` after every
received frame.

**Budget guard (early settle without shortening the episode).** At the start of each turn, if
`elapsed + 2 * turnBudget > wallClockBudgetSeconds`, the LLM is switched off for every remaining turn
and the episode finishes on the scripted layer (microseconds per turn), so it ends
`complete/<endRule>` rather than `deadline`. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the outer per-turn deadline,
`lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread (which runs
independently of the game loop, so a 7 s LLM stall cannot drop a connection), the 690 s engine stop,
and ctf's `gameOverTicks` hold before exit. On a seat's **timeout or parse failure**: retry once in
the next batch; on the second failure that seat's directive for that turn becomes the **`phalanx`**
scripted directive and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. A seat that
disconnects mid-episode keeps playing: its directive source degrades to `phalanx` and it revives on
reconnect. **No failure mode leaves a hero unactuated** — the control layer always has a directive:
this turn's, else last turn's, else `phalanx`'s.

### The per-seat view given to the LLM

Built server-side, numbers in **map pixels**, rounded to integers. This object is the tail of the
user message and is mirrored (minus `zombies`) into the `directive` record.

```json
{"wave": 1, "of": 2,
 "turn": 7, "turns": 24, "clock": {"played_s": 28, "left_s": 68},
 "you": {"id": "KNIGHT-alpha", "role": "knight", "alive": true,
         "pos": [412, 330], "aim": 128, "kills": 9,
         "reach_px": 52, "cooldown_ticks": 18, "speed_px_s": 66, "ready": true},
 "gate": {"line_x": 40, "centre": [40, 329], "breach_ends_wave": true},
 "breach": {"line_x": 1178},
 "pressure": {"alive": 17, "leader_gate_px": 388, "leader_pct": 66,
              "spawned": 34, "killed": 17, "closest_call_px": 210,
              "spawn_rate_per_s": 0.7},
 "zombies": [{"id": 118, "pos": [520, 300], "hp": 2, "gate_px": 388,
              "speed_px_s": 36, "lunging_at": null},
             "… every live zombie, smallest gate_px first, at most 40 …"],
 "squad": [{"id": "KNIGHT-beta", "role": "knight", "pos": [600, 420], "alive": true,
            "kills": 7, "last_intent": "intercept",
            "last_note": "I take the south lane", "last_say": "south"},
           "… the other three seats …"],
 "last_turn": {"your_kills": 2, "your_hits": 3, "your_shots": 4,
               "team_kills": 6, "zombies_gained": 1},
 "your_last_directive": "… your seat's own directive last turn, or null on turn 0 …",
 "score": {"team": 0.41, "team_kills": 74, "waves_cleared": 0, "round_target": 90,
           "clear_bonus": 20}}
```

### Per-seat observation: exactly what is visible and what is hidden

**The board is fully observable.** `fogOfWar: false` in every shipped variant: every seat sees the
whole arena, every live zombie and every hero. Three reasons, decided here and not revisited:
PettingZoo's KAZ is fully observable; this is a *cooperative* game, where hiding the board from
partners adds a coordination puzzle the idea never asks for and subtracts the one the idea does ask
for (role division under time pressure); and the idea's own replay plan — a horde **pressure bar** —
is a public readout, which only makes sense if the pressure is public.

**Visible**, on the seat's Sprite v1 stream (one binary message per tick) and, in the same shape, in
the view JSON above:

- The static map, its walkability sprite and the live rotating diamonds.
- **The gate and the breach**, as stated 1 × 1 markers in the init snapshot and refreshed each tick,
  in the starter's stated-marker idiom: `gate <x0>,<y0> <x1>,<y1>` and `breach <x0>,<y0> <x1>,<y1>`.
- **Every live zombie**: position, hit points, `gate_px`, and whether it is lunging and at whom.
- **Every hero**: alias, role, position, aim, alive flag, kill count, weapon-ready flag.
- **The pressure block**: zombies alive, leader distance and percentage, spawned, killed, this wave's
  closest call so far, and the current spawn rate.
- **The other three seats' LAST-turn `note` and `say`** and their last intent — the squad channel.
- Shouts within `ShoutRange` (247 px), labelled with the shouter's anonymous alias.
- The wave index, the turn index, the clock, the team score so far and the waves cleared.

**Hidden:** the other seats' directives **for the turn being decided** (all four decide
simultaneously, which is exactly why `say` and `note` matter); every seat's `PLAYER_PROMPT`; the
identity of any policy (real names never reach a seat); the episode seed; the RNG state and therefore
every future spawn row and spawn time; the exact tick a zombie will next lunge; and future ticks in
general.

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape, so the two
policy kinds are strictly comparable and the same validator runs on both. The `cogs` array is kept
(rather than flattening to one order) because it is the starter's schema, its parser and its tests
are already written against it, and it makes a future multi-hero seat free.

```json
{"note": "archers hold the choke, I take the north lane",
 "cogs": [{"id": "KNIGHT-alpha", "intent": "intercept", "target": [820, 300],
           "face": [900, 290], "say": "north"}]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes on a rune boundary; newlines collapse to spaces |
| `cogs` | array | **exactly 1** entry — the seat's own hero | extra entries dropped; an empty or missing array keeps last turn's directive, else `phalanx`'s |
| `cogs[].id` | string | the seat's own alias, case-insensitive, **≤ 16 runes** | an unmatched entry is assigned to the seat's hero by position |
| `cogs[].intent` | enum | `intercept` `hold` `screen` `focus` `fall_back` `regroup` | → `intercept` |
| `cogs[].target` | [int, int] | finite; clamped to the map box `[0, w-1] × [0, h-1]` and snapped to the nearest walkable pixel | missing / non-finite → the gate centre `[40, 329]` |
| `cogs[].face` | [int, int] \| null | finite; same clamp | → `null` (the control layer picks the aim) |
| `cogs[].say` | string | **≤ 10 runes** — it becomes a real in-game **shout** (`ShoutMaxChars` = 10), audible to every hero within `ShoutRange` = 247 px, one per hero per second | truncated to 10 runes, then the starter's `sanitizeSay` (printable ASCII minus `{`/`}`, trimmed) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized `directive` record
**≤ 900 runes** (asserted in `tests/test_replay.nim`). `register.prompt` is capped at **≤ 4000 runes**
at the transport (over-long is truncated, never rejected) and is **never** written to the replay or
the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — the starter's
`truncateRunes` (`runeLen`/`runeSubStr`). Slicing a `string` by byte index on any path to the replay
is forbidden. A byte-truncated multi-byte character is exactly the bug that makes replay bytes render
in a browser but fail a strict parser, and §Tests pins it with a 4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose; accept `cogs` as an object keyed by id; accept a bare order object without the `cogs`
wrapper; accept numeric strings for `target`/`face`; accept an unknown-case or hyphenated intent by
normalising. Only when no object with at least one usable order can be recovered do the retry and
then the fallback fire.

### System prompt (fixed; identical for both champions, one `<ROLE>` paragraph per seat)

Sent as the system message. The knight and archer paragraphs below are both present in the prompt;
the line naming which one the seat is is filled from the seat's role.

```
You are ONE hero defending a keep against a horde of the dead, in a top-down
arena 1235 by 659 pixels. The dead walk in at the EAST edge (x=1178) and march
WEST toward your gate (x=40). Two knights and two archers hold the line
together. You are <ROLE>.
KNIGHT: you swing a mace. It reaches 52 pixels in a 90-degree wedge in front of
you and kills a zombie in ONE blow, once every 0.75 seconds. You are the fastest
thing on the field at 66 pixels per second.
ARCHER: you loose arrows. They fly 528 pixels in a straight line at 288 pixels
per second and take TWO hits to kill a zombie, one shot every 0.5 seconds. You
move at 56 pixels per second - slower than a knight, faster than a zombie.
A zombie walks at 36 pixels per second and kills any hero it touches within 26
pixels. Zombies within 90 pixels of a hero stop marching and charge that hero.
THE WAVE ENDS THE INSTANT a zombie reaches the gate, OR a zombie kills ANY hero
- including a hero who is not you. There are no respawns and no second chances.
Your score is your SQUAD'S score: every zombie the four of you kill, plus a big
bonus for surviving the whole 96-second wave. Killing more than your share is
worth nothing if the line breaks.
Every 4 seconds you issue ONE order for yourself. A deterministic controller
executes it for the next 4 seconds: it walks you where you asked around walls,
turns you to face what you asked, and attacks when the blow will land. You never
control motors or the trigger directly.
You can see the whole board: every zombie, every hero, and what the other three
said LAST turn. You cannot see what they are deciding THIS turn - all four of you
decide at the same moment - so use "say" to tell them what you are about to do.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars","cogs":[{"id":"<your own id>",
  "intent":"intercept|hold|screen|focus|fall_back|regroup",
  "target":[x,y],
  "face":[x,y] or null,
  "say":"<=10 chars"}]}
Intents: intercept = go meet the zombie closest to the gate and kill it (a knight
closes to touching range; an archer stops at 300 pixels and shoots);
hold = stand at `target` and kill whatever walks into reach;
screen = put yourself 120 pixels in front of the leading zombie, between it and
the gate; focus = attack the zombie nearest `target`; fall_back = walk to `target`
and do not attack; regroup = move to the middle of your surviving squadmates.
`face` biases your aim. `say` is SHOUTED and every hero hears it.
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading (the
starter's `operatorBlock`), then a blank line, then the seat's view JSON. The prompt text is never
echoed into the replay — only `policyKind` and the resulting directive are.

### Champion #1 — `knights-archers-warden` (owner daveey), `PLAYER_PROMPT`

```
Hold a LINE, do not chase. Pick your lane from your own y position: if you are
north of y=330 you own the north half, otherwise the south half, and you fight
only the zombies whose y is in your half unless nobody else can reach one.
If you are a KNIGHT: your standing order is "intercept". Take the zombie in your
half with the smallest gate_px. Say its id, so the other knight takes a different
one. Never let a zombie inside 400 gate_px while you are alive and idle - a
zombie past 400 is thirty seconds from ending the wave and nothing else you do
matters more. Only use "fall_back" when three or more zombies are within 120
pixels of you at once: you cannot swing them all, and a dead knight ends the wave
for everybody. Retreat to [200, your own y], then intercept again.
If you are an ARCHER: your standing order is "focus", targeting the zombie in
your half with the smallest gate_px, and you stand between 300 and 450 pixels
from it. If anything is within 200 pixels of you, switch to "fall_back" toward
[120, your own y] for one turn - you are dead if it touches you and you are worth
two knights' worth of kills over a whole wave. When your half is empty, use
"hold" at [500, your own y] facing east and let them come to you.
When the pressure block says alive is 25 or more, everybody stops lane discipline:
knights "screen" the leader, archers "focus" the leader, and you say "wall".
```

### Champion #2 — `knights-archers-volley` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Kill the leader first, together, and let the rest walk. The leader is the zombie
with the smallest gate_px in the whole pressure block; every turn, everyone's
target is derived from it.
If you are an ARCHER: give "focus" with target the leader's position, every turn,
without exception. Two archers on one zombie is two arrows in the same second and
that is a kill; two archers on two zombies is two wounded zombies and no kill.
Stand at 350 to 500 pixels and never move toward the leader if that would put you
inside 250 pixels of ANY zombie - use "fall_back" toward the gate instead and
shoot from further out. Distance is your whole role.
If you are a KNIGHT: give "screen" with target the leader every turn while the
leader is inside 600 gate_px, so you are standing between it and the gate and the
archers are shooting past you into its face. When the leader is further out than
600 gate_px, switch to "intercept" on the SECOND-closest zombie instead - the
archers have the leader, and your job is to stop the next one becoming it. Say
which one you took.
Nobody ever uses "regroup" while a zombie is inside 300 gate_px. When the board is
clear of anything inside 700 gate_px, both knights "hold" at [560, 240] and
[560, 420] and both archers "hold" at [300, 240] and [300, 420]: that is the
choke, and re-forming it between rushes is how you survive the second half of the
wave when the spawn rate doubles.
```

### The control layer (deterministic, shared by every policy)

`src/kaz/control.nim`, forked from `src/ctf/control.nim`. Both LLM directives and scripted directives
are compiled by the *same* code, so the two policy kinds are strictly comparable. It is a pure
function of `(sim state, order, cogIndex) -> uint8`, and it navigates with the starter's own proven
components: `buildNavGrid` (a 34 px cell grid over `sim.isWall`), `computeField(goal)` (a BFS flow
field to a goal cell), `navSteer` (the steering vector along the field with line-of-sight
shortcutting), `nearestOpenCell`, the `StuckTicks` quarter-turn escape, and `bradsOfVector`/
`bradsErr` for the aim. Flow fields are cached and recomputed at most once per 12 ticks per distinct
goal cell.

**`roleStandoff`** = 0 px for a knight (walk onto it) and **300 px** for an archer.

For each hero, each tick:

1. **Goal point `g`** by intent (`L` = the leader, `G` = the gate centre `[40, 329]`,
   `t` = the order's target):
   - `intercept`: `L`'s position for a knight; for an archer, the point `roleStandoff` px from `L`
     along the direction from `L` toward `G` — i.e. it backs off onto the gate side and shoots. If no
     zombie is alive, `g = t`.
   - `hold`: `t`.
   - `screen`: the point `screenStandoff` = **120 px** from `L` along `L → G`, snapped to the nearest
     walkable pixel. If no zombie is alive, `g = t`.
   - `focus`: `z*` = the live zombie nearest `t`. For a knight, `g = z*`. For an archer, the first
     clear point found by probing 16 evenly spaced points on the circle of radius `archerRange` = 460
     px around `z*` (starting from the direction of `z*` → `G` and alternating outward), requiring a
     clear line to `z*` and walkable ground; if none is clear, `g = z*`. If no zombie is alive,
     `g = t`.
   - `fall_back`: `t`, clamped into `captureZone(Red)` (the gate column).
   - `regroup`: the integer mean of the **other** living heroes' centres; `G` if none is alive.
2. **D-pad** = the octant bits of `navSteer(heroPos, g)`; a hero within `ArriveRadius` of `g` stops
   moving. Diagonals only when the minor axis is ≥ 40 % of the major, so a straight run does not
   chatter between octants.
3. **Aim**, in priority order: the nearest live zombie within `aimRange` (knight **120 px**, archer
   **560 px**) with a clear path — for an archer, aimed at the zombie's **predicted** position
   `pos + vel * (dist div arrowSpeed)` in integers, which is what makes an archer actually connect on
   a moving target; else `face` when the order gave one; else the direction of `g`; else due **east**
   (the direction the horde comes from). `B` / `Select` are set to turn toward it (`aimTurnRate` = 5
   brads/tick) and neither is set when `abs(err) <= AimDeadBrads`.
4. **Trigger `A`.** Never set for `fall_back`. Never set while `fireCooldown > 0` or (knight)
   `arcTicksLeft > 0`.
   - **Knight**: set iff a live zombie's centre is inside the 52 px, ±45° wedge around the current
     aim with a clear path.
   - **Archer**: set iff `abs(err) <= 8` brads and some live zombie's **predicted** centre lies within
     `arrowHitRadius + 10` = 24 px of the aim ray inside `arrowRange`, with a clear path. An archer
     therefore only spends an arrow it expects to land, which is why two archers out-kill four at the
     same shot rate.
5. **Never both.** Up+Down and Left+Right are never set together (each pair comes from one sign), and
   `C` is never set — knights-archers places nothing `C` could throw.

### Scripted baselines

Both emit the *same* directive object an LLM does, on the same 4.0 s cadence, so their output is
legal by construction and directly comparable. Both are pure functions of the world state, which is
what makes the bounded-orders test in §Tests meaningful. Both are documented in `docs/RULES.md`, so
"cooperating with a partner you did not write" here means "a partner whose published rules you know".

- **`phalanx`** — the certification player, the per-turn fallback, the driver of a no-show seat, and
  the default. Role-aware, and it divides the horde by rank so two seats never duplicate work. Rank
  the live zombies by `gateDist` ascending, `z[0]` the leader:
  - `KNIGHT-alpha` → `intercept`, target `z[0]`. `KNIGHT-beta` → `intercept`, target `z[1]` (or
    `z[0]` when only one is alive). Knights never fall back.
  - `ARCHER-alpha` → `focus`, target `z[0]`. `ARCHER-beta` → `focus`, target `z[2]` (or the highest
    available rank). An archer with any live zombie within `archerPanicPx` = **150 px** switches to
    `fall_back` toward `[120, its own y]` for that turn.
  - With no zombies alive: knights `hold` at `[560, 240]` and `[560, 420]`, archers `hold` at
    `[300, 240]` and `[300, 420]` — the choke.
  - Fixed short says: `"on it"`, `"loose"`, `"back"`, `"choke"`. Fixed note: `"hold the gate"`.
- **`stand`** — the second filler, deliberately weaker and different in **shape** so the ladder gets
  a spread rather than two versions of one bot: every hero is `hold` at its choke post for the whole
  wave and never moves. It kills whatever walks into reach and leaks everything that walks around it.
  It loses to `phalanx` on both waves at the pinned seed, which `tests/test_control.nim` asserts.

---

## Sim module

### What is kept, what changes, by path

The fork is a rename sweep (`ctf` → `kaz`, `CTF_WIRE` → `KAZ_WIRE`; a CI grep asserts no `ctf_`/`CTF_`
identifier survives outside comments and history notes) plus the named edits below.

**Kept**:

| Path (starter → fork) | Why it is kept |
|---|---|
| `src/ctf/arena.nim`, `map_art.nim` → `src/kaz/` | the arena geometry, the wall/walk masks, `teamAnchor`, `captureZone`, `isProtectedFloor`, the map bake and the `mapSpec` round-trip. The hand-tuned `arena` layout **is** the board; the generator, pool, `mapgen_styles.nim`, `map_pool.nim`, `tools/mapkit.nim`, `tools/map_editor*`, `tools/gen_map_pool.nim` and `docs/pool-review.html` are **deleted** (this game pins `mapPath: "arena"`). |
| `src/ctf/replays.nim`, `replay_runtime.nim` | the whole replay codec, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket`. |
| `src/ctf/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, the replay-switch path, the `COGAME_*` contract, `declarePlayerFailure`, the artifact-write block, the `gamesPlayed` loop, the `wallClockBudgetSeconds` stop. Four named edits below. |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` | the whole per-turn decision layer: the parallel batch, the two deadlines, `turnSpacingMs`, the budget guard, tolerant parsing, rune caps, the fallback ladder, the nav grid and steering. Retargeted, not rewritten. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby`, `randomEndzonePosition`. |
| `src/ctf/roster.nim` | join/auth/identities/`IdentityNames`/`squadResultsJson`. Two named edits below. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/broadcast.nim` | `stepEvents`, `buildStateJson`, `rosterJson`, `firstPersonJson`, the lull scan, the beat timeline. Retargeted fields, same structure. |
| `src/ctf/global.nim` | the sprite/object pools, the soldier/rig compositor, the FX families, the first-person raycast. Three named edits below. |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | label vocabulary, the rig art compositor, the one-source JS wire constants. |
| `client/broadcast_core.js`, `chrome_common.js`, `replay_broadcast.html`, `league_replayer.html` | the broadcast chrome (§Viewer). |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js`, `ctf_replay.nim` → `kaz_replay.nim` | the emscripten link flags (`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, `useMalloc`, the `EXPORTED_FUNCTIONS` list), the OffscreenCanvas Worker, the stage-note diagnostics, the `data-replay-loaded`/`data-replay-error` signalling. |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix` | build, bundle and forensics wiring. |
| `data/` art: `soldier_{red,blue,green}*`, `rig_real/{red,blue,green}/*`, `font.ttf`, `atlas/*`, `ascii.png`, `arena_floor.png`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,red_*.webp,blue_*.webp,green_*.webp}` | real art, kept and reassigned (§Viewer §Art). `heart_*`, `ped_*`, `paintgun*`, `medkit`, `shield`, `paintbomb`, `spraycan*`, all yellow art are deleted with the mechanics they belong to. |

**Deleted** (with their tests, tools and docs), not disabled — every one of them is a config surface
the horde rules would otherwise have to reason about: the hitscan gun and its jitter/exposure model,
spray cans and floor paint, the paint grid, the paint buff, King of the Hill and `hillTicks`, the
`resident`/`visitor` regimes, hearts/flags and capture, grenades and the barrage, med kits, shields,
cardboard barriers, paint puddles, trenches, perks, handicaps, four-team free-for-all, the procedural
generator and map pool, the map editor, mapkit, the achievements catalog, and campaign mode.

**New modules:** `src/kaz/horde.nim` (the zombie list, the spawn schedule, `zombieField`, marching,
lunging, contacts, the pressure metric, the closest call), `src/kaz/arrows.nim` (the in-flight arrow
list and its resolution), `src/kaz/melee.nim` (the retuned swing wedge), and the entrypoints
`src/knights_archers.nim` (`/bin/knights-archers`) and `src/knights_archers_player.nim`
(`/bin/knights-archers-player`).

### The four named edits to `server.nim`

1. **Turn boundary.** Unchanged in shape from the starter, with `turnTicks` = 96 and four seats in the
   batch instead of two.
2. **Registration interception.** A player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration and is **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim (the paintball round-3 scar). Any other chat text from a seat is dropped — heroes shout,
   seats do not.
3. **Wave switch.** When `gamesPlayed` increments, the loop archives
   `(ticks, endRule, kills, minGateDist)` into `waveLog` before `resetToLobby()`.
4. **Wall-clock stop.** The starter's `wallClockBudgetSeconds` check at the top of every loop
   iteration, kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.

### The two named edits to `roster.nim`

1. **Aliases carry the role.** `cogAlias(cogIndex)` returns `ROLE-identity`:
   `roleOf(cogIndex) = if cogIndex < 2: knight else: archer`, identity =
   `IdentityNames[cogIndex mod 2]` → `KNIGHT-alpha`, `KNIGHT-beta`, `ARCHER-alpha`, `ARCHER-beta`.
   `cogSeat(cogIndex) = cogIndex` (identity: one seat, one hero), and every hero's `team` is `Red`.
   `slotIdentityIndex`/`shoutIdentityName` follow from `cogAlias`, so shout bubbles and sprite labels
   inherit the two-name-space rule with no further change.
2. **`squadResultsJson` becomes `heroResultsJson`** — one entry per seat, four entries in every
   seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **Fog is off.** `buildSpriteProtocolPlayerUpdates` takes a **seat** index and, when
   `config.fogOfWar` is false, uses an all-visible mask instead of the seat's fov cache. The
   shadowcasting code stays (the first-person PIP still raycasts); only the per-seat mask changes.
2. **Zombie and arrow sprite pools.** New pools `ZombieSpriteBase`/`ZombieObjectBase` sized to
   `MaxZombies` = 64 and `ArrowSpriteBase`/`ArrowObjectBase` sized to `MaxArrows` = 64, filled in
   zombie-id / arrow order, emitted incrementally like the starter's other object families. A live
   frame is therefore at most 4 heroes + 40 zombies + 16 arrows of moving objects — well inside the
   32-cog budget the starter already carries.
3. **The gate and the breach are baked floor art**, not sprites: a portcullis strip over the gate
   column and a torn, blood-dark strip over the breach column, composited into `arena_floor.png` at
   map install with pixie, the same way the starter bakes endzone paint.

### Determinism, native ↔ wasm

The mechanism is ctf's, unchanged, and it is the reason the starter is worth forking:

1. The server writes a `COWLDKAZ` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `mapSpec`, roster, every tuning field), then the record stream —
   joins (name, slot, token), leaves, per-**hero** input-mask changes, chat records (directives,
   fallbacks, register, budget guard, result) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/kaz_replay.nim` — which imports the **same**
   `src/kaz/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `kaz_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then `kaz_frame`
   re-steps the sim from the recorded masks and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). A single divergent bit is caught at the tick it happens and
   surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` gains**, appended after the existing mixes so the ordering stays stable: per zombie
   `(id, x, y, hp, lungeTarget, stuckTicks, stuckRotTicks)`; `zombieNextId`, `spawnAcc`,
   `aliveZombies`, `zombiesSpawned`, `zombiesKilled`; per arrow `(x, y, vx, vy, owner, ticksLeft)`;
   per hero `(alive, kills, hits, shots, swings, fireCooldown, arcTicksLeft)`; and
   `minGateDist`, `minGateTick`, `wavesCleared`, `waveCasualty`. `gateDist` is **derived**, not
   hashed (it is a pure function of position and the installed field).
5. All new sim arithmetic is **integer only** — cell indices, the BFS field, the swept-segment hit
   tests (`int64` intermediates), the wedge predicate, the spawn accumulator, the lead prediction. No
   floating point is introduced into `horde.nim`, `arrows.nim`, `melee.nim`, `control.nim` or the
   hashed path; a CI grep over `src/kaz/{sim,sim_types,sim_state,horde,arrows,melee,control}.nim` for
   `sin|cos|tan|arctan|sqrt|hypot|float` enforces it. This matters because Nim's `int` is 32-bit under
   `--cpu:wasm32` and the wasm build re-derives every tick.

**The sim guard `checkHordeInvariants()`** (step 6.9), evaluated every tick before any wave can be
ended on the numbers it checks: every live zombie's centre is inside the map box and on non-wall
floor; `aliveZombies` equals a full recount; `zombies.len <= MaxZombies` and `arrows.len <= MaxArrows`;
every arrow centre is inside the map box; `sum(kills[s]) == zombiesKilled`; and
`zombiesKilled + aliveZombies <= zombiesSpawned`. A trip raises `SimGuardError` → `fault`/`sim_fault`.

**Perf target:** 2 × 2304 ticks of sim plus mask compilation, 40 marching zombies and 16 live arrows
in under 20 s on a CI runner; `tests/test_perf.nim` bounds it at 120 s.

---

## Server, player, protocol

`src/kaz/server.nim` is ctf's `server.nim` with the four edits named above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`, `GET /reward`), same `COGAME_*`
runtime contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`,
`COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same real pages on both `/client/` routes
registered before any catch-all (the lantern 0.1.1 cert probe), same bounded `/healthz`+`/global`
shutdown grace after artifacts are written (lantern 0.1.3), same `src/knights_archers.nim` entrypoint
with seed randomisation before `config.update`.

### The player container

`src/knights_archers_player.nim` (built to `/bin/knights-archers-player`) is the starter's
`src/paintball_player.nim`, forked with the baseline names changed. It reads
`COWORLD_PLAYER_WS_URL`, `PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects with
bounded dialling (240 × 500 ms), and sends **one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"phalanx"|"stand"|null,"policy":"<free label>"}
```

Registration is **re-sent** for the first ~10 s of frames (10 re-sends, ~1 s apart), because joins are
slot-sequential and a seat whose slot is not the next open one is not admitted until the lower slots
have joined — the paintball round-3 scar, where a champion played the scripted baseline for a whole
episode. It then sends the Sprite v1 Ready packet (`0x85`) after each received frame — legitimate
here because it never sends inputs — and otherwise only receives. A seat that never registers, or
registers with neither field, is `scripted: "phalanx"`. The receive loop is wrapped in
`try/except CatchableError`, re-dials a dropped socket up to 6 times, and **exits 0 on a dead
socket** — the raid 0.1.3 scar: whisky's `receiveMessage` raises on a close frame, and the game's
`quit(0)` can outrun the flushed frame, so a naive player exits 1 and fails certification
intermittently.

### Results document

Written by `sim.heroResultsJson()` to `COGAME_RESULTS_URI`. It must equal the manifest's
`results_schema` key-for-key — that schema is `additionalProperties: false` and the certifier rejects
any unknown field. Adding or removing a key here means editing `coworld_manifest_template.json` in
the same commit.

```json
{"names": ["daveey", "daveey-1", "knights-archers-phalanx", "knights-archers-stand"],
 "scores": [0.6127, 0.6114, 0.6136, 0.6120],
 "win": [true, true, true, true],
 "role": ["knight", "knight", "archer", "archer"],
 "alias": ["KNIGHT-alpha", "KNIGHT-beta", "ARCHER-alpha", "ARCHER-beta"],
 "kills": [24, 19, 28, 22],
 "hits": [24, 19, 51, 41],
 "shots": [61, 48, 96, 84],
 "llmTurns": [24, 24, 0, 0],
 "fallbackTurns": [0, 1, 0, 0],
 "teamScore": 0.611,
 "teamKills": 93,
 "wavesCleared": 1,
 "waveTicks": [2304, 807],
 "waveEndRules": ["full_time", "casualty"],
 "waveKills": [70, 23],
 "closestCallPx": [136, 612],
 "reason": "complete",
 "endRule": "casualty",
 "games": 2,
 "finalTick": 3111,
 "seed": 679961}
```

`names` are the **real policy names** (spectator side). `alias` and `role` carry the in-game names.
The ten seat-indexed arrays (`names`, `scores`, `win`, `role`, `alias`, `kills`, `hits`, `shots`,
`llmTurns`, `fallbackTurns`) have exactly `num_agents` = **4** entries, which is what
`docker_smoke.sh` cross-checks against `SMOKE_SEATS`. The four wave-indexed arrays (`waveTicks`,
`waveEndRules`, `waveKills`, `closestCallPx`) have between 1 and `maxGames` entries — a `deadline`
can cut the episode after one wave — and the schema bounds them `minItems: 1, maxItems: 4`.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDKAZ`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse.
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: it takes a `.replay` path and prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"knights-archers/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "roles":[…],"policyKinds":[…],"waves":…,"tickCount":…,"directives":[…],"fallbacks":N,
  "results":{…}}`. It brace-matches the config JSON from the first `{` (the technique the starter's
  `AGENTS.md` documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.teamKills' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "knights-archers/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.teamKills > 0`, and the champion seats' directives
  `source == "llm"` with non-empty `note` and real intents — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDKAZ`, format version, `gameName` `knights-archers`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `mapSpec` (the full resolved arena geometry), `maxTicks`, `maxGames`, `turnTicks`, every horde/hero/arrow constant, `roles`, `players[].name` (real names), `slots[]`, `fastMode` |
| joins | per **seat**: `name` (real policy name), `slot`, `token` |
| inputs | per **hero** (0..3), on change: the `uint8` actuator mask — the action log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The **entire horde is re-derived**, never recorded: spawns come from the sim RNG seeded by the config
seed, and marching is a pure function of the installed field. That is why the file stays small —
~3100 ticks of hashes plus ~30 k mask-change records plus 192 directive records ≈ **350 KB**, well
under 1 MB — and why a hash mismatch is a real integrity signal rather than a rendering nit.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed sim fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `role`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `wave`, `turn`, `seat`, `alias`, `role`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note` (≤ 160 runes), `cogs`:[{`id`,`intent`,`target`,`face`,`say`}] |
| `fallback` | `wave`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. They feed
the match feed, the scrubber beats and the momentum graph:

`phase`; `wavestart` `{wave}`; `spawn` `{id, y}` (throttled to one record per 12 ticks, with a
`count`); `swing` `{by}`; `shot` `{by}`; `hit` `{by, zombie, dmg, hpLeft}`; `kill`
`{by, alias, role, zombie, gate_px}`; `lunge` `{zombie, at}` (throttled one per 24 ticks);
`closecall` `{gate_px, tick}`; `casualty` `{who, alias, zombie}`; `breach` `{zombie}`; `waveover`
`{wave, endRule, kills, ticks, closestCallPx}`.

**Beats** (scrubber markers, and the only kinds the appended block emits): `wavestart`, `closecall`,
`casualty`, `breach`, `waveover`.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Swing, Shot, ZombieHit, ZombieKill, ZombieSpawn, HeroDeath, Breach,
PhaseChange, ShoutEvent` and extended with `CloseCall, Directive`; the mandatory trailing summary row
(`type`, `ticks`, `events`, `gameVersion`) is kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is the
starter's script, kept, with two literals changed (`image_tag`, and the `docker cp` source
`/workspace/knights-archers/replay-viewer/dist/.`); it builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copies the dist out. It must stay committed **executable**
(`coworld build` requires `os.X_OK`), and the hook `mkdir -p`s the output parent before its
containment check (the ecos 2026-08-23 scar: `coworld build` pre-creates that directory, CI does not).

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/kaz_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter:
`coworld-ctf`.** Never a mixture. Splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently
(cogame-lantern, 2026-08-23). coworld-ctf's set is internally consistent and is kept as one piece:
the Worker sets `Module.onRuntimeInitialized`, the module is emitted **non-modularized** as
`kaz_replay.js`, `config.nims` exports
`_kaz_load_replay,_kaz_frame,_kaz_input,_kaz_packet_ptr,_kaz_packet_len,_kaz_mismatch_tick,
_kaz_error_ptr,_kaz_error_len,_kaz_stage_ptr,_kaz_stage_len` alongside `_main,_malloc,_free`, and
`static_replay_worker.js` does
`importScripts('./wire_constants.js','./broadcast_core.js','./kaz_replay.js')` in that order.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — which the Worker posts only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means
"a frame is on the canvas", not "a file was fetched". On failure the shell sets **`data-replay-error`**
on `<html>` with the message, in `showFailure()`. Both signals already exist in coworld-ctf's
`static_replay.js` and are inherited unchanged — this fork adds neither and removes neither. The
`coworld-replay` postMessage bridge's `ready` is posted from a callback fired **after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24) — otherwise the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from coworld-ctf.** Not edited, not
  reformatted; `tests/test_viewer.nim` pins its sha256. Everything knights-archers adds lives in the
  appended game block. Its `markBeat`/`renderBeatMarkers`/`ingestBeats` remain; `ingestBeats` ignores
  kinds it does not know and still drives `setVerdict` off the wave-over beat, which is exactly the
  behaviour this game wants.
- **`client/broadcast_core.js` is copied byte-for-byte** apart from the single `window.CTF_WIRE` →
  `window.KAZ_WIRE` identifier, which `tools/gen_wire_constants.nim` emits. The test asserts the diff
  is exactly that identifier.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`,
  transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched;
  the appended block replaces only the *contents* of the scorebug plates, adds the pressure bar and
  the closest-call marker, and retargets the feed rows, the beat rendering and the endcard's stat
  columns.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — the zoom bar (`#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`,
    `#zoom-read`) and the minimap (`#minimap`, `#minimap-canvas`). **Zoom decision: dropped.** The
    board is the fixed 1235 × 659 arena and `relayout()` always fits it whole inside the frame, so per
    the pin a fixed arena drops `#viewpanel` entirely; the page's `attachMinimap(...)` call goes with
    it (`broadcast_core.js` tolerates a missing minimap — `pendingMinimap` simply stays null — so the
    file stays byte-identical).
  - The heart/flag scorebug fields (`flag`, `carrier`, `prog`) and the `.ec-heart` endcard glyphs.
  - The `.beat-marker.steal`, `.beat-marker.return`, `.beat-marker.capture`, `.beat-marker.hillflip`
    and `.beat-marker.hillhold` CSS rules (their kinds are never emitted here).
  - The perk and handicap badges, and the paintbot hill ring / coverage arc.
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`, `#chrome`,
    `#scorebug` with `#plates-l`/`#plates-r`/`#clock`, `#bannerlane`, `#killfeed`, `#fpv` (the
    first-person picture-in-picture — the best view of a zombie arriving), `#povBadge`, `#mmwarn`,
    `#transport` **in full**, `#scrub` with `#momentum`/`#lulls`/`#scrub-win`/`#scrub-head`,
    `#endcard`.

### Transport rules

`relayout()` sets `--band` (the measured transport strip), `--topband` (the scorebug strip) and
`--hudscale` on `:root`, unchanged. **No overlay sits in the transport band**: the board is laid out
between the two bands, and every knights-archers addition (the pressure bar, the closest-call chalk
line, the feed, the banners) is positioned inside the board region or in the top band. The **endcard
stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept) so the
scrubber stays clickable underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `kazBeat(tick, kind, side, label)` — named so it can never shadow
chrome_common's `markBeat` alias, the tandem 2026-08-23 hoisting trap — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind knights-archers emits** and no others: `.beat-marker.wavestart`,
`.beat-marker.closecall`, `.beat-marker.casualty`, `.beat-marker.breach`, `.beat-marker.waveover`.
The game never calls chrome_common's `markBeat`, so no unlabelled div marker can appear.

### Readouts

1. **Horde pressure bar** (the idea's first ask) — a full-width strip immediately under the scorebug,
   inside the top band: a fill whose width is `pressure %` (the leader's progress from the breach at
   0 % to the gate at 100 %), a segmented tick per live zombie behind it, and a numeral
   `17 DEAD WALKING · LEADER 388px`. Chalk-grey to 70 %, amber 70–88 %, red past 88 %, with a 12-frame
   pulse whenever the leader sets a new minimum.
2. **Kill credits** (the idea's second ask) — four scorebug plates, two left and two right around the
   centre clock: the seat's **real policy name** (spectator side), a role glyph (mace / bow), its
   **kill count** in the big numeral, and swings (knight) or shots (archer) in the small one. The
   plate of a dead hero goes grey with a struck-through name and the tick it fell.
3. **'Closest call' marker** (the idea's third ask) — a vertical chalk line drawn on the board at the
   closest a zombie has come to the gate in the current wave, labelled `CLOSEST CALL — 136 px`, laid
   down live as the record is set; a `closecall` scrubber beat; and one endcard row per wave.
4. **Clock** — `M:SS` counting down inside the current wave, with the caption
   `wave 1/2 · 17 alive · turn 7/24`.
5. **Match feed** (`#killfeed`, renamed in copy only) — plain language, never internal notation:
   "KNIGHT-alpha cuts down Z-118", "ARCHER-beta puts two in Z-121",
   "**Z-140 IS CHARGING ARCHER-alpha**", "**THE LINE HOLDS — WAVE 1 CLEARED, 70 KILLS**",
   "**Z-140 IS THROUGH THE GATE**", and the commander lines
   ("Knight-alpha: archers hold the choke, I take the north lane"). The directive `note` and each
   hero's `say` appear here; this is where a spectator sees the LLM playing.
6. **Momentum graph** — the starter's `lead` series, retargeted to two series over the whole episode:
   **cumulative team kills** and the **leader's pressure %**, with the wave boundary marked. It is
   shipped once on the first frame, so the graph draws its full width immediately.
7. **Gate and breach** — baked floor art (§Sim module): a portcullis strip at `x < 40` and a torn
   dark strip at `x > 1178`, so the geometry of the game is legible with the HUD off.
8. **First-person PIP** (`#fpv`) — unchanged, and the single most watchable thing in the game: the
   view from a knight's helmet as the horde arrives.
9. **Transport and integrity** — play/pause, step, speeds `[1,2,3,4,8,16]`, scrubber with beat
   buttons, tick readout, skip-lulls, spoilers switch, end-hold countdown, and the `#mmwarn`
   hash-mismatch line — all verbatim.
10. **Endcard** — "WAVE 1 CLEARED · WAVE 2 LOST — ARCHER-alpha caught at 0:33", the four-seat table
    (kills, hits, shots/swings, and whether the hero survived), the team line
    "93 KILLS · 1 WAVE CLEARED · SCORE 0.611", and the per-wave closest calls. It stops at
    `var(--band)` and any seek dismisses it.

### Art

Real, and already in the repo. **Heroes**: knights are the shipped `data/soldier_red*` sprites on the
`data/rig_real/red` rigs; archers are `data/soldier_blue*` on `data/rig_real/blue`. **Zombies** are
the shipped **green** family (`data/soldier_green*`, `data/rig_real/green`) re-composited at startup
by `global.nim`'s own soldier compositor with a desaturated, mottled palette pass and a two-frame
shamble (the rig already carries a walk cycle), so a zombie reads as a corrupted cog and not as a
third team. **Held weapons** are baked at startup by the starter's own pixie compositor in
`rig_art.nim`, which already draws the held-item silhouette and its warm rim glow procedurally: the
mace is a 30 px haft with a 12 px spiked head; the bow is a 26 px arc with a string; the arrow in
flight is a 16 px shaft with a 4 px fletch, drawn at the arrow's hashed position and heading. Walls
are `client/art/walls/*.jpg`; the loading screen is the starter's locker room
(`client/art/lockerroom/bg.jpg` plus the red/blue/green cog webps). The gate portcullis and the breach
strip are baked into the floor art (§Sim module edit 3). No solid-colour placeholders, no TODO
assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`. Kept
verbatim. Knights-archers adds three rules of its own: `.plate-name` gets
`flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis` so a policy name never
collapses to "…"; under `.tiny` the shots/swings numeral is hidden and the four plates keep only
`glyph + name + kills`; and under `.tiny` the pressure bar drops its per-zombie segments, keeping the
fill, the percentage and the alive count so it reads as `▰▰▰▱▱ 66% · 17`. `tests/test_viewer.nim`
asserts all three rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-knights-archers`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `knights-archers`; `game.name` is
  **`knights-archers`** (hyphenated, matching the slug), so the secret namespace
  `secret://coworld/knights-archers/anthropic_api_key`, the page slug and the docs all agree.
- **`compose.yaml`** — one service, **underscored** so the derived manifest placeholder is
  `{{KNIGHTS_ARCHERS_IMAGE}}` (placeholders come from compose service names — the lantern 0.1.0 scar;
  `{{GAME_IMAGE}}` is not a thing; the underscored service name is the collab-cooking / fruit-market
  precedent):

  ```yaml
  services:
    knights_archers:
      image: coworld-knights-archers:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  (ctf ships two services / two images; knights-archers uses the one-image / two-entrypoints shape
  because the shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure
  (nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:knights-archers
  src/knights_archers.nim` → `/bin/knights-archers`, and the same for
  `src/knights_archers_player.nim` → `/bin/knights-archers-player`. The runtime stage copies both
  binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/knights-archers"]`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby
  0.1.27 with its sha256 check, the three marker splices, the whole `test -f` / `grep -q` assertion
  block) with the asset list swapped: red/blue/green soldier art and rigs, walls, locker room,
  `font.ttf`, `kaz_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`,
  `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`, `index.html`, `league.html`.
- **`coworld_manifest_template.json`** (validated offline with the CLI's `validate_upload_manifest`
  before the first dispatch — the hive 0.1.0 scar):
  - `$schema` set; top-level `tags`: `["horde","cooperative","knights-archers","melee","ranged","llm",
    "pettingzoo"]`; top-level **`episode_timeout_minutes: 20`**; top-level `player[]`; `game.owner`
    present; **no** top-level `replay_viewer` and **no** top-level `version`.
  - `game.name` `knights-archers`; `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.runnable` = `{"type":"game","image":"{{KNIGHTS_ARCHERS_IMAGE}}",
    "run":["/bin/knights-archers"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/knights-archers/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-knights-archers/tree/main"}` — the `env` entry is
    mandatory: without it the hosted game container never sees the coworld secret and every league
    episode silently plays scripted (hive, 2026-08-23).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`, **every array bounded**: `tokens` (`minItems` 4, `maxItems` 4), `players`
    (4, 4), `slots` (4, 4), `roles` (`minItems` 4, `maxItems` 4, items enum `["knight","archer"]`).
    Scalars, with defaults: `seed`, **`num_agents`** (integer 4..4, default 4), `minPlayers` (4),
    `maxTicks` (2304), `maxGames` (2), `turnTicks` (96), `turnBudgetMs` (7000), `attempt1Ms` (4500),
    `retryMs` (2000), `turnSpacingMs` (9000), `wallClockBudgetSeconds` (690),
    `lobbyJoinTimeoutTicks` (2400), `startWaitTicks` (120), `gameOverTicks` (72),
    `mapPath` (`"arena"`), `fogOfWar` (false), `fastMode` (true), `showPlayerLabels` (false),
    `zombieHp` (2), `zombieSpeed` (384), `zombieReach` (26), `zombieLungePx` (90),
    `zombieStuckTicks` (24), `zombieSpawnX` (1178), `gateX` (40), `spawnStartPerMille` (12),
    `spawnMaxPerMille` (50), `spawnSaturateTicks` (1920), `spawnCapAlive` (40),
    `knightReach` (52), `knightArcBrads` (32), `knightDamage` (2), `knightCooldown` (18),
    `swingTicks` (4), `archerSpeedPct` (85), `arrowSpeed` (3072), `arrowRange` (528),
    `arrowLifeTicks` (44), `arrowDamage` (1), `arrowCooldown` (12), `arrowHitRadius` (14),
    `archerRange` (460), `roleStandoff` (300), `screenStandoff` (120), `archerPanicPx` (150),
    `closeCallPx` (200), `clearBonus` (20), `roundTarget` (90), `creditEpsilon` (4, per-mille),
    `model`, `maxOutputTokens` (900).
  - `game.results_schema`: exactly the 22 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","role","reason","endRule"]`; the ten seat-indexed arrays
    `minItems: 4, maxItems: 4`; the four wave-indexed arrays `minItems: 1, maxItems: 4`;
    `reason` enum `["complete","deadline","fault"]`; `endRule` enum
    `["full_time","breach","casualty","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both** `player` and `global`, each
    `{"type":"text","value":"<docs/PROTOCOL.md inlined>"}` — object form, not a bare string (the
    garble v0.1.0 scar).
  - `game.docs`: **`readme`** = `{"type":"text","value":"<README body inlined>"}` and **`pages`** =
    three entries — `rules` ("Rules", `docs/RULES.md` inlined), `protocol` ("Wire protocol",
    `docs/PROTOCOL.md` inlined), `commanding` ("Writing a knights-archers prompt",
    `docs/COMMANDING.md` inlined) — each `{"id","title","content":{"type":"text","value":…}}`. **Text
    form, not URIs.** `tests/test_manifest.nim` asserts all four values are non-empty.
  - `player[0]` = `{"id":"baseline","type":"player","name":"Phalanx Baseline",
    "description":"Scripted hero: knights intercept the two leading zombies, archers focus-fire and
    back off when anything gets close.","image":"{{KNIGHTS_ARCHERS_IMAGE}}",
    "run":["/bin/knights-archers-player"],"env":{"PLAYER_SCRIPTED":"phalanx"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}` — the only declared
    player, and it is seated in **all four** certification slots (the raid 0.1.2 `players_missing`
    scar: every declared player entry must occupy a certification slot).
  - **Variants — `num_agents` is 4 in all four**, each with a `description`:

    | id | name | `num_agents` | `maxGames` | `maxTicks` | `spawnMaxPerMille` | `zombieHp` |
    |---|---|---|---|---|---|---|
    | `default` | Horde — two waves | **4** | 2 | 2304 | 50 | 2 |
    | `horde-short` | Horde — one wave | **4** | 1 | 2304 | 50 | 2 |
    | `horde-hard` | Horde — dense | **4** | 2 | 2304 | **72** | 2 |
    | `horde-tough` | Horde — armoured dead | **4** | 2 | 2304 | 50 | **3** |

    Every variant also carries `players` (4 named entries), `slots`
    (`[{"team":"red"},{"team":"red"},{"team":"red"},{"team":"red"}]`),
    `roles: ["knight","knight","archer","archer"]`, `tokens` (4), `minPlayers: 4`,
    `mapPath: "arena"`, `fogOfWar: false`, `turnTicks: 96`, `turnBudgetMs: 7000`,
    `attempt1Ms: 4500`, `retryMs: 2000`, `turnSpacingMs: 9000`, `wallClockBudgetSeconds: 690`,
    `lobbyJoinTimeoutTicks: 2400`, `fastMode: true`, `showPlayerLabels: false`, `seed: 679961`, and
    the full horde/hero constant block at its defaults. `default` is what the league ranks;
    `horde-hard` and `horde-tough` change **difficulty only**, never the seat count, and are scored on
    the same `roundTarget` scale so a harder variant is genuinely harder to score on.
  - **Certification fixture**: `certification.players` = four `{"player_id":"baseline"}` entries;
    `certification.game_config` = `{"players":[{"name":"Knight A"},{"name":"Knight B"},
    {"name":"Archer A"},{"name":"Archer B"}], "slots":[{"team":"red"},{"team":"red"},{"team":"red"},
    {"team":"red"}], "roles":["knight","knight","archer","archer"],
    "tokens":["t0","t1","t2","t3"], "num_agents": 4, "minPlayers": 4, "seed": 679961,
    "mapPath": "arena", "fogOfWar": false, "maxTicks": 600, "maxGames": 2, "turnTicks": 96,
    "turnBudgetMs": 7000, "turnSpacingMs": 0, "wallClockBudgetSeconds": 180,
    "lobbyJoinTimeoutTicks": 1440, "startWaitTicks": 0, "gameOverTicks": 24,
    "spawnStartPerMille": 40, "spawnSaturateTicks": 480, "fastMode": true,
    "showPlayerLabels": false}` — all four seats scripted, no LLM, no rate floor, 2 × 600 ticks. That
    is **1200 ticks = 50 s of playback** at 24 fps, deliberately longer than any viewer soak window
    (the ecos 2026-08-23 scar), while `fastMode` plays it in a handful of wall seconds. The raised
    `spawnStartPerMille` and shortened `spawnSaturateTicks` exist so the short fixture reliably
    produces spawns, hits, kills, a `closecall` and a `waveover` — a fixture that renders an empty
    board tests nothing. The `certify` step in `coworld-release.yml` passes
    **`--timeout-seconds 300`** (the default 60 s does not cover start + connect grace + waves +
    linger — cooperative-hunting 0.1.2).
- **Scaffold from `templates/`** with `<slug>` = `knights-archers`, `<IMAGE>` =
  `coworld-knights-archers`, `<SEATS>` = **4**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`, `tools/ci/docker_smoke.sh`
  (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (**copied verbatim**, no substitutions),
  `tools/ci/policies.json`, plus the starter's `tools/build_replay_viewer.sh` (**`chmod +x`**). Three
  additions to the template `ci.yml`:
  - the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format);
  - the `wasm-viewer` job gets a final step
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/replay.json 300` — the
    native↔wasm determinism gate, which fails if `kaz_mismatch_tick() != -1`;
  - repo variable `NIM_TESTS_RELEASE_ONLY` lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/knights-archers-player"`, one image,
  env-switched):

  | name | env | role |
  |---|---|---|
  | `knights-archers-warden` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `knights-archers-volley` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `knights-archers-phalanx` | `PLAYER_SCRIPTED` = `phalanx` | filler |
  | `knights-archers-stand` | `PLAYER_SCRIPTED` = `stand` | filler |

- **Repo layout**: `src/knights_archers.nim`, `src/knights_archers_player.nim`,
  `src/kaz/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, arena.nim, map_art.nim,
  horde.nim, arrows.nim, melee.nim, control.nim, directives.nim, baselines.nim, llm.nim, decide.nim,
  roster.nim, replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim,
  rig_art.nim, wire_constants.nim, server.nim}`, `replay-viewer/{kaz_replay.nim, config.nims,
  static_replay.js, static_replay_worker.js}`, `client/`, `data/`, `tests/`,
  `tools/{build_replay_viewer.sh, gen_wire_constants.nim, expand_replay.nim, extract_events.nim,
  replay_summary.py, record_fixture.sh, wasm_replay_smoke.cjs, ci/}`,
  `docs/{RULES.md, PROTOCOL.md, COMMANDING.md, plans/2026-08-26-knights-archers-design.md}`,
  `AGENTS.md`, `README.md`, `config.json`, `nimby.lock`, `knights_archers.nimble`, `compose.yaml`,
  `coworld_manifest_template.json`, `Dockerfile`, `Dockerfile.replay-viewer`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for an index or fixed-point overflow). CI is the only
harness; the sandbox has no Nim, Docker or emsdk.

1. **`tests/test_horde.nim`** — sim unit tests for the horde: `spawnRows` on the arena is non-empty
   and ≥ 120 entries, and every entry is clear floor at spin frame 0; `zombieField` is finite on every
   walkable cell and strictly decreases along any path to the gate; the spawn accumulator emits
   exactly the integral of `rate(t)` over 2304 ticks (± 1) and never emits while `aliveZombies == 40`;
   a zombie left alone crosses 1178 → 40 in **759 ± 2** ticks; a zombie walled into a pocket rotates
   after 24 stuck ticks and escapes within 120; a hero placed 89 px from a zombie is lunged at and one
   placed 91 px away is not; a hero at 25 px dies this tick and one at 27 px does not; two runs from
   the same seed produce byte-identical zombie streams and two runs from different seeds do not.
2. **`tests/test_combat.nim`** — the two weapons: a knight's swing kills a 2 hp zombie in exactly one
   blow, hits every zombie inside the 52 px ±45° wedge and none outside it, hits nothing behind a
   wall, and damages each victim **at most once per activation** even across its 4 lit ticks; the
   cooldown is exactly 18 ticks; an arrow travels 12 px/tick, dies at 44 ticks and at 528 px, is
   consumed by the first zombie it touches and by any wall, needs exactly two hits to kill, and
   **passes through heroes**; two arrows fired at the same zombie on the same tick kill it once and
   credit only the first; `MaxArrows` is never exceeded.
3. **`tests/test_scoring.nim`** — the formula and its sign: `teamScore` is 0 at 0 value, 1.0 at
   `2 × 90`, monotone non-decreasing in kills and in waves cleared, and never negative; all four
   seats' `teamScore` are **exactly equal** over 10 000 random `(kills[4], cleared)` draws;
   `max(credit) - min(credit) <= 0.004 < 1/180` — one extra team kill strictly dominates the whole
   epsilon range; `win[s]` is the same boolean for all four seats and equals `teamScore >= 0.5`; a
   `fault` episode scores what was banked with `win` false everywhere.
4. **`tests/test_endings.nim`** — end conditions: a zombie stepping to `x == 40` ends the wave
   `breach` on that tick and not the next; a hero touched ends it `casualty`; a tick in which both
   happen is `breach` (the order in §The game step 6.10); a wave that runs 2304 ticks with the line
   intact is `full_time` and increments `wavesCleared`; `waveLog` records exactly one entry per wave
   played; the 690 s stop yields `deadline`/`wall_clock` with the in-progress wave's kills banked and
   no clear bonus; a tripped invariant yields `fault`/`sim_fault` with a partial replay;
   `results.reason` and `results.endRule` are always members of the two declared enums.
5. **`tests/test_control.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines × all four seats, the emitted
   directive validates against the reply schema — exactly the seat's own id, an intent in the enum, a
   target inside the map and on walkable ground, `note` ≤ 160 runes, `say` ≤ 10 runes — and every
   compiled mask has only legal bits, never Up+Down or Left+Right together, never `C`. Plus: the same
   (state, order) pair always yields the same byte; `fall_back` never sets `A`; a knight never sets
   `A` with nothing in the wedge and an archer never sets `A` with nothing on the ray; the trigger is
   never set during a cooldown; a hero ordered to an unreachable target still moves every tick for
   120 ticks; and a `phalanx` × 4 episode at seed 679961 completes, out-kills a `stand` × 4 episode at
   the same seed on both waves, and kills **at least 20 zombies** (a pinned regression against a
   baseline that does nothing).
6. **`tests/test_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   `cogs` as an id-keyed object, a bare order object with no `cogs` wrapper, unknown and hyphenated
   intents, absent/NaN targets, off-map targets, a target inside a wall, three cogs, zero cogs, an id
   belonging to another seat, a 300-character `note`, and a `say` whose 10th and 11th characters are a
   4-byte emoji — the truncation must land on the **rune** boundary and the result must still
   round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the `phalanx`
   directive plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all four** seats' calls go
   out in **one parallel batch** (the fake records in-flight windows and the test asserts all four
   intersect); the per-turn budget is enforced with a hung client; `turnSpacingMs` holds the batch
   rate at ≤ 30 req/min for four seats; the budget guard switches to scripted and the episode still
   ends `complete`; a disconnected seat plays `phalanx` and revives on reconnect; a never-connecting
   seat is reported to `COGAME_PLAYER_FAILURE_URI` and both waves still play; a seat's directive is
   never empty on any tick after turn 0.
8. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full scripted 4-seat,
   2-wave episode writes `results.json` and a `COWLDKAZ` replay; `parseReplayBytes` accepts it;
   re-simulating from the config + mask log reproduces **every** recorded hash (including every
   zombie spawn, which is re-derived and not recorded); **strict-UTF-8 parse** —
   `tools/replay_summary.py`'s stdout parses under `json.loads(out.decode("utf-8"))` and the embedded
   config JSON decodes strictly, with the fixture forced to carry a non-ASCII policy label and a
   non-ASCII `note` so the UTF-8 path is real; every `directive` record is ≤ 900 runes;
   `results.reason` is in the legal enum; the stream contains at least one `spawn`, one `swing`, one
   `shot`, one `kill`, one `closecall`, one `directive` per seat per turn, two `wavestart` records
   and exactly one `result` record.
9. **`tests/test_identity_privacy.nim`** — the starter's test, **kept and extended**: no sprite label
   in a *seat* frame, no shout bubble, no LLM system-or-user message and no `directive` record ever
   contains a sentinel policy address — while the broadcast stream, `roster[].name`, the DOM scorebug
   and `results.names` **must** contain it. That is the two-name-space pin, asserted from both sides.
   Also: a seat's view JSON contains only `KNIGHT-*`/`ARCHER-*` aliases, and never another seat's
   *current-turn* note.
10. **`tests/test_observation.nim`** — the view contract: with `fogOfWar: false` every seat's frame
    contains every live zombie and every hero; the view JSON's `zombies` array is sorted by `gate_px`
    ascending and capped at 40; `squad[].last_note` is last turn's and never this turn's; `pressure`
    agrees with a full rescan of the sim; the seed, the RNG state and any future spawn appear nowhere
    in any seat-facing byte.
11. **`tests/test_manifest.nim`** — `num_agents == 4` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 4`; `results_schema` keys ==
    `heroResultsJson` keys; `game.protocols` has both `player` and `global` in object form;
    `game.docs.readme` and all three pages are non-empty **text**;
    `replay_viewer.bundle == "static-replay-viewer"`; every variant's
    `wallClockBudgetSeconds <= 0.6 * 1200`; every array property in `config_schema` declares
    `minItems`/`maxItems`; the compose service name derives `{{KNIGHTS_ARCHERS_IMAGE}}` and the image
    is `coworld-knights-archers`; `game.name` equals the secret namespace in
    `game.runnable.env.ANTHROPIC_API_KEY_URI`; `config_schema` covers every field
    `sim_config.update` reads; `episode_timeout_minutes == 20`.
12. **`tests/test_viewer.nim`** — the static half of the **viewer smoke** (no browser): assertions
    over `client/replay_broadcast.html` and `client/chrome_common.js` that the transport controls,
    `#scorebug`, `#bannerlane`, `#killfeed`, `#endcard`, `#mmwarn`, the `.tiny` block, the
    `--hudscale` clamp, `#endcard { bottom: var(--band`, the pressure-bar block, the closest-call
    marker and the three `.tiny`/`.plate-name` rules are present; that `#viewpanel`, `#minimap` and
    `#zoombar` are **absent**; that `chrome_common.js` is byte-identical to the starter's copy
    (sha256 pinned in the test); that `broadcast_core.js` differs from the starter's in **exactly**
    the `KAZ_WIRE` identifier; that the appended game block defines no identifier that collides with
    the chrome alias list (the tandem shadowing guard) and defines CSS for **every** beat kind the sim
    emits and no kind it does not; and that no `ctf_`/`CTF_` identifier survives in `client/`,
    `replay-viewer/` or `src/`.
13. **`tests/test_startup.nim`** — `/bin/knights-archers` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when unpinned
    and honoured when pinned; both entrypoints exist and are executable in the image (asserted by the
    docker smoke).
14. **`tests/test_perf.nim`** (release-only) — a full 2 × 2304-tick episode with mask compilation, 40
    marching zombies and live arrows completes in under 120 s.

Beyond the Nim suite, `ci.yml` runs:

- **`tools/ci/docker_smoke.sh`** — a raw-Docker episode from the certification fixture in the
  production image, seats cross-checked against **`SMOKE_SEATS=4`**, `SMOKE_REQUIRE_REPLAY_JSON=0`,
  asserting the game container exits 0 with `results.json` and a replay, **and** that every *player*
  container exited 0 (the raid 0.1.3 scar). Its replay is uploaded as the `smoke-replay` artifact.
- **the `wasm-viewer` job** — builds the bundle, asserts `index.html` and a non-empty `.wasm` exist,
  then **executes** it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
  dist/smoke/<replay> --timeout 90 --strict-text-bounds`, against the replay **`docker-smoke`
  produced** (it `needs: docker-smoke` and downloads the `smoke-replay` artifact). The bundle is
  **executed, not merely built**; the job fails unless `data-replay-loaded="true"` appears within the
  timeout, and `--strict-text-bounds` is kept because the arena is fixed and fits the frame, so
  `canvas_text.never_inside` must be 0. The job then runs
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` as the
  native↔wasm hash gate.

---

## Out of scope (v1)

- **Every ctf mechanic the horde loadout removes**: the hitscan gun and its jitter/exposure model,
  spray cans, floor paint, the paint grid and buff, King of the Hill, the resident/visitor regimes,
  hearts/flags and capture, grenades and the grenade barrage, med kits, shields, cardboard barriers,
  paint puddles, trenches, perks, handicaps, and four-team free-for-all. **Deleted, not disabled.**
- **`coworld-big-adventure`'s explore/collect adventure layer.** The idea frames KAZ as a horde mode
  bolted onto that coworld. This repo ships the horde mode as a standalone game on the paintbot
  starter and inherits **none** of big-adventure's engineering — no exploration, no collection, no
  quest state, no map streaming. Certifying big-adventure is not a dependency of this build.
- **The 05 Raid boss.** The idea calls it "a natural fit". A boss is a second entity class with its
  own state machine, its own art and its own end condition; v1 ships one zombie type, and the
  `zombies` array is already the right shape for a v0.2 boss row.
- **Zombie variety.** No fast zombies, no armoured zombies, no ranged zombies, no zombie that spawns
  more zombies. `horde-tough` reaches the same difficulty axis with one config number
  (`zombieHp: 3`), which is what a v1 needs.
- **Hero respawns, revives, healing, or a hit-point pool.** One-death-ends-it is the idea's core
  tension; anything that softens it is a different game.
- **Friendly fire.** Arrows pass through heroes. Adding it would make a co-op ladder a lottery on an
  archer's aim.
- **More than two waves per episode, or a persistent wave counter across episodes.** The wall-clock
  budget in §Decisions sizes the episode at two; a rising campaign across episodes needs state the
  platform does not carry.
- **Raw per-tick actuator control by an external policy.** The v1 control channel is the directive
  plus the server-side control layer. The recorded per-hero mask log is already the right shape for a
  v0.2 protocol addition.
- **Player debug-sprite overlays** (ctf's `0x86` channel), **inter-seat chat outside the 10-rune
  in-game shout**, **persistent memory across episodes**, and any tournament structure beyond the
  platform league.
- **Procedural terrain** — the generator, the curated pool, `mapkit`, the map editor and the
  pool-review page. Knights-archers pins the hand-tuned arena; a moving board would make the flow
  field, the gate line, the closest-call scale and the viewer's fixed-frame zoom decision all variable
  for no gain in v1.
- **Achievements.** The starter's win-gated achievement catalog and its `results.achievements` key are
  dropped; the results document carries kill, hit, shot and closest-call counters instead.
- **Audio, 3D, camera cuts, and any downloaded art asset.**
