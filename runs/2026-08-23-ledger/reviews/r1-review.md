# r1 review — cogame-ledger

Repo: `Metta-AI/cogame-ledger` cloned fresh to `/workspace/review-ledger`.
Reviewed sha: `d5531a17b6e8fd7fb82dfe7e920d75d27551143f` — verified `git log -1` on `main` matches
the sha in the brief (HEAD has not moved).
Design note: `/workspace/coworld-builder/runs/2026-08-23-ledger/design.md` (888 lines; also
committed verbatim at `docs/plans/2026-08-23-ledger-design.md` — `diff` clean).
Starter for provenance diffs: `/workspace/starters/cogame-babel` (read-only mount);
`tools/ci/*` and the three workflows diffed against `/workspace/coworld-builder/templates/`.
Files opened: `src/ledger.nim`, `src/ledger_player.nim`, `src/ledger/{types,sim,llm,server}.nim`,
`tests/{test_sim,test_bot}.nim`, `client/{renderer.js,chrome.css,replay.html,global.html,player.html}`,
`replay-viewer/{config.nims,index.html,static_replay.js,ledger_replay.nim}`,
`tools/build_replay_viewer.sh`, `tools/ci/{docker_smoke.sh,policies.json,viewer_smoke.mjs}`,
`.github/workflows/{ci,coworld-release,coworld-submit}.yml`, `coworld_manifest_template.json`,
`compose.yaml`, `ledger.nimble`, `Dockerfile*` (28 files read, 9 diffed against the starter/templates).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.

## Blocking

**None.** No observation below falsifies a named acceptance-checklist item. Items 1–14 were
each traced to code or to cited CI evidence and are listed under "Traced and consistent".
Findings N1–N9 are note-vs-code or note-vs-test divergences and assertion-strength
observations; none of them is on the checklist, so by the categorisation rule none is blocking.

## Non-blocking

### N1 — the TRUST landmark in the note is arithmetically inconsistent with the note's own formula; the code follows the formula
- Where: `src/ledger/sim.nim:162-169`, `tests/test_sim.nim:172-181`, design note lines 121-127.
- Observed: `trustPayoffs(sent, percent)` computes `arrived = 2*sent`,
  `returned = (arrived*percent + 50) div 100` clamped to `0..arrived`, and returns
  `(6 - sent + returned, 2 + arrived - returned)`. For `s = 6, p = 50`: `arrived = 12`,
  `returned = 6`, payoffs `(6, 8)`.
- Per note: line 126 lists "full trust and a fair split (`s = 6, p = 50`) → 6 / 6". The same
  paragraph's formula and its coin invariant `investor + trustee == 8 + s` give `6 + 8 = 14`
  for `s = 6`, so `6 / 6` is unreachable at `s = 6`; the fair-6/6 point of this formula is
  `s = 4, p = 50`.
- The test states this explicitly and asserts the formula's values:
  `check trustPayoffs(4, 50) == (6, 6)` / `check trustPayoffs(6, 50) == (6, 8)`
  (`tests/test_sim.nim:176-177`), with a comment naming the note's line as the error
  (`tests/test_sim.nim:172-175`). The note's other three TRUST landmarks are honoured:
  `trustPayoffs(6, 0) == (0, 14)` (`:178`), `trustPayoffs(0, 50) == (6, 2)` (`:179`), half-up at
  `s = 1, p = 25` (`:181`). The "fair play pays 6 in all three subgames" pin (note line 111) is
  asserted at `tests/test_sim.nim:211-214` using `meetingPayoffs(sgTrust, 4, 50) == (6, 6)`.
- Consequence observed: none in play — the prompt text spells out the formula, not the landmark
  (`src/ledger/llm.nim:289-306`), and the `mirror` baseline sends 4 / returns 50
  (`src/ledger/llm.nim:153-156`, `214-218`), i.e. it lands exactly on the real 6/6 point.

### N2 — the note's "first-mover counts differ by at most 1" property is neither enforced by the code nor asserted by the test
- Where: `src/ledger/sim.nim:288-298` (assignment), `tests/test_sim.nim:108-134` (test), design
  note lines 96-100 and 800-804.
- Observed: at each asymmetric pairing the schedule builder picks as first mover the member with
  the smaller running `firstCount`, breaking ties on `rng.rand(1.0) < 0.5`, then increments that
  seat's counter (`sim.nim:289-297`). That is exactly the greedy rule the note describes at lines
  97-99. There is no global balancing pass and no assertion of a ±1 bound anywhere in `src/`.
- Per note: line 100 asserts as a property that "across an episode no seat's first-mover count
  differs from another's by more than 1", and the test plan (note line 804) requires the test to
  assert it.
