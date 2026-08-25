# r1 review — factory-commons

Range: `679c933..62681ee` (whole repo at `62681eefc67266f63c852e67c60b25963ba7e18b`, verified with
`git -C /tmp/cogame-factory-commons rev-parse HEAD`)
Files read: 41 (all 17 `src/**.nim`, all 7 `tests/*.nim`, `replay-viewer/{config.nims,factory_commons_replay.nim,static_replay.js,static_replay_worker.js}`, `client/{chrome_common.js,broadcast_core.js,replay_broadcast.html}`, `coworld_manifest_template.json`, `.github/workflows/{ci,coworld-release}.yml`, `tools/ci/{docker_smoke.sh,policies.json,viewer_smoke.mjs,renderer_fixture.html}`, `tools/build_replay_viewer.sh`, `Dockerfile`, `Dockerfile.replay-viewer`, plus the starter's four counterparts under `/workspace/starters/coworld-ctf`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision clause)

Labels used below: **observed** = I read it in the tree or in a cited CI log; **inferred** = I reasoned
from code I read; **untested** = it would take a run to settle.

---

## Blocking

### B1 — No test asserts frame-by-frame reproduction of the recorded per-tick state; the replay carries two independent recordings of integrity/cap and nothing compares them
- Where: `src/factory_commons/sim_state.nim:129-152`, `src/factory_commons/replays.nim:254-379`,
  `tests/test_replay.nim:104-172`, `tests/test_sim.nim:561-574`, `tests/test_broadcast.nim:62-68`
- Observed, architecture: Factory Commons records **state**, not inputs.
  `captureFrame` (`sim_state.nim:129-152`) appends, per tick, both a `Frame`
  (`c/u/b/m`, with `m[0..1] = integrity, cap`) **and** a `series` row `[tick, integrity, cap]`.
  Playback never re-simulates: `hudFromReplay` (`replays.nim:254-379`) reads frame `index` and folds
  the recorded `events[]` up to `frame.t` for the cumulative counters
  (`presses`, `strips`, `banked`, `eaten`, `bananasMade`, `scrappedBy`). The live server
  (`server.nim:106-172`) and the replay build the *same* `HudModel` and go through the *same*
  `buildStateJson` (`broadcast.nim:126-244`), so the viewer is not fed a parallel HUD recording —
  that half of the item holds.
- Observed, tests: what exists is (a) `tests/test_replay.nim:104-113` — `frames.len == ticksPlayed`,
  `series.len == ticksPlayed`, `frame.t == i` for every frame, and structural shape of `c/u/b`;
  (b) `tests/test_replay.nim:148-161` — `hudFromReplay` is built at **four** indices
  (`0`, `len div 3`, `len div 2`, `len-1`) and its `tick`, seat count, band and `integrity <= cap`
  are checked; (c) `tests/test_sim.nim:561-574` — determinism, i.e. two runs of the same order
  script produce an identical `gameHash` and byte-identical event rows.
  What does **not** exist anywhere in `tests/`: a loop over *every* recorded frame comparing the
  replay-derived state to a re-derivation (`grep -n "for index in\|for i, frame" tests/*.nim`
  returns only `test_replay.nim:109` (structural) and the four-index list at `:148`). Nor does any
  test assert that `series.machine[i][1..2]` agrees with `frames[i].m[0..1]`, although both are
  written from the same state in the same call and are read by different parts of the viewer
  (the momentum strip reads `lead`/`series` via `broadcast.nim:206-210`; the gauge reads `fc.integrity`
  which comes from `frames[i].m[0]`).
- Checklist item: 2 — "Replaying the recorded events through the sim reproduces the recorded per-tick
  state **frame by frame**, and the viewer derives its display from that same re-derivation — not from
  a parallel recording. **A test asserts it.**"
- Why blocking: the second clause is satisfied by construction (one `HudModel`, one
  `buildStateJson`), but the final sentence — "a test asserts it" — has no counterpart in the tree.
  A regression in `hudFromReplay`'s event fold (say, `strip` stopping to add `yield` into
  `bananasMade`) would leave every current assertion green, because no test compares a derived frame
  against the sim state that produced it at more than four sample indices, and none compares the two
  recordings of integrity/cap against each other.
- Note in fairness (inferred): the design note explicitly chose state recording over input recording
  (`design.md:719-724`), so the item's literal phrasing "replaying the recorded events through the
  sim" has no direct analogue here; the equivalent assertion would be
  `for i in 0 ..< frames.len: hudFromReplay(i) == the sim state at tick i`. I am reporting the gap,
  not the architecture.

---

## Non-blocking

### N1 — Three sim constants differ from the design note, and one is off the note's repair ladder
- Where: `src/factory_commons/sim_config.nim:12-39` (rationale), `:49` `moveCooldown: 1`,
  `:60` `stripCapLoss: 16`, `:69` `eatTrigger: 6`
- Observed: the note authors `moveCooldown = 2` (`design.md:220`), `stripCapLoss = 12`
  (`design.md:182`) and `eatTrigger = 3` (`design.md:248`). The code ships 1 / 16 / 6 with a 28-line
  comment giving measurements for each. `moveCooldown 2 → 1` is rung 3 of the note's gate-(a) ladder
  and `stripCapLoss 12 → 16` is rung 1 of the gate-(c) ladder (`design.md:397-399`), so both are
  sanctioned by "repair constants in this order and re-run — no design bounce is needed"; the comment
  states rungs 1 and 2 of gate (a) were measured and did not move the binding constraint.
  **`eatTrigger 3 → 6` is not on any ladder** — the note's only `eatTrigger` rung is gate (d)'s
  `3 → 2` (`design.md:400`), i.e. the opposite direction. The comment attributes it to gate (a)'s
  "every seat ≥ 14".
