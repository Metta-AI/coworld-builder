# cogame-vizdoom-deathmatch — design note (2026-08-27)

**Starter: `Metta-AI/coworld-ctf`** (paintbot / the crewrift-derived engine), mounted read-only at
`/workspace/starters/coworld-ctf` and read for this note. **Every convention there holds here unless
this note says otherwise.** That means: Nim throughout; the `src/ctf/` module split (`sim.nim`
re-exporting the sim modules, `sim_types.nim` owning `GameVersion`, `TargetFps = 24`,
`ReplayFps = 24`, `PlayerHalf = 6`, the fixed-point motion constants `MotionScale 256 / Accel 76 /
FrictionNum 144 / MaxSpeed 704`, the flatty wire types with their sacred field order, and the rune
caps `MaxSayRunes = ShoutMaxChars = 10` / `MaxNoteRunes = 160` / `MaxPolicyLabelRunes = 48` /
`MaxFallbackDetailRunes = 200` / `MaxDirectiveRunes = 900` / `MaxPromptRunes = 4000`); continuous-2D
movement with per-axis slide collision; the recursive-shadowcast fog of war on an 8 px cell grid plus
the aim-carried vision cone and bubble; **the hitscan gun** (`fireWindupTicks` aim lock, fuzzed aim,
`GunRange = 1050`, `HitPoints = 3`, friendly fire on, `RespawnTicks`, `recordKill` / `recordDeath` /
`recordTeamKill` in `roster.nim:606-631`); **the first-person raycast picture-in-picture**
(`broadcast.nim:515 firstPersonJson`, `#fpv` in `client/replay_broadcast.html:1532`,
`tests/test_first_person_pip.nim`); the Sprite v1 protocol and the mummy HTTP/websocket server
implementing the Coworld contract; the `decide.nim` / `directives.nim` / `llm.nim` / `baselines.nim`
/ `control.nim` commander layer with its one-parallel-batch-per-turn shape, its `attempt1Ms` /
`retryMs` / `turnBudgetMs` / `turnSpacingMs` deadlines, its tolerant JSON extraction, its
rune-boundary truncation, its repair-don't-reject validator and its fallback ladder; the binary
`COWLD…` replay of *per-tick input masks plus a per-tick `gameHash`*, re-simulated by **the same sim
module** compiled to wasm by `replay-viewer/config.nims`; the `client/` broadcast chrome
(`chrome_common.js` + `broadcast_core.js` + `replay_broadcast.html` with an **appended game block**
spliced in through `window.PaintballChrome.install(PB_CTX)` at `client/replay_broadcast.html:4337`);
nimby + `Dockerfile` + `Dockerfile.replay-viewer` + `tools/build_replay_viewer.sh` +
`tools/replay_summary.py` + `tools/wasm_replay_smoke.cjs`; and the Nim test suite with its four
shards (`tests/shard_1..4.nim`, `tests/config.nims`).

