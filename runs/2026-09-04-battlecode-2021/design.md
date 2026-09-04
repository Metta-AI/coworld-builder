# cogame-battlecode — the `bc21` year module: Battlecode 2021 "Campaign" (design note, 2026-09-04)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a
branch/PR of the shipped repo that adds the year module `bc21` beside the shipped `bc26` and
`bc20`, adds the manifest variant `bc21`, keeps certification on `bc26`, and bumps the version of
the *same* coworld. **There is no `cogame-battlecode-campaign` repo and none is created.** The
starter is chosen by game shape and it is the only defensible one: bc21 is the same shape as bc26
and bc20 — a deterministic Nim grid sim compiled twice (native for the server, wasm for the
viewer), one sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm replay
viewer that re-derives every frame — and the year-module boundary
(`src/battlecode/years/<year>/`, `years/registry.nim`, `years/dispatch.nim`, `game_config.year`)
already exists and was proved by bc20. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode`
→ this. **Every convention in `Metta-AI/cogame-battlecode` holds here unless this note says
otherwise**: the Nim sim/server/player layout, `nimby.lock`, the bitworld runtime contract, the
`GameVersion` discipline, `tools/build_replay_viewer.sh`, the `replay-viewer/` bundle, the
`client/` chrome, the one-parallel-batch doctrine layer (`llm.nim` / `decide.nim` / `sheet.nim` /
`baselines.nim`), the closed results document, and "degrade, never hang".

This note lands in the repo as `docs/plans/2026-09-04-battlecode-2021-design.md` on the branch
`bc21-year-module`. The copy of record for the run is
`runs/2026-09-04-battlecode-2021/design.md`.

**Everything below about the 2021 rules was verified by reading `github.com/battlecode/battlecode21`
at commit `ed39c1a49574db57e5463d720736220506280294`** (`master`, last pushed 2022-01-11;
`gradle.properties` `release_version=2021.3.0.5`, which is the final patched season release) —
`specs/specs.md.html`, `engine/src/main/battlecode/common/GameConstants.java`,
`common/RobotType.java`, `common/Team.java`, `world/GameWorld.java`, `world/InternalRobot.java`,
`world/RobotControllerImpl.java`, `world/ObjectInfo.java`, `world/TeamInfo.java`,
`world/DominationFactor.java`, `world/IDGenerator.java`, `world/LiveMap.java`,
`world/GameMapIO.java`, `schema/battlecode.fbs`, and
`example-bots/src/main/examplefuncsplayer/RobotPlayer.java` — and by **parsing all 76 `.map21`
flatbuffers** in `engine/src/main/battlecode/world/resources/` for their real sizes, seeds,
passability arrays, Enlightenment-Center placements and influences, and symmetry. The oracle
recipe in §Tests was **executed in the sandbox**, not guessed: the 2021 engine really does compile
and run headless from a bare `javac`. Base-repo facts are from a fresh clone of
`Metta-AI/cogame-battlecode` at **`e17947d`** ("manifest: declare only the two players the cert
fixture seats"), whose shipped coworld version is **0.2.0**
(`release-result.json`, run 33850681870, `canonical: true`, `cow_id
cow_d9fc2f21-c095-4131-bd86-d35848e046f8`). Every `file:line` and constant below is to those two
trees.

### Source idea (verbatim)

```
# Idea 1218173707173046 — 29 Battlecode 2021 Campaign (mod of cogame-battlecode) — year variant bc21 + its own league

The other Tier-1 metagame in daveey's ranking (best-battlecodes.md): a season that turned over muck-spam -> slanderer-turtle (babyducks) -> buff-mucks and muck-flanks -> exponential-economy upsets, with a record number of 3-2 series and wololo's pure muckraker rush surviving all the way to finals as a genuinely different archetype. Enlightenment Centers bid INFLUENCE to win neutral centers, and spend it to build POLITICIANS (walking bombs that empower allies or convert enemies), MUCKRAKERS (cheap, expose slanderers and see far) and SLANDERERS (passive income that decays into politicians); win by eliminating every enemy center or by votes when the game ends. Symmetric 32-64 grids, up to 3000 rounds (patched mid-season). A doctrine game about when to turtle and print money, when to spam muckrakers, and when the exponential kicks in.

