# r1 fixes — bc16 (RECONSTRUCTION FROM GIT)

**Provenance.** The fixer (`coworld-builder-fixer`, thread `sthr_015kbfqU4odGWbQMbPALwGTF`) was
dispatched at 09:06Z by a session that died minutes later. The fixer finished its round anyway
but its own `r1-fixes.md` went to that session's container and was never committed, so it is
lost (see `r1-review.md`'s header for the same loss and its cause).

Unlike the review, this file is **reconstructible from primary evidence**: the fixes are ten
commits in `Metta-AI/cogame-battlecode`, each naming its finding, quoting the code it changed and
stating what it verified. Every row below is taken from `git log`/`git show` on the landed range
`fbc7d345..46b92ae` and from the CI runs cited — not from the fixer's chat reply. The
checklist-item column and the never-weakened audit at the end are the **coordinator's own**
determinations, made at 12:35Z from the diff.

## Landing

| | |
|---|---|
| branch | `bc16-r1-fixes`, 10 commits, off `main` @ `fbc7d345` |
| branch CI | `ci.yml` run [34338896940](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34338896940) @ `95ef6c9009`, conclusion **success**, 11/11 jobs |
| PR | [#11](https://github.com/Metta-AI/cogame-battlecode/pull/11) "bc16 r1 review fixes (F1-F11)", merged `--merge` 11:38:19Z |
| main after merge | `fbc7d345` → `46b92ae5ff9a78be61c659f4a2eff861aa17b838` |
| main CI | run [34346628919](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34346628919) @ `46b92ae5` — see §Main CI below |
| files touched | 14 (`+797/-90` excluding the re-recorded fixture blob) |

## Finding → commit → change → checklist item

| finding | commit | what changed | acceptance-checklist item |
|---|---|---|---|
| **F2** (the one checklist-falsifying finding) | `2e429719` | `tools/ci/renderer_fixture.html` gains its bc16 row: both seats at the full 280-rune `notes` and 48-rune `motto`, `plainWords16()`'s widest eleven clauses (502 chars), every stat measured as the widest value reached on any round of a `bulwark` mirror over the six `small` maps at the 3000-round cap, `#bc16-doctrines-toggle` beside its seven siblings, a `bc16` FILLED entry. `ci.yml`'s existing `--strict-text-bounds` fixture step now lays bc16 out at 360/720/1280 px. **The row found two real clipping defects, both fixed** in bc16's own additions block in `client/replay_broadcast.html` (`#bc16-horde` was a ~570 px `nowrap` flex line inside a `max-width:92%; overflow:hidden` box, clipping `DENS`, the mini-timeline and the tiebreak countdown to nothing at 360 px and 720 px). | **15** (satisfied — this is what F2 falsified) |
| **F1** | `3a693cd0` | The dead `#endcard.show ~ #bc16-…` suppression rule is re-keyed to `html[data-year="bc16"] #chrome:has(#endcard.on) #bc16-…` — the class the page actually toggles, parent-scoped instead of sibling-scoped. `:has()` verified supported in the smoke's chromium (141.0.7390.37). **Both grep tests that could not see the defect are replaced**: one now reads the whole `<style>` block and refuses `#endcard.show` in any selector shape; the other pins the live shape, asserts both dead shapes absent, and asserts all five boxes are named. The real gate is a computed style in the renderer fixture. `chrome_common.js` untouched; nothing above the additions banner touched. | **14** (chrome provenance), **15** |
| **F4** | `c70572002b` | Both survival measurement tables regenerated from run `34322655506`'s own numbers (`test` job 102372608026): healthy `dens=14 median=2015`, control `median=873`. Both places now name the CI run the numbers came from. Broken table gains the damage column F3 needs. Every floor confirmed still holding; **none moved**. | **7** |
| **F3** | `3238c3a5` | Honest relabelling, **no floor moved and no clause dropped**: the discriminating clauses (hard zero on the control) are named separately from the anti-degeneracy floors the control clears, and the median floor is stated to sit inside the control's own noise band. Raising `MinDamageDealt` above the control's 3333 would cross the healthy weak seat's 3608, so it was not raised. | **7** |
| **F5** | `ee134fb3` | `tools/ci/parity_tiers_bc16.py`'s **step-summary strings only**: column reads `tier A / A″`; the exit-condition line names which tiers this script runs (A, A″, C) versus the job's byte-diff step (B); a new line states Tier A′ **was not built and did not run**, that nothing in the table is evidence for it, and names the consequence (`more_archon_health` / `more_parts_net_worth` have no Java-side evidence). No comparator logic touched; `--selftest` exits 0. | none (advisory; removes a false CI claim) |
| **F6** | `f51f02cd` | No code change, per ruling. The anti-vacuity floor divergence from `design.md:2574` is recorded in `docs/PARITY.md` (+55). | none (advisory) |
| **F7** | `ef1e8bf5` | `years/bc16/rules.nim`: nineteen per-team values (was fifteen) and thirteen globals (was ten), **every census its own `mixHash` call**, so no count ≥100 can carry into the next field and mask a divergence in the tripwire. Year-neutral `match.nim:498-506` deliberately **not** touched (it would move every sibling year's committed chain); the limitation, the measured peaks and the condition a future year must check are recorded in `docs/PARITY.md` §bc16. `tests/fixtures/replay-bc16.json` re-recorded; **an assertion was added, none weakened** — `tests/test_bc16_replay.nim` now re-derives the committed fixture to its **last** round, closing the gap that `wasm_replay_smoke.cjs`'s 200-frame walk left over a 2871-round recording. | **2** (strengthened) |
| **F8** | `0e7b15e9` | `endReasonFor` raises a `Defect` naming state, round, `maxRounds` and `hasWinner` on `dfNone` instead of writing `more_archons`. `raise`, not `doAssert`, so it holds under `-d:danger`. Exported for testability; `tests/test_bc16_endladder.nim` gains the test. `ok (52 checks)` in debug, `-d:release`, `-d:danger`. | **7** (legal end reasons) |
| **F9** | `c549483f` | `renderHorde` draws `THE HORDE` as the strip's first field in every state, surviving the 360 px query; `hordeStrike()` activates `#bc16-horde.struck` on the last `wave`/`turned` beat in the playhead's step, carrying **that beat's own label** so strip, killfeed and scrubber say one sentence, and removing it after 2000 ms. `.struck` sets `white-space: normal` (the readouts' `nowrap` clipped a sentence inside an `overflow:hidden` box — measured at 360 px). | **4** (name spaces / third party), **15** |
| **F11** | `95ef6c90` | `recordAndDerive` now also returns `EpisodeReason`, and bc23's timed block asserts `episodeReason in [epDeadline, epComplete]` — bc22's shape — alongside the existing document-level check, plus a `checkEq` that the two agree. **Three assertions where there were two**; `ok (98 checks)`, was 95. | **1** (no test loosened — this is a strengthening) |
| **F10** | — | No change, by ruling: the deleted literal asserted `GameVersion == "GV10"`, i.e. that no bump may ever happen, made unsatisfiable by the authorised GV10→GV11 bump; the substantive `fixture == GameVersion` assertion survives and gained three checks. | **1** |

## Never-weakened audit (checklist item 1, second half) — coordinator-verified

Method: `git diff fbc7d345..46b92ae -- 'tests/*.nim'` read hunk by hunk, plus a targeted search
of every removed line for `check`/`doAssert`/`assert`/`skip`/`Skip`/`xfail`.

- `tests/` numstat: `test_bc16_endladder.nim +23/-0`, `test_bc16_replay.nim +26/-0`,
  `test_bc16_survival.nim +108/-27`, `test_bc23_replay.nim +19/-10`, `test_viewer.nim +123/-5`,
  `fixtures/replay-bc16.json ±1` (the F7 re-recording).
- **42 removed lines** in `tests/*.nim` against ~300 added. Of the 42, exactly four contain
  assertion-like text: two are `##` comment rows of the stale F4 measurement table; one is the
  `#endcard.show {` grep F1 replaced with a stricter whole-CSS check; one is a **reflow** of
  `check("a one-second budget on the largest map …")`, which is still present and now stronger
  (`tests/test_bc23_replay.nim:161-163`, verified by reading the file).
- **No test disabled, skipped, deleted, or given a widened tolerance.** No `skip`, `t.Skip`,
  `xfail` or `--skip` added anywhere in the range. Assertions added:
  9 in `test_viewer`, 5 in `test_bc16_replay`, 4 in `test_bc16_endladder`, 3 in
  `test_bc23_replay`, plus the renderer fixture's bc16 row and its endcard computed-style check.
- The only fixture bytes that moved are `replay-bc16.json` (F7's re-recording, with the
  re-derivation assertion **added**, not relaxed) — the GV11 fixture regeneration of
  `replay-bc22.json`/`replay-bc23.json` belongs to phase 20, not this round.

## Main CI

`ci.yml` run `34346628919` on `main` @ `46b92ae5`:

- 9 jobs green: `docker-smoke`, `parity-oracle`, and all eight per-year oracles
  (`parity-oracle-bc16/20/21/22/23/24/25`).
- `wasm-viewer` **failed at 11:43:43Z** in `Build the static replay viewer bundle`. Root cause is
  transient infrastructure, not this tree: `tar xf nim.tar.gz --strip-components=1` exited 2
  after nimby's own three internal retries — a truncated/corrupt Nim 2.2.4 toolchain download
  inside the docker build (`Error: unhandled exception: error running command 'tar xf
  nim.tar.gz' … [NimbyError]`). The **identical tree passed the identical job** on branch run
  `34338896940`.
- `test` completed **success** at 12:36Z (58 min), so attempt 1 ended `failure` with
  `wasm-viewer` as its only red job. The coordinator re-ran the failed job only
  (`gh run rerun 34346628919 --failed`, which keeps the run id), and **attempt 2 completed
  `success` at 12:43Z with all 11 jobs green** — `test`, `docker-smoke`, `wasm-viewer`,
  `parity-oracle` and the eight per-year oracles. The flake did not recur, which confirms the
  toolchain-download diagnosis over a code cause.
- **Phase-30 checklist item 1 therefore holds at the reviewed sha**: `ci.yml` conclusion
  `success` on `main` @ `46b92ae5ff9a78be61c659f4a2eff861aa17b838`, run `34346628919`, with no
  test disabled, skipped, or loosened during this run (audited above).
