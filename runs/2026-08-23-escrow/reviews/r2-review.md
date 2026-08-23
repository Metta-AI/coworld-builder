# r2 review — escrow

Repo: `/workspace/scratch/cogame-escrow-repo` = `Metta-AI/cogame-escrow` @ `dac4fc4c6c58a6465bae07f0c1cbc308b5cbf0e6` (main)
Range this round: `d68c5ec..dac4fc4` — four commits (`3b6c3eb` F1, `122cf57` F2, `1ecfa58` F4, `dac4fc4` F10),
touching `src/escrow/{llm,server,sim}.nim`, `coworld_manifest_template.json`, `tests/{test_bot,test_sim}.nim`
(6 files, +134 / −21).
Files read this round: `src/escrow/{llm,server,sim}.nim` (the changed regions in full plus the decision path,
`applyMove`, `clip`, event JSON, `replayMatch`, `resultsJson`), `src/escrow.nim`, `src/escrow_player.nim`,
`tests/test_bot.nim` (tests 15/17), `tests/test_sim.nim` (tests 5d/12), `coworld_manifest_template.json`,
`replay-viewer/{config.nims,static_replay.js,escrow_replay.nim}`, `client/renderer.js` (feed + replay driver),
`client/chrome.css`, `tools/ci/{docker_smoke.sh,policies.json}`, `.github/workflows/coworld-release.yml`,
`nimby.lock`, `/root/.nimby/pkgs/curly/src/curly.nim`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.
Prior round: `r1-review.md` (F1…F10), `r1-fixes.md`, `r1-verdict.md` (`BLOCKING: 1`, item 7's tuning sentence).
Everything carried forward below was re-verified against the code at this sha; nothing is carried on r1's word.

CI evidence at head: `gh run list -R Metta-AI/cogame-escrow --branch main -w ci.yml` → run **32646647329**,
`headSha dac4fc4c…`, conclusion **success**; jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓ with every step
`success`, including `Load the bundle in a real browser`. Full log pulled (`gh run view --log`, 3449 lines):
zero `SEAT-COUNT FAIL`, zero test failures (46 `[OK]` lines across four `nim r` groups — both test files in
debug and `-d:release`), `smoke OK: seats=4 results=267B replay=9310B reason=complete`,
`{"loaded":true,"ms":284,"clock":"TURN 0 / 6 · WAITING ON 4",…,"feed_lines":62}`.

Labels: **Observed** = I read the line at this sha. **Inferred** = I reasoned from lines I read.
**Untested** = would need a run to settle. Findings are numbered F1… restarting this round.

---

## Blocking

### F1 — checklist item 7's second sentence still has no artefact in the tree: the baseline constants carry no tuning record

- **Where:** `src/escrow/llm.nim:34-39`
  ```nim
  ## The scripted baseline's house price table. Flat across the three
  ## goods, which is what makes an equal-count swap exactly fair and an
  ## unequal one obviously not.
  HousePrice*: array[Good, int] = [gOre: 3, gGrain: 3, gTimber: 3, gHearts: 1]
  ## Units the `trader` baseline puts on the table in one contract.
  TradeUnits* = 4
  ```
- **Observed.** None of the four commits in this range touches `llm.nim:34-39` or adds any tuning artefact.
  `grep -rni 'grid\|sweep\|tune\|tuned\|harness'` over `*.nim`, `*.md`, `*.sh`, `*.json`, `*.yml` (excluding
  `docs/plans/`) returns exactly one hit at this sha — `.github/workflows/ci.yml:297`, a comment about a glob
  killing a step, unrelated. There is no `tools/tune*`, no `tmp/tune`-style script, no recorded grid in a commit
  message (`git log --format=%B d68c5ec..dac4fc4` reads F1/F2/F4/F10 only), and nothing in the run's `log.md`.
  Contrast the starter, which cites its own harness in-code: `cogame-bullwhip/src/bullwhip/llm.nim:157`.
- **What the tree does prove:** the constants *work*. `tests/test_bot.nim:108-122` asserts
  `traded.heartsMinted() * 10 >= autarky.heartsMinted() * 13` across seeds `[1, 7, 42, 1234]`, and the head CI
  log shows `traded 834 vs autarky 474` (1.76×) in both debug and release. That is an outcome canary, not a
  record of the process the checklist sentence names.
- **What the note says:** design.md:283-291 states `HousePrice`/`TradeUnits` as given values, with no tuning
  method attached.
- **Checklist item:** 7 — "Scripted baseline plays full episodes legally. … **The baseline's parameters were
  tuned with a grid harness, not guessed.**" The first sentence is fully satisfied (see Traced and consistent).
- **Why blocking:** the second sentence is a named checklist requirement and nothing in the tree or in cited CI
  evidence verifies it. This is the same item the r1 verdict carried as B1 (`r1-verdict.md:15-23`); I re-checked
  it from the code at head rather than from that verdict, and it is unchanged. **What would settle it:** a
  committed sweep harness covering `HousePrice` and `TradeUnits` with the chosen cell recorded, or a durable
  record of a sweep already run (commit message, `docs/`, run log), or a coordinator ruling that the 1.3×
  minting canary plus the legality-by-construction proof discharges the sentence.

No other blocking finding. Every other checklist item I could evaluate is satisfied at this sha; see the
Traced and consistent section, which is where the four new commits landed.

---

## Non-blocking

### F2 — an over-cap `reject` renders in the feed as a refused *contract draft*, and carries the raw `over_cap:` reason code

- **Where:** `src/escrow/sim.nim:485-494` (the new `rejectOverCap`) against `client/renderer.js:822-824`:
  ```nim
  event.text = "over_cap: " & $dropped & " " & what &
    " past the cap of " & $cap & " dropped"
  ```
  ```js
  case "reject":
    return name(event.seat) + "'s draft was refused — " +
      (event.text || "invalid contract");
  ```
- **Observed.** `evReject` is the event kind the sim already used for a refused *offer* (`sim.nim:313-341` `applyOffer`), and the renderer's one feed line for that kind is worded for a contract draft. A dropped third
  give now produces the spectator line "`Sprocket's draft was refused — over_cap: 1 gives past the cap of 2
  dropped`", which names a draft that does not exist and shows an internal reason token.
- **What the note says:** design.md:432 lists `reject` as carrying "reason code + message; a refused offer or
  an over-cap action", so the *event* is right; design.md:584-589 specifies feed lines as legible prose and
  design.md:596-600 asks that nothing be rendered "as an abbreviation or internal enum".
- **Reachability (Observed):** unreachable on every live path. `parseDecision` breaks at the cap before
  building the decision (`llm.nim:604-607` for `sign`, `llm.nim:612-615` for `give`), the `trader` baseline
  never assigns `result.gives` at all and adds at most `MaxSigns` signs (`llm.nim:175-261`,
  cap at `:201-203`), and `skHoarder` returns a bare `Decision()` (`llm.nim:263-268`), and `replayMatch`
  feeds `applyMove` a recorded move that was already truncated (`sim.nim:950-956`). Only a hand-built `Move` —
  a test — reaches it, which is what `tests/test_sim.nim:359-389` does.
- Not on the checklist (item 11 is about the scorebug at 360 px, which is unaffected). Advisory.

### F3 — the new over-cap `reject` events are recorded but are not re-derived on replay

- **Where:** `src/escrow/sim.nim:508-516` (emit, then `setLen`) and `src/escrow/sim.nim:528-534` (the `move`
  event records the **truncated** `decision.gives` / `decision.signs`), against `sim.nim:939-964 replayMatch`.
- **Observed.** Live: three gives ⇒ one `reject` + a `move` event carrying two gives. On replay, `replayMatch`
  reconstructs the `Move` from that recorded event (`sim.nim:950-956`), so `decision.gives.len == MaxGives`,
  the `if` at `sim.nim:511` is false and no `reject` is re-derived. The recorded log and the re-derived log
  therefore differ by those events.
- **Consequence (Observed + Inferred):** none for checklist item 2. A `reject` moves nothing, so every frame is
  bit-identical (`tableStateJson` carries no event list, `sim.nim:871-912`); `replayMatch` compares only
  `evTurn` seat state (`sim.nim:943-948`) and nothing compares event streams; and the viewer's feed reads the
  **recorded** `payload.events`, so the spectator still sees the reject (`renderer.js:1319`, `:1338-1341`).
  Combined with F2's reachability trace, no live episode can produce the divergence at all.
- Advisory; noted so the judge does not have to re-derive the interaction between the F2 commit and replay.

### F4 — the new `SeatDecision` path has no test for the `scripted == false` side

- **Where:** `tests/test_bot.nim:273-308` (test 17, new in `3b6c3eb`) and `tests/test_bot.nim:124-147`
  (test 15, tightened in the same commit).
- **Observed.** Test 17 forces *every* seat to fail twice (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME=http://127.0.0.1:1`,
  `check not client.disabled`) and asserts `decisions[index].scripted` plus `event.scripted` on all four
  recorded `move` events (`test_bot.nim:299-308`). Test 15 covers the `client.disabled` path and now asserts
  the flag too (`test_bot.nim:140`). No test drives a reply that *parses and validates*, so the one line that
  writes `scripted: false` — `llm.nim:697` — is never executed under assertion, and no test covers a mixed
  batch (some seats accepted, some fallen back).
