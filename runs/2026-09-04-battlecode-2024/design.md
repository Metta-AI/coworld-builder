# cogame-battlecode — the `bc24` year module: Battlecode 2024 "Breadwars" (design note, 2026-09-04)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a
branch/PR of the shipped repo that adds the year module `bc24` beside the shipped `bc26`, `bc20`
and `bc21`, adds the manifest variant `bc24`, keeps certification on `bc26`, and bumps the version
of the *same* coworld. **There is no `cogame-battlecode-breadwars` repo and none is created.** The
starter is chosen by game shape and it is the only defensible one: bc24 is the same shape as the
three shipped years — a deterministic Nim grid sim compiled twice (native for the server, wasm for
the viewer), one sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm
replay viewer that re-derives every frame — and the year-module boundary
(`src/battlecode/years/<year>/`, `years/registry.nim`, `years/dispatch.nim`, `game_config.year`)
already exists and has now been proved twice, by bc20 and by bc21. Lineage: `coworld-ctf`
(paintbot) → `cogame-battlecode` → this. The starter is `Metta-AI/cogame-battlecode`, and **every
convention there holds here unless this note says otherwise**: the Nim sim/server/player layout, `nimby.lock`, the
bitworld runtime contract, the `GameVersion` discipline, `tools/build_replay_viewer.sh`, the
`replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch doctrine layer (`llm.nim` /
`decide.nim` / `sheet.nim` / `sheet_common.nim` / `baselines.nim`), the closed results document,
and "degrade, never hang".

This note lands in the repo as `docs/plans/2026-09-04-battlecode-2024-design.md` on the branch
`bc24-year-module`. The copy of record for the run is
`runs/2026-09-04-battlecode-2024/design.md`.

**Everything below about the 2024 rules was verified by reading `github.com/battlecode/battlecode24`
at commit `166c79bbf4156c866caf434062cb1f403c01695f`** (`master`, last pushed 2024-02-03) —
`specs/specs.md.html` (spec 3.0.5), `engine/src/main/battlecode/common/GameConstants.java`,
`common/SkillType.java`, `common/TrapType.java`, `common/GlobalUpgrade.java`, `common/Team.java`,
`world/GameWorld.java`, `world/InternalRobot.java`, `world/RobotControllerImpl.java`,
`world/TeamInfo.java`, `world/Flag.java`, `world/Trap.java`, `world/ObjectInfo.java`,
`world/DominationFactor.java`, `world/IDGenerator.java`, `world/LiveMap.java`,
`world/GameMapIO.java`, `schema/battlecode.fbs`, and
`example-bots/src/main/examplefuncsplayer/RobotPlayer.java` — and by **parsing all 78 `.map24`
flatbuffers** in `engine/src/main/battlecode/world/resources/` for their real sizes, seeds,
declared symmetry, wall/water/dam counts, spawn-zone centres and crumb piles. The oracle recipe in
§Tests was **executed in this sandbox, not guessed**: Temurin JDK 8 + the released
`battlecode24-3.0.5.jar` + one driver file runs five full **2000-round** headless games in
**≈ 15 s each**, and the numbers quoted below (peak bytecode use, flag pickups, unspent upgrade
points) are measurements off those runs. Base-repo facts are from a fresh clone of
`Metta-AI/cogame-battlecode` at **`d292243`** ("r1 F12: convictionAtSpawn now does Java's float
product, not a float64 one"), whose shipped coworld version is **0.3.0**
(`runs/2026-09-04-battlecode-2021/STATE.json`, `cow_455dff0d-7f57-4b21-a28d-6603d9c458d0`,
release run 33890103949). Every `file:line` and constant below is to those two trees.

### Source idea (verbatim)

```
# 30 Battlecode 2024 Breadwars (mod of cogame-battlecode) — year variant bc24 + its own league

Duck capture-the-flag: every unit is a DUCK that specialises by levelling attack, heal or build; teams lay traps, dig water, heal each other and race to capture all three enemy flags before round 2000 (tiebreaks otherwise), with global upgrades unlocking every 600 rounds. The cheapest full port of any year: ONE unit type, a hosted spec and jar, and the best bot-licence situation of the whole series (1st, 2nd and 7th all AGPL). Meta evidence is thin (the ranking puts it in 'insufficient evidence') — expect a trap-heavy defence vs flag-rush axis with specialisation splits as the doctrine surface.

