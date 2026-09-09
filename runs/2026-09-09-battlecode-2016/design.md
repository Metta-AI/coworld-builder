# cogame-battlecode — the `bc16` year module: Battlecode 2016 "Zombie Invasion" (design note, 2026-09-09)

**Starter: `Metta-AI/cogame-battlecode` itself.** This is a **MOD**, not a new coworld: a branch/PR of
the shipped repo that adds the year module `bc16` beside the shipped `bc20`, `bc21`, `bc22`, `bc23`,
`bc24`, `bc25` and `bc26`, adds the manifest variant `bc16`, keeps certification on `bc26`, and bumps
the version of the *same* coworld. **There is no `cogame-battlecode-2016` repo and none is created.**
The starter is chosen by game shape and it is the only defensible one: bc16 is the same shape as the
seven shipped years — a deterministic Nim grid sim compiled twice (native for the server, wasm for the
viewer), one sealed JSON doctrine per seat, no engine and no JVM at runtime, a static wasm replay
viewer that re-derives every frame — and the year-module boundary
(`src/battlecode/years/<year>/`, `years/registry.nim`, `years/dispatch.nim`, `game_config.year`)
already exists and has now been proved **seven** times. Lineage: `coworld-ctf` (paintbot) →
`cogame-battlecode` → this. The starter is `Metta-AI/cogame-battlecode`, and **every convention there
holds here unless this note says otherwise**: the Nim sim/server/player layout, `nimby.lock`, the
bitworld runtime contract, the `GameVersion` discipline, `tools/build_replay_viewer.sh`, the
`replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch doctrine layer
(`llm.nim` / `decide.nim` / `sheet.nim` / `sheet_common.nim` / `baselines.nim`), the closed results
document, and "degrade, never hang".

`bc16` is the **eighth** year module and the **first pre-2020 year**. This note lands in the repo as
`docs/plans/2026-09-09-battlecode-2016-design.md` on the branch `bc16-year-module`. The copy of
record for the run is `runs/2026-09-09-battlecode-2016/design.md`.

### Provenance — every rule below was read or measured, not assumed

**The official 2016 spec is lost** (dead `s3.amazonaws.com/battlecode-specs`, dead `battlecode.org`,
no Wayback copy). There is therefore **no prose to reconcile against**: the engine source *is* the
spec, and every rule in this note carries a `file:line` citation into it. Where no citation is
possible the rule is marked a **decided divergence** with its reason.

**The rules were read from `github.com/battlecode/battlecode-server-2016` at commit
`11a0b09f26a70da19f33a61ebec4ceaf6e161aa3`** (`HEAD` of `master`, last commit "Final maps"; licence:
root `COPYING` = **GPL-3.0**). Read whole: `world/GameWorld.java` (1051 lines),
`world/RobotControllerImpl.java` (886), `world/GameMap.java` (874),
`world/control/ZombieControlProvider.java` (398), `world/InternalRobot.java` (473),
`common/RobotType.java` (390), `common/GameConstants.java` (162). Also read:
`common/{ZombieCount,ZombieSpawnSchedule,Direction,MapLocation,Team,Signal,RobotInfo,Clock,RobotController}.java`,
`world/{GameMapIO,IDGenerator,DominationFactor}.java`,
`world/control/{TeamControlProvider,PlayerControlProvider,RobotControlProvider,NullControlProvider}.java`,
`util/SquareArray.java` and the 26 files of `world/signal/`.

**All 98 official `.xml` maps in that tree were parsed** for their real sizes, seeds, computed
symmetry, rubble distributions, parts placements, archon and den counts, neutral rosters and full
zombie spawn schedules; **the per-den schedule split was recomputed for every one of them** by
re-implementing `GameMap.buildZombieSpawnMap` including its `java.util.HashMap` iteration order over
`MapLocation.hashCode() = x*13 + y*23`. The pool table in §Sim module is those measurements, not
assumptions.

**The oracle jar was downloaded and inspected in this sandbox.**
`https://s3.amazonaws.com/battlecode-releases-2016/releases/battlecode-2016.0.2.2.jar` — **HTTP 200,
6 563 607 bytes, sha256 `c78ef341af0b666acabdabf545695862b77f84076f946766787bc1549b1fdc1c`**,
**2 484 entries**, `battlecode-version` = `2016.0.2.2`, **449 `battlecode/` classes**, and every
bundled dependency it needs: `org/objectweb/asm` (58 entries — the instrumenter),
`com/thoughtworks/xstream` (463 — the map XML deserialiser), `com/fasterxml` (765),
`org/apache/commons/lang3` (236), plus
`battlecode/instrumenter/bytecode/resources/MethodCosts.txt`. **There is no `gnu/trove` and no
`net/sf/jsi` in this jar and neither is needed** — 2016's engine uses `LinkedHashMap` and `HashMap`
from the JDK, so the trove-iteration-order problem that forced bc22's `trove.nim` **does not arise
here**. So: **no Gradle, no Ivy resolution, no jsi shim, no Maven download list and no `deps.lock`**
in the oracle job. The jar carries **54** of the 98 `.xml` map resources; **every one of those 54 also
exists in the source tree** and the whole played pool is chosen from the 54, so the oracle needs no
`--map-dir`.

**The 2016 client's sprite set exists and is licensed.** `github.com/battlecode/battlecode-client-2016`
(GPL-3.0, `COPYING` present, 35 147 bytes; HEAD `317e1f3ff902ae568619c051813335ecdd72322c`) carries
**92 PNGs** under `src/main/battlecode/client/resources/art/`, including
`{archon,scout,soldier,guard,viper,turret,ttm,zombieden,standardzombie,rangedzombie,fastzombie,bigzombie}{0,1,2,3}.png`
— **four team variants of every one of the twelve robot types** (index 0 = A, 1 = B, 2 = NEUTRAL,
3 = ZOMBIE, matching `Team.values()`), plus `creep.png`, `numbers.png`, `hatch_attack.png`,
`hatch_sensor.png`, `map_bg.png` and an 8-frame `explode/` sequence. That is the art source
(§Viewer, §Packaging).

**The two competitor repositories named in the idea were NOT cloned, NOT read and contribute
nothing.** `TheDuck314/battlecode2016` and `bshimanuki/battlecode2016` carry **no licence anywhere**,
so this run treats them as unreadable. **No line of either repository is copied, vendored, compiled,
translated or read.** The chassis is designed from the engine's own mechanics and from the three
archetypes the idea itself names (turret turtle; aggressive soldier/viper; scout zombie-pull) —
see §The game "Provenance and licensing" and §Decisions.

Base-repo facts are from `Metta-AI/cogame-battlecode` at **`00c1dae`** (`main`, the merge of PR #9,
the bc22 year module), whose shipped coworld version is **0.7.0** and whose `GameVersion` is
**GV10**. Every `path:line` and constant below is to those two trees.

### Source idea (verbatim)

```
# Source idea (verbatim) — 34 Battlecode 2016 Zombie Invasion (mod of cogame-battlecode) — year variant bc16 + its own league

https://app.asana.com/1/1209016784099267/project/1217704774784096/task/1218173818034076

---

ARCHONS build SOLDIERS, GUARDS, VIPERS, TURRETS and SCOUTS and collect PARTS while ZOMBIE DENS spawn escalating waves that turn every kill into a zombie; win by killing all enemy archons or surviving with more. 3000 rounds, 30-80 grids, neutral units that can be activated. Tier 2 in the ranking with strong endogenous archetype diversity at finals (scout zombie-pulling by 'foundation', aggressive soldier/viper by 'Felix & The Buggers', turret turtles), i.e. a great doctrine menu. FEASIBILITY FLAGS: the official spec is lost (dead S3/battlecode.org, no Wayback) so the rules must be lifted from the GPL engine source; no competitor bot carries a licence, so the chassis is written from the postmortems' described strategies, not ported code; the zombie AI and neutral-unit rules must be reproduced exactly. Skip only if the engine source turns out not to define the rules unambiguously.

Seats: 2 (one cog per side). num_agents = 2 in the bc16 variant.
Motive: zero-sum. Doctrine before the war, exactly the cogame-battlecode shape: one sealed JSON sheet per cog, the Nim chassis plays.
Doctrine sheet knobs for bc16 (v1 candidates; the builder finalises them from the chassis it ports): opening {turtle | soldier_viper_aggro | scout_zombie_pull}, turret_count, guard_ratio, zombie_kiting, den_clear_round, parts_priority, archon_spread, neutral_activation, retreat_policy.
Rules, engine, oracle: Engine: https://github.com/battlecode/battlecode-server-2016 (Java 8, Ant/Ivy; root COPYING = GPL-3.0). Oracle jar: https://s3.amazonaws.com/battlecode-releases-2016/releases/battlecode-2016.0.2.2.jar (200, 6.5 MB) with the Ivy resolver in battlecode/battlecode-scaffold; JDK 8. Rules source of truth: the engine's GameConstants/RobotType and the world code (document every rule you lift with a file:line).
Chassis and baselines (behaviour sources): TheDuck314/battlecode2016 (future perfect, 1st — Greg McGlynn; no licence), bshimanuki/battlecode2016 (Foundation; no licence) — behaviour references only, no code reuse.
Ranking: Tier 2 (endogenous) in the ranking; flagged for lost spec + unlicensed bots.
Fills gap: another year of the same doctrine game with a different rule set and metagame, comparable across years on one leaderboard family (softmax.com/battlecode/<year>).
Integrity: symmetric seeded maps, sealed simultaneous doctrines, anonymous aliases, public chassis.
Replay plan (watchability): the standard static wasm viewer of cogame-battlecode — events + seed in the replay JSON, the wasm sim re-derives every frame, paintbot chrome verbatim, this year's official sprite set, an endcard in plain words.

HOW (same as every Battlecode year — mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo): Battlecode is ONE coworld with one manifest variant and one league per year. Work on a branch/PR of cogame-battlecode exactly as run 2026-09-04-battlecode-2020-soup did for bc20: add the year module `bc16` (a full behaviour port of this year's rule set to the deterministic Nim sim — server native, viewer wasm, java.util.Random reproduced, coworld-ctf/paintbot conventions and chrome verbatim; NO Java/JDK/Node in the image), a Nim chassis ported from the BEHAVIOUR of the licensed bots named below (never vendor unlicensed code; XSquare/IvanGeffner repos carry no licence anywhere), the year's doctrine sheet knobs (below) with a fixed per-robot decision budget instead of bytecode metering (documented divergence), the year's maps converted at build time, the official client's sprite set for art (credited), and the Java engine ONLY as a CI parity oracle (Tier A/B/C trace diffs on seeds; every divergence root-caused or written into docs/PARITY.md with round+map+cause — Fleet card 1218171523823317 is the standing example of what not to leave open). Add manifest variant `bc16` (num_agents 2), keep certification on bc26, bump the coworld version and re-upload (phase 40), then in phase 50 create THIS YEAR'S league: seed league_key `bc16`, league_name `Battlecode 2016 — Zombie Invasion`, default_variant_id `bc16`, short_name `bc16` (softmax.com/battlecode/bc16), its own two LLM champions (daveey + daveey-1, distinct doctrines on the chassis) and two scripted fillers, its own credit pool (grant + drip). Never touch the bc26/bc20 leagues or the game's default league. Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side). Do not start while another cogame-battlecode mod run is live (the claim prompt defers this idea until it is Done).

Source: engine and bot repos above; the year ranking is daveey's ~/Downloads/best-battlecodes.md (2026-09-03); sibling https://github.com/Metta-AI/cogame-battlecode (bc26 shipped, bc20 in progress).
```

### Where each binding pin from the brief and the idea is discharged

| Binding pin | Discharged in |
|---|---|
| MOD of `cogame-battlecode`; **one new year module `src/battlecode/years/bc16/` + manifest variant `bc16`**; **branch-only work on `bc16-year-module`, merged by PR**; nothing else on `main` touched | this paragraph, §Packaging ("Branch discipline") |
| `num_agents = 2` in `variants[bc16].game_config`, in every other variant, in the cert fixture, and as `<SEATS>` = 2 | §The game ("Seats"), §Packaging ("Variants", "The `<SEATS>` cross-check") |
| `GameVersion` **GV10 → GV11**; `ReplayCompatibleGameVersions` EXTENDED to keep GV04…GV10 | §Sim module ("Determinism"), §Packaging ("Version bump semantics") |
| Coworld manifest version **0.7.0 → 0.8.0**; certification stays **bc26**; manifest **`player[]` UNCHANGED** | §Packaging |
| `config_schema.year` enum gains `"bc16"`; `results_schema.games[].end_reason` gains this year's values; `game.description` and `game.docs.pages` gain `rules-bc16.md` | §Packaging |
| **No JVM, no JDK, no Node in the runtime image**; the Java engine is a CI parity oracle only | §Packaging, §Tests, §Out of scope |
| Every rule carries a `file:line` into `battlecode-server-2016`; an uncitable rule is a **marked decided divergence** | §The game (rules 1–7 and "Decided divergences") |
| **Bytecode metering is NOT ported** — a fixed per-robot decision budget, deterministic, no wall clock | §Sim module ("The chassis, the DecisionOps budget and the delay-decay divergence") |
| The doctrine layer unchanged: one sealed JSON sheet per cog, the Nim chassis plays it | §Decisions |
| **No knob may select an inert or weak chassis**; a `-d:bc16BrokenChassis` negative control that must FAIL; an economic-survival gate | §Decisions ("the anti-inert rule"), §Tests items 18, 19 |
| Maps converted **at build time** from the engine's `.xml`; art from the 2016 official client, credited in `NOTICE` | §Sim module ("Maps"), §Viewer ("Art"), §Packaging ("Licensing") |
| Parity tiers **pinned to what the harness can deliver**, both traces normalised identically, every divergence root-caused or ledgered with round + map + cause; JDK 8 `javac` with **no `--release`** | §Tests (`parity-oracle-bc16`) |
| Phase 50: league `bc16` / `Battlecode 2016 — Zombie Invasion` / `default_variant_id bc16` / `short_name bc16`, two LLM champions + two scripted fillers, own credit pool | §Packaging ("The phase-50 plan") |
| Doctrine-envelope tolerance (bc23): unwrap one `doctrine`/`sheet` key, count absent-key defaulting, render submitted-vs-applied | §Decisions ("The envelope pin"), §Viewer, §Tests item 14 |
| `perGameBudgetSeconds = 0` means ONE second at `match.nim:480`; tests use the `if perGame > 0:` convention and guard `games[0]`; end-reason assertions tolerant | §Tests items 22, 24 |
| Viewer beats **emitted + labelled + styled**, all three tested from the committed fixture | §Viewer ("The beat contract"), §Tests item 23 |
| Heavy sim → measured ms/round stated, viewer check with `settle=20000 soak=15` | §The game ("Match shape"), §Viewer ("Playback pacing") |
| `viewer_smoke.mjs` scrub selector prefers `#scrub`/`#seek`, excludes `#zoom-slider`; `canvas_text.total: 0` is not a pass signal | §Viewer, §Tests (`wasm-viewer`) |
| Endcard legibility: year-correct nouns, integer scores, no overflow at **1280x800** and legible at **360 px**, no HUD bleed-through, no empty mottos, doctrine card unclipped | §Viewer ("Readouts, 360 px and the endcard") |
| `policies.json` is repo-wide → phase 40 filters to bc16's four with a `policies` dispatch override | §Packaging (`tools/ci/policies.json`) |
| Two name spaces (Clan Ash / Clan Basil in-game; real names spectator-side only) | §The game ("Seats"), §Viewer |
| `## Out of scope (v1)` non-empty | §Out of scope (v1) |

### Interface facts this note is written against (read from `00c1dae`, not assumed)

- **`GameVersion` is `GV10`** and `ReplayCompatibleGameVersions` is
  `["GV04","GV05","GV06","GV07","GV08","GV09", GameVersion]`
  (`src/battlecode/sim_types.nim:16` and `:158`). This run **extends** the list to
  `["GV04",…,"GV10", GV11]`; it never resets it. `tools/ci/check_gameversion.sh` compares the
  *headline*, not the digits, so a sibling branch that takes GV11 first forces this branch to GV12 —
  expected and handled (§Packaging).
- **`config_schema.maxRounds` is `{minimum: 50, maximum: 2000}`.** bc16 plays **3000** rounds, so
  **this is the one schema bound this run must widen: `maximum` 2000 → 3000.** No shipped variant's
  value changes. This is called out here because it is the single manifest edit that is *not*
  additive-by-appending, and `tests/test_manifest.nim` must assert the new bound.
- **`D1` — the chassis is not an LLM-selectable knob.** A submitted `chassis` is recorded in
  `sheet_unknown_fields` and ignored (`sheet.nim:168-171`). **The bc16 sheet has no `chassis` key.**
- **`sheet.nim`'s envelope resolver already does everything the bc23 lesson asked for**
  (`sheet.nim:96-155`): rule order `""` → `"sheet"` → `"doctrine"` → single object-valued key, at most
  one unwrap, recorded in `Sheet.envelope` (`:59-65`), and `results_schema.required` already declares
  `sheet_envelope`. **bc16 needs no year-neutral change here** — only its own arm and the absent-key
  counting inside its own `knobs.nim` (§Decisions, "The envelope pin").
- **`ScriptedChassis`** (`sim_types.nim:182-196`, fourteen values) and **`Baseline`**
  (`baselines.nim:20-34`, fourteen values) each gain two, plus one arm each in `defaultBaselineFor`,
  `baselineFor`, `baselineChassis` and `baselineReply`. All additive.
- **`EndReason` in `sim_types.nim:216-221` is bc26-only**; each year carries its own end-reason
  strings and `GameOutcome.endReason` is a `string` (`years/dispatch.nim:58-70`). bc16 does the same —
  no year-neutral enum is touched.
- **`results_schema.games[].end_reason`'s enum already has 33 values** and already contains
  `more_archons` (bc22's `MORE_ARCHONS`), `highest_id` (bc20's), `annihilated` (bc21/bc22) and
  `abandoned`. bc16 **reuses `more_archons`, `highest_id` and `abandoned`** and adds exactly
  **three** (§Packaging).
- **`src/battlecode/rng.nim` already ports `java.util.Random`** (`nextInt()`, `nextInt(bound)` with
  both the power-of-two shortcut and the rejection loop, `nextBoolean()`) and `IDGenerator`
  (`rng.nim`, 142 lines). bc16 needs **three** live streams from it (§Sim module, D2) — more than any
  prior year — and no new primitive.
- **`src/battlecode/fdlibm.nim` already ports `StrictMath.exp` bit for bit** (`fdlibmExp`).
  bc16 needs **`Math.pow(x, 1.5)`** instead, over a finite integer-indexed domain, so it is **tabled
  at build time and never evaluated at run time** (§Sim module, "the one transcendental").
- **`match.nim:480` computes `perGame = max(1, min(config.perGameBudgetSeconds, remaining))`**, so a
  test helper that zeroes the field buys a **one-second** budget while `years/bc1x/rules.nim` one
  level down treats 0 as unbounded. bc16's tests use the `if perGame > 0:` convention from
  `tests/test_bc23_replay.nim:69` and guard every `games[0]` behind a non-empty check (§Tests).
  **`winBonusFor` at `match.nim:520` pays 200 for `{yBc25, yBc23, yBc22}`**; bc16 joins that set.
- **`beatsFor` at `src/battlecode/broadcast.nim:139` is the ONE place a beat kind is decided** and
  already carries three year discriminators (`isBc25`, `isBc23`, `isBc22` at `:145-147`) because
  `first_action`, `rout` and `duel` are spelled the same by several years. bc16 emits all three of
  those names **and `archon_lost`**, which bc22 also emits with different fields — so bc16 adds
  `isBc16` and turns four arms into four-way tests (§Viewer, "The beat contract").
- **`relayout()`'s `--statrail` measured-id set** is at `client/replay_broadcast.html:6210` and names
  thirteen ids (`econ`, `bc20-soup`, … `bc22-econ`, `bc22-units`); `#killfeed`'s `bottom` is
  `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))` (line 1270). bc16's job
  is to **keep the fix armed** — add its two boxes — not to re-fix it. The **endcard noun table** is
  keyed by `data-year` at `:6086` (`bc22: { unit: 'archon', units: 'archons', res: 'lead' }`); bc16
  adds one row, so no bc26 noun can reach a bc16 card.
- **`tools/ci/viewer_smoke.mjs` already carries the scrub-selector fix**: `SCRUB_SELECTORS =
  ['#scrub', '#seek', 'input[type="range"]']` tried **one at a time** (`:609,616`), and `ci.yml`
  asserts `scrub_selector == "#scrub"` per replay. Nothing to change; and `canvas_text.total: 0` on
  this renderer covers nothing and **is not read as a pass** (LEARNINGS 2026-09-08).
- **`tools/ci/docker_smoke.sh` already carries every env switch bc16 needs** (`SMOKE_EXPECT_YEAR`,
  `SMOKE_PLAYER_IDS`, `SMOKE_CONFIG_OVERRIDE`, `SMOKE_REPLAY_OUT`, `SMOKE_CONTRACT_PROBE`,
  `SMOKE_SEATS`, `SMOKE_REQUIRE_STATS`, `SMOKE_EXTRA_ENV`) and refuses a `SMOKE_CONFIG_OVERRIDE` that
  changes `num_agents` (`:176-201`); `tools/ci/cert_probe.py` runs inside it. bc16 adds an eighth
  episode and **needs no script change**. **`replay-viewer/config.nims` likewise needs no edit**:
  `--preload-file {rootDir}/data@data` already carries the whole `data/` tree.
- **The `test` job's `timeout-minutes` is 130** (`ci.yml:129`) against a measured ~65–75 min per round
  with six year modules (LEARNINGS 2026-09-08); bc16 raises it to **150**. **The shipped coworld
  version is 0.7.0**; this run ships **0.8.0**.