- **What the note says:** design.md:246-247 requires the fallback to be logged `scripted: true`; it says
  nothing about testing the accepted-reply side.
- **Checklist item 8** requires that "the fallback is recorded so phase 60 can count it" — recorded and
  asserted, so the item holds. Exercising `llm.nim:697` would need a stub HTTP endpoint returning a valid
  reply. Advisory.

### F5 — the player binary's frame loop is a blocking read with no explicit timeout

- **Where:** `src/escrow_player.nim:54-58`:
  ```nim
  while true:
    let received = socket.receiveMessage()
    if received.isNone:
      echo "escrow player: connection closed, exiting"
      break
  ```
- **Observed.** `whisky`'s `receiveMessage()` takes no timeout argument here; the loop exits on a `"final"`
  frame (`escrow_player.nim:72-74`) or a closed socket. The server always sends `final` to every player socket
  before writing artifacts and then `quit(0)`s (`server.nim:202-215`, `:230`), and it reaches `finishEpisode`
  on both exits from the game loop (`server.nim:291-292` done, `:293-303` deadline → `break` → `:346`).
- **Inferred:** the read is bounded in practice by the server's own bounded lifetime, and the player socket is
  informational only — decisions are server-side (`server.nim:314-337`), so a stuck player cannot stall the
  episode, the results, or the replay.