- The manifest agrees with the code (`coworld_manifest_template.json` defaults `moveCooldown 1`,
  `stripCapLoss 16`, `eatTrigger 6`) and `tests/test_manifest.nim:195-238` asserts schema defaults
  equal `defaultGameConfig()`, so nothing drifts between sim and platform.

### N2 — With `stripCapLoss = 16` the plant scraps after **five** overrides, not seven; the note's 13-banana campaign is now ≈15 over five
- Where: `src/factory_commons/machine.nim:210-231`, `src/factory_commons/sim_config.nim:60`,
  `src/factory_commons/sim_types.nim:76-77`
- Observed/inferred: `cap = max(capMin 20, cap − 16)` walks `100 → 84 → 68 → 52 → 36 → 20`; the fifth
  strip crosses `cap < pressFloor 25`, sets `scrappedBy` and emits `scrap` (`machine.nim:225-231`).
  `PrivateYield = [4,3,1]` (`sim_types.nim:77`, rung 1 of the note's gate-(b) ladder, documented at
  `sim_types.nim:70-75`) makes the campaign ≈ 4+4+3+3+1 = 15 private bananas if each lever is pulled
  at the top of its band (exact total depends on where rust has taken integrity between levers).
  The note states "**seven overrides scrap the factory**… total private haul: 13 bananas"
  (`design.md:197-375`). Every prose surface that repeats those numbers is now stale — see N3.
- Also observed: `PrivateYield` now **equals** `PublicYield` element-for-element, so a strip and a
  press pay the same number by band; the asymmetry that remains is who gets it and what it costs
  (1 cube / −16 int / −16 cap / cd 6 vs 2 cubes / −1 int / cd 12).

### N3 — Champion prompts, the player's default prompt and the system prompt's floor plan quote the note's superseded numbers
- Where: `tools/ci/policies.json:6` and `:14` (foreman/custodian `PLAYER_PROMPT`),
  `src/factory_commons_player.nim:21-35` (`DefaultPrompt`), `src/factory_commons/llm.nim:386-409`
  (`FloorPlanText`)
- Observed: the foreman prompt (shipped verbatim from `design.md:585-591`) tells the model
  "three bananas now costs the room **twelve** cap"; the shipped rule is 4 bananas and 16 cap.
  The custodian prompt's "once cap has fallen to **64** or below" names a value the cap walk no
  longer visits (100 → 84 → 68 → 52 …). `FloorPlanText` hardcodes
  "DISTANCES (cells; one cell per tick at **moveCooldown 1**)" and "a one-colour supply loop is about
  **22 ticks**" — correct for the shipped default but *not* derived from `config`, so a variant or
  hosted `game_config` that sets `moveCooldown: 2` would hand the model a floor plan that is wrong by
  2×, while the same prompt's neighbouring line ("may move once every `$c.moveCooldown` ticks",
  `llm.nim:428-429`) is interpolated correctly.

### N4 — The `steward` baseline's harvest rule is not the note's rule 3
- Where: `src/factory_commons/scripted.nim:56-85`
- Observed: the note's steward rule 3 is "`shiftIndex mod 3 == mySlot` and the chute holds ≥ 4
  bananas → eat" (`design.md:614`). The code uses `(shiftIndex + 1) mod SeatCount == seat`
  (`scripted.nim:68`, an offset from the repair rotation at `:44`) **and** adds a fairness clause
  `behind = cogs[seat].eaten + 4 <= max(eaten)` (`:72-73`) that triggers a harvest even with the chute
  below 4. Both are documented in the file (`:56-67`) as what makes gate (a)'s "every seat ≥ 14" hold.
  The order still depends only on the observation and the seat's own slot, so the note's
  "no shared state" property survives (`tests/test_baseline.nim:185-194` asserts statelessness).

### N5 — Gate (b) is skipped on the `either-or` variant; the note asks for all four
- Where: `tests/test_feasibility.nim:110-135` (the `continue` at `:113-122`)
- Observed: the note says the gates run "over seeds 1..12 on **all four variants**"
  (`design.md:379`) and gate (b) is "the stripper's score exceeds each steward's score on ≥ 8/12
  seeds" (`design.md:385-386`). The test skips `either-or` with a written reason (there the lock, not
  the economy, decides whether defection pays; gate (e) covers it). Gates (a), (c), (d) do run on all
  four (`:80`, `:143`, `:174`).

### N6 — `blocked` events collapse consecutive identical rows per seat
- Where: `src/factory_commons/sim_state.nim:24-44`, cleared at `:46-50` and `sim.nim:203-205`
- Observed: `emitBlocked` keys on `action & ":" & why` and drops a repeat, so a cog parked at the
  console through a 12-tick cooldown writes one row, not twelve. The note says an illegal
  press/strip/fix "degrades to `wait` and emits a `blocked` event carrying `why`" with no dedupe
  clause (`design.md:227-228`, `design.md:706`). `lastBlocked` is excluded from `gameHash`
  (`sim_state.nim:162-203` does not mix it), so the dedupe cannot move determinism.

