# r1 review — bc16 (RECONSTRUCTION OF RECORD)

**Read this header before you read anything below it.**

This file is **not** the reviewer's own text. The round-1 reviewer
(`coworld-builder-reviewer`, thread `sthr_015P4A6sYbtHxf9ZHaME9itS`) wrote a 737-line
`r1-review.md` into the container of the session that dispatched it. That session died at
09:06Z, immediately after recording the review's findings and dispatching the fixer, and it
never committed the file to this repo. Container filesystems do not survive a session, so the
reviewer's prose is **permanently lost**: `git log --all -- runs/2026-09-09-battlecode-2016/reviews`
returns nothing, and the path did not exist in the mount when the 12:28Z session took the run.

What follows is reconstructed by the coordinator from three **primary, contemporaneous**
sources, and nothing else:

1. `runs/2026-09-09-battlecode-2016/log.md`, lines timestamped `2026-09-09T09:05:00Z`,
   `09:05:30Z` and `09:06:00Z` — the coordinator's own record, written while the reviewer's
   reply was in front of it, of the findings' identities, the reviewer's independently verified
   CI evidence, which checklist items it found satisfied, and all eleven rulings.
2. PR [#11](https://github.com/Metta-AI/cogame-battlecode/pull/11)'s disposition table and its
   ten commit messages, each of which restates the finding it fixes with `file:line` and quotes
   the offending code.
3. The landed diff itself, `fbc7d345..46b92ae` in `Metta-AI/cogame-battlecode`.

Consequences a reader (and the judge) must hold on to:

- The **finding identities, their file:line anchors and their dispositions are recoverable and
  are recorded faithfully below.** They are cross-checked against the diff, which is primary.
- The reviewer's **full reasoning for the seven advisory findings is not recoverable.** Where
  this file states a finding's substance, it is the substance the fixer's commit message and
  the diff attest to, not the reviewer's argument for it.
- This file is therefore **weak evidence for "the reviewer looked at X"** and **strong evidence
  for "X is what changed and why"**. The judge is told this in its brief and is instructed to
  treat its own independent checklist pass — not this file — as the authority for round 1.

The loss is a process defect and is logged as one (`log.md`, `12:33:00Z 30 resume finding B`).
Its cause is structural, not incidental: a sub-agent writing into the dispatching session's
container has produced no durable artifact until the coordinator commits it. The fix belongs in
`prompts/30-review-loop.md` (commit each round's artifact the moment the sub-agent returns,
before the next dispatch) and is filed as a SPEC/prompt suggestion on the run task rather than
edited into the prompt by this run.

## Reviewed tree

- repo `Metta-AI/cogame-battlecode`, `main` @ `fbc7d345e116dcb5e7c6fbae510144da09f11a8b`
- scope: the bc16 diff `00c1dae..fbc7d345`, 118 files, +20726/-84 (a **mod** run: bc16 is added
  beside the seven shipped year modules bc20–bc26, which are out of scope, as are two named
  carried-forward pre-existing sibling bugs)
- design note: `runs/2026-09-09-battlecode-2016/design.md` (2914 lines)
- CI: run `34322655506` (`ci.yml`, `main` @ `fbc7d345`), all 11 jobs green

## CI evidence the reviewer verified independently (log 09:05:00Z)

Recorded verbatim from the coordinator's contemporaneous note, because these are the
grep-not-trust checks the checklist demands rather than claims about job colour:

- run `34322655506`: conclusion `success`, 11/11 jobs.
- **zero** occurrences of `SEAT-COUNT FAIL` in the 268 KB `docker-smoke` log (checklist item 6).
- `Load the bundle in a real browser` **present and not `continue-on-error`**; `wasm-viewer`
  declares `needs: docker-smoke` (item 13).
- bc16 replay: `loaded: true`, endcard `shown: true`, `mismatch_round: -1` (items 2, 13).
- simultaneous decision confirmed as **one** `curly.makeRequests` batch,
  `src/battlecode/years/bc16/decide.nim:1295-1312` (the checklist's simultaneous-decision rule).

Items found **satisfied with cited evidence**: 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14.
Item 1 verified (F10 was the only `tests/` hunk in scope at that point).
Item 15 **falsified** by F2 — see below.

## Findings F1–F11, with the coordinator's rulings (log 09:06:00Z) and their outcomes

`disposition` is the ruling the coordinator issued at 09:06Z, which the fixer was dispatched to
execute as decided and non-re-litigable. `landed` is what the diff `fbc7d345..46b92ae` actually
contains, verified by the coordinator at 12:35Z.

### F2 — the one checklist-falsifying finding (item 15, legibility)

`tools/ci/renderer_fixture.html:70`'s `YEARS` array had **no `bc16` row**, so the only gate in
the repo that renders LLM-authored text at its cap never laid out anything bc16 draws — no
`data-year="bc16"`, no `#bc16-*` id, nothing measured. bc16 draws a 280-rune `notes`, a 48-rune
`motto` and a 120-rune submitted sheet into `#bc16-doctrines-body`. `canvas_text.total` is 0 on
all eight replays and the CI replay carries no LLM text at all, which is exactly the blind spot
the checklist's item-15 fixture clause exists for (cogchemists, 2026-08-24). `design.md:2832`
asked for the row.

- **disposition: FIX.** Add the bc16 row so the existing `--strict-text-bounds` step lays
  `#bc16-doctrines-body` out at full cap.
- **landed:** commit `2e429719` — `bc16` appended to `YEARS`; a bc16 row reproducing
  renderArchons / renderHorde / renderEcon / renderUnits / renderDoctrines element for element,
  both seats at the full 280-rune `notes` and 48-rune `motto`, `plainWords16()`'s widest
  eleven clauses (502 chars), every stat measured as the widest value reached on any round of a
  `bulwark` mirror over the six `small` maps at the 3000-round cap, and a `bc16` FILLED entry so
  the "hides its own content" rule runs over all five readouts. `ci.yml`'s existing
  `Render the full-cap doctrine-text fixture` step now lays bc16 out at 360/720/1280 px.
  **The row immediately found two real clipping defects**, both fixed in the same commit inside
  bc16's own additions block: `#bc16-horde` was one `nowrap` flex line ~570 px wide inside a
  `max-width: 92%; overflow: hidden` box, so at 360 px (331 px) and at 720 px its tail — `DENS`,
  the mini-timeline, the tiebreak countdown — was laid out past the frame and clipped to
  nothing; plus the second defect recorded in the commit body.

### F1 — a provably dead endcard-suppression rule (advisory, but it made two tests vacuous)

`client/replay_broadcast.html:3792-3799` shipped
`html[data-year="bc16"] #endcard.show ~ #bc16-archons, …{visibility:hidden}` and it was dead
**twice over**: the class the page toggles is `.on` (`#endcard.on{display:flex}` at :1878,
`classList.add('on')` at :6823, `remove('on')` at :6771) — nothing anywhere sets `.show`; and
`~` selects only **following** siblings while `#bc16-archons/-horde/-econ/-units/-doctrines`
(:3991-3999) are emitted **before** `#endcard` (:4057) inside `#chrome`. `#endcard`'s background
is a radial gradient at 0.82–0.95 alpha and this was the page's only `visibility:hidden`
declaration, so the five readouts sat visible behind a score screen that is not opaque. Both
tests covering it were text greps that stayed green.

- **disposition: FIX**, inside bc16's additions block only (parent-scoped `:has()` acceptable;
  `client/chrome_common.js` and the inherited chrome untouched) **AND** replace both text-grep
  tests with a computed-visibility check so a dead rule is red.
- **landed:** commit `3a693cd0` — rule is now
  `html[data-year="bc16"] #chrome:has(#endcard.on) #bc16-…`; `:has()` verified supported in the
  headless chromium the smoke runs (141.0.7390.37). `tests/test_viewer.nim:1425-1428` no longer
  asserts the dead string is present: it pins the parent-scoped shape, asserts **both** dead
  shapes are absent, and asserts all five boxes are named. `tests/test_viewer.nim:490-491`'s
  `"#endcard.show {" notin page` — which passed only because the dead rule's text was
  `#endcard.show ~ …`, not `#endcard.show {` — now reads the page's whole `<style>` block and
  refuses the substring in any selector shape. The real gate is a computed style in the renderer
  fixture, which raises `#endcard` and reads `visibility` on all five boxes.

### F3 — three survival floors sit below what the broken control clears (advisory)

`MinUnitsBuilt` 25, `MinDamageDealt` 1500 and `MinMedianRounds` 1000 are below what
`-d:bc16BrokenChassis` already achieves, while the test header and `docs/RULES-BC16.md`
§Divergences item 16 read as though every substance clause discriminated.

- **disposition: FIX BY HONEST RELABELLING; floors NOT fitted to the control.** Raising
  `MinDamageDealt` above the broken 3333 would cross the healthy weak seat's 3608 — noise-fitting
  that would redden healthy runs. Name which clauses carry the discrimination and which are pure
  anti-degeneracy floors the control also clears.
- **landed:** commit `3238c3a5` — no floor moved, no clause dropped. Both places now carry the
  same table: **discriminating** (a hard zero on the control) = the 2-of-6 ratio, guards built
  per seat per game, dens killed across the six maps, `swamp`'s parts-collected pair clause;
  **anti-degeneracy only, control clears them** = units built (25 vs 55), damage dealt
  (1500 vs 3333), parts income (1 tenth vs 10 621); and the median floor is stated to sit
  **inside the control's own noise band** (1029 last session, above the floor; 873 on the shipped
  build, below it), so it is counted with the anti-degeneracy floors even though it fires today.

