# r1 review — escrow

Repo: `/workspace/scratch/cogame-escrow-repo` = `Metta-AI/cogame-escrow` @ `d68c5ecd58c8ebfb0f8c2d3b5ffa7be99c41bceb` (main)
Base: forked from `cogame-bullwhip` (`/workspace/starters/cogame-bullwhip` @ `46ea61b`), diffed where useful
Design note: `runs/2026-08-23-escrow/design.md` (753 lines)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files read in full: `src/escrow/{types,dsl,sim,llm,server}.nim`, `src/escrow.nim`, `src/escrow_player.nim`,
`tests/test_sim.nim`, `tests/test_bot.nim`, `replay-viewer/{config.nims,escrow_replay.nim,static_replay.js,index.html}`,
`coworld_manifest_template.json`, `tools/build_replay_viewer.sh`, `tools/ci/{docker_smoke.sh,policies.json}`,
`.github/workflows/ci.yml`, `.github/workflows/coworld-release.yml`, `client/chrome.css`, parts of `client/renderer.js`.
CI evidence: `gh run list -R Metta-AI/cogame-escrow --branch main -w ci.yml` → run **32644872806**, conclusion
**success** at the reviewed sha (jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓).

Findings are numbered F1…F10 as the brief asks. Observed = I read the line. Inferred = I reasoned from lines I read.
Untested = would need a run to settle.

---

## Blocking

### F1 — a seat that exhausts its LLM retry and falls back to the scripted baseline is recorded with `scripted: false`

- **Where:** `src/escrow/llm.nim:691-694`; `src/escrow/server.nim:314-328` (esp. `:319`); `src/escrow/sim.nim:508-517`;
  `src/escrow/sim.nim:656-658`.
- **Observed.** `decideAll` returns a bare `seq[Decision]`. Its terminal fallback is:

  ```nim
  # llm.nim:691-694
  for index in open:
    let seat = seats[index]
    echo "escrow llm: seat ", seat, " falling back to the trader baseline"
    result[index] = scriptedAction(sim, seat, skTrader)
  ```

  Nothing in the returned value distinguishes that `Decision` from one a model produced. The server then computes the
  flag from the *registration* state only:

  ```nim
  # server.nim:317-328
  for index, seat in seats:
    let decision = decisions[index]
    let wasScripted = scripted[seat] != skNone or client.disabled
    ...
    state.sim.applyMove(seat, decision, wasScripted)
  ```

  `scripted[seat]` is set only from the player's `{"type":"prompt","scripted":…}` frame (`server.nim:465-473`), and
  `client.disabled` is true only when there are no credentials at all (`llm.nim:146-148`) or after a 401/403
  (`llm.nim:535`). So for a credentialed episode with an LLM-registered seat whose two attempts both fail,
  `wasScripted` is `false`. `applyMove` stores it verbatim (`sim.nim:511 event.scripted = scripted`) and
  `eventToJson` writes it into the replay (`sim.nim:658 result["scripted"] = %event.scripted`).
- **What the note says:** design.md:246-247 — "**Still failing** → the seat plays `scriptedAction(sim, seat, skTrader)`
  … Logged as `scripted: true` on the `move` event so the replay is honest about it."
- **Checklist item:** 8 — "LLM reply handling. Parsing is tolerant …, retries **once** …, then falls back to the
  scripted move — **and the fallback is recorded so phase 60 can count it**." The first three clauses hold
  (`extractJsonObject` at `llm.nim:482-494`; the retry loop `for attempt in 0 .. 1` at `llm.nim:655-690`; the terminal
  fallback at `llm.nim:691-694`). The fourth does not hold on this path.
- **Why blocking:** the only durable record of the fallback is a stdout line (`llm.nim:693`), which is not in the
  replay or in `results.json`. Phase 60 reads the replay's `move.scripted` flags; on a credentialed run those flags
  will report 0 fallbacks no matter how many actually occurred, so a policy silently played by the house baseline is
  indistinguishable from one played by the model.
- **Provenance (so the fixer knows the blast radius):** inherited verbatim from the starter —
  `cogame-bullwhip/src/bullwhip/server.nim:296` has the identical `wasScripted` expression and
  `cogame-bullwhip/src/bullwhip/llm.nim:469-472` the identical untagged fallback. It is not a regression introduced
  here; the design note is what raises the bar.
- **Test coverage of this path:** none that I can find. `tests/test_bot.nim:21-47` passes `true` explicitly to
  `applyMove`; `tests/test_bot.nim:124-147` exercises only the `client.disabled` path (where the flag *is* correct).

---

## Non-blocking

### F2 — over-cap `gives`/`signs` entries are dropped silently, with no `reject` event

- **Where:** `src/escrow/sim.nim:493-496`.
- **Observed:**
  ```nim
  if decision.gives.len > MaxGives:
    decision.gives.setLen(MaxGives)
  if decision.signs.len > MaxSigns:
    decision.signs.setLen(MaxSigns)
  ```
  No event is appended for the dropped entries.
- **What the note says:** design.md:432 lists `reject` as "`turn`, `seat`, `text` (reason code + message; a refused
  offer or **an over-cap action**)". design.md:224/226 also says "entries past the 2nd dropped", which the code does.
