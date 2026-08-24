# r1 review — cooperative-hunting

Repo: `/workspace/repos/cogame-cooperative-hunting` @ `10564b04a8e11a9ace404ca7ab5fe658564471f5`
Range: `0cf270d..10564b0` (8 commits; the repo was bootstrapped this run, so this is the whole tree)
Files read in full: 34 (all of `src/`, `replay-viewer/`, `tests/`, `tools/`, `client/replay_broadcast.html`,
`coworld_manifest_template.json`, the three workflows, `Dockerfile`, `Dockerfile.replay-viewer`,
`compose.yaml`) + the two starters' counterparts for diffing.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision rule)
Design note: `/workspace/coworld-builder/runs/2026-08-24-cooperative-hunting/design.md`
(byte-identical to the in-repo copy `docs/plans/2026-08-24-cooperative-hunting-design.md`)

External evidence used: CI run **32758098973** on `main` at the reviewed sha (`success`), its
`viewer-smoke` artifact (`viewer-smoke.json`, `viewer-smoke.png`) and its `smoke-replay` artifact
(`replay.json`, `results.json`).

---

## Blocking

### B1 — `ci.yml`'s viewer smoke step carries no `--strict-text-bounds`, and the repo's `viewer_smoke.mjs` predates the flag

- Where: `.github/workflows/ci.yml:312-316`; `tools/ci/viewer_smoke.mjs:114-141` (esp. `:136`);
  compare `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs:40,118-136,173,349-350,601-603`
- Observed:
  - The smoke invocation is
    ```
    node tools/ci/viewer_smoke.mjs \
      --bundle dist/static-replay-viewer \
      --replay "${replay}" \
      --timeout 90 \
      --soak 10
    ```
    (`ci.yml:312-316`). No `--strict-text-bounds`.
  - The committed `tools/ci/viewer_smoke.mjs` is **528 lines**; the coworld-builder template is
    **709 lines** (191 differing lines). The repo copy's `parseArgs` (`:114-141`) knows
    `--bundle --replay --url --timeout --soak --out --headed -h --help` and ends
    `default: die(2, `unknown argument: ${arg}`);` (`:136`) — passing `--strict-text-bounds` to this
    copy exits 2. There is no `fillText`/`strokeText` hook and no `canvas_text` key anywhere in the
    file (`grep -n "canvas_text\|strict-text-bounds\|fillText" tools/ci/viewer_smoke.mjs` → no match).
  - Confirmed downstream: the `viewer-smoke.json` artifact from run 32758098973 has keys
    `loaded, ms, url, bundle, replay, clock, scorebug, status, loading_text, feed_lines, signals,
    scrub, soak, failure, console_tail, screenshot` — **no `canvas_text`**.
  - The arena is fixed, not pannable: design note §Viewer "Zoom decision: dropped. The arena is a
    fixed 32×32 tile board that is always drawn in full, scaled to fit the frame; nothing is ever
    off-screen" (design.md:645-648), and `#viewpanel` and its wiring are absent from the page
    (verified: `client/replay_broadcast.html` contains no `id="viewpanel"`, `attachMinimap`,
    `zoomAt` or `setZoom`).
- Checklist item: 15 — "For a **fixed arena** … `never_inside` must be **0**, and `ci.yml`'s smoke
  step must carry `--strict-text-bounds` so a regression is red rather than merely logged."
- What the design note requires: §Packaging (design.md:775-776) — "`tools/ci/docker_smoke.sh`
  (mode 100755) and `tools/ci/viewer_smoke.mjs` (**verbatim, no substitutions**) copied from the same
  templates." The committed file is not the current template.
- Why blocking: the gate the checklist names does not exist in this repo — the flag cannot be passed
  and the number it gates is never computed. A text-bounds regression is invisible to CI.

### B2 — the viewer draws LLM-authored text and ships no worst-case renderer fixture; the CI replay carries zero LLM text

- Where: `client/replay_broadcast.html:1379-1393` (`pumpFeed`), `:966-981` (`#feed` CSS),
  `src/cooperative_hunting/replay.nim:135-144` (`feedLineFor` for `plan` → `"<alias>: <say>"`,
  for `fallback` → `"<alias> fell back to <baseline> — <cause>"`);
  `.github/workflows/ci.yml:200-336` (the whole `wasm-viewer` job)
- Observed:
  - `feedLineFor("plan", …)` renders the model's `say` verbatim into a feed line
    (`replay.nim:135-140`); the page appends it as a `.feed-row.say` div (`replay_broadcast.html:1387-1391`).
    So model-authored sentences reach the viewer.
  - `#feed` is a DOM element (`replay_broadcast.html:966-981`, `max-width: min(64%, calc(320*var(--u)))`,
    `align-items: flex-end`), not canvas text — so the template's `canvas_text` instrumentation would
    report `total: 0` for it even if B1 were fixed. The board itself is drawn by
    `BroadcastCore` inside an **OffscreenCanvas in a Worker** (`replay-viewer/static_replay.js:64-72`
    `canvas.transferControlToOffscreen()`, `static_replay_worker.js:83-103`), which the template
    header itself calls out as invisible to the check.
  - The CI replay provably carries no model text: `smoke-replay/replay.json` from run 32758098973
    contains **0 events with a `say` field** and `results.fallbacks == [1,1,0,0,0,0]`,
    `results.llm_requests == 0` — the two prompt seats fell back on the no-credentials path exactly
    once each and never spoke. So `pumpFeed`'s `say` and `fallback` rendering paths are exercised by
    nothing in CI.
  - There is no fixture step in `ci.yml`: the `wasm-viewer` job's steps are
    `checkout, setup-buildx, assert hook, assert smoke present, build bundle, assert bundle complete,
    download smoke replay, setup-node, install playwright, load the bundle, upload evidence, upload bundle`
    (confirmed against the job's step list for job id 97531314108 — all 13 steps `success`).
- Checklist item: 15, last bullet — "A repo whose viewer draws LLM-authored text must therefore ship a
  **worst-case renderer fixture** … Cite the step and its `canvas_text` line; a repo that draws model
  text and has no such fixture is a blocking `legibility` finding."
- Why blocking: the class of chrome that exists only to show what a model said (`#feed` say lines,
  the fallback line) is drawn by no replay CI can produce and measured by no gate. A full-cap
  120-rune remark on six seats at once is untested at any width.
- Note for the judge: the checklist's fixture text is framed around `client/renderer.js` and canvas
  text; here the model text is DOM-rendered. I am reporting the fact and the mapping, not asserting
  how the ambiguity resolves.

### B3 — the sum of the game's own configured waits exceeds 60 % of `episodeTimeoutSeconds`

- Where: `src/cooperative_hunting.nim:923-940` (roster), `:952` (registration grace), `:580-591`
  (deadline guard), `:1101-1105` (LLM thread join), `:1112` (shutdown grace);
  `src/cooperative_hunting/sim_types.nim:521-522` (defaults);
  `src/cooperative_hunting/llm.nim:597,612` (batch deadline × 2 attempts);
  `coworld_manifest_template.json:13` (`"episode_timeout_minutes": 20`)
- Observed, tracing the process lifetime bound-by-bound:
  1. `let rosterDeadline = getMonoTime() + initDuration(seconds = config.playerConnectTimeoutSeconds)`
     (`:923-924`), loop `while connected < config.numAgents and getMonoTime() < rosterDeadline`
     (`:928`). `playerConnectTimeoutSeconds` default **120** (`sim_types.nim:522`); no manifest
     variant and not `certification.game_config` set it (grep: the key appears only in
     `config_schema`, `coworld_manifest_template.json:139`). Bound: **120 s**.
  2. `sleep(500)` registration grace (`:952`). Bound: **0.5 s**.
  3. `ep.startedAt` is stamped at the end of `newEpisode` (`:405`); `advance` settles when
     `ep.episodeSeconds() >= float(ep.config.playBudgetSeconds)` (`:580-581`). `playBudgetSeconds`
     default **660** (`sim_types.nim:521`); no variant overrides it. Bound: **660 s**.
  4. `planRequests.send("quit"); joinThread(llmThread)` (`:1102-1103`). The worker may be inside
     `client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:612`) with
     `timeoutSeconds = planTimeoutSeconds = 12`, and the `for attempt in 0 .. 1` loop
     (`llm.nim:597`) can run it twice. Bound: **≈ 24 s**.
  5. `sleep(ShutdownGraceSeconds * 1000)` with `ShutdownGraceSeconds = 20` (`:32`, `:1112`).
     Bound: **20 s**.

  Worst case = 120 + 0.5 + 660 + 24 + 20 ≈ **824 s**, i.e. **68.7 %** of the declared
  `episode_timeout_minutes: 20` = 1200 s. Even with an instantaneous roster the tail is
  660 + 24 + 20 = 704 s, leaving 16 s of headroom.
