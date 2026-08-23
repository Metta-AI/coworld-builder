# r1 fixes — hive

Repo: `Metta-AI/cogame-hive`, branch `main`.
Head: **`34b3dc9e7355d5047e95109ad117f813a509d950`**
CI: run **32624269486** — <https://github.com/Metta-AI/cogame-hive/actions/runs/32624269486> —
conclusion **`success`** (`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓, including its
`Load the bundle in a real browser` step).

Every commit was written through the GitHub Git Data API (blobs → tree → commit → `PATCH
git/refs/heads/main`); `git push` over HTTPS is rejected in this sandbox. File modes are preserved:
`tools/ci/viewer_smoke.mjs` is committed `100755`, as are `tools/ci/docker_smoke.sh` and
`tools/build_replay_viewer.sh`.

No test was weakened, skipped, disabled or deleted. Two assertions that already existed were made
*stronger* (`tests/test_viewer.nim`'s `loadedAttributes`, `tests/test_sources.nim`'s `orbitCap`);
everything else in `tests/` is additive.

---

## Disposition table

| finding | disposition | commit | files |
|---|---|---|---|
| **B1 / F1** browser viewer smoke absent | fixed | `9306b9c7`, `f3d913e0` | `.github/workflows/ci.yml`, `tools/ci/viewer_smoke.mjs`, `tools/ci/docker_smoke.sh`, `tests/test_viewer.nim` |
| **B2 / F2** `data-replay-loaded` = `'1'`, set before the first frame | fixed | `2ada8741` | `replay-viewer/static_replay.js:155-168`, `client/replay_broadcast.html:2281-2288`, `tests/test_viewer.nim:97-118` |
| **B3 / F3** recall does not use the carrying kernel | fixed | `c22f3188`, `9dd4c47d` | `src/hive/ants.nim:68-87`, `src/hive/sim.nim:462-464`, `src/hive/types.nim:12-22`, `src/hive/rules.nim:90-96`, `tests/test_ants.nim`, both fixtures |
| F4 view built before the turn clock rolls | fixed | `e44dfc16` | `src/hive/sim.nim:214-236`, `src/hive/rules.nim:115-121`, `tests/test_view.nim:46-79` |
| F5 `contacts[].ants` counts samples | fixed (count) / **refuted** (cadence) | `05f9d998` | `src/hive/sim.nim:63-67,505`, `src/hive/broadcast.nim:64-82`, `tests/test_view.nim` |
| F6 `orbitsAlive()` counts survivors in quarters | fixed | `2c893f2d` | `src/hive/sources.nim:96-112`, `tests/test_sources.nim:53-110` |
| F7 raid uses the nearest nest | fixed | `c78094d6` | `src/hive/sources.nim:166-182`, `src/hive/sim.nim:448-456`, `tests/test_sources.nim` |
| F8 snapshot at the top of the tick | **refuted** | — | `src/hive/sim.nim:576-583` |
| F9 `focus_weight` repairs to a literal 0 | fixed | `c676e0fd` | `src/hive/doctrine.nim:196`, `tests/test_doctrine.nim:73-87` |
| F10 scoreboard in nest order | **refuted** | — | design.md:730-731 |
| F11 authored rock set ≠ the note's illustrative shapes | no action (note, disclosed) | — | — |
| F12 no outer per-turn deadline | fixed | `1cb0bdff` | `src/hive/llm.nim:29-36,86-91,146-149,292-308,345-360`, `src/hive/server.nim:226-227`, `tests/test_engine.nim` |
| F13 a turn batches the LLM seats, not always 4 | **refuted** | — | `src/hive/llm.nim:267-279` |
| F14 a 403 without the magic string disables the client | fixed | `aa76ed66`, `118f8af3`, `34b3dc9e` | `src/hive/llm.nim:131-148,210-228,296-310`, `tests/test_engine.nim` |
| F15 `claude-sonnet-5` unverifiable | **refuted** | — | three sibling starters |
| F16 budget guard covered only by inspection | fixed (test) | `f9f64a27` | `tests/test_server.nim:53-80,238-285` |
| F17 done-broadcast deadline is aggregate | fixed | `1ef2a53b` | `src/hive/server.nim:320-341` |
| F18 `hive_player` invents a default prompt | fixed | `31ab9b39` | `src/hive_player.nim`, `tests/test_startup.nim` |
| F19 unbounded blocking receive loop | fixed | `31ab9b39` | `src/hive_player.nim:79-92`, `tests/test_startup.nim` |
| F20 the player sends `register` twice | **refuted** | — | `src/hive/server.nim:436-466`, `src/hive/roster.nim:49-69` |
| F21 five caps on rune boundaries | no divergence; its one gap closed | `9cb586e5` | `tests/test_doctrine.nim:123-140` |
| F22 200 vs 201 keyframes; `held` in the digest | **refuted** | — | design.md:902 |
| F23 `results` = `results_schema` | no action (traced) | — | — |
| F24 manifest matches; `sprint` also moves `bonanzaTicks` | **refuted** | — | design.md:1143 |
| F25 placeholder gate, release order, modes | no action (clean) | — | — |
| F26 `/client/replay` route exists | **refuted** (route) / fixed (its splice bug) | `949ae262` | `src/hive/server.nim:112-128`, `tests/test_server.nim:75-86` |
| F27 three test gaps | fixed | `9cb586e5` | `tests/test_ants.nim`, `tests/test_doctrine.nim`, `tests/test_server.nim` |
| F27 (sub-items: half-life window, nudge-every-turn, debug perf budgets, viewer early return) | **refuted** | — | see below |
| F28 no grid harness for the baseline | fixed | `53767886` | `tools/tune_marcher.nim`, `src/hive/baselines.nim`, `.github/workflows/ci.yml`, `tests/test_baselines.nim` |
| F29 node wasm smoke lives in `wasm-viewer` | no action (note, disclosed) | — | — |
| F30 two extra exports, no `static_replay_worker.js` | no action (note, disclosed) — now positively covered | — | run 32624269486 |

Commits, oldest first:

```
9306b9c7  F1: restore the browser viewer smoke to the wasm-viewer job
2ada8741  F2: the shell sets data-replay-loaded="true" on the first drawn frame
c22f3188  F3: a recalled ant uses the carrying kernel regardless of its flag
e44dfc16  F4: roll the turn clock before the per-seat views are built
05f9d998  F5: contacts[].ants counts distinct ants, not co-location samples
2c893f2d  F6: an orbit is alive while ANY of its four members is
c78094d6  F7: a raid is flagged from the rival's radius, not the nearest nest
c676e0fd  F9: focus_weight repairs to the previous turn's value, not a literal 0
9dd4c47d  F3 (follow-up): flush the harvest buckets when the match ends
f3d913e0  F1 (follow-up): the browser-smoke step aborted before it ran
1cb0bdff  F12: add the outer per-turn deadline the note names
aa76ed66  F14: a 403 advances the Bedrock candidate whatever the body says
1ef2a53b  F17: the done-broadcast deadline is per seat, not one shared allowance
31ab9b39  F18 + F19: the player defaults to the marcher and its receive loop is bounded
949ae262  F26 (related observation): splice the wasm module into /client/replay too
9cb586e5  F27: close the three test gaps the review named
53767886  F28: add the marcher grid harness and run it in CI
f9f64a27  F16: cover the shipped budget guard with a test, not just inspection
118f8af3  F14 (follow-up): one batch of 403s is one verdict on one candidate
34b3dc9e  F14 (follow-up 2): reset the batch recorder in the bedrock ladder test
```

---

## B1 / F1 — the browser viewer smoke

**Was:** `wasm-viewer` had no `needs: docker-smoke`, `tools/ci/viewer_smoke.mjs` did not exist,
`docker-smoke` had no `Upload the smoke replay` step, and `tools/ci/docker_smoke.sh` had had its
`SMOKE_REPLAY_OUT` variable and its replay-preserving tail deleted, so the episode's replay was
removed by the script's own EXIT trap seconds after it was validated. Nothing anywhere loaded
`index.html`: the assembled page — spliced scripts, `HiveChrome.attach`, the `art/*` fetch, the DOM
markers — was never executed.

**Is:** restored from `coworld-builder/templates/` —
`tools/ci/viewer_smoke.mjs` byte-for-byte verbatim (`diff` clean, mode 100755);
`tools/ci/docker_smoke.sh` now `diff`s clean against the template after `<slug>/<IMAGE>/<SEATS>`
substitution; `ci.yml` gains the `smoke-replay` artifact upload in `docker-smoke` and, in
`wasm-viewer`, `needs: docker-smoke`, the `Assert the viewer load test is present` step, the
artifact download, the pinned `playwright@1.55.0` install, `Load the bundle in a real browser`, and
the always-on evidence upload. The existing node wasm smoke is **kept** — it exercises the wasm32 C
ABI and the `HVP1` packet decoder, which the browser step does not.

One follow-up was needed (`f3d913e0`): under `set -o pipefail` the template's
`ls dist/smoke/*.replay dist/smoke/replay.json` exits 2 because hive's replay is JSON and the
`*.replay` half matches nothing, and `set -e` aborted the step before its own error message could
run (run 32622827812, exit code 2, no output). `|| true` on the pipeline.

**Evidence** (run 32624269486, `wasm-viewer`):

```
loading dist/smoke/replay.json in dist/static-replay-viewer
{"loaded":true,"ms":5204,"clock":"0:39 TURN 0/4","scorebug":"P1 FOOD 0 Lime P3 FOOD 0 Magenta 0:39 TURN 0/4 P2 FOOD 0 Amber P4 FOOD 0 Teal","feed_lines":0}
scrub readouts: 0%="0:39 TURN 0/4"  50%="0:17 TURN 2/4"  100%="FINAL GAME OVER"
```

The replay it loaded is the one `docker-smoke` produced in the same run (SHA256 of the artifact zip
matches on both sides of the handoff: `8f98517d…`). Three distinct clock readouts prove the bundle
does not merely render one frame. `tests/test_viewer.nim`'s new `browserSmokeIsWired` block asserts
`needs: docker-smoke`, the artifact name, the load step, the playwright pin, the absence of any
`continue-on-error`, and `SMOKE_REPLAY_OUT` in the smoke script, so the hole cannot be reopened
silently.

**Checklist item satisfied:** 13, first bullet.

## B2 / F2 — `data-replay-loaded="true"` on the first drawn frame

**Was:** `client/replay_broadcast.html:2282` set `data-replay-loaded` to `'1'`, from the chrome page,
one statement *before* the `seek(0)` that draws the first frame.

**Is:** the chrome page sets it no longer. `replay-viewer/static_replay.js` — the shell — sets
`document.documentElement.setAttribute("data-replay-loaded", "true")` inside the double
`requestAnimationFrame` that already gated `tell("ready")`, i.e. after the first paint has completed.
`data-replay-error` was already set from the same shell path (`fail()`), and still is.

**Evidence:** the harness matches on `loaded_attr === "true"`
(`tools/ci/viewer_smoke.mjs:345`), and run 32624269486 reports `"loaded":true` after 5204 ms.
`tests/test_viewer.nim:97-118` asserts the literal `setAttribute("data-replay-loaded", "true")` in
the shell, that it sits inside a `requestAnimationFrame` before `tell("ready")`, and that the page
no longer sets it.

**Checklist item satisfied:** 13, second bullet.

## B3 / F3 — recall uses the carrying kernel

**Was:** `sim.nim` called `moveAnt` with no recall flag, so `moveAnt` branched on `ant.carrying`
alone. A recalled ant that was not carrying ran `searchScore`, which subtracts
`alphaHome * H_own` — it was *repelled* by the home trail it needed to follow — and laid nothing
(step 5 skipped). `recall` is documented to players (`docs/RULES.md:127`) and to the model
(`llm.nim:57`) as "every ant drops its road and walks home, then waits"; the behaviour was "stops
depositing and wanders".

**Is:** `moveAnt` takes `recalled = false` and ORs it into the carrying branch
(`src/hive/ants.nim:77,87`); `runAnts` passes the flag it already computed
(`src/hive/sim.nim:462-464`). The PCG draw *count* per activation is unchanged — three, always,
drawn before any terrain is read — so the fixed draw order the determinism contract rests on is
intact.

`GameVersion` 1 → 2 with the prepend-only changelog line, per `AGENTS.md`. Re-recording the two
committed fixtures reproduces the identical digests, because neither is a run in which recall ever
fires: `golden_digests.json` and `sample_replay.json` are both seed-42 marcher/driftling matches of
960 ticks = 4 turns, and the marcher's recall needs `zeroStreak >= 2` **and** a previous turn that
had a focus, which is impossible before turn 4 (turns 0–2 are the opener, `focus: null`). Verified
in CI: `ok - the committed golden digests still hold` in run 32624269486.

**Tests:** `tests/test_ants.nim` gains `recallUsesTheCarryingKernel` (with `spread` compiled to
`alphaHome = 300`, a searching ant turns off its own home trail and a recalled empty ant rides it)
and `recallGathersTheColony` (24 ants parked 34 cells out on a home trail muster at the pad and hold
inside one turn — under the searching kernel with `spread: 100` they are walked straight off the
road). Both green in run 32624269486.

**Follow-up (`9dd4c47d`):** fixing recall moved the marcher far enough that a longer episode picked
up a unit *after* the last 24-tick harvest flush, and `tests/test_sources.nim`'s existing
`harvestFlush` assertion caught it (`got 166, expected 167`). The residual was always latent —
anything taken between the final `t mod 24 == 0` and the end of the episode was never reported. The
fix is in `endMatch`, which now flushes the buckets before closing the match, so the harvest stream
sums to the units removed for every episode length. **The assertion was not touched**; the code was
wrong.

**Checklist item:** correctness — `AGENTS.md` calls the resolution order the contract and
`docs/RULES.md` ships this rule to players; also the "no test loosened" half of item 1 (the failing
assertion was fixed by fixing the code).

## F4 — the turn clock rolls before the views are built

**Was:** `rules.nim:117` evaluated `provide(...)` first and `installDoctrines` was the only place
that set `sim.turn` and rolled `deliveredLastTurn`. At `t = 240` the view read `"turn": 0,
"tick": 240`, and `delivered_last_turn` reported turn N-2's deliveries.

**Is:** `sim.beginTurn()` carries the turn number and the `deliveredLastTurn` roll and is called from
`runEpisode` before `provide`. `installDoctrines` still calls it (idempotent per turn via a new
`turnRolled` field, reset on snapshot restore), so every other caller — the tests, the wasm replay
runtime's rewind path — is unchanged. `sensed` and `contactCount` are deliberately still cleared
*inside* `installDoctrines`, after the view is built: the view for turn N is exactly the record of
turn N-1's walking, which is what the note says.

**Evidence:** `tests/test_view.nim`'s `viewClockIsCurrent` runs six turns and asserts
`view["turn"] == index`, `view["tick"] == index * 240`, and `delivered_last_turn` equals the exact
delta of the running total between consecutive turns, with a final non-vacuity check.
`ok - the view's turn number and fuel gauge are one turn fresh`.

## F5 — `contacts[].ants`

**Fixed:** `sim.Sim` gains `contactAnts[colony][rival]`, one flag per ant of *your* colony, set by
the scan and cleared with `contactCount` at the top of each turn; `broadcast.contactsJson` reports
the number of flags set. `tests/test_view.nim` parks two colonies on one cell and asserts the count
is ≥ 1 and never exceeds the roster.

**Refuted (the cadence half):** the note's 15-step list has no contact scan, but the note's own view
schema requires `contacts[]`, so the scan has to exist somewhere. It runs off the tick counter
(`sim.nim:604-605`, `t mod 4 == 0`), draws nothing from the PCG stream and writes nothing the digest
reads, so it is deterministic and cannot affect the replay contract. Only the arithmetic was wrong,
and that is fixed.

## F6 — the orbit cap

`orbitsAlive()` returned `ceil(live non-bonanza / 4)` — its own comment said that was the wrong rule
and then did it. Three half-eaten orbits (six live sources) rounded to two and a fourth orbit would
spawn. Exactly one orbit spawns per spawn opportunity, so the spawn tick identifies the orbit: the
count is now the number of distinct spawn ticks still represented among the live non-bonanza
sources. No new state.

`tests/test_sources.nim`'s `orbitCap` now walks the real turn loop over 4800 ticks and asserts the
cap at every spawn opportunity (before and after each spawn); a new `aPartlyEatenOrbitHoldsItsSlot`
block builds three orbits, kills three members of each, and asserts three orbits are still alive —
the old count said one — and that bonanzas never take a slot.

No effect on either committed fixture: at the four spawn opportunities of a 960-tick match the two
counts agree (0, 1, 2, 3 orbits), which is why the golden digests are unchanged.

## F7 — the raid rule

`nearestNest` gains an `exclude` parameter and the delivery path excludes the delivering colony,
which is the note's wording ("within `raidRadius` ... of a **different** colony's nest centre"). The
same proc still answers the different question — nearest nest, no exclusion — for `near_nest` in the
view and `near` on `source_spawn`.

Honest scope note: **no behaviour changes on the shipped meadow.** The four nest centres are at least
63 Chebyshev cells apart, so with `raidRadius = 20` at most one nest can ever be within radius of a
cell and the two rules coincide; the reviewer's worked example (15 from your own nest, 18 from a
rival's) is geometrically impossible here. The fix matters because `raidRadius` is a
`game_config` knob. Digests, deliveries and results are untouched.
`tests/test_sources.nim` pins the distinction at a 40-cell radius, where the shipped geometry does
make the two rules disagree.

## F9 — `focus_weight`

`repairDoctrine` read every other integer with `base.<field>` and `focus_weight` with a hard-coded 0.
Now `base.focusWeight`. `defaultDoctrine().focusWeight` is already 0, so turn 0 is unchanged, and the
"forced 0 when `focus` is null" rule below it is unchanged. `tests/test_doctrine.nim` pins all three
cases.

## F12 — the outer per-turn deadline

`LlmClient` gains `turnBudgetSeconds` (default `22.0`, set by the server from the game config).
`decideAll` opens a turn deadline before the first attempt, clamps each attempt to what is left of
it, and skips an attempt it cannot finish — those seats get the marcher doctrine with cause
`timeout` and a detail naming the deadline, so phase 60 still counts them.
`tests/test_engine.nim`'s `outerPerTurnDeadline` installs a transport that *ignores* the deadline it
is handed and asserts the turn still returns inside its own budget having issued exactly one batch.

## F14 — a 403 advances the Bedrock candidate

The advance was gated on the literal string `Model access is denied`. Any other 401/403 disabled the
client for the whole episode with two untried candidates still on the ladder. Now any 401/403 walks
the ladder and the client is disabled only when there is no candidate left;
`tryNextBedrockModel` still returns false off the Bedrock transport, so an Anthropic-direct auth
failure disables immediately, which is right — there is no ladder there.

Two follow-ups, both caught by CI:
- `118f8af3`: with four seats per batch and three candidates, advancing once per *failed response*
  walked off the end of the ladder inside the first batch. Every request in a batch goes to the same
  candidate, so `decideAll` now snapshots it and `tryNextBedrockModel` advances only for the model
  that is still current. This is a genuine improvement independent of the test.
- `34b3dc9e`: the new test counted batches without clearing the shared recorder.

## F16 — the budget guard, tested

The no-show server fixture added for F27 squeezes `wallClockBudgetSeconds` to 40 s, below the
guard's `2 × turnBudgetSeconds = 44 s` threshold, so **`server.nim`'s own closure** engages on turn
0. The test asserts exactly one `budget_guard` event with its `remaining_s` field lands in the events
file and that the episode still ends `complete/full_time` rather than `deadline` — the whole point of
settling early. `ok - a no-show plays the marcher, is reported, the budget guard engages, and the
episode still completes`.

## F17 — the done broadcast

One 3.0 s deadline was opened before the first seat and the loop `break`ed out of the whole broadcast
once it passed, so a slow first socket could leave slots 1–3 with no result frame. Each seat now gets
its own 3.0 s deadline, with a hard overall bound of `seats × 3.0 s` so nothing here can hang. The
write order — done, replay, results — is untouched.

## F18 + F19 — the player container

`DefaultPrompt` is deleted; a seat that sets neither env var registers `scripted: "marcher"` with a
log line saying so. The receive loop polls with a 5 s deadline (whisky's `receiveMessage(timeout)`
returns `none` on expiry, having consumed nothing — the timeout applies to the 2-byte frame header
read, so no partial frame is ever swallowed) inside a 1500 s lifetime bound: longer than the
platform's 1200 s episode timeout, so it can never cut a live episode short, and finite, so a pod
whose game died without closing the socket still exits on its own.
`tests/test_startup.nim` asserts no default prompt is compiled in, that an unconfigured player
announces the marcher, and that the source carries no `while true`.

Both live in the same twenty lines, so they share one commit — noted here as the brief allows.

## F26 — `/client/replay`

**Refuted, the route:** the design note keeps it deliberately ("The game server still serves
`/client/replay` for local viewing off the identical `dist`", design.md:944) and the starter does the
same. Checklist item 3's "no `/client/replay` pod path" is about the manifest declaring a
pod-served viewer; `coworld_manifest_template.json` declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and nothing references a pod.

**Fixed, the bug the reviewer found next to it:** `splicedChrome()` replaced the `BROADCAST_CORE`
marker with `static_replay.js` alone while `Dockerfile.replay-viewer:42` replaces it with
`hive_replay.js` *and* `static_replay.js`, so on the natively served page `HiveReplayModule` was
undefined and the shell threw a `ReferenceError` inside its `load` handler — no `data-replay-error`,
just a stuck curtain. Both scripts are now spliced, in the Dockerfile's order, and
`tests/test_server.nim` asserts it.

## F27 — the three test gaps

No production code changed.

1. `tests/test_ants.nim` claimed "doubled noise" in its report line but asserted only
   `alphaFood div 4` and `alphaRival 0` — the doubling lives in `moveAnt`, which `searchScore`
   cannot show. A new block zeroes every trail weight, sets `alphaFwd 100` against `alphaNoise 60`,
   and asserts a forager never leaves the forward cell over 1000 activations while a scout sometimes
   does.
2. `tests/test_doctrine.nim` now feeds a 240-rune `fallback.detail` whose 200th rune is a 4-byte
   emoji and asserts the cut lands on the rune boundary, `validateUtf8 == -1`, and a JSON round-trip.
   That was the one capped string of the five with no multi-byte test.
3. `src/hive/server.nim`'s `declarePlayerFailure` path was uncovered. A third server mode runs an
   episode nobody connects to and asserts `player_failure.json` names slot 0 (the lowest offending
   slot only) **and** that the episode still ends `complete/full_time` on the marcher.

**Refuted sub-items:**
- *`tests/test_pheromones.nim:43` accepts 168…184 where the note says 175 ± 2.* Decay fires every 8
  ticks (`decayPeriodTicks = 8`), so the achievable resolution of "the tick at which the value first
  drops below 2000" is 8 ticks; ±2 is not reachable by construction, and 168/176/184 are the
  multiples of 8 bracketing 175. Tightening it to ±2 would make the test assert something the rules
  cannot deliver.
- *`tests/test_determinism.nim` nudges on every turn, not turn 0.* Stated in the code comment at
  `:62-64` and correct: `poach` and `lay_food` are physically inert on turn 0 (no rival paint within
  reach, nobody carrying), so a turn-0-only nudge would honestly not move the digest. All six
  integers are still individually asserted to move it.
- *`tests/test_perf.nim` allows 270 s / 30 ms in debug.* The release budgets are the note's 45 s /
  5 ms; the debug allowance exists because `ci.yml` runs every test twice and a debug build is
  roughly six times slower. It is a different build, not a loosened bound.
- *`tests/test_viewer.nim:194-203` returns early when no bundle is present.* Deliberate and now
  positively covered twice in the same job: the `wasm-viewer` job runs
  `tools/wasm_replay_smoke.cjs` against the freshly built bundle (`wasm replay smoke OK: 960 ticks,
  961 frames, packet 113204B, no digest mismatch`) and then loads it in chromium. The new
  `browserSmokeIsWired` block asserts both are wired in `ci.yml`.

## F28 — the grid harness

`tools/tune_marcher.nim` sweeps the marcher's **pump** doctrine — the only part of the baseline whose
numbers are a choice rather than a rule — over a `scouts × trail_gain` grid, plays each candidate in
seats 0 and 2 against the driftling in seats 1 and 3 at three seeds for 1440 ticks each, ranks by the
share of all food delivered (the game's own score), prints the table, and exits non-zero unless the
shipped configuration is inside the top third by rank or within 0.02 share of the best point.

`src/hive/baselines.nim` gains `MarcherParams` and `ShippedMarcher`; `scriptedDoctrine` and
`scriptedResolved` take an optional `params` that defaults to `ShippedMarcher`, so every existing
call site is byte-for-byte unchanged and the harness drives the real baseline code path rather than a
copy of it. `ci.yml`'s `test` job runs it once, in release (27 episodes; a debug build would take
minutes). `tests/test_baselines.nim` asserts the harness exists, sweeps `ShippedMarcher`, is wired
into `ci.yml`, and that the marcher's shipped pump doctrine really is `ShippedMarcher`.

**Cited output** (run 32624269486, step `Marcher parameter grid`):

```
scouts   5  trail_gain  58  share 0.5208  per seed 0.347 0.549 0.667
scouts   5  trail_gain  78  share 0.5303  per seed 0.400 0.496 0.695
scouts   5  trail_gain  95  share 0.5116  per seed 0.415 0.500 0.619
scouts  15  trail_gain  58  share 0.5302  per seed 0.372 0.549 0.670
scouts  15  trail_gain  78  share 0.5367  per seed 0.451 0.496 0.664
scouts  15  trail_gain  95  share 0.5316  per seed 0.463 0.512 0.619
scouts  30  trail_gain  58  share 0.5218  per seed 0.341 0.549 0.675
scouts  30  trail_gain  78  share 0.5010  per seed 0.355 0.454 0.694
scouts  30  trail_gain  95  share 0.4947  per seed 0.339 0.476 0.670

ranked (3 seeds x 1440 ticks, candidate marcher in seats 0/2 vs driftling in 1/3):
   1. scouts  15 trail_gain  78  0.5367   <- SHIPPED
   ...
shipped rank 1 of 9, share 0.5367, best 0.5367, gap 0.0000
marcher grid OK: the shipped parameters are at or near the top
```

The shipped `scouts 15 / trail_gain 78` is the grid's argmax.

**Checklist item satisfied:** 7, second sentence.

---

## Refuted, with evidence

**F8 — the turn snapshot is taken at the top of the tick.** Not a divergence to fix. Taking it
pre-step at `t mod 240 == 0` is precisely what lets `rewindTo` (`replay.nim:259-268`) resume a turn
and re-install that turn's doctrine; taking it after step 13 would make a backward seek land in the
middle of a turn whose doctrine had already been consumed. `Snapshot` carries every field the digest
reads, and `tests/test_determinism.nim:116-143` asserts restoration reproduces the forward digest
byte for byte at every turn. Moving it would break a working invariant to satisfy an ordinal.

**F10 — the scoreboard is in nest order, not "alias-sorted".** The note's *own worked example*
(design.md:730-731) lists `Amber, Teal, Lime, Magenta`, which is nest order and is exactly what the
code emits (`broadcast.nim:83-91`). Alphabetical would be `Amber, Lime, Magenta, Teal` and would
contradict the example. The property the schema actually needs — a fixed, alias-only order, identical
for every seat — holds. Changing it would make the code disagree with the note's example and
gratuitously change every view.

**F13 — a turn batches the LLM seats, not always 4.** The code is right. A seat playing a scripted
baseline has no prompt and needs no HTTP request; posting one would be pure waste, and in the league
mix (`tools/ci/policies.json`: two `PLAYER_PROMPT` champions, two `PLAYER_SCRIPTED` fillers) it would
double the batch for nothing. The property the checklist names — "all seats' LLM calls go out as one
parallel batch per turn; sequential calls are blocking" — holds: `llm.nim:281-310` issues at most one
`sendBatch` per attempt and `sendBatch` is `curl.makeRequests(batch, timeout)`. `tests/test_engine.nim`'s
`oneParallelBatch` asserts all four in-flight windows intersect when all four seats *are* LLM seats.
The note's "exactly 4" describes the all-champion case.

**F15 — `claude-sonnet-5`.** It is the Anthropic-direct default in all three sibling starters that
carry this client: `cogame-bullwhip/src/bullwhip/types.nim:61`,
`cogame-babel/src/babel/types.nim:57`, `cogame-parley/src/parley/types.nim:91`. Hive inherited it
verbatim. It is unreachable from CI (no `ANTHROPIC_API_KEY`, and the hosted path is Bedrock), so
changing it on a guess would be strictly worse than keeping the value three shipped games use.

**F20 — the player sends `register` twice.** The second send is load-bearing, not redundant. In
mummy, `request.upgradeToWebSocket()` (`server.nim:455`) returns while the rest of the HTTP handler
is still running; `game.socketSlots[websocket] = slot` and the roster bookkeeping happen at
`:456-461`, and the WebSocket message events are dispatched by the server's own loop. A `register`
frame that arrives before that bookkeeping lands is dropped, and the seat silently degrades to the
marcher — which is exactly the race the comment at `hive_player.nim:95-96` names. `Roster.register`
is idempotent (`roster.nim:49-69`), so the second frame costs nothing and the observable protocol
state is identical to sending one. The note's sentence describes the minimum a player must do; it is
not a cap that is worth trading a real race for.

**F22 — 200 vs 201 keyframes, and `held` in the digest.** The note's arithmetic is the thing that is
off by one: keyframes are appended at `t mod 24 == 0` for `t` in `0 … 4776`, which is exactly
`4800 / 24 = 200`, and 201 would require a keyframe at `t = 4800`, a tick the episode never
simulates. The code is asserted at `tests/test_determinism.nim:47` and `tests/test_perf.nim:25`.
`held` in `hiveStateDigest` is a superset of the note's list and strictly strengthens the
cross-build equality check; both builds run the same code, so it cannot cause a mismatch.

**F24 — `sprint` also changes `bonanzaTicks`.** The note says sprint "changes only the episode
length"; the sprint episode is 2880 ticks, so the default `bonanzaTicks: [1200, 3600]` would put the
second bonanza 720 ticks past the end of the match. `[1200]` is what "changes only the episode
length" *means* once you write it down. Removing it would ship a dead config value, not a fix.

**F30 — no `static_replay_worker.js`.** Disclosed in the brief as a known deviation: playback is
main-thread (the wasm module emits an `HVP1` packet that `client/broadcast_core.js` decodes and
paints). This round adds the evidence the reviewer said was missing — the browser smoke loads the
assembled page and reports `loaded: true` with three distinct clock readouts, so the main-thread path
demonstrably renders and advances. The two extra exports (`hive_rock_ptr/len`, `hive_tick`) are
consumed by the shell and by the node smoke and are listed in `EXPORTED_FUNCTIONS`.

---

## NOTED (not fixed)

- `nim` emits four `UnusedImport` warnings on every build (`state.nim:8 types`, `rules.nim:9
  labels, doctrine`, `baselines.nim:11 doctrine`, and now `tools/tune_marcher.nim:24 doctrine`).
  Harmless, and cleaning them is not a finding in this round.
- `tests/test_engine.nim` shares a module-level `records` sequence between blocks, which is what
  produced the follow-up in `34b3dc9e`. A per-block recorder would be tidier.
- `docs/PROTOCOL.md:86` describes `contacts[]` without saying what `ants` counts. Now that the
  semantics are pinned (distinct bodies), one clause there would help a policy author.

## Verification, item by item

| item | evidence |
|---|---|
| 1 CI green, no test loosened | run **32624269486**, conclusion `success`, `head_sha 34b3dc9e…`, branch `main`. `git log -p -- tests/` over this round: every hunk is an addition or a strengthening; the only edited assertions are `test_viewer.nim`'s `loadedAttributes` (now requires the literal `"true"` and the shell as the source) and `test_sources.nim`'s `orbitCap` (now walks the real loop and asserts the cap it only named before). |
| 2 replay re-derivation | unchanged and still green (`tests/test_replay.nim:129-148`); the node smoke re-derives 960 ticks with `no digest mismatch`. |
| 3 static viewer | manifest unchanged; `/client/replay` refuted above and its splice bug fixed. |
| 4 both name spaces | unchanged (`tests/test_view.nim:104-143`). |
| 5 degrade-never-hang | F12 (outer per-turn deadline), F17 (per-seat done deadline), F19 (bounded receive loop) close the three open ends the review named. |
| 6 `num_agents` | unchanged; `grep -c SEAT-COUNT` over run 32624269486's whole log = **0**; `smoke OK: seats=4 results=1096B replay=51871B reason=complete`. |
| 7 baseline tuned with a grid harness | F28, output cited above, shipped config ranks 1 of 9. |
| 8 LLM reply handling | unchanged, plus F14's ladder fix and F12's deadline; fallbacks still recorded with cause and a 200-rune detail. |
| 9 rune-safe truncation | F21's one gap closed (F27 item 2). |
| 10 manifest | unchanged. |
| 11 360 px legibility | unchanged (`tests/test_viewer.nim:58-81`). |
| 12 release order and scaffold | placeholder gate re-run after the `ci.yml` edits: exits 1 (no matches). `git ls-files -s`: `tools/ci/docker_smoke.sh` 100755, `tools/build_replay_viewer.sh` 100755, `tools/ci/viewer_smoke.mjs` 100755. |
| 13 viewer executes | B1 and B2, evidence above. |
