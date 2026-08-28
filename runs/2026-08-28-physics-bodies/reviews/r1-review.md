# r1 review — physics-bodies

Range: `coworld-ctf@e356bdd` (starter, read-only mount) .. `Metta-AI/cogame-physics-bodies@f6976bc5430d3da830a65d87a9bb3fad4a4cc084` (main; 3 commits: `c573490`, `b9008e6`, `f6976bc`)
Files read: 58 (all of `src/bodies/*.nim`, `src/physics_bodies*.nim`, `replay-viewer/*`, `client/*.js`, `client/replay_broadcast.html`, all 16 `tests/*.nim`, `tools/ci/*`, `tools/build_replay_viewer.sh`, `tools/build_manifest.py` output, `coworld_manifest_template.json`, all three workflows, `Dockerfile*`, `compose.yaml`, plus the starter's counterparts for diffing)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision rider)

Evidence conventions: **observed** = I read the code/log line quoted; **inferred** = I reasoned from
code I read; **untested** = would need a run to settle. CI evidence is cited by run/job id.

---

## Blocking

**None.** No finding below falsifies a named checklist item. Item-by-item, from the tree and from
cited CI evidence:

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | CI green, no test loosened | pass | run `33168835069` on `main` at `f6976bc`, conclusion **success** (`gh run list -R Metta-AI/cogame-physics-bodies --branch main -w ci.yml`); jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓. `git log -p -- tests/` for this run shows two post-fork test commits, both purely additive: `b9008e6` (+44/−1, adds `stripComments` and an id-presence requirement to `tests/test_viewer.nim`) and `f6976bc` (+59/−1, adds a sprite-scale assertion to `tests/test_observation.nim`). No deleted assertion, no widened tolerance, no skip added, no test file removed. |
| 2 | Replay re-derivation | pass | `src/bodies/replays.nim:297-307` (`stepReplay` = apply recorded events → `sim.step(replay.masks)` → `checkReplayHash`), `:266-295` (per-tick hash compare); the viewer's display is built from that same re-derived `sim` (`src/bodies/replay_runtime.nim:74-106`). Asserted by `tests/test_replay.nim:15-27,41-48,58-60,115-119,158-161`. |
| 3 | Static viewer | pass | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}` (observed via `python3 -c` dump); `tools/build_replay_viewer.sh` present and mode `100755`; wired as the hook in `.github/workflows/ci.yml` (`Build the static replay viewer bundle`) and asserted `os.X_OK` before use. No `/client/replay` declaration anywhere in the manifest. The bundle fetches only its own assets + the replay file. |
| 4 | Both name spaces | pass | `src/bodies/sim_types.nim:145,340-343` (`BUG-1`/`BUG-2` only), `src/bodies/baselines.nim:136-172` (observation carries `alias` only), `src/bodies/broadcast.nim:190-215` (`roster[].name` = real policy name, spectator side), `src/bodies/roster.nim:146-149`. Asserted by `tests/test_observation.nim`. |
| 5 | Degrade-never-hang | pass | every wait bounded — see “Traced and consistent → waits”. Wall-clock stop at `src/bodies/server.nim:617-630` (660 s default, `sim_config.nim:108` clamps to ≤720). Worst observed settle ≈660 s + 20 s grace ≈680 s < 720 s. |
| 6 | `num_agents` | pass | `num_agents: 2` in variant `default`, variant `blitz` and `certification.game_config`; `SMOKE_SEATS: "2"` in `ci.yml`. `grep -c "SEAT-COUNT FAIL" ` over the full `docker-smoke` job log (job `98840700969`) = **0**; the job printed `game=physics-bodies seats=2 …` and `smoke OK: seats=2 results=738B replay=60487B reason=complete`. |
| 7 | Scripted baseline plays full episodes legally | pass | `tests/test_baselines.nim:21-59` (bounded orders, 500 states × 2 baselines), `:62-89` (20-seed sweep, `faults == 0`), `tests/test_engine.nim:265-268` and `tests/test_replay.nim:37-40` assert `endReason == complete` on an all-scripted episode. Tuned by `tools/tune_baselines.nim`, pick recorded in `tools/ci/baseline_tuning.json`, re-asserted by `tests/test_tuning.nim`. |
| 8 | LLM reply handling | pass | tolerant parse `src/bodies/intents.nim:97-136,207-289`; retry-once `src/bodies/decide.nim:166` (`while open.len > 0 and attempt < 2`); throttle skips the retry `:220-226`; fallback recorded `:213-214,239-240` and counted `src/bodies/server.nim:784-786` → `results.fallbackTurns`. |
| 9 | Rune-safe truncation | pass | `src/bodies/intents.nim:68-95` (`truncateRunes` = `runeLen`/`runeSubStr`, the only shortening path); every string that reaches the replay goes through it (`intents.nim:288-289,342,354`, `llm.nim:168,176,184,193`). `tests/test_intents.nim:105-120` feeds a 4-byte emoji on the boundary and asserts the result is valid UTF-8; `tests/test_replay.nim:214-215` re-checks a recorded `say` with `validateUtf8`. |
| 10 | Manifest validates | pass | `game.docs = {readme:{type,value}, pages:[3 × {id,title,content:{type,value}}]}`; `game.protocols` has both `player` and `global` as `{type:"text",value}`. Asserted `tests/test_manifest.nim:155-174`. |
| 11 | Legible at 360 px | pass | `client/replay_broadcast.html:2718-2724` — `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`; labels hidden under 640 px at `:2827-2832`. Asserted `tests/test_viewer.nim:183-191`. CI's scorebug readout at load shows both plates non-collapsed. |
| 12 | Release order and scaffold | pass | `coworld-release.yml` step order: Build manifest (`:198`) → Certify locally (`:212`) → Upload the policies (`:255`) → Upload the Coworld (`:353`) → Put the Coworld secret (`:449`). Placeholder gate (`<slug>`/`<IMAGE>`/`<SEATS>` only) exits 0. `tools/ci/policies.json` has 4 policies: 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. `docker_smoke.sh` and `build_replay_viewer.sh` both `100755`. |
| 13 | Viewer executes | pass | `wasm-viewer` (job `98841130315`) `needs: docker-smoke`, no `continue-on-error`; step **“Load the bundle in a real browser”** ran and printed `{"loaded":true,"ms":1057,…}` and `soak: 12s of playback kept advancing ("0 / 1604" -> "240 / 1604" -> "288 / 1604")`. Markers: `replay-viewer/static_replay.js:161` sets `data-replay-loaded`, `:20` sets `data-replay-error`, `:32` `data-replay-mismatch-tick`. Playback opens at game start: `replay_runtime.nim:33-40` walks to `Playing`, sets `startTick = gameStartTick`, seeks there; every seek clamps to it (`replays.nim:480`, `:519`, `:522`, `:555`, `:570`). The recorded lobby is ~120 ticks (`helpers.nim`/server `startWaitTicks` 120), so this is exercised, not a 1-tick lobby. Link flags and bootstrap come from one starter: `replay-viewer/config.nims` has **no** `MODULARIZE`/`EXPORT_NAME` (verified by `grep`), and `static_replay_worker.js:8,188` is the `var Module = {}` + `Module.onRuntimeInitialized` form. |
| 14 | Chrome is the starter's | pass | `diff /workspace/starters/coworld-ctf/client/chrome_common.js client/chrome_common.js` → **byte-identical**. `client/replay_broadcast.html` is the starter's page with one appended block under the banner `PHYSICS-BODIES additions to the inherited coworld-ctf chrome` (`:2688`); the diff above the banner is removals only (`#povBadge`, `#fpv` + raycast/PiP machinery, `#viewpanel` + zoom/minimap wiring) plus copy changes — sections 1–5, the transport, scrubber, momentum, endcard and locker room are unmodified. Transport rules: (a) `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` (`:2633-2661`); (b) the only new overlay `#pb-legend` rides `bottom: calc(var(--band, 0px) + 8 * var(--u))` (`:2770`) inside `#chrome`; (c) `#endcard { bottom: var(--band, 0px) }` at `:743`, shown as `#endcard.on` (`:754`), taken down on every non-gameover frame (`:1656`); (d) beats are `<button class="beat-marker <kind>">` with `aria-label`/`title` that `CTX.send('s:' + tick)` (`:2861-2884`) and there is one CSS rule per emitted kind (`:2788-2812`). `#viewpanel` removed and the board (1920×1280) fits the frame. |
| 15 | Every drawn string fits its frame | see **N1** | The fixture and the flag exist and run; the *number* they gate is structurally 0. Not a falsification of the item as written — see N1. |
| rider | one parallel batch per turn | pass | `src/bodies/decide.nim:176-191` builds one `RequestBatch` for all open seats and issues `client.curl.makeRequests(batch, …)` once per attempt. `tests/test_engine.nim:151-179` asserts the two in-flight windows **intersect**; `:129-150` asserts `makeRequests(` appears exactly once and `.makeRequest(` never. |