Starter choice, one line: **this is the idea's own "cheaper alternative", and the crewrift/ctf engine
already ships every part of it** — fog-of-war vision cones, a hitscan gun, hit points, respawns, a
deathmatch-capable two-base arena, *and* a working first-person raycast view of a seat's cone
(`firstPersonJson`) — so the whole coworld is a new objective layer (frags − deaths, team DM, an
egocentric observation) on a real-time loop, which is row 1 of `prompts/10-design.md`'s starter table.
It is deliberately **not** the `cogame-moba` row: **this is NOT a ViZDoom/ZDoom port.** Nothing is
reproduced bit-exactly, no ZDoom container is built, no `vizdoom` Python bridge exists in this repo,
and no raw pixel buffer is ever produced. What is reproduced is ViZDoom multiplayer's *shape* — eight
agents, one map, frags − deaths, an egocentric first-person observation — on an engine that compiles
to wasm so the replay is a static file (a real ViZDoom port cannot do that, which is the second reason
the idea's own fallback is the right call).

Where this note departs from coworld-ctf it says so. The departures are: the **heart/flag objective is
retired and its capture/steal/return rules deleted** (the endzone *geometry* is kept — it is what makes
the arena a symmetric two-base map and it is what `retreat` aims at); King of the Hill, floor paint,
spray cans, the paint buff, grenades, the barrage, shields, cardboard barriers, puddles, trenches,
perks, handicaps, achievements, four-team play, the `resident`/`visitor` regimes and campaign mode are
**deleted, not disabled**; **one cog per seat** (`cogsPerTeam: 1`) instead of paintbot's squad of four,
which forces two named edits (`squadMode`'s gate and `cogIdentityIndex`); **`visionConeDeg` drops from
60 to 45** so the cone is ViZDoom's 90° default FOV; the LLM's observation is a new **egocentric
labels-and-depth view** built by the *same* ray march the viewer's first-person inset uses; and the
scoring rule is **frags − deaths**, team-summed and zero-sum.

### Source idea (verbatim)

> Port of ViZDoom's multiplayer mode (Visual Doom AI Competition 2016-17): up to 8 agents in a
> deathmatch on a Doom map, observing only their first-person frame (plus optional depth/labels
> buffers); actions: move, turn, attack, use. Frags − deaths. Single-player scenarios (basic, defend
> the center, deadly corridor, health gathering, my way home) as a training ladder.
>
> Cheaper alternative to evaluate first: coworld-ctf / crewrift already has fog-of-war vision cones,
> guns, respawn and a deathmatch-capable arena; a first-person observation mode (raycast render of the
> cone into a small frame) on that engine gives the same 'pixels only' test without ZDoom containers.
> Only do the real ViZDoom port if fidelity to the published benchmark matters.
>
> Seats: 2-8
> Motive: zero-sum FFA or 4v4 team DM
> Policy interface: per-frame discrete over pixels — neural-policy coworld; LLM needs the labels buffer
> Fills gap: first-person 3D — everything on the site is top-down
> Integrity: prefer team DM with server-assigned teams; FFA ganging detectable from the damage graph;
> maps seeded.
> Replay plan: spectator free-cam + per-seat first-person thumbnails; kill feed.

### Rail decisions taken above this note (recorded, not revisited)

| Rail | Decision | Reason |
|---|---|---|
| Starter | `coworld-ctf` | the idea's own cheaper alternative; the engine already has cones, guns, respawn and a DM arena |
| Scope | **not** a ZDoom port; no containers, no ViZDoom bridge | fidelity to the published benchmark is explicitly not required by the idea; a ZDoom process cannot compile to wasm, so the replay could not be a static bundle |
| Seats | `num_agents` = **8**, played 4v4 **team deathmatch**, teams server-assigned | the idea's own integrity note: "prefer team DM with server-assigned teams" |
| Scoring | frags − deaths (this note fixes the exact team formulation, sign and tiebreak) | pinned by the idea |
| Policy interface | **LLM prompt policy + scripted baseline**, not neural pixels; "first-person" delivered as a structured egocentric observation (the labels-buffer analogue) | the stack's standard; the idea itself says "LLM needs the labels buffer" |

### Design pins, and where each is satisfied

| Pin (`playbooks/make-coworld.md` §Phase 0 / `docs/SPEC.md` §Design pins) | Where |
|---|---|
| Starter by game shape | `coworld-ctf` — real-time loop, new rules written into this repo (title paragraph) |
| Public `Metta-AI/cogame-vizdoom-deathmatch` | §Packaging (created `--public`; `source-resolves` 404s on private) |
| LLM policy **and** scripted baseline day one, one image, env-switched | §Decisions (`PLAYER_PROMPT` vs `PLAYER_SCRIPTED=rusher\|sentry`) |
| Static wasm replay viewer, never a pod | §Viewer (`game.replay_viewer.bundle = "static-replay-viewer"`, `tools/build_replay_viewer.sh`) |
| Starter chrome verbatim, real art | §Viewer (chrome provenance; `chrome_common.js` byte-for-byte but for the named two-line wire patch; the starter's shipped art plus one nano-banana pass) |
| Two name spaces | §The game → Seats (`RED-alpha`…`BLUE-delta` in-game; real policy names spectator-side only) |
| Degrade never hang, play inside 60 % of 1200 s | §Decisions (league typical 154 s, all-LLM worst 530 s, engine stop 660 s, 60 % budget 720 s) |
| `num_agents` in every variant **and** the cert fixture, inside `game_config` | §Packaging — `num_agents: 8`, three times, plus `SMOKE_SEATS=8` |
| Simultaneous decisions as one parallel batch | §Decisions (all live seats in one `curly.makeRequests` batch per turn) |
| Replay bytes self-sufficient | §Server (config + resolved `mapSpec` + joins + per-tick masks + chat records + per-tick hashes + seed) |
| Rune-boundary truncation on every free-text field | §Decisions → Reply schema |
| Maps seeded; anonymous aliases; server-assigned teams (the idea's integrity note) | §Sim module (the `pool` variant's entry is `seed`-derived and the resolved geometry is pinned into the replay); §The game → Seats |

---

## The game

Eight cogs, four red and four blue, in one walled arena with cover, glass windows, med kits and
nothing to capture. Each cog carries a hitscan gun that kills in three hits. You see only what is
inside your **90° forward cone** (out to 1575 px, walls blocking) or your **90 px bubble** — your aim
carries your vision, so you see where you point, not where you walk. Every four and a half seconds
each seat is handed a first-person report of its cog — a sixteen-ray depth strip across the cone, a
labelled list of every contact in it with bearing and distance, its own health and ammo clock, what it
heard, and the scoreboard — and gives that cog one order. A deterministic driver executes the order
tick by tick: it steers, it turns, and it pulls the trigger when a live enemy is in the cone, in range,
with a clear line and no teammate in the corridor. Kill an enemy, take a frag. Die, lose one. After
108 seconds the two teams' net frags are compared and the margin is the score. Nobody is capturing
anything; the only thing that happens in this game is that somebody shoots first.

### Seats, cogs, teams, aliases

- **`num_agents` = 8.** Exactly eight seats, always — in both manifest variants, in the certification
  fixture, and as `SMOKE_SEATS` in `tools/ci/docker_smoke.sh`. **One cog per seat**
  (`cogsPerTeam: 1`), so eight seats drive eight cogs. That is the top of the idea's "Seats: 2-8"
  range and it is the ViZDoom Competition's own eight-player deathmatch. One cog per seat, not
  paintbot's squad of four, because the idea's policy interface is one agent's first-person frame —
  a seat that commands one body can be given the whole first-person vocabulary with no per-cog order
  array, and it is what makes "frags − deaths" a per-seat statement.
- **Teams are assigned by the server, never chosen.** Every variant's `slots[]` array is
  `red, blue, red, blue, red, blue, red, blue`, so slot parity *is* the team: seats **0, 2, 4, 6 are
  RED**, seats **1, 3, 5, 7 are BLUE**, four a side. A seat is told its team in its first observation
  and can neither request nor change it; `closedRoster` is true in every variant, so a joining player
  takes the slot its token names or is refused. This is the idea's integrity ask, satisfied
  structurally rather than by policy.
- **Two name spaces.** In-game a cog is `<TEAM>-<identity>`: `RED-alpha`, `RED-beta`, `RED-gamma`,
  `RED-delta`, `BLUE-alpha`…`BLUE-delta`, from the starter's `IdentityNames` array
  (`roster.nim:64-65`). Those aliases are the only names in an observation, a prompt, an order, a
  shout, a radio line, a replay join record or a sprite label. Each seat's **real policy/player name**
  (`daveey`, `daveey-1`, `Baseline (1)`…) exists only in the replay config's `players[].name`, in
  `results.names`, and in the viewer's scorebug plates and endcard. `showPlayerLabels` is **false** in
  every variant, so no in-board sprite can leak an identity.
- **Colours** are the starter's red and blue kits; there is no per-seat colour, so a spectator follows
  a policy through the scorebug plate, not through the board.

### The arena

The board is **1235 × 659 px in every shipped variant** — the starter's `MapWidth`/`MapHeight`
(`sim_types.nim:982-983`), installed the way the starter installs any map, through `selectCtfMap`
(`arena.nim:3442`), which also sets the fov grid, `ShoutRange = MapWidth div 5 = 247 px` and the
layout clearances from the loaded map. Two variants, two ways of choosing the geometry, **the same
dimensions either way**:

| Variant | `mapPath` | Geometry |
|---|---|---|
| `arena` (league default) | `"arena"` | the starter's hand-tuned symmetric arena, identical every episode |
| `pool` | `"pool"` + `mapSize: "standard"` | the curated 20-seed pool (`src/ctf/map_pool.nim`), entry index = the episode's randomised `seed` (`arena.nim:3388`, `mapPoolIndex: -1`), validated at generation time |

`mapSizeScale("standard") = 1.0` and `scaledGenShell` builds every standard board at exactly
1235 × 659 (`arena.nim:1516-1540`), so `BOARD_ASPECT` is a constant 1.874 in both variants. That is a
load-bearing fact for the viewer (§Viewer → zoom). `mapSize` is pinned to `"standard"` in the `pool`
variant's `game_config` and `tests/test_vzd_manifest.nim` asserts that every shipped variant resolves
to a 1235 × 659 map. `"gen"`, `"arena-large"`, `huge`/`giant`/`colossal` sizes and four-team maps are
deleted (§Sim module).

The **pool** variant is the idea's "maps seeded": the entry is drawn from the episode seed **before
any seat connects**, nothing a seat does can shift it, and the *resolved* geometry is pinned into the
replay's config as `mapSpec` (`sim_config.nim:844-855`) so a later edit to the pool cannot change what
an old replay renders.

**Zones.** For talking about the map, the board is divided once into a **5 × 3 lettered grid**:
columns `A`…`E` left to right (247 px each), rows `1`…`3` top to bottom (220, 220, 219 px). Zone
`A1` is the top-left corner, `E3` the bottom-right. Zone centres are published to every seat in its
first observation and are the only place names in the game. **Red spawns in column A, Blue in column
E** (the starter's rule: Red left, Blue right). `src/vzd/zones.nim` owns the grid, and both the prompt
and the scripted baselines speak it, so an order and a bot use the same vocabulary.

### Weapons, health, respawns — all the starter's, retuned by config only

| Thing | Value | Provenance |
|---|---|---|
| Gun | instant line-of-sight hitscan along the aim, `A` button | starter, unchanged |
| `fireWindupTicks` | 5 (≈0.2 s from trigger pull to shot; aim locks at the pull) | starter default |
| `fireCooldownTicks` | 12 (≈0.5 s between shots) | starter default |
| `gunRange` | **1050 px** on every map | starter, GV34's map-independent range |
| Aim fuzz | the starter's, unchanged — a fully visible target at max range is hit ~80 % of the time, near-certainly closer | starter |
| `hitPoints` | 3 | starter default |
| Friendly fire | **on** | starter default; a team kill costs the killer a frag (§Scoring) |
| `respawnTicks` | **48** (2.0 s), at the team's own spawn pocket, hp reset to 3 | paintbot's value, not ctf's 72 — a deathmatch wants bodies back on the board |
| `lives` | **60** | high enough that a wipe is unreachable (below) |
| Med kits | the starter's, kept: `MedKitRespawnTicks = 30 * ReplayFps` (30 s), placed by the map | starter |
| `aimTurnRate` | 5 brads/tick (≈7°/tick, a full turn in 51 ticks) | starter default |
| `visionConeDeg` | **45** (a 90° beam) | **changed from the starter's 60**: 90° is ViZDoom's default horizontal FOV, and it is the one fidelity nod this fork can honestly make |
| `visionBubble` | 90 px, still line-of-sight-blocked | starter default |
| Vision range | `visionRange() = gunRange * 3 div 2 = 1575 px` | starter, unchanged — you can see further than you can shoot |
| Glass windows | kept: block movement and bullets, transparent to vision | starter (GV15/16) |
| Shout | `say` becomes an in-world shout audible to **both** teams within `ShoutRange = 247 px`, alive `ShoutTicks = 72`, at most one per `ShoutCooldownTicks = 24` | starter, unchanged |

**A wipe is provably unreachable, which is why `EndRuleWipe` is deleted.** A cog cannot die more often
than once per `respawnTicks + 1` ticks, so in a `maxTicks = 2592` game its ceiling is
`2592 div 49 = 52` deaths, and `lives = 60 > 52`. `tests/test_vzd_sim.nim` asserts
`lives > maxTicks div (respawnTicks + 1)` for **every** shipped variant and for the cert fixture, so
the assertion cannot silently rot when a variant is retuned.

### The clock

- **Tick** = 1/24 s (`TargetFps = 24`, unchanged). **Turn** = one order round every
  `turnTicks = 108` ticks (**4.5 s**) — paintbot's cadence, kept, because the control layer's
  navigation, `FieldRefreshTicks` and `HuntMemoryTicks = 72` are all tuned against it.
- **One game** = `maxTicks = 2592` ticks = **24 turns = 108 s of sim**. `maxGames = 1`: deathmatch is
  symmetric, so unlike paintbot's resident/visitor split there is nothing to swap and no reason to pay
  a second game's wall clock.
- Between turns the loop runs uncapped (`fastMode: true`), so the sim costs ~4 s of CPU and the
  episode's wall clock is the 24 LLM turns (§Decisions).
- **Playback** is 1 tick per frame at `ReplayFps = 24`, so a full episode plays for **108 s**. The
  certification fixture is 1080 ticks = **45 s of playback**, which comfortably outlasts
  `viewer_smoke.mjs --soak 10` (§Packaging).

### Turn and tick structure — the exact resolution order

Per **decision turn** `T` (at tick `108·T` of the game, `T` from 0), in this order:

1. `engine.ctl.observeEnemies(sim)` refreshes every cog's intel window (the starter's
   `control.nim:248`), so the observation and the driver see the same `knownEnemy` state.
2. The engine snapshots the world and builds an observation for every **live seat** — a seat whose cog
   is currently dead still gets one (it respawns in ≤ 2 s and its next order matters), so all eight
   seats are live for the whole game unless they never connected.
3. All LLM seats' requests go out as **one parallel batch** (`curly.makeRequests`, the starter's
   `decide.nim:418-425` shape), attempt-1 deadline `attempt1Ms = 8000`. Scripted seats compute
   locally, in microseconds, and consume no request.
4. Every seat that timed out, errored, returned non-JSON, or returned no usable order is retried
   **once**, again as one batch, `retryMs = 3000`. A provider 429 with no other candidate model skips
   the retry (it cannot land) and falls straight through (`decide.nim:462-470`).
5. A seat still without a usable reply takes the **`rusher`** scripted order for its cog, and a
   `fallback` record is written (§Decisions → degrade).
6. Orders are installed in ascending seat index. A field that does not validate is **repaired**, never
   dropped: an unknown `intent` becomes `hunt`; an unresolvable `at` falls back to `to`; an
   out-of-board `to` is clamped; a reply that names no order at all keeps **last turn's** order (else
   `rusher`'s) and counts in `ordersRejected`.
7. `say` (≤ 10 runes) becomes an in-world **shout** at the cog's position — the starter's mechanic,
   verbatim, via `sim.applyShout` (`server.nim:1962`): audible to **anyone of any team** within 247 px,
   drawn as a speech bubble, alive for 72 ticks, hashed. Shouting gives your position away; that is the
   point. `radio` (≤ 96 runes) is the **team** channel: delivered to the three teammates' next
   observation and drawn in the spectator feed, never audible in-world. `notes` (≤ 160 runes) is
   private to the seat and echoed back to it next turn.
8. The inter-batch wall-clock floor is applied **before** the batch starts (§Decisions → cadence).

Then, for each of the next 108 ticks, in this order — this is the starter's `sim.step`
(`sim.nim:3975`) with the deleted mechanics removed and nothing reordered:

1. `tick += 1`.
2. **Roster transitions** — leaves are applied inside the deterministic step (the starter's rule), so
   a mid-match disconnect re-derives identically at playback.
3. **Lobby / game-over branches.** In `GameOver` the `gameOverTimer` counts down and the episode
   settles; in `Lobby` `stepLobby` runs. Neither is reached during play.
4. **Compile actuator masks.** For every cog in ascending index the control layer turns its standing
   order into a Sprite v1 mask (§Decisions → the driver). The **masks**, not the orders, are what the
   replay records (`server.nim:1990-1993`).
5. **Cooldowns.** `fireCooldown` and `fireWindup` decrement; a windup reaching 0 arms this tick's shot
   with the aim that was locked at the trigger pull.
6. **Aim.** Each cog's `aimBrads` rotates by `±aimTurnRate` if `B`/`Select` is held. Aim is independent
   of movement.
7. **Movement**, ascending index, the starter's integer fixed-point integrator (`applyInput`) with
   per-axis slide and cog-cog collision/bounce. Everyone moves before any shot resolves, so there is no
   processing-order advantage.
8. **Trigger.** A fresh `A` press with `canFire` starts a windup; every windup that expires this tick
   is collected and `resolveSimultaneousFire` resolves them **all at once** against the post-movement
   snapshot — the starter's rule, kept, which is what makes a mutual kill a genuine trade.
9. **Damage, kills, deaths.** Each hit removes one hit point (`recordDamage`); at zero the cog dies,
   `recordDeath(victim)` fires, and the shooter gets `recordKill` if the victim was an enemy or
   `recordTeamKill` if it was a teammate (`roster.nim:606-631`, all three kept verbatim). A `kill`
   broadcast event carries `killer`, `victim`, `tk` (team kill) and the starter's `amb`/`trade`
   attribution fields.
10. **Med kits** — `updateMedKits()` respawn timers, then `tryPickupMedKits(cog)` in ascending index.
    Nothing else is picked up: grenades, shields, spray cans, barriers and hearts do not exist here.
11. **Respawns** — `respawnPlayers()`: a cog whose `respawnTicks` expired returns at its team's spawn
    pocket with hp 3 and its aim pointed at the enemy side.
12. **Frag accounting** — `net[c] = frags[c] − teamFrags[c] − deaths[c]` and the two team totals are
    recomputed from the per-cog counters (pure derivation, no separate state). If the team lead changed
    hands and at least `LeadThrottleTicks = 48` ticks have passed since the last announcement, a `lead`
    event fires.
13. **Streaks** — a cog reaching 3, 5 or 8 frags without dying emits a `streak` event; the counter
    resets on death. Cosmetic, hashed only through the frag/death counters it reads.
14. **Shout expiry** and cosmetic FX pruning (`pruneAgedFx`) — the starter's, unchanged.
15. **End evaluation** — `checkDeathmatchEnd()`: `gameTicksElapsed() >= maxTicks` finishes the game
    with `EndRuleFullTime` (§End conditions). This proc **replaces** the starter's `checkWinCondition`
    (capture/wipe) and `checkKothEnd`; there is no mercy rule and no wipe rule.

### Scoring formula and sign

Per cog `c`, from counters the starter already maintains:

```
frags[c]      = kills of ENEMY cogs by c                     (roster.nim recordKill)
teamFrags[c]  = kills of OWN-TEAM cogs by c                  (roster.nim recordTeamKill)
deaths[c]     = every death of c, whatever the cause         (roster.nim recordDeath)
net[c]        = frags[c] - teamFrags[c] - deaths[c]
```

`net[c]` is literally the idea's **frags − deaths**, with a team kill charged to the killer as a lost
frag (the Quake/ViZDoom convention, and the only thing that stops friendly fire from being a free way
to deny an enemy a frag). Team totals and the margin:

```
teamNet[T]    = sum of net[c] over the four cogs of team T
margin(T)     = teamNet[T] - teamNet[other(T)]               (exactly antisymmetric)
DecisiveMargin = 12
scorePermille[s] = gameScorePermille(margin(team(s)), DecisiveMargin)
                 = 500 + clamp(margin * 500 div 12, -500, +500)
scores[s]     = scorePermille[s] / 1000.0                    in [0.0, 1.0]
win[s]        = scorePermille[s] > 500
```

`gameScorePermille` is the starter's own antisymmetric helper (`paint.nim:281`), reused unchanged,
which is what guarantees a red seat's score and a blue seat's score sum to **exactly 1.000** for every
legal margin. **Sign: higher is better.** `1.000` is a 12-frag rout, `0.500` a dead-even game, `0.000`
the reverse. `DecisiveMargin = 12` because a 108-second 4v4 at 3 hit points and a 0.5 s fire cooldown
produces roughly 20–35 total frags in the tuning sweep, so a 12-frag net lead is a decisive win and
smaller leads stay on the linear part of the curve where an Elo ladder can read them.

**The league ranks by `results.scores[s]`.** `results.win[s]` is `scorePermille[s] > 500`.

**Tiebreak: there is none, deliberately.** A margin of exactly 0 is a draw: all eight seats score
`0.500` and every `win` is false. A manufactured tiebreak (fewer deaths, first frag) would be a second
scoring rule the idea does not pin, it would break the exact zero sum, and Elo handles draws natively.
The endcard says `DRAW` and the seat table is *ordered* — cosmetically only — by `net`, then `frags`,
then fewer `deaths`, then alias.

**Everything else is measured and shown, never scored**: per-seat `frags`, `teamFrags`, `deaths`,
`net`, `damageDealt`, `damageTaken`, `shotsFired`, `shotsHit`, `medkits`, `longestStreak`. `damageDealt`
and `damageTaken` are recorded specifically to satisfy the idea's "ganging detectable from the damage
graph" note: they are per-seat HP totals, so a replay's damage graph is reconstructable from
`results` alone.

`tests/test_vzd_scoring.nim` asserts over 500 randomised end states that `margin(Red) == -margin(Blue)`
exactly, that `scorePermille[red] + scorePermille[blue] == 1000` exactly, that `scores ∈ [0, 1]`, and
that an all-zero margin leaves every `win` false.

### End conditions and legal `results.reason` values

The episode ends at the first of: **full time**, the **wall-clock stop**, or a **fault**.

`results.reason` is the starter's closed enum (`sim_types.nim:877-879`); **exactly these three values
are legal** and the game emits nothing else:

- **`complete`** — `gameTicksElapsed() >= maxTicks` (2592). `results.endRule = "full_time"`. Settles
  after the `gameOverTicks = 240` display hold, then writes artifacts and exits 0. The healthy value.
- **`deadline`** — the engine's own wall-clock stop (`server.nim:1407-1417`, kept) at
  `wallClockBudgetSeconds = 660`. The engine stops at the current tick and settles with the **real
  frag counters so far**: `margin` is computed over the ticks actually played, `results.finalTick`
  records where it stopped, artifacts are written, exit 0. `results.endRule = "wall_clock"`. A
  deadline episode is therefore still rankable and still exactly zero-sum. **Declared acceptable** for
  SPEC §Definition of done check 4; the budget guard below exists so it should never fire.
- **`fault`** — an unexpected exception in the sim or the loop, caught (`server.nim:2039-2047`, kept).
  The episode is settled from the last completed tick, `results.endRule ∈ {"sim_fault", "host_error"}`,
  `results.stopDetail` names it (≤ 200 runes, rune-truncated), artifacts are still written, exit 0. It
  is a defect: `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it.

`results.endRule` is therefore also a closed enum: **`full_time | wall_clock | sim_fault |
host_error`** — four of the six values the starter's schema declares. **`mercy` and `wipe` are
deleted** along with the mechanics that produced them: mercy compared hill leads (deleted), and a wipe
is unreachable because `lives = 60` exceeds the death ceiling (§Weapons). `tests/test_vzd_engine.nim`
asserts that no episode over 200 seeds ever produces either string.

**Budget guard.** At the start of each turn, if
`elapsed + 2 × max(turnBudgetMs, effectiveSpacingMs) / 1000 > wallClockBudgetSeconds`, the LLM is
switched off for every remaining turn (all seats fall to `rusher`, microseconds per turn), the
remaining ticks run at full speed, and the episode still ends `complete` / `full_time`. A
`budget_guard` record names the turn it fired. This is the starter's guard at `decide.nim:341-345`
with **one named edit**: the starter compares against `turnBudgetMs` alone, which under-counts when
the rate floor (17.1 s at eight LLM seats) is larger than the turn budget (12 s).

**A seat that never connects, disconnects, or fails every decision does not end the episode**: its cog
is driven by `rusher` and the game runs to its natural end with `deadSeats[s] = true`. Nothing a
player container does can stop the clock — `lobbyJoinTimeoutTicks = 2400` (100 s) bounds the lobby and
the per-turn deadlines bound everything after it.

---

## Decisions: LLM with scripted fallback

**Both champions are LLM prompt policies; both fillers are scripted baselines; one image, switched by
env.** `PLAYER_PROMPT=<strategy text>` makes a seat an LLM seat. `PLAYER_SCRIPTED=<name>` with
`name ∈ {rusher, sentry}` makes it a scripted seat. A seat that sets neither is
`PLAYER_SCRIPTED=rusher` — the starter's "anything unrecognised is the published default" rule
(`baselines.nim:53-60`). A scripted policy seated as a champion is a failure state.

### Where the decision happens

**In the game server, not the player container** — the starter already works this way
(`src/ctf/decide.nim` + `src/ctf/llm.nim`), and it is the only shape that works on this platform: the
`anthropic_api_key` coworld secret is injected into the **game** pod
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/vizdoom-deathmatch/anthropic_api_key` —
the hive 2026-08-23 scar), phase 60 greps the **game** log for `falling back` / `LLM provider is
unavailable`, and `docker_smoke.sh` forwards `ANTHROPIC_API_KEY` to the game container only. No
`USE_BEDROCK` flag is needed on the policies, because the player pod makes no LLM call.

`src/vizdoom_deathmatch_player.nim` is `src/paintball_player.nim` forked with **no behaviour change**:
read `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dial with bounded retries, send —
and **re-send for the first ~10 s of received frames** (the paintball 2026-08-25 slot-sequential-join
scar) — the registration blob

```json
{"type":"register","policy":"<label>","prompt":"<PLAYER_PROMPT or empty>","scripted":"rusher"|"sentry"|null}
```

with `prompt` rune-truncated at `MaxPromptRunes = 4000` and `policy` at `MaxPolicyLabelRunes = 48`,
then acknowledge frames until the socket closes, **exiting 0 on a dead socket** (the raid 0.1.3
close-frame race). The `0x85` Player Ready send is kept and is legitimate for the same reason it is in
the starter: this seat sends no inputs at all — every actuator mask comes from the control layer.

`src/vzd/llm.nim` is `src/ctf/llm.nim`, forked with no behaviour change:

- Credentials in order: **Bedrock sidecar** (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` +
  `AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION`, default `us-west-2`) →
  `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` → **none**, in which case the client is
  `disabled = true` and every turn falls back instantly with no network wait, so offline certification
  finishes in seconds.
- Bedrock model candidates in order, `BEDROCK_MODEL` pins one:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`, then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
  `tryNextBedrockModel` on 401/403 "Model access is denied" and on 429.
  **`us.anthropic.claude-sonnet-4-6` is deliberately not a candidate** (it times out on every sidecar
  call — raid round 2, 2026-08-23).
- `maxOutputTokens = 900` (400 truncates Haiku mid-object). **No `output_config.effort`** when the
  model string contains `haiku` or `4-5`. Bedrock bodies carry
  `anthropic_version: "bedrock-2023-05-31"`.
- A system prompt demanding the reply **begins with `{`**; `extractJsonObject` (outermost balanced
  `{…}`, fence-tolerant, prose-tolerant — `directives.nim:102`) and `truncateRunes` / `sanitizeSay`
  (`directives.nim:61,70`) unchanged.

### Cadence, batching, and the wall-clock arithmetic

One turn every **108 ticks**; **24 turns per episode**. At each turn the server builds every LLM
seat's request body and issues them as **ONE PARALLEL BATCH** — never sequentially; this is a
simultaneous-decision game and eight serial calls would multiply the wall clock by eight for nothing.
At most 8 calls in flight; at most `24 × 8 × 2 attempts = 384` calls per episode including retries.

**The rate floor is derived from the number of LLM seats, not fixed.** The Bedrock sidecar caps **30
requests per minute per episode**, and eight seats in one batch is eight requests. The starter's
`turnSpacingMs` is a flat floor between batch *starts* (`decide.nim:382-391`); this fork keeps that
mechanism and adds one named edit — the floor actually used is

```
effectiveSpacingMs(n) = max(turnSpacingMs, (60_000 * n + RateCap - 1) div RateCap)
RateCap = 28 requests/minute        (30 with two spare)
n       = LLM seats being called this turn
```

so `n = 8 → 17_143 ms`, `n = 2 → 5_000 ms` (the configured floor binds). A league round seating two
prompt champions and six scripted fillers therefore runs at 5 s spacing; a hypothetical all-LLM
episode throttles itself to 17.1 s and still fits. A **rolling 60 s request counter** backs it up: if
issuing the next batch would push the trailing-60 s count above 28, the seats that would exceed it
skip the call for that turn and take the `rusher` order with `cause = "rate_guard"`. Bounded, logged,
never a sleep on the critical path (the raid round 2 sidecar-throttle scar).

```
attempt1Ms                           8.0 s     (curl floors CURLOPT_TIMEOUT to whole seconds)
retryMs                              3.0 s
turnBudgetMs                        12.0 s     (monotonic deadline around the whole turn)
turnSpacingMs (configured floor)     5.0 s  -> effective 5.0 s at 2 LLM seats, 17.143 s at 8

24 turns x 5.000 s   (league: 2 prompt champions + 6 scripted fillers)   = 120 s
24 turns x 17.143 s  (worst case: all eight seats are LLM)               = 411 s
2592 ticks x 8 cogs: fixed-point motion, hitscan, shadowcast, fastMode   =   4 s
lobby / connect wait (typical)                                           =  15 s
lobby cap (lobbyJoinTimeoutTicks 2400 = 100 s at 24 fps)                 = 100 s
gameOverTicks 240 hold under fastMode + results + replay write           =  15 s
                                                                         -------
typical league episode          120 +  4 +  15 + 15                      = 154 s   < 720 s
worst all-LLM, typical lobby    411 +  4 +  15 + 15                      = 445 s   < 720 s
absolute worst (lobby cap)      411 +  4 + 100 + 15                      = 530 s   < 660 s stop
engine hard stop wallClockBudgetSeconds                                  = 660 s -> "deadline"
60 % of the assumed episodeTimeoutSeconds (1200 s)                       = 720 s
platform kill                                                            = 1200 s
```

Every shipped variant's `wallClockBudgetSeconds` is ≤ 660 and `tests/test_vzd_manifest.nim` asserts it,
together with `24 × effectiveSpacingMs(num_agents) / 1000 + 134 ≤ 660` for every variant — so a future
retune of `turnTicks` or `maxTicks` that blows the budget fails CI instead of the league.
`fastMode: true` in every variant.

### Degrade, never hang

Every wait is bounded: the two batch deadlines, the outer `turnBudgetMs`, the rate guard,
`lobbyJoinTimeoutTicks`, mummy's socket timeouts on the serve thread (which runs independently of the
game loop, so a 12 s LLM stall cannot drop a connection or stall `/healthz`), the 660 s engine stop,
and the `gameOverTicks` hold before exit — kept so `/healthz` and `/global` keep answering for a
bounded grace after artifacts are written (the lantern 0.1.3 `/global` ping scar).

On a seat's timeout or parse failure: **retry once** in the next batch; on the second failure that
seat's order for that turn becomes the **`rusher`** scripted order (the same proc the `rusher`
baseline uses — imported, never duplicated), and a `fallback` record is written with
`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard, budget_guard,
disconnected}`. `results.fallbackTurns[s]` counts them.

`rusher` — not `sentry` — is the fallback and the unregistered default **because a degraded episode
must still be a legible deathmatch**: eight sentries hold eight posts and produce a 0-0 draw with an
empty kill feed, which is a useless replay and a useless CI smoke. `rusher` walks at the contested
zone and shoots, so even a fully-degraded episode has frags in it.

**No failure mode leaves a cog unactuated.** The control layer always has an order: this turn's, else
last turn's, else `rusher`'s (`server.nim:1978-1988`, kept). A seat that never connects is reported
once to `COGAME_PLAYER_FAILURE_URI` with the platform's **closed** payload — exactly
`{"message", "failed_policy_index"}`, nothing else.

**The episode settles early rather than overrunning**: the budget guard drops every seat to scripted
play the moment two more full turns would not fit, and the remaining ticks then run at sim speed
(seconds), so the episode still ends `complete` / `full_time`.

### Per-seat observation: exactly what is visible and what is hidden

The guiding line: **a seat sees what its cog's eyes see, plus what its team says.** There is no
free-cam and no map-wide enemy list — the fog is the game. Structurally this is ViZDoom's *depth
buffer plus labels buffer*, written as text: sixteen ray distances across the cone, and one labelled
row per thing the cone or the bubble actually contains.

**Visible to a seat.**

- **The map, once, at its first turn** — board dimensions, the 15 zone ids with their centres and a
  one-word terrain word per zone (`open` / `cover` / `corridor`, derived at load from the zone's wall
  fraction), the two spawn-pocket anchors, and the med-kit spawn points. The starter's own rule is
  that the *terrain* is public knowledge and only *bodies* are fogged; keeping that means a seat can
  navigate and the driver's flow field is not lying to it.
- **The depth strip** — `rays`: **16** entries spanning the cone from −45° to +45° in 6° steps
  (bearings relative to the cog's own aim, negative = left). Each entry is
  `[bearing_deg, wall_dist_px, glass_dist_px]`, with `-1` meaning "nothing within `visionRange`". This
  is produced by `marchRays` in `src/vzd/egoview.nim` — **the same proc the viewer's first-person
  inset uses** (§Sim module), so the number the model reads and the wall the spectator sees can never
  disagree.
- **Contacts** — one row per entity the cog can legitimately see right now (inside the cone with a
  clear line, or inside the 90 px bubble), plus every enemy this cog saw within the last
  `HuntMemoryTicks = 72` ticks tagged `ticks_ago` with the position **as it was when seen** (the
  starter's `ControlState.knownEnemy` intel window, `control.nim:297`). Each row:
  `{"label": "enemy"|"ally"|"medkit", "id": "<alias or null>", "bearing": <deg, aim-relative>,
  "dist": <px>, "zone": "<id>", "hp": <0-3 or null>, "ticks_ago": <int>}`. `label` is exactly ViZDoom's
  labels-buffer object class; `bearing`/`dist` are the depth buffer's polar coordinates.
- **Your own cog** — `pos`, `aim` (brads **and** compass point), `zone`, `hp`, `alive`,
  `respawn_in_ticks`, `fire_ready` (cooldown/windup), `frags`, `deaths`, `streak`, your last order and
  its `result`, and your `notes` echoed back.
- **Your three teammates** — alias, `pos`, `hp`, `alive`, `zone`, and their last `radio` line. This is
  a **documented divergence** from the starter, whose cogs cannot see their own team (`README.md`:
  "teammates are NOT [visible] (no team radio)"): four independent policies on one team, each driving
  one body at a 4.5 s cadence, cannot play team deathmatch blind, and the idea's integrity note
  *requires* team DM. Enemies stay fogged exactly as the starter fogs them.
- **What you heard** — every shout within 247 px of your cog in the last 72 ticks: the shouting team,
  the text, the position, `ticks_ago`. This is how a careless enemy gets found.
- **The scoreboard, public to both teams** — `your_team`, `their_team` net frags, `margin`,
  per-alias frags/deaths for **your own team only**, total ticks left, turn `n/24`.

**Hidden.** Every other seat's order, notes, radio and prompt; every seat's real player name, policy
name and kind; the enemy team's per-cog frag/death breakdown (only its team total is public); enemy
positions outside your cone, bubble and 72-tick memory; enemy aim and intent; the seed; the unselected
pool entries; and the map's own `mapSpec` document (a seat gets zones, not wall rectangles — a
per-pixel wall list is neither legible to a model nor what a first-person agent has).

The observation is a JSON object appended to the user message and is mirrored (minus `your_notes`)
into the replay's `directive` record, so the replay explains every decision.

```json
{
  "you": "RED-beta",
  "team": "RED",
  "turn": 7, "turns": 24,
  "clock": {"played_s": 31, "left_s": 77},
  "map": {"w": 1235, "h": 659,
          "zones": [{"id":"A1","c":[123,110],"t":"cover"},{"id":"B1","c":[370,110],"t":"open"},
                    {"id":"C2","c":[617,330],"t":"corridor"},{"id":"E3","c":[1111,549],"t":"cover"}],
          "your_spawn": "A2", "their_spawn": "E2",
          "medkits": [{"at":[617,120],"zone":"C1"},{"at":[617,540],"zone":"C3"}]},
  "you_at": {"pos": [402,318], "aim": 8, "facing": "E", "zone": "B2",
             "hp": 2, "alive": true, "respawn_in_ticks": 0, "fire_ready": true,
             "frags": 2, "deaths": 1, "streak": 1},
  "rays": [[-45,318,-1],[-39,341,-1],[-33,377,-1],[-27,441,-1],[-21,612,-1],[-15,905,-1],
           [-9,1204,-1],[-3,-1,742],[3,-1,742],[9,1188,-1],[15,884,-1],[21,598,-1],
           [27,430,-1],[33,369,-1],[39,334,-1],[45,312,-1]],
  "contacts": [
    {"label":"enemy","id":"BLUE-alpha","bearing":-4,"dist":688,"zone":"C2","hp":3,"ticks_ago":0},
    {"label":"enemy","id":"BLUE-delta","bearing":22,"dist":915,"zone":"D3","hp":1,"ticks_ago":41},
    {"label":"medkit","id":null,"bearing":-31,"dist":214,"zone":"B1","hp":null,"ticks_ago":0}
  ],
  "team_net": [
    {"id":"RED-alpha","pos":[268,140],"hp":3,"alive":true,"zone":"A1","radio":"holding the north lane"},
    {"id":"RED-gamma","pos":[311,520],"hp":0,"alive":false,"zone":"A3","radio":"down in A3, they came from C3"},
    {"id":"RED-delta","pos":[455,330],"hp":3,"alive":true,"zone":"B2","radio":""}
  ],
  "heard": [{"team":"BLUE","text":"push mid","at":[640,330],"ticks_ago":18}],
  "score": {"you": 6, "them": 4, "margin": 2,
            "your_team": [{"id":"RED-alpha","f":3,"d":1},{"id":"RED-beta","f":2,"d":1},
                          {"id":"RED-gamma","f":1,"d":3},{"id":"RED-delta","f":2,"d":1}]},
  "your_last_order": {"intent":"hunt","at":"C2","result":"chasing"},
  "your_notes": "hold the B2 doorway, they funnel through C2"
}
```

Field rules. `aim` is brads (256 per turn, 0 = east, counter-clockwise); `facing` is the nearest of
the eight compass points, because a model reasons better about "NE" than about "32". `bearing` is
**degrees relative to your own aim**, negative left, positive right — an egocentric quantity, never a
world angle. `margin` is `teamNet[you] − teamNet[them]`, so "higher is better for me" always holds.
`result` is one of `moving | arrived | chasing | holding | firing | no_route | dead | respawned |
unknown_target` — the driver's honest report of how the previous order ended, which is what lets a
seat recover from a race it could not see. `zones` is always all fifteen entries in id order; the
excerpt above is abbreviated for this note only.

### Reply schema and per-field caps

```json
{"intent": "hunt", "at": "C2", "to": [617, 330], "face": [700, 330],
 "say": "mid", "radio": "BLUE-alpha is in C2 at 3hp, I take the north door",
 "notes": "hold B2 next turn if this fails"}
```

| Field | Type | Cap / domain |
|---|---|---|
| `intent` | string | **≤ 12 runes**; enum `hunt` \| `hold` \| `move_to` \| `flank` \| `retreat` \| `regroup`, lower-cased, hyphens/spaces normalised to `_` before matching. Anything unknown is repaired to **`hunt`** — always actuatable, always something to do |
| `at` | string | **≤ 12 runes**; a published **zone id** (`A1`…`E3`) or a **contact alias** (`BLUE-delta`). If present it **wins over** `to` and resolves to the zone centre or the contact's last known position. Unresolvable → repair to `to`, count `ordersRejected`, report `unknown_target` |
| `to` | `[x, y]` | two numbers (int, float or numeric string — the starter's tolerant `readPoint`), clamped into `[0, 1234] × [0, 658]` |
| `face` | `[x, y]` | optional; the bearing the driver holds once it arrives (used by `hold`). Clamped like `to` |
| `say` | string | **≤ 10 runes** (`MaxSayRunes = ShoutMaxChars`, the starter's cap, unchanged) — an **in-world shout**: heard by *both* teams within 247 px, drawn as a speech bubble |
| `radio` | string | **≤ 96 runes** (`MaxRadioRunes`, new) — the **team** channel: delivered to your three teammates' next observation, drawn in the spectator feed, never audible in-world |
| `notes` | string | **≤ 160 runes** (`MaxNoteRunes`, the starter's cap, unchanged) — private, echoed to this seat only next turn |
| whole reply | bytes | **≤ 4096** read from the provider before parsing |
| `PLAYER_PROMPT` | string | **≤ 4000 runes** (`MaxPromptRunes`) at registration |
| serialized `directive` record | runes | **≤ 900** (`MaxDirectiveRunes`), shrunk note-first by `boundedDirectiveRecord` |

`MaxSayRunes` stays at the starter's 10 **because the in-world speech bubble is kept verbatim** — the
chunky 9 px shout font draws a 10-character bubble and widening it would mean rewriting the bubble
renderer. Coordination lives in `radio`, which has no renderer constraint. That split is also good
design: the cheap channel is loud and gives your position away, the expensive one is private.

**Every string that lands in the replay — `say`, `radio`, `notes`, the policy label, `stopDetail`,
recorded error text — is truncated on RUNE boundaries** via the starter's `truncateRunes` /
`runeSubStr` (`directives.nim:61`), never by byte index. Byte truncation is what makes a replay that
renders in a browser fail a strict UTF-8 parser; `tests/test_vzd_replay.nim` asserts it with 4-byte
emoji sitting exactly on every cap.

Unknown top-level keys are ignored. A reply with a valid `say`/`radio` but no `intent` is **usable**:
the cog keeps its standing order and the line is delivered. A reply that is not a JSON object is a
parse failure and takes the retry. The starter's tolerant `cogs: [...]` array form is still accepted —
its single entry is read as the flat order — so a model that copies paintbot's shape is not punished.

### System prompt (fixed, identical for both champions)

```
You are ONE marine in an eight-cog team deathmatch: four RED against four BLUE on one
walled arena. You are told which side you are on; you cannot change it. Every 108 ticks
(4.5 seconds) you give your marine ONE order and a deterministic driver carries it out
until you change it: it walks, it turns, and it pulls the trigger by itself whenever a
live enemy is inside your cone, in range, with a clear line and no teammate in the way.

WHAT YOU SEE
You do NOT see the whole board. You see a 90-degree cone along your AIM out to 1575px,
plus a 90px bubble around you. Walls block both; glass windows do not.
- "rays" is your depth strip: 16 distances across the cone, left to right, in your OWN
  bearings (negative = left of your aim). -1 means nothing within sight.
- "contacts" is what your eyes actually resolved: enemies, teammates and med kits, each
  with a bearing relative to your aim, a distance, a zone and (for cogs) hit points.
  An enemy with "ticks_ago" above 0 is a MEMORY, not a sighting - it has moved.
- The map itself is public: 15 lettered zones A1..E3 (A = your left edge on RED,
  E = the right edge), each with a centre and a terrain word.

WEAPONS
Hitscan gun, 1050px range, kills in 3 hits, 0.5s between shots, and a 0.2s wind-up
during which your aim is LOCKED - a target that steps behind cover survives the shot.
Aim is fuzzed: a distant target is hit about 4 times in 5, a near one almost always.
FRIENDLY FIRE IS ON and killing a teammate costs you a frag. Med kits restore health
and respawn 30 seconds after they are taken. You respawn 2 seconds after dying, at your
own spawn, at full health.

SCORING - the only thing that counts
Your team's score is (enemy kills) - (teammate kills) - (deaths), summed over your four
marines, minus the same number for theirs. A 12-frag lead is a maximum win. Trading one
for one is worth nothing. Dying is exactly as expensive as a frag is valuable, so a
fight you are going to lose is worth walking away from.

YOUR ORDER (one per turn; your marine keeps it until you change it)
  {"intent":"hunt","at":"BLUE-alpha"}    go to that contact and kill it
  {"intent":"hold","at":"B2","face":[700,330]}  stand there, watch that bearing, shoot
  {"intent":"move_to","at":"C2"}         walk there, gun up
  {"intent":"flank","at":"D1"}           walk there the long way, through an EMPTY row
  {"intent":"retreat"}                   fall back to your own spawn and hold
  {"intent":"regroup"}                   go to where your living teammates are
"at" takes a zone id (A1..E3) or a contact's alias. "to":[x,y] works too; "at" wins.

TALKING
"say" is at most 10 characters and is SHOUTED OUT LOUD: everybody within 247px hears it
and sees where it came from, INCLUDING THE ENEMY. "radio" is up to 96 characters and
only your three teammates hear it, next turn. "notes" comes back to you and nobody else.

REPLY FORMAT
Reply with ONE JSON object and NOTHING else. Your reply MUST begin with the character {
and end with }. No prose, no markdown, no code fences.
{"intent":"hunt","at":"C2","say":"<=10 chars","radio":"<=96 chars","notes":"<=160 chars"}
```

### Champion #1 — `vzd-pointman` (owner **daveey**), `PLAYER_PROMPT`

```
Win the map, not the duel. Every turn, decide from "contacts" and your teammates' radio
where the enemy MASS is, and put three marines on one side of it while the fourth holds
the lane behind you.
Turn 1: radio which ROW you take (1 = north, 2 = mid, 3 = south) and "move_to" the zone
one column short of the middle in that row. Never open with "hunt" - there is nothing to
hunt yet and walking at the centre in the open is how the first two frags happen to you.
When a contact appears with ticks_ago 0 and hp 3 at more than 700px, do NOT hunt it:
"hold" where you are and face it. Your gun reaches 1050px, your aim is fuzzed at range,
and a marine standing still with the enemy walking into the cone wins that exchange.
When a contact appears with hp 1 or 2, or with ticks_ago 0 inside 400px, "hunt" it and
say "on it" - a wounded marine is a free frag and a free frag is two points of margin.
When YOUR hp is 1: "retreat" if no enemy is inside 400px, otherwise the nearest med kit
by "move_to" - dying gives them the point you were about to take.
When a teammate radios that they are down, do not walk into the zone that killed them
alone: "regroup" for one turn, then push that zone with whoever is with you.
When you lead by 6 or more with under 30 seconds left, every marine goes "hold" in your
own half facing the middle. A lead is defended by not dying.
Use "radio" every single turn: your zone, your hp, and the last enemy zone you saw.
Use "say" almost never - it tells them where you are.
```

### Champion #2 — `vzd-crossfire` (owner **daveey-1**, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `PLAYER_PROMPT`

```
Own two angles on one doorway and let them walk into it.
Turn 1: pick the CORRIDOR zone nearest the middle of the map from the zone list and
radio it as the killbox. "flank" to a zone that has line of sight into it from a
different row than the one your teammates radioed - never the same approach twice, and
never the straight line, because "flank" routes you through an empty row and the
straight line is where their cone already is.
Then "hold" with an explicit "face" pointed at the killbox centre and STAY. A held
marine has its aim already on the doorway; a moving marine has to turn first, and 0.2
seconds of wind-up is the whole fight. Re-issue "hold" every turn until something
changes.
Change on exactly three triggers: (1) a contact at ticks_ago 0 with hp 1 inside 500px -
"hunt" it, it is a free frag; (2) two turns with no contact at all - the killbox is
being avoided, so "flank" one zone further into their half and hold the next doorway;
(3) your hp at 1 - "retreat", heal on the way if a med kit is in contacts, come back to
the same post.
Never chase a full-health enemy across the middle: you would arrive winded, in their
teammates' cones, and give them the trade. Never fire at a contact whose ticks_ago is
above 0 - it is a memory, and the driver will not shoot at nothing anyway.
Radio your post zone and your facing every turn so your teammates can take the OTHER
angle on it, not the same one.
```

### The driver (deterministic, shared by every policy)

`src/vzd/control.nim` — the starter's `control.nim`, retargeted. It runs once per cog per tick and is
the **only** producer of input masks. It sits **outside** the determinism boundary exactly as the
starter's does (the recorded masks, not the orders, are what the replay re-plays), so it may use
ordinary floating-point navigation maths.

Kept verbatim from the starter: the `NavCell = 12` nav grid, `buildNavGrid`, `computeField` (BFS flow
field), `fieldFor` with `FieldRefreshTicks = 12` and `MaxCachedFields = 64`, `navSteer`,
`ArriveRadius = 20`, `AimDeadBrads = 4`, `FireAimBrads = 24`, `bradsErr`, `StuckTicks = 8`
obstacle-sliding, and `observeEnemies` / `knownEnemy` with `HuntMemoryTicks = 72`. Deleted: the paint
probes (`PaintProbeSteps`), the spray-arc branch and the hill goals.

| Intent | What the driver does | Finishes with |
|---|---|---|
| `hunt` | flow-field nav to the target (the named contact's last known position, else the resolved point); on arrival it sweeps ±32 brads around the approach bearing | `chasing` → `arrived`; `no_route` if the field cannot reach |
| `hold` | nav to the point, then stop dead and hold `face` if given, else sweep ±32 brads around the bearing to the map centre; zero d-pad from then on | `arrived` then `holding` |
| `move_to` | flow-field nav to the point; aim along velocity unless `face` is given; stop inside `ArriveRadius` | `moving` → `arrived` |
| `flank` | nav to the point **via a waypoint**: the zone centre of row 1 or row 3 (whichever has had no enemy contact in the last 72 ticks; if both are contested, the one further from the most recent contact) in the column midway between the cog and the target. Inside `ArriveRadius` of the waypoint the goal becomes the target | `moving` → `arrived` |
| `retreat` | nav to the team's own spawn-pocket anchor (`gameMap.teamAnchor(team)`), then `hold` facing the map centre. **Hold fire suppressed only while more than 300 px from the anchor**, so a retreating marine still defends itself | `moving` → `holding` |
| `regroup` | nav to the centroid of the living teammates' positions, snapped to the nearest walkable nav cell; then `hold` facing the map centre | `moving` → `holding` |

Any intent whose cog is **dead** emits the zero mask and reports `dead`; the tick it respawns it
reports `respawned` and resumes its standing order. No intent can leave a cog unactuated: an
unreachable target degrades to `hold` on the current bearing, which is a legal mask.

**The trigger rule (the one named edit to `compileMask`).** `A` is pressed on a tick iff **all** of:
the cog is alive; `fireCooldown == 0` and no windup is in flight; a **live enemy** is known with
`ticks_ago == 0` (seen *this* tick, never a memory); its distance is ≤ `gunRange` (1050); the aim error
to it is ≤ `FireAimBrads` (24 brads ≈ 34°); `lineOfSightClear` to it; **and no teammate's body box
(±`PlayerHalf`) intersects the bullet corridor between the cog and the target** — the starter's own
corridor test, reused. There is no suppressive fire and no firing at memories, which bounds
`shotsFired` and makes `shotsHit / shotsFired` a meaningful accuracy number. Friendly fire is on in the
*sim*; the driver simply refuses to cause it, so a team kill in a replay is always an accident of
movement (someone stepped into the corridor after the aim locked), never a bot bug.

### Scripted baselines (both shipped as fillers; `rusher` is also the server-side fallback and the default)

`src/vzd/baselines.nim`, the starter's module retargeted. Both emit the **same** order object an LLM
does, through the same validator, which is what makes the bounded-orders test meaningful. Neither ever
emits `radio` or `notes`. Both are pure functions of world state, so the same world always yields the
same order.

**`rusher`** — `PLAYER_SCRIPTED=rusher`, and the fallback. Deterministic, first matching rule wins:

1. Cog dead → `hold` at the team's spawn anchor, facing the map centre.
2. A live enemy is known within `rusherHuntPx = 520` px → `hunt` at that enemy's last known position;
   `say` = `"on it"` on the turn the intent changes to `hunt`.
3. Own `hp <= 1` and a med kit whose respawn timer is expired lies within `medPx = 360` px →
   `move_to` that med kit.
4. Otherwise → `move_to` the **contested zone**: the zone with the most distinct enemy contacts in the
   last `HuntMemoryTicks`; ties break toward the zone nearest the map centre; with no contacts at all,
   the map centre (`C2`).

**`sentry`** — `PLAYER_SCRIPTED=sentry`. Deliberately weaker and different in *shape*, so the ladder
gets a spread rather than two versions of one bot: **it never crosses the map's centre line unless it
is already hunting.**

1. Cog dead → as above.
2. A live enemy is known within `sentryHuntPx = 260` px → `hunt`.
3. Own `hp <= 1` and a med kit within 360 px → `move_to` it.
4. Otherwise → `hold` at this cog's **assigned post**, post index `(seat div 2) mod 4` of the four
   `postAnchors` on the team's own half — the two spawn-pocket corridor mouths and the two mid-lane
   mouths, derived from the installed map at load, never hard-coded — with `face` = the map centre, so
   the driver holds the bearing instead of sweeping.

Like the starter's `DefaultBaselineParams` (`baselines.nim:38-51`), the four tunables (`rusherHuntPx`,
`sentryHuntPx`, `medPx`, the post rotation) are a parameter object **chosen by a sweep, not guessed**:
`tools/tune_baselines.nim` plays the head-to-head episode over a bounded matrix and prints the table,
`tools/ci/baseline_tuning.json` records the pick, and `tests/test_vzd_tuning.nim` asserts the shipped
defaults still equal it. The sweep's target is a `rusher`-vs-`sentry` **team margin in `[+2, +10]`
frags** over 6 seeds: `rusher` must clearly win (pressure beats posting) without making the game a
walkover.

---

## Sim module

The sim is **Nim**, in the starter's module layout, under `src/vzd/`. The fork is a rename sweep
(`ctf` → `vzd`, `CTF_WIRE` → `VZD_WIRE`, `CtfError` → `VzdError`; a CI grep asserts no `ctf_`/`CTF_`
identifier survives outside comment history) plus the changes below. **The same modules compile
twice**: natively into `/bin/vizdoom-deathmatch` for the server, and to wasm through
`replay-viewer/config.nims` (`switch("path", rootDir / "src")`) for the viewer — which is the whole
reason the game lives in the starter's language.

### Kept, by path (fork = retarget in place; byte-for-byte = do not edit)

| Starter path → fork | Treatment | Why |
|---|---|---|
| `src/ctf/server.nim` → `src/vzd/server.nim` | **fork**, four named edits below | the mummy HTTP/websocket server, `/healthz`, `/player?slot&token`, `/global`, `/client/*`, `/replay-data`, join/auth/kick, the frame limiter, replay mode, the `COGAME_*` contract, `declarePlayerFailure`'s closed payload, the artifact-write block, the wall-clock stop at `server.nim:1407-1417` |
| `src/ctf/sim.nim` (vision half) → `src/vzd/vision.nim` | **fork** | `castFovOctant`, `computeFovShadowcast`, `applyFovCone`, `refreshPlayerFov`, `fovVisibleAt`, `playerVisibleTo`, `lineOfSightClear`, `visionRange` — the fog-of-war engine, the reason this starter was chosen |
| `src/ctf/sim.nim` (combat half) → `src/vzd/combat.nim` | **fork** | `canFire`, `startFireWindup`, `resolveSimultaneousFire`, the aim fuzz, the bullet corridor, `respawnPlayers` |
| `src/ctf/sim.nim` (motion half) → `src/vzd/motion.nim` | **fork** | `applyInput`, the fixed-point integrator, per-axis slide, cog-cog collision and bounce |
| `src/ctf/replays.nim`, `replay_runtime.nim` → `src/vzd/` | **fork** (magic + game name only: `CtfReplayMagic = "COWLDCTF"` → **`VzdReplayMagic = "COWLDVZD"`**) | the whole replay codec, keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`, `initReplayRuntime` / `advanceReplayFrame` / `buildReplayViewerPacket` |
| `src/ctf/decide.nim`, `directives.nim`, `llm.nim`, `baselines.nim`, `control.nim` → `src/vzd/` | **fork**, retargeted not rewritten | the per-turn parallel batch, the two deadlines, the rate floor, the budget guard at `decide.nim:341-345`, tolerant parsing, the rune caps, repair-don't-reject, the fallback ladder, the nav grid and flow fields |
| `src/ctf/sim_state.nim` → `src/vzd/sim_state.nim` | **fork** | `gameHash` / `mixHash`, `emitEvent`, `pushFeedDirective`, logging, the lobby countdown, `resetToLobby`, spawn placement |
| `src/ctf/roster.nim` → `src/vzd/roster.nim` | **fork**, three named edits below | join/auth, `IdentityNames`, `recordKill` / `recordTeamKill` / `recordDeath`, the results builder |
| `src/ctf/events.nim` → `src/vzd/events.nim` | **fork** | the tier-2 event wire format and the `eventsJsonl` summary-row contract; the `SimEventKind` set is reduced (§Server) |
| `src/ctf/broadcast.nim` → `src/vzd/broadcast.nim` | **fork**, two named edits below | `stepEvents`, `buildStateJson`, `rosterJson`, the lull scan, the beat timeline, the vision-cone wire block, **and `firstPersonJson` + `firstPersonMapJson` (`broadcast.nim:464-660`) — the raycast machinery this coworld is about** |
| `src/ctf/global.nim` → `src/vzd/global.nim` | **fork**, cut | the sprite/object pools, the compositor, the FX families, `RenderScale` — minus every deleted mechanic's draw family |
| `src/ctf/arena.nim` → `src/vzd/arena.nim` | **fork, cut** | `selectCtfMap` (the map-install choke point), `arenaCtfMap`, `generateCtfMap` + its validators, `poolCtfMap`, `mapSpecJson` / `mapFromSpecJson`, `inShape` / `pointInPolygon`, `rasterizeWallMasks`, `validateMapWalkability`, `mapWallAt`, the glass-window predicate — **without** the four-team shapes, the oversize classes, the puddles and the animated diamonds |
| `src/ctf/map_pool.nim`, `mapgen_styles.nim`, `tools/gen_map_pool.nim`, `tools/render_map_pool.nim` | **fork** | the curated 20-seed pool is the `pool` variant's "maps seeded" |
| `src/ctf/labels.nim`, `rig_art.nim`, `wire_constants.nim`, `tools/gen_wire_constants.nim` | **fork** | the label-vocabulary contract (+ `tests/label_manifest.txt`), the sprite compositor, the one-source JS wire constants |
| `src/ctf/sim_types.nim` → `src/vzd/sim_types.nim` | **fork** | `GameVersion` (restarts at `"1"` with the starter's prepend-only changelog-comment discipline and `tools/ci/check_gameversion.sh` kept), `TargetFps`/`ReplayFps` 24, `PlayerHalf` 6, the motion and combat constants, the flatty wire types (field order sacred), the rune caps, plus new `MaxRadioRunes = 96`, `LeadThrottleTicks = 48`, `DecisiveMargin = 12`, `RateCapPerMin = 28` |
| `src/ctf/sim_config.nim` → `src/vzd/sim_config.nim` | **fork** | `GameConfig` lifecycle, `config.update`, the `mapSpec` pinning at `sim_config.nim:844-855` |
| `src/ctf.nim` → `src/vizdoom_deathmatch.nim` | **fork** | the entrypoint, **including seed randomisation before `config.update`** so seed-derived draws (the pool pick) follow the final seed |
| `src/paintball_player.nim` → `src/vizdoom_deathmatch_player.nim` | **fork** | the thin seat registrar (§Decisions) |
| `client/chrome_common.js` | **byte-for-byte apart from the named two-line wire patch** (40 022 bytes either way) | §Viewer → Chrome provenance |
| `client/broadcast_core.js`, `client/replay_broadcast.html`, `client/league_replayer.html` | **fork** | §Viewer |
| `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` | **fork: identifiers and the output name only** | the emscripten link flags and the Worker bootstrap (§Viewer) |
| `replay-viewer/ctf_replay.nim` → `replay-viewer/vzd_replay.nim` | **fork** | §Viewer |
| `Dockerfile`, `Dockerfile.replay-viewer`, `tools/build_replay_viewer.sh`, `tools/wasm_replay_smoke.cjs`, `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/replay_summary.py`, `tools/record_fixture.sh`, `nimby.lock`, `flake.nix`, `tests/config.nims`, `tests/helpers.nim` | **byte-for-byte apart from names/paths** | build, bundle and forensics wiring; `build_replay_viewer.sh` already carries the ecos `mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling |
| `tools/ci/check_gameversion.sh`, `tools/ci/next_coworld_version.py` (+ its test) | **byte-for-byte** | version discipline |
| `data/arena_floor.png`, `data/font.ttf`, `data/ascii.png`, `data/pallete.png`, `data/atlas/*`, `data/medkit.png`, `data/soldier_{red,blue}*.png`, `data/soldier_{red,blue}_front{,_gun}.png`, `client/art/**` | **byte-for-byte** | real art (§Viewer → Art) |

### Deleted (with their tests, tools, docs and config surfaces), not disabled

The heart/flag objective — pedestals, carriers, capture zones as a *scoring* concept, `tryPickupFlags`,
`updateFlags`, `recordCapture`, the steal/return/capture events and `EndRuleWipe`/`EndRuleMercy`;
King of the Hill, `paint.nim`, floor paint, the paint grid, the paint buff and spray cans; grenades and
the barrage; med-kit *siblings* shields and cardboard barriers; puddles; trenches; perks and handicaps;
achievements and the achievement focus; four-team play (`Green`/`Yellow`, `symRot90`/`symQuadMirror`,
the corner/plus maps) and the `resident`/`visitor` regimes; campaign mode; the oversize map classes
(`huge`/`giant`/`colossal`) and `arena-large`; `tools/mapkit.nim`, `tools/map_editor*.nim`,
`docs/MAPKIT.md`, `docs/pool-review.html`, `scripts/campaign_puddles.py`,
`scripts/gen_campaign_maps.py`. Also deleted: the `data/` art belonging to deleted mechanics
(`heart_*`, `ped_*`, `paintgun*`, `paintbomb`, `shield`, `spraycan*`, `crew`, `*_crown`,
`soldier_{green,yellow}*`, `rig_real/`).

**The endzone geometry is kept.** Each team's spawn pocket, its clearance and its anchor are what make
the arena a symmetric two-base map, what `respawnPlayers` places bodies on, and what `retreat` aims at.
Only the *objective* attached to them is deleted. `arenaEndzoneRadius`/`ArenaEndzoneDisc` stay as pure
geometry.

### New modules

- `src/vzd/egoview.nim` — the observation builder. It owns `marchRays(sim, cogIndex, columns,
  maxRange)`, the single ray-march used by **both** the LLM's 16-ray depth strip **and**
  `broadcast.nim`'s `firstPersonJson` (which is refactored to call it with 96 columns): the model and
  the spectator therefore read the same walls. It also owns `contactsFor(seat)` (cone + bubble +
  72-tick memory, filtered through `playerVisibleTo`), the bearing/compass conversion, and the seat
  view's JSON assembly.
- `src/vzd/zones.nim` — the 5 × 3 zone grid: ids, centres, the load-time terrain word per zone (wall
  fraction < 8 % → `open`, > 22 % → `corridor`, else `cover`), `zoneAt(x, y)`, `zoneCentre(id)`, and
  the contested-zone query the `rusher` baseline uses.
- `src/vzd/deathmatch.nim` — the objective layer: the per-cog `net` derivation, the two team totals,
  the margin, `gameScorePermille` at `DecisiveMargin`, the streak counters, the throttled `lead`
  detector, and `checkDeathmatchEnd()` (full time only).

### Integer arithmetic and determinism

**Everything inside `gameHash` is integer only** — positions, velocities in `MotionScale` units, hit
points, cooldowns, windups, kill/death/team-kill counters, tick counters. The starter's fov cone filter
and the aim fuzz use floating point, and both are kept **exactly as written, byte-for-byte**, because
they are already the mechanism the starter's own native↔wasm hash chain survives: the same expression,
the same order, the same libm on both targets. What must never happen is a *new* float expression
feeding a hashed value; `tests/test_vzd_determinism.nim` greps `src/vzd/{deathmatch,zones,motion}.nim`
for float literals, `/` and `sqrt` and requires none. `egoview.nim` uses floats freely — it produces
**text for a model and pixels for a spectator**, never a hashed value, and the test whitelists it by
name for exactly that reason.

**One seeded source, consumed in this fixed order before any seat connects** (the starter's
`setupRng`):

1. the **map** — `pool` variant: entry index = the randomised `seed` (`arena.nim:3388`); `arena`
   variant: no draw at all;
2. the **home deal** — the starter's GV44 "the homes are dealt, not owned" rotation, kept, so which
   pocket Red gets is a seed draw and not a fixed advantage;
3. the **med-kit placement orbit** — the starter's `placeWalkablePickups`;
4. the **aim-fuzz stream** and the **shout jitter** stream — the starter's, unchanged.

Nothing a seat does can shift any of them. The seed is randomised in `src/vizdoom_deathmatch.nim`
before `config.update` (the starter's rule), recorded in the replay config and in `results.seed`;
`results.map` records the resolved map name. Two episodes with the same seed and the same masks are
byte-identical.

### Determinism, native ↔ wasm

The mechanism is the starter's, unchanged, and it is why the starter is worth forking:

1. The server writes a **`COWLDVZD`** replay: magic + format version + game name/version header, the
   **resolved config JSON** (including the full `mapSpec`), then the record stream — joins, leaves,
   **the per-tick input masks** the control layer produced, chat records, and **one `gameHash` per
   tick**.
2. `tools/build_replay_viewer.sh` builds `replay-viewer/vzd_replay.nim` — which imports the **same**
   `src/vzd/sim.nim` — through the pinned `emscripten/emsdk` + nimby container in
   `Dockerfile.replay-viewer`, target `replay-viewer-builder`.
3. In the browser, `vzd_load_replay` runs `parseReplayBytes` + `initReplayRuntime`; `vzd_frame`
   re-steps the sim from the recorded masks and compares `sim.gameHash()` against the recorded hash
   **every tick** (`checkReplayHash`). One divergent bit is caught at the tick it happens and surfaced
   as `mismatchTick` in `#mmwarn`.
4. **`gameHash` mixes**, in this fixed order: the starter's kept fields (tick, phase, gameOverTimer,
   gameStartTick, startWaitTimer, nextJoinOrder, and per cog `x, y, velX, velY, flipH, aimBrads, team,
   joinOrder, color, hp, alive, lives, respawnTimer, fireCooldown, fireWindup, lockedAimBrads`) — with
   every deleted mechanic's fields removed — then, **appended after them** so the inherited ordering
   never moves: per cog `frags`, `teamFrags`, `deaths`, `streak`, `damageDealt`, `damageTaken`,
   `medkitsTaken`; then the two `teamNet` totals and `leadTeam`; then the starter's shout block
   (address, team, text, tick, x, y), unchanged.
5. **The wall-clock stop is recorded as a load-bearing record, not inferred.** A wall-clock fact cannot
   be re-derived from sim state, so the stop is written as one `stop` record applied by the *same proc*
   on record and on playback, and `tests/test_vzd_replay.nim` runs the record→re-derive check for
   **every** end reason (`full_time`, `wall_clock`, `sim_fault`), not just the healthy one
   (particle-worlds `13c66d7`, 2026-08-26).

Replay size: 2592 hashes + 2592 × 8 mask bytes + ~250 chat records ≈ **50 KB**. Everything else is
re-derived in the browser.

### Documented divergences, and why (mirrored into `docs/RULES.md` §Divergences)

1. **This is not a ViZDoom port.** No ZDoom, no `vizdoom` bindings, no WAD, no raw pixel buffer, no
   depth/labels *image*. What is reproduced is the multiplayer benchmark's shape: eight agents, one
   map, egocentric observation, `frags − deaths`. §Out of scope records what a real port would need.
2. **The observation is text, not pixels.** The idea itself says "LLM needs the labels buffer"; the
   16-ray depth strip and the labelled contact list are the depth and labels buffers written as JSON.
   A neural pixel policy is out of scope (§Out of scope).
3. **Teammates are not fogged** (the starter fogs everyone: "teammates are NOT [visible] — no team
   radio"). Four independent policies on one team, each driving one body at a 4.5 s cadence, cannot
   play team deathmatch blind, and the idea's integrity note requires team DM. The `radio` channel
   gives them a voice; fogging their bodies as well would make every crossfire an accident. Enemies are
   fogged exactly as the starter fogs them.
4. **`visionConeDeg` 60 → 45.** A 90° total cone is ViZDoom's default FOV and it is the one place this
   fork can be faithful for free. It also makes aim matter: a 120° cone at 1575 px on a 1235 px board
   is very close to no fog at all.
5. **One cog per seat.** Paintbot's `cogsPerTeam: 4` squad is dropped; `num_agents` is the cog count.
   That forces the two named `squadMode`/`cogIdentityIndex` edits below.
6. **The driver refuses to cause friendly fire.** Friendly fire stays on in the sim (it is a real Doom
   deathmatch hazard and a team kill costs a frag), but no bot ever *chooses* it.
7. **`mercy` and `wipe` are gone.** Full time, wall clock or fault — nothing else can end an episode.

### The four named edits to `server.nim`

1. **`squadMode`'s gate.** The starter enables the commander layer with
   `config.numAgents > 0 and config.cogsPerTeam > 1` (`server.nim:1366-1367`). With one cog per seat
   the second clause is false, so it becomes **`config.numAgents > 0`**. `tests/test_vzd_engine.nim`
   asserts the decision engine is live in an 8-seat / 1-cog config — without this edit every seat would
   silently drive nothing and the episode would be eight motionless cogs.
2. **Turn boundary** — unchanged in shape (`server.nim:1927-1948`), with `turnTicks = 108`, all eight
   seats in the batch, and the effective-spacing floor of §Decisions.
3. **Registration interception** — a player's Sprite v1 chat message (`0x81`, surfaced as `chatText`)
   whose text parses as a registration object is consumed as registration, **not** applied as a shout
   and **not** written to the replay chat stream; the server writes a redacted `register` record
   instead (policy label and kind, never the prompt). The starter's "hold an unappliable registration
   and re-read it when the slot lands" behaviour is kept verbatim. Any other chat text from a seat is
   dropped — cogs speak through `say`.
4. **Wall-clock stop** — the starter's check at `server.nim:1407-1417`, kept, but settling from the
   **frag counters** instead of `hillLeader()`, forcing `phase = GameOver`, `reason = deadline`,
   `endRule = wall_clock`, written as the load-bearing `stop` record.

### The three named edits to `roster.nim` / `sim.nim`'s seat helpers

1. **Identities.** `cogIdentityIndex` (`sim.nim:276-278`) computes a cog's rank inside its *squad*,
   which collapses to 0 for every cog when `cogsPerTeam == 1` and would make all four red cogs
   `RED-alpha`. It becomes the cog's **rank among its own team's slots** — the starter's existing
   `slotIdentityIndex` (`roster.nim:68-77`), which already does exactly that and is already stable
   across reconnects and replays. `cogAlias` is otherwise unchanged, so aliases are
   `RED-alpha..delta` / `BLUE-alpha..delta`. `IdentityNames` itself is untouched.
2. **`squadResultsJson` → `deathmatchResultsJson`** — one entry per seat, eight entries in every
   seat-indexed array, keys exactly as §Server lists them, built from the frag/death counters instead
   of the hill counters.
3. **`recordTeamKill` is scored, not just badged.** The starter counts `teamKills` for an endscreen
   badge only; here it is a term in `net[c]` (§Scoring). The counter and the call site are unchanged;
   only the consumer is new.

### The two named edits to `broadcast.nim`

1. **`firstPersonJson` is refactored onto `marchRays`** so the LLM's depth strip and the viewer's
   raycast share one implementation, and it gains a `columns`/`maxRange` parameter. The big `#fpv`
   inset keeps the starter's `FpColumns = 96` and the full `visionRange`; the new eight-up eyes strip
   (§Viewer) calls it with `FpThumbColumns = 32` and `FpThumbRange = 600`. Cost: the strip is
   recomputed every 4th replay frame, `8 cogs × 32 columns × 300 march steps = 76 800` wall lookups
   per recompute ≈ **19 200 per frame**, about a quarter of what the single open PIP already costs
   (`96 × 788 = 75 648`).
2. **Vision cones are broadcast for every cog every frame** with `coneDeg`, `range` and `aim` — the
   starter already ships a cone block on the global stream; here it is unconditional, because the eight
   cones are the spectator's whole understanding of who can see whom.

---

## Server, player, protocol

### The contract

The starter's, unchanged in shape (`docs/PROTOCOL.md` is forked, not rewritten): `COGAME_CONFIG_URI`
in; `COGAME_RESULTS_URI`, `COGAME_SAVE_REPLAY_URI`, `COGAME_PLAYER_FAILURE_URI`, `COGAME_EVENTS_URI`
out; `COGAME_LOAD_REPLAY_URI` + `/client/replay` for local replay mode; `HOST`/`PORT`; player sockets
at `/player?slot=<i>&token=<t>`.

The certifier's browser probes are served for real and registered **before** any catch-all asset route:
`GET /client/player?slot=&token=` (token-checked, and it must **not** open the player socket),
`GET /client/global`, the `/global` websocket's first message, and `/healthz` — all kept answering for
the `gameOverTicks` grace after artifacts are written (the lantern 0.1.1 and 0.1.3 scars). A player
websocket whose token does not match its seat is **closed** (the starter does this; the flatland 0.1.1
scar is a fresh-written server that did not). Global broadcasts are fire-and-forget so a slow viewer
can never stall the episode.

### Results document (closed schema; `deathmatchResultsJson` and the manifest `results_schema` list exactly these keys)

```json
{
  "names":          ["daveey","daveey-1","Baseline (1)","Baseline (2)","Baseline (1)","Baseline (2)","Baseline (1)","Baseline (2)"],
  "aliases":        ["RED-alpha","BLUE-alpha","RED-beta","BLUE-beta","RED-gamma","BLUE-gamma","RED-delta","BLUE-delta"],
  "team":           ["red","blue","red","blue","red","blue","red","blue"],
  "scores":         [0.708,0.292,0.708,0.292,0.708,0.292,0.708,0.292],
  "win":            [true,false,true,false,true,false,true,false],
  "reason":         "complete",
  "endRule":        "full_time",
  "games":          1,
  "frags":          [6,3,4,2,3,4,2,3],
  "teamFrags":      [0,0,0,1,0,0,1,0],
  "deaths":         [2,4,3,3,4,3,3,4],
  "net":            [4,-1,1,-2,-1,1,-2,-1],
  "teamNet":        [2,-3],
  "margin":         5,
  "damageDealt":    [21,12,14,9,11,13,8,11],
  "damageTaken":    [6,12,9,9,12,9,9,12],
  "shotsFired":     [38,31,29,24,26,30,22,27],
  "shotsHit":       [21,12,14,9,11,13,8,11],
  "medkits":        [1,0,2,1,0,1,1,0],
  "longestStreak":  [3,2,2,1,1,2,1,1],
  "map":            "arena",
  "policyKinds":    ["llm","llm","scripted","scripted","scripted","scripted","scripted","scripted"],
  "crossPlay":      true,
  "llmTurns":       [24,23,0,0,0,0,0,0],
  "fallbackTurns":  [0,1,0,0,0,0,0,0],
  "ordersRejected": [0,2,0,0,0,0,0,0],
  "deadSeats":      [false,false,false,false,false,false,false,false],
  "finalTick":      2592,
  "seed":           1734029581,
  "stopDetail":     ""
}
```

Every seat-indexed array is exactly 8 long; `teamNet` is exactly 2 long (`[red, blue]`); `margin` is an
integer **from RED's point of view**. `scores[red] + scores[blue] == 1.0` exactly, for every legal
outcome. Adding a key means updating `deathmatchResultsJson`, the manifest's `results_schema` and
`tools/ci/docker_smoke.sh`'s expected-key set in the same commit — Coworld schemas are closed and
undeclared keys are dropped.

`crossPlay` is `true` when at least one LLM seat and at least one scripted seat played, which is the
normal league shape (two prompt champions among six scripted fillers) and is what the idea's
"integrity" section wants recorded: with `damageDealt`/`damageTaken` alongside it, the damage graph of
any episode is reconstructable from `results` alone.

### Replay bytes (self-sufficient)

The replay stays the starter's **binary `COWLDVZD`** format — the static wasm viewer parses exactly
this, and a JSON replay would mean rewriting `replays.nim`, `replay_runtime.nim`,
`static_replay_worker.js` and `wasm_replay_smoke.cjs`, i.e. the machinery this fork exists to reuse
(the knights-archers precedent). The consequences are handled explicitly:

- CI's `docker-smoke` job sets **`SMOKE_REQUIRE_REPLAY_JSON=0`**, which the shared
  `tools/ci/docker_smoke.sh` supports by design.
- The repo ships the starter's **`tools/replay_summary.py`** (Python 3 stdlib only, no Nim, no
  Docker), retargeted: given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout —
  `{"protocol":"vizdoom-deathmatch/v1","gameVersion":"1","seed":…,"map":"…","names":[…],
  "aliases":[…],"policyKinds":[…],"tickCount":…,"directives":[…],"radio":[…],"shouts":[…],
  "fallbacks":N,"results":{…}}` — by brace-matching the config JSON from the first `{` and decoding
  the chat records.
- **The phase-60 substitute for SPEC §Definition of done check 4:**
  ```bash
  curl -sSL "$replay_url" -o /tmp/ep.replay
  python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
  jq -e . /tmp/ep.json >/dev/null                      # strict UTF-8 JSON: ok
  jq -r '.protocol, .results.reason, .results.margin, .results.frags' /tmp/ep.json
  jq -r '[.directives[]|select(.source=="llm")]|length, .fallbacks, (.radio|length)' /tmp/ep.json
  ```
  Require `protocol == "vizdoom-deathmatch/v1"`, `results.reason == "complete"` (or the
  declared-acceptable `deadline`), a non-zero `sum(results.frags)` (somebody shot somebody), and the
  champion seats' directives with `source == "llm"`, real intents and non-empty radio lines — not all
  fallbacks.

Everything the viewer needs is in the bytes; no server is contacted except S3 for the file:

| Replay content | Carries |
|---|---|
| header | magic `COWLDVZD`, format version, `gameName` `vizdoom-deathmatch`, `gameVersion` `1` |
| config JSON | `seed`, `mapPath`, **the full resolved `mapSpec`** (dimensions, obstacles, endzones, med-kit spawns, symmetry, the dealt homes), `num_agents`, `cogsPerTeam`, `teams`, `maxTicks`, `maxGames`, `turnTicks`, `lives`, `hitPoints`, `respawnTicks`, `gunRange`, `fireCooldownTicks`, `fireWindupTicks`, `aimTurnRate`, `visionConeDeg`, `visionBubble`, `players[].name` (real names), `slots[]` (the team assignment), `fastMode`, `showPlayerLabels` |
| joins / leaves | per seat: `name` (real policy name), `slot`, `token` |
| input masks | one byte per cog per tick — this game's entire input log |
| chats | `register` / `directive` / `fallback` / `budget_guard` / `stop` / `result` records, plus each cog's `say` shouts by cog index |
| hashes | one `gameHash` per tick — the integrity chain the viewer checks |

The map is pinned in the config **as a document, not as a name** (`sim_config.nim:844-855`), so a later
edit to the pool or the generator cannot change what an old replay renders.

### Record and event vocabulary

**A. Replay chat records** (written by the server, re-applied at playback into non-hashed fields; they
drive the broadcast feed and `replay_summary.py`, and can never affect the sim):

| `k` | Fields |
|---|---|
| `register` | `seat`, `team`, `policy` (≤ 48 runes), `kind` (`llm`\|`scripted`), `baseline` |
| `directive` | `game`, `turn`, `seat`, `team`, `alias`, `source` (`llm`\|`scripted`\|`fallback`), `latency_ms`, `intent`, `at`, `target`, `face`, `say` (≤ 10 runes), `radio` (≤ 96 runes), `note` (≤ 160 runes), `view` (the observation minus `your_notes`); whole record ≤ 900 runes |
| `fallback` | `game`, `turn`, `seat`, `attempt` (1\|2), `cause`, `detail` (≤ 200 runes) |
| `budget_guard` | `turn`, `remaining_s` |
| `stop` | `tick`, `endRule` — the load-bearing wall-clock/fault stop |
| `result` | the full results document, written once at episode end (the starter's `resultRecord`, `decide.nim:246`) |

**B. Derived broadcast events** — `stepEvents` derives these from state deltas during playback, so they
cost no replay bytes and are identical live and in replay. **A closed enum of sixteen kinds:**

`phase` `{phase}`; `gamestart` `{game, games}`; `turn` `{n, of}`;
`order` `{seat, alias, intent, at, target}`; `say` `{seat, alias, text, x, y}`;
`radio` `{seat, alias, team, text}`; `fallback` `{seat, cause}`;
`shot` `{by, alias, aim, x, y}`; `hit` `{by, victim, hp, dmg}`;
`kill` `{killer, victim, tk, amb, trade}` (the starter's shape, kept verbatim so the inherited
kill-feed and `killMarkerTeam` code is unchanged); `respawn` `{who}`;
`pickup` `{who, item: "medkit"}`; `spot` `{by, target}`; `lost` `{by, target, ticks}`;
`streak` `{who, alias, n}`; `lead` `{team, margin}`; `gameover` `{winner, draw, tl, margin}`; plus
`end` `{reason, endRule, scores}`.

`tests/test_vzd_events.nim` asserts the emitted set equals exactly this list and that every kind the
appended game block consumes is in it.

**Beats** — the scrubber markers, and the only kinds the appended game block turns into buttons:
**`gamestart`, `kill`, `streak`, `lead`, `fallback`, `gameover`.** A `kill` beat is coloured by the
victim's team (the starter's `killMarkerTeam`, kept). `shot`, `hit`, `turn`, `order`, `say`, `radio`,
`respawn`, `pickup`, `spot`, `lost` and `phase` drive the feed only and never make beats — at ~30 frags
and ~250 shots an episode, a beat per shot would be an unreadable scrubber.

**C. Tier-2 analysis stream** — `COGAME_EVENTS_URI` gets the starter's JSON-lines `eventsJsonl`, with
`SimEventKind` reduced to `Shot, Hit, Damage, Kill, Death, Respawn, Heal, Pickup, PhaseChange,
GunTrigger, ShotImpact, ShoutEvent, TurnStart, Directive, Fallback, Streak, Lead` and the mandatory
trailing summary row (`type`, `ticks`, `events`, `gameVersion`) kept.

---

## Viewer

**A static wasm bundle. Never a pod.** The manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` **under `game`**, and
`tools/build_replay_viewer.sh` is coworld-ctf's hook — kept, with the image tag and the `docker cp`
source path changed (`/workspace/ctf/replay-viewer/dist/.` →
`/workspace/vzd/replay-viewer/dist/.`) — building `Dockerfile.replay-viewer`'s
`replay-viewer-builder` target and copying the dist out. It already carries the ecos 2026-08-23
`mkdir -p "$(dirname …)"` fix and the buildx / `--platform linux/amd64` handling. It stays committed
**executable** (`coworld build` hard-requires `os.X_OK`). No `/client/replay` live-server viewer is
ever declared to the platform; the game still serves `/client/replay` locally for developers.

### One starter supplies all four viewer files

**`replay-viewer/config.nims`, the wasm entry `.nim` (`replay-viewer/vzd_replay.nim`, forked from
`replay-viewer/ctf_replay.nim`), `replay-viewer/static_replay.js` + `static_replay_worker.js`, and
`index.html` (built from `client/replay_broadcast.html` by `Dockerfile.replay-viewer`'s marker
splice) ALL come from ONE starter: `coworld-ctf`** — which is this repo's own starter. **Never a
mixture.** Splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently
(cogame-lantern, 2026-08-23). The set is internally consistent and is kept as one piece: the Worker
sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), the module is emitted
**non-modularized** as `vzd_replay.js`, `config.nims` keeps `--os:linux --cpu:wasm32 --cc:clang`
through `emcc`, `--mm:arc --exceptions:goto -d:useMalloc -d:release -d:noSignalHandler`, `-O2`,
`--preload-file data@data`, `-s ALLOW_MEMORY_GROWTH`, **`-s ABORTING_MALLOC=1`** (non-negotiable:
with `-d:useMalloc` Nim never checks malloc for nil and wasm32 has no memory protection, so a failed
allocation would write through nil into address 0 and corrupt the module's own globals — the
starter's own comment in `config.nims`), `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`,
`-s EXPORTED_RUNTIME_METHODS=HEAPU8` and
`EXPORTED_FUNCTIONS=_main,_malloc,_free,_vzd_load_replay,_vzd_frame,_vzd_input,_vzd_packet_ptr,
_vzd_packet_len,_vzd_mismatch_tick,_vzd_error_ptr,_vzd_error_len,_vzd_stage_ptr,_vzd_stage_len`; and
`static_replay_worker.js` does
`importScripts('./wire_constants.js', './broadcast_core.js', './vzd_replay.js')` in that order (the
starter's line 239, renamed only).

`vzd_replay.nim` keeps `ctf_replay.nim`'s structure exactly — the `stampStage` fixed progress buffer
that survives an allocation abort, `bytesFromPointer`, the try/except publishing `lastError`, and the
`emscripten_exit_with_live_runtime()` epilogue that stops Nim's generated `main` from running module
destructors while JS keeps calling in. Two additions:

- **A load-time pre-scan.** `vzd_load_replay` re-simulates the whole episode once headlessly (2592
  ticks × 8 cogs of integer work plus fov — tens of milliseconds in wasm), records the **per-tick frag
  margin series** (the momentum graph), the kill/streak/lead/fallback beat ticks, and the lull spans,
  then resets and renders frame 0. That is what lets the momentum graph and the scrubber beats draw at
  **full width on the first frame** instead of growing in.
- `vzd_mismatch_tick` returns `checkReplayHash`'s divergence tick, or `−1`.

**Load and error signals.** The shell sets **`data-replay-loaded="true"` on `<html>`** in
`static_replay.js`'s `onWorkerMessage` `'loaded'` branch (starter line 161) — posted by the Worker only
*after* `ingestPacket()` has handed BroadcastCore the first frame and it has drawn, so the attribute
means "a frame is on the canvas", not "a file was fetched". On failure it sets **`data-replay-error`**
on `<html>` with the message, in `showFailure()` (starter lines 8-20). Both are coworld-ctf's own
signals, inherited unchanged — this fork adds neither and removes neither. The `coworld-replay`
postMessage bridge's `ready` is posted **from a callback fired after** `data-replay-loaded="true"` is
set, never on rAF timing at the call site (chorus `3c11c953`, 2026-08-24), or the softmax.com embed
samples an unpainted shell.

### Chrome provenance

- **`client/chrome_common.js` is the starter's file with ONE named, minimal patch.** A named,
  minimal patch is the only admissible change to the inherited chrome (acceptance checklist item 14),
  so here it is in full — two lines, both a rename of the game's own wire namespace, nothing else:

  ```diff
  --- coworld-ctf/client/chrome_common.js
  +++ client/chrome_common.js
  @@ -14 +14 @@
  -//    both embedded pages (src/ctf/server.nim);
  +//    both embedded pages (src/vzd/server.nim);
  @@ -72 +72 @@
  -  var WIRE = window.CTF_WIRE || {};
  +  var WIRE = window.VZD_WIRE || {};
  ```

  **Why it is required, not cosmetic:** `tools/gen_wire_constants.nim` emits `window.VZD_WIRE={…}`
  and `Dockerfile.replay-viewer` hard-asserts `grep -q '^window.VZD_WIRE={'` on the bundled
  `wire_constants.js`. A chrome still reading `window.CTF_WIRE` would find an empty object and every
  wire constant would silently fall back to its default. The patch is length-preserving — `ctf`→`vzd`
  and `CTF`→`VZD`, three characters twice — so both files are 40 022 bytes; nothing is reformatted,
  added or removed. `tests/test_vzd_viewer.nim` pins that byte length and the sha1 of the patched
  file, and asserts `window.VZD_WIRE` is present and `window.CTF_WIRE` absent, so any further
  divergence fails the build. Everything else this game adds lives in the appended game block. Its `markBeat` / `killMarkerTeam` /
  `renderBeatMarkers` / `ingestBeats` / `renderClock` / `renderTransport` / `ingestLullSpans` /
  `renderMomentum` remain; `ingestBeats` ignores kinds it does not know.
- **`client/replay_broadcast.html` is the starter's page with a game block appended** — never a rewrite
  that reuses its ids (cogame-gridlock, 2026-08-23). The starter's CSS, markup, `relayout()`
  (lines 4276-4325), transport, endcard, locker-room loader, `?embed=1` mode and `.tiny` density
  system are untouched, and the block is installed through the starter's own splice hook:
  `window.PaintballChrome` is renamed `window.VzdChrome` and its `install(PB_CTX)` /
  `frame(s, ctx, jumped)` / `event(e, s, ctx)` entry points (starter lines 4337, 2075, 3480-3481) are
  kept with the same signatures and the same `PB_CTX` payload. The starter's own appended PAINTBALL
  block (from the banner at line 4344 to EOF) is **replaced** by the DEATHMATCH block; the classic page
  above that banner is byte-identical. A test asserts the starter's byte prefix is intact up to the
  documented splice marker.
- **`client/broadcast_core.js` is forked** — it is paintbot's draw layer and this game has no flags,
  paint, hills, grenades or hearts. Kept and pinned function-by-function against the starter's text by
  `tests/test_vzd_viewer.nim`: the canvas/DPR sizing, `relayout()`, the camera, the feed queue and
  `pushFeed` **including its signature** (`replay_broadcast.html:3558`; the cogball 0.1.4 latch scar: a
  signature drift threw mid-replay and latched `static_replay.js` into `failed`), `banner`, the beat and
  lull machinery, the endcard builder, the speed chips, the `?embed=1` path, the shout-bubble renderer,
  **the whole first-person raycast painter** (`drawFpvEntity`, the column blitter, `COG_BASE`/`ART_BASE`
  derivation — never a root-absolute asset src, per `tests/test_first_person_pip.nim`), and the
  `window.CTF_WIRE` → `window.VZD_WIRE` rename emitted by `tools/gen_wire_constants.nim`. Deleted:
  every flag, paint, hill, spray and grenade draw call. Added: `drawEyesStrip`, `drawFragbug`,
  `drawStreakGlow`.
- **Elements removed** (exactly these, and the JS that feeds them):
  - **`#viewpanel`** — `#minimap`, `#minimap-canvas`, `#zoombar`, `#zoom-in`, `#zoom-out`,
    `#zoom-slider`, `#zoom-read`, and the page's `core.attachMinimap($('minimap-canvas'))` call
    (`replay_broadcast.html:4200`). **Zoom decision: dropped.** `BOARD_ASPECT` is a constant
    `1235/659 = 1.874` in **every** shipped variant (§The game → The arena, asserted by
    `tests/test_vzd_manifest.nim`), `relayout()` letterboxes the whole board into the frame at every
    width, there is no pannable area and no camera, so per the pin a fixed arena drops `#viewpanel`
    entirely. The minimap's job — knowing where the fight is — is done better here by the always-on
    eyes strip and the kill feed. `broadcast_core.js` already tolerates never being attached:
    `minimapSurface`/`minimapCtx` stay null and `drawMinimap()` returns on its first guard.
  - The paintball scorebug internals `.hillchip`, `.hcap`, `#pb-regime`, `.pb-tags`, `.pb-sub` and the
    hill/paint/spray/tagout feed rows and their CSS (the whole starter PAINTBALL block goes).
  - The ctf scorebug/endcard internals `.flagicon`, `.ec-heart`, `.squad-pip`, `.squad`.
  - The `.beat-marker.steal`, `.return`, `.capture`, `.hillflip`, `.tagout` CSS rules (starter lines
    919-934, 4431-4443) — those kinds are never emitted here. `.beat-marker.kill` is **kept** because
    `kill` is emitted, and four new rules are added (`.gamestart`, `.streak`, `.lead`, `.fallback`,
    `.gameover`).
  - The perk and handicap badges (`renderTeamMeters`'s perk/handicap paths and their CSS).
  - **Kept:** `#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`
    (`#lk-bg`, `#lk-art`, `#lk-sprites`, `#lk-cap`), `#chrome`, `#scorebug` with
    `#plates-l`/`#plates-r`/`#clock`/`#clock-time`/`#clock-caption`, **`#povBadge`**,
    **`#fpv` with every child** (`#fpv-canvas`, `#fpv-hud`, `#fpv-name`, `#fpv-hp`, `#fpv-gear`,
    `#fpv-map`, `#fpv-map-canvas`, `#fpv-cap`, `#fpv-grip`) — the first-person inset is the whole point
    of this coworld and it is inherited, not written — `#bannerlane`, `#killfeed`, `#mmwarn`,
    **`#transport` in full** (`#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`,
    `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#ffwd-chip`, `#ffwd-mini`, `#win-chip`, `#tick-clock`,
    `#speedchips`), `#scrub` with `#momentum`/`#scrub-fill`/`#lulls`/`#scrub-win`/`#scrub-head`,
    `#endcard` with `#ec-headline`/`#ec-wincond`/`#ec-how`/`#ec-teams`/`#ec-replay`, and `#status`.
  - **Added by the game block:** `#eyes` (the eight first-person thumbnails, in the top band under the
    scorebug), `#fragbug` (the net-frag scoreboard inside `#scorebug`), and `.dm-*` classes.

### Endcard and chrome label re-mapping

A forked ctf/paintbot endcard silently ships the wrong vocabulary — nothing in the starter's tests, in
`viewer_smoke.mjs` or in the label manifest covers spectator chrome strings. The re-labelings are
therefore enumerated here and enforced by a test:

| Starter string (file:line) | Becomes |
|---|---|
| `<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>Clstr</span><span>Cap</span></div>` (`replay_broadcast.html:3795`) | `<span>Cog</span><span>Frags</span><span>Deaths</span><span>Net</span><span>Acc</span>` |
| `<div class="ec-thead"><span>Cog</span><span>Tags</span><span>Out</span><span>Paint</span></div>` (3788) | deleted with the paintball block |
| `<span class="fl-cap">Lives left</span>` (3793) / `<span class="fl-cap">Hill time</span>` (3786) | `<span class="fl-cap">Net frags</span>` |
| `<span class="momentum-label">LIVES LEAD</span>` (1576) | `<span class="momentum-label">FRAG LEAD</span>` |
| `<span class="lives-label">Lives</span>` (2241) | `<span class="frag-label">Frags</span>` |
| `.lk-cap` "Filling hoppers with fresh paint…" (1480) | "Loading the map…" |
| `#clock-caption` "In the locker room" (1499) | "Marines to the deck" |
| `#mmwarn` "Replay hash mismatch — showing recorded inputs" (1524) | "Replay hash mismatch at tick N — showing recorded inputs" |
| `#btn-spoilers` title "kills / flag story / winner on the timeline ahead of the playhead (o)" (1564) | "frags / streaks / lead changes on the timeline ahead of the playhead (o)" |

**`tests/test_vzd_endcard_labels.nim`** greps the built `index.html` and `broadcast_core.js` for a
forbidden-vocabulary list — `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`, `hopper`,
`hill`, `spray`, `grenade`, `Tags`, `tagout` — outside comment blocks, and asserts **zero** matches;
and asserts each replacement string above is present exactly once. `POV`, `EYES` and `kill` are
**not** forbidden: the POV lens and the first-person inset are kept, and `kill` is a live event kind.

### Transport rules

`relayout()` sets **`--band`** (the measured transport strip), `--topband` and **`--hudscale`** on
`:root`, unchanged (starter lines 4291-4318). **No overlay sits in the transport band**: every
addition here (`#eyes`, `#fragbug`, the feed, the banners, and the inherited `#fpv`) lives inside
`#chrome`, whose box is `inset: var(--topband) 0 var(--band) 0`, so nothing can reach below the band;
`#fpv`'s default anchor is `bottom: calc(64 * var(--u))` inside that box, kept. The **endcard stops at
`var(--band)`** (`#endcard { bottom: var(--band, 0px) }`, starter line 1047, kept) so the scrubber
stays clickable underneath, and it is **dismissed by every seek** (the starter's
`$('endcard').classList.remove('on')` path, kept). **Scrubber beats are clickable, labelled buttons**:
the appended block's `dmBeat(tick, kind, side, label)` — named with a `dm` prefix so it can never
shadow `chrome_common.js`'s hoisted `var markBeat = C.markBeat` alias (the tandem 2026-08-23 hoisting
trap) — appends `<button class="beat-marker <kind> <side>" title="…" aria-label="…">` to `#scrub` and
seeks on click. CSS exists for **every kind emitted and no others**: `.beat-marker.gamestart`,
`.kill`, `.streak`, `.lead`, `.fallback`, `.gameover`. The game block never calls `markBeat`, so an
unlabelled div marker cannot appear.

**Playback rate: 1 tick per frame at `ReplayFps = 24`** (speed chips `[1, 2, 3, 4, 8, 16]`, the
starter's `PlaybackSpeeds`, default **1×**). A 2592-tick episode plays for **108 s**, and the
1080-tick certification replay for **45 s**, which is what lets `viewer_smoke.mjs --soak 10` observe
real advancement instead of a legitimately-finished replay (the ecos 2026-08-23 scar).

### Readouts

1. **The board**, drawn edge to edge: the baked arena floor and textured walls, the glass windows
   drawn as translucent panes, the med kits, and the eight cogs in their team kits with a heading
   chevron. A dead cog is a fading corpse marker with its respawn pip; a cog on a streak of ≥ 3 gets a
   soft amber halo.
2. **Vision cones** — every cog's 90° cone drawn as a translucent wedge, clipped by walls exactly as
   the sim clips it, so a spectator can see who is about to be able to see whom. This is the game made
   visible; without it a spectator sees eight dots wander.
3. **Shots** — the starter's impact rings and muzzle flashes, kept verbatim (shots are invisible to
   players but visible to the spectator, which is the whole spectator advantage).
4. **`#eyes` — eight first-person thumbnails**, one per seat, in the top band under the scorebug, in
   slot order `RED-alpha…delta` then `BLUE-alpha…delta`. Each is a 32-column raycast strip of that
   cog's cone at 600 px depth (§Sim module, recomputed every 4th frame), captioned with the alias and
   the seat's frag count, tinted by team, dimmed while the cog is dead, and **clickable — a click puts
   that seat in the big `#fpv` POV inset** (the starter's `togglePov`, reused through `PB_CTX`). This
   is the idea's "per-seat first-person thumbnails", delivered on the starter's own raycaster. Under
   `.tiny` (board ≤ 620 px, i.e. the 360 px featured embed) the eight thumbnails collapse to eight
   labelled chips: eight 45×30 raycast strips are illegible at that width, and the chips still drive
   the full-size POV inset.
5. **`#fpv` — the big first-person inset**, the starter's, unchanged: 96-column raycast of the selected
   seat's cone with billboarded contacts, its HUD (`#fpv-name`, `#fpv-hp`, `#fpv-gear`), its
   fog-honest mini-map (`#fpv-map`), the `EYES` caption, drag and resize. `#povBadge` announces the
   lens and clears it. This is the "first-person 3D" gap the idea says the site has.
6. **Scorebug** — four plates in `#plates-l` (RED) and four in `#plates-r` (BLUE): each carries the
   seat's **real policy name** (spectator side only), its in-game alias, a team colour chip, its
   `frags−deaths`, and a `↯` glyph on any seat that has taken a fallback. `#fragbug` between them
   shows the two team net totals and the margin as a big numeral. `#clock` shows the game clock;
   `#clock-time` shows `tick 1284/2592 · turn 12/24`; `#clock-caption` shows
   `RED 11 frags 9 deaths · BLUE 9 frags 11 deaths`.
7. **Match feed** (`#killfeed`) — plain language, never internal notation: `RED-beta FRAGS BLUE-alpha`,
   `BLUE-delta FRAGS RED-gamma — 3 IN A ROW`, `RED-alpha TEAM-KILLS RED-delta (−1)`,
   `BLUE-beta picks up a med kit`, `RED-gamma respawns`, `RED takes the lead, +3`,
   `RED-beta: "mid"` (shouts, with the bubble on the board),
   `RED radio: "BLUE-alpha is in C2 at 3hp, I take the north door"`, and
   `BLUE-gamma MISSED THE CALL — scripted order (timeout)`.
8. **Momentum graph** — the starter's `#momentum` SVG retargeted to the cumulative frag margin across
   the game, with lead changes marked and the playhead tracked. From the pre-scan, so it draws at full
   width immediately.
9. **Endcard** — `RED 14 — 9 BLUE · MARGIN +5` (or `DRAW`), the episode line `SCORE 0.708 / 0.292`,
   the eight-row table under the re-mapped header (`Cog | Frags | Deaths | Net | Acc`), and a summary
   line (`arena · 23 frags · 2 team kills · 6 med kits · longest streak 3`). It stops at `var(--band)`
   and any seek dismisses it.
10. **Transport and integrity** — play/pause, step back, +5 s, jump to end, loop, skip-lulls (a lull =
    120 consecutive ticks with no `kill`, `hit`, `streak`, `lead` or `pickup` event, from the
    pre-scan), spoilers switch, tick readout, speed chips, the scrubber with its six beat kinds, and
    `#mmwarn` on a hash mismatch — all the starter's, verbatim.

### Art

**Real art, no placeholders, no solid-colour squares.** Two sources, both committed:

- **The starter's shipped assets, byte-for-byte**: `data/soldier_{red,blue}.png` and the crown-free
  rotation masters through `rig_art.nim`'s existing compositor;
  `data/soldier_{red,blue}_front{,_gun}.png` — the FPV billboards the raycaster already blits;
  `data/medkit.png`; `data/arena_floor.png` tiled and darkened at install; `data/font.ttf`,
  `data/ascii.png`, `data/pallete.png`; `client/art/walls/{wall_h,wall_v}.jpg` for the wall faces; and
  `client/art/lockerroom/{bg.jpg,red_*,blue_*}.webp` for the loading screen. All of it is already the
  art of a two-team shooter — nothing here needs replacing to be real.
- **One nano-banana generation** (`playbooks/art-nanobanana.md`, `gemini-2.5-flash-image`, **≤ 2
  generations total**), anchored on the starter's own cog reference as an `inline_data` part: a single
  sheet carrying (a) a **visored helmet overlay** for the two team kits, so a cog reads as a marine
  rather than a paintballer at board scale, and (b) the **frag skull glyph** used by the kill feed row,
  the `.beat-marker.kill` marker and the endcard. `scripts/art/split_cog_sheet.py` chroma-keys and
  splits it into `data/helm_red.png`, `data/helm_blue.png`, `data/glyph_frag.png`, committed alongside
  `scripts/art/source/marines_sheet.png`, and the helmets are composited by the **existing**
  `rig_art.nim` plumbing (same masters, pivots, scale, `SoldierRotations` facings). If the Gemini
  endpoint is unavailable at build time the builder ships the starter's kits unmodified and a
  procedural skull in the bake's palette, and says so in `log.md` — never a flat rectangle.

### Legible at 360 px

The embedded featured-match iframe is ~360 px wide, so the chrome is checked **at 360 px**, not at
desktop width — and the starter already engineers exactly this: `relayout()` sets
`--hudscale = clamp(0.5, boardW/760, 1.6)` and toggles `#stage.tiny` at `boardW <= 620`, both kept
verbatim (starter lines 4307-4312). The board's aspect is `1235/659 = 1.874`; in a 360 × 203 frame
width binds, so the board renders at **360 × 192** — the whole arena in frame, which is why
`#viewpanel` is dropped. At that scale a cog body is 10 px and a cone 460 px long. Five rules are added
and asserted by `tests/test_vzd_viewer.nim`:

1. `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` so a
   policy name never collapses to "…" (the starter already ships this rule at `replay_broadcast.html:4368`; it is kept).
2. Under `.tiny`, each plate keeps only `alias + name + net`; the colour chip shrinks to 6 px and the
   fallback glyph moves inline.
3. Under `.tiny`, `#eyes` renders eight **chips** instead of eight raycast strips (§Readouts 4), and
   `#fragbug` drops to `RED 11 — 9 BLUE`.
4. Under `.tiny`, cone wedges drop to 45 % alpha so eight overlapping cones stay readable, cog aliases
   are not drawn on the board (they are on the plates), and the feed shows three rows instead of four.
5. All sizes derive from `--hudscale` so nothing is ever drawn outside the canvas
   (`--strict-text-bounds` stays on, and `canvas_text.never_inside` must be 0 — this is a fixed board).

---

## Packaging

- **Repo**: `Metta-AI/cogame-vizdoom-deathmatch`, **public at creation** (public is a certification
  prerequisite — `source-resolves` 404s on private). Slug `vizdoom-deathmatch`; **`game.name` is
  `vizdoom-deathmatch`** so the secret namespace
  `secret://coworld/vizdoom-deathmatch/anthropic_api_key`, the page slug
  `softmax.com/vizdoom-deathmatch`, the `POST /coworld-league-seeds` body and the docs all agree (the
  cooperative-hunting 2026-08-25 scar).
- **`compose.yaml`** — **one** service, because the manifest image placeholder is derived from the
  compose service name by uppercasing and mapping `-` → `_` (`{{GAME_IMAGE}}` is not a thing —
  lantern 0.1.0). ctf ships two services/two images; this fork uses the one-image / two-entrypoints
  shape because the shared `docker_smoke.sh` and `policies.json` assume a single image:

  ```yaml
  services:
    vizdoom-deathmatch:
      image: coworld-vizdoom-deathmatch:latest
      platform: linux/amd64
      build:
        context: .
        dockerfile: Dockerfile
        network: host
  ```

  ⇒ placeholder **`{{VIZDOOM_DEATHMATCH_IMAGE}}`**.
- **`Dockerfile`** — the starter's two-stage debian-slim + nimby layout verbatim in structure (pinned
  nimby 0.1.26, `nimby use 2.2.4` — the starter's `Dockerfile:29` — `nimby --global sync nimby.lock`),
  building **two** binaries: `nim c -d:release -d:useMalloc --opt:speed --stackTrace:on
  --out:vizdoom-deathmatch src/vizdoom_deathmatch.nim` → `/bin/vizdoom-deathmatch`, and the same for
  `src/vizdoom_deathmatch_player.nim` → `/bin/vizdoom-deathmatch-player`. (The Nim module tree is
  `src/vzd/`; only the two entry files and the binaries carry the dashed slug, because Nim identifiers
  cannot.) The runtime stage copies both binaries, `data/`, `*.json`, **and `client/`** (the starter's
  Dockerfile omits `client/`; this fork adds it so `/client/player` and `/client/global` serve real
  pages for the certifier's probes — the lantern 0.1.1 scar). `CMD ["/bin/vizdoom-deathmatch"]`,
  runtime `--platform=linux/amd64`.
- **`Dockerfile.replay-viewer`** — the starter's verbatim (pinned `emscripten/emsdk`, pinned nimby with
  its sha256 check, the three marker splices `<!-- WIRE_CONSTANTS -->` / `<!-- CHROME_COMMON -->` /
  `<!-- BROADCAST_CORE -->`, and the whole `test -f` / `grep -q` assertion block) with the asset list
  swapped to `data/{arena_floor,ascii,pallete,medkit}.png`, `data/soldier_{red,blue}*.png`,
  `data/helm_{red,blue}.png`, `data/glyph_frag.png`, `data/font.ttf`, `client/art/walls/*`,
  `client/art/lockerroom/*`, `vzd_replay.{js,wasm,data}`, `wire_constants.js`, `broadcast_core.js`,
  `chrome_common.js`, `static_replay.js`, `static_replay_worker.js`, `index.html`, and the
  `grep -q '^window.VZD_WIRE={'` assertion.
- **`coworld_manifest_template.json`** — the starter's `coworld_manifest_paintbot.json` as the shape,
  with these decisions:
  - `$schema` present; top-level `tags: ["shooter", "deathmatch", "first-person", "team",
    "vizdoom"]` (≥ 3; `game.tags` must **not** exist — pistonball 0.1.0); **`episode_timeout_minutes:
    20` at the top level**, not under `game`.
  - `game.name = "vizdoom-deathmatch"`, `game.owner = "daveey@softmax.com"`, `game.description`
    present (required), `game.runnable.type = "game"`,
    `game.runnable.run = ["/bin/vizdoom-deathmatch"]`,
    `game.replay_viewer = {"bundle": "static-replay-viewer"}` **under `game`** (not top-level),
    `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/vizdoom-deathmatch/anthropic_api_key"`.
  - `game.config_schema` a real JSON Schema, `additionalProperties: false`,
    `required: ["tokens", "players"]`; **every array property carries `minItems`/`maxItems`**
    (`tokens` 8/8, `players` 8/8, `slots` 8/8 — the tandem 0.1.0 scar). `tokens` is described as
    runner-injected; **no `game_config` anywhere in this manifest contains a literal `tokens` array**
    (matriculate rejects "game_config must not include runner-managed tokens" — knights-archers
    0.1.0), while `config_schema` keeps *requiring* it because the runner injects it. Properties:
    `tokens`, `players`, `slots`, `seed`, `mapPath` (enum `["arena","pool"]`), `mapSize`
    (enum `["standard"]`), `mapPoolIndex`, `teams` (const 2), `cogsPerTeam` (const 1), `minPlayers`,
    `closedRoster`, `lives`, `hitPoints`, `respawnTicks`, `gunRange`, `fireCooldownTicks`,
    `fireWindupTicks`, `aimTurnRate`, `visionConeDeg`, `visionBubble`, `turnTicks`, `maxTicks`,
    `maxGames`, `attempt1Ms`, `retryMs`, `turnBudgetMs`, `turnSpacingMs`, `wallClockBudgetSeconds`,
    `lobbyJoinTimeoutTicks`, `startWaitTicks`, `gameOverTicks`, `fastMode`, `showPlayerLabels`,
    `mapSpec`, `maxOutputTokens`, and **`num_agents` (integer, `minimum: 8`, `maximum: 8`,
    default 8)**.
  - `game.results_schema` closed and exactly the keys in §Server, with
    `reason: {"type":"string","enum":["complete","deadline","fault"]}` and
    `endRule: {"type":"string","enum":["full_time","wall_clock","sim_fault","host_error"]}`.
  - **`game.protocols` carries BOTH `player` and `global`**, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-vizdoom-deathmatch/blob/main/docs/PROTOCOL.md"}`
    — objects, never bare strings (the garble v0.1.0 scar). Both point at the same document because
    both streams speak Sprite v1 with the same extensions, exactly as the starter declares them.
  - **`game.docs`** = `{"readme": {"type":"text","value":"<the README body, inlined>"},
    "pages": [{"id":"rules.md","title":"Rules","content":{"type":"text","value":"<docs/RULES.md
    inlined>"}}, {"id":"observation.md","title":"What a seat sees",
    "content":{"type":"text","value":"<docs/OBSERVATION.md inlined>"}},
    {"id":"protocol.md","title":"Wire protocol","content":{"type":"text","value":"<docs/PROTOCOL.md
    inlined>"}}]}` — inlined text so the pages render before the repo is indexed.
  - Top-level `player[]` with `id`/`type`/`name`/`description`/`image`/`run`/`source_url` and
    `resources: {requests: {cpu: "200m", memory: "128Mi"}, limits: {cpu: "1"}}` — **`limits.cpu` must
    be at least `"1"`** (pistonball 0.1.1). Two entries, `rusher` and `sentry`, so **every declared
    player occupies a certification slot** (the raid 0.1.2 scar).

  **Variants — `num_agents: 8` inside each `game_config`, never at a variant's top level**
  (`CoworldVariant` is `additionalProperties: false` and the platform reads only
  `game_config.num_agents` — goofspiel-oshi-zumo 0.1.0). `players` and `slots` are 8 long in both, and
  `slots` alternates `red, blue, …`, which is what makes seats 0/2/4/6 RED:

  ```json
  "variants": [
    {"id": "arena", "name": "Arena deathmatch (4v4, hand-tuned map)",
     "description": "Eight cogs, four red against four blue, on the hand-tuned symmetric arena. Each cog sees only its own 90-degree cone: a sixteen-ray depth strip and a labelled list of whatever is inside it. Hitscan gun, three hit points, two-second respawns, friendly fire on. Every 4.5 seconds each seat gives its cog one order and a deterministic driver walks it, turns it and pulls the trigger. After 108 seconds the two teams' frags minus deaths are compared and the margin is the score.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"},
                                 {"name":"Cog5"},{"name":"Cog6"},{"name":"Cog7"},{"name":"Cog8"}],
                     "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"},
                               {"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}],
                     "num_agents": 8, "minPlayers": 8, "closedRoster": true,
                     "teams": 2, "cogsPerTeam": 1,
                     "mapPath": "arena",
                     "lives": 60, "hitPoints": 3, "respawnTicks": 48,
                     "gunRange": 1050, "fireCooldownTicks": 12, "fireWindupTicks": 5,
                     "aimTurnRate": 5, "visionConeDeg": 45, "visionBubble": 90,
                     "turnTicks": 108, "maxTicks": 2592, "maxGames": 1,
                     "attempt1Ms": 8000, "retryMs": 3000,
                     "turnBudgetMs": 12000, "turnSpacingMs": 5000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "startWaitTicks": 120, "gameOverTicks": 240,
                     "maxOutputTokens": 900,
                     "fastMode": true, "showPlayerLabels": false}},
    {"id": "pool", "name": "Pool deathmatch (4v4, seeded map)",
     "description": "The same 4v4 deathmatch on a map drawn from the curated twenty-seed terrain pool by the episode seed, so no policy can learn one layout. The geometry is pinned into the replay, so a replay always renders the map it was played on. Same 108 seconds, same frags minus deaths, same 90-degree cone.",
     "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"},
                                 {"name":"Cog5"},{"name":"Cog6"},{"name":"Cog7"},{"name":"Cog8"}],
                     "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"},
                               {"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}],
                     "num_agents": 8, "minPlayers": 8, "closedRoster": true,
                     "teams": 2, "cogsPerTeam": 1,
                     "mapPath": "pool", "mapSize": "standard", "mapPoolIndex": -1,
                     "lives": 60, "hitPoints": 3, "respawnTicks": 48,
                     "gunRange": 1050, "fireCooldownTicks": 12, "fireWindupTicks": 5,
                     "aimTurnRate": 5, "visionConeDeg": 45, "visionBubble": 90,
                     "turnTicks": 108, "maxTicks": 2592, "maxGames": 1,
                     "attempt1Ms": 8000, "retryMs": 3000,
                     "turnBudgetMs": 12000, "turnSpacingMs": 5000,
                     "wallClockBudgetSeconds": 660, "lobbyJoinTimeoutTicks": 2400,
                     "startWaitTicks": 120, "gameOverTicks": 240,
                     "maxOutputTokens": 900,
                     "fastMode": true, "showPlayerLabels": false}}
  ]
  ```

  **Certification fixture** — `num_agents: 8` again, inside `certification.game_config`, and exactly
  eight players so that
  `len(certification.players) == len(certification.game_config.players) == num_agents == SMOKE_SEATS
  == 8` (the four `SEAT-COUNT` invariants `docker_smoke.sh` cross-checks), with **both** declared
  players seated and both teams mixed:

  ```json
  "certification": {
    "players": [{"player_id":"rusher"},{"player_id":"rusher"},{"player_id":"sentry"},
                {"player_id":"sentry"},{"player_id":"rusher"},{"player_id":"rusher"},
                {"player_id":"sentry"},{"player_id":"sentry"}],
    "game_config": {"players": [{"name":"Cog1"},{"name":"Cog2"},{"name":"Cog3"},{"name":"Cog4"},
                                {"name":"Cog5"},{"name":"Cog6"},{"name":"Cog7"},{"name":"Cog8"}],
                    "slots": [{"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"},
                              {"team":"red"},{"team":"blue"},{"team":"red"},{"team":"blue"}],
                    "num_agents": 8, "minPlayers": 8, "closedRoster": true,
                    "teams": 2, "cogsPerTeam": 1, "seed": 42,
                    "mapPath": "arena",
                    "lives": 60, "hitPoints": 3, "respawnTicks": 48,
                    "gunRange": 1050, "fireCooldownTicks": 12, "fireWindupTicks": 5,
                    "aimTurnRate": 5, "visionConeDeg": 45, "visionBubble": 90,
                    "turnTicks": 108, "maxTicks": 1080, "maxGames": 1,
                    "turnSpacingMs": 0, "wallClockBudgetSeconds": 240,
                    "lobbyJoinTimeoutTicks": 600, "startWaitTicks": 0, "gameOverTicks": 24,
                    "fastMode": true, "showPlayerLabels": false}
  }
  ```

  1080 ticks is 10 turns — about a second of sim but **45 s of playback**, which the viewer soak
  needs. `turnSpacingMs: 0` because certification runs with no API key and every seat is scripted.
  Seed 42 on `arena` is asserted by `tests/test_vzd_engine.nim` to produce at least **four `kill`
  events and one `respawn`** inside those 1080 ticks, so the CI smoke replay always exercises the
  combat path, the kill feed and the beat markers. Four `rusher` seats against four `sentry` seats
  guarantees contact. The certify step in `coworld-release.yml` passes **`--timeout-seconds 300`**
  (the default 60 covers start + connect grace + play + linger — cooperative-hunting 0.1.3).
- **`tools/ci/policies.json`** — four policies, one image, `run: "/bin/vizdoom-deathmatch-player"`,
  following the starter's `tools/ci/paintball_policies.json` shape (including `PLAYER_POLICY_LABEL`):

  ```json
  [{"name":"vzd-pointman","run":"/bin/vizdoom-deathmatch-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text above>","PLAYER_POLICY_LABEL":"pointman"}},
   {"name":"vzd-crossfire","run":"/bin/vizdoom-deathmatch-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text above>","PLAYER_POLICY_LABEL":"crossfire"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"vzd-rusher","run":"/bin/vizdoom-deathmatch-player",
    "env":{"PLAYER_SCRIPTED":"rusher","PLAYER_POLICY_LABEL":"rusher"}},
   {"name":"vzd-sentry","run":"/bin/vizdoom-deathmatch-player",
    "env":{"PLAYER_SCRIPTED":"sentry","PLAYER_POLICY_LABEL":"sentry"}}]
  ```

  Champions #1 and #2 are the two `PLAYER_PROMPT` policies (#1 owned by daveey, #2 by daveey-1,
  uploaded while daveey-1 is the active player); the fillers are `rusher` and `sentry`, and their
  versions must differ from the champions'. No `USE_BEDROCK` flag: the LLM call is made by the
  **game** pod.
- **CI** — `.github/workflows/ci.yml` is coworld-builder's `templates/ci.yml`: the `test` job keeps the
  template's nimby/Nim toolchain and runs every `tests/*.nim` in debug and release, and the
  `docker-smoke` and `wasm-viewer` jobs are taken **unchanged** with `<slug>` → `vizdoom-deathmatch`,
  `<IMAGE>` → `coworld-vizdoom-deathmatch`, `<SEATS>` → **`8`**, plus `SMOKE_REQUIRE_REPLAY_JSON=0`
  (§Server) and `--soak 10` added to the `viewer_smoke.mjs` invocation. `coworld-release.yml` and
  `coworld-submit.yml` are the templates, with `--timeout-seconds 300` on the certify step.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed **executable**
  (mode 100755) — CI asserts the bit and invokes them by path.

---

## Tests

Nim, in the starter's layout: `tests/test_vzd_*.nim`, imported by the four balanced shards
(`tests/shard_1..4.nim`) and by `tests/tests.nim`, run from the repo **root** with
`nim c -r tests/tests.nim` locally and by `ci.yml`'s `test` job (which runs every `tests/*.nim` in both
debug and `-d:release`). `tests/config.nims` (`--path:"../src"`) and `tests/helpers.nim` are the
starter's, unchanged.

**Sim unit tests** (`tests/test_vzd_sim.nim`)

1. `seating` — an 8-seat / `cogsPerTeam: 1` config yields 8 cogs, four per team by slot parity;
   `cogAlias` returns eight **distinct** names `RED-alpha..delta` / `BLUE-alpha..delta` (the
   `cogIdentityIndex` edit — without it all four reds are `alpha`); and no seat can change its team.
2. `squad mode is live at one cog per seat` — `squadMode` is true for `numAgents: 8, cogsPerTeam: 1`
   (the `server.nim:1367` edit); with the starter's original gate the engine is dead and every cog is
   motionless, so this test is the guard on the whole game existing.
3. `gun` — a shot along a clear line at ≤ 1050 px removes one hit point; a wall between shooter and
   target blocks it; a glass window does **not** block vision but **does** block the bullet; the aim
   locks at the trigger pull and a target that steps behind cover during the 5-tick windup survives;
   `fireCooldownTicks` gates the next shot; simultaneous windups resolve against one post-movement
   snapshot so a mutual kill is a genuine trade.
4. `death and respawn` — the third hit kills; `recordKill`/`recordDeath` fire exactly once each; a
   team kill calls `recordTeamKill` and **not** `recordKill`; the cog returns after exactly
   `respawnTicks` at its own spawn pocket with hp 3 and its aim pointed at the enemy side; a dead cog
   emits the zero mask and cannot fire, move or be hit.
5. `no wipe is reachable` — for every shipped variant and the cert fixture,
   `lives > maxTicks div (respawnTicks + 1)`; and over 200 seeded all-scripted episodes no episode ever
   produces `endRule == "wipe"` or `"mercy"`.
6. `vision` — the cone is 45° each side of aim and dies at exactly `visionRange = 1575`; a target
   behind a wall is invisible at 40 px; the 90 px bubble does not see through a wall; aim carries
   vision (rotating the aim without moving changes the visible set).
7. `rays match the sim` — for 200 random cog poses, `marchRays(…, 16, visionRange)`'s distances agree
   with `lineOfSightClear` along the same bearings to within one march step, **and** the 16-ray strip
   agrees with the 96-column `firstPersonJson` sampled at the same bearings. The model and the viewer
   cannot disagree about a wall.
8. `zones` — `zoneAt` partitions the whole board with no gap and no overlap; the 15 centres are all
   walkable or snap to a walkable cell; the terrain word is a pure function of the installed map; and
   the red spawn is in column A, the blue in column E, on both variants' maps.
9. `frag accounting` — `net[c] == frags[c] - teamFrags[c] - deaths[c]` after every tick;
   `sum(deaths) == sum(frags) + sum(teamFrags)` exactly (every death has exactly one cause);
   `margin(Red) == -margin(Blue)`.
10. `scoring` — `scorePermille` matches the formula for 500 randomised end states,
    `scorePermille[red] + scorePermille[blue] == 1000` exactly, `scores ∈ [0, 1]`,
    `win == (scorePermille > 500)`, and a zero margin leaves every `win` false and every score 0.500.
11. `end conditions` — `full_time`, a forced wall-clock stop and a forced fault each produce the right
    `endRule` and the right `reason`; a deadline in mid-game settles from the frag counters at that
    tick, records `finalTick < maxTicks`, and is still exactly zero-sum.
12. `no new floats in hashed code` — a source grep over `src/vzd/{deathmatch,zones,motion}.nim` finds
    no float literal, no `/` and no `sqrt`; `vision.nim`'s and `combat.nim`'s inherited float maths is
    whitelisted by exact line range and asserted byte-identical to the starter's; `egoview.nim` is
    whitelisted wholesale and a test asserts nothing it returns reaches `gameHash`.
13. `tick budget` — a full 2592-tick, eight-cog, all-scripted episode completes in < 12 s in a release
    build, and no single tick exceeds 8 ms.
14. `seeding` — the `pool` entry is a pure function of the seed; the home deal, the med-kit orbit and
    the aim-fuzz stream are drawn in the fixed order of §Sim module **before any seat connects**; and
    **none** of it changes when seat behaviour changes (the anti-collusion pin).

**Bounded orders / legality on the scripted baselines** (`tests/test_vzd_control.nim`)

15. `baselines are bounded` — for 200 pseudo-random world states (both maps, every seat, cogs alive and
    dead, hp 1..3, med kits taken and available, contacts present and absent) and for **both** `rusher`
    and `sentry`: the returned order has an `intent` in the enum, an `at` that is a published zone id or
    a live contact alias, a `to` inside the board, `say` ≤ 10 runes, `radio` and `notes` empty, and a
    serialised directive ≤ 900 runes. A baseline that ever proposes an illegal or unbounded order fails
    the build.
16. `driver never emits an illegal mask` — over the same states, every compiled mask uses only the
    d-pad, `A`, `B` and `Select` (never `C` — there is no grenade and no barrier here); Up and Down are
    never both set and neither are Left and Right; a dead cog's mask is exactly `0`; no order can leave
    a cog with no mask; and a target inside a wall degrades to `hold`, never to a cog pressing the same
    direction forever (the starter's `StuckTicks` path, exercised).
17. `the trigger never causes friendly fire` — over 500 randomised firing geometries, the driver
    presses `A` **only** when a live enemy is visible this tick, in range, inside `FireAimBrads`, with a
    clear line, **and** no teammate body box intersects the bullet corridor; and it never presses `A`
    at a memory (`ticks_ago > 0`) or at nothing.
18. `fallback is the rusher proc` — the decision engine's fallback path and the `rusher` baseline
    resolve to the same proc, so they cannot drift; and an unregistered seat plays `rusher`.
19. `reply validation` — the validator accepts the schema, **repairs** an unknown intent to `hunt` and
    an unresolvable `at` to `to`, clamps `to`, resolves `at` over `to`, accepts a `say`-only reply,
    accepts the legacy `cogs:[…]` single-entry form, rejects a non-object, truncates
    `say`/`radio`/`notes` on **rune** boundaries at 10/96/160 with 4-byte emoji sitting exactly on each
    boundary, caps the read at 4096 bytes, and never leaves a cog without an order.
20. `baseline tuning is the swept pick` — the shipped four tunables equal
    `tools/ci/baseline_tuning.json` (the starter's `test_tuning` pattern; `ci.yml` re-runs the sweep
    with `--check`), and the recorded `rusher`-vs-`sentry` team margin over 6 seeds is inside
    `[+2, +10]` frags.

**End-to-end episode writing a replay** (`tests/test_vzd_engine.nim`)

21. `episode writes artifacts` — run a real eight-seat episode (`arena`, `maxTicks 1080`, all seats
    scripted, no API key so the LLM client is `disabled`) against a temp-dir `COGAME_*` URI set; assert
    `results.json` and the `.replay` are written, `reason == "complete"`, `endRule == "full_time"`,
    `games == 1`, `scores[red] + scores[blue] == 1.0` exactly, every seat-indexed array is 8 long, and
    the results key set equals the manifest's `results_schema` key set **exactly**.
22. `the cert seed is interesting` — seed 42 on `arena` with the fixture's 4 × `rusher` + 4 × `sentry`
    yields ≥ 4 `kill` events and ≥ 1 `respawn` inside 1080 ticks, so the CI smoke replay always
    exercises combat, the kill feed and the beat markers.
23. `no seat can stall` — a seat that connects then never answers, and a seat that never connects at
    all, both produce a finished episode inside the wall-clock budget, with `fallbackTurns` counted,
    `deadSeats` set, and exactly one closed-schema `{"message","failed_policy_index"}` failure payload.
24. `budget guard and rate guard settle early` — with each guard forced, the episode finishes
    `complete` / `full_time`, not `deadline`, and the matching record names the turn. Also asserts the
    guard's edit: with `effectiveSpacingMs(8) = 17143 > turnBudgetMs = 12000`, the guard fires against
    the **larger** of the two.
25. `the rate floor is derived` — `effectiveSpacingMs(n)` is 5000 at n ≤ 2 and 17143 at n = 8, the
    rolling 60 s counter never lets a trailing minute exceed 28 requests, and a skipped call is
    recorded as `fallback` with `cause == "rate_guard"`.

**Replay** (`tests/test_vzd_replay.nim`)

26. `record then re-derive, every end reason` — for `full_time`, `wall_clock` **and** `sim_fault`,
    record an episode and re-derive it from the bytes; assert identical hashes at every tick
    **including the stop tick** (the particle-worlds scar).
27. `replay is self-sufficient` — the bytes alone yield seat names, aliases, teams, policy kinds, the
    full config **including the resolved `mapSpec`**, the seed, every mask, every chat record and the
    result; deleting the map pool from disk does not change what the bytes render.
28. `replay_summary is strict UTF-8 JSON` — run `tools/replay_summary.py` over a replay whose every
    capped field is filled to exactly its cap with 4-byte emoji; assert the output parses under a
    **strict** UTF-8 JSON parser, contains no lone surrogates, and reports
    `protocol == "vizdoom-deathmatch/v1"`.
29. `every committed fixture carries the current GameVersion` — the starter's sweep over `tests/`,
    kept, over all committed `.bitreplay` fixtures.

**Manifest** (`tests/test_vzd_manifest.nim`)

30. `manifest pins` — `num_agents == 8` in **both** variants' `game_config` **and** in
    `certification.game_config`; `num_agents` absent at every variant top level; no literal `tokens` in
    any `game_config`; `len(player) == 2` and every declared player seated in `certification.players`;
    `len(certification.players) == len(certification.game_config.players) == 8`; every `players` and
    `slots` array is 8 long and `slots` alternates red/blue; every array in `config_schema` has
    `minItems`/`maxItems`; `episode_timeout_minutes` top-level; both `game.protocols.player` and
    `.global` present as `{"type","value"}` objects; `game.docs.readme` + three `pages`, every value
    non-empty text; `game.description` present and `game.tags` absent; ≥ 3 top-level tags;
    `player[].resources.limits.cpu >= "1"`; every `wallClockBudgetSeconds <= 660`; and
    `24 * effectiveSpacingMs(8)/1000 + 134 <= 660` for every variant.
31. `every variant constructs and resolves to 1235x659` — each variant's `game_config` builds a valid
    `GameConfig`, installs its map, and reports `MapWidth == 1235 && MapHeight == 659` (the collab-cooking
    0.1.1 scar: test every variant, not just the fixture). This is also the assertion `#viewpanel`'s
    removal rests on.
32. `manifest loads under the installed CLI` — a CI step runs the installed `coworld`'s own
    `validate_upload_manifest` / `_load_template_manifest` (0.1.42 wants `game.replay_viewer`, no
    top-level `version`, no `game.display_name`, `game.owner` required, no runner-managed `tokens` —
    the collab-cooking 2026-08-25 scar).

**Viewer** (`tests/test_vzd_viewer.nim`, static assertions in the `test` job)

33. `chrome_common is the starter's, patched exactly twice` — `client/chrome_common.js` is 40 022
    bytes, the starter's own length (the named wire patch above is length-preserving), its hash is
    pinned as a literal, and `window.VZD_WIRE` appears exactly where `window.CTF_WIRE` did.
34. `broadcast html is starter plus block` — the file begins with the starter's bytes up to the
    documented splice marker and only appends after it; `broadcast_core.js`'s kept procs are
    byte-identical to the starter's, `pushFeed`'s signature included.
35. `no shadowed chrome aliases` — no identifier in the appended game block collides with any name in
    `chrome_common.js`'s alias list (the tandem hoisting trap); the beat builder is `dmBeat`, never
    `markBeat`.
36. `beat CSS matches emitted kinds` — the set of `.beat-marker.<kind>` rules equals exactly
    `{gamestart, kill, streak, lead, fallback, gameover}`.
37. `transport, endcard and 360 px rules` — `#endcard { bottom: var(--band` present; `relayout()` sets
    `--band`/`--topband`/`--hudscale` on `:root`; no game-block element is positioned inside the band;
    the five 360 px rules exist; the removed ids (`#viewpanel`, `#minimap`, `#zoombar`, `#pb-regime`,
    …) appear nowhere; and `#fpv`, `#fpv-canvas`, `#fpv-map`, `#povBadge` and `#eyes` **do** appear.
38. `no root-absolute asset references` — the starter's own `test_first_person_pip.nim` scan, kept and
    extended to the new art: every asset in `index.html` and `league.html` loads through `COG_BASE` /
    `ART_BASE`, never from `/`.
39. `endcard labels` — `tests/test_vzd_endcard_labels.nim`: zero matches for the forbidden ctf/paintbot
    vocabulary outside comments, and each re-mapped string present exactly once (§Viewer).
40. `label manifest` — the starter's `test_label_contract` pattern: the emitted sprite/label vocabulary
    (`medkit`, `frag`, `respawning`, `own aim <brads>`, …) equals `tests/label_manifest.txt`,
    regenerated in the same commit as any label change.
41. `events are the closed enum` — `tests/test_vzd_events.nim`: the set of kinds `stepEvents` can emit
    equals exactly the sixteen listed in §Server, and every kind the appended game block consumes is in
    that set.

**Viewer smoke — the bundle is EXECUTED, not merely built**

42. **`tools/ci/viewer_smoke.mjs`** (copied verbatim from
    `coworld-builder/templates/tools/ci/viewer_smoke.mjs`, no substitutions) is run by **`ci.yml`'s
    `wasm-viewer` job**, which `needs: docker-smoke` and runs it against **the replay `docker-smoke`
    produced** (downloaded as the `smoke-replay` artifact), in headless chromium (Playwright pinned in
    both the npm module and the browser download):
    `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "$replay"
    --timeout 90 --soak 10 --strict-text-bounds`. It fails the job unless `data-replay-loaded="true"`
    (or the bridge `ready` posted after it) arrives, the clock/tick readouts **advance** across the
    soak, and `canvas_text.never_inside == 0` — this is a fixed board, so `--strict-text-bounds` stays
    on. The 1080-tick smoke replay is 45 s of playback, comfortably outlasting the 10 s soak (the ecos
    2026-08-23 scar).
43. **`tools/ci/renderer_fixture.html`**, run by its own `ci.yml` step with
    `viewer_smoke.mjs --strict-text-bounds` — because `docker_smoke.sh` runs with **no**
    `ANTHROPIC_API_KEY`, every seat in the CI replay plays scripted and emits **no `radio` and no
    `notes`**, so the smoke replay can never exercise the feed's radio path (the cogchemists
    2026-08-24 scar). The fixture **loads the shipped `dist/static-replay-viewer/index.html` in an
    iframe** and shims only the wasm entry — it does not re-implement the drawing (the particle-worlds
    2026-08-26 scar) — driving the real page with a full-cap 96-rune `radio` and 10-rune `say` on all
    eight seats, eight live eyes thumbnails, a full kill feed, a streak halo, a lead-change beat and a
    full momentum graph, at several canvas widths **including 360 px**.
44. **`tools/wasm_replay_smoke.cjs`** — the starter's headless-node run of the *exact emitted* wasm
    module against the committed fixtures, kept: wasm32-only failures (integer traps, address-space
    exhaustion) are invisible to the native shards.

---

## Out of scope (v1)

- **The real ViZDoom / ZDoom port.** No `vizdoom` Python package, no ZDoom binary, no WAD, no
  containerised Doom host, no `PLAYER`/`HOST` multiplayer handshake, and no attempt at bit-fidelity to
  the Visual Doom AI Competition's maps or numbers. It is out for two reasons the idea itself gives:
  fidelity to the published benchmark is explicitly optional, and a ZDoom process cannot compile to
  wasm — a real port could not ship a static replay bundle and would need either a live pod viewer
  (forbidden) or a recorded video artifact. Revisiting it means a new coworld, not a variant here.
- **Raw pixel observations, and a neural policy over them.** The seat's report is a 16-ray depth strip
  and a labelled contact list — ViZDoom's depth and labels buffers written as text. A screen buffer, a
  frame stack, a CNN policy and the RL-vector protocol that would carry them are a different policy
  interface and a different manifest; this coworld is an LLM-prompt coworld with a scripted baseline,
  per the stack's standard.
- **The single-player training ladder** — `basic`, `defend the center`, `deadly corridor`,
  `health gathering`, `my way home`. Five one-seat scenarios are five more maps, five more win
  conditions, five more manifest variants and a `num_agents: 1` shape that the eight-seat league
  cannot schedule. They are a natural second coworld once this one is ranking.
- **FFA (every cog for itself).** The idea offers "zero-sum FFA **or** 4v4 team DM" and its own
  integrity note prefers the second. FFA would need per-seat scoring with no zero-sum guarantee, a
  ganging-detection story the team split makes unnecessary, and eight-way spawn balancing on a
  two-base map. `teams` is pinned to 2 in `config_schema`.
- **Seat counts other than 8.** `num_agents` is fixed at 8 in both variants and in the cert fixture,
  for the batch-size, rate-cap and wall-clock reasons in §Decisions. A 2v2 or 6-seat variant is a
  different manifest and a different cadence.
- **A second game per episode with swapped sides.** Deathmatch is symmetric, so unlike paintbot's
  resident/visitor halves there is nothing to swap; `maxGames` is 1 and the wall clock is spent on one
  longer, better game instead of two short ones.
- **Weapon variety, ammo, armour and the rest of the Doom loadout.** One hitscan gun, three hit points,
  med kits. Rocket splash, a shotgun spread, weapon pickups and an ammo economy are each a new damage
  model, a new observation field and a new prompt paragraph; the frag rule does not need them.
- **Scoring anything but the team frag margin.** `frags`, `teamFrags`, `deaths`, `net`, `damageDealt`,
  `damageTaken`, `shotsFired`, `shotsHit`, `medkits` and `longestStreak` are measured, recorded in
  `results`, shown on the endcard and in the feed, and deliberately **not** in `scores`: weighting them
  would need magnitudes the idea does not pin and would break the exact zero sum the league ranks on.
- **A tiebreak.** A margin of exactly 0 is a draw at 0.500 (§Scoring). Deliberate.
- **A live spectator pod.** `/global` broadcasts a status feed (the certifier requires it) but the
  hosted spectator experience is the static replay bundle only; no live pod viewer is declared.
- **Everything the starter had that this game does not.** Hearts, flags, pedestals, carriers, captures,
  King of the Hill, floor paint, spray cans, the paint buff, grenades, the barrage, shields, cardboard
  barriers, puddles, trenches, perks, handicaps, achievements, four-team play, the resident/visitor
  regimes, campaign mode, the oversize map classes, the map editor and mapkit — all deleted, not
  disabled (§Sim module), and none of them return in v1.
