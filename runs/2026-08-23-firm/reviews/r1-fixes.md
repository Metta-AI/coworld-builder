# r1 fixes — 2026-08-23-firm (Metta-AI/cogame-firm)

Head: `62dcd64f06dd18cf4fca8ae3a612598697299afa` (main)
CI: [run 32682767057](https://github.com/Metta-AI/cogame-firm/actions/runs/32682767057) —
**success** (`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; `smoke OK: seats=5 results=374B
replay=7789B reason=complete`, no `SEAT-COUNT FAIL` in the docker-smoke log, `"loaded":true` from
the viewer smoke).

Nine commits, one per finding (F7 needed a follow-up after its own new test failed in CI, and F1
a second commit to cite the main-branch run in its record — both are noted below).

| finding | disposition | commit | files |
|---|---|---|---|
| **F1** (blocking) | fixed | `de1982e`, `62dcd64` | `tests/test_tuning.nim`, `docs/baseline-sweep.md`, `src/firm/llm.nim:41-98,235-284` |
| F2 | fixed | `d11d990` | `src/firm/llm.nim:61,240`, `src/firm/server.nim:283-287`, `tests/test_bot.nim` |
| F3 | declined | — | — |
| F4 | fixed | `7faaac3` | `data/soldier_{blue,green,yellow}_front.png` (deleted), `README.md:98`, `scripts/art/split_cog_sheet.py:19` |
| F5 | fixed | `0670fac` | `src/firm/sim.nim:559-573,626,651`, `tests/test_sim.nim:207-235` |
| F6 | fixed | `6833efa` | `src/firm/llm.nim:502,541,549,554,563`, `tests/test_bot.nim` |
| F7 | fixed | `a1b8940`, `316f380` | `src/firm/sim.nim:40-43,449,499`, `src/firm/llm.nim`, `tests/test_sim.nim` |
| F8 | declined (NEEDS-DESIGN) | — | — |
| F9 | declined | — | — |
| F10 | declined | — | — |
| F11 | declined | — | — |
| F12 | fixed | `eaa2b27` | `src/firm/sim.nim:79-80,451,500,631`, `tests/test_sim.nim:504-521` |

The four "could not determine" items are addressed at the end.

---

## F1 — no grid-tuning harness for the scripted baselines (BLOCKING, checklist item 7)

**Before.** `SteadyRun/SteadyMaint/NurseRun/NurseMaint/NurseBelow/SteadyPayroll` were bare literals
in `llm.nim:33-41`. Their only justification was the design note's arithmetic. Nothing in the tree
swept anything, so item 7's second half ("the baseline's parameters were tuned with a grid harness,
not guessed") could not be verified.

**After.** `tests/test_tuning.nim` **is** the harness, and it runs in CI with every other test
(debug and `-d:release`), so it is not a one-off script whose output could drift from the code:

- The dials are now a `BaselineParams` value (`llm.nim:41-49`) with `ShippedBaseline`
  (`llm.nim:92-97`) as `scriptedAction`'s default, so the sweep drives the **shipped policy code**
  rather than a copy of it. Production always takes the default.
- Objective, pre-registered in the harness's own header: the mean over the evaluation episodes of
  the **weakest seat's score**, `min(manager, the four workers)`. Total surplus cannot serve —
  payroll only moves money between manager and workers, so surplus is blind to the pay rule.
- Two scenario families, because the two halves of the policy are reached by different episodes.
  **S** (594 candidates: `run` × `maint` × `payroll`) is an all-`steady` table; the nurse branch
  never fires there because a steady machine holds at exactly 100. **R** (528 candidates:
  `nurseRun` × `nurseMaint` × `nurseBelow`) plays a window of shifts as `taskmaster` and hands the
  wrecked machine back to `steady` — the shape of a real mid-episode LLM fallback, and the only way
  `condition < nurseBelow` is ever reached. Both at horizons {8, 24} shifts over seeded episodes.
- The harness **asserts** the argmax: family S's argmax is exactly the shipped `run 6 / maint 3 /
  payroll 40` *and* strictly beats the runner-up; family R's argmax among repair-shaped candidates
  is exactly the shipped nurse. A constant that stops being the argmax turns CI red.
- `docs/baseline-sweep.md` records the tables, the method, what the sweep does not settle, and the
  CI run they came from.

**What the sweep decided.** `run 6 / maint 3 / payroll 40` is **confirmed** — the unique argmax of
594 candidates (0.9203 against 0.9160 for `run 7 / maint 3`). The nurse is **changed**: the design
note's `run 4 / maint 6 below 40` scores 0.6297 and ranks **130 of 240** repair-shaped candidates;
the argmax is `run 0 / maint 8 below 70` at 0.7521 — a wrecked machine spends one shift in the shop
and comes back at full condition instead of limping back over four. That is a deviation from
design.md §Scripted baselines, disclosed in `docs/baseline-sweep.md`, in the constant's own comment
(`llm.nim:80-97`) and in the F1 commit message. The unconstrained argmax (`nurse 10/0`, 0.7619) is
recorded and **not** adopted, with the reason stated: it is not a nurse at all but the `taskmaster`
foil's move, and adopting it would collapse the difference between the two shipped baselines. The
harness prints the unconstrained table beside the constrained one so that choice is on the record.

**Evidence.** Run 32682573460 (main, sha 316f380) and every run since, job `test`:
`[OK] family S: the shipped pace and pay rule are the sweep's argmax`,
`[OK] family R: the shipped nurse is the sweep's argmax among repairs`, with both tables and the
line `the design note's nurse (run 4 / maint 6 below 40): 0.6297 — rank 130 of 240`. `TaskmasterPayroll = 20`
is deliberately not swept and says so in code: `taskmaster` is the foil, fixed below the worker's
$1.50/hour indifference point by construction.

Satisfies **checklist item 7** (both halves: the legality half was already satisfied and is now
also pinned inside the harness by "the shipped baseline is legal everywhere on the grid it was
tuned on").

## F2 — a mid-episode LLM fallback was not flagged in the replay

`server.nim:283` computed `wasScripted` from the seat's static registration and the client-wide
`disabled` flag only, so a seat whose reply failed both attempts and fell back to
`scriptedAction()` was written into its `memo`/`work` event with `"scripted": false` — contradicting
`types.nim:75` and undercounting fallbacks for phase 60, which counts from the replay rather than
from the container's stdout.

`Decision` now carries the provenance (`llm.nim:61`): `scriptedAction()` sets `scripted = true` on
every move it makes, the two parsers leave it false, and the server ORs it into the flag it hands
to `applyMemo`/`applyWork`. Test in the same commit: a scripted move is flagged, a parsed reply is
not, and every decision from a credential-less `decideAll` is flagged. Serves **checklist item 8**
("the fallback is recorded so phase 60 can count it") on the replay side, not only on stdout.

## F3 — `test_bot.nim`'s documented deviation from the design note — **declined**

Not a defect: the reviewer confirmed it was written that way when the tests were created
(`75efe8b`), not loosened during this run, and the in-code NOTE explains why the note's claim
cannot hold (taskmaster's workers obey at run 10 whatever they are paid, so its 20 % payroll keeps
more revenue). Changing the test to the note's claim would make it false; changing the game to make
the note's claim true is a design change, not a fix. Left as disclosed.

## F4 — unreferenced starter sprites

Deleted `data/soldier_{blue,green,yellow}_front.png` (147 KB): nothing draws them
(`renderer.js:82-91` looks up `cog_*.png`) and `tools/build_replay_viewer.sh:51-55` copies only the
cog sprites. **`soldier_red_front.png` is kept and is not residue** — the reviewer's "referenced by
nothing" is true of the runtime but not of the tree: `scripts/art/generate_cog_sheet.py:26` anchors
the nano-banana character design on it. `README.md` and the splitter's docstring now name that one
file instead of the `soldier_*` glob.

## F5 — the DEFIED chip lit before the worker had acted

`tableStateJson` computed `"obeyed"` as `machine.setup == machine.order`; `openShift` installs the
manager's new order while `setup` still holds last shift's line, so every machine just ordered to
switch was reported defiant before its worker decided anything, and `renderer.js:1224` lights the
amber chip on `!seat.obeyed` with no guard. `sim.obeyedNow()` (`sim.nim:559-573`) answers post hoc,
which is what design.md:899-901 says the chip means: the line the worker chose this shift once it
has acted, otherwise the last resolved shift's verdict, and `true` before any shift has resolved.
Test asserts all three cases. No renderer change was needed.

## F6 — captured error text was cut on byte boundaries

The five error constructions in `llm.nim` (the quoted head of a non-JSON reply, the two auth and
throttle details, the non-2xx body, the `max_tokens` head) now use `runeSubStr`. These strings
reach the container log rather than the replay — the reviewer traced that correctly — but
**checklist item 9** names captured errors among the strings that must be rune-safe, and the log is
what phase 60 reads. Test: a 400-rune multi-byte reply with no JSON raises a `FirmError` whose
message is valid UTF-8 and shorter than the input.

## F7 — `notes` was capped only in the parser

`applyMemo`/`applyWork` stored `notes` verbatim and copied it into the event's `text`, which
reaches the replay, while `say` was trimmed at the same boundary. Both now apply the same rune-safe
`trimText(notes, MaxNotesLen)`, and `MaxNotesLen` moves from `llm.nim` to `sim.nim` beside
`MaxDirectiveLen`/`MaxReportLen` because the sim is now the module that enforces it. No live bug
was fixed — every production caller passes an already-capped string — the gap is closed.

**CI failure and fix-forward, disclosed:** the test added with `a1b8940` fed a 400-rune fixture,
which is past the directive (240) and report (120) caps but *inside* the notes cap (600), so the
new assertions checked a string that was never truncated and run
[32682358341](https://github.com/Metta-AI/cogame-firm/actions/runs/32682358341) went red on
`tests/test_sim.nim:312`. `316f380` feeds it 700 runes, past every cap. The failure was mine and it
is the only red run in this round.

## F8 — no wall-clock floor between LLM batches — **declined (NEEDS-DESIGN)**

Real and worth doing, but it is a change to the design note's §Episode budget, not a fix at a cited
site: a floor of ~10 s per batch (5 requests against the sidecar's 30 req/min) would fit inside the
existing 60 s per-shift ceiling, but it changes the typical-case arithmetic the note reasons about
and would have to be re-derived there. Recorded for phase 40/60 rather than made unilaterally by
the fixer.

## F9 / F10 — `docker_smoke.sh` player exit codes, `viewer_smoke.mjs --soak` — **declined**

Both files are byte-identical to `coworld-builder/templates/`, which the reviewer verified and
which is itself the evidence for checklist item 12. Editing them here would fork the template in
one repo and hide the gap from every other game that inherits it; the fix belongs in the template.
Neither falsifies a checklist item (F9's player-side risk is already mitigated in this repo by
`firm_player.nim:66-97`, and item 13 requires the smoke step to run, which it does).

## F11 — no schema maximum on `player_connect_timeout_seconds` — **declined**

Inference-only, and item 5 is satisfied as configured: both manifest variants and the certification
fixture set 180, giving `180 + 8×60 + 20 = 680 s < 720 s`. Adding a `maximum` to the manifest schema
would harden against an operator-supplied value that no shipped config produces, at the cost of a
manifest change that could reject a platform default. Left alone deliberately.

## F12 — the spectator frame always reported `"scripted": false`

The `Sim` carried no per-seat flag, so `sim.nim:609` (`:631` after the fix) hard-coded `false` for every
seat on every frame. The `Sim` now records, per seat, whether its last applied decision came from a baseline —
`applyMemo`/`applyWork` already take that flag and `replayMatch` replays it off the event, so the
provenance survives the round trip and the viewer's re-derived frames agree with the live ones.
Test asserts a mixed table's flags and that `replayMatch`'s final frame is byte-identical to the
live frame. Together with F2 this makes **checklist item 8**'s "recorded so phase 60 can count it"
true of the replay as well as of stdout.

---

## The reviewer's four "could not determine" items

- **`curly.makeRequests` batch bound** and **`readCogameUri`'s fetch bound**: unchanged and
  unchangeable from here — neither package is vendored or present in the sandbox, and both are
  inherited verbatim from the starter, which has run in production. Not touched.
- **The LLM-driven wall clock end to end**: still arithmetic, still untestable in CI (the only
  executed episode has no credentials). Phase 60's hosted episode settles it.
- **Whether the `steady` baseline's constants are tuned**: settled by F1 — see the harness and
  `docs/baseline-sweep.md`.

## NOTED (not fixed)

- `renderer.js:1376` computes `obeyed: entry.setup === entry.order` in the **player**-page adapter,
  the same pre-decision comparison F5 fixed in the sim. It is not the replay path and not a
  checklist item, so it is out of this round's scope.
- The `steady` manager's directive still ends with the literal sentence "Six hours running, three
  on maintenance."; it is true of `ShippedBaseline` (and CI now asserts the pace is 6/3), but it is
  a literal where the numbers beside it are parameters.
