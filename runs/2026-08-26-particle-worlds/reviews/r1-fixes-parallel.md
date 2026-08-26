# r1 fixes (PARALLEL / SUPERSEDED SESSION) — particle-worlds

Branch: `refs/heads/fixer-r1-work` @ `ae77c87dcc29af53ef9ca1b613be56cdc1ce59ec`
(Metta-AI/cogame-particle-worlds), 15 commits based on the reviewed sha
`99dcaab7f21dad18f24e6f4fa160135bd01c7102`.
Source review: `reviews/r1-review-parallel.md` (F1–F19).
`main` was **not** touched and no CI run was triggered for the branch.
CI: none. The whole test suite was run locally instead — all 14 `tests/*.nim` files pass in debug
(`nim r --hints:off --path:src`), with `test_viewer`, `test_motion`, `test_control` and
`test_replay` also re-run under `-d:release`; `src/particle_worlds.nim`,
`src/particle_worlds_player.nim` and `replay-viewer/mpe_replay.nim` all compile;
`python3 tools/build_manifest.py --check` is clean.

---

## READ THIS FIRST — what the canonical chain does not contain

This session was superseded: the owning session's fix chain `99dcaab..b6b4401` is canonical and its
judge is running against `b6b4401`. Everything below lives on the branch above, for cherry-picking.
Three items are worth the owning session's attention because **nothing in `b6b4401`'s twelve commits
touches them** (`git diff 99dcaab b6b4401 | grep -c "holdX\|deadlineHit\|recordHoldAnchor"` → `0`):

1. **F1 — `intHold` steers to the round SPAWN point.** `[correctness]`. `goalFor`'s `intHold` branch
   read `sim.holdX/holdY`, whose only writer was `placeParticles`: a particle ordered to `hold`
   after it had moved was navigated back to its spawn point on the 250 px ring — up to ~1 000 px —
   instead of braking in place. Live for `drifter`'s crypto Bob before he decodes and for any LLM
   `hold`. Fixed by `control.recordHoldAnchor`, called from the server's turn boundary as the note
   specifies ("the particle's own position at the tick the order was installed, stored per cog at
   the turn boundary"); `holdX/holdY` are not in `gameHash`, so the write cannot move the hash
   chain. New test in `tests/test_control.nim`. Branch commit `7a2c963`.
2. **F2 — the wall-clock `deadline` path records an unreproducible hash.** `[correctness]`, reported
   in the review as "inferred, untested". It is real and now **demonstrated**: the stop ran
   `bankRound` + `finishGame` (roundLog, roundsPlayed, phase, winner, isDraw, gameOverTimer — all
   hashed) at the top of the serve iteration and the step block then still wrote
   `writeHash(tick, gameHash())` for that tick. Fixed by moving the bank and the finish to a
   "wall-clock settle" block that runs *after* the frame's step has written the tick's hash and
   before the loop exits on `quitAfterFrame` — the same discipline the `fault` path already used.
   `tests/test_replay.nim` records a real mid-round deadline episode and asserts every hash
   re-derives (`hashMismatchTick == -1`), **plus a control that reproduces the old ordering and
   asserts it is caught**: it mismatches at tick 202, the stop tick. Branch commit `7374fb5`.
3. **F4 — the grid harness.** Checklist item 7's second half had nothing behind it in either chain
   as far as this session can see. `tools/tune_baselines.nim` sweeps the two continuous, role-owned
   drifter knobs against the score of the role that uses each, three seeds, four-round role cycle:
   `shadowStandoffPx` 20→403, 40→400, **60 (shipped)→399**, 80→394, 100→389, 140→379 (crypto
   eavesdropper mean, permille); `evadeProbePx` 80→988, 140→978, **200 (shipped)→1000, the grid
   optimum**, 260→974, 320→778, 400→639 (tag evader mean). `--check` fails when a shipped value is
   more than 10 permille off the best cell; wired into `ci.yml`'s `test` job (~15 s in release) with
   the table written to the step summary and kept as the `baseline-sweep` artifact. Branch commit
   `ea27c7b`.

One more thing the owning session may want regardless of whose fixture it keeps: this session's
fixture found a **real 360 px legibility defect in the shipped chrome**. `.feed-row` is the
starter's kill-feed row (`white-space: nowrap; max-width: none`, "bounded by the small font + the
pre-bounded 10-char name, so it can't run away"), and particle-worlds puts a 160-rune LLM `note` in
it. `#killfeed` is right-anchored and its rows grow **leftward**, so every full-cap remark laid out
past the left edge of the frame and was invisible — at 1280 px the note line's box started at
x = −21 and the row's `:` glyph at x = −40. No CI replay can catch it (a scripted seat emits no
note). The branch fixes it by letting the rows wrap inside the feed's own column
(`client/replay_broadcast.html`, in the appended game block: `.feed-row { white-space: normal;
max-width: 100% }`, `.feed-row .badge { overflow-wrap: anywhere }`), after which the fixture reports
`canvas text: 1098 drawn, 0 never inside the canvas (1 draw crossed an edge), 54 ellipsized` —
the 54 are nameplates and the starter's own `Filling hoppers with fresh paint…` curtain line, no
remark. Branch commit `aca0169`.

