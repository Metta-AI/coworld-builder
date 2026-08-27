# cogame-smac-starcraft-micro — design note (2026-08-27, paintbot lineage)

`Metta-AI/cogame-smac-starcraft-micro` is a five-seat **fully cooperative micro-combat** coworld: five
cogs — one cog per unit — fight three seeded set-piece skirmishes against a scripted enemy army, and
the only thing that scores is how much of that army dies and how much of yours survives. It is forked
from **`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount `/workspace/starters/coworld-ctf`.
**Every convention there holds here unless this note says otherwise** — the 24 Hz tick loop, the
Sprite v1 button-mask input, the continuous integer movement with per-pixel wall masks and slide
collision, the hitscan gun with its windup / jitter / exposure model, the arc-cone melee machinery,
the shout channel, the `COWLDxxx` replay codec with its per-tick `gameHash` chain, the seat/cog split
and the server-side directive decision layer (`src/ctf/{decide,directives,control,baselines,llm}.nim`),
the mummy server and its `COGAME_*` runtime contract, the broadcast chrome
(`client/replay_broadcast.html` + `client/chrome_common.js` + `client/broadcast_core.js`), the
emscripten static replay bundle (`replay-viewer/`, `Dockerfile.replay-viewer`,
`tools/build_replay_viewer.sh`) and the `GameVersion` changelog discipline are all inherited.

**The starter is chosen by game shape.** SMAC micro is a **real-time game loop with rules written for
this coworld** — the paintbot row of the starter table (`prompts/10-design.md`, row 2) — and the
starter already ships, tested, every layer this game needs except the enemy army and the scoring:
per-tick actuator masks recorded into a replay, a ranged hitscan weapon with range/cooldown/windup and
a line-of-sight exposure model, a forward attack cone with reach/half-angle/cooldown for melee, a
per-turn parallel LLM directive batch with a scripted fallback, a deterministic control layer that
compiles one directive into per-tick masks, and a wasm viewer that re-derives every frame from the
recorded masks and checks a hash every tick.

**Source idea, verbatim:**

> SMAC StarCraft Micro (mod of coworld-bw) — run the SMAC/SMACv2 micro scenarios inside the OpenBW Brood War engine we already wrap
>
> EXTENSION of Metta-AI/coworld-bw — a Nim wrapper around OpenBW (pixel-exact StarCraft: Brood War reimplementation) with a planned bitworld sprite-bot layer. SMAC's scenarios are tiny scripted-opponent micro fights (3 marines, 2s3z, corridor 6 zealots vs 24 zerglings, etc.) and translate directly to Brood War units; SMACv2's randomised unit types/positions are a map-generator tweak. One cog per unit (move / attack-target / stop), shared win reward + damage shaping; focus-fire, kiting and formation emerge.
>
> Alternative if coworld-bw stalls: JaxMARL's SMAX is a dependency-free clone.
>
> Seats: 3-10 units (one cog per unit) vs built-in AI
> Motive: fully cooperative vs scripted enemy
> Policy interface: per-tick discrete; an LLM 'commander' issuing scripted micro is the interesting variant
> Fills gap: ProxyWar is macro RTS; this is micro at tick rate with one cog per unit
> Integrity: cooperative cross-play scoring; scenarios seeded.
> Replay plan: OpenBW renders the real game.
>
> Source: github.com/oxwhirl/smac, smacv2; JaxMARL SMAX; github.com/Metta-AI/coworld-bw.

**The EXTENSION reading, and the coordinator's binding ruling.** The idea frames this as a mod of
`Metta-AI/coworld-bw`. `coworld-bw` is **not** a mounted starter and is not available to this build;
the idea itself sanctions the dependency-free route ("JaxMARL's SMAX is a dependency-free clone"), and
the coordinator ruled before this note was written that the coworld implements SMAC-style micro
**natively on the coworld-ctf engine**. So: no OpenBW, no Brood War binary, no BWAPI, no Blizzard data
files, no `coworld-bw` code and no dependency on either. SMAC/SMACv2 and SMAX are **rules and scenario
reference only** — the *shape* of the scenarios (a small fixed squad against a scripted enemy army of
fixed composition, ranged units that kite, melee units that body-block, focus fire as the decisive
skill, a shared win reward with damage shaping) is what is carried over. The unit classes are this
repo's own (`ranger`, `blade`, `swarm`), the numbers are tuned here, and **no bit-exact parity with
SMAC, SMACv2 or SMAX is claimed or tested**. The replay is rendered by our own static wasm viewer,
never by OpenBW.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How smac-starcraft-micro satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a real-time loop with new rules; the hitscan gun, the arc cone, the directive layer, the mask log and the wasm replay are forked, not rewritten. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-smac-starcraft-micro`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=focusfire` / `PLAYER_SCRIPTED=charge` (both fillers); one image `coworld-smac-starcraft-micro`, player entrypoint `/bin/smac-starcraft-micro-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` and `Dockerfile.replay-viewer` kept; the **same Nim sim module** compiles into `replay-viewer/smac_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` byte-for-byte, `client/broadcast_core.js` byte-for-byte but for one identifier, `client/replay_broadcast.html` = the starter's page **with one appended game block**; our squad is the shipped `data/soldier_red*` + `data/rig_real/red` family, the enemy army the shipped `blue` family, the corridor swarm the shipped `green` family recoloured and scaled by the starter's own pixie compositor. No placeholders, no downloads. (§Viewer §Art) |
| Two name spaces | Prompts, seat frames, in-game labels and shouts carry only `RANGER-alpha`…, `BLADE-alpha`… and enemy ids `E1`…`En`; real policy names appear only in the replay config JSON, `roster[].name`, the DOM scorebug/endcard and `results.names`. Test-enforced (`tests/test_identity_privacy.nim`). (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | expected 317 s / absolute worst 612 s against a 720 s budget; a 690 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 5** in variants `default`, `outnumbered`, `corridor`, `heavy` **and** in `certification.game_config`; `<SEATS>` = 5 in `tools/ci/docker_smoke.sh`. (§Packaging) |

There is **no `OPEN` section**. Every reading the idea leaves loose — how many seats inside its
"3-10", which scenarios ship, what "damage shaping" is worth on a [0,1] league scale, what the LLM
commander's grammar is — is a rail the designer decides, and each is decided below with its reason.

---

## The game

**Five cogs fight a scripted army three times, and the squad's score is one number.** Our five units
spawn in a column on the west side of a fixed arena; the enemy army spawns 475 px east of them. Both
sides walk, shoot and swing under the same physics. The enemy is a deterministic in-sim script that
picks the closest thing it can see and kills it. Nothing regenerates, nothing respawns: a unit that
dies is out for the rest of that battle, a battle that kills the whole enemy army with anybody left
alive is a **victory**, and the episode is three battles long. Everybody's score is the same score.

The three skills the idea names all fall out of these rules and none of them is coded:
**focus fire** (five units on one enemy kill it in ~3 s, five units on five enemies kill nothing),
**kiting** (a ranger out-ranges a blade 380 px to 56 px but is 10 px/s slower, so backing off while
the weapon cools is worth free damage until the arena wall arrives), and **formation** (a blade that
stands between the enemy and a ranger is the only thing that buys the ranger those seconds).

### Seats, units, roles, aliases

**`num_agents` = 5. One seat = one unit.** No seat commands more than one body and no body is
uncommanded — that is the idea's "one cog per unit", stated as an invariant. Five is inside the idea's
"3-10" and is chosen because it is exactly the SMAC **2s3z** shape (two ranged + three melee): the
smallest squad in which focus fire, kiting and body-blocking are *all* live decisions at once, and
small enough that five parallel LLM calls per turn fit the Bedrock rate floor (§Decisions).

Seat → role comes from the variant's `roles` array (length 5, always). The alias is
`<ROLE>-<identity>` where identity is the starter's `IdentityNames[...]` (`alpha, beta, gamma, delta,
epsilon`) ranked among same-role seats:

| Variant | `roles` | Aliases |
|---|---|---|
| `default`, `heavy` | `["ranger","ranger","blade","blade","blade"]` | `RANGER-alpha`, `RANGER-beta`, `BLADE-alpha`, `BLADE-beta`, `BLADE-gamma` |
| `outnumbered` | `["ranger","ranger","ranger","ranger","ranger"]` | `RANGER-alpha` … `RANGER-epsilon` |
| `corridor` | `["blade","blade","blade","blade","blade"]` | `BLADE-alpha` … `BLADE-epsilon` |

All five seats are on the starter's **Red** team. The enemy army is on **Blue** and holds no seats:
its units are sim cogs driven by the in-sim script (§The enemy army). An enemy unit's in-game name is
`E<id>` (`E1`, `E2`, …), ids assigned 1..n in spawn order at the start of each battle and stable for
that battle. Those ids are the whole point of the command grammar: `"target_id": 3` is how a commander
says *everybody shoot E3*.

### Map, tick, clock

`mapPath: "arena"` in **every** variant — the starter's hand-tuned symmetric arena, **1235 × 659** map
pixels, fixed geometry, pinned into the replay's config as `mapSpec`. No procedural terrain: a fixed
board makes the spawn columns, the corridor chokepoints, the range constants and the viewer's zoom
decision all constant, and the arena's obstacles are exactly the cover that makes line of sight matter.
`teamAnchor(Red)` (west) and `teamAnchor(Blue)` (east) exist and are used only as spawn references.

`TargetFps = ReplayFps = 24`, **kept verbatim** (every speed-coupled layer — `PlaybackSpeeds`, the lull
scan, `tickTime`, the transport bar — is keyed to it).

One **battle** is `maxTicks` = **1440** ticks = **60 s**. One **episode** is `maxGames` = **3**
battles. The map, the seed and the connected seats are identical across the three battles; the sim RNG
stream simply continues (no re-seed), so each battle's spawn jitter differs and all three are
re-derivable from the one recorded seed. `resetToLobby()` clears the bodies, the projectiles and the
counters between battles. Three battles rather than one because a single skirmish is decided by one
opening and one mistake, and one sample of that is noise; three is the cheapest average that still
fits the wall-clock budget with room to spare.

Decision turns: `turnTicks` = **120** ticks = **5.0 s** → **12 turns per battle, 36 per episode**.

### Spawns (seeded — the idea's integrity note)

At the start of each battle:

1. Our five units are placed in a column at `friendlySpawnX` = **380**, centred on
   `y = MapHeight div 2 = 329`, spaced `spawnSpacingPx` = **44** px apart in y, in seat order.
2. The enemy's units are placed the same way at `enemySpawnX` = **855**, in enemy-id order.
3. Every unit's position then gets an integer jitter `(dx, dy)`, each drawn independently from the sim
   RNG in `[-spawnJitterPx, +spawnJitterPx]` with `spawnJitterPx` = **24**, and is snapped to the
   nearest pixel at which the 13 px footprint is clear floor with the spinning diamonds at spin frame
   0 (the starter's placement search, `nearestOpenCell`-style, bounded to a 96 px ring; if nothing is
   clear the un-jittered point is used).

The two lines start **475 px** apart — just outside a ranger's 380 px range, so the first decision turn
genuinely chooses the opening (advance, hold the wall, or split). Spawns are seeded: the seed is in the
config, the config is in the replay, and a replay re-derives every spawn. SMACv2's randomised unit
*types* and free-form positions are out of scope for v1 (§Out of scope); the ±24 px jitter is the whole
of the randomisation.

### The units

Common to every unit: body 34 px drawn / 13 px footprint (`PlayerHalf` = 6), `lives` = 1, no respawn,
no healing, no regeneration, aim decoupled from movement at `AimTurnRate` = 5 brads/tick, the
starter's acceleration/friction/slide-collision model unchanged, `MotionScale` = 256.

| | **`ranger`** (ours + enemy) | **`blade`** (ours + enemy) | **`swarm`** (enemy only) |
|---|---|---|---|
| max HP | `rangerHp` = **60** | `bladeHp` = **120** | `swarmHp` = **30** |
| speed | 100 % of `MaxSpeed` 704 = **2.75 px/tick = 66 px/s** | `bladeSpeedPct` 115 → **809 units = 3.16 px/tick ≈ 76 px/s** | `swarmSpeedPct` 130 → **915 units = 3.57 px/tick ≈ 86 px/s** |
| weapon | hitscan shot (the starter's gun) | arc swing (the starter's cone) | arc swing |
| range / reach | `rangerRange` = **380 px** | `bladeReach` = **56 px**, half-angle `bladeArcBrads` = **32** (±45°) | `swarmReach` = **40 px**, same half-angle |
| damage | `rangerDamage` = **4** | `bladeDamage` = **10** | `swarmDamage` = **6** |
| cooldown | `rangerCooldown` = **18** ticks (0.75 s) | `bladeCooldown` = **30** ticks (1.25 s) | `swarmCooldown` = **24** ticks (1.0 s) |
| windup | `FireWindupTicks` = **5** ticks, aim locked at the trigger pull | swing lit `swingTicks` = **4** ticks at the aim it was thrown at | same |
| dps | 5.33 | 8.0 | 6.0 |
| line of sight | required (`paintPathClear`) | required | required |

The ranger's shot **is** the starter's hitscan gun — `FireWindupTicks`, the released-shot aim jitter
calibrated off `config.gunRange` and the `ExposureSampleStep` silhouette test are all kept exactly as
the starter has them, retuned only by `rangerRange`, `rangerCooldown` and `rangerDamage`. That model is
already recorded-and-re-derived in the starter's wasm viewer, so it costs nothing to keep and it is
what makes distance real: a fully visible body is hit ~80 % of the time at maximum range and ~99 % at
half range. The blade's swing **is** the starter's arc-cone machinery (`canFireArc` / `startArcFire` /
`resolveActiveArcCones` / `selectArcVictims`) with four constants retuned and the victim set changed to
"any living unit of the other side"; each victim is damaged **at most once per activation**, across
all four lit ticks.

**There is no friendly fire.** A shot passes through friendly bodies and a swing ignores them. SMAC has
none; adding it to a cooperative ladder would make an episode a lottery on one ranger's aim.

**Time-to-kill, which is the whole balance.** Five of ours focus-firing one enemy blade (120 hp) kill it
in ≈ 3.5 s; one enemy ranger (60 hp) in ≈ 1.7 s. Five of ours each shooting a different enemy kill
nothing in the same window. A lone ranger needs 22.5 s of uninterrupted fire to kill a blade, while the
blade needs 7.5 s of contact to kill the ranger — so a ranger that stands still loses and a ranger that
kites from 380 px gains ≈ 32 s of free fire *if it has 324 px of room behind it*, which the arena
mostly does not give it. Full-contact squad dps is 34.6 against 480 enemy hp in `default`, i.e. ~14 s of
perfect contact, which in practice lands battles at **25–45 s** inside the 60 s clock.

### The enemy army (the "built-in AI")

The enemy is **inside the sim**, hashed, integer-only and deterministic — not a player pod, not a
control-layer client, and never a recorded mask. That is a load-bearing choice: the wasm viewer
re-derives every enemy decision from the seed and the recorded friendly masks, so the enemy costs zero
replay bytes and a hash mismatch stays a real integrity signal. `src/smac/enemy_ai.nim` runs once per
tick, in enemy-id order:

1. **Target selection.** Each living enemy keeps `targetSeat` (a friendly cog index, or −1). It keeps
   its current target while that target is alive and within `leashPx` = **700 px**. Otherwise, and in
   any case every `retargetTicks` = **48** ticks, it picks the living friendly unit with the smallest
   integer squared distance that is within `aggroPx` = **600 px** **and** has a clear line
   (`paintPathClear`); ties break to the lowest cog index. A retarget only replaces a live current
   target if the new candidate is at least 1.5× closer (integer comparison `9 * dNew <= 4 * dCur`) —
   hysteresis, so an enemy does not oscillate between two units standing side by side.
2. **Movement.** With a target: step directly toward it at the unit's speed, through the starter's
   wall-slide collision. Without one: step toward `friendlySpawnAnchor` = `(friendlySpawnX, 329)`.
   There is **no flow field** — direct steering plus the wall follower below is enough on this arena
   and keeps the hashed path cheap and integer.
3. **Stuck escape.** An enemy whose position is unchanged for `enemyStuckTicks` = **24** consecutive
   ticks rotates its step vector a quarter turn clockwise for the next **12** ticks — the same wall
   follower `control.nim` uses on wedged cogs, and for the same reason (a consistent rotation escapes a
   convex obstacle instead of oscillating against it).
4. **Attack.** If the target is inside range/reach and the aim error is inside `FireAimBrads` = 24
   brads with a clear line, the enemy fires (ranger) or swings (blade/swarm) under the same weapon rules
   as ours, and its cooldown starts. Otherwise it turns toward the target at `AimTurnRate`.

The enemy composition is config, not code: `enemyRoles` is an array of role names, 1..24 entries, and
the four shipped scenarios are four values of that one field (§Packaging). **It is one difficulty
level** — SMAC's built-in-AI difficulty ladder is out of scope for v1.

### Turn and tick structure — the exact resolution order

Steps 1–5 are the server's frame; steps 6.x are `sim.step`, which is ctf's step body with the
smac insertions called out. Anything not named here is the starter's code, unchanged and in its
original position.

1. **Turn boundary.** If `sim.gameTicksElapsed() mod turnTicks == 0` and `phase == Playing`, the
   directives collected for turn `k = gameTicksElapsed() div turnTicks` (issued by the decision layer
   *before* this tick is stepped — §Decisions) become each seat's active directive, and one `directive`
   record per seat is written to the replay chat stream. `activeDirective[seat]` is **excluded from
   `gameHash`** (the starter's rule for `damagePops`/`skin`): nothing a commander says can move the
   hash chain, only the masks it produces.
2. **Control compile.** For each living friendly unit in seat order,
   `control.compileMask(sim, order, cogIndex)` emits one `uint8` Sprite v1 input mask.
3. **Record.** The five masks go to `sim.step(inputs, prevInputs)` and to
   `replayWriter.writeInputMaskChange` (ctf's function, unchanged), indexed by **cog**. **This is the
   determinism boundary.** The control layer and the LLM sit outside it; the viewer never runs either.
4. `inc sim.tickCount`; `updateAnimatedDiamonds()` — verbatim, so movement, shots and swings all resolve
   against the geometry this tick draws.
5. Roster-driven transitions (`players.len == 0` → abort/reset) — verbatim.
6. **Playing:**
   1. Per **friendly** unit, in seat order: decrement `fireCooldown`, `windupTicks` and `arcTicksLeft`;
      `applyInput` (movement and aim rotation at the role's max speed); `applyGrenadeInput` /
      `applyBarrierInput` / `applySprayInput` are **deleted**; a fresh **A** press with the weapon ready
      starts a windup (ranger) or queues a swing (blade).
   2. **NEW `stepEnemyAi()`** — the four steps above, in enemy-id order. Enemy movement, aim and trigger
      all resolve here, before any damage is applied this tick.
   3. **`resolveShots()`** — the starter's hitscan resolution, retargeted: every ranger (ours or the
      enemy's) whose windup completes this tick fires along its **locked** aim with the starter's
      jitter and exposure sampling; the first body of the *other* side whose silhouette crosses the
      bullet corridor inside `rangerRange` takes `rangerDamage`. All shots are resolved against **one
      snapshot** taken before any of them apply, so seat order confers no advantage.
   4. **`resolveSwings()`** — the starter's `resolveActiveArcCones`, retargeted: every lit swing damages
      every living unit of the other side inside the reach/half-angle wedge with a clear line, at most
      once per activation.
   5. **NEW `applyDamage()`** — damage is applied from the snapshot in one pass: hp floors at 0, a unit
      reaching 0 hp is marked dead this tick (`alive = false`, `deathTick = tickCount`), a `kill` sim
      event is emitted and the killer's `kills` counter increments. **Damage credited to the scoreboard
      is clipped to the victim's remaining hp** (overkill is never banked), which is what makes
      `dmgFrac == 1` mean exactly "the enemy army is dead".
   6. **NEW `updateArmies()`** — recompute `ourHp`, `theirHp`, `ourAlive`, `theirAlive`, and the
      `focusCount` per enemy (how many of ours have that enemy as their current attack target).
   7. **NEW `checkMicroInvariants()`** — the sim guard (§Sim module). A trip raises `SimGuardError`,
      which the server's tick loop turns into `fault` / `sim_fault`.
   8. **NEW `checkBattleEnd()`** — replaces `checkKothEnd()` / `checkWinCondition()` / `checkMaxTicks()`,
      evaluated **in this order**, so a tick that annihilates both sides is a `wipe`:
      1. If `ourAlive == 0`: `finishBattle(endRule = wipe)`.
      2. Else if `theirAlive == 0`: `inc battlesWon`; `finishBattle(endRule = victory)`.
      3. Else if `gameTicksElapsed() >= maxTicks`: `finishBattle(endRule = full_time)`.
   9. FX pruning and shout expiry — verbatim (`recentShots`, `hitFlashes`, `damagePops`, `splatters`
      cosmetic; `recentShouts` as in the starter).
7. `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` — the starter's per-tick hash chain,
   with the smac state appended after the existing mixes (§Sim module).
8. **Battle end.** When `phase` becomes `GameOver` the server increments `gamesPlayed` (its existing
   line). If `gamesPlayed < maxGames`, the battle's `(ticks, endRule, dmgFrac, lossFrac, kills)` are
   archived into `battleLog`, `resetToLobby()` clears the field, and the next battle spawns. If
   `gamesPlayed >= maxGames`, the episode ends and the artifacts are written.

### Scoring, sign, and what the league ranks by

**Fully cooperative: the score is the squad's, and every seat gets it.** Integer sim counters, one
floating-point division at the end.

```
per battle b (only battles that actually started):
  enemyStartHp_b = sum of maxHp over the enemy army at spawn      (integer, > 0)
  ourStartHp_b   = sum of maxHp over our five units at spawn      (integer, > 0)
  dmgDealt_b     = damage our units applied to enemy units, overkill clipped
  dmgTaken_b     = damage enemy units applied to our units, overkill clipped
  dmgFrac_b      = dmgDealt_b / enemyStartHp_b                    -> [0, 1]
  lossFrac_b     = dmgTaken_b / ourStartHp_b                      -> [0, 1]
  won_b          = 1 if endRule == victory (every enemy dead AND >= 1 of ours alive), else 0
  battle_b       = winWeight*won_b + dmgWeight*dmgFrac_b + survWeight*(1 - lossFrac_b)

  winWeight = 0.60, dmgWeight = 0.30, survWeight = 0.10   (they sum to 1.0)

