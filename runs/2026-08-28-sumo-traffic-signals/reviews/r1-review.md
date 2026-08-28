# r1 review — sumo-traffic-signals

Range: `311e76d..54fd040` (whole history: 5 commits; `54fd04080b0c2e75275b5ada197b431fa6dc3023` is the
reviewed sha, clean clone at `/workspace/scratch/cogame-sumo-traffic-signals`)
Files read: 71 (all of `src/`, `replay-viewer/`, `client/`, `tests/`, `tools/`, `.github/workflows/`,
`coworld_manifest_template.json`, `Dockerfile`, plus the starter mount at
`/workspace/starters/coworld-ctf` for provenance diffs and the CI logs/artifacts of run
33187823599)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
one-parallel-batch rule)

Evidence conventions: **observed** = I read it at this sha; **inferred** = I reasoned from what I
read; **untested** = it would take a run to settle. CI facts are cited by run/job id.

---

## Blocking

### B1 — Two assertions in `tests/` were removed or narrowed during this run (checklist item 1, second half)

- Where: `tests/test_signals_engine.nim:83-109` and `tests/test_signals_viewer.nim:98-112`; the
  hunks are in commit `d3fdc93` ("Fix the renderer fixture's 404s and clipping read, and record the
  wave divergence").
- Observed, hunk 1 (`git show d3fdc93 -- tests/`):
  ```
  -  test "25. seed 42 on grid4x4 yields throughput, a spillback and a wave":
  +  test "25. seed 42 on grid4x4 is an INTERESTING fixture episode":
       check sim.throughput > 0
       check sim.spillbacks >= 1
  -    check sim.greenWaves >= 1
  +    check sim.spillbackTicks >= 1
  +    check sim.starvations >= 1
  +    check sim.crossings > sim.throughput
  +    for slot in 0 ..< MaxSeats:
  +      check sim.phaseChanges[slot] > 0
  ```
  A `check` was deleted from a test file inside this run.
- Observed, hunk 2 (same commit, `tests/test_signals_viewer.nim`, test 37 — the chrome-alias
  shadowing guard):
  ```
  -          aliases.add(pair[0].strip())
  +          let name = pair[0].strip()
  +          if name.len >= 2:
  +            aliases.add(name)
  ```
  The set of `chrome_common.js` aliases the test checks for shadowing was narrowed: one-character
  aliases (`$`) are no longer checked. That is a reduced assertion domain on an existing check.
- Checklist item: item 1 — "`ci.yml` conclusion `success` on `main` at the reviewed sha, **with no
  test disabled, skipped, or loosened during this run** … Read those hunks: a deleted assertion, a
  widened tolerance, a `skip`/`t.Skip`/`xfail`/`--skip` added, or a test file removed is a blocking
  finding."
- Why blocking: item 1 states the rule without an exception clause, and both hunks fall inside its
  literal terms.
- **The mitigating facts, all verified, so the judge weighs the whole picture and not just the
  diff:**
  1. The physics bug that made a wave impossible was fixed in the **preceding** commit `9c1d4b9`
     (`src/signals/vehicles.nim:73` — `sim.cars[car].movedThisTick = true` at spawn, so a car is not
     charged a wait tick on the tick it is created). The assertion was dropped *after* the mechanism
     was made possible, not instead of fixing it. `git log -S "movedThisTick = true" -- src/signals/vehicles.nim`
     confirms the order.
  2. The removal is documented in the test file itself with a 21-line rationale
     (`tests/test_signals_engine.nim:89-109`), and the fixture episode really does produce no wave:
     the CI artifact `smoke-replay/results.json` from run 33187823599 reads
     `greenWaves: 0, spillbacks: 170, starvations: 4` on seed 42 with the cert seat mix.
  3. Hunk 1 replaces 1 assertion with 4 (plus a 4-way loop), so net assertion count rises.
  4. Hunk 2 adds three compensating structural checks in the same commit
     (`tests/test_signals_viewer.nim:117-121`: the game block is one IIFE, so nothing inside it can
     hoist into the page scope at all), and the block's own `$` is declared inside that IIFE
     (`tools/page_sig_block.html:262`).
  5. Every other `tests/` change this run is a reformat, an added assertion, or a tightening — I
     read all four commits' `tests/` hunks. `54fd040` changed `check ".plate-name {"` to
     `check ".plate .plate-name {"`, which follows a CSS rescoping and is stricter.

There are **no other blocking findings**. Items 2–15 and the one-parallel-batch rule are all
satisfied from the tree and the cited CI evidence; the per-item trace is in §Traced and consistent.

---

## Non-blocking

Everything below is a divergence from the design note, not from a named checklist item, unless a
checklist bullet is quoted.

### N1 — The renderer fixture's "full-cap 120-rune say" is 109 runes, and no run asserts its own length
- Where: `tools/ci/renderer_fixture.html:58-62`; the CI step comment at `.github/workflows/ci.yml:405-409`.
- Observed: `SAY` is `'row C eastbound is my wave: C1 at +0, C2 at +6, Delta take C3 at ' + '+12 and hold B3 while C2>C3 drains, please 🚦'`, which is **109 runes**;
  `SAY = Array.from(SAY).slice(0, 120).join('')` is therefore a no-op. The file's own comment
  (`:19`), the design note (§Tests, test 44) and the ci.yml step comment all say "a full-cap
  120-rune `say`". The fixture never asserts that any transcribed run is still full length; its
  `transcribe()` deliberately re-ellipsizes a clipped run (`:188-199`).
- Checklist bullet in tension: item 15 — "The fixture asserts its own strings are still full-length —
  one quietly shortened remark leaves it passing while testing nothing." The blocking clause that
  item 15 actually names is "a repo that draws model text and has **no such fixture**", and this
  repo has one that loads the shipped `index.html` and drives the real chrome at 360/620/900 px, so
  I do not file it as blocking. A judge reading the full-length sentence as normative would.
- Supporting evidence read: CI run 33187823599, job 98905709185, step "Drive the shipped page with a
  worst-case renderer fixture": `canvas text: 600 drawn, 0 never inside the canvas (0 draws crossed
  an edge), 48 ellipsized (--strict-text-bounds)`.

### N2 — The `fault` end reason cannot be produced by the shipped server
- Where: `src/signals/sim.nim:95-114` (`applyStop`), `src/signals/server.nim:444-595`,
  `src/sumo_traffic_signals.nim:67-96`.
- Observed: `grep -rn applyStop src/` shows the server only ever calls `applyStop(erWallClock, …)`
  (`server.nim:570`) and `applyStop(erFullPeriod, "")` (`server.nim:574`, `:637`). There is no
  `try`/`except` around the episode loop or around `when isMainModule`, so an unexpected exception
  propagates and the process exits non-zero with no `results.json`. `erFault` is constructed only in
  `tests/test_signals_engine.nim:179` and `tests/test_signals_replay.nim:98`.
- Note says (§End conditions): "`fault` — an unexpected exception in the sim or the loop. **Caught**;
  the episode is settled from the last completed tick, `results.endRule = "fault"`,
  `results.stopDetail` names it …, artifacts are still written, exit 0. A defect:
  `tools/ci/docker_smoke.sh` fails the build if the smoke episode reports it."
- Also observed: `tools/ci/docker_smoke.sh:306-308` only **prints** `episode end reason: …`; there is
  no check that fails on `fault`.
- Inferred: this is a degrade path that never fires in a healthy episode, so it does not falsify
  item 5's "every wait has an explicit bound" or "no unbounded loop"; it does mean the note's
  three-value `reason` enum is really two values in practice.

### N3 — The single retry can be pre-empted by the turn budget, because `turnBudgetMs` is measured from before the `turnSpacingMs` sleep
- Where: `src/signals/decide.nim:158-160` (`turnStart = getMonoTime()`), `:218-224` (the spacing
  sleep), `:231-236` (the budget check that breaks the attempt loop).
- Observed: `turnStart` is taken at the top of `turn()`, before the budget guard, the rate guard and
  the up-to-`turnSpacingMs` sleep. With `turnSpacingMs = 12000` and `turnBudgetMs = 14000`, a turn
  that sleeps ~9 s for spacing and then spends the full `attempt1Ms = 9000` on attempt 1 is already
  ~18 s past `turnStart`, so `getMonoTime() - turnStart >= budget` fires and the loop `break`s before
  the retry batch, writing a `fallback` record with `cause = "timeout"` and
  `detail = "per-turn budget exhausted before attempt 2"`.
- Note says (§Cadence): "`turnBudgetMs 14.0 s (monotonic deadline around the whole turn)` … 32 turns
  x max(spacing 12 s, budget 14 s)" — the `max(…)` arithmetic implies the budget is meant to bound
  the *call* portion of the turn, not spacing + calls.
- Checklist item 8 requires the retry to happen "on a parse or transport failure"; the code has a
  retry batch and reaches it whenever the budget allows. **Untested** — it needs a hosted episode
  with a real provider timing out to see how often the retry is actually skipped.
- Bounding is unaffected: the turn is still bounded at spacing (12 s) + attempt1 (9 s) ≈ 21 s.

### N4 — Fallback `cause` vocabulary differs from the note's enum
- Where: `src/signals/decide.nim:186, 211, 234, 281-283, 305-310`.
- Observed causes emitted: `budget_guard`, `no_credentials`, `rate_guard`, `timeout`,
  `transport_error`, `parse_error`, **`throttled`**. `disconnected` is never emitted anywhere
  (`grep -rn disconnected src/` returns nothing).
- Note says (§Degrade): `cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard,
  budget_guard, disconnected}`.

### N5 — Attempt 2's failure logs both "will retry" and "falling back"
- Where: `src/signals/decide.nim:289-291` and `:313-315`.
- Observed: the `echo "… attempt N failed, will retry: …"` line runs for **both** attempts; the
  `"falling back"` line then runs for the seats still open after the loop. The phase-60 grep for
  `falling back` therefore works, and `will retry` is not exclusive to attempt 1 as the note's
  §Degrade paragraph and the code's own comment at `:287-288` claim.

### N6 — Provider reply cap is applied in runes, not bytes
- Where: `src/signals/llm.nim:193-195` — `if result.len > MaxReplyBytes: result = result.truncateRunes(MaxReplyBytes)`.
- Observed: the guard compares bytes, the cut is in runes, so a 4-byte-per-rune reply can survive at
  up to ~16 KB. Rune-safety (checklist item 9) is unaffected; the note's "whole reply | bytes | ≤ 4096
  read from the provider before parsing" is not a byte bound.
- `tests/test_signals_driver.nim:235-244` ("the reply read is capped at 4096 bytes") asserts the
  constant and calls `truncateRunes` on an ASCII string; it does not exercise `llm.textOf`.

### N7 — The rate guard is applied to attempt 1 only
- Where: `src/signals/decide.nim:200-215` (guard) vs `:249-250` (the retry batch stamps requests but
  is not re-checked).
- Observed: `room` is computed once per turn, before the attempt loop. A turn in which every seat
  retries issues 8 requests but is checked as 4.
- Note says: "if issuing **the next batch** would push the trailing-60 s count above 28…".

### N8 — Signal-machine clearance timing: exactly `clearTicks`, not the note's literal step b/c reading
- Where: `src/signals/phases.nim:76-104`.
- Observed: on the tick a change clears `minGreenTicks`, the code sets `clearLeft = clearTicks` and
  then falls straight into the `clearLeft > 0` block on the same tick, decrementing it. With
  `clearTicks = 2` that is 2 ticks with no discharge (T and T+1) and the phase commits at T+1.
  A literal reading of the note's steps 2b/2c (enter clearance at T, decrement at T+1, commit at T+2)
  gives 3. The implementation satisfies the note's own stated invariant (§Tests, test 7: "every
  change costs **exactly** `clearTicks` of all-red with no discharge"; `phasechange` fires when the
  clearance ends). `tests/test_signals_sim.nim:266-292` pins `flippedAt == clearTicks`.

### N9 — `greedy`'s hold rule follows the note's `auto` rule, which differs from the note's `greedy` rule at the boundary
- Where: `src/signals/driver.nim:53-66` (`autoPhase`) and `:104-112` (`greedyOrderFor`, which calls it).
- Observed: `greedyOrderFor` holds iff `autoPhase` returns the current phase, i.e. iff
  `served(best) < served(current) + switchMargin`. The note's §Scripted baselines rule 1 is
  "hold if `served(current) >= max_P served(P) − switchMargin`", which at exact equality
  (`served(current) == served(best) − 2`) says hold while the code switches. The note's §The driver
  states the `auto` rule the code implements, and §Tests test 20 requires the two to be one
  implementation, so the note is internally inconsistent here and the code picks the `auto` reading.

### N10 — `blockedByPhaseTicks` accumulates rather than counting *consecutive* ticks
- Where: `src/signals/phases.nim:24, 36` (the `>= maxRedTicks` test) and `:141` (increment) / `:156`
  (the only reset, on crossing).
- Observed: the counter is incremented whenever the intersection may discharge and the phase forbids
  the stop-line car's movement, and is reset only when that car crosses. A car blocked 30 ticks by
  the phase, then blocked 40 ticks by spillback (which increments `spillbackBlockedTicks` and leaves
  `blockedByPhaseTicks` at 30), then blocked 30 more by the phase reaches 60 without 60 consecutive
  phase-blocked ticks.
- Note says: "a stop-line car whose movement has been forbidden for 60 **consecutive** ticks".
- Inferred, not observed in a run: this makes the starvation override slightly more eager, never
  less; the override is still bounded and latched (`overrideLeft = minGreenTicks`).

### N11 — `stops` is not counted for cars waiting in a gate queue
- Where: `src/signals/vehicles.nim:184-200` (link cars: `if sim.cars[car].movedLastTick: inc sim.cars[car].stops`)
  vs `:201-209` (gate-queue cars: no `stops` increment).
- Note's tick step 8 applies "if the car moved on the previous tick and not on this one, `stops += 1`"
  to "every car still on the network (link cell **or gate queue**)". `stopsTotal` is
  measured-but-never-scored, and the omission is symmetric across seats.

### N12 — Playback speed and duration differ from the note's arithmetic
- Where: `src/signals/sim_types.nim:39` (`PlaybackSpeeds = [1, 2, 4, 8, 16]`),
  `src/signals/replays.nim:207` (`result.speedIndex = 1`), `:36` (`FramesPerTick = 2`),
  `sim_types.nim:33` (`TargetFps = 24`).
- Observed: the default speed index is **1**, i.e. speed 2, so playback runs 2 ticks per 2 frames at
  24 fps = **24 ticks/s**, and a 256-tick episode plays for ~10.7 s. The starter's
  `src/ctf/replays.nim:252` uses `speedIndex = 0` with `PlaybackSpeeds = [1,2,3,4,8,16]`.
- Note says: "one tick per two animation frames at 30 fps = 15 ticks/second (speed chips
  `[0.5, 1, 2, 4, 8]`, default 1) … A 256-tick episode therefore plays for **17.1 s**, which is what
  lets `viewer_smoke.mjs --soak 10` observe real advancement". `replays.nim:38` and
  `tests/test_signals_engine.nim:117-119` both say "~21 s", which is the 12 ticks/s figure the
  default speed index does not produce.
- Consequence, observed in CI (run 33187823599, job 98905709185):
  `soak: 10s of playback kept advancing ("3 / 256" -> "195 / 256" -> "244 / 256")`. The soak passes
  with 12 of 256 ticks to spare. Inferred: the margin is thin but real, and the endcard hold
  (`ReplayEndHoldSeconds = 10`) plus `#clock` still changing would not rescue a frozen readout, so a
  future increase in `maxTicks` or in load time could flip it.

