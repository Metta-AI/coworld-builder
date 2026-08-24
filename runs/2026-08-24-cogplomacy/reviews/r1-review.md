# r1 review — 2026-08-24-cogplomacy

Repo: `Metta-AI/cogame-cogplomacy` @ `1b9ddad8d7e1fef17b5fc537c47911d1167c5bc3` (main)
Range: `27141df..1b9ddad` (whole tree; the repo is three commits old)
Files read: 41 source/config files + the three CI job logs of run 32722300699 + the
`smoke-replay` artifact it produced.
Checklist: `prompts/30-review-loop.md` § ACCEPTANCE CHECKLIST (items 1–14 + the
simultaneous-decision rider).
Design note: `runs/2026-08-24-cogplomacy/design.md` (identical copy committed at
`docs/plans/2026-08-24-cogplomacy-design.md`).

Sandbox has no Nim, no docker, no emsdk and no browser, so nothing below was re-executed
locally. Where I ran the rules in my head I say so. Where CI executed them I cite the run.

---

## Blocking

**None.** I could not find a finding that falsifies a named acceptance-checklist item.
Items 1–14 and the one-batch-per-turn rider are all traced below with the evidence that
satisfies them.

---

## Non-blocking

### N1 — The `expander` baseline never builds a fleet; the note says it sometimes must
- Where: `src/cogplomacy/llm.nim:347-380`, with `buildSites` at `src/cogplomacy/orders.nim:531-544`
- Observed: `buildSites` emits, for each vacant owned home centre in code order, the **army**
  option first (`result.add((province, "", ukArmy))`, orders.nim:542) and then one fleet option
  per fleet node. `scriptedBuilds` walks that list in order; for the army entry `wantFleet` is
  `site.kind == ukFleet and fleets < armies` = false, and the guard `if site.kind == ukFleet and
  not wantFleet: continue` (llm.nim:365) does not apply to an army, so the army is always taken.
  The province is then in `result`, so the same province's fleet entries hit the
  one-build-per-province guard (llm.nim:371-376) and are skipped. Net effect: the baseline builds
  an army in every case.
- Corroborated by CI, not just by reading: the `smoke-replay` artifact of run 32722300699 contains
  exactly two `build` events, `{"action":"build","unit":{"power":6,"kind":"A","province":3}}`
  (Turkey, ANK) and `{"power":3,"kind":"A","province":9}` (Germany, BER). Turkey held 1 fleet and
  2 armies at that point, and ANK is coastal, so the note's rule asks for `F ANK`.
- Note says (§Scripted baselines, expander step 7): "fill vacant owned home centres in
  province-code order, **a fleet if the centre is coastal and the power holds fewer fleets than
  armies**, otherwise an army (`STP` builds `F STP/SC`)". The `STP` clause is likewise unreachable.
- Not on the checklist: item 7 asks only that the baseline plays a legal full episode
  (`tests/test_bot.nim:91-98` asserts `reason == "complete"` and legality), which it does.

### N2 — expander's "support a moving neighbour" rule fires only when the unit has no move at all
- Where: `src/cogplomacy/llm.nim:251-283`
- Observed: `picked` is filled from the ranked options while `option.rank <= 2` (llm.nim:252-262).
  The support branch at llm.nim:272-282 runs only when `entry.dest < 0` — i.e. when no rank-0/1/2
  destination survived the claim/own-unit filters. A unit whose best option is rank (c) (a move
  that closes the BFS distance) always moves.
- Note says (§expander step 4): "If a unit's own best option is rank **(c) or (d)** and another of
  the power's units has claimed a destination adjacent to this unit, the unit issues
  `S <that unit> - <that destination>` instead."

### N3 — An illegal order does not consume its unit's slot, so a later order for the same unit is used
- Where: `src/cogplomacy/sim.nim:595-619` (`submitOrders`)
- Observed: an order that comes back `illegal` is recorded in `result.illegal` and `continue`d
  (sim.nim:606-609) **before** `claimed.add(order.unit.province)` (sim.nim:610-612). A reply of
  `["A PAR - ENG", "A PAR - BUR"]` therefore records `A PAR - ENG` as illegal and then executes
  `A PAR - BUR`. `adjudicate.alignOrders` has the same shape (`adjudicate.nim:342-353`: it takes
  the first order that is `sameUnit` **and not illegal**).
- Note says (§resolution step 1): "If a unit is named twice, keep the **first** order and drop the
  rest", and step 2: "**Every illegal order becomes `H` for that unit**". Under the note the unit
  holds; under the code it moves to BUR.
- No test covers a second order for a unit whose first was illegal.