### N7 — A 429 is retried inside the same shift instead of the next one
- Where: `src/factory_commons/llm.nim:624-626` and `:724-757`
- Observed: `textOf` raises on 429; the raising seat is added to `stillOpen` and re-batched by the
  `for attempt in 0 .. 1` loop in the same shift, then falls back. The note says "429 is logged and
  that seat is **retried in the next shift's batch**" (`design.md:645`). Consequence (inferred): a
  throttled episode issues its one retry immediately rather than waiting out the minute; the
  per-episode request ceiling is unchanged because `minTurnSeconds` floors batch *starts*
  (`llm.nim:679-692`, `server.nim:397-401`).

### N8 — `doStrip` clamps integrity down to the new cap; the note's step list does not mention it
- Where: `src/factory_commons/machine.nim:210-213`
- Observed: after `integrity -= stripWear` and `cap = max(capMin, cap − stripCapLoss)` the code adds
  `integrity = min(integrity, cap)`. The note's step 6.4 lists only the two subtractions
  (`design.md:180-185`). The clamp is what keeps the `integrity <= cap` invariant that
  `tests/test_baseline.nim:75` and `tests/test_sim.nim:551` assert; on the note's own walk it is a
  no-op (integrity falls by 16 and cap by 12/16 from equal starts).

### N9 — The certification fixture adds `capMin: 25`, which the note's fixture does not have
- Where: `coworld_manifest_template.json:617`, explained and enforced at
  `tests/test_manifest.nim:340-372`
