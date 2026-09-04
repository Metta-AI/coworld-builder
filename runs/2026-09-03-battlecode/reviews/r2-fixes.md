# r2 fixes — battlecode

Repo: `Metta-AI/cogame-battlecode`. Base: `cb37075` (main at review time; `45f4ead` was the released
0.1.5 tree, `cb37075` is its CI follow-up and the parent of this work).

**Head: `abc92ce3d7005eac6dc7bebae0e3b007033c0fd4`**
**CI: <https://github.com/Metta-AI/cogame-battlecode/actions/runs/33834906008> — conclusion `success`**

Three operator findings, sixteen commits, one logical change each. D2 is a series (eight behaviour
commits under one umbrella plus its gate) because it is eight separate defects with one symptom.

| finding | disposition | commit(s) | files |
|---|---|---|---|
| **D1** `chassis` is not an LLM knob | fixed | `96c0691` (+ `12ea9b8` version note) | `src/battlecode/sheet.nim:67`, `decide.nim:81`, `baselines.nim:24`, `replay.nim:176`, `sim_types.nim:16`, `docs/RULES.md:90`, `docs/PROTOCOL.md:63`, `tests/test_sheet.nim:119` |
| **D2** awu loses every king | fixed | `d2d19e5`, `9555d3a`, `de619f7`, `b33eb90`, `dbd93e2`, `5542ed6`, `83721b9`, `f77f450`, gate `219058c`, `abc92ce` | `src/battlecode/years/bc26/chassis/{king,rat,targets,formation,dirt,pathing,traps}.nim`, `tests/test_king_survival.nim` |
| **D3** the doctrine overlay covers the board | fixed | `2fb1aea`, `eef6684`, `2164ce6`, `dd6669f` | `client/replay_broadcast.html:2600,2935`, `tools/ci/viewer_smoke.mjs:443`, `tools/ci/renderer_fixture.html:183`, `.github/workflows/ci.yml:588`, `tests/test_viewer.nim:230` |

No test was weakened, skipped or deleted. Every test change is an added or strengthened assertion;
the three existing tests that had to move (`test_sheet`, `test_knob_sensitivity`, `test_viewer`) moved
because the surface they described changed, and each grew assertions rather than losing them. The
gates named in the brief are green **together** on the head above: the new D2 king-survival gate,
`test_knob_sensitivity` (15/15), `test_perf` (awu vs awu 2000 rounds in 4.1 s debug / 0.3 s release,
budget 45 s), `test_determinism`, `test_replay`, and parity Tiers A and B on all five pairs.

---

## D1 — `chassis` is off the LLM knob surface; every doctrine runs `awu`

**What the code did.** `chassis` was the first entry in `sheet.KnownKeys` and the first line of the
prompt preamble's THE KNOBS list, and `sheet.validate` read it into `doctrine.chassis`. A champion
that answered `{"chassis":"scaffold"}` was therefore *correctly* given the move-or-turn-only bot —
which is exactly what happened in round 1 (episode `a9a54765`): 0 rats, 0 traps, 0 cat damage, 0
cheese, three games, two wins.

**What it does now** (`96c0691`):

* `KnownKeys` has ten entries and no `chassis`; `validate` has no chassis branch at all. A reply that
  sends one takes the ordinary unknown-key path — recorded in `sheet_unknown_fields`, ignored, clan
  runs `awu` — and `decide.nim` logs the seat that tried:
  `battlecode llm: seat 1 sent `chassis`, which is not a doctrine knob: ignored, the clan runs the awu chassis`.
* The preamble's knob list is ten lines, and it says so in words: *"Your clan is driven by the `awu`
  chassis. That is not yours to choose: there is no `chassis` knob, and a reply that sends one has it
  ignored."*
* `scaffold` survives only on the filler path: `baselines.chassisFor` sets `doctrine.chassis`
  directly, so `PLAYER_SCRIPTED=scaffold` still plays the weak bot, and both scripted replies now
  carry only keys the LLM surface also has (`{"sheet":{}}`) — `test_baselines`'s "no unknown key,
  nothing repaired" check still holds for both baselines.
* The applied chassis still rides in the recorded sheet and `replay.parseSeat` restores it through
  the new `sheet.parseChassis`. Without that, a filler recording would re-derive on `awu` and every
  round of the viewer's hash chain would mismatch. `test_replay` and `test_determinism` cover it.
* **GameVersion GV03 → GV04** in the same commit (`sim_types.nim`), because the sheet a policy sees
  changed. `12ea9b8` extends the same GV04 entry to name the D2 chassis change that ships with it —
  one version, one rule set, one release.

