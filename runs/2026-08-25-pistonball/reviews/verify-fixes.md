# verify fixes — pistonball (phase-60 findings F1–F3)

Head: `30964b3d16bffe6a4df164e7c13b1c581f1a48e4` (Metta-AI/cogame-pistonball, `main`)
CI: run **32934920010** — <https://github.com/Metta-AI/cogame-pistonball/actions/runs/32934920010> —
conclusion **success** (`test` success, `docker-smoke` success, `wasm-viewer` success).

| finding | disposition | commit | files | the test that now pins it |
|---|---|---|---|---|
| F1 — turn budget consumed by the rate-floor sleep | fixed | `06bd3f7b40bdc1e08a0ae8cdf6f53cd97b18aa30` | `src/pistonball/decide.nim:369-386`, `tests/test_engine.nim:187` | test_engine "the rate-floor wait is NOT charged to the turn budget" |
| F2 — endcard `LLM/FB` reads `0/0` | fixed | `87ba2922325a1515d96783b0ebcf700f94b121f9` | `src/pistonball/replays.nim:258-277`, `tests/test_replay.nim:145` | test_replay "the endcard's per-seat llm/fallback counts survive the replay" |
| F3 — `TOUCHES` and `LLM/FB` headers overprint | fixed | `30964b3d16bffe6a4df164e7c13b1c581f1a48e4` | `client/replay_broadcast.html:4179-4191`, `tests/test_viewer.nim:105` | test_viewer "every endcard column header FITS the column it labels" |

No test was weakened, skipped or deleted; the suite is 17 files × debug+release, all green locally
and in run 32934920010's `test` job.

---

## F1 — the per-turn budget clock started before the inter-batch sleep

**What the code did.** `decide.turn` sampled `turnStart = getMonoTime()` at the top of the turn
(old `decide.nim:326`), slept out the `minBatchSpacingMs` rate floor at :368–371, and then tested
`getMonoTime() - turnStart >= budget` at :383 with `budget = turnBudgetMs`. The manifest ships
`minBatchSpacingMs 45000 > turnBudgetMs 20000`, so from turn 1 on the budget was already spent the
instant the sleep returned: every LLM seat emitted
`timeout / "per-turn budget exhausted before attempt 1"` and fell back to wavebot **without a single
request being issued**. Round 2's replay is the proof — turn 0 llm @4097 ms, turns 1–7 fallback
@0 ms for both champion seats, `budgetGuards: 0`, `progress 0.0`, `sharedScore -16.78`.

**What it does now.** `turnStart` is sampled *after* the rate-floor sleep and after
`engine.lastBatchStart` is stamped, so `turnBudgetMs` bounds the turn's own work — the two attempts
— which is what its comment ("the whole turn is wrapped in a monotonic `turnBudgetMs` deadline",
`decide.nim:16-18`) always claimed. The budget-guard arithmetic in the same proc is unchanged and
stays consistent: it already reads one turn as `turnBudgetMs + minBatchSpacingMs` seconds
(`decide.nim:334-336`), i.e. exactly spacing-then-budget, and
`tests/test_engine.nim`'s "every wait settles inside 60 % of episodeTimeoutSeconds" (worst case
`(turns-1) * minBatchSpacingMs + turnBudgetMs`) still holds and still passes.

**Evidence.** New test, using the existing fake-provider seam, in the configuration the manifest
ships but the round-1 fake-clock tests never exercised (spacing > budget):

```
tests/test_engine.nim: "the rate-floor wait is NOT charged to the turn budget"
  minBatchSpacingMs = 400, turnBudgetMs = 200
  turn 0, then turn 1 -> require provider.batches.len == 2
                         batches[1].startMs - batches[0].startMs >= 400
                         no `fallback` record in turn 1's output
                         every seat's script.source == srcLlm
```

On the pre-fix `decide.nim` it fails at
`tests/test_engine.nim(217): Check failed: provider.batches.len == 2 / provider.batches.len was 1`
— i.e. turn 1 issued no batch at all, the exact defect. With the fix: `[OK]`, debug and release.

## F2 — the endcard's LLM/FB column read 0/0 for LLM seats

**What the code did.** The endcard table's `LLM/FB` cell is
`client/replay_broadcast.html:4471` reading `p.llm` / `p.fb` from the state frame's `roster`, which
`broadcast.rosterJson` (`broadcast.nim:153-154`) fills from `sim.llmTurns` / `sim.fallbackTurns`.
Those two counters were incremented in exactly one place — `server.nim:609-611`, on the live
decision path. A **replay** re-simulates from the recorded bytes and never runs that path, so in the
static viewer (which is what softmax.com serves, and what the phase-60 screenshot shows) they stayed
zero and every row printed `0/0`, including champion seats whose own results document in the same
replay says `llmTurns [1,1]`.