- What the test actually asserts (`tests/test_sim.nim:112-134`), for seeds `[1,7,42,1234]` ×
  rounds `{4,7,14,28}`: for every asymmetric meeting `firstCount[a] <= firstCount[b]` at that
  point in the schedule (the greedy rule re-derived from the stored schedule); for a dilemma
  `a < b`; per seat `firstCount[seat] <= asymmetric[seat]`; and `sum(firstCount) == total`
  asymmetric meetings. It does not assert the ±1 bound.
- *Inference* (not observed from a run — see "Could not determine"): the ±1 bound cannot hold in
  general, because a seat's `firstCount` is capped by its number of asymmetric meetings, which is
  itself a random draw (the subgame is drawn per pairing at `sim.nim:275-279`); a seat drawn into
  few asymmetric meetings can end below another seat by more than one.

### N3 — four `client/renderer.js` functions the note lists as untouched are modified
- Where: `client/renderer.js`; design note lines 602-609.
- Observed: a function-by-function comparison of `client/renderer.js` against
  `/workspace/starters/cogame-babel/client/renderer.js` gives:
  - byte-identical: `makeRenderer`, `loadImages`, `ellipsize`, `hexToRgb`, `shade`, `rgba`,
    `roundRect`, `wrapLines`, `drawParchment`, `makeNameMap`, `applyNames`, `clampName`,
    `isBaselineFiller`, `escapeHtml`, `attachLive`, `seatBlock`, `noteHeight`, `seatColor`,
    `assetUrl`, `roundBase`, `reasonLine`, `drawTag`;
  - changed and named in the note: `describeEvent` (`:911`), `phaseText` (`:1116`),
    `matchHeader` (`:1124`), `updateScorebug` (`:1141`), `updateEndscreen` (`:1185`),
    `buildScrub` (`:1382`), plus the whole scene block `computeLayout`…`drawTag` (`:208-816`);
  - changed and listed by the note as untouched: `renderFeed` (`:961-1041` — new event kinds,
    the per-seat payoff ctx, the RING lines and the memo say-lines), `makeEffects`
    (`:1054-1094` — `speakAt/pickAt` → `roundAt/meetAt/gossipAt`), `stateToView`
    (`:1285-1299` — `glyphs` → `gossip`/`rings`/`round`/`nameOf`), `attachReplay`
    (`:1511-1601` — passes `nameMap` into `buildScrub`, plus a comment), `bindFeedToggle`
    (`:1260-1281` — two `relayout()` calls).
- Per note: line 607-609 says everything outside the scene and the six event-vocabulary helpers
  "is untouched babel code", naming `renderFeed`, `makeEffects`, `bindFeedToggle`, `stateToView`,
  `attachLive`, `attachReplay` in that list. The file's own header (`client/renderer.js:12-18`)
  contradicts the note and says `makeEffects` and "renderFeed's structure" are Ledger's; the
  note's Transport-rules section (note line 627-629) does name the `bindFeedToggle` `relayout()`
  call.
- Scale of the changes, observed: each is confined to the event vocabulary or the two new state
  fields; no starter section is deleted from the page or the CSS (see the Traced section).

### N4 — `client/chrome.css` keeps the `@font-face` block the note says was removed
- Where: `client/chrome.css:9` vs `/workspace/starters/cogame-babel/client/chrome.css:9`;
  design note lines 621-623.
- Observed: `diff` against babel's file yields a single hunk `@@ -441,3 +441,241 @@` — 238 added
  lines, zero removed, zero modified. Lines 1-441 are babel's byte for byte, including the
  `@font-face` block at line 9.
- Per note: "the only starter elements deleted are the wordmark's inner text … and babel's
  glyph-font `@font-face` fallback stack in `chrome.css`". The file is append-only; nothing was
  deleted. (Checklist item 14 requires append-only, which is what the file is.)

### N5 — the replay test asserts the frame count and the final frame, not each intermediate frame
- Where: `tests/test_sim.nim:518-525`; `src/ledger/sim.nim:847-895`;
  `replay-viewer/ledger_replay.nim:30-46`; `src/ledger/server.nim:189-193`.
- Observed: the test plays an episode, calls `replayMatch(live.config, live.events)` and checks
  `frames.len == live.events.len + 1` (`:521`), `$frames[^1].tableStateJson() ==
  $live.tableStateJson()` and the same for `resultsJson` (`:522-523`), and
  `$frames[1].tableStateJson() != $frames[^1].tableStateJson()` (`:525`). Intermediate frames are
  not compared one-by-one against the live sim's state after the same event prefix (the live sim
  does not retain per-tick snapshots, and the replay file deliberately carries no `states`
  array — `src/ledger/server.nim:165-187`).