- Observed: the note's `certification.game_config` is
  `{num_agents, seed, shifts, ticksPerShift, eitherOr, minTurnSeconds, playerConnectTimeoutSeconds,
  players}` (`design.md:1115-1117`). The shipped fixture adds `capMin: 25`, which equals `pressFloor`,
  so `cap < pressFloor` is unreachable and the fixture can never end `factory_ruined`. The test
  states the reason (without it the declared `factory-commons-stripper` seat scraps the plant in
  shift 3 and the replay is 180 ticks = 7.5 s, shorter than `ci.yml`'s 12 s soak) and asserts the
  fixture actually plays ≥ 15 s of video plus at least one press, strip, repair and eat. CI confirms:
  the smoke replay is 479 ticks and the viewer scorebug reads `CAP 25 … OVERRIDES 7`
  (run 32874694256, "Load the bundle in a real browser").

### N10 — `results.fallbacks[i]` counts only LLM-fallback shifts, not shifts a registered scripted seat played
- Where: `src/factory_commons/sim.nim:334-335`, `src/factory_commons/llm.nim:708-721`
- Observed: `applyOrder` increments `fallbacks` only when `order.source == osFallback`; a seat that
  registered `PLAYER_SCRIPTED` gets `osScripted` and reports 0. A prompt seat with no credentials
  gets `osFallback` (`llm.nim:717-720`) and is counted. The note's definition is "shifts that seat
  spent on a scripted order" (`design.md:846`), which reads wider; the code's split is documented at
  `llm.nim:714-720` and is the number phase 60 wants.

### N11 — Scrubber beats are decorated `div`s, and only the first marker of each kind carries a visible label
- Where: `client/chrome_common.js:538-543` and `:551-563` (byte-identical to the starter),
  `client/replay_broadcast.html:3004-3047`, CSS `:1296-1320`
- Observed: `markBeat(tick, kind, team)` is the starter's 3-argument signature and
  `renderBeatMarkers` creates a `div.beat-marker` with `el.__tick`. The game block does not redefine
  it (it is named `buildFactoryBeats`, `:2987`, and `tests/test_broadcast.nim:189` asserts no
  game-block name collides with the chrome alias list). `decorateFactoryBeats` gives every marker
  `role="button"`, `tabindex="0"`, an `aria-label`/`title` naming kind and tick, and a click +
  Enter/Space handler that sends `s:<tick>`; a visible `.beat-lbl` caption is appended only to the
  **first** marker of each kind (`:3028-3038`, with the reason: seven overrides would stack seven
  captions). CSS exists for all five emitted kinds — `shift`, `lock`, `strip`, `scrap`, `gameover`
  (`:1297-1305`) — and `BeatKinds` (`sim_types.nim:296`) plus `beatAt`'s `doAssert`
  (`sim_state.nim:74`) make a sixth kind impossible.

### N12 — The worst-case renderer fixture mirrors the game block rather than importing it, and its canvas draws are pre-clipped so `never_inside` cannot exceed 0
- Where: `tools/ci/renderer_fixture.html:31-36` (the limitation, stated in the file),
  `:202-227` (the canvas draw), `:289-299` (the two signals); CI step `.github/workflows/ci.yml:335-352`
- Observed: the fixture loads the **real** `client/chrome_common.js` and instantiates
  `window.ChromeCommon` (`:135-147`), builds 90-rune `say` and 320-rune `notes` from a multi-byte
  alphabet on all three seats at 360/620/1280 px, asserts the rune counts survive in the DOM
  (`:161-171`, `:265-273`), asserts no box overflows and the notes panel does not escape the frame
  (`:229-262`), and sets `data-replay-loaded`/`data-replay-error` exactly like the shell. Its CSS and
  row builders are **copies** of the appended game block, not the block itself (the block lives in
  the page's IIFE); the file says so. Its canvas control shortens each string until it measures
  inside the canvas before `fillText` (`:218-223`), so `canvas_text.never_inside` is 0 by
  construction there — the meaningful assertions in this fixture are the DOM ones.
- CI evidence (observed, run 32874694256, step "Load the worst-case renderer fixture"):
  `{"loaded":true,"ms":59,…,"feed_lines":9}` and `canvas text: 9 drawn, 0 never inside the canvas
  (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.

### N13 — `canvas_text.total` is 0 on the real bundle replay
- Where: CI run 32874694256, step "Load the bundle in a real browser":
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`
- Observed cause: the board is composited in a Dedicated Worker on an OffscreenCanvas
  (`client/broadcast_core.js:24-46`) and carries **no** `fillText` at all
  (`grep -n "fillText|strokeText|measureText" client/broadcast_core.js` → no matches); every board
  string is a server-rendered sprite (`src/factory_commons/global.nim:124-126`, `:376-377` blit
  pre-rendered `label_{bolt,cotter,ratchet}.png`), and every LLM-authored string (`say`, `notes`) is
  DOM text in the feed rows (`client/replay_broadcast.html:2967-2976`). Per checklist 15 a `total: 0`
  "is not evidence of anything"; N12's fixture is the compensating gate and it does report a non-zero
  total.

### N14 — `ci.yml`'s `NIMBY_VERSION` disagrees with both Dockerfiles
- Where: `.github/workflows/ci.yml:34-35` (`NIMBY_VERSION: "0.1.26"`, under the comment "Pins mirror
  the Dockerfile build stage; bump both together"), `Dockerfile:19` and `:23` (0.1.27),
  `Dockerfile.replay-viewer:11` (0.1.27, sha-pinned)
- Observed: the native test job builds with 0.1.26 and the image with 0.1.27. Both are green at the
  reviewed sha, so this is a documentation/pin drift, not an observed failure. The design note says
  "nimby 0.1.27" (`design.md:1126`).

### N15 — `decideAll`'s transport call sits outside the `try`; a raising transport would propagate
- Where: `src/factory_commons/llm.nim:738-757`
- Observed: `let responses = if client.stub != nil: client.stub(batch) else:
  client.curl.makeRequests(batch, client.timeoutSeconds)` is outside the `try/except CatchableError`
  that wraps `textOf` + `parseOrder` (`:747-756`). Every failure mode `tests/test_llm.nim:228-288`
  drives (timeout, 429, 403, 500, junk, refusal, max_tokens cutoff) is returned *inside* the
  `ResponseBatch`, never raised, so the "never raises" contract (`llm.nim:704`, `design.md:643`) holds
  for all tested paths. Whether `curly.makeRequests` can itself raise is under "Could not determine".

### N16 — Two test-file edits during this run, both after a red CI, both traced
- Where: `git log -p 6d6ba8b..HEAD -- tests/`
- Observed (a): `e9ccce0` changed `tests/test_broadcast.nim:184` from
  `check frame["mt"].getInt() == config.maxTicks()` to `== doc.maxTick()`. Evidence that the old form
  was **failing**, not passing: run 32873190436 (round 3, `test` job red) logs
  `FAIL: and the scheduled tick limit is stated` twice (debug and release). The new form is weaker in
  kind — `hudFromReplay` sets `result.maxTick = doc.maxTick()` (`replays.nim:260`) and
  `buildStateJson` copies it to `mt` (`broadcast.nim:153`), so the assertion now compares a value to
  its own source and can only catch the pass-through breaking.
  Observed (b): the same commit changed the end-to-end episode in `tests/test_replay.nim:46` from
  `[skSteward, skSteward, skStripper]` to `[skSteward, skSteward, skSteward]`. No assertion was
  deleted; the stripper path keeps its own block (`test_replay.nim:236-258`) and
  `tests/test_baseline.nim:149-156` still plays all six seat mixes to the natural end. Everything else
  in the tests' history is an import fix, a rename, or an added assertion
  (`test_manifest.nim:340-372` added five).

### N17 — Worst-case settle time can exceed the 720 s play budget by one shift's batch
- Where: `src/factory_commons/server.nim:287-403`, `:328-341` (the deadline),
  `:343-357` (the check), `:375-401` (batch + pacing), `:233-285` (`finishEpisode`)
- Observed: `gameStart` is taken before the connect wait (`:291-292`), so
  `playDeadline = gameStart + 0.6 × episodeTimeoutSeconds` = 720 s covers connect **and** play; the
  connect loop itself is bounded by `playerConnectTimeoutSeconds` (`:294-301`) and a fully-seated
  room breaks out immediately. The deadline is tested **between shifts** (`:352-357`), so a shift
  that starts one millisecond before the deadline still runs: worst case ≈ 20 s batch + 20 s retry
  batch + ~0.1 s of ticks + ≤ 12 s pacing, then `endEarly()` → `finishEpisode` (0.5 s flush + writes
  + `shutdownGraceSeconds 20`), i.e. **settle at ≈ 773 s** against the item's 720 s and the
  platform's 1200 s (inferred, untested). The design's own arithmetic is "~631 s < 720 s"
  (`design.md:429`) and `tests/test_llm.nim:320-326` asserts `15 × (2 × 20) + 30 = 630 < 720`, using a
  30 s connect allowance rather than the configured 180 s ceiling. Nothing here is unbounded: every
  wait (connect, batch, pacing, grace) has an explicit bound, and the episode always scores and writes.

### N18 — Overflow banana cells are chosen by walkability, not by being unoccupied
- Where: `src/factory_commons/machine.nim:106-146`
- Observed: `overflowCells` collects walkable, non-chute orthogonal neighbours of the chute in
  (row, col) order and `placeBananas` fills each to `cellBananaCap` regardless of whether a cog or a
  loose cube stands there. The note says "overflows onto the **free** floor cells orthogonally
  adjacent to the chute" (`design.md:313`). Bananas outside the chute can never be eaten
  (`sim.nim:158-176` gates on `isChute`), so they rot — which is also what the note describes.

---

## Traced and consistent

**Resolution rules (the ten steps).**
- `src/factory_commons/sim.nim:192-233` — `stepTick` runs exactly the note's ten steps in order:
  dispense (`:19-35`, stall when the mouth holds a cube **or** a cog, no matter destroyed),
  belts (`:37-58`, scanned `countdown(tail-1, BeltX0)` so a train moves as a train and the tail cube
  never moves), kernel intent for **all** seats before any resolution (`:200-205`),
  grasp/drop (`:82-131`), fix (`:209-211`), press/strip (`:213-217`), moves against the live board
  (`:133-156`), auto-eat (`:158-176`), rot (`:178-190`), then rust/cooldowns/record (`:224-232`).
  Every per-seat loop is ascending slot order; belts and dispensers iterate `[cPink, cBlue]`.
- `machine.nim:161-189` (`doPress`) — legality first (`:164-167`), band read **before** wear
  (`:172-174`), consume 1 pink + 1 blue, `integrity -= pressWear`, `cooldown = pressCooldown`,
  `publicYield(band)` bananas onto the chute via `placeBananas` (`:189`). Pinned by
  `tests/test_sim.nim:192-224`.
- `machine.nim:128-149` (`placeBananas`) — fixed west→east chute order from `chuteCells()`
  (`floor.nim:91-93`, `ConsoleX0..ConsoleX1` = 18,19,20 on row 10), each cell to `cellBananaCap`, then
  the overflow ring, then a `spoil` event with the residue. Pinned by `tests/test_sim.nim:452-471`.
- `machine.nim:191-231` (`doStrip`) — one cube (pink when `pink >= blue`), `integrity -= stripWear`,
  `cap = max(capMin, cap − stripCapLoss)` and **never** raised anywhere in the tree
  (`grep` for `machine.cap =` yields only this line and the clamp), `cooldown = stripCooldown`,
  `banked += privateYield(band)` credited straight to the seat and never placed on the floor,
  `strip` event + `strip` beat, and a `scrap` event + beat the moment `cap` crosses below
  `pressFloor` (`:225-231`). Pinned by `tests/test_sim.nim:178-251`.
- `machine.nim:233-255` (`doFix`) — bay cell, cube in hand, `cooldown == 0`, `integrity < cap`;
  consumes the cube, `integrity = min(cap, integrity + repairGain)`, no bananas.
- `machine.nim:13-28` (`bandOf`) — cap read first (`SCRAP`), then the five integrity bands with the
  two floors as the boundaries; `publicYield` is 0 in every band where a press is illegal
  (`:33-40`), so the number and the legality cannot disagree.
- `machine.nim:50-55` + `:66`/`:79` — the `either-or` mode gate; `lockMode` (`:151-159`) fires only
  when `eitherOr` and `mode == mUnset`, on the first *successful* operation, and emits both the
  `lock` event and the `lock` beat. Pinned by `tests/test_sim.nim:494-530` and gate (e)
  (`tests/test_feasibility.nim:203-230`).
- `sim.nim:291-304` (`checkEnd`) — first shift limit → `complete`/`shift_limit`, then
  `cap < pressFloor and bananas.len == 0` → `complete`/`factory_ruined`, then deadline →
  `deadline`/`deadline`; `forfeit` at `:312-315`. Exactly the note's three legal `reason` values, and
  a ruined factory reports `complete`.
- `kernel.nim:154-238` — the five jobs match the note's kernel rules 1–5 including operate 1.1's
  harvest trigger, strip 2.1's degrade-to-operate on SCRAP or a `cycle` lock, maintain 3.1, the
  `eat` job's fallback to a free chute cell, and the move-cooldown gate at `:236-237`.
  One addition beyond the note, documented at `kernel.nim:63-73`: when the planned first step lands on
  another cog, the route is re-planned with the cogs as obstacles, which is what stops two cogs
  meeting head-on from both insisting on the same blocked step for the rest of the episode.

**Decision path.**
- `llm.nim:694-763` — seats registered scripted are answered locally (`:710-714`, `source: scripted`);
  a prompt seat with a disabled client gets the steward order marked `osFallback` (`:715-720`);
  the remaining seats go out in **one** `RequestBatch` (`:727-740`) and the loop
  `for attempt in 0 .. 1` gives **exactly one** retry batch, carrying only the seats that failed
  (`:741-757`) with the note's hint appended (`:731-733`); anything still open lands on the steward
  order with `source = osFallback` and a `factory-commons llm: seat N falling back to scripted order`
  log (`:759-763`). `applyOrder` increments `fallbacks` (`sim.nim:334-335`) and `resultsJson` reports
  it (`sim.nim:378`).
- Simultaneity: `server.nim:376` calls `decideAll` **once** per shift with all seats
  (`:358-359`), on a snapshot taken under the lock (`:360`), outside the lock. There is no per-seat
  loop over the network anywhere. `tests/test_llm.nim:130-150` asserts the batch is one request per
  open seat and `client.lastBatchSize == 3`; `:176-200` asserts one batch plus exactly one retry;
  `:203-226` asserts the retry batch carries only the two failures.
- `llm.nim:579-588` (`extractJsonObject`) takes the first `{` to the last `}`, so fences and prose
  parse (`tests/test_llm.nim:40-54`). `parseOrder` (`:643-677`): missing/unknown `job` → invalid,
  absent `cube` → `any`, unknown `cube` → invalid, extra keys ignored, `strip` always accepted even
  into a SCRAP machine (`tests/test_llm.nim:111-126`).
- `llm.nim:618-641` (`textOf`) — 401/403 sets `client.disabled` for the rest of the episode and the
  retry loop breaks on it (`:725`); `tests/test_llm.nim:273-286` asserts a disabled client issues no
  further requests.
- `llm.nim:110-140` — credential order Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`,
  and with none the client disables itself immediately and logs
  "no LLM credentials; every seat plays the scripted steward". `bedrockModelIds` (`:96-104`) is
  haiku-only with `BEDROCK_MODEL` override; `requestFor` (`:590-612`) sets no `output_config.effort`.

**Waits and their bounds.**
- Connect: `server.nim:294-301`, bounded by `playerConnectTimeoutSeconds`, polls at 200 ms, starts
  with whoever is present; nobody at all → `forfeit` with results *and* replay still written
  (`:310-319`).
- LLM: `client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:740`), the same call shape
  as the bullwhip original (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:457`).
- Round barrier: there is none — the sim advances on this one thread and never blocks on a socket;
  a seat with no socket is switched to the steward for that shift (`server.nim:365-368`).
- Pacing: `sleep(config.turnPacingSleepMs(...))`, bounded by `minTurnSeconds` (`llm.nim:679-692`,
  `tests/test_llm.nim:307-318`).
- Shutdown: `sleep(500)` then `sleep(grace * 1000)` with `grace = shutdownGraceSeconds`
  (`server.nim:273`, `:283`); `/healthz` and `/global` keep answering until `quit(0)`.
- No unbounded loop: `while true` at `server.nim:343` exits on `sim.done` or the deadline; the two
  BFS routines are bounded by the fixed 26×15 grid (`floor.nim:112-235`).

**String truncation on rune boundaries.**
- `llm.nim:60-70` — `cleanText` strips, and if `runeLen > limit` cuts with
  `runeSubStr(0, limit - 1) & "…"`, so the result is exactly `limit` runes and always valid UTF-8.
  `cleanSay` folds `\n`/`\r` to spaces (`:72-75`), `cleanNotes` (`:77-78`), `cleanError` caps at
  `MaxErrorLen = 200` (`:80-81`, `sim_types.nim:66`) and is used on every captured error string
  (`:93`, `:586`, `:619-641`, `:755`, `server.nim:527`). The echoed prompt is cut at
  `MaxPromptLen = 4000` runes with `runeSubStr` in the server's prompt handler
  (`server.nim:513-515`).
- Tests: `tests/test_replay.nim:175-233` builds 90- and 320-rune strings from a palette that includes
  4-byte runes (`:184`), asserts the fixture really is multi-byte (`:191`), cuts one rune over the cap
  and asserts `runeLen <= cap` and `validateUtf8 == -1` (`:193-201`), then plays two shifts feeding
  them to every seat and asserts every recorded `say`/`notes` in the replay bytes is valid UTF-8 and
  inside the cap (`:216-233`). `tests/test_llm.nim:96-109` asserts the same through `parseOrder`.

**The replay writer and the viewer.**
- `replays.nim:101-142` — one strict-UTF-8 JSON document carrying `protocol`, `game`, `gameVersion`,
  `seed`, aliases, `policyNames`, colours, the full `config` block (`:38-88`, every rule constant,
  both yield tables, the whole floor geometry, `numAgents`), `frames`, `series.machine`, `beats`,
  `events`, `results`. `tests/test_replay.nim:82-142` asserts `validateUtf8 == -1`, the < 8 MiB bound,
  the protocol, `frames.len == series.len == ticksPlayed`, every event tick inside range and of a
  declared kind, ≥ 1 of each of `grasp`/`drop`/`press`/`fix`/`eat`, one `shift` per shift, exactly one
  `end`, and the last beat being `gameover`.
- `sim_state.nim:52-60` + `sim.nim:261`/`:286` — the shift close and the terminal event are stamped at
  `boundaryTick = tick - 1` so they land inside `0 ..< frames.len` and `eventsBetween` can deliver
  them to the feed.
- `factory_commons_replay.nim:76-103` — `factory_commons_load_replay` parses, hydrates and renders the
  first packet **directly** (the one carrying the one-shot payloads), never via `packetAt(0)`; the
  export list, `stampStage`, the packet/error/stage accessors and the
  `emscripten_exit_with_live_runtime()` epilogue (`:206-217`) match the starter's structure;
  `ctf_mismatch_tick` is gone, as the note says.
- `frame()` (`:136-172`) — seek is an array index (`frameIndexFor`, `replays.nim:225-229`), events are
  handed to the chrome only on a forward step so a scrub cannot re-fire a banner.

**Chrome provenance (checklist 14).**
- `client/chrome_common.js` is **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js`
  (`diff` empty; md5 `80ea4eb19cee21cb61fb1f009f1f45ab` both sides).
  `tests/test_broadcast.nim:240` asserts it in CI too.
- `client/replay_broadcast.html` (3109 lines vs the starter's 4165) is the starter's page with two
  banner-marked appended blocks — CSS at `:1133-1144` and JS at `:2686-2699`. A line-level
  `SequenceMatcher` of everything above the CSS banner against the starter's first 1451 lines shows
  exactly: one 306-line deletion (starter 528–833 = `#povBadge`, the whole `#fpv` family, section 4b
  `#viewpanel`/`#minimap`/`#zoombar`), one 18-line deletion (starter 1016–1033 = `#mmwarn`), one
  replaced comment line, and one 4-line insertion — the `pointer-events: none` on `#lockerroom` with
  the ecos note (`:1002-1005`). Sections 1–5 (stage, scorebug, banner lane, kill feed, transport),
  the scrubber + momentum + beat markers + lulls + spoilers, the endcard and the locker-room curtain
  are the starter's, unmodified. The markup/JS region shows the matching deletions (the 1124-line
  FPV/POV/minimap/mismatch renderer block, the zoom/pan and view-control wiring, the `#povBadge`
  handler) and the two re-lettered literals. Every inherited id in the note's keep-list is present:
  all seven transport buttons plus `#btn-spoilers`, `#speedchips`, `#ffwd-chip`, `#ffwd-mini`,
  `#win-chip`, `#scrub`, `#momentum`, `#scrub-fill`, `#lulls`, `#scrub-win`, `#scrub-head`,
  `#endcard`, `#status`, `#lockerroom`, `#bannerlane`, `#killfeed`, `#scorebug`, `#plates-l/r`,
  `#clock-time`, `#clock-caption`, `#tick-clock`.
