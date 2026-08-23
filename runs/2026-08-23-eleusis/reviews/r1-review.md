# r1 review — 2026-08-23-eleusis

Repo: `/workspace/cogame-eleusis` @ `529eb6872a91812eb2910b13a691d21e43b7fc05` (whole tree read as a
fork of `/workspace/starters/cogame-bullwhip`; no prior round exists, so nothing is carried forward).
Files read: 34 (`src/eleusis.nim`, `src/eleusis/{types,sim,llm,server}.nim`, `src/eleusis_player.nim`,
`tests/{test_sim,test_bot}.nim`, `client/{chrome.css,renderer.js,replay.html,global.html,player.html}`,
`replay-viewer/{config.nims,eleusis_replay.nim,static_replay.js,index.html}`,
`tools/build_replay_viewer.sh`, `tools/ci/{docker_smoke.sh,viewer_smoke.mjs,policies.json}`,
`.github/workflows/{ci,coworld-release,coworld-submit}.yml`, `coworld_manifest_template.json`,
`Dockerfile`, `compose.yaml`, `eleusis.nimble`, `data/*`, plus the starter counterparts diffed
byte-for-byte and the CI log for run 32659167800).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the
one-parallel-batch rule).

## Blocking

**None.** I could not find an observation that falsifies a named checklist item. Every item
1–14 was traced to code and/or cited CI evidence; the results are in *Traced and consistent*.
The deviations I did find are all from the design note's prose, not from the checklist, and are
listed as non-blocking with the reasoning shown.

## Non-blocking

### N1 — an LLM-failure fallback is recorded only on stdout; the replay event still says `scripted: false`
- Where: `src/eleusis/llm.nim:580-583`, `src/eleusis/server.nim:326`, `src/eleusis/server.nim:329-336`,
  `src/eleusis/sim.nim:711`/`726-735` (the `scripted` field on the event).
- Observed (traced): `decideAll` ends with
  ```nim
  for index in open:
    let seat = seats[index]
    echo "eleusis llm: seat ", seat, " falling back to scripted decision"
    result[index] = scriptedAction(sim, seat, skOpenbook)
  ```
  (`llm.nim:580-583`). The returned `Decision` object (`llm.nim:39-44`) has no field saying it
  came from the fallback. The server then computes
  `let wasScripted = scripted[seat] != skNone or client.disabled` (`server.nim:326`) — i.e. from
  the *seat's declared* policy and the client's global disabled flag only — and passes that as the
  `scripted` argument into `applyResearch`/`applyAnswers` (`server.nim:330`, `:336`), which is what
  lands on the `experiment`/`skip`/`answer` event (`sim.nim:711`, `:732`, `:761`) and therefore in
  the replay (`sim.nim:1027`, `:1031`, `:1055`). So a seat that is LLM-driven, has credentials, and
  whose reply failed twice records `"scripted": false` on an openbook decision.
  The separate path at `server.nim:337-349` (the sim itself refusing the decision) *does* pass
  `true`.
- Checklist item: 8 — "…then falls back to the scripted move — and the fallback is recorded so
  phase 60 can count it."
- Why non-blocking: the fallback **is** recorded — on stdout, in exactly the string
  `eleusis llm: seat N falling back to scripted decision`, which is the string
  `prompts/60-verify.md` check 5 greps for (`grep -nE 'falling back|…'`). The design note itself
  names the log line as the recording mechanism (design.md:254-255). The item does not say
  "recorded in the replay".
