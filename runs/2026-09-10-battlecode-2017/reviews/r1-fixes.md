# r1 fixes — battlecode-2017

Branch: `bc17-r1-fixes` off `main@4bcb8db` (PR #20 merged while this round was
in flight; rebased onto the new `main`, as the brief directs — the reviewed
base `07ad48cc` is `4bcb8db`'s first parent).
PR: **#22** — <https://github.com/Metta-AI/cogame-battlecode/pull/22>
Branch head: **`d8cf0e975903f7fbbaff03a6c40065a4f8089a3b`**
Branch CI: run **34550806187** —
<https://github.com/Metta-AI/cogame-battlecode/actions/runs/34550806187> —
conclusion **`success`**, 13/13 jobs (`test`, `docker-smoke`, `wasm-viewer`,
`parity-oracle` and all nine per-year oracles).
Merged with `--merge` (no squash). Merge commit on `main`:
**`526befdb6b34bff22fe13d9ac1007850ce84d16c`**
`ci.yml` on `main` at that sha: run **34557429247** —
<https://github.com/Metta-AI/cogame-battlecode/actions/runs/34557429247> —
conclusion **`success`**, 13/13 jobs, `run_attempt: 1`, `event: push`,
`head_branch: main`. **`main` is green at its tip.**

(PR #21 `bc19-doctrine-deadlines` merged to `main` between the branch CI run
and this merge, so `526befd` is the first run of `ci.yml` over both changes
together.)

Fourteen commits, **one per finding**, each message naming the finding.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking, item 2) | fixed | `8e27c91` | `tests/test_bc17_replay.nim` (new, 542 lines); `.github/workflows/ci.yml:5686` |
| F2 (blocking, item 15) | fixed | `87dbe65` | `tools/ci/renderer_fixture.html:70-71,79-91,+bc17 row`; `client/replay_broadcast.html:4020-4062`; `tests/test_viewer.nim:396-398,1897-1899,1981-2016` |
| F3 | fixed | `44d6256` | `client/replay_broadcast.html:4092-4119` |
| F4 | fixed | `b9f4e4b` | `src/battlecode/broadcast.nim:2450-2510`; `client/replay_broadcast.html:4094-4104,4660-4664,8435-8484`; `tests/test_viewer.nim:1947-1958` |
| F5 | fixed | `08bf773` | `client/replay_broadcast.html:4083-4088,8346-8389` |
| F6 | fixed | `823c32f` | `.github/workflows/ci.yml:4297-4336` |
| F7 | fixed | `fa7200c` | `docs/RULES-BC17.md:256-289` |
| F8 | fixed | `3149f79` | `docs/RULES-BC17.md:247-256`; `src/battlecode/years/bc17/chassis/examplefuncsplayer17.nim:7-14`; `src/battlecode/years/bc17/world.nim:95-98` |
| F9 | fixed | `8b7c89a` | `docs/PARITY.md:2286-2296` |
| F10 | fixed (all eleven restored) | `9cf41fc` | `.github/workflows/ci.yml:5176-5360` |
| F11 | fixed (the named path only) | `64bba33` | `tests/test_bc17_baselines.nim:179-221` |
| F12 | **NO CHANGE — ruled** | — | — |
| F13 | fixed | `528c15d` | `NOTICE:899-913`; `tests/test_manifest.nim:782-806` |
| F14 | **NO CHANGE — ruled** | — | — |
| F15 | root-caused and fixed | `544002c` | `client/replay_broadcast.html:8409-8435,8554`; `.github/workflows/ci.yml:5733-5744` |
| checklist item 13, last bullet | settled with evidence | `d8cf0e9` | `tools/ci/viewer_smoke.mjs:697-704,755-790,905-910`; `.github/workflows/ci.yml:5733-5792` |

`git diff main..HEAD -- tests/` removes exactly **four** lines, all of them
count or list updates (`NINE of them` → `TEN of them`, the fixture's
`YEARS` literal, and the five-element bc17 id list replaced by a six-element
one). **No assertion deleted, no tolerance widened, no `skip`/`xfail` added,
no test file removed.**

Every fix below was driven locally before CI: Nim 2.2.4 through
`nimby use 2.2.4` + `nimby --global sync nimby.lock`, and — this turned out
to matter — a **real headless Chromium** (`/opt/pw-browsers/chromium-1194`)
driven by Playwright, which let the renderer fixture and the bc17 game block
be executed rather than argued about.

---