---

## Non-blocking

### N1 — both `--strict-text-bounds` gates measured zero drawn strings; the LLM-text path is not covered by any CI check
- Where: CI run `33168835069`, job `98841130315`, steps “Load the bundle in a real browser” and “Drive
  the text path at full cap in the real bundle”; `tools/ci/renderer_fixture.html:197-229`;
  `tools/ci/viewer_smoke.mjs:139-141,601`; `src/bodies/global.nim:1049-1081`, `:517-545`.
- Observed: both steps printed
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
  `viewer_smoke.mjs` hooks `CanvasRenderingContext2D.prototype.fillText/strokeText` and documents at
  `:139-141` that “A viewer that draws into an OffscreenCanvas inside a worker reports total: 0 —
  which is itself the signal that this check did not cover it”; the gate at `:601` is
  `if (args.strictTextBounds && canvasText && canvasText.never_inside > 0)`, unreachable at `total: 0`.
  Two independent reasons the count is zero (both observed):
  (a) the real board is drawn in `static_replay_worker.js` on an OffscreenCanvas, outside the hook;
  (b) board text is never `fillText`ed at all — the speech band is rasterised in Nim by pixie
  (`global.nim:517-545 textPixels` → `:1067-1075 addSpriteChanged`) and blitted as sprite pixels.
  The renderer fixture does load the real `index.html` in three iframes at 360/620/1280 px and does
  self-check its 48-rune `say` / 160-rune `note` (`renderer_fixture.html:62-85,247-250`), but its shim
  replaces `window.BodiesStaticReplay.createCore` with a stub whose `start()` only pushes state JSON
  (`:197-229`) — no board is drawn, so only the DOM chrome (scorebug, feed rows, endcard) is exercised
  at full cap, and DOM text is not what `canvas_text` counts.