- **Note:** on the live path `parseDecision` already truncates at the cap first (`llm.nim:596-597`, `llm.nim:604-605`),
  so `applyMove`'s `setLen` is a second belt that only a hand-built `Move` (a test, a replayed event) can reach.
  Not on the checklist; advisory.

### F3 — `tableStateJson.heard` is an array of objects, not the array of strings the note's frame shows

- **Where:** `src/escrow/sim.nim:858-861`:
  ```nim
  for other in 0 ..< Seats:
    if other != seat and sim.heard[other].len > 0:
      heard.add(%*{"seat": other, "say": sim.heard[other]})
  ```
- **What the note says:** design.md:447 shows `"heard":["…","…","…"]`.
- **Observed consistency elsewhere:** the manifest's `game.protocols.global`
  (`coworld_manifest_template.json:244`) documents `heard[{seat,say}]`, i.e. it matches the code, not the note;
  and `client/renderer.js` never reads `heard` (grep for `heard` returns only the doc comment at `renderer.js:19`).
  So nothing is broken — the note's example frame is the thing that is out of date. Advisory.

### F4 — `clip` truncates without the `…` marker the note's reply-schema table specifies

- **Where:** `src/escrow/sim.nim:79-84`:
  ```nim
  proc clip*(text: string, limit: int): string =
    result = text.strip()
    if result.runeLen > limit:
      result = result.runeSubStr(0, limit)
  ```
  used for `offer`/`say`/`notes` at `sim.nim:497-502`.
- **What the note says:** design.md:227-228 — `say` and `notes` are "truncated at a rune boundary **with `…`**".
- **Observed mitigation:** on the LLM path `parseDecision` runs `cleanText` first (`llm.nim:557-564`), which *does*
  append `…` and returns exactly `limit` runes, so the subsequent `clip` is a no-op and the marker survives. The
  marker is only absent for a `Move` handed straight to `applyMove`. Rune-safety — the checklist's actual
  requirement (item 9) — holds on both paths. Advisory.

### F5 — four byte-index slices remain in the LLM transport error paths

- **Where:** `src/escrow/llm.nim:530`, `:539`, `:544`, `:553` —
  `response.body[0 .. min(response.body.high, 400)]` and friends.
- **Observed:** these build `EscrowError` messages. Those messages go to stdout (`llm.nim:686-687`) and into the
  retry prompt via `hints[index] = cleanText(error.msg, 300)` (`llm.nim:688`, which is rune-safe). I traced every
  string that reaches an event: `move.say/offer/text` come from `clip` (`sim.nim:497-502`), `reject.text` from
  `parseContract`'s reason strings (`dsl.nim:198-299` — the only model-supplied fragments spliced in are
  `fields[0]`/keyword tokens cut at ASCII space boundaries, `dsl.nim:221-225`), `sign.text`/`give.text` from ASCII
  literals plus integers (`sim.nim:259-306`), `end.text` from the reason enum. **No byte-sliced string reaches the
  replay.**
- **What the note says:** design.md:230-232 — "Every truncation uses the starter's `cleanText` … never a byte slice."
- **Provenance:** identical lines in `cogame-bullwhip/src/bullwhip/llm.nim:360, 369, 374, 383`. Escrow *did* rune-fix
  the one that quotes model text (`llm.nim:490-491` uses `runeSubStr` where bullwhip:321 used `head[0 ..< 160]`).
  Checklist item 9 names "`say`, `notes`, prompts, captured errors"; these captured errors are not recorded, so I
  read it as satisfied. Flagging for the judge's own read. Advisory.

### F6 — the replay's `turn`-event check compares seats only, not the recorded `board`

- **Where:** `src/escrow/sim.nim:923-928`:
  ```nim
  of evTurn:
    if event.turn != sim.turn or not sameSeats(event.seats, sim.seats):
      raise newException(EscrowError,
        "turn " & $event.turn & " does not match the seeded re-derivation")
    if sim.events.len == 0 or sim.events[^1].kind != evTurn:
      sim.events.add(event)
  ```
  `sameSeats` (`sim.nim:896-907`) compares `stock`, `escrowed`, `fills`, `heartsEarned`, `signedCount`, `forfeits`.
  `logTurn` (`sim.nim:93-101`) also records `board`, and `eventFromJson` parses it back (`sim.nim:757-759`), but
  nothing compares it.
- **What the note says:** design.md:422 — "the `turn` event is additionally *checked* against the re-derivation,
  exactly as bullwhip checks its `week` event."
- **Observed test:** `tests/test_sim.nim:589-598` tampers `events[index].seats[0].stock[gOre] += 1` and expects a
  raise — that path is covered. A tampered `board` entry in a recorded `turn` event would replay clean.
- **Checklist item 2** is nonetheless satisfied: frames are re-derived (`sim.nim:909-945`), the viewer draws
  `payload.states` produced by that same `replayMatch` in wasm (`replay-viewer/escrow_replay.nim:37-39`,
  `client/renderer.js:1338-1341`), and `tests/test_sim.nim:572-598` asserts it. Advisory.

### F7 — the `trader` baseline's offer gate is "zero live contracts", not "not at the cap"

- **Where:** `src/escrow/llm.nim:208-234`:
  ```nim
  if sim.turn + 1 > sim.config.turns - 1: return
  if sim.liveContracts(seat) != 0: return
  ...
  for other in 0 ..< Seats:
    if other == seat or sim.liveContracts(other) != 0: continue
  ```
  and `llm.nim:217` searches the surplus only over `[gOre, gGrain, gTimber]`, so `HEARTS` is never the surplus.
