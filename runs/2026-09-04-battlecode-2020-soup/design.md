# cogame-battlecode — the `bc20` year module: Battlecode 2020 "Soup" (design note, 2026-09-04)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a
branch/PR of the shipped repo that adds the year module `bc20` beside `bc26`, adds the manifest
variant `bc20`, and bumps the version of the *same* coworld. There is no `cogame-battlecode-soup`.
The starter is chosen by game shape and it is the only defensible one: bc20 is the same shape as
bc26 — a deterministic Nim grid sim compiled twice (native for the server, wasm for the viewer), a
one-shot sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm replay
viewer that re-derives every frame — and the bc26 build already cut the **year-module boundary**
(`src/battlecode/years/<year>/`, `years/registry.nim`, `game_config.year`) precisely so that a
second year is a directory, a registry line and a variant. Lineage: `coworld-ctf` (paintbot) →
`cogame-battlecode` → this. **Every convention in `Metta-AI/cogame-battlecode` holds here unless
this note says otherwise**: the Nim sim/server/player layout, `nimby.lock`, the bitworld runtime
contract, `GameVersion` discipline, `tools/build_replay_viewer.sh`, the `replay-viewer/` bundle,
the `client/` chrome, the one-parallel-batch doctrine layer (`llm.nim` / `decide.nim` /
`sheet.nim` / `baselines.nim`), the closed results document, and "degrade, never hang".

This note lands in the repo as `docs/plans/2026-09-04-battlecode-2020-soup-design.md` on the
branch `bc20-year-module`. The copy of record for the run is
`runs/2026-09-04-battlecode-2020-soup/design.md`.

**Everything below about the 2020 rules was verified by reading `github.com/battlecode/battlecode20`
at `master`** (the last 2020 state; the repo has not been pushed since 2020-11-28) — `specs/specs.md`,
`engine/src/main/battlecode/common/GameConstants.java`, `common/RobotType.java`,
`common/Transaction.java`, `world/GameWorld.java`, `world/InternalRobot.java`,
`world/RobotControllerImpl.java`, `world/IDGenerator.java`, `world/control/CowControlProvider.java`,
`schema/battlecode.fbs`, and by **parsing all 52 `.map20` files** in
`engine/src/main/battlecode/world/resources/` for their real sizes, seeds, soup, cow counts and
symmetry. Base-repo facts were read from a fresh clone of `Metta-AI/cogame-battlecode` at
`cb37075`. `file:line` and constant references below are to those trees.

### Source idea (verbatim)

```
# 28 Battlecode 2020 Soup (mod of cogame-battlecode) — add the bc20 year variant and its own league: the best-evolving Battlecode meta (lattice / rush / drone-harass / turtle) as a doctrine game

UPDATE 2026-09-03T22:05Z (daveey): this is a MOD of the existing Metta-AI/cogame-battlecode repo, not a new repo. Battlecode is one coworld with one manifest variant per year and one league per year. Work on a branch/PR of cogame-battlecode: add the year module `bc20` (Nim sim of the 2020 rules, Nim chassis from Bowl of Chowder's behaviour, converted 2020 maps, the 2020 sprite set, the bc20 sheet knobs), add manifest variant `bc20` (num_agents 2) alongside `bc26`, keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create a SECOND league: seed league_key `bc20`, league_name `Battlecode 2020 — Soup`, `default_variant_id: "bc20"`, short_name `bc20` (softmax.com/battlecode/bc20), its own two champions and fillers, its own credit pool; do NOT touch the bc26 league or the game's default league. Everything below about a separate `cogame-battlecode-soup` repo is superseded.

UPDATE 2026-09-03T21:45Z (daveey): NO JAVA AT RUNTIME. Same treatment as card 27: a FULL BEHAVIOUR PORT of the 2020 Soup rule set (rising water/flood schedule, soup deposits + refineries, miners/landscapers/drones/vaporators/net guns/design schools/fulfillment centers, dirt elevation and dig/dump, drone carry + drop-in-water, HQ burial, the 64-int blockchain with its cost model, pollution, round-3000 end and the tiebreak order) to a deterministic Nim sim (server native, viewer wasm; java.util.Random reproduced), Nim chassis bots ported from the BEHAVIOUR of examplefuncsplayer and Bowl of Chowder (AGPL) with the doctrine sheet knobs as parameters, JSON-sheet-only doctrines, the standard static wasm viewer re-deriving frames (no .bc20, no 2020 client; reuse its sprite art), and the 2020 Java engine used ONLY as a CI parity oracle (Java 8 + Gradle 6 in CI only; the image has no JDK). This removes the Java-8/tools.jar and Maven-403 hazards from the runtime entirely. Starter: cogame-battlecode itself once it has shipped (it is a coworld-ctf/paintbot fork), else coworld-ctf directly — paintbot's wasm viewer frame/chrome verbatim; not cogame-moba, not cogame-factorio. The Java-wrapper pins below are superseded wherever they conflict.

The best-designed Battlecode ever, by the competitors' own account. MIT Battlecode 2020 "Soup" is the year whose strategy space evolved almost entirely by player discovery under near-stable rules (one balance patch all season): turtle -> terraform/lattice (Super Cow Powers, Bruteforcer) -> rush -> drone-harass + passive lattice + drone-wall + drone-wall-buster, with four genuinely different builds coexisting in finals (aggressive lattice / Java Best Waifu, small-lattice + drone-wall / Smite, rush / Kryptonite, passive lattice / Bowl of Chowder). Stone Tao: "by far the best designed Battlecode... a single spec change that occurred right after sprint and that was it" (https://stonet2000.github.io/battlecode/2020/). That is exactly the property a doctrine-authoring coworld wants: a wide, legible menu of macro archetypes that beat each other in a rock-paper-scissors, not one mathematically optimal build.

The game: a 2-team turn-based grid war where the water rises every round and floods the map from the edges in. Each team starts with an HQ; miners mine SOUP from deposits and refine it, design schools build LANDSCAPERS that dig and dump dirt (terraforming the map higher than the flood, walling the HQ, or burying the enemy HQ), fulfillment centers build DELIVERY DRONES that pick up and carry any unit (including enemies, whom they drop into water), vaporators generate soup passively, net guns shoot drones. Win by burying the enemy HQ under dirt, drowning the enemy, or holding more HQ health / units when the flood ends the game at round 3000. Bytecode-limited robots, a 64-int blockchain as the only global channel.

The coworld wraps the unmodified 2020 engine and follows the cogame-battlecode (2026) build one-for-one: policy = doctrine (a JSON strategy sheet plus an optional Java strategy class on a public chassis), both seats submit once at match start, the engine plays the whole match, the recorded match file is the replay. Same server, same protocol, same viewer chrome, same doctrine loop; only the year module changes — engine, maps, chassis, sheet knobs, client.

Seats: 2 (Team A / Team B, one cog per side). num_agents = 2 in every variant and the certification fixture.
Motive: zero-sum. The doctrine choice is the whole game: lattice vs rush vs drone-harass vs turtle, when to start terraforming, how much soup to sink into vaporators, drone-wall or not.
Policy interface: text/code, one shot per episode, identical to cogame-battlecode: a DOCTRINE = (1) a JSON strategy sheet of named knobs exposed from the chassis — opening {rush | lattice | passive_lattice | turtle}, terraform_start_round, lattice_radius, landscaper_count_curve, miner_count_curve, vaporator_budget, drone_role {harass | wall | buster | carry_landscapers}, net_gun_ring, rush_trigger, wall_hq_round — plus (2) an optional Java Strategy class compiled in-container (javac + the 2020 instrumenter Verifier), compile errors back to the cog, max 3 attempts, then the sheet alone applies; both seats sealed and simultaneous; headless battlecode.server.Main plays the match; results carry HQ health, units, soup, the burial/drown round and who did it.
Scripted baselines (same image, PLAYER_SCRIPTED=<name>): bowl-of-chowder (Stone Tao's finals bot, 5th-6th, https://github.com/StoneT2000/Battlecode2020, AGPL-3.0 — the chassis; its repo also carries `rush/` and `quiet/` variants and the Chow7-10 lineage) and examplefuncsplayer (the scaffold bot). Champions are PLAYER_PROMPT LLM policies — daveey: a lattice/terraform doctrine; daveey-1: a rush + drone-harass doctrine — on the same chassis.
Fills gap: the best-evolving Battlecode metagame as a doctrine game; four documented archetypes for cogs to choose between and counter; a rising-flood clock that makes every match end visibly; the second year on the shared cogame-battlecode engine wrapper, proving the year module boundary.
Integrity (anti-collusion): symmetric seeded maps (the engine ships 52 in engine/src/main/battlecode/world/resources), sealed simultaneous doctrines, no cross-team channel except the engine's own blockchain (which both teams read — a real in-game signalling game, also the year's famous meta-gaming vector, so the replay endcard shows what each team wrote to it), anonymous aliases (Clan Ash / Clan Basil), real names spectator-side only, public chassis.

Replay plan (watchability): the official 2020 web client (battlecode20/client/visualizer, TypeScript + webpack, `battlecode-playback` reads .bc20 flatbuffers) already loads a match from a URL: `conf.matchFileURL` (client/visualizer/src/app.ts) XHRs the file and calls loadFullGameRaw. Build it with `npm run prod` into the standard static-replay-viewer bundle behind the starter chrome (scrubber, transport bar, scorebug, endcard), exactly as cogame-battlecode does with the 2026 client: the coworld replay JSON envelope embeds the .bc20 bytes base64 (match_b64), the viewer decodes it in the browser and hands it to the client's playback. No pod, no server, no engine in the browser. Spectators get the real thing: the water rising round by round, lattices climbing out of the flood, drones carrying landscapers over walls, an HQ disappearing under dirt, and an endcard naming the doctrines in plain words plus the blockchain messages each side sent.

Design pins for the builder (Java-wrapper era, superseded by the UPDATE above where they conflict): starter = Metta-AI/cogame-battlecode if it has shipped (it is a coworld-ctf/paintbot fork), else coworld-ctf directly; keep the year module boundary the 2026 build established. Repo Metta-AI/cogame-battlecode-soup, slug `battlecode-soup`, licence AGPL-3.0 (engine is GPL-3.0, Bowl of Chowder AGPL-3.0). Engine: build from source at https://github.com/battlecode/battlecode20 (tag the last 2020 release; Gradle wrapper 6.0.1, Java 8 — engine/build.gradle uses `compile` and links $JAVA_HOME/lib/tools.jar, so the image needs a JDK 8 toolchain for the engine stage; the public Maven at releases.battlecode.org does not serve 2020 (403) and maven.pkg.github.com/battlecode/battlecode20 needs a GitHub token at build time — build from source is the reliable path, prove it in CI first). Specs: battlecode20/specs/specs.md. Do NOT vendor Ivan Geffner's winning bots (https://github.com/IvanGeffner/battlecode2020: finalbota/b/c, rush, turtle, eco, dronecrunch, antidrones — no licence, all rights reserved); they are a reference for what the sheet's archetypes should express, not code to ship. CI: gradle (JDK 8 for the engine, JDK 21 for the wrapper is fine) + headless smoke (examplefuncsplayer vs bowl-of-chowder on maptestsmall, assert a .bc20 is written and loads in battlecode-playback) + the viewer smoke on that real .bc20. Timing: play inside 60% of episodeTimeoutSeconds (720 s); 3000 rounds with two full bots may not fit — measure in CI, and size the match (a round cap via the engine's -Dbc.game.* properties or a wall-clock guard that stops the engine and scores the recorded state, best-of-1 v1). Everything else as the spec.

Source: https://github.com/battlecode/battlecode20 (engine, client, specs, 52 maps); https://github.com/StoneT2000/Battlecode2020 (Bowl of Chowder chassis, AGPL) and postmortem https://stonet2000.github.io/battlecode/2020/; sibling https://github.com/Metta-AI/cogame-battlecode (2026 edition, the wrapper to reuse)
```

### What the two UPDATE blocks supersede, and where each is discharged