### F4 — both measurement tables were stale (advisory)

The inline tables claimed healthy `3 of 6 … 20 dens; median 2147` and a broken median of 1029,
while run `34322655506` (`test` job 102372608026) measured
`HEALTHY games=6 notDestroyed=3 dens=14 median=2015 rounds=@[3000,695,3000,707,3000,1030]` and
`median=873` for the control.

- **disposition: FIX** both tables from run 34322655506's own numbers and cite the run id in
  both places.
- **landed:** commit `c70572002b` — both tables regenerated from the shipped build; both places
  name the CI run the numbers came from, so future staleness is detectable; the broken table
  gains the damage column F3 needs. Every committed floor confirmed still holding on the
  regenerated numbers (`MinNotDestroyed` 2≤3, `MinUnitsBuilt` 25≤58, `MinDamageDealt` 1500≤3608,
  `MinGuardsBuilt` 2≤5, `MinDensKilled` 4≤14, `MinMedianRounds` 1000≤2015, parts income
  1≤11724 tenths, `swamp`'s pair clause 1≤1200 tenths). No floor moved.

### F5 — the CI step summary named a parity tier that never ran (advisory)

Tier A′ (the four scenario bots) was not built — `tools/oracle/bc16/` holds only `bc16greenhorn`
and `bc16idle` — and the gap is honestly disclosed in `docs/PARITY.md:1844-1885`. But
`tools/ci/parity_tiers_bc16.py` headed its summary column `tier A/A'` and printed "the phase-30
exit condition is Tiers A, A' and B passing with an EMPTY ledger" into the **CI step summary**,
under a table of eighteen bit-exact pairs. A reader of the summary alone would conclude Tier A′
ran and passed.

- **disposition: FIX the claim only.** Tier A′ stays unbuilt and disclosed; the summary must not
  say it passed.
- **landed:** commit `ee134fb3` — column reads `tier A / A″`; the exit-condition line names A,
  A″, B, C and says which the script runs (A, A″, C) versus which is the job's own byte-diff step
  (B); a new line states outright that **Tier A′ was NOT BUILT and did NOT run**, that nothing in
  the table is evidence for it, and points at `docs/PARITY.md` §bc16 with the exact consequence —
  `more_archon_health` and `more_parts_net_worth` have no Java-side evidence. No comparator logic
  touched; `--selftest` exits 0.

### F6 — parity floor substitution diverges from the design note (advisory)

- **disposition: NO CODE CHANGE.** The substituted floors are sound and already reasoned in
  `ci.yml:3013-3023` (neither oracle bot survives to round 3000; measured 298–683 rounds).
  Record the divergence from `design.md:2574` in `docs/PARITY.md`.
- **landed:** commit `f51f02cd` — recorded in `docs/PARITY.md` (+55 lines).

### F7 — hash-chain censuses folded, so two distinct censuses could collide (advisory)

`src/battlecode/years/bc16/rules.nim:395-400` folded six player-type censuses base-100/base-10⁶
into two `mixHash` calls and `:418-421` folded four zombie censuses base-100 into one. Any single
count ≥100 carried into the next field. Not hypothetical on this year: the parity job measures
`peak_robots` 104–162 and the survival gate builds 177–212 units a seat on `checkers`/`prisons`.
The chain is a **tripwire** — a collision can only hide a divergence, never manufacture one —
which is why a blind spot in it had to go.

- **disposition: PARTIAL.** Widen bc16's **own** packing in `years/bc16/rules.nim` (its fixtures
  are this run's own) but do **not** touch the year-neutral `match.nim:498-506` packing, which
  would move every sibling year's committed chain.
- **landed:** commit `ef1e8bf5` — nineteen per-team values (was fifteen) and thirteen globals
  (was ten), every census its own call; header counts corrected. `match.nim:498-506` deliberately
  untouched, with the limitation, the measured peaks and the condition a future year must check
  recorded in `docs/PARITY.md` §bc16. `tests/fixtures/replay-bc16.json` re-recorded;
  **no assertion weakened to make the new recording pass** — one was **added** in
  `tests/test_bc16_replay.nim` that re-derives the committed fixture to its **last** round,
  because `tools/wasm_replay_smoke.cjs` steps 200 frames and its `mismatch_round: -1` therefore
  covered only the first 200 rounds of a 2871-round recording.

### F8 — `dfNone` was reported as `more_archons` (advisory)

`src/battlecode/years/bc16/rules.nim:431-434` mapped `dfNone` — "no winner at all" — to
`$dfPwned`, writing `more_archons` into the shipped `end_reason`. Unreachable in the shipped
configuration (`checkEndOfMatch` always sets a winner; the abandoned path returns earlier; the
only way in is `maxRounds <= 0`, which `config_schema.maxRounds.minimum = 50` forbids) — but an
impossible state that reports a **plausible** answer is the wrong failure mode.

- **disposition: FIX** — make the unreachable state fault loudly instead of mislabelling.
- **landed:** commit `0e7b15e9` — raises a `Defect` naming the state, the round, `maxRounds` and
  `hasWinner`; `raise`, not `doAssert`, so it holds under `-d:danger`. `endReasonFor` exported so
  the behaviour is testable; `tests/test_bc16_endladder.nim` gains the test (a fresh world's
  domination factor **is** `dfNone`, the proc refuses to name a reason for it, and a decided game
  still round-trips its rung). Verified `ok (52 checks)` in debug, `-d:release` and `-d:danger`.

### F9 — THE HORDE was never drawn, and `.struck` was a rule nothing activated (advisory)

Ruling 4 of phase 10 made "THE HORDE" this year's flavour carrier and `design.md:319-320` says
the zombie team is drawn and labelled THE HORDE spectator-side. The words appeared only in a CSS
comment (`:3702`) and in the agent-facing observation (`decide.nim:639`, `:1163`); `renderHorde`
drew glyph counts, `WAVE`, `OUTBREAK`, `DENS`, `ROUND` and no faction name. Separately
`#bc16-horde.struck` (`:3724`) was a rule nothing ever set, against `design.md:1772-1776`.

- **disposition: FIX** both halves — draw the label, wire the dead `.struck` takeover.
- **landed:** commit `c549483f` — `renderHorde` draws `<span class="horde">THE HORDE</span>` as
  the strip's first field in every state, with its own rule, surviving the 360 px media query.
  `hordeStrike()` reads the beats that landed between the frame the playhead came from and the
  one it is on, takes the last `wave`/`turned` beat, puts **that beat's own label** on the strip
  (so strip, killfeed and scrubber button say the same sentence and there is no second string to
  keep in step), adds `struck`, removes it after 2000 ms. `.struck` also sets
  `white-space: normal`, because the readouts' `nowrap` applied to a **sentence** inside an
  `overflow:hidden` box clipped it — measured at 360 px.

### F10 — filed neutrally with both readings; bears on item 1 (no test loosened)

The bc16 diff deleted a literal in `tests/` that asserted `GameVersion == "GV10"`.

- **disposition: NO CHANGE — RULED not a loosening.** The deleted literal asserted that no
  version bump may ever happen, which the **authorised** GV10→GV11 bump makes unsatisfiable by
  construction; the substantive `fixture == GameVersion` assertion survives and gained three
  checks. (The reviewer filed it neutrally with both readings, which is what its prompt asks for.)
- **landed:** no code change, by ruling.

### F11 — the authorised bc23 tolerant end-reason edit had not been applied (advisory)

- **disposition: FIX** — apply the authorised-but-unapplied edit.
- **landed:** commit `95ef6c90` — the tolerance already existed at the **string** level
  (`stopped in ["deadline","complete"]`); what was missing is the shape ruling 7 named, the
  **enum-level** assertion on the value `playMatch` actually returned, which `discard reason` was
  throwing away because `recordAndDerive` returned only the game's end reason, not the episode's.
  `recordAndDerive` now returns `EpisodeReason` too; the timed block asserts
  `episodeReason in [epDeadline, epComplete]` (bc22's exact shape,
  `tests/test_bc22_replay.nim:270`) alongside the document-level check, plus a new `checkEq` that
  the two agree. **Three assertions where there were two.** `ok (98 checks)`, was 95.

## Coordinator determination made during the round, not a finding

`SMOKE_SEATS=2` in `tools/ci/docker_smoke.sh:25,:82` **is** the `<SEATS>` substitution — proved
from `templates/tools/ci/docker_smoke.sh:25,:54`, which carry `<SEATS>` at exactly those
positions (log `09:05:30Z`). This settles the item-6 second-declaration question the review left
undetermined.
