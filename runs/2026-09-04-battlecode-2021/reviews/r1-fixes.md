# r1 fixes — battlecode-2021

Repo: `Metta-AI/cogame-battlecode`, branch `main`.
Review: `runs/2026-09-04-battlecode-2021/reviews/r1-review.md` (F1–F13, 0 blocking,
plus 4 *Could not determine* items).
Base: `bdc06b0488817d6079ab4e2797c7fe1a83adbde8` → head
`d2922438d0ac8a5b528d4f303f6b9d4e31d715f4` (7 commits, one per finding fixed).
CI on the pushed head: run **33886193070**, conclusion **success**, all 6 jobs green.

Note on mechanics: git-over-https authentication is not available in this sandbox
(`github.com` returns 401 for the placeholder token, `api.github.com` works), so the
seven commits were replayed onto `main` through the Git Data API, one API commit per
local commit, same messages and file modes. `git diff HEAD origin/main` is empty.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | **fixed** | `8f0821aa4` | `tools/ci/viewer_smoke.mjs:216,224,268,272,800` |
| F2 | **fixed** | `b3ae368a5` | `docs/RULES-BC21.md:299-312`, `tools/parity_trace_bc21.nim:14-18` |
| F3 | no change (documented deviation) | — | `docs/PARITY.md:285-363`, `tools/ci/parity_tiers_bc21.py:17-31` |
| F4 | **fixed** | `5e2710efd` | `client/replay_broadcast.html:2882-2895` |
| F5 | **fixed** | `02586801e` | `src/battlecode/years/bc21/chassis/bids.nim:15-26`, `docs/RULES-BC21.md:355-361` |
| F6 | **fixed** | `41dc4458f` | `tests/test_bc21_knobs.nim:47-74` |
| F7 | no change (documented deviation) | — | `tests/test_bc21_replay.nim:103-110,272-279` |
| F8 | **fixed** | `3c9f77dbe` | `src/battlecode/decide.nim:218-224` |
| F9 | no change (finding is about the note's shape, not the shipped docs) | — | `docs/PROTOCOL.md:170-177,216-268`, `docs/REPLAY.md:71,79,151,160` |
| F10 | no change (behaviour is asserted by a test; bound is inside item 5) | — | `src/battlecode/years/bc21/rules.nim:376-379`, `tests/test_bc21_replay.nim:228-230` |
| F11 | no change (sampling and structural enforcement are as designed) | — | `tests/test_bc21_baselines.nim:53-105`, `src/battlecode/years/bc21/world.nim` action procs |
| F12 | **fixed** (and its *could not determine* settled from the pinned Java) | `d2922438d` | `src/battlecode/years/bc21/world.nim:390-399`, `tests/test_bc21_build.nim:74-81` |
| F13 | no change (finding is a sketch-vs-value mismatch; item 10's shape holds) | — | `coworld_manifest_template.json`, `tests/test_manifest.nim:220-240` |
| CND 1 — item 7's "grid harness" | **NEEDS-DESIGN**, no change | — | — |
| CND 2 — the Java expression behind F12 | settled: reviewer's inference confirmed | (in `d2922438d`) | `InternalRobot.java:67` @ `battlecode21@ed39c1a4` |
| CND 3 — the `[139, 909]` mirror asymmetry | no change (would need a new experiment) | — | — |
| CND 4 — where the knob-gate swaps are recorded | **fixed** with F6 | `41dc4458f` | `tests/test_bc21_knobs.nim:47-74` |

---

## F1 — the `--killfeed-overlap` gate never executed  *(fixed, `8f0821aa4`)*

**What the code did.** `OVERLAP_SCRIPT` was a *source string* holding a function
expression (`` `((zoomValue) => { … })` ``) handed to `page.evaluate(OVERLAP_SCRIPT,
value)`. Playwright sends `isFunction: false` for a string, evaluates the expression
without calling it, and serialises the resulting function as `undefined`. Every one of
the 18 probes therefore returned nothing, and the failure filter `r.ok === false` could
never match.

**Reproduced before touching anything.** I downloaded the `static-replay-viewer` and
`smoke-replay` artifacts of run 33879654216 and ran the *unmodified* harness with the
pinned toolchain (playwright 1.55.0, chromium 1187, the build already installed at
`/opt/pw-browsers/chromium-1187`):

```
killfeed_overlap: [{width:360,zoom:"fit"}, {width:360,zoom:"2x"}, … ]   # no `ok` key
failure: null                                                          # exit 0
```

**What it does now.**
1. `ZOOM_SCRIPT` and `OVERLAP_SCRIPT` are real functions, so Playwright calls them
   (`viewer_smoke.mjs:216`, `:224`, `:268`, `:272`).
2. The zoom slider is driven in its **own** evaluate before the 350 ms settle, so the
   `2x` row measures the 2× layout rather than the FIT layout it had just asked for —
   the review's second-order consequence (b).
3. The failure filter is `r.ok !== true` (`:800`): a probe that returns nothing at all
   is a dead gate and must be red, not silent.

**Evidence that the armed gate passes, and that it gates.** Same bundle, same three CI
replays, patched harness:

```
bc26  360/720/1280 × fit,2x   ok=true  --statrail 81px/87px/87px   hits []
bc20  360/720/1280 × fit,2x   ok=true  --statrail 90px/90px/100px  hits []
bc21  360/720/1280 × fit,2x   ok=true  --statrail 90px/90px/100px  hits []   exit 0
```

The zoom really reaches 2× now — probing `#zoom-read` after `ZOOM_SCRIPT` reads
`FIT` then `2.0×` at each of the three widths, where before the slider was never set at
all. **Negative control:** the same bundle with `#killfeed { bottom: 0 }` spliced in now
reports `#killfeed overlaps [{"id":"bc21-influence","overlap":7752},
{"id":"bc21-units","overlap":4506}] at 360px / fit zoom …` on all six rows and **exits
1**. Before this commit that same broken bundle exited 0.

**Checklist item.** 13 ("Viewer executes" — the gate that runs the bundle now has a
failing mode) and 14(b) (nothing fixed-positioned sits inside the band — this is the
gate that proves it, on all three years).

## F2 — `docs/RULES-BC21.md` claimed a CI assertion that does not exist  *(fixed, `b3ae368a5`)*

**What the docs said.** §Divergences item 1: "The `parity-oracle-bc21` job asserts that
no Java robot on any traced game exceeds **80 %** of its bytecode limit, so the bot the
oracle runs provably never hits the boundary." Confirmed false on the reviewed sha:
`Bc21Trace.java:120` says the boundary is *"reported rather than asserted"* and its only
`System.exit` guard is the robots-at-round-50 check; `parity_tiers_bc21.py` contains no
bytecode threshold; and run 33879654216's `parity-oracle-bc21` log prints
`peak bytecode use = 102%` with a `BC21_FIRST_CUTOFF` on all five maps.

**What the docs say now.** That the job *measures* the boundary — reads
`getBytecodesUsed()`, reports the peak, prints the first mid-turn cut-off, and lets
`cutoff - 1` size the Tier A window — with the measured 102 % and the five cut-off
rounds (27, 23, 33, 23, 246) named, and a pointer to `docs/PARITY.md`, which already
accounted for it honestly. The same stale claim in `tools/parity_trace_bc21.nim:14-18`
("checks it separately for the 80 %-of-limit assertion") is corrected in the same
commit.

**The gate was not touched**, per the brief: at a measured 102 % an 80 % assertion would
fail, so adding it would be inventing a red gate rather than a true statement.

**Checklist item.** None directly (no parity item); this is the published `game.docs`
page, so it serves item 10's docs and the general "no untrue statement in the shipped
docs" reading of item 1.

## F3 — Tier A window, Tier B content, Tier C ledger weaker than the design pins  *(no change)*

I did not change the parity job, and here is why each of the three gaps is an
already-documented deviation rather than a defect I can fix at the cited site:

1. **Tier A's window** is not a number the repo chooses. `parity_tiers_bc21.py:97` sets
   it to `cutoff - 1`, where `cutoff` is the round the **JVM itself** first cut a robot
   off mid-turn. Past that round the two models have consumed a different number of RNG
   draws and a bit-exact comparison is not defined (`Bc21Trace.java:120-133`). Making
   the window longer would mean asserting agreement past the point where agreement has
   no meaning. The `TIER_A_FLOOR = 20` guard exists precisely so a *shrinking* window
   fails loudly.
2. **Tier B.** The name is reassigned, and `parity_tiers_bc21.py:30-31` says so in the
   module docstring: *"(Tier B is the two JDK-only arithmetic steps, which live in the
   workflow because they need a JVM and no trace)"*. `docs/PARITY.md:355-363` states the
   omission in the reader-facing doc. Building the design's round-300/700/1500 aggregate
   comparison is a new oracle mode, not a fix at a cited line — it is a design change,
   and one whose result is already predicted by the ledger (the traces diverge at rounds
   27–246, so a round-300 aggregate comparison would fail as designed).
3. **Tier C's ledger is non-empty**, and `parity_ledger_bc21.json:9` says so in its own
   preamble: *"The target state is an EMPTY ledger. It is not empty…"*. Emptying it means
   removing the 102 %-bytecode divergence, i.e. implementing a bytecode counter — the
   thing §Divergences item 1 declares out of scope.

The checklist has no parity item, the deviation is disclosed in the two places a reader
looks (`PARITY.md` and the script's own docstring), and F2 removed the one place where a
shipped doc contradicted it. Recorded for the judge, unchanged.

## F4 — the bc21 block redefined two inherited `.beat-marker` kinds globally  *(fixed, `5e2710efd`)*

`client/replay_broadcast.html:2883-2884` declared `.beat-marker.doctrine` and
`.beat-marker.capture` **unscoped**, at equal specificity and later in the sheet than
the bc26 rule (`:2639`) and the inherited coworld-ctf rule (`:1732`), so they won for
all three years. All seven kinds this block styles now carry the
`html[data-year="bc21"]` prefix every other rule in the block already had
(`:2887-2895`).

**Evidence** (headless chromium, CI-built bundle with only this block swapped in,
probing a synthetic marker of each kind on each year's replay):

```
before   bc26/bc20  doctrine rgb(216,196,138) gold      capture rgb(143,191,106) 3px×10px
after    bc26/bc20  doctrine rgb(127,178,232) blue      capture rgb(232,163,61)  3px×12px
after    bc21       doctrine rgb(216,196,138)           capture rgb(143,191,106) 3px   (unchanged)
```

**Checklist item.** 14(d) — "CSS for every kind the page emits"; all ten bc21 kinds
still resolve (`tests/test_viewer.nim:262-265` passes on substring), and the other two
years' kinds are no longer overpainted.

## F5 — two formulas in `bids.nim`'s header and `RULES-BC21.md` item 11 that the code does not use  *(fixed, `02586801e`)*

| | stated | code |
|---|---|---|
| jitter | header `(id*7 + round*3) mod 3`; docs `hash(id, round) mod 3` | `(((id xor round·0x9E3779B1)·0x85EBCA6B) shr 13) mod 3` (`bids.nim:59-61`) |
| bid bank | both `20 + round/5`, capped at 300 | `min(150, 15 + round div 10)` (`bids.nim:92`) |

Both texts now state the code's formulas, and the header carries the reason the
additive jitter was replaced (already inline at `bids.nim:55-58`: two ids congruent
mod 3 tie in every round). Comment and documentation only — the chassis is untouched, so
no seeded game, hash chain or ledger entry moves.

## F6 — four (in fact five) of the ten asserted knob deltas are not the design's statistics  *(fixed, `41dc4458f`)*

The header claimed *three* swaps and said each was "recorded in the build report and in
docs/PARITY.md". `docs/PARITY.md` is the Java-oracle document and has no knob-gate
section, so the pointer was to nothing — this is also *Could not determine* item 4.

`tests/test_bc21_knobs.nim:47-74` now records **all five** deviations from the note's
table, each with the reason and the measured numbers that are already in the table above
it: `muck_ratio`'s enemy-half turns; `politician_size_curve`'s mix-built mean **and** its
3× → 2.5× threshold; `politician_size_curve`'s second gate (politicians built down
≥ 25 %, not empowers down ≥ 30 %); `empower_threshold`'s per-politician rate; and
`empower_threshold`'s second gate (politicians alive up ≥ 20, not conviction per empower
up ≥ 2×). The header is named as the record, so the file no longer points at a document
that does not carry it.

**No assertion, threshold or statistic was changed** — the shard still runs its 19
checks in both modes. Making the code assert the note's statistics instead would be
re-tuning the gate, which is a design decision, not a fix.

## F7 — record → re-derive covers three of the six end reasons  *(no change)*

`tests/test_bc21_replay.nim:103-110` declares the split in the file itself, `:158-163`
gives the reason the other three cannot be produced by a scripted pairing on the `small`
pool (a team that has lost every Center keeps 1-influence muckrakers wandering to the
last round — which is what the rule says should happen), and `:272-279` asserts the
split, so no rung passes on a string nobody produced. All six rungs go through the same
`checkEndOfMatch` a played game calls.

Checklist item 2 is met independently and with citations: `replay.nim:284-309` compares
**every** round's chain, `test_bc21_replay.nim` asserts `mismatchRound == -1` on four
independent recordings, and the CI `wasm-viewer` step printed `"mismatch_round":-1` on
all five replays it re-derived. What is unmet is the design note's broader claim, and
producing an `annihilated`/`more_influence`/`coin_flip` recording means authoring new
scripted scenarios — new test scaffolding, not a fix at a cited line. Recorded as a
deliberate, disclosed deviation.

## F8 — the bc21 preamble's scoring block had no heading and the ladder was missing  *(fixed, `3c9f77dbe`)*

`src/battlecode/decide.nim:218` now opens a `HOW A GAME ENDS` section — the heading both
sibling years use above the same scoring line — and states the four-rung ladder the
engine fires: annihilated, more votes, more Enlightenment Centers, greater total
influence, coin flip (drawn from the map's own `randomSeed`, `rules.nim:146-152`), plus
the round-1500 cap and the fact that annihilation outranks it (`rules.nim:160-168`,
`world.nim:71-77`). Prompt text only; no knob, scoring or event change.

**Checklist item.** None directly; it is the seat-facing statement of how a game is won,
and the note's §Decisions list of what the shared preamble carries.

## F9 — `rules_digest`, the second `doctrine_requested`, and `votes` on `game_end`  *(no change)*

All three are differences between the **design note's** sample payload/event table and
the recorded shape. The *shipped* documentation already describes the code correctly, so
there is no untrue statement to repair and no consumer to unbreak:

- `docs/PROTOCOL.md:170-177` states outright: **"No `rules_digest` … They ship instead in
  the system preamble … which the replay records once, at document level, as
  `prompt_preamble`."** `:216-268` documents the bc21 payload key by key, including
  `sheet_schema`, and repeats where the digest lives. Nothing is withheld from a seat;
  duplicating a ~6 KB digest into every seat's recorded observation would only inflate
  the replay.
- `doctrine_requested` is emitted once per LLM seat (`decide.nim:342-343`), so the
  observed count is ≤ 2 against the note's bound of 4 — **under** the bound. The retry
  batch emits `doctrine_retry`, which `docs/REPLAY.md:151` documents.
- `game_end`'s fields are exactly what `docs/REPLAY.md:79`, `:160` and `:231` list
  (`winner_alias`, `end_reason`, `points`), and the endcard reads votes from
  `result.games[].votes` (`client/replay_broadcast.html:3563-3565`), so nothing is
  un-drawable. Adding a bc21-only `votes` field would mean editing the event writer and
  three shipped documentation tables to satisfy a note's table — scope, not a fix.

## F10 — the wall-clock guard is polled every 32 rounds  *(no change)*

`rules.nim:376-379`'s `(w.currentRound and 0x1F) == 0` is **deliberate and asserted**:
`tests/test_bc21_replay.nim:228-230` checks the abandon lands *"at the first sampling
point past the budget"* (`(roundsPlayed and 0x1F) == 0`), and the abandoned game's stop
round is the one load-bearing record playback replays. Removing the mask would make that
assertion fail, and the only way to keep it green would be to rewrite it — which the
brief forbids.

The overrun is bounded and small: the release perf shard measures a 1500-round
worst-case game at 4.655 s (≈ 3.1 ms/round), so 31 rounds ≈ 0.1 s per game, ≈ 0.3 s over
a best-of-three, against the design's 445 s ≤ 720 s arithmetic; `match.nim:209-214`
clamps each game's budget to the match remainder so the match cannot walk past
`matchBudgetSeconds`. **Checklist item 5 holds** — every wait has an explicit bound and
the episode settles inside 60 % of the episode timeout.

## F11 — the invariant audit samples ~1 round in 25, and one assertion is vacuous  *(no change)*

- **Sampling.** `tests/test_bc21_baselines.nim:104-105` audits at
  `round mod 25 == 0 or round < 5` over six full 1500-round games. Emission-time
  legality is enforced *structurally* rather than by assertion: every action proc in
  `world.nim` (`move:513`, `buildRobot:539`, `bid:574`, `setFlag:586`, `doEmpower:146`,
  `expose:179`) re-checks its own `canX` and returns without effect, so an illegal order
  is a no-op and cannot produce an illegal *state* for the audit to find. Auditing every
  round of six 1500-round games is a 25× cost on a shard that already runs twice per CI
  job, for a class of violation the type system and those guards make unreachable.
- **The vacuous `opsLeft < 0` assertion** (`:78`) is true by construction — `spend`
  (`kit.nim:74-79`) is the only debit, returns early at `opsLeft <= 0`, and every call
  site in all ten chassis files passes `ops = 1`. Deleting it would be removing an
  assertion, which the brief forbids; it costs nothing and would fire if a future
  `spend(r, n)` were introduced. The substantive budget check is `:135-138`, which pins
  each type's `DecisionOps` at one tenth of the Java `bytecodeLimit`.

Checklist item 7's first half is satisfied and cited by the review itself
(`test_bc21_replay.nim:115`, `:135`, plus the docker-smoke `"reason":"complete"`).

## F12 — `convictionAtSpawn` did Java's `float × int` product in `float64`  *(fixed, `d2922438d`)*

The review labelled this *inferred* and listed the pinned Java as *Could not determine*.
**I fetched it**: `battlecode21@ed39c1a4`, `engine/src/main/battlecode/world/InternalRobot.java:67`:

```java
this.conviction = (int) Math.ceil(this.type.convictionRatio * this.influence);
```

`convictionRatio` is declared `public final float` (`RobotType.java:55`) and `influence`
is an `int`, so JLS 5.6.2 makes the product a **float**; the widening to `double`
happens at the `Math.ceil` call, after the multiply. The reviewer's reading was right
and the code comment (`world.nim:392`, "widened to double by the multiply") was the
opposite of what the language does.

**What it does now:** `int(ceil(float64(RobotSpecs[kind].convictionRatio *
float32(influence))))` — Java's float product, widened only at the ceil — with the
comment corrected and the pinned file cited.

**Evidence, from the pinned constant on a real JDK** (`0.699999988079071f`, local
`java`):

```
x=1,3,10,11,100        java(float*int) = 1,3,7,8,70   = float64 product   (unchanged)
x=2 995 933            java(float*int) = 2097153      float64 = 2097154   (first disagreement)
x=2 995 943            java(float*int) = 2097160      float64 = 2097161
```

The two forms agree for **every influence below 2 995 933**, so no game this design can
reach changes and the committed replay fixtures' hash chains are untouched; a swept
comparison over 1…10⁷ shows `convictionRatio = 1.0f` (Center, politician, slanderer)
never differs at all. The 2 995 933 case is the new assertion at
`tests/test_bc21_build.nim:80-81`, so the two forms are no longer interchangeable to the
suite. **No existing assertion was changed** (the seven `ceil(ratio*C)` cases above it
are byte-identical and still pass by the Java table above).

**Checklist item.** None directly; it is the parity claim `docs/PARITY.md` and the Tier A
window rest on.

## F13 — `game.docs` uses `"type": "uri"` where the checklist sketch writes `"text"`  *(no change)*

Item 10's *structural* requirement is met exactly and is asserted
(`tests/test_manifest.nim:220-240`: `readme` is a `{type,value}` object, all five
`pages` are `{id,title,content{type,value}}`, every target file exists,
`game.protocols` carries both `player` and `global`). The `uri` value is inherited
unchanged from `e17947d9`'s shipped, canonical 0.2.0 manifest, the design note pins it
(§Packaging), and the installed platform CLI accepts the template — the `test` job's
step "The coworld CLI accepts the manifest template" is green on the reviewed sha and on
this one. Changing the `type` to `text` while the `value` stays an `https://…` URL would
make the manifest describe its own contents wrongly and risk the CLI check, to satisfy
the *sketch* rather than the requirement. Unchanged, deliberately.

---

## The *Could not determine* items

### CND 1 — checklist item 7's "The baseline's parameters were tuned with a grid harness, not guessed."  *(NEEDS-DESIGN, no change)*

I re-ran the reviewer's search and reached the same result: there is **no tuning harness
in the tree**, for bc21 or for either older year (`ls tools/`, and
`grep -rn "grid harness\|grid_harness\|gridsearch\|sweep" tools/ tests/ docs/ src/`).
The design note does not claim one — it calls the ten knobs "v1 candidates; the builder
finalises them from the chassis it ports" (`design.md:51`) — and the defaults
(`years/bc21/knobs.nim:74-86`) carry no per-value provenance in the tree.

I did **not** fix this, for two reasons, and I flag it as the one item that may need a
decision above me:

- The only honest fixes are (a) commit a real sweep harness **and its recorded output**,
  which means running the sweep — the sandbox has no Nim toolchain, so I cannot run one,
  and committing an unrun harness with a hand-written result table would be fabricating
  the evidence the item asks for; or (b) write a provenance paragraph — but I can only
  verify the *structural* defaults against the ported bot (`bid_policy: proportional` is
  maxecosushi's ladder, `expansion: neutral_centers_first` is its neutral-capture
  behaviour); the numeric ones (45, 25, 60, 700) I cannot trace to any source in the
  tree, and writing that they came from the reference bot would be a claim I have not
  checked. Writing an unverified provenance note is exactly the failure mode F2 and F5
  were about.
- If a sweep were run and it selected different values, changing the published defaults
  is a design change (they are in the manifest's documented sheet, the fallback sheet
  and the champion prompts), not a review fix.

**What would settle it:** a committed sweep harness plus its output for the
`california-roll` defaults (axes, values tried, the statistic maximised, the values
selected), or a design-note/`docs/` paragraph naming the provenance of each of the ten
defaults. Both are phase-20-shaped work.

### CND 2 — the exact Java expression behind `convictionAtSpawn`  *(settled)*

Fetched and read from the pinned tree; see F12. `InternalRobot.java:67` +
`RobotType.java:55` confirm the reviewer's inference, and the port now matches the Java
promotion exactly rather than being merely unreachably different from it.

### CND 3 — whether the `[139, 909]` unit-count asymmetry in a mirror match is expected  *(no change)*

I did not run the controlled experiment the reviewer describes, and I did not add one:
disabling the bid jitter and the bid bank to compare per-round aggregates needs a new
build flag and a new shard, which is new test scaffolding rather than a fix at a cited
line. What this round did do is make the two documented asymmetries honest: the jitter
is now stated as the id/round multiplicative hash it actually is, in both places (F5), so
anyone reproducing the asymmetry starts from the real formula. The strongest existing
counter-evidence stands unchanged — Tier A is bit-exact against the Java engine on ids,
cooldowns, flags, bids, buffs and convictions across five map pairs, which a
side-dependent rule bug would have broken.

**What would settle it:** the reviewer's own proposal — a paired self-play run on a
rotationally symmetric map with the jitter and the bank disabled, asserting the two
teams' per-round aggregates are mirror-equal until the first interaction.

### CND 4 — whether the knob-gate swaps are recorded where the shard's header says  *(fixed with F6)*

They were not: `docs/PARITY.md` has no knob-gate section. The header no longer points
there; it is itself the record, and it now lists five swaps rather than three
(`41dc4458f`).

---

## NOTED (not fixed)

- `docs/plans/2026-09-04-battlecode-2021-design.md` (the design note's copy inside the
  repo) still carries the 80 %-assertion sentence at `:774`, `:1363` and `:1589` that F2
  removed from the published rules page. It is a record of what was planned, not a
  reader-facing claim about what shipped, so I left it alone rather than editing a
  design note.
- `viewer_smoke.mjs`'s two pre-existing script constants (`INIT_SCRIPT:496`,
  `READOUT_SCRIPT:587`) remain source strings ending `})();`. They are correct as
  written — they take no arguments — but they are the template's shape that made F1's
  construction look right. A template-side note that a parameterised probe must be a
  function is out of this repo's scope.

---

## CI

Run **33886193070** — `main`, head `d2922438d0ac8a5b528d4f303f6b9d4e31d715f4`,
workflow `ci.yml`, event `push`:
https://github.com/Metta-AI/cogame-battlecode/actions/runs/33886193070

Conclusion: **success**. All six jobs green — `test`, `parity-oracle`,
`parity-oracle-bc20`, `parity-oracle-bc21`, `docker-smoke`, `wasm-viewer`. No
`continue-on-error` was added and no test was skipped, deleted, weakened or
re-thresholded in this round: the only test-file edits are `test_bc21_knobs.nim`
(comment block only — still `bc21 knobs: ok (19 checks)`, twice) and
`test_bc21_build.nim` (**one assertion added** — `bc21 build: ok (29 checks)`, twice,
up from 28).

**The armed gate ran and reported, in CI.** The `viewer-smoke` artifact of this run
carries real probe rows where run 33879654216's carried nulls:

```
viewer-smoke-replay.json       bc26  6/6 rows ok=true  --statrail 81px/87px/87px
viewer-smoke-replay-bc20.json  bc20  6/6 rows ok=true  --statrail 90px/90px/100px
viewer-smoke-replay-bc21.json  bc21  6/6 rows ok=true  --statrail 90px/90px/100px
failure: null on all three
```

Checklist item 1 (CI green on `main` at the head of this round, no test loosened) is
satisfied with this run id.
