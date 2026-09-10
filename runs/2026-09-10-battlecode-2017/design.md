# cogame-battlecode — the `bc17` year module: Battlecode 2017 "Robotic Wildlife Fund" (design note, 2026-09-10)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a branch/PR of the shipped
repo that adds the year module `bc17` beside the shipped `bc16`, `bc19`, `bc20`, `bc21`, `bc22`, `bc23`, `bc24`, `bc25`
and `bc26`, adds the manifest variant `bc17`, keeps certification on `bc26`, and bumps the version of the *same*
coworld. **There is no `cogame-battlecode-2017` repo and none is created.** The starter is chosen by game shape and it
is the only defensible one: bc17 is the same shape as the nine shipped years — a deterministic Nim sim compiled twice
(native for the server, wasm for the viewer), one sealed JSON doctrine per seat, no engine and no foreign runtime in
the image, a static wasm replay viewer that re-derives every frame — and the year-module boundary
(`src/battlecode/years/<year>/`, `years/registry.nim`, `years/dispatch.nim`, `game_config.year`) already exists and has
now been proved **nine** times. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode` → this. The starter is
`Metta-AI/cogame-battlecode`, and **every convention there holds here unless this note says otherwise**: the Nim
sim/server/player layout, `nimby.lock`, the bitworld runtime contract, the `GameVersion` discipline,
`tools/build_replay_viewer.sh`, the `replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch doctrine layer
(`llm.nim` / `decide.nim` / `sheet.nim` / `sheet_common.nim` / `baselines.nim`), the closed results document, and
"degrade, never hang".

`bc17` is the **tenth** year module and **the only one whose world is continuous 2D float space with travelling
bullets**. It lands as `docs/plans/2026-09-10-battlecode-2017-design.md` on the branch `bc17-year-module`; the copy of
record for the run is `runs/2026-09-10-battlecode-2017/design.md`.

### Provenance — every rule and every number below was read or MEASURED in this sandbox, not assumed

**The rules were read from `github.com/battlecode/battlecode-server-2017` at commit
`165d8a8ef24f03e13a101bb8bc9f5b32dcb33c6c`** (`HEAD` of `master`, 2017-03-26, last commit *"Add GNU AGPLv3 License"*).
**Licence: the repository root `COPYING` is the GNU AFFERO GENERAL PUBLIC LICENSE v3 (34 520 bytes) and it is the ONLY
licence file anywhere in the tree** — verified by `find . -iname 'licen*' -o -iname 'copying*'`, one hit. That is the
**same licence this repository already carries**, so the combination needs no §13 argument at all.

Read whole: `world/{GameWorld,RobotControllerImpl,ObjectInfo,InternalRobot,InternalBullet,InternalTree,LiveMap,
GameMapIO,IDGenerator,TeamInfo,GameStats,DominationFactor}.java` (472 + 1 246 + 519 + 326 + 226 + 209 + 229 + 404
lines for the first eight), `world/control/*.java` (all four), `common/{GameConstants,RobotType,MapLocation,Direction,
Team,Clock,RobotInfo,TreeInfo,BulletInfo,BodyInfo}.java` (180 + 174 + 390 + 292 for the first four), and the relevant
half of `server/GameMaker.java`.

**The 1.6.2 spec page is reachable and was read**: `https://s3.amazonaws.com/battlecode-releases-2017/releases/
specs-1.6.2.html` — **HTTP 200, 44 154 bytes**, all 22 sections plus the changelog. Where it disagrees with the engine
the **engine wins**, and all **six** disagreements found are tabled in §The game.

**The oracle jar was downloaded and inspected here.**
`http://battlecode-maven.s3-website-us-east-1.amazonaws.com/org/battlecode/battlecode/2017.1.6.2/battlecode-2017.1.6.2.jar`
— **HTTP 200, 14 576 275 bytes, sha256 `9254e89268fd6efb72cafc037e3eded006aefd1d19aa44195c945b43ceb7bff9`**,
**10 210 entries**, **116 `battlecode/` classes**. `maven-metadata.xml` is also 200 (`<release>2017.1.6.2</release>`,
`lastUpdated 20170131002908`). **The published `.pom` carries NO `<dependencies>` element at all** — so the answer to
rail 2's question is settled from the artefact: **the jar is a FAT jar and needs no dependency list.** It bundles
`gnu/trove` (1 618 entries), `net/sf/jsi` (11), `kotlin/*` (≈ 380), `com/github/davidmoten` flatbuffers,
`org/objectweb/asm` (59 — the instrumenter), `org/apache/commons/{lang3,cli,io}` (381), `org/slf4j` (45),
`org/java_websocket` (68), `com/thoughtworks/xstream` (12), `org/mockito`/`junit`/`org/hamcrest` (shaded test deps),
**and all 70 `battlecode/world/resources/*.map17` map resources** — so the oracle job needs **no Gradle, no Maven
resolution, no `deps.lock`, no shim and no `--map-dir`**.

**The engine was RUN in this sandbox** (JDK 21, `NullControlProvider` on both teams — the instrumenter that needs JDK 8
is only required to load *player* classes), which is where most of the numbers below come from:

| measurement | how | result |
|---|---|---|
| all **70 official maps** parsed | `GameMapIO.loadMapAsResource` over `GameMapIO.getAvailableMaps(null)` | the table in §Sim module: sizes **30×30 … 100×100**, origins in **[2.85, 498.01]**, per-side archons **1, 2 or 3 and ALWAYS equal**, neutral trees **0 … 1 916**, tree radii **0.5 … 10.0**, `rounds` = **3000 on every one of the 70** |
| a whole game, end to end | `new GameWorld(...)` + `runRound()` to `DONE` on `Barrier`, `Conga`, `GiantForest` | **2 999 rounds played** (`timeLimitReached` is `currentRound >= rounds-1`), 86–91 ms with 4–6 robots, ended `WON_BY_DUBIOUS_REASONS` |
| the bullet economy | the same three runs, printing `getBulletSupply` at the end | **exactly `300.000000000` after 2 999 rounds.** `max(0, 2 − 0.01 × supply)` is **ZERO at any supply ≥ 200**, and both teams start at **300** — so the "2 bullets a round" trickle is *off from round 1* and the whole economy is trees (§The game, the income cliff) |
| `Math` vs `StrictMath` on the engine's own expressions | 20 000 000 random `(dx, dy)` in ±100 and the `radians` they produce | at **double** level `atan2` agrees **0/20 M** times differently (identical), while `sin` differs in **775 072** and `cos` in **655 750** samples; **after the `(float)` narrowing every engine expression agreed in 20 000 000 / 20 000 000 samples** — `(float)atan2`, `(float)sin`, `(float)cos`, `(float)sqrt`, `(float)(dist*cos)`, `(float)(dist*sin)`, `(float)toDegrees` — **0 disagreements** (§Sim module, F1–F4) |
| `gnu.trove.map.hash.TIntObjectHashMap` iteration | a probe on the jar's own shaded classes | fresh capacity **23**; `forEachValue` walks **high index → low** (ids 2,3,4,5 → `5 4 3 2`; ids 14,15,16,17,34,35 → `17 16 15 14 35 34`, which is exactly `id mod 23` descending and **matches the live engine's own `eachRobot` output**); **`clear()` RETAINS capacity** (397 → 397); and **a removal during `forEachValue` that triggers auto-compaction leaves the walk on the PRE-COMPACTION arrays** — 40 of 40 values visited while 20 were removed and the capacity shrank 97 → 67 |
| `gnu.trove.list.array.TIntArrayList` | the same probe | `insert(i, v)` inserts **before** index `i`; **`remove(int)` removes by VALUE**, not by index |
| `net.sf.jsi` `RTree.nearestN` | a probe with 200 random points and with five points at (near-)equal distance | **ascending distance order** (200/200 ascending, 0 exact ties); but for **exact ties the order is an artefact of the R-tree node layout and the priority queue's heapify** — the same five points gave `[13527, 11304, 10137, 12235]` and, after deleting and re-adding one of them, `[13527, 12235, 10137, 11304]` (§Sim module, D2) |
| `IDGenerator` | constructed from three map seeds | 4 096-id Fisher–Yates blocks from `MIN_ID = 10000`; seed 98 → `10001+`-range ids `13527, 10137, 10443, 12235, …`; the bullet generator (`setStart(32001)`) → `33728, 35734, 33147, …` |

**The three unlicensed 2017 repositories named in the idea were NOT cloned, NOT fetched, NOT read and contribute
nothing.** `benzyx/omega-ruby-battlecode`, `humford/Battlecode2017` and `SiestaGuru/Battlecode-2017---Bruteforcer` carry
**no licence**, so this run treats them as unreadable. **No line of any of them is copied, vendored, compiled,
translated, read or fetched.** The strong chassis is designed from the engine source, the 1.6.2 spec page and the four
archetypes the idea's own text names (tree farm; tank rush; lumberjack swarm; scout squat) — nothing else.

**Two upstreams that ARE licensed, and both are AGPL-3.0 — the same licence as this repository:**

- **`battlecode/battlecode-scaffold-2017`** at `76e7b51e06088fdcce2f6a6b97aff21782ae20d0` (2017-08-25). Root
  `LICENSE` = AGPL-3.0. It carries **`src/examplefuncsplayer/RobotPlayer.java` (278 lines)**, which this note reads in
  full and which becomes both the Tier A″ oracle bot and the deliberately weak scripted floor.
- **`battlecode/battlecode-client-17`** at `feb3e03820ba442ab233f05d2432b0dc2833aa98` (2017-03-26). Root `LICENSE` =
  AGPL-3.0. **Its `package.json` declares `"license": "GPL-3.0"`, which disagrees with the licence file; both are
  compatible with this repository's AGPL-3.0 and the discrepancy is recorded in `NOTICE` rather than papered over.**
  It carries the official 2017 sprite set: `src/static/img/sprites/{archon,gardener,soldier,tank,scout,lumberjack,
  bullet_tree,recruit}_{red,blue,neutral}.png` (32×32 for the small bodies, 50×50 for archon and tank, 24–25×24–25 for
  the neutral variants), `src/static/img/map/{sapling,full_health_tree,low_health_tree,tree_bullets,tree_robots}.png`
  (32×32) and `src/static/img/bullets/bullet_{slow,medium,fast}.png` (26/18/16). **So rail 7 resolves to "use the
  official set": the licence was checked, cited and covers it, and no nano-banana art is needed.**

Base-repo facts are from `Metta-AI/cogame-battlecode` at **`f057064`** (`main`, the merge of PR #17 — the bc19 year
module), whose shipped coworld version is **0.9.0** and whose `GameVersion` is **GV12**. Every `path:line` and constant
below is to those trees.

### Source idea (verbatim — the body of `runs/2026-09-10-battlecode-2017/idea.md`)

*(Fenced and verbatim, so its first line begins `## 36 Battlecode 2017 …` — the idea's own heading, **not** one of this note's nine H2 sections, which start at `## Feasibility verdict`.)*

```
## 36 Battlecode 2017 Robotic Wildlife Fund (mod of cogame-battlecode) — year variant bc17 + its own league

Asana: https://app.asana.com/1/1209016784099267/project/1217704774784096/task/1218173792280294

---

ARCHONS and GARDENERS plant bullet TREES; SOLDIERS, TANKS, SCOUTS and LUMBERJACKS fight in CONTINUOUS 2D space with travelling bullets; win by 1000 Victory Points (donate bullets) or annihilation, on 30x30 to 100x100 float maps. Tier 2 in the ranking: broad early (scout tree-squatting, tank rushes, lumberjack gas-cloud swarms, varied farm layouts) converging on soldiers after balance passes. FEASIBILITY FLAGS: this is the one continuous-space year — float ballistics, circle collisions and tree growth mean the parity oracle must match Java float semantics bit-for-bit (use float32 everywhere, replicate Math.sqrt/atan2 ordering, and gate Tier C on the maps where it holds); no competitor bot is licensed, so the chassis is written from the described strategies. Do this year last of the flagged ones.

Seats: 2 (one cog per side). num_agents = 2 in the bc17 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc17 (v1 candidates; the builder finalises them from the chassis it ports): opening {tree_farm | tank_rush | lumberjack_swarm | scout_squat}, gardener_count, farm_layout {hex | line | ring}, soldier_tank_ratio, vp_donate_policy {never | when_ahead | rush_1000}, scout_harass, shake_neutral_trees, bullet_reserve.
Rules, engine, oracle: Spec: https://s3.amazonaws.com/battlecode-releases-2017/releases/specs-1.6.2.html (200). Engine: https://github.com/battlecode/battlecode-server-2017 (Java 8 + Kotlin, Gradle 2.14.1; root COPYING AGPL-3.0). Oracle: Maven org.battlecode:battlecode:2017.1.6.2 at http://battlecode-maven.s3-website-us-east-1.amazonaws.com (metadata and jar 200, 14 MB); JDK 8.
Chassis and baselines (behaviour sources): benzyx/omega-ruby-battlecode (2nd; no licence), humford/Battlecode2017 (MIT Rejects Society, finalist; no licence), SiestaGuru/Battlecode-2017---Bruteforcer (finalist; no licence) — behaviour references only; E Doc Tablet not on GitHub.
Ranking: Tier 2 (mixed) in the ranking; flagged for continuous-space float parity + unlicensed bots.
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc17` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc17` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc17`, league_name `Battlecode 2017 — Robotic Wildlife Fund`, default_variant_id `bc17`, short_name `bc17` (softmax.com/battlecode/bc17), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### The seven coordinator rail decisions, and where each is discharged

**1.** host = `cogame-battlecode` itself; one year module + one `registry.nim` row + one arm per `dispatch.nim` `case`;
branch `bc17-year-module` → the title paragraph, §Sim module, §Packaging ("Branch discipline"). **2.** the pinned-jar
**JDK-8** oracle in a new `parity-oracle-bc17` job built on `parity-oracle-bc16` (`ci.yml:2700`), with `jar.lock`
(url + version + sha256 + bytes + jdk + note), `build_oracle.sh`, **the measured verdict that the jar is
self-contained**, and **no Java/JDK/Node in any image stage** → §Tests, §Packaging, §Out of scope. **3.**
continuous-space float parity decided per `Math.` call with engine `file:line` evidence, the tier structure and the
both-side normalisation → §Sim module F0–F5 and D1–D5, §Tests. **4.** bytecode metering → a fixed decision budget,
owed in **both** `docs/PARITY.md` and `docs/RULES-BC17.md`, numbers pinned, reachable/unreachable proved → §Sim module
V1, §Tests 13 and 20, Tier B′. **5.** no 2017 competitor bot licensed or read; the AGPL-3.0 scaffold player named as the
one exception → §Provenance, §Decisions, §Packaging. **6.** aliases stay `Clan Ash`/`Clan Basil` → §The game
("Seats"), §Viewer. **7.** sprite provenance verified before pinning, atlas `atlas_bc17`, exact list → §Provenance,
§Viewer ("Art"), §Packaging.

### Interface facts this note is written against (read from `f057064`, not assumed)

- **`GameVersion` is `GV12`** and `ReplayCompatibleGameVersions` is `["GV04" … "GV11", GameVersion]`
  (`src/battlecode/sim_types.nim:16` and `:253-254`). This run bumps to **`GV13`** and **EXTENDS** the list to
  `["GV04" … "GV12", GV13]`; it never resets it. `tools/ci/check_gameversion.sh` compares the *headline*, not the
  digits, so a sibling branch that takes GV13 first forces this branch to GV14 — expected and handled (§Packaging).
  **Consequence, stated because phase 20 owns it: any committed replay fixture whose `game_version` is `GV12` —
  `tests/fixtures/replay-bc19.json` and every other `tests/fixtures/replay-*.json` regenerated since the last bump —
  must be REGENERATED by phase 20 in the same commit as the bump**, by re-running the year's
  `tools/gen_bcNN_fixture_replay.nim`; a fixture stamped with a version this build no longer emits fails
  `tests/test_viewer.nim` and the wasm smoke.
- **`config_schema.maxRounds` is already `{minimum: 50, maximum: 3000}`.** bc17's `maxRounds` is **3000** (the engine's
  own `GameConstants.GAME_DEFAULT_ROUNDS`, which is what `LiveMap.rounds` is set to for **all 70 maps**), so **no
  schema bound has to move.** Every other bound already contains bc17's values: `gamesPerMatch ≤ 3` (bc17 uses 3),
  `perGameBudgetSeconds ≤ 300` (**120**), `matchBudgetSeconds ≤ 600` (**330**), the four millisecond bounds unchanged,
  `num_agents {minimum: 2, maximum: 2}` unchanged, `pool.enum` unchanged. **Every manifest edit in this run is
  additive.**
- **`AliasA`/`AliasB` are `"Clan Ash"`/`"Clan Basil"`** (`sim_types.nim:246-247`), shared by all nine shipped years.
  **This run does not touch them** (rail 6).
- **`EndReason` in `sim_types.nim` is bc26-only** and `GameOutcome.endReason` is a `string`; bc17 carries its own
  end-reason strings like every other year, so no year-neutral enum is touched.
- **`results_schema.games[].end_reason`'s enum already has 40 values**, including **`highest_id`** (bc20's) and
  `abandoned`; bc17 **reuses those two** and adds exactly **five** (§Packaging).
  `results_schema.games[].items.properties` already has 324 keys, and bc17 **reuses** `units_built`, `units_alive`,
  `units_lost`, `attacks`, `damage_dealt`, `kills` and `robots_lost` rather than duplicating them.
- **`sheet.nim`'s envelope resolver is year-neutral and already correct** (`sheet.nim:108-159`): resolution order `""`
  → `"sheet"` → `"doctrine"` → the single object-valued key, at most **one** unwrap, recorded in `Sheet.envelope`, and
  `results_schema.required` already declares `sheet_envelope`. **bc17 needs no year-neutral change here** — only its
  own arm (`sheet.nim:48,73-82,85,97,195,214-223,226-237` are where the bc19 arms sit) and the absent-key counting
  inside its own `knobs.nim`.
- **`ScriptedChassis`** (`sim_types.nim:263-281`, eighteen values) and **`Baseline`** (`baselines.nim:19-37`, eighteen
  values) each gain **two**, plus one arm each in `defaultBaselineFor` (`:39-51`), `baselineFor` (`:53-103`),
  `baselineChassis` and `baselineReply`. All additive. **Neither `orchard` nor `examplefuncsplayer17` collides with any
  of the eighteen existing strings** — checked, and `tests/test_baselines.nim` asserts uniqueness.
- **`src/battlecode/rng.nim` already ports `java.util.Random` and `IDGenerator`**, which is **the whole of the 2017
  engine's randomness** (D3) — needed twice, from the same map seed. `rng.nim` is **unchanged**. **bc22's
  `years/bc22/trove.nim` is NOT reused**, for the reason in D1.
- **`src/battlecode/fdlibm.nim` exists and already ports `StrictMath.exp` bit for bit** (`fdlibmExp`, added by bc16).
  **bc17 extends it with `fdlibmSin`, `fdlibmCos`, `fdlibmAtan`, `fdlibmAtan2` and the `__ieee754_rem_pio2` argument
  reduction** — the first time this repository needs a transcendental on a *runtime* path (§Sim module, F1).
- **`winBonusFor` at `match.nim:674` pays 200 for `{yBc25, yBc23, yBc22, yBc16, yBc19}`**; bc17 joins that set, for
  the reason in §The game ("Scoring"). **`match.nim:638`'s `perGame = max(1, min(field, remaining))`** is the
  zeroed-budget trap every bc17 test avoids (§Tests, conventions).
- **The viewer hooks bc17 extends are all already there and all already nine-way**: `beatsFor`
  (`src/battlecode/broadcast.nim:156`, five year discriminators at `:164-168`), `relayout()`'s `--statrail` id set
  (`client/replay_broadcast.html:7735-7738`, seventeen ids), `#killfeed`'s `bottom` (`:1270`), the `data-year` endcard
  noun table (`:7578-7605`) and the visibility guards (`:7887`, `:7899`). **bc17's job is to keep those fixes armed,
  not to re-fix them** (§Viewer).