- Checklist item: 15. The item’s blocking condition is “a repo that draws model text and **has no such
  fixture**”. A fixture exists, runs in its own step, sets `data-replay-loaded`, self-checks its string
  lengths and carries `--strict-text-bounds`, so the item as written is satisfied. The item also says
  “`total: 0` means the check covered nothing … and is not evidence of anything”, so the item’s
  *substance* (LLM-authored text fits its frame) is **not verified by anything in this repo or its CI**.
- Why not blocking: the literal requirement is met; I flag it because the judge may read the
  `total: 0` clause as making item 15 unverifiable. What would settle it: a check that measures the
  baked bubble plate — e.g. asserting in Nim that a full-cap `say` typeset at `BubbleFontPx` fits
  inside `BubbleWidthPx × BubbleBandHeightPx` without pixie clipping — or a fixture that lets the real
  wasm core run and screenshots the band.

### N2 — one missing seat leaves the sim in `Lobby` for the whole 660 s budget; the match never starts
- Where: `src/bodies/sim_state.nim:20-21`; `src/bodies/sim.nim:485-493`; `src/bodies/server.nim:644-659,752-756,617-630`.
- Observed, traced step by step: with seat 1 never connecting, `sim.lobbyJoinTimedOut()`
  (`sim_state.nim:31-36`) fires at `lobbyJoinTimeoutTicks`; `server.nim:649-659` sets
  `reportedNoShow = true`, `forceStart = true`, calls `declarePlayerFailure` and logs
  `physics-bodies: seat N never registered; driving BUG-<i+1> with pusher`. The force-start block
  (`server.nim:752-756`) then only does `sim.lobbyTicks = config.startWaitTicks` — and by then
  `lobbyTicks` is already ≥ `startWaitTicks`, so it is a no-op. The round can only start at
  `sim.nim:488-491`, guarded by `sim.lobbyIsStarting()`, which is
  `sim.phase == Lobby and sim.players.len >= sim.config.minPlayers` (`sim_state.nim:21`).
  `minPlayers` is 2 in variant `default`, variant `blitz` and the cert fixture, and nothing anywhere
  lowers it (`grep -rn "minPlayers" src/` returns only the type, the config reader and this guard).
  So with 1 of 2 seats present the predicate is false forever, `startRound()` is never called, and the
  `Lobby` branch of `step` returns before the step-12 `maxTicks` check (`sim.nim:492-493`). The loop
  is still bounded: at 660 s `server.nim:617-630` writes the `stop` record, calls
  `applyWallClockStop` (which banks nothing because `phase != Playing`, `sim.nim:581-582`), and the
  episode ends `deadline/wall_clock` with `rounds: 0`, `scores: [0.000, 0.000]`.
- Design says: §End conditions — “A seat that never connects does **not** end the episode:
  `lobbyJoinTimeoutTicks` … expires, the no-show is reported …, its bug is driven by the `pusher`
  baseline for the whole run, and the match plays to a normal ending.” §Tests 7 lists “a
  never-connecting seat is reported to `COGAME_PLAYER_FAILURE_URI`, **logged loudly, and the match
  still reaches a normal ending**”.
- Checklist item: closest is 5, which is **not** falsified — the episode settles and scores at 660 s +
  ~20 s grace ≈ 680 s, inside the 720 s allowance, and there is no unbounded loop. Untested: no suite
  covers a partial lobby (`tests/test_server.nim:123-172` connects both seats; `tests/test_engine.nim`
  never exercises the lobby path).

### N3 — the controller’s rim guard carries two terms the design does not describe
- Where: `src/bodies/control.nim:196-205` and `:250-251`.
- Observed: the design’s §The controller step 3 is
  `w = clamp((d − (R − rimGuardUm)) · 100 / rimGuardUm, 0, 100)`. The code adds a velocity
  look-ahead — `radial = max(0, v·outward)`, `stopping = radial² / 8000` — and uses
  `w = clamp((d + stopping − (ringR − guard)) · 100 / guard, 0, 100)`. It also adds a thrust floor the
  design has no counterpart for: `if w > 0.0: e = max(e, 3.0 * w / 100.0)` (`:250-251`), i.e. inside
  the guard band the controller pushes at least proportionally to `w` regardless of the intent’s
  `aggression`. Both are commented in place as deliberate. Effect (inferred): a policy that orders
  `aggression 0` still gets thrust near the rim, and the `aggression == 10` halving (`:206-207`)
  halves the braking too, as the comment states.