- **This repo records `result` (singular) in the replay**, not `results`, and a best-of-three episode
  legitimately plays **fewer** games than `gamesPerMatch` when a side clinches, with `reason` still
  `complete` (LEARNINGS 2026-09-07).

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `Metta-AI/cogame-battlecode` — the same shape as the seven shipped years (real-time grid loop, rules written in Nim for this coworld, one-shot doctrine policy). It **is** the `coworld-ctf` row of the starter table, seven generations on. |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, already public, already AGPL-3.0. **No new repo** (the idea's HOW paragraph). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints: `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=bulwark\|greenhorn` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` (unchanged); `tools/build_replay_viewer.sh` compiles the same sim module — now carrying `years/bc16/` — to wasm; the browser re-derives every round from events + config + seed. No `.rms` bytes anywhere. |
| Real art, starter chrome verbatim | 2016 client sprites cut into `data/atlas_bc16.*` (credited in `NOTICE`); `client/chrome_common.js` and `client/broadcast_core.js` byte-for-byte unchanged; `client/replay_broadcast.html` is the **existing page with a bc16 game block appended**. |
| Two name spaces | In-game aliases **Clan Ash** / **Clan Basil** (`sim_types.nim:174-175`, year-neutral); real player names only in `replay.names[]` / `results.names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **465 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[bc26\|bc20\|bc21\|bc22\|bc23\|bc24\|bc25].game_config` (all unchanged) and `variants[bc16].game_config` (new), and in `certification.game_config` (unchanged, bc26); never at variant top level. |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release workflow unchanged; the bc16 policy set is in §Packaging. |
| Both champions are LLM prompt policies, #1 owned by daveey and #2 by daveey-1; fillers are the scripted baselines, normally 2 | §Packaging (`tools/ci/policies.json`, "The phase-50 plan"). |

---

## Feasibility verdict

**Buildable. There is no load-bearing rule left undetermined by the engine source, and there is no
`OPEN` section in this note.**

The idea reserved a skip for the case where the engine "turns out not to define the rules
unambiguously". It does define them. Read against the five load-bearing areas the brief names:

| Load-bearing area | Verdict | Where it is fully determined |
|---|---|---|
| **Zombie spawn schedule** | determined | The schedule is **data in the map file**, not code: `<zombieSpawnSchedule><round number="N"><zombie-count type="T" count="C"/>` (e.g. `world/resources/arena.xml`). `ZombieSpawnSchedule.getScheduleForRound` (`common/ZombieSpawnSchedule.java:188-197`) returns the round's counts **sorted by `ZombieCount.compareTo`** = type ordinal then count (`ZombieCount.java:67-73`), so the `HashMap` it is stored in cannot leak an order. `getRounds()` sorts (`:167-178`). The per-den division is `GameMap.buildZombieSpawnMap` (`GameMap.java:718-793`) and is exact integer division with a walking leftover cursor. **One** hash-order dependency exists inside it and is resolved at build time — see D3 below. Measured across all 98 maps: every schedule is already ascending in round, and every per-den total is equal within ±1 with the ±1 landing on **both members of a symmetric pair**, so no side is ever advantaged. |
| **Infection** | determined | `InternalRobot.setInfected` (`:240-246`): a VIPER attack sets `viperInfectedTurns = 20`; any zombie attack sets `zombieInfectedTurns = 10`. `processBeingInfected` (`:248-256`), called from `processEndOfTurn` (`:447`): viper infection deals **exactly 2.0** damage and decrements; zombie infection only decrements. `GameWorld.visitDeathSignal` (`:889-903`): a robot that dies **while `isInfected()`** and whose death cause is not `ACTIVATION` spawns `type.turnsInto` on `Team.ZOMBIE` at its own square — and (`:869-877`) leaves **no rubble**. Every branch is explicit. |
| **Neutral activation** | determined | `RobotControllerImpl.activate` (`:718-747`): ARCHON only; `distanceSquaredTo(loc) <= ARCHON_ACTIVATION_RANGE = 2`; a robot must be there and its team must be `NEUTRAL`; core must be ready; cost is `activateCoreAction(ActivationSignal, 0, movementDelay)`. `GameWorld.visitActivationSignal` (`:728-742`): the neutral is killed with cause `ACTIVATION` (so: no rubble, no zombie conversion) and an identical-type robot is spawned on the activator's team with `buildDelay 0`. **Measured: 80 of the 98 maps carry neutrals, and 22 of them carry neutral ARCHONs** — activating one gives you a whole extra archon, which is the first tiebreak rung. |
| **Tiebreaks** | determined | `GameWorld.processEndOfRound` (`:634-680`) is one straight-line ladder: more ARCHONs → `PWNED`; more total archon health → `OWNED`; greater `parts stockpile + Σ partCost of live robots` → `BARELY_BEAT`; higher **maximum live archon ID** → `WON_BY_DUBIOUS_REASONS`. `setWinnerIfNonzero` (`:591-597`) is `n > 0 → A`, `n < 0 → B`, and returns `n != 0`. The comparisons are exact float64 differences. There is no coin flip and no RNG on this path. |
| **RNG** | determined | Exactly **four** `new Random(mapSeed)` instances exist, each with its own 48-bit state: `GameMap`'s origin draw (`GameMap.java:248-250`, **behaviourally inert** — D4), `IDGenerator` (`GameWorld.java:75`), `GameWorld.rand` (`:134`, read **only** by `getNearestPlayerControlled`'s tie-break, `:439`), and `ZombieControlProvider.random` (`:84`, read by `processZombie`'s `nextInt(8)` and `nextBoolean()`). Every call site is enumerated in §Sim module D2 with its exact precondition. `rng.nim` already ports `java.util.Random`. |

Two further things that *could* have been ambiguous and are not:

- **Turn order.** `gameObjectsByID` is a **`LinkedHashMap`** (`GameWorld.java:72`), so the exec order
  iterated at `:158-160` is plain **insertion order with by-value removal** — initial robots in
  map-file order, then spawns in spawn order. Every other robot iteration in the engine
  (`allObjects()`, `getAllGameObjects()`, `getAllRobotsWithinRadiusSq`,
  `getNearestPlayerControlled`, `senseNearbyRobots`, `senseHostileRobots`) reads that same
  `LinkedHashMap`. **There is no trove, no `net.sf.jsi` and no hash-ordered robot sweep anywhere in
  the 2016 round loop** — bc22's single hardest determinism problem simply does not exist here.
- **Arithmetic.** 2016 is a **float64** year (health, damage, delays, rubble, parts are all `double`)
  where 2022 was an integer one. IEEE-754 binary64 add/subtract/multiply/divide/compare are
  *exactly* specified and identical on x86-64 SSE2 and on wasm32, so a Nim port that reproduces each
  expression **in the engine's own order** is bit-exact by construction. The only non-algebraic
  function on any gameplay path is `Math.pow(x, 1.5)` in `InternalRobot.decrementDelays` (`:326`) and
  `(int) Math.sqrt(r²)` in the two radius scans; **both have finite domains and both are tabled at
  build time** (§Sim module). `Math.abs`/comparison in `MapLocation.directionTo` (`:154-182`) is
  exact.

**One rule is deliberately NOT ported and is therefore a decided divergence, not an ambiguity**: the
bytecode-dependent delay decay (`decrementDelays`, `InternalRobot.java:326`). It is pinned to its
`1.0` branch, for the reason argued in §Sim module. That is a *choice*, disclosed, tabled and tested
— not a rule the source failed to define.

---

## The game

**Battlecode 2016 "Zombie Invasion", played by doctrine, simulated in Nim.** Two cogs each command a
faction of robots on a symmetric grid between **30×30 and 80×80**. Neither cog moves a robot. At t=0
each writes a **doctrine** — a JSON sheet of eleven named knobs — and the deterministic sim plays the
whole 3000-round match from those two sheets while both cogs watch.

Each faction starts with **1 to 4 ARCHONS** (1000 HP, cannot be built, and the only thing that
decides the game: lose your last archon and you lose immediately) and **300 PARTS**. Archons build
**SOLDIERS** (30 parts, 60 HP, 4 damage at r² ≤ 13), **GUARDS** (30 parts, **145 HP**, 1.5 damage
melee, **double damage against zombies** and **4 damage blocked** off any hit above 10),
**SCOUTS** (25 parts, 80 HP, **no attack**, **ignores rubble**, sight r² ≤ 53 — the widest eye in the
game), **VIPERS** (120 parts, 120 HP, 2 damage at r² ≤ 20 that **infects for 20 turns**) and
**TURRETS** (130 parts, 100 HP, **13 damage between r² 6 and 40** but immobile — it must *pack* into a
**TTM** to move and *unpack* to shoot again). Archons also **repair** a friendly non-archon for
**1 HP a turn, free**, and **pick up every part on any square they stand on or walk onto**.

And the map is trying to kill both of them. Each map ships a fixed, public **zombie spawn schedule**
— round → counts of STANDARDZOMBIE / RANGEDZOMBIE / FASTZOMBIE / BIGZOMBIE — divided evenly among
the map's **2 to 12 ZOMBIE DENS** (2000 HP each, worth **200 parts** to whoever kills one). Zombies
belong to a third team, see the **whole map** (`sensorRadiusSquared = -1`), walk at the nearest
player-controlled robot of *either* faction and hit it. Every **300 rounds** the **outbreak level**
rises and every zombie spawned after it is stronger: ×1.0, ×1.1, ×1.2, ×1.3, ×1.5, ×1.7, ×2.0, ×2.3,
×2.6, ×3.0, then +1.0 per level — so a round-2700 BIGZOMBIE has **5000 HP and 250 damage**.

Three mechanics make this year its own game rather than a reskin:

1. **Infection turns your army into theirs.** A zombie hit infects for 10 turns; a viper hit for **20**
   and deals 2 damage a turn while it lasts. A robot that **dies while infected** leaves no corpse — it
   **stands back up as a zombie of its own type's `turnsInto`** on the zombie team, at full
   outbreak-scaled health, where it fell: archon → **BIGZOMBIE**, scout → **FASTZOMBIE**, soldier or
   guard → STANDARDZOMBIE, viper/turret/TTM → RANGEDZOMBIE. And because zombies hunt the *nearest*
   player robot of **either** faction, **an infected unit that dies in the enemy's half is a gift to
   you** — which is what `infection_policy: suicide_squad` reaches.
2. **Corpses become walls.** A robot that dies **uninfected** raises the rubble on its square by **its
   own maximum health** (1000 archon, 500 BIGZOMBIE, 145 guard — a third of that on a turret kill), and
   **rubble ≥ 100 is impassable** to everything except a SCOUT, a FASTZOMBIE and a BIGZOMBIE. So a
   battle line physically bricks itself up, and clearing rubble (`0.95r − 10` per action, floored at 0)
   is a real programme. Measured: `caverns` starts with **1078 of its 1892 squares already
   impassable** and `space` with 346 squares at **999 999**.
3. **Neutral units are free units.** 80 of the 98 official maps place NEUTRAL soldiers, guards, scouts,
   vipers and turrets — and **22 place neutral ARCHONS**. An archon within r² ≤ 2 **activates** one:
   the neutral is removed (no rubble, no zombie) and an identical robot appears on your team,
   immediately active, for **zero parts** and only its own movement delay. A neutral turret is 130
   parts free; a neutral archon is a whole extra tiebreak rung.

**That is why this year is worth playing sealed.** The idea calls 2016 Tier 2 for *endogenous*
archetype diversity: the same rule set produced turret turtles, aggressive soldier/viper pushes and
scout zombie-pulling at the finals and none dominated. The doctrine sheet in §Decisions makes exactly
those three the `opening` values, and then makes the two axes that meta under-explored — **rubble** and
**infection** — spendable choices with teeth.

**Seats: `num_agents = 2`, always.** Slot 0 = **Clan Ash**, slot 1 = **Clan Basil**. Those two
aliases are the repo's year-neutral `AliasA`/`AliasB` (`sim_types.nim:174-175`) and this run does
**not** change them: renaming them would change what every shipped year records. The 2016 flavour is
carried by the third party instead — the zombie team is drawn and labelled **THE HORDE**, is never a
seat, never scores and is never mapped to a player name. The episode seed decides which slot takes
engine-side **A** in game 1; sides alternate every game (`sideAslotFor(seed, gameIndex)`, the shape
reused from `years/bc22/maps.nim`).

**Motive: zero-sum.** One side wins a game and the other loses it; there is no cooperative payoff and
nothing to negotiate — the cogs never exchange a byte, and the only channel between them is the
board. The two name spaces follow: in-game the factions are the anonymous aliases **Clan Ash** and
**Clan Basil**, so a doctrine cannot be written against a known opponent, and the real player names
(`daveey`, `daveey-1`) exist only in `replay.names[]` / `results.names[]` and are drawn only by the
spectator-side viewer.

### Provenance and licensing

- **`battlecode/battlecode-server-2016` — GPL-3.0** (root `COPYING`), pinned at
  `11a0b09f26a70da19f33a61ebec4ceaf6e161aa3`. The 2016 **rules** are reproduced here as an
  **independent Nim implementation written from reading that source**, not as a translation of copied
  files: no Java file is vendored, no `.class` is shipped, `src/battlecode/years/bc16/**` contains no
  Java, and the engine's own toolchain exists **only** inside the `parity-oracle-bc16` CI job. The
  derivation is disclosed file by file in `NOTICE` (§Packaging) and the pinned commit is recorded in
  `docs/RULES-BC16.md`. `years/bc16/constants.nim` is *generated* from `GameConstants.java` +
  `RobotType.java` by `tools/gen_year_constants.py --year bc16` and byte-diffed in CI, so the constant
  table is provably the engine's and provably not hand-typed.
- **`battlecode/battlecode-client-2016` — GPL-3.0** (`COPYING`), pinned at
  `317e1f3ff902ae568619c051813335ecdd72322c`. `data/atlas_bc16.png` / `.json` are cut from
  `src/main/battlecode/client/resources/art/**` by `tools/build_sprite_atlas_bc16.py` and credited in
  `NOTICE` by directory and file family. No client code is shipped, built or embedded.
- **`TheDuck314/battlecode2016` and `bshimanuki/battlecode2016` carry NO LICENCE. Neither repository
  was cloned, read, copied, vendored, compiled or translated by this run, and neither contributes a
  single line to it.** The chassis `bulwark` (§Decisions) is designed from the engine's own mechanics
  and from the three archetypes the **idea text itself** names — turret turtle, aggressive
  soldier/viper, scout zombie-pull. Where this note says "the play the 2016 meta made", that is a
  statement about the idea's own characterisation of the 2016 finals, not a claim about any
  repository's contents. `docs/RULES-BC16.md` and `NOTICE` both state this in as many words.
- **`LICENSE` of this repo is AGPL-3.0** and stays that way. The repo is public, so the source offer
  is discharged by the repository itself. AGPL-3.0 is a valid downstream licence for GPL-3.0 material
  under GPL-3.0 §13, and §Packaging records that reasoning explicitly rather than leaving it implicit.

### Constants (verbatim from the pinned engine — `common/GameConstants.java`)

Generated into `src/battlecode/years/bc16/constants.nim` by `tools/gen_year_constants.py --year bc16`,
never hand-typed, and re-generated and byte-diffed in CI (§Tests item 26).

| constant | value | constant | value |
|---|---|---|---|
| `MAP_MIN_WIDTH` / `_HEIGHT` (`:14,20`) | **30** | `MAP_MAX_WIDTH` / `_HEIGHT` (`:17,23`) | **80** |
| `GAME_DEFAULT_ROUNDS` (`:161`) | **3000** | `GAME_DEFAULT_SEED` (`:158`) | 6370 (unused: every map declares its own) |
| `NUMBER_OF_ARCHONS_MAX` (`:39`) | **4** per team | `TEAM_MEMORY_LENGTH` (`:30`) | 32 — **not ported** (single-game episodes) |
| `PARTS_INITIAL_AMOUNT` (`:56`) | **300.0** per team | `ARCHON_PART_INCOME` (`:59`) | **2.0** per team per round |
| `PART_INCOME_UNIT_PENALTY` (`:62`) | **0.01** per own robot | `DEN_PART_REWARD` (`:65`) | **200.0** |
| `RUBBLE_OBSTRUCTION_THRESH` (`:73`) | **100.0** | `RUBBLE_SLOW_THRESH` (`:76`) | **50.0** |
| `RUBBLE_CLEAR_PERCENTAGE` (`:79`) | **0.05** | `RUBBLE_CLEAR_FLAT_AMOUNT` (`:82`) | **10.0** |
| `RUBBLE_FROM_TURRET_FACTOR` (`:85`) | **1.0/3.0** | `DIAGONAL_DELAY_MULTIPLIER` (`:110`) | **1.4** |
| `GUARD_ZOMBIE_MULTIPLIER` (`:92`) | **2.0** | `GUARD_DEFENSE_THRESHOLD` (`:95`) | **10.0** |
| `GUARD_DAMAGE_REDUCTION` (`:98`) | **4.0** | `VIPER_INFECTION_DAMAGE` (`:101`) | **2.0** per turn |
| `TURRET_MINIMUM_RANGE` (`:104`) | **6** (r²) | `TURRET_TRANSFORM_DELAY` (`:107`) | **10.0** on **both** counters |
| `ARCHON_REPAIR_AMOUNT` (`:113`) | **1.0** | `ARCHON_ACTIVATION_RANGE` (`:116`) | **2** (r²) |
| `DEN_SPAWN_PROXIMITY_DAMAGE` (`:119`) | **10.0** | `OUTBREAK_TIMER` (`:122`) | **300** rounds |
| `BROADCAST_RANGE_MULTIPLIER` (`:42`) | 2 | `BROADCAST_BASE_DELAY_INCREASE` (`:45`) | **0.05** |
| `BROADCAST_ADDITIONAL_DELAY_INCREASE` (`:49`) | **0.03** | `SIGNAL_QUEUE_MAX_SIZE` (`:145`) | **1000**, FIFO, oldest dropped |
| `BASIC_SIGNALS_PER_TURN` (`:148`) | **5** | `MESSAGE_SIGNALS_PER_TURN` (`:151`) | **20** |
| `NUMBER_OF_INDICATOR_STRINGS` (`:33`) | 3 — **not ported** | `EXCEPTION_BYTECODE_PENALTY` (`:36`) | 500 — **not ported** (no JVM exceptions) |
| `ARMAGEDDON_*` (`:129-138`) | **not ported**; armageddon maps are out of scope (§Out of scope) | | |

`RobotType` — the whole table verbatim from `common/RobotType.java:18-98`, in `values()` order (the
ordinal order is load-bearing: `ZombieCount.compareTo` sorts by it and the den's spawn priority reads
it). Columns are the constructor's own parameters (`RobotType.java:261-277`).

| # | type | building | zombie | infectTurns | spawnSource | parts | buildTurns | maxHealth | attack | attack r² | moveDelay | attackDelay | cooldownDelay | sight r² | bytecodeLimit | turnsInto | ignoresRubble |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `ZOMBIEDEN` | **yes** | yes | 0 | — | 0 | 0 | **2000** | 0 | 0 | 0 | 0 | 0 | **−1 (all)** | 10 000 | — | no |
| 1 | `STANDARDZOMBIE` | no | yes | **10** | ZOMBIEDEN | 0 | 0 | **60** | **2.5** | **2** | **3** | **2** | **1** | **−1 (all)** | 10 000 | — | no |
| 2 | `RANGEDZOMBIE` | no | yes | **10** | ZOMBIEDEN | 0 | 0 | **60** | **3** | **13** | **3** | **1** | **1** | **−1 (all)** | 10 000 | — | no |
| 3 | `FASTZOMBIE` | no | yes | **10** | ZOMBIEDEN | 0 | 0 | **80** | **3** | **2** | **1.4** | **1** | **1** | **−1 (all)** | 10 000 | — | **yes** |
| 4 | `BIGZOMBIE` | no | yes | **10** | ZOMBIEDEN | 0 | 0 | **500** | **25** | **2** | **4** | **3** | **2** | **−1 (all)** | 10 000 | — | **yes** |
| 5 | `ARCHON` | no | no | 0 | **— (cannot be built)** | 0 | 0 | **1000** | **0** | **24** (repair range) | **2** | **1** | **1** | **35** | **20 000** | BIGZOMBIE | no |
| 6 | `SCOUT` | no | no | 0 | ARCHON | **25** | **20** | **80** | **0** | 0 | **1.4** | **0** | **1** | **53** | **20 000** | FASTZOMBIE | **yes** |
| 7 | `SOLDIER` | no | no | 0 | ARCHON | **30** | **12** | **60** | **4** | **13** | **2** | **2** | **1** | **24** | 10 000 | STANDARDZOMBIE | no |
| 8 | `GUARD` | no | no | 0 | ARCHON | **30** | **10** | **145** | **1.5** | **2** | **2** | **1** | **1** | **24** | 10 000 | STANDARDZOMBIE | no |
| 9 | `VIPER` | no | no | **20** | ARCHON | **120** | **30** | **120** | **2** | **20** | **2** | **3** | **1** | **24** | 10 000 | RANGEDZOMBIE | no |
| 10 | `TURRET` | no | no | 0 | ARCHON | **130** | **25** | **100** | **13** | **40** (min **6**) | **0 (immobile)** | **3** | **3** | **24** | 10 000 | RANGEDZOMBIE | no |
| 11 | `TTM` | no | no | 0 | **TURRET** | **130** | **10** | **100** | **0** | 0 | **2** | **0** | **2** | **24** | 10 000 | RANGEDZOMBIE | no |

Derived predicates, ported exactly (`RobotType.java:192-259`): `canAttack()` = `attackPower > 0` (so
ARCHON, SCOUT, TTM and ZOMBIEDEN **cannot attack**); `canInfect()` = `infectTurns > 0` (VIPER and all
four zombies); `isInfectable()` = `!isZombie && this != ZOMBIEDEN` (**every player unit, archons
included**); `canMove()` = `this != ZOMBIEDEN && this != TURRET`; `canBuild()` = `ARCHON || ZOMBIEDEN`;
`canMessageSignal()` = `ARCHON || SCOUT`; `isBuildable()` = `spawnSource == ARCHON || spawnSource ==
ZOMBIEDEN` (**note: TTM's spawnSource is TURRET, so a TTM is NOT buildable and can only be reached by
packing**); `canClearRubble()` = `this != TURRET && this != TTM`.

**Outbreak multiplier** (`RobotType.java:304-320`), applied to a **zombie's** `maxHealth` and
`attackPower` **at the moment it spawns** and never afterwards (`InternalRobot.java:68,70`):
`level = round / 300` (integer), then

| level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ≥10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| multiplier | 1.00 | 1.10 | 1.20 | 1.30 | 1.50 | 1.70 | 2.00 | 2.30 | 2.60 | 3.00 | `3.00 + (level − 9)` |

In a 3000-round game `level` reaches **10** (rounds 3000/300 — the last round is index 2999, so
level 9 is the last one actually reached by a spawn; level 10 is unreachable and the port tables it
anyway). **Player units never scale** — `attackPower(round)` returns the base for non-zombies
(`:352-358`).

### The 2016 rule set — exact numbered resolution rules

The sim's own step list. Re-ordering any of it is a rules change and bumps `GameVersion`. It mirrors
`GameWorld.runRound` (`:144-197`) / `processBeginningOfRound` (`:582-589`) /
`processEndOfRound` (`:615-685`) exactly.

1. **Beginning of round.** (a) `currentRound += 1`. **`currentRound` is initialised to −1**
   (`GameWorld.java:69`), so the first round played is round **0** and the last is round **2999**;
   every round number in this note, in the trace, in the replay and on the viewer clock is
   **0-based**, exactly as the engine's is. (b) The engine then calls `processBeginningOfRound` on
   every robot in insertion order, and `InternalRobot.processBeginningOfRound` (`:431-432`) has an
   **empty body** — a genuine no-op with no observable effect, recorded here so nobody looks for the
   missing code (D1). (c) `controlProvider.roundStarted()` is empty in both providers
   (`ZombieControlProvider.java:97`, `PlayerControlProvider.java:238`) — a second no-op.
2. **Turn order.** Iterate a **snapshot** of `gameObjectsByID.keySet()` taken before the sweep
   (`GameWorld.java:158-160`). `gameObjectsByID` is a **`LinkedHashMap`** (`:72`), so the order is
   **insertion order**: the map file's `initialRobots` in **file order** first, then every spawn in
   spawn order, with removal on death leaving the survivors' relative order intact. A robot built
   this round takes **no** turn this round; a robot destroyed mid-sweep is skipped by the
   `robot == null` guard (`:164-167`). **The initial robots are NOT sorted by id** (unlike 2022) —
   ids come from `IDGenerator` and are shuffled, while the *order* is the file's. Measured: every
   official map file lists its `initial-robot` rows sorted ascending by `(originOffsetX,
   originOffsetY)`, so that is the opening turn order.
3. **Each robot's turn**, in four parts (`GameWorld.java:169-181`):
   1. **`processBeginningOfTurn`** (`InternalRobot.java:434-441`): `decrementDelays()`;
      `repairCount = 0`; `basicSignalCount = 0`; `messageSignalCount = 0`; the bytecode limit is
      reset (in this port, the `DecisionOps` budget is reset — §Sim module).
      **`decrementDelays()`** (`:323-337`) subtracts `amountToDecrement` from **both**
      `weaponDelay` and `coreDelay` and floors each at 0.0. The engine's expression is
      `1.0 − 0.3 × ((max(0.0, 8000 − currentBytecodeLimit + prevBytecodesUsed) / 8000.0) ^ 1.5)`.
      **This port pins `amountToDecrement = 1.0`** — the value the engine itself produces whenever
      `prevBytecodesUsed <= bytecodeLimit − 8000` (i.e. ≤ 2000 for a 10 000-limit unit, ≤ 12 000 for
      an archon or scout). It is bc16's headline **decided divergence**, argued in §Sim module, tabled
      in `data/bc16/tables.json` over its whole finite domain and gated by Tier B′.
   2. **Run the controller.** A player robot runs its team's chassis under that team's doctrine,
      spending at most its `DecisionOps` budget. A **zombie or den** runs the engine's own
      `ZombieControlProvider` logic, ported verbatim (rule 5 below) — it is part of the sim, not a
      chassis, and costs nothing against any budget.
      **A robot that is still being built cannot act.** `isActive()` (`InternalRobot.java:179-181`) is
      `!type.isBuildable() || roundsAlive >= buildDelay`, `canExecuteCode()` (`:183-187`) adds
      `health > 0`, and `getBytecodeLimit()` (`:197-199`) returns **0** when
      `!canExecuteCode()` — so a SOLDIER built this round is a live, targetable, blocking, damageable
      robot that **does nothing for 12 turns**. In this port a robot with `!isActive()` gets a
      `DecisionOps` budget of **0** and its controller is not run. A VIPER is inert for **30** turns,
      a TURRET for **25**, a SCOUT for **20**.
      **Readiness.** `isCoreReady()` = `coreDelay < 1` (`RobotControllerImpl.java:416-418`);
      `isWeaponReady()` = `weaponDelay < 1` (`:421-423`). Both are strict `< 1` on a **float64**.
      The legal actions, with their exact preconditions and effects, **in the engine's own order of
      definition**:
      | # | action (`RobotControllerImpl.java`) | who | preconditions | effect, in this order |
      |---|---|---|---|---|
      | 1 | `clearRubble(dir)` (`:439-466`) | `canClearRubble()` — **not TURRET, not TTM** | core ready; `dir` not `OMNI`/`NONE`; adjacent target **on the map**; **rubble exactly 0 → returns silently and costs NOTHING** (`:459-461`) | `rubble = max(0.0, r × (1 − 0.05) − 10.0)` (`GameWorld.java:846-855`); **then** `setWeaponDelayUpTo(cooldownDelay)`, `coreDelay += movementDelay` (`InternalRobot.java:378-384`). A SCOUT clears at movementDelay **1.4** — the cheapest digger |
      | 2 | `move(dir)` (`:516-538`) | `canMove()` — **not ZOMBIEDEN, not TURRET** | core ready; `dir` not `NONE`/`OMNI`; destination **pathable** = `onTheMap && (rubble < 100.0 \|\| ignoresRubble) && unoccupied` (`GameWorld.java:330-334`) | `factor1 = 1.4` if diagonal else 1.0; `factor3 = 2.0` if `!ignoresRubble && rubble(dest) >= 50.0` else 1.0; the robot **moves** (`:962-973`) and **if it is an ARCHON takes every part on the destination**; `setWeaponDelayUpTo(cooldownDelay × factor3)`; `coreDelay += movementDelay × factor1 × factor3`. **The diagonal multiplier hits the CORE delay ONLY** — a soldier stepping diagonally onto rubble 60 pays core **5.6** and weapon **2.0** |
      | 3 | `attackLocation(loc)` (`:559-584`) | `canAttack()` — SOLDIER, GUARD, VIPER, TURRET, all four zombies | weapon ready; `d² <= attackRadiusSquared`, **and `d² >= 6` for a TURRET** (`GameWorld.java:340-348`). **No vision test, no on-the-map test, no target-exists test** | `visitAttackSignal` (`:745-796`) **first**, then `weaponDelay += attackDelay`, `setCoreDelayUpTo(cooldownDelay)` (`InternalRobot.java:386-392`). The signal collects `getAllRobotsWithinRadiusSq(loc, 0)` — **splash radius ZERO**, so exactly the one robot on that square or none — and: GUARD attacker vs zombie → `rate = 2.0`; attacker `canInfect()` and target `isInfectable()` → **infected**; `damage = attackPower × rate`, and **a GUARD target hit for more than 10.0 takes `damage − 4.0`**; a **ZOMBIEDEN** brought to `<= 0` pays the attacker's team **200 parts**. **No team check exists on this path: friendly fire is legal.** An attack on an empty square is legal, hits nothing and costs full delay |
      | 4 | `broadcastSignal(r²)` (`:600-612`) / `broadcastMessageSignal(m1, m2, r²)` (`:615-634`) | any robot / **ARCHON and SCOUT only** | `r² >= 0`; `basicSignalCount < 5` / `messageSignalCount < 20` | every robot **of any team** within `r²` **except the sender** receives it into a FIFO queue capped at **1000, oldest dropped** (`InternalRobot.java:343-348`); then `x = r² / (double) sensorRadiusSquared − 2` and `0.05 + 0.03 × max(0.0, x)` is **added to BOTH** counters (`GameWorld.java:798-822`). A broadcast inside twice your own sight radius costs a flat **0.05**, and **the enemy hears every one** |
      | 5 | `build(dir, type)` (`:670-712`) | ARCHON or ZOMBIEDEN | builder `canBuild()`; `type.isBuildable()`; `type.spawnSource == builder type`; core ready; `partCost <= team parts`; **for an ARCHON only**, the square is pathable for the new type — a **ZOMBIEDEN skips pathability** (`:702-704`) and its `canBuild` is only `isEmpty(loc)` (`:662-664`), so a den spawns onto rubble ≥ 100 no player unit could stand on | `visitBuildSignal` (`:824-839`) deducts `partCost` and spawns with `buildDelay = buildTurns`; **then** `setWeaponDelayUpTo(buildTurns)`, `coreDelay += buildTurns`. An archon building a VIPER is **frozen 30 of its own turns**, a GUARD 10. The new robot spawns at full `maxHealth(currentRound)`, both delays 0, `roundsAlive = 0`, inert until `roundsAlive >= buildTurns` |
      | 6 | `activate(loc)` (`:718-747`) | **ARCHON only** | `d² <= 2`; a robot is there; its team is **`NEUTRAL`**; core ready | `visitActivationSignal` (`:728-742`) kills the neutral with cause **`ACTIVATION`**, which **skips the rubble deposit and the infection→zombie conversion** (`:869,890`), and spawns the **same type** on the activator's team with `buildDelay 0` — immediately active. Cost: `setWeaponDelayUpTo(0)` and `coreDelay += 2`. **A free unit for two core delay** |
      | 7 | `repair(loc)` (`:750-783`) | **ARCHON only** | `canAttackSquare(self, loc)`, i.e. **r² ≤ 24**; a robot is there; **your** team; **not an ARCHON**; `repairCount < 1` | `changeHealthLevel(+1.0, ARCHON)` capped at max (`InternalRobot.java:420-424`). **Costs NO delay of either kind** — it never goes through `activateCoreAction`. Every archon heals 1 HP somewhere in r² ≤ 24 every turn for free, and **that is the only healing in the game** |
      | 8 | `pack()` / `unpack()` (`:786-803`) | exactly `TURRET` / exactly `TTM` | **no readiness check at all** | `transform` (`:403-411`) swaps the type and adds **`TURRET_TRANSFORM_DELAY = 10.0` to BOTH counters**, and adjusts the per-type counts. `partCost` is not charged again |
      | 9 | `disintegrate()` (`:806-808`) | any robot | — | throws `RobotDeathException`; the sandbox terminates and `runRound` (`:178-181`) calls `suicide()` **after** `processEndOfTurn` as an ordinary `DeathSignal` — so a robot that disintegrates **while infected still becomes an enemy zombie**, and leaves rubble otherwise |
      | 10 | `resign()` (`:811-817`) | any robot | — | kills every robot of the resigner's team. **Unreachable here** — a doctrine is a JSON sheet and neither chassis calls it; recorded as *unreachable in this coworld*, not *absent upstream* |
      | 11 | sensing (free against `DecisionOps` only) | any robot | — | `canSense(loc)` is `sensorRadiusSquared == -1 \|\| d² <= sensorRadiusSquared` (`InternalRobot.java:217-222`) — **every zombie and every den senses the entire map, always**. `senseRubble`/`senseParts` return **−1** out of range rather than throwing (`:228-247`). `senseNearbyRobots` (`:322-352`) and `senseHostileRobots` (`:372-400`, which keeps the enemy team **and Team.ZOMBIE**) iterate `allObjects()` — the `LinkedHashMap` — and **return in INSERTION order**, which is what fixes which enemy a chassis sees first. `sensePartLocations` (`:250-265`) walks `MapLocation.getAllMapLocationsWithinRadiusSq(loc, min(r², sensorR²))`, whose scan order is **x ascending outer, y ascending inner** over the `(int) Math.sqrt(r²)` box, keeping `d² <= r²` (`MapLocation.java:255-278`), and **throws for `r² > 100` or `r² < 0`** — so a zombie may not call it and never does. `getInitialArchonLocations(t)` (`:101-118`) returns that team's initial ARCHON squares **sorted by `compareTo`** and is public from round 0; `getZombieSpawnSchedule()` (`:90-93`) returns the **whole-map** schedule (not the per-den split) and is free and public |
   3. **`setBytecodesUsed`** (`GameWorld.java:171`) — records the turn's cost. In this port it records
      `DecisionOps` used, for telemetry and the `#bc16-*` readouts only; **no rule reads it** (the
      delay-decay divergence).
   4. **`processEndOfTurn`**, and **only if `health > 0`** (`GameWorld.java:173-175`;
      `InternalRobot.java:443-457`): `prevBytecodesUsed = bytecodesUsed`; `roundsAlive += 1`; then
      **`processBeingInfected()`** (`:248-256`) — if `viperInfectedTurns > 0`, take **2.0** damage
      (which can kill, and then the robot **is** infected, so it becomes a zombie) and decrement it;
      if `zombieInfectedTurns > 0`, decrement it. **The two counters are independent and
      `isInfected()` is the OR of them.** Finally, if the controller terminated (disintegrate), the
      robot suicides.
4. **End of round** (`GameWorld.processEndOfRound`, `:615-685`), in exactly this order:
   1. Every robot's `processEndOfRound` — **empty** in 2016 (`InternalRobot.java:459`), a genuine
      no-op (D1).
   2. **Parts income**: team A's stockpile `+= max(0.0, 2.0 − 0.01 × getRobotCount(A))`, then team
      B's the same (`:622-627`). `getRobotCount` is that team's **total live robot count**, so income
      falls linearly with army size and **reaches exactly zero at 200 robots**. This is the whole
      economy alongside map parts and den bounties, and it is why a 2016 army has a natural ceiling.
   3. **The end-of-match check**, if `timeLimitReached()` **and** no winner is set yet.
      `timeLimitReached()` (`:606-608`) is `currentRound >= gameMap.getRounds() − 1`, and every
      official map declares `rounds = 3000`, so it fires at the end of round **2999**. The ladder,
      first non-zero difference wins (`:634-679`):
      | rung | difference computed | `DominationFactor` | our `end_reason` |
      |---|---|---|---|
      | 1 | `count(A, ARCHON) − count(B, ARCHON)` | `PWNED` | `more_archons` |
      | 2 | `Σ health of A's live ARCHONs − Σ health of B's` | `OWNED` | `more_archon_health` |
      | 3 | `(parts(A) − parts(B)) + Σ partCost over A's live robots − Σ over B's` | `BARELY_BEAT` | `more_parts_net_worth` |
      | 4 | `max live A archon id > max live B archon id` → A else **B** | `WON_BY_DUBIOUS_REASONS` | `highest_id` |
      Three details ported literally: rung 3's accumulator is **seeded with the parts difference and
      then walks every live robot of either team adding/subtracting `partCost`** in one pass
      (`:641-665`), so it includes zombies' and neutrals' cost — which is **0** for a den and a
      zombie and non-zero for a NEUTRAL soldier/guard/scout/viper/turret, and neutrals belong to
      neither team so they contribute nothing; rung 4 compares `highestAArchonID` and
      `highestBArchonID` which are **0** if that team has no archon, and **the `else` branch awards B**
      — so a 0-vs-0 tie (both teams archon-less, reachable only if both were annihilated in the same
      round) goes to **B**; and rungs 1–3 are exact `!= 0` float64 tests.
   4. If `winner != null` → `running = false` (`:682-684`).
5. **The zombie AI, ported verbatim** (`world/control/ZombieControlProvider.java`). It is *the sim*,
   and it is the half of this year a doctrine has to plan around, so it is specified action for
   action.
   1. **A den's turn** (`processZombieDen`, `:140-176`). (a) Add this round's counts from **this den's
      own** schedule (`getZombieSpawnSchedule(den.getLocation())` — the per-den split, rule 6) into
      the den's persistent queue. (b) `spawnAllPossible`. (c) If **any** type is still queued, damage
      **every non-zombie robot** on the eight adjacent squares for
      **`DEN_SPAWN_PROXIMITY_DAMAGE = 10.0`** (`:166-171`), then call `spawnAllPossible` **again**.
   2. **`spawnAllPossible`** (`:184-218`): let `start = getSpawnDirection(denLoc)`,
      `chir = getSpawnChirality(denLoc)`; for `dirOffset` 0…7 take
      `DIRECTIONS[floorMod(start + dirOffset × chir, 8)]` where `DIRECTIONS` is
      **N, NE, E, SE, S, SW, W, NW** (`:28-37`); pick the next type as **the LAST type in
      `{STANDARDZOMBIE, RANGEDZOMBIE, FASTZOMBIE, BIGZOMBIE}` order with a non-zero count**
      (`:197-202` — the loop has **no `break`**, so the priority is effectively **BIGZOMBIE, then
      FASTZOMBIE, then RANGEDZOMBIE, then STANDARDZOMBIE**); if none, stop; if `canBuild(dir, next)`
      (for a den: on the map and unoccupied), build it and decrement. **So a den spawns at most 8 per
      call and at most 16 per round.**
   3. **`getSpawnDirection`** (`:313-342`, memoised per location): the direction from the den to the
      **closest INITIAL ARCHON of either team** — `min` by `distanceSquaredTo` over
      `getInitialRobots()` filtered to `ARCHON`, **taking the first minimum in file order**
      (`Stream.min` keeps the earlier element on a tie) — then
      `DIRECTIONS.indexOf(denLoc.directionTo(closest))`, where `directionTo` is the 2.414 threshold
      form (`MapLocation.java:146-183`). An index of −1 makes the engine throw, which is why the port
      asserts it at map conversion time.
   4. **`getSpawnChirality`** (`:350-385`, memoised): **1** if the symmetry is `ROTATIONAL` or `NONE`;
      otherwise `signum(denLoc.compareTo(symmetry.getOpposite(denLoc, w, h, origin)))`, and **1** if
      that is 0 (a den on the line of symmetry). `compareTo` is x-then-y and translation-invariant, so
      the origin does not matter (V3). **This is what makes the two sides' dens spawn mirror-image
      rings** on reflected maps.
   5. **A zombie's turn** (`processZombie`, `:220-300`), with every early return in place:
      (a) `closest = getNearestPlayerControlled(myLoc)`; (b) if `closest != null` **and**
      `canAttackLocation(closest.location)`: if `isWeaponReady()` attack it — **and return either
      way**; (c) if `!isCoreReady()` → return; (d) if `closest != null`:
      `preferred = directionTo(closest.location)`, and if `canMove(preferred)` → move and return;
      **else** `preferred = DIRECTIONS[random.nextInt(8)]`; (e) `newLeft = random.nextBoolean()`;
      `next = newLeft ? rotateLeft() : rotateRight()`; if `canMove(next)` → move and return;
      (f) `final = newLeft ? rotateRight() : rotateLeft()`; if `canMove(final)` → move and return;
      (g) if the `preferred` square is **unoccupied, on the map and rubble >= 100** →
      `clearRubble(preferred)` and return; (h) if that square **is** occupied by a `NEUTRAL` and the
      weapon is ready → attack it. **A FASTZOMBIE or BIGZOMBIE ignores rubble and never reaches (g);
      a STANDARDZOMBIE or RANGEDZOMBIE digs.** Step (h) is why zombies eat the neutrals a faction did
      not activate in time.
   6. **`getNearestPlayerControlled`** (`GameWorld.java:418-440`): walk `gameObjectsByID.values()` in
      **insertion order**, keep only `team.isPlayer()` (A or B — **never NEUTRAL, never ZOMBIE**),
      track the minimum `d²`, **collect every location at that minimum**, then return the robot at
      `closest.get(rand.nextInt(closest.size()))` — **one draw from `GameWorld.rand` on EVERY call,
      including when there is exactly one candidate**, because `java.util.Random.nextInt(1)` still
      consumes a `next(31)`. Returns `null` only if **neither** faction has a live robot.
6. **The per-den schedule split** (`GameMap.buildZombieSpawnMap`, `:718-793`), resolved at **map
   conversion time** and shipped in the converted map file (D3). (a) Build `byLoc`, a
   `HashMap<MapLocation, InitialRobotInfo>` over the initial robots **at zero origin**, via
   `Collectors.toMap` (insertion order = file order). (b) Walk **`byLoc.keySet()`** — a
   `java.util.HashMap` iteration, the **one** hash-order dependency in the whole 2016 round loop — and
   for each ZOMBIEDEN append its location and then, immediately after it, its symmetric opposite if
   `oppositeRobots` holds for the pair. That gives `denLocs` in **pair order**. (c) For every
   scheduled round in ascending order and every `ZombieCount` in **type-ordinal order**, give each den
   `count / numberDens` and then walk a **persistent cursor** `currentIndex` around `denLocs` handing
   out the `count % numberDens` leftovers one at a time. The cursor **survives across types and
   across rounds**.
7. **The rubble deposit on death** (`GameWorld.visitDeathSignal`, `:857-903`), in exactly this order:
   (a) if the dead robot is a player-team **ARCHON** and that team now has **0** archons and no winner
   is set → `setWinner(opponent, DESTROYED)` — **mid-turn**, while `running` stays true, so the rest
   of the round plays out; (b) if the death cause is **not** `ACTIVATION` **and** the robot is **not
   infected** → `rubble(loc) += rubbleFactor × maxHealth`, where `rubbleFactor` is `1.0` normally and
   **`1.0/3.0` when the killing blow came from a TURRET** (`DeathSignal.RobotDeathCause.TURRET`, set
   in `InternalRobot.changeHealthLevel:286-288`); (c) remove the robot from `gameObjectsByID` and
   `gameObjectsByLoc`; (d) if the robot **was infected** and the cause is not `ACTIVATION` → spawn
   `type.turnsInto` on **`Team.ZOMBIE`** at the same square, with `maxHealth(currentRound)` — i.e.
   **outbreak-scaled at the round it turns, not the round it was built**.
   **`visitDeathSignal` returns immediately if `!running`** (`:861-867`), so once a winner has been
   set and the round has ended, deaths stop being processed.

**Five subtleties the port reproduces literally, each with its own test:**

- **`DESTROYED` fires mid-turn and does not stop the round.** Every robot after the killer in the
  exec order still takes its turn and every action is recorded (`tests/test_bc16_endladder.nim`).
- **Both factions can be annihilated in the same round.** The second `setWinner` is guarded by
  `winner == null` (`:882`), so **the first faction to lose its last archon loses** and the other
  wins even if it dies later in the same round. Ordering follows the exec order.
- **`changeHealthLevel` is the single mutation point for health** (`:278-293`): it caps at
  `maxHealth`, and at `<= 0` it calls `visitDeathSignal` — from inside an attack, a repair, viper
  infection and den-proximity damage. The port keeps one such proc with the same three
  responsibilities and the same `source == TURRET` flag rather than four copies.
- **An infected robot leaves no rubble.** The two effects are exclusive: you either get a wall or you
  get an enemy zombie, never both. That single `if` (`:869`) is the reason `infection_policy` is a
  real knob.
- **Parts on a square are all-or-nothing and archon-only.** `takeParts` (`GameWorld.java:533-539`)
  zeroes the square and returns the whole amount, and it is called from exactly two places: an
  archon **spawning** on a parts square (`:1007-1013`) and an archon **moving** onto one (`:963-969`).
  Measured: the played pool's per-square amounts run from 5 to **300** (`turtle` puts its whole
  1800 parts on **six** squares), so an archon walk is a strategic decision, not housekeeping.