| Binding update | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; no new repo; one variant per year; one league per year; certification stays bc26; version bump of the same coworld | this paragraph, §Packaging |
| NO JAVA AT RUNTIME; full behaviour port of the 2020 rule set to a deterministic Nim sim (native + wasm); `java.util.Random` reproduced | §Sim module |
| Nim chassis from the **behaviour** of examplefuncsplayer and Bowl of Chowder; JSON-sheet-only doctrines (no Java strategy class, no in-container compilation) | §Decisions, §Sim module ("the two chassis"), §Out of scope |
| Standard static wasm viewer re-deriving frames; no `.bc20` in the browser, no 2020 TypeScript client; reuse the 2020 sprite art | §Viewer |
| The 2020 Java engine as a **CI-only** parity oracle (JDK 8 + Gradle 6, built from source) | §Tests ("parity-oracle") |
| Converted 2020 maps, committed | §Sim module ("Maps") |
| Phase-50 second league `bc20` | §Packaging ("The phase-50 plan") |

### Interface caution: this note is written to the POST-fix `cogame-battlecode` interface

Three findings from the sibling run land on `main` before this build starts. Everything here assumes
they are already in:

- **D1 — the chassis is not an LLM-selectable knob.** The `chassis` field is gone from the doctrine
  sheet; the champion chassis is fixed by the operator. **The bc20 sheet has no `chassis` key**, and
  `tests/test_bc20_sheet.nim` asserts that a submitted `chassis` is recorded as an *unknown field*
  and never honoured (§Decisions, §Tests). The chassis a seat drives comes from `PLAYER_SCRIPTED`
  (scripted seats) or is the fixed champion chassis (LLM seats).
- **D2 — the scripted baseline plays, and CI has a survival gate.** bc20's strong baseline
  (`bowl-of-chowder`) has real defensive play — HQ wall, net gun ring, drone defence — and
  `tests/test_bc20_baselines.nim` gates on survival and on positive play counters, not on a win
  alone (§Tests, item 10c).
- **D3 — the doctrine overlay must be dismissible.** `#bc20-doctrines` ships with a close control,
  an Esc binding and a re-open chip; it never sits in the transport band (§Viewer).

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — same shape as bc26 (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy); it *is* the coworld-ctf row of the table, one generation on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. No new repo (idea UPDATE 22:05Z). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints. `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=bowl-of-chowder\|examplefuncsplayer` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc20/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc20` bytes anywhere. |
| Real art, starter chrome verbatim | 2020 sprites cut from `battlecode20/client/visualizer/src/static/img/` into `data/atlas_bc20.*` (credited in `NOTICE`); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc20 game block appended** (§Viewer). |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **425 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26].game_config` (unchanged), `variants[bc20].game_config` (new) and `certification.game_config` (unchanged, bc26); never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc20 policy set is in §Packaging. |

---

## The game

**Battlecode 2020 "Soup", played by doctrine, simulated in Nim.** Two cogs each command a team on a
symmetric 32×32–48×48 grid. Neither cog moves a robot. At t=0 each writes a **doctrine** — a JSON
sheet of ten named knobs — and the deterministic sim plays the whole match from those two sheets
while both cogs watch.

The clock is the water. From round 1 the water level rises on a fixed curve and floods outward one
ring per round from every already-flooded tile whose neighbour sits below the level. Anything that
is not a delivery drone dies on a flooding tile. **The HQ starts at effective elevation 2–5** (a map
guarantee), so an HQ that is never terraformed **drowns between round 464 and round 1210** — a team
that does nothing loses on a schedule. Miners mine soup and carry it to the HQ or a refinery; design
schools build landscapers that dig and dump dirt to raise the ground (a *lattice*), wall the HQ in,
or bury the enemy HQ under 50 dirt; fulfillment centers build delivery drones that pick up any unit
— including enemy landscapers — and drop them in the water; vaporators print soup and scrub
pollution; net guns shoot drones down. The only global channel is a 7-int-per-transaction,
7-transactions-per-round blockchain that both teams read, paid for in soup.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. The episode seed
decides which slot takes engine-side **A (red)** in game 1; sides alternate every game
(`sideAslotFor(seed, gameIndex)`, reused verbatim from bc26's `maps.nim`).

### Constants (verbatim from the pinned engine — `common/GameConstants.java`, `common/RobotType.java`)

Generated into `src/battlecode/years/bc20/constants.nim`, never hand-typed (§Sim module).

| unit | cost | dirt limit | soup limit | action cooldown | sensor r² | built by |
|---|---|---|---|---|---|---|
| HQ | — | health 50 | — | 1 | 48 | — (map) |
| Miner | 70 | 0 | 100 | 1 | 35 | HQ |
| Landscaper | 150 | **25** | 0 | 1 | 24 | Design School |
| Delivery Drone | 150 | 0 | 0 | **1.5** | 24 | Fulfillment Center |
| Refinery | 200 | health 15 | — | 1 | 24 | Miner |
| Vaporator | 500 | health 15 | — | 1 | 24 | Miner |
| Design School | 150 | health 15 | — | 1 | 24 | Miner |
| Fulfillment Center | 150 | health 15 | — | 1 | 24 | Miner |
| Net Gun | 250 | health 15 | — | 1 | 24 | Miner |
| Cow (NPC) | — | 0 | 0 | 2 | 10000 | — (map) |

Pollution fields (`RobotType`): HQ and Refinery `pollutionRadiusSquared 35, additive +500, global +1,
maxSoupProduced 20`; Vaporator `35, multiplicative ×0.80, global −1, maxSoupProduced 2`; Cow
`15, additive +2000, global 0`. All other types have no pollution effect.

Game constants: `INITIAL_SOUP 200`, `BASE_INCOME_PER_ROUND 1`, `SOUP_MINING_RATE 7`,
`MAX_DIRT_DIFFERENCE 3`, `DELIVERY_DRONE_PICKUP_RADIUS_SQUARED 3`,
`NET_GUN_SHOOT_RADIUS_SQUARED 15`, `BLOCKCHAIN_TRANSACTION_LENGTH 7`,
`NUMBER_OF_TRANSACTIONS_PER_BLOCK 7`, `INITIAL_COOLDOWN_TURNS 10`,
`MIN_WATER_ELEVATION -1073741824` (`Integer.MIN_VALUE/2`), `MAX_ROBOT_ID 32000`.

Derived functions (all in **float32**, Java `float`):
`waterLevel(x) = (float)(exp(0.0028x − 1.38·sin(0.00157x − 1.73) + 1.38·sin(−1.73)) − 1)`;
`cooldownCoefficient(P) = 1 + P/2000`; `sensorCoefficient(P) = 1/(1 + P/4000)²`.

### The 2020 rule set — exact numbered resolution rules

The sim's own step list. Numbers 1–9 are one round; re-ordering any of them is a rules change and
bumps `GameVersion`. It mirrors `GameWorld.runRound` / `processBeginningOfRound` /
`updateDynamicBodies` / `processEndOfRound` exactly.

1. **Round increment and income.** `currentRound += 1`. Both teams' soup pools gain
   `BASE_INCOME_PER_ROUND = 1` (`teamInfo.addSoupIncome`, applied to A and B).
2. **Beginning of round, per robot.** Every non-blocked robot runs `processBeginningOfRound` — a
   no-op in 2020, kept as a named step because the hash chain and the parity trace are taken around
   it.
3. **Turn order.** Iterate the dynamic bodies in **spawn order** (`ObjectInfo.eachDynamicBodyByExecOrder`
   — append on spawn, remove on death), **not** id order. Map bodies (2 HQs, then the cows) are
   appended in file order, so the initial exec order is the map's own.
4. **Blocked robots take no turn.** A robot held by a delivery drone is `blocked`: it does not run
   `processBeginningOfTurn`, does not act, and its cooldown does **not** decay. It *does* still get
   `resetPollutionForRobot` if its type can pollute (`GameWorld.updateRobot`).
5. **Beginning of turn.** `cooldownTurns = max(0, cooldownTurns − 1)`; the robot's `DecisionOps`
   budget is reset (§Sim module — this replaces the Java bytecode limit).
6. **Run the controller.** A cow runs the ported `CowControlProvider`; every other robot runs its
   team's chassis under that team's doctrine, spending at most its `DecisionOps` budget. A robot may
   act only while `cooldownTurns < 1`; every action adds
   `type.actionCooldown × cooldownCoefficient(pollution at the robot's tile)` to `cooldownTurns`.
   The legal actions, with their exact preconditions:
   1. **Move** (`Miner`, `Landscaper`, `Delivery Drone`, `Cow`): destination adjacent (8-neighbour),
      on the map, unoccupied, and — for everything except a drone —
      `|elevation(dest) − elevation(here)| ≤ MAX_DIRT_DIFFERENCE = 3`. A drone may enter a flooded
      tile; nothing else may.
   2. **Mine soup** (`Miner`): target is the miner's own tile or an adjacent tile, on the map, with
      soup > 0. Mines `min(7, soup(tile), 100 − soupCarrying)`; that amount is removed from the tile
      and added to the miner.
   3. **Deposit soup** (`Miner`): target adjacent, holding a robot whose type can refine (HQ or
      Refinery). Transfers `min(requested, soupCarrying)` into that building's `soupCarrying`. It is
      **not** yet in the team pool.
   4. **Build** (`HQ`→Miner; `Miner`→Refinery/Vaporator/Design School/Fulfillment Center/Net Gun;
      `Design School`→Landscaper; `Fulfillment Center`→Delivery Drone): team soup ≥ cost; the target
      tile is adjacent, on the map and unoccupied; the tile is not flooded unless the built type is a
      Delivery Drone; the elevation difference is ≤ 3 unless the built type is a Delivery Drone. Cost
      is deducted, the new robot spawns with `cooldownTurns = INITIAL_COOLDOWN_TURNS = 10`, and is
      **appended to the exec order**.
   5. **Dig dirt** (`Landscaper`): `dirtCarrying < 25`; target is own or adjacent tile, on the map;
      if the tile holds a **building**, that building must have `dirtCarrying > 0` (you may not dig
      out from under a clean building). Effect: if the tile holds a building, remove 1 from the
      building's dirt; otherwise `elevation(tile) −= 1`. Either way `dirtCarrying += 1`.
   6. **Deposit dirt** (`Landscaper`): `dirtCarrying ≥ 1`; target own or adjacent, on the map.
      `dirtCarrying −= 1`; if the tile holds a **building**, that building's dirt `+= 1`; otherwise
      `elevation(tile) += 1` and the tile is **resurfaced** (rule 8.3). A building whose accumulated
      dirt reaches its **health** (HQ 50, every other building 15) is destroyed, and that many units
      of dirt land on the now-vacant tile.
   7. **Pick up unit** (`Delivery Drone`): not already holding; the target is a **unit** (never a
      building, never another drone), within `r² ≤ 3`. The target is removed from the grid, marked
      `blocked` and rides at the drone's location.
   8. **Drop unit** (`Delivery Drone`): holding; target adjacent (or the drone's own tile when the
      drone dies), on the map, unoccupied. The unit is unblocked and placed. **If the target tile is
      flooded and the dropped unit is not a drone, it is destroyed immediately.**
   9. **Shoot** (`Net Gun`, and the `HQ`, which has a built-in net gun): the target is a Delivery
      Drone within `r² ≤ NET_GUN_SHOOT_RADIUS_SQUARED = 15`. It is destroyed.
   10. **Submit transaction** (any robot, **not** an action — no cooldown, no `isReady` check): the
       message is exactly **7 ints**; `cost > 0`; `cost ≤ team soup`. The soup is deducted
       **at submit time**, the transaction is stamped with an id from the transaction RNG (rule 8.1)
       and joins the **transaction pool**.
   11. **Read** (any robot, free): own tile and any tile within
       `round(type.sensorRadiusSquared × sensorCoefficient(P at the robot's tile))` — elevation,
       flood status, pollution, soup and robots — plus **every block ever minted**.
7. **End of turn.** In this order (`InternalRobot.processEndOfTurn`):
   1. If the type can pollute, **clear this robot's previous local pollution effect** (subtract its
      additive from, and divide its multiplicative out of, every tile it covered).
   2. If the type can refine (HQ or Refinery) and `soupCarrying > 0`: refine
      `min(soupCarrying, maxSoupProduced = 20)` into the **team pool**; set `shouldPollute`.
   3. If the type is a Vaporator: add `maxSoupProduced = 2` to the team pool unconditionally; set
      `shouldPollute`.
   4. If the type is a Cow: set `shouldPollute`.
   5. If the type can pollute and `shouldPollute`: `globalPollution = max(0, globalPollution +
      globalPollutionAmount)`, then register a fresh local effect over `r² = pollutionRadiusSquared`
      with this type's additive and multiplicative values. A refinery's local +500 therefore lasts
      **exactly one round** — it is installed here and removed at 7.1 of its own next turn.
   6. `roundsAlive += 1`.
   7. If the controller terminated the robot (`disintegrate`), destroy it now.