**What it does now.** `replays.applyReplayEvents` increments them from the `source` field of each
`script` chat record, alongside the `say` it already re-applies from that record. Both are
non-hashed presentation fields (`sim_types.nim:278-284`, "non-hashed presentation"), so the hash
chain is untouched — `tests/test_replay.nim`'s "a recorded episode re-simulates to every recorded
hash" and `tests/test_determinism.nim` both still pass. Counters and the chat cursor ride the same
keyframe (`serializeReplaySim` flattens the whole `SimServer`), so a seek or a loop restart neither
double-counts nor loses them.

**Evidence.** `tests/test_replay.nim`'s recorded episode now writes seat 0 as `srcLlm` and seat 1 as
`srcFallback` (the recorded stream therefore carries all three `source` values), and the new test
re-simulates the bytes and checks:

- `replaySim.llmTurns[0] == turnsPerSeat`, `fallbackTurns[0] == 0`
- `replaySim.fallbackTurns[1] == turnsPerSeat`, `llmTurns[1] == 0`
- a scripted seat counts as neither
- `buildStateJson(...)["roster"][0]["llm"]` and `["roster"][1]["fb"]` — the endcard's actual source —
  carry the same numbers
- after `buildReplayKeyframes` + `seekReplay(maxTick)`, the counts are identical (no double count)

On the pre-fix `replays.nim` it fails with `replaySim.llmTurns[0] was 0 / turnsPerSeat was 1` and
`roster["roster"][0]["llm"].getInt was 0`.

Note for the coordinator: CI's `docker-smoke` episode runs with no API key, so its replay has only
scripted seats and its endcard legitimately shows `0/0`. The column will show real numbers on the
next league episode, where seats decide via the LLM.

## F3 — the TOUCHES and LLM/FB headers overprinted each other

**What the code did.** The twenty-seat endcard is two side-by-side tables; the header grid and each
row grid are separate elements, so their columns must be **fixed** widths to line up
(`client/replay_broadcast.html:4179-4181`, fixed at 28/32/28/32 `--u`). The labels inherited the
starter's `.ec-thead` type (`font-size: calc(7.5 * var(--u))`, `letter-spacing: 0.12em`), which does
not fit those cells: measured in headless chromium against the pre-fix page at `--hudscale: 1.6`,
`TOUCHES` overflowed its cell by **23 px** and ran **15 px into the LLM/FB cell** — the
`TOUCHEŁŁM/FB` in the phase-60 screenshot — and `PISTON` overflowed by 8 px.

**What it does now.** The bank table's header sets its own size and tracking
(`calc(6 * var(--u))` / `0.02em`) and the four fixed columns are re-sized for it
(28/36/32/28 `--u`). Same browser measurement on the fixed page: **max overflow 0 px**, every label
ending at least 10 px before the next cell starts, in both table columns. The name column keeps
50 `--u` (80 px at that scale): `daveey` (75 px) and `daveey-1` (78 px) are unclipped, and the long
`Baseline (N)` filler names ellipsize exactly as they did before — no row changed its clipping.

**Evidence.** `tests/test_viewer.nim` gains "every endcard column header FITS the column it labels",
which reads the grid template, the cell gap, the header's font-size and letter-spacing and the
label strings out of the page itself and checks each label against its own column at a documented
upper bound for an uppercase glyph (0.7 em), plus that the fixed columns are not paid for out of the
name column (which must still hold the 7 `ch` its `.pname` refuses to shrink past). On the pre-fix
CSS it reports, for each column:

```
PISTON needs 36.0u and has 28.0u
IN PHASE needs 48.3u and has 32.0u
TOUCHES needs 42.15u and has 28.0u
LLM/FB needs 36.0u and has 32.0u
```

## NOTED (not fixed)

- In a replay, `sim.seatPolicyKind` is likewise never populated (only `server.nim:531-532` sets it),
  so the state frame's `roster[].kind` reads `"scripted"` for every seat during playback. Nothing on
  the endcard currently renders `kind`, so it is invisible today and is not part of F2; it is the
  same class of defect and would be a one-line recount off the `register` record if a future chip or
  badge starts using it.
- The endcard's `Baseline (N)` filler names ellipsize in the 50 `--u` name column (they did before
  this change too). Not a finding; recorded because the measurement is now on the record.