Seats: 2 (one cog per side). num_agents = 2 in the bc24 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc24 (v1 candidates; the builder finalises them from the chassis it ports): specialisation_split {attack | heal | build | balanced}, flag_rush_round, trap_budget, trap_placement {choke | flag_ring | spawn_ring}, heal_priority, water_dig_policy, upgrade_order (600/1200/1800), retreat_hp, flag_carry_escort.
Rules, engine, oracle: Spec: https://releases.battlecode.org/specs/battlecode24/3.0.5/specs.md.html (200). Engine: https://github.com/battlecode/battlecode24 (Java 8 + Gradle 7.6, engine/COPYING AGPL-3.0; the build hard-fails on non-JDK-8). Oracle jar: https://releases.battlecode.org/maven/org/battlecode/battlecode24/3.0.5/battlecode24-3.0.5.jar (200; 3.0.6 is saturn-only/403).
Chassis and baselines (behaviour sources): chenyx512/battlecode24 (Gone Sharkin', 1st, AGPL-3.0), jmerle/battlecode-2024 (2nd, AGPL-3.0), andli28/bc2024 (buhg, 7th, AGPL-3.0), davidteather/battlecode_24 (muskellunge, AGPL-3.0).
Ranking: Insufficient evidence in the ranking; chosen for feasibility.
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc24` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc24` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc24`, league_name `Battlecode 2024 — Breadwars`, default_variant_id `bc24`, short_name `bc24` (softmax.com/battlecode/bc24), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin from the idea's HOW paragraph is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; no new repo; one variant per year; one league per year; certification stays bc26; version bump of the same coworld | this paragraph, §Packaging |
| NO Java/JDK/Node in the runtime image; full behaviour port of the 2024 rule set to a deterministic Nim sim (native + wasm); `java.util.Random` reproduced | §Sim module |
| Nim chassis ported from the **behaviour** of the four AGPL-3.0 bot repos; never vendor unlicensed code | §Decisions ("the two chassis"), §Packaging ("Licensing") |
| The year's doctrine sheet knobs | §Decisions ("the bc24 doctrine sheet") |
| Fixed per-robot decision budget instead of bytecode metering (documented divergence) | §Sim module ("the chassis, and the bytecode divergence"), §Packaging (`docs/RULES-BC24.md` §Divergences) |
| The year's maps converted at build time | §Sim module ("Maps") |
| Official 2024 client sprite set for art, credited | §Viewer ("Art"), §Packaging ("Licensing") |
| Java engine ONLY as a CI parity oracle; Tier A/B/C on seeds; **every divergence root-caused or in `docs/PARITY.md` with round+map+cause** | §Tests (`parity-oracle-bc24`), including the **scenario bot** that makes the rare paths bit-exact instead of leaving them to round 900 (the Fleet-card 1218171523823317 lesson) |
| Manifest variant `bc24` (`num_agents` 2) added; certification stays bc26 | §Packaging |
| Phase-50 league `bc24` with its own champions, fillers and credit pool; never touch bc26/bc20/bc21 | §Packaging ("The phase-50 plan") |
| Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side) | §The game, §Viewer |

### Interface facts this note is written against (read from `d292243`, not assumed)

- **D1 — the chassis is not an LLM-selectable knob.** A submitted `chassis` is recorded in
  `sheet_unknown_fields` and ignored (`src/battlecode/sheet.nim` header; `sim_types.nim`).
  **The bc24 sheet has no `chassis` key** and `tests/test_bc24_sheet.nim` asserts the D1 behaviour.
- **D2 — the scripted baseline plays, and CI gates on substance.** bc24's strong baseline
  (`gone-sharkin`) is a real bot; the gate is competence + positive play counters, not a win
  (§Tests items 13, 14 and the `docker-smoke` substance assertion).
- **D3 — the doctrine overlay must be dismissible.** `#bc24-doctrines` ships with a close control,
  an `Escape` binding, a re-open chip and self-dismissal on the first advance; it never sits in the
  transport band (§Viewer).
- **The manifest declares exactly the two players the certification fixture seats.** `player[]` is
  `awu` and `scaffold` and **nothing else** (`coworld_manifest_template.json` at `d292243`);
  `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`
  (`defaultBaselineFor` / `baselineFor`). The bc20 run lost a release dispatch by adding
  year-specific `player[]` entries that occupied no cert slot. **This run adds no `player[]`
  entry** — see the explicit cross-check in §Packaging.
- **`GameVersion` is `GV06`** and `ReplayCompatibleGameVersions` is `["GV04", "GV05", GameVersion]`
  (`src/battlecode/sim_types.nim:16,71`). This run **extends** that list; it does not reset it.
- **`ScriptedChassis`** is the year-neutral chassis enum in `sim_types.nim`
  (`scAwu, scScaffold, scBowlOfChowder, scExamplefuncsplayer, scCaliforniaRoll,
  scExamplefuncsplayer21`); bc24 adds two values, and each year's `newSides` already falls back to
  **that year's strong chassis** for a name belonging to another year.
- **The killfeed/stat-box overlap defect handed forward from bc20 is already FIXED**, at
  `7ce9b19` + `8f0821a`: `relayout()` sets a fourth `:root` variable `--statrail`
  (`client/replay_broadcast.html:4038`), `#killfeed`'s `bottom` is
  `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))` (line 1270),
  `tests/test_viewer.nim:290,297` assert both, and `tools/ci/viewer_smoke.mjs --killfeed-overlap`
  measures client rects at 360/720/1280 px and both zooms. **bc24's job is not to re-fix it but to
  keep it armed**: the `--statrail` measurement set gains `#bc24-crumbs` and `#bc24-levels`, and
  the overlap gate runs on the bc24 replay too (§Viewer, §Tests).
- **`tools/ci/viewer_smoke.mjs`'s scrub-selector fix is already in the repo's copy** (it resolves
  `#scrub` in preference order and excludes `#zoom-slider`; `ci.yml` additionally asserts
  `scrub_selector == "#scrub"`). Nothing to do here except the pacing note in §Viewer.
- **`tools/ci/docker_smoke.sh` already carries `SMOKE_EXPECT_YEAR`, `SMOKE_PLAYER_IDS`,
  `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`, `SMOKE_CONTRACT_PROBE` and `SMOKE_REQUIRE_STATS`**
  (lines 42–57), and `tools/ci/cert_probe.py` (the 2026-09-03 certifier-contract probe) runs inside
  it. bc24 adds a fourth episode and reuses all of them; no script change is needed.
- **The shipped coworld version is 0.3.0.** This run ships **0.4.0**.

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as bc26/bc20/bc21 (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, three generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. No new repo (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=awu\|scaffold` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc24/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc24` bytes anywhere. |
| Real art, starter chrome verbatim | 2024 sprites cut from `battlecode24/client/src/static/img/` into `data/atlas_bc24.*` (credited in `NOTICE`, licence recorded honestly — §Packaging); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc24 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **445 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26].game_config`, `variants[bc20].game_config`, `variants[bc21].game_config` (all unchanged) and `variants[bc24].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc24 policy set is in §Packaging. |

---

## The game

**Battlecode 2024 "Breadwars", played by doctrine, simulated in Nim.** Two cogs each command a
flock of **50 identical ducks** on a symmetric grid between 30×30 and 60×60. Neither cog moves a
duck. At t=0 each writes a **doctrine** — a JSON sheet of ten named knobs — and the deterministic
sim plays the whole match from those two sheets while both cogs watch.

The clock is the **dam**. For the first **200 rounds** an impassable dam splits the map and nobody
can attack: ducks spawn, walk crumbs off the floor, dig water, fill water, lay invisible traps and
— uniquely in this year — **carry their own three flags to wherever they want them**, subject to a
minimum spacing of 6 tiles. At round 200 the dam evaporates, the flag placements are frozen, and
the only thing that ends the game early is **capturing all three enemy flags**. Otherwise round
2000 decides it on flags captured, then total skill levels, then crumbs, then a coin flip.

Every duck is the same duck. What makes them different is what they *do*: attacking, healing and
building each earn experience in that skill, each skill has six levels, and at level 4 a duck gains
**mastery** — that skill can keep climbing to 6 while the other two are frozen at 3. A duck that
dies goes to **jail** for 25 rounds, comes back at full health at a spawn zone, and loses
experience in its own best skill on the way in. So a flock is a portfolio: attackers that hit for
240 instead of 150, healers that mend 100 instead of 80, builders whose 200-crumb explosive trap
costs 100.

Crumbs are the only resource and they are **global per team**: 400 to start, 10 per round for free,
whatever the ducks walk over, and 30 for every kill made while standing on enemy ground. They buy
digging (20), filling (30), stun and water traps (100) and explosive traps (200) — and nothing
else, because ducks are free and infinite. Every crumb spent on a moat is a crumb not spent on an
explosive trap ringing the flag the enemy is running at.

That triangle — **level up, fortify, or run at the flags** — is the whole doctrine game.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. The episode
seed decides which slot takes engine-side **A** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc21/maps.nim`).

### Constants (verbatim from the pinned engine — `common/GameConstants.java`)

Generated into `src/battlecode/years/bc24/constants.nim` by `tools/gen_year_constants.py --year
bc24`, never hand-typed, and re-generated and byte-diffed in CI (§Tests).

| constant | value | constant | value |
|---|---|---|---|
| `GAME_MAX_NUMBER_OF_ROUNDS` | **2000** | `SETUP_ROUNDS` | **200** |
| `ROBOT_CAPACITY` (per team) | **50** | `NUMBER_FLAGS` | **3** |
| `DEFAULT_HEALTH` | **1000** | `JAILED_ROUNDS` | **25** |
| `INITIAL_CRUMBS_AMOUNT` | **400** | `PASSIVE_CRUMBS_INCREASE` | **10**/round/team |
| `KILL_CRUMB_REWARD` | **30** | `GLOBAL_UPGRADE_ROUNDS` | **600** |
| `VISION_RADIUS_SQUARED` | **20** | `ATTACK_RADIUS_SQUARED` | **4** |
| `HEAL_RADIUS_SQUARED` | **4** | `INTERACT_RADIUS_SQUARED` | **2** |
| `COOLDOWN_LIMIT` | **10** | `COOLDOWNS_PER_TURN` | **10** |
| `MOVEMENT_COOLDOWN` | **10** | `FLAG_MOVEMENT_COOLDOWN` | **20** |
| `ATTACK_COOLDOWN` | **20** | `HEAL_COOLDOWN` | **30** |
| `DIG_COST` / `DIG_COOLDOWN` | **20 / 20** | `FILL_COST` / `FILL_COOLDOWN` | **30 / 30** |
| `PICKUP_DROP_COOLDOWN` | **10** | `FLAG_DROPPED_RESET_ROUNDS` | **4** |
| `FLAG_BROADCAST_UPDATE_INTERVAL` | **100** | `FLAG_BROADCAST_NOISE_RADIUS` | **100** |
| `MIN_FLAG_SPACING_SQUARED` | **36** | `SHARED_ARRAY_LENGTH` / `MAX_SHARED_ARRAY_VALUE` | **64 / 65535** |
| `MAP_MIN_*` / `MAP_MAX_*` | **20 / 60** | `BYTECODE_LIMIT` | **25 000** (replaced — see §Sim module) |

`TrapType` (cost, triggerRadius², enterRadius², interactRadius², enterDamage, interactDamage,
doesDig, actionCooldown, invisible, opponentCooldown):

| trap | cost | trigger r² | on enter | on dig/fill/build | build cooldown | visible to enemy |
|---|---|---|---|---|---|---|
| `EXPLOSIVE` | **200** | **0** (its own tile only) | **750** damage, r² ≤ **4** | **200** damage, r² ≤ **2** | 5 | no |
| `WATER` | **100** | **2** | digs every unoccupied land tile in r² ≤ **9** | — | 5 | no |
| `STUN` | **100** | **2** | sets enemy movement **and** action cooldowns to **40**, r² ≤ **13** | — | 5 | no |

`GlobalUpgrade`: `ATTACK` +60 base damage; `HEALING` +50 base heal; `CAPTURING` +21 rounds to the
**opponent's** dropped-flag return delay (4 → 25) **and** −8 to this team's flag-carry movement
cooldown (20 → 12). One point per team at rounds **600, 1200, 1800**; each upgrade at most once.
(`ACTION` is a backwards-compatibility alias of `ATTACK` and is not offered.)

`SkillType` — experience thresholds, and the two *different* rounding regimes:

| level | attack XP | build XP | heal XP | attack: cd / dmg | build: cd / cost | heal: cd / heal |
|---|---|---|---|---|---|---|
| 1 | 15 | 5 | 20 | −5 % / +5 % | −5 % / −10 % | −5 % / +3 % |
| 2 | 30 | 10 | 40 | −7 % / +7 % | −10 % / −15 % | −10 % / +5 % |
| 3 | 45 | 15 | 70 | −10 % / +10 % | −15 % / −20 % | −15 % / +7 % |
| 4 | 75 | 20 | 100 | −20 % / +30 % | −20 % / −30 % | −15 % / +10 % |
| 5 | 110 | 25 | 140 | −35 % / +35 % | −30 % / −40 % | −15 % / +15 % |
| 6 | 150 | 30 | 180 | −60 % / +60 % | −50 % / −50 % | −25 % / +25 % |

Jail penalty, applied to the duck's **best** skill on the way into jail (ties broken
attack → build → heal, exactly `InternalRobot.jailedPenalty`), and skipped entirely if all three
experiences are 0: attack `−1,−2,−2,−5,−5,−10,−12`; build `−1,−2,−2,−3,−3,−4,−6`; heal
`−1,−5,−5,−10,−10,−15,−18`, each clamped at 0.

**The two rounding regimes are load-bearing and are the exact shape of bc21's r1-F12 defect.** Read
them off the engine, not off the spec:

- **Damage and heal are Java `float`.** `InternalRobot.getDamage()` is
  `Math.round(base * ((float) skillEffect / 100 + 1))` and `getHeal()` is the same shape — a
  **float32** product and `Math.round(float)` (= `floor(x + 0.5f)`).
- **Every cooldown and every crumb cost is Java `double`.** `attack`/`heal`/`build`/`dig`/`fill`
  all compute `(int) Math.round(C * (1 + .01 * pct))` where `.01` is a `double` literal — a
  **float64** product and `Math.round(double)`.

The resulting tables (both regimes, all levels, upgrade on and off) are **generated**, committed as
`data/bc24/skills.json`, and byte-diffed against a JDK regeneration in the parity job. For the
reader:

| attack level | damage | damage +ATTACK | attack cd | heal level | heal | heal +HEALING | heal cd |
|---|---|---|---|---|---|---|---|
| 0 | 150 | 210 | 20 | 0 | 80 | 130 | 30 |
| 1 | 158 | 221 | 19 | 1 | 82 | 134 | 29 |
| 2 | 161 | 225 | 19 | 2 | 84 | 137 | 27 |
| 3 | 165 | 231 | 18 | 3 | 86 | 139 | 26 |
| 4 | 195 | 273 | 16 | 4 | 88 | 143 | 26 |
| 5 | 203 | 284 | 13 | 5 | 92 | 150 | 26 |
| 6 | 240 | 336 | 8 | 6 | 100 | 163 | 23 |

Build level scales crumbs and cooldown together: dig costs `20,18,17,16,14,12,10` and an explosive
trap `200,180,170,160,140,120,100`; the trap build cooldown falls `5,5,5,4,4,4,3`.

### The 2024 rule set — exact numbered resolution rules

The sim's own step list. Steps 1–8 are one round; re-ordering any of them is a rules change and
bumps `GameVersion`. It mirrors `GameWorld.runRound` / `processBeginningOfRound` /
`updateDynamicBodies` / `processEndOfRound` exactly.

1. **Flag broadcast re-roll, then the round counter.** *Before* the increment: if
   `currentRound % 100 == 0` — which is true entering rounds **1, 101, 201, …** because
   `currentRound` is still the previous value — every flag in `allFlags` order gets a new
   `broadcastLoc = nearLocs[worldRng.nextInt(nearLocs.len)]`, where `nearLocs` is
   `getAllLocationsWithinRadiusSquared(flag.loc, 100)` in **engine scan order** (`x` ascending
   outer, `y` ascending inner, over the clamped box of side `2·(ceil(√r²)+1)+1`, keeping
   `dx²+dy² ≤ r²`). Then `currentRound += 1`. Then, if `currentRound % 600 == 0`, **both** teams
   gain one global-upgrade point. Then every robot runs `processBeginningOfRound` (clears the
   indicator string and `diedLocation` — a no-op for the port's purposes, kept as a named step
   because the hash chain is taken around it).
2. **Round-1 endowment.** If `currentRound == 1`, each team is credited **400** crumbs. (The engine
   does this *inside* `runRound`, after `processBeginningOfRound`, which is why a duck cannot spend
   it on round 0 and why the trace shows 400 at the top of round 1.)
3. **Turn order.** Iterate the **fixed exec order**: the 100 robots created in the world's
   constructor as `A₀, B₀, A₁, B₁, …, A₄₉, B₄₉`, with ids drawn from `IDGenerator(map.randomSeed)`
   in that order. Ducks are **never destroyed** — death is a *despawn* — so the exec order never
   changes for the whole game, and `eachDynamicBodyByExecOrder`'s skip-if-deleted branch is dead
   code in 2024. **Every robot takes a turn whether spawned or not**: a jailed duck still runs
   step 4 and step 6.
4. **Beginning of turn.** `actionCooldown`, `movementCooldown` and `spawnCooldown` each become
   `max(0, x − 10)`; the robot's `DecisionOps` budget is reset to **2 500** (§Sim module — this
   replaces the Java bytecode limit).
5. **Run the controller.** The robot runs its team's chassis under that team's doctrine, spending
   at most its `DecisionOps` budget. An **action** is legal only while `actionCooldown < 10`; a
   **move** only while `movementCooldown < 10`; a **spawn** only while `spawnCooldown < 10`. The
   legal actions, with their exact preconditions and effects:
   1. **Spawn** (only while not spawned): `spawnCooldown < 10`; the target tile is on the map, is a
      spawn-zone tile **of this team**, is unoccupied and is passable. Effect: place the duck,
      `spawned = true`, `health = 1000`, `roundsAlive = 0`. **Cooldowns are NOT reset** — the
      engine's `spawn()` has those two lines commented out — which is harmless only because 25
      jail turns already decremented them to 0. The port reproduces the engine, not the intent.
   2. **Move** (8 directions): `movementCooldown < 10`; the destination is adjacent, on the map,
      unoccupied and **passable** — `passable = !wall && !water && (!dam || round > 200)`. Effect,
      in this order: (a) the duck moves; a carried flag moves with it; (b) any crumbs on the tile
      are added to the team pool and the pile is cleared; (c) the movement cooldown is charged —
      `+10`, or `+20` while carrying a flag, or `+12` while carrying a flag **if this team owns
      CAPTURING**; (d) every **enemy** trap registered as triggering on this tile is appended to
      the duck's trigger queue, **iterated from the end of the registration list to the front**;
      (e) if the duck carries an **enemy** flag and the destination is a **friendly spawn-zone
      tile**, the flag is **captured**: removed from the game, `flagsCaptured += 1`, and if that
      is the third, the winner is set immediately with `CAPTURE`.
   3. **Attack** (r² ≤ 4): `actionCooldown < 10`; not carrying a flag; **not during setup**
      (rounds ≤ 200); the target tile holds an **enemy** duck. Effect: charge
      `round(20 · (1 + .01·attackCdPct))` (float64) to the action cooldown; then, if the blow would
      reduce the target to ≤ 0 HP **and the attacker is standing on enemy territory**, credit 30
      crumbs; apply the damage (float32 table above); `health = min(health, 1000)`; if
      `health ≤ 0` the target **despawns** (step 5.11); the attacker gains 1 attack XP subject to
      the mastery rule.
   4. **Heal** (r² ≤ 4): `actionCooldown < 10`; not carrying a flag; the target is a **different**
      friendly duck (self-heal is illegal) **below** 1000 HP. Effect: charge
      `round(30 · (1 + .01·healCdPct))`; add the heal amount, capped at 1000; +1 heal XP subject to
      the mastery rule. Healing **is** legal during setup.
   5. **Build a trap** (r² ≤ 2): `actionCooldown < 10`; not carrying a flag; the team has at least
      `round(cost · (1 + .01·buildCostPct))` crumbs; **no enemy duck within r² ≤ 2 of the target**;
      an explosive may sit on land **or water**, stun and water on land only; the tile does not
      already hold a **friendly** trap. Effect, in this order: charge the build cooldown; deduct
      the crumbs; **then** — if the tile holds an **enemy EXPLOSIVE** trap, queue that trap as an
      *interact* trigger and **return without placing anything** (the crumbs and the cooldown are
      spent anyway, and no build XP is earned); otherwise place the trap, register it in
      `trapTriggers` for every tile within its `triggerRadius`, and gain 1 build XP.
   6. **Dig** (r² ≤ 2): `actionCooldown < 10`; not carrying a flag; the target is not already
      water, is not a wall, is **not a spawn-zone tile**, holds no duck, holds no flag, holds no
      **friendly** trap, and the team can pay `round(20 · (1 + .01·buildCostPct))`. Effect: charge
      the dig cooldown, deduct the crumbs, set the tile to water, queue an enemy explosive trap on
      that tile as an *interact* trigger if there is one, and gain 1 build XP.
   7. **Fill** (r² ≤ 2): `actionCooldown < 10`; not carrying a flag; the target **is** water; the
      team can pay `round(30 · (1 + .01·buildCostPct))`. Effect: charge the fill cooldown, deduct
      the crumbs, set the tile to land, queue an enemy explosive trap as an *interact* trigger if
      there is one. **Filling earns no build XP** (patch 1.1.0) — but it is still cheapened and
      hastened by build level.
   8. **Pick up a flag** (r² ≤ 2): `actionCooldown < 10`; the duck carries nothing; the tile holds
      at least one flag; during setup the flag must be **this team's**, after setup it must be the
      **enemy's**; and at least one flag on the tile must satisfy `loc IS startLoc` **or**
      `droppedRounds != 0` — i.e. **an enemy flag cannot be picked up in the same round it was
      dropped**. Effect: take the **first flag on the tile belonging to the pickup-eligible team**
      (tile lists are append-ordered, so this is "oldest dropped first"), charge `+10` action
      cooldown, `flagsPickedUp += 1` **if the setup phase is over**, and — the easy-to-miss case —
      if the flag is an enemy flag **and the duck is already standing in a friendly spawn zone**,
      capture it right there.
   9. **Drop a flag** (r² ≤ 2): `actionCooldown < 10`; the duck carries a flag; the target tile is
      passable. Effect: place the flag on that tile, charge `+10` action cooldown **and** `+10`
      (or 20/12 while carrying — the engine calls the same `addMovementCooldownTurns`, which sees
      `hasFlag()` **false** by then, so it is a flat `+10`) movement cooldown.
   10. **Buy a global upgrade**: the team has ≥ 1 unspent upgrade point and does not already own
       that upgrade. No crumbs, no cooldown, no range. Effect: the upgrade turns on for the whole
       team immediately, one point is spent.
   11. **Read / write the shared array** (free, charged only against `DecisionOps`): 64 slots,
       values `0 … 65 535`, writes take effect **immediately** and are visible to the same team's
       later ducks in the same round. There is no range requirement and **no spawned requirement**
       — a jailed duck may read and write. Sensing (also free against `DecisionOps` only): every
       map feature and every duck within r² ≤ 20 regardless of walls or water; every flag within
       r² ≤ 20 including carried ones; **enemy traps are invisible** and friendly ones are not;
       and, after setup, for each enemy flag that is **not carried and not currently visible**, a
       *broadcast* location within r² ≤ 100 of the truth, re-rolled every 100 rounds (step 1).
6. **End of turn.** Every queued trap fires now, **in queue order**, each removing itself
   afterwards:
   - **STUN**: every enemy duck within r² ≤ 13 of the trap has **both** cooldowns *set* (not
     added) to 40.
   - **EXPLOSIVE**: `750` damage to every enemy duck within r² ≤ 4 if it was triggered by *entry*;
     `200` within r² ≤ 2 if it was triggered by a dig, fill or build. Damage goes through
     `addHealth`, so a duck reduced to ≤ 0 despawns immediately, dropping any flag it carries.
   - **WATER**: every tile within r² ≤ 9 of the trap that holds no duck, is passable, is not a
     spawn zone and holds no trap becomes **water**, in engine scan order.
   Then the trap is de-registered from `trapTriggers` over r² ≤ 2 and removed from its tile. Then
   `roundsAlive += 1` — for jailed ducks too.
   **Despawn** (from any damage source): `spawnCooldown = 250`, the jail penalty is applied to the
   best skill, any carried flag is dropped **on the duck's tile**, the duck leaves the board.
7. **End of round.** In this order:
   1. Both teams are credited **10** crumbs (this happens in `runRound`, *before*
      `processEndOfRound`).
   2. If `currentRound == 200`: **confirm flag placements**, per team independently. If all three
      of that team's flags are pairwise ≥ 6 apart (`dist² ≥ 36`), each flag's **start location
      becomes its current location**; otherwise **all three of that team's flags teleport back to
      their previous start locations**. Either way a carried flag is taken off its carrier first.
   3. If the setup phase is over: for every flag that is **not carried** and whose current location
      **is not (by object identity) its start location**: if `droppedRounds ≥ 4 + (21 if the
      OPPONENT owns CAPTURING else 0)` the flag returns to its start location; else
      `droppedRounds += 1`.
   4. Record the per-team round stats and close the round record.
   5. **End-of-match check**: if `currentRound ≥ 2000` and no winner is set yet, apply the ladder,
      first hit wins — **more flags captured** (`more_flag_captures`) → **higher sum of all skill
      levels over all 50 ducks, jailed included** (`level_sum`) → **more crumbs** (`more_bread`) →
      **coin flip** (`coin_flip`). A `capture` win set during the turn sweep is *not* re-decided
      here.
   6. If a winner is set, the game stops.
8. **Hash chain.** Append this round's state hash (§Sim module).

**Three subtleties the port reproduces literally, each with its own test:**

- **A capture win does not stop the round.** `TeamInfo.captureFlag` sets the winner the instant the
  third flag lands, but `running` is only cleared at step 7.6 — so every duck after the capturer in
  the exec order still takes its turn that round, and their actions are recorded. The port keeps
  that; `tests/test_bc24_endladder.nim` pins it.
- **`flag.getLoc() != flag.getStartLoc()` is a Java *object identity* test**, not a coordinate
  test. It is true exactly when the flag has moved since the last time `moveFlagSetStartLoc` set
  both to the same object. The port therefore carries an explicit `locIsStartRef: bool` — set true
  by the start-location writer, cleared by every pickup, drop and reset — and never compares
  coordinates. A flag dropped *exactly on its own start tile* therefore still runs a return timer
  (and returns to the same tile), and cannot be picked up on the round it was dropped.
- **Stacked flags.** Two carriers jailed on the same tile leave two flags there with independent
  timers; a pickup takes the first eligible one in list order.

**Deliberate non-rules, verified absent from the 2024 engine and therefore absent here:** there is
no unit type other than the duck and no unit cost; there is no resign action a doctrine can reach
(so `RESIGNATION` is unreachable); `DominationFactor.MORE_FLAGS_PICKED` exists but
`checkEndOfMatch` never calls it, so it is a **dead rung** and is not in our enum; there is no
terrain that slows movement (only walls, water and the setup-phase dam block it); walls are never
destroyed and spawn zones can never be dug or covered; and there is no per-team unit cap beyond the
fixed 50.

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc24` variant is **best-of-three on three
distinct maps from the `mixed` pool, played to the engine's own 2000-round cap**.

```
container start, map load, seat connect              ≤  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    ≤  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 2000 rounds                         ≤ 340 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 110)
score + replay write + shutdown grace                ≤  30 s
                                                       -------
worst case                                             445 s   <= 720 s
```

Honest per-round estimate, so the builder can check it. bc24's cost is **flat**, which is what
makes it the cheapest year: exactly **100 robot-turns per round**, always, because the roster is
fixed at 50 per team and jailed ducks still take (cheap) turns. Each turn is capped at 2 500
`DecisionOps`, so the **enforced** worst case is 2.5 × 10⁵ ops/round and 5 × 10⁸ ops for a
2000-round game. The realistic average is far lower — a duck's turn is a ≤ 69-tile vision sweep,
a bounded BFS step and one action, ≈ 250 ops — giving ≈ 2.5 × 10⁴ ops/round and ≈ 5 × 10⁷ per game,
i.e. **2–4 ms/round, 5–8 s per game** in release Nim. For scale, the Java engine plays the same
2000 rounds in **≈ 15 s** (measured in this sandbox on five maps), and it is doing instrumented
bytecode accounting on 100 sandboxed JVM threads. **The estimate is enforced, not trusted:**

- `perGameBudgetSeconds = 110` and `matchBudgetSeconds = 340` are hard monotonic-clock guards. A
  game that blows its guard is abandoned, the finished games are scored, and
  `results.reason = deadline`.
- `tests/test_bc24_perf.nim` plays a full 2000-round game on `DefaultLarge` (59×31, the largest map
  in the variant's pool) with **both seats on `specialisation_split: build`, `trap_budget: 60`,
  `water_dig_policy: moat`** — the configuration that maximises per-turn work — and **fails CI
  above 90 s**.
- If that gate ever goes red the fix is one config value — `gamesPerMatch: 3 → 1` in the `bc24`
  variant — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc24's axis (trap-heavy defence versus flag
  rush) is **map-shaped**: it turns on how far apart the spawn zones are, how much water there is
  to dig, and how narrow the post-dam chokes are, and the `mixed` pool spans all three deliberately
  (§Sim module, Maps). One map would rank the map, not the doctrine.

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

### Scoring, sign, and what the bc24 league ranks by

The 2024 game is win/lose; it has no point formula. This one is defined here, and it is a
continuous reading of the engine's own end ladder so that the score and the winner never tell
different stories:

```
share(x, y)    = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
caps[t]        = flags captured by t                       # the CAPTURE / MORE_FLAG_CAPTURES rung
levels[t]      = sum over t's 50 ducks of (attackLevel + buildLevel + healLevel), jailed included
                                                            # the LEVEL_SUM rung
crumbs[t]      = t's crumb balance at the final round        # the MORE_BREAD rung
points[t]      = int(60.0'f32 * share(caps[t],   caps[o])
                   + 25.0'f32 * share(levels[t], levels[o])
                   + 15.0'f32 * share(crumbs[t], crumbs[o]))   # TRUNCATION, not rounding
```

Four load-bearing details, each pinned by a test vector in `tests/test_bc24_scoring.nim`:

- every share is narrowed through **float32** before the weighted sum, and the sum is **truncated**
  by the `int()` cast. The reason is **recorder/re-deriver agreement**: the same arithmetic runs
  natively on x86-64 and in wasm32 and must produce the same integer;
- the three terms are exactly the engine's three deciding rungs, in the engine's own priority order
  and weighted in that order, so a `capture`, `more_flag_captures`, `level_sum` or `more_bread` win
  always comes with the matching share above 0.5;
- `share` returns **0.5 on a 0–0 total**, which is the deliberate difference from bc21's
  `x / max(1, total)`: in bc24 a great many honest games end 0–0 on captures, and a term that
  silently paid nobody would make two even games score differently for no reason;
- points are in `[0, 100]` and the two seats' points sum to ≤ 100.

Per seat, over the games actually played:

```
results.scores[t] = 100.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** The 100-per-game win bonus dominates the ≤ 100-point spread across three
games, which is what makes "capture the flags or lose" true in the ranking as well as in the rules.
**The `bc24` league ranks by `results.scores`** (Elo over the resulting ordering), exactly as the
bc26, bc20 and bc21 leagues do. A `deadline` episode scores the games that finished; a `fault`
episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` in snake_case, plus our
one wall-clock value:

| `end_reason` | engine origin | meaning |
|---|---|---|
| `capture` | `CAPTURE` | a team captured all **3** enemy flags; the game ends at the end of that round |
| `more_flag_captures` | `MORE_FLAG_CAPTURES` | round 2000 reached; more flags captured |
| `level_sum` | `LEVEL_SUM` | captures tied; higher total of all skill levels over all 50 ducks |
| `more_bread` | `MORE_BREAD` | levels tied; more crumbs banked |
| `coin_flip` | `WON_BY_DUBIOUS_REASONS` | everything tied; a draw from the world RNG |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded |

`coin_flip` and `abandoned` are already in the manifest's `end_reason` enum; `capture`,
`more_flag_captures`, `level_sum` and `more_bread` are added (§Packaging). `MORE_FLAGS_PICKED` and
`RESIGNATION` are **not** added: the first is unreachable in the engine's own `checkEndOfMatch` and
the second has no action that can produce it (`docs/RULES-BC24.md` §Divergences item 5).

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from
bc26/bc20/bc21**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped: a partial replay and `[0, 0]` are still written | `[0, 0]` |

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the
three shipped years). Container exit codes are unchanged: `0` whenever results + replay were
attempted (including `deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep
answering for the ~20 s shutdown grace, the websocket handler keeps its `Ping → Pong` **echo** (it
must return the ping's payload — commit `cb37075`, and `tools/ci/cert_probe.py` proves it) and does
not filter binary frames.

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged from the shipped years: the player container is a thin
registrar and every decision is taken inside the **game** container, because that is the only
container the platform injects the `anthropic_api_key` coworld secret into
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/battlecode/anthropic_api_key`).

**One decision turn, one parallel batch.** Both seats are asked at the same moment and their two
provider calls go out as **ONE parallel batch** (`curly.makeRequests`, `decide.nim`'s existing
shape) with the same deadline; seats are never queried one after another. The batch's wall-clock
budget is `doctrineBudgetMs = 45 000` — attempt 1 `attempt1Ms = 20 000`, the single retry
`retryMs = 12 000` — which is the per-turn budget for this game and sits inside the 720 s envelope
computed in §The game. At most 2 provider calls per seat per episode.

`src/battlecode/llm.nim` is unchanged and year-neutral: the credential ladder (Bedrock sidecar →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the single Bedrock candidate
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, fence-tolerant JSON extraction, the `throttled`
fast-fail, rune-boundary truncation, `maxOutputTokens = 1200`. With no credentials the client
disables itself at construction and every seat falls back instantly, which is what lets offline
certification and `docker-smoke` finish in seconds.

### The bc24 doctrine sheet — ten knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc24 chassis. Unknown key, wrong
type or out-of-range value → **that field's default**, recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by
answering badly — only by answering weakly.

**The LEARNINGS pin, stated as a rule the builder must hold every knob against: no setting of any
knob may produce an inert or self-starving flock.** The strategy surface lives *inside one
competent chassis*. Concretely, and independently of every knob: the chassis always spawns every
duck it can, always walks crumbs off the floor, always keeps ≥ 3 builders and ≥ 18 attackers in the
census, always defends a flag that is sensed under threat (with a stun trap out of a reserved
100-crumb floor even at `trap_budget: 0`), always answers a sensed enemy in its own territory, and
always commits to an enemy flag by `flag_rush_round`, whose range **cannot express "never"**. Every
knob moves *how much of what, when* — never *whether it plays*. `tests/test_bc24_knobs.nim` proves
each knob has teeth and `tests/test_bc24_survival.nim` proves the floor holds (§Tests 14, 15).

| field | type / values | default | what it changes (`src/battlecode/years/bc24/chassis/…`) |
|---|---|---|---|
| `specialisation_split` | `attack` \| `heal` \| `build` \| `balanced` | `balanced` | `roles.nim census()` — how the 50 duck sequence-slots are cut into builders / healers / attackers. `balanced` **6 / 16 / 28** (Gone Sharkin' shipped 3 / 20 / 27); `attack` **4 / 10 / 36**; `heal` **5 / 24 / 21**; `build` **10 / 14 / 26**. Every value keeps ≥ 3 builders, ≥ 10 healers and ≥ 18 attackers: no split can produce a flock that cannot dig, cannot mend or cannot fight. Sequence slots are assigned from the exec order, never from an RNG. |
| `flag_rush_round` | int **201 … 1200** | 450 | `attack.nim commitRound()` — the round the three attack roles stop contesting the middle and commit to the best-known enemy flag. Below it they still farm crumbs, kill in enemy territory (30 crumbs a head) and level attack; they never sit still. The range cannot express "never", and 1200 still leaves 800 rounds of raiding. |
| `trap_budget` | int **0 … 60** (percent) | 30 | `builder.nim spendPlan()` — the share of crumb *income* the builders may put into traps; the remainder funds dig/fill. **Independent of this knob** the chassis reserves 100 crumbs after round 200 and spends them on a stun trap the moment an own flag is sensed under threat (D2). At 60 the builders will bank crumbs to afford explosives. |
| `trap_placement` | `choke` \| `flag_ring` \| `spawn_ring` | `flag_ring` | `builder.nim trapTargets()` — `choke`: the narrowest passable cuts on the shortest path from each enemy spawn zone to each own flag, measured once at round 200 by the BFS width test. `flag_ring`: the ring at Chebyshev 2 around each own flag, filled clockwise from the enemy-facing side. `spawn_ring`: the eight tiles bordering each own spawn zone, so a raider that gets a flag cannot walk it out. |
| `trap_mix` | `stun` \| `explosive` \| `mixed` | `mixed` | `builder.nim trapKind()` — `stun` (100 crumbs, freezes a raid for 4 turns), `explosive` (200, 750 damage inside r² ≤ 4), `mixed` = alternate stun / explosive per placement slot, water traps only where `water_dig_policy` asks for them. |
| `heal_priority` | `wounded_first` \| `attackers_first` \| `carrier_first` | `wounded_first` | `micro.nim healTarget()` — `wounded_first`: lowest HP in r² ≤ 4. `attackers_first`: lowest-HP duck with an attack level ≥ 3, else lowest HP. `carrier_first`: any friendly flag carrier in range first, then lowest HP. |
| `water_dig_policy` | `none` \| `choke_dig` \| `moat` \| `fill_paths` | `choke_dig` | `builder.nim terraform()` — `none`: no dig/fill spend at all (builders still build traps and still level BUILD off them, so `none` is not an inert setting). `choke_dig`: dig water across the two narrowest approaches to each own flag. `moat`: dig the Chebyshev-2 ring around each own flag, leaving one gap per flag so friendly ducks can still stand on it. `fill_paths`: spend on **filling** the water on the shortest route to each enemy flag, which is how a raid crosses `Waterworld`-class terrain. |
| `upgrade_order` | array of 3 distinct strings over `attack` \| `heal` \| `capture` | `["attack","heal","capture"]` | `upgrades.nim` — spent at rounds 600 / 1200 / 1800 by the first duck of the team to act that round. A malformed, short, long or duplicated array takes the default **whole**, recorded once. |
| `retreat_hp` | int **100 … 900** | 400 | `micro.nim shouldBreak()` — the HP at which a duck breaks contact toward the nearest friendly healer, else toward its nearest spawn zone. At 900 it retreats early and is mended; at 100 it trades to the last hit. It never stops fighting: a duck that cannot retreat (cornered, or stunned) attacks. |
| `flag_carry_escort` | int **0 … 6** | 2 | `attack.nim escort()` — how many friendly ducks within r² ≤ 20 of a friendly carrier convert to escorts (screening the carrier and attacking anything that closes) for as long as the carry lasts. 0 means the carrier runs alone and everyone else keeps raiding. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — trap-heavy defence against flag rush —
so the league's headline matchup is the one this year is actually about.

- **champion #1, `battlecode-bc24-fortress` (daveey)**: *"You command a flock of 50 ducks in
  Battlecode 2024. Three of your flags; three of theirs; 2000 rounds. Your doctrine: they never get
  one out. Set specialisation_split to \"build\" or \"balanced\", trap_budget high (45-60) and
  trap_placement \"flag_ring\" or \"spawn_ring\" so a raider who reaches a flag still has to walk
  it home through explosives — an explosive trap does 750 damage inside a radius of 2 tiles and a
  duck has 1000 HP. Use water_dig_policy \"moat\" or \"choke_dig\": water is impassable and only a
  30-crumb fill undoes it. Set trap_mix \"mixed\" or \"explosive\", heal_priority \"wounded_first\"
  and retreat_hp high (600-800) so your ducks live to level up — healing feeds heal levels and
  attack feeds attack levels, and levels are the second tiebreak at round 2000. Set
  flag_rush_round late (700-1100) and flag_carry_escort 3-5 for the one raid you do make. Put
  \"capture\" late in upgrade_order and \"attack\" or \"heal\" first. In notes, say which of your
  three flags is the weak one and what you have done about it."*
- **champion #2, `battlecode-bc24-flagrush` (daveey-1)**: *"You command a flock of 50 ducks in
  Battlecode 2024. Capturing all three enemy flags ends the game instantly — nothing else does.
  Your doctrine: get there first. Set specialisation_split \"attack\", flag_rush_round early
  (220-350) so you arrive before their traps are paid for, trap_budget low (0-15) and
  water_dig_policy \"fill_paths\" so your crumbs open the road instead of closing yours. Set
  trap_placement \"choke\" for what little you build, heal_priority \"carrier_first\" and
  flag_carry_escort 4-6: a carried flag drops where its carrier dies and returns to their base 4
  rounds later, so the escort is the difference between a capture and a gift. retreat_hp low
  (150-350) — you are trading. Put \"capture\" first in upgrade_order: it cuts your flag-carry
  movement cooldown from 20 to 12 and stretches THEIR dropped-flag return from 4 rounds to 25. In
  notes, say which enemy flag you go for first and what you do if the first raid fails."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with
every default and range, the constant tables (damage/heal by level, trap costs and radii, crumb
economy), the map cards for all three games, the scoring formula, the alias pair, a **HOW A GAME
ENDS** section (the bc21 r1-F8 fix, kept), and the reply contract ("reply with ONE JSON object;
your reply must begin with `{`"). The assistant turn is prefilled with `{` and the prefix
re-attached before parsing (the procgen 0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`). It gains a `bc24`
arm with two published names. **The manifest still declares only `awu` and `scaffold`** — the two
ids the certification fixture seats — and `PLAYER_SCRIPTED` resolves per year, exactly as bc20 and
bc21 do:

| `PLAYER_SCRIPTED` | on `year: "bc24"` resolves to |
|---|---|
| `awu`, `gone-sharkin`, or anything unrecognised | **`gone-sharkin`** — the strong published doctrine and the champion chassis |
| `scaffold`, `examplefuncsplayer`, `examplefuncsplayer24`, `example` | **`examplefuncsplayer24`** — the deliberately weak floor and the oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field
(D1). `defaultBaselineFor("bc24")` is `gone-sharkin`, so a seat that says nothing useful plays the
strong doctrine, not the weak floor.

**`gone-sharkin` — the strong baseline and the champion chassis.** Behaviour ported from
`chenyx512/battlecode24` `src/bot1/` (AGPL-3.0, commit `bf245ef`; the 1st-place bot, whose README
names `bot1` as the main bot), with the navigator and shared-array discipline from
`jmerle/battlecode-2024` `src/camel_case_v21_final/` (AGPL-3.0, commit `d10ddcc`), the BFS and
comms layout from `andli28/bc2024` `src/mainbot/` (AGPL-3.0, commit `4040df7`) and the
carrier-return micro from `davidteather/battlecode_24` `src/submit6/` (AGPL-3.0, commit `d129abf`)
— all parameterised by the ten knobs. Its scripted reply is the all-defaults sheet. Algorithm:

- **Sequence and roles** (`roles.nim`): every duck derives a stable **sequence id 0…49** from its
  position in its team's exec order (deterministic, no RNG, no comms round-trip — the bot1 trick
  of a per-id lookup string, done properly). The census from `specialisation_split` cuts the
  sequence into builders (lowest ids), healers, then attackers. Six **roles** exist on top of the
  census, as in bot1: roles 0–2 defend own flags 0–2, roles 3–5 raid enemy flags 0–2; a duck claims
  the least-crowded role it is eligible for, capped at 15 claims per role, and re-claims when it
  respawns.
- **Setup, rounds 1…200** (`setup.nim`): three ducks spawn first and each carries one own flag to
  the placement `trap_placement` asks for, subject to the ≥ 6 spacing rule — **checked before the
  flag is dropped**, because a team that fails the check at round 200 has all three flags teleported
  home. Six more ducks walk spawn-zone-to-spawn-zone to prove the routes and write them to the
  shared array. The builders dig or fill per `water_dig_policy` and lay the first traps per
  `trap_budget`; digging in own territory on a checkerboard parity is also how a builder reaches
  build level 4 before the dam falls (5, 10, 15, 20 XP — cheap, and it halves every later cost).
  No attacks are possible; healing is.
- **Defence** (`defend.nim`): a defender holds the ring at Chebyshev 2–3 around its flag, kills
  anything that enters, and writes a distress bit when it sees more enemies than friends. It cannot
  pick its own flag up after setup, so "defence" is: kill the carrier, then keep the tile clear for
  the 4 rounds the flag needs to fly home. On distress, the nearest two raiders turn back.
- **Raiding** (`attack.nim`): before `flag_rush_round`, attackers contest the middle: they take
  crumb piles, they kill in enemy territory for the 30-crumb bounty, and they avoid unexplored
  tiles adjacent to enemy-held ground (an invisible trap is a 750-damage tile). After it, they path
  to the best-known enemy flag — a sensed location beats a broadcast one, and a broadcast one is
  re-read every round because it is re-rolled every 100 — pick it up, and run home to the nearest
  friendly spawn tile with `flag_carry_escort` ducks screening. A carrier cannot attack, heal,
  build, dig or fill; it moves and it drops.
- **Micro** (`micro.nim`): target the lowest-HP enemy in r² ≤ 4, breaking ties toward the highest
  attack level (kill the veteran); heal per `heal_priority`; break contact at `retreat_hp`; drop a
  stun trap on your own tile when three or more enemies close and the crumbs are there; never step
  onto a tile a friendly water trap would flood.
- **Building** (`builder.nim`): the spend plan splits crumb income by `trap_budget`, keeps the
  100-crumb defensive reserve, and never spends below the reserve before round 300 (the CI
  competence gate is what pins that number).
- **Upgrades** (`upgrades.nim`): at 600/1200/1800 the first acting duck buys the next entry of
  `upgrade_order`.
- **Comms** (`comms.nim`): the 64-slot shared array, one 16-bit word per slot:
  `0–2` own flag i as `[x:6][y:6][state:4]` (`state` = carried / at start / dropped / lost),
  `3–5` enemy flag i last-known as `[x:6][y:6][age:4]`, `6–8` own-flag distress counters,
  `9` the upgrade ledger, `10–12` spawn-zone congestion, `13–15` rally points,
  `16–47` a coarse 8×8 enemy-sighting grid with saturating counts, `48–63` role claims.
  **The word format is shared by both teams** — deliberately, because it makes the endcard able to
  decode both sides' traffic, and because the array is per-team anyway (there is no cross-team
  read in 2024).
- **Pathing** (`pathing.nim`): a bounded BFS over the sensed window plus the remembered map, with
  water and walls impassable and the dam impassable only while `round ≤ 200`, falling back to a
  greedy step with a 6-tile no-repeat history to break oscillation. Charged against `DecisionOps`.

**`examplefuncsplayer24` — the weak floor and the parity oracle's other side.** Ported
**statement-for-statement** from `battlecode24/example-bots/src/main/examplefuncsplayer/RobotPlayer.java`:
spawn at a random ally spawn location; pick up whatever flag is under you; if you hold a flag and
the setup phase is over, step toward `spawnLocs[0]`; otherwise pick a random direction and move, or
attack the tile ahead if you cannot; and, with probability `rng.nextInt() % 37 == 1`, build an
explosive trap on the tile behind you. **It needs no determinism patch** — unlike 2021's, this bot
seeds its own `java.util.Random(6147)` and never calls `Math.random()` — so the oracle's Java side
is upstream's file **byte for byte**. It may not gain behaviour: it is one side of the differential
oracle. Its scripted reply is the all-defaults sheet (it reads no knob).

Both replies go through the **same** `validate` the LLM path uses, which is what makes the
bounded-orders test meaningful and an LLM doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `gone-sharkin` chassis, `results.fallbacks[seat] = 1`, a `doctrine_fallback` event names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default; the rest of the sheet applies |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| a side takes 2 games | the episode settles immediately — no padding |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `gone-sharkin` baseline reply:

```json
{"sheet":{"specialisation_split":"balanced","flag_rush_round":450,"trap_budget":30,
          "trap_placement":"flag_ring","trap_mix":"mixed","heal_priority":"wounded_first",
          "water_dig_policy":"choke_dig","upgrade_order":["attack","heal","capture"],
          "retreat_hp":400,"flag_carry_escort":2},
 "notes":"default gone-sharkin doctrine","motto":"Bread first, blood after."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively
into `/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc24/constants.nim` | **new, generated** | every `GameConstants` value plus the `SkillType`, `TrapType` and `GlobalUpgrade` tables, emitted by `tools/gen_year_constants.py --year bc24` from the pinned battlecode24 checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc24/world.nim` | **new** | world state: walls, water, dam, spawn zones, team territory, crumb piles, traps and their trigger index, flags, the 100-duck roster and the fixed exec order, and every action of rule 5 |
| `src/battlecode/years/bc24/rules.nim` | **new** | the round loop (rules 1–8), the end ladder, the points formula |
| `src/battlecode/years/bc24/skills.nim` | **new** | XP, levels, the mastery rule, the jail penalty, and the two rounding regimes (float32 for damage/heal, float64 for cooldowns and costs) |
| `src/battlecode/years/bc24/traps.nim` | **new** | placement, the trigger index over `triggerRadius`, the enter/interact split, the water trap's dig set, de-registration |
| `src/battlecode/years/bc24/flags.nim` | **new** | pickup/drop/capture/return, `locIsStartRef`, the setup-phase confirmation, the broadcast re-roll |
| `src/battlecode/years/bc24/maps.nim` | **new** | the converted bc24 pool, the loader, spawn-zone-centre re-derivation, the per-episode draw (`drawMaps`, `sideAslotFor`) |
| `src/battlecode/years/bc24/knobs.nim` | **new** | the ten-knob `Doctrine24` type, defaults, per-field repair, `toJson`, `plainWords` |
| `src/battlecode/years/bc24/chassis/*.nim` | **new** | `sharkin.nim`, `scaffold24.nim`, `roles.nim`, `setup.nim`, `attack.nim`, `defend.nim`, `micro.nim`, `builder.nim`, `upgrades.nim`, `comms.nim`, `pathing.nim`, `kit.nim` |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc24", title: "Battlecode 2024 — Breadwars", maxRounds: 2000, pools: @["small","mixed","large"], atlas: "atlas_bc24")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc24`; `Session` gains a `yBc24` branch (`w24`, `sides24`, `chassis24`); `yearIdOf`/`strongChassisFor`/`parseScriptedChassis`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson24`. `Bc24ActionNames = ["spawn","move","attack","heal","build","dig","fill","pickup","drop","upgrade"]` is added beside `Bc20UnitNames`/`Bc21UnitNames` so `first_action.kind` has a documented vocabulary (the r1-F14 lesson) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV07`, `ReplayCompatibleGameVersions` → `["GV04","GV05","GV06", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scGoneSharkin = "gone-sharkin"` and `scExamplefuncsplayer24 = "examplefuncsplayer24"` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc24` arm in `defaultBaselineFor` and `baselineFor`; `blGoneSharkin` and `blExamplefuncsplayer24` added to `Baseline`; `baselineChassis` maps them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc24`, `doctrine24` on `Sheet`, a `knownKeysFor` arm, a `defaultSheet` field — exactly the four-line shape bc21 added |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc24 adds the land/water/wall/dam terrain, the crumb piles, the duck sprite by dominant skill, the jail rail, trap glyphs for own traps, the flag sprites and the carry trail |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc24 scorebug / feed / endcard shell records |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port (`nextInt()`, `nextInt(bound)`, `nextDouble`) and `IdGenerator` already carry everything bc24 needs |
| `data/maps/bc24/*.json` | **new, committed** | 22 converted maps |
| `data/bc24/skills.json` | **new, committed** | the whole finite skill table: damage and heal per level with and without the upgrade, and cooldown and crumb cost per level for attack, heal, build-trap, dig and fill |
| `data/atlas_bc24.png` / `.json` | **new, committed** | the 2024 sprite atlas |
| `tools/convert_maps_bc24.py` | **new** | reads `.map24` and writes `data/maps/bc24/<name>.json` |
| `tools/map_pools_bc24.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc24.py` | **new** | cuts `atlas_bc24.*` from the 2024 client sprites |
| `tools/gen_year_constants.py` | **`--year bc24` added** | reads the 2024 `GameConstants.java`, `SkillType.java`, `TrapType.java`, `GlobalUpgrade.java` |
| `tools/JavaBc24Tables.java` | **new, CI-only** | regenerates `data/bc24/skills.json` under the CI JDK 8 straight out of the released jar's own classes |
| `tools/oracle/bc24/Bc24Trace.java` | **new, CI-only** | the trace driver (§Tests) — one file, compiled against the released jar |
| `tools/oracle/bc24/Bc24Scenario.java` | **new, CI-only** | the scenario bot that makes the rare paths bit-exact (§Tests) |
| `tools/oracle/bc24/jar.lock` | **new, CI-only** | the oracle jar's URL and sha256 |
| `tools/parity_trace_bc24.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc24.py` | **new** | the tier comparison and the ledger check (the bc21 script, one year on) |
| `tools/ci/parity_ledger_bc24.json` | **new** | the accepted-divergence ledger |
| `tools/gen_bc24_fixture_replay.nim` + `tests/fixtures/replay-bc24.json` | **new, committed** | the fixture replay the wasm smoke loads |

### Determinism

- **`rng.nim` is reused unchanged.** bc24 needs `java.util.Random` in exactly three places, all
  already covered by the existing port: `IdGenerator(map.randomSeed)` (48-bit LCG, `nextInt(bound)`
  with both the power-of-two shortcut and the rejection loop, 4096-id blocks from 10 000,
  Fisher–Yates per block) — which fixes the 100 duck ids for a given map; the **world RNG**
  `Random(map.randomSeed)`, used only for the flag-broadcast re-roll and (in our port) the coin
  flip; and the oracle bot's `Random(6147)` stream, which `scaffold24.nim` reproduces call for
  call.
- **The world RNG is seeded from the map's own `randomSeed` field**, exactly as the engine does.
  The episode seed selects maps and side assignment, never the world RNG.
- **`setWinnerArbitrary`'s `Math.random()`** is replaced by a draw from the world RNG (a documented
  divergence; reachable only when captures, level sums and crumbs are all tied at round 2000).
- **Exec order is structural, not sampled.** The 100 ducks are created `A,B,A,B,…` in the world
  constructor and never removed, so the port's exec order is a fixed array. The three
  `objectInfo.eachRobot` hash-order sweeps the engine performs (`processBeginningOfRound`'s clear,
  the end-of-round record, `TeamInfo.getLevelSum`) are all order-independent — the first is
  per-robot idempotent, the second is recording, the third is an integer sum — and the port sweeps
  in ascending id. This reasoning goes into `docs/RULES-BC24.md` §Divergences item 3.
- **Spawn-zone centres are re-derived the engine's way, not the map file's.** `LiveMap.getSpawnZoneCenters`
  scans tile indices ascending and calls a tile a centre when the tiles at `i−w−1` and `i+w+1` are
  the same team's spawn zone, interleaving A into even slots and B into odd ones. The flags are then
  created in ascending tile-index order with `flag.id = tile index`. The converter records the raw
  `spawnLocations` table for provenance, and `maps.nim` **re-derives** the centres exactly as above,
  because the order decides flag ids and therefore the broadcast re-roll order.
- **The scan order is load-bearing and is ported literally**: `getAllLocationsWithinRadiusSquared`
  is `x` ascending outer, `y` ascending inner, over `[max(cx − ceil(√r²) − 1, 0) … min(cx + ceil(√r²) + 1, w − 1)]`
  and the same in `y`, keeping tiles with `dx² + dy² ≤ r²`. It fixes which tiles a water trap
  floods first and which location the broadcast re-roll picks.
- **All health, crumb and XP arithmetic is integer.** The only float arithmetic in the round loop is
  the skill scaling, and it is **exactly reproduced in the engine's two regimes**: `float32` product
  + `Math.round(float)` for damage and heal, `float64` product + `Math.round(double)` for every
  cooldown and every crumb cost. `Math.round` is `floor(x + 0.5)` in the matching width. There are
  **no transcendentals anywhere in bc24** — no `exp`, no `sqrt` in the round loop — which is why
  this year needs no `fdlibm` path at all and why its arithmetic tier is provable over its whole
  finite domain (§Tests, Tier B).
- Every round appends to a **hash chain**; the viewer re-derives each round and compares, exposing
  `bc_mismatch_round`. The values folded into the bc24 chain each round: per team — crumbs, flags
  captured, flags picked up, the three level sums, ducks spawned, ducks jailed, traps standing,
  water tiles owned; plus globally — the round number, the sum of all duck HP, the number of flags
  not at their start location, and the highest live action-cooldown value.
- Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
  (`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
  scar — and the record→re-derive test covers **every** bc24 end reason, not just `complete`.
- **`GameVersion` bumps to `GV07`** in the same commit, with a prepend-only changelog line ("bc24
  year module added; bc26, bc20 and bc21 semantics unchanged").
  **`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06", GV07]`** — it is *extended*,
  never reset: nothing a GV04/GV05/GV06 recording carries changed meaning, so every hosted replay
  keeps rendering. `tools/ci/check_gameversion.sh` is kept and claims the version across branches.

### The chassis, and the bytecode divergence

The engine's per-robot **bytecode limit** (25 000 for every unit, `GameConstants.BYTECODE_LIMIT`)
has no meaning outside the JVM instrumenter. It is replaced by a **fixed per-robot `DecisionOps`
budget of 2 500** — one tenth of the Java limit, the same convention bc20 and bc21 use. One credit
is charged for each: tile sensed, duck examined in a sense sweep, flag examined, BFS node expanded,
direction evaluated, shared-array slot read or written, and trap-placement candidate scored.
Credits are deducted inside `pathing.nim` / `kit.nim` and **enforced by the sim, not by the bot**.
When the budget reaches zero the duck's turn ends where it stands — it is **not** resumed
mid-computation next turn, which is the one place this differs from the JVM.

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to
Java bytecode granularity needs either a Nim-level instrumenter (a compiler project) or a
hand-annotation of every statement against `MethodCosts.txt`, and neither buys anything the budget
does not — the chassis are ours and are written to fit the budget.

**And in bc24, unlike bc21, this divergence is provably not exercised by the oracle.** The bc21 run
lost its long parity window because `examplefuncsplayer21` blew its whole 20 000-bytecode budget on
an uncaught exception's stack trace and the JVM paused it mid-turn. The 2024 example bot does not:
measured in this sandbox over **five full 2000-round games** (`DefaultSmall`, `Yinyang`,
`BreadPudding`, `Rivers`, `Tunnels`), the **peak bytecode use of any duck on any round was 3 % of
the 25 000 limit** and there was **no mid-turn cut-off at all**. So the Tier A bit-exact window for
bc24 is the **whole game**, and the parity job asserts that rather than assuming it: if any traced
duck ever exceeds **50 %** of the limit the job fails loudly, because past that point the
comparison stops being defined (§Tests).

### Maps

**22 of the 78 official maps** are converted and committed. Sizes, declared symmetry, seeds,
wall/water/dam counts, spawn-zone centres and crumb totals below were read out of the real `.map24`
flatbuffers (schema `GameMap`: `name`, `size`, `symmetry` `0=rotation|1=horizontal|2=vertical`,
`randomSeed`, `walls[]`, `water[]`, `divider[]` (the dam), `spawnLocations` (a `VecTable`
alternating A,B,A,B,A,B), `resourcePiles` + `resourcePileAmounts`), not assumed. Every one of the
78 parsed cleanly with the reader `tools/convert_maps_bc24.py` implements.

| pool | map | size | seed | symmetry | dam | water | walls | crumb piles / total |
|---|---|---|---|---|---|---|---|---|
| `small` | `DefaultSmall` | 31×31 | 664 | rotation | 133 | 22 | 36 | 34 / 8 200 |
| `small` | `Yinyang` | 31×31 | 21 | rotation | 133 | 154 | 24 | 48 / 6 400 |
| `small` | `BreadPudding` | 30×30 | 938 | vertical | 98 | 110 | 108 | 54 / 5 800 |
| `small` | `Rivers` | 30×30 | 363 | rotation | 66 | 124 | 60 | 24 / 4 200 |
| `small` | `Tunnels` | 30×30 | 890 | vertical | 16 | 138 | 124 | 40 / 6 600 |
| `small` | `Occulus` | 30×30 | 155 | rotation | 78 | 110 | 100 | 62 / 11 400 |
| `mixed` | `DefaultSmall`, `Yinyang` (as above), plus: | | | | | | | |
| `mixed` | `GaltonBoard` | 31×30 | 817 | vertical | 60 | 84 | 40 | 216 / 37 800 |
| `mixed` | `StackGame` | 31×30 | 31 | vertical | 76 | 104 | 112 | 92 / 9 200 |
| `mixed` | `Alligator` | 40×31 | 675 | rotation | 40 | 138 | 168 | 42 / 12 600 |
| `mixed` | `Randy` | 41×31 | 392 | vertical | 64 | 290 | 136 | 95 / 17 000 |
| `mixed` | `Anchor` | 41×32 | 294 | vertical | 201 | 60 | 84 | 67 / 20 100 |
| `mixed` | `DefaultMedium` | 45×31 | 482 | rotation | 46 | 249 | 54 | 31 / 7 900 |
| `mixed` | `Gauntlet` | 45×30 | 36 | vertical | 198 | 212 | 104 | 46 / 5 600 |
| `mixed` | `HungerGames` | 50×30 | 418 | horizontal | 112 | 124 | 80 | 94 / 22 200 |
| `mixed` | `Soccer` | 53×30 | 810 | vertical | 60 | 124 | 182 | 22 / 6 200 |
| `mixed` | `DefaultLarge` | 59×31 | 187 | vertical | 70 | 196 | 34 | 53 / 9 100 |
| `large` (reserved) | `Bunkers` | 40×40 | 228 | rotation | 44 | 132 | 110 | 22 / 5 600 |
| `large` | `Fountain` | 40×40 | 41 | horizontal | 86 | 358 | 170 | 34 / 5 400 |
| `large` | `CH3353C4K3F4CT0RY` | 45×45 | 7 | vertical | 121 | 56 | 101 | 264 / 26 400 |
| `large` | `Islands` | 49×49 | 349 | rotation | 97 | 396 | 86 | 104 / 11 600 |
| `large` | `Battlecode24` | 59×59 | 884 | horizontal | 118 | 446 | 640 | 243 / 42 500 |
| `large` | `DefaultHuge` | 59×59 | 0 | rotation | 111 | 90 | 140 | 36 / 7 400 |

`mixed` (12 maps) is the `bc24` variant's pool; `small` (6) is the pool the parity oracle and the
docker smoke run on; `large` (6) is reserved for a later variant. The `mixed` pool is chosen to
span the axis the doctrines argue about: all three symmetries; 900 to 1 829 tiles; crumb economies
from 5 600 (`Gauntlet`, where `trap_budget: 60` genuinely starves the terraforming) to 37 800
(`GaltonBoard`, where it does not); dam sizes from 40 to 201 tiles, i.e. from "one wide front" to
"three chokes"; and water from 60 to 290 tiles, which is what decides whether `fill_paths` is a
doctrine or a waste.

Maps are excluded from v1 for stated reasons, all recorded in `docs/RULES-BC24.md`: everything
above 2 700 tiles is out of the played pools for wall-clock reasons (they are converted only where
listed under `large`); `QuestionableChess` and `Racetrack` have **zero crumb piles**, so the whole
build/terraform half of the game runs on 10 crumbs a round and the knob surface collapses; and the
remaining 52 are simply not converted in v1 — the converter handles any `.map24`.

`tools/convert_maps_bc24.py` writes `data/maps/bc24/<name>.json` carrying: `name`, `width`,
`height`, `random_seed`, `symmetry` (the map's own declared value), `walls`, `water`, `dam` (three
`width × height` bit arrays), `crumbs` (a sparse `[x, y, amount]` list, with the engine's own
"amount < 100 means tenths, multiply by 10" back-compat rule applied at conversion time and
recorded), and `spawn_centers` (the six centres, in the engine's re-derived order). The converted
maps are **committed** and CI re-converts and diffs. The wasm bundle gets the same directory through
the existing `--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps
from the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which
slot takes side A in game 1; sides alternate each game. Seed, map names and side assignment are
recorded in results and in the replay.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `sheet_common`, `sheet`,
`decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never branches on
the year except through `years/dispatch.nim`, whose `Session` is a Nim object **variant** so the
compiler refuses to build a half-added year. Adding 2024 is exactly what bc20 and bc21 proved
adding a year to be: a new `years/bc24/` directory, a converted map set, a sprite atlas, one
registry line, one arm per dispatch `case`, and one manifest variant. The replay header records
`year` so a viewer can never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol
id would force every existing bc26/bc20/bc21 consumer to re-register for no change in the contract.
Both `game.protocols.player` and `game.protocols.global` continue to point at `docs/PROTOCOL.md`,
which gains a bc24 section.

### The player container (thin registrar) — unchanged

`/bin/battlecode-player` reads `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`),
dials its seat with a bounded retry (240 × 500 ms), sends **one** registration blob and then only
receives until the socket closes, then exits 0:

```json
{"type":"register","prompt":"<PLAYER_PROMPT or empty>",
 "scripted":"awu"|"scaffold"|null,
 "policy":"<PLAYER_POLICY_LABEL>"}
```

sent as a Sprite v1 chat blob (a **binary** frame — the server must not filter non-text frames) and
re-sent a bounded number of times until acknowledged. The seat token is a **credential** and a
wrong one is refused (commit `d581704`; `tools/ci/cert_probe.py` proves it against the real image).
A seat that sets neither env var takes the active year's default baseline (`gone-sharkin` on bc24).
A seat whose registration never arrives is logged loudly and reported to
`COGAME_PLAYER_FAILURE_URI`. The receive loop is wrapped in `try/except CatchableError` and exits 0
on a dead socket (the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no
per-round observation of any kind.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV07","year":"bc24",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":871345,
 "games":[{"map":"HungerGames","width":50,"height":30,"symmetry":"horizontal",
           "you_are":"A","rounds":2000,"setup_rounds":200,
           "your_spawn_centers":[[6,23],[43,23],[24,26]],
           "enemy_spawn_centers":[[6,6],[43,6],[24,3]],
           "min_spawn_separation":18.2,
           "terrain":{"walls":80,"water":124,"dam":112,"passable_pct":86.4},
           "crumbs":{"piles":94,"total":22200,"nearest_pile_to_you":3}},
          {"map":"Randy","…":"…","you_are":"B"},
          {"map":"DefaultSmall","…":"…","you_are":"A"}],
 "economy":{"start_crumbs":400,"passive_per_round":10,"kill_reward_in_enemy_territory":30,
            "dig_cost":20,"fill_cost":30,
            "trap_costs":{"explosive":200,"stun":100,"water":100},
            "trap_effects":{"explosive":"750 dmg r2<=4 on entry, 200 dmg r2<=2 on dig/fill/build",
                            "stun":"enemy cooldowns set to 40, r2<=13",
                            "water":"floods every free land tile r2<=9"},
            "flag_return_rounds":4,"flag_return_rounds_with_enemy_capture_upgrade":25},
 "units":{"per_team":50,"hp":1000,"vision_r2":20,"attack_r2":4,"heal_r2":4,"interact_r2":2,
          "jail_rounds":25,
          "damage_by_attack_level":[150,158,161,165,195,203,240],
          "heal_by_heal_level":[80,82,84,86,88,92,100],
          "xp_to_level":{"attack":[15,30,45,75,110,150],"build":[5,10,15,20,25,30],
                         "heal":[20,40,70,100,140,180]},
          "mastery":"at level 4 in one skill the other two freeze at level 3"},
 "upgrades":{"rounds":[600,1200,1800],
             "attack":"+60 base damage","heal":"+50 base heal",
             "capture":"their dropped flags take 25 rounds to fly home instead of 4; your flag-carry movement cooldown 20 -> 12"},
 "rules_digest":"<~6 KB condensed spec: the setup phase and the dam, flag placement and the 6-tile rule, spawning and jail, the two cooldown counters, move/attack/heal/build/dig/fill/pickup/drop, the three traps and how they trigger, specialisation and mastery, the shared array, the flag broadcast, and the end ladder>",
 "sheet_schema":{"…all ten knobs, their values, ranges and defaults…"},
 "scoring":{"weights":{"flag_share":60,"level_share":25,"crumb_share":15},
            "win_bonus_per_game":100,"games":3,
            "note":"shares are float32; points truncate to an integer"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with the seat's **own**
spawn-zone centres and the enemy's (they are public: the engine's own map guarantees put them
there, and both are symmetric images of each other), terrain and crumb aggregates, the seed, the
full constant tables, the knob surface with defaults, the scoring weights, the deadlines. Because
every map is symmetric, the two seats' cards are mirror images and numerically identical in every
aggregate; the only asymmetry is `you_are` and which mirrored coordinate set is labelled "yours".
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent,
in either direction, at any time); the opponent's real player name (only the alias); every in-match
state (a cog receives **no** per-round observation — one sealed doctrine, then the war); the other
seat's fallback status. Inside a match the fog is the ducks': vision r² ≤ 20, enemy traps invisible,
enemy flags only sensed or broadcast-approximated.

### Reply schema and caps

```json
{"sheet":{"specialisation_split":"attack","flag_rush_round":260,"trap_budget":10,
          "trap_placement":"choke","trap_mix":"stun","heal_priority":"carrier_first",
          "water_dig_policy":"fill_paths","upgrade_order":["capture","attack","heal"],
          "retreat_hp":250,"flag_carry_escort":5},
 "notes":"Their south flag is 9 tiles from the dam; take it before round 300 and escort it home.",
 "motto":"Quack once, run twice."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES**, cut on a rune boundary | unparseable → retry once → fallback sheet |
| `sheet` | ≤ **32** keys, each value type- and range-checked | bad field → that field's default, recorded |
| `upgrade_order` | exactly **3** distinct strings from the enum | any malformation → the whole default array, recorded once |
| `notes` | **280 runes** | truncated |
| `motto` | **48 runes** | truncated |
| unknown sheet keys recorded | ≤ **16** keys, each ≤ **40 runes** | truncated |
| provider error text stored in the replay | **200 runes** | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary**
(`truncateRunes`/`truncateBytes` in `sim_types.nim`; the reply's 16 KB cap is measured in bytes but
still cut on a rune boundary — commit `a8684c0`): byte-slicing a multi-byte character renders fine
in a browser and then fails a strict UTF-8 parser, which is exactly what makes a replay unreadable
to everything but one lenient viewer.

### Results document

The closed schema is **shared with the three shipped years** and stays that way:
`results.games[]`'s five required keys are year-neutral (`map`, `side`, `rounds_played`, `winner`,
`end_reason`), every year-specific statistic is an optional property, and `end_reason`'s enum is
the union of every year's values.

bc24's per-game keys, each a 2-array of integers in **seat** order unless marked scalar:
`flags_captured`, `flags_picked_up`, `flags_dropped`, `flags_returned`, `rounds_carrying`,
`crumbs_end`, `crumbs_collected`, `crumbs_spent`, `kill_crumbs`, `ducks_spawned`, `ducks_jailed`,
`alive_end`, `attacks`, `damage_dealt`, `kills`, `heals`, `heal_dealt`, `traps_built`,
`traps_triggered`, `trap_damage`, `tiles_dug`, `tiles_filled`, `levels_end`, `attack_levels_end`,
`build_levels_end`, `heal_levels_end`, `masteries`, `upgrades_taken` (a 3-bit mask),
`upgrade_first_round`; scalars `setup_flag_teleports` (0–2: how many teams failed the 6-tile
spacing rule at round 200) and `rounds_with_any_carry`.

Top level, unchanged: `names`, `aliases`, `scores`, `wins`, `points`, `games`, `seed`, `year`,
`policy_kind`, `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`,
`wall_clock_seconds`, `game_version`.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV07","year":"bc24",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"gone-sharkin",
           "sheet":{…as applied…},"sheet_submitted":"{…as received…}",
           "sheet_defaults_applied":["trap_budget"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":8123,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"HungerGames","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":2000,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…],"side_a_slots":[…],"abandon_after":[…],"max_rounds":2000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with
a sha256 of the committed converted map the bundle also ships), both doctrine sheets, the chassis
each seat drove, and the event list are all in the file, and the wasm sim replays every round from
them. **No `.bc24` bytes, no per-round state dump, no per-duck dump, no trap dump** — traps, water,
crumbs, levels and flag positions are pure functions of the sim, so the browser re-derives them and
the endcard reads the re-derived totals. No server is contacted except S3 for the `.replay` file.
The per-round hash chain lets the viewer prove its re-derivation matches the recording
(`bc_mismatch_round`, surfaced as `data-replay-mismatch-round` and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`. **Every event kind here is
bounded per game** — a 2000-round match with 100 ducks cannot be allowed to emit an event per
attack — and every one has CSS (§Viewer).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides` | 1/game | `game` | beat + feed |
| `setup_end` | `game`, `round` (=200), per clan `flags` (three `[x,y]`), `traps`, `dug`, `filled`, `teleported` (bool) | 1/game | `setup` | beat + feed ("The dam falls. Clan Ash has 7 traps down and its flags 9 tiles apart") |
| `first_action` | `game`, `round`, `alias`, `kind` (from `Bc24ActionNames`) | 4/game | `build` | beat + feed |
| `flag_taken` | `game`, `round`, `alias`, `flag`, `x`, `y`, `escort` | ≤ 24/game | `steal` | beat + feed |
| `flag_dropped` | `game`, `round`, `alias`, `flag`, `x`, `y`, `cause` (`killed`\|`dropped`) | ≤ 24/game | `return` | beat + feed |
| `flag_returned` | `game`, `round`, `alias`, `flag` | ≤ 24/game | `return` | beat + feed |
| `flag_captured` | `game`, `round`, `alias`, `flag`, `total` | ≤ 6/game | `capture` | **chapter marker** + feed |
| `trap_wave` | `game`, `round`, `alias`, `triggered_total`, `damage_total` | emitted when a clan's triggered-trap count crosses a multiple of 10; ≤ 20/game | `trap` | beat + feed |
| `upgrade` | `game`, `round`, `alias`, `upgrade` (`attack`\|`heal`\|`capture`) | ≤ 6/game | `upgrade` | beat + feed |
| `mastery` | `game`, `round`, `alias`, `skill`, `level` (4, 5 or 6), `ducks` | first time a clan reaches each of 4/5/6 in each skill: ≤ 9/game | `level` | beat + feed |
| `rout` | `game`, `round`, `alias`, `jailed` | a round in which a clan lost ≥ 5 ducks; ≤ 20/game | `rout` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points`, `flags` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

The whole event list for a three-game match is at most a few hundred entries, and
`tests/test_bc24_replay.nim` asserts each per-kind bound so a pathological game cannot produce a
20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc24/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.bc24` bytes, no 2024 TypeScript
client.

### All four viewer files come from ONE starter: `cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` → `cogame-battlecode` → here.
All four bundle files come from **that one starter** — never a mixture, because splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23).

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc24/`, `data/bc24/skills.json` and `data/atlas_bc24.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. The only edit is that `static_replay.js` also writes `document.documentElement.dataset.year = 'bc24'` when the header says so — the same one-line switch bc20 and bc21 added. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc24 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and no existing id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and byte-for-byte: **`client/chrome_common.js`** and **`client/broadcast_core.js`**
(their sha256 is asserted against the coworld-ctf copies in `tests/test_viewer.nim`, and that
assertion stays green because neither file is touched). `wire_constants.js` is regenerated from the
sim by `tools/gen_wire_constants.nim`, as today.

**Load signalling** (unchanged from the starter, restated because it is a checklist item):
`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on the
**first drawn frame** (the worker's `loaded` message after the first board frame is composited —
never on rAF timing at the call site, the chorus 2026-08-24 scar), and the `coworld-replay` bridge
posts `ready` from a callback fired **after** that attribute is set. On any failure — fetch, JSON
parse, an unknown `game_version`, a wasm abort, or a hash mismatch that prevents rendering — it sets
**`data-replay-error="<message>"`** on `<html>` and shows the failure card.

### The appended bc24 game block

**No starter element is removed.** The bc26 block's elements (`#coopchip`, `#bars`, `#gamechips`,
`#econ`, `#doctrines`), the bc20 block's (`#bc20-flood`, `#bc20-soup`, `#bc20-units`,
`#bc20-doctrines`, `#bc20-chain`) and the bc21 block's (`#bc21-votes`, `#bc21-influence`,
`#bc21-units`, `#bc21-doctrines`, `#bc21-bids`) all stay exactly where they are; the bc24 block adds
its own, with ids that are all new and all prefixed:

- `#bc24-flags` — the headline readout, in the same top-centre pill slot bc20 uses for its flood
  gauge and bc21 for its election: `ASH ●●○ — ○○○ BASIL`, three pips per clan (captured / carried /
  home, the carried one pulsing), and `2 to win`. It flashes when a flag changes hands.
- `#bc24-crumbs` — per clan: crumbs banked, income per round, traps standing, water tiles owned.
- `#bc24-levels` — per clan: the three level sums as `⚔ 41 ✚ 22 ⛏ 9`, ducks alive `47 / 50`, ducks
  in jail, and the upgrades owned as lit glyphs.
- `#bc24-doctrines` — both sheets in plain words, **dismissible** (D3): a `#bc24-doctrines-close`
  button with `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first
  playback advance (or after six seconds for a viewer who never presses play), and a
  `#bc24-doctrines-toggle` chip in the scorebug that re-opens it. Its body is capped and scrolls. It
  sits above the board area and **never** inside the transport band.
- `#bc24-traps` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: `static_replay.js` sets
`document.documentElement.dataset.year` from the replay header, and the stylesheet extends the
existing `html[data-year="bc21"] #bc20-… { display: none }` /
`html:not([data-year="bc21"]) #bc21-… { display: none }` pattern with the bc24 pair. Every bc24
beat-marker CSS rule is **scoped to `html[data-year="bc24"]`** (the bc21 r1-F4 fix, kept).

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The bc20 judge's advisory defect — `#killfeed` overdrawing the bottom-right year stat boxes at FIT
zoom, because the feed is anchored in board-scaled `--u` units and the boxes in pixels off the
transport band — **was fixed in the bc21 version bump** and is in the tree at `d292243`:
`relayout()` measures the union of the *visible* year stat boxes into `--statrail`
(`client/replay_broadcast.html:4038`), `#killfeed`'s `bottom` is
`max(calc(76 * var(--u)), calc(var(--band, 0px) + var(--statrail, 0px) + 8px))` (line 1270),
`tests/test_viewer.nim:290,297` assert both statically, and `viewer_smoke.mjs --killfeed-overlap`
measures client rects at 360 / 720 / 1280 px at FIT and 2× zoom on every year's replay.

**What bc24 must do — and it is the whole of the work here:**

1. add `#bc24-crumbs` and `#bc24-levels` to `relayout()`'s measured set, beside `#econ`,
   `#bc20-soup`, `#bc20-units`, `#bc21-influence` and `#bc21-units`, so the rail measures the boxes
   that are actually visible on a bc24 replay;
2. run the existing `--killfeed-overlap` gate **on the bc24 replay too**, at all three widths and
   both zooms — four replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and
   asserts the gate goes red, so a fourth year cannot quietly disarm it (the 2026-09-04 learning
   about `page.evaluate` IIFEs and gates that look armed and test nothing).

### Zoom: KEEP `#viewpanel`

The bc24 variant's pool tops out at 59×31 and the reserved large pool at 59×59. The native board
render is 16 px per tile, so 496–944 px wide — **larger than the 360 px featured-match frame**, where
a 59-wide board would give 6.1 px per tile. So the inherited `#viewpanel` (zoom bar + minimap, with
`?viewpanel=0` still honoured for thumbnail capture) is **kept**, wired to the same
`zoomAt/setZoom/panBy/panTo/resetView` core API the worker already forwards. The default view is
fit-to-board, so a spectator who touches nothing sees the whole map, both flocks and all six flags.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets
  **`--hudscale`**, **`--topband`**, **`--band`** and **`--statrail`** on `:root`, iterating to a
  fixed point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport). `#bc24-doctrines`, `#bc24-crumbs`, `#bc24-levels` and
  `#bc24-traps` are all explicitly positioned above `var(--band)`.
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`
  ("FLAG CAPTURED — Clan Ash, game 2, round 1 412"), built by a bc24-block function with its **own**
  name, `buildBc24BeatButtons` — never `markBeat` (the tandem 2026-08-23 hoisting collision) and
  never colliding with `buildBeatButtons` (bc26), `buildBc20BeatButtons` or `buildBc21BeatButtons`.
  CSS exists for **every kind emitted**: `.beat-marker.doctrine`, `.game`, `.setup`, `.build`,
  `.steal`, `.return`, `.capture`, `.trap`, `.upgrade`, `.level`, `.rout`, `.end` — `steal`,
  `return` and `capture` already exist in the shared chrome (lines 1717–1732) and are reused
  unchanged; `setup`, `trap`, `upgrade`, `level` and `rout` are new and scoped to
  `html[data-year="bc24"]`.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
  `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`,
  `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — check 8 must be dispatched with `settle=20000 soak=15`

bc21 taught this: a compute-heavy year defeats a fixed-wait scrub probe, because the Worker
re-simulates from the last keyframe on every seek and a 700 ms settle expires first (loaded:true,
viewer healthy, instrument too impatient). bc24's sim is **2000 rounds × 100 duck-turns**, i.e. in
the same class as bc21's 3.12 ms/round and probably above it. So, decided here rather than
discovered at phase 60: **the phase-60 check-8 dispatch for bc24 uses `settle=20000 soak=15`**, and
`ci.yml`'s `wasm-viewer` job runs `viewer_smoke.mjs` with `--timeout 120 --soak 15` on the bc24
replay (the other three keep `--timeout 90 --soak 10`). The docker-smoke step prints
`sim_seconds / rounds`, and `docs/RULES-BC24.md` records the measured value so the next year module
can size its own probe from a number instead of a guess.

### Art

`data/atlas_bc24.png` + `data/atlas_bc24.json` (≈ 150 KB, committed), cut by
`tools/build_sprite_atlas_bc24.py` from the official 2024 client's sprite tree
(`battlecode24/client/src/static/img/` at the pinned commit). The whole set is 51 PNGs and every one
that matters is used: `robots/{brown,white}/{base,attack,build,heal,jailed}.png` (and their
`_64x64` variants), `traps/{brown,white}/{explosive,stun,water}.png`, and
`resources/{bread,bread_outline,crumb_1,crumb_2,crumb_3}.png`. **Palette follows the client's own
two team colours: brown = side A, white = side B**, and because sides alternate each game the
scorebug plate keeps the *alias* constant and recolours its swatch per game. Licence is recorded
honestly in `NOTICE` (§Packaging): the client declares **GPL-3.0** in `client/package.json` and
carries no `LICENSE` file of its own, unlike the engine (`engine/COPYING`, AGPL-3.0).

Board rendering (`render.nim`): land, water, wall and the setup-phase dam are drawn in the repo's
own paintbot-derived tile palette (the 2024 client draws terrain procedurally, so there is nothing
to reuse and nothing to credit); water drawn as water, the dam as a visibly temporary barricade that
**dissolves at round 200** — that dissolve is the single most legible moment in the year and it gets
its own beat. Crumb piles use the `crumb_*` sprites sized by amount; a duck is drawn with the sprite
of its **dominant skill** (`base` until it has a level, then `attack`/`heal`/`build`), tinted by
health, with a small level pip; a jailed duck is drawn greyed in the **jail rail** beside the
scorebug with a countdown, because 25 rounds of absence is a story and an empty tile is not.
**Own traps are drawn, enemy traps are not** — the fog belongs to the ducks and drawing a hidden
explosive would make every trap wave unsurprising; when a trap fires, its glyph flashes at its
radius for two frames and *then* the spectator learns it was there. Flags are drawn at their tile,
carried flags ride their carrier with a two-tile trail, and a flag away from home draws its return
countdown.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else, and the `#bc24-*` boxes dropping
their word labels to glyphs under 640 px).

- `#scorebug`: both clan plates — `CLAN ASH` over the real player name (`daveey`) and the motto —
  the live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 1412 / 2000`, `game 2 of 3 — HungerGames`, and
  during the first 200 rounds `SETUP — 63 rounds to the dam`.
- `#bc24-flags`, `#bc24-crumbs`, `#bc24-levels` as above.
- `#board`: terrain, the dam and its dissolve, crumb piles, all 100 ducks by dominant skill and
  health, own traps, all six flags with carry trails and return countdowns, and the jail rail.
- `#bc24-doctrines`: each sheet in plain words ("all-in on attack", "rushes the flags at round 260",
  "spends a tenth of its crumbs on traps, at the chokes", "fills a path through the water", "takes
  the capture upgrade first", "trades at 250 HP", "sends five escorts with a carrier"), plus the
  capped `notes` and a fallback badge when a seat's doctrine came from the fallback sheet.
  Dismissible.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and
  provably clear of the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words ("Clan Basil took all
  three flags at round 1 412" / "2 000 rounds — Clan Ash captured 2 flags to 1" / "flags level at
  1–1 — Clan Ash finished 63 skill levels ahead"); the per-game score line; and `#bc24-traps`, the
  **war panel**: per clan, flags picked up / dropped / returned / captured, traps built and
  triggered and the damage they did, tiles dug and filled, crumbs earned and spent (split
  dig/fill/traps), the three level sums with masteries, which upgrades were bought and on what
  round, and ducks jailed. Nothing about traps or levels is stored in the replay: the wasm sim
  re-derives every round.

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`,
  `player` → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar). One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and
  `/bin/battlecode-player` from one image and copies `data/` (now carrying `maps/bc24/`,
  `bc24/skills.json` and `atlas_bc24.*`). **No JDK, no JRE, no Java, no node in any runtime stage** —
  the 2024 engine's toolchain exists only in the `parity-oracle-bc24` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc24 game block
  along with the other three.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc24` is 2024 'Breadwars' — 50 identical
    ducks a side, three flags each, an impassable dam for 200 rounds, and traps you cannot see until
    they go off."*
  - `tags` unchanged (already ≥ 3).
  - `game.config_schema`: `year.enum` becomes `["bc26","bc20","bc21","bc24"]`. `pool.enum`
    unchanged (`small` / `mixed` / `large`; each year owns its own pool table). `maxRounds` keeps
    `minimum 50, maximum 2000` — **bc24's 2000 is exactly the existing ceiling, so no schema change
    is needed**. `gamesPerMatch` keeps `maximum 3`; `perGameBudgetSeconds` keeps `maximum 300`
    (bc24 uses 110) and `matchBudgetSeconds` `maximum 600` (bc24 uses 340). `tokens` stays
    **declared and required** (the runner injects it — the 2026-09-03 lesson); every array keeps
    `minItems`/`maxItems`; no runner-managed `tokens` **values** inside any `game_config`.
  - `game.results_schema`: bc24's optional properties added beside the other years';
    `games.items.required` unchanged (the five year-neutral keys); `end_reason`'s enum extended with
    `capture`, `more_flag_captures`, `level_sum`, `more_bread` (`coin_flip` and `abandoned` are
    already there).
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":".../blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one
    entry and keeps the five it has: `rules.md`, `rules-bc20.md`, `rules-bc21.md`,
    **`rules-bc24.md`** (Battlecode 2024 "Breadwars": rules, knobs and divergences →
    `docs/RULES-BC24.md`), `replay.md`, `parity.md` (→ `docs/PARITY.md`, which gains a bc24
    section).
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc24
    resolution ("…, Gone Sharkin' on bc24" / "…, examplefuncsplayer24 on bc24").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The
  certifier's `players-run` step requires **every** declared `player[]` entry to occupy a slot in
  `certification.players`, and the certifier also requires
  `len(certification.players) == certification.game_config.num_agents`. With `num_agents = 2` there
  are exactly **two** cert slots, they are filled by `awu` and `scaffold`, and therefore
  **`player[]` may contain exactly those two ids and nothing else**. Adding
  `battlecode-bc24-gone-sharkin` or any other year-specific runnable to `player[]` would fail the
  release with `players_missing`. It is also unnecessary: `PLAYER_SCRIPTED` resolves **per year** in
  `src/battlecode/baselines.nim`, so seating `awu` on a bc24 episode already plays Gone Sharkin' and
  seating `scaffold` already plays examplefuncsplayer24. The scripted bc24 policies reach the league
  through `tools/ci/policies.json`, which is a *policy* list and has nothing to do with `player[]`.
  `tests/test_manifest.nim` asserts all three facts (`player[]` ids == `certification.players` ids;
  `len(certification.players) == certification.game_config.num_agents`; `num_agents` present in
  every variant's `game_config` and absent at variant top level), so the contradiction cannot be
  re-introduced silently.

  **Variants — one per Battlecode year:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | unchanged | **2** |
  | `bc21` | Battlecode 2021 — Campaign (2 seats) | unchanged | **2** |
  | `bc24` | Battlecode 2024 — Breadwars (2 seats) | `year: "bc24"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 2000`, `num_agents: 2`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 110`, `matchBudgetSeconds: 340`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `bc24`'s variant description: *"Best of three on the mixed pool. Fifty identical ducks a side and
  three flags each. A dam splits the map for 200 rounds while both flocks dig, fill, hide traps and
  choose where their flags will stand; then it falls, and the only way to end the game early is to
  carry all three enemy flags home. Ducks level up by attacking, healing or building — 2 000 rounds
  decide it."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false`).

  **Certification fixture — UNCHANGED, and stays on bc26.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, `"num_agents": 2` and its existing fast settings. There is **no bc24
  certification fixture in v1** (§Out of scope): certification is the platform's contract check, it
  already passes on bc26, and re-pointing it at a brand-new year module would put the release at the
  mercy of the newest code for no gain. bc24 is proven instead by its own `docker-smoke` episode
  (§Tests), which produces a real bc24 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  **`0.3.0 → 0.4.0`** — because it adds a variant and adds optional results properties without
  changing any existing behaviour. `GameVersion` goes `GV06 → GV07` and
  `ReplayCompatibleGameVersions` is **extended** to `["GV04","GV05","GV06","GV07"]`, so every hosted
  bc26/bc20/bc21 replay keeps rendering (the bc20 learning about `GameVersion` handling: extend,
  never reset, and claim the version across branches with `tools/ci/check_gameversion.sh`). The
  release is dispatched through the existing `coworld-release.yml` with the same step order
  (build → certify → upload-policies → upload-coworld → secret put). **Certify runs against bc26,
  exactly as before**, and `release-result.json` must still show `canonical: true` and
  `certify.replay_liveness` containing `skipped (static replay bundle declared`.

- **`tools/ci/policies.json`** gains the bc24 set beside the bc26, bc20 and bc21 sets (a scripted
  champion is a failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-bc24-fortress","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"fortress"}},
   {"name":"battlecode-bc24-flagrush","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"flagrush"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-gone-sharkin","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"gone-sharkin","PLAYER_POLICY_LABEL":"gone-sharkin"}},
   {"name":"battlecode-examplefuncsplayer24","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer24","PLAYER_POLICY_LABEL":"examplefuncsplayer24"}}]
  ```
  `<IMAGE>` is the **player** service's image (the 2026-09-03 lesson). Champion #2 is uploaded while
  `daveey-1` is the active player. LLM credentials reach the **game** container through the manifest
  env; the player pods need no Bedrock sidecar in this lineage.

  **Release dispatch shape, decided:** dispatch `coworld-release.yml` with a `policies` **override**
  limited to the four bc24 entries (the bc20 pattern), so the release does not recut vN+1 of the
  bc26/bc20/bc21 policies the three existing leagues have seated. If the override is ever dropped
  and the full file is used instead, phase 50 must take its labels from **this** release's
  `release-result.json` and never from remembered ones (the bc21 learning). Either shape works;
  this run picks the override.

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **fourth league**, created beside the bc26, bc20 and bc21 ones and touching none of them and not
the game's default league:

| field | value |
|---|---|
| `league_key` | `bc24` |
| `league_name` | `Battlecode 2024 — Breadwars` |
| `default_variant_id` | `bc24` |
| `short_name` | `bc24` → `softmax.com/battlecode/bc24` (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc24-fortress` (owned by **daveey**), `battlecode-bc24-flagrush` (owned by **daveey-1**) — deliberately the year's two poles, trap-heavy defence against a flag rush |
| fillers (scripted) | `battlecode-gone-sharkin`, `battlecode-examplefuncsplayer24` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues`
filtered on `game.coworld_name` now returns **four** rows; select by `league_key`/name or you will
configure a sibling year's league. Fillers are set **before** the first `trigger-round`. The atlas
slug is `battlecode/bc24`.

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged
by the repository itself. `NOTICE` gains five sections, and one of them is a correction of an
assumption the bc21 note could make and this one cannot:

- **`battlecode/battlecode24` engine — AGPL-3.0** (verified: `engine/COPYING` is the GNU AGPL v3;
  `schema/LICENSE` is too; **the repository root carries no LICENSE**). Pinned commit
  `166c79bbf4156c866caf434062cb1f403c01695f`. The derived files are named individually:
  `src/battlecode/years/bc24/**` (behaviour, hand-ported), `years/bc24/constants.nim` (generated
  from `GameConstants.java` + `SkillType.java` + `TrapType.java` + `GlobalUpgrade.java`),
  `data/maps/bc24/*.json` (converted from `.map24`), `data/bc24/skills.json` (generated from the
  engine's own arithmetic), and `years/bc24/chassis/scaffold24.nim` (examplefuncsplayer, ported
  statement for statement — it is the parity oracle's other side and may not gain behaviour).
  **The engine itself is used only at CI time**; no JDK, no JRE and no upstream Java source or
  bytecode exists in any image this repository builds.
- **`battlecode/battlecode24` client sprites — GPL-3.0.** `client/package.json` declares
  `"license": "GPL-3.0"` and the client directory has **no LICENSE file of its own** (this differs
  from battlecode21, whose `client/LICENSE` was the AGPL — do not copy the bc21 note's wording).
  `data/atlas_bc24.*` is cut from `client/src/static/img/**` and is credited as GPL-3.0 in `NOTICE`,
  naming the 51 source PNGs by directory. GPLv3 §13 and AGPLv3 §13 expressly permit the combination
  of GPL-3.0 and AGPL-3.0 works, which is exactly what this repository is; the repository as a whole
  remains AGPL-3.0 and `NOTICE` records the sprite files' own terms. `schema/package.json` also says
  `GPL-3.0` while `schema/LICENSE` is the AGPL — the discrepancy is recorded and is moot here,
  because **no schema code is used at all** (there is no flatbuffers reader on either side of this
  port).
- **`chenyx512/battlecode24` — AGPL-3.0**, commit `bf245ef`. What derives from it:
  `years/bc24/chassis/{sharkin,roles,setup,attack,defend,micro,builder,comms}.nim` — the sequence-id
  and role-claim scheme, the 3/20/27 census that `specialisation_split: balanced` generalises, the
  setup-phase flag carriers and route setters, the stun-trap-on-a-threatened-flag rule, the
  checkerboard builder dig, and the flag-distress protocol. **Behaviour, not code**, rewritten in
  Nim and parameterised by this coworld's doctrine sheet.
- **`jmerle/battlecode-2024` — AGPL-3.0**, commit `d10ddcc`, `src/camel_case_v21_final/`. What
  derives from it: the navigator structure and the shared-array packing discipline in
  `pathing.nim` / `comms.nim`.
- **`andli28/bc2024` — AGPL-3.0**, commit `4040df7`, `src/mainbot/`, and
  **`davidteather/battlecode_24` — AGPL-3.0**, commit `d129abf`, `src/submit6/`. What derives from
  them: the BFS memory layout, and the carrier-return and retreat micro in `micro.nim` /
  `attack.nim`.
- **XSquare / IvanGeffner repositories carry no licence** and are **not vendored, not ported, not
  compiled and not read into any file here**, in this year as in the others.

`docs/RULES-BC24.md` carries the full **§Divergences** list: (1) no bytecode instrumentation — a
fixed 2 500-`DecisionOps` budget with no mid-turn resumption, together with the measurement that
makes it harmless here (the oracle bot peaks at 3 % of the Java limit and never cuts off) and the
CI assertion that fails the job at 50 %; (2) `setWinnerArbitrary`'s `Math.random()` replaced by a
world-RNG draw; (3) the three `eachRobot` hash-order sweeps replaced by ascending-id sweeps, with
the order-independence argument; (4) Java object-identity flag comparisons reproduced by an explicit
`locIsStartRef` boolean rather than coordinate equality; (5) `MORE_FLAGS_PICKED` and `RESIGNATION`
are unreachable dead rungs and are absent from our `end_reason` enum; (6) the `deadline` wall-clock
stop, a coworld concept and not an engine one, recorded as one load-bearing record; (7) no indicator
strings, dots or lines, no profiler, no crossplay, no `.bc24` output; (8) the spec's "30×30 to
60×60" versus `GameConstants.MAP_MIN_* = 20` (the shipped set's smallest is 30×30; the converter
accepts ≥ 20); (9) the released 3.0.5 jar versus the master sources, which differ only in the
`SPEC_VERSION` string — every gameplay constant is identical, and CI proves it; (10) 22 of the 78
official maps converted, with the reasons for the exclusions; (11) both chassis are behaviour ports
parameterised by the doctrine sheet.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, `<SEATS>` = **2**). The sandbox runs none of it; CI is the harness.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc24_cooldown.nim`** — the two counters: both decrement by 10 at the start of every
   turn and floor at 0, for jailed ducks as well as spawned ones; an action needs `< 10` on the
   action counter and a move `< 10` on the movement counter; the flag-carry move charges 20, or 12
   with CAPTURING, and dropping charges `+10` action **and** `+10` movement (the engine's
   `addMovementCooldownTurns` sees `hasFlag()` false by then); a stun trap **sets** both counters to
   40 rather than adding; `spawn()` does **not** reset either counter.
2. **`tests/test_bc24_spawn.nim`** — spawning needs an unoccupied, passable, own spawn-zone tile and
   `spawnCooldown < 10`; despawn sets `spawnCooldown = 250` and jail lasts **exactly 25 turns**;
   respawn restores 1000 HP and `roundsAlive = 0`; the roster is exactly 50 per team and ids come
   from `IdGenerator(map.randomSeed)` in `A,B,A,B,…` creation order; the exec order never changes.
3. **`tests/test_bc24_combat.nim`** — damage is `Math.round(float32)` at every attack level with and
   without the ATTACK upgrade (the seven-value table above, asserted exactly); attacking is illegal
   during setup, while carrying a flag, and against a friendly or empty tile; the 30-crumb kill
   bounty is paid only when the **attacker** stands on enemy territory and only when the blow kills;
   healing is legal in setup, illegal on self, illegal at full health, capped at 1000, and rounds
   the same way; the heal amount table with and without HEALING.
4. **`tests/test_bc24_levels.nim`** — XP thresholds for all three skills; `getLevel` boundaries;
   the **mastery rule** exactly as `incrementSkill` writes it (a skill stops gaining once its XP
   reaches its level-3 threshold **and** another skill has reached level 4); **filling earns no
   build XP** while digging and trap-building do; the jail penalty hits the highest level with the
   attack → build → heal tiebreak, clamps at 0, and is skipped when all three XPs are 0; every
   cooldown and cost is `Math.round(float64)` and every damage/heal is `Math.round(float32)` — the
   test asserts both regimes on values where they disagree.
5. **`tests/test_bc24_traps.nim`** — build legality (crumbs at the build-level price, no enemy duck
   within r² ≤ 2, explosive on land or water, stun/water on land, no friendly trap already there,
   not while carrying); an **enemy explosive** under a build/dig/fill triggers as an *interact* and
   the build is cancelled while the crumbs and cooldown are still spent; trigger registration covers
   `triggerRadius` (0 for explosive, 2 for stun and water); triggers fire at the **end of the
   triggering duck's turn** in queue order; enter versus interact radius and damage (750/r²≤4 vs
   200/r²≤2); stun's r² ≤ 13 and cooldown 40; the water trap's flood set in engine scan order,
   skipping occupied, impassable, spawn-zone and trapped tiles; de-registration over r² ≤ 2; enemy
   traps are invisible to sensing and friendly ones are not.
6. **`tests/test_bc24_flags.nim`** — setup carry of own flags only; after setup, enemy flags only;
   the same-round-drop refusal; `locIsStartRef` semantics including a flag dropped on its own start
   tile; the return timer at 4 rounds, and at 25 when the **opponent** owns CAPTURING; the round-200
   confirmation, both branches (all three ≥ 6 apart → placements stick; otherwise all three
   teleport); stacked flags with independent timers and oldest-first pickup; capture by moving into
   a friendly spawn tile **and** by picking up while already standing in one; the third capture
   setting `capture` immediately while the round still finishes; a jailed carrier dropping its flag
   on its own tile.
7. **`tests/test_bc24_terrain.nim`** — dig and fill legality and their build-level prices and
   cooldowns; digging is refused on water, walls, spawn zones, occupied tiles, tiles with flags and
   tiles with friendly traps; the dam is impassable through round 200 and plain (diggable) land
   after; crumbs are collected by the mover and the pile is cleared; the `amount < 100 → ×10`
   conversion rule is applied at conversion time, once.
8. **`tests/test_bc24_upgrades.nim`** — a point per team at 600/1200/1800 and at no other round; an
   upgrade can be bought once, needs a point, costs nothing else, applies to the whole team
   immediately; ATTACK's +60 and HEALING's +50 flow through the float32 rounding; CAPTURING changes
   **the opponent's** return delay and **this team's** carry cooldown; `ACTION` is not offered.
9. **`tests/test_bc24_endladder.nim`** — `capture` on the third flag, mid-round, with the rest of the
   sweep still played; `timeLimitReached` is `round >= 2000` so round 2000 **is** played; the ladder
   fires in the engine's order with a vector each; `coin_flip` is reachable and seeded from the world
   RNG; `MORE_FLAGS_PICKED` and `RESIGNATION` are provably unreachable.
10. **`tests/test_bc24_comms.nim`** — 64 slots, values `0…65 535`, writes visible immediately to
    later ducks in the same round, reads and writes legal for **jailed** ducks, out-of-range index
    or value refused; the chassis's word packing round-trips for every field.
11. **`tests/test_bc24_sensing.nim`** — vision r² ≤ 20 through walls and water; flags sensed within
    vision including carried ones; enemy traps never sensed; the broadcast list contains exactly the
    enemy flags that are neither carried nor visible, in `allFlags` order, and is re-rolled at the
    start of rounds 1, 101, 201, … from the world RNG with the engine's scan order.
12. **`tests/test_bc24_scoring.nim`** — the points formula with float32 narrowing and truncation, one
    vector per weight; the 0–0 `share` returning 0.5; points in `[0, 100]` and the seats summing to
    ≤ 100; the ordering of `results.scores` agrees with the winner on 200 random synthetic finals.
13. **`tests/test_bc24_sheet.nim`** — every one of the ten knobs: absent → default, out of range →
    default + recorded, mistyped → default + recorded; `upgrade_order` malformations (short, long,
    duplicated, unknown value) take the **whole** default array and record once; unknown keys
    recorded (≤ 16, ≤ 40 runes); **a submitted `chassis` is recorded as an unknown field and never
    honoured** (the D1 assertion, which fails if anyone re-adds the knob); rune-boundary truncation
    of `notes`/`motto` including astral-plane characters; the 16 KB byte cap cut on a rune boundary.
14. **`tests/test_bc24_baselines.nim`** — bounded orders and legality:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the *same* `validate` the
      LLM path uses;
    - (b) in played games, **every action either chassis emits is legal for the acting duck at the
      moment it is emitted**: the right cooldown counter under 10, target in the right radius, on
      the map, of the right team, the crumbs actually present at the build-level price, no
      attacking or building or digging or filling while carrying, no attacking during setup, no
      self-heal, no dig on a spawn zone; and **no duck exceeds its 2 500 `DecisionOps`**;
    - (c) `examplefuncsplayer24` **acts** — ≥ 1 spawn, ≥ 1 move, ≥ 1 attack after round 200 — but is
      **not** required to survive: it is the deliberate weak floor and the oracle's other side, and
      it may not gain behaviour;
    - (d) `gone-sharkin` beats `examplefuncsplayer24` on 3 seeds × 2 `small` maps, 6/6.
15. **`tests/test_bc24_survival.nim`** — the **competence gate** (the LEARNINGS pin), in the bc20
    shape, with an inverted control:
    - `gone-sharkin` vs `gone-sharkin`, all-defaults sheet, 3 seeds × 2 `small` maps = 6 games.
      In **≥ 5 of 6** the game must either reach round 2000 or end on `capture` **after round 800** —
      nothing may collapse early. In **all 6**, each seat must have: spawned ≥ 45 distinct ducks,
      finished with a level sum ≥ 30, built ≥ 6 traps, dug-or-filled ≥ 10 tiles, collected ≥ 1 500
      crumbs and dealt ≥ 20 000 damage; and **across the two seats** there must be ≥ 3 enemy-flag
      pickups (a bc24 game where nobody ever touches a flag is not this game being played).
    - The same gate is then run against a **known-broken chassis** compiled behind
      `-d:bc24BrokenChassis` (a `sharkin.nim` variant that stops spawning after round 50) and
      **must fail**. A gate that cannot fail is not a gate; this assertion is what keeps it honest,
      and it is the direct answer to the 2026-09-03 finding that mechanical episode checks pass
      degenerate matches.
16. **`tests/test_bc24_knobs.nim`** — the knob-teeth gate. Paired seeded games (identical seed, map
    and opponent; the two teams identical except one knob at its low and high setting, 3 seeds
    each), each asserting a named, signed delta. Thresholds live in one table so tuning is a
    one-line change, and the header records all five substituted statistics (the bc21 r1-F6 fix):

    | knob | low → high | asserted |
    |---|---|---|
    | `specialisation_split` | `heal` → `attack` | damage dealt up ≥ 30 % **and** heal HP delivered down ≥ 60 % |
    | `flag_rush_round` | 250 → 1100 | enemy-flag pickups before round 700 down ≥ 60 % **and** crumbs collected by round 700 up ≥ 300 |
    | `trap_budget` | 0 → 60 | traps built up ≥ 10 **and** crumbs spent on dig/fill down ≥ 40 % |
    | `trap_placement` | `flag_ring` → `choke` | traps within r² ≤ 8 of an own flag down ≥ 70 % **and** traps on the measured choke tiles up ≥ 6 |
    | `trap_mix` | `stun` → `explosive` | explosive traps up ≥ 6 **and** trap damage up ≥ 1 500 |
    | `heal_priority` | `wounded_first` → `carrier_first` | heal HP delivered to flag carriers up ≥ 200 |
    | `water_dig_policy` | `none` → `moat` | tiles dug up ≥ 25 **and** crumbs spent on digging up ≥ 500 |
    | `upgrade_order` | `[attack,heal,capture]` → `[capture,heal,attack]` | the round CAPTURING is bought falls from 1800 to **600** exactly |
    | `retreat_hp` | 150 → 850 | ducks jailed down ≥ 25 % **and** heal HP received up ≥ 20 % |
    | `flag_carry_escort` | 0 → 6 | friendly ducks within r² ≤ 20 of a carrier up ≥ 2× **and** carried flags lost to the carrier's death down ≥ 30 % |

17. **`tests/test_bc24_maps.nim`** — every committed bc24 map re-converts identically from the
    pinned `.map24`; sizes, seeds, declared symmetry, wall/water/dam counts, crumb piles and totals
    match the table in §Sim module; every map is within 20…60 in both dimensions; each team has
    exactly 3 spawn-zone centres, each centre's 3×3 is all spawn zone, and the three are pairwise
    ≥ 6 apart; spawn centres re-derive in the engine's index-ascending interleaved order and flag
    ids equal their tile indices; no bc24 map name resolves to another year's map file (`Maze` and
    `Hourglass` already exist twice across years); and **the seed the `docker-smoke` step passes
    draws exactly `Yinyang`** from the `small` pool, so the smoke's map cannot drift silently.
18. **`tests/test_bc24_perf.nim`** — a full 2000-round game on `DefaultLarge` (59×31) with both
    seats on `specialisation_split: build`, `trap_budget: 60`, `water_dig_policy: moat` in
    **≤ 90 s**; failing it means switching `gamesPerMatch` to 1 (§The game).
19. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain,
    twice in one process and across a save/load; and **record → re-derive for every bc24 end
    reason** (`capture`, `more_flag_captures`, `level_sum`, `more_bread`, `coin_flip`, and the
    wall-clock `abandoned`/`deadline` stop applied by the same proc on both paths).
20. **`tests/test_bc24_replay.nim`** — a bc24 replay document round-trips; a **strict UTF-8 parse**
    of the written bytes; the viewer's re-derivation of a recorded bc24 match reproduces the
    recorded per-round hashes; traps, water, levels and flag positions re-derive identically from
    events + config + seed with nothing stored; and **every event kind respects its per-game bound**
    from the table in §Server, player, protocol.
21. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now four years wide: the
    results key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; `num_agents` present in **all four** variants' `game_config`
    and in `certification.game_config`, and **absent** at every variant top level;
    `config_schema.year.enum == ["bc26","bc20","bc21","bc24"]`; **`player[]` contains exactly the
    ids in `certification.players`** and `len(certification.players) ==
    certification.game_config.num_agents` (the pair of checks that would have caught the bc20
    release failure); every `config_schema` array bounded; `tokens` declared and required but never
    valued in a `game_config`; both `game.protocols` keys and `game.docs.readme` plus **all six**
    `pages` are `{type,value}` objects; and the installed `coworld` CLI's own
    `validate_upload_manifest` / `_load_template_manifest` accepts the template.
22. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc24** fixture
    replay; the bc24 game block shadows no `ChromeCommon` alias and no other year's game-block name
    (the tandem scar); `chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies
    by sha256; the page carries CSS for **all twelve** emitted beat kinds, with the five new ones
    scoped to `html[data-year="bc24"]`; `#bc24-doctrines` carries a dismiss control and sits outside
    `var(--band)`; and `relayout()`'s `--statrail` measurement set names `#bc24-crumbs` and
    `#bc24-levels`.

### `parity-oracle-bc24` job — the 2024 engine as a CI-only oracle

**This year's oracle is the cheapest of the series, and the recipe below was executed in the
sandbox rather than guessed.** The released fat jar
`https://releases.battlecode.org/maven/org/battlecode/battlecode24/3.0.5/battlecode24-3.0.5.jar`
(HTTP 200, 17 064 521 bytes, sha256
`9cbfc6f0b812c71a861bb203d7a100c97c694fe8440c186b3b203a58757a4095`, pinned in
`tools/oracle/bc24/jar.lock`) is **self-contained**: 11 612 entries, including all 254 `battlecode`
classes, every bundled dependency (`net.sf.jsi` among them, so the dead-artifact problem that
shaped the bc20 and bc21 jobs simply does not arise), `MethodCosts.txt`, and all 79 `.map24` map
resources. So there is **no Gradle, no jsi shim, no 94-file `javac`, no Maven Central download list
and no `deps.lock`** in this job. It is:

1. `actions/setup-java@v4`, `distribution: temurin`, `java-version: "8"`. **JDK 8 is mandatory**:
   the instrumenter rewrites `java.util` classes with ASM 5.0.4, which refuses class-file versions
   above 52, so under a newer JDK every player class load throws and the match ends empty — which is
   exactly what a "green" oracle looks like when it is proving nothing.
2. Download the jar and **verify its sha256** against `jar.lock`. Assert
   `GameConstants.SPEC_VERSION == "3.0.5"`.
3. `javac -source 8 -target 8 -cp battlecode24-3.0.5.jar -d classes tools/oracle/bc24/Bc24Trace.java
   tools/oracle/bc24/Bc24Scenario.java <upstream examplefuncsplayer/RobotPlayer.java>`.
   **Plain `-source/-target`, never `--release`** — that flag arrived in JDK 9 and dies with
   "invalid flag" on a Temurin 8 compiler in seconds (the 2026-09-04 bc21 learning; it cost that run
   a CI round).
4. Run `java -cp battlecode24-3.0.5.jar:classes battlecode.world.Bc24Trace <map> <rounds> <pkg>
   <classesDir>`. The driver is `package battlecode.world;` so it needs no reflection: it loads the
   map with `GameMapIO.loadMapAsResource(loader, "battlecode/world/resources", map, false)`, builds a
   `TeamControlProvider` over two `PlayerControlProvider`s (the **player URL must be the compiled
   classes directory** — an empty URL fails class loading and the world constructor NPEs, which cost
   this sandbox one run to discover and is why it is written down), constructs
   `new GameMaker(info, null, false)` (the null packet sink is explicitly supported) and calls
   `GameWorld.runRound()` in a loop, printing the trace **from the live objects**. **No flatbuffers
   reader, no `flatc`, no `pip install` on either side**, and the engine is used exactly as
   published.

**The trace.** One line per record; `tools/parity_trace_bc24.nim` prints the same lines from the Nim
port:

```
R <round> T <A|B> crumbs=<n> caps=<n> picked=<n> lvl=<n> alive=<n> up=<abc> upp=<n>
R <round> U <id> team=<A|B> sp=<0|1> x=<n> y=<n> hp=<n> acd=<n> mcd=<n>
           ax=<n> bx=<n> hx=<n> flag=<id|-1> ra=<n> bc=<n>
R <round> F <flagId> team=<A|B> x=<n> y=<n> start=<0|1> carried=<id|-1> dropped=<n>
R <round> W winner=<A|B|-> dom=<NAME|->
```

Units are printed **in exec order**, not id order, which is what makes an ordering bug visible. The
Java side's `bc=` column is stripped before the diff (there is no bytecode counter on the Nim side)
and is used only for the assertion in Tier A. Measured in the sandbox: a full 2000-round game is
**≈ 207 000 trace lines (~19 MB)** and **≈ 15 s of JVM** per map, so five maps cost about 75 s of
engine time; traces are written to `$RUNNER_TEMP`, compared streaming, and only the first 200
divergent lines plus a gzipped digest are uploaded.

**The tiers — pinned to what this harness can actually deliver, which was measured, not hoped.**

- **Tier A (BLOCKING) — rounds 1…2000 bit-exact, whole games, on five `small` pairs**
  (`DefaultSmall`, `Yinyang`, `BreadPudding`, `Rivers`, `Tunnels`), `examplefuncsplayer24` against
  itself, every field above. This is a *whole-game* window rather than bc21's 22–245 rounds for one
  measured reason: the 2024 example bot **never approaches its bytecode limit** — peak use across
  those five full games was **3 % of 25 000**, with **zero** mid-turn cut-offs — so the port's "no
  mid-turn resumption" divergence is never exercised and the comparison stays defined to the last
  round. The job does not assume that: it reads the `bc=` column and **fails if any duck on any
  round exceeds 50 % of the limit**, with the message naming the round and the duck, because past
  that point the window would have to shrink and the note would rather be wrong loudly than green
  quietly.
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact.** Tier A's own measurement
  showed what it cannot cover: after 2000 rounds `examplefuncsplayer24` left **all three global
  upgrade points unspent on every one of the five maps** (`upp=3`), never built a stun or water
  trap, and on three of the five never picked a flag up at all. Those are exactly the "rare code
  paths that fire mid-game" the Fleet card 1218171523823317 postmortem warns about — the ones bc26
  left as un-root-caused Tier C divergences at rounds 453 and 915. So this job runs a **second
  oracle bot of our own**, `tools/oracle/bc24/Bc24Scenario.java`, written to be (a) deterministic
  with no RNG at all, (b) cheap — the job asserts it never exceeds **25 %** of the bytecode limit,
  so it can never be cut off mid-turn — and (c) **scripted by round number to force every rare path
  early**: move all three own flags during setup (and, on one seeded variant, deliberately fail the
  6-tile spacing so the round-200 teleport fires), build all three trap types, trigger each of them
  by entry and the explosive also by dig, fill and build, drive a duck to attack level 6 and another
  to heal level 6 to exercise mastery and the level-4 freeze, get a duck jailed at level 5 to
  exercise the jail penalty, carry a flag and die with it to exercise the drop/return timer, capture
  one flag, buy all three upgrades at 600/1200/1800 in a fixed order, and then idle to round 2000 so
  the tiebreak ladder decides the game. `scaffold24.nim` gains the identical script behind
  `-d:bc24Scenario`. Both sides run it on all five pairs and must agree **bit for bit for 2000
  rounds**. This is the mechanism that converts "we hope the trap and flag code is right" into a
  gate, and it costs one file.
- **Tier B (BLOCKING) — the arithmetic, over its whole finite domain.**
  `tools/JavaBc24Tables.java`, run against the jar's own classes under the CI JDK, regenerates
  `data/bc24/skills.json` — damage and heal for all 7 levels × {upgrade on, off}, and cooldown and
  crumb cost for all 7 build levels × {explosive, stun, water, dig, fill} and all 7 attack/heal
  levels — and the job **byte-diffs** it against the committed file. bc24 has **no transcendental
  anywhere**, so unlike bc21 this tier is not a sample: it is the entire domain, and the two
  rounding regimes (float32 for damage/heal, float64 for cooldowns and costs) are proved rather
  than argued. The same step regenerates `years/bc24/constants.nim` from the pinned **sources** and
  cross-checks every value against the **jar's** classes, which is what closes the 3.0.5-jar versus
  master-sources gap recorded in `docs/RULES-BC24.md` §Divergences item 9.
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 2000-round game,
  on both bots and all five maps.** The job computes it per pair and compares it against
  `tools/ci/parity_ledger_bc24.json`, whose entries are
  `{"bot": "...", "map": "...", "first_divergent_round": N, "cause": "<one sentence>",
  "docs": "PARITY.md#<anchor>"}`. It **fails** if (a) a pair diverges and has no ledger entry,
  (b) a pair diverges **earlier** than its entry, (c) a ledger entry no longer reproduces (a stale
  excuse is as bad as a missing one), or (d) **any** divergence occurs while the traced bytecode
  peak is still under 50 % — which, on this year's evidence, means always, and therefore means a
  real rules bug rather than an instrumentation artefact.

**The note does not promise an empty ledger; it promises a rule about entries.** Every entry must
name a round, a map and a *root cause*, and a cause of "unknown" is not a cause — that is precisely
the close state the operator ruled unacceptable on 2026-09-03. What this note *does* commit to is
the thing the evidence supports: **the phase-30 exit condition is that Tier A, Tier A′ and Tier B
pass with an empty ledger**, because the measurement above says nothing in this harness forces a
divergence. If phase 30 finds one anyway, the budget for root-causing it is stated here: the
**root-cause checklist**, each item with its own unit test above, so a Tier C failure bisects in
minutes rather than becoming a card — the trap trigger queue order and the end-of-turn firing point
(test 5); an explosive triggered by build cancelling the build after spending (test 5); the water
trap's flood set and scan order (test 5); `locIsStartRef` and the same-round-drop refusal (test 6);
the 4-versus-25-round return delay and *which* team's upgrade changes it (tests 6, 8); the round-200
confirmation teleport (test 6); mastery freezing at level 3 and fill earning no build XP (test 4);
the jail penalty's tiebreak (test 4); float32 versus float64 rounding at a half-value (test 4); the
kill bounty's territory test (test 3); the capture-mid-round semantics (test 9); and the broadcast
re-roll's round parity and RNG draw order (test 11).

Tiers A, A′, B and C are the **phase-30 gate**. Every accepted divergence is listed in
`docs/RULES-BC24.md` §Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md`
gains a `bc24` section written in the same shape as the `bc21` one — including, honestly, the
measured numbers (peak bytecode %, first cut-off round if any, trace line counts, JVM seconds).

### `docker-smoke` job — now **four** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely
from `certification.game_config.num_agents` and hard-fails if the workflow's `<SEATS>` = **2**
disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes — bad-token refusal,
`/global` first frame on connect, `Ping → Pong` payload echo — against the real image on the first
episode):

1. **The bc26 certification-fixture episode**, unchanged → `dist/smoke/replay.json`.
2. **The bc20 episode**, unchanged → `dist/smoke/replay-bc20.json`.
3. **The bc21 episode**, unchanged → `dist/smoke/replay-bc21.json`.
4. **A bc24 episode**, new: `SMOKE_EXPECT_YEAR=bc24`, `SMOKE_PLAYER_IDS=awu,scaffold`,
   `SMOKE_CONTRACT_PROBE=0`, `SMOKE_REPLAY_OUT=dist/smoke/replay-bc24.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc24","pool":"small","seed":<the seed test 17 pins>,
   "gamesPerMatch":1,"maxRounds":600,"perGameBudgetSeconds":60,"matchBudgetSeconds":70,
   "connectTimeoutMs":15000}`. **600 rounds, not 400**: the first 200 are the setup phase, so a
   400-round smoke would record only 200 rounds of open play and might never show a flag change
   hands. The seed is pinned to draw `Yinyang` — the map where the *weak* bot manages flag pickups
   and captures in the reference engine run — and at the default pace 600 rounds records ~25 s of
   playback, which outlasts the viewer smoke's 15 s soak (the ecos 2026-08-23 scar).

All four run one game container + two player containers on a shared network with `file://` artifact
URIs and **no** `ANTHROPIC_API_KEY`, so both seats take the scripted path and must still complete.
All four assert: the game exits 0, **every player container exits 0**, `results.json` carries
exactly the expected key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`,
and the replay parses as **strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the
right `year`, and a non-empty `events` array. A step asserts all four replays exist and report four
different `year` values.

**The episode substance assertion (the LEARNINGS pin), in two parts.** The bc24 episode passes
`SMOKE_REQUIRE_STATS={"ducks_spawned":10,"crumbs_spent":100,"traps_built":1,"levels_end":3,
"damage_dealt":300,"heal_dealt":80}` — which the script already enforces **for both seats** — so an
episode where a seat spawned nothing, spent nothing, built nothing, levelled nothing, hit nothing
and healed nothing is a red build rather than a green one with an empty replay. Because
`SMOKE_REQUIRE_STATS` is per-seat and a 600-round game cannot guarantee *both* weak seats reach a
flag, one extra `jq` line in `ci.yml` covers the flag half across the two seats:
`([.games[0].flag_pickups[]] | add) >= 1`. Together they make an idle win machine-visible, which is
exactly what the 2026-09-03 round-1 degenerate match lacked.

### `wasm-viewer` job — the bundle is **executed**, against **all four** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay> --killfeed-overlap`
in headless chromium (Playwright pinned 1.55.0) **once per replay** — `replay.json`,
`replay-bc20.json`, `replay-bc21.json` at `--timeout 90 --soak 10`, and `replay-bc24.json` at
**`--timeout 120 --soak 15`** for the pacing reason in §Viewer. Each run requires
`data-replay-loaded="true"` (or the bridge `ready` posted after it), three **differing**
clock/scorebug readouts at 0 % / 50 % / 100 %, continued advancement across the soak,
`scrub_selector == "#scrub"` (so a seek was really exercised and the `#viewpanel` zoom slider was
not clicked instead), `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line, no
overlay covering more than 50 % of the board after the soak, and the `#killfeed`/stat-box overlap
check at 360 px, 720 px and 1280 px at both FIT and 2× zoom. `--strict-text-bounds` stays
deliberately dropped here because the board is pannable and zoomable (`#viewpanel` is kept), which
is the exact case the flag's own documentation excludes; the `canvas_text` counts are still recorded
in `viewer-smoke.json`, and the separate `tools/ci/renderer_fixture.html` step — full-cap `notes`
and `motto` on both seats at three widths including **360 px**, in the page's own CSS extracted from
`client/replay_broadcast.html` — runs through the same harness with `--strict-text-bounds`, because
every CI replay is scripted and carries no LLM text (the cogchemists 2026-08-24 scar). The fixture
gains a bc24 row. `node tools/wasm_replay_smoke.cjs` is also run against the bc24 smoke replay
**and** the committed `tests/fixtures/replay-bc24.json`, so wasm32-only failures (int overflow
traps, address-space exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation
  of anything a cog sends. The 2024 engine exists only in the `parity-oracle-bc24` CI job, and only
  as the published jar.
- **Full bytecode metering.** The 2 500-`DecisionOps` budget replaces it, with no mid-turn
  resumption. A Nim-level instrumenter is a compiler project and buys nothing the oracle does not
  already prove — and on this year's measurement the oracle never reaches the boundary at all.
- **A cog-authored Java (or any) strategy class.** Doctrines are **JSON-sheet only**; there is no
  `javac`, no instrumenter `Verifier`, no compile-error round trip and no multi-attempt loop.
  Nothing in the schema is closed against a future sandboxed hook.
- **A bc24 certification fixture, and any new `player[]` entry.** Certification stays on bc26 and
  `player[]` stays at `awu` + `scaffold`. bc24 is proven by its own `docker-smoke` episode and the
  viewer smoke run against that episode's replay.
- **56 of the 78 official maps.** The converter handles any `.map24`; v1 commits the 22 whose sizes,
  seeds, symmetry, terrain counts and crumb tables are pinned in this note. `QuestionableChess` and
  `Racetrack` are excluded on purpose (zero crumb piles collapses the build half of the game), and
  everything above 2 700 tiles stays out of the played pools for wall-clock reasons.
- **The official 2024 TypeScript client and `.map24`/replay flatbuffers in the browser.** Its
  *sprites* are reused (credited, GPL-3.0 per `client/package.json`); its app is not shipped, not
  embedded and not built. There is no flatbuffers reader on either side of this port, and no
  `match_b64` field exists.
- **Worker-side keyframe checkpoints in the viewer.** bc24 seeks re-simulate from the start of the
  game like every other year, which is why check 8 is dispatched with `settle=20000`. Keyframes are
  the obvious next optimisation for a heavy year module and they are deliberately not in v1.
- **A cog-authored comms protocol.** The 64-slot shared-array word format is the chassis's; a
  doctrine cannot redefine it. The knobs steer what gets said, not the encoding.
- **Per-duck fog in the viewer.** The spectator sees the true board — with the single, deliberate
  exception of **enemy traps**, which stay hidden until they fire, because the surprise *is* the
  trap.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the war.
- **Battlecode years other than 2026, 2020, 2021 and 2024.** The registry, `game_config.year`, the
  variant naming and `years/dispatch.nim` all support more; only these four are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. The three places where the
spec's prose and the engine disagree — map minimum size, the unreachable `MORE_FLAGS_PICKED` rung,
and the released jar's `SPEC_VERSION` — are resolved against the pinned engine in §The game and
§Packaging and recorded as divergences from the prose, not as open questions.)*