- Checklist item: none. Advisory.

### N4 — two of the three shipped `BaselineParams` differ from the values the design note states
- Where: `src/bodies/control.nim:20-22`; `tools/ci/baseline_tuning.json` (`pick`); `tests/test_tuning.nim:22-32`.
- Observed: shipped `RimGuardUmDefault = 600_000`, `ChargeLeadTicksDefault = 4`,
  `LiftEngageUmDefault = 620_000`. The design’s §Scripted baselines states
  `rimGuardUm (600 000)`, `chargeLeadTicks (6)`, `liftEngageUm (820 000)`. The shipped values equal
  the sweep’s recorded `pick` and `tests/test_tuning.nim` pins that equality, so the repo is
  self-consistent; the design note is the thing that is stale. The design explicitly authorises the
  sweep to move exactly these three numbers.
- Checklist item: none. Advisory.

### N5 — a snap-to-rest step exists in the dynamics that §Resolution order does not list
- Where: `src/bodies/sim_types.nim:95-100`; `src/bodies/sim.nim:172-176`.
- Observed: after friction, `if abs(b.vx) < RestFloorUm and abs(b.vy) < RestFloorUm: b.vx = 0; b.vy = 0`
  (`RestFloorUm = 64` µm/tick ≈ 0.0015 m/s). The design’s step 5 has 5.1–5.5 with no such clause. It is
  hashed state, applied identically on record and playback, and is what makes `tests/test_control.nim`’s
  “brace brakes to |v| = 0” claim reachable at all.
- Checklist item: none. Advisory.

### N6 — the contact-torque expression divides by `Q12` once more than the design’s formula
- Where: `src/bodies/sim.nim:349-360`; `src/bodies/ring.nim:204-207`.
- Observed: the design’s step 6.5 is `omega += (cross(rVec, (j + shove) · n̂) · 1000) div (4096 · TorsoRadius)`
  with `n̂` defined as “the Q12 unit vector”. The code passes an already-descaled force vector into
  `crossQ12` — `crossQ12(rx, ry, int32((sign*force*nx) div Q12), int32((sign*force*ny) div Q12))` — and
  `crossQ12` (`ring.nim:207`) is a plain `rx*fy − ry*fx` with no internal Q12 division, then divides the
  result by `Q12 * TorsoRadius`. Net: the code’s `delta` is 4096× smaller than the design’s formula read
  literally. Inferred practical effect: small, because `delta` is clamped to `±MaxYawMilli div 2 = ±450`
  and even the code’s value saturates that clamp for any contact with a perpendicular force component
  above ~1 800 µm/tick at a torso-edge lever arm; the two readings differ only for very weak contacts.
- Checklist item: none. Advisory.

### N7 — `contacts` is incremented on **both** bodies for a two-sided impulse
- Where: `src/bodies/sim.nim:344-347,377`.
- Observed: the receiver loop runs `for recvIdx in 0 ..< BodyCount` and skips only when
  `force = j + shoveInto[recvIdx] <= 0`. A closing contact produces `j > 0` for both bodies, so both
  get `contacts += 1` for the same pair. The design’s step 6.7 says `contacts[receiver] += 1`.
  `contacts` is hashed (`sim_state.nim:100`) and reported in `results.contacts`, so it is consistent
  between record and playback; only the semantics differ from the note. Also: a pair that touches with
  `vn >= 0` and no shove increments nothing, where the design’s wording would count it.
- Checklist item: none. Advisory.

### N8 — 25 disc pairs are built, not “ten”, and `discPairs` contains a dead branch
- Where: `src/bodies/sim.nim:194-229` (esp. `:204-209`); `src/bodies/ring.nim:3,116-118`.
- Observed: `discPairs` returns `array[25, DiscPair]` and fills all 5×5 combinations; the filtering to
  live pairs happens later, in `resolveContacts` (`:251-258`). The design’s step 6 and `ring.nim`’s own
  doc comment both say “ten disc pairs”. Separately, `:204-209` is
  `if ia >= 0 and (a.downTicks > 0 or not a.footGrounded[ia]): discard` — a no-op branch with no
  `continue`, so it changes nothing; the real skip is the later one. No behavioural consequence
  (inferred: the later filter is equivalent), but the block is dead code and the “ten” count is wrong
  in both the note and the comment.
- Checklist item: none. Advisory.

### N9 — two `tests/test_control.nim` bounds are weaker than the design’s §Tests 4 wording (documented in place, not loosened during this run)
- Where: `tests/test_control.nim:332-336` and `:128-134`.
- Observed: (a) the design asserts “`brace` brakes monotonically to `|v| = 0` within **120 ticks**”; the
  test asserts `stopped <= 240` and comments “The design note's ‘within 120 ticks’ is the right claim
  against the wrong constant” with the arithmetic (`ln(165000/64)/0.0391 = 197 ticks`). (b) the design
  asserts the rim guard holds “from **any legal state**”; the test zeroes the rollout’s starting
  velocity (`sim.bodies[0].vx = 0; vy = 0`) with the comment “An inherited 3 m/s outward velocity is not
  something a rim guard can be asked to undo.” Both were written this way in the fork commit
  `c573490`; neither was weakened during this run (`git log -p -- tests/` shows no edit to
  `test_control.nim` after `c573490`), so **item 1 is not violated**.
