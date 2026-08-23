# r2 review — raid
Range: `501040d..6a8a68c` (16 commits) + full re-trace at head   Head: `6a8a68c23a606cf7c2046568800c753ecee3dd04`
Files read: 41 (all of `src/raid/*.nim`, `src/raid.nim`, `src/raid_player.nim`, `replay-viewer/*`,
`client/replay_broadcast.html`, `client/broadcast_core.js`, all 17 `tests/*.nim`,
`tools/ci/docker_smoke.sh`, `tools/ci/policies.json`, `tools/build_replay_viewer.sh`,
`tools/wasm_replay_smoke.cjs`, `Dockerfile.replay-viewer`, all three workflows,
`coworld_manifest_template.json`, `docs/RULES.md`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST

**Head has not moved since round 1.** `git log -1 origin/main` → `6a8a68c` ("F18 (cont.): assert the
hung-client budget and the control-byte digest", 2026-08-23 06:03:40Z), the same sha r1-verdict.md
adjudicated. No round-2 fixer commit exists at the time of this read, so r1's one standing blocking
finding (checklist item 13, browser smoke) is re-verified below from the tree and from CI rather
than carried forward on the verdict's word.

CI evidence used: run **32621942459**, `main`, sha `6a8a68c`, conclusion `success`, jobs
`test` / `docker-smoke` / `wasm-viewer` all `success`
(`gh run list -R Metta-AI/cogame-raid --branch main -w ci.yml`, `gh run view 32621942459`).

---

## Finding index

| # | Observation | Category | Checklist item | Blocking candidate |
|---|---|---|---|---|
| B1 | `wasm-viewer` never loads the bundle in a browser: no `Load the bundle in a real browser` step, no `tools/ci/viewer_smoke.mjs`, no `needs: docker-smoke`, and `docker-smoke` uploads no replay | static-viewer | 13 (bullet 1) | **yes** |
| N1 | `stalwart` tank emits `on_telegraph: dodge`; healer and dps stand on `station: point` — the note says `hold` / `ranged` | correctness (design divergence) | none | no |
| N2 | Tick step runs `startHeals` after attacks; the note's step 8 lists only (a)–(e) | correctness | none | no |
| N3 | Control layer adds two heal gates (`HealWasteFloor`, "planted") the note does not specify | correctness | none | no |
| N4 | First cleave/pour fire on tick index 95/191; the note says "tick 96"/"tick 192" | correctness | none | no |
| N5 | `avoidable_hits` deliberately excludes crucible hits | correctness | none | no |
| N6 | `/client/replay` route still served by the game server | static-viewer (adjudicated r1) | 3 (literal wording) | no |
| N7 | `order.latency_ms` is the whole-batch latency, identical for every LLM seat in a turn | legibility | none | no |
| N8 | Two §Tests items are untested: the 3.0 s done-broadcast bound, and the no-show / reconnect e2e | other | none | no |
| N9 | `raid_player.nim`'s receive loop has no timer of its own | hang (player side) | 5 (not a named wait) | no |
| N10 | `requestFor` sends `output_config.effort` for non-Haiku models; the note says no effort field at all | correctness | none | no |

---

## Blocking

### B1 — the `wasm-viewer` job green at head never executes the viewer in a browser
- Where: `.github/workflows/ci.yml:190-319` (the whole `wasm-viewer` job); `.github/workflows/ci.yml:152-181`
  (the `docker-smoke` job); `tools/ci/docker_smoke.sh:1-294`; `tools/ci/` contains only
  `docker_smoke.sh` and `policies.json`.
- Observed, step by step:
  - `grep -n "needs:" .github/workflows/*.yml` → **no matches** (exit 1). `wasm-viewer` has no
    `needs: docker-smoke`; in run 32621942459 both jobs started at `06:03:45/46Z`, i.e. in parallel.
  - `find . -name '*.mjs'` → **empty**. `tools/ci/viewer_smoke.mjs` is absent from the tree, and so
    is the template's `Assert the viewer load test is present` step
    (`/workspace/coworld-builder/templates/ci.yml:238-247`).
  - The job's steps, read in order at `ci.yml:194-319`: checkout → buildx → assert the hook is
    executable (`:205-216`) → build the bundle (`:218-219`) → assert `index.html` + a non-empty
    `.wasm` exist (`:221-234`) → upload the `static-replay-viewer` artifact (`:236-242`) → stage the
    bundle into `replay-viewer/dist` (`:250-257`) → nim toolchain (`:259-307`) → "Run the viewer
    tests against the built bundle" (`:309-319`, `nim r … tests/test_viewer.nim` gated on
    `grep -q 'WASM-SMOKE OK'`). There is **no** step that opens the page.
  - The job list GitHub reports for run 32621942459's `wasm-viewer` is exactly those 13 steps
    (`gh run view 32621942459 --json jobs`): `Load the bundle in a real browser` does not appear.
  - The replay the template's browser step consumes does not exist either: `tools/ci/docker_smoke.sh`
    ends at line 294 with the artifact assertions and has no `SMOKE_REPLAY_OUT` copy (the template's
    `tools/ci/docker_smoke.sh` copies `${work_dir}/replay.json` to `dist/smoke/replay.json` in its
    last 12 lines), and `docker-smoke` in `ci.yml:175-181` has no `Upload the smoke replay` step
    (template `ci.yml:192-199`). The smoke's `work_dir` is a `mktemp` deleted by the EXIT trap
    (`tools/ci/docker_smoke.sh:58,61-66`), so the only real replay CI produces is destroyed seconds
    after it is validated.
- Checklist item: **13. Viewer executes** — "`ci.yml`'s `wasm-viewer` job is green on `main` at the
  reviewed sha **including its `Load the bundle in a real browser` step** (`tools/ci/viewer_smoke.mjs`,
  headless chromium, loading the replay `docker-smoke` produced). Cite the run id and confirm the step
  ran — a job green because the smoke step is absent, commented out, or `continue-on-error` is a
  blocking finding, and so is a `wasm-viewer` that does not `needs: docker-smoke`. … **File presence
  is not evidence here; the smoke's `loaded: true` is.**"
- Why blocking: three of the item's named conditions are falsified at the reviewed sha (step absent,
  harness absent, no `needs:` edge). Nothing in this repo has ever run the browser shell
  (`index.html` + `static_replay.js` + `static_replay_worker.js` + `broadcast_core.js`); the only
  executed artefact is the wasm module under node, which never touches the shell, the worker
  bootstrap, the OffscreenCanvas path or the two markers. The failure mode the item was written
  against (cogame-lantern: every file present, every asset 200, page hangs forever) is invisible to
  everything CI currently does.
