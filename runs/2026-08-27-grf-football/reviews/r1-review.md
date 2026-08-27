# r1 review — grf-football

Repo: `/workspace/cogame-grf-football` at `66093e57cc722ba4a604c30473e730abe14b35de` ("GV3: the
wall-clock stop is a load-bearing RECORD, not a bank").
Starter: `/workspace/starters/coworld-ctf` (read-only).
Design note: `/workspace/coworld-builder/runs/2026-08-27-grf-football/design.md` (byte-identical to
the repo's own `docs/plans/2026-08-27-grf-football-design.md` — verified by `diff`, exit 0).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Files read: 48 (every `src/grf_football/*.nim`, every `tests/*.nim`, all four `replay-viewer/*`,
`client/{chrome_common.js,replay_broadcast.html}`, the manifest, `tools/ci/*`, all three workflows).
CI evidence: `gh run list -R Metta-AI/cogame-grf-football --branch main -w ci.yml` and
`gh run view 33053836802 --log`.

This is a neutral trace. Every finding is numbered F1…F21, cites `file:line`, says what the code
does and what the design note says it should do, and names the checklist area it touches. I do not
rank severity; the categorisation below each finding is the checklist area only. `observed` = I read
it; `inferred` = I reasoned from what I read; `untested` = it would take a run to settle.

---

## Findings

### F1 — The reviewed sha's CI docker-smoke episode ends `deadline`, not `complete`; render costs ~124 ms/tick
*Checklist area: 5 (degrade-never-hang / timeout), 7*

- Where: CI run `33053836802` (the reviewed sha), job `docker-smoke`, step `Raw-Docker episode
  smoke`; the numbers are produced by `src/grf_football/server.nim:853-857` and the stop by
  `src/grf_football/server.nim:700-715`.
- Observed, verbatim from the log:
  ```
  grf-football config: … maxTicks=1440 turnTicks=240 turnSpacingMs=0 halfTicks=720
                        wallClockBudgetSeconds=180 fastMode=true
  grf-football: tick  240 budget: sim 0 ms, render  36346 ms, limiter 42 ms, elapsed  36s
  grf-football: tick  720 budget: sim 0 ms, render  92562 ms, limiter 42 ms, elapsed  93s
  grf-football: tick 1440 budget: sim 0 ms, render 178262 ms, limiter 42 ms, elapsed 179s
  grf-football: wall-clock budget reached at 180s; stopping
  game over: deadline/wall_clock 0-0
  grf-football: tick 1680 budget: sim 0 ms, render 206299 ms, limiter 42 ms, elapsed 207s
  smoke OK: seats=8 results=708B replay=122226B reason=deadline
  … "reason":"deadline","endRule":"wall_clock","finalTick":1804 …
  ```
- Traced: `sim` is 0 ms; the entire cost is `render`, i.e. the eight `buildSpriteProtocolPlayerUpdates`
  calls at `server.nim:772-787`. 178262 ms / 1440 ticks ≈ **124 ms per tick**, three times the 41.7 ms
  frame budget — which is why `limiter` is 42 ms total (the limiter never waits;
  `runFrameLimiter` at `server.nim:331-351` breaks immediately on `elapsed >= frameDuration`).
- What the design note says: §Decisions "Cadence, batching, and the wall-clock arithmetic"
  (design.md:404-415) budgets "5760 ticks of play — fastMode, all seats report ready = **25 s**"
  and an expected total of 492 s inside 720 s. The observed cost is 1440 ticks in 179 s.
- Inferred (arithmetic, not run): at 124 ms/tick a production `match` variant (`maxTicks: 5760`,
  manifest `variants[0].game_config`) needs ≈ 714 s of render *plus* the 432 s rate floor
  (`turnSpacingMs: 18000` × 24 turns, slept on the game loop at `decide.nim:399-405`), so it cannot
  reach full time before the 690 s stop at `server.nim:702`.
- Also observed: the budget guard did **not** fire in this episode. `grep -i "budget guard"` over the
  whole run log matches only the `test` job's unit test (`tests/test_engine.nim:126-144`), never
  `docker-smoke`. The guard's condition is `elapsedSeconds + 2 * perTurn > budget`
  (`decide.nim:347`) evaluated only at a turn boundary; with `turnSpacingMs = 0` the fixture's
  `perTurn` falls back to `turnBudgetMs/1000 = 10` (`decide.nim:325-329`), so the guard needed
  `elapsed > 160 s` at a turn boundary and the boundaries landed at ≈151 s and ≈179 s.
- Also observed: after the stop the loop ran ~360 more ticks of game-over hold
  (`gameOverTicks` default 360, `sim_types.nim:157`; `sim.step` GameOver branch at `sim.nim:1280-1282`)
  before `writeArtifacts()` at `server.nim:839-841`: the log shows `tick 1680 … elapsed 207s` and
  `finalTick: 1804`, i.e. ≈42 s of tail **after** the budget stop. Inferred: 690 s + ≈43 s = ≈733 s,
  past the 720 s settle requirement.
- Context (observed, outside the reviewed sha): main has since advanced to `c5cdc01`
  ("render: the rig sprite's label was making it redefine itself every frame", run `33054781746`,
  green). Its docker-smoke log reads `render 5460 ms` at tick 1440, `game over: complete/full_time`,
  `smoke OK: … reason=complete`. So the render cost is a property of this sha specifically.
- `tools/ci/docker_smoke.sh` does not gate on `reason`: it prints it
  (`docker_smoke.sh:306-308,324`), which is why `reason=deadline` went green.

### F2 — `tests/test_perf.nim` measures physics + control only, not the serve path its docstring names
*Checklist area: 5*

- Where: `tests/test_perf.nim:1-22`.
- Observed: the docstring says "A whole match of physics **plus the control layer**… 5760 ticks in
  under 120 s", and the body calls `runScriptedMatch(config)` (`tests/lib/helpers.nim:67-108`), which
  steps the sim and compiles actions but never calls `buildSpriteProtocolPlayerUpdates`,
  `stepEvents` or `buildStateJson`.
- Design note §Sim module (design.md:665-666): "Perf target: 5760 ticks of physics **plus serve** in
  under 30 s on a CI runner; `tests/test_perf.nim` bounds it at 120 s." Observed: the serve half is
  not in the measurement, so the 124 ms/tick render cost in F1 is outside this bound.
- `tests/test_replay.nim:117-186` (`theRenderPathDoesNotPerturbTheSim`) *does* exercise the render
  path, but asserts determinism, not time.

### F3 — `canvas_text` is structurally blind here: the board renders in a Worker/OffscreenCanvas, so `--strict-text-bounds` gates a count that is always 0
*Checklist area: 15 (legibility)*

- Where: `.github/workflows/ci.yml:450-454` passes `--strict-text-bounds`;
  `tools/ci/viewer_smoke.mjs:140-142` states "Only main-thread 2D contexts are seen. A viewer that
  draws into an OffscreenCanvas inside a worker reports `total: 0` — which is itself the signal that
  this check did not cover it."; the board is drawn in the Worker
  (`replay-viewer/static_replay_worker.js:65-103`, `core.attachMinimap`/`createBroadcastCore` inside
  the worker; the page transfers its canvas across).
- Observed in CI (run `33053836802`, step `Load the bundle in a real browser`):
  ```
  {"loaded":true,"ms":590,…,"feed_lines":0}
  canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
  ```
- Design note §Viewer (design.md:950-952): "the pitch is a **fixed arena** … `viewer_smoke.mjs`
  therefore runs with `--strict-text-bounds`." The flag is present as the note requires; the observed
  `total: 0` is what the checklist calls "not evidence of anything".
- `tools/ci/viewer_smoke.mjs` is byte-identical to
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff`, no output) — no
  substitutions, as the note requires.

### F4 — No worst-case renderer fixture; model-authored text reaches the DOM, not the canvas
*Checklist area: 15*

- Where: no such fixture or `ci.yml` step exists (`.github/workflows/ci.yml` has four jobs:
  `test`, `docker-smoke`, `replay-rehash`, `wasm-viewer`; no fixture step).
- Observed on the draw path: the Nim renderer draws no model text. `src/grf_football/labels.nim:13-56`
  enumerates the complete sprite vocabulary (`pitch`, `ball`, `ball shadow`, `cog`, `shirt number`,
  `seat ring`, `own cog`, `own seat`, `ball trail`, `play arc`, `goal flash`, `goal confetti`) and
  `grep -n "say\|note\|bubble\|drawText\|activeDirective" src/grf_football/global.nim` returns
  nothing. `note`/`say` are rendered as DOM feed rows through
  `client/replay_broadcast.html:3008-3021` (`feedRow(... CTX.esc(d.note) ...)` →
  `CTX.pushFeed`), inside `.feed-row` CSS at `client/replay_broadcast.html:488-522`.
- Design note §Viewer readout 3 (design.md:977-980) places `note` and `say` in `#killfeed`, i.e. the
  DOM feed. So the design does not claim canvas-drawn model text.
- Could not determine whether the checklist's "viewer draws LLM-authored text" clause binds when the
  text is DOM rather than canvas; I record the observation and leave the categorisation.
- Related observation: the CI smoke reports `feed_lines: 0`. The scripted `zonal` baseline *does*
  emit a fixed `note` and `say` (`src/grf_football/baselines.nim:52,68,75,78,81`), and
  `broadcast.applyRecord` folds them into `sim.feed`
  (`src/grf_football/broadcast.nim:200-217`) — but `grep -n "s\.feed"` over
  `client/replay_broadcast.html` finds **no consumer**: the DOM feed is fed only by `applyEvent`
  (line 1942ff) and by the appended block's `fbDirectives(s)` reading `s.directives`
  (line 3000-3023). `feed_lines: 0` was sampled on the first drawn frame, so I could not
  distinguish "timing" from "`sim.feed` is never rendered". Untested.

### F5 — Error text on the path to the replay is byte-sliced before it is rune-clipped
*Checklist area: 9 (rune-safe truncation)*

- Where: `src/grf_football/llm.nim:168` (`body[0 .. min(body.high, 400)]`), `:176`
  (`body[0 .. min(body.high, 300)]`), `:181`, `:192` (`result[0 .. min(result.high, 160)]`),
  `:201-203` (`head[0 ..< 160]`).
- Traced: each of those slices becomes a `GrfFootballError` message; `decide.nim:428-431` and
  `:460-462` put `failure.msg` into `detail`; `decide.nim:386` and `:467` write
  `"detail": clipRunes(detail, MaxDetailRunes)` into a `fallback` chat record, which
  `server.nim:533-542` (`recordAndWrite`) writes to the replay. The slice indices are **byte**
  indices on an HTTP response body / model text that may be UTF-8.
- What the design note says: design.md:776-779 — "Truncation is on rune (Unicode codepoint)
  boundaries, never bytes … Slicing a string by byte index **on any path to the replay is
  forbidden**"; design.md:770-771 names `fallback.detail` (≤ 200 runes) as one of the three further
  capped strings. `AGENTS.md` rule 2 restates it.
- Inferred, not tested: `clipRunes` (`src/grf_football/directives.nim:53-67`) re-encodes each rune it
  iterates (`clean.add($rune)`), so a mangled lead byte is likely to be *re-encoded* into valid UTF-8
  rather than passed through; but Nim's `fastRuneAt` reads the continuation bytes of a multi-byte
  lead without checking they exist, so a truncated 4-byte sequence within 3 bytes of the slice end
  indexes past `high` — an `IndexDefect` (a `Defect`, not caught by the `except CatchableError`
  handlers at `decide.nim:428`/`:460`) under the debug build the `test` job runs.
- No test covers this: `tests/test_directives.nim:112-132` and `tests/test_replay_utf8.nim:9-18`
  both feed **valid** multi-byte input at the cap (see F6). Neither feeds a byte-truncated string,
  and no test drives `llm.completionText`/`extractJsonObject` with non-ASCII.

### F6 — The multi-byte-at-the-cap tests the note promises are present
*Checklist area: 9*

- `tests/test_directives.nim:112-132`: builds a 160-rune `note` whose 160th rune is
  `"\xF0\x9F\x8F\x86"` (U+1F3C6, four bytes), clips it, and asserts `runeLen <= MaxNoteRunes`,
  `isValidUtf8(clipped)` and `clipped.validateUtf8() == -1`; then 400 consecutive emoji clipped to
  `MaxSayRunes`.
- `tests/test_replay_utf8.nim:9-18,30-36,54,72-104`: seeds the emoji on the exact boundary rune the
  clip *keeps* (`MaxNoteRunes - 2`), plus a non-ASCII `register.policy`, writes a whole episode,
  runs `tools/replay_summary.py` over the bytes, and asserts `utf8Repairs == 0`, `protocol ==
  "grf-football/v1"`, and that the emoji survived to the replay intact.
- Caps in code match the note's table (design.md:757-773): `MaxNoteRunes = 160`, `MaxSayRunes = 48`,
  `MaxPolicyRunes = 48`, `MaxDetailRunes = 200`, `MaxDirectiveRecordRunes = 900`,
  `MaxPromptRunes = 4000`, `MaxCogIdRunes = 8` (`src/grf_football/sim_types.nim:180-186`).

### F7 — Two `sim.nim` behaviours differ from the design's 12-step resolution order
*Checklist area: correctness (not a named checklist item)*

- **Possession bookkeeping.** `src/grf_football/sim.nim:1203-1207`:
  ```nim
  if sim.ball.controller >= 0:
    inc sim.teamStats[teamOfCog(int(sim.ball.controller))].possessionTicks
  elif sim.lastTouch.team >= 0:
    inc sim.teamStats[Team(sim.lastTouch.team and 1)].possessionTicks
  ```
  Design step 9 (design.md:290): "`possessionTicks[team] += 1` for the team of the **current
  controller** (nothing before the first touch)". Observed: a loose ball also credits the last
  toucher's team. (The "nothing before the first touch" half holds — `lastTouch.team` starts at −1,
  `sim.nim:161`.)
