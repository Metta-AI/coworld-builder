# r1 fixes — battlecode-2019

Head: `16b424ffcf9fbeeaf90c109b7fd04dfb52753cdc` (merge commit on `main`)
CI: <https://github.com/Metta-AI/cogame-battlecode/actions/runs/34463989522> — **`success`**,
12/12 jobs, `ci.yml`, `push` on `main` at `16b424ff` (verified by `headSha`, not by `-L 1`).

Scope this round was the four documentation/comment truthfulness defects the coordinator named
out of the r1 review's 24 advisory findings (the review has **0 blocking-candidates**): F4, F6,
F17, F24. All four were **real** — each was confirmed at its cited `file:line` before it was
touched. Nothing else was changed.

**No behavioural change.** `git diff d2f5d3d707..16b424ff -- src/ tests/*.nim` is comment lines
only (`src/` is empty in the diff; the one `tests/*.nim` hunk is `##` comment text). No
assertion, threshold, literal, fixture or workflow step moved, and the three affected test
shards report the **same check counts** before and after (see the evidence rows).

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F6 | fixed | `53d4a677f075c049abed3316360b933254915ba8` | `docs/RULES-BC19.md:129` | **none** — advisory truthfulness defect |
| F4 | fixed | `1124d4da12b963dcd5e7fd1f27c236e178da502f` | `client/replay_broadcast.html:4144-4157` | **none** — 14(d) was already satisfied; the comment was advisory |
| F24 | fixed | `1aef1a429398c9c0ca742aa1d764705b48d4bbd8` | `docs/PARITY.md:2097-2102, 2117` | **none** — advisory truthfulness defect |
| F17 | fixed | `a7e3908e2a47aa5d42bc585054e6cd1961740352` | `tests/test_bc19_sheet.nim:150-156` | **none** — 9 was already satisfied; the comment was advisory |

Refused: **none**. Disputed: **none**. Needs-design: **none**.

`git diff --stat d2f5d3d7033925655cb64a26cc1a5879c041fec5 16b424ffcf9fbeeaf90c109b7fd04dfb52753cdc`:

```
 client/replay_broadcast.html | 15 ++++++++++-----
 docs/PARITY.md               | 13 +++++++------
 docs/RULES-BC19.md           |  2 +-
 tests/test_bc19_sheet.nim    | 10 +++++++---
 4 files changed, 25 insertions(+), 15 deletions(-)
```

---

## F6 — the `fuel_reserve` knob row said the opposite of what the knob test asserts

`docs/RULES-BC19.md:129`, commit `53d4a67`. **Confirmed before fixing:** the row's last sentence
said the test asserts raw attacks down; `tests/test_bc19_knobs.nim:353-362` asserts
`downPct("attacks per military unit built", mean(a.attacks, a.military), mean(b.attacks,
b.military), T["fuel.attacks_per_military.down_pct"])`, with thresholds at `:163-164`
(`fuel.zero_fuel_rounds.down_pct: 40  # measured -49 %`,
`fuel.attacks_per_military.down_pct: 20  # measured -58 % [substituted]`) and the substitution
recorded in the file header at `:52-59`, which states raw attacks move the other way,
1 296 → 2 331.

**Before** (row tail):

> Raising it buys survival and sells aggression, which is exactly the trade the knob test
> asserts: **rounds at zero fuel down, attacks down.**

**After** (row tail):

> Raising it buys survival and sells aggression — but **RAW attacks go UP** (1 296 → 2 331),
> because at reserve 0 the order cannot afford to BUILD a soldier either: 108 military units
> built, against 462 at reserve 1500, and more soldiers make more attacks. So the trade the knob
> test asserts is the one measured **per soldier the reserve paid for**: rounds ended with the
> fuel store at zero down (−49 %, threshold 40 %) and **attacks per military unit built** down
> (−58 %, threshold 20 %).