### N13 — `results.variant` and the replay config's `variant` are always `"grid4x4"`
- Where: `coworld_manifest_template.json` — no variant's `game_config` carries a `variant` key, and
  `variant` is not a `config_schema` property; `src/signals/sim_config.nim:161` reads it only if
  present; `sim_config.nim:12-20` defaults it to `"grid4x4"`.
- Observed in the CI artifact: `smoke-replay/results.json` → `"variant": "grid4x4"`.
- Consequence, inferred: a hosted `rushhour` episode records and reports `variant: "grid4x4"`. The
  city is rebuilt from the explicit cell constants in the config JSON, not from the variant name, so
  re-derivation is unaffected — this is a labelling defect, not a determinism one.

### N14 — The board never draws the green-wave sweep
- Where: `src/signals/global.nim:33` (`WaveSpriteId`), `:45` (`WaveObjectBase`), `:88`/`:123`
  (`bakedWave`), and `src/signals/rig_art.nim:524` (`bakeWaveChip`). `grep -rn "WaveObjectBase" src/`
  finds only the declaration: `buildBoardPacket` (`global.nim:206-345`) never places a wave object.
  `src/signals/labels.nim:46` declares the `wave` label and `tests/label_manifest.txt:88` pins it, so
  the manifest carries a label the compositor cannot emit.
