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

---

## r1-F6b — the second site of the F6 falsehood

Added after the round closed, on the coordinator's ruling on `NOTED (not fixed)` item 1 above:
the sentence F6 removed from the knob table row lived at a second site in the same cog-facing
file, which left `docs/RULES-BC19.md` contradicting itself a page later. Scope was that one
sentence.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F6b | fixed | `96d0d6b974ce463329dfdcb629eccb4dc333097b` | `docs/RULES-BC19.md:244-250` (§Divergences item 14) | **none** — advisory truthfulness defect, same class as F6 |

**Before** (item 14's closing sentence):

> `    economy builds are funded whenever the order can pay. The knob's two`
> `    asserted teeth are unchanged: rounds at zero fuel down, attacks down.`

**After:**

> `    economy builds are funded whenever the order can pay. The knob's first`
> `    asserted tooth survives — rounds ended with the fuel store at zero down`
> `    (−49 %, threshold 40 %) — but the second inverts: RAW attacks go UP,`
> `    1 296 → 2 331, because an order at reserve 0 cannot afford to BUILD the`
> `    soldiers either, so what the knob test asserts is **attacks per military`
> `    unit built** down (−58 %, threshold 20 %). The `fuel_reserve` row of the`
> `    knob table above carries the reading.`

Consistent with the wording landed at `:129` in `53d4a677`, in §Divergences' own register and
wrap width, and it points at the knob table row rather than restating its arithmetic.
`tests/test_bc19_knobs.nim` is untouched — the substituted statistic is accepted. `git diff
16b424ff..f5de5bdb --name-only` is `docs/RULES-BC19.md` alone: no code, no test, no workflow.

**Grep afterwards, as asked** — `grep -n 'attacks down' docs/RULES-BC19.md` at `f5de5bdb`:

```
(no output, exit 1)
```

Zero hits in the file. **A third site does exist, and it is not in `docs/`:**
`src/battlecode/years/bc19/chassis/econ.nim:97-98` carries the same sentence as a code comment —

> `  ## for them. `fuel_reserve`'s teeth are unchanged and are exactly the two`
> `  ## the knob test asserts: rounds at zero fuel down, attacks down.`

I did **not** touch it: the ruling named `docs/RULES-BC19.md:245` and one file, and
`git diff 16b424ff..<head>` had to be that file alone. Repo-wide, those are all of them:
`grep -rn 'attacks down' .` at `f5de5bdb` returns exactly that one hit in `econ.nim`, and
`grep -rn 'asserted teeth\|two teeth\|both teeth'` returns nothing. `grep -rn 'rounds at zero
fuel'` returns `econ.nim:98` and `tests/test_bc19_knobs.nim:52`, the latter being the header
measurement, which is correct as written. So one comment in `src/` remains for whoever rules on
it; it is a comment on `canAfford`'s fuel gate and changing it moves no behaviour.

**Landed:** branch `claude/r1-f6b-sthr_01W9ytsyw786zhkaNTHb2dcb` (one commit, Git Data API,
remote tree `ee6350b6c43d23b1225fc529b6aeb8f1ab56d5fb` == local `HEAD^{tree}`), PR
<https://github.com/Metta-AI/cogame-battlecode/pull/16>, merged `--merge` →
**`f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`** on `main` (now `main`'s head).

**CI:** `ci.yml` run **34472691904** — <https://github.com/Metta-AI/cogame-battlecode/actions/runs/34472691904>
— `push`, `main`, `headSha f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`, conclusion **`success`**,
**12/12 jobs** success. Check counts unchanged again in its `test` job (`102856052199`):
`test_bc19_knobs: ok (41 checks)`, `test_bc19_sheet: ok (215 checks)`, `test_bc19_beats: ok (1240
checks)`, `test_viewer: ok (1151 checks)`.

`git diff --stat 16b424ffcf9fbeeaf90c109b7fd04dfb52753cdc f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`:

```
 docs/RULES-BC19.md | 9 +++++++--
 1 file changed, 7 insertions(+), 2 deletions(-)
```

---

## r1-F6c — the third site, in code comments

Added after the round closed, on the coordinator's ruling on the third site the post-F6b sweep
turned up. Scope was that one comment, and the ruling required it to land **after** the 0.9.0
release had been dispatched, so the release could not snapshot a sha whose `ci.yml` had not
concluded.

**The release run waited on:** `coworld-release.yml` run **34480332524** —
`workflow_dispatch`, `headSha f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb` (the r1-F6b merge, the
sha the coordinator gated on), `createdAt 2026-09-10T13:03:53Z`, conclusion **`success`** at
~13:15Z. It existed and had started before this fix was written, and I additionally waited for it
to **conclude** — its predecessors took 8–9 minutes, so the wait was cheap and it removes the one
residual hazard the ruling was aimed at: a failed release being re-dispatched on `--ref main`
into a window where my commit was present but its CI was not finished. My commit was created
after 13:15Z. Checked before landing, for the same reason: `ci.yml`'s concurrency group is
`ci-${{ github.ref }}` with `cancel-in-progress` only on `pull_request`, and
`coworld-release.yml`'s is `coworld-release` with `cancel-in-progress: false`, so a push to `main`
can cancel neither the release nor the `main` CI run.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F6c | fixed | `fd5dfc8146e09f004bab9af06fad94a11ec44cce` | `src/battlecode/years/bc19/chassis/econ.nim:97-103` (the doc comment on `canSpend`) | **none** — advisory truthfulness defect, same class as F6/F6b |

**Before** (last two lines of `canSpend`'s doc comment):

> `  ## for them. `fuel_reserve`'s teeth are unchanged and are exactly the two`
> `  ## the knob test asserts: rounds at zero fuel down, attacks down.`

**After:**

> `  ## for them. Of `fuel_reserve`'s two teeth the knob test asserts the first`
> `  ## as written — rounds ended with the fuel store at zero down, -49 %`
> `  ## against a 40 % threshold — and the second NORMALISED: raw attacks go UP,`
> `  ## 1 296 -> 2 331, because an order at reserve 0 cannot afford to BUILD the`
> `  ## soldiers either, so what is asserted is attacks per military unit built`
> `  ## down, -58 % against 20 %. `docs/RULES-BC19.md`'s `fuel_reserve` row`
> `  ## carries the reading.`

Consistent with `:129` (`53d4a677`) and `:245` (`96d0d6b9`), in the file's own `##` register and
wrap width (longest new line 79 chars; the file's previous longest was also 79), ASCII `-49 %` /
`1 296 -> 2 331` as the `.nim` comments in this repo write measurements, and it points at the
knob table row rather than restating the arithmetic.

**Comment lines only, verified mechanically:**
`git diff -U0 | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vE '^[+-]\s*##' | wc -l` = **0**.
`canSpend`'s three guards (`w.karbonite[t] - s.committedK < kCost`,
`w.fuel[t] - s.committedF < fCost`, and the `not essential and … < s.fuelGate()` gate) and every
constant are untouched; `tests/test_bc19_knobs.nim` is untouched. Correction to my own shorthand
in the F6b section above: the proc carrying this comment is **`canSpend`**, not `canAfford`.
`git diff --stat f5de5bdb f0570643` = `src/battlecode/years/bc19/chassis/econ.nim | 9 +++++++--`,
1 file, 7 insertions, 2 deletions.

**The sweep afterwards, at the merge sha `f0570643`:**

```
$ grep -rn 'attacks down' .
(no output, exit 1)

$ grep -rn 'rounds at zero fuel' .
./tests/test_bc19_knobs.nim:52:##  5. `fuel_reserve` 0 -> 1500 — rounds at zero fuel 9 381 -> 4 731 is
```

Exactly what was expected: zero hits for the falsehood anywhere in the repo, and the single
remaining `rounds at zero fuel` is the knob test header's own measurement, which is correct as
written. All three sites of the F6 sentence — `docs/RULES-BC19.md:129`, `:245` and
`econ.nim:97-98` — are now consistent with what `tests/test_bc19_knobs.nim` asserts.

**Landed:** branch `claude/r1-f6c-sthr_01W9ytsyw786zhkaNTHb2dcb` (one commit, Git Data API,
remote tree `0359511d4bd3744763bdb6af40a040dc1a00bc45` == local `HEAD^{tree}`), PR
<https://github.com/Metta-AI/cogame-battlecode/pull/17>, merged `--merge` →
**`f05706438808a4f6eac1a16a4445838f09f0422a`** on `main` (now `main`'s head).

**CI:** `ci.yml` run **34481618674** — <https://github.com/Metta-AI/cogame-battlecode/actions/runs/34481618674>
— `push`, `main`, `headSha f05706438808a4f6eac1a16a4445838f09f0422a`, conclusion **`success`**,
**12/12 jobs** success. Check counts unchanged again in its `test` job (`102885543960`), including
the shard that exercises `canSpend` through the scripted chassis:
`test_bc19_baselines: ok (72 checks)`, `test_bc19_knobs: ok (41 checks)`,
`test_bc19_sheet: ok (215 checks)`, `test_bc19_beats: ok (1240 checks)`,
`test_viewer: ok (1151 checks)` — all identical to the reviewed run's job `102798774973`.

**Note for the release ledger:** the shipped 0.9.0 artefact is the release run above, built from
`f5de5bdb`, which does **not** contain this commit. `main` is now one comment-only commit ahead of
what was released, and `ci.yml` is `success` on both shas.

---

## r1-F6c hand-off — authorised, then ordered deferred; the order arrived AFTER it had landed

**Correction to the record, first, because it matters more than the hand-off.** The coordinator's
stand-down ("do not land it, stop polling, land nothing") reached me **after** r1-F6c was already
merged and green. The section above this one is what actually happened and it stands. Timeline, in
UTC on 2026-09-10:

| time | event |
|---|---|
| 13:03:53Z | `coworld-release.yml` **34480332524** created on `f5de5bdbab` — 0.9.0 canonical + hosted-certified `cow_5657f03c-4ae9-406c-87c6-ea797645fece` |
| ~13:06Z | the ruling to fix F6c **after** the release reached me; I polled immediately and found 34480332524 already `in_progress`, which I reported as being older than the message |
| ~13:15Z | 34480332524 concluded **`success`**; I had additionally waited for that conclusion |
| 13:16:30Z | F6c merged as **`f05706438808a4f6eac1a16a4445838f09f0422a`** (PR #17, commit `fd5dfc8146e09f004bab9af06fad94a11ec44cce`); `ci.yml` run **34481618674** starts |
| 14:50Z | 34481618674 concluded **`success`**, 12/12 jobs, at `f0570643` |
| 14:52Z | report appended (`a94b0af4` in this repo) and reported to the coordinator |
| after that | stand-down received. **Nothing has been pushed to `Metta-AI/cogame-battlecode` since, and nothing will be.** |

So the wait condition was met in substance — the release was dispatched, and had *finished*, before
the fix was written — and the coordinator's own note that a run created after the instruction was
impossible is consistent with what I reported at the time. What was not possible was deferring a
commit that had already been merged four hours before the order to defer it.

**Current state of the repo, verified at the time of writing:** `main` head
`f05706438808a4f6eac1a16a4445838f09f0422a`; **no open PRs**; `ci.yml` `success` on `f0570643`
(34481618674) *and* on the released `f5de5bdb` (34472691904). The three `claude/…` branches from
this round remain in place (never deleted, per instruction). The repo is quiet.

**One consequence the resume needs, which nobody has ruled on.** Two `coworld-submit.yml` runs
were dispatched by phase 50 on `--ref main` at **13:20:05Z** (`34481984448`) and **13:20:48Z**
(`34482063422`), both **`success`** — and both carry `headSha f057064388`, i.e. they ran on the
F6c merge, three and a half minutes after it landed, not on the released `f5de5bdb`. The only
difference between those two shas is one `##` comment, so there is no behavioural consequence, but
the submit runs' sha does not equal the release's sha and a heartbeat comparing them will notice.
**`main` is one comment-only commit ahead of the 0.9.0 artefact.** Two ways to close it, both
needing a decision I did not take:
1. **Leave it.** `ci.yml` is green on both shas and the diff is a comment. The next release off
   `main` absorbs it. This is the cheap and, in my read, correct option.
2. **Revert `f0570643`** so `main` equals the released tree exactly. That is another push to a
   repo the coordinator has ordered quiet, and it would need its own CI run, so I did not do it.

**The hand-off itself, as requested — kept here so a resume finds the change already specified
rather than rediscovering it.** It is already applied at `f0570643`; if a future run reverts or
re-derives this tree, this is the text.

- **File and line:** `src/battlecode/years/bc19/chassis/econ.nim:97-98`, the last two lines of the
  doc comment on `proc canSpend*` (the fuel-gate ledger; **`canSpend`**, not `canAfford`, which is
  a shorthand slip in an earlier section of this file).
- **The false text** (as it stood at `f5de5bdb`, the released sha):

  > `  ## for them. `fuel_reserve`'s teeth are unchanged and are exactly the two`
  > `  ## the knob test asserts: rounds at zero fuel down, attacks down.`

  False for the same reason as `docs/RULES-BC19.md:129` (r1-F6) and `:245` (r1-F6b):
  `tests/test_bc19_knobs.nim:353-362` asserts *attacks per military unit built* down, and raw
  attacks measured **up** 1 296 → 2 331.
- **The replacement wording** (consistent with `:129` and `:245`, in the file's `##` register and
  79-char wrap, ASCII measurements as this repo's `.nim` comments write them):

  > `  ## for them. Of `fuel_reserve`'s two teeth the knob test asserts the first`
  > `  ## as written — rounds ended with the fuel store at zero down, -49 %`
  > `  ## against a 40 % threshold — and the second NORMALISED: raw attacks go UP,`
  > `  ## 1 296 -> 2 331, because an order at reserve 0 cannot afford to BUILD the`
  > `  ## soldiers either, so what is asserted is attacks per military unit built`
  > `  ## down, -58 % against 20 %. `docs/RULES-BC19.md`'s `fuel_reserve` row`
  > `  ## carries the reading.`

- **Comment-only, no behavioural component.** `git diff -U0 | grep -E '^[+-]' | grep -v
  '^[+-][+-]' | grep -vE '^[+-]\s*##'` is empty; `canSpend`'s three guards and `s.fuelGate()` are
  untouched; `tests/test_bc19_knobs.nim` is untouched (the substituted statistic is accepted);
  `test_bc19_baselines`, the shard that drives `canSpend` through the scripted chassis, reports the
  same **72 checks** before and after.
- **Authorised** by the coordinator as `r1-F6c` after the r1-F6b sweep found it, then **ordered
  deferred** because the run went **Blocked at phase 50** — the whole `battlecode` coworld is over
  its 15 USD/day spend cap (spent 15.39, `budget_status: over`, resets 2026-09-11T07:00:00Z), so
  the ladder creates no round and the repo is to stay still. The deferral order is honoured from
  here on: no further push.
- **The sha it sits on top of:** release run **34480332524**, `workflow_dispatch`, sha
  **`f5de5bdbab`** (0.9.0 canonical + hosted-certified `cow_5657f03c-4ae9-406c-87c6-ea797645fece`).
  As landed it is the single commit `fd5dfc81` on top of that sha, merged as `f0570643`.

**Sweep, still true at `f0570643`:** `grep -rn 'attacks down' .` → nothing repo-wide;
`grep -rn 'rounds at zero fuel' .` → only `tests/test_bc19_knobs.nim:52`, the knob test header's
own measurement, correct as written. All three sites of the F6 sentence agree with the test.
