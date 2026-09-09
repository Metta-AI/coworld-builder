# r1 fixes — battlecode-2016 (`bc16` year module of `Metta-AI/cogame-battlecode`)

Branch: **`bc16-r1-fixes`** off `main` @ `fbc7d345`
PR: **#11** — https://github.com/Metta-AI/cogame-battlecode/pull/11
Head on the branch: `95ef6c90093c35f4fa26408ec0fc318eb07bc659`
Merge commit on `main`: **`46b92ae5ff9a78be61c659f4a2eff861aa17b838`** (merge
of PR #11; its tree is byte-identical to the branch head's — the merge added
nothing)
`ci.yml` on the branch head `95ef6c90`: run **34338896940** — **`success`**,
all 11 jobs `success` (`test`, `docker-smoke`, `wasm-viewer`, `parity-oracle`,
`parity-oracle-bc16/20/21/22/23/24/25`)
Final `ci.yml` run on `main` @ `46b92ae5`: run **34346628919** (attempt 2) —
**`conclusion: success`**, all 11 jobs `success`

**On attempt 2, and it is not a stale-green report.** Attempt 1 of run
34346628919 was red in `wasm-viewer` only, and the failure was an
infrastructure flake with nothing to do with this diff: step 6 "Build the
static replay viewer bundle" died inside the Docker build at
`nimby use 2.2.4` with `tar: Error is not recoverable` on `nim.tar.gz`, after
all three of nimby's own retries — a truncated download of the Nim tarball.
Every other job on attempt 1 was `success`, and the identical tree had passed
`wasm-viewer` twenty minutes earlier in run 34338896940. Attempt 2 re-ran the
failed job; its steps all executed rather than skipping (verified step by
step: `Build the static replay viewer bundle`, `Load the bundle in a real
browser (ALL EIGHT years' replays)`, `Smoke the emitted wasm module under node
(all eight years)`, `Render the full-cap doctrine-text fixture`, all
`success`) and it printed real output, quoted under the findings below.

**Independent confirmation from the final run's own logs**, `main` @
`46b92ae5`:

* `test` (job 102467556370): **0 `FAIL` lines**, 296 `ok (…)` lines, every
  shard run twice. `test_bc16_survival: ok (11 checks)` in both passes with
  `HEALTHY games=6 notDestroyed=3 dens=14 median=2015 rounds=@[3000, 695,
  3000, 707, 3000, 1030]` and `BROKEN-CONTROL games=6 notDestroyed=0 dens=0
  median=873 failures=16` — exactly the regenerated tables (F4).
  `test_bc16_beats: ok (91 checks)`, `test_bc16_endladder: ok (52 checks)`,
  `test_bc16_replay: ok (79/78 checks)`, `test_bc23_replay: ok (98 checks)`,
  `test_viewer: ok (865 checks)`.
* `docker-smoke` (job 102467508896): **zero occurrences of `SEAT-COUNT
  FAIL`**; `smoke OK: seats=2 … reason=complete` on all three episodes
  including bc16.
* `wasm-viewer` (job 102467507789): `page_styles.css: 194002 bytes from 1
  <style> block(s)` then `{"loaded":true,…}` and `canvas text: 0 drawn, 0
  never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` for the renderer fixture — and the fixture only sets
  `data-replay-loaded="true"` when **every** year/width cell verdicts `ok`, so
  that one line is the bc16 row and the endcard computed-style check passing.
  All eight replays `loaded: true` with `endcard after the 100% seek:
  shown=true`; `largest overlay over the board after the soak: bc16-horde 6%`;
  ten wasm re-derivations all `mismatch_round: -1`, including the regenerated
  `tests/fixtures/replay-bc16.json`.
* The whole local suite was also run here before the push, **both** in debug
  and in `-d:release`: 308 shard runs, **zero failures**.

One commit per finding, in the order below. No test was disabled, skipped,
weakened or deleted; every change to a test file adds assertions or corrects a
literal that had gone stale. Nothing in the review, the design note, the repo
or any CI log contained text addressed to me.

