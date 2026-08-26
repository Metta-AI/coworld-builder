# r2 fixes — liars-dice

Head: `43159194d42cd46da491f74827bb7215f5168ec2` (origin/main)
CI: https://github.com/Metta-AI/cogame-liars-dice/actions/runs/33017451131 — **success**
(`test` 98339230359, `docker-smoke` 98339230037, `renderer-fixture` 98339230222,
`wasm-viewer` 98339466616 — all four `success`; first attempt, no red run, no retries used).

Push mechanics: direct `git push` returned `No anonymous write access` / 401 again, so the three
commits were replayed one at a time through the Git Data API (blobs → tree with `base_tree` →
commit with the exact message → `PATCH git/refs/heads/main`), preserving messages, trees and file
modes (`tools/ci/build_renderer_fixture.sh` is still `100755` on `main`). After `git fetch origin`,
`git diff HEAD origin/main` is **empty**.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking) | fixed — harness committed, sweep run, constants retuned to the winner | `ae4b86edf0dcb40837810b590b8ab4d869cf9f2f` | `tools/tune_baseline.nim`, `data/tuning/threshold_sweep.tsv`, `src/liars_dice/llm.nim:27-52,199-265`, `.github/workflows/ci.yml:152-165`, `README.md:120-152`, `coworld_manifest_template.json`, `tools/ci/policies.json` |
| F2 (non-blocking) | fixed by errata — design note appended, code left alone | — (coworld-builder: `runs/2026-08-26-liars-dice/design.md`) | `design.md` errata §, two dated entries |
| F3 (non-blocking) | fixed | `93648eb3732de5d1a914aaeb689e54e47f5593ba` | `src/liars_dice/llm.nim:187-197`, `tests/test_bot.nim:153-196` |
| F4 (non-blocking) | fixed | `43159194d42cd46da491f74827bb7215f5168ec2` | `tools/ci/build_renderer_fixture.sh:16-46` |

---

## F1 — No grid/sweep harness for the scripted baselines' parameters (checklist item 7, 2nd sentence)

**What the code did.** `BayesChallenge = 0.40` / `BayesSafe = 0.55` were plain constants with a
prose label. The only parameter evidence was `tests/test_bot.nim`'s two-point head-to-head
(0.40/0.55 vs 0.25/0.35, differing in three ways at once). No harness, no sweep output, no CI step
searched anything.

**What it does now.**

1. **A harness — `tools/tune_baseline.nim`.** A full round robin over a 110-point lattice
   (`chal` 0.05–0.55, `safe` 0.25–0.70, step 0.05, so both shipped baselines' points lie inside
   it). Every point plays every other point head to head: two seats each at a four-seat table,
   **both seatings** (slots 0/2 and 1/3 do not face the same opening rotation), 24 seeds × 30
   deals × both modes = **586 080 episodes**, ~133 s. A point's score is the mean `sim.score` over
   every seat it held, so 0.5 is break even against the whole searched surface. A second column
   scores each point against the shipped `pressure` foil, which is a fixed opponent and never a
   candidate. Statistics are **paired by seed**: seeds are replicates, and the reported band is
   2 s.e. of the paired difference against the argmax.
   To make this possible, `llm.nim` gained `Thresholds` and `scriptedActionWith` (the same body as
   before, taking the two numbers directly); `scriptedAction` is now that call with the named
   baseline's numbers. **The decision rule itself is unchanged** — the calibration test's means are
   bit-identical before and after the refactor.

2. **Its output — `data/tuning/threshold_sweep.tsv`** (120 lines: a provenance header plus all 110
   ranked cells with score, per-seed s.e., the vs-`pressure` column, and a `tiedWithBest` flag).

3. **The sweep's verdict: the shipped pair lost.** The old `0.40/0.55` ranks **80 of 110** at
   **0.49236** — below break even against the lattice. Per the brief I retuned rather than
   asserted a falsehood. The surface is a **plateau, not a peak** (`pTrue` takes discrete values,
   so a threshold only matters when it crosses one): ten cells sit within 2 s.e. of the argmax, all
   at `chal` 0.10–0.20 × `safe` 0.25–0.40. Shipping the noise-selected argmax would be overfitting,
   so the constants are now the **centre of that plateau**:
   `BayesChallenge = 0.15`, `BayesSafe = 0.35` — rank **8 of 110** at 0.51872, paired gap
   **0.00011** against the argmax `0.10/0.30` with a 2 s.e. band of **0.00034** (tied), and one
   full 0.05 step from the cliffs on either side (`safe` 0.45 and `chal` 0.25 each lose ~0.007).
   `pressure` is untouched: it is a deliberate foil, ranked by the sweep (its cell, unpadded, is
   26 of 110), never chosen by it.