- **The CI tooling needs no change at all.** `tools/ci/viewer_smoke.mjs` already carries the scrub-selector fix and
  `ci.yml` already asserts `scrub_selector == "#scrub"` per replay (and `canvas_text.total: 0` on this renderer covers
  nothing and **is not read as a pass** — LEARNINGS 2026-09-08); `tools/ci/docker_smoke.sh` already carries every env
  switch bc17 needs (`SMOKE_EXPECT_YEAR`, `SMOKE_PLAYER_IDS`, `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`,
  `SMOKE_CONTRACT_PROBE`, `SMOKE_SEATS`, `SMOKE_REQUIRE_STATS`, `SMOKE_EXTRA_ENV`), takes the seat count **solely**
  from `certification.game_config.num_agents` (`:141-190`) and refuses a `SMOKE_CONFIG_OVERRIDE` that changes it
  (`:199-201`); and **`replay-viewer/config.nims` needs no edit** because `--preload-file {rootDir}/data@data` already
  carries the whole `data/` tree. The only workflow numbers that move are the `test` job's `timeout-minutes`
  (**150 → 180**: bc17's shards are the heaviest in the repo and every file runs twice) and the new job's own.
- **This repo records `result` (singular) in the replay**, and a best-of-three episode legitimately plays **fewer**
  games than `gamesPerMatch` when a side clinches, with `reason` still `complete` (LEARNINGS 2026-09-07).
  **`tools/ci/policies.json` is repo-wide with 36 entries** (4 × 9 years); bc17 adds 4 (§Packaging).

### Design pins (`playbooks/make-coworld.md` §Phase 0, line 109) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as the nine shipped years (a real-time loop whose rules are written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, ten generations on, and the playbook's own ruling that a *continuous-physics* game takes paintbot rather than moba (2026-08-22) points at exactly this row. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. **No new repo** (the idea's HOW paragraph, rail 1). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=orchard\|examplefuncsplayer17` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc17/` — to wasm; the browser re-derives every round from events + config + seed. **No `.bc17` flatbuffer bytes anywhere.** |
| Real art, starter chrome verbatim | The official 2017 client's own sprites cut into `data/atlas_bc17.*` (AGPL-3.0, credited in `NOTICE`); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc17 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash** / **Clan Basil** (`sim_types.nim:246-247`, year-neutral); real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **435 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26\|bc20\|bc21\|bc22\|bc23\|bc24\|bc25\|bc16\|bc19].game_config` (all unchanged) and `variants[bc17].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level. |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc17 policy set is in §Packaging. |
| Both champions are LLM prompt policies, #1 owned by daveey and #2 by daveey-1; fillers are the scripted baselines, normally 2 | §Packaging (`tools/ci/policies.json`, "The phase-50 plan"). |
| Watchability: legible to a casual spectator, checked at **360 px** | §Viewer. The headline readout is the **race to 1000 Victory Points**, which is the one number this year is about. |

---

## Feasibility verdict

**Every load-bearing 2017 rule is fully determined by the engine source, the float-parity question of rail 3 has a
determinate answer that this note settles with 20 000 000 measured samples, the jar and the spec page are both
reachable and both AGPL-3.0, the sprite set is licensed under the same licence as this repository, and there is no
`OPEN` section in this note.** The idea's two feasibility flags both resolve, and the first one — the one it calls the
hard one — resolves **better** than the idea expected.

| Flag from the idea | Verdict |
|---|---|
| "float ballistics, circle collisions and tree growth mean the parity oracle must match Java float semantics bit-for-bit (use float32 everywhere, replicate `Math.sqrt`/`atan2` ordering, and gate Tier C on the maps where it holds)" | **Resolved, and Tier C does NOT have to be gated on a subset of maps.** Three measured facts make float parity *achievable by construction* rather than by luck. (i) **Every gameplay class is `strictfp`** — `GameWorld`, `ObjectInfo`, `InternalRobot`, `InternalTree`, `InternalBullet`, `RobotControllerImpl`, `LiveMap`, `GameMapIO`, `MapLocation`, `Direction`, `RobotController` (11 declarations, `grep -rn strictfp`), so there is no x87 extended-precision path to reproduce and IEEE-754 add/sub/mul/div/compare are exactly specified in both float32 and float64. (ii) **There are exactly 26 `Math.` call sites in the whole gameplay tree and only FOUR distinct non-algebraic functions among them — `sqrt`, `atan2`, `sin`, `cos`.** There is **no `Math.pow`, no `Math.exp`, no `Math.log`, no `Math.hypot` and — outside the instrumenter — no `Math.random` anywhere** (`grep -rn 'Math\.random\|Math\.hypot\|Math\.pow\|Math\.exp\|Math\.log\|StrictMath'` over `battlecode/{common,world,util,server}` returns **nothing**). (iii) **Every one of those four is narrowed to `float` at its own call site**, and the narrowing provably absorbs the only difference between `Math` and `StrictMath`: measured over 20 000 000 samples of the engine's own argument domains, `Math.sin` and `Math.cos` differ from `StrictMath` at double level in 3.9 % and 3.3 % of samples and **agree in 20 000 000 / 20 000 000 after the `(float)` cast**, while `Math.atan2` is bit-identical to `StrictMath.atan2` even before it. So the port evaluates the **fdlibm/`StrictMath`** algorithm in Nim, and the oracle is patched at its **nine** transcendental call sites from `Math.` to `StrictMath.` — a normalisation the measurement proves is observationally neutral on the published engine, applied on the ENGINE side so neither trace is massaged alone. §Sim module F1–F5 gives the per-call classification; **every call is (a) exactly specified or (b) fdlibm-ported-and-pinned, and NOT ONE is (c) irreproducible.** |
| "no competitor bot is licensed, so the chassis is written from the described strategies" | **Resolved, and the weak floor is licensed after all.** No 2017 competitor bot carries a licence, so the strong chassis (`orchard`) is designed from the engine's own mechanics and the four archetypes the idea names, and none of the three named repositories is read. But **`battlecode/battlecode-scaffold-2017` is AGPL-3.0** and carries a real 278-line `examplefuncsplayer` that hires gardeners, builds soldiers and lumberjacks, fires at the nearest enemy, strikes, chases and moves with a 7-direction obstacle probe — so the deliberately weak baseline and the differential oracle's other side are a **port of a licensed bot**, not an invention. |

Three things that could have been ambiguous and are not. **Turn order**: `ObjectInfo.dynamicBodyExecOrder`
(`ObjectInfo.java:42`) is a plain `TIntArrayList` — robots **appended on spawn** (`:254`), a bullet **inserted
immediately before its parent's index** (`:268-269`), removal **by value** (`:311`, `:320`, measured), and
`eachDynamicBodyByExecOrder` **snapshotting with `toArray()` before iterating** and skipping any id that no longer
exists (`:132-155`) — with no hash map, no sort and no priority queue in that path (measured on three maps: the exec
order after 2 999 rounds is exactly the initial bodies' id-sorted order). **The end ladder**:
`GameWorld.processEndOfRound` (`:251-327`) is one straight-line four-rung ladder with **no RNG on any branch and no
coin flip anywhere in the year**, plus two immediate conditions that fire mid-round (`setWinnerIfVictoryPoints`
`:239-245` from `donate`, `setWinnerIfDestruction` `:231-237` from every `destroyRobot`). **The economy, and it is the
year's biggest surprise**: `max(0, 2 − 0.01 × supply)` (`:264-267`) is **zero at any supply ≥ 200** and both teams
**start at 300** — measured, a 2 999-round game with no player action ends with **exactly 300.000000000 bullets on
both sides**. The idea's phrase "bullet income per round" describes a mechanic that is *switched off* for anyone
holding 200 bullets; the entire economy is trees, and *spending below 200* is what turns the trickle on. That fact
drives `bullet_reserve`'s default and both champion prompts.

**One rule is deliberately NOT ported and is therefore a decided divergence, not an ambiguity**: the per-robot
**bytecode limit with mid-computation resume** (`InternalRobot.getBytecodeLimit`, `:293-295`;
`PlayerControlProvider.runRobot`, `:129-140`). It is replaced by a fixed `DecisionOps` budget whose numbers are pinned
in §Sim module V1, whose cap is **provably non-binding for `orchard`** and whose *engine-side* counterpart is proved
never to have fired in any compared game by Tier B′. Two smaller ones (V2, V3) are the flatbuffer writer and the
R-tree tie order, both argued in §Sim module.

**BUILDABLE.**

---

## The game

**Battlecode 2017 "Robotic Wildlife Fund", played by doctrine, simulated in Nim.** Two cogs each command a faction of
robots in a **continuous, rectangular, float-coordinate arena** between **30×30 and 100×100**, whose origin is a random
offset in `[0, 500]²` and whose bodies are **circles**, not grid cells. Neither cog moves a robot. At t=0 each writes a
**doctrine** — a JSON sheet of eleven named knobs — and the deterministic sim plays the whole match from those two
sheets while both cogs watch.

Each faction starts with **1 to 3 ARCHONS** pre-placed on the map (always equal counts — measured across all 70 maps)
and **300 BULLETS**. An ARCHON (400 HP, radius 2, cannot be built, cannot shoot) hires **GARDENERS** for 100 bullets;
a GARDENER (40 HP, radius 1) is the only unit that can **plant a bullet TREE** (50 bullets, radius 1, 10 HP rising to
50) and the only unit that can **water** one (+5 HP/turn, one tree per turn), and it builds all four fighting types:
**SOLDIER** (100 bullets, 50 HP, bullet speed 2, 2 damage a bullet), **TANK** (300, 200 HP, speed 4, **5 damage**, and
it damages a tree by trying to walk over it), **SCOUT** (80, **10 HP**, speed 1.5, **0.5 damage**, stride **1.25** —
the fastest thing in the game and **the only body that may overlap a tree**) and **LUMBERJACK** (100, 50 HP, no
bullets at all, `chop` for **5** damage to one tree and `strike` for **2** damage to *everything* within distance 2 of
its centre **with no team check**).

**Bullets are the only resource, and there are only three ways to get one.** (1) **Trees.** A mature bullet tree pays
`health × 0.02` bullets a round — **1 bullet a round at full health** — and withers 0.5 HP a round unless a gardener
waters it. (2) **Shaking neutral trees.** The map's neutral trees (radius 0.5–10, HP = 200 × radius) may contain
bullets, which **any** robot can take with `shake()` at distance 1; some contain a **robot**, which only a
LUMBERJACK's `chop()` can release — and it joins the chopping team. (3) **The trickle, which is switched off.**
`max(0, 2 − 0.01 × bulletSupply)` is **zero at any supply of 200 or more**, and both sides start at 300: **measured,
a 2 999-round game with no player action ends with exactly 300.000000000 bullets.** The trickle is a *poverty
subsidy*, not an income, and an order that spends down to 120 bullets is earning 0.8 a round from it.

**Winning is a purchase.** `donate(bullets)` converts bullets into **Victory Points** at `7.5 + (12.5/3000) × round`
bullets each — 7.5 on round 1, **19.996 on round 2 999** — and **1 000 VP wins the game the instant the donation
lands**. At the average price that is ≈ **13 750 bullets**, which is ≈ 40 mature trees paying for 344 rounds. So the
year's central tension is arithmetic: every bullet is either a tree, a soldier, or a slice of the win, and **the price
goes up every round you wait**.

**The other way to win is annihilation**: if **all** of one side's robots die (trees do not count), that side loses on
the spot. And if neither happens by round 2 999 the game is decided by a four-rung ladder — victory points, then
bullet-tree count, then bullets-plus-robot-cost, then highest robot id.

Five mechanics make this year its own game rather than a reskin, and all five are choices a doctrine can spend:
(1) **bullets TRAVEL and do not care whose they are** — a radius-zero point moving `speed` units a round in a straight
line, and **the first body its segment crosses**, tree or robot, **either team, including the robot that fired it**,
takes the damage (`InternalBullet.updateBullet:98-156`); a SOLDIER's bullet crosses 2 units a round, so a shot **can
be walked out of**, and nothing else in this repository has projectiles with flight time; (2) **a triad or a pentad is
a cone, not a burst** — three bullets at ±20° for 4, five at ±15° for 6, against 1 bullet for a single shot, so volume
beats aim against a clump and misses five times against one dodging scout (and SCOUTS may fire **only** singles);
(3) **the lumberjack's strike is indiscriminate** — 2 damage to every robot *and every tree* within distance 2 of its
centre **including its own side's gardeners and its own side's farm**, which is the "gas-cloud swarm" the idea names;
(4) **trees are terrain, and terrain is money** — no body except a SCOUT may overlap a tree, so a radius-10 neutral
tree is a 20-wide wall, and the same tree holds 2 000 HP of chopping and possibly a free robot (`Maniple` has **406
trees, every single one containing a robot**; `GreenHouse` 58 trees of which **56 hold bullets and all 58 hold a
robot**); and (5) **the board is a mirror and both sides know it** — `getInitialArchonLocations(team)` returns
**either** team's starting archons, sorted (`RobotControllerImpl.java:112-131`), and every map is symmetric by
reflection or rotation (measured over the 70: 33 rotational-only, 12 horizontal-only, 5 vertical-only, 19 satisfying
two and 1 none by the archon test), so there is no scouting problem for the *enemy base* — only for what is standing
in front of it.

**That is why this year is worth playing sealed.** The idea calls 2017 Tier 2 with a broad early meta — scout
tree-squatting, tank rushes, lumberjack swarms, varied farm layouts — converging on soldiers after the balance passes.
The doctrine sheet in §Decisions makes exactly those the `opening`, `farm_layout` and `soldier_tank_ratio` axes, and
then makes two things the 2017 meta never systematically spent — **the VP price curve** (`vp_donate_policy`) and **the
income cliff at 200 bullets** (`bullet_reserve`) — into choices with teeth.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. Those two aliases are the repo's
year-neutral `AliasA`/`AliasB` (`sim_types.nim:246-247`) and this run does **not** change them: renaming them would
change what every shipped year records. The 2017 flavour — the engine's own `Team.A`/`Team.B`, drawn red and blue by
the official client — is carried by the viewer chrome and the variant description, never by the alias constants. The
episode seed decides which slot takes engine-side **Team.A** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc19/maps.nim`).

**Motive: zero-sum.** One side wins a game and the other loses it; the cogs never exchange a byte and there is no
in-game channel between them at all — 2017 has no inter-team trade and the broadcast array is per-team
(`TeamInfo.teamSharedArrays[3][10000]`). The two name spaces follow: in-game the factions are the anonymous aliases
**Clan Ash** and **Clan Basil**, so a doctrine cannot be written against a known opponent, and the real player names
(`daveey`, `daveey-1`) exist only in `replay.names[]` / `results.names[]` and are drawn only by the spectator-side
viewer.

### Provenance and licensing, in one paragraph

**Every 2017 upstream is AGPL-3.0 — the same licence this repository already carries — so unlike the 2016, 2019 and
2020 sources there is no GPL↔AGPL §13 combination argument to make at all.** The **engine**
(`battlecode-server-2017@165d8a8e`, root `COPYING` = AGPL-3.0 and the only licence file in the tree) is the rules
source and is reproduced as an **independent Nim implementation written from reading it**, never as a translation of
copied files: no Java is vendored into `src/`, `src/battlecode/years/bc17/**` contains no Java, and the engine exists
only inside the `parity-oracle-bc17` CI job and `tools/convert_maps_bc17.py`. The **oracle jar**
(`org.battlecode:battlecode:2017.1.6.2`) is the same work, verified by sha256, byte size and `SPEC_VERSION`, and never
enters an image. The **scaffold** (`battlecode-scaffold-2017@76e7b51e`, AGPL-3.0) is the behaviour source for
`examplefuncsplayer17` and for two named helpers of `orchard`. The **client** (`battlecode-client-17@feb3e038`,
AGPL-3.0) is the source of `data/atlas_bc17.*` and of nothing else. **The three unlicensed competitor repositories
were not cloned, not read and contribute nothing.** `years/bc17/constants.nim` is *generated* from the jar's own
classes and byte-diffed in CI, so the constant table is provably the engine's and provably not hand-typed. §Packaging
("Licensing") gives the exact `NOTICE` paragraphs, file by file.

### Constants — generated from the jar's own `GameConstants` and `RobotType`

Emitted into `src/battlecode/years/bc17/constants.nim` by `tools/gen_year_constants.py --year bc17`, never hand-typed,
regenerated and byte-diffed in CI (§Tests 29, Tier B). **Every value below is `float32` unless marked an integer.**

| constant | value | constant | value |
|---|---|---|---|
| `SPEC_VERSION` | **`"1.0"`** (int-free string; the third jar pin) | `GAME_DEFAULT_ROUNDS` | **3000** (int) — and `LiveMap.rounds` is set to it for **all 70 maps**, ignoring the map file (docs disagreement 1) |
| `MAP_MIN_WIDTH`/`HEIGHT` | **30** (int) | `MAP_MAX_WIDTH`/`HEIGHT` | **100** (int) |
| `VICTORY_POINTS_TO_WIN` | **1000** (int) | `NUMBER_OF_ARCHONS_MAX` | **3** (int) |
| `MAX_ROBOT_ID` | **32000** (int) | `BROADCAST_MAX_CHANNELS` | **10000** (int) |
| `BULLETS_INITIAL_AMOUNT` | **300** | `ARCHON_BULLET_INCOME` | **2** |
| `BULLET_INCOME_UNIT_PENALTY` | **0.01** — *per bullet held*, so income is **0 at supply ≥ 200** | `TEAM_MEMORY_LENGTH` | **32** (int, and not ported — V4) |
| `VP_BASE_COST` | **7.5** | `VP_INCREASE_PER_ROUND` | **12.5 / 3000** = `0.0041666666f` |
| `BULLET_TREE_MAX_HEALTH` | **50** | `BULLET_TREE_RADIUS` | **1** |
| `BULLET_TREE_COST` | **50** | `BULLET_TREE_DECAY_RATE` | **50/100** = **0.5** |
| `BULLET_TREE_BULLET_PRODUCTION_RATE` | **1/50** = **0.02** | `BULLET_TREE_CONSTRUCTION_COOLDOWN` | **10** (int) |
| `WATER_HEALTH_REGEN_RATE` | **50/10** = **5** | `PLANTED_UNIT_STARTING_HEALTH_FRACTION` | **0.2** |
| `NEUTRAL_TREE_MIN_RADIUS` | **0.5** | `NEUTRAL_TREE_MAX_RADIUS` | **10** |
| `NEUTRAL_TREE_HEALTH_RATE` | **200** (so HP = 200 × radius) | `LUMBERJACK_CHOP_DAMAGE` | **5** |
| `LUMBERJACK_STRIKE_RADIUS` | **2** | `TANK_BODY_DAMAGE` | **4** |
| `SINGLE_SHOT_COST` | **1** | `TRIAD_SHOT_COST` | **4** |
| `PENTAD_SHOT_COST` | **6** | `TRIAD_SPREAD_DEGREES` | **20** |
| `PENTAD_SPREAD_DEGREES` | **15** | `BULLET_SPAWN_OFFSET` | **0.05** |
| `GENERAL_SPAWN_OFFSET` | **0.01** | `INTERACTION_DIST_FROM_EDGE` | **1** |
| `MAX_ROBOT_RADIUS` | **2** | `EXCEPTION_BYTECODE_PENALTY` | **500** (int, not ported — V1) |

`RobotType` — the whole six-row table verbatim, **in `values()` order, which is load-bearing** (it is the ordinal on
the wire, the atlas index and the `Bc17UnitNames` index):

| # | unit | spawnSource | buildCooldown | maxHealth | bulletCost | bodyRadius | bulletSpeed | attackPower | sensorRadius | bulletSightRadius | strideRadius | bytecodeLimit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `ARCHON` | **null** | 0 | **400** | **−1** | **2** | −1 | **−1** | **10** | **15** | **0.5** | **30000** |
| 1 | `GARDENER` | ARCHON | **10** | **40** | **100** | **1** | −1 | **−1** | **7** | **10** | **0.5** | 15000 |
| 2 | `LUMBERJACK` | GARDENER | **10** | **50** | **100** | **1** | −1 | **2** | **7** | **10** | **0.75** | 15000 |
| 3 | `SOLDIER` | GARDENER | **10** | **50** | **100** | **1** | **2** | **2** | **7** | **10** | **0.8** | 15000 |
| 4 | `TANK` | GARDENER | **10** | **200** | **300** | **2** | **4** | **5** | **7** | **10** | **0.5** | 15000 |
| 5 | `SCOUT` | GARDENER | **10** | **10** | **80** | **1** | **1.5** | **0.5** | **14** | **20** | **1.25** | 15000 |

Derived predicates, ported from the engine's own expressions rather than from a table (`RobotType.java:113-158`):
`canAttack() = attackPower > 0` (so **ARCHON and GARDENER can never attack**, and the two `−1`s are why);
`canHire() = this == ARCHON`; `canBuild() = this == GARDENER`; `isHireable() = spawnSource == ARCHON` (GARDENER only);
`isBuildable() = spawnSource == GARDENER` (the four fighters); and
`getStartingHealth() = (ARCHON or GARDENER) ? maxHealth : 0.2f × maxHealth` — **so every fighter is born at 20 % health
and dormant, and a gardener is born whole and dormant for one round only.**
**`ARCHON.bulletCost` is `−1`, and that is a rule, not a sentinel:** tiebreak rung 3 sums
`robot.getType().bulletCost` over live robots (`GameWorld.java:302-304`), so **each surviving archon subtracts one
bullet from its own team's total** (docs disagreement 3). The port reproduces it and the score formula uses the
engine's exact expression.

### The 2017 rule set — exact numbered resolution rules, with every float width named

The sim's own step list. Re-ordering any of it is a rules change and bumps `GameVersion`. It mirrors
`GameWorld.runRound` (`:88-118`), `processBeginningOfRound` (`:208-224`), `updateDynamicBodies` (`:130-140`),
`updateRobot` (`:142-157`), `InternalBullet.updateBullet` (`:98-156`), `updateTrees` (`:120-128`),
`processEndOfRound` (`:251-327`) and `RobotControllerImpl` exactly. **Notation: `f32` = a float32 operation;
`f64→f32` = the expression is evaluated in float64 and narrowed at the cast the engine writes; `int` = integer.**

**1. `runRound` entry.** If `!running`, write the match footer and return `DONE` — **so a game that was decided in
   round R is not detected until the call for round R+1**, and every rule below still runs to the end of round R.
   Otherwise steps 2–9, and any exception anywhere in them is caught (`:110-113`) and ends the game with **no winner**
   (V5).

**2. `processBeginningOfRound`** (`:208-224`):
   1. **`currentRound += 1`** (int). Rounds are **1-based**; the first played round is 1 and the last is **2 999**
      (rule 9.4).
   2. **`previousBroadcasters = currentBroadcasters.values(new RobotInfo[size])`** — a trove `TIntObjectHashMap` walked
      **high slot → low slot** (**D1**), then **`currentBroadcasters.clear()`, which RETAINS the table's capacity**
      (measured). This array is what `senseBroadcastingRobotLocations()` hands a chassis, **for both teams**, so its
      order is observable to the chassis and therefore to the game.
   3. `eachRobot(processBeginningOfRound)` → `healthChanged = false`; `eachTree(processBeginningOfRound)` → the same.
      Both walk trove order; **neither has any state effect**, and this note says so explicitly so nobody ports an
      order that does not matter (`InternalRobot.java:246-248`, `InternalTree.java:178-180`).

**3. `updateDynamicBodies`** (`:130-140`) — **the exec order, and the whole of it**:
   1. `int[] snapshot = dynamicBodyExecOrder.toArray()` — **taken before the loop**, so bodies spawned during the
      round do **not** act this round and bodies destroyed during the round are silently skipped
      (`ObjectInfo.java:132-155`).
   2. For each id in the snapshot, in order: if it is a live **robot** → rule 4; else if it is a live **bullet** →
      rule 5; else skip.
   3. The list itself: robots **appended** on spawn (`:254`); a bullet **inserted at `indexOf(parent)`**, i.e.
      immediately **before** the robot that fired it (`:268-269`), so a bullet first moves on the round *after* it is
      fired and always just before its parent's next turn; removal is **by value** (measured).

**4. `updateRobot`** (`:142-157`), per robot:
   1. **`processBeginningOfTurn`** (`InternalRobot.java:250-263`): `attackCount = moveCount = repairCount =
      waterCount = shakeCount = 0` (int); `if buildCooldownTurns > 0: buildCooldownTurns -= 1` (int);
      **if `roundsAlive < 20 && type.isBuildable()`: `repairRobot(0.04f × maxHealth)`** →
      `health = min(health + heal, maxHealth)` (`f32`, then a redundant second clamp at `:221-223`);
      `currentBytecodeLimit = type.bytecodeLimit` (int, → V1).
   2. **`controlProvider.runRobot(robot)`** — the chassis runs and its actions take effect **immediately, in the order
      it emits them** (rule 6). **`getBytecodeLimit()` returns 0 unless `canExecuteCode()`**, which is
      `health > 0.0 && (type.isBuildable() ? roundsAlive >= 20 : true)` (`:281-287`) — **so a newly built fighter does
      nothing at all for its first 20 turns while healing 4 % a turn, and a gardener acts from its second round.**
      This is a *rule* and it is ported exactly; it is not the same thing as V1.
   3. `setBytecodesUsed(...)` (int, → V1).
   4. **If `health > 0`: `processEndOfTurn`** → `prevBytecodesUsed = bytecodesUsed`; **`roundsAlive += 1`**. A robot
      that died during its own turn does **not** increment `roundsAlive`.
   5. If the sandbox reports the robot terminated and it is still alive → `destroyRobot` (this is the `disintegrate()`
      path and the unhandled-exception path).

**5. `updateBullet`** (`InternalBullet.java:98-156`) — **the continuous-space core**:
   1. `bulletStart = location` (`f32`, `f32`).
   2. **`bulletFinish = bulletStart.add(dir, speed)`**: `dx = (f64→f32)(speed × cos(dir.radians))`,
      `dy = (f64→f32)(speed × sin(dir.radians))`, then `MapLocation(x + dx, y + dy)` (`f32` adds)
      — `MapLocation.java:276-278`. **Note the shape: the product is formed in float64 and narrowed once.**
   3. **`toFinish = bulletStart.directionTo(bulletFinish)`** — a **fresh** `Direction` from the *rounded* delta:
      `radians = reduce((f64→f32) atan2((double)dy, (double)dx))` where `dx = (f32)(x₂ − x₁)`. **This is not the
      bullet's own `dir`**; the two differ by float rounding, and the port must use this one.
   4. `distToFinish = bulletStart.distanceTo(bulletFinish)` = `(f64→f32) sqrt((double)(dx×dx + dy×dy))` with the two
      products and the sum in **`f32`** (`MapLocation.java:131-135`).
   5. `checkCenter = bulletStart.add(toFinish, distToFinish / 2)` — the division in `f32`, the add per step 2.
   6. **Tree candidates**: every tree with `tree.location.distanceTo(checkCenter) <= tree.radius + (10 +
      distToFinish/2)` (`ObjectInfo.java:328-349`, where the index is queried at `radius + 10` and then filtered by
      `isWithinDistance`), enumerated in **candidate order** (**D2**).
   7. For each: `hitDist = calcHitDist(...)` (rule 5.11). Keep it iff **`hitDist < hitTreeDist && hitDist >= 0`** —
      a **strict** minimum, so **an exact tie keeps the FIRST candidate in enumeration order** (D2).
   8. **Robot candidates**: every robot with `distanceTo(checkCenter) <= bodyRadius + (2 + distToFinish/2)`, same
      strict-minimum rule. **No team check and no exclusion of the firing robot**: a bullet hits its own side, and
      a robot that fires and then moves onto its own bullet is hit by it.
   9. **If nothing was hit**: `if (!gameMap.onTheMap(bulletFinish)) destroyBullet` else `setLocation(bulletFinish)`.
      `onTheMap(loc)` is a **point** test, **inclusive on all four edges**: `x >= ox && y >= oy && x <= ox+w &&
      y <= oy+h` (`LiveMap.java:152-154`).
   10. **Else**: `if (hitTreeDist < hitRobotDist && hitTree != null)` → destroy the bullet and
       `hitTree.damageTree(damage, team, fromChop = false)`; **else if `hitRobot != null`** → destroy the bullet and
       `hitRobot.damageRobot(damage)`. **A tree/robot tie at the same `hitDist` goes to the ROBOT** (the `<` fails).
       Exactly one body takes damage per bullet per round.
   11. **`calcHitDist(start, finish, targetCenter, targetRadius)`** (`:162-204`) — the segment/circle intersection,
       and every width matters:
       1. `maxDist = start.distanceTo(finish)`; `distToTarget = start.distanceTo(targetCenter)` (both `f64→f32` sqrt).
       2. `toFinish = start.directionTo(finish)`; `toTarget = start.directionTo(targetCenter)` (both atan2).
          **`directionTo` returns `null` when the two locations are `equals`** — and if `toTarget` is null the
          function **returns 0**, an immediate hit; if `toFinish` is null it **throws** (rule 1's catch, V5).
       3. `radiansBetween = toFinish.radiansBetween(toTarget)` = `reduce(toTarget.radians − toFinish.radians)`: the
          subtraction is `f32`, and `reduce` (`Direction.java:273-282`) compares against `(f32)π` and, when it wraps,
          computes `circles = (int) ceil(±(rads ∓ π) / (2π))` **in float64** and then adds `(f32)(π × 2 × circles)` to
          the `f32` value. Mixed widths, replicated per expression.
       4. **`perpDist = (f64→f32) |distToTarget × sin(radiansBetween)|`** — the product **in float64**, `Math.abs` on
          the double, narrowed once. `if (perpDist > targetRadius) return −1`.
       5. `halfChordDist = (f64→f32) sqrt((double)(targetRadius×targetRadius − perpDist×perpDist))` — the two products
          and the subtraction in **`f32`**, the sqrt in float64.
       6. **`hitDist = distToTarget × (f32) cos(radiansBetween)`** — **the cosine is narrowed FIRST and the multiply is
          `f32`**. This is a *different shape* from step 4 in the same function, and getting it wrong is the single
          easiest way to break bc17 parity.
       7. `if (hitDist < 0) { hitDist += halfChordDist; hitDist = hitDist >= 0 ? 0 : hitDist }` — a bullet already
          inside the circle hits at distance 0 — `else { hitDist -= halfChordDist; hitDist = hitDist < 0 ? 0 :
          hitDist }`. All `f32`.
       8. `if (hitDist < 0 || hitDist > maxDist) return −1;` else return `hitDist`.

**6. What a robot may do on its turn** (`RobotControllerImpl`), each applied **immediately**, each gated by a counter
   so it can happen at most once per turn — except `broadcast` and `donate`, which are unlimited:

| action | who | guards, in the engine's own order | effect |
|---|---|---|---|
| `move(dir[, dist])` / `move(center)` (`:554-607`) | any | refused if `moveCount > 0`. `dist = max(0, min(dist, strideRadius))` (`f32`); in the `MapLocation` form, if `distanceTo(center) > strideRadius` the target is **re-projected** as `location.add(location.directionTo(center), strideRadius)` — **an atan2 + sin/cos round trip, not a vector scale**. Then `canMove(center)`: `onTheMap(center, bodyRadius)`, which tests **only the four cardinal extreme points** (`LiveMap.java:175-180`), **and** emptiness — for **TANK and SCOUT** only `noRobotsExceptForRobot` (**they may overlap trees**), for everything else `isEmptyExceptForRobot` (no trees **and** no robots) | `incrementMoveCount()` fires **before** the tank branch, so **a body-attacking tank has spent its move**. TANK only: `trees = allTreesWithinRadius(center, 2)`; if non-empty, damage the tree with the **strictly smallest `tree.location.distanceTo(robot.getLocation())`** — the distance to the tank's **current** centre, not to `center` — by **4**, re-query, and **if any tree still overlaps, return without moving**. Otherwise `setLocation(center)` |
| `fireSingleShot` / `fireTriadShot` / `firePentadShot(dir)` (`:730-776`) | **not** ARCHON, GARDENER or LUMBERJACK; triad/pentad additionally **not SCOUT** | refused if `attackCount > 0`; `supply >= cost` (1 / 4 / 6, `f32` compare) | `incrementAttackCount()`; `−cost`; then `fireBulletSpread` (`:639-673`) spawning **in this exact order**: the **centre** bullet, then for `i = 1 … (toFire−1)/2` the **LEFT** at `rotateLeftDegrees(i × spread)` then the **RIGHT** — each at `location.add(thatDir, bodyRadius + 0.05f)` with the firer's `bulletSpeed` and `attackPower`. **That order fixes the bullet id sequence and the exec-order insertion**, so it is load-bearing |
| `spawnBullet` (`GameWorld.java:363-391`) | — | — | the bullet is recorded, then **a collision check at the muzzle** — `getRobotAtLocation(loc)` first, then `getTreeAtLocation(loc)` — and if either is occupied the bullet damages it and **never enters the world**. Both lookups return the **first** candidate in enumeration order (D2) |
| `strike()` (`:682-707`) | LUMBERJACK | refused if `attackCount > 0` | `incrementAttackCount()`; then **2 damage to every robot within distance 2 of its centre except itself**, and **2 damage to every tree within 2** — **no team check** on either. Enumeration order is **not** observable here (every candidate is damaged) |
| `chop(loc\|id)` (`:845-878`) | LUMBERJACK | refused if `attackCount > 0`; `location.distanceTo(tree.location) <= bodyRadius + tree.radius + 1` | `damageTree(5, team, fromChop = TRUE)` — and **`fromChop` is what releases the goodies** |
| `shake(loc\|id)` (`:890-913`) | **any** robot | refused if `shakeCount > 0`; the same interaction distance | `adjustBulletSupply(team, tree.containedBullets)` then `resetContainedBullets()`. Works on **any** tree, including a bullet tree (which holds 0) |
| `water(loc\|id)` (`:930-954`) | **GARDENER** | refused if `waterCount > 0`; the same interaction distance; **neutral trees refused** (`assertOwnedTree`) | `healTree(5)` → `health += 5` then clamp to `maxHealth` (`f32`). **The clamp is applied after the add, so watering a 48-HP tree wastes 3** |
| `hireGardener(dir)` (`:1108-1125`) | ARCHON | `supply >= 100`; `buildCooldownTurns == 0`; the circle `location.add(dir, bodyRadius + 0.01f + 1)` **on the map and empty of trees AND robots** | `setBuildCooldownTurns(10)`; `−100`; spawn. **The gardener is born at 40/40 HP** |
| `buildRobot(type, dir)` (`:1127-1144`) | GARDENER | the same shape with `type.bulletCost` and `type.bodyRadius` | `setBuildCooldownTurns(10)`; `−cost`; spawn. **The fighter is born at `0.2 × maxHealth` and dormant for 20 turns** (rule 4.2) |
| `plantTree(dir)` (`:1146-1165`) | GARDENER | `supply >= 50`; cooldown 0; the circle `add(dir, 1 + 0.01f + 1)` empty and on the map | `setBuildCooldownTurns(10)`; `−50`; the tree is born at **`0.2 × 50 = 10` HP** with `maxHealth = 50`. **A gardener's cooldown is SHARED between planting and building**, so a farm and an army compete for the same 10-turn slot |
| `broadcast(channel, data)` (`:993-998`) | **any** robot, **any number of times** | `0 <= channel < 10000` | `addBroadcaster(this.robot.getRobotInfo())` — into the trove map **keyed by robot id**, so repeats in one turn overwrite one entry; `teamSharedArrays[team][channel] = data` (int). **Free of bullets.** The broadcaster's **position** is revealed to **both** teams next round (rule 2.2) |
| `donate(bullets)` (`:1176-1184`) | **any** robot, **any number of times** | `bullets >= 0`; `supply >= bullets` | **`gained = (int) floor((double)(bullets / (7.5f + 0.0041666666f × roundNum)))`** — the price `f32`, the divide `f32`, the floor on the widened double; `−bullets` deducts the **whole** amount (the remainder is lost — the spec's "extra generosity"); `+gained` VP (int); **`setWinnerIfVictoryPoints()` immediately** (rule 8.1) |
| `disintegrate()` (`:1187-1189`) | any | — | throws `RobotDeathException` → rule 4.5. **`resign()`** exists (`:1191-1199`) and is **unreachable in this port** (V6) |

**7. Damage, healing and death**:
   1. `damageRobot(d)`: `health = max(health − d, 0)` (`f32`); then **`killRobotIfDead()` on an exact `health == 0`
      compare** → `destroyRobot`.
   2. `damageTree(d, hitBy, fromChop)`: `health −= d` (`f32`); clamp **negative to 0**; then `killTreeIfDead` on
      `health == 0` → `destroyTree(id, hitBy, fromChop)`.
   3. **`destroyTree`** (`GameWorld.java:397-431`): **only when `fromChop`** does it release goodies — the contained
      robot is spawned on the **chopping** team at the tree's centre (and **any SCOUT overlapping that circle is
      killed first**, the "falling debris" rule), and the contained bullets are credited to the chopper. **A tree that
      dies to a bullet, a strike, a tank body attack or its own decay releases nothing at all.**
   4. `destroyRobot` calls **`setWinnerIfDestruction()`** (rule 8.2) and removes the robot from the index, the id map
      and the exec order.

**8. The two immediate win conditions**, both of which fire **mid-round** and neither of which stops the round:
   1. **`setWinnerIfVictoryPoints`** (`:239-245`): `A >= 1000` → A wins `PHILANTROPIED`, else `B >= 1000` → B wins.
      **Team A is tested first**, so a simultaneous crossing is impossible (donations are sequential anyway).
   2. **`setWinnerIfDestruction`** (`:231-237`): `robotCount(A) == 0` → **B** wins `DESTROYED`, else
      `robotCount(B) == 0` → A wins. **Trees are not robots**, so a side whose last robot dies loses even with 40
      trees standing.
   3. Neither sets `running = false`; that happens only in rule 9.5. **So the rest of the round is played out and its
      income, decay and deaths are all recorded** — and if the *other* side's win condition also fires later in the
      same round, **`setWinner` overwrites the winner** (`gameStats.setWinner` has no guard). Reproduced literally,
      and `tests/test_bc17_endladder.nim` pins the double-fire case.

**9. `processEndOfRound`** (`:251-327`):
   1. `eachRobot(processEndOfRound)` — replay-only (`addHealthChanged`); `eachTree(processEndOfRound)` — replay-only
      **plus `roundsAlive += 1`** (int), which is the tree maturity clock.
   2. **The tree pass happens BEFORE this, in `updateTrees` (`:120-128`), and it is step 6 of the round in wall order**
      — stated here because the engine's method order is `updateDynamicBodies` → `updateTrees` → `processEndOfRound`:
      `float[3] totalTreeSupply`; **`eachTree` in trove order (D1)**: `totalTreeSupply[team.ordinal()] +=
      tree.updateTree()` — **an `f32` accumulation whose ORDER IS OBSERVABLE** (docs disagreement 6);
      `updateTree()` (`InternalTree.java:164-176`) is: NEUTRAL → **0**; `roundsAlive <= 80` → `healTree(0.5f)` and
      **return 0**; else `income = health × 0.02f`, then `decayTree()` = `damageTree(0.5f, NEUTRAL, false)` — which
      **can kill the tree, releasing nothing**. Then `adjustBulletSupply(A, totalTreeSupply[A])` and then B (`f32`).
   3. **Bullet income**: `adjustBulletSupply(t, max(0f, 2f − 0.01f × getBulletSupply(t)))` for **A then B** (`f32`) —
      **zero at any supply ≥ 200** (measured).
   4. **`if (timeLimitReached() && winner == null)`** — `timeLimitReached()` is **`currentRound >= rounds − 1`**, i.e.
      **round 2 999 with `rounds = 3000`** — the four-rung ladder, first match wins:
      | rung | condition | `DominationFactor` | our `end_reason` |
      |---|---|---|---|
      | 1 | `victoryPoints(A) != victoryPoints(B)` (int) | **`PWNED`** | **`more_victory_points`** |
      | 2 | else `treeCount(A) != treeCount(B)` (int, **all** own trees, sapling or mature — docs disagreement 4) | **`OWNED`** | **`more_bullet_trees`** |
      | 3 | else `totalBulletSupply(A) != totalBulletSupply(B)`, where `total = supply + Σ type.bulletCost` over live robots **in `objectInfo.robots()` order** and **ARCHON contributes −1** | **`BARELY_BEAT`** | **`more_bullet_worth`** |
      | 4 | else the team of the **highest robot id of any type** (docs disagreement 2) | **`WON_BY_DUBIOUS_REASONS`** | **`highest_id`** (REUSED) |
      **There is no coin flip and no RNG anywhere on this path.** Rung 3's sum is `f32` but every addend is an exact
      small integer-valued float, so the order of `robots()` is **not** observable here — stated so nobody ports it.
   5. `addTeamStat(...)` (replay-only); **`if (winner != null) running = false`**.

**10. `makeRound(currentRound)`** — the flatbuffer writer. **Not ported** (V2); this repo writes its own JSON replay.

### Where the docs are wrong — six disagreements, and the engine wins every one

`specs-1.6.2.html` is the human-readable spec. **Where it disagrees with the engine, the ENGINE WINS**, and the port
follows the engine. Every disagreement found:

| # | the spec says | the engine does | port follows |
|---|---|---|---|
| 1 | §16: "Different maps may run for different numbers of rounds, ranging from 1500 to 3000" | `GameMapIO.Serial.deserialize:235` sets `rounds = GameConstants.GAME_DEFAULT_ROUNDS` and **never reads a round count from the map file**; measured, `getRounds()` is **3000 on all 70 maps** | **engine** — every bc17 game is **2 999 played rounds** |
| 2 | §16: tiebreak 4 is "Highest **Archon** ID (effectively random)" | `:296-306` loops over **every** robot in `objectInfo.robots()`, so it is the highest **robot** id of any type | **engine** |
| 3 | §16: tiebreak 3 is "Number of bullets plus bullet cost of all surviving robots" | the same loop adds `type.bulletCost`, and **`ARCHON.bulletCost` is `−1`**, so **each surviving archon subtracts a bullet** | **engine**, and the score formula uses the engine's expression |
| 4 | §16: tiebreak 2 is "Number of **active** bullet trees" | `objectInfo.getTreeCount(team)` is a plain counter with **no notion of "active"**: a 10-HP sapling counts exactly as much as a 50-HP mature tree | **engine** |
| 5 | §10: "starts with 10 health, then matures by 0.5 health per turn for the next **80** turns up to a maximum of 50" | the growth branch is `roundsAlive <= 80` (**81** turns) and it **returns 0 income**, so the tree pays nothing until `roundsAlive == 81`; `healTree` clamps at 50, so the 81st growth turn is a no-op | **engine** |
| 6 | §22: "In the second phase, Trees update… **The ordering of this phase is not important to the outcome of a match**" | `updateTrees:122-124` accumulates `totalTreeSupply[team] += tree.updateTree()` **in float32 over trove hash order**, and that sum lands in the bullet supply that `donate`'s integer floor and every affordability test read | **engine** — the sentence is false, and **D1 reproduces the order rather than trusting it** |

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200` (`episode_timeout_minutes: 20`); 60 % = **720 s**. The `bc17` variant is
**best-of-three on three distinct maps from the `mixed` pool, played to the engine's own limit of 2 999 rounds**.

```
container start, map load, seat connect              <=  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    <=  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 2 999 rounds                        <= 330 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 120)
score + replay write + shutdown grace                <=  30 s
                                                       -------
worst case                                             435 s   <= 720 s
```

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s doctrine phase and
both seats' calls go out as **one parallel batch**.

**Honest per-round estimate, so the builder can check it.** bc17 is the heaviest year in this repository and the
reason is bullets:

- **The census is bullet-bounded and bullets come almost entirely from trees.** A mature tree pays 1 bullet a round
  and the played pool supports **40–120 own trees** a side at full build-out, so peak income is **40–120 bullets a
  round**; over 2 999 rounds a well-played side earns **20 000–60 000 bullets**, which is 200–600 fighters at 100 each
  or 1 000 VP with change. Realistic: **100–400 units built per side, peak alive 30–120 a side**.
- **Bullets in flight is the cost driver.** 40 bullets a round of income funds ~40 single shots a round, and a SOLDIER
  bullet lives 15–50 rounds, so a sustained firefight holds **300–1 000 bullets in flight**. Each bullet-update
  enumerates the trees within `10 + distToFinish/2` of its midpoint — on `Chess` (**924 trees on 64×64** = 0.23
  trees/unit²) that disc holds **≈ 87** — so the dominant term is **≈ 45 000 `calcHitDist` calls a round**. The common
  path is **1 atan2 + 1 sqrt + 1 sin**, because `perpDist > targetRadius` rejects most candidates before the
  `sqrt`/`cos` (rule 5.11.4), and **the three per-bullet invariants (`toFinish`, `maxDist`, `distToFinish`) are
  hoisted out of the candidate loop** — each is a deterministic function of the bullet alone, so the hoist is
  **bit-identical by construction** and `tests/test_bc17_ballistics.nim` asserts it on 10⁶ random configurations. At
  ≈ 120 ns for those three fdlibm calls that is **≈ 5.4 ms/round**, plus **≈ 1–2 ms/round** for 240 robot turns (a
  bounded grid query at `sensorRadius ≤ 14` and ≤ 1 500 DecisionOps each). Trees are trivial.
- **Estimate: 3–12 ms/round, i.e. 9–36 s per 2 999-round game in release Nim, and 27–108 s for a best-of-three** —
  inside `matchBudgetSeconds 330` with a 3× margin at the pessimistic end. For comparison, bc23 measured 1.45–2.95
  ms/round at 207–451 robots over 2 000 rounds with **no projectiles at all**.
- **`tests/test_bc17_perf.nim`** plays a full 2 999-round game on `Chess` (**64×64, 924 neutral trees, 2 archons a
  side** — the map that maximises the tree-candidate count) with both seats on `opening: tree_farm`,
  `gardener_count: 6`, `farm_layout: hex`, `soldier_tank_ratio: 0`, `bullet_reserve: 0`, `vp_donate_policy: never` —
  the configuration that maximises trees, soldiers and therefore bullets in flight — and **fails CI above 60 s**.
- **If that gate ever goes red the fix is one config value** — `gamesPerMatch: 3 → 2`, then `→ 1` — and the note says
  so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc17's axis is **map-shaped**: `Alone` (100×100, **zero** neutral
  trees, one archon a side, separation 127) is a pure farm-and-donate race; `Chess` and `LineOfFire` (924 and 1 228
  neutral trees) are lumberjack maps where the board must be cut open; `HouseDivided` and `Cramped` (archon separation
  **6.5** and **5.0**) are decided before a tree matures; `Maniple` (**406 trees, every one containing a robot**)
  makes `shake_neutral_trees` and `chop_policy` the whole doctrine. One map would rank the map, not the doctrine.
- Because this sim is the **heaviest** in the repo and the viewer's Worker re-simulates from the start of the game on
  every seek, **the phase-60 viewer check 8 is dispatched with `settle=20000 soak=15`** and `ci.yml`'s `wasm-viewer`
  job runs the bc17 replay at `--timeout 120 --soak 15`, joining bc16/bc22/bc23/bc24/bc25 in the heavy set (§Viewer).
  `docker-smoke` prints `sim_seconds / rounds` and `docs/RULES-BC17.md` records the measured value.

### Scoring, sign, and what the bc17 league ranks by

The 2017 game is win/lose; it has no point formula. This one is defined here, and it is a continuous reading of the
engine's own tiebreak ladder so that the score and the winner never tell different stories:

```
share(x, y)  = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
vp[t]        = victory points of t at the final round                          # rung 1 (int, 0..1000+)
trees[t]     = t's bullet trees alive at the final round                       # rung 2 (int)
worth[t]     = bulletSupply(t) + sum over t's live robots of type.bulletCost   # rung 3 (f32; ARCHON is -1)
points[t]    = int(64.0'f32 * share(vp[t],    vp[o])
                 + 24.0'f32 * share(trees[t], trees[o])
                 + 12.0'f32 * share(max(0'f32, worth[t]), max(0'f32, worth[o])))   # TRUNCATION, not rounding
```

Six load-bearing details, each pinned by a test vector in `tests/test_bc17_scoring.nim`:

- The three terms are **exactly the engine's three deciding rungs, in the engine's own priority order** (rule 9.4), so
  a doctrine that wins the game usually wins the shape of it too. Rung 4 (highest robot id) is deliberately **not** a
  term: it measures nothing about play.
- `worth` uses **the engine's own expression, `−1` per archon included** (docs disagreement 3). It is clamped at 0
  before `share` because a side reduced to three archons and no bullets has `worth = −3`, and a negative share is not
  a share. **The clamp is applied to the score only, never to the ladder** — the ladder compares the raw values, so a
  `worth` of `−1` still beats `−3` on rung 3 while both score 0.5.
- **`vp` and `trees` are exact integers and `worth` is a float32 built from exact small integer-valued floats**, so
  `points` is reproducible bit-for-bit between the native recorder and the wasm re-deriver. The only floats in the
  formula are the three `float32` shares and the truncating `int()`.
- The weights are **super-increasing** (`24 > 12` and `64 > 24 + 12`), so a *decisive* margin on a higher rung
  dominates everything below it. **This note claims no more than that.** A 501-to-499 VP margin is
  `501/1000 − 499/1000 = 0.002` of 64 = **0.128 points against 36 available below**, so **`points` alone can favour
  the loser**; it measures the *shape* of the game, not who won it.
- `share` returns **0.5 on a 0–0 total** (the bc16/bc19/bc22–bc25 choice): two sides that both donated nothing should
  not be separated by an arithmetic accident, and rung 1 falling through is the normal case.
- The `end_reason` is **not** computed from `points`: the ladder uses the engine's exact comparisons, so a razor-thin
  margin can decide the *winner* on a difference that rounds away in *points*. Stated explicitly, tested explicitly,
  and not a bug.

```
results.scores[t] = 200.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** bc17 joins `winBonusFor`'s **200** set (`match.nim:674`) for exactly the reason bc16, bc19 and
bc22 did: `points` can legitimately favour the loser, so only a bonus that dominates the whole `[0, 100]` range keeps
the ordering of `results.scores` **provably** in agreement with `results.wins`. A 2–0 gives `400 + mean` against
`≤ 100`; a 2–1 gives `400 + mean` against `200 + mean ≤ 300`. `tests/test_bc17_scoring.nim` asserts that agreement on
500 random synthetic finals, including clinched two-game matches, asserts the super-increasing property, and asserts
the documented `points`-disagreement case explicitly so neither is mistaken for a bug later.

**The `bc17` league ranks by ELO over match wins**, computed by the platform from the episode's winner;
`results.scores` is the per-episode number the ladder reads and its ordering agrees with `results.wins` exactly, as
above — the same shape as the nine shipped leagues. A `deadline` episode scores the games that finished; a `fault`
episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` mapped to this repo's snake_case vocabulary,
plus our one wall-clock value. `results.games[].domination_factor` carries the engine's own enum name beside it, so a
replay always traces back to a branch of the engine:

| `end_reason` | engine origin | `DominationFactor` | meaning | can fire early? | new to the manifest enum? |
|---|---|---|---|---|---|
| `victory_points_reached` | `GameWorld.java:239-245`, from `donate` | **`PHILANTROPIED`** | a side's donation took it to **≥ 1000 VP**; the winner is set the instant the donation lands and **the round still finishes** | **yes** — the intended way to win | **NEW** |
| `all_robots_destroyed` | `:231-237`, from every `destroyRobot` | **`DESTROYED`** | a side's **last robot** died (trees do not count) | **yes** | **NEW** |
| `more_victory_points` | `:274-278` | **`PWNED`** | round 2 999 reached; more VP | no | **NEW** |
| `more_bullet_trees` | `:281-287` | **`OWNED`** | VP level; more **own trees of any maturity** | no | **NEW** |
| `more_bullet_worth` | `:293-312` | **`BARELY_BEAT`** | VP and trees level; more `bullets + Σ bulletCost` (**archons −1 each**) | no | **NEW** |
| `highest_id` | `:315-317` | **`WON_BY_DUBIOUS_REASONS`** | everything level; the team of the **highest robot id** | no | **REUSED** (bc20's, identical meaning) |
| `abandoned` | — | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded | — | already present |

**Exactly FIVE values are added** — `victory_points_reached`, `all_robots_destroyed`, `more_victory_points`,
`more_bullet_trees`, `more_bullet_worth` — and **two are reused**, `highest_id` and `abandoned`. **`annihilated` is
deliberately NOT reused** for `all_robots_destroyed` even though bc21's and bc22's semantics are similar, because
`docs/RULES-BC21.md` and `docs/RULES-BC22.md` already document `annihilated` as *those* years' factor and a bc17
replay must trace to `DominationFactor.DESTROYED`; `highest_id` is reused only because the engine's own rule is
word-for-word bc20's. **No coin-flip value is added: 2017 has no coin flip.**

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from the nine shipped years**:
**`complete`** (a side won 2 games, or all scheduled games finished; scored as above), **`deadline`** (the wall-clock
guard fired mid-game: the unfinished game is discarded and the **finished games are scored**, or `[0, 0]` if none
finished) and **`fault`** (a sim invariant tripped — a bullet with no owner, a body spawned overlapping another, an
id-pool exhaustion or a hash-chain break — with a partial replay and `[0, 0]` still written).

**Best-of-N clinch semantics, stated because phase 60 has judged this wrong before (2026-09-07):** a side that takes 2
games settles the episode immediately. An episode that records **two** games with `reason: complete` on a
`gamesPerMatch: 3` variant is **correct**, not truncated; `results.games` carries only the games actually played, and
`replay.plan.maps` carries all three drawn maps so a spectator can see what the third would have been.

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the nine shipped
years). Container exit codes are unchanged: `0` whenever results + replay were attempted (including
`deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep answering for the ~20 s shutdown grace,
and the websocket handler keeps its `Ping → Pong` **payload echo** and does not filter binary frames
(`tools/ci/cert_probe.py` proves both against the real image).

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged: the player container is a thin registrar and every decision is taken
inside the **game** container, the only one the platform injects the `anthropic_api_key` secret into
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/battlecode/anthropic_api_key`).

**One decision turn, one parallel batch.** Both seats are asked at the same moment and their two provider calls go out
as **ONE parallel batch** (`curly.makeRequests`, `decide.nim`'s existing shape) with the same deadline; seats are
**never** queried one after another. The batch's wall-clock budget is `doctrineBudgetMs = 45 000` — attempt 1
`attempt1Ms = 20 000`, the single retry `retryMs = 12 000` — which is the per-turn budget for this game and sits inside
the 720 s envelope computed in §The game. At most **2 provider calls per seat per episode**.

`src/battlecode/llm.nim` is unchanged and year-neutral: the credential ladder (Bedrock sidecar → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI`), the single Bedrock candidate `us.anthropic.claude-haiku-4-5-20251001-v1:0`, fence-tolerant
JSON extraction, the `throttled` fast-fail, rune-boundary truncation, `maxOutputTokens = 1200`. **With no credentials
the client disables itself at construction and every seat falls back instantly**, which is what lets offline
certification and `docker-smoke` finish in seconds.

### The envelope pin — already fixed year-neutrally, and what bc17 must still do

The bc23 league failure (LEARNINGS 2026-09-08: champions wrapping the sheet in `{"protocol":…,"doctrine":{…}}`, every
knob landing in `sheet_unknown_fields`, the seat playing the schema-default sheet) was fixed year-neutrally by the
bc22 run and is **already on `main`**: `sheet.nim:108-159` resolves the sheet node `""` → `"sheet"` → `"doctrine"` →
the single object-valued key, unwraps **at most once**, and records which rule fired in `Sheet.envelope`, which
`replay.nim` writes as `seats[].sheet_envelope`. **bc17 changes none of that.** Its three obligations are:

1. **A `YearBc17` arm** in `knownKeysFor`, `defaultSheet`, `validate`'s `case`, `toJson` and `plainWords`
   (`sheet.nim:48,82,95,195,223,237` are where the bc19 arms sit) — the five-line shape bc16 and bc19–bc25 added.
2. **Absent-key defaulting counted, in `years/bc17/knobs.nim` only.** `applyKnobs17` adds an **absent** known key to
   `defaultsApplied` as well as a repaired one, exactly as `years/bc19/knobs.nim` and `years/bc16/knobs.nim` do, so
   `sheet_defaults_applied` for a bc17 seat is `[]` only when the cog really set all eleven knobs. This is
   deliberately **not** done year-neutrally: doing so would change what a bc16/bc19–bc26 episode records in that
   array. `tests/test_bc17_sheet.nim` asserts that a bc17 empty sheet reports all eleven names **and** that a bc19
   empty sheet still reports none, so the change is provably scoped.
3. **The divergence is rendered.** `#bc17-doctrines` draws, per seat, the applied sheet in plain words **and** a badge
   when the two disagree: `envelope: doctrine · 11 of 11 knobs defaulted`, plus the first 120 runes of
   `sheet_submitted` under a "what the cog actually sent" disclosure — the `renderDoctrines` shape already in the
   page, with bc17 ids.

### The bc17 doctrine sheet — eleven knobs, **no `chassis` key** (the D0 rule)

Each knob has a type, a range, a default, and a named site in the bc17 chassis. Unknown key, wrong type or
out-of-range value → **that field's default** (integers **clamp** instead), recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by answering badly — only by
answering weakly. **The chassis is not a knob**: a submitted `chassis` key is recorded in `sheet_unknown_fields` and
ignored (`sheet.nim`'s existing behaviour, GV04), so `examplefuncsplayer17` is reachable **only** through
`PLAYER_SCRIPTED=examplefuncsplayer17`.

**The anti-inert rule, stated as a rule the builder must hold every knob against: no setting of any knob, and no
combination of settings, may produce an inert or self-starving faction.** The strategy surface lives *inside one
competent chassis*: independently of every knob, `orchard` always **hires ≥ 1 GARDENER per archon and replaces a dead
one**, **plants its first tree by round 60 and keeps ≥ 3 alive whenever it can afford them**, **waters the
lowest-health own tree in reach every turn a gardener has nothing better to do**, **builds a fighter whenever bullets
allow and the census is below target, never fewer than two per gardener**, **answers any enemy sensed within
`defend_radius` of its own gardeners, archons or trees**, **never fires a LUMBERJACK `strike()` whose own-HP cost
exceeds the enemy's** (it hits its own trees, and its own trees are its income), **never walks a TANK onto its own
tree**, and **never donates below `bullet_reserve` unless `vp_donate_policy` is `rush_1000`**. Every knob moves *how
much of what, when* — never *whether it plays*. `tests/test_bc17_knobs.nim` proves each knob has teeth and
`tests/test_bc17_survival.nim` proves the floor holds, **with a negative control that must fail** (§Tests 20, 21).

| field | type / values | default | what it changes (`src/battlecode/years/bc17/chassis/…`) |
|---|---|---|---|
| `opening` | `tree_farm` \| `tank_rush` \| `lumberjack_swarm` \| `scout_squat` | `tree_farm` | `econ.nim plan()` — the first-400-round budget split and posture, and the four archetypes the 2017 season actually produced. **`tree_farm`**: hire to `gardener_count`, plant to the `farm_layout`, water everything, and buy fighters only to satisfy `defend_radius` until round 300 — the income curve that funds a 1 000-VP purchase. **`tank_rush`**: from the first 300 bullets, TANKs (200 HP, 5 damage a bullet, and a body attack that eats trees) walked at the mirror of your own archon; a tank two-shots a gardener and its bullets one-shot a scout, so a wave that arrives before round 300 ends the enemy farm — but 300 bullets is six trees not bought. **`lumberjack_swarm`**: LUMBERJACKs (100 bullets, 50 HP, `strike` for 2 to *everything* within distance 2) sent in threes; they cannot be shot down by a soldier's 2-damage bullet fast enough and they delete a farm in a dozen turns, and on a tree-dense map they are also the only way to open a lane. **`scout_squat`**: SCOUTs (80 bullets, 10 HP, stride 1.25, **the only body that may sit on a tree**) parked on the enemy's neutral trees where nothing but a bullet can reach them, shooting gardeners for 0.5 a turn and shaking every tree they pass. Each of the four still plants trees and still hires gardeners — the economy target is halved, never zeroed. |
| `gardener_count` | int **1 … 8** | 3 | `econ.nim gardenerTarget()` — GARDENERs wanted **per living ARCHON**. A gardener is 100 bullets and is the only unit that can plant (50) or water (+5/turn), and its **build cooldown of 10 turns is shared between planting a tree and building a fighter** — so gardener count is literally how many parallel 10-turn slots the faction owns. At 1 the faction still farms, just slowly; at 8 it spends 800 bullets on caretakers before a single tree pays out and crowds its own archon's spawn ring. Clamped. |
| `farm_layout` | `hex` \| `line` \| `ring` | `hex` | `farm.nim slots()` — where the trees go, and it is a real geometry choice because trees are also walls. **`hex`**: up to **six** radius-1 trees packed around one gardener at spacing `2 + 0.01`, the classic 2017 flower — maximum trees per gardener-turn of walking, and the gardener can water all six without moving, but one LUMBERJACK `strike()` in the middle hits **all six trees and the gardener**. **`line`**: a row along the own-archon→enemy-archon axis at spacing 2.5, which turns the farm into a **wall** across the approach and spreads the strike damage, at the cost of a gardener that must walk to water. **`ring`**: a circle of radius 4 centred on the archon, leaving four lanes — the layout that keeps the archon's own spawn ring clear and lets fighters through, and the only one that does not box a gardener in. |
| `soldier_tank_ratio` | int **0 … 100** | 25 | `military.nim mix()` — the percentage of the **military bullet budget** spent on **TANKs** rather than SOLDIERs. A TANK is 300 bullets, 200 HP, bullet speed 4 and **5 damage a bullet** with a triad and a pentad available, and it damages a tree by walking into it; a SOLDIER is 100 bullets, 50 HP, speed-2 bullets and 2 damage. So one tank is three soldiers' bullets at 1.5× the total HP and 2.5× the per-bullet damage, but it is one body that a lumberjack swarm can surround, and its stride is **0.5** against a soldier's 0.8. Clamped. |
| `lumberjack_share` | int **0 … 100** | 20 | `military.nim mix()` — the percentage of the **remainder after tanks** spent on **LUMBERJACKs**. This is the knob that decides whether the faction can open a tree-dense map at all (`Chess` has 924 neutral trees; `LineOfFire` 1 228) and whether it can answer an enemy farm. At 100 the faction has no ranged damage at all — which the anti-inert floor allows, because a lumberjack still kills — and `micro.nim`'s own-HP rule stops the swarm eating its own farm at every setting. Clamped. |
| `scout_harass` | int **0 … 100** | 15 | `scout.nim plan()` — the percentage of the **remainder after tanks and lumberjacks** spent on **SCOUTs**, and how deep they go: below 34 they screen own trees and shake neutral trees on the way; 34–66 they squat the enemy's neutral trees inside the enemy farm; above 66 they hunt gardeners exclusively and never come home. A scout has **10 HP** — one soldier bullet plus a bit — so this is a knob about spending 80 bullets for information and pressure, not about winning fights. Clamped. |
| `vp_donate_policy` | `never` \| `when_ahead` \| `rush_1000` \| `endgame_dump` | `when_ahead` | `donate.nim plan()` — **the knob this year is actually about.** A VP costs `7.5 + (12.5/3000) × round`, so it is **7.5 on round 1 and 19.996 on round 2 999**: the same 13 750 bullets buys 1 000 VP early or **690** late. `never`: no robot ever donates, and the faction plays for annihilation and the tree tiebreak. `when_ahead`: donate everything above `bullet_reserve` whenever our VP ≥ theirs, so the lead compounds at the cheapest price the faction can afford. `rush_1000`: donate every bullet above 100 from round 1 — the fastest possible purchase, funded by trees and nothing else, which means almost no army; it wins outright before round ~1200 against a farm that ignores it and loses to a tank rush that does not. `endgame_dump`: bank everything and convert at round 2 900 — deliberately the expensive price, and it is a **coherent** strategy rather than a trap, because rung 3 of the ladder is *bullets plus robot cost* and a 20 000-bullet bank wins it outright. |
| `shake_neutral_trees` | `never` \| `opportunistic` \| `dedicated` | `opportunistic` | `scout.nim shake()` + `gardener.nim` — `shake()` is free, takes one turn, works for **any** robot at distance 1 and hands over **every bullet inside the tree**. Measured over the played pool: a bc17 map carries **0 to 1 282** neutral trees and **`Chess` alone has 892 of them holding bullets**. `never`: no robot ever spends a turn on it. `opportunistic`: shake any tree already within interaction distance of a robot that has nothing better to do. `dedicated`: route one scout per archon on a shaking circuit of the nearest 20 bullet-bearing trees, which on a rich map is a real second income and on `Alone` (zero neutral trees) is a wasted scout. |
| `chop_policy` | `never` \| `clear_path` \| `harvest` | `clear_path` | `lumberjack.nim plan()` — a LUMBERJACK's `chop()` is **5 damage to one tree** and it is the **only** action that releases a neutral tree's contents (rule 7.3). `never`: lumberjacks only `strike()` bodies. `clear_path`: chop only the trees blocking the rally lane between the archons, which on `Chess` or `LineOfFire` is the difference between having an army and having an army stuck behind 900 trees. `harvest`: prefer neutral trees that **contain a robot** (measured: `Maniple` has **406 trees, every one of them containing a robot**; `MagicWood` 40; `GreenHouse` 58) — 200 × radius HP for a free fighter, which is 40 chops for a radius-1 tree and 400 for a radius-10 one. |
| `bullet_reserve` | int **0 … 2000** | 200 | `econ.nim bulletGate()` — the bullet floor below which the faction funds **only gardeners, trees and water**: no fighters, no donations, no pentads. **The default is 200 for a measured reason and not for taste**: the passive trickle is `max(0, 2 − 0.01 × supply)`, which is exactly **zero at 200 and above**, so a faction sitting on 200 bullets is earning nothing from it while a faction at 100 earns 1 a round. At 0 the faction spends to the last bullet and can be caught unable to answer a rush; at 2000 it hoards forty trees' worth of income and under-builds. Clamped. |
| `defend_radius` | int **1 … 40** (units, **not** squared — 2017 sensing is Euclidean distance) | 12 | `military.nim defend()` — the radius around a friendly ARCHON, GARDENER or bullet tree inside which a fighter breaks off whatever it is doing to answer an enemy. 12 is a little under twice a soldier's sensor radius of 7, so the default is "defend what a picket can see"; 40 is most of a 60-wide board and pins the whole army at home. At 1 the faction never defends and its gardeners are farmed for free. Clamped. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on **rune**
boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — the broad early meta against the converged one — with the
two mechanics the 2017 season never systematically spent (the **VP price curve** and the **income cliff at 200
bullets**) put on the table in both.

- **champion #1, `battlecode-bc17-orchard` (daveey)**: *"You command a faction in Battlecode 2017 'Robotic Wildlife
  Fund'. Winning is a PURCHASE: 1000 Victory Points ends the game instantly, and a point costs 7.5 bullets on round 1
  rising linearly to 20 on round 2999 — about 13750 bullets for the win at the average price, and every round you wait
  makes it dearer. Bullets come almost entirely from bullet TREES: a GARDENER plants one for 50 bullets, it starts at
  10 health, grows 0.5 a round for 81 rounds, then pays health/50 a round — 1 bullet a round at full 50 health — and
  withers 0.5 a round unless a gardener waters it for +5. THE FREE TRICKLE IS A TRAP: it is max(0, 2 minus 0.01 per
  bullet you hold), EXACTLY ZERO at 200 bullets or more, and you start at 300 — so it pays you nothing until you spend
  below 200. Your doctrine: out-farm them and buy the win. Set opening \"tree_farm\", gardener_count 4-6, farm_layout
  \"hex\" for maximum trees per gardener or \"line\" to make the farm a wall, soldier_tank_ratio low-to-middling
  (10-40) because a SOLDIER is 100 bullets and a TANK is 300, lumberjack_share 10-30 (enough to open a lane and to
  answer THEIR lumberjacks, because one strike does 2 damage to every tree within distance 2 and your trees are your
  income), scout_harass 0-30, vp_donate_policy \"when_ahead\" or \"rush_1000\" and say which and why, bullet_reserve
  100-400, shake_neutral_trees \"opportunistic\" or \"dedicated\", chop_policy \"clear_path\" or \"harvest\",
  defend_radius 10-25. In notes, say how many trees you want standing by round 500 and what you do if tanks arrive
  before round 400."*
- **champion #2, `battlecode-bc17-tankrush` (daveey-1)**: *"You command a faction in Battlecode 2017 'Robotic
  Wildlife Fund'. Everyone in 2017 farmed. Three things nobody spent properly. First: THE CLOCK ON THE PRICE. A point
  costs 7.5 bullets on round 1 and 20 on round 2999, so a farm still farming on round 2000 is buying its win at nearly
  triple price — killing their economy early is worth more than growing yours. Second: THE LUMBERJACK. 100 bullets, 50
  health, no bullets at all, and strike() puts 2 damage on EVERY robot AND EVERY TREE within distance 2 of its centre
  with NO TEAM CHECK. Three of them inside a six-tree hex farm delete the farm and the gardener in a dozen turns, and
  a soldier's 2-damage bullet cannot kill 50 health fast enough to stop them. Third: THE TANK BODY ATTACK. A TANK is
  300 bullets, 200 health, bullet speed 4 and 5 damage a bullet, and it does 4 damage to a tree just by trying to walk
  onto it. Your doctrine: get there first. Set opening \"tank_rush\" or \"lumberjack_swarm\", soldier_tank_ratio high
  (50-90) for tanks or low with lumberjack_share high (50-90) for the swarm, gardener_count 1-3 because you are buying
  an army and not an orchard, farm_layout \"ring\" so your archon's spawn ring stays clear, bullet_reserve low (0-150)
  because a banked bullet is a bullet not walking at their gardener AND because the trickle only pays below 200,
  scout_harass 20-60 to find their gardeners, vp_donate_policy \"never\" or \"endgame_dump\" and say which: \"never\"
  plays for annihilation and the bullet-tree tiebreak, \"endgame_dump\" banks everything and wins the
  bullets-plus-robot-cost tiebreak. Set chop_policy and shake_neutral_trees deliberately: a chopped neutral tree can
  contain a FREE ROBOT that joins you, and some maps have hundreds. In notes, say which of their archons your first
  wave walks at and what you do if they reach 500 points before round 1500."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every default and
range, the constant tables (the six unit types with bullet cost, health, body radius, bullet speed, attack power,
sensor and bullet-sight radius and stride; the tree arithmetic; the VP price curve; the shot costs and spreads; the
strike and chop rules; the four-rung ladder), the map cards for all three games **with their neutral-tree counts, the
trees that hold bullets or robots, and the archon separation**, the scoring formula, the alias pair, a **HOW A GAME
ENDS** section (the bc21 r1-F8 fix, kept), and the reply contract ("reply with ONE JSON object whose top-level keys are
the knob names; your reply must begin with `{`"). The assistant turn is prefilled with `{` and the prefix re-attached
before parsing (the procgen 0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`, `:53-103`). It gains a `bc17` arm with
two published names. **The manifest still declares only `awu` and `scaffold`** — the two ids the certification fixture
seats — and `PLAYER_SCRIPTED` resolves **per year**, exactly as bc16 and bc19–bc25 do:

| `PLAYER_SCRIPTED` | on `year: "bc17"` resolves to |
|---|---|
| `awu`, `orchard`, or anything unrecognised | **`orchard`** — the strong doctrine chassis and the champions' chassis |
| `scaffold`, `example`, `examplefuncsplayer`, `examplefuncsplayer17` | **`examplefuncsplayer17`** — the deliberately weak floor and the parity oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field.
`defaultBaselineFor("bc17")` is `orchard`, so a seat that says nothing useful plays the strong doctrine, not the weak
floor. `Baseline` gains `blOrchard = "orchard"` and `blExamplefuncsplayer17 = "examplefuncsplayer17"`;
`ScriptedChassis` gains `scOrchard = "orchard"` and `scExamplefuncsplayer17 = "examplefuncsplayer17"`. **Neither string
collides with the eighteen already in those enums** — checked against `sim_types.nim:263-281`, and
`tests/test_baselines.nim` asserts the enums have no duplicate strings, because a duplicate compiles and then seats the
wrong bot.

**`orchard` — the strong baseline and the champion chassis.** Written from the engine source, the 1.6.2 spec page and
the four archetypes the idea names; **no competitor bot was read** (rail 5). Two behaviours are ported from the
**AGPL-3.0** `examplefuncsplayer` and credited as such in `NOTICE`: its **`tryMove` obstacle probe** (try the intended
direction, then ±20°, ±40°, ±60°, `RobotPlayer.java:215-244`) and its **`willCollideWithMe` bullet test**
(`:253-277`) — both are named in the licence file, because "we wrote it ourselves" about code that came from
somewhere is the defect. The algorithm, parameterised by all eleven knobs:

- **`kit.nim`** — the per-side memory every robot shares and the `DecisionOps` charging: a **uniform grid** over the
  arena (cell 8 units) used for every candidate query, the mirror function derived once from
  `getInitialArchonLocations(us)` and `getInitialArchonLocations(them)` (both are public, rule 5 of §The game), the
  remembered enemy-structure roster, the remembered neutral-tree roster with `containedBullets`/`containedRobot` flags
  and a claim bit, and the navigator: the licensed `tryMove` probe plus a **continuous-space wall-follow** for the
  case where all seven directions are blocked (walk along the blocking body's tangent, at most 12 turns before
  giving up and re-planning). **Every candidate examined in any query is charged 1 `DecisionOps`**, and the budget is
  checked before a query starts, never inside it.
- **`econ.nim`** — `plan()` (from `opening`), `gardenerTarget()` (from `gardener_count`), `bulletGate()` (from
  `bullet_reserve`), and the per-archon commitment ledger so two archons cannot promise the same 100 bullets. It is
  the only place bullets are ever committed, and it holds the unconditional floor: **≥ 1 gardener per archon, a first
  tree by round 60, ≥ 3 trees alive when affordable, ≥ 2 fighters per gardener**.
- **`archon.nim`** — an archon's turn: hire into the free direction nearest the *rear* (an archon that boxes itself in
  cannot hire again), walk **away** from the nearest sensed enemy at stride 0.5 while staying within 15 of its own
  farm, broadcast the rally point on channel 0/1 once every 5 rounds, and never stand on a farm slot.
- **`gardener.nim`** — claim a farm slot from `farm.nim`, walk to it, plant when the cooldown is up and the circle is
  clear, **water the lowest-health own tree within `1 + radius + 1`** every turn it is not planting or building, and
  spend the shared 10-turn cooldown on a fighter when `military.nim` asks. **`farm.nim slots()`** implements the three
  layouts geometrically: `hex` = six slots at radius `1 + 0.01 + 1` around the gardener at 60° spacing; `line` = slots
  every 2.5 units along the own→enemy archon axis; `ring` = slots on the circle of radius 4 around the archon with
  four 30° lanes left empty.
- **`military.nim` + `micro.nim`** — the war. `mix()` (from `soldier_tank_ratio`, `lumberjack_share`,
  `scout_harass`), `defend()` (from `defend_radius`), and the four-state machine `RALLY → PUSH → SCREEN → ANSWER`.
  `micro.nim` builds the **bullet-threat set** — every sensed bullet's segment for the next two rounds, using the
  licensed `willCollideWithMe` test — and picks the move that minimises threat while closing on the target; and it
  chooses the **shot shape** by counting sensed enemies inside the cone: a pentad (6 bullets) only when ≥ 3 bodies lie
  within ±15° and the stock is above `bullet_reserve + 6`, a triad when ≥ 2 within ±20°, else a single. **A LUMBERJACK
  never strikes when the blast's own-HP cost (own robots plus own trees inside distance 2) exceeds the enemy's** — at
  every `lumberjack_share`.
- **`lumberjack.nim`** — `plan()` per `chop_policy`, including the target order for `harvest` (trees with a contained
  robot first, then trees with bullets, then trees blocking the lane), and the rule that a lumberjack in its own farm
  chops rather than strikes.
- **`scout.nim`** — `plan()` per `scout_harass` and `shake()` per `shake_neutral_trees`, including the one thing only
  a scout can do: **park on a neutral tree** (a scout may overlap a tree, rule 6.1) where no other body can reach it,
  and shoot gardeners from there.
- **`donate.nim`** — `plan()` per `vp_donate_policy`, with the exact-multiple rule: **donate `floor(surplus / price) ×
  price`, never the raw surplus**, because the remainder is destroyed (rule 6.12) and the difference is up to 20
  bullets a donation.
- **`comms.nim`** — the 10 000-channel per-team array, laid out and documented: `0..1` rally x/y, `2` round stamp
  (anything older than 10 rounds is ignored), `3..8` the enemy-archon sightings, `9..40` the farm-slot claims,
  `41..60` a threat digest by grid cell. **The chassis broadcasts at most once per unit per five rounds** and never
  from a scout inside enemy territory, because **broadcasting reveals the broadcaster's position to BOTH teams next
  round** (rule 2.2) — the one place in this year where communicating costs information rather than bullets.

**`examplefuncsplayer17` — the weak floor and the parity oracle's other side.** A port of
`battlecode-scaffold-2017/src/examplefuncsplayer/RobotPlayer.java` at `76e7b51e` (**AGPL-3.0**), and the **only** bot
in this year module that exists in two implementations that must agree statement-for-statement:
`years/bc17/chassis/examplefuncsplayer17.nim` and `tools/oracle/bc17/examplefuncsplayer17/RobotPlayer.java`. Its whole
behaviour, after the **one committed patch hunk** below:

1. **ARCHON**: `dir = randomDirection()`; **if `canHireGardener(dir)` and the next draw is `< 0.01`** → `hireGardener`;
   then `tryMove(randomDirection())`; then `broadcast(0, (int)x)` and `broadcast(1, (int)y)`.
2. **GARDENER**: read channels 0 and 1 (and **do nothing with them** — the stock bot builds a `MapLocation` it never
   uses); `dir = randomDirection()`; if `canBuildRobot(SOLDIER, dir)` and the next draw is `< 0.01` → build a SOLDIER;
   **else if** `canBuildRobot(LUMBERJACK, dir)` and the next draw is `< 0.01` and `isBuildReady()` → build a
   LUMBERJACK; then `tryMove(randomDirection())`. **It never plants a tree and never waters one.**
3. **SOLDIER**: `robots = senseNearbyRobots(-1, enemy)`; if non-empty and `canFireSingleShot()` →
   `fireSingleShot(getLocation().directionTo(robots[0].location))` — **`robots[0]` is the NEAREST enemy**, because the
   engine's candidate enumeration is ascending distance (D2); then `tryMove(randomDirection())`.
4. **LUMBERJACK**: `robots = senseNearbyRobots(1 + 2, enemy)`; if non-empty and not yet attacked → `strike()`; else
   sense all enemies within the sensor radius and `tryMove(directionTo(robots[0]))`, else move randomly.
5. **TANK and SCOUT have no `case` in the switch at all**, so `run()` returns immediately and **the robot dies** ("If
   this method returns, the robot dies!", `RobotPlayer.java:8-10`). The bot never builds either, so the path is not
   exercised — but it is a real rule of this bot and `tests/test_bc17_examplefuncsplayer17.nim` asserts it by building
   a TANK into it synthetically and requiring the robot to be destroyed on its first turn.
6. It **never donates, never shakes, never chops, never waters and never plants**, so it can never win by victory
   points and its only income is the sub-200 trickle. That is what being the weak floor means, and it is why the
   substance assertions that need trees or donations are asserted **across the pair** and not per seat (§Tests,
   `docker-smoke`).
7. **It may not gain behaviour: it is one side of the differential oracle**, and
   `tests/test_bc17_examplefuncsplayer17.nim` asserts its RNG call sequence and its branch order against a recorded
   oracle trace.

**The one patch hunk** (`tools/oracle/bc17/examplefuncsplayer17/determinism.patch`, applied to the committed copy in
CI, mirroring `tools/oracle/bc19/examplefuncsplayer19/determinism.patch`):

| hunk | change | reason |
|---|---|---|
| 1 | the **three** `Math.random()` call sites — `randomDirection()` (`:192`) and the two `< .01` build gates (`:49`, `:89-91`) — become `rng.nextDouble()`, where `rng` is a **`java.util.Random` seeded with the robot's own `rc.getID()`**, created once per robot | the stock line draws from the wall-clock-seeded global RNG, so the stock bot is **not reproducible even against itself** and no bit-exact parity is possible with it. `java.util.Random` is chosen because `src/battlecode/rng.nim` already ports it, so Tier A″ is *also* a test of that module. **The draw ORDER is load-bearing and is preserved exactly**: Java's `&&` short-circuits, so the archon draws a second time **only when `canHireGardener(dir)` is true**, and the gardener draws a third time only when the first gate fails and `canBuildRobot(LUMBERJACK, dir)` is true. `tests/test_bc17_examplefuncsplayer17.nim` pins the per-turn draw count for all four branch combinations. |

Its scripted reply is the all-defaults sheet (it reads no knob). Both replies go through the **same**
`sheet.validate` the LLM path uses, which is what makes the bounded-orders test meaningful and an LLM doctrine and a
scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `orchard` chassis, `results.fallbacks[seat] = 1`, a **`doctrine_fallback` event** names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` (45 000) | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default (or clamps, for the six integers); the rest of the sheet applies |
| the sheet arrives inside an envelope | it is unwrapped **once**, the envelope key is recorded in `seats[].sheet_envelope`, and the knobs apply |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds` (120), or the match exceeds `matchBudgetSeconds` (330) | the running game is **abandoned**, finished games are scored, `results.reason = deadline`, `plan.abandonAfter[g]` records the round it stopped at |
| the robot id pool would pass `MAX_ROBOT_ID` (32 000) and collide with the bullet id space | the `build`/`hire` is **refused**, counted in `builds_refused` and `refused_actions`, and the game continues (V3) |
| a sim invariant trips (a bullet with no owner, a body spawned overlapping another, a hash-chain break) | `results.reason = fault`, `scores = [0, 0]`, and a **partial replay is still written** |
| a side takes 2 games | the episode settles immediately — no padding (§The game, clinch semantics) |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `orchard` baseline reply, and it is exactly the all-defaults sheet:

```json
{"sheet":{"opening":"tree_farm","gardener_count":3,"farm_layout":"hex",
          "soldier_tank_ratio":25,"lumberjack_share":20,"scout_harass":15,
          "vp_donate_policy":"when_ahead","shake_neutral_trees":"opportunistic",
          "chop_policy":"clear_path","bullet_reserve":200,"defend_radius":12},
 "notes":"default orchard doctrine","motto":"Plant, water, donate."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into `/bin/battlecode`
and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing gameplay-related lives outside it; the viewer
never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc17/constants.nim` | **new, generated** | every `GameConstants` field and the whole six-row `RobotType` table with its eleven columns, emitted by `tools/gen_year_constants.py --year bc17` **from the jar's own classes by reflection** (2017's `GameConstants` is an interface, so its fields are implicitly `public static final`); CI regenerates and byte-diffs |
| `src/battlecode/years/bc17/geom.nim` | **new** | the continuous-space primitives, each one **a transcription of one Java method with its widths** (F3): `MapLocation` as a `(x, y: float32)` value type, `distanceTo`, `distanceSquaredTo`, `isWithinDistance`, `add(dir)`, `add(dir, dist)`, `translate`, `Direction` as a single `radians: float32` with `fromDeltas` (atan2), `reduce`, `rotateLeftRads/Degrees`, `rotateRightDegrees`, `radiansBetween`, `getDeltaX/Y`, and `onTheMap(loc)` / `onTheMap(loc, radius)` with the engine's **four-cardinal-point** circle test |
| `src/battlecode/years/bc17/trove.nim` | **new** | `gnu.trove` `TIntObjectHashMap`'s **observable order**, extended past bc22's copy with `forEachValue`, a capacity-retaining `clear()` and the pre-compaction snapshot semantics (D1). **A copy, not an import, and the reason is in D1** |
| `src/battlecode/years/bc17/index.nim` | **new** | the candidate index: a **uniform grid** (cell 8 units) over trees, robots and bullets, plus the six query procs that reproduce `ObjectInfo`'s filters exactly (`allTreesWithinRadius`, `allRobotsWithinRadius`, `allBulletsWithinRadius`, `treeAtLocation`, `robotAtLocation`, `isEmpty`/`isEmptyExceptForRobot`/`noRobotsExceptForRobot`) and **the one normative comparator** `(distanceSquaredTo(query), id)` ascending (D2) |
| `src/battlecode/years/bc17/units.nim` | **new** | the six-row table, the five derived predicates as the engine's own expressions, `getStartingHealth`, and the bullet-shape costs |
| `src/battlecode/years/bc17/world.nim` | **new** | world state: `robotsById`/`treesById`/`bulletsById` as `TroveIntMap` key sets beside `Table[int, …]` payloads, the **`dynamicBodyExecOrder` as a `seq[int]` with append-on-robot-spawn, insert-before-parent on bullet-spawn and removal BY VALUE**, `TeamInfo` (bullets `float32`, victory points `int`, the two 10 000-int broadcast arrays), `currentBroadcasters`/`previousBroadcasters`, the two `IDGenerator`s, and `spawnRobot`/`spawnTree`/`spawnBullet`/`destroyRobot`/`destroyTree`/`destroyBullet` |
| `src/battlecode/years/bc17/ballistics.nim` | **new** | `updateBullet` and `calcHitDist` (rule 5), **the single most width-sensitive file in the repository**, plus the hoist of the three per-bullet invariants and the property test that the hoist is bit-identical |
| `src/battlecode/years/bc17/actions.nim` | **new** | the twelve player actions of rule 6 with their guards, counters and immediate effects, in one file because the guard order and the `incrementXCount()` placement are the easiest thing in this year to get wrong |
| `src/battlecode/years/bc17/trees.nim` | **new** | `updateTree`, `growTree`, `decayTree`, `healTree`, `damageTree`, `destroyTree`'s chop-only goodie release with the **scout-crushing** rule, and the `totalTreeSupply` accumulation in trove order |
| `src/battlecode/years/bc17/rules.nim` | **new** | the ten-step round loop of §The game, the two immediate win conditions, the four-rung ladder, the points formula, `playGame` |
| `src/battlecode/years/bc17/maps.nim` | **new** | the converted bc17 pool, the loader, `poolNames`, `drawMaps`, `sideAslotFor`, `mapCard` |
| `src/battlecode/years/bc17/knobs.nim` | **new** | the eleven-knob `Doctrine17` type, `KnownKeys17`, defaults, per-field repair, **absent-key defaulting**, `toJson17`, `bc17SheetSchema`, `plainWords17` |
| `src/battlecode/years/bc17/chassis/*.nim` | **new** | `orchard.nim`, `examplefuncsplayer17.nim`, `scenario17.nim`, `kit.nim`, `econ.nim`, `archon.nim`, `gardener.nim`, `farm.nim`, `military.nim`, `micro.nim`, `lumberjack.nim`, `scout.nim`, `donate.nim`, `comms.nim` — **fourteen files**, and `NOTICE` + `docs/RULES-BC17.md` name the same paths |
| `src/battlecode/fdlibm.nim` | **changed, additive** | gains `fdlibmSin`, `fdlibmCos`, `fdlibmAtan`, `fdlibmAtan2` and `remPio2Medium` beside the existing `fdlibmExp`. **No existing proc is touched**, so no shipped year's arithmetic changes (F4) |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc17", title: "Battlecode 2017 — Robotic Wildlife Fund", maxRounds: 3000, pools: @["small","mixed","large"], atlas: "atlas_bc17")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc17`; `Session` gains a `yBc17` branch (`w17`, `sides17`, `chassis17`); `yearIdOf`/`strongChassisFor`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson17`. Three name tables are added beside the other years' (below) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV13`, `ReplayCompatibleGameVersions` → `["GV04",…,"GV12", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scOrchard` and `scExamplefuncsplayer17` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc17` arm in `defaultBaselineFor` and `baselineFor`; `blOrchard` and `blExamplefuncsplayer17` added to `Baseline`; `baselineChassis` and `baselineReply` map them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc17`, `doctrine17` on `Sheet`, and one arm each in `knownKeysFor`, `defaultSheet`, `validate`, `toJson`, `plainWords` — **the envelope resolver is untouched** |
| `src/battlecode/match.nim` | **changed** | `winBonusFor` gains `yBc17` to the 200 set; the bc17 event names are added to `collectGameEvents` |
| `src/battlecode/render.nim` | **year-aware** | **the first float-space renderer in this repo**: bodies as circles at float coordinates scaled by a `unitsPerPixel` derived from the map's width, trees as circles of their real radius with a health ring, bullets as 2 px dots with a two-round motion trail, the six unit sprites at two team palettes, health bars, a dormancy ring on a unit under 20 rounds old, and the lumberjack strike disc |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc17 scorebug / feed / endcard shell records **and the bc17 arms of `beatsFor`** (§Viewer) |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` + `IDGenerator` port. bc17 uses **two** instances, both seeded with the map seed (D3) |
| `src/battlecode/results.nim` | **changed** | the bc17 optional keys added to the closed schema's key set |
| `src/battlecode/replay.nim` | **unchanged** | it re-validates the recorded **applied** sheet wrapped in `{"sheet": …}`, so nothing bc17 does changes how an older recording re-derives |
| `data/maps/bc17/*.json` | **new, committed** | 22 converted maps (below) |
| `data/bc17/fdlibm_vectors.json` | **new, committed** | the boundary vectors and the sampled-stream digest that pin the fdlibm port against the JVM (F4) |
| `data/atlas_bc17.png` / `.json` | **new, committed** | the 2017 sprite atlas (≈ 50 KB — fourteen cells) |
| `tools/convert_maps_bc17.py` | **new, CI + build only** | the `.map17` flatbuffer walk, **reading the map resources straight out of the pinned jar**; the same hand-rolled vtable reader `tools/convert_maps_bc23.py` already uses, plus a `float32` vector accessor |
| `tools/map_pools_bc17.json`, `tools/build_sprite_atlas_bc17.py`, `tools/gen_year_constants.py` | **new / new / `--year bc17` added** | the three pools; the atlas cut from the client-17 PNGs; the constants reflected out of the jar |
| `tools/JavaBc17Tables.java` | **new, CI-only** | prints the constants, the `RobotType` table and the fdlibm vectors from the jar's own classes under JDK 8 |
| `tools/oracle/bc17/` | **new, CI-only** | `jar.lock` (url + version + sha256 + bytes + jdk + note), `build_oracle.sh` (verification, self-containment assertions, patch application, `javac`), `Bc17Trace.java` (the trace driver), the **seven** oracle bots `{bc17idle, examplefuncsplayer17, bc17scenario, bc17scenariotree, bc17scenariokill, bc17scenariotie, bc17slowbot}/RobotPlayer.java`, and the **three** patches: `strictmath.patch` (the eleven-site `Math.` → `StrictMath.` normalisation, F1), `rtree_order.patch` (one hunk replacing `ObjectInfo`'s six `nearestN` queries with the normative `(distanceSquared, id)` enumeration, D2) and `examplefuncsplayer17/determinism.patch` (§Decisions) |
| `tools/parity_trace_bc17.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc17.py` | **new** | the tier comparison and the ledger check — bc16's script, whose comparator bugs are already fixed there |
| `tools/ci/parity_ledger_bc17.json` | **new** | the accepted-divergence ledger, **empty** at the phase-30 exit |
| `tools/gen_bc17_fixture_replay.nim` + `tests/fixtures/replay-bc17.json` | **new, committed** | the fixture replay the wasm smoke and the beat test load |
| `tests/bc17_fixture.nim` | **new** | the shared fixture builder, beside `bc16_fixture.nim` … `bc19_fixture.nim` |
| `docs/RULES-BC17.md` | **new** | the year's rules, knobs and the full §Divergences list |

**A layout rule, written here because the bc24 run paid a fixer commit for its absence.** `NOTICE`, `knobs.nim`'s doc
comments and `docs/RULES-BC17.md` all point at the layout above; if the builder merges two of these modules it must
update **all three pointers in the same commit** and add a `docs/RULES-BC17.md` §Divergences item. A licence file that
credits derived behaviour to a path that does not exist is a defect, not a cosmetic slip.

Three name tables are added to `years/dispatch.nim` beside the other years', because an event field with an
undocumented vocabulary is an event field nobody can draw (the bc23 r1-F14/F25 lessons):

```
Bc17UnitNames   = ["archon", "gardener", "lumberjack", "soldier", "tank",
                   "scout"]            # RobotType.values() ordinals 0..5
Bc17ActionNames = ["nothing", "move", "fire_single", "fire_triad",
                   "fire_pentad", "strike", "chop", "shake", "water",
                   "plant", "hire", "build", "broadcast", "donate",
                   "disintegrate", "body_attack"]
Bc17RungNames   = ["-", "victory_points_reached", "all_robots_destroyed",
                   "more_victory_points", "more_bullet_trees",
                   "more_bullet_worth", "highest_id"]
```

`first_action`'s field is **`action`**, never `kind`: a field named `kind` is flattened into the same object as the
event's own `kind` key and silently overwrites it (the bc23 r1-F25 finding).

### The float ledger — rail 3, answered per call site

**F0 — the ground the answer stands on.** Every gameplay class is declared `strictfp`: `GameWorld:16`,
`ObjectInfo:29`, `InternalRobot:9`, `InternalTree:8`, `InternalBullet:8`, `RobotControllerImpl:22`, `LiveMap:17`,
`GameMapIO:26`, `InternalBody:6`, `MapLocation:11`, `Direction:7` (eleven declarations, `grep -rn strictfp`). So there
is no x87 extended-precision path anywhere, and IEEE-754 `+ − × ÷` and comparison are **exactly specified** in both
`float32` and `float64`. Nim on x86-64 uses SSE2 and wasm32 has only IEEE floats, so **every algebraic expression in
the port is bit-exact by construction provided the widths and the order match**, which is what F3 is for.

**F1 — the complete `Math.` inventory of the gameplay tree, classified.** `(a)` = bit-reproducible because the method
is exactly specified; `(b)` = bit-reproducible because this note specifies an fdlibm/`StrictMath` port in Nim **and** a
test that pins it against the JVM's own output; `(c)` = not bit-reproducible on the pinned JDK. **There is no `(c)`.**

| function | sites | where (`file:line`) | class | why |
|---|---|---|---|---|
| `Math.atan2` | **1** | `Direction.java:86` | **(b)** | the JLS allows 2 ulp, but measured over 20 000 000 samples of the engine's own `(dy, dx)` domain **`Math.atan2` and `StrictMath.atan2` returned bit-identical doubles every time** — HotSpot has no separate atan2 stub. Ported as fdlibm `__ieee754_atan2`, pinned by F4, and the oracle is patched to `StrictMath` so the agreement is enforced rather than assumed |
| `Math.sin` | **4** | `Direction.java:162`, `MapLocation.java:241`, `MapLocation.java:277`, `InternalBullet.java:183` | **(b)** | `Math.sin` **does** differ from `StrictMath.sin` at double level — measured, **775 072 of 20 000 000 samples (3.9 %)** — because HotSpot intrinsifies it. **But every one of the four sites narrows to `float` at the call site, and after the narrowing the two agreed in 20 000 000 / 20 000 000 samples.** Ported as fdlibm `__kernel_sin` + `remPio2Medium`, pinned by F4, and the oracle patched to `StrictMath` so the residual is **zero by construction** rather than ~7 × 10⁻¹¹ per call |
| `Math.cos` | **4** | `Direction.java:150`, `MapLocation.java:240`, `MapLocation.java:276`, `InternalBullet.java:190` | **(b)** | the same, measured **655 750 of 20 000 000 (3.3 %)** at double level and **0 of 20 000 000** after narrowing |
| `Math.sqrt` | **2** | `MapLocation.java:134`, `InternalBullet.java:189` | **(a)** | IEEE-754 requires `sqrt` to be **correctly rounded**; `Math.sqrt` compiles to `sqrtsd` and `StrictMath.sqrt` is the same value; Nim's `sqrt` is the same instruction. Measured: **0 of 20 000 000** disagreements. Patched to `StrictMath` anyway, so the invariant "no `Math.` transcendental survives on a gameplay path" is a one-line `grep` in CI |
| `Math.toDegrees` | **3** (one only in `toString`) | `Direction.java:172`, `:258`, `:269` | **(a)** | the JDK method **is** `angrad * 180.0 / PI` — two exactly-specified double operations on a double literal |
| `Math.toRadians` | **2** | `Direction.java:194`, `:206` | **(a)** | `angdeg / 180.0 * PI`, likewise. **This one is load-bearing**: it is how `rotateLeftDegrees(i × 20)` and `(i × 15)` turn a triad and a pentad spread into radians |
| `Math.ceil` | **2** | `Direction.java:275`, `:278` | **(a)** | exactly specified (a rounding function), and its argument here is a double expression |
| `Math.floor` | **1** | `RobotControllerImpl.java:1180` | **(a)** | exactly specified; it is the victory-point conversion |
| `Math.abs` | **2** | `Direction.java:69`, `InternalBullet.java:183` | **(a)** | a sign-bit clear |
| `Math.min` | **3** | `InternalRobot.java:220`, `RobotControllerImpl.java:531`, `:563` | **(a)** | exactly specified |
| `Math.max` | **5** | `InternalRobot.java:228`, `RobotControllerImpl.java:531`, `:563`, `GameWorld.java:264`, `:266` | **(a)** | exactly specified. `GameWorld:264,266` is the bullet-income floor |
| `Math.PI` | **7** | `Direction.java:182`, `:275`(×2), `:276`, `:277`, `:278`, `:279` | **(a)** | a `double` constant, and **`(float)Math.PI` is a different value from `Math.PI`** — the port must keep the two apart exactly where the engine does (`reduce` compares against `(float)Math.PI` and then corrects with `Math.PI*2*circles` in double) |
| **`Math.random`** | **0** | — | — | **there is none.** `grep -rn 'Math\.random'` over `battlecode/{common,world,util,server}` returns nothing; the only `Math.random` in the whole repository is in the *scaffold bot*, which this note patches (§Decisions) |
| **`Math.pow` / `exp` / `log` / `log10` / `hypot` / `cbrt` / `sinh…` / `StrictMath.*`** | **0** | — | — | **there are none anywhere in the gameplay tree.** So the fdlibm surface bc17 needs is exactly `{sin, cos, atan2}` |

**F2 — `tools/oracle/bc17/strictmath.patch`: eleven call sites, three files, and it is a NORMALISATION, not a rules
change.** It rewrites `Math.atan2/sin/cos/sqrt` to `StrictMath.*` in `common/Direction.java` (3 sites),
`common/MapLocation.java` (5) and `world/InternalBullet.java` (3) and **touches nothing else** — `abs`, `min`, `max`,
`floor`, `ceil`, `toDegrees`, `toRadians` and `Math.PI` are left exactly as they are — and `build_oracle.sh` asserts
exactly **eleven** changed lines and that `grep -c 'Math\.\(sin\|cos\|atan2\|sqrt\)'` over the three files is **0**
afterwards. **Why this is legitimate**: the 20 000 000-sample measurement shows the patch cannot change any value the
*game* observes, because every one of those eleven results is narrowed to `float32` before it reaches any state and at
`float32` the patched and unpatched engines agreed in every sample. What it buys is that the residual risk — a
double-level difference of ≤ 1 ulp straddling a `float32` rounding boundary, which the measurement bounds under 1 in
2 × 10⁷ per call and arithmetic puts at ≈ 7 × 10⁻¹¹ — becomes **exactly zero**, which is the difference between
"parity holds in most games" and "parity holds". `docs/PARITY.md` §bc17 says so with the measurement, and names the
patch as one of exactly **three** places the oracle is not the published engine.

**F3 — the width table. Java's numeric promotion is replicated PER EXPRESSION, taken from the Java text and never
from taste.** These are the shapes that differ from each other in the same codebase, which is why they are tabled:

| expression | engine site | evaluated as |
|---|---|---|
| `new Direction(dx, dy)` | `Direction.java:86` | `radians: float32 = reduce( (float32) atan2( (float64)dy, (float64)dx ) )` — **`dy` first** |
| `reduce(rads)` wrap branch | `:274-280` | compare `rads <= −(float32)PI`; `circles: int = (int) ceil( (float64)(−(rads + PI)) / (2×PI) )` — **the add and the divide in float64**; result `= rads + (float32)(PI × 2 × circles)` — **a float32 add of a float32-narrowed float64 product** |
| `radiansBetween(other)` | `:244-246` | `reduce( (float32)(other.radians − this.radians) )` — a **float32** subtract, then the mixed-width `reduce` |
| `getDeltaX(travelDist)` | `:149-151` | `(float32)( (float64)travelDist × cos((float64)radians) )` — **the product in float64, narrowed once** |
| `MapLocation.add(dir)` | `MapLocation.java:240-242` | `dx = (float32) cos(radians)`; `x + dx` in **float32** — **the cosine is narrowed BEFORE the add** |
| `MapLocation.add(dir, dist)` | `:276-278` | `dx = (float32)( (float64)dist × cos(radians) )`; `x + dx` in float32 — **a different shape from `add(dir)` in the same class** |
| `distanceTo(loc)` | `:131-135` | `dx = (float32)(x − loc.x)`; `(float32) sqrt( (float64)(dx×dx + dy×dy) )` — **the two products and the sum in float32**, only the sqrt widened |
| `distanceSquaredTo(loc)` | `:146-150` | entirely **float32** |
| `perpDist` | `InternalBullet.java:183` | `(float32)| (float64)distToTarget × sin((float64)radiansBetween) |` — **product in float64** |
| `hitDist` | `:190` | `distToTarget × (float32) cos(radiansBetween)` — **cosine narrowed FIRST, product in float32.** The two lines seven apart in the same method have **opposite** shapes, and this is the single most likely place for the port to diverge |
| `halfChordDist` | `:189` | `(float32) sqrt( (float64)( (float32)(targetRadius×targetRadius) − (float32)(perpDist×perpDist) ) )` |
| bullet income | `GameWorld.java:264-267` | `(float32) max(0f, 2f − 0.01f × supply)` — **all float32**, and `0.01f × supply` is a float32 product |
| tree income | `InternalTree.java:173` | `health × (1f/50f)` in **float32**; the constant is `BULLET_TREE_BULLET_PRODUCTION_RATE`, i.e. **`1f/50f` computed at class-init**, not the literal `0.02f` — the two are the same float32 here, and `tests/test_bc17_arith.nim` asserts it rather than assuming it |
| `totalTreeSupply` | `GameWorld.java:121-124` | a **float32** running sum over trees **in trove order** (D1) |
| VP conversion | `RobotControllerImpl.java:1173,1180` | `price = (float32)(7.5f + 0.0041666666f × roundNum)`; `gained = (int) floor( (float64)(bullets / price) )` — **the divide in float32**, the floor on the widened result |
| tiebreak rung 3 | `GameWorld.java:294-306` | a **float32** running sum seeded with `getBulletSupply(t)`, adding `(float32)type.bulletCost` per live robot |
| `repairRobot` | `InternalRobot.java:220` | `min(health + healAmount, (float32)maxHealth)` in float32, where `healAmount = 0.04f × (float32)maxHealth` |
| `points[t]` | ours | three `float32` shares, `float32` weights, one truncating `int()` (§The game, Scoring) |

`tests/test_bc17_widths.nim` asserts **one named vector per row of that table**, taken from
`data/bc17/fdlibm_vectors.json`, so a port that gets a width wrong fails a unit test rather than a 2 999-round trace
diff.

**F4 — the fdlibm port, and how it is pinned.** `src/battlecode/fdlibm.nim` gains four procs and one helper, all
additive:

- **`fdlibmAtan2(y, x: float64): float64`** — `__ieee754_atan2` in full (the sign/zero/inf table, the
  `atan(y/x)` core with its `atanhi`/`atanlo` and the eleven-coefficient odd polynomial), because the argument domain
  is unrestricted: `dx`, `dy` are arbitrary float32 deltas including ±0, denormals and equal magnitudes.
- **`fdlibmSin(x: float64): float64` / `fdlibmCos(x: float64): float64`** — `__kernel_sin` and `__kernel_cos` over the
  reduced argument, plus **`remPio2Medium`**, the *medium-size* branch of `__ieee754_rem_pio2` (`|x| < 2¹⁹ × π/2`)
  with its `pio2_1/pio2_1t`, `pio2_2/pio2_2t`, `pio2_3/pio2_3t` corrections and its `n` recomputation.
  **Why only the medium branch is needed, and why that is safe:** the engine calls `sin`/`cos` **only** on
  `Direction.radians`, which `reduce()` guarantees lies in **(−π, π]** (`Direction.java:41-44, 273-282` — every
  constructor and every rotation goes through it), so `|x| ≤ π` and `n ∈ {−2 … 2}`. **`fdlibmSin`/`fdlibmCos` raise a
  `Defect` on any argument outside `[−4, 4]`**, so a future caller cannot silently take an unimplemented path; the
  Payne–Hanek branch is named in `docs/RULES-BC17.md` §Divergences as *not implemented and not reachable*.
- `fdlibmExp` is **untouched**, so no bc16 recording changes meaning.

The pin is **`data/bc17/fdlibm_vectors.json`**, produced by `tools/JavaBc17Tables.java` under the CI **JDK 8** and
byte-diffed by Tier B:

1. **Every boundary vector explicitly** (≈ 400 rows): `±0.0`, `±(float)π`, `nextUp/nextDown((float)π)`, `±(float)π/2`,
   `±(float)π/4`, `±3(float)π/4`, the smallest normal and subnormal float32, `±2^k` for `k ∈ [−30, 7]`, the eight
   cardinals' exact radians, their triad and pentad rotations, and the `(dy, dx)` pairs `{(0,±1), (±1,0), (±1,±1),
   (0,0)}` the engine's own `Direction.getNorth/East/South/West` produce.
2. **A 2 000 000-point sample of the real domains**, by a **recipe both sides run**: `java.util.Random(20170101)`
   drawing `dx = (nextFloat() − 0.5f) × 200f`, `dy` likewise, `radians = (float) atan2(dy, dx)` — and the file commits
   **only the sha256 of the canonical byte stream** `(bits(dx), bits(dy), bits(result))…` for each of F3's eleven
   expression shapes, so the artefact stays a few KB while the gate covers two million points. `rng.nim`'s
   `java.util.Random` is what lets the Nim side draw the identical sample.
3. `tests/test_bc17_fdlibm.nim` recomputes both and **additionally asserts that `fdlibmSin(x) == sin(x)` fails for at
   least one x in the sample** — i.e. that the port is really fdlibm and not a platform-libm wrapper that agrees
   today.

**F5 — what is left, and why it cannot bite.** After F1–F4 the only floating-point facts the port depends on are
(i) IEEE-754 `+ − × ÷ sqrt` and comparison, which are exactly specified and identical on x86-64 SSE2 and wasm32;
(ii) `float64 → float32` narrowing, which is round-to-nearest-even and specified; and (iii) the fdlibm algorithm,
which is pinned by F4 against the pinned JDK. **There is no accumulation whose order is unspecified** — the one
order-sensitive sum in the game (`totalTreeSupply`) is reproduced exactly by D1, and the one that is not
order-sensitive (tiebreak rung 3) is proved so in §The game rule 9.4. **So Tier C is NOT gated on a subset of maps**,
which is where this note departs from the idea's expectation, and the ledger is expected to be **empty**.

### Determinism

- **D1 — `gnu.trove.map.hash.TIntObjectHashMap`'s iteration order is REPRODUCED, not replaced, because it is
  observable in exactly two places.** `ObjectInfo.eachRobot/eachTree/eachBullet` are `forEachValue`
  (`ObjectInfo.java:90-120`) and the comment at `:110` says it out loud: *"ordered based on robot ID hash (effectively
  random)"*. Measured on the jar's own classes **and cross-checked against the live engine**: a fresh map has capacity
  **23**, `HashFunctions.hash(int)` is the identity, the slot is `hash % length`, and `forEachValue` walks
  **high index → low**; ids `{2,3,4,5}` give `5 4 3 2` and ids `{14,15,16,17,34,35}` give `17 16 15 14 35 34`, which
  is exactly what `GameWorld`'s own `eachRobot` printed on `GiantForest`. **The two observable consequences:**
  (i) **`updateTrees`'s `float32` accumulation** `totalTreeSupply[team] += tree.updateTree()`
  (`GameWorld.java:121-124`) — the sum's last bits depend on the order, and the sum lands in the bullet supply that
  `donate`'s integer floor and every affordability comparison read (the spec claims this order does not matter — docs
  disagreement 6; it does); and (ii) **`previousBroadcasters = currentBroadcasters.values(new RobotInfo[size])`**
  (`:455-457`), the array `senseBroadcastingRobotLocations()` hands a chassis — **so the order is visible to the bot
  and therefore to the game** — where `clear()` **retains the table's capacity** (measured, 397 → 397), so the layout
  in round R depends on the historical peak broadcaster count and must be carried across rounds.
  `years/bc17/trove.nim` therefore ports: the 245-entry `PrimeFinder` ladder, `THash(10, 0.5f)` →
  `setUp(fastCeil(10/0.5f)) = setUp(20)` → `nextPrime(20) = 23`, `computeMaxSize`, the `1 + (hash % (length − 2))`
  downward probe with wrap, `insertKeyRehash`'s first-`REMOVED`-slot rule, `postInsertHook`'s two rehash triggers,
  `removeAt`'s **auto-compaction** countdown, `compact()`, `rehash()`'s descending re-insert, `values(V[])`,
  **`forEachValue`** and **`clear()` with capacity retained**. **Two deliberate differences from
  `years/bc22/trove.nim`, and they are why bc17 ships its own copy rather than importing bc22's:** (a) bc22 only ever
  calls `values(V[])` on a *snapshot*, so it never had to model iteration over a mutating table, while bc17's
  `forEachValue` walks a table that `destroyTree`/`destroyRobot` mutate — **measured, a removal that triggers
  auto-compaction leaves the walk on the PRE-compaction arrays** (40 of 40 values visited while 20 were removed and
  the capacity shrank 97 → 67), so the port models `keys`/`states` as **`ref seq`** and `rehash` **allocates new
  ones**, exactly as Java assigns new arrays and leaves the iterator's references on the old ones; and (b) bc22's file
  has no `clear()`. `tests/test_bc17_trove.nim` replays 500 random sequences against a recorded oracle order **and
  asserts the two files agree on `values(V[])` for the same sequence**, so the copy cannot drift.
  **Where the order is NOT observable, said explicitly so nobody ports it for safety:**
  `processBeginningOfRound`'s `healthChanged = false` sweeps, `processEndOfRound`'s replay-only sweeps and the tree
  `roundsAlive` increment. **And the compaction-during-iteration effect is itself unobservable in `updateTrees`**,
  because during that pass a tree is only ever removed by *its own* visit and therefore never revisited — a proof, not
  a hope, and the test asserts the pass visits every tree exactly once even when a third of them die in one round.
  **`gnu.trove.list.array.TIntArrayList`** is modelled too: `insert(i, v)` inserts **before** index `i`, and
  **`remove(int)` removes by VALUE** (both measured).
- **D2 — the `net.sf.jsi` R-tree is NOT ported; the candidate order is normalised on BOTH sides.** Every spatial query
  goes through `SpatialIndex.nearestN(point, procedure, Integer.MAX_VALUE, radius)` (`ObjectInfo.java:328-442`).
  Measured: **`nearestN` delivers entries in ascending distance from the query point** (200 random points, 200/200
  ascending), because it fills a descending priority queue and then calls `setSortOrder(ASCENDING)` and pops. **But
  for exact ties the order is an artefact of the R-tree's node layout and the queue's heapify, and it is not even
  stable under a delete-and-re-add of the same point set** — the same five points gave two different orders in the
  same process. Reproducing it means porting jsi's R-tree with its split heuristics **and** jsi's `PriorityQueue`'s
  heapify, and then depending on both forever. **Decision: the port enumerates candidates from `index.nim`'s uniform
  grid, applies the engine's own `isWithinDistance` filter, and orders them by `(distanceSquaredTo(query) ascending,
  id ascending)` — computed with `MapLocation.distanceSquaredTo`'s exact float32 expression — and
  `tools/oracle/bc17/rtree_order.patch` replaces ObjectInfo's six `nearestN` call sites with the SAME enumeration on
  the ENGINE side.** The normalisation is symmetric; neither trace is massaged alone; the patch is one hunk in one
  file; `build_oracle.sh` asserts it applied and that `grep -c nearestN` over the patched file is 0.
  **Where the order is observable, exhaustively:** (i) the two strict-minimum `hitDist` loops in `updateBullet`
  (rule 5.7, 5.8) — **ties only**; (ii) the tank's closest-tree pick (rule 6) — **ties only**; (iii)
  `getRobotAtLocation` / `getTreeAtLocation`, which return the **first** match (the muzzle check and
  `senseRobotAtLocation`), where at most one body can contain a point unless a SCOUT is on a tree — **ties only**; and
  (iv) **the ORDER of the array `senseNearbyRobots`/`Trees`/`Bullets` hands the chassis** — fully order-dependent, and
  the reason the normalisation must be *ascending distance* rather than merely a tie-break, because
  `examplefuncsplayer17` fires at `robots[0]` and that must be the nearest enemy on both sides. Where it is **not**
  observable: `strike()` (every candidate is damaged), `destroyTree`'s scout scan (every overlapping scout dies) and
  `isEmpty`/`noRobotsExceptForRobot` (a length test).
- **D3 — `java.util.Random`, two instances, both seeded with the MAP seed, drawn only at block allocation.** This is
  the **entire** RNG surface of the 2017 engine and it is smaller than any other year here. `GameWorld:48-50`
  constructs `idGenerator = new IDGenerator(gm.getSeed())` and `bulletIdGenerator = new IDGenerator(gm.getSeed())`
  followed by `bulletIdGenerator.setStart(MAX_ROBOT_ID+1)`. `IDGenerator` reserves **4 096-id blocks** from
  `MIN_ID = 10000` (`reservedIDs[i] = nextIDBlock + i + 1`, so the first block is **10 001 … 14 096**),
  **Fisher–Yates shuffles each block from `i = 4095` down to 1 with `random.nextInt(i+1)`**, and hands ids out from
  the shuffled array, allocating a new block when the cursor reaches 4 096. **Three consequences the port must get
  exactly right:** (i) **the bullet generator has consumed TWO blocks' worth of shuffles before its first id**,
  because `setStart` calls `allocateNextBlock` and the constructor already did (2 × 4 095 = 8 190 draws), and its
  first block is **32 002 … 36 097**; (ii) **no draw happens per spawn** — the id stream is a pure function of the
  seed and the spawn *count*, so a build the port refuses and the engine accepts shifts nothing until the 4 096th
  spawn; and (iii) initial bodies take their ids **from the map file, not the generator** (measured: `Barrier` 2–5,
  `GiantForest` 14–17 and 34–35), and `LiveMap`'s constructor **sorts all initial bodies by id**
  (`LiveMap.java:67`), which fixes the opening exec order. `GameWorld:39,62` also constructs a third `Random(seed)` —
  **`GameWorld.rand`, which is written and NEVER READ** (`grep -n rand GameWorld.java` finds the declaration and the
  assignment and nothing else). It is **not** ported, and `docs/RULES-BC17.md` says so, so nobody adds a stream to be
  safe. `tests/test_bc17_ids.nim` pins the first 8 robot and first 8 bullet ids for the three seeds measured here
  (`Barrier` seed 98 → `13527, 10137, 10443, 12235, 13581, 11621, 11304, 11839` and `33728, 35734, 33147, 32964,
  35666, 34517, 34646, 34056`; `Conga` 752; `GiantForest` 753) and pins the second-block boundary.
- **D4 — the exec order is an ARRAY and that is all it is** (§Feasibility, "Turn order"; `ObjectInfo.java:42,132-155,
  254,268-269,311,320`). `years/bc17/world.nim` keeps one `seq[int]`, appends robots, `insert`s bullets at
  `find(parentId)`, removes **by value**, and **snapshots the seq before every round's sweep**. A body spawned during
  round R is therefore not in round R's snapshot and does not act until R+1 — which is what makes rule 4.2's
  20-round dormancy a *separate* rule rather than the same one.
- **D5 — every engine-visible quantity is `float32`, and the port's types say so.** Health, bullet supply, radii,
  stride, bullet speed, attack power, damage, coordinates, radians and the tree arithmetic are all `float32`; victory
  points, round numbers, ids, counters and channel values are `int`. **No `float` is ever widened except where the
  engine widens it** (F3), and `tests/test_bc17_arith.nim` greps `src/battlecode/years/bc17/**` for a bare `float` or
  `float64` declaration outside `geom.nim`'s explicit double intermediates and fails on a hit.
**Every round appends to a hash chain**; the viewer re-derives each round and compares, exposing `bc_mismatch_round`.
The values folded in each round — **thirteen per team plus eleven globals**, so a re-derivation that diverged in only
one of them cannot reproduce the chain (the GV02 lesson): per team, archons / gardeners / lumberjacks / soldiers /
tanks / scouts / bullet trees alive, **the bullet supply's raw 32 bits**, victory points, robots built, robots lost,
trees planted, trees lost; globally, the round number, an FNV-1a 64 fold of the exec-order list **in exec order** and
its length, the same fold of `(id, bits(x), bits(y), bits(health))` over every live robot **in exec order**, over every
live tree **in trove order** and over every live bullet **in exec order**, the live bullet count, the ids issued by
each of the two generators and both cursors. **Folding the raw bullet-supply bits rather than a rounded value is a
bc17-specific decision and the cheapest possible tripwire for a float divergence**: one wrong ulp in the tree-income
sum shows up on the round it happens instead of as a mystery 400 rounds later.

Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record** (`plan.abandonAfter[g]`)
applied by the same proc on record and on playback — the particle-worlds scar — and the record→re-derive test covers
**every** bc17 end reason, not just `complete`.

**`GameVersion` bumps to `GV13`** in the same commit, with a prepend-only changelog line: *"the `bc17` year module:
Battlecode 2017 'Robotic Wildlife Fund' ported from battlecode-server-2017 at commit 165d8a8e (oracle jar
2017.1.6.2, `SPEC_VERSION` 1.0) — THE FIRST CONTINUOUS-SPACE YEAR: float32 coordinates and circular bodies, the
ten-step round loop whose second phase moves BULLETS and whose third updates trees, travelling bullets with
segment/circle collision and no team check, the six unit types with their float32 radii, strides, bullet speeds and
attack powers, the 20-round dormancy of a built unit at 20 % health healing 4 % a turn, bullet trees at
`health × 1/50` a round with 0.5 decay and +5 watering and an 81-round maturity, neutral trees at 200 × radius HP
holding bullets and robots that only a chop releases, the lumberjack strike hitting everything within distance 2 with
no team check, the tank body attack, the four-rung ladder at round 2 999, and victory points bought at
`7.5 + round × 12.5/3000` bullets with 1 000 ending the game the instant the donation lands, behind
`game_config.year`. The transcendental surface is `{sin, cos, atan2}` and it is ported from fdlibm into
`src/battlecode/fdlibm.nim` and pinned against the JVM's own `StrictMath`; the trove iteration order is reproduced
because the tree-income sum is float32 and order-dependent; the jsi R-tree candidate order is normalised to
(distance, id) on BOTH sides. Bytecode metering is replaced by a fixed DecisionOps budget (a documented divergence
whose only effect is how much the chassis got to think: in 2017 the bytecode count has NO effect on any rule). bc16,
bc19, bc20, bc21, bc22, bc23, bc24, bc25 AND bc26 SEMANTICS ARE UNCHANGED: no GV04..GV12 recording carries a byte
whose meaning changed — this run makes no year-neutral behaviour change at all, and `fdlibm.nim` is extended
additively — which is why `ReplayCompatibleGameVersions` is EXTENDED rather than reset and every hosted replay keeps
rendering."*
**`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06","GV07","GV08","GV09","GV10","GV11","GV12", GV13]`** —
extended, never reset. `tools/ci/check_gameversion.sh` claims the version across branches; **it compares the headline,
not the digits, so if a sibling branch lands GV13 first this branch rebases to GV14 and extends the list again** (the
bc20 precedent). **And phase 20 regenerates every committed replay fixture in the same commit** (§Interface facts).

### Decided divergences — every rule this port does NOT reproduce, with its reason

| # | Divergence | Reason |
|---|---|---|
| **V1** | **Bytecode metering is not ported.** The engine gives each robot a per-turn bytecode limit (`ARCHON` 30 000, everything else 15 000, `RobotType.java`), **pauses** the robot's thread when it runs out and **resumes it mid-computation next round** (`InternalRobot.getBytecodeLimit:293-295`, `PlayerControlProvider.runRobot:129-140`, spec §22 "Timing"), and charges 500 bytecodes for a thrown exception. It is replaced by a fixed **`DecisionOps`** budget (below) whose per-turn charge is a pure compute cap: the robot's turn **ends where it stands** rather than resuming. **The reason this divergence is far weaker here than in bc16 is worth stating: in 2017 the bytecode count has ZERO effect on any rule.** `bytecodesUsed` is stored and handed to `matchMaker.addBytecodes` (replay telemetry) and `prevBytecodesUsed` is written and never read by any gameplay path — verified by reading `GameWorld` and `RobotControllerImpl` in full. So the only thing the limit decides is *how much the chassis got to think*, and the port's cap is **provably non-binding** for both chassis (below). Tier B′ proves the engine's own pause never fired in any compared game. |
| **V2** | **The flatbuffer layer, the server and the client have no port**: `battlecode/schema/*`, `server/GameMaker` (the `.bc17` match writer), `server/NetServer`, `server/Server`, `server/Config`, `world/GameMapIO`'s writer, the whole `instrumenter/` tree and `battlecode-client-17`'s code. The **map reader** is reproduced at BUILD time by `tools/convert_maps_bc17.py`, which walks the `.map17` flatbuffers out of the pinned jar and commits JSON; the runtime sim contains **no flatbuffer reader** and there are **no `.bc17` bytes anywhere**. The replay is this repo's own self-sufficient UTF-8 JSON re-derived by the wasm sim (§Server). `setIndicatorDot`/`setIndicatorLine` are debug-only and are not ported. |
| **V3** | **The robot id pool cannot collide with the bullet id pool.** `IDGenerator` **never checks `MAX_ROBOT_ID`**: after five blocks the robot ids reach 30 481–34 576 and overlap the bullet space that starts at 32 002, and `ObjectInfo`'s own comment (`:137-138`) names the hazard — *"This can produce bugs if a bullet and a robot can have the same ID"*. The port reproduces the generator exactly and adds **one guard the engine lacks**: a `hire`/`build` that would issue an id above **32 000** is **refused** (a no-op counted in `builds_refused` and `refused_actions`). Derived ceiling: reaching it needs **≈ 22 000 robots**, i.e. ≈ 2.2 M bullets, while the richest played map's tree income over 2 999 rounds is under 1.5 M — so the floor is not reached in practice; the guard exists because "degrade, never hang" outranks fidelity to a collision. |
| **V4** | **Team memory is inert.** `TeamInfo`'s `oldTeamMemory` is whatever the previous game left (`GameWorld` takes it as a constructor argument) and `setTeamMemory`/`getTeamMemory` are the API. In this coworld **every game is independent** — the doctrine model has no cross-game channel — so the port keeps a zero-filled 32-long array per team that a chassis may write and reads back as zeros, and `orchard` never touches it. Recorded, not silently dropped. |
| **V5** | **`runRound`'s blanket `catch (Exception)`** (`GameWorld.java:110-113`) ends the game with **no winner and no domination factor** and returns `DONE`. The port reproduces the *effect* — the game stops — as **`results.reason = fault` with `scores = [0, 0]` and a partial replay**, because a coworld episode has to report something. Two engine paths can reach it and **neither is reachable here**: `resign()` iterating a mutating trove map, and a tree destroyed twice in one `updateTrees` pass (proved unreachable in D1). `tests/test_bc17_endladder.nim` asserts no gate game ever reports `fault`. |
| **V6** | **`resign()` is unreachable** (no chassis calls it and no sheet value selects it), **`Clock.getBytecodeNum`/`getBytecodesLeft` are replaced** by the `DecisionOps` counters, and the fdlibm **Payne–Hanek** branch of `__ieee754_rem_pio2` is **not implemented** because `Direction.radians` is always in (−π, π] — the port raises rather than guessing (F4). |

### The chassis, the DecisionOps budget, and the pause divergence (V1)

**The numbers, taken from the engine's own limits at the repo's standing one-tenth convention** (bc16 used 2 000 /
1 000 against Java's 20 000 / 10 000; bc20–bc26 the same shape):

| quantity | value | from |
|---|---|---|
| `OpsPerBytecode` | **1/10** | the convention, so the numbers read straight off the engine's own limits |
| `ArchonOps` | **3 000** | `ARCHON.bytecodeLimit = 30 000` |
| `UnitOps` | **1 500** | `15 000` for GARDENER, LUMBERJACK, SOLDIER, TANK and SCOUT |
| `DormantOps` | **0** | **not the divergence — the RULE.** `getBytecodeLimit()` returns 0 unless `canExecuteCode()`, i.e. `health > 0 && (isBuildable() ? roundsAlive >= 20 : true)` |

One credit is charged for each: body examined in a candidate query, grid cell scanned, farm slot scored, direction
evaluated in the `tryMove` probe, bullet tested by `willCollideWithMe`, target scored, broadcast channel read, and
tree scored for watering or chopping. Credits are deducted inside `kit.nim` and **enforced by the sim, not by the
bot**.

**Reachable or unreachable, decided by construction, with the test that proves each:**

- **The dormancy gate is REACHABLE in every single game and is a ported rule.** Every fighter is born at
  `0.2 × maxHealth` and gets **0 ops for exactly 20 turns** while `processBeginningOfTurn` heals it
  `0.04 × maxHealth` a turn — so a SOLDIER goes 10 → 50 HP over 20 turns and acts on turn 21.
  `tests/test_bc17_clock.nim` asserts a built SOLDIER emits **no action at all** on turns 1–20, has health
  `10, 12, 14, … 50` on those turns (a named vector per turn), and acts on turn 21; and asserts a hired GARDENER is
  born at **40/40** and acts on its **second** round (it is not `isBuildable`, so its gate is only the exec-order
  snapshot).
- **The op cap is UNREACHABLE by construction for both shipped chassis.** `orchard`'s heaviest turn is a GARDENER's:
  six farm-slot clearance queries over ≤ 40 grid candidates each (240), one sense sweep over ≤ 60 bodies (60), the
  water scan over ≤ 8 own trees (8), the build decision (≤ 30) and the `tryMove` probe (7 directions × ≤ 40
  candidates = 280) — **≈ 620 ops against a cap of 1 500**; an ARCHON's is ≈ 900 against 3 000; a SOLDIER's, with the
  bullet-threat set over ≤ 40 sensed bullets, ≈ 700. `examplefuncsplayer17`'s heaviest turn is one
  `senseNearbyRobots` plus a seven-direction `canMove` probe, **≈ 120 ops**. `results.games[].decision_ops_peak`
  records the measured maximum per game and **`tests/test_bc17_clock.nim` asserts it stays below the cap in every gate
  game**, so the cap is not merely generous, it is demonstrably non-binding. **And when it is reached the turn ends
  deterministically** — the cap is checked **before** each primitive and never inside one, so a primitive's *result*
  is never a function of the remaining budget, only whether the chassis got to ask; a synthetic chassis asking for
  5 000 ops is asserted to have its turn end at the cap with the world unchanged and no partial primitive.
- **On the oracle side the engine's own pause is proved never to fire**: every bot in the parity job asserts
  `Clock.getBytecodesLeft() > 5000` at the end of every turn and `System.exit(4)` otherwise (Tier B′), so
  `bytecodesUsed < limit − 5000` on every compared turn and the resume path is provably not exercised.

**Why the charge may not be the chassis's real op count**, logged here so it is not re-litigated: nothing in the 2017
rules reads the bytecode count, so there is no rule whose input this could be — unlike bc16, where the delay decay
read it and pinning it to 1.0 was a *rules* decision. Here the budget is purely a compute cap, which is why V1 is the
weakest of the ten years' metering divergences and why `docs/PARITY.md` §bc17 can say plainly that **the only
behaviour this oracle cannot compare is how much thinking each side got, and no rule reads that.**

### Maps — converted at build time from the jar's own resources, and measured here

**All 70 official maps were parsed in this sandbox** and the table below is those measurements. The engine's map format
is a **flatbuffer** (`.map17`): `GameMap{name:string, minCorner:Vec, maxCorner:Vec, bodies:SpawnedBodyTable,
trees:NeutralTreeTable, randomSeed:int}`, where `SpawnedBodyTable{robotIDs:[int], teamIDs:[byte], types:[BodyType],
locs:VecTable}` and `NeutralTreeTable{robotIDs:[int], locs:VecTable, radii:[float], containedBullets:[int],
containedBodies:[BodyType], healths:[float], maxHealths:[float]}`. `tools/convert_maps_bc17.py` walks it with the same
hand-rolled vtable reader `tools/convert_maps_bc23.py` already uses (plus a `float32` vector accessor) and writes
`data/maps/bc17/<Name>.json` carrying `name`, `width = maxCorner.x − minCorner.x`, `height`, `origin`, `seed`,
`rounds: 3000`, and the initial bodies **sorted by id, exactly as `LiveMap`'s constructor sorts them**
(`LiveMap.java:67`) — because that sort fixes the opening exec order. **Two conversion rules taken from the engine
rather than from the file**: a neutral tree's health is **recomputed** as `200 × radius` and the file's own `healths`
and `maxHealths` vectors are **ignored** (`GameMapIO.java:389-400` computes it and only warns on mismatch), and
`rounds` is **always 3 000** regardless of anything in the file (docs disagreement 1). The 22 converted maps are
**committed**, CI **re-runs the converter with `--check` and byte-diffs**, and Tier B additionally cross-checks each
one against the JVM's own `LiveMap` fields.

`trees` is the neutral-tree count; `Σr` their total radius (the honest measure of how much of the board is wall);
`r∈` their radius range; `bul`/`rob` how many of them contain bullets or a robot; `arch` archons **per side**
(always equal — measured on all 70); `sep` the minimum distance between an opposing archon pair; `sym` the symmetry
class the archon roster satisfies (`H` horizontal, `V` vertical, `R` rotational).

| pool | map | size | seed | arch | trees | Σr | r∈ | bul | rob | sep | sym |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `small` | `CropCircles` | 30×30 | 982 | **1** | 198 | 99.0 | 0.50 | 190 | 0 | 33.9 | R |
| `small` | `GreenHouse` | 30×30 | 713 | **1** | 58 | 58.0 | 1.00 | 56 | **58** | 20.1 | R |
| `small` | `HiddenTunnel` | 30×30 | 143 | **1** | 484 | 242.0 | 0.50 | 458 | 0 | 25.2 | R |
| `small` | `HouseDivided` | 30×30 | 937 | **1** | 41 | 40.9 | 0.96–1.00 | 41 | 6 | **6.5** | HR |
| `small` | `OMGTree` | 30×30 | 131 | **1** | **1** | 10.0 | **10.00** | 0 | 0 | 24.6 | V |
| `small` | `shrine` | 30×30 | 774 | **1** | **1** | 2.0 | 2.00 | 1 | 1 | 36.7 | R |
| `mixed` | `Aligned` | 42×40 | 82 | **1** | 202 | 202.0 | 1.00 | 190 | 0 | 37.6 | H |
| `mixed` | `Barrier` | 60×60 | 98 | **2** | 22 | 66.0 | 3.00 | 22 | 0 | 40.0 | HR |
| `mixed` | `Blitzkrieg` | 60×40 | 410 | **3** | 180 | 99.0 | 0.50–2.00 | 168 | 6 | 50.0 | HR |
| `mixed` | `Chess` | 64×64 | 787 | **2** | **924** | 504.0 | 0.50–2.00 | 892 | 28 | 56.0 | HR |
| `mixed` | `Cramped` | 50×50 | 192 | **1** | 44 | 89.7 | 1.99–2.50 | 0 | 4 | **5.0** | HR |
| `mixed` | `DenseForest` | 50×50 | 788 | **2** | 46 | 92.0 | 2.00 | 46 | 0 | 15.1 | R |
| `mixed` | `Hurdle` | 50×50 | 535 | **1** | 16 | 32.0 | 2.00 | 16 | 0 | 40.0 | V |
| `mixed` | `Snowflake` | 60×60 | 808 | **3** | 89 | 127.7 | 0.88–2.40 | 22 | 0 | 26.4 | R |
| `mixed` | `TreeFarm` | 52×52 | 277 | **1** | 142 | 142.0 | 1.00 | 140 | 0 | 56.9 | R |
| `mixed` | `Waves` | 60×50 | 145 | **2** | 142 | 127.4 | 0.58–1.73 | 0 | 0 | 12.0 | R |
| `large` | `Alone` | **100×100** | 610 | **1** | **0** | 0.0 | — | 0 | 0 | **127.3** | R |
| `large` | `GiantForest` | **100×100** | 753 | **3** | 10 | 100.0 | **10.00** | 10 | 0 | 56.0 | R |
| `large` | `Interference` | **100×100** | 289 | **3** | 394 | 394.0 | 1.00 | 376 | 0 | **8.5** | R |
| `large` | `LineOfFire` | 100×30 | 116 | **2** | **1 228** | 620.0 | 0.50–2.00 | 2 | 4 | 95.0 | HR |
| `large` | `Maniple` | 100×60 | 444 | **3** | 406 | 406.0 | 1.00 | 0 | **406** | 50.0 | VR |
| `large` | `Whirligig` | **100×100** | 149 | **3** | 476 | 476.0 | 1.00 | 466 | 0 | 26.1 | R |

`mixed` (**10 maps**) is the `bc17` variant's played pool; `small` (**6**) is the pool the parity oracle and the docker
smoke run on; `large` (**6**) is reserved for a later variant and **supplies one of the nine parity pairs**. The
`mixed` pool spans the axes the doctrines argue about: **archons per side 1, 2 and 3**; **neutral trees from 16
(`Hurdle`) to 924 (`Chess`)**, which is the axis `chop_policy` and `lumberjack_share` live on; **trees holding
bullets from 0 (`Cramped`, `Waves`) to 892 (`Chess`)**, the axis `shake_neutral_trees` lives on; **archon separation
from 5.0 (`Cramped`) to 56.9 (`TreeFarm`)** — exactly the axis `opening: tank_rush` lives on, since a TANK strides
0.5 and needs ~10 rounds to cross 5 and ~114 to cross 57; and **board area from 1 680 (`Blitzkrieg`) to 4 096
(`Chess`)**. One map would rank the map, not the doctrine.

**The nine parity pairs** are the six `small` maps plus `Chess` and `Cramped` from `mixed` and `Alone` from `large`,
chosen to cover every branch of every rule that has one:

| pair map | what it is the only cover for |
|---|---|
| `CropCircles` | **198 radius-0.5 trees on the smallest board** — the densest small-tree packing, so the bullet candidate loop and the `perpDist` rejection run hot from round 1 |
| `GreenHouse` | **every one of its 58 trees contains a robot and 56 contain bullets** — the chop-release path, the scout-crush rule and `shake` all fire, and it is the only pair where a faction can grow by chopping |
| `HiddenTunnel` | **484 radius-0.5 trees** — the maximum candidate count per bullet update on a small board, and the `clear_path` case |
| `HouseDivided` | **archon separation 6.5** — first blood inside 20 rounds, so combat, bullet collision and the strike all fire early. **This is the `docker-smoke` map** |
| `OMGTree` | **one radius-10 tree on a 30×30 board** — the 2 000 HP wall, the largest possible `targetRadius` in `calcHitDist`, and the scout-over-tree case |
| `shrine` | **one radius-2 tree containing one robot and one bullet cache** — the near-empty board, the shortest possible tree pass, and the control that proves the tree phase is not what makes the others agree |
| `Chess` (from `mixed`) | **924 trees on 64×64 with 28 of them holding robots** — the heaviest candidate load in the pool and the perf gate's map |
| `Cramped` (from `mixed`) | **archon separation 5.0 with radius-2.5 trees** — bodies that cannot pass each other, so `canMove`'s tank/scout split and the four-cardinal-point `onTheMap` test both matter from round 1 |
| `Alone` (from `large`) | **100×100 with ZERO trees** — the largest board, the longest bullet flights, the only pair where the tree pass is empty every round, and therefore the cleanest test of the bullet id stream and the income cliff |

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from the variant's
pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot takes engine-side **Team.A** in
game 1; sides alternate each game. Seed, map names and side assignment are recorded in results and in the replay.
**The `docker-smoke` seed is pinned so that the draw is exactly `HouseDivided`**, and `tests/test_bc17_maps.nim`
asserts that draw so the smoke's map cannot drift.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `fdlibm`, `sheet_common`, `sheet`, `decide`,
`llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`, `seats`) never branches on the year except
through `years/dispatch.nim`, whose `Session` is a Nim object **variant** so the compiler refuses to build a
half-added year. Adding 2017 is exactly what bc16 and bc19–bc25 proved adding a year to be: a new `years/bc17/`
directory, a converted map set, a sprite atlas, **one registry line**, one arm per dispatch `case` and one manifest
variant. **The one year-neutral file this run touches beyond those is `fdlibm.nim`, purely additively** (four new
procs, no existing proc changed), so no bc16 recording's `fdlibmExp` result moves. **Nothing else on `main` changes**;
the shared files this branch edits are enumerated in §Packaging, and the replay header records `year` so a viewer can
never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the year-dependent *payload*
differs (`year`, the map cards, `sheet_schema`, `scoring`), and a new id would force every bc16/bc19–bc26 consumer to
re-register for no change in the contract. Both `game.protocols.player` and `game.protocols.global` keep pointing at
`docs/PROTOCOL.md`, which gains a bc17 section.

### The player container (thin registrar) — unchanged

`/bin/battlecode-player` reads `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dials its seat with a
bounded retry (240 × 500 ms), sends **one** registration blob and then only receives until the socket closes, then
exits 0:

```json
{"type":"register","prompt":"<PLAYER_PROMPT or empty>",
 "scripted":"awu"|"scaffold"|null,
 "policy":"<PLAYER_POLICY_LABEL>"}
```

sent as a Sprite v1 chat blob (a **binary** frame — the server must not filter non-text frames), re-sent a bounded
number of times until acknowledged. The seat token is a **credential** and a wrong one is refused
(`tools/ci/cert_probe.py` proves it against the real image); a seat that sets neither env var takes the year's default
baseline (`orchard`); a seat whose registration never arrives is logged loudly and reported to
`COGAME_PLAYER_FAILURE_URI`; and the receive loop is wrapped in `try/except CatchableError` and exits 0 on a dead
socket (the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no per-round
observation of any kind. **The example below is the real `HouseDivided` card, measured in this sandbox** (30×30,
origin `(479.3870, 36.5402)`, map seed 937, Team A's archon id 55 at `(491.1370, 51.5402)`, Team B's archon id 54 at
`(497.6370, 51.5402)`, 41 neutral trees holding 222 bullets between them and 6 holding a robot).

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV13","year":"bc17",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":774113,
 "games":[{"map":"HouseDivided","map_seed":937,"width":30.0,"height":30.0,
           "origin":[479.387,36.5402],"you_are":"A",
           "rounds":2999,"rounds_are_one_based":true,
           "round_limit_note":"the engine's round cap is 3000 but the game is decided at the END of round 2999, so 2999 rounds are played",
           "continuous_space_note":"coordinates are 32-bit floats, not grid cells. Every body is a CIRCLE: an archon and a tank have body radius 2, everything else 1, a bullet tree 1 and a neutral tree 0.5 to 10. Distance is measured centre to centre and 'within distance 1 of a tree' means 1 beyond its radius.",
           "your_archons":[{"id":55,"x":491.137,"y":51.5402}],
           "enemy_archons":[{"id":54,"x":497.637,"y":51.5402}],
           "archon_separation_min":6.5,"archon_separation_max":6.5,
           "who_moves_first":"Clan Basil (robot id 54 precedes 55 in the map file, and turn order is spawn order)",
           "neutral_trees":{"count":41,"total_radius":40.9,"radius_min":0.96,"radius_max":1.0,
             "with_bullets":41,"total_contained_bullets":222,"with_a_robot":6,
             "note":"a neutral tree has 200 x radius health, blocks every body except a SCOUT, and can be SHAKEN by any robot at distance 1 for the bullets inside it. Only a LUMBERJACK's chop() releases a contained ROBOT, which then joins the chopping team."}}],
 "economy":{"start_per_team":{"bullets":300},
            "passive_income":"max(0, 2 - 0.01 x bullets_you_hold) per round -- which is EXACTLY ZERO at 200 bullets or more, and you start at 300. It only pays you once you have spent below 200.",
            "trees":{"cost":50,"planted_by":"a GARDENER only","radius":1.0,"start_health":10.0,"max_health":50.0,
                     "growth":"+0.5 health a round for its first 81 rounds, and it produces NOTHING during them",
                     "income":"health / 50 bullets a round once mature -- 1.0 a round at full health",
                     "decay":"-0.5 health a round, always","water":"+5 health, one tree per GARDENER per turn, at distance 1"},
            "shake":"any robot, one tree per turn, at distance 1: you get every bullet inside that tree",
            "chop":"a LUMBERJACK only, 5 damage to one tree at distance 1 -- and it is the ONLY way to release a robot from a neutral tree"},
 "victory":{"points_to_win":1000,
            "price":"7.5 + round x (12.5/3000) bullets per point: 7.5 on round 1, 13.75 on round 1500, 19.996 on round 2999",
            "donate":"any robot, any number of times a turn: you spend the bullets you name and gain floor(bullets / price) points. THE REMAINDER IS DESTROYED, so donate an exact multiple of the price.",
            "cost_estimate":"1000 points is about 13750 bullets at the average price -- roughly 40 mature trees paying for 344 rounds",
            "instant":"reaching 1000 points ends the game the moment the donation lands; losing your LAST ROBOT (trees do not count) loses it the same way",
            "at_round_2999":["more victory points","more bullet trees alive (a sapling counts as much as a mature tree)","more bullets plus the bullet cost of your live robots (an ARCHON counts MINUS ONE)","the team of the highest robot id"]},
 "units":{"archon":{"cost":"cannot be built","hp":400,"body_radius":2.0,"stride":0.5,"sight":10.0,"bullet_sight":15.0,
                    "does":"hires GARDENERS for 100 bullets once every 10 turns; CANNOT attack at all; you start with one to three of them"},
          "gardener":{"cost":100,"hp":40,"body_radius":1.0,"stride":0.5,"sight":7.0,"bullet_sight":10.0,
                      "does":"the ONLY unit that can plant a bullet tree (50) or water one (+5); builds the four fighters; CANNOT attack. Born at full health, acts from its second round. Its 10-turn build cooldown is SHARED between planting and building."},
          "lumberjack":{"cost":100,"hp":50,"body_radius":1.0,"stride":0.75,"sight":7.0,"attack_power":2.0,
                        "does":"no bullets at all. chop() = 5 damage to ONE tree at distance 1. strike() = 2 damage to EVERY robot and EVERY tree within distance 2 of its centre, WITH NO TEAM CHECK -- including your own gardeners and your own farm."},
          "soldier":{"cost":100,"hp":50,"body_radius":1.0,"stride":0.8,"sight":7.0,"bullet_speed":2.0,"attack_power":2.0,
                     "does":"single (1 bullet), triad (4 bullets, three shots at +/-20 degrees) or pentad (6 bullets, five shots at +/-15 degrees)"},
          "tank":{"cost":300,"hp":200,"body_radius":2.0,"stride":0.5,"sight":7.0,"bullet_speed":4.0,"attack_power":5.0,
                  "does":"the same three shot shapes with 5 damage a bullet, AND a BODY ATTACK: trying to move onto a tree does 4 damage to the nearest overlapping tree instead of moving. It can body-attack and fire in the same turn."},
          "scout":{"cost":80,"hp":10,"body_radius":1.0,"stride":1.25,"sight":14.0,"bullet_sight":20.0,"bullet_speed":1.5,"attack_power":0.5,
                   "does":"the fastest body and the widest eyes, single shots only, and THE ONLY BODY THAT MAY OVERLAP A TREE -- it can sit inside a neutral tree where nothing but a bullet can reach it."}},
 "combat":{"bullets_travel":"a bullet is a point moving `bullet_speed` units a round in a straight line. Each round it sweeps from its old point to its new one and the FIRST body the segment crosses takes the damage and the bullet vanishes. It does not check teams and it does not exclude the robot that fired it.",
           "dodging":"a soldier's bullet moves 2 a round and a soldier strides 0.8, so bullets CAN be walked out of at range, which is why volume beats aim",
           "spawn_hit":"a bullet that is spawned inside a body damages it immediately, before it ever moves",
           "no_delays":"every robot may move once AND attack once every turn, in either order, and an attack originates from where the robot ends up",
           "new_units":"a built fighter appears at 20 % health and does NOTHING for 20 turns while it heals 4 % a turn. It can be killed during them."},
 "comms":{"array":{"channels":10000,"cost":"free -- it costs no bullets","note":"one integer array per team, readable and writable by every robot of that team only, persistent until overwritten"},
          "exposure":"BROADCASTING REVEALS YOUR POSITION. Every robot that broadcast in round R has its location readable by BOTH teams in round R+1 via senseBroadcastingRobotLocations()."},
 "rules_digest":"<~6 KB condensed spec: the six unit types with their exact costs, health, radii, strides, sights, bullet speeds and attack powers; the round loop and the fact that bullets move in the same phase as robots, immediately before the robot that fired them; the tree arithmetic with the 81-round maturity; the neutral-tree rules; the shot shapes and their costs; strike and chop; the tank body attack; the income cliff at 200 bullets; the victory-point price curve; and the four-rung ladder>",
 "sheet_schema":{"…all eleven knobs, their values, ranges, defaults and notes…"},
 "scoring":{"weights":{"victory_points_share":64,"bullet_trees_share":24,"bullet_worth_share":12},"win_bonus_per_game":200,"games":3,
            "note":"shares are float32; points truncate to an integer; bullet worth is your bullets plus the bullet cost of your live robots with an ARCHON counting MINUS ONE; the league ranks by ELO on match wins and results.scores is dominated by the win bonus"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with **both** factions' archon ids and float
coordinates, the board size and origin, the neutral-tree census with how many hold bullets and how many hold robots,
the seed, the full constant tables, the economy arithmetic including the income cliff and the VP price curve, the knob
surface with defaults, the scoring weights and the deadlines. Both factions' archon positions are given because they
are **not secret**: `getInitialArchonLocations(team)` returns either team's, sorted
(`RobotControllerImpl.java:112-131`), so a chassis has them from its first turn — and `kit.nim` reads them exactly
that way in-match.

**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in either
direction, at any time); the opponent's real player name (only the alias); **every in-match state** (a cog receives
**no** per-round observation — one sealed doctrine, then the war); and the other seat's fallback status. Inside a match
the fog is the robots': **sight radius 14 for a SCOUT, 10 for an ARCHON, 7 for everything else**, measured as
Euclidean **distance** and not distance-squared (a 2017 change from every previous year); bullets are sensed further
than the units that fire them (**bullet sight 20 / 15 / 10**). Two things widen the fog: **broadcasting** reveals the
broadcaster's position to **both** teams for one round, and **an initial archon position is public from round 1**.
Nothing else occludes — there is no line-of-sight rule, and a tree does not block vision.

### Reply schema and caps

```json
{"sheet":{"opening":"tank_rush","gardener_count":2,"farm_layout":"ring",
          "soldier_tank_ratio":70,"lumberjack_share":40,"scout_harass":35,
          "vp_donate_policy":"endgame_dump","shake_neutral_trees":"dedicated",
          "chop_policy":"harvest","bullet_reserve":50,"defend_radius":8},
 "notes":"Two tanks at their archon by round 260; it is 6.5 away and a tank strides 0.5, so the wave arrives before their first tree matures at round 81+50. I bank instead of donating because rung three of the tiebreak is bullets plus robot cost.",
 "motto":"Arrive before the harvest."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES** (`MaxReplyBytes`, `sim_types.nim:243`), cut on a **rune** boundary by `truncateBytes` | unparseable → retry once → fallback sheet |
| the envelope | unwrapped **at most once** (`sheet`, `doctrine`, or a single object-valued key), the resolved key recorded in `seats[].sheet_envelope` | no envelope found → the payload itself is the sheet |
| `sheet` | ≤ **32** keys (`MaxSheetKeys`), each value type- and range-checked | bad field → that field's default, recorded in `sheet_defaults_applied` |
| `gardener_count` (1…8), `soldier_tank_ratio` (0…100), `lumberjack_share` (0…100), `scout_harass` (0…100), `defend_radius` (1…40) | integers, **clamped** to their stated ranges | out of range → clamped to the nearer bound and recorded (an integer knob is clamped, never defaulted, so "as many as possible" still means something) |
| `bullet_reserve` | integer **0 … 2000** | out of range → clamped; a non-integer → the default 200, recorded |
| every enum knob (`opening`, `farm_layout`, `vp_donate_policy`, `shake_neutral_trees`, `chop_policy`) | exactly one of its listed strings, case-folded and trimmed, `-`/space → `_` (`normalizeKey`) | unknown value → that field's default, recorded |
| an **absent** known key | takes its default and **is recorded in `sheet_defaults_applied`** (bc17 only, the envelope pin item 2) | — |
| `notes` | **280 runes** (`MaxNoteRunes`) | truncated |
| `motto` | **48 runes** (`MaxMottoRunes`) | truncated |
| unknown sheet keys recorded | ≤ **16** keys (`MaxUnknownFields`), each ≤ **40 runes** (`MaxUnknownFieldRunes`) | truncated |
| provider error text stored in the replay | **200 runes** (`MaxFallbackDetailRunes`) | truncated |
| the recorded prompt | **4000 runes** (`MaxPromptRunes`) | truncated |
| `PLAYER_POLICY_LABEL` | **48 runes** (`MaxPolicyLabelRunes`) | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary** (`truncateRunes`/`truncateBytes`,
`sim_types.nim:353-380`; the 16 KB reply cap is in bytes but is still cut on a rune boundary): byte-slicing a
multi-byte character renders fine in a browser and then fails a strict UTF-8 parser. **There are exactly two free-text
fields (`notes`, `motto`), both capped above, and every other recorded string (`sheet_unknown_fields[]`,
`fallback_detail`, `prompt`, `policy`) is capped too. The total reply byte cap is 16 384 bytes.**

### Results document

The closed schema is **shared with the nine shipped years**: `results.games[]`'s five required keys are year-neutral
(`map`, `side`, `rounds_played`, `winner`, `end_reason`), every year-specific statistic is an optional property, and
`end_reason`'s enum is the union of every year's values.

bc17's per-game keys, each a 2-array of integers in **seat** order unless marked. The seven that already exist for
another year — `units_built`, `units_alive`, `units_lost`, `attacks`, `damage_dealt`, `kills`, `robots_lost` — are
**reused rather than duplicated**:

`archons_start`, `archons_end`, `archons_lost`, `gardeners_built`, `gardeners_end`, `gardeners_lost`,
`lumberjacks_built`, `soldiers_built`, `tanks_built`, `scouts_built`, `units_built`, `units_alive`, `units_lost`,
`victory_points`, `bullets_end_tenths`, `bullets_earned_from_trees_tenths`, `bullets_shaken_tenths`,
`bullets_donated_tenths`, `bullets_spent_on_units_tenths`, `bullets_spent_on_trees_tenths`,
`bullets_spent_on_shots_tenths`, `bullets_trickled_tenths`, `bullet_worth_end_tenths`, `trees_planted`, `trees_end`,
`trees_lost`, `trees_mature_end`, `water_actions`, `shake_actions`, `chop_actions`, `neutral_trees_felled`,
`robots_released_from_trees`, `bullets_fired`, `single_shots`, `triad_shots`, `pentad_shots`, `attacks`,
`damage_dealt_tenths`, `damage_taken_tenths`, `friendly_fire_damage_tenths`, `own_trees_damaged_tenths`,
`strike_actions`, `body_attacks`, `kills`, `robots_lost`, `moves`, `broadcasts`, `builds_refused`, `refused_actions`,
`decision_ops_peak`;

scalars `archons_per_side`, `board_width_tenths`, `board_height_tenths`, `neutral_trees_start`,
`neutral_trees_with_bullets`, `neutral_trees_with_robots`, `archon_separation_min_tenths`,
`archon_separation_max_tenths`, `robot_ids_issued`, `bullet_ids_issued`, `peak_bullets_in_flight`,
`domination_factor`, `tiebreak_round`.

**Every float quantity is reported in TENTHS as an integer** (`_tenths`) — the convention bc16 established, which this
year needs more than any other because bullets, health and damage are `float32` and a raw float in a JSON results
document is a formatter argument waiting to happen. The viewer's `fmtStat` divides by 10 and prints one decimal.
**`victory_points`, every count and `decision_ops_peak` are exact integers and are NOT in tenths.**

Top level, unchanged and already declared at `f057064`: `names`, `aliases`, `scores`, `wins`, `points`, `games`,
`seed`, `year`, `policy_kind`, `sheet_defaults_applied`, `sheet_envelope`, `fallbacks`, `decision_ms`, `sim_seconds`,
`reason`, `wall_clock_seconds`, `game_version`. **bc17 adds no top-level key.**

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV13","year":"bc17",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":774113,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"orchard",
           "sheet":{…as applied…},"sheet_submitted":"{…as received, before unwrapping…}",
           "sheet_envelope":"doctrine",
           "sheet_defaults_applied":["chop_policy"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":9214,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"HouseDivided","map_seed":937,"map_json_sha256":"…",
           "sides":["A","B"],"side_a_slot":0,"rounds":2999,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…all three drawn maps, even if the match clinched in two…],
         "side_a_slots":[…],"abandon_after":[…],"max_rounds":3000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI — `result`, SINGULAR, this repo's convention */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a sha256 of the
committed converted map the bundle also ships), both doctrine sheets **and both submitted sheets with the envelope key
that was unwrapped**, the chassis each seat drove and the event list are all in the file, and the wasm sim replays
every round from them. **No `.bc17` bytes, no per-round body dump, no per-round bullet dump** — every body's float
position, health, type and counters, every bullet's position, direction, speed and damage, both supplies, both VP
totals, the broadcast arrays, the exec order, the trove layout and both `IDGenerator` states are pure functions of the
sim. **This matters more here than in any other year: a 2 999-round game with 500 bullets in flight would be a
multi-megabyte replay if positions were stored, and it is 60–200 KB because they are not.** No server is contacted
except S3 for the `.replay` file, and the per-round hash chain lets the viewer prove its re-derivation matches the
recording (`bc_mismatch_round`, surfaced as `data-replay-mismatch-round` and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round` (**1-based**, as the engine's are). **Every
event kind is bounded per game** — a 2 999-round match with 500 bullets in flight cannot be allowed to emit an event
per bullet — and every one has a beat kind with CSS (§Viewer). **No event has a field named `kind`**:
`first_action`'s field is `action` (the bc23 r1-F25 lesson).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `envelope`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `map_seed`, `width`, `height`, `archons`, `neutral_trees`, `trees_with_bullets`, `trees_with_robots`, `separation_min`, `sides` | 1/game | `game` | beat + feed |
| `first_action` | `game`, `round`, `alias`, **`action`** (from `Bc17ActionNames`) | 2/game | `build` | beat + feed |
| `unit_milestone` | `game`, `round`, `alias`, `unit` (from `Bc17UnitNames`), `total` — the **first** of each of the five buildable types per side | ≤ 10/game | `build` | beat + feed |
| `tree_planted` | `game`, `round`, `alias`, `x`, `y`, `trees` — the first six per side then every fourth | ≤ 24/game | `tree` | beat + feed |
| `tree_lost` | `game`, `round`, `alias`, `x`, `y`, `trees`, `cause` (`bullet`\|`strike`\|`chop`\|`body_attack`\|`decay`) — the first six per side then every fourth | ≤ 24/game | `tree` | beat + feed |
| `farm_online` | `game`, `round`, `alias`, `mature_trees`, `income_tenths` — the first round a side's tree income passes 10, 25 and 50 bullets a round | ≤ 6/game | `tree` | beat + feed |
| `gardener_lost` | `game`, `round`, `alias`, `x`, `y`, `gardeners_left` | ≤ 16/game | `archon` | beat + feed |
| `archon_lost` | `game`, `round`, `alias`, `x`, `y`, `archons_left`, `cause` (`bullet`\|`strike`) | ≤ 6/game | `archon` | beat + feed |
| `donation` | `game`, `round`, `alias`, `bullets_tenths`, `vp_gained`, `vp_total`, `price_tenths` — the first per side, then every crossing of a 100-VP boundary | ≤ 24/game | `donate` | beat + feed |
| `shake` | `game`, `round`, `alias`, `bullets_tenths`, `x`, `y` — the first per side then every eighth | ≤ 20/game | `shake` | beat + feed |
| `chop_reveal` | `game`, `round`, `alias`, `unit` (from `Bc17UnitNames`), `x`, `y` — a neutral tree chopped open releasing a robot | ≤ 12/game | `shake` | beat + feed |
| `strike` | `game`, `round`, `alias`, `enemy_hit`, `friendly_hit`, `trees_hit`, `own_trees_hit` — the first per side then every eighth | ≤ 20/game | `strike` | beat + feed |
| `volley` | `game`, `round`, `alias`, `bullets_fired`, `shape` (`single`\|`triad`\|`pentad`) — a round in which a side fired ≥ 10 bullets | ≤ 20/game | `volley` | beat + feed |
| `rout` | `game`, `round`, `alias`, `lost` — a round in which one side lost ≥ 4 robots | ≤ 20/game | `rout` | beat + feed |
| `duel` | `game`, `round`, `lost` (2-array) — a round in which **both** sides lost at least one robot | ≤ 20/game | `duel` | beat + feed |
| `famine` | `game`, `round`, `alias` — the first round a side's bullet supply is below 1 with a build or a shot pending, once per side | ≤ 2/game | `famine` | beat + feed |
| `tiebreak` | `game`, `round`, `rung` (from `Bc17RungNames`), `vp` (2), `trees` (2), `worth_tenths` (2) | ≤ 1/game | `end` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `domination_factor`, `points`, `vp`, `trees` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

**Thirteen beat kinds** (`doctrine`, `game`, `build`, `tree`, `archon`, `donate`, `shake`, `strike`, `volley`, `rout`,
`duel`, `famine`, `end`), and **all thirteen are emitted by the committed fixture replay** so the beat test in §Viewer
is a real gate and not a CSS inventory. The whole event list for a three-game match is at most
`11 + 3 × 232 = 707` entries, and `tests/test_bc17_replay.nim` asserts each per-kind bound so a pathological game
cannot produce a 20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by the
build hook **`tools/build_replay_viewer.sh`** (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same `sim_sources_stamp` guard so
a stale committed bundle fails CI). The bundle contains **the same sim module**, now including `years/bc17/`, compiled
to wasm; the browser re-derives every round from the replay's events, config and seed. No pod, no live viewer route,
no `.bc17` bytes, and **no JDK, no JRE and no Java of any kind** — the 2017 engine exists only inside the
`parity-oracle-bc17` CI job.

### All four viewer files come from ONE starter: `Metta-AI/cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode` → here. **All four
bundle files come from that one starter — `Metta-AI/cogame-battlecode` — and never a mixture**, because splicing one
starter's shell onto another's emscripten link flags deadlocks the viewer silently with every file present and 200
(cogame-lantern, 2026-08-23).

| bundle file | source (**all four from `Metta-AI/cogame-battlecode`, and from nothing else**) | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc17/`, `data/bc17/fdlibm_vectors.json` and `data/atlas_bc17.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are, including `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-O2`, `--mm:arc`, `--exceptions:goto` and `-d:useMalloc`. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. **No edit at all is needed for bc17**: the page already sets `document.documentElement.dataset.year` from the frame's `s.year` in the shared block, so a new year switches itself on. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc17 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and **no existing id is reused for a different purpose** (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and **byte-for-byte**: **`client/chrome_common.js` is copied byte-for-byte** into the bundle, and so is
**`client/broadcast_core.js`**; their sha256 is asserted against the `coworld-ctf` copies in `tests/test_viewer.nim`,
and that assertion stays green because **neither file is touched**. `wire_constants.js` is regenerated from the sim by
`tools/gen_wire_constants.nim`, as today.

**Load signalling** (unchanged from the starter, restated because it is a checklist item): `static_replay.js` sets
`document.documentElement.setAttribute('data-replay-loaded', 'true')` on the **first drawn frame** (`:180`) — the
worker's `loaded` message after the first board frame is composited, never on rAF timing at the call site (the chorus
2026-08-24 scar) — and the `coworld-replay` bridge posts `ready` from a callback fired **after** that attribute is set.
On any failure (fetch, JSON parse, an unknown `game_version`, a wasm abort, a rendering-blocking hash mismatch) it sets
**`data-replay-error="<message>"`** on `<html>` (`:14-20`) and shows the failure card.

### The appended bc17 game block, and chrome provenance

**No starter element is removed from the page.** The bc26 block's ids (`#coopchip`, `#bars`, `#gamechips`, `#econ`,
`#doctrines`) and the bc16/bc19–bc25 blocks' (`#bc16-archons` … `#bc19-crusade`, 54 ids in all) all stay exactly where
they are. **What bc17 removes is nothing from the page and everything from the screen**: like every other year block
it appends `html[data-year="bc17"] #coopchip, … #bc19-crusade { display: none !important }` for those 54 ids and
`html:not([data-year="bc17"]) #bc17-… { display: none !important }` for its own **six**, so on a bc17 replay exactly
the bc17 set plus the shared chrome is visible. **The precise list of starter elements bc17 hides** is the union of
the nine existing year blocks' own id sets — and `tests/test_viewer.nim` derives it **from the page source**, not from
a hand-written copy, so a tenth year cannot leave a ninth year's box visible.

The bc17 ids are all new and all prefixed:

- `#bc17-vp` — **the headline readout, and the year's whole story**, in the top-centre pill slot bc16 and bc22 use:
  the **race to 1000**, as two bars with the numbers on them (`ASH 612 ▮▮▮▮▮▮·  —  ·▮▮▮▮ 438 BASIL`), the **current
  price of a victory point** (`VP costs 12.4 bullets · +0.0042/round`) and, beside it, **how many bullets each side
  would still need** (`ASH needs 4 811 · BASIL needs 6 979`). It **flashes** on a `donation` event and goes solid gold
  the instant a side crosses 1000. This is the one number a casual spectator has to see, and it is the only one that
  never leaves the strip at any width.
- `#bc17-bullets` — **the year's second signature readout**: bullets banked, **tree income this round**
  (`🌳 38 mature → +34.6/round`), the **trickle** shown separately and greyed out when it is zero with the reason in
  plain words (`trickle 0 — you hold more than 200`), bullets spent this round split into `units / trees / shots /
  donations`, and the round counter (`ROUND 1 612 / 2 999`).
- `#bc17-econ` — per faction: trees planted / standing / mature / lost with the **cause** of each loss; bullets
  earned from trees, shaken and trickled, each broken out; bullets spent on units, trees, shots and donations; water,
  shake and chop actions; neutral trees felled and **robots released from them**.
- `#bc17-units` — per faction: the six-type census with archons emphasised, **units still dormant** shown separately
  (a 20-turn dormant fighter is not an army), units built and lost, **bullets in flight**, and **friendly-fire and
  own-tree damage as their own number** — with `lumberjack_share` high that is where the losses come from.
- `#bc17-doctrines` — both sheets in plain words, **dismissible**: a `#bc17-doctrines-close` button with
  `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first playback advance (or after six
  seconds), and a `#bc17-doctrines-toggle` chip in the scorebug that re-opens it. Its body is **capped and scrolls**
  (the bc23/bc25 clipping finding); it sits above the board area and **never** inside the transport band; and it
  carries the **submitted-vs-applied badge** the envelope pin requires.
- `#bc17-fund` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: the shared `onText` block already sets
`document.documentElement.dataset.year` from the replay header and re-runs `relayout()` on a change; the stylesheet
extends the existing `html:not([data-year="bc19"]) #bc19-… { display: none !important }` pattern with the bc17 pair.
**Every bc17 rule — including every beat-marker colour — is scoped to `html[data-year="bc17"]`** (the bc21 r1-F4 fix,
kept), so none of them can restyle another year's marker of the same name. The frame hook is
`window.Bc17Block.active(s)` / `.onFrame(s)`, added beside the existing nine in the shared `onText`, and the
`if (!isBc16 && !isBc19 && !isBc20 && …)` guards at `client/replay_broadcast.html:7887` and `:7899` become
**ten-way** tests with `!isBc17`.

### The beat contract — emission, label and style, all three tested

This is where the bc25 run failed review (r1-F26: eleven beat-kind CSS rules against two emitted kinds), so it is
specified as three obligations that **one** test asserts together against the **committed fixture replay**
(`tests/fixtures/replay-bc17.json`):

1. **Emission.** `beatsFor` in `src/battlecode/broadcast.nim:156` is the only place a beat kind is decided. bc17 adds
   `let isBc17 = doc.year == "bc17"` beside the five that are already there (`:164-168`) and an arm for each of its
   event kinds. **Four event names collide with other years and each needs the year test**: `first_action`
   (bc16/bc19/bc22/bc23/bc25 map it to `build`; bc17 joins them, `:198`), `rout` (the same set, `:207`), `duel`
   (bc16's, bc19's, bc22's and bc23's — bc17's carries the same field name with a different meaning, robots lost
   rather than launchers, so the **label** switch gains a year test), and **`archon_lost`, which bc16 AND bc22 both
   emit with different fields** — bc17's carries `archons_left` and a `cause`, so both the beat arm and the label
   switch gain the discriminator. `famine` is bc19's name and bc17 emits it with a **different field set** (no
   `resource`, because 2017 has one resource), so it needs the test too. The bc17-only kinds (`tree_planted`,
   `tree_lost`, `farm_online`, `gardener_lost`, `donation`, `shake`, `chop_reveal`, `strike`, `volley`) need no
   discriminator, because no other year emits those event names — even though two of their beat kinds (`build`,
   `end`) are spelled the same as another year's, which is exactly why the CSS scoping is mandatory.
