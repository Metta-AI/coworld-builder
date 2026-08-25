blocking: 0

# r1 verdict — fruit-market
Head: 3f1bab0f6886db7718c864fc0bcf3c8d58bcc10f   Checklist: coordinator brief §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-batch addendum)   Independent read written before reading fixes: yes

Reading order followed: checklist → design note (`runs/2026-08-25-fruit-market/design.md`;
byte-verified against `docs/plans/2026-08-25-fruit-market-design.md`) → the repo at head
(independent notes formed) → `r1-review.md` → `r1-fixes.md` consulted ONLY for the fixer's
rebuttals of F3, F16, F17, F20, after my own read of each of those four was already written.
No contamination: the fixer's disposition table was checked against the tree, never trusted.

The review was written against `43e34e1`; 20 fix commits landed after it. A finding that was
true then and is false now is **refuted at head**, not standing. Verdict: **no blocking
findings stand.** 19 of the reviewer's 23 findings are fixed at head (each verified from the
code, below); the remaining 4 (F3, F16, F17, the `f`-key half of F20) tie to no checklist
item and the checklist properties they brush against hold.

## Standing blocking findings

None.

## Refuted

### F1 — certify lacks `--timeout-seconds 300` → REFUTED (fixed at head)
- Evidence: `.github/workflows/coworld-release.yml:175` at 3f1bab0 — `--timeout-seconds 300`
  on the `coworld certify` invocation (commit f8f3394).

### F2 — a seat with neither env var becomes an LLM seat → REFUTED (fixed)
- Evidence: `src/fruit_market_player.nim:33-37` — `if prompt.len == 0 and scripted.len == 0:
  scripted = "hauler"` (commit 62fbfd4). The registration frame now carries
  `"scripted":"hauler"`, which `server.nim:379` maps to `skHauler`.

### F3 — `broadcast_core.js` byte-identical, note says "forked" → REFUTED as blocking
- Evidence: `cmp client/broadcast_core.js /workspace/starters/coworld-ctf/client/broadcast_core.js`
  at head — identical. Checklist 14 constrains `chrome_common.js` (byte-identity — holds) and
  `replay_broadcast.html` (starter page + appended block — holds); it does not name
  `broadcast_core.js`. Every readout the note routes through that file IS drawn — by
  `src/fruit_market/global.nim` (`bubbleImage`, `barImage`, `aliasImage`, `tagImage`,
  `buildPacket`) as sprite bitmaps the inherited renderer displays; CI's viewer smoke shows the
  drawn scorebug/clock (`{"loaded":true,…"scorebug":"APPLE FARMERS SCORE 110 10 trades …"}`,
  run 32907164596). A design-note-vs-code wording delta with no checklist item behind it.
  Recorded under non-blocking observations.

### F4 — `?spoilers=0` does not hold the appended beats back → REFUTED (fixed)
- Evidence: `client/replay_broadcast.html:2516-2530` — `applyMarketSpoilers(s, C)` gates every
  block-built marker on `C.getSpoilers()` and `el.__tick > s.t`; called from `onFrame` each
  frame (`:2769`); `el.__tick = b.t` set at `:2495` (commit 1727860).
  `tests/test_broadcast.nim:265-272` asserts the wiring by name.

### F5 — book rows omit the stall and never strike through → REFUTED (fixed)
- Evidence: `src/fruit_market/broadcast.nim:132-158` — `stallNameAt(cog.x, cog.y)` emitted on
  every book row; `client/replay_broadcast.html:2557-2585` keeps a cleared row struck through
  for `CLEARED_TICKS = 48` (`.fm-book-row.cleared { … line-through }`, `:2404-2405`;
  `clearedUntil[e.a/e.b]` set on `trade`, `:2704-2706`) (commit fa4c89f).
  `tests/test_broadcast.nim:134-155` asserts the stall column against the recorded cell.

### F6 — plate `trades`/`volume` hardwired to zero and unread → REFUTED (fixed)
- Evidence: `src/fruit_market/broadcast.nim:55-70` tallies both sides of every trade into the
  guild (`tallies[guild].trades.inc`, `volume += given`, mean `rateX100`); page draws them in
  `renderPlateSub` (`replay_broadcast.html:2612-2632`) (commit 8683c6d).
  `tests/test_broadcast.nim:50-77` re-derives all three from the recorded trade events and
  asserts plate equality; CI smoke screenshotted the drawn sub-line ("10 trades · 1.50 🍎/🍌").

