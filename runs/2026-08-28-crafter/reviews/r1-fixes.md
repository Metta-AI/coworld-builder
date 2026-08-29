# r1 fixes — crafter (Metta-AI/cogame-crafter)

Head: `2a62f81c2d6ac29a2c9002021ce6884a784e1dcc` (main)
CI: https://github.com/Metta-AI/cogame-crafter/actions/runs/33231383944 — **success**
(`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; green on the first attempt, no reruns)

25 findings, 25 commits, one per finding, all on `main`. Every commit was
verified locally first: the sandbox has no Nim, so one was installed
(`nimby 0.1.26` → Nim 2.2.4, `nimby --global sync nimby.lock`) and all nine
shards were run in **both** debug and `-d:release` before pushing. Nothing was
skipped, deleted or loosened; four commits **add** tests.

| finding | commit | disposition | checklist item |
|---|---|---|---|
| F1 | `67c0b9dd` | fixed (blocking) | 1 — no test skipped; 10 — manifest |
| F2 | `19509ea2` | fixed | 2 — replay re-derivation (record content) |
| F3 | `4739094f` | fixed | 2 |
| F4 | `e3d7799c` | documented divergence | — |
| F5 | `2cbeaf2f` | documented divergence | 8 |
| F6 | `200f5b9d` | documented divergence + dead-loop tidy | 7 |
| F7 | `208d1c14` | documented divergence | 14 |
| F8 | `96202fe2` | documented divergence | — |
| F9 | `760c9bd1` | documented divergence | 3, 13 |
| F10 | `d61e5dc0` | documented divergence | 13 |
| F11 | `43577023` | documented divergence | 13 |
| F12 | `3a82fac1` | documented divergence | 9 |
| F13 | `d36f0830` | fixed (test made real) | 1 |
| F14 | `5b12b90d` | fixed (+ a second, worse bug it exposed) | 7 |
| F15 | `390eae3b` | fixed | — |
| F16 | `4f748e73` | fixed | — |
| F17 | `6f030541` | fixed | 3, 14 |
| F18 | `0bd8d924` | fixed (dead code removed) | 4 |
| F19 | `6383fcfc` | fixed | 2, 7 |
| F20 | `e3120b8b` | documented divergence | — |
| F21 | `6f3ed6aa` | documented divergence | — |
| F22 | `f00cdcc9` | fixed | — |
| F23 | `e87cbef3` | fixed | — |
| F24 | `2a62f81c` | fixed (the real sweep, and the pick it names) | 7 |
| F25 | `acf2c37f` | fixed | — |

Nothing was disputed: every finding reproduced from the code. Ten are recorded
as divergences in `docs/PORTING-CRAFTER.md` rather than changed in code —
each with the reason, per the note's own rule that an *undocumented* divergence
is the defect.

---

## F1 — a `skip()` and three deleted assertions in `tests/` *(blocking)*

**Was:** `tests/test_crafter_manifest.nim:202-215` called `skip()` whenever
`python3 -c 'import coworld'` failed. `ci.yml` never installs the CLI, so item
38 ran nowhere and the shipped `game.runnable` shape was asserted by nothing
that executes. The scaffold's `source_url`, `type: player` and
`not game.image` assertions had gone with it, and `game.runnable` had no
`source_url` at all where the starter's `coworld_manifest_paintbot.json` ships
one.

**Now:** `coworld_manifest_template.json`'s `game.runnable` carries
`"source_url": "https://github.com/Metta-AI/cogame-crafter/tree/main"` — the
starter's shape, and what `source-resolves` reads at certification. Item 38 is
unconditional: it enumerates every `{{...}}` placeholder in the template,
asserts the set is exactly `{{CRAFTER_IMAGE}}`, substitutes it the way
`coworld build` does, re-parses, and asserts the structure
`validate_upload_manifest` requires (top-level key set, `game` key set,
`runnable` key set including `source_url`, every declared player's key set,
every variant's key set). The CLI load still runs wherever the CLI exists —
that branch is kept, it simply no longer swallows the whole test when it is
absent. A second test restores the three deleted assertions.

**Evidence:** `nim r --path:src tests/test_crafter_manifest.nim` →
`[OK] the manifest loads: the placeholders resolve and the shape validates`
plus the printed `(no coworld CLI here; the structural half above is what ran)`,
and `[OK] the runnable and every declared player resolve to this repo`. Green
in CI run 33231383944, job `test`, in both debug and release.
`grep -rn 'skip()' tests/` → no matches in the tree.

## F2 — 30 of 44 `directive` records carried `"view": null`

**Was:** `boundedDirectiveRecord` dropped the whole observation *first* and only
then shortened `say`, at a 4000-rune cap. **Now:** `say` shrinks first and the
view is dropped only if the record cannot fit with no `say` at all;
`MaxDirectiveRunes` is 6000. Measured worst case over 24 episodes of both
variants with a full 160-rune `say`: **4461 runes** (probe run in-sandbox), and
the observation alone tops out at 3794.

**Evidence:** new test
`[OK] the record keeps the observation even with a full-cap say` —
`record["view"] == observation` with `say` at `MaxSayRunes`. The cap is
recorded as §F of `docs/PORTING-CRAFTER.md` (the note bounds `say` and `notes`
but not the record).

## F3 — `achievementTick[]` was on the absolute clock

**Was:** `recordUnlock` stamped `sim.tickCount`; `survivalTicks` /
`results.finalTick` and every clocked rule are run-relative, so unlocks sat up
to `gameStartTick` past the end of their own episode (48 ticks in the fixture,
hundreds with the shipped `lobbyJoinTimeoutTicks: 2400`), and the viewer's
endcard — which derives each row's DAY from `chip.t / (maxTicks / day)` —
dated every unlock late. **Now:** `sim.runTick()`.

**Evidence:** new test
`[OK] achievementTick is on the RUN clock, the one finalTick is on` plays a
real episode behind a 240-tick lobby and asserts every unlock tick is inside
`finalTick` **and** that the earliest precedes `gameStartTick` — impossible on
the absolute clock. `gameHash` mixes only the unlock *mask*, so every committed
replay still re-derives (`[OK] every committed fixture carries the current
GameVersion`, and CI's `ok: loaded forager-seed42.replay, advanced 300 frames`).

## F4, F5, F7, F8, F9, F10, F11, F12, F20, F21 — documented divergences

Each is real, each reproduced, and each is now a lettered section of
`docs/PORTING-CRAFTER.md` (§G–§P) with the reason it stands:

- **F4 §G** `budget` is a 22nd derived kind. The note's own `budget_guard` chat
  record has no other way to reach the feed; it is not a beat.
- **F5 §H** `throttled` (a provider 429 with no model left to rotate to) is a
  different fact from `rate_guard` (this client declining to issue a request,
  no network wait) and phase 60 needs to tell them apart; `disconnected` is
  unemitted because a one-seat game has no round barrier to stall.
- **F7 §I** the cog and the three creatures are committed
  `gemini-2.5-flash-image` sprites split by `scripts/art/split_cog_sheet.py`,
  not a `rig_art.nim` composite (the terrain bake *is* the note's). Nothing is
  downloaded at build or runtime; at a 24 px tile with `showPlayerLabels:
  false` and no board text the sprite is the only thing that can carry facing.
- **F8 §J** `roster.nim` did not survive as a module: with one seat and no
  squads what was left was a dozen procs over the sim's own state.
- **F9 §L** `#viewpanel` is unmodified but moved after `#scrub`, because
  `viewer_smoke.mjs` resolves `#scrub, #seek, input[type=range]` in **document
  order** and was driving the zoom bar (CI 33225446565, 33226980062). The
  element is `position: absolute`.
- **F10 §K** `-s STACK_SIZE=8388608` (emsdk's 64 KB default trapped
  `crafter_load_replay`) and `-s INITIAL_MEMORY=33554432` (CI reports
  `heap 32 MB`).
- **F11 §M** one tick per frame at 24 fps with integer speed chips — the
  starter's transport carries speed as an integer tick budget per frame and
  cannot express `0.5`. The arithmetic the note's cadence protects still holds
  with 4× margin: CI's `soak: 10s of playback kept advancing ("3 / 950" ->
  "243 / 950")`.
- **F12 §N** the 16384-byte read is the JSON *envelope*; a 4096-byte cut of it
  raises in `parseJson` on every real reply. The reply *text* is still capped
  at 4096 **runes**.
- **F20 §O** the within-tick creature tiebreak is kind order. Re-sorting the
  at-most-three would change every recorded `gameHash` for no observable
  difference (`stepCreatures` walks by kind pass; creatures never share a
  cell).
- **F21 §P** the sapling draw mixes `idx(x, y)` (same 1-in-10, same purity) and
  a point-blank skeleton shot applies its 2 arrow damage directly rather than
  spawning an arrow inside the cog's own cell.

## F6 — forager's rules 1 and 4

Documented in §D (rule 1 fights rather than walls off — two of the twenty-two
achievements are only reachable by fighting; rule 4's energy condition; one
`place_stone` per turn because the only side a cog can seal without walking out
of its own hole is the one it faces). The rule-4 `while … break` that could
only ever execute once is now the `if` it always was — byte-identical
behaviour, confirmed by every replay still re-deriving.

## F13 — the vacuous item 1

`check a.config.seed == b.config.seed` and `seed == 4096 div 4096 * seed` are
gone. Item 1 now asserts all three sims played (`primitivesExecuted > 0`), that
their **live** grids differ from each other, and that regenerating from each
settled sim's own config reproduces the reference cell for cell with the live
grid differing only in the cells the cog changed.

## F14 — the post-pass could sand over its own guarantee (and a worse bug behind it)

Steps 2-5 now run **to a fixed point** (three sweeps; the second is a no-op on
every seed the first settles). Adding the assertion the reviewer asked for —
"after the whole post-pass a *reachable* tree, water and stone still exist" —
immediately failed on **seed 105, both variants**: `carve` skipped coal, iron
and diamond, so one coal cell severed the only corridor to the only reachable
tree, and no cog can mine coal before it has the wood for a pickaxe. The
corridor now sands ore too; the ore minima are step 6 and restore any count it
spends.

**Evidence:** new test
`[OK] the guaranteed tree, water and stone are still REACHABLE afterwards`
over 200 seeds × 2 variants — it fails on seed 105 before this commit. An
in-sandbox sweep of 400 seeds × 2 variants shows exactly **2 of 800 worlds
change** (seed 105 in each variant); the fixture's seed 42 is untouched, so
every replay still re-derives. `docs/PORTING-CRAFTER.md` §A is rewritten to
match (it previously promised the corridor never touches ore).

## F15, F16, F22 — documentation

- **F15** the "Three things" sentence listed five and this round added eleven;
  it now states that every divergence is a lettered section, with no count.
- **F16** `docs/RULES.md` gained a §Scoring: `scores[0]`, win/winner, the
  paper's geometric mean, why a single episode has no `p_i`,
  `tools/crafter_score.py`, the ten-episode floor and "**not** what the ladder
  ranks" — the three statements the note requires of that file.
  `tools/crafter_score.py:16` already claimed "docs/RULES.md says both"; it is
  now true.
- **F22** all five stale comments: `decide.nim`'s 12/55/110 → 24/56/112 and its
  `scout` → `forager`; `crafter_replay.nim`'s "660 ticks over a 169-cell grid"
  → 1344 over 4096; the fpv panel's "7x7" → 9x9, fixed at its **source** in
  `tools/build_broadcast_page.py` and re-derived so the derivation check still
  passes; and the viewer test's false claim about README.md.

## F17 — the page-derivation check was `|| true`

CI now checks out `Metta-AI/coworld-ctf` at the pinned sha the page was derived
from (`a7484eb`, which is the sandbox mount's HEAD) into `.starter` and runs
`python3 tools/build_broadcast_page.py --starter .starter --check` with no
`|| true`. The script now **fails** instead of returning 0 when `--check` is
given a starter that is not there.

**Evidence:** CI run 33231383944, job `test`, step "The broadcast page is the
derived page" → `client/replay_broadcast.html matches the derivation`.

## F18 — dead `playerNames`

The table was declared, read once and written nowhere, so the branch that
consulted it was dead and the join always seated `"seat-<slot>"`. Removed;
the placeholder name is written directly with a comment saying why a join
cannot carry one (the real policy name is only known at registration, which is
where it is written into the roster and the replay's join record). No
behaviour change.

## F19 — `wake_up` was never awarded when a bite ended the sleep

`stepTick` step 7 woke the cog on creature/arrow damage without going through
`applyPrimitive`, so `wokeRested` was never set on that path. It now makes the
same test `applyPrimitive` makes (`energy >= 9 and sleepRunStartEnergy < 9`)
and emits the same `sleep{state:end}` event, matching the note's predicate
("a run of ≥ 1 `sleep` ticks that began with `energy < 9` **ends** with
`energy == 9`") and its "and so does taking creature/arrow damage".

**Evidence:** new test
`[OK] wake_up also unlocks when a bite is what ends the rested run`, beside the
existing healthy-path test.

## F23 — committed ELF binaries

Ten mode-100755 executables (~8 MB) are untracked and ignored, with the `.nim`
sources explicitly kept (`git check-ignore -v` confirms
`tests/test_crafter_world` is ignored and `tests/test_crafter_world.nim` is
not).

## F24 — the tuning grid was a 9-row table that did not reproduce

Running `tools/tune_baselines.nim` prints **787** achievements for the shipped
cell where the committed file records 369: the file was not this harness's
output. It is now, literally — `--json` prints the file — over the **full
1296-cell matrix**, with `thirstThreshold` swept (the reviewer's specific
complaint: it was in `pick` and in no grid row) and every cell reporting every
tunable plus its certification-seed episode.

Running the real sweep moved the pick, so the shipped defaults moved with it:
`sleepTicks 8 → 16`, `shelterStones 4 → 2`. The pick is **constrained** to
cells whose cert-seed episode survives ≥ 900 ticks and unlocks ≥ 6 — that
episode is the CI replay `viewer_smoke.mjs --soak 10` runs against, and
`tests/test_crafter_engine.nim` already asserts that floor, so an unconstrained
sweep would have shipped a baseline the repo's own tests reject (the
unconstrained winner dies at tick 400). The constraint is in the harness's
docstring, in the recorded `metric` string and in §D.

**Evidence:** `tools/tune_baselines.nim --check` run in-sandbox after the
change → `the shipped DefaultBaselineParams are still the sweep's pick`,
exit 0. `tests/test_crafter_driver.nim` additionally asserts the grid is the
whole matrix (every tunable takes more than one value across it, every cell
carries every tunable, the pick's value for each was actually played). CI's
docker smoke on the cert seed still reports
`replay summary ok: complete death 14 unlocked` and a 949-tick replay.

## F25 — no CI grep for surviving starter identifiers

`ci.yml` now greps the whole tree, spelled through character classes so the
step cannot match itself, allowing exactly three files: the byte-identical
`client/chrome_common.js`, the one-line compatibility alias in
`src/crafter/wire_constants.nim` that lets it stay byte-identical, and the
viewer test that names the old namespace in order to assert the rename.

**Evidence:** CI run 33231383944, job `test` →
`no starter identifier survives outside comment history`.

---

## NOTED (not fixed) — outside this round's findings

1. **`longnight` seeds 259 and 291 have no tree within 12.** Found while
   building F14's regression sweep, and it **pre-dates** this round (it
   reproduces on `71bf90d`). The cause is not the carve: post-pass step 2 falls
   back to `firstGrassAtRing(6)`, which returns `ok = false` when that ring
   holds no grass, and nothing widens the search. The shipped invariants test
   sweeps seeds 1..200, so it does not see them. A fix would be to widen the
   ring search until a host cell is found. Left alone: it is not a finding in
   this review and it changes generated worlds.
2. **`results.names[0]` carries `PLAYER_POLICY_LABEL`** (F18's other half). The
   note's example is a platform player name; whether the platform injects one
   into the game config is outside this repo, so nothing was changed. Both name
   spaces are present and separate either way.
3. **The committed `docs/plans/2026-08-28-crafter-design.md`** is excluded from
   the F25 grep (`--exclude-dir=plans`): it is the design note verbatim and
   quotes the starter's paths on purpose.
