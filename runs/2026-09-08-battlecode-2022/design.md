# cogame-battlecode — the `bc22` year module: Battlecode 2022 "Mutation" (design note, 2026-09-08)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a branch/PR of
the shipped repo that adds the year module `bc22` beside the shipped `bc26`, `bc20`, `bc21`, `bc23`,
`bc24` and `bc25`, adds the manifest variant `bc22`, keeps certification on `bc26`, and bumps the
version of the *same* coworld. **There is no `cogame-battlecode-2022` repo and none is created.** The
starter is chosen by game shape and it is the only defensible one: bc22 is the same shape as the six
shipped years — a deterministic Nim grid sim compiled twice (native for the server, wasm for the
viewer), one sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm replay
viewer that re-derives every frame — and the year-module boundary
(`src/battlecode/years/<year>/`, `years/registry.nim`, `years/dispatch.nim`, `game_config.year`)
already exists and has now been proved **five** times, by bc20, bc21, bc23, bc24 and bc25. Lineage:
`coworld-ctf` (paintbot) → `cogame-battlecode` → this. The starter is `Metta-AI/cogame-battlecode`,
and **every convention there holds here unless this note says otherwise**: the Nim
sim/server/player layout, `nimby.lock`, the bitworld runtime contract, the `GameVersion` discipline,
`tools/build_replay_viewer.sh`, the `replay-viewer/` bundle, the `client/` chrome, the
one-parallel-batch doctrine layer (`llm.nim` / `decide.nim` / `sheet.nim` / `sheet_common.nim` /
`baselines.nim`), the closed results document, and "degrade, never hang".

This note lands in the repo as `docs/plans/2026-09-08-battlecode-2022-design.md` on the branch
`bc22-year-module`. The copy of record for the run is
`runs/2026-09-08-battlecode-2022/design.md`.

### Provenance — every rule below was read or measured, not assumed

**The 2022 rules were read from `github.com/battlecode/battlecode22` at commit
`6ed05b679c0822e9bbe332812ff5655812dd023e`** (`HEAD` of the default branch, last commit
2023-01-06 "Reset versions and update build scripts"):
`engine/src/main/battlecode/common/GameConstants.java`, `common/RobotType.java`,
`common/AnomalyType.java`, `common/AnomalyScheduleEntry.java`, `common/RobotMode.java`,
`common/Direction.java`, `common/MapLocation.java`, `common/Team.java`, `common/RobotController.java`,
`world/GameWorld.java` (741 lines, read whole), `world/InternalRobot.java` (497),
`world/RobotControllerImpl.java` (935), `world/ObjectInfo.java` (226), `world/TeamInfo.java` (129),
`world/LiveMap.java` (372), `world/GameMapIO.java` (345), `world/DominationFactor.java`,
`world/IDGenerator.java`, `world/MapSymmetry.java`, `world/control/PlayerControlProvider.java`,
`world/control/TeamControlProvider.java`, `server/GameInfo.java`, `server/GameMaker.java`,
`util/TeamMapping.java`, `schema/battlecode.fbs`, `build.gradle`, `engine/build.gradle`,
`gradle/wrapper/gradle-wrapper.properties`, `client/package.json`, `client/LICENSE`,
`schema/LICENSE`, `engine/COPYING`, `specs/specs.md.html` (the whole 2.2.1 spec, 31 417 bytes) and
`example-bots/src/main/examplefuncsplayer/RobotPlayer.java`.

**The oracle recipe in §Tests was EXECUTED in this sandbox, not guessed.** Temurin **8**
(`8u504-b01`, downloaded from `api.adoptium.net`) + the released `battlecode22-2.2.1.jar` + one
~200-line driver file (`Bc22Trace.java`, the bc23 driver one year back) runs whole **2000-round**
headless games in **16.4–27.4 s each**, and every number quoted below — peak bytecode use, trace
line counts, JVM seconds, robot counts, end reasons, map geometry, the CHARGE tie rate, the rubble
lattice — is a measurement off those runs. It found the same JDK-21 trap bc23 documented
(reproduced here verbatim: `java.lang.IllegalArgumentException` in
`org.objectweb.asm.ClassReader.<init>` from `TeamClassLoaderFactory.normalReader` via
`MethodCostUtil.getMethodData`, on every player class load — under JDK 21 the game ends at
**round 1** with `ANNIHILATION` and no robot ever built, and the job would be green), and it found
**one new load-bearing fact bc23's analysis has no analogue for**: the trove hash order of
`ObjectInfo.robotsArray()` decides who dies to the global CHARGE anomaly in **51–58 % of rounds**
(§Sim module, D2 — measured with a second driver, `Bc22Charge.java`).

**All 75 official `.map22` resources were parsed** for their real sizes, seeds, declared symmetry,
rubble distributions, lead placements, archon counts and full anomaly schedules with a hand-written
flatbuffer vtable walk; the pool table in §Sim module is those measurements. **The arithmetic
lattices were computed by the JVM itself** under Temurin 8 against the jar's own classes: the rubble
cooldown multiplier over every `(rubble 0…100) × (base cooldown ∈ {2,10,16,20,24,25,100,200})` pair,
the anomaly truncations, the reclaim drops, the prototype health, and the laboratory's
`Math.exp` transmutation rate over its whole reachable domain.

**The three licensed behaviour sources were cloned and read**: `iliao2345/Battlecode2022`
(AGPL-3.0, head `c42645a0`, final submission `src/fury_fix_20/`, 19 files / 4 704 lines),
`BSreenivas0713/Battlecode2022` (AGPL-3.0, head `c388fe8a`, final submission `src/MPTempName/`),
`jmerle/battlecode-2022` (MIT, head `f57d3549`, final submission `src/camel_case_v25_final/`).
**`IvanGeffner/BC22` was not cloned, not read and contributes nothing** — it carries no licence.

Base-repo facts are from `Metta-AI/cogame-battlecode` at **`47f36001`** (`main`, the merge of the
bc23 r1 fixes), whose shipped coworld version is **0.6.0** and whose `GameVersion` is **GV09**.
Every `file:line` and constant below is to those trees.

### Source idea (verbatim)

```
ARCHONS build MINERS (lead), SOLDIERS, SAGES (gold, hit hard), BUILDERS (labs and watchtowers, mutations); ANOMALIES strike every ~200 rounds (vortex, abyss, charge, fury) and the SINGULARITY at round 2000 forces tiebreaks. The ranking's canonical PATCH-DRIVEN meta: soldier-rush everywhere, then after a gold-cost cut 'every team shifting to sage spam within hours', anomalies ignored, mutations irrelevant. As a sealed-doctrine game the interesting axis is whether an LLM commander ever finds a use for labs, gold and anomaly timing that the human meta did not.

Seats: 2 (one cog per side). num_agents = 2 in the bc22 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc22 (v1 candidates; the builder finalises them from the chassis it ports): opening {soldier_rush | miner_eco | sage_spam}, miner_count_curve, soldier_sage_ratio, lab_round, gold_use {sages | mutations}, watchtower_policy, anomaly_play {ignore | time_pushes}, archon_relocate, retreat_hp.
Rules, engine, oracle: Spec: https://releases.battlecode.org/specs/battlecode22/2.2.1/specs.md.html (200). Engine: https://github.com/battlecode/battlecode22 (Java 8, Gradle 7.6, engine/COPYING AGPL-3.0). Oracle jar: https://releases.battlecode.org/maven/org/battlecode/battlecode22/2.2.1/battlecode22-2.2.1.jar (200; artifact is battlecode22, not -java).
Chassis and baselines (behaviour sources): iliao2345/Battlecode2022 (wololo, 1st, AGPL-3.0), BSreenivas0713/Battlecode2022 (7th, AGPL-3.0), jmerle/battlecode-2022 (13th-16th, MIT). IvanGeffner/BC22 no licence — reference only. 5 Musketeers not on GitHub.
Ranking: Tier 3 (patch-driven) in the ranking.
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc22` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc22` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc22`, league_name `Battlecode 2022 — Mutation`, default_variant_id `bc22`, short_name `bc22` (softmax.com/battlecode/bc22), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin from the brief and the idea is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; **one new year module `src/battlecode/years/bc22/` + manifest variant `bc22`**; everything else on `main` untouched; **branch-only work on `bc22-year-module`, merged by PR** (the sibling run 2026-09-04-battlecode-2024 is BLOCKED with PR #4 open on this repo) | this paragraph, §Packaging ("Branch discipline") |
| `num_agents = 2` in `variants[bc22].game_config`; all other variants and the bc26 cert fixture unchanged; the `<SEATS>` = 2 cross-check | §The game ("Seats"), §Packaging ("Variants", "The `<SEATS>` cross-check") |
| `GameVersion` **GV09 → GV10**; `ReplayCompatibleGameVersions` EXTENDED, never reset; prior years' semantics unchanged | §Sim module ("Determinism"), §Packaging ("Version bump semantics") |
| Coworld version **0.6.0 → 0.7.0**; certification stays bc26; manifest **`player[]` UNCHANGED** | §Packaging ("Version bump semantics", "`player[]` — UNCHANGED") |
| Sealed one-shot doctrine, ONE parallel batch of 2 LLM calls, `doctrineBudgetMs = 45000`, worst case inside 60 % of `episodeTimeoutSeconds` | §The game ("Match shape and budget"), §Decisions |
| Degrade-never-hang: retry once → verbatim fallback sheet + a `doctrine_fallback` event | §Decisions ("Degrade-never-hang") |
| **No inert chassis**; the economic-survival gate with the `-d:bc22BrokenChassis` NEGATIVE CONTROL | §Decisions ("the anti-inert rule"), §Tests items 17, 18 |
| Full behaviour port to the deterministic Nim sim; `java.util.Random` reproduced; NO Java/JDK/Node in the image; fixed per-robot decision budget instead of bytecode metering (documented divergence) | §Sim module ("Determinism", "The chassis, and the bytecode divergence"), §Packaging, §Out of scope |
| Parity oracle: Java **8** in CI only, Tiers A/A′/B/C, **root-cause-or-fail**, tiers pinned to what the harness actually delivers (measured), the comparator normalising **both** traces identically and its three known bugs fixed | §Tests (`parity-oracle-bc22`) |
| Chassis ported from the BEHAVIOUR of licensed bots only; `IvanGeffner/BC22` never vendored; the strategy surface inside ONE competent chassis | §Decisions ("Scripted baselines"), §Packaging ("Licensing") |
| Doctrine-sheet envelope unwrapped tolerantly, absent-key defaulting counted, submitted-vs-applied divergence rendered (LEARNINGS 2026-09-08) | §Decisions ("The envelope pin"), §Viewer (`#bc22-doctrines`), §Tests item 13 |
| The year's official maps converted at build time from real `.map22` geometry; symmetric seeded pool; anomalies (vortex, abyss, charge, fury) and the round-2000 Singularity tiebreaks in the resolution rules | §Sim module ("Maps"), §The game (rules 4c, 4e) |
| Official 2022 client sprite set, credited | §Viewer ("Art"), §Packaging ("Licensing") |
| Viewer: static wasm, all four files from `cogame-battlecode`, chrome byte-for-byte, appended block, transport rules, **beats emitted + labelled + styled**, zoom decision, 360 px, endcard fixed for this year's nouns | §Viewer |
| Replay self-sufficient; `result` singular; best-of-N clinch semantics | §Server, player, protocol ("Replay"), §The game ("End conditions") |
| Exact signed scoring formula; the league ranks by ELO on match wins and `results.scores` is win-ordered by construction | §The game ("Scoring") |
| Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side) | §The game, §Viewer |
| 2 LLM champions + 2 scripted fillers, same image, env-switched; champion 2 carries `daveey-1`'s `player` id | §Decisions, §Packaging (`tools/ci/policies.json`) |
| Tests: sim units, bounded-orders/legality on the scripted baseline, e2e episode writing a replay with a per-seat **substance** assertion, strict-UTF-8 parse, **executed** viewer smoke, the survival gate + negative control, the parity jobs, the cert probe | §Tests |
| Phase-50 league `bc22` / `Battlecode 2022 — Mutation` / `default_variant_id bc22` / `short_name bc22`, own champions, fillers and credit pool | §Packaging ("The phase-50 plan") |
| `## Out of scope (v1)` non-empty; prose-vs-engine conflicts resolved against the pinned engine; **no `OPEN` section** | §Out of scope (v1) |

### Interface facts this note is written against (read from `47f36001`, not assumed)

- **D1 — the chassis is not an LLM-selectable knob.** A submitted `chassis` is recorded in
  `sheet_unknown_fields` and ignored (`src/battlecode/sheet.nim:104`; `sim_types.nim` GV04 entry).
  **The bc22 sheet has no `chassis` key** and `tests/test_bc22_sheet.nim` asserts the D1 behaviour.
- **D2 — the scripted baseline plays, and CI gates on substance.** bc22's strong baseline (`wololo`)
  is a real bot; the gate is competence + positive play counters, not a win (§Tests items 17, 18 and
  the `docker-smoke` substance assertion).
- **D3 — the doctrine overlay must be dismissible.** `#bc22-doctrines` ships with a close control, an
  `Escape` binding, a re-open chip and self-dismissal on the first advance; it never sits in the
  transport band (§Viewer).
- **The manifest declares exactly the two players the certification fixture seats.** `player[]` is
  `awu` and `scaffold` and **nothing else** (`coworld_manifest_template.json` at `47f36001`);
  `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`
  (`defaultBaselineFor` / `baselineFor`, both already six-armed). The bc20 run lost a release
  dispatch (`players_missing`) by adding year-specific `player[]` entries that occupied no cert slot.
  **This run adds no `player[]` entry** — see the explicit cross-check in §Packaging.
- **`GameVersion` is `GV09`** and `ReplayCompatibleGameVersions` is
  `["GV04","GV05","GV06","GV07","GV08", GameVersion]` (`src/battlecode/sim_types.nim:16,158`). This
  run **extends** that list to `["GV04",…,"GV09", GV10]`; it does not reset it.
  `tools/ci/check_gameversion.sh` compares the *headline*, not the digits, so a sibling branch that
  takes GV10 first forces this branch to GV11 — expected and handled (§Packaging).
- **`ScriptedChassis`** is the year-neutral chassis enum in `sim_types.nim:182` (currently `scAwu,
  scScaffold, scBowlOfChowder, scExamplefuncsplayer, scCaliforniaRoll, scExamplefuncsplayer21,
  scGoneSharkin, scExamplefuncsplayer24, scSpaark, scExamplefuncsplayer25, scLemonade,
  scExamplefuncsplayer23`); bc22 adds two values, and each year's `newSession` already falls back to
  **that year's strong chassis** for a name belonging to another year.
- **`Baseline`** is the parallel enum in `baselines.nim:19` (twelve values); `defaultBaselineFor` and
  `baselineFor` are `case yearIdOf(year)` over six arms. bc22 adds one arm to each and two enum
  values, plus one `baselineChassis` and one `baselineReply` arm. All additive.
- **`sheet.nim:87–91` already unwraps a `"sheet"` envelope key — and ONLY that one.** It does not
  unwrap `"doctrine"`, and `applyKnobs*` records only *repairs*, never *absent* keys, so a champion
  that answers `{"protocol":…,"doctrine":{…}}` silently plays the all-defaults sheet with
  `defaults_applied == []`. That is exactly the bc23 league failure (LEARNINGS 2026-09-08: 2 of the
  first 3 rounds). §Decisions ("The envelope pin") fixes it.
- **`replay.nim:173–176` re-validates the recorded APPLIED sheet**, wrapped in `{"sheet": …}` — never
  `sheet_submitted`. So the envelope fix cannot change how any existing recording re-derives, which
  is why `ReplayCompatibleGameVersions` still extends (§Packaging).
- **`relayout()`'s `--statrail` set already exists** and currently names `econ`, `bc20-soup`,
  `bc20-units`, `bc21-influence`, `bc21-units`, `bc24-crumbs`, `bc24-levels`, `bc25-towers`,
  `bc25-econ`, `bc23-econ`, `bc23-units` (`client/replay_broadcast.html:5529–5531`); `#killfeed`'s
  `bottom` is `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))`
  (line 1270). bc22's job is to **keep the fix armed** — add its two boxes to that list — not to
  re-fix it.
