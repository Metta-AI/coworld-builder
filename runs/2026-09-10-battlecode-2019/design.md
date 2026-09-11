# cogame-battlecode — the `bc19` year module: Battlecode 2019 "Crusade" (design note, 2026-09-10)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a branch/PR of the shipped
repo that adds the year module `bc19` beside the shipped `bc16`, `bc20`, `bc21`, `bc22`, `bc23`, `bc24`, `bc25` and
`bc26`, adds the manifest variant `bc19`, keeps certification on `bc26`, and bumps the version of the *same* coworld.
**There is no `cogame-battlecode-2019` repo and none is created.** The starter is chosen by game shape and it is the
only defensible one: bc19 is the same shape as the eight shipped years — a deterministic Nim grid sim compiled twice
(native for the server, wasm for the viewer), one sealed JSON doctrine per seat, no engine and no foreign runtime in
the image, a static wasm replay viewer that re-derives every frame — and the year-module boundary
(`src/battlecode/years/<year>/`, `years/registry.nim`, `years/dispatch.nim`, `game_config.year`) already exists and
has now been proved **eight** times. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode` → this. The starter is
`Metta-AI/cogame-battlecode`, and **every convention there holds here unless this note says otherwise**: the Nim
sim/server/player layout, `nimby.lock`, the bitworld runtime contract, the `GameVersion` discipline,
`tools/build_replay_viewer.sh`, the `replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch doctrine
layer (`llm.nim` / `decide.nim` / `sheet.nim` / `sheet_common.nim` / `baselines.nim`), the closed results document,
and "degrade, never hang".

`bc19` is the **ninth** year module and the **first whose engine is JavaScript**. This note lands in the repo as
`docs/plans/2026-09-10-battlecode-2019-design.md` on the branch `bc19-year-module`. The copy of record for the run is
`runs/2026-09-10-battlecode-2019/design.md`.

### Provenance — every rule below was read or measured in this sandbox, not assumed

**The rules were read from `github.com/battlecode/battlecode19` at commit `80cf1cc535ec5a30559274aa1b49807ad4859925`**
(`HEAD` of `master`, 2019-08-09, last commit "update requirements and make python version deterministic to avoid sad
times"; licence: **the repository root `LICENSE` is GPL-3.0 and it is the ONLY licence file anywhere in the tree** —
verified by `find . -iname 'licen*' -o -iname 'copying*'`, one hit). Read whole: `coldbrew/game.js` (947 lines),
`coldbrew/action_record.js` (342), `coldbrew/runtime.js` (95), `coldbrew/specs.json` (113), `coldbrew/vm.js` (27),
`coldbrew/cli/run.js` (172), `coldbrew/starter/js_starter.js`, `coldbrew/bots/example_js/robot.js`,
`coldbrew/bots/exampy/robot.py`, `coldbrew/vis.js` (505) and `app/src/views/docs.js` (492 — the human-readable spec).

**The engine was RUN in this sandbox**, which is where most of the numbers below come from:

| measurement | how | result |
|---|---|---|
| a whole game end to end | `node coldbrew/cli/run.js -r bots/example_js -b bots/example_js -s 43 --chi 1000 --che 100` | exit 0, `replay.bc19` 79 454 bytes, *"Game over, blue won by greater health"* |
| the map generator over seeds 1…400 | a harness that constructs `new Game(seed, …)` and measures the three boolean maps and the castle roster | **386 of 400 playable; 13 DEGENERATE** (0 castles, 2–4 passable squares): seeds **7, 20, 24, 83, 108, 127, 175, 211, 232, 267, 283, 348, 365** |
| the round/turn structure | a deterministic hook harness reimplementing `runtime.js`'s `gameLoop` | round 1000 gets **exactly ONE robot turn**; a unit built in a round **does** take a turn in the same round; 999 × 7 + 1 = 6 994 turns on `seed-0043` with four castles and three pilgrims |
| the `visible` array's order | six identical runs of seed 1, printing the first castle's `visible` id list | **five distinct orders** — the shuffle at `game.js:717-722` uses the GLOBAL, unseeded `Math.random()` (D3) |
| `regions.sort(x => -1*x.length)` (`game.js:153`) | instrumented `makeMap` over seeds 1…150: 184 half-map region computations, 42 with more than one region (max 4) | the sort is a **plain reversal** in **42 of 42** cases under this sandbox's **Node v22.22.0**, and the region kept passable is **NOT the largest in 40 of those 42** (V3) |
| engine speed | the same harness, three seeds, ~19–22 k turns each | 1 463 / 2 293 / 3 259 ms in Node — the cost is dominated by `getGameStateDump`'s `JSON.stringify` and by `enactAttack`'s whole-board sweep, neither of which the port reproduces |
| the PREACHER's own splash | a synthetic 9×9 board, one PREACHER at (4,4) attacking (5,4) with two enemy pilgrims at (5,4) and (5,5) and a friendly at (3,4) | preacher **60 → 40 HP** (it is inside its own blast), both enemies dead, the friendly at r² 4 **unharmed**, reclaim **14 karbonite / 33 fuel**, team fuel −15 |
| the CHURCH "attack" | `processAction` on a CHURCH with `action: attack` | **ACCEPTED**, `record.action == 2` — `ATTACK_RADIUS` is the scalar `0`, not an array, so `r > undefined` and `r < undefined` are both false (D6) |
| the PILGRIM attack | the same, on a PILGRIM | throws `TypeError: Cannot read properties of null (reading '1')` → swallowed → nothing happens (D6) |
| the signal cost | `Math.ceil(Math.sqrt(r²))` for r² ∈ {0,1,2,3,4,5,9,10,16,64,100,7938} | 0,1,2,2,2,3,3,4,4,8,10,**90**; the maximum legal radius is `2·63² = 7938` |

**`mersenne-twister@1.1.0` was downloaded and read** (`npm pack mersenne-twister@1.1.0`, integrity
`sha1-+RZhjuQ9cXnvz2Qb7EUx65Zwl4o=`, pinned in `coldbrew/package-lock.json:2645-2649`). It is the
banksean/Nishimura–Matsumoto MT19937: `new MersenneTwister(seed)` calls `init_seed(seed)` = `init_genrand` with `mt[0]
= s >>> 0` (`src/mersenne-twister.js:90-104`), and `random()` is `random_int() * (1.0/4294967296.0)` =
`genrand_int32()/2³²` (`:189-192`). That is the whole generator the port has to reproduce, and it is the *only* seeded
randomness in the engine.

**`m-schier/battlecode-2019-wololo` was cloned and read** (commit `ebdd27959a83e00c4ec67c74253d2db8095e3ba6`,
`COPYING` = **GPL-3.0**, and every source file carries its own GPL header naming Paul Hindricks, Maximilian Schier and
Niclas Wüstenbecker). It is the **behaviour source** for the `saber` chassis: 5 315 lines over `robot.js` (4 197),
`WorldKnowledge.js`, `Extensions.js`, `Lattice.js`, `PriorityQueue.js`, `Strategy.js` and `Random.js`. The named
behaviours the chassis takes from it are listed in §Decisions and in `NOTICE`.

**The three unlicensed repositories named in the idea were NOT cloned, NOT read and contribute nothing.**
`j-mao/battlecode-2019`, `awesomelemonade/Battlecode2019` and `virenvshah/Battlecode2019` carry **no licence**, so
this run treats them as unreadable. **No line of any of them is copied, vendored, compiled, translated, read or
fetched.**

Base-repo facts are from `Metta-AI/cogame-battlecode` at **`6e89d0f`** (`main`, 2026-09-09), whose shipped coworld
version is **0.8.2** and whose `GameVersion` is **GV11**. Every `path:line` and constant below is to those two trees.

### Source idea (verbatim — the Notes block of `runs/2026-09-10-battlecode-2019/idea.md`)

```
CASTLES and CHURCHES build PILGRIMS (mine karbonite and fuel), CRUSADERS, PROPHETS and PREACHERS; every action burns fuel; win by castle elimination, else castle-count tiebreaks at round 1000 on boards up to 64x64. Tier 2 in the ranking with real turnover — turtle/rush/defence rock-paper-scissors, a dev nerf of the preacher rush, then economy/expansion and the emergent church-saber infiltration at qualifiers — with several coexisting archetypes. FEASIBILITY FLAGS: the engine is JavaScript ('coldbrew', npm bc19 0.4.6, vm2 sandbox) and competitor bots are JS/Python, so the oracle is `node coldbrew/cli/run.js` in CI and the parity trace is against a JS engine (integer game, so exact parity is achievable); the spec exists only as the docs page source (app/src/views/docs.js) plus coldbrew/specs.json; only a 9th-place bot is licensed.

Seats: 2 (one cog per side). num_agents = 2 in the bc19 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc19 (v1 candidates; the builder finalises them from the chassis it ports): opening {turtle | preacher_rush | pilgrim_eco}, pilgrim_count_curve, church_expansion {never | mid | early}, fuel_reserve, unit_mix, church_saber_round, symmetry_wall, castle_talk_use, defend_radius.
Rules, engine, oracle: Engine + spec: https://github.com/battlecode/battlecode19 (root LICENSE GPL-3.0; coldbrew/ = engine, coldbrew/specs.json + app/src/views/docs.js = the rules). Oracle: Node >= 8, `node coldbrew/cli/run.js` with two JS bots (port the scaffold bot's behaviour for Tier A).
Chassis and baselines (behaviour sources): m-schier/battlecode-2019-wololo (9th, GPL-3.0 — chassis behaviour source), j-mao/battlecode-2019 (NP-cgw, finalist; no licence), awesomelemonade/Battlecode2019 (CitricSky 3rd; no licence), virenvshah/Battlecode2019 (7th; no licence) — the unlicensed ones are behaviour references only.
Ranking: Tier 2 (patch-driven turnover) in the ranking; flagged for JS engine + one licensed bot.
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc19` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc19` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc19`, league_name `Battlecode 2019 — Crusade`, default_variant_id `bc19`, short_name `bc19` (softmax.com/battlecode/bc19), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; **one new year module `src/battlecode/years/bc19/` + ONE registry line + one arm per `dispatch.nim` `case`**; branch-only work on `bc19-year-module` | this paragraph, §Sim module ("The year module boundary"), §Packaging ("Branch discipline") |
| `num_agents = 2` in `variants[bc19].game_config`, in every other variant, in the cert fixture, and as `<SEATS>` = 2 | §The game ("Seats"), §Packaging ("Variants", "The `<SEATS>` cross-check") |
| `GameVersion` **GV11 → GV12**; `ReplayCompatibleGameVersions` EXTENDED to `GV04 … GV12`, never reset | §Sim module ("Determinism"), §Packaging ("Version bump semantics") |
| Coworld version **0.8.2 → 0.9.0** at phase 40; certification stays **bc26**; no variant's `players` array changes | §Packaging |
| New manifest variant `bc19` appended to `variants[]` with the same `game_config` shape as the eight shipped ones; `maxRounds` and the timing numbers decided and justified; **no `config_schema` bound has to move** | §Packaging ("Variants", "The schema bounds") |
| Parity oracle is **JavaScript**: `actions/setup-node` on a pinned Node, a pinned `battlecode/battlecode19` commit in `tools/oracle/bc19/engine.lock`, tiers modelled on `parity-oracle-bc16` (`ci.yml:2636`), **NO Node/JDK/JS runtime in the image** | §Tests (`parity-oracle-bc19`), §Packaging, §Out of scope |
| The chess clock replaced by a **fixed per-robot decision budget** with the decrement pinned to an exact constant, documented in `docs/PARITY.md` §bc19 **and** `docs/RULES-BC19.md`, and covered by a parity tier | §Sim module (V1, "The chassis and the DecisionOps clock"), §Tests (Tier B′) |
| Licence discipline: derive from GPL-3.0 `battlecode19` and GPL-3.0 `m-schier/battlecode-2019-wololo`; **never read the three unlicensed repos**; verify the sprite set's own terms; specify the exact `NOTICE` paragraphs | §The game ("Provenance and licensing"), §Viewer ("Art"), §Packaging ("Licensing") |
| In-game aliases stay year-neutral **Clan Ash / Clan Basil**; year flavour only in descriptions and chrome; real names spectator-side | §The game ("Seats"), §Viewer |
| `ci.yml`'s branch trigger list gains `bc19-year-module` (the list is at `.github/workflows/ci.yml:26`) | §Packaging ("Branch discipline") |
| Note length ≤ 2800 lines | this file |
| `## Out of scope (v1)` non-empty | §Out of scope (v1) |

### Interface facts this note is written against (read from `6e89d0f`, not assumed)

- **`GameVersion` is `GV11`** and `ReplayCompatibleGameVersions` is
  `["GV04","GV05","GV06","GV07","GV08","GV09","GV10", GameVersion]` (`src/battlecode/sim_types.nim:16` and
  `:220-221`). This run **extends** the list to `["GV04",…,"GV11", GV12]`; it never resets it.
  `tools/ci/check_gameversion.sh` compares the *headline*, not the digits, so a sibling branch that takes GV12 first
  forces this branch to GV13 — expected and handled (§Packaging).
- **`config_schema.maxRounds` is already `{minimum: 50, maximum: 3000}`** (bc16 widened it from 2000). bc19 plays
  **1000**, so **no schema bound has to move at all** — every edit to `coworld_manifest_template.json` in this run is
  purely additive. `gamesPerMatch` keeps `maximum: 3`, `perGameBudgetSeconds` `maximum: 300`, `matchBudgetSeconds`
  `maximum: 600`, and the four millisecond bounds are unchanged with bc19 inside all of them.
- **`AliasA`/`AliasB` are `"Clan Ash"`/`"Clan Basil"`** (`sim_types.nim:240-241`), shared by all eight shipped years.
  **This run does not touch them.**
- **`EndReason` in `sim_types.nim:277-282` is bc26-only**; every other year carries its own end-reason strings and
  `GameOutcome.endReason` is a `string` (`years/dispatch.nim:111`). bc19 does the same — no year-neutral enum is
  touched.
- **`results_schema.games[].end_reason`'s enum already has 36 values** and already contains `coin_flip` (bc22's) and
  `abandoned`. bc19 **reuses those two** and adds exactly **three** (§Packaging).
- **`results_schema.games[].items.properties` already has 268 keys.** bc19 **reuses** `units_built`, `units_alive`,
  `attacks`, `damage_dealt`, `kills` and `robots_lost` rather than duplicating them, and adds its own beside them.
- **`sheet.nim`'s envelope resolver is already year-neutral and already does everything the bc23 league failure asked
  for** (`sheet.nim:92-155`): resolution order `""` → `"sheet"` → `"doctrine"` → the single object-valued key, at most
  **one** unwrap, recorded in `Sheet.envelope`, and `results_schema.required` already declares `sheet_envelope`.
  **bc19 needs no year-neutral change here** — only its own arm and the absent-key counting inside its own
  `knobs.nim`.
- **`ScriptedChassis`** (`sim_types.nim:244-270`, sixteen values) and **`Baseline`** (`baselines.nim:21-36`, sixteen
  values) each gain **two**, plus one arm each in `defaultBaselineFor`, `baselineFor`, `baselineChassis` and
  `baselineReply`. All additive. **`wololo` is already taken** — `scWololo`/`blWololo` are bc22's strong chassis
  (`sim_types.nim:267`) — so bc19's strong chassis is named **`saber`**, not `wololo`, even though Team Wololo's 2019
  bot is its behaviour source. Stated here because it is exactly the sort of collision that compiles and then seats
  the wrong bot.
- **`src/battlecode/rng.nim` ports `java.util.Random` and `IDGenerator`** and nothing else. bc19's engine uses
  **MT19937**, which is not in it, so bc19 brings its own `years/bc19/mt19937.nim` (§Sim module, D1). `rng.nim` is
  **unchanged**; its `java.util.Random` is still used, for the *scaffold bot's* per-robot stream (Tier A″).
- **`src/battlecode/fdlibm.nim` is not needed**: bc19 has no transcendental on any gameplay path (§Sim module, D5).
- **`match.nim:568` computes `perGame = max(1, min(config.perGameBudgetSeconds, remaining))`**, so a test helper that
  zeroes the field buys a **one-second** budget while `years/bc19/rules.nim` one level down treats 0 as unbounded.
  bc19's tests use the `if perGame > 0:` convention from `tests/test_bc23_replay.nim:69` and guard every `games[0]`
  behind a non-empty check (§Tests). **`winBonusFor` at `match.nim:604-625` pays 200 for `{yBc25, yBc23, yBc22,
  yBc16}`**; bc19 joins that set, for the reason in §The game ("Scoring").
- **`beatsFor` at `src/battlecode/broadcast.nim:152` is the ONE place a beat kind is decided** and already carries
  four year discriminators (`isBc25`, `isBc23`, `isBc22`, `isBc16` at `:160-163`). bc19 adds `isBc19` and turns five
  arms into five-way tests (§Viewer, "The beat contract").
