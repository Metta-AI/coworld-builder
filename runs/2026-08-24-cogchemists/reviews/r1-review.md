# r1 review — cogchemists

Repo: `/workspace/build/cogchemists` at `5a82157c24e02859b1645ec2cde3ac8a7b7c823a` (tree clean, no drift).
Starter for provenance diffs: `/workspace/starters/cogame-bullwhip` @ `a87cf75`.
Design note: `/workspace/coworld-builder/runs/2026-08-24-cogchemists/design.md`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the simultaneous-decision rule).
Files read: 34 of the 45 tracked files, in full or in the regions cited (all `src/`, all `tests/`, all of
`client/replay.html`, `client/chrome.css` diff, `client/renderer.js` regions 1–740 / 826–1345 / 1480–1721,
all `replay-viewer/*`, the manifest, all three workflows, all three `tools/` scripts).
Nim toolchain is not installed in this sandbox, so no test was executed locally; CI evidence is cited
from `gh` (run **32702248279**, `main`, conclusion **success**, all three jobs green).

The coordinator asked for a neutral trace. Severity below is stated only by reference to a named
checklist item; where no checklist item covers an observation it is recorded as non-blocking regardless
of how large the gap between note and code is.

---

## Blocking

### B1 — An LLM decision that falls back to the scripted move is recorded `scripted: false`
- Where: `src/cogchemists/llm.nim:734-744`, `:745-752`, `:785-788`; `src/cogchemists/server.nim:305`,
  `:316`, `:318`; `src/cogchemists/sim.nim:524`; `src/cogchemists/sim.nim:1087`.
- Observed, step by step:
  - `decideAll` is declared `): seq[Action]` (`llm.nim:734-740`) — the only thing it returns is one
    `Action` per seat. There is no per-seat flag, out-parameter, or side channel.
  - Seats that are configured scripted, or every seat when `client.disabled`, are filled in before any
    request goes out (`llm.nim:745-752`).
  - After two attempts (`for attempt in 0 .. 1`, `llm.nim:753`), any seat still in `open` is filled with
    `result[index] = scriptedAction(sim, seat, skAssayer)` and logged
    `"seat N falling back to scripted decision"` (`llm.nim:785-788`). The returned `Action` is
    indistinguishable from a parsed one.
  - The server computes the recorded flag independently of that:
    `let wasScripted = scripted[seat] != skNone or client.disabled` (`server.nim:316`), then
    `state.sim.applyAct(seat, decision, wasScripted)` (`server.nim:318`).
  - `applyAct` copies that argument straight into the event (`sim.nim:524`, `event.scripted = scripted`)
    and `eventToJson` writes it as `"scripted"` (`sim.nim:1087`).
  - Therefore: in an episode **with** working credentials, a seat whose reply fails twice (transport
    error, parse failure, or a move the probe `applyAct` rejects) is recorded `scripted: false`, exactly
    like a successful LLM decision. The flag is correct only in the two cases where the fallback was
    decided before the batch: an explicitly scripted seat, and `client.disabled` (the offline smoke and
    offline certification — which is why `docker-smoke` cannot surface this).
- Note says: §Degrade, never hang — "A seat's decision that times out or fails to parse gets exactly one
  retry …, then **falls back to the scripted `assayer` move** for that seat, **recorded with
  `scripted: true`** so phase-60 check 4 can tell a real decision from a fallback."
- Checklist item: 8 — "LLM reply handling. Parsing is tolerant …, retries **once** …, then falls back to
  the scripted move — **and the fallback is recorded so phase 60 can count it**."
- Consequence: in a hosted league replay, the number of scripted fallbacks is not recoverable from the
  bytes; phase 60's check 4 would read 0 fallbacks on an episode where every seat fell back. (The retry
  itself, the tolerant parse, and the probe are all present and correct — this is the recording half of
  the item only.) *Observed, not run.*

---

## Non-blocking

### N1 — Error text quoted into the log is sliced on bytes, not runes
- Where: `src/cogchemists/llm.nim:657-660` (`head[0 ..< 160]`), `:697` (`response.body[0 .. min(high,400)]`),
  `:706` (`…300`), `:711` (`…300`), `:719-721` (`result[0 .. min(result.high, 160)]`).
- Observed: each is a byte slice of a server-supplied body or a model reply; the resulting string is put
  into a `CogchemistsError` message which is echoed at `llm.nim:781-782` and (for the transport case) at
  `server.nim:324`. A multi-byte character straddling the cut leaves an invalid UTF-8 byte in stdout.
- Note says: §Reply schema — "The same rune rule applies to the 4000-char player prompt and **to any error
  text quoted into the log**." (The 4000-rune prompt cap *is* rune-safe: `server.nim:466-467` and
  `src/cogchemists_player.nim:46-47` both use `runeLen`/`runeSubStr`.)
- Not blocking: checklist 9 scopes rune-safety to "every string that reaches **the replay**". I traced
  the paths: no LLM error text reaches an event. `applyRejection` records only `checkAct`'s ASCII reason
  token (`sim.nim:677`, tokens enumerated at `sim.nim:344-420`), and no event field is fed from
  `error.msg` anywhere else.