- What I *can* say about the code the missing step would exercise (observed, not evidence for the
  item — the item explicitly rules file reading out):
  - `replay-viewer/config.nims:45-46` links `-s MODULARIZE=1 -s EXPORT_NAME=RaidReplayModule`;
    `replay-viewer/static_replay_worker.js:86` bootstraps with the factory
    `self.RaidReplayModule({...}).then(instance => Module = instance)`, and
    `tools/wasm_replay_smoke.cjs:100-104` uses the same factory. `grep -rn onRuntimeInitialized`
    → no matches. Link flags and bootstrap agree; the lantern deadlock condition is **not** present.
  - Both markers exist and are set from the shell's own paths:
    `replay-viewer/static_replay.js:150` sets `data-replay-loaded="true"` when the worker's `loaded`
    message arrives, and the worker posts `loaded` only after `core.ingest(first)`
    (`static_replay_worker.js:132-137`), whose `draw()` increments `draws` and fires `onFirstFrame`
    (`client/broadcast_core.js:353-373`) — so the attribute does land after a drawn frame;
    `static_replay.js:40` sets `data-replay-error` in `showFailure`, which is reached from the
    missing-`?replay=`, fetch-timeout, worker-error, worker-crash and OffscreenCanvas-unsupported
    paths (`:87,160,173,181,189,193`).
  - The page does wire the shell: `client/replay_broadcast.html:2211` `RaidStaticReplay.createCore({…})`
    and `:2245` `core.start()`, with the three splice markers at `:1756-1758` replaced by
    `Dockerfile.replay-viewer:42-45`.
  - CI run 32621942459 logged `WASM-SMOKE OK: 647 ticks, digest 925898626, 112 events`
    (`wasm-viewer` step 13), i.e. the emitted wasm module really was loaded and driven under node.