**`results.bumps` — not arbitrated here.** Two positions exist and the owning session decides:
- `b6b4401`'s `6eccd8b` ("F9: say what results.bumps counts") **documents** it as the last round's
  count and argues an episode total "would need a second, hashed accumulator — a gameHash change and
  therefore a GameVersion bump".
- This branch's `e4f3350` (F17) **implements** the episode total with an **unhashed** accumulator:
  `SimServer.episodeBumps`, appended at the end of the type (keyframes are flatty-positional),
  written only by `bankRound`, which runs inside `sim.step` — so the replayed sim re-derives the same
  value, `gameHash` is unchanged and no GameVersion bump is needed. It also moves the endcard's bump
  column onto the same number and states both meanings in `docs/PROTOCOL.md` (manifest regenerated).
  If the per-round semantics are the ruling, drop `e4f3350`; if the episode total is, `6eccd8b`
  needs replacing.

---

## Findings → commits

| finding | disposition | branch commit | files |
|---|---|---|---|
| F1 `intHold` steers to the spawn point | fixed | `7a2c963` | `src/mpe/control.nim:363`, `src/mpe/server.nim:1948`, `tests/test_control.nim:180` |
| F2 deadline path's hash not re-derivable | fixed | `7374fb5` | `src/mpe/server.nim:1409,2103`, `tests/test_replay.nim:116,368` |
| F3 fixture does not load the real renderer | fixed | `aca0169` | `tools/ci/renderer_fixture.html`, `tools/fixture_frame.nim`, `tools/gen_fixture_frame.nim`, `tools/ci/renderer_fixture_frame.json`, `.github/workflows/ci.yml:339`, `client/replay_broadcast.html:4243`, `tests/test_viewer.nim:239` |
| F4 no grid harness for the baselines | fixed | `ea27c7b` | `tools/tune_baselines.nim`, `.github/workflows/ci.yml:150`, `tests/test_control.nim:210` |
| F5 float-free grep covers 4 of 8 modules | fixed | `613120f` | `tests/test_motion.nim:120` |
| F6 stale `turnSpacingMs` default (5 000) | fixed | `1f323f5` | `src/mpe/sim_types.nim:516`, `src/mpe/sim_config.nim:75` |
| F7 live score always 0.000 in `tag` | fixed | `9a7af98` | `src/mpe/decide.nim:163`, `tests/test_observation.nim:182` |
| F8 prompt's 60 px stand-off vs the controller | fixed | `402293c` | `src/mpe/llm.nim:255`, `tests/test_engine.nim:112` |
| F9 stale pursuer comment in `baselines.nim` | fixed | `81ed1a7` | `src/mpe/baselines.nim:189` |
| F10 prompt does not name the mode/role | fixed | `5e44d31` | `src/mpe/llm.nim:222,262`, `src/mpe/decide.nim:455`, `tests/test_engine.nim:123` |
| F11 one Bedrock candidate, not two | **won't fix** | — | `src/mpe/llm.nim:71-97` |
| F12 `zoomAt`/`setZoom`/`panBy` wiring survives | fixed | `a919dd2` | `client/replay_broadcast.html:3853`, `tests/test_viewer.nim:56` |
| F13 `chrome_common.js` one changed line | **won't fix** | — | `client/chrome_common.js:72` |
| F14 `/client/replay` pod route | fixed | `74bd5bb` | `src/mpe/server.nim:73,800`, `docs/PROTOCOL.md:18`, `coworld_manifest_template.json`, `tests/test_manifest.nim:132` |
| F15 deleted-mechanics residue | partial | `ae77c87` | `src/mpe/mapgen_styles.nim` (deleted) |
| F16 three note-specified assertions weaker/absent | fixed | `35ccf6c` | `tests/test_replay.nim:281,371`, `tests/test_engine.nim:300`, `src/mpe/server.nim:1155` |
| F17 `results.bumps` is the last round's | fixed (contested) | `e4f3350` | `src/mpe/sim_types.nim:1934`, `src/mpe/scoring.nim:196`, `src/mpe/roster.nim:714`, `src/mpe/broadcast.nim:1245`, `docs/PROTOCOL.md`, `tests/test_endings.nim:66` |
| F18 state JSON carries three extra keys | **won't fix** | — | `src/mpe/broadcast.nim:1054,1058,1096` |
| F19 wall-stop test asserts carry, not velocity | **won't fix** | — | `tests/test_motion.nim:56` |