- Note's §Readouts 3 asks for "a bright band [that] sweeps the corridor's lane in the direction of
  travel … the four stop lines on that corridor flash green in sequence". The banner, the feed line,
  the scrubber beat and the corridor tally are all implemented
  (`tools/page_sig_block.html:479-485`, `:379-411`).

### N15 — The quadrant corner label is a row letter, not the controller's alias
- Where: `src/signals/rig_art.nim:356-372`.
- Observed: `result.drawLabel($intersectionName(firstAt)[0], …)` draws the **first character of the
  quadrant's first intersection name** — "A" for both Alpha (A1) and Beta (A3), "C" for both Gamma
  (C1) and Delta (C3) — in the owner's tint.
- Note says: "each quadrant tinted faintly in its owner's colour **with the owner's alias** set at
  its outer corner". The two-name-space rule is not at risk (no real name is drawn, and the glyph
  table at `rig_art.nim:152-173` can only render `A B C D 1 2 3 4`), but the label does not identify
  the controller.

### N16 — Intersection labels are baked into the static bed, so the `.tiny` label rule cannot apply
- Where: `src/signals/rig_art.nim:330-332` bakes `A1`…`D4` into the one-time bed;
  `src/signals/global.nim:228-231` ships the bed as four fixed sprites.
- Note's §Legible at 360 px rule 3: "Under `.tiny`, **intersection labels are drawn only on the four
  corner intersections** and the queue heatmap becomes the primary readout — car chips drop their
  chevrons and render as 4 px dashes". Only the car-dash half is implemented
  (`global.nim:274-281` via the `t:` command, `global.nim:147-148`,
  `tools/page_sig_block.html:448-453`).
- Related: `tools/page_sig_block.html:249` — `#stage.tiny #board { --strict-text-bounds: 1; }` is an
  inert custom property, not a mechanism; the real signal is the `t:1` command on the same page.

### N17 — Labels are drawn with a hand-rolled 8-glyph bitmap font, not `data/font.ttf`
- Where: `src/signals/rig_art.nim:152-192` — an 8-entry 3×5 glyph table covering only `A B C D 1 2 3 4`.
- Note's §Art: "the intersection labels (`A1`…`D4`, set in `data/font.ttf`)". `data/font.ttf` ships
  and is served by the game (`src/signals/server.nim:58, 156-157`) but is not used for the bake.

### N18 — The corridor tally's `waves` figure is the in-window credit count, not a wave tally
- Where: `src/signals/broadcast.nim:197-212` — `"waves": sim.waveTicks[bucket].len + sim.waveTicks[bucket + 1].len`.
- Observed: `flow.nim:186` clears `sim.waveTicks[bucket]` the moment a wave fires, so the tally's
  number **drops to 0** exactly when a wave happens.
- Note's §Readouts 3: "a per-corridor tally (`8` tiny bars …) **increments**".

### N19 — Clock column layout differs from the note
- Where: `tools/page_sig_block.html:432-445` (`renderClockCol`).
- Observed: `#clock-time` is set to `THROUGH <n>` and `#clock-caption` to
  `demand … · waiting … · spillback … · gridlock … · waves …`. There is no `/ <par> par` sub-line;
  par rides the `title` attribute only. `#tick-clock` (the inherited transport readout) carries
  `<tick> / 256`.
- Note's §Readouts 5: "`#clock` shows the big numeral `THROUGH 372` with `/ 260 par` beneath it;
  `#clock-time` shows `tick 241/256 · turn 31/32`; `#clock-caption` shows `demand …`".
- Confirmed against the CI log's `clock` readout:
  `"THROUGH 206 DEMAND 367 · WAITING 28924 · SPILLBACK 3 · GRIDLOCK 0 · WAVES 0"`.

### N20 — The wave banner says "row" for column corridors
- Where: `tools/page_sig_block.html:481-482` — `CTX.banner(('row ' + e.corridor + ' ' + e.dir + ' wave …'))`.
- Observed: `broadcast.nim:146` emits `corridor` as `"A".."D"` for east–west and `"1".."4"` for
  north–south (`sim_state.nim:289-296`), so a northbound wave banners as `ROW 2 NORTHBOUND WAVE`.

### N21 — The server does not refuse to start when a joined seat has no register record
- Where: `src/signals/server.nim:505-522`.
- Observed: the server logs loudly (`"SEAT n (Alpha) JOINED WITHOUT A REGISTER RECORD — refusing to
  treat it as a policy; it plays the published default and is reported as dead"`), sets
  `deadSeats[slot] = true` and calls `declarePlayerFailure`, then **plays the episode anyway**.
- Note's §The three named edits to `server.nim` (edit 2) and §Tests test 26 both say the server
  "refuses to start the game". The lobby loop does hold until `allSeatsRegistered()` or
  `lobbyJoinTimeoutTicks` (`server.nim:486-499`), so an unregistered seat costs the full lobby
  timeout and then plays greedy — which is consistent with §Degrade's "a seat that never connects …
  does not end the episode", and inconsistent with edit 2.

### N22 — `/client/replay` exists as a local route
- Where: `src/signals/server.nim:42, 152-155`.
- Observed: the game serves the embedded broadcast page at `/client/replay`, `/client/global` and
  `/client/league`. Nothing declares it to the platform: `coworld_manifest_template.json:9` declares
  only `"replay_viewer": {"bundle": "static-replay-viewer"}`, and the release workflow's guard
  (`coworld-release.yml:209-210`) rejects a pod-served viewer.
- Checklist item 3 says "No `/client/replay` pod path anywhere". Read literally the string exists;
  read as "no pod-served viewer is declared" the repo complies, which is what the note states
  (§Viewer: "the game still serves `/client/replay` locally for developers") and what the starter
  does. I record the fact rather than deciding it.

### N23 — Zoom gesture handlers survive the `#viewpanel` removal
- Where: `client/replay_broadcast.html:1863-1864` (keys `z`/`x`), `:1921` (wheel), `:1938`/`:1993`
  (pinch), all calling `core.zoomAt` / `core.setZoom`.
- Observed: the panel itself is fully gone — markup, CSS, ids and the `core.attachMinimap(...)` call
  are all deleted (I diffed the inherited region against the starter; `grep -c` finds 0 occurrences
  of `viewpanel`/`zoombar`/`zoom-*`/`fpv*`/`povBadge` in the page, and the only `minimap` hit is a
  comment at `:2022`). The panel's own button/slider wiring (`btnZoomIn`, `btnZoomOut`, `zoomSlider`,
  `minimapBox`) went with it.
- Checklist item 14's bullet names "the `core.zoomAt/setZoom/attachMinimap` wiring" as part of what a
  fixed-arena game removes with the panel. On my reading the phrase means *the panel's* wiring, all
  of which is gone; the surviving handlers are the starter's own gesture path, which the note keeps
  deliberately (`replay_broadcast.html:2045-2047`, `syncViewUi`). Recorded so the judge can rule.

### N24 — `tools/ci/viewer_smoke.mjs` is not the current template
- Where: `tools/ci/viewer_smoke.mjs:425-447, 574`.
- Observed: `diff coworld-builder/templates/tools/ci/viewer_smoke.mjs` against the repo copy shows 30
  lines of difference, all of them the lineage-selector fallbacks added to the template in
  coworld-builder commit `33208c1` on the same day. The repo's copy probes `#clock`, `#scorebug`,
  `#scrub`, which are exactly the ids this page uses (it is the paintbot lineage), so nothing is
  lost — CI reported real values for all three.
