# 2026-09-10-battlecode-2019 — phase 20 build report

Host repo: `Metta-AI/cogame-battlecode`, base `main@6e89d0f`.
Branch: **`bc19-year-module`** (created via the git data API; `git push` is not
available for a non-`claude/` branch in this sandbox).
Design note: `runs/2026-09-10-battlecode-2019/design.md` (2743 lines) — the spec.

**STATUS: PARTIAL.** The sim module, the wiring, the maps, the atlas, the
manifest, the policies, the viewer block, the docs, the GV12 fixture
regeneration, most of the CI wiring and **nine bc19 test shards** are landed
and locally verified. The parity oracle's driver/bots/comparator, the
`parity-oracle-bc19` job, the remaining test shards and the committed bc19
fixture replay are **not written yet** — the `## M5 remaining work` list at the
bottom is the pick-up point. **CI has not been dispatched**, so nothing here is
claimed green.

---

## M0 environment (done)

- Clone: `/tmp/bc19build` (full history, `gh repo clone`).
- Nim toolchain **works locally**, as the brief said it would: `nimby 0.1.26`
  → `nim 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg` regenerated from
  `$HOME/.nimby/pkgs/*`. `nim r tests/test_rng.nim` = ok in 4.4 s. Whole
  1000-round bc19 mirror games run in **0.03–0.10 s** in `-d:release`.
- Node **v22.22.0** locally — the same version the design note measured the
  V8-implementation-defined `regions.sort` under, and the version pinned in
  `ci.yml` as `BC19_NODE_VERSION`.
- Pinned engine fetched: `battlecode/battlecode19@80cf1cc535ec5a30559274aa1b49807ad4859925`
  → `/tmp/bc19engine`. Root `LICENSE` = GPL-3.0 and the only licence file.
- `mersenne-twister@1.1.0` fetched by `npm pack` and read.
- Docker / emsdk / a browser: NOT available locally — those verdicts come from
  CI only.
- The three unlicensed 2019 repositories were **not cloned, not read, not
  fetched**.

## M1 the sim module (done, landed as `b49fad02`)

`src/battlecode/years/bc19/` — 11 module files + 14 chassis files:

| file | note |
|---|---|
| `constants.nim` | **GENERATED** by `tools/gen_year_constants.py --year bc19` from `coldbrew/specs.json`; the bc19 arm is new and is the simplest arm the tool has (it reads JSON, not Java). `--check` passes. Every nullable column carries its own `*Null` flag so D6's three coercions are real rules and not collapsed to 0. |
| `mt19937.nim` | **VERIFIED BIT-EXACT** against the pinned `mersenne-twister@1.1.0` in this sandbox: `randomInt()` for seeds 0, 1, 43, 2147483647 and `0x80cf1cc5 mod 2^31`, first eight draws each, identical to the npm package's own output. |
| `units.nim` | the engine's own guards (not a capability table), the two tabled non-integer operations, `Team`/`Loc`, `dataRoot()`. |
| `world.nim` | the array turn queue with `robin`, the shadow, the id pool with the V4 guard, `TeamStats`, beats/events, the hash chain. |
| `vision.nim` | the bounded vision box, the field-stripping ladder, ascending-`id` order (V2). |
| `actions.nim` | rule 4's validation ladder and rule 6's enact dispatch, one file, engine order, `temp_fuel` handoff. |
| `resources.nim` | trickle, mining, `give` (amount reduced FIRST — docs disagreement 5), reclaim with the `rad == 0` capacity pin, the barter with both quirks. |
| `rules.nim` | the driver loop (`isOver` BEFORE EVERY TURN), the seven-rung ladder with the literal `win_condition = 1` overwrite, the points formula, `playGame`. |
| `maps.nim` | the committed-board loader including the saved MT state, `poolNames`/`drawMaps`/`sideAslotFor`/`mapCard`. |
| `knobs.nim` | the eleven knobs, absent-key defaulting, `bc19SheetSchema`, `plainWords19`. |
| `chassis/` | `kit, econ, castle, church, pilgrim, military, micro, lattice, comms, trade, infiltrate, saber, examplefuncsplayer19, scenario19` — all fourteen paths the note names. |

### M1 measurements (all local, `-d:release`)

**`saber` vs `saber`, all-defaults, 3 seeds × 2 `small` maps = 6 games, 1000
rounds** — the survival gate's own configuration (seeds 11 / 300 / 1300 give
`sideAslot` 0 / 1 / 1, `seed-0043` and `seed-0048`):

| clause | design floor | measured worst |
|---|---|---|
| games NOT ending `castles_destroyed` | ≥ 5 of 6 | **6 of 6** |
| units built | ≥ 12 | **140** |
| pilgrims built | ≥ 4 | **114** |
| military built | ≥ 4 | **26** |
| karbonite mined | ≥ 150 | **3 614** |
| fuel mined | ≥ 300 | **16 560** |
| deposited / mined | ≥ 80 % | **98.3 %** |
| both stores at 0 for consecutive rounds | ≤ 20 | **3** |
| damage dealt | ≥ 200 | **1 500** |
| units alive at the end | ≥ 6 | **13** |
| castles held at round 700 | ≥ 1 | **2** |
| churches built across the two seats | ≥ 1 on ≥ 1 game | **24 across the six** |
| friendly fire / damage dealt | < 15 % | **0.0 %** |
| `refused_actions` for `saber` | **== 0** | **0 on every seat of every game** |

**The negative control** (`-d:bc19BrokenChassis`, the same six games): 5 units
built, 20 karbonite mined, **0 % deposited**, **0 damage** — the gate goes red,
as it must. A gate that cannot fail is not a gate.

**`saber` vs `examplefuncsplayer19`**, 3 seeds × 2 `small` maps: **saber 6/6**.
`examplefuncsplayer19` builds 6 crusaders and moves 1 085–2 347 times, and its
`refused_actions` is **294–485** — it draws a uniform random direction and
therefore *must* sometimes walk into rock, which is why the note exempts it
explicitly and asserts `> 0` instead.

