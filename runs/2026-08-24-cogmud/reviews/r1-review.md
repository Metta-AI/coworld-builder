# r1 review — cogmud

Repo: `/workspace/cogame-cogmud` @ `dd6f018d7b135f3e5cfbbd0349193dbf04ddfa9b` (main)
Starter: `/workspace/starters/cogame-bullwhip` (read-only, used for provenance diffs)
Design note: `/workspace/coworld-builder/runs/2026-08-24-cogmud/design.md`
(byte-identical copy committed at `docs/plans/2026-08-24-cogmud-design.md` — verified with `diff -q`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the
simultaneous-decision batch rule)
Files read: 45 (all 8 `src/` Nim files, all 4 viewer files, all 5 `client/` files, all 6 test
files, the manifest + its 8 generator sources, all 3 workflows, all 4 `tools/` files, both
Dockerfiles, `compose.yaml`, `cogmud.nimble`, `nimby.lock`, plus 9 starter files for diffs)

Findings are numbered F1… throughout, as the brief requires.

---

## Blocking

### F1 — Checklist item 7's "tuned with a grid harness, not guessed" has no artefact anywhere in the tree

- Where: `tests/test_bot.nim:157-164`; `src/cogmud/llm.nim:199-343`; absence across the whole repo
- Observed: item 7's first two clauses are fully satisfied — `tests/test_bot.nim:66-94` runs
  all-`factor`, all-`magpie` and a mixed table over seeds `[1, 7, 11, 42]` to the natural end and
  asserts `run.sim.reason == "complete"` (line 74), `event.intent != iNone` (line 82),
  `event.sentence.runeLen <= MaxSentenceLen` (83), `coin >= 0` (93) and
  `carried(seat) <= CarryLimit` (94). The third clause has nothing behind it. The baselines carry
  hardcoded numeric thresholds that are exactly the kind of thing the clause is about:
  - `factor` rule 3, `llm.nim:236` — `if sim.bid(npc, item) >= Items[item].baseValue`
  - `factor` rule 4, `llm.nim:245` — `or Items[item].baseValue >= 8`
  - `magpie` rule 2, `llm.nim:295` — `if sim.turn mod 3 == 0`
  - `magpie` rule 3, `llm.nim:312` — `>= Items[item].baseValue + 1`
  - `magpie` rule 4, `llm.nim:320` — `if price <= Items[item].baseValue - 1`
  I grepped the whole tree for `grid|sweep|harness|tuning|tuned` (excluding `docs/plans/`): the
  only hits are `world.nim:23` ("0..100 grid"), `ci.yml:297` (an unrelated comment),
  `test_bot.nim:161` (a `checkpoint` comment, "so tuning drift is visible"), and three
  `grid-template-columns` CSS strings. There is no sweep script, no committed sweep output, and
  no `runs/` artefact referenced from the repo. The design note never mentions a grid harness
  either (grepped: the word "grid" appears only in map-coordinate and CSS contexts, lines 78,
  1040, 1056, 1058, 1070).
  The nearest things that exist are: a 200-seed × 6-seat sweep in `tests/test_feasibility.nim:67`
  (which tunes nothing — it validates the *world tables* against the horizon), and a 4-seed
  ordering assertion in `test_bot.nim:157-164`
  (`check meanScore(factor) > meanScore(magpie)`), which asserts a ranking, not a search.
- Checklist item: 7 — "Scripted baseline plays full episodes legally. … **The baseline's
  parameters were tuned with a grid harness, not guessed.**"
- Why blocking: it is a named clause of a named checklist item, and I can find no evidence for it
  in the tree or in the CI logs. What would settle it: a committed harness (a `tools/` or
  `tests/` script that sweeps the five constants above over seeds and prints the mean-score
  surface), or its recorded output cited in `log.md`. I am reporting the absence, not asserting
  that the constants are wrong — the constants *are* enforced against outcomes by
  `test_bot.nim:118-164` and `test_feasibility.nim:125-136`, which is a weaker guarantee than the
  checklist names.

No other checklist item is falsified. Items 1–6 and 8–14 are traced below.

---

## Non-blocking

### F2 — `.plate-robbed` (the red ROBBED chip) can never render: `state.recentRobbed` is never produced

- Where: `client/renderer.js:1284-1286`; `src/cogmud/sim.nim:1122-1141`; `src/cogmud/server.nim:84-91`
- Observed: the scorebug emits the chip only when
  `seat.robbed && state.recentRobbed && state.recentRobbed.indexOf(index) >= 0`.
  `tableStateJson` (sim.nim:1122-1141) returns exactly
  `world, seats, rooms, npcs, offers, chronicle, town, turn, turns, turnsPlayed, phase,
  gameDone, reason` — no `recentRobbed`. `snapshotJson` (server.nim:84-91) adds only
  `type, game, policyNames, events, started, done, connected`. A repo-wide grep for
  `recentRobbed` returns two hits, both the reader in `renderer.js`. The CSS rule
  `.plate-robbed` exists (`client/chrome.css:509-517`) and is dead.
  The design says (§Readouts, line 1160-1162): "with a red `ROBBED` chip for the turn after a
  seat is victimised and an amber `HIRED` chip while it is somebody's retainer." The `HIRED`
  chip works — it reads `seat.retainerTurns > 0` (renderer.js:1287), which `tableStateJson`
  does emit (sim.nim:1066).
- Not on the checklist. Legibility/`#scorebug` content is not a checklist item; item 11 covers
  only `.plate-name` at 360 px, which is satisfied (F17).

### F3 — the amber employer↔hireling tether described in the design is not implemented

- Where: `client/renderer.js:514-516` (shield only); design.md:1140-1141
- Observed: `drawToken` draws the amber shield badge on `seat.retainerTurns > 0`
  (`drawShield`, renderer.js:548-566) — that half of the design is present. The design also says
  "with a thin amber tether drawn to its employer while they share a room". Grepping
  `client/renderer.js` for `tether` returns nothing, and for `retainerOf` returns nothing: the
  renderer never reads the field, though `tableStateJson` emits it (sim.nim:1065).
- Not on the checklist.

### F4 — `salienceOf` for `iSay` reads the `say` *field*, so a spoken line lifted out of the sentence never reaches 30

- Where: `src/cogmud/sim.nim:305-306`; `src/cogmud/sim.nim:811-813`; `src/cogmud/parse.nim:543-545`
- Observed: `of iSay: if event.say.runeLen > 40: 30 else: 20`. `emitAct` sets
  `event.say = sim.acts[seat].say` (sim.nim:812) — the reply's `say` field only. For an `iSay`
  act the actual spoken text lives in `intent.spoken` (set from the quoted span by
  `liftSpeech`, or from the whole sentence at `parse.nim:544-545`) and is broadcast at
  `sim.nim:853-855`, but is never copied into `event.say`. So an `iSay` act with a 100-rune
  spoken line and an empty `say` field scores 20, not 30.
  The design's salience table (line 824) says "speech-only act (+10 when the line exceeds 40
  characters)"; the manifest's global protocol repeats it ("a spoken line 20 (30 when it runs
  past 40 characters)"). Both are ambiguous about which string is measured; the code picks the
  `say` field.
- Not on the checklist.

### F5 — the `iGive`-to-a-non-Guild-shopkeeper salience branch (25) is unreachable

- Where: `src/cogmud/sim.nim:299` vs `src/cogmud/sim.nim:498-502`
- Observed: `salienceOf` has `elif event.npc >= 0: 25` for an `iGive` whose `reason == oOk`.
  `resolveGiveNpc` sets `result.reason = oNoMatchingCommission` unconditionally when
  `npc != GuildNpc` (sim.nim:498-499), so an `iGive` with `npc >= 0` and `reason == oOk` can only
  be a Guildhall delivery, which the previous branch already caught. Handing goods to any other
  shop therefore scores 5, not 25.
- Not on the checklist; the design's salience table has no row for this case either.

### F6 — the bottom-strip chart re-computes score in JS from hardcoded constants instead of the payload

- Where: `client/renderer.js:1207` (`var values = [6, 7, 8, 9, 11, 14];`), `1211-1213`
  (`4 * d + (d >= 2 ? 8 : 0)`), `1215` (`(wealth + 3 * points - 40) / 40`)