- Note's test 43 says "copied verbatim from `coworld-builder/templates/tools/ci/viewer_smoke.mjs`".

### N25 — `replay_summary.py`'s `policyKinds` is one entry per register record, and `names` are aliases
- Where: `tools/replay_summary.py:154-171`.
- Observed on the real CI replay: `policyKinds` has **12** entries for 4 seats, because the player
  re-sends its registration up to 10 times (`src/sumo_traffic_signals_player.nim:119-128`) and the
  server writes a fresh `register` record on every drain (`src/signals/server.nim:325-327`).
  `names` is read from the config JSON's `players[]`, which is `["Alpha","Beta","Gamma","Delta"]`.
- The phase-60 recipe in the note works: order entries derived from `directive` records carry
  `source` (`replay_summary.py:127-134`), so `[.orders[]|select(.source=="llm")]` will be non-empty
  on a champion episode. On the all-scripted CI replay the observed source set is
  `["applied","scripted"]`, as expected.
- `tests/test_signals_replay.nim:157-161` asserts `registers == MaxSeats`, which holds for the
  in-process recorder but not for a socket episode.

### N26 — The note's claimed `ctf_`/`CTF_` CI grep does not exist
- Where: `.github/workflows/ci.yml` (read in full — no such step).
- Observed residue in the inherited page region: `client/replay_broadcast.html:1385`
  (`src: 'ctf-replay'`) and `:1464` (`m.src !== 'ctf-shell'`). Neither matches `ctf_`/`CTF_`.
  `client/chrome_common.js:72` reads `window.CTF_WIRE` by design (see §Traced, provenance).

### N27 — System prompt differs from the note by one reworded line
- Where: `src/signals/llm.nim:236`.
- Observed: `A car covers one cell per tick, and an east-west block is 6 cells, a north-south 4.`
  vs the note's `A car covers one cell per tick; an east-west block is 6 cells, a north-south block 4.`
  Everything else in the 50-line prompt is byte-identical (diffed). Both champion `PLAYER_PROMPT`
  texts in `tools/ci/policies.json` are byte-identical to the note.

### N28 — Test coverage that does not assert what the note says it asserts
All 45 numbered tests are present; these are the ones whose assertions are narrower than the note's
description.
- `tests/test_signals_engine.nim:121-151` (test 26, "no seat can stall"): the note asks for a seat
  that connects then never answers, and a seat that never connects, both finishing inside the
  wall-clock budget "with `fallbackTurns` counted, `deadSeats` set, and exactly one closed-schema
  failure payload". The implemented test runs an all-scripted in-process episode, then **constructs
  the failure payload literally in the test** (`:133-141`) instead of exercising
  `declarePlayerFailure` (`server.nim:344-358`), and checks `allSeatsRegistered`/`unregisteredSeats`
  in isolation. No socket path, no `deadSeats`, no `fallbackTurns` assertion.
- `tests/test_signals_driver.nim:235-244` (test 21, the 4096-byte read cap): asserts the constant and
  a `truncateRunes` call on ASCII; does not exercise `llm.textOf` (see N6).
- `tests/test_signals_viewer.nim:70-84` (test 36, "`broadcast_core.js`'s kept procs are
  byte-identical to the starter's"): reads `client/chrome_common.js` into `starter` and only checks
  `starter.len > 0`; the actual assertions are substring-presence of eight function signatures. The
  starter is not vendored, so a byte comparison is not available in-repo. (I did the byte comparison
  myself — see §Traced.)
- `tests/test_signals_sim.nim:437-453, 466-486` (test 12, gridlock ring): `buildRing` sets
  `linkFullTicks[link] = ringTicks` directly; the note's "raises `gridlock` at **exactly**
  `ringTicks`" is not driven through 20 real ticks.
- `tests/test_signals_sim.nim:580-590` (test 13, clean crossings): the final "a stop resets
  `cleanCrossings` to 1" assertion is inside `if sim.cars[car].active and sim.cars[car].crossings > before`,
  so it can pass while asserting nothing.
- `tests/test_signals_sim.nim:294-320` (test 8, starvation override): asserts the override fires and
  `lastResult == orOverridden`; does not assert the `minGreenTicks` latch length or the return of
  control to the seat's order.
- `tests/test_signals_driver.nim:63-66` (test 18): bounds the serialised **orders array** at 1024
  bytes, not "the serialised directive" the note names.

### N29 — Smaller notes
- `coworld_manifest_template.json` `config_schema` declares one property the note's list does not:
  `speed`. `additionalProperties: false`, all three arrays carry `minItems`/`maxItems`
  (`tokens` 4/4, `players` 4/4, `slots` 0/4).
- `src/signals/global.nim:337-339`: gate-pip object ids are `GatePipObjectBase + g * 16 + i`; with
  `gateQueueCap` clamped to 64 (`sim_config.nim:103`) a config above 16 would collide ids across
  gates. The shipped value is 12.
- `src/signals/sim.nim:367-373`: the radio block iterates seats in ascending slot; the note says
  "most recent first". All lines are from the same turn, so there is no recency order to lose.
- `src/signals/directives.nim:53-61`: `sanitizeLine` drops `{` and `}` from `say`/`notes` (documented
  in the code as the record-vs-radio discriminator); the note's caps table does not mention it.
- `src/sumo_traffic_signals_player.nim:120-129`: the inner receive loop has no time bound and relies
  on the socket closing. It is in the player container and cannot stall the game (the game waits on
  seats only through the bounded lobby), and the outer reconnect loop is capped at 6.
- `src/signals/broadcast.nim:126-134`: the derived `gridlock` event's `links`/`ats` are read from
  `sim.activeGridlock` **at emit time**, not at the event's tick. In live play `stepEvents` runs once
  per turn, so a gridlock event can list a ring measured up to 8 ticks later. Non-hashed, cosmetic.

---

## Traced and consistent

**Checklist item 1 (CI).** `gh run list -R Metta-AI/cogame-sumo-traffic-signals --branch main -w ci.yml`
→ run **33187823599**, conclusion **success**, `head_sha 54fd04080b0c2e75275b5ada197b431fa6dc3023`,
event push. Jobs: `test` 98905311538 ✓, `docker-smoke` 98905311299 ✓, `wasm-viewer` 98905709185 ✓.
Every step in all three jobs is `success` or `skipped` (only step 8, the PR-only GameVersion
collision check, is skipped). The "no test loosened" half is B1.

**Checklist item 2 (replay re-derivation).** `src/signals/replays.nim:243-263` `checkReplayHash`
compares the recorded hash against `sim.gameHash()` **every tick** and records `hashMismatchTick`.
`stepReplay` (`:265-281`) applies the order record, steps the same `stepTick`, applies the stop
record through the same `applyStop`, then checks. `replay-viewer/signals_replay.nim:3` imports
`signals/sim` — the identical module the server runs, compiled to wasm by
`replay-viewer/config.nims:9` (`switch("path", rootDir / "src")`).
`tests/test_signals_replay.nim:62-124` records and re-derives **all five** end rules (`cleared`,
`gridlock`, `fullPeriod`, `wallClock`, `fault`) and asserts `hashMismatchTick == -1` both from the
load-time prescan and after a seek to `maxTick`. `:216-241` re-simulates from the bytes on a fresh
sim and compares every per-tick hash element-by-element. The wall-clock stop is a real record
(`decide.nim:93-96` `stopRecord`), applied by `sim.applyStop` on record (`server.nim:570-572`) and on
playback (`replays.nim:278-280`) — the same proc.

**Checklist item 3 (static viewer).** Manifest declares
`game.replay_viewer = {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:9`, under
`game`, not top level). `tools/build_replay_viewer.sh` is present and committed `100755`
(`git ls-files -s`), asserted for `-x` in `ci.yml:306-317` and invoked by path at `:330`, and the
release workflow guards on it (`coworld-release.yml:209-210`). The bundle's only network access is
`fetch(message.replayUrl)` in `replay-viewer/static_replay_worker.js:113`, from
`new URLSearchParams(location.search).get('replay')` (`static_replay.js:186`) — no other `fetch`,
`XMLHttpRequest` or absolute URL exists in either file. See N22 for the local dev route.