- Measured counter-evidence (observed, not inferred): the docker-smoke episode on the certification
  fixture ran 17:42:49 → 17:45:20 = **151 s** wall (`smoke OK: seats=6 results=715B replay=355041B
  reason=complete`), and the manifest variants' natural end is 3000 ticks ÷ 8 Hz = 375 s
  (predator-prey 3040 ÷ 8 = 380 s), so the normal path is ≈ 400–425 s including the grace.
- Checklist item: 5 — "Every wait … has an explicit bound; the episode settles and scores inside
  **60 %** of `episodeTimeoutSeconds` (720 s of 1200)."
- What the design note says: §Decisions (design.md:277-281) — "3000 ticks ÷ 8 Hz = 375 s, plus **≤ 45 s
  roster wait**, 5 s of round cards already counted, and a 20 s shutdown grace = **≤ 442 s, which is
  37 % of the 1200 s `episodeTimeoutSeconds` and well inside the 60 % (720 s) rule**." No code path or
  config value produces a 45 s roster wait; the note's own `GameConfig` block
  (design.md:463) states `player_connect_timeout_seconds: int = 120`, which is what the code uses.
  The note's arithmetic also omits the 660 s deadline guard and the LLM-thread join.
- Why blocking: as configured, the worst case violates the 60 % rule the item names. Every step is
  individually bounded (there is no unbounded wait in the game process — see "Traced and consistent"),
  so this is a budget question, not a hang.
- Label: the 824 s figure is an **inference** from the code's declared bounds. The 151 s figure is
  **observed** from CI.

### B4 — no test asserts frame-by-frame reproduction; the viewer restores recorded state rather than replaying events through the sim

- Where: `src/cooperative_hunting/replay.nim:486-570` (`applyTick`);
  `replay-viewer/cooperative_hunting_replay.nim:97-126` (`renderCurrent`), `:147-148`, `:207-210`;
  `tests/test_replay_parse.nim:123-147`
- Observed:
  - `applyTick` **assigns** the recorded arrays back into a `SimServer`:
    `sim.players[i].tileX = row[0].getInt()` … `.energy = row[3]` … `.score = row[4]`, flags decoded at
    `:515-520`; `sim.prey/items/berries` are `setLen(0)` and rebuilt from `frame.q` (`:527-558`);
    `sim.corpses` from `frame.c` (`:560-568`); then `sim.restampSides()` (`:570`). `sim.step()` is
    never called anywhere in `replay.nim` or `replay-viewer/`.
  - The display half **is** the game's own code: `renderCurrent` calls
    `packet = game.buildGlobalFrame(label, viewer, nextViewer)`
    (`cooperative_hunting_replay.nim:125`) — the same proc the live server calls at
    `src/cooperative_hunting.nim:1032`. There is no parallel recording of sprites.
  - The module says so outright: `chMismatchTick` returns `-1` with the comment "The replay is
    recorded state, not recorded inputs, so there is no hash to mismatch."
    (`cooperative_hunting_replay.nim:207-210`).
  - The only test in this area (`test_replay_parse.nim:123-147`, block `viewerReDerivesFrames`)
    asserts `parsedDoc.ticks.len == doc["ticks"].len` and that every 17th re-derived packet is
    non-empty (`probes > 0 and smallest > 0`). Nothing compares a re-derived per-tick state against
    the recorded one, and `test_step.nim:233-252` asserts a different property (two runs from the
    same seed and input script produce the same `stateDigest`).
- Checklist item: 2 — "Replaying the recorded events through the sim reproduces the recorded per-tick
  state **frame by frame**, and the viewer derives its display from that same re-derivation — not from
  a parallel recording. **A test asserts it.**"
- What the design note says: §Viewer (design.md:621-625) — "for each frame the module rebuilds the
  tick's `SimServer` state from `ticks[i]` and calls the **same `buildGlobalFrame` the live server
  uses**"; §Tests item 6 (design.md:815) asks only for "re-feeding each tick through the replay
  renderer yields a non-empty sprite packet". The note therefore specifies exactly what the code does.
- Why blocking: the second clause of item 2 is satisfied (display comes from the game's own frame
  builder, not a parallel recording); the first clause and the "a test asserts it" clause are not.
  This is a design-note-vs-checklist tension, and the checklist is the named authority for "blocking".

---

## Non-blocking

### N1 — `sim.captureRule` is set and asserted but never read by capture resolution
- Where: `src/cooperative_hunting/sim.nim:407` (`sim.captureRule = captureRuleFor(...)`);
  `sim.nim:888-960` (`applyAnimalCaptures` / `applyItemCaptures`); `tests/test_capture.nim:94,171`
- Observed: resolution dispatches on entity kind (`PreyKind` → `isCapturedBySides`; `ItemKind` →
  iron/gold/level-sum), never on `sim.captureRule`. `grep -rn "captureRule" src/` shows assignments
  and the enum only. `sim.windowTicks` **is** read (`sim.nim:783`).
- What the note says: design.md:161-165 step 6 — "evaluate the variant predicate
  (`sides` | `window` | `levelsum`) over the occupied sides". Functionally equivalent because the
  variant determines which entity types exist, but the enum is inert.

### N2 — four byte-boundary slices in `parsePlan` (none of them reaches the replay)
- Where: `src/cooperative_hunting/llm.nim:476` (`intent[0 ..< MaxIntentChars]`), `:481` (`side`),
  `:494` (`with` entry), `:503` (`target`)