**Deliberate non-rules, verified absent from the 2016 engine and therefore absent here:** there is no
terrain but rubble (no walls, no water, no elevation — a square is passable iff its rubble is under
100); rubble is never created except by corpses and never destroyed except by `clearRubble`; parts are
never created after round 0 except by den bounties and never regenerate; there is no unit cap other
than the income penalty; **there is no per-turn upkeep and no supply** (the `bytecodeLimit` comment
about "halved if the robot does not have sufficient supply upkeep" is a leftover from 2015 and no
supply code exists); archons cannot be built at all; TTMs cannot be built (only packed from a
TURRET); `TEAM_MEMORY_LENGTH` cross-game memory has no meaning in a single-episode game and is not
ported; and the profiler, indicator strings, indicator dots, indicator lines,
`addMatchObservation` and the whole `serial/`+`server/proxy/` layer are instrumentation with no port.

### Decided divergences — every rule this port does NOT reproduce, with its reason

The lost spec means there is no prose to reconcile; these are places where the port deliberately
differs from the **engine**, and every one is recorded in `docs/RULES-BC16.md` §Divergences and in
`docs/PARITY.md` §bc16.

| # | Divergence | Reason |
|---|---|---|
| **V1** | **The bytecode-dependent delay decay is pinned to `amountToDecrement = 1.0`.** The engine computes `1.0 − 0.3 × (max(0, 8000 − limit + prevBytecodes)/8000)^1.5` (`InternalRobot.java:326`). | There is no JVM and no bytecode counter. Deriving the term from the chassis's own `DecisionOps` would make **the chassis's implementation a rules input** — every refactor of `bulwark` would change what a round resolves to and would have to bump `GameVersion`, which is unacceptable. `1.0` is exactly what the engine produces for any robot inside `limit − 8000` bytecodes, so the divergence is "every unit behaves like a frugal 2016 bot". The engine's whole formula is nevertheless **tabled over its complete finite domain** in `data/bc16/tables.json` and byte-diffed against the JVM (Tier B′), and `tests/table_bc16_delay.nim` pins it — so the port provably knows what it diverged from. |
| **V2** | **Bytecode metering is replaced by a fixed per-robot `DecisionOps` budget**: **2000** (ARCHON, SCOUT), **1000** (SOLDIER, GUARD, VIPER, TURRET, TTM), **0** for a robot with `!isActive()`. Zombies and dens are the sim and have no budget. | One tenth of the engine's own `bytecodeLimit`, the convention bc20–bc26 use. Enforced by the sim, checked **before** each primitive and never inside one, so a primitive's *result* is never a function of the remaining budget. When the budget reaches zero the robot's turn ends where it stands — it is **not** resumed mid-computation next turn, which is the one behavioural difference from the JVM, and V1 makes it invisible to the rules. |
| **V3** | **The map's random origin is not ported.** `GameMap`'s constructor draws `origin = (rand.nextInt(500), rand.nextInt(500))` from `new Random(seed)` (`GameMap.java:248-250`). The port uses origin `(0, 0)`. | **Proven inert.** The origin is added to every coordinate uniformly. `onTheMap` subtracts it; `distanceSquaredTo`, `directionTo`, `compareTo`-sign and every radius scan are translation-invariant; `MapLocation.hashCode` is used only for `gameObjectsByLoc` and `zombieSpawnMap` **lookups**, never iteration. The one iteration over a location-keyed `HashMap` (`buildZombieSpawnMap`) uses **zero origin** already (`:723-728`). The parity comparator subtracts the origin from the Java side so both traces are origin-free. |
| **V4** | **Armageddon is not ported.** `isArmageddon()`, the day/night cycle, zombie regeneration, `ZOMBIFIED` and `CLEANSED` are absent. | Armageddon maps have **team B with zero archons** (measured: `bbg_armageddon` is 2/0 with 104 dens, `boxy_armageddon` 2/0 with 49) and 12 000 rounds; they are a single-player survival mode, not a 2-seat match. Both are excluded from every pool and `tools/convert_maps_bc16.py` **refuses** a map with `armageddon="true"` or with unequal archon counts. |
| **V5** | **`resign()` is unreachable**, and `setTeamMemory`/`getTeamMemory`, indicator strings/dots/lines, `addMatchObservation` and `Clock.yield()` have no port. | A doctrine is a JSON sheet; none of these has any effect a spectator or a score can see. Recorded as *unreachable here*, not *absent upstream*. |
| **V6** | **The `.rms` match stream, the XStream/Jackson serial layer and the `server/proxy` writers have no port.** | The replay is this repo's own self-sufficient UTF-8 JSON re-derived by the wasm sim (§Server). No `.rms` bytes exist anywhere. |
| **V7** | **44 of the 98 official maps are not converted in v1**, and 22 are. | The converter handles any 2016 `.xml` and CI parses **all 98**; v1 commits the 22 whose geometry is pinned in §Sim module. The **whole played pool is drawn from the 54 maps the oracle jar also carries as resources**, so no parity pair needs a `--map-dir`. |
| **V8** | **`EXCEPTION_BYTECODE_PENALTY` has no port.** | A Nim chassis raises nothing. |

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The `bc16` variant is **best-of-three on three
distinct maps from the `mixed` pool, played to the engine's own 3000-round cap**.

```
container start, map load, seat connect              <=  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    <=  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 3000 rounds                         <= 360 s   (matchBudgetSeconds; each game also
                                                                capped at perGameBudgetSeconds 120)
score + replay write + shutdown grace                <=  30 s
                                                       -------
worst case                                             465 s   <= 720 s
```

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**.

**Honest per-round estimate, so the builder can check it**, derived from the engine rather than
guessed:

- **The robot census is bounded by the parts economy.** Income is `max(0, 2 − 0.01 × ownRobots)` per
  team per round — **zero at 200 robots, half at 100** — so a team's total passive income over 3000
  rounds is at most **6000 parts** (much less once it has an army), plus the map's parts (measured
  **1500–20 520** on the played pool, all archon-collected) plus **200 per den killed** (4–6 dens).
  At a 30-part soldier that is roughly **200–400 units built per team per game** with a **peak alive of
  60–130 per team**, plus the schedule's **204–378 zombies** and the infection converts.
- **So the budgeted worst case is ~300 robots on the board.** Each player turn is a sense sweep, a
  bounded navigation step and one action; the sweep is the engine's own shape and is **O(n)** for
  `r² >= 16` (`GameWorld.java:398-408` walks every robot) and a box scan below, and each zombie's
  `getNearestPlayerControlled` is another **O(n)** — ~9 × 10⁴ distance tests a round at n = 300, **well
  under a millisecond** in release Nim. The expensive term is the chassis's pathfinding, charged **1
  `DecisionOps` per node expanded** and hard-capped at `300 × 2000 = 6 × 10⁵` ops a round.
- **Estimate: 2–5 ms/round, i.e. 6–15 s per 3000-round game in release Nim** — bc23's class (measured
  1.45–2.95 ms/round at 207–451 robots) scaled by 1.5× the rounds. Best of three is **18–45 s**,
  comfortably inside `matchBudgetSeconds 360`. Both budgets are hard monotonic-clock guards sampled
  every 32 rounds; a game that blows one is **abandoned**, the finished games are scored, and
  `results.reason = deadline`.
- **`tests/test_bc16_perf.nim` plays a full 3000-round game on `6147`** (45×45 = 2025 squares, the
  largest map in the played pool, 2 archons a side at rubble mean 532.6 with 18 neutrals — i.e. the
  most squares and the most units) with **both seats on `opening: soldier_viper_aggro`,
  `turret_count: 0`, `guard_ratio: 0`, `rubble_clear: aggressive`, `retreat_hp: 0`** — the
  configuration that maximises unit count, movement and rubble work — and **fails CI above 130 s**.
- **If that gate ever goes red the fix is one config value** — `gamesPerMatch: 3 → 2` in the `bc16`
  variant, then `→ 1` — and the note says so here so the builder does not redesign anything.
- Best-of-three is chosen over best-of-one because bc16's axis is **map-shaped**: the same doctrine
  pays very differently on `quadrants` (20 520 parts over 684 squares — an archon-walking economy
  where turrets are cheap) than on `turtle` (1800 parts on **6** squares and only **2** dens — a
  two-point map where whoever holds the piles wins) than on `caverns` (**1078 of 1892 squares already
  impassable** — a corridor game where a single turret closes a map). The `mixed` pool spans that axis
  deliberately (§Sim module, Maps). One map would rank the map, not the doctrine.
- **Because this sim is heavy (well above 1 ms/round) and 3000 rounds long — the longest recording in
  this repo — the phase-60 viewer check 8 is dispatched with `settle=20000 soak=15`** and `ci.yml`'s
  `wasm-viewer` job runs the bc16 replay at `--timeout 120 --soak 15` (§Viewer, the bc21 lesson).
  `docker-smoke` prints `sim_seconds / rounds` and `docs/RULES-BC16.md` records the measured value so
  the next year module can size its own probe from a number instead of a guess.

### Scoring, sign, and what the bc16 league ranks by

The 2016 game is win/lose; it has no point formula. This one is defined here, and it is a continuous
reading of the engine's own tiebreak ladder so that the score and the winner never tell different
stories:

```
share(x, y)   = if x + y == 0: 0.5'f32 else: f32(x) / f32(x + y)
archons[t]    = ARCHONs of t ALIVE at the final round                              # rung 1
archonHp[t]   = int(10.0 * sum of health over t's live ARCHONs)   # TENTHS         # rung 2
partsWorth[t] = int(parts(t)) + sum(partCost) over t's live robots                 # rung 3
points[t]     = int(64.0'f32 * share(archons[t],    archons[o])
                  + 24.0'f32 * share(archonHp[t],   archonHp[o])
                  + 12.0'f32 * share(partsWorth[t], partsWorth[o]))   # TRUNCATION, not rounding
```

Six load-bearing details, each pinned by a test vector in `tests/test_bc16_scoring.nim`:

- The three terms are **exactly the engine's three deciding rungs, in the engine's own priority
  order**, so a doctrine that wins the game usually wins the shape of it too.
- Rungs 2 and 3 are float64 in the engine and are **narrowed to integers here** — archon health to
  **tenths**, parts worth to a truncated integer — before any share is taken, and every share is then
  narrowed through **float32** with the weighted sum **truncated** by the `int()` cast. That is
  deliberate: `points` must be reproducible bit-for-bit between the native recorder and the wasm
  re-deriver, and a float64 sum reduced in a different order would not be. **The `end_reason` is NOT
  computed this way**: the ladder uses the engine's exact float64 differences (rule 4.3), so a
  razor-thin margin can decide the *winner* on a difference that rounds away in *points*. Stated
  explicitly, tested explicitly, and not a bug.
- The weights are **super-increasing** (`24 > 12` and `64 > 24 + 12`), so a *decisive* margin on a
  higher rung dominates everything below it. **This note claims no more than that.** A one-unit margin
  on a rung with large totals gives an arbitrarily small advantage (4 vs 3 archons is
  `4/7 − 3/7 = 0.143`, i.e. 9.1 points against 36 available below), so **`points` alone can favour the
  loser**; it measures the *shape* of the game, not who won it.
- `share` returns **0.5 on a 0–0 total** (the bc22–bc25 choice): two factions that both ended with no
  archons should not be separated by an arithmetic accident, and on this year's evidence a double
  annihilation by the horde is a real outcome. `points` is in `[0, 100]` and the seats sum to ≤ 100.

```
results.scores[t] = 200.0 * (games t won) + mean(points[t] over games played)
```

**Higher is better.** bc16 joins `winBonusFor`'s **200** set (`match.nim:520`) and for the same
reason bc22 did: `points` can legitimately favour the loser, so only a bonus that dominates the whole
`[0, 100]` range keeps the ordering of `results.scores` **provably** in agreement with
`results.wins`. A 2–0 gives `400 + mean` against `≤ 100`; a 2–1 gives `400 + mean` against
`200 + mean ≤ 300`. `tests/test_bc16_scoring.nim` asserts that agreement on 500 random synthetic
finals, including clinched two-game matches, and asserts the super-increasing property and the
documented `points`-disagreement case explicitly so neither is mistaken for a bug later.

**The `bc16` league ranks by ELO over match wins**, computed by the platform from the episode's
winner; `results.scores` is the per-episode number the ladder reads and its ordering agrees with
`results.wins` exactly, as above — the same shape as the seven shipped leagues. A `deadline` episode
scores the games that finished; a `fault` episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game, `results.games[].end_reason` — the engine's `DominationFactor` mapped to this repo's
snake_case vocabulary, plus our one wall-clock value:

| `end_reason` | engine origin | meaning | can fire early? | new to the manifest enum? |
|---|---|---|---|---|
| `archons_destroyed` | `DESTROYED` (`GameWorld.java:882-884`) | a faction's **last ARCHON** died; fires the instant it dies, mid-turn | **yes** — the normal way a bc16 game ends | **NEW** |
| `more_archons` | `PWNED` (`:636-639`) | round 2999 reached; more archons alive | no | reuses bc22's value (identical meaning) |
| `more_archon_health` | `OWNED` (`:668`) | archons tied; greater total live-archon health | no | **NEW** |
| `more_parts_net_worth` | `BARELY_BEAT` (`:669-670`) | health tied; greater `parts + Σ partCost` | no | **NEW** |
| `highest_id` | `WON_BY_DUBIOUS_REASONS` (`:672-677`) | everything tied; higher maximum live archon id, **B on a 0–0** | no | reuses bc20's value (identical meaning) |
| `abandoned` | — | our `perGameBudgetSeconds` / `matchBudgetSeconds` guard fired; the game is discarded | — | already present |

**`zombified` and `cleansed` are NOT added**: `ZOMBIFIED` and `CLEANSED` are reachable only on
armageddon maps (`:882-891`), which are out of scope (V4). **`annihilated` is deliberately not
reused** for `DESTROYED` even though the semantics match bc21's and bc22's, because
`docs/RULES-BC2x.md` already documents `annihilated` as *those* years' factor and a bc16 replay must
trace to `DESTROYED`; the two reuses above are taken only where the engine's own words are the same.

Per episode, `results.reason` — the closed enum the platform reads, **unchanged from the seven shipped
years**:

| `results.reason` | when | scores |
|---|---|---|
| `complete` | a side won 2 games, or all scheduled games finished | as above |
| `deadline` | the wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if none finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped (a spend that would take a stockpile negative, a robot spawned onto an occupied square, or the port's own state-hash invariant): a partial replay and `[0, 0]` are still written | `[0, 0]` |

**Best-of-N clinch semantics, stated because phase 60 has judged this wrong before (2026-09-07):** a
side that takes 2 games settles the episode immediately. An episode that records **two** games with
`reason: complete` on a `gamesPerMatch: 3` variant is **correct**, not truncated; `results.games`
carries only the games actually played, and `replay.plan.maps` carries all three drawn maps so a
spectator can see what the third would have been.

`deadline` is **declared acceptable** for this coworld at phase-60 check 4 (it already is, for the
seven shipped years). Container exit codes are unchanged: `0` whenever results + replay were
attempted (including `deadline`/`fault`), `2` on an invalid config. `/healthz` and `/global` keep
answering for the ~20 s shutdown grace, and the websocket handler keeps its `Ping → Pong` **payload
echo** and does not filter binary frames (`tools/ci/cert_probe.py` proves both against the real
image).

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** Unchanged from the shipped years: the player container is a thin
registrar and every decision is taken inside the **game** container, because that is the only
container the platform injects the `anthropic_api_key` coworld secret into
(`game.runnable.env.ANTHROPIC_API_KEY_URI = secret://coworld/battlecode/anthropic_api_key`,
`coworld_manifest_template.json`).

**One decision turn, one parallel batch.** Both seats are asked at the same moment and their two
provider calls go out as **ONE parallel batch** (`curly.makeRequests`, `decide.nim`'s existing shape)
with the same deadline; seats are **never** queried one after another. The batch's wall-clock budget
is `doctrineBudgetMs = 45 000` — attempt 1 `attempt1Ms = 20 000`, the single retry
`retryMs = 12 000` — which is the per-turn budget for this game and sits inside the 720 s envelope
computed in §The game. At most **2 provider calls per seat per episode**.

`src/battlecode/llm.nim` is unchanged and year-neutral: the credential ladder (Bedrock sidecar →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the single Bedrock candidate
`us.anthropic.claude-haiku-4-5-20251001-v1:0`, fence-tolerant JSON extraction, the `throttled`
fast-fail, rune-boundary truncation, `maxOutputTokens = 1200`. With no credentials the client
disables itself at construction and every seat falls back instantly, which is what lets offline
certification and `docker-smoke` finish in seconds.

### The envelope pin — already fixed year-neutrally, and what bc16 must still do

The bc23 league failure (LEARNINGS 2026-09-08: champions wrapping the sheet in
`{"protocol":…,"doctrine":{…}}`, all knobs landing in `sheet_unknown_fields`, the seat playing the
schema-default sheet with `defaults_applied == []`, in 2 of the first 3 rounds) was fixed
year-neutrally by the bc22 run and is **already on `main`**: `sheet.nim:96-155` resolves the sheet
node in the order `""` (the payload carries a known knob key) → `"sheet"` → `"doctrine"` → the single
object-valued key, unwraps **at most once**, and records which rule fired in `Sheet.envelope`
(`sheet.nim:59-65`), which `replay.nim` writes as `seats[].sheet_envelope` and `results.nim` as the
top-level `sheet_envelope`. **bc16 changes none of that.** Its three obligations are:

1. **A `YearBc16` arm** in `knownKeysFor`, `defaultSheet`, `validate`'s `case`, `toJson` and
   `plainWords` — the four-line shape bc21–bc25 added.
2. **Absent-key defaulting counted, in `years/bc16/knobs.nim` only.** `applyKnobs16` adds an
   **absent** known key to `defaultsApplied` as well as a repaired one, exactly as
   `years/bc22/knobs.nim:171-176` does, so `sheet_defaults_applied` for a bc16 seat is `[]` only when
   the cog really set all eleven knobs. This is deliberately **not** done year-neutrally: doing so
   would change what a bc20/bc21/bc23/bc24/bc25/bc26 episode records in that array.
   `tests/test_bc16_sheet.nim` asserts a bc16 empty sheet reports all eleven names **and** that a
   bc23 empty sheet still reports none, so the change is provably scoped.
3. **The divergence is rendered.** `#bc16-doctrines` draws, per seat, the applied sheet in plain words
   **and** a badge when the two disagree: `envelope: doctrine · 11 of 11 knobs defaulted`, and the
   first 120 runes of `sheet_submitted` under a "what the cog actually sent" disclosure — the
   `renderDoctrines` shape already in the page at `client/replay_broadcast.html:5591-5630`, with bc16
   ids. A seat that played the default sheet is visible to a spectator in one glance.

### The bc16 doctrine sheet — eleven knobs, **no `chassis` key** (D1)

Each knob has a type, a range, a default, and a named site in the bc16 chassis. Unknown key, wrong
type or out-of-range value → **that field's default** (integers **clamp** instead), recorded in
`sheet_defaults_applied` / `sheet_unknown_fields`. A sheet can never be rejected, so a cog can never
forfeit a match by answering badly — only by answering weakly.

**The anti-inert rule, stated as a rule the builder must hold every knob against: no setting of any
knob, and no combination of settings, may produce an inert or self-starving faction.** The strategy
surface lives *inside one competent chassis*. Concretely, and independently of every knob, `bulwark`
always: keeps **at least one archon collecting parts** and never lets the stockpile idle above 200
without a build order; **builds an attacker (soldier or guard) whenever parts allow and the attacker
census is below its target**, and never fewer than **3 attackers per archon**; **answers any hostile
robot sensed within r² ≤ 24 of one of its own archons**; spends every archon's free repair every turn
on the weakest damaged friendly in r² ≤ 24; **never walks its last archon into a square adjacent to a
den that has zombies queued**; and **never attacks a friendly square** (friendly fire is legal in
2016 and the chassis never uses it). Every knob moves *how much of what, when* — never *whether it
plays*. `tests/test_bc16_knobs.nim` proves each knob has teeth and `tests/test_bc16_survival.nim`
proves the floor holds, **with a negative control that must fail** (§Tests items 18, 19).

| field | type / values | default | what it changes (`src/battlecode/years/bc16/chassis/…`) |
|---|---|---|---|
| `opening` | `turtle` \| `soldier_viper_aggro` \| `scout_zombie_pull` | `turtle` | `econ.nim plan()` — the parts split and the posture for the first 600 rounds, and the three archetypes the 2016 finals actually produced. **`turtle`**: hold the archons together, spend on GUARDS (145 HP, double damage to zombies) and TURRETS behind them, clear rubble into a ring, and let the horde break itself on the wall — but **soldiers are still built**, the attacker census target is halved, never zeroed. **`soldier_viper_aggro`**: build a soldier spearhead from round 0 that leaves for the nearest enemy archon, and add a VIPER per 6 soldiers once parts allow — 120 parts and 30 build turns for a unit whose real weapon is a 20-turn infection. **`scout_zombie_pull`**: commission 2 SCOUTS per archon by round 200 (25 parts, 80 HP, sight r² ≤ 53, **ignores rubble**, cannot attack) and park them so that the nearest player-controlled robot to each den is **a scout of ours standing on the enemy's side of it** — because `getNearestPlayerControlled` is the whole zombie targeting rule and a scout is the cheapest legal bait in the game. |
| `turret_count` | int **0 … 12** | 3 | `turret.nim target()` — how many TURRETs the faction wants standing. A turret is 130 parts and **25 build turns** of a frozen archon, cannot shoot inside r² 6, deals **13** damage out to r² 40 (the longest reach in the game) and must **pack** (10 delay on both counters) to move at all. At 0 the faction is all-mobile; at 12 it is a fortress that cannot chase. Clamped. Turrets are placed by `turret.nim site()` on the lowest-rubble square that covers the largest number of remembered den approach lanes without sitting inside r² 6 of an archon. |
| `guard_ratio` | int **0 … 100** | 45 | `econ.nim attackMix()` — the percentage of the **attacker** budget that goes to GUARDS rather than SOLDIERS (both 30 parts). A guard has **145 HP against a soldier's 60**, hits for **1.5 melee — 3.0 against a zombie** — and **blocks 4 damage off any hit above 10**, which is exactly the BIGZOMBIE's 25 and the TURRET's 13. A soldier hits for **4 at r² ≤ 13**. So this knob is literally "how much of my army is for the horde and how much is for the enemy", and 2016's answer depended on the map's den count. At 0 the faction is all-soldier; at 100 all-guard, and it **still builds a soldier whenever no guard is affordable**, which is the floor that keeps 100 from being inert. Clamped. |
| `zombie_kiting` | `never` \| `ranged_only` \| `always` | `ranged_only` | `micro.nim kite()` — whether a unit backs off a closing zombie instead of trading. It has teeth because the delay table is asymmetric: a STANDARDZOMBIE pays **movementDelay 3** and a BIGZOMBIE **4** while a SOLDIER pays **2** and a SCOUT **1.4**, so a soldier can outrun both and shoot from r² ≤ 13 which is outside their r² 2 reach — but a **FASTZOMBIE pays 1.4 and ignores rubble**, so it cannot be kited and must be blocked or eaten. `never`: everything trades where it stands. `ranged_only`: soldiers, vipers and turrets kite; guards do not (they are the block). `always`: guards kite too, which cedes ground and is usually wrong on a den-heavy map — and the chassis **still takes any attack that kills its target** at every setting. |
| `den_clear_round` | int **1 … 2800** | 900 | `dens.nim schedule()` — the first round at which the faction commits a strike group to killing a ZOMBIEDEN. A den is **2000 HP** and pays **200 parts** on death; killing it stops that den's share of every future wave for the rest of the game, and the schedule escalates (measured: a played-pool den holds 51–138 queued zombies across a game). But 2000 HP at a soldier's 4 damage is **500 attacks**, and a den damages every adjacent non-zombie for **10** a round whenever it has zombies queued. Early is a real investment; late is a real concession. Clamped. |
| `parts_priority` | `units` \| `turrets` \| `vipers` | `units` | `econ.nim queue()` — what the stockpile buys first when it cannot buy everything. `units`: soldiers and guards per `guard_ratio`. `turrets`: fill `turret_count` before any further attacker. `vipers`: a VIPER (120 parts, 30 turns) before the third soldier, because a viper's 20-turn infection on an enemy soldier is 40 damage **and** a RANGEDZOMBIE in their half when it dies. |
| `archon_spread` | `huddle` \| `spread` \| `split` | `spread` | `archon.nim posture()` — where the archons stand relative to each other. Archons are the only thing that decides the game, the only repair source (1 HP, free, r² ≤ 24, once a turn) and the only parts collectors. `huddle`: keep every archon inside r² ≤ 24 of another so their repair fields overlap and one wall protects all of them — and one BIGZOMBIE lane threatens all of them. `spread`: hold r² ≈ 50–100 apart, each with its own guard screen, so no single wave can reach two. `split`: send one archon away to farm the far parts squares and the far neutrals while the rest hold — which the measured maps reward hard (`quadrants` has **20 520 parts over 684 squares**; `turtle` has 1800 on **six**). |
| `neutral_activation` | `never` \| `opportunistic` \| `hunt` | `opportunistic` | `neutral.nim plan()` — whether an archon detours to activate NEUTRAL robots (r² ≤ 2, free, 2 core delay). **Measured: 80 of the 98 official maps carry neutrals; the played pool carries 0–26 each; and `industrial` and `caverns` each carry two neutral ARCHONS, which are a whole extra tiebreak rung and another repair field and another parts collector.** `never`: archons never detour, and the horde eats the neutrals (rule 5.5h). `opportunistic`: activate anything already within r² ≤ 8 of the archon's intended path. `hunt`: route archons deliberately along the neutral roster, nearest-first with **neutral ARCHONs and TURRETs first** by value, which on a 26-neutral map is worth more than the whole passive income of the first 600 rounds. |
| `retreat_hp` | int **0 … 100** | 35 | `micro.nim retreat()` — the percentage of maximum health at which a damaged unit disengages toward the nearest friendly archon (the only healing in the game, 1 HP a turn). At 0 nothing retreats; at 100 a unit withdraws on first damage. At **every** setting the chassis still takes an attack that **kills** its target and still fights when cornered against the map edge or a rubble wall, because refusing a free kill is not a strategy. The idea's `retreat_policy` is finalised as this integer knob: an enum could not express "trade until half" and the integer is clampable, so a malformed value degrades to a number rather than to a posture. |
| `rubble_clear` | `never` \| `paths` \| `aggressive` | `paths` | `rubble.nim plan()` — **ADDED, and measured.** Rubble is this year's terrain and its economy is exact: `r → max(0, 0.95r − 10)` per action, **≥ 100 is impassable** to everything but a SCOUT/FASTZOMBIE/BIGZOMBIE, **≥ 50 doubles every movement and cooldown charge**, and **every uninfected corpse adds its own max health** (1000 for an archon, 500 for a BIGZOMBIE, 145 for a guard) so a battle line bricks itself up. Measured on the played pool: `caverns` starts with **1078 of 1892 squares impassable**, `boxy` has squares at **55 555** and `collision` at **9999** — clearing a 100 to 0 takes **14** actions, a 1000 takes **~55**, and a 55 555 is not worth touching. `never`: no unit ever clears; the faction plays the map it was given and the corpses close it. `paths`: clear only to open a route the navigator actually wants and to keep two lanes out of the archon ring, and prefer a **SCOUT** to do it (movementDelay **1.4**, the cheapest digger). `aggressive`: additionally flatten every square below 50 inside the archon ring so the whole home area is full-speed ground, which is what makes a `turtle` opening actually fast. A TURRET and a TTM **cannot clear** (`canClearRubble()`), at any setting. |
| `infection_policy` | `ignore` \| `quarantine` \| `suicide_squad` | `quarantine` | `infect.nim plan()` — **ADDED, and it is this year's largest unexploited play.** An infected robot that dies does not leave a wall, it **stands up as an enemy zombie of its own `turnsInto` at the current outbreak multiplier**, and zombies hunt the *nearest player-controlled robot of either faction*. `ignore`: the faction never reads `getInfectedTurns()`; wounded infected units die where they stand, next to their own archons, and hand the horde a fresh zombie in the middle of the home ring — which is what happens by default. `quarantine`: any unit with `zombieInfectedTurns > 0` or `viperInfectedTurns > 0` immediately walks **away** from every friendly archon and every friendly cluster and holds at ≥ r² 50 until the counter runs out (10 turns for a zombie bite, **20 and 2 damage a turn** for a viper bite, which usually kills a 60-HP soldier), so the zombie it becomes spawns in empty ground. `suicide_squad`: an infected unit instead walks **toward the nearest enemy archon** and dies there — turning a doomed 30-part soldier into a STANDARDZOMBIE inside the enemy's ring, and a doomed archon into a **BIGZOMBIE** (500 HP, 25 damage, scaled by outbreak) that hunts *them* because they are now the nearest player robots. It is the only knob on the sheet that spends your own losses as a weapon, and no 2016 archetype the idea names does it. |

`notes` and `motto` are free text with hard caps (§Server, player, protocol); every truncation is on
**rune** boundaries.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

The two doctrines are deliberately the axis the idea names — the archetype diversity the 2016 finals
produced against the two mechanics that diversity never systematically spent — so the league's
headline matchup is the question this year never got asked.

- **champion #1, `battlecode-bc16-bulwark` (daveey)**: *"You command a faction in Battlecode 2016
  'Zombie Invasion'. Two things kill you: the enemy and the horde, and the horde escalates. Zombie
  dens spawn on a public schedule that you can read from round 0, and every 300 rounds every new
  zombie gets stronger — x1.0, x1.1, x1.2, x1.3, x1.5, x1.7, x2.0, x2.3, x2.6, x3.0 — so a round-2700
  BIGZOMBIE has 5000 health and 250 damage. Your doctrine: build a wall the horde breaks itself on and
  win on archons at round 3000. A GUARD costs 30 parts, has 145 health against a soldier's 60, deals
  DOUBLE damage to zombies, and blocks 4 damage off any hit above 10 — which is exactly a BIGZOMBIE's
  25. A TURRET costs 130 parts and 25 turns of a frozen archon, cannot shoot anything closer than
  range-squared 6, and deals 13 out to range-squared 40. Set opening \"turtle\", turret_count 4-8,
  guard_ratio high (55-85), zombie_kiting \"never\" or \"ranged_only\", archon_spread \"huddle\" or
  \"spread\", rubble_clear \"aggressive\" so your home ground is full speed and your ring is closed,
  retreat_hp 40-70 so wounded units reach an archon's free 1-health-a-turn repair, and
  parts_priority \"turrets\" or \"units\". Set den_clear_round deliberately and say why: a den is 2000
  health and pays 200 parts, and every den you kill deletes its share of every future wave. Set
  infection_policy \"quarantine\" at least: an infected unit that dies becomes an enemy zombie where it
  fell, and you do not want that inside your own ring. In notes, say which den you kill first and what
  you do if their soldiers arrive before round 400."*
- **champion #2, `battlecode-bc16-pullers` (daveey-1)**: *"You command a faction in Battlecode 2016
  'Zombie Invasion'. Everyone in 2016 fought the horde. The horde has exactly one targeting rule: every
  zombie, every turn, walks at the NEAREST PLAYER-CONTROLLED ROBOT on the map, of either team — and a
  SCOUT costs 25 parts, has 80 health, sees range-squared 53, IGNORES RUBBLE ENTIRELY, and cannot
  attack. So the cheapest weapon in this game is a scout standing on the far side of a den. Second
  thing nobody spent: infection. A VIPER hit infects for 20 turns at 2 damage a turn, and ANY robot
  that dies while infected leaves no rubble and stands back up as a zombie of its own type on the
  zombie team — a soldier becomes a STANDARDZOMBIE, a scout a FASTZOMBIE, an archon a BIGZOMBIE — and
  it then hunts whoever is nearest, which can be them. Your doctrine: set opening
  \"scout_zombie_pull\" or \"soldier_viper_aggro\", parts_priority \"vipers\", turret_count low (0-3)
  because a turret cannot chase, guard_ratio low-to-middling (10-40), zombie_kiting \"always\" or
  \"ranged_only\" — a soldier pays movement delay 2 and a STANDARDZOMBIE 3, so you can outrun it and
  shoot it from range-squared 13, but a FASTZOMBIE pays 1.4 and ignores rubble, so say what you do about
  those. Set archon_spread \"split\" and neutral_activation \"hunt\": neutral robots activate for FREE
  within range-squared 2 of an archon, some maps place neutral ARCHONS, and an extra archon is the first
  tiebreak at round 3000. Set infection_policy \"suicide_squad\", rubble_clear \"paths\",
  den_clear_round late (1500-2800), retreat_hp 20-50. In notes, say where your first two scouts stand
  and which of their archons you intend to be standing next to when one of your units turns."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the constant tables (the twelve robot types with parts cost, build turns, health,
damage, ranges, the three delays, sight and `turnsInto`; the delay and rubble rules; the parts income
formula; the outbreak ladder; the infection rules; the activation rule), the map cards for all three
games **with their full zombie spawn schedules and den counts**, the scoring formula, the alias pair, a
**HOW A GAME ENDS** section (the bc21 r1-F8 fix, kept), and the reply contract ("reply with ONE JSON
object whose top-level keys are the knob names; your reply must begin with `{`"). The assistant turn is
prefilled with `{` and the prefix re-attached before parsing (the procgen 0.1.2 scar), unchanged.

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image, env-switched)

`src/battlecode/baselines.nim` is already year-aware (`baselineFor(year, name)`, `:47-84`). It gains a
`bc16` arm with two published names. **The manifest still declares only `awu` and `scaffold`** — the
two ids the certification fixture seats — and `PLAYER_SCRIPTED` resolves **per year**, exactly as
bc20–bc25 do:

| `PLAYER_SCRIPTED` | on `year: "bc16"` resolves to |
|---|---|
| `awu`, `bulwark`, or anything unrecognised | **`bulwark`** — the strong doctrine chassis and the champions' chassis |
| `scaffold`, `greenhorn`, `example`, `examplefuncsplayer` | **`greenhorn`** — the deliberately weak floor and the parity oracle's other side |

The name selects **both** the reply sheet **and the chassis**; the chassis is never a sheet field (D1).
`defaultBaselineFor("bc16")` is `bulwark`, so a seat that says nothing useful plays the strong
doctrine, not the weak floor. `Baseline` gains `blBulwark = "bulwark"` and
`blGreenhorn = "greenhorn"`; `ScriptedChassis` gains `scBulwark = "bulwark"` and
`scGreenhorn = "greenhorn"`.

**`bulwark` — the strong baseline and the champion chassis.** Written for this run from the engine's
own mechanics and from the three archetypes the idea names; **no line of any competitor repository is
copied, vendored, translated or read** (§The game, "Provenance and licensing"). Parameterised by all
eleven knobs. Algorithm, by file:

- **`kit.nim`** — the per-side memory every robot shares and the `DecisionOps` charging: the
  remembered map (rubble per square with the round it was seen, remaining parts per square, a
  dead-square set for squares seen at 0 parts), the remembered den roster with each den's remaining
  health and its **known schedule** (public: `getZombieSpawnSchedule()`), the remembered neutral
  roster by type and value, the enemy-archon estimate seeded from `getInitialArchonLocations(enemy)`
  (public from round 0) and refined by sightings, and the navigator: a bounded BFS over the sensed
  window plus the remembered map, **weighted by the real cost of each step** —
  `movementDelay × (1.4 if diagonal) × (2.0 if destination rubble ≥ 50)`, impassable at ≥ 100 unless
  the mover `ignoresRubble` — falling back to a greedy step with a 6-square no-repeat history to break
  oscillation. **Every node expanded is charged 1 `DecisionOps`**, and the budget is checked before the
  BFS starts, never inside it.
- **`econ.nim`** — `plan()` (from `opening`), `attackMix()` (from `guard_ratio`), `queue()` (from
  `parts_priority`), and the per-archon commitment ledger, so two archons cannot promise the same 30
  parts. It is the only place parts are ever committed, and it holds the unconditional floor: **≥ 3
  attackers per archon**, and a build order whenever the stockpile is above 200.
- **`archon.nim`** — an archon's turn, in the engine's own action order: build what `econ.nim` asks for
  into the free adjacent square nearest the frontier (never boxing itself in and never adjacent to a
  den with a queue); **spend the free repair** on the weakest damaged friendly non-archon in r² ≤ 24;
  `activate` per `neutral.nim`; then `posture()` per `archon_spread`, walking over parts squares
  wherever the route allows because a move onto parts collects them for nothing.
- **`combat.nim` + `micro.nim`** — the war. `micro.nim` implements `kite()` (per `zombie_kiting`) and
  `retreat()` (per `retreat_hp`); target selection prefers, in order, a target this attack will
  **kill**, then a ZOMBIEDEN inside range if `dens.nim` has committed, then the lowest-health hostile
  (vipers first, then soldiers, then guards, then turrets in TURRET form, then zombies by descending
  damage), and it **never** selects a friendly square. Guard micro is separate: a guard closes to
  r² ≤ 2 and holds, because it is the block. Turret micro is `unpack`-and-hold with a `pack` only when
  `turret.nim` has a new site.
- **`turret.nim`** — `target()` and `site()` per `turret_count`, plus the pack/unpack schedule (a
  relocation is 20+ turns of silence, taken only when the site's covered-lane count improves by ≥ 2).
  **`dens.nim`** — `schedule()` per `den_clear_round`: the den with the largest remaining queue and the
  cheapest approach, a group sized to break 2000 HP inside 250 rounds, and every member kept out of the
  eight adjacent squares except while attacking (the 10-damage proximity rule).
  **`neutral.nim`** — `plan()` per `neutral_activation`: value neutrals as `partCost` with ARCHON above
  everything, route the nearest archon, and claim in comms so two archons do not walk at the same one.
  **`rubble.nim`** — `plan()` per `rubble_clear`: the clear queue, the scout-first preference, and the
  "never touch anything above 200" rule. **`infect.nim`** — `plan()` per `infection_policy`: read both
  infection counters every turn and emit a movement request the other modules honour (`quarantine` =
  away from friends; `suicide_squad` = at the nearest enemy archon).
- **`comms.nim`** — the signal layer, and the one place this year is *harder* than the others: there is
  no shared array. A robot may send **5 basic** signals a turn (position + id + team, any type) and an
  ARCHON or SCOUT may send **20 message** signals (two 32-bit ints), each costing **0.05 delay on both
  counters** inside twice its own sight radius and `0.05 + 0.03 × (r²/sightR² − 2)` beyond it, and
  **every signal is heard by the enemy too**. The layout: message word 1 packs
  `kind:4 | x:7 | y:7 | payload:14`, word 2 packs `round:12 | value:20`; kinds are
  `0 den-sighting`, `1 den-health`, `2 neutral-sighting`, `3 neutral-claim`, `4 enemy-archon-sighting`,
  `5 rally`, `6 census`, `7 clear-request`, `8 quarantine-lane`, `9 suicide-target`. The chassis sends
  at most **1 message signal per archon per turn and 1 basic signal per scout per 5 turns**, at
  `r² = 2 × sightR²` so the cost is the flat 0.05, and it never encodes anything whose disclosure to
  the enemy costs more than the coordination is worth (den health and rally points, yes; archon
  posture, no).

**`greenhorn` — the weak floor and the parity oracle's other side.** A deliberately simple bot, and
the **only** bot in this year module that exists in two implementations that must agree
statement-for-statement: `years/bc16/chassis/greenhorn.nim` and
`tools/oracle/bc16/bc16greenhorn/RobotPlayer.java`. Its whole behaviour:

1. It seeds **`new java.util.Random(2016)` per robot** at construction and calls only `nextInt(8)`.
2. An **ARCHON**: if `getTeamParts() >= 30` and core-ready, pick `d = DIRECTIONS[rng.nextInt(8)]` and
   `build(d, SOLDIER)` if `canBuild(d, SOLDIER)`; otherwise, if core-ready, `move(DIRECTIONS[rng.nextInt(8)])`
   if it can; otherwise nothing. It never repairs and never activates.
3. A **SOLDIER**: `senseHostileRobots(myLoc, attackRadiusSquared)`; if the array is non-empty and the
   weapon is ready, `attackLocation(hostiles[0].location)`; else if core-ready,
   `move(DIRECTIONS[rng.nextInt(8)])` if it can.
4. **Every other type does nothing at all** — so `greenhorn` never builds a guard, a scout, a viper or
   a turret, never clears rubble, never sends a signal, never activates a neutral and never kills a den.
   That is what being the weak floor means, and it is why the substance assertions that need those
   things are asserted **across the pair** and not per seat (§Tests, `docker-smoke`).
5. `DIRECTIONS` is **N, NE, E, SE, S, SW, W, NW** in that order, because `nextInt(8)` indexes it.
6. **It may not gain behaviour: it is one side of the differential oracle**, and
   `tests/test_bc16_greenhorn.nim` asserts its `Random(2016)` call sequence and its branch order
   against a recorded oracle trace.

Its scripted reply is the all-defaults sheet (it reads no knob). Both replies go through the **same**
`sheet.validate` the LLM path uses, which is what makes the bounded-orders test meaningful and an LLM
doctrine and a scripted one strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays the **fallback sheet** below on the `bulwark` chassis, `results.fallbacks[seat] = 1`, a **`doctrine_fallback` event** names the cause, the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` (45 000) | whatever is unresolved takes the fallback sheet; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default (or clamps, for the four integers); the rest of the sheet applies |
| the sheet arrives inside an envelope | it is unwrapped **once**, the envelope key is recorded in `seats[].sheet_envelope`, and the knobs apply |
| a seat never registers | it plays the fallback sheet; the slot is reported to `COGAME_PLAYER_FAILURE_URI` and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds` (120), or the match exceeds `matchBudgetSeconds` (360) | the running game is **abandoned**, finished games are scored, `results.reason = deadline`, `plan.abandonAfter[g]` records the round it stopped at |
| a side takes 2 games | the episode settles immediately — no padding (§The game, clinch semantics) |
| a sim invariant trips (negative stockpile, spawn onto an occupied square, hash-chain break) | `results.reason = fault`, `scores = [0, 0]`, and a **partial replay is still written** |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

**The fallback sheet, verbatim** — identical to the `bulwark` baseline reply, and it is exactly the
all-defaults sheet:

```json
{"sheet":{"opening":"turtle","turret_count":3,"guard_ratio":45,
          "zombie_kiting":"ranged_only","den_clear_round":900,
          "parts_priority":"units","archon_spread":"spread",
          "neutral_activation":"opportunistic","retreat_hp":35,
          "rubble_clear":"paths","infection_policy":"quarantine"},
 "notes":"default bulwark doctrine","motto":"The wall holds."}
```

---

## Sim module

`src/battlecode/` stays one deterministic sim compiled **twice** from the same sources: natively into
`/bin/battlecode` and to wasm into `replay-viewer/dist/bc_replay.js|.wasm|.data`. Nothing
gameplay-related lives outside it; the viewer never re-implements a rule.

### New and changed files

| file | status | role |
|---|---|---|
| `src/battlecode/years/bc16/constants.nim` | **new, generated** | every `GameConstants` value plus the whole twelve-row `RobotType` table with its seventeen constructor fields, the `turnsInto` graph, the derived predicates and the outbreak ladder, emitted by `tools/gen_year_constants.py --year bc16` from the pinned checkout; CI regenerates and byte-diffs |
| `src/battlecode/years/bc16/units.nim` | **new** | the pure per-unit arithmetic: the `RobotType` table and predicates, `Team` (**four** values — A, B, NEUTRAL, ZOMBIE), `Dir` (ten values, `NONE`/`OMNI` last), the outbreak-scaled `maxHealth(round)`/`attackPower(round)`, the guard multiplier and reduction, the move-cost factors, and `directionTo`'s 2.414 form |
| `src/battlecode/years/bc16/world.nim` | **new** | world state: the rubble and parts arrays, the robot table, the **insertion-ordered exec list** with by-value removal, the location index, team stockpiles, per-robot signal queues, and every action of rule 3.2 |
| `src/battlecode/years/bc16/delays.nim` | **new** | the `coreDelay`/`weaponDelay` pair and its four mutators — `addCoreDelay`, `addWeaponDelay`, `setCoreDelayUpTo`, `setWeaponDelayUpTo` — plus `decrementDelays` (V1) and the two composite helpers `activateCoreAction` and `activateAttack` with their **opposite** set/add pairing. One file, because getting that pairing backwards is the single easiest way to break this year |
| `src/battlecode/years/bc16/health.nim` | **new** | the single `changeHealthLevel` mutation point with its cap, its `source == TURRET` flag, its death path, the rubble deposit, the infection→zombie conversion and the mid-turn `DESTROYED` check |
| `src/battlecode/years/bc16/zombies.nim` | **new** | the den queue, `spawnAllPossible` with `getSpawnDirection`/`getSpawnChirality`, the proximity damage, and `processZombie`'s eight-step ladder — the verbatim port of `ZombieControlProvider` |
| `src/battlecode/years/bc16/economy.nim` | **new** | the parts income formula, `takeParts`, the den bounty, and the `partsWorth` sum the ladder and the score read |
| `src/battlecode/years/bc16/signals.nim` | **new** | the per-robot FIFO queue (1000, oldest dropped), the per-turn counters (5 basic / 20 message), the broadcast radius walk over **all teams** and the two-counter delay charge |
| `src/battlecode/years/bc16/rules.nim` | **new** | the round loop of rule 1–4, the four-rung ladder, the points formula, `playGame` |
| `src/battlecode/years/bc16/maps.nim` | **new** | the converted bc16 pool, the loader, `poolNames`, `drawMaps`, `sideAslotFor`, `mapCard` |
| `src/battlecode/years/bc16/knobs.nim` | **new** | the eleven-knob `Doctrine16` type, `KnownKeys16`, defaults, per-field repair, **absent-key defaulting**, `toJson16`, `bc16SheetSchema`, `plainWords16` |
| `src/battlecode/years/bc16/chassis/*.nim` | **new** | `bulwark.nim`, `greenhorn.nim`, `scenario16.nim`, `kit.nim`, `econ.nim`, `archon.nim`, `combat.nim`, `micro.nim`, `turret.nim`, `dens.nim`, `neutral.nim`, `rubble.nim`, `infect.nim`, `comms.nim` — **fourteen files**, and `NOTICE` + `docs/RULES-BC16.md` name the same paths |
| `src/battlecode/years/registry.nim` | **one line added** | `YearSpec(id: "bc16", title: "Battlecode 2016 — Zombie Invasion", maxRounds: 3000, pools: @["small","mixed","large"], atlas: "atlas_bc16")` |
| `src/battlecode/years/dispatch.nim` | **one arm per `case`** | `YearId` gains `yBc16`; `Session` gains a `yBc16` branch (`w16`, `sides16`, `chassis16`); `yearIdOf`/`strongChassisFor`/`parseScriptedChassis`/`poolNamesFor`/`drawMapsFor`/`sideAslotFor`/`mapPathFor`/`mapCardFor`/`newSession`/`stepRound`/`currentRound`/`running`/`hashChainHex`/`mapWidth`/`mapHeight`/`playGameFor` each gain one arm, plus `statsJson16`. Three name tables are added beside the other years': `Bc16ActionNames`, `Bc16UnitNames`, `Bc16RungNames` (below) |
| `src/battlecode/sim_types.nim` | **changed** | `GameVersion` → `GV11`, `ReplayCompatibleGameVersions` → `["GV04",…,"GV10", GameVersion]`, prepend-only changelog entry; `ScriptedChassis` gains `scBulwark` and `scGreenhorn` |
| `src/battlecode/baselines.nim` | **changed** | a `yBc16` arm in `defaultBaselineFor` and `baselineFor`; `blBulwark` and `blGreenhorn` added to `Baseline`; `baselineChassis` and `baselineReply` map them |
| `src/battlecode/sheet.nim` | **changed** | `YearBc16`, `doctrine16` on `Sheet`, and one arm each in `knownKeysFor`, `defaultSheet`, `validate`, `toJson`, `plainWords` — **the envelope resolver is untouched** |
| `src/battlecode/match.nim` | **changed** | `winBonusFor` gains `yBc16` to the 200 set; the bc16 event names are added to `collectGameEvents` |
| `src/battlecode/render.nim` | **year-aware** | sprite mapping per `YearSpec.atlas`; bc16 adds the rubble heat layer with its impassable tone, parts pips per square, the twelve unit sprites at **four** team palettes, health bars, an infection ring, and a build-progress hatch for `!isActive()` robots |
| `src/battlecode/broadcast.nim` | **year-aware** | the bc16 scorebug / feed / endcard shell records **and the bc16 arms of `beatsFor`** (§Viewer) |
| `src/battlecode/rng.nim` | **unchanged, reused** | the `java.util.Random` port and `IdGenerator`. bc16 constructs **three** live streams from it (D2) |
| `src/battlecode/results.nim` | **changed** | the bc16 optional keys added to the closed schema's key set |
| `src/battlecode/replay.nim` | **unchanged** | it re-validates the recorded **applied** sheet wrapped in `{"sheet": …}` (`replay.nim:173-176`), so nothing bc16 does can change how an older recording re-derives |
| `data/maps/bc16/*.json` | **new, committed** | 22 converted maps, each carrying its **pre-split per-den schedule** (D3) |
| `data/bc16/tables.json` | **new, committed** | the whole finite arithmetic domain (below) |
| `data/atlas_bc16.png` / `.json` | **new, committed** | the 2016 sprite atlas (≈ 140 KB) |
| `tools/convert_maps_bc16.py` | **new** | reads the engine's `.xml` and writes `data/maps/bc16/<name>.json`, **including the per-den schedule split** |
| `tools/map_pools_bc16.json` | **new** | the three pools |
| `tools/build_sprite_atlas_bc16.py` | **new** | cuts `atlas_bc16.*` from the 2016 client's `art/` tree |
| `tools/gen_year_constants.py` | **`--year bc16` added** | reads the 2016 `GameConstants.java` + `RobotType.java` |
| `tools/JavaBc16Tables.java` | **new, CI-only** | regenerates `data/bc16/tables.json` under CI **JDK 8** from the jar's own classes |
| `tools/oracle/bc16/Bc16Trace.java` | **new, CI-only** | the trace driver (§Tests) — one file, compiled against the released jar |
| `tools/oracle/bc16/bc16greenhorn/RobotPlayer.java` | **new, CI-only** | `greenhorn`'s Java twin, statement for statement |
| `tools/oracle/bc16/bc16idle/RobotPlayer.java` | **new, CI-only** | the Tier A bot: `while (true) Clock.yield();` and nothing else |
| `tools/oracle/bc16/bc16scenario/RobotPlayer.java` (+ `…annihilate`, `…tie`, `…turn`) | **new, CI-only** | the Tier A′ scenario bots that force every rare path |
| `tools/oracle/bc16/build_oracle.sh` | **new, CI-only** | sha256- and size-verifies the jar, asserts its bundled `org/objectweb/asm`, `com/thoughtworks/xstream`, `MethodCosts.txt` and **54** `.xml` map resources, and compiles the driver + all six bots |
| `tools/oracle/bc16/jar.lock` | **new, CI-only** | the oracle jar's URL, size (**6 563 607**) and sha256 (**`c78ef341af0b666acabdabf545695862b77f84076f946766787bc1549b1fdc1c`**) |
| `tools/parity_trace_bc16.nim` | **new, CI-only** | the Nim side of the trace |
| `tools/ci/parity_tiers_bc16.py` | **new** | the tier comparison and the ledger check — bc22's script, whose three comparator bugs are already fixed there, **plus origin normalisation** (V3) |
| `tools/ci/parity_ledger_bc16.json` | **new** | the accepted-divergence ledger, **empty** at the phase-30 exit |
| `tools/gen_bc16_fixture_replay.nim` + `tests/fixtures/replay-bc16.json` | **new, committed** | the fixture replay the wasm smoke and the beat test load |
| `tests/bc16_fixture.nim` | **new** | the shared fixture builder, beside `bc22_fixture.nim` … `bc25_fixture.nim` |
| `docs/RULES-BC16.md` | **new** | the year's rules, knobs and the full §Divergences list |

**A layout rule, written here because the bc24 run paid a fixer commit for its absence.** The file
list above is the intended layout and `NOTICE`, `knobs.nim`'s doc comments and `docs/RULES-BC16.md`
all point at it. If the builder merges two of these modules — for example folds `delays.nim` into
`world.nim` — it must update **every one of those three pointers in the same commit** and add a
`docs/RULES-BC16.md` §Divergences item recording the merge. A licence file that credits derived
behaviour to a path that does not exist is a defect, not a cosmetic slip.

Three action/name tables are added to `years/dispatch.nim` beside the other years', because an event
field with an undocumented vocabulary is an event field nobody can draw (the bc23 r1-F14/F25
lessons):

```
Bc16ActionNames = ["clear_rubble", "move", "attack", "broadcast",
                   "broadcast_message", "build", "activate", "repair",
                   "pack", "unpack", "disintegrate"]
Bc16UnitNames   = ["zombieden", "standardzombie", "rangedzombie",
                   "fastzombie", "bigzombie", "archon", "scout", "soldier",
                   "guard", "viper", "turret", "ttm"]     # RobotType ordinals
Bc16RungNames   = ["-", "archons_destroyed", "more_archons",
                   "more_archon_health", "more_parts_net_worth",
                   "highest_id"]                          # for tiebreak.rung
```

`first_action`'s field is **`action`**, never `kind`: a field named `kind` is flattened into the same
object as the event's own `kind` key and silently overwrites it (the bc23 r1-F25 finding).

### Determinism

**`rng.nim` is reused unchanged, and bc16 runs THREE live `java.util.Random` streams — more than any
prior year.** All three are seeded with the **map seed** and all three are **separate objects with
separate 48-bit states**, so the port must construct three independent generators, not share one.

- **D2a — `IDGenerator(mapSeed)`** (`GameWorld.java:75`, `IDGenerator.java:297-346`): the 48-bit LCG,
  `nextInt(bound)` with both the power-of-two shortcut and the rejection loop, **4096-id blocks
  starting at id 1** (`reservedIDs[i] = nextIDBlock + i + 1`, `nextIDBlock` starting at **0**), each
  block **Fisher–Yates shuffled from `i = 4095` down to 1 with `nextInt(i+1)`**. It fixes the id of
  **every** robot including the initial ones — unlike 2022, where the map file carried them. A
  3000-round game spawns well under 4096 robots on the played pool, so the second block is rarely
  reached; `tests/test_bc16_rng.nim` reaches it anyway.
- **D2b — `GameWorld.rand = new Random(mapSeed)`** (`:134`), read at **exactly one site**:
  `getNearestPlayerControlled`'s `rand.nextInt(closest.size())` (`:439`). It is called **once per
  zombie turn in which at least one player robot is alive**, *including* when there is exactly one
  candidate, because `java.util.Random.nextInt(1)` still consumes a `next(31)` draw. **This is the
  highest-traffic RNG stream in any year this repo ships** — hundreds of draws a round in a late-game
  horde — and getting its call condition wrong by one draw desynchronises the whole game. The trace's
  per-round `X` line carries the stream's current 48-bit seed so Tier A catches a single missed draw
  on the round it happens.
- **D2c — `ZombieControlProvider.random = new Random(mapSeed)`** (`:84`), read at **exactly two
  sites** in `processZombie`: `random.nextInt(8)` (`:250`) **only when there is no player robot alive
  at all**, and `random.nextBoolean()` (`:255`) **only when the zombie got past the attack branch,
  past the `!isCoreReady()` branch, and past the "move in the preferred direction" branch**. The
  precondition chain in rule 5.5 is exact and is the single most order-sensitive thing in the port;
  `tests/test_bc16_zombies.nim` replays it against a recorded oracle draw sequence.
- **D2d — the map origin's two draws are NOT reproduced.** V3, proven inert.

**Five further determinism decisions, each with its written argument. All are in
`docs/RULES-BC16.md` §Divergences.**

- **D1 — the two hash-order robot sweeps in the round loop need NO port at all, because in 2016
  neither has any observable behaviour.** `processBeginningOfRound` (`GameWorld.java:586-588`) calls
  `InternalRobot.processBeginningOfRound`, whose body is **empty** (`:431-432`).
  `processEndOfRound` (`:617-619`) calls `InternalRobot.processEndOfRound`, whose body is **empty**
  (`:459`). And both iterate a `LinkedHashMap` anyway, so even their *order* is insertion order.
  Stated explicitly so nobody ports them "to be safe" and then has to justify it.
- **D2 — the exec order and every robot iteration are INSERTION order.** `gameObjectsByID` is a
  `LinkedHashMap` (`:72`), and it is the only robot collection the engine ever iterates:
  `runRound`'s snapshot (`:158`), `allObjects()` (`:239-241`) which `senseNearbyRobots` and
  `senseHostileRobots` read, `getAllGameObjects()` (`:243-246`) which rung 3 of the ladder reads,
  `getAllRobotsWithinRadiusSq` for `r² >= 16` (`:400`), and `getNearestPlayerControlled` (`:421`).
  **There is no trove, no `net.sf.jsi`, no `EnumMap` iteration and no hash-ordered robot sweep
  anywhere in the round loop.** `years/bc16/world.nim` therefore keeps one `seq[int]` exec list with
  append-on-spawn and **by-value removal** on death, plus a `Table[int, Robot]` for lookup that is
  **never iterated**. This is the single biggest simplification bc16 has over bc22, and it is worth
  saying twice: the port needs **no hash-map port of any kind at run time**.
- **D3 — the ONE hash-order dependency in the whole 2016 engine is resolved at BUILD time, not
  ported.** `GameMap.buildZombieSpawnMap` (`:718-793`) iterates `byLoc.keySet()`, a
  `java.util.HashMap<MapLocation, InitialRobotInfo>` built by `Collectors.toMap`, and that order
  decides `denLocs`, which decides which den receives each leftover zombie when a round's count does
  not divide evenly. It is *deterministic* (a pure function of `MapLocation.hashCode() = x*13 + y*23`,
  the insertion order and the table capacity) but it is a hash-map walk. **The resolution:
  `tools/convert_maps_bc16.py` reproduces Java 8's `HashMap` iteration order — `hash = h ^ (h >>> 16)`,
  bucket `hash & (n−1)`, default capacity 16, load factor 0.75, resize splitting each bucket into its
  lo/hi lists in place, iteration walking buckets 0…n−1 and each chain in insertion order — computes
  `denLocs` and the whole per-den split ONCE, and writes it into the converted map JSON as
  `dens: [{x, y, schedule: {round: {type: count}}}]`.** The runtime sim reads it and **never hashes
  anything**. Tier B **byte-diffs the committed per-den schedules against the JVM's own
  `getZombieSpawnSchedule(denLoc)`** for all 22 maps, so the emulation is proved rather than trusted.
  **Measured over all 98 maps: every per-den total is equal within ±1 and every ±1 lands on BOTH
  members of a symmetric pair, so no side is ever advantaged** — but the *identity* of the den that
  gets the extra zombie changes which square it spawns on, which is why it is reproduced.
- **D4 — the map symmetry is computed at build time and recorded, not computed at run time.**
  `GameMap.updateSymmetries` (`:529-632`) tests VERTICAL, HORIZONTAL, ROTATIONAL and (only when
  `width == height`) NEGATIVE_DIAGONAL and POSITIVE_DIAGONAL over both the rubble+parts arrays and the
  robot roster, and takes **the FIRST one that holds in that order**, warning and keeping it if more
  than one does. The only runtime reader is `getSpawnChirality`. `tools/convert_maps_bc16.py`
  reproduces the whole test and writes `symmetry` **and** `symmetries_found` into the map JSON; CI
  byte-diffs both against the JVM's own `getSymmetry()`. **Measured across the 98 maps: 61 are
  ROTATIONAL, 33 HORIZONTAL, 2 VERTICAL and 2 (the armageddon pair) NONE; and 13 maps satisfy TWO
  symmetries** — `carbonated`, `central_protocol`, `channel`, `collider`, `crater`, `fortifications`,
  `frogger`, `nexus`, `opulent`, `quartiles`, `spaghetti`, `treasure`, `tunnels` — where the engine's
  first-wins order decides, so the pool deliberately includes `frogger` (VERTICAL wins over ROTATIONAL)
  as the control that proves the resolution order.
- **D5 — the `.rms` serial layer, the XStream/Jackson serialisers, `SquareArray`'s object wrapper and
  the `server/proxy` writers have no port** (V6). `SquareArray.Double` is a flat `double[]` indexed
  `y*width + x` (`util/SquareArray.java`); the port uses a `seq[float64]` with the same indexing so the
  two checksums line up.

**The arithmetic is FLOAT64 everywhere, and that is this year's headline fidelity theme.** 2022 was an
integer year with six float truncations; 2016 is the opposite — health, damage, delays, rubble, parts
and every multiplier are `double`.

- **IEEE-754 binary64 add, subtract, multiply, divide and compare are exactly specified**, Nim on
  x86-64 uses SSE2 (never x87), and wasm32 has only IEEE doubles. So a port that reproduces **each
  expression in the engine's own order and parenthesisation** is bit-exact by construction. The port
  never re-associates, never factors and never accumulates in a different order — in particular rung 3
  of the ladder walks the robot table **once**, in exec order, seeded with the parts difference,
  exactly as `GameWorld.java:641-665` does. `tests/test_bc16_arith.nim` pins the named products the
  engine actually computes: `2 × 1.4 = 2.8`, `2 × 1.4 × 2 = 5.6`, `1.4 × 1.4 = 1.9599999999999997`,
  `60 × 1.1 = 66.00000000000001`, `145 × (1.0/3.0) = 48.333333333333336`, `100 × 0.95 − 10 = 85`,
  `2.0 − 0.01 × 137 = 0.63`.
- **Exactly two non-algebraic functions exist on gameplay paths; BOTH have finite domains and BOTH are
  tabled at build time**, so the runtime path has no transcendental at all. (i) **`Math.pow(x, 1.5)`**
  in `decrementDelays` (`InternalRobot.java:326`), whose argument is
  `max(0.0, 8000 − limit + prevBytecodes) / 8000.0` over integer terms — the **8001 values `k/8000`
  for k = 0…8000**, all in `data/bc16/tables.json`, generated by `tools/JavaBc16Tables.java` under CI
  JDK 8 and byte-diffed (Tier B′). The port does not even read that table at run time (V1 pins the
  result to 1.0); it exists so the divergence is **measured** rather than asserted.
  (ii) **`(int) Math.sqrt(r²)`** in both radius scans (`GameWorld.java:355`,
  `MapLocation.java:262`), whose reachable set is **{0, 2, 6, 13, 20, 24, 35, 40, 53}** plus whatever a
  chassis passes, bounded by 100 for the static form and clamped to `max(80, 80) = 80` for the world
  form (`:356-357`): tabled for r² = 0…10 000. **No `sqrt` on any runtime path.** `Math.abs` and the
  `2.414` comparisons in `directionTo` (`:154-182`) are exact float64 ops, and Tier B tables the whole
  lattice for `dx, dy ∈ −80…80` (**25 921 pairs**) against the JVM.
- **Health is compared with `<= 0`** and capped with `> maxHealth` (`InternalRobot.java:281,285`), and
  **delay readiness is strictly `< 1` on a float64** (`:417,422`) — so a robot at 0.0000000001 health
  is alive and a unit at exactly 1.0 core delay is **not** ready. Both ported as written;
  `tests/test_bc16_cooldown.nim` names the readiness boundary.

**Every round appends to a hash chain**; the viewer re-derives each round and compares, exposing
`bc_mismatch_round`. The values folded into the bc16 chain each round — **fifteen per team plus eleven
globals**, so a re-derivation that diverged in only one of them cannot reproduce the chain (the GV02
lesson): per team — archons alive, live robots by each of the six player types, total robot health in
tenths, total archon health in tenths, parts stockpile in tenths, `partsWorth`, robots infected,
robots lost, parts collected, dens killed, neutrals activated; plus globally — the round number, an
FNV-1a 64 hash of the rubble array (y ascending outer, x ascending inner) in tenths, an FNV-1a 64 hash
of the parts array in tenths, an FNV-1a 64 hash of the exec-order list, the exec list's length, the
live zombie count by each of the four zombie types, the number of dens standing, the number of
neutrals standing, **the 48-bit state of `GameWorld.rand`**, and **the 48-bit state of
`ZombieControlProvider.random`**. Folding the two RNG states is a bc16-specific decision and it is the
cheapest possible tripwire for a missed or extra draw (D2b/D2c).

Any wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record**
(`plan.abandonAfter[g]`) applied by the same proc on record and on playback — the particle-worlds
scar — and the record→re-derive test covers **every** bc16 end reason, not just `complete`.

**`GameVersion` bumps to `GV11`** in the same commit, with a prepend-only changelog line: *"bc16 year
module added, ported from battlecode-server-2016 at 11a0b09f (oracle jar 2016.0.2.2): the four-step
round loop over an INSERTION-ordered exec list with by-value removal and a pre-sweep snapshot, rounds
numbered from ZERO, the twelve robot types with their float64 core/weapon delay pair and its
asymmetric set-up-to/add-to charging, the rubble economy (impassable at 100, double cost at 50,
`0.95r − 10` per clear, and every uninfected corpse adding its own max health), parts income
`max(0, 2 − 0.01 × robots)` with archon-only pickup, the public per-den zombie spawn schedule with its
build-time symmetric split, the outbreak ladder, the verbatim zombie AI over THREE independent
`Random(mapSeed)` streams, infection with its 10/20-turn counters and its die-and-turn conversion,
free neutral activation, and the four-rung round-2999 tiebreak ladder, behind `game_config.year`. The
bytecode-dependent delay decay is pinned to 1.0 (a documented divergence). bc20, bc21, bc22, bc23,
bc24, bc25 AND bc26 SEMANTICS ARE UNCHANGED: no GV04..GV10 recording carries a byte whose meaning
changed, which is why `ReplayCompatibleGameVersions` is EXTENDED rather than reset and every hosted
replay keeps rendering."*
**`ReplayCompatibleGameVersions` becomes `["GV04","GV05","GV06","GV07","GV08","GV09","GV10", GV11]`**
— extended, never reset. `tools/ci/check_gameversion.sh` claims the version across branches; **it
compares the headline, not the digits, so if a sibling branch lands GV11 first this branch rebases to
GV12 and extends the list again** (the bc20 precedent).

### The chassis, the DecisionOps budget and the delay-decay divergence

The engine's per-robot **bytecode limits** (`ARCHON` and `SCOUT` 20 000, everything else 10 000) have
no meaning outside the JVM instrumenter. They are replaced by a **fixed per-robot `DecisionOps`
budget of 2000 (ARCHON, SCOUT), 1000 (SOLDIER, GUARD, VIPER, TURRET, TTM) and 0 for any robot with
`!isActive()`** — one tenth of the Java limits, the convention bc20–bc26 use. One credit is charged
for each: square sensed, robot examined in a sense sweep, BFS node expanded, direction evaluated,
signal read from the queue, parts or neutral candidate scored, den lane scored, and micro target
scored. Credits are deducted inside `kit.nim` and **enforced by the sim, not by the bot**.

Three properties make this safe, and all three are stated so nobody has to rediscover them:

- **The budget is checked *before* each primitive and never inside one.** A navigation BFS, a vision
  sweep or a micro evaluation either runs to completion or does not start. So a primitive's *result*
  is never a function of the remaining budget, only *whether the chassis got to ask*. When the budget
  reaches zero the robot's turn ends where it stands — it is **not** resumed mid-computation next
  turn, which is the one place this differs from the JVM.
- **No rule reads the budget.** This is the decisive property and it is why V1 exists. In the real
  engine the *delay decay* is a function of last turn's bytecode count, which would make the chassis's
  own implementation a rules input: a one-line refactor of `bulwark`'s BFS would change what a round
  resolves to and would have to bump `GameVersion`. Pinning `amountToDecrement = 1.0` cuts that
  dependency completely — the budget becomes a pure compute cap, exactly as in every other year, and
  the chassis is free to change without touching the rules.
- **And on the parity side the divergence is not exercised.** Tier A's `bc16idle` bot spends
  essentially no bytecodes (`while(true) Clock.yield();`) and Tier A′'s scenario bots **assert at the
  end of every turn that `Clock.getBytecodeNum()` is at or below `bytecodeLimit − 8000`** (2000, or
  12 000 for an archon/scout) and `System.exit(4)` if not — so on both sides the engine's own
  `amountToDecrement` is **exactly 1.0** and the comparison is defined for the whole game. The
  formula's other 8000 values are proved by Tier B′'s table instead. `docs/PARITY.md` §bc16 states in
  as many words that **the sub-1.0 branch of `decrementDelays` is the one behaviour parity cannot
  compare**, and why.

Why full metering is out of scope for v1, logged here so it is not re-litigated: metering Nim to Java
bytecode granularity needs either a Nim-level instrumenter (a compiler project) or a hand-annotation
of every statement against the jar's own `MethodCosts.txt`, and neither buys anything the budget does
not — the chassis are ours and are written to fit the budget.

### Maps

**22 of the 98 official maps are converted and committed. Every one of the 98 was parsed** with the
reader `tools/convert_maps_bc16.py` implements, and the table below is those measurements. The engine's
map format is **XML**, not flatbuffers — `<game-map width height origin seed rounds mapName>` with
`<initialRubble>`/`<initialParts>` as **`[y][x]` rows of `<double-array>`** (`GameMap.java:31-42`),
`<zombieSpawnSchedule><round number="N"><zombie-count type count/>`, and
`<initial-robot originOffsetX originOffsetY type team/>` rows — so the converter is a plain XML walk
with no `flatc`, no schema and no library beyond Python's stdlib.

**Every map in every pool is drawn from the 54 that the oracle jar also carries as resources**, so no
parity pair and no smoke episode needs a `--map-dir`. Measurements: `rmean` is the mean rubble over
all squares, `walls` the number of squares at rubble ≥ 100 (impassable to everything but a
scout/fast/big zombie), `parts` the map's total collectable parts and `psq` the number of squares
carrying any, `z/den` the per-den zombie total across the whole schedule and `totz` the map total,
`sep` the minimum Euclidean distance between an A archon and a B archon.

| pool | map | size | area | seed | symmetry | archons/side | dens | neutrals | rmean | rmax | walls | parts | psq | pmax | sched rounds | first wave | z/den | totz | sep |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `small` | `checkers` | 30x30 | 900 | 946 | ROTATIONAL | **2** | 4 | 30 | 100.0 | 200 | **450** | 2 000 | 10 | 200 | 10 | 150 | 67 | 266 | 7.1 |
| `small` | `zigzag` | 30x30 | 900 | 8 | ROTATIONAL | **2** | 6 | 0 | 80 000 | **1 000 000** | 72 | 3 380 | 134 | 100 | 12 | 50 | 46 | 276 | 9.1 |
| `small` | `swamp` | 34x30 | 1 020 | 8563 | ROTATIONAL | **1** | 4 | 18 | 100.1 | 999 | 58 | 1 680 | 56 | 30 | 10 | 150 | 67 | 266 | 38.3 |
| `small` | `river` | 32x32 | 1 024 | 938 | ROTATIONAL | **3** | 4 | 12 | 46.6 | 999 | 54 | 1 320 | 66 | 20 | 10 | 150 | 67 | 266 | **4.0** |
| `small` | `prisons` | 30x40 | 1 200 | 1337 | ROTATIONAL | **3** | **2** | 6 (**2 archons**) | 194.8 | 1 000 | 232 | 1 500 | 22 | 100 | 12 | 50 | **116** | 232 | 21.0 |
| `small` | `frogger` | 35x35 | 1 225 | 53 | **VERTICAL** (also rotational) | **4** | **12** | 4 | 34.3 | **80 (no walls at all)** | **0** | 3 340 | 334 | 10 | 12 | 50 | 23 | 276 | 12.0 |
| `mixed` | `closequarters` | 36x30 | 1 080 | 86 | ROTATIONAL | **4** | 4 | 0 | 220.4 | 2 000 | 164 | 2 980 | 56 | 100 | 9 | **300** | 52 | 208 | 7.0 |
| `mixed` | `lockdown` | 34x34 | 1 156 | 3434 | ROTATIONAL | **3** | 4 | 16 | 112.7 | 777 | 162 | 2 522 | 102 | 77 | 12 | 50 | 51 | 204 | 22.0 |
| `mixed` | `industrial` | 37x37 | 1 369 | 536 | ROTATIONAL | **2** | 4 | 22 (**2 archons**) | 71.9 | 1 000 | 348 | 2 120 | 65 | 200 | 12 | 50 | 69 | 276 | 30.1 |
| `mixed` | `quadrants` | 39x39 | 1 521 | 8123 | ROTATIONAL | **4** | 4 | 0 | 84.7 | 500 | 243 | **20 520** | **684** | 30 | 12 | 50 | 51 | 204 | 16.0 |
| `mixed` | `turtle` | 40x40 | 1 600 | 1337 | **HORIZONTAL** | **2** | **2** | 0 | 97.5 | 1 000 | 156 | 1 800 | **6** | **300** | 12 | 50 | **138** | 276 | 25.0 |
| `mixed` | `boxy` | 40x40 | 1 600 | 555 | ROTATIONAL | **2** | 4 | 0 | 1 263.5 | **55 555** | 264 | 1 830 | 106 | 55 | **17** | **0** | 95 | **378** | 30.2 |
| `mixed` | `voluted` | 43x41 | 1 763 | 824 | ROTATIONAL | **2** | 4 | 18 | 88.8 | 778 | 286 | 2 000 | 10 | 200 | 12 | 50 | 69 | 276 | 28.2 |
| `mixed` | `collision` | 45x40 | 1 800 | 375 | ROTATIONAL | **4** | **6** | 8 | 480.4 | 9 999 | 242 | 2 420 | 76 | 100 | **17** | **0** | 63 | **378** | 14.9 |
| `mixed` | `caverns` | 44x43 | 1 892 | 229 | ROTATIONAL | **2** | 4 | 26 (**2 archons**) | 284.9 | 500 | **1 078 of 1 892** | 1 640 | 110 | 100 | 10 | 150 | 67 | 266 | **46.0** |
| `mixed` | `6147` | 45x45 | 2 025 | 234 | ROTATIONAL | **2** | 4 | 18 | 532.6 | 6 147 | 216 | 3 120 | 74 | 80 | 12 | 50 | 69 | 276 | 22.0 |
| `large` | `desert` | 62x62 | 3 844 | 3613 | ROTATIONAL | **3** | **10** | 22 | 23.5 | 1 000 | 122 | 1 440 | 64 | 40 | 17 | **0** | 35 | 350 | **75.0** |
| `large` | `space` | 65x65 | 4 225 | 1 | ROTATIONAL | **4** | 8 | 0 | 73 457.9 | **999 999** | 346 | 2 050 | 50 | 50 | 18 | 50 | 46 | 368 | 17.0 |
| `large` | `scouting` | 65x65 | 4 225 | 652 | ROTATIONAL | **1** | **2** | 22 (**all SCOUTs**) | 183.2 | 1 500 | 516 | 6 100 | 122 | 50 | 12 | 50 | **102** | 204 | 59.7 |
| `large` | `vortex` | 69x69 | 4 761 | 125 | ROTATIONAL | **3** | 6 | **41** (**1 archon**) | 43.6 | 500 | 796 | 5 120 | 256 | 20 | 12 | 50 | 46 | 276 | 20.2 |
| `large` | `wormy` | 73x73 | 5 329 | 624 | ROTATIONAL | **3** | 8 | 48 | 1 884.0 | 10 000 | 1 004 | 2 790 | 225 | 20 | **29** | **0** | 41 | 326 | 35.4 |
| `large` | `quarry` | 80x80 | **6 400** | 1257 | ROTATIONAL | **4** | 4 | 44 | 231.2 | 1 000 | **1 604** | 8 200 | 82 | 100 | 12 | 50 | 69 | 276 | 42.4 |

`mixed` (**10 maps**) is the `bc16` variant's played pool; `small` (**6**) is the pool the parity
oracle and the docker smoke run on; `large` (**6**) is reserved for a later variant and **supplies two
of the nine parity pairs**. The `mixed` pool spans the axes the doctrines argue about: **both reachable
symmetries** (nine ROTATIONAL, one HORIZONTAL); **1 080 to 2 025 squares**; **archons per side 2, 3 and
4** (four on `closequarters`/`quadrants`/`collision` = four build sites, repair fields and parts
collectors; two on six others, which makes `archon_spread` a real risk); **dens per side from 1
(`turtle`, `prisons`) to 3 (`collision`)** — the axis `den_clear_round` and `guard_ratio` argue over;
**parts from 1 640 on 110 squares (`caverns`) to 20 520 on 684 (`quadrants`), and `turtle`'s 1 800 on
SIX squares of 300 apiece**, which decides whether `archon_spread: split` is greed or necessity;
**rubble means from 71.9 (`industrial`) to 1 263.5 (`boxy`, whose extremes are untouchable), and
`caverns` with 1 078 of 1 892 squares already impassable**, which is what makes `rubble_clear` and the
SCOUT's rubble immunity matter; **first waves from round 0 to round 300**; **schedules from 9 to 17
rounds and 204 to 378 zombies**; and **neutral rosters from 0 to 26 including two neutral ARCHONS
(`caverns`)** — the whole range of `neutral_activation`. One map would rank the map, not the doctrine.

**The nine parity pairs** are the six `small` maps plus `turtle` from `mixed` and `desert` and `space`
from `large`, chosen to cover every branch of the two rules that have branches:

| pair map | what it is the only cover for |
|---|---|
| `frogger` | **VERTICAL** symmetry (chirality ≠ 1) **and** a two-symmetry map where the engine's first-wins order decides (D4) **and** a map with **zero** impassable squares, so a divergence there is a rules bug and not a pathing bug |
| `turtle` (from the `mixed` pool) | the other **HORIZONTAL** chirality case |
| `checkers` | half the map impassable at exactly rubble 200 — the `< 100` boundary from above |
| `zigzag` | rubble at **10⁶** — `clearRubble` on a value no number of actions can clear, and `0.95r − 10` at the top of the float range |
| `river` | **minimum archon separation 4.0** — the two factions start in contact, so combat, infection and corpse rubble all fire in the first fifty rounds |
| `swamp` | **one archon a side** — a single point of failure, so `DESTROYED` fires early and the mid-turn win check is exercised |
| `prisons` | **two dens only** (so `z/den` is 116, the largest per-den queue in the pool) **and neutral ARCHONs**, so activation and the archon tiebreak rung both fire |
| `desert` | **ten dens**, first wave at round **0**, and the largest archon separation (75) — the den-spawn direction and chirality caches under load |
| `space` | **8 dens on a 65×65 map at 999 999 rubble** — the stress test for the den spawn ring and for `spawnAllPossible`'s proximity-damage fallback |

`tools/convert_maps_bc16.py` writes `data/maps/bc16/<name>.json` carrying: `name`, `width`, `height`,
`random_seed`, `rounds` (3000), `symmetry` and `symmetries_found` (D4), `rubble` and `parts` as
`width × height` float arrays in `[y][x]` order **with their exact decimal values preserved**,
`initial_robots` (`[x, y, type, team]` rows **in file order**, because that order is the opening exec
order), `schedule` (the whole-map schedule, which `getZombieSpawnSchedule()` exposes to both cogs), and
`dens` (`[{x, y, spawn_dir, chirality, schedule}]` — **the pre-split per-den schedule and the two
memoised constants, computed at build time**, D3). The converter **refuses** any map that is
`armageddon`, that has unequal archon counts, that is outside 30…80 in either dimension, or whose
`getSpawnDirection` would be −1. The converted maps are **committed** and CI re-converts and
byte-diffs them. The wasm bundle gets the same directory through the existing
`--preload-file {rootDir}/data@data` flag — **no link-flag change is needed**.

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when 0) picks three *distinct* maps from
the variant's pool by successive seed-derived indices, and `(seed shr 8) and 1` decides which slot
takes side A in game 1; sides alternate each game. Seed, map names and side assignment are recorded in
results and in the replay. Map files live under `data/maps/bc16/`, so a name shared with another year
(`turtle` also exists as bc22's, `vortex` as bc22's, `maze`/`Hourglass` elsewhere) **cannot** resolve
to the wrong file; `tests/test_bc16_maps.nim` asserts it anyway.

### The year module boundary

`game_config.year` selects a `YearSpec`. Year-neutral machinery (`rng`, `fdlibm`, `sheet_common`,
`sheet`, `decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`, `match`) never
branches on the year except through `years/dispatch.nim`, whose `Session` is a Nim object **variant**
so the compiler refuses to build a half-added year. Adding 2016 is exactly what bc20–bc25 proved
adding a year to be: a new `years/bc16/` directory, a converted map set, a sprite atlas, one registry
line, one arm per dispatch `case`, and one manifest variant. **Nothing else on `main` changes**: the
seven shipped years' modules, maps, atlases, tests and manifest variants are untouched, and the shared
files this branch edits are enumerated in §Packaging. The replay header records `year` so a viewer can
never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1` — unchanged.** The wire shape is identical; only the
year-dependent *payload* differs (`year`, the map cards, `sheet_schema`, `scoring`). A new protocol id
would force every existing bc20–bc26 consumer to re-register for no change in the contract. Both
`game.protocols.player` and `game.protocols.global` continue to point at `docs/PROTOCOL.md`, which
gains a bc16 section.

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
env var takes the active year's default baseline (`bulwark` on bc16). A seat whose registration never
arrives is logged loudly and reported to `COGAME_PLAYER_FAILURE_URI`. The receive loop is wrapped in
`try/except CatchableError` and exits 0 on a dead socket (the raid 0.1.3 scar).

### Per-seat observation (the doctrine prompt payload, recorded verbatim in the replay)

This is a **sealed one-shot** game, so the observation is the whole pre-match brief and there is no
per-round observation of any kind. The example below is the real `caverns` card, measured.

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV11","year":"bc16",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","seed":774113,
 "games":[{"map":"caverns","width":44,"height":43,"symmetry":"rotational","you_are":"A",
           "rounds":3000,"rounds_are_zero_based":true,"start_separation":46.0,
           "your_archons":[{"x":6,"y":8,"rubble":0},{"x":10,"y":34,"rubble":0}],
           "enemy_archons":[{"x":37,"y":34},{"x":33,"y":8}],
           "terrain":{"rubble_mean":284.9,"rubble_max":500,"impassable_squares":1078,
                      "total_squares":1892,"squares_over_50_rubble_pct":56.9,
                      "note":"a square is passable only if its rubble is UNDER 100, except for SCOUTs, FASTZOMBIEs and BIGZOMBIEs which ignore rubble entirely; rubble of 50 or more DOUBLES every movement and cooldown charge"},
           "parts":{"squares":110,"total":1640,"max_square":100,
                    "nearest_to_you":{"x":9,"y":11,"amount":40,"steps":4},
                    "note":"only an ARCHON collects parts, and it takes the WHOLE square by standing on it or moving onto it"},
           "dens":{"count":4,"per_side":2,"health_each":2000,"bounty_each":200,
                   "locations":[{"x":0,"y":0},{"x":43,"y":42},{"x":21,"y":3},{"x":22,"y":39}],
                   "zombies_queued_each_over_the_game":67},
           "neutrals":{"total":26,"by_type":{"soldier":22,"archon":2,"viper":2},
                       "nearest_to_you":{"x":14,"y":13,"type":"soldier","steps":8},
                       "note":"an ARCHON activates a NEUTRAL within radius-squared 2 for zero parts and 2 core delay; the neutral is replaced by an identical robot on your team, immediately active. A neutral ARCHON is a whole extra tiebreak rung."},
           "zombie_schedule":[{"round":150,"standardzombie":4},
             {"round":300,"standardzombie":6,"rangedzombie":4},
             {"round":450,"standardzombie":8,"rangedzombie":4},
             {"round":600,"standardzombie":8,"rangedzombie":4,"fastzombie":4},
             {"round":900,"standardzombie":8,"rangedzombie":4,"fastzombie":4},
             {"round":1200,"standardzombie":10,"rangedzombie":6,"fastzombie":6,"bigzombie":2},
             {"round":1500,"standardzombie":10,"rangedzombie":6,"fastzombie":6,"bigzombie":2},
             {"round":1800,"standardzombie":12,"rangedzombie":8,"fastzombie":10,"bigzombie":4},
             {"round":2100,"standardzombie":12,"rangedzombie":8,"fastzombie":10,"bigzombie":4},
             {"round":2400,"standardzombie":12,"rangedzombie":8,"fastzombie":10,"bigzombie":4}],
           "schedule_note":"these are WHOLE-MAP counts, divided as evenly as possible among the 4 dens; a den spawns at most 8 zombies per attempt and 16 per round, and if it still has a queue it damages every adjacent non-zombie for 10 first",
           "tiebreak_round":2999}],
 "economy":{"start_per_team":{"parts":300},
            "income_per_team_per_round":"max(0, 2 - 0.01 * your live robot count) parts -- so income is ZERO at 200 robots and half at 100",
            "den_bounty":200,
            "map_parts":"archon-collected only, whole-square, never regenerating"},
 "units":{"…the full twelve-row RobotType table of §The game, one object per type with parts,
            build_turns, hp, attack, attack_r2 (and attack_r2_minimum 6 for the turret), the three
            delays, sight_r2, ignores_rubble, immobile and turns_into…",
          "archon":{"parts":"cannot be built","hp":1000,"attack":0,"repair_r2":24,"sight_r2":35,
                    "move_delay":2,"cooldown_delay":1,"turns_into":"bigzombie",
                    "does":"builds SCOUT/SOLDIER/GUARD/VIPER/TURRET in an adjacent square (and is FROZEN for that unit's build turns); repairs one friendly non-archon for 1 hp within r2<=24 FOR FREE, once a turn; activates NEUTRALs within r2<=2; collects parts by standing on them. LOSE YOUR LAST ARCHON AND YOU LOSE IMMEDIATELY"},
          "scout":{"parts":25,"build_turns":20,"hp":80,"attack":0,"sight_r2":53,"move_delay":1.4,
                   "ignores_rubble":true,"turns_into":"fastzombie",
                   "does":"sees further than anything else, walks through ANY rubble, cannot attack, and is the cheapest thing you can put between a den and yourself"},
          "guard":{"parts":30,"build_turns":10,"hp":145,"attack":1.5,"attack_r2":2,"sight_r2":24,
                   "does":"DOUBLE damage against zombies, and 4 damage BLOCKED off any hit above 10"},
          "viper":{"parts":120,"build_turns":30,"hp":120,"attack":2,"attack_r2":20,"infect_turns":20,
                   "does":"infects for 20 turns at 2 damage a turn; an infected robot that dies becomes a ZOMBIE instead of leaving rubble"},
          "turret":{"parts":130,"build_turns":25,"hp":100,"attack":13,"attack_r2":40,
                    "attack_r2_minimum":6,"immobile":true,
                    "does":"the longest reach in the game, but cannot shoot inside r2 6 and cannot move or clear rubble; PACK it into a TTM (10 delay on both counters) to relocate, UNPACK to shoot"}},
 "zombies":{"team":"a third team called THE HORDE; it never wins and never scores",
            "targeting":"EVERY zombie, EVERY turn, walks at the NEAREST player-controlled robot on the map, of EITHER team; zombies see the whole map always",
            "standardzombie":{"hp":60,"attack":2.5,"attack_r2":2,"move_delay":3},
            "rangedzombie":{"hp":60,"attack":3,"attack_r2":13,"move_delay":3},
            "fastzombie":{"hp":80,"attack":3,"attack_r2":2,"move_delay":1.4,"ignores_rubble":true},
            "bigzombie":{"hp":500,"attack":25,"attack_r2":2,"move_delay":4,"ignores_rubble":true},
            "outbreak":"every 300 rounds every NEWLY SPAWNED zombie's health and damage are multiplied: x1.0, x1.1, x1.2, x1.3, x1.5, x1.7, x2.0, x2.3, x2.6, x3.0",
            "den":{"hp":2000,"bounty":200,
                   "does":"spawns its share of the public schedule into up to 8 adjacent squares a turn, in a ring starting toward the nearest initial archon; if it still has a queue it damages every adjacent non-zombie for 10 and tries again"}},
 "infection":{"zombie_bite":"10 turns, no damage",
              "viper_bite":"20 turns, 2 damage a turn",
              "on_death":"an INFECTED robot leaves NO rubble and stands back up as a zombie of its own type's turns_into, on the ZOMBIE team, at the current outbreak multiplier, on the square where it fell -- and it then hunts whoever is nearest",
              "on_activation":"a NEUTRAL killed by activation leaves no rubble and never turns"},
 "rubble":{"impassable_at":100,"doubles_cost_at":50,
           "from_a_corpse":"an UNINFECTED robot's death adds its own MAX HEALTH to its square (1000 for an archon, 500 for a bigzombie, 145 for a guard) -- a third of that if a TURRET landed the killing blow",
           "clearing":"one action turns r into max(0, 0.95*r - 10); a TURRET and a TTM cannot clear; clearing a square at exactly 0 costs nothing and does nothing"},
 "signals":{"basic_per_turn":5,"message_per_turn":20,
            "message_senders":"ARCHON and SCOUT only",
            "cost":"0.05 delay on BOTH counters inside twice your own sight radius, plus 0.03 per unit beyond it",
            "queue":1000,
            "note":"there is no shared array in 2016, and EVERY signal is heard by the enemy too"},
 "win":{"instant":"destroy the enemy's LAST ARCHON",
        "at_round_2999":["more archons alive","greater total live-archon health",
                         "greater parts stockpile plus the parts cost of every live robot",
                         "higher maximum live archon id (and Clan Basil on a 0-0)"],
        "note":"there is no elimination for losing your army: a faction with one archon and nothing else plays on to round 2999 earning 2 parts a round"},
 "rules_digest":"<~8 KB condensed spec: the twelve robot types with their exact actions, delays and turns_into; the core/weapon delay pair and exactly which action sets which counter; the rubble economy; the parts economy; the public per-den zombie schedule and the outbreak ladder; the zombie AI's eight-step ladder and its targeting rule; infection and the die-and-turn conversion; free neutral activation; friendly fire being legal; and the four-rung tiebreak ladder>",
 "sheet_schema":{"…all eleven knobs, their values, ranges, defaults and notes…"},
 "scoring":{"weights":{"archons_share":64,"archon_health_share":24,"parts_net_worth_share":12},
            "win_bonus_per_game":200,"games":3,
            "note":"shares are float32; points truncate to an integer; the league ranks by ELO on match wins and results.scores is dominated by the win bonus"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards with **both** factions'
initial archon positions (they are public: `getInitialArchonLocations` is free to every robot in the
real game, `RobotControllerImpl.java:101-118`), the rubble and parts profiles with the walking distance
to the nearest deposit, **the complete den roster and the complete zombie spawn schedule** (public:
`getZombieSpawnSchedule()` is free, `:90-93`), the neutral roster by type, the seed, the full constant
tables, the knob surface with defaults, the scoring weights and the deadlines. Because every map is
symmetric, the two seats' cards are mirror images and numerically identical in every aggregate; the
only asymmetry is `you_are` and which mirrored coordinate set is labelled "yours".
**Hidden**: the opponent's doctrine, sheet, notes and motto (sealed and simultaneous — never sent, in
either direction, at any time); the opponent's real player name (only the alias); **every in-match
state** (a cog receives **no** per-round observation — one sealed doctrine, then the war); the other
seat's fallback status; and the **per-den** split of the schedule (the whole-map schedule is public,
the per-den division is not exposed by any 2016 API and is therefore not in the card). Inside a match
the fog is the robots': sight r² ≤ 24 for soldiers, guards, vipers, turrets and TTMs, r² ≤ 35 for
archons, r² ≤ 53 for scouts, and **the whole map for every zombie and every den**. Nothing else
occludes — 2016 has no clouds and no terrain vision rule, and **an attack needs no vision at all**.

### Reply schema and caps

```json
{"sheet":{"opening":"scout_zombie_pull","turret_count":1,"guard_ratio":20,
          "zombie_kiting":"always","den_clear_round":2200,
          "parts_priority":"vipers","archon_spread":"split",
          "neutral_activation":"hunt","retreat_hp":30,
          "rubble_clear":"paths","infection_policy":"suicide_squad"},
 "notes":"Two scouts stand between den (0,0) and their west archon by round 120 so the whole north wave walks at them and then at Basil. Vipers before the third soldier; anything I infect dies next to their archon.",
 "motto":"Let them meet the horde first."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | **16 KB of BYTES** (`MaxReplyBytes`, `sim_types.nim:171`), cut on a **rune** boundary by `truncateBytes` | unparseable → retry once → fallback sheet |
| the envelope | unwrapped **at most once** (`sheet`, `doctrine`, or a single object-valued key), the resolved key recorded in `seats[].sheet_envelope` | no envelope found → the payload itself is the sheet |
| `sheet` | ≤ **32** keys (`MaxSheetKeys`), each value type- and range-checked | bad field → that field's default, recorded in `sheet_defaults_applied` |
| `turret_count` (0…12), `guard_ratio` (0…100), `retreat_hp` (0…100) | integers, **clamped** to their stated ranges | out of range → clamped to the nearer bound and recorded (an integer knob is clamped, never defaulted, so "as many as possible" still means something) |
| `den_clear_round` | integer **1 … 2800** | out of range → clamped; a non-integer → the default 900, recorded |
| every enum knob (`opening`, `zombie_kiting`, `parts_priority`, `archon_spread`, `neutral_activation`, `rubble_clear`, `infection_policy`) | exactly one of its listed strings, case-folded and trimmed, `-`/space → `_` (`normalizeKey`) | unknown value → that field's default, recorded |
| an **absent** known key | takes its default and **is recorded in `sheet_defaults_applied`** (bc16 only, the envelope pin item 2) | — |
| `notes` | **280 runes** (`MaxNoteRunes`) | truncated |
| `motto` | **48 runes** (`MaxMottoRunes`) | truncated |
| unknown sheet keys recorded | ≤ **16** keys (`MaxUnknownFields`), each ≤ **40 runes** (`MaxUnknownFieldRunes`) | truncated |
| provider error text stored in the replay | **200 runes** (`MaxFallbackDetailRunes`) | truncated |
| the recorded prompt | **4000 runes** (`MaxPromptRunes`) | truncated |
| `PLAYER_POLICY_LABEL` | **48 runes** (`MaxPolicyLabelRunes`) | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary**
(`truncateRunes`/`truncateBytes`, `sim_types.nim:277-305`; the reply's 16 KB cap is measured in bytes
but is still cut on a rune boundary): byte-slicing a multi-byte character renders fine in a browser and
then fails a strict UTF-8 parser, which is exactly what makes a replay unreadable to everything but
one lenient viewer.

### Results document

The closed schema is **shared with the seven shipped years** and stays that way: `results.games[]`'s
five required keys are year-neutral (`map`, `side`, `rounds_played`, `winner`, `end_reason`), every
year-specific statistic is an optional property, and `end_reason`'s enum is the union of every year's
values.

bc16's per-game keys, each a 2-array of integers in **seat** order unless marked scalar. The four that
already exist for another year — `units_built`, `damage_dealt`, `robots_alive`, `robots_lost` — are
**reused rather than duplicated**:

`archons_start`, `archons_end`, `archons_lost`, `archon_health_end_tenths`, `parts_end_tenths`,
`parts_worth_end`, `parts_collected_tenths`, `parts_income_tenths`, `parts_spent_tenths`,
`units_built`, `scouts_built`, `soldiers_built`, `guards_built`, `vipers_built`, `turrets_built`,
`turret_packs`, `robots_alive`, `robots_lost`, `robots_turned`, `neutrals_activated`,
`neutral_archons_activated`, `dens_destroyed`, `den_damage_dealt`, `damage_dealt`,
`zombie_damage_dealt`, `zombie_damage_taken`, `enemy_damage_dealt`, `enemy_damage_taken`,
`infections_suffered`, `infections_inflicted`, `viper_infection_damage`, `repairs`, `hp_repaired`,
`rubble_cleared_tenths`, `rubble_created_tenths`, `squares_opened`, `basic_signals`,
`message_signals`, `archon_parts_walks`;
scalars `archons_per_side`, `dens_per_side`, `dens_on_map`, `parts_on_map_start`,
`parts_squares_start`, `rubble_mean_tenths`, `impassable_squares_start`, `impassable_squares_end`,
`neutrals_on_map_start`, `zombies_spawned`, `zombies_alive_end`, `zombies_killed`,
`outbreak_level_end`, `schedule_rounds`, `tiebreak_round`.

Every float64 quantity is reported in **tenths as an integer**, for the same reason `points` is: the
recorder and the wasm re-deriver must agree, and the viewer's `fmtStat` prints `x.x` (the "no raw
unrounded floats" endcard fix).

Top level, unchanged and already declared at `00c1dae`: `names`, `aliases`, `scores`, `wins`,
`points`, `games`, `seed`, `year`, `policy_kind`, `sheet_defaults_applied`, `sheet_envelope`,
`fallbacks`, `decision_ms`, `sim_seconds`, `reason`, `wall_clock_seconds`, `game_version`. **bc16 adds
no top-level key.**

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV11","year":"bc16",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":774113,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "chassis":"bulwark",
           "sheet":{…as applied…},"sheet_submitted":"{…as received, before unwrapping…}",
           "sheet_envelope":"doctrine",
           "sheet_defaults_applied":["rubble_clear"],"sheet_unknown_fields":["chassis"],
           "notes":"…","motto":"…","decision_ms":9214,
           "prompt":{ /* THE OBSERVATION, verbatim */ },
           "fallback":null,"fallback_detail":null}],
 "prompt_preamble":"…",
 "games":[{"index":0,"map":"caverns","map_json_sha256":"…","sides":["A","B"],
           "side_a_slot":0,"rounds":3000,
           "hash_chain_sha256":"…","hash_chain_rounds":"…"}],
 "plan":{"maps":[…all three drawn maps, even if the match clinched in two…],
         "side_a_slots":[…],"abandon_after":[…],"max_rounds":3000},
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI — `result`, SINGULAR, this repo's convention */ }}
```

**Self-sufficiency is by re-derivation, not by bulk.** Names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships — including its **pre-split per-den
schedules**, so the browser never has to reproduce a Java `HashMap`), both doctrine sheets **and both
submitted sheets with the envelope key that was unwrapped**, the chassis each seat drove, and the event
list are all in the file, and the wasm sim replays every round from them. **No `.rms` bytes, no
per-round robot dump, no per-square dump** — robot positions, health, types, delays, infection
counters, `roundsAlive`, the rubble and parts arrays, the stockpiles, the signal queues, the den queues
and all three RNG states are pure functions of the sim, so the browser re-derives them and the endcard
reads the re-derived totals. No server is contacted except S3 for the `.replay` file. The per-round
hash chain lets the viewer prove its re-derivation matches the recording (`bc_mismatch_round`, surfaced
as `data-replay-mismatch-round` and in `#mmwarn`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round` (**0-based**, as the engine's
are). **Every event kind is bounded per game** — a 3000-round match with 300 robots on the board cannot
be allowed to emit an event per action — and every one has a beat kind with CSS (§Viewer). **No event
has a field named `kind`**: `first_action`'s field is `action` (the bc23 r1-F25 lesson).

