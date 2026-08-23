# r1 review — contagion

Range: `153b820..7cba8a0` (whole repo history; `7cba8a07e90dda827d069c12865aedbadfa98e57` on `main`)
Files read: 31 (`src/contagion.nim`, `src/contagion_player.nim`, `src/contagion/{types,sim,llm,server}.nim`,
`replay-viewer/{config.nims,contagion_replay.nim,static_replay.js,index.html}`,
`client/{renderer.js,chrome.css}`, `tests/{test_sim,test_bot,test_replay,test_manifest}.nim`,
`tests/support/helpers.nim`, `coworld_manifest_template.json`, `tools/build_replay_viewer.sh`,
`tools/ci/{docker_smoke.sh,viewer_smoke.mjs,policies.json}`, `.github/workflows/{ci,coworld-release}.yml`,
`Dockerfile`, `Dockerfile.replay-viewer`, `compose.yaml`, `contagion.nimble`, `scripts/*`, plus the
bullwhip starter for diffing)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST

Design note read at `/workspace/coworld-builder/runs/2026-08-23-contagion/design.md` (identical copy
committed at `docs/plans/2026-08-23-contagion-design.md`).

Method note: everything below is **observed** (I opened the file and quote it) unless it is labelled
*inferred* (I reasoned about it without running it) or *untested* (it would need a run to settle).
CI evidence is cited by run/job id.

---

## Blocking

### B1 — an LLM seat that exhausts its retry and falls back to the sentinel is recorded in the replay as `scripted: false`
- Where: `src/contagion/server.nim:291`, `src/contagion/llm.nim:616-662`, `src/contagion/sim.nim:523-530`
- Observed, traced step by step:
  1. `decideAll` (`llm.nim:601-662`) returns only `seq[Decision]`. When a seat is still open after
     attempt 1 it writes `result[index] = scriptedDecision(sim, seat, skSentinel)` (`llm.nim:659-662`)
     and echoes `contagion llm: seat N falling back to the sentinel move`. The returned `Decision`
     carries no flag distinguishing it from a model reply — `Decision` (`types.nim:66-76`) has
     `lockdown/testing/borders/aid/say/notes/corrected` and nothing else.
  2. The server then computes the scripted flag from the seat's *registration*, not from what
     `decideAll` did:
     ```nim
     let wasScripted = scripted[seat] != skNone or client.disabled   # server.nim:291
     ...
     state.sim.applyDecision(seat, decision, wasScripted)            # server.nim:302
     ```
  3. `applyDecision` copies that argument straight onto the event: `event.scripted = scripted`
     (`sim.nim:528`), and `eventToJson` writes it as the `dial` event's `"scripted"` field
     (`sim.nim:961`).
  4. Therefore, for a seat that registered as an LLM policy (`scripted[seat] == skNone`) with a live
     client (`client.disabled == false`), a timeout / transport error / parse failure / hard-invalid
     reply on **both** attempts produces a `dial` event with `"scripted": false` — indistinguishable
     in the replay bytes from a successful model reply.
  5. The *other* fallback path is marked correctly: a decision rejected by `applyDecision` inside the
     lock is retried with `state.sim.applyDecision(seat, fallback, true)` (`server.nim:303-307`), and
     the no-credentials path is marked via `client.disabled` (`server.nim:291`), so the offline /
     certification episodes are all `scripted: true`.
- Checklist item: item 8 — "retries **once** on a parse or transport failure, then falls back to the
  scripted move — **and the fallback is recorded so phase 60 can count it**."
- Design note says: §Decisions ¶3 step 3 (design.md:315-316): "Anything still open falls back to
  `scriptedDecision(sim, seat, skSentinel)` … The `dial` event records `scripted: true` so the feed
  can say `Riverbend falls back (timeout)`."
- Why blocking: the only surviving record of a per-week LLM fallback is the container's stdout line
  at `llm.nim:661`; the replay — the artifact phase 60 reads — attributes the sentinel move to the
  model. The feed line the design specifies (`renderer.js:1367-1372` renders `" (scripted)"` from
  `event.scripted`) will not appear for the timeout case it was written for.
- Note in fairness: this line is **bullwhip-verbatim** (`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim`
  has the identical `wasScripted` expression), so it is an inherited behaviour, not a new regression;
  and a fallback *is* recorded in the container log. Whether a stdout line satisfies "recorded so
  phase 60 can count it" is the judge's call — I record both facts.

Nothing else in the diff falsifies a named checklist item, on my reading. Items 1–7 and 9–13 are all
traced below; the two places where I could not close an item from the tree are in **Could not
determine**.

---

## Non-blocking

### N1 — literal reading of item 3's "no `/client/replay` pod path anywhere": the route and two doc mentions exist
- Where: `src/contagion/server.nim:472` (`result.get("/client/replay", htmlHandler("replay.html"))`),
  `coworld_manifest_template.json:237` and `:259` (the `global` protocol and `protocol.md` page text
  both name `/client/replay`), `client/replay.html` (74 lines)
