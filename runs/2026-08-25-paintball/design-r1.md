# cogame-paintball — design note (2026-08-25, paintbot lineage)

`Metta-AI/cogame-paintball` is a two-squad paintball **King of the Hill** coworld, forked from
**`Metta-AI/coworld-ctf`** (paintbot), read at its read-only mount `/workspace/starters/coworld-ctf`.
**Every convention there holds here unless this note says otherwise** — the 24 Hz tick loop, the
Sprite v1 button-mask input, the continuous movement and per-pixel wall/LoS masks, the fog of war,
the spray-can cone, the shout channel, the `COWLDxxx` replay codec with its per-tick `gameHash`
chain, the mummy server and its `COGAME_*` runtime contract, the broadcast chrome
(`client/replay_broadcast.html` + `client/chrome_common.js` + `client/broadcast_core.js`), the
emscripten static replay bundle (`replay-viewer/`, `Dockerfile.replay-viewer`,
`tools/build_replay_viewer.sh`) and the `GameVersion` changelog discipline are all inherited. The
starter is chosen by game shape: paintball is **a real-time game loop with rules written for this
coworld**, which is the paintbot row of the starter table, and this coworld is literally an
extension of that engine — the three mechanics below are new rules bolted onto the arena the
starter already ships, so every line of the loop/replay/viewer machinery is reused rather than
rewritten.

**Source idea, verbatim:**