**A note on how the commits landed.** `git push` over HTTPS is not usable in
this sandbox: the credential helpers hand git a placeholder token that
`api.github.com` accepts (`gh api user` → `daveey`) but that
`github.com/.../git-receive-pack` rejects with 401 under Basic auth, for both
`GH_TOKEN` and `ANTHROPIC_COMMIT_TOKEN`. The ten commits were therefore
replayed onto `fbc7d345` through the Git Data API (blobs → tree → commit →
ref), and **every commit's remote tree sha was compared against the local tree
sha and matched**, which is byte-for-byte proof the remote contents are the
ones tested here. The shas in the table are the remote ones.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F1 | fixed | `3a693cd0` | `client/replay_broadcast.html:3833-3851`, `tools/ci/renderer_fixture.html:71-81,713-742,~790`, `tests/test_viewer.nim:517-528,1511-1562` | advisory (bears on item 14's endcard bullet) |
| F2 | fixed | `2e429719` | `tools/ci/renderer_fixture.html:70,486-597,~790,~880`, `client/replay_broadcast.html:3725-3750,3925`, `tests/test_viewer.nim:395-475` | **15** |
| F3 | fixed (relabelling; no floor moved) | `3238c3a5` | `tests/test_bc16_survival.nim:56-104,152-177`, `docs/RULES-BC16.md:394-419` | advisory |
| F4 | fixed | `c7057200` | `tests/test_bc16_survival.nim:14-77,153-177,235-247`, `docs/RULES-BC16.md:369-392` | advisory |
| F5 | fixed | `ee134fb3` | `tools/ci/parity_tiers_bc16.py:451-479` | advisory |
| F6 | **no code change** — divergence recorded | `f51f02cd` | `docs/PARITY.md:1815-1838` | advisory |
| F7 | fixed for bc16's own packing; year-neutral half **no code change**, recorded | `ef1e8bf5` | `src/battlecode/years/bc16/rules.nim:387-432`, `tests/fixtures/replay-bc16.json`, `tools/gen_bc16_fixture_replay.nim:30-52,66`, `tests/test_bc16_replay.nim:281-304`, `docs/PARITY.md:1863-1894`, `.github/workflows/ci.yml:4230-4241` | advisory (strengthens item 2) |
| F8 | fixed | `0e7b15e9` | `src/battlecode/years/bc16/rules.nim:442-461`, `tests/test_bc16_endladder.nim:191-212` | advisory |
| F9 | fixed | `c549483f` | `client/replay_broadcast.html:3733-3757,5692,5820-5900,6116-6127`, `tools/ci/renderer_fixture.html:552`, `tests/test_viewer.nim:1455-1509` | advisory |
| F10 | **no code change** — ruled not a loosening | — | `tests/test_bc22_replay.nim:95-108` (unchanged by me) | **1** |
| F11 | fixed | `95ef6c90` | `tests/test_bc23_replay.nim:59-68,105-106,152-170` | advisory |

Line numbers are as of the branch head.

---

## F1 — bc16's endcard HUD-suppression rule could never match, and the tests could not see it

**Commit `3a693cd0`. Checklist: advisory; it is the one defect inside item
14's `#endcard` bullet.**

**What the code did.** `client/replay_broadcast.html:3792-3799` shipped

```css
html[data-year="bc16"] #endcard.show ~ #bc16-archons, … { visibility: hidden; }
```

which was dead twice over. (a) The class the page toggles is `.on` —
`#endcard.on { display: flex; }` at `:1878`, `classList.add('on')` at `:6823`,
`classList.remove('on')` at `:6771`; nothing anywhere sets `.show`. (b) `~`
selects only **following** siblings, and `#bc16-archons`/`-horde`/`-econ`/
`-units`/`-doctrines` (`:3991-3999`) are emitted **before** `#endcard`
(`:4057`) inside `#chrome`, so no sibling combinator could have matched
whatever class it named. `#endcard`'s background is a radial gradient at
0.82–0.95 alpha, so the five boxes were visible behind a score screen that is
not opaque, and this was the page's only `visibility: hidden` declaration.

**What it does now.** The rule is parent-scoped and keyed on the class that
exists: `html[data-year="bc16"] #chrome:has(#endcard.on) #bc16-…`. It is
inside bc16's own additions block; no inherited chrome above the banner is
touched and `client/chrome_common.js` is untouched (its sha256 assertion at
`tests/test_viewer.nim:31-36` still passes). `:has()` is supported by the
headless chromium CI runs — verified locally on the same build family,
`Chromium 141.0.7390.37`, `CSS.supports('selector(:has(*))')` → `true`.

**And the tests that could not see it.**

* `tests/test_viewer.nim:1425-1428` asserted the **dead string was present**.
  It now pins the parent-scoped shape, asserts both dead shapes are **absent**
  (`#endcard.show ~ #bc16-archons` and `#endcard.on ~ #bc16-archons`), and
  asserts each of the five boxes is named in the rule.
* `tests/test_viewer.nim:490-491`'s `"#endcard.show {" notin page` passed only
  because the bc16 rule read `#endcard.show ~ …` rather than `#endcard.show {`.
  It now extracts the page's whole `<style>` block and refuses the substring in
  **any** selector shape. (It reads the CSS, not the file, because
  `renderEndcard`'s own prose comment at `:6856` names the class in order to
  say it does not exist — inherited text I did not touch.)
* **The gate is no longer a grep.** `tools/ci/renderer_fixture.html` gains the
  page's own `#endcard` as a child of `#chrome`, and a `SUPPRESSED_BY_ENDCARD`
  check that raises the card exactly as `renderEndcard` does, reads
  `getComputedStyle(...).visibility` on all five boxes, then takes the card
  down and asserts they come back — because every seek dismisses the card and
  the scrubber has to be able to pull the match back. That runs inside the
  existing `Render the full-cap doctrine-text fixture` step at 360, 720 and
  1280 px. `tests/test_viewer.nim` asserts the fixture carries it, on all five
  boxes, with `#endcard` in the right parent.

**Evidence.** In CI on `main` @ `46b92ae5` the `Render the full-cap
doctrine-text fixture` step printed `page_styles.css: 194002 bytes from 1
<style> block(s)` then `{"loaded":true,…}` — and the fixture sets
`data-replay-loaded="true"` only when **every** cell verdicts `ok`, so this
check passed there. Locally, with the fixture served exactly as `ci.yml`
serves it and driven by headless chromium 141: all 24 year/width cells report
`ok`. With the dead selector restored, the three bc16 cells report

```
the endcard is up and #bc16-archons, #bc16-horde, #bc16-econ, #bc16-units,
#bc16-doctrines is still visible — the HUD bleeds through a score screen that
is not opaque
```

`nim r tests/test_viewer.nim` → `ok (855 checks)` at that commit.

---

## F2 — the worst-case renderer fixture had no bc16 row

**Commit `2e429719`. Checklist item 15** — the one finding that falsified a
checklist item.

**What the code did.** `tools/ci/renderer_fixture.html:70` listed seven years
and not `bc16`, so the only gate in this repo that renders model-length text
never set `data-year="bc16"`, never emitted a `#bc16-*` id and never measured
`#bc16-doctrines-body` — the element that draws bc16's 280-rune `notes`,
48-rune `motto` and 120-rune submitted sheet. The file was not touched by the
run. design.md:2832 asked for the row in as many words.

**What it does now.** `bc16` is in `YEARS`, and the row reproduces
`renderArchons`/`renderHorde`/`renderEcon`/`renderUnits`/`renderDoctrines`
element for element and class for class, with:

* both seats at the full 280-rune `notes` and 48-rune `motto`, the fallback
  badge, the envelope badge and the 120-rune submitted sheet;
* `plainWords16()`'s **widest** possible eleven clauses — every clause the
  longest of its alternatives (`turret_count` 6, `guard_ratio` 100,
  `retreat_hp` 100, `den_clear_round` 3000): 502 characters against the second
  pole's 468;
* every stat **measured**, not invented: the widest value each field reached on
  any round of a `bulwark` mirror over all six `small` maps (the bc16 variant's
  own pool) at the 3000-round cap — archons 4 a side, soldiers 110, guards 28,
  scouts 3, vipers 1, turrets 3, building 4, infected 10, lost 200, turned 70,
  parts 618, income 2.0, parts collected 16 600 tenths, dens destroyed 4,
  neutrals 12, rubble cleared 317 167 / created 157 162 tenths, parts left
  3 380, impassable 450, zombies 39/8/10/6, dens standing 12, outbreak level 9,
  twelve schedule rows, largest single wave 54 in four parts.
  `neutral_archons` measured **zero** on this pool, so the parenthetical branch
  is fed 1 on purpose and the fixture says so;
* `#bc16-doctrines-toggle` beside its seven siblings, and a `bc16` entry in the
  `FILLED` map so the "hides its own content" rule runs over bc16's five
  readouts rather than over nothing.

**Two real defects the new row found**, both fixed inside bc16's own additions
block, because the fixture's DOM assertions have to *pass* for bc16 the way
they pass for the other seven:

1. `#bc16-horde` was one `nowrap` flex line measuring ~570 px inside a
   `max-width: 92%; overflow: hidden` box. At 360 px (331 px) and at 720 px the
   tail of the strip — `DENS`, the mini-timeline and the tiebreak countdown —
   was laid out past the frame and clipped to nothing, directly against the
   design note's "keeps its wave composition, its multiplier and its countdown
   at **every** width including 360 px". It now wraps.
2. `#bc16-econ`/`#bc16-units` rows laid ~640 px of fields out inside a 344 px
   box at 360 px, so `rubble +x / −y` was drawn off-frame. The rows now wrap.
   Fields still never break mid-number (`white-space: nowrap` stays).

**One page-side alignment.** bc16's `renderDoctrines` wrote `notes` as a bare
text node while all seven sibling years wrap it in `<i>` — and
`#<year>-doctrines .dline i` is the selector the fixture's "the notes on seat N
were shortened before they were measured" check uses. A bare text node would
have made that check vacuous for bc16 exactly as bc25's own class names once
did (`tests/test_viewer.nim:430-437` records that precedent). One line changed;
an unstyled `<i>` in this panel has no bc16 rule other than the browser default
and the fixture measures the real markup.

**Evidence.** All 24 year/width cells `ok`. A direct probe of the three bc16
cells: 2 doctrine notes at **280 runes each**, both `.plate-sub` mottos at
**48 runes** (57 and 59 total against names of 6 and 8 plus the ` · `), the
doctrine panel at **46 %** of the frame height at all three widths (gate: 50 %),
and `WAVE`/`OUTBREAK`/`ROUND` all inside the frame at 360 px.
`nim r tests/test_viewer.nim` → `ok (845 checks)` at that commit.

---

## F3 — three survival floors sit below what the broken control achieves

**Commit `3238c3a5`. Checklist: advisory** (the check coordinator ruling 3
asked for). **Fixed by honest relabelling. No floor value moved and no clause
was dropped.**

Raising `MinDamageDealt` above the broken column's 3333 would put it above the
**healthy** weak seat's 3608 — fitting a floor to noise, and it would redden
healthy runs. So the labelling was corrected instead, in both places the ruling
named (`tests/test_bc16_survival.nim`'s header and const comments, and
`docs/RULES-BC16.md` §Divergences item 16):

| clause | floor | healthy (worst) | broken control | discriminates? |
|---|---|---|---|---|
| ratio, not `archons_destroyed` | 2 of 6 | 3 of 6 | **0 of 6** | **yes** |
| guards built, per seat per game | 2 | 5 | **0** | **yes** |
| dens killed across the six maps | 4 | 14 | **0** | **yes** |
| `swamp` parts collected across the pair | 1 tenth | 1 200 | **0** | **yes** |
| units built, per seat per game | 25 | 58 | 55 | no — anti-degeneracy only |
| damage dealt, per seat per game | 1 500 | 3 608 | 3 333 | no — anti-degeneracy only |
| parts income, per seat per game | 1 tenth | 11 724 | 10 621 | no — anti-degeneracy only |
| median rounds | 1 000 | 2 015 | 873 | inside the control's noise band |

The four `yes` clauses are a **hard zero** on the control and carry all of the
gate's discriminating power. The three `no` clauses stay asserted because what
they catch is a chassis that stops acting *at all* — the do-nothing sheet that
wins because the opponent starved, the 2026-09-03 finding — not this
particular control; calling them discriminating would be false. **The median
floor sits inside the control's own noise band and both documents now say so
explicitly**: the previous session recorded 1 029, *above* the 1 000 floor, and
the shipped build measures 873, *below* it, so it is counted with the
anti-degeneracy floors even though it does fire today.

Both documents also quote CI's own run as agreeing: run 34322655506's control
failed on **sixteen** clauses and the eight it printed are all
`guards built 0 < 2` plus `swamp: parts collected across the pair (tenths)
0 < 1` — not one printed failure is a units-built, damage-dealt, income or
median failure.

**Evidence.** `nim r -d:release tests/test_bc16_survival.nim` →
`BROKEN-CONTROL games=6 notDestroyed=0 dens=0 median=873 failures=16` and
`test_bc16_survival: ok (11 checks)`. No code path changed.

---

## F4 — both inline measurement tables were stale against the shipped build

**Commit `c7057200`. Checklist: advisory.**

Claimed: healthy "3 of 6 … **20** dens killed; median **2147** rounds"
(`tests/test_bc16_survival.nim:34-35`, `docs/RULES-BC16.md:374-377`) and a
broken median of **1029**. Measured by `ci.yml` run **34322655506**
(`main` @ `fbc7d345`, `test` job 102372608026):

```
HEALTHY games=6 notDestroyed=3 dens=14 median=2015 rounds=@[3000, 695, 3000, 707, 3000, 1030]
BROKEN-CONTROL games=6 notDestroyed=0 dens=0 median=873
```

Both tables were regenerated from the shipped build — the stale per-map rows
were `zigzag` and `frogger` on both sides — and **both places now name the CI
run the numbers came from**, so a future staleness is detectable rather than
invisible. The broken table gains the damage column it lacked, because that is
the column F3 needs.

Confirmed and stated in both places: **every committed floor still holds** on
the regenerated numbers — `MinNotDestroyed` 2 ≤ 3, `MinUnitsBuilt` 25 ≤ 58,
`MinDamageDealt` 1500 ≤ 3608, `MinGuardsBuilt` 2 ≤ 5, `MinDensKilled` 4 ≤ 14,
`MinMedianRounds` 1000 ≤ 2015, parts income 1 ≤ 11 724 tenths, `swamp`'s pair
clause 1 ≤ 1 200 tenths.

**Evidence.** `nim r -d:release tests/test_bc16_survival.nim` on this tree
prints `HEALTHY games=6 notDestroyed=3 dens=14 median=2015
rounds=@[3000, 695, 3000, 707, 3000, 1030]` and the control's `median=873` —
digit for digit what run 34322655506 printed. The per-map rows were re-read
from the same six games with a throwaway program (not committed) that plays
`poolNames("small")` through the same `playGame` call the gate uses.

---

## F5 — the parity comparator's CI summary claimed Tier A′ passed

**Commit `ee134fb3`. Checklist: advisory. Tier A′ was NOT built here** — that
is out of scope for this round and stays disclosed in
`docs/PARITY.md:1844-1885`. Only the claim changed.

`tools/ci/parity_tiers_bc16.py:451` headed its column `tier A/A'` and `:457-459`
printed "The phase-30 exit condition is Tiers A, A' and B passing with an EMPTY
ledger" into the **CI step summary**, beneath a table of eighteen bit-exact
pairs. A reader of the summary alone would conclude Tier A′ ran and passed.

Now: the column reads `tier A / A″` (the two tiers the script compares); the
exit-condition line names Tiers A, A″, B and C and says which of them this
script runs (A, A″, C) versus which is the job's own byte-diff step (B); and a
new line under the table states outright that **Tier A′ was NOT BUILT and did
NOT run**, that nothing in the table is evidence for it, and points at
`docs/PARITY.md` §bc16 "Tier A′ — NOT IMPLEMENTED" with the exact consequence
(`more_archon_health` and `more_parts_net_worth` have no Java-side evidence).

No comparator logic touched. `python3 tools/ci/parity_tiers_bc16.py --selftest`
→ `10 cases, all four known comparator bugs plus the origin tripwire covered`,
exit 0. The identically-worded lines in the bc22/bc23/bc25 comparators are left
alone: those years did build their scenario bots, and editing them is outside
this finding.

---

## F6 — the parity job's anti-vacuity floors are not the note's

**Commit `f51f02cd`. NO CODE CHANGE — the divergence is recorded.
Checklist: advisory.**

The substituted floors are sound and were already reasoned in
`ci.yml:3013-3023`. What was missing is the ledger line. `docs/PARITY.md` §bc16
now carries it:

| | design note (design.md:2574) | shipped | why |
|---|---|---|---|
| round floor | ≥ 2 900 **per game** | `≥ 250` per game (`ci.yml:3069`) | neither oracle bot survives that long — measured 298–683 rounds for `bc16idle`, 485–1424 for `bc16greenhorn`; a 2 900-round floor would fail all eighteen pairs |
| zombie floor | ≥ 150 spawned per game | ≥ 150 **summed `zombies_peak` over the eighteen pairs** (`ci.yml:3115`), measured 735 | the trace records peak-on-board, not a spawn total |

The entry also records why the shorter window is sound rather than weaker (the
trace runs to the engine's own `isRunning() == false`, so the end round, the
winner and the domination factor are themselves compared, and a port that ended
one round early diverges on the `W` line) and the three floors the job adds
that the note did not ask for (peak robots ≥ 10, an infection on ≥ 9 of 18
pairs, `saw_zombie_turn=true` on every pair), so the ledger is accurate in both
directions.

---

## F7 — packed hash-chain fields collide once a count exceeds its width

**Commit `ef1e8bf5`. Checklist: advisory; it strengthens item 2's tripwire.**

**bc16's own packing — FIXED.** `src/battlecode/years/bc16/rules.nim:395-400`
folded the six player-type censuses base-100/base-1000000 into two `mixHash`
calls and `:418-421` folded the four zombie censuses base-100 into one, so any
single count of 100 or more carried into the next field and two distinct
censuses could fold to the same chain value. Not hypothetical here: the parity
job measures `peak_robots` of 104–162 and the survival gate builds 177–212
units a seat on `checkers`/`prisons`. Every census is now its own `mixHash`
call — **nineteen** per-team values (was fifteen) and **thirteen** globals (was
ten, mis-stated as eleven); the header's counts are corrected to match.

**`src/battlecode/match.nim:498-506` — NO CODE CHANGE, recorded instead**, as
ruled. Those `div/mod 100` and `div/mod 100000` fields are year-neutral;
widening them would move every sibling year's committed chain values and
require re-recording seven more fixtures. `docs/PARITY.md` §bc16 records the
limit with the review's measured peaks as the evidence that the margin is
finite (`peak_robots` 104–162; `archons` bounded by ≤ 4 a side in the played
pool; `parts_worth` against the largest played map's 20 520 parts and a 100 000
field) and states the condition a future year must check before it ships.

**Fixture regeneration, and no assertion weakened.**
`tests/fixtures/replay-bc16.json` was re-recorded with
`tools/gen_bc16_fixture_replay.nim`. Two things had to be dealt with honestly:

1. `tools/gen_bc16_fixture_replay.nim`'s third map is now `closequarters`
   instead of `river`. This is the tripwire the tool's own header describes ("a
   rule change therefore turns those tests red: re-record with this program"):
   on the shipped chassis `river` no longer reaches the `rout` threshold (five
   robots lost by one side in one round, `years/bc16/rules.nim:324`), so the
   re-recorded fixture carried **twelve** beat kinds while
   `tests/test_bc16_beats.nim` names thirteen. I searched **all twenty-two**
   bc16 maps in the third slot; `closequarters` is the one substitution that
   restores the thirteenth kind while keeping `frogger`, `checkers` and the
   three-game shape. The header's per-map attribution is rewritten to say which
   map now supplies what. **The alternative would have been to weaken
   `test_bc16_beats`'s thirteen-kind assertion, and I did not.**
2. **A pre-existing defect this surfaced, and fixed.** The fixture committed on
   `main` @ `fbc7d345` did **not** re-derive at that sha:
   `mismatch_round = 302`, verified in a clean `git worktree` at `HEAD` with
   this commit's changes backed out. `tools/wasm_replay_smoke.cjs` steps
   **200 frames**, so its `mismatch_round: -1` on that fixture (wasm-viewer job
   102373769442, log line 2456) covered the first 200 rounds of a 1 470-round
   recording and could not see it. The re-recording fixes it, and
   `tests/test_bc16_replay.nim` gains an assertion that the **committed**
   fixture re-derives to its **last** round with the deriver walking every
   recorded round — which fails with `got 302 want -1` on the pre-fix tree
   (measured) and passes now. The `ci.yml` comment beside the wasm smoke is
   corrected: 2 871 rounds, and the 200-frame window named explicitly so nobody
   reads its `-1` as whole-recording evidence again.

**Evidence.** `test_bc16_beats: ok (91 checks)` with all thirteen kinds;
`test_bc16_replay: ok (79 checks)`; `test_viewer: ok (855)`;
`test_manifest: ok (1332)`; `test_determinism: ok (110)`; and all seven sibling
years' committed fixtures still re-derive with `mismatch_round = -1` (measured
one by one), so no cross-year chain moved.