teamScore = ( sum over battles played of battle_b ) / maxGames        -> [0, 1]
credit[s] = creditEpsilon * dmgDealt[s] / max(1, sum over seats of dmgDealt[s])
scores[s] = teamScore + credit[s]
win[s]    = (teamScore >= 0.5)        -- the same boolean for all five seats
```

**Sign: higher is better, and no term is ever negative.** `teamScore` lies in [0, 1] and is
**identical for all five seats** — that is the cooperative pin, stated as an equation. A perfect
episode (three victories with no damage taken) is exactly 1.000; three wipes with no damage dealt is
exactly 0.000; a victory always scores ≥ 0.90 for that battle (because `dmgFrac == 1` follows from it)
and a wipe always scores ≤ 0.30.

`creditEpsilon` = **0.0004** (config `creditEpsilonPerMyriad: 4`). It exists so a five-way cooperative
ladder is not a pure draw machine, and it is deliberately smaller than the smallest team term: one
ranger shot (4 hp) in the variant with the largest enemy pool (`heavy`, 660 hp) is worth
`4/660 × 0.30 / 3 = 0.000606` to **every** seat, while the entire epsilon range is **0.0004**. The
ordering is therefore lexicographic — squad damage first, personal credit only as a tie-break — so a
seat that breaks focus to farm credit loses more than it can gain. `tests/test_scoring.nim` asserts the
inequality.

**The league ranks by `results.scores[s]`** (the platform's Elo over per-episode scores; 1000 start,
K = 32).

**Calibration.** `default` (2 rangers + 3 blades against a mirror army, `enemyStartHp` 480,
`ourStartHp` 480): three victories at 45 % of our health lost = `3 × (0.60 + 0.30 + 0.055) / 3` =
**0.955**. Two victories and one full-time draw at 70 % damage dealt and 80 % taken =
`(0.955 + 0.955 + 0.23)/3` = **0.713**. Three wipes at 55 % damage dealt = `3 × 0.165 / 3` = **0.165**.
The 0.5 win threshold means "you won at least half the battles, or you traded evenly in all of them".

**How seats are filled (the idea's cross-play note).** Scoring is cross-play, not self-copies: the
certification fixture seats five scripted `focusfire` units, and the league division ships **two
scripted fillers** (`focusfire`, `charge`) alongside the two prompt champions (§Packaging), so a
round-robin at five seats normally seats a champion beside scripted partners and never seats five
copies of one policy. The game records what it was given: `results.role` names each seat's role and the
`register` replay record names each seat's policy kind.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly **three** values; `results.endRule` carries the detail of
the **last** battle played and is a closed enum of exactly **six**.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `victory` | the last battle ended with every enemy dead and at least one of ours alive. Banks `won_b = 1`. |
| `complete` | `wipe` | the last battle ended with all five of ours dead (this also covers mutual annihilation on one tick — step 6.8 evaluates `wipe` first). No win bonus; damage banked. |
| `complete` | `full_time` | the last battle ran its 1440 ticks with both sides still standing. No win bonus; damage and survival banked. |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **690**) elapsed before the third battle finished. Battles already finished keep their value; the battle in progress banks `dmgFrac`/`lossFrac` with `won = 0`; battles never started score 0. The replay is complete up to the stop tick and the game-over frame is written. **Declared acceptable for phase-60 verification** (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. |
| `fault` | `sim_fault` | `checkMicroInvariants()` tripped. The episode is scored from what was actually banked, `win` is false for every seat, a partial replay is written. |
| `fault` | `host_error` | an unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

A `fault` scores what the squad actually earned rather than a neutral 0.5: in a cooperative game there
is no opponent to be unfair to, and zeroing two real victories would be the bigger distortion.

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2400 ticks = 100 s of
lobby wall clock) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via ctf's
`declarePlayerFailure` (lowest missing slot only), its unit is driven by the `focusfire` baseline for
the whole episode, and all three battles play out.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {focusfire, charge}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=focusfire`. A scripted policy seated as a champion is a failure state.