> EXTENSION of Metta-AI/coworld-ctf (the live paintbot league: CTF, 4ffa, KotH-like modes already exist). Only Melting Pot mechanics we lack are in scope:
>     Floor paint as buff: standing on your team's colour gives speed/health bonus — makes painting tactical, not just score.
>     King of the Hill per Melting Pot: one central hill, owned when ≥80% of its tiles are your colour; continuous reward while held.
>     Resident/visitor scoring: evaluate a submitted policy both as majority and as a lone visitor among scripted teammates (ad-hoc teamwork), not just as a full team.
>
> Ship as config-gated variants inside coworld-ctf (same pattern as 4ffa and trenches).
>
> Source: meltingpot paintball__capture_the_flag, paintball__king_of_the_hill (https://youtu.be/ECzevYpi1dM , https://youtu.be/VVAfeObAZzI); github.com/Metta-AI/coworld-ctf.

**Repo shape.** The deliverable is the new public repo `Metta-AI/cogame-paintball`, forked from the
coworld-ctf starter (SPEC §Design pins). The idea's "ship as config-gated variants inside
coworld-ctf (same pattern as 4ffa and trenches)" is honoured *inside that fork*: every new mechanic
is a config gate that is **off by default** (`floorPaint`, `paintBuff`, `hill`, `loadout`,
`regimes`), exactly the way the starter gates `teams: 4`, `mapPits`, `mapPuddles`,
`barrierPickups` and `barrageMaxPerSec`, and the manifest ships them as named variants. A
gate-off config plays the starter's rules unchanged, which is what keeps the ctf tests that survive
the fork meaningful.

### Design pins (`playbooks/make-coworld.md` §Phase 0 / SPEC §"Design pins every coworld inherits")

| Pin | How paintball satisfies it |
|---|---|
| Starter by game shape | **`coworld-ctf` (paintbot)** — a real-time game loop with new rules; the idea is an extension of this very engine. (§The game, §Sim module) |
| Public `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-paintball`, **public at creation** (`source-resolves` 404s on private). (§Packaging) |
| LLM policy **and** scripted baseline day one, same image, env-switched | `PLAYER_PROMPT` (both champions) vs `PLAYER_SCRIPTED=holdline` / `PLAYER_SCRIPTED=sprayer` (both fillers); one image `coworld-paintball`, player entrypoint `/bin/paintball-player`. (§Decisions, §Packaging) |
| Static wasm replay viewer, never a pod | `"replay_viewer": {"bundle": "static-replay-viewer"}`; ctf's `tools/build_replay_viewer.sh` and `Dockerfile.replay-viewer` kept; the **same Nim sim module** compiles into `replay-viewer/paintball_replay.nim` under emscripten and re-simulates in the browser. (§Viewer) |
| Real art, starter chrome verbatim | ctf's `client/chrome_common.js` byte-for-byte, `client/broadcast_core.js` byte-for-byte, `client/replay_broadcast.html` = the starter's page **with one appended game block**; cogs are the shipped `data/soldier_*`/`data/rig_real/*` art; floor paint is baked with pixie from the starter's own stain compositor. No placeholders. (§Viewer) |
| Two name spaces | Prompts, in-game labels and shouts carry only `RED`/`BLUE` and `RED-alpha…delta`; real policy names appear only in the replay config JSON, `roster[].name`, `teams.<color>.policies`, the DOM scorebug/endcard and `results.names`. Test-enforced (`tests/test_identity_privacy.nim`, extended). (§Server, §Viewer, §Tests) |
| Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds` 1200 | expected 260 s / worst case 580 s against a 720 s budget; a 690 s engine stop; every wait bounded. Arithmetic spelled out in §Decisions. |
| `num_agents` in every variant and the cert fixture | **`num_agents` = 2** in variants `default`, `koth-resident`, `koth-visitor`, `koth-nobuff` **and** in `certification.game_config`; `<SEATS>` = 2 in `tools/ci/docker_smoke.sh`. (§Packaging) |

---

## The game

**Paintball KotH is two four-cog squads fighting over one central hill by painting the floor.**
Every cog carries a paint sprayer; the cone tags enemies *and* repaints the floor tiles it covers.
Standing on your own colour makes you faster and heals you. The team whose colour covers **≥ 80 %**
of the hill's floor tiles **owns** the hill and banks one point per tick for as long as it holds it.
An episode is played **twice** — once with each seat commanding its whole squad (**resident**), once
with each seat commanding a single cog beside three scripted teammates (**visitor**) — and the two
halves are averaged into the episode score.

### Seats, cogs, aliases

**`num_agents` = 2. One seat = one squad commander.** Seat 0 commands **RED**, seat 1 commands
**BLUE**. Each team fields **`cogsPerTeam` = 4** cogs, named with the starter's own per-team
identities (`roster.nim` `IdentityNames`): `RED-alpha`, `RED-beta`, `RED-gamma`, `RED-delta` and the
same for BLUE. Eight cogs, two websocket seats.

Two seats, not eight, because: (a) the resident/visitor mechanic *requires the game to decide* which
cogs are policy-driven and which are scripted — impossible if the platform's ladder owns the seat
assignment; (b) both champions are LLM prompt policies and a 2-seat game puts them head-to-head in
every episode; (c) two seats means **two** parallel LLM calls per turn, which is what makes the
720 s budget comfortable; (d) the starter already ships a 2-seat variant (`ctf-1v1`,
`num_agents: 2`), so nothing in the manifest or the ladder is surprised by it. Splitting 2
*connections* over 8 *cogs* is the same shape cogball shipped on this lineage, and costs the two
named edits to `roster.nim`/`replays.nim` in §Sim module.

`num_agents` is **2** everywhere: every manifest variant, the certification fixture and
`SMOKE_SEATS`.

### Map, tick, clock

`mapPath: "arena"` in every variant — the starter's hand-tuned symmetric arena, **1235 × 659** map
pixels, fixed geometry, pinned into the replay's config as usual. No procedural terrain: a fixed
board makes the hill's tile set, the paint grid and the viewer's zoom decision all constant, and
the arena's own `isProtectedFloor` guarantees an open disc of radius `flagRing` = 70 px at the map
centre — the hill needs exactly that.

`TargetFps = ReplayFps = 24`, **kept verbatim** (every speed-coupled layer — `PlaybackSpeeds`, the
lull scan, `tickTime`, the transport bar — is keyed to it).

One **game** is `maxTicks` = **2160** ticks = **90 s**. One **episode** is `maxGames` = **2** games:
game 0 plays regime `regimes[0]` = `resident`, game 1 plays `regimes[1]` = `visitor`. The map, the
seed and the connected seats are identical across the two games; the sim RNG stream simply continues
(no re-seed), and the paint grid, hill counters and cog state reset with `resetToLobby()` between
games. No side swap is needed: the arena is mirror-symmetric, so RED and BLUE start from equivalent
terrain.

Decision turns: `turnTicks` = **108** ticks = **4.5 s** → **20 turns per game, 40 per episode**.

### Loadout (config gate `loadout: "paintball"`; default `"ctf"` is the starter's)

Under `loadout: "paintball"`:

1. Every cog spawns and respawns holding a **spray can** (`hasSprayPaint = true`) and never loses
   it — on death, on respawn, ever. There are no spray-can pickups on the map.
2. The **gun is disabled** — that is already the starter's rule for a can carrier
   (`docs/RULES.md` §Spray can: "the gun is disabled while the can is held"), so no new code.
   `resolveSimultaneousFire` therefore never fires in a paintball game.
3. **No pickups are placed at all**: grenades, med kits, shields, spray cans and cardboard barriers
   are skipped in `resetGrenades`/`resetMedKits`/`resetShields`/`resetSprayPaints`/`resetBarriers`.
   `barrageMaxPerSec: 0` (no grenade barrage), `mapPits: 0`, `mapPuddles: 0`.
4. There is **no heart / flag objective**: `hill: true` replaces the capture win condition (below).
   Hearts are not placed and not drawn.

Cone numbers are the starter's, unchanged: reach **170 px** (5 cog bodies) along the centreline,
widening to **85 px** at the tip (half-angle atan(1/4) ≈ 14°), victims tested as **17 px discs**,
cone **active 5 ticks** holding the aim it was fired at, **20 ticks** to repressurize (one burst per
25 ticks), line of sight required, friendly fire on.

One number changes: **`sprayDamage` (new config field, default 3 = the starter's
`SprayPaintDamage`) is `1` in every paintball variant.** A cog has `hitPoints: 3`, so a cog is
**tagged out by three touches**, not one. That is what makes the heal half of the paint buff
meaningful and what keeps a 90 s game from being decided by one ambush.

Tag-out: hp 0 → the cog is out for `respawnTicks` = **48** ticks (2 s), then respawns at a random
spot in its own endzone at full hp with the can still in hand. `lives: 12` per cog — high enough
that a wipe is a genuine collapse rather than the normal ending, low enough that the wipe end
condition below is not dead code.

### Mechanic 1 — the paint grid and the floor-paint buff

**The paint grid.** The map is divided into square **paint tiles of `PaintTile` = 34 px** — one cog
body. On the 1235 × 659 arena that is `gw` = 37 by `gh` = 20 = **740 tiles**. Three pieces of state,
all in `gameHash`:

- `paintOwner: seq[uint8]` (length `gw*gh`): `0` = unpainted, `1` = RED, `2` = BLUE.
- `paintFloor: seq[bool]`: whether the tile is **paintable** — computed **once at map install**, as
  "the tile's centre pixel is not a wall with the spinning diamonds at spin frame 0". Computing it
  once (rather than per tick against the live, rotating wall mask) is what keeps it deterministic
  and identical between the native server and the wasm viewer, which both install the same
  `mapSpec`.
- `paintCount: array[Team, int]` — painted tile counts, maintained incrementally on every flip.

**Painting.** A tile flips to the sprayer's team colour when it is covered by an active cone: on
**every active cone tick**, for every paintable tile whose **centre** lies inside the cone shape
(the same integer cone predicate `resolveActiveArcCones` applies to bodies, evaluated with body
radius 0), `paintOwner[tile] = team`. A burst therefore lays roughly 8 tiles. Nothing else paints
the floor under `loadout: "paintball"` (there is no gun, no grenade, no barrage). Under
`loadout: "ctf"` with `floorPaint: true`, a gun shot's terrain impact tile and a grenade blast's
covered tiles flip as well — that path exists so the gate composes, and is not used by any shipped
variant.

Wall paint is unchanged: the starter's cosmetic `addPaintStain(..., onWall = true)` still marks
walls, and remains **excluded from `gameHash`**. The *floor* decals the starter used to draw from
`sim.paintStains` are replaced by the grid (§Viewer).

**The buff** (config gate `paintBuff: true`; requires `floorPaint`). Once per tick, in
`updatePaintBuff()`, each living cog reads the tile under its **body centre** — the same
"you are in it exactly while your centre is inside" convention trenches and puddles use — and
records `paintUnder ∈ {none, own, enemy}`:

| Under your feet | Max speed & acceleration | Health |
|---|---|---|
| **your own team's colour** | **×125 %** (`paintSpeedOwnPct` = 125) | after **48 consecutive ticks (2.0 s)** on own colour: **+1 hp**, capped at the cog's `maxHpFor`, counter resets to 0 |
| unpainted | ×100 % | — |
| **the enemy's colour** | **×85 %** (`paintSpeedEnemyPct` = 85) | — |

The speed multiplier is applied in `applyInput`, composed **multiplicatively after** the existing
carrier scale and **before** the trench divisor, in exactly this integer order so both ends of the
map round identically:

```
maxSpeed = ((config.maxSpeedFor(team, perks) * speedScale) div 100 * paintPct) div 100
accel    = ((config.accel                    * speedScale) div 100 * paintPct) div 100
```

With the stock `MaxSpeed` = 704 and `speedScale` = 100 (nothing is carried in paintball): own paint
880, unpainted 704, enemy paint 598 motion units — a ~47 % swing between a cog on its own lane and
one wading through the enemy's. The heal counter `ownPaintTicks` is reset to 0 by: stepping off own
paint for even one tick, taking any damage, dying, and the start of each game. Each heal emits the
starter's existing `Heal` sim event with `amount: 1`, which the feed renders.

Both halves read the **same** `paintUnder` snapshot: `updatePaintBuff` runs at the end of tick *t*
and the speed multiplier is consumed by `applyInput` on tick *t+1*, so there is exactly one
evaluation of "what am I standing on" per tick.

### Mechanic 2 — King of the Hill

**Where.** One hill, at the **map centre**. Its tile set is the **5 × 5 block of paint tiles centred
on the tile containing `(width div 2, height div 2)`** — on the arena, centre pixel (617, 329),
centre tile (18, 9), so the hill is tiles x ∈ 16..20, y ∈ 7..11, i.e. the **170 × 170 px** square
spanning pixels x 544..713, y 238..407. `hillRadiusTiles` = 2 is a config field; 2 is chosen because
5 × 5 tiles is the largest square that stays inside the arena's open centre without swallowing the
column-5 diamonds whole, and it is big enough that a single burst (~8 tiles) cannot flip it alone.

**Which tiles count.** `hillFloorTiles` = the number of hill tiles that are **paintable**
(`paintFloor`), computed once at map install with the hill's tile list. Wall tiles inside the
square (the arena's diamonds at (565, 252) and its symmetric images clip two corners) are excluded
from **both** numerator and denominator, so "80 % of the hill" always means 80 % of the floor a cog
can actually stand on. The hill square is centred on the map's symmetry centre, so its floor set is
its own image under the arena's mirror symmetry — team-fair by construction. A test asserts
`hillFloorTiles ≥ 15` and that the tile set is symmetric about the midline for every shipped
variant.

**Ownership.** Maintained incrementally as `hillPaint: array[Team, int]` (updated on every hill-tile
flip). At each tick:

```
owns(T)  ==  hillPaint[T] * 1000 >= hillFloorTiles * hillOwnPermille        # hillOwnPermille = 800
```

Because 800 > 500 at most one team can qualify; `hillOwner` is that team or `none`. **Continuous
reward while held:** every tick a team owns the hill, `hillTicks[T] += 1` — **1 hill point per
owned tick, i.e. 24 points per second**. The scorebug shows `hillTicks div 24` as **M:SS held**;
the results document reports both raw ticks and seconds.

An ownership change emits a `hillflip` sim event (throttled to at most one per 12 ticks so a
contested rim cannot flood the feed), which is a scrubber beat and a feed line
("**RED TAKES THE HILL — 84 %**").

### Mechanic 3 — resident / visitor

Each game of the episode runs a **regime**, `regimes[gameIndex]`:

- **`resident`** — every cog of a team is driven by that team's seat. The seat's directive names all
  four cogs; the seat is the *majority* — the whole squad is its policy.
- **`visitor`** — only `alpha` of each team is driven by that team's seat. `beta`, `gamma` and
  `delta` are driven by the **`holdline` scripted baseline**, compiled by the identical control
  layer. The seat is a *lone visitor among scripted teammates*: it cannot instruct them, cannot see
  their intentions, and must fit itself around what they do. Both seats are visitors in the same
  game, so the comparison stays symmetric.

The scripted partners in `visitor` are always `holdline` — a fixed, published baseline documented in
`docs/RULES.md`, so ad-hoc teamwork here means "adapt to a partner you know the rules of but do not
control", which is the Melting Pot construction, not "guess a mystery partner".

**How it composes into the league score.** Per game *g* and seat *s* (team `T(s)`, opponent `O(s)`):

```
gameScore(g, s) = 0.5 + 0.5 * clamp( (hillTicks[T] - hillTicks[O]) / hillDecisiveTicks, -1, +1 )
                                                       # hillDecisiveTicks = 720  (30 s of margin)

score(s)        = 0.5 * gameScore(resident, s) + 0.5 * gameScore(visitor, s)
win(s)          = score(s) > 0.5
```

**Higher is better**, every score lies in [0, 1], and `score(0) + score(1) == 1.0` exactly for every
legal outcome (both halves are individually zero-sum). A 30-second hold advantage in a game is a
1.000; a dead-even game is 0.500. **The league ranks by Elo computed from `results.scores`** (the
platform's only cross-game ranking input; Elo 1000 start, K 32, per the phase-50 league settings).
Because the episode score is the *mean* of the two halves, a policy that only works with clones of
itself ranks below one that also works beside strangers — which is exactly what the idea asks the
leaderboard to measure. `results` additionally reports `residentScore`, `visitorScore`,
`residentHillTicks` and `visitorHillTicks` per seat, so the two halves are separable in analysis
and on the endcard without changing what Elo consumes.

A `fault` episode scores 0.5 / 0.5 — an infra fault is nobody's loss.

### Resolution order (exact, every tick `t`, no exceptions)

Steps 1–5 are the server's frame; steps 6.x are `sim.step`, which is ctf's step body with the
paintball insertions called out. Anything not named here is the starter's code, unchanged and in
its original position.

1. **Turn boundary.** If `sim.gameTicksElapsed() mod turnTicks == 0` and `phase == Playing`, the
   directives collected for turn `k = gameTicksElapsed() div turnTicks` (issued by the decision
   layer *before* this tick is stepped — §Decisions) become each seat's active directive, and one
   `directive` record per seat is written to the replay chat stream. `sim.activeDirective[seat]` is
   **excluded from `gameHash`** (the starter's rule for `damagePops`/`skin`/`puddleTicks`): nothing
   a commander says can move the hash chain.
2. **Control compile.** For each cog in index order (`RED-alpha, RED-beta, RED-gamma, RED-delta,
   BLUE-alpha, …`), `control.compileMask(sim, directive, cogIndex)` emits one `uint8` Sprite v1
   input mask. The governing directive is the seat's active directive when the cog is *commanded*
   under this game's regime, and otherwise the `holdline` scripted directive computed by the same
   code from the same state.
3. **Record.** The eight masks go to `sim.step(inputs, prevInputs)` and to
   `replayWriter.writeInputMaskChange` (ctf's function, unchanged), indexed by **cog**. **This is
   the determinism boundary.** The control layer and the LLM are outside it: the viewer never runs
   either, it feeds the recorded masks to the identical sim.
4. `inc sim.tickCount`; `updateAnimatedDiamonds()` — verbatim, so movement, cones and vision all
   resolve against the geometry this tick draws.
5. Roster-driven transitions (`players.len == 0` → abort/reset) — verbatim.
6. **Playing:**
   1. Per cog, in index order: decrement `fireCooldown` / `fireWindup`; `applyInput` (movement and
      aim rotation, now reading `paintUnder` for the speed multiplier); `applyGrenadeInput` and
      `applyBarrierInput` are no-ops under the paintball loadout; a fresh **A** press with the can
      ready queues an arc fire.
   2. `resolveSimultaneousFire(firing)` — never populated under the paintball loadout (no gun).
   3. `startArcFire` for each queued cog, then `resolveActiveArcCones()` — cone **damage**
      (`sprayDamage` per victim per burst, line of sight required, friendly fire on), unchanged
      except for the configurable damage amount.
   4. **NEW `paintFloorFromCones()`.** For every cone active this tick, in cog index order: every
      paintable tile whose centre is inside the cone flips to the sprayer's team;
      `paintCount`/`hillPaint` are updated on each flip; one `paint` sim event per cone per tick
      carries `{tiles, hillTiles}`.
   5. Pickup and item updates (`updateGrenades`, `updateMedKits`, `updateShields`,
      `updateSprayPaints`, `updateBarriers`, `tryPickup*`, `updateFlags`) — skipped entirely under
      the paintball loadout, because nothing is placed.
   6. `respawnPlayers()` — verbatim; a respawn restores hp, keeps the can, and clears
      `ownPaintTicks`.
   7. `updatePackTicks()` — verbatim, analysis only.
   8. `updatePuddles()` / `updateBarrage()` — inert (`mapPuddles: 0`, `barrageMaxPerSec: 0`).
   9. **NEW `updatePaintBuff()`.** Per living cog: set `paintUnder` from the tile under its centre;
      if `own`, `inc ownPaintTicks` and at `ownPaintTicks == paintHealTicks` (48) heal 1 hp (capped
      at `maxHpFor`), emit `Heal`, reset the counter to 0; otherwise `ownPaintTicks = 0`.
   10. **NEW `updateHill()`.** Recompute `hillOwner` from `hillPaint` vs `hillFloorTiles`; if it
       changed and ≥ 12 ticks have passed since the last flip event, emit `hillflip` and log it;
       if a team owns the hill, `inc hillTicks[owner]`.
   11. **NEW `checkKothEnd()`** — replaces `checkWinCondition()` + `checkMaxTicks()` while
       `hill: true`, evaluated in this order:
       1. If a team has no cog that is alive or has lives left, credit the **surviving** team with
          every remaining tick (`hillTicks[survivor] += maxTicks - gameTicksElapsed()`) and
          `finishGame(survivor, endRule = wipe)`. Crediting the remainder is what stops a wipe from
          being worth less than playing the clock out.
       2. Else if `abs(hillTicks[Red] - hillTicks[Blue]) > maxTicks - gameTicksElapsed()`, the
          result cannot change: `finishGame(leader, endRule = mercy)`.
       3. Else if `gameTicksElapsed() >= maxTicks`, `finishGame(leader, endRule = full_time)` —
          a draw (`isDraw = true`) when the hill ticks are equal.
   12. FX pruning and shout expiry — verbatim (`recentShots`, `hitFlashes`, `bubbleImpacts`,
       `recentBlasts`, `sprayPaintFlashes` cosmetic; `recentShouts` and `splatters` as in the
       starter).
7. `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` — the starter's per-tick hash
   chain. `gameHash` gains, appended after the existing mixes so the ordering stays stable:
   `paintOwner` (mixed eight bytes at a time as `uint64` words), `hillPaint[]`, `hillTicks[]`,
   `ord(hillOwner)`, and per cog `ownPaintTicks` and `ord(paintUnder)`.
8. **Game end.** When `phase` becomes `GameOver` the server increments `gamesPlayed` (its existing
   line). If `gamesPlayed < maxGames`, `hillTicks` are archived into `gameHill[gameIndex]`,
   `resetToLobby()` clears the paint grid, hill counters and cog state, and the next game starts
   under `regimes[gamesPlayed]`. If `gamesPlayed >= maxGames`, the episode ends and the artifacts
   are written.

### End conditions and legal `results.reason` values

`results.reason` is a closed enum of exactly three values; `results.endRule` carries the detail of
the **last** game played.

| `reason` | `endRule` | When |
|---|---|---|
| `complete` | `full_time` | both games played their 2160 ticks. The normal ending. |
| `complete` | `mercy` | the final game's hill lead exceeded the ticks remaining. The rules ended it; still a complete episode. |
| `complete` | `wipe` | the final game ended with a team out of lives (survivor credited the remainder). |
| `deadline` | `wall_clock` | `wallClockBudgetSeconds` (default **690**) elapsed before the second game finished. Games already completed keep their scores; the game in progress is scored from its hill counts at that instant; the replay is complete up to the stop tick and the game-over frame is written. **This is declared acceptable for phase-60 verification** (SPEC §Definition of done check 4): it means the hosted LLM was slow, not that the game broke. |
| `fault` | `sim_fault` | a sim invariant guard tripped (a cog outside the map, a paint index out of range, `hillPaint > hillFloorTiles`). Scores 0.5 / 0.5, `win` both false, partial replay written. |
| `fault` | `host_error` | an unexpected server-side exception. Same treatment; best-effort artifacts written before re-raising. |

A seat that never connects does **not** end the episode: `lobbyJoinTimeoutTicks` (2400 ticks =
100 s of lobby wall clock) expires, the no-show is reported to `COGAME_PLAYER_FAILURE_URI` via
ctf's `declarePlayerFailure` (lowest missing slot only), its squad is driven by `holdline` for the
whole episode, and both games play to `full_time`.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched
by env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat; `PLAYER_SCRIPTED=<name>` with
`name ∈ {holdline, sprayer}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=holdline`. A scripted policy seated as a champion is a failure state.

### Where the decision happens

coworld-ctf has **no LLM client** (its "campaign strategist" is a platform-side feature shipping
with the `coworld` package in Metta-AI/metta, not in this repo — README §Campaign mode). Paintball
therefore ports **`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim`** into the ctf-lineage
server as `src/paintball/llm.nim`, ported verbatim in behaviour:

- Credentials, in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (read with `readCogameUri`) → **none** (client
  `disabled = true`, every turn falls back instantly with no network wait, so offline certification
  completes in seconds).
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; `tryNextBedrockModel` on 401/403 "Model access is
  denied" and on 429. `us.anthropic.claude-sonnet-4-6` is deliberately **not** a candidate (it times
  out on every sidecar call — raid round 2, 2026-08-23).
- `max_tokens = 900` (400 truncates). **No `output_config.effort`** when the model string contains
  `haiku` or `4-5`. Bedrock bodies carry `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (first `{` … last
  `}`, fence-tolerant) and rune-boundary truncation (`runeLen`/`runeSubStr`) ported unchanged.

The decision happens in the **game server**, not the player container: the `anthropic_api_key`
coworld secret is injected into the *game* pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/paintball/anthropic_api_key` — the hive
gotcha), phase 60 greps the *game* log for `falling back` / `LLM provider is unavailable`,
`docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only, and keeping the control
layer server-side is what makes the recorded mask log reproducible with no network in the loop.

### Cadence, batching, and the wall-clock arithmetic

One decision turn every **108 ticks (4.5 s of sim time)**, **20 turns per game, 40 per episode**. At
each turn the server builds both seats' request bodies and issues them as **one parallel batch** —
`client.curl.makeRequests(batch, timeout)`, the exact shape of bullwhip's `decideAll`. Seats are
**never** queried sequentially. One call per seat per turn covers all of that seat's commanded cogs,
so an episode is 2 × 40 = **80 calls**, at most 2 in flight.

Per-turn timing: attempt 1 batch deadline **4.5 s**. Any seat that timed out, errored, returned
non-JSON or returned no usable cog entry is retried **once**, again as a single batch, with a
**2.0 s** deadline. Worst case 6.5 s ≤ the **7.0 s** `turnBudgetMs = 7000` cap enforced by a
monotonic deadline around the whole turn.

**Rate floor.** The Bedrock sidecar caps **30 requests/minute per episode** (raid, 2026-08-23), and
2 seats per turn at a fast turn would sit right on it. A **`turnSpacingMs` = 5000** wall-clock floor
between the *starts* of consecutive batches holds the episode at ≤ 24 req/min. It is a floor, not a
sleep on the critical path: the loop keeps stepping sim ticks while it waits.

```
40 turns x 5.0 s spacing floor (typical; 7.0 s cap)          = 200 s   (cap: 280 s)
lobby / connect wait (typical 15 s; cap 2400 ticks = 100 s)  =  15 s   (cap: 100 s)
2 x 2160 ticks of play, fastMode, seats report ready         =  25 s   (wall-paced worst: 180 s)
game-over holds + results + replay write (retrying uploader) =  20 s
                                                             -------
expected total                                               = 260 s   < 720 s
absolute worst case (100 + 280 + 180 + 20)                   = 580 s   < 690 s stop
engine hard stop wallClockBudgetSeconds                      = 690 s   -> reason "deadline"
platform kill (episodeTimeoutSeconds)                        = 1200 s
```

720 s is 60 % of the assumed 1200 s `episodeTimeoutSeconds`; every shipped variant's
`wallClockBudgetSeconds` is ≤ 690 and a manifest test asserts it.

`fastMode: true` in every variant. ctf's `docs/PROTOCOL.md` warns that the Sprite v1 Ready packet
(`0x85`) corrupts input timing on a wall-clock-paced server — that warning is about *player* clients
whose own inputs are dead-reckoned. Paintball's seats send no inputs at all (the server computes
every mask), so the hazard does not exist here and the player harness sends `0x85` after every
received frame.

