# cogame-battlecode — the `bc23` year module: Battlecode 2023 "Tempest" (design note, 2026-09-08)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a branch/PR of
the shipped repo that adds the year module `bc23` beside the shipped `bc26`, `bc20`, `bc21`, `bc24`
and `bc25`, adds the manifest variant `bc23`, keeps certification on `bc26`, and bumps the version of
the *same* coworld. **There is no `cogame-battlecode-2023` repo and none is created.** The starter is
chosen by game shape and it is the only defensible one: bc23 is the same shape as the five shipped
years — a deterministic Nim grid sim compiled twice (native for the server, wasm for the viewer), one
sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm replay viewer that
re-derives every frame — and the year-module boundary (`src/battlecode/years/<year>/`,
`years/registry.nim`, `years/dispatch.nim`, `game_config.year`) already exists and has now been
proved **four** times, by bc20, bc21, bc24 and bc25. Lineage: `coworld-ctf` (paintbot) →
`cogame-battlecode` → this. The starter is `Metta-AI/cogame-battlecode`, and **every convention there
holds here unless this note says otherwise**: the Nim sim/server/player layout, `nimby.lock`, the
bitworld runtime contract, the `GameVersion` discipline, `tools/build_replay_viewer.sh`, the
`replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch doctrine layer (`llm.nim` /
`decide.nim` / `sheet.nim` / `sheet_common.nim` / `baselines.nim`), the closed results document, and
"degrade, never hang".

This note lands in the repo as `docs/plans/2026-09-08-battlecode-2023-design.md` on the branch
`bc23-year-module`. The copy of record for the run is
`runs/2026-09-08-battlecode-2023/design.md`.

### Provenance — every rule below was read or measured, not assumed

**The 2023 rules were read from `github.com/battlecode/battlecode23` at commit
`af42086ecd09709dc603b2aaa9e9b98312c9ef79`** (`master`, last commit 2023-02-05):
`engine/src/main/battlecode/common/GameConstants.java`, `common/RobotType.java`, `common/Anchor.java`,
`common/ResourceType.java`, `common/Direction.java`, `common/MapLocation.java`, `common/Team.java`,
`world/GameWorld.java`, `world/InternalRobot.java`, `world/robots/InternalCarrier.java`,
`world/RobotControllerImpl.java`, `world/TeamInfo.java`, `world/Island.java`, `world/Well.java`,
`world/Inventory.java`, `world/ObjectInfo.java`, `world/IDGenerator.java`, `world/LiveMap.java`,
`world/GameMapIO.java`, `world/DominationFactor.java`, `world/control/PlayerControlProvider.java`,
`schema/battlecode.fbs`, `build.gradle`, `gradle/wrapper/gradle-wrapper.properties`,
`client/package.json`, `client/LICENSE`, `engine/COPYING`, `schema/LICENSE`, and
`example-bots/src/main/examplefuncsplayer/RobotPlayer.java`.

**The oracle recipe in §Tests was EXECUTED in this sandbox, not guessed.** Temurin **8**
(`8u504-b01`) + the released `battlecode23-3.0.15.jar` + one 120-line driver file
(`Bc23Trace.java`, the bc25 driver one year back) runs whole **2000-round** headless games in
**26.5–31.1 s each**, and every number quoted below — peak bytecode use, trace line counts, JVM
seconds, unit counts, end reasons, map geometry — is a measurement off those runs. It also found the
two traps that would otherwise each have cost a CI round (§Tests, `parity-oracle-bc23`: the JDK-21
ASM failure and the non-daemon player threads). **All 103 official `.map23` resources were parsed**
for their real sizes, seeds, declared symmetry, wall/cloud/current counts, island counts and areas,
well counts and headquarters counts; the pool table in §Sim module is those measurements.

Base-repo facts are from `Metta-AI/cogame-battlecode` at **`6885a066`** (`main`, the last bc25 fixer
commit), whose shipped coworld version is **0.5.0** and whose `GameVersion` is **GV08**. Every
`file:line` and constant below is to those two trees.

### Source idea (verbatim)

```
Sky islands: HEADQUARTERS build CARRIERS (mine adamantium/mana/elixir from wells, carry anchors), LAUNCHERS (the only real attacker), AMPLIFIERS, DESTABILIZERS and BOOSTERS; win by anchoring 75% of the sky islands, else tiebreaks at round 2000, with currents and clouds shaping the map. The ranking's canonical NARROW meta: 'whichever team won the beginning launcher duel won the match' and the whole elixir tech tree went unused. That is exactly why it is worth having as a doctrine game with a real oracle: the sheet can make elixir/anchor economies a deliberate choice and the league will show whether launcher-rush really is uncounterable when doctrines are sealed.

Seats: 2 (one cog per side). num_agents = 2 in the bc23 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc23 (v1 candidates; the builder finalises them from the chassis it ports): opening {launcher_rush | carrier_eco | balanced}, launcher_ratio, well_priority {adamantium | mana | elixir}, elixir_tech {never | mid | early}, anchor_round, island_priority, amplifier_use, destabilizer_use, retreat_on_launcher_loss.
Rules, engine, oracle: Spec: https://releases.battlecode.org/specs/battlecode23/3.0.15/specs.md.html (200). Engine: https://github.com/battlecode/battlecode23 (Java 8, Gradle 7.6, engine/COPYING AGPL-3.0). Oracle jar: https://releases.battlecode.org/maven/org/battlecode/battlecode23/3.0.15/battlecode23-3.0.15.jar (200).
Chassis and baselines (behaviour sources): awesomelemonade/Battlecode2023 (Producing Perfection, 1st, AGPL-3.0), vrangr1/BattleCode2023 (4th, AGPL-3.0), jmerle/battlecode-2023 (9th-12th, MIT). 'don't @ me' (7th) and '4 Musketeers' (3rd) not found on GitHub.
Ranking: Tier 3 (narrow, patch-nudged) in the ranking.
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc23` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc23` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc23`, league_name `Battlecode 2023 — Tempest`, default_variant_id `bc23`, short_name `bc23` (softmax.com/battlecode/bc23), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin from the brief and the idea is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; **one new year module `src/battlecode/years/bc23/` + manifest variant `bc23`**; everything else on `main` untouched; branch `bc23-year-module`, PR-then-merge | this paragraph, §Packaging ("Branch discipline", "Variants") |
| `num_agents = 2` in `variants[bc23].game_config`; all other variants and the bc26 cert fixture unchanged; the `<SEATS>` = 2 cross-check | §The game ("Seats"), §Packaging ("Variants", "The `<SEATS>` cross-check") |
| `GameVersion` **GV08 → GV09** with a bc23 headline; `ReplayCompatibleGameVersions` EXTENDED, never reset | §Sim module ("Determinism"), §Packaging ("Version bump semantics") |
| Coworld version **0.5.0 → 0.6.0**; certification stays bc26; manifest `player[]` UNCHANGED | §Packaging ("Version bump semantics", "`player[]` — UNCHANGED") |
| Sealed one-shot doctrine, ONE parallel batch of 2 LLM calls, `doctrineBudgetMs = 45000`, worst case inside 60 % of `episodeTimeoutSeconds` | §The game ("Match shape and budget"), §Decisions |
| Degrade-never-hang: retry once → verbatim fallback sheet + a `doctrine_fallback` event | §Decisions ("Degrade-never-hang") |
| **No inert chassis**; competence gate with the `-d:bc23BrokenChassis` NEGATIVE CONTROL; economic-survival shape | §Decisions ("the anti-inert rule"), §Tests items 16, 17 |
| Parity oracle: Java **8** in CI only, Tiers A/A′/B/C, **root-cause-or-fail**, tiers pinned to what the harness delivers | §Tests (`parity-oracle-bc23`) |
| Fixed per-robot decision budget instead of bytecode metering (documented divergence) | §Sim module ("The chassis, and the bytecode divergence"), §Packaging (`docs/RULES-BC23.md` §Divergences) |
| The year's maps converted at build time; symmetric seeded maps; official client sprites, credited | §Sim module ("Maps"), §Viewer ("Art"), §Packaging ("Licensing") |
| Viewer: static wasm, all four files from `cogame-battlecode`, chrome byte-for-byte, appended block, transport rules, **beats emitted + labelled + styled**, zoom decision | §Viewer |
| Replay self-sufficient; `result` singular; best-of-N clinch semantics | §Server, player, protocol ("Replay"), §The game ("End conditions") |
| Exact signed scoring formula with the wins-dominate property proved; the league ranks by `results.scores` | §The game ("Scoring") |
| Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side) | §The game, §Viewer |
| 2 LLM champions + 2 scripted fillers, same image, env-switched; champion 2 carries `daveey-1`'s `player` id | §Decisions, §Packaging (`tools/ci/policies.json`) |
| Tests: native units, e2e docker-smoke with per-seat substance floors, strict UTF-8 parse, executed viewer smoke, competence gate + negative control, parity jobs, cert probe | §Tests |
| Phase-50 league `bc23` / `Battlecode 2023 — Tempest` / `default_variant_id bc23` / `short_name bc23`, own champions, fillers and credit pool | §Packaging ("The phase-50 plan") |
| `## Out of scope (v1)` non-empty; prose-vs-engine conflicts resolved against the pinned engine; **no `OPEN` section** | §Out of scope (v1) |

### Interface facts this note is written against (read from `6885a066`, not assumed)

- **D1 — the chassis is not an LLM-selectable knob.** A submitted `chassis` is recorded in
  `sheet_unknown_fields` and ignored (`src/battlecode/sheet.nim`; `sim_types.nim` GV04 entry).
  **The bc23 sheet has no `chassis` key** and `tests/test_bc23_sheet.nim` asserts the D1 behaviour.
- **D2 — the scripted baseline plays, and CI gates on substance.** bc23's strong baseline
  (`lemonade`) is a real bot; the gate is competence + positive play counters, not a win
  (§Tests items 16, 17 and the `docker-smoke` substance assertion).
- **D3 — the doctrine overlay must be dismissible.** `#bc23-doctrines` ships with a close control, an
  `Escape` binding, a re-open chip and self-dismissal on the first advance; it never sits in the
  transport band (§Viewer).
- **The manifest declares exactly the two players the certification fixture seats.** `player[]` is
  `awu` and `scaffold` and **nothing else** (`coworld_manifest_template.json` at `6885a066`);
  `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim` (`defaultBaselineFor` /
  `baselineFor`, both already five-armed). The bc20 run lost a release dispatch (`players_missing`)
  by adding year-specific `player[]` entries that occupied no cert slot. **This run adds no `player[]`
  entry** — see the explicit cross-check in §Packaging.
- **`GameVersion` is `GV08`** and `ReplayCompatibleGameVersions` is
  `["GV04","GV05","GV06","GV07", GameVersion]` (`src/battlecode/sim_types.nim:16,129`). This run
  **extends** that list; it does not reset it. `tools/ci/check_gameversion.sh` compares the *headline*,
  not the digits, so a sibling branch that takes GV09 first forces this branch to GV10 — expected and
  handled (§Packaging).
- **`ScriptedChassis`** is the year-neutral chassis enum in `sim_types.nim` (currently `scAwu,
  scScaffold, scBowlOfChowder, scExamplefuncsplayer, scCaliforniaRoll, scExamplefuncsplayer21,
  scGoneSharkin, scExamplefuncsplayer24, scSpaark, scExamplefuncsplayer25`); bc23 adds two values, and
  each year's `newSession` already falls back to **that year's strong chassis** for a name belonging to
  another year.
- **`relayout()`'s `--statrail` set already exists** and currently names `econ`, `bc20-soup`,
  `bc20-units`, `bc21-influence`, `bc21-units`, `bc24-crumbs`, `bc24-levels`, `bc25-towers`,
  `bc25-econ` (`client/replay_broadcast.html:5030–5041`); `#killfeed`'s `bottom` is
  `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))` (line 1270). bc23's job
  is to **keep the fix armed** — add its two boxes to that list — not to re-fix it.
- **`beatsFor` in `src/battlecode/broadcast.nim:129` is the ONE place a beat kind is decided**, and it
  already carries a year discriminator (`let isBc25 = doc.year == "bc25"`) because `first_action` and
  `rout` are spelled the same by bc24 and bc25 and carry different fields. bc23 emits both of those
  names too, so that discriminator becomes a three-way test (§Viewer, "the beat contract"). The bc25
  run's only blocking finding (r1-F26) was 11 beat-kind CSS rules against 2 emitted kinds; this note
  pins **emission + label + style, all three tested from the committed fixture**.
- **`tools/ci/viewer_smoke.mjs` already carries the scrub-selector fix** (`SCRUB_SELECTORS` tried one
  at a time, `#scrub` first) and `ci.yml` asserts `scrub_selector == "#scrub"` per replay. Nothing to
  do here except the pacing decision in §Viewer.
- **`tools/ci/docker_smoke.sh` already carries `SMOKE_EXPECT_YEAR`, `SMOKE_PLAYER_IDS`,
  `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`, `SMOKE_CONTRACT_PROBE`, `SMOKE_SEATS` and
  `SMOKE_REQUIRE_STATS`**, and `tools/ci/cert_probe.py` runs inside it. bc23 adds a sixth episode and
  reuses all of them; **no script change is needed**.
- **`replay-viewer/config.nims` needs no edit**: `--preload-file {rootDir}/data@data` already carries
  the whole `data/` tree, so `data/maps/bc23/`, `data/bc23/tables.json` and `data/atlas_bc23.*` ship
  with no link-flag change, and `EXPORTED_FUNCTIONS` gains nothing.
- **This repo records `result` (singular) in the replay**, not `results` — the 2026-09-07 verify
  lesson — and a best-of-three episode legitimately plays **fewer** games than `gamesPerMatch` when a
  side clinches, with `reason` still `complete`.