The idea's "an LLM 'commander' issuing scripted micro is the interesting variant" is **the** shape of
this coworld, not a variant of it: an LLM seat issues one order per turn in a fixed grammar, and a
deterministic controller executes that order at tick rate for the next five seconds. Nothing external
touches an actuator.

### Where the decision happens

In the **game server**, not the player container — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the *game* pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/smac-starcraft-micro/anthropic_api_key` —
the hive 2026-08-23 scar), phase 60 greps the *game* log for `falling back` / `LLM provider is
unavailable`, `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only, and keeping
the control layer server-side is what makes the recorded mask log reproducible with no network in the
loop.

`src/smac/llm.nim` is the starter's `src/ctf/llm.nim`, forked with no behaviour change:

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

One decision turn every **120 ticks (5.0 s of sim time)**, **12 turns per battle, 36 per episode**. At
each turn the server builds **all five** seats' request bodies and issues them as **one parallel
batch** — `client.curl.makeRequests(batch, timeout)`, the shape of the starter's `decideAll`. Seats are
**never** queried sequentially: this is a simultaneous-decision game and serial calls would quintuple
the wall clock for nothing. One call per seat per turn. An episode is at most 5 × 36 = **180 calls**,
at most 5 in flight.

Per-turn timing: attempt 1 batch deadline **`attempt1Ms` = 6000 ms**. Any seat that timed out, errored,
returned non-JSON or returned no usable cog entry is retried **once**, again as a single batch, with a
**`retryMs` = 3000 ms** deadline. Worst case 9.0 s ≤ the **`turnBudgetMs` = 10000 ms** cap enforced by a
monotonic deadline around the whole turn. Both deadlines are **whole seconds** on purpose: curly hands
them to `CURLOPT_TIMEOUT`, whose granularity is whole seconds and which therefore floors — 6000 → 6 s,
3000 → 3 s (the paintball 0.1.2 scar, where `4500` really ran as 4 s).

**Rate floor.** The Bedrock sidecar caps **30 requests/minute per episode** (raid, 2026-08-23), and five
seats per turn would blow straight through it at any fast cadence. A **`turnSpacingMs` = 12000**
wall-clock floor between the *starts* of consecutive batches holds the episode at
`5 × 60 / 12 =` **25 req/min**. It is a floor, not a sleep on the critical path: the loop keeps stepping
sim ticks while it waits, and because `turnSpacingMs` (12.0 s) exceeds `turnBudgetMs` (10.0 s), the
spacing — not the model — is what sets the episode's length.

```
36 turns x 12.0 s spacing floor (absolute worst: all 3 battles run full length) = 432 s
   typical: battles end in 25-45 s, ~22 turns                                   = 264 s
lobby / connect wait (typical 15 s; cap 2400 ticks = 100 s)                     =  15 s   (cap: 100 s)
3 x 1440 ticks of play, fastMode, seats report ready                            =  18 s   (wall-paced worst: 60 s)
game-over holds + results + replay write (retrying uploader)                    =  20 s
                                                                                -------
expected total                                                                  = 317 s   < 720 s
absolute worst case (432 + 100 + 60 + 20)                                       = 612 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                                         = 690 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                                           = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 690 and `tests/test_manifest.nim` asserts it.

`fastMode: true` in every variant. ctf's `docs/PROTOCOL.md` warns that the Sprite v1 Ready packet
(`0x85`) corrupts input timing on a wall-clock-paced server — that warning is about *player* clients
whose own inputs are dead-reckoned. These seats send no inputs at all (the server computes every mask),
so the hazard does not exist here and the player harness sends `0x85` after every received frame.

**Budget guard (early settle without shortening the episode).** At the start of each turn, if
`elapsed + 2 * turnBudget > wallClockBudgetSeconds`, the LLM is switched off for every remaining turn
and the episode finishes on the scripted layer (microseconds per turn), so it ends
`complete/<endRule>` rather than `deadline`. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the outer per-turn deadline,
`lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread (which runs
independently of the game loop, so a 10 s LLM stall cannot drop a connection), the 690 s engine stop,
and ctf's `gameOverTicks` hold before exit. On a seat's **timeout or parse failure**: retry once in the
next batch; on the second failure that seat's directive for that turn becomes the **`focusfire`**
scripted directive and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard}`. A provider
throttle with no other candidate model **skips the retry outright** (it cannot land) and fails fast to
the scripted layer for that turn — the starter's behaviour, kept. A seat that disconnects mid-episode
keeps playing: its directive source degrades to `focusfire` and it revives on reconnect. **No failure
mode leaves a unit unactuated** — the control layer always has a directive: this turn's, else last
turn's, else `focusfire`'s.

### The per-seat view given to the LLM

Built server-side, numbers in **map pixels**, rounded to integers. This object is the tail of the user
message and is mirrored (minus `enemies`) into the `directive` record.

```json
{"battle": 2, "of": 3, "scenario": "default",
 "turn": 5, "turns": 12, "clock": {"played_s": 25, "left_s": 35},
 "you": {"id": "RANGER-alpha", "role": "ranger", "alive": true,
         "pos": [412, 330], "aim": 128, "hp": 44, "hp_max": 60,
         "range_px": 380, "cooldown_ticks": 7, "ready": false,
         "damage_dealt": 96, "kills": 1, "speed_px_s": 66},
 "armies": {"ours": {"alive": 4, "hp": 301, "hp_max": 480, "hp_pct": 63},
            "theirs": {"alive": 3, "hp": 214, "hp_max": 480, "hp_pct": 45}},
 "enemies": [{"id": 3, "name": "E3", "role": "blade", "pos": [640, 302],
              "hp": 34, "hp_max": 120, "dist_px": 229, "in_your_range": true,
              "attacking": "RANGER-alpha", "focused_by": 2,
              "reach_px": 56, "speed_px_s": 76},
             "… every living enemy, nearest to you first, at most 24 …"],
 "squad": [{"id": "BLADE-alpha", "role": "blade", "pos": [600, 420],
            "alive": true, "hp": 88, "hp_max": 120, "damage_dealt": 140,
            "attacking": "E3", "last_intent": "focus",
            "last_note": "I body-block for the rangers", "last_say": "screen"},
           "… the other four seats …"],
 "last_turn": {"your_damage": 24, "your_shots": 6, "team_damage": 88,
               "enemy_kills": 1, "our_losses": 0},
 "your_last_directive": "… your seat's own note last turn, or null on turn 0 …",
 "score": {"team_so_far": 0.31, "battles_won": 0, "battle_damage_pct": 55,
           "battle_loss_pct": 37, "win_weight": 0.6, "dmg_weight": 0.3,
           "surv_weight": 0.1}}