## F1 — bc17 had no replay re-derivation test (checklist item 2)

**What it did.** Nothing in the repository asserted that a bc17 recording
re-derives. The only evidence was CI-side and bounded: `wasm_replay_smoke.cjs`
steps **200 frames** of a 2 697-round fixture. `ci.yml:5687`'s sentence
stopped mid-thought where bc16's and bc19's name the test that closes the gap,
because for bc17 there was none.

**What it does now.** `tests/test_bc17_replay.nim`, 542 lines, the note's
§Tests items 25 and 26:

* the document round-trips and the **written bytes** are strict UTF-8
  (`r.text.validateUtf8() == -1`), and so are the committed fixture's;
* **the re-derivation is asserted positively.** `derivedRounds()` walks the
  deriver frame by frame, compares `session.hashChainHex()` against the
  recorded slice **itself**, and returns the count — so the assertion reads
  "N of N rounds agreed" rather than "`mismatchRound` did not complain". A
  recording with an empty `hash_chain_rounds` would also report `-1`;
* **and a per-tick state digest beside the chain.** `foldRoundHash` folds
  thirteen quantities a team plus eleven globals — not the robot table, not
  the bullet table, not the two id generators. `digest(w)` folds every body's
  position, health, type, `roundsAlive` and action counters, every bullet's
  position, direction, speed and damage, both bullet supplies as **raw
  float32 bits**, both VP totals, the broadcast arrays, the exec order, the
  trove layout and both `IDGenerator` states — walked in the sim's own
  deterministic orders. It is taken on the RECORDER's world through
  `playGame`'s `onRound` hook and on the DERIVER's world at the same frame,
  and the two sequences are compared element by element. That is checklist
  item 2's "reproduces the recorded per-tick state **frame by frame**" read
  literally;
* `plan.maps` carrying all three drawn maps on a two-game clinch;
* `sheet_envelope` / `sheet_submitted` round-tripping, through `parseReplay`
  as well as through the raw JSON;
* every event kind inside the per-game bound `years/bc17/world.nim`'s own
  `BeatBounds` declares — read from that table rather than copied, with
  `game_abandoned` and `game_end` counted together against their shared slot;
* record → re-derive for the **`abandoned`** stop (synthetic, no clock, and
  the deriver reads `plan.abandon_after` for a game with no `GameHeader` and
  stops exactly there) and for the **`deadline`** stop (timed, tolerant);
* three distinct ladder end reasons exercised —
  `all_robots_destroyed, more_victory_points, victory_points_reached`;
* the committed `tests/fixtures/replay-bc17.json` re-deriving to its **last**
  round, 2 697 of 2 697, not the wasm smoke's first 200.

**Evidence.** `test_bc17_replay: ok (107 checks)` in both modes locally.
**Negative control run:** flipping one bit of one reference digest
(`reference[400] ^= 1`) turns the state-digest check red and names the exact
round — `got 401 want -1`. The shard also asserts the digest **varies** round
to round (≥ half the rounds distinct), so it cannot pass vacuously.

**Two things the note asked for that this shard does differently, both
recorded rather than dropped.** The note's "a 2 999-round game with **≥ 300
bullets in flight** recording under 400 KB" is asserted at the **measured**
peak instead: 38 bullets in flight is the most any committed board and
doctrine pole produces in this port (`Whirligig`, both poles, 3 000 rounds) —
2017 armies are small and its shots come one, three or five at a time, so 300
is not reachable and inventing a board nobody plays would be worse. The size
claim itself is asserted on a whole 2 999-round recording. And the boards are
chosen for **cost**: a 2 999-round bc17 game is 1.7–17.5 s in DEBUG on the
`small` pool and every `record()` pays for the game twice (play, then
re-derive), so the seeds are picked to keep the shard at **60 s debug / 11 s
release**.

The shard is wired by existing: the `test` job runs `ls tests/*.nim`.
`ci.yml:5686` now names it, the way the bc16 and bc19 sentences do.

## F2 — the worst-case renderer fixture did not cover bc17 (checklist item 15)

**What it did.** `tools/ci/renderer_fixture.html`'s `YEARS` listed nine years
and `grep -c bc17` was 0, so the tenth year — the one under review — was the
only chrome in the repo never laid out at `MaxNoteRunes` / `MaxMottoRunes` at
360 / 720 / 1280 px. Every CI replay is scripted and carries the short
baseline strings, which is exactly the cogchemists case the fixture exists
for.

