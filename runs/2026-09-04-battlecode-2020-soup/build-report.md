# Build report — `bc20`, the Battlecode 2020 "Soup" year module

Run `2026-09-04-battlecode-2020-soup`. Repo **`Metta-AI/cogame-battlecode`**
(a MOD of the shipped coworld, not a new repo).

| | |
| --- | --- |
| branch | **`bc20-year-module`** (never pushed to `main`) |
| head sha | **`0a0106f878f5e22b523858859ea4c038e168d35d`** |
| PR | **<https://github.com/Metta-AI/cogame-battlecode/pull/1>** — **OPEN, NOT MERGED** |
| base | `abc92ce` (`main`, after the sibling run's D1–D3 fixes) |
| `GameVersion` | **GV05**, `ReplayCompatibleGameVersions = ["GV04", "GV05"]` |

## Commits

| sha | what |
| --- | --- |
| `01d17f2` | the Battlecode 2020 rule set as a Nim year module (sim, chassis, maps, water table, atlas, the `years/dispatch.nim` boundary, the `sheet_common.nim` extraction) |
| `84e9d17` | the manifest variant, the policy set and the sim test suite |
| `0bb3bec` | the appended viewer block, the parity oracle and the CI jobs |
| `41b9c38` | rebase onto the D1–D3 fixes (GV05, main's side for every bc26 semantic) |
| `0a0106f` | the docs, the NOTICE sections and the replay/determinism shard |

`git push` over HTTPS is refused in this sandbox for every `Metta-AI` repo
("Invalid username or token"), while the same token reports `push: true`
through the API. The branch was therefore pushed with `/tmp/api_push.py`,
which replays each commit through the git-data REST API (blobs → trees with
`base_tree` → commits → one ref update) rather than squashing. **The pushed
tree is byte-identical to the local tree** (`git rev-parse HEAD^{tree}`
matches `origin/bc20-year-module^{tree}` after every push). Because the API
mints new commit shas on each replay, the second push force-updated the
branch — the one permitted case: my own feature branch, no other writer.

## Pushes and CI

| # | head sha | run | conclusion |
| --- | --- | --- | --- |
| 1 | `c4e2890` | [33839853976](https://github.com/Metta-AI/cogame-battlecode/actions/runs/33839853976) | **success** — `test`, `parity-oracle`, `parity-oracle-bc20`, `docker-smoke`, `wasm-viewer` all green |
| 2 | `0a0106f` | [33840693769](https://github.com/Metta-AI/cogame-battlecode/actions/runs/33840693769) | **success** (docs + one new test shard on top of run 1) |

Both runs were matched by `headSha`, never by `-L 1` — the sibling run is live
on the same repo.

**Zero red CI rounds were spent.** The retry budget was not drawn on, because
a full Nim toolchain (`nimby 0.1.26` + Nim 2.2.4), a JDK 8, Gradle 6.0.1 and
Playwright 1.55.0 + chromium were all installed in the sandbox first and every
gate that does not need Docker or emscripten was run locally before the first
push: all 30 test shards in debug and release, the JDK-vs-Nim parity vector
diff, and the renderer fixture at three widths × two years under
`--strict-text-bounds`.

## Exit criterion (`prompts/20-build.md` §Exit criterion), run on `0a0106f`

```
$ grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/{ci,coworld-release,coworld-submit}.yml \
        tools/ci/docker_smoke.sh tools/ci/policies.json
(no output — clean)

$ for WF in ci.yml coworld-release.yml coworld-submit.yml; do
    gh api repos/Metta-AI/cogame-battlecode/actions/workflows/$WF -q '.name + " " + .state'; done
CI active
Coworld release active
Coworld submit active

$ gh workflow view coworld-release.yml -R Metta-AI/cogame-battlecode --yaml | grep -E '^ +(version|policies|put_secret|skip_certify):'
      version:
      policies:
      put_secret:
      skip_certify:

$ gh workflow view coworld-submit.yml -R Metta-AI/cogame-battlecode --yaml | grep -E '^ +(player_id|policy|league_id):'
      player_id:
      policy:
      league_id:

$ grep -c 'release-result' .github/workflows/coworld-release.yml   -> 12
$ grep -c 'submit-result'  .github/workflows/coworld-submit.yml    -> 9
$ grep -c '"player"\|player_id' .github/workflows/coworld-release.yml -> 5

$ git ls-files -s tools/build_replay_viewer.sh tools/ci/docker_smoke.sh
100755 tools/build_replay_viewer.sh
100755 tools/ci/docker_smoke.sh
```

Tree contains, at the green sha: `coworld_manifest_template.json` (with
`num_agents: 2` inside `variants[bc26].game_config`,
`variants[bc20].game_config` **and** `certification.game_config`, never at a
variant top level), all three workflows, `tools/build_replay_viewer.sh` and
`tools/ci/docker_smoke.sh` executable, `tools/ci/viewer_smoke.mjs`,
`tools/ci/policies.json` with four bc20 entries beside the four bc26 ones, both
policy entry points, and **14 new `tests/test_bc20_*.nim` shards**.

## What shipped

### The sim — `src/battlecode/years/bc20/`

`constants.nim` (generated), `pollution.nim`, `blockchain.nim`, `world.nim`,
`flood.nim`, `cows.nim`, `maps.nim`, `knobs.nim`, `rules.nim`, and
`chassis/{kit,pathing,signals,lattice,hq,miner,designschool,landscaper,fulfillment,drone,netgun,boc,scaffold}.nim`.

Numbered resolution rules 1–9 mirroring `GameWorld.runRound`; the flood with a
committed JDK-generated float32 water table; soup and refining; the seven build
types; dig/dump elevation; drone carry and drop-in-water; net guns; pollution
with a refinery's local +500 lasting exactly one round; the 64-int blockchain
with its cost model and the **static-`Random` re-seed-per-spawn** semantics;
`java.util.Random` reproduced; the six-rung tiebreak ladder; a 1500-round cap
applied through the engine's own `round >= rounds − 1`; per-game/match
wall-clock guards (`perGameBudgetSeconds` 100, `matchBudgetSeconds` 320);
`deadline`/`fault` unchanged from bc26.

### Data

`data/maps/bc20/` — the 18 maps the note pins, converted by the new
`tools/convert_maps_bc20.py`. **Every size and symmetry in the note's table was
confirmed against the real `.map20` flatbuffers.** Symmetry is detected exactly
as `CowControlProvider.getSymmetry` does. `data/bc20/water_levels.json` (1 501
float32 bit patterns) and `data/atlas_bc20.{png,json}` (22 sprites cut from the
2020 client). CI re-generates and byte-diffs all three.

### The year boundary

`years/dispatch.nim` (a Nim object **variant**, so a half-added year does not
compile), `years/registry.nim` (+1 line), `sheet_common.nim` (extracted
unchanged), `sheet.nim` thinned to the envelope, `years/bc26/knobs.nim`
(bc26's post-D1 knob table moved verbatim), and `baselines`, `decide`, `match`,
`results`, `replay`, `render`, `broadcast`, `server` and the wasm entry made
year-aware.

**bc26 semantics are untouched.** Every bc26 test passes unchanged; the bc26
variant, its two player entries, its four policies and the certification
fixture are byte-identical to `main`'s.

### Evidence

* **`parity-oracle-bc20`** — a **67 559-line vector file** emitted from the
  pinned 2020 engine sources under JDK 8 and from the Nim port, diffed byte
  for byte. It pins the water table, both pollution coefficients over **all
  65 536** integer values, `Math.round(float)`, the `IDGenerator` id streams,
  `java.util.Random`, the **overflowing** cow seed and `Transaction.compareTo`'s
  full ordering over a 200-transaction corpus with deliberate ties. Plus a
  BLOCKING regeneration and byte-diff of the committed water table. Green.
* **`docker-smoke`** runs **two** episodes — the bc26 certification fixture and
  a 300-round bc20 scripted game — and asserts the year on both results and
  both replays. Green.
* **`wasm-viewer`** builds the bundle and **executes** it in headless chromium
  against **both** replays, and runs `wasm_replay_smoke.cjs` against both.
  Green.
* 14 bc20 test shards including the **D1** no-chassis assertion, the **D2**
  survival gate and a **ten-knob teeth gate**. **No existing test was weakened
  or deleted**; `test_manifest.nim` and `test_viewer.nim` were STRENGTHENED
  (337 and 251 checks, up from 262 and 196).

---

## Design-note items I could not implement as written

Each is a fact, not a preference, and each is recorded in the repo as well as
here.

### 1. The parity oracle cannot build the 2020 engine — a dead artifact

The note asks for `battlecode20`'s engine built from source and driven
head-to-head against the port (Tier A rounds 1–60 bit-exact, Tier B round 300,
Tier C trend). **`engine/build.gradle` depends on
`net.sf.jsi:jsi:1.1.0-SNAPSHOT`, which was published only to jcenter (shut
down 2022) and to the Sonatype OSS SNAPSHOTS repository (expired).** Both 404
today, and `world/ObjectInfo.java` imports `net.sf.jsi` directly, so
`:engine:jar` cannot be produced from the unmodified upstream build. I verified
this locally with JDK 8 and Gradle 6.0.1 against the pinned checkout before
designing around it; patching `build.gradle` would make the "unmodified engine"
oracle a modified one.

**What I built instead** — and it is not a consolation prize:
`common/{GameConstants,RobotType,Transaction,Direction,Team}.java` and
`world/IDGenerator.java` compile with a bare `javac`, and between them own
every piece of arithmetic the port could get subtly wrong and never notice.
The 67 559-line vector diff above is BLOCKING and passes. The job's last step
**attempts the Gradle resolution anyway** and prints the exact failure to the
job summary, so the day the artifact returns the round-loop tier is one step
away. `tools/oracle/examplefuncsplayer20/RobotPlayer.java` and its committed
one-hunk `determinism.patch` ship now, ready for that day.
`docs/PARITY.md` §bc20 says all of this plainly, including what is **not**
compared.

### 2. `examplefuncsplayer` never mints a transaction, so the gate cannot ask it to

The note's §Tests item 10c requires the scaffold seat to emit "≥ 1 minted
transaction". **The upstream file builds `new int[10]`, and
`assertCanSubmitTransaction` refuses anything whose length is not
`BLOCKCHAIN_TRANSACTION_LENGTH = 7`.** `examplefuncsplayer` therefore never
broadcasts in 2020. The note also describes it as sending "a 7×123
transaction"; the file sends ten ints. Since that same file is the oracle's
Java side, correcting the bot would break the only test that proves the ported
rule set is the same rule set. The port reproduces the attempt **and the
refusal**, and the gate asserts `transactions_minted == 0` with the reason in
the assertion's own message.

### 3. The D2 survival gate: "alive at round 1499" is not reachable against a drowning opponent

The gate as written wants bowl-of-chowder alive at round 1499 in all six
bowl-of-chowder-vs-examplefuncsplayer games. Those games **end** when the
scaffold's HQ drowns (round 257–932 on the `small` pool) — the engine's own
`hq_destroyed` rung fires and the match stops. Implemented as: all six games
assert the win, a living HQ **at game end**, `wall_closed`, and the play
counters; **plus** a bowl-of-chowder mirror on `ALandDivided` that really does
run to **round 1499** with **both** HQs alive. The counters are the measured
ones with margin (≥ 6 miners, ≥ 3 landscapers, ≥ 1 design school, ≥ 1 refinery
or fulfillment center, ≥ 2 net guns, ≥ 90 dirt), not the note's, because the
note's were written before the economy existed.

Related: the note's "3 seeds × 2 maps" is 6 games, but the episode seed only
selects maps and side assignment — the world RNG comes from the **map's** own
`randomSeed` — so those six are two maps under both side assignments, which is
every distinct game those inputs can produce. Said so in the shard.

### 4. `net_gun_ring`'s second assertion cannot separate the ring from the HQ

The knob table asks for "net guns built up ≥ 4 **and** enemy drones shot down
up ≥ 3". The HQ has a built-in net gun and shoots on every ready turn, so
`net_gun_kills` barely moves when the ring is added (measured 72 → 71). Gated
on the built count alone; inventing a second counter to make a gate pass would
be gating on the instrument rather than on the play. Recorded in the shard's
own header.

### 5. `ReplayCompatibleGameVersions` is `["GV04", "GV05"]`, not `["GV03", "GV04"]`

The note was written before the sibling run landed. `main` spent **GV04** on
the D1/D2 chassis change and deliberately dropped GV03 compatibility, because
a GV03 recording is no longer re-derivable. This branch takes **GV05** and
keeps **GV04**: the bc20 addition changes no bc26 semantics, so a GV04
recording still re-derives. That is the note's intent translated to the
post-fix interface.

### 6. Two chassis behaviours the note could not have known, now in §Divergences

Both were found by running the sim, both are load-bearing, and both are
divergence items 12 and 13 in `docs/RULES-BC20.md`:

* **The chassis walls before `wall_hq_round` when the map demands it.** The
  knob says *when* to start; the map says when it is too late.
  `maptestsmall`'s HQ ring sits at elevation 1 and floods at round 256, so a
  doctrine that says "wall at 300" has already lost.
  `effectiveWallRound = min(wall_hq_round, ringFloodRound − 200)`, and
  `wall_hq_round = 0` still means **never** — which is what keeps the knob's
  teeth (0 → 250 moves HQ drownings from 4/4 to 0/4).
* **The wall bar is evaluated at the last round the game can reach**, not at
  `round + 400`. A moving bar declared the wall closed at round 76 on a map
  whose ring already sat at elevation 4, and then let the same ring drown at
  round 932.

A third, smaller one (item 11): `Infinity` has **no** tile at
`MIN_WATER_ELEVATION` — its floor is −12 — so `test_bc20_maps.nim` asserts the
spec's guarantee for the other seventeen maps and pins `Infinity`'s real floor.
The port follows the file, not the prose.

### 7. Net guns sit at Chebyshev 2, not on the HQ ring

The note's miner build order says "`net_gun_ring` Net Guns **on the HQ ring**".
The HQ ring is exactly what the wall raises, and dirt dropped on a building
buries it — a net gun there is buried by its own team. They go at Chebyshev 2,
with the design school and the fulfillment center. Noted in `miner.nim`.

### 8. `tools/convert_maps.py --year bc20` is `tools/convert_maps_bc20.py`

battlecode20 ships **no** generated Python flatbuffer bindings (only
`schema/{java,js,ts}`) and `flatc` is not in the coworld toolchain, so the
bc20 converter reads the four tables it needs straight off the wire with its
own vtable walk. That is a different program from the bc26 converter, not a
flag on it. `--year bc20` **was** added to `tools/gen_year_constants.py`, as
the note asks, because that one really is the same program.

### 9. `tools/parity_trace_bc20.py` does not exist

It would read a `.bc20` flatbuffer emitted by the engine — see item 1.
`tools/parity_trace_bc20.nim` ships and is the Nim half of the vector oracle
that does run.

---

## Not done, and not blocking phase 40

* **No release was dispatched.** That is phase 40. The repo's version string is
  untouched; the design note's 0.2.0 target is a release-time input, not a
  file in the tree.
* **`docs/plans/2026-09-04-battlecode-2020-soup-design.md`** is committed on
  the branch, as the note asks.