- **The shipped coworld version is 0.5.0.** This run ships **0.6.0**.

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as bc26/bc20/bc21/bc24/bc25 (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, five generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. No new repo (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=awu\|scaffold` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc23/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc23` bytes anywhere. |
| Real art, starter chrome verbatim | 2023 sprites cut from `client/visualizer/src/static/img/` into `data/atlas_bc23.*` (credited in `NOTICE` — §Packaging); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc23 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **445 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26\|bc20\|bc21\|bc24\|bc25].game_config` (all unchanged) and `variants[bc23].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc23 policy set is in §Packaging. |

---

## The game

**Battlecode 2023 "Tempest", played by doctrine, simulated in Nim.** Two cogs each command a faction
of robots on a symmetric grid between **20×20 and 60×60**. Neither cog moves a robot. At t=0 each
writes a **doctrine** — a JSON sheet of twelve named knobs — and the deterministic sim plays the whole
match from those two sheets while both cogs watch.

The map holds **sky islands** (4 to 35 of them, each at most 20 tiles), **resource wells** of
adamantium and mana, **impassable storm squares**, **clouds** that blind and slow whatever stands in
them, and **directional currents** that shove every robot standing on one, one square, at the end of
every round. Each faction starts with **1 to 4 headquarters**, indestructible, each with its own
stockpile.

Everything runs off two resources and a third you have to manufacture. A **carrier** (150 HP,
capacity 40) mines 1 kg per action from a well it is standing on or beside, walks it home, and hands
it to a headquarters — and its movement cooldown is `floor(5 + 3m/8)` in its own cargo weight `m`, so
a full carrier is half the speed of an empty one. A carrier can also **throw** its whole cargo at an
enemy for `floor(5m/4)` damage — up to 50 — and the cargo is gone whether it hits or not. A
**launcher** (200 HP, 45 kg of mana) hits one square within 16 units for 20 damage and is the only
real attacker in the game. A **signal amplifier** (30 Ad + 15 Mn) is what lets ordinary robots
*write* to the faction's 64-slot shared array. And then the elixir branch: pour **600 kg of the
opposite resource** into a well and it becomes an **elixir well**; elixir buys **temporal
destabilizers** (200 kg — slow the enemy 10 % over a 15-unit patch for five rounds and then detonate
for 50 damage), **temporal boosters** (150 kg — speed your own side up 10 % over a 20-unit patch for
ten rounds) and **accelerating anchors** (300 kg).

You win by **conquering 75 % of the sky islands**: build an anchor at a headquarters (standard =
80 Ad + 80 Mn; accelerating = 300 Ex), have a carrier ferry it — an anchor weighs the carrier's whole
capacity, so a ferrying carrier carries nothing else — and plant it while standing on the island. The
island is yours until its anchor's health reaches zero, and every round that health moves by
`(% of island tiles you occupy) − (% the enemy occupies)`, so holding an island is a garrison problem,
not a one-time errand. Nobody conquering 75 % by round 2000 means the match is decided on a
five-rung ladder: islands held, then anchors ever placed, then net elixir, then net mana, then net
adamantium, then a coin flip.

**That ladder is why this year is worth playing sealed.** The 2023 metagame collapsed to "whoever won
the opening launcher duel won", and the entire elixir tree went unused — the first-place bot
(`awesomelemonade/Battlecode2023`, `src/finalBot/`) has no `Booster.java` and no `Destabilizer.java`
at all, and the ninth-place bot's `Destabilizer.run()` is one call to `tryWander()`. **Measured
here:** three full 2000-round mirror games of the official example bot ended with islands **0–0**,
anchors **0–0**, and the winner decided by rung 4 (`MORE_MANA_NET_WORTH`) — i.e. by who happened to
be holding more mana. The doctrine sheet in §Decisions makes the anchor economy and the elixir tech
tree *spendable choices with teeth*, and the league is the experiment: sealed doctrines, a real
oracle, and a scoreboard that says whether launcher-rush is actually uncounterable.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. The episode seed
decides which slot takes engine-side **A** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc25/maps.nim`).

### Constants (verbatim from the pinned engine — `common/GameConstants.java`)

Generated into `src/battlecode/years/bc23/constants.nim` by `tools/gen_year_constants.py --year bc23`,
never hand-typed, and re-generated and byte-diffed in CI (§Tests item 23).

| constant | value | constant | value |
|---|---|---|---|
| `GAME_MAX_NUMBER_OF_ROUNDS` | **2000** | `WIN_PERCENTAGE_OF_ISLANDS_OCCUPIED` | **0.75f** |
| `MAP_MIN_*` / `MAP_MAX_*` | **20 / 60** | `MIN_/MAX_STARTING_HEADQUARTERS` | **1 / 4** |
| `MIN_/MAX_NUMBER_ISLANDS` | **4 / 35** | `MAX_ISLAND_AREA` | **20** |
| `INITIAL_AD_AMOUNT` / `INITIAL_MN_AMOUNT` | **200 / 200** per HQ | `PASSIVE_AD_INCREASE` / `_MN_` | **6 / 6** per HQ |
| `PASSIVE_INCREASE_ROUNDS` | **5** | `CARRIER_CAPACITY` = `ANCHOR_WEIGHT` | **40** |
| `UPGRADE_TO_ELIXIR` | **600** | `UPGRADE_WELL_AMOUNT` | **1400** |
| `WELL_STANDARD_RATE` / `_ACCELERATED_RATE` | **1 / 3** | `CURRENT_STRENGTH` | **1** (currents every round) |
| `COOLDOWN_LIMIT` / `COOLDOWNS_PER_TURN` | **10 / 10** | `CLOUD_VISION_RADIUS_SQUARED` | **4** |
| `CLOUD_MULTIPLIER` | **+0.2** | `BOOSTER_MULTIPLIER` | **−0.1** |
| `DESTABILIZER_MULTIPLIER` | **+0.1** (on the enemy) | `ANCHOR_MULTIPLIER` | **−0.15** |
| `BOOSTER_RADIUS_SQUARED` / `_DURATION` | **20 / 10** | `DESTABILIZER_RADIUS_SQUARED` / `_DURATION` | **15 / 5** |
| `MAX_BOOST_STACKS` | **3** | `MAX_DESTABILIZE_STACKS` | **2** |
| `MAX_ANCHOR_STACKS` | **1** | `CARRIER_DAMAGE_FACTOR` | **1.25f** |
| `CARRIER_MOVEMENT_SLOPE` / `_INTERCEPT` | **0.375f / 5** | `SHARED_ARRAY_LENGTH` | **64** |
| `MAX_SHARED_ARRAY_VALUE` | **65535** | `DISTANCE_SQUARED_FROM_SIGNAL_AMPLIFIER` | **20** |
| `DISTANCE_SQUARED_FROM_HEADQUARTER` | **9** | `DISTANCE_SQUARED_FROM_ISLAND` | **4** |
| `SPEC_VERSION` | **"3.0.14"** — see §Tests: the *released 3.0.15 jar* also reports `"3.0.14"`, so **no version-string assertion anywhere**; the sha256 is the pin | `GAME_DEFAULT_SEED` | 6370 (unused here) |
| `INDICATOR_STRING_MAX_LENGTH` | 64 — **not ported** (no indicator strings) | `EXCEPTION_BYTECODE_PENALTY` | 500 — **not ported** (no JVM exceptions) |
| `MAX_DISTANCE_BETWEEN_WELLS` / `MIN_NEAREST_AD_DISTANCE` / `MAX_MAP_PERCENT_WELLS` | 100 / 100 / 0.04f — **map-generation guarantees, not runtime rules; not ported** | | |

`RobotType` — the whole table, verbatim (`buildCostAdamantium, buildCostMana, buildCostElixir,
actionCooldown, movementCooldown, health, damage, actionRadiusSquared, visionRadiusSquared,
bytecodeLimit`), cross-checked against the spec's own stat table:

| unit | Ad | Mn | Ex | action cd | move cd | HP | damage | action r² | vision r² | bytecode |
|---|---|---|---|---|---|---|---|---|---|---|
| `HEADQUARTERS` | 0 | 0 | 0 | **2** | −1 (cannot move) | **1** (indestructible) | **4** | **9** | **34** | 20 000 |
| `CARRIER` | **50** | 0 | 0 | **10** | `floor(5 + 3m/8)` | 150 | `floor(5m/4)` | **9** | 20 | 12 500 |
| `LAUNCHER` | 0 | **45** | 0 | **10** | **20** | 200 | **20** | **16** | 20 | 10 000 |
| `DESTABILIZER` | 0 | 0 | **200** | **70** | **25** | 300 | **50** | **13** | 20 | 10 000 |
| `BOOSTER` | 0 | 0 | **150** | **140** | **25** | 400 | 0 | −1 (self) | 20 | 10 000 |
| `AMPLIFIER` | **30** | **15** | 0 | −1 (no action) | **15** | 120 | 0 | −1 | **34** | 10 000 |

`Anchor` — verbatim (`totalHealth, unitsAffected, accelerationFactor, healingFrequency,
healingAmount, manaCost, adamantiumCost, elixirCost`):

| anchor | health | accel | heals | every | Mn | Ad | Ex |
|---|---|---|---|---|---|---|---|
| `STANDARD` | **250** | 0.0f | **4 HP** | every round | **80** | **80** | 0 |
| `ACCELERATING` | **750** | **−0.15f** | **6 HP** | every round | 0 | 0 | **300** |

**An `HEADQUARTERS` action cooldown of 2 against a `COOLDOWN_LIMIT` of 10 means a headquarters can act
up to FIVE times in one turn** (2+2+2+2+2 = 10, and `isActionReady` is `cooldown < 10`). That is a
load-bearing rule, not a curiosity: a rich faction with two headquarters can put ten robots on the
board in a single round, and `tests/test_bc23_cooldown.nim` pins it.

**Where the spec's prose and the engine disagree, the engine wins**, and all six disagreements are
recorded in `docs/RULES-BC23.md` §Divergences:

1. **Currents fire at the end of the ROUND, not "at the end of the turn".** The prose says a robot in
   a current "will be forced to move … at the end of the turn, applied after existing robot
   movement"; `GameWorld.processEndOfRound` calls `applyCurrents()` once, after **every** robot has
   taken its turn. The port does the same.
2. **A destabilizer's damage lands at the end of round `cast + 4`, not `cast + 5`.** `addDestabilize`
   stores `lastRound = round + 5` and the end-of-round sweep fires on `entry <= round' + 1`, so the
   50 damage is dealt at the end of round `cast + 4` — the same round the slow is still in effect,
   not "after which". Boosts, symmetrically, cover rounds `cast … cast + 9` inclusive, which *is* the
   prose's ten turns.
3. **Time-bending effects are additive on a per-tile, per-team multiplier, and the multiplier is
   quantised to two decimals after every change.** `1.0 + 0.2` (cloud) `− 0.1` per boost stack
   `+ 0.1` per destabilise stack `− 0.15` for an accelerating anchor, each step passed through
   `Math.round(x*100.0)/100.0`, and applied as `(int) Math.round(baseCooldown × multiplier)`. The
   prose's "10 % increase/reduction" is not a multiplication of the previous value.
4. **A destabilizer's detonation hits at most ONE robot per tile — the one standing there when that
   tile's entry expires — and only of the destabilised team.** The prose says "damage is dealt to all
   enemies in the affected area"; the engine's sweep is `getRobot(loc)` per tile
   (`GameWorld.processEndOfRound`), which is the same thing only because at most one robot occupies a
   tile. The port reproduces the sweep, tile by tile, in the engine's own location order.
5. **The stack guards are asymmetric and the port keeps them.** `addBoost` adjusts the multiplier only
   when the tile's list is **shorter than** `MAX_*_STACKS`, while the expiry sweep adjusts it when the
   list is **at most** `MAX_*_STACKS`, each evaluated against the list size at that moment. Over the
   life of a tile the two are balanced; the port reproduces both predicates literally instead of
   clamping a counter, because a clamped counter drifts on a tile that ever exceeded the cap.
6. **A headquarters on a current would be pushed by it.** The prose guarantees "a headquarter cannot
   be located on a current"; `applyCurrents` iterates *every* robot, headquarters included, and would
   move it. **Measured over all 103 official maps: zero headquarters sits on a current**, so the path
   is unreachable on shipped maps. The port keeps the engine's behaviour and
   `tests/test_bc23_currents.nim` asserts the unreachability on every committed map.

Two further map-generation guarantees the prose states and the engine does not enforce were **checked
across all 103 official maps and hold everywhere**: no square is both cloud and current, and no two
currents flow into the same square (also: no cloud sits on a wall, and no current flows into a wall or
off the map). So `applyCurrents`'s blocking machinery is only ever driven by robots blocking robots.

### The 2023 rule set — exact numbered resolution rules

The sim's own step list. Steps 1–4 are one round; re-ordering any of them is a rules change and bumps
`GameVersion`. It mirrors `GameWorld.runRound` / `processBeginningOfRound` / `updateDynamicBodies` /
`processEndOfRound` exactly.

1. **Beginning of round.** (a) `currentRound += 1`. (b) The engine then calls
   `processBeginningOfRound` on every robot, which does **exactly one thing: clear the indicator
   string** — and this port has no indicator strings, so step 1b is a **no-op with no observable
   effect**, recorded here so nobody looks for the missing code. (c) **On round 1 only**, walk the
   exec order and give **each** headquarters `+200` adamantium and `+200` mana — added to that
   headquarters' own stockpile *and* to the team total (`addResourceAmount` does both). A map with
   three headquarters a side therefore starts at 600/600, not 200/200; the engine throws if any
   round-1 body is not a headquarters, and the port asserts the same.
2. **Turn order.** Iterate `ObjectInfo.dynamicBodyExecOrder`, a `TIntArrayList` of robot ids with
   **append on spawn** and **by-value removal on death** (`dynamicBodyExecOrder.remove(id)` removes
   the first entry equal to `id`, compacting the list and preserving the order of the survivors). The
   array iterated is a **snapshot taken before the sweep** (`toArray()`), so a robot built this round
   does **not** take a turn this round, and a robot destroyed mid-sweep is skipped by the
   `existsRobot(id)` guard. The initial headquarters are appended in **ascending id order**, because
   `LiveMap`'s constructor sorts its initial bodies by id. Reproducing the list operations literally
   is a correctness requirement, not a detail (`tests/test_bc23_execorder.nim`).
3. **Each robot's turn**, in three parts:
   1. **Beginning of turn**: `actionCooldown = max(0, actionCooldown − 10)`;
      `movementCooldown = max(0, movementCooldown − 10)`; the robot's `DecisionOps` budget is reset to
      **2 000** (headquarters), **1 250** (carrier) or **1 000** (everything else) — §Sim module, this
      replaces the Java bytecode limit. Both cooldowns start a robot's life at **10**
      (`GameConstants.COOLDOWN_LIMIT`), so a robot built this round can neither move nor act on its
      first turn even after the decrement.
   2. **Run the controller.** The robot runs its team's chassis under that team's doctrine, spending at
      most its `DecisionOps` budget. `assertCanActLocation(loc)` is "within `actionRadiusSquared` **and**
      on the map"; `isActionReady` is `actionCooldown < 10`; `isMovementReady` is
      `movementCooldown < 10`. **There is no paint-style upkeep and no per-turn attrition in this
      year**: a robot's end of turn is `roundsAlive += 1` and nothing else. The legal actions, with
      their exact preconditions and effects, in the engine's own order of operations:
      1. **Move** (8 directions; not a headquarters): movement-ready; the destination is on the map,
         **unoccupied** and **passable** (`isPassable = !wall`; a headquarters, a well and an island
         tile are all passable, but an occupied tile is not, which is what makes headquarters
         un-walkable). Effect, in this order: (a) the robot moves; (b) `addMovementCooldownTurns()`
         adds `round(base × multiplier(NEW tile, own team))`, where `base` is the type's
         `movementCooldown` except for a carrier, whose base is `floor(0.375f × weight) + 5` in its
         **current** cargo weight. **The multiplier is read at the destination, after the move** —
         so a robot stepping into a cloud pays the cloud's 20 % on the very step that enters it.
      2. **Build a robot** (headquarters only; target within r² ≤ 9 and on the map): action-ready; the
         type is not `HEADQUARTERS`; **this headquarters' own stockpile** holds all three costs; the
         tile is unoccupied and passable. Effect, in this order: charge
         `round(2 × multiplier)` action cooldown; deduct all three costs from this headquarters (and
         from the team total); spawn the robot at the next `IDGenerator` id, at full health, with both
         cooldowns at 10.
      3. **Build an anchor** (headquarters only): action-ready; the stockpile holds the anchor's costs
         (80 Ad + 80 Mn, or 300 Ex). Effect: charge `round(2 × multiplier)`; deduct; the anchor sits in
         **that headquarters'** inventory until a carrier takes it. There is no range check and no
         limit on how many anchors a headquarters may hold.
      4. **Attack** (carrier or launcher; target within r² ≤ 9 / r² ≤ 16 and on the map): action-ready;
         a carrier additionally needs `weight > 0`. Effect, in this order: (a) charge
         `round(10 × multiplier)`; (b) if the target tile holds an **enemy non-headquarters robot**,
         deal `20` (launcher) or `floor(1.25f × weight)` (carrier); a headquarters, an ally, and an
         empty tile all take nothing; (c) **a carrier then empties its entire inventory regardless** —
         every resource (deducted from the team total too) and every anchor it was carrying is
         destroyed. **An attack can hit a robot the attacker cannot see** (there is no vision
         precondition), which is exactly how launchers fight through clouds.
      5. **Destabilize** (destabilizer; target within r² ≤ 13 and on the map): action-ready. Effect,
         in this order: (a) for every tile within **r² ≤ 15 of the target**, in the engine's location
         order, push `round + 5` onto the **enemy** team's destabilise list for that tile and, when
         that list was shorter than 2, add `+0.1` to the enemy's multiplier there; (b) *then* charge
         `round(70 × multiplier)` on the destabilizer's own tile. The damage is dealt later, at step
         4b.
      6. **Boost** (booster): action-ready. Effect, in this order: (a) for every tile within
         **r² ≤ 20 of the booster's own tile**, push `round + 10` onto **its own** team's boost list
         and, when that list was shorter than 3, add `−0.1` to its own multiplier there; (b) *then*
         charge `round(140 × multiplier)` — **read after the boost**, so a booster's own 140 is
         discounted by the boost it just cast. The boosted patch is fixed to where it was cast and does
         not follow the booster.
      7. **Collect** (carrier; target within r² ≤ 9 **and** `isAdjacentTo` — `|dx| ≤ 1 && |dy| ≤ 1`,
         which **includes the carrier's own tile**): action-ready; the tile is a well; the amount is
         `≤ 1` (a normal well) or `≤ 3` (an upgraded one), with `-1` meaning "the rate"; the cargo
         fits in the remaining capacity. Effect: charge `round(10 × multiplier)`; add that much of the
         well's **current** type to the carrier and to the team.
      8. **Transfer** (carrier; r² ≤ 9 and adjacent-or-same-tile): action-ready; a **positive** amount
         requires the carrier to hold it and the target to be a **well or a friendly headquarters**; a
         **negative** amount (withdrawing) is legal only from a **friendly headquarters** that holds
         it, and must fit the carrier's capacity. Effect: charge `round(10 × multiplier)`; move the
         resource; **a positive transfer into a well removes the resource from the team total** — the
         well swallows it. A well that has swallowed **1400 kg of its own type** upgrades to rate 3;
         a well that has swallowed **600 kg of the opposite type** becomes an **elixir well** and
         stops producing its original resource. An elixir well that has swallowed 1400 kg of elixir
         upgrades to rate 3.
      9. **Take an anchor / return an anchor** (carrier; r² ≤ 9 and adjacent-or-same-tile to a friendly
         headquarters): action-ready; the headquarters holds one of that type; the carrier has room for
         `ANCHOR_WEIGHT = 40`, i.e. **the carrier must be completely empty**. Effect: charge
         `round(10 × multiplier)`; the anchor moves between them.
      10. **Place an anchor** (carrier): action-ready; the carrier is **standing on an island tile**;
          it holds an anchor; and the island is not held by the **enemy** (an enemy anchor must be
          worn down to 0 first; your own island may be overridden, including with a different type).
          Effect: the island's owner becomes this team, its anchor becomes the placed type and its
          health becomes that type's **full** total (250 or 750) regardless of what was there before;
          an accelerating anchor registers a `−0.15` boost on every tile within r² ≤ 4 of any of the
          island's tiles; the carrier releases the anchor; charge `round(10 × multiplier)`. If the
          island was **not already ours**, `totalAnchorsPlaced` and `currentAnchorsPlaced` both
          increment and **the 75 % conquest check fires immediately, mid-turn** (see step 4d).
          Overriding an anchor on an island we already hold increments **neither** counter — which the
          spec calls out explicitly and which is a real doctrine consideration.
      11. **Write the shared array** (index 0…63, value 0…65535): legal when the robot **is** a
          headquarters or an amplifier, or has a friendly **amplifier within r² ≤ 20**, or a friendly
          **headquarters within r² ≤ 9**, or one of **its own islands within r² ≤ 4** (the island's
          minimum squared distance to the robot). **No cooldown and no cost.** Reading is always legal.
      12. **Disintegrate**: any robot may destroy itself immediately; the control provider's
          terminated flag makes `updateRobot` destroy it at the end of its own turn.
      13. **Sense** (free against `DecisionOps` only): robots, wells, islands, clouds, currents and
          per-tile time-bending state within the type's `visionRadiusSquared` (34 for a headquarters
          and an amplifier, 20 for everyone else) — **except that if either the sensing robot's tile or
          the sensed tile is a cloud, the radius collapses to 4**. That is the whole fog mechanic:
          clouds hide and blind, symmetrically. Scan order is the engine's:
          `ceiledRadius = ceil(sqrt(r²)) + 1`, then **x ascending outer, y ascending inner**, keeping
          tiles with `dx² + dy² ≤ r²`.
   3. **End of turn**: `roundsAlive += 1`. Then, if the chassis disintegrated, the robot is destroyed.
4. **End of round**, in exactly this order:
   1. **Every island advances a turn.** For each island: count the tiles occupied by each team;
      `diff = (100 × (ownerTiles − enemyTiles)) / islandArea` — **Java integer division, truncated
      toward zero, and it can be negative**; `anchorHealth = min(totalHealth, anchorHealth + diff)`.
      If that is `≤ 0` the island goes **neutral**: the owner's `currentAnchorsPlaced` decrements, an
      accelerating anchor's boost is removed, and the anchor is gone. Then, **if the island still has
      an anchor**, every friendly robot within **r² ≤ 4 of any of the island's tiles** is healed by
      the anchor's `healingAmount` (4 or 6) — every round, because both anchors have
      `healingFrequency = 1`. (A just-neutralised island heals nobody: `getLocsAffected()` returns the
      empty set when the anchor is gone, which is why the engine's `anchorPlanted.healingFrequency`
      dereference cannot fault. The port keeps that shape.) Neutral islands are skipped entirely.
   2. **Boosts and destabilisations expire.** Walk **every tile of the map** in the engine's location
      order (x ascending outer, y ascending inner) and, for **team A then team B**: scan that tile's
      boost list from the back and drop every entry `≤ round + 1`, adjusting the multiplier under the
      asymmetric guard (divergence #5); then the same for the destabilise list, and **for each entry
      dropped, if a robot of that team is standing on the tile, deal `50` damage to it**
      (`RobotType.DESTABILIZER.damage`). A robot can therefore be hit twice on one tile if two
      destabilisations expire together.
   3. **Every robot's end of round.** For a **headquarters** only: (a) deal **4** damage to every
      enemy robot within r² ≤ 9, in the engine's location scan order; (b) if `round % 5 == 0`, add
      `+6` adamantium and `+6` mana to its own stockpile and the team total. Every other robot does
      nothing. Then the team resource deltas for the round are rolled over.
   4. **Currents apply** (`round % 1 == 0`, i.e. always): (a) forecast every robot's destination as
      `location + current(location)` (`Direction.CENTER` for a tile with no current); (b) mark
      **immediately blocked** every robot whose forecast tile is impassable, off the map, or contested
      by more than one robot; (c) close that set transitively — a robot forecast onto the tile of a
      robot that is not moving is also not moving; (d) every remaining robot standing on a real current
      is lifted off the board and set down one square along it. The transitive closure is order
      independent (each tile holds at most one robot, so "visited by location" and "processed" are the
      same predicate), which is what lets the port compute it with a deterministic worklist instead of
      the engine's `HashSet` iteration (§Sim module, divergence D3).
   5. **End-of-match check**: if `currentRound >= 2000` **and no winner is set yet**, apply the ladder,
      first hit wins — **more islands held** (`more_sky_islands`) → **more anchors ever placed**
      (`more_reality_anchors`) → **more team elixir** (`more_elixir_net_worth`) → **more team mana**
      (`more_mana_net_worth`) → **more team adamantium** (`more_adamantium_net_worth`) → **coin flip**
      (`coin_flip`).
   6. If a winner is set — by the ladder, or by the **75 % conquest check that fires mid-turn inside
      `placeAnchor`** — the game stops. Then append this round's state hash (§Sim module).

**Five subtleties the port reproduces literally, each with its own test:**

- **A conquest win fires mid-turn and does not stop the round.** `TeamInfo.placeAnchor` runs the
  threshold test the instant a carrier plants an anchor, and `running` is only cleared at step 4f, so
  every robot after that carrier in the exec order still takes its turn and every action is recorded.
  `tests/test_bc23_endladder.nim` pins it.
- **The 75 % test is a float32 division**: `((float) currentAnchorsPlaced) / islandCount >= 0.75f`,
  where `currentAnchorsPlaced` is the number of islands the team **currently** holds (it decrements
  when an anchor dies). The engine then re-counts islands owned and throws `InternalError` if the two
  disagree — the port keeps that assertion as a `fault` invariant. The whole finite table is pinned:
  4 islands → 3, 5 → 4, 6 → 5, 7 → 6, **8 → 6**, 9 → 7, 10 → 8, 11 → 9, **12 → 9**, 13 → 10, 14 → 11,
  15 → 12, **16 → 12**, 17 → 13, 18 → 14, 19 → 15, **20 → 15**, 21 → 16, 22 → 17, 23 → 18, **24 → 18**,
  25 → 19, 26 → 20, 27 → 21, **28 → 21**, 29 → 22, 30 → 23, 31 → 24, **32 → 24**, 33 → 25, 34 → 26,
  35 → 27. (Every fourth entry is where float32 rounding lands exactly on the threshold; those are the
  interesting rows and Tier B checks all 32 of them against the jar.)
- **There is no elimination condition in 2023.** Headquarters are indestructible — `addHealth` returns
  immediately for a headquarters, so their nominal 1 HP is never touched — and no rule ends the game
  for having no robots. A faction that loses every carrier and launcher plays on to round 2000. So
  `results.games[].end_reason` has **no `destroy_all_units` value**, unlike bc25, and a game only ends
  early by conquest.
- **A carrier's throw empties it even when it misses**, and the resources come off the **team** total,
  not just the carrier's. That makes `carrier_throw` (§Decisions) a real economic decision and not a
  free action.
- **`resign()` exists and is unreachable.** It destroys every robot of the resigning team and sets
  `RESIGNATION`. A doctrine is a JSON sheet; neither chassis calls it. `docs/RULES-BC23.md`
  §Divergences records that it is *unreachable here* rather than *absent upstream*, and
  `tests/test_bc23_endladder.nim` asserts no chassis can reach it.

**Deliberate non-rules, verified absent from the 2023 engine and therefore absent here:** there is no
terrain other than passable/impassable, wells, islands, clouds and currents (no elevation, no water,
no rubble); walls, clouds, currents, wells and islands are never created or destroyed during a game;
robots never regenerate except from an anchor's healing; there is no unit cap of any kind; there is no
per-turn upkeep; `GameWorld.rand` and `RobotControllerImpl.random` are both constructed from the map
seed and **never read** (the port does not create them); the map file's symmetry field is recorded
and never used by the engine at runtime; `MapSymmetry`, `BuildMaps`, `MapBuilder` and
`TestMapBuilder` are map-authoring tools with no runtime role; and the profiler, indicator strings,
indicator dots and indicator lines are instrumentation with no port.

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc23` variant is **best-of-three on three
distinct maps from the `mixed` pool, played to the engine's own 2000-round cap**.

```
container start, map load, seat connect              <=  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    <=  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 2000 rounds                         <= 340 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 110)
score + replay write + shutdown grace                <=  30 s
                                                       -------
worst case                                             445 s   <= 720 s
```

Honest per-round estimate, so the builder can check it. bc23's cost is **unit-count driven**, and the
unit count is bounded only by economy: a carrier is 50 kg of adamantium and a launcher 45 kg of mana
against a passive income of 6+6 per headquarters per five rounds plus whatever the carriers mine, and
headquarters can build five units a turn. **Measured on the real engine in this sandbox**, the official
example bot against itself peaks at **121–157 robots on the board** (mean **97–124**) over three full
2000-round games on 30×30, 32×32 and 50×30 maps, and each of those games took **26.5–31.1 s of
instrumented JVM**. That is four to six times bc25's unit count, so this note sizes for it rather
than hoping:

- Each robot's turn is a ≤ 121-tile vision sweep (r² ≤ 34 for headquarters and amplifiers, ≤ 69 tiles
  at r² ≤ 20 for the rest), a bounded navigation step and one action ≈ **300 `DecisionOps`**, so at a
  budgeted worst case of **200 robots/round** that is 6 × 10⁴ ops/round and 1.2 × 10⁸ per game —
  **4–9 ms/round, 8–18 s per game** in release Nim. The *enforced* ceiling is the per-robot
  `DecisionOps` budget, which caps a round at `200 × 1250 = 2.5 × 10⁵` ops.
- The one structurally unbounded primitive in the rule set is the chassis's own pathfinding BFS. The
  port charges **1 `DecisionOps` per node expanded**, and because the budget is checked **before**
  each primitive and never inside one, a BFS is never cut in half (§Sim module).
- `perGameBudgetSeconds = 110` and `matchBudgetSeconds = 340` are hard monotonic-clock guards. A game
  that blows its guard is abandoned, the finished games are scored, and `results.reason = deadline`.
- `tests/test_bc23_perf.nim` plays a full 2000-round game on `IslandHopping` (60×30, the largest map in
  the variant's pool) with **both seats on `opening: carrier_eco`, `launcher_ratio: 80`,
  `anchor_budget: 0`** — the configuration that maximises robot count and therefore per-round work —
  and **fails CI above 100 s**.
- If that gate ever goes red the fix is one config value — `gamesPerMatch: 3 → 1` in the `bc23`
  variant — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc23's axis is **island-count-shaped**: the anchor
  economy pays very differently on a 4-island map (conquest needs 3 islands, and one launcher push
  decides it) than on a 20-island map (conquest needs 15, so garrisons and ferry logistics decide it).
  The `mixed` pool spans 4 to 20 islands deliberately (§Sim module, Maps). One map would rank the map,
  not the doctrine.
- **Because this sim is heavy (well above 1 ms/round), the phase-60 viewer check 8 is dispatched with
  `settle=20000 soak=15`** and `ci.yml`'s `wasm-viewer` job runs the bc23 replay at
  `--timeout 120 --soak 15` (§Viewer, the bc21 lesson).

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

### Scoring, sign, and what the bc23 league ranks by

The 2023 game is win/lose; it has no point formula. This one is defined here, and it is a continuous
reading of the engine's own end ladder so that the score and the winner never tell different stories:

```
share(x, y)   = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
islands[t]    = islands t HOLDS at the final round               # rung 1, and the 75% win condition
anchors[t]    = anchors t EVER placed (totalAnchorsPlaced)       # rung 2
elixir[t]     = t's team elixir at the final round               # rung 3
mana[t]       = t's team mana at the final round                 # rung 4
adamantium[t] = t's team adamantium at the final round           # rung 5
points[t]     = int(60.0'f32 * share(islands[t],    islands[o])
                  + 22.0'f32 * share(anchors[t],    anchors[o])
                  + 10.0'f32 * share(elixir[t],     elixir[o])
                  +  5.0'f32 * share(mana[t],       mana[o])
                  +  3.0'f32 * share(adamantium[t], adamantium[o]))   # TRUNCATION, not rounding
```

Six load-bearing details, each pinned by a test vector in `tests/test_bc23_scoring.nim`:

- every share is narrowed through **float32** before the weighted sum, and the sum is **truncated** by
  the `int()` cast. The reason is **recorder/re-deriver agreement**: the same arithmetic runs natively
  on x86-64 and in wasm32 and must produce the same integer;
- the five terms are exactly the engine's five deciding rungs, in the engine's own priority order;
- **the weights are strictly super-increasing from the bottom** — `22 > 10+5+3`, `10 > 5+3`, `5 > 3`,
  and `60 > 22+10+5+3` — which makes the tiebreak property *provable* rather than hopeful: a rung is
  only reached when every rung above it is tied, a tie contributes exactly 0.5 of its weight to both
  seats, and the winner's strict advantage on the deciding rung exceeds everything the loser can take
  from all rungs below it. So **a win on any of the five rungs always comes with the winner's `points`
  strictly above the loser's**. (bc25's 55/20/10/10/5 does not have this property; this note fixes the
  shape rather than inheriting it.)
- `share` returns **0.5 on a 0–0 total**, the same choice bc24 and bc25 made and for the same reason:
  two factions that both ended with zero elixir should not be scored differently by an arithmetic
  accident. On this year's evidence that case is the *common* one — the measured mirror games ended
  0–0 on islands, anchors **and** elixir — so the reachable range of `points` in a passive match is
  narrow and the mana/adamantium terms do the separating, which is exactly the ladder's own priority;
- points are in `[0, 100]` and the two seats' points sum to ≤ 100;
- **a `conquest` win can carry FEWER points than the loser**, and that is deliberate and harmless: a
  faction that conquers 12 of 16 islands at round 700 has an islands share of 0.75 (45 points) and may
  have spent its whole bank doing it, while the loser can hold 4 islands and a full treasury (up to 55).
  `points` measures the *shape* of the game, not who won it. **`results.scores` is what the league
  ranks and it is win-dominated by construction:**

```
results.scores[t] = 200.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** With `points ∈ [0, 100]`, a 2–0 gives 400+`mean` against ≤ 100, and a 2–1 gives
400+`mean` against 200+`mean` ≤ 300 — so the ordering of `results.scores` **provably** agrees with
`results.wins` in every reachable case, including a clinched best-of-three that played only two games.
`tests/test_bc23_scoring.nim` asserts that agreement on 500 random synthetic finals, and asserts the
super-increasing tiebreak property on one vector per rung. **The `bc23` league ranks by
`results.scores`** (Elo over the resulting ordering), exactly as the five shipped leagues do. A
`deadline` episode scores the games that finished; a `fault` episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` in snake_case, plus our one
wall-clock value:

| `end_reason` | engine origin | meaning |
|---|---|---|
| `conquest` | `CONQUEST` | a faction held ≥ 75 % of the islands (float32 test); fires the instant the anchor is planted |
| `more_sky_islands` | `MORE_SKY_ISLANDS` | round 2000 reached; more islands held |
| `more_reality_anchors` | `MORE_REALITY_ANCHORS` | islands tied; more anchors ever placed |
| `more_elixir_net_worth` | `MORE_ELIXIR_NET_WORTH` | anchors tied; more team elixir |
| `more_mana_net_worth` | `MORE_MANA_NET_WORTH` | elixir tied; more team mana |
| `more_adamantium_net_worth` | `MORE_ADAMANTIUM_NET_WORTH` | mana tied; more team adamantium |
| `coin_flip` | `WON_BY_DUBIOUS_REASONS` | everything tied; a draw from the world RNG |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded |

`coin_flip` and `abandoned` are already in the manifest's `end_reason` enum; the other six are added
(§Packaging). **`resignation` is not added** (unreachable — above). **`destroy_all_units` is not
reachable in this year at all** (no elimination condition).

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from the five shipped
years**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped (a spend that would take a stockpile negative, or the engine's own "reporting incorrect win" assertion): a partial replay and `[0, 0]` are still written | `[0, 0]` |

**Best-of-N clinch semantics, stated because phase 60 has judged this wrong before (2026-09-07):** a
side that takes 2 games settles the episode immediately. An episode that records **two** games with
`reason: complete` on a `gamesPerMatch: 3` variant is **correct**, not truncated; `results.games`
carries only the games actually played, and `replay.plan.maps` carries all three drawn maps so a
spectator can see what the third would have been.

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the five
shipped years). Container exit codes are unchanged: `0` whenever results + replay were attempted
(including `deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep answering for
the ~20 s shutdown grace, and the websocket handler keeps its `Ping → Pong` **payload echo** and does
not filter binary frames (`tools/ci/cert_probe.py` proves both against the real image).

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

### The bc23 doctrine sheet — twelve knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc23 chassis. Unknown key, wrong
type or out-of-range value → **that field's default**, recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by
answering badly — only by answering weakly.

**The anti-inert rule, stated as a rule the builder must hold every knob against: no setting of any
knob, and no combination of settings, may produce an inert or self-starving faction.** The strategy
surface lives *inside one competent chassis*. Concretely, and independently of every knob, the chassis
always: keeps at least **3 carriers per headquarters** mining whichever well its `well_priority`
prefers and depositing at the nearest friendly headquarters; builds a launcher whenever mana allows
and the launcher census is below its target; spends a headquarters' spare actions rather than banking
them (a headquarters may act five times a turn — §The game); answers an enemy launcher sensed within
r² ≤ 16 of one of its own headquarters; steps off a current that would carry a loaded carrier away
from home; and, from `anchor_round` onwards, keeps at least one anchor in flight whenever
`anchor_budget > 0`. Every knob moves *how much of what, when* — never *whether it plays*.
`tests/test_bc23_knobs.nim` proves each knob has teeth and `tests/test_bc23_survival.nim` proves the
floor holds, **with a negative control that must fail** (§Tests items 16, 17).

| field | type / values | default | what it changes (`src/battlecode/years/bc23/chassis/…`) |
|---|---|---|---|
| `opening` | `launcher_rush` \| `carrier_eco` \| `balanced` | `balanced` | `econ.nim plan()` — the resource split for the first 400 rounds. `launcher_rush`: every kg of mana goes to launchers, carriers capped at 3 per headquarters, the spearhead leaves for the enemy's nearest headquarters at round 1. `carrier_eco`: 6 carriers per headquarters and the first launcher only once two wells are worked, but **launchers are still built** — the census target is halved, never zeroed. `balanced`: 4 carriers per headquarters and a launcher whenever mana allows. |
| `launcher_ratio` | int **20 … 80** | 45 | `econ.nim nextBuild()` — the percentage of *build decisions* that resolve to a launcher once the carrier floor is met; the remainder go to carriers and (per `amplifier_use`) amplifiers. Clamped to the range, so no doctrine can express "no launchers" (20 % of a real build stream is still a fighting force) or "only launchers" (the carrier floor is unconditional). |
| `well_priority` | `adamantium` \| `mana` \| `balanced` | `balanced` | `carrier.nim wellTarget()` — which well a free carrier walks to. Adamantium buys carriers (50), amplifiers (30) and half of a standard anchor; mana buys launchers (45), amplifiers (15) and the other half. `balanced` alternates by the deficit against `econ.nim`'s plan. **The idea's candidate value `elixir` is deliberately NOT a value here**: no official map contains an elixir well at round 0 (measured across all 103), elixir exists only by transforming a well, and that transformation is exactly what `elixir_tech` governs — a third value here would be a second, conflicting control of one decision. Logged as a design decision, not a gap. |
| `elixir_tech` | `never` \| `mid` \| `early` | `mid` | `elixir.nim program()` — whether and when the faction converts a well to elixir by pouring **600 kg of the opposite resource** into it. `never`: the 600 kg is spent on units and anchors instead. `mid`: begin once the round is past 500, the faction has ≥ 20 robots and ≥ 2 wells are being worked — `vrangr1`'s `ElixirProducer.shouldProduceElixir` gates **minus its `MAP_SIZE > 1000` test**, which is dropped deliberately: the `small` pool's maps are 400 tiles, and keeping that gate would make this knob and `elixir_spend` dead on a third of the map set, which the anti-inert rule forbids. `early`: begin at round 200 regardless, which costs roughly 13 launchers' worth of mana up front. The target is the mana well closest to one of our own headquarters and furthest from theirs; deposits go in 40 kg carrier-loads. |
| `elixir_spend` | `accelerating_anchors` \| `boosters` \| `destabilizers` | `accelerating_anchors` | `elixir.nim sink()` — what the elixir buys once it flows: 300 kg accelerating anchors (750 anchor HP instead of 250, and −15 % cooldowns for every ally within r² ≤ 4 of the island), 150 kg boosters (−10 % over a 20-unit patch for 10 rounds, stacking three deep), or 200 kg destabilizers (+10 % on the enemy over a 15-unit patch, then 50 damage). Under `elixir_tech: never` this knob has nothing to spend — that is the *doctrine's own* choice, not a dropped field: the value is still recorded and the viewer's plain-words panel says "no elixir programme, so its sink never opens". |
| `anchor_round` | int **1 … 1800** | 400 | `anchors.nim schedule()` — the first round at which a headquarters will spend 80 Ad + 80 Mn on a standard anchor. Early anchoring wins the tiebreak rungs and starts the conquest clock; late anchoring buys launchers first. |
| `anchor_budget` | int **0 … 100** | 35 | `anchors.nim budget()` — the percentage of *income* reserved for anchors and the carriers that ferry them (a ferrying carrier must be empty, so an anchor costs a carrier round-trip as well as 160 kg). At 0 the faction never anchors and plays for the deeper rungs and a launcher win — a real strategy on a 4-island map, and still a fully playing faction. |
| `island_priority` | `nearest` \| `contested` \| `safe` | `nearest` | `anchors.nim pick()` — which island the next anchor goes to. `nearest`: fewest BFS steps from the building headquarters. `contested`: the island whose anchor health is lowest or which the enemy holds (an enemy anchor must be ground to 0 by occupancy before we can plant). `safe`: the island furthest from every enemy headquarters and sighting, i.e. the one a garrison can actually hold. |
| `amplifier_use` | `never` \| `one` \| `escort` | `one` | `amplifier.nim plan()` — amplifiers cost 30 Ad + 15 Mn and are the only way a robot away from a headquarters (r² ≤ 9) or one of our islands (r² ≤ 4) can **write** the shared array. `never`: none, and the chassis routes its writers past headquarters and islands instead. `one`: one per headquarters, parked at the midpoint between it and the frontier. `escort`: one amplifier per launcher group of four, moving with it, which is what makes a distant duel co-ordinated. |
| `destabilizer_use` | `hold` \| `defend` \| `siege` | `defend` | `micro.nim commit()` — where the faction's **strike group** goes: its destabilizers when it has elixir, otherwise its launcher spearhead. `hold`: sit on our own wells and islands. `defend`: intercept anything sensed inside our own half. `siege`: push to the enemy's nearest headquarters or held island and stay there. No value is idle — `hold` still fights whatever comes. |
| `retreat_on_launcher_loss` | `never` \| `regroup` \| `home` | `regroup` | `micro.nim retreat()` — the year's signature knob, straight from the idea. When a launcher group loses a member in one round: `never` presses on; `regroup` pulls back to the group's centroid until the group is at strength again; `home` withdraws to the nearest friendly headquarters or anchored island (where the anchor heals 4 or 6 HP a round — the only healing in the game). |
| `carrier_throw` | int **0 … 100** | 25 | `carrier.nim throwPlan()` — how willing a loaded carrier is to throw its cargo (`floor(5m/4)` damage, up to 50, and the cargo is destroyed even on a miss, off the team total). At 0 a carrier never throws and dies with its load; at 100 it throws at any enemy in r² ≤ 9. The chassis always throws when the throw would **kill** and the carrier is within r² ≤ 9, at every setting, because refusing a free kill is not a strategy. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — the launcher duel against the
elixir/anchor economy — so the league's headline matchup is the question this year never got asked.

- **champion #1, `battlecode-bc23-duel` (daveey)**: *"You command a faction in Battlecode 2023
  'Tempest'. History says this year is decided by the opening launcher duel: a launcher costs 45 kg of
  mana, hits any square within 16 units for 20 damage even through clouds, and nothing else in the
  game deals real damage. Your doctrine: win that duel and never give it back. Set opening
  \"launcher_rush\", launcher_ratio high (65-80), well_priority \"mana\", elixir_tech \"never\" — 600 kg
  of adamantium poured into a well is thirteen launchers you did not build. Set destabilizer_use
  \"siege\" so your spearhead sits on their nearest headquarters, retreat_on_launcher_loss \"never\" or
  \"regroup\", amplifier_use \"escort\" so a group four squares deep in their half still shares targets,
  and carrier_throw high (60-100): a full carrier throws for 50 damage, which is two and a half
  launcher hits, and the cargo is lost anyway if it dies. Keep anchor_budget low (0-20) but set
  anchor_round somewhere before 1200 and island_priority \"nearest\" — if neither side conquers 75% of
  the islands, round 2000 is decided first on islands held and then on anchors ever placed, so a
  faction with zero anchors can lose a game it dominated. In notes, say which enemy headquarters you
  break first and what you do if the duel is even at round 600."*
- **champion #2, `battlecode-bc23-alchemist` (daveey-1)**: *"You command a faction in Battlecode 2023
  'Tempest'. You win outright by anchoring 75% of the sky islands, and every anchor you ever place is
  the second tiebreak at round 2000. Your doctrine: the islands and the elixir nobody used. Set
  opening \"carrier_eco\" or \"balanced\", well_priority \"balanced\", anchor_round early (100-350) and
  anchor_budget high (45-70): a standard anchor is 80 kg of adamantium and 80 kg of mana, it has 250
  health, and each round its health moves by the percentage of the island your robots occupy minus
  theirs — so an anchor without a garrison is a loan, not a purchase. Set island_priority \"safe\" or
  \"contested\" and say which. Set elixir_tech \"early\" or \"mid\" and elixir_spend
  \"accelerating_anchors\": pour 600 kg of adamantium into a mana well and it becomes an elixir well;
  300 kg of elixir buys an accelerating anchor with 750 health that also cuts the cooldowns of every
  ally within 4 units of the island by 15% and heals them 6 a round. Keep launcher_ratio in the middle
  (35-50) and destabilizer_use \"defend\" — you are not trying to win the duel, you are trying to
  survive it while your islands tick. Set retreat_on_launcher_loss \"home\" so wounded launchers heal on
  your own islands, and amplifier_use \"one\". In notes, say which islands you intend to hold at round
  2000 and how many carriers are garrisoning them."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the constant tables (the six unit types, the two anchors, the well economy, the
cooldown-multiplier arithmetic, the shared-array write rule), the map cards for all three games with
their island counts and `islands_to_win`, the scoring formula, the alias pair, a **HOW A GAME ENDS**
section (the bc21 r1-F8 fix, kept), and the reply contract ("reply with ONE JSON object; your reply
must begin with `{`"). The assistant turn is prefilled with `{` and the prefix re-attached before
parsing (the procgen 0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`). It gains a `bc23`
arm with two published names. **The manifest still declares only `awu` and `scaffold`** — the two ids
the certification fixture seats — and `PLAYER_SCRIPTED` resolves per year, exactly as bc20, bc21, bc24
and bc25 do:

| `PLAYER_SCRIPTED` | on `year: "bc23"` resolves to |
|---|---|
| `awu`, `lemonade`, or anything unrecognised | **`lemonade`** — the strong published doctrine and the champion chassis |
| `scaffold`, `examplefuncsplayer`, `examplefuncsplayer23`, `example` | **`examplefuncsplayer23`** — the deliberately weak floor and the oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field (D1).
`defaultBaselineFor("bc23")` is `lemonade`, so a seat that says nothing useful plays the strong
doctrine, not the weak floor. `Baseline` gains `blLemonade = "lemonade"` and
`blExamplefuncsplayer23 = "examplefuncsplayer23"`; `ScriptedChassis` gains `scLemonade = "lemonade"`
and `scExamplefuncsplayer23 = "examplefuncsplayer23"`.

**`lemonade` — the strong baseline and the champion chassis.** Behaviour ported from
`awesomelemonade/Battlecode2023` `src/finalBot/` (AGPL-3.0, head `2e231f31`; the 1st-place bot
"Producing Perfection", whose `finalBot` directory is the final submission), with the **elixir
programme** from `vrangr1/BattleCode2023` `src/AFinalsBot/ElixirProducer.java` + `BotBooster.java` +
`BotDestabilizer.java` (AGPL-3.0, head `244af40e`; 4th place — and the only published bot of the three
that actually ran the elixir tree), and the shared-array layout and symmetry guesser from
`jmerle/battlecode-2023` `src/camel_case_v30_final/util/` (MIT, head `e776fcb2`) — all parameterised
by the twelve knobs. Its scripted reply is the all-defaults sheet. Algorithm, by file:

- **`kit.nim`** — the per-side memory every robot shares: the remembered map (passability, clouds,
  currents, well type/rate, island id/owner/anchor health, last-seen round per tile), the enemy
  headquarters guess by map symmetry (`jmerle/util/Symmetry.java` behaviour: three candidate
  reflections, eliminated as tiles are sensed), the island claim table, and the navigator — a bounded
  BFS over the sensed window plus the remembered map with chunk checkpoints
  (`finalBot/pathfinder/BFSVision` + `Checkpoints` behaviour), falling back to a greedy step with a
  6-tile no-repeat history to break oscillation, and two bc23-specific tiebreaks: **prefer a current
  that pushes you toward the target** (a free square of movement with no cooldown) and **avoid a cloud
  unless the destination is a cloud** (a cloud costs 20 % on every cooldown and blinds you to 4 units).
  Every node expanded is charged against `DecisionOps`.
- **`econ.nim`** — the build plan: `plan()` (from `opening`), `nextBuild()` (from `launcher_ratio` and
  the carrier floor), `budget()` (from `anchor_budget`), and the per-headquarters commitment ledger, so
  two headquarters cannot promise the same 160 kg. It is the only place a resource is ever committed.
- **`hq.nim`** — a headquarters' turn, and it uses **all five** of its actions when it can: build the
  anchor `anchors.nim` has scheduled, then build the unit `econ.nim` asks for at the free passable tile
  nearest the frontier (never on a well, never boxing itself in), then write the census and the anchor
  claim to the shared array (a headquarters may always write).
- **`carrier.nim`** — mine, ferry, throw: walk to the well `well_priority` names (preferring an
  upgraded well at rate 3, and a well that our own launchers cover), collect until full or until the
  cooldown makes another trip better, deposit at the nearest friendly headquarters, and — when
  `anchors.nim` has an anchor waiting and this carrier is **empty** — take it and ferry it under escort.
  `throwPlan()` implements `carrier_throw`, always taking a lethal throw inside r² ≤ 9.
- **`launcher.nim` + `micro.nim`** — the duel. `micro.nim` is the port of `finalBot/LauncherMicro`
  behaviour: attack the lowest-HP enemy inside r² ≤ 16 (tiebreak toward launchers, then destabilizers,
  then carriers holding an anchor, then carriers, then amplifiers, then boosters), prefer a target our
  20 damage will kill, keep the cooldown-adjusted stand-off distance when the enemy's group is bigger,
  and honour `destabilizer_use` for where the group lives and `retreat_on_launcher_loss` for what it
  does when it starts losing.
- **`anchors.nim`** — the island programme: `schedule()` (from `anchor_round` and `budget()`),
  `pick()` (from `island_priority`), the garrison model (an island of area `a` needs
  `ceil(a × diff/100)` more of our robots than theirs standing on it to hold its anchor at full
  health — the arithmetic is the engine's own occupancy formula, run forward), and the escort request
  to `micro.nim`.
- **`elixir.nim`** — `program()` and `sink()`, per `elixir_tech` and `elixir_spend`: choose the target
  well, route 40 kg adamantium loads into it until it flips, then spend the elixir on the named sink and
  place boosters/destabilizers where `micro.nim` says the fight is.
- **`amplifier.nim`** — placement per `amplifier_use`, and the write-window test (`amplifier r² ≤ 20`,
  `headquarters r² ≤ 9`, `own island r² ≤ 4`) that every other module calls before it tries to write.
- **`comms.nim`** — the 64-slot shared array layout, 16 bits a slot, ported from `jmerle/util/SharedArray`
  and `vrangr1/Comms` behaviour: slots **0–3** our headquarters (packed `x:6 y:6 flags:4`), **4–15**
  known wells (`x:6 y:6 type:2 upgraded:1 taken:1`), **16–27** islands (`id:6 owner:2 healthBucket:4
  claimed:1`), **28–35** enemy sightings with a 4-bit age, **36–39** the elixir target and its progress
  bucket, **40–47** rally points, **48–55** anchor claims, **56–63** the per-type census. A slot is
  written only by a robot inside a write window, and every write is charged 1 `DecisionOps`.

**`examplefuncsplayer23` — the weak floor and the parity oracle's other side.** Ported
**statement-for-statement** from
`battlecode23/example-bots/src/main/examplefuncsplayer/RobotPlayer.java`: a headquarters builds a
standard anchor whenever it can afford one, then on `rng.nextBoolean()` tries a carrier or a launcher
in a random one of the eight directions; a carrier, **if it is holding an anchor**, walks to the first
island location it senses and plants it (dead code in practice — the bot never calls `takeAnchor`, so
its carriers never hold anchors, which is measured below), then tries to collect from each of the nine
tiles around it on a coin flip, throws at `enemyRobots[0]` on `rng.nextInt(20) == 1`, steps toward
`wells[1]` on `rng.nextInt(3) == 1`, and finally moves in a random direction; a launcher attacks the
square one step EAST of itself (yes — the upstream bot's `toAttack` is
`rc.getLocation().add(Direction.EAST)`, not the enemy it just sensed) and then moves randomly. It seeds
its own `java.util.Random(6147)` and never calls `Math.random()`, so — as in bc24 and bc25 — **it needs
no determinism patch and the oracle's Java side is upstream's file byte for byte**. The eight
`directions` are NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH, SOUTHWEST, WEST, NORTHWEST **in that
order**, because `rng.nextInt(8)` indexes it, and one subtlety must be ported exactly: the anchor
branch collects island locations into a **`HashSet<MapLocation>`** and takes `iterator().next()`, whose
order depends on `MapLocation.hashCode() = (y + 0x8000) & 0xffff | (x << 16)` and on `HashSet`'s table
size — so `scaffold23.nim` reproduces Java's `HashSet` bucket order for that one call site, and
`tests/test_bc23_scaffold.nim` pins it against a recorded oracle trace. **It may not gain behaviour:
it is one side of the differential oracle.** Its scripted reply is the all-defaults sheet (it reads no
knob).

Both replies go through the **same** `validate` the LLM path uses, which is what makes the
bounded-orders test meaningful and an LLM doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `lemonade` chassis, `results.fallbacks[seat] = 1`, a **`doctrine_fallback` event** names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default; the rest of the sheet applies |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| a side takes 2 games | the episode settles immediately — no padding (§The game, clinch semantics) |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `lemonade` baseline reply, and it is exactly the
all-defaults sheet:

```json
{"sheet":{"opening":"balanced","launcher_ratio":45,"well_priority":"balanced",
          "elixir_tech":"mid","elixir_spend":"accelerating_anchors",
          "anchor_round":400,"anchor_budget":35,"island_priority":"nearest",
          "amplifier_use":"one","destabilizer_use":"defend",
          "retreat_on_launcher_loss":"regroup","carrier_throw":25},
 "notes":"default lemonade doctrine","motto":"Anchor the sky."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc23/constants.nim` | **new, generated** | every `GameConstants` value plus the whole `RobotType` and `Anchor` tables, emitted by `tools/gen_year_constants.py --year bc23` from the pinned battlecode23 checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc23/world.nim` | **new** | world state: passability, clouds, currents, the well array, the island array and island records, the robot table, the **exec-order list**, per-tile per-team cooldown multipliers and their boost/destabilise lists, the two 64-slot shared arrays, team stockpiles, and every action of rule 3.2 |
| `src/battlecode/years/bc23/rules.nim` | **new** | the four-step round loop, the end ladder, the points formula |
| `src/battlecode/years/bc23/units.nim` | **new** | the `RobotType` table, cargo weight and capacity, `addHealth`/destroy (headquarters immune), the carrier movement-cooldown and throw-damage functions, the cooldown-multiplier application |
| `src/battlecode/years/bc23/islands.nim` | **new** | island records (id, tiles, owner, anchor type, anchor health), `advanceTurn` with the occupancy formula and the healing sweep, `placeAnchor` with the **mid-turn** float32 conquest check, and the accelerating-anchor boost registration/removal |
| `src/battlecode/years/bc23/wells.nim` | **new** | well type, swallowed-inventory bookkeeping, the 600 kg elixir transformation and the 1400 kg rate upgrade, `collect`/`transfer` |
| `src/battlecode/years/bc23/tempo.nim` | **new** | the time-bending layer: per-tile per-team multipliers in **integer hundredths**, boost/destabilise lists with the engine's asymmetric stack guards, the end-of-round expiry sweep and the destabiliser detonation, and the cloud constant baked in at world construction |
| `src/battlecode/years/bc23/currents.nim` | **new** | `applyCurrents` — forecast, immediate blocking, the transitive closure, the lift-and-set-down — as a deterministic worklist (D3) |
| `src/battlecode/years/bc23/comms.nim` | **new** | the two 64-slot shared arrays, the write-window predicate (amplifier r² ≤ 20 / headquarters r² ≤ 9 / own island r² ≤ 4, and "a headquarters or an amplifier may always write"), and the value range check |
| `src/battlecode/years/bc23/maps.nim` | **new** | the converted bc23 pool, the loader, the per-episode draw (`drawMaps`, `sideAslotFor`) |
| `src/battlecode/years/bc23/knobs.nim` | **new** | the twelve-knob `Doctrine23` type, defaults, per-field repair, `toJson`, `plainWords` |
| `src/battlecode/years/bc23/chassis/*.nim` | **new** | `lemonade.nim`, `scaffold23.nim`, `scenario23.nim`, `kit.nim`, `econ.nim`, `hq.nim`, `carrier.nim`, `launcher.nim`, `micro.nim`, `anchors.nim`, `elixir.nim`, `amplifier.nim`, `comms.nim` |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc23", title: "Battlecode 2023 — Tempest", maxRounds: 2000, pools: @["small","mixed","large"], atlas: "atlas_bc23")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc23`; `Session` gains a `yBc23` branch (`w23`, `sides23`, `chassis23`); `yearIdOf`/`strongChassisFor`/`parseScriptedChassis`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson23`. `Bc23ActionNames = ["move","build_robot","build_anchor","attack","throw","destabilize","boost","collect","transfer","withdraw","take_anchor","return_anchor","place_anchor","write_array","disintegrate"]` is added beside the other years' name tables so `first_action.kind` has a documented vocabulary (the r1-F14 lesson) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV09`, `ReplayCompatibleGameVersions` → `["GV04","GV05","GV06","GV07","GV08", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scLemonade` and `scExamplefuncsplayer23` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc23` arm in `defaultBaselineFor` and `baselineFor`; `blLemonade` and `blExamplefuncsplayer23` added to `Baseline`; `baselineChassis` and `baselineReply` map them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc23`, `doctrine23` on `Sheet`, a `knownKeysFor` arm, a `defaultSheet` field — exactly the four-line shape bc21, bc24 and bc25 added |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc23 adds the terrain layer (passable/impassable, clouds, current arrows), wells with type and rate, island tiles tinted by owner with an anchor-health ring, the six unit sprites at two team palettes, cargo pips on carriers, an anchor badge on a ferrying carrier, and boost/destabilise field tinting |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc23 scorebug / feed / endcard shell records **and the bc23 arms of `beatsFor`** (§Viewer, "the beat contract") |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port (`nextInt()`, `nextInt(bound)`, `nextBoolean()`) and `IdGenerator` already carry everything bc23 needs |
| `data/maps/bc23/*.json` | **new, committed** | 22 converted maps |
| `data/bc23/tables.json` | **new, committed** | the whole finite arithmetic domain (below) |
| `data/atlas_bc23.png` / `.json` | **new, committed** | the 2023 sprite atlas |
| `tools/convert_maps_bc23.py` | **new** | reads `.map23` and writes `data/maps/bc23/<name>.json` |
| `tools/map_pools_bc23.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc23.py` | **new** | cuts `atlas_bc23.*` from the 2023 client sprites |
| `tools/gen_year_constants.py` | **`--year bc23` added** | reads the 2023 `GameConstants.java` + `RobotType.java` + `Anchor.java` |
| `tools/JavaBc23Tables.java` | **new, CI-only** | regenerates `data/bc23/tables.json` under the CI **JDK 8** straight out of the released jar's own classes |
| `tools/oracle/bc23/Bc23Trace.java` | **new, CI-only** | the trace driver (§Tests) — one file, compiled against the released jar |
| `tools/oracle/bc23/bc23scenario/RobotPlayer.java` | **new, CI-only** | the scenario bot that makes the rare paths bit-exact (§Tests) |
| `tools/oracle/bc23/examplefuncsplayer23/RobotPlayer.java` | **new, CI-only** | upstream's example bot, **byte for byte, no determinism patch** |
| `tools/oracle/bc23/build_oracle.sh` | **new, CI-only** | sha256-verifies the jar and compiles the driver + both bots |
| `tools/oracle/bc23/jar.lock` | **new, CI-only** | the oracle jar's URL, size and sha256 |
| `tools/parity_trace_bc23.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc23.py` | **new** | the tier comparison and the ledger check (the bc25 script, two years back) |
| `tools/ci/parity_ledger_bc23.json` | **new** | the accepted-divergence ledger |
| `tools/gen_bc23_fixture_replay.nim` + `tests/fixtures/replay-bc23.json` | **new, committed** | the fixture replay the wasm smoke and the beat test load |
| `tests/bc23_fixture.nim` | **new** | the shared fixture builder, beside `bc24_fixture.nim` and `bc25_fixture.nim` |
| `docs/RULES-BC23.md` | **new** | the year's rules, knobs and the full §Divergences list |

**A layout rule, written here because the bc24 run paid a fixer commit for its absence.** The file
list above is the intended layout and `NOTICE`, `knobs.nim`'s doc comments and `docs/RULES-BC23.md`
all point at it. If the builder merges two of these modules — for example folds `currents.nim` into
`world.nim` — it must update **every one of those three pointers in the same commit**, and add a
`docs/RULES-BC23.md` §Divergences item recording the merge. A licence file that credits derived
behaviour to a path that does not exist is a defect, not a cosmetic slip.

### Determinism

- **`rng.nim` is reused unchanged, and bc23 needs almost none of it.** The **only** randomness in a
  2023 game is `IDGenerator(map.getSeed())` — the 48-bit LCG, `nextInt(bound)` with both the
  power-of-two shortcut and the rejection loop, 4096-id blocks from 10 000, Fisher–Yates per block —
  which fixes the id of every robot ever built, and `Math.random()` inside `setWinnerArbitrary`.
  `GameWorld.rand` and `RobotControllerImpl.random` are both constructed from the map seed and
  **never read**; the port does not create them. The example bot's own `Random(6147)` stream is
  reproduced call for call by `scaffold23.nim`, including `nextBoolean()` and `nextInt(20)`.
- **Robot ids are load-bearing.** The initial headquarters use the ids in the map file (below the
  10 000 floor, and `LiveMap` sorts them ascending, which fixes the initial exec order) and every
  robot built during the game draws the next `IDGenerator` id, in build order. Ids do not decide turn
  order (the exec-order list does) but they decide the port's ascending-id sweeps (D1) and they appear
  in the trace, so the generator must be bit-exact. It already is: `tests/test_rng.nim` covers it and
  bc20/bc21/bc24/bc25 rely on the same code.
- **Five determinism divergences, each with its written argument.** All five are in
  `docs/RULES-BC23.md` §Divergences:
  - **D1 — `ObjectInfo.eachRobot` is a trove hash-order sweep; the port sweeps in ascending id.**
    Two sites use it. `processBeginningOfRound` only clears the indicator string, which this port does
    not have, so that site is a **no-op** and order cannot matter. `processEndOfRound` does two things
    per headquarters: deal 4 damage to every enemy within r² ≤ 9, and (every fifth round) add +6/+6 to
    its own stockpile and the team total. Resource addition is commutative. The damage is
    order-independent in outcome because each headquarters deals its 4 to each enemy in range exactly
    once and a robot that dies mid-sweep is simply gone — the final health of every robot, and the set
    of dead robots, is the same under any order (a robot on `4k` HP with `k` headquarters in range dies
    under every order; the resource refund of a destroyed carrier is likewise commutative). Written
    down here so nobody re-derives it under time pressure.
  - **D2 — `islandIdToIsland.values()` is a HashMap sweep; the port iterates ascending island id.**
    `Island.advanceTurn` reads only its own tiles and writes only its own anchor state, and its healing
    is `min(maxHealth, health + amount)` applied to robots — which commutes, because the cap is the same
    value regardless of order and healing cannot kill. `numIslandsOccupied` and the ladder's island count
    are order-free sums.
  - **D3 — `applyCurrents`'s `HashMap`/`HashSet` iteration is replaced by a deterministic worklist.**
    The blocked set is the transitive closure of "forecast onto a tile whose occupant is not moving",
    and because at most one robot occupies a tile, the engine's `visited`-by-location guard makes the
    closure a well-defined fixed point independent of iteration order. The port computes it with a
    FIFO worklist over robot ids ascending, then moves the survivors. **Measured**: on all 103 official
    maps no current flows into a wall or off the map and no two currents share a target, so the only
    real driver of blocking is robots blocking robots.
  - **D4 — `setWinnerArbitrary`'s `Math.random()`** is replaced by a draw from a world RNG seeded from
    the map's `randomSeed` (reachable only when islands, anchors, elixir, mana **and** adamantium are all
    tied at round 2000).
  - **D5 — one fidelity requirement, not a divergence:** the example bot's `HashSet<MapLocation>`
    iteration order (§Decisions) is reproduced rather than replaced, because that bot is one side of the
    differential oracle.
- **The scan order is load-bearing and is ported literally**: `getAllLocationsWithinRadiusSquared` is
  `ceiledRadius = ceil(sqrt(r²)) + 1` (**note the `+ 1`**), then **x ascending outer, y ascending
  inner**, clamped to the map, keeping tiles with `dx² + dy² ≤ r²`. It fixes which enemy a
  headquarters' end-of-round damage reaches first, the order tiles are pushed onto boost and
  destabilise lists, the order `senseNearbyRobots`/`senseNearbyWells`/`senseNearbyMapInfos` return, and
  the whole-map sweep (`getAllLocations()` is the same function with `Integer.MAX_VALUE`). `ceil(√r²)`
  is over the finite set `{4, 9, 13, 15, 16, 20, 34}` and is **precomputed as a table**, so the port
  needs no `sqrt` and no `fdlibm` path at all.
- **The arithmetic is integer everywhere except four places, and all four have a finite domain.**
  1. **The cooldown multiplier.** The port stores it as **integer hundredths** per tile per team
     (`1.0` → `100`, cloud `+20`, boost `−10`, destabilise `+10`, accelerating anchor `−15`), which is
     bit-identical to the engine's `Math.round(x*100.0)/100.0` accumulation over its whole reachable
     range, and it applies a cooldown as **`round(base × (hundredths / 100.0))` evaluated in float64
     exactly as Java does** — `hundredths/100.0` first, then the multiply, then `Math.round` =
     `floor(x + 0.5)`. This matters: for `base = 5, hundredths = 70` the real value is 3.5, but the
     float64 product is 3.4999999999999996 and Java rounds it to **3**, where an integer
     `(base*h + 50) div 100` would give 4. Reproducing the float64 ops is therefore mandatory, and
     Tier B tables the **entire** lattice (every reachable multiplier × every base cooldown in
     `{2, 10, 15, 20, 25, 70, 140}` and every carrier base 5…20).
  2. **The carrier movement cooldown** `floor(0.375f × weight) + 5` — exact in float32 for
     `weight ≤ 40` (0.375 = 3/8), tabled for all 41 weights: 0→5 … 8→8 … 20→12 … 40→20.
  3. **The carrier throw damage** `floor(1.25f × weight)` — exact (1.25 = 5/4), tabled for all 41
     weights: 4→5, 20→25, 40→50.
  4. **The conquest threshold** `((float) held) / islandCount >= 0.75f` — a genuine float32 division,
     tabled for every island count 4…35 (§The game).
  Everything else — health, resources, cargo weight, anchor health, the island occupancy formula
  (Java integer division **truncating toward zero**, which Nim's `div` matches for negative numerators)
  — is integer. **There is no transcendental anywhere in bc23**, which is why this year's arithmetic
  tier is provable over its whole finite domain (§Tests, Tier B).
- Every round appends to a **hash chain**; the viewer re-derives each round and compares, exposing
  `bc_mismatch_round`. The values folded into the bc23 chain each round: per team — islands held,
  anchors ever placed, anchors currently held, adamantium, mana, elixir, robots alive by each of the
  six types, total robot HP, total cargo weight, anchors in headquarters' inventories; plus globally —
  the round number, an FNV-1a 64 hash of the island array (id, owner, anchor type, anchor health, in
  ascending island id), an FNV-1a 64 hash of the per-tile per-team multiplier hundredths (y ascending
  outer, x ascending inner), an FNV-1a 64 hash of every well's swallowed inventory and rate, an
  FNV-1a 64 hash of both shared arrays, and the exec-order list length.
- Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
  (`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
  scar — and the record→re-derive test covers **every** bc23 end reason, not just `complete`.
- **`GameVersion` bumps to `GV09`** in the same commit, with a prepend-only changelog line ("bc23 year
  module added; bc26, bc20, bc21, bc24 and bc25 semantics unchanged").
  **`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06","GV07","GV08", GV09]`** — it is
  *extended*, never reset: nothing a GV04–GV08 recording carries changed meaning, so every hosted
  replay keeps rendering. `tools/ci/check_gameversion.sh` is kept and claims the version across
  branches; **it compares the headline, not the digits, so if a sibling branch lands GV09 first this
  branch rebases to GV10 and extends the list again** (the bc20 precedent).

### The chassis, and the bytecode divergence

The engine's per-robot **bytecode limits** (`HEADQUARTERS` 20 000, `CARRIER` 12 500, everything else
10 000) have no meaning outside the JVM instrumenter. They are replaced by a **fixed per-robot
`DecisionOps` budget of 2 000 (headquarters), 1 250 (carrier) and 1 000 (launcher, destabilizer,
booster, amplifier)** — one tenth of the Java limits, the same convention bc20, bc21, bc24 and bc25
use. One credit is charged for each: tile sensed, robot examined in a sense sweep, BFS node expanded,
direction evaluated, shared-array slot read or written, well or island candidate scored, and micro
target scored. Credits are deducted inside `kit.nim` and **enforced by the sim, not by the bot**.
`EXCEPTION_BYTECODE_PENALTY` has no port: a Nim chassis raises nothing.

Two properties make this safe and both are stated so nobody has to rediscover them:

- **The budget is checked *before* each primitive and never inside one.** A navigation BFS, an island
  occupancy evaluation or a sense sweep either runs to completion or does not start. So a primitive's
  *result* is never a function of the remaining budget, only *whether the chassis got to ask*. When the
  budget reaches zero the robot's turn ends where it stands — it is **not** resumed mid-computation next
  turn, which is the one place this differs from the JVM.
- **And in bc23 the divergence is provably not exercised by the oracle.** Measured in this sandbox over
  three full 2000-round games (`DefaultMap` 32×32, `AllElements` 30×30, `Eyelands` 50×30), the **peak
  bytecode use of any robot on any round was 823–856 — 6.6–6.9 % of the carrier's 12 500 limit — with
  no mid-turn cut-off at all**. So the Tier A bit-exact window for bc23 is the **whole game**, and the
  parity job asserts that rather than assuming it: if any robot ever exceeds **50 %** of its limit the
  job fails loudly, because past that point the comparison stops being defined (§Tests). This is the
  opposite of bc21, whose windows were 22–245 rounds because its example bot *did* hit the ceiling — and
  it is why this note can promise an empty ledger where bc21's could not.

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to Java
bytecode granularity needs either a Nim-level instrumenter (a compiler project) or a hand-annotation
of every statement against `MethodCosts.txt`, and neither buys anything the budget does not — the
chassis are ours and are written to fit the budget.

### Maps

**22 of the 103 official maps** are converted and committed. **Every one of the 103 was parsed** with
the reader `tools/convert_maps_bc23.py` implements, and the table below is those measurements, not
assumptions (flatbuffers schema `GameMap`: `name`, `minCorner`, `maxCorner`, `symmetry`
`0=rotation|1=horizontal|2=vertical`, `bodies` (a `SpawnedBodyTable` of ids, teams, types and
locations), `randomSeed`, `walls[]`, `clouds[]`, `currents[]` (a `DIRECTION_ORDER` index per tile),
`islands[]` (an island id per tile, 0 = none), `resources[]` (0 = none, 1 = Ad, 2 = Mn, 3 = Ex)).
`HQ` below is headquarters **per side**; `wells` is `adamantium/mana` (**no official map contains an
elixir well** — all 103 have zero, which is exactly why `elixir_tech` is a knob and not a map
property); `→win` is the islands needed for a conquest under the float32 threshold.

| pool | map | size | seed | symmetry | HQ | walls % | clouds | currents | islands | island tiles | wells | →win |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `small` | `Quiet` | 20×20 | 706 | rotation | 1 | 11.5 | 14 | 20 | 4 | 8 | 4/2 | 3 |
| `small` | `SmallElements` | 20×20 | 899 | rotation | 2 | 4.0 | 16 | 22 | 4 | 24 | 4/6 | 3 |
| `small` | `Lantern` | 20×20 | 899 | vertical | 1 | 11.5 | 50 | 12 | 4 | 24 | 2/2 | 3 |
| `small` | `Spin` | 20×20 | 182 | rotation | 1 | 4.5 | 218 | 50 | 4 | 20 | 2/2 | 3 |
| `small` | `Sneaky` | 20×20 | 527 | rotation | 3 | 6.0 | 148 | 48 | 4 | 24 | 2/2 | 3 |
| `small` | `Barcode` | 20×20 | 95 | rotation | 2 | 31.5 | 112 | 12 | 7 | 58 | 2/2 | 6 |
| `mixed` | `AllElements` | 30×30 | 524 | rotation | 2 | 4.4 | 22 | 26 | 6 | 36 | 6/6 | 5 |
| `mixed` | `DefaultMap` | 32×32 | 386 | rotation | 3 | 2.7 | 42 | 32 | 6 | 40 | 4/4 | 5 |
| `mixed` | `Cave` | 30×20 | 891 | rotation | 2 | 22.0 | 34 | 48 | 8 | 104 | 4/4 | 6 |
| `mixed` | `MoonPhases` | 27×25 | 736 | rotation | 2 | 10.7 | 36 | 8 | 8 | 86 | 2/4 | 6 |
| `mixed` | `Eyelands` | 50×30 | 451 | vertical | 2 | 10.3 | 8 | 82 | 4 | 76 | 8/6 | 3 |
| `mixed` | `Rectangle` | 50×30 | 753 | rotation | 2 | 8.0 | 96 | 80 | 4 | 44 | 6/6 | 3 |
| `mixed` | `Scatter` | 50×30 | 841 | rotation | 2 | 8.0 | 22 | 36 | 8 | 70 | 6/4 | 6 |
| `mixed` | `HideAndSeek` | 37×31 | 575 | rotation | 2 | 5.9 | 123 | 78 | 16 | 70 | 4/4 | 12 |
| `mixed` | `Rainbow` | 40×30 | 473 | vertical | 2 | 22.3 | 156 | 36 | 20 | 112 | 4/4 | 15 |
| `mixed` | `IslandHopping` | 60×30 | 210 | vertical | 2 | 6.2 | 24 | 70 | 8 | 124 | 4/4 | 6 |
| `large` (reserved) | `Spiderweb` | 45×45 | 914 | rotation | 2 | 4.4 | 305 | 372 | 16 | 318 | 6/6 | 12 |
| `large` | `ThirtyFive` | 48×47 | 748 | rotation | 3 | 71.5 | 54 | 68 | **35** | 232 | 6/6 | 27 |
| `large` | `Target` | 60×60 | 721 | rotation | 2 | 42.4 | 280 | 92 | 12 | 154 | 4/4 | 9 |
| `large` | `Spots` | 60×60 | 461 | horizontal | 2 | 14.7 | 620 | 176 | 8 | 142 | 8/8 | 6 |
| `large` | `Forest` | 60×60 | 781 | vertical | **4** | 5.8 | 976 | 120 | 7 | 128 | 6/4 | 6 |
| `large` | `Grievance` | 60×60 | 336 | rotation | 2 | 7.9 | 0 | 152 | 5 | 90 | 12/12 | 4 |

`mixed` (10 maps) is the `bc23` variant's pool; `small` (6) is the pool the parity oracle and the
docker smoke run on; `large` (6) is reserved for a later variant. The `mixed` pool is chosen to span
the axis the doctrines argue about: all three symmetries; 500 to 1 800 tiles; **islands from 4
(`Eyelands`, `Rectangle` — conquest needs 3, so one launcher push decides the game) to 20 (`Rainbow` —
conquest needs 15, so ferry logistics and garrisons decide it)**; **headquarters per side 2 and 3**
(three headquarters means five build actions × 3 per round and 600/600 at round 1); **cloud coverage
from 0.9 % (`Eyelands`) to 13 % (`Rainbow`)**, which is how much of the map blinds a launcher group;
and **current density from 8 tiles (`MoonPhases`) to 82 (`Eyelands`)**, which decides whether a
carrier's route home is a conveyor or a hazard.

Maps are excluded from v1 for stated reasons, all recorded in `docs/RULES-BC23.md`: everything above
1 800 tiles is out of the played pools for wall-clock reasons (six are converted anyway, under
`large`); `Marsh` (1 218 cloud tiles of 3 000, 40.6 %) and `BuildSite` (71.2 % walls) are converted for
neither pool because a map where most of the board blinds or blocks the fight makes every doctrine look
the same; and the remaining 81 are simply not converted in v1 — the converter handles any `.map23` and
`--parse-all` proves it against all 103 in CI.

`tools/convert_maps_bc23.py` writes `data/maps/bc23/<name>.json` carrying: `name`, `width`, `height`,
`random_seed`, `symmetry` (the map's own declared value, recorded and unused at runtime, exactly as the
engine does), `rounds`, `walls` (a `width × height` bit array), `clouds` (the same), `currents` (a
sparse `[x, y, dirIndex]` list over `DIRECTION_ORDER = [CENTER, WEST, NORTHWEST, NORTH, NORTHEAST,
EAST, SOUTHEAST, SOUTH, SOUTHWEST]`), `islands` (a sparse `[x, y, islandId]` list), `resources` (a
sparse `[x, y, type]` list over 1 = Ad, 2 = Mn, 3 = Ex), and `initial_bodies`
(`[id, x, y, team, type]` rows **sorted ascending by id**, because that is the order `LiveMap`'s
constructor imposes and therefore the initial exec order). The converted maps are **committed** and CI
re-converts and byte-diffs. The wasm bundle gets the same directory through the existing
`--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from
the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot
takes side A in game 1; sides alternate each game. Seed, map names and side assignment are recorded in
results and in the replay. Map files live under `data/maps/bc23/`, so a name shared with another year
(`Lantern`, `Jail`, `Maze`, `Cat`, `Heart`, `Flower`) cannot resolve to the wrong file;
`tests/test_bc23_maps.nim` asserts it anyway.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `sheet_common`, `sheet`,
`decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never branches on the
year except through `years/dispatch.nim`, whose `Session` is a Nim object **variant** so the compiler
refuses to build a half-added year. Adding 2023 is exactly what bc20, bc21, bc24 and bc25 proved
adding a year to be: a new `years/bc23/` directory, a converted map set, a sprite atlas, one registry
line, one arm per dispatch `case`, and one manifest variant. **Nothing else on `main` changes**: the
five shipped years' modules, maps, atlases, tests and manifest variants are untouched, and the shared
files this branch edits are enumerated in §Packaging. The replay header records `year` so a viewer can
never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol id
would force every existing bc26/bc20/bc21/bc24/bc25 consumer to re-register for no change in the
contract. Both `game.protocols.player` and `game.protocols.global` continue to point at
`docs/PROTOCOL.md`, which gains a bc23 section.

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
env var takes the active year's default baseline (`lemonade` on bc23). A seat whose registration never
arrives is logged loudly and reported to `COGAME_PLAYER_FAILURE_URI`. The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket (the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no
per-round observation of any kind.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV09","year":"bc23",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":871345,
 "games":[{"map":"Rainbow","width":40,"height":30,"symmetry":"vertical",
           "you_are":"A","rounds":2000,
           "islands":20,"islands_to_win":15,"island_tiles":112,
           "island_sizes":[8,6,6,6,6,6,6,6,6,6,6,6,4,4,4,4,4,4,4,4],
           "your_headquarters":[{"x":6,"y":14},{"x":9,"y":22}],
           "enemy_headquarters":[{"x":33,"y":14},{"x":30,"y":22}],
           "start_separation":27.0,
           "terrain":{"impassable":268,"impassable_pct":22.3,
                      "clouds":156,"cloud_pct":13.0,"currents":36,
                      "adamantium_wells":4,"mana_wells":4,"elixir_wells":0},
           "nearest_well_to_you":{"type":"adamantium","x":8,"y":11,"steps":4},
           "nearest_island_to_you":{"id":3,"tiles":6,"steps":7}}],
 "economy":{"start_per_headquarters":{"adamantium":200,"mana":200},
            "passive_per_headquarters_every_5_rounds":{"adamantium":6,"mana":6},
            "well_rate":1,"upgraded_well_rate":3,
            "well_upgrade_cost_same_resource":1400,
            "well_to_elixir_cost_opposite_resource":600,
            "carrier_capacity":40,"anchor_weight":40,
            "note":"a resource thrown into a well leaves your team total for good"},
 "units":{"headquarters":{"hp":"indestructible","action_cd":2,"action_r2":9,"vision_r2":34,
                          "does":"builds robots and anchors (UP TO FIVE ACTIONS A TURN), stores resources, deals 4 damage to every enemy within r2<=9 at the end of every round"},
          "carrier":{"ad":50,"hp":150,"capacity":40,"action_cd":10,"action_r2":9,"vision_r2":20,
                     "move_cd":"floor(5 + 3*cargo/8) — a full carrier is half the speed of an empty one",
                     "does":"mines 1 (or 3 from an upgraded well) per action from a well it stands on or beside, carries resources and anchors, plants anchors, and can THROW its whole cargo for floor(5*cargo/4) damage — up to 50 — losing the cargo whether it hits or not"},
          "launcher":{"mn":45,"hp":200,"damage":20,"action_cd":10,"action_r2":16,"vision_r2":20,
                      "move_cd":20,
                      "does":"the only real attacker; hits any square within r2<=16, even a robot it cannot see"},
          "amplifier":{"ad":30,"mn":15,"hp":120,"action_cd":"none","vision_r2":34,"move_cd":15,
                       "does":"lets friendly robots within r2<=20 WRITE the shared array"},
          "destabilizer":{"ex":200,"hp":300,"damage":50,"action_cd":70,"action_r2":13,"move_cd":25,
                          "does":"marks a square: every tile within r2<=15 of it gives the ENEMY +10% cooldowns for 5 rounds, then deals 50 damage to whatever enemy stands there"},
          "booster":{"ex":150,"hp":400,"action_cd":140,"move_cd":25,
                     "does":"gives every ALLY within r2<=20 of where it stood -10% cooldowns for 10 rounds; stacks 3 deep; the patch does not follow the booster"}},
 "anchors":{"standard":{"ad":80,"mn":80,"health":250,"heals_allies_within_r2_4":4},
            "accelerating":{"ex":300,"health":750,"heals_allies_within_r2_4":6,
                            "cooldowns":"-15% for allies within r2<=4 of the island"},
            "how":"a headquarters builds it; an EMPTY carrier takes it (it weighs the carrier's whole capacity), walks onto an island tile and plants it",
            "holding":"every round an anchor's health moves by (percent of the island's tiles you occupy) - (percent they occupy), capped at its max; at 0 the island goes neutral and either side can plant",
            "override":"you may replace your OWN anchor (it returns to full health) but that does NOT count as a new anchor placed for the tiebreak"},
 "tempo":{"cloud":"+20% cooldowns and vision collapses to r2<=4 — both ways, so a robot in a cloud is also hidden",
          "stacking":"ADDITIVE on a per-tile, per-team multiplier: 1.00 +0.20 cloud -0.10 per boost (max 3) +0.10 per destabilise (max 2) -0.15 accelerating anchor",
          "applied":"round(base_cooldown * multiplier), read at the tile you end up on"},
 "comms":{"shared_array":64,"max_value":65535,
          "write_rule":"a headquarters or an amplifier may always write; any other robot needs a friendly amplifier within r2<=20, a friendly headquarters within r2<=9, or one of YOUR islands within r2<=4",
          "read_rule":"always","cost":"none"},
 "win":{"instant":"hold 75% of the sky islands (see islands_to_win per map)",
        "at_round_2000":["more islands held","more anchors ever placed","more elixir",
                         "more mana","more adamantium","coin flip"],
        "note":"there is NO elimination: headquarters cannot be destroyed and a side with no robots plays on to round 2000"},
 "rules_digest":"<~7 KB condensed spec: the six unit types and their exact actions, the well economy and both transformations, anchors and the occupancy formula, clouds and currents, the additive tempo multiplier, the shared-array write windows, the five-action headquarters, and the end ladder>",
 "sheet_schema":{"…all twelve knobs, their values, ranges and defaults…"},
 "scoring":{"weights":{"islands_share":60,"anchors_share":22,"elixir_share":10,
                       "mana_share":5,"adamantium_share":3},
            "win_bonus_per_game":200,"games":3,
            "note":"shares are float32; points truncate to an integer; the league ranks by scores, which the win bonus dominates"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with **both** factions'
headquarters positions (they are public: the maps are symmetric and the engine's own map file puts them
there), island count, island sizes and **the exact number of islands a conquest needs**, the terrain
and well aggregates, the walking distance to the nearest well and island, the seed, the full constant
tables, the knob surface with defaults, the scoring weights, the deadlines. Because every map is
symmetric, the two seats' cards are mirror images and numerically identical in every aggregate; the
only asymmetry is `you_are` and which mirrored coordinate set is labelled "yours".
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in
either direction, at any time); the opponent's real player name (only the alias); every in-match state
(a cog receives **no** per-round observation — one sealed doctrine, then the war); the other seat's
fallback status. Inside a match the fog is the robots': vision r² ≤ 34 for headquarters and amplifiers,
r² ≤ 20 for everyone else, **collapsing to r² ≤ 4 whenever either end of the sightline is a cloud**, and
the enemy's shared array is never readable. Everything else inside the radius is exact.

### Reply schema and caps

```json
{"sheet":{"opening":"carrier_eco","launcher_ratio":35,"well_priority":"balanced",
          "elixir_tech":"early","elixir_spend":"accelerating_anchors",
          "anchor_round":150,"anchor_budget":60,"island_priority":"safe",
          "amplifier_use":"one","destabilizer_use":"defend",
          "retreat_on_launcher_loss":"home","carrier_throw":10},
 "notes":"Islands 3, 7 and 11 are on my side of the vertical mirror; I garrison those six tiles with four carriers and convert the mana well at (8,11) by round 300.",
 "motto":"Anchor the sky, then argue."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES**, cut on a rune boundary | unparseable → retry once → fallback sheet |
| `sheet` | ≤ **32** keys, each value type- and range-checked | bad field → that field's default, recorded |
| `launcher_ratio`, `anchor_budget`, `carrier_throw` | integers, clamped to their stated ranges | out of range → clamped to the nearer bound and recorded (an integer knob is clamped, never defaulted, so "as much as possible" still means something) |
| `anchor_round` | integer **1 … 1800** | out of range → clamped; a non-integer → the default 400, recorded |
| every enum knob | exactly one of its listed strings, case-folded and trimmed | unknown value → that field's default, recorded |
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

The closed schema is **shared with the five shipped years** and stays that way: `results.games[]`'s
five required keys are year-neutral (`map`, `side`, `rounds_played`, `winner`, `end_reason`), every
year-specific statistic is an optional property, and `end_reason`'s enum is the union of every year's
values.

bc23's per-game keys, each a 2-array of integers in **seat** order unless marked scalar (the ones
already declared for another year — `units_built`, `damage_dealt`, `robots_alive`, `robots_lost` — are
reused rather than duplicated): `islands_held_end`, `islands_captured`, `islands_lost`,
`rounds_holding_any_island`, `anchors_built`, `anchors_placed`, `anchors_lost`,
`accelerating_anchors_placed`, `adamantium_end`, `mana_end`, `elixir_end`, `adamantium_mined`,
`mana_mined`, `elixir_mined`, `resources_thrown`, `resources_banked`, `wells_transformed`,
`wells_upgraded`, `carriers_built`, `launchers_built`, `amplifiers_built`, `destabilizers_built`,
`boosters_built`, `throw_damage`, `destabilize_damage`, `hq_damage`, `anchor_heals`, `array_writes`,
`boosts_cast`, `destabilizes_cast`, `carrier_rounds_loaded`, `current_rides`; scalars
`islands_on_map`, `islands_to_win`, `headquarters_per_side`, `cloud_tiles`, `current_tiles`,
`wells_total`.

Top level, unchanged: `names`, `aliases`, `scores`, `wins`, `points`, `games`, `seed`, `year`,
`policy_kind`, `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`,
`wall_clock_seconds`, `game_version`.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV09","year":"bc23",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"lemonade",
           "sheet":{…as applied…},"sheet_submitted":"{…as received…}",
           "sheet_defaults_applied":["anchor_round"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":8123,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"Rainbow","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":2000,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…all three drawn maps, even if the match clinched in two…],
         "side_a_slots":[…],"abandon_after":[…],"max_rounds":2000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI — `result`, SINGULAR, this repo's convention */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships), both doctrine sheets, the chassis each
seat drove, and the event list are all in the file, and the wasm sim replays every round from them.
**No `.bc23` bytes, no per-round robot dump, no per-tile dump** — robot positions, cargo, health,
island ownership, anchor health, well inventories, tempo fields, stockpiles and the shared arrays are
pure functions of the sim, so the browser re-derives them and the endcard reads the re-derived totals.
No server is contacted except S3 for the `.replay` file. The per-round hash chain lets the viewer prove
its re-derivation matches the recording (`bc_mismatch_round`, surfaced as `data-replay-mismatch-round`
and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`. **Every event kind here is
bounded per game** — a 2000-round match with 150 robots on the board cannot be allowed to emit an
event per action — and every one has a beat kind with CSS (§Viewer).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides`, `islands`, `islands_to_win`, `headquarters` | 1/game | `game` | beat + feed |
| `first_action` | `game`, `round`, `alias`, `kind` (from `Bc23ActionNames`) | 4/game | `build` | beat + feed |
| `anchor_built` | `game`, `round`, `alias`, `anchor` (`standard`\|`accelerating`), `total_held` | ≤ 40/game | `anchor` | beat + feed |
| `island_captured` | `game`, `round`, `alias`, `island`, `tiles`, `anchor`, `held_now`, `to_win` | ≤ 40/game | `island` | beat + feed |
| `island_lost` | `game`, `round`, `alias`, `island`, `held_for`, `held_now` | ≤ 40/game | `island` | beat + feed |
| `conquest_progress` | `game`, `round`, `alias`, `held`, `to_win` — emitted the first time a faction reaches each of ⅓, ⅔ and one island short of `islands_to_win` | ≤ 6/game | `conquest` | beat + feed ("Clan Ash holds 14 of the 15 islands it needs") |
| `well_transformed` | `game`, `round`, `alias`, `x`, `y`, `from` (`adamantium`\|`mana`), `poured` | ≤ 8/game | `elixir` | beat + feed |
| `well_upgraded` | `game`, `round`, `alias`, `x`, `y`, `type`, `rate` | ≤ 8/game | `elixir` | beat + feed |
| `first_elixir_unit` | `game`, `round`, `alias`, `unit` (`destabilizer`\|`booster`\|`accelerating_anchor`) | ≤ 6/game | `elixir` | beat + feed |
| `boost_field` | `game`, `round`, `alias`, `x`, `y`, `stacks` — the first boost of each faction and then every 20th | ≤ 20/game | `boost` | beat + feed |
| `destabilize_hit` | `game`, `round`, `alias`, `x`, `y`, `victims`, `damage` — only when the detonation actually hit someone | ≤ 20/game | `destabilize` | beat + feed |
| `duel` | `game`, `round`, `lost` (2-array) — a round in which **both** factions lost at least one launcher | ≤ 20/game | `duel` | beat + feed |
| `rout` | `game`, `round`, `alias`, `lost` — a round in which one faction lost ≥ 5 robots | ≤ 20/game | `rout` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points`, `islands` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

Twelve beat kinds (`doctrine`, `game`, `build`, `anchor`, `island`, `conquest`, `elixir`, `boost`,
`destabilize`, `duel`, `rout`, `end`), and **all twelve are emitted by the committed fixture replay**
so the beat test in §Viewer is a real gate and not a CSS inventory. The whole event list for a
three-game match is at most a few hundred entries, and `tests/test_bc23_replay.nim` asserts each
per-kind bound so a pathological game cannot produce a 20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc23/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.bc23` bytes, no 2023 TypeScript
client.

### All four viewer files come from ONE starter: `cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` → `cogame-battlecode` → here. All
four bundle files come from **that one starter** — never a mixture, because splicing one starter's
shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized`
bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23).

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc23/`, `data/bc23/tables.json` and `data/atlas_bc23.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are, including `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-d:useMalloc` and `ENVIRONMENT=web,worker,node`. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. No edit at all is needed for bc23: the page already sets `document.documentElement.dataset.year` from the frame's `s.year` in the **shared** block, so a new year switches itself on. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc23 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and no existing id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and byte-for-byte: **`client/chrome_common.js`** and **`client/broadcast_core.js`**
(their sha256 is asserted against the coworld-ctf copies in `tests/test_viewer.nim`, and that assertion
stays green because neither file is touched). `wire_constants.js` is regenerated from the sim by
`tools/gen_wire_constants.nim`, as today.

**Load signalling** (unchanged from the starter, restated because it is a checklist item):
`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on the
**first drawn frame** (the worker's `loaded` message after the first board frame is composited — never
on rAF timing at the call site, the chorus 2026-08-24 scar), and the `coworld-replay` bridge posts
`ready` from a callback fired **after** that attribute is set. On any failure — fetch, JSON parse, an
unknown `game_version`, a wasm abort, or a hash mismatch that prevents rendering — it sets
**`data-replay-error="<message>"`** on `<html>` and shows the failure card.

### The appended bc23 game block

**No starter element is removed.** The bc26 block's elements (`#coopchip`, `#bars`, `#gamechips`,
`#econ`, `#doctrines`), the bc20 block's (`#bc20-flood`, `#bc20-soup`, `#bc20-units`,
`#bc20-doctrines`, `#bc20-chain`), the bc21 block's (`#bc21-votes`, `#bc21-influence`, `#bc21-units`,
`#bc21-doctrines`, `#bc21-bids`), the bc24 block's (`#bc24-flags`, `#bc24-crumbs`, `#bc24-levels`,
`#bc24-doctrines`, `#bc24-traps`) and the bc25 block's (`#bc25-coverage`, `#bc25-towers`, `#bc25-econ`,
`#bc25-doctrines`, `#bc25-srp`) all stay exactly where they are; the bc23 block adds its own, with ids
that are all new and all prefixed:

