# r1 fixes — gridlock

Repo: `Metta-AI/cogame-gridlock`. Review: `runs/2026-08-23-gridlock/reviews/r1-review.md`
(25 findings, **0 blocking**), reviewed at `4b74806`.

**Head: `0decf3220186f0ae07d7b03731624c07d1277847`**
**CI: https://github.com/Metta-AI/cogame-gridlock/actions/runs/32646687184 — `success`**
(jobs `test` 97211916089 ✓, `docker-smoke` 97211916175 ✓, `wasm-viewer` 97212078642 ✓,
`viewer-native` 97212347499 ✓ — the last is new, see F19.)

23 commits sit between the reviewed sha and this head: 17 from the first fixer leg, 5 new fixes,
and one test-shape follow-up. Three findings are dispositioned **no change** with the evidence
below. No test was disabled, skipped, weakened or removed: `git -C <repo> log -p 4b74806..HEAD --
tests/` contains no deleted assertion, no widened tolerance and no added skip — the only
`skip()` in the tree is F19's, which now has a CI job that turns it into a failure.

Note on shas: plain `git push` is rejected on this repo (`No anonymous write access` /
`Password authentication is not supported`), so the five new commits and the follow-up were
written through the GitHub Git Data API with `GH_TOKEN`, one API commit per local commit, parent
chain preserved. The shas below are the ones on `main`.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 keyframe at the top of the tick | **no change** (evidence below) | — | `src/gridlock/sim.nim:438-440` |
| F2 `gridlock` sampled every 24 ticks | fixed | `d9ea8c6` | `src/gridlock/sim.nim:452` |
| F3 statistics window is the turn so far | fixed (docs + code comment) | `2248251` | `docs/PROTOCOL.md:63-74`, `src/gridlock/rules.nim:15-20` |
| F4 missing route-start guard | fixed | `62f7aff` | `src/gridlock/rules.nim:163-185`, `sim.nim:437-438`, `tests/test_engine.nim` |
| F5 one shared destination cursor | **no change** (evidence below) | — | `src/gridlock/sim.nim:266-281` |
| F6 `fallback` dated one turn early | fixed | `e957810` | `src/gridlock/server.nim:139-149`, `tests/test_server.nim` |
| F7 `latency_ms` always 0 | fixed | `80f85b7` | `src/gridlock/llm.nim:308-348`, `tests/test_engine.nim` |
| F8 no outer 22 s turn deadline | fixed | `0cf410d` | `src/gridlock/llm.nim:119-330`, `server.nim:220`, `tests/test_engine.nim` |
| F9 disconnect does not degrade | fixed | `0a346be` | `src/gridlock/roster.nim:67-85`, `server.nim:136`, `tests/test_engine.nim` |
| F10 player substitutes a default prompt | fixed | `c74ca7a` | `src/gridlock_player.nim:20-34`, `tests/test_startup.nim` |
| F11 register frame sent twice | fixed | `1ddb7da` | `src/gridlock_player.nim:89-96`, `tests/test_startup.nim` |
| F12 no-credentials plan recorded `scripted` | fixed | `aca5615` | `src/gridlock/llm.nim:304-312`, `tests/test_engine.nim` |
| F13 no-float guard covered 3 modules | fixed | `f27ff29` | `tests/test_traffic.nim:179-192` |
| F14 byte slice on model text | fixed | `feafb00` | `src/gridlock/plan.nim:38-47`, `llm.nim:239-255`, `types.nim`, `tests/test_plan.nim` |
| F15 thirteen inert chrome ids | fixed | `ea9a952` | `client/chrome_common.js:469-482`, `client/replay_broadcast.html:192-198`, `tests/test_viewer.nim` |
| F16 two transport buttons mis-wired | fixed | `15b7996` | `client/chrome_common.js:451-466`, `tests/test_viewer.nim` |
| F17 gridlock overlay not in `#jamflash` | fixed | `39c8793` | `client/chrome_common.js:339-345`, `client/replay_broadcast.html:134-141`, `tests/test_viewer.nim:150-160` |
| F18 `viewer_smoke.mjs` behind the template | fixed | `be0b78f` | `tools/ci/viewer_smoke.mjs` |
| F19 native viewer case skips in CI | fixed | `3519b69` | `tests/test_viewer.nim:240-262`, `.github/workflows/ci.yml:330-414` |
| F20 nimby not sha256-checked | fixed | `243f5f5` | `Dockerfile:18-34` |
| F21 `events_last_turn` spanned two turns | fixed | `b732790` (+ `0decf32`) | `src/gridlock/view.nim:88-99`, `tests/test_view.nim` |
| F22 arterial second discharge undocumented | fixed (docs + code comment) | `0df4697` | `docs/RULES.md:78-85`, `src/gridlock/sim.nim:405-418` |
| F23 `±1` digest sensitivity not achievable | fixed (test added) | `cc464fb` | `tests/test_determinism.nim:61-87` |
| F24 plazas off the note's coordinates | **no change** (evidence below) | — | `data/gridcity.cityspec.json:566-595` |
| F25 no baseline tuning harness | fixed | `c864e15` | `tools/tune_baselines.nim`, `tools/tuning/*`, `src/gridlock/baselines.nim`, `tests/test_baselines.nim` |