- Per note: the note's own test plan (lines 826-828) asks for exactly the three assertions that
  are present, so the code matches the note. Checklist item 2's wording is "reproduces the
  recorded per-tick state **frame by frame** … A test asserts it"; the mechanism is satisfied by
  construction (the viewer's `states` come only from `replayMatch`, `ledger_replay.nim:42-45`),
  the assertion covers the count, the endpoint and one inequality.
- Also observed and consistent with the checklist: a tampered `round` event is rejected
  (`tests/test_sim.nim:527-538` against `sim.nim:868-874`), and every event kind round-trips
  through JSON with every field (`tests/test_sim.nim:540-548`).

### N6 — the viewer's ring caption names 2-seat components; the note's "ring" is a component of size ≥ 3
- Where: `client/renderer.js:663-685` (`ringGroups`), `:703-716` (`#ringnote`);
  `src/ledger/sim.nim:437-463` (`ringComponents`, `if component.len >= 3`); design note lines
  199-202 and 671-673.
- Observed: `ringGroups` union-finds every flagged pair and returns every component, with no size
  filter, so `#ringnote` renders `RING: Bolt · Rivet` for a single flagged pair. The sim's own
  `ringComponents` keeps only components of size ≥ 3 and is not called by the viewer.
- Per note: line 199 defines a ring as "a connected component of size `>= 3` in the flagged
  graph"; line 673 says the caption "names the connected component". The feed line
  `RING: Bolt · Rivet (+3.5 coins between them)` (`renderer.js:990-999`) is per flagged pair and
  matches the note's feed spec (line 690) exactly; only the `#ringnote` caption differs.
- No scoring path is involved either way (`resultsJson` reads `ringThreads().len` only,
  `sim.nim:679`).

### N7 — `outMean` is 0.0 when a flagged pair's members have no meetings outside the pair
- Where: `src/ledger/sim.nim:429-435`.
- Observed: `let outMean = if outCount == 0: 0.0 else: outSum / outCount.float`, so a pair whose
  two members have only met each other gets `delta = inMean` and is flagged whenever
  `inMean >= 6.0`.
- Per note: lines 194-199 define `outMean` as "mean of the two members' own payoffs over all of
  their meetings that were *not* with each other" and do not define the empty case.
- Reachability, *inferred*: unreachable in real play — the schedule never repeats a pair in
  consecutive rounds (`sim.nim:260-264`, asserted `tests/test_sim.nim:93-106`), so a pair that has
  met twice has each member carrying at least six other meetings. Reachable only in a
  hand-constructed history.

### N8 — the feed's RING lines and the endcard's ring rows read a module-global set by the last drawn frame
- Where: `client/renderer.js:105-109` (`var latestRings`), `:299` (set in `draw`), `:990-999`
  (feed), `:1243-1256` (endcard).
- Observed: `renderFeed` and `updateEndscreen` take their ring list from `latestRings`, which
  `draw()` overwrites every animation frame from `view.rings`; `results` itself carries only
  `ringPairs` (a count). The coupling is documented in the code at `:105-108`. In a scrubbed
  replay the ring lines therefore reflect the currently drawn frame's ring set rather than the
  frame the feed prefix ends at.
- Per note: lines 688-694 specify the feed line and the endcard ring rows but do not say where
  the pair list comes from; `resultsJson` deliberately carries only the count (note line 512).
- Nothing here touches scores (verified: `resultsJson` and `tableStateJson.seats[].score` are the
  medians, `sim.nim:663`, `sim.nim:720`).

### N9 — the replay cannot distinguish an LLM fallback from a seat that registered scripted
- Where: `src/ledger/llm.nim:637-644` and `:681-684`; `src/ledger/server.nim:349-356`;
  `src/ledger/sim.nim:542`, `:568-569`.
- Observed: `decideAll` sets `Decision.scripted = true` both for a seat whose policy registered
  `PLAYER_SCRIPTED` (`llm.nim:641-643`) and for a seat that exhausted attempt 1 + the retry
  (`llm.nim:681-684`); both land in the same `scriptedA`/`scriptedB` booleans on the `meeting`
  event. The distinguishing evidence is the stdout line
  `ledger: seat N falling back to scripted decision` (`llm.nim:683`), emitted only on the fallback
  path, plus the per-attempt failure line at `llm.nim:677-678`.
- Per note: line 342-343 specifies exactly this — "recorded with `scripted: true` on the meeting
  event and logged as `ledger: seat N falling back to scripted decision`" — so the code matches
  the note. Recorded here so phase 60 knows the count comes from the game log, not the replay.

## Traced and consistent

**Resolution rules**
- `src/ledger/sim.nim:224-231` — `positionMatching(k)` is `(7, k)` plus `((k+i) mod 7,
  (k-i+7) mod 7)` for `i in 1..3`; the circle-method 1-factorization of note step 1, verbatim.
- `src/ledger/sim.nim:246-249` — one seeded permutation `perm` relabels positions to seats (note
  step 2); `:253-265` generates `ceil(rounds/7)` passes, shuffles each pass order, and resamples
  up to 16 times while `order[0] == previous[^1]` (note step 3, including the "then accept"
  escape); `:266-268` truncates to `rounds` (note step 4).
- `src/ledger/sim.nim:275-279` — `rng.rand(99)`: `<50` DILEMMA, `<80` TRUST, else ULTIMATUM
  (0.50 / 0.30 / 0.20, note line 91-93). Empirically asserted to ±0.03 over 200 seeds ×
  28 rounds at `tests/test_sim.nim:136-151`.
- `src/ledger/sim.nim:280-298` — dilemma stores `a = min(seat)`, asymmetric stores `a = first
  mover` (note line 96-100, 446).
- `src/ledger/sim.nim:151-183` — `pdPayoffs` 6/6, 0/10, 10/0, 2/2; `trustPayoffs` as the note's
  formula; `ultimatumPayoffs` `o >= m → (12-o, o)` else `(0,0)`; `meetingPayoffs` dispatches over
  `SubGame`. Whole matrices asserted at `tests/test_sim.nim:154-214`, every payoff in `[0,14]`.
- Strategy method: one `move` per seat per round, second movers commit a rule
  (`src/ledger/llm.nim:289-319` prompt text; `sim.nim:128-133` legal ranges 0..1 / 0..6 / 0..100
  / 0..12 / 0..12), and all eight decide from one snapshot (`server.nim:322-342`).
- Resolution order, step by step: step 1 `server.nim:316-320` → `sim.beginRound` (`sim.nim:487-509`,
  appends the `round` event with all four pairs and `first`); step 2 `server.nim:341-342` →
  `decideAll` (one batch); step 3 `llm.nim:646-680` (retry sub-batch) + `:681-684` (mirror
  fallback) + `llm.nim:609-613` (clamp, logged, not retried); steps 4-8 `server.nim:344-376` →
  `sim.applyRound` (`sim.nim:612-639`: memos first, meetings in pair order 0..3, gossip in seat
  order 0..7 for seats with a note and a defined target, then `closeRound`); step 7's medians and
  rings are derived in `tableStateJson` and write no event (`sim.nim:598-610`, `:707-759`);
  step 8 `sim.nim:606-610` settles `complete`; step 9 `server.nim:384-393`; step 10
  `server.nim:301-315`.
- `src/ledger/sim.nim:207-210` — `maxMeetings(rounds) = ceil(rounds/7)` is a derived constant, no
  enforcement branch (note line 88-89); asserted at `tests/test_sim.nim:81-91`, and the perfect
  double round robin at 14 rounds at `:69-79`.

**Scoring**
- `src/ledger/sim.nim:371-383` — `median` sorts the seat's payoff list; odd → middle, even → mean
  of the two middles, `k == 0 → 0.0`. `resultsJson.scores` carries it and nothing else
  (`sim.nim:663`), `tableStateJson.seats[].score` too (`sim.nim:720`).
- Ring detection is a pure read: `ringThreads` (`sim.nim:407-435`) is called only from
  `resultsJson` for a count (`:679`) and from `tableStateJson` for the drawn threads (`:745-747`);
  no assignment to `payoffs`, `total`, `kind`, `harsh` or `scores` exists anywhere in its call
  graph. `tests/test_sim.nim:395-422` asserts the scores are identical with and without the ring
  pattern, that each score equals the median of that seat's own payoff list, and that computing
  the rings does not move the scores.

**Decision path**
- `src/ledger/llm.nim:626-684` — `decideAll` is bullwhip's `decideAll` ported (compared against
  `/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:419-472`; same structure, same
  `batch.post` / `makeRequests` / `batch[position].url` indexing). All open seats go out in ONE
  `RequestBatch` (`:649-661`), one `makeRequests` call per attempt (`:662`); `for attempt in 0..1`
  is exactly one retry (`:646`), with the corrective hint appended at `:656-659`; seats still open
  after the loop take the `mirror` scripted move (`:681-684`). No per-seat sequencing anywhere in
  `server.nim`'s round loop.