**Budget guard (early settle without shortening the episode).** At the start of each turn, if
`elapsed + 2 * turnBudget > wallClockBudgetSeconds`, the LLM is switched off for every remaining
turn and the episode finishes on the scripted layer (microseconds per turn), so it ends
`complete/full_time` rather than `deadline`. A `budget_guard` record names the turn it fired.

**Degrade, never hang.** Every wait is bounded: the two batch deadlines, the outer per-turn
deadline, `lobbyJoinTimeoutTicks` on the connect wait, mummy's socket timeouts on the serve thread
(which runs independently of the game loop, so a 7 s LLM stall cannot drop a connection), the 690 s
engine stop, and ctf's `gameOverTicks` hold before exit. On a seat's **timeout or parse failure**:
retry once in the next batch; on the second failure the seat's directive for that turn becomes the
**`holdline`** scripted directive and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, no_credentials, budget_guard}`. A seat that
disconnects mid-episode keeps playing: its directive source degrades to `holdline` and it revives on
reconnect. **No failure mode leaves a cog unactuated** — the control layer always has a directive,
defaulting to the previous turn's, then to `holdline`.

### The per-seat view given to the LLM

Built server-side from the seat's fog (§Server), numbers in **map pixels**, rounded to integers.
This object is the tail of the user message and is mirrored (minus the map arrays) into the
`directive` record.

```json
{"game": 1, "of": 2, "regime": "resident",
 "turn": 7, "turns": 20, "clock": {"played_s": 31, "left_s": 59},
 "you": {"team": "RED", "commanding": ["RED-alpha","RED-beta","RED-gamma","RED-delta"]},
 "hill": {"box": [544, 238, 713, 407], "centre": [617, 329], "floor_tiles": 21,
          "yours_pct": 52, "theirs_pct": 33, "neutral_pct": 15,
          "owner": "none", "need_pct": 80,
          "held_s": {"you": 12, "them": 19}},
 "score": {"you": 0.46, "them": 0.54, "resident_done": null},
 "map": {"w": 1235, "h": 659, "tile": 34},
 "your_cogs": [{"id": "RED-alpha", "pos": [601, 342], "aim": 8, "hp": 3, "lives": 11,
                "alive": true, "standing_on": "own", "spray_ready": true,
                "dist_to_hill": 20, "last_intent": "hold_hill"}, "… 4 …"],
 "seen_enemies": [{"id": "BLUE-beta", "pos": [702, 300], "hp": 2, "ticks_ago": 0}, "…"],
 "your_paint_near_hill": 11, "their_paint_near_hill": 7,
 "teammates_not_yours": [{"id": "RED-beta", "pos": [520, 400], "alive": true}],
 "last_turn": {"tags_dealt": 2, "tags_taken": 1, "hill_flips": 1,
               "tiles_painted": 34, "your_hold_s": 3},
 "your_last_directive": "… the directive your seat played last turn, or null on turn 0 …"}
```

`teammates_not_yours` is present only in `visitor` games (the three scripted cogs, reported exactly
as any other visible ally: position and alive flag, no intent). `resident_done` carries the
resident game's final `gameScore` for this seat while playing game 2, and is `null` in game 1.

### Reply schema and per-field caps

The LLM must return this object; the scripted baselines produce the identical shape, so the two
policy kinds are strictly comparable and the same validator runs on both.

```json
{"note": "flood the west rim, beta screens",
 "cogs": [{"id": "RED-alpha", "intent": "hold_hill", "target": [617, 329],
           "face": [700, 300], "say": "on hill"}, "… one per commanded cog …"]}
