# r1 review — particle-worlds

Repo: `/workspace/cogame-particle-worlds` (Metta-AI/cogame-particle-worlds) at
`99dcaab7f21dad18f24e6f4fa160135bd01c7102`
Range read: `6bba1d3..99dcaab` (whole fork history: `bf329e4`, `ff529a1`, `97fac7b`, `a5094e6`,
`62b3f3c`, `99dcaab`)
Design note: `/workspace/coworld-builder/runs/2026-08-26-particle-worlds/design.md`
Starter (read-only): `/workspace/starters/coworld-ctf`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision clause)
Files opened: 44 in the coworld repo (all of `src/mpe/{field,motion,scoring,beliefs,decide,
directives,llm,baselines,control,roster,replay_runtime,broadcast(part),sim(part),sim_state(part),
sim_config(part),server(part),arena(part),global(part)}.nim`, all 15 `tests/*.nim`,
`replay-viewer/*` (4), `client/*` (3, diffed against the starter), `tools/ci/*` (5), `tools/*` (3),
`coworld_manifest_template.json`, `.github/workflows/*` (3), `AGENTS.md`), plus 5 starter files
diffed, plus the full CI log for run 32953267780.

Labels used below: **[observed]** = I read the lines cited. **[inferred]** = I reasoned from lines
I read. **[untested]** = would need a hosted or CI run to settle.

---

## Blocking candidates

### F1 — the worst-case renderer fixture does not load the real renderer, and it is the only `canvas_text` evidence this repo has
- Where: `tools/ci/renderer_fixture.html:1-262` (the whole file); `.github/workflows/ci.yml:339-364`
  (the step that drives it); CI run 32953267780, `wasm-viewer` job, steps
  `Load the bundle in a real browser` and `Worst-case renderer fixture at 360 / 620 / 1280 px`.