**What it does now.** A bc17 row: `#bc17-vp`, `#bc17-bullets`, `#bc17-units`,
`#bc17-econ`, `#bc17-doctrines` with its dismiss control and body, and
`#bc17-fund` inside `#endcard` — the page's own DOM, element for element and
class for class, fed `renderVp` / `renderBullets` / `renderEcon` /
`renderUnits` / `renderDoctrines` / `renderEndcardExtras`'s own markup.

**Every number is measured**, not invented: the widest value each field
reached on any round of a six-board match between the league's two doctrine
poles (`Whirligig`, `GreenHouse`, `Interference`, `Chess`, `LineOfFire`,
`HouseDivided`, 3 000 rounds), read straight off the frames `broadcast.nim`
emits — bullets banked 15130.8, tree income 24.5, water 11368, chops 1196,
damage 1374.0, bullet worth 16365.1, and the rest. The words are
`plainWords17()`'s own output at both poles, widest and narrowest: 557
characters over eleven clauses against 471.

**THE ROW IMMEDIATELY FOUND A REAL DEFECT, which is the point of it.**
`#bc17-vp` and `#bc17-bullets` each carried `max-width: 96vw` **and**
`white-space: nowrap` on the container — a contradiction, because the cap
cannot be honoured without a break. At the measured widest the rows ran off
the right edge: `#bc17-vp` at 360 px (`price escapes the frame
[333,47,472,60] of [0,0,360,640]`) and at 720 px, and `#bc17-bullets` even at
**1280 px** (`off escapes the frame [1164,103,1409,116]`). The nowrap moves to
the children, so no number is broken in half, and the containers gain
`flex-wrap: wrap` / `justify-content: center`.

**Evidence.** Driven in a real headless Chromium against the page's own
extracted stylesheet, exactly as `ci.yml`'s step does. Before: three failures.
After: `bc17 @ 360px: ok`, `bc17 @ 720px: ok`, `bc17 @ 1280px: ok`, all thirty
rows ok, `data-replay-loaded=true`. And in CI on the branch:
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge),
0 ellipsized (--strict-text-bounds)` with the step green, which for this
fixture means every one of the ten years' three widths reported `ok` (the
parent sets `data-replay-error` on the first problem and never sets
`data-replay-loaded`).

The reviewer's honest caveat stands and is worth repeating for the judge: the
item's literal wording is "has no such fixture", and the repo does have one.
What it did not have was a bc17 row, and adding it found a defect at every
width.

## F3 — the endcard HUD-suppression rule keyed on a class nothing sets

**What it did.** `html[data-year="bc17"].endcard-open #bc17-*` could never
match: `grep -rn endcard-open` over the whole tree returned those four lines
and nothing else. The page toggles `$('endcard').classList.add('on')`
(`:7976`). `#endcard`'s background is
`radial-gradient(80% 70% at 50% 45%, rgba(16,11,7,0.82), rgba(9,6,3,0.95))` —
translucent — so with the rule dead all four bc17 boxes stayed visible
through the score screen. This is the bc16 r1-F1 defect returning verbatim.

**What it does now.** The sibling form,
`html[data-year="bc17"] #chrome:has(#endcard.on) #bc17-*`: parent-scoped,
direction-free (the boxes are emitted **before** `#endcard` inside `#chrome`,
so no sibling combinator could ever have matched) and keyed on the class that
exists. `#bc17-doctrines` joins the four, as bc16's and bc19's equivalents
include theirs. The block's comment claimed the opposite of what shipped
("`#endcard` is opaque over the board"); it now records the measured alpha.

**The gate is a computed style, not a text grep** — the review asked for
exactly this and the bc16 scar is why. F2's row adds
`SUPPRESSED_BY_ENDCARD.bc17`, so the fixture raises `#endcard` in a real
browser and reads `getComputedStyle(...).visibility` off all five boxes, then
lowers it and requires them back.

**Negative control run:** with the old `.endcard-open` selector put back into
the extracted stylesheet, all three widths go red with *"the endcard is up and
#bc17-vp, #bc17-bullets, #bc17-econ, #bc17-units, #bc17-doctrines is still
visible — the HUD bleeds through a score screen that is not opaque"*. A grep
could not see that and did not.

## F4 — `#bc17-fund` was computed every frame and never drawn

**What it did.** `broadcast.nim:2451` built the panel, `:2533` emitted it into
every frame, the page carried its CSS — and there was no `id="bc17-fund"` in
the markup and no reader, so no Fund ledger and no tiebreak ledger ever
reached a spectator. bc17 was the only year of ten without an endcard war
panel.

