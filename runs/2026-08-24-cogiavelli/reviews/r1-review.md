# r1 review — cogiavelli

Range: `b619ecc..f6862a31255c61d448b37da0d39a44db211ed179` (the whole game commit; `b619ecc` is
the bootstrap). Repo read at `/workspace/build/cogame-cogiavelli`, sha `f6862a3`.
Files read: 38 (all of `src/`, `replay-viewer/`, `client/`, `tests/`, `tools/`,
`.github/workflows/`, `coworld_manifest_template.json`, `compose.yaml`, `Dockerfile`,
`data/italy1499.json`, plus the babel starter's counterparts for every diffed file and
`src/bullwhip/llm.nim:425-478`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–14 + the
simultaneous-decision addendum).
Design note: `/workspace/coworld-builder/runs/2026-08-24-cogiavelli/design.md` (byte-identical to
the in-repo copy `docs/plans/2026-08-24-cogiavelli-design.md` — `diff` returns 0).

Convention below: **observed** = I read the code; **inferred** = I reasoned from what I read;
**untested** = it would take a run to settle.

---

## Blocking

**None.** I could not falsify any of the fourteen checklist items from the tree or from the CI
evidence. Every item I could check is recorded under *Traced and consistent*; the two items where
my verification is partial are recorded under *Could not determine* with what would settle them.

---

## Non-blocking

### N1 — `replayMatch` checks the derived event *sequence* and the shock draws, but never compares a recorded board snapshot against the re-derivation
- Where: `src/cogiavelli/sim.nim:1444-1502`; note claim at `design.md:708`.
- Observed: `replayMatch` re-runs `applyPress`/`applyOrders` (`sim.nim:1456-1461`), then for every
  recorded event asserts `logged.kind == event.kind` (`sim.nim:1470-1474`) and, for the four shock
  kinds only, compares the drawn values: `evFamine.provinces` (1476-1479), `evPlague.province`
  (1480-1483), `evAssassin.d1/d2/roll` (1484-1488), `evWinter.incomeDraws` and
  `rebellions[].roll` (1489-1497). Nothing compares `evSeason.units/owners/treasury/cityCounts`,
  `evCities.owners/counts`, `evWinter.treasury`, `evBattle.results` or `evSpend.entries` against
  the re-derived values; those branches fall into `else: discard` (1498-1499).
- What the note says: `design.md:708` — the `season` event's board fields are "the derived board,
  **checked** against the seeded re-derivation in `replayMatch`". They are not checked.