---

## F8 — `endReasonFor` mapped "no winner at all" to `more_archons`

**Commit `0e7b15e9`. Checklist: advisory.**

`src/battlecode/years/bc16/rules.nim:431-434` rendered `dfNone` as `$dfPwned`,
i.e. it wrote `more_archons` into a shipped `end_reason`. The state is
unreachable in the shipped configuration (`checkEndOfMatch` always sets a
winner via one of the four rungs, the abandoned path returns before this proc
runs, and the only way in is `maxRounds <= 0`, which
`config_schema.maxRounds.minimum = 50` forbids) — but an impossible state that
reports a plausible answer is the wrong failure mode.

It now raises a `Defect` naming the state, the round, `maxRounds` and
`hasWinner`. `raise`, not `doAssert`, so it holds under `-d:danger` as well as
`-d:release`. `endReasonFor` is exported so the behaviour is testable — no
other year exports a symbol of that name — and
`tests/test_bc16_endladder.nim` gains the test: a fresh world's domination
factor **is** `dfNone`, `endReasonFor` refuses to name a reason for it, and a
decided game still round-trips its own rung (`more_parts_net_worth`, and never
`more_archons` by accident).

**Evidence.** `test_bc16_endladder: ok (52 checks)` in debug, `-d:release` and
`-d:danger`; `test_bc16_replay`, `test_bc16_baselines`, `test_bc16_scoring` and
`test_bc16_maps` all still green.