### F7 — `say` not the quoted tail of the offer row → REFUTED (fixed)
- Evidence: `client/replay_broadcast.html:2690-2718` — `applyMarketEvents` joins the batch by
  seat (`orders[e.seat]`), the `offer` row ends
  `autoTag(order.source) + (order.say ? ' “' + esc(order.say) + '”' : '')`, and an
  order with `say` but no offer still gets its own row (commit 8f83ec7).
  `tests/test_broadcast.nim:275-283` asserts the joining by name.

### F8 — live `/global` chrome frame always carried `events: []` → REFUTED (fixed)
- Evidence: `src/fruit_market/server.nim:99-105` — `broadcastLocked` now passes
  `eventsJson(gs.sim.events[gs.eventsSent ..< gs.sim.events.len])` and advances
  `gs.eventsSent` (commit eb37171). The dead `chromeFrame` proc is gone
  (`grep chromeFrame src/` → nothing).

### F9 — baseline sweep ran 3 seeds at 50 ms → REFUTED (fixed)
- Evidence: `tests/test_baseline.nim:79` — `for seed in 1 .. 12:`; `:105` —
  `check worstRoundMs < 1.0` (commit 2755c45). A tightening, not a loosening.

### F10 — test_llm missing fallback/max_tokens/batch assertions → REFUTED (fixed)
- Evidence: `tests/test_llm.nim:243-310` — a real loopback stub transport (junk / 429 / 403 /
  silent-past-deadline) routed through `decideAll`, each asserting
  `orders[slot].source == osFallback`; `:340-353` asserts the named
  "cut off at max_tokens" error; `:313-338` asserts `buildBatch(...).len == open.len == Seats`
  on the `RequestBatch` itself, POST verb and per-seat tags, and the retry batch carrying the
  hint (commit e2188d2).

### F11 — no frame-by-frame display-equals-recorded-state test → REFUTED (fixed)
- Evidence: `tests/test_replay.nim:109-197` (commit f2bf7ce) — (a) every parsed frame's
  `c`/`o`/`r` equals `sim.frames` element-wise; (b) `chromeViewOfReplay` — the static bundle's
  only display source (`replay-viewer/fruit_market_replay.nim:56`) — equals the frame field
  for field on every 7th frame; (c) walking the recorded events reproduces every frame's
  inventories and scores, and `results.scores` again. This is checklist 2 in the state-frame
  design the coordinator ruled in-scope.

### F12 — `exhausted` emitted only from the starve drain → REFUTED (fixed)
- Evidence: `src/fruit_market/sim.nim:210-219` — `nowExhausted = cog.stamina == 0` checked
  every tick in step 8 regardless of the hunger branch; emits once per transition
  (commit b38cf37). `tests/test_sim.nim:211-237` asserts the move-that-spends-the-last-point
  case emits exactly one `exhausted`.

### F13 — forfeit replay has zero frames, viewer rejects it → REFUTED (fixed)
- Evidence: `src/fruit_market/sim.nim:369-377` — `forfeit()` records the opening frame when
  `sim.frames.len == 0` (commit ce0f065). `tests/test_replay.nim:199-224` plays the forfeit
  path, round-trips through `parseReplay`, and asserts the terminal chrome frame carries
  `ph == "gameover"` and `over.ending == "FORFEIT"`.

### F14 — test-only `mirror` selectable in the shipped image → REFUTED (fixed)
- Evidence: `src/fruit_market/sim_types.nim:247-256` — `parseScriptKind` has no `mirror`
  branch; unknown values (including "mirror") land on `skHauler` (commit 68696ae).
  `tests/test_sim.nim:55-65` asserts `parseScriptKind("mirror") == skHauler`.

### F15 — policy names reach the replay without `cleanText` → REFUTED (fixed)
- Evidence: `src/fruit_market/sim_state.nim:102-110` — `cleanText(policyNames[slot],
  MaxPolicyNameLen)` at `initSim` (commit 9352498). `tests/test_replay.nim:270-297` feeds
  multi-byte names past the cap and asserts valid UTF-8, `runeLen <= cap`, and
  `results.names == replay.policyNames`.