- **What the note says:** design.md:288-291 — "…and `target` the seat with the largest free stock of `deficit` …
  Skip if it has no surplus, no deficit, or **is at the live contract cap**."
- **Observed rationale in-code:** `llm.nim:167-170` states the zero-live rule is deliberate — it "bounds the live
  count below `MaxLive` no matter what the other three seats do in the same turn", which is what makes the baseline
  legal by construction (checklist item 7) rather than merely usually legal. The `HEARTS`-never-surplus rule is
  commented at `llm.nim:205-207`. Both were declared as known deviations by the builder (`log.md`, 14:20:16Z entry).
  Advisory.

### F8 — the server's `except EscrowError` fallback around `applyMove` is effectively unreachable

- **Where:** `src/escrow/server.nim:327-333`:
  ```nim
  try:
    state.sim.applyMove(seat, decision, wasScripted)
  except EscrowError as error:
    echo "escrow: reply rejected (", error.msg, "); using the trader baseline"
    let fallback = scriptedAction(state.sim, seat, skTrader)
    state.sim.applyMove(seat, fallback, true)
  ```
- **Observed:** `applyMove` (`sim.nim:480-491`) raises only for (a) a finished episode, (b) `seat` out of range,
  (c) a seat that has already decided this turn. Illegal *parts* of a decision are never raised — they are rejected
  and logged when the turn resolves (`sim.nim:481-483`, and the `ok:false` paths at `sim.nim:254-306`). None of
  (a)/(b)/(c) can be true for a seat drawn from `pendingSeats()` on the sole mutating thread. If (c) somehow were
  true, the second `applyMove` on line 333 would raise the same error out of the game thread.
- **Provenance:** identical shape in `cogame-bullwhip/src/bullwhip/server.nim:303-309`.
- Note this is the *only* place the code ever passes `scripted = true` for an LLM seat — which is why F1 has no
  working backstop. Advisory.

### F9 — `gameStart` is stamped before the player-connect wait, so connects are charged to the play budget

- **Where:** `src/escrow/server.nim:240-249` then `:272-274`:
  ```nim
  let gameStart = epochTime()
  let deadline = gameStart + config.playerConnectTimeoutSeconds
  while epochTime() < deadline: ... sleep(200)
  ...
  let playDeadline = if timeoutSeconds > 0.0: gameStart + timeoutSeconds * PlayBudgetFraction else: 0.0
  ```
- **Observed consequence (inferred):** with the defaults (`playerConnectTimeoutSeconds` 180,
  `episodeTimeoutSeconds` 1200 ⇒ playDeadline `gameStart + 720`), a run where a player never connects burns 180 s of
  the 720 s before turn 0. 540 s still comfortably covers the note's arithmetic (design.md:265-266: 16 turns ×
  ~20.4 s ≈ 330 s), and the wait is itself explicitly bounded, so no wait is unbounded.
- **Provenance:** identical in `cogame-bullwhip/src/bullwhip/server.nim:223-256`. Advisory.

### F10 — `results_schema.reason` carries no enum, only prose

- **Where:** `coworld_manifest_template.json:231-234` — `"reason": {"description": "…complete… or deadline…",
  "type": "string"}`.
- **What the note says:** design.md:629 — "`reason` documented as `complete | deadline`". It *is* documented, in the
  description. The code can only ever emit those two (`sim.nim:476` `settle("complete")`, `sim.nim:529`
  `settle("deadline")`, and `resultsJson` writes `""` only while `not sim.done` — `sim.nim:792` — which never reaches
  `results.json` because `finishEpisode` runs only after the loop breaks on `sim.done`, `server.nim:285-303`).
  Advisory.

---

## Traced and consistent

**Resolution rules (design.md:86-127)**

- `sim.nim:447-478 resolveTurn` performs steps 3-9 in exactly the note's order and grouping: all signings in seat
  order (`:450-452`), then all gives (`:453-455`), then all offer registrations (`:456-458`), then expiry
  (`:459-463`), then settlement (`:464-468`), then commissions (`:469-470`), then the tally (`:471-478`). Within a
  seat, reply order is preserved (the inner `for` walks `sim.moves[seat].signs` / `.gives` as listed).
- Step 1 production runs in `openTurn` (`sim.nim:103-118`) *before* the floor snapshot and the `turn` event, so
  seats decide against post-production stock — matching design.md:90-93 and asserted at `test_sim.nim:86-93`.
- Step 3 legality: `applySign` (`sim.nim:254-282`) checks contract exists / is `csOffered` / `acceptor == seat` /
  `postedTurn == sim.turn - 1` / `canPay(ask)`, locks the ASK on success and emits `sign ok:false` + reason on
  failure without moving anything — exactly design.md:96-99. Verified by `test_sim.nim:338-357`.
- Step 4 gives: `applyGive` (`sim.nim:284-306`) rejects-and-logs (self-target, out-of-range `n`, unaffordable) and
  appends to `sim.transfers` on success — design.md:100-104. `sim.transfers` is what `paidUnits` reads.
