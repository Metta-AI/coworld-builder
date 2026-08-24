# r1 review — chorus

Repo: `Metta-AI/cogame-chorus` @ `8777d565de5a845d9b085fdb835072886a1f2f6d` (main), read at `/tmp/cogame-chorus`
Range: `a2e9334..8777d56` (3 commits: bootstrap, fork, fix)
Design note: `/workspace/coworld-builder/runs/2026-08-24-chorus/design.md`
Starter (read-only): `/workspace/starters/cogame-bullwhip`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files read in full: `src/chorus/{sim,types,llm,server}.nim`, `src/chorus.nim`, `src/chorus_player.nim`,
`tests/test_sim.nim`, `tests/test_bot.nim`, `client/{chrome_common.js,renderer.js,replay_broadcast.html,global.html,player.html,chrome.css}`,
`replay-viewer/{chorus_replay.nim,config.nims,static_replay.js,index.html}`, `coworld_manifest_template.json`,
`tools/build_replay_viewer.sh`, `tools/ci/{docker_smoke.sh,chrome_check.mjs,policies.json}`, `.github/workflows/ci.yml`,
`Dockerfile`, `compose.yaml`, `chorus.nimble` — 27 files, plus byte-diffs against the starter and the CI logs
and `smoke-replay` artifact of run **32692450898**.

---

## Blocking

### F1 — the retry-exhausted LLM fallback is recorded in the replay as `scripted: false`

- **Where:** `src/chorus/llm.nim:610-613`, `src/chorus/llm.nim:40-44`, `src/chorus/server.nim:341-352`
- **Observed (traced):**
  - `decideAll` ends with the fallback loop:
    ```nim
    for index in open:
      let seat = seats[index]
      echo "chorus llm: seat ", seat, " falling back to the arpeggio baseline"
      result[index] = scriptedAction(sim, seat, skArpeggio)
    ```
    (`llm.nim:610-613`). `open` at this point is exactly the set of LLM seats that failed **both**
    attempts of the `for attempt in 0 .. 1` loop (`llm.nim:580-609`).
  - The returned `Decision` object carries no provenance field:
    ```nim
    Decision* = object
      target*: int
      steps*: seq[int]
      say*: string
      notes*: string      ## "" when the reply carried none
    ```
    (`llm.nim:40-44`). Nothing in the value distinguishes a parsed model reply from an arpeggio
    fallback.
  - The server therefore re-derives the flag from its own inputs:
    ```nim
    let decision = decisions[index]
    let wasScripted = scripted[seat] != skNone or client.disabled
    ...
    state.sim.applyBar(seat, decision.target, decision.steps,
      decision.say, decision.notes, wasScripted)
    ```
    (`server.nim:342-352`). For an LLM seat (`scripted[seat] == skNone`) on an **enabled** client
    (`client.disabled == false`) — i.e. the exact case where the two attempts timed out or failed to
    parse — `wasScripted` is `false`.
  - `applyBar` copies that straight into the event: `event.scripted = scripted` (`sim.nim:506`), and
    `eventToJson` writes it as `result["scripted"] = %event.scripted` (`sim.nim:722`). So the replay
    records `"scripted": false` for a bar that was in fact the `arpeggio` baseline.
  - The only surviving record of the fallback is the stdout line at `llm.nim:612`, which does not ride
    in the replay or in `results.json`.
  - The second fallback path — `applyBar` raising inside the server (`server.nim:353-358`) — *does*
    pass `true`. But `decideAll` already validates each decision against a `probe` sim
    (`llm.nim:600-602`), so that path is only reachable for a decision that was legal against the
    turn-open snapshot and illegal at apply time, which cannot happen here (each seat writes its own
    voice and `pendingSeats` guarantees `barIn[voice] == false`).
- **Checklist item:** 8 — "LLM reply handling. Parsing is tolerant …, retries **once** on a parse or
  transport failure, then falls back to the scripted move — **and the fallback is recorded so phase 60
  can count it**."
- **What the design note says:** §*Degrade, never hang* (design.md:311): "still failing after the retry
  | the seat plays **`arpeggio`** … the `bar` event records `scripted: true`". §*Event vocabulary*
  (design.md:581): "`scripted*: bool ## bar: decided by a scripted baseline / fallback`".
- **Why blocking:** phase 60 counts fallbacks from the replay's `scripted` flags; on a live LLM episode
  every timed-out/unparseable seat is indistinguishable from a successful model reply in the recorded
  bytes, so the fallback rate reads as 0 no matter how badly the model is doing.