2. **Label.** Every emitted beat carries a spectator-readable label built in the same `case` — e.g.
   `"CLAN ASH REACHES 1000 — the Fund is closed, game 2, round 1841"`,
   `"Clan Basil donates 240 bullets for 19 points — 612 to go, game 1, round 903"`,
   `"ARCHON DOWN — Clan Ash has none left, killed by a bullet, game 3, round 512"`,
   `"Lumberjack strike at 491,52 — two of Basil's units and four of Basil's trees, and one of Ash's own, game 1, round 611"`,
   `"Clan Ash's farm is online — 25 mature trees paying 23.4 bullets a round, game 2, round 340"`,
   `"ROUND 2999 — victory points level at 431, Clan Basil wins on bullet trees 41 to 38"` — and it becomes the
   `<button>`'s `aria-label` and `title`. Every label is ≤ 120 runes.
3. **Style.** `client/replay_broadcast.html` ships a `.beat-marker.<kind>` rule for **all thirteen** kinds, every one
   scoped to `html[data-year="bc17"]`: `.doctrine`, `.game`, `.build`, `.tree`, `.archon`, `.donate`, `.shake`,
   `.strike`, `.volley`, `.rout`, `.duel`, `.famine`, `.end`. Seven of those names already exist for other years
   (`doctrine`, `game`, `build`, `rout`, `duel`, `famine`, `end`), which is exactly why the scoping is mandatory; six
   are new (`tree`, `archon`, `donate`, `shake`, `strike`, `volley`).