- Step 5 offer registration: `applyOffer` (`sim.nim:308-336`) parses, on failure emits `reject` with
  `reason & ": " & message` and moves nothing; on success assigns `"C" & $nextId`, **locks the proposer's LOCK
  immediately** (`sim.nim:322`) and emits the `offer` event — design.md:105-109.
- Step 6 expiry: `sim.nim:460-463` expires every still-`csOffered` contract with `postedTurn == now - 1`, refunding
  the proposer (`expireContract`, `sim.nim:338-347`). An offer therefore lives exactly one turn — design.md:110-112,
  asserted at `test_sim.nim:446-455`.
- Step 7 settlement: `sim.nim:465-468` settles every `csSigned` contract with `due == now`, iterating `sim.contracts`
  in append order, which is ascending id because ids are assigned at append (`sim.nim:318-319`). The condition is
  evaluated at that moment (`settleContract` → `evalCondition`, `sim.nim:358`), after steps 3-6 —
  design.md:113-117. All four payouts × both truth values asserted at `test_sim.nim:360-402`.
- Step 8 commissions: `fillCommissions` (`sim.nim:403-426`) fills greedily up to `MaxFills = 2`, all-or-nothing per
  copy (`canPay` gate, no partial fill), credits `CommissionPay`, emits `fill` — design.md:118, `MaxFills` at
  `sim.nim:17`. Hand-computed two-turn fixture for all four profiles at `test_sim.nim:101-145`.
- Step 9 tally + horizon: `sim.nim:471-478` appends the turn record, advances, and on `turnsPlayed >= turns` runs
  `closeHorizon` then `settle("complete")` — design.md:119-122.
- **Horizon closure** (`sim.nim:428-436`): every `csOffered` contract is expired (proposer refunded) *first*, then
  every `csSigned` contract is settled with `horizon = true`, which forces `payout = poKeep`, `branch = "horizon"`,
  and no `forfeits` increment (`sim.nim:349-360, 380-383`). Nothing is stranded — design.md:124-127. Asserted at
  `test_sim.nim:457-476` including `forfeits == 0` on a horizon close.
- **Payouts** (`sim.nim:365-379`) implement exactly the four rows of design.md:131-136, paying only what was
  released from the two escrows (`sim.nim:361-362`). Nothing can be paid that is not already in escrow.
- **Escrowed stock is unusable**: `canPay` (`sim.nim:172-176`) reads `stock` only; `applyGive` reads `stock` only;
  `fillCommissions` gates on `canPay`; `evalCondition`'s `ckHolds` branch reads `sim.seats[…].stock[…]`
  (`dsl.nim:326-328`). The loophole in design.md:143-146 is implemented and asserted three ways at
  `test_sim.nim:285-336`.
- **Conservation:** `lockInto`/`releaseFrom`/`payTo` (`sim.nim:186-197`) are the only escrow movers and are always
  paired; `heartsEarned` is incremented only in `fillCommissions`. `test_sim.nim:478-517` asserts, at the end of every
  turn of a 12-turn mixed episode, `hearts == Seats*StartHearts + heartsMinted` and
  `goods == Seats*StartStock + opened*10 - consumed` (the four profiles sum to 10 of each good per turn —
  `Production` at `sim.nim:37-42`). This is design.md:692-694 verbatim.
- **Scoring:** `score(sim, seat) = sim.seats[seat].stock[gHearts]` (`sim.nim:163-166`), positive, higher-is-better,
  goods worth zero — design.md:150-158. `resultsJson` (`sim.nim:763-793`) emits exactly the note's field set
  (design.md:461-465) with policy names from `config.players` (`sim.nim:774`).
- **End conditions:** only `"complete"` (`sim.nim:476`) and `"deadline"` (`sim.nim:529`) are ever passed to `settle`
  — design.md:167-172.

**DSL (design.md:320-378)**

- `parseContract` (`dsl.nim:201-300`) implements validation rules 1-9 in the note's order with the note's exact
  reason codes: `too_long` on `runeLen > MaxOfferChars` (`:207`), `syntax` on line count / keyword order
  (`:215-224`), `bad_target` (`:238-242`), `bad_bundle` ×2 + not-both-`NOTHING` (`:245-253`), `bad_due` with
  `earliest = turn+1`, `latest = min(turn+DueWindow, turns-1)` (`:256-266`), `bad_condition` incl. the
  PAID-must-be-a-party rule (`:269-276`), `bad_payout` ×2 (`:279-282`), `unfunded` against free stock (`:285-289`),
  `contract_cap` on either side at `MaxLive` (`:292-297`). Every one of those nine codes has a test case at
  `test_sim.nim:194-239`.
- Constants match design.md:397-399: `MaxUnits = 99` (`dsl.nim:28`), `MaxOfferChars = 240` (`:30`),
  `DueWindow = 6` (`:33`), `MaxLive = 4` (`:34`), `MaxTerms = 3` (`:36`); `MaxFills = 2`, `MaxGives = 2`,
  `MaxSigns = 2`, `MaxSayLen = 160`, `MaxNotesLen = 600`, `StartStock = 3`, `StartHearts = 20`,
  `PacingBudgetMs = 120_000` (`sim.nim:15-33`).
- Case-insensitive keyword matching with an alias-preserving normalization: `dsl.nim:221` upper-cases the keyword,
  `renderContract` (`dsl.nim:74-90`) re-emits the seven lines with the alias's own capitalisation. Idempotence
  asserted at `test_sim.nim:241-258`.