### N2 — `docker_smoke.sh` prints the end reason but does not assert it
- Where: `tools/ci/docker_smoke.sh:309-311` — `reason = results.get("reason") …; if reason is not None:
  print(f"episode end reason: {reason}")`. No comparison, no `SystemExit`.
- Note says: test 25 — the smoke asserts "`results.names` / `results.scores` have 4 entries **and
  `results.reason == "complete"`**". The seat-count and array-length assertions *are* there
  (`:302-305`); the reason assertion is not.
- Provenance: `diff` against `/workspace/coworld-builder/templates/tools/ci/docker_smoke.sh` shows the
  file is the template verbatim plus the `<slug>/<IMAGE>/<SEATS>` substitutions plus one added block
  (the player-container exit check, `:243-273`). The missing assertion is the template's shape, not a
  local deletion.
- Evidence it holds in practice at this sha: CI log, `docker-smoke` step "Raw-Docker episode smoke",
  `smoke OK: seats=4 results=281B replay=10742B reason=complete`.

### N3 — The scripted baselines reason over a bounded 3 000-chemistry sample, not the whole surviving set
- Where: `src/cogchemists/chem.nim:258-270` (`BotSampleCap* = 3000`, `consistentSample`), `:272-296`
  (`largestBucket`, `certainPotion`, `canBeNegative`), `:298-307` (`alwaysExposes`);
  `src/cogchemists/llm.nim:181` and `:194` (lab), `:225` and `:234` (market), `:284`/`:288` (the sample is
  built per decision from `sim.knownFacts(seat)`).
- Observed: `consistentSample` stops at 3 000 bijections in Heap order. Early in an episode the surviving
  set is up to 40 320, so `alwaysExposes` ("for every hypothesis still standing the real potion differs
  from the claim's prediction") is evaluated over a truncated prefix — the attack is guaranteed over the
  sample, not over the seat's actual hypothesis set. Same for `largestBucket` (experiment choice) and
  `certainPotion` (the "guaranteed hit" sell).
- Note says: §Scripted baselines — "partition the seat's **currently-consistent chemistries** by the
  potion that pair would produce"; "(b) … it holds a reagent `y` whose demonstration is **guaranteed** to
  expose it". §The deduction grid pins exactness for the **grid**, and the code honours that: `solveGrid`
  enumerates all 40 320 with no cap (`chem.nim:218-231`), and the sampling comment at `chem.nim:258-262`
  says so explicitly ("the GRID itself is never sampled").
- Effect traced: the *stale-grid* direction is safe — `assayerMarket` publishes from `sim.grids[seat]`
  (exact, refreshed at phase open, `sim.nim:170-177`, `llm.nim:210-215`), and a grid computed from fewer
  facts is a superset, so `solved` on a stale grid implies `solved` on the fresh one with the same value.
  The sampled direction is one-sided the other way: `alwaysExposes` can return true when a chemistry
  outside the sample would have survived, which is a failed debunk (−2 reputation), not an illegal move.
  `tests/test_bot.nim:95-105` asserts zero false theories and zero burns for the assayer, not zero failed
  debunks.

### N4 — `applyAct` does not advance the phase; a separate step machine does
- Where: `src/cogchemists/sim.nim:66-75` (`Step` enum — not in the note), `:501-507` (`finishAct`: sets
  `acted`, records last action/result, appends the event, increments `roundsPlayed`; it does **not** open
  the next phase), `:725-732` (`needsAdvance`), `:734-763` (`advance`), and every caller
  (`server.nim:269-273`, `tests/*.nim` `drive()`).
- Note says: §Sim module — "`applyAct(sim, seat, act: Action, scripted: bool)` (… **the last act of a
  phase advances the phase, the last phase of the last round runs `exhibition()` then
  `settle("complete")`**)".