- **Note on provenance (not an excuse, stated for accuracy):** the same construction exists verbatim in
  the starter (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:474-478` and
  `src/bullwhip/server.nim:296`). It is inherited, not introduced. It is still what the checklist item
  and the design note describe as not happening.
- **Not observable in CI:** the docker-smoke episode runs with no `ANTHROPIC_API_KEY`, so
  `client.disabled == true` and every bar is correctly `"scripted": true` (verified in the
  `smoke-replay` artifact of run 32692450898 — all 24 `bar` events carry `"scripted": true`). The gap
  only opens on an episode with credentials.

---

## Non-blocking

### F2 — a zero-bar score is 15.0, not the 0.0 the design states twice

- **Where:** `src/chorus/sim.nim:299-324` (`noveltyRaw`/`noveltyScore`), `sim.nim:326-339` (`pieceScore`),
  `sim.nim:369-384` (`turnEvent`)
- **Observed (traced, then confirmed against a real replay):**
  - `noveltyRaw` opens with `if n < 2: return 0.5` (`sim.nim:303-304`).
  - `noveltyScore` is `max(0.0, 1.0 - 2.0 * abs(raw - 0.5))` (`sim.nim:324`), so `raw = 0.5` → `1.0`.
  - At `n = 0` the other three terms are 0: `consonanceScore` loops `for bar in 0 ..< n` and returns
    `0.0` when `count == 0` (`sim.nim:207-219`); `leadingScore`'s `count` and `eligible` are both 0
    (`sim.nim:226-266`); `rhythmParts` returns `(0.0, 0.0, 0.0)` because `onsets == 0` and
    `columns == 0` (`sim.nim:287-293`).
  - So `pieceScore(grid, 0).piece = 100 * (0.15 * 1.0) = 15.0` and `parts = [0, 0, 0, 1.0]`.
  - `openTurn` calls `sim.addEvent(sim.turnEvent())` (`sim.nim:400`) with `turnsPlayed == 0` at `t = 0`.
  - **Confirmed empirically** in the `smoke-replay` artifact of CI run 32692450898:
    `{"kind": "turn", "turn": 0, "chord": 0, "piece": 15.0, "parts": [0.0, 0.0, 0.0, 1.0], "credits": [0.0, 0.0, 0.0, 0.0]}`.
- **What the design says:** design.md:106 — "Append a **`turn`** event carrying `t`, `chords[t]`, and the
  running score of bars `0 .. t-1` …; at `t = 0` that score is `0.0` with all-zero parts and credits."
  design.md:228 — a `deadline` over 0 bars is "possibly 0 bars → `piece = 0`, all credits `0`".
- **Also observed:** the design is internally inconsistent here — design.md:184 says "when `n < 2`,
  `raw = 0.5`", which is precisely what the code implements and precisely what produces 15.0. Credits
  *are* all zero (`15.0 − 15.0`), as the note requires; only `piece` and `parts[3]` differ.
- **Consequence (inferred):** a `deadline` ending before any turn resolves would report
  `results.piece = 15.0` for an empty piece; and the score strip's first history point sits at 15
  rather than 0 (`renderer.js:486-498` plots `row.piece`). Neither breaks a checklist item — the value
  is inside `results_schema`'s `piece: 0..100`, and the re-derivation reproduces it exactly.
- **Not on the checklist**, so not blocking.

### F3 — `client/chrome_common.js` has no starter counterpart to byte-diff against

- **Where:** `client/chrome_common.js:1-272`; starter has no such file (`ls /workspace/starters/cogame-bullwhip/client/` →
  `chrome.css global.html player.html renderer.js replay.html`).
- **Observed:** checklist item 14's first bullet asks for a byte-identical `diff` against
  `/workspace/starters/cogame-bullwhip/client/chrome_common.js`. **That file does not exist in the
  starter**, so a literal diff is impossible. The design note anticipates this (design.md:849-856):
  every function in `chrome_common.js` is bullwhip's `client/renderer.js` function.
- **Verification I actually performed:** extracted each of the 15 named functions from both files by
  regex and compared bytes:
  `assetUrl, loadImages, seatColor, ellipsize, hexToRgb, rgba, roundRect, wrapLines, escapeHtml,
  clampName, isBaselineFiller, makeNameMap, applyNames, makeEffects, bindFeedToggle` — **all 15
  byte-identical** to `cogame-bullwhip/client/renderer.js`. The palette constants (`COLORS`,
  `COLOR_HEX`, `PAPER`, `PAPER_DIM`, `INK`, `AMBER`, `GHOST`, `STRIP`) are identical too
  (`chrome_common.js:23-37` vs `renderer.js:27-46`). The only non-starter lines are the IIFE wrapper
  (`:20-21`, `:272`), the `window.ChorusChrome = {…}` export (`:246-271`), and the one marked added
  function `relayout()` (`:221-244`) — exactly the three exceptions the design declares.
- **Recorded here so the judge does not mark item 14 unverifiable**: the substance of the bullet
  (nothing transplanted rewritten, reindented or renamed) is verified; only the literal `diff` target
  is absent.

### F4 — `client/player.html` opens a `/player` websocket, contradicting design.md:690

- **Where:** `client/player.html:49-51` — `wsPath: "/player?slot=" + encodeURIComponent(params.get("slot") || "0") + "&token=" + …`
- **What the design says:** design.md:690 — "Neither `/client/` HTML route opens a player socket."
- **Observed:** the page served at `GET /client/player` (`server.nim:529`) calls
  `ChorusRenderer.attachLive({… wsPath: "/player?slot=…&token=…"})`, which opens
  `ws://host/player?slot=…` (`renderer.js:1178-1192`). This is bullwhip's page verbatim — the diff
  against `cogame-bullwhip/client/player.html` shows only the `Bullwhip`→`Chorus` renames, the added
  `chrome_common.js` script tag, and the appended game block.
- **Why it is not a hazard in practice (inferred):** the certifier's concern (lantern 0.1.1) is that
  `GET /client/player` returns 200, which it does; the websocket is opened only by a browser that
  loads the page, and `playerUpgradeHandler` rejects any slot/token mismatch with 401 before
  registering anything (`server.nim:428-434`). A caller would need a live seat token.
- Not on the checklist. Reported because the design note asserts something the code does not do.

### F5 — the play deadline is measured from before the player-connect wait, not after it

- **Where:** `src/chorus/server.nim:249-250`, `:252-258`, `:281-283`, `:299-307`
- **Observed:**
  ```nim
  let gameStart = epochTime()
  let deadline = gameStart + config.playerConnectTimeoutSeconds
  while epochTime() < deadline: … sleep(200)      # up to 180 s
  …
  let playDeadline = gameStart + timeoutSeconds * PlayBudgetFraction   # gameStart + 720 s
  ```
  so the up-to-180 s connect wait is spent *inside* the 720 s play budget.
- **What the design says:** design.md:303 — "Container start, the 180 s player-connect wait and artifact
  writing all live in the other 40 % (480 s)."
- **Direction of the error (inferred):** conservative. The worst case is that play is cut short and the
  episode settles `reason = "deadline"`, which the design explicitly declares an acceptable ending
  (design.md:230). `long-form` (`bars = 10`, 604 s worst case) plus a full 180 s connect wait would
  exceed 720 s and trip the deadline path rather than overrun.
- **Bound on the actual settle time (inferred):** the deadline is only tested between turns
  (`server.nim:299`), so the worst case is `playDeadline` + one turn (`2 × 30 s` LLM + `0.4 s` pace)
  + `sleep(500)` + `ShutdownGraceSeconds` 20 s ≈ **801 s**, against a 1200 s platform kill. That is
  outside the checklist's literal "inside 60 %" (720 s) but is structural to the design's
  "check between turns" rule, and it is 400 s clear of the kill.
- Not blocking: no unbounded wait, no blocking read, and every configured knob is bounded (see
  *Traced and consistent*).

### F6 — `makeEffects` in the chrome module is dead for chorus's event vocabulary

- **Where:** `client/chrome_common.js:161-198`; `client/renderer.js:88-135`, `:1177`, `:1257`
- **Observed:** the copied-verbatim `makeEffects` switches on `event.kind === "week"` and
  `event.kind === "order"` (`chrome_common.js:176-184`) — bullwhip's kinds. Chorus emits
  `start|turn|bar|end` (`types.nim:25-29`), so `absorb` would never set a timer. The renderer does not
  use it: it defines and uses its own `makeChorusEffects` (`renderer.js:88`, called at `:1177` and
  `:1257`). `makeEffects` is exported (`chrome_common.js:268`) and never called.
- This is exactly what the design asks for (design.md:853 lists `makeEffects` among the functions kept
  character-for-character), so it is inherited dead code, not a regression.
- **Related, smaller:** `var SLIP_MS = 900;` (`renderer.js:44`) is declared and never used, although
  design.md:928 names `SLIDE_MS`/`SLIP_MS` as the effect timers. `SLIDE_MS` *is* used
  (`renderer.js:307`).

### F7 — at 360 px nothing on screen links a seat to its voice

- **Where:** `client/chrome.css:601-604` (chorus additions), `client/renderer.js:368-374`,
  `/workspace/starters/cogame-bullwhip/client/chrome.css:454-456`
- **Observed:**
  - `@media (max-width: 420px) { .legend-text { display: none; } }` (`chrome.css:601-603`) — the legend
    keeps its swatch and drops `TENOR Sprocket`.
  - `drawLaneLabel` draws the voice name always but the seat name only when not compact:
    `if (!L.compact && seat) { … C.clampName(seat.name || "") … }` (`renderer.js:368-374`), and
    `compact` is `width < 560` (`renderer.js:156`, `:46`).
  - The scorebug's `.plate-label` (the voice tag) is hidden by the starter's
    `@media (max-width: 640px) { .plate-label { display: none; } }`.
  - Net at 360 px: lanes show `BASS/TENOR/ALTO/SOPRANO`, the scorebug shows name + signed credit, and
    nothing states which name owns which lane except the shared colour — and the plate's colour class
    is `plate red|blue|green|yellow` (`renderer.js:940`), for which the starter's stylesheet has no
    `--tc` rule (it defines `.seat0…seat4` only, `chrome.css:205-209`), so the plate name renders in
    paper, not the seat colour. This last part is inherited verbatim from bullwhip
    (`cogame-bullwhip/client/renderer.js:1002`).
- **Checklist item 11 is satisfied regardless:** `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` is
  present twice (starter `chrome.css:288-290`, chorus addition `chrome.css:534`) and `.plate-label` is
  hidden under 640 px. The CI smoke read the scorebug back as
  `"Sprocket +10.6 TENOR Gizmo ▶ +5.5 ALTO …"` — names do not collapse.
- Legibility observation only.

### F8 — the `end` event is not covered by the event round-trip test

- **Where:** `tests/test_sim.nim:404-427`
- **Observed:** the round-trip test builds a 4-bar sim, plays **one** turn (`live.writeAll(...)`,
  `:407`) and loops over `live.events`, asserting `check evStart in kinds`, `evTurn in kinds`,
  `evBar in kinds` (`:425-427`). The sim never settles, so no `evEnd` is in `kinds` and no `end` event
  is put through `eventFromJson(eventToJson(e))`.
- **What the design says:** design.md:1187 — "`eventFromJson(eventToJson(e)) == e` for one event of
  **every** kind".
- **Mitigating, observed:** the `end` codec is exercised indirectly — `tests/test_sim.nim:441-453`
  replays a `deadline` log through `replayMatch` and asserts the replayed sim settles, and the CI
  smoke replay's `{"kind": "end", "turn": 6, "text": "complete"}` is parsed by the wasm module
  (`chorus_replay.nim:35-36`) in the green `wasm-viewer` job.

### F9 — the scrubber's beat helper is chorus's own, not `chrome_common.markBeat`

- **Where:** `client/renderer.js:703-719` (`chorusMarkBeat`), `:721-801` (`buildChorusScrub`)
- **Observed:** checklist item 14(d) names `chrome_common.markBeat(tick, kind, team, label)`. Chorus
  has no `markBeat` in `chrome_common.js` at all; the builder and the marker helper live in
  `renderer.js` under `buildChorusScrub`/`chorusMarkBeat`. The design declares this deliberately
  (design.md:897-914) as the anti-shadowing measure, and `tools/ci/chrome_check.mjs:40-48` enforces the
  disjointness (green in run 32692450898, step 6 of `wasm-viewer`).
- **The substance of 14(d) is met** and I verified it line by line — see *Traced and consistent*.
  Recorded only so the name mismatch is not mistaken for an absence.

---

## Traced and consistent

**Checklist 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-chorus --branch main -w ci.yml` → run **32692450898**, conclusion
  **success**, `headSha` **8777d565de5a845d9b085fdb835072886a1f2f6d** = the reviewed sha. All three
  jobs (`test`, `docker-smoke`, `wasm-viewer`) success, every step success, none `continue-on-error`.
- `git log --oneline -- tests/` in the coworld repo returns exactly one commit (`147138b`, the fork),
  and `git diff 147138b 8777d56 -- tests/` is **empty** — the test files were added once and never
  touched again. No deleted assertion, no widened tolerance, no `skip`, no removed file.

**Checklist 2 — replay re-derivation, and the viewer derives from it.**
- `sim.nim:645-689` `replayMatch`: `result.add(sim)` before the loop and once per event, so
  `frames[i]` = state after `events[0 ..< i]` and `len == events.len + 1` (asserted at
  `test_sim.nim:399`).
- `bar` events are the only source: `of evBar: sim.applyBar(...)` (`:682-684`). `turn` events are a
  **check** — `turn`, `chord`, `piece`, all four `parts` and all four `credits` are compared against
  `sim.turnEvent()` within `1e-4` and raise `ChorusError` otherwise (`:660-676`). Tamper tests for
  both `piece` and `chord` at `test_sim.nim:428-439`.
- The dedup fix in `8777d56` is correct as traced: the guard
  `if not sim.done and (sim.events.len == 0 or sim.events[^1].kind != evTurn)` (`:679-681`) appends the
  opening `turn` event (last event is `evStart`), skips the per-turn ones already logged by
  `openTurn` inside `applyBar → resolveTurn`, and skips the final one because `settle` has set
  `sim.done` (`:434-441`, `:443-452`). The check still runs unconditionally before the guard.
- The viewer reads `payload.states` (`renderer.js:1248`), and `states` is produced only by
  `for frame in replayMatch(config, events): states.add(frame.tableStateJson())`
  (`replay-viewer/chorus_replay.nim:37-39`; identically `server.nim:184-188` for the pod `/replay`
  route). There is **no parallel per-tick recording** in the replay payload
  (`server.nim:169-182`: `protocol, names, policyNames, config, events, results` only).
- End-to-end evidence: the 33-event, 6-bar smoke replay loaded in the wasm module in CI without
  `ch_load_replay` returning 0 (`{"loaded":true,…}`), which means `replayMatch` did not raise on real
  recorded bytes.
- Asserted final-frame identity: `check $frames[^1].tableStateJson() == $live.tableStateJson()`
  (`test_sim.nim:400`) and the same for a `deadline` log (`:453`). *Granularity note:* the test compares
  the final frame plus every recorded `turn` checkpoint, not each of the 33 frames against a recorded
  per-tick state — but no such parallel record exists to compare against, so the viewer necessarily
  displays the re-derivation.

**Checklist 3 — static viewer.**
- `coworld_manifest_template.json:15-17` → `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- `tools/build_replay_viewer.sh` present, committed mode `100755` (`git ls-files -s tools/`), invoked in
  `ci.yml:268` by path (not via `bash`), with the exec-bit assertion at `ci.yml:225-236`.
- `mkdir -p "$(dirname "${output_dir}")"` happens at `build_replay_viewer.sh:22`, before anything
  resolves against it (the ecos 2026-08-23 gotcha).
- The viewer's only network call is `fetch(url)` on the `?replay=` URL (`static_replay.js:76`); assets
  are relative (`index.html:6,37-40`, `assetBase: "./assets"` at `static_replay.js:117`). No websocket,
  no API host.
- `/client/replay` does exist as a **pod page route** (`server.nim:530`) and is mentioned in prose in
  `coworld_manifest_template.json:258` and `README.md:69`, but it is **not** declared as the
  `replay_viewer`; the manifest carries only the bundle. Same shape as the starter.

**Checklist 4 — both name spaces.**
- In-game: `tableNames` (`sim.nim:122-133`) is bullwhip's function verbatim; `systemPrompt`/`userPrompt`
  address seats only through `sim.seatName` → `sim.names[seat]` (`llm.nim:211-212, 263-386`).
  `test_sim.nim:514-540` asserts each seat's alias appears in both prompts and that **none** of four
  policy display names does.
- Player frames carry aliases (`server.nim:446`, `:117`, `:210-214`); `results.names` carries policy
  names (`sim.nim:533`). Verified in the smoke artifact: replay `names` =
  `["Tinker","Bolt","Rivet","Gizmo"]`, `policyNames`/`results.names` =
  `["Sprocket","Gizmo","Ratchet","Widget"]`.
- Spectator side: `snapshotJson` adds `policyNames` (`server.nim:96`), the viewer builds
  `C.makeNameMap(payload.names, payload.policyNames)` (`renderer.js:1250`) and applies it in
  `applyNames`/`updateScorebug`/`updateEndscreen`/`updateLegend`/feed.

**Checklist 5 — every wait and its bound.** Enumerated exhaustively:
| wait | where | bound |
|---|---|---|
| player connect | `server.nim:252-258` | `gameStart + playerConnectTimeoutSeconds` (180); 200 ms poll |
| batch-spacing floor | `server.nim:324-331` | `min(minTurnSpacingMs, playDeadline − now)`, both non-negative |
| LLM batch | `llm.nim:591` `makeRequests(batch, client.timeoutSeconds)` | `llmTimeoutSeconds` (30; schema 5..300), at most 2 attempts |
| turn pacing | `server.nim:362-363`, `:366-367` | `turnDelayMs`, itself capped by `sampleEpisode` at `PacingBudgetMs div bars` (`sim.nim:142-143`) |
| pre-artifact flush | `server.nim:223` | fixed 500 ms |
| shutdown grace | `server.nim:237` | fixed `ShutdownGraceSeconds = 20`, then `quit(0)` |
| main turn loop | `server.nim:291-363` | exits on `sim.sim.done` or the deadline; each pass writes all four bars → `resolveTurn` → strict progress |
- No unbounded loop in the game process. `applyBar` cannot raise on the fallback path
  (`server.nim:356-358`) because `scriptedAction` is legal by construction and `pendingSeats`
  guarantees the voice is open.
- Deadline honoured before opening a turn, `endEarly()` between turns only (`server.nim:299-307`,
  `sim.nim:512-519`), reason `"deadline"` — matching design step 0.
- `PlayBudgetFraction = 0.6` (`server.nim:241`); `COWORLD_TIMEOUT_SECONDS` read but assumed absent, with
  `config.episodeTimeoutSeconds` (1200) as the assumption (`server.nim:274-283`) — exactly as
  design.md:291-293 describes.

**Checklist 6 — `num_agents`.**
- Present in all three variants (`coworld_manifest_template.json:374, 401, 428`) and in
  `certification.game_config` (`:453`).
- `tools/ci/docker_smoke.sh:107-151` enforces all four invariants with a `SEAT-COUNT FAIL:` prefix:
  present (`:109-116`), positive integer (`:118-125`), `len(certification.players) == n` (`:129-135`),
  `len(certification.game_config.players) == n` (`:136-141`), and `SMOKE_SEATS` as an independent
  second declaration (`:147-151`). `SMOKE_SEATS` defaults to `4` (`:56`) and `ci.yml:184` passes
  `SMOKE_SLUG`.
- **Grepped the job logs, not the colour:** `grep -c "SEAT-COUNT FAIL"` over the full
  `docker-smoke` (job 97328450577) and `wasm-viewer` (job 97328639296) logs → **0**. The log reads
  `game=chorus seats=4 …"num_agents": 4…` and `smoke OK: seats=4 … reason=complete`, plus
  `player 0..3: exit 0`.
- `initSim` raises `ChorusError` unless `players.len == 4` (`sim.nim:403-405`).

**Checklist 7 — scripted baseline plays full episodes legally.**
- `tests/test_bot.nim:43-69`: seeds `[1,5,42,1234]` × `{skArpeggio, skPedal}`, `check sim.reason ==
  "complete"`, `turnsPlayed == bars`, every bar 16 tokens in `{-1} ∪ [0,13]`, `target == turn`,
  `say`/`notes` empty (strict mode, `:26-38`), `events.len == 5*bars+3`, all four voices covered,
  `elapsed < 2000` ms.
- I re-derived the design's own arpeggio arithmetic from the code and it reproduces exactly:
  onsets per bar `2 + 4 + 4 + 5 = 15` of 64 → density `0.234` (inside `[0.20, 0.55]`); the union of
  onset columns is `{0,2,3,4,6,8,10,12,14}` = 9 of 16, and no column has all four voices (max 3, at
  step 0); pulse total `2.0 + 4.0 + 2.8 + 3.8 = 12.6` over 15 onsets = **`Ra = 0.84`**, matching
  design.md:419. `pedalBar` gives `4·(4·1 + 4·2)/512 = 0.094`, matching design.md:423.
- `llm.nim:160-197` matches design.md:409-424 table-for-table, including `rot = bar mod 3` and
  `clampToken(tones[0] + 7)` for SOPRANO.
- `test_bot.nim:71-94` pins the quality band `[40, 92]` over 200 seeds and `pedal < arpeggio` on ≥90 %,
  and echoes mean/min/max to the log.

**Checklist 8 — parse tolerance and retry-once** (the fallback recording is F1):
- `extractJsonObject` (`llm.nim:396-409`) takes `find('{')` … `rfind('}')`, tolerating leading and
  trailing prose; quotes the head of a non-JSON reply into the error.
- `parseSteps` (`llm.nim:495-530`) accepts a JSON array of ints/floats/numeric-strings/nulls, and a
  string form after replacing `[ ] ( ) \n \t ; | ,` with spaces; `parseStepToken` (`:479-493`) maps
  `. - r rest` (lower-cased, so `R` works) to `Rest` and rounds floats. Length and range validated
  before return.
- `parseDecision` (`llm.nim:532-558`): missing/`null` `target` defaults to `turn`; int/float/string
  accepted; range-checked.
- Retry once: `for attempt in 0 .. 1` (`llm.nim:580`), the second batch appends
  `sim.retryHint(reasons[index])` (`:587-588`, `:388-392`) carrying the truncated reason and the legal
  target list.
- Each candidate is validated against a `probe = sim` copy before acceptance (`llm.nim:600-602`), so an
  illegal reply is rejected in time for the retry to carry the hint.
- `tests/test_bot.nim:116-173` covers array form, both string forms, all rest spellings, float
  rounding, numeric strings, missing target, trailing prose, and rejects lengths 15/17, token 14,
  token −2 and `target = t+1`.
- Disabled-client path: `newLlmClient` sets `disabled = true` with no credentials
  (`llm.nim:145-148`); `decideAll` then decides every seat locally and the `for attempt` loop breaks
  immediately (`llm.nim:575-582`) — **no network call, no retries**. `test_bot.nim:96-114` asserts it.

**Simultaneous decisions — one parallel batch per turn.**
- `decideAll` builds a single `RequestBatch`, `batch.post(...)` once per open seat, then **one**
  `client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:583-591`). There is no per-seat
  request call anywhere: `grep` for `makeRequests` in `src/` returns exactly this one line, and
  `curl.post` appears only in `writeArtifact` (`server.nim:155`).