Seats: 2 (one cog per side). num_agents = 2 in the bc21 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc21 (v1 candidates; the builder finalises them from the chassis it ports): opening {muck_spam | slanderer_turtle | balanced}, slanderer_ratio, muck_ratio, politician_size_curve, bid_policy {never | fixed | proportional | escalate_when_ahead}, expansion {neutral_centers_first | defend_home}, flank_policy, empower_threshold, convert_over_kill, eco_exponential_round.
Rules, engine, oracle: Spec: specs/specs.md.html in https://github.com/battlecode/battlecode21 (not hosted elsewhere). Engine: same repo, Java 8 + Gradle 6.0.1, engine/COPYING = AGPL-3.0 (no root licence). Oracle: build the engine from source in CI (JDK 8); the released jar lives only on GitHub Packages maven.pkg.github.com/battlecode/battlecode21 (needs a read:packages token; releases.battlecode.org 403s for this year) — same situation the bc20 run solved, reuse its recipe.
Chassis and baselines (behaviour sources): iliao2345/Battlecode2021 (wololo, 7th-8th, AGPL-3.0 — the distinct muck-spam lineage), BSreenivas0713/Battlecode2021 (3 Musketeers, 9th, AGPL-3.0), StoneT2000/Battlecode2021 (California Roll, 9th, AGPL-3.0; postmortem https://stonet2000.github.io/battlecode/2021/). babyducks (winner) is not on GitHub; IvanGeffner/battlecode2021 (Malott Fat Cats) has no licence — reference only.
Ranking: Tier 1 (mixed: endogenous discovery + one major mid-season nerf).
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc21` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc21` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc21`, league_name `Battlecode 2021 — Campaign`, default_variant_id `bc21`, short_name `bc21` (softmax.com/battlecode/bc21), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin from the idea's HOW paragraph is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; no new repo; one variant per year; one league per year; certification stays bc26; version bump of the same coworld | this paragraph, §Packaging |
| NO Java/JDK/Node in the runtime image; full behaviour port of the 2021 rule set to a deterministic Nim sim (native + wasm); `java.util.Random` reproduced | §Sim module |
| Nim chassis ported from the **behaviour** of the three AGPL-3.0 bot repos; never vendor unlicensed code | §Decisions ("the two chassis"), §Packaging ("Licensing") |
| The year's doctrine sheet knobs | §Decisions ("the bc21 doctrine sheet") |
| Fixed per-robot decision budget instead of bytecode metering (documented divergence) | §Sim module ("the chassis, and the bytecode divergence"), §Packaging (`docs/RULES-BC21.md` §Divergences) |
| The year's maps converted at build time | §Sim module ("Maps") |
| Official 2021 client sprite set for art, credited | §Viewer ("Art"), §Packaging ("Licensing") |
| Java engine ONLY as a CI parity oracle; Tier A/B/C on seeds; **every divergence root-caused or in `docs/PARITY.md` with round+map+cause** | §Tests (`parity-oracle-bc21`), including the **parity ledger** that makes an un-root-caused Tier C divergence a red build |
| Manifest variant `bc21` (`num_agents` 2) added; certification stays bc26 | §Packaging |
| Phase-50 league `bc21` with its own champions, fillers and credit pool; never touch bc26/bc20 | §Packaging ("The phase-50 plan") |
| Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side) | §The game, §Viewer |

### Interface facts this note is written against (read from `e17947d`, not assumed)

- **D1 — the chassis is not an LLM-selectable knob.** `chassis` is gone from the doctrine sheet;
  a submitted `chassis` is recorded in `sheet_unknown_fields` and ignored
  (`src/battlecode/sim_types.nim:37`). **The bc21 sheet has no `chassis` key** and
  `tests/test_bc21_sheet.nim` asserts the D1 behaviour.
- **D2 — the scripted baseline plays, and CI gates on substance.** bc21's strong baseline
  (`california-roll`) is a real bot, and the gate is survival + positive play counters, not a win
  (§Tests items 11 and 12).
- **D3 — the doctrine overlay must be dismissible.** `#bc21-doctrines` ships with a close control,
  an `Escape` binding, a re-open chip and self-dismissal on the first advance; it never sits in the
  transport band (§Viewer).
- **The manifest declares exactly the two players the certification fixture seats.** `player[]` is
  `awu` and `scaffold` and **nothing else** (`coworld_manifest_template.json`, commit `e17947d`);
  `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`. The bc20 run lost a
  release dispatch by adding year-specific `player[]` entries that occupied no cert slot. **This
  run adds no `player[]` entry.**
- **`GameVersion` is `GV05`** and `ReplayCompatibleGameVersions` is `["GV04", GameVersion]`
  (`src/battlecode/sim_types.nim:16,71`). This run **extends** that list; it does not reset it.
- **The shipped coworld version is 0.2.0.** This run ships **0.3.0**.

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as bc26/bc20 (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, two generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. No new repo (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=awu\|scaffold` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc21/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc21` bytes anywhere. |
| Real art, starter chrome verbatim | 2021 sprites cut from `battlecode21/client/visualizer/src/static/img/` into `data/atlas_bc21.*` (credited in `NOTICE`); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc21 game block appended** plus the one-rule killfeed fix named in §Viewer. |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **445 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26].game_config` (unchanged), `variants[bc20].game_config` (unchanged), `variants[bc21].game_config` (new) and `certification.game_config` (unchanged, bc26); never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc21 policy set is in §Packaging. |

---

## The game

**Battlecode 2021 "Campaign", played by doctrine, simulated in Nim.** Two cogs each command a
party on a symmetric grid between 32×32 and 64×64. Neither cog moves a robot. At t=0 each writes a
**doctrine** — a JSON sheet of ten named knobs — and the deterministic sim plays the whole match
from those two sheets while both cogs watch.

The clock is the **election**. Every round, one citizen's vote is auctioned: each Enlightenment
Center may bid influence, the single highest bidder in the game wins the vote for its team and
pays its bid, and the other team's top bidder pays **half its bid, rounded up, for nothing**. At
round 1500 the team with more votes wins. Before then, a team that loses **every** robot loses
immediately.

Influence is the only resource, it is **not** a global pool — it sits inside each Enlightenment
Center — and it does three incompatible jobs: it buys units, it buys votes, and it is the thing an
enemy politician steals when it converts a Center. Each Center passively earns `ceil(0.2·√t)` per
round (about 8 500 over a whole game, on top of its starting 150). **Slanderers** are the
multiplier: a slanderer built for `x` influence pays its parent Center
`floor((1/50 + 0.03·e^(−0.001x))·x)` per round for its first 51 rounds — a ~2.35× return for
`x ≈ 21…130` — and then, at 300 rounds old, silently becomes a politician of the same conviction.
**Muckrakers** are cheap (minimum influence 1), see furthest, and **expose** enemy slanderers:
the slanderer dies and the muckraker's team gets a `+0.001 × (that slanderer's influence)`
multiplier on every speech for the next 50 rounds. **Politicians** are walking bombs: a politician
**empowers**, splitting `conviction − 10` equally among every other robot in its chosen radius —
healing friendly units, feeding friendly Centers, and converting or killing everything else — and
then dies.

That triangle is the whole doctrine game. Slanderers print money but die to a single muckraker.
Muckrakers are free but win nothing on their own. Politicians convert Centers but cost the
influence the slanderers were supposed to make. And every influence point spent on any of them is
a vote not bought.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. The episode
seed decides which slot takes engine-side **A (red)** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc20/maps.nim`).

### Constants (verbatim from the pinned engine — `common/GameConstants.java`, `common/RobotType.java`)

Generated into `src/battlecode/years/bc21/constants.nim`, never hand-typed (§Sim module).

| type | spawned by | conviction ratio | base action cooldown | initial cooldown | action r² | sensor r² | detection r² | true sense | bytecode limit |
|---|---|---|---|---|---|---|---|---|---|
| `ENLIGHTENMENT_CENTER` | — (map) | 1.0 | 2.0 | 0 | 2 | 40 | 40 | yes | 20 000 |
| `POLITICIAN` | EC | 1.0 | 1.0 | **10** | 9 | 25 | 25 | no | 15 000 |
| `SLANDERER` | EC | 1.0 | 2.0 | 0 | 0 | 20 | 20 | no | 7 500 |
| `MUCKRAKER` | EC | **0.7** | 1.5 | **10** | 12 | 30 | **40** | yes | 15 000 |

Game constants: `EMPOWER_TAX 10`, `EXPOSE_BUFF_FACTOR 0.001` (a Java `double`),
`EXPOSE_BUFF_NUM_ROUNDS 50`, `EMBEZZLE_NUM_ROUNDS 50`, `EMBEZZLE_SCALE_FACTOR 0.03f` (a Java
`float`), `EMBEZZLE_DECAY_FACTOR 0.001f` (a Java `float`), `CAMOUFLAGE_NUM_ROUNDS 300`,
`INITIAL_ENLIGHTENMENT_CENTER_INFLUENCE 150`,
`PASSIVE_INFLUENCE_RATIO_ENLIGHTENMENT_CENTER 0.2f`, `ROBOT_INFLUENCE_LIMIT 100 000 000`,
`MIN_FLAG_VALUE 0`, `MAX_FLAG_VALUE 16 777 215`, `MAP_MIN_WIDTH/HEIGHT 32`,
`MAP_MAX_WIDTH/HEIGHT 64`, **`GAME_MAX_NUMBER_OF_ROUNDS 1500`**. There is no `MAX_ROBOT_ID` in
2021 (removed in patch 2021.2.0.0 because conversions mint new ids).

Derived functions:
`convictionAtSpawn(type, C) = ceil(convictionRatio × C)`;
`cooldownAdded(type, tile) = actionCooldown / passability(tile)` (a Java `double` division);
`ecPassive(t) = ceil(0.2f · √t)`;
`slandererPassive(x, roundsAlive) = roundsAlive ≤ 50 ? floor(x·(1/50 + 0.03f·exp(−0.001f·x))) : 0`;
`buff(team) = 1 + 0.001 × numBuffs(team)`.

### Which patch, and the 3000-round question

The idea says "up to 3000 rounds (patched mid-season)". **The final patched constant is 1500**, and
this note pins 1500. Named exactly: patch **2021.2.3.0 (2021-01-13)** — "Reduce number of rounds
per game (3000 → 1500)" (`specs/specs.md.html` §Changelog). The spec's §Victory prose still says
"at the conclusion of 3000 rounds"; it is stale, and the engine disagrees with it —
`GameConstants.GAME_MAX_NUMBER_OF_ROUNDS = 1500`, `GameMapIO.Serial.deserialize` sets every map's
`rounds` from that constant, and `GameWorld.timeLimitReached()` is
`currentRound >= gameMap.getRounds()`. Where the prose and the engine disagree, **the engine wins**
and `docs/RULES-BC21.md` records both readings. This is decided, not open.

The season's other pinned patch is the one daveey's ranking calls "the major mid-season nerf":
**2021.3.0.0 (2021-01-22)** — muckraker buff changed from exponential (`1.01^n`, later `1.001^n`)
to **linear** (`1 + 0.001·n`), the buff no longer applies to friendly Enlightenment Centers, and
empowering is **taxed before** the buff is applied. All three are in the pinned source and all
three are implemented (rule 6.3 below). The build target is the last release of the season,
**2021.3.0.5 (2021-02-02)**, which is what `gradle.properties` at the pinned commit declares.

### The 2021 rule set — exact numbered resolution rules

The sim's own step list. Numbers 1–7 are one round; re-ordering any of them is a rules change and
bumps `GameVersion`. It mirrors `GameWorld.runRound` / `processBeginningOfRound` /
`updateDynamicBodies` / `processEndOfRound` exactly.

1. **Beginning of round.** `currentRound += 1`. Then **buff expiry**: for each team, every buff
   batch whose recorded expiry round is `≤ currentRound` is subtracted from `numBuffs` and dropped
   (`TeamInfo.updateNumBuffs`). Then every robot runs `processBeginningOfRound` — a no-op in 2021,
   kept as a named step because the hash chain and the parity trace are taken around it.
2. **Turn order.** Iterate the robots in **spawn order** (`ObjectInfo.eachDynamicBodyByExecOrder`
   — append on spawn, remove-by-value on death), **not** id order, over a **snapshot of the order
   taken once at the start of the sweep**. A robot spawned or converted during this sweep
   therefore takes **no turn this round**; a robot destroyed during the sweep is skipped when its
   slot comes up. Map bodies (the Enlightenment Centers) are appended in the map file's own order,
   sorted by the file's body ids (`LiveMap`'s constructor sorts `initialBodies` by id).
3. **Beginning of turn.** `if cooldownTurns > 0: cooldownTurns = max(0, cooldownTurns − 1)`; the
   robot's `DecisionOps` budget is reset (§Sim module — this replaces the Java bytecode limit).
4. **Run the controller.** Every robot runs its team's chassis under that team's doctrine, spending
   at most its `DecisionOps` budget. A robot may take an **action** only while `cooldownTurns < 1`;
   every action adds `type.actionCooldown / passability(the robot's CURRENT tile)` to
   `cooldownTurns` **before** the action's effect is applied (`InternalRobot.addCooldownTurns`; for
   a move this means the cooldown is charged at the tile being left). The legal actions, with their
   exact preconditions:
   1. **Move** (`POLITICIAN`, `SLANDERER`, `MUCKRAKER`): the destination is one of the 8 adjacent
      tiles, on the map, and unoccupied; `isReady()`. There is no terrain that blocks movement —
      passability only changes the cooldown. A tile of passability `0.0` therefore yields an
      **infinite** cooldown and freezes the robot for ever; the port reproduces this (§Maps: the
      one map with such tiles is excluded).
   2. **Build robot** (`ENLIGHTENMENT_CENTER` → `POLITICIAN` | `SLANDERER` | `MUCKRAKER`):
      `isReady()`; `1 ≤ influence ≤ this EC's current influence`; the target tile is one of the 8
      adjacent tiles, on the map and unoccupied. Effect, in this order: charge the cooldown;
      `addInfluenceAndConviction(−influence)` on the EC; mint an id from the `IDGenerator`; spawn
      the unit with `conviction = ceil(ratio × influence)`,
      `convictionCap = conviction`, `parent = this EC`, appended to the exec order; then
      `setCooldownTurns(type.initialCooldown)` (10 for politicians and muckrakers, 0 for
      slanderers).
   3. **Empower** (`POLITICIAN`, radius `r² ≤ 9` chosen by the caller): `isReady()`. Effect, in
      this order:
      1. charge the cooldown;
      2. collect every robot in `r²` of the politician **in map-scan order** — `x` ascending
         outer, `y` ascending inner, over the clamped bounding box of side
         `2·(ceil(√r²)+1)+1`, keeping only tiles with `distanceSquared ≤ r²`
         (`GameWorld.getAllLocationsWithinRadiusSquared`). This order is load-bearing: it fixes the
         order in which converted robots are re-spawned, and therefore their ids.
      3. `numBots = |collected| − 1` (excluding self). **If `numBots == 0`, no robot is affected**
         — but the politician still dies at step 7.
      4. `convictionToGive = conviction − 10` (a `double`). **If `≤ 0`, no robot is affected** —
         but the politician still dies.
      5. `convictionPerBot = convictionToGive / numBots`; `buff = 1 + 0.001 × numBuffs(own team)`,
         read **once**.
      6. For each collected robot other than self, compute `conv`:
         - a **friendly Enlightenment Center**: `conv = convictionPerBot`, **unbuffed**;
         - **any other Enlightenment Center** (enemy or neutral): `convNeeded = conviction / buff`;
           if `convictionPerBot ≤ convNeeded` then `conv = convictionPerBot × buff`, else
           `conv = conviction + (convictionPerBot − convNeeded)` — i.e. the buff applies only up to
           the point of conversion and the overflow crosses unbuffed;
         - **everything else** (friendly or enemy unit): `conv = convictionPerBot × buff`.
      7. apply `empowered(caller, (int)conv, ownTeam)` — **truncation toward zero**:
         - if the target is on the caller's team the amount is positive, otherwise negated;
         - an Enlightenment Center takes `addInfluenceAndConviction(amount)` (influence and
           conviction move together, clamped above at `ROBOT_INFLUENCE_LIMIT`);
         - every other robot takes `addConviction(amount)`, clamped above at its own
           `convictionCap` (its conviction at spawn). Healing above the cap is lost;
         - if the result is `conviction < 0`: a `POLITICIAN` or an `ENLIGHTENMENT_CENTER` is queued
           for **conversion** with `newInfluence = |influence|` and `newConviction = −conviction`;
           a `SLANDERER` or `MUCKRAKER` is simply destroyed. Either way the robot is destroyed now.
      8. after the loop, spawn the queued conversions **in the order they were queued**, on the
         empowering politician's team, each keeping the destroyed robot's **old parent pointer**,
         with a **new id** and **cooldown 0** (conversions never take an initial cooldown). A
         converted unit's conviction is then set to `newConviction` (capped by its new
         `convictionCap`); a converted Enlightenment Center takes
         `addInfluenceAndConviction(0)`, which snaps conviction to influence.
   4. **Expose** (`MUCKRAKER`, by location or by id): `isReady()`; the target is on the map, within
      `r² ≤ 12`, exists, is a `SLANDERER`, and is on the enemy team. Effect: charge the cooldown;
      add the slanderer's **influence** to this team's `buffsToAdd` (applied at step 6.3); destroy
      the slanderer. A slanderer that has already camouflaged into a politician can no longer be
      exposed.
   5. **Bid** (`ENLIGHTENMENT_CENTER`, any number of times per turn): **not an action** — no
      `isReady()` check, no cooldown. `1 ≤ influence ≤ current influence`. Effect: the previous bid
      (if any) is refunded, then the new bid is **deducted from influence immediately** and held
      hostage until step 6.2. Bidding therefore reduces what the Center can build **this same
      turn**.
   6. **Set flag** (any robot): **not an action** — no `isReady()` check, no cooldown.
      `0 ≤ flag ≤ 16 777 215`. The flag persists until changed.
   7. **Sense / detect / read flags** (free, charged only against `DecisionOps`): sense robot
      details within `sensorRadiusSquared` — **politicians and slanderers see slanderers as
      politicians** (`canTrueSense` is true only for Enlightenment Centers and muckrakers);
      detect the mere presence of robots within `detectionRadiusSquared` (larger than sensor range
      for muckrakers only); sense the passability of any tile in sensor range; read the flag of any
      robot the caller can sense, **of either team**, plus — with no range limit at all — the flag
      of any Enlightenment Center, and, if the caller *is* an Enlightenment Center, the flag of any
      robot on the map.
5. **End of turn.** `roundsAlive += 1`. (The engine also records bytecodes here; the port records
   `DecisionOps` used, for the perf test only.)
6. **End of round**, after every robot has taken its turn. In this order:
   1. **Collect bids.** Sweep every robot (the port sweeps in **ascending robot id**; see §Sim
      module, Determinism, for the proof that this is order-independent). For a player-team
      Enlightenment Center, record `bid`, then `resetBid()` (which refunds the held influence).
      Per team the recorded top bidder is the maximum under **(bid descending, `roundsAlive`
      ascending, id ascending)** — exactly `InternalRobot.compareTo`, and exactly the spec's
      "lowest robot age then lowest robot ID". A team with any Enlightenment Center always has a
      top bidder, even if every Center bid 0. Then run each robot's `processEndOfRound` (6.4/6.5).
   2. **Settle the auction.** If `bidA > bidB` and `bidA > 0`: team A wins the vote, its top bidder
      pays `bidA` in full, `votes[A] += 1`. Symmetrically for B. Then, for **each** team that did
      not win, its top bidder pays `ceil(bid/2)` — implemented as `(bid + 1) / 2` in integers — for
      nothing. If both teams' top bids are equal (including both zero) **nobody wins the vote** and
      both pay half. Neutral Centers never bid.
   3. **Apply exposes.** For each team, `numBuffs += buffsToAdd`, recorded with expiry round
      `currentRound + 1 + 50`; `buffsToAdd = 0`. A buff therefore first affects speeches on
      `currentRound + 1` and is dropped at step 1 of round `currentRound + 51`.
   4. **Passive influence** (inside the 6.1 sweep, per robot): `target = parent ?: self`. If
      `target` no longer exists, nothing happens — **capturing an Enlightenment Center cuts off the
      income of every slanderer it built**. Otherwise, if the robot's team is a player team and its
      passive amount is `> 0`, `target.addInfluenceAndConviction(amount)` where the amount is
      `ceil(0.2f·√currentRound)` for an Enlightenment Center and
      `floor(x·(1/50 + 0.03f·e^(−0.001f·x)))` for a slanderer with `roundsAlive ≤ 50`, and 0
      otherwise. Neutral Centers earn nothing.
   5. **Camouflage** (inside the same sweep): a `SLANDERER` whose `roundsAlive == 300` becomes a
      `POLITICIAN`, keeping its id, influence, conviction, conviction cap, parent and flag.
   6. **End-of-match check**, in this order, first hit wins:
      1. **Annihilation.** If team A has zero robots, **B wins** (`annihilated`); else if team B has
         zero robots, A wins. A double wipe in the same round therefore awards the win to **B** —
         the engine's own asymmetry, reproduced.
      2. If `currentRound >= 1500` and no winner is set: **more votes** (`more_votes`) → **more
         Enlightenment Centers owned** (`more_enlightenment_centers`) → **higher total influence
         summed over all living non-neutral robots** (`more_influence`) → **coin flip**
         (`coin_flip`).
   7. Record the per-team round stats and close the round record.
7. **Hash chain.** Append this round's state hash (§Sim module).

**Deliberate non-rules, verified absent from the 2021 engine and therefore absent here:** there is
no global message board (flags are the only channel), no terrain that blocks movement, no unit cap,
no self-destruct a player can call (`disintegrate` was made private in 2021), no cows and no NPCs of
any kind, no map symmetry field and no engine use of symmetry, and `RobotControllerImpl`'s static
`java.util.Random` is assigned on every controller construction and then **never read** — unlike
2020, there is no transaction-id RNG quirk to reproduce.

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc21` variant is **best-of-three on three
distinct maps from the `mixed` pool, played to the engine's own 1500-round cap**. The cap is the
engine's, not ours: 1500 is `GAME_MAX_NUMBER_OF_ROUNDS` and 1500 is also the number of votes on
offer, so a game that runs the distance is *decided* by the cap rather than merely stopped at it.

```
container start, map load, seat connect              ≤  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    ≤  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 1500 rounds                         ≤ 340 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 110)
score + replay write + shutdown grace                ≤  30 s
                                                       -------
worst case                                             445 s   <= 720 s
```

Honest per-round estimate, so the builder can check it. The `mixed` pool tops out at 48×48 = 2 304
tiles, and 2021 has **no unit cap** — a muck-spam doctrine buys 1-influence muckrakers, so unit
count is bounded only by free tiles. Take a pessimistic mature game at **350 robots per team**, i.e.
700 robot-turns per round. Each robot-turn is capped at its `DecisionOps` budget (EC 2 000,
politician 1 500, muckraker 1 500, slanderer 750), so the **enforced** worst case is
≈ 1.05 × 10⁶ ops/round and ≈ 1.6 × 10⁹ ops for a 1500-round game. The realistic average is far
lower — a muckraker's turn is a ≤ 129-tile detect sweep plus a direction choice, ≈ 150 ops — giving
≈ 1 × 10⁵ ops/round and ≈ 1.6 × 10⁸ per game, single-digit seconds in release Nim. **The estimate is
enforced, not trusted:**

- `perGameBudgetSeconds = 110` and `matchBudgetSeconds = 340` are hard monotonic-clock guards. A
  game that blows its guard is abandoned, the finished games are scored, and
  `results.reason = deadline`.
- `tests/test_bc21_perf.nim` plays a full 1500-round game on `PaperWindmill` (48×48, the largest map
  in the variant's pool) with **both seats on `opening: muck_spam`, `muck_ratio: 90`** — the
  configuration that maximises unit count — and **fails CI above 75 s**.
- If that gate ever goes red the fix is one config value — `gamesPerMatch: 3 → 1` in the `bc21`
  variant — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because the 2021 archetypes (muck-spam, slanderer-turtle,
  buff-mucks, muck-flank) are a rock-paper-scissors *across map shapes* — the season's record number
  of 3-2 series is the evidence — and one map would rank the map, not the doctrine.

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

### Scoring, sign, and what the bc21 league ranks by

The 2021 game is win/lose; it has no point formula. This one is defined here, and it is a continuous
reading of the engine's own end ladder so that the score and the winner never tell different
stories:

```
alive[t]      = 1 if team t has at least one living robot at the final round else 0
survival[t]   = f32(alive[t])   / f32(max(1, alive[A] + alive[B]))        # 0.5 / 0.5 if both alive
votes[t]      = teamInfo.votes[t]                                        # the MORE_VOTES rung
centers[t]    = living Enlightenment Centers owned by t                  # the MORE_ENLIGHTENMENT_CENTERS rung
influence[t]  = sum of influence over ALL living non-neutral robots of t # the MORE_INFLUENCE rung
share_v[t]    = f32(votes[t])      / f32(max(1, votes[A] + votes[B]))
share_c[t]    = f32(centers[t])    / f32(max(1, centers[A] + centers[B]))
share_i[t]    = f32(influence[t])  / f32(max(1, influence[A] + influence[B]))
points[t]     = int(40.0'f32 * survival[t] + 35.0'f32 * share_v[t]
                  + 15.0'f32 * share_c[t] + 10.0'f32 * share_i[t])       # TRUNCATION, not rounding
```

Three load-bearing details, each pinned by a test vector in `tests/test_bc21_scoring.nim`:

- every share is narrowed through **float32** before the weighted sum, and the sum is **truncated**
  by the `int()` cast. The reason is **recorder/re-deriver agreement**: the same arithmetic runs
  natively on x86-64 and in wasm32 and must produce the same integer;
- the four terms are exactly the engine's four rungs, in the engine's own priority order and
  weighted in that order, so an `annihilated`, `more_votes`, `more_enlightenment_centers` or
  `more_influence` win always comes with the matching share above 0.5;
- points are in `[0, 100]` and the two seats' points sum to ≤ 100.

Per seat, over the games actually played:

```
results.scores[t] = 100.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** The 100-per-game win bonus dominates the ≤ 100-point spread across three
games, which is what makes "lose the election, lose the match" true in the ranking as well as in the
rules. **The `bc21` league ranks by `results.scores`** (Elo over the resulting ordering), exactly as
the bc26 and bc20 leagues do. A `deadline` episode scores the games that finished; a `fault`
episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` in snake_case, plus our one
wall-clock value:

| `end_reason` | engine origin | meaning |
|---|---|---|
| `annihilated` | `ANNIHILATED` | one team had zero robots at an end-of-round check (a double wipe awards it to B) |
| `more_votes` | `MORE_VOTES` | round 1500 reached; more citizens' votes won |
| `more_enlightenment_centers` | `MORE_ENLIGHTENMENT_CENTERS` | votes tied; more Centers owned |
| `more_influence` | `MORE_INFLUENCE` | Centers tied; higher total influence over all living non-neutral robots |
| `coin_flip` | `WON_BY_DUBIOUS_REASONS` | everything tied; a draw from the world RNG |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded |

`coin_flip` and `abandoned` are already in the manifest's `end_reason` enum (bc20 introduced them);
the other four are added (§Packaging).

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from bc26/bc20**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped: a partial replay and `[0, 0]` are still written | `[0, 0]` |

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for bc26
and bc20). Container exit codes are unchanged: `0` whenever results + replay were attempted
(including `deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep answering for
the ~20 s shutdown grace, the websocket handler keeps its `Ping → Pong` **echo** (it must return the
ping's payload — commit `cb37075`) and does not filter binary frames.

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged from bc26/bc20: the player container is a thin registrar
and every decision is taken inside the **game** container, because that is the only container the
platform injects the `anthropic_api_key` coworld secret into
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

### The bc21 doctrine sheet — ten knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc21 chassis. Unknown key, wrong
type or out-of-range value → **that field's default**, recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by
answering badly — only by answering weakly. **Every setting of every knob drives the same competent
chassis**: no knob value selects a different, weaker bot (the LEARNINGS pin). The chassis always
builds, always defends its own Centers, always paths, and always ends its games; the knobs move
*how much of what, when* — never *whether it plays*.

| field | type / values | default | what it changes (`src/battlecode/years/bc21/chassis/…`) |
|---|---|---|---|
| `opening` | `muck_spam` \| `slanderer_turtle` \| `balanced` | `balanced` | `ec.nim openingPlan()` — the build order for rounds 1…150. **`muck_spam`** (wololo's lineage): one 21-influence slanderer, then a 1-influence muckraker in a rotating direction every time the Center is ready, with the first eight told to scout; ≈ 40 muckrakers by round 100. **`slanderer_turtle`** (the babyducks pole): slanderers at the largest breakpoint the Center can afford (see `slandererBreakpoints`), plus one 20-conviction defender politician per four slanderers, and no muckrakers before round 80. **`balanced`** (California Roll's opening): alternate slanderer / 1-influence muckraker, with a single 16-influence politician on the seventh build. |
| `slanderer_ratio` | int 0…100 | 45 | `ec.nim spendMix()` — the percentage of post-opening build influence that goes to slanderers. |
| `muck_ratio` | int 0…100 | 25 | `ec.nim spendMix()` — the percentage that goes to muckrakers. Politicians take `100 − slanderer_ratio − muck_ratio`. **If the two sum above 100** they are renormalised deterministically: `s' = s·100 div (s+m)`, `m' = 100 − s'`, politicians 0. |
| `politician_size_curve` | `cheap` \| `ramp` \| `fat` | `ramp` | `ec.nim politicianInfluence(round)` — `cheap` = 18 flat; `ramp` = `clamp(18 + round div 25, 18, 120)`; `fat` = `clamp(40 + round div 8, 40, 400)`. Overridden in one case for every curve: when the chassis has a known target Center's conviction `c` and can afford it, it sizes that politician at `c + 11` (the 10-influence tax plus one), which is the cheapest guaranteed capture. |
| `bid_policy` | `never` \| `fixed` \| `proportional` \| `escalate_when_ahead` | `proportional` | `bids.nim` — `never`: never bid (every influence point goes to the army; the team must win by annihilation or on the Centers/influence rungs). `fixed`: bid 2 whenever influence ≥ 200. `proportional`: California Roll's adaptive ladder — start at 2; after a win divide by 1.25 (floor 1); after a loss double, and if the result exceeds 5 % of the Center's influence clamp it to `ceil(0.025 × influence)`; bid the ladder value once influence ≥ 400, else bid 1 while influence ≥ 50. `escalate_when_ahead`: the same ladder, doubled while own votes > opponent votes and halved (banking the difference) while behind by more than 100 votes. |
| `expansion` | `neutral_centers_first` \| `defend_home` | `neutral_centers_first` | `ec.nim targetPolicy()` — `neutral_centers_first` sends capture politicians at the neutral Center minimising `distance² + 100 × lastKnownConviction` before ever aiming at an enemy Center; `defend_home` keeps every politician within `r² ≤ 100` of an own Center and only leaves to answer a sensed threat. |
| `flank_policy` | `screen_home` \| `hunt_slanderers` \| `flank_wide` | `hunt_slanderers` | `muckraker.nim roam()` — `screen_home`: hold a ring at Chebyshev 5 around own Centers and expose anything that walks in. `hunt_slanderers`: path to the nearest sensed or flag-reported enemy slanderer, else toward the nearest known enemy Center. `flank_wide` (California Roll's "muck flanking"): route to the enemy Center along the map edge, entering from the far side, and sit on the enemy's slanderer ring rather than its politician wall. |
| `empower_threshold` | int 0…300 (percent) | 60 | `politician.nim shouldEmpower()` — a politician empowers when the enemy conviction it would remove inside its best radius is at least `empower_threshold` % of its own usable conviction (`conviction − 10`, buffed). 0 means "empower on contact"; 250 means "only in a crowd". A politician adjacent to a capturable Center always empowers regardless of the threshold, and a politician about to die to a sensed enemy politician empowers rather than waste itself. |
| `convert_over_kill` | bool | `true` | `politician.nim pickRadius()` — when `true`, the radius search maximises **convertible** conviction (enemy Centers and enemy politicians, which come back as your robots) and breaks ties away from radii that waste conviction on friendly units; when `false`, it maximises total enemy conviction removed, which favours popping slanderer and muckraker clusters. |
| `eco_exponential_round` | int 1…1500 | 700 | `ec.nim phase()` — the round at which compounding stops. Before it, `slanderer_ratio` applies at full weight and every Center reinvests. From it, **slanderer production stops entirely**, the slanderer share is redistributed to politicians and muckrakers in their existing proportion, and `bids.nim` is allowed to spend down to a 200-influence floor. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

**Every knob must have teeth.** `tests/test_bc21_knobs.nim` is a CI gate that proves each of the ten
visibly changes play, with a named signed stat delta per knob (§Tests item 13), and the endcard
reports the economic story so a spectator can see the knob in the match.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the season's two poles, so the league's headline matchup is the
one the metagame actually turned on.

- **champion #1, `battlecode-bc21-turtle` (daveey)**: *"You command a Battlecode 2021 party. A
  slanderer built for 130 influence pays your Enlightenment Center 6 influence per round for 51
  rounds — a 2.3x return — and then becomes a free politician 300 rounds later. Your doctrine: print
  money and buy the election. Set opening to \"slanderer_turtle\", slanderer_ratio 60-80,
  muck_ratio 10-20, politician_size_curve \"ramp\", expansion \"neutral_centers_first\" and
  flank_policy \"screen_home\" so enemy muckrakers never reach your slanderer ring. Set
  eco_exponential_round late (900-1200): the longer you compound, the more votes you can buy at the
  end. Use bid_policy \"escalate_when_ahead\" — there are exactly 1500 votes and the loser of each
  auction still pays half its bid, so bid when you are winning and bank when you are not. Keep
  empower_threshold high (100-180) and convert_over_kill true. In notes, say what round you expect
  to be out-earning them by and what you do if a muckraker rush arrives before round 200."*
- **champion #2, `battlecode-bc21-muckrush` (daveey-1)**: *"You command a Battlecode 2021 party. A
  muckraker costs 1 influence and kills any enemy slanderer it can reach, and every slanderer it
  exposes buffs all of your speeches by 0.1% of that slanderer's influence for 50 rounds. Your
  doctrine: their economy never starts. Set opening to \"muck_spam\", muck_ratio 55-80,
  slanderer_ratio 5-20, flank_policy \"flank_wide\" so your muckrakers arrive on the far side of
  their Center where the slanderers sit, and politician_size_curve \"cheap\" or \"ramp\" so the
  follow-up politicians arrive while the buff is still up. Set eco_exponential_round early
  (150-400) and expansion \"neutral_centers_first\" — a neutral Center you take is a Center they
  cannot. Keep empower_threshold low (0-40) and convert_over_kill false: you are killing slanderers,
  not collecting politicians. Use bid_policy \"fixed\" or \"never\"; you intend to win by
  annihilation or on Centers, not by outbidding a bank. In notes, say what you do if their turtle
  survives to round 600."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the economy tables (slanderer breakpoints and the Center passive curve), the map
cards for all three games, the scoring formula, the alias pair, and the reply contract ("reply with
ONE JSON object; your reply must begin with `{`"). The assistant turn is prefilled with `{` and the
prefix re-attached before parsing (the procgen 0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`). It gains a `bc21`
arm with two published names. **The manifest still declares only `awu` and `scaffold`** — the two
ids the certification fixture seats — and `PLAYER_SCRIPTED` resolves per year, exactly as bc20 does:

| `PLAYER_SCRIPTED` | on `year: "bc21"` resolves to |
|---|---|
| `awu`, `california-roll`, or anything unrecognised | **`california-roll`** — the strong published doctrine and the champion chassis |
| `scaffold`, `examplefuncsplayer`, `examplefuncsplayer21`, `example` | **`examplefuncsplayer21`** — the deliberately weak floor and the oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field
(D1). `defaultBaselineFor("bc21")` is `california-roll`, so a seat that says nothing useful plays
the strong doctrine, not the weak floor.

**`california-roll` — the strong baseline and the champion chassis.** Behaviour ported from
`StoneT2000/Battlecode2021` `src/maxecosushi/` (AGPL-3.0, commit `5c2a7ee`), with the muck-spam
opening from `iliao2345/Battlecode2021` `src/muckspam/` and `src/membrane3/` (AGPL-3.0, commit
`d620569`) and the multi-Center flag protocol from `BSreenivas0713/Battlecode2021`
`src/musketeerplayerfinal/` (AGPL-3.0, commit `d24af14`), all parameterised by the ten knobs.
Its scripted reply is the all-defaults sheet. Algorithm, per role:

- **Enlightenment Center** (`ec.nim`): every round, in this order — (1) sense the neighbourhood and
  fold every sensed enemy politician's conviction into `nearbyEnemyFirePower`; (2) read every own
  robot's flag through the Center's unlimited flag access and update the shared maps of known
  neutral Centers, enemy Centers and enemy slanderer sightings; (3) place a bid per `bid_policy`
  **after** reserving `nearbyEnemyFirePower + 25` influence for defence; (4) if a target Center's
  conviction is known and affordable, build the `c + 11` capture politician toward it; else build
  from `spendMix()` under `phase()`; (5) set its own flag to the compressed
  `[kind, x, y, payload]` word (below). Defence is unconditional and knob-independent: whenever a
  sensed enemy politician's conviction exceeds the Center's own conviction, the Center spends its
  next build on a defender politician of `min(influence, thatConviction + 11)` regardless of every
  ratio knob — this is the D2 rule that stops any knob setting from producing a bot that stands
  still and dies.
- **Politician** (`politician.nim`): if a capturable Center is inside `r² ≤ 9`, size the radius so
  the Center is included and empower. Else evaluate all four legal radii `{1, 2, 4, 9}` with the
  scan-order robot set the sim will actually use, score each by `convert_over_kill`, and empower if
  the best score clears `empower_threshold`. Else path to the current target
  (`expansion`-selected) or, if none is known, along the map's symmetry axis toward the mirrored
  position of the own Center — which on a symmetric map is always an enemy Center.
- **Slanderer** (`slanderer.nim`): never acts; it moves away from the nearest sensed enemy and
  toward the own Center's "safe side" (the direction with the fewest sensed enemies within
  `r² ≤ 20`), keeping a diagonal lattice spacing so a single enemy politician cannot catch two of
  them. After camouflage it is a politician and runs `politician.nim`.
- **Muckraker** (`muckraker.nim`): expose anything exposable within `r² ≤ 12` (preferring the
  highest-influence slanderer, which is the biggest buff), else roam per `flank_policy`, else park
  adjacent to a sensed enemy Center to deny it a build tile.
- **Flags** (`flags.nim`): one 24-bit word, `[kind:3][x:6][y:6][payload:9]`, with kinds
  `NEUTRAL_EC_HERE`, `ENEMY_EC_HERE`, `SLANDERER_SEEN`, `UNDER_ATTACK`, `SCOUT_DONE`,
  `EC_INFLUENCE_HINT`, `NEED_DEFENCE`, `SILENT`. Coordinates are map-relative and 6 bits, which is
  exactly enough for a 64-wide map. **The word format is shared by both teams**, which is
  deliberate: it reproduces the year's flag-decoding metagame, and it is what lets the endcard
  decode both sides' traffic (§Viewer).
- **Pathing** (`pathing.nim`): a bounded BFS over the sensed window with a passability-weighted cost
  (`1/passability` per step), falling back to a greedy step with a 6-tile no-repeat history to break
  oscillation. Charged against `DecisionOps`.
- **Economy tables** (`economy.nim`): the `slandererBreakpoints` table — the ascending influence
  values at which `floor(x·(1/50 + 0.03·e^(−0.001x)))` increases,
  `[21, 41, 63, 85, 107, 130, 154, 178, 203, 228, 255, 282, 310, 339, 368, 399, 431, 463, 497, 532,
  568, 605, 643, 683, 724, 766, 810, 855, 902, 949, 999, …]` — is **generated from the engine's own
  formula, not typed in**, and CI byte-diffs it against a JDK regeneration. It is exactly the table
  California Roll shipped (`src/maxecosushi/EnlightmentCenter.java:21`), which is the cross-check
  that the port reproduced the formula and not a lookalike.

**`examplefuncsplayer21` — the weak floor and the parity oracle's other side.** Ported
**statement-for-statement** from
`battlecode21/example-bots/src/main/examplefuncsplayer/RobotPlayer.java`: an Enlightenment Center
picks a random spawnable type and tries to build it with 50 influence in each of the eight
directions **in order, breaking out of the loop at the first direction that fails**, then bids 1; a
politician empowers at `r² = 9` if any enemy is sensed inside the action radius, else tries one
random move; a slanderer tries one random move; a muckraker exposes the first sensed enemy that can
be exposed, else tries one random move. **It may not gain behaviour** — it is one side of the
differential oracle. Its scripted reply is the all-defaults sheet (it reads no knob).

Both replies go through the **same** `validate` the LLM path uses, which is what makes the
bounded-orders test meaningful and an LLM doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `california-roll` chassis, `results.fallbacks[seat] = 1`, a `doctrine_fallback` event names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default; the rest of the sheet applies |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| a side takes 2 games | the episode settles immediately — no padding |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `california-roll` baseline reply:

```json
{"sheet":{"opening":"balanced","slanderer_ratio":45,"muck_ratio":25,
          "politician_size_curve":"ramp","bid_policy":"proportional",
          "expansion":"neutral_centers_first","flank_policy":"hunt_slanderers",
          "empower_threshold":60,"convert_over_kill":true,
          "eco_exponential_round":700},
 "notes":"default california-roll doctrine","motto":"Vote early, vote often."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc21/constants.nim` | **new, generated** | every `GameConstants` value + the `RobotType` table, emitted by `tools/gen_year_constants.py --year bc21` from the pinned battlecode21 checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc21/world.nim` | **new** | world state, the grid (passability, occupancy), robots, spawn/destroy, the exec order, and every action of rule 4 |
| `src/battlecode/years/bc21/rules.nim` | **new** | the round loop (rules 1–7), the end ladder, the points formula |
| `src/battlecode/years/bc21/empower.nim` | **new** | `getAllLocationsWithinRadiusSquared` in engine scan order, the empower/convert/heal arithmetic, `expose` |
| `src/battlecode/years/bc21/votes.nim` | **new** | bid collection, the `compareTo` top-bidder rule, the auction settlement, the buff-expiry ledger |
| `src/battlecode/years/bc21/economy.nim` | **new** | Center passive influence, slanderer embezzle, camouflage, the `slandererBreakpoints` table |
| `src/battlecode/years/bc21/maps.nim` | **new** | the converted bc21 pool, the loader, the per-episode draw (`drawMaps`, `sideAslotFor`) |
| `src/battlecode/years/bc21/knobs.nim` | **new** | the ten-knob `Doctrine21` type, defaults, per-field repair, `toJson`, `plainWords` |
| `src/battlecode/years/bc21/chassis/*.nim` | **new** | `croll.nim`, `scaffold21.nim`, `ec.nim`, `politician.nim`, `slanderer.nim`, `muckraker.nim`, `bids.nim`, `flags.nim`, `pathing.nim`, `kit.nim` |
| `src/battlecode/fdlibm.nim` | **new, year-neutral** | a port of fdlibm `exp` (the reference implementation `StrictMath.exp` uses), so the embezzle formula is identical natively and under wasm with no libm in the loop |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc21", title: "Battlecode 2021 — Campaign", maxRounds: 1500, pools: @["small","mixed","large"], atlas: "atlas_bc21")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc21`; `Session` gains a `yBc21` branch; `poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm. `Bc21UnitNames = ["enlightenment_center", "politician", "slanderer", "muckraker"]` is added beside `Bc20UnitNames` so `first_build.unit` has a documented vocabulary (the r1-F14 lesson) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV06`, `ReplayCompatibleGameVersions` → `["GV04", "GV05", GameVersion]`, prepend-only changelog entry; **new** year-neutral `ScriptedChassis` enum (below) |
| `src/battlecode/baselines.nim` | **changed** | a `yBc21` arm in `defaultBaselineFor` and `baselineFor`; `blCaliforniaRoll` and `blExamplefuncsplayer21` added to `Baseline`; `baselineChassis` returns the year-neutral `ScriptedChassis` |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc21 adds the passability terrain ramp, conviction-scaled unit sprites, the empower flash and the expose mark |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc21 scorebug / feed / endcard shell records |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port and `IDGenerator` already carry everything bc21 needs |
| `data/maps/bc21/*.json` | **new, committed** | 18 converted maps |
| `data/bc21/ec_passive.json` | **new, committed** | `ceil(0.2f·√t)` for `t ∈ [1, 1500]` |
| `data/bc21/embezzle.json` | **new, committed** | `floor(x·(1/50 + 0.03f·e^(−0.001f·x)))` for `x ∈ [1, 4096]`, plus the derived `slandererBreakpoints` |
| `data/atlas_bc21.png` / `.json` | **new, committed** | the 2021 sprite atlas |
| `tools/convert_maps_bc21.py` | **new** | reads `.map21` and writes `data/maps/bc21/<name>.json` |
| `tools/map_pools_bc21.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc21.py` | **new** | cuts `atlas_bc21.*` from the 2021 client sprites |
| `tools/gen_year_constants.py` | **`--year bc21` added** | reads the 2021 `GameConstants.java` + `RobotType.java` |
| `tools/JavaBc21Tables.java` | **new, CI-only** | regenerates `data/bc21/ec_passive.json` and `data/bc21/embezzle.json` under the CI JDK |
| `tools/oracle/bc21/Bc21Trace.java` | **new, CI-only** | the trace driver (§Tests) |
| `tools/oracle/bc21/jsi-shim/**` | **new, CI-only** | four files that stand in for a dead Maven artifact (§Tests) |
| `tools/oracle/bc21/examplefuncsplayer21/RobotPlayer.java` + `determinism.patch` | **new, CI-only** | the deterministic oracle bot |
| `tools/oracle/bc21/deps.lock` | **new, CI-only** | the eleven Maven Central coordinates + sha256 the oracle downloads |
| `tools/parity_trace_bc21.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_ledger_bc21.json` | **new** | the accepted-divergence ledger that makes Tier C blocking (§Tests) |
| `tools/gen_bc21_fixture_replay.nim` + `tests/fixtures/replay-bc21.json` | **new, committed** | the fixture replay the wasm smoke loads |

**`ScriptedChassis`, and why the year boundary needs it.** `dispatch.chassisForYear` currently
returns `array[2, rules20.ChassisKind]` — a bc20 type leaking through the year-neutral layer. It is
replaced by a closed year-neutral enum in `sim_types.nim`:
`scAwu, scScaffold, scBowlOfChowder, scExamplefuncsplayer, scCaliforniaRoll, scExamplefuncsplayer21`.
Each year's `newSides` maps it into its own kind and falls back to **that year's strong chassis** for
a name belonging to another year. This is the minimum change that lets a third year exist; no bc20
or bc26 semantics move.

### Determinism

- **`rng.nim` is reused unchanged.** bc21 needs `java.util.Random` in exactly two places, both
  already covered by the existing port: `IDGenerator(mapSeed)` (48-bit LCG, `nextInt(bound)` with
  both the power-of-two shortcut and the rejection loop, 4096-id blocks from 10000, Fisher–Yates per
  block) and the CI oracle bot's per-robot `Random(rc.getID())` stream (`nextDouble`). Robot ids
  therefore match the Java engine's for a given map seed, which is what makes the parity trace
  comparable row for row.
- **The world RNG** is seeded from the map's own `randomSeed` field, exactly as the engine does. The
  episode seed selects maps and side assignment, never the world RNG.
- **`setWinnerArbitrary`'s `Math.random()`** is replaced by a draw from the world RNG (a documented
  divergence; reachable only when votes, Center counts and total influence are all tied at round
  1500).
- **The end-of-round sweep order.** The engine sweeps `objectInfo.eachRobot`, which is
  `TIntObjectHashMap.forEachValue` — hash order, and not reproducible outside the JVM. **The port
  sweeps in ascending robot id**, and this is a *provable* non-divergence, not a hope: the sweep does
  exactly four things, and each is order-independent. (a) `resetBid` refunds a robot's own held
  influence. (b) Top-bidder selection is a maximum under the total order (bid desc, `roundsAlive`
  asc, id asc) — the engine's update predicate is exactly that maximum, so the winner does not
  depend on visit order. (c) Passive influence is an addition into a parent's counter — commutative,
  **except** at the `ROBOT_INFLUENCE_LIMIT = 10⁸` clamp. (d) Camouflage depends only on the robot's
  own `roundsAlive`. Item (c) is the only exposure, and `tests/test_bc21_economy.nim` asserts the
  clamp is never reached in any test or gate game, while `rules.nim` raises a `fault` if it ever is.
  This reasoning is written into `docs/RULES-BC21.md` §Divergences item 4.
- **The empower scan order is load-bearing and is ported literally**: `x` ascending outer, `y`
  ascending inner, over `[max(cx − ceil(√r²) − 1, 0) … min(cx + ceil(√r²) + 1, w − 1)]` and the same
  in `y`, keeping tiles with `dx² + dy² ≤ r²`. It fixes the order conversions are queued and
  therefore the ids they are re-spawned with.
- **All conviction/influence arithmetic is integer**; all cooldown, empower-split and buff arithmetic
  is **IEEE-754 `float64`** with only `+ − × ÷` and `(int)` truncation, which Nim and Java specify
  identically on both x86-64 and wasm32. The scoring shares narrow through **float32**, as above.
- **The only transcendental in the round loop is `Math.exp`, in the slanderer embezzle formula.**
  `Math.sqrt` (the Center passive) is exactly rounded by IEEE-754 and needs nothing; `Math.exp` is a
  HotSpot intrinsic and is *allowed* to differ from the reference by 1 ulp. Three mechanisms, in
  order: (1) `src/battlecode/fdlibm.nim` implements the reference `exp` bit-for-bit, so native and
  wasm always agree with each other; (2) `data/bc21/embezzle.json` commits the resulting integer
  income for **every** `x ∈ [1, 4096]` — the whole range any real doctrine builds in — and the sim
  reads the table there, so the hot path is a lookup; (3) the `parity-oracle-bc21` job regenerates
  that table under the CI JDK 8 and **byte-diffs it**, and additionally compares Java against Nim
  for a log-spaced sample of 4 096 values in `(4096, 10⁸]`. Any `x` where they differ is a
  divergence with a name and a number and goes straight into `docs/PARITY.md`; if such an `x` is
  ever inside `[1, 4096]`, the committed table already pins the JDK's answer and the sim is right by
  construction. The exponent is computed the way Java computes it — `−0.001f × x` in **float32**,
  widened to `double` for `exp`, then `0.03f × result` in `double` — which is not an accident of
  transcription but the reason the generated `slandererBreakpoints` table reproduces California
  Roll's shipped constants exactly.
- Every round appends to a **hash chain**; the viewer re-derives each round and compares, exposing
  `bc_mismatch_round`. The values folded into the bc21 chain each round: per team — votes,
  `numBuffs`, Centers owned, total influence over living non-neutral robots, living politicians,
  living slanderers, living muckrakers, and units built this game; plus globally — the round number,
  the total robot count, and the highest live robot id.
- Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
  (`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
  scar — and the record→re-derive test covers **every** bc21 end reason, not just `complete`.
- **`GameVersion` bumps to `GV06`** in the same commit, with a prepend-only changelog line ("bc21
  year module added; bc26 and bc20 semantics unchanged").
  **`ReplayCompatibleGameVersions` becomes `["GV04", "GV05", GV06]`** — it is *extended*, never
  reset: nothing a GV04 or GV05 recording carries changed meaning, so every hosted bc26 and bc20
  replay keeps rendering. `tools/ci/check_gameversion.sh` is kept and claims the version across
  branches, not just against `main`.

### The chassis, and the bytecode divergence

The engine's per-robot **bytecode limit** (`RobotType.bytecodeLimit`: Enlightenment Center 20 000,
politician 15 000, muckraker 15 000, slanderer 7 500) has no meaning outside the JVM instrumenter. It
is replaced by a **fixed per-robot `DecisionOps` budget at one tenth of the Java limit**:
Enlightenment Center **2 000**; politician **1 500**; muckraker **1 500**; slanderer **750**. One
credit is charged for each: tile sensed, tile detected, robot examined in a sense or detect sweep,
BFS node expanded, direction evaluated, flag read, and empower radius scored. Credits are deducted
inside `pathing.nim` / `kit.nim` and **enforced by the sim, not by the bot**. When the budget reaches
zero the robot's turn ends where it stands — it is **not** resumed mid-computation next turn, which
is the one place this differs from the JVM.

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to Java
bytecode granularity would require either a Nim-level instrumenter (a compiler project) or
hand-annotating every statement against `MethodCosts.txt`, and neither buys anything the budget does
not — the chassis are ours and are written to fit the budget, and the oracle runs the one bot that
provably never approaches the Java limit. That "provably" is a **CI assertion, not an assumption**:
the parity job's trace carries each Java robot's `getBytecodesUsed()` and **fails if any robot on any
traced game exceeds 80 % of its limit**, because a Java robot cut off mid-turn would behave
differently from the Nim port and the divergence would look like a rules bug.

### Maps

**18 of the 76 official maps** are converted and committed. Sizes, seeds, passability and
Enlightenment-Center placements below were read out of the real `.map21` flatbuffers, not assumed.
`sym` is **detected** by the converter (the 2021 `.map21` schema has no symmetry field and the 2021
engine never uses symmetry for anything), by testing the transforms in the order **`vertical`
(flip x), `horizontal` (flip y), `rotational` (both)** against passability and Center placement and
recording **all** that hold; the first is used for display and the map card, and the full list is
recorded.

| pool | map | size | seed | symmetry | own Centers / side | neutral Centers (influence) | min Center separation |
|---|---|---|---|---|---|---|---|
| `small` | `maptestsmall` | 32×32 | 30 | vertical | 1 | — | 21 |
| `small` | `Arena` | 32×32 | 276514 | rotational | 1 | 6 (70, 70, 500×4) | 38 |
| `small` | `Bog` | 32×32 | 238084 | rotational | 1 | 4 (70, 70, 90, 90) | 31 |
| `small` | `FrogOrBath` | 32×32 | 97 | vertical | 2 | 4 (150×4) | 7 |
| `small` | `Smile` | 32×32 | 644 | vertical | 1 | 2 (150, 150) | 25 |
| `small` | `Star` | 35×35 | 276 | vertical | 1 | 4 (150×4) | 20 |
| `mixed` | the six above, plus: | | | | | | |
| `mixed` | `Corridor` | 33×40 | 504317 | vertical + horizontal + rotational | 1 | 6 (100, 100, 500×4) | 35 |
| `mixed` | `SeaFloor` | 45×32 | 314512 | vertical | 1 | 6 (50, 50, 147, 147, 500, 500) | 30 |
| `mixed` | `quadrants` | 40×40 | 215957 | rotational | 2 | 2 (500, 500) | 24 |
| `mixed` | `Maze` | 45×45 | 886488 | rotational | 2 | 4 (500×4) | 40 |
| `mixed` | `Hourglass` | 48×48 | 692611 | vertical | 1 | 4 (500×4) | 25 |
| `mixed` | `PaperWindmill` | 48×48 | 417 | rotational | 2 | 6 (150×4, 400, 400) | 21 |
| `large` (reserved) | `Blotches` | 64×32 | 21 | rotational | 2 | 2 (324, 324) | 15 |
| `large` | `Circles` | 64×32 | 47 | rotational | 2 | 2 (373, 373) | 19 |
| `large` | `BadSnowflake` | 50×50 | 299876 | rotational | 2 | 4 (100×4) | 10 |
| `large` | `AmidstWe` | 64×64 | 475369 | rotational | 1 | 4 (50, 50, 200, 200) | 3 |
| `large` | `Yoda` | 64×64 | 309048 | rotational | 2 | 4 (120, 120, 150, 150) | 29 |
| `large` | `Gridlock` | 64×64 | 535715 | vertical | 1 | 6 (150, 150, 200, 200, 250, 250) | 59 |

`mixed` (12 maps) is the `bc21` variant's pool; `small` (6) is the pool the parity oracle and the
docker smoke run on; `large` (6) is reserved for a later variant. Note that `Hourglass` and `Maze`
are also bc20 map names — different maps, different years, different directories
(`data/maps/bc21/` vs `data/maps/bc20/`); `tests/test_bc21_maps.nim` asserts the two are not
confusable.

**Two maps are excluded on purpose**, and the reasons go in `docs/RULES-BC21.md`:

- **`Cow`** — 80×50, which violates the spec's own `MAP_MAX_WIDTH/HEIGHT = 64`, and which patch
  2021.2.4.0 explicitly removed from scrimmages ("Exclude map Cow from scrimmages as it is too
  large").
- **`Misdirection`** — 50×50, but **two of its 2 500 tiles have passability exactly 0.0**. The
  engine computes `actionCooldown / passability`, so a robot that steps onto one of those tiles takes
  an *infinite* cooldown and is frozen for the rest of the game. That is legal, it is reproduced by
  the port (`tests/test_bc21_cooldown.nim` asserts the infinite-cooldown behaviour on a synthetic
  map), and it is not a map anyone should be scored on.

The remaining 56 maps are simply not converted in v1; the converter handles any `.map21`.

`tools/convert_maps_bc21.py` writes `data/maps/bc21/<name>.json` carrying: `name`, `width`,
`height`, `origin` (the map's own `minCorner`, recorded for provenance and inert in the sim, which
works in 0-based coordinates), `random_seed`, `symmetry` (the chosen one) and `symmetries` (all that
hold), `passability` (the `width × height` `double` array, serialised as 17-significant-digit
decimals so the reader round-trips the exact bits), and `initial_bodies` (`id`, `team` ∈
`{neutral, a, b}`, `type`, `x`, `y`, `influence`). The converted maps are **committed** and CI
re-converts and diffs. The wasm bundle gets the same directory through the existing
`--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from
the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot
takes side A in game 1; sides alternate each game. Seed, map names and side assignment are recorded
in results and in the replay.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `fdlibm`, `sheet_common`,
`sheet`, `decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never
branches on the year except through `years/dispatch.nim`, whose `Session` is a Nim object **variant**
so the compiler refuses to build a half-added year. Adding 2021 is what the bc26 note promised adding
a year would be: a new `years/bc21/` directory, a converted map set, a sprite atlas, one registry
line, one arm per dispatch `case`, and one manifest variant. The replay header records `year` so a
viewer can never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol
id would force every existing bc26/bc20 consumer to re-register for no change in the contract. Both
`game.protocols.player` and `game.protocols.global` continue to point at `docs/PROTOCOL.md`, which
gains a bc21 section.

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
one is refused (commit `d581704`). A seat that sets neither env var takes the active year's default
baseline (`california-roll` on bc21). A seat whose registration never arrives is logged loudly and
reported to `COGAME_PLAYER_FAILURE_URI`.

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no
per-round observation of any kind.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV06","year":"bc21",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":871345,
 "games":[{"map":"PaperWindmill","width":48,"height":48,
           "symmetry":"rotational","symmetries":["rotational"],
           "you_are":"A","rounds":1500,
           "your_centers":[{"x":11,"y":36,"influence":150},{"x":19,"y":29,"influence":150}],
           "enemy_centers":2,
           "neutral_centers":[{"x":24,"y":24,"influence":400},{"x":23,"y":23,"influence":400},
                              {"x":8,"y":8,"influence":150},{"x":39,"y":39,"influence":150},
                              {"x":8,"y":39,"influence":150},{"x":39,"y":8,"influence":150}],
           "center_separation":21,
           "passability":{"min":0.10,"mean":0.806,"swamp_pct":11.4}},
          {"map":"Arena","…":"…","you_are":"B"},
          {"map":"maptestsmall","…":"…","you_are":"A"}],
 "economy":{"center_passive":"ceil(0.2*sqrt(round)) per center per round; 8500 total over 1500 rounds",
            "center_start_influence":150,
            "slanderer_breakpoints":[21,41,63,85,107,130,154,178,203,228,255,282,310,339,368,399,
                                     431,463,497,532,568,605,643,683,724,766,810,855,902,949],
            "slanderer_payments":51,"camouflage_round":300,
            "expose_buff":"+0.001 x slanderer influence, for 50 rounds",
            "empower_tax":10,"votes_on_offer":1500,"losing_bid_cost":"ceil(bid/2)"},
 "rules_digest":"<~6 KB condensed spec: the four types and their radii, cooldown/passability, build and conviction, empower with the buff and conversion rules, expose, embezzle and camouflage, the auction and the half-bid, flags, the end ladder>",
 "sheet_schema":{"…all ten knobs, their values, ranges and defaults…"},
 "scoring":{"weights":{"survival":40,"vote_share":35,"center_share":15,"influence_share":10},
            "win_bonus_per_game":100,"games":3,
            "note":"shares are float32; points truncate to an integer"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with the seat's **own**
Center positions and every neutral Center's position and influence, the seed, the economy tables, the
full knob surface with defaults, the scoring weights, the deadlines. Because every map is symmetric,
the two seats' cards are mirror images of each other and numerically identical in every aggregate;
the only asymmetry is `you_are` and which of the two mirrored coordinate sets is labelled "yours".
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in
either direction, at any time); the opponent's real player name (only the alias); every in-match
state (a cog receives **no** per-round observation — one sealed doctrine, then the campaign); the
other seat's fallback status. The only cross-team channel inside a match is what a robot can sense
and the flags it can read.

### Reply schema and caps

```json
{"sheet":{"opening":"muck_spam","slanderer_ratio":10,"muck_ratio":70,
          "politician_size_curve":"cheap","bid_policy":"fixed",
          "expansion":"neutral_centers_first","flank_policy":"flank_wide",
          "empower_threshold":20,"convert_over_kill":false,
          "eco_exponential_round":250},
 "notes":"Kill their slanderers before round 200; buff-mucks carry the politicians in.",
 "motto":"No lies survive daylight."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES**, cut on a rune boundary | unparseable → retry once → fallback sheet |
| `sheet` | ≤ **32** keys, each value type- and range-checked | bad field → that field's default, recorded |
| `notes` | **280 runes** | truncated |
| `motto` | **48 runes** | truncated |
| unknown sheet keys recorded | ≤ **16** keys, each ≤ **40 runes** | truncated |
| provider error text stored in the replay | **200 runes** | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary**
(`truncateRunes`/`truncateBytes` in `sim_types.nim`; the reply's 16 KB cap is measured in bytes but
still cut on a rune boundary — commit `a8684c0`): byte-slicing a multi-byte character renders fine in
a browser and then fails a strict UTF-8 parser, which is exactly what makes a replay unreadable to
everything but one lenient viewer.

### Results document

The closed schema is **shared with bc26 and bc20** and stays that way: `results.games[]`'s five
required keys are year-neutral (`map`, `side`, `rounds_played`, `winner`, `end_reason`), every
year-specific statistic is an optional property, and `end_reason`'s enum is the union of every year's
values. bc21 reuses `units_built` and `units_alive`, which already exist with the same meaning and
type, and adds the rest.

bc21's per-game keys, each a 2-array of integers in **seat** order unless marked scalar:
`centers_owned`, `centers_captured`, `centers_lost`, `neutrals_captured`, `votes`, `bids_placed`,
`bid_influence_spent`, `top_bid`, `influence_spent`, `influence_end`, `income_end`, `units_built`,
`politicians_built`, `slanderers_built`, `muckrakers_built`, `units_alive`, `politicians_alive`,
`slanderers_alive`, `muckrakers_alive`, `empowers`, `empower_conviction`, `conversions`, `exposes`,
`buff_peak`, `camouflaged`, `robots_lost`; scalars `votes_tied` (rounds in which both teams' top bids
were equal and nobody won) and `rounds_no_bid`.

Top level, unchanged: `names`, `aliases`, `scores`, `wins`, `points`, `games`, `seed`, `year`,
`policy_kind`, `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`,
`wall_clock_seconds`, `game_version`.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV06","year":"bc21",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"california-roll",
           "sheet":{…as applied…},"sheet_submitted":"{…as received…}",
           "sheet_defaults_applied":["muck_ratio"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":8123,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"PaperWindmill","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":1500,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…],"side_a_slots":[…],"abandon_after":[…],"max_rounds":1500},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships), both doctrine sheets, the chassis each
seat drove, and the event list are all in the file, and the wasm sim replays every round from them.
**No `.bc21` bytes, no per-round state dump, no flag dump** — flags are a pure function of the sim,
so the browser re-derives them and the endcard reads the re-derived traffic. No server is contacted
except S3 for the `.replay` file. The per-round hash chain lets the viewer prove its re-derivation
matches the recording (`bc_mismatch_round`, surfaced as `data-replay-mismatch-round` and in
`#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`. **Every event kind here is
bounded per game** — a 1500-round match with hundreds of robots cannot be allowed to emit an event
per empower — and every one has CSS (§Viewer).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides` | 1/game | `game` | beat + feed |
| `first_build` | `game`, `round`, `alias`, `unit` (`politician`\|`slanderer`\|`muckraker`) | 6/game | `build` | beat + feed |
| `center_taken` | `game`, `round`, `alias`, `from` (`neutral`\|`opponent`), `x`, `y`, `influence`, `by_conviction` | ≤ 24/game | `capture` | beat + feed ("Clan Ash takes the 400-influence centre at 24,24") |
| `vote_lead` | `game`, `round`, `alias`, `votes`, `opponent_votes` | emitted only when the vote **lead changes hands**; hard cap 40/game | `votes` | beat + feed |
| `bid_spike` | `game`, `round`, `alias`, `bid`, `influence_before` | the largest bid in each 100-round window per team: ≤ 30/game | `bid` | beat + feed |
| `expose_wave` | `game`, `round`, `alias`, `exposed_total`, `buff_pct` | each time a team's buff crosses a 5 % step: ≤ 20/game | `expose` | beat + feed |
| `empower_big` | `game`, `round`, `alias`, `conviction`, `victims`, `converted` | an empower that converts a Center or removes ≥ 200 enemy conviction; hard cap 40/game, the overflow counted in `results` | `empower` | beat + feed |
| `annihilated` | `game`, `round`, `alias` (the wiped clan) | ≤ 1/game | `wipe` | **chapter marker** |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points`, `votes` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

The whole event list for a three-game match is at most a few hundred entries, and
`tests/test_bc21_replay.nim` asserts each per-kind bound so a pathological game cannot produce a
20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc21/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.bc21` bytes, no 2021 TypeScript
client.

### All four viewer files come from ONE starter: `cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` → `cogame-battlecode` → here.
All four bundle files come from **that one starter** — never a mixture, because splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an
`onRuntimeInitialized` bootstrap) deadlocks the viewer silently (cogame-lantern, 2026-08-23).

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc21/`, `data/bc21/*.json` and `data/atlas_bc21.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. The only edit is that `static_replay.js` also writes `document.documentElement.dataset.year = 'bc21'` when the header says so, the same one-line switch bc20 added. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc21 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and no existing id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and byte-for-byte: **`client/chrome_common.js`** and **`client/broadcast_core.js`**
(their sha256 is asserted against the coworld-ctf copies in `tests/test_viewer.nim`, and that
assertion stays green because neither file is touched — the killfeed fix below is in
`client/replay_broadcast.html`, which is this repo's own page, and `grep -c killfeed
client/chrome_common.js` finds only two comment mentions). `wire_constants.js` is regenerated from
the sim by `tools/gen_wire_constants.nim`, as today.

### The appended bc21 game block

**No starter element is removed.** The bc26 block's elements (`#coopchip`, `#bars`, `#gamechips`,
`#econ`, `#doctrines`) and the bc20 block's (`#bc20-flood`, `#bc20-soup`, `#bc20-units`,
`#bc20-doctrines`, `#bc20-chain`) stay exactly where they are; the bc21 block adds its own, with ids
that are all new and all prefixed:

- `#bc21-votes` — the election readout, in the same top-centre pill slot bc20 uses for its flood
  gauge: `ASH 412 — 388 BASIL`, a proportional two-colour bar, and `751 to clinch`. It flashes when
  the lead changes.
- `#bc21-influence` — per clan: total Center influence, income per round, and Centers owned as
  `3 / 8` (own / on the map).
- `#bc21-units` — per clan: politicians / slanderers / muckrakers alive, and the live speech buff as
  `×1.043`.
- `#bc21-doctrines` — both sheets in plain words, **dismissible** (D3): a `#bc21-doctrines-close`
  button with `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first
  playback advance (or after six seconds for a viewer who never presses play), and a
  `#bc21-doctrines-toggle` chip in the scorebug that re-opens it. Its body is capped and scrolls. It
  sits above the board area and **never** inside the transport band.
- `#bc21-bids` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: `static_replay.js` sets
`document.documentElement.dataset.year` from the replay header, and the stylesheet extends the
existing `html:not([data-year="bc20"]) #bc20-…` pattern with `html:not([data-year="bc21"]) #bc21-…`.

### The known open defect, and its fix (in scope for this version bump)

**The bug (bc20 judge, advisory).** `#killfeed` is positioned `bottom: calc(76 * var(--u)); right:
calc(12 * var(--u))` at `z-index: 11` (`client/replay_broadcast.html:1255`), while the year stat
boxes sit at `right: 8px; bottom: calc(var(--band) + 8px)` and `calc(var(--band) + 74px)` at
`z-index: 5` (`#bc20-soup`, `#bc20-units`, same file). `--u` scales with the board, so at FIT zoom
the killfeed's 76·`--u` offset falls **below** the boxes' fixed 74 px + band offset, and the feed —
being eight z-levels higher — overdraws them. The narrow-width block at line 2757 only nudges
`#bc20-units`, which is why it survived review.

**The fix, one rule and one measurement, applied to the shared chrome so it fixes bc20 and bc26 too:**

1. `relayout()` (`client/replay_broadcast.html:3541`) gains a fourth `:root` variable,
   `--statrail`: inside the same fixed-point loop it measures the union of the bounding boxes of the
   **visible** year stat boxes for the current `data-year`
   (`#econ`, `#bc20-soup`, `#bc20-units`, `#bc21-influence`, `#bc21-units`) and sets `--statrail` to
   that union's height in px, or `0px` when the stack is empty.
2. `#killfeed`'s `bottom` becomes
   `max(calc(76 * var(--u)), calc(var(--band, 0px) + var(--statrail, 0px) + 8px))`.

Nothing else about the killfeed changes: same right anchor, same width, same `column-reverse`, same
`pointer-events: none`. `tests/test_viewer.nim` gains a static assertion that the rule uses
`--statrail`, and `tools/ci/viewer_smoke.mjs` gains an overlap gate — at 360 px, 720 px and 1280 px
and at both FIT and 2× zoom, `#killfeed`'s client rect must not intersect any visible stat box's
client rect, **on all three years' replays**. That last clause is the point: the fix is verified on
bc26 and bc20 as well as bc21, so it is a repair of the shared chrome rather than a bc21 workaround.

### Zoom: KEEP `#viewpanel`

The bc21 variant's pool tops out at 48×48 and the reserved large pool at 64×64. The native board
render is 16 px per tile, so 768–1024 px wide — **larger than the 360 px featured-match frame**, where
a 48×48 board would give 7.5 px per tile. So the inherited `#viewpanel` (zoom bar + minimap, with
`?viewpanel=0` still honoured for thumbnail capture) is **kept**, wired to the same
`zoomAt/setZoom/panBy/panTo/resetView` core API the worker already forwards. The default view is
fit-to-board, so a spectator who touches nothing sees the whole map and both capitals.

### Transport rules

- `relayout()` (inherited, kept, extended only with `--statrail`) sets **`--hudscale`**,
  **`--topband`** and **`--band`** on `:root`, iterating to a fixed point so a map-aspect change
  cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport). `#bc21-doctrines`, `#bc21-influence`, `#bc21-units` and
  `#bc21-bids` are all explicitly positioned above `var(--band)`.
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`
  ("CENTRE TAKEN — Clan Ash, game 2, round 612"), built by a bc21-block function with its **own**
  name, `buildBc21BeatButtons` — never `markBeat` (the tandem 2026-08-23 hoisting collision) and
  never colliding with `buildBeatButtons` (bc26) or `buildBc20BeatButtons` (bc20). CSS exists for
  **every kind emitted**: `.beat-marker.doctrine`, `.game`, `.build`, `.capture`, `.votes`, `.bid`,
  `.expose`, `.empower`, `.wipe`, `.end`.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`
  (already relabelled **+25**), `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`,
  `#tick-clock`, `#win-chip`, `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Load signalling

`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on the
**first drawn frame** (the worker's `loaded` message after the first board frame is composited —
never on rAF timing at the call site, the chorus 2026-08-24 scar), and the `coworld-replay` bridge
posts `ready` from a callback fired **after** that attribute is set. On any failure — fetch, JSON
parse, an unknown `game_version`, a wasm abort, or a hash mismatch that prevents rendering — it sets
`data-replay-error="<message>"` on `<html>` and shows the failure card. Unchanged from the starter,
restated because it is a checklist item.

### Art

`data/atlas_bc21.png` + `data/atlas_bc21.json` (≈ 200 KB, committed), cut by
`tools/build_sprite_atlas_bc21.py` from the official 2021 client's sprite tree
(`battlecode21/client/visualizer/src/static/img/` at the pinned commit; `client/LICENSE` is
**AGPL-3.0**, the same licence this repository carries). Verified present and used:
`robots/center{,_red,_blue}.png`, `robots/polit{,_red,_blue}.png`,
`robots/slanderer{,_red,_blue}.png`, `robots/muck{,_red,_blue}.png`,
`tiles/{DirtTerrain,RawDirtTerrain,SwampTerrain,RawSwampTerrain,terrain}.png`,
`effects/empower/polit_empower_{red,blue,empty}_{1,2}.png`,
`effects/expose/expose_{red,blue,empty,empty_small}.png`,
`effects/camouflage/camo_{red,blue}.png`,
`effects/embezzle/slanderer_embezzle_{red,blue,empty}_{1,2}.png`, `effects/death/death_empty.png`.
Credited in `NOTICE`. Palette follows the engine side, not the seat: **red = side A, blue = side B**,
and because sides alternate each game the scorebug plate keeps the *alias* constant and recolours its
swatch per game. It looks like Battlecode 2021 because it **is** Battlecode 2021's art.

Board rendering (`render.nim`): each tile is drawn from the swamp↔dirt terrain pair, interpolated by
its passability (0.1 = deep swamp, 1.0 = clean dirt), so the map's real terrain is legible at a
glance and a spectator can see why a flank is slow. Units are drawn at a size scaled by
`conviction / convictionCap` — the client's own 2021.3.0.3 convention, credited — so a fat politician
reads as fat. Enlightenment Centers draw their influence as a number and their team as the sprite
colour; a neutral Center uses `center.png`. An empower draws the `polit_empower` flash at its chosen
radius for two frames; an expose draws the `expose` mark; a camouflage draws `camo`; a slanderer
paying its parent draws the small `embezzle` tick. **Slanderers are drawn as slanderers**: the fog
belongs to the robots, not to the spectator, and hiding them would make the whole muckraker story
invisible.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else, and the `#bc21-*` boxes dropping
their word labels to glyphs under 640 px).

- `#scorebug`: both clan plates — `CLAN ASH` over the real player name (`daveey`) and the motto — the
  live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 612 / 1500`, `game 2 of 3 — PaperWindmill`.
- `#bc21-votes`, `#bc21-influence`, `#bc21-units` as above.
- `#board`: the terrain ramp, all four robot types in both colours, conviction-scaled sprites, Center
  influence numbers, and the empower / expose / camouflage / embezzle effects.
- `#bc21-doctrines`: each sheet in plain words ("spams muckrakers", "70 % of spend on muckrakers",
  "cheap politicians", "flanks wide", "empowers on contact", "stops compounding at round 250"), plus
  the capped `notes` and a fallback badge when a seat's doctrine came from the fallback sheet.
  Dismissible.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and
  now provably clear of the stat boxes.
- `#endcard`: winner alias **and** real name; the win condition in plain words ("Clan Basil won the
  election 794 votes to 706" / "Clan Ash wiped Clan Basil off the map at round 883" / "votes tied
  750–750 — Clan Ash held 5 Enlightenment Centers to 3"); the per-game score line; the economic story
  (influence earned and spent, slanderers built and exposed, politicians built, Centers taken and
  lost, biggest empower per clan); and `#bc21-bids`, the **auction panel**: per clan, votes won, bids
  placed, influence burned on losing bids, the biggest single bid and the round it bought, and the
  number of rounds the auction tied and nobody voted. Nothing about flags or bids is stored in the
  replay: the wasm sim re-derives every round.

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`,
  `player` → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar). One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe (nimby 0.1.26, Nim 2.2.4) builds
  `/bin/battlecode` and `/bin/battlecode-player` from one image and copies `data/` (now carrying
  `maps/bc21/`, `bc21/*.json` and `atlas_bc21.*`). **No JDK, no JRE, no Java, no node in any runtime
  stage** — the 2021 engine's toolchain exists only in the `parity-oracle-bc21` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc21 game block along
  with the bc26 and bc20 ones.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc21` is 2021 'Campaign' — Enlightenment
    Centers bid influence for votes and spend it on politicians, slanderers and muckrakers, and the
    election is decided at round 1500."*
  - `tags` unchanged (already ≥ 3).
  - `game.config_schema`: `year.enum` becomes `["bc26", "bc20", "bc21"]`. `pool.enum` unchanged
    (`small` / `mixed` / `large`; each year owns its own pool table). `maxRounds` keeps
    `minimum 50, maximum 2000` (bc21's 1500 fits). `gamesPerMatch` keeps `maximum 3`.
    `perGameBudgetSeconds` keeps `maximum 300` (bc21 uses 110) and `matchBudgetSeconds`
    `maximum 600` (bc21 uses 340). Every array keeps `minItems`/`maxItems`; no runner-managed
    `tokens` inside any `game_config`.
  - `game.results_schema`: bc21's optional properties added beside bc26's and bc20's;
    `games.items.required` unchanged (the five year-neutral keys); `end_reason`'s enum extended with
    `annihilated`, `more_votes`, `more_enlightenment_centers`, `more_influence` (`coin_flip` and
    `abandoned` are already there).
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":".../blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one
    entry and keeps the four it has: `rules.md` (→ `docs/RULES.md`), `rules-bc20.md` (→
    `docs/RULES-BC20.md`), **`rules-bc21.md`** (Battlecode 2021 "Campaign": rules, knobs and
    divergences → `docs/RULES-BC21.md`), `replay.md` (→ `docs/REPLAY.md`), `parity.md` (→
    `docs/PARITY.md`, which gains a bc21 section).
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly
    `[awu, scaffold]`, the two ids `certification.players` seats; only their `description` strings
    are extended to name the bc21 resolution ("…, California Roll on bc21" / "…, examplefuncsplayer21
    on bc21"). This is the pin the bc20 run learned the hard way: the certifier requires
    `len(certification.players) == num_agents` **and** every declared `player[]` entry to occupy a
    cert slot, so a bc21-specific player id would fail the release dispatch. The bc21 scripted seats
    are reached through `PLAYER_SCRIPTED` per-year resolution (§Decisions) and through
    `tools/ci/policies.json`, never through `player[]`.

  **Variants — one per Battlecode year:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | unchanged | **2** |
  | `bc21` | Battlecode 2021 — Campaign (2 seats) | `year: "bc21"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 1500`, `num_agents: 2`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 110`, `matchBudgetSeconds: 340`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `bc21`'s variant description: *"Best of three on the mixed pool. Every round auctions one citizen's
  vote; influence buys units, buys votes, and is what an enemy politician takes when it converts your
  Enlightenment Center. Turtle and print money, spam muckrakers and kill the money, or take the
  neutral Centers first — 1500 rounds decide it."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false`).

  **Certification fixture — UNCHANGED, and stays on bc26.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, `"num_agents": 2` and its existing fast settings. There is **no bc21
  certification fixture in v1** (§Out of scope): certification is the platform's contract check, it
  already passes on bc26, and re-pointing it at a brand-new year module would put the release at the
  mercy of the newest code for no gain. bc21 is proven instead by its own `docker-smoke` episode
  (§Tests), which produces a real bc21 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  **`0.2.0 → 0.3.0`** — because it adds a variant and adds optional results properties without
  changing any existing behaviour. The release is dispatched through the existing
  `coworld-release.yml` with the same step order (build → certify → upload-policies → upload-coworld
  → secret put). **Certify runs against bc26, exactly as before**, and `release-result.json` must
  still show `canonical: true` and `certify.replay_liveness` containing
  `skipped (static replay bundle declared`.

- **`tools/ci/policies.json`** gains the bc21 set beside the bc26 and bc20 sets (a scripted champion
  is a failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-bc21-turtle","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"turtle"}},
   {"name":"battlecode-bc21-muckrush","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"muckrush"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-california-roll","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"california-roll","PLAYER_POLICY_LABEL":"california-roll"}},
   {"name":"battlecode-examplefuncsplayer21","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer21","PLAYER_POLICY_LABEL":"examplefuncsplayer21"}}]
  ```
  Champion #2 is uploaded while `daveey-1` is the active player. LLM credentials reach the **game**
  container through the manifest env; the player pods need no Bedrock sidecar in this lineage.

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **third league**, created beside the bc26 and bc20 ones and touching neither them nor the game's
default league:

| field | value |
|---|---|
| `league_key` | `bc21` |
| `league_name` | `Battlecode 2021 — Campaign` |
| `default_variant_id` | `bc21` |
| `short_name` | `bc21` → `softmax.com/battlecode/bc21` |
| champions (LLM) | `battlecode-bc21-turtle` (owned by **daveey**), `battlecode-bc21-muckrush` (owned by **daveey-1**) — deliberately the season's two poles, a slanderer-turtle/eco doctrine against a muckraker rush |
| fillers (scripted) | `battlecode-california-roll`, `battlecode-examplefuncsplayer21` |
| credits | its own pool (grant + drip) |

Fillers are set **before** the first `trigger-round`. **Never touch the `bc26` league, the `bc20`
league, or the game's default league.**

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged
by the repository itself. bc21 is cleaner than bc20 here: every upstream this year touches is
already AGPL-3.0. `NOTICE` gains four sections and one non-section:

- **`battlecode/battlecode21` — AGPL-3.0** (verified: `engine/COPYING`, `client/LICENSE` and
  `schema/LICENSE` are each the GNU AGPL v3; the repository root carries no separate licence).
  Pinned commit `ed39c1a49574db57e5463d720736220506280294`, release `2021.3.0.5`. The derived files
  are named individually: `src/battlecode/years/bc21/**` (behaviour, hand-ported),
  `years/bc21/constants.nim` (generated from `GameConstants.java` + `RobotType.java`),
  `data/maps/bc21/*.json` (converted from `.map21`), `data/bc21/*.json` (generated from
  `RobotType.getPassiveInfluence`), `data/atlas_bc21.*` (cut from the 2021 client sprites), and
  `years/bc21/chassis/scaffold21.nim` (examplefuncsplayer, ported statement for statement — it is the
  parity oracle's other side and may not gain behaviour). **The engine itself is used only at CI
  time**; no JDK, no JRE and no upstream Java source exists in any image this repository builds.
- **`StoneT2000/Battlecode2021` — AGPL-3.0**, commit `5c2a7ee`. What derives from it:
  `years/bc21/chassis/{croll,ec,politician,muckraker,slanderer,bids,pathing}.nim` — the adaptive bid
  ladder, the neutral-Center scoring function, the slanderer-influence breakpoint discipline, the
  build-ratio caps keyed to distance from the nearest enemy Center, and "muck flanking". **Behaviour,
  not code**, rewritten in Nim and parameterised by this coworld's doctrine sheet.
- **`iliao2345/Battlecode2021` — AGPL-3.0**, commit `d620569`. What derives from it: the
  `opening: muck_spam` build order and the muckraker scouting fan-out in `ec.nim` and
  `muckraker.nim`, from `src/muckspam/` and `src/membrane3/`.
- **`BSreenivas0713/Battlecode2021` — AGPL-3.0**, commit `d24af14`. What derives from it: the
  multi-Center flag protocol and role vocabulary in `flags.nim`, from `src/musketeerplayerfinal/`.
- **`IvanGeffner/battlecode2021` — NO LICENCE, all rights reserved** (verified: the repository
  declares no licence anywhere). It is **not vendored, not ported, not compiled and not read into any
  file here**. Neither is the 2021 winner, babyducks, which is not published at all; where this note
  names a "babyducks pole" it means the archetype as described in public postmortems, not code.

`docs/RULES-BC21.md` carries the full **§Divergences** list: (1) no bytecode instrumentation — a
fixed `DecisionOps` budget with no mid-turn resumption, plus the CI assertion that no Java robot in a
traced game exceeds 80 % of its limit; (2) `setWinnerArbitrary`'s `Math.random()` replaced by a
world-RNG draw; (3) `Math.exp` in the embezzle formula replaced by an fdlibm port plus a committed
JDK-generated table over `x ∈ [1, 4096]`; (4) the end-of-round sweep in ascending robot id rather
than Java hash order, with the order-independence argument and the `10⁸` clamp assertion;
(5) the spec's stale "3000 rounds" prose superseded by the engine's `GAME_MAX_NUMBER_OF_ROUNDS =
1500` (patch 2021.2.3.0); (6) map origin offsets recorded but inert (the sim is 0-based); (7) no
indicator dots or lines, no profiler, no crossplay, no `.bc21` output; (8) the `deadline` wall-clock
stop, a coworld concept and not an engine one, recorded as one load-bearing record; (9) both chassis
are behaviour ports parameterised by the doctrine sheet; (10) 18 of the 76 official maps converted,
with `Cow` and `Misdirection` excluded for the stated reasons.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, `<SEATS>` = **2**). The sandbox runs none of it; CI is the harness.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc21_cooldown.nim`** — `cooldownAdded = actionCooldown / passability` computed at
   the tile being **left**; `processBeginningOfTurn` decrements by 1 and floors at 0; `isReady` is
   `cooldown < 1` strictly; initial cooldowns 10 / 0 / 10 / 0 by type; a **converted** robot gets
   cooldown 0 while a **built** robot gets `initialCooldown`; a tile of passability 0.0 gives an
   infinite cooldown and freezes the robot for ever.
2. **`tests/test_bc21_build.nim`** — build legality (`1 ≤ influence ≤ EC influence`, adjacent,
   on-map, unoccupied, `isReady`); the influence is deducted before the spawn; spawn conviction is
   `ceil(ratio × C)` with the muckraker's `0.7` producing `ceil` and not `round` (C=1 → 1, C=3 → 3,
   C=10 → 7, C=11 → 8); `convictionCap` equals spawn conviction for units and `10⁸` for Centers; the
   new robot is appended to the exec order and takes **no turn** in the round it was built.
3. **`tests/test_bc21_empower.nim`** — the whole speech, with a vector per branch: the scan order
   (`x` outer ascending, `y` inner ascending) and the ids it produces; `numBots == 0` and
   `conviction ≤ 10` both leave everyone untouched **and still kill the politician**; the split is
   `(conviction − 10) / numBots` including allies and neutrals in the divisor; a friendly Center
   gains **unbuffed** influence; a friendly unit heals, capped at its own `convictionCap`, with the
   excess lost; an enemy/neutral Center takes the buffed-until-conversion, unbuffed-overflow
   formula; a converted politician arrives with `influence = |old influence|` and
   `conviction = −old conviction` capped by its new cap; a converted Center arrives with
   `influence = |old influence|` and conviction snapped equal to it; slanderers and muckrakers are
   destroyed, never converted; every conversion keeps the destroyed robot's **old parent pointer**;
   `(int)` truncation toward zero is asserted on a fractional split.
4. **`tests/test_bc21_expose.nim`** — expose requires `isReady`, `r² ≤ 12`, an enemy `SLANDERER`;
   a camouflaged slanderer (now a politician) cannot be exposed; the buff added is the slanderer's
   **influence**, it takes effect on the **next** round, and it expires at the start of round
   `emit + 51`; overlapping buffs accumulate and expire independently; `buff = 1 + 0.001·n` exactly
   (the 2021.3.0.0 linear form, not `1.001^n`).
5. **`tests/test_bc21_economy.nim`** — `ecPassive(t) = ceil(0.2f·√t)` against the committed table for
   all 1500 rounds, summing to 8 500; the slanderer pays for `roundsAlive ∈ [0, 50]`, i.e.
   **51 payments**, the first of them on its **spawn round** (it has no turn that round but is in the
   end-of-round sweep) — an engine behaviour the spec's "for 50 turns" does not say; income 0
   thereafter; camouflage at exactly `roundsAlive == 300`, keeping id, influence, conviction, cap,
   parent and flag; a slanderer whose parent Center has been converted (and therefore destroyed and
   respawned with a new id) **stops paying**; the generated `slandererBreakpoints` equals
   `[21, 41, 63, 85, 107, 130, …, 949, 999]`; the `10⁸` influence clamp is never reached in any gate
   game and raises `fault` if it is.
6. **`tests/test_bc21_votes.nim`** — the top bidder is the maximum under (bid desc, `roundsAlive`
   asc, id asc), including the case where every Center bid 0; the winner pays in full and the loser
   pays `(bid + 1) / 2`; **equal top bids give the vote to nobody and charge both teams half**; a bid
   is deducted at `bid()` time and refunded at the start of the settlement, so a Center that bids
   cannot spend the same influence on a build that turn; a second `bid()` in the same turn replaces
   the first; neutral Centers never bid.
7. **`tests/test_bc21_endladder.nim`** — annihilation is checked **every** round and outranks the
   vote count; a double wipe in one round awards the win to **B**; `timeLimitReached` is
   `round >= 1500` (so round 1500 **is** played, unlike bc20's off-by-one); the four rungs fire in
   the engine's order with a vector for each; every `end_reason` value is producible.
8. **`tests/test_bc21_sensing.nim`** — sensor/detection radii per type; **politicians and slanderers
   see a slanderer as a politician**, Centers and muckrakers see the truth; the muckraker's detection
   radius (40) exceeds its sensor radius (30) and detection returns locations only; flag reads work
   across teams, at any range for Centers in either direction, and are refused for a robot that no
   longer exists; `0 ≤ flag ≤ 16 777 215` is enforced.
9. **`tests/test_bc21_scoring.nim`** — the points formula with float32 narrowing and truncation, one
   vector per weight; points in `[0, 100]` and the seats summing to ≤ 100; the ordering of
   `results.scores` agrees with the winner on 200 random synthetic finals.
10. **`tests/test_bc21_sheet.nim`** — every one of the ten knobs: absent → default, out of range →
    default + recorded, mistyped → default + recorded; the `slanderer_ratio + muck_ratio > 100`
    renormalisation is exactly `s' = s·100 div (s+m)`, `m' = 100 − s'`; unknown keys recorded (≤ 16,
    ≤ 40 runes); **a submitted `chassis` is recorded as an unknown field and never honoured** (the D1
    assertion, which fails if anyone re-adds the knob); rune-boundary truncation of `notes`/`motto`
    including astral-plane characters; the 16 KB byte cap cut on a rune boundary.
11. **`tests/test_bc21_baselines.nim`** — bounded orders and legality:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the *same* `validate` the
      LLM path uses — every key known, every value in range, `notes`/`motto` under cap;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the
      moment it is emitted**: `cooldownTurns < 1` for actions and *not* checked for bids and flags,
      target on the map / adjacent / in the right radius, `1 ≤ influence ≤ EC influence` on both
      build and bid, spawn tile unoccupied, expose target an enemy slanderer in range, empower radius
      `≤ 9`, flag in range; and **no robot exceeds its `DecisionOps` budget**;
    - (c) `examplefuncsplayer21` **acts** — ≥ 1 unit built, ≥ 1 bid, ≥ 1 move — but is **not**
      required to survive: it is the deliberate weak floor and the oracle's other side, and it may not
      gain behaviour;
    - (d) `california-roll` beats `examplefuncsplayer21` on 3 seeds × 2 `small` maps, 6/6.
12. **`tests/test_bc21_survival.nim`** — the **economic-survival / self-play gate** (the LEARNINGS
    pin), with an inverted control:
    - `california-roll` vs `california-roll`, all-defaults sheet, 3 seeds × 2 `small` maps = 6 games.
      In **≥ 5 of 6** the game must either reach round 1500 or end on `annihilated` **after round
      400** — nothing may die trivially early. In **all 6**, each seat must have built ≥ 40 units,
      spent ≥ 2 000 influence, placed ≥ 100 bids, held ≥ 1 Enlightenment Center at round 400, and the
      two teams together must have won ≥ 900 of the 1 500 votes on offer (a dead auction is a dead
      economy).
    - The same gate is then run against a **known-broken chassis** compiled behind
      `-d:bc21BrokenChassis` (a `croll.nim` variant that stops building after round 50) and **must
      fail**. A gate that cannot fail is not a gate; this assertion is what keeps it honest.
13. **`tests/test_bc21_knobs.nim`** — the knob-teeth gate. Paired seeded games (identical seed, map
    and opponent; the two teams identical except one knob at its low and high setting, 3 seeds each),
    each asserting a named, signed delta. Thresholds live in one table so tuning is a one-line
    change:

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `slanderer_turtle` → `muck_spam` | muckrakers built by round 150 up ≥ 25 **and** influence spent on slanderers by round 150 down ≥ 60 % |
    | `slanderer_ratio` | 0 → 90 | slanderers built up ≥ 15 **and** total passive influence generated up ≥ 800 |
    | `muck_ratio` | 0 → 90 | muckrakers built up ≥ 30 **and** enemy slanderers exposed up ≥ 4 |
    | `politician_size_curve` | `cheap` → `fat` | mean politician influence up ≥ 3× **and** empowers down ≥ 30 % |
    | `bid_policy` | `never` → `escalate_when_ahead` | votes won up ≥ 250 **and** influence spent on bids up ≥ 2 000 |
    | `expansion` | `defend_home` → `neutral_centers_first` | neutral Centers captured by round 800 up ≥ 2 |
    | `flank_policy` | `screen_home` → `flank_wide` | muckraker-turns spent in the enemy half up ≥ 150 % |
    | `empower_threshold` | 0 → 250 | empowers down ≥ 50 % **and** mean conviction delivered per empower up ≥ 2× |
    | `convert_over_kill` | `false` → `true` | enemy politicians converted up ≥ 3 |
    | `eco_exponential_round` | 200 → 1200 | slanderers built after round 400 up ≥ 10 **and** influence held in units at round 600 down ≥ 30 % |

14. **`tests/test_bc21_maps.nim`** — every committed bc21 map re-converts identically from the pinned
    `.map21`; sizes, seeds, symmetry sets and Center tables match the table in §Sim module; every map
    is 32–64 in both dimensions; passability is in `[0.1, 1.0]` on every converted map (the check that
    excluded `Misdirection`); each team has 1–3 Centers and there are ≤ 6 neutrals; team Centers all
    start at 150; the recorded symmetry actually holds; and no bc21 map name resolves to a bc20 map
    file.
15. **`tests/test_bc21_perf.nim`** — a full 1500-round game on `PaperWindmill` (48×48) with both seats
    on `opening: muck_spam`, `muck_ratio: 90` in **≤ 75 s**; failing it means switching
    `gamesPerMatch` to 1 (§The game).
16. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain,
    twice in one process and across a save/load; and **record → re-derive for every bc21 end reason**
    (`annihilated`, `more_votes`, `more_enlightenment_centers`, `more_influence`, `coin_flip`, and the
    wall-clock `abandoned`/`deadline` stop applied by the same proc on both paths).
17. **`tests/test_bc21_replay.nim`** — a bc21 replay document round-trips; a **strict UTF-8 parse** of
    the written bytes; the viewer's re-derivation of a recorded bc21 match reproduces the recorded
    per-round hashes; the flag traffic and the auction re-derive identically from events + config +
    seed with nothing stored; and **every event kind respects its per-game bound** from the table in
    §Server, player, protocol.
18. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now three years wide: the
    results key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; `num_agents` present in **all three** variants'
    `game_config` and in `certification.game_config`, and **absent** at every variant top level;
    `config_schema.year.enum == ["bc26","bc20","bc21"]`; **`player[]` contains exactly the ids in
    `certification.players`** (the check that would have caught the bc20 release failure); every
    `config_schema` array bounded; no `tokens` in any `game_config`; both `game.protocols` keys and
    `game.docs.readme` plus **all five** `pages` are `{type,value}` objects; and the installed
    `coworld` CLI's own `validate_upload_manifest` / `_load_template_manifest` accepts the template.
19. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc21** fixture replay;
    the bc21 game block shadows no `ChromeCommon` alias and no bc26/bc20 game-block name (the tandem
    scar); `chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256;
    the page carries CSS for **all ten** emitted beat kinds; `#bc21-doctrines` carries a dismiss
    control and sits outside `var(--band)`; and `#killfeed`'s `bottom` rule references `--statrail`.

### `parity-oracle-bc21` job — the 2021 Java engine as a CI-only oracle

**This is a real round-loop oracle, not an arithmetic-only one.** The bc20 run could not build its
engine because `net.sf.jsi:jsi:1.1.0-SNAPSHOT` was published only to jcenter (dead) and Sonatype OSS
SNAPSHOTS (expired). **The 2021 engine has the same single dead dependency and nothing else** — every
other coordinate in `engine/build.gradle` resolves from Maven Central today (verified: slf4j-api and
slf4j-simple 1.7.21, commons-lang3 3.4, commons-cli 1.3.1, commons-io 2.4, asm and asm-tree 5.0.4,
flatbuffers-java 1.11.0, Java-WebSocket 1.3.0, hibernate-search 3.1.0.GA, trove4j 3.0.3 — all HTTP
200). And `net.sf.jsi` is **write-only dead weight**: `ObjectInfo` calls only
`robotIndex.init/add/delete` and never queries it (`grep robotIndex world/ObjectInfo.java` → 7 hits,
all writes), so nothing it computes can reach the game.

So the job **bypasses Gradle entirely** (which also sidesteps the dead `jcenter()` repository and the
`$JAVA_HOME/lib/tools.jar` javadoc dependency) and builds with plain `javac`. **The recipe below was
executed in the sandbox and works**: 94 engine source files compile clean, and
`battlecode.server.Main` runs a headless match and writes a `.bc21`.

1. `actions/setup-java@v4`, `distribution: temurin`, `java-version: "8"`. **JDK 8 is mandatory**, and
   for a reason worth recording: the instrumenter rewrites `java.util` classes with ASM 5.0.4, which
   refuses class-file versions above 52 — under JDK 21 every player class load throws
   `IllegalArgumentException` from `ClassReader` and the match silently ends in a coin flip on round
   1500. That failure is exactly what a "green" oracle looks like when it is proving nothing, so the
   job asserts the traced games have **non-zero robot counts at round 50** before it diffs anything.
2. Fetch `battlecode/battlecode21` at `BC21_COMMIT = ed39c1a4…` as a tarball.
3. Download the eleven jars from Maven Central by the exact coordinates in
   `tools/oracle/bc21/deps.lock` and **verify each sha256**.
4. `javac -d classes tools/oracle/bc21/jsi-shim/net/sf/jsi/{SpatialIndex,Rectangle,Point}.java
   tools/oracle/bc21/jsi-shim/net/sf/jsi/rtree/RTree.java` — four files, ~30 lines total, every method
   a no-op returning the declared type. They stand in for the dead artifact and can affect nothing,
   which the job re-proves each run by asserting `ObjectInfo.java`'s sha256 against the value in
   `deps.lock`: if upstream ever *reads* the index, the hash changes and the job fails loudly rather
   than lying.
5. `javac --release 8 -cp <jars>:classes -d classes $(find engine/src/main/battlecode -name '*.java'
   -not -path '*/battlecode/doc/*')` — 94 files. `battlecode/doc/**` is excluded because it is
   javadoc taglets against `com.sun.tools.doclets` (the only thing that ever needed `tools.jar`) and
   contains no gameplay.
6. Copy every non-`.java` file under `engine/src/main/battlecode` into the classes tree
   (`MethodCosts.txt`, `AllowedPackages.txt`, `DisallowedClasses.txt`, and the 76 `.map21`).
7. `javac --release 8` the oracle bot, `tools/oracle/bc21/examplefuncsplayer21/RobotPlayer.java`.
8. Run `tools/oracle/bc21/Bc21Trace.java` (compiled in step 5, `package battlecode.world;` so it needs
   no reflection). It constructs the engine's own `LiveMap` via `GameMapIO`, a `TeamControlProvider`
   over two `PlayerControlProvider`s, and `new GameMaker(gameInfo, null, false)` — the null packet
   sink is explicitly supported (`GameMaker.createEvent` guards on it) — then calls
   `GameWorld.runRound()` in a loop and prints the trace **from the live objects**, which carry every
   field the `.bc21` does not (cooldowns, flags, bids, buff counts, bytecodes used). This means **no
   flatbuffers reader, no `flatc`, no `pip install` on either side.** The engine's own sources are
   byte-for-byte unmodified; the driver is one extra file on the classpath.

**The oracle bot is `examplefuncsplayer`, made deterministic.** The stock 2021 bot calls
`Math.random()` in `randomDirection()` **and** `randomSpawnableRobotType()`, seeded from the wall
clock, so it is not reproducible even against itself.
`tools/oracle/bc21/examplefuncsplayer21/RobotPlayer.java` is that file **verbatim except for one
committed hunk** (`determinism.patch`): a static `java.util.Random RNG = new
java.util.Random(rc.getID())` assigned at the top of `run()` — static fields are per-robot under the
instrumenter — and both `Math.random()` call sites replaced by `RNG.nextDouble()`. Nothing else
changes, including the `System.out.println` calls, because removing them would change the bytecode
budget and therefore the bot. `years/bc21/chassis/scaffold21.nim` reproduces exactly that stream
through `rng.nim`.

**The trace.** One line per record, five pairs from the `small` pool: `maptestsmall`, `Arena`, `Bog`,
`Smile`, `Star` (`FrogOrBath` is measured locally and kept out of the job so five maps of engine time
fit the runner).

```
R <round> T <team> votes=<n> buffs=<n> ecs=<n> infl=<n> pol=<n> sla=<n> muc=<n> topbid=<n> bidder=<id>
R <round> U <id> t=<TYPE> team=<A|B|N> x=<n> y=<n> inf=<n> conv=<n> cd=<%.9f> flag=<n> bid=<n> ra=<n> bc=<n>
R <round> W winner=<A|B|-> dom=<NAME|->
```

Units are printed **in exec order**, not id order, which is what makes an ordering bug visible.

- **Tier A (BLOCKING) — rounds 1–200 bit-exact on all five pairs**, every field above including ids
  and the `%.9f` cooldown. Plus: no robot's `bc=` may exceed 80 % of its type's bytecode limit on any
  traced round (§Sim module).
- **Tier B (BLOCKING) — rounds 300, 700 and 1500 agree exactly on all five pairs** on every aggregate:
  winner and `DominationFactor` (if set), votes, buffs, Centers owned, total influence, the multiset
  of living robot types per team, and the total robot count.
- **Tier C (BLOCKING against a ledger) — the first divergent round of a whole 1500-round game.** This
  is where the sibling run left a wound (Fleet card 1218171523823317: an un-root-caused Tier C
  divergence was ruled an unacceptable close state), so here it is **not** merely "reported and
  trended". The job computes the first divergent round per map and compares it against
  `tools/ci/parity_ledger_bc21.json`, whose entries are
  `{"map": "...", "first_divergent_round": N, "cause": "<one sentence>", "docs": "PARITY.md#<anchor>"}`.
  The job **fails** if (a) a map diverges and has no ledger entry, (b) a map diverges **earlier** than
  its ledger entry, or (c) a ledger entry no longer reproduces (a stale excuse is as bad as a missing
  one). The target state, and the phase-30 exit condition, is an **empty ledger**: five maps
  re-deriving 1500 rounds bit for bit.

**The root-cause checklist for a Tier C divergence**, written here so the builder does not start from
zero at 2 a.m. Every item has its own unit test above, so a Tier C failure should bisect to one of
them in minutes: the empower scan order and the ids it assigns to conversions (test 3); a conversion
arriving with cooldown 0 instead of `initialCooldown` (test 1); the slanderer's **51st** payment and
its spawn-round payment (test 5); a slanderer whose parent Center was captured (test 5); camouflage
at exactly `roundsAlive == 300` (test 5); the `(bid+1)/2` losing charge and the both-teams-tied case
(test 6); the top-bidder tiebreak by `roundsAlive` before id (test 6); the buff expiry boundary at
`emit + 51` (test 4); healing lost above `convictionCap` (test 3); `(int)` truncation of a negative
split (test 3); the double-wipe going to B (test 7); and `Math.exp`'s last ulp (§Sim module).

Two extra JDK-only steps in the same job, because they need Java and nothing else does:

- **the table step (BLOCKING):** `tools/JavaBc21Tables.java` regenerates `data/bc21/ec_passive.json`
  and `data/bc21/embezzle.json` and the job byte-diffs them against the committed files. It also
  cross-checks `Math.exp` against `StrictMath.exp` over `x ∈ [1, 4096]` and prints any disagreement
  to the job summary.
- **the tail step (BLOCKING):** the same program compares Java's `getPassiveInfluence` against the
  Nim `fdlibm` implementation for 4 096 log-spaced values in `(4096, 10⁸]`; any disagreement fails
  and is written into `docs/PARITY.md` with the exact `x`.

Tiers A, B and C and both extra steps are the **phase-30 gate**. Every accepted divergence is listed
in `docs/RULES-BC21.md` §Divergences with its reason and mirrored in the ledger.

### `docker-smoke` job — now **three** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely
from `certification.game_config.num_agents` and hard-fails if the workflow's `<SEATS>` = **2**
disagrees):

1. **The bc26 certification-fixture episode**, unchanged → `dist/smoke/replay.json`.
2. **The bc20 episode**, unchanged → `dist/smoke/replay-bc20.json`.
3. **A bc21 episode**, new: `SMOKE_EXPECT_YEAR=bc21`, `SMOKE_PLAYER_IDS=awu,scaffold`,
   `SMOKE_CONTRACT_PROBE=0`, `SMOKE_REPLAY_OUT=dist/smoke/replay-bc21.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc21","pool":"small","seed":2,"gamesPerMatch":1,"maxRounds":400,
   "perGameBudgetSeconds":45,"matchBudgetSeconds":50,"connectTimeoutMs":15000}`. Seed 2 draws `Arena`
   (32×32, six neutral Centers), which gives the 400 rounds something to be about; at the default
   pace the recording runs ~16 s, so it outlasts the viewer smoke's 10 s soak (the ecos 2026-08-23
   scar).

All three run one game container + two player containers on a shared network with `file://` artifact
URIs and **no** `ANTHROPIC_API_KEY`, so both seats take the scripted path and must still complete. All
three assert: the game exits 0, **every player container exits 0**, `results.json` carries exactly the
expected key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`, and the
replay parses as **strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the right `year`,
and a non-empty `events` array.

**New, and required by the LEARNINGS pin — the episode substance assertion.**
`tools/ci/docker_smoke.sh` gains one env knob, `SMOKE_REQUIRE_STATS`, a JSON object of
`{"<results.games[0] key>": <minimum>}` that must hold **for both seats**. The bc21 episode passes
`{"units_built":5,"influence_spent":100,"bids_placed":1,"votes":1}`; the bc20 episode passes
`{"units_built":3,"soup_mined":1}`. An episode where a seat did nothing is now a red build rather
than a green one with an empty replay.

The three replays are uploaded as the `smoke-replay` artifact, and a step asserts all three exist and
report three different `year` values.

### `wasm-viewer` job — the bundle is **executed**, against **all three** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay> --timeout 90
--soak 10` in headless chromium (Playwright pinned 1.55.0) **once per replay** —
`dist/smoke/replay.json`, `dist/smoke/replay-bc20.json` and `dist/smoke/replay-bc21.json`. Each run
requires `data-replay-loaded="true"` (or the bridge `ready` posted after it), three **differing**
clock/scorebug readouts at 0 % / 50 % / 100 %, continued advancement across the soak,
`scrub_selector == "#scrub"` (so a seek was really exercised and the `#viewpanel` zoom slider was not
clicked instead), `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line, and no
overlay covering more than 50 % of the board after the soak. **New gate, all three replays:** the
`#killfeed`/stat-box overlap check described in §Viewer, at 360 px, 720 px and 1280 px and at both FIT
and 2× zoom. `--strict-text-bounds` stays deliberately dropped here because the board is pannable and
zoomable (`#viewpanel` is kept), which is the exact case the flag's own documentation excludes; the
`canvas_text` counts are still recorded in `viewer-smoke.json`, and the separate
`tools/ci/renderer_fixture.html` step — full-cap `notes` and `motto` on both seats at three widths
including **360 px**, in the page's own CSS extracted from `client/replay_broadcast.html` — runs
through the same harness with `--strict-text-bounds`, because every CI replay is scripted and carries
no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a bc21 row.
`node tools/wasm_replay_smoke.cjs` is also run against the bc21 smoke replay **and** the committed
`tests/fixtures/replay-bc21.json`, so wasm32-only failures (int overflow traps, address-space
exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation of
  anything a cog sends. The 2021 engine exists only in the `parity-oracle-bc21` CI job.
- **Full bytecode metering.** The `DecisionOps` budget replaces it, with no mid-turn resumption. A
  Nim-level instrumenter is a compiler project and buys nothing the oracle does not already prove.
- **A cog-authored Java (or any) strategy class.** Doctrines are **JSON-sheet only**; there is no
  `javac`, no instrumenter `Verifier`, no compile-error round trip and no multi-attempt loop. Nothing
  in the schema is closed against a future sandboxed hook.
- **A bc21 certification fixture, and any new `player[]` entry.** Certification stays on bc26 and
  `player[]` stays at `awu` + `scaffold`. bc21 is proven by its own `docker-smoke` episode and the
  viewer smoke run against that episode's replay.
- **58 of the 76 official maps.** The converter handles any `.map21`; v1 commits the 18 whose sizes,
  seeds, symmetry and Center tables are pinned in this note. `Cow` (80×50, over the spec's own limit
  and dropped from scrimmages by patch 2021.2.4.0) and `Misdirection` (two tiles at passability 0.0,
  which freeze a robot for ever) are excluded on purpose.
- **The official 2021 TypeScript client, `battlecode-playback`, and `.bc21` flatbuffers in the
  browser.** Its *sprites* are reused (credited, AGPL-3.0); its webpack app is not shipped, not
  embedded and not built. No `match_b64` field exists.
- **A cog-authored flag protocol.** The flag word is the chassis's, shared by both teams; a doctrine
  cannot redefine it. The knobs steer what gets said, not the encoding.
- **Per-robot fog in the viewer.** The spectator sees the true world, slanderers included; the fog is
  a rule for robots, and hiding it would make the muckraker story invisible.
- **`babyducks`, `XSquare` and `IvanGeffner/battlecode2021` as behaviour sources.** The first is not
  published; the others carry no licence. They are named in prose as archetypes and nothing more.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the campaign.
- **Crossplay (Python bots), indicator dots and lines, the engine profiler and `speedscope`.** None of
  them exist in the port.
- **Battlecode years other than 2026, 2020 and 2021.** The registry, `game_config.year`, the variant
  naming and `years/dispatch.nim` all support more; only these three are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. The one apparent conflict —
"up to 3000 rounds" — is resolved against the pinned engine source in §The game, and recorded as a
divergence from the spec's stale prose rather than as an open question.)*