- `#bc23-islands` — **the headline readout, and the year's whole story**, in the same top-centre pill
  slot bc20 uses for its flood gauge and bc25 for its coverage bar: a two-sided island tally
  `ASH 9 ◆◆◆◆◆◆◆◆◆ / 15 to win ◇◇◇◇◇◇ 6 BASIL` with the conquest threshold marked, the count of neutral
  islands, and a health pip per held island that empties as an anchor is ground down. It flashes when
  either side captures or loses one.
- `#bc23-econ` — per faction: adamantium, mana and **elixir** banked, income over the last 50 rounds,
  cargo in flight, wells worked and their rate, and an elixir-programme badge (`600 → 412` while a well
  is being converted).
- `#bc23-units` — per faction: the six-type census with the launcher count emphasised (this is the year
  of the launcher duel), robots lost, and anchors sitting unused in headquarters.
- `#bc23-doctrines` — both sheets in plain words, **dismissible** (D3): a `#bc23-doctrines-close`
  button with `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first
  playback advance (or after six seconds for a viewer who never presses play), and a
  `#bc23-doctrines-toggle` chip in the scorebug that re-opens it. Its body is capped and scrolls. It
  sits above the board area and **never** inside the transport band.
- `#bc23-tempest` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: the shared `onText` block already sets
`document.documentElement.dataset.year` from the replay header and re-runs `relayout()` on a change;
the stylesheet extends the existing `html:not([data-year="bc25"]) #bc25-… { display: none !important }`
pattern with the bc23 pair. **Every bc23 rule — including every beat-marker colour — is scoped to
`html[data-year="bc23"]`** (the bc21 r1-F4 fix, kept), so none of them can restyle another year's
marker of the same name. The frame hook is `window.Bc23Block.active(s)` / `.onFrame(s)`, added beside
the existing four in the shared `onText`, and the
`if (!isBc20 && !isBc21 && !isBc24 && !isBc25)` guard becomes
`if (!isBc20 && !isBc21 && !isBc23 && !isBc24 && !isBc25)`.

