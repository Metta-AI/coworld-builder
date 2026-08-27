# r1 review — magent-battle

Repo: `/workspace/cogame-magent-battle` @ `95e94c9853de770c9afdea85d8d8144e80df9374` (main)
Starter (read-only): `/workspace/starters/coworld-ctf`
Design note: `runs/2026-08-27-magent-battle/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule)
Files opened: 58 (all of `src/magent/*.nim`, `src/magent_battle*.nim`, `replay-viewer/*`, `client/*`,
`tools/*`, `tools/ci/*`, all 12 `tests/test_magent_*.nim`, `coworld_manifest_template.json`,
`.github/workflows/ci.yml` + `coworld-release.yml`, `vendor/UPSTREAM.md`, `vendor/PATCHES.md`,
plus the starter's `chrome_common.js`, `broadcast_core.js`, `replay_broadcast.html`,
`replay-viewer/{config.nims,static_replay.js,static_replay_worker.js}`)
External evidence read: CI run **33052649135** (main, `95e94c9`, conclusion **success**) — full logs of
all four jobs, plus its `smoke-replay` artifact (`episode.replay`, 21,237 B) decoded locally.

## Blocking

**None.** I could not falsify any of checklist items 1–15 or the parallel-batch rule from the code,
the manifest, or the CI evidence. The two places where a strict *textual* reading of a checklist item
differs from what ships are F18 (docs `"type":"uri"` vs the item's `"type":"text"`) and F19 (`.tiny`
at 620 px vs the item's "under 640px"); both are recorded below with the evidence on each side, and in
both cases the operative property the item exists to protect is satisfied and CI-verified. F4 (the
page's byte size) is the third such place and is likewise argued from provenance evidence, not taste.

## Non-blocking

### F1 — `mapSize 31` spawns 30 soldiers per army, not the note's 25 *(correctness)*
- Where: `src/magent/arena.nim:50-96`, `tests/test_magent_spawn.nim:72-89`,
  `vendor/PATCHES.md` §7, `coworld_manifest_template.json:99-104,209-211`
- Observed: `spawnSide()` computes `isqrt((31*31*4) div 100) * 2 = isqrt(38)*2 = 12`; the left block's
  x range is `range(0,12,2)` which the upstream `0 < x` filter cuts to `{2,4,6,8,10}` (5 columns), and
  the y range is `range(9,21,2) = {9,11,13,15,17,19}` (**6** rows) ⇒ 30 cells; the right block
  (`{18..28}`, 6 columns × 6 rows) is truncated to 30. I re-ran the arithmetic independently and it
  agrees. `tests/test_magent_spawn.nim:83-85` asserts 30/30 and `:57-70` asserts the integer spawner
  equals an independent *float* transcription of `generate_map` for `mapSize ∈ {12,31,45,64}`.
  `mapSize 45` gives 81/81 (`:75-77`), and `squadPartition(30)` is `4,4,4,3,3,3,3,3,3`
  (`arena.nim:98-106`).
- Note says: design.md:118-119 and :1151-1156 say 25 per army split `3,3,3,3,3,3,3,2,2` — but :1153
  also says "asserts the number rather than trusting this paragraph".
- Assessment: the builder delta is **sound and consistent with the note's intent**. The note's 25 came
  from miscounting the y range as 5 rows. The divergence is filed in `vendor/PATCHES.md` §7, asserted
  by a test, and propagated into the manifest (variant id/name/description and the `mapSize` property
  description all say 30). The `skirmish` name "Skirmish (31x31, 30 v 30)" matches.

### F2 — the squad controller reads occupancy at decision time *(correctness)*
- Where: `src/magent/control.nim:113-139` (comment `:120-131`), `vendor/PATCHES.md` §6
- Observed: in `chooseAction`, the move scan skips any destination whose `occupantAt` is ≥ 0. I traced
  the note's literal rule and reproduce the deadlock the fixer documents: for `advance`/`focus`,
  `targetCell()` returns the enemy's **own cell** (`control.nim:59,63,77`), so once two soldiers are
  exactly 2 cells apart the argmin of squared distance is the enemy cell itself (distance 0), that move
  is blocked at resolution (`sim.nim:115-116`), and the attack branch cannot fire because 2 cells is
  outside the 8 Moore offsets — the pair is frozen for the rest of the game. Reading occupancy at
  decision time removes exactly that case.
- Determinism is preserved: `chooseActions` (`sim.nim:39-46`) computes **all** actions against the
  unmutated world before `resolveTick` touches anything, so the occupancy read is a pure function of
  the tick snapshot and the wasm re-derivation runs the same code path
  (`replay-viewer/magent_replay.nim:13` imports `magent/sim`). The property the note's rule protected —
  "a dense formation shuffles rather than teleports" — survives, because two soldiers can still pick the
  same empty cell and the loser stays put (`sim.nim:103-117`).
- Note says: design.md:522 "Occupancy is **not** consulted here".
- Assessment: **sound**. One filing nit: `PATCHES.md` is titled "Documented divergences from upstream
  `battle_v4`", and §6/§7 are divergences from the *design note*, not from upstream; they are correct
  content in a file whose title does not cover them.

### F3 — playback is 8 sim ticks/s with chips `[1,2,4,8]`, not 1 tick/frame with `[0.5,1,2,4,8]` *(static-viewer)*
- Where: `src/magent/replay_runtime.nim:13-20,60-61,274-281`, `src/magent/sim_types.nim:40-44`
- Observed: `TicksPerSecondBase = 8`; `advanceReplayFrame` adds `speed * 8` per call to an integer
  accumulator and runs one sim frame per `TargetFps (30)` accumulated, capped at 8 frames per call.
  `PlaybackSpeeds = [1,2,4,8]`, `speedIndex` defaults to 0 ⇒ speed 1. `applyCommand` maps the keys
  `1/2/4/8` (`:249-252`); there is no 0.5 chip, and `chrome_common.js:434-446` builds the chip row from
  `WIRE.speeds`, so the emitted chips are exactly those four.
- Corroborated in CI: the wasm-viewer step's readouts show the clock moving 0 → 1 tick over ~700 ms of
  playback (run 33052649135, "Load the bundle in a real browser"), i.e. ≈8 ticks/s.
- Note says: design.md:990-992 "1 tick per animation frame at 30 fps (speed chips `[0.5, 1, 2, 4, 8]`,
  default 1). A 600-tick episode therefore plays for 20 s".
- Consequence: the CI replay (123 frames) plays for ~15 s and a full 600-tick episode for ~75 s. The
  note's reason for the rate — that a soak must observe advancement rather than a finished replay — is
  served *better*, not worse. **Residue:** `sim_types.nim:40-43`'s `TargetFps` doc-comment still states
  the note's superseded model ("one tick per animation frame at 30 fps, so 600 ticks of episode play
  for 20 s"), contradicting `replay_runtime.nim:13-20` two files away. Unlike F1/F2 this delta is not
  recorded in `PATCHES.md` or anywhere else.

### F4 — `client/broadcast_core.js` is a retargeted rewrite; the chrome's dependencies do survive *(static-viewer)*
- Where: `client/broadcast_core.js:1-24,146-150,505-515,522-552`; starter's
  `client/broadcast_core.js:1386-1403`; `tests/test_magent_viewer.nim:220-244`
- Observed, provenance: the starter's core is 1,407 lines built around the Bitworld sprite protocol,
  vendored SnappyJS and an interpolating pixel camera; the fork is 556 lines with a JSON state channel
  and a cell-space grid renderer. **No proc in it is byte-identical to the starter's**, and
  `pushFeed` — which the note (design.md:922) and the file header both call load-bearing — **does not
  exist in this starter at all** (`grep -n "pushFeed" /workspace/starters/coworld-ctf/client/broadcast_core.js`
  → no match; the cogball scar it cites is another repo's). The file header's claim to have kept
  "function for function … the canvas/DPR sizing, the whole-board camera, … the feed queue and
  `pushFeed`'s SIGNATURE, … the websocket mode" overstates what is literally retained, and the shipped
  test (`test_magent_viewer.nim:223-244`) asserts *name presence*, not the byte-identity the note's
  test 27 (design.md:1300) describes.
- Observed, behaviour — I traced every call the surrounding chrome makes into the core:
  - `replay-viewer/static_replay_worker.js` is the starter's file with identifier renames only
    (`diff` against the starter: 13 hunks, all `_ctf_*` → `_magent_*` plus the `importScripts` line).
    It calls `BroadcastCore.create({canvas, playoutBuffer, viewportWidth, viewportHeight,
    devicePixelRatio, onText, onStatus, onFirstFrame, onTransform, onSendPacket})`, then
    `attachMinimap`, `start`, `sendCommand`, `clickMap`, `zoomAt/setZoom/panBy/panByMap/panTo/resetView`,
    `setViewportSize`, `getPaceStats().draws`, `stop`. **All present** (`:522-552`), the view methods as
    deliberate no-ops for a fixed board, `getPaceStats()` returning the starter's
    `{enabled,queued,presented,interval,draws}` shape that `static_replay.js:271-281` mirrors.
  - `client/page_script.js` calls only `sendCommand`, `setViewportFit`, `start`, and (from the game
    block) `setHeat`. All present.
  - `relayout()` — the one function the checklist names — is **not** in the core in either repo; it is
    in the page. `page_script.js:530-572` is a line-for-line fork of the starter's
    `replay_broadcast.html:4276-4320`, including the four-pass fixed point, the identical
    `Math.max(0.5, Math.min(1.6, boardW / 760))` and `stage.classList.toggle('tiny', boardW <= 620)`,
    and it sets `--hudscale`/`--topband`/`--band` on `document.documentElement`.
  - `chrome_common.js` (byte-identical, F5) reads `s.en, s.pl, s.lp, s.sk, s.ff, s.sp, s.t, s.st, s.mx,
    s.ph, s.lulls, s.beats, s.lead, s.teams[side].lives` — every one of them is emitted by
    `broadcast.nim:190-229`, and `tests/test_magent_engine.nim:125-146` asserts the packet's key set.
- Live consequence found while tracing: the core's own feed rows (`:416-440,146-153,459-467`) are
  handed to `onText`, and the page's `onText` is `onFrame`, which `JSON.parse`es and returns on failure
  (`page_script.js:255-258`). So every row the core formats is silently discarded; the feed the viewer
  actually shows is built independently by the game block (`game_block.html:237-284`). Harmless
  duplication of intent, and it means the "pushFeed signature" latch scar cannot arise here — the
  path is dead.
- Assessment: the delta is **sound in substance** (a paint/flag/hill/FPV draw layer cannot be
  line-forked onto an integer grid) and the starter behaviours the chrome depends on do survive; the
  overstated provenance comments and the name-presence-only test are the residue.

### F5 — chrome provenance verified positively; the page is 42 % of the starter's bytes *(static-viewer)*
- Where: `client/chrome_common.js`, `client/replay_broadcast.html`, `tools/build_broadcast_page.py`
- Observed: `client/chrome_common.js` is **byte-identical** to the starter's
  (`sha256 7ace7287…d72f7c` on both; `cmp` silent). `tests/test_magent_viewer.nim:64-79` pins its
  length (40022) and SHA-1 as literals *and* diffs against the mount when present.
- `client/replay_broadcast.html` (98,086 B, 1,996 lines) vs the starter's (234,070 B, 4,660 lines) —
  **42 %**. Item 14 says "a page a fraction of the starter's size is a rewrite and is blocking", so I
  checked provenance directly rather than by size:
  - `python3 tools/build_broadcast_page.py --starter /workspace/starters/coworld-ctf/client/replay_broadcast.html
    --page-script client/page_script.js --game-block client/game_block.html --out /tmp/rb.html` then
    `cmp /tmp/rb.html client/replay_broadcast.html` → **identical**. The committed page is
    mechanically derived from the read-only starter.
  - `diff` of the inherited prefix (starter lines 1-1603 vs fork lines 1-1082): 17 hunks, every one of
    them either a removal the note lists (`.lives-num`/`.lives-label`, `.squad`/`.squad-pip`,
    `.perk-ico*`/`.hcap`, `#povBadge`, all of `#fpv*`, all of `#viewpanel`, `.ec-heart` incl. ~15 KB of
    base64 heart PNGs, `.beat-marker.{steal,return,capture,kill}`) or a relabel from the note's table
    (title, `lk-cap`, `lk-sub`, `clock-caption`, `mmwarn`, `btn-spoilers` title, `momentum-label`).
    Stage, scorebug, banner lane, kill feed, transport (in full), scrubber + momentum + beat markers +
    lulls + spoilers, endcard and the locker-room curtain are all present and unmodified.
  - Of the 136 KB difference, ~2,000 of the 2,664 missing lines are the starter's own page IIFE
    (starter lines 1604-4660: paintbot's `renderPov`, `ingestFpMap`, `ingestCapHearts`, flag/hill/heart
    rendering) replaced by `page_script.js` (597 lines) + `game_block.html` (317). `page_script.js` is
    itself a recognisable fork, not a rewrite: `relayout()` is line-for-line (above) and
    `buildLockerRoom` keeps the starter's `LK_BOTS` structure with the *same* pose geometry numbers for
    red and blue (fork `:94-103` vs starter `:1772-1789`), reduced from four cogs to two.
- Note says: design.md:916 "A test asserts the starter's byte prefix is intact up to the documented
  splice marker and that the file only grows." Neither half is literally true — the file **shrinks**,
  and `tests/test_magent_viewer.nim:81-106` asserts landmark *order* plus the presence of the builder,
  not a byte prefix. The builder script is stronger evidence than the test the note promised, but it is
  not run in CI, so nothing on `main` would catch a hand-edit of the inherited prefix.

### F6 — every wait is bounded; `turnSpacingMs` is a blocking sleep the note said it would not be *(timeout)*
- Where: `src/magent/decide.nim:207-341`, `src/magent/sim_config.nim:33-50`,
  `src/magent/episode.nim:36-53`, `src/magent/server.nim:515-527`
- Observed bounds, each read at its site:
  - attempt 1: `curly.makeRequests(batch, max(1, attempt1Ms div 1000))` = **9 s**
    (`decide.nim:271-289`); the retry batch = **4 s** (`retryMs`). `clampConfig` forces both ≥ 1000 ms,
    so the whole-seconds floor is an identity (`sim_config.nim:44-45`).
  - retry count: `while open.len > 0 and attempt < 2` — attempt 0 and attempt 1, i.e. **exactly one
    retry** (`decide.nim:262`), and a 429 with no other candidate model breaks out before the retry
    (`:319-324`).
  - outer per-turn deadline: `turnBudgetMs = 14 s`, checked at the top of each attempt
    (`:265-270`), writing a `timeout` fallback record for every still-open seat.
  - `turnSpacingMs = 8 s` floor: implemented as `sleep(min(spacing, spacing - since))`
    (`:252-255`) — a real blocking sleep on the game loop, before `turnStart`'s budget has any effect.
    Bounded at 8 s, so checklist item 5 holds; two consequences: (a) ticks do **not** advance during
    the wait, and (b) because `turnStart` is taken *before* the sleep (`:210`), the worst-case wall
    clock inside one turn is 8 + 9 = **17 s**, exceeding `turnBudgetMs` 14 s (the budget then suppresses
    the retry rather than the first attempt).
  - engine stop: `maybeStop` fires at `elapsed >= wallClockBudgetSeconds` (660, clamped to ≤ 660 at
    `sim_config.nim:46-47`) at the **top** of every frame (`episode.nim:44-53,156`).
  - budget guard: `elapsed + 2*14 > 660` ⇒ LLM off for the rest of the episode (`decide.nim:216-223`),
    i.e. from elapsed > 632 s; a `budget_guard` record names the turn.
  - lobby: `lobbyJoinTimeoutTicks 2400` at 30 fps ≈ 80 s (`sim_state.nim:141-142`,
    `server.nim:519-526`); frame limiter is a `sleep(1)` loop bounded by `frameDuration`.
  - Worst case I compute from these: 30 × 17 = 510 s of turns + ≤ 80 s lobby + ~4 s of sim + 20 s
    shutdown grace ≈ **615 s < 660 s stop < 720 s (60 % of the manifest's 1200 s)**. A stop that lands
    mid-turn is served at most 17 s late ⇒ 677 s, still inside 720.
- Note says: design.md:157 the spacing is "a floor on the wall clock between consecutive **batch
  starts**, not a sleep on the critical path: the loop keeps stepping ticks while it waits."
- Assessment: no hang, no unbounded wait, budget intact; the note's "keeps stepping ticks" property is
  not implemented.

### F7 — `MaxReplyBytes` is enforced in runes, not bytes *(other)*
- Where: `src/magent/llm.nim:181-184`, `src/magent/sim_types.nim:27`
- Observed: `if body.len > MaxReplyBytes: body = body.truncateRunes(MaxReplyBytes)` — the guard is a
  byte test but the cut is 8192 **runes**, so up to ~32 KB of a multi-byte body can reach `parseJson`.
  Rune-safe (checklist item 9 is about safety, and this is the safe direction), and a truncated JSON
  body raises → `parse_error` → retry → `pincer`, which is the documented ladder.
- Note says: design.md:413 "whole reply | bytes | ≤ 8192 read from the provider before parsing".

### F8 — the fallback `cause` vocabulary is not the note's closed set *(other)*
- Where: `src/magent/decide.nim:306-313,331-338`
- Observed: the emitted causes are `timeout`, `transport_error`, `parse_error`, `throttled`,
  `no_credentials`, `budget_guard`. **`throttled` is not in the note's enum** and **`disconnected` is
  never emitted** (a disconnected seat simply keeps playing `pincer`; `episode.nim:60-75`).
- Note says: design.md:329 `cause ∈ {timeout, parse_error, transport_error, no_credentials,
  budget_guard, disconnected}`. Nothing consumes the enum as a closed set
  (`replay_summary.py:202-203` only counts fallbacks), so this is vocabulary drift, not a break.

### F9 — the main viewer smoke omits `--soak`, so advancement is never gated *(static-viewer)*
- Where: `.github/workflows/ci.yml:407-411`, `tools/ci/viewer_smoke.mjs:158,526`
- Observed: the step passes `--bundle --replay --timeout 90 --strict-text-bounds`; `--soak` defaults to
  `0` and the whole soak block is `if (loaded && args.soak > 0)`. Run 33052649135's step output carries
  no `soak:` line, confirming it did not run. What *is* gated: `data-replay-loaded="true"`
  (`{"loaded":true,"ms":338,…}`) and `canvas_text.never_inside == 0`. The scrub readouts are printed
  but not asserted (`viewer_smoke.mjs:568-585` records them; nothing compares them).
- Note says: design.md:1321-1324 requires `--soak 10` and "fails the job unless … the clock/tick
  readouts **advance** across the soak". Checklist item 13 does not itself name the soak, which is why
  I am filing this non-blocking.

### F10 — `canvas_text` is structurally 0; the DOM fixture is the only text gate, and it does not check its own string lengths *(legibility)*
- Where: `client/broadcast_core.js` (no `fillText`/`measureText` anywhere — `grep -c fillText` → 0),
  `tools/ci/renderer_fixture.html:39-50,113-165`, `.github/workflows/ci.yml:441-450`
- Observed: this viewer draws **no** text on canvas at all — the board layer is chips, heat bins,
  scorch marks and a chalk polyline; every string (feed, scorebug, clock, endcard, banners, beat
  labels) is DOM inside the starter's own layout. Both CI smoke steps therefore report
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)`, which per checklist item 15 "is not evidence of anything" — correctly so
  here, because there is nothing for it to cover. Item 15's "text laid out relative to another element"
  hazard (the cogchemists bubble) does not exist: no speech bubble is drawn over a cog.
- The required worst-case fixture exists, runs in its own `ci.yml` step with `--strict-text-bounds`,
  loads the **shipped** `dist/static-replay-viewer/index.html` in an iframe, waits for its
  `data-replay-loaded`, then drives the real `MagentChrome.frame` with a 120-rune `say` on both seats
  at 360/620/1024 px and measures the laid-out nodes: it fails if no `.mg-say` row reached the feed, if
  the row's box is < 20×6 px, if it is at a negative top/left, or if `#pname-0` measures < 18 px wide.
  It reported `loaded: true` in run 33052649135.
- Gap: it never asserts that `CAP_SAY` is still 120 runes or that the rendered row's text length is
  unshortened — checklist item 15's "The fixture asserts its own strings are still full-length — one
  quietly shortened remark leaves it passing while testing nothing." A future edit that shortened
  `CAP_SAY` (`renderer_fixture.html:43-50`) would leave the fixture green.

### F11 — chrome_common's verdict cap can never fire; game beats are not spoiler-gated *(legibility)*
- Where: `client/chrome_common.js:579-619,488-505`, `client/game_block.html:179-199,288-295`
- Observed: `ingestBeats` recognises only `steal`/`return`/`capture`/`gameover`; this game emits
  `firstblood`/`rout`/`wipe`/`fallback`/`end` (`replay_runtime.nim:150-194`). So (a) the shared
  `markBeat` is never called — which is the note's intent, and it is why the only markers on `#scrub`
  are the game block's labelled `<button>`s (verified: `chrome_common.js` registers no `#scrub` click
  handler, so there is no competing seek); and (b) `setVerdict` is never reached, so `#scrub-win` and
  `#win-chip` stay empty for the whole replay even though both ids are kept. The endcard carries the
  verdict instead (`page_script.js:440-472`).
- Also: `applySpoilers` only walks chrome_common's own `markerEls`, so with spoilers **off** the game
  block's five beat kinds still sit on the scrubber ahead of the playhead — while `#btn-spoilers`'
  retitled tooltip promises "kills / routs / winner on the timeline ahead of the playhead".

### F12 — a backward seek can duplicate a beat button *(legibility)*
- Where: `client/game_block.html:297-304` (`if (jumped) placed = {};`), `:179-199`
- Observed: on a detected backward jump the dedup map is cleared but the already-appended `<button>`
  nodes are not removed, and `beatsPlaced` stays `true`. The pre-scanned markers are therefore not
  re-added, but a live `fallback`/`firstblood` event replayed after the seek appends a second button at
  the same offset. Cosmetic (two identical markers overlap); both still seek correctly.

### F13 — the live (dev-only) `/client/replay` page has an inert transport axis *(other)*
- Where: `src/magent/server.nim:337-341,491-492`, `src/magent/broadcast.nim:188-193,225-229`
- Observed: in live mode `replayPlayer` is a default-initialised `ReplayPlayer`, so the packet carries
  `t = 0`, `st = 0`, `mx = 1`, `sp = 1`, and `lulls`/`beats`/`lead` are empty arrays on the first
  frame. `chrome_common.renderTransport` then renders `0 / 1` in `#tick-clock` and a static playhead,
  and `ingestLeadSeries` sets `fullLeadSeries` to an empty-points object so `recordMomentum`'s
  accumulate-as-played fallback never runs. `#clock-time`/`#clock-caption` are driven from `mg.*` and
  are correct. Only affects the developer page (never declared to the platform).

### F14 — the CI viewer smoke's 50 % scrub click did not seek *(static-viewer, inferred)*
- Where: CI run 33052649135 step "Load the bundle in a real browser";
  `client/replay_broadcast.html:800`, `client/page_script.js:84,161-172`
- Observed: the printed readouts are `0%="…turn 1/15 TICK 0/300 · 30 V 30"`,
  `50%="…turn 1/15 TICK 1/300 · 30 V 30"`, `100%="game 2/2 · turn 2/15 TICK 26/300 · 0 V 5"`. I decoded
  the same replay: `gameStart` frames are 6 and 67, there are 123 hash records and 124 frames, so
  `st = 6`, `mx = 123` and a 50 % click should send `s:65` — frame 65 is inside game 1's game-over hold
  (tick 31, 3 v 0). The reported state is game 1 tick 1 with both armies intact, which is frame 6-7.
- Inference (not observed directly): `#lockerroom` is `inset: 0; z-index: 25` and only becomes
  click-through when `.gone` lands — `#lockerroom.gone { opacity: 0; pointer-events: none; }`
  (page line 800) — which `dismissLockerRoom` schedules `LOCKER_MIN_DWELL_MS = 900 ms` after the first
  frame (`page_script.js:84,161-172`). The 50 % click happens ~400 ms after load (`ms: 338`), i.e. while
  the curtain is still hit-testable; the 100 % click ~1.1 s in, after it is not. The 0→1 tick drift over
  700 ms independently corroborates the ~8 ticks/s of F3. Both the curtain rule and the 900 ms dwell
  are inherited verbatim from the starter (`/workspace/starters/coworld-ctf/client/replay_broadcast.html:1295,1754`).
- Consequence: no user-visible defect (a human cannot click a scrubber under a visible curtain), but
  the smoke's mid-replay scrub readout is not the evidence it looks like. Combined with F9, nothing in
  CI currently exercises a mid-replay seek.

### F15 — smaller note-vs-code deltas, each traced *(other)*
- `client/league_replayer.html` is listed as a forked file (design.md:575) and **is absent** from the
  repo. Nothing references it; `?embed=1` support lives in `page_script.js:174-240`.
- `results.magentReward` is an array of decimal **strings** (`roster.nim:81`, `formatMilli`), where
  design.md:764 shows numbers. The manifest declares `{"items":{"type":"string"}}`
  (`coworld_manifest_template.json:145`), so document and schema agree, and
  `tests/test_magent_engine.nim:32-36` pins the key sets equal.
- `MaxUnits = 400` (`sim_types.nim:35`) vs the note's 200 (design.md:724). Pools are sized above the
  largest configured board either way.
- `MaxPromptRunes`/`MaxPolicyLabelRunes` are re-declared as local constants in
  `src/magent_battle_player.nim:30-31` instead of imported from `sim_types`, so the 4000/64 caps exist
  twice and can drift.
- `orders` is additionally accepted as a JSON **object** keyed by squad id
  (`directives.nim:166-173`) — more tolerant than design.md:421 ("whose `orders` is not an array is a
  parse failure"); a non-array, non-object `orders` still raises `DirectiveError` (`:176-177`), which is
  what the retry/fallback ladder needs, and `tests/test_magent_control.nim:210-215` asserts it.
- `SimEventKind` declares `Rout`, `TurnStart` and `Fallback` (`events.nim:12-17`) but the only
  `emitEvent` call sites are `Attack`, `Kill`, `Wipe`, `PhaseChange` and `Directive` — three kinds can
  never appear in the tier-2 stream.
- `tests/test_magent_endcard_labels.nim:80-85` asserts each re-mapped string is *present*; the note's
  test 31 (design.md:970-971) says "present exactly once".
- `ci.yml` has no step that re-runs `tools/tune_baselines.nim --check` (design.md:1253-1254 says it
  does); the sweep is instead re-run inside `tests/test_magent_tuning.nim:17-31`, which asserts the
  shipped pick still ranks in the top half of the grid, plus `:9-14` pinning it to
  `tools/ci/baseline_tuning.json`.
- `tests/test_magent_engine.nim:39-57` ("no seat can stall") covers only the seat that **never
  connects**; the note's test 18 also specifies "a seat that connects then never answers". The closed
  failure payload is asserted against a literal the test itself builds, not against the JSON
  `declarePlayerFailure` writes (`server.nim:290-301`).
- `Dockerfile.replay-viewer` correctly expects no `magent_replay.data` (the `--preload-file`/`FILESYSTEM=1`
  pair was dropped with the asset preload); design.md:1091 still lists `magent_replay.{js,wasm,data}`.
- Tracked stray artifacts at the repo root: `p0.log`, `p1.log` (local player logs, 365 B / 361 B,
  committed in `d9d78c0`), and `nim.cfg` is both committed and listed in `.gitignore`.

### F16 — `episode_timeout_minutes` is 20 and every budget fits, but the note's own arithmetic table is stale *(other)*
- Where: `coworld_manifest_template.json:4,202,223,243`, `tests/test_magent_manifest.nim:141-155`
- Observed: 20 min = 1200 s; `wallClockBudgetSeconds` is 660 in both variants and 240 in the cert
  fixture; the schema's maximum is 660 and `clampConfig` re-clamps to 660. The test asserts
  `timeoutSeconds >= 1200`, `budget <= 660` and `budget*100 <= timeoutSeconds*60` (i.e. ≤ 60 %).
  design.md:301-311's worst case (420 s of turns → 544 s total) is computed from a 14 s per-turn cap
  that F6 shows is really 17 s; the real worst case (~615 s) is still inside both 660 and 720.

### F17 — `config_schema.wallClockBudgetSeconds` description says "55 percent" *(other)*
- Where: `coworld_manifest_template.json:114`
- Observed: the description reads "55 percent of the assumed 1200 s episode timeout"; 660/1200 = 55 %,
  which is correct arithmetic for the stop, while the checklist's 60 % applies to the 720 s settle
  target. Not wrong, just a different number from the one a reader may be looking for.

### F18 — `game.docs` uses `"type":"uri"` where checklist item 10 spells `"type":"text"` *(manifest)*
- Where: `coworld_manifest_template.json:30-53`; `prompts/30-review-loop.md` item 10
- Observed: the **structure** item 10 names is exactly what ships —
  `docs.readme` is an object, `docs.pages` is a list of `{id, title, content:{type,value}}` — but the
  content discriminator is `"uri"` with a GitHub blob URL, not `"text"` with an inline value.
  `game.protocols` carries both `player` and `global` as `{"type":"uri","value":…}` objects
  (`:20-29`), which item 10's other half requires.
- Counter-evidence that this is intended and accepted: design.md:1116-1118 specifies `uri` explicitly;
  `tests/test_magent_manifest.nim:93-108` asserts the object shape and the https values; and CI's
  `manifest` job runs the **installed** `coworld[auth]==0.1.43`'s own
  `validate_upload_manifest` / `_load_template_manifest` / `load_manifest` over the built manifest and
  passed (run 33052649135, job 98451649555, `manifest in 11s`, conclusion success).
- Flagging it because item 10 is a named checklist item whose literal spelling differs from the tree;
  the evidence that the platform validator accepts `uri` is the CI job above.

### F19 — labels are hidden at `boardW <= 620`, not "under 640px" *(legibility)*
- Where: `client/page_script.js:563` (`stage.classList.toggle('tiny', boardW <= 620)`),
  `client/game_block.html:58-62`, `client/replay_broadcast.html:1619,1735`
- Observed: `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`
  is present verbatim (`game_block.html:6-11`) and asserted
  (`tests/test_magent_viewer.nim:213-215`). The label-hiding rule is
  `#stage.tiny .plate .alive-label, #stage.tiny .plate .kill-num, #stage.tiny .plate .fb-glyph
  { display: none; }`, and `.tiny` is toggled at **620 px**, inherited verbatim from the starter
  (starter `replay_broadcast.html:4310`), which the note pins as "kept verbatim" (design.md:1046). The
  game block's own comment says "Under 640px of board the labels go" — the comment and the checklist
  say 640, the code says 620. Between 621 and 640 px the labels stay. The case the item exists for
  (the ~360 px featured embed) is well inside `.tiny`, and the fixture drives 360 px explicitly.

## Traced and consistent

**Resolution rules**
- `src/magent/sim.nim:48-125` — one tick, in the note's order: snapshot of who was alive
  (`:67-69`), attacks ascending attacker id with the not-registered rule for empty cells and friendlies
  (`:73-99`, `attack_penalty` charged either way, `attack_opponent_reward` only on a registered enemy
  hit, immediate death freeing the cell, one `kill_reward` to the killer and one `dead_penalty` to the
  victim's army), then moves ascending id with on-board + unoccupied-at-application checks
  (`:103-117`), then recovery capped at `HpMax` (`:120-123`), then `evaluateEnd` (`:15-28`).
  `step_reward` is credited per soldier alive at the start of the tick (`:58-60`); reward accumulation
  is order-independent so paying it first is not observable.
- `src/magent/arena.nim:17-34` — 12 move offsets in exactly the note's order, 8 attack offsets in
  exactly the note's order, `ActionDoNothing 0 / ActionMoveBase 1 / ActionAttackBase 13`, and
  `ActionCount 21` (`upstream.nim:54`). `tests/test_magent_sim.nim` "offset tables" derives both sets
  from `dx²+dy² ≤ 4` and `≤ 2.25` independently.
- `src/magent/control.nim:41-139` — the note's controller table, verb by verb: `advance` → nearest
  living enemy (ties lowest enemy id, `:24-39`); `hold` → `(x,y)`; `focus` → living centroid of squad
  S, degrading to `advance` when S is extinct (`:57-63`); `flank` → enemy centroid ± 8 in y clamped to
  the board, switching to the centroid once within `ViewRadiusSq` (`:64-73`); `retreat` →
  `(ownBackX, u.y)` with `attackOk = 0`. Attack preference is focus-squad first then lowest hp with
  strict `<`, so ties break by the pinned offset order (`:92-109`); the move scan requires a strictly
  smaller squared distance or emits `do_nothing` (`:133-138`). No RNG anywhere in the file.
- Five reward terms and every other upstream constant live once, in `src/magent/upstream.nim:24-69`,
  with `vendor/upstream/battle.py` byte-pristine (`sha256 c5f589f0…c37ed`, matching
  `vendor/UPSTREAM.md`) and `tests/test_magent_upstream.nim` regex-parsing the vendored file against
  each of them. Integer pins hold: hp in tenths, rewards in thousandths, `isqrt` instead of `sqrt`,
  `sum div count` centroids, and `tests/test_magent_sim.nim` "no floating point in the sim" greps
  `sim/units/arena/control/baselines` for `float`, `sqrt`, `/` and float literals with comments
  stripped.
- Two games, sides swapped: `episode.nim:126-149` flips `redSlot` on game 2 and records the swap as a
  `gameStart` record stamped `frame + 1` (the comment at `:143-147` explains why, and the smoke replay
  bears it out: starts at frames 6 and 67, game 1 ran 31 ticks + 30 hold). `tests/test_magent_engine.nim:28`
  asserts opposite `redSlot`s. Both games re-spawn from the same pure `initUnits(mapSize)`.
- Scoring: `sim_state.nim:172-180` is the note's formula exactly; `tests/test_magent_sim.nim`
  "scoring is zero-sum" and `test_magent_tuning.nim:44` both assert `score[0]+score[1] == 0`, and the
  smoke episode's `results.scores` are `[-2, 2]`.
- End reasons: `wipe` / `tickCap` (`sim.nim:15-28`), `wallClock` (`episode.nim:36-53`), `fault`
  (`:108-124`) — each via `sim.applyStop` → `bankGame`, the same proc playback calls.

**Decision path**
- `decide.nim:273-289` builds one `RequestBatch` containing **both** seats' requests and issues them in
  a single `engine.client.curl.makeRequests(batch, …)` call. There is no per-seat request loop anywhere
  (the parallel-batch rule).
- Tolerant parse: `directives.nim:100-138` scans for the outermost balanced `{…}`, tolerates fences and
  trailing prose, and falls back to first-brace..last-brace; `tests/test_magent_control.nim:239-245`
  drives a fenced reply with prose on both sides.
- Repair-don't-reject: `directives.nim:199-244` — unknown verb, bad squad id, `focus` on a non-enemy
  id, `flank` with no side, `hold` with no coords all fall back to *that squad's previous* order and
  increment `rejected`; `hold` coords clamp into `[0, mapSize)`; duplicates last-wins; entries past the
  ninth dropped; `say`-only is usable. All six behaviours have their own `block` in
  `tests/test_magent_control.nim:120-245`, and `sim.ordersRejected` is surfaced in the results.
- Fallback identity: `baselines.nim:111-118` — `fallbackDirective` *calls* `pincerDirective`; the two
  are asserted order-for-order over 25 randomised worlds (`test_magent_control.nim:96-119`).
  `fallbackTurns` / `llmTurns` are counted per turn from `directive.source` (`episode.nim:94-99`) and
  re-derived on playback from the chat stream (`roster.nim:166-171`).
- Aliases only in the prompt: `decide.nim:60-144` builds the view from `seatAliasName`/`squadAlias`
  with enemy squads visible only where `visibleSquadStat` finds a member inside `dx²+dy² ≤ 36`
  (`units.nim:84-135`); `last_seen_turn` is `null` until first seen; all nine squads always listed.
  Opponent name, notes, orders and stats are absent. Checklist item 4's other half — real names
  spectator-side — is `broadcast.nim:123-136` (`seats[].name`) rendered by
  `page_script.js:293-328`, with `showPlayerLabels: false` in every shipped config.

**Truncation**
Every recorded string goes through `sim_types.truncateRunes` / `sanitizeLine` / `sanitizeSay`
(`sim_types.nim:93-119`): `say` 120 (`directives.nim:204,281`), `notes` 240 (`:205`), policy label 64
(`decide.nim:187`), `stopDetail` 200 (`episode.nim:119`, `roster.nim:118`), fallback `detail` 200
(`decide.nim:177`), provider error bodies 200 (`llm.nim:165,174,180`), `PLAYER_PROMPT` 4000
(`server.nim:425-426`, `magent_battle_player.nim:47-48`). `boundedDirectiveRecord`
(`directives.nim:286-302`) shrinks `say` on rune boundaries rather than slicing the serialised JSON.
`tests/test_magent_control.nim:218-238` and `tests/test_magent_replay.nim:186-244` fill every cap with
4-byte emoji and assert `validateUtf8() == -1` plus a strict Python-side `raw.decode("utf-8")`.

**Replay writer and self-sufficiency**
`replays.nim` writes `COWLDMAG` + format 1 + game name/version + the resolved config JSON + records
(join/leave/gameStart/orders/chat/hash/stop), little-endian and length-prefixed; the config carries
`seed`, `num_agents`, `mapSize`, `maxTicks`, `maxGames`, `turnTicks`, every upstream constant,
`players[].name` and `slots[]` and **no** `tokens` (`sim_config.nim:140-192`). One hash per frame
(`episode.nim:124`); the wall-clock/fault stop is a record applied by `sim.applyStop` on both sides.
`tests/test_magent_replay.nim:28-124` runs record→re-derive for **all four** end reasons and
`:126-154` corrupts one recorded hash and asserts the divergence is reported at that exact tick.
`tools/replay_summary.py` emits the note's schema and is run over the real smoke replay in CI
(`replay summary ok: magent-battle/v1 complete 123 frames`); I re-ran it locally against the artifact
and got names/aliases/policyKinds/games/tickCount/directives/fallbacks/results as documented.

**Viewer re-derivation**
`replay-viewer/magent_replay.nim:13` imports `magent/[broadcast, replay_runtime, replays, roster, sim]`
— the same `src/magent/sim.nim`, reached through `switch("path", rootDir / "src")`
(`config.nims:9`). `magent_load_replay` parses, pre-scans the whole episode headlessly, resets and
renders frame 0 (`:51-81`); `magent_mismatch_tick` returns `checkReplayHash`'s tick or −1 (`:110-111`);
`stampStage`, `bytesFromPointer`, `lastError` and the `emscripten_exit_with_live_runtime()` epilogue are
all present. The display is derived from that re-derivation only: `renderCurrent` → `buildStateJson`
from the re-simulated `SimServer`.
Link flags vs bootstrap, both from **coworld-ctf**: `config.nims` has no `MODULARIZE` and no
`EXPORT_NAME` (verified by grep and by `tests/test_magent_viewer.nim:255-257`), and the worker sets
`Module.onRuntimeInitialized` (`static_replay_worker.js:189-192`) — the matching pair. `diff` against
the starter's four files shows identifier-only changes plus the dropped `--preload-file`/`FILESYSTEM=1`
and the `frameMs` source. `ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`,
`EXPORTED_RUNTIME_METHODS=HEAPU8` and all 13 exported functions are present.
`data-replay-loaded="true"` is set on `<html>` in the adapter's `'loaded'` branch
(`static_replay.js:161-165`), which the worker posts only **after** `ingestPacket()` has handed the
first frame to BroadcastCore (`static_replay_worker.js:122-131`); `data-replay-error` is set in
`showFailure()` (`:8-27`). CI's browser step reports `loaded: true` at 338 ms.

**Chrome / transport rules (item 14 a–d)**
(a) `relayout()` sets `--hudscale`, `--topband`, `--band` on `document.documentElement`
(`page_script.js:541,562,567-568`). (b) Nothing the fork adds is fixed inside the band: the only new
positioned element is `#heatchip`, anchored `top:` in `#chrome` with no `bottom`
(`game_block.html:65-80`, asserted at `test_magent_viewer.nim:205-211`). (c) `#endcard` keeps the
starter's `bottom: var(--band, 0px)`, is shown with `#endcard.on`, is removed explicitly on a scrub
click (`page_script.js:493-494`) and state-removed whenever the phase is not a completed gameover
(`:443-446`) — the starter's `else { remove('on') }` (starter page line 2072) internalised, so every
seek (scrub, beat button, back/forward, keyboard) takes it down on the frame the seek produces.
`card.complete` is `gameLog.len >= maxGames`, so it never appears between the two games. (d) Beats are
`<button>`s with `title`, `aria-label` and `CTX.send('s:' + tick)` (`game_block.html:186-198`), with CSS
for exactly `firstblood, rout, wipe, fallback, end` (`:84-112`) — the set
`tests/test_magent_viewer.nim:170-191` computes from the page and compares to the emitted set.
`#viewpanel` and every child id, plus `#fpv*`, `#povBadge` and the ctf plate internals, are removed from
markup, CSS and JS by the builder and asserted absent with comments stripped
(`test_magent_viewer.nim:108-136`); `broadcast_core` keeps the zoom/minimap methods as no-ops so the
inherited adapter surface is intact.

**Endcard label re-mapping** — all ten rows of the note's table are in the tree and pinned:
`Commander|Kills|Lost|Alive|Reward` (`page_script.js:431-432`), `Troops left` (`:437`),
`TROOPS LEAD`, `alive-label Alive` (`:303-304`), `Forming up on the line…`, `Mustering`,
`Replay hash mismatch at tick N — showing recorded orders` (`:345-355`),
`kills / routs / winner`, `#lockerroom` aria-label untouched, and RED/BLUE replaced by alias + a
`side-chip` on both the plates and `ec-tname` (`:296-327,425-430`). The forbidden-vocabulary grep
(`tests/test_magent_endcard_labels.nim:12-14,68-78`) runs comment-stripped over all four client files
and is green.

**Manifest** — `num_agents: 2` inside `variants[0].game_config`, `variants[1].game_config` and
`certification.game_config` (lines 194, 215, 235), absent at every variant top level (asserted
`test_magent_manifest.nim:10-25`); no literal `tokens` in any `game_config` while `config_schema`
still requires it (`:27-37`, manifest `:57-65`); `game.replay_viewer.bundle = static-replay-viewer`
under `game`; `episode_timeout_minutes` top-level; four top-level tags and no `game.tags`; every
`config_schema` array carries `minItems`/`maxItems`; two `player[]` entries both seated in
`certification.players` with `limits.cpu: "1"`; results_schema closed and asserted key-for-key equal to
`armyResultsJson` (`test_magent_engine.nim:32-36`, `test_magent_manifest.nim:175-192`).
`tools/ci/docker_smoke.sh` is the builder template with only the three substitutions
(`diff` → 6 hunks, all substitutions) and carries all four `SEAT-COUNT` invariants plus the
`SMOKE_SEATS` cross-check; **`grep -c "SEAT-COUNT FAIL"` over the whole docker-smoke log of run
33052649135 = 0**, and the job printed `smoke OK: seats=2 results=588B replay=21237B reason=complete`.

**Release order and scaffold (item 12)** — `coworld-release.yml` runs Build manifest (159) → Certify
(173, `--timeout-seconds 300`) → Upload the policies (216) → Upload the Coworld (314) → Put the Coworld
secret (352), in that order, with the certify step gated on a static-bundle liveness marker.
`tools/ci/policies.json` declares four policies on one image: two `PLAYER_PROMPT` champions (champion
#2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) and the `line`/`pincer` fillers.
The checklist's placeholder gate exits 0 (`./tools/ci/check_placeholders.sh` → "no scaffold
placeholders in 9 files", exit 0); the only surviving angle-bracket names are the four documented
runtime ones (`<cow_id>`/`<sha>` in `ci.yml:295`, `<run_id>` in both release/submit recipes,
`<name>:vN` in `coworld-submit.yml:31`). Both scripts are mode 100755 and invoked by path.

**CI (item 1)** — `gh run list -R Metta-AI/cogame-magent-battle --branch main -w ci.yml`:
run **33052649135**, `completed / success`, four jobs `docker-smoke`, `manifest`, `test`, `wasm-viewer`
all ✓, `wasm-viewer` declaring `needs: docker-smoke` and running the browser step (not skipped, not
`continue-on-error`). The `test` job ran the four shards in **both** debug and release: 12 suites,
**164 `[OK]`, 0 `[FAILED]`** (82 distinct cases × 2 modes). "No test loosened":
`git log --stat -- tests/` over this run's history shows `d9d78c0` adding 21 test files (+2,343 lines)
and `5a61572` adding 21 lines to `test_magent_viewer.nim`; `git log -p 5a61572..HEAD -- tests/` is
empty. No deletion, no widened tolerance, no `skip`/`xfail`, no removed file.

**Baseline legality (item 7)** — `tests/test_magent_control.nim:44-72` drives 200 pseudo-random worlds
(both map sizes, both sides, extinct squads, randomised hp) through **both** baselines and validates
nine orders, unique own-side ids, in-enum verbs, on-board `hold` coords, `focus` targets that are
*existing enemy* squads, `left|right` sides and a ≤ 2048-byte serialisation; `test_magent_engine.nim:15-37`
runs a full scripted two-game episode to `reason == "complete"` with zero-sum scores. Tunables come
from `tools/tune_baselines.nim`'s head-to-head sweep, recorded in `tools/ci/baseline_tuning.json` and
re-swept in `test_magent_tuning.nim`.

## Could not determine

- **Whether the LLM leg works against a live provider.** `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so `newLlmClient` disables itself and every directive in every CI replay is
  `source: "scripted"` — I confirmed this on the artifact (8 directives, all `scripted`, 0 fallbacks).
  Nothing in the tree exercises `requestFor`/`textOf` against a real 200/401/429 body. Settled by
  phase 60's keyed run: `replay_summary.py` output with `[.directives[]|select(.source=="llm")]|length`
  > 0, non-empty `say`, and the game log containing neither `falling back` nor
  `LLM provider is unavailable`.
- **Whether a 45×45 episode with real LLM latency settles inside 660 s.** The `tick budget` test covers
  sim time only (< 4 s for 2×300 ticks); the 17 s worst-case turn of F6 is arithmetic from the code, not
  a measurement. Settled by a single hosted `battle`-variant episode with the key present, reading
  `results.reason` and the wall clock.
- **Whether `viewer_smoke --soak 10` would pass on this bundle.** No soak has ever run (F9), and the
  scrub evidence that would substitute for it is compromised by the locker-room curtain (F14). Settled
  by adding `--soak 10` to `ci.yml:407-411` and reading the emitted `soak:` line.
- **Whether the 620 px `.tiny` threshold matters at any real embed width.** The featured iframe is
  ~360 px (well inside) and desktop is well outside; I have no evidence about a 621–640 px surface.
  Settled by the fixture driving 630 px alongside 360/620/1024.