- **`relayout()`'s `--statrail` measured-id set** is at `client/replay_broadcast.html:7018-7021` and names fifteen ids
  (`econ`, `bc20-soup`, … `bc16-econ`, `bc16-units`); `#killfeed`'s `bottom` is `max(calc(76*var(--u)),
  calc(var(--band,0px) + var(--statrail,0px) + 8px))` (`:1270`). bc19's job is to **keep the fix armed** — add its two
  boxes — not to re-fix it. The **endcard noun table** is keyed by `data-year` at `:6871-6887`; bc19 adds one row, so
  no bc26 noun can reach a bc19 card. The nine-way visibility guard is at `:7166` and `:7178`.
- **`tools/ci/viewer_smoke.mjs` already carries the scrub-selector fix** and `ci.yml` asserts `scrub_selector ==
  "#scrub"` per replay. Nothing to change; and `canvas_text.total: 0` on this renderer covers nothing and **is not
  read as a pass** (LEARNINGS 2026-09-08).
- **`tools/ci/docker_smoke.sh` already carries every env switch bc19 needs** (`SMOKE_EXPECT_YEAR`, `SMOKE_PLAYER_IDS`,
  `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`, `SMOKE_CONTRACT_PROBE`, `SMOKE_SEATS`, `SMOKE_REQUIRE_STATS`,
  `SMOKE_EXTRA_ENV`), takes the seat count **solely** from `certification.game_config.num_agents` (`:141-173`) and
  refuses a `SMOKE_CONFIG_OVERRIDE` that changes `num_agents` (`:199-201`). bc19 adds a ninth episode and **needs no
  script change**. **`replay-viewer/config.nims` likewise needs no edit**: `--preload-file {rootDir}/data@data`
  already carries the whole `data/` tree.
- **The `test` job's `timeout-minutes` is 150** (`ci.yml:146`). bc19 raises it to **165**: its shards are the
  *lightest* in the repo (1000 rounds, a third of bc16's) but there are eighteen of them and every shard runs twice
  (debug and `-d:release`).
- **This repo records `result` (singular) in the replay**, not `results`, and a best-of-three episode legitimately
  plays **fewer** games than `gamesPerMatch` when a side clinches, with `reason` still `complete` (LEARNINGS
  2026-09-07).
- **`tools/ci/policies.json` is repo-wide and carries 32 entries** (4 per year × 8 years). bc19 adds 4, making 36, and
  phase 40 dispatches with a `policies` **override limited to those 4**.

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as the eight shipped years (turn-queue grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, nine generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. **No new repo** (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=saber\|examplefuncsplayer19` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc19/` — to wasm; the browser re-derives every round from events + config + seed. No `.bc19` bytes anywhere. |
| Real art, starter chrome verbatim | The 2019 web client's own unit icons cut into `data/atlas_bc19.*` (credited in `NOTICE`); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc19 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash** / **Clan Basil** (`sim_types.nim:240-241`, year-neutral); real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **305 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26\|bc20\|bc21\|bc22\|bc23\|bc24\|bc25\|bc16].game_config` (all unchanged) and `variants[bc19].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level. |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc19 policy set is in §Packaging. |
| Both champions are LLM prompt policies, #1 owned by daveey and #2 by daveey-1; fillers are the scripted baselines, normally 2 | §Packaging (`tools/ci/policies.json`, "The phase-50 plan"). |

---

## Feasibility verdict

**Buildable. There is no load-bearing rule left undetermined by the engine source, and there is no `OPEN` section in
this note.** The idea's four feasibility flags all resolve, and three of them resolve *better* than the idea expected:

| Flag from the idea | Verdict |
|---|---|
| "the engine is JavaScript ('coldbrew', npm bc19 0.4.6, vm2 sandbox) … the oracle is `node coldbrew/cli/run.js`" | **Resolved, and the oracle is smaller than the idea assumed.** The parity driver does **not** need `vm2`, `rollup`, `esm`, the Python/Java transpiler or `update-notifier`: it `require`s the pinned checkout's `coldbrew/game.js` and `coldbrew/action_record.js` **unmodified except for one committed patch**, reimplements `runtime.js`'s twenty-line `gameLoop`/`emptyQueue`, and instantiates each bot as a fresh module per robot. **The only npm dependency is `mersenne-twister@1.1.0`**, pinned by version and integrity hash. That drops 403 of the engine's 404 transitive packages, and with them `vm2` — a package with known sandbox-escape CVEs and a deprecation notice. Proved in this sandbox: the harness above ran whole 1000-round games with nothing but `game.js`, `action_record.js`, `specs.json` and `mersenne-twister`. |
| "integer game, so exact parity is achievable" | **Confirmed, and stronger than that.** Health, karbonite, fuel, damage, capacities, radii and yields are *all* integers (`coldbrew/specs.json`). The only non-integer arithmetic anywhere on a gameplay path is `Math.ceil(Math.sqrt(signal_radius))` (`game.js:834`, `action_record.js:329`) over the **finite** domain 0…7938 and `Math.floor(a/b)` in the reclaim (`action_record.js:305-306`). Both are tabled at build time; **the runtime has no `sqrt`, no `pow`, no `exp` and no float64 accumulation at all**, so bit-exactness is by construction rather than by care. |
| "the spec exists only as the docs page source plus `coldbrew/specs.json`" | **Resolved. The engine is the tiebreaker and it is complete.** Every rule below carries a `path:line` into `coldbrew/`. Where `app/src/views/docs.js` disagrees with the engine, **the engine wins**, and every one of the **seven** disagreements found is tabled in §The game ("Where the docs are wrong"). |
| "only a 9th-place bot is licensed" | **Resolved.** `m-schier/battlecode-2019-wololo` is GPL-3.0 with per-file headers and is a complete, sophisticated 5 315-line bot (lattice defence, Dijkstra navigation, an 8×8 strategic score grid, a 16-bit radio protocol and an 8-bit castle-talk protocol, church expansion scoring, dodge micro, charge coordination). It is more than enough for one strong chassis. The weak floor is **also licensed**: `coldbrew/bots/example_js/robot.js` sits inside the GPL-3.0 engine repository, so the deliberately weak baseline is a *port*, not an invention. No unlicensed repository is touched. |

Three things that could have been ambiguous and are not:

- **Turn order.** `this.robots` is a plain JavaScript **array** (`game.js:33`), `robin` an index into it (`:41`),
  `createItem` **appends** (`:461`) and `_deleteRobot` **splices and decrements `robin` when the removed index is
  below it** (`:939-942`). So the order is insertion order with by-value removal, and it is the only robot collection
  the engine iterates — `isOver` (`:551`), `getItem` (`:478`), `getGameStateDump` (`:672`) and `enactAttack`'s board
  sweep all read it or the shadow. **There is no hash map, no sort and no set anywhere in the round loop.** Measured:
  a unit built in a round **does** take a turn in the same round, exactly as `docs.js:167` says.
- **The end ladder.** `isOver` (`:537-614`) is one straight-line ladder over a single census pass, with no RNG except
  the two coin flips, and it is evaluated **before every turn** (`runtime.js:60`) rather than at end of round. Every
  branch is explicit; §The game rule 5 numbers all seven.
- **The economy.** There is exactly one passive income in the game — `TRICKLE_FUEL = 25` fuel per team per round,
  credited at `game.js:751-752` — and it is **flat, not per structure**. The idea's phrase "income per castle/church
  per round" describes a mechanic bc19 **does not have**; the idea is input data and the engine is the authority.
  Everything else is pilgrim mining (`+2` karbonite or `+10` fuel per `mine`, `action_record.js:215,220`), reclaim on
  a kill (`:305-306`) and the castle barter (`:228-247`).

**Two rules are deliberately NOT ported and are therefore decided divergences, not ambiguities**: the wall-clock chess
clock (V1) and the unseeded `visible`-order shuffle (V2). Both are *unreproducible in the engine itself* — the shuffle
was measured producing five different orders in six identical runs — so there is nothing to be faithful to, and the
note says exactly what the port does instead and how the oracle is made to agree. A third, the build-time map
generation (V3), exists because the generator's `regions.sort` passes an inconsistent comparator whose result is
V8-implementation-defined and because 13 of the first 400 seeds produce unplayable boards.

---

## The game

**Battlecode 2019 "Crusade", played by doctrine, simulated in Nim.** Two cogs each command a religious order of robots
on a **square, procedurally generated, mirror-symmetric** grid between **32×32 and 64×64**. Neither cog moves a robot.
At t=0 each writes a **doctrine** — a JSON sheet of eleven named knobs — and the deterministic sim plays the whole
1000-round match from those two sheets while both cogs watch.

Each order starts with **1 to 3 CASTLES** (200 HP, cannot be built, and the only thing that decides the game: lose
your last castle and you lose on the spot), **100 KARBONITE** and **500 FUEL**. Castles and CHURCHES build
**PILGRIMS** (10 karbonite / 50 fuel, 10 HP, the only unit that can mine and the only unit that can build a CHURCH),
**CRUSADERS** (15/50, 40 HP, 10 damage at r² 1–16, **speed r² 9** — the only fast unit), **PROPHETS** (25/50, 20 HP,
10 damage at **r² 16–64** and blind inside r² 16 — the lattice unit) and **PREACHERS** (30/50, 60 HP, **20 damage over
every square within r² 3 of the target**, which includes the preacher's own square). A pilgrim builds a **CHURCH** for
50 karbonite / 200 fuel; a church is a second spawn point and a second deposit point.

**Every action burns fuel from the global store**, and that is the whole game's clock: a move costs `r² ×
FUEL_PER_MOVE` (1 for a pilgrim or crusader, 2 for a prophet, **3 for a preacher**), an attack costs 10 / 10 / 25 / 15
fuel (castle / crusader / prophet / preacher), a `mine` costs 1, a radio broadcast costs `ceil(sqrt(r²))`, and the
only passive income in the game is a flat **25 fuel per team per round**. Karbonite comes from pilgrims standing on
karbonite depots (**+2** a turn, capacity 20) and fuel from pilgrims standing on fuel depots (**+10** a turn, capacity
100); both are *unrefined* until a robot `give`s them to an adjacent castle or church, which is what puts them in the
global store.

Four mechanics make this year its own game rather than a reskin:

1. **The board is a mirror, and the mirror is the map.** Every board is either horizontally or vertically symmetric
   (`game.js:300-310`), every robot gets the **whole** passable, karbonite and fuel map on its first turn
   (`game.js:728-730`), and therefore **every enemy castle's position is derivable from your own on turn one**. There
   is no scouting problem and no fog over terrain — only over units. That is why `symmetry_wall` is a knob: the
   shortest line between the two orders is known to both from round 1, and whoever fortifies it first owns the
   midline.
2. **The preacher hits you too.** `DAMAGE_SPREAD = 3` means a preacher's attack lands **20 damage on every occupied
   square within r² 3 of the target** — nine squares — **with no team check** (`action_record.js:293-316`). Its
   minimum attack range is r² 1, so a preacher firing at an adjacent enemy **damages itself** (measured: 60 → 40 HP)
   and every friendly beside it. A pilgrim has 10 HP and a prophet 20, so one friendly preacher shot deletes a
   lattice. No archetype the idea names spends that deliberately, which is why `preacher_share` is a knob.
3. **A kill pays.** When a unit dies, the killer receives **`floor((target.karbonite + CONSTRUCTION_KARBONITE/2) /
   r²_to_attacker)` karbonite and `floor(target.fuel / r²_to_attacker)` fuel**, capped at its own capacity
   (`action_record.js:301-311`). A crusader that kills a loaded pilgrim at r² 1 collects 12 karbonite and everything
   the pilgrim was carrying — so raiding the enemy's mining line is *income*, not just denial. Structures collect
   nothing: their `KARBONITE_CAPACITY` is `null` and `Math.min(n, null)` is `0` (D6).
4. **The two orders can trade with each other.** A castle may `proposeTrade(karbonite, fuel)`; when the two orders'
   standing offers match exactly, the swap executes and both offers are cleared (`action_record.js:228-247`). The
   engine's own documentation calls this "collaborate with the opposing team for mutual benefit" (`docs.js:149`). In a
   zero-sum league it is the year's largest unexploited play — karbonite is scarce and fuel trickles — which is why
   `trade_policy` is a knob.

**That is why this year is worth playing sealed.** The idea calls 2019 Tier 2 for *patch-driven* turnover:
turtle/rush/defence rock-paper-scissors, a dev nerf of the preacher rush, then economy/expansion, then the emergent
church-saber infiltration at qualifiers. The doctrine sheet in §Decisions makes exactly those the `opening` and
`church_saber_round` axes, and then makes the two mechanics the meta never systematically spent — **preacher friendly
fire** and **the barter** — spendable choices with teeth.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. Those two aliases are the repo's
year-neutral `AliasA`/`AliasB` (`sim_types.nim:240-241`) and this run does **not** change them: renaming them would
change what every shipped year records. The 2019 flavour — the engine's own RED (*Religious Exploratory Doctrinists*)
and BLUE (*Believers of Lasting Unity Everywhere*), `docs.js:136` — is carried by the viewer chrome and the variant
description, never by the alias constants. The episode seed decides which slot takes engine-side **RED** in game 1;
sides alternate every game (`sideAslotFor(seed, gameIndex)`, the shape reused from `years/bc16/maps.nim`).

**Motive: zero-sum.** One side wins a game and the other loses it; the cogs never exchange a byte, and the only
channels between them are the board and the castle barter — which is a *rule*, not a negotiation, because neither cog
can see the other's doctrine. The two name spaces follow: in-game the orders are the anonymous aliases **Clan Ash**
and **Clan Basil**, so a doctrine cannot be written against a known opponent, and the real player names (`daveey`,
`daveey-1`) exist only in `replay.names[]` / `results.names[]` and are drawn only by the spectator-side viewer.

### Provenance and licensing

- **`battlecode/battlecode19` — GPL-3.0** (root `LICENSE`, 35 149 bytes, and **the only licence file in the tree**),
  pinned at `80cf1cc535ec5a30559274aa1b49807ad4859925`. The 2019 **rules** are reproduced here as an **independent Nim
  implementation written from reading `coldbrew/`**, not as a translation of copied files: no JavaScript is vendored
  into `src/`, no `node_modules` is shipped, `src/battlecode/years/bc19/**` contains no JavaScript, and the engine's
  own toolchain exists **only** inside the `parity-oracle-bc19` CI job. `years/bc19/constants.nim` is *generated* from
  `coldbrew/specs.json` by `tools/gen_year_constants.py --year bc19` and byte-diffed in CI, so the constant table is
  provably the engine's and provably not hand-typed.
- **The sprite set's own terms were verified before pinning.** There is **no per-directory `LICENSE` and no
  `"license"` field in `app/package.json` or `coldbrew/package.json`** — checked — so `app/public/assets/img/**` is
  covered by the repository root's GPL-3.0 and nothing else. `data/atlas_bc19.*` is cut from exactly six files,
  `app/public/assets/img/s_{castle,church,pilgrim,crusader,prophet,preacher}.png` (**40×40 each**, 130–339 bytes),
  with the palette taken from `coldbrew/vis.js:486` (RED `#DD0048`, BLUE `blue`) and the terrain tones from
  `vis.js:343,399` (`#333` ground, `#eee` rock) and `vis.js:442` (`#fd5f00`, the radio line). **The sibling
  directories `app/public/assets/{css,js,fonts}` are third-party (Bootstrap, jQuery, Chartist, Pe-icon-7-stroke) and
  are NOT used, NOT cut and NOT shipped.** The upstream visualiser has **no depot art at all** (`vis.js` draws nothing
  for karbonite or fuel), so the depot pips are drawn procedurally by `render.nim` and credited to nobody.
- **`m-schier/battlecode-2019-wololo` — GPL-3.0** (`COPYING` at the root **and** a GPL header in every source file
  naming the three authors), pinned at `ebdd27959a83e00c4ec67c74253d2db8095e3ba6`. It is the **behaviour source** for
  the `saber` chassis: a behaviour port, file by file, with the correspondence named in §Decisions and in `NOTICE`. No
  JavaScript is vendored.
- **`j-mao/battlecode-2019`, `awesomelemonade/Battlecode2019` and `virenvshah/Battlecode2019` carry NO LICENCE. None
  was cloned, read, copied, vendored, compiled, translated or fetched by this run, and none contributes a single line
  to it.** Where this note says "the play the 2019 meta made", that is a statement about the *idea text's*
  characterisation of the 2019 season, not a claim about any repository's contents. `docs/RULES-BC19.md` and `NOTICE`
  both say this in as many words.
- **`LICENSE` of this repo is AGPL-3.0** and stays that way. Both 2019 upstreams are GPL-3.0, and **GPLv3 §13 / AGPLv3
  §13 expressly permit the combination**, exactly as `NOTICE:56-59` already records for the 2020 and 2016 sources.
  §Packaging repeats the reasoning rather than leaving it implicit.

### Constants — verbatim from `coldbrew/specs.json` at the pinned commit

Generated into `src/battlecode/years/bc19/constants.nim` by `tools/gen_year_constants.py --year bc19`, never
hand-typed, and re-generated and byte-diffed in CI (§Tests item 24).

| constant | value | constant | value |
|---|---|---|---|
| `MAX_ROUNDS` | **1000** | `MAX_BOARD_SIZE` | **64** (boards are 32…64, `game.js:77`) |
| `INITIAL_KARBONITE` | **100** per team | `INITIAL_FUEL` | **500** per team |
| `TRICKLE_FUEL` | **25** fuel per team per round | `MINE_FUEL_COST` | **1** |
| `KARBONITE_YIELD` | **2** per `mine` | `FUEL_YIELD` | **10** per `mine` |
| `COMMUNICATION_BITS` | **16** (radio values 0…65535) | `CASTLE_TALK_BITS` | **8** (values 0…255) |
| `MAX_TRADE` | **1024** (offers are `\|k\| < 1024`) | `MAX_ID` | **4096** (ids 1…4095, V4) |
| `CHESS_INITIAL` | **100 ms** (V1) | `CHESS_EXTRA` | **20 ms** per turn (V1) |
| `TURN_MAX_TIME` | **200 ms** (V1) | `MAX_MEMORY` | 50 000 000 — **dead code**, the check is commented out at `vm.js:15-22`; nothing to port |
| `CASTLE`/`CHURCH`/`PILGRIM`/`CRUSADER`/`PROPHET`/`PREACHER` | **0/1/2/3/4/5** (the ordinal order is load-bearing: it is `build_unit` on the wire and the atlas index) | `RED`/`BLUE` | **0/1** |
| max legal `signal_radius` | **`2·(64−1)² = 7938`** (`game.js:833`) | max legal `give` amount | **255** each (`game.js:904`, `< 2⁸`) |

`SPECS.UNITS` — the whole six-row table verbatim, in `values()` order:

| # | unit | build K | build F | K cap | F cap | speed r² | fuel/r² | HP | vision r² | dmg | attack r² | attack fuel | spread r² |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `CASTLE` | **cannot be built** | — | `null` | `null` | **0** | `null` | **200** | **100** | **10** | **1…64** | **10** | 0 |
| 1 | `CHURCH` | **50** | **200** | `null` | `null` | **0** | `null` | **100** | **100** | **0** | **`0` — a SCALAR, not a pair** (D6) | **0** | 0 |
| 2 | `PILGRIM` | **10** | **50** | **20** | **100** | **4** | **1** | **10** | **100** | `null` | `null` (D6) | `null` | `null` |
| 3 | `CRUSADER` | **15** | **50** | **20** | **100** | **9** | **1** | **40** | **49** | **10** | **1…16** | **10** | 0 |
| 4 | `PROPHET` | **25** | **50** | **20** | **100** | **4** | **2** | **20** | **64** | **10** | **16…64** | **25** | 0 |
| 5 | `PREACHER` | **30** | **50** | **20** | **100** | **4** | **3** | **60** | **16** | **20** | **1…16** | **15** | **3** |

Derived predicates, ported exactly from the engine's own guards rather than from a table: `canBuild` = `PILGRIM ||
CASTLE || CHURCH` (`game.js:884`), and a **PILGRIM may build only a CHURCH** while a **CASTLE or CHURCH may build
anything but a CHURCH** (`:887-888`) and **nobody may ever build a CASTLE** (`:889`); `canMove` = `SPEED > 0`, so a
CASTLE and a CHURCH can never move because `r > 0 == SPEED` always holds (`:915`); `canMine` = `PILGRIM` only
(`:869`); `canTrade` = `CASTLE` only (`:857`); **`give` and `signal` and `castleTalk` are available to every unit**
(`:832-849`, `:901-910`), including structures; and the attack predicate is *not* a predicate at all but a consequence
of the `ATTACK_RADIUS` shape — see D6.

### The 2019 rule set — exact numbered resolution rules

The sim's own step list. Re-ordering any of it is a rules change and bumps `GameVersion`. It mirrors `runtime.js`'s
`gameLoop` (`:58-76`), `game.js`'s `enactTurn` (`:746-788`), `getGameStateDump` (`:667-736`), `processAction`
(`:804-930`), `isOver` (`:537-614`) and `action_record.js`'s `enact` (`:319-339`) exactly.

**1. The driver loop** (`runtime.js:58-76`), repeated until it stops:
   1. **Initialise every queued robot** (`emptyQueue`, `runtime.js:42-46`; `initializeRobot`, `game.js:623-631`). In
      this port a robot is handed its side's chassis at the moment it is created, so `init_queue` is drained to 0
      before every turn, `robot.initialized` is always `true` and `robot.hook` is never `null`. **This makes
      `isOver`'s win conditions 3 and 4 (`opponent failed to initialize`, `both failed to initialize`) unreachable
      here** — recorded as *unreachable in this coworld*, not *absent upstream* (V6).
   2. **Evaluate `isOver()`** (rule 5). **This happens BEFORE EVERY SINGLE TURN, not at the end of a round.** Two
      consequences the port reproduces and tests: a game that ends by castle annihilation stops **immediately after
      the killing robot's turn** and the rest of that round's robots do **not** act; and **round 1000 consists of
      exactly ONE robot turn** — measured, 999 full rounds plus one turn, 6 994 turns on `seed-0043`.
   3. If not over, **`enactTurn()`** (rule 2).

**2. `enactTurn`** (`game.js:746-788`):
   1. If `robin >= robots.len`: `robin = 0`; `round += 1`; **`fuel[RED] += 25`; `fuel[BLUE] += 25`** (`:747-753`).
      `robin` is initialised to `Infinity` (`:41`) and `round` to `0` (`:40`), so **the first played round is round
      1** and the fuel trickle lands *before* the first robot of the round acts. Rounds in this note, in the trace, in
      the replay and on the viewer clock are all **1-based**, which is what the eight shipped years except bc16
      already use.
   2. `robot = robots[robin]`; **`robot.turn += 1`** (`:755-756`). A robot's first turn therefore has `turn == 1`,
      which is the turn — and the only turn — on which it is handed the three maps (rule 3.7).
   3. `robot.time += CHESS_EXTRA` (`:759`) — **replaced (V1)**: the robot is credited `ChessExtraOps = 400`.
   4. Build the observation (rule 3) and run the chassis. **A chassis exception is swallowed** (`:767-768`) and
      becomes "no action"; `robot.time > 0` gates whether the chassis runs at all (`:766`) — under V1 it always does.
   5. Create a **fresh `ActionRecord`**, every field `0`/`null` (`action_record.js:3-19`), and validate the action
      into it (rule 4). **A validation failure leaves the record with whatever was already set and discards the
      rest**: the throw propagates out of `processAction` into `enactTurn`'s `try/catch` (`game.js:777-779`), so e.g.
      an illegal `move` **still performs the signal and castle talk that were validated before it**.
   6. **`record.enact(game, robot)`** (rule 6).
   7. Append eight bytes to the `.bc19` replay (`:787`) — **not ported** (V5).

**3. The observation a robot gets** (`getGameStateDump`, `game.js:667-736`), in this order:
   1. `shadow = getVisible(robot)` (`:651-664`): a full `height × width` integer grid, `-1` on every square outside
      vision, else `0` for empty or the **id** of the robot standing there. The vision test is `(x − c)² + (y − r)² <=
      VISION_RADIUS` — inclusive, and the walk is **r ascending outer, c ascending inner**.
   2. `is_castle = robot.unit == CASTLE` (`:671`).
   3. For each robot `i` in **`this.robots` order** (`:672`): `d = (x−x_i)² + (y−y_i)²`; `visible = d <= my
      VISION_RADIUS`; `radioable = d <= robots[i].signal_radius` — i.e. the **sender's** currently-stored radius, from
      the sender's **current** position.
   4. `if (!visible && !radioable && !is_castle) continue` (`:677`) — a castle is *not* skipped here, which is what
      makes castle talk work at any range.
   5. Copy the robot, then delete: `initialized`, `hook`, `start_time`, `doing` always (`:684-687`); `health`,
      `karbonite`, `fuel`, `time` for **anyone but yourself** (`:689-694`); and then `if (!visible && !radioable &&
      robot.team !== r.team) continue` (`:682`) — so a castle sees **all of its own team** and **only
      visible/radioable enemies**.
   6. `if (!radioable) { r.signal = -1; r.signal_radius = -1 }` (`:696-699`); `if (!visible) delete r.unit` (`:701`);
      `if (!visible && !radioable) { delete r.x; delete r.y }` (`:703-706`); `if (!is_castle && !visible) delete
      r.team` (`:708`) — **so a castle learns the TEAM of every own-team robot on the board even without seeing it**;
      and `if (!is_castle || robot.team !== robots[i].team) delete r.castle_talk` (`:710`) — castle talk is readable
      **only by a castle, and only for its own team**.
   7. `map`, `karbonite_map` and `fuel_map` are included **iff `robot.turn === 1`** and are `[[0],[0]]` on every later
      turn (`:728-730`). `fuel` and `karbonite` are the **team globals**; `last_offer` is the 2×2 barter matrix **for
      a CASTLE only, `null` otherwise** (`:731-733`).
   8. **The `visible` array is then shuffled in place by a Fisher–Yates pass driven by the GLOBAL, UNSEEDED
      `Math.random()`** (`:717-722`). **This is not reproducible, in the engine or anywhere else** — measured: five
      distinct orders in six identical runs of seed 1. **V2** replaces it with an ascending-`id` order and patches the
      engine to match.

**4. Validation** (`processAction`, `game.js:804-930`), in the engine's own order. Every "throw" below aborts the rest
   of validation and leaves the record as it stands (rule 2.5):
   1. `robot.time -= elapsed`; **throw if `robot.time < 0` or `hook == null` or `!initialized`** (`:805-808`) — the
      freeze rule. **V1: unreachable in this port.**
   2. `if (action === null) return` (`:814`); throw "Malformed move" unless the action is a plain object (`:816`).
   3. `logs` (`:819-825`) and `error` (`:827-829`) are drained into the team log — **not ported** (V5): they carry
      `wallClock()` timestamps and nothing a score or a spectator reads.
   4. **`signal`** (`:831-843`): both `signal` and `signal_radius` must be integers, `0 <= signal < 2¹⁶`, `0 <=
      signal_radius <= 7938`; `fuel_cost = ceil(sqrt(signal_radius))`; **throw if the team's fuel is below it**, else
      set the record and compute `temp_fuel = fuel − fuel_cost`, **which every later affordability test in this turn
      uses**.
   5. **`castle_talk`** (`:845-849`): integer, `0 <= v < 2⁸`, else throw. **Free.**
   6. `if (!('action' in action)) return` (`:851`) — so a signal-only or castle-talk-only turn is legal and complete.
   7. The action must be one of **`move`, `attack`, `build`, `mine`, `trade`, `give`** (`:853-854`).
   8. **`trade`** (`:856-866`): `CASTLE` only; `trade_fuel` and `trade_karbonite` integers with `|v| < 1024`; sets
      `record.trade` and **returns** — a trade needs no `dx`/`dy`.
   9. **`mine`** (`:868-875`): `PILGRIM` only; `temp_fuel − 1 >= 0`; sets `record.mine` and **returns**. **The engine
      does NOT check here that the pilgrim is on a depot, nor that it is under capacity** — both are decided at enact
      time (rule 6.4).
   10. **The `dx`/`dy` gate** for the remaining three (`:878-880`): both integers, **not both zero**, `|dx| < 64` and
       `|dy| < 64`, and the destination **on the board**.
   11. **`build`** (`:882-899`): destination **passable**; builder is `PILGRIM`/`CASTLE`/`CHURCH`; `|dx| <= 1` and
       `|dy| <= 1`; `0 <= build_unit <= 5`; a `PILGRIM` may build **only** a `CHURCH` and a non-pilgrim may **not**
       build a `CHURCH`; **never** a `CASTLE`; the destination square **empty in the shadow**; and `karbonite[team] >=
       build K` **and** `temp_fuel >= build F`.
   12. **`give`** (`:901-910`): destination **passable** (yes — the engine tests the terrain even though only an
       occupied square can receive); `|dx| <= 1`, `|dy| <= 1`; `give_karbonite`/`give_fuel` integers in `0 … 255`; and
       the giver must actually hold them. **No team check: giving to an ENEMY robot or an ENEMY structure is legal**
       (rule 6.6).
   13. **`move`** (`:912-920`): destination passable; `r² = dx² + dy² <= SPEED`; the destination **unoccupied**
       (`shadow > 0` refused); `temp_fuel >= r² × FUEL_PER_MOVE`. **There is no path check** — a unit teleports over
       rock and over other units within its speed, exactly as `docs.js:159` says.
   14. **`attack`** (`:922-929`): `r² = dx² + dy²` must satisfy `r <= ATTACK_RADIUS[1] && r >= ATTACK_RADIUS[0]`;
       `temp_fuel >= ATTACK_FUEL_COST`. **No vision test, no team check, no target-exists test, and no on-the-map test
       beyond step 10.** See D6 for what this does to a CHURCH and a PILGRIM.

**5. `isOver`** (`game.js:537-614`), one census pass then a seven-branch ladder:
   1. **The census** (`:551-562`): for every robot, `total[team] += 1`; and **only if `initialized` and `hook`**,
      `health[team] += robot.health` and, if it is a `CASTLE`, `castles[team] += 1`; otherwise `nulls[team] += 1`.
      Then `if (total[t] === 0) nulls[t] = -1` (`:564-565`). **`health` sums EVERY live unit of the team, not just its
      castles** — the docs say "more total health" and mean exactly that (`docs.js:138`).
   2. The ladder, first match wins:
      | rung | condition | engine `win_condition` | winner | our `end_reason` |
      |---|---|---|---|---|
      | 1 | `nulls[0]==total[0] && nulls[1]==total[1]` (`:567`) | **4** | coin flip | **unreachable** (V6) |
      | 2 | `nulls[t]==total[t]` (`:571`, `:575`) | **3** | the other side | **unreachable** (V6) |
      | 3 | `castles[0]==0 && castles[1]!=0`, or the mirror (`:579`, `:583`) | **0** | the side with castles | **`castles_destroyed`** |
      | 4 | `castles[0]==0 && castles[1]==0` (`:587`) | **2** | coin flip | **`coin_flip`** |
      | 5 | `round >= 1000 && castles[0] != castles[1]` (`:591-595`) | **0** | more castles | **`more_castles`** |
      | 6 | `round >= 1000 && castles equal && health differ` (`:597-599`) | **1** | greater total unit health | **`more_unit_health`** |
      | 7 | `round >= 1000 && castles equal && health equal` (`:600-604`) | **1** — *see the quirk* | coin flip | **`coin_flip`** |
   3. **The `win_condition = 1` overwrite is reproduced literally.** At `:604` the engine executes `this.win_condition
      = 1;` **unconditionally at the end of the round-1000 else block**, after the inner branch has already set `2`
      for the coin-flip case. So a round-1000 all-square game is *recorded by the engine* as win condition 1 ("greater
      health") while the winner really is a coin flip. The port keeps **both**: the trace and
      `results.games[].win_condition` carry the engine's own number, and `end_reason` carries the finer-grained truth.
      `tests/test_bc19_endladder.nim` asserts the pair.
   4. `if (replay && win_condition !== undefined) { replay[0] = winner; replay[1] = win_condition }` (`:608-611`) —
      not ported (V5). `return this.win_condition !== undefined` (`:613`).

**6. `record.enact`** (`action_record.js:319-339`), in exactly this order:
   1. **`robin += 1`** (`:323`) — *before* the action, which is why `_deleteRobot`'s `robin--` (rule 7) lands
      correctly even when the acting robot kills itself.
   2. `robot.signal = record.signal`; `robot.signal_radius = record.signal_radius`; `robot.castle_talk =
      record.castle_talk` (`:325-327`). **All three default to 0**, so **a robot that broadcasts nothing this turn
      silently clears last turn's broadcast**: a signal is audible from the end of the sender's turn until the end of
      its next turn, i.e. to every later robot in the same round and every earlier robot in the next one — exactly
      what `docs.js:164` describes.
   3. **`fuel[team] -= ceil(sqrt(signal_radius))`** (`:329`) — charged **once per turn**, for the final radius only,
      and **before** the action's own cost.
   4. Dispatch on `record.action`: 1 `move`, 2 `attack`, 3 `build`, 4 `mine`, 5 `trade`, 6 `give`, 7 `timeout`. **0 is
      "nothing" and 7 is unreachable** — `record.timeout()` (`:164-166`) is never called anywhere in `game.js`.
      1. **`enactMove`** (`:279-287`): `fuel[team] -= r² × FUEL_PER_MOVE`; the shadow is written at the destination
         and cleared at the origin; then `robot.y`, `robot.x` are updated. In that order, because a move onto your own
         square is impossible (rule 4.10 forbids `dx==dy==0`).
      2. **`enactAttack`** (`:289-317`): `fuel[team] -= ATTACK_FUEL_COST`; then a sweep of the **whole board**, **r
         (y) ascending outer, c (x) ascending inner** (`:293-294`) — the port sweeps only the `rad <= DAMAGE_SPREAD`
         neighbourhood **in the same order**, which is what fixes the order of multiple kills and therefore the
         reclaim. For each occupied square with `rad = (y+dy − r)² + (x+dx − c)² <= DAMAGE_SPREAD`: `target.health -=
         ATTACK_DAMAGE`, **with no team check and no attacker exclusion**; and if `health <= 0` and the target is
         **not** a `CASTLE` or `CHURCH`, the attacker collects `reclaimed_karb = floor((target.karbonite + build K /
         2) / rad_to_attacker)` and `reclaimed_fuel = floor(target.fuel / rad_to_attacker)`, each clamped by
         `Math.min(held + reclaimed, MY capacity)` (`:301-311`), and then `_deleteRobot(target)` (`:312`).
         `rad_to_attacker = (y − r)² + (x − c)²` is the attacker's **own** distance to the square being processed.
      3. **`enactBuild`** (`:249-254`): `karbonite[team] -= build K`; `fuel[team] -= build F`; then `createItem(x+dx,
         y+dy, team, build_unit)` (rule 6.5).
      4. **`enactMine`** (`:213-225`): **karbonite first** — if the pilgrim's square is on the karbonite map,
         `robot.karbonite = min(robot.karbonite + 2, 20)` and `fuel[team] -= 1`; **else** if it is on the fuel map,
         `robot.fuel = min(robot.fuel + 10, 100)` and `fuel[team] -= 1`; **else throw**. Two consequences, both
         ported: a square that is on **both** maps is impossible (the generator's `c_in` rejection, `game.js:258,269`)
         but the karbonite branch would win anyway; and **mining at capacity still costs the 1 fuel and yields
         nothing** (a wasted turn, counted as `mine_actions_wasted`).
      5. **`createItem`** (`game.js:430-464`): draw an id with `do id = 1 + floor(4095 × random()); while
         (ids.indexOf(id) >= 0)` and push it to `ids` (`:433-435`) — **the ONE live MT19937 draw site in the whole
         round loop** (D1), and the reason V4 exists; then the robot record with `health = STARTING_HP`, `karbonite =
         0`, `fuel = 0`, `turn = 0`, `signal = 0`, `signal_radius = 0`, `castle_talk = 0`, `time = CHESS_INITIAL`;
         `init_queue += 1`; **`if (shadow[y][x] === 0) shadow[y][x] = id`**; and **`robots.push(robot)`** — appended,
         so the new unit is reached later in the same round.
      6. **`enactGive`** (`:256-277`): throw if the destination shadow is 0; if the receiver is a `CASTLE` or a
         `CHURCH`, `karbonite[receiver.team] += give_karbonite` and `fuel[receiver.team] += give_fuel` — **the
         RECEIVER's team, which may be the enemy's**; else the amounts are first **reduced** to `min(give, receiver
         capacity − receiver holding)` and only then transferred. Finally `robot.karbonite -= give_karbonite`;
         `robot.fuel -= give_fuel` — **using the reduced amounts**, so nothing is lost to the void (the docs are
         wrong; see below).
      7. **`enactTrade`** (`:228-247`): `last_offer[team] = [karbonite, fuel]`; **if the two orders' offers are now
         element-wise equal**, reset `last_offer` to `[[0,0],[0,0]]` and then, **if the deal is payable**
         (`karbonite[0] >= k && karbonite[1] >= −k && fuel[0] >= f && fuel[1] >= −f`), execute `karbonite[0] -= k;
         karbonite[1] += k; fuel[0] -= f; fuel[1] += f` — else **throw, with `last_offer` already cleared**. The sign
         convention is the engine's: **positive means the resource moves RED → BLUE**. Both quirks are ported: the
         initial `last_offer` is `[[0,0],[0,0]]`, so the *first* castle to offer `(0,0)` "matches" and executes a zero
         trade; and an unpayable match still clears both standing offers.

**7. Death and removal** (`_deleteRobot`, `game.js:933-943`): `shadow[y][x] = 0`; `if (!initialized) init_queue -= 1`;
   **`robots.splice(indexOf(robot), 1)`**; and **`if (robot_index < robin) robin -= 1`**. Ids are **never returned to
   the pool** (V4).

### Where the docs are wrong — seven disagreements, and which wins

`app/src/views/docs.js` (and `coldbrew/starter/js_starter.js`, the library every bot inherits) are the human-readable
spec. **Where either disagrees with `coldbrew/game.js` or `coldbrew/action_record.js`, the ENGINE WINS**, and the port
follows the engine. Every disagreement found:

| # | the docs / the starter library say | the engine does | port follows |
|---|---|---|---|
| 1 | "broadcast a 16 bit message to all units within squared radius X², consuming X Fuel" (`docs.js:164`) | `ceil(sqrt(signal_radius))` — the docs' own worked example (`ceil(sqrt(10)) = 4`) agrees with the engine while the prose does not | **engine** |
| 2 | "assigned a unique 32 bit integer ID" (`docs.js:145`); `r.id` "an integer between 1 and 4096" (`:240`) | ids are drawn from **1…4095** without replacement from a pool that is **never refilled**, by a rejection loop that **hangs forever** at exhaustion (`game.js:433-434`) | **engine**, plus the V4 guard |
| 3 | round-1000 tiebreak is "the team with more total health" — ambiguous between castles and everything (`docs.js:138`) | sums `robot.health` over **every** live initialized unit of the team (`game.js:556-557`) | **engine** |
| 4 | implies the third rung is a distinct "coin flip" outcome (`docs.js:138`) | assigns `win_condition = 1` **unconditionally** after the round-1000 block (`game.js:604`), so a coin flip is *recorded* as "greater health" | **engine** (both numbers recorded, rule 5.3) |
| 5 | "If a unit tries to give a robot more than its capacity, the excess is loss to the void" (`docs.js:260,364,454`) | the record's own amount is **reduced first** and only the reduced amount is deducted from the giver (`action_record.js:268-276`) — **nothing is lost** | **engine** |
| 6 | "Can be called multiple times in one `turn()`; … **each signal will cost Fuel**" (`docs.js:267,371,461`) | the fuel is charged **once**, for the last radius only (`action_record.js:329`). The *starter library* debits the bot's own local `this.fuel` per call (`js_starter.js:105`), which is where the sentence comes from | **engine** |
| 7 | attack is "Available for Crusaders, Prophets, Preachers" (`docs.js:261`) and `js_starter.js:186` **throws** for a CHURCH | a **CHURCH attack is ACCEPTED** as a legal 0-damage, 0-fuel action that consumes the turn — measured, `record.action == 2` — because `ATTACK_RADIUS` is the scalar `0` and both `r > undefined` and `r < undefined` are false (D6) | **engine**; the chassis never emits it, and `tests/test_bc19_baselines.nim` asserts that |

### Decided divergences — every rule this port does NOT reproduce, with its reason

| # | Divergence | Reason |
|---|---|---|
| **V1** | **The wall-clock chess clock is not ported.** `robot.time` starts at `CHESS_INITIAL = 100` ms, gains `CHESS_EXTRA = 20` ms at the start of every turn (`game.js:759`), loses the turn's measured `wallClock()` elapsed (`:771`, `:805`), and a robot with `time < 0` is frozen (`:806-808`); `vm2`'s per-turn `timeout` is `TURN_MAX_TIME = 200` ms (`vm.js:6`). **It is driven by the wall clock and is therefore not reproducible even between two runs of the engine itself.** It is replaced by a deterministic `DecisionOps` clock whose per-turn **charge equals its per-turn refill**, so the clock is provably invariant and **no robot is ever frozen**. §Sim module gives the numbers and the theorem; Tier B′ proves the engine's own freeze branch never fired in any compared game **and** proves separately that it does fire when it should. |
| **V2** | **The `visible`-array shuffle is not ported.** `getGameStateDump` shuffles the array with the **global, unseeded `Math.random()`** (`game.js:717-722`). Measured: **five distinct orders in six identical runs**. The port presents `visible` in **ascending robot `id`**, and the oracle gets a **one-hunk `determinism.patch`** that replaces the shuffle with the same ascending-`id` sort **on the ENGINE side**, so both sides see the same order and neither is normalised alone. |
| **V3** | **Maps are generated at BUILD time and committed as JSON; the runtime sim never generates a map.** Two independent reasons. (a) `regions.sort(x => -1*x.length)` (`game.js:153`) passes a **one-argument, sign-constant comparator**, so the result is implementation-defined; measured under the pinned V8 it is a **plain reversal in 42 of 42 multi-region cases**, and the region kept passable is **NOT the largest in 40 of them** — the code's evident intent is not what it does, and reproducing it means reproducing a specific V8 sort. (b) **13 of the first 400 seeds produce unplayable boards** (0 castles, 2–4 passable squares) because that same reversal keeps a tiny pocket and the castle placement then exhausts its 1000-try counter (`:177-188`). So: `tools/gen_maps_bc19.mjs` runs the pinned engine under the pinned Node, filters for playability, and writes `data/maps/bc19/*.json` — **including the MT19937 state immediately after `makeMap()` returns**, so the runtime id stream is aligned bit-exactly (D1). |
| **V4** | **The id pool cannot hang.** The engine's rejection loop (`game.js:433-434`) never terminates once all 4095 ids are spent. The port reproduces the loop exactly and adds **one guard the engine lacks**: when `ids.len >= MAX_ID − 1`, a `build` is **refused** (a no-op, counted in `builds_refused` and `refused_actions`) instead of looping. Derived ceiling on the played pool: the richest map (`seed-0030`, 19 karbonite depots a side) funds at most ≈ 2 400 units a side over 1000 rounds, so the floor is not reached in practice; the guard exists because "degrade, never hang" outranks fidelity to a hang. |
| **V5** | **The `.bc19` byte replay, `coldbrew/vis.js`, the `vm2` sandbox, `coldbrew/compiler.js` and the Python/Java transpilers, `cli/cloud.js`, `cli/upload.js`, `update-notifier`, and the `logs`/`error` channels have no port.** The replay is this repo's own self-sufficient UTF-8 JSON re-derived by the wasm sim (§Server). The log channels carry `wallClock()` timestamps (`game.js:505,526`) and nothing a score or a spectator reads. |
| **V6** | **Win conditions 3 and 4 are unreachable**, and `record.timeout()` / `enactTimeout` (`action_record.js:164,205-211`) are dead code upstream. Every robot in this port has a chassis at creation, so `nulls[t]` is always 0. Recorded as *unreachable here* rather than *absent upstream*, and `tests/test_bc19_endladder.nim` asserts they are never produced. |
| **V7** | **`robot.time` is in neither the observation nor the trace.** It is wall-clock derived (V1), so exposing it would make a doctrine's prompt and a parity trace non-reproducible. `docs.js:241` lists it as readable; the port's `me` record simply does not carry it. |
| **V8** | **`MAX_MEMORY` / `object-sizeof` has no port.** The check is commented out in the engine itself (`vm.js:15-22`), so there is nothing to reproduce. |

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200` (`episode_timeout_minutes: 20`); 60 % = **720 s**. The `bc19` variant is
**best-of-three on three distinct maps from the `mixed` pool, played to the engine's own 1000-round cap**.

```
container start, map load, seat connect              <=  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    <=  75 s   (attempt1Ms 40 000 + retryMs 24 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 75 000)
match: 3 games x 1000 rounds                         <= 200 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 60)
score + replay write + shutdown grace                <=  30 s
                                                       -------
worst case                                             335 s   <= 720 s
```

The doctrine deadlines above were raised in **0.9.1** (from `attempt1Ms` 20 000 / `retryMs` 12 000 /
`doctrineBudgetMs` 45 000) because both doctrine attempts for one seat timed out against the bedrock sidecar in league
rounds 1 and 2 while the provider answered `200 OK` to every request.

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 75 s doctrine phase,
and both seats' calls go out as **one parallel batch**.

**Honest per-round estimate, so the builder can check it**, derived from the engine's own economy rather than guessed:

- **The census is karbonite- and fuel-bounded.** Karbonite: 100 initial plus **2 per pilgrim-turn on a depot**; the
  played pool carries **4 to 13 karbonite depots a side** (measured, §Sim module), so a side that works every depot
  from round ~60 banks 7 500–24 400 karbonite over the game — 500–1 600 crusaders at 15 each. Fuel is the tighter
  constraint: the flat trickle is only **25 500** over 1000 rounds while a crusader costs 50 fuel to build plus 1 per
  r² moved and 10 per attack, so the army is funded by fuel mining (**+10** a pilgrim-turn, 2–16 fuel depots a side)
  and a doctrine that ignores fuel starves. Realistic: **150–400 units built per side, peak alive 40–120 per side**,
  i.e. **80–240 robots on the board**.
- **Per turn** the port does a bounded vision scan (`⌊√100⌋ = 10`, a 21×21 box = 441 squares, and only for the units
  that ask), an O(n) pass over the robot list for the visible/radioable test, and the chassis's own work capped at
  **4 000 DecisionOps**. At n = 240 that is ≈ 1 800 ops a turn → ≈ 4.3 × 10⁵ a round → ≈ 4.3 × 10⁸ over a whole game.
  **The port does NOT reproduce the engine's two hot spots** — `getVisible`'s full-board mask and `enactAttack`'s
  full-board sweep — because both are provably equivalent to a bounded scan.
- **Estimate: 0.6–2.5 ms/round, i.e. 0.6–2.5 s per 1000-round game in release Nim.** bc23 measured 1.45–2.95 ms/round
  at 207–451 robots over 2000 rounds; bc19 has half the rounds and half the robots. Best of three is **2–8 s**,
  comfortably inside `matchBudgetSeconds 200` — the largest margin of any year in this repo, which is why bc19's
  budgets are the tightest ones here.
- **`tests/test_bc19_perf.nim`** plays a full 1000-round game on `seed-0045` (**64×64**, the largest legal board, 3
  castles a side, 12 karbonite and 12 fuel depots a side) with both seats on `opening: pilgrim_eco`, `pilgrim_curve:
  24`, `unit_mix: 0`, `preacher_share: 0`, `church_expansion: early`, `symmetry_wall: wall`, `fuel_reserve: 0` — the
  configuration that maximises unit count, movement and lattice size — and **fails CI above 40 s**.
- **If that gate ever goes red the fix is one config value** — `gamesPerMatch: 3 → 2`, then `→ 1` — and the note says
  so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc19's axis is **map-shaped**: `seed-0017` (41×41, **one castle a
  side**, 89.3 % passable) is a pure elimination game where losing the castle loses the match on the spot; `seed-0060`
  and `seed-0107` (**three castles a side at separation 14**) are preacher-rush maps; `seed-0048` (32×32, **2
  karbonite and 2 fuel depots a side**) makes `fuel_reserve` and `church_expansion` decisive; and `seed-0125` (13
  karbonite depots a side) is an economy map where `pilgrim_curve` and `church_expansion` pay. One map would rank the
  map, not the doctrine.
- Because this sim is **light** (well under 3 ms/round) and only 1000 rounds long — the shortest recording in this
  repo — **the phase-60 viewer check 8 is dispatched with the standard `settle=700 soak=10`** and `ci.yml`'s
  `wasm-viewer` job runs the bc19 replay at `--timeout 90 --soak 10`, joining bc26/bc20/bc21 rather than the heavy set
  (§Viewer). `docker-smoke` prints `sim_seconds / rounds` and `docs/RULES-BC19.md` records the measured value.

### Scoring, sign, and what the bc19 league ranks by

The 2019 game is win/lose; it has no point formula. This one is defined here, and it is a continuous reading of the
engine's own tiebreak ladder so that the score and the winner never tell different stories:

```
share(x, y)  = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
castles[t]   = CASTLEs of t alive at the final round                          # rung 1
health[t]    = sum of health over ALL of t's live units                       # rung 2 (the engine's own)
worth[t]     = karbonite(t) + fuel(t) div 5
             + sum over t's live units of (build K, or 0 for a CASTLE)        # our third term
points[t]    = int(64.0'f32 * share(castles[t], castles[o])
                 + 24.0'f32 * share(health[t],  health[o])
                 + 12.0'f32 * share(worth[t],   worth[o]))    # TRUNCATION, not rounding
```

Six load-bearing details, each pinned by a test vector in `tests/test_bc19_scoring.nim`:

- The first two terms are **exactly the engine's two deciding rungs, in the engine's own priority order** (rule 5.2
  rungs 5 and 6), so a doctrine that wins the game usually wins the shape of it too.
- The third term is the game's economy in **karbonite-equivalent**, and `fuel div 5` is the engine's own exchange
  rate, not a taste: one `mine` action buys **2 karbonite or 10 fuel** (`KARBONITE_YIELD` / `FUEL_YIELD`), so 1
  karbonite = 5 fuel at the margin. A `CASTLE`'s build cost is `null` (it cannot be built) and contributes **0**; a
  `CHURCH` contributes **50**.
- **Every quantity here is already an integer** — bc19 has no float state at all — so unlike bc16 there is **no
  tenths-narrowing anywhere**. The only floats in the formula are the three `float32` shares and the truncating
  `int()`, which is what makes `points` reproducible bit-for-bit between the native recorder and the wasm re-deriver.
- The weights are **super-increasing** (`24 > 12` and `64 > 24 + 12`), so a *decisive* margin on a higher rung
  dominates everything below it. **This note claims no more than that.** A one-castle margin on a 3-vs-2 board is `3/5
  − 2/5 = 0.2` of 64 = **12.8 points against 36 available below**, so **`points` alone can favour the loser**; it
  measures the *shape* of the game, not who won it.
- `share` returns **0.5 on a 0–0 total** (the bc16/bc22–bc25 choice): two orders that both ended castle-less should
  not be separated by an arithmetic accident, and rung 4 of the ladder proves that is a real outcome. `points` is in
  `[0, 100]` and the seats sum to ≤ 100.
- The `end_reason` is **not** computed from `points`: the ladder uses the engine's exact integer comparisons (rule
  5.2), so a razor-thin margin can decide the *winner* on a difference that rounds away in *points*. Stated
  explicitly, tested explicitly, and not a bug.

```
results.scores[t] = 200.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** bc19 joins `winBonusFor`'s **200** set (`match.nim:604-625`) for exactly the reason bc22 and
bc16 did: `points` can legitimately favour the loser, so only a bonus that dominates the whole `[0, 100]` range keeps
the ordering of `results.scores` **provably** in agreement with `results.wins`. A 2–0 gives `400 + mean` against `≤
100`; a 2–1 gives `400 + mean` against `200 + mean ≤ 300`. `tests/test_bc19_scoring.nim` asserts that agreement on 500
random synthetic finals, including clinched two-game matches, and asserts the super-increasing property and the
documented `points`-disagreement case explicitly so neither is mistaken for a bug later.

**The `bc19` league ranks by ELO over match wins**, computed by the platform from the episode's winner;
`results.scores` is the per-episode number the ladder reads and its ordering agrees with `results.wins` exactly, as
above — the same shape as the eight shipped leagues. A `deadline` episode scores the games that finished; a `fault`
episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `win_condition` mapped to this repo's snake_case vocabulary,
plus our one wall-clock value. `results.games[].win_condition` carries the engine's own integer beside it, so a replay
always traces back to a branch of `isOver`:

| `end_reason` | engine origin | `win_condition` | meaning | can fire early? | new to the manifest enum? |
|---|---|---|---|---|---|
| `castles_destroyed` | `game.js:579-586` | **0** | one order's **last CASTLE** died; fires the instant it dies, and the game stops before the next robot acts | **yes** — the normal way a bc19 game ends | **NEW** |
| `coin_flip` | `:587-590` (both castle-less) **and** `:600-604` (round 1000, castles and health both level) | **2** / **1** | decided by a single `random() > 0.5` draw from the seeded MT19937 | the `:587` form yes; the `:600` form no | **REUSED** (bc22's, identical meaning) |
| `more_castles` | `:591-595` | **0** | round 1000 reached; more castles alive | no | **NEW** |
| `more_unit_health` | `:597-599` | **1** | castles level; greater **total health of all live units** | no | **NEW** |
| `abandoned` | — | `-1` | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded | — | already present |

**Exactly THREE values are added** — `castles_destroyed`, `more_castles`, `more_unit_health` — and **two are reused**,
`coin_flip` and `abandoned`. **`opponent_failed_to_initialize` and `both_failed_to_initialize` are NOT added**: win
conditions 3 and 4 are unreachable in this port (V6). `annihilated` is deliberately **not** reused for
`castles_destroyed` even though bc21's and bc22's semantics are similar, because `docs/RULES-BC2x.md` already
documents `annihilated` as *those* years' factor and a bc19 replay must trace to `win_condition 0` by way of the
castle-annihilation branch; the two reuses above are taken only where the engine's own words are the same.

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from the eight shipped years**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped (a spend that would take a stockpile negative, a robot spawned onto an occupied square, an id-pool exhaustion, or the port's own hash-chain invariant): a partial replay and `[0, 0]` are still written | `[0, 0]` |

**Best-of-N clinch semantics, stated because phase 60 has judged this wrong before (2026-09-07):** a side that takes 2
games settles the episode immediately. An episode that records **two** games with `reason: complete` on a
`gamesPerMatch: 3` variant is **correct**, not truncated; `results.games` carries only the games actually played, and
`replay.plan.maps` carries all three drawn maps so a spectator can see what the third would have been.

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the eight shipped
years). Container exit codes are unchanged: `0` whenever results + replay were attempted (including
`deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep answering for the ~20 s shutdown grace,
and the websocket handler keeps its `Ping → Pong` **payload echo** and does not filter binary frames
(`tools/ci/cert_probe.py` proves both against the real image).

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged from the shipped years: the player container is a thin registrar and every
decision is taken inside the **game** container, because that is the only container the platform injects the
`anthropic_api_key` coworld secret into (`game.runnable.env.ANTHROPIC_API_KEY_URI =
secret://coworld/battlecode/anthropic_api_key`, `coworld_manifest_template.json`).

**One decision turn, one parallel batch.** Both seats are asked at the same moment and their two provider calls go out
as **ONE parallel batch** (`curly.makeRequests`, `decide.nim`'s existing shape) with the same deadline; seats are
**never** queried one after another. The batch's wall-clock budget is `doctrineBudgetMs = 75 000` — attempt 1
`attempt1Ms = 40 000`, the single retry `retryMs = 24 000` (raised in 0.9.1, §Match shape and budget) — which is the
per-turn budget for this game and sits
inside the 720 s envelope computed in §The game. At most **2 provider calls per seat per episode**.

`src/battlecode/llm.nim` is unchanged and year-neutral: the credential ladder (Bedrock sidecar → `ANTHROPIC_API_KEY` →
`ANTHROPIC_API_KEY_URI`), the single Bedrock candidate `us.anthropic.claude-haiku-4-5-20251001-v1:0`, fence-tolerant
JSON extraction, the `throttled` fast-fail, rune-boundary truncation, `maxOutputTokens = 1200`. With no credentials
the client disables itself at construction and every seat falls back instantly, which is what lets offline
certification and `docker-smoke` finish in seconds.

### The envelope pin — already fixed year-neutrally, and what bc19 must still do

The bc23 league failure (LEARNINGS 2026-09-08: champions wrapping the sheet in `{"protocol":…,"doctrine":{…}}`, all
knobs landing in `sheet_unknown_fields`, the seat playing the schema-default sheet with `defaults_applied == []`, in 2
of the first 3 rounds) was fixed year-neutrally by the bc22 run and is **already on `main`**: `sheet.nim:92-155`
resolves the sheet node in the order `""` (the payload carries a known knob key) → `"sheet"` → `"doctrine"` → the
single object-valued key, unwraps **at most once**, and records which rule fired in `Sheet.envelope`, which
`replay.nim` writes as `seats[].sheet_envelope` and `results.nim` as the top-level `sheet_envelope`. **bc19 changes
none of that.** Its three obligations are:

1. **A `YearBc19` arm** in `knownKeysFor`, `defaultSheet`, `validate`'s `case`, `toJson` and `plainWords`
   (`sheet.nim:46,78,188,214,227` are where the bc16 arms sit) — the five-line shape bc21–bc25 and bc16 added.
2. **Absent-key defaulting counted, in `years/bc19/knobs.nim` only.** `applyKnobs19` adds an **absent** known key to
   `defaultsApplied` as well as a repaired one, exactly as `years/bc22/knobs.nim` and `years/bc16/knobs.nim` do, so
   `sheet_defaults_applied` for a bc19 seat is `[]` only when the cog really set all eleven knobs. This is
   deliberately **not** done year-neutrally: doing so would change what a bc16/bc20/bc21/bc23/bc24/bc25/bc26 episode
   records in that array. `tests/test_bc19_sheet.nim` asserts that a bc19 empty sheet reports all eleven names **and**
   that a bc23 empty sheet still reports none, so the change is provably scoped.
3. **The divergence is rendered.** `#bc19-doctrines` draws, per seat, the applied sheet in plain words **and** a badge
   when the two disagree: `envelope: doctrine · 11 of 11 knobs defaulted`, and the first 120 runes of
   `sheet_submitted` under a "what the cog actually sent" disclosure — the `renderDoctrines` shape already in the
   page, with bc19 ids. A seat that played the default sheet is visible to a spectator in one glance.

### The bc19 doctrine sheet — eleven knobs, **no `chassis` key** (the D1 rule)

Each knob has a type, a range, a default, and a named site in the bc19 chassis. Unknown key, wrong type or
out-of-range value → **that field's default** (integers **clamp** instead), recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit a match by answering badly — only by
answering weakly. **The chassis is not a knob**: a submitted `chassis` key is recorded in `sheet_unknown_fields` and
ignored (`sheet.nim`'s existing behaviour, GV04), so `examplefuncsplayer19` is reachable **only** through
`PLAYER_SCRIPTED=examplefuncsplayer19`.

**The anti-inert rule, stated as a rule the builder must hold every knob against: no setting of any knob, and no
combination of settings, may produce an inert or self-starving order.** The strategy surface lives *inside one
competent chassis*. Concretely, and independently of every knob, `saber` always: keeps **at least one PILGRIM on a
karbonite depot and at least one on a fuel depot** from the first affordable build, and never lets a pilgrim idle
loaded within reach of a deposit point; **builds a military unit whenever karbonite and fuel allow and the military
census is below its target**, and never fewer than **2 military units per structure**; **answers any enemy unit sensed
within `defend_radius` of one of its own structures**; **never leaves a castle without an adjacent free square to
build into**; **never fires a PREACHER when the blast would kill more of its own units than the enemy's**; and **never
`give`s to an enemy structure** (legal, rule 6.6, and never a strategy). Every knob moves *how much of what, when* —
never *whether it plays*. `tests/test_bc19_knobs.nim` proves each knob has teeth and `tests/test_bc19_survival.nim`
proves the floor holds, **with a negative control that must fail** (§Tests items 17, 18).

| field | type / values | default | what it changes (`src/battlecode/years/bc19/chassis/…`) |
|---|---|---|---|
| `opening` | `turtle` \| `preacher_rush` \| `pilgrim_eco` | `pilgrim_eco` | `econ.nim plan()` — the first-300-round budget split and posture, and the three archetypes the 2019 season actually produced. **`turtle`**: spend on PROPHETs (25 karbonite, damage at **r² 16–64** and blind inside 16) behind a lattice on the own side of the midline, keep the pilgrim count at the knob's floor, and win the round-1000 castle count — but **pilgrims are still built and depots are still worked**, the economy target is halved, never zeroed. **`preacher_rush`**: from round 1, spend the whole military budget on PREACHERs (30 karbonite, 60 HP, **20 damage over nine squares**) and walk them at the mirror of your own castle; a preacher one-shots a pilgrim (10 HP) and a prophet (20 HP) and two-shots a crusader, so an early wave that reaches a mining line ends the economy. The dev nerf the idea names is exactly why this is a knob and not the chassis's default. **`pilgrim_eco`**: ramp pilgrims to `pilgrim_curve` per structure by round 100, work every depot within reach, and buy military only to satisfy `defend_radius` until round 250. |
| `pilgrim_curve` | int **0 … 24** | 9 | `econ.nim pilgrimTarget(round)` — pilgrims wanted **per structure** at round 100, ramped linearly from 1 at round 1 and held after. A pilgrim is 10 karbonite / 50 fuel and returns **+2 karbonite or +10 fuel a turn** while it stands on a depot, so the payback is ~5 turns of karbonite mining and the ceiling is the number of depots (measured **4–13 karbonite and 2–16 fuel depots a side** on the played pool). At 0 the order still builds **one** pilgrim per structure — the floor that keeps 0 from starving — and at 24 it builds more pilgrims than there are depots, which wastes karbonite and crowds the castle's build squares. Clamped. |
| `church_expansion` | `never` \| `mid` \| `early` | `mid` | `church.nim plan()` — when a PILGRIM spends **50 karbonite / 200 fuel** on a CHURCH. A church is a second spawn point **and** a second deposit point, which is what turns a remote depot cluster from a long walk into a local economy; it has **100 HP** and no attack, so it is also a free 100 HP gift to a raider. `early`: as soon as a cluster of ≥ 3 depots is found at Chebyshev ≥ 3 from every existing structure (the wololo `MINIMUM_CHURCH_DISTANCE` rule). `mid`: only after round 200, and only when karbonite income is below the `pilgrim_curve` target. `never`: every mine is walked back to a castle, which on a 64×64 board is a 30-turn round trip. |
| `fuel_reserve` | int **0 … 2000** | 300 | `econ.nim fuelGate()` — the global fuel floor below which the order funds **only `mine` and `move`**: no attack, no build, no signal. Fuel is the thing that stops a bc19 army dead — the only passive income is **25 a round**, an attack is 10–25 and a preacher's move is **3 per r²** — and an order at 0 fuel cannot move, cannot shoot and cannot build, so it just stands there and dies. At 0 the order spends to the last unit of fuel; at 2000 it hoards and under-builds. Clamped. |
| `unit_mix` | int **0 … 100** | 45 | `military.nim mix()` — the percentage of the **military karbonite budget** spent on **PROPHETs** rather than CRUSADERs. A prophet is 25 karbonite, 20 HP, hits for 10 at **r² 16–64** and **cannot hit anything inside r² 16**; a crusader is 15 karbonite, 40 HP, hits for 10 at r² 1–16 and moves at **r² 9 — twice as far per turn as anything else in the game**. So this knob is literally "reach or legs", and it interacts with `symmetry_wall`: a lattice wants prophets, a rush wants crusaders. Clamped. |
| `preacher_share` | int **0 … 100** | 20 | `military.nim mix()` — **ADDED, and measured.** The percentage of the *remainder after prophets* spent on **PREACHERs**, so the crusader share is `(100 − unit_mix) × (100 − preacher_share) / 100`. A preacher costs 30 karbonite and **20 damage lands on every occupied square within r² 3 of its target, with no team check** — including its own square when it fires at anything closer than r² 4 (measured: 60 → 40 HP). Against a dense lattice it is the best unit in the game; inside one it is a friendly-fire disaster. `micro.nim` refuses a shot that would kill more of its own units than the enemy's at **every** setting, which is the floor that keeps 100 from being self-destructive. Clamped. |
| `church_saber_round` | int **0 … 1000** | 0 | `infiltrate.nim schedule()` — 0 means **never**; otherwise the round at which a PILGRIM plus a two-unit escort is committed to building a CHURCH **inside the enemy's half**, which is the emergent qualifier play the idea names. The infiltrating church then builds units in their economy, and because it is a *structure* it is also a deposit point for anything the escort reclaims off their pilgrims. It costs 50 karbonite, 200 fuel, a pilgrim and two escorts, and the escort has to survive a walk across the mirror — so it is a real investment with a real failure mode. Clamped. |
| `symmetry_wall` | `off` \| `screen` \| `wall` | `screen` | `lattice.nim plan()` — what the order builds on the mirror line, which **both sides know from round 1** because every robot gets the whole terrain map on its first turn. `off`: no static line; military units walk at the mirror of their own castle (the wololo `TARGET_MIRROR` behaviour). `screen`: a **sparse** prophet lattice on the own-half side of the narrowest passable corridor, occupying every other square so pilgrims can still pass and a preacher blast can only catch one prophet. `wall`: a **dense** lattice on the same line, which stops crusaders cold and also **blocks your own pilgrims** and turns one enemy preacher shot into three dead prophets. The trade-off is the point. |
| `castle_talk_use` | `position` \| `census` \| `full` | `census` | `comms.nim castleTalk()` — what the **8-bit, free, unlimited-range, castle-only** channel carries. It is one byte per unit per turn and it is the only global channel in the game, so its layout is a real choice. `position`: turn 1 and 2 carry `0b10 \| x:6` then `0b11 \| y:6`, so every castle learns every friendly structure's coordinates and can derive the enemy's by mirroring. `census`: adds a rotating `0b0 \| unit:3 \| bucket:4` census digit so the castles can divide one build queue between them without duplicating. `full`: adds `0b01 \| alert:6` — under-attack and castle-destroyed flags — which is what lets the surviving castles re-plan when one falls, at the cost of the census slot on the turns it fires. |
| `defend_radius` | int **1 … 400** (r²) | 100 | `military.nim defend()` — the squared radius around a friendly structure inside which a military unit breaks off whatever it is doing to answer an enemy. 100 is a castle's own vision radius, so the default is "defend what you can see"; 400 is r = 20, a fifth of a 64-wide board. At 1 the order never defends and its pilgrims are farmed for reclaim; at 400 nothing ever attacks. Clamped. |
| `trade_policy` | `never` \| `mirror` \| `offer_fuel` \| `offer_karbonite` | `mirror` | `trade.nim plan()` — **ADDED, and it is this year's largest unexploited mechanic.** A CASTLE may `proposeTrade(karbonite, fuel)`; when both orders' standing offers match element-wise the swap executes and both offers clear (rule 6.7). The engine's own docs call it "collaborate with the opposing team for mutual benefit" (`docs.js:149`). `never`: no castle ever proposes. `mirror`: a castle re-offers the enemy's own `last_offer` back — which matches it and executes it — **only when the deal is in our favour at the engine's own 1 karbonite = 5 fuel rate**, so a good offer is accepted and a bad one is refused. `offer_fuel`: stand a repeated offer of `karbonite = −k, fuel = +5k`, sized by our fuel above `fuel_reserve` (we sell fuel, buy karbonite — the right trade for a fuel-rich, depot-poor map). `offer_karbonite`: the mirror image. The sign convention is the engine's (**positive means RED → BLUE**), and the chassis converts from "we/they" through the game's `sideAslot`. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on **rune**
boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — the archetype rock-paper-scissors the 2019 season
produced — against the two mechanics that diversity never systematically spent, so the league's headline matchup is
the question this year never got asked.

- **champion #1, `battlecode-bc19-saber` (daveey)**: *"You command a religious order in Battlecode 2019 'Crusade'.
  Every board is a mirror: on turn one every one of your robots is handed the whole terrain map, the whole karbonite
  map and the whole fuel map, so you already know where their castles are — they are the mirror image of yours.
  Karbonite builds units and fuel runs them, and the only free income in the game is 25 fuel a round. A PILGRIM costs
  10 karbonite and 50 fuel and mines 2 karbonite or 10 fuel a turn while it stands on a depot; it must walk the load
  back to a castle or a church to make it spendable. A CHURCH costs 50 karbonite and 200 fuel, can only be built by a
  pilgrim, and is a second spawn point AND a second deposit point. Your doctrine: out-mine them, expand to the far
  depots, and win on castles at round 1000. Set opening \"pilgrim_eco\", pilgrim_curve 10-18, church_expansion
  \"early\", fuel_reserve 200-600, unit_mix high (60-90) because a PROPHET shoots from range-squared 16 to 64 and a
  lattice of them is very hard to walk into, preacher_share low (0-20), symmetry_wall \"screen\" or \"wall\",
  defend_radius 100-250, castle_talk_use \"census\" or \"full\". Set church_saber_round deliberately and say why: a
  pilgrim plus two escorts can build a CHURCH in THEIR half and spawn units inside their economy. Set trade_policy — a
  castle can barter karbonite for fuel with the enemy's castle, and one mining turn is worth 2 karbonite or 10 fuel,
  so five fuel to a karbonite is the fair rate; say which side of that trade you want. In notes, say which depot
  cluster you take first and what you do if their preachers arrive before round 200."*
- **champion #2, `battlecode-bc19-preachers` (daveey-1)**: *"You command a religious order in Battlecode 2019
  'Crusade'. Everyone in 2019 built an economy. Two things nobody spent properly. First: the PREACHER. It costs 30
  karbonite, has 60 health, and its attack puts 20 damage on EVERY OCCUPIED SQUARE within range-squared 3 of the
  square it targets — nine squares — WITH NO TEAM CHECK. A PILGRIM has 10 health and a PROPHET has 20, so one preacher
  shot deletes a mining line or a lattice. Its minimum range is 1, so if it fires at something adjacent it damages
  ITSELF and every friendly beside it — which means a dense wall of your own prophets is a liability against theirs.
  Second: the BARTER. A castle can propose a karbonite-for-fuel swap to the enemy's castle, and if the two standing
  offers match exactly the swap happens. Fuel trickles at 25 a round and karbonite does not trickle at all, so a
  fuel-rich order can buy an army from a karbonite-rich one. Your doctrine: set opening \"preacher_rush\" or
  \"pilgrim_eco\", preacher_share high (40-80), unit_mix low (0-30) because a CRUSADER moves range-squared 9 a turn —
  twice as far as anything else — and preachers need an escort that can keep up, symmetry_wall \"off\" or \"screen\"
  (never \"wall\": your own dense lattice is what their preachers are hoping for), pilgrim_curve 4-10, fuel_reserve
  low-to-middling (0-300) because a preacher move costs 3 fuel per range-squared and you would rather spend it than
  bank it, church_expansion \"never\" or \"mid\", defend_radius 1-100, castle_talk_use \"full\" so your castles know
  the moment one is under attack, and trade_policy \"offer_fuel\" or \"offer_karbonite\". In notes, say which of their
  castles your first preacher wave walks at and what you offer them in the barter and why."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every default and
range, the constant tables (the six unit types with karbonite and fuel cost, health, damage, attack range with its
**minimum**, splash radius, speed, fuel per move, vision and capacity; the economy; the reclaim formula; the radio and
castle-talk rules; the end ladder), the map cards for all three games **with their depot counts, castle positions and
symmetry axis**, the scoring formula, the alias pair, a **HOW A GAME ENDS** section (the bc21 r1-F8 fix, kept), and
the reply contract ("reply with ONE JSON object whose top-level keys are the knob names; your reply must begin with
`{`"). The assistant turn is prefilled with `{` and the prefix re-attached before parsing (the procgen 0.1.2 scar),
unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`, `:51-95`). It gains a `bc19` arm with
two published names. **The manifest still declares only `awu` and `scaffold`** — the two ids the certification fixture
seats — and `PLAYER_SCRIPTED` resolves **per year**, exactly as bc16 and bc20–bc25 do:

| `PLAYER_SCRIPTED` | on `year: "bc19"` resolves to |
|---|---|
| `awu`, `saber`, `wololo`, or anything unrecognised | **`saber`** — the strong doctrine chassis and the champions' chassis |
| `scaffold`, `example`, `examplefuncsplayer`, `examplefuncsplayer19` | **`examplefuncsplayer19`** — the deliberately weak floor and the parity oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field.
`defaultBaselineFor("bc19")` is `saber`, so a seat that says nothing useful plays the strong doctrine, not the weak
floor. `Baseline` gains `blSaber = "saber"` and `blExamplefuncsplayer19 = "examplefuncsplayer19"`; `ScriptedChassis`
gains `scSaber = "saber"` and `scExamplefuncsplayer19 = "examplefuncsplayer19"`. **`wololo` is deliberately NOT reused
as the name** even though Team Wololo's bot is the behaviour source: `scWololo`/`blWololo` are bc22's strong chassis
(`sim_types.nim:267`), and a duplicate enum string would compile and then seat the wrong bot.

**`saber` — the strong baseline and the champion chassis.** A behaviour port of `m-schier/battlecode-2019-wololo` at
`ebdd279` (GPL-3.0), parameterised by all eleven knobs. The correspondence, file by file, is in `NOTICE`; the
algorithm is:

- **`kit.nim`** — the per-side memory every robot shares and the `DecisionOps` charging: the terrain, karbonite and
  fuel maps (handed to every robot on its own turn 1 and cached), the **mirror function** derived once from the maps
  (`isXAxisMirrored` / `mirror`, `robot.js:733-786`), the remembered structure roster (own from castle talk, enemy
  from the mirror and from sightings), the remembered depot roster with a claim flag, and the navigator: **Dijkstra
  over the passable map with the real per-step fuel cost** (`r² × FUEL_PER_MOVE`, `PriorityQueue.js` + `Lattice.js`),
  with the two modes wololo calls `NAV.ECONOMIC` and `NAV.FASTEST` (`robot.js:31-34`) — economic prefers many cheap
  r²-1 steps, fastest prefers the largest legal r² per turn. **Every node expanded is charged 1 `DecisionOps`**, and
  the budget is checked before the search starts, never inside it.
- **`econ.nim`** — `plan()` (from `opening`), `pilgrimTarget()` (from `pilgrim_curve`), `fuelGate()` (from
  `fuel_reserve`), and the per-structure commitment ledger so two castles cannot promise the same 15 karbonite. It is
  the only place karbonite or fuel is ever committed, and it holds the unconditional floor: **≥ 1 karbonite pilgrim
  and ≥ 1 fuel pilgrim**, and **≥ 2 military per structure**.
- **`castle.nim`** — a castle's turn, in the engine's own action order: castle talk first (it is free and can
  accompany any action), then a build into the free adjacent square nearest the frontier (never boxing itself in),
  then — if nothing to build and an enemy is inside r² 64 — an attack for 10 damage and 10 fuel. **`church.nim`** —
  `plan()` per `church_expansion`: the depot-cluster score (wololo's `findBestConstructSpotWithScore`,
  `robot.js:1311-1398`) with the Chebyshev-3 minimum distance, and a church's own build queue once it exists.
- **`pilgrim.nim`** — the mine/construct/dropoff/scout state machine wololo calls `WORKER_STATE` (`robot.js:68-74`):
  claim the nearest unclaimed depot by Dijkstra cost, mine to capacity (never past it — a mine at capacity burns 1
  fuel for nothing), walk to the nearest structure, `give` everything, repeat; and take the `infiltrate.nim` job when
  it is scheduled.
- **`military.nim` + `micro.nim`** — the war. `mix()` (from `unit_mix` and `preacher_share`), `defend()` (from
  `defend_radius`), and the state machine wololo calls `MILITARY_STATE` (`robot.js:60-66`: `TARGET_MIRROR`, `HOLD`,
  `TARGET_TARGETS`, `HOME`, `CHARGE`) with its 6-turn charge window (`CHARGE_DURATION`, `:86`). `micro.nim` builds a
  **damage map** of every square an enemy can hit next turn and implements `findBestDodgeSpot` (`:1459-1528`) and
  `findBestAggressiveMoveCombat` (`:1529-1573`); target selection prefers, in order, a target this attack will
  **kill**, then the highest-value enemy inside range (castle, church, preacher, prophet, crusader, pilgrim), and for
  a PREACHER it **scores the whole nine-square blast and refuses any shot whose own-side kills exceed its enemy
  kills** — at every `preacher_share`.
- **`lattice.nim`** — `plan()` per `symmetry_wall`: the lattice parity (`LATTICE_DENSE` vs the every-other-square
  screen, `robot.js:97-131`), placed on the own-half side of the narrowest passable corridor found on the mirror line.
- **`comms.nim`** — the two channels, and the one place this year is *harder* than the others: there is no shared
  array. The **radio** is a 16-bit value with a fuel cost of `ceil(sqrt(r²))` that **every unit of both teams within
  the radius can read, along with the sender's id and position but NOT its team** (`docs.js:164`), so the layout must
  be worth leaking: `kind:3 | x:6 | y:6 | flag:1`, with kinds `0 hold`, `1 scout-report`, `2 target`, `3 charge`, `4
  repulse`, `5 depot-claim`, `6 lattice-slot`, `7 saber-go` — wololo's own `RADIO_PRIO` set (`robot.js:36-42`) minus
  anything whose disclosure costs more than the coordination is worth. The chassis broadcasts **at most one radio
  message per unit per five turns** and sizes the radius to the smallest that reaches the intended listener. **Castle
  talk** is 8 bits, free, unlimited range and readable only by own-team castles, laid out per `castle_talk_use` above
  (wololo's `CASTLETALK_PRIO`, `:45-51`).
- **`trade.nim`** — `plan()` per `trade_policy`, including the sign conversion and the payability pre-check, so the
  chassis never proposes a match it cannot pay (which would clear both offers and throw). **`infiltrate.nim`** —
  `schedule()` per `church_saber_round`: the target square (a passable square in the enemy half at Chebyshev ≥ 3 from
  every known enemy structure and within 2 of a depot), the escort assignment, and the abort rule if the pilgrim dies
  on the way.

**`examplefuncsplayer19` — the weak floor and the parity oracle's other side.** A port of
`coldbrew/bots/example_js/robot.js` at the pinned commit (GPL-3.0, inside the engine repository), and the **only** bot
in this year module that exists in two implementations that must agree statement-for-statement:
`years/bc19/chassis/examplefuncsplayer19.nim` and `tools/oracle/bc19/examplefuncsplayer19/robot.js`. Its whole
behaviour, after the **two committed patch hunks** below:

1. A per-robot `step` counter starting at `-1`, incremented at the top of every turn.
2. A **CASTLE**: on every turn where `step % 10 == 0`, `buildUnit(CRUSADER, 1, 1)`; otherwise nothing.
3. A **CRUSADER**: `move(choice)` where `choice` is drawn from
   `[[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]]` — the engine's own N, NE, E, SE, S, SW, W, NW order — by
   the patched RNG.
4. **Every other unit does nothing at all** — so it never builds a pilgrim, never mines, never builds a church, never
   signals, never trades and never defends. That is what being the weak floor means, and it is why the substance
   assertions that need those things are asserted **across the pair** and not per seat (§Tests, `docker-smoke`).
5. **It may not gain behaviour: it is one side of the differential oracle**, and
   `tests/test_bc19_examplefuncsplayer19.nim` asserts its RNG call sequence and its branch order against a recorded
   oracle trace.

**The two patch hunks** (`tools/oracle/bc19/examplefuncsplayer19/determinism.patch`, applied to the pinned checkout in
CI, mirroring `tools/oracle/examplefuncsplayer20/determinism.patch`):

| hunk | change | reason |
|---|---|---|
| 1 | `Math.floor(Math.random()*choices.length)` → `Math.floor(rng()*choices.length)`, where `rng` is a **`java.util.Random` seeded from the robot's own id**, created once per robot | the stock line draws from the wall-clock-seeded global RNG, so the stock bot is not reproducible even against itself and no bit-exact parity is possible with it. A `java.util.Random` is chosen rather than a second MT so the port can reuse `src/battlecode/rng.nim` unchanged, and Tier A″ is then also a test of that module against a **second** independent stream. |
| 2 | `if (this.me.team == 1) return this.buildUnit(...)` → `return this.buildUnit(...)` | the stock bot's castle build is gated on `team == 1`, so **RED never builds anything at all**. A baseline that is completely inert on one of the two sides cannot be scored, cannot fill a league and makes the survival gate meaningless. Recorded in `docs/RULES-BC19.md` §Divergences and in `docs/PARITY.md` §bc19. |

Its scripted reply is the all-defaults sheet (it reads no knob). Both replies go through the **same** `sheet.validate`
the LLM path uses, which is what makes the bounded-orders test meaningful and an LLM doctrine and a scripted one
strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (40 000) | one retry with `retryMs` (24 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `saber` chassis, `results.fallbacks[seat] = 1`, a **`doctrine_fallback` event** names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` (75 000) | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default (or clamps, for the six integers); the rest of the sheet applies |
| the sheet arrives inside an envelope | it is unwrapped **once**, the envelope key is recorded in `seats[].sheet_envelope`, and the knobs apply |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds` (60), or the match exceeds `matchBudgetSeconds` (200) | the running game is **abandoned**, finished games are scored, `results.reason = deadline`, `plan.abandonAfter[g]` records the round it stopped at |
| the id pool would be exhausted (V4) | the `build` is refused, counted in `builds_refused`, and the game continues — never an infinite loop |
| a side takes 2 games | the episode settles immediately — no padding (§The game, clinch semantics) |
| a sim invariant trips (negative stockpile, spawn onto an occupied square, hash-chain break) | `results.reason = fault`, `scores = [0, 0]`, and a **partial replay is still written** |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `saber` baseline reply, and it is exactly the all-defaults sheet:

```json
{"sheet":{"opening":"pilgrim_eco","pilgrim_curve":9,"church_expansion":"mid",
          "fuel_reserve":300,"unit_mix":45,"preacher_share":20,
          "church_saber_round":0,"symmetry_wall":"screen",
          "castle_talk_use":"census","defend_radius":100,
          "trade_policy":"mirror"},
 "notes":"default saber doctrine","motto":"Mine, then march."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing gameplay-related lives
outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc19/constants.nim` | **new, generated** | every `coldbrew/specs.json` scalar plus the whole six-row `UNITS` table with its thirteen fields, emitted by `tools/gen_year_constants.py --year bc19` from the pinned checkout; CI regenerates and byte-diffs. The bc19 arm reads **JSON**, not Java, so it is the simplest arm the tool has |
| `src/battlecode/years/bc19/mt19937.nim` | **new** | MT19937 as `mersenne-twister@1.1.0` implements it: `initSeed(s)` = `init_genrand` with `mt[0] = s and 0xFFFF_FFFF`, the 624-word state with `M = 397`, `MATRIX_A = 0x9908b0df`, the tempering shifts, and `random(): float64 = float64(randomInt()) * (1.0 / 4294967296.0)`. **Year-local, not in `rng.nim`**: `rng.nim`'s docstring scopes it to `java.util.Random` + `IDGenerator`, no other year needs MT, and bc19 needs to *save and restore* the whole 624-word state (V3) which no other year's generator does |
| `src/battlecode/years/bc19/units.nim` | **new** | the pure per-unit arithmetic: the `UnitKind` enum in the engine's ordinal order (`castle`, `church`, `pilgrim`, `crusader`, `prophet`, `preacher`), the thirteen-column table, the build/move/attack/mine/trade/give predicates as the engine's own guards express them (D6), and `signalCost(r2)` reading the committed table |
| `src/battlecode/years/bc19/world.nim` | **new** | world state: the three boolean maps, the **occupancy shadow** as a `seq[int32]` indexed `y*width + x`, the robot table, the **`robots` array as an insertion-ordered `seq[Robot]` with `robin` as an index into it and by-value removal**, team karbonite and fuel, `last_offer`, the spent-id set, and `createItem` / `deleteRobot` |
| `src/battlecode/years/bc19/actions.nim` | **new** | `processAction`'s validation ladder (rule 4) and `enact`'s dispatch (rule 6), in one file because the two halves have to stay in the engine's own order and the `temp_fuel` handoff between them is the easiest thing in this year to get wrong |
| `src/battlecode/years/bc19/resources.nim` | **new** | the trickle, mining, `give`, the reclaim formula with its `rad_to_attacker == 0` clamp, the barter with both quirks, and the `worth` sum the score reads |
| `src/battlecode/years/bc19/vision.nim` | **new** | the bounded vision box (`⌊√VISION_RADIUS⌋`, tabled), the `visible`/`radioable` predicates, the field-stripping ladder of rule 3.5-3.6, and the **ascending-`id`** ordering (V2) |
| `src/battlecode/years/bc19/rules.nim` | **new** | the driver loop of rules 1–2, `isOver`'s seven-rung ladder, the points formula, `playGame` |
| `src/battlecode/years/bc19/maps.nim` | **new** | the converted bc19 pool, the loader (including the saved MT state), `poolNames`, `drawMaps`, `sideAslotFor`, `mapCard` |
| `src/battlecode/years/bc19/knobs.nim` | **new** | the eleven-knob `Doctrine19` type, `KnownKeys19`, defaults, per-field repair, **absent-key defaulting**, `toJson19`, `bc19SheetSchema`, `plainWords19` |
| `src/battlecode/years/bc19/chassis/*.nim` | **new** | `saber.nim`, `examplefuncsplayer19.nim`, `scenario19.nim`, `kit.nim`, `econ.nim`, `castle.nim`, `church.nim`, `pilgrim.nim`, `military.nim`, `micro.nim`, `lattice.nim`, `comms.nim`, `trade.nim`, `infiltrate.nim` — **fourteen files**, and `NOTICE` + `docs/RULES-BC19.md` name the same paths |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc19", title: "Battlecode 2019 — Crusade", maxRounds: 1000, pools: @["small","mixed","large"], atlas: "atlas_bc19")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc19`; `Session` gains a `yBc19` branch (`w19`, `sides19`, `chassis19`); `yearIdOf`/`strongChassisFor`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson19`. Three name tables are added beside the other years' (below) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV12`, `ReplayCompatibleGameVersions` → `["GV04",…,"GV11", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scSaber` and `scExamplefuncsplayer19` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc19` arm in `defaultBaselineFor` and `baselineFor`; `blSaber` and `blExamplefuncsplayer19` added to `Baseline`; `baselineChassis` and `baselineReply` map them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc19`, `doctrine19` on `Sheet`, and one arm each in `knownKeysFor`, `defaultSheet`, `validate`, `toJson`, `plainWords` — **the envelope resolver is untouched** |
| `src/battlecode/match.nim` | **changed** | `winBonusFor` gains `yBc19` to the 200 set; the bc19 event names are added to `collectGameEvents` |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc19 adds the rock/ground terrain layer, karbonite and fuel depot pips (procedural — the upstream has no depot art), the six unit sprites at **two** team palettes, health bars, a carry badge on a loaded unit, and the preacher blast overlay |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc19 scorebug / feed / endcard shell records **and the bc19 arms of `beatsFor`** (§Viewer) |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port. bc19 uses it for **one** stream: `examplefuncsplayer19`'s patched per-robot generator (Tier A″). The engine's own generator is MT19937 and lives in `years/bc19/mt19937.nim` |
| `src/battlecode/results.nim` | **changed** | the bc19 optional keys added to the closed schema's key set |
| `src/battlecode/replay.nim` | **unchanged** | it re-validates the recorded **applied** sheet wrapped in `{"sheet": …}`, so nothing bc19 does can change how an older recording re-derives |
| `data/maps/bc19/*.json` | **new, committed** | 22 generated maps, each carrying the **MT19937 state after `makeMap()`** (V3, D1) |
| `data/bc19/tables.json` | **new, committed** | the whole finite arithmetic domain (below) |
| `data/atlas_bc19.png` / `.json` | **new, committed** | the 2019 sprite atlas (≈ 40 KB — twelve 16 px cells) |
| `tools/gen_maps_bc19.mjs` | **new, CI + build only** | runs the pinned engine under the pinned Node and writes `data/maps/bc19/<name>.json`. **The only tool in this repository that needs Node**, and it never runs inside a container image |
| `tools/map_pools_bc19.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc19.py` | **new** | cuts `atlas_bc19.*` from the six `app/public/assets/img/s_*.png` icons at two palettes |
| `tools/gen_year_constants.py` | **`--year bc19` added** | reads `coldbrew/specs.json` |
| `tools/JsBc19Tables.mjs` | **new, CI-only** | regenerates `data/bc19/tables.json` from the running Node's own `Math.ceil(Math.sqrt(x))` and `Math.floor` |
| `tools/oracle/bc19/bc19_trace.js` | **new, CI-only** | the trace driver (§Tests) — one file, `require`s the pinned `coldbrew/game.js` and `coldbrew/action_record.js` |
| `tools/oracle/bc19/{bc19idle,examplefuncsplayer19,bc19scenario,bc19scenariotrade,bc19scenariokill,bc19scenariotie,bc19slowbot}/robot.js` | **new, CI-only** | the seven oracle bots |
| `tools/oracle/bc19/examplefuncsplayer19/determinism.patch` | **new, CI-only** | the two committed hunks (§Decisions) |
| `tools/oracle/bc19/visible_order.patch` | **new, CI-only** | the **one** hunk that replaces `getGameStateDump`'s `Math.random()` shuffle with an ascending-`id` sort (V2) |
| `tools/oracle/bc19/engine.lock` | **new, CI-only** | the engine repository URL and commit sha, the pinned Node version, and the one npm dependency with its integrity hash |
| `tools/parity_trace_bc19.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc19.py` | **new** | the tier comparison and the ledger check — bc16's script, whose comparator bugs are already fixed there |
| `tools/ci/parity_ledger_bc19.json` | **new** | the accepted-divergence ledger, **empty** at the phase-30 exit |
| `tools/gen_bc19_fixture_replay.nim` + `tests/fixtures/replay-bc19.json` | **new, committed** | the fixture replay the wasm smoke and the beat test load |
| `tests/bc19_fixture.nim` | **new** | the shared fixture builder, beside `bc16_fixture.nim` … `bc25_fixture.nim` |
| `docs/RULES-BC19.md` | **new** | the year's rules, knobs and the full §Divergences list |

**A layout rule, written here because the bc24 run paid a fixer commit for its absence.** The file list above is the
intended layout and `NOTICE`, `knobs.nim`'s doc comments and `docs/RULES-BC19.md` all point at it. If the builder
merges two of these modules — for example folds `vision.nim` into `world.nim` — it must update **every one of those
three pointers in the same commit** and add a `docs/RULES-BC19.md` §Divergences item recording the merge. A licence
file that credits derived behaviour to a path that does not exist is a defect, not a cosmetic slip.

Three action/name tables are added to `years/dispatch.nim` beside the other years', because an event field with an
undocumented vocabulary is an event field nobody can draw (the bc23 r1-F14/F25 lessons):

```
Bc19ActionNames = ["nothing", "move", "attack", "build", "mine", "trade",
                   "give", "timeout"]   # ActionRecord.action ordinals 0..7;
                                        # 7 is unreachable upstream (V6)
Bc19UnitNames   = ["castle", "church", "pilgrim", "crusader", "prophet",
                   "preacher"]          # SPECS ordinals 0..5
Bc19RungNames   = ["-", "castles_destroyed", "coin_flip", "more_castles",
                   "more_unit_health"]  # for tiebreak.rung
```

`first_action`'s field is **`action`**, never `kind`: a field named `kind` is flattened into the same object as the
event's own `kind` key and silently overwrites it (the bc23 r1-F25 finding).

### Determinism

**bc19 has exactly ONE live generator and exactly ONE live draw site in the whole round loop.** That is the smallest
RNG surface of any year in this repo and it is why bit-exact parity is realistic here.

- **D1 — MT19937, seeded with the map seed.** `new MersenneTwister(this.seed)` at `game.js:53-54`, `init_genrand`
  semantics, `random() = genrand_int32() / 2³²`. Its call sites, exhaustively:
  1. **`makeMap()`** — hundreds of draws, **all at BUILD time** (V3). The board size (`:77`), the initial-alive
     density (`:88`), the whole cellular-automaton seeding in **column-major order** (`for w … for h …`, `:102`), the
     castle count (`:164`), every `roll_castle` y-rejection and its single x-draw (`:167-174`), every castle-placement
     re-roll (`:178-188`), the resource density (`:192`), every cluster-seed re-roll (`:197-207`), the per-cluster
     karbonite and fuel counts (`:229-230`), every depot pick and its rejection (`:254-275`), and the `transpose` coin
     (`:300`) — plus the whole sequence again on every recursive re-roll (`:359`). **The port reproduces none of it at
     run time**; `tools/gen_maps_bc19.mjs` runs it once under the pinned Node and the committed map file carries **the
     624-word state and `mti` immediately after `makeMap()` returns**, which is exactly the generator state
     `createItem` will draw from.
  2. **`createItem`'s id rejection loop** (`:433-434`) — **the ONE live draw site**. One draw per attempt, and an
     attempt is rejected only on a collision with an already-spent id, so the number of draws is a pure function of
     the state and the spent set. This is the whole reason the map file has to carry the post-`makeMap` state: get it
     wrong by one draw and every subsequent robot id differs, and ids are what `getItem` and the shadow are keyed by.
  3. **`isOver`'s coin flips** (`:568`, `:589`, `:602`) — `+(this.random() > 0.5)`, drawn **at most once per game**,
     and only on rungs 1, 4 and 7 of the ladder. Rung 1 is unreachable (V6), so in practice: once, on a double
     annihilation or an all-square round 1000. `tests/test_bc19_mt.nim` pins `initSeed(0)`, `initSeed(1)`,
     `initSeed(2147483647)` and `initSeed(80cf1cc5 mod 2³¹)` against the first 1 000 `randomInt()` outputs generated
     by the pinned npm package, and pins the save/restore of the state.
- **D2 — the turn queue is an ARRAY, and that is all it is.** `this.robots` (`game.js:33`) is a plain array; `robin`
  (`:41`) is an index; `createItem` **appends** (`:461`); `_deleteRobot` **splices and decrements `robin` when the
  removed index is below it** (`:939-942`). It is the **only** robot collection the engine iterates: `isOver`
  (`:551`), `getItem`'s linear scan (`:478`), `getGameStateDump` (`:672`). **There is no hash map, no set, no sort and
  no priority queue anywhere in the round loop**, so `years/bc19/world.nim` keeps one `seq[Robot]` with
  append-on-create and by-value removal, plus an `id → index` `Table` that is **never iterated** and is rebuilt on
  removal. A unit built in a round **does** take a turn in the same round (measured), and a unit killed after it has
  already acted correctly shifts `robin` back.
- **D3 — the `visible`-order shuffle is unseeded and is replaced (V2).** `game.js:717-722` calls the **global
  `Math.random()`**, not `this.random()`. Measured: five distinct orders in six identical runs of seed 1. The port
  orders `visible` by **ascending robot `id`** and the oracle is patched to the same order by
  `tools/oracle/bc19/visible_order.patch`, **on the engine side** — so the normalisation is symmetric and neither
  trace is massaged alone. `docs/PARITY.md` §bc19 states in as many words that this is the one place the oracle is not
  the published engine, and why.
- **D4 — `enactAttack`'s sweep order is load-bearing and is reproduced.** The engine walks the whole board **r (y)
  ascending outer, c (x) ascending inner** (`action_record.js:293-294`); the port walks only the squares with `rad <=
  DAMAGE_SPREAD` **in the same order**. It matters because multiple kills in one blast credit the reclaim in that
  order and the attacker's capacity clamps at 20 karbonite / 100 fuel, so the order decides what is collected and what
  is lost. Measured on the 9×9 probe: the (5,4) kill was processed before the (5,5) kill and the reclaim came out
  14/33.
- **D5 — the arithmetic is INTEGER everywhere, and that is this year's headline fidelity theme.** Health, karbonite,
  fuel, damage, capacities, radii, yields and costs are all integers (`coldbrew/specs.json`); JavaScript numbers are
  float64 but every value here is exactly representable and every operation is `+`, `-`, `*` or a comparison on small
  integers, so a Nim `int` port is bit-exact by construction. **Exactly two non-integer operations exist on gameplay
  paths and BOTH have finite domains and BOTH are tabled at build time:** (i)
  **`Math.ceil(Math.sqrt(signal_radius))`** (`game.js:834`, `action_record.js:329`), whose domain is the integers **0
  … 7938** — all 7 939 values in `data/bc19/tables.json`; (ii) **`Math.floor(a / b)`** in the reclaim
  (`action_record.js:305-306`), whose divisor `rad_to_attacker` ranges over the r² values reachable inside a
  PREACHER's blast plus its own square, i.e. **{0, 1, 2, 4, 5, 8, 9, 10, 13, 16}** — tabled for every `(numerator
  0…275, divisor)` pair, with the **`rad_to_attacker == 0` case pinned to the capacity clamp** (in JavaScript
  `floor(n/0) = Infinity` and `Math.min(x + Infinity, cap) = cap`; when the numerator is also 0 it is `NaN` and
  `Math.min(NaN, cap) = NaN`, but the robot is deleted on the next line so the value is never read — the port pins it
  to the capacity and `tests/test_bc19_combat.nim` names the case). **There is no `sqrt`, no `pow`, no `exp` and no
  float64 accumulation on any runtime path**, and `src/battlecode/fdlibm.nim` is not imported by bc19 at all.
- **D6 — three `null`/scalar coercions in `specs.json` are real rules and are ported as such.** JavaScript's coercion
  of `null` and `undefined` turns three missing table entries into behaviour:
  1. **`CHURCH.ATTACK_RADIUS` is the scalar `0`, not a pair.** `r > ATTACK_RADIUS[1]` is `r > undefined` = `false` and
     `r < ATTACK_RADIUS[0]` is `r < undefined` = `false`, so the range check **passes for every `dx`/`dy`**,
     `ATTACK_FUEL_COST` is 0 and `ATTACK_DAMAGE` is 0: **a CHURCH may "attack" any on-board square for free, dealing
     nothing and consuming its turn.** Measured (`record.action == 2`). Ported as a legal no-op action; the chassis
     never emits it.
  2. **`PILGRIM.ATTACK_RADIUS` is `null`.** `null[1]` throws a `TypeError`, which `enactTurn` swallows
     (`game.js:779`), so **a pilgrim attack is a validation failure**: the record keeps whatever the signal and
     castle-talk steps set and no action happens. Measured. Ported as a refused action.
  3. **`CASTLE`/`CHURCH` `KARBONITE_CAPACITY` and `FUEL_CAPACITY` are `null`.** `Math.min(n, null) === 0` for `n >=
     0`, so **a structure that lands a kill collects exactly nothing** and its own carried amounts are forced to 0.
     Ported; and it is inert, because a structure's carried amounts are never read (a `give` to a structure credits
     the *team* store, rule 6.6).

**Every round appends to a hash chain**; the viewer re-derives each round and compares, exposing `bc_mismatch_round`.
The values folded into the bc19 chain each round — **thirteen per team plus nine globals**, so a re-derivation that
diverged in only one of them cannot reproduce the chain (the GV02 lesson): per team — castles alive, churches alive,
live units of each of the four mobile types, total unit health, karbonite, fuel, units built, units lost, karbonite
mined, fuel mined; plus globally — the round number, `robin`, an FNV-1a 64 hash of the occupancy shadow (y ascending
outer, x ascending inner), an FNV-1a 64 hash of the queue's id list **in queue order**, the queue length, the number
of spent ids, both orders' `last_offer` packed into one integer, an FNV-1a 64 fold of the **MT19937 state's 624
words**, and `mti`. **Folding the generator state is a bc19-specific decision and it is the cheapest possible tripwire
for a missed or extra id draw (D1.2)** — which, given that the id stream is the only live randomness, is the single
most likely way this port can desynchronise.

Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record** (`plan.abandonAfter[g]`)
applied by the same proc on record and on playback — the particle-worlds scar — and the record→re-derive test covers
**every** bc19 end reason, not just `complete`.

**`GameVersion` bumps to `GV12`** in the same commit, with a prepend-only changelog line: *"the `bc19` year module:
Battlecode 2019 'Crusade' ported from battlecode19 at commit 80cf1cc5 (npm `bc19` 0.4.6; the spec exists only as
`coldbrew/specs.json` plus `app/src/views/docs.js`, and THE ENGINE IS THE TIEBREAKER — seven documented docs-vs-engine
disagreements, all resolved in the engine's favour): the driver loop that evaluates `isOver` BEFORE EVERY TURN (so a
castle annihilation stops the game mid-round and round 1000 gets exactly ONE turn), the turn queue as a plain
insertion-ordered ARRAY with by-value removal and `robin` shifted back on a death, units built in a round taking a
turn in the SAME round, the flat 25-fuel-per-team-per-round trickle as the only passive income, the six unit types
with their integer costs, ranges and the PREACHER's nine-square team-blind blast, the reclaim `floor((karbonite +
buildK/2) / r2_to_attacker)` with its capacity clamp, mining at 2 karbonite or 10 fuel with unrefined carry and
`give`-to-deposit, the CHURCH built only by a PILGRIM, the 16-bit radio with its `ceil(sqrt(r2))` fuel cost charged
once per turn, the free 8-bit castle-talk channel, the inter-team castle barter with its reset-then-throw quirk, and
the seven-rung `isOver` ladder with the `win_condition = 1` overwrite on a round-1000 coin flip, behind
`game_config.year`. MT19937 replaces `java.util.Random` for this year only and lives in `years/bc19/mt19937.nim`. The
wall-clock chess clock and the unseeded `visible`-order shuffle are documented divergences (V1, V2) and the map
generator is run at BUILD time (V3). bc16, bc20, bc21, bc22, bc23, bc24, bc25 AND bc26 SEMANTICS ARE UNCHANGED: no
GV04..GV11 recording carries a byte whose meaning changed — this run makes no year-neutral behaviour change at all —
which is why `ReplayCompatibleGameVersions` is EXTENDED rather than reset and every hosted replay keeps rendering."*
**`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06","GV07","GV08","GV09","GV10","GV11", GV12]`** —
extended, never reset. `tools/ci/check_gameversion.sh` claims the version across branches; **it compares the headline,
not the digits, so if a sibling branch lands GV12 first this branch rebases to GV13 and extends the list again** (the
bc20 precedent).

### The chassis, the DecisionOps clock, and the chess-clock divergence (V1)

The engine's per-robot resource is a **wall-clock chess clock**, not a bytecode counter: `robot.time` starts at
`CHESS_INITIAL = 100` ms, gains `CHESS_EXTRA = 20` ms at the start of every turn (`game.js:759`), loses the turn's
measured `wallClock()` elapsed (`:771`, `:805`), and a robot whose clock is negative is frozen and does nothing until
it accrues back above zero (`:806-808`, `docs.js:144`). `vm2` additionally kills any single turn at `TURN_MAX_TIME =
200` ms (`vm.js:6`).

**It is replaced by a `DecisionOps` clock in "ops", with the numbers taken from the engine's own constants at a fixed
20 ops per millisecond:**

| quantity | value | from |
|---|---|---|
| `OpsPerMs` | **20** | the one free parameter, chosen so the numbers below read straight off the engine's own milliseconds |
| `ChessInitialOps` | **2 000** | `CHESS_INITIAL 100 × 20`; every robot's clock at `createItem` |
| `ChessExtraOps` | **400** | `CHESS_EXTRA 20 × 20`; credited at the start of every turn (rule 2.3) |
| `TurnMaxOps` | **4 000** | `TURN_MAX_TIME 200 × 20`; the hard per-turn cap |
| **`TurnChargeOps`** | **400 — AN EXACT CONSTANT** | deliberately equal to `ChessExtraOps`, and **not derived from anything the chassis does** |

**The theorem, and it is why the numbers are these numbers:** because the per-turn charge is the exact constant
`TurnChargeOps = ChessExtraOps`, `robot.chessOps` is **invariant at 2 000 for every robot for its whole life**, and
therefore **no robot is ever frozen and the engine's `robot.time < 0` branch is unreachable in this port**. That is
the divergence, stated as an equation rather than a hope, and `tests/test_bc19_clock.nim` asserts the invariant after
every turn of a whole game.

**Why the charge may not be the chassis's real op count**, logged here so it is not re-litigated: the freeze rule is
an *engine rule*, so deriving its input from the chassis's own work would make **the chassis's implementation a rules
input** — a one-line refactor of `saber`'s Dijkstra would change what a round resolves to and would have to bump
`GameVersion`. That is unacceptable, and it is exactly the argument bc16's V1 makes about its delay decay.

**Separately, `TurnMaxOps = 4 000` is a real compute cap that the sim enforces**, and it has three properties, all
stated so nobody has to rediscover them:

- **It is checked *before* each primitive and never inside one.** A Dijkstra search, a vision sweep or a micro
  evaluation either runs to completion or does not start. So a primitive's *result* is never a function of the
  remaining budget, only *whether the chassis got to ask*. When the cap is reached the robot's turn ends where it
  stands — it is **not** resumed mid-computation next turn.
- **No rule reads it.** `decision_ops` is recorded for telemetry and for the `#bc19-*` readouts only.
- **It provably never bites in a healthy game.** `saber`'s heaviest turn is one Dijkstra over the bounded window (a
  21×21 box = **441** nodes at `VISION_RADIUS 100`), plus a scan over at most ~240 visible robots, plus a
  lattice/blast score over ≤ 441 squares — **≈ 1 100 ops worst case, under 30 % of the cap**.
  `results.games[].decision_ops_peak` records the measured maximum and `tests/test_bc19_clock.nim` **asserts it stays
  below `TurnMaxOps` in every gate game**, so the cap is not merely generous, it is demonstrably non-binding. If a
  future chassis exceeds it, the turn ends deterministically rather than hanging.

Why full metering is out of scope for v1: there is nothing to meter. bc19's engine has **no bytecode counter at all**
— that is a 2016/2020-era Battlecode mechanism, and 2019 replaced it with a wall clock precisely because each robot is
a separate JS process. There is no instruction-level quantity in the upstream to be faithful to.

`docs/PARITY.md` §bc19 and `docs/RULES-BC19.md` §Divergences both state, in as many words, that **the freeze branch of
`processAction` is the one behaviour this oracle cannot compare, and why** — and Tier B′ (§Tests) both proves it never
fired in any compared game **and** proves separately that the engine does fire it when it should.

### Maps — generated at build time, curated, and committed (V3)

**bc19 has no map files.** Every board is procedurally generated from the game seed inside the engine constructor
(`game.js:63,76-361`). Reproducing that at run time is not acceptable for two measured reasons:

1. **`regions.sort(x => -1*x.length)` (`:153`) passes a one-argument, sign-constant comparator**, so the result is
   implementation-defined. Measured under the pinned V8 over seeds 1…150 (184 half-map region computations, 42 of them
   with more than one region, max 4): the sort is a **plain reversal in 42 of 42 cases**, and the region kept passable
   — `regions[0]` — is **not the largest in 40 of them**. The code's evident intent (keep the biggest region) is not
   what it does, and a faithful port would be a port of one V8 sort.
2. **13 of the first 400 seeds produce unplayable boards.** Seeds **7, 20, 24, 83, 108, 127, 175, 211, 232, 267, 283,
   348, 365** yield **2–4 passable squares and ZERO castles**: the reversal keeps a tiny pocket, everything else is
   filled impassable, and the castle placement then exhausts its 1000-attempt counter (`:177-188`) and pushes nothing.
   `isOver` then takes rung 4 on the very first evaluation — **the game is decided by a coin flip at round 0**. A pool
   that can draw such a board is not a pool.

So: **`tools/gen_maps_bc19.mjs` runs the pinned engine under the pinned Node once, at build time**, and writes
`data/maps/bc19/<name>.json` carrying `name`, `seed`, `width`, `height`, `symmetry` (`"horizontal"` when the engine's
`transpose` was true, else `"vertical"`), the three `width × height` boolean arrays in `[y][x]` order, `castles` (`[x,
y, team]` rows **in `to_create` order**, which is the opening queue order), and **`mt_state`: the 624-word MT19937
state and `mti` immediately after `makeMap()` returned**, so the runtime draws castle ids from exactly the state the
engine would have. The generator **refuses** any board with fewer than 1 castle a side, with unequal castle counts,
with fewer than 30 % passable squares, with a passable region count above 1, or with either dimension outside 32…64 —
and CI asserts that **all 13 degenerate seeds above are refused, by seed, with the stated reason** (§Tests item 24).
The converted maps are **committed** and CI re-generates and byte-diffs them. The wasm bundle gets the directory
through the existing `--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Map names are `seed-NNNN`**, zero-padded to four digits, because the name *is* the reproduction recipe: `seed-0043`
is exactly what `new Game(43, …)` generates. No bc19 name can collide with another year's map file (`data/maps/bc19/`
is its own directory) and `tests/test_bc19_maps.nim` asserts it anyway.

**22 maps are committed. All 22 were generated and measured in this sandbox**; the table below is those measurements.
`pass` is passable squares and `pass %` their share; `karb`/`fuel` are the **total** depot counts on the whole board
(per side is half, except a depot on the axis row/column of an odd-sized board, which is a single square both sides
can mine — `seed-0017` has 9 karbonite depots for that reason); `cast` is castles **per side**; `sep` is the minimum
Euclidean distance between an opposing castle pair and `far` the maximum; `d→k`/`d→f` the distance from a RED castle
to the nearest karbonite / fuel depot.

| pool | map | size | pass | pass % | karb | fuel | cast | symmetry | sep | far | d→k | d→f |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `small` | `seed-0009` | 32×32 | 830 | 81.1 | 4 | 8 | **1** | horizontal | 25.0 | 25.0 | 1.4 | 1.0 |
| `small` | `seed-0021` | 33×33 | 827 | 75.9 | 4 | 6 | **1** | horizontal | 22.0 | 22.0 | 1.4 | 1.4 |
| `small` | `seed-0034` | 33×33 | 955 | 87.7 | 4 | 8 | **1** | **vertical** | 24.0 | 24.0 | 1.4 | 1.0 |
| `small` | `seed-0043` | 35×35 | 1 095 | **89.4** | 8 | 8 | **2** | horizontal | **14.0** | 37.7 | 1.0 | 1.0 |
| `small` | `seed-0048` | 32×32 | 786 | 76.8 | **4** | **4** | **2** | **vertical** | 21.0 | 27.7 | 1.0 | 1.4 |
| `small` | `seed-0107` | 37×37 | 965 | **70.5** | 10 | 8 | **3** | **vertical** | **14.0** | 38.3 | 1.0 | 1.0 |
| `mixed` | `seed-0005` | 39×39 | 1 333 | 87.6 | 12 | 16 | 2 | vertical | 18.0 | 31.1 | 1.4 | 1.4 |
| `mixed` | `seed-0017` | 41×41 | 1 501 | 89.3 | **9** | 10 | **1** | horizontal | 28.0 | 28.0 | 1.4 | 2.0 |
| `mixed` | `seed-0035` | 51×51 | 1 931 | 74.2 | 14 | 10 | 2 | horizontal | **34.0** | 61.4 | 1.0 | 1.4 |
| `mixed` | `seed-0039` | 50×50 | 2 302 | **92.1** | 14 | 14 | **3** | horizontal | 27.0 | 61.4 | 1.0 | 1.0 |
| `mixed` | `seed-0042` | 44×44 | 1 436 | 74.2 | **8** | **8** | **3** | horizontal | 21.0 | 49.6 | 1.0 | 1.0 |
| `mixed` | `seed-0058` | 44×44 | 1 346 | **69.5** | 14 | 18 | **1** | horizontal | 37.0 | 37.0 | 1.4 | 1.0 |
| `mixed` | `seed-0060` | 41×41 | 1 217 | 72.4 | 14 | 14 | **3** | vertical | **14.0** | 33.9 | 1.0 | 1.0 |
| `mixed` | `seed-0125` | 48×48 | 1 716 | 74.5 | **26** | 18 | 2 | vertical | 15.0 | 39.0 | 1.4 | 1.4 |
| `mixed` | `seed-0001` | 45×45 | 1 499 | 74.0 | 8 | 12 | **3** | horizontal | 22.0 | 42.6 | 1.0 | 1.0 |
| `mixed` | `seed-0003` | 50×50 | 2 280 | 91.2 | 16 | 12 | 2 | vertical | 27.0 | 40.4 | 1.0 | 1.0 |
| `large` | `seed-0013` | 61×61 | 2 943 | 79.1 | 16 | 26 | 2 | vertical | **48.0** | 56.4 | 1.0 | 1.0 |
| `large` | `seed-0030` | 62×62 | 3 324 | 86.5 | **38** | 34 | **3** | horizontal | 23.0 | 56.0 | 1.0 | 1.4 |
| `large` | `seed-0045` | **64×64** | 3 294 | 80.4 | 24 | 24 | **3** | vertical | 29.0 | 57.0 | 1.0 | 1.0 |
| `large` | `seed-0056` | **64×64** | **3 438** | 83.9 | 26 | 30 | **3** | horizontal | 27.0 | 57.0 | 1.0 | 1.4 |
| `large` | `seed-0077` | 62×62 | 3 254 | 84.7 | 22 | 32 | 2 | horizontal | **45.0** | **78.1** | 1.4 | 1.4 |
| `large` | `seed-0117` | 63×63 | 2 795 | **70.4** | 26 | 32 | **3** | vertical | 18.0 | 44.0 | 1.0 | 1.0 |

`mixed` (**10 maps**) is the `bc19` variant's played pool; `small` (**6**) is the pool the parity oracle and the
docker smoke run on; `large` (**6**) is reserved for a later variant and **supplies one of the nine parity pairs**.
The `mixed` pool spans the axes the doctrines argue about: **both symmetries** (six horizontal, four vertical);
**1 217 to 2 302 passable squares**; **castles per side 1, 2 and 3** (`seed-0017` and `seed-0058` are single-castle
elimination games; `seed-0039`, `seed-0042`, `seed-0060` and `seed-0001` give three spawn points and three things to
lose); **karbonite depots from 4 a side (`seed-0042`) to 13 (`seed-0125`)** — the axis `pilgrim_curve` and
`church_expansion` argue over; **minimum castle separation from 14 (`seed-0060`) to 37 (`seed-0058`)** — which is
exactly the axis `opening: preacher_rush` lives on, since a preacher moves at r² 4 and needs ~9 turns to cross 14 and
~24 to cross 37; and **passability from 69.5 % (`seed-0058`) to 92.1 % (`seed-0039`)**, which decides whether
`symmetry_wall: wall` closes a corridor or is a waste of 20 prophets. One map would rank the map, not the doctrine.

**The nine parity pairs** are the six `small` maps plus `seed-0017` and `seed-0125` from `mixed` and `seed-0045` from
`large`, chosen to cover every branch of every rule that has one:

| pair map | what it is the only cover for |
|---|---|
| `seed-0009` | the **smallest board with one castle a side** — the shortest possible game and the whole ladder on a 1-castle board |
| `seed-0021` | the poorest **1-castle** board (2 karbonite a side) — the fuel and karbonite floors, and `mine` at capacity |
| `seed-0034` | **vertical** symmetry with one castle a side — the mirror function's other axis |
| `seed-0043` | **separation 14 with two castles a side** and the most open small board — first blood inside 20 rounds, so combat, reclaim and the preacher blast all fire early. **This is the `docker-smoke` map** |
| `seed-0048` | **the poorest board in the pool: 2 karbonite and 2 fuel depots a side** — the only pair where an order can genuinely run out of both |
| `seed-0107` | **three castles a side at separation 14 on the most closed small board** — the multi-castle queue order, castle talk between three castles, and the corridor case for `symmetry_wall` |
| `seed-0017` (from `mixed`) | **one castle a side on an open 41×41** — `castles_destroyed` on the first castle death, and the longest 1-castle walk |
| `seed-0125` (from `mixed`) | **13 karbonite depots a side** — the church-expansion and depot-claim paths under load, and the largest unit census in the pair set |
| `seed-0045` (from `large`) | **64×64, the largest legal board, 3 castles a side** — the r² 7938 radio radius, the widest Dijkstra, and the id stream under the most builds |

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from the variant's
pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot takes engine-side RED in game 1;
sides alternate each game. Seed, map names and side assignment are recorded in results and in the replay. **The
`docker-smoke` seed is pinned so that the draw is exactly `seed-0043`**, and `tests/test_bc19_maps.nim` asserts that
draw so the smoke's map cannot drift.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `fdlibm`, `sheet_common`, `sheet`, `decide`,
`llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`, `seats`) never branches on the year except
through `years/dispatch.nim`, whose `Session` is a Nim object **variant** so the compiler refuses to build a
half-added year. Adding 2019 is exactly what bc16 and bc20–bc25 proved adding a year to be: a new `years/bc19/`
directory, a generated map set, a sprite atlas, **one registry line**, one arm per dispatch `case`, and one manifest
variant. **Nothing else on `main` changes**: the eight shipped years' modules, maps, atlases, tests and manifest
variants are untouched, and the shared files this branch edits are enumerated in §Packaging. The replay header records
`year` so a viewer can never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the year-dependent *payload*
differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol id would force every existing
bc16/bc20–bc26 consumer to re-register for no change in the contract. Both `game.protocols.player` and
`game.protocols.global` continue to point at `docs/PROTOCOL.md`, which gains a bc19 section.

### The player container (thin registrar) — unchanged

`/bin/battlecode-player` reads `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`), dials its seat with a
bounded retry (240 × 500 ms), sends **one** registration blob and then only receives until the socket closes, then
exits 0:

```json
{"type":"register","prompt":"<PLAYER_PROMPT or empty>",
 "scripted":"awu"|"scaffold"|null,
 "policy":"<PLAYER_POLICY_LABEL>"}
```

sent as a Sprite v1 chat blob (a **binary** frame — the server must not filter non-text frames) and re-sent a bounded
number of times until acknowledged. The seat token is a **credential** and a wrong one is refused
(`tools/ci/cert_probe.py` proves it against the real image). A seat that sets neither env var takes the active year's
default baseline (`saber` on bc19). A seat whose registration never arrives is logged loudly and reported to
`COGAME_PLAYER_FAILURE_URI`. The receive loop is wrapped in `try/except CatchableError` and exits 0 on a dead socket
(the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no per-round
observation of any kind. The example below is the real `seed-0043` card, measured.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV12","year":"bc19",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":774113,
 "games":[{"map":"seed-0043","map_seed":43,"width":35,"height":35,"you_are":"RED",
           "rounds":1000,"rounds_are_one_based":true,
           "symmetry":"horizontal",
           "symmetry_note":"mirrored across the VERTICAL midline (x -> width-1-x). Every robot is handed the whole terrain, karbonite and fuel map on its FIRST turn, so their castles are exactly the mirror of yours and you know where they are from round 1.",
           "passable_squares":1095,"total_squares":1225,"passable_pct":89.4,
           "your_castles":[{"x":4,"y":33},{"x":10,"y":1}],
           "enemy_castles":[{"x":30,"y":33},{"x":24,"y":1}],
           "castle_separation_min":14.0,"castle_separation_max":37.7,
           "karbonite_depots":{"total":8,"per_side":4,"nearest_to_you":{"x":4,"y":32,"steps":1},
             "note":"a PILGRIM standing on one mines +2 unrefined karbonite a turn (cap 20) for 1 fuel; mining at capacity still costs the fuel and yields nothing"},
           "fuel_depots":{"total":8,"per_side":4,"nearest_to_you":{"x":5,"y":33,"steps":1},
             "note":"a PILGRIM standing on one mines +10 unrefined fuel a turn (cap 100) for 1 fuel"},
           "deposit_note":"unrefined karbonite and fuel are UNSPENDABLE until a robot GIVEs them to an adjacent CASTLE or CHURCH, which credits that structure's team global store"}],
 "economy":{"start_per_team":{"karbonite":100,"fuel":500},
            "passive_income_per_team_per_round":{"fuel":25,"karbonite":0,"note":"the ONLY free income in the game, and FLAT -- it does NOT scale with castles or churches"},
            "mining":{"karbonite_per_turn":2,"fuel_per_turn":10,"fuel_cost_per_mine":1,"pilgrim_karbonite_capacity":20,"pilgrim_fuel_capacity":100},
            "reclaim":"when you kill a non-structure you gain floor((its carried karbonite + its build karbonite / 2) / r2_between_you_and_it) karbonite and floor(its carried fuel / r2) fuel, capped at your own capacity. Structures gain nothing.",
            "trade":"a CASTLE may propose a karbonite-for-fuel swap to the ENEMY's castles; when both sides' standing offers match element-wise the swap executes and both offers clear. Positive means the resource moves from RED to BLUE. |offer| < 1024."},
 "units":{"castle":{"build":"cannot be built","hp":200,"vision_r2":100,"damage":10,"attack_r2":[1,64],"attack_fuel":10,"speed_r2":0,
                    "does":"builds PILGRIM/CRUSADER/PROPHET/PREACHER in an adjacent square; reads the free 8-bit castle-talk channel of every friendly unit at ANY range; barters with the enemy's castles; cannot move. LOSE YOUR LAST CASTLE AND YOU LOSE ON THE SPOT"},
          "church":{"build":{"karbonite":50,"fuel":200},"built_by":"a PILGRIM only","hp":100,"vision_r2":100,"damage":0,"speed_r2":0,
                    "does":"a second spawn point AND a second deposit point; cannot move, cannot read castle talk, has no attack"},
          "pilgrim":{"build":{"karbonite":10,"fuel":50},"hp":10,"vision_r2":100,"speed_r2":4,"fuel_per_r2":1,"karbonite_capacity":20,"fuel_capacity":100,
                     "does":"the ONLY unit that can mine and the ONLY unit that can build a CHURCH; cannot attack at all"},
          "crusader":{"build":{"karbonite":15,"fuel":50},"hp":40,"vision_r2":49,"speed_r2":9,"fuel_per_r2":1,"damage":10,"attack_r2":[1,16],"attack_fuel":10,
                      "does":"the only FAST unit -- range-squared 9 a turn, twice as far as anything else"},
          "prophet":{"build":{"karbonite":25,"fuel":50},"hp":20,"vision_r2":64,"speed_r2":4,"fuel_per_r2":2,"damage":10,"attack_r2":[16,64],"attack_fuel":25,
                     "does":"the longest reach in the game, and BLIND INSIDE range-squared 16 -- it cannot hit anything closer than that"},
          "preacher":{"build":{"karbonite":30,"fuel":50},"hp":60,"vision_r2":16,"speed_r2":4,"fuel_per_r2":3,"damage":20,"attack_r2":[1,16],"attack_fuel":15,"damage_spread_r2":3,
                      "does":"20 damage to EVERY OCCUPIED SQUARE within range-squared 3 of the target -- nine squares -- WITH NO TEAM CHECK. Its minimum range is 1, so firing at an adjacent enemy damages ITSELF and every friendly beside it"}},
 "combat":{"no_vision_needed":"an attack needs no line of sight and no vision -- only the range check",
           "no_team_check":"an attack may legally land on your own units; the chassis never does it",
           "no_path_check":"a move goes to any square within its speed even if the route is blocked; one unit per square, and a move onto an occupied or impassable square is refused"},
 "comms":{"radio":{"bits":16,"max_r2":7938,"fuel_cost":"ceil(sqrt(r2)), charged ONCE per turn",
            "note":"every unit of BOTH teams inside the radius reads the value, the sender's id and position, but NOT its team. Audible from the end of your turn until the end of your next."},
          "castle_talk":{"bits":8,"fuel_cost":0,"range":"unlimited","note":"readable ONLY by CASTLES of your own team, one value per unit per turn"}},
 "win":{"instant":"destroy the enemy's LAST CASTLE -- the game stops immediately, before the next robot acts",
        "at_round_1000":["more castles alive","greater TOTAL HEALTH of all your live units (not just castles)","a coin flip"],
        "both_castleless":"a coin flip",
        "note":"round 1000 consists of exactly ONE robot turn: the game-over check runs before every turn, and the round counter reaches 1000 on the first turn of that round"},
 "rules_digest":"<~6 KB condensed spec: the six unit types with their exact costs, health, ranges (with the prophet's MINIMUM range and the preacher's blast), speeds and fuel costs; the driver loop and the fact that the game-over check runs before every turn; the turn queue and the fact that a unit built this round acts this round; the economy and the deposit rule; the reclaim formula; the radio and castle-talk rules; the barter; and the seven-rung end ladder>",
 "sheet_schema":{"…all eleven knobs, their values, ranges, defaults and notes…"},
 "scoring":{"weights":{"castles_share":64,"unit_health_share":24,"net_worth_share":12},"win_bonus_per_game":200,"games":3,
            "note":"shares are float32; points truncate to an integer; net worth is karbonite + fuel/5 + the build cost of every live unit; the league ranks by ELO on match wins and results.scores is dominated by the win bonus"},
 "budget":{"attempt1_ms":40000,"retry_ms":24000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with **both** orders' castle positions, the
symmetry axis, the passability profile, the depot counts and the walking distance to the nearest of each, the seed,
the full constant tables, the knob surface with defaults, the scoring weights and the deadlines. Both orders' castle
positions are given because they are **not secret**: every robot is handed the complete terrain, karbonite and fuel
maps on its first turn (`game.js:728-730`) and the board is a mirror, so the enemy castles are derivable in a few
operations on turn 1 — and `kit.nim`'s `mirrorOf` derives them exactly that way in-match. Because every map is
symmetric, the two seats' cards are mirror images and numerically identical in every aggregate; the only asymmetry is
`you_are` and which mirrored coordinate set is labelled "yours".

**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in either
direction, at any time); the opponent's real player name (only the alias); **every in-match state** (a cog receives
**no** per-round observation — one sealed doctrine, then the war); the other seat's fallback status; and
**`robot.time`** (V7 — it is wall-clock derived, so exposing it would make the prompt non-reproducible). Inside a
match the fog is the robots': vision r² ≤ 100 for a castle, a church and a pilgrim, ≤ 64 for a prophet, ≤ 49 for a
crusader and **≤ 16 for a preacher** — the unit with the biggest blast has the smallest eyes, which is why it needs an
escort. Nothing else occludes; terrain is fully known from turn 1 and **an attack needs no vision at all**. Two
exceptions widen the fog inward: a **radio** broadcast makes its sender's id, position, value and radius readable to
everything inside the radius **of both teams** (`game.js:675,696-699`), and a **castle** additionally learns the
`team`, `id`, `turn` and `castle_talk` of **every friendly unit on the board** regardless of distance
(`:677,682,708,710`), which is what the `castle_talk_use` knob spends.

### Reply schema and caps

```json
{"sheet":{"opening":"preacher_rush","pilgrim_curve":5,"church_expansion":"never",
          "fuel_reserve":120,"unit_mix":10,"preacher_share":70,
          "church_saber_round":0,"symmetry_wall":"off",
          "castle_talk_use":"full","defend_radius":36,
          "trade_policy":"offer_fuel"},
 "notes":"Three preachers at their north castle by round 90; it is 14 squares away and a preacher crosses that in nine turns. I sell fuel for karbonite because the trickle funds me and it does not.",
 "motto":"Nine squares at a time."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES** (`MaxReplyBytes`, `sim_types.nim:238`), cut on a **rune** boundary by `truncateBytes` | unparseable → retry once → fallback sheet |
| the envelope | unwrapped **at most once** (`sheet`, `doctrine`, or a single object-valued key), the resolved key recorded in `seats[].sheet_envelope` | no envelope found → the payload itself is the sheet |
| `sheet` | ≤ **32** keys (`MaxSheetKeys`), each value type- and range-checked | bad field → that field's default, recorded in `sheet_defaults_applied` |
| `pilgrim_curve` (0…24), `unit_mix` (0…100), `preacher_share` (0…100), `defend_radius` (1…400) | integers, **clamped** to their stated ranges | out of range → clamped to the nearer bound and recorded (an integer knob is clamped, never defaulted, so "as many as possible" still means something) |
| `fuel_reserve` | integer **0 … 2000** | out of range → clamped; a non-integer → the default 300, recorded |
| `church_saber_round` | integer **0 … 1000** | out of range → clamped; a non-integer → the default 0, recorded |
| every enum knob (`opening`, `church_expansion`, `symmetry_wall`, `castle_talk_use`, `trade_policy`) | exactly one of its listed strings, case-folded and trimmed, `-`/space → `_` (`normalizeKey`) | unknown value → that field's default, recorded |
| an **absent** known key | takes its default and **is recorded in `sheet_defaults_applied`** (bc19 only, the envelope pin item 2) | — |
| `notes` | **280 runes** (`MaxNoteRunes`) | truncated |
| `motto` | **48 runes** (`MaxMottoRunes`) | truncated |
| unknown sheet keys recorded | ≤ **16** keys (`MaxUnknownFields`), each ≤ **40 runes** (`MaxUnknownFieldRunes`) | truncated |
| provider error text stored in the replay | **200 runes** (`MaxFallbackDetailRunes`) | truncated |
| the recorded prompt | **4000 runes** (`MaxPromptRunes`) | truncated |
| `PLAYER_POLICY_LABEL` | **48 runes** (`MaxPolicyLabelRunes`) | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary** (`truncateRunes`/`truncateBytes`,
`sim_types.nim:334-358`; the reply's 16 KB cap is measured in bytes but is still cut on a rune boundary): byte-slicing
a multi-byte character renders fine in a browser and then fails a strict UTF-8 parser, which is exactly what makes a
replay unreadable to everything but one lenient viewer. **The total reply byte cap is 16 384 bytes.**

### Results document

The closed schema is **shared with the eight shipped years** and stays that way: `results.games[]`'s five required
keys are year-neutral (`map`, `side`, `rounds_played`, `winner`, `end_reason`), every year-specific statistic is an
optional property, and `end_reason`'s enum is the union of every year's values.

bc19's per-game keys, each a 2-array of integers in **seat** order unless marked scalar. The six that already exist
for another year — `units_built`, `units_alive`, `attacks`, `damage_dealt`, `kills`, `robots_lost` — are **reused
rather than duplicated**:

`castles_start`, `castles_end`, `castles_lost`, `churches_built`, `churches_end`, `churches_lost`,
`enemy_half_churches`, `unit_health_end`, `karbonite_end`, `fuel_end`, `net_worth_end`, `karbonite_mined`,
`fuel_mined`, `karbonite_spent`, `fuel_spent`, `fuel_trickled`, `karbonite_reclaimed`, `fuel_reclaimed`,
`karbonite_deposited`, `fuel_deposited`, `units_built`, `pilgrims_built`, `crusaders_built`, `prophets_built`,
`preachers_built`, `units_alive`, `units_lost`, `mine_actions`, `mine_actions_wasted`, `give_actions`, `attacks`,
`damage_dealt`, `damage_taken`, `friendly_fire_damage`, `self_damage`, `splash_kills`, `kills`, `robots_lost`,
`moves`, `move_fuel_spent`, `radio_messages`, `radio_fuel_spent`, `castle_talks`, `trades_proposed`,
`trades_executed`, `trade_karbonite_net`, `trade_fuel_net`, `lattice_units_placed`, `builds_refused`,
`refused_actions`, `decision_ops_peak`;

scalars `castles_per_side`, `board_width`, `passable_squares`, `karbonite_depots`, `fuel_depots`,
`symmetry_horizontal` (0/1), `castle_separation_min`, `castle_separation_max`, `ids_spent`, `win_condition`,
`tiebreak_round`, `queue_length_end`.

**No key is reported in tenths**: bc19 has no float state at all (D5), so every number above is an exact integer and
the viewer's `fmtStat` prints it as one.

Top level, unchanged and already declared at `6e89d0f`: `names`, `aliases`, `scores`, `wins`, `points`, `games`,
`seed`, `year`, `policy_kind`, `sheet_defaults_applied`, `sheet_envelope`, `fallbacks`, `decision_ms`, `sim_seconds`,
`reason`, `wall_clock_seconds`, `game_version`. **bc19 adds no top-level key.**

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV12","year":"bc19",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":774113,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"saber",
           "sheet":{…as applied…},"sheet_submitted":"{…as received, before unwrapping…}",
           "sheet_envelope":"doctrine",
           "sheet_defaults_applied":["trade_policy"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":9214,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"seed-0043","map_seed":43,"map_json_sha256":"…",
           "sides":["RED","BLUE"],"side_a_slot":0,"rounds":1000,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…all three drawn maps, even if the match clinched in two…],
         "side_a_slots":[…],"abandon_after":[…],"max_rounds":1000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI — `result`, SINGULAR, this repo's convention */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a sha256 of the