```

| Field | Type | Cap / legal values | Repair when violated |
|---|---|---|---|
| `note` | string | **≤ 160 runes** | truncated to 160 runes on a rune boundary |
| `cogs` | array | exactly the seat's **commanded** cogs (4 in `resident`, 1 in `visitor`) | extra entries dropped; a missing cog keeps last turn's directive, else `holdline`'s |
| `cogs[].id` | string | one of the seat's commanded ids, case-insensitive, **≤ 12 runes** | unmatched entries assigned to the seat's commanded cogs by position |
| `cogs[].intent` | enum | `paint_hill` `hold_hill` `hunt` `guard` `paint_path` `fall_back` | → `paint_hill` |
| `cogs[].target` | [int, int] | finite; clamped to the map box `[0, w-1] × [0, h-1]` and snapped to the nearest walkable pixel | missing / non-finite → the hill centre |
| `cogs[].face` | [int, int] \| null | finite; same clamp | → `null` (the control layer picks the aim, §below) |
| `cogs[].say` | string | **≤ 10 runes** — it becomes a real in-game **shout** (`ShoutMaxChars` = 10), audible to *both* teams within `ShoutRange` = 247 px, one per cog per second | truncated to 10 runes, then the starter's `sanitizeShout` (printable ASCII, trimmed) |

Three further caps on strings that reach the replay: `register.policy` **≤ 48 runes**, any recorded
error text (`fallback.detail`) **≤ 200 runes**, and the whole serialized `directive` record
**≤ 900 runes** (asserted in `tests/test_replay.nim`). `register.prompt` is capped at
**≤ 4000 runes** at the transport (over-long is truncated, never rejected) and is **never** written
to the replay or the results.

**Truncation is on rune (Unicode codepoint) boundaries, never bytes.** In Nim that means
`runeLen`/`runeSubStr`; slicing a `string` by byte index on any path to the replay is forbidden. A
byte-truncated multi-byte character is exactly the bug that makes replay bytes render in a browser
but fail a strict parser, and §Tests pins it with a 4-byte emoji sitting on the boundary.

**Parsing is tolerant:** strip markdown fences; take the outermost balanced `{…}` if the model
prefixed prose; accept `cogs` as an object keyed by id; accept numeric strings for `target`/`face`;
accept an unknown-case intent by lowercasing. Only when no object with at least one usable cog entry
can be recovered do the retry and then the fallback fire.

### System prompt (fixed, identical for both champions, sent as the system message)

```
You command a squad of paintball robots in a top-down arena, 1235 by 659 pixels.
Every 4.5 seconds you issue ONE directive for the cogs you command. A deterministic
controller executes it for the next 4.5 seconds: it walks each cog toward its target
around walls, turns it to face what you told it to face, and fires the paint sprayer
when the shot is worth taking. You never control motors or the trigger directly.
The game is KING OF THE HILL. One hill sits at the centre of the map. Your team OWNS
it while at least 80% of the hill's floor tiles are your colour, and you bank points
every tick you own it. The team with more banked hill time wins.
Paint is also a buff: standing on YOUR colour makes a cog 25% faster and heals one hit
point every 2 seconds; standing on THEIR colour makes it 15% slower. Painting the lane
you attack down is not decoration, it is your speed.
A sprayed cog loses 1 of its 3 hit points; three touches tag it out for 2 seconds.
You cannot see the whole map: enemies appear only inside your cogs' vision cones and
their small bubbles, and the report tells you how many ticks ago each one was seen.
Reply with a single JSON object and NOTHING else. Your reply MUST begin with '{'.
Schema:
{"note":"<=160 chars","cogs":[
  {"id":"<one of the cogs you command>",
   "intent":"paint_hill|hold_hill|hunt|guard|paint_path|fall_back",
   "target":[x,y],
   "face":[x,y] or null,
   "say":"<=10 chars"} , ... one entry per cog you command ]}
Intents: paint_hill = go to the nearest hill tile that is not yours and paint it;
hold_hill = stay on the hill, keep it yours, spray anyone who steps on it;
hunt = close on the nearest enemy you know about and spray it;
guard = hold `target` and watch the hill; paint_path = paint a lane from where you are
toward `target`; fall_back = walk to `target` without spraying. `face` biases the aim
when nothing is in range. `say` is SHOUTED and the enemy hears it if they are close.
```

**User message** = the seat's `PLAYER_PROMPT` text under a "GUIDANCE FROM YOUR OPERATOR" heading
(bullwhip's `operatorBlock`, ported), then a blank line, then the seat's view JSON. The prompt text
is never echoed into the replay — only `policyKind` and the resulting directive are.

### Champion #1 — `paintball-holdcentre` (owner daveey), `PLAYER_PROMPT`

```
Own the hill and never give it back. Every turn, put at least two cogs on the hill:
the one already closest to the centre gets intent "hold_hill" with target the hill
centre, and the next closest gets "paint_hill" with target the hill tile nearest the
enemy side, because that is the edge they will flip first. Keep exactly one cog on
"guard" at a point about 250 pixels off the hill on YOUR side, facing the hill, so a
flank has to go through somebody. The last cog runs "paint_path" between your guard
point and the hill, so your squad always has a fast own-colour lane to reinforce down.
Switch a cog to "hunt" only when the report shows an enemy within about 250 pixels of
the hill and seen this turn - chasing anything further away loses more hill time than
the tag is worth. If you already own the hill, do not add a third cog to it: spend the
spare cog widening your paint around the rim so their next burst cannot flip you.
If they own the hill, send everyone but the guard at it with "paint_hill" and different
targets on different edges - simultaneous edges is how 80% breaks.
```

### Champion #2 — `paintball-splitpaint` (owner daveey-1, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Win the fight first, then the hill takes itself. Keep two cogs paired: give both
"hunt" with the same target - the enemy seen most recently nearest the hill - because
two sprayers on one cog tag it out in half the time and a tagged cog paints nothing for
two seconds. Give one cog "hold_hill" at the hill centre at all times, so the clock is
never zero for you. Give the last cog "paint_path" with target the enemy's half of the
hill, keeping your own colour under your pair's feet as they push - your pair being
25% faster than the cogs they hunt is the whole plan.
When your hold cog reports it is standing on "enemy" paint, promote it to "paint_hill"
targeting the hill centre and pull one of the pair back to "hold_hill" instead.
When you own the hill and hold more seconds than they do, switch both hunters to
"guard" at points about 300 pixels either side of the hill and just make them come to
you. Use "fall_back" only for a cog on 1 hit point, target your own end of the map, and
only until it heals on your paint.
```

### The control layer (deterministic, shared by every policy)

`src/paintball/control.nim`. Both LLM directives and scripted directives are compiled by the *same*
code, so the two policy kinds are strictly comparable. It is a pure function of
`(sim state, directive, cogIndex) -> uint8`, and it navigates with the starter's own
proven components, lifted out of `players/baseline/baseline.nim` and repointed at the sim's real
wall mask instead of the observation stream: `buildNavGrid` (a 34 px cell grid over `sim.isWall`),
`computeField(goal)` (BFS flow field to a goal cell), `navSteer` (the steering vector along the
field with line-of-sight shortcutting), `nearestOpenCell`, and `bradsOf`/`bradsErr` for the aim.
Flow fields are cached per team and recomputed at most once per 12 ticks per distinct goal cell.

For each cog, each tick:

1. **Goal point `g`** by intent (`H` = hill centre, `t` = directive target):
   - `paint_hill`: the centre of the nearest hill floor tile whose owner is not this cog's team;
     if every hill tile is already ours, the nearest hill tile to `t`.
   - `hold_hill`: the nearest **own-colour** hill tile centre if there is one, else `H`.
   - `hunt`: the last known position of the nearest enemy seen within 72 ticks; if none is known,
     degrade to `paint_hill`.
   - `guard`: `t`.
   - `paint_path`: the nearest tile on the straight line from the cog to `t` whose owner is not this
     cog's team; if the whole line is ours, `t`.
   - `fall_back`: `t`, clamped into the cog's own endzone.
2. **D-pad** = the octant bits of `navSteer(cogPos, g)`. A cog within 20 px of `g` stops moving.
3. **Aim.** The desired brads are, in priority order: the nearest enemy inside the vision cone or
   bubble within 300 px; else `face` when the directive gave one; else `g`'s direction when the
   intent paints (`paint_hill`, `paint_path`, `hold_hill`); else `H`. `B` / `Select` are set to turn
   toward it (`aimTurnRate` = 5 brads/tick), and neither is set when `abs(err) <= 4`.
4. **Trigger.** `A` is set iff the can is ready (`arcTicksLeft == 0` and the repressurize timer is
   0), `abs(aimErr) <= 24` brads, and either (i) an enemy body is within the cone's 170 px reach
   along the aim with line of sight, or (ii) the intent paints and the tile 85 px ahead along the
   aim is a paintable tile **not** owned by this cog's team. `fall_back` never sets `A`.
5. **Never both.** Up+Down and Left+Right are never set together; `C` is never set.

### Scripted baselines

Both emit the *same* directive object on the same 4.5 s cadence, so their output is legal by
construction and directly comparable to an LLM's. Both are pure functions of the world state, which
is what makes the bounded-orders test in §Tests meaningful.

- **`holdline`** — the certification player, the fallback directive, the driver of every scripted
  teammate in a `visitor` game, and the default. Of the cogs it governs: the one nearest the hill
  centre is `hold_hill` at `H`; the next two are `paint_hill`, targeted at the two hill tiles
  furthest from each other that are not this team's colour (or `H` when the hill is fully ours); the
  furthest is `guard` at the midpoint between the team's spawn anchor and `H`. Any governed cog with
  a known enemy within 200 px switches to `hunt` on that enemy. Fixed short `note`/`say`
  ("hold", "paint", "watch").
- **`sprayer`** — the second filler, deliberately weaker and different in shape: every governed cog
  gets `paint_hill` at the nearest non-own hill tile, nobody guards, and `hunt` fires only when an
  enemy is within 120 px. The "everyone paints" baseline; it loses to `holdline` and gives the
  ladder a spread.

---

## Sim module

### What is kept, what changes, by path

**Kept verbatim** (mechanical `ctf` → `paintball` / `CTF_WIRE` → `PAINTBALL_WIRE` rename sweep only;
a CI grep asserts no `ctf_`/`CTF_` identifier survives outside comments and history notes):

| Path | Why it is kept |
|---|---|
| `src/ctf/arena.nim`, `map_art.nim` → `src/paintball/` | the arena geometry, the wall/walk masks, `isProtectedFloor`, the map bake and `mapSpec` round-trip. The hand-tuned `arena` layout is the paintball board; the generator, pool, `mapgen_styles.nim`, `map_pool.nim`, `tools/mapkit.nim`, `tools/map_editor*`, `tools/gen_map_pool.nim` and `docs/pool-review.html` are **deleted** (paintball pins `mapPath: "arena"`). |
| `src/ctf/replays.nim`, `replay_runtime.nim` | the whole replay codec, keyframes, `serializeReplaySim`/`deserializeReplaySim`, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket`. Two named edits below. |
| `src/ctf/server.nim` | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, `runFrameLimiter`, the replay-switch path, the `COGAME_*` contract, `declarePlayerFailure`, the artifact-write block, the `gamesPlayed` loop. Five named edits below. |
| `src/ctf/sim_state.nim` | `gameHash`/`mixHash`, `emitEvent`, logging, the lobby countdown. New fields, same machinery. |
| `src/ctf/roster.nim` | join/auth/rewards/identities/`playerResultsJson`. Two named edits below. |
| `src/ctf/events.nim` | the tier-2 event wire format and the `eventsJsonl` summary-row contract. New `SimEventKind` values only. |
| `src/ctf/broadcast.nim` | `stepEvents`, `buildStateJson`, `rosterJson`, `firstPersonJson`, the lull scan, the beat timeline. Retargeted fields, same structure. |
| `src/ctf/global.nim` | the sprite/object pools, fog-of-war shadowcasting, the soldier/rig compositor, the FX families, the stain compositor (`buildPaintStainSprite`), the first-person raycast. Two named edits below. |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | label vocabulary, the rig art compositor, the one-source JS wire constants. |
| `client/broadcast_core.js`, `client/chrome_common.js`, `client/replay_broadcast.html`, `client/league_replayer.html` | the broadcast chrome (§Viewer). |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js`, `ctf_replay.nim` → `paintball_replay.nim` | the emscripten link flags (`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, the `EXPORTED_FUNCTIONS` list), the OffscreenCanvas Worker, the stage-note diagnostics. One named edit (§Viewer). |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`, `tools/ci/check_gameversion.sh`, `nimby.lock`, `flake.nix` | build, bundle and forensics wiring. |
| `data/` art: `soldier_{red,blue}*`, `rig_real/{red,blue}/*`, `font.ttf`, `atlas/*`, `ascii.png`, `arena_floor.png`, `spraycan*.png`, `client/art/walls/*`, `client/art/lockerroom/{bg.jpg,red_*.webp,blue_*.webp}` | real art, kept. Green/yellow team art, `heart_*`, `paintgun*`, `medkit`, `shield`, `paintbomb`, `ped_*` are deleted with the mechanics they belong to. |

**Deleted** (with their tests, tools and docs): four-team mode, hearts/flags and capture, the gun and
its jitter/exposure model, grenades and the barrage, med kits, shields, cardboard barriers, paint
puddles, trenches, perks, handicaps, the procedural generator and map pool, the map editor, mapkit,
the achievements catalog, and the campaign notes. Deleted, not disabled — every one of them is a
config surface the paintball rules would otherwise have to reason about.

**New modules:** `src/paintball/paint.nim` (the grid, the cone→tile rasteriser, the buff, the hill),
`src/paintball/control.nim` (the control layer), `src/paintball/directives.nim` (the reply schema,
tolerant parse, repair, caps), `src/paintball/baselines.nim` (`holdline`, `sprayer`),
`src/paintball/llm.nim` (ported from bullwhip), `src/paintball/decide.nim` (the turn loop, batching,
deadlines, fallbacks), `src/paintball_player.nim` (the thin player registrar).

### The five named edits to `server.nim`

1. **Input source.** Where ctf reads `appState.inputMasks` (the socket) into `inputs[playerIndex]`,
   paintball calls `control.compileMasks(sim, directives)` and fills `inputs[cogIndex]` for the
   eight cogs. `writeInputMaskChange` is called with the **cog** index. Player sockets no longer
   contribute input.
2. **Turn boundary.** Immediately before stepping a tick where
   `sim.gameTicksElapsed() mod turnTicks == 0`, the loop runs `decide.turn(sim, llm, seats)`, which
   issues the one parallel batch, applies the deadlines and the `turnSpacingMs` floor, installs the
   directives and writes the `directive`/`fallback` records — all inside a monotonic `turnBudgetMs`
   bound.
3. **Registration interception.** A player's Sprite v1 chat message (`0x81`, surfaced by
   `applyPlayerViewerMessage` as `chatText`) whose text parses as a registration object is consumed
   as registration and is **not** applied as a shout and **not** written to the replay chat stream;
   the server writes a redacted `register` record instead (policy label and kind, never the prompt).
   Any other chat text from a seat is dropped — cogs shout, seats do not.