---

## New this leg

### F3 — `jam_index` / `districts_heat` window · `2248251`
*Checklist: none directly; keeps item 10's inlined docs truthful.*

What the code did and still does: `resetTurnWindow` (`src/gridlock/rules.nim:15`) clears the
accumulators at every `installPlans`, and `refreshHeat` divides by whatever has landed since — so
the window is **the turn so far**, not a fixed trailing 240 ticks. The shipped
`docs/PROTOCOL.md` said "over the previous turn window", which is true of the number a *seat* is
handed (its view is built in `seatRequestsLocked` **before** `installPlans` advances the clock, so
the last recompute of the previous turn — 193 samples, 48 ticks before the boundary — is what it
reads) but not of the mid-turn `heat` events, whose first sample after a boundary covers one tick.
The protocol page now states exactly what is measured, over what, and why the first heat event of
a turn reads low; `rules.nim` carries the same sentence at the reset site.
`coworld_manifest_template.json` was regenerated (`python3 scripts/make_manifest.py`) so the
inlined copy still matches byte for byte — `tests/test_manifest.nim` "the inlined docs match the
committed files" ✓.

A true rolling 240-tick window was **not** made: it needs a per-lane ring buffer over 288 lanes,
and it would move the jam index the scripted dispatcher reads (`baselines.nim` ladders at 35/55/75),
i.e. new plans, new digests and a regenerated golden fixture. That is a design change, not a fix.

### F17 — the gridlock alarm now lights `#jamflash` · `39c8793`
*Checklist: item 11 (legibility) / item 13's chrome.*

What it did: a `gridlock` event armed `flash` in `broadcast_core.js:423-430`, drawn as a hatched
district rectangle on the board canvas (`drawFlash`, `:322-334`); `#jamflash` — the element the
note's readout 4 names — stayed empty. What it does now: the same event branch in
`chrome_common.js` that raises `#bannerlane` also adds `.show` to `#jamflash` and clears it after
2200 ms, and the page has the CSS that makes that a full-frame red pulse
(`#jamflash.show{opacity:1}` over an inset box-shadow). The district rectangle stays on the canvas
deliberately: only the canvas carries the pan/zoom transform, so a DOM overlay cannot place it
over the right nine blocks. Evidence: new case `a gridlock event drives #jamflash, not only the
canvas` in `tests/test_viewer.nim` — green in `test` (both modes) and in `viewer-native`.

### F19 — the native viewer case now runs against a real bundle · `3519b69`
*Checklist: item 1 (no test skipped) and item 13 (the viewer executes).*