- `NOT ALWAYS` is rejected as a typo (`dsl.nim:181-183`) — the note only defines `NOT` over the two atoms
  (design.md:353), so this is consistent.
- `paidUnits` (`dsl.nim:304-315`) sums `sim.transfers` with `turn >= contract.signedTurn`, sender == the named cog,
  receiver == the *other* party — design.md:349-352. All four corner cases (same-turn, pre-signature, wrong
  recipient, never, plus `NOT` inversion) asserted at `test_sim.nim:404-443`.

**Decision path (design.md:198-255)**

- **One parallel batch per turn.** `decideAll` builds a single `RequestBatch` over all still-open seats and issues
  `client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:661-670`). The server calls it once per turn
  with `seats = state.sim.pendingSeats()` (`server.nim:304`, `:314`), which is all four seats at turn start
  (`sim.nim:151-158` + `openTurn` resetting `moveIn`). No per-seat sequential call anywhere. Satisfies the
  checklist's "simultaneous-decision games: one parallel batch per turn".
- **Retry exactly once**, carrying the exact error: `for attempt in 0 .. 1` (`llm.nim:655`) with
  `"\n\nYour previous reply was invalid: " & hints[index] & ". Respond with ONLY the requested JSON object."`
  (`llm.nim:665-667`) and the retry batch containing only `open` seats (`llm.nim:662-669`).
- **Tolerant parsing:** `extractJsonObject` (`llm.nim:482-494`) takes the first `{` to the last `}`, so fences and
  surrounding prose are accepted; asserted at `test_bot.nim:246-250`.
- **Strict legality probe before acceptance:** `sim.validateMove(seat, decision)` (`llm.nim:681-683`), which walks
  the sim's own resolution order (signs → gives → offer) against a copy of the seat's stock (`sim.nim:201-250`).
  This is the note's "probe apply on a copy of the sim" (design.md:240-243) expressed as a pure validator rather
  than bullwhip's `probe.applyOrder`; it produces the same accept/reject decision and the same error text.
- **Execution-time rejection is per-action, not fatal** — `applySign`/`applyGive`/`applyOffer` log `ok:false` /
  `reject` and continue (design.md:249-251).
- **No credentials ⇒ every seat scripted, zero network waits:** `newLlmClient` sets `disabled` when no bedrock
  endpoint/token and no key (`llm.nim:140-148`); `decideAll` short-circuits at `llm.nim:649-654` and `:656`.
  Asserted with a <2 s wall-clock bound at `test_bot.nim:124-147`. This is the path `docker_smoke.sh` takes and the
  CI log confirms it ran: `episode end reason: complete`, `smoke OK: seats=4 … reason=complete`.
- **Model plumbing:** `output_config.effort` omitted for haiku / `4-5` (`llm.nim:512-515`); bedrock model rotation
  on "Model access is denied" / 429 (`llm.nim:105-113`, `:529-541`); `maxOutputTokens` default 1100
  (`types.nim:204`, manifest `:115`); the `stop_reason == max_tokens` guard at `llm.nim:551-553`.
- `parseScriptKind` (`llm.nim:67-74`) maps `1/true/yes/trader → skTrader`, `hoarder/autarky → skHoarder`, else
  `skNone` — design.md:278-279, asserted at `test_bot.nim:148-154`.

**Every wait and its bound (checklist item 5)**

- Player-connect loop: `while epochTime() < deadline` with `deadline = gameStart + playerConnectTimeoutSeconds`
  (`server.nim:241-249`) — bounded.
- LLM batch: `makeRequests(batch, client.timeoutSeconds)` with `timeoutSeconds = config.llmTimeoutSeconds`
  (`llm.nim:63`, `:123`, `:670`) — bounded, and at most two batches per turn.
- Turn loop: `while true` (`server.nim:285`) exits on `state.sim.done` (`:291-292`) or on the pre-turn deadline
  check (`:293-303`):
  ```nim
  if playDeadline > 0.0 and epochTime() + maxTurnSeconds > playDeadline:
    ... state.sim.endEarly(); state.broadcastLocked(); break
  ```
  with `maxTurnSeconds = 2.0 * config.llmTimeoutSeconds.float + 5.0` (`server.nim:278`) = **125 s** at the default
  60, and `playDeadline = gameStart + timeoutSeconds * 0.6` (`server.nim:232`, `:272-274`) = **720 s** of the
  default 1200. This is the *lookahead* the note asks for (design.md:268-270) and is stricter than the starter,
  which only checks `epochTime() > playDeadline` (`cogame-bullwhip/src/bullwhip/server.nim:270`).
- `COWORLD_TIMEOUT_SECONDS` is read but assumed absent (`server.nim:265-271`), falling back to
  `config.episodeTimeoutSeconds`; the manifest does not hand it to the game container
  (`coworld_manifest_template.json:26-28` sets only `ANTHROPIC_API_KEY_URI`) — design.md:259-262.
- `endEarly` (`sim.nim:521-529`) is idempotent (`if sim.done: return`), runs the horizon closure first, then
  `settle("deadline")`. Asserted at `test_sim.nim:519-544`, including that a second `endEarly` is a no-op and that
  `applyMove` afterwards raises.