- **Out-of-play placement.** `sim.nim:1035` calls `handleOutOfPlay()` inside the four-substep loop,
  once per substep. Design step 8 (design.md:287-288) lists the out-of-play test at the *tick* level,
  after step 7's substeps. The design's "only if no goal" ordering is honoured (`sim.nim:1031-1036`
  tests `goalScoredBy` first and returns).

### F8 — `gameHash` mixes three cosmetic pool lengths the design says it never mixes
*Checklist area: 2 (replay re-derivation)*

- Where: `src/grf_football/sim_state.nim:117-119`:
  ```nim
  result.mixHashInt(sim.trail.len)
  result.mixHashInt(sim.arcs.len)
  result.mixHashInt(sim.goalFx.len)
  ```
- Design step 11 (design.md:294-297): "`gameHash` mixes tick, phase, restart state, score, and every
  cog's position, velocity, direction, modes, stamina and timers, plus the ball's position, velocity
  and `z`. It **never** mixes directives, notes, **FX or trails**." `sim_types.nim:524-527` labels
  `trail`, `arcs`, `goalFx` "never hashed". The module docstring at `sim_state.nim:5-9` repeats the
  claim.
- Traced: the three pools are appended inside `sim.step` on both sides of the boundary
  (`sim.nim:1229-1231` trail, `sim.nim:542,580,809,829,872` arcs, `sim.nim:910` goalFx) and bounded
  deterministically by `trimFx` (`sim.nim:1043-1054`), so hashing their lengths is reproducible on
  re-simulation — and the CI chain is green (F9). The observation is that the note's stated
  invariant and the code disagree. `sim.feed` is correctly not hashed.

