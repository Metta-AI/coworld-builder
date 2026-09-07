# cogame-battlecode — the `bc25` year module: Battlecode 2025 "Chromatic Conflict" (design note, 2026-09-07)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a branch/PR
of the shipped repo that adds the year module `bc25` beside the shipped `bc26`, `bc20`, `bc21` and
`bc24`, adds the manifest variant `bc25`, keeps certification on `bc26`, and bumps the version of
the *same* coworld. **There is no `cogame-battlecode-2025` repo and none is created.** The starter
is chosen by game shape and it is the only defensible one: bc25 is the same shape as the four
shipped years — a deterministic Nim grid sim compiled twice (native for the server, wasm for the
viewer), one sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm replay
viewer that re-derives every frame — and the year-module boundary (`src/battlecode/years/<year>/`,
`years/registry.nim`, `years/dispatch.nim`, `game_config.year`) already exists and has now been
proved **three** times, by bc20, bc21 and bc24. Lineage: `coworld-ctf` (paintbot) →
`cogame-battlecode` → this. The starter is `Metta-AI/cogame-battlecode`, and **every convention
there holds here unless this note says otherwise**: the Nim sim/server/player layout, `nimby.lock`,
the bitworld runtime contract, the `GameVersion` discipline, `tools/build_replay_viewer.sh`, the
`replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch doctrine layer (`llm.nim` /
`decide.nim` / `sheet.nim` / `sheet_common.nim` / `baselines.nim`), the closed results document, and
"degrade, never hang".

This note lands in the repo as `docs/plans/2026-09-07-battlecode-2025-design.md` on the branch
`bc25-year-module`. The copy of record for the run is
`runs/2026-09-07-battlecode-2025/design.md`.

**Everything below about the 2025 rules was verified by reading `github.com/battlecode/battlecode25`
at commit `28975a487c1a30ed2b5bed644fe6ecd2c3dd1482`** (`master`, last commit 2025-01-26) —
`engine/src/main/battlecode/common/GameConstants.java`, `common/UnitType.java`,
`common/PaintType.java`, `common/Team.java`, `world/GameWorld.java`, `world/InternalRobot.java`,
`world/RobotControllerImpl.java`, `world/TeamInfo.java`, `world/ObjectInfo.java`,
`world/DominationFactor.java`, `world/IDGenerator.java`, `world/LiveMap.java`,
`world/GameMapIO.java`, `util/FlatHelpers.java`, `schema/battlecode.fbs`,
`client/src/colors.ts`, `client/src/constants.ts`, `client/package.json`, and
`example-bots/src/main/examplefuncsplayer/RobotPlayer.java` — and by **parsing all 75 `.map25`
flatbuffers** in `engine/src/main/battlecode/world/resources/` for their real sizes, seeds, declared
symmetry, wall counts, ruin counts, initial bodies and pre-painted tiles. **The oracle recipe in
§Tests was EXECUTED in this sandbox, not guessed**: Temurin/OpenJDK **21** + the released
`battlecode25-java-3.1.0.jar` + one driver file runs whole **2000-round** headless games in
**5.1–7.0 s each**, and every number quoted below (peak bytecode use, trace line counts, JVM
seconds, unit counts, end reasons) is a measurement off those runs. It also found the single
gotcha that would otherwise have cost a CI round — see `--add-opens` in §Tests. Base-repo facts are
from a fresh clone of `Metta-AI/cogame-battlecode` at **`5e7c8b7`** (the merge of
`bc24-year-module`, PR #4), whose shipped coworld version is **0.4.0** and whose `GameVersion` is
**GV07**. Every `file:line` and constant below is to those two trees.

### Source idea (verbatim)

```
2D-Splatoon: SOLDIERS, MOPPERS and SPLASHERS paint a 20-60 grid in their colour, build paint/money/defense TOWERS on ruins, and lay Special Resource Patterns that boost income; win by painting over 70% of the map or eliminating the enemy, else tiebreaks at round 2000. Same Java-21 toolchain generation as 2026, so the port and the sprite pipeline are the closest cousin of the shipped bc26 module. The ranking tilts it narrow (SRP-packing + coverage economy, tower-sacking nerfed mid-season, late defense-tower chokes as the differentiating edge), which makes it a good doctrine test: paint economy vs tower aggression vs choke defence.

Seats: 2 (one cog per side). num_agents = 2 in the bc25 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc25 (v1 candidates; the builder finalises them from the chassis it ports): opening {paint_eco | tower_rush | balanced}, unit_mix (soldier/mopper/splasher ratios), srp_priority, tower_type_order, ruin_claim_radius, defense_tower_chokes {never | late | early}, paint_reserve_floor, mop_enemy_paint, splash_targets {towers | territory}.
Rules, engine, oracle: Spec: https://releases.battlecode.org/specs/battlecode25/3.1.0/specs.pdf (200). Engine: https://github.com/battlecode/battlecode25 (Java 21, Gradle 8.10; engine/COPYING AGPL-3.0; Python via snek-engine, MIT). Oracle jar: https://releases.battlecode.org/maven/org/battlecode/battlecode25-java/3.1.0/battlecode25-java-3.1.0.jar (200; 3.1.2 saturn-only/403). API episode key bc25java.
Chassis and baselines (behaviour sources): erikji/battlecode25 (SPAARK, High-School 1st, AGPL-3.0), ecoArcGaming/battlecode25 (Novice 2nd, AGPL-3.0). Just Woke Up (winner) and Om Nom (3rd) are not on GitHub; IvanGeffner/BC25 has no licence — reference only.
Ranking: Tier 3-leaning in the ranking; chosen for port cost (Java 21 generation).
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc25` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc25` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc25`, league_name `Battlecode 2025 — Chromatic Conflict`, default_variant_id `bc25`, short_name `bc25` (softmax.com/battlecode/bc25), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin from the idea's HOW paragraph is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; no new repo; one variant per year; one league per year; certification stays bc26; version bump of the same coworld | this paragraph, §Packaging |
| NO Java/JDK/Node in the runtime image; full behaviour port of the 2025 rule set to a deterministic Nim sim (native + wasm); `java.util.Random` reproduced | §Sim module |
| Nim chassis ported from the **behaviour** of the two AGPL-3.0 bot repos; never vendor unlicensed code | §Decisions ("the two chassis"), §Packaging ("Licensing") |
| The year's doctrine sheet knobs | §Decisions ("the bc25 doctrine sheet") |
| Fixed per-robot decision budget instead of bytecode metering (documented divergence) | §Sim module ("the chassis, and the bytecode divergence"), §Packaging (`docs/RULES-BC25.md` §Divergences) |
| The year's maps converted at build time | §Sim module ("Maps") |
| Official 2025 client sprite set for art, credited | §Viewer ("Art"), §Packaging ("Licensing") |
| Java engine ONLY as a CI parity oracle; Tier A/A′/B/C on seeds; **root-cause-or-fail** | §Tests (`parity-oracle-bc25`) |
| Manifest variant `bc25` (`num_agents` 2) added; certification stays bc26 | §Packaging |
| Phase-50 league `bc25` with its own champions, fillers and credit pool; never touch bc26/bc20/bc21/bc24 | §Packaging ("The phase-50 plan") |
| Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side) | §The game, §Viewer |
| Branch-only work on `bc25-year-module`, PR-then-merge | §Packaging ("Branch discipline") |

### Interface facts this note is written against (read from `5e7c8b7`, not assumed)

- **D1 — the chassis is not an LLM-selectable knob.** A submitted `chassis` is recorded in
  `sheet_unknown_fields` and ignored (`src/battlecode/sheet.nim` header; `sim_types.nim` GV04 entry).
  **The bc25 sheet has no `chassis` key** and `tests/test_bc25_sheet.nim` asserts the D1 behaviour.
- **D2 — the scripted baseline plays, and CI gates on substance.** bc25's strong baseline (`spaark`)
  is a real bot; the gate is competence + positive play counters, not a win (§Tests items 15, 16 and
  the `docker-smoke` substance assertion).
- **D3 — the doctrine overlay must be dismissible.** `#bc25-doctrines` ships with a close control, an
  `Escape` binding, a re-open chip and self-dismissal on the first advance; it never sits in the
  transport band (§Viewer).
- **The manifest declares exactly the two players the certification fixture seats.** `player[]` is
  `awu` and `scaffold` and **nothing else** (`coworld_manifest_template.json` at `5e7c8b7`);
  `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`
  (`defaultBaselineFor` / `baselineFor`, both already four-armed). The bc20 run lost a release
  dispatch by adding year-specific `player[]` entries that occupied no cert slot. **This run adds no
  `player[]` entry** — see the explicit cross-check in §Packaging.
- **`GameVersion` is `GV07`** and `ReplayCompatibleGameVersions` is `["GV04","GV05","GV06",
  GameVersion]` (`src/battlecode/sim_types.nim:16,105`). This run **extends** that list; it does not
  reset it.
- **`ScriptedChassis`** is the year-neutral chassis enum in `sim_types.nim` (currently `scAwu,
  scScaffold, scBowlOfChowder, scExamplefuncsplayer, scCaliforniaRoll, scExamplefuncsplayer21,
  scGoneSharkin, scExamplefuncsplayer24`); bc25 adds two values, and each year's `newSession`
  already falls back to **that year's strong chassis** for a name belonging to another year.
- **`tools/ci/viewer_smoke.mjs` already carries the scrub-selector fix.** Its
  `SCRUB_SELECTORS = ['#scrub', '#seek', 'input[type="range"]']` is tried **one selector at a time**
  in `scrubTarget()` (`viewer_smoke.mjs:609–624`), with the zoom-slider incident recorded in the
  comment above it, and `ci.yml` additionally asserts `scrub_selector == "#scrub"` per replay
  (`ci.yml:1510–1517`). **Nothing to do here** except the pacing decision in §Viewer.
- **`relayout()`'s `--statrail` set already exists** and currently names `econ`, `bc20-soup`,
  `bc20-units`, `bc21-influence`, `bc21-units`, `bc24-crumbs`, `bc24-levels`
  (`client/replay_broadcast.html:4536`); `#killfeed`'s `bottom` is
  `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))` (line 1270). bc25's job
  is to **keep the fix armed**, not to re-fix it.
- **`tools/ci/docker_smoke.sh` already carries `SMOKE_EXPECT_YEAR`, `SMOKE_PLAYER_IDS`,
  `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`, `SMOKE_CONTRACT_PROBE` and `SMOKE_REQUIRE_STATS`**,
  and `tools/ci/cert_probe.py` runs inside it. bc25 adds a fifth episode and reuses all of them; no
  script change is needed.
- **The bc24 sibling run is Blocked at phase 30 with its module already merged to `main`.** Expect
  fixer commits to `main` (the last one, `0950ff9`, was a documentation-vs-tree correction). All bc25
  work is on `bc25-year-module`, rebased onto `main` before every push, and touches **no** bc24 file
  except the five shared ones named in §Packaging.