- Observed:
  - `renderer_fixture.html` contains **exactly one `<script>` tag** and it has no `src`
    (`tools/ci/renderer_fixture.html:68` is the only `<script`; `grep` for
    `chrome_common|broadcast_core|renderer.js` matches only the prose comment at line 10). The page
    is a ~190-line inline `drawBoard()` (lines 102-235) that re-implements the marks, the symbol
    bubbles, the plates, the radio strip, the crypto rows and the note wrap with its own
    `measureText` layout.
  - Its own header comment at `tools/ci/renderer_fixture.html:10` claims *"This page loads the REAL
    chrome (chrome_common.js and the same DOM ids the broadcast page uses)"*. It does not: no
    external script is fetched, and the only shared ids are the four empty stub `<div>`s at lines
    59-67 (`#stage`, `#scorebug`, `#killfeed`, `#scrub`, `#clock`), which nothing reads.
  - The fixture's self-check is real and passes: `NOTE` is 160 codepoints (verified by counting the
    concatenation at lines 73-75 — 160 exactly, last rune U+1F680) and lines 244-251 set
    `data-replay-error` if that drifts or if a symbol is not one rune.
  - The main viewer smoke reported `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed
    an edge), 0 ellipsized (--strict-text-bounds)` (CI log line 5778). The real viewer renders in an
    OffscreenCanvas Worker (`replay-viewer/static_replay.js:89`: *"This browser does not support
    OffscreenCanvas Workers"*; `replay-viewer/static_replay_worker.js:8,188,192`), so
    `viewer_smoke.mjs`'s main-thread `CanvasRenderingContext2D` instrumentation
    (`tools/ci/viewer_smoke.mjs:327-370`) sees nothing from it.
  - The fixture step reported `canvas text: 49 drawn, 0 never inside …` (CI log line 5809).
- Design note says: §Tests, line 1622-1627 — *"`tools/ci/renderer_fixture.html` — a worst-case
  renderer fixture … **it loads the real renderer** with a full-cap 160-rune `note` on every seat …"*.
- Checklist item: 15, third and fourth bullets — *"a page that **loads the real
  `client/renderer.js`**, hands it a frame built to hurt … renders it at several canvas sizes …
  and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step"* and
  *"`total: 0` means the check covered nothing (a worker/OffscreenCanvas or WebGL renderer) and is
  not evidence of anything."*
- Why it matters, concretely: the two `canvas_text` numbers in CI are (a) `total: 0`, which the
  checklist explicitly disqualifies as evidence, and (b) `total: 49` from a page that never executes
  `client/broadcast_core.js`, `client/chrome_common.js` or the `mpe-` block appended to
  `client/replay_broadcast.html:4125`. The shipped bubble geometry
  (`src/mpe/global.nim:5381-5434`, `buildShoutBubble` + `shoutBubblePlacement`), the shipped
  `#killfeed` note rows and the shipped `#mpe-crypto` panel are therefore untested by every gate in
  the tree. **[observed]**, with the CI-log consequence **[observed]** and the "untested" conclusion
  **[inferred]**.
- Category the judge will want: `legibility` (item 15).

### F2 — `client/chrome_common.js` is not byte-identical to the starter's, and the design note says it is
- Where: `client/chrome_common.js:72` vs `/workspace/starters/coworld-ctf/client/chrome_common.js:72`.
- Observed: the full `diff` is one line and one line only:
  ```
  72c72
  <   var WIRE = window.MPE_WIRE || {};
  ---
  >   var WIRE = window.CTF_WIRE || {};
  ```
  sha256 `44cfecde…61d13` (fork) vs `7ace7287…72f7c7b` (starter). `tests/test_viewer.nim:180-191`
  pins the fork's sha and asserts `"CTF_WIRE" notin chrome`, so the change is deliberate and
  test-locked, and `tests/test_viewer.nim:199-218` (the `ctf_`/`CTF_`/`PB_` grep over `client/`)
  would fail if the starter's line survived.
- Design note says: §Viewer §Chrome provenance, lines 1191-1195 — *"**`client/chrome_common.js` is
  copied byte-for-byte from coworld-ctf.** Not edited, not reformatted; `tests/test_viewer.nim` pins
  its sha256."* The single-identifier allowance is granted in the note only to
  `client/broadcast_core.js` (lines 1197-1198: *"copied byte-for-byte apart from the single
  `window.CTF_WIRE` → `window.MPE_WIRE` identifier"*). The note does not name a chrome_common patch.
- Where it *is* recorded: `AGENTS.md` §Lineage — *"`client/chrome_common.js` is byte-for-byte the
  starter's apart from the one `window.MPE_WIRE` identifier … `client/broadcast_core.js` is the same
  deal."* That is the repo's own operating guide, not the design note.
- Checklist item: 14, first bullet — *"`client/chrome_common.js` is **byte-identical** to the
  starter's … the only admissible change is a named, minimal patch **recorded in the design note**."*
- Both sides, stated plainly: the change is one identifier, minimal, named, and mechanically forced
  by the design note's own `ctf_`/`CTF_` rename-sweep rule (§Sim module, line 833). It is *not*
  recorded in the design note, which instead asserts the opposite. **[observed]**
- Category: `static-viewer` (item 14).

### F3 — the `turnSpacingMs` rate-floor sleep is inside the per-turn monotonic budget, which suppresses the single retry at the shipped settings
- Where: `src/mpe/decide.nim:358-361` (`turnStart = getMonoTime()`), `:419-425` (the spacing sleep),
  `:429-437` (the loop's budget check), `:499-507`; config values
  `tests/fixture.nim:41-44,72` and `coworld_manifest_template.json` variants
  (`turnBudgetMs: 10000`, `attempt1Ms: 6000`, `retryMs: 3000`, `turnSpacingMs: 9000`).
- Observed, step by step:
  1. `turnStart` is captured at the very top of `turn()` (`decide.nim:361`).
  2. If a previous batch exists and `turnSpacingMs > 0`, the proc sleeps
     `turnSpacingMs - since` where `since` is measured from the previous batch's **start**
     (`decide.nim:420-422`). With `turnSpacingMs = 9000` this sleep is up to ~9 s.
  3. The attempt loop's first statement is
     `if getMonoTime() - turnStart >= budget:` with `budget = turnBudgetMs = 10 000 ms`
     (`decide.nim:432`). The sleep is already inside that window.
  4. Steady state at the shipped variant: the previous batch takes ~2 s and 108 ticks run in
     `fastMode` in well under 1 s, so `since ≈ 2.5 s` and the sleep is ≈ 6.5 s. Attempt 1 then runs
     with a 6 s deadline. If attempt 1 **times out**, elapsed at the top of the retry iteration is
     ≈ 12.5 s ≥ 10 s: the loop writes a `fallback` record with `attempt: 2, cause: "timeout"` and
     `break`s (`decide.nim:433-437`). **The retry batch is never issued.**
  5. If attempt 1 fails *fast* (a parse error at ~1 s) the retry does still fire (6.5 + 1 < 10).
- Design note says: §Decisions §Cadence, lines 447-453 — *"attempt 1 batch deadline `attempt1Ms` =
  6000 ms, single retry `retryMs` = 3000 ms … Worst case 6 + 3 = 9 s ≤ the **`turnBudgetMs` =
  10 000 ms** cap enforced by a monotonic deadline **around the whole turn**."* The note's arithmetic
  treats the 9 s spacing floor and the 10 s turn budget as separate quantities
  (lines 461-462: *"40 turns x 9.0 s spacing floor … = 360 s / absolute worst: every turn spends the
  full 10 s turn budget = 400 s"*), i.e. as alternatives, not as one window.
- Checklist item: 8 — *"retries **once** on a parse or transport failure, then falls back to the
  scripted move."*
- What is **not** at risk: this cannot hang and cannot overrun. Batch starts are held ≥ 9 s apart
  and per-turn work is ≤ 9 s, so 40 turns ≈ 380 s, inside the 690 s stop and well inside 720 s.
  **[inferred]** from the arithmetic above.
- Test coverage: no test exercises `turn()` with `variantConfig`. `tests/test_engine.nim:152-177`
  ("an unusable reply retries exactly once") runs with `fixtureConfig`, whose `turnSpacingMs` is
  **0** (`tests/fixture.nim:44`), so the sleep is absent and the retry always fires;
  `tests/test_engine.nim:237-253` (the rate-floor test) uses `turnSpacingMs = 600`, small enough
  never to reach the budget. **[observed] / [untested]** at the shipped settings.

### F4 — one turn can write two or three `fallback` records for the same seat, so `replay_summary.py`'s `fallbacks` is not a turn count
- Where: `src/mpe/decide.nim:433-437` (budget-exhausted record, `attempt+1`), `:493-494` (per-failed-
  attempt record), `:510-522` (the tail record, hard-coded `attempt` 2);
  `src/mpe/server.nim:1955-1956` (`sim.fallbackTurns[seat]` is incremented **once** per seat per
  turn); `tools/replay_summary.py:110,128,185` (`fallbacks` counts *records*).
- Observed: on the ordinary two-failure turn a seat produces three records — attempt 1 (line 493),
  attempt 2 (line 493), and the tail drifter record (line 521). CI log lines 09:34:59 show exactly
  this triple for all four seats ("attempt 1 failed", "attempt 2 failed", "falling back to drifter
  (parse_error)"). On a budget-exhausted turn the seat gets two records both stamped `attempt: 2`
  with **different** causes (`"timeout"` from line 435, then `"parse_error"` from line 520).
- Design note says: §Record vocabulary, line 1098 — `fallback` carries `attempt (1|2)`; and the
  phase-60 recipe at lines 1060-1062 reads `.fallbacks` from `replay_summary.py` alongside
  `results.fallbackTurns`. The two numbers count different things and will not agree.
- Checklist item: 8 — *"the fallback is recorded so phase 60 can count it."* The fallback **is**
  recorded (so the item is satisfied in substance); the observation is that the count is
  multiple-per-turn and that two records for the same `(seat, turn, attempt)` can disagree on
  `cause`. **[observed]**
- `tests/test_engine.nim:171` asserts `fallbacks >= 4` for four seats, so the suite tolerates the
  multiplicity.

---

## Non-blocking observations

### F5 — `bedrockModelIds()` ships one model candidate; the design note lists two
- Where: `src/mpe/llm.nim:71-87` returns `@["us.anthropic.claude-haiku-4-5-20251001-v1:0"]`.
- Design note says: §Decisions, lines 428-430 — *"Bedrock model candidates in order, `BEDROCK_MODEL`
  pins one: `us.anthropic.claude-haiku-4-5-20251001-v1:0`, **then**
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`."*
- Consequence traced: with one candidate, `tryNextBedrockModel` (`llm.nim:89-97`) always returns
  false, so (a) a 429 always sets `client.throttled = true` and the turn fails fast — which is the
  behaviour the design and `tests/test_engine.nim:179-197` both want; and (b) a 401/403 carrying
  `"Model access is denied"` falls through to `client.disabled = true` (`llm.nim:181-186`), killing
  the LLM for the rest of the episode rather than rotating. Both are degrade-not-hang paths.
  The code carries a 10-line comment (`llm.nim:74-83`) recording the measurement that removed the
  sonnet candidate. **[observed]**

### F6 — the system prompt does not carry the per-turn mode/role line the design specifies
- Where: `src/mpe/llm.nim:207,222` — `SystemPrompt` is a `const`, and line 222 reads
  `THIS ROUND IS NAMED IN THE REPORT BELOW, AND SO IS YOUR ROLE.`
- Design note says: line 636 — `THIS ROUND IS <MODE> AND YOU ARE THE <ROLE>.` and line 618-619 —
  *"the line naming which mode and role the seat is in is filled per turn."*
- Observed: the mode and role do reach the model, via the view JSON's `"mode"` and `"you".role`
  (`src/mpe/decide.nim:170,178`), so no information is lost; the prompt text differs from the note.
  **[observed]**

### F7 — a `tag` pursuer's `shadow` behaves differently from what the system prompt tells the model
- Where: `src/mpe/control.nim:384-425`. For `sim.isPursuer(seat)` the shadowed body is forced to the
  evader (`:394-401`, ignoring `target`) and the stand-off becomes `tagPx div 2` = **10 px**
  (`:415-416`), not `shadowStandoffPx` = 60 px.
- The prompt the model reads says (`src/mpe/llm.nim:254-255`): *"shadow = close to 60 pixels of the
  particle nearest `target` and stay there"*. The design note's control-layer spec (line 779-781)
  says the same, with no `tag` exception.
- The code carries a 10-line justification comment (`control.nim:385-393,407-415`) citing a measured
  71 px closest approach and zero contact ticks with the 60 px stand-off, and
  `tests/test_control.nim:158-178` pins the new behaviour. **[observed]** — this is a deliberate,
  tested rule change that the design note and the shipped prompt both still describe the old way.

### F8 — `baselines.nim`'s `tag` pursuer comment contradicts the line beneath it
- Where: `src/mpe/baselines.nim:189-197` says *"A pursuer runs a PURE PURSUIT: `go` straight at the
  evader's current position. `shadow` is the wrong intent for a baseline pursuer…"*, and
  `:201` then sets `result.intent = intShadow`.
- Observed: the *behaviour* is correct given F7 (control.nim makes a pursuer's `shadow` a 10 px
  pursuit); only the comment is stale. **[observed]**

### F9 — `results.bumps` and the endcard's bump column report the **last round's** counter, not the episode's
- Where: `src/mpe/roster.nim:714` (`bumps.add(%sim.bumps[min(seat, 3)])`),
  `src/mpe/broadcast.nim:1245` (`overBumps.add(%sim.bumps[seat])`), and
  `src/mpe/field.nim:217` (`sim.bumps[seat] = 0` inside `beginRound`).
- Observed: `beginRound` zeroes `bumps[seat]` at the start of every round, so at episode end the
  array holds only round 4's (`tag`'s) bump ticks. `src/mpe/scoring.nim:156-158` uses the same
  per-round counter for the `spread` debit, which is correct for scoring.
- Design note says: §Results document, line 1013 — `"bumps": [14, 9, 22, 6]` listed among the ten
  **seat-indexed** arrays; §Viewer readout 10, line 1283 — the endcard table carries *"bumps"*
  alongside the four per-round columns and the mean, reading as an episode figure. The note does not
  state the intended aggregation explicitly. **[observed]** with the intent **could-not-determine**.

### F10 — a seat's own `score.this_round_so_far` is always `0.0` in a `tag` round
- Where: `src/mpe/decide.nim:164-166,195` computes `soFar` from `sim.roundAccum[seat] div elapsed`;
  `src/mpe/scoring.nim:132-133` — `of modeTag: discard   ## tag scores from the contact counters at
  round end` — so `roundAccum` is never written in `tag`.
- Contrast: the spectator frame does special-case it —
  `src/mpe/broadcast.nim:1052-1053`,
  `if sim.mode == modeTag: sim.tagRoundPermille(seat, elapsed) else: …`.
- Design note says: §Per-seat observation, line 567 — `"score": {"this_round_so_far": 0.58, …}` with
  no mode exception; §Round rules gives `tag` a live-computable term
  (`credit[p]*1000 div tagTargetTicks`, `(ticks - tagTicks)*1000 div ticks`). **[observed]**

### F11 — three modules the design note says are deleted are still in the tree
- Where: `src/mpe/paint.nim` (11 799 bytes, header: *"the particle-worlds floor-paint grid, the paint
  buff, and King of the Hill"*), `src/mpe/map_pool.nim`, `src/mpe/mapgen_styles.nim`;
  `paint` is imported by `src/mpe/sim.nim:13,16`.
- Design note says: §Sim module **Deleted**, lines 856-862 — *"the paint grid and the paint buff,
  King of the Hill and `hillTicks` … the procedural generator, the map pool"*, *"**Deleted, not
  disabled**"*; and §Repo layout (lines 1470-1473) does not list any of the three.
- Observed: they are dead at runtime — `sim_config.nim:59` defaults `floorPaint: false`,
  `sim_config.nim:765-770` makes `paintBuff`/`hill` require `floorPaint`, and neither `floorPaint`
  nor `hill` nor `paintBuff` appears in `game.config_schema` (52 properties, verified; the schema is
  `additionalProperties: false`), so no hosted config can enable them. `tools/mapkit.nim`,
  `tools/map_editor*`, `tools/gen_map_pool.nim`, `tools/map_render.nim` and `docs/pool-review.html`
  **are** gone (`ls tools/`). **[observed]**

### F12 — `coworld-release.yml`'s certify step does not pass `--timeout-seconds 300`
- Where: `.github/workflows/coworld-release.yml:167-175`; `grep -n "timeout-seconds"` on that file
  returns only `:311` (`upload-coworld --timeout-seconds 900`) and `:313`
  (`--hosted-smoke-timeout-seconds 1800`).
- Design note says: line 1442-1444 — *"The `certify` step in `coworld-release.yml` passes
  **`--timeout-seconds 300`** (the default 60 s does not cover start + connect grace + four rounds +
  linger — cooperative-hunting 0.1.2)."*
- Not on the checklist (item 12 fixes only the step **order**, which is correct here — see the
  Traced section). **[observed]**

### F13 — `game.protocols.player` and `game.protocols.global` carry identical text
- Where: `coworld_manifest_template.json`, `game.protocols.player.value` and
  `game.protocols.global.value` are both the whole 12 545-character `docs/PROTOCOL.md`
  (byte-identical; verified by length and by diffing the two strings).
- Design note says: line 1387-1391 — *"`player` documents the seat websocket … `global` documents
  the spectator frame"*, i.e. two different documents.
- Checklist item 10 requires only that **both** keys exist in object form, which they do. **[observed]**

### F14 — the landmark rejection sampler is a `while true` with no hard attempt cap
- Where: `src/mpe/field.nim:137-151`. The spacing relaxes by 20 px every 400 attempts and floors at
  `MinLandmarkSpacingPx` = 120 (`sim_types.nim:629`); once at 120 it never relaxes further, so the
  loop's termination is probabilistic, not bounded.
- Observed: the acceptance region is large — placement box is
  `1235 - 1 - 280 = 954` by `659 - 1 - 280 = 378` px with `landmarkMargin` = 140, and only border
  walls exist (`arena.nim:747-766`, `leftObstacles = @[]`) — so four points ≥ 120 px apart are
  accepted with high probability per draw. `tests/test_field.nim` runs 10 000 seeds (design line
  1503: *"the rejection sampler terminates for every one of 10 000 seeds"*), and the suite is green.
- Design note says: line 172 — *"`if attempts mod 400 == 0: spacing = max(120, spacing - 20)`
  # always terminates"*, i.e. this is the designed shape.
- Checklist item 5 says *"there is no unbounded loop"*; this loop is unbounded in form and
  terminating in practice. **[observed]** form, **[inferred]** practice.

### F15 — the game pod still serves `/client/replay`
- Where: `src/mpe/server.nim:824-853` routes `bitworldClient.ReplayClientRoute`,
  `bitworldClient.CoworldReplayClientRoute` and `LeagueReplayerPath` to
  `EmbeddedBroadcastReplayHtml` (`:73`). This is byte-inherited from the starter
  (`/workspace/starters/coworld-ctf/src/ctf/server.nim` has the identical block at the same lines).
- Design note says: §Server, lines 956-958 — the route is listed as inherited and intended.
- Checklist item 3 says *"No `/client/replay` pod path anywhere."* The **manifest** declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` and nothing else
  (`coworld_manifest_template.json`, `game.replay_viewer`); the only other occurrences of the string
  are inside the inlined `docs/PROTOCOL.md` route table. So no platform routing points at a pod;
  the pod simply also serves a dev page. **[observed]** — noted so the judge can rule on the literal
  reading.

### F16 — `tests/test_replay.nim`'s stream test is weaker than the design's test spec
- Where: `tests/test_replay.nim:165-184`. It asserts `counts["roundcard"] == 4`,
  `counts["register"] == 16`, `counts["directive"] >= 4`, `counts["result"] == 1`.
- Design note says: line 1555-1558 — *"the stream contains four `roundcard` records, **one
  `directive` per seat per turn**, at least one non-silent `symbol`, at least one `bump`, one
  `onpoint`, one `decode`, one `tag`, four `roundover`s and exactly one `result` record."*
- Observed: the non-silent symbol is covered at `:296-314`; `bump`, `decode`, `roundover`,
  `roundstart`, `word`, `firstword` are covered by the derived-event test at `:243-245`; `tag` is
  covered by the direct detector at `:249-275` (with an explicit note that a drifter pack does not
  reliably tag inside 540 ticks). **`onpoint` is asserted nowhere in the stream or the derived-kind
  list**, and the per-seat-per-turn directive count is relaxed to `>= 4`. **[observed]**

### F17 — the test change made during this run (`99dcaab`)
- Where: `git show 99dcaab -- tests/` — `tests/test_motion.nim:124-149`, +15/−2, the only test-file
  change after the initial authoring commits (`ff529a1`, `97fac7b`).
- Observed: the float-free grep changed from `if needle in code` to a `callsBanned` helper that
  requires the needle **not** be preceded by an alphanumeric or `_`. The stated motive is that
  `isqrt(` (`src/mpe/scoring.nim:22-45`, the integer square root that exists so the hashed path never
  calls libm) contains the substring `sqrt(`. No assertion was deleted, no test file removed, no
  `skip`/`xfail` added, the `check` remains, and the module list
  (`["field", "motion", "scoring", "beliefs"]`, line 137) is unchanged by the commit.
- The matcher only checks the character **before** the needle, so `floating` still trips and
  `myfloat` no longer does. The module list does **not** cover `control.nim` or `sim*.nim`, which the
  design note names (line 936); that narrowness predates this run.
- Checklist item 1, second half — I record this as the one test-file diff in the run so the judge can
  read the hunk itself. **[observed]**

### F18 — the `.tiny` breakpoint is `boardW <= 620`, not a literal `640px` rule
- Where: `client/replay_broadcast.html:4093`
  (`stage.classList.toggle('tiny', boardW <= 620)`) — byte-identical to
  `/workspace/starters/coworld-ctf/client/replay_broadcast.html:4312`. `grep -n 640` over the fork's
  page matches only a prose comment at `:1258`; the starter is the same.
- The label-hiding rules are `client/replay_broadcast.html:4197-4198`
  (`#stage.tiny .plate .mpe-round, #stage.tiny .plate .mpe-lbl { display: none; }`),
  `:4254`, `:4290`, `:4324-4325`, all asserted by `tests/test_viewer.nim:100-106`.
- Checklist item 11 says *"labels hidden under `640px`"*. The mechanism is the starter's `.tiny`
  density system at a 620 px board width; a board between 621 and 640 px keeps its labels.
  **[observed]** — reported so the judge sees the exact number rather than assuming a 640 px rule.

---

## Traced and consistent

**Resolution rules — the four scenarios, the field, the scoring.**
- `src/mpe/arena.nim:735-766` — `mapPath: "field"` builds a 1235 × 659 board, `leftObstacles = @[]`
  (border walls only), four corner anchors, `layoutCorners` + `symQuadMirror`, `validateMap()`.
  `MapWidth`/`MapHeight` = 1235/659 at `src/mpe/sim_types.nim:798-799`.
- `src/mpe/scoring.nim:17-20` — `closeness(d) = 1000 - min(1000, d*1000 div closeScalePx)`, exactly
  design line 242.
- `spread`: `scoring.nim:62-78` (nearest-particle closeness per mark, averaged over the four marks)
  and `:145-159` (`base - min(bumpPenaltyCap, bumps*bumpPenaltyPermille)`, `max(0, …)` then clamped)
  match design lines 252-256. `motion.nim:102-109` credits **one** bump tick per seat per tick, which
  is what design line 254 says and what keeps the guard's `bumps[s] <= tickCount` true.
- `deceive`: `scoring.nim:108-116` — `gc = goodCloseness(0)` (nearest non-role-0 seat),
  `vc = roleCloseness(0)`, `goodP = clamp(500 + (gc-vc) div 2, 0, 1000)`,
  `advP = clamp(500 + (vc-gc) div 2, 0, 1000)`, role 0 gets `advP`. Design lines 267-271, exactly.
- `crypto`: `scoring.nim:117-131` — `bc = roleCloseness(1)`, `ec = max(e1, e2)`,
  `pairP` to roles 0 and 1, `clamp(500 + (e_k - bc) div 2, …)` to roles 2 and 3. Design lines
  287-291, exactly.
- `tag`: `scoring.nim:135-143` — pursuer `min(1000, credit*1000 div tagTargetTicks)`, evader
  `(ticks - tagTicks)*1000 div ticks`. Design lines 302-307, exactly.
- Episode score: `scoring.nim:203-213` (mean of banked rounds, clamped 0..1000) →
  `roster.nim:685,691-692` (`permille/1000.0`, `win = not faulted and permille >= 500`).
  Design lines 313-317. Rounds never started are simply never banked (`scoring.nim:182-201`),
  matching design line 322.
- Roles: `field.nim:197-232` draws mode → roles (`(perm[s]+r) mod 4`) → landmarks → goal → key →
  spawn offset, in that fixed order, all from `sim.rng`. `field.nim:94-106` derives `perm` from a
  **separate** `initRand(int64(seed)*2 + 1)` stream with the int64 widening `62b3f3c` added.
- Physics: `motion.nim:16-50` — damp both axes (`vel*192 div 256`, dead-zone `stopThreshold` 8),
  then impulse, then per-axis clamp; `sim.nim:4032-4068` calls it in seat order and then the
  starter's `applyMomentumAxis` twice (Y then X). Design lines 191-198 and step 6.1, exactly.
  Alice is held at rest and zeroed each tick (`sim.nim:4053-4060`) while `turnAim` still runs
  (`sim.nim:4044`, `motion.nim:52-65`) — design lines 217-219.
- Kinematics: `field.nim:71-84` — `accel*pursuerAccelPct div 100` (250 → 187) and
  `maxSpeed*pursuerSpeedPct div 100` (1100 → 847). Design line 206.
- Step order: `sim.nim:4188-4203` is `dampAndDrive → resolveBumps → resolveTags → scoreTick →
  updateBeliefs → checkFieldInvariants → checkRoundEnd`, matching design steps 6.1–6.7 in order.
- `checkRoundEnd` (`sim.nim:4136-4148`) ends a round **only** on `gameTicksElapsed() >= maxTicks`,
  banks with `EndRuleFullTime`, no early win. Design step 6.7 and design line 369.
- The sim guard `checkFieldInvariants` (`sim.nim:4070-4134`) implements every invariant design lines
  941-947 list: in-box and non-wall particles, 4 marks, non-wall marks, palette colour, ≥ 120 px
  pairwise, `roleIndex` a permutation, `roundIndex` in range, `commSymbol` in the 9-value alphabet,
  `bumps <= tickCount`, `tagCredit <= tagTicks`, `tagTicks <= tickCount`, four distinct key symbols,
  banked permille in 0..1000. `tests/test_endings.nim:117-155` trips eight of them individually.
- `results.reason`/`endRule` enums: three and four values, `src/mpe/roster.nim:755-758` +
  `tests/test_endings.nim:11-16,157-177`.

**Decision path.**
- One parallel batch: `src/mpe/decide.nim:440-461` builds one `RequestBatch` with one `batch.post`
  per open seat and issues a single `client.curl.makeRequests(batch, deadlineMs div 1000)`.
  `tests/test_engine.nim:118-150` stands a real mummy fake up on 127.0.0.1:8791, holds every reply
  400 ms, and asserts `seen.len == 4`, `elapsed < 4*400`, and that at least one pair of *server-side*
  handler windows intersects. This is a real test of the simultaneous-decision clause, not an
  assertion about the code shape. Green in CI (log: `[OK] all four seats' calls go out in ONE
  parallel batch`).
- Tolerant parsing: `directives.nim:126-165` (`extractJsonObject`: balanced-brace scan that skips
  string contents and escapes, with a first-brace..last-brace rescue), `:212-227`
  (`cogs` accepted as array or id-keyed object), `:167-210` (int / float / numeric-string
  coordinates, `{x,y}` objects, NaN and ±1e9 rejected, clamp to the field box), `:116-124`
  (case- and hyphen-normalised intents, unknown → `go`), `:72-92` (first **rune**, upper-cased,
  gated on A..H). Every one of these is exercised by `tests/test_directives.nim:27-178`.
- Retry-once then scripted fallback: `decide.nim:429` (`while open.len > 0 and attempt < 2`),
  `:510-522` (anything still open plays `drifterFor`, `source = dsFallback`, with a `fallback`
  record). `tests/test_engine.nim:152-177` asserts exactly two batches of four and
  `source == dsFallback` on all four seats. (See F3 for the shipped-config caveat.)
- Throttle fail-fast: `llm.nim:187-193` sets `client.throttled` only when no candidate remains;
  `decide.nim:500-507` breaks before the retry. `tests/test_engine.nim:179-197` asserts one batch,
  not two, and `cause == "throttled"` ×4.
- Fallback causes are exactly the design's six-value enum
  (`timeout`, `parse_error`, `transport_error`, `throttled`, `no_credentials`, `budget_guard`):
  `decide.nim:401,435,485-492,516-520`.
- No credentials → instant disable with no network wait: `llm.nim:130-136`, and the log phrase
  `"the LLM provider is unavailable"` that phase 60 greps for; `"falling back"` at
  `decide.nim:404,524`. `tests/test_engine.nim:312-328` asserts four `no_credentials` records.
- Budget guard: `decide.nim:372-379` fires when `elapsed + 2*turnBudgetSeconds >
  wallClockBudgetSeconds`, writes one `budget_guard` record and switches every remaining turn to the
  scripted layer. `tests/test_engine.nim:255-278` asserts zero network calls after it fires.
- No particle is ever unactuated: `decide.nim:314-347` (`repairMissingOrders`: this turn's → last
  turn's → drifter's) and `server.nim:1989-1998` (a seat with no directive at all gets
  `drifterFor`). `tests/test_engine.nim:280-293` asserts a non-empty directive for every seat on
  turns 1..5.
- Deadline validation: `sim_config.nim:739-757` rejects sub-second and non-whole-second
  `attempt1Ms`/`retryMs` and rejects `attempt1Ms + retryMs > turnBudgetMs`.
  `tests/test_engine.nim:219-235` pins both.

**Waits and their bounds.** Every `sleep`/`while true` in the runtime path, enumerated:
- `decide.nim:422` — spacing sleep, bounded by `turnSpacingMs` (the `min()` is redundant but safe:
  `since < turnSpacingMs` at that point, so the value is `turnSpacingMs - since` ∈ (0, 9000]).
- `decide.nim:432,460` — the two batch deadlines (6 s, 3 s) and the outer 10 s monotonic check.
- `server.nim:998-1008` — the frame limiter, bounded by `frameDuration` with `sleep(1..2 ms)` slices.
- `server.nim:1386` — the main loop, exited by `quitAfterFrame` from (a) the wall-clock stop
  (`:1409-1423`, `wallClockBudgetSeconds` 690), (b) `gamesPlayed >= maxGames` (`:2096-2098`), or
  (c) a `fault` (`:2041-2060`).
- `server.nim:2305-2312` — the post-artifact shutdown grace, bounded by `ShutdownGraceSeconds`.
- `server.nim:1542-1576` — `lobbyJoinTimeoutTicks` on the connect wait, with `declarePlayerFailure`
  for the lowest missing slot.
- `server.nim:446` — the anonymous-name generator; terminates because `nextIndex` increments.
- `field.nim:137` — see F14.
- `src/particle_worlds_player.nim:82-90` (240 × 500 ms dial), `:114-147` (outer loop bounded by
  `ReconnectAttempts` 6). The inner `while true` at `:119` is a blocking `socket.receiveMessage()`
  that exits on the exception whisky raises on a close frame — this file is byte-equivalent to the
  starter's `src/paintball_player.nim` modulo names (verified by a name-normalised `diff`: 8 hunks,
  all prose).
- Arithmetic against the 720 s budget: every shipped variant carries
  `wallClockBudgetSeconds: 690` and the certification fixture 180
  (`coworld_manifest_template.json`); `tests/test_manifest.nim:133-139` computes
  `episode_timeout_minutes * 60 * 6 div 10`, asserts it equals 720, and asserts every variant and the
  fixture are `<= 720`. The `docker-smoke` episode ran in 36 s wall clock (CI log 09:30:43 → 09:31:19).

**Rune-safe truncation.**
- `directives.nim:63-70` — `truncateRunes` uses `runeLen`/`runeSubStr`, the single place any recorded
  string is shortened. No byte slice reaches the replay on any path I traced.
- Call sites: `note` → `sanitizeNote` (`directives.nim:111-114`, `MaxNoteRunes` 160);
  `register.policy` → `decide.nim:246` (`MaxPolicyLabelRunes` 48);
  `fallback.detail` → `decide.nim:232` (`MaxFallbackDetailRunes` 200);
  the whole serialized `directive` record → `boundedDirectiveRecord` (`directives.nim:341-358`,
  `MaxDirectiveRunes` 900, shrinking only the note, guard-bounded at 12 iterations);
  provider error bodies → `llm.nim:180,188,196,205`; `PLAYER_PROMPT` → `llm.nim:266`
  (`MaxPromptRunes` 4000, never written to the replay).
- `parseSymbol` (`directives.nim:72-92`) takes the first **rune**, not the first byte.
- Test: `tests/test_directives.nim:123-148` — 159 ASCII runes then U+1F680 then `"TAIL"`, asserts
  `runeLen == 160`, `validateUtf8() == -1`, `endsWith("\u{1F680}")`, and that the whole serialized
  record re-parses. `:150-164` feeds 160 four-byte runes (640 bytes) and asserts the record still
  parses as JSON. `:166-173` pins `sanitizeNote` on 2-byte runes. This is checklist item 9 in full.
- `tests/test_replay.nim:296-322,326-348` re-checks it end to end with a non-ASCII policy label and
  note through `tools/replay_summary.py`'s stdout under strict UTF-8.

**Replay writer and re-derivation.**
- The determinism boundary is `server.nim:1976-2002`: one `compileMask` per particle per tick, fed
  both to `sim.step` and to `replayWriter.writeInputMaskChange`; `server.nim:2070`
  `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` every tick. Lobby/game-over ticks
  write explicit zero masks (`:2004-2012`) so `prev` cannot diverge at a round boundary.
- `gameHash` (`sim_state.nim:289-333`) appends every field the design lists at lines 927-931 —
  `roundIndex`, `mode`, `roleIndex[0..3]`, `perm[0..3]`, `spawnOffsetBrads`, `goalLandmark`,
  `keySymbols[0..3]`, every landmark `(x,y,colour)`, per seat
  `bumps/roundAccum/tagCredit/nearestMark/settledTicks/decodedMark/onPointDone/tagContact`,
  `coverAccum`, `tagTicks`, `roundsPlayed` and every `roundLog` entry — and **excludes**
  `commSymbol`/`commPrev`/`commTurn`, which are only touched by `installSymbol`
  (`sim_state.nim:340-351`) and `pushFeedDirective` (`:353-381`), both documented and both
  presentation-only. `recentShouts` (which *is* hashed, `sim_state.nim:280-288`) is **not** used for
  the symbol bubbles — `global.nim:5381-5434` reads `sim.commSymbol` directly, and `sim.nim:3893`
  clears `recentShouts`. That resolves the tension the design note's step 6.8 wording created.
- `roundIndex` advances **inside** the step, in `resetToLobby` (`sim.nim:3910-3911`), reached from
  `step`'s GameOver branch (`sim.nim:4175-4179`), so the replayed sim re-derives it. The server
  explicitly does *not* advance it (`server.nim:2087-2088`).
- Re-derivation test: `tests/test_replay.nim:134-163` parses the recorded bytes, builds a fresh sim
  from the recorded **config only**, replays through `advanceReplayFrame`, and asserts
  `player.hashMismatchTick == -1` across the whole hash stream — with the landmark draw, colour
  permutation, role cycle and key all re-derived rather than read from records. This is checklist
  item 2's "frame by frame" assertion.
- The viewer derives its display from that same re-derivation, not from a parallel recording:
  `replay_runtime.nim:83-138` builds the packet from the **re-simulated** `sim`
  (`sim.buildSpriteProtocolUpdates(...)` and `sim.buildStateJson(...)`), and
  `replay-viewer/mpe_replay.nim:41-44,95-113` calls exactly that after each
  `replay.advanceReplayFrame(game, …)`. There is no second state source anywhere in the path.
- Native↔wasm gate: `.github/workflows/ci.yml:366-377` runs
  `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer "${REPLAY}" 300`; CI log line
  `ok: loaded replay.json, advanced 300 frames (6600261 packet bytes, heap 148 MB)`.
- Record vocabulary: `register` (`decide.nim:235-249`, redacted — no `prompt` key, asserted by
  `tests/test_identity_privacy.nim:82-89`), `roundcard` (`decide.nim:251-281`),
  `directive` (`directives.nim:305-339`), `fallback` (`decide.nim:222-233`),
  `budget_guard` (`decide.nim:294-295`), `result` (`decide.nim:283-292`, the full results document
  embedded once so the bytes are self-sufficient).
- Replay size: `tests/test_replay.nim:350-351` asserts < 1 MB; CI's real episode was 31 394 B.

**Manifest.**
- `num_agents: 4` in all five variants (`default`, `coop`, `deception`, `comms`, `chase`) **and** in
  `certification.game_config`; `len(certification.players) == 4`;
  `len(certification.game_config.players) == 4`. Verified directly from the JSON and asserted by
  `tests/test_manifest.nim:23-33`.
- `tools/ci/docker_smoke.sh:106-152` enforces all four seat-count invariants the checklist names —
  `num_agents` present (`:110-118`), a positive integer (`:120-126`), `len(certification.players)`
  equal to it (`:129-134`), `len(certification.game_config.players)` equal to it (`:135-140`) — plus
  `SMOKE_SEATS` as an independent second declaration (`:141-152`), every one prefixed
  `SEAT-COUNT FAIL:`. **`grep -c "SEAT-COUNT FAIL" ` over the full CI log for run 32953267780 returns
  0**, and the job printed `game=particle-worlds seats=4` and `smoke OK: seats=4 … reason=complete`.
- `game.docs` shape: `readme` = `{"type":"text","value":…}` (7 207 chars) and `pages` = three
  entries, each `{"id","title","content":{"type":"text","value":…}}` — `rules` (12 036),
  `protocol` (12 545), `commanding` (6 595). All non-empty. Checklist item 10 satisfied.
- `game.protocols` carries **both** `player` and `global`, each in object form (see F13 for the
  content observation).
- `game.replay_viewer = {"bundle": "static-replay-viewer"}`; no top-level `replay_viewer`, no
  top-level `version`, no `game.display_name`; `episode_timeout_minutes: 20`; `game.owner` present;
  `tags` exactly the seven the note lists.
- `game.runnable.env.ANTHROPIC_API_KEY_URI =
  "secret://coworld/particle-worlds/anthropic_api_key"`, matching `game.name`
  (`tests/test_manifest.nim:191-197`).
- `results_schema`: `additionalProperties: false`, exactly 22 properties matching
  `particleResultsJson`'s 22 keys (`roster.nim:737-762`), required list as specified.
- `config_schema`: `additionalProperties: false`, `required: ["tokens","players"]`, every array
  property (`tokens` 4/4, `players` 4/4, `slots` 4/4, `rounds` 1/4) carries `minItems`/`maxItems`,
  `num_agents` is `integer 4..4 default 4`.
- The manifest is generated, not hand-edited: `.github/workflows/ci.yml:104-110` runs
  `python3 tools/build_manifest.py --check`.
- Placeholder gate: the checklist's exact `grep` over the three names across
  `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`, `docker_smoke.sh`, `policies.json`
  returns nothing → exits 0.
- `tools/ci/policies.json`: four policies, all `"run": "/bin/particle-worlds-player"` —
  `particle-worlds-swarm` (`PLAYER_PROMPT`), `particle-worlds-cipher` (`PLAYER_PROMPT`, and
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` — champion #2, as required),
  `particle-worlds-drifter` and `particle-worlds-beeline` (both `PLAYER_SCRIPTED`).
  Two LLM champions + two scripted fillers.
- Release order: `coworld-release.yml` runs build (`:153`) → certify (`:167`) → **upload the
  policies** (`:206`) → upload-coworld (`:304`) → secret put (`:342`), in that order, with the
  ordering rationale in the header comment at `:10-16`. All three workflows present.
  `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both committed `100755`
  (`git ls-files -s`), and `ci.yml:173-182,237-249` asserts the exec bit before invoking either
  by path.

**Static viewer / viewer executes.**
- CI run **32953267780** on `main` at the reviewed sha `99dcaab`: `conclusion: success`;
  `test` ✓ 9m24s, `docker-smoke` ✓ 1m54s, `wasm-viewer` ✓ 2m45s.
- `wasm-viewer` `needs: docker-smoke` (`ci.yml:224`), downloads the `smoke-replay` artifact
  (`:289-292`), and the `Load the bundle in a real browser` step **ran** with
  `--bundle dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90 --soak 12
  --strict-text-bounds` (`ci.yml:331-336`). No `continue-on-error` anywhere in the job.
  Output: `{"loaded":true,"ms":2089,"clock":"0:00 TIME LEFT ROUND 2/4 · DECEIVE · TURN 1/2",
  "scorebug":"○ P1 GOOD 0.751 0.78 THIS ROUND — … ◈ P2 ADVERSARY …","feed_lines":0}` and
  `soak: 12s of playback kept advancing ("0 / 1035" -> "236 / 1035" -> "284 / 1035")`.
- Both markers are set from the shell's own code paths:
  `replay-viewer/static_replay.js:158-162` sets `data-replay-loaded="true"` in the `'loaded'`
  branch, and the Worker posts `'loaded'` only **after** `ingestPacket()`
  (`static_replay_worker.js:125-130`); `showFailure()` at `static_replay.js:8-20` sets
  `data-replay-error`. `tests/test_viewer.nim:239-256` pins both.
- **Emscripten flags and the JS bootstrap are the same lineage.** `replay-viewer/config.nims` has
  **no** `MODULARIZE` and **no** `EXPORT_NAME` (lines 42-55: `-s ALLOW_MEMORY_GROWTH`,
  `-s ABORTING_MALLOC=1`, `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`,
  `-s EXPORTED_RUNTIME_METHODS=HEAPU8`, `--preload-file …/data@data`, `-o …/mpe_replay.js`,
  and the `_mpe_*` export list). The worker declares `var Module = {}` (`static_replay_worker.js:8`),
  waits on `Module.onRuntimeInitialized` (`:188`), sets `self.Module = Module` (`:192`) and
  `importScripts('./wire_constants.js', './broadcast_core.js', './mpe_replay.js')` (`:239`) — the
  non-modularized pairing. I diffed all four viewer files against
  `/workspace/starters/coworld-ctf/replay-viewer/`: **every difference is the `ctf`→`mpe` identifier
  rename and nothing else** (config.nims 4 hunks, worker 13 hunks, shell 2 hunks, all renames).
  `tests/test_viewer.nim:251-255` asserts `MODULARIZE notin flags` and `EXPORT_NAME notin flags`.
  This is the cogame-lantern hazard, and it is clean here.
- The bundle contacts nothing but the replay URL: `static_replay_worker.js:113-116`
  `fetch(message.replayUrl, {credentials:'omit', mode:'cors'})` is the only network call in the
  bundle.
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` clean), so no
  substitution weakened the harness.

**Chrome provenance (page).**
- `client/replay_broadcast.html` is 4 676 lines against the starter's 4 660 — a fork, not a rewrite.
  The banner `particle-worlds additions to the inherited coworld-ctf chrome` is at line **4125** and
  occurs exactly once (`tests/test_viewer.nim:117-119`). The starter's own appended
  `PAINTBALL additions…` banner sat at its line 4344; the fork's block replaces it, so the page
  carries exactly one game block (`PaintballChrome`, `PB_MODE`, `PB_CTX` all absent —
  `tests/test_viewer.nim:122-124`).
- I diffed the whole page against the starter (1 327 diff lines, 565 removed / 581 added). Every
  above-banner hunk falls into one of: the `ctf`→`mpe` rename (title, `CtfStaticReplay`,
  `ctf-replay`/`ctf-shell`, `CTF-Doubles` comment), the `#viewpanel` removal (CSS 705-833, the
  `body[data-noviewpanel]` rule 1452-1459, the markup 1506-1523, the `?viewpanel=0` handler
  1876-1885, the zoom/minimap JS 4132-4244, the z/x/0 keys 3971-3975), the dead beat CSS
  (`.kill`/`.steal`/`.return`/`.capture` at 917-934), the `.ec-heart` block (1221-1239), and the
  `PB_MODE`→`MPE_MODE` plate/endcard/verdict retarget — which sat above the starter's own banner too.
  These are exactly the removals design lines 1206-1219 list.
- Sections 1–5 survive: `tests/test_viewer.nim:30-40` asserts all 30 inherited ids
  (`#viewport`, `#stage`, `#board`, `#lightpool`, `#grain`, `#lockerroom`, `#chrome`, `#scorebug`,
  `#plates-l/r`, `#clock*`, `#bannerlane`, `#killfeed`, `#fpv`, `#povBadge`, `#mmwarn`,
  `#transport`, `#scrub`, `#momentum`, `#lulls`, `#scrub-fill/win/head`, `#speedchips`,
  `#ffwd-chip`, `#win-chip`, `#tick-clock`, `#endcard`).
- Transport rules, each checked in the page:
  (a) `relayout()` sets `--band`, `--topband` and `--hudscale` on **`document.documentElement`**
      (`tests/test_viewer.nim:63-71` asserts `root.style.setProperty` plus all three names);
  (b) nothing fixed-positioned sits in the band — `tests/test_viewer.nim:78-87` opens each of
      `#mpe-rail`, `#mpe-radio`, `#mpe-crypto` and asserts `top:` present and `bottom:` absent;
  (c) `#endcard { … bottom: var(--band, 0px) }` is kept and every seek runs
      `$('endcard').classList.remove('on')` (`tests/test_viewer.nim:73-76`);
  (d) beats are labelled `<button>`s that seek: `function mpeBeat(` +
      `document.createElement('button')` + `el.setAttribute('aria-label', label)` +
      `CTX.send('s:' + tick)` (`tests/test_viewer.nim:174-178`), named `mpeBeat` so the chrome
      alias block's hoisted `var markBeat` cannot shadow it, with a generic collision check over
      the whole `MPE_CTX` alias list (`tests/test_viewer.nim:134-155`).
- Beat-kind CSS is exactly the five kinds the sim emits and no others: `src/mpe/replays.nim:679-683`
  declares `@["roundstart","firstword","onpoint","tag","roundover"]` for `numAgents > 0`, and
  `tests/test_viewer.nim:157-173` reads that literal out of `replays.nim`, requires
  `.beat-marker.<kind>` for each, and requires the eight dead kinds to be **absent**.
- `#viewpanel` decision: dropped, as the design note says (lines 1207-1212) for a fixed 1235 × 659
  arena. `tests/test_viewer.nim:42-61` asserts all 15 markers, CSS selectors and JS symbols
  (`attachMinimap(`, `ZOOM_STEP`, `SLIDER_TRAVEL`) are gone from the non-comment code, not merely
  hidden. `client/broadcast_core.js` stays byte-identical-but-for-`MPE_WIRE` because
  `pendingMinimap` tolerates the missing element.
- `client/broadcast_core.js` differs from the starter's in exactly one line
  (`:49`, `window.CTF_WIRE` → `window.MPE_WIRE`, two occurrences on one line), which is precisely
  what design line 1197-1198 allows and what `tests/test_viewer.nim:193-197` pins by sha.
- `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` at
  `client/replay_broadcast.html:4152-4157` — character-for-character the starter's rule
  (`/workspace/starters/coworld-ctf/client/replay_broadcast.html:4369-4374`) — asserted by
  `tests/test_viewer.nim:89-99`. Checklist item 11's first half.

**Both name spaces.**
- Agents see aliases only: `decide.nim:132,142,155,177` build every id from `sim.cogAlias(i)`;
  `roster.nim:64-105` keeps `IdentityNames`/`slotIdentityIndex`/`shoutIdentityName` untouched from
  the starter; the symbol-bubble label is `labelShout(teamText, IdentityNames[...], text)`
  (`global.nim:5453-5455`).
- The viewer maps aliases to real names: `roster[].name` carries the policy name, `results.names`
  carries it (`roster.nim:686-690`), and the scorebug renders it — visible in the CI smoke's own
  scorebug string (`○ P1 GOOD 0.751 …`).
- `tests/test_identity_privacy.nim:32-135` asserts both directions with a sentinel address across
  all four modes: absent from every seat view, from both LLM messages, from every `directive` and
  `register` record and from the bubble label; **present** in `buildStateJson`, in all four
  `roster[].name` entries and in `results.names`. Checklist item 4, both halves.

**Scripted baseline plays full episodes legally.**
- Legality: `tests/test_control.nim:37-77` — 4 modes × 125 scattered states × 2 baselines × 4 seats =
  4 000 checks that the directive validates against the reply schema (own id, enum intent, target
  inside the field box, `note` ≤ 160 runes, symbol a single rune from the 9-value alphabet) and that
  the compiled mask never sets Up+Down, Left+Right, `A` or `C`. CI log:
  `[OK] 500 random states x 2 baselines x 4 modes x 4 seats are all legal`. Legality is
  structural in `control.nim:441+` (one sign per axis), and `A`/`C` are never emitted.
- Natural end with `reason == "complete"`: `tests/test_replay.nim:20-114` plays a full all-`drifter`
  four-round episode through the **real** replay writer to its natural end, and `:316` asserts
  `summary["results"]["reason"] == ReasonComplete` (and `roundsPlayed == 4` at `:315`).
  `tests/test_endings.nim:50-63` independently asserts `reason == complete`,
  `endRule == full_time`, `roundsPlayed == 4` on a four-round run.
  The production image does the same in Docker: CI log `episode end reason: complete`,
  `all 4 player containers exited 0`.
- Baseline tuning is evidenced rather than guessed: `tests/test_control.nim:180-241` asserts the
  `drifter` × 4 episode completes four rounds, covers ≥ 80 % in `spread`, gets its `crypto` Bob onto
  the goal, and **beats** `beeline` × 4 on the mean at the pinned seed. That is a comparative bar,
  not a grid harness; I found no grid-search harness in the tree and the design note does not
  describe one.

**Field/scoring/parse tests present and green.** All 15 `tests/*.nim` ran in **both** debug and
release in the `test` job (`ci.yml:111-157`), and the job is green.

---

## Could not determine

- **Whether `results.bumps` was intended to be per-episode or per-round (F9).** The design note
  gives an example array and an endcard column but never states the aggregation. Settled by: a line
  in the design note, or a test asserting one or the other.
- **Whether F3's retry suppression ever fires in a hosted run.** It needs a hosted episode with
  `turnSpacingMs = 9000` and an attempt-1 timeout. Settled by: a phase-60 replay whose `fallback`
  records show `attempt: 2, cause: "timeout"` with no second batch in the game log, or a unit test
  that calls `engine.turn` twice with `variantConfig` and a hung provider and counts the recorded
  request windows.
- **Whether the `#stage.tiny` 620 px breakpoint (F18) is what "labels hidden under 640px" means.**
  Both the starter and the fork use `<= 620`; neither has a 640 px rule. Settled by the judge
  reading the checklist against the starter's convention.
- **The `coworld-replay` postMessage bridge's `ready` ordering** (design lines 1185-1187). I found
  no `coworld-replay` bridge in either the fork or the starter — the page posts
  `{src: 'mpe-replay'}` (`client/replay_broadcast.html:1717`, the starter's `'ctf-replay'` at its
  `:1919`) and `static_replay.js:151` fires `config.onFirstFrame` *after* the `'loaded'` branch has
  set the attribute (`:158-162`), which is the ordering the note asks for. Settled by naming which
  bridge the note means.
- **Whether the design note's `certify --timeout-seconds 300` (F12) is a hard release requirement.**
  Not on the checklist; settled by phase 40.