- `#viewpanel` is **removed, not hidden**: no markup, no CSS, no ids; the only surviving
  `core.zoomAt`/`setZoom` references (`:2502`, `:2519`, `:2574`) are the inherited wheel/pinch
  handlers, and the game block's own comment at `:2459` states the panel and its steering are gone.
  `client/broadcast_core.js:16-19` records `attachMinimap`/`drawMinimap` as deliberately inert.
- Transport rules: (a) `relayout()` (`:2634-2679`) measures `#scorebug` and `#transport` and sets
  `--hudscale`, `--topband` and `--band` on `document.documentElement` (`:2648`, `:2669`, `:2674-2675`),
  iterating to a fixed point; `--u` is defined on `:root` (`:40-42`). (b) The two appended overlays are
  appended to `#chrome` (`:2734-2743`), which is `inset: var(--topband) 0 var(--band) 0` (`:112`), and
  both are anchored from the top (`:1216`, `:1263`) — nothing rides in the transport band.
  (c) `#endcard` is `top: var(--topband); bottom: var(--band)` (`:722-723`), shown with
  `#endcard.on` (`:734`, set at `:3080`), and the inherited frame path removes `.on` whenever
  `s.ph !== 'gameover'` (`:1872-1873`) — and `ph` is `gameover` only on the last recorded frame
  (`broadcast.nim:154` with `over = index >= frames.len - 1`, `replays.nim:373`), so any seek off the
  end takes the card down. (d) covered in N11.
