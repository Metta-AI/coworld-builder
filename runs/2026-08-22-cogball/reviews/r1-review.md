# r1 review — cogball

Repo: `Metta-AI/cogame-cogball` @ `812c661d72bca98b9770f1799c214230d7b2e086` (branch `main`),
cloned to `/workspace/scratch/review-cogball`.
Design note: `/workspace/coworld-builder/runs/2026-08-22-cogball/design.md` — byte-identical to
`docs/plans/2026-08-22-cogball-design-v2.md` in the repo (verified with `diff`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Files read: 47 (all 24 `src/**.nim`, `replay-viewer/cogball_replay.nim` + `config.nims` +
`static_replay*.js`, all 12 `tests/*.nim` + `tests/lib/helpers.nim`, all 8 `tools/**`, all 3
workflows, `Dockerfile.replay-viewer`, `coworld_manifest_template.json`, `compose.yaml`,
`config.json`, `AGENTS.md`, `client/replay_broadcast.html` (targeted), the starter
`coworld-ctf/client/` for comparison).
CI evidence: run **32613856995**, conclusion `success`, `headSha 812c661d…` — confirmed via
`gh run list -R Metta-AI/cogame-cogball --branch main -w ci.yml`. Jobs `test`, `docker-smoke`,
`wasm-viewer` all `success`. `grep -c "SEAT-COUNT FAIL" ci.log` → **0**.

**Summary: I found nothing in this tree that I can show falsifies a named acceptance-checklist
item.** All 38 findings below are divergences from the design note, gaps in what a test actually
asserts, or dead/unreachable code. The register is neutral: each finding states what the code does
and what the note says. Severity is left to the judge.

Legend on each finding: **Observed** = I read it at the cited lines. **Inferred** = I reasoned
from the code without running it. **Untested** = it would take a run to settle.

---

## Findings

### A. The resolution rules (note §The game)

**F1 — pass/interception attribution is derived from every kick, not from `intent: "pass"`.**
- Where: `src/cogball/sim.nim:318-319` (`pendingPass` armed on *every* kick), `sim.nim:440-450`
  (next different toucher → `passesCompleted` or `interceptions`).
- Observed: `applyKicks` sets `sim.pendingPass = PassRecord(...)` unconditionally for any robot
  whose kick lands, regardless of the directive's intent. `recordTouch` then credits a completed
  pass or an interception on the next different toucher inside `PassWindowTicks` (96, correct).
- Note says: §Shots, saves, passes — "A kick made **under intent `pass`** whose next touch is a
  different robot of the same seat within 96 ticks is a completed pass".
- Context: the code comment at `sim.nim:437-439` and `AGENTS.md` §"The control layer is OUTSIDE the
  determinism boundary" state the reason explicitly — the sim can never read a directive, because
  pass/save counters are inside `gameHash` (`sim_state.nim:116-117`). The divergence is deliberate
  and documented in the repo; the note was not updated to match.

**F2 — the effective scoring band is narrowed by the ball radius.**
- Where: `src/cogball/pitch.nim:37-44` (`xBounds`) vs `pitch.nim:73-82` (`goalScoredBy`).
- Observed: `goalScoredBy` tests the ball **centre** against `[GoalYMin, GoalYMax]` = [9 m, 16 m],
  exactly as the note's step 6.8 says. But `xBounds(y, radius)` only opens the goal plane when
  `y >= GoalYMin + radius and y <= GoalYMax - radius`; `resolveBallWalls` (`sim.nim:538-548`) runs
  immediately before the goal test in the same substep and clamps `ball.x` to `PitchXMin + radius`
  otherwise. Net: a ball whose centre is within `BallRadius` = 0.35 m of the mouth edge is walled
  off and cannot cross the plane, so the realised mouth for the centre is y ∈ [9.35 m, 15.65 m].
- Note says: the goal test is on the centre against the full 7 m band; the walls are "the
  goal-line segments … **outside the mouth**".
- Inferred (from the substep order at `sim.nim:595-606`), not run.

**F3 — the stalemate box is ±1 500 000 µm, i.e. 3 m across.**
- Where: `src/cogball/sim.nim:654-662`, `src/cogball/sim_types.nim:104`.
- Observed: `if abs(dx) <= StalemateBox and abs(dy) <= StalemateBox` with
  `StalemateBox = 1_500_000`. The counter therefore runs while the ball stays inside a 3 m × 3 m
  square centred on the anchor.
- Note says: "inside the **1 500 000 µm box** anchored where the counter last reset" — ambiguous
  between half-width and full width; the code reads it as half-width.
- Everything else in step 8 matches: increment-then-compare (`>=`) means the drop fires on the
  240th consecutive tick, which `tests/test_physics.nim:252-257` pins exactly.

**F4 — the kickoff freeze also zeroes the ball's velocity.**
- Where: `src/cogball/sim.nim:630-641`.
- Observed: the frozen branch zeroes every robot's `vx/vy/spin` **and** `sim.ball.vx/vy`.
- Note says: step 2 — "every robot's mask is forced to 0, every velocity and `spin` is set to 0".
  The ball is not named. Harmless in practice (the kickoff reset already zeroes it at
  `sim.nim:149`), but it is one extra thing the frozen branch writes.

**F5 — the seeded jitter stream advances twice before the first played tick.**
- Where: `src/cogball/sim.nim:109` (`initSimServer` → `kickoffReset`) and `sim.nim:234`
  (`startGame` → `kickoffReset`).
- Observed: `kickoffReset` draws four `sim.rng.rand(500_000)` values (`sim.nim:172`). It runs once
  at construction and again at `startGame`, so the placement a match actually kicks off from is
  the *second* draw set.
- Note says: "Each of the four flank robots gets a deterministic y jitter of
  `sim.rng.rand(500_000) − 250_000`". It does not describe a double reset.
- Determinism is unaffected: the viewer reconstructs with `initSimServer(config)`
  (`replay_runtime.nim:25`) and re-steps, so both draws happen in the same order.

**F6 — the `drop` broadcast beat is inferred from a counter transition, not from the sim event.**
- Where: `src/cogball/broadcast.nim:127-130`.
- Observed: `if sim.stalemateTicks == 0 and tracker.stalemate >= 1 and … and tracker.stalemate >=
  int32(sim.config.stalemateTicks) - 1`. A ball that *leaves* the box on the exact tick where the
  previous tick's counter read 239 also resets the counter to 0 (`sim.nim:660-662`) and satisfies
  every clause, so a spurious `drop` beat is emitted with no drop having happened.
- Note says: §Record and event vocabulary B — `drop` is a derived beat. It does not specify how.
  Consequence is confined to a scrubber marker and the beat list (never hashed).
- Inferred, not run.

**F7 — the match-start kickoff emits no `kickoff` broadcast beat.**
- Where: `src/cogball/broadcast.nim:136-139`.
- Observed: the `kickoff` chrome event is gated on `sim.lastGoalTick == int32(tick)`, so it only
  fires on the restart *after a goal*. `startGame` → `kickoffReset` emits the tier-2 `Kickoff`
  `SimEvent` (`sim.nim:178`) but sets no `lastGoalTick`.
- Note says: §B lists `kickoff` among the derived broadcast events without qualification.

**F8 — the neutral drop clears more state than the note describes.**
- Where: `src/cogball/sim.nim:198-201`.
- Observed: `neutralDrop` resets `lastTouch`, `prevTouch`, `pendingShot` and `pendingPass` in
  addition to the ball, the robots inside 3 m and the counter. All four are inside `gameHash`
  (`sim_state.nim:118-131`), so this is part of the recorded truth, as the note requires — it is
  simply more than the note enumerates.

### B. The decision path (note §Decisions)

**F9 — the `turnBudgetMs` cap is a pre-issue check, not an interrupt; the realised worst case is
~9.0 s, not the note's 8.5 s.**
- Where: `src/cogball/decide.nim:284-286` (deadline), `decide.nim:332-342` (the attempt loop),
  `decide.nim:214-223` (`curlyBatch`, `max(1, timeoutSeconds)`).
- Observed: `allowedMs = min(wantMs, remainingMs)` is evaluated *before* each batch; nothing
  interrupts a batch already in flight. The transport timeout is `(allowedMs + 999) div 1000`
  whole seconds, so `retryMs = 2500` becomes a **3 s** curl timeout. Worst case 6 s + 3 s = 9.0 s
  against the 9.0 s cap, plus body-building and parse time.
- Note says: "attempt 1 batch deadline 6.0 s … retried once … with a 2.5 s deadline. Worst case
  8.5 s ≤ the 9.0 s `turnBudgetMs` cap enforced by a monotonic deadline around the whole turn."
- The code comment at `decide.nim:211-213` acknowledges the rounding. The note's own budget table
  already charges 40 × 9.0 s = 360 s, so the arithmetic downstream is unchanged.
- `tests/test_engine.nim:68-97` bounds a hung client, but its assertion is `elapsed < 3000` ms
  against a 300 ms configured budget — a 10× margin, not the budget.

**F10 — a `fallback` record is written for attempt 1 even when the retry succeeds.**
- Where: `src/cogball/decide.nim:371-379`; consumed at `tools/replay_summary.py:200-201`.
- Observed: any non-ok reply on attempt 1 writes `{"k":"fallback","attempt":1,…}` and *then*
  re-queues the seat. `replay_summary.py` increments `fallbacks` for every such record.
- Note says: §Record vocabulary A gives `fallback` an `attempt` (1|2) field, so per-attempt
  records are by design — but the phase-60 recipe in §Replay bytes reads `.fallbacks` alongside
  the count of `source=="llm"` directives, and `.fallbacks` will exceed the number of turns that
  actually fell back.

**F11 — the timeout/transport-error split is a substring test on the transport's error text.**
- Where: `src/cogball/decide.nim:354` — `if reply.error.contains("imeout"): "timeout" else:
  "transport_error"`.
- Observed: the cause label depends on curl's message wording. Both labels are in the note's legal
  cause set, so a misclassification changes only the recorded reason string.

**F12 — `output_config.effort` is never set on the Bedrock path.**
- Where: `src/cogball/llm.nim:139-150`.
- Observed: the `effort` block is added only in the `else` (Anthropic direct) branch, and there
  only when `"haiku" notin client.model and "4-5" notin client.model`. On Bedrock the model comes
  from `bedrockModels` (`llm.nim:79-83`) and `client.model` is not consulted, so the field is never
  emitted regardless of the model string.
- Note says: "**No `output_config.effort`** when the model string contains `haiku` or `4-5`". The
  code is strictly more conservative than the rule; the Bedrock default list leads with a
  `haiku-4-5` profile, so the outcome matches for the default case.

**F13 — a mid-episode auth failure is later recorded as `cause: "no_credentials"`.**
- Where: `src/cogball/llm.nim:157-164` (401/403 sets `client.disabled = true`),
  `src/cogball/decide.nim:312-324`.
- Observed: once `client.disabled` is set, every subsequent turn takes the instant-fallback branch
  and records `cause: "no_credentials"` — even though credentials were present and were rejected.
- Note says: the cause enum is `{timeout, parse_error, transport_error, no_credentials,
  budget_guard}`; the label is legal, the attribution is coarse.

Everything else on the decision path traced clean — see §Traced and consistent.

### C. Waits and bounds (note §Decisions "Degrade, never hang")

**F14 — `fault/host_error` is unreachable, and an unexpected exception writes no artifacts.**
- Where: `src/cogball/sim.nim:729-731` (`hostErrorStop`), `src/cogball.nim:94-102`
  (`runServerLoop` call site), `src/cogball/server.nim:747-764` (the artifact-write block).
- Observed: `grep -rn hostErrorStop src/ tests/ replay-viewer/ tools/` returns **only** the
  definition — it has no caller. `runServerLoop(...)` at `src/cogball.nim:94` is not inside a
  `try`. The artifact block (`writeReplay`, `eventsJsonl`, `writeResults`) is reached only via
  `quitAfterFrame` at `server.nim:747`. So an unexpected exception inside the loop unwinds out of
  `isMainModule` with a traceback, and no `results.json`, no replay upload and no events file are
  written — only `defer: replayWriter.closeReplayWriter()` (`server.nim:411-412`) runs.
- Note says: §End conditions — "`fault` | `host_error` | An unexpected server-side exception. Same
  treatment; **best-effort artifacts written before re-raising**." `endRuleText(erHostError)`
  (`sim_types.nim:523`) and the manifest's `endRule` enum both declare the value.
- Inferred from the call graph, not run. `tests/test_engine.nim:228-232` covers `sim_fault` only,
  and does so by calling `finishGame` directly (see F27).

**F15 — `shouldAbortFiniteMatch` has no caller.**
- Where: `src/cogball/sim.nim:238-243`. Confirmed by grep across `src/`, `tests/`, `tools/`,
  `replay-viewer/`. Dead code; its docstring describes a lobby-collapse path nothing invokes.

**F16 — the 690 s clock starts *after* the board bake, which is itself unbounded.**
- Where: `src/cogball/server.nim:433-441` (the bake block) then `server.nim:466`
  (`episodeStart = getMonoTime()`), and `server.nim:611-616` (the stop, `elapsed >=
  config.wallClockBudgetSeconds`).
- Observed: `sim.warmBoardRenderCaches()` runs before `episodeStart` is taken, so bake time is not
  charged against `wallClockBudgetSeconds`. Total process wall clock is therefore
  `bake + ≤690 s + gameOver hold + artifact writes` against the 720 s settle requirement.
- Note says: the arithmetic table charges "engine hard stop `wallClockBudgetSeconds` = 690 s" and
  claims an absolute worst case of 680 s. The bake is not a line in that table.
- The bake duration is logged (`server.nim:439-441`) but the CI docker-smoke log only dumps
  container stdout on failure, so the run I cited carries no number. See §Could not determine.

**F17 — the player container's receive is an unbounded blocking read.**
- Where: `src/cogball_player.nim:70-95` — `socket.receiveMessage()` inside `while true`, with no
  deadline. It exits on exception or `isNone`.
- Observed: the loop terminates when the server closes the socket (`server.nim:762`
  `httpServer.close()`). If the game pod dies without closing, the player blocks until the
  platform's episode kill.
- Note says: §The player container — "otherwise only receives, until the socket closes." The
  checklist's degrade-never-hang clause names "LLM call, seat reply, round barrier"; this is none
  of those, and no server-side wait depends on it.

**F18 — a spectator speed command changes the live tick rate and the wall-clock check granularity.**
- Where: `src/cogball/server.nim:637-639` (`liveSpeedIndex.applySpeedCommand`) and
  `server.nim:639` (`for _ in 0 ..< playbackSpeed(liveSpeedIndex)`), against the once-per-outer-
  iteration wall-clock check at `server.nim:611-616`.
- Observed: a `/global` viewer can raise `liveSpeedIndex` to 5, so up to **16** sim ticks (and at
  most one turn boundary, since 16 < `turnTicks` 120) execute between two wall-clock checks. Still
  bounded; the overshoot is 16 ticks plus one turn budget.
- Note says: nothing. This is ctf's live transport path, kept.

### D. String truncation (note §Reply schema and per-field caps)

**F19 — `capRecord` can truncate a directive record into unparseable JSON.**
- Where: `src/cogball/directives.nim:50-64` (`clipRunes`), `directives.nim:158-161` (`capRecord`),
  `src/cogball/decide.nim:250-251` (`addRecord` → `capRecord`),
  `src/cogball/sim_types.nim:127` (`MaxDirectiveRecordRunes = 900`).
- Observed: `capRecord` clips the **whole serialized record** at 900 runes with
  `runeSubStr(0, 899) & "…"`. I measured the serialized shape (compact JSON, the exact key set
  `directiveJson` emits at `directives.nim:132-156`):
  - empty note and says: **467** runes
  - plain 160-rune note + three 48-rune says: **771** runes
  - a 160-rune note of `"` + three 48-rune says of `"` (each escaped to `\"`): **1075** runes
  So ~130 runes of escaping headroom. A quote- or backslash-heavy LLM `note`/`say` pushes the
  record past 900 and `clipRunes` cuts it mid-object, producing a chat record that is valid UTF-8
  (the cut is on a rune boundary, as required) but is **not valid JSON**.
- Consequence, traced: `broadcast.applyRecord` catches the parse failure and silently returns
  (`broadcast.nim:152-156`), so the feed loses the line; `replay_summary.py:183-187` `continue`s,
  so the phase-60 `select(.source=="llm")|length` under-counts. The sim, the mask log and the hash
  chain are unaffected (records are outside the determinism boundary).
- Note says: "the whole serialized directive record **≤ 900 runes** … the new cap is asserted in
  `test_replay.nim`". `tests/test_directives.nim:162` asserts
  `capRecord($record).runeLen <= MaxDirectiveRecordRunes` — true by construction — and
  `tests/test_replay.nim:125-128` asserts every chat record parses, but only for scripted
  baselines whose `note`/`say` are fixed short ASCII strings (`baselines.nim:82`, `101`).
- Inferred + measured offline in Python; not run against the Nim serializer.

**F20 — `register` and `result` records bypass `capRecord`.**
- Where: `src/cogball/server.nim:602-609` (register) and `server.nim:678`
  (`recordAndWrite(sim.resultRecordJson())`); `recordAndWrite` (`server.nim:470-476`) does not cap.
- Observed: only records produced through `engine.addRecord` are capped. `register` is bounded
  indirectly (`policy` is clipped to 48 runes at `server.nim:571`); `result` is bounded only by the
  length of the two real policy names.
- Note says: the ≤900 cap is stated for "the whole serialized **directive** record", so this is
  arguably correct behaviour — but `tests/test_replay.nim:125` asserts ≤900 for *every* chat
  record, an assertion that would fail on a real episode with long enough policy names.

All the other caps trace exactly: `note` 160 (`directives.nim:228`), `say` 48
(`directives.nim:252`), `policy` 48 (`server.nim:571`), `detail` 200 (`decide.nim:375`), `prompt`
4000 (`server.nim:569`), robot id 8 (`directives.nim:73`) — all through `clipRunes`, which uses
`runeLen`/`runeSubStr` and no byte slicing.

### E. The replay writer and the viewer

**F21 — `pitchRgba` is a dead field in the positionally-serialized keyframe layout.**
- Where: `src/cogball/sim_types.nim:390` (`pitchRgba*: seq[uint8]  ## baked turf, stripped from
  keyframes`), `src/cogball/replays.nim:139-142`.
- Observed: `grep -rn pitchRgba src/ replay-viewer/` returns **only** the declaration — nothing
  ever writes it. `serializeReplaySim` flattys the whole `SimServer` and its comment says "the
  board bake is process-wide (global.nim owns it), so unlike ctf there is nothing to strip". The
  field is therefore always an empty seq occupying a keyframe slot.
- Note says: nothing about `pitchRgba`. `AGENTS.md` §Layout warns that `SimServer` is serialized
  positionally — "append fields, never insert or reorder" — so the slot cannot be removed without
  invalidating keyframe layout.

**F22 — two details in `tools/replay_summary.py`.**
- Where: `tools/replay_summary.py:67-68` and `:135`.
- Observed (a): `Reader.text()` decodes with `errors="replace"`, so a byte-truncated string in the
  replay is silently repaired to U+FFFD instead of surfacing. The script's strict-UTF-8 output
  promise is therefore met by construction rather than by the replay bytes being clean. The real
  UTF-8 check on the replay lives on the Nim side (`tests/test_replay.nim:127`,
  `isValidUtf8(chat.message)`), which does test the bytes.
- Observed (b): `chain = 1469598103934665603` is annotated "FNV-1a offset basis, 64-bit". The FNV-1a
  64-bit offset basis is `14695981039346656037` (as used correctly at `sim_state.nim:78`); the
  literal here is one digit short. It is only a self-consistent digest seed for the `hashChain`
  field compared between two recordings, so the value is functionally arbitrary — the comment is
  what is wrong.

### F. The manifest

**F23 — `numAgents` (camelCase) is read but not declared in `config_schema`.**
- Where: `src/cogball/sim_config.nim:145-146` reads both `num_agents` and `numAgents`;
  `coworld_manifest_template.json` `game.config_schema.properties` declares only `num_agents` and
  is `additionalProperties: false`. `tests/test_manifest.nim:112` explicitly allow-lists
  `numAgents` out of its coverage check.
- Observed: nothing in the repo emits `numAgents`, so no config the platform can build will trip
  the certifier. The alias is unreachable through a validated config.

**F24 — `showPlayerLabels` is declared, defaulted, parsed, echoed and asserted — and never read.**
- Where: `src/cogball/sim_types.nim:343`, `sim_config.nim:33`/`:161`/`:240`,
  `tests/test_server.nim:121-122`. `src/cogball/global.nim:735` mentions it only in a docstring.
- Observed: `grep -rn showPlayerLabels src/ client/` finds no renderer that consults it. The
  two-name-space property holds by construction instead — every board label is built from
  `robotId()`/`seatAlias()` (`labels.nim`, `global.nim:747-748`), and no code path can put
  `player.address` on the board.
- Note says: "**real player names** … `showPlayerLabels` is forced false on the player stream."
  The outcome is what the note wants; the mechanism named in the note is inert.

### G. The tests (note §Tests)

All 12 suites the note lists exist and all 12 ran in CI run 32613856995 (I read the `nim r` lines
in the log; `test_perf.nim` release-only, everything else in both debug and `-d:release`).

**F25 — no test covers the never-connecting-seat path.**
- Where: the note's test 6 lists "a never-connecting seat is reported to
  `COGAME_PLAYER_FAILURE_URI` and the match still reaches `full_time`".
  `tests/test_engine.nim:278-288` (the run list) has no such case. The nearest is
  `tests/test_server.nim:194-210`, which asserts `sim.lobbyJoinTimedOut()` and then calls
  `sim.startGame()` **by hand**; it never exercises `declarePlayerFailure`
  (`server.nim:357-368`), never asserts the failure JSON shape, and never plays to `full_time`.
- `grep -rn declarePlayerFailure tests/` → no hits. `tests/test_startup.nim:108` only greps
  `server.nim` for the literal string `COGAME_PLAYER_FAILURE_URI`.

**F26 — the budget-guard test does not run the episode to `complete/full_time`.**
- Where: `tests/test_engine.nim:141-167`.
- Observed: it asserts the guard fires once, sticks, costs no network call, and writes one
  `budget_guard` record. It never advances the sim to game over.
- Note says: test 6 — "the budget guard switches to scripted **and the episode still ends
  `complete/full_time`**".

**F27 — the sim-fault test does not trip the physics guard, and asserts no partial replay.**
- Where: `tests/test_engine.nim:228-232` calls `faulted.finishGame(reasonFault, erSimFault)`
  directly. `physicsGuardTripped` (`sim.nim:579-591`) has no test caller (grep: only its
  definition and its one call site in `stepPlaying`).
- Note says: test 6 — "**a raised physics guard** yields `fault/sim_fault` with 0.5/0.5 scores
  **and a partial replay**". The scores half is asserted; the trigger and the partial replay are
  not.

**F28 — two `test_physics` tolerances are looser than the note's wording.**
- Where: `tests/test_physics.nim:50-53` — wall restitution asserted within `expected div 8`
  (±12.5 %); the note says "within the fixed-point quantum".
  `tests/test_physics.nim:109-117` — the kick asserts `ball.vx > KickImpulse * 9 div 10` and the
  reaction within `expectedReaction div 3` (±33 %); the note says the kick "sets the along-heading
  ball speed to **exactly** `max(vpar,0) + 375000`".
- Both tests fold in one substep of drag before the measurement (the code comments say so), which
  is why exactness is not asserted; the golden-hash fixture (`test_determinism.nim:85-123`) is what
  actually pins the numbers bit-for-bit.

**F29 — test_replay checks "at least one kick, one shot" from sim stats, not the stream.**
- Where: `tests/test_replay.nim:144-148` reads `recorded.sim.stats[…].kicks/shots`.
- Note says: test 7 — "the **record stream** contains at least one `kick`, one `shot`, one
  `directive` per seat per turn, and exactly one `result` record." The directive-per-seat-per-turn
  (`:141-143`, `>= 9` for a 10-turn match) and the single `result` (`:140`) *are* checked against
  the stream; `kick`/`shot` are broadcast-derived events, not chat records, so there is nothing in
  the stream to count.

**F30 — test_server exercises several contract clauses by re-implementation or by grepping source.**
- Where: `tests/test_server.nim:36-51` re-implements the registration predicate inline rather than
  calling `parseRegistration` (which is not exported from `server.nim:370-377`);
  `test_server.nim:179-192` asserts routes by `readFile("src/cogball/server.nim").contains(...)`;
  `test_server.nim:139-158` writes `results.json` with `writeFile` rather than through
  `runtimeConfig.writeResults`.
- Note says: test 8 — "registration chat accepted and **not** echoed into the replay chat stream";
  "`/client/global`, `/client/player`, `/client/replay`"; "artifact writes to `file://` URIs".
  I found **no** assertion anywhere that a registration chat is not echoed into the replay chat
  stream, and the three `/client/*` routes are not among the greps at `:186-187` (only
  `/healthz`, `/replay-data`, `/client/font.ttf`, `/client/league`). The module docstring
  (`test_server.nim:6-10`) says the suite "exercises the pure pieces directly" and starts no
  process, which is consistent with what it does.
- The two-name-space half of test 8 (`test_server.nim:82-137`) *is* asserted properly and
  end-to-end on real packets — see §Traced and consistent.

### H. The scripted baselines (note §Scripted baselines)

**F31 — two tuned constants differ from the note's numbers.**
- Where: `src/cogball/baselines.nim:18` `KeeperArc = 2_000_000` (2 m) and `baselines.nim:23`
  `StrikerRange = 9_000_000` (9 m).
- Note says: keeper target `(xOwnGoal + **3 m**·attackDir, …)`; striker "intent `shoot` if the ball
  is in the opponent half or **within 6 m**".
- Context for checklist item 7 ("tuned with a grid harness, not guessed"): both constants are
  `{.intdefine.}` (`baselines.nim:17-31`) precisely so a sweep can drive them from the command
  line, and the doc comments record results ("2 m beats 3 m and 4 m against `swarm` over 48
  matches (both sides played)"; "9 m beats 6 m"). **No grid-harness script is committed** — I
  searched `tools/`, `tests/` and the workflows and found none. The evidence for the sweep is the
  comments plus the `{.intdefine.}` mechanism.

**F32 — the `back` target y is `ball.y ± 1.5 m`, not the midpoint pulled to the far side.**
- Where: `src/cogball/baselines.nim:122-129`: `midX = (ball.x + ownGoalX) div 2` (the midpoint, as
  the note says) but `targetY = clamp(ball.y + side, …)`.
- Note says: "target = **midpoint of ball and own goal**, pulled 1.5 m to the far y-side". The x
  is the midpoint; the y is the ball's, offset.

**F33 — `swarm`'s role labels are not fixed striker/striker/back.**
- Where: `src/cogball/baselines.nim:156-172`. The deepest robot reports `roleBack` **only while
  `guard`** (the ball is in its own half); otherwise all three report `roleStriker`.
- Note says: "Roles reported as `striker`/`striker`/`back`." The intents match the note exactly.

**F34 — `third` is computed and discarded.**
- Where: `src/cogball/baselines.nim:87-91` computes `third`, `baselines.nim:142` `discard third`.
  The branch that would use it (`else:` at `:118`) reaches the same robot by elimination.

### I. The control layer

**F35 — for `hold`/`press` the kick aim is the pitch centre.**
- Where: `src/cogball/control.nim:219-228`: when the intent is `inHold` or `inPress` and no boards
  override fired, `aimX, aimY = CentreX, CentreY`.
- Note says: step 5 — the aim target is "opponent goal for `shoot`, `T` for `pass`, `C` for
  `clear`, `E` for the boards override, **the ball-away-from-own-goal direction otherwise**". For
  `chase`/`intercept` the code does use `targetGoalX(seat)` (`control.nim:232-235`); for
  `hold`/`press` it uses the centre spot instead, which is a different direction whenever the
  robot is not on the halfway line.
- The `hold`/`press` gate itself ("never kick unless the ball is between the robot and its own
  goal") is implemented exactly, at `control.nim:222-226`.

### J. Viewer legibility and the scaffold

**F36 — the `.tiny` toggle is at `boardW <= 620`, not 640.**
- Where: `client/replay_broadcast.html:2723` — `stage.classList.toggle('tiny', boardW <= 620);`,
  with the CSS comment at `:158` and `:1443` naming "the 640×360 floor".
- Checklist item 11 says "labels hidden under **640px**". The design note says the starter
  "toggles `#stage.tiny` at `boardW ≤ 620`, with the CSS comment naming 'the 640×360 floor'. Kept
  verbatim." So the note and the code agree; the checklist's number and the code's differ by 20 px.
  The `.plate-name` rule the checklist names verbatim **is** present:
  `client/replay_broadcast.html:152` — `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow:
  hidden;` — and `tests/test_viewer.nim:44-47` asserts both it and
  `#stage.tiny .plate .stat { display: none; }` (`:160`).

**F37 — `/client/replay` survives in two files that ship in the bundle.**
- Where: `client/broadcast_core.js:196` (`['/client/replay', '/replay'],` — the route→ws mapping
  table) and `client/league_replayer.html:446` (`src = ROUTE_BASE + '/client/replay?embed=1';`)
  and `:882`. `Dockerfile.replay-viewer:35` copies `broadcast_core.js` into the bundle and `:44-46`
  renders `league_replayer.html` into `league.html` inside the bundle.
- Observed: both strings are inherited verbatim from the starter — the same lines exist at
  `/workspace/starters/coworld-ctf/client/broadcast_core.js:196` and
  `coworld-ctf/client/league_replayer.html:447,886`. The **static viewer entry point is clean**:
  cogball's `client/replay_broadcast.html` (which becomes `index.html`) contains no `/client/replay`
  string, `Dockerfile.replay-viewer:39` splices `static_replay.js` into the `BROADCAST_CORE` slot,
  and `Dockerfile.replay-viewer:67` asserts `! grep -q '<script src="./broadcast_core.js">'` in
  index.html. The only network call in the static path is
  `replay-viewer/static_replay_worker.js:113` `fetch(message.replayUrl, …)`, whose URL comes from
  the page's `?replay=` query parameter (`static_replay.js:162`) — i.e. the S3 object.
- Checklist item 3 says "No `/client/replay` pod path anywhere". The strings are present; the
  bundle's `index.html` does not use them; `league.html` does. `game.replay_viewer` is
  `{"bundle": "static-replay-viewer"}` and `coworld-release.yml:190-200` hard-fails certification
  unless the certifier reports the STATIC bundle.

**F38 — the superseded round-1 design note carries no superseded marker.**
- Where: `docs/plans/2026-08-22-cogball-design.md:1-13`. Its opening still reads as the live note
  ("forked from **`Metta-AI/cogame-moba`**"). `grep -in "supersed|obsolete|historical"` on the file
  returns nothing. Commit `433da18`'s message says the note "stays in `docs/plans/` as the record
  of what it was", but the file itself does not say so; `docs/plans/2026-08-22-cogball-design-v2.md`
  is the accepted one.

---

## Traced and consistent

**Resolution order** — `src/cogball/sim.nim:630-721` executes the note's ten steps in order:
turn boundary (`server.nim:642-654`, before the tick it governs) → kickoff freeze
(`sim.nim:631-641`, `step` also passes `ZeroInputs` at `sim.nim:713-717`) → control compile
(`server.nim:656`) → record (`server.nim:657`, `writeInputFrameMasks`) → kicks
(`sim.nim:643`, `applyKicks`, robot index order, each kick seeing the previous kick's ball state)
→ four substeps in the exact internal order 1-8 (`sim.nim:593-607`: robots, ball, robot-wall,
robot-robot, robot-ball, ball-post, ball-wall, goal test; the goal test `return`s, abandoning the
remaining substeps) → cooldowns (`sim.nim:646-648`) → possession + stalemate (`sim.nim:650-664`) →
hash (`server.nim:663`, `writeHash(uint32(sim.tickCount), sim.gameHash())`, once per tick) → turn
end (`sim.nim:679-688`, `(elapsed+1) mod turnTicks == 0`, mercy at `|gd| >= mercyGoalDiff` on the
boundary, `full_time` at `elapsed+1 >= maxTicks`).

**Physics constants** — every number in the note's step 6 matches `sim_types.nim:59-90`:
`SpinAccel 6`, `SpinDampNum 64`, `SpinMax 96`, `ThrustAccel 7800`, `GripNum 85`,
`GripBrakeNum 255` (= 85 × 3, the note's "grip ×3"), `RobotDragNum 13`, `BallDragNum 6`,
`Substeps 4`, restitutions 25/35/55/70/80 %, `DribbleTangentPct 80`, `BallWallTangentPct 98`,
`RobotMaxSpeed 291 600`, `BallMaxSpeed 1 041 600`, `KickImpulse 375 000`, `KickCooldownTicks 12`,
`KickRange 1 350 000` (= 550 000 + 350 000 + 450 000), `KickoffFreezeTicks 25`,
`AssistWindowTicks`/`PassWindowTicks` 96, `DefaultStalemateTicks 240`, `DropClearRadius 3 000 000`.
The kick model at `sim.nim:290-308` is the note's formula term for term, including the exact
integer arc test `2·dot >= d·4096` and the `BallMassG/RobotMassG` reaction.

**Kickoff reset** — `sim.nim:145-178` places all seven bodies exactly as the note's paragraph
describes (restarting seat's slot-0 at 1.5 m on its own side, the other seat's at 3.0 m on the far
side, flanks at ±9 m and y = 12.5 ± 4.5 m with `rng.rand(500_000) − 250_000` jitter, Azure
headingQ 0 / Crimson 2048 = brad 128, all velocities/spins/cooldowns 0, `Kickoff` emitted with the
restarting seat). `tests/test_physics.nim:197-232` asserts every one of these coordinates and pins
the jitter to the seed.

**Neutral drop** — `sim.nim:180-203` teleports the ball to `nearestDropSpot` with zero velocity,
pushes every robot inside 3 m out to exactly `DropClearRadius`, resets the counter and emits
`Drop`; all of it inside the hashed step. `pitch.nim:23-28` places the four spots at the note's
coordinates. `tests/test_physics.nim:234-265` asserts the exact firing tick and the cleared radius.

**Scoring** — `roster.nim:120-134`: `500 + clamp(roundDiv(gd*500, 3), ±500)` permille, with
`roundDiv` symmetric under negation. I checked every outcome by hand: 3-0 → 1000/0, 2-0 → 833/167,
2-1 → 667/333, draw → 500/500, fault → 500/500, `win = gd > 0` and false on fault.
`tests/test_engine.nim:235-252` sweeps 0-6 × 0-6 and asserts the pair sums to 1000 exactly.

**One parallel batch** — `decide.nim:326-329` collects both seats into one `calls` seq;
`decide.nim:342` issues them in a single `engine.batch(...)`; `decide.nim:214-223` maps that onto
one `client.curl.makeRequests(batch, …)`. The retry (`decide.nim:377-380`) rebuilds one batch.
`tests/test_engine.nim:45-66` records each call's in-flight window and asserts they intersect,
which a sequential implementation would fail.

**Credential ladder** — `llm.nim:99-127`: Bedrock (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME` or
`AWS_BEARER_TOKEN_BEDROCK`, region from `AWS_REGION`/`AWS_DEFAULT_REGION` default `us-west-2`) →
`ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` via `readCogameUri` (`llm.nim:57-68`) → `disabled`.
Model candidates and `tryNextBedrockModel` on "Model access is denied" / 429 at `llm.nim:70-93`,
`157-168`. `max_tokens` from `maxOutputTokens` (default 900, `sim_types.nim:120`), no
`temperature`, `anthropic_version: bedrock-2023-05-31` on the Bedrock body.
`extractJsonObject` (`llm.nim:184-196`) is first-`{`-to-last-`}`, fence- and prose-tolerant.

**Tolerant parse and repair table** — `directives.nim:214-290` implements every row of the note's
table: unknown role → `wing` (`:104`), unknown intent → `chase` (`:114`), unknown kick → `auto`
(`:117`), non-finite/missing target → the robot's current position (`:266-271`), out-of-pitch
target clamped (`:37-40`), `pass_to` not a distinct teammate → null and `pass` degrades to `shoot`
(`:274-278`, `control.nim:99-103`), extra entries dropped (`:241-242`), unmatched ids assigned by
position (`:236-243`), missing robots filled from last turn then from `formation` (`:282-289`),
`usable` false only when no robot entry was recovered (`:281-290`). `robots` accepted as an
id-keyed object (`:195-212`) and numeric strings accepted for `target` (`:183-191`).
`tests/test_directives.nim` covers all of these plus the emoji-on-the-boundary case.

**Fallback wiring** — `decide.nim:264-272` (`formation` is the fallback directive),
`:383-388` (two failures → `formation`), `:389-404` (both seats always settled, `hasDirective`
always set, `llmTurns`/`fallbackTurns` incremented, one directive record per seat per turn). The
`hasDirective` guarantee is what keeps the server's `opening` condition
(`server.nim:649-650`) from re-firing a turn on every tick.

**Budget guard** — `decide.nim:291-301`: `elapsedSeconds + 2 * ceil(turnBudgetMs/1000) > budget`
→ `llmOff` for the rest of the match plus one `budget_guard` record carrying the turn and the
remaining seconds. Matches the note's formula exactly.

**Turn cadence** — I traced the arithmetic: `startGame` runs inside `sim.step`'s Lobby branch and
`tickCount` increments after it, so the first Playing iteration sees `elapsedTicks == 1`; the
`opening` clause fires turn 0 there, then `elapsedTicks mod 120 == 0` fires turns 1…39 at
elapsed 120…4680. Exactly **40** turns for `maxTicks = 4800`. The code comment at
`server.nim:645-648` states this reasoning.

**Wall-clock stop** — `server.nim:611-616`, at the top of every loop iteration, `phase == Playing`
only, `sim.wallClockStop()` → `finishGame(reasonDeadline, erWallClock)` (`sim.nim:723-727`), which
is idempotent (`sim.nim:212-213`), so a stop landing on the same tick as full time cannot overwrite
the verdict.

**Lobby bound** — `sim_state.nim:28-34` counts LOBBY ticks only; `sim.step`'s Lobby branch
increments `lobbyWaitTimer` whenever `players.len < minPlayers` (`sim.nim:701-704`);
`server.nim:621-630` declares the failure for the lowest missing slot and calls `startGame()`
without ending the episode. `runFrameLimiter` (`server.nim:335-355`) paces at 24 Hz when no player
is ready (`allPlayersReady` returns false on `active == 0`, `:333`), so 2400 lobby ticks ≈ 100 s.

**Game-over hold** — `finishGame` sets `gameOverTimer = config.gameOverTicks` (120 = 5 s);
`sim.step`'s GameOver branch decrements it (`sim.nim:718-720`); the loop breaks at
`server.nim:673` and the artifact block runs at `:747-764`, writing the `result` record *last* so
its `finalTick` equals the one in `results.json`.

**Replay writer format** — `replays.nim:86-97`: magic `COWLDBAL`, format version 1, `gameName`
`cogball`, `gameVersion` `1`, `joinKind: rjkNameSlotToken`, `allowChat`, `hashOrder: rhoStop`.
Config JSON echo at `sim_config.nim:210-258` carries seed, num_agents, every tuning field and the
pitch geometry. Joins at `server.nim:532-533`, per-robot input-mask changes at
`replays.nim:107-131` (the `player` byte is a **robot** index 0..5 — named edit 1, asserted at
`tests/test_replay.nim:87-89`), chat records for directive/fallback/register/result, one
`writeHash` per tick. Edit 2 (a leave does not shift the mask arrays) at `replays.nim:228-234` +
`roster.nim:94-101`.

**Replay re-derivation** — `replays.nim:301-306` (`stepReplay`: apply events → build inputs from
the recorded masks → `sim.step` → `checkReplayHash`) and `:268-299` (`checkReplayHash` compares
`sim.gameHash()` against the recorded hash **every tick** and records `hashMismatchTick`).
`tests/test_replay.nim:99-116` replays a real recorded episode with `mismatchQuit = true`, asserts
`hashMismatchTick == -1` over >1000 ticks and that the goal counts match the recording.
`tests/test_determinism.nim:16-40` replays the same mask log three times (twice in-process, once in
a fresh sim) over a full 4800-tick match. Checklist item 2 is satisfied, and the viewer derives
from the same re-derivation: `replay-viewer/cogball_replay.nim:8` imports `cogball/sim` directly
and `:91-95` calls `advanceReplayFrame` → `stepReplay`, with no parallel recording anywhere.

**Cross-build gate** — `.github/workflows/ci.yml:154-174` records the fixture with the **native**
build of the same commit and gates it with `tools/ci/check_fixture.py` (which asserts
`results.reason == "complete"`, ≥1000 ticks, ≥18 directives, both seats registered);
`:168-174` uploads it; `:232-236` the `wasm-viewer` job downloads it; `:285-291` runs
`node tools/wasm_replay_smoke.cjs "$PWD/dist/static-replay-viewer" … 300`, which fails on
`_cogball_mismatch_tick() !== -1` before and after 300 frames
(`tools/wasm_replay_smoke.cjs:89-106`) and has a 120 s watchdog (`:29-32`). CI log line:
`ok: loaded cogball-679961.bitreplay, advanced 300 frames (10054058 packet bytes, heap 34 MB)`.

**Bundle contents** — `Dockerfile.replay-viewer:31-73` emits `index.html`, `league.html`,
`static_replay.js`, `static_replay_worker.js`, `chrome_common.js`, `broadcast_core.js`,
`wire_constants.js`, `cogball_replay.js/.wasm/.data`, `font.ttf` and the wall/lockerroom art, then
asserts each with `test -f`/`grep -q`. The rig sheets ride in `cogball_replay.data` via
`--preload-file {rootDir}/data@data` (`replay-viewer/config.nims`). Emscripten flags
`ABORTING_MALLOC=1`, `ALLOW_MEMORY_GROWTH`, `ENVIRONMENT=web,worker,node`, `--cpu:wasm32` all
present and asserted at `tests/test_viewer.nim:192-195`.

**Manifest** — `num_agents: 2` in variant `default`, variant `sprint` and
`certification.game_config`; `certification.players` len 2; `certification.game_config.players`
len 2 (all read directly out of the JSON). `replay_viewer` is `{"bundle":
"static-replay-viewer"}`. `game.protocols` carries both `player` and `global`. `game.docs.readme`
is `{"type":"text","value":…}` (5472 chars) and `pages` is exactly three entries
`rules.md`/`protocol.md`/`coaching.md`, each `{"id","title","content":{"type":"text","value"}}`
(9291/6902/6698 chars); `tests/test_manifest.nim:152-158` asserts the inlined text equals the
current files byte for byte. `results_schema` declares exactly the 15 keys `playerResultsJson`
writes, in the same set, `additionalProperties: false`, `required` = the note's 7, `reason` and
`endRule` enums complete, every array `minItems/maxItems: 2` — I diffed both key lists by hand.
`config_schema` declares 27 properties covering every key `sim_config.update` reads except the
`numAgents` alias (F23).

**Seat-count invariants** — `tools/ci/docker_smoke.sh:102-143` enforces all four:
`num_agents` present (`:104-110`), a positive non-bool integer (`:111-117`),
`len(certification.players) == num_agents` (`:121-126`),
`len(certification.game_config.players) == num_agents` (`:127-132`), plus the independent
`SMOKE_SEATS` cross-check (`:138-143`, default 2 at `:47`). Every one exits with a message
prefixed `SEAT-COUNT FAIL:`. The smoke ran with `SMOKE_REQUIRE_REPLAY_JSON: "0"`
(`ci.yml:211-214`) and logged `smoke OK: seats=2 results=300B replay=48192B reason=complete`.

**Two name spaces** — `sim_types.nim:448-462` is the only source of `Azure`/`Crimson` and
`AZ-1`..`CR-3`; `decide.nim:83-188` builds the seat view from those alone (no `address`, no seed);
`labels.nim` is the whole board vocabulary and carries no name. Real names appear only in
`configJson` `players[].name` (`sim_config.nim:220`), the join records (`server.nim:532`),
`rosterJson`/`teamPoliciesJson` (`broadcast.nim:207-250`) and `results.names`
(`roster.nim:136-145`). `tests/test_server.nim:82-137` asserts the composed LLM user message and
every board-label string in a real player packet contain no `player.address`, and that the chrome
roster and `results.names` do.

**Integer-determinism discipline** — every stored body/stat field in `sim_types.nim:214-258` is an
explicit `int32` (`distanceUm` is `int64` and unhashed). Every product in `sim.nim`, `trig.nim`
and `control.nim` is taken in `int64` and narrowed with an explicit `div` — I read every
arithmetic line in `sim.nim:35-607` and `control.nim:33-241` and found no exception.
`SinQ12` is a committed 256-entry literal table (`trig.nim:23-47`); `isqrt` is Newton with an
exact fix-up loop (`trig.nim:57-81`); `bradsOfVectorI` is a 5-step binary search on the exact
cross-product comparison with the fold applied before the search (`trig.nim:87-139`).
`tests/test_determinism.nim:141-162` strips comments and string literals (`helpers.nim:104-147`,
including the `1'i64` numeric-suffix case) and greps 21 banned identifiers plus `std/math` across
all seven guarded modules, and greps four build scripts for `-ffast-math`.
`test_determinism.nim:164-209` re-derives all 256 table entries from `math.sin`, checks `isqrt`
exhaustively below 2¹⁶ and on perfect squares to 2⁴⁰, and checks `bradsOfVectorI` against
`arctan2` to ±1 brad over 100 000 vectors plus exact antisymmetry. All passed in CI in both debug
and release. Note that `directives.nim` *does* use floats (`viewX`, `round2`, `worldXOfView`) —
correctly, since it is outside the guarded set and its output reaches the sim only through a
directive, which is outside the determinism boundary.

**Hash contents** — `sim_state.nim:74-135` mixes tick, phase, verdict, score, every body's
position/velocity/heading/spin/cooldown, plus the stats, touch/shot/pass bookkeeping and the
roster length/join order. It mixes **no** directive, note, FX, trail, paint or feed field;
`test_determinism.nim:211-227` mutates all of those and asserts the hash does not move.

**Scaffold** — three workflows present. `coworld-release.yml` step order is
build manifest (`:153`) → certify (`:167`) → **upload-policies** (`:206`) → upload-coworld
(`:304`) → secret put (`:342`). `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are
both mode **100755** (`git ls-files -s`) and both are invoked **by path**, not through `bash`
(`ci.yml:214`, `:260`), with an explicit `test -x` assertion before each (`:191-199`, `:246-257`).
`tools/ci/policies.json` has four entries, all `"run": "/bin/cogball-player"`: two `PLAYER_PROMPT`
champions (`cogball-total`, `cogball-counter`) and two `PLAYER_SCRIPTED` fillers, with champion #2
carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at `policies.json:17`. The
checklist's placeholder gate exits **0** — I ran it verbatim. The only surviving angle-bracket
names are exactly the four documented as expected residue: `<cow_id>`/`<sha>` at `ci.yml:218`,
`<run_id>` at `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` at
`coworld-submit.yml:31`.

**CI green, no test loosened** — run 32613856995 `success` on the reviewed sha. `git log
--name-status -- tests/` shows four commits: `59f2100` added the round-1 Python suite,
`67ab6d3` modified `tests/viewer_core_harness.js`, `433da18` **deleted the entire round-1
Python/C tree wholesale** (39 files, 9395 deletions — the server, the C sim, the JSON replay, the
JS viewer harness and all 13 Python tests), and `51cd7ec` added the 12 Nim suites plus
`tests/lib/helpers.nim`, `tests/data/golden_hashes.json` and the fixture. `433da18`'s message
records the reason: the operator ruled cogball takes coworld-ctf, not cogame-moba, and the round-1
tree was removed "so the paintbot-lineage implementation that follows is not read as a patch on
top of it". No `skip`/`xfail`/`when false` appears anywhere in the current `tests/*.nim`
(I grepped). I record the wholesale deletion as a fact for the judge: it is a lineage change, not
a test weakened to make a run green, and no assertion in the current tree was widened after being
written.

## Could not determine

- **How long the board bake takes** (F16). `sim.warmBoardRenderCaches()` runs before the 690 s
  clock starts and logs its duration at `server.nim:439-441`, but the docker-smoke step only dumps
  container stdout on failure, so run 32613856995 carries no number. The whole 1200-tick smoke
  episode took ~18 s wall clock (`02:51:50.13` container start → `02:52:08.70` smoke OK), which
  upper-bounds the bake at well under 18 s — but that is an inference from the surrounding
  timestamps, not a measurement. *What would settle it:* an `echo` of the "board render caches
  baked in N ms" line in a CI log, e.g. by having docker_smoke.sh dump the game log on success too.
- **Whether the grid harness behind the baseline constants exists** (F31). The `{.intdefine.}`
  mechanism and the recorded sweep results are in `baselines.nim:17-31`, but no harness script is
  committed to `tools/`, `tests/` or the workflows. *What would settle it:* a committed sweep
  script, or a link/log from the run that produced "2 m beats 3 m and 4 m … over 48 matches".
- **Whether F19's >900-rune directive record is reachable in practice.** I measured the serialized
  length in Python against the exact key set `directiveJson` emits, not against Nim's `$JsonNode`.
  It needs an LLM reply whose `note` + three `say`s together carry ~130 characters that JSON-escape
  (`"` or `\`). *What would settle it:* a Nim test that feeds a quote-saturated note and says
  through `parseDirective` → `directiveJson` → `capRecord` and asserts the result still
  `parseJson`es.
- **The end-to-end websocket contract.** No test starts the server process (`test_server.nim:6-10`
  says so explicitly), so the registration-not-echoed property, the HTTP 403 response, the
  `/client/*` route responses and the `file://` artifact writes are asserted by proxy (F30). The
  docker smoke does exercise the real binary end to end and asserts `results.json` and a replay
  exist, which covers the artifact path in practice. *What would settle the rest:* a test that
  launches `/bin/cogball` and drives a websocket, or an assertion in the docker smoke that the
  written replay's chat stream contains a `register` record and no raw registration text.