### N4 — `replayMatch` cross-checks fewer recorded fields than the note's event table promises
- Where: `src/cogplomacy/sim.nim:1237-1281`
- Observed, per event kind: `start` compares only `event.units.len` against the seeded board
  (1240-1242); `phase` compares only `year`, `season`, `phaseKind` (1243-1248) — the recorded
  `units`, `owners` and `counts[7]` on that event are never compared; `adjudicate` compares only
  `event.results.len` (1255-1257) — no outcome is compared; `centres` compares the full 34-slot
  ownership table (1272-1276); `press`/`orders`/`retreat`/`build` are re-applied through the rules,
  which is the real re-derivation.
- Note says (§Event vocabulary, `phase` row): "`units`, `owners`, `counts[7]` — the derived board,
  **checked** against the seeded re-derivation in `replayMatch`".
- Checklist item 2 is still satisfied: the frames come from re-running the sim, not from a parallel
  recording (`server.nim:198-202` and `replay-viewer/cogplomacy_replay.nim:39-41` both build
  `states` from `replayMatch`), and `tests/test_sim.nim:408-414` asserts
  `frames.len == events.len + 1` plus final-frame equality with the live `tableStateJson`.

### N5 — The prompt-delivery wait is 5 s, not `player_connect_timeout_seconds`, and a late prompt still takes over
- Where: `src/cogplomacy/server.nim:288-314` and `src/cogplomacy/server.nim:508-526`
- Observed: after the connect loop (bounded by `playerConnectTimeoutSeconds`, server.nim:278-286)
  the prompt wait is `promptDeadline = min(deadline, epochTime() + 5.0)` (server.nim:291). Seats
  still lacking a prompt are switched to `skExpander` (server.nim:306-310). But the websocket
  handler writes `state.scripted[slot] = scripted` unconditionally on any later `prompt` frame
  (server.nim:520-523), so a prompt arriving at t+6 s puts the seat back on the LLM path.
- Note says (§Degrade, never hang): "A seat that never delivers a prompt **by the time play starts
  (`player_connect_timeout_seconds`, default 180)** plays `expander` **for the whole episode**".
  The code's bound is tighter (5 s) and its effect is not permanent. Both directions are
  degrade-safe — nothing waits longer than the note allows — but neither matches the note's text.

### N6 — The feed prints raw order notation and unnamed provinces where the note specifies words
- Where: `client/renderer.js:1458-1495`
- Observed: an `orders` event renders `powerWord(event.power) + " orders: " + (event.orders||[]).join("; ")`
  (renderer.js:1459-1461), i.e. `France orders: A PAR - BUR; F BRE S A PAR - BUR`. A bounce renders
  `"A move bounces."` with no province (1471-1474); a dislodgement renders
  `"Austria is dislodged and must retreat."` with no province, attacker or destination (1476-1479);
  a standoff renders `"STANDOFF — nothing enters."` with no province (1480-1482).
- Note says (§Readouts, `#feed`): `France orders Paris → Burgundy; Brest supports Paris → Burgundy.`,
  `Germany's Munich → Burgundy bounces. STANDOFF in Burgundy.`, `Austria's Trieste is dislodged by
  Venice (supported by Rome) and retreats to Albania.`
- The data is present in the event (`results[].order` carries province ids —
  see the `adjudicate` event in the smoke replay), and `orderWords`
  (`src/cogplomacy/orders.nim:52-68`) is written for exactly this wording but has **no caller**
  anywhere in the tree (`unitWords` is called only by `orderWords`; `powerAdjective`,
  `mapdata.nim:463`, is also uncalled). The starter's `describeEvent` (renderer.js:704-730) is
  likewise retained but never called — `renderFeed` uses `diploFeedLines` (renderer.js:772).
- Checklist item 11 (legibility) is about `.plate-name` and the 640 px labels, which are satisfied
  (see Traced), so this is not blocking under the checklist. On the canvas itself the note's rule is
  met: province **names** are drawn, never codes (renderer.js:366-370).

### N7 — A province vacated by a dislodged unit counts as a legal retreat destination
- Where: `src/cogplomacy/sim.nim:570-591` then `src/cogplomacy/orders.nim:435-458`
- Observed: `resolveOrders` rebuilds `board.units` **without** the dislodged units (sim.nim:572-586)
  and stores them in `sim.dislodged`; `openRetreats` (sim.nim:209-218) then runs the retreat phase
  against that board, so `retreatDestinations`' emptiness test `board.unitAt(dest) >= 0`
  (orders.nim:445, 456) sees a province holding a still-unretreated dislodged unit as empty.
- Note says (§step 9): the destination must be "(b) **empty after the movement phase**", which the
  code satisfies on a literal reading. Standard Diplomacy (and DATC) bars retreating into a
  province occupied by another unit, including one that is itself dislodged. Flagging the
  divergence, not asserting the note is wrong.
- `tests/test_adjudicate.nim:260-275` covers attacker-origin, standoff and occupied-by-a-live-unit;
  it does not cover this case.

