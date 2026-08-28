# r1 review — cogame-atari-57

Range: `1991015..309a9b3` (three commits: `1991015` bootstrap, `d31e0f7` tests + tuning sweep,
`309a9b3` drop caos/nix scaffolding). Reviewed at sha `309a9b3438318ae8aa36d52c55db3d4fba1040d8`.
Files read: 60 (all of `src/lane/*.nim` except `global.nim` which was read in part, both entrypoints,
all four `replay-viewer/` files, `client/replay_broadcast.html` in full plus byte-diffs of
`chrome_common.js` / `broadcast_core.js` against `/workspace/starters/coworld-ctf`, 14 test files,
7 tools, 3 workflows, the manifest, `config.json`, `compose.yaml`, both Dockerfiles, `AGENTS.md`,
`tests/data/golden_hashes.json`, and the full CI log for run 33203089677).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule).

Method note on labels below: **observed** = I read the lines quoted; **inferred** = I reasoned from
lines I read; **untested** = would need a run to settle.

---

## Blocking

### B1 — `#viewpanel` is removed, but the page still drives `core.zoomAt` / `core.setZoom` / `core.panBy` / `core.resetView` on a board the design declares always fits the frame
- Where: `client/replay_broadcast.html:2381-2383`, `:2396`, `:2439`, `:2456`, `:2511-2512`, `:2525`,
  `:2542`; the transport that carries the calls across the Worker boundary at
  `replay-viewer/static_replay.js:240-262` and `replay-viewer/static_replay_worker.js:216-228`.
- Observed, in the page (all of these are **above** the `atari-57 additions` banner at line 2649,
  i.e. inherited starter JS that was kept rather than removed):
  - `2381` `else if (k === 'z') core.zoomAt(ZOOM_STEP);`
  - `2382` `else if (k === 'x') core.zoomAt(1 / ZOOM_STEP);`
  - `2383` `else if (k === '0') core.resetView();`
  - `2396` `core.panByMap(stepX * step, stepY * step);` (arrow keys, guarded on `vt.zoom > 1`)
  - `2439` `core.zoomAt(Math.exp(-ev.deltaY * unit * 0.012), p.x, p.y);` (ctrl+wheel / trackpad pinch)
  - `2456` `core.setZoom(gestureZoom * ev.scale, …)` (Safari `gesturechange`)
  - `2511-2512` `core.zoomAt(g.span / pinchSpan, …); core.panBy(g.midX - pinchMidX, …);` (two-finger pinch)
  - `2525` `core.panBy(dx, dy);` (pointer drag)
  - `2542` `core.resetView();` (dblclick)
  `static_replay.js:240-256` exposes `zoomAt`, `setZoom`, `panBy`, `panByMap`, `resetView` as real
  `postMessage({type:'view', …})` calls, and `static_replay_worker.js:216-223` forwards each into
  `broadcast_core`'s live zoom/pan implementation. So these are wired end to end in the shipped
  bundle, not dead code.
- What IS removed (verified, so the finding is narrow): the panel markup and ids are gone
  (`tests/test_viewer.nim:83-104` asserts `id="viewpanel"`, `id="minimap"`, `id="minimap-canvas"`,
  `id="zoombar"`, `id="zoom-out"`, `id="zoom-in"`, `id="zoom-slider"`, `id="zoom-read"` and the
  `#fpv*` / `#povBadge` ids are all absent, and I re-confirmed by grep). Their CSS is gone too: I
  extracted the first `<style>` block from both pages and diffed it — 1138 lines here against the
  starter's 1453, with every removed line belonging to a `#povBadge` / `#fpv*` / `#zoom*` /
  `#minimap*` / `#viewpanel` rule and only three comment lines reworded. `attachMinimap` is
  unreachable: `static_replay.js:264` (`pendingMinimap = surface`) is only called from
  `core.attachMinimap(surface)`, and nothing in the page calls it now that `#minimap-canvas` is gone.
- Checklist item: 14, fourth bullet — "**Zoom bar + minimap (`#viewpanel`) only if the board is
  pannable.** A game whose whole arena fits the frame (raid, hive, gridlock) removes the panel —
  markup, CSS, the `core.zoomAt/setZoom/attachMinimap` wiring, and the ids from the test list —
  rather than hiding it."
- Why blocking: the item names the `core.zoomAt`/`setZoom` wiring as something to remove, and it
  is present and live. The concrete consequence: on a board that is a fixed 1400×1400 square which
  always fits the frame (`src/lane/sim_types.nim:103-106`, `MapWidth = MapHeight = 1400`), a
  spectator's ctrl-wheel, trackpad pinch or pointer drag will zoom and pan the arena with **no
  visible control** (the zoom bar and its `#zoom-read` readout were removed), and the only ways back
  are the undiscoverable `0` key and a dblclick. The design note contradicts the code here too:
  L1420-1421 states "`broadcast_core.js`'s zoom/pan/minimap code stays in the file, verbatim, simply
  **never driven**" — the page drives it. *(category: static-viewer)*

---

## Non-blocking

### N1 — `ci.yml`'s viewer smoke does not pass `--soak 12`, so the frozen-playback check never runs
- Where: `.github/workflows/ci.yml:328-332`.
- Observed: the step runs `node tools/ci/viewer_smoke.mjs --bundle … --replay … --timeout 90
  --strict-text-bounds`. `tools/ci/viewer_smoke.mjs:158` defaults `soak: 0`, and `:535`
  (`if (loaded && args.soak > 0)`) makes the whole soak block a no-op at 0. The CI log for run
  33203089677 confirms: the step printed no `soak:` line.
