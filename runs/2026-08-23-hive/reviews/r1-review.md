# r1 review — hive

Repo: `Metta-AI/cogame-hive` at `48465f363ff1c09079d57fc40da717bd2f37e594` (clean checkout at
`/workspace/scratch/cogame-hive-repo`; history is two commits, the second adds the whole game).
Design note: `/workspace/coworld-builder/runs/2026-08-23-hive/design.md` (1337 lines, read in full).
Starters diffed: `/workspace/starters/coworld-ctf`, `/workspace/starters/cogame-bullwhip`,
`/workspace/coworld-builder/templates/{ci.yml,coworld-release.yml,coworld-submit.yml,tools/ci/*}`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (read first, items 1–13).

Files read: 62 (all of `src/hive*`, `replay-viewer/*`, `client/{broadcast_core.js,replay_broadcast.html}`
CSS/attach paths, all 16 `tests/*.nim` + `tests/support/helpers.nim` + both fixtures, all three
workflows, `tools/{build_replay_viewer.sh,wasm_replay_smoke.cjs,record_fixtures.nim,ci/*}`,
`Dockerfile.replay-viewer`, `coworld_manifest_template.json`, `data/meadow.fieldspec.json`,
`compose.yaml`, `config.json`, `docs/RULES.md` §Resolution order, `AGENTS.md`).

Findings are numbered F1…F30 and tagged **factual divergence** (code does X, note says Y),
**risk** (code is internally consistent but a named failure mode is not covered), or **note**
(observation, no divergence). Where a finding touches a checklist item I name it; categorisation
against the checklist is in §Blocking / §Non-blocking. Everything labelled *observed* was read in
the file at the cited line; *inferred* means I reasoned from the code without executing it;
*untested* means only a run would settle it.

---

## Blocking

### B1 / F1 — `ci.yml`'s `wasm-viewer` job neither `needs: docker-smoke` nor loads the bundle in a browser; `tools/ci/viewer_smoke.mjs` is absent
- Where: `.github/workflows/ci.yml:190-254` (whole job), `:152-181` (docker-smoke ends at the smoke
  run), `tools/ci/docker_smoke.sh:294` (file ends); template comparison
  `/workspace/coworld-builder/templates/ci.yml:207-320`, `templates/tools/ci/docker_smoke.sh` tail.
- Observed, step by step:
  - The repo's `wasm-viewer` job (`ci.yml:190-193`) declares `runs-on`/`timeout-minutes` and goes
    straight to `steps:`. The template's `needs: docker-smoke` line
    (`templates/ci.yml:212`) is deleted, together with its comment.
  - The template's steps `Assert the viewer load test is present`, `Download the smoke replay`,
    `setup-node`, `Install Playwright (pinned 1.55.0)`, `Load the bundle in a real browser`
    (`templates/ci.yml:238-303`) and `Upload the viewer smoke evidence` are all absent. In their
    place the repo has `Node smoke the emitted wasm module` (`ci.yml:241-247`) running
    `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer tests/fixtures/sample_replay.json`.
  - `tools/ci/viewer_smoke.mjs` does not exist in the tree (`find` over the repo; the only viewer
    harness is `tools/wasm_replay_smoke.cjs`).
  - The producer side is removed too: `docker-smoke`'s `Upload the smoke replay` step
    (`templates/ci.yml:187-198`) is gone, and `tools/ci/docker_smoke.sh` has had its
    `SMOKE_REPLAY_OUT` variable (`templates/…:34-40,58`) and its replay-preservation tail
    (`templates/…:303-315`, `mkdir -p`/`cp` into `dist/smoke/replay.json`) deleted. So even if the
    browser step were restored it would have no artifact to download.
  - CI evidence at the reviewed sha: run **32621277603**, `head_sha 48465f36…`, branch `main`,
    conclusion `success`, jobs `wasm-viewer` ✓ 1m27s, `docker-smoke` ✓ 1m15s, `test` ✓ 3m02s
    (`gh run view 32621277603 -R Metta-AI/cogame-hive`). The `wasm-viewer` log's last functional
    line is `wasm replay smoke OK: 960 ticks, 961 frames, packet 113204B, no digest mismatch`
    — node, not chromium; there is no `loaded: true`, no screenshot artifact, no `viewer-smoke.json`.
- Checklist item: 13, first bullet — "`ci.yml`'s `wasm-viewer` job is green on `main` at the
  reviewed sha **including its `Load the bundle in a real browser` step** (`tools/ci/viewer_smoke.mjs`,
  headless chromium, loading the replay `docker-smoke` produced)… a job green because the smoke step
  is absent… is a blocking finding, and so is a `wasm-viewer` that does not `needs: docker-smoke`."
- Why blocking: the one gate that executes the assembled page (index.html + spliced scripts +
  `HiveChrome.attach` + art fetch + `data-replay-loaded`) is not run anywhere. The node smoke
  exercises the wasm module's C ABI and the packet decoder only; it never parses `index.html`,
  never calls `HiveChrome.attach`, never sets or reads the DOM markers. This is exactly the
  lantern-shaped hole the checklist names, even though the specific lantern defect (MODULARIZE vs
  bootstrap) is *not* present here — see T7.

### B2 / F2 — `data-replay-loaded` is set by the chrome page, as `'1'`, before the first frame is drawn; the shell sets only `data-replay-error`
- Where: `client/replay_broadcast.html:2282` (`document.documentElement.setAttribute('data-replay-loaded', '1');`),
  set inside `HiveChrome.attach`'s `board.loadArt().then(...)` at `:2275-2288`, immediately before
  `relayout(); seek(0);` (`:2283-2284`); `seek()` is what first paints (`:2140-2153`,
  `board.ingest(api.packet(), nests)` → `HiveBoard.draw`, `client/broadcast_core.js:324-329`).
  `replay-viewer/static_replay.js:44` sets `data-replay-error`; `:147,:173` remove it; the shell
  never sets `data-replay-loaded` (grep over the tree returns only the page, the test and the design).
