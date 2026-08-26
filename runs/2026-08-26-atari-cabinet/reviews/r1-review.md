# r1 review — atari-cabinet

Repo: `Metta-AI/cogame-atari-cabinet`, reviewed at **`ac7eca8acfc2eadf316c5eb6eda9f84881a76fcf`** (`main` HEAD; cloned to `/tmp/cogame-atari-cabinet`).
Range: `b8875d8` (bootstrap) .. `ac7eca8` — 121 files, +26 002 lines.
Design note: `/workspace/coworld-builder/runs/2026-08-26-atari-cabinet/design.md` (identical copy in-repo at `docs/plans/2026-08-26-atari-cabinet-design.md`).
Starter for provenance: `/workspace/starters/coworld-ctf`.
Files read: 48 (all of `src/cabinet/*.nim`, both entrypoints, all 17 `tests/*.nim` + `tests/helpers.nim`, `replay-viewer/*`, `client/*`, `tools/ci/*`, `tools/build_replay_viewer.sh`, `tools/replay_summary.py`, `Dockerfile.replay-viewer`, all three workflows, `coworld_manifest_template.json`, `AGENTS.md`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision addendum).

CI evidence used below: `gh run list -R Metta-AI/cogame-atari-cabinet --branch main -w ci.yml` →
run **32984942130**, `workflow_dispatch`, headSha `ac7eca8…`, conclusion **success**, jobs `test` / `docker-smoke` / `wasm-viewer` all `success`. (Two earlier runs at the same sha — 32984632295 and the push run 32984636790 — are `startup_failure` with zero-length job durations, i.e. GitHub never started them; see "Traced and consistent".)

---

## Blocking

### r1-1 — [legibility] The worst-case renderer fixture ellipsizes 12 full-cap **remarks**, not labels, and the job is green

- Where: `tools/ci/renderer_fixture.html:186-201`; evidence in CI run 32984942130, job `wasm-viewer`, step "Render the worst-case text fixture at 360 / 620 / 1280 px".
- Observed: the fixture's block 4 lays out the 160-rune stance **`note`** on all four seats as one-line feed rows at board width, then shortens whatever does not fit:
  ```html
  186    // 4. the match feed's worst row: a full-cap note. …
  194      var text = row;
  195      while (ctx.measureText(text).width > width - 16 && text.length > 4) {
  196        text = text.slice(0, text.length - 2);
  197      }
  198      if (text !== row) text = text + '…';
  ```
  The CI log for that step reports:
  ```
  canvas text: 22 drawn, 0 never inside the canvas (0 draws crossed an edge), 12 ellipsized (--strict-text-bounds)
    ellipsized: "RED: RED is on one life and its wall is down to two bricks; "
    ellipsized: "BLUE: BLUE is on one life and its wall is down to two bricks"
    …(12 rows: 4 seats × 3 widths)
  ```
  Every one of the 12 ellipsized strings is the seat's `note` — a sentence — not a nameplate. `never_inside` is 0, so the gated number passes and the step is green.
- Checklist item: **15**, third bullet, verbatim: *"Ellipsis is a design choice for **labels** (a card name in a 52 px card) and a defect for **sentences**. If `ellipsized` counts a remark rather than a nameplate, the box is too small — widen the band, do not shorten the text."*
- Why blocking: the only CI gate that draws LLM-authored text at full cap reports that every full-cap remark it draws is cut. The fixture's own contract (`tools/ci/renderer_fixture.html:31-33`, "It self-checks its own string lengths first") is satisfied on the *input* side but the *output* is truncated, so the fixture passes while demonstrating the exact defect item 15 names. What would settle it differently: a reserved band whose height is sized from `MaxNoteRunes` measured in the drawing font, with wrapping rather than a `slice`, and `ellipsized == 0` for the note rows.
- Note (observed, not inferred): the truncation loop at line 196 cuts by JS UTF-16 code units (`text.slice`), so it can in principle split the surrogate pair of the `🎯` the fixture injects at `renderer_fixture.html:76,79`. In the shipped strings the emoji is followed by filler padding (`padRunes`, line 62-68), so no run has actually split it; this is a property of the fixture, not of the server's rune discipline, which is correct (see r1-24).

### r1-2 — [legibility] Nothing in CI probes the text the *shipped* renderer draws; the fixture is a re-implementation