- **`beatsFor` in `src/battlecode/broadcast.nim:134` is the ONE place a beat kind is decided**, and it
  already carries a two-way year discriminator (`let isBc25 = doc.year == "bc25"`,
  `let isBc23 = doc.year == "bc23"`) because `first_action` and `rout` are spelled the same by bc24,
  bc25 and bc23. bc22 emits both of those names too, so those two arms become three-way tests, and
  `duel` (bc23's) gains a year test in the **label** switch (§Viewer, "the beat contract"). The page
  already ships 39 distinct `.beat-marker.<kind>` rules and 47 `html[data-year="bc23"]`-scoped rules;
  bc22 adds its own scoped set.
- **`tools/ci/viewer_smoke.mjs` already carries the scrub-selector fix** (`SCRUB_SELECTORS` tried one
  at a time, `#scrub` first, `#zoom-slider` excluded) and `ci.yml` asserts
  `scrub_selector == "#scrub"` per replay. Nothing to do here except the pacing decision in §Viewer.
- **`tools/ci/docker_smoke.sh` already carries `SMOKE_EXPECT_YEAR`, `SMOKE_PLAYER_IDS`,
  `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`, `SMOKE_CONTRACT_PROBE`, `SMOKE_SEATS` and
  `SMOKE_REQUIRE_STATS`**, and `tools/ci/cert_probe.py` runs inside it. bc22 adds a seventh episode
  and reuses all of them; **no script change is needed**.
- **`replay-viewer/config.nims` needs no edit**: `--preload-file {rootDir}/data@data` already carries
  the whole `data/` tree, so `data/maps/bc22/`, `data/bc22/tables.json` and `data/atlas_bc22.*` ship
  with no link-flag change, and `EXPORTED_FUNCTIONS` gains nothing.
- **`src/battlecode/fdlibm.nim` already ports `StrictMath.exp` bit for bit** (`fdlibmExp`, added for
  bc21's embezzle curve). bc22's laboratory transmutation rate is a `Math.exp` and reuses it — see
  §Sim module, "the one transcendental".
- **`src/battlecode/rng.nim` already ports `java.util.Random`** (`nextInt()`, `nextInt(bound)`,
  `nextBoolean()`) and `IDGenerator`. bc22 needs **both** `IDGenerator` *and* a live
  `Random(mapSeed)` (the VORTEX draw), which is new: bc23 constructed neither.
- **This repo records `result` (singular) in the replay**, not `results` — the 2026-09-07 verify
  lesson — and a best-of-three episode legitimately plays **fewer** games than `gamesPerMatch` when a
  side clinches, with `reason` still `complete`.
- **`end_reason`'s manifest enum already contains `annihilated`** (bc21's `dfAnnihilated`,
  `years/bc21/world.nim:73`), `coin_flip` and `abandoned`. bc22 reuses all three and adds exactly
  three values (§Packaging).
- **The shipped coworld version is 0.6.0.** This run ships **0.7.0**.
- **CI wall clock on this repo is ~65–75 min per round** with six year modules (LEARNINGS
  2026-09-08). The `test` job's `timeout-minutes` goes 110 → **130** and the note's shard budget is
  sized for it (§Tests).

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as bc26/bc20/bc21/bc23/bc24/bc25 (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, six generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. No new repo (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=awu\|scaffold` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc22/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc22` bytes anywhere. |
| Real art, starter chrome verbatim | 2022 sprites cut from `client/visualizer/src/static/img/` into `data/atlas_bc22.*` (credited in `NOTICE` — §Packaging); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc22 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **445 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26\|bc20\|bc21\|bc23\|bc24\|bc25].game_config` (all unchanged) and `variants[bc22].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc22 policy set is in §Packaging. |
| Both champions are LLM prompt policies, champion #1 owned by daveey and #2 by daveey-1; fillers are the scripted baselines, normally 2 | §Packaging (`tools/ci/policies.json`, "The phase-50 plan"). |

---

## The game

**Battlecode 2022 "Mutation", played by doctrine, simulated in Nim.** Two cogs each command a faction
of robots on a symmetric grid between **20×20 and 60×60**. Neither cog moves a robot. At t=0 each
writes a **doctrine** — a JSON sheet of eleven named knobs — and the deterministic sim plays the whole
match from those two sheets while both cogs watch.

Each faction starts with **1 to 4 ARCHONS** (600 HP, indestructible by nothing, and **the only thing
that decides the game**: lose your last archon and you lose immediately). Archons build **MINERS**
(50 Pb) that dig lead and gold out of the map squares, **BUILDERS** (40 Pb) that put up
**LABORATORIES** (180 Pb — the only source of gold in the game) and **WATCHTOWERS** (150 Pb),
**SOLDIERS** (75 Pb, 3 damage, and the whole human metagame), and **SAGES** (20 Au, 45 damage, one
shot every twenty turns, and the only unit that can *envision an anomaly*). Buildings can be
**mutated** to level 2 (lead) and level 3 (gold), and can **transform** between TURRET mode (act, do
not move) and PORTABLE mode (move, do not act) — so an archon can get up and walk.

Every square carries **rubble** (0…100) which multiplies every cooldown a robot pays on it by
`1 + rubble/10`, and some squares carry **lead**. Lead is finite in a way that decides the whole
economy: the map regenerates **+5 Pb every 20 rounds on every square that still holds at least
1 Pb**, so a miner that takes a square to zero **kills that deposit for the rest of the game**.
Gold enters the map only when a robot dies (20 % of its build cost is dropped where it stood — an
archon drops **20 Au**), or is manufactured by a laboratory, whose price in lead per gold is
`⌊20 − 18·e^(−k·n)⌋` in the number `n` of friendly robots the lab can see: **2 Pb per Au for a
lab standing alone, 11 Pb per Au with forty friends nearby.** Alchemists prefer solitude.

And the world is unstable. Each map ships a fixed **anomaly schedule** — every robot can read it —
of roughly one event per 200 rounds drawn from four types: **ABYSS** (10 % of every square's metal
and of both team reserves, gone), **CHARGE** (the top 5 % of *all* droids on the board, ranked by how
many friendly robots each can see, destroyed), **FURY** (every building **in turret mode** loses 5 %
of its maximum health) and **VORTEX** (the rubble map is reflected or rotated according to the map's
symmetry). At round 2000 the **SINGULARITY** consumes the weaker team on a three-rung ladder.

**That is why this year is worth playing sealed.** The 2022 metagame was patch-driven and narrow:
soldier rush everywhere, then a gold-cost cut moved every team to sage spam inside hours, anomalies
ignored and mutations irrelevant. The engine, read closely, says the ignored parts have teeth that
nobody spent: FURY does nothing at all to a building in **PORTABLE** mode, so a faction that reads
the schedule can stand its archons up for one round and take zero; CHARGE ranks the **combined**
droid population of both teams, so the side that clumps donates the victims — and with fewer than
**20** droids on the board it kills *nobody* (measured); ABYSS truncates, so a square holding
**9 or fewer** lead loses nothing; and a lonely laboratory makes gold at **2 Pb** apiece, which is
under three per cent of a sage's lead-equivalent price at the crowded rate. The doctrine sheet in
§Decisions makes labs, gold and anomaly timing *spendable choices with teeth*, and the league is the
experiment.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. The episode seed
decides which slot takes engine-side **A** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc23/maps.nim`).

**Motive: zero-sum.** One side wins a game and the other loses it; there is no cooperative payoff,
no shared reward and nothing to negotiate — the cogs never exchange a byte, and the only channel
between them is the board. The two name spaces follow from that: in-game the factions are the
anonymous aliases **Clan Ash** and **Clan Basil**, so a doctrine cannot be written against a known
opponent, and the real player names (`daveey`, `daveey-1`) exist only in `replay.names[]` /
`results.names[]` and are drawn only by the spectator-side viewer.

### Constants (verbatim from the pinned engine — `common/GameConstants.java`, cross-checked against the jar's own classes under Temurin 8)

Generated into `src/battlecode/years/bc22/constants.nim` by `tools/gen_year_constants.py --year bc22`,
never hand-typed, and re-generated and byte-diffed in CI (§Tests item 24).

| constant | value | constant | value |
|---|---|---|---|
| `SPEC_VERSION` | **"2.2.1"** — and, unlike bc23's and bc25's, it **matches the jar's version**, so §Tests asserts it *as well as* the sha256 | `GAME_MAX_NUMBER_OF_ROUNDS` | **2000** |
| `MAP_MIN_WIDTH`/`_HEIGHT` | **20** | `MAP_MAX_WIDTH`/`_HEIGHT` | **60** |
| `MIN_STARTING_ARCHONS` | **1** | `MAX_STARTING_ARCHONS` | **4** |
| `MIN_RUBBLE` / `MAX_RUBBLE` | **0 / 100** | `COOLDOWN_LIMIT` / `COOLDOWNS_PER_TURN` | **10 / 10** |
| `INITIAL_LEAD_AMOUNT` | **200** per TEAM (not per archon) | `INITIAL_GOLD_AMOUNT` | **0** |
| `PASSIVE_LEAD_INCREASE` | **2** per team per round | `ADD_LEAD_EVERY_ROUNDS` / `ADD_LEAD` | **20 / 5** |
| `TRANSFORM_COOLDOWN` | **100** | `MUTATE_COOLDOWN` | **100** |
| `PROTOTYPE_HP_PERCENTAGE` | **0.8f** | `RECLAIM_COST_MULTIPLIER` | **0.2f** |
| `MAX_LEVEL` | **3** | `SHARED_ARRAY_LENGTH` | **64** |
| `MAX_SHARED_ARRAY_VALUE` | **65535** | `ALCHEMIST_LONELINESS_A` / `_B` | **20.0 / 18.0** (double) |
| `ALCHEMIST_LONELINESS_K_L1/L2/L3` | **0.02 / 0.01 / 0.005** (double) | `GAME_DEFAULT_SEED` | 6370 (unused here) |
| `INDICATOR_STRING_MAX_LENGTH` | 64 — **not ported** (no indicator strings) | `EXCEPTION_BYTECODE_PENALTY` | 500 — **not ported** (no JVM exceptions) |

`RobotType` — the whole table, verbatim, **printed by the jar's own classes** (`buildCostLead,
buildCostGold, actionCooldown, movementCooldown, health, damage, actionRadiusSquared,
visionRadiusSquared, bytecodeLimit`, plus every `getMaxHealth/getDamage/getHealing/…MutateCost/
…Dropped` value per level):

| unit | Pb | Au | act cd | move cd | HP 1/2/3 | dmg 1/2/3 | heal 1/2/3 | act r² | vis r² | bytecode | L2 cost | L3 cost | Pb dropped 1/2/3 | Au dropped 1/2/3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ARCHON` | 0 | **100** (nominal; cannot be built) | **10** | **24** | **600/1080/1944** | −2/−4/−6 | **2/4/6** | **20** | **34** | 20 000 | **300 Pb** | **80 Au** | 0/60/60 | **20/20/36** |
| `LABORATORY` | **180** | 0 | **10** | **24** | 100/180/324 | 0/0/0 | 0 | **0** | **53** | 5 000 | **150 Pb** | **25 Au** | 36/66/66 | 0/0/5 |
| `WATCHTOWER` | **150** | 0 | **10** | **24** | 150/270/486 | **4/8/12** | 0 | **20** | **34** | 10 000 | **150 Pb** | **60 Au** | 30/60/60 | 0/0/12 |
| `MINER` | **50** | 0 | **2** | **20** | 40 | 0 | 0 | **2** | 20 | 10 000 | — | — | 10 | 0 |
| `BUILDER` | **40** | 0 | **10** | **20** | 30 | −2 | **2** | **5** | 20 | 7 500 | — | — | 8 | 0 |
| `SOLDIER` | **75** | 0 | **10** | **16** | 50 | **3** | 0 | **13** | 20 | 10 000 | — | — | 15 | 0 |
| `SAGE` | 0 | **20** | **200** | **25** | 100 | **45** | 0 | **25** | **34** | 10 000 | — | — | 0 | **4** |

`AnomalyType` — verbatim (`isGlobalAnomaly, isSageAnomaly, globalPercentage, sagePercentage`):

| anomaly | global? | sage? | global % | sage % | what it does |
|---|---|---|---|---|---|
| `ABYSS` | yes | yes | **0.1f** | **0.99f** | global: 10 % of every square's Pb and Au **and** of both team reserves. Sage: 99 % of the metal on every square within r² ≤ 25 |
| `CHARGE` | yes | yes | **0.05f** | **0.22f** | global: destroy the top `(int)(0.05 × D)` of **all D droids on the board**, ranked by friendly robots in vision, descending. Sage: every **enemy** droid within r² ≤ 25 loses 22 % of its max HP |
| `FURY` | yes | yes | **0.05f** | **0.1f** | global: every building **in TURRET mode** loses 5 % of its max HP. Sage: 10 %, within r² ≤ 25 |
| `VORTEX` | yes | **no** | 0 | 0 | reflect or rotate the rubble array per the map's declared symmetry |

**A MINER's action cooldown of 2 against a `COOLDOWN_LIMIT` of 10 means a miner can mine up to FIVE
times in one turn on rubble-free ground** (2+2+2+2+2 = 10, and `canActCooldown` is
`actionCooldownTurns < 10`). That is load-bearing, not a curiosity — it is why the whole lead
economy is miner-count-driven — and `tests/test_bc22_cooldown.nim` pins it. On rubble 60 the same
miner pays `(int)((1+6.0)*2) = 14` and mines **once**, which is why `pyramid_raiders` (measured
rubble mean **58.1**) is a different game from `flowers` (mean **5.5**).

### Where the spec's prose and the engine disagree, the engine wins

All nine disagreements are resolved against the pinned engine and recorded in
`docs/RULES-BC22.md` §Divergences:

1. **A transform charges exactly ONE cooldown counter, not both.** The prose says transforming
   "increases both of the Building's cooldowns by 100". `RobotControllerImpl.transform()` flips the
   mode **first** and then charges `TRANSFORM_COOLDOWN` to the **action** counter if the new mode is
   TURRET and to the **movement** counter otherwise. The untouched counter is invisible because the
   new mode gates it (`RobotMode.TURRET.canMove == false`, `PORTABLE.canAct == false`), and
   `canTransformCooldown()`/`getTransformCooldownTurns()` read the *mode-appropriate* counter — so the
   engine is self-consistent and the prose is wrong. The port charges one counter.
2. **The rubble multiplier truncates and is evaluated in float64.** `getCooldownWithMultiplier` is
   `(int) ((1 + getRubble(location) / 10.0) * cooldown)` — a float64 divide, a float64 multiply and a
   **truncation**, not a round, and not the integer form. **Measured on the JVM: over
   `rubble 0…100 × base ∈ {2,10,16,20,24,25,100,200}` the float64 form and the integer form
   `((10+r)*c) div 10` disagree on 22 pairs**, always by one and always with the float one lower —
   e.g. `base 25, rubble 36 → 114` (integer form: 115), `base 100, rubble 13 → 229` (230),
   `base 200, rubble 92 → 2039` (2040). The port reproduces the float64 expression and Tier B tables
   the entire lattice.
3. **Where the multiplier is read.** The prose says "if the robot is located on a square with `r`
   rubble at the conclusion of the action". `addActionCooldownTurns`/`addMovementCooldownTurns` read
   `this.location` at the moment they are called: `move()` moves the robot **first** and then charges
   at the **destination** (the engine's own comment says so), and every other action charges at the
   robot's own unchanged square. `mutate()` charges the **builder's** action cooldown at the
   builder's square and the **building's** 100+100 at the building's square. Nothing else moves.
4. **The passive lead is added BEFORE the anomaly and the map regeneration AFTER it.** The prose
   groups both increases in one sentence and the engine's own changelog claims "Make passive Lead
   increase occur after Anomalies are processed". `processEndOfRound` adds the team's `+2` (A then B)
   as its **first** statement, *then* runs each robot's end of round, *then* the scheduled anomaly,
   *then* the every-20-rounds `+5` to each square holding `> 0` Pb. So an ABYSS on round *r* eats
   10 % of a reserve that already includes that round's `+2`, and it does **not** touch a `+5` that
   has not happened yet. Ordering is a rule; the port keeps it.
5. **CHARGE ranks BOTH teams' droids together, and under 20 droids it kills nobody.**
   `causeChargeGlobal` iterates `objectInfo.robotsArray()` — the *whole* robot table, both teams —
   collects every robot in `DROID` mode, sorts descending by `getNumVisibleFriendlyRobots(false)` and
   destroys the first `(int)(0.05f × droids.size())`. The prose's "the top 5% Droids" hides two
   facts: the ranking is *global*, so a clumped faction donates victims while a spread one loses
   none, and **`(int)(0.05f × n)` is 0 for every `n ≤ 19`** (measured: 19→0, 20→1, 39→1, 40→2, 59→2,
   60→3). Archons, laboratories and watchtowers are never DROID, so CHARGE can never kill a
   building — including a `PROTOTYPE` one.
6. **FURY truncates, and only touches TURRET mode.** `causeFuryUpdate` deals
   `(int)(-1 * maxHealth * reduceFactor)` — a float32 product truncated toward zero — to every robot
   whose `getMode() == TURRET`. **Measured:** a level-1 watchtower (150) loses **7**, not 8; a
   level-2 watchtower (270) loses **13**; a level-3 archon (1944) loses **97**; a level-1 archon
   (600) loses 30; a level-1 laboratory (100) loses 5. A building in **PORTABLE** mode and a
   **PROTOTYPE** take **nothing**. This is the year's largest unexploited play and `anomaly_play`
   (§Decisions) is the knob that reaches it.
7. **FURY's own elimination check skips the archon rung.** `addHealth(…, false)` is called with
   `checkArchonDeath = false`, so a fury that destroys archons does not fire `ANNIHILATION` from
   inside `destroyRobot`; `causeFuryUpdate` then checks both teams afterwards, and **if both are
   eliminated in the same fury it goes straight to `setWinnerIfMoreGoldValue` → `…LeadValue` →
   `setWinnerArbitrary`, skipping `MORE_ARCHONS`.** That is the only path by which
   `more_gold_net_worth`, `more_lead_net_worth` or `coin_flip` can fire **before** round 2000. The
   engine's changelog calls it out ("Trigger tiebreakers if all Archons are destroyed
   simultaneously during Fury") and `tests/test_bc22_endladder.nim` pins it.
8. **ABYSS truncates in float32, so a small pile is immune.** `causeAbyssGridUpdate` computes
   `(int)(0.1f * currentLead)` per square. **Measured: a square holding 1…9 Pb loses 0**; 10→1,
   25→2, 99→9, 100→10, 300→30. The team reserve loses `(int)(-1 * 0.1f * reserve)`, i.e.
   `−⌊reserve/10⌋` (truncation toward zero, so 25 → −2). Combined with divergence 4 and the +5
   regeneration this makes `mine_floor` (§Decisions) a real economic knob rather than a nicety.
9. **Archon ids are below 10 000 and fix the initial turn order.** The prose says "Robots are
   assigned unique random IDs no smaller than 10,000, except for your Archons"; measured, the map
   files carry small ids (`maze`: 2, 3, 6, 7, 8, 9) and `LiveMap`'s constructor sorts its initial
   bodies **ascending by id**, which is exactly the initial `ObjectInfo.dynamicBodyExecOrder`. So
   A and B alternate in the opening turn order and the port must reproduce it.

Two further engine oddities are resolved rather than "fixed": **`resign()` exists and is unreachable**
(it destroys every robot of the resigning team; a doctrine is a JSON sheet and neither chassis calls
it — `docs/RULES-BC22.md` records that it is *unreachable here*, not *absent upstream*, and
`tests/test_bc22_endladder.nim` asserts no chassis reaches it); and **`MIN_RUBBLE` is 0 but three of
the 75 official maps have a minimum of 2 and many have 1**, so "no rubble at all" is a property of
the map, not of the rule set, and on `maze` (minimum 60 on its opening rows) every cooldown starts at
7× base.

### The 2022 rule set — exact numbered resolution rules

The sim's own step list. Steps 1–4 are one round; re-ordering any of them is a rules change and bumps
`GameVersion`. It mirrors `GameWorld.runRound` / `processBeginningOfRound` / `updateDynamicBodies` /
`processEndOfRound` exactly.

1. **Beginning of round.** (a) `currentRound += 1`. (b) The engine then calls
   `processBeginningOfRound` on every robot, which does **exactly one thing: clear the indicator
   string** — and this port has no indicator strings, so step 1b is a **no-op with no observable
   effect**, recorded here so nobody looks for the missing code. There is **no round-1 special
   case**: both teams' 200 Pb and 0 Au are credited by the `GameWorld` constructor, once, per
   **team** (not per archon), before round 1 begins.
2. **Turn order.** Iterate `ObjectInfo.dynamicBodyExecOrder`, a `TIntArrayList` of robot ids with
   **append on spawn** and **by-value removal on death** (`dynamicBodyExecOrder.remove(id)` removes
   the first entry equal to `id`, compacting the list and preserving the order of the survivors). The
   array iterated is a **snapshot taken before the sweep** (`toArray()`), so a robot built this round
   does **not** take a turn this round, and a robot destroyed mid-sweep is skipped by the
   `existsRobot(id)` guard. The initial archons are appended in **ascending id order** (divergence 9).
   Reproducing the list operations literally is a correctness requirement, not a detail
   (`tests/test_bc22_execorder.nim`).
3. **Each robot's turn**, in three parts:
   1. **Beginning of turn**: `actionCooldownTurns = max(0, actionCooldownTurns − 10)`;
      `movementCooldownTurns = max(0, movementCooldownTurns − 10)`; the robot's `DecisionOps` budget
      is reset to **2 000** (archon), **1 250** (miner, soldier, sage, watchtower), **750** (builder)
      or **500** (laboratory) — §Sim module, this replaces the Java bytecode limit. **Both cooldowns
      start a robot's life at 0** (`InternalRobot`'s constructor sets them to 0, not to
      `COOLDOWN_LIMIT`), so a droid built on round *r* takes its first turn on round *r+1* and can
      act and move on it. **This is the opposite of bc23** and it is why bc22 armies grow so fast.
   2. **Run the controller.** The robot runs its team's chassis under that team's doctrine, spending
      at most its `DecisionOps` budget. `assertCanActLocation(loc)` is
      "`distanceSquaredTo(loc) <= actionRadiusSquared` **and** on the map"; `assertIsActionReady` is
      "`mode.canAct` **and** `actionCooldownTurns < 10`"; `assertIsMovementReady` is "`mode.canMove`
      **and** `movementCooldownTurns < 10`". A robot's end of turn is `roundsAlive += 1` and nothing
      else: **there is no per-turn upkeep and no attrition in this year.** The legal actions, with
      their exact preconditions and effects, in the engine's own order of definition:
      1. **Move** (8 directions; `mode.canMove`, i.e. DROID or PORTABLE): movement-ready; the
         destination is **on the map** and **unoccupied** (rubble never blocks — it only costs).
         Effect, in this order: (a) the robot moves; (b) `addMovementCooldownTurns(type.movementCooldown)`
         charges `(int)((1 + rubble(NEW tile)/10.0) × base)` — **read at the destination, after the
         move**.
      2. **Build a robot** (`ARCHON` → MINER \| BUILDER \| SOLDIER \| SAGE; `BUILDER` → LABORATORY \|
         WATCHTOWER; nothing else builds anything): action-ready; the **team** stockpile holds
         `buildCostLead` and `buildCostGold`; the target square is the builder's own square plus one
         of the eight directions, on the map and unoccupied. Effect, in this order: charge
         `(int)((1 + rubble(own square)/10.0) × builderType.actionCooldown)` — **10** for both an
         archon and a builder; deduct both costs from the team; spawn the robot at the next
         `IDGenerator` id. A **droid** spawns in `DROID` mode at
         full health with both cooldowns 0. A **building** spawns in `PROTOTYPE` mode at
         `(int)(0.8f × maxHealth)` — measured 120 for a watchtower, 80 for a laboratory — and can
         neither act nor move until a builder has repaired it to full.
      3. **Attack** (`WATCHTOWER`, `SOLDIER`, `SAGE`): action-ready; the target square is within the
         type's action radius **and on the map**; **there is a robot there** and it is on the **enemy**
         team. Effect: charge `(int)((1 + rubble(own square)/10.0) × actionCooldown)`, then deal
         `getDamage(level)` — 4/8/12 for a watchtower by level, **3** for a soldier, **45** for a
         sage. An attack on an empty square is illegal, and there is **no vision precondition**: a
         soldier can shoot a square it cannot see.
      4. **Envision an anomaly** (`SAGE` only): action-ready; the anomaly is `ABYSS`, `CHARGE` or
         `FURY` (`VORTEX.isSageAnomaly == false`). Effect, in this order: charge
         `(int)((1 + rubble/10.0) × 200)` — twenty turns on flat ground — **then** run the sage
         version over `getAllLocationsWithinRadiusSquared(own square, 25)`:
         **ABYSS** removes `(int)(0.99f × metal)` of Pb and of Au from every square in range;
         **CHARGE** deals `(int)(-1 × 0.22f × maxHealth(level))` to every **enemy** robot in range
         whose mode is `DROID`; **FURY** deals `(int)(-1 × maxHealth(level) × 0.1f)` to every robot in
         range whose mode is `TURRET`, and then runs the same double-elimination check as the global
         fury (divergence 7).
      5. **Repair** (`ARCHON` → any non-building; `BUILDER` → any building): action-ready; the target
         square is in the action radius (20 for an archon, **5** for a builder) and on the map; there
         is a **friendly** robot there of a repairable type. Effect: charge the repairer's own
         `actionCooldown` × the rubble multiplier, then `addHealth(+getHealing(level))` — **2/4/6**
         for an archon by level, **2** for a builder at every level. `addHealth` caps at
         `getMaxHealth(level)` and, **if the target was a `PROTOTYPE` and is now at full health, it
         becomes a `TURRET`**. So a watchtower needs **15** builder repairs to come alive and a
         laboratory **10**.
      6. **Mine lead / mine gold** (`MINER` only): action-ready; the target square is within
         **r² ≤ 2** — which is exactly the miner's own square and all eight neighbours, since a
         diagonal neighbour is at r² = 2 — and on the map; the square holds **≥ 1** of that metal.
         Effect: charge `(int)((1 + rubble(own square)/10.0) × 2)`; move **exactly one unit** from the
         square to the team's reserve. Five mines a turn on flat ground, one on rubble 60.
      7. **Mutate** (`BUILDER` only): action-ready; the target square is within r² ≤ 5 and on the map;
         a **friendly building** stands there whose mode is not `DROID`/`PROTOTYPE` and whose level is
         `< 3`; the **team** holds `getLeadMutateCost(level+1)` and `getGoldMutateCost(level+1)`
         (level 2 costs lead — 300 archon / 150 watchtower / 150 laboratory; level 3 costs gold —
         80 / 60 / 25). Effect, in this order: charge the builder's own action cooldown; deduct both
         costs; `level += 1` and `health += getMaxHealth(new) − getMaxHealth(old)` (so a mutation is
         also a full heal of the difference); then charge the **building** `MUTATE_COOLDOWN = 100` on
         **both** its counters, each through its own square's rubble multiplier.
      8. **Transmute** (`LABORATORY` only): action-ready; the **team** holds at least
         `getTransmutationRate()` lead. The rate is
         `(int)(20.0 − 18.0 × exp(−k × n))` where `k` is 0.02 / 0.01 / 0.005 by the lab's level and
         `n = getNumVisibleFriendlyRobots(true)` — **recomputed on the spot** as
         `senseNearbyRobots(-1, ownTeam).length`, i.e. every friendly robot except itself within
         r² ≤ 53. Effect: charge the lab's own action cooldown × its rubble multiplier; deduct that
         much lead; add **exactly 1 gold**. **Measured rate at level 1**: n=0 → **2**, n=3 → 3,
         n=6 → 4, n=10 → 5, n=13 → 6, n=21 → 8, n=30 → 10, n=40 → 11, n=200 → 19.
      9. **Transform** (any building, i.e. `mode.canTransform`): the mode-appropriate counter is
         `< 10`. Effect: flip TURRET ↔ PORTABLE, **then** charge `TRANSFORM_COOLDOWN = 100` to the
         action counter if the new mode is TURRET and to the movement counter otherwise (divergence 1),
         through the square's rubble multiplier. Ten of its own turns of doing nothing, on flat
         ground.
      10. **Read / write the shared array** (any robot, index 0…63, value 0…65535): **no cooldown, no
          range test, no cost of any kind** — unlike 2023 there is no amplifier and no write window.
          The only price is bytecode, which this port charges as `DecisionOps`.
      11. **Disintegrate**: any robot may destroy itself immediately (the controller throws
          `RobotDeathException`; the control provider's terminated flag makes `updateRobot` destroy it
          at the end of its own turn).
      12. **Sense** (free against `DecisionOps` only): robots, rubble, lead and gold within the type's
          `visionRadiusSquared` — **20** for a miner, builder and soldier, **34** for an archon,
          watchtower and sage, **53** for a laboratory. **There is no fog mechanic beyond the radius**:
          no clouds, no terrain occlusion, and the anomaly schedule (`getAnomalySchedule()`) is
          readable by every robot at all times. Scan order is the engine's:
          `ceiledRadius = ceil(sqrt(r²)) + 1`, then **x ascending outer, y ascending inner**, keeping
          squares with `dx² + dy² ≤ r²`, clamped to the map.
   3. **End of turn**: `roundsAlive += 1`. Then, if the chassis disintegrated, the robot is destroyed.
4. **End of round**, in exactly this order:
   1. **Passive lead**: `+2` to team A's reserve, then `+2` to team B's.
   2. **Every robot's end of round.** `InternalRobot.processEndOfRound` is **empty** in 2022 — a
      genuine no-op, recorded here so nobody looks for the missing code (and see §Sim module D1: it is
      why the engine's hash-ordered `eachRobot` sweep needs no port at either of its two sites).
   3. **The scheduled anomaly**, if `map.viewNextAnomaly().roundNumber == currentRound`. Exactly one
      entry is consumed per round (`takeNextAnomaly`), and the four bodies are:
      - **ABYSS**: for every square of the map in the engine's whole-map scan order, remove
        `(int)(0.1f × lead)` and `(int)(0.1f × gold)`; then remove `⌊0.1 × reserve⌋` from A's lead,
        B's lead, A's gold and B's gold, **in that order**.
      - **CHARGE**: collect every `DROID`-mode robot of **both teams** in `robotsArray()` order,
        calling `updateNumVisibleFriendlyRobots()` on each; **stable-sort** descending by that count;
        destroy the first `(int)(0.05f × count)`, in that order, each through the ordinary
        `destroyRobot` path (so each drops its reclaim metal and each can fire `ANNIHILATION`).
      - **FURY**: for every square in whole-map scan order, if a robot stands there **in TURRET
        mode**, deal `(int)(-1 × maxHealth(level) × 0.05f)` with `checkArchonDeath = false`; then run
        the double-elimination check (divergence 7).
      - **VORTEX**: mutate the **rubble array only** (never the lead or gold arrays, never the
        `LiveMap`) per `map.getSymmetry()`: `VERTICAL` → reflect across the horizontal centre line
        (`flipRubbleVertically`, `changeIdx = 2`); `HORIZONTAL` → reflect across the vertical centre
        line (`flipRubbleHorizontally`, `changeIdx = 1`); `ROTATIONAL` → draw
        `rand.nextInt(width == height ? 3 : 2)` and, **on a non-square map, add 1**, then
        `0 → rotate 90° clockwise`, `1 → flip horizontally`, `2 → flip vertically`. The draw comes
        from `GameWorld.rand`, a `java.util.Random` seeded with the **map seed** — the only place in
        the 2022 round loop that reads it, and therefore a hard fidelity requirement (§Sim module D4).
   4. **Map lead regeneration**: if `currentRound % 20 == 0`, add **+5** to every index of the lead
      array whose value is **`> 0`**. A square mined to zero is dead for the rest of the game.
   5. **Roll over** the per-round team deltas (`TeamInfo.processEndOfRound`).
   6. **End-of-match check**: if `currentRound >= map.getRounds()` (2000) **and no winner is set
      yet**, apply the Singularity ladder, first hit wins — **more archons alive**
      (`more_archons`) → **greater gold net worth** (`more_gold_net_worth`) → **greater lead net
      worth** (`more_lead_net_worth`) → **coin flip** (`coin_flip`). "Net worth" is the team's
      reserve **plus** `getGoldWorth(level)` / `getLeadWorth(level)` summed over every live robot of
      that team, so a level-3 archon is worth 300 Pb and 180 Au of net worth while it lives.
   7. If a winner is set — by the ladder, by the mid-turn `ANNIHILATION` inside `destroyRobot`, or by
      the fury check in 4c — the game stops. Then append this round's state hash (§Sim module).

**Four subtleties the port reproduces literally, each with its own test:**

- **`ANNIHILATION` fires mid-turn and does not stop the round.** `destroyRobot` runs
  `if (type == ARCHON && getRobotTypeCount(team, ARCHON) == 0) setWinner(other, ANNIHILATION)`, and
  `running` is only cleared at step 4g, so every robot after the killer in the exec order still takes
  its turn and every action is recorded. `tests/test_bc22_endladder.nim` pins it.
- **Both teams can be annihilated in the same round** — the engine's own comment says so — and only
  the fury path handles it specially (divergence 7). Outside a fury, the *second* team's last-archon
  death simply overwrites the winner with the other team, so the ordering of two archon deaths inside
  one round is load-bearing and follows the exec order.
- **`addHealth` is the single mutation point for health, and it is re-entrant.** It caps at max,
  promotes a full-health `PROTOTYPE` to `TURRET`, and calls `destroyRobot` at `≤ 0` — from inside a
  repair, an attack, a mutation and every anomaly. The port keeps one `addHealth` with the same three
  responsibilities rather than four copies.
- **A robot's reclaim drop lands on the square it last occupied, and stacks.** `destroyRobot` adds
  `getLeadDropped(level)` and `getGoldDropped(level)` to that index of the lead/gold arrays. So a
  killing field accumulates metal — and **because gold enters the map only this way, an archon's
  death drops 20 Au (36 at level 3) that the enemy's miners can pick up.**

**Deliberate non-rules, verified absent from the 2022 engine and therefore absent here:** there is no
terrain other than rubble (no walls — every square is passable, only slow), no water, no elevation;
rubble is never created or destroyed except by a VORTEX, which only permutes it; lead and gold squares
are never created except by reclaim drops and the +5 regeneration; there is no unit cap of any kind;
there is no per-turn upkeep; buildings other than archons cannot be built by archons and archons
cannot be built at all; `net.sf.jsi`'s RTree in `ObjectInfo` is written on every spawn/move/death and
**never read for any gameplay decision** (`getAllRobotsWithinRadiusSquared` scans locations, not the
index), so it has no port — which is exactly the dead-artifact problem that forced bc21's jsi shim,
absent here twice over (§Tests); `RobotControllerImpl.random` is a `static` field reassigned in every
controller constructor and **never read** (the port does not create it); the map file's `symmetry`
field is recorded **and used** — by VORTEX, unlike every other year, where it is inert; and the
profiler, indicator strings, indicator dots and indicator lines are instrumentation with no port.

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc22` variant is **best-of-three on three
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

Honest per-round estimate, so the builder can check it. bc22's cost is **unit-count driven**, and the
unit count is bounded only by the lead economy: a miner is 50 Pb and a soldier 75 Pb against a passive
income of 2 Pb/round plus whatever the miners dig, and a miner mines up to five units a turn.
**Measured on the real engine in this sandbox**, the official example bot against itself carries
**85–135 robots on the board on average** and peaks at **108–204** on 20×20 to 30×30 maps
(**349** on 60×60 `vortex`), over full 2000-round games that each took **16.4–27.4 s of instrumented
JVM**. So:

- Each robot's turn is a ≤ 69-square vision sweep (r² ≤ 20; 121 at r² ≤ 34 for archons, watchtowers
  and sages; 177 at r² ≤ 53 for laboratories), a bounded navigation step and one to five actions ≈
  **300 `DecisionOps`**, so at a budgeted worst case of **200 robots/round** that is 6 × 10⁴
  ops/round and 1.2 × 10⁸ per game — **3–7 ms/round, 6–14 s per game** in release Nim. The *enforced*
  ceiling is the per-robot `DecisionOps` budget, which caps a round at `200 × 1250 = 2.5 × 10⁵` ops.
- The one structurally unbounded primitive in the rule set is the chassis's own pathfinding BFS. The
  port charges **1 `DecisionOps` per node expanded**, and because the budget is checked **before**
  each primitive and never inside one, a BFS is never cut in half (§Sim module).
- `perGameBudgetSeconds = 110` and `matchBudgetSeconds = 340` are hard monotonic-clock guards. A game
  that blows its guard is abandoned, the finished games are scored, and `results.reason = deadline`.
- `tests/test_bc22_perf.nim` plays a full 2000-round game on `fisherman` (45×35 = 1 575 squares, the
  largest map in the played `mixed` pool, **3 archons a side** at rubble mean 13.9 — i.e. the most
  build actions per round on the fastest ground, which is what maximises the robot census) with
  **both seats on `opening: miner_eco`,
  `miner_count_curve: heavy`, `mine_floor: 0`, `retreat_hp: 0`** — the configuration that maximises
  robot count and therefore per-round work — and **fails CI above 100 s**.
- If that gate ever goes red the fix is one config value — `gamesPerMatch: 3 → 1` in the `bc22`
  variant — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc22's axis is **map-economy-shaped**: the same
  doctrine pays very differently on `intersection` (measured 2 000 Pb on 40 squares, so miners
  saturate and the game is a soldier war) than on `pyramid_raiders` (150 Pb on 30 squares at rubble
  mean 58, so every unit is precious and a lab is worth more than four soldiers). The `mixed` pool
  spans that axis deliberately (§Sim module, Maps). One map would rank the map, not the doctrine.
- **Because this sim is heavy (well above 1 ms/round), the phase-60 viewer check 8 is dispatched with
  `settle=20000 soak=15`** and `ci.yml`'s `wasm-viewer` job runs the bc22 replay at
  `--timeout 120 --soak 15` (§Viewer, the bc21 lesson).

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

### Scoring, sign, and what the bc22 league ranks by

The 2022 game is win/lose; it has no point formula. This one is defined here, and it is a continuous
reading of the engine's own Singularity ladder so that the score and the winner never tell different
stories:

```
share(x, y) = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
archons[t]  = archons of t ALIVE at the final round                        # rung 1
gold[t]     = t's gold reserve + sum(getGoldWorth(level)) over t's live robots   # rung 2
lead[t]     = t's lead reserve + sum(getLeadWorth(level)) over t's live robots   # rung 3
points[t]   = int(64.0'f32 * share(archons[t], archons[o])
                + 24.0'f32 * share(gold[t],    gold[o])
                + 12.0'f32 * share(lead[t],    lead[o]))     # TRUNCATION, not rounding
```

Five load-bearing details, each pinned by a test vector in `tests/test_bc22_scoring.nim`:

- every share is narrowed through **float32** before the weighted sum, and the sum is **truncated** by
  the `int()` cast. The reason is **recorder/re-deriver agreement**: the same arithmetic runs natively
  on x86-64 and in wasm32 and must produce the same integer;
- the three terms are exactly the engine's three deciding rungs, in the engine's own priority order,
  and the two net-worth terms are computed with the engine's own `getGoldWorth`/`getLeadWorth` so a
  mutated building counts what the ladder says it counts;
- the weights are **super-increasing** (`24 > 12` and `64 > 24 + 12`), so a *decisive* margin on a
  higher rung dominates everything below it. **This note does not claim more than that.** A one-unit
  margin on a rung with large totals gives an arbitrarily small share advantage (18 archons cannot
  happen, but 4 vs 3 archons is `4/7 − 3/7 = 0.143`, i.e. 9.1 points, against 36 available below), so
  **`points` alone can favour the loser** — as it can in bc23. `points` measures the *shape* of the
  game, not who won it, and the thing the ladder reads is win-dominated by construction:

```
results.scores[t] = 200.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** With `points ∈ [0, 100]`, a 2–0 gives 400+`mean` against ≤ 100, and a 2–1 gives
400+`mean` against 200+`mean` ≤ 300 — so the ordering of `results.scores` **provably** agrees with
`results.wins` in every reachable case, including a clinched best-of-three that played only two
games. `tests/test_bc22_scoring.nim` asserts that agreement on 500 random synthetic finals, and
asserts the super-increasing property and the documented `points`-disagreement case explicitly, so
neither is mistaken for a bug later.

- `share` returns **0.5 on a 0–0 total**, the same choice bc23/bc24/bc25 made and for the same reason:
  two factions that both ended with zero gold should not be scored differently by an arithmetic
  accident. On this year's evidence that case is the *common* one for gold — the measured mirror
  games ended with **0 Au on both sides in every game**, because the example bot never builds a
  laboratory — so the reachable range of `points` in a passive match is narrow and the archon and
  lead terms do the separating, which is exactly the ladder's own priority;
- points are in `[0, 100]` and the two seats' points sum to ≤ 100.

**The `bc22` league ranks by ELO over match wins**, computed by the platform from the episode's
winner; `results.scores` is the per-episode number the ladder reads and its ordering agrees with
`results.wins` exactly, as above — the same shape as the six shipped leagues. A `deadline` episode
scores the games that finished; a `fault` episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` in snake_case, plus our one
wall-clock value:

| `end_reason` | engine origin | meaning | can fire early? |
|---|---|---|---|
| `annihilated` | `ANNIHILATION` | a faction's **last archon** was destroyed; fires the instant it dies, mid-turn | **yes** — the normal way a bc22 game ends |
| `more_archons` | `MORE_ARCHONS` | round 2000 reached; more archons alive | no |
| `more_gold_net_worth` | `MORE_GOLD_NET_WORTH` | archons tied; greater gold net worth | **yes**, but only through the fury double-elimination path (divergence 7) |
| `more_lead_net_worth` | `MORE_LEAD_NET_WORTH` | gold tied; greater lead net worth | **yes**, same path |
| `coin_flip` | `WON_BY_DUBIOUS_REASONS` | everything tied; a draw from the world RNG | **yes**, same path |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded | — |

`annihilated`, `coin_flip` and `abandoned` are **already** in the manifest's `end_reason` enum
(bc21's and bc26's); `more_archons`, `more_gold_net_worth` and `more_lead_net_worth` are added
(§Packaging). **`resignation` is not added** (unreachable — above). There is no
`destroy_all_units`-style value: losing every *droid* ends nothing, and a faction with one archon and
no other robot plays on to round 2000 earning 2 Pb a round.

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from the six shipped
years**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped (a spend that would take a reserve negative — the engine's own `addLead`/`addGold` throw on that — or the port's own state-hash invariant): a partial replay and `[0, 0]` are still written | `[0, 0]` |

**Best-of-N clinch semantics, stated because phase 60 has judged this wrong before (2026-09-07):** a
side that takes 2 games settles the episode immediately. An episode that records **two** games with
`reason: complete` on a `gamesPerMatch: 3` variant is **correct**, not truncated; `results.games`
carries only the games actually played, and `replay.plan.maps` carries all three drawn maps so a
spectator can see what the third would have been.

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the six
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

### The envelope pin — the one year-neutral change this run makes, and why

**LEARNINGS 2026-09-08, from this repo's own bc23 league:** LLM champions sometimes wrap the sheet in
a protocol envelope (`{"protocol":…,"doctrine":{…}}`). `sheet.nim:87–91` unwraps a key named
`"sheet"` and **only** that one, so all eleven knobs land in `sheet_unknown_fields`, the seat plays
the schema-default sheet, `sheet_defaults_applied` stays **empty** (the keys were *absent*, not
malformed), and the endcard renders the applied sheet as if the cog had written it. **It happened in
2 of the first 3 bc23 rounds and one champion won on defaults.** Three concrete fixes, and the note
pins all three:

1. **Tolerant envelope unwrap, year-neutral, in `sheet.nim`.** Before knob parsing, `validate`
   resolves the sheet node in this order and records which rule fired in a new
   `Sheet.envelope: string` field (additive):
   - `""` — the payload itself carries at least one **known** knob key for this year → use the
     payload (today's behaviour, unchanged);
   - `"sheet"` — `payload["sheet"]` is a `JObject` (today's behaviour, unchanged);
   - `"doctrine"` — `payload["doctrine"]` is a `JObject` (**new**);
   - `"<key>"` — the payload has **exactly one** key whose value is a `JObject` and the payload's own
     keys include **no** known knob name (**new**, and it is what catches
     `{"battlecode_2022_doctrine": {…}}`);
   - otherwise `""` and the payload is used as today.
   Key names are matched through the existing `normalizeKey` (trim, lowercase, `-`/space → `_`), so
   `"Doctrine"` and `"my-sheet"` resolve. Nesting is unwrapped **at most once** — a deliberate bound,
   so a malicious 500-deep reply cannot cost anything.
   **This cannot change how any recording re-derives**: `replay.nim:173–176` re-validates the recorded
   **applied** sheet, wrapped in `{"sheet": …}`, and an applied sheet is always a flat object of known
   keys. `GameVersion` still bumps, because live decision behaviour changes; the compatibility list
   still **extends**, because no recorded byte changes meaning (§Packaging).
2. **Absent-key defaulting is counted — in `years/bc22/knobs.nim` only.** `applyKnobs22` adds an
   **absent** known key to `defaultsApplied` as well as a repaired one, so `sheet_defaults_applied`
   for a bc22 seat is `[]` only when the cog really set all eleven knobs. This is deliberately
   **not** done year-neutrally in `sheet.nim`: doing so would change what a bc26/bc20/bc21/bc23/
   bc24/bc25 episode records in that array, which is the one thing "prior years' semantics unchanged"
   forbids. `tests/test_bc22_sheet.nim` asserts a bc22 empty sheet reports all eleven names and a
   bc23 empty sheet still reports none.
3. **The divergence is rendered.** `#bc22-doctrines` draws, per seat, the applied sheet in plain
   words **and** a badge when the two disagree: `envelope: doctrine`, `11 of 11 knobs defaulted`, and
   the first 120 runes of `sheet_submitted` under a "what the cog actually sent" disclosure. A seat
   that played the default sheet is visible to a spectator in one glance, which is the whole point of
   the finding.

### The bc22 doctrine sheet — eleven knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc22 chassis. Unknown key, wrong
type or out-of-range value → **that field's default** (integers **clamp** instead), recorded in
`sheet_defaults_applied` / `sheet_unknown_fields`. A sheet can never be rejected, so a cog can never
forfeit a match by answering badly — only by answering weakly.

**The anti-inert rule, stated as a rule the builder must hold every knob against: no setting of any
knob, and no combination of settings, may produce an inert or self-starving faction.** The strategy
surface lives *inside one competent chassis*. Concretely, and independently of every knob, the
chassis always: keeps at least **3 miners per archon** digging the nearest lead and never fewer;
builds a soldier whenever lead allows and the soldier census is below its target; spends an archon's
action rather than banking it; answers an enemy attacker sensed within r² ≤ 20 of one of its own
archons; repairs a damaged droid standing in an archon's r² ≤ 20; and never lets its **last** archon
enter PORTABLE mode while an enemy attacker is sensed within eight squares. Every knob moves *how
much of what, when* — never *whether it plays*. `tests/test_bc22_knobs.nim` proves each knob has
teeth and `tests/test_bc22_survival.nim` proves the floor holds, **with a negative control that must
fail** (§Tests items 17, 18).

| field | type / values | default | what it changes (`src/battlecode/years/bc22/chassis/…`) |
|---|---|---|---|
| `opening` | `soldier_rush` \| `miner_eco` \| `sage_spam` | `miner_eco` | `econ.nim plan()` — the lead split for the first 400 rounds. `soldier_rush`: the miner census is held at the 3-per-archon floor and every other lead goes to soldiers, whose spearhead leaves for the enemy's nearest archon at round 1. `miner_eco`: 8 miners per archon (or one per two visible lead squares, whichever is smaller) before the second soldier, but **soldiers are still built** — the census target is halved, never zeroed. `sage_spam`: `lab_round` is pulled forward to `min(lab_round, 150)`, the faction banks lead to the lab's transmute price instead of spending it, and every 20 Au becomes a sage. Sages cost **gold**, of which the faction starts with **zero**, so this value is a *gold programme*, not a round-1 build order — which is exactly the patch-driven meta the idea names, made explicit. |
| `miner_count_curve` | `lean` \| `steady` \| `heavy` | `steady` | `econ.nim minerTarget()` — the miner census per archon as a function of round and **remembered live lead squares**. `lean`: 3 + one per four squares, capped 6. `steady`: 3 + one per two squares, capped 12. `heavy`: 4 + one per square, capped 20 — which saturates the map and, on a poor map, spends more on miners than they dig back. The floor of 3 is unconditional at every value. |
| `mine_floor` | int **0 … 5** | 1 | `miner.nim mineUntil()` — **the year's signature knob, and it is measured, not invented.** How much lead a miner leaves on a square. The map adds **+5 every 20 rounds to every square holding ≥ 1**, so mining to 0 destroys that deposit permanently; and the global ABYSS removes `⌊0.1 × square⌋`, which is **0 for any square holding ≤ 9**. At `0` the faction strip-mines (maximum income now, a dead map by round 900 — measured: the example-bot mirror on `charge` ran the whole map to zero lead at **round 934**). At `1` — the first-place bot's own `mine_until` — every worked square regenerates for ever. At `5` the faction farms conservatively and leaves 20 % of every 25-square. The chassis overrides the floor to `0` when it is **losing on archons** (the first-place bot's own rule), at every setting, because a doomed faction does not need a farm. |
| `soldier_sage_ratio` | int **0 … 100** | 65 | `econ.nim attackMix()` — the percentage of the faction's **attack budget, measured in lead-equivalent**, that goes to soldiers rather than to gold-for-sages, where a sage's lead-equivalent is `20 × the lab's current transmute rate` (2 Pb/Au alone, 11 Pb/Au crowded — §The game). At 100 the faction never banks lead for transmutation and builds only soldiers. At 0 it holds lead at the transmute price and turns every 20 Au into a sage — **and still builds a soldier whenever no laboratory exists**, which is the floor that keeps 0 from being inert. Clamped to the range, so no doctrine can express "no attackers". |
| `lab_round` | int **1 … 1800** | 300 | `lab.nim schedule()` — the first round at which a builder is commissioned and the first LABORATORY is placed. A lab is 180 Pb **plus 10 builder repair actions** to bring an 80-HP prototype to 100, so it is a real investment; `opening: sage_spam` pulls this forward to at most 150. Clamped. |
| `lab_solitude` | int **0 … 40** | 12 | `lab.nim solitude()` — the maximum number of friendly robots the lab tolerates inside its r² ≤ 53 vision before it stops transmuting and (in TURRET mode) transforms to PORTABLE and walks away from the crowd. The transmute price is `⌊20 − 18·e^(−0.02n)⌋`, so **12 is exactly the first-place bot's own gate** (`transmute_cost < 6` ⟺ `n ≤ 12`, measured). At 0 the lab transmutes only when utterly alone, at **2 Pb per gold**; at 40 it transmutes at any price up to 11. The lab's placement follows: `lab.nim site()` picks the lowest-rubble square at least six squares from every archon and every remembered lead cluster. |
| `gold_use` | `sages` \| `mutations` | `sages` | `gold.nim sink()` — what gold buys once it flows. `sages`: 20 Au each, 45 damage, one shot every twenty turns, and the only unit that can envision an anomaly. `mutations`: the **level-3** mutations, which cost gold — 80 Au for an archon (1944 HP and +6 repair), 60 Au for a watchtower (12 damage), 25 Au for a laboratory (k = 0.005, i.e. 2 Pb/Au out to n = 8). Level-2 mutations cost **lead** and are governed by `watchtower_policy` and the archon programme, not by this knob. Under `soldier_sage_ratio: 100` this knob has nothing to spend — that is the *doctrine's own* choice, not a dropped field: the value is still recorded and the viewer's plain-words panel says "no gold programme, so its sink never opens". |
| `watchtower_policy` | `never` \| `home` \| `forward` | `home` | `builder.nim towers()` — whether builders put up watchtowers and where. A watchtower is 150 Pb and **15 builder repairs** (120 → 150 at 2 HP a repair) before it can fire at all, and it fires 4 damage at r² ≤ 20 — which is 150 HP of wall plus a soldier's worth of damage that never moves. `never`: no watchtowers, and the builder's lead goes to laboratories. `home`: one per archon, placed in the lowest-rubble square within four of the archon, level-2-mutated (150 Pb) once the second lab exists. `forward`: built at the frontier the strike group holds, which is the play the 2022 meta never made. |
| `anomaly_play` | `ignore` \| `time_pushes` | `time_pushes` | `anomaly.nim plan()` — **the axis the idea is actually asking about.** `ignore` never calls `getAnomalySchedule()`; the faction plays as if the world were stable, which is what the human meta did. `time_pushes` reads the schedule at the start of every turn and does five specific things, each of which the engine actually rewards (§The game, divergences 5–8, and every one of them measured): (a) **before a FURY** (which only damages TURRET-mode buildings and truncates), transform every building whose transform counter is ready to PORTABLE on round `r−11` and back on `r+1` — the archons lose ~20 turns of building and take **zero**; (b) **before a CHARGE**, scatter droids so no friendly robot sees more than four others, because the ranking is over the **combined** droid population and the clumped side donates the victims; (c) **immediately after a CHARGE**, push with the strike group, into an enemy that just lost its densest 5 %; (d) **before an ABYSS**, spend the reserve down rather than hold it (10 % of the bank, gone) and stop mining squares above 9 Pb, which lose nothing; (e) **before a VORTEX**, relocate any archon whose square is about to become high-rubble under the map's own symmetry — computable exactly, because the reflection is deterministic for HORIZONTAL and VERTICAL maps and one of three known permutations for ROTATIONAL. The first-place bot does only (e). |
| `archon_relocate` | `never` \| `safety` \| `lead` | `safety` | `archon.nim relocate()` — whether an archon transforms to PORTABLE (100 movement cooldown, ten of its own turns inert, movement cooldown 24 × rubble per step afterwards) and walks. `never`: archons never leave their opening square — but they still transform for `anomaly_play`'s fury dodge, which is a different decision and is governed by that knob. `safety`: relocate away from a sensed attacker or a square about to become high-rubble, and **never** when this is the faction's last archon and an enemy attacker is inside eight squares. `lead`: additionally walk toward the richest remembered unmined cluster, which the measured maps make attractive (on `intersection` the 2 000 Pb sits on 40 squares in two bands). |
| `retreat_hp` | int **0 … 100** | 40 | `micro.nim retreat()` — the percentage of maximum health at which a droid disengages toward the nearest friendly archon (repair 2/4/6 a turn at r² ≤ 20 — the only healing in the game). At 0 nothing retreats; at 100 a droid withdraws on first damage. At **every** setting the chassis still takes an attack that **kills** its target and still fights when it is cornered against the map edge, because refusing a free kill is not a strategy. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — the patch-driven human meta against the
gold-and-anomaly game nobody played — so the league's headline matchup is the question this year
never got asked.

- **champion #1, `battlecode-bc22-rush` (daveey)**: *"You command a faction in Battlecode 2022
  'Mutation'. History says this year is decided in the first four hundred rounds by soldiers: a
  soldier costs 75 lead, has 50 health and deals 3 damage at range 13, and an archon has 600 health
  and is the only thing that matters — kill the last one and you win instantly. Your doctrine: out-mine
  them early, out-soldier them by round 400, and never let a lab or an anomaly distract you. Set
  opening \"soldier_rush\" or \"miner_eco\", miner_count_curve \"steady\" or \"heavy\",
  soldier_sage_ratio high (80-100), lab_round late (900-1800), gold_use \"sages\" (it will rarely
  fire), watchtower_policy \"home\" so your archons are not naked, archon_relocate \"never\" or
  \"safety\", and retreat_hp low (0-25) so wounded soldiers keep trading. Set mine_floor to 1: the map
  adds 5 lead every 20 rounds to every square that still has at least 1 on it, so a miner that takes a
  square to zero has destroyed that deposit for the rest of the game — the single cheapest mistake in
  this year. Choose anomaly_play deliberately and say why: \"ignore\" is what every human team did. In
  notes, say which enemy archon you break first and what you do if the soldier war is even at round
  800."*
- **champion #2, `battlecode-bc22-transmuter` (daveey-1)**: *"You command a faction in Battlecode 2022
  'Mutation'. Everyone in 2022 rushed soldiers and ignored three things the engine actually rewards.
  First, gold: a laboratory turns lead into gold at 20 minus 18 times e to the minus 0.02 times the
  number of friendly robots it can see — 2 lead per gold standing alone, 11 in a crowd — and 20 gold
  is a sage, which deals 45 damage, fifteen times a soldier's. Second, anomalies: the schedule is
  public, a FURY only damages buildings in TURRET mode (a building in PORTABLE mode takes nothing), a
  CHARGE destroys the top 5% of ALL droids on the board ranked by how many friends each can see (so
  the side that clumps donates the victims, and under 20 droids it kills nobody), and an ABYSS takes
  10% rounded down (so a square holding 9 or fewer lead loses nothing). Third, mutations: 80 gold turns
  an archon into 1944 health that repairs 6 a turn. Your doctrine: set opening \"sage_spam\" or
  \"miner_eco\", lab_round early (100-350), lab_solitude low (0-8) so your lab makes gold at 2 or 3
  lead apiece, soldier_sage_ratio low-to-middling (10-45), gold_use \"sages\" or \"mutations\" and say
  which, anomaly_play \"time_pushes\", archon_relocate \"safety\", watchtower_policy \"home\" or
  \"forward\", mine_floor 1 or 2 and retreat_hp 40-70 so your gold units survive to shoot twice. In
  notes, say what your first 60 gold buys and which anomaly you intend to be standing on the right side
  of."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the constant tables (the seven unit types with their per-level health, damage,
repair, mutation costs and reclaim drops; the rubble multiplier; the lead regeneration rule; the four
anomalies with their exact truncated arithmetic; the transmutation curve), the map cards for all three
games with their rubble and lead profiles **and their full anomaly schedules**, the scoring formula,
the alias pair, a **HOW A GAME ENDS** section (the bc21 r1-F8 fix, kept), and the reply contract
("reply with ONE JSON object whose top-level keys are the knob names; your reply must begin with
`{`"). The assistant turn is prefilled with `{` and the prefix re-attached before parsing (the procgen
0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`). It gains a `bc22`
arm with two published names. **The manifest still declares only `awu` and `scaffold`** — the two ids
the certification fixture seats — and `PLAYER_SCRIPTED` resolves per year, exactly as bc20, bc21,
bc23, bc24 and bc25 do:

| `PLAYER_SCRIPTED` | on `year: "bc22"` resolves to |
|---|---|
| `awu`, `wololo`, or anything unrecognised | **`wololo`** — the strong published doctrine and the champion chassis |
| `scaffold`, `examplefuncsplayer`, `examplefuncsplayer22`, `example` | **`examplefuncsplayer22`** — the deliberately weak floor and the oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field (D1).
`defaultBaselineFor("bc22")` is `wololo`, so a seat that says nothing useful plays the strong
doctrine, not the weak floor. `Baseline` gains `blWololo = "wololo"` and
`blExamplefuncsplayer22 = "examplefuncsplayer22"`; `ScriptedChassis` gains `scWololo = "wololo"` and
`scExamplefuncsplayer22 = "examplefuncsplayer22"`.

**`wololo` — the strong baseline and the champion chassis.** Behaviour ported from
`iliao2345/Battlecode2022` `src/fury_fix_20/` (AGPL-3.0, head `c42645a0`; the 1st-place bot
"wololo", whose `fury_fix_20` directory is the highest-numbered and therefore final iteration —
19 files, 4 704 lines, read whole), with the **laboratory and builder programme** from
`BSreenivas0713/Battlecode2022` `src/MPTempName/` (AGPL-3.0, head `c388fe8a`; 7th place, and the bot
whose directory list — `MPLaboratory`, `MPMoreLabs` — shows it actually iterated on the gold economy),
and the **shared-array layout and the Dijkstra navigators** from `jmerle/battlecode-2022`
`src/camel_case_v25_final/` (MIT, head `f57d3549`, `util/SharedArray.java` +
`dijkstra/Dijkstra20|34|53.java`) — all parameterised by the eleven knobs. Its scripted reply is the
all-defaults sheet. Algorithm, by file:

- **`kit.nim`** — the per-side memory every robot shares: the remembered map (rubble, last-seen lead
  and gold per square with the round it was seen, and a **dead-square set** for squares seen at 0
  lead), the enemy-archon guess by the map's declared symmetry (all three reflections are candidates
  and are eliminated as squares are sensed — `jmerle/util` behaviour), and the navigator: a bounded
  BFS over the sensed window plus the remembered map, **weighted by `1 + rubble/10`** because that is
  literally the cooldown it will pay (`fury_fix_20/Bfs.java` + `Pathing.java` behaviour), falling back
  to a greedy step with a 6-square no-repeat history to break oscillation. Every node expanded is
  charged against `DecisionOps`.
- **`econ.nim`** — the build plan: `plan()` (from `opening`), `minerTarget()` (from
  `miner_count_curve`), `attackMix()` (from `soldier_sage_ratio`), and the per-archon commitment
  ledger, so two archons cannot promise the same 75 Pb. It is the only place lead or gold is ever
  committed. It carries `fury_fix_20/Archon.java`'s own saturation caps
  (`SOLDIER_SATURATION_CAP = 400`, `WATCHTOWER_SATURATION_CAP = 500`) and its miner-employment
  measure (a 20-round ring buffer of how many miners actually mined, which is what stops it building
  miners for a mined-out map).
- **`archon.nim`** — an archon's turn: build what `econ.nim` asks for in the free adjacent square
  nearest the frontier (never boxing itself in), repair the weakest friendly droid in r² ≤ 20 by the
  first-place bot's own priority (sage, then soldier, then miner, and miners only when they are not
  mining), write the census and the archon-alive bitmap to the shared array, and run `relocate()`.
- **`miner.nim`** — mine and walk: `mineUntil()` implements `mine_floor` (and the losing-position
  override), the nine-square scan takes gold first (gold is scarcer than lead and enters the map only
  by reclaim), and `try_to_mine` is called **before and after** the move, exactly as
  `fury_fix_20/Miner.java` does, because a miner's action cooldown of 2 lets it mine, move and mine
  again in one turn.
- **`soldier.nim` + `micro.nim`** — the war. `micro.nim` is the port of `fury_fix_20/Micro.java`
  behaviour: attack the lowest-HP enemy inside r² ≤ 13 (tiebreak toward sages, then soldiers, then
  watchtowers in turret mode, then builders, then miners, then prototypes), prefer a target this
  attack will kill, hold the rubble-adjusted stand-off distance when the enemy group is bigger, and
  honour `retreat_hp`. Sage micro is separate and gated on the sage's 200-turn action cooldown: a sage
  advances only when `roundsSinceShot >= 0.6 × cooldown`, the first-place bot's own rule.
- **`builder.nim`** — prototypes and repairs: commission on `lab.nim schedule()` and
  `builder.nim towers()`, place, then **repair to full before doing anything else** (a prototype that
  is never finished is 180 Pb of nothing), then level-2-mutate with lead when `watchtower_policy` or
  the archon programme asks.
- **`lab.nim`** — `schedule()`, `site()`, `solitude()`: place the lab away from the crowd, transmute
  while the rate is at or under the `lab_solitude` price, and in TURRET mode transform to PORTABLE and
  walk when the crowd arrives.
- **`gold.nim`** — `sink()`, per `gold_use`: sages at the archon nearest the fight, or the level-3
  mutation with the best marginal value (a lab first at 25 Au, then a watchtower at 60, then an archon
  at 80).
- **`anomaly.nim`** — `plan()`, per `anomaly_play`: the five timed plays listed in the knob table,
  each computed from `getAnomalySchedule()` and the map's own symmetry, and each expressed as a
  request the other modules honour (a transform request, a scatter target, a push window, a spend-down
  order, a relocation).
- **`comms.nim`** — the 64-slot shared array layout, 16 bits a slot, ported from
  `jmerle/util/SharedArray` and `MPTempName/Comms.java` behaviour: slots **0–3** our archons (packed
  `x:6 y:6 alive:1 level:2`), **4–7** the enemy-archon guess and its confidence, **8–23** remembered
  live lead clusters (`x:6 y:6 bucket:4`), **24–27** gold sightings, **28–35** enemy sightings with a
  4-bit age, **36–39** the lab sites and their current rate, **40–47** rally points, **48–55** the
  anomaly programme (next type, round bucket, the requested play), **56–63** the per-type census.
  Writes are free in this year (no cooldown, no range test — §The game rule 3.2.10), so the only
  budget is `DecisionOps`, and every write is charged 1.

**`examplefuncsplayer22` — the weak floor and the parity oracle's other side.** Ported
**statement-for-statement** from
`battlecode22/example-bots/src/main/examplefuncsplayer/RobotPlayer.java`: an archon picks
`directions[rng.nextInt(8)]` and then, on `rng.nextBoolean()`, tries to build a MINER, else a
SOLDIER; a miner loops `dx, dy ∈ {−1,0,1}` in **that** order and, per square,
`while (canMineGold) mineGold; while (canMineLead) mineLead`, then moves in
`directions[rng.nextInt(8)]` if it can; a soldier senses
`senseNearbyRobots(actionRadiusSquared, opponent)`, attacks `enemies[0].location` if it can, then
moves in `directions[rng.nextInt(8)]`; a builder, sage, laboratory and watchtower do **nothing at
all** — which is why this bot never makes a gold, never puts up a building and always ends at round
2000 on `MORE_LEAD_NET_WORTH` (measured: **all eight** full-game mirrors ended exactly that way). It
seeds its own `java.util.Random(6147)` and never calls `Math.random()`, so — as in bc23, bc24 and
bc25 — **it needs no determinism patch and the oracle's Java side is upstream's file byte for byte
apart from its `package` line**. The eight `directions` are NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH,
SOUTHWEST, WEST, NORTHWEST **in that order**, because `rng.nextInt(8)` indexes it. **It may not gain
behaviour: it is one side of the differential oracle.** Its scripted reply is the all-defaults sheet
(it reads no knob).

Both replies go through the **same** `validate` the LLM path uses, which is what makes the
bounded-orders test meaningful and an LLM doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `wololo` chassis, `results.fallbacks[seat] = 1`, a **`doctrine_fallback` event** names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default (or clamps, for the five integers); the rest of the sheet applies |
| the sheet arrives inside an envelope | it is unwrapped once, the envelope key is recorded, and the knobs apply (the envelope pin above) |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| a side takes 2 games | the episode settles immediately — no padding (§The game, clinch semantics) |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `wololo` baseline reply, and it is exactly the
all-defaults sheet:

```json
{"sheet":{"opening":"miner_eco","miner_count_curve":"steady","mine_floor":1,
          "soldier_sage_ratio":65,"lab_round":300,"lab_solitude":12,
          "gold_use":"sages","watchtower_policy":"home",
          "anomaly_play":"time_pushes","archon_relocate":"safety",
          "retreat_hp":40},
 "notes":"default wololo doctrine","motto":"Leave one lead behind."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc22/constants.nim` | **new, generated** | every `GameConstants` value plus the whole `RobotType` table with its per-level `getMaxHealth`/`getDamage`/`getHealing`/`get*MutateCost`/`get*Dropped`/`get*Worth` values and the `AnomalyType` table, emitted by `tools/gen_year_constants.py --year bc22` from the pinned battlecode22 checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc22/world.nim` | **new** | world state: the rubble, lead and gold arrays, the robot table, the **exec-order list**, the **trove-order robot table** (D2), the two 64-slot shared arrays, team reserves, and every action of rule 3.2 |
| `src/battlecode/years/bc22/rules.nim` | **new** | the four-step round loop, the Singularity ladder, the points formula |
| `src/battlecode/years/bc22/units.nim` | **new** | the `RobotType` table, `RobotMode` and its three predicates, level/health/damage/healing/worth/drop by level, the single `addHealth` (cap, PROTOTYPE→TURRET promotion, destroy-at-zero, the `checkArchonDeath` flag), and the **rubble cooldown multiplier reproduced in float64** |
| `src/battlecode/years/bc22/economy.nim` | **new** | mining, the reclaim drop, the passive `+2`, the every-20-rounds `+5` regeneration over squares holding `> 0`, and the **laboratory transmutation rate** (the one transcendental — below) |
| `src/battlecode/years/bc22/anomaly.nim` | **new** | the schedule reader and the four anomaly bodies (global and sage), including CHARGE's combined-population stable sort, FURY's `checkArchonDeath = false` double-elimination check and VORTEX's three rubble permutations with the `Random(mapSeed)` draw |
| `src/battlecode/years/bc22/buildings.nim` | **new** | PROTOTYPE / TURRET / PORTABLE, `transform` (one counter, after the flip), `mutate` (the builder's cooldown, the level-up-and-heal, the building's 100+100) |
| `src/battlecode/years/bc22/trove.nim` | **new** | a faithful port of **trove4j 3.0.3**'s `TIntObjectHashMap` insert / remove / rehash and its **high-index-to-low** `values()` walk, used at exactly one site (D2). ~200 lines, one purpose, one test file |
| `src/battlecode/years/bc22/maps.nim` | **new** | the converted bc22 pool, the loader, the per-episode draw (`drawMaps`, `sideAslotFor`) |
| `src/battlecode/years/bc22/knobs.nim` | **new** | the eleven-knob `Doctrine22` type, defaults, per-field repair, **absent-key defaulting** (the envelope pin item 2), `toJson`, `plainWords` |
| `src/battlecode/years/bc22/chassis/*.nim` | **new** | `wololo.nim`, `scaffold22.nim`, `scenario22.nim`, `kit.nim`, `econ.nim`, `archon.nim`, `miner.nim`, `builder.nim`, `soldier.nim`, `micro.nim`, `lab.nim`, `gold.nim`, `anomaly.nim`, `comms.nim` |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc22", title: "Battlecode 2022 — Mutation", maxRounds: 2000, pools: @["small","mixed","large"], atlas: "atlas_bc22")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc22`; `Session` gains a `yBc22` branch (`w22`, `sides22`, `chassis22`); `yearIdOf`/`strongChassisFor`/`parseScriptedChassis`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson22`. `Bc22ActionNames = ["move","build_robot","attack","envision","repair","mine_lead","mine_gold","mutate","transmute","transform","write_array","disintegrate"]` is added beside the other years' name tables so the `first_action` event's **`action`** field has a documented vocabulary (the bc23 r1-F14/F25 lessons) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV10`, `ReplayCompatibleGameVersions` → `["GV04","GV05","GV06","GV07","GV08","GV09", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scWololo` and `scExamplefuncsplayer22` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc22` arm in `defaultBaselineFor` and `baselineFor`; `blWololo` and `blExamplefuncsplayer22` added to `Baseline`; `baselineChassis` and `baselineReply` map them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc22`, `doctrine22` on `Sheet`, a `knownKeysFor` arm, a `defaultSheet` field — the four-line shape bc21/bc23/bc24/bc25 added — **plus the year-neutral envelope unwrap and the new `Sheet.envelope` field** (§Decisions, the envelope pin) |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc22 adds the rubble heat layer, lead and gold pips per square, the seven unit sprites at two team palettes with a **mode/level badge** (prototype hatching, portable outline, level pips), health bars, and an anomaly flash overlay |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc22 scorebug / feed / endcard shell records **and the bc22 arms of `beatsFor`** (§Viewer, "the beat contract") |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port and `IdGenerator`. bc22 is the first year to need a **live** `Random(mapSeed)` at round time (the VORTEX draw), which the existing type already supports |
| `src/battlecode/fdlibm.nim` | **unchanged, reused** | `fdlibmExp` — the laboratory rate's `Math.exp` |
| `data/maps/bc22/*.json` | **new, committed** | 22 converted maps |
| `data/bc22/tables.json` | **new, committed** | the whole finite arithmetic domain (below) |
| `data/atlas_bc22.png` / `.json` | **new, committed** | the 2022 sprite atlas |
| `tools/convert_maps_bc22.py` | **new** | reads `.map22` and writes `data/maps/bc22/<name>.json` |
| `tools/map_pools_bc22.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc22.py` | **new** | cuts `atlas_bc22.*` from the 2022 client sprites |
| `tools/gen_year_constants.py` | **`--year bc22` added** | reads the 2022 `GameConstants.java` + `RobotType.java` + `AnomalyType.java` |
| `tools/JavaBc22Tables.java` | **new, CI-only** | regenerates `data/bc22/tables.json` under the CI **JDK 8** straight out of the released jar's own classes |
| `tools/oracle/bc22/Bc22Trace.java` | **new, CI-only** | the trace driver (§Tests) — one file, compiled against the released jar. **The driver written and executed in the sandbox for this note is the artefact to land.** |
| `tools/oracle/bc22/bc22scenario/RobotPlayer.java` | **new, CI-only** | the Tier A′ scenario bot that makes the rare paths bit-exact (§Tests) |
| `tools/oracle/bc22/examplefuncsplayer22/RobotPlayer.java` | **new, CI-only** | upstream's example bot, **byte for byte apart from its `package` line, no determinism patch** |
| `tools/oracle/bc22/build_oracle.sh` | **new, CI-only** | sha256- and size-verifies the jar, asserts the bundled `gnu.trove` / `net.sf.jsi` and the 75 `.map22` resources, and compiles the driver + both bots |
| `tools/oracle/bc22/jar.lock` | **new, CI-only** | the oracle jar's URL, size and sha256 |
| `tools/parity_trace_bc22.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc22.py` | **new** | the tier comparison and the ledger check — the bc23 script **with its three known bugs fixed** (below) |
| `tools/ci/parity_ledger_bc22.json` | **new** | the accepted-divergence ledger |
| `tools/gen_bc22_fixture_replay.nim` + `tests/fixtures/replay-bc22.json` | **new, committed** | the fixture replay the wasm smoke and the beat test load |
| `tests/bc22_fixture.nim` | **new** | the shared fixture builder, beside `bc23_fixture.nim`, `bc24_fixture.nim` and `bc25_fixture.nim` |
| `docs/RULES-BC22.md` | **new** | the year's rules, knobs and the full §Divergences list |

**A layout rule, written here because the bc24 run paid a fixer commit for its absence.** The file
list above is the intended layout and `NOTICE`, `knobs.nim`'s doc comments and `docs/RULES-BC22.md`
all point at it. If the builder merges two of these modules — for example folds `buildings.nim` into
`world.nim` — it must update **every one of those three pointers in the same commit**, and add a
`docs/RULES-BC22.md` §Divergences item recording the merge. A licence file that credits derived
behaviour to a path that does not exist is a defect, not a cosmetic slip.

### Determinism

- **`rng.nim` is reused unchanged, and bc22 needs MORE of it than any prior year.** Two independent
  `java.util.Random` streams are load-bearing:
  1. **`IDGenerator(map.getSeed())`** — the 48-bit LCG, `nextInt(bound)` with both the power-of-two
     shortcut and the rejection loop, 4096-id blocks from 10 000, Fisher–Yates per block — fixes the
     id of every robot ever built. The initial archons use the ids in the map file, which are
     **below** the 10 000 floor and are sorted ascending by `LiveMap`, which fixes the initial exec
     order (§The game, divergence 9).
  2. **`GameWorld.rand = new Random(map.getSeed())`**, which bc22 **actually reads**: `nextInt(3)` on
     a square rotational map and `nextInt(2)` on a non-square one, once per VORTEX. Both generators
     are constructed from the *same* seed, so they produce the same first values — and they are
     **separate objects with separate 48-bit states**, which the port must reproduce as two
     independent streams rather than one shared one. `tests/test_bc22_maps.nim` pins the first
     vortex permutation of every committed map with a vortex in its schedule against the oracle.
  3. `Math.random()` inside `setWinnerArbitrary` — divergence D3 below.
  The example bot's own `Random(6147)` stream is reproduced call for call by `scaffold22.nim`,
  including `nextInt(8)` and `nextBoolean()`.
- **Five determinism divergences and two fidelity requirements, each with its written argument.** All
  seven are in `docs/RULES-BC22.md` §Divergences:
  - **D1 — `ObjectInfo.eachRobot` is a trove hash-order sweep, and in 2022 it needs NO port at all.**
    It has exactly three call sites. `processBeginningOfRound` clears the indicator string, which this
    port does not have — a no-op. `processEndOfRound` calls `InternalRobot.processEndOfRound`, whose
    body in 2022 is the comment `// anything` and nothing else — **a genuine no-op**, verified by
    reading the file. `resign()` is the third and is unreachable from a JSON doctrine. So unlike
    bc23, where the argument had to be about commutativity, here there is no observable behaviour to
    order. Stated explicitly so nobody ports it "to be safe" and then has to justify it.
  - **D2 — `ObjectInfo.robotsArray()` IS load-bearing, at exactly one site, and it is ported rather
    than replaced. This is the single most important determinism decision in this note.**
    `robotsArray()` is trove's `values(V[])`, which walks the internal open-addressing table **from
    the highest index down to 0**, so its order is a function of the table's capacity, its insertion
    order and its tombstone history — deterministic, but not id order and not spawn order. It is read
    at three sites. `setWinnerIfMoreGoldValue` and `setWinnerIfMoreLeadValue` are sums, so they are
    order-free. `causeChargeGlobal` is **not**: it collects every DROID in that order, stable-sorts
    descending by friendly-robots-in-vision, and destroys the first `(int)(0.05f × n)` — so ties at
    the cut are broken by the trove order.
    **Measured in this sandbox with a purpose-built probe (`Bc22Charge.java`), over 600 rounds on
    three maps: a tie straddles the 5 % cut in 51 %, 55 % and 58 % of sampled rounds** (e.g.
    `maze` round 127, 20 droids, cut at `8 == 8`, head `[8,8,7,7,6,6,6,6,5,5,4,4]`). Since 30–40 % of
    the scheduled anomalies on the shipped maps are CHARGE, a wrong tie-break would diverge nearly
    every game at its first charge — which is exactly the "rare code path that fires mid-game" the
    Fleet-card postmortem warns about, except it is not rare. So `years/bc22/trove.nim` reproduces
    trove4j **3.0.3**'s `TIntObjectHashMap`: `HashFunctions.hash(key) & 0x7fffffff`, the
    `PrimeFinder` capacity ladder, the `% length` initial probe with a `1 + (hash % (length − 2))`
    step, `FREE`/`FULL`/`REMOVED` states, `rehash` on `size > loadFactor × capacity` or `free == 0`,
    and the descending-index `values()` walk. **This is a fidelity requirement, not a divergence.**
    The trace carries a per-round `H hashord=<fnv1a64 of the ids in robotsArray() order>` line so
    Tier A compares it **every round**, not only on charge rounds, and `tests/test_bc22_trove.nim`
    replays 500 random spawn/destroy sequences against a recorded oracle order.
  - **D3 — `setWinnerArbitrary`'s `Math.random()`** is replaced by a draw from a world RNG seeded from
    the map's `randomSeed`, reachable only when archons, gold net worth **and** lead net worth are all
    tied (at round 2000, or inside a fury double elimination).
  - **D4 — the VORTEX draw is reproduced, not replaced.** A fidelity requirement, above.
  - **D5 — `net.sf.jsi`'s `RTree` has no port.** `ObjectInfo` adds, moves and deletes robot ids in a
    spatial index and **never queries it**: every radius query in the engine goes through
    `GameWorld.getAllRobotsWithinRadiusSquared`, which enumerates squares. So the index cannot affect
    any outcome. Worth stating twice: the dead upstream `net.sf.jsi` artifact is what forced bc21's
    94-file shim, and here it is both **bundled in the jar** (so the oracle needs no shim) and
    **behaviourally dead** (so the port needs no index).
  - **D6 — `RobotControllerImpl.random` is a `static` field, reassigned in every controller
    constructor, and never read.** Not ported.
  - **D7 — bytecode metering** → a fixed `DecisionOps` budget (below).
- **The scan order is load-bearing and is ported literally**:
  `getAllLocationsWithinRadiusSquaredWithoutMap` is `ceiledRadius = ceil(sqrt(r²)) + 1` (**note the
  `+ 1`**), `minX = max(cx − cr, 0)`, …, `maxY = min(cy + cr, height − 1)`, then **x ascending outer,
  y ascending inner**, keeping squares with `dx² + dy² ≤ r²`. It fixes which enemy
  `senseNearbyRobots` returns first (which is the square the example bot's soldier attacks), the order
  ABYSS and FURY sweep the map (`getAllLocations()` is the same function with
  `Integer.MAX_VALUE`, so `ceiledRadius = 46342` and the bounds clamp to the whole map), and the
  order the sage anomalies apply. `ceil(√r²)` is over the finite set `{2, 5, 13, 20, 25, 34, 53}` and
  is **precomputed as a table**, so the port needs no `sqrt` on this path.
- **The arithmetic is integer everywhere except six places, and all six have a finite domain.**
  1. **The rubble cooldown multiplier**, `(int)((1 + rubble/10.0) * base)` — float64 divide, float64
     multiply, truncate. **It is NOT equal to the integer form**: measured on the JVM, 22 of the 808
     `(rubble, base)` pairs over the bases actually used disagree, always with the float one lower
     (§The game, divergence 2). Reproducing the float64 expression is mandatory and Tier B tables the
     entire lattice `rubble 0…100 × base ∈ {2, 10, 16, 20, 24, 25, 100, 200}`.
  2. **The prototype health** `(int)(0.8f × maxHealth)` — float32, tabled for all nine building
     health values: 600→480, 1080→864, 1944→1555, 150→120, 270→216, 486→388, 100→80, 180→144,
     324→259.
  3. **The reclaim drops** `(int)(worth × 0.2f)` — float32, tabled for every reachable
     `getLeadWorth`/`getGoldWorth` value (0, 20, 25, 40, 50, 60, 75, 80, 100, 150, 180, 300, 486, 600).
  4. **The anomaly truncations** — float32 in every case: ABYSS `(int)(0.1f × metal)` per square (and
     therefore **0 for any square holding ≤ 9**) and `(int)(−1 × 0.1f × reserve)` per team; ABYSS-sage
     `(int)(0.99f × metal)`; CHARGE global `(int)(0.05f × droidCount)` (**0 for every count ≤ 19**);
     CHARGE-sage `(int)(−1 × 0.22f × maxHealth)`; FURY `(int)(−1 × maxHealth × 0.05f)` and
     `× 0.1f`. Every one is tabled over its whole reachable domain.
  5. **The Singularity's net-worth sums** are integer, but the `points` formula's `share` is
     **float32** and the weighted sum is **truncated** (§The game, Scoring) — for
     recorder/re-deriver agreement between x86-64 and wasm32.
  6. **The one transcendental: the laboratory rate.** `(int)(20.0 − 18.0 × Math.exp(−k × n))` in
     `double`, with `k ∈ {0.02, 0.01, 0.005}` and `n` = friendly robots inside r² ≤ 53, i.e.
     `n ∈ 0 … 176` (one robot per square, minus itself, over the 177 squares at r² ≤ 53). `Math.exp`
     is not specified to be bit-exact across JVMs; `StrictMath.exp` is, and in practice HotSpot's
     `Math.exp` agrees with it on this domain — the bc21 argument, unchanged. The port therefore
     computes the rate with the existing **`fdlibm.nim` `fdlibmExp`**, generates the whole
     `3 × 177` table into `data/bc22/tables.json` at build time, **and reads the table at run time**,
     so the runtime path has no transcendental at all. Tier B byte-diffs that table against the
     values the **JVM itself** prints under Temurin 8. Measured level-1 spot values: n=0 → **2**,
     n=3 → 3, n=6 → 4, n=10 → 5, n=13 → 6, n=21 → 8, n=30 → 10, n=40 → 11.
- Every round appends to a **hash chain**; the viewer re-derives each round and compares, exposing
  `bc_mismatch_round`. The values folded into the bc22 chain each round: per team — archons alive,
  robots alive by each of the seven types, robots alive by each of the four modes, total robot HP,
  the sum of building levels, lead reserve, gold reserve, lead net worth, gold net worth; plus
  globally — the round number, an FNV-1a 64 hash of the rubble array (y ascending outer, x ascending
  inner — it changes on a VORTEX), an FNV-1a 64 hash of the lead array, an FNV-1a 64 hash of the gold
  array, an FNV-1a 64 hash of both shared arrays, the exec-order list length, **an FNV-1a 64 hash of
  the ids in `robotsArray()` (trove) order** (D2), and the index of the next unconsumed anomaly.
- Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
  (`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
  scar — and the record→re-derive test covers **every** bc22 end reason, not just `complete`.
- **`GameVersion` bumps to `GV10`** in the same commit, with a prepend-only changelog line ("bc22 year
  module added; bc26, bc20, bc21, bc23, bc24 and bc25 semantics unchanged; the doctrine-sheet
  envelope unwrap is year-neutral and changes no recorded byte's meaning").
  **`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06","GV07","GV08","GV09", GV10]`** — it
  is *extended*, never reset: nothing a GV04–GV09 recording carries changed meaning (and the envelope
  change cannot reach a recording, because `replay.nim` re-validates the **applied** sheet), so every
  hosted replay keeps rendering. `tools/ci/check_gameversion.sh` is kept and claims the version across
  branches; **it compares the headline, not the digits, so if a sibling branch lands GV10 first this
  branch rebases to GV11 and extends the list again** (the bc20 precedent).

### The chassis, and the bytecode divergence

The engine's per-robot **bytecode limits** (`ARCHON` 20 000, `MINER`/`SOLDIER`/`SAGE`/`WATCHTOWER`
10 000, `BUILDER` 7 500, `LABORATORY` 5 000) have no meaning outside the JVM instrumenter. They are
replaced by a **fixed per-robot `DecisionOps` budget of 2 000 (archon), 1 250 (miner, soldier, sage,
watchtower), 750 (builder) and 500 (laboratory)** — one tenth of the Java limits, the same convention
bc20, bc21, bc23, bc24 and bc25 use. One credit is charged for each: square sensed, robot examined in
a sense sweep, BFS node expanded, direction evaluated, shared-array slot read or written, lead or gold
candidate scored, and micro target scored. Credits are deducted inside `kit.nim` and **enforced by
the sim, not by the bot**. `EXCEPTION_BYTECODE_PENALTY` has no port: a Nim chassis raises nothing.
Also absent by design: the engine's own note that a cut-off robot's computation is **resumed at
exactly that point next turn** — this port ends the robot's turn where it stands instead
(below).

Two properties make this safe and both are stated so nobody has to rediscover them:

- **The budget is checked *before* each primitive and never inside one.** A navigation BFS, a vision
  sweep or a micro evaluation either runs to completion or does not start. So a primitive's *result*
  is never a function of the remaining budget, only *whether the chassis got to ask*. When the budget
  reaches zero the robot's turn ends where it stands — it is **not** resumed mid-computation next
  turn, which is the one place this differs from the JVM.
- **And in bc22 the divergence is provably not exercised by the oracle.** Measured in this sandbox
  over eight full 2000-round games (`maze`, `chalice`, `snowflake_redux`, `nottestsmall`, `rugged`,
  `squer`, `charge`, `island_hopping`, `equals`, `vortex`), the **peak bytecode use of any robot on
  any round was 680–760 — 6–7 % of the 10 000 limit, always a MINER — with no mid-turn cut-off at
  all**. So the Tier A bit-exact window for bc22 is the **whole game**, and the parity job asserts
  that rather than assuming it: if any robot ever exceeds **50 %** of its limit the job fails loudly,
  because past that point the comparison stops being defined (§Tests). This is the same shape bc23
  could promise and the opposite of bc21, whose windows were 22–245 rounds because its example bot
  *did* hit the ceiling.

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to Java
bytecode granularity needs either a Nim-level instrumenter (a compiler project) or a hand-annotation
of every statement against the jar's own `MethodCosts.txt`, and neither buys anything the budget does
not — the chassis are ours and are written to fit the budget.

### Maps

**22 of the 75 official maps** are converted and committed. **Every one of the 75 was parsed** with
the reader `tools/convert_maps_bc22.py` implements, and the table below is those measurements, not
assumptions (flatbuffers schema `GameMap`: `name`, `minCorner`, `maxCorner`, `symmetry`
`0 = rotation | 1 = horizontal | 2 = vertical` — the index order of `MapSymmetry.values()`, verified —
`bodies` (a `SpawnedBodyTable` of ids, team ids `1 = A / 2 = B` per `util/TeamMapping`, `BodyType`
ordinals and locations), `randomSeed`, `rubble[]`, `lead[]`, `anomalies[]` (an `AnomalyType` ordinal:
`0 = abyss, 1 = charge, 2 = fury, 3 = vortex`) and `anomalyRounds[]`). **Measured across all 75: every
initial body is an `ARCHON`, and both teams always have the same number of them** (31 maps with 2 a
side, 21 with 1, 15 with 3, 8 with 4). `rounds` is not in the file — `GameMapIO` hard-codes
`GAME_MAX_NUMBER_OF_ROUNDS`.

| pool | map | size | seed | symmetry | archons/side | rubble mean/max/min | lead squares | lead total | max square | anomalies ab/ch/fu/vo (n) | first | archon separation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `small` | `chalice` | 20x20 | 350 | vertical | **1** | 8.6 / 50 / 0 | 20 | 220 | 20 | 3/2/4/0 (9) | 200 | 17.0 |
| `small` | `maze` | 20x20 | 474 | horizontal | **3** | 34.7 / 60 / 0 | 12 | 240 | 20 | 2/3/3/1 (9) | 201 | 7.0 |
| `small` | `nottestsmall` | 20x20 | 396 | rotation | **1** | 36.4 / 98 / 0 | 24 | 960 | 64 | 0/6/0/5 (11) | 180 | 18.4 |
| `small` | `snowflake_redux` | 20x20 | 319 | rotation | **2** | 14.6 / 50 / 0 | 32 | 760 | 50 | 4/2/3/0 (9) | 200 | 19.0 |
| `small` | `rugged` | 21x21 | 850 | rotation | **1** | 27.1 / 100 / 2 | 26 | 550 | 40 | 0/0/0/0 (**0**) | — | 18.4 |
| `small` | `charge` | 25x30 | 51 | rotation | **1** | 13.9 / 60 / 0 | 16 | 460 | 60 | 2/6/1/1 (10) | 200 | 32.0 |
| `mixed` | `equals` | 30x30 | 681 | horizontal | **2** | 12.3 / 64 / 0 | 28 | 804 | 45 | 5/0/5/0 (10) | 201 | 19.0 |
| `mixed` | `monument` | 30x30 | 970 | vertical | **1** | 20.4 / 100 / 0 | 10 | 500 | 50 | **10**/0/0/0 (10) | 200 | 21.0 |
| `mixed` | `island_hopping` | 30x30 | 273 | rotation | **1** | 21.9 / 30 / 0 | 40 | 880 | 40 | 2/2/4/1 (9) | 200 | 26.9 |
| `mixed` | `progress` | 30x30 | 999 | horizontal | **2** | 9.2 / 50 / 0 | 32 | 1600 | 50 | 1/2/3/2 (8) | 200 | 21.0 |
| `mixed` | `collaboration` | 38x25 | 707 | rotation | **4** | 18.3 / 100 / 0 | 34 | 412 | **190** | 4/3/3/0 (10) | 189 | 25.0 |
| `mixed` | `standoff` | 40x25 | 884 | rotation | **3** | 10.0 / 80 / 0 | 40 | 220 | 10 | 1/5/1/2 (9) | 200 | 18.0 |
| `mixed` | `intersection` | 49x25 | 491 | horizontal | **2** | 21.2 / 100 / 0 | 40 | **2000** | 50 | 5/4/0/0 (9) | 200 | 20.0 |
| `mixed` | `pyramid_raiders` | 42x34 | 363 | vertical | **1** | **58.1** / 100 / 0 | 30 | **150** | 5 | 2/4/3/0 (9) | 200 | 33.0 |
| `mixed` | `defenseless` | 40x31 | 250 | horizontal | **2** | 16.3 / 80 / 0 | 41 | 205 | 5 | 0/6/2/**5** (13) | **5** | 20.0 |
| `mixed` | `fisherman` | 45x35 | 793 | horizontal | **3** | 13.9 / 90 / 0 | 36 | 180 | 5 | 0/6/3/0 (9) | 200 | 16.0 |
| `large` | `turtle` | 40x40 | 196 | **vertical** | **2** | 12.0 / 40 / 0 | 20 | 360 | 50 | 4/2/3/**1** (10) | 200 | 21.0 |
| `large` | `flowers` | 40x40 | 830 | rotation | **2** | **5.5** / 40 / 0 | 38 | 810 | 30 | 2/2/3/2 (9) | 169 | 7.1 |
| `large` | `despair` | 45x45 | 315 | rotation | **2** | 18.7 / 100 / 0 | 56 | 1284 | 42 | 3/3/3/1 (10) | 225 | 45.3 |
| `large` | `chessboard` | 47x47 | 445 | rotation | **2** | 23.8 / 90 / 0 | 60 | 1360 | 50 | 3/2/5/0 (10) | 200 | 42.0 |
| `large` | `colosseum` | 60x60 | 354 | **horizontal** | **3** | 25.0 / 99 / 0 | 124 | 3160 | 40 | 3/4/2/0 (9) | 201 | 11.0 |
| `large` | `vortex` | 60x60 | 26 | rotation | **4** | 24.2 / 100 / 0 | 140 | 3500 | 25 | 0/0/0/**12** (12) | 51 | 22.0 |

`mixed` (10 maps) is the `bc22` variant's pool; `small` (6) is the pool the parity oracle and the
docker smoke run on; `large` (6) is reserved for a later variant **and supplies two of the eight
parity pairs** (below). The `mixed` pool is chosen to span the axis the doctrines argue about:
**all three symmetries**; 900 to 1 575 squares; **archons per side 1, 2, 3 and 4**
(`collaboration` has four, which means four build actions a round and four repair posts, and
`monument`/`pyramid_raiders`/`island_hopping` have one, which means a single point of failure);
**lead totals from 150 (`pyramid_raiders`, and 30 squares of 5 apiece, so `mine_floor` decides whether
the map survives at all) to 2 000 (`intersection`, 40 squares averaging 50, so miners saturate and the
game is a soldier war)**; **rubble means from 9.2 (`progress`, everything is fast) to 58.1
(`pyramid_raiders`, where a soldier pays 16 × 6.8 ≈ 108 movement cooldown per step and the game is
almost static)**; and **anomaly schedules from all-ABYSS (`monument`, ten of them, so banking is
punished ten times) through charge-heavy (`standoff`, `fisherman`, `defenseless` — six charges each)
to vortex-heavy (`defenseless`, five, the first at round 5)**. One map would rank the map, not the
doctrine.

**The eight parity pairs** are the six `small` maps plus `turtle` and `vortex` from `large`, and they
are chosen to cover **all four arms of `causeVortexGlobal`**, which is the only RNG-reading rule in
the year: `nottestsmall` (20×20, rotational, **square** → `rand.nextInt(3)`, so rotate/flipH/flipV are
all reachable, and five vortexes to reach them), `charge` (25×30, rotational, **non-square** →
`rand.nextInt(2) + 1`, so only flipH/flipV), `maze` (horizontal → `flipRubbleHorizontally`, no draw),
`turtle` (**vertical** → `flipRubbleVertically`, no draw — the one arm no small map covers), `vortex`
(60×60 square rotational with **twelve** vortexes and nothing else, which is the arm's stress test),
and `chalice`/`snowflake_redux`/`rugged` for the abyss/charge/fury bodies and the anomaly-free
control. `rugged` has **no anomaly schedule at all** (measured: 0 entries, one of only three such
maps), which makes it the control that proves a divergence is a *rules* bug and not an anomaly bug.

Maps are excluded from v1 for stated reasons, all recorded in `docs/RULES-BC22.md`: everything above
1 600 squares is out of the played pool for wall-clock reasons (four are converted anyway, under
`large`); `maptestsmall` (rubble uniformly 1, 1 016 lead squares totalling **49 788** Pb — an
engine test fixture, not a game) and `squer` (zero anomalies **and** 8 lead squares totalling 204 on
625 squares — a starvation map) are converted for neither pool; and the remaining 53 are simply not
converted in v1 — the converter handles any `.map22` and `--parse-all` proves it against all 75 in CI.

`tools/convert_maps_bc22.py` writes `data/maps/bc22/<name>.json` carrying: `name`, `width`, `height`,
`random_seed`, `symmetry` (the map's own declared value, and in this year it is **used at runtime**, by
VORTEX), `rounds` (2000, the engine's hard-coded value), `rubble` (a `width × height` array of ints
0…100), `lead` (the same, sparse `[x, y, amount]` rows), `anomalies` (a list of `[round, type]` rows
in file order — the engine consumes them in order and asserts nothing about sortedness, and
**measured: every official schedule is already ascending in round**), and `initial_bodies`
(`[id, x, y, team, type]` rows **sorted ascending by id**, because that is the order `LiveMap`'s
constructor imposes and therefore the initial exec order). The converted maps are **committed** and CI
re-converts and byte-diffs. The wasm bundle gets the same directory through the existing
`--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from
the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot
takes side A in game 1; sides alternate each game. Seed, map names and side assignment are recorded in
results and in the replay. Map files live under `data/maps/bc22/`, so a name shared with another year
(`island_hopping` also exists as bc23's `IslandHopping`, `maze` as bc20's/bc21's `Maze`,
`flowers`/`turtle`/`leaf`) cannot resolve to the wrong file; `tests/test_bc22_maps.nim` asserts it
anyway.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `fdlibm`, `sheet_common`,
`sheet`, `decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never
branches on the year except through `years/dispatch.nim`, whose `Session` is a Nim object **variant**
so the compiler refuses to build a half-added year. Adding 2022 is exactly what bc20, bc21, bc23,
bc24 and bc25 proved adding a year to be: a new `years/bc22/` directory, a converted map set, a sprite
atlas, one registry line, one arm per dispatch `case`, and one manifest variant. **Nothing else on
`main` changes**: the six shipped years' modules, maps, atlases, tests and manifest variants are
untouched, and the shared files this branch edits are enumerated in §Packaging. The replay header
records `year` so a viewer can never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol id
would force every existing bc26/bc20/bc21/bc23/bc24/bc25 consumer to re-register for no change in the
contract. Both `game.protocols.player` and `game.protocols.global` continue to point at
`docs/PROTOCOL.md`, which gains a bc22 section.

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
env var takes the active year's default baseline (`wololo` on bc22). A seat whose registration never
arrives is logged loudly and reported to `COGAME_PLAYER_FAILURE_URI`. The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket (the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no
per-round observation of any kind. The example below is the real `intersection` card, measured.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV10","year":"bc22",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":871345,
 "games":[{"map":"intersection","width":49,"height":25,"symmetry":"horizontal",
           "you_are":"A","rounds":2000,
           "your_archons":[{"x":2,"y":2,"rubble":0},{"x":46,"y":22,"rubble":0}],
           "enemy_archons":[{"x":2,"y":22},{"x":46,"y":2}],
           "start_separation":20.0,
           "terrain":{"rubble_mean":21.2,"rubble_median":0,"rubble_max":100,
                      "squares_over_50_rubble_pct":19.8},
           "lead":{"squares":40,"total":2000,"max_square":50,
                   "nearest_to_you":{"x":5,"y":4,"amount":50,"steps":3},
                   "within_vision_of_your_archons":4},
           "gold":{"squares":0,"total":0,
                   "note":"gold is never on the map at round 0: it comes only from a laboratory or from the 20% reclaim a dying robot drops"},
           "anomaly_schedule":[{"round":200,"type":"abyss"},{"round":400,"type":"charge"},
                               {"round":600,"type":"abyss"},{"round":800,"type":"charge"},
                               {"round":1000,"type":"abyss"},{"round":1200,"type":"charge"},
                               {"round":1400,"type":"abyss"},{"round":1600,"type":"charge"},
                               {"round":1800,"type":"abyss"}],
           "singularity_round":2000}],
 "economy":{"start_per_team":{"lead":200,"gold":0},
            "passive_per_team_per_round":{"lead":2},
            "map_regeneration":{"every_rounds":20,"amount":5,
                                "rule":"added ONLY to a square that still holds at least 1 lead — a square mined to zero is dead for the rest of the game"},
            "mine_rate":"one unit per action; a miner's action cooldown is 2 against a limit of 10, so up to FIVE mines a turn on rubble-free ground",
            "reclaim":"a destroyed robot drops 20% of its build cost (including mutations) on the square it last occupied; an archon drops 20 gold, 36 at level 3",
            "laboratory":{"lead_per_gold":"floor(20 - 18*exp(-k*n)) where n is the friendly robots the lab can see (vision r2<=53) and k is 0.02 / 0.01 / 0.005 by level",
                          "measured_level1":{"0":2,"3":3,"6":4,"10":5,"13":6,"21":8,"30":10,"40":11}}},
 "units":{"archon":{"au":"cannot be built (nominal 100)","hp":"600/1080/1944 by level",
                    "act_cd":10,"move_cd":24,"act_r2":20,"vis_r2":34,
                    "does":"builds MINER, BUILDER, SOLDIER and SAGE in an adjacent square; repairs a friendly non-building for 2/4/6 a turn within r2<=20; LOSE YOUR LAST ARCHON AND YOU LOSE THE GAME IMMEDIATELY"},
          "laboratory":{"pb":180,"hp":"100/180/324","act_cd":10,"move_cd":24,"vis_r2":53,
                        "does":"turns lead into exactly 1 gold per action at the loneliness price above; the ONLY source of gold; built by a BUILDER as an 80-HP prototype that needs 10 builder repairs to come alive"},
          "watchtower":{"pb":150,"hp":"150/270/486","dmg":"4/8/12","act_cd":10,"act_r2":20,"vis_r2":34,
                        "does":"a building that shoots; built by a BUILDER as a 120-HP prototype that needs 15 builder repairs to come alive"},
          "miner":{"pb":50,"hp":40,"act_cd":2,"move_cd":20,"act_r2":2,"vis_r2":20,
                   "does":"mines one lead or one gold per action from its own square or any of the eight around it"},
          "builder":{"pb":40,"hp":30,"act_cd":10,"move_cd":20,"act_r2":5,"vis_r2":20,
                     "does":"builds LABORATORY and WATCHTOWER, repairs a friendly building 2 a turn, and MUTATES a friendly building a level"},
          "soldier":{"pb":75,"hp":50,"dmg":3,"act_cd":10,"move_cd":16,"act_r2":13,"vis_r2":20,
                     "does":"the general-purpose attacker, and the whole 2022 metagame; 3 damage a hit, so an archon takes 200 hits"},
          "sage":{"au":20,"hp":100,"dmg":45,"act_cd":200,"move_cd":25,"act_r2":25,"vis_r2":34,
                  "does":"45 damage — fifteen soldiers' worth — once every twenty turns; and the ONLY unit that can ENVISION an anomaly"}},
 "buildings":{"modes":"a building is built as a PROTOTYPE at 80% health that can neither act nor move; a BUILDER repairing it to full turns it into a TURRET (acts, cannot move); TRANSFORM flips TURRET<->PORTABLE (moves, cannot act) and costs 100 cooldown on the mode-appropriate counter, i.e. ten of its own turns",
              "mutations":"level 2 costs LEAD (archon 300, watchtower 150, laboratory 150); level 3 costs GOLD (archon 80, watchtower 60, laboratory 25); a mutation is applied by a BUILDER within r2<=5 and freezes the building for 100 on BOTH counters",
              "archons_walk":"an archon is a building: it can transform to PORTABLE and relocate"},
 "rubble":{"range":"0..100 per square, fixed except by a VORTEX",
           "effect":"every cooldown a robot pays is floor((1 + rubble/10) * base), evaluated at the square the robot is standing on when the action resolves — and for a MOVE that is the DESTINATION square"},
 "anomalies":{"schedule":"public to every robot at all times, per map, roughly one per 200 rounds",
              "abyss":"10% of the lead and gold on EVERY square and in BOTH team reserves, rounded DOWN — so a square holding 9 or fewer loses nothing",
              "charge":"the top 5% of ALL droids on the board, ranked by how many friendly robots each can see, are destroyed; the ranking is over BOTH teams together, so the side that clumps donates the victims; and floor(0.05*n) is ZERO for any droid count of 19 or fewer",
              "fury":"every building IN TURRET MODE loses 5% of its max health, rounded down (a level-1 watchtower loses 7); a building in PORTABLE mode and a PROTOTYPE take NOTHING",
              "vortex":"the rubble map is reflected or rotated according to the map's declared symmetry; lead, gold and robots do not move",
              "sage_versions":{"abyss":"99% of the metal on every square within r2<=25",
                               "charge":"every enemy droid within r2<=25 loses 22% of its max health",
                               "fury":"every turret-mode building within r2<=25 loses 10% of its max health",
                               "vortex":"NOT available to a sage"}},
 "comms":{"shared_array":64,"max_value":65535,
          "write_rule":"any robot, any time, no cooldown, no range test, no cost","read_rule":"always"},
 "win":{"instant":"destroy the enemy's LAST ARCHON",
        "at_round_2000":["more archons alive","greater gold net worth (reserve + live robots' gold worth)","greater lead net worth","coin flip"],
        "note":"there is no elimination for losing droids: a faction with one archon and nothing else plays on to round 2000 earning 2 lead a round"},
 "rules_digest":"<~7 KB condensed spec: the seven unit types and their exact actions and per-level tables, the four building modes and both mutation ladders, the rubble multiplier and where it is read, the lead economy and the regeneration rule, the reclaim table, the laboratory curve, the four anomalies with their exact truncated arithmetic and the sage versions, the free shared array, and the Singularity ladder>",
 "sheet_schema":{"…all eleven knobs, their values, ranges and defaults…"},
 "scoring":{"weights":{"archons_share":64,"gold_net_worth_share":24,"lead_net_worth_share":12},
            "win_bonus_per_game":200,"games":3,
            "note":"shares are float32; points truncate to an integer; the league ranks by ELO on match wins and results.scores is dominated by the win bonus"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with **both** factions' archon
positions (they are public: the maps are symmetric and the engine's own map file puts them there), the
rubble profile, the lead and gold inventories with the walking distance to the nearest deposit, **the
complete anomaly schedule** (which is public to every robot in the real game — `getAnomalySchedule()`
is free), the seed, the full constant tables, the knob surface with defaults, the scoring weights and
the deadlines. Because every map is symmetric, the two seats' cards are mirror images and numerically
identical in every aggregate; the only asymmetry is `you_are` and which mirrored coordinate set is
labelled "yours".
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in
either direction, at any time); the opponent's real player name (only the alias); every in-match state
(a cog receives **no** per-round observation — one sealed doctrine, then the war); the other seat's
fallback status. Inside a match the fog is the robots': vision r² ≤ 20 for miners, builders and
soldiers, r² ≤ 34 for archons, watchtowers and sages, r² ≤ 53 for laboratories, and **nothing else
occludes** — 2022 has no clouds and no terrain vision rule. The enemy's shared array is never
readable. Everything else inside the radius is exact.

### Reply schema and caps

```json
{"sheet":{"opening":"sage_spam","miner_count_curve":"steady","mine_floor":2,
          "soldier_sage_ratio":25,"lab_round":140,"lab_solitude":6,
          "gold_use":"mutations","watchtower_policy":"forward",
          "anomaly_play":"time_pushes","archon_relocate":"safety",
          "retreat_hp":55},
 "notes":"Lab goes six squares north-east of my west archon where nothing walks; the first 60 gold is a level-3 lab and then archon mutations. I stand my archons up for the round-400 charge and push straight after it.",
 "motto":"Two lead a gold."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES**, cut on a rune boundary | unparseable → retry once → fallback sheet |
| the envelope | unwrapped **at most once** (`sheet`, `doctrine`, or a single object-valued key), the resolved key recorded in `seats[].sheet_envelope` | no envelope found → the payload itself is the sheet |
| `sheet` | ≤ **32** keys, each value type- and range-checked | bad field → that field's default, recorded |
| `mine_floor` (0…5), `soldier_sage_ratio` (0…100), `lab_solitude` (0…40), `retreat_hp` (0…100) | integers, clamped to their stated ranges | out of range → clamped to the nearer bound and recorded (an integer knob is clamped, never defaulted, so "as much as possible" still means something) |
| `lab_round` | integer **1 … 1800** | out of range → clamped; a non-integer → the default 300, recorded |
| every enum knob (`opening`, `miner_count_curve`, `gold_use`, `watchtower_policy`, `anomaly_play`, `archon_relocate`) | exactly one of its listed strings, case-folded and trimmed, `-`/space → `_` | unknown value → that field's default, recorded |
| an **absent** known key | takes its default and **is recorded in `sheet_defaults_applied`** (the envelope pin, item 2 — bc22 only) | — |
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

The closed schema is **shared with the six shipped years** and stays that way: `results.games[]`'s
five required keys are year-neutral (`map`, `side`, `rounds_played`, `winner`, `end_reason`), every
year-specific statistic is an optional property, and `end_reason`'s enum is the union of every year's
values.

bc22's per-game keys, each a 2-array of integers in **seat** order unless marked scalar (the ones
already declared for another year — `units_built`, `damage_dealt`, `robots_alive`, `robots_lost` — are
reused rather than duplicated): `archons_start`, `archons_end`, `archons_lost`,
`archon_relocations`, `lead_mined`, `gold_mined`, `lead_end`, `gold_end`, `lead_net_worth_end`,
`gold_net_worth_end`, `lead_reclaimed`, `gold_reclaimed`, `squares_mined_dry`,
`miners_built`, `builders_built`, `soldiers_built`, `sages_built`, `labs_built`, `labs_finished`,
`watchtowers_built`, `watchtowers_finished`, `mutations_l2`, `mutations_l3`, `transmutes`,
`gold_transmuted`, `lead_spent_transmuting`, `repairs`, `hp_repaired`, `envisions`,
`sage_damage`, `soldier_damage`, `watchtower_damage`, `array_writes`, `transforms`,
`rounds_with_a_lab`, `anomaly_losses_charge`, `anomaly_losses_fury_hp`, `anomaly_losses_abyss_lead`,
`anomalies_dodged`; scalars `archons_per_side`, `lead_on_map_start`, `lead_squares_start`,
`rubble_mean`, `anomalies_scheduled`, `vortexes_scheduled`, `singularity_round`.

Top level, unchanged: `names`, `aliases`, `scores`, `wins`, `points`, `games`, `seed`, `year`,
`policy_kind`, `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`,
`wall_clock_seconds`, `game_version` — plus one **new, optional, year-neutral** top-level key,
`sheet_envelope` (a 2-array of strings), so the envelope pin's finding is machine-visible in the
results document as well as on the doctrine card.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV10","year":"bc22",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"wololo",
           "sheet":{…as applied…},"sheet_submitted":"{…as received, before unwrapping…}",
           "sheet_envelope":"doctrine",
           "sheet_defaults_applied":["lab_solitude"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":8123,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"intersection","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":2000,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…all three drawn maps, even if the match clinched in two…],
         "side_a_slots":[…],"abandon_after":[…],"max_rounds":2000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI — `result`, SINGULAR, this repo's convention */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships), both doctrine sheets **and both
submitted sheets with the envelope key that was unwrapped**, the chassis each seat drove, and the
event list are all in the file, and the wasm sim replays every round from them. **No `.bc22` bytes,
no per-round robot dump, no per-square dump** — robot positions, health, modes, levels, cooldowns, the
rubble/lead/gold arrays, the reserves, the shared arrays and the anomaly cursor are pure functions of
the sim, so the browser re-derives them and the endcard reads the re-derived totals. No server is
contacted except S3 for the `.replay` file. The per-round hash chain lets the viewer prove its
re-derivation matches the recording (`bc_mismatch_round`, surfaced as `data-replay-mismatch-round`
and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`. **Every event kind here is
bounded per game** — a 2000-round match with 135 robots on the board cannot be allowed to emit an
event per action — and every one has a beat kind with CSS (§Viewer). **No event has a field named
`kind`**: the `first_action` event's field is `action`, because a field named `kind` is flattened into
the same object as the event's own `kind` key and silently overwrites it (the bc23 r1-F25 finding).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `envelope`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides`, `archons`, `lead_on_map`, `anomalies` | 1/game | `game` | beat + feed |
| `first_action` | `game`, `round`, `alias`, **`action`** (from `Bc22ActionNames`) | 4/game | `build` | beat + feed |
| `lab_built` | `game`, `round`, `alias`, `x`, `y`, `finished` (bool), `rate` | ≤ 12/game | `lab` | beat + feed |
| `first_sage` | `game`, `round`, `alias`, `gold_spent_total` | 2/game | `sage` | beat + feed |
| `watchtower_built` | `game`, `round`, `alias`, `x`, `y`, `finished` (bool) | ≤ 16/game | `tower` | beat + feed |
| `mutation` | `game`, `round`, `alias`, `target` (`archon`\|`laboratory`\|`watchtower`), `level`, `cost_lead`, `cost_gold` | ≤ 24/game | `mutate` | beat + feed |
| `gold_milestone` | `game`, `round`, `alias`, `gold_total`, `rate` — the first gold and then every 20th | ≤ 20/game | `gold` | beat + feed |
| `anomaly_struck` | `game`, `round`, `type`, `droids_lost` (2-array), `turret_hp_lost` (2-array), `lead_lost` (2-array), `rubble_changed` (bool) — **one per scheduled anomaly**, and the measured maximum schedule length is 13 | ≤ 14/game | `anomaly` | beat + feed |
| `anomaly_dodged` | `game`, `round`, `alias`, `type`, `how` (`portable_before_fury`\|`spread_before_charge`\|`spent_before_abyss`\|`relocated_before_vortex`), `saved` | ≤ 20/game | `dodge` | beat + feed |
| `archon_lost` | `game`, `round`, `alias`, `archons_left`, `gold_dropped` | ≤ 8/game | `archon` | beat + feed |
| `archon_relocated` | `game`, `round`, `alias`, `from_x`, `from_y`, `to_x`, `to_y`, `rubble_before`, `rubble_after` | ≤ 16/game | `archon` | beat + feed |
| `rout` | `game`, `round`, `alias`, `lost` — a round in which one faction lost ≥ 5 robots | ≤ 20/game | `rout` | beat + feed |
| `duel` | `game`, `round`, `lost` (2-array) — a round in which **both** factions lost at least one attacker | ≤ 20/game | `duel` | beat + feed |
| `singularity` | `game`, `round`, `rung` (`more_archons`\|`more_gold_net_worth`\|`more_lead_net_worth`\|`coin_flip`), `archons` (2-array), `gold` (2-array), `lead` (2-array) | ≤ 1/game | `end` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points`, `archons` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

Fourteen beat kinds (`doctrine`, `game`, `build`, `lab`, `sage`, `tower`, `mutate`, `gold`, `anomaly`,
`dodge`, `archon`, `rout`, `duel`, `end`), and **all fourteen are emitted by the committed fixture
replay** so the beat test in §Viewer is a real gate and not a CSS inventory. The whole event list for
a three-game match is at most a few hundred entries, and `tests/test_bc22_replay.nim` asserts each
per-kind bound so a pathological game cannot produce a 20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc22/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.bc22` bytes, no 2022 TypeScript
client.

### All four viewer files come from ONE starter: `cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode` →
here. All four bundle files come from **that one starter** — never a mixture, because splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23).

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc22/`, `data/bc22/tables.json` and `data/atlas_bc22.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are, including `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-d:useMalloc` and `ENVIRONMENT=web,worker,node`. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. No edit at all is needed for bc22: the page already sets `document.documentElement.dataset.year` from the frame's `s.year` in the **shared** block, so a new year switches itself on. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc22 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and no existing id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and byte-for-byte: **`client/chrome_common.js`** and **`client/broadcast_core.js`**
(their sha256 is asserted against the coworld-ctf copies in `tests/test_viewer.nim`, and that
assertion stays green because neither file is touched). `wire_constants.js` is regenerated from the
sim by `tools/gen_wire_constants.nim`, as today.

**Load signalling** (unchanged from the starter, restated because it is a checklist item):
`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on the
**first drawn frame** (the worker's `loaded` message after the first board frame is composited — never
on rAF timing at the call site, the chorus 2026-08-24 scar), and the `coworld-replay` bridge posts
`ready` from a callback fired **after** that attribute is set. On any failure — fetch, JSON parse, an
unknown `game_version`, a wasm abort, or a hash mismatch that prevents rendering — it sets
**`data-replay-error="<message>"`** on `<html>` and shows the failure card.

### The appended bc22 game block

**No starter element is removed.** The bc26 block's elements (`#coopchip`, `#bars`, `#gamechips`,
`#econ`, `#doctrines`), the bc20 block's (`#bc20-flood`, `#bc20-soup`, `#bc20-units`,
`#bc20-doctrines`, `#bc20-chain`), the bc21 block's (`#bc21-votes`, `#bc21-influence`, `#bc21-units`,
`#bc21-doctrines`, `#bc21-bids`), the bc23 block's (`#bc23-islands`, `#bc23-econ`, `#bc23-units`,
`#bc23-doctrines`, `#bc23-tempest`), the bc24 block's (`#bc24-flags`, `#bc24-crumbs`, `#bc24-levels`,
`#bc24-doctrines`, `#bc24-traps`) and the bc25 block's (`#bc25-coverage`, `#bc25-towers`,
`#bc25-econ`, `#bc25-doctrines`, `#bc25-srp`) all stay exactly where they are; the bc22 block adds
its own, with ids that are all new and all prefixed:

- `#bc22-archons` — **the headline readout, and the year's whole story**, in the same top-centre pill
  slot bc20 uses for its flood gauge and bc23 for its island tally: a two-sided archon tally
  `ASH ▲▲▲ 3 — 3 ▲▲▲ BASIL` with a health pip per archon that drains as it is shot, a level dot
  (1/2/3), and a **portable** outline on any archon currently walking. It flashes red when an archon
  dies, because that is the only event that can end the game.
- `#bc22-anomaly` — **the year's signature readout, and the one no other year has**: the anomaly
  clock. The next scheduled anomaly, its type, and how many rounds away
  (`FURY in 37`), the whole remaining schedule as a mini-timeline under the transport-band clock, and
  the Singularity countdown (`SINGULARITY round 2000 — 588 to go`). When an anomaly fires it takes
  over the strip for two seconds with what it did in plain words
  (`CHARGE — 6 droids gone: 4 Ash, 2 Basil`), which is the single most watchable thing in this year.
- `#bc22-econ` — per faction: lead and gold banked, lead income over the last 20 rounds, **lead still
  on the map and how many squares have been mined dry** (the `mine_floor` story, made visible),
  laboratories standing and each one's **current transmute rate** (`lab 2 Pb/Au`), and gold spent.
- `#bc22-units` — per faction: the seven-type census with soldiers emphasised (this is the year of the
  soldier), prototypes shown separately from finished buildings, and robots lost.