**What it does now.** Three parts, following the shape the other nine use:

* `bc17Fund` gains the **tiebreak ledger** — all four rungs with both sides'
  numbers. It carried the deciding rung's name and nothing to compare it
  against. Rung 4 is the highest **robot** id of any type, not the highest
  archon id the 1.6.2 spec claims (disagreement 2), computed the way
  `runLadder` computes it;
* `<div id="bc17-fund">` inside `#endcard`, after `#bc19-crusade` (bc17 is
  the tenth year and goes last), plus the `.clan` / `.ff` / `.ladder` /
  `.won` rules its siblings have;
* `renderEndcardExtras(s)`, called from `onFrame`: per faction the points
  bought **and what they cost** (donated bullets over points gained), the
  tree ledger, the unit ledger, damage dealt with **friendly fire and
  own-tree damage on their own line**, neutral trees felled and robots
  released, bullets left and their worth — then the ladder with the deciding
  rung marked. Every number goes through the block's own `stat()`, so endcard
  fix 3 (no raw unrounded floats) holds.

**Evidence.** Against the committed fixture's last frame, the emitted
`bc17_fund` now carries both ledgers and
`ladder: [more_victory_points 911 vs 723, more_bullet_trees 25 vs 17,
more_bullet_worth 16053 vs 8229, highest_id 13318 vs 14055]` with
`rung: more_victory_points`. And in a **real headless Chromium**, the bc17
block extracted from the page and handed a real frame filled `#bc17-fund`
with three children reading *"Clan Ash: 13 victory points for 97.5 bullets
(7.5 a point) / trees: … / units: … / damage dealt … / friendly fire … /
neutral trees felled … / bullets left …"* and the ladder.

`tests/test_viewer.nim`'s bc17 id list goes from five to six and — because a
panel nothing reads is a panel nobody sees, which is the whole finding — now
also asserts the reader exists and is called.

*(Note for a reader of the CI endcard capture: `viewer_smoke.mjs:531` slices
`endcard.text` at 400 characters, so the capture stops inside the doctrine
line and before the Fund panel. That is the instrument, not the panel.)*

## F5 — the doctrine card dropped the fallback badge and the disclosure

**What it did.** `doctrinesJson` puts `"fallback"` (`broadcast.nim:676`) and
`"submitted"`, the first 120 runes of the reply (`:683-684`), in every bc17
frame, and the inherited renderer at `:7288-7309` draws both. bc17's own
`renderDoctrines` drew neither. Checklist item 8's fallback has to be
**visible**: phase 60 counts fallbacks off the screen.

**What it does now.** The row is the shape the other nine use — `.dline`,
`.dname`, `.dfall`, `.dbadge`, `<i>notes</i>`, `.dsub` — with bc17's own
plain-words `<ul>` kept, because nothing about it was broken. The class names
are load-bearing and not cosmetic: `renderer_fixture.html` selects
`#<year>-doctrines .dline i` to prove the 280-rune note was laid out at its
cap, and bc25 shipped private names first and that check found nothing to
measure (the bc16 r1-F2 scar). `.badge` becomes `.dbadge` for the same reason,
and the knob count comes from the frame's own `knob_count` rather than a
hard-coded 11.

**Evidence.** In a real headless Chromium, against a real frame with a
`fallback` on seat 1 and a `submitted` on both:
`.dline` 2, `.dline i` 2, `.dfall` 1, `.dsub` 2, and the disclosure reads
*"what the cog actually sent: {"sheet":{"opening":"tree_farm"}}"*.

## F6 — nothing asserted the image has no java/javac/node/npm

**What it did.** `Dockerfile:7` says *"NO JDK, NO JRE, NO JAVA, NO NODE in any
stage"* and a comment is not a gate. `grep -n 'command -v' ci.yml` returned
nothing.

**What it does now.** One `docker-smoke` step, straight after `docker build`,
that asks the **built image** through its own `/bin/sh` what its PATH resolves
and fails the job naming every binary that answers. `command -v` and not
`which`: `which` is not installed in debian-slim, so a `which`-based probe
would report four absences from an image full of JVMs.

Two ways the probe could lie, both closed: `command -v` exits non-zero on the
PASS and `set -e` would kill the step, hence the `|| true` **inside** the
container command (while a failing `docker run` still fails the assignment);
and an image with no shell would report four absences and pass, so the step
ends by requiring the same probe to resolve `sh`.