What it did: `tests/test_viewer.nim`'s "the emitted module replays to the end when a bundle is
present" called `skip()` whenever `dist/static-replay-viewer/gridlock_replay.js` was absent. The
`test` job's runner has no emsdk, so the bundle was never there and the case that drives the
**emitted 32-bit module** had never once executed in CI — `[SKIPPED]`, both modes, every run.

What it does now: the bundle path comes from `GRIDLOCK_VIEWER_BUNDLE` (default unchanged), and a
missing bundle is a **failure** (`fail()` with a checkpoint) whenever `GRIDLOCK_REQUIRE_BUNDLE` is
set. The new `viewer-native` job (`needs: wasm-viewer`) downloads the bundle `wasm-viewer` built,
installs the same nimby/Nim pins as `test`, and runs the file with both variables set. Outside CI
— a sandbox with no emsdk — the notice and the skip remain, so no developer workflow was broken
and no assertion was weakened: a case that never ran now runs.

Evidence (job 97212347499, this run): `[Suite] the native half of the viewer check` →
`[OK] the emitted module replays to the end when a bundle is present`. Locally, with the variable
set and no bundle, the binary exits 1 with `GRIDLOCK_REQUIRE_BUNDLE is set and
dist/static-replay-viewer/gridlock_replay.js is missing`.

### F22 — the arterial's second discharge is described · `0df4697`
*Checklist: none; closes the "implementation detail not described by the note" half of the finding.*

`serviceStep` (`src/gridlock/sim.nim:405-418`) promotes the van in the cell behind the stop line
into the stop line and crosses it when an arterial's first discharge emptied it. Nothing said so:
`docs/RULES.md` step 7 said "discharge up to 2 … from the stop line", which one van per cell makes
impossible on its own, and the code site had no comment. Both now state the promotion, that it
belongs to service and not to movement (it does not wait for a move tick), and why it cannot put
two vans in one cell (the vacated cell is written `-1` before the van is re-indexed). No behaviour
change — `tests/test_traffic.nim` already pins the caps and the one-van-per-cell invariant over a
full run, and still does. Manifest regenerated for the docs change; `test_manifest` ✓.

### F23 — one-unit digest sensitivity, where one unit exists · `cc464fb`
*Checklist: item 2's determinism property.*

The reviewer's arithmetic is right and the existing `+37 mod 101` case stays: `congestion_weight`
feeds `jamTerm = (weight * occupancy * 24) div 100`, which is 0 on an empty lane for **every**
weight, so ±1 provably cannot move a cost there. The note's claim is nevertheless true of a field
with no such floor: `activeCap = (dispatch * fleetSize + fleetSize) div 100` steps a whole van
every two units. The new case asserts `activeCap(20) + 1 == activeCap(21)` and then runs two
1920-tick episodes at seed 11 that differ only in seat 0's `dispatch` on turn 1 — 20 against 21 —
and asserts the keyframe digests diverge. Green in debug and `-d:release`; the golden fixture is
untouched and still matches.

### F21 follow-up — the documented-keys case keeps its own name · `0decf32`
Not a new finding. `b732790` added the `events_last_turn` window assertions by renaming the
existing `the documented keys are all there` test and appending its body — no assertion was lost,
but `git log -p -- tests/` read like a deleted test, which is exactly what item 1 tells the judge
to treat as blocking. Same assertions, restored under their own name; both cases green.

---

## No change (with evidence)

### F1 — the keyframe is written at the top of the tick
*Advisory, touches item 2. Code: `src/gridlock/sim.nim:438-440`; header `:6-17`.*