committed generated map the bundle also ships — **including its saved MT19937 state**, so the browser never has to run
the JavaScript generator), both doctrine sheets **and both submitted sheets with the envelope key that was
unwrapped**, the chassis each seat drove, and the event list are all in the file, and the wasm sim replays every round
from them. **No `.bc19` bytes, no per-round robot dump, no per-square dump** — unit positions, health, types, carried
karbonite and fuel, `turn` counters, signals, castle-talk values, the occupancy shadow, both stockpiles, `last_offer`,
the spent id set and the MT19937 state are pure functions of the sim, so the browser re-derives them and the endcard
reads the re-derived totals. No server is contacted except S3 for the `.replay` file. The per-round hash chain lets
the viewer prove its re-derivation matches the recording (`bc_mismatch_round`, surfaced as
`data-replay-mismatch-round` and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round` (**1-based**, as the engine's are). **Every
event kind is bounded per game** — a 1000-round match with 240 units on the board cannot be allowed to emit an event
per action — and every one has a beat kind with CSS (§Viewer). **No event has a field named `kind`**: `first_action`'s
field is `action` (the bc23 r1-F25 lesson).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `envelope`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `map_seed`, `width`, `symmetry`, `sides`, `castles`, `karbonite_depots`, `fuel_depots`, `separation_min` | 1/game | `game` | beat + feed |
| `first_action` | `game`, `round`, `alias`, **`action`** (from `Bc19ActionNames`) | 2/game | `build` | beat + feed |
| `unit_milestone` | `game`, `round`, `alias`, `unit` (from `Bc19UnitNames`), `total` — the **first** of each of the four buildable mobile types per side | ≤ 8/game | `build` | beat + feed |
| `church_built` | `game`, `round`, `alias`, `x`, `y`, `churches`, `enemy_half` (0\|1) | ≤ 16/game | `church` | beat + feed |
| `church_lost` | `game`, `round`, `alias`, `x`, `y`, `churches` | ≤ 16/game | `church` | beat + feed |
| `castle_lost` | `game`, `round`, `alias`, `x`, `y`, `castles_left`, `cause` (`castle`\|`crusader`\|`prophet`\|`preacher`) | ≤ 6/game | `castle` | beat + feed |
| `depot_claimed` | `game`, `round`, `alias`, `resource` (`karbonite`\|`fuel`), `x`, `y`, `worked` — the first six per side then every fourth | ≤ 20/game | `mine` | beat + feed |
| `famine` | `game`, `round`, `alias`, `resource` (`karbonite`\|`fuel`) — the first round the side's store hits 0 with a build or an attack pending, once per resource per side | ≤ 4/game | `famine` | beat + feed |
| `trade` | `game`, `round`, `karbonite`, `fuel`, `payable` (0\|1) — an offer that MATCHED, payable or not | ≤ 20/game | `trade` | beat + feed |
| `preacher_splash` | `game`, `round`, `alias`, `enemy_killed`, `friendly_killed`, `self_damage` — the first per side then every eighth | ≤ 20/game | `splash` | beat + feed |
| `rout` | `game`, `round`, `alias`, `lost` — a round in which one side lost ≥ 4 units | ≤ 20/game | `rout` | beat + feed |
| `duel` | `game`, `round`, `lost` (2-array) — a round in which **both** sides lost at least one unit | ≤ 20/game | `duel` | beat + feed |
| `tiebreak` | `game`, `round`, `rung` (from `Bc19RungNames`), `castles` (2), `health` (2), `worth` (2) | ≤ 1/game | `end` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `win_condition`, `points`, `castles` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

**Twelve beat kinds** (`doctrine`, `game`, `build`, `church`, `castle`, `mine`, `famine`, `trade`, `splash`, `rout`,
`duel`, `end`), and **all twelve are emitted by the committed fixture replay** so the beat test in §Viewer is a real
gate and not a CSS inventory. The whole event list for a three-game match is at most **a few hundred entries** (worst
case `3 × (1+2+8+16+16+6+20+4+20+20+20+20+1+1+1) = 468` plus 11 pre-match), and `tests/test_bc19_replay.nim` asserts
each per-kind bound so a pathological game cannot produce a 20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`, built by the
build hook **`tools/build_replay_viewer.sh`** (unchanged — same containment checks, same `docker build --target
replay-viewer-builder` + `docker create` + `docker cp` shape, same `sim_sources_stamp` guard so a stale committed
bundle fails CI). The bundle contains **the same sim module**, now including `years/bc19/`, compiled to wasm; the
browser re-derives every round from the replay's events, config and seed. No pod, no live viewer route, no `.bc19`
bytes, and **no Node and no JavaScript engine of bc19's own** — the year's JavaScript exists only in the
`parity-oracle-bc19` CI job and in `tools/gen_maps_bc19.mjs`, which runs at build time on a developer machine or in CI
and never inside an image.

### All four viewer files come from ONE starter: `Metta-AI/cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode` → here. **All four
bundle files come from that one starter — `Metta-AI/cogame-battlecode` — and never a mixture**, because splicing one
starter's shell onto another's emscripten link flags (`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized`
bootstrap) deadlocks the viewer silently with every file present and 200 (cogame-lantern, 2026-08-23).

| bundle file | source (**all four from `Metta-AI/cogame-battlecode`, and from nothing else**) | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc19/`, `data/bc19/tables.json` and `data/atlas_bc19.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are, including `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-O2`, `--mm:arc`, `--exceptions:goto` and `-d:useMalloc`. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. **No edit at all is needed for bc19**: the page already sets `document.documentElement.dataset.year` from the frame's `s.year` in the shared block, so a new year switches itself on. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc19 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and **no existing id is reused for a different purpose** (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and **byte-for-byte**: **`client/chrome_common.js` is copied byte-for-byte** into the bundle, and so is
**`client/broadcast_core.js`**; their sha256 is asserted against the `coworld-ctf` copies in `tests/test_viewer.nim`,
and that assertion stays green because **neither file is touched**. `wire_constants.js` is regenerated from the sim by
`tools/gen_wire_constants.nim`, as today.

**Load signalling** (unchanged from the starter, restated because it is a checklist item): `static_replay.js` sets
`document.documentElement.setAttribute('data-replay-loaded', 'true')` on the **first drawn frame** — the worker's
`loaded` message after the first board frame is composited, never on rAF timing at the call site (the chorus
2026-08-24 scar) — and the `coworld-replay` bridge posts `ready` from a callback fired **after** that attribute is
set. On any failure — fetch, JSON parse, an unknown `game_version`, a wasm abort, or a hash mismatch that prevents
rendering — it sets **`data-replay-error="<message>"`** on `<html>` and shows the failure card.

### The appended bc19 game block, and chrome provenance

**No starter element is removed from the page.** The bc26 block's ids (`#coopchip`, `#bars`, `#gamechips`, `#econ`,
`#doctrines`) and the bc16/bc20/bc21/bc22/bc23/bc24/bc25 blocks' (`#bc16-archons` … `#bc25-srp`, 48 ids in all) all
stay exactly where they are. **What bc19 removes is nothing from the page and everything from the screen**: like every
other year block it appends `html[data-year="bc19"] #coopchip, … #bc25-srp { display: none !important }` for those 48
ids and `html:not([data-year="bc19"]) #bc19-… { display: none !important }` for its own **six**, so on a bc19 replay
exactly the bc19 set plus the shared chrome is visible. **The precise list of starter elements bc19 hides** is the
union of the eight existing year blocks' own id sets, i.e. exactly the ids that already appear in the seven
`html:not([data-year="bcNN"])` rules plus bc26's five — and `tests/test_viewer.nim` derives that list from the page
source rather than from a hand-written copy, so a ninth year cannot leave an eighth year's box visible.