- Observed: these are byte slices, not `runeCap`. Traced each: `intent` is then coerced to
  `LegalIntents` or `"hunt"` (`:477`); `side` to `N/S/E/W` or `"any"` (`:483-485`); a `with` entry is
  kept only `if name in aliases` (`:495`); `target` raises unless `target in legal` (`:506-507`).
  A byte-cut value therefore never survives into a `Plan` and never reaches the replay. Every string
  that *does* reach the replay goes through `runeCap` / `cleanText` — see "Traced and consistent".

### N3 — `chrome_common.js` is loaded but never instantiated; the page reimplements the transport
- Where: `client/replay_broadcast.html:1231` (`need('chrome_common.js', 'ChromeCommon')`),
  `:1404-1435` (`pushHuntBeat`/`buildBeats`/`gateBeats`), `:1488-1551` (`buildSpeedChips`/`wireTransport`),
  `:1356-1369` (`updateClock`); compare `/workspace/starters/coworld-ctf/client/replay_broadcast.html:1614-1618`
  (`if (!window.ChromeCommon) {…} var C = window.ChromeCommon({…})`)
- Observed: the only three occurrences of the string `ChromeCommon` in the page are the `need(...)`
  guard and two comments (`:1256`, `:1405`). `window.ChromeCommon(...)` is never called. Beats are
  built by the page's own `pushHuntBeat`, not `chrome_common.markBeat(tick, kind, team, label)`.
  Consequence: `#momentum`, `#lulls` and `#scrub-win` are resolved by nothing and stay empty (only
  `#win-chip` is written, at `:1471`); the momentum graph and lull spans never render.
- Checklist item 14(d) is nonetheless met in substance: beats are labelled `<button>`s
  (`:1409-1414`, `mark.textContent = label`, `aria-label` at `:1415`) that seek to their tick
  (`:1416-1419` → `seekTo`), and every emitted kind has CSS (`:1081-1085`:
  `.beat-marker.round/.bigcatch/.smallcatch/.tag/.end`), matching
  `frames.nim:522 LegalBeatKinds` exactly.
- Note says (design.md:629-634) chrome_common "owns the clock, the transport bar, the scrubber, beat
  markers, lull spans and the spoiler toggle". In the shipped page it owns none of them.

### N4 — `relayout()` is not the starter's
- Where: `client/replay_broadcast.html:1600-1626`; compare
  `/workspace/starters/coworld-ctf/client/replay_broadcast.html:4110-4160`