- Observed effect: the emitted event sequence is exactly the note's (`start, round, phase, act×4, phase,
  act×4, …, exhibition, end`, asserted at `tests/test_sim.nim:102-110` and `:690-700`), and the reason the
  code splits it out is documented at `sim.nim:734-736` ("Emits exactly ONE structural event … so every
  recorded event has its own distinct spectator frame"). It is an API-contract difference from the note,
  not an event-stream difference. `stExhibition` (`sim.nim:757-759`) is unreachable: `stActing` calls
  `runExhibition` directly at `:755`.

### N5 — The canvas endcard stamps the truth into the grid strip only; no per-seal TRUE/FALSE tag, no truth row
- Where: `client/renderer.js:690-698` (at the exhibition frame `chemistry.length === 8`, every hole-cam
  cell is redrawn as the true signature in amber); `:522-591` (`drawSeal` — takes no verdict argument and
  draws no TRUE/FALSE tag); `:475-519`/`drawBoard` at `:480-519` (no truth row). `grep -n "chemistry"
  client/renderer.js` returns only lines 603, 692, 696, 1361, 1410 — no other consumer.
- Note says: §The stage, "The endcard reveal" — "every cell resolves to the true signature" (present),
  "correct seals get an amber `TRUE +5`, false seals a red `FALSE −6`" (absent from the canvas), "and the
  row of true signatures is drawn once, large, under the board" (absent).
- Where the verdicts do appear: the feed (`renderer.js:915-921`, "EXHIBITION — Nightcap R+G-B+ TRUE:
  Sprocket +5 …") and the endscreen table's `true`/`false` columns (`:1284-1288`, `:1301-1303`). No
  checklist item covers stage decoration; checklist 14 (chrome provenance) is satisfied — see below.

### N6 — The system prompt omits the Printing Press's royalty doubling
- Where: `src/cogchemists/llm.nim:434-437` (publish: "+2 reputation (+3 with the Printing Press) …
  Standing seals earn their author **+1 coin every round open**" — no Press variant) and `:448`
  ("buy mortar (-4 coin) or buy press (-5 coin), once each." — no effect stated).
- Note says: §Prompts — the system prompt carries "the LAB and MARKET menus with **every cost and
  reward**"; §MARKET menu — "**Printing Press**: `publish` pays +3 instead of +2, **and royalties pay 2
  instead of 1**".
- The rule itself is implemented (`sim.nim:202-206`, `PressRoyaltyCoin`), and the Mortar's effect *is*
  stated in the prompt (`llm.nim:421-425`). Only the royalty half of the Press is missing from the text a
  seat sees.

### N7 — Two starter bootstrap variables are renamed in both replay pages
- Where: `client/replay.html:69-70` (`var wsScheme` / `var replaySocket`, starter: `var scheme` /
  `var socket`), `:75` (`relayout()` where the starter calls `fit()`), `:89`, `:91`.
- Note says: §Chrome provenance — "**Elements removed: none.** The only edits are (a) the wordmark's
  inner text … and the `<title>`, and (b) **one appended element**: `<div id="labbar"></div>`."
- Observed: `diff` against the starter shows exactly: title, wordmark, `#clock` initial text
  (`WEEK 0` → `ROUND 0`), the appended `#labbar` div, the `relayout()`/`buildLabBar()` additions (which
  §Transport rules does sanction), the two variable renames, and the `labbar:` key added to the
  `attachReplay` options. **Nothing is removed**, every starter id survives, and the renames are what
  `tests/test_viewer.nim:130-142` (the anti-shadowing check) is enforcing. `replay-viewer/index.html`
  gets the identical treatment.

### N8 — Two sub-assertions of note tests 10 and 12 are absent
- Where: `tests/test_sim.nim:273-288` (endorse) and `:368-412` (same-phase conflicts).
- Note says: test 10 — endorse "is illegal on your own seal, **on a burned seal**, and twice"; test 12 —
  "an endorse of the same seal by the same seat twice is **`rejected:already_endorsed`**".
- Observed: `own_theory` (`:277`) and `already_endorsed` (`:288`) are asserted through `checkAct`; the
  burned-seal case is not asserted anywhere (it is reachable — `sealIndex` only returns standing seals,
  `sim.nim:301-306`, so a burned seal yields `no_such_theory`, not `already_endorsed`), and the
  double-endorse case is asserted as a `checkAct` reason rather than as a recorded rejection event. The
  rejection-event shape *is* asserted for `publish` (`:382-387`) and the burned-seal debunk (`:403-404`).

### N9 — Test 16's "no signature the seat's own facts do not imply" is not asserted
- Where: `tests/test_sim.nim:515-573`.
- Observed: the test asserts the frame has no `chemistry` key (`:526`), that no rival `table` entry
  carries `hand`/`grid`/`notes`/`facts`/`chemistries` (`:527-529`), that no rival's notes appear in the
  frame text or the prompt (`:536-541`), that an unsolved ingredient is never printed `SOLVED`
  (`:543-546`), and the full converse (every held card, every attackable seal, an affordable artifact all
  appear verbatim in `LEGAL MOVES`, `:547-559`).
- Note says: test 16 adds "**and no signature of the true chemistry that the seat's own facts do not
  already imply**". That clause has no corresponding `check`.

### N10 — Replay grid equality is asserted for the final frame only
- Where: `tests/test_sim.nim:588-594` — `frames.len == events.len + 1`, `$frames[^1].tableStateJson() ==
  $sim.tableStateJson()`, and `frames[^1].grids[seat]` vs `sim.grids[seat]` for all four seats. No loop
  compares intermediate frames.
- Note says: test 17 — "**all four grids in the re-derived frames equal the live ones**" (plural frames).
- Context for checklist 2: the replay bytes carry **no** per-tick state (`server.nim:126-150`: protocol,
  names, policyNames, config, events, results — no `states`), so there is no parallel recording for the
  viewer to prefer; `states` is produced *by* the re-derivation, in the server's replay mode
  (`server.nim:152-156`) and in the wasm module (`replay-viewer/cogchemists_replay.nim:38-40`), and
  `attachReplay` draws `states[index]` (`renderer.js:1633`, `:1654-1657`, `:1704-1707`). What
  `replayMatch` does assert per event is in "Traced and consistent" below.