Same cog-facing register, same single table row, table structure untouched (one line changed,
`| … |` pipes intact). `tests/test_bc19_knobs.nim` was **not** touched — per the coordinator's
ruling the test is right and the sentence was wrong. Evidence it still is the test that shipped:
`test_bc19_knobs: ok (41 checks)` in the `test` job of both the reviewed run
(job `102798774973`) and the run at my head (job `102828140990`) — identical count.

**Checklist item: none.** No item names the knob table. Item 7's "tuned with a grid harness,
not guessed" is *supported* by `test_bc19_knobs.nim` and is unaffected by a doc sentence.

## F4 — the beat-marker comment claimed twelve emitted kinds

`client/replay_broadcast.html:4144-4157`, commit `1124d4d`. **Confirmed before fixing:** the
comment said `tests/test_bc19_beats.nim` "asserts that the COMMITTED FIXTURE REPLAY emits every
one of them"; that test asserts the reverse for `famine` at `:59-60`
(`checkEq("and \`famine\` is the one it does not (see the header)", "famine" in kinds, false)`),
names the other eleven individually at `:56-58`, exercises `famine`'s label from two synthetic
events at `:145-162`, and asserts a scoped rule for all twelve declared kinds at `:172-188`.
`famine` is only reachable on the refusal path of an affordability check
(`src/battlecode/years/bc19/actions.nim:143, 179, 210-211, 254, 272`), and every one of those
raises increments `refused_actions`, which the scripted champion's survival gate pins at 0
(`tests/test_bc19_baselines.nim:72-73`). `.github/workflows/ci.yml:4975` already said "ELEVEN OF
THE TWELVE" correctly, and so does `tests/test_viewer.nim:1775`.

**Before:**

> `/* Beat markers, EVERY ONE scoped to html[data-year="bc19"]. TWELVE kinds,`
> `   and `tests/test_bc19_beats.nim` asserts that the COMMITTED FIXTURE`
> `   REPLAY emits every one of them -- emission, label and style, all three,`
> `   and the CSS check reads the kinds the fixture ACTUALLY EMITTED rather`
> `   than a hand-written list (the bc25 r1-F26 finding). SIX of the twelve`

**After:**

> `/* Beat markers, EVERY ONE scoped to html[data-year="bc19"]. TWELVE kinds`
> `   DECLARED here, ELEVEN OF THEM EMITTED by the committed fixture replay:`
> `   `famine` fires only on the refusal path of an affordability check`
> `   (`src/battlecode/years/bc19/actions.nim`), and the scripted champion's`
> `   `refused_actions == 0` survival gate precludes it. That is what`
> `   `tests/test_bc19_beats.nim` asserts -- the eleven by emission, label and`
> `   style, `famine`'s ABSENCE from the fixture, its LABEL off two synthetic`
> `   events, and a scoped rule for ALL TWELVE declared kinds -- and the style`
> `   check reads the kinds the fixture ACTUALLY EMITTED rather than a`
> `   hand-written list (the bc25 r1-F26 finding). SIX of the twelve`

The rest of the comment (the six inherited names, the six new ones) and **all twelve CSS rules**
are byte-identical. Comment text only: `grep -c 'html\[data-year="bc19"\] .beat-marker\.'` is
**12** before and after, so the declared-kind inventory the test parses out of the page source at
`:172-188` is unchanged — and my comment deliberately contains no `.beat-marker.` selector text,
which would have been picked up by that parser.
Evidence: `test_bc19_beats: ok (1240 checks)` and `test_viewer: ok (1151 checks)` in job
`102828140990`, both identical to the reviewed run's counts.

**Checklist item: none.** Item 14(d) ("CSS for every kind the page emits") was satisfied at the
reviewed sha and still is — the reviewer's own verdict. This was a false comment, nothing more.

## F24 — `docs/PARITY.md` §bc19 §Status cited a superseded run

`docs/PARITY.md:2097-2102` and `:2117`, commit `1aef1a4`. **Confirmed and re-derived from the log
before fixing**, `gh api .../actions/jobs/102798775171/logs`:

- `compared 54 whole-game pairs, 0 failure(s)` (one line, log line 1009);
- `grep -c BIT-EXACT` = **54**;
- the five comparator self-test lines (`self-test: a one-line-longer trace diverges at round 2,
  as it must`, and four more);
- `ok …/data/bc19/tables.json: 7939 ceil(sqrt(r2)) values and 10 reclaim divisors`;
- `all 13 degenerate seeds refused by name`;
- the anti-vacuity block: `RED/BLUE: fuel rose by exactly 25 a round for 1000 rounds and
  karbonite never moved`, `ids seen across the whole game: ids=4`, `round 1000 has 1 action
  line(s)`, `wc=1`;
- `the CHURCH and its 0-damage attack fired on all nine boards`;
- the `bc19slowbot` Tier B′(b) run present;
- job timing `2026-09-10T08:23:06Z → 08:24:59Z` (= 1 m 53 s) from the jobs API;
- `parity-bc19-digests` is **absent** from run `34454858348`'s artifact list (read from
  `…/actions/runs/34454858348/artifacts`: `static-replay-viewer`, `viewer-smoke`, `parity-bc22`,
  `smoke-replay`, `parity-traces-bc24`, `parity-bc23`, `parity-bc25`, `parity-traces-bc21`,
  `parity-bc16`, `parity-traces`, `parity-vectors-bc20`), which is what the empty-ledger
  paragraph rests on. `tools/ci/parity_ledger_bc19.json` on disk is `[]`.

**Before:**

> which runs on every push. The first run taken as a verdict is
> **`34446572285`** — job `parity-oracle-bc19`, id `102772780365`, on
> `bc19-year-module` at `7aa8e6712c`, **conclusion `success`**, wall clock
> **1 m 57 s** (06:46:01Z → 06:47:58Z). Every tier named above ran in that one
> job and every tier passed:

**After:**

> which runs on every push. The run taken as the verdict is the one on `main`
> at the shipped sha: **`34454858348`** — job `parity-oracle-bc19`, id
> **`102798775171`**, on `main` at `d2f5d3d707`, **conclusion `success`**, wall
> clock **1 m 53 s** (08:23:06Z → 08:24:59Z), reporting `compared 54
> whole-game pairs, 0 failure(s)` over 54 `BIT-EXACT` lines. Every tier named
> above ran in that one job and every tier passed:

and, in the same paragraph's empty-ledger sentence, `does not exist in run `34446572285`` →
``does not exist in run `34454858348``. Both edits cite only what the log and the artifact list
say; no tier row was re-worded and no verdict was upgraded.

Note on the citation's sha: the run cited is the one at the **shipped/reviewed** sha
`d2f5d3d707`, as the brief directs — a §Status paragraph cannot cite the run of the commit that
carries it. For the record, `parity-oracle-bc19` is also `success` at my merge sha (job
`102828141062` in run `34463989522`, 54 `BIT-EXACT` lines), so the paragraph's substance holds at
`main`'s current head too.

**Checklist item: none.** Advisory. No checklist item cites the parity oracle.

## F17 — the truncation test's comment described the wrong rune

`tests/test_bc19_sheet.nim:150-156`, commit `a7e3908`. **Confirmed before fixing:** Nim's `\u`
escape consumes exactly four hex digits, so `"\u1F3F0"` is U+1F3F followed by ASCII `'0'` — a
3-byte rune plus one byte — not the 4-byte U+1F3F0. Checked arithmetically: 4 bytes and 2 runes
per repetition; the JSON prefix `{"sheet":{"opening":"turtle"},"notes":"` is 39 bytes, so the
16 384-byte cut lands 1 byte into a repetition, i.e. **mid-rune**, and 20 000 repetitions is
80 041 bytes > the cap. So every assertion in the block remains sound under the corrected
reading, which is why none of them was touched.

**Before:**

> `  ## Rune-boundary truncation, INCLUDING astral-plane characters, and the`
> `  ## 16 384-BYTE reply cap.`
> `  let long = repeat("\u1F3F0", 400)          ## a castle emoji, 4 bytes each`

**After:**

> `  ## Rune-boundary truncation with MULTI-BYTE input AT THE CAP, and the`
> `  ## 16 384-BYTE reply cap. Nim's `\u` escape takes EXACTLY FOUR hex digits,`
> `  ## so the literal below is U+1F3F -- a 3-BYTE rune -- followed by the`
> `  ## ASCII character `0`, not the 4-byte castle emoji U+1F3F0: still four`
> `  ## bytes and two runes a repetition, so the caps below are still fed`
> `  ## multi-byte text whose rune boundaries do not line up with the byte cut.`
> `  let long = repeat("\u1F3F0", 400)          ## 3-byte rune, then `0``

The literal `repeat("\u1F3F0", 400)`, the second literal `repeat("\u1F3F0", 20000)` and all five
`check`/`checkEq` calls are unchanged, as instructed. Evidence: `test_bc19_sheet: ok (215
checks)` in job `102828140990` — the same 215 checks as the reviewed run's job `102798774973`, so
nothing was added, removed or weakened.

**Checklist item: 9, already satisfied.** Item 9 requires "multi-byte input at the cap … asserts
the output is valid UTF-8", which this block always did. The astral-plane claim was the comment's
error, not the test's.

---

## NOTED (not fixed)

Left alone deliberately — not findings in this round's review and not in the brief. Recorded here
rather than edited.

1. **`docs/RULES-BC19.md:245`** (§Divergences item 14) ends: *"The knob's two asserted teeth are
   unchanged: rounds at zero fuel down, attacks down."* That is the **same false claim as F6** at
   a second site in the same file. F6 cites `:129` only and the brief names `:129` only, so I did
   not touch it. If the judge or the coordinator wants the file internally consistent, this is the
   one-line follow-up, and it is the only other occurrence in `docs/`
   (`grep -n 'attacks down' docs/RULES-BC19.md` → `:129` (now rewritten) and `:245`).
2. **`client/replay_broadcast.html:3626` and `:3898`** carry the same "asserts that the COMMITTED
   FIXTURE REPLAY emits every one of them" sentence for bc23 and bc16. Pre-existing, other years,
   flagged out of scope by the reviewer under F4; untouched.
3. **The reviewer's "could not determine" #2 is settled in the code's favour, no change needed.**
   `tools/ci/renderer_fixture.html:57-60` claims astral-plane characters and the claim is **true**
   there: the literals are `'\u{1F400}'` (`:167`) and `'\u{1F9C0}'` (`:169`), JS `\u{…}`
   braced escapes, i.e. genuine 4-byte runes, counted with `Array.from` (`:86`). Nothing to fix —
   the F17 defect was specific to Nim's four-hex-digit `\u`.

## How it landed

- Branch `claude/r1-fixes-sthr_01W9ytsyw786zhkaNTHb2dcb`, four commits, one per finding, created
  through the GitHub Git Data API (blob → tree → commit → create-ref; no force, no history
  rewrite — a plain `git push` is refused from this sandbox). Remote tree sha
  `eda7d26cba4f426eae374f43cc0315f9841467b2` equals the local `HEAD^{tree}`, so what landed is
  byte-for-byte what was reviewed locally.
- PR: <https://github.com/Metta-AI/cogame-battlecode/pull/15>, merged with `--merge` (a merge
  commit, as the year modules land) → `16b424ffcf9fbeeaf90c109b7fd04dfb52753cdc` on `main`.
- `ci.yml` run **34463989522** — `push`, `main`, `headSha 16b424ffcf9fbeeaf90c109b7fd04dfb52753cdc`,
  conclusion **`success`**, all 12 jobs `success` (`test`, `docker-smoke`, `wasm-viewer` and the
  nine parity oracles). Found by matching `headSha`, not by `gh run list -L 1`.