- What would settle it: `tools/ci/viewer_smoke.mjs` in the tree, the template's
  `Load the bundle in a real browser` step plus `needs: docker-smoke` in `wasm-viewer`, the
  `SMOKE_REPLAY_OUT`/`smoke-replay` artifact hand-off from `docker-smoke`, and one green run on
  `main` whose log carries the harness's `loaded: true` line.

---

## Non-blocking

### N1 — the `stalwart` baseline's reaction and stations differ from the note's description
- Where: `src/raid/baselines.nim:197-200` (tank), `:238-241` (healer), `:285-288` (dps).
- Observed: the tank order is `Order(intent: inTankBoss, station: stPoint, target: "boss",
  onTelegraph: rxDodge, px: PitCx, py: PitCy - TankStandDy …)`. The design note (§Decisions →
  Scripted baselines) specifies `on_telegraph: hold` for the stalwart tank, and `station: ranged`
  for the healer and the dps; the code puts healer and dps on `station: point` with explicit
  coordinates (`HealerStands`, `DpsStands`, `MeltdownStacks`, `baselines.nim:36-55`). The dps
  cardinals sit on the 260 px `RangedRingPx` circle, so they are geometrically the note's ranged
  ring; the healer stands (`[617,440]`, `[760,420]`, `[474,420]`) are 111–190 px from the pit
  centre, i.e. not the ranged ring.
- Note vs code: the departure is argued in place — `baselines.nim:188-196` does the arithmetic
  (120 hp per 8 s cleave + 36.7 hp/s melee = 52 hp/s against a 45 hp/s sustained healer ceiling) and
  concludes holding is a slow wipe. `tests/test_baselines.nim:161-176` pins that stalwart still
  more than doubles greenhorn on four seeds, and `:191+` pins that the tank's emitted reaction is
  `soak` on crucible duty.
- Not blocking: no checklist item names the baselines' reaction; item 7 asks only that the scripted
  baseline plays a full legal episode (it does, `tests/test_baselines.nim:150-159`) and that the
  parameters were tuned with a grid harness (`tools/tune_baselines.nim`, present).