- The batch runs outside the state lock on `simCopy` taken under it (`server.nim:296-338`), and all
  four bars are applied under the lock afterwards (`:340-359`) — matching design steps 3-5.

**Checklist 9 — rune-safe truncation.**
- `applyBar`: `if message.runeLen > MaxSayLen: message = message.runeSubStr(0, MaxSayLen)`
  (`sim.nim:489-490`); `notes` the same at `MaxNotesLen = 600` (`sim.nim:495-497`).
- `cleanText` (`llm.nim:470-477`) cuts at `runeSubStr(0, limit - 1) & "…"`; used for `notes`
  (`:535`), `say` (`:536`, then newlines collapsed to spaces at `:537`), and captured error text at
  `MaxErrorLen = 200` (`:605`).
- Delivered prompt: `if prompt.runeLen > MaxPromptLen: prompt = prompt.runeSubStr(0, MaxPromptLen)`
  with `MaxPromptLen = 4000` (`server.nim:496-497`, `:36`).
- The two strings that reach the replay are `event.say` and `event.text` (`sim.nim:505,507`) plus the
  end reason (`"complete"`/`"deadline"`, ASCII). Captured error text never enters an event — it is only
  appended to the retry prompt.
- `test_sim.nim:354-382` feeds 400×`"音"` and 900×`"音"`, asserts `runeLen == 100` / `== 600` exactly,
  `validateUtf8() == -1` on the strings, on every event's `say`/`text`, **and on the serialised event
  JSON bytes**, and round-trips them.
