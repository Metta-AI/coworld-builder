# r1 review — sokoban

Repo: `Metta-AI/cogame-sokoban` @ `464b2abda558bb7c36949dd8dbd783d638f479de` (clone at `/tmp/cogame-sokoban`)
Range: `46a24b6..464b2ab` (3 commits: bootstrap → `feat(sokoban)` → 2 fixes)
Starter: `coworld-ctf` at `/workspace/starters/coworld-ctf` (`4f8f77c`)
Design note: `runs/2026-08-29-sokoban/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)
Files opened and read in full: 34 (all of `src/sokoban/*.nim`, `src/sokoban.nim`, `src/sokoban_player.nim`,
`replay-viewer/*`, `client/sokoban_block.html`, `client/replay_broadcast.html` (targeted spans + full prefix diff),
`client/broadcast_core.js` (diff), `client/chrome_common.js` (sha), all 10 `tests/*.nim`, `coworld_manifest_template.json`,
`tools/ci/{docker_smoke.sh,viewer_smoke.mjs,policies.json,renderer_fixture.html,baseline_tuning.json}`,
`tools/build_replay_viewer.sh`, `scripts/build_broadcast_page.py`, all three workflows, `Dockerfile`,
`Dockerfile.replay-viewer`); plus CI logs for run `33243111396` (jobs `99075729539` docker-smoke, `99075892979` wasm-viewer).

Nineteen findings (F1–F19). None of them is one I can show falsifies a named checklist item outright; F9 and F17
are the two where the checklist's literal wording and the shipped artefact disagree and I say so explicitly rather
than deciding it. Everything else is a divergence from the design note, an internal inconsistency, or a gap in
coverage. Categorisation is the judge's.

---

## Blocking

I found nothing I can demonstrate to be a blocking violation of a named checklist item. Items 1, 2, 3, 4, 5, 6, 7,
8, 10, 11, 12, 13 and 14 were each traced to code or to cited CI evidence and are recorded under **Traced and
consistent** below. Items 9 and 15 are the two where I have concrete observations that a judge may read as
falsifying: they are F3 and F9 respectively, filed under Non-blocking with the exact checklist sentence quoted
against the exact code, so the judge can decide without re-tracing.

---

## Non-blocking

### F1 — the `dropped` count reported back to the seat is hard-coded to zero
- Where: `src/sokoban/sim.nim:386-396` (specifically `:393`), read at `src/sokoban/sim.nim:605-613`
- Observed: `endTurn` builds the seat's report as
  ```nim
  sim.lastReport = TurnReport(
    executed: sim.turnExecuted, pushes: sim.turnPushes, blocked: sim.turnBlocked,
    truncated: sim.turnTruncated,
    dropped: 0,                      # sim.nim:393
    unreachable: sim.turnUnreachable, notes: notes, valid: true)
  ```
  `observationJson` then emits `"dropped": sim.lastReport.dropped` (`sim.nim:611`). A repo-wide grep for
  `lastReport` finds writes only here and reads only in `sim.nim:605-613` and `decide.nim:103-108`; nothing ever
  assigns a non-zero `dropped`. The *replay* record is correct — `decide.nim:107` writes
  `"dropped": directive.dropped + directive.overCap` — so the two disagree by construction.
- What the note says: §Turn and tick structure 6b — an entry that does not validate is "dropped … counted in
  `repliesRepaired`, and **reported back next turn**"; §Per-seat observation lists `last_turn.dropped`; §Tests 24
  claims the validator "reports `truncated` / `dropped` / `unreachable` back accurately".
- Coverage: `grep -rn "last_turn\|lastReport" tests/` returns **nothing**. No shipped test touches `last_turn` at all.
- Consequence (observed): a policy that sends a malformed action is told `dropped: 0` next turn, so the
  self-correction loop both champion prompts rely on ("If `last_turn` says …") never fires for dropped entries.

### F2 — a wall-clock or fault stop zeroes the level that was in play, including its parked crates
- Where: `src/sokoban/sim.nim:635-651`
- Observed, step by step:
  1. `settle(reason, rule, detail)` with `sim.levelActive == true` and `reason != endComplete` calls
     `sim.finishLevel(loUnreached)` (`:639-641`).
  2. `finishLevel` (`:238-246`) writes `record.outcome = loUnreached`, `record.boxesPlaced = sim.levelBoxesPlaced`,
     `record.moves = sim.levelMove`, `record.turns = sim.levelTurn`, `record.pushes = sim.levelPushes`.
  3. The very next loop (`:642-648`) is `if sim.levels[i].outcome in {loRunning, loUnreached}: … moves = 0;
     turns = 0; pushes = 0; boxesPlaced = 0` — which matches the record just written and **resets all four to 0**.
  4. `boxCredit` (`:412-414`) sums `record.boxesPlaced`, and `episodeScore` (`:421-427`) weights it at 10 000, so
     up to 30 000 points of real, earned progress on the in-flight level are discarded; `finalTick`
     (`:432-434`) is `Σ record.moves`, so it under-reports the real tick count after a deadline stop.
- What the note says: §End conditions, `deadline` — the engine "settles with the **real** levels solved so far
  (**never zeroed**, so a deadline episode is still rankable), marks every **unstarted** level
  `levelOutcome = "unreached"` with `levelMoves = 0`, `levelTurns = 0`, `levelPushes = 0`,
  `levelBoxesPlaced = 0`". The level in play is not an unstarted level.
- Coverage: `tests/test_sokoban_sim.nim:445-460` asserts only that records *already marked* `loUnreached` carry
  zeros, and closes with `check episode.sim.episodeScore() >= 0`, which is true of every episode. The test cannot
  distinguish "unstarted, correctly zeroed" from "in play, wrongly zeroed".
- Related, same proc: for `reason == endComplete` with a level still active, `:640-641` marks it `loOutOfSteps`
  even when the episode ended on the turn cap rather than the step budget, so `results.outOfSteps` is incremented
  for a level that did not run out of steps.

### F3 — the provider reply is byte-truncated before parsing, on a path that reaches the replay
- Where: `src/sokoban/llm.nim:197-208` (`:198-199` and `:207-208`)
- Observed:
  ```nim
  var body = response.body
  if body.len > MaxReplyBytes * 8:
    body = body[0 ..< MaxReplyBytes * 8]      # llm.nim:198-199  — byte slice
  …
  if result.len > MaxReplyBytes:
    result = result[0 ..< MaxReplyBytes]      # llm.nim:207-208  — byte slice
  result = result.rePrefix()
  ```
  `result` is the concatenated assistant text. It is handed to `extractJsonObject` → `parseDirective`
  (`decide.nim:255-256`), whose `say`/`notes` are then rune-truncated (`directives.nim:186-187`) and written to
  the replay (`server.nim:313-316`, `decide.nim:109`). `truncateRunes` (`sim_types.nim:185-193`) only *shortens*;
  it cannot repair a codepoint the byte slice already split. The file's own comment at `llm.nim:178-181` states
  exactly this hazard for a different string and uses `truncateRunes` there instead.
- What the note says: §Reply schema — "whole reply | bytes | **≤ 4096 read from the provider before parsing**",
  i.e. the note does specify a byte cap here.
- Checklist item 9 (quoted): "Every string that reaches the replay (`say`, `notes`, prompts, captured errors) is
  truncated on **rune** boundaries."
- **Inferred, not observed**: for a split codepoint to actually land in the replay, the byte-truncated text must
  still parse as a JSON object with the broken byte inside `say` or `notes`. Nim's `std/json` does not validate
  UTF-8, so this is possible; I did not construct the input that proves it. The rune-truncation test that does
  exist (`tests/test_sokoban_baselines.nim:174-184`) feeds an *already valid* 400-emoji string and asserts
  `validateUtf8() == -1` after `parseDirective` — it never exercises the 4096-byte cut in `llm.nim`.

### F4 — `actionsDropped` double-counts entries that `repliesRepaired` already counts
- Where: `src/sokoban/sim.nim:278-280`
- Observed:
  ```nim
  sim.actionsDropped += directive.dropped + directive.overCap
  sim.macrosUnreachable += expansion.unreachable
  sim.repliesRepaired += directive.dropped
  ```
  `directive.dropped` is entries that failed validation; `directive.overCap` is entries past
  `maxActionsPerTurn` (`directives.nim:192-198`). An invalid entry therefore increments both `actionsDropped`
  and `repliesRepaired`.
- What the note says: §Turn 6a — entries past the cap "are dropped and counted in `actionsDropped`"; 6b — an
  entry that does not validate is "dropped …, counted in `repliesRepaired`". The two counters are described as
  disjoint. Both are in `results` (`sim.nim:516-518`), so a phase-60 reader adding them double-counts.

### F5 — `throttled` is an eighth fallback cause outside the note's closed set
- Where: `src/sokoban/decide.nim:263-272` (`:269-270`)
- Observed: `elif error.msg.startsWith("llm throttled"): lastCause = "throttled"`, which is written into the
  `fallback` record's `cause` field by `fallbackRecord` (`decide.nim:68-72`) via `fallbackPlan` (`:287`).
- What the note says: §Degrade, never hang — "a `fallback` record is written with
  `cause ∈ {timeout, parse_error, transport_error, no_credentials, rate_guard, budget_guard, disconnected}`."
  `throttled` is not in that set, and `disconnected` is never produced anywhere (grep across `src/`).

### F6 — `baselineNodeCap` ships as 8, not the note's 20 000
- Where: `src/sokoban/sim_types.nim:222` (`baselineNodeCap: 8`), `src/sokoban/search.nim:29-36`
  (`DefaultSearchParams(nodeCap: 8, …)`), `tools/ci/baseline_tuning.json:4` (`"nodeCap": 8`), and all three
  `game_config` blocks in `coworld_manifest_template.json` (`ladder`, `hard`, `certification` — verified by
  parsing the file: `baselineNodeCap 8` in each).
- Observed: the repo is **internally consistent** at 8 and asserts it —
  `tests/test_sokoban_events.nim:143-155` checks `baseline_tuning.json` ≡ `DefaultSearchParams` ≡ the manifest's
  `baselineNodeCap`. `search.nim:31-36` carries the rationale: "a 20 000-node cap measured 1.00 / 1.00 / 0.99
  across the tiers, which is precisely the superhuman floor the design note's test 25 exists to keep out of the
  image."
- What the note says: §Baselines step 5 "`baselineNodeCap = 20_000`", §Packaging variants `"baselineNodeCap": 20000`
  three times, §Server config-JSON row, and §Out of scope "`pusher` is a fixed 20 000-node best-first search".
  The note is stale relative to a deliberate, documented, tested decision.
- Also: the note's `tests/test_sokoban_tuning.nim` does not exist; the assertion lives in
  `tests/test_sokoban_events.nim:143-160`. The note's "`ci.yml` re-runs the sweep with `--check`" is not in
  `.github/workflows/ci.yml` (grep for `tune_baselines` across the workflows returns nothing), though
  `tools/tune_baselines.nim` is committed.

### F7 — the relaxed-tier fallback picks the deepest attempt, not the one closest to `bandMin`
- Where: `src/sokoban/levelgen.nim:299-306`
- Observed: `if bfs.reached > bestReached: … bestReached = bfs.reached; bestBoard = board; bestNode = relaxed.node`
  — a strict "keep the largest `reachedDepth`" rule.
- What the note says: §Level sourcing step 11 — "take the attempt whose `reachedDepth` is **closest to
  `bandMin`**". Since every attempt's `reached` is clamped at its own `targetDepth` (`levelgen.nim:201-202`) and
  `targetDepth ∈ [bandMin, bandMax]`, "largest" and "closest to `bandMin`" pick different attempts whenever two
  attempts straddle `bandMin`. `optPushes` is still exact either way (BFS first-discovery depth), so this changes
  which relaxed level ships, not its honesty.

### F8 — the committed page-provenance script does not run against the mounted starter
- Where: `scripts/build_broadcast_page.py:192-197` vs `/workspace/starters/coworld-ctf/client/replay_broadcast.html:3806`
- Observed: running the repo's own documented command
  ```
  python3 scripts/build_broadcast_page.py /workspace/starters/coworld-ctf/client/replay_broadcast.html \
      /tmp/rebuilt.html client/sokoban_block.html
  ```
  fails at `build_broadcast_page.py:40`:
  `AssertionError: anchor not found: '<div class="ec-thead"><span>Player</span><span>K</span><span>D</span>…'`.
  The starter's line is now
  `'<div class="ec-thead"><span>Player</span><span>K</span><span>D</span><span>TK</span><span>Clstr</span><span>Cap</span></div>'`
  — it has gained a `TK` column. The design note's own citations are ~11 lines below the mounted starter's
  (`:3795` vs `:3806` for that line, `:4344` vs `:4355` for the PAINTBALL banner), i.e. the fork was taken from an
  earlier starter revision and the starter has moved since.
- The test that claims to cover this (`tests/test_sokoban_viewer.nim:54-58`) only asserts the script *file exists*
  and contains the substrings `"replay_broadcast.html"` and `"PaintballChrome"`. It never executes it.
- **What I verified instead, directly**: the shipped page's prefix (lines 1..2927, above its
  `SOKOBAN additions to the inherited coworld-ctf chrome` banner at `client/replay_broadcast.html:2928`) diffed
  against the starter's prefix (lines 1..4354, above its banner at `:4355`) gives **1490 removed / 63 added
  lines**. Every removal hunk I opened maps to a removal the design note lists: the raycast FPV pipeline
  (starter `:2542-3476`, 935 lines, starting at `function renderFpv(s)` and ending before `function
  renderMismatch(s)`), the zoom-bar + minimap wiring (`:4143-4255`), the eye-level billboard art
  (`:2093-2126`, `:3982-4000`), `#viewpanel`/`#zoombar` CSS and markup, `#povBadge`, `#fpv-hp`/`#fpv-gear`/
  `#fpv-map`, `#endcard .ec-heart`, and the `kill`/`steal`/`return`/`capture` beat CSS. All 63 additions are the
  vocabulary re-mappings and the `SokobanChrome`/`SK_READY`/crate-chip splices the note names. This is a
  derivation of the starter's page, not a rewrite; what is missing is a *mechanical* way to re-verify it, which
  is what the script was for.

### F9 — the `--strict-text-bounds` gate measured zero strings, on both CI steps
- Where: `.github/workflows/ci.yml:327-332` and `:356-360`; CI run `33243111396`, job `99075892979` (`wasm-viewer`, green)
- Observed, from the job log:
  ```
  Load the bundle in a real browser:
    {"loaded":true,"ms":565,"clock":"SOLVED 1/6 WEIGHT 1/12 · MOVE 64/200 · SCORE 1050143", …,"feed_lines":0}
    soak: 10s of playback kept advancing ("1 / 430" -> "97 / 430" -> "121 / 430")
    canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
  Drive the shipped chrome with a worst-case frame:
    {"loaded":true,"ms":630,"clock":null,"scorebug":null,"feed_lines":0}
    canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
  ```
  `tools/ci/viewer_smoke.mjs` is **byte-identical to `templates/tools/ci/viewer_smoke.mjs`** (verified by `diff`),
  and its own header at `:140-142` says: "Only main-thread 2D contexts are seen. A viewer that draws into an
  OffscreenCanvas inside a worker reports `total: 0` — which is itself the signal that this check did not cover
  it." This bundle does exactly that: `replay-viewer/static_replay_worker.js` owns the WASM runtime and the
  OffscreenCanvas in a Dedicated Worker (`replay-viewer/static_replay.js:194` `new Worker(workerUrl, {name:
  'sokoban-static-replay'})`).
- The worst-case fixture is present and is driven by its own step, as the checklist asks. What it drives, though,
  is DOM text, not canvas text: the 140-rune `say` (`tools/ci/renderer_fixture.html:43-46`) reaches the page
  through `skFeed` (`client/sokoban_block.html:521-527`), which builds `document.createElement('div')` and hands
  it to the inherited `ctx.pushFeed(row)`. The only canvas the game block draws into is the dead-square inset
  (`client/sokoban_block.html:398-457`), which draws **no text at all** (only `fillRect`/`arc`) — deliberately,
  per its own comment at `:394-397`. So the flag is on, the number is 0, and nothing measured it. The fixture
  also never asserts its own strings survived at full length after rendering
  (`tools/ci/renderer_fixture.html:183-191` sets `data-replay-loaded` on the *absence of a thrown exception*).
- Checklist item 15, quoted, both ways: "For a **fixed arena** … `never_inside` must be **0**, and `ci.yml`'s
  smoke step must carry `--strict-text-bounds`" — literally satisfied (0, and the flag is on both steps). And:
  "`total: 0` means the check covered nothing (a worker/OffscreenCanvas or WebGL renderer) and is not evidence of
  anything", plus "The fixture asserts its own strings are still full-length — one quietly shortened remark leaves
  it passing while testing nothing." I report the numbers; the judge decides which sentence governs.
- What would settle it: a fixture that renders the remark into a 2D canvas on the main thread (or a
  `viewer_smoke.mjs` that instruments the worker), and an assertion in the fixture that the rendered
  `#killfeed` row still contains all 140 runes at 360 px.

### F10 — artefacts the note names that are not in the tree
- Where: `git ls-files` at `464b2ab`
- Absent: `tests/test_sokoban_tuning.nim` (note §Tests 26), `tests/test_sokoban_endcard_labels.nim`
  (§Viewer, §Tests 46), `tests/shard_1..4.nim` and `tests/tests.nim` (§Tests preamble), `client/league_replayer.html`
  (§Kept table), `src/sokoban/roster.nim` and `src/sokoban/sim_state.nim` and `src/sokoban/rig_art.nim`
  (§Kept table, §The two named edits to `roster.nim`), `tools/expand_replay.nim`, `tools/extract_events.nim`,
  `tools/record_fixture.sh`, `flake.nix` (§Kept table), `docs/MAPKIT.md`-adjacent tooling (correctly deleted).
- Observed mitigations: the endcard-label assertions live in `tests/test_sokoban_viewer.nim:221-248`; the tuning
  assertion in `tests/test_sokoban_events.nim:143-160`; `seatAlias`/`ladderResultsJson` live in
  `src/sokoban/sim.nim:105-109` and `:440-526` rather than a `roster.nim`. `.github/workflows/ci.yml:117-119`
  runs `ls tests/*.nim`, so the absent shard files skip nothing — every committed test file runs, in debug and
  in `-d:release`.

### F11 — shipped sweep sizes and the baseline-strength band are smaller/wider than the note's
- Where: `tests/helpers.nim:11-17`, `tests/helpers.nim:89-91`, `tests/test_sokoban_baselines.nim:209-218`,
  `tests/test_sokoban_sim.nim:472-487`
- Observed:
  - `const SweepSeeds* = when defined(release): 8 else: 2` (`helpers.nim:11`) with a comment that names the
    divergence: "the design note asks for 5 000-seed sweeps."
  - `const SampleStates* = when defined(release): 60 else: 12` (`helpers.nim:89`).
  - The strength gate is `low = [45, 10, 0]`, `high = [100, 65, 30]` (`test_sokoban_baselines.nim:214-215`),
    against the note's 0.60–0.95 / 0.15–0.55 / 0.00–0.20. The comment at `:209-213` states the widening and why.
  - The no-float test (`test_sokoban_sim.nim:472-487`) greps for `float`, `sqrt` and `.0` but **not** for `/`,
    which the note's test 12 names. (I checked: `src/sokoban/{sim,grid,deadlock,levelgen,search,driver,baselines}.nim`
    contain no `/` division on the paths I read; `server.nim:199` does use `/` for the lobby seconds, and
    `server.nim` is not in the note's no-float list.)
- These are all in the initial test commit; nothing was loosened after the fact (see checklist item 1 below).

### F12 — `replays.nim` / `replay_runtime.nim` are new implementations, not the "magic + game name only" fork the note claims
- Where: `src/sokoban/replays.nim` (305 lines) vs `/workspace/starters/coworld-ctf/src/ctf/replays.nim` (943);
  `src/sokoban/replay_runtime.nim` (343) vs the starter's (142)
- Observed: a wholly different codec — `RecordKind = {rkLevel, rkPlan, rkChat, rkStop}` (`replays.nim:27-31`),
  a bespoke little-endian writer/reader, no keyframes, and a `seekReplay` that rewinds to tick 0 and re-steps
  (`replay_runtime.nim:145-150`) rather than the starter's keyframe cache. The module header at `replays.nim:1-17`
  documents the rewrite honestly.
- What the note says: §Kept table — "`src/ctf/replays.nim`, `replay_runtime.nim` → `src/sokoban/`: **fork (magic +
  game name only:** `CtfReplayMagic = "COWLDCTF"` → `SokobanReplayMagic = "COWLDSOK"`) … the whole replay codec,
  keyframes, the incremental scan, lull spans, beat events, seek/speed/transport commands, `checkReplayHash`".
  Elsewhere the same note requires per-level XSB records and per-turn plan records that the starter's format has
  no place for, so the note is internally inconsistent here; the code is the coherent half.
- One concrete consequence in the new parser: `replays.nim:250` `record.plan.source = DirectiveSource(cursor.readU8())`,
  `:254` `action.kind = ActionKind(cursor.readU8())`, `:257` `action.dir = Dir(cursor.readU8())` convert an
  unvalidated 0..255 byte to a 3- or 4-value enum. The tier field on the same path *is* validated
  (`:235-237` raises "unknown tier in replay level record"). In a `-d:release` viewer build (checks off) a
  corrupt byte is an out-of-range enum rather than a raised `SokobanError`.

### F13 — the tier-2 analysis stream emits 3 of its 11 declared kinds
- Where: `src/sokoban/events.nim:12-25` declares `LevelStart, TurnStart, Directive, Fallback, Move, Push, BoxOn,
  BoxOff, Deadlock, Solved, Failed`; `src/sokoban/server.nim:299`, `:317`, `:325` are the only `log.add` call
  sites in the repo (grep for `se[A-Z]` across `src/` and `tests/`), emitting `seLevelStart`, `seTurnStart`
  and `seMove` only.
- What the note says: §Record and event vocabulary C names the full reduced vocabulary as what
  `COGAME_EVENTS_URI` receives, and calls `Move` "the per-tick row that makes this stream a full action trace for
  `cogamer-rl`". `Push`, `BoxOn`, `BoxOff`, `Deadlock`, `Solved`, `Failed`, `Directive` and `Fallback` rows are
  never written. `tests/test_sokoban_events.nim:93-101` checks only that the *enum names* match the note's list,
  not that any is emitted.
- The mandatory trailing summary row is present and asserted (`events.nim:41-53`, `test_sokoban_events.nim:78-92`).

### F14 — playback cadence, speed chips and interpolation differ from the note
- Where: `src/sokoban/replay_runtime.nim:12-20`, `src/sokoban/sim_types.nim:53-56`, `src/sokoban/global.nim:274-288`
- Observed:
  - `ReplayFps* = 24`, `FramesPerTick* = 2` → one tick every two presentation frames at 24 fps = **12 ticks/s**;
    a 1 200-tick episode plays for 100 s. The note's §Transport says "one tick per three animation frames at
    30 fps = 10 ticks/second … A 1 200-tick episode plays for **120 s**". The code's own comment states 12/100 s,
    and `ci.yml:326` repeats it. Either way the CI replay (430 ticks ⇒ ~36 s) comfortably outlasts `--soak 10`,
    which the job log confirms.
  - `PlaybackSpeeds* = [1, 2, 4, 8]` (`sim_types.nim:53`), published to the chrome as `SOKOBAN_WIRE.speeds`
    (`wire_constants.nim:25`). The note's §Transport says `[0.5, 1, 2, 4, 8]`. `applyReplayCommand`
    (`replay_runtime.nim:270-273`) handles exactly `'1' '2' '4' '8'`, so the shipped set is self-consistent.
  - `buildViewerPacket` places the cog and the crates at exact `cellX(cell) * CellPixels` every frame
    (`global.nim:277-288`); there is no sub-tick interpolation anywhere. The note's §Transport asks for "the cog's
    position and any pushed box interpolated across the three frames so a push glides instead of snapping".

### F15 — the deadlock flash is a banner and a feed line, not a board effect
- Where: `client/sokoban_block.html:559-566`
- Observed: on a `deadlock` event the block pushes a feed row and calls `ctx.banner('DEADLOCK CREATED — CRATE
  CORNERED AT (x,y)')`; the scrubber beat is drawn from the pre-scan (`replay_runtime.nim:200-205`,
  `sokoban_block.html:257-284`) with the tallest/reddest CSS rule (`:168-173`).
- What the note says: §Readouts 3 — "the offending box is **ringed in red**, the **cell flashes twice**,
  `#bannerlane` reads … for two seconds, and the scrubber gets its `.deadlock` beat." The ring and the flash are
  not drawn; nothing in `global.nim` or the block emits them. `tests/test_sokoban_viewer.nim:254-257` asserts the
  string `DEADLOCK CREATED` is in the block, not that anything is drawn on the board.

### F16 — `results.names` carries the policy label, not a player name
- Where: `src/sokoban_player.nim:38-45`, `src/sokoban/server.nim:504-527` (`:522-525`), `src/sokoban/sim.nim:453`
- Observed: the registration blob the player sends is exactly
  `{"policy": <PLAYER_POLICY_LABEL|"llm"|<scripted>|"pusher">, "prompt": …, "scripted": …}` — **no `name` key**
  (`sokoban_player.nim:38-45`). `applyRegistration` reads `payload{"name"}` (`server.nim:522`) and, finding it
  empty, sets `shared.names[slot] = shared.policies[slot]` (`:524-525`). `ladderResultsJson` then emits that as
  `results.names[0]` (`sim.nim:453`). CI confirms it: the wasm-viewer scorebug read `ALPHA pusher SCORE 1050143`.
- What the note says: §Seats and aliases — the seat's "real policy/player name (`daveey`, `daveey-1`,
  `Baseline (1)`) lives only in `results.names`, in the replay's join record, and spectator-side in the viewer's
  scorebug plate"; §Results shows `"names": ["daveey"]`.
- Checklist item 4 is still satisfied on its own terms: two distinct name spaces exist and are separated —
  the alias `Alpha` is all the model ever sees (`tests/test_sokoban_obs.nim:98-109` asserts no policy name reaches
  the observation), and a different, spectator-only name is on the plate (`broadcast.nim:19-22`,
  `sokoban_block.html:291-296`). What differs from the note is *which* name that is.

### F17 — `game.docs` uses `"type":"uri"`, the checklist spells `"type":"text"`
- Where: `coworld_manifest_template.json` → `game.docs`
- Observed:
  ```json
  "docs": {"readme": {"type": "uri", "value": "https://github.com/Metta-AI/cogame-sokoban/blob/main/README.md"},
           "pages": [{"id": "rules.md", "title": "Rules",
                      "content": {"type": "uri", "value": ".../docs/RULES.md"}}, … 3 pages]}
  ```
  All four targets exist in the tree (`docs/RULES.md`, `docs/ACTIONS.md`, `docs/LEVELS.md`, `README.md`).
  `tests/test_sokoban_manifest.nim:63-75` asserts the *shape* (`readme` an object, three pages, each with `id`,
  `title` and an object `content`) but not the `type` value.
- Checklist item 10, quoted: "`game.docs` is
  `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`".
- Counter-evidence the judge should weigh: the starter does the same —
  `/workspace/starters/coworld-ctf/coworld_manifest_paintbot.json` `game.docs.readme` is
  `{"type":"uri","value":"https://github.com/Metta-AI/coworld-ctf/blob/master/README.md"}` — and the design note
  §Packaging specifies `uri` deliberately. The structural half of item 10 (`game.protocols` carrying **both**
  `player` and `global` as `{"type","value"}` objects) is satisfied and asserted
  (`test_sokoban_manifest.nim:63-68`).

### F18 — the action parser accepts `do` spellings outside the note's enum
- Where: `src/sokoban/directives.nim:134-142`
- Observed: `case doText of "moves", "move", "seq": akMoves; of "push": akPush; of "goto", "go": akGoto;
  of "wait", "": akWait; else: return (false, Action())`. An empty/absent `do` becomes a `wait` rather than a
  dropped entry.
- What the note says: §Reply schema — `actions[].do` is "enum `moves` | `push` | `goto` | `wait`, lower-cased
  before matching". This is tolerance in the policy's favour, not a rewrite of an action into a different one
  (§Turn 6b's rule holds: nothing is repaired into another push), but it is a wider domain than the note declares
  and than `docs/ACTIONS.md` will tell a policy author.

### F19 — `settle` and `finishEpisode` sit outside the fault handler
- Where: `src/sokoban/server.nim:276-355`
- Observed: the `try:` block spans the turn loop `:277-340` and its `except CatchableError` (`:341-345`) sets
  `reason = endFault`. `writer.writeStop` (`:347-349`), `gameSim.settle` (`:350`) and `finishEpisode` (`:351`)
  are **after** the handler. `finishEpisode` → `writeArtifact` (`:106-118`) raises `IOError` on a non-2xx POST
  (`:116`), and `writeCogameUri` can raise too; an exception there propagates out of `runGame` on the game
  thread with no results and no replay written.
- What the note says: §End conditions, `fault` — "Caught; the episode is settled from the last completed tick …
  **artifacts are still written, exit 0**."

---

## Traced and consistent

Each line says what I opened and what I checked.

**Checklist 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-sokoban --branch main -w ci.yml` → run **33243111396**, conclusion
  **success**, at the reviewed sha `464b2ab`; jobs `test` (11m6s), `docker-smoke` (1m29s), `wasm-viewer`
  (2m25s) all green. The preceding run 33241703242 failed on the `feat` commit and was fixed by the two
  follow-up commits.
- `git log --stat -- tests/` shows tests added once, in `3724a05`, and `git log -p 3724a05..HEAD -- tests/`
  is **empty** — no test file was changed, skipped, widened or removed after it landed. `ci.yml:104-150` runs
  every `tests/*.nim` twice (debug and `-d:release`) and exits non-zero on any failure; there is no `skip`,
  `xfail` or `--skip` anywhere in `tests/`.

**Checklist 2 — replay re-derivation, frame by frame, and the viewer derives from it.**
- `tests/test_sokoban_replay.nim:96-113` re-simulates from the bytes and asserts
  `data.hashes[game.tick - 1] == game.gameHashValue` on **every** tick, plus final tick / levels solved / box
  credit. `:18-42` repeats the record → re-derive check for all four end rules (`ladderComplete`, `turnCap`,
  `wallClock`, `fault`) and asserts `player.hashMismatchTick == -1` and identical results JSON — the wall-clock
  stop is a real record (`replays.nim:187-192`) applied by the same proc on record and playback
  (`replay_runtime.nim:112-116` → `sim.settle`).
- The viewer's display comes from that re-derivation and nothing else: `replay-viewer/sokoban_replay.nim:95-108`
  → `advanceReplayFrame` (`replay_runtime.nim:297-339`) → `stepReplay` → `sim.stepTick` → `buildStateJson`
  (`broadcast.nim:85-187`). There is no parallel recording; `test_sokoban_replay.nim:92-94` even asserts
  `"generateLevel" notin` the runtime source.

**Checklist 3 — static viewer.**
- `coworld_manifest_template.json` → `game.replay_viewer == {"bundle": "static-replay-viewer"}` under `game`,
  asserted at `tests/test_sokoban_manifest.nim:77-82` (which also asserts no top-level `replay_viewer`).
- `tools/build_replay_viewer.sh` is committed **100755** (`git ls-files -s`), asserted for presence *and* the
  exec bit by `ci.yml:233-244`, and invoked by path at `:257`. Its `docker cp` source is
  `/workspace/sokoban/replay-viewer/dist/.` (`:57`), matching `Dockerfile.replay-viewer`'s `WORKDIR`.
- The bundle fetches only its own origin + the replay URL: `replay-viewer/static_replay.js` is the starter's file
  with two identifier renames (full `diff` below), and `static_replay_worker.js` `importScripts` three local files.
- On the literal phrase "No `/client/replay` pod path anywhere": the *game server* serves `/client/replay`
  locally (`src/sokoban/server.nim:589`, linked from the seat page at `:410`). The starter does the same
  (`coworld-ctf/src/ctf/server.nim:631,646,844`) while shipping a `static-replay-viewer` manifest, and the design
  note §Viewer says so explicitly ("the game still serves `/client/replay` locally for developers"). Nothing is
  declared to the platform.

**Checklist 4 — both name spaces.** Alias side: `seatAlias` (`sim.nim:105-109`) → `"Alpha"`; the observation's
`"you"` is the alias (`sim.nim:574`); `tests/test_sokoban_obs.nim:98-109` asserts `sokoban-lookahead`,
`lookahead` and `daveey` are all absent from the serialised observation; `showPlayerLabels: false` in every
variant. Spectator side: `rosterJson` emits `name` (real) and `alias` separately (`broadcast.nim:13-32`); the
plate writes `name` into `#name-red` and the alias into `.sk-alias` (`sokoban_block.html:291-322`). See F16 for
*which* real name it is.

**Checklist 5 — degrade-never-hang; every wait bounded.** I enumerated every wait:
- Lobby: `server.nim:199-208`, bounded by `lobbyJoinTimeoutTicks / TargetFps` = 2400/24 = 100 s, `sleep(200)` poll.
- Register grace: `server.nim:210-219`, `min(now + 4 s, connectDeadline + 4 s)`, `sleep(100)` poll.
- Turn spacing floor: `decide.nim:212-216`, `sleep(min(turnSpacingMs, turnSpacingMs - since))` ≤ 2 600 ms, and it
  runs *after* the budget guard.
- LLM attempt 1: `attempt1Ms` = 6 000 ms via `makeRequests(batch, deadlineMs div 1000)` (`decide.nim:249-250`).
- Retry: exactly one, `retryMs` = 3 000 ms; the loop is `while attempt < 2` (`decide.nim:223`), with an outer
  monotonic `turnBudgetMs` check before each attempt (`:226-229`). `attempt1Ms + retryMs == turnBudgetMs` and
  `sim_config.validate` (`sim_config.nim:136-143`) rejects a config where it does not.
- Rate guard: `decide.nim:126-136`, rolling 60 s counter, cap 28, no sleep.
- Budget guard: `decide.nim:174-181`, fires when `elapsed + 2 × ceil(turnBudgetMs/1000) > wallClockBudgetSeconds`.
- Engine stop: `server.nim:280-286`, checked at the top of every loop iteration, `690 s`.
- Tick loop: `while not gameSim.turnComplete()` (`server.nim:320`); `turnComplete` is
  `turnEnded or queueIndex >= turnMoves` (`sim.nim:383-384`) and `stepTick` increments `queueIndex` on every
  non-early-return path, and its only early return (`sim.nim:304-305`) requires `turnEnded` or
  `not levelActive` — and `finishLevel` always sets both together (`sim.nim:238-239`, `:357-381`). Bounded at 20.
- Generator: `genNodeCap` 200 000 dequeues × `genAttemptCap` 8 (`levelgen.nim:148`, `:243`).
- Search: `params.nodeCap` expansions (`search.nim:135`).
- Replay scan: `while sim.phase != phGameOver and sim.tick < 100_000` (`replay_runtime.nim:170`) plus a
  no-advance guard (`:128-133`).
- Shutdown grace: `sleep(20 s); quit(0)` (`server.nim:354-355`).
- `episodeTimeoutSeconds` arithmetic: `episode_timeout_minutes: 20` ⇒ 1 200 s; every
  `wallClockBudgetSeconds ≤ 690 ≤ 720 = 60 %`, asserted twice at `tests/test_sokoban_manifest.nim:96-103`
  (`budget * 100 <= timeoutSeconds * 60`). CI's real episode settled in **24 s** wall clock
  (`docker-smoke` log: `smoke OK: seats=1 results=924B replay=53113B reason=complete`).
- Simultaneous-decision clause: not applicable — one seat, one request, `decide.nim:242-250` posts a single
  request into the starter's `makeRequests` batch.

**Checklist 6 — `num_agents`.** `1` in `variants[0].game_config`, `variants[1].game_config` and
`certification.game_config`, never at a variant top level (asserted `test_sokoban_manifest.nim:12-24`).
`tools/ci/docker_smoke.sh:110-152` enforces all four invariants with `SEAT-COUNT FAIL:` prefixes plus the
independent `SMOKE_SEATS=1` cross-check; the file differs from `templates/tools/ci/docker_smoke.sh` **only** in
the three substituted placeholders (verified by `diff`). `grep -n "SEAT-COUNT" ` over the full 2 064-line
docker-smoke log of run 33243111396 returns **zero matches**, and the log shows
`game=sokoban seats=1 config={… "num_agents": 1 …}`.

**Checklist 7 — scripted baseline plays full episodes legally.**
`tests/test_sokoban_engine.nim:12-69` runs a full all-scripted `ladder` episode and asserts
`sim.reason == endComplete` plus all six results identities.
`tests/test_sokoban_manifest.nim:126-149` repeats it for **every** variant and the cert fixture.
Legality: `tests/test_sokoban_baselines.nim:34-58` checks every emitted action of both baselines against every
schema bound (≤ 8 actions, `box ∈ 0..3`, `times ∈ 1..8`, `seq ⊆ UDLR` and ≤ 20, empty `say`/`notes`, serialised
≤ 1024 bytes) over `SampleStates` positions; `:81-101` checks the expanded primitive queue is ≤ `turnMoves`,
every entry legal, and `queueOrWait` never returns nothing; `:103-117` asserts the fallback path and the `pusher`
baseline produce identical action JSON. Tuning: `tools/tune_baselines.nim` is committed,
`tools/ci/baseline_tuning.json` records the sweep (40 seeds, 0.6875/0.375/0.0625), and
`tests/test_sokoban_events.nim:143-160` asserts the shipped defaults equal it — not guessed. (See F6 and F11 for
the value and the widened band.)

**Checklist 8 — LLM reply handling.** Tolerant parse: `extractJsonObject` (`directives.nim:72-111`) scans for the
outermost balanced `{…}` respecting strings and escapes, falls back to first-brace..last-brace, and is asserted
against fences + trailing prose (`test_sokoban_baselines.nim:186-191`). Retry exactly once:
`while attempt < 2` (`decide.nim:223`). Fallback is the `pusher` proc, imported not duplicated
(`decide.nim:163-171` → `sim.scriptedDirective(blPusher)` → `baselines.pusherPlan`), asserted identical at
`test_sokoban_baselines.nim:103-117`. Recorded for phase 60: `fallbackRecord` (`decide.nim:68-72`) into the replay
chat stream, `results.fallbackTurns` (`sim.nim:479-482`, incremented at `server.nim:311-312`), and the two log
phrasings are distinct — `"attempt 1 failed, will retry"` at `decide.nim:276-277`, `"falling back to pusher"` only
at `:193`, `:202`, `:283`, `:288` (all genuine fallbacks, never attempt 1). `llm.nim:122-123` prints the
phase-60 phrase `"the LLM provider is unavailable"` when there are no credentials.

**Checklist 9 — rune-safe truncation.** `truncateRunes` (`sim_types.nim:185-193`) is `runeSubStr`, and it is the
single shortening primitive: `sanitizeSay`/`sanitizeNote` (`directives.nim:53-70`), the action `do`/`seq`/`dir`
caps (`:134`, `:146`, `:161`), `stopDetail` (`sim.nim:525`, `:651`), the policy label (`decide.nim:81`,
`server.nim:518`, `:523`), the fallback detail (`decide.nim:71`), the prompt (`sokoban_player.nim:34`,
`server.nim:504`, `llm.nim:281`), and every provider error body (`llm.nim:182`, `:190`, `:196`, `:212`).
`boundedRecord` (`directives.nim:214-228`) shrinks the free text rather than the serialised JSON. Test:
`tests/test_sokoban_baselines.nim:174-184` feeds 400 × U+1F9CA (4-byte) into `say` and `notes` and asserts
`runeLen == 140/320` and `validateUtf8() == -1`; `tests/test_sokoban_replay.nim:115-148` fills every capped field
to its cap with the same emoji, runs `tools/replay_summary.py`, and asserts strict-UTF-8 JSON with no lone
surrogates. See **F3** for the one byte slice I found on this path.

**Checklist 10 — manifest validates.** `game.protocols` carries both `player` and `global` as
`{"type","value"}` objects; `game.docs` has `readme` + three `pages` each with `id`/`title`/object `content`
(see F17 on the `type` value). Additionally verified: `$schema` present, five top-level `tags`,
`episode_timeout_minutes` at top level and absent from `game`, `game.tags` absent, `game.description` present,
`game.owner` present, no top-level `version`, no `game.display_name`, `config_schema.additionalProperties: false`
with `required: ["tokens","players"]` and `minItems`/`maxItems` on all four array properties
(`tokens` 1/1, `players` 1/1, `slots` 0/1, `tierLadder` 6/6), no literal `tokens` in any `game_config`,
`results_schema.additionalProperties: false` with `reason` and `endRule` enums exactly as the note specifies, and
the results key set **exactly** equal (39 = 39, empty symmetric difference) to `sim.nim`'s `ResultsKeys` and to
`ladderResultsJson`'s output — asserted at `tests/test_sokoban_engine.nim:71-87`.

**Checklist 11 — legible at 360 px.** `client/replay_broadcast.html:2954-2960`:
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`
and `:3148-3150` `@media (max-width: 640px) { .solved-label, .sk-alias, .fl-cap { display: none; } }`. Asserted
at `tests/test_sokoban_viewer.nim:142-146`. `relayout()` keeps the starter's
`--hudscale = clamp(0.5, boardW/760, 1.6)` and `#stage.tiny` at `boardW <= 620` verbatim (`:2894-2896`).
The board aspect really is 1.000 at runtime: `global.nim:229-233` declares the viewport as
`BoardPixels × BoardPixels` = 480×480, the page reads it back through `core.getTransform().nativeW/nativeH` and
feeds `syncBoardAspect` (`replay_broadcast.html:1725-1728`, the starter's own line, kept), so `BOARD_ASPECT`
leaves its 1235/659 pre-stream default on the first frame.

**Checklist 12 — release order and scaffold.** `coworld-release.yml`: `Build the Coworld manifest` (`:159`) →
`Certify locally` (`:173`, with `--timeout-seconds 300` at `:182`) → `Upload the policies` (`:216`, with a comment
stating it must precede upload-coworld) → `Upload the Coworld` (`:314`) → `Put the Coworld secret` (`:410`). All
three workflows present. `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both `100755`.
`tools/ci/policies.json` has exactly four policies: two `PLAYER_PROMPT` champions (`sokoban-lookahead`,
`sokoban-orderfirst`) with champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus two
scripted fillers (`PLAYER_SCRIPTED=pusher`, `PLAYER_SCRIPTED=nudger`) — asserted at
`tests/test_sokoban_manifest.nim:164-184`. The placeholder gate exits **1** (no matches) for
`<slug>`/`<IMAGE>`/`<SEATS>` across the five named files; the surviving angle-bracket names are exactly the
documented residue — `<cow_id>`/`<sha>` in `ci.yml:210`, `<cow_id>` in `coworld-release.yml:75,358`,
`<run_id>` in `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>` in `coworld-submit.yml:31`.

**Checklist 13 — viewer executes.**
- `wasm-viewer` `needs: docker-smoke` (`ci.yml:220`); the smoke step `Load the bundle in a real browser`
  (`:301-332`) is present, not commented, has no `continue-on-error`, and ran green in job `99075892979` with
  `{"loaded":true,"ms":565,…}` and `soak: 10s of playback kept advancing ("1 / 430" -> "97 / 430" -> "121 / 430")`.
  Playwright is pinned 1.55.0 in both places (`:295-299`).
- Both markers come from the shell's own code paths: `data-replay-loaded="true"` at
  `replay-viewer/static_replay.js:161` (inside `onWorkerMessage`'s `'loaded'` branch), `data-replay-error` at
  `:20` inside `showFailure()`. `diff` against the starter shows `static_replay.js` differs by exactly two lines
  (`ctf-static-replay` → `sokoban-static-replay`, `window.CtfStaticReplay` → `window.SokobanStaticReplay`), so
  both signals are inherited unedited.
- Lobby dwell: this replay format has **no lobby frames to dwell through**. `RecordKind` is
  `{rkLevel, rkPlan, rkChat, rkStop}` (`replays.nim:27-31`) — there is no lobby record; `writer.writeHash` is
  called only inside the turn loop (`server.nim:324`), after `gameSim.phase = phPlaying` (`:271`); and
  `newSimFromReplay` (`replay_runtime.nim:55-59`) sets `phase = phPlaying` before the first step. `startTick` is
  therefore 0 and *is* the game start (`replay_runtime.nim:243-245`), the scrubber axis `st` is 0
  (`broadcast.nim:117`), and every seek/`,`/`b` command clamps to `player.startTick`
  (`replay_runtime.nim:278-283`). The CI soak confirms the first readout is tick `1 / 430`, not a frozen dwell.
- Link flags ↔ bootstrap, same starter: `replay-viewer/config.nims` has **no** `MODULARIZE` and **no**
  `EXPORT_NAME` (verified by grep; the whole `passL` block is at `:42-54`), and
  `replay-viewer/static_replay_worker.js:188-191` sets `Module.onRuntimeInitialized`. `diff` against
  `coworld-ctf` shows `config.nims` differs only in the output name, the export symbol names and two comment
  words; `static_replay_worker.js` differs only in the `_ctf_*` → `_sokoban_*` renames and the `importScripts`
  filename. `-s ABORTING_MALLOC=1`, `--preload-file data@data`, `-s ENVIRONMENT=web,worker,node` and the 13
  exported functions are all present and all thirteen are `exportc`'d in `replay-viewer/sokoban_replay.nim`.
  Asserted at `tests/test_sokoban_viewer.nim:184-219`. The smoke's `loaded: true` is the evidence, not file
  presence.

**Checklist 14 — chrome is the starter's.**
- `client/chrome_common.js` is **byte-identical**: 40 022 bytes, sha256
  `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, identical to the starter's by `sha256sum`
  and `wc -c`. Pinned as a literal at `tests/test_sokoban_viewer.nim:15-30`. The rename is done *outside* the
  file, by aliasing `window.CTF_WIRE = window.SOKOBAN_WIRE` (`wire_constants.nim:33`).
- `client/broadcast_core.js` is *more* faithful than the note claims: `diff` against the starter is **2 lines
  removed, 12 added** — a 10-line provenance comment plus two identifier renames (`CTF_WIRE` → `SOKOBAN_WIRE`,
  and one comment path). None of the note's promised `drawRoomBed`/`drawWalls`/`drawBoxes`/… procs exist there;
  the board is drawn by the inherited sprite-protocol compositor from `global.nim`'s packet, which is the
  starter's own mechanism. `pushFeed`'s signature is untouched (it takes a node; `sokoban_block.html:521-527`
  builds a node and hands it over, exactly as the starter's callers do).
- `client/replay_broadcast.html` is the starter's page plus a game block under the banner
  `SOKOBAN additions to the inherited coworld-ctf chrome` at `:2928`. Prefix diff evidence and the removal audit
  are in **F8**. Sections 1–5 are present: `#stage`/`#board`/`#viewport`, `#scorebug` with `#plates-l`/`#plates-r`/
  `#clock`, `#bannerlane`, `#killfeed`, `#transport` in full (all 13 ids), `#scrub` with `#momentum`/`#lulls`/
  `#scrub-fill`/`#scrub-win`/`#scrub-head`, `#endcard` with its five children, and the `#lockerroom` curtain —
  all 49 kept ids asserted present and all 13 removed ids asserted absent at
  `tests/test_sokoban_viewer.nim:157-182` (I re-ran the greps by hand and confirm the counts).
- Transport rules (a)–(d):
  (a) `relayout()` (`:2860-2904`) does `var root = document.documentElement;` and
  `root.style.setProperty('--hudscale'|'--topband'|'--band', …)` — on `:root`, not `#stage`.
  (b) Every game-block absolute element anchors to the *top* band: `#sk-ribbon` and `#sk-pips` use
  `top: calc(var(--topband, 0px) + …)` (`:2994`, `:3010`) and, under `.tiny`, `bottom: calc(var(--band, 0px) + 124/112 …)`
  (`:3122`, `:3126`) — i.e. they ride *above* the band, never inside it. Asserted `:134-140` of the viewer test.
  (c) `#endcard { … bottom: var(--band, 0px); … }` (`:830`), shown with `#endcard.on { display: flex }`
  (`:841`), and the inherited `else { $('endcard').classList.remove('on'); }` (`:1760`) runs on every frame
  *before* the game block (`:1763`), and the block only re-adds `on` when `s.ph === 'gameover'`
  (`sokoban_block.html:605`). A seek re-simulates to a non-gameover phase, so the card comes down.
  (d) Beats are real `<button>`s with `title` + `aria-label` that seek on click via `ctx.send('s:' + tick)`
  (`sokoban_block.html:257-273`), built by `skBeat` — never `markBeat` — with the `sk-` prefix rationale in the
  banner comment, and asserted at `tests/test_sokoban_viewer.nim:70-92`, `:116-121`. CSS exists for exactly the
  seven kinds `BeatKinds` declares and no others (`sokoban_block.html:161-173`), machine-checked by extracting
  every `.beat-marker.<kind>` from the page and comparing the sorted set to `sim.nim:667-668`
  (`test_sokoban_viewer.nim:94-114`). I re-ran that grep: `{levelstart, boxon, solved, failed, fallback, end,
  deadlock}` — exact match.
  One residue: the *inherited* `case 'kill'/'steal'/'return'/'capture'` branches still call `markBeat`
  (`replay_broadcast.html:2203-2206`) and their CSS was cut. Those kinds are not in this game's closed event
  enum (`sim.nim:663-665`) and cannot be emitted, so the branches are unreachable; I note it as dead inherited
  code, not a finding.
- `#viewpanel` + minimap: removed as a fixed arena should. `id="viewpanel"`, `id="minimap"`,
  `id="minimap-canvas"`, `id="zoombar"`, `id="zoom-*"` appear **nowhere** in the page (only two prose mentions in
  the banner comment at `:2932-2933`), and `core.attachMinimap(...)` has no call site in the page. The
  `attachMinimap`/`drawMinimap` definitions remain inside `broadcast_core.js` because that file is kept
  byte-for-byte; the design note §Viewer states this and notes `minimapSurface` stays null and `drawMinimap()`
  returns on its first guard — I read `broadcast_core.js:550-565` and confirm the guard.

**Other things I traced and found consistent with the note**
- The tick physics matches §Turn and tick structure step for step: `sim.nim:300-381` — `tick`/`levelMove`
  increment, pop-or-`wait`, wall → `blockedMoves`, box-with-blocked-beyond → `blockedMoves`, box-with-free-beyond
  → push + `boxon`/`boxoff`, else walk; `levelBoxesPlaced` as a running maximum (`:351-354`); termination
  evaluated only when `boxMoved` in the order solved → deadlocked (`:356-368`); the step cap checked on every
  tick (`:370-373`); hash mixed and appended (`:375-377`); early break (`:379-381`).
- `computeGameHash` (`sim.nim:148-173`) mixes exactly the fields, in exactly the order, §Determinism point 5
  lists.
- The deadlock detector is the ordered disjunction the note specifies (`deadlock.nim:83-110`), with the
  dead-square fixpoint computed from walls and targets only (`:22-53`) — I checked the pull relation
  (`c-d` floor **and** `c-2d` floor) matches, and I reasoned through the 2×2 frozen-block test: every push of a
  box inside a fully-occupied 2×2 requires standing on another cell of that block, so the block is genuinely
  immovable and the test is sound. `tests/test_sokoban_sim.nim:267-281` is the soundness test (never flags a
  position drawn from the generator's own backward BFS, all of which are solvable by construction), and
  `:176-206` brute-force-checks the dead-square flood against exhaustive search on small boards.
- Scoring (`sim.nim:402-434`) is `1_000_000×solvedWeight + 10_000×boxCredit + movesSavedTotal`, every term
  additive, no deadlock penalty; `win[0] = solvedWeight >= parWeight` (`:429-430`); `winner` is `0` or `null`
  (`:488`). Asserted analytically and over 500 randomised end states at `tests/test_sokoban_sim.nim:364-433`.
- Level purity: every draw is `mix64(seed, levelIndex, attempt, salt)` (`levelgen.nim:30-44`), never a consumed
  stream; `backwardBfs`'s `Table` is used only for membership, never iterated, so determinism holds.
  `tests/test_sokoban_levelgen.nim:41-56` asserts levels are identical under different play.
- Observation hides the seed, future levels, the solution and the score; `pushes_available` carries no deadlock
  annotation (`sim.nim:562-568`, asserted `test_sokoban_obs.nim:58-77` including the `entry.len == 3` check).
- Replay writer (`replays.nim:141-203`): header (magic, format version, gameName, gameVersion, protocol, resolved
  config JSON), body (level / plan / chat / stop records), then the hash array. `configJson`
  (`sim_config.nim:150-191`) carries all 23 keys the note's §Server config row lists — asserted by name at
  `tests/test_sokoban_replay.nim:53-59`.
- `tools/replay_summary.py` is Python-3-stdlib-only, brace-matches the config JSON and emits the documented shape
  (`:179-194`), exercised end-to-end at `tests/test_sokoban_replay.nim:115-148`.
- `Dockerfile` builds both binaries and `WORKDIR /workspace/sokoban` with `data/` copied alongside
  (`Dockerfile:59-64`), so `levelgen.loadFallback`'s relative `data/levels/fallback_<tier>.xsb`
  (`levelgen.nim:20`, `:204-211`) resolves in the container.
- `websocketHandler` keeps the `Ping → send(data, Pong)` branch with no `kind` guard (`server.nim:544-546`);
  `/client/player` is token-checked and does not open a socket (`:392-411`); the player socket 403s on a bad
  token (`:454-458`); the certifier probes are registered before the catch-all asset route (`:584-594`);
  global broadcasts are fire-and-forget (`:120-132`).

---

## Could not determine

- **Whether F3's byte slice can actually put a split codepoint in a shipped replay.** It needs a provider reply
  whose text exceeds 4 096 bytes and whose cut lands mid-codepoint *inside* a `say`/`notes` string that still
  parses. What would settle it: a unit test that feeds `LlmClient.textOf` a synthetic 4 097-byte body with a
  4-byte emoji straddling byte 4 096 and asserts `validateUtf8()` on the resulting `directive.say`.
- **Whether the shipped `client/replay_broadcast.html` is reproducible from the starter revision it was actually
  forked from.** The mounted starter has moved (F8). What would settle it: the starter sha the fork was taken at,
  recorded in the repo, and a CI step that runs `scripts/build_broadcast_page.py` against it and `diff`s.
- **Whether the level-generation budget holds in a debug CI build.** `helpers.nim:11-17` says six levels measure
  ~2.8 s release / ~6.8 s debug, and `tests/test_sokoban_sim.nim:488-491` gates a whole episode at `< 10.0 s`
  CPU — looser than the note's "< 1 s in a release build" (§Tests 13). The `test` job took 11m6s, which is
  consistent but not a measurement of the per-episode figure. What would settle it: the per-test timings from the
  `test` job's `::group::` output, which I did not fetch.
- **Whether `never_inside` would be 0 if the check could see the worker's canvas.** F9's number is 0 because
  nothing was measured, so the check tells us nothing either way about the board's own drawn text (level ribbon
  and pips are DOM; the inset draws no text; the scorebug and feed are DOM). What would settle it: a
  main-thread-canvas fixture, or instrumenting `OffscreenCanvasRenderingContext2D` inside the worker.
- **`results.names` on the real platform.** F16 is what the code does with the registration blob the shipped
  player sends; whether the platform injects a player name by some other route (an env var the player container
  could forward as `name`) I could not determine from this repo. What would settle it: a prod `results.json` from
  a league episode, or the runner's player-env contract.