4. **Regime switch.** When `gamesPlayed` increments, the loop archives `hillTicks` into
   `gameHill[gameIndex]` and sets `sim.regime = config.regimes[min(gamesPlayed, high)]` before the
   next `startGame`.
5. **Wall-clock stop.** A `wallClockBudgetSeconds` check at the top of every loop iteration forces
   `phase = GameOver`, `reason = deadline`, `endRule = wall_clock`.

### The two named edits to `replays.nim`

1. **Masks are indexed by cog, not by roster slot.** `replayPrevInputs`/`replayInputs` build
   `seq[InputState](sim.cogCount)` instead of `sim.players.len` as a roster length, and
   `replayWriter.lastMasks` is sized to the cog count. Joins/leaves still carry the two **seats**
   (name, slot, token).
2. **A leave does not shift the mask arrays.** ctf deletes a leaving player's mask/overlay entries;
   paintball's cogs are fixed for the whole episode, so `applyReplayEvents` removes the roster entry
   and leaves the cog mask slots alone (keeping ctf's behaviour here would renumber cogs mid-replay).

Plus: `CtfReplayMagic "COWLDCTF"` → `PaintballReplayMagic "COWLDPNT"`, `GameName* = "paintball"`,
`GameVersion* = "1"` with ctf's prepend-only changelog-comment discipline, and
`tools/ci/check_gameversion.sh` kept as is.

### The two named edits to `roster.nim`

1. **Seats and cogs are different things.** `sim.players` holds the eight **cogs**;
   `sim.rewardAccounts` and `sim.config.players/slots/tokens` hold the two **seats**. A cog's
   `seat` field (0 or 1) is set at squad construction from its team; `slotOf(cogIndex)` returns the
   cog's seat, so every broadcast event keyed by slot keeps working. Join/auth still runs per seat,
   strictly slot-sequential, so `lobbyJoinTimedOut` still names the stuck seat.
2. **`playerResultsJson` aggregates by seat.** One entry per seat in every array (2 entries), with
   per-cog counters summed over the seat's team. The paintball keys are listed in §Server.

### The two named edits to `global.nim`

1. **Fog is per seat, not per cog.** `buildSpriteProtocolPlayerUpdates` takes a **seat** index and
   ORs the fov caches of the cogs that seat *commands under the current regime* (all four in
   `resident`, only `alpha` in `visitor`). Each commanded cog draws the distinct self marker; the
   seat's uncommanded teammates are fogged like anyone else. That makes the visitor regime a
   genuinely narrower view, which is the point of it.
2. **Floor paint replaces the floor stains.** The append-only cosmetic `paintStains` list is
   restricted to `onWall = true` marks; floor decals come from the paint grid, drawn from a new pool
   `PaintTileSpriteBase` / `PaintTileObjectBase` sized to `MaxPaintTiles` = 768, eight blot variants
   per team picked by a hash of the tile index (the starter's `StainVariants` idiom), emitted
   incrementally — only tiles whose owner changed since the viewer's last frame are re-placed.
   `diamondStains` is deleted with the generator's spinning-diamond paint bookkeeping retained for
   the arena's own diamonds.

### Determinism, native ↔ wasm

The mechanism is ctf's, unchanged, and it is the reason the starter is worth forking:

1. The server writes a `COWLDPNT` replay: magic + format version + game name/version header, the
   **resolved config JSON** (seed, `mapSpec`, roster, every tuning field), then the record stream —
   joins (name, slot, token), leaves, per-**cog** input-mask changes, chat records (directives,
   fallbacks, register, budget guard, result) and **one `gameHash` per tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/paintball_replay.nim` — which imports the
   **same** `src/paintball/sim.nim` — through the pinned `emscripten/emsdk:4.0.15` + nimby container
   in `Dockerfile.replay-viewer`.
3. In the browser, `paintball_load_replay` runs `parseReplayBytes` + `initReplayRuntime`, then
   `paintball_frame` re-steps the sim from the recorded masks and compares `sim.gameHash()` against
   the recorded hash **every tick** (`checkReplayHash`). A single divergent bit is caught at the tick
   it happens and surfaced as `mismatchTick` in `#mmwarn`.
4. All new sim arithmetic is **integer only** — tile indices, cone/tile coverage tests (`int64`
   intermediates), the permille ownership comparison, the buff multipliers. No floating point is
   introduced into `paint.nim`, `control.nim` or the hashed path; a CI grep over
   `src/paintball/{sim,sim_types,sim_state,paint,control}.nim` for
   `sin|cos|tan|arctan|sqrt|hypot|float` enforces it. This matters because Nim's `int` is 32-bit
   under `--cpu:wasm32` and the wasm build re-derives every tick.

Perf target: 2 × 2160 ticks of sim plus mask compilation and paint rasterisation in under 20 s on a
CI runner; `tests/test_perf.nim` bounds it at 120 s.

---

## Server, player, protocol

`src/paintball/server.nim` is ctf's `server.nim` with the five edits named above. Same routes
(`GET /healthz`, `GET /player?slot=N&token=T`, `GET /global`, `GET /client/global`,
`GET /client/player`, `GET /client/replay`, `GET /replay-data`, `GET /reward`), same `COGAME_*`
runtime contract (`COGAME_CONFIG_URI`, `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`,
`COGAME_PLAYER_FAILURE_URI`, `COGAME_LOAD_REPLAY_URI`, `COGAME_EVENTS_URI`, `COGAME_METRICS_URI`,
`COGAME_HOST`/`COGAME_PORT`), same 403 on a bad slot/token, same real pages on both `/client/`
routes registered before any catch-all (the lantern 0.1.1 cert probe), same bounded
`/healthz`+`/global` shutdown grace after artifacts are written (lantern 0.1.3), same
`src/paintball.nim` entrypoint with seed randomisation before `config.update`.

### The player container

`src/paintball_player.nim` (built to `/bin/paintball-player`) reads `COWORLD_PLAYER_WS_URL`,
`PLAYER_PROMPT`, `PLAYER_SCRIPTED` and `PLAYER_POLICY_LABEL`, connects, and sends **one Sprite v1
chat message** carrying its registration:

```json
{"type":"register","prompt":"<strategy text or empty>",
 "scripted":"holdline"|"sprayer"|null,"policy":"<free label>"}
```

It then sends the Sprite v1 Ready packet (`0x85`) after each received frame — legitimate here
because it never sends inputs — and otherwise only receives, until the socket closes. A seat that
never registers, or registers with neither field, is `scripted: "holdline"`. Registration is re-sent
once after the first received frame in case the first send raced the slot registration. The receive
loop is wrapped in `try/except CatchableError` and **exits 0 on a dead socket** — the raid 0.1.3
scar: whisky's `receiveMessage` raises on a close frame, and the game's `quit(0)` can outrun the
flushed frame, so a naive player exits 1 and fails certification intermittently.

### Per-seat observation: exactly what is visible and what is hidden

**Visible** — on the seat's Sprite v1 stream (one binary message per tick) and, in the same shape,
in the LLM view JSON:

- The static map (terrain is always visible in this engine), the arena's walkability sprite, and the
  live rotating diamonds.
- The **hill**, stated outright as an invisible 1 × 1 marker in the init snapshot and refreshed each
  tick, in the starter's stated-marker idiom:
  `hill <x0>,<y0> <x1>,<y1> own <red|blue|none> red <pct> blue <pct>`. Hill ownership and the two
  coverage percentages are **always visible to both seats** — it is the scoreboard, and Melting Pot's
  hill reward is public.
- The seat's own cogs: position, aim (`own aim <brads>` markers, one per commanded cog), hp bar
  (`hp <hp>/<maxHp>`), lives, spray readiness, and what each is standing on.
- Floor paint **inside the seat's fog** — painted tiles render as floor decals, so paint the seat's
  cogs can see is intel and paint across the map is not.
- Enemy cogs and their identity badges **only** inside the union of the commanded cogs' vision cones
  (±60° around each cog's aim, out to 1.5 × 1050 px, stone blocks, glass does not) or their ~90 px
  bubbles. The LLM view additionally carries enemies **seen within the last 72 ticks** with
  `ticks_ago`, which is memory the commander legitimately has.
- Shouts within `ShoutRange` (247 px of a commanded cog), labelled with the shouter's anonymous
  identity, from **either** team.
- Spray impact rings and paint splats, exactly as the starter renders them.
- The clock, the game index, the regime, the turn index, and both seats' banked hill seconds.

**Hidden:** the other seat's directive, prompt, `note` and view; the identity of any policy (real
names never reach a seat); enemy cogs outside vision and older than 72 ticks; floor paint outside
the seat's fog; the episode seed; the enemy's hp except where a visible cog's hp bar says so; future
ticks; and — in a `visitor` game — anything its three scripted teammates know but have not shown by
where they are standing.

### Results document

Written by `sim.playerResultsJson()` to `COGAME_RESULTS_URI`. It must equal the manifest's
`results_schema` key-for-key — that schema is `additionalProperties: false` and the certifier
rejects any unknown field (the starter carries the scar: `shotsFired`/`shotsHit` were pulled back
out for exactly this reason). Adding or removing a key here means editing
`coworld_manifest_template.json` in the same commit.

```json
{"names": ["daveey", "daveey-1"],
 "scores": [0.604, 0.396],
 "win": [true, false],
 "team": ["red", "blue"],
 "residentScore": [0.708, 0.292],
 "visitorScore": [0.500, 0.500],
 "hillTicks": [1103, 806],
 "residentHillTicks": [742, 442],
 "visitorHillTicks": [361, 364],
 "paintTiles": [214, 186],
 "tagsDealt": [17, 14],
 "tagsTaken": [14, 17],
 "llmTurns": [40, 40],
 "fallbackTurns": [0, 1],
 "reason": "complete",
 "endRule": "full_time",
 "games": 2,
 "finalTick": 4320,
 "seed": 679961}
```

`names` are the **real policy names** (spectator side). `team` carries the in-game aliases. Every
array has exactly `num_agents` = 2 entries, which is what `docker_smoke.sh` cross-checks.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDPNT`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse.
The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no Docker): it takes a
  `.replay` path and prints one strict-UTF-8 JSON object to stdout —
  `{"protocol":"paintball/v1","gameVersion":"1","seed":…,"names":[…],"aliases":[…],
  "policyKinds":[…],"regimes":[…],"tickCount":…,"directives":[…],"fallbacks":N,"results":{…}}`. It
  brace-matches the config JSON from the first `{` (the technique the starter's `AGENTS.md`
  documents for prod forensics) and decodes the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4** is therefore:
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks' /tmp/ep.json
  ```
  Require `protocol == "paintball/v1"`, `results.reason == "complete"` (or the declared-acceptable
  `deadline`), and the champion seats' directives `source == "llm"` with non-empty `note` and real
  intents — not all fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDPNT`, format version, `gameName` `paintball`, `gameVersion` `1` |
| config JSON | `seed`, `num_agents`, `mapSpec` (the full resolved arena geometry), `cogsPerTeam`, `regimes`, `maxTicks`, `maxGames`, `turnTicks`, every paint/hill/buff constant, `players[].name` (real names), `slots[].team`, `fastMode` |
| joins | per **seat**: `name` (real policy name), `slot`, `token` |
| inputs | per **cog** (0..7), on change: the `uint8` actuator mask — the action log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `result` records |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

Size: 4320 ticks of hashes plus ~40 k mask-change records plus 80 directive records ≈ 400 KB, well
under 1 MB.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed sim
fields; they drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `team`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `game`, `turn`, `seat`, `team`, `regime`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `note` (≤ 160 runes), `cogs`:[{`id`,`intent`,`target`,`face`,`say`}] |
| `fallback` | `game`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `result` | the full results document, written once at episode end |

**B. Derived broadcast events** — `stepEvents` (`broadcast.nim`, retargeted) derives these from state
deltas during playback, so they cost no replay bytes and are identical live and in replay. They feed
the match feed, the scrubber beats and the momentum graph:
`phase`, `gamestart` (`{game, regime}`), `spray` (a burst), `paint` (`{by, tiles, hillTiles}`,
throttled to one per cog per 6 ticks), `tag` (`{by, victim}`), `tagout` (`{by, victim}`),
`heal` (`{who}`), `hillflip` (`{team, pct}`), `hillhold` (every 24 owned ticks, `{team, seconds}`),
`respawn`, `gameover` (`{game, winner, draw, hillTicks}`). **Beats** (scrubber markers) are
`gamestart`, `hillflip`, `tagout` and `gameover`.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `SprayUse, Damage, Kill, Death, Respawn, Heal, PhaseChange, ShoutEvent`
and extended with `PaintTiles, HillFlip, HillHold, Directive`; the mandatory trailing summary row
(`type`, `ticks`, `events`, `gameVersion`) is kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` is the
starter's script, kept, with two literals changed (`image_tag`, and the `docker cp` source
`/workspace/paintball/replay-viewer/dist/.`); it builds `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copies the dist out. It must stay committed **executable**
(`coworld build` requires `os.X_OK`), and the hook `mkdir -p`s the output parent before its
containment check (the ecos, 2026-08-23 scar: `coworld build` pre-creates that directory, CI does
not).

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim`
(`replay-viewer/paintball_replay.nim`, forked from `replay-viewer/ctf_replay.nim`),
`replay-viewer/static_replay.js` + `static_replay_worker.js`, and `index.html` (built from
`client/replay_broadcast.html`) all come from ONE starter: `coworld-ctf`.** Never a mixture.
Splicing one starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23);
coworld-ctf's set is internally consistent — the Worker sets `Module.onRuntimeInitialized`, the
module is emitted non-modularized as `paintball_replay.js`, `config.nims` exports
`_paintball_load_replay,_paintball_frame,_paintball_packet_ptr,_paintball_packet_len,
_paintball_mismatch_tick,_paintball_error_ptr,_paintball_error_len,_paintball_stage_ptr,
_paintball_stage_len` alongside `_main,_malloc,_free`, and `static_replay_worker.js`
`importScripts('./wire_constants.js','./broadcast_core.js','./paintball_replay.js')` in that order.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch — which the Worker posts only *after*
`ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute means
"a frame is on the canvas", not "a file was fetched". On failure the shell sets
**`data-replay-error`** on `<html>` with the message: this is the **one named edit** to
`static_replay.js`, whose `showFailure()` currently only writes `#status` — without it a deadlocked
bundle looks identical to a slow one. The `coworld-replay` postMessage bridge's `ready` is posted
from a callback fired **after** `data-replay-loaded="true"` is set, never on rAF timing at the call
site (chorus `3c11c953`, 2026-08-24) — otherwise the softmax.com embed samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is copied byte-for-byte from coworld-ctf.** Not edited, not
  reformatted. Everything paintball adds lives in the appended game block. Its `markBeat`/
  `renderBeatMarkers`/`ingestBeats` remain; `ingestBeats` ignores kinds it does not know and still
  drives `setVerdict` off `gameover`, which is exactly the behaviour paintball wants.
- **`client/broadcast_core.js` is copied byte-for-byte** apart from the single `window.CTF_WIRE` →
  `window.PAINTBALL_WIRE` identifier, which `tools/gen_wire_constants.nim` emits.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a
  rewrite that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`,
  transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density system are untouched;
  the appended block replaces only the *contents* of the scorebug plates, the feed rows, the beat
  rendering and the endcard's stat columns.
- **Elements removed** (exactly these, and the JS that feeds them):
  `#viewpanel` — the zoom bar and minimap. **Zoom decision:** the board is the fixed 1235 × 659
  arena and `relayout()` always fits it whole inside the frame, so per the pin a fixed arena drops
  `#viewpanel` entirely; the page's `attachMinimap(...)` call goes with it (`broadcast_core.js`
  tolerates a missing minimap: `pendingMinimap` simply stays null, so the file stays byte-identical).
  Also removed: the heart/flag elements of the scorebug (`flag`, `carrier`, `prog` fields and the
  `.ec-heart` endcard glyphs), the `.beat-marker.steal/.return/.capture` rules, and the perk/handicap
  badges (paintball has neither).
  **Kept:** `#stage`, `#board`, `#lockerroom`, `#scorebug`, `#bannerlane`, `#killfeed`, `#fpv` (the
  first-person picture-in-picture — it is the best view of what floor paint looks like from a cog's
  eye), `#povBadge`, `#mmwarn`, `#transport` in full, `#endcard`, `#lightpool`, `#grain`.