- `docker_smoke.sh:290-296` decodes the whole replay as UTF-8 and parses it as JSON
  (`SMOKE_REQUIRE_REPLAY_JSON=1` default) — green in run 32692450898.

**Checklist 10 — manifest validates.**
- `game.docs` = `{"readme": {"type":"text","value":…}, "pages":[{id,title,content:{type,value}} ×2]}`
  (`coworld_manifest_template.json:261-284`), pages `rules.md` and `scoring.md`.
- `game.protocols` carries **both** `player` (`:252-255`) and `global` (`:256-259`).
- `config_schema` is `additionalProperties: false`, `required: ["tokens","players"]`, and every array
  property carries `minItems`/`maxItems` = 4 (`:40-68`). `num_agents` is `integer, min 4, max 4`.
  Every key it declares is read by `types.nim:70-100`, and the snake-cased
  `player_connect_timeout_seconds` matches `types.nim:92-94`.
- `results_schema` is `additionalProperties: false` with the 14 required keys, `scores` items
  `−100..100`, `piece` `0..100`, the four components `0..1`, `bars` `≥0`, `maxBars` `≥4` — and
  `resultsJson` (`sim.nim:537-552`) emits exactly those 14 keys and nothing else. Verified against the
  real `results.json` from the smoke.
- `episode_timeout_minutes: 20` = the 1200 s the code assumes.