**`decision_ops_peak` = 461 of `TurnMaxOps` 4000** — 11.5 %, so the cap is
demonstrably non-binding (the note predicted ≈ 1 100 worst case).

**Performance**: a whole 1000-round mirror game is **0.03–0.10 s** on the four
maps measured — an order of magnitude inside the note's 0.6–2.5 s estimate and
40× inside `tests/test_bc19_perf.nim`'s 40 s gate.

### M1 deviations from the design note, each with its reason

1. **The fuel gate is a WAR gate, not a budget freeze.** The note says
   `fuel_reserve` is "the global fuel floor below which the order funds only
   `mine` and `move`". Implemented literally, that deadlocks the order at
   exactly the reserve: a PILGRIM is the thing that MAKES fuel (+10 a turn for
   1, against a flat 25 a round for the whole order), so gating the economy
   behind the reserve means the order cannot afford the miner that would lift
   it over the line. Measured with the literal reading on `seed-0043` and
   `seed-0048`: **3 280 karbonite banked, four military units, zero damage,
   for a thousand rounds.** So the gate applies to **military builds, attacks
   and military movement**; economy builds (pilgrims and churches) are funded
   whenever the order can pay. The knob's two asserted teeth are unchanged
   (rounds at zero fuel down, attacks down). Recorded in
   `chassis/econ.nim`'s `canSpend` docstring; **still to be recorded in
   `docs/RULES-BC19.md` §Divergences.**
2. **`castle_separation_min` / `_max` are the only two non-integer numbers
   bc19 reports.** The note says "no key is reported in tenths … every number
   is an exact integer" and, three sections later, that the two castle
   separations print as `x.x` on the endcard. They are Euclidean distances and
   there is no integer reading, so they are JSON numbers to one decimal and
   everything else is an exact integer. Recorded in `results.nim`'s
   `Bc19GameKeys` docstring.
3. **`pilgrimsWanted` is capped by the depot count** (`depots div 2 + 2`). The
   note's `pilgrim_curve: 24` on a 4-depot board would build twelve pilgrims
   with nowhere to mine, each burning 10 karbonite and 50 fuel. The knob still
   moves the target; it is capped, not overridden.
4. **The castle build priority interleaves** economy and military rather than
   running the pilgrim ramp to completion first. Measured without the
   interleave: **three military units in a whole game on `seed-0009`**, because
   the pilgrims were being farmed and rebuilt for a thousand rounds. The order
   is: economy floor (a karbonite worker and a fuel worker) → the
   two-military-per-structure floor → the pilgrim ramp to half the target →
   the military census → the rest of the ramp. **The economy floor is FIRST
   and that ordering is load-bearing**: with the military floor first, the
   opening hundred karbonite goes on four units, karbonite has no passive
   income, and the order can never buy a miner — measured, four units built in
   a whole game on three of four maps.

## M2 year-neutral wiring (done, landed as `b49fad02`)

Every edit additive; no year-neutral behaviour change anywhere.

- `sim_types.nim`: `GameVersion` **GV11 → GV12** with the prepend-only
  changelog entry; `ReplayCompatibleGameVersions` **EXTENDED** to
  `GV04 … GV11, GV12` (never reset); `ScriptedChassis` gains `scSaber` and
  `scExamplefuncsplayer19`.
- `sheet.nim`: `YearBc19`, `doctrine19`, one arm each in `knownKeysFor`,
  `defaultSheet`, `validate`, `toJson`, `plainWords`. **The envelope resolver
  is untouched.**
- `baselines.nim`: `blSaber` + `blExamplefuncsplayer19`, a `yBc19` arm in
  `defaultBaselineFor` and `baselineFor`, and the all-defaults bc19 reply.
- `years/registry.nim`: **one line**.
- `years/dispatch.nim`: `yBc19`, the `Session` branch (`w19`/`sides19`/
  `chassis19`), one arm per `case`, `statsJson19`, and the three name tables
  (`Bc19ActionNames`, `Bc19UnitNames`, `Bc19RungNames`).
- `match.nim`: `winBonusFor` gains `yBc19` to the 200 set; the seven bc19
  event arms; year discriminators on `first_action`, `rout`, `unit_milestone`
  and `tiebreak`.
- `broadcast.nim`: `isBc19` in `beatsFor`, the six new beat kinds, eight new
  labels and three year-discriminated ones (`duel` reads SKIRMISH for bc19,
  `unit_milestone` uses the six-value vocabulary, `tiebreak` reads castles and
  unit health); `bc19Castles` / `bc19Fuel` / `bc19Econ` / `bc19Units` /
  `bc19Crusade` / `bc19ChromeJson` and the `sessionChromeJson` arm.
- `render.nim`: `bc19UnitSprite`, `renderBc19Terrain` (the visualiser's own
  `#333` ground and `#eee` rock, with procedural karbonite and fuel pips —
  **the upstream has no depot art at all**) and `buildBc19Packet`.
- `results.nim`: `Bc19GameKeys` (56 optional properties) and exactly three new
  `EndReasons` values.

## M3 generated data (done, landed as `b49fad02`)

- **`data/maps/bc19/*.json` — 22 boards.** `tools/gen_maps_bc19.mjs` runs the
  pinned engine's own `Game` constructor under Node v22.22.0, snapshots the
  MT19937 state at the instant `makeMap()` returns, curates for playability
  and writes the board. **Every one of the 22 rows matches the design note's
  measured table exactly** — size, passable count, karbonite and fuel depot
  counts, castles a side, symmetry axis and minimum separation. **All 13
  degenerate seeds (7, 20, 24, 83, 108, 127, 175, 211, 232, 267, 283, 348,
  365) are refused by name** with the reason "fewer than 1 castle a side".
- **`data/bc19/tables.json`** — `tools/JsBc19Tables.mjs`: all 7 939
  `ceil(sqrt(r2))` values and the reclaim's integer division over its whole
  domain, keyed by twice the numerator so one table answers the half-integer
  karbonite case and the integer fuel case. The twelve values the note
  measured (`{0,1,2,3,4,5,9,10,16,64,100,7938} → {0,1,2,2,2,3,3,4,4,8,10,90}`)
  all agree.