8. **End of round**, after every body has taken its turn:
   1. **Blockchain.** Drain up to `NUMBER_OF_TRANSACTIONS_PER_BLOCK = 7` transactions from the pool
      into this round's block, in the pool's priority order: **higher cost first; ties broken by
      higher transaction id; ties broken by the lexicographically earlier serialized message**
      (`Transaction.compareTo`, where the serialized message is the 7 ints joined by `_`).
      Transactions that did not make the cut **stay in the pool** and remain eligible for ever. Each
      minted transaction increments its team's `blockchainsSent`. **The transaction id comes from a
      single static `java.util.Random` that the engine re-seeds with the map seed every time a robot
      controller is constructed — i.e. on every spawn, including the two HQs and every cow.** That
      quirk decides ties and is reproduced exactly (§Sim module, Determinism).
   2. **Water level.** `waterLevel = getWaterLevel(currentRound)` (float32).
   3. **Flood fill.** Collect the set of tiles that are flooded *now*, before any change. For each
      such tile, for each of the 8 directions: if the neighbour is on the map, is not already
      flooded, and `float32(elevation) < waterLevel`, flood it — and **destroy any robot standing
      there that cannot fly**. Because the origin set is snapshotted first, the flood advances
      **exactly one ring per round**. (Rule 6.6's deposit runs `tryResurface`, which un-floods a tile
      the moment `float32(elevation) ≥ waterLevel`.)
   4. **End-of-match check.** Only when `roundLimitReached || destroyedHQ(A) || destroyedHQ(B)`, and
      only if no winner is set yet. `roundLimitReached` is the engine's own
      `currentRound >= maxRounds − 1` — with `maxRounds = 1500` the last played round is **1499**;
      the off-by-one is the engine's and is reproduced. The ladder, in order, first hit wins:
      1. **HQ destroyed** — exactly one team's HQ is gone → the other team wins (`hq_destroyed`).
      2. **Quantity** — more **robots** alive, buildings included (`quantity`).
      3. **Quality** — greater **net worth** = team soup pool + Σ `type.cost` over all living
         non-neutral robots (`quality`).
      4. **Broadcasts** — more transactions **minted** (`broadcasts`).
      5. **Highest robot id** — the team owning the highest-id living non-neutral robot
         (`highest_id`).
      6. **Coin flip** — reachable only when neither team has a single living robot (`coin_flip`).
   5. Record the per-team round stats and close the round record.
9. **Hash chain.** Append this round's state hash (§Sim module).

**Cows** (`world/control/CowControlProvider.java`, ported exactly). A cow's RNG is
`java.util.Random(84307 × mapSeed + 20201 × (cowId / 2))`, created lazily on the cow's first turn.
Each turn: if the cow is ready, draw up to **4** directions as
`DIRECTIONS[floor(nextDouble() × 8)]` over `{N, NE, E, SE, S, SW, W, NW}`, reversing the direction
when `cowId` is odd, and move on the first draw that is legal **and** whose destination is not
flooded — **stopping the draw loop the moment it moves**. If the cow is not ready, it burns exactly
4 `nextDouble()` calls and does nothing. The reversal uses the map **symmetry**, which the engine
**recomputes on every robot spawn** from the *current* world (soup, elevation and robot types under
each candidate transform), testing candidates in the order **vertical, horizontal, rotational** and
taking the first survivor, defaulting to rotational. All of that is load-bearing and is ported
literally.

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc20` variant is **best-of-three on three
distinct maps with a 1500-round cap**. The cap is not arbitrary: elevation 6 floods at round 1413
and elevation 7 at 1546, so by round 1500 every HQ has either been terraformed above the water or
has drowned — the game is *decided* by the cap rather than merely stopped at it. (The idea's
"round 3000" is the elevation-1000 flood point; it explicitly allows sizing below it.)

```
container start, map load, seat connect              ≤  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    ≤  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 1499 rounds                         ≤ 320 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 100)
score + replay write + shutdown grace                ≤  30 s
                                                       -------
worst case                                             425 s   <= 720 s
```

Honest per-round estimate, so the builder can check it: the bc20 mixed pool tops out at 48×48 =
2304 tiles. A mature lattice game carries roughly 120 robots per team, so ≈ 240 robot-turns per
round at ≤ 1000 `DecisionOps` each = ≤ 2.4 × 10⁵ ops/round worst case, ≈ 3.6 × 10⁸ ops for a
1499-round game — single-digit seconds to ~30 s in release Nim. The flood fill is a full-grid scan
plus 8 neighbours (≈ 18 k operations/round, 27 M/game — negligible), and pollution install/clear
touches ≈ 113 tiles per polluting robot per turn (≈ 7 M/game). **The estimate is enforced, not
trusted:**

- `perGameBudgetSeconds = 100` and `matchBudgetSeconds = 320` are hard monotonic-clock guards. A
  game that blows its guard is abandoned, the finished games are scored, and
  `results.reason = deadline`.
- `tests/test_bc20_perf.nim` plays a full 1499-round game on `CentralSoup` (48×48, the largest map
  in the variant's pool) with both scripted chassis and **fails CI above 55 s**.
- If that gate ever goes red the fix is one config value — `gamesPerMatch: 3 → 1` in the `bc20`
  variant — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because the four archetypes the idea is built around
  (rush / lattice / passive lattice / turtle) are a rock-paper-scissors *across map shapes*; one map
  would rank the map, not the doctrine.

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

### Scoring, sign, and what the bc20 league ranks by

The 2020 game is win/lose; it has no point formula. This one is defined here, and it is a
continuous reading of the engine's own tiebreak ladder so that the score and the winner never tell
different stories:

```
hq[t]        = 1 if team t's HQ is alive at the final round else 0
survival[t]  = f32(hq[t])        / f32(max(1, hq[A] + hq[B]))         # 0.5 / 0.5 if both alive
units[t]     = count of living robots of team t (BUILDINGS INCLUDED, exactly the QUANTITY tiebreak)
worth[t]     = team soup pool + sum of type.cost over living non-neutral robots of t
                                                                      # exactly the QUALITY tiebreak