- **The shipped coworld version is 0.4.0.** This run ships **0.5.0**.

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as bc26/bc20/bc21/bc24 (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, four generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. No new repo (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=awu\|scaffold` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc25/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc25` bytes anywhere. |
| Real art, starter chrome verbatim | 2025 sprites cut from `battlecode25/client/src/static/img/` into `data/atlas_bc25.*` (credited in `NOTICE`, licence recorded honestly — §Packaging); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc25 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **445 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26|bc20|bc21|bc24].game_config` (all unchanged) and `variants[bc25].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc25 policy set is in §Packaging. |

---

## The game

**Battlecode 2025 "Chromatic Conflict", played by doctrine, simulated in Nim.** Two cogs each
command a clan of steampunk robot bunnies on a symmetric grid between **20×20 and 60×60**. Neither
cog moves a bunny. At t=0 each writes a **doctrine** — a JSON sheet of ten named knobs — and the
deterministic sim plays the whole match from those two sheets while both cogs watch.

The game is a paint war. Every tile a robot stands on, walks past or splashes is either **your
colour, their colour, or bare**, and the score *is* the colour count: the first clan to hold **70 %
of the map** wins on the spot, and if nobody does, round 2000 decides it on **area painted** first
of all. Paint is also the fuel. Every robot carries a stash; below 50 % full its cooldowns lengthen;
at zero it cannot move, cannot act, and bleeds **20 HP a turn** until something refills it. So the
whole economy is a loop: paint tiles → paint towers on ruins → paint towers mine paint → robots
refill → paint more tiles.

Three robots do the painting. A **soldier** (250 HP, 200 paint) paints one tile within radius 3 for
5 paint, or hits an enemy tower for 50. A **splasher** (150 HP, 300 paint) throws a 50-paint bomb up
to 2 tiles away that repaints everything within r² ≤ 4 — and, inside r² ≤ 2, paints **over enemy
paint**, which is the only way a clan reclaims ground at scale. A **mopper** (50 HP, 100 paint)
erases one enemy tile, steals 10 paint from an enemy robot standing on it, or swings its mop in a
cardinal direction and takes 5 paint from up to **six** enemies at once; it is also the only unit
that can hand paint to an ally.

Towers are the map's furniture. Each clan starts with a **money tower and a paint tower, both
already at level 2**, sitting on ruins. Every other tower must be *painted into existence*: a robot
paints an exact 5×5 two-colour pattern around a ruin and calls it done, and the pattern it painted
decides whether a **money**, **paint** or **defense** tower rises there. Towers spawn robots, shoot
(one single-target shot **and** one area shot every turn, no cooldown), and mine — and a defense
tower makes every friendly tower hit harder. Nobody may hold more than **25**.

And then there is the **Special Resource Pattern**: a different 5×5 shape, painted anywhere, paid
for with 200 chips, that must survive **50 rounds undisturbed** and then gives **+3 per turn to
every mining tower you own**. One SRP with eight mining towers is +24/turn forever; one mopper
walking through it at round 49 is 200 chips in the bin. That is the year's signature tension, and it
is the first knob on the sheet.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. The episode seed
decides which slot takes engine-side **A** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc24/maps.nim`).

### Constants (verbatim from the pinned engine — `common/GameConstants.java`, `common/UnitType.java`)

Generated into `src/battlecode/years/bc25/constants.nim` by `tools/gen_year_constants.py --year
bc25`, never hand-typed, and re-generated and byte-diffed in CI (§Tests).

| constant | value | constant | value |
|---|---|---|---|
| `GAME_MAX_NUMBER_OF_ROUNDS` | **2000** | `PAINT_PERCENT_TO_WIN` | **70** |
| `MAP_MIN_*` / `MAP_MAX_*` | **20 / 60** | `MAX_WALL_PERCENTAGE` | **20** |
| `MIN_RUIN_SPACING_SQUARED` | **25** | `MAX_NUMBER_OF_TOWERS` | **25** |
| `INITIAL_TEAM_MONEY` | **2500** | `NUMBER_INITIAL_TOWERS` | **2** (1 paint, 1 money, both L2) |
| `INITIAL_TOWER_PAINT_AMOUNT` | **500** | `INITIAL_ROBOT_PAINT_PERCENTAGE` | **100** |
| `PENALTY_NEUTRAL_TERRITORY` | **1** | `PENALTY_ENEMY_TERRITORY` | **2** |
| `MOPPER_PAINT_PENALTY_MULTIPLIER` | **2** | `NO_PAINT_DAMAGE` | **20** |
| `INCREASED_COOLDOWN_THRESHOLD` | **50** | `INCREASED_COOLDOWN_INTERCEPT` / `_SLOPE` | **100 / −2** |
| `VISION_RADIUS_SQUARED` | **20** | `COOLDOWN_LIMIT` / `COOLDOWNS_PER_TURN` | **10 / 10** |
| `MOVEMENT_COOLDOWN` | **10** | `BUILD_ROBOT_COOLDOWN` | **10** |
| `ATTACK_MOPPER_SWING_COOLDOWN` | **20** | `PAINT_TRANSFER_COOLDOWN` | **10** |
| `MARK_RADIUS_SQUARED` | **2** | `PAINT_TRANSFER_RADIUS_SQUARED` | **2** |
| `BUILD_ROBOT_RADIUS_SQUARED` | **4** | `BUILD_TOWER_RADIUS_SQUARED` | **2** |
| `RESOURCE_PATTERN_RADIUS_SQUARED` | **8** | `PATTERN_SIZE` | **5** |
| `MARK_PATTERN_PAINT_COST` | **25** | `COMPLETE_RESOURCE_PATTERN_COST` | **200** chips |
| `EXTRA_RESOURCES_FROM_PATTERN` | **3** | `RESOURCE_PATTERN_ACTIVE_DELAY` | **50** |
| `EXTRA_DAMAGE_FROM_DEFENSE_TOWER` | **5** | `EXTRA_TOWER_DAMAGE_LEVEL_INCREASE` | **2** |
| `DEFENSE_ATTACK_BUFF_AOE_EFFECTIVENESS` | **0** | `SPLASHER_ATTACK_AOE_RADIUS_SQUARED` | **4** |
| `SPLASHER_ATTACK_ENEMY_PAINT_RADIUS_SQUARED` | **2** | `MOPPER_ATTACK_PAINT_DEPLETION` / `_ADDITION` | **10 / 5** |
| `MOPPER_SWING_PAINT_DEPLETION` | **5** | `MESSAGE_RADIUS_SQUARED` | **20** |
| `BROADCAST_RADIUS_SQUARED` | **80** | `MESSAGE_ROUND_DURATION` | **5** |
| `MAX_MESSAGES_SENT_ROBOT` / `_TOWER` | **1 / 20** | `MAX_MESSAGE_BYTES` | **4** |
| `ROBOT_BYTECODE_LIMIT` | **17 500** (replaced — §Sim module) | `TOWER_BYTECODE_LIMIT` | **20 000** (replaced) |
| `GAME_DEFAULT_SEED` | 6370 (unused here) | `MAX_TURNS_WITHOUT_PAINT` | 10 — **DEPRECATED in the engine, not ported** |

`UnitType` — the whole table, verbatim (`paintCost, moneyCost, attackCost, health, level,
paintCapacity, actionCooldown, actionRadiusSquared, attackStrength, aoeAttackStrength, paintPerTurn,
moneyPerTurn, attackMoneyBonus`):

| unit | paint cost | chip cost | attack paint | HP | paint cap | action cd | action r² | single dmg | AoE dmg | paint/turn | chips/turn | chips/hit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `SOLDIER` | 200 | 250 | **5** | 250 | 200 | **10** | **9** | 50 (towers only) | — | — | — | — |
| `SPLASHER` | 300 | 400 | **50** | 150 | 300 | **50** | **4** | — | 100 (towers only) | — | — | — |
| `MOPPER` | 100 | 300 | **0** | 50 | 100 | **30** | **2** | −10 paint | — | — | — | — |
| `PAINT_TOWER` L1/L2/L3 | — | 1000/2500/5000 | 0 | 1000/1500/2000 | 1000 | 10 | **9** | 20 | 10 | **5/10/15** | — | — |
| `MONEY_TOWER` L1/L2/L3 | — | 1000/2500/5000 | 0 | 1000/1500/2000 | 1000 | 10 | **9** | 20 | 10 | — | **20/30/40** | — |
| `DEFENSE_TOWER` L1/L2/L3 | — | 1000/2500/5000 | 0 | 2000/2500/3000 | 1000 | 10 | **16** | **40/50/60** | **20/25/30** | — | — | **20/30/40** |

**Where the spec's prose and the engine disagree, the engine wins, and the disagreements are
load-bearing.** All three are recorded in `docs/RULES-BC25.md` §Divergences:

1. **The 70 % denominator.** The spec says "70 % of *paintable* squares". The engine
   (`TeamInfo.addPaintedSquares` → `checkWin`) divides by `GameWorld.areaWithoutWalls`, which is
   `width × height − walls` and therefore **counts ruin and tower tiles that can never be painted**.
   On `DefaultSmall` (20×20, 28 walls, 12 ruins) the denominator is **372**, so the threshold is
   **261** tiles out of **360** that are actually paintable — **72.5 %** of real paintable area, not
   70 %. The port divides by `areaWithoutWalls`. The viewer shows *both* numbers (§Viewer).
2. **The spec's "Attack Radius" column is a mixture of radii and squared radii.** The engine's
   `actionRadiusSquared` is **9** for a soldier (the spec's "3" is a radius), **4** for a splasher
   (the spec's "2" is a radius), **2** for a mopper (the spec's "2" is already squared), **9** for
   money/paint towers and **16** for defense towers (the spec's "3" and "4" are radii). The port uses
   the engine's `actionRadiusSquared` everywhere.
3. **The clumping penalty counts towers.** The spec says "1 times the number of adjacent allied
   bots". The engine counts every allied **unit** within r² ≤ 2, towers included
   (`InternalRobot.processEndOfTurn` → `getAllRobotsWithinRadiusSquared(loc, 2, team)`), so a robot
   standing next to its own paint tower pays for it. The port counts towers.

### The four 5×5 patterns, decoded

The engine ignores the `paintPatterns` field on the map file
(`GameWorld`: `//ignore patterns passed in with map and use hardcoded values`) and uses four
hard-coded 32-bit ints. `getPatternBit(pattern, dx, dy)` is
`(pattern >> (5 * (dx + 2) + (dy + 2))) & 1`; **bit 1 means SECONDARY colour, bit 0 means PRIMARY**.
Decoded, with `dy = +2` on top and `dx = −2` on the left (`P` = primary, `S` = secondary):

| `RESOURCE` = 28873275 | `PAINT_TOWER` = 18157905 | `MONEY_TOWER` = 15583086 | `DEFENSE_TOWER` = 4685252 |
|---|---|---|---|
| `SSPSS` | `SPPPS` | `PSSSP` | `PPSPP` |
| `SPPPS` | `PSPSP` | `SSPSS` | `PSSSP` |
| `PPSPP` | `PPSPP` | `SPPPS` | `SSSSS` |
| `SPPPS` | `PSPSP` | `SSPSS` | `PSSSP` |
| `SSPSS` | `SPPPS` | `PSSSP` | `PPSPP` |

All four are invariant under all eight square symmetries, which is why the engine's rotation/reflect
logic is commented out and `markTowerPattern(type, loc, rotationAngle, reflect)` ignores both extra
arguments. The port hard-codes the four ints, generates the four boolean tables from them, and
`tests/test_bc25_patterns.nim` byte-checks the tables against a regeneration from the ints. **The
tower-pattern check skips the centre tile** (`dx == dy == 0 && isTowerPattern`); the SRP check does
not.

Colour encoding, exactly the engine's: `0` bare, `1` A-primary, `2` A-secondary, `3` B-primary,
`4` B-secondary. `teamFromPaint` maps 1,2 → A and 3,4 → B. Markers use the same 0/1/2 alphabet per
team (`0` none, `1` primary, `2` secondary) and are stored in **two separate per-team arrays**; a
marker is invisible to the enemy and affects nothing but sensing.

### The 2025 rule set — exact numbered resolution rules

The sim's own step list. Steps 1–6 are one round; re-ordering any of them is a rules change and
bumps `GameVersion`. It mirrors `GameWorld.runRound` / `processBeginningOfRound` /
`updateDynamicBodies` / `processEndOfRound` exactly.

1. **Beginning of round.** In this order: (a) `currentRound += 1`; (b) **`updateResourcePatterns()`**
   — walk `resourcePatternCenters` **in list order**, re-check each centre's SRP paint; a centre
   whose pattern is broken is dropped from the list and its lifetime reset to 0, a centre that still
   matches stays and has its lifetime **incremented**; (c) every unit runs
   `processBeginningOfRound`: clear its message buffer of messages older than
   `MESSAGE_ROUND_DURATION = 5` rounds, clear the indicator string, and — for towers only — mine.
   A **paint** tower adds `paintPerTurn + 3 × (active SRPs of its team)` to **its own stash** (capped
   at 1000); a **money** tower adds `moneyPerTurn + 3 × (active SRPs of its team)` to the **team**
   chip pool. An SRP counts as active when its lifetime is `>= 50`. **The SRP bonus is per mining
   tower, not per team.**
2. **Turn order.** Iterate `ObjectInfo.dynamicBodyExecOrder`, a plain append-ordered list of unit ids
   with **by-value removal**: a unit created (or spawned into) the world is appended; a unit
   destroyed is removed from wherever it sits, compacting the list. So the exec order is **dynamic**
   in bc25 — unlike bc24's fixed roster — and reproducing the list operations literally is a
   correctness requirement, not a detail. The four starting towers are appended in the order the
   map's `InitialBodyTable` lists them. A unit destroyed during the sweep is skipped by the
   `existsRobot(id)` guard; the array being iterated is a **snapshot taken before the sweep**
   (`dynamicBodyExecOrder.toArray()`), so a unit built this round does **not** take a turn this
   round.
3. **Beginning of turn.** `sentMessagesCount = 0`; `towerHasSingleAttacked = towerHasAreaAttacked =
   false`; `actionCooldown = max(0, actionCooldown − 10)`; `movementCooldown = max(0,
   movementCooldown − 10)`; the unit's `DecisionOps` budget is reset to **1 750** (robots) or
   **2 000** (towers) — §Sim module, this replaces the Java bytecode limit.
4. **Run the controller.** The unit runs its team's chassis under that team's doctrine, spending at
   most its `DecisionOps` budget. `assertCanActLocation(loc, r²)` (`RobotControllerImpl:191`) gates
   every ranged action on "on the map and within `r²` of the actor"; the port reproduces it as one
   predicate. `isActionReady` is `actionCooldown < 10` **and** (for robots) `paint > 0`;
   `isMovementReady` is `movementCooldown < 10` **and** (for robots) `paint > 0`. The legal actions,
   with their exact preconditions and effects, **in the engine's own order of operations**:
   1. **Move** (8 directions, robots only): movement-ready; the destination is on the map,
      **unoccupied**, and **passable** (`passable = !wall && !ruin`; every tower sits on a ruin, so a
      tower tile is impassable for this reason and not by a separate rule). Effect: (a) the robot
      moves; (b) `addMovementCooldownTurns()` — base **10**, and *then* the low-paint surcharge
      computed from the **post-move** paint stash (rule 4.11).
   2. **Soldier attack / paint** (r² ≤ 9): action-ready; `paint >= 5`; **the target is not a wall**.
      Effect, in this order: (a) charge the action cooldown **10** with the surcharge read from the
      paint stash **before** the attack cost is deducted; (b) `addPaint(−5)`; (c) if the target tile
      holds a **tower of the other team**, deal **50** damage to it and stop; (d) otherwise, if the
      tile is paintable and is **bare or already this team's colour**, set it to the chosen colour
      (primary or secondary — the soldier picks). A soldier can never paint over enemy paint and can
      never damage a robot.
   3. **Splasher attack** (r² ≤ 4): action-ready; `paint >= 50`. Effect: (a) charge cooldown **50**
      (surcharge from the pre-cost stash); (b) `addPaint(−50)`; (c) for **every** tile within
      r² ≤ 4 of the target, in **engine scan order** (rule 4.12): if it holds an enemy **tower**,
      deal **100**; then, if the tile is paintable — paint it if it is bare or ours, and paint it
      **even if it is enemy paint** when it is also within **r² ≤ 2** of the target. One splash can
      damage several towers.
   4. **Mopper attack** (r² ≤ 2): action-ready; the target is **passable** (no wall, no ruin).
      Effect: (a) charge cooldown **30** (the mopper's `attackCost` is 0, so pre/post is moot);
      (b) if an enemy **robot** stands there, it loses **10** paint and the mopper gains **5**;
      (c) either way, if the tile carries **enemy** paint, it becomes **bare** (not ours).
   5. **Mop swing** (moppers, one of NORTH/SOUTH/EAST/WEST): action-ready; the adjacent tile in that
      direction is on the map. Effect: charge cooldown **20**; then, for the **six** offsets of that
      direction — the three tiles one step away and the three tiles two steps away, exactly the
      `dx`/`dy` tables in `InternalRobot.mopSwing` — every **enemy robot** (not tower) standing there
      loses **5** paint. Off-map offsets are skipped. Nothing is repainted.
   6. **Tower attack** (towers): **no cooldown check at all** — `assertCanAttackTower` does not call
      `assertIsActionReady`, and `RobotControllerImpl.attack` only charges a cooldown when the actor
      `isRobotType()`. A tower may fire **one single-target shot** (target within its
      `actionRadiusSquared`, `towerHasSingleAttacked` false) **and one AoE shot** (`loc == null`,
      `towerHasAreaAttacked` false) per turn. Single damage is
      `attackStrength + defenseTowerDamageIncrease(team)`; AoE damage is `aoeAttackStrength` plus
      `round(defenseBuff × 0 / 100.0)` = **+0**, applied to every enemy unit within the tower's
      radius in scan order. If **either** shot hit at least one enemy, the team gains the tower's
      `attackMoneyBonus` (20/30/40 for defense towers, 0 otherwise) — **once per shot**, so a defense
      tower that lands both earns twice.
   7. **Build a robot** (towers, r² ≤ 4): action-ready; the actor is a tower; the type is
      SOLDIER/SPLASHER/MOPPER; **the tower's own paint** ≥ the type's `paintCost`; the **team's**
      chips ≥ the type's `moneyCost`; the tile is unoccupied and passable. Effect, in this order:
      charge the tower **+10** action cooldown (towers never get the low-paint surcharge); spawn the
      robot at 100 % of its paint capacity; deduct the paint from the **tower**; deduct the chips
      from the **team**.
   8. **Mark / unmark** (robots, r² ≤ 2): the tile is paintable. Sets or clears this team's marker.
      **No cooldown, and — read from the engine — no paint cost**: `setMarker` charges nothing, so
      the spec's "1 paint" for a bare `mark()` is prose the engine does not implement. Recorded as
      divergence-from-prose #4.
   9. **Mark a tower pattern** (robots, r² ≤ 2 of the ruin) / **mark an SRP** (robots, r² ≤ 8 of the
      centre): the centre is a **valid pattern centre** — at least 2 tiles from every map edge, and
      for an SRP additionally **every one of the 25 tiles is paintable**; the robot has ≥ **25**
      paint. Effect: deduct **25** paint (SRP path) and write the 25 markers. *(The tower-pattern
      path in `RobotControllerImpl.markTowerPattern` checks the 25-paint precondition and writes the
      markers; the port charges the 25 paint on both paths and `tests/test_bc25_patterns.nim` pins
      the charge against the oracle trace.)*
   10. **Complete a tower pattern** (robots, r² ≤ 2 of the ruin) / **complete an SRP** (robots,
       r² ≤ 8 of the centre). Tower: the centre is a ruin with no tower and no unit on it; the team
       has ≥ 1000 chips; the centre is ≥ 2 from every edge; the 24 non-centre tiles match the chosen
       type's pattern **exactly** in this team's primary/secondary colours; the team holds < **25**
       towers. Effect: the tower appears at level 1 with 500 paint and full HP, the team pays
       **1000** chips, and a **defense** tower immediately adds **+5** to the team's tower damage.
       SRP: the team has ≥ **200** chips; the centre is not already this team's active SRP centre;
       the centre is a valid pattern centre; all 25 tiles match the resource pattern. Effect: the
       centre is registered with **lifetime 0** and the team pays **200** chips. It starts paying at
       lifetime ≥ 50 (rule 1b).
   11. **Upgrade a tower** (robots, r² ≤ 2): the target is a friendly tower at level 1 or 2; the team
       has ≥ the next level's `moneyCost` (2500 or 5000). Effect: pay the chips; the tower's type
       becomes the next level and its health becomes `newType.health − (oldType.health − health)`,
       i.e. **damage is carried across the upgrade**; a defense tower adds a further **+2** to the
       team's tower damage. No cooldown, no paint.
   12. **Transfer / withdraw paint** (r² ≤ 2): action-ready; the target is a different friendly unit;
       the amount is non-zero; a **positive** amount (giving) is legal only from a **mopper**; a
       **negative** amount (withdrawing) is legal only **from a tower**; the amounts fit both
       stashes. Effect, in this order: move the paint, **then** charge **+10** action cooldown — so
       the surcharge is read from the **post-transfer** stash. (Contrast rule 4.2, where the cooldown
       is charged before the cost. Both orders are the engine's; both are ported literally.)
   13. **Send a message** (r² ≤ 20): the target holds a friendly unit; **exactly one of the two is a
       tower** (robot↔tower only); the sender is under its per-turn cap (1 for robots, 20 for
       towers); and the robot's tile and the tower's tile are **connected by this team's paint** —
       a 4-neighbour BFS over tiles of this team's colour, starting at the robot's tile and refusing
       to start at all if the robot is not standing on team paint. Effect: a 32-bit word plus the
       sender id and the round lands in the recipient's buffer, readable for 5 rounds.
   14. **Broadcast** (towers): under the 20-message cap. Sends the word to every **friendly tower**
       within r² ≤ 80, in scan order, with **no paint-connectivity requirement**, and counts as one
       message.
   15. **Disintegrate**: any robot may destroy itself immediately. Free, no range, no cooldown.
   16. **Sense** (free against `DecisionOps` only): every map feature, marker, paint colour, ruin and
       unit within r² ≤ 20, in **engine scan order**. Markers are per-team and only this team's are
       returned. There is no fog beyond the radius and no hidden state at all: everything inside
       r² ≤ 20 is exact.
5. **End of turn.** For a **robot** only, in this order: (a) the territory penalty — bare tile:
   `−1 × mopperMultiplier`; enemy tile: `−2 × mopperMultiplier`; own tile: nothing — where
   `mopperMultiplier` is **2** for a mopper and 1 otherwise; (b) the crowding penalty — `−n` on bare
   or own ground and `−2n` on enemy ground, where `n` is the number of **allied units, towers
   included**, within r² ≤ 2, excluding itself. Then, for a robot whose paint is now **exactly 0**,
   `−20 HP`; a robot reduced to ≤ 0 HP is destroyed immediately. Then `roundsAlive += 1`.
   **Destruction** (from any source, at any point): the tile is cleared, a defense tower's damage
   buff is removed, the team's live-unit counter drops, and **if that counter reaches 0 the OPPONENT
   wins with `DESTROY_ALL_UNITS`** — set immediately, mid-sweep.
6. **End of round.** In this order: (a) record the per-team round stats, including
   `coverage = round(paintedSquares × 1000.0 / areaWithoutWalls)` as an integer per mille;
   (b) roll the money snapshot; (c) **end-of-match check**: if `currentRound >= 2000` **and no winner
   is set yet**, apply the ladder, first hit wins — **more squares painted**
   (`more_squares_painted`) → **more towers alive** (`more_towers_alive`) → **more chips**
   (`more_money`) → **more paint summed over all robots and towers** (`more_paint_in_units`) →
   **more robots alive** (`more_robots_alive`) → **coin flip** (`coin_flip`); (d) if a winner is set,
   the game stops. Then append this round's state hash (§Sim module).

**Four subtleties the port reproduces literally, each with its own test:**

- **A paint win fires mid-action and does not stop the round.** `TeamInfo.addPaintedSquares` runs
  `checkWin` on **every single tile recolour**, so a team can cross 70 % in the middle of a
  splasher's AoE loop; `running` is only cleared at step 6d, so every unit after the winner in the
  exec order still takes its turn and its actions are recorded. `tests/test_bc25_endladder.nim` pins
  it. The same is true of `DESTROY_ALL_UNITS`.
- **`totalPaintedSquares` is a live count, not a cumulative one.** `setPaint` decrements the old
  owner and increments the new one, and it is a **no-op on a non-paintable tile**, so mopping a tile
  bare lowers a clan's count and painting a wall does nothing at all. The name in the engine
  (`getNumberOfPaintedSquares`) is misleading and the port's field is called `livePainted`.
- **The exec-order list is mutated by value.** Building a robot appends its id; destroying one
  removes the first matching entry and shifts everything after it forward. The order of the
  survivors is preserved. This is what makes a Nim `seq[int]` with `delete(find(id))` the correct
  port, and `tests/test_bc25_execorder.nim` drives 500 random build/destroy sequences against the
  oracle's own list.
- **`processBeginningOfRound` is a hash-order sweep in the engine** (`ObjectInfo.eachRobot` →
  trove `forEachValue`) and the port sweeps in **ascending id** instead. This is safe and the
  argument is written down: the sweep only clears per-unit state, tops up a tower's **own** paint
  stash (capped per tower), and adds to a **commutative** team chip total. No branch in it reads
  another unit's state. `docs/RULES-BC25.md` §Divergences item 3.

**Deliberate non-rules, verified absent from the 2025 engine and therefore absent here:** there is
no map terrain other than walls and ruins (no water, no dam, no rubble, no cooldown terrain); ruins
cannot be created or destroyed; walls cannot be created or destroyed; there is no unit cap other
than the 25-tower cap and what paint and chips allow; a robot never regenerates HP; `GameWorld.rand`
is constructed from the map seed and **never read** (the port does not create it); `confirmRuinPlacements`
computes a validity flag and discards it (dead code); the map's `paintPatterns` array is read and
then **ignored** in favour of the four hard-coded ints; and `MAX_TEAM_EXECUTION_TIME` (20 minutes of
JVM per team) is an instrumentation rule with no meaning outside the JVM.

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc25` variant is **best-of-three on three
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

Honest per-round estimate, so the builder can check it. bc25's cost is **unit-count driven**, and
the unit count is bounded by economy rather than by a roster: the tower cap is 25 a side and a
soldier costs 200 paint, which at a realistic 6–10 paint towers is roughly one new robot every two
rounds per clan. **Measured on the real engine in this sandbox**, `examplefuncsplayer` against
itself peaks at **26–29 units on the board across every map size from 20×20 to 59×59** and plays a
whole 2000-round game in **5.1–7.0 s of instrumented JVM**. A competent chassis spends its chips
better; the port budgets for a worst case of **130 units/round** (up to 50 towers and 80 robots) and
enforces it:

- Each unit's turn is a ≤ 69-tile vision sweep, a bounded navigation step and one or two actions
  ≈ 300 `DecisionOps`, so ≈ 3.9 × 10⁴ ops/round and ≈ 8 × 10⁷ per game — **3–6 ms/round, 6–12 s per
  game** in release Nim. The *enforced* ceiling is 130 × 2 000 = 2.6 × 10⁵ ops/round.
- The one unbounded primitive in the rule set is the paint-connectivity BFS behind `sendMessage`.
  The port charges it **1 `DecisionOps` per node expanded**, which makes the chassis pay for its own
  chatter and bounds it structurally; and, because the budget is checked **before** each primitive
  and never inside one, a BFS is never cut in half (§Sim module).
- `perGameBudgetSeconds = 110` and `matchBudgetSeconds = 340` are hard monotonic-clock guards. A
  game that blows its guard is abandoned, the finished games are scored, and
  `results.reason = deadline`.
- `tests/test_bc25_perf.nim` plays a full 2000-round game on `DefaultLarge` (50×30, the largest map
  in the variant's pool) with **both seats on `opening: tower_rush`, `srp_priority: 100`,
  `defense_tower_chokes: early`** — the configuration that maximises tower count and therefore
  per-round work — and **fails CI above 90 s**.
- If that gate ever goes red the fix is one config value — `gamesPerMatch: 3 → 1` in the `bc25`
  variant — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc25's axis is **map-shaped**: it turns on ruin
  density (how much of the game is tower economy), wall percentage (whether choke defence is even a
  thing) and open area (whether SRP packing pays). The `mixed` pool spans all three deliberately
  (§Sim module, Maps). One map would rank the map, not the doctrine.

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

### Scoring, sign, and what the bc25 league ranks by

The 2025 game is win/lose; it has no point formula. This one is defined here, and it is a continuous
reading of the engine's own end ladder so that the score and the winner never tell different
stories:

```
share(x, y)   = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
area[t]       = t's live painted squares at the final round     # rung 1, and the 70% win condition
towers[t]     = t's towers alive at the final round             # rung 2
chips[t]      = t's chip balance at the final round             # rung 3
paint[t]      = sum of paint over all t's robots and towers     # rung 4
bots[t]       = t's robots alive at the final round             # rung 5
points[t]     = int(55.0'f32 * share(area[t],   area[o])
                  + 20.0'f32 * share(towers[t], towers[o])
                  + 10.0'f32 * share(chips[t],  chips[o])
                  + 10.0'f32 * share(paint[t],  paint[o])
                  +  5.0'f32 * share(bots[t],   bots[o]))       # TRUNCATION, not rounding
```

Five load-bearing details, each pinned by a test vector in `tests/test_bc25_scoring.nim`:

- every share is narrowed through **float32** before the weighted sum, and the sum is **truncated**
  by the `int()` cast. The reason is **recorder/re-deriver agreement**: the same arithmetic runs
  natively on x86-64 and in wasm32 and must produce the same integer;
- the five terms are exactly the engine's five deciding rungs, in the engine's own priority order and
  weighted in that order. Because a rung is only reached when every rung above it is **tied** — and a
  tie gives both seats a share of exactly 0.5 on that term — a `more_squares_painted`,
  `more_towers_alive`, `more_money`, `more_paint_in_units` or `more_robots_alive` win **always**
  comes with the winner's weighted sum strictly above the loser's;
- `share` returns **0.5 on a 0–0 total**, the same choice bc24 made and for the same reason: two
  clans that both ended with zero towers should not be scored differently by an arithmetic accident;
- points are in `[0, 100]` and the two seats' points sum to ≤ 100;
- `paint_enough_area` and `destroy_all_units` need no special case: the first implies an area share
  well above 0.5, the second implies `bots` and `paint` shares of exactly 1.0.

Per seat, over the games actually played:

```
results.scores[t] = 200.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** The win bonus is **200**, not bc24's 100, and the difference is deliberate:
`points` is a mean in `[0, 100]`, so a 100-per-game bonus makes a 2–1 result *theoretically* tie on
`scores` in the degenerate all-or-nothing case, while 200 makes the ordering of `results.scores`
**provably** agree with `results.wins`. `tests/test_bc25_scoring.nim` asserts that agreement on 500
random synthetic finals — with 100 it would be a `>=`; with 200 it is a `>`. **The `bc25` league
ranks by `results.scores`** (Elo over the resulting ordering), exactly as the four shipped leagues
do. A `deadline` episode scores the games that finished; a `fault` episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` in snake_case, plus our one
wall-clock value:

| `end_reason` | engine origin | meaning |
|---|---|---|
| `paint_enough_area` | `PAINT_ENOUGH_AREA` | a team's live painted squares reached **70 %** of `width × height − walls`; fires the instant the tile flips |
| `destroy_all_units` | `DESTROY_ALL_UNITS` | a team's last robot **or** tower died |
| `more_squares_painted` | `MORE_SQUARES_PAINTED` | round 2000 reached; more live painted squares |
| `more_towers_alive` | `MORE_TOWERS_ALIVE` | area tied; more towers standing |
| `more_money` | `MORE_MONEY` | towers tied; more chips |
| `more_paint_in_units` | `MORE_PAINT_IN_UNITS` | chips tied; more paint summed over robots and towers |
| `more_robots_alive` | `MORE_ROBOTS_ALIVE` | paint tied; more robots standing |
| `coin_flip` | `WON_BY_DUBIOUS_REASONS` | everything tied; a draw from the world RNG |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded |

`coin_flip` and `abandoned` are already in the manifest's `end_reason` enum; the other seven are
added (§Packaging). **`RESIGNATION` is not added.** It exists in `DominationFactor` and
`RobotControllerImpl.resign()` is a real method, but a doctrine is a JSON sheet and neither chassis
calls it, and the engine's other resignation trigger (`MAX_TEAM_EXECUTION_TIME`) is a JVM wall-clock
rule with no port. `docs/RULES-BC25.md` §Divergences item 6 records that this is *unreachable here*
rather than *absent upstream* — the distinction bc24's note could not draw and this one can.

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from the four shipped
years**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped (e.g. a spend that would take chips negative): a partial replay and `[0, 0]` are still written | `[0, 0]` |

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the
four shipped years). Container exit codes are unchanged: `0` whenever results + replay were attempted
(including `deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep answering for
the ~20 s shutdown grace, the websocket handler keeps its `Ping → Pong` **payload echo** and does not
filter binary frames (`tools/ci/cert_probe.py` proves both against the real image).

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged from the shipped years: the player container is a thin
registrar and every decision is taken inside the **game** container, because that is the only
container the platform injects the `anthropic_api_key` coworld secret into
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/battlecode/anthropic_api_key`).

**One decision turn, one parallel batch.** Both seats are asked at the same moment and their two
provider calls go out as **ONE parallel batch** (`curly.makeRequests`, `decide.nim`'s existing shape)
with the same deadline; seats are never queried one after another. The batch's wall-clock budget is
`doctrineBudgetMs = 45 000` — attempt 1 `attempt1Ms = 20 000`, the single retry `retryMs = 12 000` —
which is the per-turn budget for this game and sits inside the 720 s envelope computed in §The game.
At most 2 provider calls per seat per episode.

`src/battlecode/llm.nim` is unchanged and year-neutral: the credential ladder (Bedrock sidecar →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the single Bedrock candidate
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, fence-tolerant JSON extraction, the `throttled`
fast-fail, rune-boundary truncation, `maxOutputTokens = 1200`. With no credentials the client
disables itself at construction and every seat falls back instantly, which is what lets offline
certification and `docker-smoke` finish in seconds.

### The bc25 doctrine sheet — ten knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc25 chassis. Unknown key, wrong
type or out-of-range value → **that field's default**, recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by
answering badly — only by answering weakly.

**The LEARNINGS pin, stated as a rule the builder must hold every knob against: no setting of any
knob may produce an inert or self-starving clan.** The strategy surface lives *inside one competent
chassis*. Concretely, and independently of every knob, the chassis always: builds robots whenever a
tower can pay for one; paints the tile under a soldier that is standing on bare or enemy ground;
sends a robot below `paint_reserve_floor` to the nearest friendly paint tower or mopper; claims the
nearest unclaimed ruin inside `ruin_claim_radius` and paints its pattern; upgrades a tower when the
chip balance is above twice the next level's cost; keeps at least **2 moppers and 1 splasher** in the
census once the chip income allows it; and answers an enemy robot sensed inside its own paint. Every
knob moves *how much of what, when* — never *whether it plays*. `tests/test_bc25_knobs.nim` proves
each knob has teeth and `tests/test_bc25_survival.nim` proves the floor holds (§Tests 15, 16).

| field | type / values | default | what it changes (`src/battlecode/years/bc25/chassis/…`) |
|---|---|---|---|
| `opening` | `paint_eco` \| `tower_rush` \| `balanced` | `balanced` | `econ.nim plan()` — the chip/paint split for the first 400 rounds. `paint_eco`: 70 % of chips to robots, ruins claimed only when a soldier is already adjacent, first SRP attempted by round 150. `tower_rush`: 70 % of chips banked for `completeTowerPattern`, soldiers pushed to the two nearest ruins from round 1, no SRP before round 400. `balanced`: 50/50, ruins claimed opportunistically. **All three build robots and all three paint from round 1.** |
| `unit_mix` | object `{soldier, mopper, splasher}`, ints **0 … 100**, normalised to sum 100 after clamping `soldier ≥ 30`, `mopper ≥ 10`, `splasher ≥ 10` | `{60, 25, 15}` | `econ.nim nextBuild()` — the target census a tower builds toward. The clamps are the anti-inert floor: no mix can produce a clan with no moppers (it could never reclaim ground) or no splashers (it could never fight over painted ground). A malformed object, a missing key or a negative value takes the **whole** default and records once. |
| `srp_priority` | int **0 … 100** | 35 | `econ.nim srpBudget()` — the percentage of chip *income* reserved for `completeResourcePattern` (200 chips each) and for the soldier-turns that paint the 25 tiles. At 0 the clan never pays the 200 and spends everything on towers and robots — a real strategy on a ruin-dense map, not an idle one. At 100 it still builds robots out of the tower paint stashes, which `srp_priority` cannot touch. |
| `tower_type_order` | array of exactly **3 distinct** strings over `money` \| `paint` \| `defense` | `["money","paint","defense"]` | `econ.nim towerKindFor()` — the cyclic preference when a ruin is claimable. `defense` is only ever chosen when `defense_tower_chokes` allows it (below); if it does not, the entry is skipped and the cycle continues. A malformed, short, long or duplicated array takes the default **whole**, recorded once. |
| `ruin_claim_radius` | int **4 … 20** | 10 | `soldier.nim claimTarget()` — how far from its current frontier a soldier will walk to start a tower pattern. Low keeps the clan compact around its own paint; high spreads it across the map and into contest. It cannot express "never": at 4 a soldier still claims a ruin it is standing next to. |
| `defense_tower_chokes` | `never` \| `late` \| `early` | `late` | `siege.nim chokePlan()` — whether and when defense towers are built at the measured chokepoints between the two starting positions. `never`: `defense` is dropped from `tower_type_order` and those chips buy money/paint towers instead. `late`: from round 900, or immediately once the clan has lost a tower. `early`: from round 200. The chokepoints are the narrowest passable cuts on the shortest path between the two clans' starting money towers, measured once at round 1 by a BFS width test. |
| `paint_reserve_floor` | int **10 … 70** (percent of capacity) | 30 | `kit.nim needsRefill()` — the stash percentage at which a robot breaks off and walks to the nearest friendly paint tower (or asks the nearest mopper). Below 50 % the engine's cooldown surcharge is already biting, so a low floor is a real trade: more time on task, slower actions, and a hard stop at 0. |
| `mop_enemy_paint` | int **0 … 100** | 40 | `mopper.nim turnPlan()` — the share of mopper turns spent erasing enemy tiles rather than stripping enemy robots (mop swing / single mop on an occupied tile) and refilling allies. At 0 moppers are pure harassment and paint logistics; at 100 they are a coverage weapon. Refilling an ally below `paint_reserve_floor` always pre-empts both. |
| `splash_targets` | `towers` \| `territory` \| `mixed` | `mixed` | `splasher.nim aim()` — how a splasher picks its centre. `towers`: maximise enemy-tower damage inside r² ≤ 4. `territory`: maximise the count of enemy tiles inside r² ≤ 2 plus bare tiles inside r² ≤ 4. `mixed`: whichever scores higher this turn, with a 1.25× multiplier on the tower term. |
| `upgrade_policy` | `never` \| `paint_first` \| `money_first` \| `defense_first` | `money_first` | `econ.nim upgradePick()` — which tower gets the next 2 500 or 5 000 chips. `never` does not stop the clan spending: those chips go to new towers and new robots instead, which is the "spread wide" strategy against "build tall". The other three name the type that gets priority; ties break toward the tower nearest the front. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — paint economy against tower aggression
and choke defence — so the league's headline matchup is the one this year is actually about.

- **champion #1, `battlecode-bc25-coverage` (daveey)**: *"You command a clan of paint robots in
  Battlecode 2025. You win by painting 70% of the map, and if nobody does, round 2000 is decided by
  who painted more. Your doctrine: own the ground. Set opening \"paint_eco\", srp_priority high
  (55-90) — a Special Resource Pattern costs 200 chips and 25 painted tiles and then pays +3 per
  turn to EVERY mining tower you own, forever, so two patterns and eight towers is +48 a turn. Set
  unit_mix soldier-heavy (soldier 60-75, mopper 15-25, splasher 10-15): soldiers paint for 5 paint a
  tile at radius 3 and are the cheapest coverage in the game. Set splash_targets \"territory\" —
  a splasher repaints everything within radius 2 of its centre INCLUDING enemy paint, which is the
  only way to take ground back at scale. Set paint_reserve_floor high (40-60) so your robots never
  hit 0 paint: at 0 they cannot move, cannot act, and lose 20 health a turn. Set
  defense_tower_chokes \"never\" or \"late\" and tower_type_order with \"paint\" first — paint
  towers are what keep the soldiers painting. Set ruin_claim_radius wide (12-20) and upgrade_policy
  \"paint_first\". In notes, say which corner of the map you intend to own and what your paint
  income per round will be by round 500."*
- **champion #2, `battlecode-bc25-siege` (daveey-1)**: *"You command a clan of paint robots in
  Battlecode 2025. Towers are the map: they spawn your robots, they mine your chips and paint, they
  shoot twice a turn for free, and a team with no towers and no robots loses on the spot. Your
  doctrine: build a wall of them and knock theirs down. Set opening \"tower_rush\" and
  tower_type_order with \"money\" first — a level-3 money tower is 40 chips a turn and a tower costs
  1000/2500/5000 to build and upgrade. Set defense_tower_chokes \"early\": each live defense tower
  adds +5/+7/+9 to the single-target damage of EVERY tower you own, and a level-3 defense tower hits
  for 60 and earns you 40 chips every time it connects. Set upgrade_policy \"defense_first\" or
  \"money_first\". Set unit_mix splasher-heavy (soldier 30-45, mopper 15-25, splasher 30-45): a
  splasher does 100 damage to every enemy tower within radius 2 of its centre and a tower has
  1000-3000 health, so splashers are your siege engine. Set splash_targets \"towers\",
  srp_priority low (0-20), ruin_claim_radius tight (4-9) and paint_reserve_floor low (10-25) — you
  are trading. In notes, say which enemy tower you break first and what you do if the rush stalls."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the constant tables (unit stats, tower stats and levels, the paint economy, the
cooldown surcharge), the four pattern pictures, the map cards for all three games, the scoring
formula, the alias pair, a **HOW A GAME ENDS** section (the bc21 r1-F8 fix, kept), and the reply
contract ("reply with ONE JSON object; your reply must begin with `{`"). The assistant turn is
prefilled with `{` and the prefix re-attached before parsing (the procgen 0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`). It gains a `bc25`
arm with two published names. **The manifest still declares only `awu` and `scaffold`** — the two ids
the certification fixture seats — and `PLAYER_SCRIPTED` resolves per year, exactly as bc20, bc21 and
bc24 do:

| `PLAYER_SCRIPTED` | on `year: "bc25"` resolves to |
|---|---|
| `awu`, `spaark`, or anything unrecognised | **`spaark`** — the strong published doctrine and the champion chassis |
| `scaffold`, `examplefuncsplayer`, `examplefuncsplayer25`, `example` | **`examplefuncsplayer25`** — the deliberately weak floor and the oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field
(D1). `defaultBaselineFor("bc25")` is `spaark`, so a seat that says nothing useful plays the strong
doctrine, not the weak floor. `Baseline` gains `blSpaark = "spaark"` and
`blExamplefuncsplayer25 = "examplefuncsplayer25"`; `ScriptedChassis` gains `scSpaark = "spaark"` and
`scExamplefuncsplayer25 = "examplefuncsplayer25"`.

**`spaark` — the strong baseline and the champion chassis.** Behaviour ported from
`erikji/battlecode25` `src/SPAARK/` (AGPL-3.0, head `63165da`; the High-School 1st-place bot, whose
`SPAARK` directory is the final submission), with the mopper and splasher micro from
`ecoArcGaming/battlecode25` `java/src/v3/` (AGPL-3.0, branch `newMopper`, head `8f17e87`; the Novice
2nd-place bot) — all parameterised by the ten knobs. Its scripted reply is the all-defaults sheet.
Algorithm, by file:

- **`kit.nim`** — the per-side memory every unit shares: the remembered map (paint colour, walls,
  ruins, tower ownership, last-seen round per tile), the ruin claim table, the choke set,
  `needsRefill()` (the `paint_reserve_floor` test), and the navigator: a bounded BFS over the sensed
  window plus the remembered map, walls and ruins impassable, falling back to a greedy step with a
  6-tile no-repeat history to break oscillation, and a "prefer own paint" tiebreak because walking
  on own paint costs no paint at all. Every node expanded is charged against `DecisionOps`.
- **`econ.nim`** — the chip and paint plan: `plan()` (from `opening`), `nextBuild()` (from
  `unit_mix`), `srpBudget()` (from `srp_priority`), `towerKindFor()` (from `tower_type_order` and
  `defense_tower_chokes`), `upgradePick()` (from `upgrade_policy`). It is the only place chips are
  ever committed, so no two towers can promise the same 5 000.
- **`tower.nim`** — a tower's turn: fire the single-target shot at the lowest-HP enemy robot in
  range (tiebreak toward splashers, then soldiers, then moppers), fire the AoE shot whenever any
  enemy is in range, then build the unit `econ.nim` asks for at the free tile nearest the front, then
  broadcast the frontier word if it is under its 20-message cap.
- **`soldier.nim`** — claim a ruin inside `ruin_claim_radius`, walk to it, `markTowerPattern` the
  type `econ.nim` names, paint the marked tiles that do not match (that is exactly the loop the
  upstream example bot uses and the loop SPAARK optimises), and `completeTowerPattern` the moment it
  is legal. With no ruin to claim, paint the frontier: the tile under itself if it is not already
  ours, else the nearest bare or enemy tile within r² ≤ 9 that maximises the count of own-paint
  neighbours (which is what makes a connected blob rather than confetti — and connectivity is what
  messaging needs). Also lays the 25 SRP tiles when `econ.nim` has funded one.
- **`splasher.nim`** — `aim()` per `splash_targets`, and never splash a centre whose score is below a
  floor of 3 tiles or 1 tower, so a splasher does not burn 50 paint on one bare tile.
- **`mopper.nim`** — refill an ally below `paint_reserve_floor` first (that is the only unit that
  can), then the `mop_enemy_paint` split: mop the enemy tile that most reduces the enemy's connected
  frontier, or mop-swing the cardinal direction covering the most enemy robots (the swing hits six
  tiles, so two enemies is already better than one single mop).
- **`siege.nim`** — the choke plan and the tower-breaking plan: which enemy tower the splashers
  converge on (lowest HP, then nearest, then defense towers first because they buff everything else),
  and when defense towers go up at the measured chokes.
- **`comms.nim`** — the 32-bit message word: `[kind:3][x:6][y:6][round8:8][payload:9]`, with kinds
  `frontier`, `ruin_claimed`, `tower_lost`, `enemy_mass`, `srp_here`, `refill_here`, `choke`,
  `retreat`. Towers relay by `broadcastMessage` (r² ≤ 80, no paint needed); robots send only when
  `connectedByPaint` says they can, which is why the chassis paints connected blobs.

**`examplefuncsplayer25` — the weak floor and the parity oracle's other side.** Ported
**statement-for-statement** from
`battlecode25/example-bots/src/main/examplefuncsplayer/RobotPlayer.java`: a tower picks a random
direction and a random `rng.nextInt(3)`, builds a soldier on 0 and a mopper on 1 and does nothing on
2 (the splasher branch is commented out upstream and stays commented out here), then reads its
messages; a soldier scans `senseNearbyMapInfos()` in engine scan order and keeps the **last** ruin it
sees, steps toward it, marks the **paint**-tower pattern if the tile behind the step is unmarked,
paints every mismatched marked tile within r² ≤ 8 of the ruin, completes the pattern if it can, then
moves in a random direction and paints under itself if the tile is not already allied; a mopper moves
in a random direction, mop-swings that direction if it can, else mops the tile ahead. It seeds its
own `java.util.Random(6147)` and never calls `Math.random()`, so — as in bc24 — **it needs no
determinism patch** and the oracle's Java side is upstream's file **byte for byte**. The eight
`directions` are NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH, SOUTHWEST, WEST, NORTHWEST **in that
order**, because `rng.nextInt(8)` indexes it. It may not gain behaviour: it is one side of the
differential oracle. Its scripted reply is the all-defaults sheet (it reads no knob).

Both replies go through the **same** `validate` the LLM path uses, which is what makes the
bounded-orders test meaningful and an LLM doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `spaark` chassis, `results.fallbacks[seat] = 1`, a `doctrine_fallback` event names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default; the rest of the sheet applies |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| a side takes 2 games | the episode settles immediately — no padding |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `spaark` baseline reply:

```json
{"sheet":{"opening":"balanced","unit_mix":{"soldier":60,"mopper":25,"splasher":15},
          "srp_priority":35,"tower_type_order":["money","paint","defense"],
          "ruin_claim_radius":10,"defense_tower_chokes":"late","paint_reserve_floor":30,
          "mop_enemy_paint":40,"splash_targets":"mixed","upgrade_policy":"money_first"},
 "notes":"default spaark doctrine","motto":"Paint it and hold it."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc25/constants.nim` | **new, generated** | every `GameConstants` value plus the whole `UnitType` table and the four pattern ints, emitted by `tools/gen_year_constants.py --year bc25` from the pinned battlecode25 checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc25/world.nim` | **new** | world state: walls, ruins, the paint colour array, the two marker arrays, tower ownership by tile, the unit table, the **dynamic exec-order list**, the live-painted counters, `areaWithoutWalls`, and every action of rule 4 |
| `src/battlecode/years/bc25/rules.nim` | **new** | the six-step round loop, the end ladder, the points formula |
| `src/battlecode/years/bc25/units.nim` | **new** | the `UnitType` table, the cooldown surcharge, `addPaint` clamping, `addHealth`/destroy, the upgrade damage-carry rule, the end-of-turn paint penalties |
| `src/battlecode/years/bc25/paint.nim` | **new** | `setPaint` with the live-count bookkeeping and the mid-action 70 % win check, `isPaintable`/`isPassable`, `teamFromPaint`, the primary/secondary alphabet, `connectedByPaint` (charged BFS) |
| `src/battlecode/years/bc25/patterns.nim` | **new** | the four hard-coded pattern ints, `getPatternBit`, `checkPattern` (tower variant skips the centre), `markPattern`, `isValidPatternCenter`, `areaIsPaintable`, the SRP registry with lifetimes and `updateResourcePatterns` |
| `src/battlecode/years/bc25/towers.nim` | **new** | tower build/upgrade/destroy, the 25-tower cap, the defense-damage ledger, mining, the two per-turn attack flags, the `attackMoneyBonus` |
| `src/battlecode/years/bc25/comms.nim` | **new** | the 5-round message buffers, the robot/tower send rules, the paint-connectivity gate, `broadcastMessage` |
| `src/battlecode/years/bc25/maps.nim` | **new** | the converted bc25 pool, the loader, the per-episode draw (`drawMaps`, `sideAslotFor`) |
| `src/battlecode/years/bc25/knobs.nim` | **new** | the ten-knob `Doctrine25` type, defaults, per-field repair, `toJson`, `plainWords` |
| `src/battlecode/years/bc25/chassis/*.nim` | **new** | `spaark.nim`, `scaffold25.nim`, `scenario25.nim`, `kit.nim`, `econ.nim`, `tower.nim`, `soldier.nim`, `splasher.nim`, `mopper.nim`, `siege.nim`, `comms.nim` |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc25", title: "Battlecode 2025 — Chromatic Conflict", maxRounds: 2000, pools: @["small","mixed","large"], atlas: "atlas_bc25")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc25`; `Session` gains a `yBc25` branch (`w25`, `sides25`, `chassis25`); `yearIdOf`/`strongChassisFor`/`parseScriptedChassis`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson25`. `Bc25ActionNames = ["move","paint","splash","mop","mop_swing","transfer","withdraw","build_robot","mark","mark_tower_pattern","mark_srp","complete_tower_pattern","complete_srp","upgrade_tower","tower_attack","tower_aoe","message","broadcast","disintegrate"]` is added beside the other years' name tables so `first_action.kind` has a documented vocabulary (the r1-F14 lesson) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV08`, `ReplayCompatibleGameVersions` → `["GV04","GV05","GV06","GV07", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scSpaark` and `scExamplefuncsplayer25` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc25` arm in `defaultBaselineFor` and `baselineFor`; `blSpaark` and `blExamplefuncsplayer25` added to `Baseline`; `baselineChassis` and `baselineReply` map them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc25`, `doctrine25` on `Sheet`, a `knownKeysFor` arm, a `defaultSheet` field — exactly the four-line shape bc21 and bc24 added |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc25 adds the paint layer (four colours + bare), walls, ruins, the six unit sprites at two team palettes, tower level pips, paint bars, marker ghosts and SRP outlines |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc25 scorebug / feed / endcard shell records |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port (`nextInt()`, `nextInt(bound)`) and `IdGenerator` already carry everything bc25 needs |
| `data/maps/bc25/*.json` | **new, committed** | 22 converted maps |
| `data/bc25/tables.json` | **new, committed** | the whole finite arithmetic domain (below) |
| `data/atlas_bc25.png` / `.json` | **new, committed** | the 2025 sprite atlas |
| `tools/convert_maps_bc25.py` | **new** | reads `.map25` and writes `data/maps/bc25/<name>.json` |
| `tools/map_pools_bc25.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc25.py` | **new** | cuts `atlas_bc25.*` from the 2025 client sprites |
| `tools/gen_year_constants.py` | **`--year bc25` added** | reads the 2025 `GameConstants.java` + `UnitType.java` |
| `tools/JavaBc25Tables.java` | **new, CI-only** | regenerates `data/bc25/tables.json` under the CI JDK 21 straight out of the released jar's own classes |
| `tools/oracle/bc25/Bc25Trace.java` | **new, CI-only** | the trace driver (§Tests) — one file, compiled against the released jar |
| `tools/oracle/bc25/bc25scenario/RobotPlayer.java` | **new, CI-only** | the scenario bot that makes the rare paths bit-exact (§Tests) |
| `tools/oracle/bc25/build_oracle.sh` | **new, CI-only** | sha256-verifies the jar and compiles the driver + both bots |
| `tools/oracle/bc25/jar.lock` | **new, CI-only** | the oracle jar's URL, size and sha256 |
| `tools/parity_trace_bc25.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc25.py` | **new** | the tier comparison and the ledger check (the bc24 script, one year on) |
| `tools/ci/parity_ledger_bc25.json` | **new** | the accepted-divergence ledger |
| `tools/gen_bc25_fixture_replay.nim` + `tests/fixtures/replay-bc25.json` | **new, committed** | the fixture replay the wasm smoke loads |

**A layout rule, written here because the bc24 run paid a fixer commit for its absence (`0950ff9`).**
The file list above is the intended layout and `NOTICE`, `knobs.nim`'s doc comments and
`docs/RULES-BC25.md` all point at it. If the builder merges two of these modules — for example folds
`comms.nim` into `kit.nim` — it must update **every one of those three pointers in the same commit**,
and add a `docs/RULES-BC25.md` §Divergences item recording the merge. A licence file that credits
derived behaviour to a path that does not exist is a defect, not a cosmetic slip.

### Determinism

- **`rng.nim` is reused unchanged, and bc25 needs almost none of it.** The **only** randomness in a
  2025 game is `IDGenerator(map.getSeed())` — the 48-bit LCG, `nextInt(bound)` with both the
  power-of-two shortcut and the rejection loop, 4096-id blocks from 10 000, Fisher–Yates per block —
  which fixes the id of every unit ever built, and `Math.random()` inside `setWinnerArbitrary`.
  `GameWorld.rand` is constructed from the map seed and **never read**; the port does not create it.
  The example bot's own `Random(6147)` stream is reproduced call for call by `scaffold25.nim`.
- **Unit ids are load-bearing.** The four starting towers use the ids in the map file (1–4, below the
  10 000 floor) and every unit built during the game draws the next `IDGenerator` id, in build order.
  Ids do not decide turn order (the exec-order list does) but they decide the port's ascending-id
  sweep in step 1c and they appear in every message, so the generator must be bit-exact. It already
  is: `tests/test_rng.nim` covers it and bc20/bc21/bc24 rely on the same code.
- **`setWinnerArbitrary`'s `Math.random()`** is replaced by a draw from a world RNG seeded from the
  map's `randomSeed` (a documented divergence; reachable only when area, towers, chips, paint and
  robot counts are all tied at round 2000).
- **The scan order is load-bearing and is ported literally**: `getAllLocationsWithinRadiusSquared` is
  `x` ascending outer, `y` ascending inner, over
  `[max(cx − ceil(√r²) − 1, 0) … min(cx + ceil(√r²) + 1, w − 1)]` and the same in `y`, keeping tiles
  with `dx² + dy² ≤ r²`. It fixes which tile a splasher paints first (and therefore which recolour
  crosses 70 %), which enemy a tower's AoE hits first, and which order `senseNearbyMapInfos` returns
  — which the example bot's "keep the last ruin you saw" loop depends on. `ceil(√r²)` is over the
  finite set `{2, 4, 8, 9, 16, 20, 80}` and is **precomputed as a table**, so the port needs no
  `sqrt` and no `fdlibm` path at all.
- **All health, chip and paint arithmetic is integer.** The only floating point in the whole round
  loop is `Math.round(double)` in four places — the paint-percentage `round(paint × 100.0 / capacity)`,
  the cooldown surcharge `round(add × (100 − 2 × pct) / 100.0)` (note the **int × int** product before
  the `/100.0`), the coverage per-mille `round(painted × 1000.0 / areaWithoutWalls)`, and the
  always-zero AoE defense buff `round(buff × 0 / 100.0)`. All four are **float64** and
  `Math.round(double)` is `floor(x + 0.5)`. **There is no float32 anywhere in bc25** — the opposite
  of bc24's two-regime trap — and there are **no transcendentals**, which is why this year's
  arithmetic tier is provable over its whole finite domain (§Tests, Tier B).
- Every round appends to a **hash chain**; the viewer re-derives each round and compares, exposing
  `bc_mismatch_round`. The values folded into the bc25 chain each round: per team — live painted
  squares, chips, towers alive by type and level, robots alive by type, total paint in units, active
  SRPs, SRP lifetimes summed; plus globally — the round number, an FNV-1a 64 hash of the whole paint
  colour array (y ascending outer, x ascending inner), an FNV-1a 64 hash of the two marker arrays,
  the sum of all unit HP, and the exec-order list length.
- Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
  (`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
  scar — and the record→re-derive test covers **every** bc25 end reason, not just `complete`.
- **`GameVersion` bumps to `GV08`** in the same commit, with a prepend-only changelog line ("bc25 year
  module added; bc26, bc20, bc21 and bc24 semantics unchanged").
  **`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06","GV07", GV08]`** — it is *extended*,
  never reset: nothing a GV04–GV07 recording carries changed meaning, so every hosted replay keeps
  rendering. `tools/ci/check_gameversion.sh` is kept and claims the version across branches.

### The chassis, and the bytecode divergence

The engine's per-unit **bytecode limits** (`ROBOT_BYTECODE_LIMIT = 17 500`,
`TOWER_BYTECODE_LIMIT = 20 000`) have no meaning outside the JVM instrumenter. They are replaced by
a **fixed per-unit `DecisionOps` budget of 1 750 (robots) and 2 000 (towers)** — one tenth of the
Java limits, the same convention bc20, bc21 and bc24 use. One credit is charged for each: tile
sensed, unit examined in a sense sweep, BFS node expanded (including the paint-connectivity BFS),
direction evaluated, message read or written, pattern tile scored, and ruin or tower candidate
scored. Credits are deducted inside `kit.nim` and **enforced by the sim, not by the bot**.

Two properties make this safe and both are stated so nobody has to rediscover them:

- **The budget is checked *before* each primitive and never inside one.** A `connectedByPaint` BFS,
  a `checkPattern` sweep or a splasher's AoE loop either runs to completion or does not start. So a
  primitive's *result* is never a function of the remaining budget, only *whether the chassis got to
  ask*. When the budget reaches zero the unit's turn ends where it stands — it is **not** resumed
  mid-computation next turn, which is the one place this differs from the JVM.
- **And in bc25 the divergence is provably not exercised by the oracle.** Measured in this sandbox
  over six full 2000-round games (`DefaultSmall`, `Filter`, `Justice`, `CastleDefense`, `Paintball`,
  `DefaultMedium`, `DefaultLarge`, `DefaultHuge`), the **peak bytecode use of any unit on any round
  was 2 460–2 622, i.e. 14.1–15.0 % of the 17 500 robot limit**, and there was **no mid-turn cut-off
  at all**. So the Tier A bit-exact window for bc25 is the **whole game**, and the parity job asserts
  that rather than assuming it: if any unit ever exceeds **50 %** of its limit the job fails loudly,
  because past that point the comparison stops being defined (§Tests).

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to
Java bytecode granularity needs either a Nim-level instrumenter (a compiler project) or a
hand-annotation of every statement against `MethodCosts.txt`, and neither buys anything the budget
does not — the chassis are ours and are written to fit the budget.

### Maps

**22 of the 75 official maps** are converted and committed. Sizes, declared symmetry, seeds, wall
counts, ruin counts and pre-painted tile counts below were read out of the real `.map25` flatbuffers
(schema `GameMap`: `name`, `size`, `symmetry` `0=rotation|1=horizontal|2=vertical`, `randomSeed`,
`walls[]` (bool per tile), `paint[]` (byte per tile), `ruins` (a `VecTable`),
`initialBodies` (four `SpawnAction`s), `paintPatterns[4]` — **ignored by the engine and by us**), not
assumed. Every one of the 75 parsed cleanly with the reader `tools/convert_maps_bc25.py` implements.
`ruins` in the table below is the file's ruin list **plus the four starting-tower tiles**, which the
engine adds to `allRuins` in its own constructor and which the map file does **not** contain.

| pool | map | size | seed | symmetry | walls (%) | ruins | pre-paint |
|---|---|---|---|---|---|---|---|
| `small` | `DefaultSmall` | 20×20 | 363 | rotation | 28 (7.0) | 12 | 16 |
| `small` | `CastleDefense` | 20×20 | 842 | rotation | 60 (15.0) | 10 | 62 |
| `small` | `Paintball` | 20×20 | 733 | rotation | 46 (11.5) | 12 | 122 |
| `small` | `Justice` | 21×20 | 519 | vertical | 31 (7.4) | 12 | 34 |
| `small` | `Filter` | 21×21 | 64 | horizontal | 22 (5.0) | 9 | 12 |
| `small` | `Jail` | 20×30 | 63 | vertical | 60 (10.0) | 12 | 106 |
| `mixed` | `DefaultSmall`, `Justice` (as above), plus: | | | | | | |
| `mixed` | `Fossil` | 30×30 | 520 | horizontal | 32 (3.6) | 18 | 114 |
| `mixed` | `SandyBeach` | 30×30 | 852 | vertical | 78 (8.7) | 20 | 470 |
| `mixed` | `rain` | 30×30 | 22 | rotation | 50 (5.6) | 16 | 30 |
| `mixed` | `roads` | 30×30 | 535 | horizontal | 130 (14.4) | 12 | 146 |
| `mixed` | `DefaultMedium` | 35×35 | 424 | vertical | 32 (2.6) | 23 | 72 |
| `mixed` | `Money` | 35×35 | 228 | rotation | 84 (6.9) | 24 | 234 |
| `mixed` | `Portal` | 35×35 | 955 | rotation | 96 (7.8) | 26 | 140 |
| `mixed` | `Bunny` | 44×30 | 137 | vertical | 92 (7.0) | 20 | 258 |
| `mixed` | `DefaultLarge` | 50×30 | 340 | vertical | 24 (1.6) | 24 | 178 |
| `mixed` | `leavemealone` | 50×30 | 134 | vertical | 136 (9.1) | 18 | 324 |
| `large` (reserved) | `HungerGames` | 50×50 | 8 | rotation | 242 (9.7) | 30 | 286 |
| `large` | `Oasis` | 59×59 | 603 | rotation | 142 (4.1) | 28 | 272 |
| `large` | `DefaultHuge` | 59×59 | 248 | horizontal | 60 (1.7) | 53 | 128 |
| `large` | `Leaf` | 60×60 | 398 | vertical | 160 (4.4) | 56 | 140 |
| `large` | `SMILE` | 60×60 | 347 | vertical | 118 (3.3) | 42 | 546 |
| `large` | `gardenworld` | 60×60 | 684 | rotation | 420 (11.7) | 26 | 60 |

`mixed` (12 maps) is the `bc25` variant's pool; `small` (6) is the pool the parity oracle and the
docker smoke run on; `large` (6) is reserved for a later variant. The `mixed` pool is chosen to span
the axis the doctrines argue about: all three symmetries; 400 to 1 500 tiles; **ruin density from
12.0 per 1 000 tiles (`leavemealone`, where the game is a coverage war because there are barely any
towers to build) to 30.0 (`DefaultSmall`, where it is a tower sprint)**; and **wall percentages from
1.6 % (`DefaultLarge`, no chokes exist, so `defense_tower_chokes` is nearly a dead knob) to 14.4 %
(`roads`, where it is the whole game)**. Pre-painted area ranges from 16 tiles to 470, which decides
whether a splasher has anything to overpaint in the opening.

Maps are excluded from v1 for stated reasons, all recorded in `docs/RULES-BC25.md`: everything above
1 500 tiles is out of the played pools for wall-clock reasons (six are converted anyway, under
`large`); `Terminal`, `box`, `catface`, `fix`, `gridworld`, `maze`, `shell` and `windmill` have
**zero pre-painted tiles and no starting paint blob**, which is legal but makes the first fifty
rounds identical on every doctrine; and the remaining 45 are simply not converted in v1 — the
converter handles any `.map25`.

`tools/convert_maps_bc25.py` writes `data/maps/bc25/<name>.json` carrying: `name`, `width`, `height`,
`random_seed`, `symmetry` (the map's own declared value), `walls` (a `width × height` bit array),
`ruins` (a sparse `[x, y]` list, **exactly the file's list, without the tower tiles**), `paint` (a
sparse `[x, y, colour]` list over the 0…4 alphabet), and `initial_bodies` (four `[id, x, y, team,
type]` rows **in file order**, because that order is the initial exec order). The converted maps are
**committed** and CI re-converts and byte-diffs. The wasm bundle gets the same directory through the
existing `--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from
the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot
takes side A in game 1; sides alternate each game. Seed, map names and side assignment are recorded
in results and in the replay. Map files live under `data/maps/bc25/`, so a name shared with another
year (`DefaultSmall`, `DefaultMedium`, `DefaultLarge`, `DefaultHuge`, `Maze`/`maze`, `HungerGames`)
cannot resolve to the wrong file; `tests/test_bc25_maps.nim` asserts it anyway.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `sheet_common`, `sheet`,
`decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never branches on the
year except through `years/dispatch.nim`, whose `Session` is a Nim object **variant** so the compiler
refuses to build a half-added year. Adding 2025 is exactly what bc20, bc21 and bc24 proved adding a
year to be: a new `years/bc25/` directory, a converted map set, a sprite atlas, one registry line,
one arm per dispatch `case`, and one manifest variant. The replay header records `year` so a viewer
can never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol
id would force every existing bc26/bc20/bc21/bc24 consumer to re-register for no change in the
contract. Both `game.protocols.player` and `game.protocols.global` continue to point at
`docs/PROTOCOL.md`, which gains a bc25 section.

### The player container (thin registrar) — unchanged

`/bin/battlecode-player` reads `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dials
its seat with a bounded retry (240 × 500 ms), sends **one** registration blob and then only receives
until the socket closes, then exits 0:

```json
{"type":"register","prompt":"<PLAYER_PROMPT or empty>",
 "scripted":"awu"|"scaffold"|null,
 "policy":"<PLAYER_POLICY_LABEL>"}
```

sent as a Sprite v1 chat blob (a **binary** frame — the server must not filter non-text frames) and
re-sent a bounded number of times until acknowledged. The seat token is a **credential** and a wrong
one is refused (`tools/ci/cert_probe.py` proves it against the real image). A seat that sets neither
env var takes the active year's default baseline (`spaark` on bc25). A seat whose registration never
arrives is logged loudly and reported to `COGAME_PLAYER_FAILURE_URI`. The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket (the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no
per-round observation of any kind.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV08","year":"bc25",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":871345,
 "games":[{"map":"Portal","width":35,"height":35,"symmetry":"rotation",
           "you_are":"A","rounds":2000,
           "your_start_towers":[{"kind":"paint","level":2,"x":8,"y":9},
                                {"kind":"money","level":2,"x":26,"y":9}],
           "enemy_start_towers":[{"kind":"paint","level":2,"x":26,"y":25},
                                 {"kind":"money","level":2,"x":8,"y":25}],
           "start_separation":16.0,
           "terrain":{"walls":96,"wall_pct":7.8,"ruins":26,"ruins_per_1000":21.2,
                      "area_without_walls":1129,"truly_paintable":1103,
                      "tiles_to_win":791,"pre_painted":140},
           "chokes":3}],
 "economy":{"start_chips":2500,"tower_costs":[1000,2500,5000],
            "money_tower_per_turn":[20,30,40],"paint_tower_per_turn":[5,10,15],
            "defense_tower_chips_per_hit":[20,30,40],
            "srp":{"chip_cost":200,"paint_cost_to_mark":25,"tiles":25,
                   "rounds_undisturbed_to_activate":50,
                   "bonus":"+3 per turn to EVERY mining tower you own"},
            "max_towers":25},
 "units":{"soldier":{"hp":250,"paint_cap":200,"paint_cost":200,"chip_cost":250,
                     "attack_paint":5,"attack_r2":9,"cooldown":10,
                     "does":"paints one tile, or 50 damage to an enemy tower"},
          "splasher":{"hp":150,"paint_cap":300,"paint_cost":300,"chip_cost":400,
                      "attack_paint":50,"attack_r2":4,"cooldown":50,
                      "does":"paints everything within r2<=4 of the centre, over ENEMY paint within r2<=2, and 100 damage to every enemy tower in the blast"},
          "mopper":{"hp":50,"paint_cap":100,"paint_cost":100,"chip_cost":300,
                    "attack_paint":0,"attack_r2":2,"cooldown":30,
                    "does":"erases one enemy tile and steals 10 paint from a robot on it; mop swing (cooldown 20) takes 5 paint from up to SIX enemies in a cardinal direction; the only unit that can give paint to an ally"}},
 "paint_rules":{"vision_r2":20,
                "end_turn_cost":"1 paint on bare ground, 2 on enemy ground, 0 on your own; DOUBLED for moppers; plus 1 per adjacent allied unit (towers count), doubled on enemy ground",
                "low_paint":"below 50% of capacity every cooldown grows by (100 - 2*percent)%",
                "zero_paint":"cannot move, cannot act, loses 20 HP every turn"},
 "towers":{"how_built":"paint an exact 5x5 two-colour pattern around a ruin, then complete it for 1000 chips",
           "patterns":{"money":["PSSSP","SSPSS","SPPPS","SSPSS","PSSSP"],
                       "paint":["SPPPS","PSPSP","PPSPP","PSPSP","SPPPS"],
                       "defense":["PPSPP","PSSSP","SSSSS","PSSSP","PPSPP"],
                       "srp":["SSPSS","SPPPS","PPSPP","SPPPS","SSPSS"],
                       "legend":"P = your primary colour, S = your secondary; both count as yours for territory"},
           "hp":{"money":[1000,1500,2000],"paint":[1000,1500,2000],"defense":[2000,2500,3000]},
           "attacks":"one single-target shot AND one area shot per turn, no cooldown; defense towers add +5/+7/+9 to every allied tower's single shot"},
 "win":{"instant":"paint 70% of (width*height - walls), or destroy every enemy robot AND tower",
        "at_round_2000":["more squares painted","more towers alive","more chips",
                         "more paint in units","more robots alive","coin flip"]},
 "rules_digest":"<~7 KB condensed spec: the paint alphabet and territory, the three robots and their exact attacks, the end-of-turn paint bill, the cooldown surcharge, towers and the pattern build, upgrades and the defense buff, SRPs and the 50-round delay, messages and paint connectivity, and the end ladder>",
 "sheet_schema":{"…all ten knobs, their values, ranges and defaults…"},
 "scoring":{"weights":{"area_share":55,"tower_share":20,"chip_share":10,
                       "paint_share":10,"robot_share":5},
            "win_bonus_per_game":200,"games":3,
            "note":"shares are float32; points truncate to an integer"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with both clans' starting
tower positions (they are public: the maps are symmetric and the engine's own map file puts them
there), the terrain and ruin aggregates, **the exact tile count needed to win** (`tiles_to_win` =
`ceil(0.70 × area_without_walls)`, with `truly_paintable` beside it so the cog can see the gap that
divergence #1 creates), the seed, the full constant tables, the four pattern pictures, the knob
surface with defaults, the scoring weights, the deadlines. Because every map is symmetric, the two
seats' cards are mirror images and numerically identical in every aggregate; the only asymmetry is
`you_are` and which mirrored coordinate set is labelled "yours".
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in
either direction, at any time); the opponent's real player name (only the alias); every in-match
state (a cog receives **no** per-round observation — one sealed doctrine, then the war); the other
seat's fallback status. Inside a match the fog is the robots': vision r² ≤ 20, and the enemy's
**markers** are never sensible (they are stored in a separate per-team array). Everything else inside
the radius is exact — bc25 has no hidden-information mechanic beyond markers and range.

### Reply schema and caps

```json
{"sheet":{"opening":"tower_rush",
          "unit_mix":{"soldier":40,"mopper":20,"splasher":40},
          "srp_priority":10,"tower_type_order":["money","defense","paint"],
          "ruin_claim_radius":6,"defense_tower_chokes":"early",
          "paint_reserve_floor":20,"mop_enemy_paint":15,
          "splash_targets":"towers","upgrade_policy":"defense_first"},
 "notes":"Their money tower at (26,9) is 6 tiles from the middle choke; three splashers break it before round 600.",
 "motto":"Two colours, one map."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES**, cut on a rune boundary | unparseable → retry once → fallback sheet |
| `sheet` | ≤ **32** keys, each value type- and range-checked | bad field → that field's default, recorded |
| `unit_mix` | an object of exactly the 3 integer keys, each 0…100 | any malformation → the whole default object, recorded once |
| `tower_type_order` | exactly **3** distinct strings from the enum | any malformation → the whole default array, recorded once |
| `notes` | **280 runes** | truncated |
| `motto` | **48 runes** | truncated |
| unknown sheet keys recorded | ≤ **16** keys, each ≤ **40 runes** | truncated |
| provider error text stored in the replay | **200 runes** | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary**
(`truncateRunes`/`truncateBytes` in `sim_types.nim`; the reply's 16 KB cap is measured in bytes but
still cut on a rune boundary): byte-slicing a multi-byte character renders fine in a browser and then
fails a strict UTF-8 parser, which is exactly what makes a replay unreadable to everything but one
lenient viewer.

### Results document

The closed schema is **shared with the four shipped years** and stays that way: `results.games[]`'s
five required keys are year-neutral (`map`, `side`, `rounds_played`, `winner`, `end_reason`), every
year-specific statistic is an optional property, and `end_reason`'s enum is the union of every year's
values.

bc25's per-game keys, each a 2-array of integers in **seat** order unless marked scalar:
`squares_painted`, `coverage_permille`, `peak_coverage_permille`, `tiles_painted`, `tiles_mopped`,
`tiles_overpainted`, `chips_end`, `chips_earned`, `chips_spent`, `paint_in_units_end`, `paint_mined`,
`paint_spent`, `robots_built`, `soldiers_built`, `splashers_built`, `moppers_built`, `robots_alive`,
`robots_lost`, `robot_rounds_starved`, `towers_built`, `towers_upgraded`, `towers_alive`,
`towers_lost`, `money_towers_end`, `paint_towers_end`, `defense_towers_end`, `srp_completed`,
`srp_active_end`, `srp_rounds_active`, `splash_attacks`, `mop_swings`, `tower_damage_dealt`,
`robot_damage_dealt`, `messages_sent`, `markers_placed`; scalars `paintable_tiles`,
`area_without_walls`, `tiles_to_win`, `ruins`, `rounds_with_any_srp`.

Top level, unchanged: `names`, `aliases`, `scores`, `wins`, `points`, `games`, `seed`, `year`,
`policy_kind`, `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`,
`wall_clock_seconds`, `game_version`.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV08","year":"bc25",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"spaark",
           "sheet":{…as applied…},"sheet_submitted":"{…as received…}",
           "sheet_defaults_applied":["srp_priority"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":8123,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"Portal","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":2000,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…],"side_a_slots":[…],"abandon_after":[…],"max_rounds":2000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships), both doctrine sheets, the chassis each
seat drove, and the event list are all in the file, and the wasm sim replays every round from them.
**No `.bc25` bytes, no per-round paint dump, no per-unit dump, no marker dump** — paint, markers,
towers, SRPs, chips and unit positions are pure functions of the sim, so the browser re-derives them
and the endcard reads the re-derived totals. No server is contacted except S3 for the `.replay` file.
The per-round hash chain lets the viewer prove its re-derivation matches the recording
(`bc_mismatch_round`, surfaced as `data-replay-mismatch-round` and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`. **Every event kind here is
bounded per game** — a 2000-round match cannot be allowed to emit an event per paint stroke — and
every one has CSS (§Viewer).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides`, `ruins`, `tiles_to_win` | 1/game | `game` | beat + feed |
| `first_action` | `game`, `round`, `alias`, `kind` (from `Bc25ActionNames`) | 4/game | `build` | beat + feed |
| `tower_built` | `game`, `round`, `alias`, `tower` (`money`\|`paint`\|`defense`), `x`, `y`, `total` | ≤ 50/game | `tower` | beat + feed |
| `tower_upgraded` | `game`, `round`, `alias`, `tower`, `level` (2 or 3), `x`, `y` | ≤ 50/game | `upgrade` | beat + feed |
| `tower_lost` | `game`, `round`, `alias`, `tower`, `x`, `y`, `remaining` | ≤ 50/game | `siege` | beat + feed |
| `srp_completed` | `game`, `round`, `alias`, `x`, `y`, `pending` | ≤ 20/game | `srp` | beat + feed |
| `srp_active` | `game`, `round`, `alias`, `x`, `y`, `active_total`, `income_bonus` | ≤ 20/game | `srp` | beat + feed |
| `srp_broken` | `game`, `round`, `alias`, `x`, `y`, `age` | ≤ 20/game | `srp` | beat + feed |
| `coverage` | `game`, `round`, `alias`, `permille` — emitted the first time a clan crosses each multiple of 100 ‰ upward | ≤ 14/game | `coverage` | beat + feed ("Clan Ash passes 40 % — 79 tiles from the win") |
| `starved` | `game`, `round`, `alias`, `robots` — a round in which ≥ 5 of a clan's robots ended their turn at 0 paint | ≤ 20/game | `starve` | beat + feed |
| `rout` | `game`, `round`, `alias`, `lost` — a round in which a clan lost ≥ 5 robots | ≤ 20/game | `rout` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points`, `coverage` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

The whole event list for a three-game match is at most a few hundred entries, and
`tests/test_bc25_replay.nim` asserts each per-kind bound so a pathological game cannot produce a
20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc25/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.bc25` bytes, no 2025 TypeScript
client.

### All four viewer files come from ONE starter: `cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` → `cogame-battlecode` → here. All
four bundle files come from **that one starter** — never a mixture, because splicing one starter's
shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized`
bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23).

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc25/`, `data/bc25/tables.json` and `data/atlas_bc25.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are, including `-s ABORTING_MALLOC=1` and `ENVIRONMENT=web,worker,node`. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. No edit at all is needed for bc25: the page already sets `document.documentElement.dataset.year` from the frame's `s.year` in the **shared** block (`client/replay_broadcast.html:4657`), so a new year switches itself on. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc25 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and no existing id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar). |

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

### The appended bc25 game block

**No starter element is removed.** The bc26 block's elements (`#coopchip`, `#bars`, `#gamechips`,
`#econ`, `#doctrines`), the bc20 block's (`#bc20-flood`, `#bc20-soup`, `#bc20-units`,
`#bc20-doctrines`, `#bc20-chain`), the bc21 block's (`#bc21-votes`, `#bc21-influence`, `#bc21-units`,
`#bc21-doctrines`, `#bc21-bids`) and the bc24 block's (`#bc24-flags`, `#bc24-crumbs`, `#bc24-levels`,
`#bc24-doctrines`, `#bc24-traps`) all stay exactly where they are; the bc25 block adds its own, with
ids that are all new and all prefixed:

- `#bc25-coverage` — **the headline readout, and the year's whole story**, in the same top-centre pill
  slot bc20 uses for its flood gauge and bc24 for its flag pips: a two-sided bar
  `ASH 41 % ▓▓▓▓▒▒▒▒▒▒ 38 % BASIL` with a **70 % tick** on each side, the tile counts
  (`463 / 791 to win`) and the bare remainder. It flashes when either side crosses a decile.
- `#bc25-towers` — per clan: money / paint / defense counts with level pips (`⛁2 ⛁3 ⬢2 ✚1`), towers
  alive out of the 25 cap, and towers lost.
- `#bc25-econ` — per clan: chips banked, chips per round, paint held across all units, active SRPs
  and the income they add (`SRP ×2 → +6/tower`), and pending SRPs with their countdown to 50.
- `#bc25-doctrines` — both sheets in plain words, **dismissible** (D3): a `#bc25-doctrines-close`
  button with `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first
  playback advance (or after six seconds for a viewer who never presses play), and a
  `#bc25-doctrines-toggle` chip in the scorebug that re-opens it. Its body is capped and scrolls. It
  sits above the board area and **never** inside the transport band.
- `#bc25-srp` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: the shared `onText` block already sets
`document.documentElement.dataset.year` from the replay header and re-runs `relayout()` on a change
(`client/replay_broadcast.html:4655–4660`); the stylesheet extends the existing
`html:not([data-year="bc24"]) #bc24-… { display: none !important }` pattern with the bc25 pair. **Every
bc25 rule — including every beat-marker colour — is scoped to `html[data-year="bc25"]`** (the bc21
r1-F4 fix, kept). The frame hook is `window.Bc25Block.active(s)` / `.onFrame(s)`, added beside the
existing three in the shared `onText`, and the `if (!isBc20 && !isBc21 && !isBc24)` guard becomes
`if (!isBc20 && !isBc21 && !isBc24 && !isBc25)`.

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The `--statrail` repair is already in the tree: `relayout()` measures the union of the *visible* year
stat boxes into `--statrail` (`client/replay_broadcast.html:4536–4546`), `#killfeed`'s `bottom` is
`max(calc(76 * var(--u)), calc(var(--band, 0px) + var(--statrail, 0px) + 8px))` (line 1270),
`tests/test_viewer.nim` asserts both statically, and `viewer_smoke.mjs --killfeed-overlap` measures
client rects at 360 / 720 / 1280 px at FIT and 2× zoom on every year's replay.

**What bc25 must do — and it is the whole of the work here:**

1. add `bc25-towers` and `bc25-econ` to `relayout()`'s measured id list, beside `econ`, `bc20-soup`,
   `bc20-units`, `bc21-influence`, `bc21-units`, `bc24-crumbs` and `bc24-levels`;
2. run the existing `--killfeed-overlap` gate **on the bc25 replay too**, at all three widths and both
   zooms — five replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and
   asserts the gate goes red, so a fifth year cannot quietly disarm it (the 2026-09-04 learning about
   `page.evaluate` IIFEs and gates that look armed and test nothing).

### Zoom: KEEP `#viewpanel`

The bc25 variant's pool tops out at 50×30 and the reserved large pool at 60×60. The native board
render is 16 px per tile, so 480–960 px wide — **larger than the 360 px featured-match frame**, where
a 60-wide board would give 6.0 px per tile. So the inherited `#viewpanel` (zoom bar + minimap, with
`?viewpanel=0` still honoured for thumbnail capture) is **kept**, wired to the same
`zoomAt/setZoom/panBy/panTo/resetView` core API the worker already forwards. The default view is
fit-to-board, so a spectator who touches nothing sees the whole map and the whole paint war, which in
this year is exactly the right default: the picture *is* the colour of the map.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets
  **`--hudscale`**, **`--topband`**, **`--band`** and **`--statrail`** on `:root`, iterating to a
  fixed point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport). `#bc25-doctrines`, `#bc25-coverage`, `#bc25-towers`,
  `#bc25-econ` and `#bc25-srp` are all explicitly positioned above `var(--band)`.
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`
  ("TOWER LOST — Clan Basil's defense tower, game 2, round 1 412"), built by a bc25-block function
  with its **own** name, `buildBc25BeatButtons` — never `markBeat` (the tandem 2026-08-23 hoisting
  collision) and never colliding with `buildBeatButtons` (bc26), `buildBc20BeatButtons`,
  `buildBc21BeatButtons` or `buildBc24BeatButtons`. CSS exists for **every kind emitted**:
  `.beat-marker.doctrine`, `.game`, `.build`, `.tower`, `.upgrade`, `.siege`, `.srp`, `.coverage`,
  `.starve`, `.rout`, `.end` — all eleven **scoped to `html[data-year="bc25"]`**, so none of them can
  restyle another year's marker of the same name (`build`, `upgrade` and `end` already exist for
  other years).
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
  `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`,
  `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — check 8 must be dispatched with `settle=20000 soak=15`

bc21 taught this: a compute-heavy year defeats a fixed-wait scrub probe, because the Worker
re-simulates from the last keyframe on every seek and a 700 ms settle expires first (loaded:true,
viewer healthy, instrument too impatient). bc25 is 2000 rounds over a growing unit population and a
whole-map paint array, i.e. in the same class as bc21 and bc24. So, decided here rather than
discovered at phase 60: **the phase-60 check-8 dispatch for bc25 uses `settle=20000 soak=15`**, and
`ci.yml`'s `wasm-viewer` job runs `viewer_smoke.mjs` with `--timeout 120 --soak 15` on the bc25
replay (bc24 keeps the same; bc26/bc20/bc21 keep `--timeout 90 --soak 10`). The docker-smoke step
prints `sim_seconds / rounds`, and `docs/RULES-BC25.md` records the measured value so the next year
module can size its own probe from a number instead of a guess.

**The scrub selector needs no change.** `tools/ci/viewer_smoke.mjs` in this repo already resolves
`#scrub` before `#seek` before `input[type="range"]`, **one selector at a time**, and `ci.yml`
asserts `scrub_selector == "#scrub"` after every run. The 2026-09-03/09-04 zoom-slider defect is
fixed here; bc25 inherits the fix and the assertion, and adds nothing.

### Art

`data/atlas_bc25.png` + `data/atlas_bc25.json` (≈ 140 KB, committed), cut by
`tools/build_sprite_atlas_bc25.py` from the official 2025 client's sprite tree
(`battlecode25/client/src/static/img/` at the pinned commit). The whole set is **43 PNGs** and every
one that matters is used: `robots/{silver,gold}/{soldier,splasher,mopper,money_tower,paint_tower,defense_tower}.png`
(and their `_64x64` variants), `ruins/silver.png` (+`_64x64`), `dirty.png`, and
`icons/{chip_silver,chip_gold,paint_silver,paint_gold,grid_silver,grid_gold,gears,hammer,mop,mopper}.png`
(+ their `_64x64` variants). **Palette follows the client's own two team names:
`TEAM_COLOR_NAMES = ['Silver', 'Gold']` (`client/src/constants.ts:111`), so silver = side A and gold
= side B**, and because sides alternate each game the scorebug plate keeps the *alias* constant and
recolours its swatch per game. The four paint colours and the wall/tile colours are the client's own
`DEFAULT_GLOBAL_COLORS` (`client/src/colors.ts`): A-primary `#666666`, A-secondary `#565656`,
B-primary `#b28b52`, B-secondary `#997746`, walls `#547f31`, bare tile `#4c301e`. Licence is recorded
honestly in `NOTICE` (§Packaging): the client declares **GPL-3.0** in `client/package.json` and
carries no `LICENSE` file of its own — the same situation as bc24, verified again here.

Board rendering (`render.nim`): the paint layer is drawn first as a flat colour per tile — this is
the picture, and it must read at a glance, so primary and secondary of the same team differ only
slightly in value while the two teams differ strongly in hue. Walls and ruins are drawn over it;
a ruin with no tower shows a faint outline of the pattern the nearer clan has marked on it, which is
how a spectator learns that a tower is *coming*. Towers are drawn at 1×1 with a level pip (one, two
or three dots) and a health bar; robots are drawn by type with a **paint bar under them** (the
client's own optional overlay, made permanent here, because paint is the resource the whole year is
about) and greyed at 0 paint. A completed-but-not-yet-active SRP draws its 25 tiles with a dashed
outline and a countdown to 50; an active one draws a solid outline and a `+3` badge. Enemy markers
are never drawn — they are per-team state and drawing them would leak.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else, and the `#bc25-*` boxes dropping
their word labels to glyphs under 640 px).

- `#scorebug`: both clan plates — `CLAN ASH` over the real player name (`daveey`) and the motto — the
  live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 1412 / 2000`, `game 2 of 3 — Portal`.
- `#bc25-coverage`, `#bc25-towers`, `#bc25-econ` as above.
- `#board`: the paint layer, walls, ruins with pending patterns, all towers with level and health,
  all robots with type and paint bar, SRP outlines with countdowns, and a splash flash at the moment
  of a splasher's blast.
- `#bc25-doctrines`: each sheet in plain words ("rushes towers", "banks a tenth of its chips for
  resource patterns", "builds defense towers at the chokes from round 200", "splashers aim at
  towers", "refills at 20 % paint", "upgrades defense towers first"), plus the capped `notes` and a
  fallback badge when a seat's doctrine came from the fallback sheet. Dismissible.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and
  provably clear of the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words ("Clan Basil painted
  70 % of Portal at round 1 412" / "Clan Ash destroyed everything Clan Basil had at round 883" /
  "2 000 rounds — Clan Ash painted 463 tiles to 402"); the per-game score line; and `#bc25-srp`, the
  **war panel**: per clan, tiles painted / mopped / overpainted, peak and final coverage, towers built
  / upgraded / lost by type, chips earned and spent, paint mined and spent, robots built by type and
  lost, robot-rounds spent at zero paint, SRPs completed / activated / broken and the rounds they were
  live. Nothing about towers, paint or SRPs is stored in the replay: the wasm sim re-derives every
  round.

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`, `player`
  → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar). One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and
  `/bin/battlecode-player` from one image and copies `data/` (now carrying `maps/bc25/`,
  `bc25/tables.json` and `atlas_bc25.*`). **No JDK, no JRE, no Java, no node in any runtime stage** —
  the 2025 engine's toolchain exists only in the `parity-oracle-bc25` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc25 game block along
  with the other four.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc25` is 2025 'Chromatic Conflict' — paint
    robots colour a grid, build money, paint and defense towers by painting exact patterns onto ruins,
    and win by owning 70 % of the map."*
  - `tags` unchanged (already ≥ 3).
  - `game.config_schema`: `year.enum` becomes `["bc26","bc20","bc21","bc24","bc25"]`. `pool.enum`
    unchanged (`small` / `mixed` / `large`; each year owns its own pool table). `maxRounds` keeps
    `minimum 50, maximum 2000` — **bc25's 2000 is exactly the existing ceiling, so no schema change is
    needed**. `gamesPerMatch` keeps `maximum 3`; `perGameBudgetSeconds` keeps `maximum 300` (bc25 uses
    110) and `matchBudgetSeconds` `maximum 600` (bc25 uses 340). `tokens` stays **declared and
    required** (the runner injects it — the 2026-09-03 lesson); every array keeps `minItems`/`maxItems`;
    no runner-managed `tokens` **values** inside any `game_config`.
  - `game.results_schema`: bc25's optional properties added beside the other years';
    `games.items.required` unchanged (the five year-neutral keys); `end_reason`'s enum extended with
    `paint_enough_area`, `destroy_all_units`, `more_squares_painted`, `more_towers_alive`,
    `more_money`, `more_paint_in_units`, `more_robots_alive` (`coin_flip` and `abandoned` are already
    there).
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one
    entry and keeps the six it has: `rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc24.md`,
    **`rules-bc25.md`** (Battlecode 2025 "Chromatic Conflict": rules, knobs and divergences →
    `docs/RULES-BC25.md`), `replay.md`, `parity.md` (→ `docs/PARITY.md`, which gains a bc25 section).
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc25
    resolution ("…, SPAARK on bc25" / "…, examplefuncsplayer25 on bc25").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The
  certifier's `players-run` step requires **every** declared `player[]` entry to occupy a slot in
  `certification.players`, and the certifier also requires
  `len(certification.players) == certification.game_config.num_agents`. With `num_agents = 2` there are
  exactly **two** cert slots, they are filled by `awu` and `scaffold`, and therefore **`player[]` may
  contain exactly those two ids and nothing else**. Adding `battlecode-bc25-spaark` or any other
  year-specific runnable to `player[]` would fail the release with `players_missing`. It is also
  unnecessary: `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`, so seating
  `awu` on a bc25 episode already plays SPAARK and seating `scaffold` already plays
  examplefuncsplayer25. The scripted bc25 policies reach the league through `tools/ci/policies.json`,
  which is a *policy* list and has nothing to do with `player[]`. `tests/test_manifest.nim` asserts
  all three facts (`player[]` ids == `certification.players` ids;
  `len(certification.players) == certification.game_config.num_agents`; `num_agents` present in every
  variant's `game_config` and absent at variant top level), so the contradiction cannot be
  re-introduced silently.

  **Variants — one per Battlecode year:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | unchanged | **2** |
  | `bc21` | Battlecode 2021 — Campaign (2 seats) | unchanged | **2** |
  | `bc24` | Battlecode 2024 — Breadwars (2 seats) | unchanged | **2** |
  | `bc25` | Battlecode 2025 — Chromatic Conflict (2 seats) | `year: "bc25"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 2000`, `num_agents: 2`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 110`, `matchBudgetSeconds: 340`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `bc25`'s variant description: *"Best of three on the mixed pool. Two clans of paint robots colour a
  grid. Soldiers paint one tile at a time, splashers repaint a blast radius including the enemy's
  ground, and moppers wipe it back to bare. Towers are built by painting an exact 5×5 pattern onto a
  ruin, and a Special Resource Pattern pays every mining tower you own — if it survives fifty rounds.
  Paint 70 % of the map, destroy everything they have, or be ahead on colour at round 2 000."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false`).

  **Certification fixture — UNCHANGED, and stays on bc26.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, `"num_agents": 2` and its existing fast settings (`pool: small`, `seed: 1`,
  `gamesPerMatch: 1`, `maxRounds: 400`). There is **no bc25 certification fixture in v1** (§Out of
  scope): certification is the platform's contract check, it already passes on bc26, and re-pointing
  it at a brand-new year module would put the release at the mercy of the newest code for no gain.
  bc25 is proven instead by its own `docker-smoke` episode (§Tests), which produces a real bc25 replay
  that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  **`0.4.0 → 0.5.0`** — because it adds a variant and adds optional results properties without
  changing any existing behaviour. `GameVersion` goes `GV07 → GV08` and
  `ReplayCompatibleGameVersions` is **extended** to `["GV04","GV05","GV06","GV07","GV08"]`, so every
  hosted bc26/bc20/bc21/bc24 replay keeps rendering (the bc20 learning about `GameVersion` handling:
  extend, never reset, and claim the version across branches with `tools/ci/check_gameversion.sh`).
  The release is dispatched through the existing `coworld-release.yml` with the same step order
  (build → certify → upload-policies → upload-coworld → secret put). **Certify runs against bc26,
  exactly as before**, and `release-result.json` must still show `canonical: true` and
  `certify.replay_liveness` containing `skipped (static replay bundle declared`.

- **Branch discipline.** All work lands on the branch **`bc25-year-module`**, PR-then-merge, and
  `ci.yml`'s `on.push.branches` gains that branch beside `main`, `bc20-year-module`,
  `bc21-year-module` and `bc24-year-module`. The sibling bc24 run is **Blocked at phase 30 with its
  module already merged to `main`**, so fixer commits to `main` are expected. The branch is rebased
  onto `origin/main` before every push. bc25 touches exactly these shared files —
  `sim_types.nim`, `baselines.nim`, `sheet.nim`, `years/registry.nim`, `years/dispatch.nim`,
  `render.nim`, `broadcast.nim`, `client/replay_broadcast.html`, `coworld_manifest_template.json`,
  `tools/ci/policies.json`, `tools/gen_year_constants.py`, `.github/workflows/ci.yml`,
  `docs/PARITY.md`, `NOTICE`, `README.md` — and every edit to each of them is **additive** (a new
  enum value, a new `case` arm, a new appended block), which is what makes those rebases clean. If a
  fixer commit takes `GV08` first, this branch rebases to `GV09` and extends the compatibility list
  again — the bc20 precedent, and `tools/ci/check_gameversion.sh` is the thing that catches it.

- **`tools/ci/policies.json`** gains the bc25 set beside the bc26, bc20, bc21 and bc24 sets (a
  scripted champion is a failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-bc25-coverage","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"coverage"}},
   {"name":"battlecode-bc25-siege","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"siege"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-spaark","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"spaark","PLAYER_POLICY_LABEL":"spaark"}},
   {"name":"battlecode-examplefuncsplayer25","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer25","PLAYER_POLICY_LABEL":"examplefuncsplayer25"}}]
  ```
  `<IMAGE>` is the **player** service's image (the 2026-09-03 lesson). Champion #2 is uploaded while
  `daveey-1` is the active player. LLM credentials reach the **game** container through the manifest
  env; the player pods need no Bedrock sidecar in this lineage.

  **Release dispatch shape, decided:** dispatch `coworld-release.yml` with a `policies` **override**
  limited to the four bc25 entries (the bc20 pattern), so the release does not recut vN+1 of the
  bc26/bc20/bc21/bc24 policies the four existing leagues have seated. If the override is ever dropped
  and the full file is used instead, phase 50 must take its labels from **this** release's
  `release-result.json` and never from remembered ones (the bc21 learning). Either shape works; this
  run picks the override.

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **fifth league**, created beside the bc26, bc20, bc21 and bc24 ones and touching none of them and
not the game's default league:

| field | value |
|---|---|
| `league_key` | `bc25` |
| `league_name` | `Battlecode 2025 — Chromatic Conflict` |
| `default_variant_id` | `bc25` |
| `short_name` | `bc25` → `softmax.com/battlecode/bc25` (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc25-coverage` (owned by **daveey**), `battlecode-bc25-siege` (owned by **daveey-1**) — deliberately the year's two poles, coverage economy against tower siege |
| fillers (scripted) | `battlecode-spaark`, `battlecode-examplefuncsplayer25` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues`
filtered on `game.coworld_name` now returns **five** rows; select by `league_key`/name or you will
configure a sibling year's league. Fillers are set **before** the first `trigger-round`. The atlas
slug is `battlecode/bc25`.

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged by
the repository itself. `NOTICE` gains four sections:

- **`battlecode/battlecode25` engine — AGPL-3.0** (verified: `engine/COPYING` is the GNU AGPL v3;
  `schema/LICENSE` is too; **the repository root carries no LICENSE**). Pinned commit
  `28975a487c1a30ed2b5bed644fe6ecd2c3dd1482`. The derived files are named individually:
  `src/battlecode/years/bc25/**` (behaviour, hand-ported), `years/bc25/constants.nim` (generated from
  `GameConstants.java` + `UnitType.java`), `data/maps/bc25/*.json` (converted from `.map25`),
  `data/bc25/tables.json` (generated from the engine's own arithmetic), and
  `years/bc25/chassis/scaffold25.nim` (examplefuncsplayer, ported statement for statement — it is the
  parity oracle's other side and may not gain behaviour). **The engine itself is used only at CI
  time**; no JDK, no JRE and no upstream Java source or bytecode exists in any image this repository
  builds.
- **`battlecode/battlecode25` client sprites — GPL-3.0.** `client/package.json` declares
  `"license": "GPL-3.0"` and the client directory has **no LICENSE file of its own** (verified again
  for 2025; the same situation as 2024 and *not* the same as 2021). `data/atlas_bc25.*` is cut from
  `client/src/static/img/**` and is credited as GPL-3.0 in `NOTICE`, naming the 43 source PNGs by
  directory. GPLv3 §13 and AGPLv3 §13 expressly permit the combination of GPL-3.0 and AGPL-3.0 works,
  which is exactly what this repository is; the repository as a whole remains AGPL-3.0 and `NOTICE`
  records the sprite files' own terms. `schema/package.json` also says `GPL-3.0` while
  `schema/LICENSE` is the AGPL — the discrepancy is recorded and is moot here, because **no schema
  code is used at all** (there is no flatbuffers reader on either side of this port, only a
  hand-written vtable walk in the map converter).
- **`erikji/battlecode25` — AGPL-3.0**, head `63165da`, `src/SPAARK/`. What derives from it:
  `years/bc25/chassis/{spaark,kit,econ,tower,soldier,siege,comms}.nim` — the tower-driven build order,
  the ruin claim table and its comms word, the frontier-connectivity painting rule, the choke
  measurement, and the navigator's own-paint-preferring tiebreak. **Behaviour, not code**, rewritten
  in Nim and parameterised by this coworld's doctrine sheet.
- **`ecoArcGaming/battlecode25` — AGPL-3.0**, branch `newMopper`, head `8f17e87`, `java/src/v3/`. What
  derives from it: the mopper turn plan (refill first, then swing-versus-single scoring) and the
  splasher aiming heuristic, in `years/bc25/chassis/{mopper,splasher}.nim`.
- **`IvanGeffner/BC25` carries no licence** (verified: the GitHub API reports `license: null`) and is
  **not vendored, not ported, not compiled and not read into any file here**, in this year as in the
  others. Just Woke Up and Om Nom are not published anywhere and contribute nothing.

`docs/RULES-BC25.md` carries the full **§Divergences** list: (1) no bytecode instrumentation — a fixed
1 750/2 000-`DecisionOps` budget with no mid-turn resumption and no mid-primitive cut, together with
the measurement that makes it harmless here (peak 14.1–15.0 % of the limit, zero cut-offs) and the CI
assertion that fails the job at 50 %; (2) `setWinnerArbitrary`'s `Math.random()` replaced by a
world-RNG draw; (3) the `eachRobot` hash-order sweep in `processBeginningOfRound` replaced by an
ascending-id sweep, with the order-independence argument; (4) the spec's "1 paint to mark" is not
implemented by the engine and is not implemented here; (5) the 70 % denominator is
`width × height − walls`, which counts unpaintable ruin tiles — with the `DefaultSmall` arithmetic;
(6) `RESIGNATION` is reachable in the engine through `rc.resign()` but unreachable here, and
`MAX_TEAM_EXECUTION_TIME` has no port; (7) the map's `paintPatterns` array is ignored in favour of the
four hard-coded pattern ints, exactly as the engine does; (8) `MAX_TURNS_WITHOUT_PAINT`,
`GameWorld.rand` and `confirmRuinPlacements` are dead in the engine and absent here; (9) the
`deadline` wall-clock stop, a coworld concept and not an engine one, recorded as one load-bearing
record; (10) no indicator strings, dots, lines, timeline markers or profiler, and no `.bc25` output;
(11) 22 of the 75 official maps converted, with the reasons for the exclusions; (12) the released
3.1.0 jar carries `SPEC_VERSION = "1"`, so the jar's identity is pinned by **sha256** rather than by a
version string; (13) both chassis are behaviour ports parameterised by the doctrine sheet;
(14) the chassis file layout, if the builder merges any two modules.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, `<SEATS>` = **2**). The sandbox runs none of it; CI is the harness.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc25_cooldown.nim`** — the two counters: both decrement by 10 at the start of every
   turn and floor at 0; an action needs `< 10` **and** non-zero paint (robots), a move the same; the
   low-paint surcharge `add + round(add × (100 − 2 × pct) / 100.0)` with `pct = round(paint × 100.0 /
   capacity)`, asserted at every `(paint, capacity)` pair for all three robot types and all four base
   cooldowns, including the boundary at exactly 50 %; **towers never get the surcharge**; a tower's
   attack charges **no** cooldown at all; `buildRobot` charges the tower +10; the attack path charges
   the cooldown from the **pre-cost** stash and `transferPaint` from the **post-transfer** stash.
2. **`tests/test_bc25_paint.nim`** — the 0…4 colour alphabet and `teamFromPaint`; `setPaint` is a
   no-op on walls and ruins; the live-count bookkeeping (paint over the enemy moves one from their
   count to ours, mopping bare removes one from theirs and adds none to ours); the 70 % check fires
   **the instant** the count crosses `0.70 × areaWithoutWalls` and not one tile earlier, including
   the `DefaultSmall` case (372 → 261); the round already finishes after it fires.
3. **`tests/test_bc25_units.nim`** — soldier paint/attack legality and effect at r² ≤ 9 (walls
   refused, enemy paint never overwritten, towers damaged for 50, robots never damaged); splasher at
   r² ≤ 4 with the r² ≤ 4 AoE and the r² ≤ 2 enemy-paint window, in engine scan order, damaging every
   enemy tower in the blast; mopper single at r² ≤ 2 (10 paint off, 5 on, tile to bare, ruins and
   walls refused); mop swing's exact six offsets for all four cardinals with off-map skipping and
   towers immune; `addPaint` clamping at 0 and capacity; `addHealth` capping at max and destroying at
   ≤ 0.
4. **`tests/test_bc25_towers.nim`** — the tower table at all three levels; `completeTowerPattern`
   legality (ruin, no tower, no unit, ≥ 1000 chips, ≥ 2 tiles from every edge, exact 24-tile pattern
   with the centre skipped, 25-tower cap) and effect (level 1, 500 paint, full HP, chips deducted,
   defense buff +5); `upgradeTower` legality and the **damage-carry** rule
   (`newHealth = newType.health − (oldType.health − health)`), the +2 defense buff per level, and that
   L3 cannot be upgraded; the two per-turn attack flags; single damage `attackStrength + buff` and AoE
   damage `aoeAttackStrength + 0`; the `attackMoneyBonus` paid once per landing shot, so a defense
   tower that lands both earns twice; mining at the start of the round into the tower's own capped
   stash (paint) or the team pool (chips).
5. **`tests/test_bc25_patterns.nim`** — the four ints decode to the four tables in the note;
   `getPatternBit`'s index arithmetic; bit 1 = secondary; the tower check skips the centre and the SRP
   check does not; `isValidPatternCenter` (2 tiles from every edge, and for SRPs all 25 tiles
   paintable); `markPattern` writes 25 markers and skips unpaintable tiles; the 25-paint charge on
   both mark paths; the map's `paintPatterns` field is read and ignored.
6. **`tests/test_bc25_srp.nim`** — `completeResourcePattern` legality (200 chips, valid centre, not
   already this team's centre, exact 25-tile match) and effect (registered at lifetime 0, chips
   deducted); the lifetime increments once per round in `updateResourcePatterns`; **the bonus starts at
   lifetime ≥ 50 and not at 49**; a broken pattern is dropped and its lifetime **reset to 0**, so
   repainting it restarts the 50-round clock; the bonus is `+3 × activeSRPs` per **mining tower**, not
   per team; and an enemy SRP centre on the same tile is a separate registration.
7. **`tests/test_bc25_penalties.nim`** — the end-of-turn bill: 1/2/0 by territory, ×2 for moppers,
   plus `n` (or `2n` on enemy ground) allied **units within r² ≤ 2 including towers**; exactly 0 paint
   costs 20 HP that same turn; a robot at 0 paint can neither move nor act but can disintegrate; a
   robot killed by the 20 HP is removed inside its own end-of-turn.
8. **`tests/test_bc25_comms.nim`** — robot↔tower only, never robot↔robot or tower↔tower; the r² ≤ 20
   range; the paint-connectivity BFS (4-neighbour, own colour only, refusing to start off own paint);
   the 1/20 per-turn caps; the 5-round buffer expiry at the start of a round; `broadcastMessage` to
   friendly towers within r² ≤ 80 with **no** connectivity requirement, counting one against the cap;
   the chassis's word packing round-trips for every kind.
9. **`tests/test_bc25_execorder.nim`** — the dynamic exec-order list: append on build, **by-value
   removal** on destroy preserving the order of the survivors, the pre-sweep snapshot so a unit built
   this round takes no turn this round, and the `existsRobot` skip for a unit destroyed mid-sweep.
   500 random build/destroy sequences replayed against the oracle's own list.
10. **`tests/test_bc25_endladder.nim`** — `paint_enough_area` fires mid-action (inside a splasher's
    AoE loop) and the round still finishes; `destroy_all_units` fires the moment a team's last **unit**
    (robot **or** tower) dies; `timeLimitReached` is `round >= 2000` so round 2000 **is** played; the
    five tiebreak rungs fire in the engine's order with a vector each; `coin_flip` is reachable and
    seeded from the world RNG; `RESIGNATION` is provably unreachable from any chassis.
11. **`tests/test_bc25_scoring.nim`** — the points formula with float32 narrowing and truncation, one
    vector per weight; the 0–0 `share` returning 0.5; points in `[0, 100]` and the seats summing to
    ≤ 100; a win on each of the five rungs comes with the winner's points strictly higher; and
    `results.scores` **strictly** orders the match winner above the loser on 500 random synthetic
    finals (which is what the 200-per-game bonus buys over bc24's 100).
12. **`tests/test_bc25_sheet.nim`** — every one of the ten knobs: absent → default, out of range →
    default + recorded, mistyped → default + recorded; `unit_mix` malformations (missing key, negative,
    non-object) take the **whole** default object and record once, and the clamps
    (`soldier ≥ 30`, `mopper ≥ 10`, `splasher ≥ 10`) then the normalisation to 100 are exact;
    `tower_type_order` malformations (short, long, duplicated, unknown value) take the **whole** default
    array and record once; unknown keys recorded (≤ 16, ≤ 40 runes); **a submitted `chassis` is recorded
    as an unknown field and never honoured** (the D1 assertion, which fails if anyone re-adds the knob);
    rune-boundary truncation of `notes`/`motto` including astral-plane characters; the 16 KB byte cap
    cut on a rune boundary.
13. **`tests/test_bc25_sensing.nim`** — vision r² ≤ 20 through walls; the engine scan order (x
    ascending outer, y ascending inner) for map infos, robots and AoE targets, asserted against a
    recorded oracle sweep; **only this team's markers are returned**; the precomputed `ceil(√r²)` table
    matches `Math.ceil(Math.sqrt(r²))` for every radius the rule set uses.
14. **`tests/test_bc25_maps.nim`** — every committed bc25 map re-converts identically from the pinned
    `.map25`; sizes, seeds, declared symmetry, wall counts, ruin counts and pre-painted counts match
    the table in §Sim module; every map is within 20…60 in both dimensions; the four initial bodies are
    two per team, one paint and one money, and they are **upgraded to level 2 with 500 paint** at world
    construction; the ruin list does **not** contain the four tower tiles and the world adds them; ruin
    centres are pairwise ≥ 5 apart (`MIN_RUIN_SPACING_SQUARED = 25`); no bc25 map name resolves to
    another year's map file; and **the seed the `docker-smoke` step passes draws exactly
    `DefaultSmall`** from the `small` pool, so the smoke's map cannot drift silently.
15. **`tests/test_bc25_survival.nim`** — the **competence gate** (the LEARNINGS pin), in the bc24
    shape, with an inverted control:
    - `spaark` vs `spaark`, all-defaults sheet, 3 seeds × 2 `small` maps = 6 games. In **≥ 5 of 6** the
      game must either reach round 2000 or end on `paint_enough_area` **after round 600** — nothing may
      collapse early, and a `destroy_all_units` before round 600 fails the gate outright. In **all 6**,
      each seat must have: built ≥ 8 robots; built ≥ 2 towers beyond its starting two; upgraded ≥ 1
      tower; finished at ≥ 12 % coverage; earned ≥ 4 000 chips; mined ≥ 3 000 paint; and spent
      ≤ 25 % of its robot-rounds at zero paint. **Across the two seats** there must be ≥ 1 SRP that
      completed **and stayed active for ≥ 50 rounds** — a bc25 game where nobody ever lands a resource
      pattern is not this game being played.
    - The same gate is then run as a **subprocess** against a **known-broken chassis** compiled behind
      `-d:bc25BrokenChassis` (a `spaark.nim` variant whose soldiers stop painting the tile under
      themselves, so the clan bleeds paint on neutral ground and starves) and **must come back red**.
      A gate that cannot fail is not a gate; this assertion is what keeps it honest, and it is the
      direct answer to the 2026-09-03 finding that mechanical episode checks pass degenerate matches.
    - **The thresholds above are the design floor, not the committed numbers.** bc24's own gate had to
      be re-tuned because the note's pre-economy guesses would have let the broken control pass. Phase
      20 **measures** a healthy mirror and the broken control, sets the committed thresholds between
      them with margin (and never below this note's floor), and records **both** measured ranges in the
      test's header comment — exactly as `tests/test_bc24_survival.nim` does today.
16. **`tests/test_bc25_knobs.nim`** — the knob-teeth gate. Paired seeded games (identical seed, map and
    opponent; the two clans identical except one knob at its low and high setting, 3 seeds each), each
    asserting a named, signed delta. Thresholds live in one table so tuning is a one-line change, and
    the header records every substituted statistic (the bc21 r1-F6 fix):

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `tower_rush` → `paint_eco` | robots built by round 400 up ≥ 40 % **and** towers built by round 400 down ≥ 2 |
    | `unit_mix` | `{80,10,10}` → `{30,10,60}` | splashers built up ≥ 3× **and** tiles overpainted up ≥ 200 |
    | `srp_priority` | 0 → 100 | SRPs completed up ≥ 2 **and** chips spent on towers down ≥ 25 % |
    | `tower_type_order` | `[money,paint,defense]` → `[paint,money,defense]` | paint towers at round 1000 up ≥ 2 **and** chips at round 1000 down ≥ 300 |
    | `ruin_claim_radius` | 4 → 20 | mean distance from a claimed ruin to the clan's start up ≥ 50 % **and** towers built up ≥ 1 |
    | `defense_tower_chokes` | `never` → `early` | defense towers built up ≥ 2 **and** enemy robots killed by towers up ≥ 20 % |
    | `paint_reserve_floor` | 10 → 70 | robot-rounds at zero paint down ≥ 60 % **and** tiles painted down ≥ 10 % |
    | `mop_enemy_paint` | 0 → 100 | enemy tiles mopped up ≥ 150 **and** paint transferred to allies down ≥ 50 % |
    | `splash_targets` | `territory` → `towers` | damage dealt to enemy towers up ≥ 40 % **and** tiles painted by splashers down ≥ 30 % |
    | `upgrade_policy` | `never` → `money_first` | towers upgraded up ≥ 3 **and** chips earned by round 1500 up ≥ 15 % |

17. **`tests/test_bc25_baselines.nim`** — bounded orders and legality:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the *same* `validate` the LLM
      path uses;
    - (b) in played games, **every action either chassis emits is legal for the acting unit at the
      moment it is emitted**: the right cooldown counter under 10 and paint above 0, the target in the
      right radius, on the map, of the right team, the chips and paint actually present, no robot
      painting over enemy paint, no mopper attacking a ruin or wall, no tower moving, no
      `completeTowerPattern` over the 25-tower cap, no message across an unpainted gap; and **no unit
      exceeds its `DecisionOps` budget**;
    - (c) `examplefuncsplayer25` **acts** — ≥ 1 robot built, ≥ 1 tile painted, ≥ 1 mop swing — but is
      **not** required to survive or to compete: it is the deliberate weak floor and the oracle's other
      side, and it may not gain behaviour;
    - (d) `spaark` beats `examplefuncsplayer25` on 3 seeds × 2 `small` maps, 6/6.
18. **`tests/test_bc25_perf.nim`** — a full 2000-round game on `DefaultLarge` (50×30) with both seats on
    `opening: tower_rush`, `srp_priority: 100`, `defense_tower_chokes: early` in **≤ 90 s**; failing it
    means switching `gamesPerMatch` to 1 (§The game).
19. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain, twice
    in one process and across a save/load; and **record → re-derive for every bc25 end reason**
    (`paint_enough_area`, `destroy_all_units`, all five tiebreak rungs, `coin_flip`, and the wall-clock
    `abandoned`/`deadline` stop applied by the same proc on both paths).
20. **`tests/test_bc25_replay.nim`** — a bc25 replay document round-trips; a **strict UTF-8 parse** of
    the written bytes; the viewer's re-derivation of a recorded bc25 match reproduces the recorded
    per-round hashes; paint, markers, towers, SRPs and chips re-derive identically from events + config
    + seed with nothing stored; and **every event kind respects its per-game bound** from the table in
    §Server, player, protocol.
21. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now five years wide: the
    results key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; `num_agents` present in **all five** variants' `game_config` and
    in `certification.game_config`, and **absent** at every variant top level;
    `config_schema.year.enum == ["bc26","bc20","bc21","bc24","bc25"]`; **`player[]` contains exactly the
    ids in `certification.players`** and
    `len(certification.players) == certification.game_config.num_agents` (the pair of checks that would
    have caught the bc20 release failure); every `config_schema` array bounded; `tokens` declared and
    required but never valued in a `game_config`; both `game.protocols` keys and `game.docs.readme` plus
    **all seven** `pages` are `{type,value}` objects; and the installed `coworld` CLI's own
    `validate_upload_manifest` / `_load_template_manifest` accepts the template.
22. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc25** fixture replay;
    the bc25 game block shadows no `ChromeCommon` alias and no other year's game-block name (the tandem
    scar); `chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256; the
    page carries CSS for **all eleven** emitted bc25 beat kinds, every one scoped to
    `html[data-year="bc25"]`; `#bc25-doctrines` carries a dismiss control and sits outside `var(--band)`;
    and `relayout()`'s `--statrail` measurement set names `bc25-towers` and `bc25-econ`.
23. **`tests/test_constants.nim` (extended)** — `tools/gen_year_constants.py --year bc25 --check`
    regenerates `years/bc25/constants.nim` from the pinned sources and byte-diffs it, and
    `tools/convert_maps_bc25.py --engine … --check` re-converts all 22 committed maps and byte-diffs
    them, plus `--parse-all` reads **all 75** official `.map25` files with the converter's own vtable
    walk (a reader that only works on the maps we ship is a reader nobody can extend the pool with).

### `parity-oracle-bc25` job — the 2025 engine as a CI-only oracle

**This year's oracle is the cheapest of the series after bc24's, and the recipe below was EXECUTED in
the sandbox rather than guessed.** The released fat jar
`https://releases.battlecode.org/maven/org/battlecode/battlecode25-java/3.1.0/battlecode25-java-3.1.0.jar`
(HTTP 200, **9 223 721 bytes**, sha256
`d0cc775610d5221fc17b23d818bc881bb3e882076a809696d15f8d380b09520b`, pinned in
`tools/oracle/bc25/jar.lock`) is **self-contained**: 6 413 entries, all 182 `battlecode` classes,
every bundled dependency (`net.sf.jsi`, `gnu.trove`, `org.apache.commons.lang3` among them, so the
dead-artifact problem that shaped the bc20 and bc21 jobs does not arise), `MethodCosts.txt`, and all
**75** `.map25` map resources. So there is **no Gradle, no jsi shim, no multi-file `javac`, no Maven
Central download list and no `deps.lock`** in this job. It is:

1. `actions/setup-java@v4`, `distribution: temurin`, `java-version: **"21"**`. The engine's
   `build.gradle` sets `sourceCompatibility = VERSION_21` and hard-fails below it, and the
   instrumenter uses **ASM 9.7.1**, which is happy with class-file version 65. **Compile with plain
   `javac -nowarn -encoding UTF-8 -cp <jar>` and no `--release`, no `-source`, no `-target`** — the
   JDK and the engine target the same version, so the bc21 lesson ("match javac flags to the JDK") is
   discharged by using none at all. `-source 8` here would be as wrong as `--release 8` was there.
2. Download the jar and **verify its sha256** against `jar.lock`. **Do not assert a version string**:
   `GameConstants.SPEC_VERSION` in the 2025 sources is the literal `"1"`, not `"3.1.0"`, so bc24's
   `test "${spec}" = "3.0.5"` step has no bc25 equivalent. The sha256 *is* the version pin, and Tier B
   cross-checks the constants instead.
3. **`--add-opens=java.base/jdk.internal.misc=ALL-UNNAMED` is MANDATORY on every `java` invocation.**
   This was discovered by running it, and it is the exact "green oracle proving nothing" trap: without
   the flag, the instrumented `java.util.Random` class fails its static initialiser with
   `IllegalAccessError: class instrumented.java.util.Random … cannot access class
   jdk.internal.misc.Unsafe`, **every player class load throws, all four starting towers die by
   exception on round 1, and the game ends at round 1 with `DESTROY_ALL_UNITS` and a four-line trace**.
   The job exits 0 and the diff is empty. `tools/oracle/bc25/Bc25Trace.java` therefore **fails loudly
   (exit 3) if no robot is ever built**, and `ci.yml` additionally asserts every game reached at least
   1 900 rounds.
4. Run `java -Xmx2g -XX:+UseSerialGC --add-opens=java.base/jdk.internal.misc=ALL-UNNAMED
   -cp battlecode25-java-3.1.0.jar:classes battlecode.world.Bc25Trace <map> <rounds> <pkg>
   <classesDir>`. The driver is `package battlecode.world;` so it needs no reflection except for
   `ObjectInfo.dynamicBodyExecOrder` (private, and reading it is the only way to print in exec order):
   it loads the map with `GameMapIO.loadMapAsResource(loader, "battlecode/world/resources", map,
   false)`, builds a `TeamControlProvider` over two `PlayerControlProvider`s (**the player URL must be
   the compiled classes directory** — an empty URL fails class loading and the world constructor NPEs),
   constructs `new GameMaker(info, null, false)` (the null packet sink is explicitly supported) and
   calls `GameWorld.runRound()` in a loop, printing the trace **from the live objects**. **No
   flatbuffers reader, no `flatc`, no `pip install` on either side**, and the engine is used exactly as
   published.

**The trace.** One line per record; `tools/parity_trace_bc25.nim` prints the same lines from the Nim
port:

```
R <round> T <A|B> money=<n> painted=<n> towers=<n> bots=<n> paintunits=<n> srp=<n>
R <round> M chk=<fnv1a64 of the colour array, y asc outer, x asc inner> mk=<fnv1a64 of both marker arrays>
R <round> P <centerIdx> team=<A|B> life=<n>
R <round> U <id> team=<A|B> ty=<UnitType> x=<n> y=<n> hp=<n> pnt=<n> acd=<n> mcd=<n> ra=<n> bc=<n>
R <round> W winner=<A|B|-> dom=<NAME|->
```

Units are printed **in exec order**, not id order, which is what makes an ordering bug visible; the
paint checksum is what makes a single mispainted tile visible without printing 3 600 tiles a round.
The Java side's `bc=` column is stripped before the diff (there is no bytecode counter on the Nim
side) and is used only for the Tier A headroom assertion. **Measured in this sandbox** (the `T`, `M`,
`U` and `W` lines exactly as above; `P` and `mk=` are the shipped driver's additions): a full
2000-round game is **38 010–51 381 trace lines (3.0–4.0 MB)** and **5.1–7.0 s of JVM** per map, so
eighteen pairs cost roughly two minutes of engine time. Traces are written to `$RUNNER_TEMP`, compared
streaming, and only the first 200 divergent lines plus a gzipped digest are uploaded.

**The tiers — pinned to what this harness can actually deliver, which was measured, not hoped.**

- **Tier A (BLOCKING) — rounds 1…2000 bit-exact, whole games, on six `small` pairs**
  (`DefaultSmall`, `CastleDefense`, `Paintball`, `Justice`, `Filter`, `Jail`),
  `examplefuncsplayer25` against itself, every field above. This is a *whole-game* window for one
  measured reason: the 2025 example bot **never approaches its bytecode limit** — peak use across
  eight full games was **2 460–2 622, i.e. 14.1–15.0 % of 17 500**, with **zero** mid-turn cut-offs —
  so the port's "no mid-turn resumption" divergence is never exercised and the comparison stays
  defined to the last round. The job does not assume that: it reads the `bc=` column and **fails if
  any unit on any round exceeds 50 % of its type's limit**, naming the round and the unit, because past
  that point the window would have to shrink and the note would rather be wrong loudly than green
  quietly.
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact.** Tier A's own measurement showed
  exactly what it cannot cover. Over eight full 2000-round games the example bot **never built a
  defense tower, never built a splasher (the branch is commented out upstream), never upgraded a
  tower, never completed a single resource pattern, never sent a message, and ended every one of the
  eight games on `MORE_SQUARES_PAINTED` at round 2000 with coverage between 9 % and 14 %** — so
  `paint_enough_area`, `destroy_all_units`, the four deeper tiebreak rungs, the SRP lifecycle, the
  25-tower cap, the defense buff and the whole comms subsystem are untested by it. Those are precisely
  the "rare code paths that fire mid-game" the Fleet card 1218171523823317 postmortem warns about. So
  this job runs a **second oracle bot of our own**, `tools/oracle/bc25/bc25scenario/RobotPlayer.java`,
  written to be (a) deterministic with **no RNG at all**, (b) cheap — the job asserts it never exceeds
  **25 %** of its bytecode limit, so it can never be cut off mid-turn — and (c) **scripted by round
  number to force every rare path early**: build all three tower types on ruins and upgrade one of each
  to L2 and then L3; build all three robot types; complete an SRP, hold it 60 rounds so it activates,
  then deliberately mop one of its tiles so it deactivates and its lifetime resets; splash over enemy
  paint and over a tower; mop-swing in all four cardinal directions; drive a robot to exactly 0 paint
  and let it take 20 HP a turn until it dies; drain a tower's paint stash so it cannot build; send a
  robot→tower message across paint, then break the paint and prove the send is refused; broadcast
  tower→tower across an unpainted gap; disintegrate one robot; and, on the `bc25scenariopaint`
  variant, paint one small map past **70 %** so `PAINT_ENOUGH_AREA` fires, while the
  `bc25scenariowipe` variant kills every enemy unit so `DESTROY_ALL_UNITS` fires. `scenario25.nim` is
  its Nim twin, written line for line against it, behind `-d:bc25Scenario` (+`-d:bc25ScenarioPaint` /
  `-d:bc25ScenarioWipe`). Both sides run all three variants on all six pairs and must agree **bit for
  bit for the whole game**. The job then asserts, **off the JAVA trace**, that the paths really fired:
  a `LEVEL_THREE_*` of each type appears; `srp=1` appears and later returns to 0; a `W` line with
  `dom=PAINT_ENOUGH_AREA` and one with `dom=DESTROY_ALL_UNITS` exist; a robot record with `pnt=0`
  appears in consecutive rounds with falling `hp`; and the marker checksum changes. **A scenario bot
  that agrees bit for bit while doing nothing proves nothing**, and this is the step that stops it.
  *(If the engine's own instrumentation makes any one of these scripted paths impossible to force
  deterministically, the failing item is dropped from the scenario bot and **added to
  `docs/PARITY.md` §What is NOT compared with the reason** — never silently left in a bot that does
  not reach it.)*
- **Tier B (BLOCKING) — the arithmetic, over its whole finite domain.** `tools/JavaBc25Tables.java`,
  run against the jar's own classes under the CI JDK 21, regenerates `data/bc25/tables.json` — the
  whole `UnitType` table (13 fields × 12 types); the paint-percentage function
  `round(paint × 100.0 / capacity)` for **every** `(paint, capacity)` pair over the three robot
  capacities and 1000 for towers; the cooldown surcharge for every paint percentage 0…100 × every base
  cooldown in the rule set `{10, 20, 30, 50}` plus the movement 10; the coverage per mille
  `round(painted × 1000.0 / areaWithoutWalls)` over every `areaWithoutWalls` a 20…60 map can have and
  every painted count that matters at the 70 % boundary; and the four pattern bit tables — and the job
  **byte-diffs** it against the committed file. bc25 has **no transcendental anywhere and no float32
  anywhere**, so unlike bc21 this tier is not a sample: it is the entire domain. The same step
  cross-checks every `GameConstants` field against the **jar's** classes, which is what closes the
  "released jar versus pinned master sources" gap in the absence of a usable `SPEC_VERSION`
  (`docs/RULES-BC25.md` §Divergences item 12).
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 2000-round game, on
  all four bots and all six maps.** The job computes it per pair and compares it against
  `tools/ci/parity_ledger_bc25.json`, whose entries are
  `{"bot": "...", "map": "...", "first_divergent_round": N, "cause": "<one sentence>",
  "docs": "PARITY.md#<anchor>"}`. It **fails** if (a) a pair diverges and has no ledger entry, (b) a
  pair diverges **earlier** than its entry, (c) a ledger entry no longer reproduces (a stale excuse is
  as bad as a missing one), or (d) **any** divergence occurs while the traced bytecode peak is still
  under 50 % — which, on this year's evidence, means always, and therefore means a real rules bug
  rather than an instrumentation artefact.

**Root-cause-or-fail is the standing rule, and it is the operator's ruling on the bc26 run (Fleet card
1218171523823317), not this note's preference.** An unexplained Tier C divergence is a **FAIL**, not a
ledger line. Every ledger entry must name a round, a map and a *root cause*; a cause of "unknown" is
not a cause and the ledger schema rejects it. What this note commits to is what the evidence supports:
**the phase-30 exit condition is that Tiers A, A′ and B pass with an EMPTY ledger**, because the
measurement above says nothing in this harness forces a divergence. If phase 30 finds one anyway, the
budget for root-causing it is stated here — the **root-cause checklist**, each item with its own unit
test above, so a Tier C failure bisects in minutes rather than becoming a card:

the dynamic exec-order list's by-value removal and the pre-sweep snapshot (test 9); the splasher's
scan order and its two radii (test 3); the mopper's "bare, not ours" rule and the six swing offsets
(test 3); the cooldown surcharge's int×int-then-`/100.0` shape and the pre-cost-versus-post-transfer
ordering (test 1); the end-of-turn bill including **towers in the crowding count** (test 7); the
70 % denominator and the mid-action win (test 2); the tower upgrade's damage carry and the defense
buff ledger on build, upgrade and destroy (test 4); the SRP lifetime reset on break and the ≥ 50
threshold (test 6); the pattern centre skip and the validity box (test 5); paint connectivity refusing
to start off own paint (test 8); and the `IDGenerator` stream that fixes every built unit's id
(`tests/test_rng.nim`).

Tiers A, A′, B and C are the **phase-30 gate**. Every accepted divergence is listed in
`docs/RULES-BC25.md` §Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md`
gains a `bc25` section written in the same shape as the `bc24` one — including, honestly, the measured
numbers (peak bytecode %, cut-offs, trace line counts, JVM seconds, and the `--add-opens` trap).

### `docker-smoke` job — now **five** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely
from `certification.game_config.num_agents` and hard-fails with `SEAT-COUNT FAIL:` if the workflow's
`<SEATS>` = **2** disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes —
bad-token refusal, `/global` first frame on connect, `Ping → Pong` payload echo — against the real
image on the first episode):

1. **The bc26 certification-fixture episode**, unchanged → `dist/smoke/replay.json`.
2. **The bc20 episode**, unchanged → `dist/smoke/replay-bc20.json`.
3. **The bc21 episode**, unchanged → `dist/smoke/replay-bc21.json`.
4. **The bc24 episode**, unchanged → `dist/smoke/replay-bc24.json`.
5. **A bc25 episode**, new: `SMOKE_EXPECT_YEAR=bc25`, `SMOKE_PLAYER_IDS=awu,scaffold`,
   `SMOKE_CONTRACT_PROBE=0`, `SMOKE_REPLAY_OUT=dist/smoke/replay-bc25.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc25","pool":"small","seed":<the seed test 14 pins>,
   "gamesPerMatch":1,"maxRounds":600,"perGameBudgetSeconds":60,"matchBudgetSeconds":70,
   "connectTimeoutMs":15000}`. **600 rounds**: long enough that at the default pace the replay records
   ~25 s of playback and therefore outlasts the viewer smoke's 15 s soak (the ecos 2026-08-23 scar),
   and long enough that the strong chassis has built and upgraded towers. The seed is pinned to draw
   `DefaultSmall`, the smallest map in the pool, so the episode is fast and the map cannot drift.

All five run one game container + two player containers on a shared network with `file://` artifact
URIs and **no** `ANTHROPIC_API_KEY`, so both seats take the scripted path and must still complete. All
five assert: the game exits 0, **every player container exits 0**, `results.json` carries exactly the
expected key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`, and the replay
parses as **strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the right `year`, and a
non-empty `events` array. A step asserts all five replays exist and report five different `year`
values.

**The episode substance assertion (the LEARNINGS pin), in two parts.** The bc25 episode passes
`SMOKE_REQUIRE_STATS` — the **per-seat** floor, which the script already enforces for both seats — with
`{"robots_built":4,"tiles_painted":150,"chips_spent":500,"paint_spent":400}`. Those four are things
*both* chassis do, including the weak floor: the upstream example bot builds robots from round 1 and
paints under itself every turn. **Three signatures of the year are things only a seat playing well
does** — building a tower beyond the starting two, upgrading one, and landing a resource pattern — so
asserting them per-seat would be asserting that the weak floor is not weak. They are asserted
**across the pair** by one `jq` step in `ci.yml`, reading the **replay's** `result` block (not
`dist/smoke/results.json`, which every episode overwrites in turn — the bc24 fix):
`([.result.games[0].towers_built[]] | add) >= 1` and
`([.result.games[0].towers_upgraded[]] | add) >= 1` and
`([.result.games[0].squares_painted[]] | add) >= 200`. Together they make an idle win
machine-visible, which is exactly what the 2026-09-03 round-1 degenerate match lacked.

**And the floors are measured, not guessed.** The numbers above are a lower bound derived from the
Java example-bot mirror measured in this sandbox (which, over whole games, builds 20–29 units and
paints 46–218 tiles a side). Phase 20 runs the real bc25 smoke once, reads the actual per-seat
statistics out of `dist/smoke/replay-bc25.json`, and sets the committed floors at roughly half the
weak seat's measured value — never below this note's numbers — recording the measurement in a comment
beside the step, exactly as the bc24 fix (`fa5083a`) did.

### `wasm-viewer` job — the bundle is **executed**, against **all five** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay>
--killfeed-overlap` in headless chromium (Playwright pinned 1.55.0) **once per replay** —
`replay.json`, `replay-bc20.json`, `replay-bc21.json` at `--timeout 90 --soak 10`, and
`replay-bc24.json` **and `replay-bc25.json`** at **`--timeout 120 --soak 15`** for the pacing reason in
§Viewer. Each run requires `data-replay-loaded="true"` (or the bridge `ready` posted after it), three
**differing** clock/scorebug readouts at 0 % / 50 % / 100 %, continued advancement across the soak,
`scrub_selector == "#scrub"` (so a seek was really exercised and the `#viewpanel` zoom slider was not
clicked instead), `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line, no overlay
covering more than 50 % of the board after the soak, and the `#killfeed`/stat-box overlap check at
360 px, 720 px and 1280 px at both FIT and 2× zoom. `--strict-text-bounds` stays deliberately dropped
here because the board is pannable and zoomable (`#viewpanel` is kept), which is the exact case the
flag's own documentation excludes; the `canvas_text` counts are still recorded in `viewer-smoke.json`,
and the separate `tools/ci/renderer_fixture.html` step — full-cap `notes` and `motto` on both seats at
three widths including **360 px**, in the page's own CSS extracted from `client/replay_broadcast.html`
at run time — runs through the same harness with `--strict-text-bounds`, because every CI replay is
scripted and carries no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a bc25 row.
`node tools/wasm_replay_smoke.cjs` is also run against the bc25 smoke replay **and** the committed
`tests/fixtures/replay-bc25.json`, so wasm32-only failures (int overflow traps, address-space
exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation of
  anything a cog sends. The 2025 engine exists only in the `parity-oracle-bc25` CI job, and only as the
  published jar.
- **Full bytecode metering.** The 1 750/2 000-`DecisionOps` budget replaces it, with no mid-turn
  resumption and no mid-primitive cut. A Nim-level instrumenter is a compiler project and buys nothing
  the oracle does not already prove — and on this year's measurement the oracle never reaches 15 % of
  the boundary.
- **A cog-authored Java (or any) strategy class.** Doctrines are **JSON-sheet only**; there is no
  `javac`, no instrumenter `Verifier`, no compile-error round trip and no multi-attempt loop. Nothing
  in the schema is closed against a future sandboxed hook.
- **A bc25 certification fixture, and any new `player[]` entry.** Certification stays on bc26 and
  `player[]` stays at `awu` + `scaffold`. bc25 is proven by its own `docker-smoke` episode and the
  viewer smoke run against that episode's replay.
- **53 of the 75 official maps.** The converter handles any `.map25`; v1 commits the 22 whose sizes,
  seeds, symmetry, terrain and ruin counts are pinned in this note. The eight maps with zero
  pre-painted tiles and everything above 1 500 tiles are excluded on purpose, for the reasons in §Sim
  module.
- **The official 2025 TypeScript client, and `.map25`/replay flatbuffers in the browser.** Its
  *sprites* and *colour table* are reused (credited, GPL-3.0 per `client/package.json`); its app is not
  shipped, not embedded and not built. There is no flatbuffers library on either side of this port —
  the map converter is a hand-written vtable walk — and no `match_b64` field exists.
- **Worker-side keyframe checkpoints in the viewer.** bc25 seeks re-simulate from the start of the game
  like every other year, which is why check 8 is dispatched with `settle=20000`. Keyframes are the
  obvious next optimisation for a heavy year module and they are deliberately not in v1.
- **A cog-authored comms protocol.** The 32-bit message word format is the chassis's; a doctrine cannot
  redefine it. The knobs steer what gets said, not the encoding.
- **Per-robot fog in the viewer.** The spectator sees the true board, with the single deliberate
  exception of **enemy markers**, which are per-team state and are never drawn.
- **Secondary-colour strategy as a doctrine surface.** The engine distinguishes primary and secondary
  paint *only* when checking a pattern; territory, scoring and the 70 % win treat them identically. The
  chassis therefore uses secondary paint exclusively where a pattern asks for it, and no knob exposes
  the choice. A future year module could make it a bluffing surface; this one does not.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the war.
- **Battlecode years other than 2026, 2020, 2021, 2024 and 2025.** The registry, `game_config.year`,
  the variant naming and `years/dispatch.nim` all support more; only these five are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. The four places where the
spec's prose and the engine disagree — the 70 % denominator, the radius-versus-squared-radius column,
the clumping penalty counting towers, and the "1 paint to mark" the engine never charges — are all
resolved **against the pinned engine** in §The game and recorded as divergences from the prose, not as
open questions. The two places where the engine itself is ambiguous — `RESIGNATION` being reachable
through an API no doctrine can call, and `SPEC_VERSION` being the useless string `"1"` — are resolved
in §The game and §Tests and recorded in `docs/RULES-BC25.md`.)*
