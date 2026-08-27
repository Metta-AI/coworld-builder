# r1 fixes — rware-warehouse

Repo: `Metta-AI/cogame-rware-warehouse`
Head: `d5b5686ba4e97abfd1674d93e82814ed75232639` (main)
CI: https://github.com/Metta-AI/cogame-rware-warehouse/actions/runs/33081235780 — **success**
(jobs `test` ✓, `manifest` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; run created 14:15:32Z on
`d5b5686`, `--event push`).

Review: `runs/2026-08-27-rware-warehouse/reviews/r1-review.md` (F1–F23). Base was `d303e6c`.
One commit per finding, in F order. `git push` is refused for this sandbox helper
("No anonymous write access"), so the 23 commits were replayed onto `main` through the
`gh api` blobs→tree→commit→ref route, one API commit per local commit; each created tree's sha
was compared against the local tree's sha before the ref moved, so the pushed content is
byte-identical to what was tested locally.

**No test was weakened, skipped or deleted.** Every test change in this round adds a test or
tightens an existing one (`git log -p d303e6c..HEAD -- tests/` shows only additions plus the
one behavioural-consequence edit inside the new F17 test, which moves it from `forceActions`
to the real pilot loop — a strengthening).

| finding | disposition | commit | files |
|---|---|---|---|
| F1  | fixed | `c7052f8` | `src/rware/pilot.nim:192`, `tests/test_rware_pilot.nim` |
| F2  | fixed | `c4ce419` | `src/rware/llm.nim:246`, `src/rware/decide.nim:181`, `docs/PROTOCOL.md:103`, `tests/test_rware_engine.nim` |
| F3  | fixed | `4dd0143` | `src/rware/sim.nim:311`, `tests/test_rware_requests.nim`, `tests/replays/rware.replay` |
| F4  | documented, not changed | `4b8b82d` | `vendor/PATCHES.md` #12, `docs/PORTING-RWARE.md`, `src/rware/baselines.nim:127` (local rename only) |
| F5  | fixed | `9330d32` | `src/rware/baselines.nim:142`, `tests/test_rware_pilot.nim` |
| F6  | documented, not changed | `981d745` | `vendor/PATCHES.md` #13, `docs/PORTING-RWARE.md` |
| F7  | documented, not changed | `fa4ccfc` | `vendor/PATCHES.md` #14, `docs/PORTING-RWARE.md` |
| F8  | documented, not changed | `8b993c1` | `vendor/PATCHES.md` #15, `docs/PORTING-RWARE.md` |
| F9  | documented, not changed | `98f82bb` | `vendor/PATCHES.md` #16, `docs/PORTING-RWARE.md` |
| F10 | fixed | `a9403df` | `tools/ci/renderer_fixture.html`, `.github/workflows/ci.yml`, `tests/test_rware_viewer.nim` |
| F11 | documented, not changed | `9994d7c` | `vendor/PATCHES.md` #17, `docs/PORTING-RWARE.md` |
| F12 | documented, not changed | `ea61943` | `vendor/PATCHES.md` #18, `docs/PORTING-RWARE.md` |
| F13 | fixed (with a partial refutation, below) | `1cf37fc` | `src/rware/decide.nim:31,377,403`, `docs/PROTOCOL.md:163`, `tests/test_rware_engine.nim` |
| F14 | fixed | `4f8a79f` | `src/rware/decide.nim:268,341`, `src/rware/sim_config.nim:63`, `tests/test_rware_engine.nim` |
| F15 | fixed | `ba75dbb` | `src/rware/jam.nim:75,99`, `src/rware/sim.nim:345`, `src/rware/broadcast.nim:54`, `src/rware/replay_runtime.nim:152`, `tests/test_rware_sim.nim`, fixture |
| F16 | fixed | `d98ac65` | `src/rware/roster.nim:163`, `tests/test_rware_replay.nim` |
| F17 | fixed | `ae468ef` | `src/rware/pilot.nim:31,173`, `src/rware/warehouse.nim:275`, `src/rware/baselines.nim:31`, `tools/ci/baseline_tuning.json`, `vendor/PATCHES.md` #19, fixture, `tests/test_rware_pilot.nim` |
| F18 | fixed | `d05aea8` | `src/rware/sim.nim:25`, `tests/test_rware_pilot.nim` |
| F19 | documented, not changed | `bd3736c` | `vendor/PATCHES.md` #20, `docs/PORTING-RWARE.md`, `docs/RULES.md:101` |
| F20 | fixed | `751dc96` | `src/rware/sim_state.nim:74`, `src/rware/broadcast.nim:170`, `tests/test_rware_endcard_labels.nim` |
| F21 | fixed | `a954be4` | `tools/build_broadcast_page.py:7,24`, `client/page_script.js:600`, `client/replay_broadcast.html` (regenerated) |
| F22 | fixed | `2186a75` | `tests/test_rware_engine.nim:53` |
| F23 | fixed | `d5b5686` | `src/rware/decide.nim:260,354`, `tests/test_rware_engine.nim` |