The bc19 ids are all new and all prefixed:

- `#bc19-castles` — **the headline readout, and the year's whole story**, in the top-centre pill slot bc16 and bc22
  use: a two-sided castle tally `ASH ♜♜ 2 — 3 ♜♜♜ BASIL` with a 200-HP pip per castle that drains as it is shot, a
  **church count** beside it (`+2 ⛪`), and it **flashes red when a castle dies**, the only event that can end the game
  before round 1000.
- `#bc19-fuel` — **the year's signature readout, and the one no other year has**: the fuel clock, in the top band
  beside the castle pill. Karbonite and fuel banked as two bars, the **fuel delta this round** (`+25 −38` — the flat
  trickle against what the order actually spent, so a spectator sees an order going broke twenty rounds early), the
  mining rate (`⛏ 7k 4f`), unrefined karbonite and fuel **in transit** on pilgrims, and the round counter (`ROUND 612
  / 1000`). On a `famine` event it takes over the strip for two seconds in plain words (`CLAN ASH IS OUT OF FUEL —
  nothing can move`), and on a `trade` event (`BARTER — Ash gives 40 karbonite for 200 fuel`). It **keeps both bars,
  the delta and the round counter at every width**, including 360 px.
- `#bc19-econ` — per order: karbonite and fuel banked, mined and spent; depots worked out of depots reachable;
  churches built / standing / lost **with those in the enemy's half called out**; karbonite and fuel reclaimed off
  kills; and the barter ledger (offers, swaps, net karbonite, net fuel).
