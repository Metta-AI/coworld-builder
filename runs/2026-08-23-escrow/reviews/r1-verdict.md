blocking: 1

# r1 verdict — escrow

Head: `dac4fc4c6c58a6465bae07f0c1cbc308b5cbf0e6` (`Metta-AI/cogame-escrow`, main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** (all sources, tests, viewer files, workflows, manifest, CI logs, and `git log -p -- tests/` were read and my checklist pass was complete before opening `r1-review.md`; `r1-fixes.md` was opened last, only to audit dispositions). One contamination note, declared: while pulling the run directory listing I saw the coordinator's `log.md`, whose phase-30 lines carry a one-line summary of the review/fix shape ("F1 blocking … F3/F5–F9 dismissed"). This happened *after* my code read was complete and before I read either review file; it did not supply any code-level claim I had not already formed.

CI evidence at head: `gh run list -R Metta-AI/cogame-escrow --branch main -w ci.yml` → run **32646647329**, `headSha dac4fc4c…`, conclusion **success**; jobs `test` ✓ / `docker-smoke` ✓ / `wasm-viewer` ✓, every step `success`, including `Load the bundle in a real browser`.

---

## Standing blocking findings

### B1 — item 7, second sentence: "The baseline's parameters were tuned with a grid harness, not guessed" is not verifiable from the tree   (source: judge; the reviewer filed it as "could not determine", which under the binding rule is the same thing)

- Where: `src/escrow/llm.nim:37-39` — `HousePrice = [ORE:3, GRAIN:3, TIMBER:3, HEARTS:1]`, `TradeUnits = 4`.
- Verified at head: the constants carry a rationale comment ("Flat across the three goods, which is what makes an equal-count swap exactly fair") but no tuning record. There is **no grid/sweep harness anywhere in the tree** (`grep -rni 'grid|tune|sweep'` over `src/ tests/ tools/ docs/ README.md` returns only the design note's unrelated "the only harness" line about CI), no tuning entry in the run's `log.md`, and no tuning mention in any commit message. Contrast the starter, whose baseline constant cites its harness in-code (`cogame-bullwhip/src/bullwhip/llm.nim:157` — "…orders of 150+ (tmp/tune.nim)"); escrow has no equivalent citation. What the tree *does* prove: the parameters work — `tests/test_bot.nim:108-122` asserts `traded.heartsMinted() * 10 >= autarky.heartsMinted() * 13` on 4 seeds, and the head CI log shows `traded 834 vs autarky 474` (1.76×) in both debug and release. That verifies the outcome, not the process the checklist sentence names. The first sentence of item 7 is fully satisfied (see checklist pass below).
- Checklist item: 7 — "…The baseline's parameters were tuned with a grid harness, not guessed."
- Rule applied: "A checklist item you cannot verify from the tree or from cited CI evidence counts as blocking — this is the only rule."
- What would settle it: (a) a committed sweep harness (e.g. `tools/tune_baseline.nim` or a `tmp/tune`-style script) whose grid covers `HousePrice` and `TradeUnits`, with the chosen cell recorded; or (b) a durable record of the sweep already run (commit message, `docs/`, or the run log) with the grid and the numbers; or (c) a coordinator ruling that the CI-run 1.3× minting canary plus the legality-by-construction proof (`test_bot.nim:21-96`) discharges the sentence. Note the category is outside {hang, timeout, static-viewer, manifest, num_agents}, so this residue does not force phase 90 on round exhaustion.

- [other] src/escrow/llm.nim:37-39 checklist item 7's "tuned with a grid harness, not guessed" has no verifiable artefact in the tree — no sweep harness, no recorded grid for HousePrice/TradeUnits; only the 1.3× outcome canary exists

## Refuted / resolved reviewer findings

### F1 — LLM-fallback seats recorded `scripted: false` → RESOLVED AT HEAD (was true at d68c5ec)
- Evidence: `src/escrow/llm.nim:49-58` at head defines `SeatDecision* = object; move*: Decision; scripted*: bool`; all three baseline paths set `scripted: true` (registration `llm.nim:660-666`, no-credentials same branch via `client.disabled`, terminal fallback `llm.nim:704-708`); a model reply that parses and passes `validateMove` sets `scripted: false` (`llm.nim:697`). The server writes the travelled flag through: `let wasScripted = decisions[index].scripted` → `state.sim.applyMove(seat, decision, wasScripted)` (`server.nim:317-331`). `tests/test_bot.nim:273-308` (test 17) forces a double transport failure with credentials present (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME=http://127.0.0.1:1`), asserts `not client.disabled`, and asserts every recorded `move` event carries `scripted: true`. Head CI log: `[OK] 17.` in both debug and release. A finding fixed before the head is not standing.

### F2 — over-cap gives/signs dropped silently → RESOLVED AT HEAD (was advisory anyway)
- Evidence: `src/escrow/sim.nim:485-494 rejectOverCap` + `sim.nim:509-516` emit `reject` with `over_cap: <n> … past the cap of <c> dropped` before `setLen`. `tests/test_sim.nim:359-389` (test 5d) asserts 2 rejects, 2 gives, 2 signs, truncated move event. `[OK] 5d.` at head.

### F3 — `tableStateJson.heard` is `[{seat,say}]`, not the note's `[string]` → REFUTED as a defect
- Evidence: `sim.nim:878-881` emits `{"seat": other, "say": …}`; the shipped protocol contract documents exactly that (`coworld_manifest_template.json:245` — `heard[{seat,say}]`), and `client/renderer.js` never reads `heard`. The code and the manifest agree; the stale artefact is the design note's example frame. No checklist item touches it. Advisory, correctly dismissed.

### F4 — `clip` truncated without the `…` marker → RESOLVED AT HEAD (was advisory; item 9 held both before and after)
- Evidence: `sim.nim:79-89` — `clip(text, limit, marker = false)`; `applyMove` passes `marker = true` for `say`/`notes` (`sim.nim:521-522`), offer stays bare. Test 12 now asserts `endsWith("…")` at the emoji-on-the-cut boundary; `[OK] 12.` at head.

### F5 — four byte-index slices in LLM transport error paths → REFUTED as a checklist matter
- Evidence: `llm.nim:540,549,554,563` byte-slice `response.body` into `EscrowError` messages. I traced every string that reaches an event at head: `move.say/offer/text` via rune-safe `clip` (`sim.nim:517-522`), `reject.text` from `parseContract` reason strings built from already-rune-clipped offer text (`dsl.nim:201-300`), `sign/give.text` from ASCII literals + integers (`sim.nim:259-311`), `end.text` from the two-value reason enum. The byte-sliced messages reach only stdout and the retry hint (`hints[index] = cleanText(error.msg, 300)`, rune-safe, `llm.nim:701`), which never enters the replay. Item 9 names strings "that reach the replay"; none of these do. Advisory at most.

### F6 — replay `turn`-event check compares seats only, not `board` → CONFIRMED as observed, REFUTED as blocking
- Evidence: `sim.nim:944 sameSeats(event.seats, sim.seats)`; no board comparison. But item 2 requires frame-by-frame re-derivation with the viewer drawing from that re-derivation, and a test — all present: `replayMatch` (`sim.nim:929-965`) replays only `move` events, the wasm module builds `states` with the same `replayMatch` (`replay-viewer/escrow_replay.nim:37-39`), the renderer draws `payload.states` only (`renderer.js:1319, 1338-1341`), and `test_sim.nim:604-630` asserts frame count, final-frame equality of `tableStateJson` *and* `resultsJson`, a honoured deadline stop, and a tamper rejection. A tampered recorded `board` cannot mislead the viewer because the board it draws is re-derived, never read from the recorded event. Advisory.

### F7 — trader offers only at zero live contracts; HEARTS never the surplus → REFUTED as a defect
- Evidence: deliberate and load-bearing — `llm.nim:176-180` documents that the zero-live gate "bounds the live count below MaxLive no matter what the other three seats do in the same turn", which is what makes item 7's "legal by construction" true rather than probabilistic (four seats could otherwise pile offers onto one addressee in the same simultaneous turn and blow the cap at registration). `test_bot.nim:46-47` asserts `liveContracts <= MaxLive` for every seat after every apply. Deviation from the note, conformance with the checklist. Advisory.

### F8 — server's `except EscrowError` around `applyMove` unreachable → CONFIRMED, advisory
- Evidence: `sim.nim:496-507` raises only for done/bad-seat/already-decided, none reachable for seats drawn from `pendingSeats()` on the sole mutating thread (`server.nim:285-337`). Dead defensive code, starter-verbatim; its F1-related side effect is gone now that the flag travels with the decision. No checklist item.

### F9 — `gameStart` stamped before the connect wait → CONFIRMED, REFUTED as blocking
- Evidence: `server.nim:240-243, 272-274`. Every wait remains explicitly bounded (connect ≤ 180 s, LLM batch ≤ `llmTimeoutSeconds` × 2 batches, pre-turn lookahead `epochTime() + maxTurnSeconds > playDeadline` at `server.nim:293-303` with `maxTurnSeconds = 125 s`, `playDeadline = start + 720 s`). Charging connects to the play budget makes the game stop *earlier* than the platform requires — conservative in exactly the direction item 5 wants. Advisory.

### F10 — `results_schema.reason` had no enum → RESOLVED AT HEAD
- Evidence: `coworld_manifest_template.json:234` now carries `"enum": ["complete", "deadline"]`; the sim emits exactly those two (`sim.nim:481, 549`) and `""` never reaches `results.json` (`finishEpisode` runs only after `sim.done`).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 32646647329 `success` at `dac4fc4c…`; all 3 jobs green. `git log -p -- tests/` read hunk by hunk: `d68c5ec` corrects hand-computed expectations that were one production step behind (exact array equalities kept, four *added*: `test_sim.nim:124-131,139-144`); `3b6c3eb` tightens test 15 (`decisions[index].move.*` + new `scripted` assert) and adds test 17; `122cf57`/`1ecfa58` only add tests/assertions. No deleted assertion, no widened tolerance, no skip/xfail, no removed file. Both test files run in debug and `-d:release` at head (log shows all four `nim r` groups, 170 `[OK]` lines, zero FAILED). |
| 2 Replay re-derivation | PASS | `sim.nim:929-965 replayMatch` (moves are ground truth, `turn` events checked via `sameSeats`, derived events discarded and re-derived); viewer draws `payload.states` built by the same `replayMatch` in wasm (`escrow_replay.nim:37-39`, `renderer.js:1319,1338-1341`); asserted `test_sim.nim:604-630`. |
| 3 Static viewer | PASS | `coworld_manifest_template.json:15-17` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755 (`git ls-files -s`), the `coworld build` hook (release workflow certify step enforces the bundle and rejects a `/client/replay` viewer, `coworld-release.yml:200-201`); shell fetches only the `?replay=` URL (`static_replay.js:74-96`), all assets relative. The `/client/replay` HTML route (`server.nim:497`) and the protocol-text mention are starter-verbatim live-server pages (`cogame-bullwhip/src/bullwhip/server.nim:470`, its manifest :210); the *declared* viewer is the static bundle. |
| 4 Both name spaces | PASS | prompts/player frames alias-only (`llm.nim:377,459-460`; `server.nim:421,111`, final-frame alias swap `server.nim:199-211`); viewer maps alias→policy for non-baseline seats (`renderer.js:735-762 makeNameMap`/`isBaselineFiller`); `results.names` = policy names (`sim.nim:794`). |
| 5 Degrade-never-hang | PASS | connect wait bounded (`server.nim:241-249`); LLM batch bounded (`makeRequests(batch, timeoutSeconds)`, `llm.nim:683`), ≤ 2 batches/turn; pre-turn lookahead `epochTime() + 125 > start + 720` → `endEarly()` + `reason="deadline"` (`server.nim:278,293-303`; `sim.nim:541-549`, asserted test 9); pacing clamped by `sampleEpisode` (`sim.nim:74-77`, called `escrow.nim:41`); no-credentials path zero network waits (test 15, <2 s bound); no unbounded loop or blocking read found. |
| 6 num_agents | PASS | `num_agents: 4` in `config_schema` (:69-74), `standard` (:361), `sprint` (:387), `certification.game_config` (:411); `docker_smoke.sh:106-152` enforces all four invariants with `SEAT-COUNT FAIL:` prefixes plus the independent `SMOKE_SEATS` cross-check (:54,146-151); grepped the full head-run log: **zero `SEAT-COUNT FAIL`**, and `game=escrow seats=4 … "num_agents": 4`, `smoke OK: seats=4 … reason=complete`. |
| 7 Scripted baseline full episodes, legal | **FAIL (second sentence only)** | First sentence PASS: `test_bot.nim:21-96` — `validateMove == ""` before every scripted apply, `reason == "complete"`, `turnsPlayed == turns`, no reject/`ok:false` on scripted seats, DUE window, `n` in 1..99, gives/signs ≤ 2, `liveContracts ≤ MaxLive`, 4 seeds × 3 mixes < 2 s. Second sentence ("tuned with a grid harness"): **not verifiable from the tree** — see B1. |
| 8 LLM reply handling | PASS | tolerant extract (`llm.nim:492-504`, fences/prose, asserted `test_bot.nim:247-251`); exactly one retry carrying the exact error (`for attempt in 0 .. 1`, `llm.nim:668,679-680`); fallback to scripted (`llm.nim:704-708`); fallback recorded on the move event via `SeatDecision.scripted` → `applyMove` → `eventToJson` (`llm.nim:49-58`, `server.nim:317-331`, `sim.nim:531,678`), asserted by tests 15 and 17. |
| 9 Rune-safe truncation | PASS | `clip` (`sim.nim:79-89`) and `cleanText` (`llm.nim:567-574`) both `runeLen`/`runeSubStr`; applied to offer/say/notes (`sim.nim:517-522`), prompt (`server.nim:466-467`, 4000 cap), quoted reply head (`llm.nim:500-501`), retry hint (`llm.nim:701`). Tests 12 and 16 feed multi-byte at the cap (emoji on the cut) and assert `validateUtf8 == -1` on the strings and the whole replay bytes, plus `parseJson` success. |
| 10 Manifest validates | PASS | `game.docs.readme = {type:"text",value}` (:249-251); `pages` = 2 × `{id,title,content:{type:"text",value}}` (:253-269); `game.protocols` has both `player` (:239-241) and `global` (:243-245). |
| 11 Viewer legible at 360 px | PASS | `client/chrome.css:280-292` `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (exact declarations present); `:484-488` `@media (max-width: 640px) { .plate-label, .plate-stock { display: none; } … }`. |
| 12 Release order and scaffold | PASS | `coworld-release.yml` single job, steps in order: Build manifest (:153) → Certify (:167) → Upload policies (:206, explicitly before upload-coworld) → Upload coworld (:304) → Put secret (:342); ci.yml's smoke runs against an image built in the same job (`ci.yml:176-185`). Three workflows present; `docker_smoke.sh` 100755; `policies.json` = 4 distinct policies, champions `escrow-drafter` + `escrow-swapper` (both `PLAYER_PROMPT`) + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (:15); the three-name placeholder grep over all five files exits 0 (run in the checkout). |
| 13 Viewer executes | PASS | run 32646647329 `wasm-viewer` green **including** step `Load the bundle in a real browser` (conclusion `success`; log `{"loaded":true,"ms":284,…}` against the replay docker-smoke produced); `needs: docker-smoke` (`ci.yml:212`); no `continue-on-error` anywhere in the workflows. Markers: `static_replay.js:133` sets `data-replay-loaded="true"` inside the double rAF on the first drawn frame; `:63` sets `data-replay-error` in `fail()` (missing `?replay=`, fetch timeout via AbortController, wasm rejection, outer catch), removed on retry/success. Matched pair: `config.nims:44-45` `-s MODULARIZE=1 -s EXPORT_NAME=EscrowReplayModule`; shell calls the factory `EscrowReplayModule()` and awaits it (`static_replay.js:150-158`); no `Module.onRuntimeInitialized` in the tree. |
| Simultaneous batch | PASS | one `RequestBatch` per attempt over all pending seats, `client.curl.makeRequests(batch, …)` (`llm.nim:674-683`); server decides all pending seats in one `decideAll` per turn outside the lock (`server.nim:304-314`). No sequential per-seat call anywhere. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `3b6c3eb` | `SeatDecision` travels the flag; server writes it through; test 17 forces a credentialed double failure and asserts `scripted: true` on every move event; `[OK] 17.` both modes at head | yes |
| F2 | fixed, `122cf57` | `rejectOverCap` + test 5d; `[OK] 5d.` both modes | yes |
| F3 | no change (manifest matches code; renderer never reads `heard`) | confirmed by my own grep/read | yes |
| F4 | fixed, `1ecfa58` | `clip(…, marker)` + test 12 `endsWith("…")`; `[OK] 12.` both modes | yes |
| F5 | no change (nothing byte-sliced reaches the replay) | confirmed by my own trace of every event string | yes |
| F6 | no change (item 2 satisfied; board is re-derived, never drawn from the record) | confirmed | yes |
| F7 | no change (zero-live gate is what makes legality constructive) | confirmed; test asserts the cap holds | yes |
| F8 | no change (dead defensive code, starter shape) | confirmed | yes |
| F9 | no change (bounded, conservative direction) | confirmed | yes |
| F10 | fixed, `dac4fc4` | manifest :234 enum present | yes |

## Non-blocking observations

- `sim.history` (`TurnRecord.moves`) still has no reader — inherited starter state, harmless.
- `replayMatch` does not compare the recorded `turn` event's `board` (F6) — a cheap future strengthening, no checklist item.
- The four byte-index slices in `llm.nim` transport errors (F5) would be a one-line-each `cleanText` hardening if anyone ever routes a transport error into an event.
- The count is 1; the standing item's category (`other`) is outside {hang, timeout, static-viewer, manifest, num_agents}, so it is round-continuing residue, not a phase-90 trigger, if the budget exhausts.

BLOCKING: 1