**Checklist item 4 (two name spaces).** In-game names are `seatAlias(slot)` →
`Alpha/Beta/Gamma/Delta` (`sim_types.nim:264, 279-285`). The observation builder
(`sim.nim:301-407`) uses only `seatAlias`, `seatQuadrant`, intersection/link/gate ids — I read every
field; `sim.players[].name` appears nowhere in it, in `cityBlockJson`, or in the user message
(`llm.nim:252-264`, which is `operatorBlock(PLAYER_PROMPT) + view`). Real names ride
`results.names` (`roster.nim:136`), the replay join records (`server.nim:470-471`) and the spectator
roster (`roster.nim:82-105`), and the viewer maps them onto the plates
(`tools/fork_broadcast_page.py:470` via `teamName`), the pressure rail
(`tools/page_sig_block.html:341-344, 369`) and the endcard (`:517, 545`).
`showPlayerLabels` is `false` in every variant and in the cert fixture, and defaults false
(`sim_config.nim:54`). `tests/test_signals_viewer.nim:244-249` asserts no board label carries a real
name.

**Checklist item 5 (degrade never hang) — every wait and its bound.** All observed:
| wait | bound | where |
|---|---|---|
| LLM attempt 1 | `attempt1Ms = 9000` → `CURLOPT_TIMEOUT` 9 s (integer-second floor is an identity; `sim_config.nim:126` clamps ≥ 1000) | `decide.nim:237-256` |
| LLM retry | `retryMs = 4000` → 4 s | same |
| whole turn | `turnBudgetMs = 14000` monotonic, checked before each attempt | `decide.nim:159, 231-236` (see N3) |
| batch spacing | `turnSpacingMs = 12000` floor between batch starts, one bounded `sleep` | `decide.nim:218-224` |
| rolling rate | `RateGuardMaxRequests = 28` in `RateGuardWindowSeconds = 60`; over-budget seats take greedy, never sleep | `decide.nim:132-137, 200-215`; `sim_types.nim:76-77` |
| budget guard | `elapsed + 2 × ceil(turnBudgetMs/1000) > wallClockBudgetSeconds` → LLM off for the rest | `decide.nim:164-172` |
| lobby | `while sim.lobbyTicks < lobbyJoinTimeoutTicks` with `sleep(1000 div 24)`: 2400 ticks = 100 s (cert 600 = 25 s) | `server.nim:486-499` |
| engine stop | `elapsed >= wallClockBudgetSeconds` checked at the top of every turn; clamped ≤ 660 | `server.nim:538-543`; `sim_config.nim:132-133` |
| shutdown grace | `gameOverTicks = 48` × 1/24 s = 2 s | `server.nim:587-594`; `sim_types.nim:104` |
| replay frame | `steps = min(steps, 64)` per frame | `replay_runtime.nim:84` |
| seat sockets | mummy's serve thread runs independently of the game loop (`server.nim:413-419, 473-479`); global broadcasts are fire-and-forget (`server.nim:223-243`) | |

Total (inferred from those bounds): worst case = 32 turns × max(12 s spacing, 9 s + 4 s calls) ≈
448 s, + lobby ≤ 100 s + settle/artifacts + 2 s grace ≈ **≤ 570 s**, with the engine stop at 660 s
and the last started turn able to overrun it by ≤ ~21 s → **≤ ~683 s < 720 s**. The only `while true`
loops in the tree are `runReplayLoop` (`server.nim:421-442`, entered only when
`COGAME_LOAD_REPLAY_URI` is set — local developer replay mode, never the episode path) and the
player container's receive loop (N29). `server.nim:566-567` breaks the turn loop if a turn advanced
no ticks ("never spin"). `tests/test_signals_engine.nim:198-204` asserts the arithmetic.

**Checklist item 6 (`num_agents`).** Present in both variants' `game_config` and in
`certification.game_config`, value 4, and **absent at every variant top level** (variant keys are
exactly `id/name/description/game_config`). `certification.players` = 4 entries,
`certification.game_config.players` = 4 entries. `tools/ci/docker_smoke.sh:110-151` enforces all four
invariants with `SEAT-COUNT FAIL:` prefixes, plus the `SMOKE_SEATS` cross-check
(`:54` `seats_expected="${SMOKE_SEATS:-4}"`, `:146-151`). I grepped the full docker-smoke job log of
run 33187823599 for `SEAT-COUNT` — **no matches**; the job printed
`smoke OK: seats=4 results=960B replay=73396B reason=complete`.
`tests/test_signals_manifest.nim:19-70` pins all of it.

**Checklist item 7 (scripted baseline plays legally to the end).**
`tests/test_signals_engine.nim:14-42` runs a real four-seat scripted episode through
`runEpisode` with a temp-dir `COGAME_*` set, asserts `results.json` and the `.replay` exist,
`reason == "complete"`, `throughput > 0`, `scores` equal `sim.scoreOf(slot)`, and the two identities.
`tests/test_signals_driver.nim:39-66` checks 200 pseudo-random worlds × both baselines × all four
slots for order-count, ownership, uniqueness, verb/phase enum membership, `phase != phCLR`, and
`0 ≤ delay ≤ turnTicks-2`. The tunables are the sweep's: `tools/tune_baselines.nim` writes
`tools/ci/baseline_tuning.json`, `ci.yml:167` re-runs it with `--check`, and
`tests/test_signals_tuning.nim` pins the shipped defaults against the record and against every
variant. Confirmed end-to-end in CI on the real image: `results.json` from the smoke artifact reads
`reason: complete, endRule: fullPeriod, throughput: 217, finalTick: 256, turnsPlayed: 32`.

**Checklist item 8 (LLM reply handling).** `extractJsonObject` (`directives.nim:84-123`) scans for
the outermost balanced `{…}` with string/escape awareness, tolerates fences and prose, and falls back
to first-brace..last-brace. `parseControllerReply` (`:159-239`) repairs rather than rejects at every
field, accepts `orders` as an array **or** an object keyed by intersection id (`:140-157`), and a
`say`-only reply is usable. Exactly one retry: `while open.len > 0 and attempt < 2`
(`decide.nim:228`), with the retry batch carrying a corrective suffix (`:242-244`). The fallback is
the shared greedy proc — `installScripted(…, blGreedy, dsFallback)` →
`sim.scriptedReply(slot, blGreedy)` → `baselines.nim:39` → `driver.greedyOrderFor`, the same proc the
`greedy` baseline uses, asserted by `tests/test_signals_driver.nim:99-127`. Every fallback is
recorded (`decide.nim:65-73`) and counted in `sim.fallbackTurns[slot]`, which reaches
`results.fallbackTurns` (`roster.nim:147, 188`).

**Checklist item 9 (rune-safe truncation).** `truncateRunes` (`sim_types.nim:268-277`) uses `runeLen`
/ `runeSubStr` only. Every capped string goes through it: `say` 120 and `notes` 240
(`directives.nim:47-64`), `policy` 64 (`decide.nim:85`, `roster.nim:49, 64`), `fallback.detail` 200
(`decide.nim:72`, `llm.nim:171, 180, 186`), `PLAYER_PROMPT` 4000 (`server.nim:307`, `llm.nim:259`,
and player-side `sumo_traffic_signals_player.nim:36-52`), `stopDetail` 200 (`sim.nim:108`,
`roster.nim:191`, `server.nim:353`), the whole directive record 4000 (`directives.nim:290-311`, which
drops the `view` rather than cutting the serialised JSON). `tests/test_signals_driver.nim:216-233`
feeds 200/400 four-byte 🚦 through the validator and asserts `runeLen == cap`,
`validateUtf8() == -1`, and `len == cap * 4`. `tests/test_signals_replay.nim:164-214` runs
`tools/replay_summary.py` over a replay whose capped fields are filled with the same emoji and
asserts a strict UTF-8 JSON parse and `protocol == "signals/v1"`. I ran `replay_summary.py` against
the real CI replay myself: it emits valid JSON with `protocol signals/v1`, `gameVersion "1"`,
`tickCount 256`, 1024 order entries, 128 directives.