`tests/test_bc17_beats.nim` loads the committed fixture, calls `beatsFor`, and asserts: **at least 26 beats over at
least 11 distinct kinds**, every beat's label non-empty and ≤ 120 runes, every emitted kind present in the
thirteen-kind vocabulary, and — reading the page source — a `html[data-year="bc17"] .beat-marker.<kind>` rule for
**every kind the fixture actually emitted** (not for every kind in a hand-written list).
`tools/gen_bc17_fixture_replay.nim` is written to produce all thirteen kinds, and the test fails if the fixture stops
doing so.

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The `--statrail` repair is already in the tree (`relayout()` measuring the visible year stat boxes at
`client/replay_broadcast.html:7735-7749`, `#killfeed`'s `bottom` at `:1270`, `tests/test_viewer.nim` asserting both
statically, and `viewer_smoke.mjs --killfeed-overlap` measuring client rects at 360 / 720 / 1280 px at FIT and 2× zoom
on every year's replay). **What bc17 must do — and it is the whole of the work here:**

1. add **`bc17-econ` and `bc17-units`** to `relayout()`'s measured id list, beside the seventeen already there.
   (`#bc17-vp` and `#bc17-bullets` are **top**-band pills and are deliberately not in the rail set.)
2. run the existing `--killfeed-overlap` gate **on the bc17 replay too**, at all three widths and both zooms — ten
   replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and asserts the gate
   goes red, so a tenth year cannot quietly disarm it.

### Zoom: KEEP `#viewpanel`

**Decided: `#viewpanel` (the zoom bar + minimap) is KEPT, and bc17 is the strongest case for it in the repository.**
bc17 boards are **30×30 to 100×100 in continuous float space** — the `mixed` pool spans 42×40 to 64×64 and `large`
reaches 100×100 — so at a legible 16 px per world unit they are **480 to 1 600 px wide**, every one of them larger
than the 360 px featured-match frame, where a 64-wide board gives 5.6 px per unit and a 100-wide board **3.6**. Worse
than any grid year: the bodies are *circles of radius 1 to 10*, so a radius-1 gardener at 3.6 px/unit is a 7-pixel dot
and a bullet is a subpixel. A fixed arena would drop the panel; this is emphatically not one. The inherited
`#viewpanel` is kept and wired to the same `zoomAt/setZoom/panBy/panTo/resetView` core API the worker already
forwards, with `?viewpanel=0` still honoured for thumbnail capture, and the default view is fit-to-board so a
spectator who touches nothing sees the whole map, both archons and every farm at once.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets **`--hudscale`**,
  **`--topband`**, **`--band`** and **`--statrail`** on **`:root`**, iterating to a fixed point so a map-aspect change
  cannot leave dead strips. bc17 exercises that harder than any other year (its maps run **100×30** to square), so
  `tests/test_viewer.nim` asserts the fixed point converges for aspect ratios 0.3, 1.0 and 3.33.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band (scorebug) and the
  bottom band (transport). `#bc17-vp`, `#bc17-bullets`, `#bc17-econ`, `#bc17-units`, `#bc17-doctrines` and
  `#bc17-fund` are all explicitly positioned above `var(--band)`; the bullets strip's spend row sits **immediately
  above** `var(--band)`, never inside it.
- **The endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek dismisses it**:
  `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`, built by a bc17-block
  function with its **own** name, **`buildBc17BeatButtons`** — never `markBeat` (the tandem 2026-08-23 hoisting
  collision) and never colliding with `buildBeatButtons` (bc26), `buildBc16BeatButtons`, `buildBc19BeatButtons`,
  `buildBc20BeatButtons`, `buildBc21BeatButtons`, `buildBc22BeatButtons`, `buildBc23BeatButtons`,
  `buildBc24BeatButtons` or `buildBc25BeatButtons`. The spoiler gate is honoured by `applyBc17BeatSpoilers`, the same
  shape as the other eight blocks. **Every beat kind the sim emits has a CSS rule** (the beat contract, item 3).
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`,
  `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`, `#scrub` +
  `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — bc17 takes the HEAVY probe, and the reason is measured

bc21 taught the repo that a compute-heavy year defeats a fixed-wait scrub probe, because the Worker re-simulates from
the start of the game on every seek. **bc17 is the most exposed year this repo has**: 2 999 rounds (the joint longest,
with bc16) at an estimated 3–12 ms/round with hundreds of bullets in flight (§The game), so a 100 % seek re-simulates
9–36 s of native work in a wasm Worker, which is slower again. Decided here rather than discovered at phase 60: **the
phase-60 check-8 dispatch for bc17 uses `settle=20000 soak=15`** and `ci.yml`'s `wasm-viewer` job runs the bc17 replay
at **`--timeout 120 --soak 15`** (joining bc16/bc22/bc23/bc24/bc25; bc19/bc20/bc21/bc26 keep `--timeout 90
--soak 10`). `docker-smoke` prints `sim_seconds / rounds` and `docs/RULES-BC17.md` records it; **if the measured value
exceeds 15 ms/round, phase 20 lowers the smoke episode's `maxRounds` rather than the soak** — the soak must still
outlast the replay (the ecos 2026-08-23 scar), and the smoke's 900 rounds is 36 s of playback at 25 fps, which does.

**The scrub selector needs no change.** `tools/ci/viewer_smoke.mjs` in this repo already resolves `#scrub` before
`#seek` before `input[type="range"]`, **one selector at a time**, excluding `#zoom-slider`, and `ci.yml` asserts
`scrub_selector == "#scrub"` after every run. And **`canvas_text.total: 0` on this renderer is not a pass signal**
(LEARNINGS 2026-09-08): the text-bounds check covers nothing here, which is why `--strict-text-bounds` is dropped on
the replay runs and applied instead to `tools/ci/renderer_fixture.html`, where the text is real (§Tests).

### Art

`data/atlas_bc17.png` + `data/atlas_bc17.json` (≈ 50 KB, committed), cut by `tools/build_sprite_atlas_bc17.py` from
**the official 2017 client's own sprite set** at `battlecode/battlecode-client-17@feb3e038`, whose root `LICENSE` is
**AGPL-3.0** — **the same licence as this repository**, checked and cited (rail 7). **The exact files, all verified
present with their real dimensions:**

| atlas cell | source file | size |
|---|---|---|
| `archon_a`, `archon_b` | `src/static/img/sprites/archon_{red,blue}.png` | 50×50 |
| `gardener_a`, `gardener_b` | `sprites/gardener_{red,blue}.png` | 32×32 |
| `lumberjack_a`, `lumberjack_b` | `sprites/lumberjack_{red,blue}.png` | 32×32 |
| `soldier_a`, `soldier_b` | `sprites/soldier_{red,blue}.png` | 32×32 |
| `tank_a`, `tank_b` | `sprites/tank_{red,blue}.png` | 50×50 |
| `scout_a`, `scout_b` | `sprites/scout_{red,blue}.png` | 32×32 |
| `bullet_tree_a`, `bullet_tree_b` | `sprites/bullet_tree_{red,blue}.png` | 32×32 |
| `tree_mature`, `tree_hurt`, `tree_sapling` | `map/{full_health_tree,low_health_tree,sapling}.png` | 32×32 |
| `tree_bullets`, `tree_robots` | `map/{tree_bullets,tree_robots}.png` | 32×32 — the neutral-tree overlays that say *this one has something in it* |
| `bullet_slow`, `bullet_medium`, `bullet_fast` | `bullets/bullet_{slow,medium,fast}.png` | 26/18/16 — one per bullet speed, so a spectator can see a tank shell from a scout's pea |

That is **twenty-one cells from twenty-one files, all in the same repository under one licence**. The `*_neutral`
variants and `recruit_*` (a unit type that does not exist in the shipped `RobotType`) are **not used, not cut and not
shipped**; neither is `src/static/img/controls/` (the client's own transport icons — this repo has its own chrome) nor
`map/tiled_1.jpg` (a background texture the float renderer does not want). **`NOTICE` records the repository, the
commit, the AGPL-3.0 licence file, the exact twenty-one paths, and the fact that `package.json` declares `GPL-3.0`
while `LICENSE` is AGPL-3.0** — both compatible with this repository, and saying so is cheaper than leaving a
discrepancy implicit. **No nano-banana art is needed for bc17** and none is generated.

Board rendering (`render.nim`) — **the first float-space renderer in this repo, and the whole point of the year**:

- The board is drawn at `unitsPerPixel` derived from the map's own width and the frame, so a 30×30 map fills the frame
  and a 100×100 map fits it; `#viewpanel` zooms and pans from there.
- **Neutral trees at their real radius**, from `tree_mature`/`tree_hurt` tinted by `health / maxHealth`, with the
  `tree_bullets` or `tree_robots` overlay when they hold something — so `Maniple`'s 406 robot-bearing trees read as
  406 little presents. **Bullet trees** at radius 1 with a **maturity ring** that fills over the first 81 rounds and
  then a **health ring** that drains as they wither, so "the farm is online" is a visible state change and not a
  number. **Bodies are circles at their real radius** with the sprite inside — an archon and a tank at radius 2 are
  visibly twice a soldier — with a **dormancy ring** on a fighter under 20 rounds old and a health bar under
  everything.
- **Bullets are the year's signature**: a 2 px dot in the firing team's colour with a **two-round motion trail**,
  sized by its sprite (`bullet_fast` at speed 4, `bullet_medium` at 2, `bullet_slow` at 1.5). At FIT on a 100-wide
  board they read as tracer fire; zoomed in you can watch one being dodged. A **lumberjack strike** draws its
  distance-2 disc for one second **including the parts that cover its own side** — the frame that makes
  `lumberjack_share` make sense; a **tank body attack** flashes the damaged tree; a **donation** floats the
  bullets-for-points figure above the donating robot; an **archon death** draws a two-second wash.

### Readouts, 360 px and the endcard

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is **checked at that width**, not at
desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, word labels hidden under 640 px, `#viewpanel`
shrinking to its minimum before anything else, and the `#bc17-*` boxes dropping their word labels to glyphs under
640 px; **`#bc17-vp` keeps both bars, both numbers and the price at every width**, because it is the readout that
makes the year make sense).

- `#scorebug`: both faction plates — `CLAN ASH` over the real player name (`daveey`) and the motto — the live points
  number and `#gamechips` (best-of-3 state). `#clock` / `#clock-time` / `#clock-caption`: `round 1 612 / 2 999`,
  `game 2 of 3 — HouseDivided`. `#bc17-vp`, `#bc17-bullets`, `#bc17-econ` and `#bc17-units` as above.
- `#board`: the float arena, every tree at its real radius, every body as a circle with its sprite, every bullet with
  its trail, the strike discs and the selected unit's **sight circle** (a real circle, because 2017 sensing is a
  Euclidean radius and not a squared one).