- `#bc22-doctrines` — both sheets in plain words, **dismissible** (D3): a `#bc22-doctrines-close`
  button with `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first
  playback advance (or after six seconds for a viewer who never presses play), and a
  `#bc22-doctrines-toggle` chip in the scorebug that re-opens it. Its body is capped and scrolls. It
  sits above the board area and **never** inside the transport band. It carries the
  **submitted-vs-applied badge** the envelope pin requires (§Decisions): when
  `sheet_envelope != ""` or `sheet_defaults_applied` is non-empty it shows
  `envelope: doctrine · 11 of 11 knobs defaulted` and a disclosure with the first 120 runes of
  `sheet_submitted`.
- `#bc22-mutation` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: the shared `onText` block already sets
`document.documentElement.dataset.year` from the replay header and re-runs `relayout()` on a change;
the stylesheet extends the existing `html:not([data-year="bc23"]) #bc23-… { display: none !important }`
pattern with the bc22 pair. **Every bc22 rule — including every beat-marker colour — is scoped to
`html[data-year="bc22"]`** (the bc21 r1-F4 fix, kept), so none of them can restyle another year's
marker of the same name. The frame hook is `window.Bc22Block.active(s)` / `.onFrame(s)`, added beside
the existing five in the shared `onText`, and the
`if (!isBc20 && !isBc21 && !isBc23 && !isBc24 && !isBc25)` guard becomes
`if (!isBc20 && !isBc21 && !isBc22 && !isBc23 && !isBc24 && !isBc25)`.