### F16 — lobby needs all `numAgents` sockets; partial roster burns 180 s → REFUTED as blocking
- Evidence: `src/fruit_market/server.nim:176-191` at head — unchanged
  (`connectedCount >= config.numAgents and registeredCount >= connectedCount`). Checklist 5
  requires an explicit bound on every wait: this one has it (`connectDeadline = gameStart +
  playerConnectTimeoutSeconds`, 180 s, `sleep(200)` polls) and the lobby time comes out of the
  same `gameStart` the play deadline is measured from (`:219`), so worst case is
  180 + 12 × max(18, 40) = 660 s < 720 s. Bounded, no hang, budget holds
  (`tests/test_llm.nim:368-372` asserts the arithmetic). The note's literal phrasing is
  degenerate at zero connections (the reviewer says so too), so the extra term is
  load-bearing. Design-note wording delta only; no checklist item falsified. Behaviour change,
  if wanted, is a design call — recorded under non-blocking observations.

### F17 — `minTurnSeconds` is a sleep, not a tick-through floor → REFUTED as blocking
- Evidence: `src/fruit_market/server.nim:245-252` at head — unchanged bounded
  `sleep(wait)` with `wait <= minTurnSeconds` (schema max 60). Per-round wall clock is
  `max(minTurnSeconds, batch+retry)` — identical to the note's own budget arithmetic; the
  30 rpm ceiling holds (`tests/test_llm.nim:355-359`). The note's "keeps stepping sim ticks
  while it waits" is unimplementable without changing round semantics (a round IS the 60 ticks
  its orders drive). Checklist 5 satisfied; no item falsified. Non-blocking observation.

### F18 — a dead socket keeps its LLM prompt → REFUTED (fixed)
- Evidence: `src/fruit_market/server.nim:396-407` — `CloseEvent` sets
  `state.connected[slot] = false` with the log line "playing hauler for the rest of the
  episode" (commit 4698c93); `decideAll` gates on `connected[slot]` (`llm.nim:664`).

### F19 — fixture re-implements the anchors; real bundle `canvas_text.total` is 0 → REFUTED as blocking (fixed by compensating test)
- Evidence: commit 0768736 added `tests/test_global.nim:124-160`, which drives the SHIPPED
  renderer — `global.nim`'s real `buildPacket` — with worst-case state (full-cap offers on
  every seat, STARVING+EXHAUSTED tags, seats pinned at the extreme rows/columns, `offerN` up
  to the schema-max 12), decodes the packet with the sprite protocol's own parser, and fails
  if any placed object leaves the 1536×864 board. This is exactly the settle-it experiment the
  reviewer named under "Could not determine". Checklist 15's evidence chain at head:
  - main smoke carries `--strict-text-bounds` (ci.yml:337) — its `canvas_text` line at run
    32907164596: `canvas text: 0 drawn, 0 never inside …` (total 0 because the shipped path
    draws no canvas text at all: strings are sprite bitmaps; `say`/`notes` are DOM);
  - fixture step "Worst-case renderer fixture" with `--strict-text-bounds`:
    `canvas text: 135 drawn, 0 never inside the canvas (0 draws crossed an edge), 0
    ellipsized` — total > 0, `never_inside` 0; the fixture asserts its own `say` is exactly
    80 chars and survives into the drawn feed line (`renderer_fixture.html:77-80,175`);
  - the LLM-authored text this viewer actually draws is DOM (`#killfeed`, order book, roster),
    covered by `dom_text_smoke.mjs` at 13 viewports down to 360 px with a full-cap 80-char
    `say` on all eight seats, asserting every row is inside the viewport and not collapsed —
    green in the same run.
  Item 15 satisfied; nothing stands.

### F20 — `+`/`-` speed keys ignored → REFUTED (fixed); `f` half not a checklist item
- Evidence: `src/fruit_market/global.nim:578-579` — `of '+', '=': state.speed =
  steppedSpeed(state.speed, 1)` / `of '-', '_': …, -1` walking `PlaybackSpeeds`
  (commit 9cf75e4); `tests/test_global.nim:95-122` drives the ladder in both directions.
  `'f'` (skip-lulls) remains an explicit `discard`: this game emits no `lulls` spans, the
  button is starter chrome that checklist 14 says to keep, and no checklist item names it.
  Non-blocking observation.

### F21 — nimby pin drift between Dockerfiles → REFUTED (fixed)
- Evidence: `Dockerfile.replay-viewer:13` at head pins `0.1.26`, matching `Dockerfile:15,19`
  and `ci.yml:35` (commit dd2aceb). Both images built green in run 32907164596.