### N8 — A press letter addressed to `ALL` is dropped rather than published
- Where: `src/cogplomacy/llm.nim:627-631` and `src/cogplomacy/sim.nim:411-423`
- Observed: `parsePress` resolves the recipient with `powerByName(item{"to"}.getStr())`
  (llm.nim:627); `"ALL"` is not a power name, so it returns `-1` (mapdata.nim:466-471) and the
  letter is skipped by `if to < 0 or to == power: continue` (llm.nim:628-629). `applyPress`
  independently drops any letter with `toPower < 0` (sim.nim:414-415). Public speech is only ever
  the `broadcast` field.
- Note says (§Reply schema): `letters[].to` is a "power name or `ALL` (case-insensitive)"; only an
  "unknown recipient" is supposed to be dropped. (Pledges do handle `ALL` — llm.nim:645-650.)

### N9 — `docker_smoke.sh` asserts less than §CI jobs describes
- Where: `tools/ci/docker_smoke.sh:247-297`
- Observed: the script asserts no `player_failure.json`, `results.json` present, non-empty and
  valid UTF-8 JSON, `len(results.names) == seats` and `len(results.scores) == seats`, and that the
  replay file is non-empty and parses as UTF-8 JSON. It **prints** `episode end reason: <reason>`
  (line 278-280) but does not assert it; it does not validate `results.json` against
  `results_schema`, and it does not check that the replay carries `events`/`results`/`names`/
  `policyNames`/`powers`/`config`.
- Note says (§CI jobs, docker-smoke): "asserting `results.json` validates against `results_schema`,
  `reason == "complete"`, seven scores, and that the written `.replay` … carries `events`,
  `results`, `names`, `policyNames`, `powers` and `config`."
- The note also says the script is "copied from the same templates", and it is: the only diff
  against `coworld-builder/templates/tools/ci/docker_smoke.sh` is the `<slug>`/`<IMAGE>`/`<SEATS>`
  substitution (28 diff lines, all comments + three defaults). The two halves of the note disagree;
  the code follows the copy-verbatim half. The checklist (item 6) only requires the four
  seat-count invariants, which are present verbatim (docker_smoke.sh:106-151). The observed run
  printed `smoke OK: seats=7 … reason=complete`.

### N10 — Byte-sliced error text in `llm.nim` (log-only, inherited from the starter)
- Where: `src/cogplomacy/llm.nim:596-600, 730, 739, 744, 752-753`
- Observed: model/HTTP text is cut with byte ranges (`head[0 ..< 160]`,
  `response.body[0 .. min(response.body.high, 400)]`) rather than `runeSubStr`, so a cut can land
  mid-rune. Those strings only ever become `CogplomacyError` messages, which `decideAll` catches
  and `echo`es (llm.nim:796-799) — no path puts them into an event, `notes`, `tableStateJson` or
  the replay. Byte-identical to the starter (`cogame-bullwhip/src/bullwhip/llm.nim:327, 366, 375,
  380`).
- Checklist item 9 names "captured errors" among the strings that reach the replay; these do not
  reach it. Everything that does is rune-cut (see Traced).

### N11 — With `episodeTimeoutSeconds <= 0` there would be no play deadline
- Where: `src/cogplomacy/server.nim:323-333` and `:348`
- Observed: `playDeadline` is `0.0` when `timeoutSeconds <= 0.0`, and the pre-batch check is
  `if playDeadline > 0.0 and epochTime() > playDeadline` — so a non-positive timeout disables the
  60 % budget entirely. Unreachable through the manifest (`episodeTimeoutSeconds` is
  `minimum: 60`, `coworld_manifest_template.json:92-98`, default 1200) and the loop still
  terminates at the year cap, so this is a latent hole rather than a live one.

### N12 — Two of the nine event kinds are not required by the round-trip test
- Where: `tests/test_sim.nim:396-406`
- Observed: every event the episode produced is round-tripped and compared
  (`$eventToJson(round) == $eventToJson(event)`, test_sim.nim:402-403), but the presence assertion
  lists only `evStart, evPhase, evPress, evOrders, evAdjudicate, evCentres, evEnd` — `evRetreat`
  and `evBuild` are not required to appear.
- Note says (§Tests, test_sim): "event JSON round-trips … for **all nine kinds**".

### N13 — Checklist item 7's "tuned with a grid harness" has no artefact in the tree
- Where: `src/cogplomacy/llm.nim:194-308` (both baselines), `tests/test_bot.nim:90-172`
- Observed: neither baseline has a numeric parameter to tune — `expander` is a fixed 4-level rank
  ordering with code-order tie-breaks (llm.nim:199-212) and `hedgehog` is unconditional
  hold/support-hold (llm.nim:285-308). There is no tuning script anywhere in the repo. The nearest
  evidence is the seeds-1..8 sweep (test_bot.nim:91-98) and the mixed-table assertion that
  `expanderTotal > hedgehogTotal` (test_bot.nim:164-172).