- Pacing: `sleep(config.turnDelayMs)` (`server.nim:337-338`, `:341-342`), clamped by
  `sampleEpisode` to `PacingBudgetMs div turns` (`sim.nim:75-76`), called once at startup (`src/escrow.nim:41`).
- `finishEpisode` (`server.nim:184-230`): two 500 ms sleeps, an artifact write with a 60 s curl timeout
  (`server.nim:150`), then `quit(0)`.
- `src/escrow_player.nim:54-79` blocks on `socket.receiveMessage()` until `"final"` or a closed socket. Verbatim
  from `cogame-bullwhip/src/bullwhip_player.nim:53-78`. The server always sends `final` before writing artifacts
  (`server.nim:202-215`), so the read terminates. **Untested here** — I did not run it; the docker-smoke log shows
  the episode completing and the game exiting 0.

**String truncation (checklist item 9)**

- `clip` (`sim.nim:79-84`) and `cleanText` (`llm.nim:557-564`) both use `runeLen`/`runeSubStr`. Applied to `offer`
  (`sim.nim:497`), `say` (`:501`, after `\n → space` and the `talk:false` silencing at `:498-500`), `notes`
  (`:502`), the operator prompt (`server.nim:463-464`, `runeSubStr(0, MaxPromptLen)` with `MaxPromptLen = 4000`),
  the model-reply head quoted in an error (`llm.nim:490-491`), and the retry hint (`llm.nim:688`).
- `test_sim.nim:667-720` is the note's strict-UTF-8 test (design.md:700-703): multi-byte runes with an emoji exactly
  on the cut for `say`, `notes` and `offer`; asserts `runeLen == cap`, `validateUtf8() == -1` on every recorded
  string, `validateUtf8(bytes) == -1` on the assembled replay bytes, and `parseJson(bytes)` succeeding with the
  round-tripped strings still valid UTF-8. `test_bot.nim:206-219` asserts the same at the `parseDecision` boundary.

**Replay writer — self-sufficient bytes (design.md:468-476)**

- `replayPayload` (`server.nim:157-176`) emits `protocol: "escrow.replay.v1"`, `names` (the four aliases),
  `policyNames` (`server.nim:73-78`, from `config.players`), `config: {turns, seed, talk, sampled: true}`, the full
  `events` array and `results`. Everything the viewer needs — including **the seed**, from which
  `tableNames` (`sim.nim:55-66`) and the profile deal (`sim.nim:129-134`) are re-derived — is in those bytes.
- `sampled: true` is written unconditionally, and `configFromReplay` (`server.nim:503-512`) / the wasm loader
  (`escrow_replay.nim:31`) both set it, so `sampleEpisode` never re-fits a replayed config (`sim.nim:72-73`).
- The CI docker-smoke produced a 9310-byte replay and the wasm-viewer job loaded it, so the bytes are demonstrably
  sufficient at this sha (run 32644872806).

**Viewer re-derivation (checklist items 2 and 13)**

- `replayMatch` (`sim.nim:909-945`) replays only `move` events through `applyMove`; everything else is either
  checked (`evTurn`) or discarded and re-derived (`else: discard`, `:942-944`). `frames[i] = state after
  events[0..<i]`, and `result.add(sim)` per event gives `events.len + 1` frames — asserted at
  `test_sim.nim:572-580` (`frames.len == live.events.len + 1`, final frame's `tableStateJson` and `resultsJson`
  equal to the live ones), plus the tamper test at `:589-598` and the recorded-deadline case at `:581-588`.
- The wasm module imports **`escrow/sim`** — the same module the server runs (`escrow_replay.nim:9-11`) — and calls
  the same `replayMatch` to build `states` (`escrow_replay.nim:37-39`). The renderer reads
  `states[min(index, …)]` (`renderer.js:1338-1341`) and never derives state itself
  (`renderer.js:1132-1136 stateToView` only copies `state.seats/board/recent`). **Frames are re-derived, not
  parallel-recorded.**
- **MODULARIZE / bootstrap are a matched pair, both from bullwhip.** `replay-viewer/config.nims:45-46` links with
  `-s MODULARIZE=1 -s EXPORT_NAME=EscrowReplayModule`; `replay-viewer/static_replay.js:150` calls the factory
  `EscrowReplayModule().catch(…)` and awaits the promise (`:155-158`). There is no
  `Module.onRuntimeInitialized` anywhere in the tree (grepped). `diff` against
  `cogame-bullwhip/replay-viewer/{config.nims,static_replay.js,index.html}` shows the changes are *only* the
  renames (`bw_*` → `esc_*`, `BullwhipReplayModule` → `EscrowReplayModule`,
  `BullwhipRenderer` → `EscrowRenderer`, wordmark, clock label) plus the two added marker lines — i.e. all four
  viewer files come from one starter, as design.md:522-531 requires.
- **Both readiness markers, both from the shell's own code:** `static_replay.js:131-136` sets
  `data-replay-loaded="true"` inside the double `requestAnimationFrame` alongside `tell("ready")`;
  `static_replay.js:63` sets `data-replay-error` in `fail()`, which is reached from a missing `?replay=`
  (`:141-143`), a fetch timeout/abort (`:88-94` via `FETCH_TIMEOUT_MS = 20000` and an `AbortController`), a wasm
  rejection (`:103-107`) and the outer `.catch` (`:159-161`); it is removed on retry (`:146`) and on success
  (`:114`). `client/renderer.js:1391` also sets `data-replay-loaded`, which the note calls deliberate
  (design.md:542-545).