- Observed: the marker's value is `'1'`, not `"true"`; it is set from `replay_broadcast.html`'s
  inline script (which becomes `index.html` in the bundle, `Dockerfile.replay-viewer:40-43`), not
  from `static_replay.js`; and it is set one statement *before* the first `seek(0)`/draw rather than
  after it. `tests/test_viewer.nim:98-99` accepts the marker in either file
  (`"data-replay-loaded" in page or … in shell`).
- Checklist item: 13, second bullet — "`index.html` / `static_replay*.js` set
  `data-replay-loaded="true"` on `<html>` on the **first drawn frame**… Both markers, both set from
  the shell's own code paths."
- Why blocking (for the judge to weigh): the marker is present and on `<html>`, but (a) its value is
  `1` rather than `true`, so a strict `[data-replay-loaded="true"]` probe would not match, and
  (b) it is set before the first paint, so it cannot distinguish "attached" from "drew a picture".
  Note the value question is only decidable against whatever the (absent) `viewer_smoke.mjs`
  asserts — see §Could not determine.

### B3 / F3 — recall does not put ants on the carrying kernel
- Where: `src/hive/sim.nim:366-372` and `:437-444`; `src/hive/ants.nim:68-104` (`moveAnt` reads
  `let carrying = ant.carrying` at `:82` and branches on it at `:99`); design §Resolution order
  step 4 (design.md:270-273) and `docs/RULES.md:127-129`.
- Observed, traced: in `runAnts`, `let recalled = doctrine.recall` (`sim.nim:367`); if `recalled and
  inOwnPad` the ant is marked `held` and `continue`d (`:368-370`). Otherwise, for a recalled ant:
  step 5 is skipped (`if not recalled:` at `:375`), pickup at `:389-409` still runs, delivery at
  `:413` still runs, and step 8 calls
  `moveAnt(sim.antState[g], sim.meadow, sim.planes, sim.sources.foodNear, colony, kernel,
  coefficient, sim.rng)` (`:442-443`) — **no recall flag is passed**. `moveAnt` therefore selects
  `searchScore` for any ant whose `carrying` flag is false (`ants.nim:99-104`).
- What the note says: "uses the **carrying** kernel in step 8 regardless of its carrying flag"
  (design.md:271-272); `docs/RULES.md:127` repeats it ("walk home on the carrying kernel").
- Consequence (inferred, untested): a recalled empty ant outside its pad runs the searching kernel,
  which subtracts `alphaHome * H_own` — i.e. it is *repelled* by the home trail it would need to
  follow home — and lays nothing (step 5 skipped), so it reaches the pad only by chance. `recall`
  is documented in the system prompt (`src/hive/llm.nim:57`) and both champion prompts as "every ant
  drops its road and walks home, then waits"; the implemented behaviour is closer to "stops
  depositing and wanders". `sim.nim:245-254` still emits a `recall` event counting ants not yet held.
- Checklist item: 6? no. This is a rules-vs-note divergence, i.e. checklist **correctness** category
  if the judge treats the note's resolution order as the contract; it falsifies no numbered item
  verbatim. Listed here because `AGENTS.md` calls the resolution order "the contract" and
  `docs/RULES.md` ships the wrong behaviour to players. I flag it for the judge rather than
  asserting it is blocking.

---

## Non-blocking

### Resolution order and rules

**F4 — the per-seat view is built before the turn clock rolls, so `view.turn` lags one turn and
`delivered_last_turn` is two turns stale.** *(factual divergence)*
- Where: `src/hive/rules.nim:116-117` (`if match.tick mod turnTicks == 0:
  match.installDoctrines(provide(match, match.tick div match.config.turnTicks))` — `provide` is
  evaluated *first*); `src/hive/sim.nim:213` (`sim.turn = sim.tick div sim.config.turnTicks`, only
  set inside `installDoctrines`); `:215-217` (the `deliveredLastTurn` roll, also inside);
  `src/hive/broadcast.nim:119` (`"turn": match.turn`) and `:137`
  (`"delivered_last_turn": match.deliveredLastTurn[colony]`).
- Traced: at `t = 240` the provider runs with `match.turn` still `0`, so the view handed to the LLM
  and to `turnFrame` (`broadcast.nim:160-168`) reads `"turn": 0, "tick": 240`. The design's worked
  view is `{"turn": 7, … "tick": 1680}` (design.md:715). Likewise `deliveredLastTurn` was last
  written at the *start of turn N-1*, where it captured turn N-2's deliveries; the view for turn N
  therefore reports turn N-2's total, not turn N-1's.
- Impact: `marcher` reads `delivered_last_turn` as its fuel gauge (`src/hive/baselines.nim:76,84`)
  and champion #1's prompt says "Watch delivered_last_turn like a fuel gauge" (design.md:496); both
  act on a two-turn-old number. `sensed`/`contacts`/`last_doctrine` are *correctly* one turn old
  because they are cleared inside the same `installDoctrines` — that part matches the note.
- Not covered by a test: `tests/test_view.nim` builds views mid-turn (`:15-23,:49-53`), where
  `match.turn` is current, so the lag never appears.

**F5 — `scanContacts` is an extra step, run every 4 ticks, and `contacts[].ants` counts samples, not
ants.** *(factual divergence)*
- Where: `src/hive/sim.nim:459-476` and the call site `:567-568` (`if sim.tick mod 4 == 0`);
  `src/hive/broadcast.nim:64-81` (`count += hits`).
- Observed: the 15-step order in the design (design.md:257-314) has no contact scan. Each 4-tick
  sample increments `contactCount[colony][rival][block]` once per co-located ant, and the view sums
  those increments over the whole turn, so `"ants": 7` in the design's example
  (design.md:729) is, in the code, "co-location samples this turn", which for a busy block over 60
  samples can exceed the colony's 24 bodies. Deterministic either way (the comment at `:460-461`
  says so).