| `kind` | fields | bound | beat | drawn as |
|---|---|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | 1 | — | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | 4 | — | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `envelope`, `defaults_applied`, `unknown_fields` | 2 | `doctrine` | feed line |
| `doctrine_retry` | `slot`, `cause` (`timeout`\|`parse`\|`throttled`\|`transport`) | 2 | — | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | 2 | `doctrine` | feed line (red) |
| `game_start` | `game`, `map`, `width`, `height`, `sides`, `archons`, `dens`, `parts_on_map`, `neutrals`, `schedule_rounds` | 1/game | `game` | beat + feed |
| `first_action` | `game`, `round`, `alias`, **`action`** (from `Bc16ActionNames`) | 2/game | `build` | beat + feed |
| `unit_milestone` | `game`, `round`, `alias`, `unit` (from `Bc16UnitNames`), `total` — the **first** of each of the five buildable types per side | ≤ 10/game | `build` | beat + feed |
| `zombie_wave` | `game`, `round`, `counts` (4-array by zombie ordinal), `dens_spawning`, `outbreak_level` — **one per scheduled round**; the measured maximum schedule length on any pool map is 29 | ≤ 30/game | `wave` | beat + feed |
| `outbreak` | `game`, `round`, `level`, `multiplier_permille` — one per 300 rounds | ≤ 10/game | `outbreak` | beat + feed |
| `den_destroyed` | `game`, `round`, `alias`, `x`, `y`, `bounty`, `dens_left`, `queue_deleted` | ≤ 12/game | `den` | beat + feed |
| `neutral_activated` | `game`, `round`, `alias`, `unit`, `x`, `y`, `total` — the first six per side and then every fourth | ≤ 20/game | `activate` | beat + feed |
| `infection` | `game`, `round`, `alias`, `victim_unit`, `source` (`viper`\|`zombie`), `turns` — the first per side and then every tenth | ≤ 20/game | `infect` | beat + feed |
| `turned` | `game`, `round`, `alias`, `unit`, `became`, `x`, `y`, `outbreak_level` | ≤ 24/game | `turned` | beat + feed |
| `archon_lost` | `game`, `round`, `alias`, `archons_left`, `cause` (`zombie`\|`enemy`\|`infection`\|`den_proximity`\|`disintegrate`) | ≤ 8/game | `archon` | beat + feed |
| `rout` | `game`, `round`, `alias`, `lost` — a round in which one faction lost ≥ 5 robots | ≤ 20/game | `rout` | beat + feed |
| `duel` | `game`, `round`, `lost` (2-array) — a round in which **both** factions lost at least one attacker | ≤ 20/game | `duel` | beat + feed |
| `tiebreak` | `game`, `round`, `rung` (from `Bc16RungNames`), `archons` (2), `archon_health_tenths` (2), `parts_worth` (2) | ≤ 1/game | `end` | beat + feed |
| `game_end` | `game`, `round`, `winner_alias`, `winner_slot`, `end_reason`, `points`, `archons` | 1/game | `end` | beat + feed |
| `game_abandoned` | `game`, `round`, `map` | ≤ 1/game | `end` | beat + feed |
| `episode_end` | `reason` | 1 | — | endcard |