**Checklist item 10 (manifest validates).** `game.docs` = `{"readme":{"type":"uri","value":…},
"pages":[{id,title,content:{type,value}} × 3]}`. `game.protocols` carries **both** `player` and
`global`, each an object `{"type":"uri","value":…}`. `game.description` present (>40 chars),
`game.tags` absent, top-level `tags` has 5. `episode_timeout_minutes: 20` at top level, not under
`game`. No top-level `version`, no `game.display_name`, `game.owner` present. `results_schema` has
exactly 39 properties, `additionalProperties: false`, `reason` enum
`["complete","deadline","fault"]`, `endRule` enum
`["cleared","gridlock","fullPeriod","wallClock","fault"]`; `tests/test_signals_engine.nim:44-67`
asserts the emitted key set equals it exactly in both directions and that `roster.resultsKeySet()`
agrees — and the real CI `results.json` has 39 keys.
No `game_config` anywhere contains a literal `tokens` array, while `config_schema.required` still
lists it. `ci.yml:187-217` attempts the installed CLI's own `validate_upload_manifest`.

**Checklist item 11 (legible at 360 px).** `tools/page_sig_block.html:35-41`:
`.plate .plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`,
deliberately scoped through `.plate` so it outranks the inherited `.plate .team-name` rule.
`relayout()` toggles `#stage.tiny` at `boardW <= 620` (`replay_broadcast.html:2116`, the starter's
threshold) and the `.tiny` rules hide the quadrant tag, the `Served` label and the rail's `waiting`
figure (`page_sig_block.html:242-255`). `--hudscale = clamp(0.5, boardW/760, 1.6)` (`:2114`).
Board aspect `34/26 = 1.3077` (`sim_types.nim:115-116`; the geometry closes exactly:
`boxX(3)+2+4 = 34`, `boxY(3)+2+3 = 26`), asserted by `tests/test_signals_viewer.nim:172-174`.

**Checklist item 12 (release order and scaffold).** `coworld-release.yml` runs
Build the Coworld manifest (`:159`) → Certify locally (`:173`, `--timeout-seconds 300` at `:184`) →
Upload the policies (`:216`) → Upload the Coworld (`:314`) → Put the Coworld secret (`:410`), in that
order and in one job with a freshly built binary. All three workflows present.
`tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both `100755` in the index.
`tools/ci/policies.json` has four distinct policies, all `run: /bin/sumo-traffic-signals-player`:
two `PLAYER_PROMPT` champions (`signals-greenwave`, `signals-gatekeeper`) and two scripted fillers
(`signals-greedy`, `signals-fixedcycle`); champion #2 carries
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` and champion #1 carries none; no
`USE_BEDROCK`. Both champion prompt texts are **byte-identical** to the design note (diffed
programmatically). The placeholder gate:
```
grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml .github/workflows/coworld-release.yml \
  .github/workflows/coworld-submit.yml tools/ci/docker_smoke.sh tools/ci/policies.json
```
→ **no matches, exit 0**. Surviving angle-bracket names are exactly the expected residue:
`<cow_id>`/`<sha>` in `ci.yml:283`, `<run_id>` in `coworld-release.yml:21` and
`coworld-submit.yml:17`, `<name>` in `coworld-submit.yml:31`, plus two more `<cow_id>` in
`coworld-release.yml:75, 358` (the same class of runtime value).

**Checklist item 13 (viewer executes).** `wasm-viewer` `needs: docker-smoke` (`ci.yml:293`) and every
step is green in run 33187823599, **including** "Load the bundle in a real browser"
(`tools/ci/viewer_smoke.mjs`, headless chromium, Playwright pinned 1.55.0 in both places, loading
`dist/smoke/episode.replay` — the replay docker-smoke produced and uploaded as `smoke-replay`). It is
not `continue-on-error` and is not commented out. Its stdout:
```
{"loaded":true,"ms":606,"clock":"THROUGH 206 DEMAND 367 · WAITING 28924 · SPILLBACK 3 · GRIDLOCK 0 · WAVES 0", …}
soak: 10s of playback kept advancing ("3 / 256" -> "195 / 256" -> "244 / 256")
scrub readouts: 0%="THROUGH 206 …"  50%="THROUGH 96 …"  100%="THROUGH 217 …"
```
`data-replay-loaded="true"` is set on `<html>` in `static_replay.js:158-161`, in the `'loaded'`
branch the Worker posts only after `ingestPacket()` has handed the core the first frame;
`data-replay-error` is set in `showFailure()` (`static_replay.js:8-20`). Both are the starter's own
code paths, inherited unchanged (I diffed both files against
`/workspace/starters/coworld-ctf/replay-viewer/`: the entire difference is two identifier renames).
**No lobby dwell is possible in this replay format**: the codec (`/tmp/bitworld/src/bitworld/replays.nim`)
has no `gameStart` record at all, and the server writes hashes only inside the turn loop
(`server.nim:555-559`) — the lobby produces no ticks and no hashes, so tick 0 *is* the game start and
`startTick` is legitimately 0. **Link flags and bootstrap are from the same starter**:
`replay-viewer/config.nims` has no `MODULARIZE` and no `EXPORT_NAME` (I grepped), and
`static_replay_worker.js:188-191` sets `Module.onRuntimeInitialized` with `self.Module = Module`
before `importScripts('./wire_constants.js', './broadcast_core.js', './signals_replay.js')` at
`:239` — the non-modularized pairing. `tools/wasm_replay_smoke.cjs` ran the emitted module headless
in node against the same replay: `ok: loaded episode.replay, advanced 300 frames`.