- Checklist item: none (item 1 covers loosening *during this run* only). Advisory.

### N10 — `complete/match_won` re-derivation is not separately pinned
- Where: `tests/test_replay.nim:31-48`, esp. `:39-40`.
- Observed: the design’s §Tests 10 lists four end reasons to record→re-derive, naming
  `complete/match_won` first. The test’s first block asserts
  `episode.sim.endRule in [EndRuleMatchWon, EndRuleFullTime]`, so whichever of the two the
  `pusher` vs `anchor` episode at seed 5104773 happens to produce is what gets re-derived; the other is
  covered only by the second block, which is explicitly `full_time`. `tests/test_scoring.nim:133-141`
  does assert `endRule == match_won` on a clinching episode, but does not re-derive it.
- Checklist item: none (item 2 is satisfied by the four re-derivation blocks that do run). Advisory.

### N11 — the CLI manifest validation the design puts “as a CI step” runs only in the release workflow
- Where: `.github/workflows/coworld-release.yml:164-193`; `tests/test_manifest.nim` (no CLI call);
  `.github/workflows/ci.yml` (no such step).
- Observed: `_load_template_manifest` and `validate_upload_manifest` are invoked in
  `coworld-release.yml`’s “Validate the manifest template with the CLI” step, wrapped in
  `try/except ImportError` that downgrades a missing CLI to `::warning::`. The design’s §Packaging
  (“validate offline with the CLI … **as a CI step** before dispatching”) and §Tests 12 (“the installed
  CLI's own `_load_template_manifest` + `validate_upload_manifest` accept the template”) put it in the
  test suite. `tests/test_manifest.nim` asserts everything else on that list from the JSON directly.
- Checklist item: 10 is satisfied by the shape assertions (`tests/test_manifest.nim:155-174`). Advisory.

### N12 — every `round` chat record is written at the final tick, not at the tick its round ended
- Where: `src/bodies/server.nim:924-928`; `tests/helpers.nim:106-109`.
- Observed: the `round` records are emitted inside the `quitAfterFrame` artifact block, all with
  `tickTime(sim.tickCount)` (the episode’s last tick). The design’s §Record and event vocabulary calls
  the `round` record “**load-bearing**: `bankRound` applies it identically on record and playback”.
  In the code, `bankRound` is called inside the hashed `step` (`sim.nim:540`) and the replay applier
  explicitly refuses to re-apply `round` records — `replays.nim:243-245`: “`round` records re-derive
  inside `bankRound`, so re-applying one here would double-bank it”. So re-derivation is correct; the
  records are forensic only (`tools/replay_summary.py`), and their timestamps do not locate the rounds.
- Checklist item: none. Advisory.

### N13 — the lull map is always empty, so skip-lulls is inert
- Where: `src/bodies/broadcast.nim:154-157`; `src/bodies/replays.nim:405-408`, `:309-327`, `:78-84`.
- Observed: `stepEvents` emits a `turn_end` event whenever `turn != tracker.prevTurn and phase == Playing`
  — every `turnTicks` (36) ticks. The scan’s lull collector adds a beat tick for **any** event whose
  kind is not in `["contact","shove","rim_slip"]` (`replays.nim:405-407`), so `turn_end` lands in
  `beatTicks` every 36 ticks. `buildLullSpans` needs `b − a + 1 >= MinLullTicks` where
  `a = prevBeat + LullLeadTicks + 1` and `b = nextBeat − LullLeadTicks − 1`, i.e. a gap of at least
  `144 + 98 = 242` ticks between consecutive beats. With beats 36 ticks apart no span ever qualifies, so
  `lullSpans` is always `@[]` and `state["lulls"]` is never emitted (`broadcast.nim:354-358`).
  Design §Beats says `stagger` is not a beat either, yet it is also collected here. The design’s state
  JSON example shows `"lulls": [[430, 590]]`.
- Checklist item: none. Advisory (a transport control that never does anything).

### N14 — board speech bubbles persist until replaced, not the 2.5 s the design specifies
- Where: `src/bodies/global.nim:1093-1106` (`bubbleLines`); `src/bodies/sim_state.nim:130-138`.
- Observed: `bubbleLines` takes the newest `say` per body out of `sim.feedIntents`, a ring buffer capped
  at `2 * BodyCount = 4` records. Each turn pushes 2 records, so a bug’s bubble is displayed until its
  next turn replaces it (1.5 s cadence) — there is no timer. The design’s §Readouts 6 says “drawn for
  2.5 s”. No consequence for bounds (the band is fixed), only for dwell time.
- Checklist item: none. Advisory.

### N15 — the round/ring caption lives in a new `#pb-ring` element, not in `#clock-caption`
- Where: `client/replay_broadcast.html:2979-2990`, `:3017-3030`.
- Observed: the design’s §Readouts 1 says `#clock-caption = "ROUND 3 of 5 · RING 2.31 m"`. The game
  block instead appends a `#pb-ring` div inside `#clock` carrying that string, and sets
  `#clock-caption` to the literal `'Round clock'`. Both are on screen — the CI readout shows
  `"0:05 ROUND CLOCK ROUND 1 OF 4 · RING 3.00 M"`. The new element is inside `#scorebug`, not the
  transport band, so transport rule (b) is unaffected.
- Checklist item: none. Advisory.

### N16 — build artefacts are committed, and `config.nims` gains a third change beyond the two the design names
- Where: `replay-viewer/dist/nimcache/**` (≈70 generated `.c` files, committed in `c573490`);
  `replay-viewer/config.nims:47`.
- Observed: the design’s §Viewer table says `config.nims` is ctf’s “verbatim except `ctf_replay.js` →
  `bodies_replay.js` and the `EXPORTED_FUNCTIONS` list renamed”. The actual diff also adds
  `--preload-file {rootDir / "client" / "art"}@client/art`. That addition is **necessary and correct**:
  `src/bodies/global.nim:447` reads `client/art/walls/wall_v.jpg` at runtime, so the wasm build needs it
  in MEMFS. The committed `replay-viewer/dist/nimcache/` tree is emscripten build residue that
  `tools/build_replay_viewer.sh` regenerates in a container (`:29-30 rm -rf`/`mkdir -p`).
- Checklist item: none. Advisory.

### N17 — smaller design/code drifts, each observed, none with a behavioural consequence
- `src/bodies/baselines.nim:230-259` — `pusher` emits **five** distinct `say` strings across six
  branches (“closing” is shared); the design’s §Scripted baselines says “one of four fixed strings”.
- `src/bodies/decide.nim:103-105,156-159,169-173` — the per-turn budget is a **pre-check** before each
  attempt, and the inter-batch `sleep` is measured inside the same window, so a turn’s worst-case wall
  time is `turnSpacingMs + attempt1Ms + retryMs` ≈ 20 s rather than the `turnBudgetMs` 16 s the design
  calls “the whole turn … wrapped”. Still bounded, and turn starts are 6 s apart by construction. The
  design also calls the floor a “stop-interruptible sleep”; the code uses a plain `os.sleep`
  (`decide.nim:159`), bounded by `turnSpacingMs`.
- `src/bodies/ring.nim:53-62` + `src/bodies/sim.nim:467,502` — a round’s last tick is `roundTick = 395`,
  at which `ringRadiusNow = 1_996_000` µm. The design’s §The game says the ring “reaches 1.992 m by the
  round clock”; `1_992_000` is `ringRadiusAt(cfg, 396)`, the value the observation reports as
  `radius_at_round_end_m` (`baselines.nim:75-76`) and the value `tests/test_ring.nim:27` pins. The ring
  never actually contracts to 1.992 m inside a round.
- `client/broadcast_core.js` differs from the starter’s copy in **two** lines — the
  `CTF_WIRE`→`BODIES_WIRE` identifier (`:49`) and a comment path `src/ctf/sim.nim`→`src/bodies/sim.nim`
  (`:268`). The design’s §Tests 13 says “differs … in **exactly** the `BODIES_WIRE` identifier”;
  `tests/test_viewer.nim:71-73` asserts presence/absence rather than an exact diff, so it passes.
- `src/bodies/sim.nim:501-509` — step 3 recomputes leg reach from the **previous** tick’s posture
  (`body.posture()` reads `lastCmd`, which `applyDynamics` overwrites at `:145`), while step 5’s thrust
  uses the **new** posture. That is the literal reading of the design’s ordering (3 before 4/5); noted
  because it is a subtle one-tick coupling a reader could mistake for a bug.

---

## Traced and consistent

**Resolution order** (`src/bodies/sim.nim:477-570`) — walked against §Resolution order 1–12:
step 3 ring geometry + `refreshLegs` (`:502-509`); step 4 yaw servo (`body.nim:77-94`: self-driven term
skipped when `downTicks > 0`, drag and clamp kept, `hMilli` wrapped into `0..31999`); step 5 traction
(`:157-163`), friction (`:167-170`), per-posture clamp (`:180-185`), `p += v` (`:187-188`); step 6
swept contacts in one fixed order with the positional split, restitution impulse, one-sided shove with
`(4 − groundedA)/8` recoil (zero at four grounded legs, `:328-329`), torque, tilt load, lift self-tilt,
and the post-loop `MaxBodySpeedHard` clamp (`:392-400`); step 7 tilt/knockdown (`:402-426`); step 8
arena clamp (`:428-443`); step 9 round-end checks in the exact order ring-out → knockout → round clock,
with both-outside and `CentreTieUm` draw branches (`:445-475`); step 10 `bankRound` called only from
inside `step` (`:91-114`, `:540`); step 12 episode checks in order (`:544-569`) then `assertInvariants`.

**Ring shrink law** — `ring.nim:53-62` is `max(rmin, r0 − max(0, roundTick − startAt)·per)`, a pure
function of `(config, roundTick)`, called once per tick at `sim.nim:502`. `roundTick` is not advanced
during `RoundReset`, so the arc freezes for the hold. `tests/test_ring.nim:17-29` re-derives it at every
tick of a round.

**Rounds, end swap** — `ring.nim:91-109`: bug 0 takes the drawn axis on even rounds and
`axis + 16` on odd ones (`swapped = (roundIndex mod 2) == 1`), each facing `mine + 16`, both at
`StartRadius` from the centre. `tests/test_ring.nim` exercises it over 50 seeds.

**Scoring and antisymmetry** — `sim.nim:85-114` (`RoundWinMicro + bonusMicro`, 250 000 for `ring_out`
and `knockout`, 0 for `decision`, nothing banked on a draw); `roster.nim:106-111`
`seatScoreMicro(s) = raw(s) − raw(1−s)`, which is one subtraction and its negation; `labels.nim:22-33`
`roundTo` is sign-symmetric by construction (`if scaled >= 0 … else −(…)`), so
`round3(x) + round3(−x) == 0.0` bit-exactly. `tests/test_scoring.nim:90-107` asserts the sum is exactly
`0` over 200 randomised round logs, `:31-72` reproduces all six worked examples, `:109-116` pins the
`±3.750` range.

**Decision path** — credential ladder Bedrock → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` → disabled
(`llm.nim:96-129`); one haiku candidate (`:70-80`); `throttled` set only when no candidate remains
(`:175-181`); `max_tokens` from config (default 900), no `output_config` for haiku (`:148-151`);
system prompt demands a leading `{` (`:219`). `decide.nim` turn: throttle flag cleared per turn (`:110`),
budget guard (`:117-125`), seats classified (`:128-149`, an LLM seat that cannot call is recorded as a
`fallback` with cause `no_credentials`/`budget_guard`, not silently as scripted), rate floor
(`:156-162`), ≤2 batches (`:166`), whole-batch deadline in whole seconds (`:190-191`, and
`sim_config.nim:103-104` refuses a sub-second value so the floor division is an identity), per-seat
parse with cause classification (`:194-217`), throttle fast-fail (`:220-226`), anything still open plays
`pusher` with a `fallback` record and the `falling back` log phrase phase 60 greps for (`:229-243`).

**Every wait and its bound** — LLM batch: `makeRequests(batch, max(1, deadlineMs div 1000))`
(`decide.nim:190-191`, 9 s then 5 s). Inter-batch floor: `sleep(min(turnSpacingMs, turnSpacingMs − since))`
(`:159`), ≤6 s. Per-turn: monotonic pre-check against `turnBudgetMs` (`:169-173`). Lobby:
`lobbyJoinTimeoutTicks` (`sim_state.nim:31-36`) — but see N2. Frame limiter:
`sleep(max(1, min(2, remaining)))` inside a loop bounded by `frameDuration` (`server.nim:482-495`).
Engine stop: 660 s (`server.nim:617-630`), clamped ≤720 by `sim_config.nim:108`. Shutdown grace:
`while getMonoTime() < graceUntil: sleep(200)` with `ShutdownGraceSeconds = 20` (`server.nim:82,958-961`).
Replay lobby walk in the browser: bounded by `replayMaxTick()` (`replay_runtime.nim:33-37`). Seek
convergence: `SeekTicksPerFrame` slices (`replays.nim:460-474`). No unbounded loop and no blocking read
found in the game loop, the decision layer or the replay runtime. `drawInt` has no rejection sampling
(`ring.nim:38-47`), and exactly 6 draws happen per episode, all at `t = 0` (`sim.nim:50-58`), asserted by
`tests/test_determinism.nim:244-273`.

**String truncation** — every path to the replay: `intents.nim:288-289` (`note` → 160 runes,
`say` → `sanitizeSay` which cuts on runes *first* then filters printable ASCII and strips `{`/`}`),
`:342` (`register.policy` → 48), `:354` (`fallback.detail` → 200), `:318-332` (`boundedIntentRecord`
shrinks the `note`/`say` fields, never the serialized JSON, with a `guard < 12` loop bound),
`server.nim:717` (`register.prompt` → 4000 at transport, truncated not rejected, and never written to
the replay — `registerRecord` carries only the label/kind/baseline), `llm.nim:168,176,184,193`
(provider bodies rune-truncated before they become `fallback.detail`). `extractJsonObject`’s error
message is rune-truncated too (`intents.nim:131-133`). I found no byte-index slice on any string that
reaches the replay; `roster.nim:210-215`’s only slice is at an ASCII `'('`.

**Replay writer** — magic `COWLDPBD`, format version 1, `GameName`/`GameVersion` from `sim_types`
(`replays.nim:86-97`); command-byte log written change-only through the codec’s own guard
(`replays.nim:102-116`, called from `server.nim:805`), pre-sized to `BodyCount` rather than the roster
so a no-show seat’s bug still records bytes (`:118-124`); one `gameHash` per tick (`server.nim:827`);
`gameHash` mixes tick, phase, round index/tick/resetLeft, ring radius, all per-body physics and
counters, `roundsWon`/`roundMicro`/`ringOuts`/`knockouts`/`knockdownsSuffered`/`perm`, `rngDraws`,
`roundLog.len`, `isDraw`, `winner`, `stopTick` — a superset of the design’s list — and mixes no FX,
`say`, note or label (`sim_state.nim:77-113`). The wall-clock `stop` is the one load-bearing record and
is applied by the same proc on both sides (`server.nim:623-629` ↔ `replays.nim:253-255`); one extra
GameOver tick is stepped so the stop lands inside the hash chain. `result` and `round` records ride the
chat stream and are told from a shout by the leading `{` (`sim_state.nim:134`).

**Viewer re-derivation and provenance** — all four viewer files are ctf’s with renames only (diffs run
above): `config.nims` (2 renames + the justified preload), `static_replay.js` (2 renames),
`static_replay_worker.js` (identifier renames + the `importScripts` target), `bodies_replay.nim` forked
from `ctf_replay.nim`. `chrome_common.js` byte-identical, and its one starter-name reference —
`window.CTF_WIRE` at `:72` — is harmless by design: it is used only for `speeds` and `fps`, whose
inline fallbacks `[1,2,3,4,8,16]` and `24` are exactly this game’s `PlaybackSpeeds`/`TargetFps`, which
are kept verbatim; `src/bodies/wire_constants.nim:10-14` documents that decision and
`broadcast_core.js` reads `BODIES_WIRE`. The bundle’s `index.html` is the same
`client/replay_broadcast.html` with the three markers substituted
(`Dockerfile.replay-viewer:39-42`), asserted present at `:53-67`.

**Manifest** — `num_agents: 2` in `variants[default].game_config`, `variants[blitz].game_config` and
`certification.game_config`, and absent at every variant top level; `certification.players` has 2
entries and `certification.game_config.players` has 2; cert seed `5104773`; `roundsToClinch == maxRounds == 4`
so it cannot clinch early; `ringShrinkPerTickUm: 0`; `turnSpacingMs: 0`; `wallClockBudgetSeconds: 180`.
`results_schema` has exactly 21 properties matching `playerResultsJson`’s 21 keys
(`roster.nim:176-199`), `additionalProperties: false`, every per-seat array `minItems/maxItems: 2`,
`roundResults` 0..5, `reason` enum of 3, `endRule` enum of 5. `config_schema` is
`additionalProperties: false`, `required: ["tokens","players"]`, every array carries
`minItems`/`maxItems` (`tokens` 1..2, `players` 1..2, `slots` 0..2), and its 33 properties cover every
key `sim_config.update` reads (`tests/test_manifest.nim:135-152` derives the list from the source).
Top-level `tags` has 5 entries; `game.tags` absent; no top-level `version`; no `game.display_name`;
`game.owner` present; secret namespace `secret://coworld/physics-bodies/anthropic_api_key` equals
`game.name`. `python3 tools/build_manifest.py` regenerates the committed file byte-identically (I ran it
and restored the tree; `git status` clean).

**Tests** — all 15 suites the design names are present plus `test_tuning.nim`; `NIM_TESTS_RELEASE_ONLY`
is set on the repo to `tests/test_perf.nim tests/test_baselines.nim`, exactly as the design says
(`gh variable list`). `tools/ci/viewer_smoke.mjs` is **byte-identical** to
`coworld-builder/templates/tools/ci/viewer_smoke.mjs`; `tools/ci/docker_smoke.sh` is the template with
only the three named substitutions (`<slug>`→`physics-bodies`, `<IMAGE>`→`coworld-physics-bodies`,
`<SEATS>`→`2`). The four expected angle-bracket residues (`<cow_id>`/`<sha>`, `<run_id>` ×2,
`<name>:vN`) are the only ones present.

---

## Could not determine

- **Whether a full-cap 48-rune `say` renders inside the reserved bubble plate.** The plate is
  `BubbleWidthPx = 880` × `BubbleBandHeightPx = 120` logical px at `BubbleFontPx = 26`
  (`global.nim:73-76`), typeset by pixie with `bounds = vec2(w − 16·pad, h − 8·pad)`
  (`:532-533`); anything past the bounds is clipped by the image raster rather than drawn at a negative
  coordinate. Arithmetically `"BUG-1: " + 48` runes at 26 px is ~715–860 px, i.e. one or two lines
  inside 864×112 — but no test measures it and no CI check can see it (N1). What would settle it: a Nim
  test that typesets the cap string with `data/font.ttf` at `BubbleFontPx` and asserts the arrangement’s
  bounding box fits, or a screenshot of the band from a run with a real `say`.
- **Whether a live LLM episode stays inside the 660 s stop.** §Decisions’ arithmetic assumes 6 s
  start-to-start over 60 turns (354 s); the code’s per-turn worst case is ~20 s (N17), which the budget
  guard and the stop bound but which no CI run exercises — `docker_smoke.sh` runs with no
  `ANTHROPIC_API_KEY`, so every CI turn falls back instantly. Untested; would need a hosted episode
  (phase 60’s `replay_summary.py` check).
- **Whether `results.reason == "complete"` holds on the platform for a two-champion match.** Every
  green path I can verify is all-scripted. Untested; same phase-60 evidence would settle it.