### N11 — The performance budgets the note quotes hold only under `-d:release`
- Where: `tests/test_chem.nim:9-10` — `SolveBudgetMs = when defined(release): 25 else: 250`,
  `RefreshBudgetMs = when defined(release): 400 else: 4000`; used at `:207` and `:226`.
- Note says: test 5 — "a full grid solve with 40 facts completes in **under 25 ms native**, and the
  memoised per-phase refresh for a 10-round episode totals **under 400 ms**". CI runs every test file in
  both modes (`ci.yml:104-149`), so the 25/400 ms bound is exercised, just not in the debug pass.
  Related: the note says "≤ 4 × 2 × 10 + 4 = 84 recomputes"; the test loops 80 (`:217-221`,
  `2 * MaxRounds * Seats`).

### N12 — The play deadline is tested once per phase, not before the retry batch
- Where: `src/cogchemists/server.nim:289-296` (the check) then `:305` (`decideAll`, which fires up to two
  batches internally, `llm.nim:753-784`).
- Note says: §Decisions — "The deadline is checked **before every batch**"; §End conditions — "checked
  **before every LLM batch, i.e. only ever between phases**". The code matches the second phrasing.
- Bound traced: worst case one phase = spacing floor 10 s + 20 s + 20 s ≈ 50 s of overshoot past the
  deadline, against `720 − 663 ≈ 57 s` of headroom in the note's own arithmetic and ~480 s of real
  headroom on the typical episode. Every wait in that path is explicitly bounded — see "Traced and
  consistent".

### N13 — `observationJson` carries `you.facts`, which the note's player-frame listing omits
- Where: `src/cogchemists/sim.nim:995-1000` (`"facts": privateFacts` inside `you`).
- Note says: §Player protocol — `"you":{coin,reputation,score,hand,mortar,press,grid,chemistries,notes}`
  (no `facts`); §Per-seat observation item 6 — "**Its own facts**: every `mixFull` it holds privately, as
  a table". The two halves of the note disagree; the code implements the fuller one, and the manifest's
  `game.protocols.player` text (`coworld_manifest_template.json:274`) documents `facts` in the frame, so
  the shipped protocol description and the code agree.

---

## Traced and consistent

**Resolution rules — the eight numbered steps (§The game).**
- Step 1 round open: `sim.nim:196-218` — royalties paid on every *standing* seal, `PressRoyaltyCoin` when
  the author owns the press (`:202-206`); the demand for the round is published from the seeded array
  (`:213`, drawn once at `:249-250` from `ColouredPotions`, so never MUD); initiative published (`:214`).
  Seals published in round *r* first earn at the open of *r+1*, as the note requires.
- Step 2/4 phase open: `openPhase` (`sim.nim:220-231`) rotates `say`→`heard`, clears the bench, and calls
  `refreshGrids` (`:170-177`) — one exact `solveGrid` per seat whose facts moved, memoised on
  `factsVersion`/`gridVersion` (`:179-186`).
- Steps 3/5 resolution in initiative order: `server.nim:280` snapshots `initiativeOrder(round)`,
  `:308-326` applies in that order under the lock; a raise becomes
  `applyRejection` → `result: "rejected:<reason>"` + the `pass` stipend (`sim.nim:662-682`).
  `initiativeOrder(round)[i] == (i + round) mod 4` (`sim.nim:188-192`).
- Step 6/7/8: `advance` (`sim.nim:734-763`) → `runExhibition` (`:684-713`) → `settle` (`:715-723`).
- Mixing rule: `chem.nim:111-133`. I re-implemented the note's three clauses in Python and checked all 28
  unordered pairs against the Nim reading: exactly 2 pairs per coloured potion, 16 MUD, and the note's
  five worked examples (`BLUE+`, `GREEN+`, `RED-`, `RED+`, `MUD`) reproduce. Symmetric by construction
  (`diff = sa xor sb`); `count != 1` (including 0, i.e. the same ingredient twice) → MUD (`:127-128`).
  `tests/test_chem.nim:59-88` asserts the same three facts.
- LAB menu costs/rewards: `forage` 2 draws, cap 6, overflow recorded in `discarded` (`sim.nim:530-537`);
  `test_student` −1 coin, both cards, private `mixFull` only (`:538-548`); `test_self` free, private
  `mixFull` **and** public `mixSign`, rep +1/0/−2 with outcomes `glowed`/`ok`/`poisoned` (`:552-563`);
  Mortar spares card `b` for both (`:541`, `:330-332`); `transmute` +2 (`:566-569`); `pass` +1
  (`:656-659`).
- MARKET menu: `sell` hit +6/+1, miss +2/−1, always public `mixFull` (`:570-590`); `publish` −1 coin,
  +2/+3 with press, seal pinned standing, illegal where a seal stands (`:591-601`, `:378-385`);
  `endorse` −1 coin **paid to the author**, never own, never twice (`:602-610`, `:386-394`); `buy`
  mortar −4 / press −5, once each, gated on `config.artifacts` (`:647-655`, `:405-418`).