### F9 — Replay re-derivation is implemented frame-by-frame, tested, and green in CI
*Checklist area: 2* — traced and consistent, recorded as a finding because it is the checklist's core item.

- The chain: `replays.nim:306-311` (`stepReplay` = apply events → `sim.step(recorded bytes)` →
  `checkReplayHash`) and `replays.nim:273-304` (compares `sim.gameHash()` against
  `data.hashes[hashIndex]` at **every** tick, sets `hashMismatchTick`).
- The viewer's display is derived from that same re-derived `sim`:
  `replay_runtime.nim:76-125` (`buildReplayViewerPacket` calls `sim.buildSpriteProtocolUpdates` and
  `sim.buildStateJson` on the re-stepped sim) and `replay-viewer/grf_football_replay.nim:44-47,83-99`
  (`grf_frame` → `advanceReplayFrame` → `renderCurrent`). There is no parallel recording of display
  state anywhere in the bundle.
- Tests: `tests/test_replay.nim:53-83` (1440-tick episode round-trip, `not hashValidationFailed`),
  `:117-186` (the same with the whole render path in the loop, asserted every tick),
  `:188-261` (`deadline/wall_clock`, `fault/host_error`, `fault/sim_fault` each recorded as a `stop`
  record and re-derived), `tests/test_determinism.nim:41-66`.
- CI at the reviewed sha: `replay-rehash` green, and `wasm-viewer`'s determinism gate logged
  `ok: loaded grf-679961.replay, advanced 4000 frames` and `ok: loaded replay.json, advanced 4000
  frames` — 4000 frames, not the 300 the design note names at design.md:658-659.

### F10 — The `stop` and `state` replay records are not in the design note's record vocabulary
*Checklist area: 2*

- Where: `server.nim:713-715` writes `{"k":"stop","reason":…,"rule":…,"tick":…}`;
  `broadcast.nim:226-240` applies it by calling `sim.finishGame` on both record and playback;
  `server.nim:749-752` writes `{"k":"state","t":…,"d":<stateDigest>}` every
  `StateDigestTicks = 120` (`sim_state.nim:183-188`).
- Design note §Record and event vocabulary A (design.md:864-870) lists exactly five kinds:
  `register`, `directive`, `fallback`, `budget_guard`, `result`. Design §Replay bytes
  (design.md:853) repeats "chats | `register` / `directive` / `fallback` / `budget_guard` / `result`
  records".
- Observed: `GameVersion` is `"3"` with a prepended changelog explaining both additions
  (`sim_types.nim:24-51`); the `stop` record is the documented fix for a `deadline` replay diverging
  at its stop tick, and `tests/test_replay.nim:188-261` covers it. The design note has not been
  updated to name either record.

### F11 — Chrome provenance: `chrome_common.js` byte-identical, page is the starter's with an appended block, CSS above the banner is deletions only
*Checklist area: 14* — traced and consistent.

- `diff client/chrome_common.js /workspace/starters/coworld-ctf/client/chrome_common.js` → identical.
  Pinned in `tests/test_viewer.nim:47-61` by length (40022) and FNV-1a.
- Banner at `client/replay_broadcast.html:2696-2717`
  (`GRF-FOOTBALL additions to the inherited coworld-ctf chrome`), followed by exactly one `<style>`
  (2718-2864) and one `<script>` (2865-3171). `tests/test_viewer.nim:31-35` requires the banner.
- I diffed the CSS **above** the banner (`lines 1-1165`) against the starter's (`lines 1-1459`):
  the only hunks are pure deletions — the `#fpv` block (starter 548-833) and the `#viewpanel`/
  `body[data-noviewpanel]` block (starter 1451-1459). No line above the banner is *modified*.
  These are exactly the removals design.md:938-948 lists.
- Sections present and unmodified above the banner: stage/viewport/board (77-112), scorebug
  (154-169), banner lane, kill feed, transport (552-560), scrubber + momentum + beat markers +
  lulls (623-648), endcard (750-963), locker-room curtain. Page is 3174 lines vs the starter's 4660
  — the delta is the deleted fpv/viewpanel blocks plus the deleted first-person renderer.
- Transport rules, each checked:
  (a) `relayout()` at `client/replay_broadcast.html:2641-2670` — `var root =
  document.documentElement;` then `root.style.setProperty('--hudscale' | '--topband' | '--band', …)`.
  ✔ `:root`, not `#stage`.
  (b) Nothing the appended block draws is anchored to the band: `#fb-possbar` is
  `top: calc(var(--topband, 0px) - 5 * var(--u))` (2780-2791), `#fb-goalreplay` is
  `top: calc(var(--topband, 0px) + 16 * var(--u))` (2848-2862), `#fb-half` is a child of `#clock`
  (3025-3033). `tests/test_viewer.nim:128-137` asserts `#transport` never appears below the banner.
  (c) `#endcard { … bottom: var(--band, 0px); }` at `:761`, shown with `#endcard.on` at `:772` and
  `:2256` (`card.classList.add('on')`), and removed from **state** on every non-gameover frame at
  `:1677` (`else { $('endcard').classList.remove('on'); }`) — so any seek that lands back in play
  takes it down on the next frame.
  (d) Beats are labelled buttons: `fbBeat` at `:2897-2918` builds
  `document.createElement('button')` with `type`, `className = 'beat-marker ' + kind + team`,
  `title`, `aria-label`, and a click handler that does `CTX.send('s:' + tick)`. CSS exists for every
  kind the page emits: `.gamestart` (2810), `.goal`/`.goal.red`/`.goal.blue` (2816-2818), `.shot`
  (2819-2821), `.save` (2822), `.foul` (2827), `.halftime` (2832), `.gameover` (2837).
  `tests/test_viewer.nim:104-116` pins all of it.