Not changed, and deliberately. A keyframe taken at the top of tick `t` is the state **leaving tick
`t-1`**; the note's step 12 would label the state leaving `t` with `t`. Nothing about the property
item 2 asks for depends on which of the two conventions is used, because every consumer uses the
same one: `rederive` re-runs the identical `stepTick` (`src/gridlock/replay.nim:293-302`), and
`tests/test_replay.nim:111-123` asserts every keyframe `t`, `d` and every byte of `vehicles_b64`
against the recording. What *does* depend on it is the seek design: the per-turn snapshot is taken
at the same phase (`sim.nim:259-260`, with the comment saying so) precisely so that a backward seek
lands on a state whose digest is the keyframe's — asserted by
`tests/test_determinism.nim:72-89`. Moving the call to the end of the tick would shift every
recorded digest by one tick, break that snapshot/keyframe pairing, and require regenerating
`tests/fixtures/golden_digests.json` — a design change with no behavioural gain. The deviation is
already documented in the module's own header, which numbers it `0` and says so.

### F5 — one shared canonical destination cursor
*Advisory. Code: `src/gridlock/sim.nim:266-281`.*

The code is what the note's own invariant requires, so nothing changed. §Parcels draws **one**
canonical sequence `D[k]` and gives fleet `j` `mirror_j(D[k])` "so the four demand streams are
congruent" — the note's §Tests item 3 states that congruence as a required assertion, and
`tests/test_parcels.nim:30-48` asserts it, including that each fleet's depot-to-destination
distance is identical across the four fleets. Step 3's phrase "that fleet's next canonical index
`k`" is the outlier: a per-fleet cursor would break congruence the first time a fleet at
`backlogMax` skipped an order, because from then on fleet `j` would be serving a different index
than its mirror. Step 3 also says the skipped fleet gets "nothing" — which is exactly what
`issueOrders` does with its `continue` at the cap. Implementing the per-fleet reading would
falsify the note's fairness argument and an existing test; that is a design decision for the
author, not a fix.

### F24 — plazas moved off the note's example coordinates
*Advisory, disclosed deviation. Data: `data/gridcity.cityspec.json` (four `disc` pieces, r 30).*

Verified independently and left alone. `margin_px` 64 + `node_spacing_px` 112 puts grid lines at
64, 176, 288, 400, 512, 624, 736, 848, 960. The note's example disc `{cx: 512, cy: 512, r: 34}`
spans 478–546, which straddles the line at 512 — it would fail the note's own rule that scenery
never overlaps a lane's cells and the test that pins it (`tests/test_city.nim:51-69`, ±10 px of
every grid line). The shipped four discs span 426–486 and 538–598: clear of 400±10 and 512±10, and
mirror-invariant under both axes (`tests/test_city.nim:47-49`). The deviation is what makes the
note's stated invariant achievable.

---

## Carried from the first fixer leg (verified from each sha's diff)

- **F2 `d9ea8c6`** — `stepTick` no longer gates `gridlockWatch` on `tick mod TargetFps`; the
  240-tick per-district cooldown in `rules.nim` is now the only limiter, as the note states.
  *(no checklist item; event granularity)*
- **F4 `62f7aff`** — `routeStartFailure` added and applied where a replan lands
  (`replanStep`), reported through `invariantFailure`; step 14's fifth guard exists. Test plants a
  route that does not start at the van's own node. *(item 2, correctness)*
- **F6 `e957810`** — `applyDecision` takes the turn loop's index instead of `sim.turn`, which
  `installPlans` had not yet advanced; `fallback` events are dated with the turn their plans are
  for. *(item 8 — phase 60 can count fallbacks by turn)*
- **F7 `80f85b7`** — `decideAll` times each batch and stamps `latencyMs` on every parsed plan (and
  the turn's total on a fallback plan); `plan` events no longer all read 0. *(item 8's recording)*
- **F8 `0cf410d`** — `client.turnBudgetSeconds` is now consumed: each attempt is clamped to what
  is left of the 22 s turn budget and a retry that cannot finish inside it is dropped for the
  scripted plan. The 14/6 deadlines are unchanged and still pinned. *(item 5 — bounded waits)*