- Batch mapping: `seatForBatchPosition(seats, open, position)` (`llm.nim:617-624`) with the
  reply read as `responses[position]` (`:672-673`); asserted against a shuffled arrival order at
  `tests/test_bot.nim:290-316`.
- Tolerant parse: `extractJsonObject` takes the first `{`…last `}` (`llm.nim:485-495`);
  `parseMoveValue` accepts `JInt`/`JFloat` (half-up)/`JBool`/words `cooperate|c|coop|cooperation`
  / `defect|d|defection` case-insensitively, and numeric strings with `%`, `coins`, `coin`
  suffixes (`:559-601`); out of range is clamped and logged (`:609-613`). Asserted at
  `tests/test_bot.nim:232-274` including prose-around-the-object and the `"maybe"` rejection.
- No credentials ⇒ `client.disabled` at construction (`llm.nim:145-148`), every seat scripted with
  no network wait (`llm.nim:640-644`); asserted under 1 s at `tests/test_bot.nim:203-230`.
  401/403 disables the client (`llm.nim:530-538`), 429 sets `throttled` and rotates the Bedrock
  model (`:539-543`); `us.anthropic.claude-sonnet-4-6` is absent from the candidate list
  (`:100-103`).

**Waits and bounds**
- Player connect: bounded loop to `gameStart + playerConnectTimeoutSeconds`, 200 ms poll
  (`server.nim:258-266`).