### F22 — docker_smoke checks shape, not `game.results_schema` → REFUTED (fixed)
- Evidence: `tools/ci/docker_smoke.sh:275-387` — results.json validated against the
  manifest's own `game.results_schema` with a keyword-complete checker that hard-fails on any
  keyword it has not been taught (commit 4b122a9). Run 32907164596 logged
  `results.json validates against game.results_schema`.

### F23 — feed-cap and fresh-server assertions absent → REFUTED (fixed)
- Evidence: commit 3f1bab0 — `tests/test_broadcast.nim:156-215` composes every feed row the
  episode can produce and asserts `runeLen <= 200` + valid UTF-8;
  `tests/test_sim.nim:349-356` re-execs the test binary (`--emit-game-hash`) and asserts the
  fresh-process `gameHash` equals the in-process one.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
| --- | --- | --- |
| 1 CI green, no test loosened | PASS | run 32907164596, head `3f1bab0f…`, conclusion `success` (also 32900609480 at 43e34e1, `success`). `git log -p -- tests/`: only three `check` lines ever removed — `ticksPlayed == 720` (became `doAssert`, test_sim.nim:20), the tautological batch count (replaced by real `RequestBatch` assertions, test_llm.nim:326-338), `worstRoundMs < 50.0` (tightened to `< 1.0`, test_baseline.nim:105). No skip/xfail/deleted file; the one ci.yml test-adjacent change (5a039e8) strengthened the manifest-loader check. |
| 2 replay re-derivation | PASS (per coordinator's state-frame ruling) | tests/test_replay.nim:109-197 — recorded frames survive the parse element-wise; `chromeViewOfReplay` (the viewer's only display source, fruit_market_replay.nim:56-61) equals the frame field-for-field; walking the recorded events reproduces every frame's inventories/scores and `results.scores`; determinism twice in-process + fresh process (test_sim.nim:341-356). |
| 3 static viewer | PASS | manifest:16-18 `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755 (`git ls-files -s`); worker's only network call is `fetch(message.replayUrl)` (static_replay_worker.js:113); no `/client/replay` route anywhere (server.nim:411-416 registers healthz/global/player only). |
| 4 both name spaces | PASS | observation carries aliases only (llm.nim:171-233; test_llm.nim:394-403 asserts no farmType/inventory/score on other cogs); roster `pol` = policy name (broadcast.nim:85-86; test_broadcast.nim:79-86); `results.names` = policy names (sim_state.nim:187). |
| 5 degrade-never-hang | PASS | lobby bounded 180 s (server.nim:172-191); batch bounded `llmTimeoutSeconds` whole-seconds, retry once (llm.nim:670-677; sub-second rejected, sim_config.nim:181-186); pacing sleep ≤ minTurnSeconds ≤ 60; play deadline 0.6×timeout checked per round → `endEarly()` (server.nim:219,234-239); shutdown `sleep(500)` + grace 20 s + `quit(0)` (server.nim:151-166); bad token → 401 (server.nim:310-313); player receive loop bounded 200 ms + exit-0-on-dead-socket (fruit_market_player.nim:52-60); worst case 660 s < 720 s (asserted test_llm.nim:368-372). |
| 6 num_agents | PASS | 8 in all four variants (manifest:599,639,679,719) and certification (manifest:757); docker_smoke.sh:110-151 — four SEAT-COUNT invariants + SMOKE_SEATS cross-check; `grep -c "SEAT-COUNT FAIL"` over the run-32907164596 docker-smoke log = 0; smoke logged `seats=8 … reason=complete`. |
| 7 scripted baseline full episodes | PASS | test_baseline.nim: 12 seeds × 4 variants × 3 mixes, every order/action/state bound asserted per tick, episodes to natural end; test_feasibility gate (a) asserts `reason == "complete"`/`round_limit` on ≥10/12 seeds; tuning is measured, not guessed — rendezvous stall measured 34 vs 10 fills (scripted.nim:62-66), HaulerStock retune reasoned against gates (scripted.nim:16-21), gates (a)–(d) enforced in CI. |
| 8 LLM reply handling | PASS | `extractJsonObject` tolerant of fences/prose (llm.nim:462-474; tests llm:110-129); retry once with hint (llm.nim:670-677); fallback = hauler recorded `source:"fallback"` on the `order` event (llm.nim:694-697, events.nim); stub-transport tests assert `osFallback` end-to-end (test_llm.nim:243-310). |
| 9 rune-safe truncation | PASS | `cleanText` runeSubStr (sim_state.nim:42-49) applied to say/notes (llm.nim:559-560), error text (llm.nim:690, MaxErrorLen 200), prompt (server.nim:373-374), policy names (sim_state.nim:106-108); tests feed multi-byte at the caps and assert valid UTF-8 (test_replay.nim:226-305). |
| 10 manifest validates | PASS | `game.docs` = readme text + 2 pages with `{id,title,content:{type:"text"}}` (manifest:474-497); `game.protocols.player` and `.global` both `{"type":"text",…}` (manifest:464-473); `check_manifest_loads.py` runs coworld 0.1.42's own loader, green in CI (run 32907164596, test job). |
| 11 legible at 360 px | PASS | `.plate-name, #scorebug .team-name { flex: 1 1 auto; min-width: 3.2em; }` (replay_broadcast.html:2311-2312); `@media (max-width: 640px)` hides lives-label/chip-pol/book-stall (:2313-2317); dom_text_smoke green at 13 widths incl. 360 (run 32907164596). |
| 12 release order and scaffold | PASS | coworld-release.yml: build(:153) → certify(:167, `--timeout-seconds 300`) → upload-policies(:207) → upload-coworld(:305) → secret put(:343); docker-smoke builds its image in-job before the smoke; all three workflows present; docker_smoke.sh mode 100755; policies.json = 2 × PLAYER_PROMPT champions + 2 scripted fillers, champion #2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (policies.json:13); placeholder grep for `<slug>\|<IMAGE>\|<SEATS>` over the five files returns nothing (verified; gate passes). |
| 13 viewer executes | PASS | run 32907164596 wasm-viewer green, `needs: docker-smoke` (ci.yml:226); "Load the bundle in a real browser" step ran and reported `{"loaded":true,…}`, soak advancing, three distinct scrub readouts (`ROUND 5/6 TICK 242` / `ROUND 4/6 TICK 196` / `FINAL MARKET CLOSED`); no continue-on-error; `data-replay-loaded` set by the shell (static_replay.js:147), `data-replay-error` in `showFailure` (:16); config.nims has no MODULARIZE/EXPORT_NAME and the worker uses `Module.onRuntimeInitialized` (static_replay_worker.js:165) — matched pair from the one starter. |
| 14 chrome is the starter's | PASS | `chrome_common.js` byte-identical (cmp silent); `replay_broadcast.html` = starter page minus the four authorised families (viewpanel/fpv/povBadge/mmwarn — I diffed all 1912 changed lines above the banner; the only additions are the two re-letterings, lockerroom pointer-events, and the coordinator-accepted `FruitMarketBlock.onFrame` hook) + banner + appended block; (a) relayout sets `--band`/`--hudscale`/`--topband` on `document.documentElement` (:2264-2270); (b) appended overlays clipped between the bands, pointer-events none (:2326,:2368); (c) `#endcard` `bottom: var(--band, 0px)` (:724), `.on` (:735), removed on every non-gameover frame i.e. every seek (:1627); (d) beats are labelled `<button>`s seeking `s:<tick>` with CSS for exactly the five emitted kinds (:2408-2422,:2481-2500); `#viewpanel` fully removed — markup, CSS, wiring, ids (test_broadcast.nim:232-240 asserts by name). |
| 15 drawn strings fit | PASS | main smoke carries `--strict-text-bounds` (never_inside 0; total 0 because the shipped board draws no canvas text — strings are sprite bitmaps); the compensating chain: fixture step `canvas text: 135 drawn, 0 never inside … 0 ellipsized (--strict-text-bounds)` with a full-cap 80-char say asserted full-length on every seat (renderer_fixture.html:77-80); the SHIPPED renderer's anchors held to account by tests/test_global.nim:124-160 (real buildPacket, sprite-protocol decode, worst case at the board edges, offerN 12); LLM-authored text is DOM and dom_text_smoke drives it with full-cap says at 13 viewports. Run 32907164596, wasm-viewer job, all three steps green. |
| addendum: one parallel batch | PASS | `decideAll` builds ONE `RequestBatch` over all open seats and issues it via `curl.makeRequests(batch, timeoutSeconds)` (llm.nim:670-677); test_llm.nim:313-338 asserts `batch.len == Seats` on the batch object itself. No sequential per-seat path exists. |