- Observed: `chartFrom` duplicates `Items[].baseValue`, `PointsPerUnit`, `CompletionBonus`,
  `Quest.count`, `PointValue`, `StartCoin` and `ScoreScale` as JS literals rather than reading
  `world.items[i].value` — which *is* in the payload (`worldJson`, world.nim:173-178) and *is*
  used elsewhere in the same file (`itemName`, renderer.js:125-130). A change to any of those
  constants would silently desynchronise the chart from the real score. Note the authoritative
  numbers on screen — the scorebug's `score`, the endcard's rows — come from
  `state.seats[i].score` / `payload.results`, i.e. from the wasm re-derivation, so checklist
  item 2 is not affected; only the trend line is a JS re-computation.
  `chartFrom:1224` also hardcodes `event.npc === 4` for `GuildNpc`, as do `beatKind:919`
  and `actLine:947`.
- Not on the checklist.

### F7 — `tests/test_sim.nim`'s observation-split assertion for other seats' commissions is a tautology

- Where: `tests/test_sim.nim:773-775`
- Observed:
  ```nim
  for quest in 0 ..< Quests:
    check ("\"delivered\":" & $sim.quests[other][quest].delivered) ==
      ("\"delivered\":" & $sim.quests[other][quest].delivered)
  ```
  Both sides of the `==` are the identical expression; `text` (the seat's `playerStateJson`) is
  never consulted. The assertion cannot fail. The design's test item 13 (line 1352-1354) asks
  that "each seat's `playerStateJson` contains no other seat's `coin`, `items`, `quests`, `notes`
  or `score`". The *other* clauses of that item are really asserted: `notes` at line 771-772,
  the room id at 776, other NPCs' books at 779-782, and the converse (every referent named) at
  784-800; and `test_sim.nim:806-814` asserts `view{"score"}`, `view{"seats"}`, `view{"npcs"}`
  and `view{"rooms"}` are all nil. I separately traced `playerStateJson` (sim.nim:1157-1268) and
  confirm it emits nothing about another seat but `sim.names[other]` for co-located cogs
  (1193-1196), retainer names (1224-1229) and offer-from names (1218) — no other seat's purse,
  pack, quests, notes or score. So the redaction is correct; the assertion is not.
- Not on the checklist. This test file has exactly one commit in the repo's history (`c8ffb6c`,
  all files `A`), so this is not a loosening under item 1 — it was written this way.

### F8 — the restock test computes an expected stock array and never asserts against it

- Where: `tests/test_sim.nim:290-301`
- Observed: `expected` is built by replaying the round-robin (lines 292-297) and then never
  compared to `sim.npcs[npc].stock`. The assertions that follow are `stock[item] <= StockCap`
  (299), `stock[item] >= opening[npc][item]` (301) and `stock[item] == 0` for non-trade items
  (305). The design's test item 6 (line 1325-1326) asks that "each NPC's items each gain exactly
  `12 div tradeList.len` (± the round-robin remainder)"; the exact-gain half is not asserted.
  I traced the implementation by hand (`openTurn`, sim.nim:223-227): index `sim.turn mod
  trade.len`, `+1`, capped at `StockCap`, which is what the design specifies.
- Not on the checklist.

### F9 — `tests/test_parse.nim`'s reason-coverage test asserts prose coverage, not production

- Where: `tests/test_parse.nim:387-396`
- Observed: the test iterates `for reason in Outcome` and checks `outcomeText(...).len > 0` and
  `seen == 26`. That proves `sim.nim:318-355` has a prose line for every enum value (it does),
  not the design's claim (line 1385-1386) that "Every one of the 26 outcome reasons is produced
  by at least one case in this file or `test_sim.nim`". I checked which reasons are actually
  produced across both files: `oUnparsed` is produced only inside the `in [oNoVerb, oUnparsed]`
  disjunction at test_parse.nim:437, and I found no case producing `oRejected` (it is emitted
  only by `server.nim:305-308`, which no test drives) or `oCarryLimit`.
- Not on the checklist.

### F10 — restock is skipped at turn 0; the shipped `rules.md` says it happens at every open

- Where: `src/cogmud/sim.nim:220-227` vs `scripts/manifest/rules.md:99-102` and design.md:135-136
- Observed: `openTurn` guards the restock with `if sim.turn > 0:`, commented "Restock at the open
  of every turn after the first: the world table's stock is what the shops hold at turn 0."
  The design (line 135) says "At each turn's open, every NPC adds +1 to exactly one item on its
  trade list — index `turn mod tradeList.len`", with no turn-0 exemption, and `rules.md:101`
  repeats "Every shopkeeper restocks one good" inside step 1 with no exemption.
  The guard is what makes the design's own arithmetic correct: §Prices (line 131-132) and the
  worked landmark (line 298) both price "two hides from a shop holding 8", and Tanner Oda's
  `initialStock` for hide is 8 (`world.nim:98`). Without the guard, hide would be 9 at turn 0
  and `askAt(0, 9) + askAt(0, 8) = 3 + 4 = 7`, not 9, and `test_score.nim:89` would fail.
  So the code is right and two prose sources are loose. `rules.md:45` does label the shop table
  "deals in (opening stock)", which points the same way.
- Not on the checklist.

### F11 — `iHire` clamps an unaffordable fee rather than refusing to post; the design says both things

- Where: `src/cogmud/sim.nim:606-616`; design.md:244 vs design.md:1344
- Observed: `let fee = min(max(1, intent.coin), sim.cogs[seat].coin)` then
  `if fee < 1 or sim.cogs[seat].coin < fee: result.reason = oCannotAfford`. With `coin = 10` and
  `intent.coin = 15` the offer is posted at 10. Only `coin == 0` yields `oCannotAfford`.
  The design's intent table (line 244) says "Posts a hire offer for `coin` (1 .. the seat's
  coin)" — a clamp, which is what the code does. The design's test list (line 1344) says
  "a hire offer with `coin` above the employer's purse is **never posted**" — a refusal, which
  the code does not do. `tests/test_sim.nim:644-655` exercises only the `coin = 0` case, so it
  passes under either reading. The design contradicts itself; the code follows the intent table.
- Not on the checklist.

### F12 — a hire accepted in class 4 already guards its employer in class 5 of the same turn

- Where: `src/cogmud/sim.nim:891-902` (class 4) → `904-910` (class 5); `662-663`; `369-373`
- Observed: `resolveAccept`'s `okHire` branch sets `retainerOf` and `retainerTurns = 3`
  immediately (lines 662-663). Class 5 then calls `retainersPresent(...)` (723-724), which counts
  any seat with `retainerOf == x and retainerTurns > 0` in the room — including one hired
  seconds earlier in the same turn. The design's class order (line 2207-2214) fixes cog-to-cog
  before robbery and says nothing about this interaction; the system prompt (line 481-483) says
  "for three turns the hireling cannot rob you and guards you while it stands beside you".
  Observed, not judged: it is a consequence of the class order the design specifies.
- Not on the checklist.

### F13 — goods handed to a shopkeeper enter its stock even for items outside its trade list

- Where: `src/cogmud/sim.nim:494-496`
- Observed: `resolveGiveNpc` does `sim.npcs[npc].stock[intent.item] = min(StockCap, … + units)`
  *before* the Guild/commission branch, so handing Guildmaster Vell (trade list `[rope, lamp]`,
  world.nim:109) two hides leaves `npcs[4].stock[0] == 2` for a good Vell does not deal in.
  Nothing can be bought back — `resolveBuy` checks `dealsIn` first (sim.nim:409) — and
  `tableStateJson` reports `ask`/`bid` as `0` for a non-traded item (sim.nim:1096-1097), so this
  is inert bookkeeping, but it does mean `test_sim.nim:303-305`'s "nothing outside the trade list
  ever appears" holds only in the restock test's wait-only episode.
- Not on the checklist. The design says only "the goods enter its stock" (line 241), which is
  literally what the code does.

### F14 — `client/global.html` and `client/player.html` carry the appended banner verbatim, describing elements those two pages do not have

