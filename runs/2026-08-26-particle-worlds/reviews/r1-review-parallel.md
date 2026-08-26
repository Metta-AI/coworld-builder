# r1 review — particle-worlds

Repo: `/workspace/cogame-particle-worlds` @ `99dcaab7f21dad18f24e6f4fa160135bd01c7102` (main)
Starter: `/workspace/starters/coworld-ctf` (read-only mount, diffed where provenance matters)
Design note: `/workspace/coworld-builder/runs/2026-08-26-particle-worlds/design.md` (1669 lines)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST items 1–15
CI evidence: run `32953267780` (push, main) — `test` ✓ 9m24s, `docker-smoke` ✓ 1m54s, `wasm-viewer` ✓ 2m45s
Files opened: 47 (24 under `src/mpe/`, 12 tests, 3 workflows, 4 `client/`, 4 `replay-viewer/`, manifest, 3 tools) + the full CI log

Findings are numbered F1–F19 and tagged with the checklist category they would fall under, or
`advisory` where no checklist item names them. I do not rank or predict a verdict.

---

## Findings

### F1 — `intHold` steers to the round SPAWN point, not to where the particle was when the order landed — [correctness]

- **Where:** `src/mpe/control.nim:376-380`; the only writer is `src/mpe/field.nim:194-195`.
- **Observed.** `goalFor`'s `intHold` branch reads `(sim.holdX[seat], sim.holdY[seat])`:
  ```nim
  of intHold:
    ## The particle's own position at the tick the order was installed, so a
    ## DRIFTING particle is steered back rather than allowed to coast away.
    if seat >= 0 and seat < 4: (sim.holdX[seat], sim.holdY[seat])
  ```
  `grep -rn "holdX" src/` returns exactly two sites: `field.nim:194` (`sim.holdX[seat] = spot.x`,
  inside `placeParticles`, called once per round from `beginRound`) and the read above. Nothing in
  `server.nim`'s turn-boundary block (`server.nim:1943-1970`) or in `decide.turn` updates
  `holdX`/`holdY` when a directive is installed.
- **What the note says.** design.md:772-774 — "`hold`: the particle's own position **at the tick the
  order was installed** (stored per cog at the turn boundary), so a drifting particle is steered
  back rather than allowed to coast away." The shipped system prompt tells the model the same thing
  in plainer words (`src/mpe/llm.nim:252-253`: "hold = brake and stay where you are").
- **Consequence, traced.** A particle that has moved since spawn and is then ordered `hold` is
  navigated back to its spawn point on the 250 px ring — up to ~1 000 px away — rather than braking
  in place. This is on the live path for `drifter`'s `crypto` Bob before he decodes
  (`baselines.nim:170-171` sets `intHold`) and for any LLM `hold`. `drifter`'s Alice also uses
  `intHold` (`baselines.nim:156`) but is anchored, so she is unaffected.
- **Coverage:** no test exercises `intHold` after displacement. `tests/test_control.nim:90-101`
  tests the ArriveRadius rule with an explicit goal, not `hold`.

### F2 — the wall-clock `deadline` path mutates hashed state outside `sim.step`, so the stop tick's recorded hash is not re-derivable — [correctness] (inferred, untested)

- **Where:** `src/mpe/server.nim:1405-1423`, `src/mpe/server.nim:2044`, `src/mpe/server.nim:2070`;
  hashed fields at `src/mpe/sim_state.nim:161-170` and `:320-333`; comparator at
  `src/mpe/replays.nim` `checkReplayHash`.
- **Observed.** At the top of every loop iteration:
  ```nim
  if squadMode and not deadlineHit and
      (getMonoTime() - episodeStart).inSeconds.int >= config.wallClockBudgetSeconds:
    deadlineHit = true
    sim.endReason = ReasonDeadline
    sim.endRule = EndRuleWallClock
    if sim.phase == Playing:
      sim.bankRound(sim.gameTicksElapsed(), EndRuleWallClock)   # server.nim:1418
    sim.finishGame(Red, isDraw = true)                          # server.nim:1422
    quitAfterFrame = true
  ```
  `bankRound` appends to `sim.roundLog` and increments `roundsPlayed` (`scoring.nim:200-201`), both
  of which are mixed into `gameHash` (`sim_state.nim:320-333`). `finishGame` writes `phase`,
  `winner`, `isDraw` and `gameOverTimer`, all mixed at `sim_state.nim:161-170`.
  Nothing between line 1423 and the step block returns or `continue`s (the only `continue` in that
  span, at 1921, is inside `if shouldReset:`). The step block still runs `sim.step(...)` at
  `server.nim:2044` — now down the `GameOver` branch (`sim.nim:4172-4176`) — and then writes
  `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` at `server.nim:2070`. Exactly one
  hash is therefore recorded for a state that was reached by a server-side mutation.
- **Inference.** At playback the sim reaches that tick with `phase == Playing` and without the extra
  `roundLog` entry, runs the Playing branch instead, and `checkReplayHash` (no tolerance — it
  compares `sim.gameHash()` to the recorded value and sets `hashMismatchTick` on any difference)
  reports a mismatch at the stop tick. I could not run this; it is reasoning over the two paths.
- **What the note says.** design.md:389 makes `deadline`/`wall_clock` a first-class, "declared
  acceptable" end condition, and design.md:1085-1086 says a hash mismatch "is a real integrity
  signal". Checklist item 2 requires frame-by-frame re-derivation.
- **The `fault` path is clean by contrast** (`server.nim:2055-2061`): it sets `phase = GameOver` and
  `break`s **before** `writeHash`, so no unreproducible hash is recorded.
- **Coverage.** `tests/test_endings.nim:71-98` reproduces the identical server sequence
  (`bankRound` then `finishGame` from outside `step`) and asserts the results document, but never
  touches a hash. `tests/test_replay.nim:134-163` asserts every hash re-derives, but only for the
  `complete` 4-round path. **What would settle it:** record an episode with a
  `wallClockBudgetSeconds` short enough to fire mid-round and run the existing
  `parseReplayBytes` + `advanceReplayFrame` loop over it.

### F3 — the worst-case renderer fixture does not load the real renderer; the real viewer's text-bounds gate covered nothing — [legibility / static-viewer]

- **Where:** `tools/ci/renderer_fixture.html` (262 lines, whole file); `.github/workflows/ci.yml:346-364`;
  CI log lines 5778 and 5809.