### F12 — Beats are drawn by the game block's own `fbBeat`, not by `chrome_common.markBeat`
*Checklist area: 14(d)*

- Where: `client/replay_broadcast.html:2897-2918` (`fbBeat`) vs `client/chrome_common.js:538-562`
  (`markBeat` / `renderBeatMarkers`, which build `document.createElement('div')` with no label and
  no click handler).
- Checklist item 14(d) names `chrome_common.markBeat(tick, kind, team, label)` as the mechanism.
  Observed: `chrome_common.js` is unmodified (F11), so its `markBeat` has no `label` parameter and
  produces divs; the football beats bypass it entirely and are buttons. Design note §Transport rules
  (design.md:963-967) describes exactly this (`button.beat-marker`, `aria-label`, click = seek).
- Traced that no unlabelled div marker can reach the scrubber in this game:
  `chrome_common.ingestBeats` (`:579-588`) calls `markBeat` only for `steal`/`return`/`capture`, and
  the derived event vocabulary (`broadcast.nim:81-167`) emits none of those; the appended `fbEvent`
  intercepts every football kind and returns `true` (`:2931-2996`), so the inherited switch at
  `:1942-1945` is never reached for a football event. The inherited
  `.beat-marker.kill/.steal/.return/.capture` CSS at `:633-648` is dead but present.
- Also observed: the up-front beat timeline the server ships carries only `goal`, `drop` and
  `gameover` (`replays.nim:400-402`), and `fbFrame`'s timeline loop (`:3141-3162`) has no `drop`
  branch — so a `drop` beat draws no marker at all, and no marker without CSS is ever created.
  Design note §Scrubber beats (design.md:879-880) does not list `drop` as a beat.

### F13 — `#viewpanel` is removed, but `core.zoomAt` / `core.setZoom` / `core.panBy` wiring is deliberately kept
*Checklist area: 14 (last bullet)*

- Where: markup, CSS and ids are gone (diff above; `tests/test_viewer.nim:23-24,63-72` asserts
  `#fpv`, `#viewpanel`, `#minimap`, `#zoombar`, `#zoom-`, `fpv-canvas`, `minimap-canvas` appear
  nowhere in the page). `attachMinimap` is never called from the page
  (`grep -n "attachMinimap" client/replay_broadcast.html` → no match; it exists only in
  `client/broadcast_core.js:548` and `replay-viewer/static_replay_worker.js:225-227`).
- Retained wiring, with the page's own comment: `client/replay_broadcast.html:2586-2591`
  > "The starter's zoom cluster and minimap (the view panel) are removed: the whole 1200x800 pitch
  > is always letterboxed into the frame … The keyboard's z / x / arrow handlers below still drive
  > core.zoomAt / core.panBy for a viewer who wants a closer look at a scramble"

  and the call sites: `:2426-2427` (`z`/`x` keys), `:2484` (ctrl+wheel pinch), `:2501`
  (`core.setZoom` on Safari gesture), `:2556` (touch pinch), plus `core.panBy` on drag.
- Checklist item 14 last bullet says a fixed-arena game "removes the panel — markup, CSS, **the
  `core.zoomAt/setZoom/attachMinimap` wiring**, and the ids from the test list". Design note §Viewer
  (design.md:939-941, 949-952) lists only the panel's markup/CSS/ids as removed and says "Zoom:
  dropped … `#viewpanel` (zoom bar + minimap) is removed entirely"; it does not mention the keyboard
  or gesture handlers. So the code matches the note and diverges from the checklist wording.
- Design note §Viewer (design.md:949-950) does answer the "is the board larger than the frame"
  question directly: "The pitch is a **fixed arena** — the whole 1200 × 800 board is always
  letterboxed into the frame — so `#viewpanel` … is removed entirely, per the rule that it exists
  only for boards larger than the frame."

### F14 — No grid harness for the scripted baseline exists in the tree
*Checklist area: 7*

- Observed: `grep -rni "grid harness\|grid sweep\|parameter grid\|tuned with"` over the whole repo
  returns nothing; the only `grid` matches are CSS `display: grid` in
  `client/replay_broadcast.html:154,863`. `tools/` contains no sweep or tuning script
  (`build_manifest.py`, `build_replay_viewer.sh`, `expand_replay.nim`, `extract_events.nim`,
  `gen_trig_table.nim`, `gen_wire_constants.nim`, `page_surgery.py`, `record_fixture.sh`,
  `replay_summary.py`, `wasm_replay_smoke.cjs`, `ci/*`). `docs/plans/` holds only the design note.
- The only spread evidence is `tests/test_control.nim:99-116` (`zonalBeatsGegenpress`): two seeds
  × both side assignments, asserting `zonalGoals >= pressGoals`.
- What the design note says: §Tests item 4 (design.md:1199-1204) promises only "`zonal` beats
  `gegenpress` over the head-to-head fixture (the ladder needs a spread)" — the note does not
  promise a grid harness. Checklist item 7 does.

### F15 — The all-scripted "complete" assertion and the "every order legal" assertion are in different tests at different match lengths
*Checklist area: 7*

- `results.reason == "complete"`: `tests/test_scoring.nim:78-82`
  ```nim
  block fullTime:
    let match = runScriptedMatch(testConfig(maxTicks = 480))
    doAssert match.reason == reasonComplete and match.rule == erFullTime
  ```
  480 ticks (20 s of sim), driven by the real control layer via
  `tests/lib/helpers.nim:67-108`.
- Every order/action legal: `tests/test_control.nim:12-27` (`everyByteIsLegal`, 1440-tick scripted
  match, every one of 22 bytes per tick decoded and re-encoded), `:29-53` (`ordersAreBounded`, both
  baselines over 60 pseudo-random worlds: `note`/`say` caps, targets inside the pitch, `pass_to` a
  teammate or null, never self), `:55-66` (one order per seat for its own shirt), `:68-82`
  (22 legal bytes every tick), `:84-97` (a restart forces the taker's byte to `0x00` and zeroes
  every action code).
- Design note §Tests item 4 (design.md:1199-1204) asks for the legality sweep "over a 1440-tick
  scripted match", which is what `everyByteIsLegal` does. Observed: no single test both plays to the
  natural end and asserts legality; the two halves are split.

### F16 — Manifest, `num_agents`, docs shape and protocols all match
*Checklist area: 3, 6, 10* — traced and consistent.

- `coworld_manifest_template.json`: `game.replay_viewer == {"bundle": "static-replay-viewer"}`.
- `num_agents == 8` in `variants[0].game_config` (`match`), `variants[1].game_config` (`half`), and
  `certification.game_config`; neither variant carries a top-level `num_agents`;
  `len(certification.players) == 8`, `len(certification.game_config.players) == 8`,
  `len(...slots) == 8`. Pinned by `tests/test_manifest.nim:15-35`.
- `game.docs` shape: `readme = {"type":"text","value":<5889 chars>}`; `pages` = three entries each
  `{"id","title","content":{"type":"text","value":…}}` — `rules.md`/"Rules" (13581),
  `protocol.md`/"Wire protocol" (11929), `coaching.md`/"Writing a grf-football prompt" (5767).
  Pinned by `tests/test_manifest.nim:50-68`. `AGENTS.md` records that the template is generated by
  `tools/build_manifest.py`, and `.github/workflows/ci.yml:104-108` runs `--check` on it.