- Observed: the manifest's own `replay_viewer` is `{"bundle": "static-replay-viewer"}`
  (`coworld_manifest_template.json:17-19`) and nothing declares a pod-served viewer to the platform;
  `test_manifest.nim:20-25` asserts `"client/replay" notin manifest["game"]["replay_viewer"]`. The
  `/client/replay` route is a debug page served by the game container in replay mode, inherited
  verbatim from the starter (`cogame-bullwhip/src/bullwhip/server.nim:470`) and explicitly prescribed
  by this design note (design.md:513-515 routes list, design.md:799-800 "a pointer to `/client/global`,
  `/client/replay` and the static bundle").
- Why I filed it non-blocking: the substantive requirement of item 3 (static bundle declared, hook
  present + executable + wired, viewer contacts only the replay URL) is satisfied — see *Traced*.
  A judge reading the final sentence of item 3 literally would reach the opposite conclusion; I am
  flagging it rather than deciding it.

### N2 — an unconnected seat is only a sentinel when the LLM client is disabled
- Where: `src/contagion/server.nim:525-526`, `:220-227`, `:291`, `src/contagion/llm.nim:618-624`
- Observed: `state.scripted = newSeq[ScriptKind](config.players.len)` initialises every seat to
  `skNone` (the enum's first value), and `state.prompts` to `""`. The connect loop
  (`server.nim:220-226`) starts the game after `playerConnectTimeoutSeconds` regardless. A seat whose
  container never connects therefore reaches `decideAll` with `kind == skNone`; `llm.nim:620` sends it
  to the model whenever `client.disabled` is false, with an empty operator block
  (`llm.nim:277-281` returns `""` for an empty prompt).
- Design note says: §Decisions ¶3 step 5 (design.md:320-324) "after `player_connect_timeout_seconds`
  (180) the game starts with whoever is there, and **unconnected seats are treated as
  `PLAYER_SCRIPTED=sentinel`**".
- Consequence (*inferred*): with credentials present, an unconnected seat costs a model round trip per
  week and plays an unguided-prompt policy rather than the sentinel. It does not affect the offline /
  certification path (`client.disabled` ⇒ sentinel, `llm.nim:130-133`), which is the load-bearing one.

### N3 — the certification fixture seats `contagion-player` at slot 0 (builder delta 1)
- Where: `coworld_manifest_template.json:428-447` — `players` is
  `[contagion-player, contagion-sentinel ×2, contagion-laggard ×3]`
- Design note says: §Packaging (design.md:827) `players` = `[{"player_id":"contagion-sentinel"} × 3,
  {"player_id":"contagion-laggard"} × 3]` — "six seats, all scripted, no LLM, sub-second".
- Observed: the builder's stated reason holds up — `test_manifest.nim:107-124` asserts
  `declared == seated`, i.e. every id in `manifest["player"]` occupies a certification slot, which is
  what `coworld certify`'s players-ran check requires; with the note's fixture `contagion-player`
  would be declared and never seated. The CI docker-smoke drives exactly this fixture and completes:
  `game=contagion seats=6 … episode end reason: complete`, `smoke OK: seats=6 results=342B
  replay=19848B` (run 32635551779, job 97184628980).
- The one thing that changes (*inferred*, untested): in hosted certification the slot-0 seat is an LLM
  policy, so if `ANTHROPIC_API_KEY_URI` resolves during certification the LLM path is exercised there;
  the design's "no LLM, sub-second" no longer describes it. Worst case is still bounded — 6 weeks ×
  `turnBudgetSeconds` 35 = 210 s.

### N4 — `chrome.css` changes more than the note's "two additions and nothing else" (builder delta 2)
- Where: `client/chrome.css:27` (`--orange: #e08a3a;`), `:211` (`.seat5`), `:266-270`
  (`repeat(6, 1fr)`, `gap: 8px` was `10px`), `:276-280` (`.plate` `gap: 5px` was `7px`),
  `:297-310` (`.plate-label` gains `white-space/overflow/text-overflow/min-width` and
  `flex: 0 100 auto` where the starter had `flex: none`), `:458-468` (`.plate-backlog` → `.plate-dead`,
  `flex: 0 20 auto`), `:471-476` (640 px block gains `grid-template-columns: repeat(3, 1fr)`),
  `:477-479` (420 px block, `repeat(2, 1fr)`, unchanged from the starter)
- Design note says: design.md:648-652 "bullwhip's file with **two additions and nothing else**" plus
  the `.plate-backlog` → `.plate-dead` rename.
- Observed: the additional edits are all in service of six plates fitting where the starter had four;
  `.plate-name` is untouched and still carries `min-width: 3.2em; flex: 1 1 auto`
  (`chrome.css:282-294`), which is the rule item 11 names. Diff against the starter is 7 hunks, all
  scorebug/plate geometry.

### N5 — measured calibration differs from the note's illustrative table (builder delta 5)
- Where: `tests/test_bot.nim:90-120`; CI run 32635551779 job 97184629083 stdout
- Observed (CI log, both debug and release runs identical):
  ```
  idle mean score -45575 deaths 182375 | locked mean score 5902 deaths 2601
  seed 7: sentinel deaths 7487 mean score 9114 | laggard deaths 181689 mean score -46317
  ```
  `totals()` (`test_bot.nim:10-16`) sums deaths across the six seats and means the score, so per
  region: idle ≈ 30 400 dead / score −45 575; all-lockdown-4 ≈ 433 dead / score +5 902;
  sentinel ≈ 1 250 dead / score ≈ +9 100.
- Design note says (design.md:242-246): never touch a dial ≈ 21 000 deaths, score ≈ −27 000;
  lockdown 4 throughout ≈ 500 deaths, score ≈ +7 000; timed suppression ≈ 1 500 deaths, ≈ +11 400.
- Observation: the **ordering and signs** the note claims hold exactly and are asserted
  (`test_bot.nim:118-120`, `:102-103`), and the lockdown-4 and sentinel rows are within ~20 %. The
  idle row is not: 30 400 deaths per region against 21 000, score −45 575 against −27 000. I
  re-derived the note's own constants by hand and the code is the one that is self-consistent — over
  20 unmitigated weeks essentially the whole population resolves (≈ 1 M × 0.35/week to exhaustion) at
  an IFR pinned at the 3.2 % overload ceiling (`sim.nim:298-304`), which is ≈ 30 k deaths, not 21 k.
  The note's GDP figure for that row (≈ 15 000) *does* match: measured gdp = −45 575 + 2×30 396 ≈
  15 200. So the divergence is confined to the note's death/score arithmetic, not to the rules.

### N6 — `tableStateJson.curves` carries a fourth series `confirmed` (builder delta 6)
- Where: `src/contagion/sim.nim:726, 736, 740, 750-755`; asserted in `tests/test_sim.nim:639`
- Design note says: design.md:458 `"curves":{"infected":…,"deaths":…,"gdp":…}` — three series.
- Observed: the extra series is what the epi strip's dotted reported-curve readout needs
  (design.md:693-697 §7 asks for exactly that picture), it is revealed only up to the current week
  like the others (`sim.nim:732-736` iterates `sim.history`), and it is additive — no existing key
  changed shape.

### N7 — `edges[].flow` is a susceptible-weighted people count accumulated from both ends (builder delta 7)
- Where: `src/contagion/sim.nim:359-360, 372-377`
  ```nim
  let imported = (((Edges[edge].mobility * passPpm(effGate[edge])) div Ppm) *
      ((CrossBetaPpm * prevalence[far]) div Ppm)) div Ppm
  force += imported
  sim.edgeFlow[edge] += s0[pos] * imported div Ppm
  ```
- Design note says: design.md:463-464 "`edges[].flow` is that week's imported-infection contribution
  across the road (`Σ imp` in people)".
- Observed: the note's phrase is ambiguous (`imp` is a ppm force, not people); the code pins it as
  susceptible × force ÷ 1e6, i.e. people, and since both endpoints add into the same
  `edgeFlow[edge]`, the value is the road's two-way total. It is reset each week (`sim.nim:359-360`),
  is viewer-only (nothing in the rules reads it), and is not part of the `week` event / `RegionState`,
  so it is outside `replayMatch`'s field-for-field check — the viewer recomputes it in the re-derived
  frames rather than reading it from the replay.

### N8 — the fallback move inside the apply loop is computed from a partially latched sim
- Where: `src/contagion/server.nim:301-307`; `src/contagion/sim.nim:461-471`; `src/contagion/llm.nim:151-175`
- Observed: `applyDecision` latches into live state immediately (`sim.regions[pos].lockdown/testing`,
  `gates[slot]` at `sim.nim:468-471`). The main decision path is clean — every seat's decision comes
  from `simCopy`, a snapshot taken before the batch (`server.nim:275-277`). But the rejection
  fallback calls `scriptedDecision(state.sim, seat, skSentinel)` on the **live** sim
  (`server.nim:306`), after lower-index seats in the same week have already latched. `sentinelDecision`
  reads neighbours through `estimatedRatePpm` (`llm.nim:147-149, 171`), which divides `confirmed` by
  `DetectPpm[region.testing]` — and `testing` is one of the values already latched.
- Design note says: design.md:156-157 "no governor sees another's week-`w` decision before
  submitting"; design.md:416-418 "the apply order across seats cannot change the outcome: it only
  latches".
- Observation: the note's claim is exactly true for a *fixed* set of decisions — `test_sim.nim:484-497`
  proves the shuffled-order table state is byte-identical. It is not true when a decision is
  *generated* from the mutating sim, which is this fallback path and also `playScripted`
  (`tests/support/helpers.nim:36-42`, ascending seat order, deterministic). The leaked quantity is a
  neighbour's current-week `testing` level only.

### N9 — non-rune-safe slices on captured HTTP error bodies (they do not reach the replay)
- Where: `src/contagion/llm.nim:449, 458, 463, 472`
  (`response.body[0 .. min(response.body.high, 400)]`, `… 300`, `result[0 .. min(result.high, 160)]`)
- Observed: these are byte slices and can cut a multi-byte sequence. They are only ever `echo`ed:
  the `ContagionError` they build is caught at `llm.nim:654-657` and printed, and the server's own
  catch prints (`server.nim:303-305`). Nothing writes an error string into a `GameEvent` —
  `eventToJson` (`sim.nim:931-966`) emits only `say`, `text` (notes) and numbers. The one error
  string that *is* rune-trimmed is `extractJsonObject`'s quoted head (`llm.nim:408-412`,
  `head.runeSubStr(0, 160)`), which is the path the design names (design.md:308-311).
- Checklist item 9 names "captured errors" among strings that reach the replay; on this trace none do.

### N10 — feed wording diverges from §Viewer 9, and one feed line mixes the two name spaces
- Where: `client/renderer.js:884-909`, `:1365-1372`
- Observed: a corrected reply renders `"<name> — reply corrected to a legal move"`
  (`renderer.js:897-902`) where the note asks for `Riverbend — aid clamped to ledger`
  (design.md:705); a scripted/fallback dial appends `" (scripted)"` (`renderer.js:1370`) where the
  note asks for `Saltmarch falls back (timeout)` (design.md:705). The aid line
  (`renderer.js:885-890`) is `clampName(nameMap.seat(event.seat)) + " sends " + amount + " to " +
  entry.to` — the **sender** is mapped to the policy display name while the **recipient** stays a
  region alias, so one line can read `daveey-warden sends 150 to Riverbend` where the note's example
  is `Harborlea sends 150 to Riverbend`.
- Both name spaces are nonetheless present and wired (see *Traced*); this is a rendering-copy
  divergence, not a redaction one — `entry.to` is an alias in the replay by construction
  (`sim.nim:663-666`).

### N11 — `weeks < 4` raises at config-load rather than being clamped
- Where: `src/contagion/types.nim:150-151` (`if config.weeks < 4: raise …`), against
  `src/contagion/sim.nim:185` (`result.weeks = max(min(config.weeks, MaxWeeks), MinWeeks)`)
- Design note says: design.md:410 `sampleEpisode(config)` "clamps `weeks` to 4..40".
- Observed: `contagion.nim:33` calls `config.update` before `sampleEpisode(config)` (`:41`), so a
  runtime config of `weeks: 2` throws `ContagionError` at startup instead of clamping to 4. The upper
  bound *is* clamped. Unreachable through the manifest, whose schema pins `weeks` to 4..40
  (`coworld_manifest_template.json`, `properties.weeks` minimum 4 maximum 40).

### N12 — `curl.makeRequests` is outside the per-seat `try`
- Where: `src/contagion/llm.nim:642`
- Observed: `let responses = client.curl.makeRequests(batch, timeout)` is not wrapped; the `try` starts
  at `:646` and covers only response handling. *Inferred*: if `makeRequests` itself raised, the
  exception would leave `decideAll`, leave `runGame` (which has no top-level handler,
  `server.nim:214-317`), and kill the game thread while `gameServer.serve` keeps the process alive in
  the main thread (`server.nim:531-533`) — no results, no replay, until the platform timeout. This is
  bullwhip-verbatim (`cogame-bullwhip/src/bullwhip/llm.nim`, same line unwrapped). Whether `curly`
  raises on transport failure or reports it per-request in `responses[].error` (which the code does
  handle, `llm.nim:647-648`) I could not settle from this tree — see *Could not determine*.

---

## Traced and consistent

**Resolution rules — the eight numbered steps (design.md:159-225)**

- `src/contagion/sim.nim:436-533` step 1: dials latch, `borders[slot] == -1` keeps last week's gate
  (`:463-469`), out-of-range gate raises (`:465-466`). Effective gate is
  `max(gate[a], gate[b])` in `effectiveGate` (`sim.nim:291-296`) — verified against the note's
  `eff(e) = max(...)`; `test_sim.nim:195-212` asserts the looser end cannot re-open a road.
- Step 2 talk: `sim.says[pos]` set at latch (`sim.nim:509`), rotated into `heard` at the next
  `openWeek` (`sim.nim:221-223`), delivered to all six (`sim.nim:673-676`, `:822-826`), suppressed
  when `talk` is false (`sim.nim:504-505`). `test_sim.nim:450-470` asserts public delivery, one week
  late, and that `heard` clears.
- Step 3 aid: clamped at latch against `max(0, min(MaxAidPerWeek, gdp))` (`sim.nim:476-499`) and
  settled in `resolveWeek` (`sim.nim:338-347`). I checked the note's "gdp as it stood at the start of
  this step" is the same number: nothing between `applyDecision` and `resolveWeek`'s step 3 touches a
  ledger (grep of `\.gdp` assignments: `sim.nim:345`, `:403` only). Order-independence therefore
  holds, and `test_sim.nim:305-320` asserts aid received this week cannot be re-sent.
- Step 4 spread: `sim.nim:349-383`. Forces computed from `i0/s0/a0` snapshots taken at `:330-333`
  before any mutation; `passPpm` (`sim.nim:306-309`) is `LeakPpm + (Ppm-LeakPpm)*GatePass/Ppm`, so
  `passPpm(2) == 120_000` exactly (`test_sim.nim:166-167`) — the 12 % floor. `force` capped at
  `ForceCapPpm` (`:378`), `newInfections` capped at `s0` (`:379`).
- Steps 5–7: `sim.nim:385-417`. I re-derived the whole pinned fixture from `test_sim.nim:104-163`
  independently in Python against the note's formulas and got, field for field:
  `prev 100000, local 57600, pass 120000, imp_main 2100, imp_back 1260, force 63060,
  newInf 56754, S 843246, I 156754, sick 235131, output 611895, gross 611, spend 155, ledger 1456,
  load 6270160, ifr 32000, resolved 35000, deaths 1120, recovered 33880, I_final 121754,
  confirmed 42613, confirmedNew 19863` — every one of these is the exact literal asserted at
  `test_sim.nim:150-161`. Integer truncating division throughout; no float appears in `sim.nim`.
- IFR overload: `ifrPpm` (`sim.nim:298-304`) = `BaseIfrPpm + BaseIfrPpm*min(3e6, max(0, load-1e6))/1e6`;
  `test_sim.nim:170-173` pins `ifrPpm(HospitalCap) == BaseIfrPpm` and
  `ifrPpm(4*HospitalCap) == 4*BaseIfrPpm` (0.8 % → 3.2 %), matching design.md:207.
- Step 8: `sim.nim:419-434` — `weeksPlayed`/`week` advance, the final week is logged and observed with
  no decisions, then `settle("complete")`; otherwise `openWeek`. `test_replay.nim:100-102` asserts
  `weekEvents == weeks + 1`.
- Scoring: `score = gdp - DeathPenalty*dead` (`sim.nim:287-289`), both signs asserted
  (`test_sim.nim:323-332`); `results_schema.properties.scores.items` carries no `maximum`
  (`test_manifest.nim:80`, verified in the manifest).

**Decision path (checklist 8, and the "one parallel batch" rider)**

- One batch per week for all six seats: `llm.nim:633-642` builds a single `RequestBatch` over the
  open seats and issues `client.curl.makeRequests(batch, timeout)` once per attempt. There is no
  per-seat request loop anywhere; `server.nim:285-286` calls `decideAll` once per week.
- Tolerant parse: `extractJsonObject` takes `text.find('{') .. text.rfind('}')` (`llm.nim:401-413`),
  so surrounding prose and fences are accepted. `coerceDial` (`llm.nim:483-505`) accepts int, float
  (rounded) and numeric string. `test_bot.nim:141-150` covers all three.
- Hard-invalid vs soft-corrected split matches design.md:579-593 exactly: missing/out-of-range
  `lockdown`/`testing` raise (`llm.nim:486-504`), `borders` not an object raises (`:524`), `aid` not an
  array raises (`:558`); unknown road, gate outside 0..2, self/unknown/negative aid recipient and the
  4th entry are corrections that set `corrected` (`:535, 548-552, 560-596`). `test_bot.nim:152-217`
  asserts both halves.
- Retry exactly once, then sentinel: `for attempt in 0 .. 1` (`llm.nim:626`) with the hint text
  appended verbatim from design.md:311 (`llm.nim:638-639`), then `llm.nim:659-662`.
- Pre-flight legality: `var probe = sim; probe.applyDecision(seat, decision, false)`
  (`llm.nim:651-652`) rejects an illegal reply into the retry rather than into the sim.
- No credentials ⇒ every seat scripted with no network: `newLlmClient` sets `disabled = true`
  (`llm.nim:130-133`) and `decideAll` short-circuits at `:620` / `:627`. `test_bot.nim:261-275`
  asserts all six seats get their registered baseline with no call.

**Every wait and its bound (checklist 5)**

- Player connect: `while epochTime() < deadline` with `sleep(200)`, `deadline = gameStart +
  playerConnectTimeoutSeconds` (`server.nim:218-226`); default 180 (`types.nim:106`,
  manifest default 180 in both variants and the cert fixture).
- Play budget: `PlayBudgetFraction = 0.6` (`server.nim:209`), `playDeadline = gameStart +
  timeoutSeconds * 0.6` with `timeoutSeconds` falling back to `config.episodeTimeoutSeconds` = 1200
  when `COWORLD_TIMEOUT_SECONDS` is absent (`server.nim:241-250`) ⇒ 720 s, as the note states.
- Deadline check is between weeks only: `server.nim:264-274` inside the lock, before the batch;
  `sim.endEarly()` → `settle("deadline")` (`sim.nim:535-541`) and `break`. No half-week can reach the
  replay because `resolveWeek` runs only on the sixth `applyDecision` (`sim.nim:532-533`).
  `test_sim.nim:373-388` asserts `reason == "deadline"` with `weeks < maxWeeks` and idempotence.
- LLM first batch: `timeout = client.timeoutSeconds` = `llmTimeoutSeconds` = 25 (`types.nim:109`,
  manifest default 25). Retry: `timeout = max(5, min(10, remaining))` where
  `remaining = budgetSeconds - elapsed` (`llm.nim:630-632`) — bounded by what is left of the week's
  35 s, exactly as design.md:298-299 requires, and never a second full 25 s.
- Per-week ceiling (*inferred* arithmetic): 25 + 10 + apply + `turnDelayMs` 0.3 ≈ 35.35 s;
  20 × 35.35 = 707 s ≤ 720; because the deadline is tested *before* each week the last week can
  overrun to ≈ 755 s, still far inside 1200 s with `finishEpisode`'s two 500 ms sleeps
  (`server.nim:195, 205`) and the artifact writes.
- No round barrier exists to bound: the server decides for every pending seat itself; a player socket
  is only a prompt-delivery channel (`server.nim:437-454`). There is no blocking read anywhere in
  `runGame`.
- Main loop terminates: `while true` (`server.nim:256`) breaks on `sim.done` or the deadline, and each
  iteration applies a decision for *every* pending seat, so `resolveWeek` fires every iteration
  (`pendingSeats` is either all six or empty, `sim.nim:214-228` / `:432-434`).
- Viewer fetch: 20 s `AbortController` (`static_replay.js:14, 71-88`) with a Retry button.
- Smoke: `SMOKE_TIMEOUT` 900 s with an explicit deadline loop (`docker_smoke.sh:226-235`).

**String truncation (checklist 9)**

- `say`: `runeLen > MaxSayLen` ⇒ `runeSubStr(0, 159) & "…"` (`sim.nim:506-507`), newlines and CRs
  flattened (`:503`); `notes`: `runeSubStr(0, 699) & "…"` (`sim.nim:512-514`). Parser side
  `cleanText` does the same (`llm.nim:474-481`). Aid recipient name `runeSubStr(0, 24)`
  (`llm.nim:567-568`). Prompt frame `runeSubStr(0, 4000)` (`server.nim:441-442`). Error head
  `runeSubStr(0, 160)` (`llm.nim:409-410`).
- Multi-byte tests at the cap: `test_sim.nim:427-448` (400×`é` → `runeLen == 160`,
  `validateUtf8() == -1`), `:472-481` (900×`é` → 700), `test_bot.nim:219-235`,
  and `test_replay.nim:10-54` feeds 4-byte emoji (`🦠`, `🏥`), combining marks (`e\u0301`,
  `a\u0308`) and CJK right at the cap and asserts `validateUtf8(bytes) == -1` over the whole
  serialised payload plus byte-stable `parseJson` round-trip (`:56-68`).

**Replay writer (self-sufficiency)**

- `replayPayload` (`server.nim:130-153`) emits `protocol`, `rules` (`RulesVersion`), `names` (region
  aliases by seat, from `sim.names`), `policyNames` (`config.players[].name`), `config`
  `{weeks, seed, talk, sampled:true}`, `events`, `results` — every field design.md:479-487 lists.
  Each `week` event carries all six `RegionState`s in position order (`sim.nim:206-212`,
  `:604-623`), so per-week true state is in the bytes.
- `test_replay.nim:70-102` asserts every one of those fields plus one `week` event per observed week
  and `6 × Seats` dial events; `docker_smoke.sh:285-292` re-parses the produced replay as strict UTF-8
  JSON with `SMOKE_REQUIRE_REPLAY_JSON=1` (`docker_smoke.sh:57`), and did so in CI (19 848 B).

**Replay re-derivation and the viewer (checklist 2, 13)**

- `replayMatch` (`sim.nim:898-927`): `initSim(config)` re-draws the permutation, `outbreakPos` and
  `variantWeek` from the seed alone (`sim.nim:240-247`); each `dial` is replayed through
  `applyDecision`; each `week` event is compared **field for field** via
  `sameRegions` on the whole `RegionState` (`sim.nim:890-896`, `:915-918`) plus `week` and `variant`,
  raising `ContagionError` on any mismatch. `frames[i]` = state after `events[0..<i]` (`:909, :927`).
- Asserted: `test_sim.nim:516-542` (`frames.len == events.len + 1`, final frame's `tableStateJson`
  byte-equal to the live one, and the same through the JSON round trip), `:554-566` (a tampered
  `infected` **and** a flipped `variant` both raise), `test_replay.nim:104-125` (the wasm module's
  own Nim path: `states.len == events.len + 1`, `states[^1]` equals the live final frame).
- The viewer draws from that re-derivation, not a parallel recording: `attachReplay` reads
  `payload.states` (`renderer.js:1413`) and `currentState()` indexes it (`:1435-1438`); `states` is
  produced by `replayMatch` in the wasm module (`replay-viewer/contagion_replay.nim:37-39`) and by
  `statesFromEvents` in replay mode (`server.nim:155-159`).
- Factory/bootstrap pair: `config.nims:44-45` sets `-s MODULARIZE=1 -s
  EXPORT_NAME=ContagionReplayModule`, and the shell **calls the factory**:
  `modulePromise = ContagionReplayModule().catch(...)` (`static_replay.js:138`). `onRuntimeInitialized`
  appears nowhere in the shell (grepped). Exported symbols in `config.nims:47` are exactly the five
  `_cg_*` the shell calls (`static_replay.js:92-103`) — asserted statically at
  `test_manifest.nim:213-228`.
- Readiness markers: `data-replay-loaded="true"` is set **inside the first `frame()` iteration, after
  `renderer.draw(view)` returns**, guarded by `announced` (`renderer.js:1420, 1482-1488`) — the
  design's deliberate improvement over bullwhip, which sets it after starting the rAF loop
  (`cogame-bullwhip/client/renderer.js:1390`). `data-replay-error` is set in `fail()` and removed on
  each attempt (`static_replay.js:56, 107, 134`). Both live in files the bundle ships
  (`build_replay_viewer.sh:46-50` copies `renderer.js` and `static_replay.js`).
- The bundle **executed** in CI: run 32635551779, job `wasm-viewer` 97184741494, step
  `Load the bundle in a real browser`, `needs: docker-smoke` (`ci.yml:212`), against the replay
  `docker-smoke` produced. Output:
  `{"loaded":true,"ms":289,"clock":"WEEK 0 / 6 · WAITING ON 6","scorebug":"Sprocket ▶ 0 RIVERBEND
  Gizmo ▶ 0 ASH …","feed_lines":77}` and scrub readouts at 0/50/100 %. Not `continue-on-error`; step
  is present and ran. `tools/ci/viewer_smoke.mjs` is byte-identical to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (diff -q: identical).
- Viewer contacts nothing but the replay URL: the only `fetch(` in the bundle is
  `static_replay.js:76` on `?replay=`; the only `new WebSocket` in `renderer.js:1281` is in
  `attachLive`, which the static shell never calls. Assets are relative (`assetBase: "./assets"`,
  `static_replay.js:117`).

**Manifest (checklist 6, 10, 12)**

- `game.replay_viewer = {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json:17-19`);
  `tools/build_replay_viewer.sh` present, committed **100755** (`git ls-files -s` → `100755`), and
  `ci.yml:225-236` asserts the exec bit and invokes it by path.