- **Provenance (Observed):** verbatim from `cogame-bullwhip/src/bullwhip_player.nim:53-78`; unchanged this
  round. Checklist item 5 names "LLM call, seat reply, round barrier", all of which are bounded (see Traced
  and consistent); this loop is neither, but the item's "no … blocking read" clause is literal, so I record the
  observation rather than deciding it. **Untested** — I did not run a container.

---

## Traced and consistent

### The four new commits

- **`3b6c3eb` (F1 of r1) — the scripted flag now travels with the decision.** `llm.nim:49-58` defines
  `SeatDecision* = object; move*: Decision; scripted*: bool`. I traced every path that can produce one:
  - *registered baseline* — `llm.nim:659-665`: `if kind != skNone or client.disabled:` →
    `SeatDecision(move: scriptedAction(…), scripted: true)`;
  - *no credentials* — the same branch, via `client.disabled`, set at `llm.nim:157` when there is no bedrock
    endpoint/token and no key; the attempt loop then never runs (`llm.nim:668-670`
    `if open.len == 0 or client.disabled: break`), so zero network waits;
  - *accepted model reply* — `llm.nim:687-697`, `scripted: false`, and only after
    `parseDecision(extractJsonObject(text), …)` **and** `sim.validateMove(seat, decision)` both pass;
  - *post-retry fallback* — `llm.nim:704-708`, after `for attempt in 0 .. 1` (`llm.nim:668`) has emptied its
    two batches, `SeatDecision(move: scriptedAction(sim, seat, skTrader), scripted: true)`;
  - *auth failure mid-episode* — `llm.nim:539-547` sets `client.disabled = true` on 401/403 and raises, so the
    seat lands in `stillOpen`, the `attempt 1` guard breaks on `client.disabled`, and the terminal fallback
    tags it `true`.
  The server writes exactly that flag: `server.nim:318-322` (`let decision = decisions[index].move`,
  `let wasScripted = decisions[index].scripted`) → `server.nim:331 state.sim.applyMove(seat, decision,
  wasScripted)` → `sim.nim:531 event.scripted = scripted` → `sim.nim:678 result["scripted"] = %event.scripted`.
  The flag round-trips: `sim.nim:742` reads it back and `sim.nim:950-956` replays with `event.scripted`, so a
  re-derived move event carries the same flag. This is the only remaining computation of the flag — the old
  `scripted[seat] != skNone or client.disabled` expression is gone (`git show 3b6c3eb`), and `state.scripted`
  is now read only to *feed* `decideAll` (`server.nim:307`, `:314`). The one other `applyMove` call site,
  the (unreachable, see below) `except EscrowError` fallback at `server.nim:332-336`, passes `true`, which is
  correct for the baseline it applies. **No regression: the change is strictly more accurate.** The only
  behavioural difference beyond the fix is that when `client.disabled` flips *during* a batch, seats whose
  replies were already accepted that turn are now recorded `false` instead of `true` — the honest reading.
  Design.md:246-247 asks for exactly this.