**F6 — `orbitsAlive()` counts surviving sources in quarters, so the `maxOrbits = 3` cap is not what
the note describes.** *(factual divergence / risk)*
- Where: `src/hive/sources.nim:97-106`; call site `src/hive/sim.nim:272-273`.
- Observed: the body counts live non-bonanza sources and returns `(live + 3) div 4`. Its own comment
  says "counting non-bonanza survivors in quarters is wrong" and then does exactly that. Three
  orbits each half-eaten (6 live sources) return `(6+3) div 4 = 2`, so a fourth orbit spawns while
  three are partly alive; conversely four orbits with one survivor each return 1.
- Note says: "if fewer than `maxOrbits = 3` orbits are alive, exactly one new orbit spawns"
  (design.md:167-168).
- The test that names this rule does not assert it: `tests/test_sources.nim:53-62` (`orbitCap`) only
  asserts `spawned mod 4 == 0` and reports "orbits spawn four at a time and respect maxOrbits".

**F7 — a raid is flagged only when the *nearest* nest within `raidRadius` is a rival.** *(factual
divergence, minor)*
- Where: `src/hive/sim.nim:419-429`; `src/hive/sources.nim:160-169` (`nearestNest` returns the
  closest nest ≤ `raidRadius`, ties to the lowest index).
- Note says: "If `carried_from`'s cell was within `raidRadius = 20` Chebyshev cells of a *different*
  colony's nest centre, the delivery is flagged `raid: true`" (design.md:285-287). A source 15 cells
  from your own nest and 18 from a rival's is inside the rival's radius but is not counted.
  The same `nearestNest` drives `near_nest` in the view (`broadcast.nim:52`) and `near` on
  `source_spawn` (`sim.nim:289-291`), consistently.

**F8 — the turn snapshot (step 14) is taken at the top of the tick, before step 2.** *(note)*
- Where: `src/hive/sim.nim:557-563`, inside `stepTick` before `spawnSources()`; design step 14 sits
  after the keyframe (design.md:306-309).
- Observed: taking it pre-step at `t mod 240 == 0` is what makes `rewindTo`
  (`src/hive/replay.nim:259-268`) able to resume a turn and re-install that turn's doctrine
  (`replay.nim:250-253`). `Snapshot` (`sim.nim:20-31`) carries planes, sources, ants, rng, delivered,
  harvested — every field the digest reads (`sim.nim:154-183`) — but not `sensed`, `contactCount`,
  `seenAmount/seenTurn`, `deliveredTurnStart`; none of those feed the step or the digest.
  `tests/test_determinism.nim:116-143` asserts snapshot restoration reproduces the forward digest.

**F9 — `focus_weight` repairs to a literal 0, not to the previous turn's value.** *(factual
divergence, minor)*
- Where: `src/hive/doctrine.nim:196` (`result.focusWeight = readPercent(node{"focus_weight"}, 0)`);
  every other integer uses `base.<field>` (`:185-190`). Note's table: "`focus_weight` … as `scouts`,
  default 0" (design.md:792), i.e. missing → previous turn's value.

**F10 — the public scoreboard is emitted in nest order, not "alias-sorted" order.** *(note)*
- Where: `src/hive/broadcast.nim:83-91`; note says "in a fixed alias-sorted order" (design.md:749).
  With the shipped `data/meadow.fieldspec.json:20-25` the nest order is Amber, Teal, Lime, Magenta —
  the order shown in the design's own example (design.md:730-731) but not alphabetical. Fixed and
  alias-only either way.

**F11 — the authored rock set differs from the note's illustrative shapes.** *(note, disclosed in
the brief)*
- Where: `data/meadow.fieldspec.json:6-19` — 12 shapes (5 discs, 3 rects, 2 polygons, …), all inside
  the top-left quadrant. None of the note's three illustrative shapes (design.md:624-626) appears;
  the note's polygon `[[30,52]…[28,62]]` would in any case sit outside the authored quadrant.
  The invariants the note actually pins hold: `src/hive/field.nim:168-175` ORs in all four mirror
  images, and `tests/test_field.nim:23-54` asserts both mirrors, pads/bonanza cells free, and one
  4-connected component (plus a 5–30 % rock density band the note does not state).

### Decision path, waits and bounds

**F12 — there is no outer 22 s per-turn deadline; the bound is the two attempt deadlines.**
*(factual divergence)*
- Where: `src/hive/llm.nim:29-30` (`FirstAttemptSeconds = 14`, `RetryAttemptSeconds = 6`), `:281-296`
  (`for attempt in 0 .. 1` … `client.sendBatch(batch, deadline)`); `src/hive/server.nim:250-256` —
  `turnBudgetSeconds` appears **only** in the budget-guard predicate
  `elapsed + 2.0 * gameConfig.turnBudgetSeconds > wallBudget`. Nothing wraps `decideAll` in a
  22 s timer.
- Note says: "one parallel batch … wrapped in one per-turn deadline"; "one outer per-turn deadline
  of 22.0 s" (design.md:383, 425-426).
- Consequence: the worst case is still bounded at 14 + 6 = 20 s per turn plus request-assembly
  (`userMessage` builds four views), so the arithmetic in design.md:388-396 survives; what is missing
  is the belt-and-braces outer bound. `tests/test_engine.nim:130-146` asserts a hung fake client
  returns in < 5 s, using a fake that sleeps `min(timeout,1)*100 ms` — it exercises the code path,
  not the real 14/6 s deadlines. *Untested* against a real hung socket.