- `game.protocols` carries **both** `player` and `global`, each
  `{"type":"uri","value":"https://github.com/Metta-AI/cogame-grf-football/blob/main/docs/PROTOCOL.md"}`.
- `results_schema`: `additionalProperties: false`, `required` = the six the note names, 22 properties
  equal key-for-key to `playerResultsJson()` (asserted in `tests/test_manifest.nim:70-87` by set
  comparison against the live document).
- `tools/build_replay_viewer.sh` exists, is committed `100755` (`git ls-files -s`), and is the
  starter's script with only the two literals the note names changed (`image_tag`,
  `docker cp` source) plus one comment reword — verified by `diff` against the starter.
- Minor: `tags` sits at the manifest **top level**, not at `game.tags` as design.md:1099 says.
  `tests/test_manifest.nim:45-46` deliberately asserts `not m["game"].hasKey("tags")` and
  `m["tags"].len >= 3` — the code and its test agree, the design note's path is stale.

### F17 — `SEAT-COUNT` invariants, placeholder gate, and workflow order
*Checklist area: 6, 12* — traced and consistent.

- `tools/ci/docker_smoke.sh` is `100755`, and enforces four invariants before any container starts,
  each exiting non-zero with a `SEAT-COUNT FAIL:` prefix:
  `certification.game_config.num_agents` present (`:110-117`), a positive integer (`:123`),
  `len(certification.players) == num_agents` (`:131-133`),
  `len(certification.game_config.players) == num_agents` (`:138-140`). `SMOKE_SEATS` is the
  independent second declaration (`:54`, `seats_expected="${SMOKE_SEATS:-8}"` — the `<SEATS>`
  substitution) cross-checked at `:141-149`.
- `grep -n "SEAT-COUNT" ` over the whole reviewed-sha run log returns **no match**; the docker-smoke
  log line reads `smoke OK: seats=8 …`.