- Play deadline: `COWORLD_TIMEOUT_SECONDS` if set, else `config.episodeTimeoutSeconds` (1200,
  `types.nim:55`), times `PlayBudgetFraction = 0.6` (`server.nim:38`, `:288-290`) ⇒ 720 s.
- Pre-round reserve: `RoundReserveSeconds = 70.0` / `ScriptedReserveSeconds = 2.0`
  (`server.nim:43-49`) checked before every `beginRound` (`:304-315`); on trip, `endEarly()` →
  `reason = "deadline"` (`sim.nim:641-647`) and the loop breaks.
- Per HTTP call: `client.timeoutSeconds = config.llmTimeoutSeconds` (30) applied to the whole
  batch (`llm.nim:662`). Artifact POST bounded at 60 s (`server.nim:159`).
- Rate-limit floor: sleeps only the remainder of `minRoundIntervalMs` (doubled once throttled),
  and only when LLM seats exist (`server.nim:386-393`); cert fixture sets it to 0.
- Shutdown: `sleep(500)` then artifacts then `sleep(ShutdownGraceSeconds * 1000)` (20 s) then
  `quit(0)` (`server.nim:228-244`, `:51-55`).
- The only `while true` in the game path is the round loop (`server.nim:300`), and every path out
  of it is a `break` on `sim.done` or the deadline; `finishEpisode` is unconditional after it
  (`:395`). No blocking read: prompts arrive on the websocket handler thread
  (`server.nim:507-521`) and are read from a snapshot under the lock (`:326-329`).
- `grep -rn "while true|sleep\(|readLine|stdin|waitFor" src/` returns only the lines above plus
  the player's receive loop (`src/ledger_player.nim:66-92`), which is wrapped in
  `try/except CatchableError` and exits 0 (note line 566-571).

**Truncation**
- `cleanText` strips then cuts with `runeSubStr(0, limit - 1) & "…"` (`llm.nim:464-471`);
  `singleLine` maps CR/LF (and tab) to spaces and drops other control runes (`:473-483`).
- note ≤ 120 and memo ≤ 400 applied in `parseDecision` (`llm.nim:606-607`, caps at
  `sim.nim:50-51`); prompts cut rune-safely at `MaxPromptLen = 4000` (`server.nim:35`,
  `:514-515`); every quoted error string goes through `cleanText` (`llm.nim:493-494`, `:529`,
  `:531`, `:543`, `:546`, `:554-555`, `:678`).
- Asserted: 500 `é` → exactly 120 runes, valid UTF-8, ends `…`, survives a JSON round trip
  (`tests/test_sim.nim:317-327`); 900 `日` → 400 runes valid UTF-8 (`:329-337`);
  `tests/test_bot.nim:276-288` for the parse path.

**Replay writer**
- `src/ledger/server.nim:165-187` — `protocol`, `names` (aliases), `policyNames`,
  `config{rounds, seed, sampled, schedule}` with the fully expanded schedule
  (`sim.scheduleJson`, `sim.nim:828-843`), `events`, `results`. No `states` in the written bytes;
  `states` is added only by the replay server (`:566-575`) and by the wasm module
  (`replay-viewer/ledger_replay.nim:36-46`), in both cases from `replayMatch`.