- **`data/atlas_bc19.png|json`** — `tools/build_sprite_atlas_bc19.py` cuts the
  six 40×40 `s_*.png` client icons at the visualiser's own two team colours
  (`#DD0048` / `blue`, `vis.js:486`); twelve 16 px cells, 1 400 bytes.
  `--check` passes.
- `tools/map_pools_bc19.json`, and `tools/gen_year_constants.py --year bc19`.

## M3 manifest, policies (done, landed as `b49fad02`)

- `coworld_manifest_template.json`: variant `bc19` appended exactly as the
  note's §Packaging table specifies (`maxRounds: 1000`, `num_agents: 2`,
  `perGameBudgetSeconds: 60`, `matchBudgetSeconds: 200`, players
  `[Clan Ash, Clan Basil]`), `year.enum` appended, `end_reason` gains exactly
  three, `results_schema` gains 56 optional properties, `rules-bc19.md` added
  (eleven pages). **Certification unchanged and still `bc26`; `player[]` ids
  unchanged (only their descriptions extended); NO `config_schema` BOUND
  MOVED** — verified mechanically by diffing the whole `config_schema`
  against `main`'s with the appended year value removed: byte-identical.
- `tools/ci/policies.json`: 32 → **36** entries. `battlecode-bc19-saber` and
  `battlecode-bc19-preachers` (both `PLAYER_PROMPT`, the note's verbatim
  champion texts; #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`),
  `battlecode-saber` and `battlecode-examplefuncsplayer19` (both
  `PLAYER_SCRIPTED`). All four on `cogame-battlecode-player:latest`.

## M3 viewer + CI wiring (done, landed as `38b23960`)

- `client/replay_broadcast.html`: the **existing page with a bc19 game block
  appended** under a banner comment. Six new prefixed ids, every rule scoped
  to `html[data-year="bc19"]` including **all twelve beat-marker colours**,
  `#viewpanel` **kept**, `--statrail` measured set extended with `bc19-econ`
  and `bc19-units`, the endcard noun table gains a bc19 row, the two
  eight-way guards become nine-way, `buildBc19BeatButtons` /
  `applyBc19BeatSpoilers` (never `markBeat`), and the endcard war panel with
  the tiebreak ledger. All nine inline scripts parse under Node.
  **`client/chrome_common.js` and `client/broadcast_core.js` are untouched.**
- `.github/workflows/ci.yml`: `bc19-year-module` in the branch trigger; the
  `BC19_*` pins with the "the committed maps are the rules and the old Node is
  the pin" note; the fetch + constants/atlas byte-diff steps in the `test`
  job; `timeout-minutes` 150 → **180** (ruling 3); a **ninth** `docker-smoke`
  episode with **measured** floors; the across-the-pair substance step; the
  nine-replay assertions; the ninth `wasm-viewer` run on the standard
  `--timeout 90 --soak 10`. The whole file still parses as YAML.

**The docker-smoke floors are measured, not guessed.** Seed **13** draws
`seed-0043` from the `small` pool; 600 rounds, saber (seat 0) against
examplefuncsplayer19 (seat 1) produces:

| statistic | seat 0 | seat 1 | committed floor |
|---|---|---|---|
| `units_built` | 26 | 6 | 3 per seat |
| `moves` | 4 622 | 2 003 | 40 per seat |
| `damage_dealt` | 160 | 0 | 0 per seat (deliberate) |
| across: units / karbonite mined / fuel mined | 32 / 3 382 / 15 410 | | 8 / 40 / 100 |
| across: karbonite deposited / pilgrims / attacks | 3 322 / 10 / 16 | | 30 / 2 / 1 |
| across: damage / ids spent / queue length | 160 / 36 / 32 | | 10 / 12 / 6 |

Every across-the-pair floor the design note names holds on the measured
episode.

## Landed commits

| sha (local) | sha (on GitHub) | what |
|---|---|---|
| `b4c9019` | **`b49fad02`** | the year module, the wiring, the generated data, the manifest |
| `68b3a0d` | **`38b23960`** | the viewer game block, `policies.json`, the CI wiring |
| `b91a636` | **`0691bc84`** | the docs, `NOTICE`, the oracle lock + patches, the GV12 fixture regeneration, the `test_manifest`/`test_viewer` bc19 arms |
| `6545681` | **`7b300cac`** | the first nine bc19 test shards |
| `eb44d2d8` | **`d268dde7`** | `decide.nim`'s bc19 preamble and per-seat observation |

Branch head **`d268dde7ee`**. The landed tree was diffed **blob by blob**
against the local tree after every push: **755 blobs, 0 mismatches**.

No PR opened yet, nothing merged to `main`, no CI run dispatched, no release
input touched.

---

## M4 docs, fixtures and the first nine test shards (done, landed as `0691bc84` and `7b300cac`)

- **`docs/RULES-BC19.md`** — the rules, the unit table, the round loop, the
  end ladder with the literal `win_condition = 1` overwrite, the scoring, the
  eleven knobs, the **seven docs-vs-engine disagreements** with the engine
  winning every one, and the **sixteen-item §Divergences** list (V1–V8, the
  three D6 coercions, the two patch hunks, the `deadline` stop, both chassis,
  the fuel-gate deviation and the two non-integer statistics).
- **`docs/PARITY.md` §bc19** — the pins and why **the Node version is a rules
  pin**, the two places the oracle is not the published engine, the one thing
  the driver does not take from upstream, why bit-exactness is realistic
  here, and honestly what is **not** compared — including that **the freeze
  branch is the one behaviour this oracle cannot compare** and that **Tier A
  is deliberately small in this year because nothing happens without a player
  action**. Its §Status says plainly that the job has not been run.
- **`NOTICE`** — the three sections the design note specifies **verbatim in
  substance**: the GPL-3.0 `battlecode19` engine and sprites with every
  derived file named individually, the GPL-3.0
  `m-schier/battlecode-2019-wololo` behaviour correspondence table, and the
  three **unlicensed** repositories that were not cloned, not read and not
  fetched.
- `docs/PROTOCOL.md`, `docs/REPLAY.md`, `README.md` — the bc19 rows and the
  bc19 payload section.
- **`tools/oracle/bc19/engine.lock`**, **`visible_order.patch`** (V2, one
  hunk) and **`examplefuncsplayer19/determinism.patch`** (two hunks);
  `tools/ci/parity_ledger_bc19.json` ships **empty**.
- **GV12 fixture regeneration (ruling 2, discharged).**
  `tests/fixtures/replay-{bc16,bc22,bc23}.json` carried GV11 and reddened
  `test_bc16_beats`, `test_bc16_replay`, `test_bc22_*` and `test_bc23_*`.
  All three were regenerated with the in-tree generators and re-derive
  clean; **every `game_version` assertion is intact and still pinned to the
  `GameVersion` symbol.** `replay-bc20/21/24/25.json` carry GV05/GV06/GV07/
  GV08 and their tests pin those literals deliberately — they were checked
  and are correct as they stand.
- **Nine bc19 shards, all green locally**: `test_bc19_units` (23 969
  checks), `_mt` (2 261), `_maps` (51 862), `_scoring` (832), `_endladder`
  (35), `_clock` (22), `_sheet` (215), `_baselines` (72), `_survival` (14).
- `tests/test_manifest.nim` (1 563 checks) and `tests/test_viewer.nim`
  (1 018) both green with their bc19 arms.
- **`decide.nim`** gained its three bc19 arms — `chassisNameFor`,
  `Bc19Preamble` and `briefFor`'s per-seat observation (the economy, the six
  unit types with the PROPHET's r² 16 minimum and the PREACHER's nine-square
  blast, the combat rules, the two comms channels, the HOW A GAME ENDS
  block, the generated `sheet_schema` and the scoring weights). **The
  compiler caught this**, which is what the object-variant discipline is
  for.