**Checklist 11 — legible at 360 px.**
- `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` inherited at `chrome.css:280-291` and restated
  in the chorus block at `chrome.css:533-534`.
- `@media (max-width: 640px) { .plate-label { display: none; } … }` inherited at `chrome.css:452-456`.
- The CI viewer smoke read the scorebug back intact at every scrub position (see below).

**Checklist 12 — release order and scaffold.**
- `coworld-release.yml` step order: `Build the Coworld manifest` (:153) → `Certify locally` (:167) →
  `Upload the policies` (:206) → `Upload the Coworld` (:304) → `Put the Coworld secret` (:342).
- All three workflows present (`ci.yml`, `coworld-release.yml`, `coworld-submit.yml`).
- `tools/ci/docker_smoke.sh` mode `100755`; the docker-smoke job builds the image in the same job that
  runs the smoke (`ci.yml:176-185`).
- `tools/ci/policies.json` has 4 policies: two `PLAYER_PROMPT` champions (`chorus-cantor`,
  `chorus-weaver`) with materially different strategies — cantor is motif/strong-beat discipline,
  weaver is interlock/rest-when-three/rewrite-the-weakest — plus `chorus-arpeggio` and `chorus-pedal`
  as `PLAYER_SCRIPTED` fillers. Champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:15`).
- The placeholder gate runs clean: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`,
  `coworld-release.yml`, `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` → **no matches**
  (grep exit 1 → the gate exits 0).