- `replay-viewer/config.nims` vs the starter's: identical except the emitted name
  (`factory_commons_replay.js`), the renamed export list and the dropped `_ctf_mismatch_tick`.
  **No `-s MODULARIZE=1`, no `EXPORT_NAME`** — and `replay-viewer/static_replay_worker.js:164` uses
  `Module.onRuntimeInitialized` with `importScripts('./wire_constants.js','./broadcast_core.js',
  './factory_commons_replay.js')` (`:212`). Matched pair, both from coworld-ctf; the lantern
  splice is not present. `static_replay.js` differs from the starter's only by the added
  `data-replay-error` line (`:15-19`), the worker name `'factory-commons-static-replay'` (`:166`),
  and the removed mismatch plumbing; `data-replay-loaded="true"` is still set at `:141`.

**Manifest and packaging (checklist 3, 6, 10, 12).**
- `coworld_manifest_template.json`: `game.replay_viewer.bundle == "static-replay-viewer"`;
  `game.docs` is `{"readme":{"type":"text","value":…},"pages":[{id,title,content:{type:text,value}}]}`
  with `rules.md` and `policies.md`; `game.protocols` carries **both** `player` and `global`, each a
  `{"type":"text","value":…}` object; `$schema`, seven tags, `episode_timeout_minutes: 20`,
  `game.owner`, `game.runnable.type == "game"` with
  `ANTHROPIC_API_KEY_URI = secret://coworld/factory_commons/anthropic_api_key` (namespace equal to
  `game.name` character for character); no top-level `version`, no `game.display_name`, no `tokens` in
  the cert fixture. `config_schema` is closed and every array property carries `minItems`/`maxItems`;
  all 34 defaults equal `defaultGameConfig()`.
