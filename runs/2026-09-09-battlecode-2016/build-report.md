# build-report — `bc16` year module of `Metta-AI/cogame-battlecode`

Run: `2026-09-09-battlecode-2016` · slug `battlecode-2016` · year key `bc16`
Repo: `https://github.com/Metta-AI/cogame-battlecode` · base `main` at `00c1dae`
Branch: `bc16-year-module` (branch-only, one PR, merge with `gh pr merge --merge`)
Design note: `runs/2026-09-09-battlecode-2016/design.md` (2914 lines, read in full)
Phase prompt: `prompts/20-build.md` (read in full)

This file is written INCREMENTALLY, one section per milestone.

## M0 — environment and method (before any code)

Facts established in the sandbox, because they change the method:

- **Nim runs locally.** `nimby` 0.1.26 + Nim 2.2.4 installed exactly as `ci.yml`
  does (`nimby use 2.2.4`, `nimby --global sync nimby.lock`, `nim.cfg`
  regenerated from `~/.nimby/pkgs`). `nim r --path:src tests/test_bc22_units.nim`
  → `ok (293 checks)` in 4.2 s. So compile errors and unit-test failures are
  caught in seconds locally instead of in a 65–90 minute CI round. **CI remains
  the only verdict claimed**; local runs are development only and are never
  reported as green CI.
- **Docker, emsdk and a browser are still absent**, so `docker-smoke` and
  `wasm-viewer` are CI-only, as the phase prompt says.
- **Network reaches the sources the note pins.** `battlecode/battlecode-server-2016`
  clones at `11a0b09f26a70da19f33a61ebec4ceaf6e161aa3` (98 `.xml` maps present),
  `battlecode/battlecode-client-2016` clones, and the oracle jar
  `battlecode-2016.0.2.2.jar` is HTTP 200 at 6 563 607 bytes — the size the note
  pins.