- Reported for the judge to weigh against item 7's second sentence; the first sentence
  (all-scripted episode to `reason == "complete"` with every action inside legal bounds) is
  asserted at test_bot.nim:95-98 and 141-147.

### N14 — Minor, recorded for completeness
- `tests/test_map.nim:118-127` ("a coast's fleet adjacency is a subset of the province's") builds
  `whole` as the union over the province's own nodes and then checks each node's neighbours are in
  that union — true by construction, so the assertion cannot fail.
- `types.nim:111` adds a fifth `PhaseKind`, `pkDone`, which is not in the note's list
  (§types.nim). It surfaces as `"phase":"done"` in `tableStateJson` (sim.nim:990) after `settle`.
- `sim.nim:956-965`: the frame's `stabs` array is taken from the most recent `adjudicate` event
  regardless of phase, so stabs persist visually into the next press/orders frames. The per-seat
  `stabbedThisTurn` flag *is* cleared each phase (sim.nim:189-190, 200-201).

---

## Traced and consistent

**Resolution rules (§The movement-phase resolution).**
- Step 1 own-unit filter / one-order-per-unit / missing-order-holds: `sim.nim:595-619`
  (`parseOrder` rejects a province holding no unit as `notthere` and another power's unit as
  `wrongunit`, orders.nim:172-177; unordered units get `H` at sim.nim:615-619). See N3 for the
  illegal-order interaction.
- Step 2 legality repair and the six reasons: `orders.nim:157-317`. Fleet inland/unreachable →
  `wrongunit`/`nonadjacent` (223-235); army to sea → `wrongunit` (210-211); non-adjacent with no
  convoy → `nonadjacent` (215-217); support of a non-adjacent destination → `nonadjacent`
  (259-260, 278-279); support/convoy of a unit that is not there → `notthere` (252-254, 295-297);
  army ordering a convoy → `wrongunit` (283-284); fleet convoyed → `wrongunit` (221-222);
  convoying fleet not at sea → `wrongunit` (285-286); two reachable coasts unnamed →
  `ambiguouscoast` (236-237), exactly one → filled silently (238). `tests/test_adjudicate.nim:222-258`
  pins all of them, including `F BOT - STP` → `STP/SC` and `F MAO - SPA` → `ambiguouscoast`.
- Step 3 void unmatched supports/convoys: `adjudicate.nim:67-91`; a void support leaves the unit
  holding at strength 1 (`holdStrength`, adjudicate.nim:213-224, counts only `okSupportHold` that
  `supportCounts`). Test 16 (test_adjudicate.nim:215-220).
- Step 4 convoy paths, including DATC 6.G (adjacent + convoy path resolves as a land move unless
  `VIA CONVOY`): `adjudicate.nim:59-65` (`isConvoyed`) and `120-165` (`pathOk`, walking only fleets
  whose convoy order matches and that survived). No path ⇒ `orNoConvoy` and the army stays
  (adjudicate.nim:399-400; test 13 asserts the origin is not vacated).
- Step 5 the four strengths: hold `adjudicate.nim:213-224`, attack `226-241` (including the
  self-dislodgement zero at 238-240 and the exclusion of supports from the occupant's power at
  241), defend `243-244`, prevent `246-252`. Success test `adjudicate.nim:256-275` — beats hold or,
  head-to-head, defend, and strictly beats every other mover's prevent. Kruijswijk marks and cycle
  detection at `adjudicate.nim:299-338`; the two backup rules at `277-297`.
- Step 6 cut supports with both exceptions: `adjudicate.nim:169-190`. Same-power attacks never cut
  (182-183); a convoyed attack whose path failed never cuts (184-185); an attack out of the
  province the support is aimed into cuts only if it succeeds, i.e. dislodges the supporter
  (186-189). Tests 5, 6, 7.
- Step 7 dislodgements with the attacker's origin recorded: `adjudicate.nim:367-378`.
  Step 8 standoffs (two or more bounced moves into one province, sorted by code):
  `adjudicate.nim:380-388, 419-420`, barred for retreats at `orders.nim:443, 454`.
- Step 9 retreats: destinations `orders.nim:435-458`; missing/unparsable/illegal ⇒ disband
  (`orders.nim:466-520`, `sim.nim:697-711`); two units to the same province both disband
  (`sim.nim:662-674`, the `counted[move.to] == 1` gate).
- Step 10 Fall-only ownership then an immediate solo check: `sim.nim:297-314` called from
  `afterMovement` only in `seFall` (316-324), `checkSolo` at 325. `tests/test_sim.nim:129-140`
  asserts the table is unchanged until Fall orders resolve.