- `#bc19-units` — per order: the six-type census with castles emphasised, **units carrying an unrefined load** shown
  separately, units built / lost, and **friendly-fire and self damage as their own number**, because with
  `preacher_share` high that is where the losses come from.
- `#bc19-doctrines` — both sheets in plain words, **dismissible**: a `#bc19-doctrines-close` button with
  `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first playback advance (or after six
  seconds), and a `#bc19-doctrines-toggle` chip in the scorebug that re-opens it. Its body is **capped and scrolls**
  (the bc23/bc25 clipping finding); it sits above the board area and **never** inside the transport band; and it
  carries the **submitted-vs-applied badge** the envelope pin requires.
- `#bc19-crusade` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: the shared `onText` block already sets
`document.documentElement.dataset.year` from the replay header and re-runs `relayout()` on a change; the stylesheet
extends the existing `html:not([data-year="bc16"]) #bc16-… { display: none !important }` pattern with the bc19 pair.
**Every bc19 rule — including every beat-marker colour — is scoped to `html[data-year="bc19"]`** (the bc21 r1-F4 fix,
kept), so none of them can restyle another year's marker of the same name. The frame hook is
`window.Bc19Block.active(s)` / `.onFrame(s)`, added beside the existing eight in the shared `onText`, and the `if
(!isBc16 && !isBc20 && !isBc21 && !isBc22 && !isBc23 && !isBc24 && !isBc25)` guard at
`client/replay_broadcast.html:7166` and `:7178` becomes a nine-way test with `!isBc19`.