### The beat contract — emission, label and style, all three tested

This is where the bc25 run failed review (r1-F26: eleven beat-kind CSS rules against two emitted
kinds), so it is specified as three obligations that one test asserts together against the
**committed fixture replay** (`tests/fixtures/replay-bc22.json`):

1. **Emission.** `beatsFor` in `src/battlecode/broadcast.nim:134` is the only place a beat kind is
   decided. bc22 adds an arm for each of its event kinds. Three names collide with other years —
   `first_action` and `rout` (bc23 and bc25 spell both) and `duel` (bc23's) — so the existing pair of
   discriminators gains `let isBc22 = doc.year == "bc22"`, `first_action` maps to `build` for
   **bc22, bc23 and bc25** and to `""` for bc24, `rout` maps to `rout` for **bc22, bc23 and bc25**,
   and `duel`'s **label** switch gains a year test because bc22's `duel` carries the same field name
   with a different meaning (attackers lost, not launchers). The bc22-only kinds (`lab_built`,
   `first_sage`, `watchtower_built`, `mutation`, `gold_milestone`, `anomaly_struck`,
   `anomaly_dodged`, `archon_lost`, `archon_relocated`, `singularity`) need no discriminator, because
   no other year emits those event names — even though two of their beat kinds (`tower`, `end`) are
   spelled the same as another year's, which is exactly why the CSS scoping is mandatory.
2. **Label.** Every emitted beat carries a spectator-readable label built in the same `case` — e.g.
   `"Clan Ash finishes a laboratory at 12,7 — 3 lead per gold, game 2, round 318"`,
   `"CHARGE — 6 droids gone: 4 Ash, 2 Basil, game 1, round 400"`,
   `"Clan Basil stands its archons up and takes nothing from the FURY — game 3, round 604"`,
   `"ARCHON DOWN — Clan Ash has 2 left, and 20 gold is on the ground at 41,19"`,
   `"SINGULARITY — round 2000, archons level at 2, Clan Basil wins on gold net worth 148 to 96"` —
   and it becomes the `<button>`'s `aria-label` and `title`.
3. **Style.** `client/replay_broadcast.html` ships a `.beat-marker.<kind>` rule for **all fourteen**
   kinds, every one scoped to `html[data-year="bc22"]`: `.doctrine`, `.game`, `.build`, `.lab`,
   `.sage`, `.tower`, `.mutate`, `.gold`, `.anomaly`, `.dodge`, `.archon`, `.rout`, `.duel`, `.end`.
   Seven of those names already exist for other years (`doctrine`, `game`, `build`, `tower`, `rout`,
   `duel`, `end`), which is exactly why the scoping is mandatory; seven are new
   (`lab`, `sage`, `mutate`, `gold`, `anomaly`, `dodge`, `archon`).

`tests/test_bc22_beats.nim` loads the committed fixture, calls `beatsFor`, and asserts: **at least 28
beats over at least 10 distinct kinds**, every beat's label non-empty and ≤ 120 runes, every emitted
kind present in the fourteen-kind vocabulary, and — reading the page source — a
`html[data-year="bc22"] .beat-marker.<kind>` rule for **every kind the fixture actually emitted**
(not for every kind in a hand-written list). `tools/gen_bc22_fixture_replay.nim` is written to produce
all fourteen kinds, and the test fails if the fixture stops doing so.

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The `--statrail` repair is already in the tree: `relayout()` measures the union of the *visible* year
stat boxes into `--statrail` (`client/replay_broadcast.html:5525–5541`), `#killfeed`'s `bottom` is
`max(calc(76 * var(--u)), calc(var(--band, 0px) + var(--statrail, 0px) + 8px))` (line 1270),
`tests/test_viewer.nim` asserts both statically, and `viewer_smoke.mjs --killfeed-overlap` measures
client rects at 360 / 720 / 1280 px at FIT and 2× zoom on every year's replay.

**What bc22 must do — and it is the whole of the work here:**

1. add `bc22-econ` and `bc22-units` to `relayout()`'s measured id list, beside `econ`, `bc20-soup`,
   `bc20-units`, `bc21-influence`, `bc21-units`, `bc24-crumbs`, `bc24-levels`, `bc25-towers`,
   `bc25-econ`, `bc23-econ` and `bc23-units`. (`#bc22-archons` and `#bc22-anomaly` are **top**-band
   pills and are deliberately not in the rail set.)
2. run the existing `--killfeed-overlap` gate **on the bc22 replay too**, at all three widths and both
   zooms — seven replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and
   asserts the gate goes red, so a seventh year cannot quietly disarm it (the 2026-09-04 learning
   about `page.evaluate` IIFEs and gates that look armed and test nothing).

### Zoom: KEEP `#viewpanel`

The bc22 variant's pool spans 30×30 to 49×25 and 45×35, and the reserved `large` pool reaches 60×60.
The native board render is 16 px per square, so 400–960 px wide — **larger than the 360 px
featured-match frame**, where a 49-wide board would give 7.3 px per square. So the inherited
`#viewpanel` (zoom bar + minimap, with `?viewpanel=0` still honoured for thumbnail capture) is
**kept**, wired to the same `zoomAt/setZoom/panBy/panTo/resetView` core API the worker already
forwards. The default view is fit-to-board, so a spectator who touches nothing sees the whole map,
both factions' archons and every lead deposit at once — which in this year is the right default,
because the story is *where the lead is and who is standing on it*.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets
  **`--hudscale`**, **`--topband`**, **`--band`** and **`--statrail`** on `:root`, iterating to a fixed
  point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport). `#bc22-archons`, `#bc22-anomaly`, `#bc22-econ`,
  `#bc22-units`, `#bc22-doctrines` and `#bc22-mutation` are all explicitly positioned above
  `var(--band)`. The anomaly mini-timeline sits **immediately above** `var(--band)`, never inside it.
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`, built by
  a bc22-block function with its **own** name, `buildBc22BeatButtons` — never `markBeat` (the tandem
  2026-08-23 hoisting collision) and never colliding with `buildBeatButtons` (bc26),
  `buildBc20BeatButtons`, `buildBc21BeatButtons`, `buildBc23BeatButtons`, `buildBc24BeatButtons` or
  `buildBc25BeatButtons`. The spoiler gate is honoured by `applyBc22BeatSpoilers`, the same shape as
  the other five blocks.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
  `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`,
  `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — check 8 must be dispatched with `settle=20000 soak=15`