- Debunk arithmetic, both cases: `sim.nim:611-646`. `real = mix(chem[x], chem[y])`,
  `predicted = mixSignatures(claim, chem[y])`, the real potion is minted public either way (`:625`).
  Burn: author −4, debunker +3, each endorser −1, status `burned`, `notSig(x, claim)` minted, `x`
  publishable again because `sealIndex` filters on standing (`:626-638`, `:301-306`). Survive: debunker
  −2, author +1, `vindications` +1 (`:639-644`). Both asserted at `tests/test_sim.nim:319-366`, the
  survive case with an explicitly *wrong* claim this reagent cannot expose (`:353-357`).
- Exhibition payoffs: true +5 author / +2 each endorser, false −6 / −3, burned seals skipped
  (`sim.nim:690-704`), event carries the whole chemistry (`:710-711`). Asserted
  `tests/test_sim.nim:415-445`.
- Coin can never go negative: every coin-spending verb is gated in `checkAct` (`sim.nim:364-365`,
  `:383`, `:393`, `:403`, `:411`, `:415`) and `pass` is unconditional (`:353-354`), so a legal move
  always exists. `tests/test_bot.nim:56` asserts it over 12 scripted episodes.
- Scoring: `score = reputation + 0.2*coin` (`sim.nim:271-274`, `CoinWeight* = 0.2` at `:51`).
  `tests/test_score.nim:73-96` reproduces the note's 22.2 landmark (rep 18, coin 21) and the 13.2
  do-nothing floor to 1e-9, and the 11-point true-vs-false gap. I re-derived both by hand and they match.

**Decision path.** One `RequestBatch` per attempt, one `curly.makeRequests` for all open seats
(`llm.nim:756-767`) — the simultaneous-decision rule at the foot of the checklist is satisfied; there is
no per-seat call anywhere. `extractJsonObject` takes `find('{')`..`rfind('}')`, so surrounding prose and
fences are tolerated (`:650-661`, asserted `tests/test_bot.nim:240-246`). `parseReply` normalises the verb
(`-`/space → `_`, lowercased, `:334-338`), resolves ingredients by full name, ≥3-letter unique prefix, or
index (`:305-332`), rejects a wrong-phase verb against the phase's menu (`:353-356`), and parses the
signature tolerantly (`chem.nim:87-101`). Illegal-at-this-instant replies are caught by a probe copy —
`var probe = sim; probe.applyAct(seat, action, false)` (`llm.nim:776-778`) — inside the `try`, so they
retry rather than silently falling back. `for attempt in 0 .. 1` = exactly one retry, with the
"your previous reply was invalid" hint appended to the second batch (`:753`, `:760-762`).
`client.disabled` short-circuits before any network work and zeroes the spacing floor
(`llm.nim:137-143`, `:727-728`, `:748`), asserted at `tests/test_bot.nim:133-162`.

**Every wait and its bound.**
- Player connect: `while epochTime() < connectDeadline` with `sleep(200)`, deadline =
  `gameStart + playerConnectTimeoutSeconds` (default 180) — `server.nim:221-229`.
- LLM call: `client.curl.makeRequests(batch, client.timeoutSeconds)` with
  `timeoutSeconds = config.llmTimeoutSeconds` (20) — `llm.nim:767`, `:110`.
- Batch spacing: `awaitBatchSlot` sleeps at most `minBatchSpacingMs` and only relative to the previous
  batch *start* (`llm.nim:723-732`).
- Play deadline: `PlayBudgetFraction* = 0.6` (`server.nim:212`), timeout from
  `COWORLD_TIMEOUT_SECONDS` or `config.episodeTimeoutSeconds` (1200) (`:244-253`), tested at `:289`,
  past it `endEarly()` + break (`:294-296`). `endEarly` runs the exhibition first and settles
  `"deadline"`, and is a no-op once done (`sim.nim:765-774`); asserted
  `tests/test_sim.nim:447-459`, `:702-716`.
- Round barrier: there is no blocking read. The loop is `while true` with three exits (done, deadline,
  and the drain loop at `server.nim:334-342`); the `seats.len == 0` branch (`:298-300`) is preceded by the
  deadline test, and is in fact unreachable because `needsAdvance` is true whenever all seats have acted
  (`sim.nim:725-732`).
- Shutdown grace: `sleep(max(0, grace) * 1000)` with `grace = config.shutdownGraceSeconds` (20) then
  `quit(0)` — `server.nim:206-210`, after `results.json` and the replay are written and after the final
  frames are pushed to players (`:170-191`).
- Pacing: `turnDelayMs` is clamped by `sampleEpisode` to `PacingBudgetMs div (2*rounds)`
  (`sim.nim:141-151`), i.e. ≤ 60 s of pacing per episode.
- Player side: the receive loop is wrapped in `try/except CatchableError` and exits 0 on a dead socket
  (`src/cogchemists_player.nim:63-93`).