4. **A CI gate — `.github/workflows/ci.yml`, job `test`, step "Sweep the scripted baseline's
   thresholds".** Runs the same harness with `--check`: a reduced-but-real slice — the **whole
   110-point lattice**, 8 seeds, dice only, ~20 s — and exits non-zero unless the shipped point is
   the lattice optimum **or paired-tied with it**. It is not a two-point comparison: every cell is
   swept and ranked on every push. Hand-editing either constant without rerunning the harness now
   fails CI.

**Evidence.** CI run 33017451131, job `test` 98339230359, step *Sweep the scripted baseline's
thresholds*, stdout:

```
# shipped point: 0.15/0.35 (BayesChallenge/BayesSafe), rank 1 of 110
# grid optimum: 0.15/0.35 score 0.52114; shipped 0.52114; paired gap 0.00000 (2 s.e. band 0.00000) -> shipped IS the optimum
# plateau: 37 of 110 points are paired-tied with the optimum (2 s.e. of the paired difference)
OK: the shipped point 0.15/0.35 is the grid optimum over 110 points
```

(the CI slice's shorter run has a wider tie band, hence 37 tied cells there vs 10 in the committed
24-seed × 2-mode table.) Side effects, all in the same job's log: the pre-existing calibration test
*improves* — `bayes mean 0.5250000000000001 vs pressure mean 0.4750000000000001`, against
0.5167/0.4833 at the reviewed sha — and no test was loosened, skipped or deleted. A pacing check I
ran locally before committing: with the new thresholds a deal runs 2.80 bids on average instead of
1.31, and 0 of 1200 deals hit the `maxBidsPerDeal` cap, so the retune lengthens the bluffing, it
does not degenerate it.

**Mirrors updated in the same commit** (they quoted the old numbers): the manifest template's
player-facing rules text and the `liars-dice-calibrator` policy description, the calibrator
prompt's "under 40% … at least 55%", and a new README section *Tuning the scripted baseline*
documenting the design, the reproduction commands and the CI slice.

**Checklist item satisfied:** item 7, second sentence — "The baseline's parameters were tuned with
a grid harness, not guessed." The harness, its table and a CI step that re-searches the lattice are
all in the tree at the reviewed head. (Item 7's first sentence and item 1's "no test loosened" are
unaffected and re-verified green in the same run.)

## F2 — The design note's fixed line counts for the speech plate and notes parchment are stale

Disposition: **fixed by errata; no code change** (the reviewer's own finding says the code is right
and the note is out of date, and checklist 15 requires exactly what the code does).

Under the coordinator's sanction I appended a dated errata section at the end of
`/workspace/coworld-builder/runs/2026-08-26-liars-dice/design.md`. Nothing above it was edited and
its acceptance status is untouched. Two entries:

- the *2026-08-26 (r2, F2)* entry records that checklist 15 overrides the note's "2 lines" /
  "3 lines, ellipsized" / "1 line below 480 px", and that `capLines()` → `seatBlock()` size the
  bands from `MaxSayLen`/`MaxNotesLen` instead;
- a second *2026-08-26 (r2, F1)* entry, which I added because my own F1 commit created a new
  note-vs-code divergence: the note states `chal = 0.40, safe = 0.55` in § *The two scripted
  baselines* and test-plan item 16's parenthetical rationale ("the tighter thresholds must beat the
  looser ones") no longer describes why the calibration test passes. **Flagging this explicitly:
  the coordinator sanctioned one errata line for F2, and I appended a second for F1.** If that
  exceeds the sanction, revert the second bullet — the tree is unaffected either way.

**Checklist item:** none violated (the reviewer records F2 as documentation-vs-code only). The
errata protects checklist 15 from a future "restore the note's numbers" edit.