- The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`,
  `coworld-release.yml`, `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` → no match.
- All three workflows present. `coworld-release.yml` step order: `Build the Coworld manifest`
  (`:159`) → `Certify locally` (`:173`) → `Upload the policies` (`:212`, with the comment "BEFORE
  upload-coworld: observed, upload-policy reports the local image missing if it runs after
  upload-coworld") → `Upload the Coworld` (`:310`) → `Put the Coworld secret` (`:348`, "AFTER
  upload-coworld: the secret namespace is the Coworld's").
- `tools/ci/policies.json`: four policies, all `"run": "/bin/grf-football-player"`, one image.
  Two `PLAYER_PROMPT` champions with distinct prompts (`grf-football-tiki`, `grf-football-counter`,
  matching design.md:481-513 verbatim), two scripted fillers (`PLAYER_SCRIPTED=zonal`,
  `PLAYER_SCRIPTED=gegenpress`). Champion #2 (`grf-football-counter`, the second `PLAYER_PROMPT`
  entry) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.

### F18 — Two test assertions were replaced during this run
*Checklist area: 1 (second half — "no test loosened")*

Recorded so the judge can weigh them; both are documented in their commit messages.

- `aef2def` ("tests: assert what a tackle IS…"), `tests/test_physics.nim` `slideTackleAndFoul`:
  ```
  -    doAssert sim.ball.controller != int32(carrier),
  -      "a slide that reaches the ball knocks it loose"
  -    doAssert sim.cogStats[tackler].tackles == 1
  +    doAssert sim.cogStats[tackler].tackles == 1,
  +      "a slide that reaches the ball first is credited as a tackle"
  +    doAssert sim.cogStats[tackler].fouls == 0,
  +      "a slide that reaches the ball first is never a foul"
  ```
  Net: the "knocks it loose" assertion is gone; a `fouls == 0` assertion is new. Commit rationale:
  "Whether the loose ball then rolls to the tackler, to a third cog, or back to the cog it was taken
  from is ordinary play, and the sim deliberately privileges none of them."
- `c755d4d`, `tests/test_physics.nim` `keeperCatchesAndParries`:
  ```
  -    doAssert sim.restartKind != rkGoalKick, "a 25 m/s ball is parried, not caught"
  +    doAssert sim.teamStats[Blue].saves >= 1, "the parry is credited as a save"
       doAssert speedOf(sim.ball.vx, sim.ball.vy) <= KeeperParryCap + 1, …
  +    doAssert sim.goals(Red) == 0, "a parried shot is not a goal"
  ```
  Net: one assertion replaced by two. Commit rationale: "a parried ball at the keeper's feet is
  legitimately gathered on the next substep".
- Tightenings in the same window (recorded for completeness): `98bdfaf` raised
  `tests/test_replay.nim`'s `hashes.len > 700` → `> 1400` and `ticks > 700` → `> 1400`, and added
  `theRenderPathDoesNotPerturbTheSim`. No test file was deleted
  (`git log --diff-filter=D --name-only -- tests/` → empty). No `skip`/`xfail`/`--skip` appears
  anywhere in `tests/`.

### F19 — Built-in AI keeper has no goal-kick rule of its own
*Checklist area: correctness (not a named checklist item)*

- Where: `src/grf_football/builtin_ai.nim:359-372`. When `sim.ball.controller == index` the code
  takes `sim.safeOnBall(index)` for **every** cog, keeper included, and returns; the keeper-specific
  branch at `:374-377` is only reached when the keeper does *not* hold the ball.
- Design note §The built-in AI item 1 (design.md:556-560): "…on possession, goal-kick `pass_long` to
  the most open teammate beyond the halfway line, else `pass_short` to the nearest full back."
  Observed: that rule is not implemented; the keeper on the ball runs the generic safe option
  (`builtin_ai.nim:250-279`), whose first branch is `pass_short` under pressure, then `shot` inside
  20 m of the *opponent* goal, then carry, then `pass_long` to the most advanced open teammate.

### F20 — `steerAction` drops the direction nibble on arrival without consulting "is chasing"
*Checklist area: correctness (not a named checklist item)*

- Where: `src/grf_football/builtin_ai.nim:337-344`:
  ```nim
  if code < 1 or code > 4:
    let d = distI(px - sim.cogs[index].x, py - sim.cogs[index].y)
    if d < ArriveUm: dir = 0
  ```
- Design note §The control layer item 2 (design.md:537-538): "`0` when `dist(p*, pos) < 400 000`
  **and the cog is not chasing the ball**". Observed: the chasing predicate is computed in
  `control.nim:89-95` (`var chasing`) and used only for the sprint bit (`control.nim:107`); it is
  never passed to `steerAction`, so an arrived-and-chasing cog also gets `dir = 0`. `ArriveUm` is
  400 000 as specified (`builtin_ai.nim:32`).

### F21 — `client/replay_broadcast.html` retargets the inherited script in place, not only by appending
*Checklist area: 14*

- Where: `client/replay_broadcast.html:1564-1567`, `:1628`, `:1679-1680`, `:1772`, `:1784-1799`,
  `:1833-1860`, `:1931-1937`, `:2087-2096`, `:2182`, `:2294-2330`. The starter's `PB_MODE`/`PB_CTX`
  paintball branches became `FB_MODE`/`FB_CTX` football branches (latched on `s.half !== undefined`
  instead of `s.regime !== undefined`), the plate contents changed from hill-time/tags to
  goals/shots/possession, the endcard's win-condition chip and "how" text were rewritten, and the
  event switch gained the `FootballChrome.event` interception.
- Design note §Chrome provenance (design.md:933-937): "The file keeps its CSS, markup, `relayout()`
  and behaviour; football-specific chrome is a **single appended `<style>` + `<script>` block at the
  end of the page**". Observed: the appended block is real and is the only place new DOM nodes are
  created, but the inherited script above the banner was also edited in place. The page's own banner
  is explicit about this (`:2699-2703`: "Everything above this banner is the classic broadcast page,
  **edited only where the mode demands** and always behind FB_MODE"), and every new node introduced
  above the banner carries the `fb-` prefix (`fb-shots-`, `fb-statline-`, `fb-chip`, `fb-sub`,
  `fb-lbl`), which `tests/test_viewer.nim:74-102` asserts. Checklist item 14 gates on the **CSS**
  above the banner, which is deletions-only (F11).

---

## Traced and consistent

Recorded here because coverage is as informative as doubt. Each line says what I opened and how I
checked it.

- **CI green at the reviewed sha.** `gh run view 33053836802 --json headSha,conclusion,jobs`:
  `sha 66093e57cc722ba4a604c30473e730abe14b35de`, `conclusion success`, and all four jobs
  (`test`, `docker-smoke`, `replay-rehash`, `wasm-viewer`) `success`. Note: main has since moved to
  `c5cdc01849fbf2e4ff5efbea0912a254ee6f1401` (run `33054781746`, also green) — the reviewed sha is
  no longer the tip of `main`.
- **Simultaneous decision → one parallel batch per turn.** `decide.nim:260-290` (`curlyBatch` builds
  a single `RequestBatch` and calls `client.curl.makeRequests(batch, max(1, timeoutSeconds))` once);
  `decide.nim:362-392` collects **all** LLM seats into one `calls` seq before any transport call;
  `decide.nim:414-427` issues at most two batches. Asserted by
  `tests/test_engine.nim:46-63` (`rec.calls.len == 1` and `rec.calls[0] == SeatCount == 8`, every
  seat present, every `activeDirective[seat].source == dsLlm`). No sequential per-seat call path
  exists — `grep` finds no `makeRequests` outside `curlyBatch`.
- **Retry-once-then-scripted-fallback, and the fallback is recorded.** `decide.nim:414` bounds the
  loop at `attempt <= 2`; failures on either attempt write
  `{"k":"fallback","turn","seat","attempt","cause","detail"}` (`:463-468`); seats still in `calls`
  after the loop get `fallbackFor` = `zonal` with `source = dsFallback` (`:475-479`, `:315-323`);
  `sim.seatStats[seat].fallbackTurns` is incremented at `:492`, and surfaces in results at
  `roster.nim:176`. Cause vocabulary implemented: `timeout`, `throttled`, `transport_error`
  (`:442-446`), `parse_error` (`:458`, `:461`), `no_credentials` / `budget_guard` /
  `transport_error` on the no-transport path (`:374-387`) — the six the note names at
  design.md:430-431. Tests: `test_engine.nim:65-86` (exactly two attempts, one record per failed
  attempt per seat = 16, cause `timeout`), `:88-102` (unparseable prose → `parse_error`, retried
  once), `:104-124` (no credentials → `no_credentials`, turn costs < 2000 ms, no seat unactuated),
  `:126-144` (budget guard).
- **Tolerant parsing.** `llm.nim:194-206` (`extractJsonObject`: outermost `{`…`}`, fences and prose
  prefixes tolerated); `directives.nim:266-287` (`cogs` as array, bare object, or id-keyed map);
  `:238-264` (`numberOf` accepts numeric strings, rejects NaN/±Inf); `:102-137` (every enum repairs
  to the documented default); `:331-343` (target clamped via `worldXOfView`/`worldYOfView`, or the
  cog's current position); `:344-351` (`pass_to` must be a teammate ≠ self, else `-1`); `:311-317`
  (first usable entry wins, extras dropped); `:355-357` (missing entry → last turn's, else the
  fallback's). Every repair in the note's table (design.md:757-773) has a test in
  `tests/test_directives.nim:12-110`.
- **Every wait and its bound.** LLM batch attempts: `attempt1Ms` 6000 / `retryMs` 3000, floored to
  whole seconds (`decide.nim:416-427`), inside a monotonic `turnBudgetMs` 10000 deadline
  (`decide.nim:407-408`); `sim_config.nim:127-138` rejects `turnBudgetMs < attempt1Ms + retryMs` and
  any sub-second `attempt1Ms`/`retryMs` (curl's whole-second granularity, the note's scar at
  design.md:398-399). Rate floor sleep is bounded by `min(waitMs, turnSpacingMs)`
  (`decide.nim:399-405`). Frame limiter: bounded `while true` that breaks on
  `elapsed >= frameDuration`, sleeping 1-2 ms (`server.nim:340-350`). Lobby: `lobbyJoinTimedOut()`
  at 1440 lobby ticks → `declarePlayerFailure` + `startGame()` (`server.nim:675-684`,
  `sim_state.nim:29-35`) — a no-show does not end the episode. Engine stop: `server.nim:700-715`,
  re-checked **inside** the tick loop rather than once per outer iteration. Player container:
  `ConnectTimeoutMs` 90 s and `ReceiveTimeoutMs` 120 s, both explicit
  (`src/grf_football_player.nim:24-42`). Host error: `server.nim:858-887` records
  `fault/host_error`, writes artifacts best-effort, re-raises. No unbounded loop or blocking read
  found. (The *aggregate* wall-clock question is F1.)
- **Both name spaces.** `cogId` is the only in-game identity (`sim_types.nim:624-628`);
  `decide.seatViewJson` builds the seat view entirely from `cogId`/`teamPrefix`/`roleText`
  (`decide.nim:104-239`) and never reads `player.address` or `policyLabel`; the prompt is held in
  `SeatPolicy.prompt` and marked "never recorded, never echoed" (`decide.nim:80`) and never enters
  `directiveJson` (`directives.nim:153-183`). Spectator side: real names in `roster[].name`/`pol`
  (`broadcast.nim:291-309`), `teams.<team>.policies` (`broadcast.nim:250-270`), `results.names`
  (`roster.nim:132-140,163`), and the replay's config JSON / joins. `tests/test_identity_privacy.nim`
  asserts all of it, including `showPlayerLabels` forced **true** (line 43 — "the guarantee must be
  the VOCABULARY, not the flag") and a source-level grep that `global.nim` reads neither `address`
  nor `policyLabel` (`:80-88`).
- **Emscripten link flags ↔ bootstrap, same lineage.** `replay-viewer/config.nims:42-54` — no
  `MODULARIZE`, no `EXPORT_NAME`, `-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s
  ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8` — matched by
  `replay-viewer/static_replay_worker.js:8` (`var Module = {};`) and `:188-192`
  (`Module.onRuntimeInitialized = function () { runtimeReady = true; start(); }`). All four viewer
  files diff against the starter's as **only** the mechanical `ctf_` → `grf_` rename
  (`config.nims`: 4 hunks, all the rename; `static_replay.js`: 2 hunks, worker name and
  `window.CtfStaticReplay` → `window.GrfStaticReplay`; `static_replay_worker.js`: 14 hunks, all
  `Module._ctf_*` → `Module._grf_*` and `importScripts('./grf_replay.js')`; the wasm entry is ctf's
  `ctf_replay.nim` renamed). `tests/test_viewer.nim:164-190` pins the rename, the absence of
  `MODULARIZE`, the presence of `onRuntimeInitialized`, and both DOM markers.
- **`data-replay-loaded` / `data-replay-error`.** `replay-viewer/static_replay.js:161`
  (`document.documentElement.setAttribute('data-replay-loaded', 'true')`, on the Worker's `loaded`
  message, which the Worker posts only after `ingestPacket()` has fed the first frame packet to the
  core — `static_replay_worker.js:120-129`) and `:19-20` (`showFailure` sets `data-replay-error`),
  reached from every failure path (`:89,94,175,179,188,197,201,215`). CI evidence:
  `{"loaded":true,"ms":590,…}`.
- **Static viewer, S3 only.** `game.replay_viewer.bundle == "static-replay-viewer"`;
  the Worker fetches exactly one URL, `message.replayUrl`, with `credentials: 'omit', mode: 'cors'`
  (`static_replay_worker.js:113-117`); `tests/test_viewer.nim:149-162` asserts none of the three
  bundle sources contains `src="/client/replay"` or `fetch('/client/replay`, and that
  `client/league_replayer.html` is deleted. (The game **server** still serves
  `bitworldClient.ReplayClientRoute` / `CoworldReplayClientRoute` at `server.nim:255-262` — that is
  the inherited live-pod spectator route, which design.md:672-674 explicitly keeps; it is not part
  of the static bundle.)
- **`.plate-name` and the 640 px rule.** `client/replay_broadcast.html:2723-2728`
  (`flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis`) and `:2756-2767`
  (`#stage.tiny .fb-stat/.lives-label/.fb-chip { display: none }` plus
  `@media (max-width: 640px) { … display: none }`). Asserted at `tests/test_viewer.nim:118-126`.
  `relayout()` keeps the starter's `--hudscale = clamp(0.5, boardW/760, 1.6)` and
  `#stage.tiny` at `boardW <= 620` (`:2663-2665`).
- **Scoring matches the note's formula.** `roster.nim:122-127`:
  `500 + clamp(roundDiv(gd * 500, 3), -500, 500)`, and `500` flat for `reasonFault`. Checked by
  hand: gd 0→500, 1→667, 2→833, 3→1000, −2→167. `seatWon` = `endReason != fault and gd > 0`
  (`:129-130`). `tests/test_scoring.nim:15-56` pins the margins, the exact complementarity
  (`scorePermille(0) + scorePermille(1) == 1000`), the eight-seat sum of 4000 across a 7×7 grid, and
  the fault case. Design §Scoring (design.md:330-344).
- **End conditions.** `results.reason` is the closed three-value enum
  (`sim_types.nim:229-232`, `reasonText` at `:693-697`) with the five `endRule` values
  (`:221-227`); `finishGame` is idempotent — "the first ending wins" (`sim.nim:310-329`, tested at
  `tests/test_scoring.nim:107-113`); mercy at a turn boundary (`sim.nim:1240-1244`), full time
  (`:1245-1246`), the physics guard → `sim_fault` (`sim.nim:999-1015,1224-1226`), wall clock and
  host error via `wallClockStop`/`hostErrorStop` (`:1285-1293`) and the `stop` record.
  `tests/test_scoring.nim:78-105` reaches all five.
- **Pitch geometry against the note's table** (design.md:121-137): every constant matches —
  `PitchXMin/Max 3/87 Mµm`, `PitchYMin/Max 3/57`, centre `(45, 30)`, `CentreCircleR 9`,
  `GoalYMin/Max 26/34`, `PostRadius 100_000`, penalty area `PenaltyDepth 16` + `PenaltyHalfH 20`
  (→ `x ≤ 19 000 000`), six-yard `SixYardDepth 5.5` + `SixYardHalfH 10` (→ `x ≤ 8 500 000`),
  `BoardX/Y 0.3…89.7 / 0.3…59.7`, `CogRadius 500_000`, `BallRadius 220_000`
  (`sim_types.nim:60-91`). I recomputed all eleven formation anchors from
  `ShirtAnchorX`/`ShirtAnchorY` (`sim_types.nim:571-597`) into view coordinates and every one equals
  the note's 4-3-3 table (design.md:308-320). `DropSpots` (`:607-611`) = (±21, ±13.5) m.
  `DirVecQ12`/`DirBrads` (`:555-568`) are the eight compass directions in screen convention.
- **Movement/ball/contact constants** against design.md:174-219: `Accel 25_000`,
  `IdleDragNum 96`, `BaseSpeed 250_000`, `SprintSpeed 337_500`, `DribbleSpeed 200_000`,
  `KeeperSpeed 229_000`, `TiredSpeedPct 85`/`TiredStamina 200`/`ExhaustedStamina 50`,
  `StaminaMax 1000`/`Drain 6`/`Recover 2`, `BallDragNum 7`, `BallMaxSpeed 1_333_333`,
  `Gravity 4_340`, `AirApex 4_000_000`, `GroundZ 400_000`, pass speeds 583_333/916_666/750_000 and
  ranges 25/45/40 m, `ShotSpeed 1_083_333`, `ControlRadius 1_100_000`, `ControlSpeed 500_000`,
  `DeflectPct 45`, `DribbleOffsetOff 900_000`/`On 550_000`, `CogRestitutionPct 20`,
  `PostRestitutionPct 70`, `KeeperCatchRadius 1_500_000`/`Speed 750_000`/`ParryPct 60`/`Cap 500_000`,
  `TackleKnockSpeed 250_000`, `SlideSpeed 400_000`, `SlideTicks 12`, `GroundedAfterSlide 24`,
  `GroundedAfterFoul 48`, cooldowns 12/18, `Substeps 4`, `RestartTicks 36`,
  `StalemateTicks 480`/`StalemateBox 2_000_000`, `RestartClearRadius 5_000_000`,
  `RestartTakerOffset 800_000`, `AssistWindowTicks`/`PassWindowTicks 144`,
  `TouchThrottleTicks 8`. All match. Shot aim error is
  `e = 2 + dist_m div 6 (+4 if an opponent is within 2 m)`, `err = draw(2e) − e`, from the seeded
  sim `Rand` (`sim.nim:551-583`) — integer draws only.
- **The 19-action byte.** `actionDir` (`sim_types.nim:758-762`, nibbles 9..15 → 0), `actionCode`
  (`:764-767`), `actionSprint` (`:769-770`), `encodeAction` (`:772-778`, clamps rather than raises).
  `tests/test_actions.nim` round-trips every legal byte, asserts 9..15 decode as 0, that a pass/shot
  from a cog with no ball is a no-op, and that sprint/dribble are sticky and always defined.
- **Substep order.** `sim.nim:1017-1037` (`runSubsteps`) runs integrate cogs → integrate ball →
  cog-cog pairs → boundary clamp → slides (ball, then opponents) → ball vs cogs (control / deflect /
  keeper catch-parry) → carry → posts → netting → goal test → out-of-play, matching design step 7's
  eight-item list (design.md:272-286) with `carryBall` inserted after control and the out-of-play
  test per substep (F7).
- **Restart table.** `handleOutOfPlay` (`sim.nim:933-997`): touchline → throw-in to the team that did
  *not* touch it last, nearest non-keeper to the crossing point; goal line, last touched by the
  defender → corner at the nearest arc; last touched by the attacker → goal kick to the defending
  keeper at the nearest six-yard corner. Keeper catch → goal kick from the six-yard centre
  (`sim.nim:814-817`). Foul → indirect free kick clamped to the 16 m line (`sim.nim:767-775` with
  `pitch.freeKickSpot:94-105`; I traced the `other(team)` double-negation and it resolves to the
  fouled team receiving the kick and the tackler's own area being the one clamped out of). Goal →
  kickoff by the conceding team from the centre spot (`sim.nim:925-931`). Half-time / match start →
  kickoff by shirt 10 (`sim.nim:256-286`, `sim.nim:1156-1165` — the team that did *not* kick off at
  tick 0). Dead-ball phase: taker snapped 800 000 µm behind the spot, opponents inside
  5 000 000 µm pushed radially out to exactly that radius, everyone else moving normally
  (`sim.nim:1099-1154`). Stalemate drop at 480 ticks inside the sim (`sim.nim:288-304`,
  `:1210-1222`). `tests/test_physics.nim` covers all of these.
- **Turn boundary and cadence.** `server.nim:717-732` runs `engine.turn` immediately before the tick
  it governs, with an `opening` flag so turn 0 fires on the first tick that has no directive
  (`activeDirective` is pre-seeded at `sim.nim:187-195` so no cog is ever unactuated).
  `turnTicks = 240` → 24 turns over 5760 ticks (`sim.nim:96-106`).
  `compileActions` returns a byte for all 22 cogs on every tick and forces the taker to `0x00` and
  every other cog's code to 0 during a restart (`control.nim:186-213`).
- **Determinism discipline.** `tests/test_determinism.nim:12-26,68-76` greps eight hashed modules
  (`sim`, `sim_types`, `sim_config`, `sim_state`, `pitch`, `control`, `builtin_ai`, `trig`) for 17
  float-family identifiers over comment- and string-stripped source
  (`tests/lib/helpers.nim:110-153`); `:78-83` re-derives all 256 `SinQ12` entries from `math.sin`;
  `:85-94` checks `isqrt` exhaustively to 20000 and on perfect squares to 2⁴⁰; `:96-108` checks
  `bradsOfVectorI` is exactly antisymmetric under y → −y. The design's float ban
  (design.md:634-636) names four modules; the code and test cover eight.
- **`.plate-name`, beat CSS, kept/removed ids, alias shadowing** are all machine-asserted in
  `tests/test_viewer.nim`, including a shadowing guard for the 14 chrome aliases
  (`:25-29,139-147`, the cogame-tandem scar) and the `fb-` prefix sweep of the appended block
  (`:74-102`).
- **State JSON.** `broadcast.buildStateJson:342-461` emits every key
  `tests/test_broadcast_state.nim:19-36` lists; `teams` is keyed `red`/`blue` with `lives` mirroring
  `goals` so the inherited momentum curve draws goal difference unmodified
  (`broadcast.nim:272-289`); a seek frame hydrates the scorebug and end-card from state with zero
  events (`tests/test_broadcast_state.nim:85-104`). The design's illustrative snippet
  (design.md:1010-1031) shows `"lead": [0,0,1,…]`, `"over": false` and `"hold": 0`; the code emits
  `lead` as `{teams, pts}` (`broadcast.nim:415-425`), `over` as an object present only at game over
  (`:438-457`) and `hold` only when non-zero — these are the starter's shapes that
  `chrome_common.js` reads, so the snippet is the loose one.
- **Derived event vocabulary** (`broadcast.stepEvents:81-167`) emits `phase`, `gamestart`,
  `gameover`, `goal`, `shot`, `save`, `tackle`, `pass`, `foul`, `touch` (throttled to
  `TouchThrottleTicks`), `drop`, `halftime`, `restart`, `turn_end` — the closed set
  `tests/test_broadcast_state.nim:76-79` asserts, matching design.md:872-877.
- **Manifest ↔ engine round-trip.** `tests/test_manifest.nim:89-125` runs every variant's and the
  cert fixture's `game_config` through the real `config.update` and asserts `numAgents == 8` and
  `maxTicks == 1440`; `:127-139` asserts the fixture fits the certifier's 60 s clock (1440 ticks
  = 60 s of sim, `turnSpacingMs == 0`, `fastMode`); `:162-171` asserts the game runnable's
  `ANTHROPIC_API_KEY_URI` equals `secret://coworld/<game.name>/anthropic_api_key`.
- **`system` prompt and both champion prompts** in `decide.nim:26-60` and `tools/ci/policies.json`
  match design.md:437-473 and :481-513 word for word (I diffed them by eye line by line).

---

## Could not determine

- **Whether a production `match` episode settles inside 720 s at this sha.** F1's extrapolation is
  arithmetic from a 1440-tick CI episode; only a 5760-tick run with `turnSpacingMs: 18000` would
  settle it. What would settle it: a `docker-smoke` (or hosted) episode using
  `variants[0].game_config` rather than the certification fixture, with the
  `grf-football: tick … budget:` lines and the final `reason`.
- **Whether `clipRunes` survives an invalid-UTF-8 input in a debug build (F5).** Nim's `fastRuneAt`
  reads continuation bytes without a length check; whether that raises `IndexDefect` or reads the
  string's terminating NUL depends on the bounds-check behaviour of `string.[]` in the `test` job's
  debug build. What would settle it: a test that calls
  `clipRunes("a".repeat(398) & "\xF0\x9F\x8F\x86"[0..1], 200)` — i.e. a deliberately byte-truncated
  multi-byte sequence — in both debug and release.
- **Whether `sim.feed` is rendered anywhere in the viewer (F4).** `grep -n "s\.feed"` over
  `client/replay_broadcast.html` finds no consumer, and the CI smoke's `feed_lines: 0` was sampled on
  the first drawn frame, so I cannot distinguish "sampled too early" from "never rendered". What
  would settle it: a `viewer_smoke.mjs` reading taken after the playhead has passed a goal or a
  directive turn, or a grep of `client/broadcast_core.js` for a `feed` consumer (I read
  `broadcast_core.js` only around the zoom/minimap API).
- **Whether the checklist's "viewer draws LLM-authored text" clause binds for DOM-only model text
  (F4).** Observed facts recorded; the categorisation is not mine.
- **Whether the two test-assertion replacements in F18 count as "loosened".** Both are documented
  and both add assertions while removing one; I report the diffs rather than the verdict.
