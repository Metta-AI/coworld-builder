# r1 fixes — battlecode-2020-soup (the `bc20` year module)

Repo `Metta-AI/cogame-battlecode`. Branch `claude/r1-fixes-bc20-sthr01VF1z7e1XozHUMAxbVXVKVV`,
branched from `main` at `551c5427e3b88deedfc7155c41a18f193c0ff6c9` (main had not moved),
merged to `main` as PR [#2](https://github.com/Metta-AI/cogame-battlecode/pull/2).

Fifteen findings, one commit each, in the review's own numbering. Five are **code** defects,
three are **test** defects, seven are **documentation**: the code was right for the game and the
design note was not, so the divergence is declared where the note's other divergences live
(`docs/RULES-BC20.md` §Divergences, `docs/PROTOCOL.md`, `docs/REPLAY.md`) rather than the code
being made worse to match prose. One extra commit fixes a defect found while verifying F13.

| finding | disposition | commit | what changed | checklist item protected |
|---|---|---|---|---|
| F1 | fixed | `3bee5ee` | `tools/ci/renderer_fixture.html:336` measured `#doctrines` on every row; under `data-year="bc20"` that element is `display:none`, so the "the panel may not take half the frame" rule passed on a 0×0 rect. Now measures the year-aware `probe`. | **15** (every drawn string fits its frame) |
| F2 | fixed | `d12f35a` | `drone_water_drop` carried no victim team, so `match.nim:131` named `1 - e.b` — the other clan — even for a friendly or cow drop. The event now carries the dropped unit's team ordinal and `victim_alias` is that clan, or `neutral`. Test added. | advisory (feed/beat legibility) |
| F3 | DOCUMENTED | `d046fc1` | The observation carries no `rules_digest`/`sheet_schema`. Both contents ship in `Bc20Preamble`, recorded once as `prompt_preamble`. `docs/PROTOCOL.md` §The bc20 observation now says so and names the field a consumer should read. | advisory |
| F4 | DOCUMENTED | `0fd26fb` | `flood_table["7"]` is the sentinel `WaterTableMaxRound + 1 = 1501`, not the note's 1546. `docs/PROTOCOL.md` carries both numbers, which one the payload reports and why; `floodTableJson`'s doc comment points at it. | advisory |
| F5 | fixed | `9f7e6b1` | `decide.nim:315` logged "the clan runs the awu chassis" on bc20 too. Now prints `chassisNameFor(config.year, seats[slot], sheet)`. | advisory (operator legibility) |
| F6 | DOCUMENTED | `98670d6` | The builder-miner's Refinery-second order and its Chebyshev-2 net guns are now §Divergences item 16, each with the rule that forces it; `miner.nim`'s header lists the Refinery it actually builds. | advisory |
| F7 | DOCUMENTED | `3224c51` | `fulfillment.nim`'s header claimed a `NEED_DRONES` branch that does not exist and could not fire (nothing broadcasts the code). Header corrected, `SigNeedDrones` marked RESERVED with why its code point is kept, §Divergences item 15. | advisory |
| F8 | fixed | `925ef4f` | `tests/test_bc20_replay.nim`'s "record → re-derive covered every end reason" was satisfied by three string literals and by an unconditional `abandoned` add outside a branch that **never fires**. Rewritten: two lists, real ladder vectors, and a deterministic end-to-end abandoned round trip. 45 → 67 checks. | **2** (replay re-derivation) |
| F9 | fixed | `3920551` | `opening` and `rush_trigger` now gate on the design note's own statistics (enemy-half arrival delta; adjacency by round 350) as well as the arrival counter. 14 → 16 checks. | **7** (baseline tuned, not guessed) |
| F10 | DOCUMENTED + test | `83f5cd5` | Move-into-water destroys the mover. §Divergences item 17 with the upstream citation at `7618f6b`, and `tests/test_bc20_flood.nim` now pins the path the oracle cannot reach. 26 → 32 checks. | advisory |
| F11 | fixed | `e18ad4f` | Three stale pointers corrected (in the constants **generator**, so `--check` still byte-matches), and `tools/ci/check_gameversion.sh` wired into `ci.yml` for the first time. The fourth (GV04 → GV05 in the knobs header) landed in `3920551`. | advisory |
| F12 | fixed | `e9a044b` | `SeatPolicy.baseline` deleted — one write, no reads. | advisory |
| F13 | fixed | `c7e2e5f` | `tests/fixtures/replay-bc20.json` (5 881 bytes, 119 rounds) plus `tools/gen_bc20_fixture_replay.nim` that records it, a native re-derivation test, and a third `wasm_replay_smoke.cjs` target. | **13** (viewer executes) |
| F13 follow-up | fixed | `4121a21` | The node wasm smoke had **never run**: `require()` shadows `global.Module`, so the glue built its own and `onRuntimeInitialized` was never called — 0.1 s, no output, exit 0, on every run including main's. Loaded through `vm.runInThisContext` now, with a watchdog. | **13** |
| F14 | DOCUMENTED | `3a897cf` | `first_build.unit` is the engine's own `RobotType` names (hence `delivery_drone`), and the chassis really does build miners and a refinery. `docs/REPLAY.md` lists the eight reachable values and why. | advisory |
| F15 | DOCUMENTED | build-report addendum | "byte-identical to `main`'s" is decoded-identical: the manifest was re-serialised with non-ASCII escaping off. Corrected in the build report; **no repo change** — see below. | advisory |

Final main sha: **`e07412ab960d5bb7b05d7b8f9015c6c16f339769`**.
Green CI on main: run **33847918283** —
<https://github.com/Metta-AI/cogame-battlecode/actions/runs/33847918283>, conclusion **success**
(`test`, `parity-oracle`, `parity-oracle-bc20`, `docker-smoke`, `wasm-viewer`).
Branch/PR CI green first: **33846271859** (`3a897cf0`, success) and **33847092207**
(`4121a21e`, success). Every run matched by `headSha`.

**No test was weakened, skipped, deleted or loosened; four shards gained assertions
(drone 26 → 33, flood 26 → 32, knobs 14 → 16, replay 45 → 67) and no other shard's count moved.**

---

## F1 — the fixture's bc20 rows measured a hidden panel

`renderer_fixture.html`'s verdict already computes `probe = year === 'bc20' ? 'bc20-doctrines' :
'doctrines'` for its CSS-loaded check, then line 336 threw that away and read `'doctrines'`
unconditionally. Under `data-year="bc20"` the inherited panel is
`display: none !important` (`client/replay_broadcast.html:2653-2656`), so `getBoundingClientRect()`
is 0×0 and `panel.height > frame.height * 0.5` is false for free on all three bc20 rows.

Evidence, run in the sandbox against the page's own extracted CSS with the threshold temporarily
forced to `0.0`: **three** `the doctrine panel takes N%` errors before the change (the bc26 rows
only), **six** after — the bc20 rows report 20 %, 17 % and 18 % of their frames. At the shipped
0.5 threshold the fixture is green, and its `canvas_text` line is unchanged
(`0 drawn, 0 never inside`, which for this page is correct: every LLM-authored string is DOM text).

## F2 — the victim was assumed to be the enemy

`dropUnit`/`dropHeldUnit` emit for **any** unit dropped onto a flooded tile. The emit now carries
`$ord(dropped.team)`, and `match.nim` maps `0`/`1` to the clan alias and anything else to
`neutral`. `tests/test_bc20_drone.nim` gains a friendly-landscaper drop and a cow drop and asserts
the victim team on the existing enemy case. The stat counter is untouched — it counts every unit
that is not the drone's own, which the new test now states explicitly rather than leaving implied.

## F3 — `rules_digest` / `sheet_schema`

Refuted as a defect, documented as a layout difference. Both contents reach every seat in the
system preamble (`decide.nim:122-180`), which the replay records once at document level. Putting
them in `seats[].prompt` as well would write the ~7 KB digest and the whole knob table twice into
every replay for no new information. `docs/PROTOCOL.md` now names both keys, says where they live
and tells a consumer to read `prompt_preamble`.

## F4 — `flood_table["7"]`

1501 is `roundWaterReaches`'s "never inside the table" sentinel; the committed water table is
rounds 0…1500 and is regenerated and **byte-diffed against the JDK generator as a blocking CI
step**, so recording 1546 would mean generating water levels for rounds the sim cannot play.
Both numbers are now in `docs/PROTOCOL.md` with which one the payload carries and why; levels 1–6
remain pinned by `tests/test_bc20_flood.nim`.

## F5 — the chassis log line

One expression. `chassisNameFor` is the same resolution `server.nim:387` records on the seat, so
the log line and the replay now agree. The D1 behaviour (record, never honour) is unchanged and
still asserted by `tests/test_bc20_sheet.nim:171-187`.

## F6 — the build order

Two divergences, both forced by rules the note's order fights: a walled HQ is eight elevation steps
above the ground outside its ring against `MAX_DIRT_DIFFERENCE = 3`, so the economy stops at the
moment the wall succeeds unless a second drop-off exists; and dirt dropped on a building buries it,
so the HQ ring — the tiles the landscapers raise — is the one place a net gun may not stand.
§Divergences item 16, and `miner.nim`'s own header now lists the Refinery.

## F7 — `NEED_DRONES`

The branch cannot be written honestly: no role broadcasts `SigNeedDrones`, so it would guard a
signal that never arrives, and inventing a broadcaster is a play change (it would move the D2 gate
and the drone knob's teeth), not a comment fix. The code point stays — renumbering the signal table
would change the meaning of every message in every recorded match — and is marked RESERVED.
§Divergences item 15.

## F8 — the coverage loop

The reviewer was right and the problem is worse than reported: **the deadline branch never fires
at all.** Measured in the sandbox, a full 1499-round `CentralSoup` game re-derives in **268 ms** in
release and 2.3 s in debug, so a one-second guard cannot trip and the unconditional
`seenReasons.add("abandoned")` was the only reason the loop passed.

Now:
* `reDerived` and `ladderVector` are separate lists and the loop names which one each reason must
  be in, so a reason nobody produced cannot satisfy it;
* `broadcasts`, `highest_id` and `coin_flip` are real vectors through the same `checkEndOfMatch` a
  played game calls, on a bare world (the committed maps arrive with their own HQs and cows, which
  is why the last rungs need one);
* `abandoned` is end-to-end and deterministic. The recorder's own guard is made to fire by holding
  the clock in `playGame`'s round callback — the real code path, `budgetSeconds` and all, not a
  mock — the stop round is written as `plan.abandon_after[0]` with no `GameHeader`, the document is
  re-derived **from the written bytes**, and the deriver's hash chain at the stop round is compared
  against the recorder's own `roundChains` entry. That comparison is the only thing that can prove
  the two agree for an abandoned game, and it did not exist before.

The abandoned block's previous assertions are all still made (game discarded, stop round recorded,
playback stops there) — unconditionally now instead of inside an `if` that never ran.

## F9 — the two proxy gates

Both of the note's statistics turned out to be measurable, so they are measured rather than
declared. `runSet` records, per game, the round a friendly unit first stood closer to the enemy HQ
than to its own (the round cap standing in for "never crossed"), and whether one stood adjacent to
the enemy HQ by round 350.

* `opening` turtle → rush: enemy-half arrival 1811 → 878 summed over the four games, i.e. **233
  rounds earlier per game**; gated at 100 a game, the same half-the-measured-delta rule the other
  nine thresholds follow. The note asks 200; gating at the note's own number leaves 14 % of margin,
  which is a flake, not a gate.
* `rush_trigger` 0 → 220: adjacent to the enemy HQ **by round 350** in 0 of 4 games at `0` and 1 of
  4 at `220` — the note's clause verbatim.

Both original counters are kept. The header table records both new measurements.

## F10 — move into water

Not a divergence from the engine; a divergence from the note's prose. Verified against the pinned
upstream at `7618f6b`, quoted in the code and in §Divergences item 17:
`RobotControllerImpl.assertCanMove` (`:344-365`) tests type, adjacency, bounds, occupancy,
`MAX_DIRT_DIFFERENCE` and readiness and **never mentions flooding**; `move` (`:382-391`) tests it
afterwards and calls `disintegrate()`, which throws `RobotDeathException` (`:937-939`);
`GameWorld.updateRobot` (`:190-191`) destroys the robot. The port destroys it at the flood test
instead of at the end of the same turn, which nothing can observe because no other body acts in
between. `tests/test_bc20_flood.nim` now pins it: `canMove` says yes, the miner dies, neither tile
holds it, and a drone flies onto the same tile and lives.

## F11 — the stale pointers and the unused script

`constants.nim` is generated, so its header was fixed in `tools/gen_year_constants.py` and the file
regenerated against the pinned sources; `--check` still matches byte for byte (verified locally
against a fresh checkout of `battlecode20@7618f6b`). `check_gameversion.sh` now runs in the `test`
job on every non-`main` ref against a depth-1 fetch of `origin/main`. It ran green on both PR runs:
`base (FETCH_HEAD) = GV05 … head (HEAD) = GV05 … OK: GV05 unchanged from the base — no rule change
claimed`.

## F12 — `SeatPolicy.baseline`

Deleted, with its one write and its one mention in a test constructor. The `scripted` field's doc
comment now says where resolution happens and why it is not done at registration: a parsed
`Baseline` on a seat is a bc26 answer to a question that has not been asked yet.

## F13 — the committed fixture, and the smoke that never ran

The fixture earns its keep: 5 881 bytes, 119 rounds, byte-identical on a re-run, a real recording
written by the same `ReplayDoc.toJson` the server writes, and its generator refuses to write a
recording that does not re-derive. `tests/test_bc20_replay.nim` proves the committed bytes still
parse, carry a `GameVersion` in `ReplayCompatibleGameVersions`, and re-derive round for round under
the current sim — with the re-record command in the assertion's own message, because a rule change
*should* turn this red.

Verifying it exposed a second defect, fixed in `4121a21`: **`tools/wasm_replay_smoke.cjs` had never
executed a single wasm frame.** The emitted glue opens with
`var Module = typeof Module != "undefined" ? Module : {}`; under `require()` that `var` is hoisted
into the module scope and shadows `global.Module`, so the glue builds its own empty Module,
`onRuntimeInitialized` is never called, node runs out of work and exits 0. The step took 0.1 s and
printed nothing on every run, including main's green `33841592052` — the pre-existing evidence for
that step was worth exactly as much as an `outside: 0` on an empty canvas. Loading the same bytes
through `vm.runInThisContext` (plus a 60 s watchdog that exits 1 rather than exiting 0 in silence)
makes it real. CI run **33847918283 on `main`**, job `wasm-viewer`, step "Smoke the emitted wasm
module under node", now prints three lines where it used to print none:

```
runtime initialized; loading replay.json
{"loaded":true,"game_version":"GV05",…,"first_packet_bytes":74797,"frames":200,"mismatch_round":-1}
runtime initialized; loading replay-bc20.json
{"loaded":true,"game_version":"GV05",…,"first_packet_bytes":71039,"frames":200,"mismatch_round":-1}
runtime initialized; loading replay-bc20.json          ← tests/fixtures/
{"loaded":true,"game_version":"GV05",…,"first_packet_bytes":69456,"frames":200,"mismatch_round":-1}
```

As a negative control, the same script against `results.json` now exits 1 with
`bc_load_replay failed: not a cogame-battlecode-replay document` where before it also exited 0.

## F14 — `first_build.unit`

Documented, not narrowed. `Bc20UnitNames` is the engine's own `RobotType` names, which is why the
drone is `delivery_drone`; the chassis genuinely builds miners and a refinery, so suppressing those
beats would hide two builds a spectator watches happen, and renaming them would make the feed line
disagree with the sim. `docs/REPLAY.md` lists the eight reachable values and points at §Divergences
item 16 for the two the note did not expect. All ten beat kinds still have CSS.

## F15 — "byte-identical"

Confirmed and corrected in prose, not in code. A structural JSON compare of `abc92ce` against
`551c542` reports no change under `/variants/0`, `/certification` or either `/player` entry; the
only textual change is that two bc26 strings lost their `\u2014` escape — the variant `name` the
review names, and also `player[scaffold].description` (`abc92ce:coworld_manifest_template.json:468`,
`:491`). The whole file is now uniformly raw UTF-8 (six em dashes, no `\u` escapes), so restoring
the escape on two strings would make the file internally inconsistent to satisfy a sentence.
The sentence is what was wrong; the build report carries an addendum saying so.

## NOTED (not fixed)

* `tests/test_bc20_replay.nim`'s ladder vectors for `broadcasts`, `highest_id` and `coin_flip`
  duplicate `tests/test_bc20_scoring.nim:110-147`. Kept deliberately: the coverage loop in the
  replay shard must be able to point at something it produced itself, and the two shards can be
  run independently.
* `wasm_replay_smoke.cjs`'s frame loop reports `frames: 200` on a 119-round replay, so
  `bc_frame()` keeps returning 1 past the end of the recording. Harmless for the smoke's `>= 50`
  floor, and outside this round's findings, but the count is not the round count.
* `tools/ci/check_gameversion.sh`'s `rule()` extracts `.*## ` from the `GameVersion` line, which
  carries no `##` comment in this tree, so the "rule headline" it compares is the whole line. That
  is conservative (any change to the line counts as a new rule) and it works, but it is not what
  the script's own comment describes.