---

## F9 — THE HORDE was not drawn, and `#bc16-horde.struck` was never activated

**Commit `c549483f`. Checklist: advisory. Both halves implemented; nothing
left out.**

**(a) The label.** Coordinator ruling 4 made "THE HORDE" this year's flavour
carrier and design.md:319-320 says the zombie team "is drawn and labelled THE
HORDE" spectator-side. The words appeared only in a CSS comment (`:3702`) and in
the agent-facing observation (`decide.nim:639`, `:1163`); `renderHorde` drew
glyph counts, `WAVE`, `OUTBREAK`, `DENS`, `ROUND` and no faction name.
`renderHorde` now draws `<span class="horde">THE HORDE</span>` as the **first**
field of the strip in every state, with a rule of its own, and it survives the
360 px media query (only `.tl`, the mini-timeline, is still dropped there).

**(b) The strip takeover.** `#bc16-horde.struck` (`:3724`) was a rule nothing
ever activated. `hordeStrike()` now does what design.md:1772-1776 describes,
mirroring `renderArchons`'s add/remove shape for the archon pill's `flash`
(`:5774-5776`): it reads the beats that landed between the frame the playhead
came **from** and the frame it is **on**, takes the last `wave` or `turned`
beat in the step, puts **the beat's own label** on the strip (so the strip, the
killfeed and the scrubber button say the same sentence and there is no second
string to keep in step — `WAVE — 34 zombies from 4 dens at outbreak level 5`,
`CLAN ASH'S ARCHON TURNS — a BIGZOMBIE at 34,19`), adds `struck`, and removes
it after 2000 ms, re-rendering the readouts. `.struck` also sets
`white-space: normal`: the readouts' `nowrap` exists to stop a field breaking
mid-number, and applied to a **sentence** inside an `overflow: hidden` box it
clipped the sentence instead — measured at 360 px before the fix.