- **Local JDK is 21, not 8.** The oracle needs Temurin 8 (the note's item 1); the
  jar's bundled ASM 5-era instrumenter breaks on 21. Local Java is therefore used
  only to validate the `java.util.HashMap` iteration-order emulation the map
  converter needs (D3), which is implementation-identical in 8 and 21.

Engine rules were read from the pinned checkout, not from the note's summary:
`common/GameConstants.java`, `common/RobotType.java`, `world/GameWorld.java`,
`world/InternalRobot.java`, `world/RobotControllerImpl.java`,
`world/control/ZombieControlProvider.java`, `world/GameMap.java`,
`common/{MapLocation,Direction,ZombieSpawnSchedule,ZombieCount,Team}.java`,
`world/IDGenerator.java`, `world/GameMapIO.java`. Two facts the note states
slightly differently and the port follows the SOURCE on:

1. `GameMap`'s random origin (V3) is only drawn by the *programmatic*
   constructor; a map loaded from XML gets its `origin` from the file
   (`arena.xml` = `266,163`) because XStream sets the final field directly. The
   port still uses origin `(0, 0)` and the conclusion (inert, translation
   invariant) is unchanged — the reason is recorded here so the divergence text
   is true.
2. `getScheduleForRound` sorts by `ZombieCount.compareTo` and `getRounds()`
   sorts, so the only hash-order dependency is `buildZombieSpawnMap`'s
   `byLoc.keySet()` walk — exactly as the note's D3 says.

## M1 — data generation (done, and cross-validated)

**`tools/convert_maps_bc16.py`** (new, 620 lines). Reads the engine's XML
(`<game-map>` + `[y][x]` `<double-array>` rows + `<zombieSpawnSchedule>` +
`<initial-robot>`), computes the symmetry (D4), the per-den schedule split
(D3) and the two memoised den constants, and writes
`data/maps/bc16/<name>.json`. Three validations, all passing:

1. **The Java 8 `HashMap` iteration order emulation is PROVED, not trusted.**
   `JavaHashMap` (`h ^ (h >>> 16)`, bucket `hash & (n-1)`, capacity 16, load
   factor 0.75, resize splitting each bucket into its lo/hi lists in place,
   iteration walking buckets 0..n-1 and each chain in insertion order) was
   compared against a real `java.util.HashMap` fed by `Collectors.toMap` with
   `MapLocation.hashCode() = x*13 + y*23`, on **all 98 official rosters**:
   **98 maps compared, 0 mismatches**. (Bucket chains never reach 8 entries on
   any official roster, so treeification cannot be reached; the converter
   raises rather than guessing if it ever is.)
2. **All 98 official `.xml` maps parse** with `--parse-all`, and **the two
   armageddon maps are REFUSED** with the stated reason (V4):
   `98 official .xml files parsed, 2 refused`.
3. **Every one of the 22 rows of the design note's map table reproduces
   exactly** — size, area, seed, symmetry (including `frogger` = VERTICAL with
   `vertical+rotational` found, the D4 control), archons/side, dens, neutrals,
   rubble mean and max, impassable count, parts total/squares/max, schedule
   length, first wave, per-den zombie total and map total. The note's
   measurements and this independently written converter agree on all 22 maps
   and all 20 columns.

`tools/map_pools_bc16.json`: the three pools exactly as the note names them.
22 maps committed, 396 KB total.

**`tools/gen_year_constants.py --year bc16`** (added arm). 2016's
`GameConstants` is an **interface**, so its fields carry no
`public static final` and the shared `CONST_RE` sees none of them — the bc16
arm has its own regex, recorded in the file's docstring. One shared addition:
`RUBBLE_FROM_TURRET_FACTOR = 1.0 / 3.0` is the only Java *expression*
initialiser in the year, so `1.0/3.0` joins `nim_literal`'s expression table
as `0.3333333333333333` (the double the quotient rounds to — which is why
`145 * (1.0/3.0) = 48.333333333333336` is a named parity vector). Generated
`src/battlecode/years/bc16/constants.nim`; `--check` is idempotent and the
bc20..bc25 arms are untouched.

**`tools/build_sprite_atlas_bc16.py`** (new). Cuts `data/atlas_bc16.png`
(27 538 bytes) + `.json` (2 217) from `battlecode/battlecode-client-2016`
(GPL-3.0, pinned `317e1f3f`) at 16 px: **49 sprites — all twelve robot types
at ALL FOUR `Team` palettes** (a = A, b = B, neutral, horde) plus `creep`. So
bc16 is the first year in the repo whose art can draw a NEUTRAL robot as
itself rather than as a greyed team sprite, which matters because
`neutral_activation` is a headline knob. `--check` verified idempotent.

## M2 — the sim module (done, compiles, plays)

`src/battlecode/years/bc16/`, in the note's own file layout: `constants.nim`
(generated), `units.nim`, `delays.nim`, `health.nim`, `world.nim`,
`economy.nim`, `signals.nim`, `zombies.nim`, `rules.nim`, `maps.nim`,
`knobs.nim`, and `chassis/` with all fourteen files (`kit`, `econ`, `archon`,
`combat`, `micro`, `turret`, `dens`, `neutral`, `rubble`, `infect`, `comms`,
`bulwark`, `greenhorn`, `scenario16`).

**One layout divergence from the note, and it is recorded as such** (to go
into `docs/RULES-BC16.md` §Divergences item 14): the note's `health.nim` was
to carry "the single `changeHealthLevel` mutation point ... the death path,
the rubble deposit, the infection->zombie conversion and the mid-turn
`DESTROYED` check". The mutation half of that list has to reach world state
(the rubble array, the occupancy index, the exec list, `spawnRobot` for the
zombie that stands up), so in Nim it must live beside that state or the two
files import each other. The split landed is: `health.nim` owns the two
independent infection counters, the viper tick, the health cap and
`deathConsequence` (the ordered decision a death makes); `world.nim` owns
`changeHealthLevel`, which applies exactly that decision once and is still
the ONE mutation point. The doc comment in `health.nim` states this; the
`NOTICE` / `docs/RULES-BC16.md` pointers are part of the remaining work.

Year-neutral wiring, all compiler-enforced through the `Session` object
variant: `sim_types.nim` (GV11 + prepend-only changelog +
`ReplayCompatibleGameVersions` extended to GV04..GV11 + `scBulwark`/
`scGreenhorn`), `rng.nim` (ONE optional parameter: `IDGenerator`'s first
block, **0 in 2016** so ids start at 1, against the 10 000 floor every later
year uses — every existing call site keeps the default), `sheet.nim`,
`baselines.nim`, `years/registry.nim`, `years/dispatch.nim` (Session arm,
every `case` arm, `statsJson16` with all the note's result keys, and
`Bc16ActionNames` / `Bc16UnitNames` / `Bc16RungNames`), `decide.nim`
(`Bc16Preamble` + the whole bc16 observation payload), `broadcast.nim`
(`beatsFor`'s bc16 arms with the four colliding names year-tested, and the
five bc16 chrome records `bc16_archons` / `bc16_horde` / `bc16_econ` /
`bc16_units` / `bc16_siege`), `render.nim` (the six-step rubble heat ramp with
hard breaks at 50 and 100, parts pips sized by amount with a hollow mark once
taken, and the four-palette unit sprites; 2016's y axis grows SOUTH, so unlike
every other year the row is not flipped).

**Local evidence (release Nim; CI is still the only verdict and no CI run is
claimed here):** every module compiles; `src/battlecode/{decide,broadcast,
render,server,match,results,replay}.nim` all compile with their bc16 arms; a
3000-round `bulwark` mirror on `river` runs in **2.2 s = 0.74 ms/round** at a
peak of 45/41 robots (the note estimated 2-5 ms/round), on `caverns` 0.45
ms/round, on `prisons` 1.6 ms/round; `w.refusedActions == 0` in every game
played so far (the legality audit) and `opsUsedPeak == 183` against a 2000/1000
budget.

### Chassis measurements, and one finding the next session must act on

Measured `bulwark` vs `bulwark` on the all-defaults sheet, 3000 rounds, the
six `small` maps (release Nim):

| map | rounds | end reason | units built | guards | turrets | dens killed | parts (tenths) | turned |
|---|---|---|---|---|---|---|---|---|
| checkers | 724 | archons_destroyed | 64/70 | 9/14 | 7/6 | 0/0 | 10000/10000 | 65/58 |
| zigzag | 605 | archons_destroyed | 57/53 | 5/9 | 2/2 | 0/0 | 5100/2900 | 2/21 |
| swamp | 1148 | archons_destroyed | 71/70 | 5/4 | 3/4 | 1/0 | 0/0 | 36/57 |
| river | 697 | archons_destroyed | 64/67 | 7/16 | 2/2 | 0/0 | 6400/5600 | 13/12 |
| prisons | 3000 | more_archons | 117/179 | 7/9 | 6/1 | 0/2 | 4000/11000 | 0/19 |
| frogger | 1158 | archons_destroyed | 121/133 | 32/20 | 4/6 | 1/2 | 13600/18600 | 92/107 |

**FINDING (blocking for `tests/test_bc16_survival.nim` as the note specifies
it).** The note's survival gate asks that **>= 5 of 6** mirror games "reach
the round limit or end on the tiebreak ladder (i.e. NOT
`archons_destroyed`)". The measured healthy mirror reaches **1-2 of 6**, and
the reason is arithmetic in the engine rather than a chassis bug: 2016 combat
is extremely slow (a GUARD deals 1.5, doubled to **3.0** against a zombie,
once a round; a SOLDIER deals 4 at attackDelay 2, i.e. **2/round**; a TURRET
13 at attackDelay 3, i.e. **4.3/round**) while a level-9 BIGZOMBIE has
**1500 HP and 75 damage** — so a single late BIGZOMBIE outlives ~350
turret-rounds. Where the factions **broke the dens** the game was stable
(`frogger` reached 3000 in an earlier iteration with 6 dens killed a side;
`prisons` reaches 3000 with 2), and where they did not, the horde won. That is
exactly the axis `den_clear_round` exists for, and it says the committed
threshold has to be measured rather than assumed. Two candidate resolutions
for the next session, in the note's own terms ("the thresholds above are the
design floor, not the committed numbers... never drop the clause"):
   (a) keep the clause and commit the MEASURED ratio with both measurements
       (healthy vs `-d:bc16BrokenChassis`) inline in the test header — the
       bc23 r1-F21/F22 ruling; and/or
   (b) spend one more chassis iteration on den-breaking specifically (a
       standing strike group sized to 2000 HP, and a `den_clear_round` floor
       that commits while attackers survive), which is the play that
       demonstrably stabilises the mirror.
Either way the `-d:bc16BrokenChassis` negative control must still come back
red, and that is the part that keeps the gate honest.

Two chassis decisions taken from measurement and recorded in the code:
* the turret deficit outranks a further attacker once the unconditional
  attacker floor is met AND the stockpile can afford 130 + 30 — without it a
  `turret_count: 3` doctrine built **zero** turrets in 900 rounds on `river`,
  i.e. the knob had no teeth;
* the archon walks at the nearest REMEMBERED parts square when none is in
  sight — a sight-radius-only archon collected **zero** parts in 1 350 rounds
  on `caverns`, whose 110 deposits are all outside r2 35 of its opening
  square.

## M3 — landed on the branch

**Branch `bc16-year-module`, commit `c488388f4a74152ea79c12d8ac7e57acfa93751b`**
(parent `00c1dae`, the merge of PR #9). Landed through the GitHub Git Data API
exactly as the brief pins it — blobs written to files and passed with
`gh api --input`, never as argv flags — and **the landed tree was diffed
against the intended file list and verified: 62 files, every blob sha matching
the bytes sent**. `/tmp/land.py` carries that recipe including the
verification step.

Files landed (62): the eleven `years/bc16/*.nim` + fourteen
`years/bc16/chassis/*.nim`; the nine year-neutral files above; the four tools;
`data/atlas_bc16.{png,json}`; and the 22 `data/maps/bc16/*.json`.

**No CI run has been triggered and none is claimed.** `bc16-year-module` is
deliberately not yet in `ci.yml`'s `on.push.branches` and no PR is open, so
this commit cost no CI round. That is on purpose: the tree still fails
`tests/test_manifest.nim`-class checks that depend on work not yet done
(below), and a 65-90 minute round against a knowingly incomplete tree buys
nothing.

## M4 — regression state of the SEVEN shipped years

The existing suite is being re-run locally against the branch tree (130 test
files, each compiled and run; the sandbox does ~1 shard/8 s so a full pass is
~20 min). At the time of writing **31 shards have run and 31 passed, with zero
failures**, including the three that this run's year-neutral edits could most
plausibly have broken:

- `tests/test_manifest.nim` — **ok (1113 checks)**;
- `tests/test_constants.nim` — **ok (191 checks)** (so the bc20..bc25
  generator arms still byte-diff after the shared `nim_literal` addition);
- `tests/test_determinism.nim` — **ok (87 checks)**;
- plus `test_bc20_*`, `test_bc21_*` shards (maps, knobs, sheet, replay, perf,
  expose, empower, …) all green.

The compiler's own year check did its job three times during the port:
`decide.nim`, `broadcast.nim` and `render.nim` each refused to build until
bc16 had its arm (`not all cases are covered; missing: {yBc16}`), which is
precisely the "a half-added year does not compile" guarantee the dispatch
`Session` variant exists for.

## M5 — NOT DONE, with the exact remaining work

This session did not reach a green CI, and does not claim one. What remains,
in the order the next session should take it (each item is independent of the
others except where noted):

1. **`coworld_manifest_template.json`** — the `bc16` variant (`num_agents: 2`
   inside `game_config`, never at variant top level), `config_schema.year`
   enum gains `"bc16"` (appended), **`config_schema.maxRounds.maximum`
   2000 -> 3000** (the one non-additive edit), the bc16 optional
   `results_schema` properties (the `statsJson16` key set is already the
   source of truth), `end_reason` enum + exactly three values
   (`archons_destroyed`, `more_archon_health`, `more_parts_net_worth`),
   `game.description` sentence, the `rules-bc16.md` docs page (tenth), and the
   two `player[]` descriptions extended. **`player[]` itself and the
   certification fixture stay UNCHANGED on bc26** (pin 2/4).
2. **`tools/ci/policies.json`** — the four bc16 entries with the note's exact
   labels (`battlecode-bc16-bulwark`, `battlecode-bc16-pullers` carrying
   `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`,
   `battlecode-bulwark`, `battlecode-greenhorn`), the two champion prompts
   verbatim from the note's §Decisions, 32 entries total, no sibling entry
   renumbered or re-prompted.
3. **`.github/workflows/ci.yml`** — `bc16-year-module` added to
   `on.push.branches`; the `test` job's `timeout-minutes` **130 -> 150** (an
   authorised cross-year edit); a `BC16_COMMIT` / client-commit env pin and
   the "the bc16 generated files match the pinned 2016 sources" step
   (`gen_year_constants.py --year bc16 --check`,
   `convert_maps_bc16.py --check`, `--parse-all` asserting **98**,
   `build_sprite_atlas_bc16.py --check`); the **eighth `docker-smoke`
   episode** (`SMOKE_EXPECT_YEAR=bc16`, `maxRounds: 900`, the seed pinned to
   draw `river`, the across-the-pair `jq` substance assertions read from the
   REPLAY's `result` block); the `wasm-viewer` job's bc16 replay run at
   `--timeout 120 --soak 15`; and the `parity-oracle-bc16` job.
4. **`client/replay_broadcast.html`** — the appended bc16 game block: the
   seven `#bc16-*` ids, the 41 sibling ids hidden under
   `html[data-year="bc16"]`, all thirteen `.beat-marker.<kind>` rules scoped
   to `html[data-year="bc16"]`, `buildBc16BeatButtons` /
   `applyBc16BeatSpoilers`, `bc16-econ` + `bc16-units` added to
   `relayout()`'s `--statrail` set, the noun row
   `bc16: { unit: 'archon', units: 'archons', res: 'parts' }`, the
   `isBc16` guard, and `window.Bc16Block`. The chrome JSON it draws is
   already emitted (`bc16_archons` / `bc16_horde` / `bc16_econ` /
   `bc16_units` / `bc16_siege`).
5. **`data/bc16/tables.json` + `tools/JavaBc16Tables.java`** — the whole
   finite arithmetic domain (`pow(k/8000, 1.5)` for k = 0..8000,
   `(int)Math.sqrt(r2)` for 0..10 000, the `directionTo` lattice for
   dx, dy in -80..80, the outbreak ladder, the guard pair, the rubble clear
   map, the income curve). NOTE: the port does not READ this table at run
   time (V1 pins the result to 1.0); it exists so the divergence is measured.
6. **Tests** — the note's 27 items. `tests/bc16_fixture.nim` and
   `tools/gen_bc16_fixture_replay.nim` + `tests/fixtures/replay-bc16.json`
   first, because the beats and wasm smokes load them. Two conventions the
   repo has been bitten by, both to be obeyed: never zero
   `perGameBudgetSeconds` in a helper (use `tests/test_bc23_replay.nim:69`'s
   `if perGame > 0:`), and guard every `games[0]`. For the perf gate, the
   repo's OWN precedent is `tests/test_bc21_perf.nim`, which plays the same
   game in both passes and asserts the wall-clock budget in release only, with
   the reason in its header — that is the pattern to follow, and it is not a
   weakening.
7. **The authorised sibling edit**: `tests/test_bc23_replay.nim:132-144` gets
   bc22's tolerant end-reason shape (`reason in [epDeadline, epComplete]`).
   NOT yet applied.
8. **Docs** — `docs/RULES-BC16.md` (the year's rules, the eleven knobs and the
   full §Divergences list V1-V8 + D1-D5 + the `health.nim`/`world.nim` split
   above as item 14 + the chassis's use of the public den roster), the bc16
   sections of `docs/PARITY.md`, `docs/PROTOCOL.md`, `docs/REPLAY.md`,
   `NOTICE` (the four sections the note specifies, naming
   `battlecode-server-2016` GPL-3.0 `11a0b09f`, `battlecode-client-2016`
   GPL-3.0 `317e1f3f` by directory and file family, the CI-only jar, and the
   two UNLICENSED repositories by name as not cloned/read/vendored), and
   `README.md`. Also `docs/plans/2026-09-09-battlecode-2016-design.md` (the
   note itself).
9. **`parity-oracle-bc16`** — `tools/oracle/bc16/{jar.lock,build_oracle.sh,
   Bc16Trace.java,bc16idle,bc16greenhorn,bc16scenario*}`,
   `tools/parity_trace_bc16.nim`, `tools/ci/parity_tiers_bc16.py` (bc22's
   script + the float allowlist + origin normalisation + `zip_longest`),
   `tools/ci/parity_ledger_bc16.json` (empty at the phase-30 exit). The jar is
   HTTP 200 at the pinned 6 563 607 bytes. **Method note for the next
   session, and it is worth a lot:** Nim runs in this sandbox (M0), so if a
   Temurin 8 JDK can also be fetched here, the whole parity loop — Java trace,
   Nim trace, comparator — runs LOCALLY in seconds instead of in 90-minute CI
   rounds, and Tier A can be driven to bit-exactness before the first push.
   That is the single highest-leverage thing available to the next session.
10. **Then**: PR, iterate on PR CI, merge with `gh pr merge --merge`, and run
    the eight phase-20 exit checks.

## Exit-criterion checks 1-8

**Not run: none of them can pass yet.** Check 1 (ci.yml success on main at the
merge commit) requires items 1-9; checks 2-5 (placeholders, exec bits,
workflow registration, workflow inputs) are unaffected by this run so far and
were not re-run; check 6 (`num_agents` in all eight variants) requires item 1;
check 7 (the note's test list running in CI) requires items 3 and 6; check 8
(parity divergences root-caused or ledgered) requires item 9.

## Deviations from the design note so far

1. **`health.nim` / `world.nim` split** (M2) — the mutation half of the note's
   `health.nim` list lives in `world.nim` because it must reach world state.
   To be recorded in `docs/RULES-BC16.md` §Divergences item 14 and in
   `NOTICE`, per the note's own layout rule.
2. **The chassis reads the den roster from the map** rather than
   rediscovering it by sighting. The whole-map zombie schedule is public in
   the real game and this coworld's own observation hands both cogs the den
   locations, so nothing hidden is being read; the sim's fog is untouched and
   no RULE reads the roster. To be recorded in `docs/RULES-BC16.md` as a
   chassis convenience.
3. **`rng.nim` gained one optional parameter** (`initIdGenerator(seed,
   firstBlock = MinId)`) because 2016's `IDGenerator` starts its block at 0
   and mints ids from 1. The note said `rng.nim` was "unchanged, reused"; the
   change is additive and every existing call site keeps the default, so no
   other year's id stream moves.
4. **The V3 reasoning is corrected in the report and in the code comments**:
   the map's random origin is only drawn by `GameMap`'s *programmatic*
   constructor; an XML-loaded map takes `origin` from the file (XStream sets
   the final field directly), e.g. `arena.xml` = `266,163`. The conclusion is
   unchanged (inert, translation-invariant, port uses `(0,0)`), but the note's
   stated reason is not what the source does.
5. **The survival gate's 5-in-6 ratio is not reachable on the measured
   healthy mirror** (M2 FINDING). Unresolved; two candidate resolutions
   recorded, both keeping the clause and the negative control.

## M6 — one regression the GV11 bump causes, found locally (would have cost a CI round)

The local suite run turned up exactly one failure, and it is a real
consequence of the authorised `GameVersion` bump rather than a bug in the port:

```
FAIL tests/test_bc22_beats.nim :: FAIL at this GameVersion: got GV10 want GV11
     (1 of 359 checks failed)
```

Four shards assert the COMMITTED FIXTURE REPLAY's own `game_version` is
EQUAL to the current `GameVersion`:
`tests/test_bc22_beats.nim:41`, `tests/test_bc22_replay.nim`,
`tests/test_bc23_beats.nim` and `tests/test_bc23_replay.nim` (grep:
`doc.gameVersion, GameVersion`). The committed fixtures
`tests/fixtures/replay-bc22.json` and `replay-bc23.json` both carry `GV10`;
bc20/bc21/bc24/bc25's fixtures carry GV05/GV06/GV07/GV08 and their beats
shards do NOT make that assertion, so only those two are affected.

**Resolution for the next session (and it must NOT be to weaken the
assertion):** regenerate those two fixtures with the generators already in
the tree — `tools/gen_bc22_fixture_replay.nim` and
`tools/gen_bc23_fixture_replay.nim` — so they carry GV11, exactly as the bc22
run itself did when it bumped GV09 -> GV10 (which is why bc23's fixture reads
GV10 today rather than GV09). That is regeneration of a generated artefact
forced by an authorised version bump, not a change to a sibling year's
behaviour: the fixtures' events, maps and sheets are reproduced by the same
committed generators.

Everything else that has run is green: **39 shards run, 38 passed, 1 failed
(the GV assertion above)**, including `test_manifest` (1113 checks),
`test_constants` (191), `test_determinism` (87), and the whole bc20, bc21 and
(so far) bc22 families.

## Commit / PR / CI ledger

| item | value |
|---|---|
| branch | `bc16-year-module` |
| commit | `c488388f4a74152ea79c12d8ac7e57acfa93751b` (parent `00c1dae`) |
| files landed | 62, every blob sha verified against the bytes sent |
| PR | **not opened** (the tree is knowingly incomplete; see M5) |
| CI runs | **none triggered, none claimed** |
| failing job names | n/a — no CI run |