- Step 11 builds/disbands: entitlement `delta = centres − units` (`sim.nim:220-221`), builds only
  in vacant owned home centres (`orders.nim:531-544`, `parseAdjustment` 586-596), surplus waived
  (`sim.nim:792`), disbands exact with civil disorder filling the rest (`sim.nim:808-814`), the
  civil-disorder pick being the unit furthest from the nearest owned home centre on its own graph
  with code tie-break (`sim.nim:734-754`). `tests/test_sim.nim:169-205`.
- Step 12 elimination: `sim.nim:272-276`, and eliminated powers are excluded from every pending set
  (`livePowers`, sim.nim:161-164, used at 193, 204, 228). Their seats still receive state frames
  carrying `"eliminated"` (`server.nim:142`).
- Solo at 18 or last-owner-standing, score 1.0/0.0: `sim.nim:254-270`, `sim.nim:147-154`;
  `tests/test_sim.nim:207-242`, `tests/test_score.nim:61-88`.
- Scoring `c/34` with a constant denominator, sum ≤ 1: `sim.nim:154`, `tests/test_score.nim:26-52,
  104-114`. The three `reason` values and the `""`-while-running rule: `sim.nim:865`,
  `tests/test_sim.nim:262-269`. The smoke run's `results.json` shows
  `scores=[0.088…, 0.088…, 0.1176…, …]` summing to 24/34.
- The map itself: I re-parsed `mapdata.nim` and confirmed 75 provinces (19 sea, 14 inland, 42
  coastal = 56 land), 34 centres, home-centre counts 3/3/3/3/3/4/3, `ArmyAdj` and `FleetAdj` both
  fully symmetric with no missing node, no army edge touching a sea, no fleet edge touching an
  inland province, 64 fleet nodes (19 + 42 + 3 split coasts), and the 22 opening units. I also
  spot-checked ~40 border lists against the standard board (BUL/EC, BUL/SC, SPA/NC, SPA/SC,
  STP/NC, STP/SC, MAO, NTH, ION, BLA, CON) and found no error. `tests/test_map.nim` pins the same
  properties.