- **`3b6c3eb` tests.** Test 17 (`test_bot.nim:273-308`) asserts `not client.disabled` (so it is not test 15's
  path), that each returned move equals `scriptedAction(sim, seat, skTrader)` in `offer`/`signs`/`gives.len`,
  that `decisions[index].scripted` is true, and — after applying — that all four recorded `move` events carry
  `event.scripted` (`:299-308`, `check moves == Seats`). The head CI log shows the two failed attempts per seat
  and `[OK] 17.` in both debug and release (log lines 310, 339). Test 15 was tightened, not loosened: hard-coded
  `sim.applyMove(seat, decisions[index], true)` became `sim.applyMove(seat, decisions[index].move,
  decisions[index].scripted)` plus a new `check decisions[index].scripted` (`test_bot.nim:137-144`).
- **`122cf57` (F2 of r1).** `rejectOverCap` (`sim.nim:485-494`) emits a `reject` with the live `sim.turn` and
  the seat, called before each `setLen` (`sim.nim:511-516`). Both caps are still enforced, and the recorded
  `move` event carries the truncated lists (`sim.nim:533-534`). `test_sim.nim:359-389` asserts two rejects
  (both attributed to the right seat, both `startsWith("over_cap")`), exactly `MaxGives` give events,
  `MaxSigns` sign events and the truncated `move` event. `[OK] 5d.` in both modes (log lines 358, 391). See
  F2/F3 above for the two observations this commit raises.
- **`1ecfa58` (F4 of r1).** `clip*(text, limit, marker = false)` (`sim.nim:79-89`) —
  `if marker: result.runeSubStr(0, limit - 1) & "…"` — keeps the output at exactly `limit` runes and stays on
  rune boundaries. `applyMove` passes `marker = true` for `say` and `notes` only (`sim.nim:521-522`); the offer
  DSL is still cut bare (`sim.nim:517`), which is right because `…` is not contract syntax and a truncated
  contract must fail the parser. **Idempotent, so replay is unaffected:** the LLM path already marks the cut
  in `cleanText` (`llm.nim:567-574`, byte-for-byte the same expression), producing exactly `limit` runes, so
  the later `clip` sees `runeLen == limit` and does nothing; likewise a recorded `say`/`notes` re-clipped
  during `replayMatch` is unchanged. `test_sim.nim:716-725` now asserts `endsWith("…")` alongside the existing
  `runeLen == cap` and `validateUtf8() == -1`, with the emoji still on the cut. `[OK] 12.` in both modes
  (log lines 372, 405).
- **`dac4fc4` (F10 of r1).** `coworld_manifest_template.json:234` adds `"enum": ["complete", "deadline"]` beside
  the existing description. The sim can emit only those two (`sim.nim:481 settle("complete")`,
  `sim.nim:549 settle("deadline")`), and the `""` default never reaches `results.json` because `finishEpisode`
  runs only after the loop breaks on `sim.done` (`server.nim:285-346`). The manifest still parses
  (`json.load`), and `docker-smoke`, which builds and gates on it, is green with no `SEAT-COUNT FAIL`.