### The beat contract — emission, label and style, all three tested

This is the one place the bc25 run failed review (r1-F26: eleven beat-kind CSS rules against two
emitted kinds), so it is specified as three obligations that one test asserts together against the
**committed fixture replay** (`tests/fixtures/replay-bc23.json`):

1. **Emission.** `beatsFor` in `src/battlecode/broadcast.nim:129` is the only place a beat kind is
   decided. bc23 adds an arm for each of its event kinds. Two names collide with other years —
   `first_action` and `rout`, which bc24 and bc25 also spell — so the existing two-way discriminator
   (`let isBc25 = doc.year == "bc25"`) becomes an explicit year test: `first_action` maps to `build`
   for **bc23 and bc25** and to `""` for bc24; `rout` maps to `rout` for **bc23 and bc25**. The new
   bc23-only kinds (`anchor_built`, `island_captured`, `island_lost`, `conquest_progress`,
   `well_transformed`, `well_upgraded`, `first_elixir_unit`, `boost_field`, `destabilize_hit`, `duel`)
   need no discriminator because no other year emits them.
2. **Label.** Every emitted beat carries a spectator-readable label built in the same `case` — e.g.
   `"Clan Ash anchors island 3 (9 of the 15 it needs) — game 2, round 1 412"`,
   `"ANCHOR LOST — Clan Basil's island 7 after 240 rounds"`,
   `"Clan Ash turns the mana well at 8,11 into elixir — game 1, round 604"`,
   `"LAUNCHER DUEL — 3 lost to 2, game 3, round 188"` — and it becomes the `<button>`'s `aria-label`
   and `title`.