### Transport rules

`relayout()` sets `--band` (the measured transport strip) and `--topband` (the scorebug strip) and
`--hudscale` on `:root`, unchanged. **No overlay sits in the transport band**: the board is laid out
between the two bands, and every paintball addition (hill ring, feed, banners) is positioned inside
the board region. The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band, 0px) }`,
the starter's rule, kept) so the scrubber stays clickable underneath, and it is **dismissed by every
seek** (the starter's `else { $('endcard').classList.remove('on'); }` path, kept). **Scrubber beats
are clickable, labelled buttons**: the appended block's `pbBeat(tick, kind, team, label)` — named so
it can never shadow chrome_common's `markBeat` alias, the tandem 2026-08-23 hoisting trap — appends
`<button class="beat-marker <kind> <team>" title="…" aria-label="…">` to `#scrub` and seeks on click.
CSS exists for **every kind paintball emits**: `.beat-marker.gamestart`, `.beat-marker.hillflip.red`,
`.beat-marker.hillflip.blue`, `.beat-marker.tagout.red`, `.beat-marker.tagout.blue`,
`.beat-marker.gameover`. Paintball never calls chrome_common's `markBeat`, so no unlabelled div
marker can appear.

### Readouts

1. **Score bug** (top, always on): two team plates — real policy name (spectator side), colour chip,
   **hill time held** as `M:SS`, live **hill coverage %**, and tag-outs — around the centre clock
   column. `teams.<color>` carries `{hill, held, cov, own, tags, cogs, policies}` in place of ctf's
   `{lives, flag, carrier, prog}`.
2. **Clock**: `M:SS` counting down inside the current game, with the caption
   `game 1/2 · RESIDENT · turn 7/20` (or `VISITOR`). The regime is on screen at all times, because
   the resident/visitor split is the thing a spectator most needs told.
3. **The board is the readout.** Painted tiles are drawn as translucent team-tinted floor decals, so
   the arena visibly changes colour as the game goes — territory is legible at a glance without any
   label.
4. **Hill overlay**: the 170 × 170 px hill drawn as a chalk square baked into the floor, plus a live
   ring in the owner's colour (grey while unowned) and a coverage arc showing each team's percentage;
   the ring pulses for 12 frames on a flip.
5. **Match feed** (`#killfeed`, renamed in copy only): plain language — "RED-beta tags BLUE-alpha",
   "**RED TAKES THE HILL — 84 %**", "BLUE-delta healed on blue paint", and the commander lines
   ("Red command: flood the west rim, beta screens"). The directive `note` and each cog's `say`
   appear here; this is where a spectator sees the LLM playing.
6. **Momentum graph**: the starter's `lead` series, retargeted from lives to the **hill-tick
   difference**, drawn over the whole episode from the first frame (both games end to end, with the
   game boundary marked).
7. **Buff pips**: a small chevron over a cog standing on its own paint (speed up) and a downward one
   on enemy paint, plus the starter's existing green `hp` pips for the heal.
8. **First-person PIP** (`#fpv`): unchanged, and now the clearest demonstration of the buff — the
   floor under the selected cog is its own colour or the enemy's.
9. **Transport and integrity**: play/pause, step, speeds `[1,2,3,4,8,16]`, scrubber with beat
   buttons, tick readout, skip-lulls, spoilers switch, end-hold countdown, and the `#mmwarn`
   hash-mismatch line — all verbatim.
10. **Endcard**: "RED holds 1:56 — BLUE 1:14 · resident 0.71 / visitor 0.50", the per-team cog table
    (tags dealt/taken, tiles painted, hill seconds), the winner headline, and the replay countdown.
    It stops at `var(--band)` and any seek dismisses it.

### Art