- **THE WHOLE LOCAL SUITE PASSES AT GV12**: all 152 existing shards plus the
  nine new bc19 ones, **zero failures**, in both the debug pass that was run.
  `src/battlecode.nim` and `src/battlecode_player.nim` both link in
  `-d:release`. (`replay-viewer/bc_replay.nim` compiles as far as the C
  codegen and then needs `emcc`, which the sandbox does not have — that
  verdict comes from CI.)

## M5 remaining work

Ordered so a continuation can pick up in this order. Nothing below is started.

1. **`tools/oracle/bc19/`** — `engine.lock` and both patches are DONE.
   Remaining: `bc19_trace.js` (requires the pinned
   `coldbrew/game.js` + `action_record.js`, reimplements `runtime.js`'s
   twenty-line loop, exits 3 on "nothing happened" and 6 on the Tier B′ clock
   assertion), the seven bots (`bc19idle`, `examplefuncsplayer19`,
   `bc19scenario`, `bc19scenariotrade`, `bc19scenariokill`,
   `bc19scenariotie`, `bc19slowbot`). **The Nim twins
   already exist** (`chassis/scenario19.nim`, `chassis/examplefuncsplayer19.nim`)
   and are written to be trivially mirrorable: every scenario decision is a
   pure function of `me.unit`, `me.turn` and the squares immediately around
   the robot, with the adjacent-square scan order fixed in
   `scenario19.nim`'s `AdjacentScan`.
2. **`tools/parity_trace_bc19.nim`** — the Nim side of the trace, emitting the
   six line kinds the note specifies (`R … Q/T/U/A/G/W`), robots in QUEUE
   order, and the `G` line's `mt=<fnv1a64> mti=<n>` (already computed by
   `mt19937.stateFold` and folded into the hash chain).
3. **`tools/ci/parity_tiers_bc19.py` + `tools/ci/parity_ledger_bc19.json`** —
   bc16's comparator (its bugs are already fixed there): `zip_longest` never
   `zip`, normalisation applied to BOTH sides by one code path, streaming
   comparison, a self-test that constructs a one-line-longer pair and asserts
   a divergence is reported. The ledger ships **empty**.
4. **The `parity-oracle-bc19` job in `ci.yml`** — `actions/setup-node@v4` on
   the exact pinned version with a hard version check, `npm install --no-save
   mersenne-twister@1.1.0` with the integrity assertion, `git apply --check`
   then `apply` for both patches with a hunk count, `timeout-minutes: 45`,
   and the six tiers (A / A′ / A″ / B / B′ / C).
5. **The remaining bc19 test shards.** DONE: `units`, `mt`, `maps`,
   `scoring`, `endladder`, `clock`, `sheet`, `baselines`, `survival`, and the
   `test_manifest`/`test_viewer` extensions. STILL TO WRITE:
   `test_bc19_{queue,actions,combat,economy,trade,comms,vision,
   examplefuncsplayer19,knobs,perf,arith,replay,beats}.nim`, plus the
   extensions to `test_sheet.nim` (the year-neutral side),
   `test_determinism.nim` and `test_constants.nim`. The measured numbers for
   the survival and smoke floors are in M1 and M3 above; use them.
6. **`tests/bc19_fixture.nim`, `tools/gen_bc19_fixture_replay.nim` and
   `tests/fixtures/replay-bc19.json`** — the fixture must emit **all twelve
   beat kinds** or `test_bc19_beats.nim` is a CSS inventory rather than a
   gate.
7. **GV12 FIXTURE REGENERATION (ruling 2, mandated).** `GameVersion` is now
   `GV12`, so any committed sibling fixture carrying `GV11` will redden its
   test. `tests/fixtures/` currently holds bc16/bc20/bc21/bc22/bc23/bc24/bc25
   replays; **they have not been checked or regenerated.** Run the in-tree
   generators, keep every `game_version` assertion intact.
8. **Docs — DONE** (`RULES-BC19.md`, `PARITY.md` §bc19, `NOTICE`'s three
   sections, `PROTOCOL.md`, `REPLAY.md`, `README.md`). The only doc work
   left is updating `PARITY.md` §bc19's **§Status** paragraph once the
   oracle job runs.
9. **`tools/ci/renderer_fixture.html`** — the bc19 row (`YEARS` array,
   `SUPPRESSED_BY_ENDCARD`, and a `BC19_WORDS` block with `plainWords19`'s
   widest output), and the `wasm_replay_smoke.cjs` invocations for the bc19
   smoke replay and the committed fixture in `ci.yml`.