### The beat contract — emission, label and style, all three tested

This is where the bc25 run failed review (r1-F26: eleven beat-kind CSS rules against two emitted kinds), so it is
specified as three obligations that **one** test asserts together against the **committed fixture replay**
(`tests/fixtures/replay-bc19.json`):

1. **Emission.** `beatsFor` in `src/battlecode/broadcast.nim:152` is the only place a beat kind is decided. bc19 adds
   `let isBc19 = doc.year == "bc19"` beside the four that are already there (`:160-163`) and an arm for each of its
   event kinds. **Five names collide with other years and each needs the year test**: `first_action`
   (bc16/bc22/bc23/bc25 map it to `build`; bc19 joins them), `rout` (same set), `duel` (bc16's, bc22's and bc23's —
   bc19's carries the same field name with a different meaning, units lost rather than launchers, so the **label**
   switch gains a year test), `unit_milestone` (bc16 emits it with a twelve-value unit vocabulary; bc19's is
   six-valued, so the label switch gains a year test), and `tiebreak` (bc16 emits it with `archon_health_tenths`; bc19
   carries `health` and `worth`). The bc19-only kinds (`church_built`, `church_lost`, `castle_lost`, `depot_claimed`,
   `famine`, `trade`, `preacher_splash`) need no discriminator, because no other year emits those event names — even
   though two of their beat kinds (`build`, `end`) are spelled the same as another year's, which is exactly why the
   CSS scoping is mandatory.
2. **Label.** Every emitted beat carries a spectator-readable label built in the same `case` — e.g. `"CASTLE DOWN —
   Clan Ash has 1 left, killed by a preacher, game 2, round 318"`, `"Clan Basil raises a church at 41,7 — inside Ash's
   half, game 1, round 402"`, `"BARTER — Ash gives 40 karbonite for 200 fuel, game 1, round 260"`, `"CLAN ASH IS OUT
   OF FUEL — nothing can move, game 3, round 715"`, `"Preacher blast at 22,19 — three of Basil's dead and one of
   Ash's, game 2, round 190"`, `"ROUND 1000 — castles level at 2, Clan Basil wins on unit health 640 to 410"` — and it
   becomes the `<button>`'s `aria-label` and `title`. Every label is ≤ 120 runes.
3. **Style.** `client/replay_broadcast.html` ships a `.beat-marker.<kind>` rule for **all twelve** kinds, every one
   scoped to `html[data-year="bc19"]`: `.doctrine`, `.game`, `.build`, `.church`, `.castle`, `.mine`, `.famine`,
   `.trade`, `.splash`, `.rout`, `.duel`, `.end`. Five of those names already exist for other years (`doctrine`,
   `game`, `build`, `rout`, `duel`, `end` — six, in fact), which is exactly why the scoping is mandatory; six are new
   (`church`, `castle`, `mine`, `famine`, `trade`, `splash`).

`tests/test_bc19_beats.nim` loads the committed fixture, calls `beatsFor`, and asserts: **at least 24 beats over at
least 10 distinct kinds**, every beat's label non-empty and ≤ 120 runes, every emitted kind present in the twelve-kind
vocabulary, and — reading the page source — a `html[data-year="bc19"] .beat-marker.<kind>` rule for **every kind the
fixture actually emitted** (not for every kind in a hand-written list). `tools/gen_bc19_fixture_replay.nim` is written
to produce all twelve kinds, and the test fails if the fixture stops doing so.

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The `--statrail` repair is already in the tree: `relayout()` measures the union of the *visible* year stat boxes into
`--statrail` (`client/replay_broadcast.html:7011-7031`), `#killfeed`'s `bottom` is `max(calc(76 * var(--u)),
calc(var(--band, 0px) + var(--statrail, 0px) + 8px))` (`:1270`), `tests/test_viewer.nim` asserts both statically, and
`viewer_smoke.mjs --killfeed-overlap` measures client rects at 360 / 720 / 1280 px at FIT and 2× zoom on every year's
replay. **What bc19 must do — and it is the whole of the work here:**

1. add **`bc19-econ` and `bc19-units`** to `relayout()`'s measured id list, beside the fifteen already there.
   (`#bc19-castles` and `#bc19-fuel` are **top**-band pills and are deliberately not in the rail set.)
2. run the existing `--killfeed-overlap` gate **on the bc19 replay too**, at all three widths and both zooms — nine
   replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and asserts the gate
   goes red, so a ninth year cannot quietly disarm it.

### Zoom: KEEP `#viewpanel`

**Decided: `#viewpanel` (the zoom bar + minimap) is KEPT, and bc19 is the strongest case for it in the repository.**
The reason is the board sizes and it is not close. bc19 boards are **square and 32×32 to 64×64**; the `mixed` pool
spans **39×39 to 51×51** and the reserved `large` pool reaches **64×64**. The native board render is 16 px per square,
so **512 px to 1024 px wide** — every single one of them **larger than the 360 px featured-match frame**, where a
51-wide board gives 7 px per square and a 64-wide board gives **5.6**. A fixed arena would drop the panel; this is not
one. So the inherited `#viewpanel` is kept and wired to the same `zoomAt/setZoom/panBy/panTo/resetView` core API the
worker already forwards, with `?viewpanel=0` still honoured for thumbnail capture. The default view is fit-to-board,
so a spectator who touches nothing sees the whole map, both orders' castles and every depot at once — which in this
year is the right default, because the story is *who is standing between whose pilgrims and whose depots*.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets **`--hudscale`**,
  **`--topband`**, **`--band`** and **`--statrail`** on **`:root`**, iterating to a fixed point so a map-aspect change
  cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band (scorebug) and the
  bottom band (transport). `#bc19-castles`, `#bc19-fuel`, `#bc19-econ`, `#bc19-units`, `#bc19-doctrines` and
  `#bc19-crusade` are all explicitly positioned above `var(--band)`; the fuel strip's delta row sits **immediately
  above** `var(--band)`, never inside it.
- **The endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek dismisses it**:
  `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`, built by a bc19-block
  function with its **own** name, **`buildBc19BeatButtons`** — never `markBeat` (the tandem 2026-08-23 hoisting
  collision) and never colliding with `buildBeatButtons` (bc26), `buildBc16BeatButtons`, `buildBc20BeatButtons`,
  `buildBc21BeatButtons`, `buildBc22BeatButtons`, `buildBc23BeatButtons`, `buildBc24BeatButtons` or
  `buildBc25BeatButtons`. The spoiler gate is honoured by `applyBc19BeatSpoilers`, the same shape as the other seven
  blocks. **Every beat kind the sim emits has a CSS rule** (the beat contract, item 3).
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`, `#btn-end`,
  `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`, `#scrub` +
  `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — the standard probe, and why bc19 does not need the heavy one

bc21 taught the repo that a compute-heavy year defeats a fixed-wait scrub probe, because the Worker re-simulates from
the start of the game on every seek. **bc19 is the least exposed year this repo has**: 1000 rounds (a third of bc16's,
half of bc26's) at an estimated 0.6–2.5 ms/round with 80–240 units on the board (§The game), so a 100 % seek
re-simulates 0.6–2.5 s of native work in a wasm Worker. So, decided here rather than discovered at phase 60: **the
phase-60 check-8 dispatch for bc19 uses the standard `settle=700 soak=10`**, and `ci.yml`'s `wasm-viewer` job runs
`viewer_smoke.mjs` with **`--timeout 90 --soak 10`** on the bc19 replay (joining bc26/bc20/bc21;
bc16/bc22/bc23/bc24/bc25 keep `--timeout 120 --soak 15`). The `docker-smoke` step prints `sim_seconds / rounds` and
`docs/RULES-BC19.md` records the measured value; **if the measured value exceeds 3 ms/round, bc19 moves to the heavy
set and this paragraph is the record of why** — phase 20 makes that call from the number, not from a guess.

**The scrub selector needs no change.** `tools/ci/viewer_smoke.mjs` in this repo already resolves `#scrub` before
`#seek` before `input[type="range"]`, **one selector at a time**, excluding `#zoom-slider`, and `ci.yml` asserts
`scrub_selector == "#scrub"` after every run. And **`canvas_text.total: 0` on this renderer is not a pass signal**
(LEARNINGS 2026-09-08): the text-bounds check covers nothing here, which is why `--strict-text-bounds` is dropped on
the replay runs and applied instead to `tools/ci/renderer_fixture.html`, where the text is real (§Tests).

### Art

`data/atlas_bc19.png` + `data/atlas_bc19.json` (≈ 40 KB, committed), cut by `tools/build_sprite_atlas_bc19.py` from
the **official 2019 web client's own unit icons** —
`app/public/assets/img/s_{castle,church,pilgrim,crusader,prophet,preacher}.png` at `battlecode/battlecode19@80cf1cc5`,
**six 40×40 PNGs**, downsampled to 16 px and emitted at **two team palettes** (twelve cells). The palette is the
engine's own visualiser's: **RED `#DD0048`, BLUE `blue`** (`coldbrew/vis.js:486`), on the same ground/rock tones it
uses (`#333` and `#eee`, `vis.js:343,399`), with the radio-line colour `#fd5f00` (`vis.js:442`). **The upstream
visualiser draws no depot art at all** — it renders robots as coloured circles and terrain as rectangles — so the
karbonite and fuel depot pips are **drawn procedurally by `render.nim`** and credited to nobody. `NOTICE` records the
source repository, its commit, its root GPL-3.0 `LICENSE`, the exact six files, **and the fact that
`app/public/assets/{css,js,fonts}` are third-party (Bootstrap, jQuery, Chartist, Pe-icon-7-stroke) and are not used**.

Board rendering (`render.nim`): the **terrain layer is drawn first** — ground in the visualiser's own `#333`, rock in
`#eee` — then **karbonite pips (cyan diamonds) and fuel pips (amber circles)**, hollow when unworked and filled while
a pilgrim stands on them, which is how a spectator sees an economy come online. Units are drawn by type at the two
palettes with a health bar, a **carry badge** on any unit holding unrefined karbonite or fuel (a loaded pilgrim is the
most valuable target on the board because of the reclaim rule), and a **range ring on the selected unit** that draws a
prophet's *annulus* — its r² 16 blind zone as a hole — because "the prophet cannot shoot the thing next to it" is the
most confusing rule in this year without a picture. A radio broadcast draws a one-second `#fd5f00` circle at its
radius (the visualiser's own "nexi" colour); a **preacher attack draws its nine-square blast for one second in the
attacker's own colour, including the squares that hit its own side** — the frame that makes `preacher_share` make
sense; and a castle death draws a two-second red wash.

### Readouts, 360 px and the endcard

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is **checked at that width**, not at
desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, word labels hidden under 640 px, `#viewpanel`
shrinking to its minimum before anything else, and the `#bc19-*` boxes dropping their word labels to glyphs under 640
px; **`#bc19-fuel` keeps both bars, the fuel delta and the round counter at every width**, because it is the readout
that makes the year make sense).

- `#scorebug`: both order plates — `CLAN ASH` over the real player name (`daveey`) and the motto — the live points
  number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 612 / 1000`, `game 2 of 3 — seed-0043`.
- `#bc19-castles`, `#bc19-fuel`, `#bc19-econ`, `#bc19-units` as above.
- `#board`: the terrain layer, the depot pips, every unit with type, team, health and carry state, the selected unit's
  range ring, radio circles and preacher blasts.
- `#bc19-doctrines`: each sheet in plain words ("mines first and fights later", "wants nine pilgrims per structure",
  "expands to a church once the depots run short", "keeps three hundred fuel in the bank", "spends nearly half its
  army karbonite on prophets", "one shot in five is a preacher", "never sends a church into their half", "screens the
  midline without closing it", "tells its castles the census", "answers anything within ten squares of a structure",
  "matches a barter only when the rate favours it"), plus the capped `notes`, the **submitted-vs-applied badge**, and
  a fallback badge when a seat's doctrine came from the fallback sheet. Dismissible, capped and scrolling.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and provably clear of
  the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words; the per-game score line; and
  `#bc19-crusade`, the **war panel**: per order, castles started / lost / left and how they died; churches built,
  standing, lost and how many were in the enemy's half; karbonite and fuel mined, deposited, spent and banked, with
  the trickle broken out from the mined fuel so a spectator can see who earned their army; units built by type and
  units lost; **damage dealt, damage taken, and friendly-fire and self damage as their own line**; kills and the
  resources reclaimed off them; the barter ledger; and the **tiebreak ledger** — all three round-1000 rungs with both
  sides' numbers and which one decided it. None of it is stored in the replay: the wasm sim re-derives every round.

**The endcard's five known template defects are fixed for bc19, not inherited broken** (bc23's and bc25's phase-60
verifications found them; bc22 fixed four for every year and bc16 kept them armed). Each is asserted by
`tests/test_viewer.nim` (§Tests item 25):

1. **This year's nouns, not bc26's.** bc19's row in the `data-year` noun table
   (`client/replay_broadcast.html:6871-6887`) is `bc19: { unit: 'castle', units: 'castles', res: 'karbonite', res2:
   'fuel' }`, and the phrase table adds `church`, `pilgrim`, `crusader`, `prophet`, `preacher`, `depot`, `barter`.
   **No "rat", "cheese", "king", "archon", "parts", "lead" or "gold" appears on a bc19 card.**
2. **No clipping or overflow at 1280×800.** The war panel's grid is `max-height: calc(100vh - var(--band) -
   var(--topband) - 24px)` with `overflow-y: auto` on the body only, and `viewer_smoke.mjs --killfeed-overlap` asserts
   `#endcard.scrollHeight <= #endcard.clientHeight` at **1280×800** after the 100 % seek. **bc19 is checked at
   1280×800 AND at 360 px wide.**
3. **No raw unrounded floats.** Every printed number goes through one `fmtStat(value, kind)` formatter — integers as
   integers, percentages as `NN %`, `points`/`scores` as **integers**, and distances as `x.x` — and a `/\d\.\d{3,}/`
   grep of the rendered text fails the test. bc19 makes this easy: **every bc19 statistic is already an integer**
   (D5); the only decimals on the card are the two castle-separation distances, which are printed as `x.x`.
4. **No empty mottos and no "a accelerating"-class grammar.** A blank `motto` renders **nothing**, and
   **`plainWords19()` has no article concatenation anywhere** — every knob value maps to a complete clause.
5. **No HUD bleed-through.** `#endcard` is opaque over the board and the `#bc19-*` boxes are `visibility: hidden`
   while it shows (the bc23 finding).

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`, `player` →
  `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar), `platform: linux/amd64`, `build: {context: ., network: host}`. One
  image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and `/bin/battlecode-player` from
  one image and copies `data/` (now carrying `maps/bc19/`, `bc19/tables.json` and `atlas_bc19.*`). **No Node, no npm,
  no JS runtime, no JDK, no JRE and no Java in any runtime stage** — the 2019 engine is JavaScript and it exists only
  in the `parity-oracle-bc19` CI job and in `tools/gen_maps_bc19.mjs`, which runs at build time and never inside an
  image. `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc19 game block along with the
  other eight.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc19` is 2019 'Crusade' — castles and churches build
    pilgrims that mine karbonite and fuel, crusaders, prophets and preachers; every action burns fuel and the only
    free income is twenty-five fuel a round; the board is a mirror so both sides know where the other's castles are
    from round one; a preacher's blast hits nine squares with no team check; the two orders may barter karbonite for
    fuel with each other; and a side wins by destroying every enemy castle, or by holding more of them at round one
    thousand."*
  - `tags` unchanged (already four: `battlecode`, `strategy`, `mixed-motive`, `wasm`).
  - `game.config_schema`: `year.enum` becomes `["bc26","bc20","bc21","bc24","bc25","bc23","bc22","bc16","bc19"]` —
    **appended, so no existing index moves**. **NO BOUND MOVES.** `maxRounds` is already `{minimum: 50, maximum:
    3000}` (bc16 widened it) and bc19 uses **1000**; `gamesPerMatch` keeps `maximum 3` (bc19 uses 3);
    `perGameBudgetSeconds` keeps `maximum 300` (bc19 uses **60**); `matchBudgetSeconds` keeps `maximum 600` (bc19 uses
    **200**); `attempt1Ms`/`retryMs` keep `1000…60000` (40 000 / 24 000 since 0.9.1); `doctrineBudgetMs` keeps `1000…120000`
    (75 000 since 0.9.1); `connectTimeoutMs` keeps `1000…120000` (25 000); `num_agents` keeps `{minimum: 2, maximum: 2}`. `pool.enum`
    unchanged. `tokens` stays **declared and required** (the runner injects it — the 2026-09-03 lesson); every array
    keeps `minItems`/`maxItems`; **no runner-managed `tokens` values inside any `game_config`**;
    `additionalProperties: false` stays. **Every edit this run makes to the manifest is additive.**
  - `game.results_schema`: bc19's optional properties added beside the other years' (§Server, Results document);
    `games.items.required` unchanged (the five year-neutral keys); **`end_reason`'s enum extended with exactly THREE
    values — `castles_destroyed`, `more_castles`, `more_unit_health`.** `coin_flip` (bc22's) and `abandoned` are
    **already there and are reused**; `opponent_failed_to_initialize` and `both_failed_to_initialize` are **not
    added** (unreachable, V6). Top-level `required` is unchanged — `sheet_envelope` is already in it.
  - `game.protocols` — **both** keys, unchanged: `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — **`readme`** = `{"type":"uri","value":".../blob/main/README.md"}`; **`pages`** gains one entry and
    keeps the ten it has: `rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc22.md`, `rules-bc23.md`,
    `rules-bc24.md`, `rules-bc25.md`, `rules-bc16.md`, **`rules-bc19.md`** (*Battlecode 2019 "Crusade": rules, knobs
    and divergences* → `docs/RULES-BC19.md`), `replay.md`, `parity.md` (→ `docs/PARITY.md`, which gains a bc19
    section). **Eleven pages**, every one a `{id, title, content: {type, value}}` object.
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc19 resolution ("…,
    saber on bc19" / "…, examplefuncsplayer19 on bc19").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The certifier's
  `players-run` step requires **every** declared `player[]` entry to occupy a slot in `certification.players`, and it
  also requires `len(certification.players) == certification.game_config.num_agents`. With **`num_agents = 2`** there
  are exactly **two** cert slots, they are filled by `awu` and `scaffold`, and therefore **`player[]` may contain
  exactly those two ids and nothing else**. Adding `battlecode-bc19-saber` or any other year-specific runnable to
  `player[]` would fail the release with `players_missing` (LEARNINGS 2026-09-04). It is also unnecessary:
  `PLAYER_SCRIPTED` resolves **per year** in `src/battlecode/baselines.nim`, so seating `awu` on a bc19 episode
  already plays `saber` and seating `scaffold` already plays `examplefuncsplayer19`. The scripted bc19 policies reach
  the league through `tools/ci/policies.json`, which is a *policy* list and has nothing to do with `player[]`.
  `tests/test_manifest.nim` asserts all three facts (`player[]` ids == `certification.players` ids;
  `len(certification.players) == certification.game_config.num_agents`; `num_agents` present in every variant's
  `game_config` and absent at every variant top level), so the contradiction cannot be re-introduced silently.

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
  | `bc19` | Battlecode 2019 — Crusade (2 seats) | `year: "bc19"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 1000`, **`num_agents: 2`**, `attempt1Ms: 40000`, `retryMs: 24000`, `doctrineBudgetMs: 75000`, `perGameBudgetSeconds: 60`, `matchBudgetSeconds: 200`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  **No shipped variant's `game_config` changes, and no variant's `players` array changes.**

  **Why these timing numbers.** `maxRounds: 1000` is the engine's own `SPECS.MAX_ROUNDS` and there is no reading under
  which a bc19 game runs longer: `isOver` fires at `round >= 1000` (`game.js:591`) and the port must reproduce that,
  so any other value would be a rules change rather than a config choice. `perGameBudgetSeconds: 60` and
  `matchBudgetSeconds: 200` are the **tightest** budgets of any year in the repo and they are deliberate: bc19 is the
  shortest year (1000 rounds against bc16's 3000 and bc26's 2000) with the lightest per-round cost (0.6–2.5 ms/round
  estimated against bc23's measured 1.45–2.95), so a game is 0.6–2.5 s and a match 2–8 s — a **~25× margin** on
  `matchBudgetSeconds`. Making them larger would only widen the worst case in the 720 s envelope for no gain; making
  them smaller would leave no room for a slow runner. The four millisecond values are the repo-wide doctrine-phase
  numbers, identical across all nine variants, because the doctrine phase is year-neutral. All nine values are inside
  their existing `config_schema` bounds, so **no bound has to move**.

  `bc19`'s variant description: *"Best of three on the mixed pool, one thousand rounds each. Castles are the only
  thing that matters: destroy all of theirs and you win on the spot. Castles and churches build pilgrims, crusaders,
  prophets and preachers; pilgrims mine karbonite and fuel and must carry each load back to a structure before it can
  be spent. Every action burns fuel, and the only free income is twenty-five fuel a round. The board is a mirror, and
  every robot is handed the whole map on its first turn, so neither side has to look for the other. A preacher puts
  twenty damage on nine squares at once and does not check whose units are standing there. Castles may barter
  karbonite for fuel with the enemy's castles. At round one thousand the side with more castles wins, then the side
  with more total unit health, then a coin flip."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level (`CoworldVariant` is
  `additionalProperties: false` and rejects a variant-level `num_agents` — cogame-goofspiel-oshi-zumo 0.1.0,
  2026-08-26).

  **The `<SEATS>` cross-check, named explicitly.** `.github/workflows/ci.yml` substitutes **`<SEATS>` = 2** into the
  `docker-smoke` job, and `tools/ci/docker_smoke.sh` takes the seat count **solely** from
  `certification.game_config.num_agents` (`:141-173`), hard-failing with `SEAT-COUNT FAIL:` if the workflow's value
  disagrees — and it also refuses a `SMOKE_CONFIG_OVERRIDE` that tries to change `num_agents` (`:199-201`). Since the
  cert fixture keeps `num_agents: 2` and the bc19 variant declares `num_agents: 2`, the two independent declarations
  agree. **There is exactly one seat number in this note and it is 2.**

  **Certification fixture — UNCHANGED, and stays on `bc26`.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps `"year": "bc26"`,
  **`"num_agents": 2`** and its existing fast settings (`pool: small`, `seed: 1`, `gamesPerMatch: 1`, `maxRounds:
  400`, `attempt1Ms: 4000`, `retryMs: 2000`, `doctrineBudgetMs: 9000`, `perGameBudgetSeconds: 40`,
  `matchBudgetSeconds: 45`, `connectTimeoutMs: 15000`). There is **no bc19 certification fixture in v1** (§Out of
  scope): certification is the platform's contract check, it already passes on bc26, and re-pointing it at a brand-new
  year module would put the release at the mercy of the newest code for no gain. bc19 is proven instead by its own
  `docker-smoke` episode (§Tests), which produces a real bc19 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** — **`0.8.2 → 0.9.0`**, bumped
  at **phase 40, not by the build** — because it adds a variant and adds optional results properties without changing
  any existing *rule* and without moving any schema bound. `GameVersion` goes **`GV11 → GV12`** and
  `ReplayCompatibleGameVersions` is **extended** to
  `["GV04","GV05","GV06","GV07","GV08","GV09","GV10","GV11","GV12"]`, so every hosted
  bc16/bc20/bc21/bc22/bc23/bc24/bc25/bc26 replay keeps rendering (the bc20 learning: extend, never reset, and claim
  the version across branches with `tools/ci/check_gameversion.sh`). **This run makes no year-neutral behaviour change
  at all** — the envelope resolver, the results shape and the replay shape are already what bc19 needs — so no
  recorded byte anywhere changes meaning. The release is dispatched through the existing `coworld-release.yml` with
  the same step order (build → certify → upload-policies → upload-coworld → secret put). **Certify runs against bc26,
  exactly as before**, and `release-result.json` must still show `canonical: true` and `certify.replay_liveness`
  containing `skipped (static replay bundle declared`.

- **Branch discipline.** All work lands on the branch **`bc19-year-module`**, PR-then-merge, and **`ci.yml`'s
  `on.push.branches` list (`.github/workflows/ci.yml:26-28`) gains `bc19-year-module`** beside `main`,
  `bc16-year-module`, `bc20-year-module`, `bc21-year-module`, `bc22-year-module`, `bc23-year-module`,
  `bc24-year-module` and `bc25-year-module`. The branch is rebased onto `origin/main` before every push. **The
  leagues, variants, modules, maps, atlases and versions of bc16 and bc20–bc26 are never touched.** If a sibling
  branch lands `GV12` first, this branch rebases to `GV13` and extends the compatibility list again — the bc20
  precedent, and `tools/ci/check_gameversion.sh` is the thing that catches it.

  bc19 touches exactly these shared files — `sim_types.nim`, `baselines.nim`, `sheet.nim`, `years/registry.nim`,
  `years/dispatch.nim`, `render.nim`, `broadcast.nim`, `results.nim`, `match.nim`, `client/replay_broadcast.html`,
  `coworld_manifest_template.json`, `tools/ci/policies.json`, `tools/gen_year_constants.py`,
  `.github/workflows/ci.yml`, `docs/PARITY.md`, `docs/PROTOCOL.md`, `docs/REPLAY.md`, `NOTICE`, `README.md`,
  `tests/test_manifest.nim`, `tests/test_viewer.nim`, `tests/test_determinism.nim`, `tests/test_constants.nim`,
  `tests/test_sheet.nim` — and **every edit to each of them is additive** (a new enum value, a new `case` arm, a new
  appended block, a new list entry). **There is no subtractive or bound-moving edit anywhere in this run**, which is a
  first for a year module in this repository and is worth the reviewer's attention only in that there is nothing to
  look for. **Everything else on `main` is untouched**: no bc16/bc20/bc21/bc22/bc23/bc24/bc25/bc26 module file, map,
  atlas, test or variant is edited.

- **`tools/ci/policies.json`** gains the bc19 set beside the eight year sets already there — the file is **repo-wide
  and carries 4 entries per year (36 after this run)**. A scripted champion is a failure state; filler versions must
  differ from champion versions. **Exactly these four bc19 entries, with these labels:**
  ```json
  [{"name":"battlecode-bc19-saber","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text, §Decisions>","PLAYER_POLICY_LABEL":"saber"}},
   {"name":"battlecode-bc19-preachers","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text, §Decisions>","PLAYER_POLICY_LABEL":"preachers"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-saber","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"saber","PLAYER_POLICY_LABEL":"saber"}},
   {"name":"battlecode-examplefuncsplayer19","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer19",
           "PLAYER_POLICY_LABEL":"examplefuncsplayer19"}}]
  ```
  | policy | kind | env | owner | league role |
  |---|---|---|---|---|
  | `battlecode-bc19-saber` | **LLM prompt** | `PLAYER_PROMPT` | **daveey** (the CI token's own player) | champion #1 — the economy / church-expansion doctrine |
  | `battlecode-bc19-preachers` | **LLM prompt** | `PLAYER_PROMPT` | **daveey-1** (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) | champion #2 — the preacher-rush / barter doctrine |
  | `battlecode-saber` | scripted | `PLAYER_SCRIPTED=saber` | — | filler (the strong chassis on default knobs) |
  | `battlecode-examplefuncsplayer19` | scripted | `PLAYER_SCRIPTED=examplefuncsplayer19` | — | filler (the weak floor) |

  `image` is the **player** service's image (the 2026-09-03 lesson: `cogame-battlecode` alone matches nothing `compose
  build` produces and fails at "Docker image is not available locally"). **Champion
  #2 carries the `"player"` field** and is uploaded while `daveey-1` is the active player. LLM
  credentials reach the **game** container through the manifest env; the player pods need no Bedrock sidecar in this
  lineage.

  **Release dispatch shape, decided: dispatch `coworld-release.yml` with a `policies` OVERRIDE limited to exactly the
  four bc19 entries above** (the bc20 pattern), so the release does not recut vN+1 of the 32 bc16/bc20–bc26 policies
  the eight existing leagues have seated (LEARNINGS 2026-09-08: dispatching the whole file recuts every sibling year's
  policies). **Phase 40 must assert the filter returns exactly 4 before dispatching.** If the override is ever dropped
  and the full file is used instead, phase 50 must take its labels from **that** release's `release-result.json` and
  never from remembered ones (the bc21 learning).

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

A **ninth league**, created beside the bc16/bc20–bc26 ones, touching none of them and not the game's default league:

| field | value |
|---|---|
| `league_key` | `bc19` |
| `league_name` | `Battlecode 2019 — Crusade` |
| `default_variant_id` | `bc19` |
| `short_name` | `bc19` → **`softmax.com/battlecode/bc19`** (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc19-saber` (owned by **daveey**), `battlecode-bc19-preachers` (owned by **daveey-1**) — deliberately the year's two poles: the economy the season converged on against the two mechanics it never systematically spent |
| fillers (scripted) | `battlecode-saber`, `battlecode-examplefuncsplayer19` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues` filtered on
`game.coworld_name` returns several rows; **select by `league_key`/name client-side, never positionally or by count**
(LEARNINGS 2026-09-08: the count is a prediction, not a fact). Fillers are set **before** the first `trigger-round`.
**The verify slug is `battlecode/bc19`, not `battlecode-2019`**: `softmax.com/battlecode-2019` does not exist, and the
phase-60 check-6 link and the phase-70 play link both take `softmax.com/battlecode/bc19`. The atlas slug is likewise
`battlecode/bc19`.

### Licensing — the exact `NOTICE` paragraphs phase 20 must add

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged by the repository
itself. Both 2019 upstreams are **GPL-3.0**, and **GPLv3 §13 / AGPLv3 §13 expressly permit the combination**, exactly
as `NOTICE:56-59` already records for the 2020 sources and `NOTICE:616-731` for the 2016 ones. `NOTICE` gains
**three** sections, appended after the existing bc16 ones:

**1. `## battlecode/battlecode19 engine and sprites — GPL-3.0`**