- Checklist item: item 2 ("Replaying the recorded events through the sim reproduces the recorded
  per-tick state frame by frame … A test asserts it"). I record this as non-blocking because the
  substantive half of item 2 *is* satisfied — the viewer's display comes from the re-derivation
  (`replay-viewer/cogiavelli_replay.nim:38-39`) and not from a parallel recording, and
  `tests/test_sim.nim:301-307` asserts `frames.len == events.len + 1` and that the final frame's
  `tableStateJson` is byte-equal to the live sim's. The gap is that a tampered board snapshot
  (as opposed to a tampered *draw*, which `tests/test_sim.nim:309-321` proves does raise) would
  pass silently.
- Note (inferred): the starter does the same — babel's `replayMatch`
  (`/workspace/starters/cogame-babel/src/babel/sim.nim:505-535`) checks only its round schedule,
  never a board snapshot. Cogiavelli is strictly stricter than babel here (it checks kind-for-kind
  on *every* event, babel does not).

### N2 — `replayMatch` compares rebellion rolls only when the two lists are the same length
- Where: `src/cogiavelli/sim.nim:1493-1497`.
- Observed:
  ```nim
  if logged.rebellions.len == event.rebellions.len:
    for index in 0 ..< event.rebellions.len:
      if logged.rebellions[index].roll != event.rebellions[index].roll: raise ...
  ```
  A recorded `winter` event carrying a *different number* of rebellion rolls than the
  re-derivation produces is accepted without a raise. `incomeDraws` immediately above (1490-1492)
  uses `!=` on the whole seq and so does catch a length difference.
- What the note says: `design.md:299-302` — "`replayMatch` … **raises if a recorded draw
  disagrees with the re-derived one**".
- Checklist item: none names this. Non-blocking.

### N3 — the peace and support pledges are evaluated against the **post-movement** board, so a successful stab into a non-city province is not stamped
- Where: `src/cogiavelli/sim.nim:552-604`, called at `sim.nim:774` — i.e. after
  `sim.runRetreats()` at `sim.nim:772` has rebuilt `sim.board` with every successful move applied.
- Observed, `plPeace` branch (`sim.nim:575-580`):
  ```nim
  let hostile =
    (sim.board.hasUnit(into) and sim.board.unitAt(into).power == victim) or
    (isCity(into) and sim.owner[CityIndex[into]] == victim)
  ```
  `sim.board` here is the board *after* movement and retreats. Traced consequences:
  * a pledger's move into a victim-held **non-city** province that **succeeds** — the victim's
    unit is gone from `into` and the pledger's unit is there, so the first disjunct is false; the
    second is false because `into` is not a city ⇒ **no stab recorded**;
  * the same move that **bounces** — the victim's unit is still at `into` ⇒ **stab recorded**;
  * a move into a victim-**owned city** is caught either way, because `sim.owner` is still
    pre-`updateCities` at this point (`updateCities` runs at `sim.nim:780`).
- Observed, `plSupport` branch (`sim.nim:588-600`): `sim.board.unitAt(order.auxFrom).power ==
  pledge.toPower` — same post-movement board, so a support of an allied unit that successfully
  *moved away* reads as "supported nobody" and the pledge is recorded broken.
- What the note says: `design.md:388,390` — peace is broken when the orders "…move any unit into a
  province occupied by a Milanese unit … **or** support any such move"; support is broken when the
  orders "…contain no order supporting a Neapolitan unit". Both are stated over the orders and the
  pre-resolution board.
- Checklist item: none. The pledge/`stab` mechanism is not named in any of the fourteen items.
  Non-blocking. Not covered by any test (no test in `tests/` exercises `pledgeStabs`).

### N4 — the ledger block in the orders/press prompt is capped by line count, not by "the last two years"
- Where: `src/cogiavelli/llm.nim:473-499`.
- Observed: `let cutoff = sim.year - 1` (476) is computed, never used in the filter, and then
  explicitly thrown away — `discard cutoff` (494). The filter that survives is
  `if lines.len > 40: lines = lines[lines.len - 40 .. ^1]` (497-498).
- What the note says: `design.md:349-350`, `design.md:511` — the prompt carries "the resolved
  ledger of the last two years". `historyText` (`llm.nim:501-524`) *does* implement the two-year
  window correctly (`if sim.history.len > 6: start = sim.history.len - 6`, i.e. 2 years × 3
  seasons).
- Checklist item: none. Non-blocking. (Direction of the divergence: at 4 years the ledger can be
  longer than two years' worth, never shorter, so no information the note promises is withheld.)

### N5 — the bribe menu in the orders prompt always quotes 9 / 15, with `defence` hard-wired to 0
- Where: `src/cogiavelli/llm.nim:573-585` — `var defence = 0` (578) is never assigned, and the
  line printed is `" — disband " & $(BribeDisbandCost + defence) & ", buy " & $(BribeBuyCost +
  defence)`.
- What the note says: `design.md:357-359` promises "the complete list of bribable enemy units with
  the exact **minimum ducats** each would cost (the same predicates the validator applies,
  precomputed)". The note's own worked example at `design.md:522` is `A ROM (PAPACY) — disband 9,
  buy 15`, i.e. the note's example is the defence-free figure too.
- Inferred: the true minimum cannot be known at prompt time — the defender's `defend` entries are
  submitted in the *same* simultaneous batch (`design.md:369`, hidden information), so `defence`
  is unknowable when the menu is built. The dead variable is the only artefact.
- Checklist item: none. Non-blocking.

### N6 — the Spring famine draw uses rejection sampling, so it consumes a variable (≥ 2) number of draws from the shock stream
- Where: `src/cogiavelli/sim.nim:311-317`:
  ```nim
  while sim.famine.len < FamineProvinces:
    let draw = land[sim.shockRng.rand(land.high)]
    if draw notin sim.famine: sim.famine.add(draw)
  ```
- What the note says: `design.md:294-296` — the stream is "advanced in exactly this order and
  nowhere else: (1) Spring famine, **2 draws**".
- Observed consequence: on a collision the loop draws a third (or fourth …) time. The stream stays
  fully deterministic from the seed and the replay re-derives it identically
  (`tests/test_sim.nim:323-333` asserts byte-identical event logs for a repeated seed;
  `tests/test_money.nim:235-254` asserts draw reproducibility), so nothing observable breaks — only
  the note's "2 draws" wording is inexact.
- Checklist item: none. Non-blocking.

### N7 — the adjudicator carries a third cycle-breaking fallback beyond the note's "exactly two backup rules"
- Where: `src/cogiavelli/adjudicate.nim:212-254`, specifically 250-254:
  ```nim
  if voided.len == 0:
    ## Nothing convoyed to void: break the cycle on its first member so
    ## the resolver always terminates.
    r.state[cycle[0]] = mResolved
    r.value[cycle[0]] = false
  ```
- Observed: `backupRule` implements (a) circular movement — a cycle made only of moves resolves
  every move `true` (224-228); (b) the Szykman rule — every convoyed move implicated in the cycle
  is voided (230-249); and (c) the above, which fires only when the cycle is neither all-moves nor
  contains a convoyed move.
- What the note says: `design.md:239-242` — "**Backup rules, exactly two**".
- Inferred: (c) is a termination guarantee, not a rule with game semantics — without it a cycle of
  mixed non-convoy orders could loop. It is the reason the design note's claim at `design.md:611`
  ("the resolver's cycle detection terminates on the two backup rules") holds in practice.
- Checklist item: none. Non-blocking.

### N8 — `conquestCheck` takes the *last* power at ≥ 12 cities when two are simultaneously at 12
- Where: `src/cogiavelli/sim.nim:443-458`:
  ```nim
  for power in 0 ..< Powers:
    if counts[power] >= VictoryCities: leader = power
  ```
  — the assignment overwrites, so with two powers at exactly 12 the higher power index wins.
- What the note says: `design.md:311-312` names one conqueror without tie-breaking language.
- Inferred: 12 + 12 = 24 = `TotalCities`, so the tie is reachable only when every city is owned and
  split exactly evenly between two powers. No test covers it.
- Checklist item: none. Non-blocking.

### N9 — a bribe that is merely **underpaid** is reported with `outcome == "defended"`
- Where: `src/cogiavelli/money.nim:141-153`. `var outcome = "defended"` (144) is the default; an
  entry that fails `entry.amount >= bribeCost(entry.kind) + defence[province]` (145) keeps it, even
  when `defence[province] == 0` and the payer simply bid below cost.
- What the note says: `design.md:202` — the outcome vocabulary is `bought` / `disbanded` /
  `outbid` / `defended`, with `defended` implied to mean "the owner's loyalty payment beat it".
  There is no vocabulary entry for "underpaid", so the code has nowhere else to put it.
- Downstream: the viewer prints this through `bribeLine` in the appended feed block; a 5-ducat
  disband attempt against 0 defence reads as "defended".
- Checklist item: none. Non-blocking.

### N10 — the seat→power permutation and the cog aliases are drawn from **two** setup streams, not one
- Where: `src/cogiavelli/sim.nim:186` (`initRand(int64(seed) * 6779 + 31)` for `tableNames`) and
  `sim.nim:243` (`initRand(int64(config.seed) * 7919 + 17)` for the permutation). The shock stream
  is a third, `sim.nim:249` (`initRand(int64(config.seed) * 104729 + 7)`), which matches
  `design.md:293` exactly.
- What the note says: `design.md:65-66` — the permutation is "drawn from **the same RNG stream as
  the aliases**"; `design.md:302-303` — both are "drawn once at `initSim` from a separate stream"
  (separate, i.e., from the shock stream — which is true).
- Observed: both setup streams are pure functions of `config.seed`, so determinism and
  self-sufficiency are unaffected; `tests/test_sim.nim:323-327` asserts the same seed reproduces
  both the permutation and the aliases.
- Checklist item: none. Non-blocking.

### N11 — `assassinate` amounts are clamped to 6..30 **before** the affordability test, in two places
- Where: `src/cogiavelli/llm.nim:785-786` (parse time, per the note) and again in
  `src/cogiavelli/money.nim:70-71` (inside `validateSpend`, before the
  `if treasury[power] < entry.amount` check at 85-87).
- Observed consequence: a power writing `assassinate 3` is charged 6 if it can afford 6, and a
  power with 4 ducats writing `assassinate 4` has the entry clamped to 6 and then dropped as
  `insufficient`. Both are consistent with `design.md:187-189` ("`amount` is the ducats paid,
  clamped to 6..30 at parse time"); I record it because the clamp happens on the *server* side too,
  which the note attributes to parse time only. `tests/test_money.nim:118-137` pins the clamp.
- Checklist item: none. Non-blocking.

### N12 — `AssassinFaces = 36` is declared but never used by the roll
- Where: `src/cogiavelli/money.nim:17` declares it; the roll is computed as
  `6 * (d1 - 1) + d2` from two `rng.rand(1 .. 6)` draws (`money.nim:101-103`). The only reference
  to the constant is `tests/test_money.nim:134`.
- Observed: the arithmetic is identical to a uniform 1..36 draw, so the constant is documentation.
  `design.md:671` lists `AssassinFaces = 36` among the required constants, so it is present as
  specified. Non-blocking, recorded for completeness.

### N13 — `mapdata.nim` exports more than the note's "Nothing else"
- Where: `src/cogiavelli/mapdata.nim` — beyond the note's list (`design.md:626-630`) it also
  exports `PowerLongNames` (36-37), `PowerPromptNames` (39-40), `StraitOfMessina` (145),
  `CityIndex` (234), `isSea`/`isCoastal`/`isLand`/`isCity` (262-273), `convoyReachable` (299-326),
  `codeLess`/`sortByCode` (328-335), and the 42 area-id constants (44-85).
- What the note says: `design.md:630` — "Procs: `provinceByCode`, `isAdjacent`, `bfsDistance`.
  Nothing else."
- Observed: every extra is a pure helper used by `orders.nim`, `money.nim`, `sim.nim` or the tests.
  Non-blocking.

### N14 — `tests/test_bot.nim` accepts `reason == "conquest"` as well as `"complete"`
- Where: `tests/test_bot.nim:63-64`:
  ```nim
  check(sim.reason == "complete" or sim.reason == "conquest",
    "a scripted table always reaches an end condition, got " & sim.reason)
  ```
- What the note says: `design.md:1270` — "the episode always reaches `reason = "complete"`".
- Checklist item: item 7 names `results.reason == "complete"`. I record this as non-blocking and
  not a "loosened test": `git log --name-status -- tests/` shows all seven test files were **added**
  in the single commit `f6862a3` and none was edited, widened, skipped or deleted during this run,
  so the item-1 half is clean; and `conquest` is a legitimate natural end (`design.md:329`) that a
  scripted table can reach, so the disjunction is broader than the note's wording rather than a
  weakened assertion of it. The judge should decide whether the letter of item 7 is met — see also
  *Could not determine* §1.

### N15 — the endcard drops the `stabs` column and the ledger does not animate
- Where: `client/renderer.js:2494-2500` — the endcard header row is
  `"" / power / cities / ducats / spent / score`; `ledgerHtml` (`renderer.js:2520-2560`) renders a
  static 6×6 matrix.
- What the note says: `design.md:1052-1056` — "rows ranked by score with columns `power`, `cities`,
  `ducats`, `spent`, **`stabs`**, `score`" and a ledger "animating one year per second in a loop".
- Observed: the endcard is inside `#endscreen` and therefore stops at `var(--band)` and is
  dismissed on every seek, as the note requires (see *Traced and consistent*). Only the two
  cosmetic features above are absent. Non-blocking.

### N16 — `feedClass` emits two classes (`feed-end`, `feed-it`) not in the note's appended-CSS list
- Where: `client/renderer.js:2211-2218` maps `end -> "feed-end"` and `season`/`start` ->
  `"feed-it"`; the note's appended-CSS list (`design.md:920-922`) does not mention them.
- Observed: both rules already exist in the inherited babel chrome —
  `/workspace/starters/cogame-babel/client/chrome.css:245-246`. Every other class the mapper emits
  (`feed-broadcast`, `feed-order`, `feed-gift`, `feed-dagger`, `feed-bribe`, `feed-bounce`,
  `feed-cities`, `feed-plague`, `feed-famine`, `feed-winter`) plus the `extraLines` classes
  (`feed-letter`, `feed-pledge`, `feed-illegal`, `feed-dislodge`, `feed-stab`, `feed-notes`,
  `feed-rebel`) is defined in the appended block (`client/chrome.css:620-637`). No emitted class is
  without a rule. Non-blocking.

### N17 — `src/cogiavelli_player.nim` blocks on `receiveMessage()` with no timeout
- Where: `src/cogiavelli_player.nim:52-53`:
  ```nim
  while true:
    let received = socket.receiveMessage()
  ```
  `whisky`'s signature is `proc receiveMessage*(ws: WebSocket, timeout = -1)`
  (`/root/.nimby/pkgs/whisky/src/whisky.nim:73`); `-1` blocks indefinitely.
- Observed mitigations, all in code: the game sends the `final` frame to every player socket
  **before** it writes artifacts (`src/cogiavelli/server.nim:245-248`) and the player breaks out on
  `final` (`cogiavelli_player.nim:69-71`); `receiveMessage` raises on a close frame or a truncated
  read (whisky.nim:86-87) and the raise is caught at `cogiavelli_player.nim:76-77` and exits 0; the
  game then quits after a bounded 20 s grace (`server.nim:260-262`).
- Provenance: byte-for-byte the starter's pattern —
  `/workspace/starters/cogame-babel/src/babel_player.nim:51-52` is the identical `while true` /
  `socket.receiveMessage()`.
- Checklist item: item 5 says "there is no unbounded loop or blocking read". I report the fact
  rather than categorise it: the read is literally unbounded, it is in the *player* container not
  the game, the game side has no unbounded wait (see *Traced and consistent* §Waits), and the
  pattern is inherited verbatim from the named starter. **untested**: whether a game container that
  dies without closing the socket would leave a player pod spinning until the platform kills it.

### N18 — the note's mandated system-prompt wording uses em dashes where the code uses ASCII hyphens
- Where: `src/cogiavelli/llm.nim:616` ("they arrive, always - this is the only promise"),
  `llm.nim:619` ("a roll of two dice - beat the roll"), `llm.nim:630` ("nothing else - no
  analysis"). The note's verbatim block at `design.md:490,494,506` has `—` in all three places.
- Observed: every other line of the required block is character-for-character the note's text, and
  the dynamic first three lines are produced by `otherPowersText` (`llm.nim:587-594`), which for
  Venice yields exactly `MILAN, FLORENCE, the PAPACY, NAPLES and the TURK`
  (`PowerPromptNames`, `mapdata.nim:39-40`). Non-blocking.

### N19 — `client/player.html` opens the player websocket when the page is loaded
- Where: `client/player.html:51,59-60` — `attachLive({… wsPath: "/player?slot=" + … })`.
- What the note says: `design.md:793-794` — "Both `/client/` routes serve real pages and neither
  opens the player socket (lantern 0.1.1)".
- Observed: the *route handler* does not open a socket — it serves a file
  (`src/cogiavelli/server.nim:522`, `htmlHandler("player.html")`). The served page connects to
  `/player` with `slot`/`token` from the query string, and the upgrade handler rejects a bad token
  with 401 (`server.nim:429-435`). This is babel's page unchanged apart from the wordmark, the
  renderer alias and the `relayout()` insertion (`diff` against
  `/workspace/starters/cogame-babel/client/player.html` shows only those hunks). Non-blocking.

### N20 — the note's `test_map` description says "the land graph is connected"; the test asserts it is in two components
- Where: `tests/test_map.nim:88-113` asserts exactly two components — the mainland at 34 provinces
  and Sicily at 2 — with a comment explaining that `MES`/`PAL` touch nothing but each other.
- What the note says: `design.md:1196` — "the land graph is connected and the fleet graph is
  connected".
- Observed: the test is right and the note's sentence is wrong for the army graph, because the same
  note requires `CAL–MES` to be the one fleet-only edge and "an army reaches Sicily (`MES`, `PAL`)
  only by convoy" (`design.md:138-139`). The map table (`src/cogiavelli/mapdata.nim:126-127`) gives
  `MES` the single land neighbour `PAL` and `PAL` the single land neighbour `MES`, so a connected
  army graph is impossible. Non-blocking; recorded as a note-vs-code divergence resolved in the
  code's favour.

---

## Traced and consistent

### The numbered resolution order (note §The game, steps 1–12 and W1–W5)

- `src/cogiavelli/sim.nim:666-808` — `resolveSeason` runs, in source order and with no branch that
  reorders them: **step 4** payment (670-687, `for power in 0 ..< Powers` → `validateSpend`), **step
  5** assassination (689-708), **step 6** bribes (710-745), **step 7** order repair (747-759),
  **step 8** `adjudicate` (761-770), **step 9** `runRetreats` (771-777), **step 10**
  `updateCities` (779-781), **step 11** plague, Summer only (783-798), **step 12**
  `advanceSeason` (807-808). Steps 1 and 2 are in `beginSeason` (`sim.nim:294-337`), step 3 is
  `applyOrders` (`sim.nim:810-860`).
- **Step 1**, famine: `sim.nim:308-321`, Spring only, 2 distinct land provinces from
  `0 ..< NumLand`, `evFamine` event carrying both codes. Constant `FamineProvinces = 2`
  (`money.nim:19`). See N6 for the draw count.
- **Step 2**, press: `sim.nim:322-333`. `pending[seat] = not eliminated and not pressBlocked`
  (326-327) — a power paralysed last season writes nothing; `pressBlocked` is cleared immediately
  after (328-329) so the silence lasts exactly one window. Skipped entirely when
  `config.press == false` (334-337). Letters **to** a silenced power are still delivered
  (`llm.nim:526-542` reads `sim.pressLast & sim.press` unconditionally).
- **Step 3**: `applyOrders` records ≤ 24 orders each ≤ 40 runes (`sim.nim:820-825`), ≤ 6 spend
  entries (826-834), and a `builds` list only when `sim.season == seAutumn` (835-841).
- **Step 4**: `money.nim:50-92`. Entries are walked with `for entry in entries.mitems` in the order
  written; `insufficient` (85-87), `notarget` (64-66, 73-75), `illegal` for a bribe on one's own
  unit (82-84), an assassination on oneself (67-69) and a `defend` on someone else's unit (79-81);
  every survivor is debited **before** anything resolves (88) and a `gift` credits the recipient in
  the same step (91-92). Pinned by `tests/test_money.nim:23-68`.
- **Step 5**: `money.nim:94-106`. `d1 = rng.rand(1..6)`, `d2 = rng.rand(1..6)`,
  `roll = 6 * (d1 - 1) + d2` ⇒ uniform 1..36; `success = roll <= entry.amount` with `amount`
  clamped to `AssassinMin = 6` / `AssassinMax = 30` (`money.nim:15-16`). Entries are gathered in
  ascending payer index at `sim.nim:690-694`. Paralysis sets both `paralysed` (this season's
  movement) and `pressBlocked` (next season's window) at `sim.nim:706-708`; treasuries are
  untouched. Simultaneous hits on one target are idempotent (both write `true`).
  `tests/test_money.nim:118-157`.
- **Step 6**: `money.nim:108-153`. `defence[province]` is the sum of *applied* `spDefend` entries
  on that province (113-116); since `validateSpend` rejects a `defend` on a foreign unit
  (`money.nim:79-81`), that sum can only be the owner's, exactly as `design.md:195` requires. A
  bribe takes effect iff `amount >= bribeCost(kind) + defence` with
  `BribeDisbandCost = 9`, `BribeBuyCost = 15` (`money.nim:9-10, 44-48`); the strictly largest
  qualifying amount wins and an exact tie makes all of them `outbid` with no refund (129-149).
  Effects applied at `sim.nim:728-745`: `disbanded` removes the unit, `bought` transfers it in
  place and sets `forcedHold[province]`. `tests/test_money.nim:70-116`.
- **Step 7**: `sim.nim:422-441` + `orders.nim:239-313`. Orders are parsed against the board **after**
  step 6's transfers (`resolveSeason` calls `normaliseOrders` at 753, after the board rebuild at
  714-745); a unit ordered twice keeps the first (`sim.nim:430-432`, reason `notowned`); a paralysed
  power's orders and a bought unit's order become holds (`sim.nim:756-757`); every unordered unit
  gets a hold (`sim.nim:439-441`). `checkLegality` covers each predicate the note names: fleet
  ordered inland (`orders.nim:259-264`, `wrongunit`), army into a sea (269-273, `wrongunit`), army
  across a non-adjacent hop with no possible convoy path (274-277, `nonadjacent`/`noconvoy`),
  support of a non-adjacent destination (283-293, `nonadjacent`), support/convoy naming an empty
  province (279-282, 287-290, 303-306, `notthere`), army ordering a convoy (294-298, `wrongunit`),
  fleet being convoyed (307-310, `wrongunit`), convoying fleet not in a sea (299-302, `wrongunit`).
  Every illegal order becomes a hold and lands in `event.illegal` with a one-word `why`
  (`sim.nim:433-437`, `sim.nim:849-850`); nothing invalidates the rest of the reply.
  `tests/test_adjudicate.nim:209-229`.
- **Step 8**: `src/cogiavelli/adjudicate.nim`. All four strengths present and matching the note's
  definitions: hold (137-148, 0 if the occupier moves away, else 1 + supports-to-hold), attack
  (150-167, 0 on a failed path, **0 if the destination holds a unit of the mover's own power that
  is not vacating** — the self-dislodgement ban at 163-166 — else `1 + supportCount(index,
  occupant.power)`, i.e. supports from the occupant's own power are excluded), defend (169-170),
  prevent (172-178, 0 on a failed path or a lost head-to-head). `resolveMove` (180-201) requires
  the attack to exceed every rival's prevent strength and then the defend strength (head-to-head)
  or the hold strength. Supports are cut by any move into the supporter's province by a **different
  power** with a usable path, except a move originating in the province the support points into
  (`supportGiven`, 116-135), and a dislodged supporter's support is cut unconditionally (133-135).
  Convoy paths are BFS over seas whose fleets issued matching, undislodged convoy orders
  (`convoyPathOk`, 43-74). Szykman-voided moves also stop cutting support, because `pathOk` returns
  false for them (76-80). Standoffs = provinces with ≥ 2 bounced moves and nothing entering
  (368-377). All 19 note cases exist as one-assertion blocks in
  `tests/test_adjudicate.nim:59-251`, including the beleaguered garrison (130-137), the
  circular-movement ring and its external disruption (139-150), the Szykman paradox (192-200) and
  the two head-to-head cases (231-240).
- **Step 9**: `sim.nim:486-550`. Successful moves are applied first so "empty after movement" is
  true (494-515); the dislodged are sorted by province code (519-520); options are filtered to
  adjacency on the unit's own graph, not occupied, not a standoff province, not the attacker's
  origin (523-531); ties break by ascending code via `options.sortByCode()` (532) and then by
  smallest BFS distance to the nearest owned city (534-541); nothing legal ⇒ `Retreat(to: -1)`
  = disband (542-543); a taken destination is marked `occupied` so the next dislodged unit
  re-picks (546). Recorded inside the `battle` event (`sim.nim:773`). Asserted end to end by
  `tests/test_sim.nim:335-365` (never to the attacker's origin, never to an occupied province,
  takes the destination nearest home).
- **Step 10**: `sim.nim:460-484` — every city with a unit standing in it changes hands
  immediately, every season; unoccupied cities keep their owner; the `cities` event carries the
  owner table, per-power counts and the gained/lost lists; `conquestCheck` runs at the end (484).
  `tests/test_sim.nim:91-109` asserts flips happen outside Autumn.
- **Step 11**: `sim.nim:783-798` — Summer only, one uniform draw from the 24 cities
  (`Cities[sim.shockRng.rand(TotalCities - 1)]`), every unit in the province destroyed with no
  retreat, the province retained in `sim.plagueCity` so W3 excludes it from income
  (`sim.nim:615-617`).
- **Step 12 / Winter**: `sim.nim:644-664` and `sim.nim:606-642`. W1 `runRebellions`
  (`money.nim:166-185`: ascending power index, then ascending province code, non-home owned city
  with no unit, `rng.rand(1..6)`, reverts on `RebellionFace = 1`, **every** roll recorded); W2
  `strikeFamine` (`money.nim:187-196`); W3 `collectIncome` (`money.nim:198-212`:
  `CityIncome = 3` per owned city excluding `barren` = this year's famine provinces + the plague
  city, plus one `rng.rand(0 .. IncomeDrawMax)` draw per power in ascending index); W4 `payUpkeep`
  (`money.nim:214-250`: `UpkeepPerUnit = 1`, disbands furthest-from-nearest-owned-city first with
  ties by ascending code, then pays for every survivor); W5 `runBuilds` (`money.nim:252-295`:
  `BuildCost = 3`, vacant city the power owns — any owned city — fleet only if `isCoastal`,
  duplicates skipped as `occupied`). All five ride in one `winter` event carrying every roll,
  casualty, ducat and build (`sim.nim:608-635`). Elimination at zero cities and zero units after W5
  (`sim.nim:636-642`). `tests/test_money.nim:159-233`.
- **Constants**, all present and equal to the note (`design.md:670-672`, `design.md:676-680`):
  `money.nim:8-20` — `BribeDisbandCost 9`, `BribeBuyCost 15`, `BuildCost 3`, `UpkeepPerUnit 1`,
  `CityIncome 3`, `IncomeDrawMax 3`, `AssassinMin 6`, `AssassinMax 30`, `AssassinFaces 36`,
  `RebellionFace 1`, `FamineProvinces 2`, `StartTreasury 12`; `sim.nim:17-42` — `Seats 6`,
  `Powers 6`, `VictoryCities 12`, `MinYears 1`, `MaxYears 10`, `StartYear 1499`,
  `SeasonsPerYear 3`, `PacingBudgetMs 60_000`, `MaxBroadcastLen 400`, `MaxLetterLen 400`,
  `MaxLetters 5`, `MaxPledges 4`, `MaxNotesLen 800`, `MaxOrderLen 40`, `MaxSpendEntries 6`,
  `MaxBuilds 6`, plus babel's `CogNames` verbatim; `mapdata.nim:226` `TotalCities 24`.
  `sim.nim:258` seeds every power with `StartTreasury`.
- **The map**: I transcribed all 36 rows of `src/cogiavelli/mapdata.nim:94-133` against the note's
  table (`design.md:88-123`) — code, display name, kind, city flag, home power and both the land
  and sea columns match on every row, as do the six sea rows (`mapdata.nim:135-142` vs
  `design.md:125-128`) and all 18 start units (`mapdata.nim:246-253` vs `design.md:146-147`).
  Twenty-four cities, eighteen home + six neutral (`TUR GEN TRI FER BOL MES`), verified by count
  and by `tests/test_map.nim:10-47`. The two graphs are generated from the one table
  (`mapdata.nim:178-217`), with coast-hops gated on `shareASea` (201-208) and the single
  fleet-only `CAL–MES` edge (145, 209-210).
- **Scoring**: `sim.nim:158-169` — conquest returns 1.0/0.0, otherwise
  `min((cities + min(ducats, 24) / 24) / 24, 1.0)`, exactly `design.md:314`. `resultsJson`
  (`sim.nim:864-899`) emits all twelve keys the note lists and `""` for `reason` while the sim is
  running. `tests/test_score.nim` covers the neutral-dilution case, 24 vs 48 ducats, conquest at
  exactly 12, an eliminated power's treasury-only term, and the first-Spring deadline
  (`3/24 + (12/24)/24`).
- **End reasons**: exactly three strings are ever written — `"conquest"` (`sim.nim:458`),
  `"complete"` (`sim.nim:660`), `"deadline"` (`sim.nim:356`).

### The decision path (checklist items 8 and the simultaneous-decision addendum)

- `src/cogiavelli/llm.nim:892-944` — `decideAll` is a faithful port of bullwhip's
  (`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:425-478`), including the
  `batch.post(..., $index)` tagging and the positional `responses[position]` read. Curly's contract
  makes the positional read correct: "The return value seq is in the same order as the request
  batch" (`/root/.nimby/pkgs/curly/src/curly.nim:718`).
- **ONE batch per phase**: `var batch: RequestBatch` is built over all still-open seats and handed
  to a single `client.curl.makeRequests(batch, client.timeoutSeconds)` (llm.nim:915-925). There is
  exactly one `makeRequests` call in the whole tree (`grep` over `src/` returns `llm.nim:925` and
  nothing else) and no per-seat `curl.post`. Driven from `server.nim:342`, once per loop iteration.
- **Retry once**: `for attempt in 0 .. 1` (llm.nim:912) — at most two batches per phase; the retry
  batch appends `InvalidHint` = "Your previous reply was invalid. Respond with ONLY the requested
  JSON object." (llm.nim:33-34, 921-922), which is the note's wording verbatim
  (`design.md:597-598`).
- **Tolerant parse**: `extractJsonObject` takes the first `{` to the last `}` (llm.nim:698-709), so
  fences and surrounding prose are accepted — asserted by `tests/test_bot.nim:167-173`. A reply is
  invalid **only** if it is not a JSON object or the phase's required key is missing/wrong-kind
  (`parsePress` llm.nim:715-722; `parseOrdersReply` llm.nim:805-809) — asserted by
  `tests/test_bot.nim:175-187`. Illegal *contents* are repaired, never rejected
  (`tests/test_bot.nim:189-212`).
- **Scripted fallback, recorded**: `llm.nim:941-944` logs
  `"cogiavelli: seat N falling back to scripted decision"` (the note's string,
  `design.md:599`) and calls `scriptedAction(..., skCondottiere, phase)`, whose first statement is
  `result.scripted = true` (llm.nim:417). That flag reaches the event via
  `event.scripted = scripted` in `applyPress`/`applyOrders` (`sim.nim:376`, `sim.nim:846`) and is
  serialised as `"scripted": true` in `eventToJson` (`sim.nim:1147-1148`), so phase 60 can count
  it. The server's belt-and-braces `except CogiavelliError` path also passes `true`
  (`server.nim:358-367`).
- **No credentials ⇒ immediate scripted, no network**: `newLlmClient` sets `disabled = true` when
  neither Bedrock nor an API key is present (llm.nim:142-145), and `decideAll` short-circuits every
  seat at llm.nim:906-909 before any batch is built. `tests/test_bot.nim:132-146` proves it by
  handing `decideAll` a client with a nil `Curly` handle — any network call would crash — and
  asserting six scripted decisions come back.
- **401/403 disables the client for the episode** (llm.nim:866-874); **429 and Bedrock
  model-access denial rotate the candidate** via `tryNextBedrockModel` (llm.nim:103-111, 868-878),
  which is babel's proc unchanged.
- **Two named baselines**: `parseScriptKind` accepts `1`/`true`/`yes`/`condottiere` →
  `skCondottiere` and `banker`/`miser` → `skBanker` (llm.nim:68-74), exactly `design.md:561-562`.
  Both are silent in a press phase (`llm.nim:418-419`).

### Every wait and its bound (checklist item 5)

I enumerated every blocking construct in `src/`:

| where | construct | bound |
|---|---|---|
| `server.nim:274-280` | player-connect wait, `sleep(200)` poll | `gameStart + config.playerConnectTimeoutSeconds` (default 180) |
| `server.nim:309` | the season loop `while true` | breaks on `sim.done` (321-326 deadline, 332-337 no pending seat) and terminates naturally via `settle("complete")` at `sim.nim:660` after ≤ `MaxYears = 10` years |
| `llm.nim:925` | `makeRequests` | `client.timeoutSeconds` = `config.llmTimeoutSeconds`, default 45, schema-capped 5..300 |
| `llm.nim:912` | retry loop | exactly 2 iterations ⇒ ≤ 90 s per phase |
| `server.nim:370-374` | pacing `sleep(turnDelayMs)` | `sampleEpisode` caps it at `PacingBudgetMs div (years*3*3)` (`sim.nim:195-206`), idempotent via `sampled` |
| `server.nim:250` | `sleep(500)` before artifact writes | fixed |
| `server.nim:260` | shutdown grace | `ShutdownGraceSeconds = 20.0` (server.nim:42) |
| `server.nim:181` | artifact `curl.post` | explicit `60` |
| `llm.nim:84` → `readCogameUri` | one-shot secret fetch | curly's `get` default `timeout = 60` (`/root/.nimby/pkgs/curly/src/curly.nim:642-648`) |
| `cogiavelli_player.nim:53` | `receiveMessage()` | **unbounded** — see N17 |

- **The 60 % budget**: `PlayBudgetFraction* = 0.6` (`server.nim:39`);
  `playDeadline = gameStart + timeoutSeconds * PlayBudgetFraction` (`server.nim:301-303`), with
  `timeoutSeconds` from `COWORLD_TIMEOUT_SECONDS` when set and otherwise
  `config.episodeTimeoutSeconds` (default 1200, `types.nim:236`) ⇒ **720 s of 1200**. The check is
  the first thing inside the loop's `withLock`, i.e. **before every batch**
  (`server.nim:321-326`), and past it `endEarly()` ⇒ `reason = "deadline"`. A season transition can
  only happen inside the `applyOrders` that closes a phase (`sim.nim:859-860` → `resolveSeason` →
  `advanceSeason`), which is always downstream of a batch, so the pre-batch check is also the
  pre-transition check — the comment at `server.nim:318-320` states this and the control flow
  bears it out (**inferred** from tracing, not from a test).
- **Final frames before artifacts**: `server.nim:245-248` sends `final` to every player socket and
  broadcasts, and only then (after the lock is released) writes results and the replay
  (`server.nim:250-255`) — babel's `finishEpisode` ordering kept.
- **Ping → Pong**: `server.nim:478-480` answers `Ping` frames on any socket, so the certifier's
  `/global` ping is answered.
- **`initSim` seat guard**: raises `CogiavelliError` when `config.players.len != 6`
  (`sim.nim:234-236`).

### String truncation on rune boundaries (checklist item 9)

- `cleanText` (`sim.nim:100-106`) is the only truncator: `runeLen` gate, `runeSubStr(0, limit - 1)`
  and a `…` marker, so the result is always ≤ `limit` runes and always valid UTF-8.
- Applied to every string that reaches an event: `broadcast` (`sim.nim:377`, cap 400),
  `letters[].text` (`sim.nim:395`, cap 400), `notes` (`sim.nim:411`, `sim.nim:853`, cap 800),
  order strings (`sim.nim:824` and `llm.nim:815`, cap 40), `spend[].targetUnit` (`sim.nim:832`,
  cap 24), `builds[]` (`sim.nim:840`, cap 24), `illegal[].raw` (`sim.nim:434`, cap 40); at parse
  time also `letters[].to` / `pledges[].to` / `spend[].target` (cap 24, `llm.nim:730, 746, 787`)
  and `pledges[].province` (cap 8, `llm.nim:749`). The player prompt is capped at
  `MaxPromptLen = 4000` runes through the same proc (`server.nim:34`, `server.nim:492-493`).
  Every cap matches the note's reply-schema table (`design.md:533-551`).
- Array caps: 5 letters + one-per-power dedup (`sim.nim:384-397`), 4 pledges (`sim.nim:399`),
  24 orders (`sim.nim:822`), 6 spend entries (`sim.nim:827`), 6 builds (`sim.nim:838`) — all
  truncate from the end, never reject.
- Captured error strings are byte-sliced (`llm.nim:705-706`, `867`, `876`, `881`, `890`) but they
  are only ever `echo`ed (`llm.nim:937-938`, `server.nim:359-360`, `server.nim:507`) — I traced
  every use and none is written into a `GameEvent`, so no byte-sliced string can reach the replay.
- Test: `tests/test_sim.nim:193-217` feeds `900 × "é—😀"` into broadcast, a letter and notes and
  asserts `runeLen == cap` and `validateUtf8(...) == -1` on each, plus on the whole frame;
  `tests/test_viewer.nim:80-113` asserts the whole replay payload is strict UTF-8 and re-parses
  after a multi-byte press fixture, and that every re-derived frame is UTF-8.

### The replay writer (note §Replay payload)

- `src/cogiavelli/server.nim:187-213` emits `protocol` = `cogiavelli.replay.v1`, `names`
  (aliases), `policyNames` (`config.players[i].name`, `server.nim:79-84`), `powers` (per seat),
  `config` = `{years, seed, press, sampled, victoryCities, totalCities, map: "italy1499"}`,
  `events` and `results` — every field the note lists at `design.md:766-770`, plus `totalCities`.
- **13 event kinds**, all defined (`types.nim:153-166`) and all serialised/deserialised with a
  dedicated branch (`sim.nim:1151-1306` / `1322-1440`): `start season famine press orders spend
  assassin bribe battle cities plague winter end`. `tests/test_sim.nim:280-299` asserts the log
  covers every kind and that `eventFromJson(eventToJson(e)) == e` for each.
- **Self-sufficiency**: the seed re-derives the permutation, the aliases and the whole shock stream
  (`sim.nim:240-249`); each `orders` event carries the *pre-validation* `spend` sheet and the
  `builds` list (`sim.nim:851-852`, serialised at `sim.nim:1195-1202`), which is what lets
  `replayMatch` re-run `validateSpend` and reproduce the ledger; each `press` event carries every
  letter including the private ones and every pledge (`sim.nim:1169-1184`); `battle` carries every
  order result, dislodgement, retreat, standoff and stab; `winter` carries every roll, kill,
  income, draw, upkeep, disband and build; `end` carries cities, treasury and the conqueror.
- **Strict UTF-8**: asserted at `tests/test_viewer.nim:101-104` on a payload built from a
  deliberately multi-byte press fixture, and again by `docker_smoke.sh` in CI (run 32725516744,
  `smoke OK: seats=6 results=435B replay=22340B reason=complete`).

### The viewer's re-derivation (checklist items 3, 13, 14)

- **Same sim in the browser**: `replay-viewer/cogiavelli_replay.nim:9-50` imports `cogiavelli/sim`
  and calls `replayMatch(config, events)` → `tableStateJson()` per frame — the same adjudicator,
  the same money rules, the same seeded stream. Exports `cog_load_replay`, `cog_payload_ptr`,
  `cog_payload_len`, `cog_error_ptr`, `cog_error_len` (22-72) and keeps babel's
  `emscripten_exit_with_live_runtime()` epilogue (74-83).
- **MODULARIZE/EXPORT_NAME handshake, one starter**: `replay-viewer/config.nims` is babel's file
  with three renames only (`diff` against the starter shows exactly the `-o`, `EXPORT_NAME` and
  `EXPORTED_FUNCTIONS` lines): `-s MODULARIZE=1`, `-s EXPORT_NAME=CogiavelliReplayModule`,
  `EXPORTED_FUNCTIONS=_main,_malloc,_free,_cog_load_replay,_cog_payload_ptr,_cog_payload_len,_cog_error_ptr,_cog_error_len`.
  `replay-viewer/static_replay.js:149` calls the **factory** `CogiavelliReplayModule()` and the
  handshake at 91-108 is `_malloc` → `HEAPU8.set` → `_cog_load_replay` → `_cog_payload_ptr` /
  `_cog_payload_len`. There is **no** `onRuntimeInitialized` anywhere in the tree (`grep` returns
  nothing). This is the cogame-lantern failure mode, and it is not present.
- **Both markers, from the shell's own code**: `data-replay-loaded="true"` is set at the end of
  `attachReplay`'s `makeRenderer` callback, `client/renderer.js:1393` (babel's line 1309 kept
  verbatim); `data-replay-error` is set by `fail()` at `replay-viewer/static_replay.js:56` and
  removed on a successful retry at 107 and 145. `static_replay.js:120-133` is the one substantive
  addition over babel: `tell("ready")` is now posted only *after* `data-replay-loaded` appears,
  with a 600-frame bail-out, instead of on bare rAF timing.
- **Bundle, never a pod**: `coworld_manifest_template.json:15-17` declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}`. `tools/build_replay_viewer.sh` exists,
  is committed `-rwxr-xr-x`, and is asserted present-and-executable by `ci.yml:225-236`; it
  `mkdir -p`s the output parent (line 21, the ecos fix), builds the wasm locally or in the pinned
  `Dockerfile.replay-viewer`, copies `cogiavelli_replay.{js,wasm}`, `index.html`,
  `static_replay.js`, `client/renderer.js`, `client/chrome.css` and the ten data assets including
  `italy1499.json`, then re-asserts `index.html`, the map asset and `data-replay` in
  `static_replay.js` (62-64). The only `/client/replay` string in the manifest is inside the
  `global` protocol *description* (`coworld_manifest_template.json:254`); no viewer path is
  declared. The bundle fetches only `?replay=<url>` and its own relative assets.
- **Chrome provenance.** Babel ships no `chrome_common.js` and no `replay_broadcast.html`
  (confirmed: `/workspace/starters/cogame-babel/client` = `chrome.css global.html player.html
  renderer.js replay.html fixtures/`), so the note maps the rule onto `renderer.js` + `chrome.css`
  + `replay.html` (`design.md:888-896`). Diffed against the starter:
  * `client/chrome.css` — **0 removed lines, 234 added**, all after the starter's last line, under
    the banner at `client/chrome.css:444-450`. Contains exactly what the note lists:
    `:root { --band: 96px; --hudscale: 1; }` (452), `.seat5 { --tc: var(--amber); }` (455),
    `.plate-power/.plate-cities/.plate-ducats/.plate-stab/.plate-frozen/.plate-out` (457-495),
    the `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` override (498), `#ducatbar` with
    `font-size: calc(11px * var(--hudscale))` (511-518), `.beat-label` (573-591) plus a rule for
    each of the twelve beat kinds (593-619), all seventeen feed colours (621-638),
    `#loading { bottom: var(--band); top: 0; }` (640), and the `640px` / `420px` queries
    (662-677).
  * `client/renderer.js` — 1271 added lines and **2 modified**, both at named hook points: line
    853-854 appends a per-kind feed class to the existing class string, and line 1369-1371 routes
    playback pacing through `CogiavelliChrome.stepMs`. Nothing is deleted. `describeEvent`
    (762-800) and the canvas `draw` (218-229) are *extended* with new cases/early-outs, exactly as
    `design.md:899-902` allows. The appended block starts at the `// ---------- Cogiavelli
    ----------` banner (1405) and ends with `window.CogiavelliRenderer = window.BabelRenderer;`
    (2587), so the renamed global is an alias of the starter's, not a re-implementation.
  * `client/replay.html` — **7 lines changed, 21 added, 0 elements removed**: the `<title>`, the
    wordmark inner text, `BabelRenderer` → `CogiavelliRenderer` (2 call sites), the `relayout()`
    bootstrap replacing the bare `fit()` wiring, and one appended `<div id="ducatbar">` between
    `#scorebug` and `#board-wrap` (line 20). `replay-viewer/index.html` gets the identical
    treatment plus the `cogiavelli_replay.js` script tag. `tests/test_viewer.nim:164-177` asserts
    all twenty starter ids survive, that `#ducatbar` was added and `#viewpanel` was not.
- **Transport rules, each checked in the page**:
  (a) `relayout()` measures `#transport`'s `offsetHeight` and sets `--band` and `--hudscale` on
  `document.documentElement` (`client/replay.html:49-57`, `replay-viewer/index.html:51-59`) and
  calls `fit()` from inside itself, so the canvas and the custom properties cannot disagree; it is
  bound to `load`, `resize` and — via `bindFeedToggle`'s resize dispatch — the feed-toggle path.
  (b) `#transport` is the last child of `#stage` in normal flex flow
  (`/workspace/starters/cogame-babel/client/chrome.css:128-136`, unmodified); the only
  absolutely-positioned overlays (`#lightpool`, `#grain`, `#endscreen`) live inside `#board-wrap`,
  which ends where the band begins; `#loading` is pinned with `bottom: var(--band)`
  (`client/chrome.css:640`).
  (c) `#endscreen` is `position: absolute; inset: 0` inside `#board-wrap` (starter chrome.css:372-380),
  shown with the class its own rule uses — `#endscreen.show { display: flex; }` (starter:381) and
  `container.classList.toggle("show", !!show)` (`client/renderer.js:1020`) — and **every** index
  change calls `updateEndscreen(..., index >= events.length && events.length > 0, ...)`
  (`client/renderer.js:1354-1355`), so a scrub click, a beat button, back/forward and the keyboard
  all take it down. Babel's `setIndex`, verbatim.
  (d) Beats are real `<button type="button" class="beat-marker <kind>">` elements with a `title`,
  an `aria-label`, a `.beat-label` tooltip and an `onclick` that `evt.stopPropagation()`s and calls
  `onSeek(i + 1)` (`client/renderer.js:2445-2457`); `markDucatBeat` (2459-2471) emits them for the
  eleven kinds in `BEAT_KINDS` (2333-2336) plus a derived `stab` beat per stab inside a `battle`,
  and the appended CSS has a rule for all twelve. The container keeps babel's drag-to-seek
  pointer handlers and `scrub-head`/`scrub-fill` update (`client/renderer.js:1264-1292`).
  `#viewpanel` is absent from the whole tree.
- **360 px legibility**: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`
  (`client/chrome.css:498`, asserted verbatim by `tests/test_viewer.nim:181-182`); under 640 px
  `.plate-ducats, .plate-cities { display: none; }` (`chrome.css:663`) hides the labels while
  `.plate-power`, `.plate-name` and `.plate-score` (the city count) stay; `#ducatbar` shrinks to
  counts and coin figures (665-671); under 420 px `#scorebug` goes to two columns (675-677).
  Below 640 px the canvas draws the action box instead of the whole map
  (`client/renderer.js:1526-1560`, `boardBox`).

### The manifest (checklist items 6, 10, 12)

- `num_agents: 6` in `standard` (`coworld_manifest_template.json:376`), in `gunboat` (408) and in
  the certification fixture (438). `SMOKE_SEATS` defaults to `6` (`tools/ci/docker_smoke.sh:54`)
  and the script enforces all four invariants with `SEAT-COUNT FAIL:`-prefixed exits
  (docker_smoke.sh:106-149). CI run 32725516744's docker-smoke log contains **zero** occurrences of
  `SEAT-COUNT FAIL` and prints `game=cogiavelli seats=6 … "num_agents": 6`.
- `"replay_viewer": {"bundle": "static-replay-viewer"}` (15-17). `episode_timeout_minutes: 20` (12).
  Seven tags (3-11). `game.name = "cogiavelli"` (14); `runnable.type = "game"`, image
  `{{COGIAVELLI_IMAGE}}` matching the compose service `cogiavelli` (`compose.yaml:2-3`), run
  `["/bin/cogiavelli"]`, and `env.ANTHROPIC_API_KEY_URI =
  "secret://coworld/cogiavelli/anthropic_api_key"` (26-28).
- `config_schema`: `additionalProperties: false`, `required ["tokens","players"]`; the only two
  array properties, `tokens` (40-49) and `players` (50-68), both carry `minItems: 6, maxItems: 6`;
  `num_agents` is `integer, minimum 6, maximum 6` (69-74); every other property matches the note's
  ranges and defaults.
- `results_schema`: `additionalProperties: false`, all twelve keys required, every one of the eight
  arrays `minItems: 6, maxItems: 6`, `scores` bounded `0..1` (129-245).
- `game.protocols` carries **both** `player` (248-251) and `global` (252-255), each as
  `{"type": "text", "value": …}`.
- `game.docs` carries `readme` as `{"type":"text","value":…}` (258-261) and `pages` as two entries
  each with `id`, `title` and `content: {"type":"text","value":…}` (262-279) — `rules.md` with the
  full numbered order and `map.md` with the 42 areas.
- Three player runnables (282-349) all running `/bin/cogiavelli-player` from
  `{{COGIAVELLI_IMAGE}}`, and all three occupy at least one certification slot (445-464:
  `cogiavelli-player` ×3, `cogiavelli-condottiere` ×2, `cogiavelli-banker` ×1).
- `tools/ci/policies.json`: four entries — `cogiavelli-medici` and `cogiavelli-borgia` are
  `PLAYER_PROMPT` champions, `cogiavelli-condottiere` and `cogiavelli-banker` are
  `PLAYER_SCRIPTED=<name>` fillers. Champion **#2** (`cogiavelli-borgia`, the second
  `PLAYER_PROMPT` entry) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`
  (policies.json:17). All four `env` blocks carry `"USE_BEDROCK": "true"` (6, 14, 23, 31).
- Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows,
  `docker_smoke.sh` and `policies.json` returns **no matches** (exit 1), so the gate exits 0.
- `coworld-release.yml` runs, in order, `coworld build` (153-165) → `coworld certify` (166-205) →
  **Upload the policies** (206-303) → `coworld upload-coworld` (304-341) → `coworld secret put`
  (342-363), with the header comment stating the same ordering constraints. All three workflows are
  present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both `0755`.

### The tests, against the note §Tests

| note §Tests | file | verdict |
|---|---|---|
| `test_map` — 42/36/6, 24 cities, 18+6 homes/neutrals, both graphs symmetric, no army↔sea, no fleet↔inland, coast-hops iff shared sea, `BAR–CAL` is not one, `CAL–MES` fleet-only, fleet graph connected, 18 legal start units, no-split-coast on PIS/ROM/CAL/MES/AVL, `bfsDistance` finite to a city | `tests/test_map.nim:10-180` | all present; "land graph connected" is asserted as two components instead — see N20 |
| `test_adjudicate` — 19 cases, one assertion each | `tests/test_adjudicate.nim:59-251` | all 19 blocks present and numbered to match |
| `test_money` | `tests/test_money.nim:23-254` | payment order, binding gift, illegal targets, 9-exact/1-defence threshold, buy transfer, equal-bribes-cancel + strictly-larger-wins, clamp 6..30 and `roll <= amount`, a ten-roll fixed-seed table, income minus famine/plague plus draw, upkeep furthest-first, rebellion only on a d6 of 1 on an empty non-home owned city, build cost/vacancy/coastal, and seed reproducibility |
| `test_sim` | `tests/test_sim.nim:56-365` | season sequencing (`press → orders` ×3, Winter takes no decision), gunboat skips press, ownership flips outside Autumn, conquest at 12 and last-power-standing, `endEarly` ⇒ deadline, results shape and score bounds, rune-safe caps with an emoji fixture, array truncation, **policy names never reach `systemPrompt`/`pressPrompt`/`ordersPrompt`** (268-278), 13-kind event round-trip, `frames.len == events.len + 1` and final-frame equality, `replayMatch` raises on an altered draw, seed determinism, retreat rules |
| `test_bot` — legality/affordability | `tests/test_bot.nim:100-159` | 8 seeds × `condottiere`, 8 × `banker`, a mixed table, and 5-banker-vs-1-condottiere; every `orders` event has an empty `illegal` list, every unit ordered once, no self-standoff, `spend ≤ 6` and affordable at write time, builds land in a city (coastal for a fleet), no treasury negative, and the wall-beating assertion. Reply parsing: fenced, prose-wrapped, missing key, oversize order, non-integer amount, unknown action, no-object-at-all |
| `test_score` | `tests/test_score.nim:30-89` | formula, 24-vs-48 ducats, conquest 1.0/0.0, eliminated power, first-Spring deadline, `[0,1]` for 0..24 cities |
| `test_viewer` — strict UTF-8 | `tests/test_viewer.nim:58-203` | frame key list, strict-UTF-8 payload + re-parse + every re-derived frame, the naming guard, chrome provenance, chrome CSS, and the map asset |

### CI (checklist items 1, 13)

- `gh run list -R Metta-AI/cogame-cogiavelli --branch main -w ci.yml` →
  **run id 32725516744, headSha `f6862a31255c61d448b37da0d39a44db211ed179`, conclusion
  `success`, status `completed`.**
- Per-job/per-step conclusions from `gh run view 32725516744 --json jobs`: `test` success (every
  `tests/*.nim` in debug and release, `ci.yml:104-150`); `docker-smoke` success, step
  `Raw-Docker episode smoke` success; `wasm-viewer` success **including the step
  `Load the bundle in a real browser`** — no `continue-on-error` anywhere in `ci.yml`, and the job
  declares `needs: docker-smoke` (`ci.yml:212`).
- The viewer smoke's own stdout line from that run:
  `{"loaded":true,"ms":300,"clock":"SPRING 1499 · ORDERS · FLORENCE","scorebug":"FLORENCE Sprocket 3 CITIES 3 units · 12đ …","feed_lines":67}`
  followed by `soak: 10s of playback kept advancing`. It ran
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90 --soak 10`
  against the artefact `docker-smoke` produced (`sha256` of the uploaded and downloaded artifact
  match). `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` returns 0).
- docker-smoke stdout: `episode end reason: complete` /
  `smoke OK: seats=6 results=435B replay=22340B reason=complete`. Full-log grep for
  `SEAT-COUNT FAIL` over all 4093 lines returns **0**.
- "No test loosened": `git log --oneline --name-status -- tests/` shows one commit, `f6862a3`, with
  seven `A` (added) entries and no `M`, `D` or `R`. Nothing was disabled, skipped, widened or
  removed during this run.

### Both name spaces (checklist item 4)

- **In game, anonymous.** Prompts address `PowerNames` only (`llm.nim:596-600`, `llm.nim:640-648`);
  `tableNames` draws a cog alias per seat from babel's `CogNames` pool (`sim.nim:39-42`,
  `sim.nim:183-193`); the player websocket's `welcome` carries `power` and the **alias**, never the
  policy name (`server.nim:442-450`); the redacted `state` frame likewise (`server.nim:135-161`);
  the `final` frame carries `aliasNames`, not `results["names"]` (`server.nim:232-244`).
  `tests/test_sim.nim:268-278` scans all three prompt builders for all six
  `config.players[i].name` values across all six seats.
- **Spectator-side, real.** The replay carries `names` (aliases), `policyNames` and `powers`
  (`server.nim:188-200`); the `/global` snapshot adds `policyNames` (`server.nim:96`);
  `resultsJson` attributes by `sim.config.players[seat].name` (`sim.nim:878`). The viewer's
  `makeNameMap` (`client/renderer.js:701-728`) displays the **policy** name for a seat whose policy
  is not a baseline filler and falls back to the alias otherwise, and `nameMap.text()` rewrites any
  alias occurring inside recorded free text.

---

## Could not determine

1. **Item 7's second sentence — "The baseline's parameters were tuned with a grid harness, not
   guessed."** I found no grid harness, sweep script, tuning log or fitted-parameter record
   anywhere in the tree: `tools/` holds only `build_replay_viewer.sh` and `ci/`
   (`docker_smoke.sh`, `policies.json`, `viewer_smoke.mjs`); `scripts/` holds only the two art
   scripts; `grep -rni "grid harness\|tuning\|tuned"` over `docs/plans/*.md`, `tests/` and `tools/`
   returns nothing, and the design note never uses the word. The baselines' magic numbers
   (`treasury >= 12` and `>= 20` for the condottiere's bribes, `llm.nim:299,321`; `defend` of 4 at
   `treasury >= 15` and builds at `>= 30` for the banker, `llm.nim:396-404`; the vacate penalty of
   1 / 2-in-Autumn, `llm.nim:206`) are stated as constants in both the note (`design.md:577-590`)
   and the code, with no derivation shown. What is present is an *outcome* assertion —
   `tests/test_bot.nim:120-130` requires the condottiere to end with strictly more cities than each
   of five bankers over a 3-year gunboat episode at seed 5. **What would settle it:** a committed
   sweep script or a recorded grid result in the repo or the run directory, or a statement in
   `runs/2026-08-24-cogiavelli/log.md` naming the harness that produced those constants.
   (I did not read `log.md`; my brief scoped me to the repo and the design note.)
2. **Whether the per-event frames the viewer scrubs to are the intended per-tick states.**
   *Observed*: `replayMatch` pushes one frame per **recorded** event (`sim.nim:1501-1502`), but the
   `applyOrders` that closes a phase runs the entire resolution cascade in one call
   (`sim.nim:859-860` → `resolveSeason` → `advanceSeason` → `beginSeason`), so the frames attached
   to that season's `spend`, `assassin`, `bribe`, `battle`, `cities`, `plague` and `season` events
   are all the *same* post-cascade state (the `else: discard` branch at `sim.nim:1465-1466` mutates
   nothing). *Inferred*: scrubbing to the `battle` beat therefore shows the board as it stood after
   retreats, plague and the season advance, while the feed line and the clock (which read the event
   itself via `setBeat`, `renderer.js:1346-1349`) describe the battle. Babel's `replayMatch` has
   the same shape, and the CI viewer smoke's `--soak 10` passed with the clock/scorebug advancing,
   so nothing hangs or blanks. **untested** — what would settle it: a screenshot or readout diff
   across two adjacent intra-resolution beats, or a test asserting that the frame at a `cities`
   event differs from the frame at the following `season` event.
3. **`readCogameUri`'s behaviour when `ANTHROPIC_API_KEY_URI` points at a file rather than an
   HTTP URI.** `resolveApiKey` (`llm.nim:76-87`) delegates to bitworld's `readCogameUri`, whose
   file branch is a bare `readFile(path)` (`/root/.nimby/pkgs/bitworld/src/bitworld/runtime.nim:104`)
   — bounded for a regular file, but I cannot rule out a blocking read on a FIFO or a hung network
   mount from the tree. It is a one-shot call at `newLlmClient`, wrapped in
   `except CatchableError` (`llm.nim:85-87`), and the HTTP branch has curly's 60 s default. **What
   would settle it:** a statement of what the platform mounts at that URI, or an explicit timeout at
   the call site.