**Checklist 13 — viewer executes.**
- `wasm-viewer` `needs: docker-smoke` (`ci.yml:212`); step 12, `Load the bundle in a real browser`,
  **ran and succeeded** in run 32692450898 with
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay … --timeout 90 --soak 10`.
  Log evidence:
  `{"loaded":true,"ms":292,"clock":"BAR 2 / 6 · C MIXOLYDIAN · 84 BPM · WAITING ON 3","scorebug":"Sprocket +10.6 TENOR Gizmo ▶ +5.5 ALTO Ratchet ▶ +2.5 BASS Widget ▶ +0.6 SOPRANO","feed_lines":41}`,
  `soak: 10s of playback kept advancing`, and three differing scrub readouts
  (`0%="BAR 2 / 6 …"  50%="BAR 3 / 6 …"  100%="FINAL — PIECE 68.4"`). No `continue-on-error` anywhere in
  the job.
- `data-replay-loaded="true"` is set at `renderer.js:1339`, after the frame IIFE at `:1315-1337` has
  already run once synchronously and called `renderer.draw(...)` at `:1333` — i.e. on the first drawn
  frame. `data-replay-error="<message>"` is set in `static_replay.js:56` on every failure path
  (missing `?replay=`, the 20 s `AbortController` fetch timeout `:71-88`, non-200 `:78`, wasm rejection
  `:96-99`) and removed on a successful load/retry (`:107`, `:134`).
- **Same-starter bootstrap, verified by diff:** `replay-viewer/config.nims` differs from
  `cogame-bullwhip/replay-viewer/config.nims` by exactly the output filename, `EXPORT_NAME`
  (`BullwhipReplayModule` → `ChorusReplayModule`) and the `_bw_*` → `_ch_*` export list.
  `MODULARIZE=1` is kept (`config.nims:38`), and `static_replay.js:138` calls the factory
  `ChorusReplayModule().catch(...)` — the diff against the starter's shell shows only the same
  renames. No `Module.onRuntimeInitialized` anywhere. All four viewer files
  (`config.nims`, `chorus_replay.nim`, `static_replay.js`, `index.html`) diff clean against bullwhip's
  with only renames plus, in `index.html`, the added `chrome_common.js` script tag and the banner-marked
  game block.

**Checklist 14 — chrome is the starter's.**
- `client/replay_broadcast.html` **is** `cogame-bullwhip/client/replay.html` (74 lines) with exactly:
  the `<title>`, `#wordmark` `BULL<span>WHIP` → `CHO<span>RUS`, `#clock` `WEEK 0` → `BAR 0`,
  `BullwhipRenderer` → `ChorusRenderer` (3 sites), **one** inserted
  `<script src="/client/chrome_common.js">` before `renderer.js`, and the game block appended under
  `<!-- chorus additions to the inherited cogame-bullwhip chrome -->`. I ran the diff; there is nothing
  else. Sections 1-5 of the CSS/markup above the banner are untouched and **no element is removed** —
  `#layout #stage #topband #wordmark #clock #topright #statuschip #feedtoggle #scorebug #board-wrap
  #table #lightpool #grain #endscreen #transport #scrub .tbar #play #pos #feed #loading` all present.