- Where: `client/global.html:54-67`, `client/player.html:62-75`
- Observed: both pages' appended banner comment says "Two elements are APPENDED - #townbar
  between #scorebug and #board-wrap, and .treel#reel as a third row inside #transport". Grepping
  both files for `transport|reel|scrub` returns only comment lines — neither page has a
  `#transport`, a `#scrub` or a `#reel` (the starter's live pages ship none). `#townbar` *is*
  appended in both (global.html:20, player.html:20). `relayout()` on those pages therefore
  measures `transport` as `null` and sets `--band: 0px` (global.html:74-78), which is the
  correct behaviour for a page with no band, but the comment overstates what was appended.
- Not on the checklist (item 14 names `replay_broadcast.html`, whose role here is
  `client/replay.html` per design.md:1028-1032; that page is correct — see F22).

### F15 — the `wander` verb is a fourth parse-table addition not listed in `parse.nim`'s header

- Where: `src/cogmud/parse.nim:99` (`VerbEntry(token: "wander", kind: iMove, guard: vgAlways)`)
  vs `src/cogmud/parse.nim:10-19`
- Observed: the header documents exactly three deliberate additions (`off`, `have`/`has`,
  verbless purchase). `wander` is a fifth movement verb that the design's verb table (line 706)
  does not list, and it is load-bearing: `magpie`'s ramble emits `"I wander over to <room>."`
  (llm.nim:343) on every fallthrough turn, and `test_bot.nim:77` asserts zero unreadable
  scripted sentences. It *is* documented in the shipped docs page
  (`scripts/manifest/sentences.md:29`, "wander") and tested (`test_parse.nim:76`), so it is not
  undocumented — just not in the header's own list.
  I also diffed the whole verb table against design.md:706-718 and found these further additions,
  all documented in `sentences.md`: `picks` (parse.nim:113 / sentences.md:30), `asks`
  (parse.nim:180-181 / sentences.md:39-40), and the guard for `put` and `read` relaxed from the
  design's "(down)" / "(the board)" to `vgAlways` (parse.nim:122, 194 — sentences.md:31, 40
  match the code, the design note does not). Also `OfferWords` adds `bargain`/`proposal`
  (parse.nim:47, covered by sentences.md:36's "offer/deal/terms" only partially), `CoinWords`
  adds `crown`/`crowns` (parse.nim:43 / sentences.md:63-64 ✓), and `all|every|everything`
  (parse.nim:323 / sentences.md:61 ✓).
- Not on the checklist.

### F16 — smaller design-vs-code prose gaps, each verified

- `docs`: design.md:302 says the worked landmark scores **2.03**; `81/40 = 2.025` exactly.
  `tests/test_score.nim:100-101` asserts `2.025` to `1e-9` — the code and test are right, 2.03 is
  the 2-dp display. Design's own §Tests item 5 (line 1415) says "reproduces **2.03** to 1e-9",
  which is arithmetically impossible; the test does the right thing.
- `design.md:1484` lists "a live-server (`/client/replay`) replay viewer" as out of scope, but
  §Server (line 921) keeps the route and `server.nim:468` registers it, `client/replay.html`
  exists, and the manifest's global-protocol text advertises "`/client/replay` plays a recorded
  episode". The design contradicts itself; the code follows §Server, and the *manifest* declares
  only the static bundle (checklist item 3 is satisfied — see F20).
- `design.md:1116` names `tools/make_cog_colors.py`; the file is at
  `scripts/art/make_cog_colors.py`.
- `design.md:909-913`'s server pseudocode calls `openTurn()` explicitly each iteration;
  `server.nim:252-274` does not — `openTurn` is driven from `initSim` (sim.nim:274) and from
  `resolveTurn` (sim.nim:936). Equivalent, and `pendingSeats()` is read at server.nim:269 as the
  pseudocode's next line does. Calling it in the server too would double-open.
- `server.nim:317-318` sleeps `turnDelayMs` once more after the loop breaks, so a 14-turn
  episode pays 15 pacing sleeps (15 × 400 ms = 6 000 ms), still well inside
  `PacingBudgetMs = 20 000` (sim.nim:37, capped by `sampleEpisode` at sim.nim:84-85).
- `design.md:1184-1185` says "Below 560 px the map drops the room descriptions to names only".
  `drawRoomCard` (renderer.js:314-320) only ever draws `room.name.toUpperCase()`; a description
  is never drawn at any width. The *other* half of that sentence is implemented:
  `computeLayout` sets `compact: width < 560` (renderer.js:170) and `drawAwning` does
  `rows.slice(0, 1)` when compact (renderer.js:398).
- `matchHeader` (renderer.js:1258-1262) reports "WAITING ON 6" on the closing `turn` frame,
  because `resolveTurn:940-942` resets `acts[]` before `logTurn()` while `done` is still false.
  The very next frame (the `end` event's) reads `FINAL · <name> <score>`. Cosmetic; the CI
  readouts confirm the sequence works (`0%="TURN 4 / 8 · WAITING ON 6"`,
  `100%="FINAL · RATCHET 1.73"`).

### F17 — the LLM→scripted fallback is recorded only on stdout, not on the `act` event

- Where: `src/cogmud/llm.nim:704-707`; `src/cogmud/server.nim:295`; `src/cogmud/sim.nim:814`
- Observed: after the retry batch, `decideAll` logs
  `"cogmud llm: seat ", seat, " falling back to scripted decision"` (llm.nim:706) and returns
  `scriptedAction(sim, seat, skFactor)`. The server then computes
  `let wasScripted = scripted[seat] != skNone or client.disabled` (server.nim:295) — which is
  `false` for an LLM seat that fell back on this turn — and passes it into `applyAction`, so
  `event.scripted` (sim.nim:814) records `false` and the replay/results carry no trace of the
  fallback. Phase 60 must count the stdout lines.
  This is exactly what the design specifies (line 601-602: "Each fallback logs `cogmud llm: seat
  <n> falling back to scripted decision` on stdout"), and checklist item 8 says only "the
  fallback is recorded so phase 60 can count it" — the stdout line is that record. Reporting it
  so the judge can see the mechanism explicitly: the `scripted` flag is **not** it.
- Checklist item 8 is satisfied by the log line; I am not calling this blocking.

---

## Traced and consistent

**Checklist 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-cogmud --branch main -w ci.yml` → run **32685902639**,
  conclusion **success**, `headSha` **dd6f018d7b135f3e5cfbbd0349193dbf04ddfa9b** (the reviewed
  sha). Jobs: `test` success, `docker-smoke` success, `wasm-viewer` success. Every step in all
  three jobs reports `success`; no step is skipped or `continue-on-error`.
- `git log --name-status -- tests/` → a single commit `c8ffb6c`, every path `A` (added). No test
  file was modified, deleted, weakened, or gained a skip during this run.
- `ci.yml:104-150` runs every `tests/*.nim` twice (debug and `-d:release`) and `exit "${fail}"`
  after the loop, so a single failure reddens the job.

**Checklist 2 — replay re-derivation, and the viewer derives from it.**
- `replayMatch` (sim.nim:1294-1358) re-runs the recorded `act` events through `applyActionSteps`
  and, for **every** recorded `turn` event, calls `sameWorld` (sim.nim:1272-1292) — which
  compares all 9 room floors, all 5 NPC stock arrays + coin, and all 6 cogs'
  `room/prevRoom/coin/items/delivered/retainerOf/retainerTurns/robberies/robbed` — raising
  `CogmudError` on any mismatch (1322-1329). A full successful `replayMatch` is therefore a
  frame-by-frame check of every turn snapshot.
- The tamper test: `tests/test_sim.nim:870-881` mutates one NPC's coin by +1 in one recorded
  `turn` event and `expect CogmudError`. Frame count and final-frame equality:
  `test_sim.nim:829-835` asserts `frames.len == events.len + 1`,
  `$frames[^1].tableStateJson() == $live.tableStateJson()` and the same for `resultsJson()`.
- The viewer runs *the same module*: `replay-viewer/cogmud_replay.nim:13` imports `cogmud/sim`
  and line 41 does `for frame in replayMatch(config, events): states.add(frame.tableStateJson())`.
  `config.nims:9` puts `rootDir/src` on the path, so the wasm build compiles the identical
  `sim.nim`/`parse.nim`. `static_replay.js:101-119` hands that payload straight to
  `CogmudRenderer.attachReplay`, and `attachReplay:1671-1673` reads
  `states[Math.min(index, states.length - 1)]` — a single source, not a parallel recording.
- `replayMatch` pre-seeds the recorded reason before replaying (sim.nim:1300-1308,
  `sim.recordedReason = recordedReason`, consumed by `settle` at sim.nim:789), because a
  wall-clock `deadline` is not derivable from the rules. Both places a deadline can land are
  tested: `test_sim.nim:883-909` covers "at a turn open" and "immediately after the sixth act".

**Checklist 3 — static viewer, no pod path.**
- `coworld_manifest_template.json:17-19` → `"replay_viewer": {"bundle": "static-replay-viewer"}`
  (same location as the starter's, `starters/cogame-bullwhip/…:game.replay_viewer`).
- `tools/build_replay_viewer.sh` present, committed `100755` (`git ls-files -s` →
  `100755 35b530f…`). It is bullwhip's hook with three renames plus the `mkdir -p
  "$(dirname "${output_dir}")"` added at line 21 (the ecos fix), and two extra sprites at line 57.
  `ci.yml:225-236` asserts both `-f` and `-x` before invoking it by path (line 249).
- `coworld-release.yml:199-201` carries the "a pod-served `/client/replay` viewer is not
  acceptable" guard. No `replay_viewer` path/pod declaration exists anywhere in the manifest —
  the only `/client/replay` strings in the tree are the live-server route (server.nim:468), its
  page, and prose.
- Network reach of the bundle: `static_replay.js:76` `fetch(url)` for the `?replay=` URL and
  nothing else; `renderer.js:48-50` `assetUrl` resolves against `assetBase` (`"./assets"`,
  static_replay.js:117), all bundle-local. No websocket is opened on the `attachReplay` path.

**Checklist 4 — both name spaces.**
- Agents see aliases only: `sim.names` comes from `tableNames` (sim.nim:54-65, bullwhip's
  function and `CogNames` list kept verbatim at sim.nim:47-50). Every seat-facing string uses it —
  `playerStateJson` (sim.nim:1243, 1196, 1218, 1228, 1254), `userPrompt`/`systemPrompt`
  (llm.nim:360, 417, 460, 490-509), the welcome frame (server.nim:391), and the `final` frame,
  which explicitly substitutes aliases for the results' policy names (server.nim:169-180).
- Spectator side: `resultsJson` uses `sim.config.players[seat].name` (sim.nim:999);
  `snapshotJson` adds `policyNames` (server.nim:87); `replayPayload` carries both `names`
  (aliases, server.nim:124-127) and `policyNames` (line 133). `makeNameMap` (renderer.js:842-866)
  is **byte-identical to bullwhip's** (diffed), including `isBaselineFiller` so `Baseline`-labelled
  fillers keep their alias, and `nameMap.text()` is applied inside the chronicle's verbatim
  sentences at renderer.js:1057, 1075, 1081 — the design's requirement (line 414-418).
- `tests/test_score.nim:133-140` asserts `results["names"][seat] == "P<n+1>"` (policy) while
  `sim.names[seat] != results["names"][seat]` (alias).

**Checklist 5 / the batch rule — every wait bounded, and 704 s < 720 s.**
- Player connect: `while epochTime() < connectDeadline` with `sleep(200)`
  (server.nim:215-221), `connectDeadline = gameStart + playerConnectTimeoutSeconds` (180 s,
  types.nim:207).
- LLM: `decideAll` runs `for attempt in 0 .. 1` (llm.nim:674) — exactly two batches — with
  `budget = client.timeoutSeconds` (24) then `max(8, timeoutSeconds div 2)` (12), passed to
  `client.curl.makeRequests(batch, budget)` (llm.nim:688-691). `turnBudgetSeconds` mirrors it
  (`config.llmTimeoutSeconds + max(8, config.llmTimeoutSeconds div 2)`, sim.nim:71) and
  `test_sim.nim:955` asserts it equals **36**.
- **ONE parallel batch per turn**: `decideAll` builds a single `RequestBatch`, posts every open
  seat into it (llm.nim:677-685) and fires one `makeRequests`. The server calls it once per turn
  with `seats = pendingSeats()` = all six (server.nim:269, 290). No per-seat loop of requests
  exists anywhere. `sim.nim:151-158` returns all six pending seats in seat order.
- Deadline: checked **before** the batch, under the lock, never mid-turn
  (server.nim:263-268 → `endEarly()` → `broadcastLocked()` → `break`).
  `playDeadline = gameStart + timeoutSeconds * PlayBudgetFraction` (server.nim:244) with
  `PlayBudgetFraction = 0.6` (sim.nim:35), and `timeoutSeconds` from `COWORLD_TIMEOUT_SECONDS`
  falling back to `config.episodeTimeoutSeconds = 1200` (server.nim:236-242, types.nim:205).
- Arithmetic: `sampleEpisode` (sim.nim:79-83) → `budget = 0.6·1200 − 180 − 20 = 520`;
  `520 / 36 = 14.44 → 14`; clamped into `[6, 40]`. `test_sim.nim:956-964` asserts
  `fitted.turns == 14`, that `14 × 36 + 180 + 20 = 704 < 720`, and idempotence
  (`sampleEpisode(fitted).turns == fitted.turns`). `cogmud.nim:41` calls it once, after the seed
  is settled; `configFromReplay` sets `sampled = true` so a replay is never re-fitted
  (server.nim:485, cogmud_replay.nim:34).
- `MinBatchSpacingMs = 12_000` (sim.nim:41): applied at server.nim:280-285 only when
  `not client.disabled and lastBatchAt > 0.0`, so `docker-smoke` and offline certification never
  sleep on it; `12 < 36` so it never lengthens the worst case.
  `tests/test_bot.nim:191-217` asserts a full 14-turn disabled episode finishes in `< 5000 ms`.
- Game loop: `while true` with two `break`s (done, deadline) and a strictly increasing
  `turnsPlayed`; `applyAction` raises once `sim.done` (sim.nim:954-955), and
  `test_sim.nim:923-924` asserts that.
- `finishEpisode` (server.nim:152-207): final frames to players → `sleep(500)` → artifacts →
  `sleep(500)` → `sleep(grace * 1000)` (20 s, types.nim:210) → `quit(0)`. Exactly the design's
  order (line 904-905, 615-618).
- The player binary's read loop (`cogmud_player.nim:59-86`) is wrapped in
  `try/except CatchableError` and ends `quit(0)` (line 91), which is the fix the design requires
  at line 619-622 and the starter lacks (diffed against `bullwhip_player.nim`, which has neither
  the wrapper nor the `quit(0)`). `receiveMessage()` itself has no explicit deadline argument —
  it is whisky's, inherited verbatim — but it returns `none` on timeout and raises on close, and
  `docker_smoke.sh:251-260` hard-fails any player still running 60 s after the game exits. The
  smoke log for run 32685902639 shows `all 6 player containers exited 0`.
- A seat that never connects is not waited on: decisions are server-side, and an unconnected slot
  simply keeps `prompts[slot] = ""` (server.nim:519).

**Checklist 6 — `num_agents` everywhere, four invariants, `SEAT-COUNT FAIL` absent.**
- Manifest: `variants[0].game_config.num_agents = 6` (`standard`),
  `variants[1].game_config.num_agents = 6` (`honest-town`),
  `certification.game_config.num_agents = 6`. `len(certification.players) == 6`,
  `len(certification.game_config.players) == 6`.
  `config_schema.properties.num_agents = {"type":"integer","minimum":6,"maximum":6}`.
- `tools/ci/docker_smoke.sh` enforces all four, each with the `SEAT-COUNT FAIL:` prefix:
  present (lines 110-118), positive integer (119-125), `len(certification.players)` (129-134),
  `len(certification.game_config.players)` (135-140); and `SMOKE_SEATS` as an independent second
  declaration (`seats_expected="${SMOKE_SEATS:-6}"`, line 54 → cross-checked at 146-151).
  Committed `100755`.
- `grep -c "SEAT-COUNT FAIL"` over the full `docker-smoke` job log of run 32685902639
  (2 005 lines) → **0**. The log shows `game=cogmud seats=6 config={… "num_agents": 6 …}` and
  `smoke OK: seats=6 results=309B replay=21645B reason=complete`.
- `ci.yml:7-10` documents `<SEATS>` = 6 as a cross-check, not a fallback.
- The sim enforces it too: `initSim` raises unless `config.players.len == Seats`
  (sim.nim:237-239) and `update` raises on `players.len != 6` (types.nim:256-257), asserted at
  `test_sim.nim:992-998`.

**Checklist 8 — LLM reply handling.**
- Tolerant parse: `extractJsonObject` (llm.nim:559-570) takes `text[find('{') .. rfind('}')]`,
  so fences and surrounding prose are stripped; `test_bot.nim:268-275` covers
  ` ```json …``` ` and `"Sure! {…} Hope that helps."`.
- Invalid = not an object / `action` missing / not a string / empty after strip
  (`parseDecision`, llm.nim:641-648); `test_bot.nim:249-257` covers all four.
- Exactly one retry: `for attempt in 0 .. 1` (llm.nim:674) with the design's verbatim hint text
  at 682-683.
- Then the scripted fallback: llm.nim:704-707. An **unreadable but well-formed** action is
  explicitly *not* retried — `parseDecision` accepts it (`test_bot.nim:259-266` asserts the
  decision is valid and that `parseSentence` then returns `iNone`).
- Transport failures that count as retryable: timeout/transport error (llm.nim:600-601), 401/403
  (602-610, which also latches `client.disabled = true` so the rest of the episode is scripted
  with no network), 429 with model rotation (611-614), non-2xx (615-617), refusal (619-620), and
  `max_tokens` before any JSON (624-626).
- No credentials ⇒ every seat scripted immediately: `newLlmClient` sets `disabled` (llm.nim:164-167),
  `decideAll` short-circuits at 669-671 and `break`s the attempt loop at 675.
  `test_bot.nim:191-217` asserts `client.disabled` and a full episode with no network.

**Checklist 9 — rune-safe truncation, and strict-UTF-8 replay.**
- Two truncators, both rune-based: `cutRunes` (sim.nim:171-176, `runeSubStr`) applied to
  `sentence`/`say`/`notes` in `applyActionSteps` (961-968), to every room-log line
  (`logRoom`, 186), and to spoken text (853, 860); and `cleanText` (llm.nim:628-635,
  `runeSubStr(0, limit - 1) & "…"`) applied to `action`/`say`/`notes` at parse time
  (llm.nim:646-651). Caps: `MaxSentenceLen* = 240`, `MaxSayLen* = 160`, `MaxNotesLen* = 600`,
  `MaxRoomLogLen* = 200` (sim.nim:42-46); the prompt cap is `MaxPromptLen* = 4000`
  (llm.nim:35), enforced with `runeSubStr` at server.nim:436-437.
- Captured errors are truncated too, but on **bytes**: llm.nim:566-567 (`head[0 ..< 160]`),
  603 (`response.body[0 .. min(high, 400)]`), 612, 617, 626. Those strings go only to
  `error.msg` → `echo` on stdout (llm.nim:700-701); they never reach the replay, so the
  checklist's "every string that reaches the replay" is unaffected. Worth knowing, not a finding.
- Test: `test_sim.nim:702-723` feeds `"é" × 900` as sentence, say and notes and asserts
  `runeLen == 240 / 160 / 600`, `validateUtf8() == -1` on all three, then encodes the whole event
  log to JSON and asserts the encoding validates and `parseJson`es.
  `test_bot.nim:238-243` does the same through `parseDecision`, and 277-281 asserts `cleanText`
  cuts on a rune boundary and marks the cut.
- End to end: `docker_smoke.sh:311-318` decodes the replay bytes with `.decode("utf-8")`
  (strict) before `json.loads`, default `SMOKE_REQUIRE_REPLAY_JSON=1` (line 57). Green in the
  cited run (`replay=21645B`).
- `speech = false` forces `say` to `""` (sim.nim:963-964); asserted at `test_sim.nim:725-732`.

**Checklist 10 — manifest shape.**
- `game.docs.readme` is `{"type":"text","value":…}`; `game.docs.pages` is a 3-element array, each
  `{"id","title","content":{"type":"text","value":…}}` — ids `rules.md`, `sentences.md`,
  `scoring.md`, exactly the three the design names (line 1244-1254).
- `game.protocols` carries **both** `player` and `global`, each `{"type":"text","value":…}`.
  The `player` value documents `cogmud.player.v1`, the frame shapes, the redaction, the reply
  caps, the 4 000-char prompt cap, the `scripted` values and "a policy is just a prompt".
  The `global` value documents the snapshot shape, the whole event vocabulary (including
  `prevRoom` in the `cogs` schema), the complete 26-value outcome list, the salience table and
  `index.html?replay=<url>`.
- Also present and matching the design: `$schema`, top-level `episode_timeout_minutes: 20`,
  `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/cogmud/anthropic_api_key"`,
  `run: ["/bin/cogmud"]`, `image: "{{COGMUD_IMAGE}}"` (derived from the compose service name
  `cogmud`, compose.yaml:2, image `coworld-cogmud:latest`), `source_url`, owner
  `daveey@gmail.com`, the 9 tags verbatim.
- `config_schema`: `additionalProperties: false`, `required: ["tokens","players"]` (tokens kept
  required), `tokens`/`players` `minItems`/`maxItems` 6, every other property present with the
  bounds and defaults the design lists (turns 6..40 default 14; episodeTimeoutSeconds 60..6000
  default 1200; turnDelayMs 0..10000 default 400; maxOutputTokens 64..2000 default 900;
  llmTimeoutSeconds 5..300 default 24; shutdownGraceSeconds 0..120 default 20;
  player_connect_timeout_seconds number default 180; model documented as direct-Anthropic-only).
- `results_schema`: all 11 required fields, every array `minItems`/`maxItems` 6, `reason`
  documented as `complete` or `deadline`. `resultsJson` (sim.nim:987-1019) emits exactly those.
- Three player runnables (`cogmud-player`, `cogmud-factor` with `PLAYER_SCRIPTED=factor`,
  `cogmud-magpie` with `PLAYER_SCRIPTED=magpie`), all one image + `/bin/cogmud-player`,
  `100m`/`64Mi` requests, `1` cpu limit. The certification fixture seats all three
  (`[player, factor, player, magpie, factor, player]`), so no runnable is orphaned.
- The manifest is in sync with its generator: running `scripts/manifest/build.py` produced a
  byte-identical file (`git status --porcelain` empty afterwards).

**Checklist 11 — legible at 360 px.**
- `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` at `client/chrome.css:280-292` — the
  starter's own rule, inside the byte-identical prefix.
- `@media (max-width: 640px) { .plate-label { display: none; } … }` at chrome.css:460-464 —
  again the starter's. The appended block adds earlier sheds that never touch the name:
  `.plate-pack` at 1180 px, `.plate-label` at 900 px, `.plate-label` + `.plate-room` at 560 px,
  and `#scorebug { grid-template-columns: repeat(2, 1fr); }` + `.treel button:nth-child(n+5)
  { display: none; }` at 480 px (chrome.css:611-630) — which is the design's "the highlight reel
  keeps four buttons at that width".
- `.plate-room` explicitly shrinks four times faster than the name (`flex: 0 4 auto`,
  chrome.css:496).
- `tests/test_viewer.nim:93-104` asserts `min-width: 3.2em`, `flex: 1 1 auto`, both media
  queries and both grid rules.
- The canvas re-fits from `relayout()` (replay.html:102) and `computeLayout` sets
  `compact: width < 560` (renderer.js:170).

**Checklist 12 — release order and scaffold.**
- Three workflows present: `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`.
- `coworld-release.yml` step order: `Build the Coworld manifest` (153) → `Certify locally` (167)
  → `Upload the policies` (206) → `Upload the Coworld` (304) → `Put the Coworld secret` (342).
  Exactly build → certify → upload-policies → upload-coworld → secret put.
  `ci.yml`'s only smoke builds its image in the same job (`Build image`, line 177, then
  `Raw-Docker episode smoke`, 185).
- `tools/ci/docker_smoke.sh` present and `100755`; `tools/build_replay_viewer.sh` `100755`;
  `tools/ci/viewer_smoke.mjs` `100755`.
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` → no output).
- `tools/ci/policies.json`: four policies — two `PLAYER_PROMPT` champions (`cogmud-merchant`,
  `cogmud-broker`) plus two scripted fillers (`cogmud-factor` → `PLAYER_SCRIPTED=factor`,
  `cogmud-magpie` → `PLAYER_SCRIPTED=magpie`). Champion **#2** (`cogmud-broker`, the second
  `PLAYER_PROMPT` entry) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`.
- The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files
  returns nothing. The surviving angle-bracket names are exactly the four documented as expected
  residue: `<cow_id>`/`<sha>` (ci.yml:202), `<run_id>` (coworld-release.yml:21,
  coworld-submit.yml:17), `<name>:vN` (coworld-submit.yml:31).

**Checklist 13 — the viewer executes.**
- `ci.yml`'s `wasm-viewer` job declares `needs: docker-smoke` (line 212) and its step
  `Load the bundle in a real browser` (293-316) runs
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "${replay}"
  --timeout 90 --soak 15` against the `smoke-replay` artifact. No `continue-on-error` anywhere in
  the file. In run **32685902639** that step reports `success`, with output:
  `{"loaded":true,"ms":290,"clock":"TURN 4 / 8 · WAITING ON 6","scorebug":"Sprocket THE SMITHY
  0.50 40C … Piston THE SMITHY -0.05 4C 4 items","feed_lines":117}`,
  `soak: 15s of playback kept advancing`, and
  `scrub readouts: 0%="TURN 4 / 8 · WAITING ON 6"  50%="TURN 5 / 8 · WAITING ON 6"
  100%="FINAL · RATCHET 1.73"` — three distinct readouts, `data-replay-error` never set.
  (I read `viewer_smoke.mjs:400-424`: `moved` is computed over `clock|tick|scorebug`, so the
  `null -> null -> null` in the message is only the absent `#tick` field; the gate really fired
  on `clock`/`scorebug`.)
- Both markers, from the shell's own code paths: `data-replay-loaded="true"` is set at
  `client/renderer.js:1722`, at the end of `attachReplay`'s `makeRenderer` callback and *after*
  the frame IIFE's first synchronous `renderer.draw(view)` — the same position as bullwhip's
  (`starters/cogame-bullwhip/client/renderer.js:1390`). `data-replay-error` is set at
  `static_replay.js:56` and removed on a successful retry at 107 and 149.
  `static_replay.js:126-139` additionally gates the `coworld-replay` `ready` envelope on the
  loaded attribute, bounded at 240 frames then `fail("renderer never drew a frame")` — the
  eleusis fix the design names (line 1010-1015).
- **MODULARIZE / bootstrap are a matched pair, both from bullwhip.** `replay-viewer/config.nims`
  differs from the starter's in exactly 3 lines (output name, `EXPORT_NAME=CogmudReplayModule`,
  the `_cm_*` export list) and keeps `-s MODULARIZE=1` (line 38), `-O2`,
  `ALLOW_MEMORY_GROWTH`, `ABORTING_MALLOC=1`, `ENVIRONMENT=web`,
  `EXPORTED_RUNTIME_METHODS=HEAPU8`. `static_replay.js:153` calls the factory:
  `modulePromise = CogmudReplayModule().catch(…)`. There is **no** `onRuntimeInitialized`
  anywhere in the file (grepped; `test_viewer.nim:175` asserts its absence).
  Every exported symbol lines up three ways — `_cm_load_replay`/`_cm_payload_ptr`/`_cm_payload_len`/
  `_cm_error_ptr`/`_cm_error_len` in `config.nims:41`, `module._cm_*` in `static_replay.js:94-103`,
  `{.exportc: "cm_*".}` in `cogmud_replay.nim:25,58,64,67,73` — and `test_viewer.nim:177-189`
  asserts all three for all five. `emscripten_exit_with_live_runtime()` at cogmud_replay.nim:80-85.
- The fetch is bounded: `FETCH_TIMEOUT_MS = 20000` with an `AbortController`
  (static_replay.js:14, 71-88).

**Checklist 14 — chrome provenance.**
- `client/chrome.css` is **byte-identical to the starter's for its first 11 964 bytes**
  (`cmp -n 11964 starters/cogame-bullwhip/client/chrome.css cogame-cogmud/client/chrome.css` →
  clean), i.e. all 467 starter lines, with a single `/* ---------- Cogmud ---------- */` block
  appended at 468-630. No existing rule is edited or deleted (`diff` reports only `467a468,630`).
  `tests/fixtures/starter_chrome.css` is itself byte-identical to the starter's file (`cmp`
  clean), so `test_viewer.nim:75-83` diffs against the real thing without a starter checkout.
- The appended block contains exactly what the design lists (line 1038-1056):
  `:root { --band: 84px; --hudscale: 1; }` (477), `#scorebug { grid-template-columns:
  repeat(6, 1fr); }` (481), `.seat5 { --tc: var(--orange); }` + `--orange` (482-483),
  `.plate-room`/`.plate-pack`/`.plate-robbed`/`.plate-hired` (486-524),
  `#townbar` with `font-size: calc(11px * var(--hudscale))` (527-539),
  `.treel` + `.treel button` (543-572), `#loading { bottom: var(--band); }` (574),
  the feed colours (599-605) and the small-screen queries (611-630).
- `client/replay.html` is the starter's page **plus** an appended block under the banner
  `COGMUD additions to the inherited cogame-bullwhip chrome`. The `diff` against
  `starters/cogame-bullwhip/client/replay.html` shows only: `<title>`, the wordmark
  `BULL<span>WHIP</span>` → `COG<span>MUD</span>`, `#clock` text `WEEK 0` → `TURN 1`, two
  namespace renames `BullwhipRenderer` → `CogmudRenderer`, **two added elements**
  (`<div id="townbar">` at line 20 between `#scorebug` and `#board-wrap`, and
  `<div class="treel" id="reel">` at line 33 as a third row *inside* `#transport`), and the
  appended banner + `relayout()` script. **Nothing is removed** — every starter id survives
  (`#layout, #stage, #topband, #wordmark, #clock, #topright, #statuschip, #feedtoggle,
  #scorebug, #board-wrap, canvas#table, #lightpool, #grain, #endscreen, #transport, .scrub#scrub,
  .tbar, .tbtn#play, .tpos#pos, #feed, #loading`), as does the `fit()` + `bindFeedToggle`
  bootstrap. 109 lines vs the starter's 74 — an addition, not a rewrite.
  `replay-viewer/index.html` gets the identical treatment (88 lines vs the starter's 53; `./`
  asset paths and the `cogmud_replay.js` / `static_replay.js` script tags).
  `test_viewer.nim:110-133` asserts every id, both appended elements, `reel` inside `#transport`,
  `#townbar` between `#scorebug` and `#board-wrap`, and `"viewpanel" notin text`.
- (a) `relayout()` sets `--band` and `--hudscale` on **`document.documentElement`**
  (replay.html:95-103, index.html:74-82) — `root.style.setProperty("--band", band + "px")` from
  `#transport`'s `offsetHeight`, which therefore includes the reel row; `--hudscale =
  clamp(0.8, innerWidth/960, 1.15)`; and it calls `fit()` (a top-level `function fit()` in the
  starter's own script, so a global — the `typeof fit === "function"` guard resolves). Bound to
  `load` and `resize` (104-105); `bindFeedToggle` dispatches a `resize` event on both the initial
  collapse and every toggle (renderer.js:1387-1389, 1398), so the feed toggle re-runs it.
  `test_viewer.nim:135-146` asserts all of this on both pages.
- (b) Nothing fixed-positioned sits in the band. `#transport` is the last child of `#stage` in
  normal flex flow; the three absolutely-positioned overlays `#lightpool`/`#grain`/`#endscreen`
  are all inside `#board-wrap` (replay.html:21-26), which is `position: relative; flex: 1`
  (chrome.css:95) and ends where the band begins; `#loading` is `position: absolute; inset: 0`
  (chrome.css:249-250) overridden to `bottom: var(--band)` by the later, equal-specificity
  appended rule (chrome.css:574). `#townbar` is static (no `position` in its rule).
- (c) `#endscreen` is `position: absolute; inset: 0` inside `#board-wrap` (chrome.css:374-376),
  so its bottom edge *is* `var(--band)` above the page bottom — the design's stated mechanism
  (line 1087-1089). It is shown with the class its CSS rule uses: `#endscreen.show { display:
  flex; }` (chrome.css:383) and `container.classList.toggle("show", !!show)`
  (renderer.js:1326) — and crucially the toggle runs *before* the `dataset.built` early-return
  (1327), so it fires on every call. `setIndex` calls
  `updateEndscreen(options.endscreen, payload.results, index >= events.length &&
  events.length > 0, nameMap)` on **every** index change (renderer.js:1697-1699), and every seek
  path routes through `setIndex`: the scrubber's pointer drag/click (`onSeek` at 1652-1655 →
  `seekFromEvent` 1608-1614 / pointerdown-move-up 1616-1629), each beat button's `onclick`
  (`markCogmudBeat`, 1509-1512), each reel button's `onclick` (1547), and the play toggle's
  restart (1662). **There are no back/forward buttons and no keyboard handler in this lineage** —
  the starter's transport is `.tbtn#play` + `.tpos#pos` only, and grepping both pages and
  `renderer.js` for `keydown`/`keyup` returns nothing — so "every seek" is fully covered by the
  seeks that exist. `test_viewer.nim:230-235` asserts the toggle line and that `updateEndscreen(`
  appears inside `setIndex` before `setIndex(0, true)`.
- (d) Beats are labelled, clickable `<button>`s: `markCogmudBeat` (renderer.js:1494-1513) creates
  `document.createElement("button")`, `type="button"`, `className = "beat-marker " + kind + " seat<n>"`,
  `title` and `aria-label` set to `beatLabel(...)`, and an `onclick` that
  `stopPropagation()`s then `onSeek(index + 1)`; the container keeps its drag-to-seek pointer
  handlers, which explicitly skip clicks landing on a `.beat-marker` (1617-1620). Beats are
  emitted for every `act` with `salience >= 40` and for the `end` event (1592-1600). The five
  kinds `beatKind` can return — `rob`, `commission`, `deal`, `market`, `end`
  (renderer.js:914-926) — **each have a CSS rule**: `.beat-marker.rob/.commission/.deal/.market/.end`
  at chrome.css:585-596 and `.treel button.rob/.commission/.deal/.market/.end` at 568-572.
  `test_viewer.nim:85-91` asserts both families for all five.
  Turn spans and the every-fourth separator are the starter's `buildScrub` logic, kept
  (renderer.js:1568-1587).
- The naming guard: the builders are `markCogmudBeat` / `buildCogmudReel`, never
  `markBeat`/`buildScrub` (renderer.js:1498, 1523); `test_viewer.nim:148-164` walks all four
  pages, extracts top-level `function`/`var` names above and below the banner, and asserts the
  intersection is empty plus `"markBeat" notin game`.
- Zoom/minimap: `grep -rn "viewpanel\|zoomAt\|setZoom\|attachMinimap"` over `.js/.html/.css/.nim`
  returns **nothing** outside `test_viewer.nim`'s absence assertion. The starter ships none and
  none was added, which is what the design says (line 1069-1072) and what a fixed nine-room
  arena on a 0..100 grid warrants (`computeLayout` rescales every card to the canvas,
  renderer.js:146-172).

**Resolution rules, traced.**
- Turn open (`openTurn`, sim.nim:203-234), in the design's order: offers older than `turn - 1`
  expire (206-211 — "posted on t, acceptable only on t+1"); every `retainerTurns > 0` decrements
  and clears `retainerOf` at 0 (213-217); `acts[]` reset (218); NPC restock (220-227, see F10);
  `roomLog` → `heardLog` (229-231); `phase = phTurn`; one `turn` event carrying all 9
  `RoomState`s, 5 `NpcState`s and 6 `CogState`s (`logTurn`, 192-201).
- Initiative: `initiativeOrder(turn)[k] = (k + turn) mod Seats` (sim.nim:144-149), asserted
  element-by-element and as a permutation with equal leads at `test_sim.nim:180-191`.
  `resolveTurn` iterates `for position, seat in order` in every class, and `position` (the
  initiative rank) is what lands in `event.order` (sim.nim:841, 805).
- Class order, exactly the design's six plus the no-op sweep, each appending its `act` event as
  it resolves so the log order *is* the resolution order: speech (846-860), shop
  (864-878, `iBuy`/`iSell`/`iQuest`/`iGive`-with-`npc`), ground (881-889), cog-to-cog (892-902),
  robbery (906-910), movement (913-917), no-ops (921-930). `emitted[]` guarantees one event per
  seat per turn.
- Contention: stock, ground items and offers are all consumed in place by the earlier initiative
  — asserted at `test_sim.nim:363-392` (last unit of stock → `oOutOfStock` for the loser;
  contested ground item → `oNoSuchItem`) and 394-422 (second accept → `oNoSuchOffer`).
- Price curve: `askAt(item, stock) = clamp(base + 1·(6 − stock), max(2, base div 2), base·3)`
  (sim.nim:98-104); `bidAt = max(1, ask·2 div 3)` (106-108). I checked the design's numbers by
  hand: `askAt(hide,8)=4`, `askAt(hide,7)=5` → 9 for two; `askAt(rope,6)=8`, `askAt(rope,5)=9`
  → 17; `bidAt(relic,3)=max(1, 17·2 div 3)=11`. All three are asserted at
  `test_score.nim:89-91` and `test_sim.nim:205-223`. Each unit of a multi-unit purchase is priced
  from the stock at the moment it changes hands (`resolveBuy`'s `while got < want` loop re-reads
  `sim.ask(npc, item)` after each `dec stock`, sim.nim:424-432); selling walks the *falling* bid
  the same way (459-469). Partial fills never overdraw (`if coin < price: break`, 426-427;
  `if npc.coin < price: break`, 461) — `test_sim.nim:239-250` and 252-267.
- Commission partial credit: `credit` (sim.nim:359-367) banks `PointsPerUnit(4) × units` and adds
  `CompletionBonus(8)` exactly on the delivery that crosses `count`, guarded by
  `delivered - units < count` so a third unit banks nothing. `resolveGiveNpc` (478-524) moves the
  goods irrevocably first, credits across both quests up to their outstanding amounts (505-512),
  and reports `oNoMatchingCommission` when `credited == 0`. `result.coin` carries the *points*
  banked, which is what `salienceOf` (289-292), the FX (renderer.js:1160-1166) and the feed
  (renderer.js:947-950) read. `test_sim.nim:309-359` covers 1-of-2 → 4, the second → 4+8, a
  third → `oNoMatchingCommission` with the goods gone, a non-commission item to Vell, and a
  commission item to another shop.
- Robbery: `A = 1 + retainersPresent(robber, room) + (dark ? 1 : 0)`,
  `D = 1 + retainersPresent(victim, room) + (dark ? 0 : 2)`, success iff `A > D`
  (sim.nim:723-726, expressed as `if attack <= defence: fail`). All four design cases check out
  by hand (lit/none 1v3 fail; dark/none 2v1 win; dark/victim-guarded 2v2 fail; dark/both 3v2 win)
  and are asserted at `test_sim.nim:477-529`. Loot is the highest-`baseValue` item, ties by lowest
  id (`bestLoot`, 375-381 — ascending scan with a strict `>`), else `min(victimCoin, RobCoin=10)`,
  else `oNothingToTake`; failure costs `min(robberCoin, FineCoin=8)` paid to the victim (727-734).
  Ordering guards: `self_target` before `no_such_cog` before `not_in_room` before
  `thievery_forbidden` before `bound_by_contract` (704-718). Robbery reads start-of-turn rooms
  because movement is class 6 — asserted explicitly at `test_sim.nim:578-591` (the victim is
  robbed *and* the move still happens).
  One implementation detail beyond the note: on success with a **full robber pack**
  (`free <= 0`, sim.nim:737-738) coin is taken instead of the item; the design only contemplates
  an empty victim. Commented in place (748-749).
- Hire/trade: offers are posted without escrow and execute at acceptance (`resolveAccept`,
  618-668), which re-checks the offerer's goods, the acceptor's coin and carry space and reports
  `oOfferExpired` otherwise (641-645) — `test_sim.nim:443-460`. Same-room is checked against
  start-of-turn positions (634). Acceptance is `postedTurn == sim.turn - 1` only (622).
- Scoring: `wealth = coin + Σ baseValue·held` (sim.nim:125-128); `questPoints = Σ (4·delivered +
  8 if complete)` (130-134); `score = (wealth + 3·questPoints − 40) / 40.0` (136-138). Derived
  from state, never accumulated. Doing nothing = exactly `0.0` (`test_sim.nim:940-946`,
  `test_score.nim:53-58`); a stolen relic swings both seats by exactly `14/40`
  (`test_score.nim:68-82`); a pure trader at +40 coin = `1.00` (103-106).
  `resultsJson` reports all 11 fields including `robberies` and `robbed` (987-1019).
- Endings: exactly two. `"complete"` at `resolveTurn:938-945` — closing `turn` event **then**
  `settle`, so `events[^1].kind == evEnd` and `events[^2].kind == evTurn`
  (`test_sim.nim:919-920`); `"deadline"` via `endEarly` (976-983), idempotent
  (`if sim.done: return`, asserted at `test_sim.nim:926-933`).
- Event/state schema vs what the viewer reads: I checked every `act` field the renderer touches
  against `eventToJson` (sim.nim:1388-1427) — `seat`, `order`, `intent`, `room`, `reason`,
  `salience`, `scripted` are always written; `toRoom`/`item`/`npc`/`other` only when `>= 0`,
  `qty`/`coin` only when `!= 0`, `sentence`/`say`/`text` only when non-empty.
  `eventFromJson` (1429-1481) restores the same defaults (`-1`, `0`, `""`). The renderer's
  readers all tolerate the omissions (`event.qty || 0` at 928, `event.item < 0 ||
  event.item === undefined` at 966). `test_sim.nim:841-868` round-trips one event of **every**
  kind field by field and asserts `seen == {evStart, evTurn, evAct, evEnd}`.
- `tableStateJson` (sim.nim:1037-1141) emits every key the design's sample shows, and
  `test_sim.nim:837-839` asserts `tableStateJson()["world"] == worldJson()`.

**The replay writer.**
- `replayPayload` (server.nim:117-144) writes `protocol: "cogmud.replay.v1"`, `names` (the table
  aliases), `policyNames`, `config` = `{turns, seed, speech, thievery, sampled: true, world:
  worldJson()}`, `events` (every event via `eventToJson`) and `results`. The bytes are
  self-sufficient: the seed re-derives starting rooms, commissions, ground items and aliases
  (`initSim`, sim.nim:250-269, one rng stream in the fixed order the design names, plus
  `tableNames`'s own stream at sim.nim:58), and `config.world` carries the complete room/item/NPC
  tables so the parchment map is drawable from the bytes alone. Nothing else is fetched
  (static_replay.js fetches only the `?replay=` URL).
- `writeArtifact` honours the `COGAME_*_METHOD` hints (server.nim:102-115); the replay goes out
  as `application/octet-stream` (194) and results as `application/json` (190).
- `docker_smoke.sh:336-341` copies the produced replay to `dist/smoke/replay.json` and `ci.yml`
  uploads it as `smoke-replay` for the viewer job.

**The world tables** (`world.nim:42-110`) match the design's three tables exactly — I checked all
nine rooms (id/name/keywords/x/y/dark/exits), all six items (keywords + `baseValue` 6/7/8/9/11/14)
and all five NPCs (keywords/room/trade list/initial stock). Only difference: the design's NPC
table repeats `dockmaster` twice in Dockmaster Fen's keywords (line 117), evidently a typo; the
code has `@["dockmaster", "fen"]`. `Adjacency` and `Dist` are built from the tables at module init
(119-143), so an exit change cannot leave them stale, and `test_sim.nim:58-100` re-derives BFS
independently and compares.

**Packaging.** `compose.yaml` service `cogmud`, `image: coworld-cogmud:latest`,
`platform: linux/amd64`, `build: {context: ., network: host}`. `Dockerfile` = bullwhip's renamed
(nimby 0.1.26 / Nim 2.2.4, matching `ci.yml`'s `NIMBY_VERSION`/`NIM_VERSION`);
`Dockerfile.replay-viewer` on `emscripten/emsdk:4.0.15` + nimby 0.1.27 + Nim 2.2.4, exactly as the
design says. `nimby.lock` is **byte-identical to the starter's**. `cogmud.nimble` v0.1.0,
`srcDir = "src"`, the five required deps. `data/` = bullwhip's four sprites + `arena_floor.png` +
`font.ttf` + `FONT_LICENSE.txt`, plus the two committed recolours
`soldier_violet_front.png` / `soldier_orange_front.png`; `renderer.js:24-32` already runs
`COLORS = ["red","blue","green","yellow","violet","orange"]` with `COLOR_HEX` for both, and
`makeRenderer:73-75` maps all six into the asset list. `test_viewer.nim:204-218` asserts the build
hook ships all eight assets and that each exists on disk.

**The seven documented deltas the brief names — each verified where the builder claims it.**

| delta | claimed location | verified |
|---|---|---|
| `off` / `have`+`has` / verbless purchase | `parse.nim` header | `parse.nim:10-19` lists all three with reasons; implemented at `parse.nim:101` (`off`, `vgRoomSlot`), `147-148` (`have`/`has`, `vgTargetSlot`), `442-450` (verbless, NPC+item ⇒ `iBuy`). Also in the shipped `sentences.md:29,34,43-45` and tested at `test_parse.nim:78,125,221-224`. **Consistent.** |
| number words past twelve | `parse.nim` comment | `parse.nim:36-42` with the reason ("the note's own phrasebook says … FIFTEEN coins"), which is true — design.md:526 and `llm.nim:46`. Documented publicly at `sentences.md:59-62`. Tested at `test_parse.nim:149-150` (fifteen → coin 15). **Consistent.** |
| retainer literal-note timing | tests | `test_sim.nim:609-611` explains it in a comment and 620-629 uses `applyActionSteps` to inspect the frame *at acceptance* (`retainerTurns == 3`), then 636-642 walks the decrements to 0 and the clear. Matches `sim.nim:662-663` + `213-217`. **Consistent.** |
| magpie dark-preference ramble | `llm.nim` | `llm.nim:323-329` states the rule and the reason ("the lowest-id rule alone never leads to the Docks or Cutpurse Alley, both high-id, so the baseline that is supposed to exercise the robbery path would never rob") — which is true of the world table (`Rooms[5]`, `Rooms[6]`). Implemented at 330-343. Publicly documented in the manifest's `cogmud-magpie` description ("walks toward the dark when its hands are empty"). Its consequence is tested: `test_bot.nim:144-155` (`iRob >= 1`) and 166-175 (the cert fixture's offline mix contains a theft). **Consistent.** |
| `prevRoom` field | `types.nim` | `types.nim:41-43` with its reason. Set at `sim.nim:259` (init `-1`) and `770` (on move); carried in `cogStateJson` (1381) and read back (1467); included in the `sameWorld` tamper check (1286). Declared in the manifest's global protocol (`"cogs":[6 x {room,prevRoom,coin,…}]`). **Consistent.** |
| `Sim` in `types.nim`, re-exported from `sim.nim` | `types.nim` | `types.nim:173-177` gives the reason (the pure parser needs `Sim` without an import cycle). `sim.nim:15-17` does `import … types, parse` + `export types, parse`, so `sim.Sim` is the name every consumer uses; `parse.nim:21-23` imports only `types`. Every test and both entrypoints import `cogmud/sim` alone. **Consistent.** |
| feasibility oracle tighter than the note's route | tests | `test_feasibility.nim:85-92` explains it in full ("visiting The Smithy first (5-4-3, 2 moves) is two turns shorter, so the oracle finds MORE slack than the note claims") and then asserts the note's numbers **as an upper bound** (`plan.turns <= 11`, `plan.cost <= 24`, lines 100-101), plus the note's own graph distances at 105-113. **Consistent.** |

None of the seven silently contradicts the note elsewhere. The one delta that is *not* on the
brief's list and *not* in `parse.nim`'s header is `wander` — see F15; it is documented in the
shipped `sentences.md` and tested, so it is not undocumented, only unlisted.

---

## Could not determine

- **Whether the `factor`/`magpie` thresholds were in fact swept rather than chosen** (F1). The
  tree carries no harness and the design note never claims one, so I can report only the absence.
  What would settle it: a committed sweep script plus its output, or a cited `log.md` entry
  recording the search.
- **Whether whisky's `receiveMessage()` carries a read deadline.** `cogmud_player.nim:54-58`
  asserts it does ("only a timeout returns none"), and the loop is wrapped and exits 0, and
  `docker_smoke.sh:251-260` bounds the player's lifetime to 60 s past the game's exit — but the
  whisky source is not in this sandbox, so I could not read the deadline itself. What would
  settle it: reading `~/.nimby/pkgs/whisky/src/whisky.nim`, or a hosted run where the game is
  killed without closing sockets.
- **Whether `viewer_smoke.mjs`'s `--soak 15` window is long enough for this fixture in the
  worst case.** The design's arithmetic (line 645-648) says 59 events × 450–1500 ms ≈ 40 s, and
  `test_sim.nim:980-988` and `test_bot.nim:175` both assert the fixture is exactly 59 events, and
  the CI run passed the soak. I did not measure real playback wall-clock; the dwell logic
  (`renderer.js:1704-1710`: 1500 ms per `turn`, 900 ms per act with speech, 450 ms otherwise,
  1500 ms for `end`) gives `1 + 8×1500 + 48×450 + 1×1500 + 1×1500 ≈ 37 s` for an all-scripted
  fixture where no act carries `say`, which is consistent. What would settle it: the
  `viewer-smoke.json` artifact's per-sample indices.