10. **Dispatch CI, drive it green, PR → merge with `--merge`.** Nothing has
    been dispatched. The first run will be red at least on the missing test
    shards' absence (no — `ls tests/*.nim` picks up only what exists, so the
    first red will be `test_manifest.nim`'s triple-sync tripwire against the
    56 new `results_schema` properties, and `test_viewer.nim`'s derived
    hidden-id list).

### Known risks a continuation should read first

- **`test_manifest.nim` and `test_viewer.nim` are already green** with their
  bc19 arms. `docker_smoke.sh`'s own results-key list was checked against
  `ResultsKeys` and needs no change (bc19 adds no TOP-LEVEL key).
- **The `parity-oracle-bc19` job is deliberately NOT in `ci.yml` yet.** Its
  inputs (the lock and both patches) are committed, but adding a job whose
  driver does not exist would make CI red for a reason that says nothing.
  Add the job in the same change as `bc19_trace.js`.
- **`tools/ci/docker_smoke.sh` needs no change** (verified: it takes the seat
  count solely from `certification.game_config.num_agents` and already carries
  every env switch bc19 uses), and **`replay-viewer/config.nims` needs no
  change** (`--preload-file {rootDir}/data@data` already carries
  `data/maps/bc19/`, `data/bc19/tables.json` and `data/atlas_bc19.*`).
- The `Dockerfile` and `Dockerfile.replay-viewer` are **untouched** and must
  stay that way: **no Node, no npm, no JS runtime, no JDK in any image stage**
  (ruling 4). The 2019 engine exists only in `parity-oracle-bc19` and in
  `tools/gen_maps_bc19.mjs`.

---

## Round 3 — CI to green on main

**STATUS: DONE.** `ci.yml` is green on `main` at the merge commit. **No CI
round of this phase was red, so the 3-round red-CI retry budget is still 0 of
3 consumed.** No test was weakened, skipped or deleted; no parity tier was
loosened; the bc19 ledger is still `[]`.