- Concrete consequence to be aware of: phase 60 check 4's replay-side counter
  (`jq '[.events[]|select(.fallback==true)]|length'`) reads a field this game never emits, and the
  nearest field it does emit (`scripted`) reads `false` for exactly the case check 4 wants to
  count. Behaviour is inherited verbatim from the starter
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:296`,
  `.../llm.nim:471-472`), so this is starter parity, not a fork regression.

### N2 — a slot that never delivers a prompt does not play `openbook`; it plays LLM-driven with an empty operator block
- Where: `src/eleusis/server.nim:575-576`, `server.nim:250-258`, `src/eleusis/llm.nim:537-543`,
  `src/eleusis/llm.nim:325-329`.
- Observed: `state.scripted = newSeq[ScriptKind](config.players.len)` (`server.nim:576`) leaves every
  slot at `skNone` (the first enum value, `llm.nim:35`) and `state.prompts` at `""`
  (`server.nim:575`). Only a `{"type":"prompt"}` frame changes them (`server.nim:494-496`). The
  connect wait at `server.nim:250-258` is bounded by `playerConnectTimeoutSeconds` and then simply
  proceeds. In `decideAll`, the scripted short-circuit is
  `if kind != skNone or client.disabled:` (`llm.nim:539`), so a never-connected seat with
  credentials present goes to the LLM with `prompts[seat] == ""`, which makes `operatorBlock`
  return `""` (`llm.nim:326-327`) — an LLM decision with no operator guidance, not the openbook
  baseline.
- Design says: "A slot that never delivers a prompt (player pod never connected within
  `player_connect_timeout_seconds = 180`) plays `openbook` for the whole episode." (design.md:255-257).
- Why non-blocking: checklist item 5 asks that the wait be bounded (it is — 180 s, `server.nim:250`)
  and that the episode advance (it does). No checklist item names this behaviour. With no
  credentials the note's statement holds exactly, because `client.disabled` is then true
  (`llm.nim:141-144`).

### N3 — three chrome helpers the note calls "kept verbatim" are absent, and most of the named chrome functions are modified rather than byte-identical
- Where: `client/renderer.js` (whole file), compared function-by-function against
  `/workspace/starters/cogame-bullwhip/client/renderer.js`.
- Observed (mechanical comparison of each named function body):
  - byte-identical: `isBaselineFiller` (`renderer.js:573`), `makeNameMap` (`:577`),
    `applyNames` (`:603`), `clampName` (`:611`), `bindFeedToggle` (`:975`), `ellipsize`, `roundRect`.
  - modified: `renderFeed`, `blockHead`, `escapeHtml` (only `String(text)` added, `:744`),
    `updateScorebug`, `updateEndscreen`, `reasonLine`, `buildScrub`, `attachLive`, `attachReplay`,
    `makeEffects`, `matchHeader`, `stateToView`, `playerFrameToState`, `describeEvent`.
  - removed entirely: `wrapLines`, `drawBubble`, `peakOrders` (bullwhip has all three; eleusis has
    none of them). `relayout`/`bindRelayout` are new (`renderer.js:1015`, `:1027`).
- Design says: "The chrome half of `client/renderer.js` is kept verbatim: … `buildScrub`,
  `attachLive` / `attachReplay` and their pacing loop, `makeEffects`, `ellipsize` / `roundRect` /
  `wrapLines` / `drawBubble`." (design.md:583-590).
- Why non-blocking: checklist item 14's provenance tests are on `chrome.css` byte-identity and on
  the page being the starter's page plus an appended block — both hold (see *Traced*). The
  item does not require function-level byte-identity of `renderer.js`. Every modification I read
  is a state-shape rename (`seat.cost`→`seat.score`, `week`→`round`) or the new game's content;
  `wrapLines`/`drawBubble` were the speech-bubble helpers of the conveyor scene, which the note
  itself authorises replacing, and `peakOrders` fed a "peak order" endcard column the fork drops.

### N4 — no variant and no certification fixture validates against `game.config_schema` as written
- Where: `coworld_manifest_template.json` — `game.config_schema.required` is `["tokens","players"]`;
  `variants[*].game_config` (standard/open-science/closed-shop) and `certification.game_config`
  carry `players` but no `tokens`.
- Observed: running each `game_config` through a Draft 2020-12 validator against
  `game.config_schema` produces `'tokens' is a required property` for all four.
- Design says: "`additionalProperties: false`, and every variant + the cert fixture must validate
  against it." (design.md:690).
- Why non-blocking: not on the checklist (item 10 covers `game.docs` and `game.protocols` only,
  and both are correct — see *Traced*). `tokens` is injected by the platform at run time, and the
  starter's manifest has the identical shape
  (`/workspace/starters/cogame-bullwhip/coworld_manifest_template.json`: same
  `required: ["tokens","players"]`, its one variant also omits `tokens`). Everything else in the
  four configs validates: `num_agents` 5, `players` `minItems/maxItems: 5`,
  `additionalProperties: false` with no stray keys.

### N5 — `docker_smoke.sh` prints `results.reason` but does not assert it is in `{complete, deadline}`
- Where: `tools/ci/docker_smoke.sh:308-310`:
  ```python
  reason = results.get("reason") or results.get("end_reason")
  if reason is not None:
      print(f"episode end reason: {reason}")
  ```
- Design says: test item 18 — "asserts the game container exits 0, `results.json` is valid UTF-8
  JSON with 5 `names`/`scores`, `reason ∈ {complete, deadline}`…" (design.md:820-824).
- Why non-blocking: not on the checklist; the file is `templates/tools/ci/docker_smoke.sh` verbatim
  apart from the fork addition (I diffed them — the only other differences are the three
  substitutions). The CI log for run 32659167800 shows `episode end reason: complete`, so the
  intent is met in fact if not by assertion.

### N6 — `sim.capText` truncates without the `…` marker the note's field table specifies
- Where: `src/eleusis/sim.nim:638-645`:
  ```nim
  if result.runeLen > limit:
    result = result.runeSubStr(0, limit)
  ```
  versus `src/eleusis/llm.nim:459-466`:
  ```nim
  result = result.runeSubStr(0, limit - 1) & "…"
  ```
- Design says: `hypothesis` "**≤ 120 runes**, newlines → spaces, truncated with `…` on a rune
  boundary" (design.md:283).
- Why non-blocking: checklist item 9 requires only rune-boundary truncation, and both procs use
  `runeSubStr`. On the live LLM path the reply passes through `cleanText` first (`llm.nim:501-503`),
  so the `…` is present and `capText` is then a no-op. Only a direct sim call (tests, replay
  restore) sees the un-marked cut. `tests/test_sim.nim:465-487` asserts 120/600 **runes** and
  `validateUtf8() == -1` on the whole `$payload`.

### N7 — `endEarly` leaves an undisclosed pending result *pending*, not hoarded
- Where: `src/eleusis/sim.nim:809-828`. `endEarly` discards the open test and calls
  `settle("deadline")`; it never touches `sim.seats[seat].pending`, so the result is not moved into
  `secrets` and `seats[].hoarded` is not incremented.
- Design says: "pending undisclosed results stay hoarded" (design.md:211-212).
- Why non-blocking: economically identical (a pending result was never on the board and never
  earned credit); only the `hoarded` counter and the spectator drawer differ. Not on the checklist.

### N8 — `endEarly` leaves the discarded test's `answers` in `benchStateJson` with `open: false`
- Where: `src/eleusis/sim.nim:816-827` sets `sim.test.open = false` and rolls back
  `correct`/`answered`, but leaves `sim.test.answers`/`answered[]` populated;
  `sim.nim:942-975` then renders that test with `"open": false` and per-seat `correct` counts.
- Observed consequence: `updateTestPanel` (`client/renderer.js:846-889`) treats `!test.open` as
  "settled" and reveals the truth stamps and pip correctness for a test that scored nobody.
- Why non-blocking: cosmetic, and only on the `deadline` path. `resultsJson.tests` correctly
  excludes it (`sim.nim:870` reads `testsDone`, which `endEarly` does not increment), and
  `tests/test_sim.nim:349-378` asserts that.

### N9 — the degenerate test top-up does not exclude `used`, and can in principle repeat a strip
- Where: `src/eleusis/sim.nim:504-520`. The balanced draw at `:489-503` correctly excludes
  `sim.used ∪ sim.usedTest`. The top-up pool is built with
  `if strip notin chosen and strip notin sim.usedTest` (`:510`) — `sim.used` is **not** excluded —
  and the final loop `while chosen.len < testStrips: chosen.add(stripOfIndex(index mod StripUniverse))`
  (`:518-520`) filters nothing at all and can add a strip already in `chosen`.
- Design says: strips must "have never been the subject of any experiment in this episode" and
  "have not appeared in an earlier test", and the draw must be `testStrips/2` PASS + `testStrips/2`
  FAIL (design.md:118-123).
- Why non-blocking (inference, not observed at run time): both branches are unreachable until one
  side of the 256-strip universe is nearly exhausted — with the shipped defaults (24 rounds × 5
  seats = at most 120 experiments, `MinPassFraction = 0.10` ⇒ ≥ 25 strips per side) the pools are
  never short. The code comments say as much (`:504-506`). A repeated strip inside one test would
  also let one author be paid twice for the same `(strip, confirmer)` pair, because the citation
  loop is keyed on the *index* into `test.strips` (`sim.nim:586`). Not on the checklist; would need
  a crafted episode to reach.

### N10 — the play deadline is disabled entirely if `episodeTimeoutSeconds <= 0`
- Where: `src/eleusis/server.nim:273-286`. If `COWORLD_TIMEOUT_SECONDS` is absent,
  `timeoutSeconds = config.episodeTimeoutSeconds.float`; if that is `<= 0` then
  `playDeadline = 0.0` and the check at `:300` (`if playDeadline > 0.0 and …`) never fires.
  `types.nim:99-152` (`update`) validates `rounds`, `testEvery` and `testStrips` but not
  `episodeTimeoutSeconds`.
- Why non-blocking: `game.config_schema.episodeTimeoutSeconds` has `minimum: 60` and
  `additionalProperties: false`, so the platform cannot deliver 0; the default is 1200
  (`types.nim:90`). The loop would still terminate normally at `rounds` rounds. Labelled an
  inference — I did not run it.

### N11 — the note's worst-case batch arithmetic omits the retry batch
- Where: `src/eleusis/llm.nim:544` (`for attempt in 0 .. 1`) and `:556`
  (`makeRequests(batch, client.timeoutSeconds)`).
- Observed: a turn whose replies all fail sends two parallel batches, each bounded at
  `llmTimeoutSeconds = 40`, so a pathological turn costs ≤ ~80 s, not 40 s.
- Design says: "a pathological episode where every batch burns its full timeout reaches 720 s after
  ~18 batches" (design.md:242-244).
- Why non-blocking: item 5 is about boundedness and settling inside 60 % of the timeout. Both hold:
  the retry is a second *parallel* batch (not sequential calls), the deadline is re-checked before
  every turn (`server.nim:300`), and the worst case simply settles `deadline` after ~9 turns instead
  of ~18 — which the design already declares an acceptable `results.reason` (design.md:208-216) and
  the results schema permits.

### N12 — `benchStateJson` carries five keys the note's example frame does not, and `test.correct` can be null
- Where: `src/eleusis/sim.nim:989-1010` emits `decided`, `experimentCost`, `knowledgePool`,
  `citePot` and `closest` in addition to the note's list (design.md:437-455); `sim.nim:964-966`
  emits `null` in `test.answers` and `test.correct` for an unanswered seat, where the note's
  example shows `"correct":[4,3,5,2,4]`.
- Why non-blocking: purely additive, and the manifest's `global` protocol text documents the real
  shape including `decided` and the three economy constants
  (`coworld_manifest_template.json` `game.protocols.global.value`). The viewer tolerates the nulls
  (`renderer.js:872-878` guards `row && row[i]`). Not on the checklist.

## Traced and consistent

### Resolution rules — research rounds (note items 1–5)
- `sim.nim:392-398` (`openRound`) — emits `evRound` with the round number and clears
  `decided[0..4]`. `sim.nim:425-431` (`pendingSeats`) returns undecided seats in seat order.
- `sim.nim:769-786` (`applyResearch`) — raises `EleusisError` on `done`, bad seat, wrong phase,
  a second decision by the same seat, and (via `normaliseStrip`, `:163-182`) a malformed strip;
  then `recordTalk` → `discloseNow` → `runExperiment`, in that order.
- **Documented deviation, verified as documented.** `sim.nim:11-20` states that disclosure and
  experiment are applied *per seat as the decision lands* rather than all-disclosures-then-all-
  experiments. I traced the equivalence claim: `discloseNow` (`:657-703`) reads only that seat's
  `pending` and `sim.board`; `runExperiment` (`:705-738`) writes only that seat's `log`/`pending`/
  `spend` and `sim.used`. Since the server applies the batch in seat order 0..4
  (`server.nim:324`), the duplicate check at `:666-669` resolves in the same seat order under both
  orderings, and no experiment can change any other seat's disclosure. The observable difference is
  the **event stream order** (`round, disclose0, experiment0, disclose1, …` instead of
  `round, disclose0..4, experiment0..4`) — which is exactly what buys one replay frame per event
  (`sim.nim:19-20`).
- Charging: `sim.nim:717-719` — `spend += experimentCost`, `experiments += 1`, `used.incl(strip)`,
  exactly once per non-empty strip; `""` takes the `evSkip` branch at `:707-714` and charges
  nothing. `tests/test_sim.nim:147-174` asserts both, plus the double-decision raise.
- Pipelined disclosure: `runExperiment` sets `pending` (`sim.nim:722`) and only the *next* turn's
  `discloseNow` consumes it (`:660-662`), so a rival reading `sim.board` this round sees last
  round's corkboard. `tests/test_sim.nim:176-211` walks a full publish/duplicate/hoard round and
  asserts the disclose-event mode sequence `["publish","duplicate","hoard"]`.
- Duplicate handling: `sim.nim:665-683` — a publish of a strip already on the board becomes
  `mode = "duplicate"`, `author = -1`, `duplicate = true`, `published` is **not** incremented, and
  the fact still goes on the board as a confirmation. The citation loop then skips it explicitly
  (`sim.nim:597`: `if fact.duplicate or fact.author < 0 or fact.author == seat: continue`).
- `sim.nim:552-559` (`advanceTurn`) — `roundsPlayed` increments per research round, and a test opens
  when `round mod testEvery == 0 or round >= rounds`. I hand-checked `rounds=24,testEvery=6` (tests
  after 6/12/18/24 = 28 batches) and the cert fixture `rounds=6,testEvery=3` (tests after 3 and 6 =
  8 batches), and the non-divisible case `rounds=7,testEvery=6` (tests after 6 and 7).

### Resolution rules — prediction tests (note items 6–10)
- Balanced held-out draw: `sim.nim:485-524` builds `passPool`/`failPool` from strips in neither
  `sim.used` nor `sim.usedTest`, shuffles both **from `sim.rng`** (the episode stream seeded at
  `initSim`, `sim.nim:413`), takes `testStrips div 2` from each, shuffles the result, and derives
  `truth` by `evaluate`. `openTest` (`:526-550`) adds the strips to `usedTest`, snapshots
  `testBoardCut = board.len`, and emits the `evTest` event carrying `strips` and `truth`.
  `tests/test_sim.nim:213-241` asserts 3 PASS / 3 FAIL, `strip notin sim.used`, `truth` matching
  `evaluate`, and that test 2 holds out test 1's strips.
- Answer collection: `applyAnswers` (`sim.nim:788-807`) runs `recordTalk` → `discloseNow` →
  `recordAnswer`, so the last research round's pending result always gets its decision *before* the
  answers score — and, because `discloseNow` appends to `sim.board` at index ≥ `testBoardCut`, a
  publication made on the test turn cannot earn credit in that same test. Wrong-length vectors raise
  at `:801-804` and again at `:742-745`.
- Knowledge pool: `sim.nim:566-579` — `pool[seat] = knowledgePool * correct[seat] / max(1, total)`.
  Sums to `knowledgePool` when anyone is right and to 0 when nobody is. `tests/test_sim.nim:244-270`
  hand-computes a 5-seat case (`[6,3,0,0,0]` → `20·6/9`, `20·3/9`, 0) and the barren case.
- Citation settlement: `sim.nim:586-613`. For each `(test strip index, seat)` where the seat
  answered *and* was correct, the loop scans `0 ..< min(testBoardCut, board.len)` — so **only facts
  published before the test opened** — skipping duplicates, authorless facts, and `fact.author == seat`
  (self-citation impossible by construction), requiring `hamming(fact.strip, strip) == 1`
  (`hamming` at `:195-201`), and de-duplicating with `if fact.author notin authors` so an author is
  paid **at most once per (strip, confirmer)** however many of its facts support the strip. The pot
  is `citePot / authors.len` split equally (`:606-608`), credited to the author and tagged onto the
  supporting board card's `cites`. `tests/test_sim.nim:272-323` is a hand-built board that exercises
  each clause separately and pins the exact numbers (author 1 = 0.25, author 2 = 0.75, self-citer =
  0.0, Hamming-2 = 0.0, post-cut publication = 0.0, three citations, `correctAll == [2,1,0,0,0]`).
- Scoring: `sim.nim:433-434` — `score = knowledge + credit − spend`; higher is better and may be
  negative. `tests/test_sim.nim:325-346` asserts the identity and `score < 0` for a spend-only seat.
  `resultsJson` (`:832-876`) carries policy names, `rounds = roundsPlayed`, `maxRounds`,
  `tests = testsDone`, `ruleId`, `rule`, `closest`, `closestName`, `reason`.
- Endings: `settleTest:632-636` — `complete` when `test.round >= config.rounds`, otherwise
  `round += 1; openRound()`. `endEarly:809-828` — idempotent (`:814-815`), rolls the open test's
  `correct`/`answered` back out, sets `open = false`, and settles `"deadline"`. `reason` is only ever
  one of those two strings.
- `closestSeat` (`sim.nim:452-465`) — highest `correct/answered`, ties to the higher score, then the
  lower seat index (the loop only replaces on a strict improvement); `-1` when nobody answered.

### The catalogue and the machine
- `sim.nim:205-232` (`catalogue`) enumerates 4+4+8+16+12+4+4+2+2+12 = **68** instances in the note's
  template order. `tests/test_sim.nim:43-68` pins the boundary indices (0,3,4,8,9,16,32,44,48,52,54,56,67)
  and asserts `describeRule` is unique across all 68.
- `passes` (`sim.nim:234-268`) implements each predicate as the note's table specifies, including
  `rkAdjacent` with `c = d`, `0` counting as even for `rkParity`, `rkBefore` requiring both colours,
  and `rkMoreThan` failing on a tie. `tests/test_sim.nim:79-119` covers all ten families.
- `pickRule` (`sim.nim:336-339`) = `initRand(seed*7919 + 17)` → shuffle → first instance with
  `passFraction ∈ [0.10, 0.90]`; `initSim` (`:413-416`) runs the *same* stream via `pickRuleWith`
  and then keeps that `rng` for every test draw, so `pickRule(seed).id == initSim(seed).ruleId`.
  `tests/test_sim.nim:121-134` checks determinism and the band over 200 seeds.
- `stripOfIndex`/`indexOfStrip` (`sim.nim:148-161`) are lexicographic over `R<B<G<Y`; round-tripped
  over all 256 in `tests/test_sim.nim:70-77`.

### Decision path (checklist 8 + the one-parallel-batch rule)
- **One batch per turn.** `server.nim:307-321` snapshots the sim under the lock, releases it, and
  calls `client.decideAll(simCopy, seats, prompts, scripted)` once. `llm.nim:546-556` builds a single
  `RequestBatch` containing every open seat and issues one
  `client.curl.makeRequests(batch, client.timeoutSeconds)`. There is no per-seat request loop
  anywhere. `curly.makeRequests` is `{.raises: [].}` and takes a per-request timeout in seconds
  (`/root/.nimby/pkgs/curly/src/curly.nim:711-715`).
- **Tolerant parse.** `extractJsonObject` (`llm.nim:386-398`) takes `text[find('{') .. rfind('}')]`,
  so surrounding prose and markdown fences are tolerated; on failure it quotes the first 160 chars
  of the reply. `tests/test_bot.nim:171-172` asserts `"prose {…} tail"` parses.
- **Tolerant on shape, strict on legality.** `parseDecision` (`llm.nim:496-521`) accepts
  `publish` as bool/int/float/string (`parseBoolish:468-479`), answers as `PASS/FAIL/P/F/true/false`
  in either case or as JSON booleans (`parseAnswer:481-494`), and normalises the strip through
  `normaliseStrip`. Wrong answer-vector length, an unrecognised answer, a non-object payload, a
  missing `experiment`, `"RBG"` and `"RBGZ"` all raise — `tests/test_bot.nim:122-159` asserts each.
- **Legality before acceptance.** `llm.nim:566-573` applies the parsed decision to `var probe = sim`
  (a value copy) and only accepts it if the probe does not raise, so an illegal move never reaches
  the live sim and the retry carries the hint.
- **Exactly one retry.** `for attempt in 0 .. 1` (`llm.nim:544`), with
  `"Your previous reply was invalid. Respond with ONLY the requested JSON object and nothing else."`
  appended on `attempt > 0` (`llm.nim:551-553`).
- **Then `openbook`.** `llm.nim:580-583`, plus a second belt in the server at `server.nim:337-351`
  if the sim itself refuses the decision, and a third `except` so that even a refused fallback only
  leaves the turn open (which the play deadline then settles).
- **No credentials ⇒ all scripted, no network wait.** `newLlmClient` (`llm.nim:136-144`) sets
  `disabled = true` and logs when neither the Bedrock env pair nor `ANTHROPIC_API_KEY` nor
  `ANTHROPIC_API_KEY_URI` resolves; `decideAll:539` then takes the scripted branch for every seat and
  `:545` breaks out of the attempt loop before any request is built.
  `tests/test_bot.nim:104-120` asserts `client.disabled`, five scripted decisions matching
  `scriptedAction`, and that the round resolves. CI run 32659167800 shows the line
  `eleusis llm: no LLM credentials; using scripted fallback` and a complete episode.
- Bedrock candidate list `llm.nim:96-99`: haiku first, `us.anthropic.claude-sonnet-4-6` absent, as
  the note requires; `BEDROCK_MODEL` pins a single id.

### Every wait and its bound (checklist 5)
| wait | where | bound |
|---|---|---|
| player connect | `server.nim:250-258` | `playerConnectTimeoutSeconds` = 180 (`types.nim:93`), `sleep(200)` poll, then plays on |
| play deadline | `server.nim:280-286`, checked at `:300` **before every batch** | `gameStart + episodeTimeoutSeconds × PlayBudgetFraction`; `PlayBudgetFraction = 0.6` (`server.nim:241`) ⇒ 720 s of 1200; `endEarly()` then settles `deadline` |
| LLM batch | `llm.nim:556` | `client.timeoutSeconds = config.llmTimeoutSeconds` = 40 (`llm.nim:119`, `types.nim:96`) |
| batch spacing | `server.nim:317`, `:357-360` | floor measured from `batchStart`, i.e. between the **starts** of consecutive batches; `minBatchSpacingMs` = 12000 (`types.nim:91`) |
| artifact write | `server.nim:145-155` | POST path bounded at 60 s explicitly; PUT path via `writeCogameUri` → curly's 60 s default |
| shutdown grace | `server.nim:37`, `:237-239` | `ShutdownGraceMs = 20_000`, then `quit(0)` |
| player receive | `src/eleusis_player.nim:57-85` | `whisky.receiveMessage()` blocks with no timeout, but the whole loop is wrapped in `try/except CatchableError` and exits 0 on a dead socket; the socket's lifetime is bounded by the game's own `quit(0)` above (inference, not run) |

- The only unconditional loop is `while true` in `runGame` (`server.nim:288`); it exits on
  `state.sim.done` (`:295-296`) or the deadline (`:300-306`). Every other loop is `for` over a fixed
  range. No blocking read exists in the game process.
- `sampleEpisode` (`sim.nim:370-384`) matches the note's formula exactly
  (`maxBatches = int(episodeTimeoutSeconds × 0.6 × 1000 / max(minBatchSpacingMs,1)) − 2`), is guarded
  by `sampled` so it is idempotent, clamps `rounds` to `[MinRounds=4, MaxRounds=60]`, and never
  reduces below `MinRounds`. With the defaults `24 + 4 = 28 ≤ 58`, so nothing is trimmed.
  `src/eleusis.nim:34-41` randomises the seed **before** calling it, as the note requires, and
  `server.nim:541` sets `sampled = true` on a replay config so a replay is never re-fitted.

### String truncation (checklist 9)
- `llm.nim:459-466` (`cleanText`) — `runeLen` check, `runeSubStr(0, limit - 1) & "…"`.
- `sim.nim:638-645` (`capText`) — `runeSubStr(0, limit)`, with `oneLine` folding `\n`/`\r` to spaces
  for the hypothesis (`:650`).
- `server.nim:484-487` — the player-delivered prompt is cut at `MaxPromptLen = 4000`
  (`server.nim:35`) with `runeSubStr`.
- Captured error text is byte-sliced (`llm.nim:393-394`, `:434`, `:444`, `:448`, `:457`) but those
  strings are `echo`ed to stdout only; they never reach a `GameEvent` field, so nothing byte-cut
  enters the replay. I checked every writer of `event.text`/`event.hypothesis`
  (`sim.nim:712-713`, `:733-734`, `:762-763`) — all read `sim.seats[seat].{notes,hypothesis}`, which
  only `recordTalk` writes.
- `tests/test_sim.nim:465-487` feeds 200 and 900 multi-byte runes, asserts 120/600 runes,
  `validateUtf8() == -1` on the fields, on every event, and on the serialised
  `$payload`, and re-parses it. `tests/test_bot.nim:160-166` does the same for `cleanText`.

### Replay writer (checklist 2)
- `server.nim:157-182` (`replayPayload`) — `protocol: "eleusis.replay.v1"`, alias `names`,
  `policyNames`, a self-sufficient `config` (`rounds`, `testEvery`, `testStrips`, `seed`,
  `experimentCost`, `knowledgePool`, `citePot`, `ruleId`, `ruleText`, `sampled: true`), the whole
  `events` transcript, and `results`. It deliberately does **not** carry `states` — the viewer
  re-derives them, so there is no parallel recording.
- Event vocabulary `types.nim:42-51` and `sim.nim:1014-1090` (`eventToJson`) match the note's table
  for all nine kinds; `eventFromJson` (`:1101-1149`) round-trips them.
  `tests/test_sim.nim:381-419` asserts a 9-kind round trip field by field.
- `replayMatch` (`sim.nim:1153-1223`) replays only the decision events
  (`disclose`/`experiment`/`skip`/`answer`) through the rules; `round`, `test`, `settle` and `end`
  are **checked, not trusted** (`:1169-1171`, `:1194-1196`, `:1203-1205`, `:1212-1222`), and a
  recorded `deadline` end is applied via `endEarly` because it is not derivable. Returns
  `events.len + 1` frames (`result.add(sim)` once before the loop, once per event).
- `tests/test_sim.nim:421-446` asserts `frames.len == events.len + 1`, that the final frame's
  `benchStateJson` **string-equals** the live sim's, and that a recorded deadline replays;
  `:448-462` asserts a tampered `test` event raises.
- Seed → ruleId assertion: `replay-viewer/eleusis_replay.nim:37-45` re-derives with
  `pickRule(config.seed)` and raises `EleusisError` when it disagrees with the recorded `ruleId`;
  `elLoadReplay`'s `except` (`:63-65`) stores the message and returns 0, which
  `static_replay.js:96-99` turns into `fail(...)` → `data-replay-error` (`:56`). Hard failure, as
  the note specifies.

### Viewer re-derivation and the MODULARIZE pairing (checklist 13)
- `eleusis_replay.nim:49-51` builds `states[i] = benchStateJson(replayMatch(config, events)[i])` —
  the same `eleusis/sim` module the server runs (`:10`).
- `client/renderer.js:1283` `var states = payload.states || []`; `:1305-1308` `currentState()` indexes
  it; `:1310-1330` `setIndex` drives the clock, scorebug, testpanel and endcard from that state
  alone. Nothing in the renderer re-computes game state.
- `data-replay-loaded="true"` is set at `renderer.js:1366`, inside `attachReplay`'s `makeRenderer`
  callback and *after* the synchronous first `frame()` call (`:1291-1364`) has run
  `renderer.draw(view)` — i.e. on the first drawn frame, the same position as bullwhip's `:1390`.
- `data-replay-error` is set by the shell's own `fail()` at `static_replay.js:56` and cleared at
  `:107`/`:134`. The `coworld-replay` bridge (`loading`→`ready`→`error`) and the 20 s
  `AbortController` fetch bound are kept (`:14`, `:25-31`, `:67-89`, `:122-124`).
- **MODULARIZE pairing.** `replay-viewer/config.nims:38-39` sets `-s MODULARIZE=1` and
  `-s EXPORT_NAME=EleusisReplayModule`; `static_replay.js:138` calls the factory
  `EleusisReplayModule()` and awaits the promise. No `onRuntimeInitialized` anywhere in the tree
  (grepped). Both files are bullwhip's with names substituted — the only diffs are the four
  `bw_`→`el_` / `Bullwhip`→`Eleusis` renames in `config.nims` and six in `static_replay.js`.
  `EXPORTED_FUNCTIONS` (`config.nims:41`) lists exactly the five `_el_*` symbols the shell calls,
  plus `_main`/`_malloc`/`_free`; `EXPORTED_RUNTIME_METHODS=HEAPU8` (`:40`) matches
  `module.HEAPU8` usage at `static_replay.js:63`/`:93`. `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`,
  `ENVIRONMENT=web`, `-d:useMalloc`, `--mm:arc`, `--exceptions:goto` are all kept verbatim.
- **CI evidence.** Run **32659167800** on `main` at `529eb6872a91812eb2910b13a691d21e43b7fc05`,
  conclusion `success`. `wasm-viewer` `needs: docker-smoke` (`ci.yml:212`); its step
  `Load the bundle in a real browser` ran (step 11, conclusion `success`, no `continue-on-error`
  anywhere in `ci.yml`) and printed:
  ```
  {"loaded":true,"ms":291,"clock":"ROUND 2 / 6 · 3 OF 5 IN","scorebug":"Sprocket ▶ -$2.0 PUB 1 SEC 0 …","feed_lines":133}
  soak: 10s of playback kept advancing (null -> null -> null)
  scrub readouts: 0%="ROUND 2 / 6 · 3 OF 5 IN"  50%="ROUND 4 / 6 · 0 OF 5 IN"  100%="ROUND 6 / 6 · FINAL"
  ```
  Three differing clock readouts, `loaded: true`, soak passed. (The `null -> null -> null` in the
  soak line prints only the `tick` field of the readout, which this chrome has no element for;
  `viewer_smoke.mjs:401-402` accepts movement in `clock`, `tick` **or** `scorebug`, and would have
  set `playFailure` had none moved.)
- `--soak 10` is the fork's only change to `templates/ci.yml` (`ci.yml:306-316`); the rest of
  `ci.yml`, all of `coworld-release.yml`, all of `coworld-submit.yml` and all of
  `tools/ci/viewer_smoke.mjs` are the templates verbatim apart from the three substitutions.

### Chrome provenance (checklist 14)
The bullwhip lineage has no `client/chrome_common.js` and no `client/replay_broadcast.html`; the
design note maps the checklist's names onto `client/chrome.css` + the chrome half of
`client/renderer.js`, and `client/replay.html` (design.md:569-572). I checked the mapped files:
- `client/chrome.css` — the first **11 964 bytes** are byte-identical to
  `starters/cogame-bullwhip/client/chrome.css` (`cmp -n 11964` passes; `diff` reports a single
  `467a468,664` append). The appended block opens with the banner
  `/* ---- eleusis ---- … APPENDED ONLY … */` (`chrome.css:469-475`). Nothing above it is edited or
  deleted, including the now-unused `.plate-backlog` (`:307`), exactly as the note says.
- `client/replay.html` / `global.html` / `player.html` — each is the starter's page with only
  (a) the `<title>` text, (b) `BULL<span>WHIP</span>` → `ELEU<span>SIS</span>`, (c) `WEEK 0` →
  `ROUND 1`, (d) `BullwhipRenderer` → `EleusisRenderer`, and (e) a banner-commented block
  `<!-- eleusis additions to the inherited cogame-bullwhip chrome … -->` adding
  `<div id="testpanel">` and `<div id="drawer">` **inside `#board-wrap`**. 80/58/66 lines vs the
  starter's 74/52/60 — an append, not a rewrite. No inherited element is removed.