Local verification for every commit: all 13 `tests/test_*.nim` run green in **both** debug and
`-d:release`, plus `tools/tune_baselines.nim --check`, `tools/extract_events.nim` and
`tools/expand_replay.nim` over the re-recorded fixture, `tools/build_broadcast_page.py`
reproduction against the read-only starter, `tools/ci/check_placeholders.sh`, and a native build
of both binaries and a `nim check` of the wasm entry. (A Nim 2.2.4 toolchain was installed in the
sandbox with the repo's own `nimby.lock`, so the whole `test` job ran locally before the push.)

---

## F1 — `hold` drove the robot to a park cell — **fixed** `c7052f8`

`chooseAction` routed `okHold` into the idle-park branch before the on-goal branch, so a robot
told to stand still rotated and drove to the nearest non-lane highway cell — the opposite of the
note (design.md:612), the shipped system prompt (`llm.nim:220`) and `docs/RULES.md:102`, and it
broke champion #2's jam-standoff protocol ("hold" + "holding, you go").

Now `hold` keeps its `orRunning` outcome, has no goal cell, and falls through to the no-goal
return as `NOOP`; only a **finished or refused** order parks. Evidence:
`tests/test_rware_pilot.nim` → "hold stands still, wherever the robot is standing" drives four
ticks from a storage cell and from the queue lane with the park cell elsewhere in both cases.
Checklist: correctness (no single item; item 7's legal-action assertions still pass).

## F2 — the ASCII floor plan was never sent — **fixed** `c4ce419`

`asciiMap` had no caller outside a test. `llm.floorPlanBlock` now renders the plan and
`decide.seatUserMessage` — the single proc that assembles a seat's user message, shared by
attempt 1 and the retry — prepends operator guidance, the plan, then the fogged view.

Deviation recorded rather than hidden: the note sends the plan *once at registration*; a provider
call carries no conversation state, so it rides in front of **every** request, byte-identical for
the whole episode. `docs/PROTOCOL.md:103` now says that instead of claiming the registration path
did something it did not do. Evidence: `tests/test_rware_engine.nim` → "the driver is handed the
floor plan" asserts the shipped assembly contains the plan, that every row is board-width in the
`#`/`.`/`W` vocabulary the system prompt uses, and that the retry message carries it too.
Checklist: correctness / legibility of the agent contract.

## F3 — the refill could re-draw the shelf just delivered — **fixed** `4dd0143`

Upstream (`warehouse.py:915-917`) computes `candidates` while the delivered shelf is still in the
queue; the port cleared the flag first, so the delivered shelf was in its own replacement pool.
Worse than a stream shift: the re-requested shelf was still standing on the pad on the robot's
forks, so the **next tick credited it again** — the recorded fixture delivered 12 where the
port's own rules allow 6.

The draw now happens before the flag is cleared. Evidence: `tests/test_rware_requests.nim` → "the
refill draws from upstream's candidate set" transcribes upstream's list and compares the drawn
shelf against it over 25 refills at three seeds; it fails on the old ordering (verified by
reverting `sim.nim` alone). `tests/replays/rware.replay` re-recorded — the recorded per-tick
hashes are a function of these rules. Checklist: item 2 (the fixture still re-derives frame by
frame; `wasm-viewer`'s "Headless wasm smoke" plays it with `rware_mismatch_tick` clean).

## F4 — `fetch` steers to the shelf's standing cell — **documented, not changed** `4b8b82d`

The behaviour is right and the finding is really "undocumented": a re-stowed shelf's home cell is
empty, so a home-cell `fetch` would report `shelf_gone` forever for a shelf the request board
keeps drawing. Recorded as `vendor/PATCHES.md` divergence 12 and mirrored in
`docs/PORTING-RWARE.md`. The only code change is the misleading local name the finding cites
(`let home = shelves[id].cell` → `standing`). Checklist: item 14-adjacent provenance/legibility.

## F5 — `fetch` tie-break was queue position — **fixed** `9330d32`

Aligned to the note (design.md:638, :652): both baselines now compare `(cost, shelf id)`, so the
tie-break no longer depends on the request RNG's draw order. Evidence:
`tests/test_rware_pilot.nim` → "an equal-cost fetch is broken by the lowest shelf id" (two shelves
one step either side of a robot, both baselines, both queue orders); fails on the old rule. The
tuning sweep was re-run as instructed: `tools/tune_baselines.nim --check` still passed with the
then-shipped pick (rank 7 of 27) at this commit; the pick moved later, under F17. The fixture is
unchanged by this commit — an exact BFS tie between two requested shelves does not occur in it.
Checklist: item 7 (the baseline's parameters remain sweep-derived, not guessed).

## F6 / F7 / F8 / F9 / F11 / F12 / F19 — undocumented deviations — **documented, not changed**

Each is consistent, deliberate behaviour whose defect was the missing record. `vendor/PATCHES.md`
now carries a second section, *"Divergences from the design note's viewer and packaging plan"*
(the entries above it are divergences from upstream), and `docs/PORTING-RWARE.md` mirrors it
entry for entry, as it did before.

- **F6** `981d745` — #13, the dropped `--preload-file data@data` / `-s FILESYSTEM=1`: nothing in
  the bundle reads a preloaded file (`Dockerfile.replay-viewer` copies assets next to the worker,
  `broadcast_core.js` fetches them), and the **bootstrap-critical** half of the flag set —
  non-modularized module + `Module.onRuntimeInitialized` — is untouched, which is the pairing
  checklist item 13 actually gates on.
- **F7** `fa4ccfc` — #14, speed chips `[1,2,4,8]`: the speed is an integer multiplier from
  `sim_types` through `jsIntArray` to the tick accumulator; `0.5` would put a float on the one
  path this port keeps integer-only. Default 1, so the note's playback arithmetic is unaffected.
- **F8** `8b993c1` — #15, `.tiny` at 640 px: **checklist item 11** says "labels hidden under
  `640px`", so 620 would leave 621–640 px as a band contradicting the checklist and the game
  block's own CSS comment. The `--hudscale` clamp beside it is still verbatim.
- **F9** `98f82bb` — #16, no `rig_art.nim`: the starter's compositor exists to feed the Bitworld
  sprite protocol; this game's wire is one JSON state object per frame over an integer grid. The
  outcome the note describes (96 chips, tinted crates, darkened tiled floor, same byte-for-byte
  assets) is produced in `broadcast_core.js` at load, in the one file both delivery modes run.
- **F11** `9994d7c` — #17, the dropped `kill` forbidden word: `#killfeed` is an id the note keeps,
  so a literal `kill` gate cannot be zero; the thing the word guarded (`.beat-marker.kill`) is
  enforced positively by `REMOVED_SELECTORS` and the beat-CSS set assertion.
- **F12** `ea61943` — #18, `game.docs` inline `text`: this matches **checklist item 10** exactly,
  which is the gate a release is judged on; the note's `uri` form is the older shape and the
  platform validator accepts either. Said so in the entry.
- **F19** `bd3736c` — #20, `yield`'s own-cell and queue-lane exclusions, with the reasons (a
  self-yield is a length-1 cycle and unblocks nobody; backing into the queue lane moves the
  standoff onto the one lane every delivery needs). `docs/RULES.md`'s order table now states the
  own-cell exclusion too.

## F10 — `canvas_text` total 0 — **fixed** `a9403df`

The honest fix, not a note: `tools/ci/renderer_fixture.html` now also drives the **shipped**
`client/broadcast_core.js` — the same file the Worker runs — against a plain main-thread canvas
with the same worst-case frame at 360/620/630/1024 px, so the two `fillText` sites on the board
(the `W1`/`W2` pad labels and the requested-shelf ids) are drawn where `viewer_smoke.mjs`'s hook
can measure them. The fixture fails outright if that renderer drew no strings, so `total: 0`
cannot come back silently. `viewer_smoke.mjs` itself is untouched (still byte-identical to the
builder template), and `ci.yml` now says at the bundle step why *its* number is 0 (OffscreenCanvas
in a Worker) and which step carries the gate.

Evidence, CI run 33081235780, job `wasm-viewer`:
- `Worst-case renderer fixture (full-cap commander lines)` →
  `canvas text: 29 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
- `Load the bundle in a real browser` → still `canvas text: 0 drawn, …`, now documented in
  `ci.yml` as expected for a Worker-rendered board.
`tests/test_rware_viewer.nim` → "the renderer fixture measures the board's own canvas text" pins
the wiring from the tree. Checklist: item 15.

## F13 — `throttled` outside the closed enum — **fixed**, with a partial refutation `1cf37fc`

Fixed as instructed: the enum is closed again. A provider 429 is reported as `transport_error`
(the 429 text is already in the record's `detail`, and the log still carries "provider throttled
with no other candidate"), and the seven causes are named once as `decide.FallbackCauses`.

Partial refutation of the finding's framing: the deviation was **not** undocumented —
`docs/PROTOCOL.md:163-171` listed `throttled` in its cause table and explicitly called it "a
divergence from the design note's enum". I still closed the enum, because the note is
authoritative here and a reader switching on the note's seven values gets a silently unhandled
branch otherwise; `docs/PROTOCOL.md` was updated to match. Evidence:
`tests/test_rware_engine.nim` → "every fallback cause is in the note's closed enum" pins the list,
greps the decision layer for a surviving `"throttled"` literal, and asserts every cause a real
episode writes is one of the seven. Checklist: item 8.

## F14 — the spacing sleep ate the retry window — **fixed** `4f8a79f`

`turnStart` is now taken at the **batch start**, after the `turnSpacingMs` floor — that sleep is
time deliberately spent *not* calling the provider, and counting it against the budget spent
8–9 s of 14 s waiting and then wrote off a timed-out attempt 1 with "per-turn budget exhausted
before attempt 2", i.e. no retry, which is exactly what checklist item 8 requires.
`sim_config.clampConfig` now repairs any non-zero `turnBudgetMs` up to `attempt1Ms + retryMs`, so
the ladder cannot be configured out of the budget.

Every bound stays explicit and the worst case is unchanged: a turn costs at most
`max(turnSpacingMs, turnBudgetMs) = 14 s`, 25 turns = **350 s** — the note's own figure
(design.md:361) — inside the 660 s engine stop, the 680 s stop+grace and the 720 s target.
Evidence: `tests/test_rware_engine.nim` → "the retry always fits inside the turn budget" asserts
the ladder fits for the shipped defaults, for **every** manifest variant and for the certification
fixture, that a too-small budget is repaired upward, and that each LLM-bearing variant's 25-turn
worst case lands inside its own `wallClockBudgetSeconds`. Checklist: items 5 and 8.

## F15 — jam detector reported only the largest group — **fixed** `ba75dbb`

`detectJam` now unions **every** linked group of ≥ 2, ascending — the note's "set of robots …
closed transitively". And a membership change no longer re-raises `started` with no `jamclear`
between: it closes the running jam (count, span, `clearedTicks`) and opens a new one on the same
tick, with `stepEvents` and the beat scan emitting clear-then-start so the pair reads
`jam → jamclear → jam`. Evidence: `tests/test_rware_sim.nim` → "two disjoint standoffs are one
jam, and a change of members clears" drives four robots into two disjoint standoffs (one jam set
of four), then asserts clear+start when one pair turns away, then a plain clear. Fixture
re-recorded — jam members are hashed. Checklist: item 2 (hash chain), correctness.

## F16 — playback counted fallback turns differently — **fixed** `d98ac65`

Playback counted `fallback` records with `attempt == 2`: that double-counted a seat which failed
both attempts (two attempt-2 records) and missed a seat that never got to call at all (one
attempt-1 `budget_guard`/`rate_guard`/`no_credentials` record). Both counters now come from the
`directive` record's `source`, written once per seat per turn with the directive that was actually
installed — the same field and the same rule as `episode.nim`. No schema change; the field was
already there and is non-hashed. Evidence: `tests/test_rware_replay.nim` → "the re-derived
per-turn counters equal the recorded ones" (two credential-less LLM seats, all four seats
compared); fails on the old rule. Checklist: item 2.

## F17 — a credited `deliver` squatted the workstation — **fixed** `ae468ef`

A `deliver` whose carried shelf has left the request board, and which has either reached the pad
or already been credited (`lastResult == done`), is now **finished**, so the robot parks like any
other idle robot — on that tick and on every later one, not only while it stands on the goal cell.

`parkCell` had to become path-aware for that to be an improvement rather than a lateral move: it
ranked candidates by straight-line distance, which picks a *different* cell from each cell along
the way, so a robot leaving a workstation chased a target that moved with it and walked the whole
queue lane instead of stepping out of it (traced tick by tick before the change). It now ranks by
one BFS distance field over the robot's believed grid (`warehouse.bfsDistanceField`), ties by
lowest cell index as before.

Two re-derived consequences, both recorded rather than asserted:
- the fixture goes from 6 delivered to **23**, and the CI docker-smoke replay from
  `DELIVERED 12 … TICK 289` (run 33074159923) to `DELIVERED 13 … TICK 279` (run 33081235780);
- the sweep's pick moves: `yieldAfter` 6 → 4, **1st of 27** at the tool's horizon
  (`tools/tune_baselines.nim --check`), `penalty` and `stowClearance` unchanged.
  `tools/ci/baseline_tuning.json`, `DefaultBaselineParams` and `vendor/PATCHES.md` divergence 19
  carry that, with the note's own mechanism quoted: the tunables come from the sweep, and CI
  re-runs the sweep precisely so a controller change that invalidates the pick is red here.

Evidence: `tests/test_rware_pilot.nim` → "a credited deliver finishes and gets off the pad"
asserts `running` before the credit, `done` after it, and that the pilot leaves the pad and stays
on a non-lane park cell. Checklist: items 5/7 (throughput and legal play), correctness.

## F18 — turn 1's default was `hold` — **fixed** `d05aea8`

`applyOrders`'s no-previous-order branch now takes `courteousDirective`'s order — the same proc
the fallback uses, imported not copied — so the ladder is the note's: this turn's, else last
turn's, else courteous's. Evidence: `tests/test_rware_pilot.nim` → "turn 1's default order is
courteous's, not hold" for every seat, and a say-only reply on a later turn still keeps the
standing order. Checklist: item 8.

## F20 — endcard "TEAM SCORE" was seat 0's score — **fixed** `751dc96`

The score formula's first term is identical for all four seats and *is* the team's score, so the
endcard headlines exactly that (`sim.teamScore()`, the shared term named once and reused by
`scoreOf`). Per-seat deliveries are already in the endcard rows; `results.scores` is per seat and
unchanged, so the league is unaffected. Evidence: `tests/test_rware_endcard_labels.nim` → "TEAM
SCORE is the team's score" asserts `scoreOf(seat) == teamScore() + delivered[seat]` and that the
rendered endcard carries the team number. Checklist: legibility.

## F21 — stale MAGENT-BATTLE / 45x45 text — **fixed** `a954be4`

Fixed in `tools/build_broadcast_page.py` (docstring + the `REMOVED_SELECTORS` justification, now
"a fixed 10x11 / 16x11 grid that relayout() fits whole") and in `client/page_script.js`.
`client/replay_broadcast.html` was **regenerated** by that script from the read-only starter, so
the committed page still reproduces byte for byte (`diff` clean against the rebuild, marker count
1). Checklist: item 14 (provenance legibility).

## F22 — test 22's missing half — **fixed** `2186a75`

Added the "connects then never answers" case: a seat that joins, registers as an LLM seat and
never produces a usable reply for the whole episode. It asserts `complete` at the tick cap, that
the seat is **not** a dead seat and no failure payload is declared for it, `fallbackTurns[0] ==
turnsPlayed` with `llmTurns[0] == 0`, that its robot was actuated (it moved, stowed or delivered),
and that the replay carries one enum-legal `fallback` record per turn saying why. The
never-connects half is unchanged. Checklist: items 5 and 7.

## F23 — the rate guard skipped the retry batch — **fixed** `d5b5686`

`rateRoom()` names the rolling-60 s arithmetic once and **both** batches consult it; a seat with
no room skips the retry and takes the courteous order with `cause = "rate_guard"`, exactly as a
seat skipped at attempt 1 does. Still no sleep on the critical path. Evidence:
`tests/test_rware_engine.nim` → "the rate guard bounds every batch, not just the first" exercises
the window at the limit, over it, and with stamps aged out, and asserts both batches consult it.
Checklist: item 5.

---

## NOTED (not fixed)

- **`GameVersion` is still `"1"`.** F3, F5, F15, F17 and F18 change the rules a replay
  re-simulates under, and GV1's changelog line says "Obsoletes nothing". No GV1 replay exists
  outside this repo (the committed fixture was re-recorded in the same commits, and nothing has
  been released), and `tools/ci/check_gameversion.sh` only guards cross-branch collisions, so
  nothing is broken today. If any GV1 replay is ever published before release, the number should
  be bumped with a prepended changelog line.
- **`docs/plans/2026-08-27-rware-warehouse-design.md`** (the repo's copy of the design note) still
  quotes `yieldAfter = 6` and the pre-fix numbers. I did not edit the note; `vendor/PATCHES.md`
  divergence 19 records the re-sweep and why.
- **`pilot.nim`'s `of okHold: discard`** in the on-goal branch is now unreachable (a `hold` has no
  goal cell). Kept only because Nim wants the case exhaustive.
- **The certification fixture's 240 s `wallClockBudgetSeconds`** is smaller than 25 turns of the
  14 s worst case; it is fine because that fixture runs with no API key (every seat scripted, no
  LLM wait) and the budget guard settles it early, which "budget guard settles early, still
  complete" asserts. The new timing test therefore checks the 25-turn worst case for the shipped
  variants and the ≤ 660 s cap for all three, and says why in the test.