> Repository: <https://github.com/battlecode/battlecode19>, pinned at commit
> **`80cf1cc535ec5a30559274aa1b49807ad4859925`** (`HEAD` of `master`, 2019-08-09). **The repository
> root `LICENSE` is the GNU General Public License v3 (35 149 bytes) and it is the ONLY licence file
> anywhere in the tree** — there is no per-directory `LICENSE` and neither `app/package.json` nor
> `coldbrew/package.json` declares a `"license"` field — so every file used below is covered by that
> one licence. GPLv3 §13 and AGPLv3 §13 expressly permit the combination of GPL-3.0 and AGPL-3.0
> works, which is exactly what this repository is; the repository as a whole remains AGPL-3.0 and this
> file records the upstream's own terms.
>
> What derives from it, named individually:
>
> * `src/battlecode/years/bc19/{units,world,actions,resources,vision,rules,maps,knobs}.nim` — the
>   2019 rule set, **hand-written in Nim from reading the source** (a behaviour port, not a
>   translation of copied files) from `coldbrew/game.js`, `coldbrew/action_record.js`,
>   `coldbrew/runtime.js`, `coldbrew/vm.js` and `coldbrew/specs.json`, with
>   `app/src/views/docs.js` as the human-readable spec. **Where the docs and the engine disagree the
>   engine wins**; all seven disagreements are tabled in `docs/RULES-BC19.md`. Every deliberate
>   difference is in `docs/RULES-BC19.md` §Divergences;
> * `src/battlecode/years/bc19/mt19937.nim` — MT19937 as `mersenne-twister@1.1.0` implements it
>   (`init_genrand` seeding, `genrand_int32() / 2³²`), which `coldbrew/game.js:53-54` constructs from
>   the map seed. The underlying algorithm is Matsumoto and Nishimura's, distributed under the
>   three-clause BSD notice reproduced in `src/battlecode/years/bc19/mt19937.nim`'s header;
> * `src/battlecode/years/bc19/constants.nim` — **generated** by
>   `tools/gen_year_constants.py --year bc19` from `coldbrew/specs.json`, and re-generated and
>   byte-diffed in CI, so the constant table is provably the engine's and provably not hand-typed;
> * `data/maps/bc19/*.json` — 22 boards **generated at build time** by `tools/gen_maps_bc19.mjs`,
>   which runs the pinned engine's own `Game` constructor under the pinned Node and records the
>   resulting maps, castle roster and MT19937 state. bc19 ships no map files upstream: every board is
>   procedurally generated from the seed (`coldbrew/game.js:76-361`);
> * `data/bc19/tables.json` — the whole finite arithmetic domain
>   (`Math.ceil(Math.sqrt(r²))` for r² 0…7938 and the reclaim's integer divisions), regenerated by
>   `tools/JsBc19Tables.mjs` under the pinned Node and byte-diffed by the `parity-oracle-bc19` job;
> * `src/battlecode/years/bc19/chassis/examplefuncsplayer19.nim` —
>   `coldbrew/bots/example_js/robot.js`, ported statement for statement **with the two hunks of
>   `tools/oracle/bc19/examplefuncsplayer19/determinism.patch`** applied (a deterministic per-robot
>   RNG in place of `Math.random()`, and the removal of the `this.me.team == 1` guard that makes the
>   stock bot inert on RED). It is the parity oracle's other side, so it **may not gain behaviour**;
> * `data/atlas_bc19.png`, `data/atlas_bc19.json` — cut by `tools/build_sprite_atlas_bc19.py` from
>   **six files**, `app/public/assets/img/s_{castle,church,pilgrim,crusader,prophet,preacher}.png`
>   (40×40 each), at the two team palettes `coldbrew/vis.js:486` uses (RED `#DD0048`, BLUE `blue`),
>   with the terrain tones from `vis.js:343,399` and the radio-line colour from `vis.js:442`.
>   **`app/public/assets/{css,js,fonts}` are third-party (Bootstrap, jQuery, Chartist,
>   Pe-icon-7-stroke) and are NOT used, NOT cut and NOT shipped.** The upstream visualiser draws no
>   karbonite or fuel depot art at all, so those pips are `render.nim`'s own;
> * `tools/oracle/bc19/bc19_trace.js` and the seven oracle bots under `tools/oracle/bc19/` — written
>   against the engine's own `Game` and `ActionRecord` API, **compiled and run only in CI**.
>
> **The engine itself is used only at CI time and at map-generation time**, from a `git clone` of the
> pinned commit, with **one npm dependency** (`mersenne-twister@1.1.0`, integrity
> `sha1-+RZhjuQ9cXnvz2Qb7EUx65Zwl4o=`, pinned in `tools/oracle/bc19/engine.lock`). The engine's other
> 403 transitive packages — including `vm2`, `rollup`, `esm` and `update-notifier` — are **not
> installed**, because the trace driver drives `Game` directly and needs none of them.
> **No Node, no npm, no JavaScript runtime, no JDK and no upstream JavaScript source exists in any
> image this repository builds.**
>
> **Two hunks of the engine are patched, in CI only, and both are recorded in `docs/PARITY.md`
> §bc19**: `tools/oracle/bc19/visible_order.patch` replaces `getGameStateDump`'s Fisher–Yates shuffle
> (`coldbrew/game.js:717-722`), which draws from the **global, unseeded `Math.random()`** and is
> therefore not reproducible even against itself, with an ascending-`id` sort; and
> `tools/oracle/bc19/examplefuncsplayer19/determinism.patch` does the same job for the example bot.

**2. `## m-schier/battlecode-2019-wololo — the strategy the `saber` chassis distils, GPL-3.0`**

> Repository: <https://github.com/m-schier/battlecode-2019-wololo>, pinned at commit
> **`ebdd27959a83e00c4ec67c74253d2db8095e3ba6`**. **`COPYING` is the GNU General Public License v3**,
> and every source file carries its own GPL-3.0 header naming Paul Hindricks, Maximilian Schier and
> Niclas Wüstenbecker (Team Wololo, 9th place, Battlecode 2019). Placement in the 2019 finals is the
> reason it was chosen: it is the only bot of that standard with a licence.
>
> `src/battlecode/years/bc19/chassis/{saber,kit,econ,castle,church,pilgrim,military,micro,lattice,comms,trade,infiltrate}.nim`
> is a **behaviour port**, not a translation: no JavaScript is vendored. The correspondence:
>
> | here | from there |
> | --- | --- |
> | `kit.nim`'s mirror derivation | `robot.js:733-786` (`isXAxisMirrored`, `mirror`, `mirrorIfChurchExtendable`) |
> | `kit.nim`'s navigator and its two modes | `Lattice.js`, `PriorityQueue.js`, `robot.js:31-34` (`NAV.ECONOMIC` / `NAV.FASTEST`), `:1135-1236` |
> | `econ.nim`'s posture set | `robot.js:88-140` (`STRATEGY_OPTIONAL_TANK_RUSH`, `STRATEGY_BOOM_RED`, `STRATEGY_BOOM_BLUE`, `STRATEGY_BOOM_DEFENSIVE`) |
> | `castle.nim`'s state machine | `robot.js:53-58` (`CASTLE_STATE`) |
> | `pilgrim.nim`'s state machine | `robot.js:68-74` (`WORKER_STATE`) |
> | `military.nim`'s state machine and its charge | `robot.js:60-66` (`MILITARY_STATE`), `:84-86` (`CHARGE_DURATION`), `:1749-1770` |
> | `church.nim`'s siting score and its minimum distance | `robot.js:76-82` (`STRUCTURE_MINING_INFLUENCE`, `MINIMUM_CHURCH_DISTANCE`), `:1237-1398` |
> | `micro.nim`'s damage map and dodge/aggressive move | `robot.js:1459-1573` |
> | `comms.nim`'s two protocols | `robot.js:36-51` (`RADIO_PRIO`, `CASTLETALK_PRIO`), `:206-391` (the encoders) |
> | `lattice.nim`'s parity and interweave | `robot.js:97-131` (`LATTICE_DENSE`, `LATTICE_INTERWEAVE`) |
> | `kit.nim`'s strategic score grid | `Strategy.js` (the 8×8 civil/combat/danger grid and its decay) |
>
> The knob surface is **ours**, not theirs: wololo hard-codes its strategy constants and this coworld
> makes eleven of them a doctrine (§Decisions). `Random.js`'s `Math.random()`-based `choice` and
> `weightedChoice` are **not ported at all** — the chassis is deterministic.

**3. `## j-mao/battlecode-2019, awesomelemonade/Battlecode2019, virenvshah/Battlecode2019 — NOT READ`**

> All three repositories carry **no licence anywhere**, so this run treats them as unreadable. They
> are **not cloned, not read, not copied, not vendored, not compiled, not translated and not
> fetched**, and none contributes a single line to this repository. Where this repository's documents
> describe "the play the 2019 meta made", that is a statement about the run's source idea's
> characterisation of the 2019 season, not a claim about any repository's contents.

`docs/RULES-BC19.md` carries the full **§Divergences** list: (1) **the wall-clock chess clock replaced by a
`DecisionOps` clock whose charge equals its refill**, with the invariance theorem and the argument about why deriving
the charge from the chassis's work would make the chassis a rules input (V1); (2) **the unseeded `visible`-order
shuffle replaced by an ascending-`id` order**, with the measurement (five orders in six runs) and the engine-side
patch (V2); (3) **map generation moved to build time**, with the `regions.sort` measurement (42 of 42 reversals, 40 of
42 keeping a non-largest region) and the thirteen degenerate seeds (V3); (4) **the id-pool hang guard** (V4); (5)
**the `.bc19` byte replay, `vis.js`, `vm2`, the transpilers and the log channels not ported** (V5); (6) **win
conditions 3 and 4 and `enactTimeout` unreachable** (V6); (7) **`robot.time` absent from the observation and the
trace** (V7); (8) **`MAX_MEMORY` dead upstream** (V8); (9) **the seven docs-vs-engine disagreements**, each with its
`path:line` and the engine's answer; (10) **the three `null`/scalar coercions that are real rules** (D6), including
the legal 0-damage CHURCH attack and the PILGRIM attack that is a validation failure; (11) **the two committed hunks
of the example bot's patch**, including the removal of the `team == 1` guard and why an inert-on-RED baseline cannot
be scored; (12) **the `deadline` wall-clock stop**, a coworld concept and not an engine one, recorded as one
load-bearing record; (13) **both chassis are ours**: `saber` a behaviour port of a GPL-3.0 bot, `examplefuncsplayer19`
a statement-for-statement port that may not gain behaviour; (14) the chassis file layout, if the builder merges any
two modules; (15) **the score's `fuel div 5` exchange rate**, derived from `KARBONITE_YIELD` and `FUEL_YIELD`, and the
fact that the *winner* is decided on the engine's exact integer comparisons while *points* are decided on float32
shares, so the two can disagree on a razor-thin margin.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` = `cogame-battlecode`, **`<SEATS>` =
2**). The sandbox runs none of it; **CI is the only harness**. The `test` job's `timeout-minutes` goes **150 → 165**
(bc19's shards are the lightest in the repo — 1000 rounds against bc16's 3000 — but there are eighteen of them and
every file runs twice, debug and `-d:release`).

**Two conventions every bc19 test file obeys, because the repo has been bitten by both:** **never zero
`perGameBudgetSeconds`** in a helper (`match.nim:568` clamps it to `max(1, min(field, remaining))`, so a zeroed field
buys a **one-second** budget while `years/bc19/rules.nim` treats 0 as unbounded — the symptom is a shard that passes
in `-d:release` and fails in debug; use the `if perGame > 0:` convention from `tests/test_bc23_replay.nim:69`); and
**guard every `games[0]`** behind a non-empty check, with every end-reason assertion tolerant (`reason in [epDeadline,
epComplete]`, never strictly `epDeadline` on a runner-speed-dependent shard).

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc19_units.nim`** — the six-row table and every derived predicate against `data/bc19/tables.json`:
   build costs, HP, capacities, speeds, fuel-per-r², vision, damage and attack ranges; **the PROPHET's r² 16 MINIMUM**
   (15 refused, 16 and 64 accepted, 65 refused); the CRUSADER's r² 9 speed; **the CHURCH's scalar `ATTACK_RADIUS = 0`
   making a church attack LEGAL for 0 fuel and 0 damage** and the **PILGRIM's `null` making a pilgrim attack a refused
   action** (both D6, both measured on the real engine); **`Math.min(n, null) == 0`** so a structure kill reclaims
   nothing; and `signalCost(r²)` for r² ∈ {0,1,2,3,4,5,9,10,16,64,100,7938} = {0,1,2,2,2,3,3,4,4,8,10,90} — the twelve
   values measured in this sandbox.
2. **`tests/test_bc19_queue.nim`** — the turn queue, this year's whole tempo. `robin` starts at `high(int)` so the
   first `enactTurn` opens round **1**; the trickle lands **before** the round's first robot acts; **a unit built in a
   round takes a turn in the same round** (the measured 7-turns-in-round-1 case on `seed-0043`); a unit killed after
   it has acted shifts `robin` back and the next robot is not skipped; a unit killed **by its own splash** leaves
   `robin` pointing at the next robot; the initial castles are in **`to_create` order** (RED, BLUE, RED, BLUE, …); and
   **round 1000 consists of exactly ONE turn** with the game-over check firing immediately after it. 500 random
   build/kill sequences replayed against the oracle's own queue.
3. **`tests/test_bc19_actions.nim`** — the validation ladder of rule 4 **in the engine's own order**, the easiest
   thing in this year to get wrong: a `signal` validated **before** the action, so an illegal `move` **still
   broadcasts**; `temp_fuel` handed from the signal step to every later affordability test; a `castle_talk`-only turn
   legal and complete; the six-name whitelist; `trade` and `mine` **returning before the `dx`/`dy` gate**; `dx == dy
   == 0` refused; the build guards (adjacent, passable, empty, affordable, pilgrim→church only, non-pilgrim→never
   church, never a castle); `give`'s destination-passable test and its 0…255 bounds; `move`'s `r² <= SPEED` and its
   **absence of any path check**; and `attack`'s **absence of a vision test, a team check and a target-exists test**.
4. **`tests/test_bc19_combat.nim`** — the PREACHER, the most-cited case in the year. The blast is every occupied
   square with `rad <= 3` of the **target square** — nine squares — **with no team check and no attacker exclusion**;
   the named vector is the measured 9×9 probe: a preacher at (4,4) firing at (5,4) with enemy pilgrims at (5,4) and
   (5,5) and a friendly at (3,4) ends at **40 HP**, kills both enemies, leaves the friendly at r² 4 **untouched**,
   reclaims exactly **14 karbonite and 33 fuel** and costs **15 fuel**. The sweep order is **y ascending outer, x
   ascending inner** and the test asserts the reclaim credited in that order with the capacity clamp; `floor((k +
   buildK/2)/rad)` is checked for every `rad ∈ {1,2,4,5,8,9,10,13,16}`; **`rad_to_attacker == 0` is pinned to the
   capacity clamp**; and a CASTLE/CHURCH kill reclaims **nothing** (D6.3).
5. **`tests/test_bc19_economy.nim`** — `INITIAL_KARBONITE 100` / `INITIAL_FUEL 500` credited **once per team**; the
   flat **+25 fuel per team per round** at the start of every round, **not scaled by structures**; `mine` yielding
   **+2 karbonite** (cap 20) or **+10 fuel** (cap 100) for **1 fuel**, karbonite branch first, **and burning the fuel
   for nothing at capacity**; `mine` off a depot refused; `give` to a robot **reducing the amount before deducting
   it** so nothing is lost (docs disagreement 5); `give` to a structure crediting the **receiver's team global**,
   including the enemy's; and `worth` = `karbonite + fuel div 5 + Σ build K over live units` with a CASTLE
   contributing 0 and a CHURCH 50.
6. **`tests/test_bc19_trade.nim`** — the barter: the sign convention (**positive = RED → BLUE**); `|offer| < 1024`;
   CASTLE only; an unmatched offer leaving both standing; a matching pair **clearing both offers and then executing**;
   a matching pair that is **not payable** clearing both offers **and then throwing**, so the offers are gone and
   nothing moved (the reproduced quirk); and the initial `[[0,0],[0,0]]` making the first `(0,0)` proposal match and
   execute a zero trade.
7. **`tests/test_bc19_comms.nim`** — the radio: 16-bit values, `0 <= r² <= 7938`, cost `ceil(sqrt(r²))` charged **once
   per turn and before the action's own cost**; readable by **every unit of both teams** inside the radius along with
   the sender's `id`, `x` and `y` but **not its `team`**; **a robot that broadcasts nothing clearing last turn's
   broadcast**; and an unaffordable broadcast refused **without cancelling the action**. Castle talk: 8 bits, free,
   unlimited range, readable **only by a castle of the same team**, and a castle additionally seeing the `team`, `id`
   and `turn` of **every friendly unit on the board** regardless of distance.
8. **`tests/test_bc19_vision.nim`** — vision r² ≤ 100 (castle, church, pilgrim), ≤ 64 (prophet), ≤ 49 (crusader), **≤
   16 (preacher)**, inclusive at the boundary; the shadow `-1` outside vision, `0` empty, the `id` otherwise; the
   field-stripping ladder of rule 3.5-3.6 asserted field by field for the five cases (self / visible enemy /
   radioable-only / castle-and-own-team / neither); the three maps present **only** on `turn == 1`; `last_offer`
   **only** for a castle; and **`visible` returned in ascending `id`** (V2), asserted against the patched oracle's own
   order.
9. **`tests/test_bc19_endladder.nim`** — the seven rungs in the engine's order with a vector each; `castles_destroyed`
   firing **mid-round** with the remaining robots of that round **not acting**; `round >= 1000` firing after exactly
   one turn of round 1000; castles level and health differing → `more_unit_health`, health summed over **all** live
   units; **castles and health level → `coin_flip` with `win_condition` recorded as 1** (the `:604` overwrite,
   asserted as an explicit expectation); both sides castle-less → `coin_flip` with `win_condition 2`; and **win
   conditions 3 and 4 and `enactTimeout` provably never produced** (V6).
10. **`tests/test_bc19_scoring.nim`** — the points formula with its float32 shares and truncation, one vector per
    weight; the 0–0 `share` returning 0.5; points in `[0, 100]` and the seats summing to ≤ 100; the super-increasing
    property (`24 > 12`, `64 > 36`) asserted as arithmetic; **the documented case where `points` favours the loser**
    asserted as an explicit expectation; and `results.scores` **strictly** ordering the match winner above the loser
    on 500 random synthetic finals including clinched two-game matches, with `winBonusFor("bc19") == 200.0`.
11. **`tests/test_bc19_maps.nim`** — every committed map loads and its size, symmetry axis, passable count, depot
    counts, castle roster (in `to_create` order), separations and **saved MT19937 state** match §Sim module's measured
    table; every map is 32…64 square with **equal castle counts ≥ 1** and **exactly one passable region**; **no bc19
    map name resolves to another year's file**; and **the `docker-smoke` seed draws exactly `seed-0043`**, so the
    smoke's map cannot drift. (The *regeneration* byte-diff needs Node and therefore lives in `parity-oracle-bc19`.)
12. **`tests/test_bc19_mt.nim`** — MT19937: `initSeed` for four seeds against the first 1 000 `randomInt()` outputs of
    the pinned npm package; `random() == float64(randomInt()) / 2³²`; save/restore of the 624-word state and `mti`
    round-tripping exactly; **the id draw loop consuming exactly one draw per attempt and rejecting only on a
    collision**; and **the V4 guard** refusing a build at 4095 spent ids instead of looping (with a synthetic
    pre-filled id set, and the test **documents that the engine would hang here**).
13. **`tests/test_bc19_clock.nim`** — the `DecisionOps` clock (V1): `ChessInitialOps = 2000`, `ChessExtraOps = 400`,
    `TurnChargeOps = 400`, `TurnMaxOps = 4000`; **the invariant `chessOps == 2000` after every turn of a whole
    1000-round game**, i.e. no robot is ever frozen; the cap checked **before** each primitive and never inside one; a
    synthetic chassis asking for 5 000 ops having its turn end deterministically at the cap; and **`decision_ops_peak
    < TurnMaxOps`** in a real `saber` vs `saber` game, so the cap is demonstrably non-binding.
14. **`tests/test_bc19_sheet.nim`** — every one of the eleven knobs: **absent → default AND recorded in
    `defaults_applied`** (and the same test asserts a **bc23** empty sheet still records none, so the change is
    provably scoped); mistyped → default + recorded; unknown enum value → default + recorded; **the six integer knobs
    CLAMP rather than defaulting** (and a non-integer defaults); enum values case-folded, trimmed and `-`/space
    normalised; unknown keys recorded (≤ 16, ≤ 40 runes); **a submitted `chassis` recorded as an unknown field and
    never honoured**; rune-boundary truncation of `notes`/`motto` including astral-plane characters; the
    **16 384-byte** reply cap cut on a rune boundary; **`plainWords19()` returning a non-empty, article-free complete
    clause for every value of every knob**; and **the envelope resolver from the bc19 side**: `{"sheet":{…}}`,
    `{"doctrine":{…}}`, `{"protocol":"x","doctrine":{…}}`, `{"battlecode_2019_doctrine":{…}}`, a bare flat sheet, a
    payload with **both** a known knob key and a `doctrine` key (the flat one wins), and a two-object payload (no
    unwrap) — each with the expected `sheet_envelope` value, and nesting unwrapped **at most once**.
15. **`tests/test_sheet.nim` (extended)** — the same resolver from the **year-neutral** side: every existing
    bc16/bc20–bc26 vector still parses to the same `Sheet` it did before, so this run is provably additive for the
    eight shipped years.
16. **`tests/test_bc19_examplefuncsplayer19.nim`** — the weak floor reproduced statement for statement against a
    recorded oracle trace: the per-robot `step` counter starting at `-1`; the castle's `step % 10 == 0` build of a
    CRUSADER at `(1,1)` **on both teams** (patch hunk 2); the crusader's direction draw from the engine's own N, NE,
    E, SE, S, SW, W, NW list through the patched per-robot `java.util.Random(id)` (patch hunk 1); and the **pilgrim,
    prophet, preacher and church branches doing nothing at all**. **It may not gain behaviour: it is one side of the
    differential oracle.**
17. **`tests/test_bc19_baselines.nim`** — **bounded orders and legality**:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the **same** `sheet.validate` the LLM path
      uses;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the moment it is
      emitted**: the actor's own type permits it; a build target adjacent, passable, empty and affordable with the
      right `build_unit` for the builder; a move within `SPEED` onto a passable unoccupied on-board square, affordable
      at `r² × FUEL_PER_MOVE`; an attack inside `[ATTACK_RADIUS[0], ATTACK_RADIUS[1]]` and affordable; a `mine` only
      by a PILGRIM, only on a depot and **only under capacity**; a `give` only to an adjacent occupied square with
      amounts the giver holds and ≤ 255; a `trade` only by a CASTLE with `|offer| < 1024` **and only when the match
      would be payable**; a radio radius ≤ 7938 and affordable; **no CHURCH attack ever** (D6, legal upstream and
      never used), **no deliberate attack on a friendly square ever**, and **no `give` to an enemy structure ever**;
      and **no robot exceeding `TurnMaxOps`**;
    - (c) **`refused_actions == 0` for `saber`** on both seats across the gate games — the bounded-orders assertion
      proper. **`examplefuncsplayer19` is explicitly EXEMPT and its exemption is asserted as such**: it draws a
      uniform random direction and therefore *must* sometimes walk into rock or into another unit (observed in the
      real engine run: *"Cannot move onto impassable terrain"*), so `refused_actions == 0` on it would assert that the
      weak floor is not the weak floor. The test asserts `refused_actions[weak] > 0` instead, so a future "fix" to the
      oracle's other side fails loudly;
    - (d) `examplefuncsplayer19` **acts** — ≥ 1 crusader built, ≥ 1 move made — but is **not** required to survive, to
      mine, to build a church, to trade or to compete;
    - (e) `saber` beats `examplefuncsplayer19` on **3 seeds × 2 `small` maps, 6/6**.
18. **`tests/test_bc19_survival.nim`** — the **economic-survival gate** (the LEARNINGS 2026-09-03 pin), with an
    inverted control. **The key design point, stated because it is bc19-specific: in this year an order does not get
    eaten, it RUNS OUT.** There is no NPC threat and no escalating clock; the only passive income is 25 fuel a round,
    karbonite has **none**, and an order that does not mine cannot build, cannot attack and eventually cannot move.
    - `saber` vs `saber`, all-defaults sheet, **3 seeds × 2 `small` maps = 6 games**, each to round
      1000. In **≥ 5 of the 6** the game must **reach the round limit or end on the round-1000 ladder** (i.e. **not**
      `castles_destroyed`) — the ≥ 4-in-5 shape the pin asks for, rounded up so the committed ratio is at or above it
      — and in **all 6** each seat must have: **still held at least one castle at round 700**; built ≥ 12 units of
      which ≥ 4 PILGRIMs and ≥ 4 military; mined ≥ 150 karbonite **and** ≥ 300 fuel; **deposited ≥ 80 % of what it
      mined** (an order that mines and never walks the load home has not played the game); **never had both stores at
      0 for more than 20 consecutive rounds** (the fuel-solvency clause); dealt ≥ 200 damage; and finished with ≥ 6
      units alive. **Across the two seats** at least one church must have been built on at least one of the six games,
      and **friendly-fire damage must be under 15 % of damage dealt**.
    - The same gate then runs as a **subprocess** against a **known-broken chassis** compiled behind
      **`-d:bc19BrokenChassis`** — a `saber.nim` variant whose pilgrims **mine but never `give`** (so nothing is ever
      refined), whose castles **ignore `fuel_reserve` entirely** (so the order spends to 0 fuel and freezes), and
      which **never builds a second pilgrim** — and it **must come back red**. That control is chosen deliberately: it
      is exactly the failure a "did it build units?" check would pass, and it is the failure this year's economy makes
      possible. **A gate that cannot fail is not a gate.**
    - **The thresholds above are the design floor, not the committed numbers.** Phase 20 **measures** a healthy mirror
      and the broken control, sets the committed thresholds between them with margin (never below this note's floor),
      and records **both** measured ranges in the test's header comment, exactly as `tests/test_bc16_survival.nim`
      does. If a floor proves unsatisfiable on the measured healthy mirror, the resolution is the bc23 r1-F21/F22 one:
      **lower the committed number to roughly half the weak seat's measured value and record the measurement inline**
      — never drop the clause.
19. **`tests/test_bc19_knobs.nim`** — the knob-teeth gate, and the **direct enforcement of the anti-inert rule**.
    Paired seeded games (identical seed, map and opponent; the two orders identical except one knob at its low and
    high setting, 3 seeds each), each asserting a named, signed delta. Thresholds live in one table so tuning is a
    one-line change, and the header records every substituted statistic (the bc21 r1-F6 fix). **Plus one assertion
    over the whole sweep: in every one of the 78 games, BOTH seats built ≥ 8 units, mined ≥ 100 karbonite and still
    had a unit alive at round 500** — i.e. **no setting of any knob produces an inert order**.

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `pilgrim_eco` → `preacher_rush` | preachers built by round 200 up ≥ 5 **and** karbonite mined down ≥ 30 % **and** mean distance of own military from own castles up ≥ 50 % |
    | `opening` | `pilgrim_eco` → `turtle` | prophets built up ≥ 4 **and** `lattice_units_placed` up ≥ 6 **and** enemy units killed inside `defend_radius` up ≥ 30 % |
    | `pilgrim_curve` | 1 → 20 | pilgrims built up ≥ 6 **and** karbonite mined up ≥ 40 % **and** military built down ≥ 25 % |
    | `church_expansion` | `never` → `early` | churches built up ≥ 2 **and** karbonite mined up ≥ 20 % **and** churches lost up ≥ 0.5 (the exposure is the point), on `seed-0125` (13 karbonite depots a side) |
    | `fuel_reserve` | 0 → 1500 | rounds with fuel at 0 down ≥ 80 % **and** attacks down ≥ 20 % (the trade-off is the point) |
    | `unit_mix` | 0 → 100 | prophets built up ≥ 6 **and** crusaders built down ≥ 70 % **and** mean own-unit speed per turn down ≥ 25 % |
    | `preacher_share` | 0 → 80 | preachers built up ≥ 5 **and** `splash_kills` up ≥ 4 **and** `friendly_fire_damage` up ≥ 40 (the cost is the point) |
    | `church_saber_round` | 0 → 250 | `enemy_half_churches` up ≥ 1 **and** enemy karbonite mined down ≥ 15 % |
    | `symmetry_wall` | `off` → `wall` | `lattice_units_placed` up ≥ 8 **and** enemy units reaching within r² 100 of an own castle down ≥ 40 % **and** own pilgrim mean walk length up ≥ 10 % (the wall blocks you too) |
    | `castle_talk_use` | `position` → `full` | `castle_talks` up ≥ 200 **and** duplicate builds (two structures queuing the same unit in one round) down ≥ 50 %, on `seed-0107` (three castles a side) |
    | `defend_radius` | 1 → 400 | own pilgrims killed down ≥ 30 % **and** enemy structures damaged down ≥ 25 % |
    | `trade_policy` | `never` → `offer_fuel` | `trades_executed` up ≥ 1 **and** `trade_karbonite_net` up ≥ 20 **and** `trade_fuel_net` down ≥ 100 |

20. **`tests/test_bc19_perf.nim`** — a full 1000-round game on `seed-0045` (**64×64**, the largest played map) with
    both seats on the unit-maximising configuration named in §The game, in **≤ 40 s**; failing it means switching
    `gamesPerMatch` to 2 and then 1.
21. **`tests/test_bc19_arith.nim`** — the integer-fidelity shard: **every value in `data/bc19/tables.json`** asserted
    against the committed file — `ceil(sqrt(r²))` for all **7 939** values of r² and the reclaim's integer division
    over its whole reachable domain — plus the assertion that **no bc19 module imports `fdlibm` or calls `sqrt`, `pow`
    or `exp`** (a grep over `src/battlecode/years/bc19/**`), so the "no runtime transcendental" claim is enforced
    rather than asserted.
22. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain, twice in one process
    and across a save/load; **the MT19937 state folded into the chain**, asserted by a vector that consumes one extra
    id draw and shows the chain diverging on that round; and **record → re-derive for every bc19 end reason**
    (`castles_destroyed`, `more_castles`, `more_unit_health`, `coin_flip` on both its branches, and the
    `abandoned`/`deadline` stop applied by the same proc on both paths).
23. **`tests/test_bc19_replay.nim`** — a bc19 replay document round-trips; a **strict UTF-8 parse** of the written
    bytes; the viewer's re-derivation of a recorded bc19 match reproduces the recorded per-round hashes; unit
    positions, health, types, carried karbonite and fuel, `turn` counters, signals, castle-talk values, the occupancy
    shadow, both stockpiles, `last_offer`, the spent id set and the MT19937 state all re-derive identically from
    events + config + seed with **nothing stored**; `plan.maps` carries all three drawn maps even when the match
    clinched in two; `seats[].sheet_envelope` and `sheet_submitted` round-trip; and **every event kind respects its
    per-game bound** from the table in §Server. The end-reason assertion is **tolerant** and every `games[0]` read is
    guarded.
24. **`tests/test_bc19_beats.nim`** — the **beat contract** (§Viewer): from the committed
    `tests/fixtures/replay-bc19.json`, `beatsFor` must return **≥ 24 beats over ≥ 10 distinct kinds**, every one with
    a non-empty label of ≤ 120 runes, every kind inside the twelve-kind vocabulary, and a `html[data-year="bc19"]
    .beat-marker.<kind>` CSS rule present in `client/replay_broadcast.html` for **every kind the fixture actually
    emitted**. Emission, label and style, all three, from the committed artefact.
25. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now **nine years** wide: the results key set
    + the `reason` enum == the manifest `results_schema` == the key set `tools/ci/docker_smoke.sh` asserts;
    **`num_agents` present in all nine variants' `game_config` and in `certification.game_config`, and absent at every
    variant top level**; `config_schema.year.enum ==
    ["bc26","bc20","bc21","bc24","bc25","bc23","bc22","bc16","bc19"]`; **every `config_schema` bound UNCHANGED from
    `main` and every one of the nine variants' values inside it** (the one assertion that proves this run moved no
    bound); **`player[]` contains exactly the ids in `certification.players`** and `len(certification.players) ==
    certification.game_config.num_agents`; `end_reason`'s enum containing `castles_destroyed`, `more_castles`,
    `more_unit_health`, `coin_flip` and `abandoned` and **not** `opponent_failed_to_initialize` or
    `both_failed_to_initialize`; every `config_schema` array bounded; `tokens` declared and required but never valued
    in a `game_config`; **both `game.protocols` keys** and `game.docs.readme` plus **all eleven** `pages` being
    `{type, value}` objects; and the installed `coworld` CLI's own `validate_upload_manifest` /
    `_load_template_manifest` accepting the template.
26. **`tests/test_constants.nim` (extended)** — the per-year **generated-files-match-the-pinned-sources** check: the
    `test` job gains a *"Fetch the pinned Battlecode 2019 sources"* step (a `curl` of the GitHub tarball at `80cf1cc5`
    — no `git`, no `npm`) and a *"The bc19 generated files match the pinned 2019 sources"* step running
    `tools/gen_year_constants.py --year bc19 --engine "$BC19_DIR" --check`, which regenerates
    `src/battlecode/years/bc19/constants.nim` from `coldbrew/specs.json` and **byte-diffs** it. The shard reads
    `getEnv("BC19_DIR")` and skips with a loud message when the checkout is absent, exactly as the bc22/bc23/bc25 arms
    do. **The map and table regeneration byte-diffs need Node and therefore run in `parity-oracle-bc19`, not here** —
    said explicitly so nobody looks in the wrong job.
27. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module loads under node
    and answers `bc_load_replay`/`bc_frame` on the committed **bc19** fixture replay; the bc19 game block shadows no
    `ChromeCommon` alias and no other year's game-block name (the tandem scar); **`chrome_common.js` and
    `broadcast_core.js` still match the coworld-ctf copies by sha256**; `#bc19-doctrines` carries a dismiss control,
    is capped-and-scrolling and sits outside `var(--band)`; **every `#bc19-*` rule is scoped to
    `html[data-year="bc19"]`**; `relayout()`'s `--statrail` measurement set names `bc19-econ` and `bc19-units`; the
    list of hidden starter ids is **derived from the page source** and covers all eight other years' boxes; and the
    **endcard fixes 1–5** from §Viewer (bc19's noun row present and no other year's resource noun inside it; the
    `scrollHeight <= clientHeight` rule at 1280×800; every printed number through `fmtStat` with a `/\d\.\d{3,}/` grep
    failing the test; a blank motto rendering nothing; no article-plus-enum concatenation; and the `visibility:
    hidden` rule for the `#bc19-*` boxes while the endcard shows).

### `parity-oracle-bc19` job — the 2019 JavaScript engine as a CI-only oracle

**The recipe below is built on facts measured in this sandbox, not guessed.** The tier structure is modelled on
`parity-oracle-bc16` (`.github/workflows/ci.yml:2636`) — same nimby/Nim install, same `nim.cfg` regeneration, same
streaming comparator, same ledger discipline — with the JVM steps replaced by Node ones. **`timeout-minutes: 45`**
(bc19's games are a third of bc16's length and the engine measured 1.5–3.3 s per 1000-round game in Node, so eighteen
pairs is minutes, not an hour).

1. **`actions/setup-node@v4` with an EXACT `node-version`**, recorded in `tools/oracle/bc19/engine.lock` alongside the
   engine commit sha and the one npm dependency, and the next step **hard-fails unless `node --version` equals the
   lock exactly**. **This is not a preference.** `coldbrew/game.js:153` passes `regions.sort` a one-argument,
   sign-constant comparator, so the map generator's output is **V8-implementation-defined**; measured under the
   sandbox's **v22.22.0** the sort is a plain reversal in 42 of 42 multi-region cases and keeps a non-largest region
   in 40 of them, and a V8 whose insertion sort behaves differently would generate **different boards from the same
   seeds**. Phase 20 writes the lock from the version `setup-node` actually installs, regenerates the 22 maps with it,
   and commits both. **If a future Node bump makes the regeneration byte-diff fail, the committed maps are the rules
   and the old Node is the pin**; regenerating instead is a *rules change* and bumps `GameVersion`. That sentence is
   in `docs/PARITY.md` §bc19 and in the lock's own `note` field.
2. **Clone the pinned engine and install exactly one package.** `git clone` + `checkout 80cf1cc5…`, then `npm install
   --no-save mersenne-twister@1.1.0` with the integrity hash asserted against the lock. **No `npm install` of
   `coldbrew/package.json`**: the driver needs `game.js`, `action_record.js`, `specs.json` and `mersenne-twister` and
   nothing else — proved in this sandbox, where whole 1000-round games ran on exactly that set. That drops **403
   transitive packages including `vm2`** (deprecated, with known sandbox-escape CVEs), `rollup`, `esm` and
   `update-notifier`, which makes a **network call** on every `cli/run.js` invocation (`cli/run.js:13-16`) — another
   reason not to use the CLI.
3. **Apply the two committed patches and assert they applied.** `git apply --check` then `apply` for
   `tools/oracle/bc19/visible_order.patch` (V2) and `tools/oracle/bc19/examplefuncsplayer19/determinism.patch`
   (§Decisions), each asserted to change exactly the expected number of hunks. **These are the only two places the
   oracle is not the published engine**, and `docs/PARITY.md` §bc19 names both with their reasons.
4. **The driver must fail loudly when nothing happens, and it must exit non-zero.** `tools/oracle/bc19/bc19_trace.js`
   **exits 3** if no robot ever took an action or no unit was ever built, which is what catches a silently broken bot
   load; `ci.yml` additionally asserts per pair that the game reached at least round **900** (or ended earlier with a
   `W` line), that at least **8 robots** were alive at once, and that at least one `A` line carries a non-`NOTHING`
   action. Every `node` invocation is wrapped in `timeout 600`.
5. **The driver reimplements `runtime.js`'s twenty-line loop and nothing else.** It `require`s the patched
   `coldbrew/game.js` and `coldbrew/action_record.js` **unmodified beyond step 3**, constructs `new Game(seed,
   chessInitial, chessExtra, false, false, false)`, drains `init_queue` by handing each robot a fresh instance of the
   bot module (one closure per robot, which is what `vm2` gave each bot and what makes a per-robot `step` counter
   per-robot), then loops `emptyQueue(); if (game.isOver()) break; game.enactTurn();` exactly as `runtime.js:58-76`
   does. **`docs/PARITY.md` §bc19 records that the loop is the one thing the oracle does not take from upstream, with
   the argument**: `runtime.js` drives it through `setInterval`, which cannot be run synchronously to completion, and
   `cli/run.js` additionally requires the rollup compiler, `vm2` and a network update check.
6. **The map is generated, not loaded** — `new Game(seed, …)` runs the real generator, and the driver **asserts the
   generated board is byte-identical to `data/maps/bc19/seed-NNNN.json`** before the first turn, and that the
   post-`makeMap` MT19937 state matches the committed `mt_state`, which is what proves the id stream is aligned (D1).
   That is the map regeneration byte-diff (item 26) and it lives here because it needs Node.

**The trace.** One line per record; `tools/parity_trace_bc19.nim` prints the same lines from the Nim port. **Every
value is an integer, so there is no float formatting to disagree about** — the single biggest thing bc19 has going for
it over its siblings.

```
R <round> Q robin=<n> live=<n> ids=<n>
R <round> T <RED|BLUE> karb=<n> fuel=<n> ca=<n> ch=<n> pi=<n> cr=<n> pr=<n> pe=<n> hp=<n> offer=<k>:<f>
R <round> U <id> team=<RED|BLUE> ty=<CASTLE|CHURCH|PILGRIM|CRUSADER|PROPHET|PREACHER> x=<n> y=<n> hp=<n> k=<n> f=<n> t=<n> sig=<n> sr=<n> ct=<n>
R <round> A <id> act=<NOTHING|MOVE|ATTACK|BUILD|MINE|TRADE|GIVE> dx=<n> dy=<n> u=<n> gk=<n> gf=<n> tk=<n> tf=<n>
R <round> G shadowchk=<fnv1a64> queuechk=<fnv1a64> mt=<fnv1a64> mti=<n>
R <round> W winner=<RED|BLUE|-> wc=<0|1|2|3|4|->
```

Robots are printed **in queue order**, not id order, which is what makes an ordering bug visible; the **`G` line's
`mt` and `mti` fields are bc19's own addition and they are the most valuable fields in the trace** — a single missed
or extra id draw (D1.2) surfaces on the round it happens instead of as a mystery 300 rounds later.
`tools/ci/parity_tiers_bc19.py`'s `normalize()` **is applied to BOTH sides by the same code path** and does exactly
two things: it re-parses every named checksum field (`shadowchk`, `queuechk`, `mt`) as an unsigned 64-bit integer and
re-emits it canonically, and it strips the `t=` field from **both** traces only for the Tier-B′ headroom assertion
(LEARNINGS 2026-09-08: bc23's comparator stripped a field from the Java side only and every pair "diverged" at round
1). **Nothing is normalised on one side only, and there is no float allowlist because there are no floats.** The
comparator uses **`itertools.zip_longest`, never `zip`** (a one-line-longer oracle trace must not read bit-exact) and
carries a self-test that constructs exactly that pair and asserts a divergence is reported. Traces go to
`$RUNNER_TEMP`, are compared **streaming** (never loaded whole), and only the first 200 divergent lines plus a gzipped
digest are uploaded.

**The tiers — pinned to what this harness can actually deliver, and honest about which one carries the weight.**

- **Tier A (BLOCKING) — rounds 1…1000 bit-exact, whole games, on the nine pairs**, with `bc19idle` against itself (a
  bot whose `turn()` returns `null`). **This tier is deliberately small, and that is the single most important
  difference between bc19 parity and bc16 parity.** In bc16 the zombies are engine-side, so an idle player still
  exercises half the game; **in bc19 nothing at all happens without a player action** — no NPCs, no terrain change, no
  passive spawning. So Tier A proves exactly the queue and `robin`, the round counter, the flat fuel trickle, the
  initial castles' id draws off the committed MT state, the `isOver` evaluation points, and the round-1000 ladder with
  all three rungs (which **do** fire: both sides keep every castle and end level on castles and on health, so
  `coin_flip` with `win_condition 1` is exercised on every pair). Worth having and cheap, but **the load-bearing tiers
  are A′ and A″.** The job asserts off the **oracle** trace that Tier A really did those things: `fuel` rises by
  exactly 25 a round for both teams; `ids` equals `2 × castles_per_side` and never grows; the final `W` line carries
  `wc=1`; and round 1000 has exactly one `A` line.
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact.** Four scenario bots of our own, each
  deterministic with **no RNG at all** and cheap enough that Tier B′'s clock assertion holds, and each **scripted by
  round number to force every rare path early**. **`bc19scenario`**: build one of each of PILGRIM, CRUSADER, PROPHET,
  PREACHER and a CHURCH from a pilgrim; move at every legal `r²` for every mobile type, proving the per-r² fuel
  charge; mine karbonite to capacity **and one turn past it**; `give` to a robot under capacity, to a robot **over**
  capacity (proving nothing is lost), to an own church and **to an enemy church**; attack with a CASTLE at r² 64 and
  1, a CRUSADER at 16 and 1, a **PROPHET at 16 and 64 and refused at 15**, and a PREACHER at 1 and 16; fire a PREACHER
  so its blast kills two enemies, damages a friendly and damages **itself**, proving the reclaim divisor at 1, 2 and
  4; issue a **CHURCH attack** (the legal 0-damage quirk, D6.1) and a **PILGRIM attack** (the refused quirk, D6.2);
  broadcast at r² 0, 1, 2, 3, 5, 10 and **7938**, proving the seven fuel costs; send castle talk from a mobile unit
  and read it at a castle; build onto an occupied square and move onto rock (both refused); and issue a signal in the
  same turn as an illegal move, proving the signal still lands. **`bc19scenariotrade`**: an unmatched offer, a matched
  payable offer, a matched **unpayable** offer (both offers clear, nothing moves), and the initial `(0,0)` zero trade.
  **`bc19scenariokill`**: crusaders onto the enemy's single castle on `seed-0017` until `castles_destroyed` fires,
  proving the game **stops before the next robot acts**. **`bc19scenariotie`**: mirrored sides so the round-1000
  ladder walks `more_castles`, `more_unit_health` and — on one seed — the **coin flip with `win_condition 1`**.
  `scenario19.nim` is their Nim twin, written line for line, behind `-d:bc19Scenario` (+`-d:bc19ScenarioTrade` /
  `-d:bc19ScenarioKill` / `-d:bc19ScenarioTie`). Both sides run all four on the nine pairs and must agree **bit for
  bit for the whole game**. The job then asserts, **off the ORACLE trace**, that the paths really fired: a `U` line
  for each of the six types; a `ty=` transition to `CHURCH`; a pilgrim's `k=`/`f=` rising by exactly 2 and 10 and then
  **not rising** at capacity; a team `karb`/`fuel` jump matching a `GIVE`; a `TRADE` line followed by both teams'
  stores moving in opposite directions; an `A act=ATTACK` line followed by three `U` lines disappearing in one round;
  a `wc=0` on the kill scenario; and `wc=0`, `wc=1` and the coin-flip `wc=1` across the tie set. *(If any scripted
  path turns out impossible to force deterministically, the failing item is dropped from the bot and **added to
  `docs/PARITY.md` §What is NOT compared with the reason** — never silently left in a bot that does not reach it.)*
- **Tier A″ (BLOCKING) — `examplefuncsplayer19` against itself, whole games, bit-exact, on the nine pairs.** It is the
  one bot with a live per-robot `java.util.Random(id)` (patch hunk 1), so this tier proves the port's
  `src/battlecode/rng.nim` reproduces a **second, independent** generator call-for-call alongside the MT19937 the
  engine itself runs — and it is the tier that runs the real filler, so a filler that stops being reproducible fails a
  blocking gate rather than a league round.
- **Tier B (BLOCKING) — the constants, the arithmetic and the map data, over their whole finite domains.**
  `tools/JsBc19Tables.mjs`, under the pinned Node, regenerates `data/bc19/tables.json`: every `coldbrew/specs.json`
  scalar and the whole six-row `UNITS` table with all thirteen fields (read **from the engine's own `specs.json`**);
  `Math.ceil(Math.sqrt(r²))` for **all 7 939** values of r² ∈ 0…7938; and the reclaim's `floor((k + K/2)/rad)` and
  `floor(f/rad)` over `k ∈ 0…20`, `f ∈ 0…100`, `K ∈ {10,15,25,30,50}` and `rad ∈ {0,1,2,4,5,8,9,10,13,16}` — **and the
  job byte-diffs it against the committed file**. It **also** regenerates **all 22 committed maps** from their seeds
  and byte-diffs those against `data/maps/bc19/*.json`, including the saved MT19937 state, **and asserts that all 13
  degenerate seeds (7, 20, 24, 83, 108, 127, 175, 211, 232, 267, 283, 348, 365) are refused by name with the stated
  reason** — which proves V3's curation rather than trusting it. bc19 has **exactly two non-integer operations** and
  both domains are finite, so this tier is not a sample: it is the entire domain.
- **Tier B′ (BLOCKING) — the chess-clock divergence, proved where it is observable.** Two steps: (a) **the driver
  asserts, after every turn of every compared game, that every live robot's `robot.time >= CHESS_INITIAL`** and exits
  **6** otherwise — so the engine's own freeze branch (`game.js:806-808`) provably never fired in any game this job
  compares, and V1's divergence is provably not exercised; and (b) a **separate, non-compared** run on one seed with
  **`bc19slowbot`**, whose `turn()` busy-loops for a calibrated ~40 ms, asserts that the engine **does** freeze it —
  `robot.time` goes negative and its `A` line becomes `NOTHING` — at the turn the formula `time_{n+1} = time_n + 20 −
  elapsed` predicts, within ±2 turns for runner jitter. Step (b) compares nothing against the Nim side (the port has
  no wall clock) and exists so the port's *reading* of the rule is proved rather than asserted. `docs/PARITY.md` §bc19
  states in as many words that **the freeze branch is the one behaviour this oracle cannot compare, and why**.
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 1000-round game, on all six
  comparing bots and all nine maps.** The job computes it per pair and compares it against
  `tools/ci/parity_ledger_bc19.json`, whose entries are `{"bot": …, "map": …, "first_divergent_round": N, "cause":
  "<one sentence>", "docs": "PARITY.md#<anchor>"}`. It **fails** if (a) a pair diverges with no ledger entry, (b) a
  pair diverges **earlier** than its entry, (c) a ledger entry no longer reproduces (a stale excuse is as bad as a
  missing one), or (d) any divergence occurs while Tier B′'s clock assertion still holds — which, on every bot in this
  job, means **always**, and therefore means a real rules bug rather than a timing artefact.

**Root-cause-or-fail is the standing rule, and it is the operator's ruling on the bc26 run (Fleet card
1218171523823317), not this note's preference.** An unexplained Tier C divergence is a **FAIL**, not a ledger line; a
cause of "unknown" is not a cause and the ledger schema rejects it. **The phase-30 exit condition is that Tiers A, A′,
A″, B and B′ pass with an EMPTY ledger**, and this note believes that is achievable because the three things that
historically forced divergences are all absent: **the arithmetic is entirely integer** (no float narrowing anywhere),
**there is no hash-ordered or sorted collection in the round loop** (D2), and **the RNG surface is one generator with
one live draw site** (D1). **The one place a divergence is genuinely plausible is the id draw stream** — a build the
port refuses and the engine accepts, or vice versa, shifts every subsequent id — which is exactly why the `G` line
carries the MT state and `mti` **every round** rather than only on interesting rounds.

If phase 30 finds a divergence anyway, the **root-cause checklist**, each item with its own unit test above, so a Tier
C failure bisects in minutes rather than becoming a card: the id draw loop and the committed MT state (tests 12, 11);
the queue's append/splice/`robin--` discipline and the same-round turn for a new unit (test 2); the validation
ladder's order and the `temp_fuel` handoff (test 3); the blast neighbourhood, its sweep order and the reclaim clamp
(test 4); the trickle, the mine branches and the `give` reduction (test 5); the barter's clear-then-throw (test 6);
the signal's once-per-turn charge and its clear-on-silence (test 7); the vision boundaries and the field-stripping
ladder (test 8); the seven ladder rungs and the `win_condition = 1` overwrite (test 9); and the three `null`/scalar
coercions (test 1).

Tiers A, A′, A″, B, B′ and C are the **phase-30 gate**. Every accepted divergence is listed in `docs/RULES-BC19.md`
§Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md` gains a `bc19` section in the same shape
as the `bc16` one — including, honestly: the exact Node version and why it is pinned, the one npm dependency and the
403 that are not installed, the two engine patches with their reasons, the fact that the driver reimplements
`runtime.js`'s loop, the trace line counts and Node seconds phase 20 measures, the peak and mean robot counts, **the
explicit statement that Tier A is small in this year because nothing happens without a player**, and **the explicit
statement that the freeze branch of `processAction` is the one behaviour this oracle cannot compare, and why (V1)**.

### `docker-smoke` job — now **nine** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely from
`certification.game_config.num_agents` and hard-fails with `SEAT-COUNT FAIL:` if the workflow's **`<SEATS>` = 2**
disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes — bad-token refusal, `/global` first
frame on connect, `Ping → Pong` **payload echo** — against the real image on the first episode):

1–8. **The bc26 certification-fixture episode and the bc20, bc21, bc24, bc25, bc23, bc22 and bc16 episodes, all
   unchanged** → `dist/smoke/replay.json`, `replay-bc20.json`, `replay-bc21.json`, `replay-bc24.json`,
   `replay-bc25.json`, `replay-bc23.json`, `replay-bc22.json`, `replay-bc16.json`.
9. **A bc19 episode**, new: `SMOKE_EXPECT_YEAR=bc19`, `SMOKE_PLAYER_IDS=awu,scaffold`, `SMOKE_CONTRACT_PROBE=0`,
   `SMOKE_REPLAY_OUT=dist/smoke/replay-bc19.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc19","pool":"small","seed":<the seed test 11 pins>,
   "gamesPerMatch":1,"maxRounds":600,"perGameBudgetSeconds":60,"matchBudgetSeconds":70, "connectTimeoutMs":15000}`.
   **600 rounds and not 400**, for reasons that are this year's: on the pinned map (`seed-0043`, 35×35, two castles a
   side, **minimum castle separation 14**, 89.4 % passable, 4 karbonite and 4 fuel depots a side) a 400-round window
   shows the opening economy but not the first military exchange, while 600 rounds guarantees **a pilgrim on every
   near depot, at least one deposit at a castle, at least one military unit built on both sides, and first contact** —
   a crusader crosses 14 squares in ~5 turns once built. 600 rounds also records ~15–20 s of playback, which
   comfortably outlasts the viewer smoke's 10 s soak (the ecos 2026-08-23 scar). The seed is pinned to draw
   `seed-0043` and `tests/test_bc19_maps.nim` asserts that draw.

All nine run one game container + two player containers on a shared network with `file://` artifact URIs and **no
`ANTHROPIC_API_KEY`**, so both seats take the scripted path and must still complete. All nine assert: the game exits
0, **every player container exits 0**, `results.json` carries exactly the expected key set, `reason == "complete"`,
`scores` has 2 entries, `fallbacks == [0, 0]`, and the replay parses as **strict UTF-8 JSON** with `format ==
"cogame-battlecode-replay"`, the right `year`, and a non-empty `events` array. A step asserts all nine replays exist
and report **nine different `year` values**.