**Decision path.** `decideAll` (`llm.nim:755-804`) builds **one** `RequestBatch` per attempt and
fires it with a single `curl.makeRequests` (llm.nim:779-788) for every open seat — the
simultaneous-decision rider is satisfied, and the server calls it once per phase outside the lock
(`server.nim:368`). Scripted seats and every seat when `client.disabled` are answered without
touching the network (llm.nim:769-775). Parsing is tolerant (`extractJsonObject` takes the first
`{`…last `}`, llm.nim:590-601; fenced and prose-wrapped fixtures at test_bot.nim:202-208). A reply
is invalid only for a non-object or a missing/wrong-typed required key (llm.nim:681-692); illegal
contents are repaired (test_bot.nim:210-240). Exactly one retry, carrying the note's hint verbatim
(`for attempt in 0 .. 1`, llm.nim:776; hint at 783-785). Anything still failing is answered by
`expander` and logged with the note's exact line, `cogplomacy: seat N falling back to scripted
decision` (llm.nim:801-804). 401/403 disables the client for the episode (llm.nim:729-737), 429 and
"Model access is denied" rotate the Bedrock candidate (llm.nim:731-741, 100-108). The server's
belt-and-braces `try/except` around each apply falls back to `expander` (server.nim:373-382).
*One nuance for phase 60:* the per-seat fallback is recorded only in stdout — the event's
`scripted` flag is `scripted[seat] != skNone or client.disabled` (server.nim:372), which is exactly
what the starter does (`cogame-bullwhip/src/bullwhip/server.nim:296`).

**Every wait and its bound.** Player connect: `while epochTime() < deadline` with
`deadline = start + playerConnectTimeoutSeconds` (server.nim:278-286, default 180). Prompt grace:
≤ 5 s (server.nim:291-300; see N5). LLM batch: `client.timeoutSeconds` = `llmTimeoutSeconds`
(default 45, schema max 300) passed to `makeRequests` (llm.nim:788; curly's per-request timeout,
`curly.nim:711-715`), at most two batches per phase. Play budget: `PlayBudgetFraction = 0.6`
(server.nim:254) of `COWORLD_TIMEOUT_SECONDS` or `episodeTimeoutSeconds` (server.nim:323-332) —
720 s of 1200 — checked **before every batch** inside the lock (server.nim:346-354) and settling
with `reason = "deadline"` via `endEarly` (sim.nim:248-252). Pacing: `turnDelayMs` clamped by
`PacingBudgetMs div (years*7)` in `sampleEpisode` (sim.nim:106-115), applied at server.nim:386-390.
Shutdown: `sleep(500)` + `ShutdownGraceSeconds = 20` then `quit(0)` (server.nim:238-252). Worst
case I can construct: 720 s (deadline) + one in-flight batch with its retry (≤ 90 s) + ~0.5 s +
20 s ≈ 831 s against the 1200 s kill. The play loop cannot spin without progress: every iteration
either applies a decision for every pending seat (each apply removes the seat from `pending`,
sim.nim:458, 656, 728, 836) or hits `done`/`seats.len == 0`/the deadline and breaks
(server.nim:344-363). The adjudicator's recursion carries its own `ResolveStepCap = 200_000`
(adjudicate.nim:46-49, 300-302). The player's `receiveMessage()` is a blocking read
(cogplomacy_player.nim:51, whisky default `timeout = -1`), bounded by the game's own bounded
lifetime; a dead socket raises and is caught, exiting 0 (cogplomacy_player.nim:74-79).

**Truncation, on rune boundaries.** `cleanText` uses `runeLen`/`runeSubStr` and marks the cut with
`…` (sim.nim:79-86). Applied to: broadcast 400 (sim.nim:404, llm.nim:619), letter text 400
(sim.nim:418, llm.nim:631), letters capped at 6 (sim.nim:411-413, llm.nim:623-624), pledges capped
at 4 (sim.nim:426-427, llm.nim:635-636), notes 800 in all four phases (sim.nim:443, 641, 715, 822;
llm.nim:658, 665, 672, 679), orders 34 × 32 runes (sim.nim:633-637 + 601-603; llm.nim:603-610,
664), retreats 12 × 32 (sim.nim:692-699, llm.nim:671), adjustments 10 × 32 (sim.nim:770-774,
llm.nim:678), player prompt 4000 runes via `runeSubStr` (server.nim:512-513). `tests/test_sim.nim:297-315`
feeds 600 repeats of `🕊️` and asserts `runeLen <= cap`, `validateUtf8(...) == -1` and the `…`
marker; `tests/test_viewer.nim:20-35, 102-134` repeats it across the whole payload and the derived
`states`. The CI smoke replay decodes as UTF-8 (I decoded the artifact).

**Replay writer.** `server.nim:173-196` writes `protocol`, `names` (aliases), `policyNames`
(policies), `powers`, `config{years,seed,press,sampled}`, `events`, `results`. I inspected the
artifact from run 32722300699: all seven keys present, 40 events over the nine-kind vocabulary
(`start`, `phase`×5, `press`×14, `orders`×14, `adjudicate`×2, `centres`, `build`×2, `end`), aliases
`['Tinker','Gasket',…]` distinct from `policyNames` `['Sprocket','Gizmo',…]`, `config
{'years':1,'seed':7,'press':True,'sampled':True}`. `eventToJson`/`eventFromJson` (sim.nim:1050-1225)
omit-and-default symmetrically; `tests/test_sim.nim:396-403` asserts the round trip on every event
produced (see N12).

**Viewer re-derivation and provenance.** The wasm module parses the replay and calls the same
`replayMatch` over the same `sim`/`adjudicate` modules
(`replay-viewer/cogplomacy_replay.nim:24-52`), and the server's replay mode does the same
(`server.nim:198-202`); the renderer draws `payload.states` only (`renderer.js:1224-1249`).
`client/chrome.css` is byte-for-byte bullwhip's 467 lines plus one appended block from line 469
(verified with `diff`: the only hunk is `@@ -465,3 +465,187 @@`). `client/replay.html` is
bullwhip's page with the title/wordmark changed, `relayout()` added and **one** appended element,
`<div id="centrebar">` between `#scorebug` and `#board-wrap`; every starter id survives
(`replay.html:9-39`), and `tests/test_viewer.nim:199-211` asserts the id list plus
`id="viewpanel"` **absent**. `replay-viewer/{config.nims,cogplomacy_replay.nim,static_replay.js,index.html}`
are all bullwhip's with rename-only diffs; `MODULARIZE=1` + `EXPORT_NAME=CogplomacyReplayModule`
(config.nims:37-38) match the shell's factory call `CogplomacyReplayModule()`
(static_replay.js:140) and the `_malloc`/`HEAPU8.set`/`_cp_load_replay` handshake
(static_replay.js:92-104) — same starter on both sides, no `onRuntimeInitialized` anywhere.
`data-replay-loaded="true"` is set at the end of `attachReplay`'s `makeRenderer` callback after the
first `renderer.draw` (renderer.js:1252-1280, identical to bullwhip renderer.js:1386-1390);
`data-replay-error` is set in the shell's own `fail()` and removed on a successful retry
(static_replay.js:44-58, 107, 136). Transport rules: `relayout()` sets `--band` and `--hudscale` on
`document.documentElement` and calls `fit()` (replay.html:54-65, index.html:51-62), bound to
`load`, `resize` and the feed toggle's dispatched resize (renderer.js:985-989); `#transport` is the
last flow child of `#stage` and `#endscreen` is `position:absolute; inset:0` inside `#board-wrap`
(replay.html:23-35, chrome.css:48-56, 95, 128-136, 374-383), `#loading { bottom: var(--band); }`
(chrome.css:613); every `setIndex` calls `updateEndscreen(...)`, which does
`classList.toggle("show", !!show)` (renderer.js:1245-1248, 909), so every seek dismisses the
endcard. Beats are `<button type="button">` with `aria-label`/`title` and an `onclick` seek
(renderer.js:1371-1391), the container keeps its pointer drag-to-seek and ignores pointerdown on a
beat (renderer.js:1174-1188), and all eight kinds emitted (`press, orders, adjudicate, stab,
retreat, build, centres, end`, renderer.js:1293-1311) have a CSS rule (chrome.css:578-585) over the
starter's base `.beat-marker` (chrome.css:195-203), which supplies the seat tint through `--tc`.
Legibility: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (chrome.css:496, also inherited at
280-291), `.plate-units { display: none; }` and a 4-column scorebug under 640 px
(chrome.css:617-623), 2 columns under 420 px (chrome.css:626-629), province labels restricted to
the action box under 640 px (renderer.js:352-372, 170-206). The naming guard holds:
`markDiploBeat`/`buildCentreBar` (renderer.js:1371, 1396) and `tests/test_viewer.nim:144-183`
asserts the two name sets are disjoint.