Line numbers are post-fix.

---

## Per finding

### F1 — `intHold` steers to the round spawn point — `7a2c963`
`goalFor`'s `intHold` branch returned `(sim.holdX[seat], sim.holdY[seat])`, and `grep -rn holdX
src/` had exactly two sites: the read, and `placeParticles` writing the spawn point once per round.
Now `control.recordHoldAnchor(sim, cogIndex)` records the particle's live centre and the server
calls it in the existing `for order in directive.orders` block at the turn boundary, next to
`installSymbol`. Nothing hashed changes (`sim_state.gameHash` mixes no control state), so the
recorded mask log and the viewer's re-derivation are untouched. Evidence: new test
`hold brakes where the order landed, not at the round spawn point` — displaces a crypto listener
420×160 px from spawn, anchors it, asserts `goalFor == the displaced position`, asserts no d-pad bit
is pressed (it really brakes), then drifts it 200 px further and asserts it is steered back to the
anchor rather than to the spawn ring. Satisfies checklist item 7's "every order inside its legal
bounds" only incidentally; it is a correctness fix against design.md:772-774.

### F2 — the wall-clock stop's hash — `7374fb5`
Detection stays at the top of the iteration (it still sets the unhashed `endReason`/`endRule`, the
echo and `quitAfterFrame`); the bank and the finish move into a documented "wall-clock settle"
block after `prevInputs = lastStepInputs`, i.e. after the frame's `sim.step` + `writeHash`. Evidence:
`tests/test_replay.nim`'s `recordDeadlineEpisode` plays a real episode through the replay writer and
stops it mid-round both ways round. The shipped ordering re-derives every hash
(`replayMismatchTick == -1`) and reports `reason == deadline`, `endRule == wall_clock`,
`roundsPlayed == 1`; the pre-fix ordering is caught — the test prints
`Replay hash mismatch at tick 202; expected 1385645226157481520, got 13154929015269700104` and
asserts `>= 0`. Satisfies checklist item 2 (frame-by-frame re-derivation, asserted by a test) on the
`deadline` path, which previously had no hash coverage at all.

### F3 — the worst-case renderer fixture — `aca0169`
Three changes, one commit:
1. **It loads the shipped renderer.** The fixture fetches `./index.html` — the bundle's own copy of
   `client/replay_broadcast.html`, spliced with `client/chrome_common.js` and `wire_constants.js` by
   `Dockerfile.replay-viewer` — and boots it in three iframes at 360 / 620 / 1280 px. The only
   substitution is the wasm shell: a stub `window.MpeStaticReplay` captures the page's own
   `coreConfig.onText` (the same entry point the Worker feeds) and reports the fitted transform.
   Every string measured is laid out by `renderScorebug` / `renderClock` / `renderTransport` / the
   feed / `window.MpeChrome`.
2. **The frame is the server's.** `tools/fixture_frame.nim` builds it with
   `broadcast.buildStateJson` over a real four-round episode; `tools/gen_fixture_frame.nim` writes
   `tools/ci/renderer_fixture_frame.json`; `tests/test_viewer.nim` regenerates it and fails on
   drift. It carries a full-cap 160-rune note on every seat, a non-silent symbol on all four
   particles, the crypto panel with three belief rows, the full mark rail, one feed row of every
   kind the sim emits, and the endcard with four cards. `ci.yml` copies both files next to the
   bundle.
3. **The measurement.** `viewer_smoke.mjs` instruments `CanvasRenderingContext2D` and this chrome is
   DOM, so after the real chrome lays a frame out every rendered LINE is mirrored onto a top-frame
   canvas at the exact rect the browser used, in the same font, clamped where the browser clips.
   `--strict-text-bounds` then gates the real layout. Sequence per width: the frame with every event
   (four remarks settle as the feed's four rows), a settle frame, the wire (events with no
   directives behind them), then the endcard — measured after each.
Evidence: local `node tools/ci/viewer_smoke.mjs --url … --strict-text-bounds` →
`canvas text: 1098 drawn, 0 never inside the canvas (1 draws crossed an edge), 54 ellipsized`, and
`data-replay-loaded="true"`. Satisfies checklist item 15. It also caught the `.feed-row` overflow
described in the header, which is fixed in the same commit.

### F4 — the grid harness — `ea27c7b`
See the header for the sweep tables. Satisfies checklist item 7's second half. The two knobs that
are compile-time constants rather than config — a pursuer's `tagPx div 2` stand-off and
`control.ArriveRadius` — are named in the harness as out of the grid, with their measurements at
their definitions.

### F5 — the float-free grep — `613120f`
`control.nim` is float-free end to end and joins the line-by-line list (now five modules). The three
residue-bearing modules the note names (`sim`, `sim_types`, `sim_state`) are covered by
**reachability** instead of by omission: the test parses the routines of all eight modules, walks the
call graph from `sim.step` counting every identifier that names a routine in those modules as a call
(an over-approximation, which is the strict direction), and fails on any libm call or float on the
reachable path. 102 routines are reachable; exactly one carries a float —
`sim_state.resetFlag`'s `float(sim.flags[team].x)`, an exact int→float conversion building the
coordinates of an unhashed FX event — and that exception is named **and** asserted to still be
reachable and still float-bearing, so it cannot rot into a hole. Verified discriminating: inserting
`sqrt(2.0)` into `sim.checkRoundEnd` makes the test print
`REACHABLE FLOAT: sim.nim checkRoundEnd -> let probe = sqrt(2.0)` and fail. The narrowing the review
flagged (`callsBanned` whole-identifier matching, needed because `isqrt(` contains `sqrt(`) is kept
and is strictly necessary; no assertion was removed.

### F6 — `turnSpacingMs` default — `1f323f5`
`defaultGameConfig()` now uses `DefaultParticleTurnSpacingMs` (9 000, whose comment states the
four-seat arithmetic); the starter's `DefaultTurnSpacingMs = 5000` and its stale "holds 2 seats"
comment are deleted rather than left to be picked up again. No shipped path changed (every variant
and the schema already carried 9 000).

### F7 — the live score in `tag` — `9a7af98`
`seatViewJson` now uses `tagRoundPermille` in `tag` and the accumulator elsewhere, the same rule
`broadcast.buildStateJson` already used. New test drives a real contact and asserts both the
pursuer's and the evader's live number against `tagRoundPermille`, and that `roundAccum` really is 0.

### F8 — the prompt's stand-off — `402293c`
The intents line now reads "shadow = close to 60 pixels of the particle nearest `target` and stay
there, EXCEPT in TAG, where a pursuer always shadows the EVADER whatever `target` says and closes to
inside the 20-pixel tag radius rather than standing off". `docs/RULES.md` already documented the
exception; only the prompt was stale. `tests/test_engine.nim` pins the prompt text next to
`test_control`'s pin on the behaviour.

### F9 — the pursuer comment — `81ed1a7`
Comment only: it now describes the close pursuit the baseline actually runs and names the controller
exception that makes `intShadow` the right intent there.

### F10 — the per-turn mode/role line — `5e44d31`
The const carries design.md:636's line verbatim (`THIS ROUND IS <MODE> AND YOU ARE THE <ROLE>.`) and
`llm.systemPromptFor(mode, role)` fills it per seat per turn at the `requestFor` call site. The test
asserts the filled line for every mode and role and that no unfilled placeholder can reach a
provider.

### F11 — the Bedrock candidate ladder — **won't fix**
The note asks for haiku-4-5 then `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. The code ships one
candidate with a 10-line measured rationale at `llm.nim:74-83`: 133 hosted calls to sonnet-4-5, all
"Timeout was reached". Restoring it would mean that on a 403 or a 429 the ladder switches to a model
this game has measured as answering nothing, i.e. it trades a fallback that works (the scripted
layer, microseconds) for one that burns the turn budget. The finding is advisory (no checklist item
names it) and the departure is documented in-code; what is genuinely missing is the *disclosure*,
which belongs in the design note — and this session is not permitted to edit it. Recommend the
owning session either records the departure in §Decisions or re-adds the candidate deliberately.

### F13 — `chrome_common.js`'s one changed line — **won't fix**
`window.CTF_WIRE` → `window.MPE_WIRE`, one line of 838, verified by `diff` against the starter.
Checklist item 14 admits "a named, minimal patch recorded in the design note"; design.md:833 declares
the global `CTF_WIRE` → `MPE_WIRE` rename across the fork and `AGENTS.md` states the one-identifier
exception for both `chrome_common.js` and `broadcast_core.js`; `tests/test_viewer.nim` pins the
sha256 and asserts `count("window.MPE_WIRE") == 1` / `"CTF_WIRE" notin chrome`. Making the file
byte-identical again would mean aliasing the starter's identifier back into the fork, which the
rename sweep and that test both forbid. (`b6b4401`'s `eee8254` records the patch in the design note,
which is the right resolution and one this session could not make.)

### F15 — deleted-mechanics residue — partial, `ae77c87`
`src/mpe/mapgen_styles.nim` (15.2 KB of terrain-style generators for a fixed board) is imported by
nothing and is deleted. The other two files the note names are load-bearing imports of the inherited
engine, not dead files: `map_pool.nim` is imported by `arena.nim` (the "pool" map path's seed list)
and `paint.nim` by `sim.nim`. Removing them means editing the starter's map and paint surface, which
is larger than the finding; both are unreachable from `sim.step` — which F5's reachability walk now
*proves* rather than asserts — and the paint block in `gameHash` is gated on `config.floorPaint`,
which no shipped variant sets.

### F16 — the three assertions — `35ccf6c`
1. `counts["directive"] >= 4` → the records are parsed and counted as (round, turn, seat) triples,
   with exactly one of each required, `4 × turnsPerRound × 4 seats`.
2. `onpoint` added to the derived-stream required list, and the walk now stages one real pursuer
   contact inside the tag round so `tag` comes off the same stream (a drifter pack does not reliably
   catch a faster evader inside 540 ticks — that is the mode); all five scrubber beat kinds are
   asserted too.
3. The absent test now exists: `a never-connecting seat is REPORTED and all four rounds still play`
   times a real lobby out with three seats joined, declares the no-show through the server's own
   `declarePlayerFailure` (exported for this) against a `file://` URI, reads `player_failure.json`
   back and asserts `failed_policy_index == 3`, then force-starts with the missing particle as a
   trusted bot and plays four rounds to `complete` / `full_time`.
Nothing was weakened or removed to make any of this pass.

### F17 — `results.bumps` — `e4f3350`, contested
See the header. Implementation detail for whoever rules: `episodeBumps` is appended at the END of
`SimServer` (keyframes are flatty-positional), accumulated in `bankRound` as each round banks, and
is **not** mixed into `gameHash` — `bankRound` runs inside `sim.step`, so the replayed sim reaches
the same value by the same path and no GameVersion bump is required. The live spectator frame keeps
the per-round counter; the endcard column and `results.bumps` become the episode total.
`tests/test_endings.nim` plays four rounds with two particles parked on each other and asserts
`results.bumps` equals the summed per-round counters and exceeds the last round's.

### F18 — three state keys beyond the note's list — **won't fix**
`livePermille`, `episodePermille` and `bumps` are documented in `docs/PROTOCOL.md`, in the manifest's
inlined copy of it, and asserted present by `tests/test_viewer.nim:230-234`. The shipped docs and the
code agree; only design.md:1128's "adds exactly these" block is behind, and this session may not edit
the design note. No repo change is correct here.

### F19 — the wall-stop test — **won't fix**
design.md:1493-1494 ("stops with zero velocity on that axis") and design.md:196-198
(`applyMomentumAxis` is inherited "unchanged") are in tension, and the code follows the second: on a
blocked step with no slide the integrator runs `carry = 0; break` and never writes `velX`/`velY`.
The test asserts exactly what the inherited integrator does, and says so in its own comment. Changing
the test to assert zeroed velocity would fail; changing the integrator would fork the starter's
motion model and force a GameVersion bump for a cosmetic wording difference. The note's two
statements need reconciling, which is a design-note edit.

---

## NOTED (not fixed)

- The pod still serves the starter's static assets that only the removed replay page used —
  `/client/art/walls/*`, `/client/art/lockerroom/*`, `/client/soldier_*_front*.png`,
  `/client/font.ttf` and their `staticRead` consts (~120 lines in `server.nim`). Dead after F14, but
  removing them is not the finding, and the static bundle copies those files from `client/` and
  `data/` itself.
- `client/league_replayer.html` remains in the tree. The bundle builds `league.html` from it
  (`Dockerfile.replay-viewer`), so it is not residue — but its native-mode branch points at
  `/client/replay`, which no longer exists in the pod; only the bundle's own `ROUTE_BASE` path is
  live now.
- `tools/ci/viewer_smoke.mjs` reports `canvas_text.total = 0` on the real replay because the bundle
  draws in a Worker on an OffscreenCanvas, and it instruments the main thread only. The fixture is
  the answer to that for text, but the *shipped* pixel-font sprite path (`global.addSeatSymbolBubbles`,
  `addSeatLandmarks`) is still measured by no gate. Settling it needs either an
  `OffscreenCanvasRenderingContext2D` instrument inside the worker (a change to the verbatim
  template) or a Nim-side bounds assertion on the bubble/landmark sprite rects at bake time.
- The fixture's one remaining `outside` draw is a single glyph 1 px past the right edge of the
  360 px board (`A`, box `[361,234,363,237]`); `never_inside` is 0, and the harness reports `outside`
  without gating it.