- Transport rule (a): `relayout()` (`renderer.js:1015-1025`) measures `#transport`'s
  `getBoundingClientRect().height` and writes `--band` and `--hudscale` on
  `document.documentElement` (i.e. `:root`, `:1016`/`:1019`/`:1024`), and is the only writer of
  either variable (grepped `setProperty` across the tree). `bindRelayout` (`:1027-1034`) binds
  `load`, `resize` and a `ResizeObserver` on `#stage`, and is called from both `attachLive`
  (`:1043`) and `attachReplay` (`:1290`).
- Transport rule (b): `#board-wrap { position: relative; flex: 1 }` (`chrome.css:95`) is a flex
  sibling *above* `#transport` (`:128-136`); `#testpanel` and `#drawer` are `position: absolute`
  inside it (`chrome.css:510`, `:562`), so nothing rides over the band. The appended
  `#endscreen { inset: 0 0 var(--band, 0px) 0; }` (`chrome.css:644`) keeps the endcard clear of it.
- Transport rule (c): the endcard is shown with `container.classList.toggle("show", !!show)`
  (`renderer.js:937`), matching its CSS rule `#endscreen.show { display: flex }`
  (`chrome.css:383`). Every seek routes through `setIndex`, which calls
  `updateEndscreen(…, index >= events.length && events.length > 0, …)` (`renderer.js:1328-1330`),
  so any non-final seek takes it down. Both seek entry points — the scrub track's drag/click
  (`buildScrub`'s track handler) and each beat button's `onclick` (`:1238-1241`) — call `onSeek` →
  `setIndex(next, true)` (`:1294-1297`). There are no back/forward buttons and no keyboard handler
  in this lineage's chrome (`index.html` has only `#play` and `#pos`), so there is no third seek
  path to check.
- Transport rule (d): `buildScrub` emits `document.createElement("button")` with
  `marker.type = "button"`, `className = "beat-marker " + beat.cls`, `aria-label`, `title` and an
  `onclick` that seeks to that event index (`renderer.js:1229-1241`). `beatFor` (`:1169-1204`)
  emits exactly five kinds — `beat-experiment`, `beat-publish`, `beat-hoard`, `beat-test`,
  `beat-end death` — and `chrome.css:597-628` carries a rule for **every one of them** plus the
  shared `button.beat-marker` reset, hover and `:focus-visible`. Labels read
  `round 7 — Gizmo tests RBGY`, `round 8 — Gizmo publishes RBGY (PASS)`, `prediction test 2`,
  as the note specifies.
- Zoom bar / minimap: bullwhip ships no `#viewpanel`, and the fork adds none —
  `grep -rn 'viewpanel\|zoomAt\|setZoom\|attachMinimap'` returns nothing in either repo. The note
  justifies this (design.md:591-595: the bench is a fixed composition).
- Art: `data/cog_{red,blue,green,yellow}_front.png` are **md5-identical** to bullwhip's
  `soldier_*_front.png`; `cog_violet_front.png` (180×192, 44 kB) and `bench_surface.png` (256×256,
  81 kB) are new real images with `scripts/art/` sources committed. `chrome.css:207` already carries
  `.seat4 { --tc: var(--violet); }` (inherited).

### Both name spaces (checklist 4)
- Agents see aliases only: `tableNames` (`sim.nim:357-368`) draws a seeded shuffle of `CogNames`;
  every prompt table uses `sim.names` (`llm.nim:266`, `:292`, `:305`, `:320`); the player socket's
  `welcome`/`state`/`final` frames all carry `sim.names[slot]` (`server.nim:439`, `:112`,
  `:210-213`); the player frame is redacted and carries no `rule`, `ruleId`, `truth`, other seats'
  `secrets` or other seats' notes (`server.nim:100-130`).
  `tests/test_bot.nim:174-196` asserts the rule text and another seat's notes are absent from both
  the system and user prompts.
- Viewer maps aliases to policy names for non-baseline seats:
  `isBaselineFiller` / `makeNameMap` / `applyNames` / `clampName` (`renderer.js:573-616`) are
  **byte-identical** to the starter's; `policyNames` rides in the replay (`server.nim:167`,
  `replayPayload:169`) and in `/global` (`server.nim:94`), and `resultsJson.names` are policy names
  (`sim.nim:846`).