bc21 taught this: a compute-heavy year defeats a fixed-wait scrub probe, because the Worker
re-simulates from the last keyframe on every seek and a 700 ms settle expires first (loaded:true,
viewer healthy, instrument too impatient). bc22 is squarely in that class: the measured Java mirror
carries **85–135 robots on the board on average** with peaks of **108–204** on the pool's map sizes
(349 on 60×60), i.e. between bc25's 26–29 and bc23's 121–157, and the per-round cost estimated in
§The game is 3–7 ms. So, decided here rather than discovered at phase 60: **the phase-60 check-8
dispatch for bc22 uses `settle=20000 soak=15`**, and `ci.yml`'s `wasm-viewer` job runs
`viewer_smoke.mjs` with `--timeout 120 --soak 15` on the bc22 replay (bc23, bc24 and bc25 keep the
same; bc26/bc20/bc21 keep `--timeout 90 --soak 10`). The docker-smoke step prints
`sim_seconds / rounds`, and `docs/RULES-BC22.md` records the measured value so the next year module
can size its own probe from a number instead of a guess.

**The scrub selector needs no change.** `tools/ci/viewer_smoke.mjs` in this repo already resolves
`#scrub` before `#seek` before `input[type="range"]`, **one selector at a time** and excluding
`#zoom-slider`, and `ci.yml` asserts `scrub_selector == "#scrub"` after every run.

### Art

`data/atlas_bc22.png` + `data/atlas_bc22.json` (≈ 120 KB, committed), cut by
`tools/build_sprite_atlas_bc22.py` from the official 2022 client's sprite tree
(`client/visualizer/src/static/img/` at the pinned commit `6ed05b67`). **Measured: the upstream set is
177 PNGs, of which `robots/` holds 56** and every one that matters here is used:
`robots/{blue,red}_{miner,builder,soldier,sage}.png` (the four droids),
`robots/{blue,red}_{archon,lab,watchtower}{,_level1,_level2,_level3}.png` (the three buildings at
three levels), `robots/{blue,red}_{archon,lab,watchtower}_prototype.png` (the prototype state — which
this year needs, because a prototype is a real and distinct game state), and
`robots/{blue,red}_{archon,lab,watchtower}_portable_level{1,2,3}.png` (the portable state — likewise),
plus `resources/lead.png`, `resources/gold.png` and `star.png`. **Palette follows the client's own two
team colours — blue = side A, red = side B** — and because sides alternate each game the scorebug plate
keeps the *alias* constant and recolours its swatch per game. Licence is recorded honestly in `NOTICE`
(§Packaging): `client/LICENSE` **is the GNU AGPL v3**, while `client/package.json` declares
`"license": "GPL-3.0"` — both facts are stated, and the AGPL file is the one the repository relies on.

Board rendering (`render.nim`): the **rubble heat layer** is drawn first, because rubble is this
year's terrain and a spectator who cannot see it cannot understand why a soldier is standing still —
a five-step ramp from bare ground (0) through to near-black (100), with the exact value in the tooltip
and a legend chip in `#bc22-econ`; the client's own `tiles/terrain*.png` photographs do not survive a
16 px cut, so the ramp is this repository's own paintbot-derived tones, as bc23's is. Lead squares
carry the `lead.png` glyph sized by amount with the **number** printed at ≥ 12 px per square, and a
**hollow glyph the moment a square hits zero** — which is how a spectator sees a `mine_floor: 0`
faction eating its own map. Gold squares carry `gold.png` (they only ever appear where something
died). Robots are drawn by type at two team palettes with a health bar, a **level pip** for a mutated
building, **hatching** for a prototype and a **dashed outline** for a portable one. An anomaly draws a
two-second full-board wash in its own colour (abyss violet, charge white, fury orange, vortex teal)
and, for a VORTEX, the rubble layer visibly re-orients, which is the most spectacular single frame in
any Battlecode year this repo ships.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else, and the `#bc22-*` boxes dropping
their word labels to glyphs under 640 px; `#bc22-anomaly` keeps its type word and countdown at every
width, because it is the readout that makes the year make sense).

- `#scorebug`: both faction plates — `CLAN ASH` over the real player name (`daveey`) and the motto —
  the live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 1412 / 2000`, `game 2 of 3 — intersection`.
- `#bc22-archons`, `#bc22-anomaly`, `#bc22-econ`, `#bc22-units` as above.
- `#board`: the rubble heat layer, lead and gold with numbers, every robot with type, team, health,
  mode and level.
- `#bc22-doctrines`: each sheet in plain words ("mines the map dry", "leaves one lead on every square
  so it regenerates", "first laboratory at round 140 and keeps it away from the crowd so gold costs
  three lead", "spends gold on level-three mutations", "builds a watchtower at the frontier", "reads
  the anomaly schedule and stands its buildings up before a fury", "walks its archons toward lead",
  "pulls a soldier out at 55 % health"), plus the capped `notes`, the **submitted-vs-applied badge**,
  and a fallback badge when a seat's doctrine came from the fallback sheet. Dismissible.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and
  provably clear of the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words; the per-game score
  line; and `#bc22-mutation`, the **war panel**: per faction, archons started / lost / left and how
  many walked; lead and gold mined, reclaimed, banked and spent; squares mined dry; laboratories
  built / finished and the gold they made at what average price; watchtowers built / finished;
  mutations by level; sages built and the damage they did against soldiers' and watchtowers'; repairs
  and HP restored; and an **anomaly ledger** — for each of the scheduled anomalies, what each side
  lost and what it dodged. Nothing about archons, resources, buildings or anomalies is stored in the
  replay: the wasm sim re-derives every round.

**The endcard template is FIXED for bc22, not inherited broken.** bc25's and bc23's phase-60
verifications both found the same shared-template defects and both handed them forward; this run
fixes them in `client/replay_broadcast.html` **for all years in the same commit**, because they are
one template:

1. **This year's nouns, not bc26's.** The endcard's noun table is keyed by `data-year`; bc22's entries
   are `archon`/`archons`, `lead`, `gold`, `laboratory`, `watchtower`, `soldier`, `sage`, `miner`,
   `builder`, `mutation`, `anomaly`. No "rat", no "cheese", no "king" appears on a bc22 card.
   `tests/test_viewer.nim` asserts the bc26 nouns are absent from every non-bc26 branch of the table.
2. **No clipping or overflow at 1280×800.** The war panel's grid is `max-height: calc(100vh -
   var(--band) - var(--topband) - 24px)` with `overflow-y: auto` on the panel body only, and
   `tools/ci/viewer_smoke.mjs --killfeed-overlap` gains a `#endcard` scroll-height-vs-client-height
   assertion at 1280×800 after the 100 % seek. bc25's finding was the winner's stat block being cut
   off; this makes it a gate.
3. **No raw unrounded floats.** Every number the card prints goes through one formatter
   (`fmtStat(value, kind)`): integers as integers, rates as `x.x`, percentages as `NN %`, and
   `points`/`scores` as integers (they already are). `tests/test_viewer.nim` greps the rendered card
   text for `/\d\.\d{3,}/` and fails on a hit.
4. **No empty mottos and no "a accelerating"-class grammar.** A blank `motto` renders **nothing** (no
   empty quotes, no orphan dash), and every generated phrase is built from a full sentence per case
   rather than an article plus a knob value — bc23 shipped `"a accelerating"` because it concatenated
   `"a "` with an enum string. bc22's plain-words builder has no article concatenation anywhere:
   every knob value maps to a complete clause, listed in `knobs.nim plainWords22()` and asserted
   non-empty and article-free by `tests/test_bc22_sheet.nim`.

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`, `player`
  → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar), `platform: linux/amd64`,
  `build: {context: ., network: host}`. One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and
  `/bin/battlecode-player` from one image and copies `data/` (now carrying `maps/bc22/`,
  `bc22/tables.json` and `atlas_bc22.*`). **No JDK, no JRE, no Java, no node in any runtime stage** —
  the 2022 engine's toolchain exists only in the `parity-oracle-bc22` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc22 game block along
  with the other six.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc22` is 2022 'Mutation' — miners dig lead
    out of a map that only regenerates the squares you do not empty, laboratories turn lead into gold
    at a price that rises with company, and anomalies strike every two hundred rounds until the
    Singularity takes the weaker side at round 2000."*
  - `tags` unchanged (already four: `battlecode`, `strategy`, `mixed-motive`, `wasm`).
  - `game.config_schema`: `year.enum` becomes `["bc26","bc20","bc21","bc24","bc25","bc23","bc22"]`
    (appended, so no existing index moves). `pool.enum` unchanged (`small` / `mixed` / `large`; each
    year owns its own pool table). `maxRounds` keeps `minimum 50, maximum 2000` — **bc22's 2000 is
    exactly the existing ceiling, so no schema change is needed**. `gamesPerMatch` keeps `maximum 3`;
    `perGameBudgetSeconds` keeps `maximum 300` (bc22 uses 110) and `matchBudgetSeconds` `maximum 600`
    (bc22 uses 340). `tokens` stays **declared and required** (the runner injects it — the 2026-09-03
    lesson); every array keeps `minItems`/`maxItems`; no runner-managed `tokens` **values** inside any
    `game_config`; `additionalProperties: false` stays.
  - `game.results_schema`: bc22's optional properties added beside the other years' (§Server, player,
    protocol), plus the new year-neutral optional `sheet_envelope`; `games.items.required` unchanged
    (the five year-neutral keys); `end_reason`'s enum extended with exactly **three** values —
    `more_archons`, `more_gold_net_worth`, `more_lead_net_worth`. **`annihilated`, `coin_flip` and
    `abandoned` are already there** (bc21's and bc26's) and bc22 reuses them rather than adding
    near-duplicates. **`resignation` is not added** (unreachable from a JSON doctrine) and there is no
    droid-elimination value, because losing every droid ends nothing in this year.
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one
    entry and keeps the eight it has: `rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc23.md`,
    `rules-bc24.md`, `rules-bc25.md`, **`rules-bc22.md`** (Battlecode 2022 "Mutation": rules, knobs
    and divergences → `docs/RULES-BC22.md`), `replay.md`, `parity.md` (→ `docs/PARITY.md`, which gains
    a bc22 section). Nine pages, every one a `{id, title, content:{type, value}}` object.
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc22
    resolution ("…, wololo on bc22" / "…, examplefuncsplayer22 on bc22").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The
  certifier's `players-run` step requires **every** declared `player[]` entry to occupy a slot in
  `certification.players`, and the certifier also requires
  `len(certification.players) == certification.game_config.num_agents`. With `num_agents = 2` there
  are exactly **two** cert slots, they are filled by `awu` and `scaffold`, and therefore **`player[]`
  may contain exactly those two ids and nothing else**. Adding `battlecode-bc22-wololo` or any other
  year-specific runnable to `player[]` would fail the release with `players_missing`. It is also
  unnecessary: `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`, so seating
  `awu` on a bc22 episode already plays `wololo` and seating `scaffold` already plays
  `examplefuncsplayer22`. The scripted bc22 policies reach the league through
  `tools/ci/policies.json`, which is a *policy* list and has nothing to do with `player[]`.
  `tests/test_manifest.nim` asserts all three facts (`player[]` ids == `certification.players` ids;
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
  | `bc23` | Battlecode 2023 — Tempest (2 seats) | unchanged | **2** |
  | `bc22` | Battlecode 2022 — Mutation (2 seats) | `year: "bc22"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 2000`, `num_agents: 2`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 110`, `matchBudgetSeconds: 340`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `bc22`'s variant description: *"Best of three on the mixed pool. Miners dig lead out of the map,
  and the map only puts lead back on squares you did not empty — so the cheapest mistake in this year
  is mining the last unit off a deposit. Soldiers cost lead and deal three damage; sages cost gold,
  deal forty-five, and gold exists only because a laboratory makes it, more cheaply the lonelier it
  is. Anomalies strike every two hundred rounds — the abyss eats your bank, the charge kills whoever
  clumped hardest, the fury burns buildings that are standing still, and the vortex reshuffles the
  ground — and at round 2000 the Singularity takes the weaker side. Lose your last archon and you
  lose immediately."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false`).

  **The `<SEATS>` cross-check, named explicitly.** `.github/workflows/ci.yml` substitutes
  **`<SEATS>` = 2** into the `docker-smoke` job, and `tools/ci/docker_smoke.sh` takes the seat count
  **solely** from `certification.game_config.num_agents`, hard-failing with `SEAT-COUNT FAIL:` if the
  workflow's value disagrees — and it also refuses a `SMOKE_CONFIG_OVERRIDE` that tries to change
  `num_agents`. Since the cert fixture keeps `num_agents: 2` and the bc22 variant declares
  `num_agents: 2`, the two independent declarations agree. A ranged or vague seat count here would
  fail CI later, not here; there is exactly one number in this note and it is **2**.

  **Certification fixture — UNCHANGED, and stays on bc26.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, `"num_agents": 2` and its existing fast settings (`pool: small`, `seed: 1`,
  `gamesPerMatch: 1`, `maxRounds: 400`, `attempt1Ms: 4000`, `retryMs: 2000`, `doctrineBudgetMs: 9000`,
  `perGameBudgetSeconds: 40`, `matchBudgetSeconds: 45`, `connectTimeoutMs: 15000`). There is **no bc22
  certification fixture in v1** (§Out of scope): certification is the platform's contract check, it
  already passes on bc26, and re-pointing it at a brand-new year module would put the release at the
  mercy of the newest code for no gain. **This is also the pin the LEARNINGS 2026-09-04 entry demands
  explicitly**: the cert fixture has exactly 2 players = `num_agents`, so adding `player[]` entries
  fails `players_missing`. bc22 is proven instead by its own `docker-smoke` episode (§Tests), which
  produces a real bc22 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  **`0.6.0 → 0.7.0`** — because it adds a variant and adds optional results properties without
  changing any existing *rule*. `GameVersion` goes `GV09 → GV10` and
  `ReplayCompatibleGameVersions` is **extended** to
  `["GV04","GV05","GV06","GV07","GV08","GV09","GV10"]`, so every hosted
  bc26/bc20/bc21/bc23/bc24/bc25 replay keeps rendering (the bc20 learning about `GameVersion`
  handling: extend, never reset, and claim the version across branches with
  `tools/ci/check_gameversion.sh`). **The one year-neutral behaviour change this run makes — the
  doctrine-sheet envelope unwrap (§Decisions) — cannot reach a recording**, because
  `replay.nim:173–176` re-validates the recorded *applied* sheet, which is always a flat object of
  known keys; that is why the compatibility list extends rather than resets, and the changelog entry
  says so in as many words. The release is dispatched through the existing `coworld-release.yml` with
  the same step order (build → certify → upload-policies → upload-coworld → secret put).
  **Certify runs against bc26, exactly as before**, and `release-result.json` must still show
  `canonical: true` and `certify.replay_liveness` containing
  `skipped (static replay bundle declared`.

- **Branch discipline.** All work lands on the branch **`bc22-year-module`**, PR-then-merge, and
  `ci.yml`'s `on.push.branches` gains that branch beside `main`, `bc20-year-module`,
  `bc21-year-module`, `bc23-year-module`, `bc24-year-module` and `bc25-year-module`. The branch is
  rebased onto `origin/main` before every push. **The sibling run 2026-09-04-battlecode-2024 is
  BLOCKED with its PR #4 open on this repo and its bc24 module already on `main`**, so this run is
  branch-only until its own PR merges and it must never touch that branch, that PR or the bc24
  module; if PR #4 lands first and takes `GV10`, this branch rebases to `GV11` and extends the
  compatibility list again — the bc20 precedent, and `tools/ci/check_gameversion.sh` is the thing
  that catches it. bc22 touches exactly these shared files — `sim_types.nim`, `baselines.nim`,
  `sheet.nim`, `years/registry.nim`, `years/dispatch.nim`, `render.nim`, `broadcast.nim`, `replay.nim`
  (the two-line `sheet_envelope` read/write), `results.nim` (the enum list), `match.nim` (the bc22
  event names), `client/replay_broadcast.html`, `coworld_manifest_template.json`,
  `tools/ci/policies.json`, `tools/gen_year_constants.py`, `tools/ci/viewer_smoke.mjs` (the endcard
  overflow assertion), `.github/workflows/ci.yml`, `docs/PARITY.md`, `NOTICE`, `README.md`,
  `tests/test_manifest.nim`, `tests/test_viewer.nim`, `tests/test_determinism.nim`,
  `tests/test_constants.nim`, `tests/test_sheet.nim` — and every edit to each of them is **additive**
  (a new enum value, a new `case` arm, a new appended block) **except two**, which are named here so
  the reviewer looks for them: the `sheet.nim` envelope resolver (a rewrite of five lines, with the
  existing behaviour preserved as the first two rules) and the four shared-endcard fixes in
  `client/replay_broadcast.html` (§Viewer), which deliberately change what **every** year's endcard
  renders. **Everything else on `main` is untouched**: no bc26/bc20/bc21/bc23/bc24/bc25 module file,
  map, atlas or variant is edited.