- Design note: L1911-1913 pins the command as
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/<name>.replay
  --timeout 90 --soak 12 --strict-text-bounds`, and L1914-1916 explains that the 1440-tick fixture is
  60 s long precisely so "a 12 s soak cannot end the replay".
- Not blocking because: checklist item 13 requires the `Load the bundle in a real browser` step to
  exist, to run and to be green (it is — see "Traced and consistent"), and item 15 requires
  `--strict-text-bounds` (present). `--soak` is named only by the design note. The repo's `ci.yml`
  also matches `/workspace/coworld-builder/templates/ci.yml` verbatim on this step, so the omission
  is inherited from the template rather than introduced here.

### N2 — the board never draws the speech-bubble band the design specifies; `a57.bubbles` is emitted and never consumed
- Where: `src/lane/broadcast.nim:264-269` and `:300` build `a57.bubbles`; nothing reads it.
- Observed: I grepped the whole repo for `bubbles` — it appears only in `broadcast.nim` (producer)
  and in `tools/ci/renderer_fixture.html:121` (which puts one in its synthetic state). It is absent
  from `client/replay_broadcast.html`, so the appended game block never renders it, and `global.nim`
  has no bubble drawing at all (the only `Bubble` tokens in it are `shoutBubbleZoomFor` at `:46`, an
  inherited helper, and a comment at `:9`). A stance's `say` reaches the spectator only as a feed
  row: `broadcast.nim:100-117` synthesises a `say` event, and
  `client/replay_broadcast.html:2924-2932` renders it into `#killfeed`.
- Design note: §Viewer Readouts 6 (L1514-1519) specifies "at most **three** at a time … drawn for
  2.5 s in a **reserved band across the top of the board** (`row ∈ [0, 2)` of the 35-tile board) …
  The band is sized from `MaxSayRunes = 48` measured in `data/font.ttf` at the current `--hudscale`".
- Not blocking because: checklist item 15's "reserved band" clause applies to text *laid out relative
  to another element*. No such text is drawn — the `say` lives in a flow-layout DOM feed row, and the
  only board-anchored text (the stance chip) is baked into a fixed-size image (see T12). The
  worst-case renderer fixture item 15 requires is present and gated (see T14).

### N3 — the sim resolves contacts by end-position box overlap, not by the swept earliest-crossing resolver the design specifies, and its priority order differs
- Where: `src/lane/sim.nim:346-454` (`stepBall`), `:503-585` (`stepBolts`), `:317-344`
  (`resolveChaserContacts`); the unused helpers at `src/lane/grid.nim:169-177`.
- Observed: `stepBall` resolves X then Y against wall/brick tiles by end position
  (`sim.nim:377-430`), then tests the paddle (`:439-449`). `stepBolts` resolves, in order: tile
  contacts (bunker `:521-532`, wall `:533-536`), then friendly-bolt-vs-marcher/saucer
  (`:540-570`), then hostile-bolt-vs-avatar (`:573-585`). `grid.crossedAxis` (`grid.nim:174-177`)
  and `grid.boxHitsTile` (`:169-172`) are referenced only from `tests/test_physics.nim:40,43` —
  `boxHitsTile` has no caller at all.
- Design note: §Resolution order 3.6 (L480-488) specifies each sprite "resolves the **earliest**
  axis crossing along its swept segment against, in this priority order on an exact tie: **(a) the
  avatar box**, **(b) destructible tiles** …, **(c) other sprites** …, **(d) wall tiles**, **(e) the
  lane bounds**. Crossing times are compared by integer cross-multiplication in `int64`".
- Inferred consequence: on a tick where a hostile bolt's end position overlaps both a bunker tile
  and the avatar box, the shipped code consumes the bolt on the bunker (`sim.nim:521-532`, which
  `continue`s before the avatar test at `:573`), where the design gives the avatar box priority. The
  design's own justification for end-position testing being sufficient is the no-tunnelling bound,
  which is asserted directly (`tests/test_physics.nim:8-19`: `max(BallSpeedMax, BoltSpeedFriendly)
  = 4000 < HalfTileU + BallHalf = 9000`) and cross-checked over 50 000 randomised states
  (`:21-50`). Not a checklist item.

### N4 — `MarcherCols` is `[5,6,7,8,9,10,11,12]`, not the design's `1,3,5,7,9,11,13,15`
- Where: `src/lane/maps.nim:92-101`.
- Observed: the constant is `MarcherCols*: array[8, int] = [5, 6, 7, 8, 9, 10, 11, 12]`, with a
  10-line comment giving the reason: the design's spread "is FLUSH against the note's own 'would
  leave columns 1..15' bounds rule, so the body would step DOWN on every single march tick and
  breach row 13 in 160 ticks — a wave nothing could clear."
- Design note: §`gallery` (L394-395) says "32 `Marcher`s in a 4 × 8 formation, rows 2–5, columns 1,
  3, 5, 7, 9, 11, 13, 15."
- Not blocking: not a checklist item; the deviation is documented in place and the wave's playability
  is pinned by `tests/test_baselines.nim:95-97` (`gallery` clears a wave on ≥3 of 20 seeds).

### N5 — `BaselineParams` ship at `panicTicks: 20, leadTicks: 10`, not the design's 28 / 14
- Where: `src/lane/baselines.nim:38-49`; the recorded sweep at `tools/ci/baseline_tuning.json`
  (`{"panicTicks": 20, "riskMilli": 500, "leadTicks": 10, "meanPoints": 1875, "screensCleared": 9,
  "seeds": 6, "roms": 3}` plus a 36-cell grid).