### r1 "could not determine" items that code can now settle

- **"Whether F1 matters in practice / would need a forced double failure."** Settled: `test_bot.nim:273-308`
  is exactly that test, and it runs in both modes at head. The path r1 could not exercise is now exercised.
- **`sim.history` / `TurnRecord.moves`.** Settled as write-only dead state: the only mentions in the whole tree
  are the two writes, `sim.nim:121 sim.history.add(record)` and `sim.nim:476 sim.history[^1].moves = sim.moves`,
  plus the field declaration `types.nim:188`. `grep -rn history src/ replay-viewer/ tests/` returns nothing
  else — no reader in `tableStateJson`, `resultsJson`, any event, the replay payload, or the viewer. Inherited
  starter shape; no checklist item touches it.
- **The item-7 tuning sentence** remains unsettled — see F1.

### Every wait and its bound (checklist item 5)

- Player-connect loop `while epochTime() < deadline` with `deadline = gameStart + playerConnectTimeoutSeconds`
  (`server.nim:241-249`), `sleep(200)` per iteration — bounded (180 s by default).
- LLM batch: `client.curl.makeRequests(batch, client.timeoutSeconds)` (`llm.nim:683`) with
  `timeoutSeconds: config.llmTimeoutSeconds` (`llm.nim:133`). curly is pinned at `1.1.1` (`nimby.lock:11`) and
  `makeRequests` is declared `{.raises: [], gcsafe.}` with a `timeout` parameter and per-request errors
  (`/root/.nimby/pkgs/curly/src/curly.nim:711-722`), so the call at `server.nim:314` — which is *not* inside a
  `try` — cannot raise out of the game thread on this dependency version. At most two batches per turn
  (`llm.nim:668`).
- Turn loop `while true` (`server.nim:285`) exits on `state.sim.done` (`:291-292`) or on the pre-turn lookahead
  `if playDeadline > 0.0 and epochTime() + maxTurnSeconds > playDeadline` (`:293-303`) →
  `state.sim.endEarly(); state.broadcastLocked(); break`, with `maxTurnSeconds = 2.0 *
  config.llmTimeoutSeconds.float + 5.0` (`:278`) = **125 s** and `playDeadline = gameStart + timeoutSeconds *
  PlayBudgetFraction` (`:272-274`, `PlayBudgetFraction = 0.6` at `:232`) = **720 s** of the default 1200.
  Matches design.md:257-270. `COWORLD_TIMEOUT_SECONDS` is read but assumed absent (`server.nim:265-271`) and
  the manifest hands the game container only `ANTHROPIC_API_KEY_URI` (`coworld_manifest_template.json:26-28`).
- `endEarly` (`sim.nim:541-549`) is idempotent (`if sim.done: return`), runs `closeHorizon()` first, then
  `settle("deadline")`.
- Pacing: `sleep(config.turnDelayMs)` (`server.nim:340-341`, `:344-345`), clamped at startup by
  `sampleEpisode` to `PacingBudgetMs div turns` (`sim.nim:75-76`, called `escrow.nim:41`).
- `finishEpisode` (`server.nim:184-230`): two 500 ms sleeps and artifact writes with a 60 s curl timeout
  (`server.nim:150`), then `quit(0)`.
- The one blocking read without an explicit timeout is the player's frame loop — F5 above.

### Replay writer — self-sufficient bytes (design.md:468-476)

- `replayPayload` (`server.nim:157-176`) emits `protocol: "escrow.replay.v1"` (`ReplayVersion = 1`,
  `server.nim:36`), `names` (the four aliases), `policyNames`, `config: {turns, seed, talk, sampled: true}`,
  the full `events` array and `results`. **The seed is in the bytes** (`server.nim:170`), and it is the only
  source of randomness (`initSim` draws the alias shuffle and the profile deal from it, `sim.nim:55-66`,
  `:125-134`).
- Both re-readers reconstruct the config from those bytes alone and set `sampled = true` so `sampleEpisode`
  never re-fits: the replay server (`server.nim:506-515`) and the wasm module
  (`replay-viewer/escrow_replay.nim:26-33`). Neither reads anything else — no second fetch, no side channel.