- Where: `tools/ci/renderer_fixture.html:16-29` and `:48-218`; `src/cabinet/global.nim:599-662`; `.github/workflows/ci.yml:335-363`; CI run 32984942130, step "Load the bundle in a real browser".
- Observed, in three steps:
  1. The shipped board bakes every string — stance chips, speech bubbles, the ROM caption — into **sprites**, server-side, with pixie, and ships them over the sprite protocol:
     ```nim
     604    template bakeText(text: string, r, g, b: uint8, size: int): int =
     644      let spriteId = bakeText(label, tint[0], tint[1], tint[2], 22)
     653      emitObject(packet, placed, id, max(2, (MapWidth - baked.width) div 2),
     654        max(2, min(MapHeight - baked.height - 2, py)), 8_500, BoardLayer, spriteId)
     ```
     There is no `fillText` on the client for board text and there is no `client/renderer.js` in the repo at all (`find . -name 'renderer*.js'` → nothing).
  2. Consequently the real-bundle smoke reports `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. `ci.yml:348-349` states this explicitly: *"the shipped board composites in a Worker, which the fillText probe cannot see."*
  3. `tools/ci/renderer_fixture.html` therefore does not load any shipped renderer. It is a self-contained 220-line page that re-derives the layout by hand (`renderer_fixture.html:109-203`), importing nothing from `client/`, `replay-viewer/` or `src/`. Its bubble band constants (`BUBBLE_BAND_LO_CU = 92`, `:105-106`) are re-typed literals that happen to match `global.nim:62-63`; `tests/test_viewer.nim:198-206` asserts the literals are present in the fixture, not that they agree with `global.nim`.
- Checklist item: **15**, fourth bullet: *"A repo whose viewer draws LLM-authored text must therefore ship a worst-case renderer fixture: **a page that loads the real `client/renderer.js`**, hands it a frame built to hurt … Cite the step and its `canvas_text` line; a repo that draws model text and has no such fixture is a blocking `legibility` finding."*
- Why blocking: the combination is that item 15's whole class of coverage is absent. `canvas_text.total == 0` on the shipped bundle is, in the checklist's own words, *"not evidence of anything"*; and the fixture that exists tests a parallel hand-written layout, so a regression in `global.nim`'s bubble/chip placement (e.g. the missing right-edge clamp noted under "Could not determine") is invisible to every gate. `--strict-text-bounds` is present on both steps (`ci.yml:323`, `:363`), so the flag requirement of item 15 is met; the coverage requirement is not.
- What would settle it: a fixture that drives the actual text path — e.g. a Nim test that calls `global.addBoard` on a state with a full-cap `say`/`note` on all four seats and asserts every baked sprite's `(x, y, width, height)` lies inside `[0, MapWidth] × [0, MapHeight]`, plus a browser page that loads the real bundle against a synthesised replay carrying those strings.

---

## Non-blocking

### r1-3 — [timeout] `turnBudgetMs` is measured from before the inter-batch sleep, so the retry can be pre-empted and the real per-turn bound is ≈26 s, not 16 s

- Where: `src/cabinet/decide.nim:348-352`, `:401-412`, `:414-423`.
- Observed: `turnStart = getMonoTime()` is taken at line 350, **before** the rate floor:
  ```nim
  406    if open.len > 0 and engine.batchStarted and sim.config.turnSpacingMs > 0:
  407      let since = (getMonoTime() - engine.lastBatchStart).inMilliseconds.int
  408      if since < sim.config.turnSpacingMs:
  409        sleep(min(sim.config.turnSpacingMs, sim.config.turnSpacingMs - since))
  ```
  and the budget is only checked at the *top* of each attempt:
  ```nim
  419      if getMonoTime() - turnStart >= budget:
  420        for seat in open:
  421          result.add(fallbackRecord(turnIndex, seat, attempt + 1, "timeout", …))
  423        break
  ```
  With the shipped variant values (`turnSpacingMs` 12 000, `attempt1Ms` 9 000, `retryMs` 5 000, `turnBudgetMs` 16 000, manifest variants), a turn that sleeps 8 s and then times out attempt 1 at 9 s has consumed 17 s ≥ 16 s and **skips the retry**; a turn that sleeps 6 s and times out attempt 1 has consumed 15 s, passes the check, and then runs the 5 s retry for a 26 s turn. So (a) the single retry the design promises is intermittently unavailable in production, and (b) the "whole turn is wrapped in `turnBudgetMs`" claim is not what the code enforces.
- What the note says: §Decisions — *"the whole turn is wrapped in `turnBudgetMs = 16 000` (`attempt1Ms + retryMs = 14 000 ≤ 16 000`, asserted by §Tests 12)"*, with the 12 000 ms floor listed as a separate wait.
- Not blocking: every wait is still explicitly bounded (checklist item 5). The budget guard's own per-turn estimate is `(turnBudgetMs + turnSpacingMs + 999) div 1000 = 28 s` (`decide.nim:360-362`), which conservatively covers the real 26 s maximum, so the 660 s stop is not endangered.
- Side effect, same lines: when the budget pre-empts, the seat gets **two** `fallback` records for the turn — one at `:421` with `attempt = 2, cause = "timeout"` and one at `:491` with `attempt = 2` and a recomputed cause. Phase 60 counts fallbacks from these records.

### r1-4 — [correctness] The `+7`-index offset for two balls served in the same tick is never applied

- Where: `src/cabinet/sim.nim:26`, `:191-208`, `:549-559`.
- Observed: `serveBall(sim, index, offsetIndex)` applies the offset at `:195-196`, but the only call site is `sim.serveBall(index, 0)` at `:558`. `grep -rn 'serveBall(' src/` returns that one call. Both balls therefore draw independent directions from the seeded stream and are spawned at exactly `(ArenaHalf, ArenaHalf)` (`:198-199`).
- What the note says: §The game / Serves — *"When two balls are served in the same tick the second is offset by `+7` indices from the first."*
- Consequence: two balls can be served on the same tick with adjacent or identical direction indices from the same point. Deterministic and hash-stable either way; `SecondBallDirOffset` is dead code.

### r1-5 — [correctness] `near_miss` is declared everywhere and emitted nowhere

- Where: `src/cabinet/sim_types.nim:269` (`NearMiss` enum), `src/cabinet/events.nim:23` (`"near_miss"`), `src/cabinet/sim.nim:27` (`NearMissUu* = 12_000'i32`), `client/replay_broadcast.html:4349`.
- Observed: `grep -rn 'NearMiss\|near_miss' src/` finds the enum, the wire name and the constant; no `emitEvent(NearMiss …)` exists in `sim.nim` and `broadcast.nim:61-151` never emits `{"k": "near_miss"}`. The JS handler at `replay_broadcast.html:4345-4351` groups `near_miss` with the suppressed continuous kinds and returns `true` (no feed row) even if one arrived.
- What the note says: §Record and event vocabulary lists `near_miss` as a derived broadcast event ("the drama the game is made of"), and §Viewer readout 7 lists the feed line *"SO CLOSE — B2 grazed RED's bar"*.
- Consequence: that feed line can never appear.

### r1-6 — [correctness] `chase` picks `j = ±6` by side difference instead of running the 13-index aim search

- Where: `src/cabinet/control.nim:277-296`.
- Observed:
  ```nim
  288        let j =
  289          if effective == stChase:
  290            let diff = ((stance.aimAt - cabinet) mod CabinetCount + CabinetCount) mod CabinetCount
  292            if diff == 3: -6 else: 6
  293          else:
  294            sim.aimOffsetJ(cabinet, predictions[chosen].perSide[cabinet].along, stance.aimAt)
  ```
- What the note says: §The autopilot step 3 — *"`aim`, `chase` → for each of the 13 outgoing indices `j = −6 … +6`, walk the outgoing ray … take the **smallest |j|** that does"*. Only §Decisions' stance glossary describes `chase` as "the most aggressive aim … available", which the code's comment (`:283-287`) reads as always-tip. The two halves of the note disagree; the code follows the glossary.

### r1-7 — [correctness] The far paddle aims at the **near** paddle line's arrival, not `FarPaddleDepth`

- Where: `src/cabinet/control.nim:340-361`; `src/cabinet/control.nim:36-100` (`predictBall`).
- Observed: `predictBall` only ever records a crossing of `PaddleDepth`:
  ```nim
  71        if before > PaddleDepth and after <= PaddleDepth:
  74          result.perSide[side].along = localOf(side, nx, ny).along
  ```
  and the foozpong branch consumes exactly that value for the far bar:
  ```nim
  349        if prediction.perSide[cabinet].reaches:
  350          farTarget = prediction.perSide[cabinet].along
  ```
  `FarPaddleDepth` (340 000 µu) appears in `control.nim` nowhere.
- What the note says: §The autopilot step 7 — *"the same steps 1–5 against the second-smallest `arriveTick` ball **at `FarPaddleDepth`**"*. The far bar therefore tracks where the ball will be 20 cu *behind* it, which is a different along-position on every non-perpendicular trajectory.