**F13 — a turn batches the number of *LLM* seats, not always 4.** *(factual divergence, minor)*
- Where: `src/hive/llm.nim:267-279` — seats with `scripted[seat] != skNone`, or `client.disabled`,
  or an empty prompt are resolved scripted and never enter `open`; only `open` seats are posted
  (`:286-294`). Note says "Every turn batches exactly 4 requests" (design.md:384).
  `tests/test_engine.nim:74-108` gives all four seats prompts, so its
  `checkEqual(record.size, Colonies)` (`:95`) is true under that configuration. In the league mix
  (2 champions + 2 scripted fillers, `tools/ci/policies.json`) each batch will hold 2. The property
  the checklist cares about — one parallel batch per turn, never sequential — holds: one
  `sendBatch` call per attempt, `curl.makeRequests` (`llm.nim:140-144`).

**F14 — a 401/403 that does not say "Model access is denied" disables the client for the rest of the
episode instead of advancing the Bedrock candidate.** *(factual divergence)*
- Where: `src/hive/llm.nim:210-217`. The ladder advance at `:212-214` is gated on the literal string
  `"Model access is denied" in response.body`; otherwise `client.disabled = true` and every later
  turn short-circuits to scripted (`:269`, `:282`). A 429 does advance the candidate (`:218-221`).
- Note says: "on a 403 the client advances to the next candidate" (design.md:439).
- Bedrock ladder itself matches the note exactly: `:117-121` lists haiku-4-5, sonnet-4-6,
  sonnet-4-5 in that order, with `BEDROCK_MODEL` pinning one (`:112-114`).

**F15 — `max_tokens`, `temperature`, and the absence of `output_config.effort` all match; the
Anthropic-direct default model id is `claude-sonnet-5`.** *(note)*
- Where: `src/hive/llm.nim:137` (`newLlmClient(model = "claude-sonnet-5", maxOutputTokens = 900)`),
  `:181-201` (body carries `max_tokens`, `temperature: 0.4`, `system`, `messages`; Bedrock adds
  `anthropic_version`; direct adds `model`; no `output_config` key anywhere in the file).
  `src/hive/server.nim:221` constructs with the defaults, so `max_tokens = 900` ✓. The design pins
  only the Bedrock ladder, so the direct-path model id is unspecified; `claude-sonnet-5` is not an
  id I can verify. *Untested* — reaching it needs `ANTHROPIC_API_KEY` with no Bedrock sidecar.

**F16 — the budget guard is implemented as the note describes, but only in `server.nim`, and no test
exercises that code.** *(risk)*
- Where: `src/hive/server.nim:228-232` (`wallBudget = min(wallClockBudgetSeconds,
  episodeTimeoutSeconds * 0.6)`; with the shipped defaults 660 vs 720 → 660, matching the note),
  `:250-256` (guard, one `budget_guard` event with `remaining_s`), `:258-268` (once engaged, every
  seat gets a `marcher` doctrine tagged `dsFallback` with cause `budget_guard` for all remaining
  turns), `:293-294` (`outOfTime` → `deadline`/`wall_clock` at `wallBudget`).
- `tests/test_engine.nim:148-170` re-implements a guard inside its own provider and asserts the
  *episode* still ends `complete/full_time`; it never calls `server.nim`'s closure. Same for the
  disconnect-degrade rule, re-implemented at `tests/test_engine.nim:265-266`. So the shipped guard
  and the shipped `scripted[seat] = if connected … else skMarcher` line (`server.nim:243-245`) are
  covered only by inspection.

**F17 — done-broadcast deadline is an aggregate 3 s, not per-seat.** *(factual divergence, minor)*
- Where: `src/hive/server.nim:321-328`: `doneDeadline = epochTime() + DoneBroadcastSeconds` (3.0,
  `:38`) then `for slot, socket in game.playerSockets: if epochTime() > doneDeadline: break`.
  The note says "a 3.0 s per-seat deadline on the final done-broadcast" (design.md:427). The write
  order — done → replay → results — is exactly the note's (`:320-338`), and the 20 s shutdown grace
  is at `:360-364` (`ShutdownGraceSeconds = 20.0`, `:37`).

**F18 — `hive_player` invents a default prompt when neither env var is set, making the seat an LLM
seat.** *(factual divergence)*
- Where: `src/hive_player.nim:20-31` (`DefaultPrompt`), `:41-44` (`if prompt.len == 0 and
  scripted.len == 0: prompt = DefaultPrompt`), `:47-53` (register frame carries it).
- Note says: "A seat that sets neither defaults to `PLAYER_SCRIPTED=marcher`" (design.md:363-364)
  and "A seat that never registers, or registers with neither field, is treated as
  `scripted: 'marcher'`" (design.md:693-694). The *server* honours the note
  (`src/hive/roster.nim:38`, `:64-67`), so this only bites when the shipped player container runs
  with no env — which the certification fixture never does (`game.player[0].env.PLAYER_SCRIPTED =
  "marcher"`).

**F19 — the player's receive loop is an unbounded blocking read.** *(risk, checklist item 5's "no
blocking read")*
- Where: `src/hive_player.nim:74-84`: `while true: … socket.receiveMessage()`, no deadline; the loop
  exits on `isNone` (close), an exception, or `{"done": true}`. The connect side *is* bounded
  (`:33`, `:58-68`, 4 attempts with 1/2/3 s backoff, then `quit(0)`), and
  `tests/test_startup.nim:79-94` asserts an unreachable game exits 0 in < 60 s. The game side always
  broadcasts `done` and then `quit(0)` after the grace, so in practice the socket closes; a game pod
  that dies without closing would leave the player pod blocked until the platform kills it.