- **Observed.** The fixture contains no `<script src=...>` and no `<link>`: every string it measures
  is drawn by its own `drawBoard()` (lines 100-235), a hand-written approximation of the board, the
  bubbles, the plates, the radio strip, the crypto panel and the note. Its own banner comment
  (lines 11-12) claims "This page loads the REAL chrome (chrome_common.js and the same DOM ids the
  broadcast page uses)"; it loads neither `client/chrome_common.js` nor `client/broadcast_core.js`
  nor the bundle, and the DOM ids it declares (`#scorebug`, `#killfeed`, `#scrub`, `#clock`, lines
  63-66) are empty containers that nothing populates.
- **What the checklist says.** Item 15: "a page that **loads the real `client/renderer.js`**, hands
  it a frame built to hurt … renders it at several canvas sizes". This starter has no
  `client/renderer.js`; the drawing code that ships is `client/broadcast_core.js` plus the
  wasm-emitted sprite pipeline in `src/mpe/global.nim` (`addSeatSymbolBubbles` at `global.nim:5381`,
  `addSeatLandmarks` at `:5850`). Neither is exercised by the fixture.
- **Everything else item 15 asks for is present and green:**
  - the fixture self-checks its own strings are full length — `renderer_fixture.html:240-247`
    (`if runes !== 160 → data-replay-error`, and each symbol exactly one rune);
  - three widths, 360/620/1280 (`:234-236`);
  - `data-replay-loaded` on the first rAF and `data-replay-error` on failure (`:243-256`);
  - its own `ci.yml` step with `--strict-text-bounds` (`ci.yml:360-364`);
  - CI log 5809: `canvas text: 49 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
- **And the real-viewer gate reported nothing.** CI log 5778, from the `Load the bundle in a real
  browser` step against `dist/smoke/replay.json`:
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
  `total: 0` — the bundle renders in a Dedicated Worker on an OffscreenCanvas
  (`replay-viewer/static_replay.js:194`, `static_replay_worker.js`), which the main-thread
  `CanvasRenderingContext2D.prototype` wrap in `viewer_smoke.mjs:359-362` cannot see. The checklist
  says verbatim: "`total: 0` means the check covered nothing … and is not evidence of anything."
  So the only canvas-text evidence in this run comes from code that does not ship.
- **`tools/ci/viewer_smoke.mjs` is byte-identical to `templates/tools/ci/viewer_smoke.mjs`**
  (`diff` clean), so the harness itself is the verbatim copy the design asks for.

### F4 — no grid harness exists for the baselines — [advisory] (checklist item 7, second half)

- **Where:** absent from `tools/`, `tests/`, `docs/`, and the design note.
- **Observed.** `grep -rin "grid harness|sweep|harness"` over `docs/ tests/ tools/ src/ README.md
  AGENTS.md` returns only unrelated hits ("nav grid", "delete sweep", "the player harness sends
  0x85", "CI is the only harness"). `tools/` contains `build_manifest.py`, `build_replay_viewer.sh`,
  `expand_replay.nim`, `extract_events.nim`, `gen_wire_constants.nim`, `int32_rehearsal.nim`,
  `record_fixture.sh`, `replay_summary.py`, `toolutil.nim`, `wasm_replay_smoke.cjs`, `ci/` — no
  tuning tool. The design note has no tuning section; §Scripted baselines (design.md:798-825) states
  the parameters without a derivation.
- **What exists instead.** One comparative assertion at a single seed:
  `tests/test_control.nim:239-241` — `check drifter.cover >= 80`, `check drifter.bobOnGoal`,
  `check drifter.mean > beeline.mean`, all at `FixtureSeed = 679961`.
- Checklist item 7's first half **is** met: `tests/test_control.nim:180-241` plays an all-scripted
  4 × 1080 episode to the natural end and asserts `played == 4`; `tests/test_endings.nim:50-63`
  asserts `results.reason == "complete"` / `endRule == "full_time"` / `roundsPlayed == 4`;
  `tests/test_replay.nim:316` asserts it again from the replay bytes; and
  `tests/test_control.nim:37-77` asserts 4 000 emitted directives × masks are inside legal bounds
  (`never A`, `never C`, never Up+Down, never Left+Right, target inside the box, symbol one rune
  from the nine-value alphabet).

### F5 — the run's only `tests/` change narrows an assertion, and the float-free grep covers 4 of the note's 8 modules — [correctness]

- **Where:** commit `99dcaab` (`tests: the float-free grep must match whole identifiers`),
  `tests/test_motion.nim:120-147`.
- **Observed (`git log -p -- tests/`).** Three commits touch `tests/` in this run
  (`ff529a1`, `97fac7b`, `99dcaab`); only `99dcaab` modifies an existing test. Its diff replaces
  ```nim
  -          if needle in code:
  -          check needle notin code
  ```
  with a `callsBanned` helper that only matches when the character before the needle is not
  alphanumeric or `_`. No test file was deleted, no `skip`/`xfail` added, no `check` removed
  (`grep -E "^\-.*(check|assert|test \")"` over the whole `tests/` history returns exactly the one
  line above, which is replaced by the equivalent `check not code.callsBanned(needle)`).
  The stated reason is real: `isqrt(` (`scoring.nim:22`) contains the substring `sqrt(`.
  The assertion is nonetheless strictly narrower than before. Checklist item 1 names "a widened
  tolerance" as blocking; I record the change and its rationale and leave the adjudication.
- **Scope, separately.** `test_motion.nim:140` iterates `["field", "motion", "scoring", "beliefs"]`.
  design.md:936-937 specifies the grep over
  `src/mpe/{sim,sim_types,sim_state,field,motion,scoring,beliefs,control}.nim`. The four uncovered
  modules, checked by hand:
  - `control.nim` — **is** float-free (`grep -n "sin(|cos(|tan(|arctan|sqrt(|hypot(|float"` returns
    nothing), despite its own header at `control.nim:12-13` claiming "this module may use ordinary
    floating-point navigation maths";
  - `sim_types.nim:1958-1971` — `aimVector` uses `cos`/`sin` and `bradsOfVector` uses `arctan2`;
  - `sim.nim:656-714, 1124-1138, 1355, 1727-1801` — `diamondSpinAngle`, spray-paint cone,
    gun jitter, all float;
  - `sim_state.nim:617-632` — float event coordinates.
  I traced reachability: `sim.step`'s Playing body (`sim.nim:4188-4210`) calls only `dampAndDrive`,
  `resolveBumps`, `resolveTags`, `scoreTick`, `updateBeliefs`, `checkFieldInvariants`,
  `checkRoundEnd` and two `pruneAgedFx` calls; none reaches those procs. `AimUnitX`/`AimUnitY`
  (`sim_types.nim:541+`) are **integer literals**, not compile-time trig, so the AGENTS.md hazard
  ("a compile-time cos/sin evaluated by whichever libm the build container ships") does not apply.
  `AnimatedDiamonds` is empty on this board (`arena.nim:762` `leftObstacles = @[]` →
  `buildAnimatedDiamonds` returns `@[]`), so `updateAnimatedDiamonds` is the no-op the note claims.
  The wasm gate ran clean: CI log 5825, `ok: loaded replay.json, advanced 300 frames`.

### F6 — the compiled-in `turnSpacingMs` default is the starter's 5 000, not the note's 9 000 — [timeout] (advisory in effect)

- **Where:** `src/mpe/sim_types.nim:516-517` vs `:642`; `src/mpe/sim_config.nim:75`.
- **Observed.**
  ```nim
  DefaultTurnSpacingMs* = 5000  ## wall-clock floor between batch STARTS; holds
                                ## 2 seats under the sidecar's 30 req/min cap.
  ```
  `defaultGameConfig()` uses it (`sim_config.nim:75`). A separate
  `DefaultParticleTurnSpacingMs* = 9000` exists at `sim_types.nim:642` and is what the test fixtures
  use (`tests/fixture.nim:72`).
- **Effect is nil on every shipped path:** all five manifest variants carry
  `"turnSpacingMs": 9000` and `config_schema.turnSpacingMs.default` is `9000`; the cert fixture
  carries `0`. Only a config that omitted the field would fall to 5 000, which for four seats is
  4 × 60 / 5 = **48 req/min**, above the 30/min sidecar cap the design cites (design.md:455-457).
  The stale comment ("holds 2 seats") is the ctf value carried across.

### F7 — the seat's own live score is always `0.000` in a `tag` round — [correctness]

- **Where:** `src/mpe/decide.nim:163-166` and `:195`; `src/mpe/scoring.nim:132-133`;
  contrast `src/mpe/broadcast.nim:1049-1054`.
- **Observed.** `seatViewJson` computes
  ```nim
  soFar = clamp(int(sim.roundAccum[min(max(0, seat), 3)] div elapsed), 0, 1000)
  ```
  and emits it as `"this_round_so_far": soFar.float / 1000.0`. `scoreTick`'s `modeTag` arm is
  `discard` — `tag` scores from the contact counters at round end — so `roundAccum` stays 0 for the
  whole round and every seat reads `0.0` for its live score in all ten `tag` turns.
  The spectator frame handles the same case correctly:
  ```nim
  live.add(%(if sim.mode == modeTag: sim.tagRoundPermille(seat, elapsed)
             else: clamp(int(sim.roundAccum[seat] div elapsed), 0, 1000)))
  ```
- **What the note says.** design.md:567 declares `"score": {"this_round_so_far": 0.58, …}` in the
  per-seat view with no mode exception, and design.md:520 lists "the seat's own banked round scores"
  among what every seat sees. `rounds_banked` and `episode_so_far` are correct; only the in-round
  number is dead in `tag`. `tests/test_observation.nim:169` checks the score block's shape, not its
  value in `tag`.

### F8 — a `tag` pursuer's `shadow` closes to `tagPx div 2` and targets the evader directly, not 60 px from "the particle nearest `target`" — [correctness] (disclosed deviation 2, verified as described)

- **Where:** `src/mpe/control.nim:384-426`, specifically `:394-403` (target selection) and
  `:415-417` (stand-off).
  ```nim
  standoff =
    if sim.isPursuer(seat): max(1, sim.config.tagPx div 2)      # 10 px
    else: max(1, sim.config.shadowStandoffPx)                   # 60 px
  ```
  and, above it, a pursuer's `other` is forced to `sim.seatWithRole(0)` (the evader) rather than
  `nearestOtherParticle(cogIndex, tx, ty)`.
- **What the note says.** design.md:779-781: "`shadow`: the point `shadowStandoffPx` = **60 px**
  from the *other* particle nearest `t`". The **shipped system prompt** says the same to the model
  (`llm.nim:255-256`: "shadow = close to 60 pixels of the particle nearest `target` and stay
  there"), and champion #2's prompt is written against it ("Two `shadow` the evader and one goes to
  the point 300 pixels ahead…"). So a model reasoning from the prompt has a different model of
  `shadow` in `tag` than the controller implements.
- Both deviations are documented in-code with a measured rationale (`control.nim:386-393` and
  `:408-414`) and are pinned by `tests/test_control.nim:158-177`. Reported as observed, exactly as
  disclosed; the prompt/controller mismatch is the part the note does not cover.

### F9 — `baselines.nim`'s pursuer comment contradicts the line under it — [advisory]

- **Where:** `src/mpe/baselines.nim:188-203`.
- **Observed.** The comment reads "A pursuer runs a **PURE PURSUIT**: `go` straight at the evader's
  current position. `shadow` is the wrong intent for a baseline pursuer even though it reads like
  the right one — it parks at `shadowStandoffPx` = 60 px…". Line 201 is
  `result.intent = intShadow`. The behaviour is in fact close pursuit, because F8's controller
  branch overrides the stand-off to 10 px for pursuers — but the comment describes an
  implementation (`intGo`) that is not there, and it asserts `shadow` parks at 60 px, which the
  controller does not do for this role.

### F10 — the shipped system prompt does not name the mode and role in the line the note reserves for them — [advisory]

- **Where:** `src/mpe/llm.nim:222`.
- **Observed.** `THIS ROUND IS NAMED IN THE REPORT BELOW, AND SO IS YOUR ROLE.`
- **What the note says.** design.md:636: `THIS ROUND IS <MODE> AND YOU ARE THE <ROLE>.`, and
  design.md:618-619: "the line naming which mode and role the seat is in is filled per turn".
  The prompt is a `const` with no substitution site. Nothing is hidden from the model —
  `seatViewJson` carries `"mode"` (`decide.nim:171`) and `"you": {"role": …}` (`decide.nim:178`) —
  but the per-turn fill the note specifies is not implemented.

### F11 — the Bedrock candidate ladder has one model, not the note's two — [advisory]

- **Where:** `src/mpe/llm.nim:71-97`.
- **Observed.** `bedrockModelIds()` returns `@["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`
  (a `BEDROCK_MODEL` env pin overrides it). Consequently `tryNextBedrockModel` (`:89-92`) always
  returns `false`, so: a 401/403 carrying "Model access is denied" falls through to
  `client.disabled = true` for the rest of the episode (`:184-186`), and a 429 sets
  `client.throttled = true` (`:189-192`), which `decide.turn:500-507` reads to skip the retry.
- **What the note says.** design.md:428-431: "Bedrock model candidates **in order** … haiku-4-5,
  then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; `tryNextBedrockModel` on 401/403 … and on
  429." The code carries a 10-line rationale (`llm.nim:74-83`) for dropping sonnet-4-5 (133 hosted
  calls, all "Timeout was reached"). This is a deliberate, documented departure from the note's
  §Decisions, not disclosed in the builder's list.

### F12 — `core.zoomAt` / `setZoom` / `panBy` wiring survives the `#viewpanel` removal — [static-viewer] (advisory)

- **Where:** `client/replay_broadcast.html:3889-3896` (ctrl+wheel), `:3901-3913` (Safari gesture),
  `:3960-3970` (two-finger pinch); the decision comment is at `:3997-4002`.
- **Observed.** The ids, markup, CSS, keyboard bindings and `attachMinimap(` call are all gone —
  `tests/test_viewer.nim:42-61` pins the absence of `id="viewpanel"`, `id="zoombar"`, `id="zoom-in"`,
  `id="zoom-out"`, `id="zoom-slider"`, `id="zoom-read"`, `id="minimap"`, `id="minimap-canvas"`,
  `#viewpanel`, `#zoombar`, `#zoom-slider`, `#zoom-read`, `attachMinimap(`, `ZOOM_STEP`,
  `SLIDER_TRAVEL`, over the page with comment lines stripped. The three zoom/pan gesture handlers
  remain live. The page's own comment says "What survives is the touch-action sync and the cursor"
  — it does not mention the surviving `zoomAt`/`setZoom`/`panBy` calls.
- Checklist item 14 names "the `core.zoomAt/setZoom/attachMinimap` wiring" among what a fixed-arena
  game removes. design.md:1207-1212's removal list names only `#viewpanel`, its children and the
  `attachMinimap(...)` call.
- The remaining `minimap` matches in the page (`:676`, `:1348`, `:1917`, `:3152`) are the **FPV PIP's**
  tactical inset (`#fpv-map`), which design.md:1223 explicitly keeps as part of `#fpv`.

### F13 — `client/chrome_common.js` is not byte-identical to the starter's; it carries exactly one changed line — [static-viewer] (disclosed deviation 3, verified as described)

- **Where:** `client/chrome_common.js:72`.
- **Observed (`diff /workspace/starters/coworld-ctf/client/chrome_common.js client/chrome_common.js`):**
  ```
  72c72
  <   var WIRE = window.CTF_WIRE || {};
  ---
  >   var WIRE = window.MPE_WIRE || {};
  ```
  One line, 838 lines total, nothing else. `client/broadcast_core.js` likewise differs in exactly
  one line (`:49`, the same identifier).
- **What the note says.** design.md:59 and design.md:1191 both say `chrome_common.js` is
  "copied **byte-for-byte** from coworld-ctf … Not edited, not reformatted", and reserve the
  one-identifier allowance for `broadcast_core.js` only (design.md:1196-1198). design.md:833 does
  declare a global `CTF_WIRE` → `MPE_WIRE` rename sweep across the fork, and `AGENTS.md` states the
  one-identifier exception for both files. Checklist item 14 admits "a named, minimal patch recorded
  in the design note".
- `tests/test_viewer.nim:180-197` pins the sha256 of the fork's own copies and asserts
  `count("window.MPE_WIRE") == 1` / `"CTF_WIRE" notin chrome`; it cannot diff the starter, which is
  not present in CI. I diffed it here.

### F14 — `/client/replay` remains a game-pod route — [static-viewer] (advisory)

- **Where:** `src/mpe/server.nim:840-853` (serves `EmbeddedBroadcastReplayHtml`, defined at `:73`);
  `docs/PROTOCOL.md:18`; three inlined copies of that table inside
  `coworld_manifest_template.json` (`game.protocols.player`, `game.protocols.global`,
  `game.docs.pages[protocol]`).
- **Observed.** The route is the starter's live/embedded board page for the episode in progress, not
  the platform replay viewer. `game.replay_viewer` is `{"bundle": "static-replay-viewer"}` (verified
  by parsing the manifest), `tools/build_replay_viewer.sh` exists at mode `100755`
  (`git ls-files -s`), `ci.yml`'s `wasm-viewer` job asserts it is `os.X_OK` before invoking it, and
  `coworld-release.yml:167-205` fails certification unless the log carries
  `Replay liveness: skipped (static replay bundle declared`.
- Checklist item 3's literal wording is "No `/client/replay` pod path **anywhere**". The design keeps
  the route on purpose (design.md:957-958 lists it among the "same routes").

### F15 — deleted-mechanics residue survives, unreachable — [advisory] (disclosed deviation 1, verified as described, not worse)

- **Where:** `src/mpe/paint.nim` (11.8 KB), `src/mpe/mapgen_styles.nim` (15.2 KB),
  `src/mpe/map_pool.nim` (395 B) are present; `src/mpe/sim.nim` retains the spray-paint cone
  (`:1124-1138`), the gun jitter (`:1355`), grenade flight (`:1962`), `bouncePlayers`'s siblings and
  the KotH/paint helpers; `client/replay_broadcast.html:3331-3334` still calls chrome_common's
  `markBeat` for `kill`/`steal`/`return`/`capture`.
- **Reachability traced.** `gameHash`'s paint block is gated on `sim.config.floorPaint`
  (`sim_state.nim:259`), which defaults `false` (`sim_config.nim:59`) and is set in no shipped
  variant; `sim.step`'s Playing body never enters any of those procs (F5); the four dead
  `markBeat` kinds cannot be emitted, because `replays.nim`'s beat list for `numAgents > 0` is
  exactly `@["roundstart", "firstword", "onpoint", "tag", "roundover"]` and `tests/test_viewer.nim:157-178`
  asserts that list against the page's CSS in both directions.
- **What the note says.** design.md:841 lists `mapgen_styles.nim`, `map_pool.nim` and the map tools
  as **deleted**; design.md:856-862 says the mechanics are "Deleted, not disabled".
- The tools and assets side of that promise **is** kept: `tools/mapkit.nim`, `tools/map_editor*`,
  `tools/gen_map_pool.nim`, `tools/map_render.nim` and `docs/pool-review.html` are all absent, and
  `data/` (29 entries) contains no `heart_*`, `ped_*`, `paintgun*`, `medkit`, `shield`,
  `paintbomb` or `spraycan*`.

### F16 — three test assertions the note specifies are weaker or absent — [advisory]

- **Where:** `tests/test_replay.nim:181-184`, `:243-275`; `tests/test_engine.nim` (whole file).
- **Observed.**
  - design.md:1556-1558 asks the replay-stream test to assert "**one `directive` per seat per
    turn**"; `test_replay.nim:183` asserts `check counts["directive"] >= 4`.
  - The same note line asks for "one `onpoint`, one `decode`, one `tag`". `test_replay.nim:243-244`
    requires `["roundstart", "word", "firstword", "bump", "decode", "roundover"]` — `onpoint` is not
    in the list, and `tag` is exercised by a direct `resolveTags()` unit block
    (`test_replay.nim:249-275`) rather than from the recorded stream, with the reason stated at
    `:246-248` (a `drifter` pack does not reliably tag a faster evader inside 540 ticks).
  - design.md:1545-1546 asks `test_engine` for "a never-connecting seat is reported to
    `COGAME_PLAYER_FAILURE_URI` and all four rounds still play". No such test exists; the code path
    is `server.nim:1541-1549` (`declarePlayerFailure` on the lowest missing slot, then
    `squadForceStart = true`, then squad construction at `:1648-1665` adds the missing particles as
    trusted bots up to `sim.totalCogs()`), which I traced but which no test drives.

### F17 — `results.bumps` is the last round's bump count, not the episode's — [advisory]

- **Where:** `src/mpe/roster.nim:714`; reset at `src/mpe/field.nim:217`.
- **Observed.** `bumps.add(%sim.bumps[min(seat, 3)])` reads the live per-round counter, which
  `beginRound` zeroes at the start of every round. In the `default` variant round 4 is `tag`, so
  `results.bumps` reports bumps accrued during `tag` — while the only mode where bumps affect the
  score is `spread` (round 1, `scoring.nim:154-159`). Every other seat-indexed stat in the document
  is either an episode aggregate (`scores`, `llmTurns`, `fallbackTurns`) or an explicit per-round
  array (`roundScores`, `roles`).
- **What the note says.** design.md:1013 shows `"bumps": [14, 9, 22, 6]` for a four-round episode
  without stating the scope; design.md:1282-1284 lists "bumps" among the endcard's per-seat columns
  alongside "the per-round permille in four columns". The spectator frame's own `bumps`
  (`broadcast.nim:1093-1096`) is the same per-round counter, so the DOM and the results agree with
  each other.

### F18 — the state JSON carries three keys beyond the note's list — [advisory]

- **Where:** `src/mpe/broadcast.nim:1054` (`livePermille`), `:1058` (`episodePermille`),
  `:1096` (`bumps`).
- **What the note says.** design.md:1128: "Particle-worlds adds **exactly these**", then a block
  that omits all three. `docs/PROTOCOL.md` and its inlined manifest copy document all three, and
  `tests/test_viewer.nim:230-234` asserts their presence, so the shipped docs and the code agree;
  only the design note is behind.

### F19 — the wall-stop test asserts carry-cleared, not velocity-zeroed — [advisory] (disclosed deviation 4, verified as described)

- **Where:** `tests/test_motion.nim:56-75`; the behaviour is `src/mpe/sim.nim:585-628`.
- **Observed.** The test asserts `sim.players[0].carryX == 0`, the x bound, and that the Y axis is
  untouched. It does not assert `velX == 0`. Tracing `applyMomentumAxis`: on a blocked step with no
  slide available it runs `carry = 0; break` (`sim.nim:622-623`) and never writes `velX`/`velY`
  except through `bouncePlayers` (a player-on-player collision, not a wall).
- **What the note says.** design.md:1493-1494: "a particle driven into a wall **stops with zero
  velocity on that axis** and keeps the other." The starter's inherited integrator does not do that,
  and design.md:196-198 elsewhere insists `applyMomentumAxis` is inherited "unchanged" — so the
  note's two statements are in tension and the code follows the second. The test's comment
  (`test_motion.nim:67-70`) says exactly this.

---

## Remaining disclosed deviations — verified, no finding raised

- **(5) `bumps[s]` increments once per seat per tick.** `motion.nim:102-109` credits one tick per
  touching seat, not one per pair, with the reason in the comment. This **matches** design.md:254
  verbatim ("bumps[s] += 1 for each tick in which s is within bumpPx (14 px) of any other agent")
  and is what keeps the sim guard's `bumps[s] <= tickCount` (`sim.nim:4113-4115`) satisfiable.
  Design step 6.2 (design.md:349-351) says "for each unordered pair … `inc bumps[s]` for both
  seats", which the implementation's comment calls out as the contradicting reading; the formula
  wins. Not a deviation from the scoring section.
- **(6) `roundIndex` advances inside `resetToLobby`** — `sim.nim:3906-3910`, guarded on
  `numAgents > 0 and gameStartTick >= 0`, with the reason (it is hashed at `sim_state.nim:295`, so
  the replayed sim must re-derive it) in a 6-line comment. `server.nim:2085-2087` explicitly does
  **not** advance it. This is what makes the round switch re-derivable and it is exercised by
  `test_replay.nim:134-163`, which crosses three round boundaries with zero mismatch.
- **(7) cruise pinned `(996, 1000]` and `(744, 748]`** — `test_motion.nim:39-40` and `:53-54`, with
  the truncation argument in the comment. design.md:1492-1493 says `1000 ± 2` / `748 ± 2`; the
  shipped bound is tighter above and one unit looser below. The closed-form fixed points are exactly
  1000 (`0.75·1000 + 250`) and 748 (`0.75·748 + 187`).
- **(8) extra files** `tools/build_manifest.py`, `tools/int32_rehearsal.nim`, `tools/toolutil.nim`
  are present and each carries a stated purpose; `build_manifest.py --check` is wired at
  `ci.yml:109` and was green.

---

## Traced and consistent

**Resolution rules**

- `src/mpe/sim.nim:4150-4210` — the step body follows design §The game steps 4–6.8 in order:
  `inc tickCount` → `updateAnimatedDiamonds` (a genuine no-op: `arena.nim:762` `leftObstacles = @[]`
  → `AnimatedDiamonds` empty) → roster transitions → `dampAndDrive` → `resolveBumps` →
  `resolveTags` → `scoreTick` → `updateBeliefs` → `checkFieldInvariants` → `checkRoundEnd` →
  FX pruning. `server.nim:2070` writes the hash after the step (step 7).
- `src/mpe/motion.nim:16-50` — damp both axes (`192/256`, `stopThreshold` 8), then impulse, then a
  per-axis clamp; `sim.nim:4066-4068` integrates with the starter's `applyMomentumAxis` Y-then-X.
  Anchored Alice is held at rest with velocity and carry both zeroed (`sim.nim:4054-4059`) and her
  aim still turns (`sim.nim:4043`), matching design.md:216-219.
- `src/mpe/field.nim:71-84` — `particleAccel` 250 / 187 (75 %), `particleMaxSpeed` 1100 / 847 (77 %),
  pursuers only, matching design.md:205-209.
- `src/mpe/scoring.nim:96-133` — all four per-tick terms are the note's equations, integer for
  integer: `spread` shares one `cover` across four seats and accumulates `coverAccum`;
  `deceive` is `clamp(500 ± (gc − vc) div 2, 0, 1000)` with `gc` the min over non-role-0 seats;
  `crypto` is `pairP` for roles 0 and 1 and `clamp(500 + (e_k − bc) div 2)` per Eve with
  `ec = max(e1, e2)`; `tag` scores from counters at round end (`:135-143`).
  `roundPermille` (`:145-161`) floors `spread` at 0 after the capped bump debit and clamps every
  mode into 0..1000; `episodePermille` (`:203-213`) means over `roundLog.len` only, so an unplayed
  round is excluded rather than zeroed (design.md:322-323).
- `src/mpe/field.nim:197-232` — `beginRound` draws mode → roles → landmarks+colours → goal → key →
  spawn rotation in that fixed order, matching design.md:200-232's wire-format claim.
  `roleIndex[s] = (perm[s] + roundIndex) mod 4` at `:203-204` is design.md:122 exactly;
  `episodePerm` (`:94-106`) widens to `int64` before `seed * 2 + 1`, which is the wasm32 overflow
  fix commit `62b3f3c` describes.
- `src/mpe/field.nim:119-151` — the rejection sampler is design.md:164-173 line for line, with the
  spacing relaxed 20 px per 400 attempts and floored at `MinLandmarkSpacingPx = 120`
  (`sim_types.nim:629`), so it always terminates. `drawKey` (`:153-164`) samples 4 without
  replacement from A..H.
- `src/mpe/sim.nim:4070-4132` — `checkFieldInvariants` covers every clause design.md:941-947 lists:
  particles inside the box and off walls, four marks, marks off walls with a valid palette colour
  and ≥ 120 px apart, `roleIndex` a permutation, `roundIndex` in range, `commSymbol` in the
  nine-value alphabet, `bumps[s] <= tickCount`, `tagCredit[s] <= tagTicks`,
  `tagTicks <= tickCount`, four distinct key symbols in `crypto`, and every banked permille in
  0..1000. Each clause is negatively tested at `tests/test_endings.nim:117-155`.
- `src/mpe/sim.nim:4136-4148` — `checkRoundEnd` fires only on `elapsed >= maxTicks`; no mercy, no
  wipe, no early win. `tests/test_endings.nim:179-195` parks every particle on the goal in all four
  modes and proves the round still runs to the tick.
- `src/mpe/beliefs.nim:15-58` — `nearestMark` / `settledTicks` inside `landmarkRadius + 60`,
  `decode` at `SettleTicks = 48`, `onpoint` once per round inside `landmarkRadius + 12`; anchored
  agents are excluded. Matches design.md:358-362.

**Decision path**

- `src/mpe/decide.nim:440-461` — one `RequestBatch` built for all open seats, issued as
  `engine.client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`. One call per seat per turn.
  `tests/test_engine.nim:118-150` proves it against a real mummy fake: exactly four handler windows,
  wall time under 4× the per-call hold, and at least one pair of windows intersecting **inside the
  provider**. No sequential path exists.
- `src/mpe/directives.nim:126-165` — `extractJsonObject` walks for the outermost balanced `{…}`
  with string/escape awareness, then falls back to first-brace..last-brace; fence- and
  prose-tolerant. `parseSquadDirective` (`:229-303`) repairs every field the note's table lists and
  raises only when no cog entry is recoverable. `tests/test_directives.nim` covers all 13 cases the
  note names.
- Retry-once-then-fall-back: `decide.nim:429` (`while open.len > 0 and attempt < 2`) with the second
  batch using `retryMs`; `:509-525` writes the `fallback` record with the cause chosen from
  `{no_credentials, budget_guard, throttled, parse_error}` and installs the `drifter` directive.
  `tests/test_engine.nim:152-197` proves 8 handler calls for a bad reply and **4** for a 429
  (fail-fast, no retry). The fallback is countable: `server.nim:1955-1956` increments
  `sim.fallbackTurns[seat]`, which reaches `results.fallbackTurns` (`roster.nim:716-718`).
- Phase-60 greppable strings are present: `decide.nim:404`, `:524` echo `falling back`, and
  `llm.nim:135` echoes `the LLM provider is unavailable`.
- `decide.nim:314-347` — `repairMissingOrders` is the note's ladder: this turn's, else last turn's,
  else `drifter`'s. `server.nim:1985-1993` adds a fourth floor — a particle with no directive at all
  gets a freshly built `drifter` order — so no particle is ever unactuated.
  `tests/test_engine.nim:280-293` asserts a non-empty directive on every seat for turns 1..5.

**Every wait and its bound**

- LLM batch: `attempt1Ms` 6000, `retryMs` 3000 (`sim_types.nim:514-515`), both validated as whole
  seconds and `attempt1 + retry <= turnBudgetMs` (`sim_config.nim:739-757`,
  `tests/test_engine.nim:219-235`).
- Outer per-turn monotonic deadline: `decide.nim:360, 432-437` — `turnBudgetMs` 10 000, checked
  before each attempt, with a `timeout` fallback record when it has expired.
  `tests/test_engine.nim:199-217` proves it against a 4 s hung provider.
- Rate floor: `decide.nim:419-425` — bounded sleep of at most `turnSpacingMs`, measured from the
  previous batch **start**. Note that `turnStart` is taken before this sleep, so a full 9 s spacing
  sleep consumes most of the 10 s turn budget and the retry is then skipped by the `:432` check;
  worst-case turn wall time is spacing + attempt 1 = ~15 s, and batch starts stay ≥ 9 s apart, so
  the 40-turn arithmetic (design.md:461-471) holds.
- Budget guard: `decide.nim:372-379` — `elapsed + 2 * turnSeconds > wallClockBudgetSeconds` switches
  the LLM off for the remainder and writes a `budget_guard` record.
  `tests/test_engine.nim:255-278` proves zero provider calls after it fires.
- Lobby: `server.nim:1541-1549` — `lobbyJoinTimedOut()` reports the lowest missing slot to
  `COGAME_PLAYER_FAILURE_URI` and force-starts rather than aborting; `lobbyJoinTimeoutTicks` is
  2400 (100 s) in every variant, 1440 in the fixture.
- Engine stop: `server.nim:1405-1423`, 690 s, `wallClockBudgetSeconds.maximum = 720` in
  `config_schema`, and `tests/test_manifest.nim:133-139` asserts every variant is inside
  `episode_timeout_minutes * 60 * 0.6` = 720 s.
- Shutdown grace: `server.nim:2303-2312`, `ShutdownGraceSeconds = 20` (`:184`), a bounded
  `while getMonoTime() < graceUntil: sleep(200)`.
- Player container: `src/particle_worlds_player.nim:27-31` — 240 × 500 ms dial, 6 reconnects,
  10 registration resends, `try/except CatchableError` around the receive loop and `quit(0)` at
  `:147`.
- No unbounded loop found on any of these paths. `decide.nim`'s only `sleep` is the bounded rate
  floor; `directives.nim:352` bounds the note-shrink loop at 12 iterations.

**String truncation**

- `directives.nim:63-70` — `truncateRunes` is the single shortening primitive and uses
  `runeLen`/`runeSubStr`. Callers: `sanitizeNote` → 160 (`:114`), `registerRecord` → 48
  (`decide.nim:246`), `fallbackRecord` → 200 (`decide.nim:232`), `operatorBlock` → 4000
  (`llm.nim:266`), `boundedDirectiveRecord` → 900 by shrinking the **note**, never the serialized
  string (`directives.nim:341-358`), and the provider-body paths in `llm.nim:180, 188, 196, 205`.
- `parseSymbol` (`directives.nim:72-92`) takes the first **rune**, upper-cases it, and gates on
  `A..H`, so a multi-byte symbol field is never sliced mid-codepoint.
- `tests/test_directives.nim:123-149` feeds a 4-byte emoji sitting exactly on the 160-rune cap and
  asserts the result round-trips `%$` → `parseJson` and validates as UTF-8;
  `tests/test_replay.nim:296-324` re-checks the whole path end-to-end through
  `tools/replay_summary.py` with a non-ASCII policy label and note.

**Replay writer**

- `src/mpe/replays.nim:142` — `MpeReplayMagic = "COWLDMPE"`; `tests/test_replay.nim:125-126`
  asserts the magic and the `particle-worlds` game name in the first 64 bytes.
- One `gameHash` per tick at `server.nim:2070`. The hash (`sim_state.nim:289-333`) carries every
  field design.md:926-931 names and excludes `commSymbol`/`commPrev`/`commTurn`
  (`sim_state.nim:337-345` documents the exclusion; `installSymbol` writes nothing hashed).
  `roundAccum` and `coverAccum` are `int64` and are mixed with `cast[uint64]`, so the 32-bit wasm
  build hashes the same bits.
- Self-sufficiency: `roundcard` (`decide.nim:251-281`), `register` (`:235-249`), `directive`
  (`directives.nim:305-339`), `fallback` (`decide.nim:222-233`), `budget_guard` (`:294-295`) and one
  `result` record embedding the whole results document (`:283-292`, written at
  `server.nim:2249`). `tests/test_replay.nim:165-184` counts 4 roundcards, 16 registers and exactly
  1 result; `:350-351` asserts the file is under 1 MB (CI produced 31 394 B for the 4 × 240 fixture).
- `tools/replay_summary.py:80` emits `protocol = "particle-worlds/v1"`; Python 3 stdlib only.

**Viewer re-derivation**

- `replay-viewer/mpe_replay.nim` imports the same `src/mpe` modules;
  `tests/test_replay.nim:134-163` re-parses the written bytes, runs `initReplayRuntime` +
  `advanceReplayFrame` to the last recorded tick and asserts `hashMismatchTick == -1` across all
  four rounds — the landmark draw, the colour permutation, the role cycle and the key are all
  re-derived, not read from records.
- Native ↔ wasm gate: `ci.yml:366-376` runs `tools/wasm_replay_smoke.cjs` on the emitted module
  against the docker-smoke replay; CI log 5825:
  `ok: loaded replay.json, advanced 300 frames (6600261 packet bytes, heap 148 MB)`.
- Emscripten flags and bootstrap are the **same** starter's, verified by diff against
  `/workspace/starters/coworld-ctf/replay-viewer/`: `config.nims` differs only in the `ctf_`→`mpe_`
  export names and the output filename; it is **non-`MODULARIZE`** (no `MODULARIZE`, no
  `EXPORT_NAME`) and `static_replay_worker.js` sets `Module.onRuntimeInitialized` — the matched
  pair. `tests/test_viewer.nim:239-256` pins both halves. `static_replay.js` differs in 2 lines
  (worker name, `window.MpeStaticReplay`), `static_replay_worker.js` in 14 (all `_ctf_*` → `_mpe_*`).
- Load signals: CI log 5778 — `{"loaded":true,"ms":2089,"clock":"0:00 TIME LEFT ROUND 2/4 · DECEIVE · TURN 1/2",...}`
  plus `soak: 12s of playback kept advancing ("0 / 1035" -> "236 / 1035" -> "284 / 1035")`. The
  `wasm-viewer` job carries `needs: docker-smoke` (`ci.yml:224`), the smoke step is present and not
  `continue-on-error`, and it loads the replay `docker-smoke` uploaded.

**Manifest**

- Parsed with `json.load`: `game.replay_viewer == {"bundle": "static-replay-viewer"}`;
  `episode_timeout_minutes == 20`; `game.protocols` has both `player` and `global`, each a
  `{"type":"text","value":…}` **object**; `game.docs.readme` is text (7 207 chars) and
  `game.docs.pages` is three `{id,title,content:{type,value}}` entries (rules 12 036, protocol
  12 545, commanding 6 595 chars) — checklist item 10 satisfied.
- `game.results_schema` has exactly **22** properties matching `particleResultsJson`'s 22 keys
  (`roster.nim:738-761`), `additionalProperties: false`,
  `required: ["names","scores","win","reason","endRule","roundsPlayed"]`.
  `tests/test_manifest.nim:48-99` asserts key equality in both directions.
- `game.runnable.env.ANTHROPIC_API_KEY_URI == "secret://coworld/particle-worlds/anthropic_api_key"`.
- **`num_agents` = 4 in all five variants** (`default`, `coop`, `deception`, `comms`, `chase`) **and
  in `certification.game_config`**; `len(certification.players) == 4` and
  `len(certification.game_config.players) == 4`. `tests/test_manifest.nim:23-47` and `:230-250`
  assert it and that every variant's `game_config` constructs a valid sim.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`, `coworld-release.yml`,
  `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` returns **nothing** (exit 1) — item 12's
  gate exits 0.
- `tools/ci/policies.json`: four policies, all `"run": "/bin/particle-worlds-player"`; two
  `PLAYER_PROMPT` champions (`particle-worlds-swarm`, `particle-worlds-cipher`) and two
  `PLAYER_SCRIPTED` fillers; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.
- `coworld-release.yml` step order: Build the Coworld manifest (167) → Certify locally (167) →
  Upload the policies (206) → Upload the Coworld (304) → Put the Coworld secret (342). All three
  workflows present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` both mode
  `100755`.

**`num_agents` / docker-smoke**

- `grep -ci "SEAT-COUNT FAIL" /tmp/ci.log` → **0**. The docker-smoke log carries
  `game=particle-worlds seats=4 config={… "num_agents": 4, …}` and
  `smoke OK: seats=4 results=878B replay=31394B reason=complete`, with
  `SMOKE_REQUIRE_REPLAY_JSON: "0"` (`ci.yml:196`).

**Both name spaces**

- `roster.nim:693-694` builds `alias` from `teamText` + `IdentityNames[slotIdentityIndex(seat)]`
  (`cogAlias` untouched); real names go only to `results.names` (`:687-691`), `roster[].name` and
  the replay config JSON. `tests/test_identity_privacy.nim` asserts both sides with a sentinel
  address across the seat view, both LLM messages, the `directive` record, the `register` record,
  the symbol bubble label and the spectator frame.

**Legibility at 360 px**

- `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`
  is present and pinned field-by-field at `tests/test_viewer.nim:89-99`;
  `classList.toggle('tiny', boardW <= 620)` and the `Math.max(0.5, Math.min(1.6, boardW / 760))`
  hudscale clamp at `:63-71`; `#endcard { bottom: var(--band, 0px) }` and
  `$('endcard').classList.remove('on')` at `:73-76`; no `mpe-` overlay declares a `bottom:`
  (`:78-87`). `relayout()` sets `--hudscale`/`--topband`/`--band` on `root`
  (`replay_broadcast.html:4092-4097`, `root = document.documentElement`).
- Beats are labelled `<button>`s that seek: `mpeBeat` at `replay_broadcast.html:4404`,
  `document.createElement('button')`, `el.setAttribute('aria-label', label)`, `CTX.send('s:' + tick)`,
  all pinned at `tests/test_viewer.nim:174-178`. CSS exists for exactly the five emitted kinds
  (`:4336-4360`) and for none of the eight dead ones.

**Tests, and CI**

- All 14 test files ran (CI log line 289), in **both debug and release** except
  `tests/test_perf.nim`, which `NIM_TESTS_RELEASE_ONLY` restricts to release (log lines 291, 1725) —
  exactly as design.md:1455 specifies.
- `python3 tools/build_manifest.py --check` ran green (`ci.yml:109`), so the manifest is not
  hand-edited.

---

## Could not determine

- **F2's replay divergence on the `deadline` path.** I reasoned it out of the two code paths but
  could not execute anything (no Nim, Docker or emsdk in this sandbox). What would settle it: an
  episode recorded with `wallClockBudgetSeconds` short enough to stop mid-round, then run through
  the existing `parseReplayBytes` + `advanceReplayFrame` loop from `test_replay.nim:134`, asserting
  `hashMismatchTick == -1`.
- **Whether a live LLM episode stays inside 60 % of `episodeTimeoutSeconds`.** Every wait is bounded
  and the arithmetic checks out on paper (40 turns × max(9 s spacing, 6 + 3 s calls) = 360–400 s,
  plus lobby ≤ 100 s, play ≤ 60 s, artifacts ~25 s ⇒ ≤ 585 s against the 690 s stop), but no CI job
  runs with an `ANTHROPIC_API_KEY`, so the only measured episode is the 4 × 240-tick offline
  fixture that finished in 1m54s. Settled only by a phase-60 hosted run.
- **Whether the shipped symbol bubbles and crypto panel stay inside the frame.** The bundle draws in
  a Worker/OffscreenCanvas, so `viewer_smoke.mjs` reported `canvas_text: total 0` on the real
  replay (F3), and the fixture that reported 49 draws does not run the shipping renderer. Settled by
  a fixture that imports `client/broadcast_core.js` and feeds it a real state frame, or by a
  `viewer_smoke.mjs` that instruments `OffscreenCanvasRenderingContext2D` inside the worker.
- **Whether `results.bumps` (F17) is intended as per-round or per-episode.** design.md:1013 and
  :1282 do not say. Settled by a line in the note or a per-round `bumps` array.