### r1-8 — [correctness] The autopilot adds a "shadow vs committed" mode the note does not describe

- Where: `src/cabinet/control.nim:300-331`.
- Observed:
  ```nim
  309      let intercept = arrival.along - offset
  310      let shadow = localOf(cabinet, sim.balls[chosen].x, sim.balls[chosen].y).along
  311      let committed =
  312        if arrival.reaches and arrival.tick <= max(1, stance.leadTicks): intercept
  313        else: shadow
  ```
  Outside the `lead_ticks` window the bar shadows the ball's current along-projection instead of moving to the intercept.
- What the note says: §The autopilot step 4 — *"`c* = arriveAlong − off`, clamped to `±PaddleTravelHalf`"*, with `lead_ticks` entering only in step 5's divisor. The code's own comment (`:303-308`) explains the addition as what makes `lead_ticks 0` (spinner) arrive late.

### r1-9 — [correctness] `repairStance` replaces the whole stance on any single illegal field

- Where: `src/cabinet/decide.nim:292-317`.
- Observed: `validateStance` returns the *first* violation; if it is non-empty the code discards the parsed stance entirely and substitutes `bulwark`'s, keeping only `note`, `say`, `source`, `latencyMs`:
  ```nim
  312    var repaired = engine.bulwarkFor(sim, seat)
  313    repaired.note = stance.note
  317    stance = repaired
  ```
- What the note says: §Sim module — *"`repairMissingOrders` (retargeted: a missing field keeps last turn's value, else `bulwark`'s)"*, i.e. per field. The per-field repair does exist upstream in `stances.parseCabinetStance` (`stances.nim:249-328`), so an *absent* field is repaired as designed; only a *present but illegal* field triggers the wholesale substitution. Note that `parseCabinetStance` already sanitises `target_ball` and `aim_at` against the live/out tables (`:285`, `:292`), so this path is reachable mainly through a stale `previous` value.

### r1-10 — [correctness] Two mechanisms exist in the sim that the resolution order does not describe

- Where: `src/cabinet/sim.nim:406-413` (`releaseIndex`), `:469-500` (`containBall`).
- Observed (a): a gripped ball is released along `dl' = 16 − 2·(near − 4)`, i.e. aimed by the drive level in the releasing byte. §Resolution order 4.1 only says a held ball is force-released "as if `grip == 2`" and never specifies the outgoing direction; the mechanism is an addition, but it is the reason the release needs no extra replay record and it is symmetric across both builds.
- Observed (b): after every motion, `containBall` walks all four sides and, if the ball centre sits inside `BallHalf` of a side, either **concedes** (`:487-489`) or pushes the ball back to the wall face and reflects it (`:494-499`). This is a second concede path outside §Resolution order step 4.6 and a position repair the note's step 7 instead treats as a `fault/sim_fault` trigger ("a ball centre outside the arena"). The code's comment (`:470-476`) explains it as a corner-remainder guard. Deterministic and identical on both builds; the invariant guard at `:704-707` still fires for a centre genuinely outside `[0, ArenaSide]`.

### r1-11 — [correctness] Step ordering: the guard runs before the end checks and the hash after them

- Where: `src/cabinet/sim.nim:763-779`; `src/cabinet/server.nim:697-708`; `src/cabinet/replays.nim:294-299`.
- Observed: `step` does paddles → balls → `recomputeScore` (all four) → `guardInvariants()` (`:769`) → `aliveCabinets() <= 1` → `maxTicks`. The hash is written by the caller *after* `step` returns (`server.nim:708`), and `stepReplay` checks it in the same place (`replays.nim:298-299`).
- What the note says: §Resolution order 5 → 6 → 7, i.e. score → hash → end checks, with the invariant guard as the last of the end checks.
- Consequence: the final tick's `gameHash` carries `phase == GameOver`, `winnerCabinet` and `placement` (all of which `gameHash` mixes, `sim_state.nim:224/229/249`). Server and viewer agree because both call `gameHash` at the same point, so re-derivation is unaffected; the note's stated ordering is simply not what ships.

### r1-12 — [correctness] `last_standing` also fires when **zero** cabinets are alive

- Where: `src/cabinet/sim.nim:771-773`; `src/cabinet/sim_state.nim:71-74`.
- Observed: `if sim.aliveCabinets() <= 1: … finishGame(ReasonComplete, EndRuleLastStanding)`. Two balls can concede in the same tick (the ball loop at `:765-766` runs each ball independently, and `concede` at `:446-454` eliminates on the spot), so 2 alive → 0 alive in one tick is reachable. `assignPlacements` still produces a total order, so `results` stays well-formed, but the endcard reads "LAST CABINET STANDING" with nobody standing.
- What the note says: §End conditions — `complete`/`last_standing` when *"Exactly one cabinet still has `lives > 0`"*.

### r1-13 — [other] `RenderScale` is 1, not the 2 the note says is "kept unchanged", and `boardRenderScaleFor` was edited