Real, and mostly already in the repo. Cogs are the shipped `data/soldier_red*` / `data/soldier_blue*`
sprites composed by `global.nim` and the `data/rig_real/{red,blue}` rigs; the held weapon is the
shipped `data/spraycan_held.png`; walls are `client/art/walls/*.jpg`; the loading screen is the
starter's locker room (`client/art/lockerroom/bg.jpg` plus the red/blue cog webps). Floor paint is
baked at startup with pixie by the starter's own `buildPaintStainSprite` compositor, retuned for a
tile: eight 34 px matte splats per team with frayed edges and a peak alpha of 104, chosen per tile by
a hash of the tile index so a painted area reads as organic spray rather than a checkerboard. The
hill's chalk square is baked into the floor art at map install. No solid-colour placeholders, no TODO
assets, no downloaded art.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`. Kept
verbatim. Paintball adds two rules of its own: `.plate-name` gets
`flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis` so a policy name never
collapses to "…", and under `.tiny` the tag counter and the coverage % are hidden so the plates read
`▮ daveey 1:56 — 1:14 daveey-1 ▮` plus the clock and the regime chip. `tests/test_viewer.nim` asserts
both rules are present.

---

## Packaging

- **Repo**: `Metta-AI/cogame-paintball`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `paintball`; `game.name` is **`paintball`**
  (no underscore), so the secret namespace `secret://coworld/paintball/anthropic_api_key`, the page
  slug and the compose service all agree (the cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — one service, named for the coworld, so the manifest placeholder is
  `{{PAINTBALL_IMAGE}}` (placeholders are derived from compose service names — the lantern 0.1.0
  scar):

  ```yaml
  services:
    paintball:
      image: coworld-paintball:latest
      platform: linux/amd64
      build:
        context: .
        network: host
  ```

  (ctf ships two services/two images; paintball uses the one-image/two-entrypoints shape because the
  shared `docker_smoke.sh` and `policies.json` assume a single image.)
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure
  (nimby 0.1.26, `nimby use 2.2.4`, `nimby --global sync nimby.lock`), building **two** binaries:
  `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on --out:paintball src/paintball.nim` →
  `/bin/paintball`, and the same for `src/paintball_player.nim` → `/bin/paintball-player`. Runtime
  stage copies both binaries, `data/`, `client/`, `*.json`. `CMD ["/bin/paintball"]`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (`emscripten/emsdk:4.0.15`, pinned nimby
  0.1.27 with its sha256 check, the three marker splices, the whole `test -f` / `grep -q` assertion
  block) with the asset list swapped: red/blue soldier art only, walls, locker room, `font.ttf`,
  `paintball_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`, `chrome_common.js`,
  `static_replay.js`, `static_replay_worker.js`, `index.html`, `league.html`.
- **`coworld_manifest_template.json`** (validated offline with the CLI's `validate_upload_manifest`
  before the first dispatch — the hive 0.1.0 scar):
  - `$schema` set; top-level `tags`: `["shooter","team","paintball","king-of-the-hill","llm"]`;
    `episode_timeout_minutes: 20`.
  - `game.name` `paintball`; `game.runnable` `{"type":"game","image":"{{PAINTBALL_IMAGE}}",
    "run":["/bin/paintball"],
    "env":{"ANTHROPIC_API_KEY_URI":"secret://coworld/paintball/anthropic_api_key"},
    "source_url":"https://github.com/Metta-AI/cogame-paintball/tree/main"}`.
  - `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`.
  - `game.config_schema` — a real JSON Schema, `additionalProperties: false`, required
    `["tokens","players"]`, **every array bounded**: `tokens` (`minItems` 2, `maxItems` 2),
    `players` (2, 2), `slots` (2, 2), `regimes` (`minItems` 1, `maxItems` 4, items enum
    `["resident","visitor"]`). Scalars: `seed`, **`num_agents`**, `minPlayers`, `cogsPerTeam`
    (default 4), `lives` (12), `hitPoints` (3), `sprayDamage` (1), `respawnTicks` (48),
    `aimTurnRate` (5), `visionConeDeg` (60), `visionBubble` (90), `maxTicks` (2160),
    `maxGames` (2), `turnTicks` (108), `turnBudgetMs` (7000), `attempt1Ms` (4500),
    `retryMs` (2000), `turnSpacingMs` (5000), `wallClockBudgetSeconds` (690),
    `lobbyJoinTimeoutTicks` (2400), `startWaitTicks` (120), `gameOverTicks` (72),
    `mapPath` (`"arena"`), `loadout` (`"paintball"`), `floorPaint` (true), `paintBuff` (true),
    `hill` (true), `paintTile` (34), `hillRadiusTiles` (2), `hillOwnPermille` (800),
    `hillDecisiveTicks` (720), `paintSpeedOwnPct` (125), `paintSpeedEnemyPct` (85),
    `paintHealTicks` (48), `fastMode` (true), `showPlayerLabels` (false), `model`,
    `maxOutputTokens` (900).
  - `game.results_schema`: exactly the 19 keys in §Server, `additionalProperties: false`,
    `required: ["names","scores","win","team","reason","endRule"]`, every array
    `minItems: 2, maxItems: 2`, `reason` enum `["complete","deadline","fault"]`, `endRule` enum
    `["full_time","mercy","wipe","wall_clock","sim_fault","host_error"]`.
  - `game.protocols`: **both** `player` and `global`, each
    `{"type":"text","value":"<docs/PROTOCOL.md inlined>"}` — object form, not a bare string (the
    garble v0.1.0 scar).
  - `game.docs`: `readme` = `{"type":"text","value":"<README body inlined>"}` and `pages` = three
    entries — `rules` ("Rules", `docs/RULES.md` inlined), `protocol` ("Wire protocol",
    `docs/PROTOCOL.md` inlined), `commanding` ("Writing a paintball prompt", `docs/COMMANDING.md`
    inlined), each `{"id","title","content":{"type":"text","value":…}}`. **Text form, not URIs** (the
    starter's URI form is not copied). A manifest test asserts all four values are non-empty.
  - `player[0]` = `{"id":"baseline","type":"player","name":"Paintball Holdline Baseline",
    "description":"Scripted squad commander: hold the hill, paint its far edge, keep one guard.",
    "image":"{{PAINTBALL_IMAGE}}","run":["/bin/paintball-player"],
    "env":{"PLAYER_SCRIPTED":"holdline"},"source_url":…,
    "resources":{"requests":{"cpu":"100m","memory":"64Mi"},"limits":{"cpu":"1"}}}` — the only
    declared player, and it is seated in both certification slots (the raid 0.1.2 `players_missing`
    scar: every declared player entry must occupy a certification slot).
  - **Variants — `num_agents` is 2 in all four**, each with a `description`:

    | id | name | `num_agents` | `maxGames` | `regimes` | `maxTicks` | `paintBuff` | `hill` |
    |---|---|---|---|---|---|---|---|
    | `default` | King of the Hill (resident + visitor) | **2** | 2 | `["resident","visitor"]` | 2160 | true | true |
    | `koth-resident` | King of the Hill (resident only) | **2** | 1 | `["resident"]` | 2160 | true | true |
    | `koth-visitor` | King of the Hill (lone visitor) | **2** | 1 | `["visitor"]` | 2160 | true | true |
    | `koth-nobuff` | King of the Hill (no paint buff) | **2** | 2 | `["resident","visitor"]` | 2160 | **false** | true |

    Every variant also carries `players` (2 named entries), `slots`
    (`[{"team":"red"},{"team":"blue"}]`), `tokens` (2), `minPlayers: 2`, `cogsPerTeam: 4`,
    `mapPath: "arena"`, `loadout: "paintball"`, `floorPaint: true`, `lives: 12`, `hitPoints: 3`,
    `sprayDamage: 1`, `respawnTicks: 48`, `turnTicks: 108`, `turnBudgetMs: 7000`,
    `turnSpacingMs: 5000`, `wallClockBudgetSeconds: 690`, `lobbyJoinTimeoutTicks: 2400`,
    `fastMode: true`, `showPlayerLabels: false`, `seed: 679961`. `koth-resident`/`koth-visitor` exist
    so the two halves can be laddered separately for analysis; they change only `maxGames`/`regimes`,
    never the seat count.
  - **Certification fixture**: `certification.players` = `[{"player_id":"baseline"},
    {"player_id":"baseline"}]`; `certification.game_config` = `{"players":[{"name":"Red Command"},
    {"name":"Blue Command"}], "slots":[{"team":"red"},{"team":"blue"}], "tokens":["t0","t1"],
    "num_agents": 2, "minPlayers": 2, "cogsPerTeam": 4, "seed": 679961, "mapPath": "arena",
    "loadout": "paintball", "floorPaint": true, "paintBuff": true, "hill": true,
    "regimes": ["resident","visitor"], "maxTicks": 600, "maxGames": 2, "turnTicks": 108,
    "turnBudgetMs": 7000, "turnSpacingMs": 0, "wallClockBudgetSeconds": 180,
    "lobbyJoinTimeoutTicks": 1440, "startWaitTicks": 0, "gameOverTicks": 24, "lives": 12,
    "hitPoints": 3, "sprayDamage": 1, "fastMode": true, "showPlayerLabels": false}` — both seats
    scripted, no LLM, no rate floor, 2 × 600 ticks. That is **1200 ticks = 50 s of playback** at
    24 fps, deliberately longer than any viewer soak window (the ecos 2026-08-23 scar), while
    `fastMode` plays it in a handful of wall seconds. The `certify` step in `coworld-release.yml`
    passes **`--timeout-seconds 300`** (the default 60 s covers start + connect grace + rounds +
    linger — cooperative-hunting 0.1.2).
- **Scaffold from `templates/`** with `<slug>` = `paintball`, `<IMAGE>` = `coworld-paintball`,
  `<SEATS>` = **2**: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`,
  `tools/ci/docker_smoke.sh` (**`chmod +x`**), `tools/ci/viewer_smoke.mjs` (copied verbatim),
  `tools/ci/policies.json`, plus the starter's `tools/build_replay_viewer.sh` (**`chmod +x`**). Three
  additions to the template `ci.yml`:
  - the `docker-smoke` step gets `SMOKE_REQUIRE_REPLAY_JSON: "0"` (binary replay format);
  - the `wasm-viewer` job gets a final step
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/replay.json 300` — the
    native↔wasm determinism gate, which fails if `paintball_mismatch_tick() != -1`;
  - repo variable `NIM_TESTS_RELEASE_ONLY` lists `tests/test_perf.nim`.
- **`tools/ci/policies.json`** (all four `"run": "/bin/paintball-player"`, one image, env-switched):

  | name | env | role |
  |---|---|---|
  | `paintball-holdcentre` | `PLAYER_PROMPT` = champion #1 prompt (§Decisions) | champion #1, owner daveey |
  | `paintball-splitpaint` | `PLAYER_PROMPT` = champion #2 prompt, plus `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` | champion #2, owner daveey-1 |
  | `paintball-holdline` | `PLAYER_SCRIPTED` = `holdline` | filler |
  | `paintball-sprayer` | `PLAYER_SCRIPTED` = `sprayer` | filler |

- **Repo layout**: `src/paintball.nim`, `src/paintball_player.nim`,
  `src/paintball/{sim.nim, sim_types.nim, sim_config.nim, sim_state.nim, arena.nim, map_art.nim,
  paint.nim, control.nim, directives.nim, baselines.nim, llm.nim, decide.nim, roster.nim,
  replays.nim, replay_runtime.nim, broadcast.nim, events.nim, global.nim, labels.nim, rig_art.nim,
  wire_constants.nim, server.nim}`, `replay-viewer/{paintball_replay.nim, config.nims,
  static_replay.js, static_replay_worker.js}`, `client/`, `data/`, `tests/`,
  `tools/{build_replay_viewer.sh, gen_wire_constants.nim, expand_replay.nim, extract_events.nim,
  replay_summary.py, record_fixture.sh, wasm_replay_smoke.cjs, ci/}`,
  `docs/{RULES.md, PROTOCOL.md, COMMANDING.md, plans/2026-08-25-paintball-design.md}`, `AGENTS.md`,
  `README.md`, `config.json`, `nimby.lock`, `paintball.nimble`, `compose.yaml`,
  `coworld_manifest_template.json`, `Dockerfile`, `Dockerfile.replay-viewer`.

---

## Tests

`tests/*.nim`, run by the template `ci.yml` `test` job in **both debug and release** (debug enables
Nim's range/overflow checks — the cheapest catch for an index or fixed-point overflow). CI is the
only harness; the sandbox has no Nim, Docker or emsdk.

1. **`tests/test_paint.nim`** — sim unit tests for the grid: `paintFloor` marks exactly the tiles
   whose centre is walkable at spin frame 0; a cone fired due east from a known position paints
   exactly the expected tile list (a golden set), and none behind the sprayer; a repaint over an
   enemy tile moves one count from each team and leaves the total constant; `paintCount` and
   `hillPaint` equal a full rescan of `paintOwner` after 500 random bursts; painting is symmetric —
   the mirror-image burst on the mirror-image position paints the mirror-image tiles.
2. **`tests/test_buff.nim`** — the buff: a cog on own paint has max speed 880 and accel 95 motion
   units, on enemy paint 598/64, on unpainted 704/76 (the exact integer results of the composition
   rule); 48 continuous ticks on own paint heals exactly 1 hp and resets the counter; 47 ticks then
   one tick off heals nothing; a heal never exceeds `maxHpFor`; taking damage resets the counter;
   dying resets it; with `paintBuff: false` none of it fires and the tick-by-tick `gameHash` matches
   a run with the whole feature compiled out of the config.
3. **`tests/test_hill.nim`** — KotH: `hillFloorTiles` on the arena is ≥ 15 and its tile set is
   symmetric about the midline; ownership flips **exactly** at the 80 % threshold (at
   `ceil(0.8 * hillFloorTiles) - 1` tiles nobody owns, at that count the team does); two teams can
   never both own it; `hillTicks` increments once per owned tick and not while unowned; a wipe
   credits the survivor with exactly the remaining ticks; mercy fires on the first tick the lead
   exceeds the remainder and not before; a 2160-tick game with equal hill ticks ends
   `full_time` + `isDraw`.
4. **`tests/test_scoring.nim`** — the formula and its sign: `gameScore` is 1.0 at a +720 tick margin,
   0.0 at −720, 0.5 at 0, monotone in between; `score(0) + score(1) == 1.0` (to 1e-9) over 10 000
   random `(residentMargin, visitorMargin)` pairs; a seat that wins resident and loses visitor by the
   same margin scores exactly 0.5 — the property the resident/visitor mean exists to create;
   `win[s] == (score[s] > 0.5)`; a `fault` episode is 0.5/0.5 with `win` both false.
5. **`tests/test_regimes.nim`** — resident/visitor wiring: in a `resident` game all four cogs of a
   team follow the seat's directive and none follows `holdline`; in a `visitor` game exactly
   `alpha` follows the seat and `beta`/`gamma`/`delta` produce byte-identical masks to a pure
   `holdline` run from the same state; the regime advances `resident` → `visitor` across
   `gamesPlayed`; the seat's fog in a `visitor` game is a strict subset of its fog in a `resident`
   game from the same positions.
6. **`tests/test_control.nim`** — **the bounded-orders / legality assertion on the scripted
   baselines**: for 500 pseudo-random world states × both baselines, the emitted directive validates
   against the reply schema — exactly the commanded cog ids, all intents in the enum, targets inside
   the map and on walkable pixels, `note` ≤ 160 runes, `say` ≤ 10 runes — and every compiled mask
   has only legal bits, never Up+Down or Left+Right together, never `C`. Plus: the same
   (state, directive) pair always yields the same byte; `fall_back` never sets `A`; the trigger is
   never set while repressurizing; a cog ordered to an unreachable target does not stall (it moves
   every tick for 120 ticks); and a `holdline` vs `sprayer` episode at seed 679961 completes,
   `holdline` wins, and **the hill changes hands at least twice** (a pinned regression against a
   degenerate stalemate).
7. **`tests/test_directives.nim`** — tolerant parsing and repair: prose-prefixed JSON, fenced JSON,
   `cogs` as an id-keyed object, unknown intents, absent/NaN targets, off-map targets, a target
   inside a wall, five cogs, zero cogs, an id from the other team, a 300-character `note`, and a
   `say` whose 10th and 11th characters are a 4-byte emoji — the truncation must land on the **rune**
   boundary and the result must still round-trip `%$` → `parseJson` and decode as UTF-8. Two
   consecutive failures ⇒ the `holdline` directive plus a `fallback` record; a timeout on attempt 1
   ⇒ exactly one retry.
8. **`tests/test_engine.nim`** — the turn loop against a fake LLM client: both seats' calls go out in
   **one parallel batch** (the fake records in-flight windows and the test asserts they intersect);
   the per-turn budget is enforced with a hung client; `turnSpacingMs` holds the batch rate at
   ≤ 24/min; the budget guard switches to scripted and the episode still ends `complete/full_time`;
   the 690 s stop yields `deadline/wall_clock`; a raised sim guard yields `fault/sim_fault` with
   0.5/0.5 and a partial replay; a disconnected seat plays `holdline` and revives on reconnect; a
   never-connecting seat is reported to `COGAME_PLAYER_FAILURE_URI` and both games still reach
   `full_time`.
9. **`tests/test_replay.nim`** — **an end-to-end episode writing a replay**: a full
   scripted-vs-scripted 2-game episode writes `results.json` and a `COWLDPNT` replay;
   `parseReplayBytes` accepts it; re-simulating from the config + mask log reproduces **every**
   recorded hash; **strict-UTF-8 parse** — `tools/replay_summary.py`'s stdout parses under
   `json.loads(out.decode("utf-8"))` and the embedded config JSON decodes strictly, with the fixture
   forced to carry a non-ASCII policy label and a non-ASCII `note` so the UTF-8 path is real; every
   `directive` record is ≤ 900 runes; `results.reason` is in the legal enum; the stream contains at
   least one `spray`, one `paint`, one `hillflip`, one `directive` per seat per turn, two
   `gamestart` records and exactly one `result` record.
10. **`tests/test_identity_privacy.nim`** — the starter's test, **kept and extended**: no sprite label
    in a *seat* frame ever contains a sentinel policy address (the starter's sweep), and the new
    sweep adds the composed LLM system+user message and the `directive` record — while the
    board/broadcast stream, `roster[].name`, `teams.<color>.policies` and `results.names` **must**
    contain it. That is the two-name-space pin, asserted from both sides.
11. **`tests/test_manifest.nim`** — `num_agents == 2` in **every** variant *and* in
    `certification.game_config`; `len(certification.players) == 2`; `results_schema` keys ==
    `playerResultsJson` keys; `game.protocols` has both `player` and `global` in object form;
    `game.docs.readme` and all three pages are non-empty **text**;
    `replay_viewer.bundle == "static-replay-viewer"`; every variant's
    `wallClockBudgetSeconds <= 0.6 * 1200`; every array property in `config_schema` declares
    `minItems`/`maxItems`; the compose service name and image match `{{PAINTBALL_IMAGE}}` /
    `coworld-paintball`; `game.name` has no underscore and equals the secret namespace in
    `game.runnable.env.ANTHROPIC_API_KEY_URI`; `config_schema` covers every field
    `sim_config.update` reads.
12. **`tests/test_viewer.nim`** — the static half of the **viewer smoke** (no browser): assertions
    over `client/replay_broadcast.html` and `client/chrome_common.js` that the transport controls,
    `#scorebug`, `#bannerlane`, `#killfeed`, `#endcard`, `#mmwarn`, the `.tiny` block, the
    `--hudscale` clamp, `#endcard { bottom: var(--band` and the `.plate-name` rule are present; that
    `#viewpanel`, `#minimap` and `#zoombar` are **absent**; that `chrome_common.js` is byte-identical
    to the starter's copy (sha256 pinned in the test); that `broadcast_core.js` differs from the
    starter's in **exactly** the `PAINTBALL_WIRE` identifier; that the appended game block defines no
    identifier that collides with the chrome alias list (the tandem shadowing guard) and defines CSS
    for every beat kind the sim emits; and that no `ctf_`/`CTF_` identifier survives in `client/`,
    `replay-viewer/` or `src/`.
13. **`tests/test_startup.nim`** — `/bin/paintball` exits non-zero with a clean message and no
    traceback when `COGAME_CONFIG_URI` is missing or unparseable; the seed is randomised when
    unpinned and honoured when pinned; both entrypoints exist and are executable in the image
    (asserted by the docker smoke).
14. **`tests/test_perf.nim`** (release-only) — a full 2 × 2160-tick episode with mask compilation and
    paint rasterisation completes in under 120 s.

Beyond the Nim suite, `ci.yml` runs:

- **`tools/ci/docker_smoke.sh`** — a raw-Docker episode from the certification fixture in the
  production image, seats cross-checked against `SMOKE_SEATS=2`, `SMOKE_REQUIRE_REPLAY_JSON=0`,
  asserting the game container exits 0 with `results.json` and a replay, **and** that every *player*
  container exited 0 (the raid 0.1.3 scar). Its replay is uploaded as the `smoke-replay` artifact.
- **the `wasm-viewer` job** — builds the bundle, asserts `index.html` and a non-empty `.wasm` exist,
  then **executes** it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
  dist/smoke/replay.json --timeout 90 --strict-text-bounds`, against the replay `docker-smoke`
  produced. The bundle is executed, not merely built; `--strict-text-bounds` is kept because the
  arena is fixed and fits the frame, so `canvas_text.never_inside` must be 0. The job then runs
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer dist/smoke/replay.json 300` as the
  native↔wasm hash gate.

---

## Out of scope (v1)

- **Every ctf mechanic the paintball loadout removes**: hearts/flags and capture, the hitscan gun and
  its jitter/exposure model, grenades and the grenade barrage, med kits, shields, cardboard barriers,
  paint puddles, trenches, perks, handicaps, and four-team free-for-all. Deleted, not disabled.
- **Procedural terrain** — the generator, the curated pool, `mapkit`, the map editor and the
  pool-review page. Paintball pins the hand-tuned arena; a moving board would make the hill's tile
  set, the paint grid size and the viewer's fixed-frame zoom decision all variable for no gain in v1.
- **Melting Pot's paintball CTF mode.** The idea names `paintball__capture_the_flag` only as a
  source; the three mechanics it puts in scope are the buff, the hill and resident/visitor. A
  paint-CTF variant is a v0.2 config gate over the same grid.
- **More than two regimes** — no 2-resident/2-visitor mixed squads, no cross-play matrix over three
  or more policies per episode, no "visitor among *another policy's* teammates" (that needs seat
  assignment paintball does not own). The `regimes` array is bounded at 4 entries so the shape exists.
- **Raw per-tick actuator control by an external policy.** One Sprite v1 mask cannot address four
  cogs; the v1 control channel is the directive plus the server-side control layer. The recorded
  action log is already the right shape for a v0.2 protocol addition (`num_agents` 8, one cog per
  seat).
- **Paint decay / drying.** Tiles keep their colour until repainted. Melting Pot does the same, and a
  decay clock would put a second timer in `gameHash` for no rule the idea asks for.
- **Paint on walls as gameplay.** Wall marks stay cosmetic; only floor tiles have owners.
- **Achievements.** The starter's win-gated achievement catalog and its `results.achievements` key
  are dropped; the results document carries hill and tag counters instead.
- **Player debug-sprite overlays** (ctf's `0x86` channel), **inter-seat chat**, **persistent memory
  across episodes**, and any tournament structure beyond the platform league.
- **Campaign mode.** ctf's territory-campaign integration is a platform-side feature and is not wired
  up for paintball in v1.
- **Audio, 3D, camera cuts, and any downloaded art asset.**