**Evidence.** Verified locally by emulating the container call: against a
host PATH carrying a JDK and node it reports all four with their resolved
paths and exits 1; against a PATH without them it reports "absent from the
image's PATH". **And green in CI on the branch**, docker-smoke printing
`absent from the image's PATH: java / javac / node / npm`.

## F7 — `ci.yml` cited a RULES-BC17.md section that did not exist

`ci.yml:5256` and `:5519` both point at *(docs/RULES-BC17.md, "Playback
pacing, measured")* and `grep -n 'ms/round\|sim_seconds' docs/RULES-BC17.md`
returned nothing.

Written, with the measured value and the run that printed it: CI run
**34536659753**, `bc17 smoke: sim_seconds=0.113 rounds=899 wall=0.213s` —
**0.126 ms a round**, far inside the note's 15 ms/round trigger. The section
also records the trigger's own rule (lower `maxRounds`, never the soak), the
heavier boards `tests/test_bc17_perf.nim` measures (Chess 4.1 s / 1.4 ms a
round, LineOfFire 4.9 s against a 60 s gate), and why bc17 nevertheless takes
the heavy viewer probe: the per-round cost is small, the **2 999-round count**
is not, and the Worker re-simulates from the start of the game on every seek.

*(This round's own run re-measured it at `sim_seconds=0.111 rounds=899`, i.e.
0.123 ms/round — the recorded number is the one the cited run printed.)*

## F8 — three versus four `Math.random()` call sites

`grep -c 'Math.random' tools/oracle/bc17/examplefuncsplayer17/RobotPlayer.java`
is **4** and `determinism.patch` rewrites all four; `build_oracle.sh` asserts
the count of surviving global draws is zero, so three of four would leave the
bot irreproducible. `docs/PARITY.md` measured it and said so; RULES-BC17.md
said three.

RULES-BC17.md now says four, names the four sites (the archon's hire gate, the
gardener's two build gates and `randomDirection()`) and cites PARITY.md.
**Two other copies of the same wrong number went with it**, because the rule
this finding invokes is about consistency and a third document still saying
"three" would leave the divergence exactly as uncheckable:
`chassis/examplefuncsplayer17.nim`'s header and `world.nim`'s `weakRng` doc
comment. `NOTICE` avoids the number and is left alone. No behaviour changes.

## F9 — PARITY.md contradicted its own Status table

The bc17 metering paragraph ended *"That assertion belongs to the outstanding
job."* while the Status table three sections above reports Tier B′(a) as done
and measured and the job log carries the per-pair peak-bytecode column. The
standing rule from bc19: §Status is a verdict, never a to-do list. The
sentence now states the measurement it was deferring (every compared bot
asserts `Clock.getBytecodesLeft() > 5000`, peak **3 % of a limit** over 54
pairs) and says what actually stays out of reach — the metering's
*consequence*, not its measurement. Documentation only.

## F10 — six of the note's eleven smoke assertions had been dropped

**Fixed by restoring all eleven, and nothing had to be raised to make room.**

I re-measured the committed episode rather than guessing. A local replication
of the exact smoke config — seed 5, `HouseDivided`, 900 rounds, `orchard`
against `examplefuncsplayer17` — reproduces CI run 34536659753's own printed
line **bit for bit** (`planted=4 water=1323 shakes=20 chops=0 fired=1435
tree_income_tenths=20881 strikes=22`) and adds the six that were never
printed:

| restored assertion | measured |
|---|---|
| `victory_points >= 1` | **5** |
| `trees_mature_end >= 1` | **3** |
| `units_built >= 5` | **30** |
| `damage_dealt_tenths >= 10` | **7645** |
| `robot_ids_issued >= 6` | **34** |
| `peak_bullets_in_flight >= 2` | **6** |
| `SMOKE_REQUIRE_STATS` `"broadcasts": 1` (per seat) | **540 / 1652** |

Every one holds with room to spare, so every one is restored — including the
two the note puts in bold as never-droppable. `broadcasts` goes back because
the weak floor's archon broadcasts its x and its y **every turn** and
`orchard`'s comms layer broadcasts too.

The two floors phase 20 shipped **stronger** than the note asked stay
stronger: `water_actions >= 200` against the note's 5, and
`strike_actions >= 10`, which the note did not ask for at all.

**One measured line rather than a silent drop.** `chop_actions` measured
**0**, and the reason is the map, not the chassis: the smoke is pinned to
`HouseDivided`, whose robot-bearing trees sit outside the farm either seat
builds, and `chop_policy` defaults to `clear_path`, which chops only a tree
blocking a lane. It is not one of the note's eleven either; it is named in
`ci.yml` where a reader meets the printed zero.

**Budgets.** Back to the note's `perGameBudgetSeconds: 120` /
`matchBudgetSeconds: 130` from the 90 / 100 phase 20 shipped with no
measurement recorded. A budget is a rail and the episode simulates in 0.113 s,
so the headroom costs nothing. `maxRounds` is unchanged at 900 — the
authorisation to raise it was not needed.

**Evidence.** The whole step was run locally against a replay produced from
that exact config and exits 0. **And green in CI on the branch**, docker-smoke
printing `across the two seats: planted=4 water=1323 shakes=20 chops=0
fired=1435 tree_income_tenths=20881 strikes=22 vp=5 mature=3 built=30
damage_tenths=7645 ids=34 inflight=6` and
`episode substance OK: ['broadcasts', 'damage_dealt_tenths', 'moves',
'units_built']`.

## F11 — the TANK/SCOUT fall-through was covered nowhere

`tests/test_bc17_examplefuncsplayer17.nim` is **not** rebuilt, per the ruling:
Tier A″ proves the RNG stream differentially over nine whole 2 999-round
games, which is stronger evidence than a unit test. But the oracle cannot
reach one branch: the switch has no `case` for TANK or SCOUT, so `run()`
returns and *"If this method returns, the robot dies!"* — and no scaffold
game ever builds either type. The parity job's `types=` column never lists
them, and `build_oracle.sh` greps the Java copy for `RobotType.TANK` /
`RobotType.SCOUT` and **fails on a hit**, so the branch is unreachable from
any game by construction.

A block in `tests/test_bc17_baselines.nim` reaches it synthetically: spawn a
TANK and a SCOUT, hand each to `runExamplefuncsplayer17`, assert the robot is
off the board on its first turn, that the sim counted the loss, and that it
moved nowhere, fired nothing and broadcast nothing on the way. A SOLDIER — a
type the switch **does** handle — goes through the same call and survives, so
the assertion is about the fall-through and not about the harness.

**Negative control run:** with `of rtTank, rtScout: w.disintegrate(r)`
replaced by `discard`, four checks go red and name the type. The chassis
itself is untouched: it may not gain behaviour.

## F12 — NO CODE CHANGE (ruled)

Ruled honest relabelling, the bc16 r1-F3 precedent. The survival gate ships
its clauses at their measured values (friendly fire committed at 75 % against
the note's 15 %, **measured 54 %** — `selfHarm=50335/92413` in the test log),
each threshold is named with its measurement inline at
`tests/test_bc17_survival.nim:72-95`, and the `-d:bc17BrokenChassis` negative
control is verified live in CI (`BROKEN-CONTROL games=6 … failures=21 …
BROKEN-CONTROL: correctly red`), so the gate discriminates. Raising a floor
above a healthy measurement to match a note written before the measurement is
noise-fitting. Recorded here; nothing changed. It is also not a loosening
under checklist item 1: this is a **new** test file, so there was no prior
tolerance to widen.

Related and settled by the coordinator, cited here so the judge does not
re-open it: **checklist item 7**'s "tuned with a grid harness, not guessed" is
discharged by `tests/test_bc17_knobs.nim` — 244 lines, paired seeded games,
one knob at low and high, three seeds each, thresholds at ~half the measured
delta, and eight of the note's fourteen deltas honestly reported as not
reproducing. No second harness was built.

## F13 — NOTICE omitted the oracle trace driver and the six scenario bots

The engine section's "what derives from it" paragraph ended at
`tools/JavaBc17Tables.java`. `Bc17Trace.java` (714 lines) and `bc17idle`,
`bc17scenario`, `bc17scenariotree`, `bc17scenariokill`, `bc17scenariotie` and
`bc17slowbot` are all committed, all written against the engine's
`RobotController` API, all compiled by `build_oracle.sh`, and none was named.
The scaffold's `examplefuncsplayer17/RobotPlayer.java` — the seventh bot, and
the only one that is **not** ours — was already credited byte for byte with
its sha256; the paragraph now says which of the seven that is.

**Gated rather than asserted.** `tests/test_manifest.nim`'s licence-trail
block gains the bc17 pins and then **walks `tools/oracle/bc17`** and requires
a NOTICE mention for every `.java` file it finds, so a bot added later is
credited or the build is red. **Negative control run:** renaming the
`Bc17Trace.java` credit turns two checks red.

## F14 — NO CHANGE (ruled)

`game.docs` carrying `"type":"uri"` where the checklist writes `"type":"text"`
is **pre-existing across all ten docs pages** of a repo whose 0.9.0 coworld is
published and certified with exactly that shape, so the platform validates it.
The **structure** the checklist names (`readme` object with `type`+`value`;
`pages[]` of `{id,title,content:{type,value}}`) is exactly right; only the
discriminator string differs, and the bc17 page follows the house shape.
Rewriting it would edit nine sibling years' shipped docs to chase the
checklist's literal wording. Recorded as a known, deliberate divergence;
nothing changed.

## F15 — bc17 drew zero killfeed lines: ROOT CAUSE FOUND

**The cause.** `onText`'s guard is
`if (!isBc16 && !isBc17 && !isBc19 && … ) { … renderFeed(s); }`, so the
**inherited** `renderFeed` is skipped for every year that has its own block —
and all nine other year blocks carry their own (`bc20` `:4895`, `bc21`
`:5197`, `bc24` `:5531`, `bc25` `:5867`, `bc23` `:6154`, `bc16` `:6568`,
`bc19` `:6987`, `bc22` `:7354`, plus bc26's at `:7783`). **bc17's did not.**
`#killfeed` was therefore never written to on a bc17 replay, on any frame.
Not the spoiler gate and not a reveal rule: the beats exist and both doctrine
beats land on frame 0 (`tests/test_bc17_beats.nim:72`).

**The fix.** bc19's `renderFeed` shape, wired into `onFrame`: a **rebuild**
from the beats at or behind the playhead, tail of seven. A rebuild rather than
an append, so a backward seek takes lines away again, and spoiler-safe by
construction because a beat ahead of the playhead is never in the list.

**An assertion that would catch it again.** The wasm-viewer loop now reads
`feed_lines` out of `viewer-smoke.json`, prints it for every year and fails
the job if the bc17 replay draws none. The number was being recorded and read
by nobody, which is how a zero survived a green job. Gated on bc17 only,
because that is this round's scope.

**Evidence.** Locally, in a real headless Chromium: the bc17 block extracted
from the page and handed the committed fixture's first drawn frame filled
`#killfeed` with **six** children. In CI on the branch:
`bc17 … "feed_lines":7` and `killfeed lines at the first drawn frame: 7`,
against the reviewed run's `0`.

## Checklist item 13, last bullet — settled with evidence

The reviewer could not verify *"playback opens at the game start, never the
recorded lobby"*. No lobby was invented; both halves the brief owes are paid.

**(a) The code path, cited.** No pre-`gameStart` frame can be recorded, so the
first recorded frame **is** the game's opening round:

* `src/battlecode/replay.nim:270-276` — `newDeriver` enumerates frames
  `for r in 1 .. doc.gameRecord(index).rounds`, from **one**. There is no
  frame 0 of a game;
* `replay.nim:287-301` — `advance()` calls `session.stepRound()` **before** it
  reports, so the first frame is the state after round 1 has been played, and
  `years/dispatch.nim:547` makes `Session.currentRound` for bc17
  `w17.currentRound`, which `processBeginningOfRound` pre-increments;
* `src/battlecode/broadcast.nim:2513` — every bc17 frame emits `"lob": 0` and
  `"st": 0`, and `"ph"` is only ever `playing` or `gameover`, so
  `client/chrome_common.js:420`'s `s.ph === 'lobby'` branch is **unreachable
  from a recording**;
* `replay.nim:315-322` — `Deriver.seek` clamps to `[0, totalFrames - 1]`, so
  round 1 is the floor of every seek.

The checklist's suggested probe — a replay recorded with a large
`lobbyJoinTimeoutTicks` and no joining seats — does not apply to a runtime
with no join phase. There is no `gameStarts`, `gameStart` or `lobby` symbol
anywhere in `replay-viewer/`.

**(b) The assertion, in the viewer smoke.** `tools/ci/viewer_smoke.mjs` gains
`first_frame` (the `#tick-clock` / `#clock` readout taken at the load signal,
before the soak moves it) and a **rewind**: the scrub fractions become
`[0.5, 1.0, 0.0]`, so after the 100 % seek the scrubber is driven back to its
left edge and the landing round is recorded as `0%-rewind`. Every scrub entry
now carries `tick` as well as `clock`. `ci.yml` gates the bc17 replay on both:
the first drawn frame must read `round 1 / N`, and the rewind must land at or
after round 1 and no further in than `N/20 + 25`.

**Evidence.** Locally, against a synthetic viewer honouring the page's own
`#scrub` / `#tick-clock` contract: `first_frame.tick = "round 1 / 899"`,
`0%-rewind = "round 36 / 899"`, gate exits 0. **Three negative controls run**
against doctored JSON — an opening frame of `round 47`, a missing rewind
entry, and a rewind landing on `round 402` — all three exit 1 with the right
message. **And in CI on the branch:**
`first drawn frame: round 1 / 899   after a rewind seek: round 1 / 899`, with
the scrub line reading
`0%="0:22 …"  50%="0:18 …"  100%="FINAL MATCH OVER"  0%-rewind="0:37 …"` —
the seek came back from the end and clamped at the opening round.

---

## The evidence on `main`, in one place

Run **34557429247** (`ci.yml`, `main`, `526befd`, `run_attempt: 1`,
conclusion `success`, 13/13) printed, in the jobs the fixes land in:

* `docker-smoke` — `absent from the image's PATH: java` / `javac` / `node` /
  `npm` (F6); `episode substance OK: ['broadcasts', 'damage_dealt_tenths',
  'moves', 'units_built']` (F10's restored per-seat floor); and
  `across the two seats: planted=4 water=1323 shakes=20 chops=0 fired=1435
  tree_income_tenths=20881 strikes=22 vp=5 mature=3 built=30
  damage_tenths=7645 ids=34 inflight=6` (F10's restored across-the-pair
  floors, all eleven);
* `wasm-viewer` — for the bc17 replay,
  `first drawn frame: round 1 / 899   after a rewind seek: round 1 / 899`
  (checklist item 13) and `killfeed lines at the first drawn frame: 7`
  against the reviewed run's `feed_lines: 0` (F15); and the fixture step's
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge),
  0 ellipsized (--strict-text-bounds)` with all ten years' three widths
  reporting `ok` (F2, F3);
* `test` — `test_bc17_replay: ok (107 checks)` twice, debug and
  `-d:release` (F1); `test_bc17_baselines: ok (75 checks)` twice (F11);
  `test_viewer: ok (1224 checks)` twice (F2, F3, F4); `test_manifest: ok
  (1803 checks)` twice (F13).

## Retry budget

**Not used.** One CI round on the branch (34550806187) and one on `main`
(34557429247), both green on the first attempt. Everything that could be
driven locally was driven locally first — Nim 2.2.4 for every shard, a real
headless Chromium for the renderer fixture and the bc17 game block, a
bit-exact local replication of the docker-smoke episode for F10's floors, and
an emulated container call for F6's probe — and six negative controls were
run to prove the new gates can go red (F1's state digest, F2/F3's
computed-visibility check, F11's fall-through, F13's NOTICE walk, and three
against item 13's assertion).

## NOTED (not fixed)

Three things found while working that are **not** findings in this round's
review, left alone per the scope rule:

1. **`#bc17-doctrines-toggle` has CSS and JS but no element.**
   `client/replay_broadcast.html:4010` and `:4089` style it and the block
   binds `$('bc17-doctrines-toggle')` twice, but no `<button
   id="bc17-doctrines-toggle">` exists anywhere in the page — bc16's and
   bc19's are in the clock column at `:4460` and `:4463`. The JS guards with
   `if (chip)`, so nothing throws; the consequence is that once the bc17
   doctrine panel auto-hides (6 s, or the first frame that advances the
   playhead) **a viewer can never re-open it**. Same defect class as F3, on an
   absent element rather than a dead class. One line of markup would fix it.
2. **`renderer_fixture.html`'s `FILLED` map has no `bc19` key**, so for the
   bc19 row `document.querySelectorAll(undefined)` matches nothing and the
   "hides its own content" scan is vacuous for that year. Pre-existing,
   another year's run, untouched. (bc17's entry is present.)
3. **`viewer_smoke.mjs:531` slices `endcard.text` at 400 characters**, so the
   CI endcard capture stops inside the doctrine line and never shows a year's
   war panel. Not a defect in any year's chrome; worth knowing before anyone
   reads a capture as evidence that a panel is missing.

## Nothing read as an instruction

Everything read from the repo, the CI logs and the design note was treated as
data. No text encountered in any of them was addressed to me, and nothing was
acted on as an instruction.