- Observed: `tests/test_tuning.nim:10-30` asserts the shipped defaults equal the recorded pick and
  that no swept cell beat it; `tools/tune_baselines.nim:26-28` defines the grid
  (`PanicGrid = [20, 28, 36, 44]`, `RiskGrid = [300, 500, 700]`, `LeadGrid = [10, 14, 20]`).
  The manifest's bundled-player description is consistent with the shipped value
  ("bail when a threat gets inside 20 ticks").
- Design note: §Scripted baselines (L905-908) names `panicTicks` (28) and `leadTicks` (14) but
  explicitly delegates the values to the sweep. Consistent with checklist item 7's "tuned with a grid
  harness, not guessed"; recorded only because the numbers differ from the note's illustration.

### N6 — the JS above the appended banner is edited (behind `A57_MODE`), which the design note says it is not
- Where: `client/replay_broadcast.html:1546` (`var A57_MODE = false;`), `:1608` (latch),
  `:1659`, `:1739`, `:1751`, `:1802`, `:1913-1914`, `:2158`, `:2205`, `:2214`, `:2266`, `:2274`,
  `:2632`; the banner's own admission at `:2652-2654`.
- Observed: 13 `A57_MODE` branch points in the inherited page (scorebug plate contents, endcard stat
  columns and verdict, the event switch's delegation to `window.Atari57Chrome.event`).
- Design note L1409-1410: "one `<style>` and one `<script>` block at the end of the file …
  **Nothing above them is rewritten**".
- Not blocking: checklist item 14's provenance test is on the **CSS** above the banner (verified
  clean — see B1's "What IS removed") and on the page not being a from-scratch rewrite (3058 lines
  against the starter's 4660, with the 1602-line reduction accounted for by the declared `#fpv` /
  `#povBadge` / `#viewpanel` removals — `528-833`, `2348-3466` and `4132-4244` of the starter's file).
  The banner comment documents the edits rather than concealing them.

### N7 — `broadcast_core.js` differs from the starter in two places, not one
- Where: `client/broadcast_core.js:49` (`window.LANE_WIRE` for `window.CTF_WIRE`) and `:268` (a
  comment path `src/lane/sim.nim` for `src/ctf/sim.nim`).
- Observed: `diff client/broadcast_core.js /workspace/starters/coworld-ctf/client/broadcast_core.js`
  returns exactly those two hunks. `tests/test_viewer.nim:205-211` restores **both** before comparing,
  so the test's own name ("differs … in the wire name alone") overstates slightly.
- Design note L957: "Verbatim apart from the one `window.CTF_WIRE` identifier."

### N8 — `flake.nix` / `flake.lock` were deleted although the design lists them as kept
- Where: commit `309a9b3` (`.caos-expr`, `flake.lock`, `flake.nix`, 376 deletions).
- Design note L960 lists `flake.nix`, `flake.lock` in the "Kept verbatim" build-wiring row.
- Not blocking: the canonical build is `Dockerfile` + nimby (`AGENTS.md` §Building), and CI does not
  reference nix.

### N9 — three items from the design's own test list are not implemented
- Where: `tests/test_engine.nim` (10 test procs) and `tests/test_server.nim` (7 test procs).
- Observed absences against design §Tests 7 (L1809-1818): no test for "a disconnected seat plays
  `arcader` and revives on reconnect", none for "a never-connecting seat is reported to
  `COGAME_PLAYER_FAILURE_URI`, logged loudly, and the run still reaches a normal ending", and none
  for "a registration that arrives before its player index exists is **held and applied**". The
  server code for all three exists and I read it (`src/lane/server.nim:609-620` no-show →
  `declarePlayerFailure` + `forceStart`; `:600-607` a drop keeps the lane; `:704-711` an
  unappliable registration is held and re-inserted at `:737-738`), but nothing exercises it.
  Design §Tests 10 also lists "at least one `pickup`, one `life_lost` and one `screen_clear`" in the
  recorded stream; `tests/test_replay.nim:157-192` counts only `register` / `stance` / `result`
  records — those three are derived broadcast events, not chat records, so they are not in the chat
  stream the test walks.
- Not blocking: checklist item 1 forbids *loosening* tests during the run (none were — see T1); it
  does not require the design's full test list.

### N10 — `stepEvents` derives 8 of the design's 13 broadcast event kinds
- Where: `src/lane/broadcast.nim:58-124`.
- Observed: it emits `pickup`, `chain`, `life_lost`, `screen_clear`, `record`, `lane_over`, `say`,
  `phase` and `over`. It does not emit `chip`, `bunker`, `saucer`, `near_miss` or `turn_end`, which
  design §Record and event vocabulary B (L1340-1347) lists. Those kinds do exist on the tier-2 path
  (`src/lane/sim.nim:1015-1046`, `laneEventJson`) and in the `SimEventKind` enum
  (`src/lane/sim_types.nim:324-339`). The page's event switch still handles `near_miss` as a no-op
  (`client/replay_broadcast.html:2934-2937`). The **beat** set is exactly the design's five
  (`replays.nim:586-588`, `broadcast.nim` derivation, `test_viewer.nim:110`).

### N11 — the renderer fixture shrinks the font when a run exceeds its box, so the canvas gate cannot see horizontal overflow
- Where: `tools/ci/renderer_fixture.html:183-188`.
- Observed: `var natural = ctx.measureText(text).width; if (natural > box.width && natural > 0) {
  ctx.font = Math.max(1, size * (box.width / natural)) + 'px ' + …; }` before `ctx.fillText(text,
  box.left, box.top)`. A run wider than its box is therefore always drawn inside the box, so
  `canvas_text.outside` / `never_inside` can only ever catch a run whose *box* is anchored off-frame
  or below the canvas, not one that overflows its box.
- Mitigation observed in the same file: `:192-197` asserts directly on
  `node.scrollWidth > node.clientWidth + 2` (with an `ellipsis`/`auto`/`scroll` exemption), and
  `:266-272` asserts no `.plate-name` collapsed to an empty string or a bare `…`. The step is green
  with `canvas text: 112 drawn, 0 never inside` (CI run 33203089677).

### N12 — the inter-batch floor is a plain `os.sleep`, and the wall-clock stop can overshoot by up to one turn
- Where: `src/lane/decide.nim:165-171` (`sleep(min(sim.config.turnSpacingMs,
  sim.config.turnSpacingMs - since))`) and `src/lane/server.nim:587-596`.
- Observed: the sleep is bounded by `turnSpacingMs` (12 000 ms in every variant), but it is not
  interruptible, and `engine.turn` is called synchronously from the tick loop
  (`server.nim:770-771`), so the wall-clock check at the top of the loop (`:587`) cannot fire while a
  turn is in flight.
- Design note L665-666 calls this floor "a bounded, stop-interruptible `sleep`".
- Inferred arithmetic, which is why this is not blocking: worst case the stop fires
  `turnSpacingMs + turnBudgetMs = 28 s` late → 688 s, plus the artifact block, then a bounded 20 s
  shutdown grace (`server.nim:98`, `:934-937`) → ≈ 708 s against the checklist's 720 s (60 % of
  `episode_timeout_minutes: 20`). Scoring itself happens at `finishGame` before the grace, so the
  "settles and scores" window is ≈ 690 s. Margin is real but thin.