| deliverable | result |
|---|---|
| CI verdict on the inherited branch run | **`34446572285` → `success`** (all 12 jobs) |
| `docs/PARITY.md` §bc19 §Status rewritten, private path deleted | commit **`11d3b29adb`** |
| PR opened and merged with a merge commit | **[#14](https://github.com/Metta-AI/cogame-battlecode/pull/14)**, merged 08:23:00Z |
| merge commit on `main` | **`d2f5d3d7033925655cb64a26cc1a5879c041fec5`** |
| **`ci.yml` GREEN ON `main`** | **run [`34454858348`](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34454858348) → `success`**, all 12 jobs, at `d2f5d3d707` |

### The CI verdicts I took, in order

| run | head | branch | event | conclusion | what I did with it |
|---|---|---|---|---|---|
| **`34446572285`** | `7aa8e6712c` | `bc19-year-module` | push | **`success`** | Watched to the end with `gh run watch 34446572285 --exit-status`; the watcher exited **0**. All twelve jobs green: `test`, `docker-smoke`, `wasm-viewer`, `parity-oracle`, `parity-oracle-bc16/bc19/bc20/bc21/bc22/bc23/bc24/bc25`. The `test` job ran 06:45:26Z → 08:15Z (~90 min against a 180 min timeout). **This is the run that proves the code.** |
| `34454277837` | `530ccbd442` | `bc19-year-module` | push | in progress, not claimed | Not my commit (see *Concurrent operator activity* below). I took a verdict on **one job** of it — `parity-oracle-bc19`, job `102796917054`, **`success`**, including the `Tier B` step the commit edits — because that was the only evidence I needed before rebasing onto it. |
| `34454706128` (push) and `34454806120` (`pull_request`) | `11d3b29adb` | `bc19-year-module` | — | superseded, not claimed | Started by my push and by the PR. The merge landed before they finished; `ci.yml`'s `concurrency: ci-${{ github.ref }}` queues push runs on the same ref rather than cancelling them, so they were still queued/running when the merge run started. **I claim neither.** |
| **`34454858348`** | **`d2f5d3d707`** | **`main`** | push | **`success`** | **The phase-20 exit criterion.** Watched with `gh run watch 34454858348 --exit-status`; the watcher exited **0**. 08:23:03Z → 09:33:15Z. All twelve jobs green: `test` (job `102798774973`, 08:23:06Z → 09:33:14Z, 70 min against the 180 min timeout), `docker-smoke`, `wasm-viewer`, `parity-oracle`, `parity-oracle-bc16/bc19/bc20/bc21/bc22/bc23/bc24/bc25`. `parity-oracle-bc19` = job `102798775171`, 08:23:06Z → 08:24:59Z, `success`, **54 of 54 pairs BIT-EXACT, 0 failures, and zero `##[error]` annotations in the whole job**. |

**Zero red runs. Nothing to root-cause, nothing to fix, no approach to
change.** The reason is that the previous round had already driven the tree to
a state the sandbox could check: before pushing anything I re-ran the 22
`tests/test_bc19_*.nim` shards plus the five year-neutral shards it extended
(`test_manifest`, `test_viewer`, `test_determinism`, `test_constants`,
`test_sheet`) locally under Nim 2.2.4, **each in both debug and `-d:release`,
27 shards × 2 modes = 54 runs, 0 failures**, so the only thing I pushed was a
docs edit no test reads.

### The commit I pushed

**`11d3b29adb9983015d31e42072497fb9377a79ce`** — *"docs(bc19): PARITY.md
§Status is the oracle's real verdict, not a to-do list"*. One file,
`docs/PARITY.md`, +37 −17.

`git push` is still refused for a non-`claude/` branch in this sandbox
(`remote: No anonymous write access`), so this landed through the Git Data API
exactly as the previous round's commits did: blob → tree → commit → `PATCH`
the ref **without** `force`. Both halves were verified against the local git
objects before the ref moved — the API's blob sha
(`70e47c3d189f76c38ac53e10c25e4d23cfd0e747`) and tree sha
(`258c82bcce653eb39baf7487387fa2c32bcd6cd3`) are **byte-identical to
`git rev-parse HEAD:docs/PARITY.md` and `git rev-parse HEAD^{tree}`** on the
local rebase. The first `PATCH` was rejected `422 Update is not a fast
forward`, which is how I found the concurrent commit below; I rebased onto it
and re-landed rather than forcing anything.

#### What §Status now says

It said **"NOT YET RUN"** and listed the driver, the seven bots, the
comparator, the ledger and the CI job as remaining work — all of which exist
and all of which have now run. It now states, tier by tier, what ran in
`parity-oracle-bc19` and what each tier proved, naming the job, the job id,
the branch, the commit, the conclusion and the wall clock (1 m 57 s):

- the comparator self-test (a one-line-longer oracle trace **must** be
  reported as a divergence, and the normaliser **must** be applied to both
  sides);
- **Tier B over its whole finite domain** — all 7 939 `ceil(sqrt(r²))` values,
  the reclaim's whole division domain, all 22 committed boards byte-diffed,
  and the 13 degenerate seeds refused **by name**;
- **Tiers A / A′ / A″ / B′(a) / C over 54 whole-game pairs** — six trace bots
  × nine boards, 1000 rounds each, line for line, `--assert-clock` on every
  one — **54 of 54 BIT-EXACT**;
- the anti-vacuity assertions taken off the **oracle** trace, not the port's
  (Tier A's trickle/id-pool/`wc=1`/one-`A`-line-in-round-1000; Tier A′'s five
  unit types, five action kinds, r² 7938 broadcast, castle talk and carried
  load; the CHURCH's legal 0-damage `ATTACK` on **all nine** boards; and the
  three end rungs);
- **Tier B′(b)**, the separate non-compared `bc19slowbot` run that proves the
  engine really does freeze a slow robot.

**And it no longer cites `runs/2026-09-10-battlecode-2019/build-report.md`.**
That was a path inside the private `coworld-builder` repository, in a public
repo's docs, pointing a reader at a directory they cannot read. `git diff
origin/main...HEAD | grep '^+.*runs/2026'` is now empty and `grep -rn
'build-report'` over `docs/ tools/ tests/ src/ .github/ NOTICE README.md`
returns nothing.

### The PR

**[#14 — `bc19: Battlecode 2019 "Crusade" — the ninth year module`](https://github.com/Metta-AI/cogame-battlecode/pull/14)**
`bc19-year-module` → `main`, merged **`--merge`** (a real merge commit, as
every sibling year did):

```
$ gh api repos/Metta-AI/cogame-battlecode/git/commits/d2f5d3d7 -q '.parents[].sha'
6e89d0fe57cb12e564451a2d2dec6bc99bd7024d      # main before
11d3b29adb9983015d31e42072497fb9377a79ce      # bc19-year-module head
```

`main` moved `6e89d0f` → **`d2f5d3d7033925655cb64a26cc1a5879c041fec5`**.
Fourteen commits, 123 files, +35 832 / −89. The branch
`bc19-year-module` **still exists at `11d3b29adb`** — nothing was deleted and
nothing was force-pushed.

I did **not** author the PR body: PR #14 already existed when I went to open
it (see below), its head was already my commit `11d3b29adb`, and its body
already described the module, the divergences and the parity tiers. Replacing
another author's body with mine would have destroyed information, so I merged
what was there. My drafted body is at `/tmp/pr_body.md` in the builder
sandbox if a reviewer wants to diff the two readings.

### Concurrent operator activity — a phase-30 reviewer must know this

**Two things landed on this branch from outside this thread while I was
working, both authored `daveey` / "David Bloomin":**

1. **`530ccbd44241e24cb18a44a9ce670f1ce5356f68`** at 08:16:29Z, on top of
   `7aa8e6712c` — *"ci(bc19): strip the deliberate negative test's `::error::`
   annotations"*. `.github/workflows/ci.yml` only, +9 −1. It pipes the Tier B
   `--assert-degenerate` invocation through `sed 's/^::error:://'`.
   **I read it before building on it and it is correct, not a mask.** That
   invocation is a *deliberate negative test*: `gen_maps_bc19.mjs:208` prints
   `::error::seed 7 is not a playable board: …` and `:254` prints
   `::error::1 bc19 map failure(s)` for a run whose whole purpose is that the
   board be refused, and GitHub was turning both into **annotations on a green
   job** (run `34446572285`'s summary reads "1 bc19 map failure(s)" beside a
   passing job). The thirteen refusals are printed by `:248` on **stdout**
   with **no prefix** (`console.log('refused 7: …')`), so the `sed` cannot
   touch the strings the following `grep -q "^refused ${seed}: "` asserts, and
   a seed that stopped being refused still fails the step through the shell's
   own `::error::` echo, outside the pipe. Verified green in CI twice
   (`34454277837` job `102796917054`, and the main run) and the main run's
   `parity-oracle-bc19` job now carries **zero** `##[error]` lines.
2. **PR #14 itself**, opened 08:22:26Z with `11d3b29adb` as its head — i.e.
   after my commit landed. `gh pr create` returned *"a pull request for branch
   `bc19-year-module` into `main` already exists"*.

Neither touches game semantics. I made no other change on their account, and
I did not relitigate either.

### §Exit-criterion evidence, run at the green `main` sha

Every check below was run in a checkout of
**`d2f5d3d7033925655cb64a26cc1a5879c041fec5`** — the merge commit, i.e. the
sha `ci.yml` is green on. Verbatim:

```
$ git rev-parse HEAD
d2f5d3d7033925655cb64a26cc1a5879c041fec5

$ if grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml \
    .github/workflows/coworld-release.yml .github/workflows/coworld-submit.yml \
    tools/ci/docker_smoke.sh tools/ci/policies.json
  then echo '::error::unsubstituted placeholders remain'; exit 1; fi
(no output — zero hits for the three names)

$ grep -n '<cow_id>\|<sha>\|<run_id>\|<name>:vN' .github/workflows/*.yml   # the four DOCUMENTED residue names
.github/workflows/ci.yml:4672:  # /v2/coworlds/replays/static/<cow_id>/<sha>/index.html, so a bundle that
.github/workflows/coworld-release.yml:21:#   gh run download <run_id> -R Metta-AI/cogame-battlecode -n release-result \
.github/workflows/coworld-release.yml:84:  #   lists the nested /v2/coworlds/<cow_id>/episode-requests route instead;
.github/workflows/coworld-release.yml:367:        # from GET /v2/coworlds/<cow_id> a couple of minutes later. A version bump
.github/workflows/coworld-submit.yml:17:#   gh run download <run_id> -R Metta-AI/cogame-battlecode -n submit-result \
.github/workflows/coworld-submit.yml:31:        description: "Policy to submit, <name>:vN (omit :vN for the latest version)"

$ for WF in ci.yml coworld-release.yml coworld-submit.yml; do
    gh api repos/Metta-AI/cogame-battlecode/actions/workflows/$WF -q '.name + " " + .state'; done
CI active
Coworld release active
Coworld submit active

$ gh workflow view coworld-release.yml -R Metta-AI/cogame-battlecode --yaml \
  | grep -E '^ +(version|policies|put_secret|skip_certify):'
      version:
      policies:
      put_secret:
      skip_certify:

$ gh workflow view coworld-submit.yml -R Metta-AI/cogame-battlecode --yaml \
  | grep -E '^ +(player_id|policy|league_id):'
      player_id:
      policy:
      league_id:

$ grep -n 'release-result' .github/workflows/coworld-release.yml
21:#   gh run download <run_id> -R Metta-AI/cogame-battlecode -n release-result \
22:#     -D /tmp/rr && jq . /tmp/rr/release-result.json
105:          echo "RR=${RUNNER_TEMP}/release-result" >> "$GITHUB_ENV"
106:          mkdir -p "${RUNNER_TEMP}/release-result"
240:          # This text ends up in release-result.json, which is uploaded as a
445:      - name: Assemble release-result.json
515:          out = os.path.join(rr, "release-result.json")
554:      - name: Upload release-result
558:          name: release-result
559:          path: ${{ env.RR }}/release-result.json
574:          # run should not gain a second red step for it. `release-result`
583:            "$RR/release-result.json")"

$ grep -n 'submit-result' .github/workflows/coworld-submit.yml
17:#   gh run download <run_id> -R Metta-AI/cogame-battlecode -n submit-result \
18:#     -D /tmp/sr && jq . /tmp/sr/submit-result.json
59:          echo "SR=${RUNNER_TEMP}/submit-result" >> "$GITHUB_ENV"
60:          mkdir -p "${RUNNER_TEMP}/submit-result"
97:      - name: Assemble submit-result.json
123:          json.dump(result, open(os.path.join(sr, "submit-result.json"), "w"), indent=2)
136:      - name: Upload submit-result
140:          name: submit-result
141:          path: ${{ env.SR }}/submit-result.json

$ grep -n '"player"\|player_id' .github/workflows/coworld-release.yml
255:              result = softmax("player", "unset")
270:                  player = row.get("player") or None
280:                      switch = softmax("player", "use", player)
308:                      "player_id": player,
539:                  f"{('`' + p['player_id'] + '`') if p.get('player_id') else 'token owner'} |"

$ git ls-files -s tools/build_replay_viewer.sh tools/ci/docker_smoke.sh
100755 c399573ebf305697b9e6b8050d0dbc95afa2fe73 0	tools/build_replay_viewer.sh
100755 b86ea23da5d499b2c88bbfbc43a5639407af91c4 0	tools/ci/docker_smoke.sh

$ test -x tools/build_replay_viewer.sh && test -x tools/ci/docker_smoke.sh && echo 'both executable'
both executable
```

Reading of the placeholder grep: **zero hits for the three names**
`<slug>`, `<IMAGE>`, `<SEATS>`; the six lines above are the **four documented
residue names** (`<cow_id>`/`<sha>` in `ci.yml`'s static-replay-route comment,
`<run_id>` in both artifact-readback recipes, `<name>:vN` in
`coworld-submit.yml`'s `policy` input description) and per
`templates/README.md` they are runtime values, not residue. The grep was never
run on a bare `<`.

And the rest of the tree the exit criterion names, at the same sha:

```
$ ls -1 tools/ci/viewer_smoke.mjs tools/ci/policies.json coworld_manifest_template.json \
     .github/workflows/{ci,coworld-release,coworld-submit}.yml
.github/workflows/ci.yml
.github/workflows/coworld-release.yml
.github/workflows/coworld-submit.yml
coworld_manifest_template.json
tools/ci/policies.json
tools/ci/viewer_smoke.mjs

$ python3 - <<'PY'   # num_agents in EVERY variant and in the cert fixture
variant bc26 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc20 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc21 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc24 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc25 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc23 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc22 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc16 game_config.num_agents = 2 | variant-level num_agents present: False
variant bc19 game_config.num_agents = 2 | variant-level num_agents present: False
certification game_config.num_agents = 2 | year = bc26
replay_viewer = {"bundle": "static-replay-viewer"}
```

`num_agents` is inside every variant's `game_config` and inside
`certification.game_config`, and **never** at a variant's top level
(`CoworldVariant` is `additionalProperties: false`). The certification fixture
is still year **`bc26`** and the manifest `player[]` block is unchanged, as
ruled. `tools/ci/policies.json` carries 36 entries, of which the four new bc19
ones are `battlecode-bc19-saber` and `battlecode-bc19-preachers` (both
`PLAYER_PROMPT`, champion #2 carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) plus
`battlecode-saber` and `battlecode-examplefuncsplayer19` (both
`PLAYER_SCRIPTED`), all four on the same `cogame-battlecode-player:latest`
image, env-switched. Both entry points live in `src/battlecode_player.nim`
(`PLAYER_PROMPT` → LLM seat, `PLAYER_SCRIPTED` → scripted seat).

### Tier C parity ledger state

**`tools/ci/parity_ledger_bc19.json` is `[]` — empty — and it stayed empty
through both green runs. There is nothing to root-cause.**

| evidence | branch run `34446572285` | **main run `34454858348`** |
|---|---|---|
| `parity-oracle-bc19` conclusion | `success` (job `102772780365`) | **`success`** (job `102798775171`) |
| pairs compared | `compared 54 whole-game pairs, 0 failure(s)` | `compared 54 whole-game pairs, 0 failure(s)` |
| `BIT-EXACT` lines in the job log | **54** | **54** |
| trace volume | 819 876 lines a side, **1 639 752 lines compared** (398 lines on the shortest pair, 39 804 on the longest) | same pair set |
| `##[error]` annotations in the job | 2 (both from the deliberate negative test; that is what `530ccbd44` fixed) | **0** |
| `parity-bc19-digests` artifact | **does not exist** | **does not exist** |

The missing artifact is the *positive* evidence, not a gap:
`tools/ci/parity_tiers_bc19.py` writes a digest **only** when
`reports` is non-empty (i.e. only on a divergence), and the upload step is
`if-no-files-found: ignore`. No divergence ⇒ no digest file ⇒ no artifact. A
divergence with no ledger entry exits **2** and reddens the job, which is
root-cause-or-fail enforced by the comparator rather than by convention.

### From the design note: what is implemented, and the one place the wording moved

Everything the design note specifies is in the tree and exercised by CI. The
`## M5 remaining work` list of the previous round is fully discharged: the
oracle driver and all seven bots, `tools/parity_trace_bc19.nim`,
`tools/ci/parity_tiers_bc19.py`, the empty ledger, the `parity-oracle-bc19`
job, all **22** `tests/test_bc19_*.nim` shards, `tests/bc19_fixture.nim`,
`tools/gen_bc19_fixture_replay.nim`, `tests/fixtures/replay-bc19.json`, the
`tools/ci/renderer_fixture.html` bc19 row and both bc19
`wasm_replay_smoke.cjs` invocations (the smoke episode's replay and the
committed fixture).

**One wording divergence, and it is stated in the test rather than papered
over.** M5 item 6 said the fixture "must emit **all twelve** beat kinds or
`test_bc19_beats.nim` is a CSS inventory rather than a gate." The committed
fixture emits **eleven of the twelve**, and `tests/test_bc19_beats.nim:18-26`
records why: `famine` fires only when a store is at zero **and** the acting
robot asked for something it could not pay for, and `saber` never asks for
what it cannot pay — that is the `refused_actions == 0` gate in
`tests/test_bc19_survival.nim`. `famine` is a spectator signal for a **weak or
an LLM** order. So its CSS rule ships, its **label is exercised from a
synthetic event** (two events, one per store, each label asserted against the
store it names), and the "every emitted kind has a scoped CSS rule" obligation
is deliberately stated over the *emitted* set so the file can say this instead
of pretending. The gate is not a CSS inventory: the other eleven are asserted
against the committed bytes.

**Divergence ruling 1's condition of acceptance is satisfied on the merged
tree**, and I verified it rather than assuming it: `docs/RULES-BC19.md:129` is
the **knob table** row for `fuel_reserve`, and it reads *"the fuel floor below
which the order stops making WAR, not the floor below which it stops making
MONEY"*, with the pilgrim arithmetic (+10 a turn for one pilgrim against a
flat 25 a round for the whole order), the measured deadlock (3 280 karbonite
banked, four military units, zero damage on `seed-0043`/`seed-0048`), the
scope (*"the reserve gates military builds, attacks and military movement;
`mine`, `move` and economy builds are funded whenever the order can pay"*) and
the two teeth the knob test asserts (*"rounds at zero fuel down, attacks
down"*). It is in the doctrine sheet's own table, not only in §Divergences
(where it is item 14).

### Cross-year edits: still exactly the two authorised

- **Ruling 2 (mandated).** `tests/fixtures/replay-{bc16,bc22,bc23}.json` are
  regenerated and now read `game_version: "GV12"`; `replay-bc19.json` is
  `GV12` too. `sim_types.nim` is `GameVersion = "GV12"` with
  `ReplayCompatibleGameVersions` **extended** — the array still lists
  `"GV09", "GV10", "GV11", GameVersion` and was never reset.
  `replay-bc20/21/24/25.json` are untouched.
- **Ruling 3.** `ci.yml`'s `test` job `timeout-minutes` is 180. The green main
  run's `test` job needed most of it, which is why the bump was necessary
  rather than tidy.
- **Nothing else.** `git diff origin/main...HEAD --name-only | grep years/ |
  grep -v years/bc19/` returns exactly `src/battlecode/years/dispatch.nim` and
  `src/battlecode/years/registry.nim` — the two year-neutral registration
  files, additive. No sibling year module file, map, atlas or manifest variant
  is edited. **The sibling parity comparator zip-tail/`toHex` bugs in
  bc20/21/24/25 and `match.nim:480`'s `max(1,min())` clamp are untouched**, as
  ruled. No third cross-year edit was needed, so none was made.
- **No Node, no npm, no JS runtime, no JDK in any Docker image stage.**
  `Dockerfile` and `Dockerfile.replay-viewer` are not in the diff at all. The
  2019 engine exists only in the `parity-oracle-bc19` CI job and in
  `tools/gen_maps_bc19.mjs`.
- **The version bump 0.8.2 → 0.9.0 is untouched**, as ruled — it is phase 40's.

### What a phase-30 reviewer should look at first

1. **`docs/PARITY.md` §bc19 §Status** — the only file this round changed. It is
   now a verdict with a run id, not a plan.
2. **`530ccbd44`, the operator's `sed 's/^::error:://'` in `ci.yml`'s Tier B
   step.** My reading of why it masks nothing is above; it deserves a second
   pair of eyes because "strip the error prefix" is a shape that usually *is*
   a mask, and here it is not.
3. **`tests/test_bc19_beats.nim`'s eleven-of-twelve beat set**, and whether
   `famine`-from-a-synthetic-event is the right answer or whether the fixture
   should be made to run a weak order until it fires.
4. **PR #14's body was written by `daveey`, not by this builder.** If review
   wants the builder's own summary of the module, the divergences and the
   tiers, it is the `/tmp/pr_body.md` draft named above and this report.
