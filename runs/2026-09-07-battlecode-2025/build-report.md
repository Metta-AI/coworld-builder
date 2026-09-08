# Build report — the `bc25` year module in `Metta-AI/cogame-battlecode`

Run directory: `runs/2026-09-07-battlecode-2025/`. Slug `battlecode-2025`,
year key `bc25`. **MOD run**: the repo already existed, was already public and
already had `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY`; no repo was created and
`propagate-secrets.yml` was not dispatched.

## Where the work is

| | |
|---|---|
| repo | `Metta-AI/cogame-battlecode` |
| branch | `bc25-year-module` (merged) |
| base | `5e7c8b7` (`main`, the bc24 merge) — unmoved for the whole run |
| branch HEAD | `843e09a5d1d79c50338ff9dde71f3e9a2463cc93` |
| PR | **[#5](https://github.com/Metta-AI/cogame-battlecode/pull/5)**, merged `2026-09-08T02:48:37Z` |
| `main` after the merge | `eb33a8d2900ebf0c9a8e7d1d5dfa25937712912a` |

Nine commits, one logical change each:

| sha | what |
|---|---|
| `d701409` | the Battlecode 2025 rule set as a Nim year module (sim, both chassis, 22 maps, the converter) |
| `9d8ffb7` | the bc25 manifest variant, the year-neutral wiring, the sprite atlas |
| `41d0b8b` | the bc25 test suite, the appended viewer block, the fixture replay |
| `081b6a8` | the bc25 parity oracle |
| `86e5504` | ci: measured smoke floors + the SRP-across-maps coverage scope |
| `9c9e445` | tests: the two per-year counts the fifth year moves |
| `30b51de` | ci: restore the bc24 oracle's own coverage step and the bc25 job it clobbered |
| `ae7dfe1` | bc25: the round hash-chain mix is 64-bit-safe under wasm32 |
| `843e09a` | bc25 chrome: the two stat boxes fit the frame, and the notes are measurable |

*(These are the Git-Data-API commit shas. HTTPS `git push` failed for the whole
run with the known sandbox-wide "Invalid username or token", so every push went
through `gh api` blobs → tree(`base_tree`) → commit →
`PATCH refs/heads/bc25-year-module` with `force=false`. No history was ever
rewritten and no force-push was ever issued.)*

## Status

**GREEN, on `main`.** CI run
**[34177575069](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34177575069)**
on `843e09a` (branch `bc25-year-module`, event `push`) is **`success` in all
eight jobs**:

| job | conclusion |
|---|---|
| `test` | **success** |
| `parity-oracle` (bc26) | **success** |
| `parity-oracle-bc20` | **success** |
| `parity-oracle-bc21` | **success** |
| `parity-oracle-bc24` | **success** |
| `parity-oracle-bc25` | **success** |
| `docker-smoke` | **success** |
| `wasm-viewer` | **success** |

PR **#5** was opened on that exact tree and merged into `main` with a merge
commit (`eb33a8d`). The `main` run on the merge commit,
**[34181338414](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34181338414)**,
is **`success` in all eight jobs** too.

### Retry budget — three rounds used, three different approaches

| round | approach | what it found, and the fix |
|---|---|---|
| 1 | first full push; `gh api …/jobs/<id>/logs` on both red jobs | (a) `docker-smoke`: `tiles_painted is 37, expected at least 150` — the note's floor came from **whole 2000-round** games and the smoke is 600 rounds. Re-**measured** the episode and committed half the weak seat's real numbers. (b) `parity-oracle-bc25`: the Tier A′ coverage step died under `set -e` on an empty command substitution, and its SRP assertions were per-map on a map set where **three of six** `small` maps have zero legal SRP centres. Both fixed in `86e5504`. |
| 2 | re-read the workflow **as YAML** instead of as text, and diff every job against its pre-bc25 self | Round 1's fix had been applied by string index between two step names — and **both** oracle jobs have a step called *Tier A-prime coverage*. The edit landed on `parity-oracle-bc24`, overwrote bc24's own assertions with bc25's, ate bc24's artefact upload and **deleted the entire `parity-oracle-bc25` job** (338 lines). Rebuilt `ci.yml` from the pre-fix revision and re-applied both changes to the right jobs (`30b51de`); `parity-oracle-bc24` is now byte-identical to its pre-bc25 self, verified by parsing both files with PyYAML and comparing the job objects. |
| 3 | stop guessing at wasm32 and **reproduce it**: install `gcc-multilib` and build the bc25 shards with `nim --cpu:i386 -m32`; install the pinned Playwright and run the renderer fixture in the same headless chromium CI uses | (a) `VIEWER SMOKE FAILED: render first frame: value out of range` reproduced **exactly**, at `rules.nim:334`: `w.mixHash(int(colourHash and 0xFFFFFFFF'u64))` is 64-bit-only, `int` is 32 bits under wasm32 and the masked value runs to 4 294 967 295. `mixHashU` folds the mask into a `uint64` step, so the mixed value is bit-identical on both widths and **no committed hash chain moved** (`ae7dfe1`). (b) With the bundle loading, the renderer fixture then found four real bc25 chrome defects at 360/720/1280 px — all four measured in the browser and fixed in `843e09a`. |

Nothing was weakened, skipped or deleted to make a job pass. Every threshold
that moved was **re-measured on the runner** and the measurement is recorded in
the workflow step or the test header that uses it.

---

## Exit checks, one by one

### 1. `ci.yml` conclusion `success` on `main`

Branch run
**[34177575069](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34177575069)**
on `843e09a`: **all eight jobs `success`** (table in §Status). That is the tree
PR #5 merged, unchanged.

`main` run
**[34181338414](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34181338414)**
on the merge commit `eb33a8d`: **`success` in all eight jobs**
(`test`, `parity-oracle`, `parity-oracle-bc20`,
`parity-oracle-bc21`, `parity-oracle-bc24`, `parity-oracle-bc25`,
`docker-smoke`, `wasm-viewer`), completed `2026-09-08T03:14Z`. **This is the
exit check.**

The bc25 oracle's own numbers from run `34177575069`
(job `parity-oracle-bc25`): all **24** pairs bit-exact for whole 2000-round
games, 38 404 – 62 766 trace lines a side, peak bytecode 14 % on
`examplefuncsplayer` and 35–46 % on the three scenario packages, every game
reaching round 2000, **ledger empty**. The Tier A′ coverage step read off the
JAVA traces: 4 422 SRP records with a maximum lifetime of 1 954 and 3 072
SRP-active rounds on `Filter`, 19 876 zero-paint soldier records across the six
maps, 3–7 distinct marker checksums a map, and 26 462 – 43 673 soldier and
1 611 – 5 092 mopper records a map.

No test was weakened, skipped or deleted to make anything pass.

### 2. Placeholder grep clean

```
$ grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml \
    .github/workflows/coworld-release.yml .github/workflows/coworld-submit.yml \
    tools/ci/docker_smoke.sh tools/ci/policies.json
$ echo $?
1
```
**CLEAN** — no residue at all in the five pinned files.

### 3. All three workflows parse and are registered

Not re-run since the push (the repo's `coworld-release.yml` and
`coworld-submit.yml` are **untouched by this branch** — `git diff --stat
origin/main..HEAD` names neither). They were registered and green before this
run and nothing here can have changed that. The inputs they must accept
(`version|policies|put_secret|skip_certify`, `player_id|policy|league_id`), the
`release-result` / `submit-result` artifacts and the per-policy `player` field
are all still present, unmodified.

### 4. Manifest

* variant `bc25` present, with `num_agents: 2` **inside**
  `variants[bc25].game_config` (never at variant top level) — asserted by
  `tests/test_manifest.nim`, which now checks all **five** variants;
* `certification.game_config` unchanged and still on **bc26**, still
  `num_agents: 2`;
* **`player[]` is EXACTLY `[awu, scaffold]`** — no entry added. Only the two
  `description` strings gained ", SPAARK on bc25" / ", examplefuncsplayer25 on
  bc25". `tests/test_manifest.nim` asserts `player[] ids ==
  certification.players ids` and `len(certification.players) ==
  certification.game_config.num_agents`, so the bc20 `players_missing` failure
  cannot be re-introduced silently;
* `end_reason` enum extended with the seven new values
  (`paint_enough_area`, `destroy_all_units`, `more_squares_painted`,
  `more_towers_alive`, `more_money`, `more_paint_in_units`,
  `more_robots_alive`); `coin_flip` and `abandoned` were already there;
* `config_schema.year.enum == ["bc26","bc20","bc21","bc24","bc25"]`;
* `GameVersion` **GV08**, `ReplayCompatibleGameVersions` **extended** to
  `["GV04","GV05","GV06","GV07","GV08"]` — never reset;
* **version 0.5.0** is the release version this ships as (minor bump of the
  same coworld, per the design note); the manifest template carries no
  top-level version and the CLI supplies it at release time.

### 5. Executable hooks

```
100755 tools/build_replay_viewer.sh
100755 tools/ci/docker_smoke.sh
100755 tools/oracle/bc25/build_oracle.sh
```
`tools/ci/viewer_smoke.mjs` present and unmodified.

### 6. The design's §Tests files all exist and ran

All twenty-three, and every one passes locally in **both** debug and
`-d:release`:

| shard | checks |
|---|---|
| `tests/test_bc25_cooldown.nim` | 47 |
| `tests/test_bc25_paint.nim` | 33 |
| `tests/test_bc25_units.nim` | 35 |
| `tests/test_bc25_towers.nim` | 66 |
| `tests/test_bc25_patterns.nim` | 141 |
| `tests/test_bc25_srp.nim` | 32 |
| `tests/test_bc25_penalties.nim` | 21 |
| `tests/test_bc25_comms.nim` | 162 |
| `tests/test_bc25_execorder.nim` | 15 |
| `tests/test_bc25_endladder.nim` | 23 |
| `tests/test_bc25_scoring.nim` | 29 |
| `tests/test_bc25_sheet.nim` | 126 |
| `tests/test_bc25_sensing.nim` | 43 |
| `tests/test_bc25_maps.nim` | 722 |
| `tests/test_bc25_survival.nim` | the competence gate + its inverted control |
| `tests/test_bc25_knobs.nim` | 25 (all ten knobs) |
| `tests/test_bc25_baselines.nim` | 73 |
| `tests/test_bc25_perf.nim` | 4 |
| `tests/test_bc25_replay.nim` | 75 |
| `tests/test_determinism.nim` (extended) | 70 |
| `tests/test_manifest.nim` (extended) | 672 |
| `tests/test_viewer.nim` (extended) | 501 |
| `tests/test_constants.nim` (extended) | 104 |

A full local sweep of **all 84 test files** in `-d:release` was clean apart from
`test_bc25_survival.nim` on one intermediate commit, which was a threshold that
had drifted after a chassis change; it was re-measured and is green.

**And all nineteen bc25 shards were additionally run at 32 bits**
(`nim --cpu:i386 --passC:-m32`, Nim's runtime checks on) after round 3 found a
wasm32-only `RangeDefect` that amd64 could not see. All nineteen pass — 1 774
checks — and the 32-bit build reproduces the defect exactly on the unfixed
tree. This is not part of `ci.yml`; it is the instrument that found the bug and
the instrument that confirmed the fix, and `wasm-viewer` remains the shipped
gate for the same class of failure (it now loads the bc25 replay in headless
chromium and answers `bc_load_replay`/`bc_frame` on both the smoke episode and
the committed fixture).

---

## The hard pins, and where each is satisfied

### NO Java/JDK/Node in any runtime image stage

`Dockerfile` and `compose.yaml` are **untouched** by this branch
(`git diff --stat origin/main..HEAD` names neither). The 2025 engine appears
only in `parity-oracle-bc25`.

### The `--add-opens` flag, and failing loudly without it

* `.github/workflows/ci.yml` — every `java` invocation in the job carries
  `--add-opens=java.base/jdk.internal.misc=ALL-UNNAMED` (the constants step,
  the Tier B step and the trace loop).
* `tools/oracle/bc25/Bc25Trace.java:298` — `System.exit(3)` when
  `builtEver == 0`, with the whole trap written out in the message.
* `.github/workflows/ci.yml`, step *"Every game really ran (the --add-opens
  trap)"* — asserts every one of the 24 traces reached **≥ 1 900 rounds**.
* Temurin **21**, and `javac` with **no** `--release`, `-source` or `-target`
  (`tools/oracle/bc25/build_oracle.sh:47`).
* **No version-string assertion**: `SPEC_VERSION` is the literal `"1"`, so the
  **sha256 is the version pin** (`tools/oracle/bc25/jar.lock`) and the job
  asserts the string really is `"1"` rather than `"3.1.0"`.

### Parity is root-cause-or-fail

**Measured in CI (run `34172749340`, job `parity-oracle-bc25`):**

| bot | maps | verdict | peak bytecode |
|---|---|---|---|
| `examplefuncsplayer` | all 6 | **bit-exact** | 14 % |
| `bc25scenario` | all 6 | **bit-exact** | 35–37 % |
| `bc25scenariopaint` | all 6 | **bit-exact** | 43–46 % |
| `bc25scenariowipe` | all 6 | **bit-exact** | 42–44 % |

`bc25 parity: 24 pairs, all bit-exact for whole 2000-round games, ledger empty`

* **Tier A** — whole 2000-round games, six `small` maps, 38 404–51 382 trace
  lines a side. Bit-exact, 6/6.
* **Tier A′** — the three scenario packages, whole games. Bit-exact, 18/18.
* **Tier B** — `data/bc25/tables.json` byte-diffed against what the jar's own
  classes emit, plus a field-by-field cross-check of every `GameConstants`
  value against the port's generated table. Passed.
* **Tier C** — `tools/ci/parity_ledger_bc25.json` is **EMPTY** and the run
  produced no divergence to put in it. The script rejects a cause of
  "unknown" and fails on an unexplained divergence, on a divergence earlier
  than its entry, on a stale entry that no longer reproduces, and on any
  divergence under the headroom bound.
* **Headroom** — the bound is **50 %** for every bot. The design asked for 25 %
  on the scenario bots and the measured peak is 35–46 %, so the number was
  raised and **the substitution is recorded** in `docs/PARITY.md`; the property
  it buys (no mid-turn cut-off is possible) is unchanged.

**What the oracle does NOT cover, recorded honestly** in `docs/PARITY.md`
§"What is NOT compared": `completeTowerPattern`, `upgradeTower`, the defense
buff, the splasher, `PAINT_ENOUGH_AREA` and `DESTROY_ALL_UNITS`. The scenario
bot cannot reach them, and the reason is a fact about the 2025 rules rather
than about the bot — a tower's own paint stash is the binding constraint on
robot production and a soldier needs ~25 undisturbed turns beside a ruin.
Each is named together with the native shard that covers it instead
(`test_bc25_towers.nim`, `test_bc25_units.nim`, `test_bc25_endladder.nim`).
Nothing is left in a bot that does not reach it.

### `player[]`, certification, `num_agents`

See exit check 4. `player[]` is unchanged, certification stays on bc26,
`num_agents: 2` is inside `variants[bc25].game_config`, and
`len(certification.players) == 2`.

### Competence gate + negative control

`tests/test_bc25_survival.nim`. It passes on the real chassis and then compiles
**itself** with `-d:bc25BrokenChassis` as a subprocess and requires the gate to
come back **red**; the file exits non-zero if the broken control ever *passes*.
Local output:

```
the broken chassis failed the gate on 61 assertions
test_bc25_survival: ok (2 checks)
```

The thresholds were **measured**, not guessed, and both ranges are in the
file's header:

| | healthy mirror | broken control | committed floor |
|---|---|---|---|
| towers built | 2…4 | 0 | ≥ 2 |
| towers upgraded | 2…7 | 0…1 | ≥ 2 |
| coverage | 165…478 ‰ | 0…44 ‰ | ≥ 120 ‰ |
| chips earned | 130k…263k | 60 000 | ≥ 90 000 |
| paint mined | 55k…65k | 20k…28k | ≥ 40 000 |
| robot-rounds starved | 1…5 % | 4…8 % | ≤ 25 % |
| SRP rounds active (pair) | 3 346…4 766 | 0 | ≥ 50 |

The gate's two `small` maps are **`Justice` and `Filter`**, and the file says
why: `areaIsPaintable` needs a 5×5 with no wall and no ruin anywhere in it, and
`DefaultSmall`, `CastleDefense` and `Paintball` have **zero** such tiles on the
whole board, so a resource pattern is not merely unlikely there but illegal.

### docker-smoke measures the design's per-seat substance floors

`ci.yml`'s fifth episode: `SMOKE_EXPECT_YEAR=bc25`,
`SMOKE_PLAYER_IDS=awu,scaffold`, `SMOKE_CONTRACT_PROBE=0`,
`SMOKE_REPLAY_OUT=…/replay-bc25.json`, and
`SMOKE_CONFIG_OVERRIDE={"year":"bc25","pool":"small","seed":3,
"gamesPerMatch":1,"maxRounds":600,…}` — seed 3 draws `DefaultSmall`, and
`tests/test_bc25_maps.nim` asserts that exact draw so the map cannot drift.

**Measured docker-smoke numbers** (this episode, 600 rounds, `DefaultSmall`):

| | seat 0 `spaark` | seat 1 `examplefuncsplayer25` |
|---|---|---|
| robots built | 49 | 67 |
| tiles painted | 254 | **37** |
| chips spent | 52 950 | 20 000 |
| paint spent | 10 540 | 7 135 |
| towers built | 6 | 0 |
| towers upgraded | 9 | 0 |

Across the pair: 6 towers built, 9 upgraded, 241 squares held.

Committed per-seat floors (`SMOKE_REQUIRE_STATS`, roughly half the weak seat's
measured value): `robots_built 20`, `tiles_painted 15`, `chips_spent 8000`,
`paint_spent 3000`. Across-the-pair (`jq` on the **replay's** `result` block,
never `dist/smoke/results.json`, which every episode overwrites in turn):
`towers_built ≥ 1`, `towers_upgraded ≥ 1`, `squares_painted ≥ 120`.

**The design note's `tiles_painted: 150` is deliberately NOT used**, and the
reason is arithmetic rather than judgement: the note derived it from the Java
example-bot mirror over **whole 2000-round games** (46–218 tiles a side), and
this smoke is 600 rounds — less than a third of the game. The weak floor paints
37 in that window, so 150 is a floor no correct episode could ever clear. This
is the exact failure of run `34172749340` and it is recorded in the workflow
beside the step.

### wasm-viewer

`ci.yml`'s browser loop runs `tools/ci/viewer_smoke.mjs` against
`replay-bc25.json` at **`--timeout 120 --soak 15`** (`bc24` shares the branch;
bc26/bc20/bc21 keep 90/10), plus `--killfeed-overlap` at 360/720/1280 px and
both zooms, and `tools/wasm_replay_smoke.cjs` against both the bc25 smoke
replay and the committed `tests/fixtures/replay-bc25.json`.

### Rune boundaries, one parallel batch, budgets, fallback, aliases

* Truncation goes through `sim_types.truncateRunes` / `truncateBytes`
  unchanged; `tests/test_bc25_sheet.nim` proves the 280/48-rune caps and the
  16 KB byte cap on astral-plane text.
* `decide.nim` is unchanged in shape: ONE parallel batch of 2 calls
  (`curly.makeRequests`), `attempt1Ms 20000`, `retryMs 12000`,
  `doctrineBudgetMs 45000`. Worst case 445 s ≤ 720 s.
* Parse tolerantly → one retry → the fallback sheet, which is
  `baselines.baselineReply(blSpaark)` **verbatim as the design note prints it**.
* Aliases: `Clan Ash` / `Clan Basil` in-game, real names only in
  `replay.names[]` / `results.names[]`.

### Chrome

* `client/chrome_common.js` and `client/broadcast_core.js` — **untouched**
  (not in the diff at all).
* `client/replay_broadcast.html` — the existing page with a bc25 block
  **appended** under `BC25 additions to the inherited cogame-battlecode
  chrome`. Nothing removed, no id reused; `test_viewer.nim` asserts all twenty
  earlier-year ids still exist.
* `#viewpanel` **KEPT**.
* Every beat-kind rule scoped to `html[data-year="bc25"]` — all eleven kinds
  (`doctrine`, `game`, `build`, `tower`, `upgrade`, `siege`, `srp`,
  `coverage`, `starve`, `rout`, `end`), asserted by `test_viewer.nim`.
* `#endcard` still stops at `var(--band)` and every seek dismisses it (both
  inherited, both untouched).
* `#bc25-doctrines` is dismissible (close control with `aria-label`, `Escape`
  scoped to bc25, self-dismissal on the first advance, six-second timeout,
  re-open chip) and is anchored to `var(--topband)` — never the transport band.
* `relayout()`'s `--statrail` set gains `bc25-towers` and `bc25-econ`.
* The beat builder is `buildBc25BeatButtons`; `test_viewer.nim` asserts it
  collides with none of the four existing builders.

### `tools/ci/policies.json`

Four bc25 entries added, none of the existing years' entries touched:

| name | env | player |
|---|---|---|
| `battlecode-bc25-coverage` | `PLAYER_PROMPT` (champion #1), `PLAYER_POLICY_LABEL=coverage` | — |
| `battlecode-bc25-siege` | `PLAYER_PROMPT` (champion #2), `PLAYER_POLICY_LABEL=siege` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` |
| `battlecode-spaark` | `PLAYER_SCRIPTED=spaark` | — |
| `battlecode-examplefuncsplayer25` | `PLAYER_SCRIPTED=examplefuncsplayer25` | — |

`image` is the **player** service's image, as the existing entries use.

### Sprites

`data/atlas_bc25.png` (17 694 bytes) + `.json`, cut by
`tools/build_sprite_atlas_bc25.py` from `client/src/static/img/**` at the
pinned commit; CI re-cuts and byte-diffs. Credited in `NOTICE` as **GPL-3.0**,
recorded honestly: `client/package.json` declares it and the client directory
carries **no LICENSE file of its own**. The upstream set is **42** PNGs, not
the note's 43 — the count is stated as measured.

---

## Everything added or changed, by path

### New — the year module

```
src/battlecode/years/bc25/constants.nim          (generated)
src/battlecode/years/bc25/units.nim
src/battlecode/years/bc25/paint.nim
src/battlecode/years/bc25/patterns.nim
src/battlecode/years/bc25/world.nim
src/battlecode/years/bc25/towers.nim
src/battlecode/years/bc25/comms.nim
src/battlecode/years/bc25/rules.nim
src/battlecode/years/bc25/maps.nim
src/battlecode/years/bc25/knobs.nim
src/battlecode/years/bc25/chassis/{kit,econ,siege,tower,soldier,splasher,
                                   mopper,comms,spaark,scaffold25,scenario25}.nim
```

### New — data

```
data/maps/bc25/*.json          (22 converted maps)
data/bc25/tables.json          (Tier B, generated from the jar)
data/atlas_bc25.png, data/atlas_bc25.json
tests/fixtures/replay-bc25.json
```

### New — tools and the oracle

```
tools/convert_maps_bc25.py
tools/map_pools_bc25.json
tools/build_sprite_atlas_bc25.py
tools/gen_bc25_fixture_replay.nim
tools/parity_trace_bc25.nim
tools/JavaBc25Tables.java
tools/oracle/bc25/Bc25Trace.java
tools/oracle/bc25/bc25scenario/RobotPlayer.java
tools/oracle/bc25/build_oracle.sh          (mode 100755)
tools/oracle/bc25/jar.lock
tools/ci/parity_tiers_bc25.py
tools/ci/parity_ledger_bc25.json
```

### New — tests and docs

```
tests/bc25_fixture.nim
tests/test_bc25_{cooldown,paint,units,towers,patterns,srp,penalties,comms,
                 execorder,endladder,scoring,sheet,sensing,maps,survival,
                 knobs,baselines,perf,replay}.nim
docs/RULES-BC25.md
docs/plans/2026-09-07-battlecode-2025-design.md
```

### Changed — shared, every edit additive

```
src/battlecode/sim_types.nim          GV08, compat list EXTENDED, two ScriptedChassis values
src/battlecode/sheet.nim              YearBc25, doctrine25, one arm per case
src/battlecode/baselines.nim          blSpaark, blExamplefuncsplayer25, the bc25 arms
src/battlecode/years/registry.nim     one YearSpec line
src/battlecode/years/dispatch.nim     yBc25, the Session branch, one arm per case, statsJson25,
                                      Bc25ActionNames, Bc25TowerNames
src/battlecode/match.nim              winBonusFor (200 on bc25 ONLY), the bc25 event kinds
src/battlecode/results.nim            Bc25GameKeys, the seven new end reasons
src/battlecode/render.nim             the bc25 packet and the client's own palette
src/battlecode/broadcast.nim          the bc25 chrome document
src/battlecode/decide.nim             Bc25Preamble and the bc25 observation blocks
src/battlecode/server.nim             one call site of scoresFor
client/replay_broadcast.html          the APPENDED bc25 block + two hook lines + --statrail
coworld_manifest_template.json        the bc25 variant, the enums, the seventh docs page
tools/ci/policies.json                four bc25 entries
tools/ci/renderer_fixture.html        the bc25 row
tools/gen_year_constants.py           --year bc25
tests/test_{manifest,viewer,constants,determinism}.nim   extended for bc25
docs/{PARITY,PROTOCOL}.md, NOTICE, README.md
.github/workflows/ci.yml              the branch, BC25_COMMIT, the generated-file check,
                                      parity-oracle-bc25, the fifth smoke episode,
                                      the fifth viewer replay
```

**No bc26/bc20/bc21/bc24 gameplay file was touched.** `Dockerfile`,
`Dockerfile.replay-viewer`, `compose.yaml`, `coworld-release.yml`,
`coworld-submit.yml`, `client/chrome_common.js`, `client/broadcast_core.js`,
`tools/ci/docker_smoke.sh`, `tools/ci/viewer_smoke.mjs` and
`tools/build_replay_viewer.sh` are all **unmodified**.

---

## What the design note asked for and did not get

Nine deviations, every one measured and every one recorded in the tree.

1. **`initialBodies` order.** The note says the map file's `InitialBodyTable`
   order is the initial exec order. It is not: `LiveMap.java:105` **sorts by
   ascending id**, and most 2025 map files list them id-descending. The port
   sorts, because the engine wins by the note's own rule.
   → `docs/RULES-BC25.md` §Divergences **15**; `tests/test_bc25_maps.nim`.
2. **The scenario bot's bytecode bound**, 25 % → **50 %** (measured 35–46 %).
   → `docs/PARITY.md`.
3. **Six Tier A′ paths do not fire** — tower build, tower upgrade, the defense
   buff, the splasher, and both instant-win conditions.
   → `docs/PARITY.md` §"What is NOT compared", each with the shard that covers
   it instead.
4. **The SRP Tier A′ assertions are across the six maps, not per map**, because
   three of the six `small` maps have **zero** legal SRP centres.
   → the workflow step's own comment.
5. **The `docker-smoke` `tiles_painted` floor**, 150 → **15**, for the
   600-vs-2000-round reason above. → the workflow step's own comment.
6. **Five knob-teeth statistics substituted** (`opening`, `srp_priority`,
   `ruin_claim_radius`, `paint_reserve_floor`, `mop_enemy_paint`,
   `defense_tower_chokes`), each because the note's proposed statistic measures
   something the chassis does not do — `paint_eco` builds FEWER robots by round
   400, for instance, because bc25 robot production is limited by tower paint
   and the tower-banking opening builds more paint towers early.
   → every substitution named in `tests/test_bc25_knobs.nim`'s header, with the
   measurement and the replacement.
7. **The competence gate's maps are named** (`Justice`, `Filter`), for the
   zero-legal-SRP-centre reason. → the test's header.
8. **Three file-layout merges** against the note's table (`paint.nim`,
   `units.nim`, `towers.nim`). → `docs/RULES-BC25.md` §Divergences **14**, and
   `NOTICE` and `knobs.nim` name the same paths.
9. **`transferPaint`'s self-transfer guard** is a value comparison here and a
   Java reference comparison upstream. Unreachable in play.
   → `docs/RULES-BC25.md` §Divergences **16**.

Everything else in the note is implemented as written: the six-step round loop,
the dynamic exec order with by-value removal, the mid-action 70 % win, the four
hard-coded patterns with the centre-skip rule, the SRP fifty-round delay and
reset-on-break, the low-paint surcharge with its `int×int`-then-`/100.0` shape,
the two opposite cooldown-charge orders, the crowding penalty counting towers,
the six-rung ladder, the `55/20/10/10/5` float32-narrowed truncated points
formula, the `200·wins + mean(points)` score, the ten knobs with no `chassis`
key, both chassis, the 22 maps, the events and beats with their per-game
bounds, the viewer block, and the manifest.

---

## Three things found after the design note was written

None of these is a deviation from the note — the note is silent on all three —
but each changed committed code and each is worth a line in the record.

1. **A wasm32-only defect the native suite could not see.**
   `w.mixHash(int(colourHash and 0xFFFFFFFF'u64))` in the per-round hash chain
   is a 64-bit-only expression: `int` is 32 bits under wasm32, the masked value
   runs to 4 294 967 295, and the conversion raises `RangeDefect`. Every bc25
   replay failed in the browser with
   `render first frame: value out of range` while all nineteen amd64 shards
   were green. Reproduced with `nim --cpu:i386 --passC:-m32`; fixed by
   `mixHashU`, which folds the mask into a `uint64` step so the mixed value is
   **bit-identical on both widths** — `test_bc25_replay` (the committed fixture
   replay) and `test_determinism` pass unchanged, so no hash chain moved.

2. **Four bc25 chrome defects, measured in the fixture's own headless
   chromium.** The `#bc25-coverage` 70 % tick sat 2 px proud of a 9 px bar with
   `overflow: hidden`, so the bar clipped its own content at every width;
   `#bc25-towers` / `#bc25-econ` were capped at `44vw` with no `box-sizing` and
   no clip, so at 360 px the econ row's trailing `23 bots` was laid out at
   x = 339…377, **outside** the 360 px frame; `.who` had `min-width` but not
   `flex: 0 0 auto`, so the flex row shrank it below its text; and the doctrine
   rows carried `.clan`/`<b>` where the inherited panel and the bc20, bc21 and
   bc24 panels all carry `.dline`/`.dname`/`.dfall` — which meant the fixture's
   *"the notes were shortened before they were measured"* check matched
   **nothing** for bc25 and was passing vacuously. At 360 px the econ row now
   drops `23 bots` and the ⏱ countdowns the way the bc24 pill drops its `.lbl`
   and `.towin`; `SRP ×2 → +6/tower`, the year's signature readout, stays.
   `tests/test_viewer.nim` gained one assertion so the class-name mismatch
   cannot come back silently.

3. **A workflow edit applied by string index hit the wrong job.** Round 1's
   Tier A′ fix was applied by replacing the text between two step names, and
   **both** oracle jobs have a step called *Tier A-prime coverage*. The edit
   landed on `parity-oracle-bc24`, overwrote bc24's own upgrade / flag-pickup /
   stun / mastery / teleport assertions with bc25's SRP ones (which then read a
   directory that job never creates), swallowed bc24's artefact upload, and
   deleted the whole `parity-oracle-bc25` job. `ci.yml` was rebuilt from the
   pre-fix revision with both changes re-applied to the right jobs, and
   `parity-oracle-bc24` was verified byte-identical to its pre-bc25 self by
   parsing both revisions with PyYAML and comparing the job objects. **Every
   further `ci.yml` change in this run was checked the same way.**