- `num_agents: 3` in **all four** variants and in `certification.game_config`; `players` is the three
  aliases in slot order in each; `player[]` has exactly three entries (one prompt, two scripted) and
  each occupies one certification slot. Asserted at `tests/test_manifest.nim:82-106`, `:266-273`.
- `tools/ci/docker_smoke.sh:106-152` enforces all four seat-count invariants plus the `SMOKE_SEATS`
  second declaration, each with a `SEAT-COUNT FAIL:` prefix; both it and
  `tools/build_replay_viewer.sh` are mode 100755. `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three
  workflows, `docker_smoke.sh` and `policies.json` returns nothing, so the phase-12 gate exits 0.
- `.github/workflows/coworld-release.yml` runs Build the Coworld manifest (`:153`) → Certify locally
  (`:167`) → **Upload the policies** (`:206`) → Upload the Coworld (`:304`) → Put the Coworld secret
  (`:342`), in that order. `tools/ci/policies.json` defines four policies: two `PLAYER_PROMPT`
  champions with `USE_BEDROCK: "true"` and two scripted fillers, and champion #2
  (`factory-commons-custodian`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.
- No `/client/replay` pod path exists anywhere (the only hit is the release workflow's own error
  message forbidding it, `coworld-release.yml:201`). `tools/build_replay_viewer.sh:19-23` carries the
  ecos `mkdir -p`-before-`pwd -P` fix and copies from
  `/workspace/factory_commons/replay-viewer/dist/.`.

**Both name spaces (checklist 4).**
- Agents: `observationJson` (`llm.nim:293-382`) and `systemPrompt` (`:411-486`) emit only
  `Aliases[]`; no policy name, player name, model name or seed appears
  (`tests/test_llm.nim:335-357` asserts the negatives). `say` is the only inter-seat channel and other
  seats' `notes` are never included.
- Viewer/platform: `roster[].name` is the alias and `roster[].pol` the policy name
  (`broadcast.nim:91-124`), `results.names` carries policy names and `results.aliases` the aliases
  (`sim.nim:347-368`), and the replay carries both `names[]` and `policyNames[]`
  (`replays.nim:115-119`). Asserted at `tests/test_broadcast.nim:100-118` and
  `tests/test_replay.nim:56-63`.

**Legibility at 360 px (checklist 11).**
- `client/replay_broadcast.html:1155` — `.plate-name, .plate .team-name { flex: 1 1 auto;
  min-width: 3.2em; }`; `:1353-1357` hides `.fc-chip .fc-pol` and `.lives-label` under 640 px, with
  `#stage.tiny` (switched at `boardW <= 620`, `:2670`) doing the same and narrowing the gauge.