## F3 — The "≤ 3 × faces candidates" invariant is asserted by no test

**What the code did.** The bound held by construction (`min(bidQuantity + RaiseQuantitySteps - 1,
total)` × faces) and nothing counted it, so widening the window would break no test.

**What it does now.** The window is yielded from one place — `iterator raiseCandidates*(sim)` in
`llm.nim`, which the baseline itself iterates, so the test cannot drift away from the code it
guards. `tests/test_bot.nim`'s new test *"the raise enumeration never exceeds 3 x faces
candidates"* drives real episodes (3 seeds × both modes, 4 seats, 4 deals) and at **every** mid-deal
state counts what the iterator produces: each candidate's quantity is inside
`q0 .. q0 + RaiseQuantitySteps - 1` and its face inside `lowFace()..highFace()`, the count never
exceeds `RaiseQuantitySteps * faces`, and — so the bound is not vacuous — the ceiling is actually
**reached** in each mode (18 in dice, 30 in poker).

**Evidence.** CI run 33017451131, job `test`: `[OK] the raise enumeration never exceeds 3 x faces
candidates`, in both the debug and the `-d:release` pass. The refactor is behaviour-preserving: the
calibration means printed either side of it are identical.

**Checklist item:** none (the reviewer scoped it to design-note test-plan item 15); it closes that
test-plan item, and it strengthens item 7's "every order/action is inside its legal bounds" from
outputs-only to the enumeration behind them.

## F4 — The renderer's copies of the server caps had no agreement check

**What the code did.** `client/renderer.js:143-144` and `client/fixtures/worst_case.js:14-15` each
carried their own `140` / `400`, mirroring `src/liars_dice/sim.nim:27-28` by hand. Nothing compared
them, and because the fixture builds its strings from *its* copy, raising a cap in `sim.nim` alone
would under-reserve the band while the fixture stayed green.

**What it does now.** `tools/ci/build_renderer_fixture.sh` reads `MaxSayLen` and `MaxNotesLen` out
of `sim.nim` and refuses to assemble the fixture unless both JS files carry the same numbers,
printing the offending file, its value and the server's on failure. It runs in the
`renderer-fixture` job on every push (and locally for anyone who builds the fixture), before the
copy step, so a stale mirror is red rather than silent. I put the check in the build hook rather
than in `ci.yml` so it also fires on a local build; the hook is still committed `100755`.

**Evidence.** CI run 33017451131, job `renderer-fixture` 98339230222, step *Assemble the worst-case
renderer fixture*: `cap MaxSayLen = 140 agrees in renderer.js and worst_case.js` /
`cap MaxNotesLen = 400 agrees in renderer.js and worst_case.js`. Both drift directions were
verified locally before committing: setting `MAX_SAY_LEN = 150` in `renderer.js`, and
`MaxNotesLen* = 401` in `sim.nim`, each exit 1. The fixture itself is unchanged and still green:
`canvas text: 81758 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`.

**Checklist item:** none directly; it hardens checklist 15's "sized from the cap the server
enforces" against silent drift.

---

## NOTED (not fixed)

- **`liars_dice.nimble` still declares no task**, so the harness is invoked as
  `nim r -d:release --path:src tools/tune_baseline.nim` (documented in the README and in the CI
  step) rather than `nimble tune`. A task would be a convenience only; the entry point, the table
  and the gate all exist without it.
- **The committed table is not regenerated in CI** — the full 586 080-episode sweep takes ~2.2
  minutes, so CI runs the 110-point / 8-seed slice instead and the full table is produced offline
  by the same binary and the same code path. Regenerating it in CI would be the stronger claim if
  the runtime budget ever allows it.
- **The `pressure` foil was not swept.** It is deliberately suboptimal (its unpadded cell ranks 26
  of 110) and its role is to be catchable, so tuning it would defeat its purpose; the sweep ranks
  it rather than choosing it. If a later round wants provenance for `pressure` too, the harness
  already scores every point against it.
- **`tools/ci/policies.json`'s `liars-dice-needler` prompt** still says "Bid one step higher than
  the calibrated line" and challenges "under 35% likely". That is a champion's own strategy, not a
  mirror of the constants, so I left it alone.