**Evidence.** `tests/test_sheet.nim` block *"`chassis` is NOT a knob (r2-D1)"*: `chassis notin
KnownKeys`; `{"chassis":"scaffold","cat_engagement":"hunt"}` yields `doctrine.chassis == chAwu`,
`"chassis" in unknownFields`, `defaultsApplied.len == 0`, and `cat_engagement` still applied; the
preamble carries no `\n  chassis ` knob line. `test_sheet` 92 checks green; the whole `test` job green
in both debug and release.

---

## D2 — why the awu chassis lost its kings, and what changed

### The diagnosis, with the five questions answered

Measured with `awu`-default vs `awu`-default on the five parity maps at the reviewed sha, 2000 rounds,
instrumented per round (king hp, hp attributed to cat scratches from the event stream vs everything
else, bank, dirt in the king ring, nearest-cat distance, cheese on the map).

**The headline: they did not die to cats. They starved.** Every king that died lost **590 of its 600
hp to an empty bank** (`RatKingHealthLoss` 10/round) and between **0 and 140** to a cat:

```
DefaultSmall   king t1  cat 0    other 590     bank first empty r760
closeup        both     cat 0    other 590     bank first empty r1250   <- 0 cat damage by anyone
toomuchcheese  3x t0    cat 0    other 590     bank first empty r357
dirtfulcat     3x t1    cat 0/140/40 other 590/450/550   bank first empty r249
cheesefarm     (survived)                       bank never empty
```