share_u[t]   = f32(units[t])     / f32(max(1, units[A] + units[B]))
share_w[t]   = f32(worth[t])     / f32(max(1, worth[A] + worth[B]))
points[t]    = int(60.0'f32 * survival[t] + 25.0'f32 * share_u[t] + 15.0'f32 * share_w[t])
                                                                      # TRUNCATION, not rounding
```

Three load-bearing details, each pinned by a test vector in `tests/test_bc20_scoring.nim`:

- every share is narrowed through **float32** before the weighted sum, and the sum is **truncated**
  by the `int()` cast. The reason is not fidelity to Java here (this formula is ours) but
  **recorder/re-deriver agreement**: the same arithmetic runs natively on x86-64 and in wasm32 and
  must produce the same integer;
- `units[t]` is the **robot count including buildings**, and `worth[t]` includes the team soup pool
  — because those are precisely what the engine's own ladder compares, so a `quantity` or `quality`
  win always comes with the matching share above 0.5;
- points are in `[0, 100]` and the two seats' points sum to ≤ 100.

Per seat, over the games actually played:

```
results.scores[t] = 100.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** The 100-per-game win bonus dominates the ≤ 100-point spread across three
games, which is what makes "lose your HQ, lose the game" true in the ranking as well as in the
rules. **The `bc20` league ranks by `results.scores`** (Elo over the resulting ordering), exactly as
the bc26 league does. A `deadline` episode scores the games that finished; a `fault` episode scores
`[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` in snake_case, plus our
one wall-clock value:

| `end_reason` | engine origin | meaning |
|---|---|---|
| `hq_destroyed` | `HQ_DESTROYED` | exactly one HQ was buried under 50 dirt or drowned |
| `quantity` | `QUANTITY_OVER_QUALITY` | round cap or a double HQ loss; more living robots wins |
| `quality` | `QUALITY_OVER_QUANTITY` | equal robots; greater net worth wins |
| `broadcasts` | `GOSSIP_GIRL` | equal worth; more minted transactions wins |
| `highest_id` | `HIGHBORN` | equal broadcasts; the highest living robot id wins |
| `coin_flip` | `WON_BY_DUBIOUS_REASONS` | neither team has a living robot; a draw from the world RNG |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded |

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from bc26**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped: a partial replay and `[0, 0]` are still written | `[0, 0]` |

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for bc26).
Container exit codes are unchanged: `0` whenever results + replay were attempted (including
`deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep answering for the ~20 s
shutdown grace, the websocket handler keeps its `Ping → Pong` **echo** (it must return the ping's
payload — commit `cb37075`) and does not filter binary frames.

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged from bc26: the player container is a thin registrar and
every decision is taken inside the **game** container, because that is the only container the
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

### The bc20 doctrine sheet — ten knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc20 chassis. Unknown key, wrong
type or out-of-range value → **that field's default**, recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by
answering badly — only by answering weakly.

| field | type / values | default | what it changes (`src/battlecode/years/bc20/chassis/…`) |
|---|---|---|---|
| `opening` | `rush` \| `lattice` \| `passive_lattice` \| `turtle` | `passive_lattice` | `boc.nim` `openingPlan()` — the build order and the role split for the first 400 rounds. `rush`: 8 miners then a forward Design School near the enemy HQ, landscapers dig the enemy HQ out and bury it. `lattice`: terraform outward from the HQ while contesting the middle. `passive_lattice`: terraform inward first, wall the HQ, then expand (the Bowl of Chowder build). `turtle`: wall immediately, minimum miners, maximum net guns. |
| `terraform_start_round` | int 1…1500 | 300 | `landscaper.nim` `terraformOpensAt()` — the round at which landscapers stop reinforcing the wall and start raising the lattice. |
| `lattice_radius` | int 2…12 | 6 | `lattice.nim` — the Chebyshev radius around the own HQ inside which every non-wall tile is raised to `waterLevel(round + 250) + 1`. |
| `landscaper_count_curve` | `lean` \| `steady` \| `swarm` (target = `4 + round/220` × 0.6 / 1.0 / 1.7, capped 40) | `steady` | `hq.nim` / `designschool.nim` `landscaperTarget(round)`. |
| `miner_count_curve` | `lean` \| `steady` \| `swarm` (target = `6 + round/300` × 0.6 / 1.0 / 1.7, capped 25) | `steady` | `hq.nim` `minerTarget(round)`. |
| `vaporator_budget` | int 0…6 | 2 | `miner.nim` — stop building vaporators once `vaporatorsBuilt >= budget`. Each costs 500 soup and returns 2 soup + −1 global pollution per round. |
| `drone_role` | `harass` \| `wall` \| `buster` \| `carry_landscapers` | `harass` | `drone.nim` — `harass`: hunt enemy units inside `r² ≤ 3` and drop them on the nearest flooded tile. `wall`: hold a ring at Chebyshev 4 from the enemy HQ, blocking ground movement. `buster`: hunt *enemy drones sitting in a wall* by baiting them over own net guns, and ferry a landscaper to the enemy HQ. `carry_landscapers`: ferry own landscapers over impassable elevation onto the lattice. |
| `net_gun_ring` | int 0…6 | 2 | `miner.nim` — how many net guns to build around the own HQ before spending on anything else. |
| `rush_trigger` | int 0…1500 (**0 = never**) | 0 | `boc.nim` — the round at which the rush wave commits to the enemy HQ. Only meaningful with `opening = rush` (with any other opening it selects the round at which a single harassing landscaper is sent). |
| `wall_hq_round` | int 0…1500 (**0 = never**) | 250 | `landscaper.nim` — the round at which landscapers begin raising the 8 tiles adjacent to the own HQ. Never walling is a real (and usually losing) choice: the HQ drowns between round 464 and 1210. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

**Every knob must have teeth.** `tests/test_bc20_knobs.nim` is a CI gate that proves each of the ten
visibly changes play, with a named signed stat delta per knob (§Tests item 11), and the endcard
reports the economic story so a spectator can see the knob in the match.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

- **champion #1, `battlecode-bc20-latticer` (daveey)**: *"You command a Battlecode 2020 team. The
  water rises every round and your HQ starts at elevation 2–5, so it drowns somewhere between round
  464 and round 1210 unless landscapers raise the ground around it. Your doctrine: out-build the
  flood. Set opening to \"lattice\" or \"passive_lattice\", wall the HQ early (wall_hq_round 180–260),
  start terraforming by round 250–350, take a lattice_radius of 6–9, and spend on vaporators
  (2–4) so your soup keeps coming after the near deposits are mined out. Keep a net_gun_ring of at
  least 2 so enemy drones cannot lift your landscapers off the wall, run drone_role
  \"carry_landscapers\" or \"wall\", and leave rush_trigger at 0. In notes, say which elevation you
  are building to and by what round."*
- **champion #2, `battlecode-bc20-rusher` (daveey-1)**: *"You command a Battlecode 2020 team. An
  enemy HQ needs 50 dirt on it to die, and a landscaper carries 25. Your doctrine: get there before
  their wall does. Set opening to \"rush\", a rush_trigger between 180 and 320, a lean or steady
  miner_count_curve, and a swarm landscaper_count_curve so the second wave arrives while the first is
  digging. Take drone_role \"harass\" or \"buster\" to lift their landscapers off their own wall and
  drop them in the water. Keep wall_hq_round non-zero anyway — if the rush stalls you still have to
  survive the flood — but keep lattice_radius small (2–4) and vaporator_budget low (0–1); soup spent
  on economy is soup not spent on landscapers. In notes, say what you do if the rush fails."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the flood table, the map cards for all three games, the scoring formula, the alias
pair, and the reply contract ("reply with ONE JSON object; your reply must begin with `{`"). The
assistant turn is prefilled with `{` and the prefix re-attached before parsing (the procgen 0.1.2
scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` becomes **year-aware**: `baselineFor(year, name)`. For `bc20` the two
published names are `bowl-of-chowder` (the default for an unrecognised name — a seat that says
nothing useful plays the strong published doctrine, not the weak floor) and `examplefuncsplayer`.
The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field
(D1).

**`bowl-of-chowder` — the strong baseline and the champion chassis.** Behaviour ported from
`StoneT2000/Battlecode2020` `src/FinalChowBotStable/` (AGPL-3.0), parameterised by the ten knobs. Its
scripted reply is the all-defaults sheet, i.e. the passive-lattice build. Algorithm, per role:

- **HQ** (`hq.nim`): on round 1 broadcast `HQ_LOCATION` with the own HQ tile; thereafter build a
  Miner whenever `minersAlive < minerTarget(round)` and soup ≥ 70, preferring the direction away
  from the nearest flooded tile. Shoot any enemy drone within `r² ≤ 15` before building. From round
  `wall_hq_round`, broadcast `WALL_IN` once. If `dirtOnSelf ≥ 25` (half-buried) broadcast
  `HQ_UNDER_ATTACK` every round and stop building until it clears.
- **Miner** (`miner.nim`): if `soupCarrying = 100` or (`soupCarrying > 0` and no soup is visible),
  path to the nearest refinery/HQ and deposit; else path to the nearest known soup tile (own vision,
  else the best tile broadcast by `ANNOUNCE_SOUP`), mine it, and broadcast `ANNOUNCE_SOUP` the first
  time it sees a deposit of ≥ 200. One miner is elected **builder** (lowest id alive) and builds, in
  this order and only when the team pool can afford it without stalling miner production: 1 Design
  School at Chebyshev 2 from the HQ on the side away from the water; `net_gun_ring` Net Guns on the
  HQ ring; 1 Fulfillment Center; `vaporator_budget` Vaporators inside the lattice; a second Design
  School after round 600. Every miner flees a tile that will flood next round
  (`elevation < waterLevel(round + 1)`).
- **Design School** (`designschool.nim`): build a Landscaper whenever
  `landscapersAlive < landscaperTarget(round)` and soup ≥ 150, preferring a direction on the HQ side.
- **Landscaper** (`landscaper.nim`): three modes, in priority order. **(a) Wall**, from round
  `wall_hq_round`: claim the lowest of the 8 tiles adjacent to the own HQ, dig from a tile *outside*
  the lattice and deposit onto the claimed tile until it is `waterLevel(round + 400) + 2` or higher;
  when every ring tile clears that bar, emit `wall_closed` and drop to (b). **(b) Terraform**, from
  `terraform_start_round`: pick the lowest tile within `lattice_radius` of the HQ that is below
  `waterLevel(round + 250) + 1` and raise it, keeping the checkerboard parity Bowl of Chowder used so
  units can always path through the lattice. **(c) Attack**: if an enemy building is adjacent, deposit
  onto it every turn; a landscaper delivered next to the enemy HQ digs the enemy wall down and then
  buries the HQ. Any landscaper on a tile that floods next round moves first and digs second.
- **Fulfillment Center** (`fulfillment.nim`): build a Delivery Drone whenever
  `dronesAlive < 4 + round/300` (capped 14) and soup ≥ 150, and always when `NEED_DRONES` is on the
  chain.
- **Delivery Drone** (`drone.nim`): behaviour selected by `drone_role` (table above). Every role
  avoids tiles within `r² ≤ 15` of a known enemy Net Gun or enemy HQ unless carrying a landscaper to
  the enemy HQ; a carried unit is always dropped on the nearest flooded tile that is not adjacent to
  a friendly building.
- **Net Gun** (`netgun.nim`): shoot the closest enemy drone within `r² ≤ 15`, preferring one that is
  carrying a unit.
- **Signalling** (`signals.nim`): messages are 7 ints — `[SIGNAL_KEY, teamOrdinal, code, p0, p1, p2,
  p3]` — submitted at a fee of `max(1, teamSoup/200)` and only when `teamSoup > 120`, so the
  blockchain never starves the build. `SIGNAL_KEY` is a fixed constant shared by both teams, which is
  deliberate: it reproduces the year's famous meta-gaming vector and it is what lets the endcard
  decode both sides' traffic (§Viewer).
- **Pathing** (`pathing.nim`): the bug-walk-with-BFS-window Bowl of Chowder used — a bounded BFS over
  the sensed window (r² 24 or 35 by unit), falling back to a wall-follow when the target is outside
  it, with a 6-tile no-repeat history to break oscillation. Charged against `DecisionOps`.

This baseline satisfies the D2 survival gate by construction: it walls, it gunners, it terraforms,
and `tests/test_bc20_baselines.nim` proves it (§Tests item 10c). It does not idle to a win — its
opponent in the gate is the scaffold, which *acts* and merely drowns.

**`examplefuncsplayer` — the weak floor and the parity oracle's other side.** Ported
**statement-for-statement** from `battlecode20/example-bots/src/main/examplefuncsplayer/RobotPlayer.java`:
the HQ tries to build a Miner in each of the 8 directions in order; a Miner submits a 7×`123`
transaction at fee 10 on each of its first two turns, tries two random moves, tries to build a
Fulfillment Center in each direction, then tries to refine and then to mine in each direction; a
Fulfillment Center tries to build a Drone in each direction; a Drone picks up the first enemy unit
within `r² ≤ 3` or else moves randomly; Refinery, Vaporator, Design School, Landscaper and Net Gun do
nothing. **It may not gain behaviour** — it is one side of the differential oracle, exactly as bc26's
`scaffold.nim` is. Its scripted reply is the all-defaults sheet (no knob it reads).

Both replies go through the **same** `validate` the LLM path uses, which is what makes the
bounded-orders test meaningful and an LLM doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `bowl-of-chowder` chassis, `results.fallbacks[seat] = 1`, a `doctrine_fallback` event names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default; the rest of the sheet applies |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| a side takes 2 games | the episode settles immediately — no padding |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `bowl-of-chowder` baseline reply:

```json
{"sheet":{"opening":"passive_lattice","terraform_start_round":300,"lattice_radius":6,
          "landscaper_count_curve":"steady","miner_count_curve":"steady","vaporator_budget":2,
          "drone_role":"harass","net_gun_ring":2,"rush_trigger":0,"wall_hq_round":250},
 "notes":"default bowl-of-chowder doctrine","motto":"Soup first."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc20/constants.nim` | **new, generated** | every `GameConstants` value + the `RobotType` table, emitted by `tools/gen_year_constants.py --year bc20` from the pinned battlecode20 checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc20/world.nim` | **new** | world state, the grid (elevation, flood, soup, pollution), robots, `TeamInfo`, spawn/destroy, and every action of rule 6 |
| `src/battlecode/years/bc20/rules.nim` | **new** | the round loop (rules 1–9), the end-of-match ladder, the points formula |
| `src/battlecode/years/bc20/flood.nim` | **new** | the water-level table lookup, `floodfill`, `tryResurface`, drown resolution |
| `src/battlecode/years/bc20/pollution.nim` | **new** | global pollution, the per-robot local additive/multiplicative registry, the cooldown and sensor coefficients |
| `src/battlecode/years/bc20/blockchain.nim` | **new** | the transaction pool, `Transaction.compareTo`, per-round minting, fee accounting, the re-seeded transaction-id RNG |
| `src/battlecode/years/bc20/cows.nim` | **new** | the NPC cow provider, including the per-spawn symmetry recomputation |
| `src/battlecode/years/bc20/maps.nim` | **new** | the converted bc20 pool, the loader, the per-episode draw (`drawMaps`, `sideAslotFor` reused from the bc26 shape) |
| `src/battlecode/years/bc20/knobs.nim` | **new** | the ten-knob `Doctrine20` type, defaults, per-field repair, `toJson`, `plainWords` |
| `src/battlecode/years/bc20/chassis/*.nim` | **new** | `boc.nim`, `scaffold.nim`, `hq.nim`, `miner.nim`, `designschool.nim`, `landscaper.nim`, `fulfillment.nim`, `drone.nim`, `netgun.nim`, `lattice.nim`, `pathing.nim`, `signals.nim`, `kit.nim` |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc20", title: "Battlecode 2020 — Soup", maxRounds: 1500, pools: @["small","mixed","large"], atlas: "atlas_bc20")` |
| `src/battlecode/years/dispatch.nim` | **new** | the **only** place a `case year` appears: `sheetFor(year, text)`, `baselineFor(year, name)`, `playGameFor(year, …)`, `spritesFor(year, …)` |
| `src/battlecode/sheet_common.nim` | **new (extracted)** | `normalizeKey`, `readNumber`, `readBool`, `extractJsonObject`, `sanitizeLine`, the rune/byte caps — moved out of `sheet.nim` unchanged |
| `src/battlecode/sheet.nim` | **thinned** | the year-neutral `Sheet` envelope (`notes`, `motto`, `defaultsApplied`, `unknownFields`, `submitted`, `knobsJson`) and a dispatcher into `years/<year>/knobs.nim`. bc26's `Doctrine` type, its defaults, its `validate` body and its `plainWords` **move verbatim** into `years/bc26/knobs.nim` (minus the `chassis` branch, which D1 deletes). No bc26 semantics change. |
| `src/battlecode/baselines.nim` | **year-aware** | `baselineFor(year, name)`; bc26 `awu`/`scaffold`, bc20 `bowl-of-chowder`/`examplefuncsplayer` |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc20 adds elevation shading and the flood overlay |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc20 scorebug / feed / endcard shell records |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port and `IDGenerator` already carry everything bc20 needs |
| `data/maps/bc20/*.json` | **new, committed** | 18 converted maps |
| `data/bc20/water_levels.json` | **new, committed** | the 1500-entry float32 water-level table (below) |
| `data/atlas_bc20.png` / `.json` | **new, committed** | the 2020 sprite atlas |
| `tools/convert_maps.py` | **`--year bc20` added** | reads `.map20` and writes `data/maps/bc20/<name>.json` |
| `tools/gen_year_constants.py` | **`--year bc20` added** | reads the 2020 `GameConstants.java` + `RobotType.java` |
| `tools/build_sprite_atlas.py` | **`--year bc20` added** | cuts `atlas_bc20.*` from the 2020 client sprites |
| `tools/JavaWaterLevels.java` | **new, CI-only** | regenerates `data/bc20/water_levels.json` under the CI JDK |
| `tools/oracle/examplefuncsplayer20/RobotPlayer.java` | **new, CI-only** | the deterministic oracle bot (below) |
| `tools/parity_trace_bc20.nim` / `.py` | **new, CI-only** | the two sides of the bc20 parity trace |

### Determinism

- **`rng.nim` is reused unchanged.** bc20 needs `java.util.Random` in four places, all already
  covered by the existing port: `IDGenerator(mapSeed)` (48-bit LCG + `nextInt(bound)` with both the
  power-of-two shortcut and the rejection loop + the Fisher–Yates block shuffle, `ID_BLOCK_SIZE 4096`,
  `MIN_ID 10000`), the transaction-id RNG, the cow RNG (`nextDouble`), and the CI oracle bot's RNG.
  Robot ids therefore match the Java engine's for a given map seed, which is what makes the parity
  trace comparable row for row.
- **The transaction-id RNG quirk.** `RobotControllerImpl.random` is a `private static Random`
  assigned `new Random(gameWorld.getMapSeed())` **in the constructor**, so it is re-seeded every time
  a robot controller is constructed — on every spawn, and on the two HQs and every cow at map load.
  The port reproduces this exactly, because it decides the minting order among equal-fee
  transactions.
- **The world RNG** is seeded from the map's own `randomSeed` field, exactly as the engine does. The
  episode seed selects maps and side assignment, never the world RNG.
- **`setWinnerArbitrary`'s `Math.random()`** is replaced by a draw from the world RNG (a documented
  divergence; reachable only when neither team has a living robot).
- **The water level is a committed table, not a formula.** `getWaterLevel` uses `Math.exp` and
  `Math.sin`, which HotSpot implements as intrinsics that are *not* bit-identical to any libm we
  would link natively or under emscripten. Since the function depends only on the round number,
  `tools/JavaWaterLevels.java` emits `data/bc20/water_levels.json` — rounds 0…1500, each value the
  **float32 bit pattern** as an 8-digit hex string — under the CI JDK, and the sim (native and wasm)
  reads that table. The table is committed and CI regenerates and diffs it. Bit-exact against Java by
  construction, on every platform, with no libm in the loop.
- **All cooldown, pollution and sensor arithmetic is float32**, matching Java `float`, and
  `Math.round(float)` is implemented as `floor(x + 0.5)`. The pollution coefficients keep their
  closed forms; the `parity-oracle` job proves them equal to Java over the whole integer domain
  `P ∈ [0, 65535]` in a JDK-only step (§Tests).
- Every round appends to a **hash chain**; the viewer re-derives each round and compares, exposing
  `bc_mismatch_round`. The seven per-team values entering the bc20 chain each round: team soup, soup
  refined, living robots, net worth, dirt moved, transactions minted, and living-HQ flag; plus the
  three global values global pollution, flooded-tile count and the water-level bit pattern.
- Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
  (`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
  scar — and the record→re-derive test covers **every** bc20 end reason, not just `complete`.
- **`GameVersion` bumps to `GV04`** in the same commit, with a prepend-only changelog line ("bc20
  year module added; bc26 semantics unchanged"). `ReplayCompatibleGameVersions` becomes
  `["GV03", "GV04"]` — nothing a GV03 replay carries changed meaning, so every hosted bc26 replay
  keeps rendering. `tools/ci/check_gameversion.sh` is kept and claims the version across branches,
  not just against `main` (the sibling run is live on the same repo).

### The chassis, and the bytecode divergence

The engine's per-robot **bytecode limit** (`RobotType.bytecodeLimit`: HQ 20 000, units 10 000, Net
Gun 7 000, other buildings 5 000, Cow 0) has no meaning outside the JVM instrumenter. It is replaced
by a **fixed per-robot `DecisionOps` budget at one tenth of the Java limit**: HQ 2000; Miner,
Landscaper, Delivery Drone 1000; Net Gun 700; Refinery, Vaporator, Design School, Fulfillment Center
500; Cow 0 (the engine's own cow provider reports 0 bytecodes). One credit is charged for each: tile
sensed, robot examined in a sense sweep, BFS node expanded, direction evaluated, and block read.
Credits are deducted inside `pathing.nim` / `kit.nim` and **enforced by the sim, not by the bot**.
When the budget reaches zero the robot's turn ends where it stands — it is **not** resumed mid-computation
next turn, which is the one place this differs from the JVM. This makes per-round cost bounded,
machine-independent and deterministic.

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to
Java bytecode granularity would require either a Nim-level instrumenter (a compiler project) or
hand-annotating every statement with the `MethodCosts.txt` table, and neither buys anything the
budget does not — the chassis are ours, they are written to fit the budget, and the *oracle* runs the
one bot that provably never approaches the Java limit anyway. See "What parity means" below.

### Maps

**18 of the 52 official maps** are converted and committed. Sizes, seeds and symmetry below were read
out of the real `.map20` flatbuffers, not assumed.

| pool | maps (size, symmetry — **engine naming**) |
|---|---|
| `small` (6) | `maptestsmall` 32×32 vertical, `WateredDown` 32×32 horizontal, `Infinity` 33×33 rotational, `Spiral` 33×33 rotational, `Hourglass` 40×32 horizontal, `ALandDivided` 41×32 vertical |
| `mixed` (12, **the `bc20` variant's pool**) | the six above + `Climb` 40×40 rotational, `Constriction` 40×40 rotational, `CentralLake` 41×41 rotational, `Toothpaste` 45×37 rotational, `TwoLakeLand` 45×45 horizontal, `CentralSoup` 48×48 rotational |
| `large` (6, reserved for a later variant) | `Hills` 60×60 rotational, `OmgThisIsProcedural` 60×64 vertical, `Squares` 63×63 vertical, `BeachFrontProperty` 64×64 rotational, `Maze` 64×64 rotational, `TheHighGround` 64×64 rotational |

`CowFarm` and `DidAMonkeyMakeThis` are deliberately excluded: both carry tiles at
`Integer.MAX_VALUE/2` elevation, which is legal but makes the elevation shading meaningless and the
timing untypical. `maptestsmall` is kept despite carrying soup on all 1024 tiles because it is the
map the parity oracle and the fast smoke run on; the anomaly is noted in `docs/RULES-BC20.md`.

**Symmetry is not in the file.** The 2020 `.map20` schema has no symmetry field, so the converter
**detects** it exactly the way the engine does (`CowControlProvider.getSymmetry`): candidates in the
order **`vertical`, `horizontal`, `rotational`**, each eliminated by the first tile where soup,
elevation or robot type disagrees under that transform, first survivor wins, default `rotational`
when none survives. Engine naming: `vertical` flips x (`symmetricX = w−1−x`), `horizontal` flips y
(`symmetricY = h−1−y`), `rotational` flips both. `Squares` survives all three and therefore records
`vertical`, which is what the engine picks. `tests/test_bc20_maps.nim` asserts the committed value
against a fresh detection and asserts that the sim's own per-spawn recomputation agrees with the
engine's on round 1.

`tools/convert_maps.py --year bc20` writes `data/maps/bc20/<name>.json` carrying: `name`, `width`,
`height`, `symmetry`, `random_seed`, `initial_water` (the map's `initialWater` int), `elevation` (the
`dirt` int array), `water` (the bool array of initially flooded tiles), `pollution`, `soup`, and
`initial_bodies` (id, team, type, x, y — 2 HQs plus the cows). The converted maps are **committed**
and CI re-converts and diffs. The wasm bundle gets the same directory through the existing
`--preload-file data@data`.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from
the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot
takes side A in game 1; sides alternate each game. Seed, map names and side assignment are recorded
in results and in the replay.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `sheet_common`, `sheet`,
`decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never branches on the
year except through `years/dispatch.nim`. Adding 2020 is exactly what the bc26 note promised adding
2027 would be: a new `years/bc20/` directory, a converted map set, a sprite atlas, one registry line,
one dispatch entry and one manifest variant. The replay header records `year` so a viewer can never
mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol
id would force every existing bc26 consumer to re-register for no change in the contract. Both
`game.protocols.player` and `game.protocols.global` continue to point at `docs/PROTOCOL.md`, which
gains a bc20 section.

### The player container (thin registrar) — unchanged

`/bin/battlecode-player` reads `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dials
its seat with a bounded retry (240 × 500 ms), sends **one** registration blob and then only receives
until the socket closes, then exits 0:

```json
{"type":"register","prompt":"<PLAYER_PROMPT or empty>",
 "scripted":"bowl-of-chowder"|"examplefuncsplayer"|"awu"|"scaffold"|null,
 "policy":"<PLAYER_POLICY_LABEL>"}
```

sent as a Sprite v1 chat blob (a **binary** frame — the server must not filter non-text frames) and
re-sent a bounded number of times until acknowledged. The seat token is a **credential** and a wrong
one is refused (commit `d581704`). A seat that sets neither env var takes the active year's default
baseline. A seat whose registration never arrives is logged loudly and reported to
`COGAME_PLAYER_FAILURE_URI`.

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV04","year":"bc20",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":871345,
 "games":[{"map":"CentralLake","width":41,"height":41,"symmetry":"rotational",
           "you_are":"A",
           "hq_elevation":4,
           "hq_separation":34,
           "soup_tiles":50,"soup_total":24800,"soup_near_hq":3100,
           "cows":4,
           "initially_flooded_tiles":118,
           "rounds":1500},
          {"map":"Constriction","…":"…","you_are":"B"},
          {"map":"maptestsmall","…":"…","you_are":"A"}],
 "flood_table":{"1":256,"2":464,"3":677,"4":931,"5":1210,"6":1413,"7":1546},
 "rules_digest":"<~7 KB condensed spec: flood, soup and refining, the seven build types, dig/dump and elevation, drone carry and drop, net guns, pollution, the blockchain and its fee model, the end ladder>",
 "sheet_schema":{"…all ten knobs, their values, ranges and defaults…"},
 "scoring":{"weights":{"hq_survival":60,"unit_share":25,"net_worth_share":15},
            "win_bonus_per_game":100,"games":3,
            "note":"shares are float32; points truncate to an integer"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards *with the seat's own HQ
starting elevation and the HQ separation*, the seed, the flood table (which round each elevation
floods at), the full knob surface with defaults, the scoring weights, the deadlines. Because every
map is symmetric, both seats see numerically identical map cards; `you_are` is the only asymmetry.
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in
either direction, at any time); the opponent's real player name (only the alias); every in-match
state (a cog receives **no** per-round observation — one sealed doctrine, then the war); the other
seat's fallback status. The only cross-team channel inside a match is the sim's own blockchain and
what a robot can see.

### Reply schema and caps

```json
{"sheet":{"opening":"rush","terraform_start_round":420,"lattice_radius":3,
          "landscaper_count_curve":"swarm","miner_count_curve":"lean","vaporator_budget":0,
          "drone_role":"harass","net_gun_ring":1,"rush_trigger":240,"wall_hq_round":300},
 "notes":"Bury them by 400; if it stalls, wall at 300 and lattice out.",
 "motto":"Soup is for the patient."}
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
(`runeLen`/`runeSubStr`; the reply's 16 KB cap is measured in bytes but still cut on a rune
boundary — commit `a8684c0`): byte-slicing a multi-byte character renders fine in a browser and then
fails a strict UTF-8 parser, which is exactly what makes a replay unreadable to everything but one
lenient viewer.

### Results document

The closed schema is **shared with bc26** and stays that way. The only change is that the
year-specific per-game statistics move from `required` to optional, so each year emits its own:

- `results.games[].` **required** (year-neutral): `map`, `side`, `rounds_played`, `winner`,
  `end_reason`.
- `results.games[].` **optional**: bc26's existing eleven keys, unchanged and still emitted by bc26;
  plus bc20's keys below. The two sets do not collide. `end_reason`'s enum becomes the union of both
  years' values plus `abandoned`. This is deliberately *not* a nested `stats` object: nesting would
  change the bytes every shipped bc26 replay's `result` block carries and force a compatibility shim
  in the endcard. Relaxing `required` changes nothing that already exists.

bc20's per-game keys, each a 2-array in **seat** order unless marked scalar: `hq_alive`,
`hq_lost_round` (−1 if alive), `hq_lost_cause` (`buried` \| `drowned` \| `none`), `soup_mined`,
`soup_refined`, `net_worth`, `units_alive`, `units_built`, `miners_built`, `landscapers_built`,
`drones_built`, `vaporators_built`, `net_guns_built`, `dirt_moved`, `drone_pickups`,
`drone_water_drops`, `net_gun_kills`, `transactions_sent`, `transactions_minted`,
`blockchain_soup_spent`; scalars `global_pollution_peak`, `flooded_tiles_end`, `water_level_end`.

Top level, unchanged: `names`, `aliases`, `scores`, `wins`, `points`, `games`, `seed`, `year`,
`policy_kind`, `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`,
`wall_clock_seconds`, `game_version`.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV04","year":"bc20",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm","chassis":"bowl-of-chowder",
           "sheet":{…as applied…},"sheet_submitted":"{…as received…}",
           "sheet_defaults_applied":["lattice_radius"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":8123,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"CentralLake","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":947,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…],"side_a_slots":[…],"abandon_after":[…],"max_rounds":1500},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships), both doctrine sheets, the chassis each
seat drove, and the event list are all in the file, and the wasm sim replays every round from them.
**No `.bc20` bytes, no per-round state dump, no blockchain dump** — the blockchain is a pure function
of the sim, so the browser re-derives it and the endcard reads the re-derived blocks. No server is
contacted except S3 for the `.replay` file. The per-round hash chain lets the viewer prove its
re-derivation matches the recording (`bc_mismatch_round`, surfaced as `data-replay-mismatch-round`
and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`. Ten beat kinds are emitted and
**every one has CSS** (§Viewer).

| `kind` | fields | beat | drawn as |
|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `defaults_applied`, `unknown_fields` | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides` | `game` | beat + feed |
| `flood_stage` | `game`, `round`, `level` (int 1…7), `water_level`, `flooded_tiles` | `flood` | beat + feed ("water reaches elevation 3") |
| `first_build` | `game`, `round`, `alias`, `unit` (`design_school`\|`landscaper`\|`fulfillment_center`\|`drone`\|`vaporator`\|`net_gun`) | `build` | beat + feed |
| `wall_closed` | `game`, `round`, `alias`, `min_ring_elevation` | `wall` | beat + feed |
| `rush_launched` | `game`, `round`, `alias`, `units` | `rush` | beat + feed |
| `drone_water_drop` | `game`, `round`, `alias`, `victim_alias`, `victim_unit` | `drop` | beat + feed |
| `hq_buried` | `game`, `round`, `alias` (victim), `by_alias`, `dirt` | `bury` | **chapter marker** |
| `hq_drowned` | `game`, `round`, `alias` (victim), `water_level` | `drown` | **chapter marker** |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points` | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | `end` | beat + feed |
| `episode_end` | `reason` | — | endcard |

`flood_stage` is emitted once per integer level reached, so a 1499-round game emits at most 6 of
them; `first_build` is emitted once per team per unit kind. The whole event list for a three-game
match is a few hundred entries.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc20/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.bc20` bytes, no 2020 TypeScript
client.

### All four viewer files come from ONE starter: `cogame-battlecode` (its own shipped bc26 viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` → `cogame-battlecode` → here.

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** The `--preload-file {rootDir}/data@data` flag already carries the whole `data/` tree, so `data/maps/bc20/`, `data/bc20/water_levels.json` and `data/atlas_bc20.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. Splicing an `onRuntimeInitialized` bootstrap onto `MODULARIZE`/`EXPORT_NAME` link flags is the cogame-lantern 2026-08-23 silent deadlock; all four files here come from this one starter and none of the four changes its loader. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc20 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and no existing id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and byte-for-byte: **`client/chrome_common.js`** and **`client/broadcast_core.js`**
(their sha256 is already asserted against the coworld-ctf copies in `tests/test_viewer.nim`, and that
assertion stays green because neither file is touched). `wire_constants.js` is regenerated from the
sim by `tools/gen_wire_constants.nim`, as today.

### The appended bc20 game block

**No starter element is removed.** The bc26 block's elements (`#coopchip`, `#bars`, `#gamechips`,
`#econ`, `#doctrines`) stay exactly where they are; the bc20 block adds its own, with ids that are all
new and all prefixed:

- `#bc20-flood` — the water readout: the water level to 2 dp, a flood ring gauge (percentage of the
  map under water), and `HQ elev N / water M` per clan, flashing red when `water ≥ HQ elevation − 1`.
- `#bc20-soup` — team soup pools, plus soup mined and refined per clan.
- `#bc20-units` — per clan, counts by type (Mi / La / Dr / Va / NG / DS / FC) and the HQ's dirt load
  as `dirt/50`.
- `#bc20-doctrines` — both sheets in plain words, **dismissible** (D3): a `#bc20-doctrines-close`
  button with `aria-label="Dismiss doctrines"`, an `Escape` binding, and a `#bc20-doctrines-toggle`
  chip in the scorebug that re-opens it. It sits above the board area and **never** inside the
  transport band.
- `#bc20-chain` — the blockchain panel on the endcard (below).

Year selection is one attribute plus CSS, not a rewrite: `static_replay.js` sets
`document.documentElement.dataset.year` from the replay header, and the stylesheet hides
`[data-year="bc20"] #coopchip, [data-year="bc20"] #bars, …` and `[data-year="bc26"] #bc20-*`.

### Zoom: KEEP `#viewpanel`

The bc20 variant's pool tops out at 48×48 and the reserved large pool at 64×64. The native board
render is 16 px per tile, so 768–1024 px wide — **larger than the 360 px featured-match frame**, where
a 48×48 board would give 7.5 px per tile. So the inherited `#viewpanel` (zoom bar + minimap, with
`?viewpanel=0` still honoured for thumbnail capture) is **kept**, wired to the same
`zoomAt/setZoom/panBy/panTo/resetView` core API the worker already forwards. The default view is
fit-to-board, so a spectator who touches nothing sees the whole map and the flood front.

### Transport rules

- `relayout()` (inherited, kept) sets **`--hudscale`**, **`--topband`** and **`--band`** on `:root`,
  iterating to a fixed point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport). `#bc20-doctrines` and `#bc20-chain` are explicitly excluded
  from that band.
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`
  ("HQ BURIED — Clan Ash, game 2, round 947"), built by a bc20-block function with its **own** name,
  `buildBc20BeatButtons` — never `markBeat` (the tandem 2026-08-23 hoisting collision) and never
  colliding with the bc26 block's `buildBeatButtons`. CSS exists for **every kind emitted**:
  `.beat-marker.doctrine`, `.game`, `.flood`, `.build`, `.wall`, `.rush`, `.drop`, `.bury`,
  `.drown`, `.end`.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`
  (relabelled **+25 rounds**), `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`,
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

`data/atlas_bc20.png` + `data/atlas_bc20.json` (≈ 300 KB, committed), cut by
`tools/build_sprite_atlas.py --year bc20` from the official 2020 client's sprite tree
(`battlecode20/client/visualizer/src/static/img/` at a pinned commit), verified present:
`HQ_{red,blue}.png`, `Miner_*`, `Landscaper_*`, `Drone_*` **and `Drone_*_carry`**, `Refinery_*`,
`Vaporator_*`, `SOUPER_*` (the Design School), `Fulfillment_*`, `Net_gun_*`, `Cow.png`, and
`soup.png`. Credited in `NOTICE`. Palette follows the engine side, not the seat: **red = side A,
blue = side B**, and because sides alternate each game the scorebug plate keeps the *alias* constant
and recolours its swatch per game. It looks like Battlecode 2020 because it **is** Battlecode 2020's
art.

Board rendering (`render.nim`): each tile gets a nine-step elevation ramp keyed to the *current* water
level (so the lattice reads as terrain rising out of the sea, not as a static heightmap), a water
overlay on flooded tiles, and a soup dot sized by the tile's remaining soup. Drones draw the `_carry`
frame while holding. The HQ draws a dirt-fill ring at `dirt/50`.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else).

- `#scorebug`: both clan plates — `CLAN ASH` over the real player name (`daveey`) and the motto — the
  live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 947 / 1500`, `game 2 of 3 — CentralLake`.
- `#bc20-flood`, `#bc20-soup`, `#bc20-units` as above.
- `#board`: elevation shading, the flood, soup, all seven building types, miners/landscapers/drones,
  cows, and the drone carry frame.
- `#bc20-doctrines`: each sheet in plain words ("rushes at round 240", "walls at 300", "lattice
  radius 3", "swarm landscapers", "no vaporators", "drones harass"), plus the capped `notes` and a
  fallback badge when a seat's doctrine came from the fallback sheet. Dismissible.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured).
- `#endcard`: winner alias **and** real name; the win condition in plain words ("Clan Basil buried
  Clan Ash's HQ at round 947 under 50 dirt" / "Clan Ash's HQ drowned at round 1103, water 4.71" /
  "round limit — Clan Basil held 41 robots to 28"); the per-game score line; the economic story
  (soup refined, landscapers built, dirt moved, drones downed, enemies dropped in the water per
  clan); and `#bc20-chain`, the **blockchain panel**: per clan, transactions minted, soup spent on
  fees, the highest fee paid and the round it bought, and the **last five minted messages decoded to
  plain words** through the chassis's own signal table ("Clan Ash, round 612 — WALL_IN"). Messages
  whose first int is not `SIGNAL_KEY` are shown as raw ints. Nothing about the chain is stored in the
  replay: the wasm sim re-derives every block.

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`,
  `player` → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar). One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe (nimby 0.1.26, Nim 2.2.4) builds
  `/bin/battlecode` and `/bin/battlecode-player` from one image and copies `data/` (now carrying
  `maps/bc20/`, `bc20/water_levels.json` and `atlas_bc20.*`). **No JDK, no JRE, no Java, no node in
  any runtime stage** — the 2020 engine's toolchain exists only in the `parity-oracle` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc20 game block along
  with the bc26 one.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — rewritten to lead with the coworld rather than one year: *"Battlecode,
    played by doctrine. Two cogs each write one sealed JSON strategy sheet and a deterministic Nim
    port of an official Battlecode rule set plays the whole match from those two sheets. Variant
    `bc26` is 2026 'Uneasy Alliances' — rat clans allied against NPC cats until one of them betrays.
    Variant `bc20` is 2020 'Soup' — the water rises every round, and a team either terraforms its way
    above the flood, walls its HQ in, or buries the enemy's under fifty units of dirt."*
  - `tags` unchanged (already ≥ 3: `battlecode`, `strategy`, `mixed-motive`, `wasm`).
  - `game.config_schema`: `year.enum` becomes `["bc26", "bc20"]`. `pool.enum` is unchanged
    (`small` / `mixed` / `large`; each year owns its own pool table). `maxRounds` keeps
    `minimum 50, maximum 2000` (bc20's 1500 fits). `gamesPerMatch` keeps `maximum 3`. Every array
    keeps `minItems`/`maxItems`; no runner-managed `tokens` inside any `game_config`.
  - `game.results_schema`: `games.items.required` narrowed to the five year-neutral keys, bc26's
    eleven keys kept as optional properties, bc20's keys added as optional properties, `end_reason`'s
    enum extended to the union (§Server, player, protocol).
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":".../blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":".../blob/main/README.md"}`; `pages` gains one
    entry and keeps the three it has: `rules.md` (Rules, knobs and deliberate divergences — bc26 →
    `docs/RULES.md`), **`rules-bc20.md`** (Battlecode 2020 "Soup": rules, knobs and divergences →
    `docs/RULES-BC20.md`), `replay.md` (→ `docs/REPLAY.md`), `parity.md` (→ `docs/PARITY.md`, which
    gains a bc20 section).
  - `player[]` gains two entries beside `awu` and `scaffold`, all four `image: {{PLAYER_IMAGE}}`,
    `run: ["/bin/battlecode-player"]`, `resources.limits.cpu: "1"`:
    - `bowl-of-chowder` — "Bowl of Chowder baseline (2020) — passive lattice, ported behaviour",
      `env: {"PLAYER_SCRIPTED":"bowl-of-chowder","PLAYER_POLICY_LABEL":"bowl-of-chowder"}`
    - `examplefuncsplayer` — "scaffold baseline (2020) — the ported example bot, weak",
      `env: {"PLAYER_SCRIPTED":"examplefuncsplayer","PLAYER_POLICY_LABEL":"examplefuncsplayer"}`

  **Variants — one per Battlecode year:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | `year: "bc20"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 1500`, `num_agents: 2`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 100`, `matchBudgetSeconds: 320`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false`).

  **Certification fixture — UNCHANGED, and stays on bc26.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, `"num_agents": 2` and its existing fast settings. There is **no bc20
  certification fixture in v1** (§Out of scope): certification is the platform's contract check, it
  already passes on bc26, and re-pointing it at a brand-new year module would put the release at the
  mercy of the newest code for no gain. bc20 is proven instead by its own `docker-smoke` episode
  (§Tests), which produces a real bc20 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  `0.1.x → 0.2.0` — because it adds a variant and adds optional results properties without changing
  any existing behaviour. The release is dispatched through the existing `coworld-release.yml` with
  the same step order (build → certify → upload-policies → upload-coworld → secret put). **Certify
  runs against bc26, exactly as before**, and `release-result.json` must still show `canonical: true`
  and `certify.replay_liveness` containing `skipped (static replay bundle declared`.

- **`tools/ci/policies.json`** gains the bc20 set beside the bc26 set (a scripted champion is a
  failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-bc20-latticer","run":"/bin/battlecode-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"latticer"}},
   {"name":"battlecode-bc20-rusher","run":"/bin/battlecode-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"rusher"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-bowl-of-chowder","run":"/bin/battlecode-player",
    "env":{"PLAYER_SCRIPTED":"bowl-of-chowder","PLAYER_POLICY_LABEL":"bowl-of-chowder"}},
   {"name":"battlecode-examplefuncsplayer","run":"/bin/battlecode-player",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer","PLAYER_POLICY_LABEL":"examplefuncsplayer"}}]
  ```
  Champion #2 is uploaded while `daveey-1` is the active player. LLM credentials reach the **game**
  container through the manifest env; the player pods need no Bedrock sidecar in this lineage.

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **second league**, created beside the bc26 one and touching neither it nor the game's default
league: `league_key` **`bc20`**, `league_name` **`Battlecode 2020 — Soup`**,
`default_variant_id` **`bc20`**, `short_name` **`bc20`** (→ `softmax.com/battlecode/bc20`), its own
two champions (`battlecode-bc20-latticer` owned by daveey, `battlecode-bc20-rusher` owned by
daveey-1), its own two fillers (`battlecode-bowl-of-chowder`, `battlecode-examplefuncsplayer`), and
its own credit pool. Fillers are set **before** the first `trigger-round`.

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged
by the repository itself. `NOTICE` gains two sections and one non-section:

- **`battlecode/battlecode20` — GPL-3.0** (verified: the repository's licence is GPL-3.0, unlike
  battlecode26's AGPL-3.0). Pinned commit recorded. GPLv3 and AGPLv3 are explicitly made compatible
  for combined works (AGPLv3 §13 / GPLv3 §13), so an AGPL-3.0 repo may carry work derived from it;
  the derived files are named individually: `src/battlecode/years/bc20/**` (behaviour, hand-ported),
  `years/bc20/constants.nim` (generated from `GameConstants.java` + `RobotType.java`),
  `data/maps/bc20/*.json` (converted from `.map20`), `data/bc20/water_levels.json` (generated from
  `GameConstants.getWaterLevel`), `data/atlas_bc20.*` (cut from the 2020 client sprites), and
  `years/bc20/chassis/scaffold.nim` (examplefuncsplayer, ported statement for statement — it is the
  parity oracle's other side and may not gain behaviour). **The engine itself is used only at CI
  time**, built from source with JDK 8 + Gradle 6 in the `parity-oracle` job; no JDK, no JRE and no
  upstream Java source exists in any image this repository builds.
- **`StoneT2000/Battlecode2020` — AGPL-3.0.** Pinned commit recorded. What derives from it:
  `years/bc20/chassis/boc.nim` and the modules it calls (`hq`, `miner`, `designschool`,
  `landscaper`, `fulfillment`, `drone`, `netgun`, `lattice`, `pathing`, `signals`). **Behaviour, not
  code** — the passive-lattice build order, the wall-then-terraform landscaper priority, the
  builder-miner election, the drone roles and the signal-code discipline are its ideas, rewritten in
  Nim and parameterised by this coworld's doctrine sheet. None of its Java is copied, compiled or
  shipped.
- **`IvanGeffner/battlecode2020` — NO LICENCE, all rights reserved** (verified: the repository
  declares no licence). It is **not vendored, not ported, not compiled and not read into any file
  here**. It is cited in `docs/RULES-BC20.md` only as the public record of what the year's winning
  archetypes were; the archetype vocabulary in the sheet comes from the published postmortems
  (Stone Tao's and Java Best Waifu's) and from the spec, not from that code.

`docs/RULES-BC20.md` also carries the full **§Divergences** list: (1) no bytecode instrumentation —
a fixed `DecisionOps` budget with no mid-turn resumption; (2) `setWinnerArbitrary`'s `Math.random()`
replaced by a world-RNG draw; (3) `Math.exp`/`Math.sin` in the water level replaced by a committed
JDK-generated float32 table; (4) a 1500-round cap in place of the map's 10 000, applied through the
engine's own `currentRound >= rounds − 1`; (5) no indicator dots or lines, no profiler, no crossplay,
no `.bc20` output; (6) the `deadline` wall-clock stop, which is a coworld concept and not an engine
one, recorded as one load-bearing record; (7) both chassis are behaviour ports parameterised by the
doctrine sheet; (8) 18 of the 52 official maps converted.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, `<SEATS>` = **2**). The sandbox runs none of it; CI is the harness.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc20_flood.nim`** — the committed water table matches
   `GameConstants.getWaterLevel` at the spec's own checkpoints (elevation 1 floods at 256, 3 at 677,
   5 at 1210, 6 at 1413 — the last inside our cap); flood fill expands **exactly one ring per round**
   from the pre-fill snapshot; a non-flying robot on a newly flooded tile dies and a drone does not;
   a deposit that lifts a tile to `elevation ≥ waterLevel` resurfaces it in the same action; the
   initial flooded set comes from the map's `water` array; a drone dropped into water survives and a
   miner dropped into water dies.
2. **`tests/test_bc20_dirt.nim`** — dig lowers an empty/flooded/unit tile by 1 and raises
   `dirtCarrying` to at most 25; dig on a clean building is illegal and on a dirty one removes 1 from
   the building; deposit on a building adds 1 and **destroys it at its health** (HQ 50, others 15),
   releasing that many dirt onto the vacated tile; a dying landscaper drops its carry;
   `MAX_DIRT_DIFFERENCE = 3` gates movement and non-drone building placement but not drones.
3. **`tests/test_bc20_drone.nim`** — pickup radius² 3; only units, never buildings, never drones; the
   held unit is `blocked` (no turn, cooldown frozen) and rides with the drone; drop requires an
   unoccupied on-map tile and destroys a non-drone dropped into water; a dying drone drops its cargo
   on its own tile; a carried cow stops polluting.
4. **`tests/test_bc20_burial.nim`** — 50 dirt on an HQ destroys it, records `destroyHQ`, and the
   end-of-round ladder awards `hq_destroyed` to the other team in the same round; the released 50
   dirt raises the tile; a **double** HQ loss in one round falls through to `quantity`.
5. **`tests/test_bc20_blockchain.nim`** — `cost > 0` and `cost ≤ team soup`, soup deducted at submit;
   exactly 7 ints; ≤ 7 minted per round in comparator order (cost desc, then id desc, then serialized
   message ascending); unminted transactions stay eligible for ever; `blockchainsSent` counts
   **minted**, not submitted; and the transaction-id RNG is **re-seeded with the map seed on every
   robot spawn**, with a vector that fails if it is seeded once.
6. **`tests/test_bc20_pollution.nim`** — global pollution floors at 0; a refinery's local +500 lasts
   exactly one round and is removed at the start of its own next turn; the vaporator's ×0.80 and −1;
   cows' +2000 over `r² ≤ 15`; `Math.round(float)` implemented as `floor(x + 0.5)` in both
   coefficients; a blocked robot still has its pollution reset.
7. **`tests/test_bc20_cows.nim`** — the seed `84307·mapSeed + 20201·(id div 2)`; up to 4 `nextDouble`
   draws when ready with **early exit on a successful move**, exactly 4 when not ready; the odd-id
   direction reversal; symmetry recomputed on every spawn with the candidate order
   `[vertical, horizontal, rotational]` and first-survivor-wins, defaulting to rotational.
8. **`tests/test_bc20_scoring.nim`** — the points formula with float32 narrowing and truncation; the
   tiebreak ladder in the engine's order with a vector for each rung; `roundLimitReached` is
   `round >= maxRounds − 1` (a 1500-round cap plays 1499); every `end_reason` value is producible.
9. **`tests/test_bc20_sheet.nim`** — every one of the ten knobs: absent → default, out of range →
   default + recorded, mistyped → default + recorded; unknown keys recorded (≤ 16, ≤ 40 runes);
   **a submitted `chassis` is recorded as an unknown field and never honoured** (the D1 assertion,
   which fails if anyone re-adds the knob); rune-boundary truncation of `notes`/`motto` including
   astral-plane characters; the 16 KB byte cap cut on a rune boundary.
10. **`tests/test_bc20_baselines.nim`** — bounded orders, legality **and the D2 survival gate**:
    - (a) both `PLAYER_SCRIPTED` values produce a sheet that passes the *same* `validate` the LLM path
      uses — every key known, every value in range, `notes`/`motto` under cap;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the
      moment it is emitted**: `cooldownTurns < 1`, target on the map and in range, elevation
      difference ≤ 3 for non-drones, enough team soup, spawn tile unoccupied and not flooded for
      non-drones, dig legal against the target, 7-int messages with `0 < cost ≤ team soup`; and no
      robot exceeds its `DecisionOps` budget;
    - (c) **the survival gate**: over 3 seeds × 2 `small`-pool maps of `bowl-of-chowder` vs
      `examplefuncsplayer`, the Bowl of Chowder seat must, in **every** one of the 6 games, still have
      a living HQ at round 1499, have built ≥ 10 miners, ≥ 8 landscapers, ≥ 1 design school, ≥ 1
      fulfillment center and ≥ 1 net gun, have moved ≥ 200 dirt, have emitted `wall_closed`, and have
      won. The scaffold seat must **act** — ≥ 1 miner built, ≥ 1 mine action, ≥ 1 minted transaction,
      ≥ 1 drone built — but is **not** required to survive: it is the deliberate weak floor and the
      oracle's other side, and it may not gain behaviour. A baseline that idled to a win fails (a)
      through (c).
11. **`tests/test_bc20_knobs.nim`** — the knob-teeth gate. Paired seeded games (identical seed, map
    and opponent; the two teams identical except that one knob at its low and high setting, 3 seeds
    each), each asserting a named, signed delta. Thresholds live in one table so tuning is a one-line
    change:

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `turtle` → `rush` | first enemy-half friendly unit arrives ≥ 200 rounds earlier |
    | `terraform_start_round` | 900 → 100 | dirt moved by round 700 up ≥ 150 % |
    | `lattice_radius` | 3 → 10 | tiles raised above the water within r = 10 of the HQ up ≥ 60 |
    | `landscaper_count_curve` | `lean` → `swarm` | landscapers built up ≥ 50 % |
    | `miner_count_curve` | `lean` → `swarm` | miners built up ≥ 50 % |
    | `vaporator_budget` | 0 → 6 | vaporators built up ≥ 4 **and** global pollution at round 1000 lower by ≥ 3 |
    | `drone_role` | `carry_landscapers` → `harass` | enemy units dropped into water up ≥ 5 |
    | `net_gun_ring` | 0 → 6 | net guns built up ≥ 4 **and** enemy drones shot down up ≥ 3 |
    | `rush_trigger` | 0 → 220 | a friendly unit stands adjacent to the enemy HQ by round 350 |
    | `wall_hq_round` | 0 → 250 | own-HQ ring tiles ≥ 5 above the round-250 water level up ≥ 6, **and** HQ-drowned games fall from ≥ 4/6 to 0/6 |

12. **`tests/test_bc20_maps.nim`** — every committed bc20 map re-converts identically; sizes and
    symmetry match the pinned table; the sim's per-spawn symmetry detector agrees with the converter
    on round 1; every map has exactly 2 HQs and ≥ 1 tile at `MIN_WATER_ELEVATION`; the elevation,
    water, pollution and soup arrays are all `width × height`.
13. **`tests/test_bc20_perf.nim`** — a full 1499-round game on `CentralSoup` (48×48) with both
    scripted chassis in **≤ 55 s**; failing it means switching `gamesPerMatch` to 1 (§The game).
14. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain,
    twice in one process and across a save/load; and **record → re-derive for every bc20 end reason**
    (`hq_destroyed`, `quantity`, `quality`, `broadcasts`, `highest_id`, `coin_flip`, and the
    wall-clock `abandoned`/`deadline` stop applied by the same proc on both paths).
15. **`tests/test_replay.nim` (extended)** — a bc20 replay document round-trips; a **strict UTF-8
    parse** of the written bytes; the viewer's re-derivation of a recorded bc20 match reproduces the
    recorded per-round hashes; the blockchain re-derives identically from events + config + seed with
    nothing stored.
16. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now year-aware: the results
    key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; `num_agents` present in **both** variants' `game_config` and
    in `certification.game_config`, and **absent** at every variant top level;
    `config_schema.year.enum == ["bc26","bc20"]`; every `config_schema` array bounded; no `tokens` in
    any `game_config`; both `game.protocols` keys and `game.docs.readme` plus **all four** `pages`
    are `{type,value}` objects; and the installed `coworld` CLI's own
    `validate_upload_manifest` / `_load_template_manifest` accepts the template.
17. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on a committed **bc20** fixture replay;
    the bc20 game block shadows no `ChromeCommon` alias and no bc26 game-block name (the tandem
    scar); `chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256;
    the page carries CSS for **all ten** emitted beat kinds; `#bc20-doctrines` carries a dismiss
    control and sits outside `var(--band)`.

### `parity-oracle` job — the 2020 Java engine as a CI-only oracle

The 2020 engine is **built from source** (the idea's pin: `releases.battlecode.org/maven` 403s on
2020 and the GitHub Package Registry needs a token). Steps: `actions/setup-java@v4` with
`distribution: temurin, java-version: "8"`; check out `battlecode/battlecode20` at the pinned commit;
run its Gradle **6** wrapper to build the engine jar (`engine/build.gradle` uses `compile` and links
`$JAVA_HOME/lib/tools.jar`, which is exactly why JDK 8 is required); `pip install flatbuffers` for
the trace reader. **None of this exists in any image.**

**The oracle bot is `examplefuncsplayer`, made deterministic.** The stock 2020 example bot calls
`Math.random()` in `randomDirection()`, which is seeded from the wall clock — so the stock bot is not
reproducible even against itself, and no bit-exact parity is possible with it. `tools/oracle/examplefuncsplayer20/RobotPlayer.java`
is that file **verbatim except for one change**: a per-robot `java.util.Random RNG = new
java.util.Random(rc.getID())` created at the top of `run()`, and the single live `Math.random()` call
site replaced by `RNG.nextDouble()`. The Nim `scaffold.nim` reproduces exactly that stream through
the existing `rng.nim`. The patch is CI-only, is a committed one-hunk diff against the upstream file,
and is documented in `docs/PARITY.md`.

**What "parity" means for CI — stated exactly.** It is an **outcome-and-state** comparison on
**scripted-vs-scripted** matches. **Bytecode counts are not compared and are not emitted by either
side**, because the Nim port meters `DecisionOps` and not JVM bytecodes. `bowl-of-chowder` is **not**
in the oracle: it is a behaviour port with knobs, so it is not statement-identical to the Java bot and
never could be bit-exact — the oracle proves the *engine* is right, and the baselines test proves the
*chassis* is right. Five pairs, all from the bc20 `small` pool: `maptestsmall`, `WateredDown`,
`Infinity`, `Spiral`, `Hourglass`. `tools/parity_trace_bc20.py` reads the `.bc20` flatbuffer with the
schema's Python bindings and `tools/parity_trace_bc20.nim` emits the same trace from the Nim sim; the
job diffs them at three tiers.

- **Tier A (BLOCKING) — rounds 1–60 bit-exact on all five pairs.** Per round, per robot **in exec
  order**: id, type, team, x, y, `cooldownTurns` (float32 printed `%.6f`), `soupCarrying`,
  `dirtCarrying`, `blocked`. Per round, globally: the water level (float32 bit pattern), the flooded
  tile count and the sorted list of tiles that flooded this round, `globalPollution`, team soup A and
  B, and this round's minted block (each transaction's cost and its 7 ints, in minting order).
- **Tier B (BLOCKING) — round 300 agrees exactly on all five pairs.** Winner (if any) and
  `end_reason`, per-team living-robot count, per-team net worth, per-team team soup, per-team
  transactions minted, global pollution, flooded tile count, the water level, and the multiset of
  living robot types per team.
- **Tier C (reported, trended, non-blocking) — the first divergent round of a whole 1499-round
  game**, printed to the job summary with a committed baseline in `docs/PARITY.md`, so a number that
  moves *down* is a visible regression even though it does not fail the job.

Two extra JDK-only steps in the same job, because they need Java and nothing else does:

- **the coefficient step:** a tiny Java program prints `getCooldownPollutionCoefficient(P)` and
  `getSensorRadiusPollutionCoefficient(P)` as float32 bit patterns for **every** `P ∈ [0, 65535]`; the
  Nim closed forms must agree on all 65 536 values. Blocking.
- **the water-table step:** `tools/JavaWaterLevels.java` regenerates `data/bc20/water_levels.json`
  and the job byte-diffs it against the committed file. Blocking.

Tiers A and B and both extra steps are the **phase-30 gate**. Every accepted divergence is listed in
`docs/RULES-BC20.md` §Divergences with its reason.

### `docker-smoke` job — now **two** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely
from `certification.game_config.num_agents` and hard-fails if the workflow's `<SEATS>` disagrees):

1. **The bc26 certification-fixture episode**, exactly as today → `dist/smoke/replay.json`.
2. **A bc20 episode**, new, with `year: "bc20"`, `pool: "small"`, `seed: 3`, `gamesPerMatch: 1`,
   `maxRounds: 300`, `perGameBudgetSeconds: 40`, `matchBudgetSeconds: 45`, `connectTimeoutMs: 15000`
   and the two seats on `PLAYER_SCRIPTED=bowl-of-chowder` and `PLAYER_SCRIPTED=examplefuncsplayer`
   → `dist/smoke/replay-bc20.json`.

Both episodes run one game container + two player containers on a shared network with `file://`
artifact URIs and **no** `ANTHROPIC_API_KEY`, so both seats take the scripted path and must still
complete. Both assert: game exits 0, **every player container exits 0**, `results.json` carries
exactly the expected key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`,
and the replay parses as **strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the right
`year`, and a non-empty `events` array. Both replays are uploaded as the `smoke-replay` artifact.
A 300-round bc20 game plays for ~20 s at the default pace, so the replay outlasts the 10 s viewer
soak (the ecos 2026-08-23 scar).

### `wasm-viewer` job — the bundle is **executed**, against **both** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay> --timeout 90
--soak 10` in headless chromium (Playwright pinned 1.55.0) **once per replay** —
`dist/smoke/replay.json` and `dist/smoke/replay-bc20.json`. Each run requires
`data-replay-loaded="true"` (or the bridge `ready` posted after it), three **differing**
clock/scorebug readouts at 0 % / 50 % / 100 %, continued advancement across the soak,
`scrub_selector == "#scrub"` (so a seek was really exercised and the `#viewpanel` zoom slider was not
clicked instead), and `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line.
`--strict-text-bounds` stays deliberately dropped here because the board is pannable and zoomable
(`#viewpanel` is kept), which is the exact case the flag's own documentation excludes; the
`canvas_text` counts are still recorded in `viewer-smoke.json`, and the separate
`tools/ci/renderer_fixture.html` step — full-cap `notes` and `motto` on both seats at three widths
including **360 px**, in the page's own CSS extracted from `client/replay_broadcast.html` — runs
through the same harness with `--strict-text-bounds`, because every CI replay is scripted and carries
no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a bc20 row.
`node tools/wasm_replay_smoke.cjs` is also run against the bc20 replay, so wasm32-only failures
(int overflow traps, address-space exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation
  of anything a cog sends. The 2020 engine exists only in the `parity-oracle` CI job.
- **Full bytecode metering.** The `DecisionOps` budget replaces it, with no mid-turn resumption. A
  Nim-level instrumenter is a compiler project and buys nothing the oracle does not already prove.
- **A cog-authored Java (or any) strategy class.** The idea's UPDATE makes doctrines **JSON-sheet
  only**; there is no `javac`, no instrumenter `Verifier`, no compile-error round trip and no
  3-attempt loop. Nothing in the schema is closed against a future sandboxed hook.
- **A bc20 certification fixture.** Certification stays on bc26 (idea UPDATE 22:05Z). bc20 is proven
  by its own `docker-smoke` episode and the viewer smoke run against that episode's replay.
- **34 of the 52 official maps.** The converter handles any `.map20`; v1 commits the 18 whose sizes,
  symmetry and timings are pinned in this note. `CowFarm` and `DidAMonkeyMakeThis` are excluded on
  purpose (Integer.MAX_VALUE/2 plateaus).
- **The official 2020 TypeScript client, `battlecode-playback`, and `.bc20` flatbuffers in the
  browser.** Its *sprites* are reused (credited); its webpack app is not shipped, not embedded and
  not built. No `match_b64` field exists.
- **Bowl of Chowder's `rush/` and `quiet/` variants and the Chow7–Chow10 lineage** as separate
  baselines. One BoC-derived chassis, parameterised by the sheet; the archetypes are knob settings,
  not separate bots.
- **Ivan Geffner's bots.** No licence, all rights reserved: referenced in prose, never read into code.
- **Per-tile pollution rendering.** Global pollution is a number in the readout and on the endcard;
  a per-tile haze is not drawn in v1.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the flood.
- **Crossplay (Python bots), indicator dots and lines, the engine profiler and `speedscope`.** None
  of them exist in the port.
- **Battlecode years other than 2026 and 2020.** The registry, `game_config.year`, the variant naming
  and `years/dispatch.nim` all support more; only these two are registered.
