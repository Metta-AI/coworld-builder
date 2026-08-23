# r1 review — gridlock

Repo: `Metta-AI/cogame-gridlock`, reviewed at **`4b74806497a81972ba5b60a8af53ed8062a4f716`** (current
`main` head; matches the sha the brief named). Clone: `/tmp/cogame-gridlock`.
Design note: `/workspace/coworld-builder/runs/2026-08-23-gridlock/design.md`.
Starter compared against: `/workspace/starters/coworld-ctf` (paintbot), read-only mount.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–13 + the
simultaneous-decision batching rule). Files opened: **51** (21 `src/`, 4 `replay-viewer/`,
5 `client/`, 13 `tests/`, 3 workflow/Docker, 5 tools/manifest/data). CI evidence: run
**32635065143** on `main`, conclusion `success`, jobs `test` (97183459816), `docker-smoke`
(97183459700), `wasm-viewer` (97183629937).

**Blocking findings: 0.** Every item on the acceptance checklist was traced to code or to cited CI
output and holds. Twenty-four non-blocking observations follow, each with `file:line`; one checklist
sub-clause (item 7's "tuned with a grid harness") has no artefact in the tree and is recorded under
*Could not determine*.

Labels used below: **observed** = I read the lines and they say this; **inferred** = I reasoned from
the lines; **untested** = would need a run to settle.

---

## Blocking

None.

Each checklist item and where I verified it is listed under *Traced and consistent* below, including
the ones the brief singled out (14-step resolution order, decision path, waits and bounds, rune
truncation, replay writer, viewer re-derivation, viewer pairing, load markers, manifest/`num_agents`,
two name spaces, tests, `tools/ci/` scaffold).

---

## Non-blocking

### Sim / resolution order

**F1 — the keyframe is written at the *top* of the tick (note's step 12 → code's step 0).**
*[touches item 2 · advisory]*
- Where: `src/gridlock/sim.nim:438-457` (`stepTick`), header comment `src/gridlock/sim.nim:6-17`.
- Observed: `stepTick` opens with `if sim.tick mod TargetFps == 0: recordKeyframe(sim)` (`:439-440`)
  and only then runs orders → loading → dispatch → move → service → replans → stats. The note's
  §"Resolution order" numbers the keyframe **12**, after congestion statistics. The module's own
  header renumbers it `0` and says so explicitly.
- Consequence (inferred): a keyframe at tick `t` digests the state *entering* `t`, not leaving it.
  The seek snapshot is taken at the same phase (`installPlans`, `src/gridlock/sim.nim:259-260`), so
  snapshot and keyframe at the same tick agree — `tests/test_determinism.nim:72-89` asserts exactly
  that, and the viewer re-runs the same `stepTick`, so the re-derivation is unaffected. This is an
  ordering deviation from the note, not an inconsistency in the code.

**F2 — `gridlock` events are evaluated every 24 ticks, not every tick.** *[advisory]*
- Where: `src/gridlock/sim.nim:453-454`; `src/gridlock/rules.nim:129-161`.
- Observed: `if sim.tick mod TargetFps == 0: gridlockWatch(sim)`. `gridlockWatch` counts lanes with
  `q >= laneCells` per district and requires ≥ 4 plus a 240-tick per-district cooldown
  (`rules.nim:133-141`). The note (step 11) states the condition without a sampling period ("If four
  or more lanes … are simultaneously at `laneCells`"), with only the one-per-district-per-240-ticks
  cap. `jam`/`jam_clear` *are* checked every tick (`sim.nim:452`, `rules.nim:107-127`).
- Consequence (inferred): a gridlock lasting under 24 ticks can go unrecorded. Nothing in the
  checklist covers event granularity.

**F3 — `jam_index` and `districts_heat` are measured over the turn *so far*, not a fixed 240-tick
window.** *[advisory]*
- Where: `src/gridlock/rules.nim:15-23` (`resetTurnWindow`), `:25-49` (`accumulateStats`), `:73-103`
  (`refreshHeat`); called from `src/gridlock/sim.nim:220` and `:455-456`.
- Observed: the accumulators are cleared at every `installPlans`, and `refreshHeat` divides by
  whatever has accumulated since. At the first refresh of a turn the window is 48 ticks, at the last
  it is 240. The note says "over the previous 240 ticks" (§view) and "measured over the previous
  turn" (`districts_heat`). The repo's own `docs/PROTOCOL.md` says "over the previous turn window",
  i.e. the shipped docs match the code and the design note is the outlier.

**F4 — four of the note's five invariant guards are implemented; a fifth guard was added.**
*[advisory]*
- Where: `src/gridlock/rules.nim:163-189`.
- Observed: two-vehicles-in-one-cell (`:179-180`), off-graph lane (`:172-173`), off-graph cell
  (`:174-177`), backlog above cap (`:185-186`), delivered counter decreased (`:187-188`), plus a
  cell-index-desynchronised guard (`:182-183`) that the note does not list. The note's step 14 also
  names "a route whose first lane does not start at the vehicle's node after a completed replan" —
  no such check exists in this proc or elsewhere (`grep` over `src/gridlock/`).
- Consequence (inferred): a stale-route condition is *handled* rather than faulted — `nextLaneOf`
  falls back to `cheapestOutgoing` (`src/gridlock/traffic.nim:111-127`), which is the note's own
  documented behaviour in §Routing, so the missing guard is for a state the router repairs anyway.

**F5 — one shared canonical destination cursor, not a per-fleet cursor.** *[advisory]*
- Where: `src/gridlock/sim.nim:266-281`.
- Observed: `issueOrders` reads `sim.destSchedule[sim.destCursor]` once and advances the cursor once,
  then gives every fleet `mirror_j` of that single canonical node, `continue`-ing past any fleet at
  `backlogMax`. The note says "destination = `mirror_j(D[k])` for **that fleet's** next canonical
  index `k`", which reads as a per-fleet cursor.
- Consequence (inferred): a fleet that skips an order at the cap loses that index permanently rather
  than deferring it. The four fleets therefore stay exactly congruent tick-for-tick (which is what
  the note's fairness argument wants); a per-fleet cursor would let them drift apart after a cap hit.
  `tests/test_parcels.nim` asserts the mirror congruence, not the cursor discipline.

**F6 — `fallback` events carry the *previous* turn number from turn 1 onward.** *[advisory]*
- Where: `src/gridlock/server.nim:139-146` (`applyDecision`), called at `:257` **before**
  `runTurn` → `installPlans`; `sim.turn` is only ever assigned in
  `src/gridlock/sim.nim:205`.
- Observed: `newEvent(seFallback, gs.game.tick, gs.game.turn, …)` runs while `sim.turn` still holds
  the previous turn's index (the tick `t` is correct). For turn N ≥ 1 the emitted record is
  `{"t": N*240, "turn": N-1}`. The `budget_guard` event at `:235-236` passes the loop's own `turn`
  and is correct.
- Consequence (inferred): phase 60 counting fallbacks by `turn` would attribute them one turn early;
  counting by `t` or by seat is unaffected. `results.fallback_turns` / `fallback_causes`
  (`src/gridlock/rules.nim:268-273`) are per-seat totals and are correct.

**F7 — `latency_ms` is never measured; every recorded plan carries 0.** *[advisory]*
- Where: `src/gridlock/plan.nim:28`, `:165`; `src/gridlock/sim.nim:244`;
  `src/gridlock/replay.nim:54`.
- Observed: `latencyMs` is initialised to 0 in `defaultPlan()` and *reset* to 0 in `repairPlan`; a
  full grep of `src/` finds no assignment other than `planFromJson` reading it back out of a replay.
  `decideAll` (`src/gridlock/llm.nim:293-342`) never times an attempt. The note's replay example and
  the `plan` event table both carry `latency_ms` (example `4120`), and `tests/test_replay.nim:21`
  plants the value by hand rather than through the engine.

**F8 — there is no separate 22 s outer per-turn deadline; the bound is 14 s + 6 s.** *[touches
item 5 · advisory]*
- Where: `src/gridlock/llm.nim:31-32`, `:308-318`; `src/gridlock/server.nim:225-284`;
  `src/gridlock/startup.nim:53-58`.
- Observed: `decideAll` loops `for attempt in 0 .. 1` and passes `FirstAttemptSeconds` (14) then
  `RetryAttemptSeconds` (6) to `runBatch` → `client.curl.makeRequests(batch, timeoutSeconds)`
  (`llm.nim:284`). `cfg.turnBudgetSeconds` (22.0) is consumed **only** by
  `budgetGuardEngaged(elapsed, turnBudgetSeconds, wallClockBudgetSeconds)` (`server.nim:230-231`,
  `startup.nim:53-58`); no code wraps the turn in a 22 s deadline. The note's §Decisions lists "one
  outer per-turn deadline of 22.0 s" among the bounded waits.
- Consequence (traced): the wait is still explicitly bounded — 14 + 6 = 20 ≤ 22 — which is what
  checklist item 5 requires, and `tests/test_engine.nim:103-124` pins the two deadlines and the
  two-attempt cap. The missing wrapper only matters if `makeRequests` were to ignore its timeout
  (untested here; CI's `test` job exercises the `batchOverride` seam, not libcurl).

**F9 — a mid-match disconnect does not degrade the seat to `dispatcher`.** *[advisory]*
- Where: `src/gridlock/roster.nim:67-73` (`effectiveScript`); `src/gridlock/server.nim:130-137`
  (`seatRequestsLocked`); `:446-453` (close handler).
- Observed: the close handler clears `seats[slot].connected`, but `effectiveScript` — the only thing
  `seatRequestsLocked` consults — branches on `scripted` and on whether the stored prompt is empty,
  never on `connected`. A seat that registered with a prompt and then dropped keeps being sent to the
  LLM for the rest of the match. The note (§Decisions) says "A seat that disconnects mid-match keeps
  playing: its plan source degrades to `dispatcher` and revives on reconnect", and §Tests item 9
  lists "a mid-match disconnect degrades to `dispatcher` and revives on reconnect" as an assertion.
- Observed: `tests/test_engine.nim` contains no such test (its "seats that misbehave" suite covers
  no-shows, tokens and prompt truncation only, `:202-252`).
- Consequence (inferred): no hang and no unactuated fleet — the seat keeps a plan either way — but
  the described degradation is neither implemented nor tested.

### Decision path / player

**F10 — the player binary substitutes a default *prompt* when neither env var is set, so such a seat
becomes an LLM seat.** *[advisory]*
- Where: `src/gridlock_player.nim:15-24` (`DefaultPrompt`), `:34-37`.
- Observed: `if strutils.strip(prompt).len == 0 and scripted.len == 0: prompt = DefaultPrompt`. The
  note says twice that "A seat that sets neither defaults to `PLAYER_SCRIPTED=dispatcher`"
  (§Decisions, §Server). The **server** side does implement that default
  (`src/gridlock/roster.nim:70-71`: empty prompt ⇒ `skDispatcher`), but the player never sends an
  empty prompt.
- Consequence (traced): certification and the docker smoke are unaffected — the manifest's only
  player entry sets `PLAYER_SCRIPTED=dispatcher`
  (`coworld_manifest_template.json` `player[0].env`) and `tools/ci/docker_smoke.sh:165-178` feeds
  exactly that env to every container. A container launched with neither variable would consume LLM
  calls instead of running scripted.

**F11 — the player sends its `register` frame twice.** *[advisory]*
- Where: `src/gridlock_player.nim:67` (immediately after connect) and `:97` (again on `welcome`).
- Observed: `applyRegistration` is idempotent (`src/gridlock/roster.nim:36-59`), so the second frame
  overwrites identical values. The note says the player "sends exactly one text frame";
  `tests/test_startup.nim` asserts the frame's *content*, not its count.

**F12 — a no-credentials seat's plan is recorded with `source: "scripted"`, not `"fallback"`.**
*[touches item 8 · advisory]*
- Where: `src/gridlock/llm.nim:299-307`.
- Observed: when `client.disabled`, an LLM seat gets `scriptedPlan(..., skDispatcher)` — whose source
  is `psScripted` (`src/gridlock/baselines.nim:36-37`) — **and** a `FallbackRecord` with
  `cause: fcNoCredentials`. The `fallback` event is therefore written to the replay
  (`server.nim:140-146`) and `results.fallback_causes[seat].no_credentials` increments
  (`server.nim:141`), but `results.fallback_turns` does not (it counts `psFallback` plans only,
  `server.nim:147-149`) and the `plan` event reads `scripted`.
- Consequence (traced): the checklist's "the fallback is recorded so phase 60 can count it" is
  satisfied — the `fallback` event and the cause histogram are both present. The two-attempt path
  *does* set `psFallback` (`llm.nim:339-342`), so this only affects the credential-less case.

**F13 — the no-float source guard covers three modules, not `src/gridlock/*.nim`.** *[advisory]*
- Where: `tests/test_traffic.nim:7-14` (`StepPathModules` = `graph.nim`, `traffic.nim`,
  `parcels.nim`; `BannedCalls`), `:167-206`.
- Observed: the note's §Tests item 2 says "grep `src/gridlock/*.nim`". `rules.nim` — whose
  `accumulateStats`, `jamWatch`, `gridlockWatch` and `refreshHeat` all run inside `stepTick` — is not
  in the list, and it does import `std/math` (`src/gridlock/rules.nim:10`) and use `float` and
  `round` in `meanTripSeconds` (`:219-223`). The test does separately scan the `stepTick` body itself
  (`tests/test_traffic.nim:177-187`).
- Verified by reading: every per-tick proc in `rules.nim` is integer-only; the float use is confined
  to `meanTripSeconds`, which is called from `resultsJson` (`:260`) and never from the step path or
  the digest (`src/gridlock/state.nim:45-62` hashes integers and the u64 PCG state only). So the
  determinism property holds; the *guard* is narrower than the note describes.

**F14 — `extractJsonObject` byte-slices the error head.** *[touches item 9 · advisory]*
- Where: `src/gridlock/plan.nim:41-45` — `head = head[0 ..< 160]` on a raw model reply.
- Observed: that message becomes `error.msg` in `decideAll`, which passes it through
  `cleanLine(failure, MaxDetailRunes)` (`src/gridlock/llm.nim:336`) before it reaches
  `fallback.detail`. `cleanLine` iterates `text.runes` and re-emits `$rune`
  (`src/gridlock/types.nim:246-255`), so a byte-split multi-byte sequence is re-encoded as valid
  UTF-8 rather than propagated — the recorded string is valid UTF-8 (inferred from Nim's
  `fastRuneAt` bounds handling; not exercised by a test with invalid input). It is nonetheless the
  one byte-index slice on a path that can reach the replay. Two further byte slices exist on
  response bodies (`src/gridlock/llm.nim:239`, `:247`, `:252`), which reach the same `cleanLine`.

### Viewer

**F15 — thirteen inherited chrome ids are present in the markup but nothing ever writes to them.**
*[touches item 11/13 · advisory]*
- Where: `client/replay_broadcast.html:255` (`#ffwd-mini`), `:260` (`#jamflash`), `:276-278`
  (`#momentum`, `#lulls`, `#scrub-win`), `:287-289` (`#btn-loop`, `#btn-skip`, `#btn-spoilers`),
  `:292-293` (`#ffwd-chip`, `#win-chip`), `:302` (`#ec-replay`), `:304-307` (`#lockerroom`, `#lk-*`).
- Observed: a grep for each id across `client/chrome_common.js`, `client/broadcast_core.js` and
  `replay-viewer/static_replay.js` returns **0** references for all thirteen. `#mmwarn` is driven by
  CSS (`client/replay_broadcast.html:153`, `html[data-replay-mismatch-tick] #mmwarn{display:block}`)
  and does work. `tests/test_viewer.nim:140-142` asserts only that the ids exist in the markup.
- Against the note: readout 8 requires `#momentum` re-purposed to plot four delivery curves plus the
  jam index, `gridlock`/`jam`/`deliver`-burst ticks marked on the scrub bar, loop, lull-skip and
  spoilers; readout 5 requires the `skipLulls`/`lullSpans`/`#btn-skip`/`#ffwd-chip` machinery with
  `#clock-caption` reading `CITY FLOWING — 16×`. None of that machinery exists. The builder disclosed
  "`#momentum` curves declared but not drawn"; the observed scope is larger — the whole lull/marker
  layer and three transport buttons.

**F16 — two transport buttons are wired to something other than their inherited meaning.**
*[advisory]*
- Where: `client/chrome_common.js:452-458` (`#btn-back` → `core.seek(Math.max(0, chrome.meta ? 0 : 0))`,
  i.e. unconditionally seek 0) and `:459-462` (`#btn-fwd` → `core.setSpeed(16)`).
- Observed: the note's readout 8 lists "back one tick" and "+5 s". `#btn-restart` (`:448-449`)
  already seeks 0, so `#btn-back` duplicates it.

**F17 — the gridlock district overlay is drawn on the wasm canvas, not into `#jamflash`.**
*[advisory]*
- Where: `client/broadcast_core.js:322-334` (`drawFlash`, 48-frame hatched district rect) and
  `:423-430` (armed from a `gridlock` event). `#jamflash` (`client/replay_broadcast.html:260`) stays
  empty.
- Observed: the note's readout 4 asks for the overlay "in `#jamflash`". The visual ships; the element
  named for it does not carry it. The `#bannerlane` half of readout 4 *is* implemented
  (`client/chrome_common.js:338-349`), as is the `meter`-held banner line (`:78-81`).

**F18 — `tools/ci/viewer_smoke.mjs` is not the current builder template.** *[touches item 13 ·
advisory]*
- Where: `tools/ci/viewer_smoke.mjs` (451 lines) vs
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (528 lines).
- Observed: the repo's copy is an earlier revision — it lacks the `--soak` option and the
  playback-freeze check added to the template in coworld-builder commit `b735c07`
  ("cogball: 80 close — LEARNINGS, `--soak` template fold", 2026-08-23 09:50 UTC). The repo's first
  commit is 2026-08-23 10:45 UTC, i.e. the template already carried `--soak` when the repo was
  scaffolded. Diff is additive-only in the template's favour: `--soak` parsing, `pageErrors`
  collection, the three-sample soak block, and `if (!loaded || playFailure)`.
- Against the checklist: item 13 requires the `Load the bundle in a real browser` step to run and be
  green, which it did (see *Traced and consistent*, item 13) — the step passes `--timeout 90` and no
  `--soak` in either version (`.github/workflows/ci.yml:293-309`), so the missing option changes
  nothing about what CI actually asserted. The note says the file is taken "verbatim"; it is not the
  current verbatim file. Recording it so the judge can weigh it; I do not read it as falsifying
  item 13 as written.

**F19 — the native half of the viewer test skips when no bundle is present.** *[touches item 1 ·
advisory]*
- Where: `tests/test_viewer.nim:203-219` — `if not fileExists(bundle / "gridlock_replay.js"): … skip()`.
- Observed: in CI's `test` job the bundle is absent, so the case logs "no built bundle in
  dist/static-replay-viewer; ci.yml's wasm-viewer job is the gate for the browser half" and reports
  `[SKIPPED]` (run 32635065143, job 97183459816). This skip was present in the initial commit — the
  only commit that touched `tests/` (`git log -p -- tests/` shows one commit, `9cdfae6`) — so it is
  **not** a test loosened during this run, and item 1's second half is clean. The browser half did
  execute in `wasm-viewer`.

### Packaging / docs

**F20 — the game `Dockerfile` pins nimby by version URL but does not sha256-check it.** *[advisory]*
- Where: `Dockerfile:18-30` (curl → chmod, no checksum) vs `Dockerfile.replay-viewer:14-18`
  (`echo "3b3084…  /usr/local/bin/nimby" | sha256sum -c -`).
- Observed: the note's §Packaging says the game image uses "nimby pinned by sha256". Versions also
  differ by design layer: 0.1.26 in `Dockerfile` and `.github/workflows/ci.yml:35`, 0.1.27 in
  `Dockerfile.replay-viewer` (which is what the note pins for the viewer image). `AGENTS.md` says
  ci.yml's pins mirror the Dockerfile build stage, and they do.

**F21 — `events_last_turn` spans the last *two* turns.** *[advisory]*
- Where: `src/gridlock/view.nim:88-98`.
- Observed: `lower = max(0, (sim.turn - 1) * turnTicks)`. `buildView` is called from
  `seatRequestsLocked` (`src/gridlock/server.nim:130-137`) *before* `installPlans` advances
  `sim.turn`, so at the start of turn N, `sim.turn == N-1` and `lower == (N-2)*240` — the window
  covers turns N-2 and N-1. Capped at 6 lines, newest first.

**F22 — the arterial second discharge pulls a van forward outside the movement step.** *[advisory,
implementation detail not described by the note]*
- Where: `src/gridlock/sim.nim:406-420`.
- Observed: for `k > 0` (arterials only, `dischargePerStep` = 2, `src/gridlock/graph.nim:114-115`),
  if the stop line is now empty the code promotes the van at `cells-2` into the stop line
  (`:411-418`) and crosses it, outside the `t mod moveTicks` gate. The note's step 7 says "discharge
  up to `dischargePerStep(lane)` vehicles … from the stop line", which cannot yield 2 without this
  promotion (one van per cell). The one-vehicle-per-cell invariant is preserved: the vacated cell is
  written `-1` before the occupant is re-indexed, and `tests/test_traffic.nim` asserts no cell ever
  holds two vans over a full run, plus the ≤2/≤1/0 discharge caps.

**F23 — the digest-sensitivity test perturbs by `+37 mod 101`, and the note's `±1` claim is not
achievable as written.** *[advisory; disclosed deviation, examined]*
- Where: `tests/test_determinism.nim:43-59`.
- Observed: the test changes `congestionWeight` on one seat, one turn, by `(w + 37) mod 101`, with a
  comment that the derived coefficients are coarse. Reading the cost model
  (`src/gridlock/graph.nim:122-136`), `jamTerm = (congestionWeight * occupancy * 24) div 100`: on an
  empty lane (`occupancy == 0`) the term is 0 for *every* weight, so a ±1 change provably cannot move
  a cost on any empty lane, and `replanQueue` moves only every 10 points of patience
  (`src/gridlock/plan.nim:242-244`). The note's §Tests item 6 ("a one-unit change in **any** single
  plan integer changes the final digest") is therefore not a true statement about this rule set; the
  shipped substitute is a weaker but honest claim. The golden fixture
  (`tests/fixtures/golden_digests.json`, 41 keyframes for seed 42 / 960 ticks) is compared, not
  regenerated, when present (`tests/test_determinism.nim:120-135`).

**F24 — plazas moved off the note's example coordinates.** *[advisory; disclosed deviation,
examined]*
- Where: `data/gridcity.cityspec.json:566-595` — four `disc` pieces at (456,456), (568,456),
  (456,568), (568,568), `r: 30`, replacing the note's single `{cx: 512, cy: 512, r: 34}`.
- Observed and checked arithmetically: node (4,4) sits at pixel (512,512)
  (`src/gridlock/types.nim:275-276`), so the note's example disc would cover the CENTRE intersection
  box and the lane cells running through it — which would fail the note's own rule that scenery
  "never overlaps a lane's cells" and the test that pins it
  (`tests/test_city.nim:52-68`, ±10 px of every grid line). The shipped four discs span
  x,y ∈ [426,486] and [538,598]; the nearest road corridors are at 400±10 and 512±10 — clear. They
  are also mirror-invariant under both axes (`src/gridlock/city.nim:114-134`,
  `tests/test_city.nim:48-50`). The deviation is sound and is what makes the note's stated invariant
  achievable.

---

## Traced and consistent

Checklist items, in order.

1. **CI green, no test loosened.** `gh run list -R Metta-AI/cogame-gridlock --branch main -w ci.yml`
   → run **32635065143**, `completed success`, push of `4b74806`. Jobs: `test` ✓ 16s (short because
   the nimby toolchain and nimcache came from the `actions/cache` hit — "Cache hit occurred on the
   primary key nimby-Linux-0.1.26-2.2.4-a97afe82…"), `docker-smoke` ✓ 1m30s, `wasm-viewer` ✓ 2m5s.
   The `test` job log shows **32** groups —
   all 16 `tests/*.nim` in debug **and** in `-d:release` — with no `::error::FAILED` line; the only
   `[SKIPPED]` is F19's conditional bundle case. `git -C /tmp/cogame-gridlock log -p -- tests/`
   returns a single commit (`9cdfae6`, the initial import): no assertion deleted, no tolerance
   widened, no test file removed during this run.
2. **Replay re-derivation, frame by frame, and the viewer derives from it.**
   `src/gridlock/replay.nim:293-302` (`rederive`) re-runs `initSim` + `installPlans` from
   `seed`+`city`+`seat_depots`+`plans` only; `tests/test_replay.nim:111-123` asserts every keyframe
   `t` and `d` and **`rederived.vehicleBytes == decode(vehicles_b64)`** byte-for-byte plus the final
   delivered counts. The wasm side runs the identical path
   (`replay-viewer/gridlock_replay.nim:81-99` → `player.advanceOneTick()` → packet built by
   `frameJson(player.sim, …)`, `src/gridlock/render.nim:87-128`), so the drawn lane occupancy `q` and
   van array `v` come from the re-derived sim, not from the recording; the recorded digest is
   compared per keyframe and surfaced as `gridlock_mismatch_tick`
   (`src/gridlock/replay.nim:230-242`, `:257-260`), which the shell turns into
   `data-replay-mismatch-tick` → `#mmwarn` (`replay-viewer/static_replay.js:81-86`,
   `client/replay_broadcast.html:153`). Backward seek off the in-memory turn snapshot lands exactly
   (`src/gridlock/replay.nim:268-291`; `tests/test_replay.nim:125-143` checks the mid-digest after a
   round trip).
3. **Static viewer.** `coworld_manifest_template.json` → `game.replay_viewer` =
   `{"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` exists, is committed
   `100755` (`git ls-files -s` → `100755 … tools/build_replay_viewer.sh`), keeps paintbot's four
   safety checks (absolute path, name, inside-repo, not a symlink, `:22-34`) and is asserted present
   *and* executable before use (`.github/workflows/ci.yml:225-236`). The only network call the bundle
   makes is `fetch(message.replayUrl)` in the worker
   (`replay-viewer/static_replay_worker.js:118-144`), URL taken from `?replay=`
   (`replay-viewer/static_replay.js:213-217`). No `/client/replay` pod path is declared anywhere in
   the manifest; the game server's `/client/replay` route
   (`src/gridlock/server.nim:462`) is the local-viewing route the note explicitly keeps and the
   starter also has (`/workspace/starters/coworld-ctf/src/ctf/server.nim:627,642,840`).
4. **Both name spaces.** Prompts/views/events carry only depot aliases: `FleetAliases` are indexed by
   **depot**, never by seat, at every emission site (`src/gridlock/view.nim:139,160`,
   `src/gridlock/sim.nim:242,253`, `src/gridlock/rules.nim:155`), and `describe`
   (`src/gridlock/events.nim:31-51`) names seats by index. `tests/test_view.nim:141-171` runs a whole
   scripted episode and asserts **no** string in any seat's view or any event body contains any name
   from `results.names`; `:173-189` asserts the seat→depot permutation is a permutation and varies by
   seed. Real names exist only in `replay.names.players` (`src/gridlock/replay.nim:79`),
   `results.names` (`src/gridlock/rules.nim:249`) and the viewer's meta packet
   (`src/gridlock/render.nim:42`) → scorebug/endcard (`client/chrome_common.js:118,232`).
5. **Degrade-never-hang, inside 60 % of 1200 s.** Every wait I could find and its bound:
   connect wait `while epochTime() < connectDeadline … sleep(200)`
   (`src/gridlock/server.nim:191-198`, bound `playerConnectTimeoutSeconds`, 90 hosted / 60 cert);
   LLM attempt 1 = 14 s and attempt 2 = 6 s, at most two attempts
   (`src/gridlock/llm.nim:308-318`); turn loop bounded by `turnsPerEpisode`
   (`server.nim:219`); spacing sleep bounded by `minTurnSpacingSeconds`
   (`server.nim:278-283`, `startup.nim:60-64`, and skipped when the client is disabled or no seat
   wants the LLM); done-broadcast 3.0 s (`server.nim:52,169`); shutdown grace 20.0 s
   (`server.nim:47,184`) *after* artifacts are written; engine hard stop
   `if epochTime() - gameStart > cfg.wallClockBudgetSeconds → endEpisode("deadline","wall_clock")`
   (`server.nim:268-273`); budget guard at `elapsed + 2*22 > 660` disables the LLM for all remaining
   turns and emits `budget_guard` (`server.nim:230-240`). No unbounded loop: the replan FIFO is
   drained under `routeBudgetPerTick` (`sim.nim:422-436`) and compacts (`traffic.nim:45-61`);
   Dijkstra terminates on a settled set (`graph.nim:155-172`). `validate()` refuses any config with
   `wallClockBudgetSeconds > 0.6 * episodeTimeoutSeconds` (`src/gridlock/config.nim:144-147`), and
   `tests/test_manifest.nim:96-105` asserts the same for every variant and the cert fixture (660 and
   420 ≤ 720). Worst case traced: the stop is checked after a turn, and the guard fires at
   elapsed > 616 s, so the overshoot after 660 s is at most one already-scripted turn plus the 3 s
   broadcast — artifacts land well under 720 s. Untested end-to-end at hosted latency.
6. **`num_agents`.** 4 in variant `default`, variant `rush` and `certification.game_config`;
   `len(certification.players) == len(certification.game_config.players) == 4` (verified by parsing
   the manifest). `config_schema.num_agents` is `integer, min 4, max 4, default 4`. The server
   refuses anything else at startup (`src/gridlock/config.nim:127-131`).
   `tools/ci/docker_smoke.sh:109-151` carries all four invariants plus the `SMOKE_SEATS` second
   declaration, each exiting non-zero with `SEAT-COUNT FAIL:`; `SMOKE_SEATS` default is `4`
   (`:54`). **`grep -n "SEAT-COUNT" ` over the full docker-smoke job log (job 97183459700) returns
   nothing**, and the job printed `game=gridlock seats=4 config={… "num_agents": 4 …}` and
   `smoke OK: seats=4 results=1100B replay=72881B reason=complete`.
   `tests/test_manifest.nim:11-37` re-asserts all of it natively.
7. **Scripted baseline plays a full legal episode.** `runScriptedEpisode`
   (`src/gridlock/sim.nim:511-520`) ends `complete`/`full_time`;
   `tests/test_perf.nim:26-38` runs the real 4800-tick all-`dispatcher` episode and asserts
   `game.tick == 4800` **and** `game.reason == "complete"`; the all-`beeline` jam-heavy table also
   completes (`:40-48`). Legality: `tests/test_baselines.nim` validates 500 pseudo-random views ×
   both baselines against the schema and checks the derived quantities stay in
   `replanQueue 3..13`, `activeCap 0..50`, `releasePerStep 1..6`, every lane cost > 0 and ≤ 1200,
   and asserts the ordering (`dispatcher` out-delivers `beeline`; all-`beeline` delivers strictly
   fewer parcels than all-`dispatcher` at the same seed). (Tuning provenance: see *Could not
   determine*.)
8. **LLM reply handling.** Tolerant: `extractJsonObject` finds the first `{`, walks a
   string/escape-aware depth counter and takes the outermost balanced object
   (`src/gridlock/plan.nim:38-70`) — prose prefixes and ``` fences both land inside it, pinned by
   `tests/test_plan.nim:18-28`; numeric strings, `"70%"`, floats and bools are accepted
   (`plan.nim:72-96`), `corridor`/`avoid` accept `[bx,by]`, `{"bx":…,"by":…}` and district names
   (`:105-143`). Exactly one retry with the "your previous reply was invalid" hint
   (`llm.nim:198-207`, `:308-318`; `tests/test_plan.nim:194-224` asserts two calls, deadlines
   `[14, 6]`, and that the retry can succeed). Then the `dispatcher` plan with `source: psFallback`
   (`llm.nim:339-342`) and a `fallback` event carrying `seat`, `attempt`, `cause`, `detail` into the
   replay (`server.nim:139-146`), plus per-seat `fallback_turns` / `fallback_causes` in the results
   (`rules.nim:268-273`).
9. **Rune-safe truncation.** `clipRunes`/`cleanLine` use `runeLen`/`runeSubStr` and never a byte
   slice (`src/gridlock/types.nim:238-255`). Applied at every string that reaches the replay:
   `note` ≤ 140 and `say` ≤ 32 (`plan.nim:196-201`), `policy` ≤ 48 (`roster.nim:57-58`),
   `fallback.detail` ≤ 200 (`llm.nim:336`), `prompt` ≤ 4000 via `runeSubStr`
   (`roster.nim:46-48`) and never written to the replay or results (grep: no `prompt` key in
   `replayJson`/`resultsJson`). Tests: `tests/test_plan.nim:114-131` puts a 4-byte truck emoji on the
   32nd rune of a `say`, asserts `runeLen == 32`, `validateUtf8 == -1`, and a `%*`/`parseJson` round
   trip; `tests/test_replay.nim:38-40` asserts the whole replay file is valid UTF-8
   (`validateUtf8(raw) == -1`) *before* parsing, with a non-ASCII `say` forced into the stream
   (`:16-19`); `tests/test_engine.nim:244-252` truncates a 4500-rune prompt of 3-byte runes.
10. **Manifest validates.** `game.docs` = `{"readme": {"type":"text","value": …5336 chars},
    "pages": [{"id":"rules.md","title":"Rules","content":{"type":"text",…8454}},
    {"id":"protocol.md","title":"Wire protocol","content":{"type":"text",…8463}}]}`;
    `game.protocols` carries **both** `player` (2635 chars) and `global` (1771), both
    `{"type":"text"}`. `tests/test_manifest.nim:126-155` asserts the shapes *and* that the inlined
    values equal `README.md`, `docs/RULES.md`, `docs/PROTOCOL.md` byte for byte.
    `results_schema.properties` is exactly the 27 keys `resultsJson` emits (`ResultsKeys`,
    `src/gridlock/rules.nim:313-319`), with `additionalProperties:false`, `reason` enum of 3 and
    `end_rule` enum of 4 — cross-checked by set equality in `tests/test_manifest.nim:106-124`.
    `episode_timeout_minutes: 20`, 5 tags, `$schema` present.
11. **Legible at 360 px.** `client/replay_broadcast.html:63-65`:
    `.plate .team-name,.plate-name{flex:1 1 auto;min-width:3.2em;overflow:hidden;
    text-overflow:ellipsis;white-space:nowrap}` — both selectors, exactly the checklist's rule.
    `@media (max-width: 640px)` at `:225-239` hides `#planbar`, `#viewpanel`, `.chiplabel` (the
    speed-chip labels), the fleet aliases/bars and the district grid, and reduces the feed to two
    lines. `--hudscale` is driven from the board width by
    `client/chrome_common.js:371-378` (`clamp(0.5, w/760, 1.6)`, `.tiny` under 420 px), and
    `tests/test_viewer.nim:150-172` pins all of it. CI's browser smoke rendered a four-plate scorebug:
    `"scorebug":"P1 Verde 0 P3 Copper 0 P2 Saffron 0 P4 Cobalt 0"`.
12. **Release order and scaffold.** `.github/workflows/coworld-release.yml` step order:
    `Build the Coworld manifest` (:153) → `Certify locally` (:167) → **`Upload the policies`**
    (:206) → `Upload the Coworld` (:304) → `Put the Coworld secret` (:342). All three workflows
    present. `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are committed `100755`
    (also asserted natively, `tests/test_manifest.nim:200-206`, and in CI before use,
    `ci.yml:166-174`, `:225-236`). `tools/ci/policies.json` defines four distinct policies, all
    `"run": "/bin/gridlock-player"`: two `PLAYER_PROMPT` champions (`gridlock-flowwright`,
    `gridlock-backstreet`) and two `PLAYER_SCRIPTED` fillers (`dispatcher`, `beeline`); **champion #2
    carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`**. The placeholder gate
    (`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files) matches nothing and exits 0; the
    four documented residue names (`<cow_id>`/`<sha>` in ci.yml's static-route comment, `<run_id>` in
    both artifact-readback recipes, `<name>:vN` in the submit policy description) are present and are
    expected. `tools/ci/docker_smoke.sh` differs from the builder template only in the three
    substitutions (`diff` shows 5 hunks, all `<slug>`/`<IMAGE>`/`<SEATS>` → `gridlock`/
    `coworld-gridlock`/`4`); `ci.yml` likewise.
13. **Viewer executes.** `wasm-viewer` `needs: docker-smoke` (`.github/workflows/ci.yml:212`), and
    the `Load the bundle in a real browser` step (`:293-309`) **ran** in job 97183629937 and printed
    `{"loaded":true,"ms":289,"clock":"00:39 TURN 0/4","scorebug":"P1 Verde 0 …","feed_lines":4}` plus
    `scrub readouts: 0%="00:39 TURN 0/4"  50%="00:17 TURN 2/4"  100%="00:00 TURN 3/4"`, against
    `dist/smoke/replay.json` — the replay `docker-smoke` produced in the same run. Not
    `continue-on-error`, not commented out. Markers: `data-replay-loaded="true"` is set in the
    `firstFrame` branch (`replay-viewer/static_replay.js:184-188` → `markLoaded()` at `:44-51`) as
    well as on `loaded` (`:192-196`), and `data-replay-error` is set inside `showFailure`
    (`:77`), with the `coworld-replay` bridge posting `loading` (`:42`), `ready` (double rAF,
    `:48-50`) and `error` (`:78`) — all from the shell's own code. **The pairing:**
    `replay-viewer/config.nims` carries no `MODULARIZE` and no `EXPORT_NAME` (`:43-55`, a
    line-for-line fork of the starter's file at
    `/workspace/starters/coworld-ctf/replay-viewer/config.nims` with the four renames), and
    `replay-viewer/static_replay_worker.js` uses `Module.onRuntimeInitialized` (`:202-216`) with
    `importScripts('./wire_constants.js','./broadcast_core.js','./gridlock_replay.js')` (`:256-257`)
    — the paintbot lineage on both halves, with a one-macrotask `setTimeout` defer so nothing calls
    an export before `callMain()`. `tests/test_viewer.nim:36-97` asserts both halves and the
    exported-symbol ↔ called-symbol correspondence; `Dockerfile.replay-viewer:69-71` re-greps
    `onRuntimeInitialized` and `importScripts` in the emitted bundle.
14. **Simultaneous batching.** `decideAll` builds one `requests` array over all open seats and issues
    it through a single `client.curl.makeRequests(batch, timeoutSeconds)`
    (`src/gridlock/llm.nim:272-291`, `:311-318`); nothing iterates seats with a per-seat call.
    `tests/test_engine.nim:31-66` records each seat's in-flight window through the `batchOverride`
    seam and asserts all four windows pairwise intersect, `batches == 1`, `sizes == @[4]`; `:67-84`
    asserts every turn of a whole episode batches exactly 4; `:86-101` asserts scripted seats never
    enter the batch.

Additional traces the brief asked for:

- **Resolution order 1–14** maps onto `stepTick` (`src/gridlock/sim.nim:438-457`) as: turn clock =
  `installPlans` (`:204-260`, plans installed, tie noise drawn in fleet-then-lane order, per-turn
  counters rolled, every on-road van enqueued, `turn_start` + one `plan` + one `meter` per seat
  emitted, snapshot taken); signals = pure function, no state (`graph.nim:104-112`); orders
  (`:441-442`); loading (`:443`, `loadTicks` countdown then route assignment, `sim.nim:283-304`);
  dispatch metering (`:444-445`, `activeCap`/`releasePerStep`/cell-0-empty gate,
  `sim.nim:306-329`); movement downstream-first cell 12→0 (`:446-447`, `traffic.nim:63-81`);
  intersection service in node order over approaches N,E,S,W (`:448-449`, `sim.nim:394-420`,
  `graph.nim:62-71`), 2 arterial / 1 local (`graph.nim:114-115`), red = 0 (`sim.nim:402-404`);
  spillback by construction (no step — one van per cell, blocked crossings simply not made,
  `sim.nim:380-381`, `traffic.nim:74-77`); pickup/delivery inside the discharge
  (`sim.nim:331-392`, including the blocked-onward-cell delivery bay at `:341-343`, own-depot
  absorption at `:364-371`, rival depots inert); replans capped at `routeBudgetPerTick`
  (`:422-436`); congestion statistics every tick (`rules.nim:25-49`), heat every 48
  (`sim.nim:455-456`); keyframe every 24 (see F1); seek snapshot per turn (`sim.nim:259-260`, in
  memory only — `snapshots` never appears in `replayJson`); end check
  (`sim.nim:496-504` + `endEpisode` `:459-490`, three `reason` values only).
- **Replay writer.** `src/gridlock/replay.nim:47-106` emits every documented top-level key with
  `protocol == "gridlock.replay.v1"` (`src/gridlock/types.nim:53`), the resolved config with tokens
  excluded (`src/gridlock/config.nim:152-182`), the city raw JSON pinned verbatim
  (`replay.nim:89`), `seat_depots`, `names.{players,aliases,policy_kinds,colours}`, the 80-record
  plan stream, keyframes with the u32 digest, `vehicles_b64` (u16 LE lane + cell + state, docked
  sentinel 65535, `sim.nim:191-197`), the event stream and the results document. Strict reader
  rejects a bad protocol, a non-permutation `seat_depots`, a `vehicles_b64` length mismatch, an
  out-of-range lane, truncated JSON and a missing key — each with a message, not a crash
  (`replay.nim:119-210`; `tests/test_replay.nim:149-186`).
- **Digest.** FNV-1a u32 over tick, every van's `(lane, cell, state, target, parcelId)`, every lane's
  occupancy, the four delivered counters, the four backlog sizes and both PCG words
  (`src/gridlock/state.nim:45-62`) — exactly the note's list, integer-only.
- **Two disclosed deviations verified sound beyond F23/F24:** `tests/test_server.nim` is static +
  unit (its header says so, `:1-11`) and pins the route registration order, the 403/409 responses,
  the Ping→Pong answer, the file://-only sinks and the artifact write order
  (`done` → `writeReplay` → `writeResults` → grace → `quit(0)`, `:60-80`); the live socket contract
  is proven by `docker_smoke` — one game container + 4 player containers on a shared network, which
  reached `reason=complete` with a 72 881-byte JSON replay in the cited run. The viewer chrome is
  authored to paintbot's architecture rather than byte-copied (`client/replay_broadcast.html` is 315
  lines against the starter's ~4 100), and all 55 inherited ids the note lists are present — see F15
  for which of them are inert.

---

## Could not determine

- **F25 — checklist item 7's "the baseline's parameters were tuned with a grid harness, not
  guessed."** *[item 7]* Nothing in the tree is a tuning harness: `tests/test_baselines.nim` asserts
  legality and an *ordering* (dispatcher > beeline; all-beeline total < all-dispatcher total at the
  same seed), which is evidence the two baselines are separated, not evidence the thresholds
  (`30 + jam` clamped 30..95, dispatch 100/80/60/45 at jam 35/55/75, spread 40/80 at 45, patience
  60/35 at 40 — `src/gridlock/baselines.nim:34-62`) were swept. The design note itself does not
  promise a grid harness for gridlock; it states the thresholds directly (§Scripted baselines). What
  would settle it: a committed sweep script or a run log under `runs/2026-08-23-gridlock/` showing a
  parameter grid and the delivered totals it chose from, or an explicit statement from the builder
  that the values were derived some other way.
- **`curly.makeRequests` honouring its timeout argument.** *[item 5, untested]* `runBatch` passes an
  `int` seconds value (`src/gridlock/llm.nim:284`); the package is not vendored in this sandbox, so I
  read the call site but not the implementation. The code compiles and runs in CI, so the signature
  matches; whether the deadline is enforced per-batch or per-request is not visible from here. CI's
  engine tests exercise the `batchOverride` seam, not libcurl. What would settle it: a live episode
  with a hung endpoint, or reading `curly`'s `makeRequests` at the pinned revision in `nimby.lock`.
- **Hosted wall-clock behaviour.** The 490 s expected / 660 s stop arithmetic is traceable from the
  constants (see item 5 above) but has only been exercised offline — the docker smoke ran with no
  credentials, so every turn fell back instantly (episode wall clock 25 s, 10:56:10 → 10:56:35). What
  would settle it: phase 60's hosted episode timings and the `turns_llm` / `fallback_turns` numbers
  in its results document.