3. **Style.** `client/replay_broadcast.html` ships a `.beat-marker.<kind>` rule for **all twelve**
   kinds, every one scoped to `html[data-year="bc23"]`: `.doctrine`, `.game`, `.build`, `.anchor`,
   `.island`, `.conquest`, `.elixir`, `.boost`, `.destabilize`, `.duel`, `.rout`, `.end`. Five of those
   names already exist for other years, which is exactly why the scoping is mandatory.

`tests/test_bc23_beats.nim` loads the committed fixture, calls `beatsFor`, and asserts: **at least 24
beats over at least 8 distinct kinds**, every beat's label non-empty and ≤ 120 runes, every emitted
kind present in the twelve-kind vocabulary, and — reading the page source — a
`html[data-year="bc23"] .beat-marker.<kind>` rule for **every kind the fixture actually emitted**
(not for every kind in a hand-written list). `tools/gen_bc23_fixture_replay.nim` is written to produce
all twelve kinds, and the test fails if the fixture stops doing so.

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The `--statrail` repair is already in the tree: `relayout()` measures the union of the *visible* year
stat boxes into `--statrail` (`client/replay_broadcast.html:5030–5041`), `#killfeed`'s `bottom` is
`max(calc(76 * var(--u)), calc(var(--band, 0px) + var(--statrail, 0px) + 8px))` (line 1270),
`tests/test_viewer.nim` asserts both statically, and `viewer_smoke.mjs --killfeed-overlap` measures
client rects at 360 / 720 / 1280 px at FIT and 2× zoom on every year's replay.