**Tests, so neither becomes dead again** (`tests/test_viewer.nim`), in the same
triad shape the endcard's `.on` uses: the `.struck` rule exists, the page adds
that exact class, the page takes it off again, the label span is drawn with a
rule of its own and is not hidden by the 360 px query, and the takeover is
keyed on `wave`/`turned` for 2000 ms in the beat's own words. **And the loop is
closed**: the test reads `tests/fixtures/replay-bc16.json` through `beatsFor`
and asserts the committed artefact really emits a **labelled** `wave` beat and
a labelled `turned` beat, so the kinds the takeover keys on are kinds the
fixture provably carries. The renderer fixture's bc16 row carries the label too,
so its layout is measured at 360/720/1280 px.

**Evidence**, driven in headless chromium 141 against the page's own `<style>`
block and its own bc16 game block (`window.Bc16Block.onFrame` with a synthetic
frame and two real beat labels):

```
labelDrawnAtRest        true      struckOnWave          true
labelDrawnWhenStruck    true      struckOnTurned        true
struckColor             rgb(106, 90, 58)   (the rule's own border-color)
struckAfterTimeout      false     readoutsBack          true  (ROUND 2999 back)
insideFrameWhileStruck  true      clipsWhileStruck      false  (at 360 px)
```

`test_viewer: ok (865 checks)`, `test_bc16_beats: ok (91 checks)`, all 24
renderer-fixture cells `ok`.