**Checklist item 14 (chrome is the starter's).**
- `client/chrome_common.js` is **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js`
  (`diff` clean; both sha256 `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`,
  40 022 bytes), pinned as a literal in `tests/test_signals_viewer.nim:11-13`. It still reads
  `window.CTF_WIRE` (`:72`) and `src/signals/wire_constants.nim:26-36` publishes
  `window.SIGNALS_WIRE` and aliases `window.CTF_WIRE` to it precisely to preserve the byte pin —
  this is builder divergence (4), verified, and the reason is documented in the module header.
- `client/broadcast_core.js` differs from the starter's by **exactly one line** (`:49`,
  `CTF_WIRE` → `SIGNALS_WIRE`) — builder divergence (3), verified. The board is drawn Nim-side
  through the sprite protocol (`src/signals/global.nim`, `src/signals/rig_art.nim`), so the note's
  `drawCityBed`/`drawQueueHeat`/… live there, as the builder recorded.
- `client/replay_broadcast.html` **reproduces byte-for-byte** from the starter's page plus
  `tools/page_sig_block.html` through `tools/fork_broadcast_page.py`: I ran
  `python3 tools/fork_broadcast_page.py /workspace/starters/coworld-ctf/client/replay_broadcast.html tools/page_sig_block.html /tmp/forked.html`
  and `diff /tmp/forked.html client/replay_broadcast.html` is clean. The file is 2 718 lines vs the
  starter's 4 660, and I diffed the inherited region line-range by line-range: every deletion is on
  the note's removal list — the FPV/POV pipeline (starter `:2347-3466`, 1 120 lines), the
  `#viewpanel` CSS/markup/wiring, the ctf scorebug internals and `.squad` pips, the paintbot event
  routing (`kill`/`steal`/`return`/`capture`), the paintbot endcard (replaced by the signals
  endcard), the flag-icon wiring, the `.ec-heart`/`.ec-badge` glyphs and the beat CSS for kinds this
  game never emits. Sections 1–5 (stage, scorebug, banner lane, kill feed, transport, scrubber +
  momentum + beat markers + lulls + spoilers, endcard, locker-room curtain) survive; the appended
  block starts at `:2148` under the banner
  `sumo-traffic-signals additions to the inherited coworld-ctf chrome`.
- Transport rules, each read in the page: (a) `relayout()` (`:2080-2124`) measures `#transport` and
  `#scorebug` and sets `--band`, `--topband` and `--hudscale` on `document.documentElement`
  (`root.style.setProperty` at `:2115, 2120, 2121`) — `:root`, not `#stage`. (b) The only game-block
  overlay, `#sigrail`, is appended **inside `#scorebug`** (`page_sig_block.html:287`,
  `#scorebug { flex-wrap: wrap }` at `:29`), i.e. inside the measured top band; `#killfeed` rides
  `bottom: calc(76 * var(--u))` and `#endcard` `inset: var(--topband) 0 var(--band) 0`
  (`replay_broadcast.html:612-618`). (c) `#endcard` keeps `bottom: var(--band, 0px)` (`:618`), is
  shown with `#endcard.on` (`:629`, `renderEndcard` adds `'on'`), and every frame whose phase is not
  `gameover` removes it (`:1535`, the starter's path) — so any seek away from the end takes it down.
  (d) Beats are `<button class="beat-marker <kind> <colour>" title aria-label>` appended to `#scrub`
  with a click handler that sends `s:<tick>` (`page_sig_block.html:295-315`), and the CSS covers
  exactly `{wave, spillback, gridlock, fallback, end}` (`:170-174`), asserted set-equal by
  `tests/test_signals_viewer.nim:123-144`. The block never calls `markBeat`
  (`tests/test_signals_viewer.nim:115-116`).
- `#viewpanel` and the minimap are **dropped**, not hidden: 0 occurrences of `viewpanel`, `zoombar`,
  `zoom-in/out/slider/read`, `fpv*` and `povBadge` in the page; the only `minimap` hit is a comment;
  `core.attachMinimap(...)` is gone. `broadcast_core.js` tolerates never being attached
  (`minimapSurface`/`minimapCtx` stay null). See N23.
- Endcard vocabulary: `tests/test_signals_endcard_labels.nim` scans the page and
  `broadcast_core.js` outside comments for `Lives/LIVES/Clstr/Cap</flag/heart/paint/hopper/hill/POV/
  spray/grenade/med kit/kill` and asserts zero, plus seven re-mapped strings present exactly once.

**Checklist item 15 (every drawn string fits its frame).**
- `--strict-text-bounds` is on **both** smoke steps (`ci.yml:400` and `:424`).
- Bundle run: `canvas text: 0 drawn, 0 never inside the canvas, 0 ellipsized`. `total: 0` is expected
  and, per the checklist, is not evidence: the board is drawn in a Dedicated Worker on an
  OffscreenCanvas (`static_replay.js:89`, `static_replay_worker.js` `minimap`/`resize` handling), so
  the main-thread instrumentation sees nothing.
- Renderer fixture run (`tools/ci/renderer_fixture.html`, its own `ci.yml` step at `:410-425`):
  `canvas text: 600 drawn, 0 never inside the canvas (0 draws crossed an edge), 48 ellipsized`.
  `never_inside == 0` at 360/620/900 px is the gated number and it is 0.
- The remark path is unclipped and therefore transcribed in full: `.feed-row` is
  `white-space: nowrap; max-width: none` with **no** `overflow: hidden` and no `text-overflow`
  (`replay_broadcast.html:377-394`), and `.feed-row .badge` (`:401-409`) adds none, so the fixture's
  `clips` test (`renderer_fixture.html:188-189`) is false for it and it is drawn at its measured
  left edge. Since `never_inside == 0`, the 109-rune radio line landed inside the canvas at every
  width. Every `text-overflow: ellipsis` rule in the page is on a **name label** — `.plate .team-name`
  (`:205-208`), `.plate .plate-name` (`:2183-2184`), `.pr-name` (`:2268-2269`),
  `#endcard .ec-team .ec-name` (`:2361-2362`), `#endcard .ec-tname` (`:692-693`),
  `#endcard .ec-row .pname` (`:754-755`), `#endcard .fl-cap`-adjacent (`:708-709`) — never a
  sentence; the endcard **headline** was explicitly moved off ellipsis to wrapping
  (`page_sig_block.html:229-238`, `overflow: visible; text-overflow: clip`).
- A band is reserved whether or not anything is speaking: `#killfeed` carries
  `min-height: calc(4 * 22 * var(--u))` — "fixed 4-row reserve" (`replay_broadcast.html:371`) — and
  `#stage.tiny #killfeed` a 3-row reserve at `:961`.
- See N1 for the fixture's string length.

**The one-parallel-batch rule.** `decide.nim:239-256`: one `RequestBatch` is filled with every open
seat's request and issued as a single `engine.client.curl.makeRequests(batch, …)`. There is no
per-seat call site anywhere; scripted seats never enter the batch (`:191-192`).

**Resolution rules — the 7-step turn order.** `server.nim:532-567` and `decide.turn`:
1 snapshot/observation (`sim.nim:301`, built per seat inside the batch loop at `decide.nim:241`);
2 one parallel batch with `attempt1Ms` (`decide.nim:237-256`); 3 one retry with `retryMs`, again as
one batch (`:228, 238`); 4 greedy + a `fallback` record (`:302-315`); 5 orders applied in ascending
slot then ascending intersection index, unnamed intersections keep their order, invalid entries
repaired to the previous order and counted (`sim.applyReply` at `sim.nim:184-207`,
`directives.nim:201-239`), orders naming a foreign intersection dropped and counted (`:194-196`);
6 `say` ≤ 120 and the accepted orders become replay chat records (`decide.nim:106-126` `ordersRecord`,
`directives.nim:266-288` `directiveRecord`), `say` is broadcast to every other seat next turn
(`sim.nim:367-373`), `notes` is echoed to that seat only (`sim.nim:406-407`);
7 `turnSpacingMs` floors the gap between batch starts (`decide.nim:218-224`).

**Resolution rules — the 13-step tick order.** `sim.stepTick` (`sim.nim:137-165`) calls, in the
note's order: `inc tickCount` + `rollMovedFlags` (1), `stepSignals` (2 — `phases.nim:40-119`, with
2a `ticksInPhase`/`requestedPhase`, 2b clearance, 2c enter clearance, 2d deferral counted, 2e the
starvation override latched for `minGreenTicks` and emitting `seStarve`), `dischargeStopLines` (3 —
`phases.nim:121-172`: ascending intersection, `N,E,S,W`, one car per approach, `blockedByPhaseTicks`
on a forbidden movement, `spillbackBlockedTicks` when the receiving cell 0 is occupied,
`crossings`/`cleanCrossings`/`waitSinceLastCrossing` bookkeeping and the corridor credit),
`advanceLinks` (4 — `vehicles.nim:129-148`, ascending link index, `i` from `L−2` down to 0),
`drainExits` (5 — `vehicles.nim:150-176`, every exit link every tick, so exit links never spill back),
`admitGateQueues` (6), `spawnDemand` (7 — `vehicles.nim:21-82`, the pure `mix64(seed,g,t)` hash,
opposite gate on `throughRunnerPermille`, `(h shr 24) mod 16` otherwise with the self-gate re-map,
`gateQueueCap` rejection counted), `accountWaits` (8, charged to the downstream owner —
`Σ seatWaitTicks == networkWaitTicks` by construction, asserted per tick over a whole episode at
`tests/test_signals_sim.nim:397-412`), `measureFlow` (9 — `flow.nim:45-79`), `detectGridlock` (10 —
`flow.nim:97-164`, DFS from the lowest link index, `ringEligible` requires `linkFullTicks >= ringTicks`,
never latched), the wave window (11, credited at the crossing in step 3 and evaluated in
`flow.nim:166-189`: trailing `waveWindow`, `waveVehicles` credits, window cleared so one wave is one
event), `mixTick` (12), `evaluateEnd` (13). `mixTick` (`sim.nim:28-73`) mixes in exactly the note's
order: per intersection `(phase, clearLeft, ticksInPhase, requested, order.verb, order.phase,
order.delay)`, per link `(occupancy bitmask, queueLen)`, per live car
`(link, cell, waitTicks, cleanCrossings, blockedByPhaseTicks)`, then `throughput, rejected,
demandGenerated, networkWaitTicks, seatWaitTicks[0..3], greenWaves`, then the sorted active spillback
set, the sorted active ring set, then `tick`.

**End conditions.** `evaluateEnd` (`sim.nim:116-131`): `cleared` when
`tick >= demandEndTick and cityEmpty()`, `gridlock` when `stallTicks >= gridlockStallTicks` (the
stall counter is incremented in `stepTick:155-163` only when no car exited and no car moved),
`fullPeriod` at `tick >= maxTicks`; `wallClock` from `server.nim:538-543, 569-572`. `EndReason`
is the closed three-value enum (`sim_types.nim:177-182`) mapped in `applyStop:109-113`; `EndRule` is
the closed five-value enum (`:169-175`). Both enums are mirrored in `results_schema`. See N2 for
`fault`.

**Scoring.** `scoreFor` (`sim_types.nim:387-392`) = `1_000_000·throughput − 1_000·netWaitK −
10·seatWaitK`, with `netWaitK = min(999, wait div 200)` and `seatWaitK = min(99, wait div 800)`
(`:394-398`) — one implementation, used by the sim, the results doc and the endcard.
`win[s] = throughput >= parThroughput`, the same for all four seats; `winner` is `null`
(`roster.nim:140, 158`). `tests/test_signals_scoring.nim` checks the formula over 500 random end
states, both analytic bounds (`netWaitK ≤ 696 < 999` from `(352 + 16×12)×256 = 139 264`;
`seatWaitK ≤ 71 < 99` from `224×256 = 57 344`), and lexicographic dominance in both directions over
500 more. I verified it against the real CI episode by hand:
`throughput 217, networkWaitTicks 30 678 → netWaitK 153; seatWaitTicks [8503,10456,4103,7616] →
seatWaitK [10,13,5,9]` gives `[216846900, 216846870, 216846950, 216846910]`, which is exactly the
`scores` array in `smoke-replay/results.json`.

**Replay writer.** `SignalsReplayMagic = "COWLDSIG"`, format version 1, `gameName
"sumo-traffic-signals"`, `gameVersion "1"` (`replays.nim:27-58`); a `const`, not a module-level
`let`, with the emscripten-ordering reason documented at `:41-48`. The writer opens with the
resolved config JSON (`sim_config.configJson:225-271` — seed, variant, num_agents, every rule
constant, `players[]`, `slots[]`, `fastMode`, and **never** `tokens`, asserted at
`tests/test_signals_replay.nim:147-148`), then four join records (`server.nim:469-471`), the register
chats, one `orders` record per turn (the whole input log, 16 entries + the four `say` lines), the
`directive`/`fallback`/`budget_guard` chats, one `writeHash` per tick (`server.nim:559`), the `stop`
record when the wall clock fires, and one `result` record. Size on the real episode: 73 396 bytes
for 256 ticks.

**Divergences the builder recorded — all ten verified as stated:**
1. Test 25's wave assertion dropped, spillback+starvation asserted instead; the wait-tick-at-spawn
   bug fixed in the preceding commit. ✔ (see B1 for the checklist consequence)
2. Cert episode ends `fullPeriod` with `throughput 217 < par 260`, `win [false×4]`,
   `reason complete`. ✔ (`smoke-replay/results.json`, run 33187823599)
3. `broadcast_core.js` forked with only the `CTF_WIRE`→`SIGNALS_WIRE` rename; the board is drawn
   Nim-side. ✔ (one-line diff against the starter)
4. `chrome_common.js` still reads `window.CTF_WIRE`; `wire_constants.nim:36` aliases it. ✔
5. `global.nim`/`broadcast.nim`/`sim.nim` are starter-idiom, not line ports. ✔ (read; they follow the
   starter's shapes with retargeted fields)
6. 40 car chips + 20 tiny dashes, not 120. ✔ (`global.nim:82-83`, `tests/label_manifest.txt`)
7. `league_replayer.html` not shipped. ✔ (absent from `client/`)
8. `record_fixture.sh` wraps a new `record_fixture.nim`; no committed `.replay`; the GameVersion
   sweep records at test time. ✔ (`tests/fixtures/` holds only `README.md`;
   `tests/test_signals_replay.nim:258-273` records a fresh one and corrupts its version byte to prove
   the codec refuses a mismatch)
9. `tune_baselines --check` emits `::notice` on a different best cell. ✔
   (`tools/tune_baselines.nim:168-175`; the annotation is present in run 33187823599: "this run's
   best cell is switchMargin=0 greenCap=6 (margin 658) against the shipped 2/6 (margin 366)", and the
   step is green)
10. Additions `fork_broadcast_page.py`, `check_broadcast_page.py`, `page_smoke.mjs`,
    `serve_bundle.mjs`. ✔ (all present and wired: `ci.yml:179, 224, 414`)

**Other things I verified and found consistent.** `city.nim` builds 80 links / 352 cells with the
note's cell counts, and the board arithmetic closes at 34×26 exactly. `ownerOf` produces the note's
quadrant table. `PhaseId`/`Movement`/`Approach`/`OrderVerb`/`BlockCause`/`OrderResult` are the note's
enums with the note's index order. `phasePermits` is the note's permitted-movement table and returns
false for `phCLR`. `parsePhase` rejects `CLR` (`directives.nim:76-82`, `SelectablePhases` only).
`delay` is clamped to `0 … turnTicks−2 = 6`. `MaxSayRunes = 120`, `MaxNoteRunes = 240`,
`MaxPromptRunes = 4000`, `MaxPolicyLabelRunes = 64`, `MaxStopDetailRunes = 200`,
`MaxOrdersPerReply = 4`, `MaxRadioLines = 3` — all as the note pins them. `GameVersion = "1"` with the
prepend-only changelog comment; `TargetFps = 24`. `BroadcastEventKinds` is exactly the note's fifteen
and `BeatEventKinds` exactly the five, asserted set-equal in `tests/test_signals_events.nim` together
with the tier-2 sixteen-kind vocabulary and its mandatory trailing summary row. The seed is
randomised in `src/sumo_traffic_signals.nim:76-84` **before** `config.update`, with the compiled-in
`0xA6019` used as the "nobody chose a seed" sentinel and stripped so it cannot clobber the random
one. `Dockerfile` builds both binaries into `/bin/sumo-traffic-signals` and
`/bin/sumo-traffic-signals-player` and copies `data/`, `client/` and `*.json`. `compose.yaml` has one
service whose name yields `{{SUMO_TRAFFIC_SIGNALS_IMAGE}}`. All five docs the manifest points at
exist and are substantive (README 116 lines, RULES 177, SIGNALS 166, PROTOCOL 118, PORTING 81).

---

## Could not determine

- **Whether any of the fixture's 48 `ellipsized` runs is a sentence rather than a name label.**
  `ci.yml:421-425` writes the fixture's report to `fixture-out/viewer-smoke.json`, but the
  `viewer-smoke` artifact upload (`:440-450`) collects only the repo-root `viewer-smoke.png/json`,
  so `ellipsized_samples` for the fixture run is not in the artifacts. The indirect evidence is
  strong (every ellipsis rule in the page is on a name label; the remark path has no clipping
  property at all; `never_inside == 0`), but it is inference. **What would settle it:** add
  `fixture-out/` to the artifact paths and read `canvas_text.ellipsized_samples`.
- **Whether the retry is skipped in practice on a spacing-bound turn (N3).** It needs a hosted
  episode with a real provider that times out on attempt 1; no LLM episode has been run at this sha
  (`llmTurns [0,0,0,0]` in the only recorded results). **What would settle it:** a phase-60 episode
  with `ANTHROPIC_API_KEY` set, then `jq '[.[]|select(.k=="fallback")]' ` over the replay's chat
  records looking for `cause == "timeout"` with `attempt == 2` vs
  `detail == "per-turn budget exhausted before attempt 2"`.
- **The note's "worst case 569 s" wall clock.** My arithmetic from the code gives ≤ ~683 s including
  the last-turn overrun past the 660 s check, which is inside the 720 s pin but not the note's
  figure. Untested — no episode has yet made 32 real LLM turns. **What would settle it:** the phase-60
  episode's wall-clock duration and `results.turnsPlayed`/`finalTick`.
- **Whether item 14's "the `core.zoomAt/setZoom/attachMinimap` wiring" is meant to cover the
  starter's keyboard/wheel/pinch gesture handlers (N23), or only the panel's own controls.** The
  panel's controls are gone; the gestures remain. **What would settle it:** a ruling from the judge
  on the scope of that phrase.