- **The bundle executes.** `ci.yml:207-212` `wasm-viewer` `needs: docker-smoke`; `ci.yml:293-309` is the
  `Load the bundle in a real browser` step, not commented out and with no `continue-on-error`; it downloads the
  smoke replay (`:277-281`) and runs `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
  … --timeout 90`. Job log for run 32644872806 / job 97207631277:
  `{"loaded":true,"ms":303,"clock":"TURN 0 / 6 · WAITING ON 4","scorebug":"Sprocket ▶ 20 FARMER 4/9/4 …",
  "feed_lines":62}` and `scrub readouts: 0%="TURN 0 / 6 · WAITING ON 4" 50%="TURN 3 / 6 · WAITING ON 4"
  100%="TURN 6 / 6 · FINAL"`.
- `tools/ci/viewer_smoke.mjs` is byte-identical to `coworld-builder/templates/tools/ci/viewer_smoke.mjs`
  (`diff -q` clean) and is committed `100755`.
- **Contacts nothing but S3:** `grep -n http` over `replay-viewer/index.html`, `replay-viewer/static_replay.js`,
  `client/chrome.css` and `client/renderer.js` returns exactly one hit — `renderer.js:1172`, inside the live
  websocket driver, which the static bundle never calls. All bundle assets are relative (`./renderer.js`,
  `./escrow_replay.js`, `./chrome.css`, `./assets/…`).
- `tools/build_replay_viewer.sh` is committed `100755` (`git ls-files -s`), takes the bundle dir as its one
  argument, builds locally via `nim c -d:emscripten` or falls back to the pinned `Dockerfile.replay-viewer`, copies
  the seven data assets plus `index.html` / `static_replay.js` / `renderer.js` / `chrome.css`, and ends with
  `test -f index.html` + `grep -q 'data-replay' static_replay.js` — design.md:547-555 verbatim.

**Manifest (checklist items 3, 6, 10)**

- `game.replay_viewer = {"bundle": "static-replay-viewer"}` (`:15-17`). No pod replay viewer is declared.
  (`server.nim:494` does register a `/client/replay` HTML route and the global-protocol text mentions it at
  `:244` — both are verbatim starter behaviour: `cogame-bullwhip/src/bullwhip/server.nim:470` and its manifest
  `:210`. The *declared* viewer is the bundle.)
- `num_agents: 4` in **`variants[0].standard`** (`:360`), **`variants[1].sprint`** (`:386`), and
  **`certification.game_config`** (`:410`); plus the `config_schema` entry with `minimum: 4, maximum: 4`
  (`:69-74`). `certification.players` has 4 entries (`:416-429`) and `certification.game_config.players` has 4
  (`:396-409`).
- `tools/ci/docker_smoke.sh:106-152` enforces all four invariants with `SEAT-COUNT FAIL:` prefixes: `num_agents`
  present (`:110-118`), a positive integer (`:120-126`), `len(certification.players) == it` (`:128-134`),
  `len(certification.game_config.players) == it` (`:136-140`), and the independent `SMOKE_SEATS` cross-check
  (`:54`, `:145-152`). I grepped the full docker-smoke job log for run 32644872806 (job 97207488211): **no
  `SEAT-COUNT FAIL` anywhere**; the log shows `game=escrow seats=4 config={… "num_agents": 4 …}` and
  `smoke OK: seats=4 results=267B replay=9310B reason=complete`.
- `game.docs` has the required shape: `readme.{type:"text",value}` (`:248-251`) and
  `pages: [{id,title,content:{type:"text",value}}]` ×2 — `rules.md` (`:253-260`) and `dsl.md` (`:261-268`) —
  design.md:633-636.
- `game.protocols` carries **both** `player` (`:238-241`) and `global` (`:242-245`).
- Three player runnables on the same image `{{ESCROW_IMAGE}}` running `/bin/escrow-player`: `escrow-player`
  (no env, `:274-292`), `escrow-trader` (`PLAYER_SCRIPTED=trader`, `:293-315`), `escrow-hoarder`
  (`PLAYER_SCRIPTED=hoarder`, `:316-338`) — design.md:641-647.
- `results_schema` matches `resultsJson` field for field, with `scores`/`hearts` items `integer, minimum: 0`
  (`:157-176`); the score can never be negative (`canPay`/`lockInto`/`applyGive` all gate on free stock).
- `source_url` is `https://github.com/Metta-AI/cogame-escrow/tree/main` (`:29`) and the repo is public
  (`gh` reads it without auth failure).

**Name spaces (checklist item 4)**

- Prompts carry aliases only: `systemPrompt`/`userPrompt` use `sim.names[…]` throughout
  (`llm.nim:367`, `:449-450`, `:274`, `:290`, `:302`, `:361`). `config.players[].name` is never read in `llm.nim`.
- Player frames carry aliases: `welcome.name = state.sim.names[slot]` (`server.nim:419`),
  `state.name` (`server.nim:111`), and `finishEpisode` deliberately swaps in `aliasNames` for the final frame
  (`server.nim:198-211`).