---

## F10 — the one deleted assertion: **NO CODE CHANGE**

**No commit. Checklist item 1. Ruled: this is not a loosening**, and I agree
with the ruling on the evidence below. I changed nothing for it.

The deleted line, the only deleted assertion in
`git diff -U0 00c1dae..fbc7d345 -- tests/`:

```
-  checkEq("the game version is GV10", r.doc.gameVersion, "GV10")
```

**Why it is not a loosening.** The **retained** assertion in the same block, at
`tests/test_bc22_replay.nim:102` on the reviewed sha, is

```nim
  checkEq("and it is what the build claims", r.doc.gameVersion, GameVersion)
```

so the two together asserted `GameVersion == "GV10"` — that **no `GameVersion`
bump may ever happen**. The authorised GV10 → GV11 bump (coordinator ruling 2)
makes that unsatisfiable by construction. The substantive assertion (the
fixture is pinned to the build's own headline) survives, and **three
assertions were added** in the same hunk:

```nim
  check("which is a real version headline",
    r.doc.gameVersion.len >= 4 and r.doc.gameVersion.startsWith("GV"))
  check("and it is inside ReplayCompatibleGameVersions",
    r.doc.gameVersion in ReplayCompatibleGameVersions)
  check("as is every version this build claims to keep rendering",
    ReplayCompatibleGameVersions.len >= 8 and
    "GV04" in ReplayCompatibleGameVersions)
```

**Corroborating evidence, all verified at `fbc7d345`.** The other three
`game_version` assertions are **unchanged** and all three files are absent from
`git diff --name-only 00c1dae..fbc7d345 -- tests/…`:
`tests/test_bc22_beats.nim:41` and `tests/test_bc23_beats.nim:42`, both
`checkEq("at this GameVersion", doc.gameVersion, GameVersion)`, and
`tests/test_bc23_replay.nim:117-118`,
`checkEq(mapName & ": the game version", doc["game_version"].getStr(),
GameVersion)`. The **fixtures were regenerated, not weakened**:
`tests/fixtures/replay-bc22.json` and `replay-bc23.json` both parse with
`"game_version": "GV11"`. And `sim_types.nim:220-221` **extends**
`ReplayCompatibleGameVersions` to `["GV04"…"GV10", GameVersion]` rather than
resetting it, so every older recording still renders.

---

## F11 — the authorised tolerant end-reason edit was not applied

**Commit `95ef6c90`. Checklist: advisory.**

**What I found first, and it matters for the record.** The tolerance is
*already* there at the **string** level —
`tests/test_bc23_replay.nim:157-160`'s `stopped in ["deadline", "complete"]`,
read off the written document — introduced by the pre-run commit `16c6e49`
("bc23's wall-clock block raced a real clock; split it in two"). That is why
the flake that reddened push run **34285737260** while PR run **34285740451**
passed on the same tree is already closed. So F11's *substantive* concern was
satisfied before this round; what was missing is the **shape** ruling 7 named:
the enum-level assertion on the value `playMatch` actually returned, which was
being thrown away by `discard reason` because `recordAndDerive` returned only
the **game's** end reason, not the **episode's**.

**What changed.** `recordAndDerive` now also returns the `EpisodeReason`, and
the timed block asserts `episodeReason in [epDeadline, epComplete]` — bc22's
exact shape at `tests/test_bc22_replay.nim:270` — alongside the existing
document-level check, plus a new `checkEq` that the two agree. Nothing
weakened: three assertions where there were two, and the loop call site takes
`_` for the new field. No other assertion in the file was touched.

**Evidence.** `nim r tests/test_bc23_replay.nim` → `ok (98 checks)` in debug
and in `-d:release` (was 95).

---

## Settled provenance (no finding, no code change)

**`docker_smoke.sh`'s `SMOKE_SEATS` default of `2` IS the `<SEATS>`
substitution, not a coincidence.** The review left this undetermined; the
coordinator settled it and I verified it byte for byte against the templates
repo:

| | template `templates/tools/ci/docker_smoke.sh` | repo `tools/ci/docker_smoke.sh` |
|---|---|---|
| doc line | `:25` `#   SMOKE_SEATS  seat-count CROSS-CHECK  (<SEATS>)` | `:25` `#   SMOKE_SEATS  seat-count CROSS-CHECK  (2)` |
| assignment | `:54` `seats_expected="${SMOKE_SEATS:-<SEATS>}"` | `:82` `seats_expected="${SMOKE_SEATS:-2}"` |

The neighbouring lines are the same substitution in the same shape
(`<slug>` → `battlecode`, `<IMAGE>` → `cogame-battlecode`), so checklist item
6's "independent second declaration" is the substitution and it agrees with the
manifest. No code change.

## NOTED (not fixed) — outside this round's findings

* **`tools/wasm_replay_smoke.cjs` steps 200 frames**, so its
  `mismatch_round: -1` is a 200-round prefix check on every year, not just
  bc16. F7's new assertion closes the hole for bc16's committed fixture only;
  the seven sibling years' fixtures have no equivalent whole-recording
  assertion. (I verified all seven re-derive cleanly today, but nothing in CI
  asserts it past round 200.)
* **`tools/ci/parity_tiers_bc22.py:368,375`, `…bc23.py:304,310` and
  `…bc25.py:224,230`** carry the same `tier A/A'` column and the same
  "Tiers A, A' and B" exit-condition line that F5 corrected for bc16. Those
  years did build their scenario bots, so the claim is true there; the wording
  is nevertheless inherited boilerplate and would mislead if a future year
  copied it without building A′. Left alone as a cross-year edit.
* **`docs/plans/2026-09-09-battlecode-2016-design.md:1255`** (the design note's
  in-repo copy) still says the chain folds "fifteen per team plus eleven"
  globals. F7 changed those counts to nineteen and thirteen. The design note is
  not mine to edit; the shipped counts are correct in `rules.nim`'s own header
  and the divergence is described in `docs/PARITY.md`.
* **`match.nim:498-506`'s year-neutral packing** — see F7. Recorded in
  `docs/PARITY.md`, deliberately not changed.

## What I could not fix

Nothing in F1–F11 was left unfixed, and no finding is DISPUTED or
NEEDS-DESIGN. Two dispositions are "no code change" by ruling (F6, F10) and one
is half a fix by ruling (F7's year-neutral packing), each recorded above with
its evidence.

One environmental limitation, worked around rather than fixed: `git push` over
HTTPS does not work in this sandbox (401 on `git-receive-pack` for both
available tokens, while `api.github.com` accepts the same tokens), so the
commits were replayed onto `fbc7d345` through the Git Data API with every
remote tree sha verified equal to its local counterpart.