**String truncation.** `say`: `cleanSay` strips, collapses `\n`/`\r`, and cuts with
`runeSubStr(0, MaxSayLen)` (`sim.nim:479-486`); `notes`: `runeSubStr(0, MaxNotesLen)` (`:488-491`);
`cleanText` (used for `action` 24, `a`/`b` 24, `signature` 12, `artifact` 12, `say`, `notes`) cuts at
`limit - 1` runes and appends `…`, so the result is exactly `limit` runes (`llm.nim:292-298`); player
prompt 4000 runes on both ends (`server.nim:466-467`, `cogchemists_player.nim:46-47`).
`tests/test_sim.nim:462-487` feeds `"é"×400` / `"ø"×800` and asserts 140/600 runes,
`validateUtf8() == -1` on every `say` and `text` in the log, and that the whole serialised event array
survives a strict parse; `tests/test_bot.nim:193-207` asserts the same for the parser side. With
`talk = false` every `say` is `""` (`sim.nim:480-481`, asserted `tests/test_sim.nim:489-496`).

**Replay writer and `replayMatch`.** The written payload is protocol/names/policyNames/config
(rounds, seed, talk, artifacts, sampled, chemistry)/events/results — `server.nim:126-150`, matching
§Replay payload. `replayMatch` (`sim.nim:1155-1222`) rebuilds from `config.seed`, then **raises
`CogchemistsError`** on: a recorded chemistry ≠ the seeded one (`:1172-1174`), a recorded opening hand ≠
the re-derivation (`:1175-1179`), an out-of-order round (`:1182-1184`), a recorded demand ≠ the seeded one
(`:1185-1188`), a recorded `draws` array ≠ the re-derivation (`:1203-1205`), a recorded potion ≠ the
re-derived one (`:1206-1208`), and a recorded exhibition chemistry ≠ the truth (`:1213-1215`).
`frames[i]` = state after `events[0..<i]`, `frames.len == events.len + 1` (`:1165`, `:1222`). A recorded
`deadline` end re-derives as `deadline` (`:1216-1221`, asserted `tests/test_sim.nim:676-687`). All three
tamper cases are asserted (`tests/test_sim.nim:644-674`), and every event kind round-trips field by field
with all six kinds required to be present (`:596-642`).

**Viewer re-derivation.** `replay-viewer/cogchemists_replay.nim:22-54` is `bullwhip_replay.nim` renamed
(`diff` confirms: comments, `bw_`→`cc_`, `weeks`→`rounds`, `artifacts` added) and calls the same
`replayMatch` + `tableStateJson` the server runs (`:39-40`), returning 0 and setting `lastError` on a
raise (`:52-54`). All four viewer files are bullwhip's: `config.nims` differs only in output name,
`EXPORT_NAME`, and the exported symbol list; `static_replay.js` differs only in the `cc_` symbols, the
renderer global, the added `labbar` option, and the ready-polling block; `index.html` differs only in
title/wordmark/clock text, the `#labbar` div, the script name, and `relayout()`.
**MODULARIZE pairing:** `-s MODULARIZE=1` + `-s EXPORT_NAME=CogchemistsReplayModule`
(`config.nims:38-39`) against `modulePromise = CogchemistsReplayModule()` in the shell
(`static_replay.js:153`); `onRuntimeInitialized` appears nowhere (`tests/test_viewer.nim:144-157` asserts
both directions). **Signals:** `data-replay-loaded="true"` is set at `renderer.js:1711`, after the
`(function frame(timestamp){…})(0)` IIFE at `:1683-1709` has already called `renderer.draw(view)` once —
i.e. on the first drawn frame, and byte-for-byte where bullwhip sets it (`starter renderer.js:1390`).
`data-replay-error` is set on every failure path and removed on a successful retry
(`static_replay.js:56`, `:107`, `:149`). `start()` posts `ready` only after polling the loaded attribute,
bounded at 240 frames then `fail("renderer never drew a frame")` (`static_replay.js:120-139`).

**Chrome provenance.** `client/chrome.css` bytes 0..11963 are **byte-identical** to the starter's
(verified: `sha1 = 8f0d16397cb227a427ec1112d39c180f1aef1bfd` for both the prefix and the whole starter
file), followed by exactly one `/* ---------- Cogchemists ---------- */` block (occurrences: 1);
`tests/test_viewer.nim:70-80` pins the same hash. `client/replay.html` is the starter page: every id in
the note's list is present in source order (`:9-37`), `#labbar` sits between `#scorebug` and
`#board-wrap` (`:19-21`), and `diff` shows **no removals**. `relayout()` sets `--band` (measured from
`#transport.offsetHeight`) and `--hudscale` on `document.documentElement` and then calls `fit()` from the
same function (`:52-63`), bound to `load`, `resize`, and — via `bindFeedToggle`'s dispatched
`resize` (`renderer.js:1326-1341`) — the feed toggle. Nothing fixed-positioned rides in the band:
`#lightpool`/`#grain`/`#endscreen` are absolute inside `#board-wrap` (`chrome.css:95`, `:374-376`), which
ends where `#transport` begins in normal flex flow, and `#loading` is pinned with
`bottom: var(--band)` (`chrome.css:600`). `#endscreen` is shown with the class its rule uses
(`#endscreen.show`, `chrome.css:383`; `container.classList.toggle("show", !!show)` at
`renderer.js:1254`), and **every** index change calls `updateEndscreen` (`renderer.js:1678-1679` inside
`setIndex`, which is what both the scrub drag, the beat buttons and the auto-advance go through).
Beats are `<button type="button">` with `title` + `aria-label` + an `onclick` that seeks
(`renderer.js:1489-1504`), the container keeps its pointerdown/move/up drag-seek handlers
(`:1607-1617`), and `beatKind` emits exactly seven kinds — publish, debunk, sell, test, trade,
exhibition, end (`:1506-1519`) — each of which has a CSS rule in the appended block
(`chrome.css:545-580`), asserted at `tests/test_viewer.nim:82-85`. The builder is named
`markChemBeat`, never `markBeat` (`:1487-1489`, asserted `test_viewer.nim:130-135`). No `#viewpanel`,
`zoomAt`, `setZoom` or `attachMinimap` exists anywhere in `client/` or `replay-viewer/` (grep: no hits) —
the note says the arena is fixed and bullwhip ships no panel.