**The episode substance assertion (the LEARNINGS 2026-09-03 pin), in two parts.** The bc19 episode passes
`SMOKE_REQUIRE_STATS` — the **per-seat** floor the script already enforces for both seats — with
`{"units_built":3,"moves":40,"damage_dealt":0}`. Those are things *both* chassis do, including the weak floor:
`examplefuncsplayer19`'s castles build a crusader every tenth turn from round 1 and its crusaders move every turn.
(`damage_dealt` is floored at **0** per seat deliberately — the weak floor never aims, so it may legitimately deal
nothing.) **The signatures of the year are things only a seat playing well does** — mining, depositing, expanding to a
church, trading, landing a preacher blast — and `examplefuncsplayer19` does **none** of them, so asserting them
per-seat would be asserting that the weak floor is not weak. They are asserted **across the pair** by one `jq` step in
`ci.yml`, reading the **replay's** `result` block (not `dist/smoke/results.json`, which every episode overwrites in
turn — the bc24 fix): `([.result.games[0].units_built[]] | add) >= 8`, `([.result.games[0].karbonite_mined[]] | add)
>= 40`, `([.result.games[0].fuel_mined[]] | add) >= 100`, `([.result.games[0].karbonite_deposited[]] | add) >= 30`,
`([.result.games[0].pilgrims_built[]] | add) >= 2`, `([.result.games[0].attacks[]] | add) >= 1`,
`([.result.games[0].damage_dealt[]] | add) >= 10`, `(.result.games[0].ids_spent) >= 12` and
`(.result.games[0].queue_length_end) >= 6`. Together they make an idle win machine-visible, which is exactly what the
2026-09-03 round-1 degenerate match lacked. **And the floors are measured, not guessed**: phase 20 runs the real bc19
smoke once, reads the actual per-seat statistics out of `dist/smoke/replay-bc19.json`, and sets the committed floors
at roughly **half the weak seat's measured value** — never above what a correct episode produces — and where that
conflicts with "never below this note's numbers", **the second constraint wins and the measurement goes inline in
`ci.yml`** (the bc23 r1-F22 ruling: a floor derived from whole 1000-round games is wrong for a 600-round smoke). **If
the across-the-pair `karbonite_deposited >= 30` or `attacks >= 1` assertion does not hold on the measured episode, the
fix is to raise the smoke's `maxRounds` until it does — never to drop the assertion**: an episode of this year in
which nobody ever refined a load or fired a shot is not this game being played.

### `wasm-viewer` job — the bundle is **executed**, against **all nine** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete (`index.html`, a
non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`, `static_replay.js`,
`static_replay_worker.js`, `wire_constants.js`), then run `node tools/ci/viewer_smoke.mjs --bundle
dist/static-replay-viewer --replay <replay> --killfeed-overlap` in headless chromium (Playwright pinned **1.55.0** in
both places — the npm module and the browser download) **once per replay**: `replay.json`, `replay-bc20.json`,
`replay-bc21.json` **and `replay-bc19.json`** at `--timeout 90 --soak 10`, and `replay-bc24.json`, `replay-bc25.json`,
`replay-bc23.json`, `replay-bc22.json` and `replay-bc16.json` at `--timeout 120 --soak 15`. **This is the viewer smoke
the checklist asks for: `tools/ci/viewer_smoke.mjs`, run by `ci.yml`'s `wasm-viewer` job, against the replay
`docker-smoke` actually produced — the bundle is EXECUTED in a real browser, not merely built.**

Each run requires: **`data-replay-loaded="true"`** (or the bridge `ready` posted after it — and **`data-replay-error`
must be absent**); three **differing** clock/scorebug readouts at 0 % / 50 % / 100 %; continued advancement across the
soak; **`scrub_selector == "#scrub"`** (so a seek was really exercised and the `#viewpanel` zoom slider was not
clicked instead); `#endcard` **computed-shown** after the 100 % seek carrying a `clan` line; the **`#endcard`
no-overflow assertion at 1280×800** (§Viewer, endcard fix 2); no overlay covering more than 50 % of the board after
the soak; and the `#killfeed`/stat-box overlap check at **360 px, 720 px and 1280 px at both FIT and 2× zoom**.

`--strict-text-bounds` stays deliberately dropped on the replay runs because the board is pannable and zoomable
(`#viewpanel` is kept), which is the exact case the flag's own documentation excludes — and because
**`canvas_text.total: 0` on this renderer covers nothing and must not be read as a pass** (LEARNINGS 2026-09-08). The
counts are still recorded in `viewer-smoke.json`, and the separate `tools/ci/renderer_fixture.html` step — full-cap
`notes` and `motto` on both seats at three widths **including 360 px**, in the page's own CSS extracted from
`client/replay_broadcast.html` at run time — runs through the same harness **with** `--strict-text-bounds`, because
every CI replay is scripted and carries no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a **bc19
row**. `node tools/wasm_replay_smoke.cjs` is also run against the bc19 smoke replay **and** the committed
`tests/fixtures/replay-bc19.json`, so wasm32-only failures (int overflow traps, address-space exhaustion) in the new
year module are caught.

---

## Out of scope (v1)

- **Any JavaScript, Node or npm at runtime.** No JS engine, no `vm2`, no in-container compilation of anything a cog
  sends. The 2019 engine exists only in the `parity-oracle-bc19` CI job and in `tools/gen_maps_bc19.mjs`, which runs
  at build time on a developer machine or in CI. **No JDK and no JRE either** — bc19's engine is not Java at all, and
  the repository's other years' JVM oracles are untouched by this run. The only other Node in this repository is the
  CI-only Playwright harness.
- **`vm2` and the rest of the engine's 404-package dependency tree.** The oracle driver needs `coldbrew/game.js`,
  `coldbrew/action_record.js`, `coldbrew/specs.json` and `mersenne-twister@1.1.0` — proved by running whole games on
  exactly that set. `vm2` is deprecated and carries known sandbox-escape CVEs; `update-notifier` makes a network call
  on every `cli/run.js` invocation (`cli/run.js:13-16`); `rollup`, `esm` and the Python/Java transpilers exist only to
  compile competitor bots, and this coworld has none. Not installed, in CI or anywhere else.
- **The wall-clock chess clock** (V1). The `DecisionOps` clock replaces it with charge == refill, so the clock is
  provably invariant and the engine's freeze branch is unreachable. There is **no bytecode counter in bc19's engine at
  all** — that is a 2016/2020-era mechanism, and 2019 replaced it with a wall clock precisely because each robot is
  its own process — so there is no instruction-level quantity to be faithful to. Tier B′ proves the branch never fired
  in any compared game and proves separately that it fires when it should.
- **Reproducing the `visible`-array shuffle** (V2). It draws from the **global, unseeded `Math.random()`** and was
  measured producing five different orders in six identical runs of the same seed, so there is nothing to reproduce.
  The port orders by ascending `id` and the oracle is patched to match, on the engine side.
- **Runtime map generation** (V3). `regions.sort` at `coldbrew/game.js:153` passes an inconsistent comparator whose
  result is V8-implementation-defined (measured: a plain reversal in 42 of 42 multi-region cases, keeping a
  non-largest region in 40 of them), and **13 of the first 400 seeds produce unplayable boards with zero castles**.
  Maps are generated once at build time under a pinned Node, curated for playability, and committed; the runtime sim
  contains no map generator.
- **The other 364 playable seeds of the first 400, and every seed above 400.** 22 boards are committed and their
  geometry is pinned in §Sim module. `tools/gen_maps_bc19.mjs` handles any seed and CI regenerates all 22; widening
  the pool is one JSON edit plus one CI run, and it is not v1's job.
- **The `.bc19` byte replay format, `coldbrew/vis.js` and the official web visualiser** (V5). Its *unit icons* are
  reused (credited, GPL-3.0); its code is not shipped, not embedded and not built. There are no `.bc19` bytes anywhere
  and no byte-format writer on either side.
- **The `logs` and `error` channels** (V5). `robotLog`/`robotError` push `wallClock()` timestamps into a per-team
  array (`game.js:492-528`) that nothing a score or a spectator reads consumes. The Nim chassis raises nothing and
  logs through the repo's own logger.
- **Win conditions 3 and 4, and `enactTimeout`** (V6). Every robot in this port has a chassis at creation, so
  `initialized` and `hook` are always set and `nulls[t]` is always 0; `record.timeout()` is never called anywhere in
  the upstream engine. `tests/test_bc19_endladder.nim` asserts none of the three is ever produced.
- **`robot.time` in the observation or the trace** (V7), and **`MAX_MEMORY` / `object-sizeof`** (V8, the check is
  commented out upstream at `vm.js:15-22`).
- **A cog-authored bot in any language.** Doctrines are **JSON-sheet only**; there is no compiler, no sandbox, no
  compile-error round trip and no multi-attempt loop. Nothing in the schema is closed against a future sandboxed hook.
- **A bc19 certification fixture, and any new `player[]` entry.** Certification stays on **bc26** and `player[]` stays
  at `awu` + `scaffold` — the cert fixture seats exactly `num_agents = 2` players, so a third `player[]` id fails the
  release with `players_missing` (LEARNINGS 2026-09-04). bc19 is proven by its own `docker-smoke` episode and the
  viewer smoke run against that episode's replay.
- **Worker-side keyframe checkpoints in the viewer.** bc19 seeks re-simulate from the start of the game like every
  other year. bc19 is the year that needs them **least** — 1000 rounds at an estimated 0.6–2.5 ms/round, which is why
  it takes the standard `settle=700 soak=10` probe rather than the heavy one — and keyframes remain the obvious next
  optimisation for the heavy year modules. Deliberately not in v1.
- **A cog-authored comms protocol.** The 16-bit radio layout and the 8-bit castle-talk layout in `comms.nim` are the
  chassis's; a doctrine chooses *which* of the three castle-talk layouts to run (`castle_talk_use`) but cannot
  redefine a field, cannot set a broadcast radius and cannot add a message kind. In this year **every radio broadcast
  is readable by the enemy** (`docs.js:164`), so exposing the layout would be exposing a channel a doctrine could use
  to leak what it should not.
- **A per-castle or per-depot target knob, and a `friendly_fire` knob.** `church_saber_round` decides *when* the order
  commits an infiltration and `defend_radius` decides *how far* it defends; *which* castle a wave walks at and *which*
  depot a pilgrim claims are the chassis's call (the mirror of the nearest own structure, and the cheapest unclaimed
  depot by Dijkstra cost), and exposing them would let a doctrine name a target that does not exist on the map in
  front of it, which the anti-inert rule forbids. Friendly fire is *legal* in 2019 (rule 6.4.2 has no team check) and
  the chassis uses it only where the engine forces it — inside a preacher's own blast — and never as a choice;
  `tests/test_bc19_baselines.nim` asserts no deliberate friendly attack is ever emitted.
- **Per-robot fog in the viewer.** The spectator sees the true board; the fog is the robots'. Terrain, karbonite and
  fuel are public from every robot's first turn anyway (`game.js:728-730`), so the only hidden thing is unit
  positions, and hiding them from a spectator would hide the game.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the watchable artifact is
  the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no messages between
  cogs. One sealed doctrine, then the war. (The **in-game** castle barter is a *rule* the chassis plays, not a channel
  between cogs: neither cog can see the other's doctrine, so `trade_policy` is a standing instruction, not a
  negotiation.)
- **Battlecode years other than 2016, 2019, 2020, 2021, 2022, 2023, 2024, 2025 and 2026.** The registry,
  `game_config.year`, the variant naming and `years/dispatch.nim` all support more; only these nine are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open. All four of the idea's feasibility flags
resolve — §Feasibility verdict gives the file-by-file reason for each, and three resolve better than the idea
expected: the oracle needs one npm package rather than 404, the game is integer-valued end to end, and the weak floor
is licensed because it ships inside the GPL-3.0 engine repository. The eight places where this port deliberately
differs from the engine are enumerated as **decided divergences V1–V8** with a reason each, the six determinism
decisions as **D1–D6**, and the seven places where the human-readable spec contradicts the engine are tabled with the
engine winning every one. The idea's nine candidate knobs all survive with exact types, ranges and defaults —
`pilgrim_count_curve` finalised as the integer `pilgrim_curve`, `unit_mix` finalised as the prophet share of the
military budget — and **two** are added from the engine's own measurements: `preacher_share`, because the preacher's
nine-square blast has no team check and hits its own square, and `trade_policy`, because the two orders can barter
with each other and no archetype the idea names spends that. The one question the idea does not raise and this note
had to settle — whether to port a V8-implementation-defined `Array.prototype.sort` into the sim or resolve the map
generator at build time — is settled in §Sim module V3 **by moving it to a build-time generator, curating the 13
unplayable seeds out, and byte-diffing all 22 committed boards against the pinned engine in Tier B**, which is
strictly better than either porting it or approximating it.)*