### N2 — the tick's ability sub-order carries a sixth phase the note does not list
- Where: `src/raid/sim.nim:418-424`; `src/raid/abilities.nim:191-193`.
- Observed: step 8 runs `doInterrupts → doTaunts → doShields → completeHeals → doAttacks →
  startHeals`. The note's step 8 lists exactly (a) interrupt, (b) taunt, (c) shield, (d) heal
  completion, (e) attacks. `startHeals` (beginning a cast) is a sixth call after (e), commented at
  `abilities.nim:191-193` as deliberate ("a cast started now first ticks on the next tick and lands
  exactly HealCastTicks later").
- Not blocking: the note never says where a cast *starts*; the observable rule it does pin (a heal
  completes at exactly 24 ticks) is asserted by `tests/test_combat.nim:62-83`.

### N3 — two heal gates in the control layer are not in the note's control-layer spec
- Where: `src/raid/control.nim:147-157` (`HealWasteFloor = 60`, `worthHealing`), `:352-358`
  (`planted`: never start a cast while the controller still intends to walk).
- Observed: the note's control layer sets `bit2 heal` "when a heal target is selected and mana ≥ 60
  and no cast is running". The code additionally refuses to begin a cast on a cog missing < 60 hp
  and refuses to begin one on a tick where `moveX/moveY != 0`. Both are commented with their reason
  (overheal waste; the 8 px cast-cancel rule).
- Not blocking: r1 filed the same observation (F4) and the fixer answered with the comments now in
  place; no checklist item covers it.

### N4 — the first cleave and the first pour fire one tick before the note's prose
- Where: `src/raid/types.nim:98` (`CleaveFirstTick* = 96`), `:104` (`PourFirstTick* = 192`);
  `src/raid/state.nim:96` (`cleaveCd: CleaveFirstTick, pourCd: PourFirstTick`);
  `src/raid/boss.nim:8-13` (timers decrement) then `src/raid/sim.nim:432` (`scheduleBoss` fires on
  `cleaveCd <= 0`).
- Observed: the counter is armed before tick 0 and every tick spends a decrement before scheduling,
  so the cast starts on tick index 95 (the 96th tick) and the pour on index 191. The note says
  "The first cleave of an encounter starts at tick 96" / "First pour at tick 192".
- Note vs code: `docs/RULES.md:134-135` and `:146-147` now state the index explicitly, and
  `tests/test_boss.nim:43` (`testFirstCleaveAndPourTicks`) pins both. r1 escalated this and the
  judge adjudicated "keep the code, keep the doc+test". Re-verified unchanged at head.

### N5 — `avoidable_hits` counts cleave and pour but never crucible
- Where: `src/raid/telegraphs.nim:96` and `:102` (`avoidableHits.inc`) versus `:106-109` (the
  crucible branch, with the reason written out).
- Observed: the note defines `avoidable_hits` as "a hit by a telegraph the cog was inside at
  resolution". The crucible branch deliberately does not increment it, because standing in a
  crucible is the correct play.
- Not blocking: a per-seat meter, not part of the score (`src/raid/scoring.nim:70` records it,
  nothing reads it back); no checklist item names it.

### N6 — the game server still routes `/client/replay`
- Where: `src/raid/server.nim:420` `result.get("/client/replay", replayPageHandler)`.
- Observed: the route exists at head and serves `client/replay_broadcast.html`
  (`server.nim:284-287`). The *hosted* viewer is the static bundle — the manifest declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` and the worker fetches only the `?replay=`
  URL plus same-origin bundle assets (`replay-viewer/static_replay_worker.js:118`, `:71`).
- Not blocking: r1's judge adjudicated this against item 3's literal "No `/client/replay` pod path
  anywhere" and ruled it does not falsify the item (both starters carry the identical local-debug
  route). Recorded here because I read it, not to reopen it.

### N7 — every LLM seat in a turn is stamped with the same `latency_ms`
- Where: `src/raid/server.nim:250-255`; `src/raid/llm.nim` never assigns `latencyMs`.
- Observed: `decide` measures `epochTime()` around the whole `decideAll` call and writes that single
  figure into every decision whose `source != osScripted`; `installOrders` copies it into the
  `order` event (`src/raid/sim.nim:340`). A seat that answered in 1.2 s and a seat that took the
  full 7 s therefore record the same `latency_ms` — the batch's wall time.
- Note vs code: the note's `order` record carries `latency_ms` per seat but never says it must be
  per-seat-measured; with a single `curly.makeRequests` batch the batch time is also the slowest
  seat's time. Phase 60 reads `source`/`intent`/`note`, not latency.

### N8 — two §Tests items have no test
- Where: `tests/test_server.nim:1-162` (the whole file); `tests/test_engine.nim:219-228` (the
  run list).
- Observed: §Tests 11 asks for "the `done` broadcast is bounded at 3.0 s per seat" — `test_server.nim`
  covers `/healthz`, 403, 409, register, `/global`, the client routes, `/replay-data` and the
  file-only sinks, and never exercises `broadcastDone`; `grep -rn "DoneBroadcast\|reconnect\|
  everRegistered\|declarePlayerFailure" tests/` → no matches. §Tests 9 asks for "a seat that never
  registers plays `stalwart` and is reported to `COGAME_PLAYER_FAILURE_URI`" and "a mid-encounter
  disconnect degrades to `stalwart` and revives on reconnect" — both behaviours exist
  (`server.nim:217-235`, `:405-416`) and neither has a test.
- Not blocking: r1's F18 recorded the same two gaps and the fixer recorded them as open. Item 5's
  bound itself *is* implemented and enforced (`server.nim:129-149`), which is what the checklist asks.

### N9 — the player container's receive loop has no timer
- Where: `src/raid_player.nim:83-88` `while true: let received = socket.receiveMessage()`.
- Observed: `whisky`'s `receiveMessage` blocks until a frame, a close, or a socket error. The connect
  side *is* bounded (`:66-77`, 5 attempts with backoff, then `quit(0)`), and the loop ends on the
  `done` frame (`:93-95`) or on `isNone` (`:85-87`).
- Not blocking: item 5 names the LLM call, the seat reply and the round barrier — all server-side and
  all bounded (see Traced). This loop is bounded in practice by the server's own bounded lifetime
  (`server.nim:267` `quit(0)` after `finishEpisode`) and matches the starter convention.

### N10 — `output_config.effort` is sent for non-Haiku models
- Where: `src/raid/llm.nim:185-188`: `if "haiku" notin client.model and "4-5" notin client.model:
  body["output_config"] = %*{"effort": "low"}`.
- Observed: the note says `max_tokens = 900`, **no `output_config.effort`** (Haiku 4.5 rejects it),
  `temperature = 0.4`. The code implements the Haiku carve-out but still sends the field for other
  models; the shipped default model is `claude-sonnet-5` (`src/raid/config.nim:46`, and the manifest
  `config_schema.model.default`), so the field *is* sent on the default Anthropic path.
- Not blocking: a request-shaping detail with a bounded failure mode (a 400 becomes a parse/transport
  fallback via `textOf` → `causeOf` → the scripted order); no checklist item names it.

---

## Traced and consistent

**Resolution rules (design §Resolution order, 19 steps).**
- `src/raid/sim.nim:367-486` `stepOnce` runs the note's 19 steps in the note's order, each labelled:
  clock/enrage (`:372-377`), control compile in seat order (`:379-383`), quantise-and-record with
  `clamp(±100)`, `clamp(±AimTurnRate)` and `action and 0x1F` (`:385-398`), aim then boss aim
  (`:400-405`), cog motion then add motion then unstick (`:407-412`), timers (`:414-416`),
  abilities (`:418-424`, see N2), retarget (`:426-428`), boss scheduling (`:430-433`), telegraph
  resolution then pools (`:435-437`), boss/add attacks (`:439-440`), deaths (`:442-466`), phase
  check (`:468-469`), keyframe (`:471-473`), end check (`:475-486`).
- End check order matches the note exactly: fault → `boss.hp <= 0` kill → `aliveCount() == 0` wipe →
  `tick >= maxTicks` enrage_timeout (`sim.nim:476-486`), with the tick incremented first so
  "`t + 1 == maxTicks`" is what fires.
- Boss numbers cross-checked against §The game: cone `±32` brads / 180 px / 48-tick fuse / 120 damage
  (`types.nim:93-96`), cadence `[192,192,168,144]` by phase (`:97`, used at `telegraphs.nim:92`),
  pour 90 px / 60 ticks / 80 damage / cadence `[240,240,216]` (`types.nim:100-104`), crucible 110 px /
  72 ticks / 168 cadence / 240 split (`:110-113`, `telegraphs.nim:104-119`), Spill cap 5
  (`telegraphs.nim:112`), Overload 96-tick cast / 480 cadence / 70 damage / 400 heal
  (`types.nim:116-119`, `boss.nim:167-187`), adds 220 hp / 2 per wave / 360 ticks / cap 8 / Feed at 4
  (`types.nim:121-129`, `boss.nim:77-106,162-165`), enrage triple + 24-tick melee
  (`boss.nim:191-193`, `state.nim:209-220`). Damage multiplier order is one integer expression,
  `base × feed × spill × enrage` truncated last (`state.nim:213-220`).
- Facing is frozen for the whole cleave telegraph (`boss.nim:19-30`, early-return on
  `cleaveLive()`); pours draw only living non-tanks (`telegraphs.nim:37-49`); pool bite every 24
  ticks and expiry at 240 with a cap of 6 that expires the oldest (`pools.nim:9-46`).

**The decision path.**
- One batch per turn: `llm.nim:269-283` builds a single `RequestBatch` over every open seat and calls
  `client.curl.makeRequests(batch, timeout)` once per attempt; there is no per-seat request loop.
  `curly`'s own contract confirms the positional pairing the code relies on —
  `/root/.nimby/pkgs/curly/src/curly.nim:711-719`: "The return value seq is in the same order as the
  request batch", so `responses[position]` ↔ `open[position]` ↔ `batch[position]` is correct. This
  is bullwhip's `decideAll` shape verbatim (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:437-470`).
- Tolerant parse: `orders.nim:13-48` `extractJsonObject` finds the first `{`, tracks string/escape
  state, returns the outermost balanced object, and falls back to the last `}` for a truncated reply;
  `parseOrder:134-160` accepts unknown enums (falling to the role default) and only raises on a
  missing/blank `intent`; `numberFrom:117-132` accepts numeric strings and rejects non-finite floats;
  `canonicalTarget:71-115` accepts `boss`/`SMELTER-9`, aliases case-insensitively, `A<n>`, an integer
  1–8 and 0.
- Exactly one retry: `llm.nim:269` `for attempt in 0 .. 1`, with `RetryHint` appended on the second
  pass (`:276-277`) and the retry deadline swapped in (`:281-282`).
- Fallback recorded: the except arm (`llm.nim:295-303`) installs the stalwart order with
  `source: osFallback`, `attempts: attempt+1`, `cause: causeOf(error.msg)` and a `runeCap`ped detail;
  `engine.nim:34-48` `noteFallback` increments the per-cause counter and emits a `fallback` event
  with `attempt`, `cause` and `detail`; `scoring.nim:75-79` writes `fallback_causes` per seat, so
  phase 60 can count them. `tests/test_orders.nim:165-186` asserts the event, the cause and the
  per-seat counters; `:150-163` asserts that only an unusable reply raises.
- Baseline env switch: `baselines.nim:57-64` `parseScriptKind` (`1/true/yes/stalwart/default` →
  stalwart, `greenhorn/green/novice` → greenhorn, else none), read from the register frame at
  `server.nim:382-390`, with "registered with neither field → stalwart" at `:388-390` and
  "never registered → stalwart + `COGAME_PLAYER_FAILURE_URI`" at `:217-235`.

**Every wait and its bound.**
- LLM attempt: `curly.makeRequests(batch, timeout)` where `timeout` is
  `deadlineSeconds(llmAttemptSeconds)` = 7 then `deadlineSeconds(llmRetrySeconds)` = 3
  (`llm.nim:133-134,281-283`; `config.nim:54-65`). `curly` sets `OPT_TIMEOUT` per easy handle
  (`curly.nim:290`), whole seconds — which is exactly what `deadlineSeconds` rounds up to.
- `config.validate` refuses a config whose **rounded** deadlines exceed `turnBudgetSeconds`
  (`config.nim:88-94`), asserted at `tests/test_engine.nim:198-217` (6.2 + 3.2 → refused).
- Player connect wait: bounded by `playerConnectTimeoutSeconds` (`server.nim:196-203`); register
  grace bounded at 3 s (`:205-215`).
- Done broadcast: `server.nim:129-149`, a cumulative `seats × 3.0 s` allowance, with a seat whose
  turn arrives after the allowance **skipped** — the bound is enforced, not merely logged.
- Budget guard: `engine.nim:87-99`, engages when `elapsed + 2 × turnBudget > wallClockBudget`, emits
  `budget_guard` once and drops every remaining turn to the scripted layer with `cause: fcBudget`.
- Engine hard stop: `engine.nim:113-118`, unconditional, checked on every 24th tick →
  `deadline/wall_clock`.
- Artifact writes: `server.nim:105` explicit 60 s on the POST path; the PUT path goes through
  `bitworld/runtime.writeCogameUri`, which uses `curly`'s pool `put` whose default timeout is 60 s
  (`/root/.nimby/pkgs/bitworld/src/bitworld/runtime.nim:208-218`, `curly.nim:664`). This closes r1's
  "unverifiable" note on `writeCogameUri`.
- Arithmetic: default variant `wallClockBudgetSeconds = 660 ≤ 720 = 0.6 × 1200`, enforced at config
  load (`config.nim:95-98`) and asserted for every variant and the cert fixture
  (`tests/test_manifest.nim:96-109`). `tests/test_engine.nim:160-196` drives a client that hangs to
  its full 10 s every turn and asserts the episode ends `complete`, inside the budget, having been
  queried at most once per turn.
- No unbounded loop in the step path: `runEncounter`'s `while not sim.done` advances `sim.tick` every
  iteration and `stepOnce` finishes at `maxTicks` (`sim.nim:485-486`).

**String truncation.**
- `labels.nim:49-57` `runeCap` = `utf8Only` (drops malformed bytes, `:31-47`) + newline flattening +
  `runeSubStr`. Every replay-bound string goes through it: `say`/`note` at parse and repair
  (`orders.nim:153-154`, `:247-248`), `policy` label (`server.nim:391`), fallback detail
  (`engine.nim:47`, `llm.nim:266,301`), fault detail (`engine.nim:122`), player names
  (`state.nim:119` via `sanitizeName`), and all four captured-error cuts in `llm.nim:204,212,217,226`.
  `extractJsonObject`'s own error quote is rune-cut too (`orders.nim:18-19`). The prompt cap uses
  `runeSubStr` directly (`server.nim:380-381`) and never reaches the replay.
- Tests: `tests/test_orders.nim:210-243` puts a 4-byte emoji astride the 400/300/300/160 caps and
  feeds an invalid-UTF-8 body; `:245-267` puts it at the 200th rune of `fallback.detail`, records it
  through `applyTurn`, serialises and re-parses; `tests/test_replay.nim:36-40` asserts the whole
  replay file is valid UTF-8 **before** parsing, with a non-ASCII `say` forced into the stream.

**The replay writer.**
- `replay.nim:81-101` emits every documented top-level key with `protocol: "raid.replay.v1"`,
  `format_version: 1`, the resolved config with tokens excluded (`config.nim:159-195`), the map spec
  verbatim, names/aliases/roles/policy_kinds/colors, the phase table, `controls_b64`, keyframes with
  `int64` digests (`:49`), the event array and the results document.
- `tests/test_replay.nim:43-78` asserts the key set, `controls_b64.len == tick_count × 5 × 4`, the
  legal `reason`/`end_rule` enums, five scores, and at least one of each of
  `encounter_start/order/telegraph/telegraph_resolve/phase_start/turn_start/end`.
- Write order at the end of an episode is replay **then** results (`server.nim:171-174`), with the
  reason at the call site; the `done` frames go out before both (`:164`).

**Re-derivation and the viewer.**
- `replay.nim:148-188` `rederive` rebuilds config+arena from the replay itself, re-installs the
  recorded `order` events per turn (`ordersFromEvents:111-146`) and re-runs `stepOnce`, so the
  control bytes are recompiled rather than replayed; `firstDigestMismatch:190-206` compares every
  recorded keyframe digest (`int64`, with the emscripten 32-bit `int` hazard called out at `:195-196`)
  and `controlsMatch:208-215` compares the decoded control stream byte for byte.
  `tests/test_replay.nim:82-86` asserts both; `:100-110` asserts a foreign protocol is rejected.
- The viewer displays the re-derived frames, not a parallel recording:
  `replay-viewer/raid_replay.nim:54-56` `rederive(payload, keyframeEvery = 1)` then
  `frames = rebuilt.keyframes`; the recorded keyframes are used only for the mismatch number
  (`:56`), surfaced as `raid_mismatch_tick` (`:103-104`) → `data-replay-mismatch-tick`
  (`static_replay.js:44-48`).
- Determinism guard: `tests/test_determinism.nim:73` greps `src/raid/*.nim` for float maths and
  `-ffast-math`; `:104-160` re-runs the same seed in-process and in a fresh instance and asserts a
  one-byte control change moves the digest; `:161` pins the committed golden fixture.

**The manifest (items 6, 10, 3, 12).**
- `num_agents = 5` in `variants[default].game_config`, `variants[sprint].game_config` and
  `certification.game_config`; `len(certification.players) == 5` and
  `len(certification.game_config.players) == 5` (read directly from
  `coworld_manifest_template.json`); asserted by `tests/test_manifest.nim:10-32`.
- `tools/ci/docker_smoke.sh:98-143` enforces all four seat-count invariants plus the independent
  `SMOKE_SEATS:-5` cross-check, each exiting with a `SEAT-COUNT FAIL:` prefix.
  `grep -c 'SEAT-COUNT FAIL'` over the full log of run 32621942459 → **0**; the smoke logged
  `game=raid seats=5 …` and `smoke OK: seats=5 results=1440B replay=47263B reason=complete`.
- `game.docs` = `readme` (text, 5327 chars) + two pages `rules.md` (15605) / `protocol.md` (15211),
  each `{"type":"text","value":…}`; `game.protocols` carries both `player` (2468) and `global`
  (1720), both text. `game.replay_viewer = {"bundle": "static-replay-viewer"}`;
  `episode_timeout_minutes = 20`. `results_schema.properties` has 35 keys equal to
  `scoring.resultsKeys()` and to what `resultsJson` emits (asserted by
  `tests/test_manifest.nim:34-54`); `reason`/`end_rule` enums are the closed three/six.
- `tools/build_replay_viewer.sh` and `tools/ci/docker_smoke.sh` are both mode `100755`
  (`git ls-files -s`). `coworld-release.yml` order: build manifest (`:153`) → certify (`:167`) →
  upload policies (`:206`) → upload coworld (`:304`) → secret put (`:342`).
  `tools/ci/policies.json` has four entries — `raid-anvil` (`PLAYER_PROMPT`), `raid-triage`
  (`PLAYER_PROMPT` + `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `raid-stalwart` and
  `raid-greenhorn` (`PLAYER_SCRIPTED`). The checklist's placeholder gate, run verbatim over the three
  workflows, `docker_smoke.sh` and `policies.json`: no match → exits 0.

**Two name spaces (item 4).** `seatView` (`broadcast.nim:64-159`) contains aliases only — no seed, no
other seat's `note`, no prompt text, no real name; `tests/test_view.nim:56+` greps a serialised view
for each of those. Real names live in `globalSnapshot` (`broadcast.nim:167`), `replay.names.players`
(`replay.nim:63-76`) and `results.names` (`scoring.nim:60`).

**Legibility (item 11).** `client/replay_broadcast.html:1556`
`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`
and `:1612` `@media (max-width: 640px)`; asserted statically by `tests/test_viewer.nim:50-64`.

**Item 1's second half.** `git log -p 501040d..HEAD -- tests/` removes exactly six lines: two
docstring/`done()` rewordings in `test_determinism.nim`, two never-read `FakeClient` fields
(`hangSeconds`, `attemptSeconds`) replaced by a real hung-client test, and two `import` lines that
were widened. No assertion deleted, no tolerance widened, no skip added, no test file removed. The
`test` job ran 17 files × 2 modes = 34 `nim r` invocations with `NIM_TESTS*` unset, and the log has
no `FAILED`.

---

## Could not determine

- **Whether the shipped bundle actually renders in a browser.** This is B1's subject: nothing in CI
  or in the sandbox executes `index.html`. I can read that the link flags and the worker bootstrap
  agree and that both markers are set from the shell's own paths, but the checklist rules that out as
  evidence. Settled by: `tools/ci/viewer_smoke.mjs` + the `Load the bundle in a real browser` step +
  `needs: docker-smoke` + the `smoke-replay` artifact, and one green run whose log shows the
  harness's `loaded: true`.
- **Whether the emsdk bundle build in run 32621942459 was a full compile.** The `wasm-viewer` job's
  "Build the static replay viewer bundle" step and the whole job completed in 2m04s
  (`06:03:46Z → 06:05:50Z`) with no docker layer cache configured, which is fast for
  `emscripten/emsdk:4.0.15` + `nimby sync` + a Nim wasm compile. The step is green and the later
  node harness did load a real `raid_replay.js`/`.wasm` (`WASM-SMOKE OK: 647 ticks`), so the artefact
  clearly exists; I simply did not read the step's own log line by line to confirm no layer was
  reused. Settled by reading the step log or the uploaded `static-replay-viewer` artifact's
  timestamps.
- **The real-world per-seat latency spread behind N7.** Only an episode with live credentials would
  show whether the batch-wide figure is materially different from per-seat times; the offline path
  records 0. Settled by a hosted episode's `order` events.