- `num_agents: 6` in `variants[standard].game_config` (`:359`), `variants[sprint].game_config` (`:391`)
  and `certification.game_config` (`:421`); `tokens`/`players` bounds 6..6 and `num_agents`
  minimum=maximum=6 in `config_schema`. `test_manifest.nim:27-45` asserts all of it.
- `docker_smoke.sh:106-151` enforces the four invariants the checklist names — `num_agents` present
  (`:110-118`), positive integer (`:119-125`), `len(certification.players) == it` (`:129-134`),
  `len(certification.game_config.players) == it` (`:135-140`) — plus the independent `SMOKE_SEATS`
  cross-check (`:141-151`), each exiting non-zero with a `SEAT-COUNT FAIL:` prefix. `SMOKE_SEATS`
  default is 6 (`:54`), asserted against `Seats` at `test_manifest.nim:145-149`. I grepped the full
  docker-smoke job log for `SEAT-COUNT` — **no occurrences**; the job printed `seats=6` and
  `smoke OK: seats=6`.
- `game.docs` is `{"readme":{"type":"text","value":…},"pages":[{id,title,content:{type,value}} × 2]}`
  with ids `rules.md`, `protocol.md`; the rules page carries all eight numbered steps, both constant
  tables, the redaction list and the reply schema (7 242 chars, headings checked). `game.protocols`
  carries **both** `player` and `global`, each `{"type":"text","value":…}`. `test_manifest.nim:86-105`
  asserts non-empty text for all three plus the `contagion.player.v1` / `/global` markers.