- The wasm module imports **`escrow/sim`**, the same module the server runs
  (`replay-viewer/escrow_replay.nim:9-11`), and builds `states` with the same `replayMatch`
  (`:36-39`); `renderer.js:1338-1341` draws `payload.states[…]` and never derives state itself.
- CI at head produced a 9310-byte replay in `docker-smoke` and the `wasm-viewer` job loaded that same artifact
  (`{"loaded":true,…}`), so the bytes are demonstrably sufficient at this sha.

### Viewer bootstrap / link flags (checklist item 13)

- `replay-viewer/config.nims:44-47` links `-s MODULARIZE=1 -s EXPORT_NAME=EscrowReplayModule
  -s EXPORTED_RUNTIME_METHODS=HEAPU8 -s EXPORTED_FUNCTIONS=_main,_malloc,_free,_esc_load_replay,
  _esc_payload_ptr,_esc_payload_len,_esc_error_ptr,_esc_error_len`, matching the `exportc` names in
  `escrow_replay.nim:23,55,61,64,70`.
- `replay-viewer/static_replay.js:150-158` calls the **factory** `EscrowReplayModule().catch(…)` and awaits the
  promise. `grep -rn onRuntimeInitialized` over the tree returns nothing. Matched pair, both from bullwhip.
- I re-checked the "same starter" claim mechanically: `diff` of `static_replay.js` and `config.nims` against
  `/workspace/starters/cogame-bullwhip/replay-viewer/*` after renaming `escrow→bullwhip`/`esc_→bw_` shows only
  the added lineage comments and the two added marker lines — no spliced shell.
- Markers, both from the shell's own code: `static_replay.js:131-134` sets `data-replay-loaded="true"` inside
  the double `requestAnimationFrame` alongside `tell("ready")`; `:63` sets `data-replay-error` in `fail()`,
  reached from a missing `?replay=`, a fetch timeout (`FETCH_TIMEOUT_MS = 20000` + `AbortController`,
  `:75-94`), a wasm rejection and the outer catch; removed on retry (`:146`) and success (`:114`).
  `renderer.js:1391` sets the loaded marker too, which design.md:542-545 calls deliberate.
- The `wasm-viewer` job `needs: docker-smoke`, and its `Load the bundle in a real browser` step ran and passed
  at head (job step list above); no `continue-on-error` anywhere.

### Manifest (items 3, 6, 10, and 12's gate)

Re-read at head (parsed with `json.load`, values printed):
`game.replay_viewer = {"bundle": "static-replay-viewer"}` (`:15-17`); `num_agents` in `config_schema`
(`:69-74`, integer min 4 max 4), in `variants.standard` (`:361`), `variants.sprint` (`:387`) and
`certification.game_config` (`:411`); `len(certification.players) == 4` and
`len(certification.game_config.players) == 4`; cert seats
`[escrow-player, escrow-trader, escrow-player, escrow-hoarder]`; `game.docs.readme = {type,value}` and two
pages `rules.md`/`dsl.md`, each `{id,title,content:{type,value}}`; `game.protocols` = `{player, global}`;
`results_schema` properties exactly the eleven `resultsJson` fields, `reason` now enum-constrained (`:234`);
three player runnables all on `{{ESCROW_IMAGE}}` running `/bin/escrow-player`; `source_url` the public repo
(`:29`). `tools/ci/docker_smoke.sh:110-151` enforces the four seat invariants with `SEAT-COUNT FAIL:` prefixes
plus the independent `SMOKE_SEATS` cross-check (`:54`, `:146-151`) — unchanged this round, and the head log has
zero occurrences of the prefix. The three-name placeholder grep over the five files returns no matches (gate
exits 0). `tools/ci/policies.json` has four policies — `escrow-drafter` and `escrow-swapper` (`PLAYER_PROMPT`)
plus `escrow-trader`/`escrow-hoarder` (`PLAYER_SCRIPTED`) — with champion #2 carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. `coworld-release.yml` step order:
Build manifest (`:153`) → Certify (`:167`) → Upload policies (`:206`) → Upload coworld (`:304`) → Put secret
(`:342`). `client/chrome.css:280-292` still has `.plate-name { … flex: 1 1 auto; min-width: 3.2em; }` and
`:484-488` hides `.plate-label`/`.plate-stock` under 640 px.