- Observed: ours sets `--hudscale`, `--band`, `--topband` on `document.documentElement` and re-arms
  itself with `requestAnimationFrame(relayout)` (`:1624`). The starter's version runs a 4-pass
  fixed-point band iteration, sizes `#stage.style.width/height` in px to the board aspect, and is
  driven by a `ResizeObserver` + `resize` listener. Ours never sets `#stage`'s size, so
  `#stage { width: 100%; height: 100% }` (`:69-79`, the starter's CSS, unmodified) stands and the
  fixed-aspect letterbox is delegated to `core.setViewportFit()` (`:1621-1623`).
- Checklist 14(a) is met: `relayout()` measures `#transport` (`:1610-1611`) and sets `--band` and
  `--hudscale` on `document.documentElement` (`:1605-1611`). The note (design.md:653-654) says the
  variables are set "by the starter's `relayout()`" — the function is a rewrite, not the starter's.

### N5 — the scorebug ellipsizes names and clips score digits at 1280 px
- Where: `client/replay_broadcast.html:1015` (`.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow:
  hidden; text-overflow: ellipsis; white-space: nowrap; }`), `:989` (`#scorebug .plates { flex-direction:
  row; flex-wrap: wrap; …; overflow: hidden; }`), `:993-1002` (`.hplate { … min-width: 0; flex: 1 1 0 }`)
- Observed, from `viewer-smoke.png` (run 32758098973, 1280×800): all six plates render their policy
  name truncated — `Cog-B coo…`, `Cog-C coo…`, `Cog-A big …`, `Cog-E big …`, `Cog-D side…`,
  `Cog-F mo…`. The `.plate-score` of the fifth plate is sliced on its left edge by the sixth plate's
  colour chip, and the sixth plate's score is sliced by the right frame edge. The `viewer-smoke.json`
  `scorebug` string confirms the underlying text is full (`"Cog-B cooperative-hunting-prompt 0 …"`).
- Checklist item 11 is met literally: the exact rule `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`
  is present (`:1015`) and `@media (max-width: 640px)` hides labels (`:1103-1104`,
  `#speedchips .chip-label, .tbtn .label { display: none !important; }`).
- The note (design.md:666-668) says names "otherwise collapse to '…'" at ~360 px and the rule is there
  to prevent it. At 1280 px they collapse anyway. I could not test 360 px here (no browser).

### N6 — the 4 KB chrome label will drop early beats on a manifest-length episode
- Where: `src/cooperative_hunting/frames.nim:585-603` (trim loop), `sim_types.nim:195`
  (`MaxChromeLabelBytes = 4096`); `client/replay_broadcast.html:1424-1428` (`buildBeats` latches once)
- Observed: the trim loop drops feed lines from the front first, then **beats from the front**
  (`frames.nim:594-600`), so it is the *earliest* beats that go. Each beat serialises as
  `{"t":1234,"k":"smallcatch"}` ≈ 28 bytes. Measured on the CI replay: **44 beats in 1040 ticks**
  (37 smallcatch, 4 round, 2 bigcatch, 1 end) ≈ 0.042 beats/tick. A staghunt manifest variant is
  3000 ticks → **≈ 127 beats ≈ 3.6 kB**, plus the seats block (6 × ≈ 110 B ≈ 660 B) and the clock —
  over 4096. (Inference from the measured rate; not observed at full length.)
- The note (design.md:538-540) says "`beats` is shipped **complete on the first frame**". The page
  latches whatever the first non-empty `beats` array carries (`beatsBuilt` guard, `:1425-1426`).

### N7 — `certification.game_config` carries no `tokens`
- Where: `coworld_manifest_template.json:558-600`
- Observed: `certification.game_config` = `{players[6], num_agents: 6, variant, rounds: 2,
  ticksPerRound: 480, tickHz: 8, seed}`. No `tokens` key.
- The note (design.md:728-731) specifies `tokens: [six]` in the fixture. Checklist item 6's four
  invariants are all satisfied regardless, and `tools/ci/docker_smoke.sh` injects its own tokens (the
  smoke log shows `config={… "tokens": ["token-0" … "token-5"]}`).

### N8 — `turnsTotal` is 24, the note says 25
- Where: `src/cooperative_hunting.nim:382-383`
  (`(config.rounds * config.ticksPerRound) div max(1, config.planIntervalTicks)` = 2880 ÷ 120 = 24)
- The note (design.md:281-282) says "25 planning turns per episode". The value is only printed in the
  observation header (`llm.nim:291`, `TURN n/24`).

### N9 — the observation has no 2000-character cap
- Where: `src/cooperative_hunting/llm.nim:277-409`; `tests/test_llm_reply.nim:173-174`
- Observed: every list is bounded (party ≤ 5 lines `:307`, animals ≤ 12 `:371-372`, legal targets ≤ 12+`none`
  `:257-259`, blocked tiles ≤ 40 `:385`, recent ≤ 5 `:405`, strategy `runeCap(prompt, 1200)` `:409`),
  but the assembled string is never capped. The test asserts `observation.runeLen < 4000`.
- The note (design.md:308) says "the observation, deterministic, **≤ 2000 characters**, every list
  bounded".

### N10 — no test exercises the two-attempt retry loop
- Where: `tests/test_llm_reply.nim:78-91` (block `retryContract`)
- Observed: the block asserts the contents of the `RetryHint` string constant and that the
  `FallbackCause` enum contains all five causes. `runPlanBatch`'s `for attempt in 0 .. 1` loop
  (`llm.nim:597-633`) is never driven with a stub transport, so "exactly one retry, then fallback"
  is verified by reading, not by a test. `test_llm_reply.nim:70-76` does assert that an out-of-set
  target raises with `"LEGAL TARGETS"` in the message, which is what routes to the retry.
- The note (design.md:817-818) asks for "a `target` outside `LEGAL TARGETS` triggering exactly one
  retry and then the fallback".

### N11 — the player binary makes an unbounded blocking read
- Where: `src/cooperative_hunting_player.nim:290` (`let first = ws.receiveMessage(-1)`)
- Observed: whisky's `receiveMessage(timeout = -1)` blocks on `receiveFrame(-1)` and only returns
  `none` on `TimeoutError` (`vendored-whisky/whisky.nim:73-78`), so `-1` waits indefinitely. This is
  inherited verbatim from the starter (`coworld-staghunt/players/rabbiteer/rabbiteer.nim:587`).
  It is bounded in practice by the game's exit: a close frame raises, the `except CatchableError`
  at `:323-327` prints and `quit(0)`. CI confirms it works — "all 6 player containers exited 0"
  in the docker-smoke log. The connect loop is separately bounded
  (`MaxConnectAttempts = 240` × 250 ms = 60 s, `:26`, `:328-333`).
- Checklist item 5 speaks of "the episode" and the game's waits; the game process itself has no
  unbounded wait (see "Traced and consistent"). Recording the player-side read for completeness.

### N12 — `PLAYER_FALLBACK_SCRIPTED` overrides `PLAYER_SCRIPTED`
- Where: `src/cooperative_hunting_player.nim:48-58`
- Observed: `result.baseline = if fallback.len > 0: parseBaselineKind(fallback) elif scripted.len > 0:
  parseBaselineKind(scripted) else: bkBigGameHunter`. A seat with both env vars set plays the
  *fallback* name. `tools/ci/policies.json` and the manifest's `player[]` never set
  `PLAYER_FALLBACK_SCRIPTED`, so this is unreachable in the shipped configuration.
- The note (design.md:366-367) describes `PLAYER_FALLBACK_SCRIPTED` as "what a prompt seat plays
  between plans", not as an override for a scripted seat.

### N13 — `#bannerlane` was removed from the markup but is not on the note's removal list
- Where: `tools/build_replay_page.py:686` (`body.replace('    <div id="bannerlane"></div>\n', "")`);
  `client/replay_broadcast.html:431-459` (the starter's "3. BANNER LANE" CSS section, retained)
- Observed: the element is gone from the body; its CSS (`#bannerlane`, `.banner-chip` and variants)
  survives as dead rules. The note's removal list (design.md:638-644) names `#fpv*`, `#lockerroom`/
  `#lk-*`, `#killfeed`, `#povBadge`, `#mmwarn` and the `#viewpanel` group — not `#bannerlane`.
  Similarly, the `lk-*` keyframes survive as dead CSS (`client/replay_broadcast.html:915-931`).

### N13b — the starter's own beat-marker kinds survive as dead CSS
- Where: `client/replay_broadcast.html:583-598` (`.beat-marker.kill`, `.steal`, `.steal::after`,
  `.return`, `.capture`)
- Observed: these are ctf kinds this game never emits (`frames.nim:522 LegalBeatKinds` and
  `replay.nim:156-169` between them can only produce `round, bigcatch, smallcatch, tag, end`). Harmless
  — checklist 14(d)'s failure mode is the reverse (a kind with no rule); recording it because a grep
  for `.beat-marker.` returns nine kinds, not five.

### N14 — a planning turn skipped because a batch is still in flight is recorded nowhere
- Where: `src/cooperative_hunting.nim:417-421` (`if not ep.llmEnabled or ep.batchInFlight: return`)
- Observed: when the previous batch has not returned by the next 120-tick boundary, `dispatchPlanBatch`
  returns without incrementing `ep.turn`, without logging a `fallback` event, and without touching
  `ep.seats[].fallbacks`. Seats keep their previous plan — which is what the note's
  "the sim does **not** wait for it" (design.md:275-277) prescribes — but phase 60 sees no trace.
  The note's degrade table (design.md:391-401) has no row for this case. `rate_budget` skips *are*
  recorded, via `runPlanBatch`'s `fcRateBudget` → `pollPlanBatch` → `fallback` event
  (`llm.nim:591-594`, `cooperative_hunting.nim:505-523`).

### N15 — `configNode` omits two resolved `GameConfig` fields
- Where: `src/cooperative_hunting/replay.nim:175-194`
- Observed: `config` in the replay carries 13 keys; `closedRoster` and `focusElephant`
  (`sim_types.nim:278-279`) are not among them.
- The note (design.md:553) says `"config":{ ...every resolved GameConfig field, defaults expanded... }`.

### N16 — the manifest's variant/cert `players[]` display names are the in-game aliases
- Where: `coworld_manifest_template.json:426-441` and every variant / `certification.game_config`
- Observed: all four variants and the fixture list `[{"name":"Cog-A"} … {"name":"Cog-F"}]`. The seat's
  real name comes from `?name=` and overrides these (`src/cooperative_hunting.nim:968-970`), and the
  in-game alias is an independent seeded permutation (`sim.nim:425-435`), so a display name "Cog-A"
  need not be the seat whose alias is `Cog-A`. In the CI replay the `?name=` path won and
  `seats[].name` reads `cooperative-hunting-prompt` / `big_game_hunter` / `sidekick` / `modeler`.

### N17 — the literal string `/client/replay` exists in `client/broadcast_core.js`
- Where: `client/broadcast_core.js:196` (`['/client/replay', '/replay']`)
- Observed: this is inside the starter's live-websocket route-derivation table. The file is
  **byte-identical** to `/workspace/starters/coworld-ctf/client/broadcast_core.js`
  (md5 `677fe90f2be107b810c24aef02b936a3` both sides), which checklist item 14 requires. No such route
  exists on the server: `src/cooperative_hunting.nim:689-696` (`isStaticRoute`) serves only
  `PlayerClientRoute`, `PlayerClientHtmlRoute`, `GlobalClientRoute`, `GlobalClientHtmlRoute`,
  `SnappyClientRoute`, `SnappyClientPath`, and `runReplayServer` does not exist in the tree
  (`grep -rn runReplayServer src/` → comments only). Recording it because checklist item 3 says
  "No `/client/replay` pod path anywhere" and a grep will hit this line.

### N18 — the play/pause button label is inverted
- Where: `client/replay_broadcast.html:1507-1510`
- Observed: `core.setPlaying(!core.isPlaying()); byId('btn-play').textContent = core.isPlaying() ? '▶' : '❚❚';`
  — after switching to *playing* it shows `▶` (the "play" glyph) and after pausing it shows `❚❚`.
  The initial markup is `▶` (`:1173`) while `static_replay.js:58` starts with `playing = true`.

### N19 — the 0 % scrub probe returned the same clock as the pre-scrub read
- Where: `viewer-smoke.json` (run 32758098973) `scrub[0] = {"at":"0%","clock":"ROUND 1 OF 2 STAG HUNT · 244 / 960"}`,
  identical to the top-level `clock` field; 50 % and 100 % differ
  (`498 / 960`, `960 / 960`). `client/replay_broadcast.html:1529-1535` (`#scrub` click → `seekTo`),
  `replay-viewer/static_replay.js:197-200` (`seek` posts to the worker), `static_replay_worker.js:157-168`.
- Observed only. The smoke's three-distinct-clocks assertion passed. Whether the 0 % click seeks and
  the probe read before the worker round-trip completed, or the click landed off-track, cannot be
  settled from the artifact.

### N20 — `RECENT` lines are concatenated on one line
- Where: `src/cooperative_hunting/llm.nim:401-407`
- Observed: `result.add("RECENT (<=5 lines):")` then, for each line, `result.add("  " & line)` with no
  `\n` between entries; a single `"\n"` is added after the loop. The note's example
  (design.md:323) shows them space-separated on one line too, so this matches the note; recording it
  because the header says "<=5 lines".

---

## Traced and consistent

**Checklist 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-cooperative-hunting --branch main -w ci.yml` → run **32758098973**,
  conclusion **success**, on `main`, for commit "viewer: drop the starter's dangling rajdhani @font-face"
  = the reviewed sha `10564b0`. Jobs: `test` ✓ 2m38s, `docker-smoke` ✓ 3m38s, `wasm-viewer` ✓ 2m39s.
- `git log -p -- tests/` — every hunk is an addition. `tests/test_capture.nim` (+249) in `96584bb`;
  the other seven files (+1397) in `f232f19`. `git log -p -- tests/ | grep -E "^-[^-]"` returns
  nothing: no deleted assertion, no widened tolerance, no `skip`, no removed file.
- `ci.yml:104-150` runs every `tests/*.nim` twice (debug and `-d:release`) and fails the job on any
  non-zero exit; `NIM_TESTS*` repo variables are unset (the default `ls tests/*.nim` path is taken).

**Checklist 3 — static viewer.**
- `coworld_manifest_template.json:31-33` — `"replay_viewer": {"bundle": "static-replay-viewer"}`
  under `game`, the same placement as the starter's `coworld_manifest_paintbot.json`.
- `tools/build_replay_viewer.sh` exists, mode **100755** (`git ls-files -s` → `100755 452f2f9…`), and
  is asserted present + `-x` and invoked **by path** in `ci.yml:225-249`.
- The viewer's only network egress is `fetch(message.replayUrl, {credentials:'omit', mode:'cors'})`
  (`static_replay_worker.js:111-114`) where `replayUrl` comes from the `?replay=` query param
  (`static_replay.js:153`); everything else is `importScripts('./broadcast_core.js',
  './cooperative_hunting_replay.js')` (`:217`) and `new Worker(new URL('./static_replay_worker.js', …))`
  (`static_replay.js:12,161`). No other `fetch`/`XMLHttpRequest`/`WebSocket` in the bundle files.
- `runReplayServer` and any `/client/replay` route are absent from `src/` (see N17 for the one
  surviving literal, inside the byte-identical starter file).

**Checklist 4 — both name spaces.**
- Agents see aliases only: `buildPlayerFrame` (`frames.nim:457-490`) emits terrain / corpses / berries /
  items / prey / indicators / player sprites / HUD digits and an identity packet — no name string, and
  no `ChromeSpriteId`. The `0x91` plan body carries `intent/target/side/with/say/src` with `with`
  filtered to aliases (`cooperative_hunting.nim:525-542`, `llm.nim:487-496`). The observation prints
  `me.alias` and other seats' aliases (`llm.nim:294,311`).
- The viewer maps alias → real name: `chromeSeatNode` carries both `alias` and `name`
  (`frames.nim:529-541`); the page renders `.plate-alias` + `.plate-name`
  (`replay_broadcast.html:1297-1306`) and the endcard row the same way (`:1456-1463`). Confirmed live
  in `viewer-smoke.json`: `"Cog-B cooperative-hunting-prompt 0 Cog-C cooperative-hunting-prompt 8 …"`.
- `results.names` / `results.aliases` are both present and distinct
  (`cooperative_hunting.nim:316-318`; asserted in `tests/test_scoring.nim:226-234`).

**Checklist 5 — no unbounded wait in the game process.** Every wait traced:
`rosterDeadline` (`cooperative_hunting.nim:923-940`), `sleep(500)` (`:952`),
`planReplies.tryRecv()` — non-blocking (`:461-463`), `advance`'s wall-clock guard (`:580-591`),
per-tick `sleep(frameDuration - elapsed)` (`:1093-1096`), `joinThread` after `send("quit")`
(`:1102-1103`), `sleep(ShutdownGraceSeconds*1000)` (`:1112`), and the `no_players` path
(`:943-948`, writes zero-score results and `quit(0)`). The LLM lives on its own thread
(`:133-188`) with `curly.makeRequests(batch, timeoutSeconds)` (`llm.nim:612`); the sim only polls.
The budget arithmetic is B3.

**Checklist 6 — `num_agents`.**
- Present and `6` in all four variants (`coworld_manifest_template.json:450, 483, 516, 549`) and in
  `certification.game_config` (`:580`). `len(certification.players) == 6`
  (`pack-caller, pack-caller, big-game-hunter, big-game-hunter, sidekick, modeler` — every declared
  runnable occupies at least one slot) and `len(certification.game_config.players) == 6`.
- `tools/ci/docker_smoke.sh` is the coworld-builder template with only the three substitutions
  (`:5, 20-25, 49-50, 54`) plus an appended per-player exit-0 check (`:243-272`) that the note
  requires (design.md:828-829). The four seat-count invariants and their `SEAT-COUNT FAIL:` prefix
  are at `:113, 123, 131, 138, 148`. Mode **100755** (`git ls-files -s` → `100755 cef97b6…`).
- **`grep -c "SEAT-COUNT FAIL" docker-smoke.log` → 0** for job 97530210532. The log carries
  `game=cooperative_hunting seats=6 config={… "num_agents": 6 …}` and
  `smoke OK: seats=6 results=715B replay=355041B reason=complete`.

**Checklist 7 — scripted baseline plays full episodes legally.**
- `tests/test_episode.nim:21-82` runs a 6-seat all-scripted episode to the natural end and asserts
  `outcome.reason == erComplete`, `results["reason"] == "complete"`, both artifacts written, and
  `replay["ticks"].len == rounds * (ticksPerRound + RoundEndDisplayTicks)`.
  `:84-105` repeats it for all four variants.
- `tests/test_baseline_orders.nim:96-125` drives all eight baselines for 2000 ticks (600 in the other
  three variants) and asserts ≤ 1 direction bit per mask, no undefined bit and `<= 0x7f`, ≤ 1 mask per
  tick, never a move it could not pay for, and that each bot moved at least once.
  `:127-150` asserts every `0x90` body is ≤ 4096 bytes, valid UTF-8 and valid JSON.
- The mask is clamped in code too: `decideMask` keeps only the first of
  `[ButtonUp, ButtonDown, ButtonLeft, ButtonRight]` (`baselines.nim:1412-1420`).
- On tuning: design.md:360-364 and §Out of scope 7 (design.md:875-877) state the baselines are
  staghunt's own code carried over unchanged and explicitly not retuned in v1; `.claude/skills/
  stag-hunt-balance/` and `balance_sweep.sh` come along and CI does not run them. I found no grid
  harness in this repo — see "Could not determine".

**Checklist 8 — LLM reply handling.**
- Tolerant extraction: `extractJsonObject` (`llm.nim:422-456`) walks the text tracking string state
  and escapes and returns the first balanced `{…}` span; tested against clean JSON, trailing prose,
  leading prose + a ```json fence, and a `}` inside a string (`test_llm_reply.nim:22-48`).
- Exactly one retry: `for attempt in 0 .. 1` (`llm.nim:597`); attempt 1 re-issues only the seats in
  `stillOpen` with `RetryHint` appended (`:606-608`, `:613-633`). Seats still failing come back with
  `ok == false` and a cause.
- Fallback recorded: `pollPlanBatch` (`cooperative_hunting.nim:505-523`) sets `src = "fallback:<cause>"`,
  `target = "none"`, increments `ep.seats[index].fallbacks`, and logs a `fallback` event with
  `{alias, baseline, cause}`. `results.fallbacks` is a per-seat array (`:322`). The player's
  `decideWithPlan` falls through to the scripted baseline when `plan.target == "none"`
  (`cooperative_hunting_player.nim:164-170`).
- Observed live: `smoke-replay/results.json` → `fallbacks: [1,1,0,0,0,0]`, `llm_requests: 0` — the two
  prompt seats fell back once each on the no-credentials path and no network call was made, and the
  episode still ended `complete`. That is exactly design.md:397.
- Both causes are enumerated: `FallbackCause` = `timeout, parse, illegal_target, rate_budget,
  no_credentials` (`llm.nim:56-62`), asserted at `test_llm_reply.nim:85-91`.
- **Simultaneous-decision rule:** all prompt seats go out in ONE `curly.makeRequests` batch per turn —
  `var batch: RequestBatch; for index in open: … batch.post(...)` then a single
  `client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:604-612`). There is no per-seat
  sequential call anywhere. Dispatch is once per `planIntervalTicks` boundary
  (`cooperative_hunting.nim:1020-1022`).

**Checklist 9 — rune-safe truncation.**
- One helper: `runeCap` = `text.runeSubStr(0, limit)` after a `runeLen` check
  (`sim_types.nim:434-443`); `cleanText` = `sanitizeLine` then `runeCap(result, limit-1) & "…"`
  (`llm.nim:458-463`).
- Applied to every string that reaches the replay or a sprite label: `say`/`note`
  (`llm.nim:498-499`), the registered prompt (`cooperative_hunting.nim:801`,
  `cooperative_hunting_player.nim:58`), the `?name=` policy name (`cooperative_hunting.nim:769`),
  `config.players[]` (`:122`), `Player.name` (`sim.nim:184`), replay seat `alias`/`name`
  (`replay.nim:228-229`), replay `config.players` (`replay.nim:179`), chrome seat `alias`/`name`
  (`frames.nim:532-533`), chrome feed text (`frames.nim:568`), captured error strings
  (`llm.nim:623`, `:453-454`).
- Test: `tests/test_replay_parse.nim:84-121` builds `"x"*119 + U+1F98C + "tail"`, caps it, and asserts
  `capped.runeLen == 120`, `validateUtf8(capped) == -1`, `capped.endsWith("\u{1F98C}")`, then writes it
  through the real writer and asserts the whole document is still `validateUtf8 == -1`, still parses,
  and round-trips the rune. `:65-81` asserts no `note` ever reaches the replay and every `say` is
  within 120 runes. `test_llm_reply.nim:101-115` caps 400 4-byte runes and 500 2-byte runes.

**Checklist 10 — manifest validates.**
- `game.docs` = `{"readme": {"type":"text","value":…}, "pages":[…]}` with four pages, each
  `{id, title, content:{type,value}}`: `rules.md`, `variants.md`, `protocol.md`, `policies.md`
  (`coworld_manifest_template.json:325-423`).
- `game.protocols` carries **both** `player` and `global`, each a `{"type":"text","value":…}` object,
  not a bare string (`:315-324`).
- `$schema` set (`:2`), 8 tags including the four the note names (`:3-12`),
  `episode_timeout_minutes: 20` top-level (`:13`), `game.runnable.type: "game"`,
  `image: "{{COOPERATIVE_HUNTING_IMAGE}}"` — derived from the compose service name
  `cooperative_hunting` (`compose.yaml:2`) — and
  `env.ANTHROPIC_API_KEY_URI = "secret://coworld/cooperative-hunting/anthropic_api_key"`.
- `game.config_schema` is a real 2020-12 schema with `minItems: 6` / `maxItems: 6` on **both** array
  properties (`tokens` and `players`) and `num_agents` pinned `minimum: maximum: 6`.
- Reproducible: `python3 tools/build_manifest.py` regenerates the committed template exactly
  (I ran it; JSON-normalised diff is empty).

**Checklist 12 — release order and scaffold.**
- `coworld-release.yml` step order: "Build the Coworld manifest" (`:153`) → "Certify locally" (`:167`)
  → "Upload the policies" (`:206`, with the comment "BEFORE upload-coworld") → "Upload the Coworld"
  (`:304`) → "Put the Coworld secret" (`:342`, "AFTER upload-coworld"). All three workflows present:
  `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`.
- `tools/ci/docker_smoke.sh` present, mode 100755 (above). `tools/ci/policies.json` has **four**
  distinct policies: `cooperative-hunting-pack-caller` (`PLAYER_PROMPT` + `USE_BEDROCK`),
  `cooperative-hunting-quartermaster` (`PLAYER_PROMPT` + `USE_BEDROCK`, and
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` — champion #2, the second `PLAYER_PROMPT`
  entry), plus `cooperative-hunting-biggame` (`PLAYER_SCRIPTED: big_game_hunter`) and
  `cooperative-hunting-sidekick` (`PLAYER_SCRIPTED: sidekick`). Both champions are prompt policies.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`, `coworld-release.yml`,
  `coworld-submit.yml`, `tools/ci/docker_smoke.sh`, `tools/ci/policies.json` → **no matches**
  (gate exits 0).

**Checklist 13 — viewer executes.**
- `wasm-viewer` declares `needs: docker-smoke` (`ci.yml:212`) and downloads its `smoke-replay`
  artifact (`:277-281`), so the bundle is run against the replay this repo's own container produced.
- The `Load the bundle in a real browser` step **ran and succeeded** — job 97531314108, step 11 of 13,
  conclusion `success`; not commented out, no `continue-on-error`.
- `viewer-smoke.json` shows `"loaded": true`, `"ms": 288`,
  `signals.data_replay_loaded == "true"`, `signals.data_replay_error == null`,
  `bridge: ["loading","ready"]`, `soak: {seconds: 10, moved: true, page_errors: []}` with the clock
  advancing `4 → 196 → 244`, and three distinct scrub clocks.
- Both markers come from the shell's own code: `data-replay-loaded` at
  `static_replay.js:124` inside the `message.type === 'loaded'` branch, with `tell('ready')` posted
  from **inside** that branch immediately after (`:131`) — delta (b) of the note;
  `data-replay-error` at `static_replay.js:44` inside `showFailure` — delta (a). Both deltas are
  present and are the only two.
- **Link flags and bootstrap are the same starter's, and they agree.** `replay-viewer/config.nims:39-51`
  emits `-o …/cooperative_hunting_replay.js` with `-s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1
  -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node -s EXPORTED_RUNTIME_METHODS=HEAPU8` and an
  `EXPORTED_FUNCTIONS` list — and **no `MODULARIZE`, no `EXPORT_NAME`**, exactly like
  `/workspace/starters/coworld-ctf/replay-viewer/config.nims`. The worker matches that pairing:
  `var Module = {}` … `Module.onRuntimeInitialized = function () {…}` … `self.Module = Module` …
  `importScripts('./broadcast_core.js', './cooperative_hunting_replay.js')`
  (`static_replay_worker.js:16, 179-183, 217`). No factory call anywhere. Every symbol the worker
  calls (`_ch_load_replay, _ch_frame, _ch_seek, _ch_input, _ch_tick_count, _ch_packet_ptr,
  _ch_packet_len, _ch_error_ptr, _ch_error_len, _ch_stage_ptr, _ch_stage_len, _ch_mismatch_tick`) is
  both in `EXPORTED_FUNCTIONS` (`config.nims:50`) and `exportc`'d in
  `replay-viewer/cooperative_hunting_replay.nim:128-226`. The `ctf_* → ch_*` rename is applied on
  both sides together. `--preload-file {rootDir}/sprites@sprites` replaces `data@data` as the note
  specifies.
- `Dockerfile.replay-viewer` splices `<!-- CHROME_COMMON -->` → `chrome_common.js` and
  `<!-- BROADCAST_CORE -->` → `static_replay.js`, copies `broadcast_core.js`/`chrome_common.js` into
  `dist/`, and asserts the wasm, the data file, both JS files and the un-spliced markers are gone.

**Checklist 14 — chrome provenance.**
- `client/chrome_common.js` is **byte-identical** to
  `/workspace/starters/coworld-ctf/client/chrome_common.js` (md5 `80ea4eb19cee21cb61fb1f009f1f45ab`
  both sides). `client/broadcast_core.js` likewise (md5 `677fe90f2be107b810c24aef02b936a3`).
- `client/replay_broadcast.html` is **provably** the starter's page with a game block appended:
  running `python3 tools/build_replay_page.py /workspace/starters/coworld-ctf` against the mounted
  starter reproduces the committed file **byte for byte** (diff is empty). The generator takes the
  starter's head (`src[0:6]`), CSS (`src[7:1459]`, filtered), and body (`src[1462:1600]`).
- The banner comment is present twice — CSS at `:957-964` and script at `:1248-1260`, both reading
  "cooperative-hunting additions to the inherited coworld-ctf chrome".
- Diffing our CSS 1..957 against the starter's 1..1270: the only differences are the `<title>`, the
  dropped `@font-face rajdhani` (the bundle ships no font file — `10564b0`), the `#killfeed` →
  `#feed` comment rename, and the removal of exactly the note's list (`#killfeed`, `#povBadge`,
  `#fpv*`/`.fpv-*`, `#viewpanel`/`#minimap`/`#zoombar`/`.zbtn`/`#zoom-*`, `#mmwarn`). Sections
  1 (scorebug), 3 (banner lane), 5 (transport), 6 (end-card) and the scrubber/momentum/lulls/spoiler
  rules are present and unmodified. The page is 1631 lines to the starter's 4165, but the shortfall
  is the starter's ~2500 lines of ctf-specific JS, not the CSS or markup (see N3).
- Removed ids are gone from the markup and required ids are kept — I verified all 19 chrome_common ids
  present exactly once and all 26 removed ids absent; `tests/test_chrome.nim:200-219` asserts the same.
- (a) `relayout()` measures `#transport` and sets `--band` and `--hudscale` on
  `document.documentElement` (`:1603-1611`); the game block only reads them (`:969, 1045, 1089`).
- (b) Nothing fixed-positioned sits inside the band: `#feed` and `#gamechips` ride
  `bottom: calc(var(--band, 0px) + 6 * var(--u))` (`:969`, `:1045`).
- (c) `#endcard { bottom: var(--band, 0px); }` (`:1089`); it is shown with `.on`
  (`:1470`, and the CSS rule is `#endcard.on { display: flex; … }` at `:704`); **every** seek goes
  through `seekTo`, whose first statement is `hideEndcard()` (`:1480-1486`) — scrub click
  (`:1529-1535`), beat marker (`:1416-1419`), restart/back/forward/end buttons (`:1511-1514`),
  keyboard `e , b .` (`:1541-1550`).
- (d) Beats: labelled `<button>` elements with `textContent = label`, `title`, `aria-label`, and an
  `onclick` that seeks (`:1409-1419`); CSS for all five kinds (`:1081-1085`), and
  `beatKindForEvent` (`replay.nim:156-169`) plus the `LegalBeatKinds` filter in `buildChromeLabel`
  (`frames.nim:559-562`) make those five the only kinds that can be emitted —
  `tests/test_chrome.nim:68-113, 227-234` asserts both halves.
- Zoom panel: correctly **removed**, not hidden — no markup, no CSS, no `zoomAt`/`setZoom`/
  `attachMinimap` anywhere in the page or `static_replay.js`, and the ids are on the test's
  removed list. The design note (design.md:645-648) says the 32×32 board is always drawn in full.
- No game-block function shadows a ChromeCommon alias: the beat builder is `pushHuntBeat`
  (`:1404`), asserted at `tests/test_chrome.nim:170-197` against a 47-name alias list.

**Resolution rules (design.md §Rules / §Turn-tick structure).**
- `isCapturedBySides` (`sim.nim:789-806`): Rabbit `n∨s∨e∨w`; Boar `(n∧e)∨(n∧w)∨(s∧e)∨(s∧w)`;
  Stag `(n∧s)∨(e∧w)`; Moose count ≥ 3; Elephant `n∧s∧e∧w`. Matches the note exactly.
- Side occupancy is one predicate for every variant: `stamp.tick > 0 and sim.globalTick - stamp.tick
  <= sim.windowTicks - 1` (`sim.nim:779-783`), with `windowTicks = 3` only for coop-mining
  (`sim_types.nim:500-501`), so `windowTicks = 1` reproduces base staghunt through the same code —
  asserted both ways at `tests/test_capture.nim:148-163` and `:108-134`.
- Rewards paid **in full to every participant** except lbf: `creditCapture` (`sim.nim:831-859`)
  awards `scoreTotal` to each slot unless `splitScore`, in which case
  `award = scoreTotal div slots.len` and `if i == 0: award += scoreTotal mod slots.len` — and `slots`
  was `sort()`ed ascending at `:817`, so the remainder goes to the lowest slot. Asserted at
  `tests/test_capture.nim:186-200` (level-5 food, three level-2 hunters → 4/3/3, energy not split).
- Reward table matches the note: rabbit 1/15, boar 3/90, stag 5/60, moose 10/140, elephant 18/220
  (`sim_types.nim:61-70`); iron 1/10, gold 8/40 (`:91-94`); lbf `2×level` / `20×level` (`:100-101`);
  berry 1/12, tag 6 / −30 / respawn 24 (`:107-111`).
- Tick order in `step` (`sim.nim:1192-1229`) is the note's list, steps 3→8, with steps 1/2/9/10/11
  owned by the server loop (`cooperative_hunting.nim:995-1096`) in the same order.
- predator-prey: roles `(slot + roundIndex) mod 2` (`sim.nim:358-359`), tag = the stag predicate on a
  player (`:980-982`), tall grass hides a forager beyond Chebyshev 2 in a **per-seat** frame only
  (`sim.nim:1087-1103`, used by `frames.nim:328`), never on `/global` — asserted at
  `tests/test_step.nim:206-229`. No NPC animals: `hasAnimals()` is true only for `"staghunt"`
  (`sim.nim:86-87`), matching §Out of scope 4.
- Four manifest variants map to the four `variant` strings the sim knows
  (`sim_types.nim:506-507`, `cooperative_hunting.nim:105-108` rejects anything else and keeps the
  default), and `tests/test_episode.nim:84-105` runs all four end to end.

**Scoring (design.md §Scoring).**
- `resetRound` zeroes `player.score` (`sim.nim:1260`), `freezeRound` snapshots it into
  `ep.roundScores` (`cooperative_hunting.nim:358-370`), and `resultsJson` sums the round arrays into
  `scores.add(%max(0, totals[i]))` (`:310-320`). No term is ever negative: trample and gore touch
  `energy` only (`sim.nim:573-574`, `:666-667`), tag costs the forager energy and no score
  (`sim.nim:994-996`). `tests/test_scoring.nim:209-222` asserts every score is a non-negative
  integer and that `scores` is the sum of the `rounds` arrays.
- Three legal reasons only: `EndReason` is `erComplete | erDeadline | erNoPlayers`
  (`sim_types.nim:251-255`) and `$ep.reason` is the only thing written
  (`cooperative_hunting.nim:355`, `:897`). `tests/test_scoring.nim:178, 199-200` and
  `test_replay_parse.nim:151-152` check the set. The deadline path is exercised end to end at
  `tests/test_scoring.nim:237-255` (`playBudgetSeconds = 1`, asserts `reason == "deadline"`, one
  partial round scored not zeroed, scores present, and a `deadline` event in the replay).
- `no_players` writes zero-score results **and** a replay, then sleeps the grace and `quit(0)`
  (`cooperative_hunting.nim:858-908`, `:943-948`).

**Replay writer (design.md §Replay bytes).**
- Header, seats, rounds, ticks and results, assembled by hand (`replay.nim:237-358`); `p` on every
  tick, `q`/`c` only when the serialised text changed, `ev` only when non-empty
  (`recordTick`, `:313-345`) — exactly the note's one compression. `flags` bits 1/2/4/8/16 match
  design.md:576-577 (`replay.nim:24-27`, `playersArray` `:270-283`).
- `EventVocabulary` (`replay.nim:36-40`) is the note's 15 names verbatim, and
  `tests/test_episode.nim:68-80` asserts the episode emits nothing outside it.
- Every key the note lists is present and asserted (`tests/test_replay_parse.nim:46-56`), and the
  reader/writer round-trip is exercised on a real episode. `escapeJson` is used for every key and
  string (`replay.nim:104, 325, 338, 353`).
- The document is self-sufficient: `world.tiles` is the full 1024-char string
  (asserted `test_replay_parse.nim:52-53`), plus `grass`, `berries`, `seats[].name/alias`, the
  expanded `config`, `rounds[].roles`, and `results`.
- Observed on the real artifact: 355 041 B for 1040 ticks, `reason: complete`,
  `scores: [4,25,16,12,14,17]`, six seats with `kind` `prompt/prompt/scripted×4`.

**Registration / protocol (design.md §Server, player, protocol).**
- `0x90` client→server: `[0x90, len_lo, len_hi, body…]` written by
  `cooperative_hunting_player.nim:66-76` and parsed at `cooperative_hunting.nim:824-833`.
  `parseRegistration` (`:787-807`) drops a malformed / oversized / non-UTF-8 body and returns
  `{scripted, big_game_hunter}` — never a disconnect, exactly design.md:511-512.
- `0x91` server→client goes **only** to `pkPrompt` seats (`cooperative_hunting.nim:1084-1087`),
  at most one per planning turn (`ep.planReady[slot]` is cleared on send).
- Routes: `/healthz` (`:677-684`), `/player` and `/global` without an upgrade serve the static
  bitworld client pages with no socket side effect (`:743-748`, `:698-718`), `/player` with an
  upgrade checks the token (`:749-762`, 403 on mismatch), `/global` with an upgrade joins the
  spectator set, everything else 200 text (`:782-785`).

**Art.** All new furniture is drawn with the starter's `patternToRgbaSprite` DSL and registered in the
sprite cache — iron, gold, the countdown ring, ripe/picked berries, food, tall grass and its dim
variant, and the level badges (`art.nim:440-479`, `:603-616`). No placeholder box, no new PNG.

---

## Could not determine

- **360 px legibility.** The only screenshot CI produces is 1280×800 (`viewer-smoke.png`). The
  `@media (max-width: 640px)` block (`client/replay_broadcast.html:1103-1125`) restacks the scorebug
  to one column and hides `.plate-alias`, `.plate-energy` and `.plate-badge`, which may be why the
  1280 px clipping in N5 does not occur at 360 px — but I have no browser here to check. What would
  settle it: a `viewer_smoke.mjs` run (or a Playwright screenshot) at 360 px wide, or a second
  `--out` screenshot at that viewport in the `wasm-viewer` job.
- **Whether the 4 KB chrome-label trim engages on a manifest-length episode.** The CI replay is the
  1040-tick certification fixture (44 beats). N6's ~127-beat figure for a 3000-tick episode is
  extrapolated. What would settle it: a `docker_smoke.sh` run with `rounds: 3, ticksPerRound: 960`,
  or a unit test that feeds `buildChromeLabel` 130 beats + 6 seats and asserts nothing is dropped.
- **Whether the 0 % scrub probe genuinely seeks** (N19). What would settle it: the smoke reading the
  clock after an explicit `advanced` round-trip, or a probe at 25 % as a control.
- **The grid harness behind checklist item 7's "tuned, not guessed".** The note says the balance
  constants and the eight bots are staghunt's, carried over unchanged and explicitly not retuned
  (design.md:102-103, 360-364, 875-877), and `.claude/skills/stag-hunt-balance/SKILL.md` plus
  `balance_sweep.sh` are named as the harness that comes along un-run. I can see the skill files in
  the tree but not the harness's output for *these* numbers. What would settle it: a pointer to the
  staghunt sweep that produced them, or the note stating explicitly that the item is satisfied by
  inheritance.
- **Whether `curly.makeRequests`'s `timeout` argument bounds the whole batch or each request.** I read
  the call site (`llm.nim:612`) but `curly` is not vendored in this sandbox, so B3's `≤ 24 s` join
  figure assumes per-batch. If it is per-request-with-a-shared-deadline the figure is the same; if
  requests can serialise, it is larger. What would settle it: reading `curly`'s `makeRequests`.