**F20 — the player sends `register` twice.** *(factual divergence, minor)*
- Where: `src/hive_player.nim:70` and again at `:97` on receipt of `welcome` ("in case the first send
  raced the server's slot registration"). Note: "the player sends exactly one text frame"
  (design.md:684). `Roster.register` is idempotent (`src/hive/roster.nim:49-69`), so the second frame
  is harmless.

### Truncation

**F21 — all five caps are implemented on rune boundaries.** *(note — traced, no divergence)*
- `note` ≤ 140 / `say` ≤ 32: `src/hive/doctrine.nim:20-25` (`truncateRunes` → `runeLen`/`runeSubStr`),
  applied at `:199-200`; caps in `src/hive/types.nim:46-50`.
- `register.policy` ≤ 48: `src/hive/roster.nim:8-12`, applied `:68`.
- `fallback.detail` ≤ 200: `src/hive/llm.nim:316` and again at `src/hive/server.nim:279`.
- `register.prompt` ≤ 4000: `src/hive/roster.nim:59-61` (transport) and `src/hive/llm.nim:172-174`
  (message assembly).
- Also rune-safe: the parser's error head (`doctrine.nim:92-94`).
- Tests: `tests/test_doctrine.nim:87-109` feeds a 37-rune `say` whose 32nd/33rd runes are 4-byte
  emoji, asserts the cut lands on the rune boundary, `validateUtf8 == -1`, and a `%*`/`$`/`parseJson`
  round-trip; `tests/test_engine.nim:277-290` does the same for `policy` (48) and `prompt` (4000).
  One gap: no test feeds a multi-byte `fallback.detail` at the 200-rune cap.

### Replay writer and re-derivation

**F22 — the replay is written and re-read exactly as the note describes; two arithmetic details
differ.** *(note)*
- `hive.replay.v1`, `format_version 1`, and every documented top-level key:
  `src/hive/replay.nim:77-99`. Strict read: `validateUtf8` first (`:105-106`), protocol check
  (`:113-116`), doctrine records range-checked (`:155-161`), `keyframes.len == (tick_count+23) div 24`
  (`:185-189`), `ants_b64` length `keyframes × 4 × antsPerColony × 3` (`:193-198`).
- Doctrines are the input log (`sim.nim:260-265` writes one record per seat per turn;
  `replay.nim:143-170` reads them back into a per-turn array).
- Re-derivation: `initReplayRuntime` (`replay.nim:200-218`) rebuilds the sim from `seed` + `field`
  + config and *verifies* the seed-derived seat permutation equals the recorded `seat_nests`;
  `stepOne` (`:246-257`) reinstalls the recorded doctrine at each turn boundary and compares each
  keyframe digest (`checkDigest`, `:231-244`, first mismatch latches, playback continues).
- Difference from the note's size arithmetic: for a 4800-tick episode the code produces **200**
  keyframes (ticks 0…4776; `sim.nim:575`, asserted at `tests/test_determinism.nim:47` and
  `tests/test_perf.nim:25`), not the note's 201 (design.md:902).
- Difference: `hiveStateDigest` also feeds `ant.held` (`sim.nim:166`) on top of the note's list
  (design.md:647-649). Harmless; both builds run the same code.

**F23 — `results` is key-for-key the manifest's `results_schema`.** *(note — traced)*
- `src/hive/rules.nim:199-226` emits 25 keys; `ResultsKeys` (`:228-234`) lists the same;
  `coworld_manifest_template.json` `game.results_schema.properties` has the identical 25 and
  `required` repeats them; enums `["complete","deadline","fault"]` and
  `["full_time","wall_clock","sim_fault","host_error"]` match. `tests/test_manifest.nim:113-147`
  asserts all three sets are equal by sorting them.

### Manifest and packaging

**F24 — the manifest matches the note in every respect I checked.** *(note — traced)*
- `num_agents: 4` in `variants[default].game_config`, `variants[sprint].game_config`, and
  `certification.game_config`; `certification.players` is four `{"player_id":"baseline"}`;
  `certification.game_config.players` is four. `episode_timeout_minutes: 20`.
  `game.replay_viewer.bundle == "static-replay-viewer"`. `game.protocols` has both `player`
  (10 959 chars) and `global` (1 752 chars), both `{"type":"text","value":…}`. `game.docs.readme`
  is text (4 385 chars) and `pages` are `rules.md` (9 227) and `protocol.md` (10 959), both
  `content.type == "text"`. `game.runnable.image == "{{HIVE_IMAGE}}"` matches compose service `hive`
  (`compose.yaml:2`). Asserted by `tests/test_manifest.nim:13-36,38-51,53-79,81-111`.
- One deviation from the note's own words: the `sprint` variant also changes `bonanzaTicks` to
  `[1200]`, where the note says sprint "changes only the episode length" (design.md:1145). Since the
  sprint episode is 2880 ticks, a 3600-tick bonanza could never fire; the change looks necessary.

**F25 — placeholder gate, release order, policies and executable bits are clean.** *(note — traced)*
- `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`,
  `docker_smoke.sh`, `policies.json` returns nothing (exit 1) — checklist item 12's gate passes.
- `coworld-release.yml` and `coworld-submit.yml` are byte-identical to
  `templates/*` after `<slug>/<IMAGE>/<SEATS>` substitution (`diff` empty), so the
  build → certify → upload-policies → upload-coworld → secret-put order is the template's.
- `git ls-files -s`: `tools/build_replay_viewer.sh` 100755, `tools/ci/docker_smoke.sh` 100755,
  `tools/ci/policies.json` 100644 — the two hooks are executable as required.
- `tools/ci/policies.json` has four policies, all `"run": "/bin/hive-player"`: two `PLAYER_PROMPT`
  champions (`hive-pathwright`, `hive-swarmraid`) and two `PLAYER_SCRIPTED` fillers; champion #2
  carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Asserted by
  `tests/test_manifest.nim:182-214`.
- Seat-count invariants: `tools/ci/docker_smoke.sh:98-141` retains all four `SEAT-COUNT FAIL:`
  checks plus the independent `SMOKE_SEATS=4` cross-check (`:47`). The docker-smoke log for run
  32621277603 contains no `SEAT-COUNT` string and ends
  `smoke OK: seats=4 results=1076B replay=53253B reason=complete`.
- `docker-smoke` builds the image in the same job immediately before the smoke
  (`ci.yml:172-181`), so a stale binary cannot be smoked.

**F26 — the server still registers `GET /client/replay`.** *(note, checklist item 3 wording)*
- Where: `src/hive/server.nim:528` (route), `:384-388` (handler serving the spliced chrome),
  `tests/test_server.nim:75-83`. The design keeps this deliberately ("The game server still serves
  `/client/replay` for local viewing off the identical `dist`", design.md:944) and the starter does
  the same (`/workspace/starters/coworld-ctf/src/ctf/server.nim:627,642,840`). The manifest declares
  the static bundle and nothing references a pod-served viewer; I record it because checklist item 3
  says "No `/client/replay` pod path anywhere".
- Related, observed: `splicedChrome()` (`src/hive/server.nim:112-125`) replaces `<!-- BROADCAST_CORE -->`
  with **only** `static_replay.js`, while `Dockerfile.replay-viewer:42` replaces it with
  `hive_replay.js` *and* `static_replay.js`. On the native `/client/replay` page `HiveReplayModule`
  is therefore undefined and `static_replay.js:177` would throw a `ReferenceError` inside the `load`
  handler — no `data-replay-error`, just a stuck curtain. The static bundle (the shipped artifact) is
  unaffected. `tests/test_server.nim:77-80` only checks that the page carries `id="board"`,
  `wire_constants.js` and `chrome_common.js`.

### Tests

**F27 — the 16 files the note lists are all present, and nothing in `tests/` was weakened during
this run.** *(note — checklist item 1, second half)*
- `git log -p --name-only -- tests/` shows every test file, `tests/support/helpers.nim` and both
  fixtures introduced in the single commit `48465f3`; there is no later commit and therefore no
  deleted assertion, widened tolerance or added skip *within this run*.
- Coverage against the note's list, file by file, is close. Where the shipped test is weaker than the
  note's sentence:
  - `tests/test_pheromones.nim:43` accepts the half-life crossing anywhere in **168…184** ticks;
    the note says "below 2000 after 175 ± 2 ticks" (design.md:1193). Decay fires every 8 ticks, so
    the achievable resolution is 8 ticks — ±2 is not reachable by construction.
  - `tests/test_determinism.nim:61-93` nudges each doctrine integer on **every** turn, not turn 0;
    the deviation is stated in the code comment (`:62-64`: `poach`/`lay_food` are inert on turn 0).
    It does assert all six integers each move the final digest.
  - `tests/test_perf.nim:13-14` allows 270 s / 30 ms in a debug build; the release budgets are the
    note's 45 s / 5 ms.
  - `tests/test_ants.nim:134-150` asserts `alphaFood div 4` and `alphaRival 0` but **not** the
    doubled scout noise, though its `report` line claims it; the doubling lives in
    `src/hive/ants.nim:87` and is unasserted.
  - `tests/test_sources.nim:53-62` does not assert the `maxOrbits` cap (see F6).
  - `tests/test_engine.nim:237-253` asserts the unregistered-seat default but not the
    `COGAME_PLAYER_FAILURE_URI` report the note's test 9 names; `tests/test_server.nim:189-190` only
    asserts the *negative* (no failure file when all four connect). `src/hive/server.nim:206-219`
    (the `declarePlayerFailure` path) is therefore uncovered.
  - `tests/test_viewer.nim:194-203` silently `return`s when no built bundle is present, which is
    always true in the `test` job; the real module run happens in `wasm-viewer` (F1).
- Strong coverage worth naming: `tests/test_replay.nim:129-148` re-derives the whole episode from
  the doctrine stream and asserts **every** keyframe digest and **every** byte of `ants_b64`;
  `:150-160` asserts seek-to-end/mid/backwards land exactly; `:162-177` asserts six malformed
  documents are rejected. `tests/test_view.nim:104-143` runs a full episode and asserts no
  `results.names` string appears in any view, any `userMessage` prompt, or any event body — and that
  aliases *do* appear, so the assertion is not vacuous.

**F28 — no grid-search harness for the baseline parameters exists in the tree.** *(risk — checklist
item 7, second sentence)*
- `tools/` contains `record_fixtures.nim`, `gen_wire_constants.nim`, `build_replay_viewer.sh`,
  `wasm_replay_smoke.cjs`, `ci/`. Nothing sweeps `marcher`'s constants. The ordering claim is
  asserted at one seed: `tests/test_baselines.nim:128-147` runs a 4800-tick
  marcher/driftling/marcher/driftling match at seed 42, asserts `complete/full_time` and that the
  marcher seats out-deliver the driftling seats. The legality half of item 7 is fully covered
  (`tests/test_baselines.nim:41-81`, 500 hostile views × 2 baselines, schema + compiled-coefficient
  ranges).

**F29 — the node wasm smoke lives in the `wasm-viewer` job rather than `test`.** *(note, disclosed in
the brief)*
- `ci.yml:241-247`; `tests/test_viewer.nim:185-209` explains why (the `test` runner has no emsdk).
  CI evidence: `wasm replay smoke OK: 960 ticks, 961 frames, packet 113204B, no digest mismatch`.

**F30 — two extra wasm exports and no `static_replay_worker.js`.** *(note, disclosed in the brief)*
- Extra exports `hive_rock_ptr`/`hive_rock_len` (`replay-viewer/hive_replay.nim:113-117`) and
  `hive_tick` (`:122-123`), both listed in `EXPORTED_FUNCTIONS` (`replay-viewer/config.nims:50`) and
  both consumed by the shell (`replay-viewer/static_replay.js:118-124`) and the node smoke
  (`tools/wasm_replay_smoke.cjs:40,48`). The note's export list (design.md:948-950) does not include
  them.
- `static_replay_worker.js` is listed in the note's bundle manifest (design.md:962) and does not
  exist. Playback is main-thread: `Dockerfile.replay-viewer:28` copies `client/broadcast_core.js`
  into the bundle, `client/replay_broadcast.html:1727` loads it, and the wasm module emits a binary
  `HVP1` packet (`src/hive/render.nim:9-27,46-92`) that `broadcast_core.js:124-172` decodes and
  paints. The note's own §Viewer text describes the OffscreenCanvas-Worker protocol as kept
  verbatim (design.md:988-991); the code replaced it. The packet layout in `render.nim` and the
  decoder in `broadcast_core.js` are cross-checked byte-for-byte by the node smoke
  (`tools/wasm_replay_smoke.cjs:127-158`), which is the mitigation.

---

## Traced and consistent

- **T1 — Resolution steps 1–3, 5–13 in order.** `src/hive/sim.nim:554-577` runs
  `spawnSources` → `retireSources` → `runAnts` → (contacts) → trail-war @48 → decay @8 → harvest @24
  → keyframe @24; `runAnts` (`:351-457`) does deposit(5) → pickup(6) → delivery(7) → move(8) →
  release(9) in ant order over `(t+g) mod antStepTicks == 0` (`:356-357`); step 1 is
  `installDoctrines` (`:211-265`) called from `rules.nim:116-117`; step 15 is `rules.nim:119-127`
  (`t+1 == episodeTicks` → `complete/full_time`; the wall-clock probe → `deadline/wall_clock`;
  `t mod 24 == 0` invariant guard → `fault/sim_fault`). Constants all match the note:
  `TrailWarPeriod 48`, `HarvestPeriod 24`, `KeyframePeriod 24` (`sim.nim:82-84`) and
  `src/hive/config.nim:10-41` (24 ants, 4800/240/2 ticks, 4000/4/248/8, 12, 3, 240/60/1440/14,
  `[1200,3600]`/100/900, 20, 800, 22/660/90 s). Pickup scan order N,NE,E,SE,S,SW,W,NW =
  `types.nim:63-64`; lowest live source id wins (`sim.nim:396-402`).
- **T2 — Kernel formulas and tie-breaking.** `searchScore` (`ants.nim:27-45`) is
  `(αFood·F_own)≫4 + (αRival·F_rivalMax)≫4 − (αHome·H_own)≫4 + [fwd]αFwd + 900·foodAdjacent + noise`;
  `carryScore` (`:47-66`) is `(βHome·H_own)≫4 + [within 12 and closing]1200 + [fwd]260 + noise`;
  candidates are `(d+7)&7, d, (d+1)&7` (`:20-22`); the winner is chosen with a strict `>`
  (`:105`) scanning left→forward→right, so ties break left, then forward, then right; boxed-in turns
  `(d+2)&7` and does not move (`:109-114`). Scout modifiers: `alphaFood div 4`, `alphaRival 0`
  (`:36-38`), noise `rnd(2·alphaNoise)` (`:87`); carrying noise `rnd(32)` (`:86`, `CarryNoise` in
  `types.nim:43`). Coefficient table `doctrine.nim:47-62` reproduces the note's nine rows exactly,
  including `scoutCount = (scouts·ants + 50) div 100`; `tests/test_baselines.nim:83-116` pins both
  endpoints of every row.
- **T3 — PCG discipline.** One stream (`types.nim:191-215`), first draw is the seat permutation in
  `newSim` (`sim.nim:110-112`), then per tick sources (`sources.nim:147-149`, exactly two draws per
  attempt) then ants in ant order; `moveAnt` draws all three noise values before looking at terrain
  (`ants.nim:83-88`) and `releaseHeading` always draws both the roll and the uniform
  (`ants.nim:148-152`), so the draw count per activation is terrain-independent.
- **T4 — One parallel batch, tolerant parse, exactly one retry, recorded fallback.**
  `llm.nim:281-320` issues at most two `sendBatch` calls per turn and `sendBatch` defaults to
  `client.curl.makeRequests(batch, timeoutSeconds)` (`:140-144`); the retry appends the
  "your previous reply was invalid" hint (`:288-292`); after the second failure every remaining seat
  gets `scriptedResolved(..., skMarcher, ..., dsFallback)` (`:322-327`) and the caller writes a
  `fallback` event with `attempt`, `cause ∈ {timeout,parse_error,transport_error,no_credentials,
  budget_guard}` and a 200-rune `detail` (`server.nim:274-279`, `events.nim:67-74`,
  `rules.nim:141-148`). Parsing is a brace-scanner that survives prose and fences
  (`doctrine.nim:66-96`), accepts numeric strings, `"70%"`, floats and bools (`:98-120`),
  `focus` as `[bx,by]` or `{"bx","by"}` (`:135-160`), and only raises when no recognised doctrine key
  is recoverable (`:210-214`). `tests/test_engine.nim:74-146` and `tests/test_doctrine.nim` cover all
  of this; the repaired doctrine is what is installed *and* recorded (`sim.nim:234-265`).
- **T5 — Every wait I could find, and its bound.** Player connect: `playerConnectTimeoutSeconds`
  (90 hosted / 60 cert) polled at 200 ms (`server.nim:196-204`). LLM attempts: 14 s then 6 s
  (`llm.nim:29-30,284`). Engine hard stop: `wallBudget` = min(660, 0.6·1200) (`server.nim:228-230,
  293-294`). Done broadcast: 3 s aggregate (`:321-328`, see F17). Shutdown grace: 20 s then `quit(0)`
  (`:360-364`). Artifact POST: 60 s curl timeout (`:137`). Viewer fetch: 20 s `AbortController` with
  a Retry button (`static_replay.js:15,81-98,49-56`). Player connect retry: 4 attempts, ≤ 6 s of
  backoff, then `quit(0)` (`hive_player.nim:33,58-68`). The only unbounded wait I found is F19.
  No `while true` without an exit in the server or the sim; `runEpisode` terminates on tick count
  (`rules.nim:115-127`), and the kernel's boxed-in rule is guarded by the single-component invariant
  (`field.nim:210-237`, asserted in `tests/test_field.nim:44-54`).
- **T6 — Two name spaces.** Aliases come from the fieldspec (`data/meadow.fieldspec.json:20-25`) and
  are attached to *nests*; the seat→nest permutation is the first PCG draw and varies with the seed
  (`tests/test_view.nim:145-159` finds ≥ 4 distinct permutations in 40 seeds). Views, prompts,
  `turn` frames and every event body carry `match.meadow.nests[colony].alias` only
  (`broadcast.nim:103-168`, `sim.nim:143-148,253-258`, `events.nim`). Real names appear in exactly
  three places: `replay.names.players` (`replay.nim:66,85-90`), `results.names`
  (`rules.nim:182,199`), and the spectator/scorebug path (`global.nim:29-31`,
  `client/replay_broadcast.html:1806`). Asserted end-to-end at `tests/test_view.nim:104-143`.
- **T7 — MODULARIZE / EXPORT_NAME agree with the bootstrap.** `replay-viewer/config.nims:47-48`
  links `-s MODULARIZE=1 -s EXPORT_NAME=HiveReplayModule`; `replay-viewer/static_replay.js:176-181`
  calls the factory `HiveReplayModule()` and awaits the promise — it never waits on
  `Module.onRuntimeInitialized` (grep: the string does not occur in the repo).
  `tools/wasm_replay_smoke.cjs:83-84` does the same (`const factory = require(modulePath);
  const module = await factory();`) and that path is green in CI. This is the specific lantern
  deadlock the checklist names, and it is **not** present.
- **T8 — 360 px legibility rules.** `client/replay_broadcast.html:1486-1491` —
  `.plate .team-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }`
  — declared *after* the inherited rule at `:201-219` (so it wins), and
  `@media (max-width: 640px)` at `:1600-1612` hides `#doctrinebar` and `#viewpanel`, shrinks
  `#nestbug` to dot+numeral, hides `.lives-label`, and clamps banner text to
  `clamp(11px, 3.4vw, 17px)`. Paintbot's `--hudscale = Math.max(0.5, Math.min(1.6, boardW/760))` and
  `.tiny` at `boardW <= 620` survive (asserted `tests/test_viewer.nim:48-56`). Note the checklist
  writes the selector as `.plate-name`; this repo (and its starter) use `.plate .team-name`, which
  is what the design note pins (design.md:1065).
- **T9 — Scoring.** `rules.nim:46-61`: `total == 0` → four 0.25s; otherwise the first three seats are
  `delivered/total` and the fourth is the residual `1 − Σ`, in slot order via `seatNest`. `win` is
  `slot == seat` with `winnerSlot` returning −1 on a tied maximum (`:67-80`), rendered as JSON `null`
  (`:221`). Fault → `faultScores()` and `winner: null` (`:96,103,160-161`). `tests/test_scoring.nim`
  pins the worked example to 1e-5, exact 1.0 sums over 500 random vectors, the tie, the empty match,
  monotonicity, and a deadline cut.
- **T10 — Field bake.** `field.nim:160-175` stamps authored shapes then ORs the four mirror images,
  so symmetry cannot drift; nest pads and bonanza cells are validated at load (`:196-208`);
  `pointInPolygon` keeps the starter's strict-straddle, odd-on-either-side convention in int64
  (`:48-92`).
- **T11 — Event vocabulary.** All 13 record types from the note's table exist with the documented
  fields (`events.nim:13-142`), including the short-key `deliver` (`t,c,n,s,r`) and `harvest`
  (`t,s,c,u`), and `eventsJsonl`'s trailing summary row (`:144-151`).
- **T12 — CI green at the reviewed sha.** Run 32621277603, `head_sha 48465f36…`, branch `main`,
  conclusion `success`; jobs `test`, `docker-smoke`, `wasm-viewer` all ✓. Only annotations are the
  Node-20 deprecation notices.

---

## Could not determine

- **Whether B2's marker value (`'1'`) and placement satisfy the platform's probe.** The repo has no
  `viewer_smoke.mjs`, so there is nothing in-tree that states the expected value. What would settle
  it: the template's `templates/tools/ci/viewer_smoke.mjs` (present in coworld-builder, absent here)
  and a run of it against `dist/static-replay-viewer` reporting `loaded: true`.
- **Whether the assembled page actually renders.** The node smoke proves the wasm module runs and
  that `broadcast_core.js`'s decoder accepts a real packet, but nothing loads `index.html`,
  runs `HiveChrome.attach`, fetches `art/*`, or drives `tickLoop`. A headless-chromium load of the
  built bundle with a real replay is the only evidence that would settle it. *Untested.*
- **The real 14 s / 6 s deadlines and the Bedrock ladder.** Both are exercised only through the
  `sendBatch` seam with fakes (`tests/test_engine.nim:27-62`); no test issues a real HTTP request,
  and no CI job has credentials (the docker smoke runs credential-free, which is why every turn
  fell back and the episode finished in ~22 s). Phase 60 against a live pod is what settles it.
- **The effect of F3 (recall) and F4 (stale `delivered_last_turn`) on play quality.** Both are
  deterministic and reproducible, so they cannot break the replay contract, but whether they change
  the ladder's separation would need a scripted A/B run. *Untested.*
- **Whether `claude-sonnet-5` (F15) is a valid Anthropic model id.** Unreachable in the sandbox; only
  matters on the `ANTHROPIC_API_KEY` path, not on the hosted Bedrock path.