**What bc23 must do — and it is the whole of the work here:**

1. add `bc23-econ` and `bc23-units` to `relayout()`'s measured id list, beside `econ`, `bc20-soup`,
   `bc20-units`, `bc21-influence`, `bc21-units`, `bc24-crumbs`, `bc24-levels`, `bc25-towers` and
   `bc25-econ`;
2. run the existing `--killfeed-overlap` gate **on the bc23 replay too**, at all three widths and both
   zooms — six replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and
   asserts the gate goes red, so a sixth year cannot quietly disarm it (the 2026-09-04 learning about
   `page.evaluate` IIFEs and gates that look armed and test nothing).

### Zoom: KEEP `#viewpanel`

The bc23 variant's pool tops out at 60×30 and the reserved large pool at 60×60. The native board render
is 16 px per tile, so 480–960 px wide — **larger than the 360 px featured-match frame**, where a
60-wide board would give 6.0 px per tile. So the inherited `#viewpanel` (zoom bar + minimap, with
`?viewpanel=0` still honoured for thumbnail capture) is **kept**, wired to the same
`zoomAt/setZoom/panBy/panTo/resetView` core API the worker already forwards. The default view is
fit-to-board, so a spectator who touches nothing sees the whole map, every island and both factions'
territory at once — which in this year is the right default, because the story is *where* the robots
are, not what colour the ground is.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets
  **`--hudscale`**, **`--topband`**, **`--band`** and **`--statrail`** on `:root`, iterating to a fixed
  point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport). `#bc23-islands`, `#bc23-econ`, `#bc23-units`,
  `#bc23-doctrines` and `#bc23-tempest` are all explicitly positioned above `var(--band)`.
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek dismisses
  it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`, built by a
  bc23-block function with its **own** name, `buildBc23BeatButtons` — never `markBeat` (the tandem
  2026-08-23 hoisting collision) and never colliding with `buildBeatButtons` (bc26),
  `buildBc20BeatButtons`, `buildBc21BeatButtons`, `buildBc24BeatButtons` or `buildBc25BeatButtons`.
  The spoiler gate is honoured by `applyBc23BeatSpoilers`, the same shape as the other four blocks.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
  `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`,
  `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — check 8 must be dispatched with `settle=20000 soak=15`

bc21 taught this: a compute-heavy year defeats a fixed-wait scrub probe, because the Worker
re-simulates from the last keyframe on every seek and a 700 ms settle expires first (loaded:true,
viewer healthy, instrument too impatient). **bc23 is the heaviest year module in the repo**: the
measured Java mirror carries **121–157 robots** on the board (bc25's carried 26–29), so its per-round
cost is comfortably above the 1 ms/round threshold the bc21 learning names. So, decided here rather
than discovered at phase 60: **the phase-60 check-8 dispatch for bc23 uses `settle=20000 soak=15`**,
and `ci.yml`'s `wasm-viewer` job runs `viewer_smoke.mjs` with `--timeout 120 --soak 15` on the bc23
replay (bc24 and bc25 keep the same; bc26/bc20/bc21 keep `--timeout 90 --soak 10`). The docker-smoke
step prints `sim_seconds / rounds`, and `docs/RULES-BC23.md` records the measured value so the next year
module can size its own probe from a number instead of a guess.

**The scrub selector needs no change.** `tools/ci/viewer_smoke.mjs` in this repo already resolves
`#scrub` before `#seek` before `input[type="range"]`, **one selector at a time**, and `ci.yml` asserts
`scrub_selector == "#scrub"` after every run.

### Art

`data/atlas_bc23.png` + `data/atlas_bc23.json` (≈ 130 KB, committed), cut by
`tools/build_sprite_atlas_bc23.py` from the official 2023 client's sprite tree
(`client/visualizer/src/static/img/` at the pinned commit). The set is **83 PNGs** and the ones that
matter are all used: `robots/{blue,red}_{headquarters,carrier,launcher,amplifier,destabilizer,booster}.png`
(and their `_smaller` variants), `resources/{adamantium,mana,elixir}{,_smaller}.png`,
`resources/{adamantium,mana,elixir}_well{,_upgraded}{,_smaller}.png`,
`resources/{anchor,accelerating_anchor}{,_smaller}.png`, `tiles/terrain*.png` and `star.png`.
**Palette follows the client's own two team colours — blue = side A, red = side B** — and because sides
alternate each game the scorebug plate keeps the *alias* constant and recolours its swatch per game.
Licence is recorded honestly in `NOTICE` (§Packaging): `client/LICENSE` **is the GNU AGPL v3**, while
`client/package.json` declares `"license": "GPL-3.0"` — both facts are stated, and the AGPL file is the
one the repository relies on, which makes this year's sprite provenance *simpler* than bc24's and
bc25's (whose clients carried no LICENSE at all).

Board rendering (`render.nim`): impassable storm squares and clouds are drawn first as terrain (a cloud
is a translucent haze, and it is the one place the spectator sees more than the robots do — see §Out of
scope); currents are drawn as faint directional arrows, because a spectator who cannot see the currents
cannot understand why a carrier is drifting; wells are drawn with their resource glyph and a rate badge
(`×3` when upgraded) and turn into the elixir well sprite the moment they transform, which is the
single most watchable event of the elixir programme; island tiles are tinted by owner with an
**anchor-health ring** around the island's centroid that drains as occupancy goes against the owner;
robots are drawn by type at two team palettes, a carrier with **cargo pips** (and an anchor badge when
it is ferrying, because that carrier is the most important unit on the board), and a health bar under
each; a destabilised patch is a cold overlay and a boosted patch a warm one, so a spectator can see the
tempo fields the doctrines paid elixir for.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else, and the `#bc23-*` boxes dropping
their word labels to glyphs under 640 px).

- `#scorebug`: both faction plates — `CLAN ASH` over the real player name (`daveey`) and the motto —
  the live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 1412 / 2000`, `game 2 of 3 — Rainbow`.
- `#bc23-islands`, `#bc23-econ`, `#bc23-units` as above.
- `#board`: terrain, clouds, current arrows, wells with type and rate, island tiles with owner tint and
  anchor-health rings, every robot with type, health and cargo, the ferrying carriers badged, and the
  boost/destabilise fields.