- **F9 `0a346be`** — `effectiveScriptNow` degrades a seat that connected and dropped to
  `dispatcher` for as long as it is away, reviving on reconnect; the turn loop reads it. Test walks
  drop and reconnect. *(item 5 — no LLM spend on an absent seat; item 8)*
- **F10 `c74ca7a`** — the player's `DefaultPrompt` is gone; a container with neither
  `PLAYER_PROMPT` nor `PLAYER_SCRIPTED` registers `scripted: "dispatcher"`, as README, PROTOCOL and
  the note all say. *(item 12's policy contract)*
- **F11 `1ddb7da`** — the duplicate `register` on `welcome` is gone; test asserts exactly one
  `socket.send(` in the player and that it precedes the receive loop. *(item 12)*
- **F12 `aca5615`** — a credential-less LLM seat's plan is recorded `psFallback`, so
  `results.fallback_turns` counts a seat that never played its own policy. *(item 8)*
- **F13 `f27ff29`** — the transcendental grep now walks every `src/gridlock/*.nim` (≥19 modules),
  keeping the narrower `float` scan on the step path. *(item 2 — cross-build determinism)*
- **F14 `feafb00`** — `extractJsonObject` and the three response-body heads cut on runes
  (`clipRunes`/`cleanLine`), never bytes. *(item 9)*
- **F15 `ea9a952`** — `#btn-loop` is wired (playback restarts at the end); `#btn-skip` and
  `#btn-spoilers`, whose lull machinery this build does not ship, are hidden in CSS so no visible
  control is inert. The remaining ids render nothing and keep their names. Test: "no visible
  transport control is a no-op". *(item 11)*
- **F16 `15b7996`** — `#btn-back` seeks one tick back and `#btn-fwd` seeks +5 s, the transport's
  inherited meanings, instead of "seek 0" and "speed 16". *(item 11)*
- **F18 `be0b78f`** — `tools/ci/viewer_smoke.mjs` is now byte-identical to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff -q` → identical), including `--soak`
  and the playback-freeze check. *(item 13)*
- **F20 `243f5f5`** — the game `Dockerfile` sha256-checks the nimby asset it downloads, like
  `Dockerfile.replay-viewer` does. *(item 12 — reproducible image)*
- **F21 `b732790`** — `events_last_turn`'s lower bound is `sim.turn * turnTicks`, so the window is
  the turn that just played rather than that turn plus the one before it. *(item 4/8 — what a seat
  is told)*
- **F25 `c864e15`** — `tools/tune_baselines.nim` sweeps the real `dispatcher` (every constant is a
  field of `DispatcherTuning`, defaults exactly what shipped), across three loads × three seeds,
  135 full-factorial tunings + 42 coordinate steps + a held-out-seed re-run; `tools/tuning/
  dispatcher_grid.{md,json}` is that run's output and `tests/test_baselines.nim` asserts the
  shipped constants are the committed grid's winner. Digests and the golden fixture unchanged.
  *(item 7 — "tuned with a grid harness, not guessed", the review's one Could-not-determine)*

---

## NOTED (not fixed)

- The `test` job still prints two `[SKIPPED]` lines (debug and release) for the bundle case. That
  runner has no emsdk, so the bundle cannot exist there; the assertion is now gated in
  `viewer-native` instead, where it passes against the real artifact. Removing the skip entirely
  would mean building the wasm bundle twice per run.
- The review's other two *Could not determine* items are unchanged and unchangeable from here:
  `curly.makeRequests` honouring its timeout (the package is not vendored in this sandbox — F8's
  outer deadline now bounds the turn even if it does not), and hosted wall-clock behaviour, which
  only phase 60's real episode timings can settle.
- `jam_index`'s first `heat` event after a turn boundary is computed over a one-tick window and
  reads low (F3). Documented rather than fixed, for the reason given above.