- `policyNames` rides on the `/global` snapshot (`server.nim:90`) and in the replay (`server.nim:167`) for
  spectators; `renderer.js:739-762 makeNameMap` maps alias → policy name for non-baseline seats
  (`isBaselineFiller`, `renderer.js:735-737`) and also rewrites aliases inside feed text (`nameMap.text`).
- `results.names` is policy names (`sim.nim:774`).

**Viewer legibility (checklist item 11)**

- `client/chrome.css:280-292` — `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }`, unchanged from the starter.
- `client/chrome.css:484-488` — `@media (max-width: 640px) { .plate-label, .plate-stock { display: none; } … }`,
  i.e. labels hidden under 640 px with the name kept.

**Release order and scaffold (checklist item 12)**

- The placeholder gate exits 0:
  `grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml docker_smoke.sh policies.json`
  → no matches.
- All three workflows present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are `100755`
  (`git ls-files -s`).
- `coworld-release.yml` step order: `Build the Coworld manifest` (`:153`) → `Certify locally` (`:167`) →
  `Upload the policies` (`:206`) → `Upload the Coworld` (`:304`) → `Put the Coworld secret` (`:342`).
- `tools/ci/policies.json` defines four distinct policies: two `PLAYER_PROMPT` champions (`escrow-drafter` `:3-8`,
  `escrow-swapper` `:9-16`) and two scripted fillers (`escrow-trader` `:17-23`, `escrow-hoarder` `:24-30`), with
  champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`:15`).

**CI green, no test loosened (checklist item 1)**

- `gh run list -R Metta-AI/cogame-escrow --branch main -w ci.yml` → run **32644872806**, `success`, at
  `d68c5ec`; jobs `test` (49 s), `docker-smoke` (1m7s), `wasm-viewer` (1m40s) all ✓.
- `git log -p -- tests/` over this run: the only test change is `d68c5ec`. Reading the hunks —
  `test_sim.nim:101-145` had its hand-computed stock expectations *corrected* (they were one production step
  behind; the numbers are still exact array equalities, and four new full-array assertions were added for the
  farmer/forester/factor);
  `test_sim.nim:336` `check locked.seats[factor].stock[gOre] == 1` → `== 3` (same reason, still an exact equality);
  `test_sim.nim:685-688` `sim.says[mason]` → `sim.heard[mason]` (the turn has resolved, so last turn's `say` has
  moved into `heard`) — the two assertions (`runeLen == MaxSayLen`, `validateUtf8() == -1`) are unchanged;
  one `##` doc comment turned into a `#` comment to fix a compile error. **No assertion deleted, no tolerance
  widened, no skip/xfail added, no test file removed.**
- `ci.yml:104-150` runs every `tests/*.nim` in both debug and `-d:release`; `NIM_TESTS*` repo-variable overrides
  exist in the template but are unset (the log shows both files running in both modes).

---

## Could not determine

- **Checklist item 7, second sentence — "The baseline's parameters were tuned with a grid harness, not guessed."**
  I found no tuning harness in the tree (`grep -rni 'grid\|harness\|tuned\|sweep'` over `*.nim`, `*.md`, `*.sh`
  excluding `docs/plans/` returns nothing) and no tuning entry in `runs/2026-08-23-escrow/log.md`. The closest
  artefacts are `HousePrice`/`TradeUnits` (`llm.nim:37-39`), whose values the design states as given
  (design.md:283-291), and the `test_bot.nim:108-122` canary asserting `traded.heartsMinted() * 10 >=
  autarky.heartsMinted() * 13`. **What would settle it:** a committed sweep script or a log/commit entry recording
  the grid that produced `HousePrice = 3/3/3/1` and `TradeUnits = 4`; or a ruling that the 1.3× canary plus the
  legality proof at `test_bot.nim:66-96` discharges the item. The first half of item 7 — "a test runs an
  all-scripted episode to the natural end, asserts `results.reason == "complete"`, and asserts every order/action is
  inside its legal bounds" — is clearly satisfied (`test_bot.nim:21-96`: `validateMove == ""` on every scripted
  decision before it is applied, `reason == "complete"`, `turnsPlayed == turns`, no `reject`/`ok:false` attributed
  to a scripted seat, `liveContracts <= MaxLive` after every apply, `DUE` inside the window, every `n` in
  `1..MaxUnits`, gives ≤ 2, signs ≤ 2, no say/notes, 4 seeds × 3 mixes under 2 s).

- **Whether F1 matters for phase 60 in practice.** Untested: `docker-smoke` runs with no `ANTHROPIC_API_KEY`, which
  is exactly the `client.disabled` branch where the flag *is* correct. Only a credentialed episode in which a model
  reply fails twice exercises the mis-flagged path. **What would settle it:** either a unit test that drives
  `decideAll` through a forced double failure and asserts the resulting `move` event carries `scripted: true`, or a
  change that has `decideAll` return the per-seat fallback flag.

- **The `TurnRecord.moves` history.** `sim.history` is written (`sim.nim:114-116`, `:471`) but I found no reader —
  it is not in `tableStateJson`, `resultsJson`, any event, or the replay. Design.md:405 lists it as part of the
  `Sim` shape without saying what consumes it. **What would settle it:** confirmation that it is intentionally
  dead state carried over from bullwhip (`cogame-bullwhip/src/bullwhip/sim.nim` keeps the same field). Not a defect
  either way; noted only so the judge does not re-derive it from scratch.