### Static viewer wiring (checklist 3)
- `coworld_manifest_template.json` line 16-18: `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- `tools/build_replay_viewer.sh` exists, committed **mode 100755** (`git ls-files -s`), is the
  starter's script with the asset list swapped and the documented ecos fix
  (`mkdir -p "$(dirname "${output_dir}")"` moved **before** the containment check, `:43-46`).
  It bundles `eleusis_replay.js`/`.wasm`, `replay-viewer/index.html`,
  `replay-viewer/static_replay.js`, `client/renderer.js`, `client/chrome.css` and the six data
  assets into `assets/`. `ci.yml:224-236` asserts both the file and the exec bit before running it
  by path.
- The bundle contacts nothing but the `?replay=` URL (`static_replay.js:128`, `:143`); the only
  other fetches are same-origin bundle assets.
- No pod replay viewer is declared anywhere in the manifest (grepped). The server does register a
  `GET /client/replay` debug page (`server.nim:520`) — as the starter does
  (`bullwhip/server.nim:470`) — and the design note declares it a local-debug/certification page
  (design.md:854-855); it is never referenced by the manifest except in the `global` protocol prose.

### Manifest (checklist 6, 10, 12)
- `num_agents: 5` in **every** variant (`standard`, `open-science`, `closed-shop`) **and** in
  `certification.game_config`. `certification.players` has 5 entries;
  `certification.game_config.players` has 5. `<SEATS>` → `SMOKE_SEATS` default `5`
  (`docker_smoke.sh:54`).
- `docker_smoke.sh:106-151` enforces the four invariants before any container starts —
  `num_agents` present (`:110-118`), a positive non-bool integer (`:119-125`),
  `len(certification.players) == num_agents` (`:129-134`),
  `len(certification.game_config.players) == num_agents` (`:135-140`) — plus the independent
  `SMOKE_SEATS` cross-check (`:146-151`). All five raise with the `SEAT-COUNT FAIL:` prefix.
  I grepped the full CI log for run 32659167800: **0 occurrences of `SEAT-COUNT FAIL`**; the log
  shows `game=eleusis seats=5` and `smoke OK: seats=5 … reason=complete`.
- `game.docs` is exactly `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`
  with pages `rules.md` (5 440 chars, carries the full catalogue table) and `economy.md`
  (2 284 chars). `game.protocols` carries **both** `player` and `global`; the player text includes
  "a policy is a prompt", the `PLAYER_PROMPT`/`PLAYER_SCRIPTED` contract and the full frame shapes,
  and the global text documents the `benchStateJson` shape plus the spectator-only fields.
- `$schema` present, 8 tags, `episode_timeout_minutes: 20`, `game.name: "eleusis"`,
  `runnable.type: "game"`, `image: "{{ELEUSIS_IMAGE}}"` (derived from the compose service name
  `eleusis`, `compose.yaml:2`), `run: ["/bin/eleusis"]`,
  `env.ANTHROPIC_API_KEY_URI: "secret://coworld/eleusis/anthropic_api_key"`,
  `source_url: https://github.com/Metta-AI/cogame-eleusis/tree/main`.