- **`tools/ci/policies.json`** gains the bc22 set beside the bc26, bc20, bc21, bc23, bc24 and bc25
  sets (a scripted champion is a failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-bc22-rush","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"rush"}},
   {"name":"battlecode-bc22-transmuter","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"transmuter"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-wololo","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"wololo","PLAYER_POLICY_LABEL":"wololo"}},
   {"name":"battlecode-examplefuncsplayer22","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer22","PLAYER_POLICY_LABEL":"examplefuncsplayer22"}}]
  ```
  `<IMAGE>` is the **player** service's image (the 2026-09-03 lesson). **Champion #2 carries the
  `"player"` field `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` (daveey-1)** and is uploaded while that
  player is active. LLM credentials reach the **game** container through the manifest env; the player
  pods need no Bedrock sidecar in this lineage.

  **Release dispatch shape, decided:** dispatch `coworld-release.yml` with a `policies` **override**
  limited to the four bc22 entries (the bc20 pattern), so the release does not recut vN+1 of the
  bc26/bc20/bc21/bc23/bc24/bc25 policies the six existing leagues have seated. If the override is
  ever dropped and the full file is used instead, phase 50 must take its labels from **this**
  release's `release-result.json` and never from remembered ones (the bc21 learning). Either shape
  works; this run picks the override.

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **seventh league**, created beside the bc26, bc20, bc21, bc23, bc24 and bc25 ones and touching none
of them and not the game's default league:

| field | value |
|---|---|
| `league_key` | `bc22` |
| `league_name` | `Battlecode 2022 — Mutation` |
| `default_variant_id` | `bc22` |
| `short_name` | `bc22` → `softmax.com/battlecode/bc22` (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc22-rush` (owned by **daveey**), `battlecode-bc22-transmuter` (owned by **daveey-1**) — deliberately the year's two poles, the patch-driven soldier meta against the gold-and-anomaly game nobody played |
| fillers (scripted) | `battlecode-wololo`, `battlecode-examplefuncsplayer22` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues`
filtered on `game.coworld_name` now returns **seven** rows; select by `league_key`/name or you will
configure a sibling year's league. Fillers are set **before** the first `trigger-round`. The atlas
slug is `battlecode/bc22`.

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged by
the repository itself. `NOTICE` gains five sections:

- **`battlecode/battlecode22` engine — AGPL-3.0** (verified: `engine/COPYING` **and**
  `schema/LICENSE` **and** `client/LICENSE` are each the GNU AGPL v3; the repository root itself
  carries no `LICENSE` file). Pinned commit `6ed05b679c0822e9bbe332812ff5655812dd023e`. The derived
  files are named individually: `src/battlecode/years/bc22/**` (behaviour, hand-ported),
  `years/bc22/constants.nim` (generated from `GameConstants.java` + `RobotType.java` +
  `AnomalyType.java`), `years/bc22/trove.nim` (**trove4j 3.0.3**'s `TIntObjectHashMap` iteration
  order, reproduced as behaviour — see the separate section below, because trove is **not** AGPL),
  `data/maps/bc22/*.json` (converted from `.map22`), `data/bc22/tables.json` (generated from the
  engine's own arithmetic), and `years/bc22/chassis/scaffold22.nim` (examplefuncsplayer, ported
  statement for statement — it is the parity oracle's other side and may not gain behaviour).
  **The engine itself is used only at CI time**; no JDK, no JRE and no upstream Java source or
  bytecode exists in any image this repository builds.
- **`net.sf.trove4j:trove4j` 3.0.3 — LGPL-2.1.** `years/bc22/trove.nim` reproduces the *observable
  iteration order* of `TIntObjectHashMap` (§Sim module, D2). It is a behaviour port of a documented
  open-addressing scheme, hand-written in Nim, with no trove source or bytecode vendored, compiled or
  copied; the class files reached only the **CI-only** oracle jar's classpath, never any image. The
  dependency and its licence are recorded because reproducing a library's iteration order is a
  derivation of its *behaviour* and the repository says so plainly rather than leaving it implicit.
- **`battlecode/battlecode22` client sprites — AGPL-3.0.** `client/LICENSE` **is** the GNU AGPL v3
  while `client/package.json` declares `"license": "GPL-3.0"`; both facts are recorded and the AGPL
  file governs. `data/atlas_bc22.*` is cut from `client/visualizer/src/static/img/**` and is credited
  in `NOTICE`, naming the source directories (`robots/`, `resources/`, and `star.png`).
  `schema/package.json` also says `GPL-3.0` while `schema/LICENSE` is the AGPL — the discrepancy is
  recorded and is moot here, because **no schema code is used at all** (there is no flatbuffers reader
  on either side of this port, only a hand-written vtable walk in the map converter).
- **`iliao2345/Battlecode2022` — AGPL-3.0**, head `c42645a0`, `src/fury_fix_20/`. What derives from
  it: `years/bc22/chassis/{wololo,kit,econ,archon,miner,soldier,micro,anomaly}.nim` — the rubble-
  weighted BFS and its checkpoint navigator, the miner's `mine_until` floor and its mine-move-mine
  turn shape, the archon's build-rate/urgency model with its saturation caps and its 20-round miner
  employment ring buffer, the archon repair priority (sage, then soldier, then idle miner), the
  soldier and sage micro with the sage's `0.6 × cooldown` advance gate, and the pre-vortex archon
  relocation. **Behaviour, not code**, rewritten in Nim and parameterised by this coworld's doctrine
  sheet.
- **`BSreenivas0713/Battlecode2022` — AGPL-3.0**, head `c388fe8a`, `src/MPTempName/`. What derives
  from it: `years/bc22/chassis/{lab,builder,gold,comms}.nim` — the laboratory siting and solitude
  gate, the builder's prototype-then-repair discipline, the mutation ladder's marginal-value ordering,
  and the comms slot layout it shares with jmerle's. It is the published bot of the three whose own
  directory history (`MPLaboratory`, `MPMoreLabs`) shows it actually iterated on the gold economy,
  which is why this year's headline doctrine axis has a real behaviour source.
- **`jmerle/battlecode-2022` — MIT**, head `f57d3549`, `src/camel_case_v25_final/`. What derives from
  it: `years/bc22/chassis/comms.nim` (the 64-slot shared-array layout and its 16-bit packing, from
  `util/SharedArray.java`) and `kit.nim`'s per-radius navigators (from
  `dijkstra/Dijkstra20|34|53.java`, one per vision radius, which is the right shape for a year whose
  radii are 20 / 34 / 53).
- **Unlicensed repositories are not vendored, not ported, not compiled, not read and not cloned** —
  the same rule as every other year, applied here to **`IvanGeffner/BC22`**, which carries no licence
  anywhere and contributes nothing. `5 Musketeers` is not published on GitHub and likewise contributes
  nothing.

`docs/RULES-BC22.md` carries the full **§Divergences** list: (1) no bytecode instrumentation — a
fixed 2 000/1 250/750/500-`DecisionOps` budget with no mid-turn resumption and no mid-primitive cut,
together with the measurement that makes it harmless here (peak 6–7 % of the limit, zero cut-offs)
and the CI assertion that fails the job at 50 %; (2) `setWinnerArbitrary`'s `Math.random()` replaced
by a world-RNG draw (D3); (3) `eachRobot`'s hash-order sweeps not ported at all, with the
no-observable-behaviour argument per site (D1); (4) **`robotsArray()`'s trove order ported rather
than replaced, with the 51–58 % CHARGE-tie measurement that forces it** (D2); (5)
`net.sf.jsi`'s RTree written and never read, so not ported (D5); (6)
`RobotControllerImpl.random` dead (D6); (7) the nine prose-versus-engine resolutions from §The game;
(8) `resignation` reachable in the engine through `rc.resign()` but unreachable here; (9) the
laboratory rate's `Math.exp` computed through `fdlibm` and tabled over its whole reachable domain,
with the argument about `Math.exp` versus `StrictMath.exp`; (10) the `deadline` wall-clock stop, a
coworld concept and not an engine one, recorded as one load-bearing record; (11) 22 of the 75
official maps converted, with the reasons for the exclusions; (12) the year-neutral doctrine-sheet
envelope unwrap and bc22-only absent-key defaulting, with the reason each is scoped the way it is;
(13) both chassis are behaviour ports parameterised by the doctrine sheet; (14) the chassis file
layout, if the builder merges any two modules; (15) the four shared-endcard template fixes, which
change what every year's endcard renders.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, `<SEATS>` = **2**). The sandbox runs none of it; CI is the harness. The `test`
job's `timeout-minutes` goes **110 → 130** (LEARNINGS 2026-09-08: the test job alone is already
~60 min with six year modules, and each file runs twice — debug and `-d:release`).

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc22_cooldown.nim`** — the two counters: both decrement by 10 at the start of every
   turn and floor at 0; **a robot starts life with both at 0**, so a droid built on round *r* acts and
   moves on round *r+1* (the opposite of bc23, and pinned here because it is the thing that makes
   bc22 armies grow); an action needs `< 10` **and** `mode.canAct`; a move needs `< 10` **and**
   `mode.canMove`; **a MINER with `actionCooldown = 2` mines exactly five times in one turn on rubble
   0 and is refused the sixth**, and exactly once on rubble 60; **the rubble multiplier is the float64
   expression `(int)((1 + r/10.0) * base)`** and the 22 measured `(base, rubble)` pairs where it
   differs from the integer form are named vectors (`base 25 r 36 → 114`, `base 100 r 13 → 229`,
   `base 200 r 92 → 2039`); and **where the multiplier is read**: a move charges at the
   **destination**, every other action at the actor's own square, and a mutation charges the builder at
   the builder's square and the building's 100+100 at the building's square.
2. **`tests/test_bc22_units.nim`** — the seven-type table and every per-level value against
   `data/bc22/tables.json`: `getMaxHealth`, `getDamage`, `getHealing`, `getLeadMutateCost`,
   `getGoldMutateCost`, `getLeadWorth`, `getGoldWorth`, `getLeadDropped`, `getGoldDropped`; a
   soldier's 3 at r² ≤ 13 and a sage's 45 at r² ≤ 25 **including at a robot it cannot see**; an attack
   on an empty square or on an ally is illegal; `canBuild`, `canAttack`, `canEnvision`, `canRepair`,
   `canMine`, `canMutate`, `canTransmute` and `isBuilding` for all 49 type pairs; `addHealth` capping
   at max, promoting a full-health PROTOTYPE to TURRET, destroying at `≤ 0`, and honouring
   `checkArchonDeath`; and **the reclaim drop landing on the square the robot last occupied and
   stacking**, with `ARCHON` dropping **20 Au** at level 1 and **60 Pb + 36 Au** at level 3.
3. **`tests/test_bc22_economy.nim`** — mining one unit per action from the miner's own square or any
   of the eight around it (r² ≤ 2) and never from an empty square; the passive `+2` per team per
   round; **the every-20-rounds `+5` added only to squares holding `> 0`**, with the named regression
   that a square taken to 0 never recovers (and the measured example-bot fact that the whole
   `charge` map reached 0 lead at **round 934**); and the **laboratory rate** table for all
   `3 × 177` `(level, n)` pairs against `data/bc22/tables.json`, including n=0 → 2 and n=40 → 11, plus
   the `fdlibmExp`-vs-committed-table agreement assertion (the bc21 shape).
4. **`tests/test_bc22_anomaly.nim`** — one entry consumed per matching round and **never two**; the
   schedule readable at all times; and each body exactly:
   **ABYSS** removing `(int)(0.1f × square)` in whole-map scan order (with **9 → 0** and 10 → 1 as
   named vectors) and `⌊reserve/10⌋` from A-lead, B-lead, A-gold, B-gold **in that order**;
   **CHARGE** ranking the **combined** droid population, stable-sorting descending, destroying
   `(int)(0.05f × n)` (with **19 → 0**, 20 → 1, 39 → 1, 40 → 2, 59 → 2, 60 → 3 tabled for n 0…500),
   never touching a building or a prototype, and each victim dropping its reclaim;
   **FURY** hitting only TURRET mode with truncation (**level-1 watchtower → 7**, level-2 → 13,
   level-3 archon → 97), sparing PORTABLE and PROTOTYPE entirely, and running the
   `checkArchonDeath = false` double-elimination check;
   **VORTEX** permuting only the rubble array, with all four arms exercised — `VERTICAL` → flipV with
   no draw, `HORIZONTAL` → flipH with no draw, `ROTATIONAL` square → `rand.nextInt(3)`,
   `ROTATIONAL` non-square → `rand.nextInt(2) + 1` — and the `Random(mapSeed)` stream asserted against
   a recorded oracle sequence; plus the three sage versions (99 % / 22 % of max HP on enemy droids /
   10 % on turrets, all within r² ≤ 25) and the fact that a sage cannot envision a VORTEX.
   **And the ordering test:** passive `+2` lands **before** the anomaly and the map `+5` **after** it,
   asserted on a round where an ABYSS and a multiple of 20 coincide.
5. **`tests/test_bc22_buildings.nim`** — a building spawns as `PROTOTYPE` at `(int)(0.8f × maxHealth)`
   (120 watchtower, 80 laboratory, tabled for all nine values) and can neither act nor move; **15
   builder repairs finish a watchtower and 10 finish a laboratory**; a full-health prototype becomes a
   TURRET on the repair that fills it; `transform` flips the mode **first** and then charges 100 to
   the **action** counter when the new mode is TURRET and to the **movement** counter otherwise
   (divergence 1), through the square's rubble multiplier, and `canTransformCooldown` /
   `getTransformCooldownTurns` read the mode-appropriate counter; `mutate` charges the builder, levels
   the building, adds exactly the health difference, and charges the building 100 on **both** counters;
   level 2 costs lead and level 3 costs gold; a level-3 building refuses a fourth mutation; a DROID and
   a PROTOTYPE refuse mutation; and **an archon transforms to PORTABLE and walks** at movement cooldown
   24 × rubble.
6. **`tests/test_bc22_execorder.nim`** — the exec-order list: append on build, **by-value removal** on
   destroy preserving the order of the survivors, the pre-sweep snapshot so a robot built this round
   takes no turn this round, the `existsRobot` skip for a robot destroyed mid-sweep, and the initial
   archons in **ascending id** because `LiveMap` sorts them (measured `maze` ids 2, 3, 6, 7, 8, 9, so
   A and B alternate). 500 random build/destroy sequences replayed against the oracle's own list.
7. **`tests/test_bc22_trove.nim`** — **the D2 fidelity gate.** `years/bc22/trove.nim`'s
   `TIntObjectHashMap` reproduces trove4j 3.0.3: the capacity ladder from `PrimeFinder`, the
   `hash & 0x7fffffff` initial probe modulo the table length and the `1 + (hash % (length − 2))` step,
   `FREE`/`FULL`/`REMOVED` states, the rehash trigger, and the **descending-index** `values()` walk.
   500 random spawn/destroy sequences (drawn from the real `IDGenerator` id stream, because the ids
   are what the hash sees) are compared against a **recorded oracle order** — the `H hashord` line of
   the Tier A trace — and a separate vector asserts that a CHARGE with a tie at the cut destroys the
   same robots as the JVM. The test carries the measurement that forces it in its header: **ties
   straddle the 5 % cut in 51–58 % of rounds** (measured on `maze`, `chalice` and `island_hopping`).
8. **`tests/test_bc22_sensing.nim`** — vision r² ≤ 20 for miners, builders and soldiers, r² ≤ 34 for
   archons, watchtowers and sages, r² ≤ 53 for laboratories, with **no occlusion of any kind**; the
   engine scan order with the `ceil(sqrt(r²)) + 1` box and the map clamp, asserted against a recorded
   oracle sweep; the precomputed `ceil(√r²)` table matching `Math.ceil(Math.sqrt(r²))` for
   `{2, 5, 13, 20, 25, 34, 53}`; `senseNearbyRobots` excluding self and returning in scan order (which
   is what fixes the square the example bot's soldier attacks); an attack needing **no** vision; and
   `getNumVisibleFriendlyRobots` counting friendly robots **excluding itself** inside r² ≤ 53 for a
   laboratory.
9. **`tests/test_bc22_comms.nim`** — index 0…63 and value 0…65535 enforced; **any robot may read and
   write at any time with no cooldown, no range test and no cost** (the 2022 rule, and the one place
   this year is *simpler* than 2023); the two teams' arrays are isolated and neither can read the
   other's; and the chassis's 16-bit slot packing round-trips for every slot class.
10. **`tests/test_bc22_endladder.nim`** — `annihilated` fires **mid-turn** inside `destroyRobot` and
    the round still finishes; **both teams annihilated in one round** resolves by exec order outside a
    fury and by the gold/lead/coin ladder **inside** one (divergence 7), which is the only way
    `more_gold_net_worth` / `more_lead_net_worth` / `coin_flip` fires before round 2000; the three
    Singularity rungs fire in the engine's order with a vector each, computed with `getGoldWorth` /
    `getLeadWorth` over live robots plus reserves; `coin_flip` is reachable and seeded from the world
    RNG (D3); **a faction with one archon and no other robot plays on to round 2000** and keeps
    earning 2 Pb a round; and `resign()` is provably unreachable from any chassis.
11. **`tests/test_bc22_scoring.nim`** — the points formula with float32 narrowing and truncation, one
    vector per weight; the 0–0 `share` returning 0.5 (and the **measured-common** all-zero gold case,
    since the example bot never builds a laboratory and every measured mirror ended 0 Au – 0 Au);
    points in `[0, 100]` and the seats summing to ≤ 100; the super-increasing property
    (`24 > 12`, `64 > 36`) asserted as arithmetic; **the documented case where `points` favours the
    loser** asserted as an explicit expectation rather than left to be found; and `results.scores`
    **strictly** ordering the match winner above the loser on 500 random synthetic finals, including
    clinched two-game matches.
12. **`tests/test_bc22_maps.nim`** — every committed bc22 map re-converts identically from the pinned
    `.map22`; sizes, seeds, declared symmetry, rubble mean/max/min, lead squares/total/max, archons per
    side and the **full anomaly schedule** match the table in §Sim module; every map is within 20…60 in
    both dimensions; **every initial body is an ARCHON and both sides have the same number** (1…4);
    rubble is within 0…100 everywhere; **the first VORTEX permutation of every committed map with a
    vortex** matches the oracle (which is what pins the `Random(mapSeed)` stream); no bc22 map name
    resolves to another year's map file; and **the seed the `docker-smoke` step passes draws exactly
    `snowflake_redux`** from the `small` pool, so the smoke's map cannot drift silently.
13. **`tests/test_bc22_sheet.nim`** — every one of the eleven knobs: **absent → default AND recorded
    in `defaults_applied`** (the envelope pin, item 2 — and the same test asserts a **bc23** empty
    sheet still records none, so the change is provably scoped); mistyped → default + recorded;
    unknown enum value → default + recorded; **the five integer knobs CLAMP to their range rather than
    defaulting** (and a non-integer defaults); enum values are case-folded, trimmed and `-`/space
    normalised; unknown keys recorded (≤ 16, ≤ 40 runes); **a submitted `chassis` is recorded as an
    unknown field and never honoured** (the D1 assertion, which fails if anyone re-adds the knob);
    rune-boundary truncation of `notes`/`motto` including astral-plane characters; the 16 KB byte cap
    cut on a rune boundary; **`plainWords22()` returns a non-empty, article-free complete clause for
    every value of every knob** (the "a accelerating" fix, §Viewer); and **the envelope resolver**:
    `{"sheet":{…}}`, `{"doctrine":{…}}`, `{"protocol":"x","doctrine":{…}}`,
    `{"battlecode_2022_doctrine":{…}}`, a bare flat sheet, a payload with **both** a known knob key
    and a `doctrine` key (the flat one wins), and a two-object payload (no unwrap) — each with the
    expected `sheet_envelope` value, and nesting unwrapped **at most once**.
14. **`tests/test_sheet.nim` (extended)** — the same envelope resolver from the **year-neutral** side:
    every existing bc26/bc20/bc21/bc23/bc24/bc25 vector still parses to the same `Sheet` it did
    before, so the one shared change this run makes is provably additive for the six shipped years.
15. **`tests/test_bc22_scaffold.nim`** — `examplefuncsplayer22` reproduced statement for statement: the
    `Random(6147)` call sequence (`nextInt(8)`, `nextBoolean()`) in the engine's own order; the archon
    picking a direction **before** the coin flip; the miner's `dx, dy ∈ {−1,0,1}` loop order and its
    `while (canMineGold) … while (canMineLead)` inner loops; the soldier attacking
    `senseNearbyRobots(actionRadiusSquared, opponent)[0].location`; and the **builder, sage,
    laboratory and watchtower branches doing nothing at all** — every one asserted against a recorded
    oracle trace. It may not gain behaviour: it is one side of the differential oracle.
16. **`tests/test_bc22_baselines.nim`** — bounded orders and legality:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the *same* `validate` the LLM
      path uses;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the
      moment it is emitted**: the right cooldown counter under 10 **and** the mode permitting it, the
      target inside the right radius and on the map, a robot of the right team actually present where
      one is required, the **team** reserve actually holding both costs, the destination unoccupied for
      a move and a build, the level and mode preconditions for a mutation, `mode.canTransform` for a
      transform, `canTransmute` and the lead-vs-rate test for a transmute, no building moving in TURRET
      mode, no non-attacker attacking, no non-miner mining, no non-sage envisioning; and **no robot
      exceeds its `DecisionOps` budget**;
    - (c) `examplefuncsplayer22` **acts** — ≥ 1 miner built, ≥ 1 soldier built, ≥ 1 lead mined,
      ≥ 1 attack landed — but is **not** required to survive, to build a building, or to compete;
    - (d) `wololo` beats `examplefuncsplayer22` on 3 seeds × 2 `small` maps, 6/6.
17. **`tests/test_bc22_survival.nim`** — the **economic-survival gate** (the LEARNINGS pin), with an
    inverted control. **The key design point, stated because it is bc22-specific and easy to get
    wrong: in this year the map's lead is finite unless you leave some behind, so a chassis that
    strip-mines looks rich for four hundred rounds and then starves.** The gate therefore keys on
    **units, buildings, gold and archon survival**, and on **lead still on the map**:
    - `wololo` vs `wololo`, all-defaults sheet, 3 seeds × 2 `small` maps = 6 games, each to round
      2000. In **≥ 5 of the 6** the game must **reach the round limit or end on the Singularity
      ladder** (i.e. not `annihilated`) — the ≥ 4-in-5 shape the LEARNINGS pin asks for, rounded up to
      5-in-6 so the committed ratio is at or above it — and in **all 6** each seat must have: built
      ≥ 25 miners and
      ≥ 15 soldiers; mined ≥ 600 lead; built ≥ 1 builder and ≥ 1 laboratory and **finished** it;
      transmuted ≥ 5 gold; **still held at least one archon at round 1500**; and finished with ≥ 10
      robots alive. **Across the two seats** the map must still hold ≥ 25 % of its starting lead at
      round 2000 (the `mine_floor: 1` default working), and ≥ 1 anomaly must have measurably hit
      someone.
    - The same gate is then run as a **subprocess** against a **known-broken chassis** compiled behind
      **`-d:bc22BrokenChassis`** — a `wololo.nim` variant whose miners **ignore `mine_floor` and always
      mine to zero** and whose archons **never build a builder**, so the map is stripped by round 900
      (measured on the real engine: the example-bot mirror emptied `charge` at round 934), no
      laboratory is ever built, no gold is ever made, and the faction is a lead-starved soldier queue —
      and it **must come back red**. That control is chosen deliberately: it is exactly the failure a
      "did it build units?" check would pass, and it is the failure this year's signature knob exists
      to prevent. A gate that cannot fail is not a gate; this assertion is what keeps it honest, and it
      is the direct answer to the 2026-09-03 finding that mechanical episode checks pass degenerate
      matches.
    - **The thresholds above are the design floor, not the committed numbers.** Phase 20 **measures** a
      healthy mirror and the broken control, sets the committed thresholds between them with margin
      (and never below this note's floor), and records **both** measured ranges in the test's header
      comment — exactly as `tests/test_bc23_survival.nim`, `test_bc24_survival.nim` and
      `test_bc25_survival.nim` do today. If any floor here proves unsatisfiable on the measured healthy
      mirror, the resolution is the bc23 r1-F21/F22 one: **lower the committed number to roughly half
      the weak seat's measured value and record the measurement inline** — never drop the clause.
18. **`tests/test_bc22_knobs.nim`** — the knob-teeth gate. Paired seeded games (identical seed, map and
    opponent; the two factions identical except one knob at its low and high setting, 3 seeds each),
    each asserting a named, signed delta. Thresholds live in one table so tuning is a one-line change,
    and the header records every substituted statistic (the bc21 r1-F6 fix):

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `miner_eco` → `soldier_rush` | soldiers built by round 400 up ≥ 60 % **and** miners built by round 400 down ≥ 30 % |
    | `opening` | `miner_eco` → `sage_spam` | round of the first laboratory earlier by ≥ 100 **and** sages built up ≥ 2 |
    | `miner_count_curve` | `lean` → `heavy` | miners built up ≥ 2× **and** lead mined up ≥ 40 % |
    | `mine_floor` | 0 → 3 | **lead still on the map at round 2000 up ≥ 3×** **and** squares mined dry down ≥ 60 % **and** lead mined by round 400 down ≥ 10 % (the trade-off is the point) |
    | `soldier_sage_ratio` | 100 → 0 | sages built up ≥ 3 **and** soldiers built down ≥ 30 % **and** gold transmuted up ≥ 40 |
    | `lab_round` | 1500 → 100 | round of the first finished laboratory earlier by ≥ 900 **and** gold transmuted up ≥ 30 |
    | `lab_solitude` | 40 → 0 | mean lead spent per gold down ≥ 30 % **and** laboratory transforms up ≥ 1 (run with `lab_round: 150` on both sides, since the knob is only reachable once a lab exists) |
    | `gold_use` | `sages` → `mutations` | level-3 mutations up ≥ 2 **and** sages built down ≥ 2 |
    | `watchtower_policy` | `never` → `forward` | watchtowers finished up ≥ 2 **and** mean distance of a watchtower from its own archons up ≥ 40 % against `home` |
    | `anomaly_play` | `ignore` → `time_pushes` | **anomalies dodged up ≥ 2** **and** droids lost to CHARGE down ≥ 30 % **and** turret HP lost to FURY down ≥ 40 % |
    | `archon_relocate` | `never` → `lead` | archon relocations up ≥ 2 **and** mean rubble under the archons down ≥ 15 % |
    | `retreat_hp` | 0 → 80 | soldiers lost down ≥ 20 % **and** HP repaired up ≥ 150 |

19. **`tests/test_bc22_perf.nim`** — a full 2000-round game on `fisherman` (45×35, 3 archons a side)
    with both seats on `opening: miner_eco`, `miner_count_curve: heavy`, `mine_floor: 0`,
    `retreat_hp: 0` in **≤ 100 s**; failing it means switching `gamesPerMatch` to 1 (§The game).
20. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain, twice
    in one process and across a save/load; the **two independent `java.util.Random` streams**
    (`IDGenerator` and the VORTEX draw) staying independent; and **record → re-derive for every bc22
    end reason** (`annihilated`, all three Singularity rungs, `coin_flip`, and the wall-clock
    `abandoned`/`deadline` stop applied by the same proc on both paths).
21. **`tests/test_bc22_replay.nim`** — a bc22 replay document round-trips; a **strict UTF-8 parse** of
    the written bytes; the viewer's re-derivation of a recorded bc22 match reproduces the recorded
    per-round hashes; robot positions, health, modes, levels, the rubble/lead/gold arrays, the reserves,
    both shared arrays and the anomaly cursor re-derive identically from events + config + seed with
    nothing stored; `plan.maps` carries all three drawn maps even when the match clinched in two;
    `seats[].sheet_envelope` and `sheet_submitted` round-trip; and **every event kind respects its
    per-game bound** from the table in §Server, player, protocol — including `anomaly_struck ≤ 14`
    against the measured maximum schedule length of 13.
22. **`tests/test_bc22_beats.nim`** — the **beat contract** (§Viewer): from the committed
    `tests/fixtures/replay-bc22.json`, `beatsFor` must return **≥ 28 beats over ≥ 10 distinct kinds**,
    every one with a non-empty label of ≤ 120 runes, every kind inside the fourteen-kind vocabulary,
    and a `html[data-year="bc22"] .beat-marker.<kind>` CSS rule present in
    `client/replay_broadcast.html` for **every kind the fixture actually emitted**. Emission, label
    and style, all three, from the committed artefact — the durable shape the bc25 r1-F26 finding
    asked for.
23. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now seven years wide: the
    results key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; `num_agents` present in **all seven** variants'
    `game_config` and in `certification.game_config`, and **absent** at every variant top level;
    `config_schema.year.enum == ["bc26","bc20","bc21","bc24","bc25","bc23","bc22"]`; **`player[]`
    contains exactly the ids in `certification.players`** and
    `len(certification.players) == certification.game_config.num_agents` (the pair of checks that
    would have caught the bc20 release failure); `end_reason`'s enum containing `annihilated`,
    `more_archons`, `more_gold_net_worth`, `more_lead_net_worth`, `coin_flip` and `abandoned` and
    **not** `resignation`; every `config_schema` array bounded; `tokens` declared and required but
    never valued in a `game_config`; both `game.protocols` keys and `game.docs.readme` plus **all
    nine** `pages` are `{type,value}` objects; and the installed `coworld` CLI's own
    `validate_upload_manifest` / `_load_template_manifest` accepts the template.
24. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc22** fixture replay;
    the bc22 game block shadows no `ChromeCommon` alias and no other year's game-block name (the tandem
    scar); `chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256;
    `#bc22-doctrines` carries a dismiss control and sits outside `var(--band)`; every `#bc22-*` rule is
    scoped to `html[data-year="bc22"]`; `relayout()`'s `--statrail` measurement set names `bc22-econ`
    and `bc22-units`; and **the four shared-endcard fixes** (§Viewer): the bc26 nouns are absent from
    every non-bc26 branch of the endcard noun table, every printed number goes through `fmtStat` (a
    grep for `/\d\.\d{3,}/` in the rendered card text fails the test), a blank motto renders nothing,
    and no generated phrase concatenates an article with an enum string.
25. **`tests/test_constants.nim` (extended)** — `tools/gen_year_constants.py --year bc22 --check`
    regenerates `years/bc22/constants.nim` from the pinned sources and byte-diffs it, and
    `tools/convert_maps_bc22.py --engine … --check` re-converts all 22 committed maps and byte-diffs
    them, plus `--parse-all` reads **all 75** official `.map22` files with the converter's own vtable
    walk (a reader that only works on the maps we ship is a reader nobody can extend the pool with).

### `parity-oracle-bc22` job — the 2022 engine as a CI-only oracle

**The recipe below was EXECUTED in this sandbox, not guessed.** The released fat jar
`https://releases.battlecode.org/maven/org/battlecode/battlecode22/2.2.1/battlecode22-2.2.1.jar`
(HTTP 200, **16 989 241 bytes**, sha256
`56e7530b89893584bf706c90937b3df0eb583cd850f058f9d62004cd5ce78e1c`, pinned in
`tools/oracle/bc22/jar.lock`) is **self-contained**: **11 549 entries**, every `battlecode` class,
every bundled dependency — including **`net.sf.jsi`** and **`gnu.trove`** (trove4j 3.0.3, dated
2012-06-03), so the dead-artifact problem that forced bc21's jsi shim, its 94-file `javac` and its
`deps.lock` **does not arise here** — plus
`battlecode/instrumenter/bytecode/resources/MethodCosts.txt` and all **75** `.map22` map resources.
So there is **no Gradle, no shim, no multi-file compile, no Maven Central download list and no
`deps.lock`** in this job. It is:

1. `actions/setup-java@v4`, `distribution: temurin`, `java-version: **"8"**`. **This is not a
   preference and it is not negotiable, and the reason was measured *here*, not inherited:** the
   engine's `engine/build.gradle` sets `sourceCompatibility = 1.8` and declares
   `org.ow2.asm:asm:5.0.4`, which cannot read modern class files. Under **JDK 21** the instrumenter
   throws `java.lang.IllegalArgumentException` inside `org.objectweb.asm.ClassReader.<init>` from
   `battlecode.instrumenter.TeamClassLoaderFactory.normalReader:233` (via
   `MethodCostUtil.getMethodData:96`) on **every** player class load; every robot dies as it spawns,
   **no robot is ever built**, and — measured — the game ends at **round 1** with
   `winner=A dom=ANNIHILATION` after 6 trace lines, and the job would exit 0. That is the exact
   "green oracle proving nothing" trap, and it is why item 3 below exists.
2. **Compile with plain `javac -nowarn -encoding UTF-8 -cp <jar>` and NO `--release`, no `-source`,
   no `-target`.** `--release` arrived in JDK 9 and dies with "invalid flag" on a JDK-8 `javac` in
   seconds — the bc21 lesson, and this job is JDK 8, so the flag must be absent rather than set to 8.
   The compiler *is* 8, so the target is 8.
3. **The driver must fail loudly when nothing happens, and it must call `System.exit()`.** Two
   requirements: (a) `tools/oracle/bc22/Bc22Trace.java` **exits 3 if no robot is ever built**, which
   is what catches item 1 (and `ci.yml` additionally asserts every game reached at least **1 900
   rounds** and carried at least **60 robots** at its peak); (b) the sandboxed player threads are
   **non-daemon**, so a driver that returns or throws without `System.exit()` hangs forever. Every
   `java` invocation in the job is wrapped in `timeout 600`.
4. Download the jar and **verify its sha256 and size** against `jar.lock`, **and assert
   `GameConstants.SPEC_VERSION == "2.2.1"`** — measured, and unlike bc23's and bc25's jars this one
   really does report its own version, so the version string is a *second* pin rather than a trap.
   Tier B cross-checks every constant anyway.
5. Run `java -Xmx2g -XX:+UseSerialGC -cp battlecode22-2.2.1.jar:classes battlecode.world.Bc22Trace
   <map> <rounds> <pkgA> <classesDirA> [<pkgB> <classesDirB>]`. The driver is
   `package battlecode.world;` so it needs reflection only for `ObjectInfo.dynamicBodyExecOrder`
   (private — the only way to print in exec order) and `GameWorld.lead` / `gold` / `rubble` (private —
   the only way to checksum the three map arrays). It loads the map with
   `GameMapIO.loadMapAsResource(loader, "battlecode/world/resources", map)` (**three** arguments in
   2022, not bc23's four), builds a `TeamControlProvider` over two `PlayerControlProvider`s (**the
   player URL must be the compiled classes directory** — an empty URL fails class loading),
   constructs `new GameMaker(info, null, false)` (the null packet sink is supported) and calls
   `GameWorld.runRound()` in a loop, printing the trace **from the live objects**, with the players'
   own `System.out` diverted into a discarded stream so the example bot's per-turn `println` cannot
   interleave with the trace. **No flatbuffers reader, no `flatc`, no `pip install` on either side**,
   and the engine is used exactly as published.

**The trace.** One line per record; `tools/parity_trace_bc22.nim` prints the same lines from the Nim
port:

```
R <round> T <A|B> pb=<n> au=<n> ar=<n> la=<n> wa=<n> mi=<n> bu=<n> so=<n> sa=<n>
R <round> G leadchk=<fnv1a64> goldchk=<fnv1a64> rubblechk=<fnv1a64> leadsum=<n> goldsum=<n>
R <round> U <id> team=<A|B> ty=<TYPE> md=<MODE> lv=<n> x=<n> y=<n> hp=<n> acd=<n> mcd=<n> bc=<n>
R <round> S <A|B> arr=<fnv1a64 of the 64-slot shared array>
R <round> H hashord=<fnv1a64 of the ids in robotsArray() order>
R <round> A next=<idx> type=<ABYSS|CHARGE|FURY|VORTEX|-> round=<n>
R <round> Z winner=<A|B|-> dom=<NAME|->
```

Robots are printed **in exec order**, not id order, which is what makes an ordering bug visible; the
`H` line is what makes a **trove-order** bug visible (D2) and it is compared **every round**, not only
on charge rounds; the three map checksums are what make a single wrong square visible without printing
3 600 squares a round, and `rubblechk` is what proves a VORTEX permuted the right way (**measured**:
on `charge`, `rubblechk` changes exactly once, at round 1000, and never again). The Java side's `bc=`
column is **stripped from both sides identically** before the diff and is used only for the Tier A
headroom assertion. **Measured in this sandbox** (the `T`, `G`, `U`, `S` and `Z` lines exactly as
above; `H` and `A` are the shipped driver's additions): a full 2000-round game is
**180 177–280 518 trace lines (17.9 MB on `maze`)** and **16.4–27.4 s of JVM** per map, and the board
carries **108–204 robots** at its peak on the parity maps (**349** on 60×60 `vortex`), mean 85–135.
So eight pairs cost roughly three minutes of engine time and ~150 MB of temporary trace. Traces are
written to `$RUNNER_TEMP`, compared **streaming** (never loaded whole), and only the first 200
divergent lines plus a gzipped digest are uploaded.

**`tools/ci/parity_tiers_bc22.py` is bc23's script with all three known comparator bugs fixed, and it
fixes the three sibling scripts in the same commit** (LEARNINGS 2026-09-08 asks for exactly that):

1. **`bc=` is stripped from BOTH traces** by one `normalize()` applied to each side. bc23's script
   already does this; `parity_tiers_bc21.py`, `_bc24.py` and `_bc25.py` do not, which made every pair
   "diverge" at round 1 on otherwise-identical lines.
2. **`itertools.zip_longest`, never `zip`.** `zip` stops at the shorter file and **discards the
   tail**, so a Java trace one line longer than the Nim trace reads bit-exact. The comparator's own
   self-test constructs exactly that pair and asserts the comparator reports a divergence.
3. **Hex folds are canonicalised on both sides.** Java's `Long.toHexString` emits lowercase with **no
   leading zeros** and, for a negative long, the unsigned 64-bit form; Nim's `toHex` zero-pads to 16.
   `normalize()` re-parses the value of every **named checksum field** — an explicit allowlist
   (`leadchk`, `goldchk`, `rubblechk`, `arr`, `hashord`) — as an unsigned 64-bit integer and re-emits
   it canonically, so neither emitter's formatting can create or hide a divergence. Decimal fields
   (`x`, `y`, `hp`, …) are untouched, which is why the allowlist is explicit rather than a regex over
   anything hex-shaped.

**The tiers — pinned to what this harness can actually deliver, which was measured, not hoped.**

- **Tier A (BLOCKING) — rounds 1…2000 bit-exact, whole games, on eight pairs**
  (`chalice`, `maze`, `nottestsmall`, `snowflake_redux`, `rugged`, `charge`, `turtle`, `vortex` —
  chosen in §Sim module to cover all four `causeVortexGlobal` arms, all four anomaly bodies, archon
  counts 1–4, all three symmetries and one map with **no** anomaly schedule as a control),
  `examplefuncsplayer22` against itself, every field above **including `H hashord`**. This is a
  *whole-game* window for one measured reason: the 2022 example bot **never approaches its bytecode
  limit** — peak use across eight full 2000-round games was **680–760, i.e. 6–7 % of the 10 000 limit,
  always a MINER** — with **zero** mid-turn cut-offs — so the port's "no mid-turn resumption"
  divergence is never exercised and the comparison stays defined to the last round. The job does not
  assume that: it reads the `bc=` column and **fails if any robot on any round exceeds 50 % of its
  type's limit**, naming the round and the robot, because past that point the window would have to
  shrink and this note would rather be wrong loudly than green quietly. (This is exactly where bc21
  could not go: its example bot *did* hit the ceiling, which is why its windows were 22–245 rounds.)
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact.** Tier A's own measurement showed
  exactly what it cannot cover. Over eight full 2000-round games the example bot **never built a
  builder, a sage, a laboratory or a watchtower, never mutated, never transformed, never transmuted,
  never envisioned, never wrote the shared array, never made a single gold, and ended EVERY game at
  round 2000 on `MORE_LEAD_NET_WORTH` with gold 0–0** — so the whole building, mutation, gold, sage
  and anomaly-response half of the rule set, and both of the ladder's upper rungs, and `ANNIHILATION`
  itself, are untested by it. Those are precisely the "rare code paths that fire mid-game" the Fleet
  card 1218171523823317 postmortem warns about — except that here they are most of the game. So this
  job runs a **second oracle bot of our own**, `tools/oracle/bc22/bc22scenario/RobotPlayer.java`,
  written to be (a) deterministic with **no RNG at all**, (b) cheap — the job asserts it never exceeds
  **25 %** of its bytecode limit, so it can never be cut off mid-turn — and (c) **scripted by round
  number to force every rare path early**: build a builder; build a laboratory prototype and repair it
  through all ten repairs to a turret; transmute at three different loneliness values and prove the
  rate; build a watchtower and repair it through all fifteen; mutate a laboratory to level 2 with lead
  and to level 3 with gold, and an archon to level 2, and prove the health jump and the 100+100 freeze;
  transform an archon to PORTABLE, move it two squares, transform back, and prove exactly one counter
  was charged each time; envision each of ABYSS, CHARGE and FURY with a sage and prove the three
  radii and truncations; write and read the shared array from a robot with nothing nearby (legal in
  this year, illegal in 2023); mine one square to zero and another to exactly 1, and prove at the next
  multiple of 20 that only the second regenerates; stand a watchtower in TURRET mode and another in
  PORTABLE mode through a scheduled FURY and prove 7 and 0; clump eight droids and scatter eight
  through a scheduled CHARGE; hold 250 lead through a scheduled ABYSS and prove the 25 lost; and
  disintegrate one robot. Two further variants force the ends:
  **`bc22scenarioannihilate`** walks soldiers onto the enemy's single archon on `chalice` until
  `ANNIHILATION` fires (and asserts the **20 Au** reclaim landed on the square), and
  **`bc22scenariotie`** mirrors both sides exactly so the ladder walks down to
  `MORE_LEAD_NET_WORTH` and, on one seed, to `WON_BY_DUBIOUS_REASONS`; a third,
  **`bc22scenariofury`**, arranges for a scheduled FURY to destroy the last archon of **both** teams
  so divergence 7's early gold/lead ladder fires. `scenario22.nim` is its Nim twin, written line for
  line against it, behind `-d:bc22Scenario` (+`-d:bc22ScenarioAnnihilate` / `-d:bc22ScenarioTie` /
  `-d:bc22ScenarioFury`). Both sides run all four variants on the eight pairs and must agree **bit for
  bit for the whole game**. The job then asserts, **off the JAVA trace**, that the paths really fired:
  a `U` line with `ty=LABORATORY md=PROTOTYPE` appears and later the same id with `md=TURRET`; a
  `U` line with `lv=2` and one with `lv=3`; a `U` line with `md=PORTABLE` and a later `x=`/`y=` change
  on that id; `au=` on a `T` line rises without any robot dying; `goldsum` rises after an archon dies;
  `rubblechk` changes on a vortex round and not otherwise; `arr=` changes; a `Z` line with
  `dom=ANNIHILATION`, one with `dom=MORE_LEAD_NET_WORTH` and one with `dom=WON_BY_DUBIOUS_REASONS`
  exist; and an `A` line's `next=` advances exactly once per scheduled round. **A scenario bot that
  agrees bit for bit while doing nothing proves nothing**, and this is the step that stops it. *(If the
  engine's own instrumentation makes any one of these scripted paths impossible to force
  deterministically, the failing item is dropped from the scenario bot and **added to
  `docs/PARITY.md` §What is NOT compared with the reason** — never silently left in a bot that does not
  reach it.)*
- **Tier B (BLOCKING) — the arithmetic, over its whole finite domain.** `tools/JavaBc22Tables.java`,
  run against the jar's own classes under the CI **JDK 8**, regenerates `data/bc22/tables.json` — the
  whole `RobotType` table (9 constructor fields × 7 types) with every per-level
  `getMaxHealth`/`getDamage`/`getHealing`/`getLeadMutateCost`/`getGoldMutateCost`/`getLeadWorth`/
  `getGoldWorth`/`getLeadDropped`/`getGoldDropped` value; the `AnomalyType` table; **the entire rubble
  cooldown lattice** `rubble 0…100 × base ∈ {2, 10, 16, 20, 24, 25, 100, 200}` computed as
  `(int)((1 + r/10.0) * c)` by the JVM itself (808 entries, of which the 22 that differ from the
  integer form are flagged in the file so a reviewer can see them); the prototype health
  `(int)(0.8f × hp)` for all nine building health values; the reclaim `(int)(worth × 0.2f)` for every
  reachable worth; the four anomaly truncations over their whole reachable domains — ABYSS
  `(int)(0.1f × m)` and `(int)(0.99f × m)` for `m` 0…20 000 (a square can accumulate reclaim without
  bound in principle; the whole of 0…1 000 plus a decade sample above it), CHARGE
  `(int)(0.05f × n)` for `n` 0…500, CHARGE-sage `(int)(0.22f × hp)` and FURY
  `(int)(hp × 0.05f)` / `× 0.1f` for all nine health values; and the **laboratory rate**
  `(int)(20.0 − 18.0 × Math.exp(−k × n))` for all `3 × 177` `(level, n)` pairs — and the job
  **byte-diffs** it against the committed file. bc22 has exactly **one** transcendental and its domain
  is finite, so this tier is not a sample: it is the entire domain.
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 2000-round game, on
  all five bots and all eight maps.** The job computes it per pair and compares it against
  `tools/ci/parity_ledger_bc22.json`, whose entries are
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
bytecode measurement says nothing in this harness forces a divergence. **The one place a divergence is
genuinely plausible is D2** — the trove iteration order — which is why the `H hashord` line is compared
every round rather than only on charge rounds: a trove bug will surface on round 1 as a checksum
mismatch, not on round 400 as a mystery. If phase 30 finds a divergence anyway, the budget for
root-causing it is stated here — the **root-cause checklist**, each item with its own unit test above,
so a Tier C failure bisects in minutes rather than becoming a card:

the trove `values()` order and the CHARGE stable sort (test 7); the exec-order list's by-value removal
and the pre-sweep snapshot (test 6); the float64 rubble multiplier and **where** it is read
(test 1); the anomaly ordering — passive `+2` before, map `+5` after (test 4); FURY's TURRET-only
truncation and its `checkArchonDeath = false` path (tests 4, 10); ABYSS's per-square floor and its
four-reserve order (test 4); the VORTEX permutation and the `Random(mapSeed)` stream (tests 4, 12);
the transform's single counter and the mutation's double one (test 5); the prototype health and the
repair-to-turret promotion (test 5); the `+5` regeneration's `> 0` predicate and the mined-dry set
(test 3); the laboratory rate table and the `n` it is computed from (tests 3, 8); the reclaim drop and
its stacking (test 2); the `ceil+1` scan box and `senseNearbyRobots`'s self-exclusion (test 8); the
Singularity's `get*Worth` sums (test 10); and the `IDGenerator` stream that fixes every built robot's
id (`tests/test_rng.nim`).

Tiers A, A′, B and C are the **phase-30 gate**. Every accepted divergence is listed in
`docs/RULES-BC22.md` §Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md`
gains a `bc22` section written in the same shape as the `bc23` one — including, honestly, the measured
numbers (peak bytecode %, cut-offs, trace line counts, JVM seconds, peak and mean robot counts, the
JDK-21 ASM trap, the non-daemon-thread hang, and the **51–58 % CHARGE tie rate** that forced the trove
port).

### `docker-smoke` job — now **seven** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely from
`certification.game_config.num_agents` and hard-fails with `SEAT-COUNT FAIL:` if the workflow's
`<SEATS>` = **2** disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes —
bad-token refusal, `/global` first frame on connect, `Ping → Pong` payload echo — against the real
image on the first episode):

1. **The bc26 certification-fixture episode**, unchanged → `dist/smoke/replay.json`.
2. **The bc20 episode**, unchanged → `dist/smoke/replay-bc20.json`.
3. **The bc21 episode**, unchanged → `dist/smoke/replay-bc21.json`.
4. **The bc24 episode**, unchanged → `dist/smoke/replay-bc24.json`.
5. **The bc25 episode**, unchanged → `dist/smoke/replay-bc25.json`.
6. **The bc23 episode**, unchanged → `dist/smoke/replay-bc23.json`.
7. **A bc22 episode**, new: `SMOKE_EXPECT_YEAR=bc22`, `SMOKE_PLAYER_IDS=awu,scaffold`,
   `SMOKE_CONTRACT_PROBE=0`, `SMOKE_REPLAY_OUT=dist/smoke/replay-bc22.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc22","pool":"small","seed":<the seed test 12 pins>,
   "gamesPerMatch":1,"maxRounds":700,"perGameBudgetSeconds":70,"matchBudgetSeconds":80,
   "connectTimeoutMs":15000}`. **700 rounds and not 400**, for two reasons that are both this year's:
   the default `lab_round` is 300 and a laboratory needs a builder commissioned, walked, placed and
   then **ten** repairs, so the window has to reach roughly round 400 for the strong chassis to
   actually make a gold — which is the one signature of this year the smoke asserts across the pair
   (below) — and the smallest map's **first anomaly is at round 200**, so 700 rounds guarantees at
   least one anomaly actually struck. 700 rounds also records ~25 s of playback, which outlasts the
   viewer smoke's 15 s soak (the ecos 2026-08-23 scar). The seed is pinned to draw
   `snowflake_redux` (20×20, two archons a side, 32 lead squares totalling 760, first anomaly at
   round 200), the liveliest small map, so the episode is fast and the map cannot drift.

All seven run one game container + two player containers on a shared network with `file://` artifact
URIs and **no** `ANTHROPIC_API_KEY`, so both seats take the scripted path and must still complete. All
seven assert: the game exits 0, **every player container exits 0**, `results.json` carries exactly the
expected key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`, and the
replay parses as **strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the right `year`,
and a non-empty `events` array. A step asserts all seven replays exist and report seven different
`year` values.

**The episode substance assertion (the LEARNINGS pin), in two parts.** The bc22 episode passes
`SMOKE_REQUIRE_STATS` — the **per-seat** floor, which the script already enforces for both seats —
with `{"units_built":15,"lead_mined":100,"damage_dealt":10}`. Those three are things *both* chassis do,
including the weak floor: the upstream example bot's archons build a miner or a soldier most turns from
round 1, its miners mine every adjacent square every turn (five times a turn on flat ground), and its
soldiers attack `enemies[0]`. **The signatures of the year are things only a seat playing well does** —
commissioning a builder, finishing a laboratory, making a gold, mutating a building, dodging an
anomaly (the example bot does **none** of those: measured, its builder, sage, laboratory and
watchtower branches are empty and it made 0 gold in all eight full games) — so asserting them
per-seat would be asserting that the weak floor is not weak. They are asserted **across the pair** by
one `jq` step in `ci.yml`, reading the **replay's** `result` block (not `dist/smoke/results.json`,
which every episode overwrites in turn — the bc24 fix):
`([.result.games[0].units_built[]] | add) >= 45`,
`([.result.games[0].lead_mined[]] | add) >= 300`,
`([.result.games[0].builders_built[]] | add) >= 1`,
`([.result.games[0].labs_built[]] | add) >= 1`,
`([.result.games[0].labs_finished[]] | add) >= 1`,
`([.result.games[0].transmutes[]] | add) >= 1` and
`([.result.games[0].anomaly_losses_charge[]] + [.result.games[0].anomaly_losses_fury_hp[]] + [.result.games[0].anomaly_losses_abyss_lead[]] | add) >= 1`.
Together they make an idle win machine-visible, which is exactly what the 2026-09-03 round-1
degenerate match lacked.

**And the floors are measured, not guessed.** The per-seat numbers above are a lower bound derived from
the Java example-bot mirror measured in this sandbox (which carries 85–135 robots alive per side on
average and mines continuously). Phase 20 runs the real bc22 smoke once, reads the actual per-seat
statistics out of `dist/smoke/replay-bc22.json`, and sets the committed floors at roughly half the weak
seat's measured value — **never above what a correct episode produces**, and, where that conflicts with
"never below this note's numbers", **the second constraint wins and the measurement goes inline in
`ci.yml`** (the bc23 r1-F22 ruling, restated here so the builder does not have to rediscover it: a
floor derived from whole 2000-round games is wrong for a 700-round smoke). **If the across-the-pair
`labs_finished >= 1` or `transmutes >= 1` assertion does not hold on the measured episode, the fix is
to raise the smoke's `maxRounds` until it does, or to pass
`SMOKE_EXTRA_ENV`-style doctrine overrides pulling `lab_round` to 150 — never to drop the
assertion**: an episode of this year in which nobody ever makes a gold is not this game being played.

### `wasm-viewer` job — the bundle is **executed**, against **all seven** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay>
--killfeed-overlap` in headless chromium (Playwright pinned 1.55.0) **once per replay** —
`replay.json`, `replay-bc20.json`, `replay-bc21.json` at `--timeout 90 --soak 10`, and
`replay-bc24.json`, `replay-bc25.json`, `replay-bc23.json` **and `replay-bc22.json`** at
**`--timeout 120 --soak 15`** for the pacing reason in §Viewer. Each run requires
`data-replay-loaded="true"` (or the bridge `ready` posted after it), three **differing**
clock/scorebug readouts at 0 % / 50 % / 100 %, continued advancement across the soak,
`scrub_selector == "#scrub"` (so a seek was really exercised and the `#viewpanel` zoom slider was not
clicked instead), `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line, **the new
`#endcard` no-overflow assertion at 1280×800** (§Viewer, endcard fix 2), no overlay covering more than
50 % of the board after the soak, and the `#killfeed`/stat-box overlap check at 360 px, 720 px and
1280 px at both FIT and 2× zoom. `--strict-text-bounds` stays deliberately dropped here because the
board is pannable and zoomable (`#viewpanel` is kept), which is the exact case the flag's own
documentation excludes; the `canvas_text` counts are still recorded in `viewer-smoke.json`, and the
separate `tools/ci/renderer_fixture.html` step — full-cap `notes` and `motto` on both seats at three
widths including **360 px**, in the page's own CSS extracted from `client/replay_broadcast.html` at run
time — runs through the same harness with `--strict-text-bounds`, because every CI replay is scripted
and carries no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a bc22 row.
`node tools/wasm_replay_smoke.cjs` is also run against the bc22 smoke replay **and** the committed
`tests/fixtures/replay-bc22.json`, so wasm32-only failures (int overflow traps, address-space
exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation of
  anything a cog sends. The 2022 engine exists only in the `parity-oracle-bc22` CI job, and only as
  the published jar. No Node in any runtime stage either — the only Node in this repository is the
  CI-only Playwright harness.
- **Full bytecode metering.** The 2 000/1 250/750/500-`DecisionOps` budget replaces it, with no
  mid-turn resumption and no mid-primitive cut. A Nim-level instrumenter is a compiler project and
  buys nothing the oracle does not already prove — and on this year's measurement the oracle never
  reaches 8 % of the boundary.
- **A cog-authored Java (or any) strategy class.** Doctrines are **JSON-sheet only**; there is no
  `javac`, no instrumenter `Verifier`, no compile-error round trip and no multi-attempt loop. Nothing
  in the schema is closed against a future sandboxed hook.
- **A bc22 certification fixture, and any new `player[]` entry.** Certification stays on bc26 and
  `player[]` stays at `awu` + `scaffold` — the cert fixture seats exactly `num_agents = 2` players, so
  a third `player[]` id fails the release with `players_missing` (LEARNINGS 2026-09-04). bc22 is proven
  by its own `docker-smoke` episode and the viewer smoke run against that episode's replay.
- **53 of the 75 official maps.** The converter handles any `.map22` and CI parses all 75; v1 commits
  the 22 whose geometry is pinned in this note. `maptestsmall` (an engine test fixture: rubble
  uniformly 1 and 49 788 lead) and `squer` (204 lead on 625 squares and no anomalies — a starvation
  map) are excluded on purpose, as is everything above 1 600 squares for the played pool.
- **The official 2022 TypeScript client and Electron visualizer, and `.map22`/replay flatbuffers in
  the browser.** Its *sprites* are reused (credited, AGPL-3.0 per `client/LICENSE`); its app is not
  shipped, not embedded and not built. There is no flatbuffers library on either side of this port —
  the map converter is a hand-written vtable walk — and no `match_b64` field exists.
- **Worker-side keyframe checkpoints in the viewer.** bc22 seeks re-simulate from the start of the
  game like every other year, which is why check 8 is dispatched with `settle=20000`. Keyframes remain
  the obvious next optimisation for the heavy year modules and are deliberately not in v1.
- **A cog-authored comms protocol.** The 64-slot shared-array layout is the chassis's; a doctrine
  cannot redefine it. In this year writes are free and unrestricted, so there is not even a
  write-window knob to expose.
- **A `sage_target` or per-anomaly envision knob.** `anomaly_play` decides *whether* the faction reads
  the schedule and acts on it; which of ABYSS/CHARGE/FURY a sage envisions when it has the action to
  spare is the chassis's call (nearest-value-first: FURY against a visible turret cluster, CHARGE
  against a visible droid clump, ABYSS otherwise). Exposing it as a twelfth knob would let a doctrine
  pick the value that does nothing on the board in front of it, which the anti-inert rule forbids.
- **Indicator strings, dots, lines, the profiler, and `.bc22` output of any kind.** They are
  instrumentation with no runtime meaning and no port.
- **The `net.sf.jsi` spatial index.** Written and never read by the engine (§Sim module, D5), so it has
  no port and no test beyond the assertion that no radius query consults one.
- **Per-robot fog in the viewer.** The spectator sees the true board, including squares no robot can
  see. This year has no occlusion mechanic at all, so the only thing hidden from a faction is distance
  — and the viewer does not simulate per-faction knowledge. (The enemy's shared array is likewise
  visible to a spectator and never to a robot.)
- **Rubble as a buildable or destroyable resource.** Rubble is fixed except by a VORTEX, which only
  permutes it; nothing in the rule set adds, removes or walks around it, and the port adds nothing.
  Likewise lead squares are never created except by the +5 regeneration and by reclaim drops, and gold
  never appears on the map except by reclaim.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the war.
- **Battlecode years other than 2020, 2021, 2022, 2023, 2024, 2025 and 2026.** The registry,
  `game_config.year`, the variant naming and `years/dispatch.nim` all support more; only these seven
  are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. The nine places where the
spec's prose and the engine disagree — the transform's single cooldown counter, the float64
truncating rubble multiplier, where that multiplier is read, the passive-lead-before /
map-regeneration-after ordering, CHARGE's combined population and its zero-under-twenty floor,
FURY's truncation and its TURRET-only reach, FURY's archon-check bypass, ABYSS's per-square floor,
and the sub-10 000 archon ids that fix the opening turn order — are all resolved **against the pinned
engine** in §The game and recorded as divergences from the prose, not as open questions. The two
places where the engine itself is odd — `resign()` being reachable through an API no doctrine can
call, and `MIN_RUBBLE = 0` while three official maps bottom out at 2 — are resolved in §The game and
`docs/RULES-BC22.md`. The idea's knob list is taken as given and finalised: all nine of its candidates
survive with exact types and ranges, and **two** are added from the chassis and the measurements —
`mine_floor`, because the map's `+5`-only-on-non-empty regeneration is the year's cheapest mistake and
the first-place bot has an explicit `mine_until` for it, and `lab_solitude`, because the transmutation
price is a function of company and the first-place bot gates on exactly `transmute_cost < 6`. The one
determinism question the idea does not raise and this note had to settle — whether to reproduce trove's
hash order or to substitute a deterministic tie-break — is settled in §Sim module D2 **by
measurement** (a tie straddles the CHARGE cut in 51–58 % of rounds, so a substitute tie-break would
diverge in nearly every game), not by preference.)*