That is the same signature the review saw on `mercifullattice` ("kings died with 0 cat damage dealt
by anyone").

1. **Is the `king_shell` dirt ring actually built, and when?** Partly, slowly, and never finished. On
   `DefaultSmall` the ring stood at 5/16 tiles at round 200 and 10/16 at round 1000; on
   `toomuchcheese` one king's ring went *down* (7/16 → 1/16) as cats dug through it. A ring with a
   gap is not a barrier. Worse, the shell had **no stopping condition**: a rat dug any dirt in reach
   whether or not the wall had anywhere to grow and kept the spoil, at `DigDirtCheeseCost` 5 from the
   same bank the kings eat from — on `closeup` the two clans dug 141 and 169 tiles (700–850 cheese,
   most of a game's income) and one starved at round 592 behind a wall it was still building.
2. **Do kings wander into cat vision cones?** No. `runKing` never moves; a crown sits where it is
   crowned. (A newly crowned king appears wherever four rats mustered, which is why the trap ring in
   `f77f450` is keyed on "a cat near *any* of my crowns", not on the starting one.)
3. **Does hunt/squeak behaviour pull cats toward the king?** **Yes, every single round.** The king
   squeaked the best cheese tile it could see on every turn, from a fixed 3×3 body; a cat in ATTACK
   turns to face the first squeak it hears (`cats.nim:162`, ported from `InternalRobot` at
   `engine.1.2.5`) and `SqueakRadiusSquared` is 16. The crown was a beacon walking cats onto itself.
4. **Is there retreat or re-shell when a cat is within N tiles?** There was **nothing** — no code path
   anywhere in the chassis read "a cat is near my king". Kings cannot retreat (3×3, `moveCd` 40), so
   the answer had to be defence, not flight.
5. **Do cat traps ring the king?** **No.** `traps.nim` placed a cat trap next to whatever cat a rat
   happened to see, wherever that was on the map. Nothing was ever laid between a cat and a crown.

And the two economic defects that actually did the killing:

6. **A buried king can never start.** On `closeup` both kings begin in a corner packed with the map's
   own dirt: every build tile is impassable, so the king spawns no rat, the clan earns nothing, and
   the arithmetic is exact — 2500 cheese ÷ 2 per round = 1250, plus 600 hp ÷ 10 = 60, dead at 1310.
   Observed: both kings dead at round 1310, 0 rats built, 0 cheese, 0 cat damage.
7. **The clan crowned courts it could not feed and never collected the map.** `king_count_target` was
   read as an order: `toomuchcheese` crowned its third king on round 35 off the opening bank, then
   burned 6 cheese/round against ~3 of income. Meanwhile miners only ever chased cheese already
   inside their 90° cone and the greedy two-sidestep `stepToward` could not cross a maze, so **2 900
   uncollected cheese sat on `DefaultSmall` at round 1000 and 12 630 on `closeup` at round 900** while
   every crown on both maps starved.

### The commits (each one logical change, all inside the `bc26` chassis)

| commit | change |
|---|---|
| `d2d19e5` | a buried king digs its own door — only while the clan is down to its last rat and the ring holds no free tile (a *crowded* ring is not a buried one; digging every time an own rat is in the way costs 5 cheese a turn and starves faster) |
| `9555d3a` | `king.famine` (bank under the crowns' starvation floor) suspends the `cheese_ferry_ratio` split: every rat mines |
| `de619f7` | `targets.nearestCheeseMine` + the brain's until-now-unused `knownMine`: miners find a mine, remember it, walk back to it and **camp** it, sweeping the cone instead of wandering |
| `b33eb90` | `formation.wantsMoreKings` also asks whether the clan can feed the enlarged court **to the end of the game**: bank + (achieved ferry rate × rounds remaining, discounted a quarter) ≥ burn + floor |
| `dbd93e2` | the dirt shell stops eating the crowns' food: no dirt work in famine, no digging while holding unplaceable spoil, no digging unless a wanted wall tile is open |
| `5542ed6` | rats path with the world's own `getBfsDir` (the cats' wall-aware BFS, cached per target, 25 credits) after greedy fails, and **dig through** dirt when every direction is blocked — the note's own "BFS pathing" line was the one distilled-awubot behaviour never written |
| `83721b9` | the king stops squeaking while a cat is inside `SqueakRadiusSquared` |
| `f77f450` | a rat that sees a cat within five tiles of one of its own crowns lays its cat trap **on the ring between the two** (100 damage + 20 stun for 10 cheese). Gated on `catsAreTargets()` so `cat_engagement: avoid` still lays none and still does zero cat damage |

The DecisionOps budgets are untouched (the BFS is charged 25 credits like any other primitive) and
nothing outside `years/bc26/chassis/` changed — `scaffold.nim`, `world.nim`, `cats.nim`, `rules.nim`
and both halves of the parity oracle are byte-identical, which is why Tier A and Tier B are green
unchanged.

### The gate, and its pre-fix numbers

`tests/test_king_survival.nim` (`219058c`): awu-default vs awu-default, the five parity maps, 2000
rounds. Two rules — **no game may lose a clan its last king before round 1500**, and **at least 4 of 5
must reach round 2000 or end on points**. The king count is read round by round rather than from
`end_reason`, because a *mutual* wipe records `round_limit`: `closeup` ended 1310/`round_limit` with
both clans dead, and a gate that trusted the label would have called it a pass.

**Pre-fix (`45f4ead`/`cb37075`, GV03): 8 of the gate's 11 checks fail.**

```
DefaultSmall   1012 rounds  kings_destroyed  clan 1 wiped at 1012          FAIL
closeup        1310 rounds  round_limit      BOTH clans wiped at 1310      FAIL
toomuchcheese   436 rounds  kings_destroyed  clan 0 wiped at 436           FAIL
cheesefarm      421 rounds  cats_cleared     both crowned                  pass
dirtfulcat      314 rounds  kings_destroyed  clan 1 wiped at 314           FAIL
                                             on points: 2 of 5             FAIL
```

**Post-fix, from the green CI run (job `test`, both debug and release):**

```
DefaultSmall   2000 rounds  round_limit   kings [1,2]  cat damage [680,800]   cheese [5815,8490]
closeup        1484 rounds  cats_cleared  kings [1,1]  cat damage [6440,1560] cheese [3580,2775]
toomuchcheese  2000 rounds  round_limit   kings [2,1]  cat damage [1210,2150] cheese [5320,4760]
cheesefarm     1902 rounds  cats_cleared  kings [1,1]  cat damage [4230,3770] cheese [4220,8305]
dirtfulcat      702 rounds  cats_cleared  kings [1,1]  cat damage [5610,2390] cheese [1270,1505]
test_king_survival: ok (11 checks)
```

All five keep both clans crowned; **no clan's bank ever empties on any of the five maps**, and the
worst cat damage any king takes is 20 hp (was 590 hp of starvation plus up to 140 of cat). Cheese
delivered on `DefaultSmall` went 3 535/2 240 → 5 815/8 490.

**The other gates, on the same head:** `test_knob_sensitivity: ok (15 checks)` — every knob still has
its teeth, including `cat_engagement avoid→hunt` (and `avoid` still does *exactly* zero cat damage,
which is what forced the trap ring to respect the knob), and the chassis pair, which is now built the
way the filler path builds it (`baselines.chassisFor`) since a doctrine can no longer select it.
`test_perf: ok` — awu vs awu, 2000 rounds on `DefaultMedium`, **4.121 s** debug / **0.323 s** release
against the 45 s budget. `parity-oracle: success` — Tier A bit-exact through round 50 and Tier B
through round 200 on all five pairs.

---

## D3 — the board is the picture again

**Why it persisted: nothing dismissed it.** `renderDoctrines` wrote `#doctrines` once, on the first
frame (`if (doctrinesRendered) return;`), and the panel had no header, no collapsed state, no timer,
no seek handler and no height cap. Not on play, not on a timer, not on a click — there was no
dismissal of any kind in the page. Its CSS is `max-width: 44%` anchored above the transport band with
unbounded height, so at the 360 px featured-match width two seats' `notes` at the 280-rune cap fill
most of the board region for the whole replay. That is what both screenshots show.

**What dismisses it now** (`2fb1aea`), in the page:

* **playback advancing** — the first frame where the playhead moves and `s.t > 0` closes it;
* **a 6 s timer** — for a viewer who never presses play;
* **its own header button** (`#doctrines-toggle`, a real `<button>` with `aria-expanded`) re-opens
  and re-closes it, and a panel the viewer opened by hand stays open;
* and the body is capped at `max(60u, 33vh − band)` with `overflow-y: auto`, so even opened, at full
  caps, at 360 px, it cannot own the board.

**How CI fails on it now**, so this cannot come back:

* `tools/ci/viewer_smoke.mjs` (`eef6684`) measures, at every readout and after the soak, the largest
  visible element covering the board canvas — absolutely placed, painting a background of its own at
  ≥ 20 % opacity, and carrying text, which is what a card/panel/curtain is and what the ambient
  `#lightpool` / `#grain` / `#chrome` layers are not — and records it as `obscured`.
* `.github/workflows/ci.yml`'s `wasm-viewer` job fails when that element holds **> 50 %** of the board
  while playback is advancing.
* `tools/ci/renderer_fixture.html` (`2164ce6`, corrected by `dd6669f`) — the one CI page that lays
  both seats out at their **full rune caps** in the page's own CSS at 360/720/1280 — now builds the
  panel exactly as the page builds it and fails if it takes more than half the frame height. This
  matters because every replay CI produces is *scripted*: its notes are eight-word strings, so the
  browser gate on the smoke replay alone would never see the size that did the damage.
* `tests/test_viewer.nim` pins the contract statically: the capped scrollable body, the `.closed`
  rule, the toggle button, and each of the three dismissals by name; plus that the harness records
  `obscured` and that `ci.yml` gates on it.

**Evidence from the green run** (job `wasm-viewer`, step *Load the bundle in a real browser*):

```
scrub selector: #scrub
largest overlay over the board after the soak: econ 2%
endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH
```

The three differing clock readouts and the "still advancing at the end of the soak" check are the
harness's own gates and passed unchanged (`clock: "0:07 GAME 1 OF 1 — TOOMUCHCHEESE"` at the first
readout, moving across the soak, `FINAL` at 100 %). The doctrine panel is no longer even the largest
thing over the board — `#econ`, the permanent economy readout, is, at 2 %.

One follow-up commit was needed here and it is mine: `2164ce6`'s fixture gate went red on its first CI
run (33833709379, `wasm-viewer`: `dline escapes the frame [16,569,158,739] of [0,0,360,640]`) because
content inside a *scrolling* box is laid out at full height and clipped by the box, so a child's rect
legitimately runs past the frame. `dd6669f` skips descendants of a scroller in the containment walk
and still measures the scroller itself. Fixed forward; the red run is on the record.

---

## NOTED (not fixed) — outside this round's findings

* `tools/ci/check_gameversion.sh` cannot read this repo's GameVersion at all: it greps `'"[0-9]*"'`
  out of the declaration and our versions are `GV04`, so it exits 1 with *"could not read
  GameVersion"* on any invocation. It is not wired into `ci.yml`, so nothing was masked, but the
  guard the design note inherits from coworld-ctf is inert here.
* `READOUT_SCRIPT` in `tools/ci/viewer_smoke.mjs` is a template literal, so the `\s` in the endcard
  text's `.replace(/\s+/g, " ")` is eaten before the browser sees it — the shipped regex is `/s+/g`
  and collapses runs of the letter *s* in the endcard readout instead of whitespace. Cosmetic in the
  log line only; my own probe avoids regexes for exactly this reason.
* `king_count_target` is now bounded by income on poor maps, which is correct but makes the knob's
  *visible* effect map-dependent: on the five parity maps a default clan settles at one or two crowns.
  If the league wants richer courts the lever is map choice or `StarvationReserve`, not the knob.