**Thirteen beat kinds** (`doctrine`, `game`, `build`, `wave`, `outbreak`, `den`, `activate`, `infect`,
`turned`, `archon`, `rout`, `duel`, `end`), and **all thirteen are emitted by the committed fixture
replay** so the beat test in §Viewer is a real gate and not a CSS inventory. The whole event list for a
three-game match is at most **a few hundred entries** (worst case `3 × (1+2+10+30+10+12+20+20+24+8+20+20+1+1+1) = 540`
plus 11 pre-match), and `tests/test_bc16_replay.nim` asserts each per-kind bound so a pathological game
cannot produce a 20 MB replay.

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by the build hook **`tools/build_replay_viewer.sh`** (unchanged — same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module**, now including `years/bc16/`, compiled to wasm; the browser re-derives every round from the
replay's events, config and seed. No pod, no live viewer route, no `.rms` bytes, no 2016 Java Swing
client.

### All four viewer files come from ONE starter: `Metta-AI/cogame-battlecode` (its own shipped viewer)

The viewer is **extended, never replaced**. Lineage: `coworld-ctf` (paintbot) → `cogame-battlecode` →
here. **All four bundle files come from that one starter — `Metta-AI/cogame-battlecode` — and never a
mixture**, because splicing one starter's shell onto another's emscripten link flags
(`MODULARIZE`/`EXPORT_NAME` vs an `onRuntimeInitialized` bootstrap) deadlocks the viewer silently with
every file present and 200 (cogame-lantern, 2026-08-23).

| bundle file | source (all from `Metta-AI/cogame-battlecode`) | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `cogame-battlecode/replay-viewer/config.nims` | **unchanged, byte for byte.** `--preload-file {rootDir}/data@data` already carries the whole `data/` tree, so `data/maps/bc16/`, `data/bc16/tables.json` and `data/atlas_bc16.*` need no flag change. `EXPORTED_FUNCTIONS` is unchanged (no new export). **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as they are, including `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-O2`, `--mm:arc`, `--exceptions:goto` and `-d:useMalloc`. |
| the wasm entry `replay-viewer/bc_replay.nim` | `cogame-battlecode/replay-viewer/bc_replay.nim` | extended in place: the same exports (`bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`), the same `stageNote` OOM buffer and the same `emscripten_exit_with_live_runtime` main. It reads the replay header's `year` and steps that year's sim through `years/dispatch.nim`. **No new export, no new bootstrap.** |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `cogame-battlecode/replay-viewer/…` | **unchanged loader.** The worker keeps its bootstrap exactly: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file. **No edit at all is needed for bc16**: the page already sets `document.documentElement.dataset.year` from the frame's `s.year` in the shared block, so a new year switches itself on. |
| `index.html` | `cogame-battlecode/client/replay_broadcast.html` | the **existing page with a bc16 game block appended**, assembled by the same `sed` marker substitution already in `Dockerfile.replay-viewer` (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Nothing is rewritten and **no existing id is reused for a different purpose** (the cogame-gridlock 2026-08-23 scar). |

Also unchanged and **byte-for-byte**: **`client/chrome_common.js`** is **copied byte-for-byte** into
the bundle, and so is **`client/broadcast_core.js`**; their sha256 is asserted against the
`coworld-ctf` copies in `tests/test_viewer.nim`, and that assertion stays green because neither file
is touched. `wire_constants.js` is regenerated from the sim by `tools/gen_wire_constants.nim`, as
today.

**Load signalling** (unchanged from the starter, restated because it is a checklist item):
`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on the
**first drawn frame** — the worker's `loaded` message after the first board frame is composited, never
on rAF timing at the call site (the chorus 2026-08-24 scar) — and the `coworld-replay` bridge posts
`ready` from a callback fired **after** that attribute is set. On any failure — fetch, JSON parse, an
unknown `game_version`, a wasm abort, or a hash mismatch that prevents rendering — it sets
**`data-replay-error="<message>"`** on `<html>` and shows the failure card.

### The appended bc16 game block

**No starter element is removed from the page.** The bc26 block's ids (`#coopchip`, `#bars`,
`#gamechips`, `#econ`, `#doctrines`) and the bc20/bc21/bc22/bc23/bc24/bc25 blocks' (`#bc20-flood` …
`#bc25-srp`, 41 ids in all) all stay exactly where they are. **What bc16 removes is nothing from the
page and everything from the screen**: like every other year block it appends
`html[data-year="bc16"] #coopchip, … #bc25-srp { display: none !important }` for those 41 ids and
`html:not([data-year="bc16"]) #bc16-… { display: none !important }` for its own **seven**, so on a
bc16 replay exactly the bc16 set plus the shared chrome is visible. The bc16 ids are all new and all
prefixed:

- `#bc16-archons` — **the headline readout, and the year's whole story**, in the same top-centre pill
  slot bc22 uses: a two-sided archon tally `ASH ▲▲ 2 — 3 ▲▲▲ BASIL` with a health pip per archon that
  drains as it is shot (1000 HP each), a **green ring** on any archon that is zombie-infected and a
  **violet ring** on any that is viper-infected, and it **flashes red when an archon dies**, because
  that is the only event that can end the game.
- `#bc16-horde` — **the year's signature readout, and the one no other year has**: the horde clock. In
  the top band beside the archon pill: zombies alive by type
  (`◆12 ➤6 ⚡4 ●1`), the **next scheduled wave, its composition and how many rounds away**
  (`WAVE 12+8+10+4 in 37`), the **outbreak level and multiplier** (`OUTBREAK 5 — ×1.7`), **dens
  standing** (`DENS 4`) and the tiebreak countdown (`ROUND 2999 — 412 to go`). On a wave round it takes
  over the strip for two seconds with what happened in plain words
  (`WAVE — 34 zombies from 4 dens at ×1.7`), and on a `turned` event with
  (`CLAN ASH'S ARCHON TURNS — a BIGZOMBIE at 34,19`), which is the single most watchable thing in this
  year. It **keeps its wave composition and its countdown at every width**, including 360 px.
- `#bc16-econ` — per faction: parts banked (integer), income per round (`2 − 0.01 × units`, printed as
  `x.x`), parts still on the map, **dens destroyed and the bounty collected**, neutrals activated (and
  how many of them were ARCHONs), and **impassable squares on the map now vs at round 0** — the rubble
  story, made visible.
- `#bc16-units` — per faction: the six player-type census with archons emphasised, **units still
  building** shown separately (a soldier is inert for 12 turns and a viper for 30), **units infected**,
  and robots lost / robots turned.
- `#bc16-doctrines` — both sheets in plain words, **dismissible**: a `#bc16-doctrines-close` button
  with `aria-label="Dismiss doctrines"`, an `Escape` binding, self-dismissal on the first playback
  advance (or after six seconds for a viewer who never presses play), and a `#bc16-doctrines-toggle`
  chip in the scorebug that re-opens it. Its body is **capped and scrolls** (the bc23/bc25
  doctrine-card clipping finding), and it sits above the board area and **never** inside the transport
  band. It carries the **submitted-vs-applied badge** the envelope pin requires.
- `#bc16-siege` — the endcard panel (below).

Year selection is one attribute plus CSS, not a rewrite: the shared `onText` block already sets
`document.documentElement.dataset.year` from the replay header and re-runs `relayout()` on a change
(`client/replay_broadcast.html:6329`); the stylesheet extends the existing
`html:not([data-year="bc22"]) #bc22-… { display: none !important }` pattern with the bc16 pair.
**Every bc16 rule — including every beat-marker colour — is scoped to `html[data-year="bc16"]`** (the
bc21 r1-F4 fix, kept), so none of them can restyle another year's marker of the same name. The frame
hook is `window.Bc16Block.active(s)` / `.onFrame(s)`, added beside the existing six in the shared
`onText`, and the `if (!isBc20 && !isBc21 && !isBc22 && !isBc23 && !isBc24 && !isBc25)` guard becomes
`if (!isBc16 && !isBc20 && !isBc21 && !isBc22 && !isBc23 && !isBc24 && !isBc25)`.

### The beat contract — emission, label and style, all three tested

This is where the bc25 run failed review (r1-F26: eleven beat-kind CSS rules against two emitted
kinds), so it is specified as three obligations that **one** test asserts together against the
**committed fixture replay** (`tests/fixtures/replay-bc16.json`):

1. **Emission.** `beatsFor` in `src/battlecode/broadcast.nim:139` is the only place a beat kind is
   decided. bc16 adds `let isBc16 = doc.year == "bc16"` beside the three that are already there
   (`:145-147`) and an arm for each of its event kinds. **Four names collide with other years and each
   needs the year test**: `first_action` (bc22/bc23/bc25 map it to `build`; bc16 joins them),
   `rout` (same three; bc16 joins), `duel` (bc22's and bc23's; bc16's carries the same field name with
   a different meaning — attackers lost, not launchers — so the **label** switch gains a year test),
   and **`archon_lost`**, which bc22 already emits with `gold_dropped` where bc16 carries `cause` — so
   the label switch gains a year test there too. The bc16-only kinds (`zombie_wave`, `outbreak`,
   `den_destroyed`, `neutral_activated`, `infection`, `turned`, `unit_milestone`, `tiebreak`) need no
   discriminator, because no other year emits those event names — even though two of their beat kinds
   (`build`, `end`) are spelled the same as another year's, which is exactly why the CSS scoping is
   mandatory.
2. **Label.** Every emitted beat carries a spectator-readable label built in the same `case` — e.g.
   `"WAVE — 34 zombies from 4 dens at ×1.7, game 2, round 1800"`,
   `"Clan Ash breaks the den at 0,0 — 200 parts and 43 zombies deleted, game 1, round 912"`,
   `"OUTBREAK 5 — every new zombie is 1.7× stronger from here"`,
   `"Clan Basil activates a neutral ARCHON at 21,14 — it has four now"`,
   `"CLAN ASH'S SOLDIER TURNS — a STANDARDZOMBIE at 34,19, and it is hunting Basil"`,
   `"ARCHON DOWN — Clan Ash has 1 left, killed by a BIGZOMBIE"`,
   `"ROUND 2999 — archons level at 2, Clan Basil wins on archon health 1740 to 1155"` — and it becomes
   the `<button>`'s `aria-label` and `title`. Every label is ≤ 120 runes.
3. **Style.** `client/replay_broadcast.html` ships a `.beat-marker.<kind>` rule for **all thirteen**
   kinds, every one scoped to `html[data-year="bc16"]`: `.doctrine`, `.game`, `.build`, `.wave`,
   `.outbreak`, `.den`, `.activate`, `.infect`, `.turned`, `.archon`, `.rout`, `.duel`, `.end`. Six of
   those names already exist for other years (`doctrine`, `game`, `build`, `archon`, `rout`, `duel`,
   `end` — seven, in fact), which is exactly why the scoping is mandatory; six are new (`wave`,
   `outbreak`, `den`, `activate`, `infect`, `turned`).

`tests/test_bc16_beats.nim` loads the committed fixture, calls `beatsFor`, and asserts: **at least 26
beats over at least 10 distinct kinds**, every beat's label non-empty and ≤ 120 runes, every emitted
kind present in the thirteen-kind vocabulary, and — reading the page source — a
`html[data-year="bc16"] .beat-marker.<kind>` rule for **every kind the fixture actually emitted** (not
for every kind in a hand-written list). `tools/gen_bc16_fixture_replay.nim` is written to produce all
thirteen kinds, and the test fails if the fixture stops doing so.

### The killfeed/stat-box rule: keep the fix armed, do not re-fix it

The `--statrail` repair is already in the tree: `relayout()` measures the union of the *visible* year
stat boxes into `--statrail` (`client/replay_broadcast.html:6210-6220`), `#killfeed`'s `bottom` is
`max(calc(76 * var(--u)), calc(var(--band, 0px) + var(--statrail, 0px) + 8px))` (line 1270),
`tests/test_viewer.nim` asserts both statically, and `viewer_smoke.mjs --killfeed-overlap` measures
client rects at 360 / 720 / 1280 px at FIT and 2× zoom on every year's replay. **What bc16 must do —
and it is the whole of the work here:**

1. add **`bc16-econ` and `bc16-units`** to `relayout()`'s measured id list, beside the thirteen already
   there. (`#bc16-archons` and `#bc16-horde` are **top**-band pills and are deliberately not in the
   rail set.)
2. run the existing `--killfeed-overlap` gate **on the bc16 replay too**, at all three widths and both
   zooms — eight replays, one loop in `ci.yml`;
3. keep the negative control the bc21 r1 fix shipped: the gate's own self-test breaks the rule and
   asserts the gate goes red, so an eighth year cannot quietly disarm it (the 2026-09-04 learning
   about `page.evaluate` IIFEs and gates that look armed and test nothing).

### Zoom: KEEP `#viewpanel`

**Decided: `#viewpanel` (the zoom bar + minimap) is KEPT.** The reason is the map sizes and it is not
close. The `bc16` variant's played pool spans **36×30 to 45×45** and the reserved `large` pool reaches
**80×80**; the native board render is 16 px per square, so **480 px to 1280 px wide** — every single one
of them **larger than the 360 px featured-match frame**, where a 45-wide board gives 8 px per square
and an 80-wide board gives 4.5. A fixed arena would drop the panel; this is not one. So the inherited
`#viewpanel` is kept and wired to the same `zoomAt/setZoom/panBy/panTo/resetView` core API the worker
already forwards, with `?viewpanel=0` still honoured for thumbnail capture. The default view is
fit-to-board, so a spectator who touches nothing sees the whole map, both factions' archons, every den
and every parts pile at once — which in this year is the right default, because the story is *where
the dens are and who is standing between them and the archons*.

### Transport rules

- `relayout()` (inherited, kept, extended only with the two new boxes in the `--statrail` set) sets
  **`--hudscale`**, **`--topband`**, **`--band`** and **`--statrail`** on **`:root`**, iterating to a
  fixed point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and the bottom band (transport). `#bc16-archons`, `#bc16-horde`, `#bc16-econ`,
  `#bc16-units`, `#bc16-doctrines` and `#bc16-siege` are all explicitly positioned above
  `var(--band)`; the horde strip's wave timeline sits **immediately above** `var(--band)`, never
  inside it.
- **The endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`, built by a
  bc16-block function with its **own** name, **`buildBc16BeatButtons`** — never `markBeat` (the tandem
  2026-08-23 hoisting collision) and never colliding with `buildBeatButtons` (bc26),
  `buildBc20BeatButtons`, `buildBc21BeatButtons`, `buildBc22BeatButtons`, `buildBc23BeatButtons`,
  `buildBc24BeatButtons` or `buildBc25BeatButtons`. The spoiler gate is honoured by
  `applyBc16BeatSpoilers`, the same shape as the other six blocks.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
  `#btn-end`, `#btn-loop`, `#btn-skip`, `#btn-spoilers`, `#speedchips`, `#tick-clock`, `#win-chip`,
  `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Playback pacing — check 8 must be dispatched with `settle=20000 soak=15`

bc21 taught this: a compute-heavy year defeats a fixed-wait scrub probe, because the Worker
re-simulates from the start of the game on every seek and a 700 ms settle expires first
(`loaded:true`, viewer healthy, instrument too impatient). **bc16 is the most exposed year this repo
has**: it is **3000 rounds, 50 % longer than any other year**, at an estimated **2–5 ms/round** with a
budgeted 300 robots on the board (§The game), so a 100 % seek re-simulates 6–15 s of native work in a
wasm Worker. So, decided here rather than discovered at phase 60: **the phase-60 check-8 dispatch for
bc16 uses `settle=20000 soak=15`**, and `ci.yml`'s `wasm-viewer` job runs `viewer_smoke.mjs` with
**`--timeout 120 --soak 15`** on the bc16 replay (joining bc22/bc23/bc24/bc25; bc26/bc20/bc21 keep
`--timeout 90 --soak 10`). The `docker-smoke` step prints `sim_seconds / rounds` and
`docs/RULES-BC16.md` records the measured value.

**The scrub selector needs no change.** `tools/ci/viewer_smoke.mjs` in this repo already resolves
`#scrub` before `#seek` before `input[type="range"]`, **one selector at a time** (`:609,616`) and
excluding `#zoom-slider`, and `ci.yml` asserts `scrub_selector == "#scrub"` after every run. And
**`canvas_text.total: 0` on this renderer is not a pass signal** (LEARNINGS 2026-09-08): the
text-bounds check covers nothing here, which is why `--strict-text-bounds` is dropped on the replay
runs and applied instead to `tools/ci/renderer_fixture.html`, where the text is real (§Tests).

### Art

`data/atlas_bc16.png` + `data/atlas_bc16.json` (≈ 140 KB, committed), cut by
`tools/build_sprite_atlas_bc16.py` from the **official 2016 client's** sprite tree
(`battlecode/battlecode-client-2016`, GPL-3.0, pinned at `317e1f3f`,
`src/main/battlecode/client/resources/art/`). **Measured: the upstream set is 92 PNGs, and it carries
exactly what this year needs — `{archon,scout,soldier,guard,viper,turret,ttm,zombieden,standardzombie,rangedzombie,fastzombie,bigzombie}{0,1,2,3}.png`,
i.e. all twelve robot types at all four `Team` palettes (0 = A, 1 = B, 2 = NEUTRAL, 3 = ZOMBIE)** —
plus `creep.png` (the rubble texture), `hatch_attack.png` / `hatch_sensor.png`, `numbers.png` and an
8-frame `explode/` sequence. Because the client ships a **NEUTRAL palette of every type**, this is the
first year in the repo whose art can show a neutral robot as itself rather than as a greyed team
sprite — which matters, because `neutral_activation` is a headline knob. Palette follows the client's
own team colours — **blue = side A, red = side B, green = the horde, grey = neutral** — and because
sides alternate each game the scorebug plate keeps the *alias* constant and recolours its swatch per
game. Licence is recorded in `NOTICE` (§Packaging), naming the source repository, its commit, its
GPL-3.0 `COPYING` and the exact directory the sprites came from.

Board rendering (`render.nim`): the **rubble heat layer is drawn first**, because rubble is this year's
terrain and a spectator who cannot see it cannot understand why a soldier is standing still. It is a
**six-step ramp with a hard break at the two thresholds that matter**: bare ground (0), light (1–49),
**heavy (50–99, drawn with a diagonal hatch because it doubles every cost)**, **impassable (100–999,
drawn as a solid block)**, **wall (1000+, drawn as a solid block with a heavier border)** and
**bedrock (≥ 10 000, drawn near-black — `zigzag` and `space` reach 10⁶)**; the exact value is in the
tooltip and a legend chip sits in `#bc16-econ`. Parts squares carry a pip **sized by amount with the
number printed at ≥ 12 px per square**, and go hollow the moment an archon takes them, which is how a
spectator sees an `archon_spread: split` faction eating the map. Robots are drawn by type at the four
team palettes with a health bar, a **build-progress hatch** while `!isActive()` (a viper is inert for
30 turns — the single most confusing thing on screen without it), an **infection ring** (green for a
zombie bite, violet for a viper bite, with the remaining turn count at ≥ 20 px per square), and a
**pack indicator** on a TTM. A den draws a **queue badge** with the number of zombies it is holding, so
`den_clear_round` is legible. A wave round draws a two-second amber wash from each spawning den; a
`turned` event draws a one-second green flash on the square and an arrow to the victim's own archon,
which is the frame that makes `infection_policy` make sense.

### Readouts, 360 px and the endcard

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is **checked at that
width**, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, word labels hidden
under 640 px, `#viewpanel` shrinking to its minimum before anything else, and the `#bc16-*` boxes
dropping their word labels to glyphs under 640 px; **`#bc16-horde` keeps its wave composition, its
outbreak multiplier and its countdown at every width**, because it is the readout that makes the year
make sense).

- `#scorebug`: both faction plates — `CLAN ASH` over the real player name (`daveey`) and the motto —
  the live points number, and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 1412 / 2999`, `game 2 of 3 — caverns`.
- `#bc16-archons`, `#bc16-horde`, `#bc16-econ`, `#bc16-units` as above.
- `#board`: the rubble heat layer, parts with numbers, every robot with type, team, health, build
  progress and infection state, and every den with its queue.
- `#bc16-doctrines`: each sheet in plain words ("holds its archons together behind a guard wall",
  "wants three turrets standing", "45 % of its army is guards", "kites zombies with everything ranged",
  "breaks a zombie den at round 900", "spends parts on units first", "spreads its archons", "activates
  a neutral it passes", "pulls a unit out at 35 % health", "clears rubble to open the routes it needs",
  "walks its infected units away from its own archons"), plus the capped `notes`, the
  **submitted-vs-applied badge**, and a fallback badge when a seat's doctrine came from the fallback
  sheet. Dismissible, capped and scrolling.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured), and
  provably clear of the stat boxes at every width and zoom.
- `#endcard`: winner alias **and** real name; the win condition in plain words; the per-game score
  line; and `#bc16-siege`, the **war panel**: per faction, archons started / lost / left and how they
  died; parts collected, banked and spent, and the income they were losing to army size; units built by
  type and how many were still building when the game ended; dens destroyed and the queue that deleted;
  neutrals activated (with neutral ARCHONs called out); **infections suffered and inflicted, and how
  many of your own units stood back up on the horde's side**; damage dealt to and taken from the enemy
  and the horde, separately; rubble cleared and rubble created; and the **tiebreak ledger** — all four
  rungs with both sides' numbers and which one decided it. Nothing about archons, parts, rubble, dens or
  zombies is stored in the replay: the wasm sim re-derives every round.

**The endcard's five known template defects are fixed for bc16, not inherited broken** (bc23's and
bc25's phase-60 verifications found them; bc22 fixed four for every year and this run keeps them armed
and adds the fifth). Each is asserted by `tests/test_viewer.nim` (§Tests item 27):

1. **This year's nouns, not bc26's.** bc16's row in the `data-year` noun table (`:6086`) is
   `bc16: { unit: 'archon', units: 'archons', res: 'parts' }`, and the phrase table adds `zombie`,
   `den`, `horde`, `rubble`, `neutral`, `scout`, `soldier`, `guard`, `viper`, `turret`. **No "rat",
   "cheese", "king", "lead" or "gold" appears on a bc16 card.**
2. **No clipping or overflow at 1280×800.** The war panel's grid is
   `max-height: calc(100vh - var(--band) - var(--topband) - 24px)` with `overflow-y: auto` on the body
   only, and `viewer_smoke.mjs --killfeed-overlap` asserts
   `#endcard.scrollHeight <= #endcard.clientHeight` at **1280×800** after the 100 % seek. **bc16 is
   checked at 1280×800 AND at 360 px wide.**
3. **No raw unrounded floats.** Every printed number goes through one `fmtStat(value, kind)`
   formatter — integers as integers, tenths as `x.x`, percentages as `NN %`, `points`/`scores` as
   **integers** — and a `/\d\.\d{3,}/` grep of the rendered text fails the test. That is why every bc16
   float statistic is reported in **tenths as an integer**.
4. **No empty mottos and no "a accelerating"-class grammar.** A blank `motto` renders **nothing**, and
   **`plainWords16()` has no article concatenation anywhere** — every knob value maps to a complete
   clause.
5. **No HUD bleed-through.** `#endcard` is opaque over the board and the `#bc16-*` boxes are
   `visibility: hidden` while it shows (the bc23 finding).

---

## Packaging

- **`compose.yaml` — unchanged.** Service names are load-bearing (`game` → `{{GAME_IMAGE}}`, `player`
  → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar), `platform: linux/amd64`,
  `build: {context: ., network: host}`. One image, two entrypoints.
- **`Dockerfile` — unchanged in shape.** The nimby recipe builds `/bin/battlecode` and
  `/bin/battlecode-player` from one image and copies `data/` (now carrying `maps/bc16/`,
  `bc16/tables.json` and `atlas_bc16.*`). **No JDK, no JRE, no Java, no Node in any runtime stage** —
  the 2016 engine's toolchain exists only in the `parity-oracle-bc16` CI job.
  `Dockerfile.replay-viewer` is unchanged except that its `sed` block emits the bc16 game block along
  with the other seven.