**360 px legibility.** `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` — `chrome.css:280-292`
(inherited from the starter, unmodified). `@media (max-width: 640px)` hides `.plate-label` and
`.plate-coin` and shrinks `#labbar`; `@media (max-width: 420px)` keeps the two-column scorebug and hides
`.plate-solved` (`chrome.css:602-609`). Canvas side: `L.narrow` at `< 640` drops hand cards to a count
(`renderer.js:305-314`), drops the seal's ingredient name (`:540-546`), and collapses the hole-cam strip
to "N solved · M left" per seat (`:611-635`); `#labbar` shortens below 420 (`:1229-1231`). Readouts are
words and numerals throughout (`ROUND 3 / 4 · LAB · WAITING ON 2` — from the CI smoke's own readout —
`SEAL BURNED`, `RED+`, `rep`).

**Two name spaces.** In-game names come from `tableNames` (seeded shuffle of `CogNames`,
`sim.nim:128-139`); policy names appear only in `resultsJson` (`sim.nim:791`) and the spectator
`policyNames` array (`server.nim:72-78`, `:139`). `makeNameMap`/`applyNames`/`isBaselineFiller` are
bullwhip's, unchanged (`renderer.js:834-870`; the regex is identical to the starter's), and they swap
names only where rendered. The final frame sent to players carries aliases, not policy names
(`server.nim:175-186`).

**Manifest.** `"replay_viewer": {"bundle": "static-replay-viewer"}` (`:16-18`);
`num_agents: 4` in `standard` (`:402`), in `silent-academy` (`:429`) **and** in
`certification.game_config` (`:454`); `config_schema` with `additionalProperties: false`,
`required: ["tokens","players"]`, `minItems`/`maxItems` 4 on both arrays, `num_agents` integer min 4 max 4,
and every documented bound (`:32-147`); `results_schema` with all twelve required keys and 4/4 bounds on
every array, `scores` unbounded numbers (`:149-269`); `game.docs` is
`{"readme":{"type":"text","value":…},"pages":[{id,title,content:{type,value}}×3]}` (`:281-312`) with
rules.md / deduction.md / scoring.md carrying the mixing table, the debunk's two cases and the 22.2 /
13.2 landmarks; `game.protocols` carries **both** `player` and `global` in full (`:271-280`);
`env.ANTHROPIC_API_KEY_URI = "secret://coworld/cogchemists/anthropic_api_key"` (`:28`);
`episode_timeout_minutes: 20` (`:13`); eight tags (`:3-12`); three player runnables, each occupying at
least one certification slot (`:314-381`, `:461-474`). `compose.yaml` service is `cogchemists` and the
image placeholder is `{{COGCHEMISTS_IMAGE}}` throughout.