- Where: `src/cabinet/global.nim:28-34`, `:107-120`; starter at `/workspace/starters/coworld-ctf/src/ctf/global.nim:1091`, `:1108-1113`.
- Observed:
  ```nim
   28    RenderScale* {.intdefine.} = 1        # starter: 2
  110    if mapWidth * mapHeight * RenderScale * RenderScale > MaxSupersampledMapPixels:
  ```
  (the starter's predicate is `mapWidth * mapHeight > MaxSupersampledMapPixels`). `predictedViewerRenderBytes(1000, 1000)` is therefore `1e6 · 4 · (4·1 + 6) = 40 MB`, not the 88 MB the note computes.
- What the note says: §World, units — *"`boardRenderScaleFor` still returns `RenderScale = 2` … `predictedViewerRenderBytes(1000, 1000) = 88 000 000 bytes (88 MB)` … and every one of those constants is **kept unchanged**."*
- Consequence: the spectator board bakes at 1000×1000 rather than a supersampled 2000×2000. Well inside the wasm budget either way (`tests/test_viewer.nim:190-196` asserts the preflight passes); the visible effect is board sharpness. The code's comment at `:29-32` gives the reason.

### r1-14 — [static-viewer] The viewer smoke runs with no `--soak`, so the frozen-playback check never executes

- Where: `.github/workflows/ci.yml:319-323`; `tools/ci/viewer_smoke.mjs:158`, `:526`.
- Observed: the step invokes
  ```
  node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "${replay}" --timeout 90 --strict-text-bounds
  ```
  `parseArgs` defaults `soak: 0` (`viewer_smoke.mjs:158`) and the soak block is gated on `args.soak > 0` (`:526`), so the `frozen: playback stopped advancing` failure path (`:553`) is dead in this repo. CI run 32984942130's log for that step prints no `soak:` line, confirming it did not run.
- What the note says: §Tests, CI jobs — *"`node tools/ci/viewer_smoke.mjs --bundle … --replay … --timeout 90 --soak 12 --strict-text-bounds` … The job fails if … the soak sees playback stop advancing"*, and §Packaging justifies the 1440-tick cert fixture *"comfortably longer than the viewer smoke's 12 s soak"*.
- Not blocking: checklist item 13 requires the step to exist and run with both markers and matching link flags, which it does (`{"loaded":true,"ms":547, …}` in the log). The soak is a design-note requirement only.

### r1-15 — [other] The certify step carries no `--timeout-seconds 300`, and the test that was meant to enforce it matches the wrong step

- Where: `.github/workflows/coworld-release.yml:173-181`; `tests/test_manifest.nim:240-241`.
- Observed: the certify invocation is
  ```
  uvx --from "$COWORLD_PKG" coworld certify dist/coworld_manifest.json --no-open-report
  ```
  with no timeout flag. `grep -n 'timeout-seconds' .github/workflows/coworld-release.yml` returns only lines 317 and 319, which belong to the **upload-coworld** step. `tests/test_manifest.nim:241` is
  ```nim
  check "--timeout-seconds" in sourceText(".github/workflows/coworld-release.yml")
  ```
  which passes on those upload lines, so the assertion is vacuous with respect to its own comment ("the release workflow gives certify room for the shutdown grace").
- What the note says: §Packaging — *"Because 35 s is close to `coworld certify`'s 60 s default, the release workflow's certify step passes **`--timeout-seconds 300`** (cooperative-hunting 0.1.2 → 0.1.3); the fixture is **not** shrunk."*
- Consequence: the fixture's own budget is ~10 s connect + ~1 s physics + a hard 20 s shutdown grace (`server.nim:72`, `:811-815`) ≈ 31–35 s against a 60 s default. Tight, and phase 40 is where it would show.

### r1-16 — [correctness] The baseline pin asserts materially weaker properties than §Tests 5, and the shipped physics rarely eliminates anyone

- Where: `tests/test_baselines.nim:1-15` (header), `:68-94`, `:110-132`, `:134-177`; `src/cabinet/baselines.nim:34-46`.
- Observed:
  - `reactTicks` ships at **140**, not the note's 56 (`baselines.nim:43`), with the reason recorded in the const's doc comment. This is legitimate under the note's own rule (§Scripted baselines: the three tunables are what the sweep moves), and `tests/test_tuning.nim` + `tools/ci/baseline_tuning.json` pin the sweep's pick.
  - `test_baselines.nim:81-94` asserts `seedsWithConcede >= 17` where the criterion is `episode.concedes >= 1` — i.e. "at least one concede on at least 17 of 20 seeds", not the note's *"at least 6 concedes and at least one elimination on at least 17 of 20 seeds"*. There is no elimination assertion anywhere in the file.
  - `:110-132` asserts `bulwarkWins >= 6` and `<= 16` in a 2/2 mix, not the note's *"a `bulwark` seat in placement 1 on at least 15 of 20 seeds"*.
  - `:134-177` explicitly replaces the note's *"four `spinner`s produce strictly more concedes and a strictly lower mean score"* with a "distinguishable and non-degenerate" assertion, documenting a measured counter-example (foozpong: 82 spinner concedes vs 104 bulwark).
  - The file's header states the measured rate: *"tops out around 2 concedes per warlords episode"* — with 4 cabinets × 3 lives, that means `complete/last_standing` is essentially unreachable under all-scripted play, and every all-scripted episode ends `complete/full_time`.
- What the note says: §Tests 5, §Scripted baselines ("at least one elimination on most seeds"), §End conditions (`last_standing` is "the good ending"), and the §Scoring worked examples ("3rd, eliminated at 104 s", "4th, eliminated at 41 s").
- Not blocking: checklist item 7 asks for a full-episode legality test with `results.reason == "complete"` (asserted at `:85`) and grid-tuned parameters (both present). The deviations were written this way in the first commit — `git diff --stat c11a369 ac7eca8 -- tests/` is empty, so nothing was loosened during the run.

### r1-17 — [timeout] The parallel-batch test asserts batch *structure*, not overlapping in-flight windows

- Where: `tests/test_engine.nim:113-135`.
- Observed:
  ```nim
  119    # STRUCTURE first: every alive seat is in ONE batch. That is the design's
  121    # requirement and it is immune to how libcurl happens to schedule four
  123    check curly.len(engine.turnBatch(game, @[0, 1, 2, 3], 0, 0)) == CabinetCount
  128    check providerCalls == CabinetCount
  129    check providerWindows.len == CabinetCount
  ```
  `providerWindows` is recorded (`:23`, `:50-51`) but never tested for intersection.
- What the note says: §Tests 7 — *"the fake records in-flight windows; the test asserts all four intersect"*.
- Not blocking: the checklist addendum requires the calls to *go out* as one parallel batch, and `src/cabinet/decide.nim:319-337` + `:431-432` build one `RequestBatch` and hand it to `curly.makeRequests` in a single call, with no per-seat loop around the transport. That is verified by reading the code, and the test's structural assertion covers it.

### r1-18 — [legibility] `#cab-legend` uses `var(--band)` without the `0px` fallback

- Where: `client/replay_broadcast.html:4124-4134`.
- Observed: `bottom: calc(var(--band) + 6 * var(--u));`. If `--band` has not yet been set on `:root`, the whole `calc()` is invalid at computed-value time and the declaration is dropped, so the legend falls to its static position (potentially inside the transport band) until `relayout()` runs.
- Checklist item 14(b) quotes the pattern as `bottom: calc(var(--band, 0px) + …)`. Every inherited rule in the page uses the fallback form (e.g. `#endcard { bottom: var(--band, 0px) }`, `:747`).
- Not blocking: `relayout()` runs on load and in a `ResizeObserver`, so the window is a frame or two; `#cab-rom` is inside `#clock` and unaffected.

### r1-19 — [static-viewer] `#viewpanel` markup and CSS are gone, but the page still drives `core.zoomAt` / `core.setZoom`

- Where: `client/replay_broadcast.html:3627-3628`, `:3685`, `:3702`, `:3757`, `:3805-3806`, `:3854-3904`.
- Observed: the panel's markup and CSS are removed (verified: `tests/test_viewer.nim:79-90` asserts the ids and the six CSS selectors are absent, and the diff against the starter removes lines 528-832 and 1506-1549). The slider/minimap wiring survives but is guarded:
  ```js
  3858    if (zoomSlider && minimapBox && btnZoomIn && btnZoomOut) {
  3859    core.attachMinimap($('minimap-canvas'));
  ```
  However the keyboard and gesture handlers are **not** guarded and still zoom the board:
  ```js
  3627      else if (k === 'z') core.zoomAt(ZOOM_STEP);
  3685      core.zoomAt(Math.exp(-ev.deltaY * unit * 0.012), p.x, p.y);
  3757          core.zoomAt(g.span / pinchSpan, g.midX - rect.left, g.midY - rect.top);
  ```
- What the note says: §Chrome provenance — *"`broadcast_core.js`'s zoom/pan/minimap code stays in the file, verbatim, simply never driven."* It is driven, by `z`/`x` and by pinch, on a board the note says always fits the frame. Checklist item 14's fourth bullet asks for the `core.zoomAt/setZoom/attachMinimap` wiring to be removed rather than hidden; the panel is genuinely removed, the call sites are not.
- Not blocking: with no readout there is no way to see the zoom level, but the board still refits on `0`/double-click (inherited), so there is no dead state.

### r1-20 — [other] The inherited region above the banner *is* edited, contrary to the note's "nothing above them is rewritten"

- Where: `client/replay_broadcast.html:1..4002` vs `/workspace/starters/coworld-ctf/client/replay_broadcast.html:1..4342`; banner at `:4003-4029`.
- Observed: `diff <(head -4342 starter) <(head -4002 cabinet)` = 501 removed / 161 added lines. The removals are dominated by exactly the elements the note lists (the `#povBadge`/`#fpv`/`#viewpanel` CSS block, starter lines 528-832; the `#viewpanel` and `#fpv` markup, 1506-1549; the `?viewpanel=0` opt-out, 1452-1459). The additions are the starter's own `PB_MODE` game branches retargeted to `CAB_MODE` (plate contents at `:1854-1930`, feed/beat routing at `:3124-3129`, endcard columns at `:3379-3529`) plus null guards on the removed elements (`:1988-1996`, `:2014`, `:2179`, `:2931`, `:2990`, `:3609`).
- Checklist item 14 is satisfied: the page is 4454 lines against the starter's 4660 (not "a fraction of the starter's size"), `client/chrome_common.js` is byte-identical (`sha256 7ace7287…` on both copies), `client/broadcast_core.js` differs in exactly one line (`CTF_WIRE` → `CABINET_WIRE` at `:49`), and `client/league_replayer.html` differs in exactly four lines (`'ctf-shell'` → `'cabinet-shell'`). Recorded here only because the note's wording ("Nothing above them is rewritten") does not match what shipped.

### r1-21 — [other] Design-note asset name is wrong; the code is right

- Where: `src/cabinet/sim_types.nim:131` (`DarkBgPath* = "data/darkbg.aseprite"`), `src/cabinet/global.nim:207` (`readAsepriteImage`).
- Observed: the note names `data/darkbg.png` in §Design pins and §Art. Neither the repo nor the starter ships `darkbg.png`; both ship `darkbg.aseprite`, and the code reads it with the right reader. Nothing to fix in the code.

### r1-22 — [correctness] `sanitizeSay` strips every non-ASCII rune, so an LLM `say` can never carry one

- Where: `src/cabinet/stances.nim:62-74`; `tests/test_replay.nim:126-156`.
- Observed: `sanitizeSay` truncates to 48 runes on a rune boundary and then keeps only `32 ≤ value < 127` minus `{`/`}`. This matches the note's §Reply schema (*"truncated to 48 runes, then ctf's printable-ASCII shout sanitiser"*). The UTF-8 end-to-end test at `test_replay.nim:128` sets `stance.say = "🎯 next"` **directly** on the object, bypassing `sanitizeSay`, so the emoji reaches the replay and `tools/replay_summary.py` is exercised on real multi-byte bytes. `note` is not ASCII-filtered (`sanitizeNote`, `:76-78`), so the UTF-8 risk the checklist item 9 names is real on the `note` path and is what the test actually protects.
- Recorded as an observation only: item 9 is satisfied (`tests/test_stances.nim:94-119` feeds a 4-byte emoji straddling the 48-rune boundary and asserts the result decodes).

### r1-23 — [other] Four assertions the note's §Tests 7 and §Tests 11 name have no test

- Where: `tests/test_engine.nim` (12 tests), `tests/test_server.nim` (5 tests).
- Observed missing, by name:
  - "a disconnected seat plays `bulwark` and revives on reconnect" (§Tests 7);
  - "a never-connecting seat is reported to `COGAME_PLAYER_FAILURE_URI` and the run still reaches a normal ending" (§Tests 7);
  - "a registration that arrives before its player index exists is **held and applied**, not dropped" (§Tests 7) — the held-registration path is real code (`server.nim:585-625`) but only `parseRegistration` is unit-tested (`test_engine.nim:297`);
  - "`/healthz` and `/global` still answer 15 s after the artifacts are written" (§Tests 11) — the 20 s grace is real code (`server.nim:72`, `:811-815`) but untested.
- Consequence: four of the note's degrade-never-hang paths are code-reviewed only. Not a checklist item.

### r1-24 — [manifest] `num_agents` lives inside `variants[].game_config`, not at the variant's top level

- Where: `coworld_manifest_template.json`, all three variants (`game_config.num_agents == 4`) and `certification.game_config.num_agents == 4`.
- Observed: `variants[i].num_agents` is absent; `variants[i].game_config.num_agents` is `4` in `warlords`, `quadrapong` and `foozpong`, and `certification.game_config.num_agents` is `4` with `len(certification.players) == 4` and `len(certification.game_config.players) == 4`.
- Checklist item 6 is satisfied on every clause I can verify: `tools/ci/docker_smoke.sh:106-150` implements all four invariants against `certification.game_config.num_agents` plus the `SMOKE_SEATS` cross-check, every failure message is prefixed `SEAT-COUNT FAIL:`, `SMOKE_SEATS` defaults to `4` (`:54`), and `grep -c 'SEAT-COUNT FAIL' ci_log.txt` over the full log of run 32984942130 returns **0** with `smoke OK: seats=4 results=552B replay=41403B reason=complete`. Recorded only because the placement differs from a literal reading of "in every manifest variant"; it matches the design note's own variant table, whose `num_agents` column sits beside `players`/`slots`, which are `game_config` keys.

---

## Traced and consistent

- **Checklist 1 (CI green, no test loosened).** `gh run list -R Metta-AI/cogame-atari-cabinet --branch main -w ci.yml` → run **32984942130**, headSha `ac7eca8acfc2eadf316c5eb6eda9f84881a76fcf`, conclusion `success`, jobs `test`/`docker-smoke`/`wasm-viewer` all `success`. Two earlier attempts at the same sha (32984632295 workflow_dispatch, 32984636790 push) are `startup_failure` with `completedAt = 0001-01-01` on their jobs, i.e. GitHub failed to start them; the re-dispatch is the run that executed. "No test loosened": `git diff --stat c11a369 ac7eca8 -- tests/` is **empty** — the only file changed after the initial drop is `client/replay_broadcast.html`. All 17 test files ran; the log shows 34 `nim r … tests/*.nim` invocations (every file in debug and release except `test_perf.nim`/`test_baselines.nim`, which are release-only per `NIM_TESTS_RELEASE_ONLY`), and no `FAILED (` line.
- **Checklist 2 (replay re-derivation).** `tests/test_replay.nim:10-91` writes a real `COWLDCAB` replay per ROM, re-parses it, and re-steps from the recorded bytes with `mismatchQuit = true` asserting `hashMismatchTick == -1` over >900 ticks; `tests/test_determinism.nim:19-28` asserts `replaySteps(config, first.commandLog) == first.hashes` frame by frame. The viewer uses the same path: `replay-viewer/cabinet_replay.nim` imports `cabinet/[…, replay_runtime, replays, sim]` and `replays.stepReplay:294-299` calls `sim.step(commands)` then `checkReplayHash`, which compares `sim.gameHash()` against the recorded value at every tick (`:262-292`). The viewer's display is built from that same re-derived `sim` (`replay_runtime.buildReplayViewerPacket:74-106`), not from a parallel recording.
- **Checklist 3 (static viewer).** `coworld_manifest_template.json` `game.replay_viewer == {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` exists at mode `100755` (`git ls-files -s`), diffs against the starter in exactly two lines (`image_tag`, the `docker cp` source path `/workspace/cabinet/replay-viewer/dist/.`), and is invoked by path at `ci.yml:254`. No `/client/replay` pod path in the manifest; the release workflow hard-fails if certify does not print the static-bundle liveness marker (`coworld-release.yml:81`, `:200-208`).
- **Checklist 4 (both name spaces).** Agents see aliases only: `decide.seatViewJson:76-229` emits `aliasOfCabinet` everywhere and no `seatName`; `global.buildSpriteProtocolPlayerUpdates:664-682` uses the alias-only board. Real names live in `broadcast.rosterJson:171-193`, `roster.playerResultsJson:238`, and the endcard rows. `tests/test_locality.nim:114-148` asserts both halves.
- **Checklist 5 (every wait bounded).** LLM: `attempt1Ms 9000` / `retryMs 5000` handed to `curly.makeRequests(batch, max(1, deadlineMs div 1000))` (`decide.nim:424-432`); inter-batch floor `sleep(min(turnSpacingMs, turnSpacingMs − since))` (`:409`); per-turn `turnBudgetMs` gate (`:419`); budget guard (`:359-367`). Lobby: `lobbyJoinTimeoutTicks` (`sim_state.nim:100-104`, `sim.nim:752-762`, `server.nim:521-531`). Serve sampling: `for _ in 0 ..< ServeRejectAttempts` (32) then a fixed 8-entry scan (`sim.nim:181-189`) with a `> 8` fault guard (`:723-726`). Frame limiter: bounded by `frameDuration` (`server.nim:374-395`). Shutdown grace: `while getMonoTime() < graceUntil: sleep(200)` for 20 s (`server.nim:811-818`). Record-shrink loop bounded at 12 iterations (`stances.nim:404-410`). Engine stop at 660 s (`server.nim:502-510`). No unbounded loop found in `src/`.
- **Checklist 8 (LLM reply handling).** Tolerant parse: `stances.extractJsonObject:96-135` (balanced-brace scan with a first-brace/last-brace fallback, fence- and prose-tolerant), synonyms and percent handling at `:137-151`, `:222-232`, `:314-323`. One retry: `while open.len > 0 and attempt < 2` (`decide.nim:416`), with the throttle fast-fail at `:471-477`. Fallback recorded with cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, budget_guard} at `:390`, `:456-465`, `:485-492`, and counted into `game.fallbackTurns` at `server.nim:672`, surfaced in `results.fallbackTurns`. `tests/test_engine.nim:182-211` pins zero retries on throttle and exactly one on garbage.
- **Checklist 9 (rune-safe truncation).** `stances.truncateRunes:53-60` is the single shortening path and uses `runeLen`/`runeSubStr`. Applied at every cap the note names: `note` 160 (`:78`, `:380`), `say` 48 (`:69`, `:391`), `register.policy` 48 (`decide.nim:246`), `fallback.detail` 200 (`decide.nim:260`), the whole stance record 600 (`stances.nim:394-410`), `register.prompt` 4000 (`server.nim:605`). Test: `tests/test_stances.nim:94-119` places a 4-byte emoji on the 48-rune boundary and asserts a valid-UTF-8 round trip; `tests/test_replay.nim:99-157` runs the whole replay through `json.loads(out.decode("utf-8"))` in `tools/replay_summary.py`.
- **Checklist 10 (manifest validates).** `game.docs.readme = {"type":"text","value":…}` (5 502 chars) and `pages = [rules.md, protocol.md, stances.md]`, each `{id, title, content:{type,value}}` with 8 540 / 8 530 / 4 557 chars. `game.protocols` carries **both** `player` and `global`, each a `{"type":"text","value":…}` object. `results_schema` has exactly the 22 keys of `roster.resultsKeys()` with `additionalProperties: false`, every per-seat array `minItems: 4, maxItems: 4`, and the three enums exactly as the note specifies. `config_schema` is `additionalProperties: false`, `required: ["tokens","players"]`, every array bounded (`tokens` 1..4, `players` 1..4, `slots` 0..4), and covers every key `sim_config.update` reads (verified by hand against `sim_config.nim:254-290`; the only omission is the `numAgents` camelCase alias of `num_agents`, which `tests/test_manifest.nim:112` exempts explicitly). Top-level `tags` has 5 entries; `game.tags` is absent; `game.description` present; no top-level `version`, no `game.display_name`. Secret namespace `secret://coworld/atari-cabinet/anthropic_api_key` == `game.name`.
- **Checklist 11 (360 px).** `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` at `client/replay_broadcast.html:4035-4040`; labels hidden under `@media (max-width: 640px)` at `:4109-4112`; `#stage.tiny` (boardW ≤ 620) collapses the brick bar to a numeral and hides the legend at `:4104-4108`. `relayout()`'s `Math.max(0.5, Math.min(1.6, boardW / 760))` clamp and `stage.classList.toggle('tiny', boardW <= 620)` are the starter's, unmodified (`tests/test_viewer.nim:56-61`).
- **Checklist 12 (release order and scaffold).** `coworld-release.yml` runs `coworld build` (`:159`) → `coworld certify` (`:173`) → `Upload the policies` (`:212`) → `coworld upload-coworld` (`:310`) → `coworld secret put` (`:348`), in that order in one job. All three workflows present; `tools/ci/docker_smoke.sh` mode `100755`. `tools/ci/policies.json` has four policies, all `"run": "/bin/atari-cabinet-player"`, two with `PLAYER_PROMPT` and two with `PLAYER_SCRIPTED` ∈ {bulwark, spinner}; the second `PLAYER_PROMPT` entry carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`policies.json:17`). The placeholder gate `grep -n '<slug>\|<IMAGE>\|<SEATS>' …` over the five named files returns **no matches** (exit 1), so the gate exits 0.
- **Checklist 13 (viewer executes).** `wasm-viewer` `needs: docker-smoke` (`ci.yml:217`); the "Load the bundle in a real browser" step ran and printed `{"loaded":true,"ms":547,"clock":"1:00 TIME LEFT WARLORDS · TURN 1/12","scorebug":"RED P2 SCORE 60.00 GREEN P1 SCORE 60.00 …"}` with no `continue-on-error`. Markers: `replay-viewer/static_replay.js:161` sets `data-replay-loaded="true"` on the Worker's `loaded` message (first drawn frame) and `:14-20` sets `data-replay-error`; `:32` sets `data-replay-mismatch-tick`. Link flags vs bootstrap **agree and come from the same starter**: `replay-viewer/config.nims` differs from `coworld-ctf`'s in exactly 4 lines (all `ctf_` → `cabinet_` renames) with **no `MODULARIZE` and no `EXPORT_NAME`**, and `static_replay_worker.js:8` is `var Module = {};` with `Module.onRuntimeInitialized` at `:188` and `importScripts('./wire_constants.js','./broadcast_core.js','./cabinet_replay.js')` at `:239` — the non-modularized form. `static_replay.js` and `static_replay_worker.js` differ from the starter's only in the `ctf_`→`cabinet_` export names and the two Worker/global names.
- **Checklist 14 (chrome provenance).** `client/chrome_common.js` sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` — **identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js`, `diff` empty. `client/replay_broadcast.html` is the starter's page with the game block appended under `ATARI-CABINET additions to the inherited coworld-ctf chrome` (`:4003-4005`); sections 1–6 (stage, scorebug, banner lane, kill feed, transport + scrubber + momentum + beats + lulls, endcard, locker room) are all present and byte-identical apart from the removals the note lists (see r1-20). Transport rules: (a) `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` (`:3950`, `:3971-3977`); (b) the two overlays the game block adds ride `#chrome` with `bottom: calc(var(--band) + …)` (`:4124-4134`) and `#clock` respectively; (c) `#endcard { top: var(--topband, 0px); bottom: var(--band, 0px) }` at `:745-747`, shown with `#endcard.on` (`:758`), and removed on every frame whose phase is not `gameover` (`:1713`), which is what makes every seek dismiss it; (d) scrubber beats are `document.createElement('button')` with `title`, `aria-label` and a click that sends `s:<tick>` (`:4209-4221`), and `button.beat-marker` plus one rule per emitted kind (`concede`, `breach`, `eliminated`, `last_standing`, `over`) exist at `:4138-4170` — matching `replays.ScrubberBeatKinds` exactly. Zoom panel removed (see r1-19 for the residual call sites).
- **Resolution rules, step by step.** (1) turn boundary at `gameTicksElapsed() mod turnTicks == 0` with a `lastTurnKey` de-dup (`server.nim:654-679`); `activeStance` is not hashed — `gameHash` mixes no stance field (`sim_state.nim:217-268`). (2) autopilot compiled in **cabinet index order** and recorded against the driving seat (`server.nim:682-694`); byte layout `near = cmd mod 9`, `far = (cmd div 9) mod 9`, `grip = cmd div 81` with `cmd >= 243 → 40` shared between the server and the replay runtime (`sim.nim:31-37`, tested exhaustively at `tests/test_physics.nim:187-202`). (3) paddle motion in cabinet order, near then far, clamped to `±PaddleTravelHalf`, `paddleVel` recorded as the applied delta, out cabinets zeroed (`sim.nim:517-547`). (4) ball motion in id order with the exact priority (a) paddles near-then-far in cabinet order, (b) bricks in cabinet/row/column order, (c) mouth lines, (d) solid walls — implemented as scan order plus a strict `isBefore` tie-break (`sim.nim:301-379`, `consider` at `:309-313`); one contact per ball per tick with the remainder applied along the new index (`:686-697`). Deflection fan `j = clamp(roundDiv(offset·6, half) + spin, −6, +6)`, `dl' = 16 − 2j` with `spin` thresholds 12 000 / 4 000 (`sim.nim:381-404`), and `tests/test_physics.nim:95-115` proves `dl' ∈ [4, 28]` and even over 4 × 64 × 13 × 7 = 23 296 cases — more than the note's 9 984. (5) score folded every tick for all four cabinets (`sim.nim:767-768`) by the exact five-term non-negative formula with the lives term divided by `startingLives` (`:214-228`). (6) per-tick `writeHash(uint32(tick), gameHash())` (`server.nim:708`), and `gameHash` mixes every field the note lists plus `placement` and `serveFallbacks` and a `perm` digest, and no presentational field. (7) end checks — see r1-11 for the ordering caveat.
- **Scoring and placement.** Weights `60/15/2/0.5/0.25` million micro-points (`sim_types.nim:102-106`) match §Scoring; `recomputeScore` is the only writer of `scoreMicro`. The placement chain at `sim.nim:230-259` implements exactly the three-tier rule with the lower-index tiebreak, `assignPlacements` insertion-sorts on it, and `tests/test_scoring.nim:90-134` asserts it is a strict permutation of 1..4 over 20 000 randomised end states with `win[s] == (placements[s] == 1)`.
- **ROM presets.** `rom.RomPresets:29-42` reproduces the note's table row for row, including `farPaddleHalfCu: 5` on all three. `applyPreset:65-91` skips every key the incoming config named, and `sim_config.update:243-252` calls it *after* reading `rom` and *before* the explicit keys — the `defaults → preset → explicit` order the cert fixture's `rom: warlords` + `startingLives: 9` relies on (`tests/test_rom.nim:11-33`). Every variant's `game_config` is constructed and stepped for 600 ticks with four bulwarks (`test_rom.nim:60-90`).
- **Replay writer.** Magic `COWLDCAB`, format version 1, `GameName "atari-cabinet"`, `GameVersion "1"` with a prepend-only `GV1` changelog comment (`replays.nim:91-102`, `sim_types.nim:29-35`); `tools/ci/check_gameversion.sh` kept. Config JSON carries `seed`, `rom`, the fully resolved preset, `perm` (re-derived from the seed at `sim_config.nim:350-356`, which the note's "perm is the first draw" makes valid), the whole geometry table, the reward constants, `players[].name` (real) and `slots[].alias` (`:326-428`). Command bytes are written change-only through `writeInputMaskChange` (`replays.nim:112-126`). One hash per tick. `result` control record embedded once (`decide.nim:266-274`, written at `server.nim:787`). Keyframes serialise the **whole** `SimServer` via flatty (`replays.nim:137-144`), which covers every new field by construction — broader than the note's "static geometry and perm excluded", and harmless.
- **Player container.** `src/atari_cabinet_player.nim`: 240 × 500 ms dial (`:25-26`), one registration chat re-sent on `RegistrationResends`/`ResendEveryFrames` (`:27-28`, `:116-117`), Ready packet `0x85` after each frame (`:47-53`), receive loop in `try/except CatchableError` with `quit(0)` on a dead socket (`:121`, `:132`), and no input ever sent. Manifest `player[0].resources.limits.cpu == "1"` and it occupies all four certification slots.
- **Seeded stream (builder deviation: hand-rolled xorshift128+).** `arena.initRngState/next/drawInt:44-78` is a SplitMix64-seeded xorshift128+ working entirely in the `uint64` domain, with the stated reason (`sim_types.nim:166-172`: `std/random`'s `Rand` has private fields the flatty keyframe pass cannot see). This preserves the property the note actually cares about — *"no draw ever touches `rand(int)`"*, whose `int` is 32-bit under `--cpu:wasm32` — and `tests/test_determinism.nim:66-80` greps the guarded modules for `rand(`. `perm` and 200 subsequent draws are asserted to be pure functions of the seed (`:90-114`). Sound.
- **Lobby force-start (builder deviation).** Implemented in both layers and they agree: `sim.step`'s Lobby branch starts on `lobbyIsStarting()` (players ≥ `minPlayers`) or `lobbyJoinTimedOut()` (`sim.nim:742-762`), and `server.nim:521-531` independently declares the no-show to `COGAME_PLAYER_FAILURE_URI` (lowest missing slot, `game.nextPlayerSlot()`) and sets `forceStart`. `config.update` clamps `minPlayers` to `numAgents` (`sim_config.nim:291-292`), so the two gates cannot disagree. Uncommanded cabinets fall to `bulwarkStance` at `server.nim:687-690`. Deterministic at playback because the recorded joins reproduce the lobby length.
- **`league_replayer.html` renamed only (builder deviation).** `diff` against the starter is 4 changed lines, all `'ctf-shell'` → `'cabinet-shell'`, matching the `m.src !== 'cabinet-shell'` guard the board page now expects (`replay_broadcast.html:1639`).
- **"No nano-banana sprites" (builder deviation).** The design note never requires generated sprites; §Art requires the board to be baked with pixie from the repo's shipped assets, which is what `global.nim:153-260` does (`font.ttf`, `darkbg.aseprite`, `arena_floor.png`, `wall_h/v.jpg`, the four `heart_<colour>.png`). Nothing to reconcile.
- **Two-name-space and information hiding.** `tests/test_locality.nim` asserts the positive half (every ball, paddle, brick bit and lives count is in the seat's view) and the negative half (no other seat's stance/note/say/prompt, no `perm`, no `seed`, no RNG state, no wall-clock fact, no `players[i].address`), plus that `paddleCommand`'s signature is structurally limited.
- **`chrome_common.js` reads `window.CTF_WIRE`** (`:72`) and `src/cabinet/wire_constants.nim:27` publishes `window.CTF_WIRE = window.CABINET_WIRE` as an alias, with the reason recorded at `:28-31`. This is the only way to satisfy both "byte-identical chrome_common" and "no `CTF_` identifier in `src/`"; `tests/test_determinism.nim:125-150` exempts exactly those two files with the reason inline. `client/broadcast_core.js` uses `window.CABINET_WIRE` only.
- **`teams[k].policies` is an array of real policy names** (`broadcast.nim:168`), not the `1` in the note's state-JSON example. `chrome_common.js:135` (`if (tr && tr.policies && tr.policies.length) return tr.policies;`) consumes it as a list, so the implementation matches the byte-identical chrome and the note's example is the thing that is wrong. Same for `roster[].lives = max(0, lives − 1)` (`broadcast.nim:185`): `chrome_common.js:288`/`:303` documents the squad-pip rule `p.lives + (p.alive ? 1 : 0)`, so the −1 is the correct adaptation, not an off-by-one.
- **Replay config JSON carries `tokens`** (`sim_config.nim:421`). Inherited verbatim from the starter (`coworld-ctf/src/ctf/sim_config.nim:953`); not a change made here.

---

## Could not determine

- **Whether a full-cap `say` bubble can overflow the board's right edge.** `global.nim:653` clamps the bubble's x to `max(2, (MapWidth - baked.width) div 2)` — a lower bound only. If a baked `"YELLOW: " + 48 runes` sprite at size 22 in `data/font.ttf` measures wider than 1000 board px, the sprite is drawn from x = 2 and its tail leaves the board. Settling evidence: the pixie-measured width of that string at size 22 (a one-line Nim test calling `textSprite` and asserting `baked.width + 4 <= MapWidth`), or the sprite bounds probe suggested in r1-2. The same shape applies to the stance chips, whose right clamp is the hard-coded `MapWidth - 120` (`:628`) rather than the baked width.
- **Whether `complete/last_standing` ever occurs under real LLM play.** All the measurement in the repo is all-scripted (`tests/test_baselines.nim`), where the header records ~2 concedes per warlords episode. An LLM seat compiles through the same autopilot, so I would expect a similar defence rate, but I have no hosted-episode evidence. Settling evidence: phase 60's `results.endRule` distribution over real league episodes, or a harness run with a live `ANTHROPIC_API_KEY`.
- **Whether the two `startup_failure` runs at `ac7eca8` indicate anything about the tree.** Both have zero-duration jobs and no logs (`gh run view … --log` returns nothing usable), which is the signature of a GitHub-side start failure rather than a repo problem, and the immediate re-dispatch of the identical sha went fully green. Settling evidence: a fresh `workflow_dispatch` on `main` at the same sha, or a `push` event that starts normally.
- **Whether the `wasm-viewer` job would catch a genuinely frozen replay.** With `--soak` absent (r1-14) the only liveness evidence is the single `loaded: true` plus the three scrub readouts at 0 % / 50 % / 100 %, which are seeks rather than playback. Settling evidence: re-running the step with `--soak 12` and reading the `soak:` line.