- **`coworld_manifest_template.json`:**
  - `game.name = "battlecode"` (== the secret namespace == the slug), unchanged.
  - `game.description` — one sentence appended: *"Variant `bc16` is 2016 'Zombie Invasion' — archons
    build soldiers, guards, vipers, turrets and scouts and collect parts while zombie dens spawn
    escalating waves on a public schedule, every kill by a zombie stands the victim back up on the
    horde's side, and every uninfected corpse becomes a wall; win by destroying the enemy's last
    archon, or by having more of them at round 2999."*
  - `tags` unchanged (already four: `battlecode`, `strategy`, `mixed-motive`, `wasm`).
  - `game.config_schema`: `year.enum` becomes
    `["bc26","bc20","bc21","bc24","bc25","bc23","bc22","bc16"]` — **appended, so no existing index
    moves**. **`maxRounds` becomes `{minimum: 50, maximum: 3000}`** — the one bound this run widens
    (was 2000), because bc16 plays 3000; no shipped variant's value changes and
    `tests/test_manifest.nim` asserts the new bound and that every shipped variant is inside it.
    `pool.enum` unchanged; `gamesPerMatch` keeps `maximum 3`, `perGameBudgetSeconds` `maximum 300`
    (bc16 uses 120), `matchBudgetSeconds` `maximum 600` (bc16 uses 360), and the four millisecond
    bounds are unchanged with bc16 inside all of them. `tokens` stays **declared and required** (the
    runner injects it — the 2026-09-03 lesson); every array keeps `minItems`/`maxItems`; **no
    runner-managed `tokens` values inside any `game_config`**; `additionalProperties: false` stays.
  - `game.results_schema`: bc16's optional properties added beside the other years' (§Server, Results
    document); `games.items.required` unchanged (the five year-neutral keys); **`end_reason`'s enum
    extended with exactly THREE values — `archons_destroyed`, `more_archon_health`,
    `more_parts_net_worth`.** `more_archons` (bc22's), `highest_id` (bc20's) and `abandoned` are
    **already there and are reused**; `zombified` and `cleansed` are **not added** (armageddon-only,
    V4); `resignation` is **not added** (unreachable). Top-level `required` is unchanged —
    `sheet_envelope` is already in it.
  - `game.protocols` — **both** keys, unchanged:
    `player` and `global`, each
    `{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — **`readme`** = `{"type":"uri","value":".../blob/main/README.md"}`; **`pages`** gains
    one entry and keeps the nine it has: `rules.md`, `rules-bc20.md`, `rules-bc21.md`, `rules-bc22.md`,
    `rules-bc23.md`, `rules-bc24.md`, `rules-bc25.md`, **`rules-bc16.md`** (*Battlecode 2016 "Zombie
    Invasion": rules, knobs and divergences* → `docs/RULES-BC16.md`), `replay.md`, `parity.md`
    (→ `docs/PARITY.md`, which gains a bc16 section). **Ten pages**, every one a
    `{id, title, content: {type, value}}` object.
  - **`player[]` — UNCHANGED. No entry is added.** It stays exactly `[awu, scaffold]`, the two ids
    `certification.players` seats; only their `description` strings are extended to name the bc16
    resolution ("…, bulwark on bc16" / "…, greenhorn on bc16").

  **The cross-check the bc20 run paid a release dispatch to learn, done explicitly here.** The
  certifier's `players-run` step requires **every** declared `player[]` entry to occupy a slot in
  `certification.players`, and it also requires
  `len(certification.players) == certification.game_config.num_agents`. With **`num_agents = 2`** there
  are exactly **two** cert slots, they are filled by `awu` and `scaffold`, and therefore **`player[]`
  may contain exactly those two ids and nothing else**. Adding `battlecode-bc16-bulwark` or any other
  year-specific runnable to `player[]` would fail the release with `players_missing` (LEARNINGS
  2026-09-04). It is also unnecessary: `PLAYER_SCRIPTED` resolves **per year** in
  `src/battlecode/baselines.nim`, so seating `awu` on a bc16 episode already plays `bulwark` and
  seating `scaffold` already plays `greenhorn`. The scripted bc16 policies reach the league through
  `tools/ci/policies.json`, which is a *policy* list and has nothing to do with `player[]`.
  `tests/test_manifest.nim` asserts all three facts (`player[]` ids == `certification.players` ids;
  `len(certification.players) == certification.game_config.num_agents`; `num_agents` present in every
  variant's `game_config` and absent at every variant top level), so the contradiction cannot be
  re-introduced silently.

  **Variants — one per Battlecode year. `num_agents` is 2 in every one of them, and it is the only
  seat count in this note:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | unchanged | **2** |
  | `bc20` | Battlecode 2020 — Soup (2 seats) | unchanged | **2** |
  | `bc21` | Battlecode 2021 — Campaign (2 seats) | unchanged | **2** |
  | `bc24` | Battlecode 2024 — Breadwars (2 seats) | unchanged | **2** |
  | `bc25` | Battlecode 2025 — Chromatic Conflict (2 seats) | unchanged | **2** |
  | `bc23` | Battlecode 2023 — Tempest (2 seats) | unchanged | **2** |
  | `bc22` | Battlecode 2022 — Mutation (2 seats) | unchanged | **2** |
  | `bc16` | Battlecode 2016 — Zombie Invasion (2 seats) | `year: "bc16"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `maxRounds: 3000`, **`num_agents: 2`**, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 120`, `matchBudgetSeconds: 360`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  `bc16`'s variant description: *"Best of three on the mixed pool, three thousand rounds each. Archons
  are the only thing that matters: lose your last one and you lose on the spot. They build soldiers,
  guards, vipers, turrets and scouts out of parts they collect by walking over them, and they repair
  one wounded robot a turn for free. Zombie dens spawn escalating waves on a schedule both sides can
  read from round zero, and every three hundred rounds the zombies get stronger. Anything a zombie or a
  viper bites is infected, and anything that dies while infected stands back up on the horde's side —
  so a soldier you lose in their half is a zombie hunting them. Anything that dies uninfected leaves a
  wall of rubble where it fell. At round 2999 the side with more archons wins."*

  `num_agents` lives **inside each variant's `game_config`**, never at the variant top level
  (`CoworldVariant` is `additionalProperties: false` and rejects a variant-level `num_agents` —
  cogame-goofspiel-oshi-zumo 0.1.0, 2026-08-26).

  **The `<SEATS>` cross-check, named explicitly.** `.github/workflows/ci.yml` substitutes
  **`<SEATS>` = 2** into the `docker-smoke` job, and `tools/ci/docker_smoke.sh` takes the seat count
  **solely** from `certification.game_config.num_agents`, hard-failing with `SEAT-COUNT FAIL:` if the
  workflow's value disagrees — and it also refuses a `SMOKE_CONFIG_OVERRIDE` that tries to change
  `num_agents` (`docker_smoke.sh:176-201`). Since the cert fixture keeps `num_agents: 2` and the bc16
  variant declares `num_agents: 2`, the two independent declarations agree. **There is exactly one
  number in this note and it is 2.**

  **Certification fixture — UNCHANGED, and stays on `bc26`.** `certification.players` remains
  `[{"player_id":"awu"},{"player_id":"scaffold"}]` and `certification.game_config` keeps
  `"year": "bc26"`, **`"num_agents": 2`** and its existing fast settings (`pool: small`, `seed: 1`,
  `gamesPerMatch: 1`, `maxRounds: 400`, `attempt1Ms: 4000`, `retryMs: 2000`, `doctrineBudgetMs: 9000`,
  `perGameBudgetSeconds: 40`, `matchBudgetSeconds: 45`, `connectTimeoutMs: 15000`). There is **no bc16
  certification fixture in v1** (§Out of scope): certification is the platform's contract check, it
  already passes on bc26, and re-pointing it at a brand-new year module would put the release at the
  mercy of the newest code for no gain. bc16 is proven instead by its own `docker-smoke` episode
  (§Tests), which produces a real bc16 replay that the `wasm-viewer` job then executes.

- **Version bump semantics.** This ships as a **minor version bump of the same coworld** —
  **`0.7.0 → 0.8.0`** — because it adds a variant, adds optional results properties and widens one
  schema bound without changing any existing *rule*. `GameVersion` goes **`GV10 → GV11`** and
  `ReplayCompatibleGameVersions` is **extended** to
  `["GV04","GV05","GV06","GV07","GV08","GV09","GV10","GV11"]`, so every hosted
  bc20/bc21/bc22/bc23/bc24/bc25/bc26 replay keeps rendering (the bc20 learning: extend, never reset,
  and claim the version across branches with `tools/ci/check_gameversion.sh`). **This run makes no
  year-neutral behaviour change at all** — the envelope resolver, the results shape and the replay
  shape are already what bc16 needs — so no recorded byte anywhere changes meaning. The release is
  dispatched through the existing `coworld-release.yml` with the same step order (build → certify →
  upload-policies → upload-coworld → secret put). **Certify runs against bc26, exactly as before**, and
  `release-result.json` must still show `canonical: true` and `certify.replay_liveness` containing
  `skipped (static replay bundle declared`.

- **Branch discipline.** All work lands on the branch **`bc16-year-module`**, PR-then-merge, and
  `ci.yml`'s `on.push.branches` gains that branch beside `main`, `bc20-year-module`,
  `bc21-year-module`, `bc22-year-module`, `bc23-year-module`, `bc24-year-module` and
  `bc25-year-module`. The branch is rebased onto `origin/main` before every push. **The leagues,
  variants, modules, maps, atlases and versions of bc20–bc26 are never touched.** If a sibling branch
  lands `GV11` first, this branch rebases to `GV12` and extends the compatibility list again — the
  bc20 precedent, and `tools/ci/check_gameversion.sh` is the thing that catches it.

  bc16 touches exactly these shared files — `sim_types.nim`, `baselines.nim`, `sheet.nim`,
  `years/registry.nim`, `years/dispatch.nim`, `render.nim`, `broadcast.nim`, `results.nim`,
  `match.nim`, `client/replay_broadcast.html`, `coworld_manifest_template.json`,
  `tools/ci/policies.json`, `tools/gen_year_constants.py`, `tools/ci/viewer_smoke.mjs` (only if the
  endcard-overflow assertion needs the 360 px width added), `.github/workflows/ci.yml`,
  `docs/PARITY.md`, `docs/PROTOCOL.md`, `docs/REPLAY.md`, `NOTICE`, `README.md`,
  `tests/test_manifest.nim`, `tests/test_viewer.nim`, `tests/test_determinism.nim`,
  `tests/test_constants.nim`, `tests/test_sheet.nim` — and **every edit to each of them is additive**
  (a new enum value, a new `case` arm, a new appended block, a new list entry) **except one**, which is
  named here so the reviewer looks for it: **`config_schema.maxRounds.maximum` 2000 → 3000**, a
  widened bound that accepts everything it accepted before. **Everything else on `main` is untouched**:
  no bc20/bc21/bc22/bc23/bc24/bc25/bc26 module file, map, atlas, test or variant is edited.

- **`tools/ci/policies.json`** gains the bc16 set beside the seven year sets already there — the file
  is **repo-wide and carries 4 entries per year (32 after this run)**. A scripted champion is a failure
  state; filler versions must differ from champion versions. **Exactly these four bc16 entries, with
  these labels:**
  ```json
  [{"name":"battlecode-bc16-bulwark","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #1 text, §Decisions>","PLAYER_POLICY_LABEL":"bulwark"}},
   {"name":"battlecode-bc16-pullers","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_PROMPT":"<champion #2 text, §Decisions>","PLAYER_POLICY_LABEL":"pullers"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-bulwark","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"bulwark","PLAYER_POLICY_LABEL":"bulwark"}},
   {"name":"battlecode-greenhorn","run":"/bin/battlecode-player",
    "image":"cogame-battlecode-player:latest",
    "env":{"PLAYER_SCRIPTED":"greenhorn","PLAYER_POLICY_LABEL":"greenhorn"}}]
  ```
  | policy | kind | env | owner | league role |
  |---|---|---|---|---|
  | `battlecode-bc16-bulwark` | **LLM prompt** | `PLAYER_PROMPT` | **daveey** (the CI token's own player) | champion #1 — the turret-turtle doctrine |
  | `battlecode-bc16-pullers` | **LLM prompt** | `PLAYER_PROMPT` | **daveey-1** (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) | champion #2 — the scout-pull / infection doctrine |
  | `battlecode-bulwark` | scripted | `PLAYER_SCRIPTED=bulwark` | — | filler (the strong chassis on default knobs) |
  | `battlecode-greenhorn` | scripted | `PLAYER_SCRIPTED=greenhorn` | — | filler (the weak floor) |

  `<IMAGE>` is the **player** service's image (the 2026-09-03 lesson: `cogame-battlecode` alone matches
  nothing `compose build` produces and fails at "Docker image is not available locally"). **Champion
  #2 carries the `"player"` field** and is uploaded while `daveey-1` is the active player. LLM
  credentials reach the **game** container through the manifest env; the player pods need no Bedrock
  sidecar in this lineage.

  **Release dispatch shape, decided: dispatch `coworld-release.yml` with a `policies` OVERRIDE limited
  to exactly the four bc16 entries above** (the bc20 pattern), so the release does not recut vN+1 of
  the 28 bc20–bc26 policies the seven existing leagues have seated (LEARNINGS 2026-09-08: dispatching
  the whole file recuts every sibling year's policies). **Phase 40 must assert the filter returns
  exactly 4 before dispatching.** If the override is ever dropped and the full file is used instead,
  phase 50 must take its labels from **that** release's `release-result.json` and never from remembered
  ones (the bc21 learning).

### The phase-50 plan (from the idea, recorded here so phase 50 does not re-derive it)

An **eighth league**, created beside the bc20–bc26 ones, touching none of them and not the game's
default league:

| field | value |
|---|---|
| `league_key` | `bc16` |
| `league_name` | `Battlecode 2016 — Zombie Invasion` |
| `default_variant_id` | `bc16` |
| `short_name` | `bc16` → **`softmax.com/battlecode/bc16`** (`POST /leagues/$L/short-name`) |
| champions (LLM) | `battlecode-bc16-bulwark` (owned by **daveey**), `battlecode-bc16-pullers` (owned by **daveey-1**) — deliberately the year's two poles: the archetypes the 2016 finals produced against the two mechanics they never systematically spent |
| fillers (scripted) | `battlecode-bulwark`, `battlecode-greenhorn` |
| credits | its own pool: `POST /leagues/$L/reward-pool/grants` (100 credits, idempotency key) + `PUT /leagues/$L/reward-pool/drip` `{"daily_drip_credits":100,"max_balance_credits":300}` — an unfunded pool produces a 200 from `trigger-round` and no round row at all |

Do **not** call `POST /games/$GAME/default-league` — that is the first league's. `GET /leagues`
filtered on `game.coworld_name` returns several rows; **select by `league_key`/name client-side, never
positionally or by count** (LEARNINGS 2026-09-08: the count is a prediction, not a fact — bc24 is
Blocked and has no league). Fillers are set **before** the first `trigger-round`. **The verify slug is
`battlecode/bc16`, not `battlecode-2016`**: `softmax.com/battlecode-2016` does not exist, and the
phase-60 check-6 link and the phase-70 play link both take `softmax.com/battlecode/bc16` (LEARNINGS
2026-09-08). The atlas slug is likewise `battlecode/bc16`.

### Licensing

`LICENSE` is **AGPL-3.0** and stays that way; the repo is public, so the source offer is discharged by
the repository itself. **Both 2016 upstreams are GPL-3.0, and GPL-3.0 §13 explicitly permits
combination with AGPL-3.0 material, so AGPL-3.0 is a valid licence for the combined work** — stated
here rather than left implicit, because it is the first time this repo has taken in GPL-3.0 (rather
than AGPL-3.0) upstream material. `NOTICE` gains four sections, whose content is §The game
"Provenance and licensing" verbatim plus the per-file attribution:

- **`battlecode/battlecode-server-2016` engine — GPL-3.0** (root `COPYING`), pinned
  `11a0b09f…`. Derived files named individually: `src/battlecode/years/bc16/**` (behaviour,
  hand-written in Nim from reading the source), `years/bc16/constants.nim` (generated),
  `years/bc16/zombies.nim` (the `ZombieControlProvider` behaviour — the one module that is a
  near-literal reproduction, and it says so), `data/maps/bc16/*.json` (converted, with the build-time
  den split and symmetry) and `data/bc16/tables.json` (generated under JDK 8).
- **`battlecode/battlecode-client-2016` sprites — GPL-3.0** (`COPYING`), pinned `317e1f3f…`.
  `data/atlas_bc16.*` is cut from `src/main/battlecode/client/resources/art/**`, credited by directory
  and by file family. No client code is shipped, built or embedded.
- **The oracle jar** is downloaded **in CI only**, pinned by URL, size (6 563 607) and sha256 in
  `tools/oracle/bc16/jar.lock`; its bundled third-party classes reach only that job's classpath, never
  any image and never this repository's source tree.
- **Unlicensed repositories are not vendored, not ported, not compiled, not read and not cloned** —
  **`TheDuck314/battlecode2016`** and **`bshimanuki/battlecode2016`**, by name.

`docs/RULES-BC16.md` carries the full **§Divergences** list: (1) **the bytecode-dependent delay decay
pinned to 1.0** (V1), with the table that proves the port knows the formula and the argument about why
deriving it from `DecisionOps` would make the chassis a rules input; (2) **no bytecode instrumentation
— a fixed 2000/1000/0-`DecisionOps` budget** with no mid-turn resumption and no mid-primitive cut
(V2); (3) **the map's random origin not ported, with the inertness proof** (V3); (4) **armageddon not
ported**, with the measurement that both armageddon maps are 2-vs-0 (V4); (5) **`resign`, team memory
and the indicator/observation APIs unreachable or absent** (V5); (6) **no `.rms` serial layer** (V6);
(7) **the build-time resolution of the one `HashMap` iteration order** (D3), with the note that the
runtime sim hashes nothing; (8) **the build-time computation of map symmetry** (D4), with the
first-wins order and the thirteen two-symmetry maps; (9) **the two hash-order sweeps that are genuine
no-ops and are therefore not ported at all** (D1); (10) **22 of the 98 official maps converted**, with
the reasons for the exclusions (V7); (11) `EXCEPTION_BYTECODE_PENALTY` (V8); (12) **the `deadline`
wall-clock stop**, a coworld concept and not an engine one, recorded as one load-bearing record;
(13) **both chassis are ours**: `bulwark` written for this run from the engine's mechanics, `greenhorn`
existing in a Java twin that may not gain behaviour; (14) the chassis file layout, if the builder
merges any two modules; (15) **the score's tenths-narrowing**, and the fact that the *winner* is
decided on the engine's exact float64 differences while *points* are decided on the narrowed integers,
so the two can disagree on a razor-thin margin.

---

## Tests

Everything runs in `.github/workflows/ci.yml` (`<slug>` = `battlecode`, `<IMAGE>` =
`cogame-battlecode`, **`<SEATS>` = 2**). The sandbox runs none of it; **CI is the only harness**. The
`test` job's `timeout-minutes` goes **130 → 150** (LEARNINGS 2026-09-08: the test job alone is already
~60 min with six year modules and each file runs twice — debug and `-d:release`; bc16's 3000-round
shards are the longest in the repo).

**Two conventions every bc16 test file obeys, because the repo has been bitten by both:**

- **Never zero `perGameBudgetSeconds` in a test helper.** `match.nim:480` clamps it to
  `max(1, min(field, remaining))`, so a zeroed field silently buys a **one-second** budget while
  `years/bc16/rules.nim` one level down treats 0 as unbounded — and the symptom is diagnostic: a
  3000-round shard that **passes in `-d:release` and fails in debug**. Every bc16 test uses the
  `if perGame > 0:` convention from `tests/test_bc23_replay.nim:69`.
- **Guard every `games[0]`** behind a non-empty check, so a failed assertion prints a FAIL instead of
  an `IndexDefect` (and in release, where bounds checks are off, instead of an unchecked OOB read whose
  "pass" is not trustworthy). And **every end-reason assertion is tolerant** —
  `reason in [epDeadline, epComplete]`, never strictly `epDeadline` on a runner-speed-dependent shard.

### `test` job — native Nim (each file runs twice: debug and `-d:release`)

1. **`tests/test_bc16_cooldown.nim`** — the delay pair, this year's whole tempo. Both counters are
   **float64**; `decrementDelays` subtracts exactly **1.0** and floors at 0.0 (V1); readiness is
   **strictly `< 1`**; and **the set/add pairing is asserted per action**, because getting it backwards
   is the easiest way to break bc16: `activateCoreAction` does `setWeaponDelayUpTo(a)` then
   `addCoreDelay(m)` while `activateAttack` does `addWeaponDelay(a)` then `setCoreDelayUpTo(m)` —
   **opposite** in both the set/add choice and which counter gets which. Named vectors: a soldier's
   diagonal step onto rubble 60 charges **core 5.6 / weapon 2.0**; its attack **weapon +2 / core
   up-to 1**; a turret's attack **weapon +3 / core up-to 3**; a `pack` **+10 on both, no readiness
   check**; a VIPER build **weapon up-to 30 / core +30**; an `activate` **weapon up-to 0 / core +2**; a
   **repair nothing at all**; and `clearRubble` on a 0 square nothing and no change.
2. **`tests/test_bc16_units.nim`** — the twelve-row table and all eight derived predicates against
   `data/bc16/tables.json`: `canAttack` (ARCHON, SCOUT, TTM, ZOMBIEDEN **false**), `canInfect`,
   `isInfectable` (**every player unit true, archons included**), `canMove` (ZOMBIEDEN, TURRET false),
   `canBuild`, `canMessageSignal` (ARCHON, SCOUT only), `isBuildable` (**TTM false** — only reachable
   by packing), `canClearRubble` (TURRET, TTM false); the **outbreak ladder** for levels 0…10 (a
   level-9 BIGZOMBIE is **1500 HP / 75 damage**); a **GUARD taking `damage − 4` above 10 and the full
   damage at 10 or below** (2.5 → 2.5; 25 → 21; 13 → 9) and **dealing 3.0 to a zombie, 1.5 to a player
   unit**; a **TURRET refusing r² 5 and accepting exactly 6 and exactly 40**; and an attack on an
   **empty square** and on an **ally** both being *legal* and both costing full delay.
3. **`tests/test_bc16_rubble.nim`** — `< 100` passable, `>= 100` not, **except** SCOUT, FASTZOMBIE and
   BIGZOMBIE which pass anything; `>= 50` doubles **both** the movement and the cooldown charge and
   `< 50` doubles neither; `clearRubble` is `max(0, 0.95r − 10)` with vectors `100 → 85`, `10 → 0`,
   `0 → no-op-and-no-cost`, `1 000 000 → 949 990`, and **14 clears take a 100 to 0 while 55 take a
   1000**; a corpse adds **its own maxHealth** (archon 1000, BIGZOMBIE 500 at level 0 and **1500 at
   level 9**, guard 145) and **one third on a TURRET kill** (`145 × (1.0/3.0) = 48.333333333333336`, a
   named vector); and an **infected corpse adds nothing**.
4. **`tests/test_bc16_infection.nim`** — a VIPER hit sets `viperInfectedTurns = 20`, any zombie hit
   sets `zombieInfectedTurns = 10`, **the two counters are independent** and `isInfected()` is their
   OR; `processBeingInfected` runs **in `processEndOfTurn` and only when health > 0**, deals **exactly
   2.0** for a viper infection and **nothing** for a zombie one, and decrements each (so 20 viper turns
   deal 40 total — not enough to kill a full 60-HP soldier, and the named vector is one already at 40
   or below); an infected robot that dies **leaves no rubble and spawns `turnsInto` on Team.ZOMBIE at
   its own square with `maxHealth(currentRound)`** — ARCHON → **BIGZOMBIE**, SCOUT → FASTZOMBIE,
   SOLDIER and GUARD → STANDARDZOMBIE, VIPER/TURRET/TTM → RANGEDZOMBIE; a **NEUTRAL killed by
   activation never turns**; a **disintegrating infected robot does**; and the new zombie takes **no
   turn in the round it spawns**.
5. **`tests/test_bc16_zombies.nim`** — the verbatim AI, and the most order-sensitive shard in the
   module. The den: this round's counts added from **its own** split schedule, then `spawnAllPossible`,
   then — **only if a queue remains** — 10 damage to every adjacent non-zombie and a **second**
   `spawnAllPossible`; the ring order `DIRECTIONS[floorMod(start + i × chir, 8)]` with `DIRECTIONS` =
   N, NE, E, SE, S, SW, W, NW; the **spawn priority BIGZOMBIE → FASTZOMBIE → RANGEDZOMBIE →
   STANDARDZOMBIE** (the no-`break` loop takes the *last* non-zero type); a den spawning **onto rubble
   ≥ 100** (it skips the pathability test) but never onto an occupied square; **at most 8 per call and
   16 per round**. The zombie: the eight-step ladder of rule 5.5 with **every early return in place**,
   asserted against a recorded oracle draw sequence — including that `random.nextBoolean()` is consumed
   **only** when the preferred direction is blocked, that `random.nextInt(8)` is consumed **only** when
   no player robot is alive, and that `GameWorld.rand.nextInt(closest.size())` is consumed **on every
   call including size 1**; that a FASTZOMBIE/BIGZOMBIE never reaches the `clearRubble` step; and that
   step (h) attacks a **NEUTRAL** in the preferred square. Plus `getSpawnDirection`'s first-minimum-in-
   file-order tie-break and `getSpawnChirality`'s **1 for ROTATIONAL/NONE, `signum(compareTo(opposite))`
   otherwise, 1 on the line of symmetry**.
6. **`tests/test_bc16_execorder.nim`** — the exec list: append on spawn, **by-value removal** on death
   preserving the survivors' order, the pre-sweep snapshot so a robot spawned this round takes no turn
   this round, the skip for a robot destroyed mid-sweep, the initial robots in **map-file order** (not
   id order), and **`!isActive()` robots taking a turn with a zero budget and doing nothing**. 500
   random spawn/destroy sequences replayed against the oracle's own list.
7. **`tests/test_bc16_sensing.nim`** — sight r² ≤ 24 (soldier, guard, viper, turret, TTM), ≤ 35
   (archon), ≤ 53 (scout), and **`-1` = the whole map for every zombie and den**;
   `senseRubble`/`senseParts` returning **−1** out of range rather than throwing; `senseNearbyRobots`
   returning **insertion order** with self excluded (what fixes the enemy `greenhorn` attacks);
   `senseHostileRobots` including **Team.ZOMBIE**; the static scan order (**x ascending outer, y
   ascending inner** over the `⌊√r²⌋` box, keeping `d² <= r²`) against a recorded oracle sweep and its
   **throw above r² 100**; the world form's `min(⌊√r²⌋, 80)` clamp; the tabled `⌊√r²⌋` for r² 0…10 000;
   **an attack needing no vision**; and `getInitialArchonLocations` sorted and public from round 0.
8. **`tests/test_bc16_economy.nim`** — `PARTS_INITIAL_AMOUNT = 300.0` credited **once per team** by the
   constructor; income `max(0.0, 2.0 − 0.01 × robotCount)` added **A then B** at the end of every
   round, **zero at exactly 200 robots** and `0.63` at 137 (a named float64 vector); `takeParts`
   zeroing the square and returning the **whole** amount, called **only** for an ARCHON spawning on or
   moving onto a parts square and for **no other type**; the **200-part den bounty** paid to the
   attacker's team **only when the den's health reaches ≤ 0**; and `partsWorth` = `int(parts) + Σ
   partCost over live robots` computed in **one exec-order pass** exactly as rung 3 does.
9. **`tests/test_bc16_signals.nim`** — 5 basic and 20 message signals a turn, reset in
   `processBeginningOfTurn`; **message signals from ARCHON and SCOUT only**; a negative radius refused;
   the broadcast reaching **every robot of every team** within `r²` **except the sender**; the FIFO
   queue capped at **1000 with the oldest dropped**; `readSignal` popping the head and
   `emptySignalQueue` draining in order; and the delay charge `0.05 + 0.03 × max(0, r²/sightR² − 2)`
   added to **both** counters, with the named vectors `r² = 2 × sightR² → 0.05` and
   `r² = 3 × sightR² → 0.08`.
10. **`tests/test_bc16_activation.nim`** — ARCHON only; r² ≤ 2 (so the eight neighbours and the
    archon's own square, since a diagonal is r² 2); the target must exist and must be **NEUTRAL**;
    core ready; the neutral removed with **no rubble and no zombie**; an identical type spawned on the
    activator's team with **`buildDelay 0`, immediately active**; the cost **weapon up-to 0, core +2**;
    a **neutral ARCHON raising `getRobotTypeCount(team, ARCHON)`** and therefore the first tiebreak
    rung; and a neutral **turret** arriving in TURRET form (not TTM).
11. **`tests/test_bc16_endladder.nim`** — `archons_destroyed` fires **mid-turn** inside the death path
    and the round still finishes; **both factions annihilated in one round** resolves to the one whose
    last archon died **second** (the `winner == null` guard), by exec order; `timeLimitReached()` is
    `currentRound >= 2999` so **round 2999 is played**; the four rungs fire in the engine's order with
    a vector each, computed on **exact float64 differences**; rung 4 awarding **B on a 0–0 archon-id
    tie**; **a faction with one archon and no other robot playing on to round 2999** and still earning
    parts; and `resign()` being provably unreachable from any chassis.
12. **`tests/test_bc16_scoring.nim`** — the points formula with the tenths narrowing, the float32
    shares and the truncation, one vector per weight; the 0–0 `share` returning 0.5; points in
    `[0, 100]` and the seats summing to ≤ 100; the super-increasing property (`24 > 12`, `64 > 36`)
    asserted as arithmetic; **the documented case where `points` favours the loser** asserted as an
    explicit expectation rather than left to be found; **the documented case where the ladder's
    float64 rung and the tenths-narrowed points disagree** likewise; and `results.scores` **strictly**
    ordering the match winner above the loser on 500 random synthetic finals, including clinched
    two-game matches, with `winBonusFor("bc16") == 200.0`.
13. **`tests/test_bc16_maps.nim`** — every committed map re-converts identically from the pinned
    `.xml`, and sizes, seeds, **computed symmetry and `symmetries_found`**, rubble mean/max, impassable
    counts, parts squares/total/max, archons per side, den count and locations, neutral rosters and the
    **full whole-map schedule** match §Sim module's table; every map is within 30…80 in both dimensions
    with **equal archon counts** and **no armageddon flag**; **the per-den split and the two memoised
    den constants (`spawn_dir`, `chirality`) match the recorded JVM values** for all 22 maps;
    **`frogger` resolves to VERTICAL** and records both symmetries (D4); no bc16 map name resolves to
    another year's file; **every pool map is one of the 54 the jar carries**; and **the
    `docker-smoke` seed draws exactly `river`**, so the smoke's map cannot drift.
14. **`tests/test_bc16_sheet.nim`** — every one of the eleven knobs: **absent → default AND recorded in
    `defaults_applied`** (and the same test asserts a **bc23** empty sheet still records none, so the
    change is provably scoped); mistyped → default + recorded; unknown enum value → default +
    recorded; **the four integer knobs CLAMP to their range rather than defaulting** (and a
    non-integer defaults); enum values case-folded, trimmed and `-`/space normalised; unknown keys
    recorded (≤ 16, ≤ 40 runes); **a submitted `chassis` recorded as an unknown field and never
    honoured** (the D1 assertion, which fails if anyone re-adds the knob); rune-boundary truncation of
    `notes`/`motto` including astral-plane characters; the 16 KB **byte** cap cut on a rune boundary;
    **`plainWords16()` returning a non-empty, article-free complete clause for every value of every
    knob** (the "a accelerating" fix); and **the envelope resolver from the bc16 side**:
    `{"sheet":{…}}`, `{"doctrine":{…}}`, `{"protocol":"x","doctrine":{…}}`,
    `{"battlecode_2016_doctrine":{…}}`, a bare flat sheet, a payload with **both** a known knob key and
    a `doctrine` key (the flat one wins), and a two-object payload (no unwrap) — each with the expected
    `sheet_envelope` value, and nesting unwrapped **at most once**.
15. **`tests/test_sheet.nim` (extended)** — the same resolver from the **year-neutral** side: every
    existing bc20–bc26 vector still parses to the same `Sheet` it did before, so this run is provably
    additive for the seven shipped years.
16. **`tests/test_bc16_greenhorn.nim`** — `greenhorn` reproduced statement for statement against a
    recorded oracle trace: the per-robot `Random(2016)` call sequence (`nextInt(8)` only); the archon's
    **parts-check → direction-draw → build-or-move** order; the soldier's
    `senseHostileRobots(myLoc, attackRadiusSquared)[0].location` target and its **insertion-order**
    resolution; and the **scout, guard, viper, turret and TTM branches doing nothing at all**.
    **It may not gain behaviour: it is one side of the differential oracle.**
17. **`tests/test_bc16_baselines.nim`** — bounded orders and legality:
    - (a) both `PLAYER_SCRIPTED` resolutions produce a sheet that passes the **same** `sheet.validate`
      the LLM path uses;
    - (b) in played games, **every action either chassis emits is legal for the acting robot at the
      moment it is emitted**: the right counter under 1.0 for the right action; the target inside the
      right radius (and **outside r² 6 for a turret**); the destination on the map, unoccupied, and
      under rubble 100 unless the mover ignores rubble; the team stockpile actually holding
      `partCost`; `spawnSource == builder type`; `isActive()` true for the actor; **no TURRET moving,
      no TURRET or TTM clearing rubble, no non-attacker attacking, no non-archon repairing or
      activating, no message signal from anything but an ARCHON or SCOUT**; ≤ 1 repair, ≤ 5 basic and
      ≤ 20 message signals a turn; **NO FRIENDLY-FIRE ATTACK EVER** (it is legal in 2016 and the
      chassis must never use it); and **no robot exceeding its `DecisionOps` budget**;
    - (c) `greenhorn` **acts** — ≥ 1 soldier built, ≥ 1 attack landed, ≥ 1 move made — but is **not**
      required to survive, to build a guard/scout/viper/turret, to activate a neutral, to kill a den or
      to compete;
    - (d) `bulwark` beats `greenhorn` on **3 seeds × 2 `small` maps, 6/6**.
18. **`tests/test_bc16_survival.nim`** — the **economic-survival gate** (the LEARNINGS 2026-09-03 pin),
    with an inverted control. **The key design point, stated because it is bc16-specific and easy to
    get wrong: in this year a faction does not starve, it gets EATEN.** Parts income is unconditional
    (2 a round minus the army penalty) but the zombie schedule escalates by ×3 and every unit you lose
    uninfected becomes a wall while every unit you lose infected becomes an enemy. So the gate keys on
    **archon survival, army composition, den progress and infection hygiene**:
    - `bulwark` vs `bulwark`, all-defaults sheet, **3 seeds × 2 `small` maps = 6 games**, each to round
      2999. In **≥ 5 of the 6** the game must **reach the round limit or end on the tiebreak ladder**
      (i.e. **not** `archons_destroyed`) — the ≥ 4-in-5 shape the pin asks for, rounded up to 5-in-6 so
      the committed ratio is at or above it — and in **all 6** each seat must have: **still held at
      least one archon at round 2000**; built ≥ 20 units of which ≥ 5 GUARDs and ≥ 1 TURRET; collected
      ≥ 400 parts from the map; **killed ≥ 1 zombie den**; dealt ≥ 2000 damage to zombies; activated
      ≥ 1 neutral where the map has any; and finished with ≥ 8 robots alive. **Across the two seats**
      the horde must not hold more robots at round 2999 than both factions combined, and **fewer than
      40 % of each faction's losses may have `turned`**.
    - The same gate is then run as a **subprocess** against a **known-broken chassis** compiled behind
      **`-d:bc16BrokenChassis`** — a `bulwark.nim` variant whose archons **never build a GUARD and
      never repair**, whose units **ignore `infection_policy` entirely** so every infected loss stands
      up inside the home ring, and which **never commits to a den** — and it **must come back red**. That
      control is chosen deliberately: it is exactly the failure a "did it build units?" check would
      pass, and it is the failure this year's two added knobs exist to prevent. **A gate that cannot
      fail is not a gate**; this assertion is what keeps it honest, and it is the direct answer to the
      2026-09-03 finding that mechanical episode checks pass degenerate matches.
    - **The thresholds above are the design floor, not the committed numbers.** Phase 20 **measures** a
      healthy mirror and the broken control, sets the committed thresholds between them with margin
      (and never below this note's floor), and records **both** measured ranges in the test's header
      comment — exactly as `tests/test_bc22_survival.nim` and its siblings do today. If any floor here
      proves unsatisfiable on the measured healthy mirror, the resolution is the bc23 r1-F21/F22 one:
      **lower the committed number to roughly half the weak seat's measured value and record the
      measurement inline** — never drop the clause.
19. **`tests/test_bc16_knobs.nim`** — the knob-teeth gate, and the **direct enforcement of the
    anti-inert rule**. Paired seeded games (identical seed, map and opponent; the two factions
    identical except one knob at its low and high setting, 3 seeds each), each asserting a named,
    signed delta. Thresholds live in one table so tuning is a one-line change, and the header records
    every substituted statistic (the bc21 r1-F6 fix). **Plus one assertion over the whole sweep: in
    every one of the 66 games, BOTH seats built ≥ 10 units, dealt ≥ 500 damage and still had a robot
    alive at round 1000** — i.e. **no setting of any knob produces an inert faction**.

    | knob | low → high | asserted |
    |---|---|---|
    | `opening` | `turtle` → `soldier_viper_aggro` | soldiers + vipers built by round 600 up ≥ 60 % **and** guards built down ≥ 30 % **and** mean distance of own units from own archons up ≥ 40 % |
    | `opening` | `turtle` → `scout_zombie_pull` | scouts built up ≥ 3 **and** zombie damage **taken** down ≥ 25 % **and** enemy zombie damage taken up ≥ 15 % |
    | `turret_count` | 0 → 10 | turrets built up ≥ 5 **and** parts spent on units down ≥ 30 % **and** zombie damage taken down ≥ 20 % |
    | `guard_ratio` | 0 → 100 | guards built up ≥ 8 **and** soldiers built down ≥ 60 % **and** robots lost to zombies down ≥ 25 % |
    | `zombie_kiting` | `never` → `always` | robots lost to zombies down ≥ 20 % **and** total damage dealt to zombies down ≥ 10 % (the trade-off is the point) |
    | `den_clear_round` | 2500 → 200 | round of the first den kill earlier by ≥ 1500 **and** zombies spawned over the game down ≥ 25 % **and** parts collected up ≥ 200 (the bounties) |
    | `parts_priority` | `units` → `vipers` | vipers built up ≥ 2 **and** infections **inflicted** up ≥ 15 **and** soldiers built down ≥ 20 % |
    | `parts_priority` | `units` → `turrets` | turrets built up ≥ 2 **and** units built down ≥ 15 % |
    | `archon_spread` | `huddle` → `split` | mean pairwise archon distance up ≥ 60 % **and** parts collected from the map up ≥ 30 % **and** archons lost up ≥ 0.5 (the risk is the point) |
    | `neutral_activation` | `never` → `hunt` | neutrals activated up ≥ 4 **and** units built down ≥ 10 % (the detour costs build turns), run on `caverns` and `industrial` where the roster is 22–26 including neutral archons |
    | `retreat_hp` | 0 → 80 | robots lost down ≥ 20 % **and** hp repaired up ≥ 120 |
    | `rubble_clear` | `never` → `aggressive` | rubble cleared up ≥ 5× **and** impassable squares at round 2999 down ≥ 25 % **and** mean own-unit movement charge down ≥ 10 % |
    | `infection_policy` | `ignore` → `quarantine` | **own units that `turned` within r² 100 of an own archon down ≥ 60 %** **and** archons lost to zombies down ≥ 20 % |
    | `infection_policy` | `quarantine` → `suicide_squad` | **own units that `turned` within r² 100 of an ENEMY archon up ≥ 3** **and** enemy zombie damage taken up ≥ 20 % |

20. **`tests/test_bc16_perf.nim`** — a full 3000-round game on `6147` (45×45, the largest played map)
    with both seats on the unit-maximising configuration named in §The game, in **≤ 130 s**; failing it
    means switching `gamesPerMatch` to 2 and then 1.
21. **`tests/test_bc16_arith.nim`** — the float64 fidelity shard: every named product from §Sim module
    ("The arithmetic is FLOAT64 everywhere") asserted as a **bit-exact** float64 literal; the
    `directionTo` lattice for `dx, dy ∈ −80…80` (25 921 pairs) against the committed table; the
    `⌊√r²⌋` table for r² 0…10 000; the outbreak ladder; and the whole `pow(k/8000, 1.5)` table for
    k = 0…8000 (`tests/table_bc16_delay.nim` reads the same file and asserts the **1.0 branch** is
    exactly what V1 pins).
22. **`tests/test_determinism.nim` (extended)** — same seed + same sheets ⇒ identical hash chain, twice
    in one process and across a save/load; **the three `java.util.Random` streams staying
    independent**, asserted by folding all three states into the chain and by a vector that advances
    one and leaves the other two unchanged; and **record → re-derive for every bc16 end reason**
    (`archons_destroyed`, all four rungs, and the `abandoned`/`deadline` stop applied by the same proc
    on both paths).
23. **`tests/test_bc16_replay.nim`** — a bc16 replay document round-trips; a **strict UTF-8 parse** of
    the written bytes; the viewer's re-derivation of a recorded bc16 match reproduces the recorded
    per-round hashes; robot positions, health, types, delays, infection counters, `roundsAlive`, the
    rubble and parts arrays, the stockpiles, the signal queues, the den queues and all three RNG states
    re-derive identically from events + config + seed with **nothing stored**; `plan.maps` carries all
    three drawn maps even when the match clinched in two; `seats[].sheet_envelope` and
    `sheet_submitted` round-trip; and **every event kind respects its per-game bound** from the table
    in §Server — including `zombie_wave <= 30` against the measured maximum schedule length of 29.
    The end-reason assertion is **tolerant** (`reason in [epDeadline, epComplete]`) and every
    `games[0]` read is guarded.
24. **`tests/test_bc16_beats.nim`** — the **beat contract** (§Viewer): from the committed
    `tests/fixtures/replay-bc16.json`, `beatsFor` must return **≥ 26 beats over ≥ 10 distinct kinds**,
    every one with a non-empty label of ≤ 120 runes, every kind inside the thirteen-kind vocabulary,
    and a `html[data-year="bc16"] .beat-marker.<kind>` CSS rule present in
    `client/replay_broadcast.html` for **every kind the fixture actually emitted**. Emission, label and
    style, all three, from the committed artefact.
25. **`tests/test_manifest.nim` (extended)** — the triple-sync tripwire, now **eight years** wide: the
    results key set + the `reason` enum == the manifest `results_schema` == the key set
    `tools/ci/docker_smoke.sh` asserts; **`num_agents` present in all eight variants' `game_config`
    and in `certification.game_config`, and absent at every variant top level**;
    `config_schema.year.enum == ["bc26","bc20","bc21","bc24","bc25","bc23","bc22","bc16"]`;
    **`config_schema.maxRounds.maximum == 3000` and every shipped variant's `maxRounds` inside it**;
    **`player[]` contains exactly the ids in `certification.players`** and
    `len(certification.players) == certification.game_config.num_agents` (the pair of checks that would
    have caught the bc20 release failure); `end_reason`'s enum containing `archons_destroyed`,
    `more_archons`, `more_archon_health`, `more_parts_net_worth`, `highest_id` and `abandoned` and
    **not** `zombified`, `cleansed` or `resignation`; every `config_schema` array bounded; `tokens`
    declared and required but never valued in a `game_config`; **both `game.protocols` keys** and
    `game.docs.readme` plus **all ten** `pages` being `{type, value}` objects; and the installed
    `coworld` CLI's own `validate_upload_manifest` / `_load_template_manifest` accepting the template.
26. **`tests/test_constants.nim` (extended)** — `tools/gen_year_constants.py --year bc16 --check`
    regenerates `years/bc16/constants.nim` from the pinned sources and byte-diffs it, and
    `tools/convert_maps_bc16.py --engine … --check` re-converts all 22 committed maps and byte-diffs
    them, plus `--parse-all` reads **all 98** official `.xml` files (a reader that only works on the
    maps we ship is a reader nobody can extend the pool with) and asserts the two armageddon maps are
    **refused** with the stated reason.
27. **`tests/test_viewer.nim` (extended)** + `tools/wasm_replay_smoke.cjs` — the emitted wasm module
    loads under node and answers `bc_load_replay`/`bc_frame` on the committed **bc16** fixture replay;
    the bc16 game block shadows no `ChromeCommon` alias and no other year's game-block name (the tandem
    scar); **`chrome_common.js` and `broadcast_core.js` still match the coworld-ctf copies by sha256**;
    `#bc16-doctrines` carries a dismiss control, is capped-and-scrolling and sits outside
    `var(--band)`; **every `#bc16-*` rule is scoped to `html[data-year="bc16"]`**; `relayout()`'s
    `--statrail` measurement set names `bc16-econ` and `bc16-units`; the **endcard fixes 1–5** from
    §Viewer (bc16's noun row present and no other year's resource noun inside it; the
    `scrollHeight <= clientHeight` rule at 1280×800; every printed number through `fmtStat` with a
    `/\d\.\d{3,}/` grep failing the test; a blank motto rendering nothing; no article-plus-enum
    concatenation; and the `visibility: hidden` rule for the `#bc16-*` boxes while the endcard shows).

### `parity-oracle-bc16` job — the 2016 engine as a CI-only oracle

**The recipe below is built on facts measured in this sandbox, not guessed.** The released jar
`https://s3.amazonaws.com/battlecode-releases-2016/releases/battlecode-2016.0.2.2.jar` (**HTTP 200,
6 563 607 bytes, sha256 `c78ef341af0b666acabdabf545695862b77f84076f946766787bc1549b1fdc1c`**, pinned
in `tools/oracle/bc16/jar.lock`) is **self-contained**: **2 484 entries**, `battlecode-version` =
`2016.0.2.2`, **449 `battlecode/` classes**, `org/objectweb/asm` (58), `com/thoughtworks/xstream`
(463 — the map XML reader), `com/fasterxml` (765), `org/apache/commons/lang3` (236),
`battlecode/instrumenter/bytecode/resources/MethodCosts.txt`, and **54 `.xml` map resources**. So there
is **no Ant, no Ivy resolution, no Gradle, no shim, no Maven Central download list and no `deps.lock`**
in this job, and — because every pool map is one of those 54 — **no `--map-dir`**. The job is:

1. `actions/setup-java@v4`, `distribution: temurin`, `java-version: **"8"**`. **This is not a
   preference:** the jar bundles a 2016-era ASM and a 2016-era XStream, and the whole instrumenter is
   built for Java 8 class files. The bc22 and bc23 runs both measured the failure mode on a modern JDK
   — `java.lang.IllegalArgumentException` inside `org.objectweb.asm.ClassReader.<init>` on **every**
   player class load, no robot ever built, the game over in one round, **and the job exiting 0** — and
   2016's ASM is older still. Item 3 exists because of that trap.
2. **Compile with plain `javac -nowarn -encoding UTF-8 -cp <jar>` and NO `--release`, no `-source`,
   no `-target`.** `--release` arrived in JDK 9 and dies with "invalid flag" on a JDK-8 `javac` in
   seconds (the bc21 lesson); the compiler **is** 8, so the target is 8.
3. **The driver must fail loudly when nothing happens, and it must call `System.exit()`.** Two
   requirements: (a) `tools/oracle/bc16/Bc16Trace.java` **exits 3 if no zombie is ever spawned and no
   robot ever takes an action**, which is what catches item 1, and `ci.yml` additionally asserts every
   game reached at least **2 900 rounds** and that at least **150 zombies** were spawned; (b) the
   sandboxed player threads are **non-daemon**, so a driver that returns or throws without
   `System.exit()` hangs forever. Every `java` invocation in the job is wrapped in `timeout 900`.
4. Download the jar and **verify its sha256 and size** against `jar.lock`. **There is no
   `SPEC_VERSION` in 2016's `GameConstants`** — the field does not exist — so the sha256 and the size
   are the only pins, plus `battlecode-version` = `2016.0.2.2` read out of the jar entry. Tier B
   cross-checks every constant anyway.
5. Run `java -Xmx2g -XX:+UseSerialGC -cp battlecode-2016.0.2.2.jar:classes battlecode.world.Bc16Trace
   <map> <rounds> <pkgA> <classesDirA> <pkgB> <classesDirB>`. The driver is
   `package battlecode.world;` so it needs reflection only for `GameWorld.rubble` / `parts` /
   `gameObjectsByID` / `rand` (private — the only way to checksum the two map arrays, print in exec
   order and read the RNG state) and `ZombieControlProvider.random`. It loads the map with
   `GameMapIO.loadMap(name, null)` (the resource fallback path, `GameMapIO.java:56-61`), builds a
   `TeamControlProvider` registering a `PlayerControlProvider` for **Team.A** and **Team.B** and a
   `ZombieControlProvider` for **Team.ZOMBIE and Team.NEUTRAL** (both are required — `TeamControlProvider`
   asserts a provider for every team it is asked about, and a NEUTRAL robot's `runRobot` reaches
   `ZombieControlProvider`'s "somehow controlling a non-zombie robot → kill it" branch, which is why
   **neutrals must be registered to a `NullControlProvider`, not to the zombie one** —
   `world/control/NullControlProvider.java` exists for exactly this and the driver uses it), constructs
   the `GameWorld` and calls `runRound()` in a loop, printing the trace **from the live objects**, with
   the players' own `System.out` diverted into a discarded stream. **No XML writing, no `.rms`, no
   `pip install` on either side**, and the engine is used exactly as published.

**The trace.** One line per record; `tools/parity_trace_bc16.nim` prints the same lines from the Nim
port. All coordinates are **origin-relative** on both sides (V3).

```
R <round> T <A|B> parts=<%.6f> ar=<n> sc=<n> so=<n> gu=<n> vi=<n> tu=<n> tt=<n>
R <round> Z zn=<n> zs=<n> zr=<n> zf=<n> zb=<n> dens=<n> neu=<n> outbreak=<n>
R <round> G rubblechk=<fnv1a64> partschk=<fnv1a64> rubblesum=<%.6f> partssum=<%.6f>
R <round> U <id> team=<A|B|N|Z> ty=<TYPE> x=<n> y=<n> hp=<%.6f> cd=<%.6f> wd=<%.6f> zi=<n> vi=<n> ra=<n> bd=<n> bc=<n>
R <round> D <id> x=<n> y=<n> hp=<%.6f> q=<s>:<r>:<f>:<b>
R <round> X world=<48-bit hex> zombie=<48-bit hex> idgen=<48-bit hex>
R <round> W winner=<A|B|-> dom=<NAME|->
```

Robots are printed **in exec order**, not id order, which is what makes an ordering bug visible; the
**`X` line is bc16's own addition and it is the most valuable line in the trace** — it carries all
three RNG states every round, so a single missed or extra `nextInt`/`nextBoolean` (D2b/D2c) surfaces on
the round it happens instead of as a mystery 400 rounds later. Every float64 is printed with
`%.6f`-style fixed formatting **on both sides by the same rule**, and
`tools/ci/parity_tiers_bc16.py`'s `normalize()` re-parses **every named float field** through an
explicit allowlist (`parts`, `hp`, `cd`, `wd`, `rubblesum`, `partssum`) and re-emits it canonically, and
re-parses every named checksum field (`rubblechk`, `partschk`, `world`, `zombie`, `idgen`) as an
unsigned 64-bit integer and re-emits it canonically — **so neither emitter's formatting can create or
hide a divergence**. The `bc=` column is **stripped from BOTH traces by one `normalize()` applied to
each side** and is used only for the Tier A headroom assertion (LEARNINGS 2026-09-08: bc23's comparator
stripped it from the Java side only and every pair "diverged" at round 1). The comparator uses
**`itertools.zip_longest`, never `zip`** (a one-line-longer Java trace must not read bit-exact) and
carries a self-test that constructs exactly that pair and asserts a divergence is reported. Traces are
written to `$RUNNER_TEMP`, compared **streaming** (never loaded whole), and only the first 200 divergent
lines plus a gzipped digest are uploaded. `parity_tiers_bc16.py` is bc22's script — whose three
comparator bugs are already fixed there — plus the float allowlist and the origin normalisation.

**The tiers — pinned to what this harness can actually deliver.**

- **Tier A (BLOCKING) — rounds 0…2999 bit-exact, whole games, on nine pairs**
  (`checkers`, `zigzag`, `swamp`, `river`, `prisons`, `frogger`, `turtle`, `desert`, `space` — chosen
  in §Sim module to cover both reachable symmetries and both chiralities, a two-symmetry map, the
  rubble boundary at 100 and the extreme at 10⁶, minimum and maximum archon separation, one and four
  archons a side, two and ten dens, neutral ARCHONs, and a map with zero impassable squares as the
  control), with **`bc16idle` against itself**: a bot whose whole body is
  `while (true) Clock.yield();`. **This is a real and large tier, not a trivial one, and that is the
  single most important thing to understand about bc16 parity**: the zombie half of this game is
  **engine-side**, so an idle player still exercises the den schedules and their per-den split, the
  spawn ring's direction and chirality, `spawnAllPossible` and its proximity-damage fallback, the whole
  eight-step zombie movement ladder, all three RNG streams, infection and the die-and-turn conversion,
  the corpse-rubble deposit, `clearRubble` by digging zombies, the parts income curve, both factions'
  archons being eaten, the mid-turn `DESTROYED` check, **and** the round-2999 ladder on the games where
  an archon survives. The job asserts off the **Java** trace that all of that really happened: a `zs`/
  `zr`/`zf`/`zb` count rises; a `D` line's queue is non-empty; `rubblechk` changes on a round with no
  clearing; a `U` line with `team=Z` appears at a square where a `team=A` line was; `zi`/`vi` counters
  go non-zero; and a `W` line carries a `dom`. **A tier that agrees bit for bit while nothing happens
  proves nothing**, and this is the step that stops it.
- **Tier A′ (BLOCKING) — the scenario pairs, whole games, bit-exact.** Tier A cannot cover any *player*
  action, so this job runs **four scenario bots of our own**, each (a) deterministic with **no RNG at
  all**, (b) cheap — each **asserts at the end of every turn that `Clock.getBytecodeNum()` is at or
  below `bytecodeLimit − 8000`** and `System.exit(4)` otherwise, so the engine's own
  `amountToDecrement` is exactly 1.0 and V1 is not exercised — and (c) **scripted by round number to
  force every rare path early**:
  **`bc16scenario`** builds one of each of SCOUT, SOLDIER, GUARD, VIPER and TURRET and proves each
  build freeze; moves in all eight directions proving the diagonal and rubble factors separately;
  clears a square from 100 to 0 in fourteen actions and one at 0 for free; attacks an empty square, an
  ally and an enemy; proves a TURRET refusing r² 5 and accepting 6 and 40; packs and unpacks proving
  10-on-both twice; repairs, proving 1 HP for zero delay and the one-per-turn cap; **activates a
  NEUTRAL soldier and a NEUTRAL ARCHON**, proving the no-rubble/no-turn/immediately-active spawn; sends
  a basic and a message signal at three radii proving the three delay values; walks an archon onto a
  parts square; lets a VIPER infect an enemy; and disintegrates one robot.
  **`bc16scenarioturn`** lets an infected SOLDIER, SCOUT and ARCHON die and proves each becomes the
  right zombie type at the right outbreak multiplier with no rubble.
  **`bc16scenarioannihilate`** walks soldiers onto the enemy's single archon on `swamp` until
  `DESTROYED` fires and proves the round still finished. **`bc16scenariotie`** mirrors both sides so
  the ladder walks `PWNED` → `OWNED` → `BARELY_BEAT` and, on one seed, `WON_BY_DUBIOUS_REASONS`.
  `scenario16.nim` is their Nim twin, written line for line, behind `-d:bc16Scenario`
  (+`-d:bc16ScenarioTurn` / `-d:bc16ScenarioAnnihilate` / `-d:bc16ScenarioTie`). Both sides run all
  four variants on the nine pairs and must agree **bit for bit for the whole game**. The job then
  asserts, **off the JAVA trace**, that the paths really fired: a `U` line for each of the five built
  types; a `bd=` column going from non-zero to zero on the same id; a `ty=TTM` line and a later
  `ty=TURRET` line on the same id; a `team=N` line disappearing on the same round a `team=A` line of
  the same `ty` appears; `parts=` rising on a round with no den kill (a parts square) and by exactly 200
  on a round with one; `zi=`/`vi=` counters; a `team=Z` line at a former `team=A` square with the right
  `ty`; and `W` lines carrying `DESTROYED`, `PWNED`, `OWNED`, `BARELY_BEAT` and
  `WON_BY_DUBIOUS_REASONS` across the set. *(If the instrumenter makes any one of these scripted paths
  impossible to force deterministically, the failing item is dropped from the scenario bot and **added
  to `docs/PARITY.md` §What is NOT compared with the reason** — never silently left in a bot that does
  not reach it.)*
- **Tier A″ (BLOCKING) — `greenhorn` against itself, whole games, bit-exact, on the nine pairs.**
  `greenhorn` is the one bot with a live `java.util.Random(2016)` per robot, so this tier is what proves
  the port's `rng.nim` reproduces a **fourth** independent stream call-for-call alongside the engine's
  three, and it is also the tier that runs the real filler.
- **Tier B (BLOCKING) — the arithmetic and the map data, over their whole finite domains.**
  `tools/JavaBc16Tables.java`, run against the jar's own classes under the CI **JDK 8**, regenerates
  `data/bc16/tables.json`: the whole twelve-row `RobotType` table with all seventeen fields and the
  `turnsInto` graph; the eight derived predicates for all twelve types; the outbreak ladder for levels
  0…12; **`Math.pow(k/8000.0, 1.5)` for all 8 001 k** (Tier B′, the V1 table); **`(int) Math.sqrt(r²)`
  for r² 0…10 000**; the **`directionTo` lattice for `dx, dy ∈ −80…80`** (25 921 pairs); the guard
  reduction and multiplier over every reachable attack power; the rubble clear map `max(0, 0.95r − 10)`
  over r ∈ {0…1000} plus a decade sample to 10⁶; and the parts income `max(0, 2 − 0.01n)` for
  n = 0…400 — **and the job byte-diffs it against the committed file**. It **also** regenerates, from
  the JVM's own `GameMap.getSymmetry()` and `getZombieSpawnSchedule(denLoc)`, **the symmetry and the
  complete per-den split of all 22 committed maps**, and byte-diffs those against
  `data/maps/bc16/*.json` — which is what proves D3's build-time `HashMap`-order emulation and D4's
  symmetry computation rather than trusting them. bc16 has exactly **two** non-algebraic functions and
  both domains are finite, so this tier is not a sample: it is the entire domain.
- **Tier C (BLOCKING against a ledger) — the first divergent round of every whole 3000-round game, on
  all six bots and all nine maps.** The job computes it per pair and compares it against
  `tools/ci/parity_ledger_bc16.json`, whose entries are
  `{"bot": "...", "map": "...", "first_divergent_round": N, "cause": "<one sentence>",
  "docs": "PARITY.md#<anchor>"}`. It **fails** if (a) a pair diverges and has no ledger entry, (b) a
  pair diverges **earlier** than its entry, (c) a ledger entry no longer reproduces (a stale excuse is
  as bad as a missing one), or (d) **any** divergence occurs while the traced bytecode peak is still
  under `limit − 8000` — which, on every bot in this job, means **always**, and therefore means a real
  rules bug rather than an instrumentation artefact.

**Root-cause-or-fail is the standing rule, and it is the operator's ruling on the bc26 run (Fleet card
1218171523823317), not this note's preference.** An unexplained Tier C divergence is a **FAIL**, not a
ledger line. Every ledger entry must name a round, a map and a *root cause*; a cause of "unknown" is
not a cause and the ledger schema rejects it. **The phase-30 exit condition is that Tiers A, A′, A″, B
and B′ pass with an EMPTY ledger**, and this note believes that is achievable because the two things
that historically forced divergences are both absent here: there is **no hash-ordered robot sweep**
(D2) and there is **no run-time transcendental** (both are tabled). **The one place a divergence is
genuinely plausible is the RNG call conditions** — `GameWorld.rand`'s draw-on-every-call and
`ZombieControlProvider.random`'s three-branch precondition chain — which is exactly why the `X` line
carries all three states **every round** rather than only on interesting rounds.

If phase 30 finds a divergence anyway, the budget for root-causing it is stated here — the
**root-cause checklist**, each item with its own unit test above, so a Tier C failure bisects in
minutes rather than becoming a card: the three RNG streams' call conditions (tests 5, 22); the exec
list's by-value removal and pre-sweep snapshot (test 6); the delay pair's set/add pairing per action
(test 1); the `< 1` readiness boundary (test 1); the rubble thresholds and the clear formula (test 3);
the corpse deposit and its turret third (test 3); infection's two counters, its 2.0 damage and its
die-and-turn conversion (test 4); the den's spawn priority, ring order and proximity fallback (test 5);
the per-den split and the two memoised den constants (tests 5, 13, Tier B); the symmetry resolution
order (test 13, Tier B); the parts income float and the archon-only pickup (test 8); the signal delay
formula (test 9); activation's no-rubble/no-turn path (test 10); the four ladder rungs on exact float64
differences and rung 4's B-on-a-tie (test 11); the sense scan order and insertion-order return
(test 7); and the `IDGenerator` block stream (test 22 / `tests/test_rng.nim`).

Tiers A, A′, A″, B, B′ and C are the **phase-30 gate**. Every accepted divergence is listed in
`docs/RULES-BC16.md` §Divergences with its reason and mirrored in the ledger, and `docs/PARITY.md`
gains a `bc16` section written in the same shape as the `bc22` one — including, honestly: the measured
jar facts, the absence of `SPEC_VERSION`, the JDK-8 requirement and the trap it avoids, the
`NullControlProvider`-for-NEUTRAL requirement, the trace line counts and JVM seconds phase 20 measures,
the peak and mean robot counts, **and the explicit statement that the sub-1.0 branch of
`decrementDelays` is the one behaviour this oracle cannot compare, and why (V1)**.

### `docker-smoke` job — now **eight** episodes

Build the production image, then run `tools/ci/docker_smoke.sh` (which takes the seat count solely
from `certification.game_config.num_agents` and hard-fails with `SEAT-COUNT FAIL:` if the workflow's
**`<SEATS>` = 2** disagrees, and which runs `tools/ci/cert_probe.py`'s certifier-contract probes —
bad-token refusal, `/global` first frame on connect, `Ping → Pong` **payload echo** — against the real
image on the first episode):

1–7. **The bc26 certification-fixture episode and the bc20, bc21, bc24, bc25, bc23 and bc22 episodes,
   all unchanged** → `dist/smoke/replay.json`, `replay-bc20.json`, `replay-bc21.json`,
   `replay-bc24.json`, `replay-bc25.json`, `replay-bc23.json`, `replay-bc22.json`.
8. **A bc16 episode**, new: `SMOKE_EXPECT_YEAR=bc16`, `SMOKE_PLAYER_IDS=awu,scaffold`,
   `SMOKE_CONTRACT_PROBE=0`, `SMOKE_REPLAY_OUT=dist/smoke/replay-bc16.json`, and
   `SMOKE_CONFIG_OVERRIDE={"year":"bc16","pool":"small","seed":<the seed test 13 pins>,
   "gamesPerMatch":1,"maxRounds":900,"perGameBudgetSeconds":90,"matchBudgetSeconds":100,
   "connectTimeoutMs":15000}`. **900 rounds and not 400 or 600**, for two reasons that are both this
   year's: on the pinned map (`river`, 32×32, three archons a side, four dens, **first wave at round
   150**) a 400-round window would show **one** wave and no escalation, while 900 rounds guarantees
   **three scheduled waves, an outbreak level change at round 300 and another at 600, and a viper
   built at all** (a viper is 120 parts against a 2-a-round income, so it lands around round 400–600);
   and the `docker-smoke` substance assertions below need infection and turning to have happened at
   least once, which needs zombies to have reached a unit. 900 rounds also records ~37 s of playback,
   which comfortably outlasts the viewer smoke's 15 s soak (the ecos 2026-08-23 scar). The seed is
   pinned to draw `river`, whose **4.0 archon separation** makes the two factions fight immediately, so
   the episode is short **and** eventful, and `tests/test_bc16_maps.nim` asserts that draw so the map
   cannot drift.

All eight run one game container + two player containers on a shared network with `file://` artifact
URIs and **no `ANTHROPIC_API_KEY`**, so both seats take the scripted path and must still complete. All
eight assert: the game exits 0, **every player container exits 0**, `results.json` carries exactly the
expected key set, `reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`, and the replay
parses as **strict UTF-8 JSON** with `format == "cogame-battlecode-replay"`, the right `year`, and a
non-empty `events` array. A step asserts all eight replays exist and report **eight different `year`
values**.

**The episode substance assertion (the LEARNINGS 2026-09-03 pin), in two parts.** The bc16 episode
passes `SMOKE_REQUIRE_STATS` — the **per-seat** floor, which the script already enforces for both
seats — with `{"units_built":6,"damage_dealt":150,"parts_collected_tenths":500}`. Those three are
things *both* chassis do, including the weak floor: `greenhorn`'s archons build a soldier whenever
parts allow from round 0, its soldiers attack `senseHostileRobots()[0]`, and its archons walk randomly
over parts squares. **The signatures of the year are things only a seat playing well does** —
commissioning a guard or a turret, activating a neutral, killing a den, quarantining an infected unit
— and `greenhorn` does **none** of them, so asserting them per-seat would be asserting that the weak
floor is not weak. They are asserted **across the pair** by one `jq` step in `ci.yml`, reading the
**replay's** `result` block (not `dist/smoke/results.json`, which every episode overwrites in turn —
the bc24 fix):
`([.result.games[0].units_built[]] | add) >= 18`,
`([.result.games[0].damage_dealt[]] | add) >= 400`,
`([.result.games[0].guards_built[]] | add) >= 1`,
`([.result.games[0].infections_suffered[]] | add) >= 1`,
`([.result.games[0].robots_turned[]] | add) >= 1`,
`([.result.games[0].zombie_damage_dealt[]] | add) >= 200`,
`(.result.games[0].zombies_spawned) >= 12` and
`(.result.games[0].outbreak_level_end) >= 2`.
Together they make an idle win machine-visible, which is exactly what the 2026-09-03 round-1
degenerate match lacked. **And the floors are measured, not guessed**: phase 20 runs the real bc16
smoke once, reads the actual per-seat statistics out of `dist/smoke/replay-bc16.json`, and sets the
committed floors at roughly **half the weak seat's measured value** — never above what a correct
episode produces — and where that conflicts with "never below this note's numbers", **the second
constraint wins and the measurement goes inline in `ci.yml`** (the bc23 r1-F22 ruling, restated here
so the builder does not rediscover it: a floor derived from whole 3000-round games is wrong for a
900-round smoke). **If the across-the-pair `robots_turned >= 1` or `guards_built >= 1` assertion does
not hold on the measured episode, the fix is to raise the smoke's `maxRounds` until it does — never to
drop the assertion**: an episode of this year in which nobody was ever infected is not this game being
played.

### `wasm-viewer` job — the bundle is **executed**, against **all eight** smoke replays

`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the bundle is complete
(`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`, `broadcast_core.js`,
`static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then run
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay>
--killfeed-overlap` in headless chromium (Playwright pinned **1.55.0** in both places — the npm module
and the browser download) **once per replay**: `replay.json`, `replay-bc20.json`, `replay-bc21.json`
at `--timeout 90 --soak 10`, and `replay-bc24.json`, `replay-bc25.json`, `replay-bc23.json`,
`replay-bc22.json` **and `replay-bc16.json`** at **`--timeout 120 --soak 15`** for the pacing reason
in §Viewer.

Each run requires: **`data-replay-loaded="true"`** (or the bridge `ready` posted after it — and
**`data-replay-error` must be absent**); three **differing** clock/scorebug readouts at 0 % / 50 % /
100 %; continued advancement across the soak; **`scrub_selector == "#scrub"`** (so a seek was really
exercised and the `#viewpanel` zoom slider was not clicked instead); `#endcard` **computed-shown**
after the 100 % seek carrying a `clan` line; the **`#endcard` no-overflow assertion at 1280×800**
(§Viewer, endcard fix 2); no overlay covering more than 50 % of the board after the soak; and the
`#killfeed`/stat-box overlap check at **360 px, 720 px and 1280 px at both FIT and 2× zoom**.

`--strict-text-bounds` stays deliberately dropped on the replay runs because the board is pannable and
zoomable (`#viewpanel` is kept), which is the exact case the flag's own documentation excludes — and
because **`canvas_text.total: 0` on this renderer covers nothing and must not be read as a pass**
(LEARNINGS 2026-09-08). The counts are still recorded in `viewer-smoke.json`, and the separate
`tools/ci/renderer_fixture.html` step — full-cap `notes` and `motto` on both seats at three widths
**including 360 px**, in the page's own CSS extracted from `client/replay_broadcast.html` at run time —
runs through the same harness **with** `--strict-text-bounds`, because every CI replay is scripted and
carries no LLM text (the cogchemists 2026-08-24 scar). The fixture gains a **bc16 row**.
`node tools/wasm_replay_smoke.cjs` is also run against the bc16 smoke replay **and** the committed
`tests/fixtures/replay-bc16.json`, so wasm32-only failures (int overflow traps, address-space
exhaustion) in the new year module are caught.

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation of
  anything a cog sends. The 2016 engine exists only in the `parity-oracle-bc16` CI job and only as the
  published jar. **No Node in any runtime stage either** — the only Node in this repository is the
  CI-only Playwright harness.
- **Full bytecode metering, and the bytecode-dependent delay decay** (V1, V2). The
  2000/1000/0-`DecisionOps` budget replaces metering, with no mid-turn resumption and no mid-primitive
  cut, and `amountToDecrement` is pinned to 1.0. A Nim-level instrumenter is a compiler project, and
  deriving the decay from the chassis's own op count would make every chassis refactor a rules change.
  The engine's whole formula is tabled and tested anyway, so the divergence is measured, not assumed.
- **A cog-authored Java (or any) strategy class.** Doctrines are **JSON-sheet only**; there is no
  `javac`, no instrumenter `Verifier`, no compile-error round trip and no multi-attempt loop. Nothing
  in the schema is closed against a future sandboxed hook.
- **A bc16 certification fixture, and any new `player[]` entry.** Certification stays on **bc26** and
  `player[]` stays at `awu` + `scaffold` — the cert fixture seats exactly `num_agents = 2` players, so
  a third `player[]` id fails the release with `players_missing` (LEARNINGS 2026-09-04). bc16 is proven
  by its own `docker-smoke` episode and the viewer smoke run against that episode's replay.
- **Armageddon** (V4): `isArmageddon`, the 300/900-round day-night cycle, zombie regeneration, the
  `ARMAGEDDON_*` constants, `ZOMBIFIED` and `CLEANSED`. Both official armageddon maps are **2 archons
  vs 0** over 12 000 rounds with 49 and 104 dens — a single-player survival mode, not a 2-seat match —
  and the converter refuses them by name and by flag.
- **76 of the 98 official maps.** The converter handles any 2016 `.xml` and CI parses **all 98**; v1
  commits the 22 whose geometry is pinned in §Sim module, all of them from the 54 the oracle jar also
  carries. Nothing above 6 400 squares is converted, and nothing outside the 54 is in any pool.
- **Cross-game team memory** (`TEAM_MEMORY_LENGTH = 32`, `setTeamMemory`/`getTeamMemory`), **indicator
  strings, dots and lines, `addMatchObservation`, `Clock.yield`, the profiler**, and **`resign()`** —
  all V5: instrumentation, cross-match state, or an API a JSON doctrine cannot reach.
  `tests/test_bc16_endladder.nim` asserts no chassis reaches `resign`.
- **The official 2016 Java Swing client, the `.rms` match stream and the XStream/Jackson serial
  layer** (V6). Its *sprites* are reused (credited, GPL-3.0); its app is not shipped, not embedded and
  not built. There is no XML **writer** on either side and no `.rms` bytes anywhere.
- **The map's random origin** (V3). Proven inert; the port uses `(0, 0)` and the parity comparator
  normalises the Java side.
- **Worker-side keyframe checkpoints in the viewer.** bc16 seeks re-simulate from the start of the
  game like every other year, which is why check 8 is dispatched with `settle=20000 soak=15`. bc16 is
  the year that makes the case strongest — 3000 rounds is 50 % longer than any other — and keyframes
  remain the obvious next optimisation for the heavy year modules. Deliberately not in v1.
- **A cog-authored comms protocol.** The signal layout in `comms.nim` is the chassis's; a doctrine
  cannot redefine it, cannot set the broadcast radius and cannot add a message kind. In this year every
  signal is heard by the enemy, so exposing the layout would be exposing a channel a doctrine could
  use to leak information it should not have.
- **A `zombie_target` / per-den strike-order knob, and a `friendly_fire` knob.** `den_clear_round`
  decides *when* the faction commits and `opening: scout_zombie_pull` decides *whether* it baits;
  *which* den the strike group breaks is the chassis's call (largest remaining queue, cheapest
  approach), and exposing it would let a doctrine pick a den unreachable on the map in front of it,
  which the anti-inert rule forbids. Friendly fire is *legal* in 2016 (rule 3.2.3) and there is no
  reading under which shooting your own soldiers is a strategy; `tests/test_bc16_baselines.nim`
  asserts neither chassis ever emits one.
- **Per-robot fog in the viewer, and rubble as a buildable resource.** The spectator sees the true
  board; this year has no occlusion mechanic at all (and zombies see everything anyway). Rubble is
  created only by corpses and removed only by `clearRubble`, parts are never created after round 0
  except by den bounties, and the port adds nothing to either.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the war.
- **Battlecode years other than 2016, 2020, 2021, 2022, 2023, 2024, 2025 and 2026.** The registry,
  `game_config.year`, the variant naming and `years/dispatch.nim` all support more; only these eight
  are registered.

*(No `OPEN` section: nothing in the idea leaves a rule genuinely open, and §Feasibility verdict gives
the file-by-file reason for each of the five areas the brief named — zombie spawn schedule, infection,
neutral activation, tiebreaks and RNG. The lost spec creates no ambiguity because there is no prose to
reconcile: the engine source is the only authority and it is complete. The eight places where this port
deliberately differs from that authority are enumerated as **decided divergences V1–V8** with a reason
each, and the five determinism decisions as **D1–D5**; none of them is an open question. The idea's
nine candidate knobs all survive with exact types, ranges and defaults — `retreat_policy` finalised as
the integer `retreat_hp`, `zombie_kiting` finalised as a three-value enum — and **two** are added from
the engine's own measurements: `rubble_clear`, because rubble is this year's terrain and both its
thresholds and its corpse source are exact, and `infection_policy`, because a robot that dies infected
becomes an enemy zombie and no archetype the idea names spends that deliberately. The one question the
idea does not raise and this note had to settle — whether to port a `java.util.HashMap` iteration order
into the sim or resolve it at build time — is settled in §Sim module D3 **by moving it to the map
converter and proving it against the JVM in Tier B**, which is strictly better than either porting it
or approximating it.)*