**Workflows and scaffold.** Three workflows present. The checklist-12 placeholder gate
(`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files) returns **no matches** → exits 0; the four
documented residue names (`<cow_id>`/`<sha>` in `ci.yml:202`, `<run_id>` in `coworld-release.yml:21` and
`coworld-submit.yml:17`, `<name>:vN` in `coworld-submit.yml:31`) are exactly the expected ones.
`coworld-release.yml` order: build manifest (`:153`) → certify (`:167`) → **upload the policies**
(`:206`) → upload the Coworld (`:304`) → put the secret (`:342`, `if` after upload). `docker_smoke.sh` is
mode `100755` (git index `100755`), `build_replay_viewer.sh` `100755`; `ci.yml` asserts both bits before
invoking them by path (`:166-175`, `:225-237`). `tools/ci/viewer_smoke.mjs` is **byte-identical** to
`/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` empty). `tools/ci/policies.json`
defines four distinct policies: two `PLAYER_PROMPT` champions (`cogchemists-empiricist`,
`cogchemists-careerist`) with champion #2 carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus `PLAYER_SCRIPTED=assayer` and
`PLAYER_SCRIPTED=quack` fillers. Seat-count invariants: all four are enforced before any container starts
(`docker_smoke.sh:110-118` present, `:119-125` positive integer, `:129-134` `len(certification.players)`,
`:135-140` `len(certification.game_config.players)`), plus the independent `SMOKE_SEATS` cross-check
(`:141-151`), each exiting non-zero with a `SEAT-COUNT FAIL:` prefix.

**CI evidence (checklist 1, 6, 13).** `gh run list -R Metta-AI/cogame-cogchemists --branch main -w ci.yml`
→ run **32702248279**, head commit `bot: the quack must spell symmetric pairs the way LEGAL MOVES does`
(= the reviewed sha), conclusion **success**, 3m17s. Per-job: `test` success (step "Run tests" success),
`docker-smoke` success (step "Raw-Docker episode smoke" success), `wasm-viewer` success **including the
step "Load the bundle in a real browser"** — no `continue-on-error` on it (`ci.yml:293-317`), and
`wasm-viewer` declares `needs: docker-smoke` (`ci.yml:212`). Full log grep: `SEAT-COUNT FAIL` occurs
**0** times. Smoke output: `game=cogchemists seats=4 … "num_agents": 4 … "rounds": 4`,
`episode end reason: complete`, `smoke OK: seats=4 results=281B replay=10742B reason=complete`,
`all 4 player containers exited 0`. Viewer smoke output:
`{"loaded":true,"ms":276,"clock":"ROUND 2 / 4 · LAB · WAITING ON 2","scorebug":"Sprocket ▶ 10 REP 4c 0
SOLVED …","feed_lines":62}` and `soak: 15s of playback kept advancing (null -> null -> null)` — the three
`null`s are the harness's optional `#tick` selector, which this page does not ship
(`viewer_smoke.mjs:289`); `moved` is computed over `["clock","tick","scorebug"]` with `.some()`
(`viewer_smoke.mjs:402-403`), so the pass came from the clock/scorebug moving in **both** intervals, and
`data-replay-error` was never set (the run would have failed otherwise, `:56`, `:440-470`).
The only test-file change in this run's history is `5a82157`, which **strengthens** the bounded/legal
assertions (`check` → `doAssert` with a message) and deletes nothing: `git show 5a82157 -- tests/` shows
`-check showAct(decision) in result.legalMoves(seat)` replaced by the same predicate under `doAssert`,
same for `say`/`notes`/coin/hand-cap. No `skip`, no widened tolerance, no removed file.

**Tests, note items 1–27, presence check.** 1–5 `tests/test_chem.nim:58-226` (with an independent
`nextPermutation` brute force at `:29-56`); 6–18 `tests/test_sim.nim:80-716`; 19–22
`tests/test_bot.nim:68-246`; 23 `tests/test_score.nim:61-115`; 24 `tests/test_viewer.nim:69-169`;
25–26 `tools/ci/docker_smoke.sh` (see N2 for the one missing assertion); 27 `ci.yml:207-317`. Every item
exists and asserts what the note says except the sub-clauses recorded in N2, N8, N9, N10 and N11.
The 47-event arithmetic in the note checks out: 4 rounds × (1 round + 2 phase + 8 acts) + start +
exhibition + end = 47, and at the coded dwell times (`renderer.js:1687-1693`: 1400 round / 900 phase /
800 act / 3000 exhibition / 2000 end) that is ≈ 44.6 s of playback against a 15 s soak.

---

## Could not determine

- **Checklist 7's second sentence — "The baseline's parameters were tuned with a grid harness, not
  guessed."** There is no tuning harness, sweep script, or recorded grid anywhere in the tree
  (`git ls-files` has no `tools/tune*`, no bench, and the design note's §Tests does not describe one).
  What exists instead: the assayer has essentially one free numeric knob (`me.coin >= StudentCost + 1`,
  `llm.nim:190`) plus `BotSampleCap = 3000` (`chem.nim:258`), and `tests/test_bot.nim:121-131` asserts
  assayer-mean > quack-mean on each of four seeds and **echoes both numbers** so drift is visible.
  What would settle it: a harness script or a recorded sweep in the repo or the run directory, or a
  statement in `log.md` about how the two thresholds were chosen.
- **Whether the sampled `alwaysExposes` (N3) ever produces a failed debunk in practice.** Deciding it
  needs an instrumented run counting `outcome == "survived"` for assayer seats over a seed sweep; nothing
  in the tree records it and I cannot compile Nim here.
- **Local test execution.** No `nim`/`nimble` in this sandbox, so every test assertion above is read, not
  run. CI ran all five files twice (debug and `-d:release`) in run 32702248279, step "Run tests" green.
- **`/client/replay` route vs checklist 3's "No `/client/replay` pod path anywhere".** The repo does
  register `GET /client/replay` (`server.nim:500`) and ships `client/replay.html`; both are the starter's
  live-server replay page and are inherited unchanged in shape. The *manifest* declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` and no pod path of any kind
  (`coworld_manifest_template.json:16-18`, and no `"path"`/`"type": "pod"` key exists in the file). I read
  the checklist item as aimed at the manifest declaration, which is satisfied; flagging it here so the
  judge can decide whether the inherited live route counts.