- `#bc17-doctrines`: each sheet in plain words ("farms first and fights later", "packs its trees six to a gardener",
  "spends a quarter of its army money on tanks", "sends scouts to squat their farm", "donates whenever it is ahead",
  "chops only what blocks the lane", "keeps two hundred bullets in the bank" — one clause per knob), plus the capped
  `notes`, the **submitted-vs-applied badge** and a fallback badge when a seat's doctrine came from the fallback
  sheet. Dismissible, capped and scrolling.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and provably clear of
  the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words; the per-game score line; and
  `#bc17-fund`, the **Fund panel**: per faction, victory points bought and **what they cost** (bullets donated ÷
  points gained, so a spectator sees who bought cheap); trees planted / mature / lost and how they died; bullets
  earned from trees, shaken and trickled, **with the trickle broken out**; bullets spent on units, trees, shots and
  donations; units built by type and lost; damage dealt and taken, and **friendly-fire and own-tree damage as their
  own line**; kills; neutral trees felled and robots released from them; and the **tiebreak ledger** — all four rungs
  with both sides' numbers and which one decided it. None of it is stored in the replay: the wasm sim re-derives every
  round.

**The endcard's five known template defects are fixed for bc17, not inherited broken** (bc23's and bc25's phase-60
verifications found them; bc22 fixed four for every year and bc16/bc19 kept them armed). Each is asserted by
`tests/test_viewer.nim` (§Tests 30):