**Manifest.** `num_agents: 7` in `standard` (line 349), `gunboat` (384) and `certification` (417),
with `minimum: 7, maximum: 7` in `config_schema` (70-75); `SMOKE_SEATS` default `7`
(docker_smoke.sh:54) is the independent second declaration and the four invariants are enforced
before any container starts (docker_smoke.sh:106-151, all messages prefixed `SEAT-COUNT FAIL:`).
`"replay_viewer": {"bundle": "static-replay-viewer"}` (line 16-18). `game.docs` is
`readme` + `pages[rules.md, map.md]` in the exact `{"type":"text","value":…}` /
`{"id","title","content"}` shape (227-250). `game.protocols` carries both `player` and `global`
(217-226). `config_schema` and `results_schema` match the note field for field, including
`additionalProperties: false`, the 7-item arrays and `scores` bounded to `[0,1]`.
`episode_timeout_minutes: 20` (line 13) is a top-level key the lineage already uses
(`cogame-parley` 20, `cogame-moba` 60, `cogame-factorio` 60) and agrees with the 1200 s default.
`{{COGPLOMACY_IMAGE}}` matches the compose service name `cogplomacy` (compose.yaml:2-3).

**Workflows and scaffold.** All three workflows present and parsed; `ci.yml` and
`coworld-release.yml`/`coworld-submit.yml` differ from `coworld-builder/templates/` only by the
`<slug>`/`<IMAGE>`/`<SEATS>` substitution. `coworld-release.yml` order is build (line 153) →
certify (167) → upload-policies (206) → upload-coworld (304) → secret put (342). The placeholder
gate `grep -n '<slug>\|<IMAGE>\|<SEATS>' …` returns no match over all five files. Modes:
`tools/build_replay_viewer.sh` 100755, `tools/ci/docker_smoke.sh` 100755,
`tools/ci/viewer_smoke.mjs` 100755 (and byte-identical to the template).
`tools/ci/policies.json` has four policies — two `PLAYER_PROMPT` champions
(`cogplomacy-diplomat`, `cogplomacy-opportunist`) with the second carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus `PLAYER_SCRIPTED` `expander` and
`hedgehog`.

**CI at the reviewed sha (checklist item 1 and 13).** `gh run list -R Metta-AI/cogame-cogplomacy
--branch main -w ci.yml` → run **32722300699**, conclusion **success**, head commit
"Play the expander baseline for a seat that never delivers a prompt" (= 1b9ddad). Jobs: `test` 30 s
(all six test files run twice, debug and `-d:release` — I read the twelve `nim r` group headers in
the log), `docker-smoke` 1 m 19 s (`game=cogplomacy seats=7`, seven player containers from the cert
seat mix, `episode end reason: complete`, `smoke OK: seats=7 results=409B replay=23728B
reason=complete`; **no `SEAT-COUNT FAIL` anywhere in the log**), `wasm-viewer` 1 m 30 s with
`needs: docker-smoke` and the `Load the bundle in a real browser` step present, not
`continue-on-error`, printing
`{"loaded":true,"ms":294,"clock":"SPRING 1901 · PRESS · WAITING ON 7","scorebug":"AUSTRIA Sprocket ▶ 3 3 UNITS …","feed_lines":39}`
and `scrub readouts: 0%=… 50%="FALL 1901 · PRESS · WAITING ON 6" 100%="WINTER 1901 · FINAL ·
RUSSIA 4 CENTRES"`. "No test loosened": `git log --oneline -- tests/` shows tests were added in a
single commit (8a48336) and never touched since; there is no deletion, widened tolerance or skip
to find.