- `game.results_schema` matches `resultsJson` key for key; `scores` is `{"type":"number"}` unbounded
  (may be negative) and `reason` is `enum ["complete","deadline"]`.
- Three top-level `player[]` runnables — `eleusis-player` (no `PLAYER_SCRIPTED`),
  `eleusis-openbook`, `eleusis-hoarder` — all `{{ELEUSIS_IMAGE}}` / `/bin/eleusis-player`, and the
  cert fixture seats all three (slots 0/2/4 prompt, 1 openbook, 3 hoarder), so `players-run` cannot
  report `players_missing`.
- `coworld-release.yml` order: `Build the Coworld manifest` (`:153`) → `Certify locally` (`:167`) →
  `Upload the policies` (`:206`) → `Upload the Coworld` (`:304`) → `Put the Coworld secret` (`:342`).
  Certification runs against the image `coworld build` produced in the same run. All three workflows
  present; `tools/ci/docker_smoke.sh` present and mode 100755.
- `tools/ci/policies.json` — four policies: `eleusis-empiricist` (`PLAYER_PROMPT`),
  `eleusis-guarded` (`PLAYER_PROMPT`, and carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` at line 15), `eleusis-openbook`
  (`PLAYER_SCRIPTED=openbook`), `eleusis-hoarder` (`PLAYER_SCRIPTED=hoarder`). The prompt texts
  match the design note's table verbatim.
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` across `ci.yml`, `coworld-release.yml`,
  `coworld-submit.yml`, `docker_smoke.sh`, `policies.json` returns **nothing** (exit 1 ⇒ the gate
  exits 0). The four documented residue names survive and only those: `<cow_id>`/`<sha>` in
  `ci.yml:202`, `<run_id>` in `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` in
  `coworld-submit.yml:31`.

### Legibility at 360 px (checklist 11)
- `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` — `chrome.css:280-292` (inherited verbatim
  from the starter).
- `.plate-label { display: none }` under `@media (max-width: 640px)` — `chrome.css:460-461`
  (inherited). The appended block adds `#scorebug { grid-template-columns: repeat(3, 1fr) }` at
  640 px (`:651-652`) and `repeat(2, 1fr)` at 420 px (`:661-662`), keeping all five plates; the
  `PUB`/`SEC`/`+$` chips stay and only shrink (`:663`). `#scorebug` is `repeat(5, 1fr)` at desktop
  (`:485`).
- Verdicts render as the words `PASS`/`FAIL` (`renderer.js:128-131` `verdictWord`, used by the
  canvas stamp, the test panel and the drawer), and tokens are coloured chips carrying their letter
  (`renderer.js:869-874`, `chrome.css:527-537`).

### Baseline legality and learning (checklist 7)
- `scriptedAction` (`llm.nim:191-208`) — version space from `consistentRules(knownFacts(seat))`
  (`sim.nim:344-353`, `:442-446`), majority-vote `predict` with ties → PASS (`llm.nim:166-171`),
  information-greedy `chooseStrip` over a per-seat seeded sweep
  `initRand(seed*7919 + 101*seat + 3)` (`llm.nim:152-159`, `:173-189`), `publish = kind != skHoarder`
  (`:200`), hypothesis = `describeRule(consistent[0])` or `"no consistent rule"` (`:197-199`),
  and it never writes notes.
- `tests/test_bot.nim:50-68` plays five mixed baseline seats over five seeds to
  `reason == "complete"`, with `checkLegal` (`:20-33`) run on **every** decision *before* the sim is
  asked to apply it — `experiment` is `""` or 4 chars all in `Colours`, `answers.len ==
  config.testStrips`, `hypothesis.runeLen <= MaxHypothesisLen` and valid UTF-8, `notes` empty.
  `:70-84` asserts ≥ 70 % final-test accuracy over 10 seeds (CI reports 1.0). `:86-102` asserts
  `hoarder` publishes zero and `openbook` publishes everything non-duplicate.
- Note on "tuned with a grid harness": the baseline engine has **no free numeric parameters** — the
  strip choice is argmin of `|2·hits − |consistent||` and the prediction is a majority vote — so
  there is nothing a grid could sweep. No harness exists in the tree and the design note does not
  claim one. Test 14's ≥ 70 % gate is the quality evidence in its place. Stated as an observation,
  not a finding.

### CI green + no test loosened (checklist 1)
- `gh run list -R Metta-AI/cogame-eleusis --branch main -w ci.yml`:
  `completed  success  "CI: the coworld-builder scaffold, substituted for this game"  CI  main  push
  **32659167800**  3m35s  2026-08-23T18:47:37Z`; `gh run view 32659167800 --json headSha` →
  `529eb6872a91812eb2910b13a691d21e43b7fc05` — the reviewed sha. All three jobs (`test`,
  `docker-smoke`, `wasm-viewer`) and all their steps report `success`.
- `git log -p -- tests/` in the coworld repo shows **one** commit touching `tests/`
  (`cc6a9f3 tests: the design note's list, items 1-17`) — the files are added, never modified. No
  assertion deleted, no tolerance widened, no `skip`/`xfail` introduced, no test file removed.
  I also grepped the whole tree for `skip`/`xfail` inside `tests/`: none.
- The CI log shows both test files running in **both** modes:
  `nim r --hints:off --path:src tests/test_bot.nim`, `… -d:release … test_bot.nim`,
  `… test_sim.nim`, `… -d:release … test_sim.nim`, every case `[OK]`.
  `gh variable list` returns nothing, so `NIM_TESTS`/`NIM_TESTS_DEBUG_ONLY`/`NIM_TESTS_RELEASE_ONLY`
  are unset and the default `ls tests/*.nim` glob is what ran.

### Test-list coverage vs the note's items 1–21
1–12 → `tests/test_sim.nim` (`:43`, `:79`, `:121`, `:147`, `:176`, `:213`, `:244`, `:272`, `:325`,
`:349`, `:381`+`:421`+`:448`, `:465`). 13–17 → `tests/test_bot.nim` (`:50`, `:70`, `:86`, `:104`,
`:122`). 18 → `docker_smoke.sh` (with the N5 caveat). 19 → `docker_smoke.sh:243-272` (the
per-player exit-code assertion; CI log shows `player 0..4 exited 0`). 20 → `ci.yml`'s
`Upload the smoke replay` step (artifact `smoke-replay`, id 9498273062, sha256 matched by the
`wasm-viewer` download). 21 → the `wasm-viewer` job, evidenced above.
Two sub-clauses are asserted indirectly rather than directly: item 16's "makes no network call"
(established structurally by `client.disabled` short-circuiting `decideAll` at `llm.nim:539`/`:545`
before any `RequestBatch` is built, not by intercepting a socket), and item 11's
"`$replayJson` decodes as strict UTF-8" (covered by `test_sim.nim:483-487` on the event array
rather than on the whole replay payload — the whole-payload strict parse is `docker_smoke.sh:315-322`
in CI).

## Could not determine

- **Whether the LLM path itself behaves as the note describes end to end.** CI runs with no
  `ANTHROPIC_API_KEY` by design (`docker_smoke.sh:194-199`), so every code path from
  `requestFor` through `textOf` to the retry batch is exercised only by unit tests on synthetic
  JSON. What would settle it: a hosted episode's log (phase 60 check 5) showing per-turn batches
  ~12 s apart with no `falling back` lines, plus `results.reason == "complete"`.
- **Whether the 12 s spacing actually holds 25 req/min against the hosted sidecar's 30 req/min cap
  when a retry batch fires.** A turn that retries issues 5 + k requests inside one 12 s window.
  What would settle it: a hosted log with no `429`/`llm throttled` lines over a full episode.
- **Whether `writeCogameUri`'s PUT path is bounded.** It calls `newCurlPool(1).put(value, headers,
  data)` with no explicit timeout (`bitworld/runtime.nim:193-218`); curly's request default is 60 s
  (`curly.nim:511`, `:603`), which I read but did not confirm applies through `CurlPool.put`. It runs
  after the episode has already settled and scored, so it cannot affect checklist item 5's 60 %
  bound either way. What would settle it: reading `curlpool`'s `put` signature, or a hosted run
  whose artifacts land.
- **Whether the appended `#endscreen { inset: 0 0 var(--band, 0px) 0; }` is load-bearing.**
  `#endscreen` lives inside `#board-wrap`, which is already a flex sibling above `#transport`, so
  the band inset appears redundant. It is harmless and matches the note (design.md:604-606); I could
  not determine from the CSS alone whether any viewport makes it necessary. What would settle it: a
  360 px screenshot with the endcard up and the scrubber visible.