- `client/chrome.css`: `diff` against the starter shows **only** an appended block after line 467,
  banner `/* ---------- chorus additions ---------- */`. `tools/ci/chrome_check.mjs:58-76` pins the
  first 11 964 bytes to sha256 `2bfa9443…`; I independently confirmed
  `sha256sum /workspace/starters/cogame-bullwhip/client/chrome.css` = that hash and
  `head -c 11964 client/chrome.css | sha256sum` = the same.
- `client/global.html` and `client/player.html` are forked the same way (renames + script tag +
  appended block; verified by diff).
- **(a)** `relayout()` writes `--topband`, `--band`, `--hudscale` on `document.documentElement`
  (`chrome_common.js:228, 237-240`), on `load` and `resize` (`:242-243`), and `bindFeedToggle`
  dispatches a `resize` on every toggle (`:216`). `--hudscale` is `clamp(0.7, stageWidth/960, 1.6)`
  (`:236`).
- **(b)** Nothing fixed-positioned sits in the band: the two chorus additions are `#audio.tbtn` inside
  the existing `.tbar` (`index.html:65-70`) and `#chorus-legend`, a `display: flex` static element
  appended to `#transport` (`index.html:72-88`, `chrome.css:552-566`).
- **(c)** `#endscreen { bottom: var(--band, 0px); }` (`chrome.css:519`); shown with the class its own
  CSS rule uses — `#endscreen.show { display: flex; }` (starter `chrome.css:383`) toggled by
  `container.classList.toggle("show", !!show)` as `updateEndscreen`'s **first** statement
  (`renderer.js:970`), which `setIndex` calls on **every** index change
  (`renderer.js:1305-1307`). The seeks that exist — scrub pointerdown/move (`:782-789`), beat-marker
  click (`:713-716`), and the play button restart (`:1271-1274`) — all route through `setIndex`. The
  page has no back/forward buttons and no keyboard handler (neither does the starter's), so there is no
  uncovered seek path.
- **(d)** Beats are `<button type="button">` with `title`, `aria-label` and an `onclick` that seeks
  (`renderer.js:703-719`); one per event, with labels like
  `"Bar 3 — Sprocket (Alto) writes 6 notes"` (`:756-763`). Every emitted kind has a CSS rule:
  `bar`, `edit`, `turn`, `end`, `start` (`chrome.css:522-547`), plus the inherited `.seat0…seat4`
  `--tc` rules. Drag-to-seek on the track is kept alongside.
- **Zoom:** no `#viewpanel`, no `zoomAt`/`setZoom`/`attachMinimap`, no minimap anywhere in `client/`,
  `replay-viewer/` or `tools/` — grep returns nothing. The starter has none either, and the board is a
  fixed `bars × 16` grid always fitted to the frame (`renderer.js:154-177`).

**Rules, resolution order, events — design fidelity.**
- Seeded setup order matches design.md:80 exactly: `shuffle(voices)`, `rand(root)`, `rand(mode)`,
  `bpm = 84 + 6*rand(4)`, `rand(progression)` (`sim.nim:412-425`), one stream.
- Tables match: `ConsonanceW` (`sim.nim:47-49`) = design.md:151; `PulseW` (`:51-54`) = the
  1.0/0.7/0.4 pattern; `motionScore` (`:189-194`) = design.md:161; `densityScore` (`:196-200`) =
  design.md:174-175; `R = 0.40·Ra + 0.35·Rb + 0.25·Rc` (`:297`) = design.md:179; weights
  0.35/0.25/0.25/0.15 (`:55-58`, `:334-339`) = design.md:193.
- The density denominator is `(columns * Voices)` — four voices always, including in the muted call
  (`sim.nim:291`, comment `:272-274`), and `test_sim.nim:342-352` pins it by constructing a grid where
  a three-voice denominator would report `1.0` and the four-voice one must not.
- `mutedGrid` (`sim.nim:341-348`) replaces the voice's bars with `restBar()` and **keeps the bar
  count**, so the muted voice still counts in the novelty mean and the interlock columns — exactly
  design.md:203-206.
- `credits` is `whole − without` with **the identical function on both sides**
  (`sim.nim:350-356`); `test_sim.nim:292-311` asserts exact equality over 50 random grids,
  `:313-322` that muting a silent voice is `0.0` exactly, `:324-340` that a grinding voice goes
  negative. Real evidence: the smoke replay's final credits `[10.82, 5.57, 2.15, −0.99]` — genuinely
  signed.
- Turn resolution: hold-then-open (`openTurn`, `sim.nim:386-400`), `heard := says; says := ["",…]`
  (`:397-398`), `turnsPlayed := turn + 1` on the fourth bar (`:444`), final `turn` event then
  `settle("complete")` (`:445-449`). Edit semantics: `grid[voice][target] = bar` with the hold at
  `grid[voice][turn]` untouched when `target < turn` (`:480`, tested at `test_sim.nim:176-200`).
- Event count `5B + 3` verified twice: asserted at `test_sim.nim:397` and `test_bot.nim:61`, and the
  real 6-bar smoke replay has **33** events = `5·6 + 3`.
- Event JSON shape matches design.md:591-596 field-for-field, including `say`/`text` omitted when
  empty — confirmed against the real replay bytes.
- `results.scores[i] = credit(i)` rounded to 6 decimals (`sim.nim:534`); `results.names` are policy
  names (`:533`).
- Only two `reason` values exist: `"complete"` (`sim.nim:449`) and `"deadline"` (`:519`). No third
  `settle` call site.
- `say` newline collapsing lives on the only live path — `cleanText(...).replace("\n", " ")`
  (`llm.nim:536-537`); `applyBar` itself only `strip()`s (`sim.nim:484`), which is consistent because
  scripted decisions have `say == ""`.

**Player process.**
- `chorus_player.nim:56-84` wraps the whole receive loop in `try/except CatchableError` and falls
  through to `socket.close()` inside its own `try`, exiting 0 — the raid 0.1.3→0.1.4 fix the design
  promises (design.md:777-779). Diffed against `bullwhip_player.nim`: this is the one behavioural
  change plus the `DefaultPrompt` text.
- `docker_smoke.sh:322-345` asserts **every** player container exits 0, and the CI log shows
  `player 0: exit 0` … `player 3: exit 0`.

---

## Could not determine

- **Checklist 7's second sentence — "the baseline's parameters were tuned with a grid harness, not
  guessed."** There is no tuning harness in the tree (`tools/` holds only
  `build_replay_viewer.sh` and `ci/`), and the design note never mentions one. What *is* present is
  `tests/test_bot.nim:71-94`, a 200-**seed** sweep that pins the arpeggio band to `[40, 92]`, asserts
  `pedal < arpeggio` on ≥90 % of seeds and echoes mean/min/max — a regression harness over seeds, not
  over parameters. I also re-derived the design's stated arpeggio figures from the code and they match
  to the digit (density 0.234, 9/16 columns, `Ra = 0.84`), which is evidence the numbers were computed
  rather than guessed. *What would settle it:* a committed sweep script or a recorded sweep log, or a
  line in the design/run log naming the grid that produced these onset sets.