**CI (checklist 1, 13).**
- Run **32874694256**, branch `main`, `headSha 62681eefc67266f63c852e67c60b25963ba7e18b`,
  conclusion **success**; jobs `test`, `docker-smoke`, `wasm-viewer` all success.
  `wasm-viewer` has `needs: docker-smoke` (`ci.yml:212`) and its step 11 **"Load the bundle in a real
  browser"** ran with `--strict-text-bounds --soak 12` and reported
  `{"loaded":true,"ms":407,"clock":"SHIFT 5 / 8 TICK 288 OF 479",…}`,
  `soak: 12s of playback kept advancing ("0 / 479" -> "239 / 479" -> "288 / 479")`, and three distinct
  scrub readouts (`0%="SHIFT 5 / 8 TICK 288 OF 479"`, `50%="… TICK 256 …"`, `100%="FINAL SHIFT LIMIT"`).
  Step 12 "Load the worst-case renderer fixture" ran and passed (N12). No step is
  `continue-on-error`.
- `grep -c "SEAT-COUNT FAIL" ` over the full run log: **0**. The smoke log shows
  `game=factory_commons seats=3`, `all 3 player containers exited 0`,
  `smoke OK: seats=3 results=453B replay=98954B reason=complete`.

**Scoring (checklist, design §Scoring).**
- `score(seat) = eaten + banked` (`sim_state.nim:107-108`), integer, higher better;
  `win[i] = (score[i] == max)` with ties marking several winners (`sim.nim:363-371`);
  presses/strips/repairs/misfeeds are reported and not scored. `tests/test_replay.nim:56-80` asserts
  `scores[i] == eaten[i] + banked[i]` and the win rule.

---

## Could not determine

- **Whether `curly.makeRequests` can raise** (relevant to N15). The `curly` package is not present in
  this sandbox (`find / -name curly.nim` → nothing) and no vendored copy is in the repo, so I could
  read only the call site. What would settle it: the `curly` source at the version in `nimby.lock`,
  or a `tests/test_llm.nim` case whose stub raises and asserts `decideAll` still returns three orders.
- **Whether the baseline constants were tuned with a grid harness** (checklist 7, second sentence).
  No sweep script is committed (`grep -rn "harness" tests/ tools/ docs/ scripts/` finds only an
  unrelated comment in `viewer_smoke.mjs:81`). What exists is the 28-line measurement narrative in
  `src/factory_commons/sim_config.nim:12-39` (naming the measured values for `moveCooldown`,
  `stripCapLoss` and `eatTrigger`) and `tests/test_feasibility.nim`, which sweeps 12 seeds × 4
  variants × the gate-relevant seat mixes and fails on the economy. What would settle it: a committed
  sweep/tuning script, or a cited run log showing the grid that produced 1 / 16 / 6.
- **The hosted connect path's real cost** (relevant to N17). The 180 s connect ceiling versus the
  30 s the note and `tests/test_llm.nim:322` assume is a configuration question I can only read, not
  measure. What would settle it: a hosted episode log showing the gap between container start and
  "starting with 3/3 seats connected".
- **Whether the appended feed's DOM text ever clips at 360 px in the real page** rather than in the
  mirrored fixture (N12). The fixture's copies of `.feed-row`/`.fc-chip`/`.notes` are pinned by their
  own assertions, but nothing renders `client/replay_broadcast.html`'s own rules with full-cap strings.
  What would settle it: pointing `viewer_smoke.mjs --strict-text-bounds` at the real bundle with a
  replay whose `order` events carry full-cap `say`/`notes` (CI's replay carries none, by design —
  `docker_smoke.sh` runs with no key).