- `#bc23-doctrines`: each sheet in plain words ("rushes launchers", "converts a mana well to elixir
  from round 200", "spends elixir on accelerating anchors", "first anchor at round 150 with 60 % of
  income reserved", "goes for the safest islands", "one amplifier per headquarters", "withdraws wounded
  launchers to heal on its own islands", "carriers rarely throw"), plus the capped `notes` and a
  fallback badge when a seat's doctrine came from the fallback sheet. Dismissible.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and
  provably clear of the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words ("Clan Basil anchored 15
  of Rainbow's 20 sky islands at round 1 412" / "2 000 rounds — Clan Ash held 9 islands to 6" / "2 000
  rounds — islands and anchors level, Clan Ash won on mana, 387 to 343"); the per-game score line; and
  `#bc23-tempest`, the **war panel**: per faction, islands captured / lost / held at the end and the
  rounds it held any, anchors built / placed / lost (and how many were accelerating), adamantium, mana
  and elixir mined / banked / thrown away, wells transformed and upgraded, robots built by type and
  lost, launcher-duel damage split by source (launcher, throw, destabiliser, headquarters), anchor
  healing received, shared-array writes, and current rides. Nothing about islands, anchors, resources or
  tempo is stored in the replay: the wasm sim re-derives every round.

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`, `player`
  → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar). One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and
  `/bin/battlecode-player` from one image and copies `data/` (now carrying `maps/bc23/`,
  `bc23/tables.json` and `atlas_bc23.*`). **No JDK, no JRE, no Java, no node in any runtime stage** —
  the 2023 engine's toolchain exists only in the `parity-oracle-bc23` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc23 game block along
  with the other five.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc23` is 2023 'Tempest' — carriers mine
    adamantium and mana from sky wells, launchers fight the only real war, and a faction wins by
    ferrying reality anchors onto 75 % of the sky islands."*
  - `tags` unchanged (already four: `battlecode`, `strategy`, `mixed-motive`, `wasm`).
  - `game.config_schema`: `year.enum` becomes `["bc26","bc20","bc21","bc24","bc25","bc23"]`
    (appended, so no existing index moves). `pool.enum` unchanged (`small` / `mixed` / `large`; each
    year owns its own pool table). `maxRounds` keeps `minimum 50, maximum 2000` — **bc23's 2000 is
    exactly the existing ceiling, so no schema change is needed**. `gamesPerMatch` keeps `maximum 3`;
    `perGameBudgetSeconds` keeps `maximum 300` (bc23 uses 110) and `matchBudgetSeconds` `maximum 600`
    (bc23 uses 340). `tokens` stays **declared and required** (the runner injects it — the 2026-09-03
    lesson); every array keeps `minItems`/`maxItems`; no runner-managed `tokens` **values** inside any
    `game_config`; `additionalProperties: false` stays.
  - `game.results_schema`: bc23's optional properties added beside the other years' (§Server, player,
    protocol); `games.items.required` unchanged (the five year-neutral keys); `end_reason`'s enum
    extended with `conquest`, `more_sky_islands`, `more_reality_anchors`, `more_elixir_net_worth`,
    `more_mana_net_worth`, `more_adamantium_net_worth` (`coin_flip` and `abandoned` are already
    there). **`resignation` and `destroy_all_units` are not added for bc23** — the first is unreachable
    from a JSON doctrine and the second does not exist in this year's rule set.
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one
    entry and keeps the seven it has: `rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc24.md`,
    `rules-bc25.md`, **`rules-bc23.md`** (Battlecode 2023 "Tempest": rules, knobs and divergences →
    `docs/RULES-BC23.md`), `replay.md`, `parity.md` (→ `docs/PARITY.md`, which gains a bc23 section).
    Eight pages, every one a `{type, value}` object.
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc23
    resolution ("…, lemonade on bc23" / "…, examplefuncsplayer23 on bc23").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The
  certifier's `players-run` step requires **every** declared `player[]` entry to occupy a slot in
  `certification.players`, and the certifier also requires
  `len(certification.players) == certification.game_config.num_agents`. With `num_agents = 2` there are
  exactly **two** cert slots, they are filled by `awu` and `scaffold`, and therefore **`player[]` may
  contain exactly those two ids and nothing else**. Adding `battlecode-bc23-lemonade` or any other
  year-specific runnable to `player[]` would fail the release with `players_missing`. It is also
  unnecessary: `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`, so seating
  `awu` on a bc23 episode already plays `lemonade` and seating `scaffold` already plays
  `examplefuncsplayer23`. The scripted bc23 policies reach the league through `tools/ci/policies.json`,
  which is a *policy* list and has nothing to do with `player[]`. `tests/test_manifest.nim` asserts all
  three facts (`player[]` ids == `certification.players` ids;
  `len(certification.players) == certification.game_config.num_agents`; `num_agents` present in every
  variant's `game_config` and absent at every variant top level), so the contradiction cannot be
  re-introduced silently.

  **Variants — one per Battlecode year:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | unchanged | **2** |
  | `bc21` | Battlecode 2021 — Campaign (2 seats) | unchanged | **2** |
  | `bc24` | Battlecode 2024 — Breadwars (2 seats) | unchanged | **2** |
  | `bc25` | Battlecode 2025 — Chromatic Conflict (2 seats) | unchanged | **2** |
  | `bc23` | Battlecode 2023 — Tempest (2 seats) | `year: "bc23"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 2000`, `num_agents: 2`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 110`, `matchBudgetSeconds: 340`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `bc23`'s variant description: *"Best of three on the mixed pool. Carriers mine adamantium and mana
  from wells and haul it home at half speed when they are full; launchers are the only unit that deals
  real damage, and they can shoot through the clouds that blind everyone. Pour 600 kg of the wrong
  resource into a well and it becomes elixir, which buys temporal boosters, destabilizers and the
  better kind of reality anchor. Win by anchoring 75 % of the sky islands — and an anchor only holds
  while your robots stand on the island."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false`).

  **The `<SEATS>` cross-check, named explicitly.** `.github/workflows/ci.yml` substitutes
  **`<SEATS>` = 2** into the `docker-smoke` job, and `tools/ci/docker_smoke.sh` takes the seat count
  **solely** from `certification.game_config.num_agents`, hard-failing with `SEAT-COUNT FAIL:` if the
  workflow's value disagrees — and it also refuses a `SMOKE_CONFIG_OVERRIDE` that tries to change
  `num_agents`. Since the cert fixture keeps `num_agents: 2` and the bc23 variant declares
  `num_agents: 2`, the two independent declarations agree. A ranged or vague seat count here would fail
  CI later, not here; there is exactly one number in this note and it is **2**.

  **Certification fixture — UNCHANGED, and stays on bc26.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, `"num_agents": 2` and its existing fast settings (`pool: small`, `seed: 1`,
  `gamesPerMatch: 1`, `maxRounds: 400`, `attempt1Ms: 4000`, `retryMs: 2000`, `doctrineBudgetMs: 9000`,
  `perGameBudgetSeconds: 40`, `matchBudgetSeconds: 45`, `connectTimeoutMs: 15000`). There is **no bc23
  certification fixture in v1** (§Out of scope): certification is the platform's contract check, it
  already passes on bc26, and re-pointing it at a brand-new year module would put the release at the
  mercy of the newest code for no gain. bc23 is proven instead by its own `docker-smoke` episode
  (§Tests), which produces a real bc23 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  **`0.5.0 → 0.6.0`** — because it adds a variant and adds optional results properties without
  changing any existing behaviour. `GameVersion` goes `GV08 → GV09` and
  `ReplayCompatibleGameVersions` is **extended** to `["GV04","GV05","GV06","GV07","GV08","GV09"]`, so
  every hosted bc26/bc20/bc21/bc24/bc25 replay keeps rendering (the bc20 learning about `GameVersion`
  handling: extend, never reset, and claim the version across branches with
  `tools/ci/check_gameversion.sh`). The release is dispatched through the existing
  `coworld-release.yml` with the same step order (build → certify → upload-policies → upload-coworld →
  secret put). **Certify runs against bc26, exactly as before**, and `release-result.json` must still
  show `canonical: true` and `certify.replay_liveness` containing
  `skipped (static replay bundle declared`.

- **Branch discipline.** All work lands on the branch **`bc23-year-module`**, PR-then-merge, and
  `ci.yml`'s `on.push.branches` gains that branch beside `main`, `bc20-year-module`,
  `bc21-year-module`, `bc24-year-module` and `bc25-year-module`. The branch is rebased onto
  `origin/main` before every push. bc23 touches exactly these shared files — `sim_types.nim`,
  `baselines.nim`, `sheet.nim`, `years/registry.nim`, `years/dispatch.nim`, `render.nim`,
  `broadcast.nim`, `client/replay_broadcast.html`, `coworld_manifest_template.json`,
  `tools/ci/policies.json`, `tools/gen_year_constants.py`, `.github/workflows/ci.yml`,
  `docs/PARITY.md`, `NOTICE`, `README.md`, `tests/test_manifest.nim`, `tests/test_viewer.nim`,
  `tests/test_determinism.nim`, `tests/test_constants.nim` — and every edit to each of them is
  **additive** (a new enum value, a new `case` arm, a new appended block), which is what makes those
  rebases clean. **Everything else on `main` is untouched**: no bc26/bc20/bc21/bc24/bc25 module file,
  map, atlas or variant is edited. If a fixer commit takes `GV09` first, this branch rebases to `GV10`
  and extends the compatibility list again — the bc20 precedent, and `tools/ci/check_gameversion.sh`
  is the thing that catches it.

- **`tools/ci/policies.json`** gains the bc23 set beside the bc26, bc20, bc21, bc24 and bc25 sets (a
  scripted champion is a failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-bc23-duel","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"duel"}},
   {"name":"battlecode-bc23-alchemist","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"alchemist"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-lemonade","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"lemonade","PLAYER_POLICY_LABEL":"lemonade"}},
   {"name":"battlecode-examplefuncsplayer23","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer23","PLAYER_POLICY_LABEL":"examplefuncsplayer23"}}]
  ```
  `<IMAGE>` is the **player** service's image (the 2026-09-03 lesson). **Champion #2 carries the
  `"player"` field `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` (daveey-1)** and is uploaded while that
  player is active. LLM credentials reach the **game** container through the manifest env; the player
  pods need no Bedrock sidecar in this lineage.

  **Release dispatch shape, decided:** dispatch `coworld-release.yml` with a `policies` **override**
  limited to the four bc23 entries (the bc20 pattern), so the release does not recut vN+1 of the
  bc26/bc20/bc21/bc24/bc25 policies the five existing leagues have seated. If the override is ever
  dropped and the full file is used instead, phase 50 must take its labels from **this** release's
  `release-result.json` and never from remembered ones (the bc21 learning). Either shape works; this
  run picks the override.

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **sixth league**, created beside the bc26, bc20, bc21, bc24 and bc25 ones and touching none of them
and not the game's default league:

| field | value |
|---|---|
| `league_key` | `bc23` |
| `league_name` | `Battlecode 2023 — Tempest` |
| `default_variant_id` | `bc23` |
| `short_name` | `bc23` → `softmax.com/battlecode/bc23` (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc23-duel` (owned by **daveey**), `battlecode-bc23-alchemist` (owned by **daveey-1**) — deliberately the year's two poles, the launcher duel against the elixir/anchor economy |
| fillers (scripted) | `battlecode-lemonade`, `battlecode-examplefuncsplayer23` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues`
filtered on `game.coworld_name` now returns **six** rows; select by `league_key`/name or you will
configure a sibling year's league. Fillers are set **before** the first `trigger-round`. The atlas slug
is `battlecode/bc23`.

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged by
the repository itself. `NOTICE` gains five sections:

- **`battlecode/battlecode23` engine — AGPL-3.0** (verified: `engine/COPYING` **and** `schema/LICENSE`
  **and** `client/LICENSE` are each the GNU AGPL v3, and the GitHub API reports the repository as
  AGPL-3.0; the repository root itself carries no `LICENSE` file). Pinned commit
  `af42086ecd09709dc603b2aaa9e9b98312c9ef79`. The derived files are named individually:
  `src/battlecode/years/bc23/**` (behaviour, hand-ported), `years/bc23/constants.nim` (generated from
  `GameConstants.java` + `RobotType.java` + `Anchor.java`), `data/maps/bc23/*.json` (converted from
  `.map23`), `data/bc23/tables.json` (generated from the engine's own arithmetic), and
  `years/bc23/chassis/scaffold23.nim` (examplefuncsplayer, ported statement for statement — it is the
  parity oracle's other side and may not gain behaviour). **The engine itself is used only at CI
  time**; no JDK, no JRE and no upstream Java source or bytecode exists in any image this repository
  builds.
- **`battlecode/battlecode23` client sprites — AGPL-3.0.** `client/LICENSE` **is** the GNU AGPL v3
  (unlike 2024 and 2025, whose clients had no LICENSE file), while `client/package.json` declares
  `"license": "GPL-3.0"`; both facts are recorded and the AGPL file governs. `data/atlas_bc23.*` is cut
  from `client/visualizer/src/static/img/**` and is credited in `NOTICE`, naming the source
  directories (`robots/`, `resources/`, `tiles/`). `schema/package.json` also says `GPL-3.0` while
  `schema/LICENSE` is the AGPL — the discrepancy is recorded and is moot here, because **no schema code
  is used at all** (there is no flatbuffers reader on either side of this port, only a hand-written
  vtable walk in the map converter).
- **`awesomelemonade/Battlecode2023` — AGPL-3.0**, head `2e231f31`, `src/finalBot/`. What derives from
  it: `years/bc23/chassis/{lemonade,kit,econ,hq,carrier,launcher,micro,anchors}.nim` — the launcher
  micro and target priority, the chunk-checkpoint BFS navigator, the current- and cloud-aware stepping
  tiebreaks, the symmetry-based enemy-headquarters guess, the island and well trackers, and the
  headquarters build order. **Behaviour, not code**, rewritten in Nim and parameterised by this
  coworld's doctrine sheet.
- **`vrangr1/BattleCode2023` — AGPL-3.0**, head `244af40e`, `src/AFinalsBot/`. What derives from it:
  `years/bc23/chassis/elixir.nim` (the elixir programme — target selection, the 40 kg deposit loop and
  the map-size/round/robot-count gates from `ElixirProducer.java`) and the booster/destabilizer
  commitment rules from `BotBooster.java` / `BotDestabilizer.java`. It is the **only** published bot of
  the three that actually ran the elixir tree, which is why this year's headline doctrine axis has a
  real behaviour source.
- **`jmerle/battlecode-2023` — MIT**, head `e776fcb2`, `src/camel_case_v30_final/`. What derives from
  it: `years/bc23/chassis/comms.nim` (the 64-slot shared-array layout and its 16-bit packing) and
  `kit.nim`'s symmetry elimination, from `util/SharedArray.java` and `util/Symmetry.java`.
- **Unlicensed repositories are not vendored, not ported, not compiled and not read into any file
  here** — the same rule as every other year. `'don't @ me'` (7th) and `'4 Musketeers'` (3rd) are not
  published on GitHub and contribute nothing.

`docs/RULES-BC23.md` carries the full **§Divergences** list: (1) no bytecode instrumentation — a fixed
2 000/1 250/1 000-`DecisionOps` budget with no mid-turn resumption and no mid-primitive cut, together
with the measurement that makes it harmless here (peak 6.6–6.9 % of the limit, zero cut-offs) and the
CI assertion that fails the job at 50 %; (2) `setWinnerArbitrary`'s `Math.random()` replaced by a
world-RNG draw (D4); (3) the `eachRobot` hash-order sweeps replaced by ascending-id sweeps, with the
order-independence argument per site (D1); (4) the island HashMap sweep replaced by ascending island id
(D2); (5) `applyCurrents`'s `HashMap`/`HashSet` iteration replaced by a deterministic worklist, with the
fixed-point argument (D3); (6) the six prose-versus-engine resolutions from §The game (currents at end
of round; destabiliser damage at `cast + 4`; additive quantised multipliers; one victim per tile;
the asymmetric stack guards; a headquarters on a current being pushed, and its measured
unreachability); (7) `resignation` reachable in the engine through `rc.resign()` but unreachable here;
(8) the map file's `symmetry` field read and unused at runtime, exactly as the engine does;
(9) `GameWorld.rand`, `RobotControllerImpl.random`, `INDICATOR_STRING_MAX_LENGTH`,
`EXCEPTION_BYTECODE_PENALTY`, the profiler and the indicator dots/lines all dead or absent here;
(10) the `deadline` wall-clock stop, a coworld concept and not an engine one, recorded as one
load-bearing record; (11) 22 of the 103 official maps converted, with the reasons for the exclusions;
(12) **the released 3.0.15 jar's `GameConstants.SPEC_VERSION` is the literal `"3.0.14"`**, so the jar's
identity is pinned by **sha256** rather than by a version string, and Tier B cross-checks the constants
instead; (13) both chassis are behaviour ports parameterised by the doctrine sheet; (14) the chassis
file layout, if the builder merges any two modules; (15) **a STANDARD anchor placed over our own
ACCELERATING anchor leaves the accelerating anchor's `−0.15` cooldown boost registered on those tiles
forever**, because `Island.advanceTurn`'s removal path only fires for an anchor that is still
`ACCELERATING` — engine behaviour, ported literally, tested (§Tests item 4) rather than "fixed".

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, `<SEATS>` = **2**). The sandbox runs none of it; CI is the harness.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc23_cooldown.nim`** — the two counters: both decrement by 10 at the start of every
   turn and floor at 0; a robot starts life with both at 10, so it can neither move nor act on its
   first turn; an action needs `< 10`; **a headquarters with `actionCooldown = 2` takes exactly five
   actions in one turn and is refused the sixth**; the carrier's base movement cooldown
   `floor(0.375f × weight) + 5` at every weight 0…40; and **the exact charge order per action**, which
   is not uniform in this engine and matters whenever the tile multiplier changes: `move` charges
   **after** the move at the **destination** tile; `buildRobot`, `buildAnchor`, `attack`,
   `collectResource` and `transferResource` charge **before** their effect; `boost`, `destabilize`,
   `takeAnchor`, `returnAnchor` and `placeAnchor` charge **after** it — so a booster's own 140 is
   discounted by the boost it just cast, and a destabilizer's 70 is not (it slows the *enemy*).
2. **`tests/test_bc23_units.nim`** — the six-type table; a launcher's 20 at r² ≤ 16 **including at a
   robot it cannot see**; a carrier's `floor(1.25f × weight)` at every weight 0…40; an attack on a
   headquarters, an ally or an empty tile deals nothing **and a carrier still empties its inventory**,
   with the resources coming off the **team** total and any carried anchor destroyed; `addHealth` caps
   at max and destroys at ≤ 0; **a headquarters is immune** (`addHealth` returns immediately) and its
   nominal 1 HP is never touched; destruction refunds nothing and removes the carrier's cargo from the
   team total.
3. **`tests/test_bc23_wells.nim`** — collect at rate 1 and, after an upgrade, 3; `-1` means "the rate";
   adjacency is `|dx| ≤ 1 && |dy| ≤ 1` **and therefore includes the carrier's own tile**; capacity 40
   enforced; a transfer **into** a well removes the resource from the team total for good;
   **600 kg of the opposite resource transforms an adamantium or mana well into an elixir well** and it
   stops producing its old resource; **1400 kg of its own type upgrades the rate to 3**, including for
   an elixir well; a well that has been transformed counts its 1400 against elixir thereafter; and a
   negative transfer is legal only from a friendly headquarters that holds the amount.
4. **`tests/test_bc23_islands.nim`** — the occupancy formula
   `diff = (100 × (ownerTiles − enemyTiles)) div area` with **truncation toward zero on negative
   numerators**, at every `(owner, enemy, area)` triple for areas 1…20; `health = min(total, health +
   diff)`; neutralisation at `≤ 0` with the anchor counter decrement and the accelerating-anchor boost
   removal; healing of every friendly robot within **r² ≤ 4 of any island tile**, every round, by 4
   (standard) or 6 (accelerating), and **no healing on the round the island went neutral**;
   `placeAnchor` legality (neutral or own island yes, enemy-anchored no); an **override of our own
   anchor restores full health but increments neither anchor counter**; the mid-turn conquest check;
   and **the engine quirk that a STANDARD anchor placed over our own ACCELERATING anchor leaves the
   `−0.15` boost registered forever**, because the removal path only fires for an anchor that is still
   `ACCELERATING` — ported literally and recorded as `docs/RULES-BC23.md` §Divergences item 15.
5. **`tests/test_bc23_tempo.nim`** — the multiplier as integer hundredths: cloud `+20` baked at world
   construction; boost `−10` up to 3 stacks; destabilise `+10` on the **enemy** up to 2; accelerating
   anchor `−15`, 1 stack; the **asymmetric add/remove guards** reproduced literally and shown to be
   balanced over a tile that exceeded the cap; the expiry sweep in the engine's whole-map location
   order, **team A then team B**; a destabilisation dealing **50 at the end of round `cast + 4`** to at
   most one robot per tile and only of the destabilised team (and twice if two entries expire
   together); a boost covering rounds `cast … cast + 9`; and the **float64 reproduction test**:
   `round(base × (h/100.0))` evaluated exactly as Java does, with the `base = 5, h = 70 → 3` case
   (an integer `(5*70+50) div 100` would give 4) as a named vector, over the whole reachable lattice.
6. **`tests/test_bc23_currents.nim`** — forecast, immediate blocking (impassable, off-map, contested by
   two robots), the transitive closure, and the lift-and-set-down; the closure is asserted equal to a
   reference fixed point over 500 random robot layouts; a headquarters standing on a current **is**
   pushed (engine behaviour) **and** no committed map lets that happen; currents fire **every** round,
   after every robot's turn.
7. **`tests/test_bc23_comms.nim`** — the write window: a headquarters or an amplifier may always write;
   any other robot needs a friendly amplifier within r² ≤ 20, a friendly headquarters within r² ≤ 9, or
   one of its **own** islands within r² ≤ 4 (`Island.minDistTo`); index 0…63 and value 0…65535 enforced;
   reading is always legal; **no cooldown and no cost**; the two teams' arrays are isolated and neither
   can read the other's; and the chassis's 16-bit slot packing round-trips for every slot class.
8. **`tests/test_bc23_sensing.nim`** — vision r² ≤ 34 for headquarters and amplifiers, r² ≤ 20 for the
   rest, **collapsing to r² ≤ 4 whenever the sensing robot's tile OR the sensed tile is a cloud**
   (both directions, which is what makes a cloud a hiding place); the engine scan order with the
   `ceil(sqrt(r²)) + 1` box, asserted against a recorded oracle sweep; the precomputed `ceil(√r²)`
   table matches `Math.ceil(Math.sqrt(r²))` for `{4, 9, 13, 15, 16, 20, 34}`; and an attack needs **no**
   vision.
9. **`tests/test_bc23_execorder.nim`** — the exec-order list: append on build, **by-value removal** on
   destroy preserving the order of the survivors, the pre-sweep snapshot so a robot built this round
   takes no turn this round, the `existsRobot` skip for a robot destroyed mid-sweep, and the initial
   headquarters in **ascending id** because `LiveMap` sorts them. 500 random build/destroy sequences
   replayed against the oracle's own list.
10. **`tests/test_bc23_endladder.nim`** — `conquest` fires **mid-turn** inside `placeAnchor` and the
    round still finishes; the float32 threshold `held / islandCount >= 0.75f` for **every** island count
    4…35 against the table in §The game; the five tiebreak rungs fire in the engine's order with a
    vector each; `coin_flip` is reachable and seeded from the world RNG; **a faction with zero robots
    plays on to round 2000** (there is no elimination condition) and its headquarters keep earning
    passive income; and `resignation` is provably unreachable from any chassis.
11. **`tests/test_bc23_scoring.nim`** — the points formula with float32 narrowing and truncation, one
    vector per weight; the 0–0 `share` returning 0.5 (and the measured-common all-zero case for
    islands, anchors **and** elixir); points in `[0, 100]` and the seats summing to ≤ 100; **the
    super-increasing property** (`22 > 10+5+3`, `10 > 5+3`, `5 > 3`, `60 > 40`) asserted as arithmetic
    **and** exercised as a win on each of the five rungs coming with strictly higher points; the
    documented and legal case of a `conquest` win scoring fewer points than the loser; and
    `results.scores` **strictly** ordering the match winner above the loser on 500 random synthetic
    finals, including clinched two-game matches.
12. **`tests/test_bc23_sheet.nim`** — every one of the twelve knobs: absent → default, mistyped →
    default + recorded, unknown enum value → default + recorded; **the three integer knobs and
    `anchor_round` CLAMP to their range rather than defaulting** (and a non-integer defaults);
    enum values are case-folded and trimmed; unknown keys recorded (≤ 16, ≤ 40 runes); **a submitted
    `chassis` is recorded as an unknown field and never honoured** (the D1 assertion, which fails if
    anyone re-adds the knob); rune-boundary truncation of `notes`/`motto` including astral-plane
    characters; the 16 KB byte cap cut on a rune boundary.
13. **`tests/test_bc23_maps.nim`** — every committed bc23 map re-converts identically from the pinned
    `.map23`; sizes, seeds, declared symmetry, wall/cloud/current counts, island counts, island tiles,
    well counts and headquarters-per-side match the table in §Sim module; every map is within 20…60 in
    both dimensions; island counts are within 4…35 and **no island exceeds 20 tiles**; both factions
    have the same number of headquarters; **no headquarters sits on a current, an island or a well**;
    **no tile is both cloud and current**; no bc23 map name resolves to another year's map file; and
    **the seed the `docker-smoke` step passes draws exactly `Quiet`** from the `small` pool, so the
    smoke's map cannot drift silently.
14. **`tests/test_bc23_scaffold.nim`** — `examplefuncsplayer23` reproduced statement for statement: the
    `Random(6147)` call sequence (`nextInt(8)`, `nextBoolean()`, `nextInt(20)`, `nextInt(3)`) in the
    engine's own order; the **`HashSet<MapLocation>` iteration order** its anchor branch depends on
    (`hashCode = (y + 0x8000) & 0xffff | (x << 16)`); the launcher attacking the square one step
    **EAST of itself** rather than the enemy it just sensed; the nine-tile coin-flip collect loop; and
    the `wells[1]` step — every one asserted against a recorded oracle trace. It may not gain
    behaviour: it is one side of the differential oracle.
15. **`tests/test_bc23_baselines.nim`** — bounded orders and legality:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the *same* `validate` the LLM
      path uses;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the
      moment it is emitted**: the right cooldown counter under 10, the target in the right radius and on
      the map, the adjacency test where the engine has one, the resources actually present in the
      **acting headquarters'** stockpile (not the team total), the carrier's capacity, the island
      standing for `placeAnchor`, the write window for `writeSharedArray`, no headquarters moving, no
      robot attacking without being a carrier or a launcher; and **no robot exceeds its `DecisionOps`
      budget**;
    - (c) `examplefuncsplayer23` **acts** — ≥ 1 carrier built, ≥ 1 launcher built, ≥ 1 anchor built,
      ≥ 1 collect, ≥ 1 throw — but is **not** required to survive or to compete;
    - (d) `lemonade` beats `examplefuncsplayer23` on 3 seeds × 2 `small` maps, 6/6.
16. **`tests/test_bc23_survival.nim`** — the **competence gate** (the LEARNINGS pin), with an inverted
    control. **The key design point, stated because it is bc23-specific and easy to get wrong: in this
    year a resource is added to the team total the moment a carrier *mines* it, but a headquarters can
    only spend from its **own** stockpile. So a faction whose carriers never deposit looks rich and
    builds nothing.** The gate therefore keys on **units, anchors and islands**, never on team net
    worth:
    - `lemonade` vs `lemonade`, all-defaults sheet, 3 seeds × 2 `small` maps = 6 games, each to round
      2000. In **all 6**, each seat must have: built ≥ 12 carriers and ≥ 8 launchers; **deposited**
      ≥ 400 kg into its headquarters; built ≥ 1 anchor and **placed** ≥ 1; held at least one island for
      ≥ 100 consecutive rounds; and finished with ≥ 8 robots alive. **Across the two seats** there must
      be ≥ 1 island that changed hands, and in **≥ 4 of the 6** games ≥ 1 well transformed to elixir
      (the default `elixir_tech: mid` opens after round 500 — §Decisions — so a 2000-round game has
      room for it).
    - The same gate is then run as a **subprocess** against a **known-broken chassis** compiled behind
      **`-d:bc23BrokenChassis`** — a `lemonade.nim` variant whose carriers **mine but never transfer to
      a headquarters**, so the team totals grow while the build queue starves — and **must come back
      red**. That control is chosen deliberately: it is exactly the failure a net-worth-based check
      would pass. A gate that cannot fail is not a gate; this assertion is what keeps it honest, and it
      is the direct answer to the 2026-09-03 finding that mechanical episode checks pass degenerate
      matches.
    - **The thresholds above are the design floor, not the committed numbers.** Phase 20 **measures** a
      healthy mirror and the broken control, sets the committed thresholds between them with margin
      (and never below this note's floor), and records **both** measured ranges in the test's header
      comment — exactly as `tests/test_bc24_survival.nim` and `tests/test_bc25_survival.nim` do today.
17. **`tests/test_bc23_knobs.nim`** — the knob-teeth gate. Paired seeded games (identical seed, map and
    opponent; the two factions identical except one knob at its low and high setting, 3 seeds each),
    each asserting a named, signed delta. Thresholds live in one table so tuning is a one-line change,
    and the header records every substituted statistic (the bc21 r1-F6 fix):

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `carrier_eco` → `launcher_rush` | launchers built by round 400 up ≥ 60 % **and** carriers built by round 400 down ≥ 30 % |
    | `launcher_ratio` | 20 → 80 | launchers built up ≥ 2× **and** carriers built down ≥ 40 % |
    | `well_priority` | `adamantium` → `mana` | mana mined up ≥ 50 % **and** adamantium mined down ≥ 30 % |
    | `elixir_tech` | `never` → `early` | wells transformed up ≥ 1 **and** elixir mined up ≥ 300 |
    | `elixir_spend` | `boosters` → `destabilizers` | destabilizers built up ≥ 2 **and** destabilize damage up ≥ 100 (run with `elixir_tech: early` on both sides, since the sink is only reachable when elixir flows) |
    | `anchor_round` | 1500 → 100 | round of the first anchor placed earlier by ≥ 800 **and** rounds holding any island up ≥ 400 |
    | `anchor_budget` | 0 → 100 | anchors placed up ≥ 3 **and** launchers built down ≥ 25 % |
    | `island_priority` | `nearest` → `safe` | mean distance from a captured island to the enemy's nearest headquarters up ≥ 30 % **and** islands lost down ≥ 1 |
    | `amplifier_use` | `never` → `escort` | amplifiers built up ≥ 2 **and** shared-array writes up ≥ 3× |
    | `destabilizer_use` | `hold` → `siege` | mean distance of the strike group from its own headquarters up ≥ 40 % **and** damage dealt to enemy carriers up ≥ 30 % |
    | `retreat_on_launcher_loss` | `never` → `home` | launchers lost down ≥ 20 % **and** anchor healing received up ≥ 50 |
    | `carrier_throw` | 0 → 100 | resources thrown up ≥ 200 **and** resources deposited down ≥ 15 % |

18. **`tests/test_bc23_perf.nim`** — a full 2000-round game on `IslandHopping` (60×30) with both seats
    on `opening: carrier_eco`, `launcher_ratio: 80`, `anchor_budget: 0` in **≤ 100 s**; failing it means
    switching `gamesPerMatch` to 1 (§The game).
19. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain, twice
    in one process and across a save/load; and **record → re-derive for every bc23 end reason**
    (`conquest`, all five tiebreak rungs, `coin_flip`, and the wall-clock `abandoned`/`deadline` stop
    applied by the same proc on both paths).
20. **`tests/test_bc23_replay.nim`** — a bc23 replay document round-trips; a **strict UTF-8 parse** of
    the written bytes; the viewer's re-derivation of a recorded bc23 match reproduces the recorded
    per-round hashes; robot positions, cargo, islands, anchors, wells, tempo fields, stockpiles and both
    shared arrays re-derive identically from events + config + seed with nothing stored; `plan.maps`
    carries all three drawn maps even when the match clinched in two; and **every event kind respects
    its per-game bound** from the table in §Server, player, protocol.
21. **`tests/test_bc23_beats.nim`** — the **beat contract** (§Viewer): from the committed
    `tests/fixtures/replay-bc23.json`, `beatsFor` must return **≥ 24 beats over ≥ 8 distinct kinds**,
    every one with a non-empty label of ≤ 120 runes, every kind inside the twelve-kind vocabulary, and a
    `html[data-year="bc23"] .beat-marker.<kind>` CSS rule present in `client/replay_broadcast.html` for
    **every kind the fixture actually emitted**. Emission, label and style, all three, from the
    committed artefact — the durable shape the bc25 r1-F26 finding asked for.
22. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now six years wide: the results
    key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; `num_agents` present in **all six** variants' `game_config` and
    in `certification.game_config`, and **absent** at every variant top level;
    `config_schema.year.enum == ["bc26","bc20","bc21","bc24","bc25","bc23"]`; **`player[]` contains
    exactly the ids in `certification.players`** and
    `len(certification.players) == certification.game_config.num_agents` (the pair of checks that would
    have caught the bc20 release failure); every `config_schema` array bounded; `tokens` declared and
    required but never valued in a `game_config`; both `game.protocols` keys and `game.docs.readme` plus
    **all eight** `pages` are `{type,value}` objects; and the installed `coworld` CLI's own
    `validate_upload_manifest` / `_load_template_manifest` accepts the template.
23. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc23** fixture replay;
    the bc23 game block shadows no `ChromeCommon` alias and no other year's game-block name (the tandem
    scar); `chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256;
    `#bc23-doctrines` carries a dismiss control and sits outside `var(--band)`; every `#bc23-*` rule is
    scoped to `html[data-year="bc23"]`; and `relayout()`'s `--statrail` measurement set names
    `bc23-econ` and `bc23-units`.
24. **`tests/test_constants.nim` (extended)** — `tools/gen_year_constants.py --year bc23 --check`
    regenerates `years/bc23/constants.nim` from the pinned sources and byte-diffs it, and
    `tools/convert_maps_bc23.py --engine … --check` re-converts all 22 committed maps and byte-diffs
    them, plus `--parse-all` reads **all 103** official `.map23` files with the converter's own vtable
    walk (a reader that only works on the maps we ship is a reader nobody can extend the pool with).

### `parity-oracle-bc23` job — the 2023 engine as a CI-only oracle

**The recipe below was EXECUTED in this sandbox, not guessed**, and it found two traps that would each
have cost a CI round. The released fat jar
`https://releases.battlecode.org/maven/org/battlecode/battlecode23/3.0.15/battlecode23-3.0.15.jar`
(HTTP 200, **16 982 927 bytes**, sha256
`5d4e42a51946cc1c2149426485bda8096ff1c088c77e3ed075c06ce5968ed72a`, pinned in
`tools/oracle/bc23/jar.lock`) is **self-contained**: 11 566 entries, every `battlecode` class, every
bundled dependency — including **`net.sf.jsi`** and **`gnu.trove`**, so the dead-artifact problem that
forced bc21's jsi shim, its 94-file `javac` and its `deps.lock` **does not arise here** — plus
`battlecode/instrumenter/bytecode/resources/MethodCosts.txt` and all **103** `.map23` map resources.
So there is **no Gradle, no shim, no multi-file compile, no Maven Central download list and no
`deps.lock`** in this job. It is:

1. `actions/setup-java@v4`, `distribution: temurin`, `java-version: **"8"**`. **This is not a
   preference and it is not negotiable, and the reason was measured:** the engine's `build.gradle` sets
   `sourceCompatibility = 1.8` and the jar bundles **ASM 5.0.4**, which cannot read modern class
   files. Under **JDK 21** the instrumenter throws `java.lang.IllegalArgumentException` inside
   `org.objectweb.asm.ClassReader.<init>` from `TeamClassLoaderFactory.normalReader`
   (via `MethodCostUtil.getMethodData`) on **every** player class load; every robot dies as it spawns,
   **no robot is ever built**, the trace is a few hundred empty lines and **the job exits 0**. That is
   the exact "green oracle proving nothing" trap bc25 hit from the other direction, and it is why
   item 3 below exists.
2. **Compile with plain `javac -nowarn -encoding UTF-8 -cp <jar>` and NO `--release`, no `-source`,
   no `-target`.** `--release` arrived in JDK 9 and dies with "invalid flag" on a JDK-8 `javac` in
   seconds — the bc21 lesson, and this job is JDK 8, so the flag must be absent rather than set to 8.
   The compiler *is* 8, so the target is 8.
3. **The driver must fail loudly when nothing happens, and it must call `System.exit()`.** Two measured
   requirements: (a) `tools/oracle/bc23/Bc23Trace.java` **exits 3 if no robot is ever built**, which is
   what catches item 1 (and `ci.yml` additionally asserts every game reached at least **1 900 rounds**
   and built at least **100 robots**); (b) the sandboxed player threads are **non-daemon**, so a driver
   that returns or throws without `System.exit()` hangs forever — measured, the first run of this driver
   hung until the harness timeout after an unrelated exception. Every `java` invocation in the job is
   wrapped in `timeout 600`.
4. Download the jar and **verify its sha256 and size** against `jar.lock`. **Do not assert a version
   string**: the *released 3.0.15* jar's `GameConstants.SPEC_VERSION` is the literal **`"3.0.14"`**
   (measured), so bc24's `test "${spec}" = "3.0.5"` step has no bc23 equivalent. The sha256 *is* the
   version pin, and Tier B cross-checks the constants instead.
5. Run `java -Xmx2g -XX:+UseSerialGC -cp battlecode23-3.0.15.jar:classes battlecode.world.Bc23Trace
   <map> <rounds> <pkgA> <classesDirA> [<pkgB> <classesDirB>]`. The driver is
   `package battlecode.world;` so it needs reflection only for `ObjectInfo.dynamicBodyExecOrder` and
   `GameWorld.islandIdToIsland` (both private, and reading them is the only way to print in exec order
   and in island-id order): it loads the map with `GameMapIO.loadMapAsResource(loader,
   "battlecode/world/resources", map, false)`, builds a `TeamControlProvider` over two
   `PlayerControlProvider`s (**the player URL must be the compiled classes directory** — an empty URL
   fails class loading), constructs `new GameMaker(info, null, false)` (the null packet sink is
   supported) and calls `GameWorld.runRound()` in a loop, printing the trace **from the live objects**.
   **No flatbuffers reader, no `flatc`, no `pip install` on either side**, and the engine is used
   exactly as published.

**The trace.** One line per record; `tools/parity_trace_bc23.nim` prints the same lines from the Nim
port:

```
R <round> T <A|B> ad=<n> mn=<n> ex=<n> isl=<n> anch=<n> anchheld=<n>
R <round> I <islandId> own=<0|1|2> hp=<n> anch=<STANDARD|ACCELERATING|->
R <round> W <wellIdx> ty=<AD|MN|EX> rate=<1|3> ad=<n> mn=<n> ex=<n>
R <round> M chk=<fnv1a64 of the per-tile per-team multiplier hundredths, y asc outer, x asc inner>
R <round> U <id> team=<A|B> ty=<TYPE> x=<n> y=<n> hp=<n> ad=<n> mn=<n> ex=<n> anc=<n> acd=<n> mcd=<n> bc=<n>
R <round> S <A|B> arr=<fnv1a64 of the 64-slot shared array>
R <round> Z winner=<A|B|-> dom=<NAME|->
```

Robots are printed **in exec order**, not id order, which is what makes an ordering bug visible;
islands in ascending id; the multiplier checksum is what makes a single wrong tempo tile visible
without printing 3 600 tiles a round. The Java side's `bc=` column is stripped before the diff (there is
no bytecode counter on the Nim side) and is used only for the Tier A headroom assertion. **Measured in
this sandbox** (the `T`, `I`, `U` and `Z` lines exactly as above; `W`, `M` and `S` are the shipped
driver's additions): a full 2000-round game is **210 577–264 676 trace lines (18–22 MB)** and
**26.5–31.1 s of JVM** per map, and the board carries **121–157 robots** at its peak (mean 97–124), so
six pairs cost roughly three minutes of engine time and ~120 MB of temporary trace. Traces are written
to `$RUNNER_TEMP`, compared **streaming** (never loaded whole), and only the first 200 divergent lines
plus a gzipped digest are uploaded.

**The tiers — pinned to what this harness can actually deliver, which was measured, not hoped.**

- **Tier A (BLOCKING) — rounds 1…2000 bit-exact, whole games, on six `small` pairs**
  (`Quiet`, `SmallElements`, `Lantern`, `Spin`, `Sneaky`, `Barcode`), `examplefuncsplayer23` against
  itself, every field above. This is a *whole-game* window for one measured reason: the 2023 example bot
  **never approaches its bytecode limit** — peak use across three full 2000-round games was
  **823–856, i.e. 6.6–6.9 % of the carrier's 12 500** — with **zero** mid-turn cut-offs — so the port's
  "no mid-turn resumption" divergence is never exercised and the comparison stays defined to the last
  round. The job does not assume that: it reads the `bc=` column and **fails if any robot on any round
  exceeds 50 % of its type's limit**, naming the round and the robot, because past that point the window
  would have to shrink and this note would rather be wrong loudly than green quietly. (This is exactly
  where bc21 could not go: its example bot *did* hit the ceiling, which is why its windows were 22–245
  rounds. The tiers here are sized by measurement, not by ambition.)
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact.** Tier A's own measurement showed
  exactly what it cannot cover. Over three full 2000-round games the example bot **never took an anchor
  from a headquarters, never placed one, never captured an island, never built an amplifier, a
  destabilizer or a booster, never transferred a resource to a headquarters, never upgraded or
  transformed a well, never wrote the shared array, and ended every game on `MORE_MANA_NET_WORTH` at
  round 2000 with islands 0–0 and anchors 0–0** — so `CONQUEST`, the first two ladder rungs, the whole
  anchor and island subsystem, the elixir tree, the tempo fields and every comms path are untested by
  it. Those are precisely the "rare code paths that fire mid-game" the Fleet card 1218171523823317
  postmortem warns about. So this job runs a **second oracle bot of our own**,
  `tools/oracle/bc23/bc23scenario/RobotPlayer.java`, written to be (a) deterministic with **no RNG at
  all**, (b) cheap — the job asserts it never exceeds **25 %** of its bytecode limit, so it can never be
  cut off mid-turn — and (c) **scripted by round number to force every rare path early**: build a
  standard anchor and (after transforming a well) an accelerating one; take, ferry and plant both on a
  neutral island, then override our own anchor and prove the counters do **not** increment; let an
  island be ground down by enemy occupancy until it goes neutral, and re-take it; transform a mana well
  with 600 kg of adamantium and then upgrade a well with 1400 kg of its own type; build an amplifier and
  write the shared array from outside every other window, then step out of range and prove the write is
  refused; write from a robot standing within r² ≤ 4 of our own island; cast a boost and measure the
  discounted 140; cast a destabilisation and let it detonate on a robot; throw a full carrier at an
  enemy (a hit) and at an empty tile (a miss) and prove the cargo is gone both times; ride a current and
  be blocked by one; sense from inside a cloud and be sensed from outside one; take five build actions
  from one headquarters in one turn; and disintegrate one robot. Two further variants force the ends:
  **`bc23scenarioconquest`** anchors 3 of the 4 islands on `Quiet` so `CONQUEST` fires, and
  **`bc23scenariotie`** mirrors both sides exactly so the ladder walks down to
  `MORE_ADAMANTIUM_NET_WORTH` and, on one seed, to `WON_BY_DUBIOUS_REASONS`. `scenario23.nim` is its Nim
  twin, written line for line against it, behind `-d:bc23Scenario` (+`-d:bc23ScenarioConquest` /
  `-d:bc23ScenarioTie`). Both sides run all three variants on all six pairs and must agree **bit for
  bit for the whole game**. The job then asserts, **off the JAVA trace**, that the paths really fired:
  an `I` line with `own=1` and `anch=STANDARD` appears and later one with `anch=ACCELERATING`; an `I`
  line returns to `own=0`; a `W` line's `ty=` changes from `MN` to `EX` and another's `rate=` from 1 to
  3; the `M` checksum changes and returns; an `S` checksum changes; a `Z` line with `dom=CONQUEST` and
  one with `dom=MORE_ADAMANTIUM_NET_WORTH` exist. **A scenario bot that agrees bit for bit while doing
  nothing proves nothing**, and this is the step that stops it. *(If the engine's own instrumentation
  makes any one of these scripted paths impossible to force deterministically, the failing item is
  dropped from the scenario bot and **added to `docs/PARITY.md` §What is NOT compared with the
  reason** — never silently left in a bot that does not reach it.)*
- **Tier B (BLOCKING) — the arithmetic, over its whole finite domain.** `tools/JavaBc23Tables.java`,
  run against the jar's own classes under the CI **JDK 8**, regenerates `data/bc23/tables.json` — the
  whole `RobotType` table (10 fields × 6 types) and `Anchor` table (8 fields × 2); the carrier movement
  cooldown `floor(0.375f × w) + 5` for **every** weight 0…40; the carrier throw damage
  `floor(1.25f × w)` for every weight 0…40; **the entire cooldown-multiplier lattice** — every
  reachable multiplier (1.00 with cloud, boost stacks 0…3, destabilise stacks 0…2 and the anchor's
  −0.15, i.e. every reachable hundredths value) × every base cooldown in `{2, 10, 15, 20, 25, 70, 140}`
  **and** every carrier base 5…20, as `(int) Math.round(base × multiplier)` computed by the JVM itself;
  the conquest threshold `held / total >= 0.75f` for every island count 4…35 and every held count; and
  the island occupancy `(100 × (a − b)) / area` for every `(a, b)` pair up to area 20 — and the job
  **byte-diffs** it against the committed file. bc23 has **no transcendental anywhere**, so unlike bc21
  this tier is not a sample: it is the entire domain. The same step cross-checks every `GameConstants`
  field against the **jar's** classes, which is what closes the "released jar versus pinned master
  sources" gap in the absence of a usable `SPEC_VERSION` (`docs/RULES-BC23.md` §Divergences item 12).
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 2000-round game, on
  all four bots and all six maps.** The job computes it per pair and compares it against
  `tools/ci/parity_ledger_bc23.json`, whose entries are
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

the exec-order list's by-value removal and the pre-sweep snapshot (test 9); the per-action charge order,
especially `boost`/`destabilize`/`placeAnchor` charging **after** their effect and `move` charging at the
**destination** (test 1); the float64 multiplier rounding, including the `base 5 × 0.70 → 3` case
(test 5); the destabilisation firing at `cast + 4` and hitting one robot per tile (test 5); the
asymmetric stack guards (test 5); the island occupancy formula's truncation toward zero and the healing
sweep's radius (test 4); the anchor-override counters and the STANDARD-over-ACCELERATING boost quirk
(test 4); the well transformation and upgrade thresholds and the fact that a transfer into a well leaves
the team total (test 3); the carrier's weight-based movement and its inventory-emptying throw (tests 1
and 2); the current closure (test 6); the shared-array write windows (test 7); the cloud vision collapse
in **both** directions and the `ceil+1` scan box (test 8); the float32 conquest threshold (test 10); and
the `IDGenerator` stream that fixes every built robot's id (`tests/test_rng.nim`).

Tiers A, A′, B and C are the **phase-30 gate**. Every accepted divergence is listed in
`docs/RULES-BC23.md` §Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md` gains
a `bc23` section written in the same shape as the `bc25` one — including, honestly, the measured numbers
(peak bytecode %, cut-offs, trace line counts, JVM seconds, peak robot counts, the JDK-21 ASM trap and
the non-daemon-thread hang).

### `docker-smoke` job — now **six** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely from
`certification.game_config.num_agents` and hard-fails with `SEAT-COUNT FAIL:` if the workflow's
`<SEATS>` = **2** disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes —
bad-token refusal, `/global` first frame on connect, `Ping → Pong` payload echo — against the real image
on the first episode):

1. **The bc26 certification-fixture episode**, unchanged → `dist/smoke/replay.json`.
2. **The bc20 episode**, unchanged → `dist/smoke/replay-bc20.json`.
3. **The bc21 episode**, unchanged → `dist/smoke/replay-bc21.json`.
4. **The bc24 episode**, unchanged → `dist/smoke/replay-bc24.json`.
5. **The bc25 episode**, unchanged → `dist/smoke/replay-bc25.json`.
6. **A bc23 episode**, new: `SMOKE_EXPECT_YEAR=bc23`, `SMOKE_PLAYER_IDS=awu,scaffold`,
   `SMOKE_CONTRACT_PROBE=0`, `SMOKE_REPLAY_OUT=dist/smoke/replay-bc23.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc23","pool":"small","seed":<the seed test 13 pins>,
   "gamesPerMatch":1,"maxRounds":800,"perGameBudgetSeconds":70,"matchBudgetSeconds":80,
   "connectTimeoutMs":15000}`. **800 rounds** and not 600: the default `anchor_round` is 400, so the
   window has to be long enough for the strong chassis to actually build, ferry and plant an anchor —
   which is the one signature of this year the smoke asserts across the pair (below) — and 800 rounds
   still records ~30 s of playback, which outlasts the viewer smoke's 15 s soak (the ecos 2026-08-23
   scar). The seed is pinned to draw `Quiet` (20×20, four islands, one headquarters a side), the
   smallest map in the pool, so the episode is fast and the map cannot drift.

All six run one game container + two player containers on a shared network with `file://` artifact URIs
and **no** `ANTHROPIC_API_KEY`, so both seats take the scripted path and must still complete. All six
assert: the game exits 0, **every player container exits 0**, `results.json` carries exactly the expected
key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`, and the replay parses as
**strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the right `year`, and a non-empty
`events` array. A step asserts all six replays exist and report six different `year` values.

**The episode substance assertion (the LEARNINGS pin), in two parts.** The bc23 episode passes
`SMOKE_REQUIRE_STATS` — the **per-seat** floor, which the script already enforces for both seats — with
`{"units_built":20,"adamantium_mined":60,"mana_mined":40,"damage_dealt":20}`. Those four are things
*both* chassis do, including the weak floor: the upstream example bot's headquarters build a robot most
turns from round 1, its carriers collect from any adjacent well on a coin flip, and damage accrues from
launchers and from the headquarters' own 4-per-round aura. **The signatures of the year are things only a
seat playing well does** — depositing cargo at a headquarters, taking an anchor, planting it and holding
an island (the example bot does **none** of those: measured, it never calls `transferResource` or
`takeAnchor` at all) — so asserting them per-seat would be asserting that the weak floor is not weak.
They are asserted **across the pair** by one `jq` step in `ci.yml`, reading the **replay's** `result`
block (not `dist/smoke/results.json`, which every episode overwrites in turn — the bc24 fix):
`([.result.games[0].units_built[]] | add) >= 60`,
`([.result.games[0].resources_banked[]] | add) >= 200`,
`([.result.games[0].anchors_built[]] | add) >= 1`,
`([.result.games[0].anchors_placed[]] | add) >= 1` and
`([.result.games[0].islands_captured[]] | add) >= 1`. Together they make an idle win machine-visible,
which is exactly what the 2026-09-03 round-1 degenerate match lacked.

**And the floors are measured, not guessed.** The per-seat numbers above are a lower bound derived from
the Java example-bot mirror measured in this sandbox (which at round 600 has **48–68 robots alive per
side** and mines continuously). Phase 20 runs the real bc23 smoke once, reads the actual per-seat
statistics out of `dist/smoke/replay-bc23.json`, and sets the committed floors at roughly half the weak
seat's measured value — **never below this note's numbers, and never above what a correct episode
produces** (the bc25 r1-F34 lesson: a floor derived from whole 2000-round games is wrong for an
800-round smoke) — recording the measurement in a comment beside the step. **If the across-the-pair
`islands_captured >= 1` assertion does not hold on the measured episode, the fix is to raise the smoke's
`maxRounds` until it does, never to drop the assertion**: an episode of this year in which nobody ever
anchors an island is not this game being played.

### `wasm-viewer` job — the bundle is **executed**, against **all six** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay>
--killfeed-overlap` in headless chromium (Playwright pinned 1.55.0) **once per replay** —
`replay.json`, `replay-bc20.json`, `replay-bc21.json` at `--timeout 90 --soak 10`, and
`replay-bc24.json`, `replay-bc25.json` **and `replay-bc23.json`** at **`--timeout 120 --soak 15`** for
the pacing reason in §Viewer. Each run requires `data-replay-loaded="true"` (or the bridge `ready`
posted after it), three **differing** clock/scorebug readouts at 0 % / 50 % / 100 %, continued
advancement across the soak, `scrub_selector == "#scrub"` (so a seek was really exercised and the
`#viewpanel` zoom slider was not clicked instead), `#endcard` **computed-shown** after the 100 % seek
carrying a `clan` line, no overlay covering more than 50 % of the board after the soak, and the
`#killfeed`/stat-box overlap check at 360 px, 720 px and 1280 px at both FIT and 2× zoom.
`--strict-text-bounds` stays deliberately dropped here because the board is pannable and zoomable
(`#viewpanel` is kept), which is the exact case the flag's own documentation excludes; the `canvas_text`
counts are still recorded in `viewer-smoke.json`, and the separate `tools/ci/renderer_fixture.html`
step — full-cap `notes` and `motto` on both seats at three widths including **360 px**, in the page's own
CSS extracted from `client/replay_broadcast.html` at run time — runs through the same harness with
`--strict-text-bounds`, because every CI replay is scripted and carries no LLM text (the cogchemists
2026-08-24 scar). The fixture gains a bc23 row. `node tools/wasm_replay_smoke.cjs` is also run against
the bc23 smoke replay **and** the committed `tests/fixtures/replay-bc23.json`, so wasm32-only failures
(int overflow traps, address-space exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation of
  anything a cog sends. The 2023 engine exists only in the `parity-oracle-bc23` CI job, and only as the
  published jar.
- **Full bytecode metering.** The 2 000/1 250/1 000-`DecisionOps` budget replaces it, with no mid-turn
  resumption and no mid-primitive cut. A Nim-level instrumenter is a compiler project and buys nothing
  the oracle does not already prove — and on this year's measurement the oracle never reaches 7 % of the
  boundary.
- **A cog-authored Java (or any) strategy class.** Doctrines are **JSON-sheet only**; there is no
  `javac`, no instrumenter `Verifier`, no compile-error round trip and no multi-attempt loop. Nothing in
  the schema is closed against a future sandboxed hook.
- **A bc23 certification fixture, and any new `player[]` entry.** Certification stays on bc26 and
  `player[]` stays at `awu` + `scaffold`. bc23 is proven by its own `docker-smoke` episode and the viewer
  smoke run against that episode's replay.
- **81 of the 103 official maps.** The converter handles any `.map23` and CI parses all 103; v1 commits
  the 22 whose geometry is pinned in this note. `Marsh` (40.6 % cloud) and `BuildSite` (71.2 % walls) are
  excluded on purpose, as is everything above 1 800 tiles for the played pools.
- **The official 2023 TypeScript client and Electron visualizer, and `.map23`/replay flatbuffers in the
  browser.** Its *sprites* are reused (credited, AGPL-3.0 per `client/LICENSE`); its app is not shipped,
  not embedded and not built. There is no flatbuffers library on either side of this port — the map
  converter is a hand-written vtable walk — and no `match_b64` field exists.
- **Worker-side keyframe checkpoints in the viewer.** bc23 seeks re-simulate from the start of the game
  like every other year, which is why check 8 is dispatched with `settle=20000`. Keyframes are the
  obvious next optimisation for the heaviest year module in the repo and they are deliberately not in v1.
- **A cog-authored comms protocol.** The 64-slot shared-array layout is the chassis's; a doctrine cannot
  redefine it. `amplifier_use` steers who can speak, not the encoding.
- **Indicator strings, dots, lines, the profiler, and `.bc23` output of any kind.** They are
  instrumentation with no runtime meaning and no port.
- **Per-robot fog in the viewer.** The spectator sees the true board, including inside clouds, which the
  robots cannot. Clouds are drawn as haze so a spectator can see *why* a launcher group lost track of a
  carrier, but the viewer does not simulate per-faction knowledge. (The enemy's shared array is likewise
  visible to a spectator and never to a robot.)
- **Well depletion, map mutation and anchor repair as mechanics.** Wells are infinite, terrain is fixed
  and an anchor's health moves only by occupancy — all three are the engine's own rules, restated here so
  nobody adds a "nice" one.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the watchable
  artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the war.
- **Battlecode years other than 2026, 2020, 2021, 2023, 2024 and 2025.** The registry,
  `game_config.year`, the variant naming and `years/dispatch.nim` all support more; only these six are
  registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. The six places where the spec's
prose and the engine disagree — currents at end of round, the destabiliser's `cast + 4` detonation, the
additive quantised multiplier, one detonation victim per tile, the asymmetric stack guards, and a
headquarters standing on a current — are all resolved **against the pinned engine** in §The game and
recorded as divergences from the prose, not as open questions. The three places where the engine itself
is odd — `resign()` being reachable through an API no doctrine can call, a STANDARD anchor placed over
our own ACCELERATING one leaving its boost registered forever, and the released 3.0.15 jar reporting
`SPEC_VERSION = "3.0.14"` — are resolved in §The game, §Tests and `docs/RULES-BC23.md`. The idea's one
under-specified knob candidate, `well_priority: elixir`, is resolved in §Decisions with its reason: no
map has an elixir well and `elixir_tech` already owns that decision.)*