1. **This year's nouns, not bc26's.** bc17's row in the `data-year` noun table
   (`client/replay_broadcast.html:7578-7605`) is `bc17: { unit: 'archon', units: 'archons', res: 'bullets',
   res2: 'victory points' }`, and the phrase table adds `gardener`, `soldier`, `tank`, `scout`, `lumberjack`,
   `bullet tree`, `neutral tree`. **No "rat", "cheese", "king", "castle", "karbonite", "parts", "lead", "soup" or
   "gold" appears on a bc17 card.**
2. **No clipping or overflow at 1280×800.** The Fund panel's grid is
   `max-height: calc(100vh - var(--band) - var(--topband) - 24px)` with `overflow-y: auto` on the body only, and
   `viewer_smoke.mjs --killfeed-overlap` asserts `#endcard.scrollHeight <= #endcard.clientHeight` at **1280×800**
   after the 100 % seek. **bc17 is checked at 1280×800 AND at 360 px wide.**
3. **No raw unrounded floats — and this is the year that needs it.** Every printed number goes through one
   `fmtStat(value, kind)` formatter: counts and victory points as integers, `*_tenths` keys divided by 10 and printed
   with **one** decimal, shares as `NN %`, `points`/`scores` as integers, and coordinates as `x.x`. A
   `/\d\.\d{3,}/` grep of the rendered text fails the test. **Nothing in the replay or the results document carries a
   raw float32** (§Server, Results document), which is what makes this enforceable rather than aspirational.
4. **No empty mottos and no "a accelerating"-class grammar.** A blank `motto` renders **nothing**, and
   **`plainWords17()` has no article concatenation anywhere** — every knob value maps to a complete clause.
5. **No HUD bleed-through.** `#endcard` is opaque over the board and the `#bc17-*` boxes are `visibility: hidden`
   while it shows (the bc23 finding).

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`, `player` →
  `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar), `platform: linux/amd64`, `build: {context: ., network: host}`. One
  image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and `/bin/battlecode-player` from
  one image and copies `data/` (now carrying `maps/bc17/`, `bc17/fdlibm_vectors.json` and `atlas_bc17.*`). **NO Java,
  NO JDK, NO JRE, NO Node, NO npm and no JVM of any kind in any stage** — rail 2, and the 2017 engine exists only in
  the `parity-oracle-bc17` CI job and in `tools/convert_maps_bc17.py`, which is **pure Python and reads the map
  resources out of the jar without a JVM**, at build time. Phase 20 adds one `docker-smoke` step asserting `java`,
  `javac`, `node` and `npm` are absent from the built image's `PATH`. `Dockerfile.replay-viewer` is unchanged except
  that its `sed` block emits the bc17 game block along with the other nine.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc17` is 2017 'Robotic Wildlife Fund' — the continuous-space
    year: archons hire gardeners who plant bullet trees; soldiers, tanks, scouts and lumberjacks fight with travelling
    bullets in float coordinates; a victory point costs seven and a half bullets on round one and twenty on round
    two thousand nine hundred and ninety-nine; and a side wins by buying one thousand of them, by killing every enemy
    robot, or by holding more of them at the round limit."*
  - `tags` unchanged (already four: `battlecode`, `strategy`, `mixed-motive`, `wasm`).
  - `game.config_schema`: `year.enum` becomes
    `["bc26","bc20","bc21","bc24","bc25","bc23","bc22","bc16","bc19","bc17"]` — **appended, so no existing index
    moves**. **NO BOUND MOVES**: `maxRounds` is already `{50, 3000}` and bc17 uses **3000**; `gamesPerMatch` keeps
    `maximum 3` (3); `perGameBudgetSeconds` `maximum 300` (**120**); `matchBudgetSeconds` `maximum 600` (**330**);
    `attempt1Ms`/`retryMs` `1000…60000` (20 000 / 12 000); `doctrineBudgetMs` `1000…120000` (45 000);
    `connectTimeoutMs` `1000…120000` (25 000); `num_agents` `{minimum: 2, maximum: 2}`; `pool.enum` unchanged.
    `tokens` stays **declared and required** (the runner injects it — the 2026-09-03 lesson); every array keeps
    `minItems`/`maxItems`; **no runner-managed `tokens` values inside any `game_config`**;
    `additionalProperties: false` stays. **Every manifest edit in this run is additive.**
  - `game.results_schema`: bc17's optional properties added beside the other years' (§Server, Results document);
    `games.items.required` unchanged (the five year-neutral keys); **`end_reason`'s enum extended with exactly FIVE
    values — `victory_points_reached`, `all_robots_destroyed`, `more_victory_points`, `more_bullet_trees`,
    `more_bullet_worth`.** `highest_id` (bc20's) and `abandoned` are **already there and are reused**; **no coin-flip
    value is added, because 2017 has no coin flip**. Top-level `required` is unchanged — `sheet_envelope` is already
    in it.
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — **`readme`** = `{"type":"uri","value":".../blob/main/README.md"}`; **`pages`** keeps its eleven
    (`rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc22.md`, `rules-bc23.md`, `rules-bc24.md`, `rules-bc25.md`,
    `rules-bc16.md`, `rules-bc19.md`, `replay.md`, `parity.md` → `docs/PARITY.md`, which gains a bc17 section) and
    gains **`rules-bc17.md`** (*Battlecode 2017 "Robotic Wildlife Fund": rules, knobs and divergences* →
    `docs/RULES-BC17.md`). **Twelve pages**, every one a `{id, title, content: {type, value}}` object.
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc17 resolution
    ("…, orchard on bc17" / "…, examplefuncsplayer17 on bc17").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The certifier's
  `players-run` step requires **every** declared `player[]` entry to occupy a slot in `certification.players` **and**
  `len(certification.players) == certification.game_config.num_agents`. With **`num_agents = 2`** there are exactly
  **two** cert slots, filled by `awu` and `scaffold`, so **`player[]` may contain exactly those two ids and nothing
  else**; adding `battlecode-bc17-orchard` would fail the release with `players_missing` (LEARNINGS 2026-09-04). It is
  also unnecessary, because `PLAYER_SCRIPTED` resolves **per year**, so seating `awu` on a bc17 episode already plays
  `orchard` and `scaffold` already plays `examplefuncsplayer17`; the scripted bc17 policies reach the league through
  `tools/ci/policies.json`, which has nothing to do with `player[]`. `tests/test_manifest.nim` asserts all three
  facts, so the contradiction cannot be re-introduced silently.

  **Variants — one per Battlecode year. `num_agents` is 2 in every one of them, and 2 is the only seat count in this
  note:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | unchanged | **2** |
  | `bc21` | Battlecode 2021 — Campaign (2 seats) | unchanged | **2** |
  | `bc24` | Battlecode 2024 — Breadwars (2 seats) | unchanged | **2** |
  | `bc25` | Battlecode 2025 — Chromatic Conflict (2 seats) | unchanged | **2** |
  | `bc23` | Battlecode 2023 — Tempest (2 seats) | unchanged | **2** |
  | `bc22` | Battlecode 2022 — Mutation (2 seats) | unchanged | **2** |
  | `bc16` | Battlecode 2016 — Zombie Invasion (2 seats) | unchanged | **2** |
  | `bc19` | Battlecode 2019 — Crusade (2 seats) | unchanged | **2** |
  | `bc17` | Battlecode 2017 — Robotic Wildlife Fund (2 seats) | `year: "bc17"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 3000`, **`num_agents: 2`**, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 120`, `matchBudgetSeconds: 330`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  **No shipped variant's `game_config` changes, and no variant's `players` array changes.**

  **Why these timing numbers.** `maxRounds: 3000` is the engine's own `GameConstants.GAME_DEFAULT_ROUNDS`, which
  `GameMapIO.Serial.deserialize:235` assigns to **every** map regardless of the file (measured on all 70), and
  `timeLimitReached()` is `currentRound >= maxRounds − 1`, so **2 999 rounds are played** and any other value would
  be a rules change rather than a config choice. `perGameBudgetSeconds: 120` and `matchBudgetSeconds: 330` are the
  **largest** budgets of any year in this repo and they are deliberate: bc17 is the joint-longest year (2 999 rounds)
  and by far the heaviest per round (3–12 ms estimated, against bc23's measured 1.45–2.95 with no projectiles), so a
  game is 9–36 s and a match 27–108 s — a **3× margin** on `matchBudgetSeconds` at the pessimistic end. Making them
  larger would push the worst case in the 720 s envelope from 435 s toward the ceiling for no gain; making them
  smaller would risk a `deadline` on a slow runner. The four millisecond values are the repo-wide doctrine-phase
  numbers, identical across all ten variants, because the doctrine phase is year-neutral. All ten values are inside
  their existing `config_schema` bounds, so **no bound has to move**.

  `bc17`'s variant description: *"Best of three on the mixed pool, two thousand nine hundred and ninety-nine rounds
  each, in continuous space. Archons hire gardeners; gardeners plant bullet trees that pay a bullet a round once
  grown, and build soldiers, tanks, scouts and lumberjacks. Bullets travel: a shot crosses two units a round and the
  first body its line touches takes the damage, whoever's it is. A lumberjack's strike hits everything within two of
  it, including its own farm. Any robot can spend bullets on victory points, and a point costs seven and a half
  bullets on the first round and twenty on the last — so waiting is expensive. A thousand points ends the game on the
  spot, and so does losing your last robot. Otherwise the winner at the round limit is decided by points, then by
  trees standing, then by bullets in the bank."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level (`CoworldVariant` is
  `additionalProperties: false` and rejects a variant-level `num_agents` — cogame-goofspiel-oshi-zumo 0.1.0,
  2026-08-26).

  **The `<SEATS>` cross-check, named explicitly.** `.github/workflows/ci.yml` substitutes **`<SEATS>` = 2** into the
  `docker-smoke` job, and `tools/ci/docker_smoke.sh` takes the seat count **solely** from
  `certification.game_config.num_agents` (`:141-190`), hard-failing with `SEAT-COUNT FAIL:` if the workflow's value
  disagrees — and it also refuses a `SMOKE_CONFIG_OVERRIDE` that tries to change `num_agents` (`:199-201`). Since the
  cert fixture keeps `num_agents: 2` and the bc17 variant declares `num_agents: 2`, the two independent declarations
  agree. **There is exactly one seat number in this note and it is 2.**

  **Certification fixture — UNCHANGED, and stays on `bc26`.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps `"year": "bc26"`,
  **`"num_agents": 2`** and its existing fast settings (`pool: small`, `seed: 1`, `gamesPerMatch: 1`,
  `maxRounds: 400`, `attempt1Ms: 4000`, `retryMs: 2000`, `doctrineBudgetMs: 9000`, `perGameBudgetSeconds: 40`,
  `matchBudgetSeconds: 45`, `connectTimeoutMs: 15000`). There is **no bc17 certification fixture in v1** (§Out of
  scope): certification is the platform's contract check, it already passes on bc26, and re-pointing it at the
  newest and heaviest year module would put the release at the mercy of it for no gain — and bc17's own timing
  (§The game) would not fit `coworld certify`'s 60 s default anyway. bc17 is proven instead by its own `docker-smoke`
  episode (§Tests), which produces a real bc17 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** A **minor version bump of the same coworld** — **`0.9.0 → 0.10.0`**, bumped at **phase
  40, not by the build and not by this note** — because it adds a variant and optional results properties without
  changing any existing *rule* and without moving any schema bound. `GameVersion` goes **`GV12 → GV13`** and
  `ReplayCompatibleGameVersions` is **extended** to `["GV04",…,"GV12","GV13"]`, so every hosted bc16/bc19–bc26 replay
  keeps rendering (the bc20 learning: extend, never reset, and claim the version across branches with
  `tools/ci/check_gameversion.sh`). **This run's one year-neutral code change is purely additive** — four new procs in
  `fdlibm.nim` — so no recorded byte changes meaning, and **phase 20 regenerates every committed replay fixture in the
  bump commit** (§Interface facts). The release goes through the existing `coworld-release.yml` with the same step
  order (build → certify → upload-policies → upload-coworld → secret put); **certify runs against bc26, exactly as
  before**, and `release-result.json` must still show `canonical: true` and `certify.replay_liveness` containing
  `skipped (static replay bundle declared`.

- **Branch discipline.** All work lands on the branch **`bc17-year-module`**, PR-then-merge, and **`ci.yml`'s
  `on.push.branches` list (`.github/workflows/ci.yml:26-29`) gains `bc17-year-module`** beside `main`,
  `bc16-year-module`, `bc19-year-module`, `bc20-year-module`, `bc21-year-module`, `bc22-year-module`,
  `bc23-year-module`, `bc24-year-module` and `bc25-year-module`. The branch is rebased onto `origin/main` before
  every push. **The leagues, variants, modules, maps, atlases and versions of bc16 and bc19–bc26 are never touched.**
  If a sibling branch lands `GV13` first, this branch rebases to `GV14` and extends the compatibility list again —
  the bc20 precedent, and `tools/ci/check_gameversion.sh` is the thing that catches it.

  bc17 touches exactly these shared files — `sim_types.nim`, `fdlibm.nim`, `baselines.nim`, `sheet.nim`,
  `years/registry.nim`, `years/dispatch.nim`, `render.nim`, `broadcast.nim`, `results.nim`, `match.nim`,
  `client/replay_broadcast.html`, `coworld_manifest_template.json`, `tools/ci/policies.json`,
  `tools/gen_year_constants.py`, `.github/workflows/ci.yml`, `docs/PARITY.md`, `docs/PROTOCOL.md`, `docs/REPLAY.md`,
  `NOTICE`, `README.md`, `tests/test_manifest.nim`, `tests/test_viewer.nim`, `tests/test_determinism.nim`,
  `tests/test_constants.nim`, `tests/test_sheet.nim`, `tests/test_baselines.nim`, and **every
  `tests/fixtures/replay-*.json`** (regenerated for the `GV13` stamp) — and **every edit to each of them is additive**
  (a new enum value, a new `case` arm, a new appended block, a new list entry, four new procs, a regenerated
  fixture). **There is no subtractive or bound-moving edit anywhere in this run.** **Everything else on `main` is
  untouched**: no bc16/bc19/bc20/bc21/bc22/bc23/bc24/bc25/bc26 module file, map, atlas or variant is edited.

- **`tools/ci/policies.json`** gains the bc17 set beside the nine year sets already there — the file is **repo-wide
  and carries 4 entries per year (40 after this run)**. A scripted champion is a failure state; filler versions must
  differ from champion versions. **Exactly these four bc17 entries, with these labels:**
  ```json
  [{"name":"battlecode-bc17-orchard","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text, §Decisions>","PLAYER_POLICY_LABEL":"orchard"}},
   {"name":"battlecode-bc17-tankrush","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text, §Decisions>","PLAYER_POLICY_LABEL":"tankrush"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-orchard","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"orchard","PLAYER_POLICY_LABEL":"orchard"}},
   {"name":"battlecode-examplefuncsplayer17","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer17",
           "PLAYER_POLICY_LABEL":"examplefuncsplayer17"}}]
  ```
  | policy | kind | env | owner | league role |
  |---|---|---|---|---|
  | `battlecode-bc17-orchard` | **LLM prompt** | `PLAYER_PROMPT` | **daveey** (the CI token's own player) | champion #1 — the farm-and-buy doctrine |
  | `battlecode-bc17-tankrush` | **LLM prompt** | `PLAYER_PROMPT` | **daveey-1** (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) | champion #2 — the rush / swarm / bank doctrine |
  | `battlecode-orchard` | scripted | `PLAYER_SCRIPTED=orchard` | — | filler (the strong chassis on default knobs) |
  | `battlecode-examplefuncsplayer17` | scripted | `PLAYER_SCRIPTED=examplefuncsplayer17` | — | filler (the weak floor) |

  `image` is the **player** service's image (the 2026-09-03 lesson: `cogame-battlecode` alone matches nothing
  `compose build` produces and fails at "Docker image is not available locally"). **Champion #2 carries the
  `"player"` field** and is uploaded while `daveey-1` is the active player. LLM credentials reach the **game**
  container through the manifest env; the player pods need no Bedrock sidecar in this lineage.

  **Release dispatch shape, decided: dispatch `coworld-release.yml` with a `policies` OVERRIDE limited to exactly the
  four bc17 entries above** (the bc20 pattern), so the release does not recut vN+1 of the 36 bc16/bc19–bc26 policies
  the nine existing leagues have seated (LEARNINGS 2026-09-08: dispatching the whole file recuts every sibling year's
  policies). **Phase 40 must assert the filter returns exactly 4 before dispatching.** If the override is ever
  dropped and the full file is used instead, phase 50 must take its labels from **that** release's
  `release-result.json` and never from remembered ones (the bc21 learning).

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **tenth league**, created beside the bc16/bc19–bc26 ones, touching none of them and not the game's default league:

| field | value |
|---|---|
| `league_key` | `bc17` |
| `league_name` | `Battlecode 2017 — Robotic Wildlife Fund` |
| `default_variant_id` | `bc17` |
| `short_name` | `bc17` → **`softmax.com/battlecode/bc17`** (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc17-orchard` (owned by **daveey**), `battlecode-bc17-tankrush` (owned by **daveey-1**) — deliberately the year's two poles: the economy the season converged on against the rushes and swarms it started with |
| fillers (scripted) | `battlecode-orchard`, `battlecode-examplefuncsplayer17` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues` filtered on
`game.coworld_name` returns several rows; **select by `league_key`/name client-side, never positionally or by count**
(LEARNINGS 2026-09-08: the count is a prediction, not a fact). Fillers are set **before** the first `trigger-round`.
**The verify slug is `battlecode/bc17`, not `battlecode-2017`**: `softmax.com/battlecode-2017` does not exist, and the
phase-60 check-6 link and the phase-70 play link both take `softmax.com/battlecode/bc17`. The atlas slug is likewise
`battlecode/bc17`.

### Licensing — the exact `NOTICE` paragraphs phase 20 must add

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged by the repository
itself. **Every 2017 upstream is also AGPL-3.0**, so — unlike the 2016, 2019 and 2020 sources, for which
`NOTICE` records a GPLv3 §13 / AGPLv3 §13 combination argument — **there is no licence-compatibility question here at
all: the licences are identical.** `NOTICE` gains **three** sections, appended after the existing bc19 ones:

**1. `## battlecode/battlecode-server-2017 engine — AGPL-3.0`**

> Repository: <https://github.com/battlecode/battlecode-server-2017>, pinned at commit
> **`165d8a8ef24f03e13a101bb8bc9f5b32dcb33c6c`** (`HEAD` of `master`, 2017-03-26). **The repository
> root `COPYING` is the GNU Affero General Public License v3 (34 520 bytes) and it is the ONLY licence
> file anywhere in the tree** — verified — so every file used below is covered by that one licence,
> **the same licence this repository carries**. The published artefact `org.battlecode:battlecode:2017.1.6.2`
> (a fat jar, sha256 `9254e89268fd6efb72cafc037e3eded006aefd1d19aa44195c945b43ceb7bff9`, 14 576 275 bytes)
> is the same work; it bundles `gnu/trove` (LGPL-2.1), `net/sf/jsi` (LGPL/BSD), the Kotlin standard
> library, flatbuffers-java, Apache Commons, SLF4J, Java-WebSocket and ObjectWeb ASM, **none of which is
> redistributed by this repository**: the jar is downloaded in CI and never enters an image.
>
> What derives from it, named individually: `src/battlecode/years/bc17/{geom,index,units,world,
> ballistics,actions,trees,rules,maps,knobs}.nim` — the 2017 rule set **hand-written in Nim from reading
> the source** (a behaviour port, not a translation of copied files) from `world/{GameWorld,ObjectInfo,
> InternalRobot,InternalTree,InternalBullet,RobotControllerImpl,LiveMap}.java` and
> `common/{GameConstants,RobotType,MapLocation,Direction}.java`, with `specs-1.6.2.html` as the
> human-readable spec — **where the spec and the engine disagree the engine wins**, and all six
> disagreements plus every deliberate difference are in `docs/RULES-BC17.md`;
> `src/battlecode/years/bc17/trove.nim` — the **observable iteration order** of
> `gnu.trove.map.hash.TIntObjectHashMap` (trove4j 3.0.3, **LGPL-2.1**), reproduced because
> `GameWorld.updateTrees` accumulates a float32 sum in it; **this file vendors no trove source and no
> trove bytecode**, it reproduces the behaviour of a documented open-addressing scheme hand-written in
> Nim, and this paragraph records the dependency and its licence because reproducing a library's
> iteration order is a derivation of its behaviour; `src/battlecode/fdlibm.nim`'s `fdlibmSin`,
> `fdlibmCos`, `fdlibmAtan`, `fdlibmAtan2` and `remPio2Medium` — ports of **fdlibm 5.3**, the algorithm
> `java.lang.StrictMath` is specified against, whose original Sun Microsystems notice is reproduced in
> that file's header; `src/battlecode/years/bc17/constants.nim` — **generated** by
> `tools/gen_year_constants.py --year bc17` by reflecting `GameConstants` and `RobotType` out of the
> jar's own classes and byte-diffed in CI; `data/maps/bc17/*.json` — 22 of the engine's own 70
> `battlecode/world/resources/*.map17` flatbuffers, converted at build time by
> `tools/convert_maps_bc17.py` (the runtime sim has no flatbuffer reader); and
> `tools/oracle/bc17/Bc17Trace.java` plus the seven oracle bots, written against the engine's own API and
> **compiled and run only in CI**.
>
> **The engine is used only at CI time and at map-conversion time**, from the published jar, verified by
> sha256, byte size and `GameConstants.SPEC_VERSION`. **No JDK, no JRE, no Java and no upstream Java
> source exists in any image this repository builds.**
>
> **Three hunks of the engine are patched, in CI only, and all three are recorded in `docs/PARITY.md`
> §bc17**: `strictmath.patch` rewrites the eleven `Math.{atan2,sin,cos,sqrt}` call sites in
> `common/Direction.java`, `common/MapLocation.java` and `world/InternalBullet.java` to `StrictMath` (a
> normalisation the 20 000 000-sample measurement proves is observationally neutral at `float32`);
> `rtree_order.patch` replaces `ObjectInfo`'s six `net.sf.jsi` `nearestN` queries with a deterministic
> `(squared distance, id)` enumeration, because jsi's exact-tie order is an artefact of the R-tree's
> insertion history and is not stable even against itself; and
> `examplefuncsplayer17/determinism.patch` replaces the scaffold bot's three `Math.random()` calls with a
> per-robot `java.util.Random(id)`.

**2. `## battlecode/battlecode-scaffold-2017 — the licensed weak floor, AGPL-3.0`**

> Repository: <https://github.com/battlecode/battlecode-scaffold-2017>, pinned at commit
> **`76e7b51e06088fdcce2f6a6b97aff21782ae20d0`** (2017-08-25). Root `LICENSE` is the GNU Affero General
> Public License v3.
>
> `src/battlecode/years/bc17/chassis/examplefuncsplayer17.nim` is a **statement-for-statement port** of
> `src/examplefuncsplayer/RobotPlayer.java` with the one hunk of `determinism.patch` applied (a
> deterministic per-robot RNG in place of `Math.random()`, whose draw ORDER — including Java's `&&`
> short-circuit — is preserved exactly). It is the parity oracle's other side, so it **may not gain
> behaviour**. Two of its helpers are also the behaviour source for two procs of the strong chassis, and
> saying so is cheaper than leaving it implicit: `kit.nim`'s seven-direction obstacle probe is `tryMove`
> (`RobotPlayer.java:215-244`) and `micro.nim`'s bullet-collision test is `willCollideWithMe`
> (`:253-277`). **Nothing else in `orchard` comes from anywhere but the engine source, the 1.6.2 spec
> page and this run's own design.**

**3. `## benzyx/omega-ruby-battlecode, humford/Battlecode2017, SiestaGuru/Battlecode-2017---Bruteforcer — NOT READ`**

> All three repositories carry **no licence anywhere**, so this run treats them as unreadable. They are
> **not cloned, not read, not copied, not vendored, not compiled, not translated and not fetched**, and
> none contributes a single line to this repository. Where this repository's documents describe "the play
> the 2017 meta made", that is a statement about the run's source idea's characterisation of the 2017
> season, not a claim about any repository's contents.

**4. `## battlecode/battlecode-client-17 sprites — AGPL-3.0`**

> Repository: <https://github.com/battlecode/battlecode-client-17>, pinned at commit
> **`feb3e03820ba442ab233f05d2432b0dc2833aa98`** (2017-03-26). **The root `LICENSE` is the GNU Affero
> General Public License v3; `package.json` declares `"license": "GPL-3.0"`. The two disagree, and both
> are compatible with this repository's AGPL-3.0** — recorded here rather than papered over.
>
> `data/atlas_bc17.png` and `data/atlas_bc17.json` are cut by `tools/build_sprite_atlas_bc17.py` from
> exactly **twenty-one** files: `src/static/img/sprites/{archon,gardener,lumberjack,soldier,tank,scout,
> bullet_tree}_{red,blue}.png` (fourteen, 32×32 and 50×50),
> `src/static/img/map/{full_health_tree,low_health_tree,sapling,tree_bullets,tree_robots}.png` (five,
> 32×32) and `src/static/img/bullets/bullet_{slow,medium,fast}.png` (three, 26/18/16 — one per bullet
> speed). **`sprites/*_neutral.png`, `sprites/recruit_*.png` (a unit type the shipped `RobotType` does not
> have), `sprites/unknown.png`, `src/static/img/controls/`, `yellow_star.png` and `map/tiled_1.jpg` are
> NOT used, NOT cut and NOT shipped.** No client code is shipped, embedded or built.


`docs/RULES-BC17.md` carries the full **§Divergences** list, which is exactly: **V1–V6** verbatim from §Sim module
("Decided divergences"); **D1–D5** verbatim from §Sim module ("Determinism"), including `GameWorld.rand` being
constructed and never read; **F1–F5** verbatim from §Sim module ("The float ledger"), including the three CI-only
engine patches and the 20 000 000-sample measurement; the **six spec-vs-engine disagreements** with their `file:line`;
the **`deadline` wall-clock stop** as a coworld concept recorded as one load-bearing record; the provenance of **both
chassis** (`orchard` ours, `examplefuncsplayer17` a port that may not gain behaviour); the chassis file layout, if the
builder merges any two modules; and **the score's clamp of a negative `bullet_worth`**, with the note that the
*winner* is decided on the engine's exact comparisons while *points* are decided on float32 shares, so the two can
disagree on a razor-thin margin. **It restates rather than paraphrases: a divergence described two different ways in
two documents is a divergence nobody can check.**

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` = `cogame-battlecode`,
**`<SEATS>` = 2**). The sandbox runs none of it; **CI is the only harness**. The `test` job's `timeout-minutes` goes
**150 → 180** (bc17's shards are the heaviest in the repo — 2 999 rounds with bullets in flight — and every file runs
twice, debug and `-d:release`).

**Two conventions every bc17 test file obeys, because the repo has been bitten by both:** **never zero
`perGameBudgetSeconds`** in a helper (`match.nim:638` clamps it to `max(1, min(field, remaining))`, so a zeroed field
buys a **one-second** budget while `rules.nim` treats 0 as unbounded — the symptom is a shard that passes in
`-d:release` and fails in debug; use the `if perGame > 0:` convention of `tests/test_bc23_replay.nim:69`); and
**guard every `games[0]`** behind a non-empty check, with tolerant end-reason assertions.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

The nineteen unit shards below are stated as a table, densely, because each one is a file and a claim rather than a
narrative. **Every row is a committed file, and every claim in it is an assertion phase 20 must write.**

| # | file | what it asserts |
|---|---|---|
| 1 | `tests/test_bc17_units.nim` | the six-row table against the generated constants (costs, health, radii, strides, both sight radii, bullet speeds, attack powers, cooldowns); **`ARCHON.bulletCost == −1` and `ARCHON.attackPower == −1`**, so `canAttack()` is false for ARCHON and GARDENER and true for the other four; `canHire`/`canBuild`/`isHireable`/`isBuildable`; and `getStartingHealth()` — **a SOLDIER born at exactly 10.0, a TANK at 40.0, a SCOUT at 2.0, a GARDENER at 40.0** |
| 2 | `tests/test_bc17_geom.nim` | `Direction(dx, dy)` for the eight cardinals **and for `(0,0)`, which the engine turns into `(0,1)`** (`Direction.java:83-85`); `reduce` at `±(float)π`, one ulp either side, and at `+3π` (the `circles` correction); `rotateLeft/RightDegrees(20)` and `(15)` giving the triad and pentad angles; `distanceTo` vs `distanceSquaredTo`; **`onTheMap(loc)` inclusive on all four edges** and `onTheMap(loc, r)` testing **only the four cardinal points** (a named vector where a circle overlapping a corner is accepted — the engine's own behaviour); and **`MapLocation(NaN, y)` passing NaN through**, because `x == Float.NaN` is always false (`MapLocation.java:33-34`) — a rule the port must not "fix" |
| 3 | `tests/test_bc17_widths.nim` | **one named vector per row of the F3 width table**, so a port that computes `hitDist` with the `perpDist` shape (or vice versa) fails a unit test rather than a 2 999-round trace diff |
| 4 | `tests/test_bc17_fdlibm.nim` | the ≈ 400 boundary vectors value-for-value and the eleven expression-shape digests byte-for-byte against `data/bc17/fdlibm_vectors.json` (F4); `fdlibmSin`/`fdlibmCos` **raising** outside `[−4, 4]`; and the proof the port is **not** a platform-libm wrapper (≥ 1 sample where `fdlibmSin(x) != sin(x)` at double level) |
| 5 | `tests/test_bc17_ballistics.nim` | the year's crux. `calcHitDist`: a shot at the centre of a radius-1 body at distance 5 (hit at `5 − 1`); a graze at exactly `perpDist == targetRadius` (**a hit** — the test is `>`) and one ulp beyond (a miss); a bullet **starting inside** the circle (forced to 0); a target **behind** the bullet (rejected); a target beyond `maxDist` (rejected); and a bullet **on the target's centre** (`toTarget == null` → 0). `updateBullet`: the **strict** minimum keeping the first candidate on a tie, the **tree/robot tie going to the robot**, exit through each of the four edges, a bullet hitting **its own team**, a bullet hitting **the robot that fired it** after it moved onto it, and the muzzle collision. **Plus the hoist property**: hoisted and unhoisted forms agree bit-for-bit on 10⁶ random configurations |
| 6 | `tests/test_bc17_trees.nim` | a planted tree at **10.0** growing `+0.5` while `roundsAlive <= 80` (the exact 81-value sequence, **zero income throughout**), the first income at `roundsAlive == 81` paying `health × (1/50)`, `−0.5` decay after; `waterTree` adding 5 and **clamping at 50 so watering a 48-HP tree wastes 3**; a neutral tree at `200 × radius` that **never decays and cannot be watered**; `damageTree` clamping negatives to 0 and killing on an exact `== 0`; and **`destroyTree`'s `fromChop` gate** — a bullet, a strike, a body attack or decay releases **nothing**, a chop releases the bullets **and** the contained robot on the chopping team **after killing any SCOUT overlapping the spawn circle** |
| 7 | `tests/test_bc17_actions.nim` | the twelve actions of rule 6 with their guards in the engine's order: one move and one attack per turn in **either** order; `incrementMoveCount` landing **before** the tank branch, so a body-attacking tank has spent its move; the over-stride **re-projection**; the TANK/SCOUT emptiness split (a SCOUT may end on a tree, a SOLDIER may not); the shot gates (**no ARCHON, GARDENER or LUMBERJACK; no SCOUT triad or pentad**); the **centre-left-right** spawn order and the resulting bullet id sequence; `strike` hitting own robots and own trees; `chop`/`shake`/`water` at `bodyRadius + targetRadius + 1` and refused one ulp beyond; `water` refused on a neutral tree and twice a turn; `shake` once a turn **by any type**; the spawn circles at `bodyRadius + 0.01 + targetRadius`; the **shared 10-turn cooldown between planting and building**; `broadcast` at 0 and 9 999 and refused at −1 and 10 000; and **`donate`'s exact arithmetic** — the price at rounds 1, 1 500 and 2 999, `floor(bullets/price)`, **the whole amount deducted including the destroyed remainder**, and the immediate win at 1 000 |
| 8 | `tests/test_bc17_economy.nim` | `BULLETS_INITIAL_AMOUNT 300` once per team; **the income cliff** at supply 0 (2.0), 100 (1.0), 199 (0.01), **200 (exactly 0.0)** and 300 (0.0), plus the measured whole-game fact that two idle factions finish 2 999 rounds with **exactly `300.000000000`**; the tree-income sum in trove order (D1) against a recorded vector; and `bullet_worth = supply + Σ bulletCost` with an ARCHON contributing **−1** |
| 9 | `tests/test_bc17_execorder.nim` | initial bodies in **map-file id order** — named vectors from `HouseDivided` (**Team B's archon id 54 precedes Team A's id 55**) and `Chess` (ids 1028–1031 interleaving `B, A, B, A`); robots appended on spawn; **a bullet inserted immediately before its parent**, so it first moves the round *after* it is fired; removal **by value**; the per-round **snapshot**, so a body spawned this round does not act this round; and a body killed after acting shifting nothing |
| 10 | `tests/test_bc17_ids.nim` | the two `IDGenerator`s (D3): the first 8 robot and first 8 bullet ids for the three seeds measured here (98, 752, 753); **the bullet generator's two-block head start**; the 4 096-id block boundary and its reshuffle; **no draw per spawn**; and **the V3 guard** refusing a build that would issue an id above 32 000 (the test **documents that the engine would collide here**) |
| 11 | `tests/test_bc17_trove.nim` | the iteration order (D1): fresh capacity **23**; `forEachValue` descending on the two measured id sets; `clear()` retaining capacity; **the pre-compaction snapshot semantics**; auto-compaction after the countdown; 500 random spawn/destroy/clear sequences against a recorded oracle order; **`years/bc22/trove.nim` and `years/bc17/trove.nim` agreeing on `values(V[])` for the same sequence**; `TIntArrayList`'s insert-before and remove-by-value; and the proof that **`updateTrees` visits every tree exactly once even when a third of them die in one round** |
| 12 | `tests/test_bc17_index.nim` | the candidate order (D2): the normative `(distanceSquared, id)` comparator; the grid returning **exactly** `ObjectInfo`'s filtered set over 10 000 random configurations against a brute-force scan; `treeAtLocation`/`robotAtLocation` returning the nearest match; `senseNearbyRobots` **ascending by distance** so `robots[0]` is the nearest enemy; and the sight radii 14 / 10 / 7 and bullet-sight 20 / 15 / 10, inclusive at the boundary |
| 13 | `tests/test_bc17_clock.nim` | `ArchonOps = 3000`, `UnitOps = 1500`, `DormantOps = 0`; **the dormancy rule** — a built SOLDIER emitting no action on turns 1–20 with the exact health sequence `10, 12, … 50` and acting on turn 21, and a hired GARDENER born at 40/40 acting on its second round; the cap checked **before** each primitive; a synthetic chassis asking 5 000 ops ending its turn at the cap **with the world unchanged**; and **`decision_ops_peak < cap` for both chassis in every gate game** (V1) |
| 14 | `tests/test_bc17_endladder.nim` | `victory_points_reached` firing the instant a donation crosses 1 000 **and the round still finishing**; `all_robots_destroyed` on the last robot's death **with 40 trees standing**; the **double-fire** case where the later `setWinner` overwrites; the four rungs at 2 999 with a vector each, including **rung 2 counting a 10-HP sapling as much as a mature tree** and **rung 3 subtracting one per surviving archon**; `timeLimitReached()` firing at `currentRound == 2999` and **not** at 3 000; **no coin flip and no RNG on any end path**; and **no gate game ever reporting `fault`** (V5) |
| 15 | `tests/test_bc17_scoring.nim` | the points formula's float32 shares and truncation, one vector per weight; the 0–0 `share` returning 0.5; **the negative-`worth` clamp applied to the score and NEVER to the ladder**; points in `[0, 100]` and the seats summing to ≤ 100; the super-increasing property as arithmetic; **the documented case where `points` favours the loser** as an explicit expectation; and `results.scores` **strictly** ordering the winner above the loser on 500 random synthetic finals including clinched matches, with `winBonusFor("bc17") == 200.0` |
| 16 | `tests/test_bc17_maps.nim` | every committed map's size, origin, seed, `rounds == 3000`, archon ids and float coordinates, neutral-tree census and archon separations **matching §Sim module's measured table**; 30…100 in both dimensions with **equal archon counts of 1, 2 or 3**; a neutral tree's health **recomputed as `200 × radius`, not read from the file**; **no bc17 map name resolving to another year's file**; and **the `docker-smoke` seed drawing exactly `HouseDivided`** |
| 17 | `tests/test_bc17_sheet.nim` | every one of the eleven knobs: **absent → default AND recorded in `defaults_applied`** (and a **bc19** empty sheet still recording none, so the change is provably scoped); mistyped and unknown-enum → default + recorded; **the six integer knobs CLAMPING rather than defaulting**; enums case-folded, trimmed and `-`/space normalised; unknown keys recorded (≤ 16, ≤ 40 runes); **a submitted `chassis` recorded as unknown and never honoured**; rune-boundary truncation of `notes`/`motto` including astral-plane characters; the **16 384-byte** reply cap cut on a rune boundary; **`plainWords17()` non-empty, article-free and complete for every value of every knob**; and the envelope resolver from the bc17 side over seven payload shapes (`{"sheet":…}`, `{"doctrine":…}`, `{"protocol":…,"doctrine":…}`, `{"battlecode_2017_doctrine":…}`, a bare flat sheet, a payload with **both** a flat knob and a `doctrine` key (the flat one wins), and a two-object payload with no unwrap) each with its expected `sheet_envelope`, unwrapped **at most once** |
| 18 | `tests/test_sheet.nim` (extended) | the same resolver from the **year-neutral** side: every existing bc16/bc19–bc26 vector still parsing to the `Sheet` it did before, so this run is provably additive for the nine shipped years |
| 19 | `tests/test_bc17_examplefuncsplayer17.nim` | the weak floor statement for statement against a recorded oracle trace: the per-robot `java.util.Random(id)` stream and **the per-turn draw count for all four branch combinations** (the `&&` short-circuit); the archon's `randomDirection` → hire-gate → `tryMove` order and its two broadcasts **every turn**; the gardener's SOLDIER-then-LUMBERJACK gate order with the second gate's extra `isBuildReady()`; the soldier firing at **`robots[0]`, the nearest enemy**; the lumberjack's strike-then-chase at radius `1 + 2`; **the TANK/SCOUT fall-through killing the robot on its first turn**; and the seven-direction probe order (intended, ±20°, ±40°, ±60°). **It may not gain behaviour: it is one side of the differential oracle** |
20. **`tests/test_bc17_baselines.nim`** — **bounded orders and legality**:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the **same** `sheet.validate` the LLM path
      uses;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the moment it is
      emitted**: the actor's type permits it; at most one move and one attack per turn, at most one water, one shake;
      a move within `strideRadius` onto a circle that is on the map and empty (of trees too, unless the actor is a
      TANK or a SCOUT); a shot the faction can afford with the right shape for the type; a `chop`/`shake`/`water`
      target inside `bodyRadius + targetRadius + 1`; a build/hire/plant onto a clear on-map circle with the cooldown
      expired and the bullets in hand; a `broadcast` channel in `0 … 9999`; a `donate` amount the faction holds; **no
      donation below `bullet_reserve` unless `vp_donate_policy` is `rush_1000`**, **no `strike` whose own-HP cost
      exceeds the enemy's**, **no TANK walking onto its own tree**, and **no robot exceeding its op cap**;
    - (c) **`refused_actions == 0` for `orchard`** on both seats across the gate games — the bounded-orders assertion
      proper. **`examplefuncsplayer17` is explicitly EXEMPT and its exemption is asserted as such**: it draws a
      uniform random direction and therefore *must* sometimes try to walk into a tree or off the map, so
      `refused_actions == 0` on it would assert that the weak floor is not the weak floor. The test asserts
      `refused_actions[weak] > 0` instead, so a future "fix" to the oracle's other side fails loudly;
    - (d) `examplefuncsplayer17` **acts** — ≥ 1 gardener hired, ≥ 1 fighter built, ≥ 1 shot fired, ≥ 100 moves — but
      is **not** required to plant, water, shake, chop, donate, survive or compete;
    - (e) `orchard` beats `examplefuncsplayer17` on **3 seeds × 2 `small` maps, 6/6**.
21. **`tests/test_bc17_survival.nim`** — the **economic-survival gate** (the LEARNINGS 2026-09-03 pin), with an
    inverted control. **The key design point, stated because it is bc17-specific: in this year a faction does not get
    eaten, it FAILS TO COMPOUND.** There is no NPC threat and no escalating clock; the passive trickle is zero above
    200 bullets and only 2 a round at zero, so a faction that never plants a tree has an income of at most 2 a round
    against a unit price of 100 — it simply never has an army, and it can never buy a single victory point at 7.5+
    bullets without first earning them.
    - `orchard` vs `orchard`, all-defaults sheet, **3 seeds × 2 `small` maps = 6 games**, each to round 2 999. In
      **≥ 5 of the 6** the game must **reach the round limit or end on `victory_points_reached`** (i.e. **not**
      `all_robots_destroyed`) — the ≥ 4-in-5 shape the pin asks for, rounded up so the committed ratio is at or above
      it — and in **all 6** each seat must have: **still held at least one ARCHON at round 2 000**; hired ≥ 2
      GARDENERs; **planted ≥ 6 bullet trees and had ≥ 4 alive at round 1 500**; **had ≥ 3 trees MATURE (roundsAlive
      > 80) by round 600**; earned ≥ 400 bullets from trees; built ≥ 8 fighters; **watered ≥ 40 times** (a farm
      nobody waters is a farm that dies at 0.5 a round); dealt ≥ 200 tenths of damage; **bought ≥ 20 victory
      points**; and finished with ≥ 4 robots alive. **Across the two seats** at least one neutral tree must have been
      shaken on at least one of the six games, and **friendly-fire plus own-tree damage must be under 15 % of damage
      dealt**.
    - The same gate then runs as a **subprocess** against a **known-broken chassis** compiled behind
      **`-d:bc17BrokenChassis`** — an `orchard.nim` variant whose gardeners **plant but never water** (so the farm
      dies at 0.5 a round and the income curve never compounds), which **never donates** (so the victory-point floor
      cannot be met), and which **ignores `bullet_reserve`** and spends to zero (so the trickle is its only income) —
      and it **must come back red**. That control is chosen deliberately: it is exactly the failure a "did it build
      units?" check would pass, and it is the failure this year's economy makes possible. **A gate that cannot fail
      is not a gate.**
    - **The thresholds above are the design floor, not the committed numbers.** Phase 20 **measures** a healthy
      mirror and the broken control, sets the committed thresholds between them with margin (never below this note's
      floor), and records **both** measured ranges in the test's header comment, exactly as
      `tests/test_bc16_survival.nim` does. If a floor proves unsatisfiable on the measured healthy mirror, the
      resolution is the bc23 r1-F21/F22 one: **lower the committed number to roughly half the weak seat's measured
      value and record the measurement inline** — never drop the clause.
22. **`tests/test_bc17_knobs.nim`** — the knob-teeth gate, and the **direct enforcement of the anti-inert rule**.
    Paired seeded games (identical seed, map and opponent; the two factions identical except one knob at its low and
    high setting, 3 seeds each), each asserting a named, signed delta. Thresholds live in one table so tuning is a
    one-line change, and the header records every substituted statistic (the bc21 r1-F6 fix). **Plus one assertion
    over the whole sweep: in every one of the 78 games, BOTH seats hired ≥ 1 gardener, planted ≥ 3 trees and still
    had a robot alive at round 1 500** — i.e. **no setting of any knob produces an inert faction**.

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `tree_farm` → `tank_rush` | tanks built by round 600 up ≥ 2 **and** trees planted down ≥ 40 % **and** mean distance of own fighters from own archons up ≥ 50 % |
    | `opening` | `tree_farm` → `lumberjack_swarm` | lumberjacks built up ≥ 4 **and** enemy trees felled up ≥ 6 **and** `bullets_fired` down ≥ 60 % |
    | `opening` | `tree_farm` → `scout_squat` | scouts built up ≥ 3 **and** enemy gardeners killed up ≥ 1 **and** `shake_actions` up ≥ 4 |
    | `gardener_count` | 1 → 7 | gardeners built up ≥ 4 **and** trees planted up ≥ 8 **and** fighters built down ≥ 25 % |
    | `farm_layout` | `hex` → `line` | mean pairwise distance between own trees up ≥ 60 % **and** own trees lost to a single strike down ≥ 50 % **and** `water_actions` per tree down ≥ 15 % (the gardener has to walk), on `TreeFarm` |
    | `soldier_tank_ratio` | 0 → 100 | tanks built up ≥ 3 **and** soldiers built down ≥ 70 % **and** `damage_dealt_tenths` per bullet fired up ≥ 100 % |
    | `lumberjack_share` | 0 → 80 | lumberjacks built up ≥ 4 **and** `strike_actions` up ≥ 20 **and** enemy trees felled up ≥ 8 **and** `own_trees_damaged_tenths` up ≥ 20 (the cost is the point) |
    | `scout_harass` | 0 → 80 | scouts built up ≥ 4 **and** own robots lost up ≥ 3 (a scout has 10 HP — the cost is the point) **and** enemy gardeners killed up ≥ 1 |
    | `vp_donate_policy` | `never` → `rush_1000` | `victory_points` up ≥ 200 **and** fighters built down ≥ 50 % **and** the share of games ending in `victory_points_reached` up |
    | `vp_donate_policy` | `never` → `endgame_dump` | `bullets_end_tenths` up ≥ 20 000 **and** `victory_points` up ≥ 20 **and** the share of games decided on rung 3 (`more_bullet_worth`) up |
    | `shake_neutral_trees` | `never` → `dedicated` | `shake_actions` up ≥ 10 **and** `bullets_shaken_tenths` up ≥ 300, on `Chess` (892 trees hold bullets) |
    | `chop_policy` | `never` → `harvest` | `chop_actions` up ≥ 20 **and** `robots_released_from_trees` up ≥ 1, on `GreenHouse` (every tree holds a robot) |
    | `bullet_reserve` | 0 → 1500 | rounds with a bullet supply below 1 down ≥ 80 % **and** `bullets_fired` down ≥ 20 % (the trade-off is the point) |
    | `defend_radius` | 1 → 40 | own gardeners killed down ≥ 30 % **and** enemy trees felled down ≥ 25 % |

| # | file | what it asserts |
|---|---|---|
| 23 | `tests/test_bc17_perf.nim` | a full 2 999-round game on `Chess` (**64×64, 924 neutral trees** — the map that maximises the bullet candidate count) with both seats on the bullet-maximising configuration of §The game, **in ≤ 60 s**; failing it means `gamesPerMatch: 3 → 2 → 1` |
| 24 | `tests/test_bc17_arith.nim` | `BULLET_TREE_DECAY_RATE == 50f/100f == 0.5f`, `BULLET_TREE_BULLET_PRODUCTION_RATE == 1f/50f`, `WATER_HEALTH_REGEN_RATE == 50f/10f == 5f` and `VP_INCREASE_PER_ROUND == 12.5f/3000f` asserted **as the engine computes them**, not as decimal literals; the income cliff at exactly 200; the named products the engine really computes (`0.04f × 400f`, `0.2f × 50f`, `0.01f × 300f`, `7.5f + 0.0041666666f × 2999`); **and a grep over `src/battlecode/years/bc17/**` asserting no bare `float`/`float64` declaration outside `geom.nim`'s named double intermediates**, so the float32 claim is enforced rather than asserted |
| 25 | `tests/test_determinism.nim` (extended) | same seed + same sheets ⇒ identical hash chain, twice in one process and across a save/load; **the raw bullet-supply bits folded into the chain**, asserted by a vector that perturbs the tree-income sum by one ulp and shows the chain diverging on that round; and **record → re-derive for every bc17 end reason** (`victory_points_reached`, `all_robots_destroyed`, all four ladder rungs, and the `abandoned`/`deadline` stop applied by the same proc on both paths) |
| 26 | `tests/test_bc17_replay.nim` | a bc17 replay round-trips; **a strict UTF-8 parse of the written bytes**; the viewer's re-derivation reproducing every recorded per-round hash; every body's float position, health, type and counters, every bullet's position, direction, speed and damage, both supplies, both VP totals, the broadcast arrays, the exec order, the trove layout and both `IDGenerator` states re-deriving identically from events + config + seed **with nothing stored**; `plan.maps` carrying all three drawn maps even on a two-game clinch; `seats[].sheet_envelope` and `sheet_submitted` round-tripping; **a 2 999-round game with ≥ 300 bullets in flight recording under 400 KB** (the self-sufficiency claim, measured); and **every event kind respecting its per-game bound**. End-reason assertions tolerant, every `games[0]` guarded |
| 27 | `tests/test_bc17_beats.nim` | the **beat contract** (§Viewer) from the committed `tests/fixtures/replay-bc17.json`: **≥ 26 beats over ≥ 11 distinct kinds**, every label non-empty and ≤ 120 runes, every kind inside the thirteen-kind vocabulary, and a `html[data-year="bc17"] .beat-marker.<kind>` rule in `client/replay_broadcast.html` for **every kind the fixture actually emitted** — emission, label and style, all three, from the committed artefact |
| 28 | `tests/test_manifest.nim` (extended) | the triple-sync tripwire, now **ten years** wide: the results key set + the `reason` enum == the manifest `results_schema` == the key set `docker_smoke.sh` asserts; **`num_agents` present in all ten variants' `game_config` and in `certification.game_config`, and absent at every variant top level**; `config_schema.year.enum == ["bc26","bc20","bc21","bc24","bc25","bc23","bc22","bc16","bc19","bc17"]`; **every `config_schema` bound UNCHANGED from `main` and every one of the ten variants' values inside it**; **`player[]` containing exactly the ids in `certification.players`** and `len(certification.players) == certification.game_config.num_agents`; `end_reason` containing the five new values plus `highest_id` and `abandoned`; every array bounded; `tokens` declared and required but never valued in a `game_config`; **both `game.protocols` keys** and `game.docs.readme` plus **all twelve** `pages` as `{type, value}` objects; and the installed `coworld` CLI's own `validate_upload_manifest` / `_load_template_manifest` accepting the template |
| 29 | `tests/test_constants.nim` (extended) | the `test` job gains a *"Fetch the pinned 2017 jar"* step (a sha256- and size-verified `curl` of the Maven artefact — no Gradle) and *"The bc17 maps match the jar"* running `tools/convert_maps_bc17.py --jar "$BC17_JAR" --out data/maps/bc17 --check`, which re-walks all 22 flatbuffers and **byte-diffs** them. The shard reads `getEnv("BC17_JAR")` and skips loudly when absent, as the bc22/bc23/bc25 arms do. **The constants byte-diff needs a JVM for reflection and therefore runs in `parity-oracle-bc17`; the map conversion is pure Python and runs here** — said explicitly so nobody looks in the wrong job |
| 30 | `tests/test_viewer.nim` (extended) + `tools/wasm_replay_smoke.cjs` | the emitted wasm module loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc17** fixture; the bc17 game block shadows no `ChromeCommon` alias and no other year's game-block name (the tandem scar); **`chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256**; `#bc17-doctrines` carries a dismiss control, is capped-and-scrolling and sits outside `var(--band)`; **every `#bc17-*` rule scoped to `html[data-year="bc17"]`**; `relayout()`'s `--statrail` set naming `bc17-econ` and `bc17-units` and **its fixed point converging for aspect ratios 0.3, 1.0 and 3.33**; the hidden-starter-id list **derived from the page source** and covering all nine other years' boxes; and the **endcard fixes 1–5** of §Viewer |
| 31 | `tests/test_baselines.nim` (extended) | `ScriptedChassis` and `Baseline` have **no duplicate strings** across all twenty values, `defaultBaselineFor("bc17") == blOrchard`, and the bc17 `PLAYER_SCRIPTED` resolution table of §Decisions holds for every listed spelling plus an unrecognised one |

### `parity-oracle-bc17` job — the 2017 Java engine as a CI-only oracle

**The recipe below is built on facts measured in this sandbox, not guessed.** The tier structure is modelled on
`parity-oracle-bc16` (`.github/workflows/ci.yml:2700`) — same nimby/Nim install, same `nim.cfg` regeneration, same
streaming comparator, same ledger discipline. **`timeout-minutes: 90`** (bc16's is 75; bc17's games are 2 999 rounds
with real ballistics and there are 54 compared pairs, and phase 20 records the measured JVM seconds in
`docs/PARITY.md`). **If the measured wall clock exceeds 80 minutes, phase 20 reduces Tier A″ from nine pairs to the
six `small` pairs and records that reduction in `docs/PARITY.md` §bc17 with the measurement** — a bounded, decided
fallback, not a discovery.

`tools/oracle/bc17/jar.lock`, verbatim:

```json
{
  "url": "http://battlecode-maven.s3-website-us-east-1.amazonaws.com/org/battlecode/battlecode/2017.1.6.2/battlecode-2017.1.6.2.jar",
  "version": "2017.1.6.2",
  "spec_version": "1.0",
  "bytes": 14576275,
  "sha256": "9254e89268fd6efb72cafc037e3eded006aefd1d19aa44195c945b43ceb7bff9",
  "engine_commit": "165d8a8ef24f03e13a101bb8bc9f5b32dcb33c6c",
  "scaffold_commit": "76e7b51e06088fdcce2f6a6b97aff21782ae20d0",
  "client_commit": "feb3e03820ba442ab233f05d2432b0dc2833aa98",
  "jdk": "8",
  "note": "MEASURED: the published .pom carries NO <dependencies> element and the jar is a FAT jar -- 10210 entries, 116 battlecode classes, and it bundles gnu/trove (1618), net/sf/jsi (11), kotlin (~380), com/github/davidmoten flatbuffers, org/objectweb/asm (59 -- the instrumenter), org/apache/commons/{lang3,cli,io} (381), org/slf4j (45), org/java_websocket (68), com/thoughtworks/xstream (12) and the shaded junit/mockito/hamcrest test tree -- SO THIS JOB NEEDS NO GRADLE, NO MAVEN RESOLUTION, NO deps.lock AND NO SHIM. It also carries all 70 battlecode/world/resources/*.map17 resources, so no --map-dir is needed either and tools/convert_maps_bc17.py reads the maps straight out of the jar with no JVM. Unlike 2016 there IS a GameConstants.SPEC_VERSION (\"1.0\"), so the pins are sha256 + byte size + SPEC_VERSION read by reflection. IT MUST RUN ON TEMURIN 8: the jar bundles a 2017-era ASM 5.0.4 and the whole instrumenter is built for Java 8 class files; under a modern JDK the instrumenter throws IllegalArgumentException inside ClassReader.<init> on every player class load, nothing is ever built, the game ends in one round and the job would exit 0 while proving nothing (the bc22/bc23 measurement, and 2017's ASM is the same vintage). Bc17Trace.java exits 3 on that condition. NOTE that gnu/trove AND net/sf/jsi ARE both present and both ARE load-bearing here, unlike 2016: trove's TIntObjectHashMap iteration order is observable through GameWorld.updateTrees's float32 sum and through senseBroadcastingRobotLocations, and jsi's RTree candidate order is observable through senseNearbyRobots -- see docs/PARITY.md section bc17, D1 and D2."
}
```

`tools/oracle/bc17/build_oracle.sh`, modelled line-for-line on `tools/oracle/bc16/build_oracle.sh`:

1. **Verify the jar by sha256 AND byte size** against `jar.lock`, then **by `GameConstants.SPEC_VERSION`** read with
   `java -cp <jar>` reflection (2017 *has* the field, unlike 2016, so it is a third independent pin).
2. **Assert the jar really is self-contained**: the listing goes to a **file** first (`unzip -l | grep -q` takes
   SIGPIPE the moment grep is satisfied and under `set -o pipefail` fails a perfectly good jar — the bc16 scar), then
   require `org/objectweb/asm`, `gnu/trove`, `net/sf/jsi`, `com/google/flatbuffers` and **exactly 70**
   `battlecode/world/resources/*.map17` entries.
3. **Apply the three patches and assert each applied**: `git apply --check` then `apply` for `strictmath.patch`
   (assert **eleven** changed lines and that `grep -c 'Math\.\(sin\|cos\|atan2\|sqrt\)'` over the three patched files
   is **0**), `rtree_order.patch` (assert `grep -c nearestN` over `ObjectInfo.java` is **0**) and
   `examplefuncsplayer17/determinism.patch` (assert `grep -c 'Math\.random'` is **0**). **These are the only three
   places the oracle is not the published engine**, and `docs/PARITY.md` §bc17 names all three with their reasons.
4. **Assert the weak floor has not gained behaviour**: `grep -qF` for `plantTree(`, `water(`, `donate(`, `shake(`,
   `chop(`, `RobotType.TANK` and `RobotType.SCOUT` in `examplefuncsplayer17/RobotPlayer.java` and **fail on a hit**,
   because it is one side of the differential oracle.
5. **Compile with plain `javac -nowarn -encoding UTF-8 -cp <jar>` and NO `--release`, no `-source`, no `-target`.**
   `--release` arrived in JDK 9 and dies with "invalid flag" on a JDK-8 `javac` in seconds (the bc21 lesson); the
   compiler **is** 8, so the target is 8. The job's first step additionally asserts `java -version` contains `1.8.`
   **and** that `javac --release 8 -version` **fails**, so the trap is asserted rather than trusted.
6. **The driver must fail loudly when nothing happens, and it must call `System.exit()`.**
   `tools/oracle/bc17/Bc17Trace.java` **exits 3** if no robot ever took an action and no bullet was ever spawned;
   `ci.yml` additionally asserts per pair that the game reached at least round **2 900** (or ended earlier with a `W`
   line), that at least **8** robots were alive at once on the non-idle tiers, and that at least one `A` line carries
   a non-`NOTHING` action. The sandboxed player threads are **non-daemon**, so a driver that returns without
   `System.exit()` hangs forever; every `java` invocation is wrapped in `timeout 900`.
7. **The driver uses the engine exactly as published (beyond step 3).** `package battlecode.world;`, so it needs
   reflection only for `ObjectInfo`'s private `gameRobotsByID`/`gameTreesByID`/`gameBulletsByID`/
   `dynamicBodyExecOrder` and `GameWorld`'s `currentBroadcasters` (the only way to print in trove order, in exec order
   and to checksum the broadcaster array). It builds a real `GameInfo` + `GameMaker(gameInfo, null)`, calls
   `makeGameHeader()`, registers a `PlayerControlProvider` for **Team.A** and **Team.B** (**and nothing for
   Team.NEUTRAL, because 2017 has no neutral ROBOTS — only neutral trees — so unlike 2016 no `NullControlProvider`
   registration is needed**; the driver asserts none is ever spawned), constructs the `GameWorld` with a zero
   `oldTeamMemory`, and loops `runRound()` with the players' `System.out` discarded. **No flatbuffer file is written
   and no `.bc17` bytes are produced on either side.**

**The trace, and its one important departure from every sibling year: every float is printed as its RAW IEEE-754
BITS in hex, never as a decimal.** A `float32` needs nine significant decimal digits to round-trip, and a formatter
mismatch between a Java `%.9g` and a Nim `formatFloat` would masquerade as a divergence for a week — bc16 solved that
with a `%.6f` convention plus a per-field float allowlist in the comparator, and bc17 removes the problem instead of
managing it. **The consequence is that `parity_tiers_bc17.py` needs NO float allowlist at all**, which is one fewer
place for a comparator bug to hide.

```
R <round> T <A|B> bul=<hex8> vp=<n> ar=<n> ga=<n> lj=<n> so=<n> ta=<n> sc=<n> tr=<n> trm=<n>
R <round> U <id> team=<A|B> ty=<ARCHON|GARDENER|LUMBERJACK|SOLDIER|TANK|SCOUT> x=<hex8> y=<hex8> hp=<hex8> ra=<n> ac=<n> mc=<n> wc=<n> shc=<n> cd=<n> bc=<n>
R <round> E <id> team=<A|B|N> x=<hex8> y=<hex8> r=<hex8> hp=<hex8> mhp=<hex8> cb=<n> crob=<TYPE|-> ra=<n>
R <round> B <id> team=<A|B> x=<hex8> y=<hex8> dir=<hex8> sp=<hex8> dmg=<hex8> ra=<n>
R <round> A <id> act=<NOTHING|MOVE|FIRE_SINGLE|FIRE_TRIAD|FIRE_PENTAD|STRIKE|CHOP|SHAKE|WATER|PLANT|HIRE|BUILD|BROADCAST|DONATE|BODY_ATTACK> tgt=<n> x=<hex8> y=<hex8> arg=<hex8>
R <round> G exec=<fnv1a64> execlen=<n> ubod=<fnv1a64> tbod=<fnv1a64> bbod=<fnv1a64> nb=<n> rid=<n> bid=<n> broad=<fnv1a64>
R <round> W winner=<A|B|-> dom=<PHILANTROPIED|DESTROYED|PWNED|OWNED|BARELY_BEAT|WON_BY_DUBIOUS_REASONS|->
```

**Robots and bullets are printed in EXEC ORDER and trees in TROVE ORDER**, which is what makes an ordering bug visible
on the round it happens; the **`G` line is bc17's own addition and it is the most valuable line in the trace** — it
carries the exec-order fold, the three body folds, the two id counters and **the broadcaster array's fold**, so a
trove bug (D1) or an id-stream bug (D3) surfaces immediately instead of as a mystery 400 rounds later.
`tools/parity_trace_bc17.nim` prints the same lines from the Nim port.
`tools/ci/parity_tiers_bc17.py`'s `normalize()` **is applied to BOTH sides by the same code path** and does exactly
two things: it re-parses every named hex field as an unsigned integer and re-emits it canonically, and it strips the
`bc=` (bytecode) column from **both** traces, using it only for the Tier-B′ headroom assertion (LEARNINGS 2026-09-08:
bc23's comparator stripped a field from the Java side only and every pair "diverged" at round 1). **Nothing is
normalised on one side only.** The comparator uses **`itertools.zip_longest`, never `zip`** (a one-line-longer Java
trace must not read bit-exact) and carries a self-test that constructs exactly that pair and asserts a divergence is
reported. Traces go to `$RUNNER_TEMP`, are compared **streaming** (never loaded whole), and only the first 200
divergent lines plus a gzipped digest are uploaded.

**The tiers — pinned to what this harness can actually deliver, and honest about which one carries the weight.**

- **Tier A (BLOCKING) — rounds 1…2 999 bit-exact, whole games, on the nine pairs**, with `bc17idle` against itself (a
  bot whose body is `while (true) Clock.yield();`). **This tier is deliberately small, and that is worth saying:** in
  2017 nothing happens without a player action — no NPCs, no passive spawning, no terrain change — so Tier A proves
  exactly the round counter, the initial exec order off the map file, the neutral-tree pass (up to **1 228** trees a
  round on `LineOfFire`, all returning zero income but all taking `processBeginningOfRound` and `roundsAlive++`), the
  trove machinery idle, the **income cliff**, and the ladder falling through to rung 4. The job asserts off the
  **Java** trace that it really did those things: `bul` is the bits of `300.0f` on **every** round of **every** pair
  (the measured fact turned into a gate); `rid` and `bid` never grow; `execlen` equals the initial body count; and the
  final `W` line carries `WON_BY_DUBIOUS_REASONS`. Cheap and worth having, but **the load-bearing tiers are A′ and
  A″.**
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact, on the nine pairs.** Four scenario bots of our
  own, each deterministic with **no RNG at all**, each cheap enough that Tier B′'s headroom assertion holds, and each
  **scripted by round number to force every rare path early**. **`bc17scenario`**: hire a GARDENER and prove the
  10-turn cooldown; plant the first slot of each of the three layouts and prove the **shared** cooldown between
  planting and building; water a tree at 45 HP and at 48 HP (the wasted 3); build one of each of LUMBERJACK, SOLDIER,
  TANK and SCOUT and prove the **20-turn dormancy** and the 4 %-a-turn heal; move at exactly `strideRadius`, at half
  of it and at **twice** it (the atan2 re-projection); move a SCOUT **onto** a neutral tree and a SOLDIER into one
  (refused); fire a **single**, a **triad** and a **pentad** at a known angle and prove the **centre-left-right**
  spawn order, the ±20°/±15° offsets and the bullet id sequence; fire into a body adjacent to the muzzle (the spawn
  collision); fire at a tree; let a bullet leave through the east edge; fire so a bullet hits **its own** side;
  `strike()` with an own gardener, an own bullet tree, an enemy soldier and a neutral tree all inside distance 2
  (**no team check** on either list); `chop` a neutral tree to 0 and prove the contained robot **is** released and
  joins the chopper, then kill an identical tree with a **bullet** and prove **nothing** is released; `shake` a tree
  with bullets and one without; `broadcast` on channels 0 and 9 999, read them back, and prove the position is
  exposed to **both** teams next round; and `donate` a **non-multiple** of the price, proving the remainder is
  destroyed. **`bc17scenariotree`**: the tree life cycle in isolation — the 81-round growth with its exact health
  sequence and zero income, the first income round, decay to death, and a tree killed by a **TANK body attack**
  (4 damage, the move spent, the tank refusing to move while still blocked). **`bc17scenariokill`**: soldiers walked
  onto the enemy's single archon on `HouseDivided` until `DESTROYED` fires, proving the winner is set **mid-round**,
  **the round still finishes**, and the next `runRound` returns `DONE`. **`bc17scenariotie`**: mirrored sides scripted
  so the ladder walks rung 1 (a 1-VP difference), rung 2 (a 1-tree difference), rung 3 (a 1-bullet difference
  **including the archon's −1**) and rung 4, one rung per seed. `scenario17.nim` is their Nim twin, written line for
  line, behind `-d:bc17Scenario` (+`Tree`/`Kill`/`Tie`). Both sides run all four on the nine pairs and must agree
  **bit for bit for the whole game**. The job then asserts, **off the JAVA trace**, that the paths really fired: a
  `U` line for each of the six types; an `hp=` rising by exactly the bits of `0.04 × maxHealth` on twenty consecutive
  rounds for a new fighter with **no `A` line** during them; `B` lines appearing three and five at a time with the
  right `dir=` spacing; an `E` line's `hp=` falling by the bits of `4.0f` on a `BODY_ATTACK` round; an `E` line
  disappearing on a `CHOP` round **followed by a new `U` line of the contained type**, and an `E` line disappearing on
  a bullet hit **with no new `U` line**; a `bul=` jump matching a `SHAKE`; a `vp=` jump matching a `DONATE` with the
  floor arithmetic; and `W` lines carrying `PHILANTROPIED`, `DESTROYED`, `PWNED`, `OWNED`, `BARELY_BEAT` and
  `WON_BY_DUBIOUS_REASONS` across the set. *(If any scripted path turns out impossible to force deterministically, the
  failing item is dropped from the bot and **added to `docs/PARITY.md` §What is NOT compared with the reason** — never
  silently left in a bot that does not reach it.)*
- **Tier A″ (BLOCKING) — `examplefuncsplayer17` against itself, whole games, bit-exact, on the nine pairs.** It is
  the one bot with a live per-robot `java.util.Random(id)` (the determinism patch), so this tier proves the port's
  `src/battlecode/rng.nim` reproduces that stream call-for-call **including the `&&` short-circuit that decides
  whether a draw happens at all** — and it is the tier that runs the real filler, so a filler that stops being
  reproducible fails a blocking gate rather than a league round.
- **Tier B (BLOCKING) — the constants, the arithmetic and the map data.** `tools/JavaBc17Tables.java`, under the
  pinned JDK 8, prints (i) **every `GameConstants` field** by reflection (2017's `GameConstants` is an **interface**,
  so its fields are implicitly `public static final` and reflection sees all of them) and the whole six-row
  `RobotType` table with its eleven columns, byte-diffed against the generated
  `src/battlecode/years/bc17/constants.nim`; (ii) **the fdlibm vectors** — the ≈ 400 boundary rows and the eleven
  expression-shape digests over the 2 000 000-point sample of F4 — byte-diffed against
  `data/bc17/fdlibm_vectors.json`; and (iii) **all 22 converted maps' `LiveMap` fields** (width, height, origin,
  seed, `rounds`, and every initial body's id, team, type, float coordinates, radius, health, contained bullets and
  contained robot **in `getInitialBodies()` order**) byte-diffed against `data/maps/bc17/*.json`, which is what
  proves the Python flatbuffer walk rather than trusting it.
- **Tier B′ (BLOCKING) — the metering divergence, proved where it is observable.** Two steps: (a) **every bot in
  this job asserts `Clock.getBytecodesLeft() > 5000` at the end of every turn and `System.exit(4)` otherwise**, so
  the engine's own pause-and-resume provably never fired in any game this job compares and V1's divergence is
  provably not exercised; and (b) a **separate, non-compared** run on one seed with **`bc17slowbot`**, whose `turn()`
  burns a calibrated ~20 000 bytecodes, asserts that the engine **does** pause it — its `A` line becomes `NOTHING`
  and its `bc=` column pegs at the limit — at the turn the limit predicts. Step (b) compares nothing against the Nim
  side (the port has no bytecode counter) and exists so the port's *reading* of the rule is proved rather than
  asserted. `docs/PARITY.md` §bc17 states in as many words that **the only behaviour this oracle cannot compare is
  how much thinking each side got, and that no 2017 rule reads it.**
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 2 999-round game, on all six
  comparing bots and all nine maps, and NOT gated on a subset of maps.** The job computes it per pair and compares it
  against `tools/ci/parity_ledger_bc17.json`, whose entries are `{"bot": …, "map": …, "first_divergent_round": N,
  "cause": "<one sentence>", "docs": "PARITY.md#<anchor>"}`. It **fails** if (a) a pair diverges with no ledger entry,
  (b) a pair diverges **earlier** than its entry, (c) a ledger entry no longer reproduces (a stale excuse is as bad
  as a missing one), or (d) any divergence occurs while Tier B′'s headroom assertion still holds — which, on every
  bot in this job, means **always**, and therefore means a real rules bug rather than a metering artefact. **The
  idea's expectation that Tier C would have to be "gated on the maps where float parity holds" is refuted by F1–F5
  and by the three normalisation patches: there is no map on which parity is expected to fail, and if one appears it
  is a bug and not a map.**

**Root-cause-or-fail is the standing rule, and it is the operator's ruling on the bc26 run (Fleet card
1218171523823317), not this note's preference.** An unexplained Tier C divergence is a **FAIL**, not a ledger line; a
cause of "unknown" is not a cause and the ledger schema rejects it. **The phase-30 exit condition is that Tiers A, A′,
A″, B and B′ pass with an EMPTY ledger**, and that is achievable because every one of the four things that
historically forced divergences is absent or normalised: **the RNG surface is two generators drawn only at block
boundaries** (D3), **the exec order is an array** (D4), **the one order-dependent float sum is reproduced exactly**
(D1), and **the one irreproducible ordering and the one 1-ulp transcendental gap are both normalised on the ENGINE
side by committed one-hunk patches** (D2, F2). **The place a divergence is genuinely plausible is a width** —
`hitDist` and `perpDist` are seven lines apart in the same Java method with opposite shapes (F3) — which is why
`tests/test_bc17_widths.nim` exists and why every float in the trace is printed as raw bits.

If phase 30 finds a divergence anyway, the **root-cause checklist**, each item with its own unit test above, so a
Tier C failure bisects in minutes rather than becoming a card: the eleven width shapes (3); the fdlibm vectors (4);
`calcHitDist`'s branches and the strict-minimum tie rules (5); the tree life cycle and the `fromChop` gate (6); the
action guards and the `incrementMoveCount` placement (7); the income cliff and the trove-ordered tree sum (8, 11); the
exec order and the bullet-before-parent insert (9); the two id streams and the bullet generator's head start (10); the
candidate order and the sight radii (12); the dormancy gate (13); and the four rungs with the archon's −1 (14).

Tiers A, A′, A″, B, B′ and C are the **phase-30 gate**. Every accepted divergence is listed in `docs/RULES-BC17.md`
§Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md` gains a `bc17` section in the same shape
as the `bc16` one — including, honestly: the measured jar facts and the empty `.pom`, the `SPEC_VERSION` pin, the
JDK-8 requirement and the trap it avoids, **the three engine patches with their reasons and the 20 000 000-sample
measurement that justifies the `StrictMath` one**, the fact that no `NullControlProvider` registration is needed in
2017, the trace line counts and JVM seconds phase 20 measures, the peak robot and bullet counts, **that Tier A is
small in this year because nothing happens without a player**, and **that the metering divergence is the one behaviour
this oracle cannot compare, and that no rule reads it**.

### `docker-smoke` job — now **ten** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely from
`certification.game_config.num_agents` and hard-fails with `SEAT-COUNT FAIL:` if the workflow's **`<SEATS>` = 2**
disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes — bad-token refusal, `/global` first
frame on connect, `Ping → Pong` **payload echo** — against the real image on the first episode):

1–9. **The bc26 certification-fixture episode and the bc20, bc21, bc24, bc25, bc23, bc22, bc16 and bc19 episodes,
   all unchanged** → `dist/smoke/replay.json`, `replay-bc20.json`, `replay-bc21.json`, `replay-bc24.json`,
   `replay-bc25.json`, `replay-bc23.json`, `replay-bc22.json`, `replay-bc16.json`, `replay-bc19.json`.
10. **A bc17 episode**, new: `SMOKE_EXPECT_YEAR=bc17`, `SMOKE_PLAYER_IDS=awu,scaffold`, `SMOKE_CONTRACT_PROBE=0`,
    `SMOKE_REPLAY_OUT=dist/smoke/replay-bc17.json`, and
    `SMOKE_CONFIG_OVERRIDE={"year":"bc17","pool":"small","seed":<the seed test 16 pins>,
    "gamesPerMatch":1,"maxRounds":900,"perGameBudgetSeconds":120,"matchBudgetSeconds":130,
    "connectTimeoutMs":15000}`.
    **900 rounds and not 400**, for reasons that are this year's: on the pinned map (`HouseDivided`, 30×30, one archon
    a side, **archon separation 6.5**, 41 neutral trees all holding bullets and 6 holding a robot) a 400-round window
    shows the opening but **not a mature tree** — a bullet tree needs **81 growth rounds after planting**, and a
    gardener must first be hired (10-turn cooldown) and walk to a slot. 900 rounds guarantees **a hired gardener, a
    planted tree, a MATURE tree paying income, a fighter built and dormancy-expired on both sides, and first contact**
    (6.5 units is ~9 rounds for a soldier), and records ~36 s of playback at 25 fps, comfortably outlasting the viewer
    smoke's **15 s** soak (the ecos 2026-08-23 scar). The seed is pinned to draw `HouseDivided` and
    `tests/test_bc17_maps.nim` asserts that draw.

All ten run one game container + two player containers on a shared network with `file://` artifact URIs and **no
`ANTHROPIC_API_KEY`**, so both seats take the scripted path and must still complete. All ten assert: the game exits
0, **every player container exits 0**, `results.json` carries exactly the expected key set, `reason == "complete"`,
`scores` has 2 entries, `fallbacks == [0, 0]`, and the replay parses as **strict UTF-8 JSON** with
`format == "cogame-battlecode-replay"`, the right `year`, and a non-empty `events` array. A step asserts all ten
replays exist and report **ten different `year` values**.

**The episode substance assertion (the LEARNINGS 2026-09-03 pin), in two parts.** The bc17 episode passes
`SMOKE_REQUIRE_STATS` — the **per-seat** floor the script already enforces for both seats — with
`{"units_built":2,"moves":200,"broadcasts":1,"damage_dealt_tenths":0}`. Those are things *both* chassis do, including
the weak floor: `examplefuncsplayer17`'s archon hires on a 1-in-100 draw whenever it can afford it and broadcasts its
position **every turn**, and every one of its robots moves every turn. (`damage_dealt_tenths` is floored at **0** per
seat deliberately — the weak floor fires only when an enemy is inside sensor range, so it may legitimately deal
nothing on a 900-round window.) **The signatures of the year are things only a seat playing well does** — planting,
watering, letting a tree mature, shaking, donating — and `examplefuncsplayer17` does **none** of them, so asserting
them per-seat would be asserting that the weak floor is not weak. They are asserted **across the pair** by one `jq`
step in `ci.yml`, reading the **replay's** `result` block (not `dist/smoke/results.json`, which every episode
overwrites in turn — the bc24 fix): `([.result.games[0].trees_planted[]] | add) >= 1`,
`([.result.games[0].trees_mature_end[]] | add) >= 1`, `([.result.games[0].water_actions[]] | add) >= 5`,
`([.result.games[0].bullets_earned_from_trees_tenths[]] | add) >= 10`,
`([.result.games[0].shake_actions[]] | add) >= 1`, `([.result.games[0].victory_points[]] | add) >= 1`,
`([.result.games[0].units_built[]] | add) >= 5`, `([.result.games[0].bullets_fired[]] | add) >= 10`,
`([.result.games[0].damage_dealt_tenths[]] | add) >= 10`, `(.result.games[0].robot_ids_issued) >= 6` and
`(.result.games[0].peak_bullets_in_flight) >= 2`. Together they make an idle win machine-visible, which is exactly
what the 2026-09-03 round-1 degenerate match lacked. **And the floors are measured, not guessed**: phase 20 runs the
real bc17 smoke once, reads the actual per-seat statistics out of `dist/smoke/replay-bc17.json`, and sets the
committed floors at roughly **half the weak seat's measured value** — never above what a correct episode produces —
and where that conflicts with "never below this note's numbers", **the second constraint wins and the measurement
goes inline in `ci.yml`** (the bc23 r1-F22 ruling: a floor derived from whole 2 999-round games is wrong for a
900-round smoke). **If the across-the-pair `victory_points >= 1` or `trees_mature_end >= 1` assertion does not hold
on the measured episode, the fix is to raise the smoke's `maxRounds` until it does — never to drop the assertion**:
an episode of this year in which nobody ever grew a tree or bought a point is not this game being played.

### `wasm-viewer` job — the bundle is **executed**, against **all ten** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete (`index.html`, a
non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`, `static_replay.js`,
`static_replay_worker.js`, `wire_constants.js`), then run `node tools/ci/viewer_smoke.mjs --bundle
dist/static-replay-viewer --replay <replay> --killfeed-overlap` in headless chromium (Playwright pinned **1.55.0** in
both places — the npm module and the browser download) **once per replay**: `replay.json`, `replay-bc19.json`,
`replay-bc20.json` and `replay-bc21.json` at `--timeout 90 --soak 10`, and `replay-bc24.json`, `replay-bc25.json`,
`replay-bc23.json`, `replay-bc22.json`, `replay-bc16.json` **and `replay-bc17.json`** at
`--timeout 120 --soak 15`. **This is the viewer smoke the checklist asks for: `tools/ci/viewer_smoke.mjs`, run by
`ci.yml`'s `wasm-viewer` job, against the replay `docker-smoke` actually produced — the bundle is EXECUTED in a real
browser, not merely built.**

Each run requires: **`data-replay-loaded="true"`** (or the bridge `ready` posted after it — and **`data-replay-error`
must be absent**); three **differing** clock/scorebug readouts at 0 % / 50 % / 100 %; continued advancement across the
soak; **`scrub_selector == "#scrub"`** (so a seek was really exercised and the `#viewpanel` zoom slider was not
clicked instead); `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line; the **no-overflow
assertion at 1280×800**; no overlay covering more than 50 % of the board after the soak; and the `#killfeed`/stat-box
overlap check at **360 px, 720 px and 1280 px at both FIT and 2× zoom**.

`--strict-text-bounds` stays deliberately dropped on the replay runs because the board is pannable and zoomable
(`#viewpanel` is kept), which is the exact case the flag's own documentation excludes — and because
**`canvas_text.total: 0` on this renderer covers nothing and must not be read as a pass** (LEARNINGS 2026-09-08). The
counts are still recorded in `viewer-smoke.json`, and the separate `tools/ci/renderer_fixture.html` step — full-cap
`notes` and `motto` on both seats at three widths **including 360 px**, in the page's own CSS extracted from
`client/replay_broadcast.html` at run time — runs through the same harness **with** `--strict-text-bounds`, because
every CI replay is scripted and carries no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a **bc17
row**. `node tools/wasm_replay_smoke.cjs` is also run against the bc17 smoke replay **and** the committed
`tests/fixtures/replay-bc17.json`, so wasm32-only failures are caught — including the bc17-specific one, **a float32
narrowing difference between the native and the wasm backend**: this is the first year whose sim depends on
`float64 → float32` narrowing every round, so `tests/test_bc17_replay.nim`'s hash-chain re-derivation is run **under
wasm** by that script and not only natively.

---

## Out of scope (v1)

- **Any Java, JDK, JRE, JVM, Node or npm at runtime.** No engine, no instrumenter, no sandbox, no in-container
  compilation of anything a cog sends. The 2017 engine exists only in the `parity-oracle-bc17` CI job;
  `tools/convert_maps_bc17.py` is **pure Python** and reads the map flatbuffers out of the jar **without a JVM**, at
  build time. The only other Node in this repository is the CI-only Playwright harness.
- **The flatbuffer layer and the official client** (V2): `battlecode/schema/*`, `server/GameMaker`'s `.bc17` writer,
  `server/{NetServer,Server,Config}`, `world/GameMapIO`'s writer and the whole `instrumenter/` tree have no port. The
  client's **sprites** are reused (credited, AGPL-3.0); its **code** is not shipped, embedded or built. There are no
  `.bc17` bytes anywhere and no byte-format writer on either side.
- **Bytecode metering with mid-computation resume** (V1). The `DecisionOps` budget replaces it and the cap is
  provably non-binding for both shipped chassis; the engine's own pause is proved never to have fired in any compared
  game by Tier B′. Metering Nim to Java bytecode granularity would need either a Nim-level instrumenter (a compiler
  project) or a hand-annotation of every statement against the jar's `MethodCosts.txt`, and neither buys anything
  here, because **no 2017 rule reads the bytecode count at all**.
- **Porting `net.sf.jsi`'s R-tree** (D2). Its ascending-distance ordering is reproduced exactly by a uniform grid and
  an explicit comparator; its **exact-tie** ordering is an artefact of node splitting and priority-queue heapify that
  is not stable even against itself in the same process (measured), so there is nothing faithful to reproduce.
  The oracle is patched to the same comparator on the engine side, so the normalisation is symmetric.
- **The fdlibm Payne–Hanek argument-reduction branch** (V6, F4). `Direction.radians` is always in (−π, π] by
  construction, so `remPio2Medium` is the only branch the engine can reach; the port **raises** outside `[−4, 4]`
  rather than guessing, and the unimplemented branch is named in `docs/RULES-BC17.md`.
- **`GameWorld.rand`** (D3, a third `Random(mapSeed)` the engine constructs and **never reads** — porting it would be
  inventing a stream), **team memory** (V4, meaningless where every game is independent; a zero-filled array is kept
  so the API exists and `orchard` never touches it), **`resign()`** (V6, unreachable and, in the engine, an iteration
  over a mutating trove map) and the debug indicator APIs (`setIndicatorDot`/`setIndicatorLine`, which draw only in
  the official client). All four recorded rather than silently dropped.
- **The other 48 official maps.** 22 boards are committed and their geometry is pinned in §Sim module from a
  measurement of **all 70**. `tools/convert_maps_bc17.py` handles any of them and CI regenerates all 22; widening the
  pool is one JSON edit plus one CI run, and it is not v1's job. The maps deliberately left out include the
  1 916-tree `ModernArt` and the 1 359-tree `GreatDekuTree` (whose candidate loads would double the perf gate for no
  new rule coverage) and the 0-archon-symmetry outliers.
- **A bc17 certification fixture, and any new `player[]` entry.** Certification stays on **bc26** and `player[]`
  stays at `awu` + `scaffold` — the cert fixture seats exactly `num_agents = 2` players, so a third `player[]` id
  fails the release with `players_missing` (LEARNINGS 2026-09-04) — and bc17's own timing would not fit
  `coworld certify`'s 60 s default. bc17 is proven by its own `docker-smoke` episode and the viewer smoke run against
  that episode's replay.
- **A cog-authored bot in any language.** Doctrines are **JSON-sheet only**: no compiler, no sandbox, no
  compile-error round trip, no multi-attempt loop. Nothing in the schema is closed against a future sandboxed hook.
- **Worker-side keyframe checkpoints in the viewer.** bc17 seeks re-simulate from the start of the game like every
  other year, and bc17 is the year that needs them **most** (2 999 rounds at 3–12 ms/round, which is why it takes the
  heavy `settle=20000 soak=15` probe). Deliberately not in v1, and named here so the next run has the argument made.
- **A cog-authored comms protocol.** The 10 000-channel layout in `comms.nim` is the chassis's; a doctrine cannot
  redefine a channel, cannot set a broadcast cadence and cannot add a message kind. In this year **broadcasting
  reveals the broadcaster's position to both teams** (rule 2.2), so exposing the layout would be exposing a channel a
  doctrine could use to leak what it should not.
- **A per-tree or per-target knob, and a `friendly_fire` knob.** `chop_policy` decides *what kind* of tree a
  lumberjack goes for and `defend_radius` decides *how far* the army answers; *which* tree, *which* archon a wave
  walks at and *which* farm slot a gardener claims are the chassis's call (the nearest by the grid, the mirror of the
  nearest own archon, and the first free slot of the layout), and exposing them would let a doctrine name a target
  that does not exist on the map in front of it, which the anti-inert rule forbids. Friendly fire is *legal* in 2017 —
  a bullet has no team check and `strike()` hits its own farm — and the chassis takes it only where the engine forces
  it, never as a choice; `tests/test_bc17_baselines.nim` asserts no strike whose own-HP cost exceeds the enemy's is
  ever emitted.
- **Per-robot fog in the viewer** (the spectator sees the true board; the fog is the robots', and both factions'
  initial archon positions are public to the *players* from round 1 anyway), **live spectating of an in-progress
  match** (`/global` carries the phase and the result; the watchable artefact is the recorded replay), and **per-round
  cog interaction of any kind** — no mid-match observations, no doctrine amendments, no messages between cogs. One
  sealed doctrine, then the war. (2017 has **no** inter-team channel at all: the broadcast array is per-team, and the
  only thing one side learns from the other is where its broadcasters were standing.)
- **Battlecode years other than the ten registered** (2016, 2017, 2019–2026). The registry, `game_config.year`, the
  variant naming and `years/dispatch.nim` all support more; only these ten are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. Both of the idea's feasibility flags resolve —
§Feasibility verdict gives the file-by-file reason for each — and the first one resolves better than the idea
expected: the continuous-space float question has a determinate answer, measured over 20 000 000 samples, and **Tier
C does not have to be gated on a subset of maps**. The whole `Math.` inventory of the gameplay tree is classified per
call site in §Sim module F1 and **every one of the 29 references is (a) exactly specified or (b) fdlibm-ported and
pinned; none is (c) irreproducible**. The six places this port deliberately differs from the engine are enumerated as
**decided divergences V1–V6** with a reason each, the five determinism decisions as **D1–D5**, the six places where
the 1.6.2 spec contradicts the engine are tabled with the engine winning every one, and the three CI-only engine
patches are each named with the measurement that justifies it. The idea's eight candidate knobs all survive with exact
types, ranges and defaults — `scout_harass` finalised as an integer share of the military budget, `soldier_tank_ratio`
finalised as the tank share of it — and **three** are added from the engine's own arithmetic: `lumberjack_share`,
because a lumberjack is the only unit that can open a 924-tree map and the only one that can delete a farm;
`chop_policy`, because a chop is the only action that releases a robot from a neutral tree and one played map has 406
of them; and a fourth value on `vp_donate_policy` (`endgame_dump`), because rung 3 of the engine's own ladder is
bullets-plus-robot-cost and banking is therefore a real strategy rather than a trap. The one question the idea does not
raise and this note had to settle — whether to reproduce the jsi R-tree's exact-tie order, port it, or normalise it —
is settled in §Sim module D2 **by normalising it to `(squared distance, id)` on BOTH sides with a one-hunk engine
patch**, on the measured ground that the engine's own order is not stable against itself and so there is nothing
faithful to reproduce.)*

