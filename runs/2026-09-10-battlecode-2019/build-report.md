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