- `results_schema.properties.reason.enum == ["complete","deadline"]`, `additionalProperties:false`,
  required key set == the key set `resultsJson` actually writes (asserted dynamically against the sim
  at `test_manifest.nim:61-84`).
- Release order: `coworld-release.yml` runs Build the Coworld manifest (:153) → Certify locally (:167)
  → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342), in that
  order and in one job. No smoke step in the release workflow. All three workflows present;
  `tools/ci/docker_smoke.sh` committed 100755.
- `tools/ci/policies.json`: four policies, all `"run": "/bin/contagion-player"`, two `PLAYER_PROMPT`
  champions (`contagion-warden` 1 145 chars, `contagion-broker` 881 chars, distinct) and two
  `PLAYER_SCRIPTED` fillers; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` and it is the only `player` key
  (`test_manifest.nim:151-177`).
- Placeholder gate: I ran the checklist's exact grep for `<slug>|<IMAGE>|<SEATS>` over the five named
  files — **no matches, exit 0**. The surviving angle-bracket names are exactly the four documented
  as expected residue: `<cow_id>`, `<sha>` (ci.yml comment), `<run_id>` ×2 (release/submit readback
  recipes), `<name>` from `<name>:vN` (submit input description).

**Both name spaces (checklist 4)**

- In-game: prompts and the player socket carry region aliases only — `systemPrompt`/`userPrompt` use
  `RegionNames` throughout (`llm.nim:233-397`), the welcome frame sends
  `"name": regionOf(slot)` (`server.nim:391-399`), the final frame is re-written with
  `aliasNames` before it reaches players (`server.nim:176-189`). `test_bot.nim:292-294` and
  `test_sim.nim:667-669` assert no policy display name appears in the prompt or the player view.
- Spectator-only: `results.names` (`sim.nim:581`), `replay.policyNames` (`server.nim:144`), and the
  renderer's `makeNameMap`/`applyNames`/`clampName` (`renderer.js:773-812`) — byte-identical to
  bullwhip's (`cogame-bullwhip/client/renderer.js:778-813`), including `isBaselineFiller` so baseline
  seats keep their alias. The CI viewer smoke's scorebug readout shows the real names
  (`Sprocket ▶ 0 RIVERBEND …`), i.e. both spaces present in one frame.
- The seat→position permutation is re-drawn per episode from the seed (`sim.nim:240-245`), asserted a
  bijection, stable per seed and varying across seeds (`test_sim.nim:56-73`).

**Scripted baseline plays full episodes legally (checklist 7, first half)**

- `test_bot.nim:19-46`: six sentinels, six laggards and a 3/3 mix, seeds `[1,7,42,1234]`, each a full
  20-week episode with `check sim.reason == "complete"`; every emitted `lockdown in 0..4`,
  `testing in 0..3`, every `borders[slot] in 0..2`, `aid.len == 0`, `say.len == 0`, and
  `dials == 20*Seats`. `applyDecision` raising is itself the legality assertion
  (`helpers.nim:32-42`). `test_bot.nim:48-73` proves both baselines are pure functions of the
  seat-observable view by mutating hidden truth and asserting identical decisions.
- The sentinel/laggard thresholds match design.md:371-386 line for line (`llm.nim:151-192`), including
  the ×0.8 variant tightening and the laggard's "lockdown 3 for exactly three weeks then open
  forever" (asserted `locked == 3` at `test_bot.nim:75-88`).

**CI (checklist 1)**

- `gh run list -R Metta-AI/cogame-contagion --branch main -w ci.yml` → run **32635551779**,
  conclusion **success**, on `main`, 2026-08-23T11:05:20Z, at the reviewed sha. Jobs:
  `docker-smoke` ✓ 54 s, `test` ✓ 1 m 8 s, `wasm-viewer` ✓ 1 m 29 s.
- No test loosened: `git log -p --stat -- tests/` shows a **single** commit touching `tests/`
  (`7cba8a0`, +1 416 lines, 5 new files, 0 deletions). No test file was modified or removed, no
  assertion deleted, no tolerance widened, and there is no `skip`/`xfail` anywhere in `tests/`.
- Every `tests/*.nim` runs twice, debug and `-d:release` (`ci.yml:104-150`); the CI log shows both
  passes of each file. `NIM_TESTS*` repo variables are unset (the log shows the default `ls tests/*.nim`
  expansion running all four files).

**Other things I opened and found consistent with the note**

- `contagion_player.nim:61-92`: the receive loop is wrapped in `try/except CatchableError` and exits
  cleanly on a dead socket (builder delta 3), with the prompt re-sent after `welcome`
  (`:77-79`) to cover the slot-registration race, as design.md:606 requires.
- `types.nim:44-60`: every people/credit field is `int64` (builder delta 4); the comment at
  `types.nim:5-10` gives the wasm32 reason and the force arithmetic does reach ~9e11
  (`s0 * force` with `s0` ≈ 1e6, `force` ≤ 9e5).
- `scripts/make_manifest.py` (556 lines) and `scripts/art/make_props.py` (334 lines) exist as claimed
  (builder delta 8); `recolor_sprite.py` (55 lines) produces the violet/orange portraits.
- Art is authored, not placeholder: `map_board.png` 1600×1000 / 6 300 distinct colours,
  `region_tile.png` 320×252 / 873, six portraits 180×192 with 5 600–10 200 colours each; all twelve
  assets are copied by the build hook and their presence is asserted
  (`test_manifest.nim:200-211`).
- `finishEpisode` (`server.nim:161-207`) is bullwhip-verbatim including both `sleep(500)`s (builder
  delta 9): final frames to players first, then results (`application/json`) and replay
  (`application/octet-stream`), then `quit(0)`.
- `Dockerfile` two-stage, both binaries, `CMD ["/bin/contagion"]`; `Dockerfile.replay-viewer`
  `emscripten/emsdk:4.0.15` with `test -s replay-viewer/dist/contagion_replay.wasm`; `compose.yaml`
  service `contagion` → `coworld-contagion:latest` (asserted `test_manifest.nim:137-143`).
- `episode_timeout_minutes: 20` in the manifest = the 1200 s the code assumes (`types.nim:103`).

---

## Could not determine

1. **Item 7's "tuned with a grid harness, not guessed."** There is no grid/sweep/tuning harness in the
   tree: grepping `grid|harness|sweep|tune|calibrat` across `*.nim`, `*.py`, `*.sh`, `*.md` (excluding
   `docs/plans/`) returns only `np.mgrid` in `make_props.py` and the word "calibration" in a
   `test_bot.nim` comment. The design note does not mention a harness either. What exists is
   `test_bot.nim:90-120`, which asserts the *shape* of the calibration over four seeds. What would
   settle it: a committed sweep script, or the builder's phase report citing the sweep it ran and the
   parameters it produced.
2. **Whether `curly.makeRequests(batch, timeout)` can raise** (bears on N12) **and whether `timeout`
   is seconds.** `curly` is an external dependency, not vendored here; the seconds reading is
   consistent with `curl.post(uri, headers, data, 60)` at `server.nim:123` and with bullwhip's use.
   What would settle it: reading `curly`'s `makeRequests` signature in `~/.nimby/pkgs`, or a CI run
   with a deliberately dead endpoint.
3. **Whether `bitworld/runtime`'s `readCogameUri` / `writeCogameUri` carry their own timeouts.**
   `resolveApiKey` (`llm.nim:70`) fetches `ANTHROPIC_API_KEY_URI` once at client construction, inside
   the play budget; `writeCogameUri` (`server.nim:128`) writes the artifacts. Both are external and
   not in this tree. The one artifact path that *is* bounded here is the HTTP POST branch
   (`server.nim:123`, 60 s). What would settle it: reading `bitworld/runtime`'s source, or a hosted
   run where the secret URI is unreachable.
4. **Whether the LLM-driven per-week ceiling holds under non-default config.** `llmTimeoutSeconds` is
   schema-permitted up to 300 while `turnBudgetSeconds` maxes at 120 (`config_schema`), and nothing
   clamps the first batch's timeout against the week budget (`llm.nim:629`) — only the retry is
   bounded. Under the manifest's own defaults (25 / 35) the note's arithmetic holds; under a
   pathological override a week could exceed its budget, with the between-weeks deadline check
   (`server.nim:264`) as the remaining backstop. Untested: no CI run exercises the LLM path
   (`docker_smoke.sh:198` — "no ANTHROPIC_API_KEY: the game must complete on its scripted baselines").