**Two name spaces.** In-game the seat is only a power: `systemPrompt` interpolates
`PowerNames[power]` only (llm.nim:407-418) and `userPrompt` never touches
`config.players[i].name` (llm.nim:545-586); `tests/test_sim.nim:368-384` scans both prompts for
every policy name **and** every cog alias across a whole episode. Spectator-side, the replay
carries `names` (aliases) and `policyNames` (server.nim:174-186) and the viewer's name map swaps
policy names in for non-baseline seats while leaving baseline fillers on their alias
(renderer.js:644-680). The final player frame carries aliases, results carry policy names
(server.nim:218-231, sim.nim:842-866).

**The builder's seven deviations, each on its merits.**
1. `sim.board: Board` (types.nim:145-149, sim.nim:51) — `board.units` and `board.owner[34]` are
   exactly the note's two fields, bundled so `adjudicate(board, orders)` can stay pure. No
   behaviour follows from the packaging. Fine.
2. Replaced test examples — the note's case 5 (`F TRI S A ALB - GRE`) is unplayable on the real
   board: TRI's fleet adjacency is `ADR ALB VEN` (mapdata.nim:288), so a fleet in Trieste cannot
   support into Greece. The substitute (`F ION S A ALB - GRE`, ION–GRE adjacent at mapdata.nim:239,
   cut by `F AEG - ION`) tests the same rule on a legal board (test_adjudicate.nim:92-100). Same
   for the dislodged-supporter case, which the note left board-free. Fine.
3. Map polygons from a committed script — `scripts/art/build_map1901.py` (247 lines) is in the
   repo and `data/map1901.json` is committed; I parsed it: 75 provinces, polygons 8–17 points, a
   `label` and `dot` per province, coast anchors for SPA/STP/BUL, `space 1000×800`.
   `tests/test_viewer.nim:226-250` pins name/kind/centre/poly-length against `mapdata.nim`. Fine.
4. One-sea convoy enumeration only (orders.nim:340-358, with the comment saying so) — longer
   convoys still parse (orders.nim:213-218) and adjudicate (the three-fleet chain passes at
   test_adjudicate.nim:173-178). I computed the enumeration size for all 22 opening units: the
   largest is 19 orders (A MUN, A VEN), far under `MaxLegalOrders = 64`, so the cap is not silently
   truncating the list at 1901. Fine.
5. `episode_timeout_minutes: 20` — see Manifest above. Fine.
6. 20 s shutdown grace (server.nim:37-40, 248-252) — it runs *after* results and replay are
   written, and the smoke shows the whole container life at 22 s. Costs 20 s of a 480 s margin.
   Fine.
7. Player exits 0 on a dead socket (cogplomacy_player.nim:45-79) — the game's `quit(0)` can outrun
   mummy's queued final frame; the smoke wrote no `player_failure.json`. Fine.

---

## Could not determine

- **Whether the Szykman branch of `backupRule` is ever the branch that fires.** Reading
  `adjudicate.nim:277-297`, the paradox branch requires the *dependency cycle* to contain a
  convoyed move. Tracing test 15 (`F LON S F WAL - ENG` / `F WAL - ENG` / `A BRE - LON` /
  `F ENG C A BRE - LON`) by hand, the only index that enters `depList` is the non-convoyed
  `F WAL - ENG` — `pathOk` recurses into it from `convoyFleetDislodged` without ever guessing the
  convoyed move — so `paradox` is false and the **circular-movement** branch resolves it to
  success, which happens to produce exactly the outcomes the note and the test require (and CI is
  green on that test). This is an inference from reading, not an execution; what would settle it is
  an instrumented run over a paradox suite (Pandin's paradox, the DATC 6.F.* family) checking which
  branch fires and whether `szykman[]` is ever set. I found no case where the outcome is wrong.
- **Whether the appended endcard alliance graph and the press/stab animations render as the note
  describes.** `startAllianceGraph` (renderer.js:1604-1668) and `drawPress`/`drawStabs`
  (renderer.js:540-628) read the right fields, and the viewer smoke drew a first frame, but the
  smoke's screenshot is at index 0 and the smoke replay contains no pledges or stabs (all seven
  seats were silent baselines), so nothing exercised those paths. A replay with live LLM press
  would settle it.
- **Live LLM behaviour** (auth-failure disable, model rotation, the retry batch). No credentials in
  CI or in this sandbox, so `decideAll`'s network path is read-only evidence; `tests/test_bot.nim:174-190`
  covers only the credential-less branch.