- **`curly.makeRequests(batch, client.timeoutSeconds)` semantics.** The `curly` package is not in the
  sandbox, so I cannot read the signature to confirm the unit of the second argument or the behaviour
  on timeout. The call is byte-identical in shape to the starter's
  (`cogame-bullwhip/src/bullwhip/llm.nim:457`), and the `test` job compiles and runs `chorus/llm`
  green. *What would settle it:* `curly`'s `makeRequests` declaration at the version pinned in
  `nimby.lock`.
- **`whisky.receiveMessage`'s default read timeout.** `chorus_player.nim:58-61` treats a `none`
  return as "connection closed, exiting" and breaks. If whisky's default timeout is shorter than a
  turn (up to ~60 s of LLM wait), a player would exit 0 mid-episode; the game does not care (the prompt
  is already delivered and decisions are server-side), and the `CloseEvent` handler
  (`server.nim:514-521`) just deregisters the socket. Either way it is bounded and exits 0 — the smoke
  shows all four players exit 0 on a ~22 s episode. *What would settle it:* whisky's
  `receiveMessage` signature/default at the pinned version, or a hosted episode log with LLM turns.
- **Whether phase 60 counts fallbacks from the replay's `scripted` flag or from container stdout.**
  This determines how much F1 actually costs. *What would settle it:* the phase-60 prompt's fallback
  counting step.