```

### Per-seat observation: exactly what is visible and what is hidden

**The board is fully observable.** `fogOfWar: false` in every shipped variant: every seat sees the whole
arena, every living unit on both sides and every unit's hit points. Three reasons, decided here and not
revisited: SMAC scenarios are small set-piece fights whose difficulty is *micro*, not scouting; this is
a *cooperative* game, where hiding the board from partners adds a coordination puzzle the idea never
asks for and subtracts the one it does ask for (focus fire under time pressure); and the idea's own
replay plan is a public army-strength readout, which only makes sense if army strength is public. The
starter's fog machinery is not deleted — the first-person PIP still raycasts — only the per-seat
visibility mask changes.

**Visible**, on the seat's Sprite v1 stream (one binary message per tick) and, in the same shape, in the
view JSON above:

- The static map, its walkability sprite and the live rotating diamonds.
- **Every living unit on both sides**: position, aim, role, current and maximum hit points, alive flag,
  and weapon-ready flag.
- **Every enemy's current target** (`attacking`: the alias of the friendly unit it is closing on, or
  `null`) and **`focused_by`**, how many of ours are currently attacking it. Both are things a
  spectator of the board can see, and `focused_by` is what makes focus fire coordinable.
- **The armies block**: alive counts and hit-point totals for both sides, absolute and as a percentage
  of the battle's starting pool.
- **The other four seats' LAST-turn `note`, `say` and intent** — the squad channel.
- Shouts within `ShoutRange` (247 px), labelled with the shouter's anonymous alias.
- The battle index, the scenario id, the turn index, the clock, the running team score and the scoring
  weights.

**Hidden:** the other seats' directives **for the turn being decided** (all five decide simultaneously,
which is exactly why `say` and `note` matter); every seat's `PLAYER_PROMPT`; the identity of any policy
(real names never reach a seat); the episode seed; the RNG state and therefore every future spawn jitter
and every future shot's aim jitter; the enemy AI's internal `retargetTicks` counter, leash state and
stuck counters; and future ticks in general.

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape, so the two policy
kinds are strictly comparable and the same validator runs on both. The `cogs` array is kept (rather than
flattened to one order) because it is the starter's schema, its parser and its tests are already written
against it.

```json
{"note": "everyone on E3, blades screen the rangers",
 "cogs": [{"id": "RANGER-alpha", "intent": "focus", "target_id": 3,
           "target": [640, 302], "face": [700, 300], "say": "E3"}]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes on a rune boundary; newlines collapse to spaces |
| `cogs` | array | **exactly 1** entry — the seat's own unit | extra entries dropped; an empty or missing array keeps last turn's directive, else `focusfire`'s |
| `cogs[].id` | string | the seat's own alias, case-insensitive, suffix-tolerant, **≤ 16 runes** | an unmatched entry is assigned to the seat's unit by position |
| `cogs[].intent` | enum | `focus` `attack_move` `kite` `hold` `screen` `retreat` `regroup` | → `focus` |
| `cogs[].target_id` | int \| null | the numeric id of a **living** enemy | a dead or unknown id → the living enemy nearest `target`; `null` → the same |
| `cogs[].target` | [int, int] | finite; clamped to the map box `[0, w-1] × [0, h-1]` and snapped to the nearest walkable pixel | missing / non-finite → the position of the enemy named by `target_id`, else the enemy army's centroid |
| `cogs[].face` | [int, int] \| null | finite; same clamp | → `null` (the control layer picks the aim) |
| `cogs[].say` | string | **≤ 10 runes** — it becomes a real in-game **shout** (`ShoutMaxChars` = 10), audible to every friendly unit within `ShoutRange` = 247 px, one per unit per second | truncated to 10 runes, then the starter's `sanitizeSay` (printable ASCII minus `{`/`}`, trimmed) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized `directive` record **≤ 900
runes** (`MaxDirectiveRunes`, asserted in `tests/test_replay.nim`). `register.prompt` is capped at
**≤ 4000 runes** at the transport (over-long is truncated, never rejected) and is **never** written to
the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes** — the starter's `truncateRunes`
(`runeLen`/`runeSubStr`). Slicing a `string` by byte index on any path to the replay is forbidden. A
byte-truncated multi-byte character is exactly the bug that makes replay bytes render in a browser but
fail a strict parser, and §Tests pins it with a 4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model prefixed
prose; accept `cogs` as an object keyed by id; accept a bare order object without the `cogs` wrapper;
accept numeric strings for `target_id`/`target`/`face`; accept `"E3"` or `"e3"` where an integer
`target_id` was asked for; accept an unknown-case or hyphenated intent by normalising. Only when no
object with at least one usable cog entry can be recovered do the retry and then the fallback fire.

### System prompt (fixed; identical for both champions, one `<ROLE>` line per seat)

Sent as the system message.

```
You command ONE unit in a five-unit squad fighting a scripted enemy army in a
top-down arena 1235 by 659 pixels. You are <ROLE>. Your whole squad shares ONE
score: how much of the enemy army you destroy, whether you wipe it out, and how
much of your own health survives. Personal kills are worth almost nothing.
RANGER: you shoot. Range 380 pixels, 4 damage, one shot every 0.75 seconds, 60
health, 66 pixels per second. You die to two seconds of melee contact.
BLADE: you swing. Reach 56 pixels in a 90-degree wedge, 10 damage, one swing
every 1.25 seconds, 120 health, 76 pixels per second - faster than a ranger.
The enemy has the same weapons. Enemy units pick the closest of you they can
see and walk at it until it dies.
FOCUS FIRE IS THE WHOLE GAME. Five units shooting five different enemies kill
nothing; five units on ONE enemy kill it in about three seconds, and a dead
enemy stops shooting back forever. Every enemy carries a numeric id: name it in
"target_id" and say it out loud so the others pick the same one.
KITING: a ranger out-ranges a blade six to one but is slower. Backing away
while your weapon is on cooldown wins free damage - until you run out of arena.
SCREENING: a blade standing between the enemy and a ranger buys that ranger the
seconds it needs. A dead ranger deals no damage for the rest of the battle.
Every 5 seconds you issue ONE order for yourself. A deterministic controller
executes it for the next 5 seconds: it walks you where you asked around walls,
turns you to face what you asked, and pulls the trigger when the shot will
land. You never control motors or the trigger directly.
You can see the whole board: every unit, its health, what each enemy is walking
at, and how many of you are already shooting it. You cannot see what your
squadmates are deciding THIS turn - all five of you decide at the same moment -
so use "say" to call your target.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars","cogs":[{"id":"<your own id>",
  "intent":"focus|attack_move|kite|hold|screen|retreat|regroup",
  "target_id":<enemy id> or null,
  "target":[x,y],
  "face":[x,y] or null,
  "say":"<=10 chars"}]}
Intents: focus = attack the enemy named by target_id (a ranger holds 300 pixels
off it, a blade closes to touching range); attack_move = advance to `target`
and attack whatever comes into range on the way; kite = attack the nearest
enemy while backing off to 340 pixels, standing still only to fire (rangers
only; a blade reads it as focus); hold = stand at `target` and fire at anything
in range; screen = put yourself 90 pixels in front of the most wounded friendly
ranger, between it and the nearest enemy; retreat = walk to `target` and do not
fire; regroup = move to the middle of your surviving squadmates.
`face` biases your aim. `say` is SHOUTED and every nearby squadmate hears it.
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading (the
starter's `operatorBlock`), then a blank line, then the seat's view JSON. The prompt text is never
echoed into the replay — only `policyKind` and the resulting directive are.

### Champion #1 — `smac-starcraft-micro-marshal` (owner daveey), `PLAYER_PROMPT`

```
One target at a time, and never lose a ranger.
Every turn, compute the kill order yourself: of the enemies in range of anybody
in the squad, take the one with the LOWEST hp; break ties by the one closest to
our rangers. That is the target for EVERY unit this turn. Put its id in
target_id and put its id in "say", every single turn, even when it has not
changed - that is how five separate decisions become one volley.
If you are a RANGER: intent "focus" on the kill order. If any enemy blade or
swarm is within 200 pixels of you, switch to "kite" this turn instead and put
that enemy in target_id: you are worth more alive at 300 pixels than dead at
50. Never use "attack_move"; walking into an army is how a ranger dies.
If you are a BLADE: intent "screen" while any friendly ranger is alive and any
melee enemy is within 300 pixels of it - target the enemy, not the ranger; the
controller works out where to stand. Otherwise "focus" the kill order. You have
twice a ranger's health: spend it.
When the armies block says theirs.alive is 1, everyone "focus" it and finish
the battle - a victory is worth twice all the damage shaping combined.
When ours.alive is 1 and theirs.alive is 2 or more, that last unit uses
"kite" every turn and never stops moving: full-time with damage banked scores,
a wipe does not.
```

### Champion #2 — `smac-starcraft-micro-skirmish` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Fight at the wall, not in the open, and make them come to you.
Turn 0 and turn 1, before contact: every unit "hold" at a post on OUR side of
the map - blades at [430, 250], [430, 330] and [430, 410], rangers at
[330, 290] and [330, 370]. A tight line means every enemy that arrives is
inside every one of our weapons at once, and their AI walks into it.
From contact on, the target is the enemy with the SMALLEST dist_px in the
enemies list - the one that has already committed to us - and everyone names it
in target_id and in "say".
If you are a BLADE: "focus" that target. Do not chase anything further than 350
pixels away; if the nearest enemy is further than that, "hold" your post
instead and let it come.
If you are a RANGER: "focus" the same target, but if your own hp is below half,
"retreat" toward [200, your own y] for one turn and then rejoin. A ranger at
20 health is one swing from being worth nothing.
Nobody uses "regroup" while any enemy is within 250 pixels of anybody.
When the armies block says our hp_pct is more than 25 points above theirs, the
line is winning: switch every unit to "attack_move" on the enemy centroid and
close it out before the clock runs down - a full-time draw throws away the win
weight you have already earned.
```

### The control layer (deterministic, shared by every policy)

`src/smac/control.nim`, forked from `src/ctf/control.nim`. Both LLM directives and scripted directives
are compiled by the *same* code, so the two policy kinds are strictly comparable. It is a pure function
of `(sim state, order, cogIndex) -> uint8`, and it navigates with the starter's own proven components:
`buildNavGrid` (a 12 px cell grid over the wall mask), `computeField(goal)` (a BFS flow field to a goal
cell, cached, recomputed at most once per `FieldRefreshTicks` = 12 per distinct goal), `navSteer` (the
steering vector with line-of-sight shortcutting and no corner cutting), `nearestOpenCell`, the
`StuckTicks` = 8 quarter-turn escape, and `bradsOfVector`/`bradsErr` for the aim. It sits **outside** the
determinism boundary, so it may keep the starter's floating-point navigation maths.

Constants: `rangerStandoff` = **300 px**, `kiteStandoff` = **340 px**, `screenStandoff` = **90 px**,
`aimRange` = **420 px** (ranger) / **120 px** (blade), `chaseCapPx` = **520 px**.

**Resolving the order's enemy `E*`**: `target_id` if it names a living enemy, else the living enemy
nearest the order's `target`, else the living enemy nearest the unit, else none.

For each living friendly unit, each tick:

1. **Goal point `g`** by intent (`C` = the integer mean of our living units' centres, `t` = the order's
   clamped target):
   - `focus`: **blade** → `E*`'s position. **ranger** → the first clear point found by probing 16 evenly
     spaced points on the circle of radius `rangerStandoff` around `E*`, starting from the direction
     `E* → C` and alternating outward, requiring walkable ground and a clear line to `E*`; if none is
     clear, `g = E*`. If no enemy is alive, `g = t`.
   - `attack_move`: `g = t`.
   - `kite`: a **blade** compiles this exactly as `focus` on `E*`. A **ranger**: let `N` be the nearest
     living enemy. If `fireCooldown == 0` **and** `N` is inside `rangerRange` with a clear line, the
     d-pad is **cleared** — the unit stands and shoots. Otherwise `g` = the point `kiteStandoff` px from
     `N` along the direction `N →` the unit, clamped to the map box and snapped to walkable ground. That
     alternation is shoot-and-scoot, and it is the only place in the design where a goal depends on the
     weapon's cooldown.
   - `hold`: `g = t`.
   - `screen`: let `R` = the living friendly **ranger** with the lowest `hp` (ties to the lowest seat
     index) and `N` = the living enemy nearest `R`. `g` = the point `screenStandoff` px from `R` along
     `R → N`, snapped to walkable ground. With no living ranger, or no living enemy, this compiles as
     `attack_move` on `E*` (or `t` if there is no enemy).
   - `retreat`: `t`, clamped into `captureZone(Red)` — our home column on the west edge.
   - `regroup`: the integer mean of the **other** living friendly units' centres; `t` if none is alive.
   - **Chase cap**: for `focus`, `attack_move` and `screen`, if `g` is further than `chaseCapPx` from the
     unit's current position, `g` is pulled back to the point `chaseCapPx` along the way. A unit never
     abandons the squad for half a map on one order.
2. **D-pad** = the octant bits of `navSteer(unitPos, g)`; a unit within `ArriveRadius` = 20 px of `g`
   stops moving; the `StuckTicks` quarter-turn deflection applies. Diagonals only when the minor axis is
   ≥ 40 % of the major, so a straight run does not chatter between octants.
3. **Aim**, in priority order: `E*` when it is alive and within `aimRange` with a clear line — for a
   **ranger** aimed at `E*`'s **predicted** position `pos + vel * ticksOfFlight` where the shot is
   instantaneous but the windup is 5 ticks, i.e. lead by `vel * FireWindupTicks`, in integers; else the
   nearest living enemy within `aimRange`; else `face` when the order gave one; else the direction of
   `g`; else due **east** (where the enemy comes from). `B` / `Select` are set to turn toward it and
   neither is set when `abs(err) <= AimDeadBrads` = 4.
4. **Trigger `A`.** Never set for `retreat`. Never set while `fireCooldown > 0`, `windupTicks > 0` or
   (blade) `arcTicksLeft > 0`. Never set when `abs(err) > FireAimBrads` = 24.
   - **Ranger**: set iff some living enemy's predicted centre lies within `BulletHalfWidth + PlayerHalf`
     of the aim ray inside `rangerRange`, with a clear line. A ranger therefore only spends a shot it
     expects to land.
   - **Blade**: set iff a living enemy's centre is inside the `bladeReach`, ±45° wedge around the current
     aim with a clear line.
5. **Never both.** Up+Down and Left+Right are never set together (each pair comes from one sign), and
   `C` is never set — this loadout places nothing `C` could throw.

### Scripted baselines

Both emit the *same* directive object an LLM does, on the same 5.0 s cadence, so their output is legal by
construction and directly comparable. Both are pure functions of the world state, which is what makes
the bounded-orders test in §Tests meaningful. Both are documented in `docs/RULES.md`, so "cooperating
with a partner you did not write" here means "a partner whose published rules you know".

- **`focusfire`** — the certification player, the per-turn fallback, the driver of a no-show seat, and
  the default. Every governed unit derives the **same** kill order from state alone, so five independent
  seats running it converge on one target without communicating:
  1. Rank the living enemies by, in order: (a) inside 420 px of any living friendly unit before
     everything else; (b) current `hp` ascending; (c) integer squared distance to our squad centroid
     ascending; (d) enemy id ascending. `e[0]` is the kill order.
  2. A living **ranger** issues `focus` on `e[0]` — unless a living melee enemy (blade or swarm) is
     within `panicPx` = **150 px** of it, in which case it issues `kite` with that enemy as `target_id`.
     `say` = the target's name (`"E3"`) or `"kite"`.
  3. A living **blade** issues `screen` (target `e[0]`) when at least one friendly ranger is alive **and**
     some melee enemy is within **260 px** of that ranger; otherwise `focus` on `e[0]`. `say` = `"screen"`
     or the target's name.
  4. With no living enemy: everyone `regroup`. Fixed note: `"focus fire"`.
- **`charge`** — the second filler, deliberately weaker and different in **shape** so the ladder gets a
  spread rather than two versions of one bot: every unit issues `attack_move` at the living enemy nearest
  **itself**, every turn. Nobody kites, nobody screens, nobody shares a target — the squad splits its
  damage across the whole enemy army and loses the trade. Fixed note `"charge"`, fixed say `"go"`. A
  `focusfire × 5` episode scores strictly higher than a `charge × 5` episode at the pinned seed, which
  `tests/test_control.nim` asserts.

---

## Sim module

### What is kept, what changes, by path

The fork is a rename sweep (`ctf` → `smac`, `CTF_WIRE` → `SMAC_WIRE`, `COWLDCTF` → `COWLDSMC`; a CI grep
asserts no `ctf_`/`CTF_` identifier survives outside comments and history notes) plus the named edits
below.

**Kept**:

| Path (starter → fork) | Why it is kept |
|---|---|
| `src/ctf/arena.nim`, `map_art.nim` → `src/smac/` | the arena geometry, the wall/walk masks, `teamAnchor`, `captureZone`, `isProtectedFloor`, the map bake and the `mapSpec` round-trip. The hand-tuned `arena` layout **is** the board; the generator, pool, `mapgen_styles.nim`, `map_pool.nim`, `tools/mapkit.nim`, `tools/map_editor*`, `tools/gen_map_pool.nim` and `docs/pool-review.html` are **deleted** (this game pins `mapPath: "arena"`). |
| `src/ctf/replays.nim`, `replay_runtime.nim` | the whole replay codec, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket`. |
| `src/ctf/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, the replay-switch path, the `COGAME_*` contract, `declarePlayerFailure`, the artifact-write block, the `gamesPlayed` loop, the `wallClockBudgetSeconds` stop. Four named edits below. |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` | the whole per-turn decision layer: the parallel batch, the two deadlines, `turnSpacingMs`, the budget guard, tolerant parsing, rune caps, the fallback ladder, the nav grid and steering. Retargeted, not rewritten. |
| `src/ctf/sim.nim` (combat core) | `applyInput`, the movement/slide/collision model, the hitscan shot path with windup, aim jitter and `ExposureSampleStep` exposure sampling, `paintPathClear` line of sight, `canFireArc`/`startArcFire`/`resolveActiveArcCones`/`selectArcVictims`, `bradsOfVector`, `distSq`, the shout channel, `cogAlias`. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown, `resetToLobby`. |
| `src/ctf/roster.nim` | join/auth/identities/`IdentityNames`/the seat-indexed results document. Two named edits below. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/broadcast.nim` | `stepEvents`, `buildStateJson`, `rosterJson`, `firstPersonJson`, the lull scan, the beat timeline. Retargeted fields, same structure. |
| `src/ctf/global.nim` | the sprite/object pools, the soldier/rig compositor, the FX families, the first-person raycast. Three named edits below. |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | label vocabulary, the rig art compositor, the one-source JS wire constants. |
| `client/broadcast_core.js`, `chrome_common.js`, `replay_broadcast.html`, `league_replayer.html` | the broadcast chrome (§Viewer). |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js`, `ctf_replay.nim` → `smac_replay.nim` | the emscripten link flags (`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, `useMalloc`, the `EXPORTED_FUNCTIONS` list), the OffscreenCanvas Worker, the stage-note diagnostics, the `data-replay-loaded`/`data-replay-error` signalling. |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix` | build, bundle and forensics wiring. |
| `data/` art: `soldier_{red,blue,green}*`, `rig_real/{red,blue,green}/*`, `font.ttf`, `atlas/*`, `ascii.png`, `arena_floor.png`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,red_*.webp,blue_*.webp,green_*.webp}` | real art, kept and reassigned (§Viewer §Art). `heart_*`, `ped_*`, `medkit`, `shield`, `paintbomb`, `spraycan*`, `paintgun*` and all yellow art are deleted with the mechanics they belong to. |

**Deleted** (with their tests, tools and docs), not disabled — every one is a config surface the micro
rules would otherwise have to reason about: spray cans and floor paint, the paint grid, the paint buff,
King of the Hill and `hillTicks`, the `resident`/`visitor` regimes, hearts/flags and capture, grenades
and the barrage, med kits, shields, cardboard barriers, paint puddles, trenches, perks, handicaps,
four-team free-for-all, respawns and `lives > 1`, the procedural generator and map pool, the map editor,
mapkit, the achievements catalog, and campaign mode.

**New modules:** `src/smac/units.nim` (the role table, per-unit hp/speed/weapon resolution, the damage
ledger), `src/smac/enemy_ai.nim` (the in-sim scripted army), `src/smac/scenario.nim` (spawn placement,
`enemyRoles` expansion, the army bookkeeping and the score terms), and the entrypoints
`src/smac_starcraft_micro.nim` (`/bin/smac-starcraft-micro`) and
`src/smac_starcraft_micro_player.nim` (`/bin/smac-starcraft-micro-player`).

### The four named edits to `server.nim`

1. **Turn boundary.** Unchanged in shape from the starter, with `turnTicks` = 120 and five seats in the
   batch instead of two.
2. **Registration interception.** A player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed as
   registration and is **not** applied as a shout and **not** written to the replay chat stream; the
   server writes a redacted `register` record instead (policy label and kind, never the prompt). The
   starter's "hold an unappliable registration and re-read it when the slot lands" behaviour is kept
   verbatim (the paintball round-3 scar). Any other chat text from a seat is dropped — units shout, seats
   do not.
3. **Battle switch.** When `gamesPlayed` increments, the loop archives
   `(ticks, endRule, dmgDealt, dmgTaken, kills, losses)` into `battleLog` before `resetToLobby()`, then
   re-spawns both armies with fresh seeded jitter.
4. **Wall-clock stop.** The starter's `wallClockBudgetSeconds` check at the top of every loop iteration,
   kept, forcing `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`. **The stop is recorded
   as one load-bearing record applied by the SAME proc on record and on playback** (particle-worlds
   `13c66d7`, 2026-08-26): a wall-clock fact cannot be re-derived from sim state, so writing it outside
   `sim.step` while still hashing that tick is what makes every deadline-ended replay show a hash
   warning. `GameVersion` is bumped for it and `tests/test_endings.nim` re-derives EVERY end reason, not
   just `complete`.

### The two named edits to `roster.nim`

1. **Aliases carry the role.** `cogAlias(cogIndex)` returns `ROLE-identity` for a friendly unit
   (`roleOf(cogIndex)` from the config's `roles` array, identity = `IdentityNames[rank among same-role
   seats]`) and `E<id>` for an enemy unit. `cogSeat(cogIndex) = cogIndex` for friendly units (one seat,
   one unit) and −1 for enemies. `slotIdentityIndex`/`shoutIdentityName` follow from `cogAlias`, so shout
   bubbles and sprite labels inherit the two-name-space rule with no further change.
2. **`squadResultsJson` becomes `microResultsJson`** — one entry per seat, five entries in every
   seat-indexed array, keys exactly as §Server lists them.

### The three named edits to `global.nim`

1. **Fog is off.** `buildSpriteProtocolPlayerUpdates` takes a **seat** index and, when `config.fogOfWar`
   is false, uses an all-visible mask instead of the seat's fov cache. The shadowcasting code stays (the
   first-person PIP still raycasts); only the per-seat mask changes.
2. **Health is drawn.** Every unit carries a 3 px hp pip bar above its sprite, filled to
   `hp / hp_max`, red for the enemy army and white for ours, plus the starter's existing floating damage
   pops. A spectator must be able to see focus fire *working*, not infer it.
3. **The two spawn columns are baked floor art**, not sprites: a chalked muster line at
   `x = friendlySpawnX` and a scorched line at `x = enemySpawnX`, composited into `arena_floor.png` at map
   install with pixie, the same way the starter bakes endzone paint.

### Determinism, native ↔ wasm

The mechanism is ctf's, unchanged, and it is the reason the starter is worth forking:

1. The server writes a `COWLDSMC` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `mapSpec`, roster, `roles`, `enemyRoles`, every tuning field), then the
   record stream — joins (name, slot, token), leaves, per-**cog** input-mask changes for the five friendly
   units, chat records (directives, fallbacks, register, budget guard, stop, result) and **one `gameHash`
   per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/smac_replay.nim` — which imports the **same**
   `src/smac/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container in
   `Dockerfile.replay-viewer`.
3. In the browser, `smac_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then `smac_frame`
   re-steps the sim from the recorded masks and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). A single divergent bit is caught at the tick it happens and
   surfaced as `mismatchTick` in `#mmwarn`.
4. **`gameHash` gains**, appended after the existing mixes so the ordering stays stable: per unit (ours
   and the enemy's, in cog order) `(x, y, aimBrads, hp, alive, fireCooldown, windupTicks, arcTicksLeft,
   damageDealt, kills)`; per enemy additionally `(targetSeat, retargetCounter, stuckTicks,
   stuckRotTicks)`; and `ourHp`, `theirHp`, `ourAlive`, `theirAlive`, `battleDmgDealt`, `battleDmgTaken`,
   `battlesWon`, `battleIndex`. `focusCount` is **derived**, not hashed.
5. **The enemy AI is inside the hash and is integer-only**: cell-free direct steering, integer squared
   distances, the integer hysteresis comparison, the integer quarter-turn deflection. The starter's
   existing float use inside the shot resolution (`BulletHalfWidth`, the jitter sigma) is kept exactly as
   it is — it is already recorded-and-re-derived by the starter's own wasm viewer — but **no new float
   enters the hashed path**. A CI grep over `src/smac/{units,enemy_ai,scenario}.nim` for
   `sin|cos|tan|arctan|sqrt|hypot|float` enforces it. This matters because Nim's `int` is 32-bit under
   `--cpu:wasm32` and the wasm build re-derives every tick.

**The sim guard `checkMicroInvariants()`** (step 6.7), evaluated every tick before any battle can be
ended on the numbers it checks: every living unit's centre is inside the map box and on non-wall floor;
`ourAlive`/`theirAlive` equal full recounts; every unit's `hp` is in `[0, maxHp]` and a unit with
`hp == 0` is not alive; `sum(damageDealt[ours]) == battleDmgDealt` and the same for the enemy side;
`battleDmgDealt <= enemyStartHp` and `battleDmgTaken <= ourStartHp` (the overkill clip, asserted rather
than assumed); `players.len == 5 + enemyRoles.len`. A trip raises `SimGuardError` → `fault`/`sim_fault`.

**Perf target:** 3 × 1440 ticks of sim plus mask compilation with 25 units on the board (the `corridor`
variant) in under 20 s on a CI runner; `tests/test_perf.nim` bounds it at 120 s.

---

## Server, player, protocol

`src/smac/server.nim` is ctf's `server.nim` with the four edits named above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`, `GET /client/player`,
`GET /client/replay`, `GET /replay-data`, `GET /reward`), same `COGAME_*` runtime contract
(`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`,
`COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`, `COGAME_HOST`/`COGAME_PORT`), same
403 on a bad slot/token, same **real pages on both `/client/` routes registered before any catch-all**
(the lantern 0.1.1 cert probe: the runner probes `/healthz`, `GET /client/player?slot=0&token=<t>`, a
bad-token player websocket and `GET /client/global` *before* starting player pods, and neither
`/client/` route may open the player socket), same bounded `/healthz` + `/global` shutdown grace (~20 s)
after artifacts are written (lantern 0.1.3), same `src/smac_starcraft_micro.nim` entrypoint with seed
randomisation **before** `config.update`.

### The player container

`src/smac_starcraft_micro_player.nim` (built to `/bin/smac-starcraft-micro-player`) is the starter's
`src/paintball_player.nim`, forked with the baseline names changed. It reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects with bounded dialling
(240 × 500 ms), and sends **one Sprite v1 chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"focusfire"|"charge"|null,"policy":"<free label>"}
```

Registration is **re-sent** for the first ~10 s of frames (10 re-sends, ~1 s apart), because joins are
slot-sequential and a seat whose slot is not the next open one is not admitted until the lower slots have
joined — the paintball round-3 scar, where a champion played the scripted baseline for a whole episode.
It then sends the Sprite v1 Ready packet (`0x85`) after each received frame — legitimate here because it
never sends inputs — and otherwise only receives. A seat that never registers, or registers with neither
field, is `scripted: "focusfire"`. The receive loop is wrapped in `try/except CatchableError`, re-dials a
dropped socket up to 6 times, and **exits 0 on a dead socket** — the raid 0.1.3 scar: whisky's
`receiveMessage` raises on a close frame, and the game's `quit(0)` can outrun the flushed frame, so a
naive player exits 1 and fails certification intermittently.

### Results document

Written by `sim.microResultsJson()` to `COGAME_RESULTS_URI`. It must equal the manifest's
`results_schema` key-for-key — that schema is `additionalProperties: false` and the certifier rejects any
unknown field. Adding or removing a key here means editing `coworld_manifest_template.json` in the same
commit.

```json
{"names": ["daveey", "daveey-1", "smac-starcraft-micro-focusfire",
           "smac-starcraft-micro-charge", "smac-starcraft-micro-focusfire"],
 "scores": [0.7132, 0.7130, 0.7134, 0.7129, 0.7133],
 "win": [true, true, true, true, true],
 "role": ["ranger", "ranger", "blade", "blade", "blade"],
 "alias": ["RANGER-alpha", "RANGER-beta", "BLADE-alpha", "BLADE-beta", "BLADE-gamma"],
 "damageDealt": [188, 164, 241, 233, 210],
 "damageTaken": [60, 41, 120, 96, 74],
 "kills": [2, 1, 3, 2, 1],
 "deaths": [1, 0, 1, 1, 0],
 "shots": [92, 84, 61, 58, 55],
 "llmTurns": [34, 34, 0, 0, 0],
 "fallbackTurns": [2, 2, 0, 0, 0],
 "teamScore": 0.7129,
 "battlesWon": 2,
 "battleResults": ["victory", "full_time", "victory"],
 "battleTicks": [812, 1440, 690],
 "battleDamagePct": [100, 71, 100],
 "battleLossPct": [39, 78, 31],
 "enemyKilled": 9,
 "enemyTotal": 15,
 "scenario": "default",
 "reason": "complete",
 "endRule": "victory",
 "games": 3,
 "finalTick": 2942,
 "seed": 679961}
```

`names` are the **real policy names** (spectator side). `alias` and `role` carry the in-game names. The
**26 keys are exactly the `results_schema` keys.** The twelve seat-indexed arrays (`names`, `scores`,
`win`, `role`, `alias`, `damageDealt`, `damageTaken`, `kills`, `deaths`, `shots`, `llmTurns`,
`fallbackTurns`) have exactly `num_agents` = **5** entries, which is what `docker_smoke.sh` cross-checks
against `SMOKE_SEATS`. The four battle-indexed arrays (`battleResults`, `battleTicks`, `battleDamagePct`,
`battleLossPct`) have between 1 and `maxGames` entries — a `deadline` can cut the episode after one
battle — and the schema bounds them `minItems: 1, maxItems: 6`.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDSMC`** format — the static wasm viewer parses exactly this,
and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`, `static_replay_worker.js` and
`wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse. The consequences are handled
explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker),
  retargeted: it takes a `.replay` path and prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"smac-starcraft-micro/v1","gameVersion":"1","seed":…,"scenario":…,"names":[…],
  "aliases":[…],"roles":[…],"enemyRoles":[…],"policyKinds":[…],"battles":…,"tickCount":…,
  "directives":[…],"fallbacks":N,"results":{…}}`. It brace-matches the config JSON from the first `{`
  (the technique the starter's `AGENTS.md` documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.enemyKilled, .results.teamScore' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "smac-starcraft-micro/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), `results.enemyKilled > 0`, and the champion seats' directives
  `source == "llm"` with non-empty `note` and real intents — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDSMC`, format version, `gameName` `smac-starcraft-micro`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `mapSpec` (the full resolved arena geometry), `roles`, `enemyRoles`, `scenario`, `maxTicks`, `maxGames`, `turnTicks`, every unit/AI/scoring constant, `players[].name` (real names), `slots[]`, `fastMode` |
| joins | per **seat**: `name` (real policy name), `slot`, `token` |
| inputs | per **friendly cog** (0..4), on change: the `uint8` actuator mask — the action log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

**The entire enemy army is re-derived**, never recorded: its spawn positions come from the sim RNG seeded
by the config seed, and every one of its decisions is a pure integer function of the sim state. That is
why the file stays small — ~2900 ticks of hashes plus ~25 k mask-change records plus 180 directive
records ≈ **330 KB**, well under 1 MB — and why a hash mismatch is a real integrity signal rather than a
rendering nit.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed sim fields;
they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `alias`, `role`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `battle`, `turn`, `seat`, `alias`, `role`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note` (≤ 160 runes), `cogs`:[{`id`,`intent`,`target_id`,`target`,`face`,`say`}] |
| `fallback` | `battle`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `reason` (`deadline`), `endRule` (`wall_clock`) — the load-bearing wall-clock stop, applied by the same proc on record and on playback |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. They feed the
match feed, the scrubber beats and the momentum graph:

`phase`; `battlestart` `{battle, scenario, ours, theirs}`; `shot` `{by}`; `swing` `{by}`;
`hit` `{by, target, dmg, hpLeft}`; `kill` `{by, alias, target, targetRole}`;
`loss` `{who, alias, by}`; `firstblood` `{by, target}`;
`focus` `{target, n}` — emitted when `focusCount` for one enemy first reaches 2 or more, throttled to one
per 24 ticks; `lastcog` `{who}` — one friendly unit left alive;
`battleover` `{battle, endRule, ticks, damagePct, lossPct}`.

**Beats** (scrubber markers, and the only kinds the appended block emits): `battlestart`, `firstblood`,
`loss`, `lastcog`, `battleover`.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Shot, Swing, Hit, Damage, Kill, Death, PhaseChange, ShoutEvent` and extended
with `Focus, Directive`; the mandatory trailing summary row (`type`, `ticks`, `events`, `gameVersion`) is
kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is the starter's
script, kept, with two literals changed (`image_tag`, and the `docker cp` source
`/workspace/smac/replay-viewer/dist/.`); it builds `Dockerfile.replay-viewer`'s `replay-viewer-builder`
target and copies the dist out. It must stay committed **executable** (`coworld build` requires
`os.X_OK`), and the hook `mkdir -p`s the output parent before its containment check (the ecos 2026-08-23
scar: `coworld build` pre-creates that directory, CI does not).

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/smac_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html`) ALL come from ONE starter: `coworld-ctf`.**
Never a mixture. Splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently
(cogame-lantern, 2026-08-23). coworld-ctf's set is internally consistent and is kept as one piece: the
Worker sets `Module.onRuntimeInitialized`, the module is emitted **non-modularized** as `smac_replay.js`,
`config.nims` exports
`_smac_load_replay,_smac_frame,_smac_input,_smac_packet_ptr,_smac_packet_len,_smac_mismatch_tick,
_smac_error_ptr,_smac_error_len,_smac_stage_ptr,_smac_stage_len` alongside `_main,_malloc,_free`, and
`static_replay_worker.js` does
`importScripts('./wire_constants.js','./broadcast_core.js','./smac_replay.js')` in that order.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — which the Worker posts only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means "a
frame is on the canvas", not "a file was fetched". On failure the shell sets **`data-replay-error`** on
`<html>` with the message, in `showFailure()`. Both signals already exist in coworld-ctf's
`static_replay.js` and are inherited unchanged — this fork adds neither and removes neither. The
`coworld-replay` postMessage bridge's `ready` is posted from a callback fired **after**
`data-replay-loaded="true"` is set, never on rAF timing at the call site (chorus `3c11c953`,
2026-08-24) — otherwise the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from coworld-ctf.** Not edited, not reformatted;
  `tests/test_viewer.nim` pins its sha256. Everything this game adds lives in the appended game block.
  Its `markBeat`/`renderBeatMarkers`/`ingestBeats` remain; `ingestBeats` ignores kinds it does not know
  and still drives `setVerdict` off the battle-over beat, which is exactly the behaviour this game wants.
- **`client/broadcast_core.js` is copied byte-for-byte** apart from the single `window.CTF_WIRE` →
  `window.SMAC_WIRE` identifier, which `tools/gen_wire_constants.nim` emits. The test asserts the diff is
  exactly that identifier.
- **`client/replay_broadcast.html` is the starter's page with a game block APPENDED** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`, transport,
  endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched; the appended
  block replaces only the *contents* of the scorebug plates, adds the two army-strength bars and the
  focus ring, and retargets the feed rows, the beat rendering and the endcard's stat columns.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — the zoom bar (`#zoombar`, `#zoom-in`, `#zoom-out`, `#zoom-slider`, `#zoom-read`)
    and the minimap (`#minimap`, `#minimap-canvas`). **Zoom decision: dropped.** The board is the fixed
    1235 × 659 arena and `relayout()` always fits it whole inside the frame, so per the pin a fixed arena
    drops `#viewpanel` entirely; the page's `attachMinimap(...)` call goes with it (`broadcast_core.js`
    tolerates a missing minimap — `pendingMinimap` simply stays null — so that file stays byte-identical).
  - The heart/flag scorebug fields (`flag-*`, `carrier`, `prog`) and the `.ec-heart` endcard glyphs.
  - The hill chips (`.hillchip`, `#hill-*`, `#hcap-*`) and the paint-coverage arc.
  - The `.beat-marker.steal`, `.return`, `.capture`, `.hillflip` and `.hillhold` CSS rules (their kinds
    are never emitted here).
  - The perk and handicap badges (`#tags-*`).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`, `#chrome`,
    `#scorebug` with `#plates-l`/`#plates-r`/`#clock`, `#bannerlane`, `#killfeed`, `#fpv` (the
    first-person picture-in-picture), `#povBadge`, `#mmwarn`, `#transport` **in full**, `#scrub` with
    `#momentum`/`#lulls`/`#scrub-win`/`#scrub-head`, `#endcard`.

### Transport rules

`relayout()` sets `--band` (the measured transport strip), `--topband` (the scorebug strip) and
`--hudscale` on `:root`, unchanged. **No overlay sits in the transport band**: the board is laid out
between the two bands, and every addition here (the army bars, the focus ring, the feed, the banners) is
positioned inside the board region or in the top band. The **endcard stops at `var(--band)`**
(`#endcard { bottom: var(--band, 0px) }`, the starter's rule, kept) so the scrubber stays clickable
underneath, and it is **dismissed by every seek** (the starter's
`else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats are clickable, labelled
buttons**: the appended block's `smacBeat(tick, kind, side, label)` — named so it can never shadow
chrome_common's `markBeat` alias, the tandem 2026-08-23 hoisting trap — appends
`<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind this game emits** and no others: `.beat-marker.battlestart`,
`.beat-marker.firstblood`, `.beat-marker.loss`, `.beat-marker.lastcog`, `.beat-marker.battleover`. The
game never calls chrome_common's `markBeat`, so no unlabelled div marker can appear.

### Readouts

1. **Two army-strength bars** — a full-width double strip immediately under the scorebug, inside the top
   band: OURS (white) and THEIRS (red), each filled to `hp / hp_max` for the current battle, with a
   segmented notch per living unit and the numerals `4 UP · 301/480 (63%)`. This is the idea's
   "shared win reward + damage shaping" made visible: the bars *are* the score.
2. **Five seat plates** — three left and two right of the centre clock: the seat's **real policy name**
   (spectator side), a role glyph (gun / blade), a slim hp bar, and its **damage dealt** in the big
   numeral with kills in the small one. A dead unit's plate goes grey with a struck-through name and the
   tick it fell.
3. **Focus ring** — the single most legible thing in the game: whenever two or more of our units are
   attacking the same enemy, that enemy gets an animated ring on the board with the count inside it
   (`×4`), and the feed prints `FOCUS FIRE — 4 ON E3`. A spectator sees the squad's coordination as a
   shape, not as text.
4. **Clock** — `M:SS` counting down inside the current battle, with the caption
   `battle 2/3 · default · 4 v 3 · turn 5/12`.
5. **Match feed** (`#killfeed`, renamed in copy only) — plain language, never internal notation:
   "RANGER-alpha drops E3", "BLADE-beta steps in front of RANGER-beta",
   "**E5 IS ON RANGER-alpha**", "**BLADE-gamma IS DOWN**",
   "**ARMY DESTROYED — BATTLE 1 WON, 39% HEALTH LOST**", and the commander lines
   ("Ranger-alpha: everyone on E3, blades screen the rangers"). The directive `note` and each unit's
   `say` appear here; this is where a spectator sees the LLM playing.
6. **Momentum graph** — the starter's `lead` series, retargeted to two series over the whole episode: our
   army hp % and the enemy army hp %, with the battle boundaries marked. It is shipped once on the first
   frame, so the graph draws its full width immediately.
7. **Health pips and damage pops** — per-unit hp bars (§Sim module edit 2) and the starter's floating
   `-4` / `-10` pops and `KO` markers, kept.
8. **First-person PIP** (`#fpv`) — unchanged: the view down a ranger's barrel as a blade closes.
9. **Transport and integrity** — play/pause, step, speeds `[1,2,3,4,8,16]`, scrubber with beat buttons,
   tick readout, skip-lulls, spoilers switch, end-hold countdown, and the `#mmwarn` hash-mismatch line —
   all verbatim.
10. **Endcard** — "BATTLE 1 WON · BATTLE 2 DRAWN · BATTLE 3 WON", the five-seat table (damage dealt,
    damage taken, kills, survived), the team line "9 OF 15 KILLED · 2 BATTLES WON · SCORE 0.713", and the
    per-battle damage/loss percentages. It stops at `var(--band)` and any seek dismisses it.

### Art

Real, and already in the repo. **Our squad** is the shipped `data/soldier_red*` sprites on the
`data/rig_real/red` rigs; **the enemy army** is the shipped `data/soldier_blue*` on `data/rig_real/blue`;
the **corridor swarm** is the shipped **green** family (`data/soldier_green*`, `data/rig_real/green`)
re-composited at startup by `global.nim`'s own soldier compositor at 0.7 × scale with a desaturated
palette pass, so twenty of them read as a swarm rather than a third team. **Held weapons** are baked at
startup by the starter's own pixie compositor in `rig_art.nim`, which already draws the held-item
silhouette and its warm rim glow procedurally: the ranger keeps the starter's 34 px top-down gun
(`GunLengthPx`/`GunGripPx`/`GunRightPx`, unchanged); the blade is a 24 px straight blade at the
short-item grip the spray can uses (`SprayHeldGripPx`), so the two silhouettes are distinguishable at a
glance, which is the whole reason the starter draws held items at all. Walls are
`client/art/walls/*.jpg`; the loading screen is the starter's locker room (`client/art/lockerroom/bg.jpg`
plus the red/blue/green cog webps). The two spawn lines are baked into the floor art (§Sim module edit 3).
No solid-colour placeholders, no TODO assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at desktop
width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`. Kept verbatim.
This game adds three rules of its own: `.plate-name` gets
`flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis` so a policy name never
collapses to "…" (the featured-match scar); under `.tiny` a plate keeps only `glyph + name + hp bar` and
drops the kill numeral, so five plates still fit; and under `.tiny` the army bars drop their per-unit
notches, keeping the two fills, the percentages and the alive counts so they read as
`▰▰▰▱▱ 63% · 4  |  ▰▰▱▱▱ 45% · 3`. `tests/test_viewer.nim` asserts all three rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-smac-starcraft-micro`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `smac-starcraft-micro`; `game.name` is
  **`smac-starcraft-micro`** (hyphenated, matching the slug), so the secret namespace
  `secret://coworld/smac-starcraft-micro/anthropic_api_key`, the page slug, `POST /coworld-league-seeds`
  and the docs all agree (the cooperative-hunting 2026-08-25 scar: the namespace must equal `game.name`
  exactly).
- **`compose.yaml`** — one service, **underscored** so the derived manifest placeholder is
  `{{SMAC_STARCRAFT_MICRO_IMAGE}}` (placeholders come from compose service names — the lantern 0.1.0
  scar; `{{GAME_IMAGE}}` is not a thing):

  ```yaml
  services:
    smac_starcraft_micro:
      image: coworld-smac-starcraft-micro:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  (ctf ships two services / two images; this fork uses the one-image / two-entrypoints shape because the
  shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (nimby
  0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:smac-starcraft-micro
  src/smac_starcraft_micro.nim` → `/bin/smac-starcraft-micro`, and the same for
  `src/smac_starcraft_micro_player.nim` → `/bin/smac-starcraft-micro-player`. The runtime stage copies
  both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/smac-starcraft-micro"]`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby 0.1.27
  with its sha256 check, the three marker splices, the whole `test -f` / `grep -q` assertion block) with
  the asset list swapped: red/blue/green soldier art and rigs, walls, locker room, `font.ttf`,
  `smac_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`, `league.html`.
- **`coworld_manifest_template.json`** (validated offline with the CLI's `validate_upload_manifest`
  before the first dispatch — the hive 0.1.0 scar):
  - `$schema` set; top-level `tags`:
    `["micro","cooperative","smac","rts","combat","llm","starcraft"]`; top-level
    **`episode_timeout_minutes: 20`**; top-level `player[]`; `game.owner` present; `game.description`
    present (required); **no** `game.tags` (forbidden — tags are top-level only), **no** top-level
    `replay_viewer`, **no** top-level `version`, **no** `game.display_name`.
  - `game.name` `smac-starcraft-micro`; `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.runnable` = `{"type":"game","image":"{{SMAC_STARCRAFT_MICRO_IMAGE}}",
    "run":["/bin/smac-starcraft-micro"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/smac-starcraft-micro/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-smac-starcraft-micro/tree/main"}` — the `env` entry
    is mandatory: without it the hosted game container never sees the coworld secret and every league
    episode silently plays scripted (hive, 2026-08-23).
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`, **every array property bounded with `minItems`/`maxItems`** (the tandem 0.1.0
    scar): `tokens` (5, 5), `players` (5, 5), `slots` (5, 5), `roles` (5, 5, items enum
    `["ranger","blade"]`), `enemyRoles` (**minItems 1, maxItems 24**, items enum
    `["ranger","blade","swarm"]`). Scalars, with defaults: `seed`, **`num_agents`** (integer 5..5, default
    5), `minPlayers` (5), `scenario` (string), `maxTicks` (1440), `maxGames` (3), `turnTicks` (120),
    `turnBudgetMs` (10000), `attempt1Ms` (6000), `retryMs` (3000), `turnSpacingMs` (12000),
    `wallClockBudgetSeconds` (690), `lobbyJoinTimeoutTicks` (2400), `startWaitTicks` (120),
    `gameOverTicks` (72), `mapPath` (`"arena"`), `fogOfWar` (false), `fastMode` (true),
    `showPlayerLabels` (false), `friendlySpawnX` (380), `enemySpawnX` (855), `spawnSpacingPx` (44),
    `spawnJitterPx` (24), `rangerHp` (60), `rangerRange` (380), `rangerDamage` (4), `rangerCooldown` (18),
    `bladeHp` (120), `bladeSpeedPct` (115), `bladeReach` (56), `bladeArcBrads` (32), `bladeDamage` (10),
    `bladeCooldown` (30), `swingTicks` (4), `swarmHp` (30), `swarmSpeedPct` (130), `swarmReach` (40),
    `swarmDamage` (6), `swarmCooldown` (24), `aggroPx` (600), `leashPx` (700), `retargetTicks` (48),
    `enemyStuckTicks` (24), `rangerStandoff` (300), `kiteStandoff` (340), `screenStandoff` (90),
    `chaseCapPx` (520), `panicPx` (150), `winWeightPermille` (600), `dmgWeightPermille` (300),
    `survWeightPermille` (100), `creditEpsilonPerMyriad` (4), `model`, `maxOutputTokens` (900).
  - **No literal `tokens` array in any variant's `game_config` or in `certification.game_config`** — the
    runner injects them, and matriculate rejects `game_config must not include runner-managed tokens`
    (cogame-knights-archers 0.1.0, 2026-08-26). `config_schema` still *requires* `tokens`; that is
    correct and is asserted both ways in `tests/test_manifest.nim`.
  - `game.results_schema`: exactly the 26 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","role","reason","endRule"]`; the twelve seat-indexed arrays
    `minItems: 5, maxItems: 5`; the four battle-indexed arrays `minItems: 1, maxItems: 6`; `reason` enum
    `["complete","deadline","fault"]`; `endRule` enum
    `["victory","wipe","full_time","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both** `player` and `global`, each
    `{"type":"text","value":"<docs/PROTOCOL.md inlined>"}` — object form, not a bare string (the garble
    v0.1.0 scar).
  - `game.docs`: **`readme`** = `{"type":"text","value":"<README body inlined>"}` and **`pages`** = four
    entries — `rules` ("Rules", `docs/RULES.md` inlined), `scenarios` ("Scenarios and their SMAC
    lineage", `docs/SCENARIOS.md` inlined — including the "no OpenBW, no Blizzard assets, no parity
    claim" statement), `protocol` ("Wire protocol", `docs/PROTOCOL.md` inlined), `commanding` ("Writing a
    micro prompt", `docs/COMMANDING.md` inlined) — each
    `{"id","title","content":{"type":"text","value":…}}`. **Text form, not URIs.**
    `tests/test_manifest.nim` asserts all five values are non-empty.
  - `player[0]` = `{"id":"baseline","type":"player","name":"Focus Fire Baseline",
    "description":"Scripted unit: the whole squad derives one kill order from state, rangers kite when a
    melee enemy closes, blades screen the rangers.","image":"{{SMAC_STARCRAFT_MICRO_IMAGE}}",
    "run":["/bin/smac-starcraft-micro-player"],"env":{"PLAYER_SCRIPTED":"focusfire"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}` — the only declared
    player, and it is seated in **all five** certification slots (the raid 0.1.2 `players_missing` scar:
    every declared player entry must occupy a certification slot; and the pistonball 0.1.1 scar: the
    bundled player CPU limit minimum is `"1"`).
  - **Variants — `num_agents` is 5 in all four**, each with a required `description`:

    | id | name | `num_agents` | `roles` | `enemyRoles` | enemy hp pool |
    |---|---|---|---|---|---|
    | `default` | Micro — two and three | **5** | 2 × ranger, 3 × blade | 2 × ranger, 3 × blade | 480 |
    | `outnumbered` | Micro — five against six | **5** | 5 × ranger | 6 × ranger | 360 |
    | `corridor` | Micro — the corridor | **5** | 5 × blade | 20 × swarm | 600 |
    | `heavy` | Micro — outgunned | **5** | 2 × ranger, 3 × blade | 3 × ranger, 4 × blade | 660 |

    Every variant also carries `players` (5 named entries), `slots`
    (`[{"team":"red"}] × 5`), `minPlayers: 5`, `scenario` (= the variant id), `mapPath: "arena"`,
    `fogOfWar: false`, `maxTicks: 1440`, `maxGames: 3`, `turnTicks: 120`, `turnBudgetMs: 10000`,
    `attempt1Ms: 6000`, `retryMs: 3000`, `turnSpacingMs: 12000`, `wallClockBudgetSeconds: 690`,
    `lobbyJoinTimeoutTicks: 2400`, `fastMode: true`, `showPlayerLabels: false`, `seed: 679961`, and the
    full unit/AI constant block at its defaults. `default` is what the league ranks; the other three
    change **composition only**, never the seat count, and are scored on the same normalised [0, 1] scale
    (every damage term divides by that scenario's own starting pool) so a harder scenario is genuinely
    harder to score on. The four scenarios are this repo's adaptations of the SMAC shapes **2s3z**,
    **5m_vs_6m**, **corridor** and **3s5z_vs_3s6z**; `docs/SCENARIOS.md` states the lineage and the
    no-parity claim.
  - **Certification fixture**: `certification.players` = five `{"player_id":"baseline"}` entries;
    `certification.game_config` = `{"players":[{"name":"Unit A"},{"name":"Unit B"},{"name":"Unit C"},
    {"name":"Unit D"},{"name":"Unit E"}], "slots":[{"team":"red"} × 5],
    "roles":["ranger","ranger","blade","blade","blade"],
    "enemyRoles":["ranger","ranger","blade","blade","blade"], "num_agents": 5, "minPlayers": 5,
    "scenario":"default", "seed": 679961, "mapPath": "arena", "fogOfWar": false, "maxTicks": 480,
    "maxGames": 3, "turnTicks": 120, "turnBudgetMs": 10000, "turnSpacingMs": 0,
    "wallClockBudgetSeconds": 180, "lobbyJoinTimeoutTicks": 1440, "startWaitTicks": 0,
    "gameOverTicks": 24, "friendlySpawnX": 470, "enemySpawnX": 760, "fastMode": true,
    "showPlayerLabels": false}` — all five seats scripted, no LLM, no rate floor, three 480-tick battles.
    The spawn columns are pulled to 290 px apart so contact happens inside the first 100 ticks and the
    fixture reliably produces shots, hits, a `firstblood`, a `loss` and a `battleover`: a fixture that
    renders two armies walking tests nothing. Expected length ≈ **1100–1440 ticks = 46–60 s of playback**
    at 24 fps, deliberately longer than any viewer soak window (the ecos 2026-08-23 scar), while
    `fastMode` plays it in a handful of wall seconds. The `certify` step in `coworld-release.yml` passes
    **`--timeout-seconds 300`** (the default 60 s does not cover start + connect grace + three battles +
    linger — cooperative-hunting 0.1.2).
- **Scaffold from `templates/`** with `<slug>` = `smac-starcraft-micro`, `<IMAGE>` =
  `coworld-smac-starcraft-micro`, `<SEATS>` = **5**:
  `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`, `tools/ci/docker_smoke.sh`
  (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (**copied verbatim**, no substitutions),
  `tools/ci/policies.json`, plus the starter's `tools/build_replay_viewer.sh` (**`chmod +x`**). Three
  additions to the template `ci.yml`:
  - the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format);
  - the `wasm-viewer` job gets a final step
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` — the
    native↔wasm determinism gate, which fails if `smac_mismatch_tick() != -1`;
  - repo variable `NIM_TESTS_RELEASE_ONLY` lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/smac-starcraft-micro-player"`, one image,
  env-switched):

  | name | env | role |
  |---|---|---|
  | `smac-starcraft-micro-marshal` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `smac-starcraft-micro-skirmish` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `smac-starcraft-micro-focusfire` | `PLAYER_SCRIPTED` = `focusfire` | filler |
  | `smac-starcraft-micro-charge` | `PLAYER_SCRIPTED` = `charge` | filler |

- **Repo layout**: `src/smac_starcraft_micro.nim`, `src/smac_starcraft_micro_player.nim`,
  `src/smac/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, arena.nim, map_art.nim, units.nim,
  enemy_ai.nim, scenario.nim, control.nim, directives.nim, baselines.nim, llm.nim, decide.nim,
  roster.nim, replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim,
  rig_art.nim, wire_constants.nim, server.nim}`, `replay-viewer/{smac_replay.nim, config.nims,
  static_replay.js, static_replay_worker.js}`, `client/`, `data/`, `tests/`,
  `tools/{build_replay_viewer.sh, gen_wire_constants.nim, expand_replay.nim, extract_events.nim,
  replay_summary.py, record_fixture.sh, wasm_replay_smoke.cjs, ci/}`,
  `docs/{RULES.md, SCENARIOS.md, PROTOCOL.md, COMMANDING.md,
  plans/2026-08-27-smac-starcraft-micro-design.md}`, `AGENTS.md`, `README.md`, `config.json`,
  `nimby.lock`, `smac_starcraft_micro.nimble`, `compose.yaml`, `coworld_manifest_template.json`,
  `Dockerfile`, `Dockerfile.replay-viewer`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables Nim's
range/overflow checks — the cheapest catch for an index or fixed-point overflow). CI is the only harness;
the sandbox has no Nim, Docker or emsdk.

1. **`tests/test_units.nim`** — sim unit tests for the two weapons: a ranger's shot removes exactly 4 hp,
   fires no more often than every 18 ticks, lands only after a 5-tick windup with the aim **locked at the
   pull**, never crosses a wall, and cannot hit a friendly unit; a blade's swing removes exactly 10 hp,
   hits every enemy inside the 56 px ±45° wedge and none outside it, hits nothing behind a wall, and
   damages each victim **at most once per activation** across its 4 lit ticks; hp floors at 0 and a unit
   at 0 hp is not alive; overkill damage is clipped out of the ledger (a 3 hp unit hit for 10 banks 3);
   a blade covers 3.16 px/tick and a swarm 3.57 px/tick; a lone ranger kiting with 400 px of room beats a
   lone blade and the same ranger cornered does not.
2. **`tests/test_enemy_ai.nim`** — the scripted army: an enemy picks the nearest visible friendly unit
   inside 600 px and keeps it while it lives and stays inside 700 px; the 1.5× hysteresis prevents a
   retarget between two equidistant units; an enemy with no target walks toward the friendly spawn anchor;
   an enemy walled into a pocket rotates after 24 stuck ticks and escapes within 120; two runs from the
   same seed produce byte-identical enemy streams and two runs from different seeds do not; a CI grep
   proves `src/smac/{units,enemy_ai,scenario}.nim` contain no floating-point token.
3. **`tests/test_scoring.nim`** — the formula and its sign: `battle_b` is 0 at (no win, no damage, all
   health lost) and 1 at (win, no damage taken), monotone non-decreasing in `dmgFrac` and non-increasing
   in `lossFrac`, and never negative; `dmgFrac == 1` **iff** every enemy is dead; `teamScore ∈ [0, 1]`;
   all five seats' `teamScore` are **exactly equal** over 10 000 random draws;
   `max(credit) - min(credit) <= 0.0004 < 0.000606` — one ranger shot of team damage in the worst-case
   variant strictly dominates the whole epsilon range; `win[s]` is the same boolean for all five seats and
   equals `teamScore >= 0.5`; a `deadline` scores the battles banked with unplayed battles at 0; a `fault`
   scores what was banked with `win` false everywhere.
4. **`tests/test_endings.nim`** — end conditions: the last enemy dying with one of ours alive ends the
   battle `victory` on that tick and not the next; our last unit dying ends it `wipe`; a tick in which
   both happen is `wipe` (the order in §The game step 6.8); 1440 ticks with both sides standing is
   `full_time`; `battleLog` records exactly one entry per battle played; the 690 s stop yields
   `deadline`/`wall_clock`, and **re-deriving the replay reproduces the hash at the stop tick** — the
   record→re-derive assertion runs for **every** end reason, not just `complete` (particle-worlds
   2026-08-26); a tripped invariant yields `fault`/`sim_fault` with a partial replay; `results.reason` and
   `results.endRule` are always members of the two declared enums.
5. **`tests/test_control.nim`** — **the bounded-orders / legality assertion on the scripted baselines**:
   for 500 pseudo-random world states × both baselines × all five seats, the emitted directive validates
   against the reply schema — exactly the seat's own id, an intent in the enum, a `target_id` that is
   either null or a **living** enemy, a target inside the map and on walkable ground, `note` ≤ 160 runes,
   `say` ≤ 10 runes — and every compiled mask has only legal bits, never Up+Down or Left+Right together,
   never `C`. Plus: the same (state, order) pair always yields the same byte; `retreat` never sets `A`; a
   ranger never sets `A` with nothing on the ray and a blade never sets `A` with nothing in the wedge; the
   trigger is never set during a cooldown or a windup; a `kite` ranger stops moving on the tick its
   cooldown reaches 0 with an enemy in range and moves otherwise; a unit ordered to an unreachable target
   still moves every tick for 120 ticks; and a `focusfire × 5` episode at seed 679961 completes and scores
   **strictly higher** than a `charge × 5` episode at the same seed on every shipped variant, killing at
   least 3 enemy units in `default` (a pinned regression against a baseline that does nothing).
6. **`tests/test_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON, `cogs`
   as an id-keyed object, a bare order object with no `cogs` wrapper, unknown and hyphenated intents,
   `"E3"` where an integer `target_id` was asked for, a `target_id` naming a dead enemy, a `target_id`
   naming an enemy that never existed, absent/NaN targets, off-map targets, a target inside a wall, three
   cogs, zero cogs, an id belonging to another seat, a 300-character `note`, and a `say` whose 10th and
   11th characters are a 4-byte emoji — the truncation must land on the **rune** boundary and the result
   must still round-trip `%$` → `parseJson` and decode as UTF-8. Two consecutive failures ⇒ the
   `focusfire` directive plus a `fallback` record; a timeout on attempt 1 ⇒ exactly one retry; a
   `throttled` attempt 1 ⇒ **no** retry and an immediate scripted turn.
7. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: **all five** seats' calls go out
   in **one parallel batch** (the fake records in-flight windows and the test asserts all five intersect);
   the per-turn budget is enforced with a hung client; `turnSpacingMs` holds the batch rate at ≤ 30 req/min
   for five seats; the budget guard switches to scripted and the episode still ends `complete`; a
   disconnected seat plays `focusfire` and revives on reconnect; a never-connecting seat is reported to
   `COGAME_PLAYER_FAILURE_URI` and all three battles still play; a seat's directive is never empty on any
   tick after turn 0.
8. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full scripted 5-seat,
   3-battle episode writes `results.json` and a `COWLDSMC` replay; `parseReplayBytes` accepts it;
   re-simulating from the config + mask log reproduces **every** recorded hash (including every enemy
   decision and every spawn, which are re-derived and not recorded); **strict-UTF-8 parse** —
   `tools/replay_summary.py`'s stdout parses under `json.loads(out.decode("utf-8"))` and the embedded
   config JSON decodes strictly, with the fixture forced to carry a non-ASCII policy label and a non-ASCII
   `note` so the UTF-8 path is real; every `directive` record is ≤ 900 runes; `results.reason` is in the
   legal enum; the stream contains at least one `shot`, one `swing`, one `hit`, one `kill`, one `focus`,
   one `directive` per seat per turn, three `battlestart` records and exactly one `result` record.
9. **`tests/test_identity_privacy.nim`** — the starter's test, **kept and extended**: no sprite label in a
   *seat* frame, no shout bubble, no LLM system-or-user message and no `directive` record ever contains a
   sentinel policy address — while the broadcast stream, `roster[].name`, the DOM scorebug and
   `results.names` **must** contain it. That is the two-name-space pin, asserted from both sides. Also: a
   seat's view JSON contains only `RANGER-*`/`BLADE-*`/`E<n>` names, and never another seat's
   *current-turn* note.
10. **`tests/test_observation.nim`** — the view contract: with `fogOfWar: false` every seat's frame
    contains every living unit on both sides; the view JSON's `enemies` array is sorted by distance
    ascending and capped at 24; `focused_by` agrees with a full rescan of the sim; `squad[].last_note` is
    last turn's and never this turn's; the seed, the RNG state, the enemy AI's retarget/stuck counters and
    any future jitter appear nowhere in any seat-facing byte.
11. **`tests/test_manifest.nim`** — `num_agents == 5` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 5` and
    `len(certification.game_config.players) == 5`; **no variant declares `num_agents` at its top level**
    (goofspiel scar) and **no `game_config` carries a literal `tokens` array** (knights-archers scar) while
    `config_schema.required` still contains `tokens`; `results_schema` keys == `microResultsJson` keys;
    `game.protocols` has both `player` and `global` in object form; `game.docs.readme` and all four pages
    are non-empty **text**; `replay_viewer.bundle == "static-replay-viewer"`; every variant's
    `wallClockBudgetSeconds <= 0.6 * 1200`; every array property in `config_schema` declares
    `minItems`/`maxItems`; `game.description` present and `game.tags` absent; ≥ 3 top-level `tags`;
    `episode_timeout_minutes == 20`; the compose service name derives `{{SMAC_STARCRAFT_MICRO_IMAGE}}` and
    the image is `coworld-smac-starcraft-micro`; `game.name` equals the secret namespace in
    `game.runnable.env.ANTHROPIC_API_KEY_URI`; `config_schema` covers every field `sim_config.update`
    reads; and **every variant's `game_config` actually constructs a sim** (the collab-cooking 0.1.1 scar:
    test EVERY variant, not just the fixture — here that means the 25-unit `corridor` roster is built and
    stepped).
12. **`tests/test_viewer.nim`** — the static half of the **viewer smoke** (no browser): assertions over
    `client/replay_broadcast.html` and `client/chrome_common.js` that the transport controls, `#scorebug`,
    `#bannerlane`, `#killfeed`, `#endcard`, `#mmwarn`, the `.tiny` block, the `--hudscale` clamp,
    `#endcard { bottom: var(--band`, the army-bar block, the focus ring and the three `.tiny`/`.plate-name`
    rules are present; that `#viewpanel`, `#minimap` and `#zoombar` are **absent**; that `chrome_common.js`
    is byte-identical to the starter's copy (sha256 pinned in the test); that `broadcast_core.js` differs
    from the starter's in **exactly** the `SMAC_WIRE` identifier; that the appended game block defines no
    identifier that collides with the chrome alias list (the tandem shadowing guard) and defines CSS for
    **every** beat kind the sim emits and no kind it does not; and that no `ctf_`/`CTF_` identifier
    survives in `client/`, `replay-viewer/` or `src/`.
13. **`tests/test_startup.nim`** — `/bin/smac-starcraft-micro` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when unpinned and
    honoured when pinned; both `/client/global` and `/client/player` serve a real page and neither opens
    the player socket (the lantern 0.1.1 cert probe); `/healthz` and `/global` keep answering for the
    shutdown grace after artifacts are written (lantern 0.1.3); both entrypoints exist and are executable
    in the image (asserted by the docker smoke).
14. **`tests/test_perf.nim`** (release-only) — a full 3 × 1440-tick `corridor` episode (25 units) with mask
    compilation completes in under 120 s.

Beyond the Nim suite, `ci.yml` runs:

- **`tools/ci/docker_smoke.sh`** — a raw-Docker episode from the certification fixture in the production
  image, seats cross-checked against **`SMOKE_SEATS=5`**, `SMOKE_REQUIRE_REPLAY_JSON=0`, asserting the
  game container exits 0 with `results.json` and a replay, **and** that every *player* container exited 0
  (the raid 0.1.3 scar). Its replay is uploaded as the `smoke-replay` artifact.
- **the `wasm-viewer` job** — builds the bundle, asserts `index.html` and a non-empty `.wasm` exist, then
  **executes** it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
  dist/smoke/<replay> --timeout 90 --strict-text-bounds`, against the replay **`docker-smoke` produced**
  (the job `needs: docker-smoke` and downloads the `smoke-replay` artifact). The bundle is **executed, not
  merely built**; the job fails unless `data-replay-loaded="true"` appears within the timeout, and
  `--strict-text-bounds` is kept because the arena is fixed and fits the frame, so
  `canvas_text.never_inside` must be 0. The job then runs
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/<replay> 300` as the native↔wasm
  hash gate.

---

## Out of scope (v1)

- **OpenBW, Brood War and `Metta-AI/coworld-bw`.** No engine wrap, no BWAPI, no Blizzard data files, no
  Blizzard art, no `.rep` replays and no OpenBW rendering. The coordinator's binding ruling: `coworld-bw`
  is not available, the idea sanctions the dependency-free route, and this coworld implements the rules
  natively on paintbot with its own art and its own static wasm viewer.
- **Bit-exact parity with SMAC, SMACv2 or SMAX.** The scenarios are adaptations of those *shapes*; no
  numerical, action-space or reward-curve parity is claimed or tested, and no PySC2/JaxMARL dependency is
  taken.
- **SMACv2's randomised generators.** Randomised unit *types* per episode, randomised start positions
  beyond the seeded ±24 px jitter, and randomised spawn geometry are all v0.2. `enemyRoles` and `roles`
  are already the right shape for a generator to write into.
- **The full SMAC scenario roster.** Four scenarios ship; the other twenty-odd are `enemyRoles`/`roles`
  values away and cost nothing but variants, which the seat-count pin bounds at five units per scenario.
- **Unit abilities and unit variety beyond the three classes** — no stim, blink, medivacs, healing,
  cloaking, splash damage, air units, or per-unit upgrades. One weapon per class, one number each.
- **Enemy difficulty levels.** SMAC's built-in AI has a difficulty ladder; this ships one script, and it
  is published in `docs/RULES.md` so a prompt can be written against it.
- **Fog of war and vision advantages.** Full observability is decided in §Decisions; terrain height,
  detectors and vision radii are not modelled.
- **Macro**: no production, no resources, no bases, no unit counts changing mid-battle. This is micro at
  tick rate — the idea's own framing of what separates it from ProxyWar.
- **Friendly fire, respawns, healing, hit-point regeneration, and more than one life.** A unit that dies
  is out; anything that softens that changes what focus fire is worth.
- **Raw per-tick actuator control by an external policy.** The v1 control channel is the directive plus
  the server-side control layer. The recorded per-cog mask log is already the right shape for a v0.2
  protocol addition.
- **More than three battles per episode, or state carried across episodes.** The wall-clock budget in
  §Decisions sizes the episode at three.
- **Procedural terrain** — the generator, the curated pool, `mapkit`, the map editor and the pool-review
  page. This game pins the hand-tuned arena; a moving board would make the spawn columns, the range
  constants and the viewer's fixed-frame zoom decision all variable for no gain in v1.
- **Achievements.** The starter's win-gated achievement catalog and its `results.achievements` key are
  dropped; the results document carries damage, kill, death and shot counters instead.
- **Player debug-sprite overlays** (ctf's `0x86` channel), **inter-seat chat outside the 10-rune in-game
  shout**, **persistent memory across episodes**, and any tournament structure beyond the platform league.
- **Audio, 3D, camera cuts, and any downloaded art asset.**