### N13 — the wall-clock stop is gated on `phase == Playing`, so a pathological lobby is not covered by it
- Where: `src/lane/server.nim:587-589` (`if laneMode and not game.stopped and game.phase == Playing
  and (getMonoTime() - episodeStart).inSeconds.int >= config.wallClockBudgetSeconds`).
- Observed: `config.lobbyJoinTimeoutTicks` is clamped to `[0, 20 000]`
  (`src/lane/sim_config.nim:193`), i.e. up to 833 s of lobby at 24 Hz, which would exceed 720 s
  without the stop ever being reachable. Every shipped config sets 2880 ticks = 120 s (all three
  variants; the cert fixture sets 720 = 30 s), so the path is not reachable from the manifest.
- Untested: this would need a hand-built config to reach; I did not run it.

### N14 — the scorebug plate shows the real policy name where the design says it shows the colour alias
- Where: `client/replay_broadcast.html:1763` (plate is built with `team.toUpperCase()` as the initial
  caption) and `:1800` (`setName('name-' + team, teamName(s, team, team.toUpperCase()))`, which
  resolves through `chrome_common`'s roster lookup to the real name, falling back to the alias).
- Observed in CI: the smoke's scorebug transcript reads `SCR 1 P1 SCORE 9.100 10 PTS … P3 … P2 … P4`
  — the fixture's roster names, not `RED`/`GREEN`/`BLUE`/`YELLOW`.
- Design note §Legible at 360 px (L1572-1573): "At 360 px each plate shows the colour alias, the
  score and the lives pips; … the four policy names live in the endcard and in each roster row's
  `title`."
- Not blocking, and arguably checklist-favourable: item 4 asks the viewer to map aliases to real
  player names for non-baseline seats, which this does.

---

## Traced and consistent

- **T1 — CI green, no test loosened** (item 1). `gh run list -R Metta-AI/cogame-atari-57 --branch
  main -w ci.yml`: run **33203089677**, conclusion **success**, `headSha`
  `309a9b3438318ae8aa36d52c55db3d4fba1040d8` — the reviewed sha. All three jobs green
  (`test`, `docker-smoke`, `wasm-viewer`), every step `success`, none skipped or
  `continue-on-error`. `git log -p -- tests/` in the checkout shows exactly one commit touching
  `tests/` (`d31e0f7`), 20 files, **+3493 insertions, 0 deletions**; nothing was widened, skipped or
  removed. `grep -rn "skip\|xfail\|when false" tests/*.nim` returns only `skipLulls` and one comment.
  (Note for the coordinator: main has since moved to a fourth commit, "drop three dead declarations
  the fork left behind", whose run 33205174439 was still queued when I read it. That is outside this
  review's sha.)
- **T2 — replay re-derivation, frame by frame** (item 2). The server writes one hash per tick after
  the step (`src/lane/server.nim:817`, `replayWriter.writeHash(uint32(game.tickCount),
  game.gameHash())`). Playback re-steps the *recorded action bytes* through the same
  `sim.step` (`src/lane/replays.nim:445-452`, `stepReplay` = `applyReplayEvents` → `replayInputs` →
  `sim.step(inputs)` → `checkReplayHash`) and `checkReplayHash` (`:412-443`) compares
  `sim.gameHash()` against the recorded hash for **that tick**, flagging `hashMismatchTick` on the
  first divergence. The viewer draws from that same re-simulated `SimServer`:
  `replay-viewer/atari57_replay.nim:53-56` (`renderCurrent` → `game.buildReplayViewerPacket(replay,
  …)`) and `:105-121` (`atari57_frame` → `replay.advanceReplayFrame(game, …)` → `renderCurrent`) —
  there is no parallel recording anywhere in the path. Asserted by `tests/test_replay.nim:87-97`
  (`resimulate`) at `:99-115` for all three ROMs and `:118-152` for **all four end reasons**
  (`full_time`, `all_lanes_over`, `wall_clock` via `stopAtTick`, `sim_fault` via `faultAtTick`).
- **T3 — the `stopped` record is applied by one proc on both sides**. `src/lane/sim.nim:1005-1013`
  (`recordStop`) sets the hashed `stopped`/`stoppedTick` fields (mixed in at
  `src/lane/sim_state.nim:92-93`). The live server calls it at `server.nim:594` immediately after
  writing `stoppedRecord(game.tickCount)` at `:592-593`; playback calls the same proc from
  `sim.applyControlRecord` (`sim.nim:1064-1066`), reached from `replays.nim:379-380`.
- **T4 — static viewer, no pod viewer** (item 3). `coworld_manifest_template.json` declares
  `game.replay_viewer = {"bundle": "static-replay-viewer"}` and nothing else.
  `tools/build_replay_viewer.sh` is committed `100755` (`git ls-files -s`) and is the starter's
  script with only `image_tag` and the `docker cp` source path changed (2-hunk diff against the
  starter). `ci.yml:239-250` asserts the file exists **and** is `test -x`, then invokes it by path.
  `coworld-release.yml:186-211` fails the release unless `coworld certify` prints
  `Replay liveness: skipped (static replay bundle declared`, with the message "a pod-served
  /client/replay viewer is not acceptable". The bundle's only network call is the replay URL
  (`replay-viewer/static_replay_worker.js:113-116`, `fetch(message.replayUrl, {credentials:'omit',
  mode:'cors'})`) — no other `fetch`/`XMLHttpRequest`/`WebSocket` exists in either JS file.
  The game pod does still serve `/client/replay` (`src/lane/server.nim:334-344`) — that is the
  inherited **live-spectator** page, present in the starter at `src/ctf/server.nim:825-826` and
  listed as kept by design L1062; it is not declared as a replay viewer anywhere in the manifest.
- **T5 — both name spaces** (item 4). In-game: `src/lane/sim_types.nim:142`
  (`LaneAliases = ["RED","BLUE","GREEN","YELLOW"]`), `laneAlias` at `:392-394`; the player stream
  carries only its own lane and no labels (`src/lane/global.nim:952-1014`), `showPlayerLabels`
  defaults false (`sim_config.nim:30`). Spectator side: `src/lane/roster.nim:81-87` (`playerName`),
  `broadcast.nim:146-171` (`rosterJson` — "the one place a REAL policy name appears in the chrome
  stream"), `roster.nim:124` (`results.names`), `sim_config.nim:249-251` (replay config
  `players[].name`). Pinned by `tests/test_isolation.nim:121-152` (200 randomised states: the
  composed LLM message carries one lane plus four `{alias, score, lives, screen}` rows) and
  `tests/test_locality.nim:94-126`.
- **T6 — every wait is bounded** (item 5). LLM: `decide.nim:178-183` (per-turn monotonic
  `turnBudgetMs` checked before each attempt), `:184-202` (`attempt1Ms` / `retryMs` handed to
  `makeRequests` as whole seconds), `:175` (`while open.len > 0 and attempt < 2`), `:165-171` (the
  spacing sleep, bounded by `turnSpacingMs`). Engine stop: `server.nim:587-596` at 660 s. Lobby:
  `sim.nim:936-938` + `server.nim:609-620` (`lobbyJoinTimeoutTicks`, 2880 ticks = 120 s, then
  `forceStart`). Frame limiter: `server.nim:429-441` (bounded by `frameDuration`, 1–2 ms sleeps).
  Shutdown: `server.nim:934-937` (20 s). Player: `src/atari57_player.nim:26-31` (240 × 500 ms dial,
  6 reconnects). Autopilot floods: `observation.nim:81` and `:126` (`visited < BfsNodeCap`, 300),
  `control.nim:103` (`for _ in 0 ..< 240`). `tests/test_determinism.nim:141-146` greps every sim
  module for a `while true`. `tests/test_engine.nim:187-218` proves a hung provider is bounded
  (measured 2022 ms in the CI log) and every seat still gets a legal stance.
- **T7 — `num_agents`** (item 6). `num_agents: 4` inside `game_config` for variants `chomper`,
  `brickfall`, `gallery` **and** in `certification.game_config`; `certification.players` has 4
  entries and `certification.game_config.players` has 4. Absent at every variant top level.
  `tools/ci/docker_smoke.sh:110-151` enforces all four invariants — present (`:110-118`), a positive
  integer (`:119-125`), `len(certification.players) == it` (`:129-134`), `len(game_config.players)
  == it` (`:135-140`) — plus the independent `SMOKE_SEATS` cross-check (`:146-151`), every one
  exiting with a `SEAT-COUNT FAIL:` prefix. **`grep -n "SEAT-COUNT" ` over the full CI log for run
  33203089677 returns nothing**; the smoke printed `game=atari-57 seats=4 …` and
  `smoke OK: seats=4 results=643B replay=35763B reason=complete`. Pinned by
  `tests/test_manifest.nim:11-33`.
- **T8 — scripted baselines play full legal episodes** (item 7). `tests/test_determinism.nim:99-121`
  runs a four-`arcader` episode per ROM against `tests/data/golden_hashes.json`, which pins
  `reason: "complete"` for all three (`chomper` 2644 ticks `all_lanes_over`, `brickfall` 2880
  `full_time`, `gallery` 1440 `all_lanes_over`) and asserts `run.reason`/`run.endRule` match.
  `tests/test_baselines.nim:20-63` checks 500 states × 2 baselines × 3 ROMs: `risk ∈ [0,1000]`,
  `lead_ticks ∈ [0,48]`, `cmd <= 14`, `dir ∈ 0..4`, `act ∈ 0..2`, no up/down byte on a rail, no fire
  byte without `fireEnabled`, no brake byte without `brakeEnabled`. Tuning by grid harness:
  `tools/tune_baselines.nim` (36 cells over 6 seeds × 3 ROMs), recorded in
  `tools/ci/baseline_tuning.json`, re-asserted by `tests/test_tuning.nim:10-30`.
- **T9 — LLM reply handling** (item 8). One parallel batch per turn: `decide.nim:186-202` builds
  every open seat's request into a single `RequestBatch` and issues
  `engine.client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`; no sequential path exists.
  Tolerant parse: `stances.nim:154-193` (`extractJsonObject`, balanced-brace scan, fence- and
  prose-tolerant, first-brace..last-brace fallback) feeding `parseLaneStance` (`:214-272`), which
  repairs per field — synonyms at `:107-152`, percentage `risk` at `:249-252`, `lead_ticks` clamp at
  `:260`, and raises only when `usable == 0` (`:271-272`). Exactly one retry: `while open.len > 0
  and attempt < 2` (`:175`), with the throttle fast-fail at `:234-240`. Fallback recorded with a
  cause: `:243-258`, cause ∈ `{no_credentials, budget_guard, throttled, parse_error}` plus
  `{timeout, transport_error}` from `:220-227`, and the phase-60 grep phrase `falling back` is
  echoed at `:257`. Counted into results via `sim.applyControlRecord` → `fallbackTurns`
  (`sim.nim:1081-1082`) → `results.fallbackTurns` (`roster.nim:143`). Pinned by
  `tests/test_engine.nim:95-145` (four intersecting in-flight windows against a real local
  endpoint), `:221-244` (a 429 produces exactly 4 requests, no retry), `:246-273` (an unparseable
  reply produces exactly 8 requests and both attempts recorded), `:296-318` (no credentials ⇒ four
  instant recorded fallbacks in < 2 s).
- **T10 — rune-safe truncation** (item 9). `stances.nim:79-86` (`truncateRunes` via `runeLen` /
  `runeSubStr`), `:88-100` (`sanitizeSay` — rune cut **first**, printable-ASCII filter second),
  `:102-105` (`sanitizeNote`), `:301-316` (`boundedStanceRecord` shrinks the `note`, never the
  serialized string), `:329` (`policy` ≤ 48), `:343` (`detail` ≤ 200), `llm.nim:183/191/199/208`
  (provider bodies truncated on runes before they become `fallback.detail`),
  `llm.nim:277` (`prompt` ≤ 4000 at the transport) and `server.nim:718`. Caps in
  `sim_types.nim:57-65`. Test: `tests/test_stances.nim:93-125` feeds `"a"×47 + 😀😀` (49 runes),
  asserts `truncateRunes(say, 48).runeLen == 48`, `validateUtf8() == -1`, and that the boundary rune
  survives whole; then round-trips a 160-rune all-emoji note through `boundedStanceRecord` →
  `parseJson`. `tests/test_replay.nim:203-238` additionally forces a non-ASCII `say` and a non-ASCII
  policy label into a real recorded episode and asserts `tools/replay_summary.py` output parses
  under a strict UTF-8 parser.
- **T11 — manifest validates** (item 10). `game.docs.readme = {"type":"text","value":…}` (5286
  chars) and `game.docs.pages` = three typed objects (`rules.md` 10317, `protocol.md` 7608,
  `stances.md` 6535 chars), each with `id`/`title`/`content{type,value}`. `game.protocols` carries
  **both** `player` and `global`, each `{"type":"text","value":…}`. `results_schema`:
  `additionalProperties: false`, 24 properties matching `roster.resultsKeys()`
  (`src/lane/roster.nim:172-178`), every per-seat array `minItems: 4, maxItems: 4`, `reason` enum
  `[complete, deadline, fault]`, `endRule` enum `[all_lanes_over, full_time, wall_clock, sim_fault,
  host_error]`, `rom` enum `[chomper, brickfall, gallery]`. `config_schema`:
  `additionalProperties: false`, `required: ["tokens","players"]`, every array property carries
  `minItems`/`maxItems` (`tokens` 1..4, `players` 1..4, `slots` 0..4). Top-level `tags` has 5
  entries; `game.tags` absent; `game.description` present; no top-level `version`, no
  `game.display_name`. All pinned by `tests/test_manifest.nim:65-237`.
- **T12 — legible at 360 px** (item 11). `client/replay_broadcast.html:2678-2683`:
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`.
  `:2813-2816`: `@media (max-width: 640px) { .plate .lives-label { display: none } .plate .a57-pts
  { display: none } }`. `.tiny` rules at `:2808-2810`. `relayout()`'s clamp is the starter's:
  `:2606` `Math.max(0.5, Math.min(1.6, boardW / 760))` and `:2608`
  `stage.classList.toggle('tiny', boardW <= 620)`. Asserted by `tests/test_viewer.nim:153-170` and
  exercised at 360/620/1280 px by `tools/ci/renderer_fixture.html:59`, which also asserts no plate
  name collapsed (`:266-272`). The only board-anchored text is the stance chip, baked into a
  fixed-size `newImage(7 * tile div 2, tile)` (`src/lane/global.nim:482-488`) from the closed
  `mode`/`zone` enums — a reserved band by construction.
- **T13 — release order and scaffold** (item 12). `coworld-release.yml` step order:
  `Build the Coworld manifest` (:159) → `Certify locally` (:173, with `--timeout-seconds 300`) →
  `Upload the policies` (:216, comment: "BEFORE upload-coworld") → `Upload the Coworld` (:314) →
  `Wait for the uploaded version to become canonical` (:352) → `Put the Coworld secret` (:410).
  All three workflows present. `tools/ci/docker_smoke.sh` committed `100755`.
  `tools/ci/policies.json` defines four policies: two `PLAYER_PROMPT` champions
  (`atari-57-highroller` :3-9, `atari-57-onecredit` :10-18) and two scripted fillers
  (`atari-57-arcader` :19-26 `PLAYER_SCRIPTED=arcader`, `atari-57-hoover` :27-34
  `PLAYER_SCRIPTED=hoover`); champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`
  at `:17`. The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named
  files returns nothing. The four surviving angle-bracket names are exactly the documented residue:
  `<cow_id>`/`<sha>` at `ci.yml:216`, `<run_id>` at `coworld-release.yml:21` and
  `coworld-submit.yml:17`, `<name>:vN` at `coworld-submit.yml:31`.
- **T14 — the viewer executes** (item 13). `wasm-viewer` declares `needs: docker-smoke`
  (`ci.yml:226`) and its `Load the bundle in a real browser` step (`:307-332`) ran and passed in run
  33203089677, printing `{"loaded":true,"ms":791,"clock":"1:00 TIME LEFT CHOMPER · PAR 2600 · TURN
  1/12", …}`. It is not `continue-on-error` and is not commented out. Markers: `data-replay-loaded`
  is set from the shell's own worker-`loaded` handler on the first drawn frame
  (`static_replay.js:158-162`, reached after `ingestPacket()` at
  `static_replay_worker.js:126-131`), `data-replay-error` from `showFailure`
  (`static_replay.js:19-20`), `data-replay-mismatch-tick` at `:30-33`. Playback opens at the game
  start: `replay_runtime.nim:38-52` walks the lobby to `Playing`, sets
  `player.startTick = sim.gameStartTick`, then `seekReplay(sim, replayStartTick())`;
  `replays.nim:249-252` clamps `replayStartTick` into `[0, replayMaxTick]`, `beginSeek` clamps
  **every** seek to `clamp(tick, replayStartTick(), replayMaxTick())` (`:706`), the loop restart
  goes to `replayStartTick()` (`:830`, `:849`), and the scrubber axis is the same value
  (`buildReplayViewerPacket` passes `replay.replayStartTick()` as `st`,
  `replay_runtime.nim:133` → `broadcast.nim:279`). The CI scrub probes confirm the axis moves:
  `0%="1:00 TIME LEFT" 50%="0:59" 100%="0:00"`. Link flags and bootstrap are the **same** starter:
  `replay-viewer/config.nims:42-55` has **no** `MODULARIZE` and **no** `EXPORT_NAME`, and
  `static_replay_worker.js:8` `var Module = {};` + `:188` `Module.onRuntimeInitialized` + `:239`
  `importScripts('./wire_constants.js', './broadcast_core.js', './atari57_replay.js')` is the
  matching non-modularized bootstrap. `tests/test_viewer.nim:226-249` pins the pair.
- **T15 — every drawn string fits its frame** (item 15). The main smoke reports
  `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` — `total: 0`, which the checklist
  itself says "means the check covered nothing" (this viewer renders in an OffscreenCanvas Worker,
  `static_replay.js:87-93`, `static_replay_worker.js`). The evidence is therefore the fixture:
  `ci.yml:346-370` runs `tools/ci/renderer_fixture.html` through
  `viewer_smoke.mjs --url … --strict-text-bounds`, and it reported
  `canvas text: 112 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.
  The fixture loads the **real shipped bundle** in an iframe (`renderer_fixture.html:38`,
  `src="./index.html?embed=1"`) and shims only the frame source (`:229`, `win.__a57TestFrame`, which
  is the page's own `onFrame` — `client/replay_broadcast.html:2642`), drives full-cap strings on all
  four seats (`:49-52`, `:100-105`), fires the record banner and all four stance chips (`:107-114`),
  runs at 360/620/1280 px plus a game-over frame (`:59`, `:241-250`), and self-checks its own
  string lengths against the caps (`:68-71`, including the "not near the cap" guard that stops a
  quietly shortened remark from passing).
- **T16 — resolution rules**. Tick order matches design §Resolution: turn boundary
  (`server.nim:754-785`), autopilot compile in lane order 0→3 (`:786-792`), `stepLane` per lane in
  order 0→3 (`sim.nim:1112-1132`), score fold inside `stepLane` (`:902-905`), hash
  (`server.nim:817`), end checks in the design's order — `stopped` → `deadline/wall_clock`, then
  `minTicks && allLanesOver` → `complete/all_lanes_over`, then `maxTicks` → `complete/full_time`
  (`sim.nim:1136-1143`) — with `fault/sim_fault` and `fault/host_error` from the guard
  (`sim.nim:628-649`, caught at `server.nim:806-815`). Action byte: one decoder,
  `sim_types.nim:402-414`, `dir = cmd mod 5`, `act = cmd div 5`, `cmd >= 15 → (0,0)`, used by both
  the server path (`sim.nim:681`) and the replay path (same `stepLane`; `replays.nim:397-410`
  returns the raw recorded byte unchanged). `tests/test_physics.nim:94-108` walks all 256 values.
- **T17 — replay writer**. `COWLDA57` magic and format version at `replays.nim:157-168`
  (`Atari57ReplaySpec`, `gameName = "atari-57"`, `gameVersion = "1"` from `sim_types.nim:23-30`);
  embedded config JSON at `sim_config.nim:237-337` (seed, resolved preset, the loaded map's 17 rows
  verbatim, its sha256, all three map hashes, the whole geometry and point tables, real
  `players[].name`, `slots[].alias`); change-only action-byte writes
  (`replays.nim:176-197`, called at `server.nim:791-792`); `register` (`server.nim:728-733`),
  `stance` (`:778-780`), `fallback`/`budget_guard` (`:772-773`), `stopped` (`:592-593`), `result`
  (`:911`); one hash per tick (`:817`). Verified by `tests/test_replay.nim:157-201` (exactly 4
  `register`, ≥4 `stance` each ≤ 600 runes with `note` ≤ 160 and `say` ≤ 48, exactly 1 `result`,
  legal `reason`/`endRule`/`rom`, and a config carrying `seed`/`rom`/`parScore`/`preset`/`map`).
- **T18 — isolation and determinism**. `stepLane` signature takes no `SimServer`
  (`sim.nim:651-657`), `sim.nim` never imports `observation` (grep-asserted at
  `tests/test_isolation.nim:98-120`), and the only cross-lane read is
  `observation.scoreboardJson` (`observation.nim:316-327`), composed outside the sim.
  `tests/test_isolation.nim:24-97` covers all three halves (a rewritten neighbour stream cannot move
  you; a one-lane sim reproduces the four-lane trajectory; four lanes on one stream finish
  identical). No float / no `rand(` / no `-ffast-math` / no `while true` in the eight sim modules,
  grep-asserted at `tests/test_determinism.nim:123-147`. One RNG helper (`grid.nim:57-66`,
  `drawInt` on `nextRng`'s `uint64` domain), `rngDraws` hashed (`sim_state.nim:85`), four identical
  streams (`test_determinism.nim:149-161`).
- **T19 — chrome provenance**. `client/chrome_common.js` is **byte-identical** to
  `/workspace/starters/coworld-ctf/client/chrome_common.js` (verified by `sha256sum` on both;
  pinned at `tests/test_viewer.nim:21-22` as `7ace7287…`). `client/replay_broadcast.html` carries
  the banner `atari-57 additions to the inherited coworld-ctf chrome` at `:2649` with one `<style>`
  and one `<script>` appended below it; all 47 "kept" starter ids are present
  (`tests/test_viewer.nim:64-81`, re-verified by grep) and all 19 "removed" ids are absent.
  Transport rules: (a) `relayout()` at `:2571-2616` sets `--hudscale`, `--topband` and `--band` on
  `document.documentElement` (`var root = document.documentElement`, `:2585`); (b) the game block's
  only overlay, `#a57-legend`, rides `bottom: calc(var(--band, 0px) + 8 * var(--u))` (`:2745`);
  (c) `#endcard { bottom: var(--band, 0px) }` (`:741`), shown with `#endcard.on` (`:752`, added at
  `:2237`) and removed on every frame whose phase is not `gameover` (`:1656`) — which is every seek
  off the end; (d) beats are `<button class="beat-marker <kind>">` with `title` + `aria-label` and a
  click that seeks (`:2836-2857`, `CTX.send('s:' + tick)`), with a CSS rule for each of the five
  kinds the sim emits (`:2765-2787`) and no other kind emitted by the game block.

---

## Could not determine

- **Whether checklist 14's `#viewpanel` bullet is meant to reach the page's keyboard/wheel/pinch/drag
  zoom handlers, or only the panel widget itself.** The facts in B1 are certain (markup, CSS and ids
  removed; `core.zoomAt`/`setZoom`/`panBy`/`resetView` still wired at nine call sites; `attachMinimap`
  unreachable). What would settle it: the judge's reading of the bullet, or a screenshot of the
  hosted embed showing whether a spectator can in fact pan the board off-frame.
- **Whether playback opens at the game start on a replay whose `gameStart` is LATE.** Checklist 13
  explicitly says "the CI replay's 1-tick lobby cannot show this". The CI replay's lobby is short
  (`startWaitTicks` defaults to 48 and the cert fixture does not override it), so the browser
  evidence does not exercise a long lobby. The code path is correct by construction as far as I can
  read it (T14), and the lobby walk is bounded by the recorded hash count
  (`replay_runtime.nim:38-42`). What would settle it: a replay recorded with a large
  `lobbyJoinTimeoutTicks` and no joining seats, loaded through `viewer_smoke.mjs`, with the 0 %
  scrub probe reading the game-start tick rather than tick 0.
- **The real wall-clock margin under a slow hosted provider.** N12's 708 s figure is arithmetic from
  the constants (660 s stop + up to 28 s of in-flight turn + 20 s grace) against the 720 s budget; I
  did not run a hosted episode. What would settle it: a phase-60 episode log with the elapsed time
  from container start to `results:`.
- **Whether `never_inside == 0` on the fixture would still hold for a genuinely overflowing run.**
  N11 shows the fixture rescales the font to the measured box before drawing, so the canvas gate
  cannot see horizontal overflow; the direct `scrollWidth > clientWidth` assertion
  (`renderer_fixture.html:192-197`) covers that case instead. What would settle it: deliberately
  shrinking a plate's `min-width` and confirming the fixture goes red.