### CI green, no test loosened (item 1)

Run **32646647329** `success` at `dac4fc4c…`. I read every test hunk in `d68c5ec..dac4fc4`
(`git log -p -- tests/`, three commits): `3b6c3eb` adds test 17 (+38 lines) and rewrites four lines of test 15
from `decisions[index].offer` to `decisions[index].move.offer` **and adds** `check decisions[index].scripted`
and a flag-carrying `applyMove`; `122cf57` adds test 5d (+32, no other line touched); `1ecfa58` adds two
`endsWith("…")` assertions to test 12 (+5); `dac4fc4` touches no test. **No assertion deleted, no tolerance
widened, no `skip`/`xfail` added, no test file removed.** Both files run in debug and `-d:release` (log lines
283, 312, 341, 374); 46 `[OK]` lines, zero failures (`FAILED` appears once in the log, inside the workflow's
own echoed script text at line 266).

### Carried from r1 and re-verified unchanged at this sha (all advisory there, all still advisory)

- `tableStateJson.heard` is `[{seat,say}]` (`sim.nim:878-881`), matching the shipped protocol text
  (`coworld_manifest_template.json:245`); `renderer.js` never reads `heard`. The note's example frame
  (design.md:447) is the stale artefact.
- `replayMatch` compares only seat state on an `evTurn`, not the recorded `board` (`sim.nim:943-946`,
  `sameSeats` at `:916-927`). Item 2 still holds because the board the viewer draws is re-derived, never read
  from the recorded event.
- The `trader` baseline gates offers on `sim.liveContracts(seat) != 0` rather than the cap
  (`llm.nim:220-221`, `:240-242`), with the in-code rationale at `llm.nim:176-180`; `HEARTS` is never the
  surplus (`llm.nim:227`). Deviates from design.md:288-291, conforms to item 7's legality-by-construction.
- The `except EscrowError` around `applyMove` (`server.nim:332-336`) remains unreachable: `applyMove` raises
  only for a finished episode, a bad seat index, or a seat that already decided (`sim.nim:501-507`), none
  possible for seats drawn from `pendingSeats()` on the sole mutating thread.
- `gameStart` is stamped before the connect wait (`server.nim:240-241`, `:272-274`), so connects are charged to
  the 720 s play budget — conservative in the direction item 5 wants.
- Four byte-index slices survive in transport error paths (`llm.nim:540`, `:549`, `:554`, `:563`). I re-traced
  every string that reaches an event at head: `move.say/offer/text` via `clip` (`sim.nim:517-522`),
  `reject.text` from `parseContract` reason codes (`applyOffer`, `sim.nim:313-341`) and from `rejectOverCap`'s ASCII literal + integers,
  `sign/give.text` from ASCII literals + integers (`sim.nim:259-311`), `end.text` from the two-value reason.
  None of the byte-sliced strings reaches the replay; they go to stdout and to
  `hints[index] = cleanText(error.msg, 300)` (`llm.nim:701`), which is rune-safe.

---

## Could not determine

- **Whether item 7's "tuned with a grid harness" is satisfied outside the tree.** F1. What would settle it is
  listed there: a committed harness, a durable record of the sweep, or a coordinator ruling.
- **Whether a mixed credentialed batch tags seats correctly end-to-end** (some seats accepted, some fallen
  back). The code path is traced and, I believe, correct — `llm.nim:697` is the only writer of `false` and it
  runs per index inside the per-seat `try` — but no test executes it (F4) and CI runs the offline path.
  **What would settle it:** a test with a stub HTTP endpoint returning one valid JSON reply and one failure,
  asserting `scripted` is `false` for the first seat and `true` for the second; or a credentialed episode log
  showing a mix of `scripted` flags in the replay.
- **The player container's exit in a real deployment** (F5) is untested here; the docker-smoke log shows the
  game exiting 0 with results and replay written, which is the property that matters for the platform, but I
  did not observe a player container's own exit at this sha.