## Non-blocking observations

- `broadcast_core.js` is byte-identical to the starter's where the design note says "forked"
  (F3). The division of labour (all game pixels from `global.nim` over the sprite protocol) is
  the starter's own; no checklist item constrains this file. If the note is to be the record,
  amend the note, not the code.
- Partial-roster lobby waits the full 180 s grace (F16) and `minTurnSeconds` is a bounded
  sleep rather than a tick-through floor (F17): both bounded, both inside the 720 s budget,
  both deviations from design-note phrasing only. Any behaviour change is a design call.
- `'f'` (skip-lulls) is an inherited transport key/button that is a no-op because this game
  emits no `lulls` spans (F20 second half). Starter chrome kept per checklist 14.
- `HaulerEatGuard* = 99` in scripted.nim:16 is declared and never used (dead constant;
  `haulerOrder` uses the literal 45).
- Design note says 429 retries "in the next round's batch"; code retries the 429'd seat once
  in the same round's retry batch, then falls back (llm.nim:521-523, 670-697). Bounded either
  way; no checklist item.

## Fixer report audit

| finding | fixer said | I verified | agrees |
| --- | --- | --- | --- |
| F1 | fixed f8f3394 | coworld-release.yml:175 `--timeout-seconds 300` | yes |
| F2 | fixed 62fbfd4 | fruit_market_player.nim:33-37 defaults to `scripted = "hauler"` | yes |
| F3 | no change, rebutted | broadcast_core.js byte-identical; readouts drawn in global.nim; no checklist item | yes |
| F4 | fixed 1727860 | applyMarketSpoilers + C.getSpoilers gate, tested | yes |
| F5 | fixed fa4c89f | stall on book rows (broadcast.nim:132-158) + strike-through (page:2557-2585) | yes |
| F6 | fixed 8683c6d | guild tallies computed (broadcast.nim:55-70) and drawn (renderPlateSub), tested against recorded events | yes |
| F7 | fixed 8f83ec7 | say quoted on the offer row, `auto` tag from order.source, say-only row kept | yes |
| F8 | fixed eb37171 | broadcastLocked feeds `events[eventsSent..]` to live spectators | yes |
| F9 | fixed 2755c45 | 12 seeds, `< 1.0` ms | yes |
| F10 | fixed e2188d2 | stub transport asserts osFallback/max_tokens/RequestBatch | yes |
| F11 | fixed f2bf7ce | frame-by-frame + events-rederivation + view-equals-frame suites | yes |
| F12 | fixed b38cf37 | `nowExhausted` transition emit in step 8, move-empties-stamina tested | yes |
| F13 | fixed ce0f065 | forfeit records opening frame; parseReplay round-trip tested | yes |
| F14 | fixed 68696ae | parseScriptKind: "mirror" → skHauler, tested | yes |
| F15 | fixed 9352498 | cleanText on policyNames at initSim, tested at the cap | yes |
| F16 | no change, rebutted | bounded 180 s inside the 720 s budget; note phrasing degenerate | yes |
| F17 | no change, rebutted | bounded sleep; wall-clock arithmetic unchanged; rpm + budget tested | yes |
| F18 | fixed 4698c93 | CloseEvent sets `connected[slot] = false` | yes |
| F19 | fixed 0768736 | test_global.nim drives the real buildPacket at the edges; fixture + dom smoke green with cited canvas_text lines | yes |
| F20 | `+`/`-` fixed 9cf75e4, `f` inert by intent | global.nim:578-579 ladder + test; no `lulls` emitted for `f` to skip | yes |
| F21 | fixed dd2aceb | Dockerfile.replay-viewer:13 pins 0.1.26 | yes |
| F22 | fixed 4b122a9 | schema_check against game.results_schema; CI logged the validation line | yes |
| F23 | fixed 3f1bab0 | feed-cap suite + fresh-process gameHash re-exec | yes |

## Could not verify (and why it does not block)

- The feasibility margins (gates a–d) and every Nim test result are verified from CI
  execution (run 32907164596, test job green at this head), not from local execution — the
  sandbox has no Nim toolchain. The checklist accepts cited CI evidence; cited.
- Whether an artifact-write IOError could leave the process alive past the grace (reviewer's
  "could not determine" note): unreached in any CI or certification path observed, bounded by
  the platform's episode timeout either way, and tied to no checklist item.

BLOCKING: 0