- Strict UTF-8 of the produced bytes is checked end-to-end in CI:
  `tools/ci/docker_smoke.sh:287` `json.loads(replay_path.read_bytes().decode("utf-8"))` with
  `SMOKE_REQUIRE_REPLAY_JSON=1` (`:53`), green in run 32670836320 ("replay saved for the viewer
  smoke: … replay.json (6304 bytes)").

**Viewer re-derivation and the wasm shell**
- `replay-viewer/ledger_replay.nim:22-46` parses the replay, rebuilds the config from
  `names`/`seed`/`rounds`, calls `replayMatch(config, events)` and emits one `tableStateJson` per
  frame — the same Nim `sim` module the server runs (`import ledger/sim`, `:11`). No parallel
  recording is read.
- `replay-viewer/config.nims:38-41` — `-s MODULARIZE=1 -s EXPORT_NAME=LedgerReplayModule`, exports
  `_led_*`; `replay-viewer/static_replay.js:138` calls the factory `LedgerReplayModule()` and
  `:94-104` calls `_led_load_replay` / `_led_payload_ptr` / `_led_payload_len` / `_led_error_*`.
  No `Module.onRuntimeInitialized` anywhere. `diff` against babel's four viewer files shows only
  the rename hunks — one starter, shell and link flags together.
- Readiness markers: `data-replay-loaded="true"` is set in `attachReplay` after the first
  synchronous `renderer.draw` (`client/renderer.js:1571-1597` frame loop, attribute at `:1599`; babel's line, unchanged);
  `data-replay-error` is set in `fail()` (`static_replay.js:56`) and removed on success
  (`:107`, `:134`). Both from the bundle's own code paths.
- CI evidence (run **32670836320**, `main`, sha `d5531a1…`, conclusion `success`): job
  `wasm-viewer` `needs: docker-smoke` (`.github/workflows/ci.yml:212`), no `continue-on-error`
  anywhere in `.github/workflows/` (grep: no hits), and the step **"Load the bundle in a real
  browser"** concluded `success` with
  `{"loaded":true,"ms":292,"clock":"ROUND 3 / 6 · SETTLING","scorebug":"Sprocket 5.0 MEDIAN …
  Rivet 6.0 MEDIAN","feed_lines":39}`, `soak: 15s of playback kept advancing`, and
  `scrub readouts: 0%=… 50%="ROUND 3 / 6 · SETTLING" 100%="FINAL — 6 ROUNDS"`.

**Chrome provenance**
- `client/replay.html` — `diff` against babel's page: 17 changed lines, all of them the title, the
  wordmark `BA<span>BEL</span>` → `LED<span>GER</span>`, `BabelRenderer` → `LedgerRenderer`, and a
  9-line block `<div id="gossip-rail"></div>` / `<div id="ringnote"></div>` appended inside
  `#board-wrap` under the banner comment "LEDGER additions to the inherited cogame-babel chrome"
  (`client/replay.html:25-33`). No starter element is removed; every `#layout`/`#stage`/`#topband`/
  `#wordmark`/`#clock`/`#topright`/`#statuschip`/`#feedtoggle`/`#scorebug`/`#board-wrap`/`#table`/
  `#lightpool`/`#grain`/`#endscreen`/`#transport`/`#scrub`/`#play`/`#pos`/`#feed`/`#loading` id
  survives in the same nesting. `replay-viewer/index.html` carries the same block (`:25-31`).
  83 lines vs the starter's 74 — an append, not a rewrite.
- `client/chrome.css` — append-only, single hunk after line 441 (see N4).
- `#viewpanel`: absent from the whole tree (`grep -rn "viewpanel|zoomAt|attachMinimap|setZoom"
  client/ replay-viewer/ tools/` → no hits) and absent from babel too, matching note line 624.
- Transport rules: (a) `relayout()` measures `#transport` and sets `--band` and `--hudscale` on
  `document.documentElement` (`client/renderer.js:1103-1114`), bound to `load` and `resize`
  (`:1113-1114`) and called from `bindFeedToggle` (`:1277`, `:1280`); the CSS defaults live on
  `:root` (`client/chrome.css:452-461`). (b) every HUD layer (`#lightpool`, `#grain`,
  `#endscreen`, `#gossip-rail`, `#ringnote`) is inside `#board-wrap`, the grid row above
  `#transport` (`client/replay.html:20-33`), and `#gossip-rail`/`#ringnote` are positioned inside
  it (`chrome.css:513-521`, `:562-576`). (c) `#endscreen { bottom: var(--band, 0px); }`
  (`chrome.css:509`), shown with the class its rule uses — `container.classList.toggle("show",
  !!show)` (`renderer.js:1187`) against babel's `#endscreen.show { display: flex; }`
  (`chrome.css:381`); every seek runs `setIndex(next, true)` → `updateEndscreen(…, index >=
  events.length && events.length > 0, …)` (`renderer.js:1551-1568`), so scrub-track clicks and
  beat-marker clicks (`:1526-1532`, `:1429-1434`) both take it down. There is no keyboard or
  back/forward seek path in this lineage — `grep` for `keydown`/`popstate` in `client/` and
  `replay-viewer/` returns nothing, in babel too. (d) beats are
  `<button type="button" class="beat-marker …">` with `aria-label` + `title` that seek to their
  event index (`renderer.js:1419-1437`, `:1474`); the six emitted kinds — `beat-meet kind`,
  `beat-meet harsh`, `beat-meet mutual`, `beat-meet broken`, `beat-gossip`, `beat-end death`
  (`:1452-1472`) — each have a CSS rule (`chrome.css:596-635`), and `button.beat-marker` gets the
  reset + `:focus-visible` rules at `:582-595`. `.round-span/.alt/.round-sep` are babel's,
  unchanged (`renderer.js:1400-1414`).
- 360 px legibility: `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }`
  (`chrome.css:478-482`); labels hidden under 640 px (`chrome.css:495-503`, and `.plate-label`
  again under 980 px at `:681`); plaza plates at `Math.max(11, …)` px (`renderer.js:614`,
  `:625`); gossip rail collapsed under 480 px (`chrome.css:556-559`).

**Manifest**
- `game.replay_viewer = {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:14-16`);
  `tools/build_replay_viewer.sh` present, mode 100755 (`git ls-files -s`), babel's hook with the
  renames plus the `mkdir -p "$(dirname …)"` ecos fix (`tools/build_replay_viewer.sh:44-48`); no
  `/client/replay` is declared as the platform viewer (the only occurrence of the string is prose
  in the `global` protocol text at line 243, which names the static bundle as the viewer).
- `num_agents: 8` in `variants[0].game_config`, `variants[1].game_config` and
  `certification.game_config`; `len(certification.players) == 8`,
  `len(certification.game_config.players) == 8`; cert `seed: 7`, `rounds: 6`,
  `minRoundIntervalMs: 0`, all three declared runnables occupy at least one cert slot.
- `game.docs.readme = {"type":"text","value":…}` and `game.docs.pages = [{id,title,content{type,
  value}} × 2]` (`rules.md`, `strategy.md`); `game.protocols` carries both `player` and `global`.
- `config_schema` `additionalProperties: false` with `tokens`/`players` minItems=maxItems=8,
  `num_agents` min=max=8, `rounds` 4..28 default 14, `episodeTimeoutSeconds` default 1200,
  `minRoundIntervalMs` default 20000, `llmTimeoutSeconds` default 30 — matching `types.nim:51-61`
  and `types.nim:63-96`. `results_schema` matches `resultsJson` field for field with
  `scores.items.minimum = 0` and `reason` enum `["complete","deadline"]`; `resultsJson` only ever
  emits those two because `finishEpisode` runs after a settle (`server.nim:307-315`, `:378-382`,
  `sim.nim:478-485`).
- `episode_timeout_minutes: 20`, `env.ANTHROPIC_API_KEY_URI = secret://coworld/ledger/anthropic_api_key`,
  `source_url`, `owner`, 7 tags.

**Workflows and scaffold**
- All three workflows are `coworld-builder/templates/*` with only the `<slug>`/`<IMAGE>`/`<SEATS>`
  substitutions, plus one addition in `ci.yml` (`--soak 15` and its comment, `:306-314`).
- `coworld-release.yml` order: `coworld build` (`:159`) → `coworld certify` (`:173`) → upload the
  policies (`:206`) → `coworld upload-coworld` (`:309`) → `coworld secret put` (`:358`).
- `tools/ci/docker_smoke.sh` mode 100755, template-identical apart from the substitution hunks,
  with the four seat-count invariants each exiting non-zero and prefixed `SEAT-COUNT FAIL:`
  (`:110-118` missing, `:119-125` positive integer, `:129-134` `len(certification.players)`,
  `:135-140` `len(certification.game_config.players)`, `:146-151` the independent `SMOKE_SEATS`
  cross-check). `grep -i "SEAT-COUNT"` over the full log of run 32670836320: no hits.
- `tools/ci/policies.json` — four policies: `ledger-reputation` (`PLAYER_PROMPT`),
  `ledger-broker` (a *different* `PLAYER_PROMPT`) carrying
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:15`), `ledger-mirror`
  (`PLAYER_SCRIPTED=mirror`), `ledger-shark` (`PLAYER_SCRIPTED=shark`).
- The checklist's placeholder gate over the five files exits 0 (run: no matches for
  `<slug>|<IMAGE>|<SEATS>`). The four documented residue names survive as expected:
  `<cow_id>`/`<sha>` (`ci.yml:202`), `<run_id>` (`coworld-release.yml:21`,
  `coworld-submit.yml:17`), `<name>:vN` (`coworld-submit.yml:31`).

**Tests and CI**
- Run **32670836320** on `main` at the reviewed sha: conclusion `success`; jobs `test`,
  `docker-smoke`, `wasm-viewer` all `success`, every step `success`
  (`gh run view … --json jobs`).
- "No test loosened during this run": `git log --oneline -- tests/` shows the test files entering
  at `728e57e`. The history contains a repo re-bootstrap (`f0deb93` "Initial commit: .gitignore",
  whose parent is `de5ab5d`, deletes the whole tree and it is re-committed above it), so I
  compared the two generations directly: `git diff de5ab5d:tests/test_sim.nim HEAD:tests/test_sim.nim`
  and the same for `test_bot.nim` are both **empty** — byte-identical, no assertion removed, no
  tolerance widened, no skip added. No `skip`/`xfail`/`t.Skip` token exists in `tests/`.
- Sim units present as the note plans them: schedule (`test_sim.nim:52-151`), payoff kernels
  (`:153-221`), median (`:223-251`), conduct (`:253-279`), gossip incl. rune truncation
  (`:281-337`), rings never scoring (`:339-422`), legality (`:424-483`), endings (`:485-515`),
  replay (`:517-560`), determinism (`:562-584`).
- Baselines: full episodes for seeds `[1,7,42,1234]` × {8 mirror, 8 shark, 4/4} with every move
  inside `legalMoveRange`, every payoff in `[0,14]`, `reason == "complete"`, under 5 s
  (`test_bot.nim:60-87`, driven through `scriptedAction` at `:23-49`); legality for every
  (subgame, role) over 20 seeds × 21 rounds (`:95-116`); mirror reciprocation < 0.25 against
  sharks and > 0.9 among mirrors (`:133-157`).
- The end-to-end "episode writes a replay" evidence is CI's `docker-smoke`, not a Nim test — the
  note's test plan also places it there (note lines 852-859): the smoke plays one real episode in
  raw docker with the cert seat mix, asserts the game and every player container exited 0, and
  parses the replay as strict UTF-8 JSON.

**Both name spaces**
- Agents see aliases only: observations are built from `sim.names` (`llm.nim:248-249`, used
  throughout `userPrompt`), and the player socket is redacted to the seat's own tallies
  (`server.nim:115-139`). Spectators get `policyNames` alongside (`server.nim:92-98`, `:109`),
  the replay carries both (`server.nim:177-178`), and the viewer maps aliases → policy names for
  non-baseline seats via babel's untouched `makeNameMap`/`isBaselineFiller`
  (`renderer.js:825-865`). `resultsJson.names` carries policy names (`sim.nim:662`), the final
  player frame carries aliases (`server.nim:210-219`).

## Could not determine

- Whether the note's ±1 first-mover bound (N2) actually holds for any concrete seed. The sandbox
  has no Nim toolchain (`which nim` → nothing), so I could not run `nim c -r tests/test_sim.nim`
  with an added `max(firstCount) - min(firstCount) <= 1` assertion. What would settle it: that
  one-line assertion run over a few hundred seeds in the `test` job.
- Whether the 16-attempt resample cap (`sim.nim:262`) can ever fall through and place a pair in
  consecutive rounds for a production (unpinned) seed. The test covers four fixed seeds and passes;
  the fall-through probability is `(1/7)^16` per pass boundary by inspection, but that is a
  probability argument, not an observation. What would settle it: a sweep over N seeds asserting
  the no-consecutive property, or an assertion on the attempt counter.
- The wait bound inside `writeCogameUri` for the non-POST artifact path (`server.nim:163`).
  `bitworld/runtime` is a dependency (`nimby.lock`), not vendored in this tree, so I could not read
  its timeout; the POST branch is explicitly bounded at 60 s (`server.nim:159`). This is inherited
  from babel unchanged. What would settle it: reading `bitworld/runtime`'s `writeCogameUri`.
- Whether the `0%` scrub readout in the CI viewer-smoke log (`"ROUND 3 / 6 · SETTLING"`) reflects a
  seek. Reading `tools/ci/viewer_smoke.mjs:430-441`, the `0%` entry is the pre-existing readout and
  not a click (only 50 % and 100 % are clicked), so the log is consistent with a working seek — but
  I did not exercise a 0 % seek. What would settle it: a headless run clicking the track's left
  edge and reading `#clock`.
