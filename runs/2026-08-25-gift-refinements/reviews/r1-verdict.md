blocking: 0

# r1 verdict — gift-refinements

Head: `30a0405ff5305270febc8552019635272b5092c2`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
Review adjudicated: `reviews/r1-review.md` (written against `45ef01a`; thirteen fix commits F1–F13 plus A1 have landed on main since).
`r1-fixes.md` was **not read**, per the brief — every disposition below is verified against the code at head, not against the fixer's self-report.

## Standing blocking findings

None. Every reviewer finding is either fixed at head (verified in the tree, cited below) or was advisory against the checklist; my own independent pass found no checklist item falsified at `30a0405`.

## Refuted / resolved at head

The reviewer's findings were written against `45ef01a` and assigned no severity. Adjudicating each against the checklist **at the current head**:

### F1 — early-settle autobank stamped past the last frame → RESOLVED AT HEAD
- Evidence: `src/gift_refinements/sim.nim` `settleEarly()` — `let settleTick = if sim.frames.len > 0: sim.frames[^1].tick else: 0; sim.autobankAll(at = settleTick)`; `server.nim:422` calls `sim.settleEarly()`. Test `tests/test_replay.nim` block `earlySettleStaysInsideTheRecordedFrames` plays a 3-round deadline settle and asserts every event tick `< played`, the tick index carries the closing rows, and `sum(results.scores) == bankedByAutobank`. The finding was real at `45ef01a` (item 2 territory) and no longer reproduces.

### F2 — forfeit replay has zero frames and the shipped parser rejects it → RESOLVED AT HEAD
- Evidence: `sim.nim` `finish()` — `if sim.frames.len == 0: sim.captureFrame()` with the F2 comment. Test `tests/test_replay.nim` block `aForfeitReplayIsStillPlayable` finishes an untouched sim as `erForfeit` and round-trips the bytes through `parseReplay` (frames.len == 1, reason == "forfeit", tick-0 index non-empty).

### F3 — `?spoilers=0` did not hold the game block's beat markers back → RESOLVED AT HEAD
- Evidence: `client/game_block.html:279-305` — `giftMarkers[]`, `applyGiftSpoilers(s)` gating on `CTX.C.getSpoilers()`, re-gated via a `MutationObserver` with `attributeFilter: ['class']` on the chrome's spoilers button; `:328 giftMarkers.push(el)`; `:708 applyGiftSpoilers(s)` applied per frame. Gated by `tests/test_broadcast.nim` block `spoilersHoldThisBlocksBeatsBack`.

### F4 — beat markers re-appended after a backward seek → RESOLVED AT HEAD
- Evidence: `client/game_block.html:256` declares `var placedBeats = {}` once; `:663` comment "deliberately NOT cleared on a jump"; `:310 if (placedBeats[key]) return;`. The `if (jumped) placedBeats = {}` line the reviewer cited is gone. Gated by `tests/test_broadcast.nim` block `beatMarkersAreBuiltOnce` (asserts no second `placedBeats = {}` outside the declaration).

### F5 — `notes` recorded but drawn nowhere → RESOLVED AT HEAD
- Evidence: `client/game_block.html:222-236` (`.feed-row .gr-notes`, shown on `:hover`/`.gr-open`) and `:343-370` (the `order` feed row renders `e.notes` in the expanded row, toggles `aria-expanded`). CI measures it: dom_text_smoke log for run 32921048633 reports `expanded notes=1` at all viewports incl. `ok 360x640`.

### F6 — `giftmiss` unreachable in kernel-driven play → ADVISORY; now pinned
- The behaviour was and is the note's own kernel rule 2 ("target is currently hittable"), not a checklist violation. At head it is documented (README delta 7) and pinned by `tests/test_sim.nim` block `theKernelNeverSchedulesABeamThatMisses` (kernel episodes on all four variants emit gifts and zero `giftmiss`). Nothing to block on.

### F7 — README delta section undercounted → RESOLVED AT HEAD
- Evidence: `README.md:137-143` — "except the ten readings below"; deltas **1–10** enumerated, including `gaveYouLastRound` in tokens (3), per-action cooldowns (4), round-event tick (5), gift-before-spill (6), `giftmiss` (7), `broadcast_core.js` unforked (8), the fourth derivation edit class (9).

### F8 — `broadcast_core.js` byte-identical where the note says "forked" → ADVISORY; now documented
- The tree is the conservative direction (starter renderer untouched; drawing lives in `src/gift_refinements/global.nim`); no checklist item requires the fork. At head it is a named delta (README delta 8, `README.md:209-217`). Checklist item 14 concerns `chrome_common.js` (byte-identical — verified `cmp` against `/workspace/starters/coworld-ctf/client/chrome_common.js`, identical) and the page (see item 14 below).

### F9 — baseline latency bound 50× the note's → RESOLVED AT HEAD
- Evidence: `tests/test_baseline.nim` now times every one of the 1728 rounds in **microseconds** and asserts `median <= 1000`, `p99 <= 1000` (the note's 1 ms), `worst <= 50_000` as an outlier guard, and echoes all three. This is a strict tightening of the removed `slowest <= 50` ms check (verified in the `git log -p -- tests/` hunks — see item 1).

### F10 — constant-true wire-constants assertion → RESOLVED AT HEAD
- Evidence: `tests/test_broadcast.nim:246-248` — `check(WireConstantsJs.startsWith("window.CTF_WIRE={"), …)` on the const the engine actually emits; the `… or true, ""` expression is gone.

### F11 — strict-text-bounds gates zero strings on the bundle → RESOLVED AT HEAD (mitigation verified + mirror pinned)
- The bundle draws board text as sprites, so the bundle step legitimately reports `total: 0`; checklist item 15's required worst-case fixture exists and produces coverage. Evidence at head: run 32921048633 `wasm-viewer` step "Worst-case renderer fixture (canvas text bounds)" → `canvas text: 84 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. The reviewer's caveat (hand-mirrored anchors could drift) is closed by `tests/test_broadcast.nim` block `theFixtureMirrorsTheEnginesBoardAnchors`, which pins the fixture's `CELL/COLS/ROWS/COG` line, the six spawn cells and the 13 px caption to `CellPx`, `Cols`, `Rows`, `CogPx`, `SpawnCells`; the fixture header no longer claims `chrome_common.js` is loaded (asserted in the same block).

### F12 — fourth edit class in the page derivation → ADVISORY; now recorded as a delta
- Evidence: `scripts/derive_broadcast_page.py:33-43` — "THIS IS A FOURTH CLASS OF EDIT AND THE NOTE LICENSES THREE … recorded as a delta in README.md"; README delta 9. The edit (deleting the dead `PB_MODE` latch when the starter's own appended paintball block is replaced) is enumerated in-tree and the derivation reproduces the shipped page (the reviewer ran it byte-identically at `45ef01a`; the script and page moved together since — `git log` shows F3's page change came with a derivation change in the same commit).

### F13 — no `state` frame at episode end → RESOLVED AT HEAD
- Evidence: `server.nim:433-436` — before `final`, `for slot in seated: sendSeat(slot, observationJson(sim.seatView(slot), sim.scene()))` with the F13 comment.

### A1 (advisory) — rate-floor comment contradicted the call order → RESOLVED AT HEAD
- Evidence: `decide.nim:405-412` — the comment now says the floor "is applied at the TOP of `turn`, which `server.nim` calls before the round's ticks … measured between batch STARTS", matching `server.nim:396` and `decide.nim:413-421`. (Head commit `30a0405` is exactly this fix.)

A2–A9 remain accurate advisory observations at head; none names a checklist item.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32921048633** conclusion `success` on `main` at `30a0405` (headSha confirmed via `gh run view --json headSha`); jobs test / docker-smoke / manifest-loads / wasm-viewer all green. `git log -p --since="2026-08-25T20:00:00Z" -- tests/` read hunk-by-hunk: creation commit `fed76e4` plus additive test commits F1/F2/F4/F3/F6/F9/F10/F11; the only removals are F9's `slowest <= 50` ms check (replaced by median/p99 ≤ 1000 µs + worst ≤ 50 ms — strictly tighter) and F10's constant-true `… or true` check (replaced by a real assertion). No skip/xfail/tolerance-widening/test-file deletion (`git log --diff-filter=D -- tests/` empty). |
| 2 Replay re-derivation | PASS | State-recording design: the replay carries per-tick state frames (`replays.nim:95-109`), and the wasm viewer derives its packet through the **same** `BroadcastTracker`/`buildStateJson` fold the live server uses (`replay-viewer/gift_refinements_replay.nim:80-104` imports `gift_refinements/broadcast, global`). Tests assert the equivalences: `tests/test_ledger.nim:107-160` (`ledgerRebuiltFromEventsEqualsTheLiveOne`, `trackerFoldIsSeekAccurate` — "a seek re-folds the tracker to exactly the streamed state"), `tests/test_broadcast.nim:166-225` (packet built from `parseReplay(replayBytes(sim))` decodes), `tests/test_sim.nim` determinism block (same seed + orders → identical `gameHash`, identical frame count, twice and across a fresh server). No parallel recording exists. |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, invoked by ci.yml:282 and required-executable by ci.yml:251-262 (the `coworld build` hook contract); viewer fetches only the replay URL. No `/client/replay` route in `server.nim` (routes are `/healthz`, `/client/player`, `/player`, `/client/global`, `/global`, `server.nim:31-35`); the `'/client/replay'` string in `client/broadcast_core.js:196` is the starter's own page-URL→ws-path mapping table (byte-identical file), not a served route. |
| 4 Both name spaces | PASS | Seats see aliases only: `SeatView` built from `sim.aliases` (`sim.nim:511,542`), prompts name only aliases (`decide.nim:187-234`), `tests/test_llm.nim` asserts no policy/model/seed leak. Viewer maps: `broadcast.nim:122,244` `"pol": scene.policyNames[slot]`; `results.names` = policy names (`sim.nim:624`), populated from `config.players[].name` (`server.nim:336-338`). `tests/test_broadcast.nim:59-78`. |
| 5 Degrade-never-hang | PASS | Lobby bounded by `playerConnectTimeoutSeconds` (`server.nim:361-370`); LLM: `attempt1Ms`/`retryMs` handed to `CURLOPT_TIMEOUT` (`decide.nim:450-451`), monotonic `turnBudgetMs` cap (`decide.nim:366,430`), budget guard flips remaining rounds scripted (`decide.nim:374-381`); play deadline (0.6 × episodeTimeout) checked at every round boundary (`server.nim:388-395`) → `settleEarly()`; `turn` never raises; player side bounded (`gift_refinements_player.nim`, exits 0 on dead socket). Worst case 12×34 s + 180 s + 20 s = 608 s < 720 s, asserted in `tests/test_llm.nim` (`worstEpisodeSeconds <= playDeadlineSeconds`, rate < 30/min). |
| 6 num_agents | PASS | `num_agents: 6` in all four variants and `certification.game_config` (verified by loading the JSON); `tools/ci/docker_smoke.sh:106-151` enforces all four invariants (present, positive int, `len(certification.players)==it`, `len(game_config.players)==it`) plus the `SMOKE_SEATS` cross-check, each failure prefixed `SEAT-COUNT FAIL`. Grepped the docker-smoke log of run 32921048633: **no** `SEAT-COUNT FAIL`; `game=gift-refinements seats=6`, `smoke OK: seats=6 … reason=complete`, "all 6 player containers exited 0". |
| 7 Scripted baseline full episodes, legal | PASS | `tests/test_feasibility.nim` gate (a): all-reciprocator on 4 variants × 12 seeds asserts `sim.reason == erComplete and sim.ending == eeRoundLimit` and `sim.round == config.rounds` after playing every round through `stepWithKernel`; `tests/test_baseline.nim` audits every order (enums, target ≠ self, `gift` in 0..10 and ≤ held) and every per-tick action/world invariant over 4 variants × 12 seeds × 3 rooms. Real end-to-end: docker-smoke episode ended `reason=complete`. Tuning: the note's repair ladder was run and measured (documented `tests/test_feasibility.nim:22-30` and README delta 1-2, per-variant measured figures in-tree); parameters are gated, not guessed. |
| 8 LLM reply handling | PASS | `orders.nim:55-94` tolerant extraction (balanced-brace scan, fence/prose tolerant, first/last-brace fallback); one retry batch of only the failed seats with the appended hint (`decide.nim:333-336,441-442`); fallback to `reciprocatorOrder` with `source = osFallback`, a `fallbackRecord` JSON log row, and the "falling back to scripted order" phrase (`decide.nim:490-507`) — recorded on the `order` event for phase 60. `tests/test_llm.nim` covers all of it including the stubbed-transport path. |
| 9 Rune-safe truncation | PASS | One primitive `cleanText`/`truncateRunes` (`sim_types.nim:175-192`, `runeSubStr`) used for say/notes/prompts/error text; `tests/test_replay.nim` block `runeTruncationSurvivesAStrictParser` feeds multi-byte input at the caps and asserts `validateUtf8 == -1` on the recorded bytes. |
| 10 Manifest validates | PASS | `game.docs` = `{readme:{type:text,value},pages:[{id,title,content:{type:text,value}}×2]}`; `game.protocols.player` and `.global` both `{type:text}` (verified by loading the JSON). `manifest-loads` job green in run 32921048633 (coworld 0.1.38's own `_load_template_manifest`). |
| 11 Viewer legible at 360 px | PASS | `.plate-name … { flex: 1 1 auto; min-width: 3.2em; }` (`client/game_block.html:44-47`, in-page at `replay_broadcast.html:2382-2385`); chip labels hidden under 640 px (`game_block.html:119-125`). Executed evidence: dom_text_smoke `ok 360x640: feed rows=4 expanded notes=1 trust rows=3 roster chips=6 plate names=2`, `{"ok":true,"viewports":13}` (run 32921048633). |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify (:167, `--timeout-seconds 300`) → Upload policies (:214) → Upload Coworld (:312) → Put secret (:350); docker-smoke builds its own image in-run (ci.yml:203) before the smoke. All three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions (both `USE_BEDROCK`), champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, 2 scripted fillers. Placeholder gate run at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files → no match, exits 0. |
| 13 Viewer executes | PASS | (i) run 32921048633 `wasm-viewer` green with step "Load the bundle in a real browser" executed (not skipped, no `continue-on-error` in ci.yml), `needs: docker-smoke` (ci.yml:238), log: `{"loaded":true,"ms":375,…}` and three distinct scrub readouts (`0%="ROUND 5 / 6 TICK 241 OF 360" 50%="ROUND 4 / 6 TICK 197 OF 360" 100%="FINAL TICK 359 OF 360"`), `--soak 10` + `--strict-text-bounds` on the invocation. (ii) `static_replay.js:153` sets `data-replay-loaded="true"` on the loaded frame; `showFailure` sets `data-replay-error` (`:14-20`). (iii) `replay-viewer/config.nims` has no `MODULARIZE`/`EXPORT_NAME` (diff vs starter: only names), worker bootstraps `Module.onRuntimeInitialized` (`static_replay_worker.js:184`) — the matched non-MODULARIZE pair from the one starter. |
| 14 Chrome is the starter's | PASS | (i) `client/chrome_common.js` byte-identical to the starter (`cmp` clean). (ii) `client/replay_broadcast.html` is the starter's page with the game block appended; the committed derivation `scripts/derive_broadcast_page.py` enumerates every edit (note's removals, two + two re-lettered literals, `#lockerroom pointer-events`, and the named fourth class — README delta 9); the size delta (159 KB vs 233 KB) is the enumerated cuts (starter's own appended paintball block + `#viewpanel`/`#fpv`/`#povBadge`/`#mmwarn`), not a rewrite. (iii) transport: `relayout()` sets `--band`/`--hudscale`/`--topband` on `:root` (`replay_broadcast.html:2272-2288`); overlays ride `calc(var(--band…))` (`game_block.html:132`); `#endcard` `bottom: var(--band, 0px)` (`:723`), shown with `.on` (`:734`), taken down on seek (starter's own non-gameover-frame removal); beats are labelled `<button>`s with CSS for all five kinds, gated by `tests/test_broadcast.nim` blocks `beatsAreLabelledClickableButtons`/`transportRulesHold`. (iv) fixed 24×14 board always fits → `#viewpanel` removed entirely, gated by block `removedSurfacesAreGone`. |
| 15 Every drawn string fits | PASS | Board text is sprite-blitted (no page `fillText`), so the gated evidence is the required worst-case fixture: run 32921048633 step "Worst-case renderer fixture (canvas text bounds)" → `canvas text: 84 drawn, 0 never inside the canvas … (--strict-text-bounds)` — `total > 0`, `never_inside = 0`, strict flag on; fixture sets `data-replay-loaded` (`renderer_fixture.html:412`), carries full-cap say/notes on every seat, and dom_text_smoke asserts full-length strings at 13 viewports. The bundle step also carries `--strict-text-bounds` (its `total: 0` is expected and is not the evidence). Mirror-drift risk pinned by `tests/test_broadcast.nim` `theFixtureMirrorsTheEnginesBoardAnchors`. |
| Simultaneous batch | PASS | One `RequestBatch` over all open seats, one `curl.makeRequests` call per attempt (`decide.nim:437-451`); retry batch carries only failures. `tests/test_llm.nim` block `oneBatchCarriesEveryOpenSeat`. |

## Fixer report audit

Per the brief, `r1-fixes.md` was **not read**; in place of auditing the fixer's self-report, each fix commit's claim (its commit message) was verified against the tree at head:

| finding | fix commit claims | I verified at head | agrees |
|---|---|---|---|
| F1 | settle stamps at `frames[^1].tick` | `sim.nim` `settleEarly()` + test | yes |
| F2 | forfeit replay playable | `finish()` captures a frame; parser round-trip test | yes |
| F3 | spoilers gate the block's beats | `game_block.html:279-305,708` + test | yes |
| F4 | beat dedup map permanent | `game_block.html:256,310,663` + test | yes |
| F5 | notes drawn in expanded row | `game_block.html:222-236,343-370`; CI `expanded notes=1` | yes |
| F6 | giftmiss pinned + documented | `test_sim.nim` new block; README delta 7 | yes |
| F7 | README lists every delta | README deltas 1–10, count correct | yes |
| F8 | broadcast_core delta recorded | README delta 8 | yes |
| F9 | 1 ms bound, µs resolution, printed | `test_baseline.nim` median/p99 ≤ 1000 µs, echoed | yes |
| F10 | real wire-constants assertion | `WireConstantsJs.startsWith(...)` | yes |
| F11 | fixture header truthful, mirror pinned | fixture header + `theFixtureMirrorsTheEnginesBoardAnchors` | yes |
| F12 | fourth edit class named as delta | `derive_broadcast_page.py:33-43`, README delta 9 | yes |
| F13 | state frame at episode end | `server.nim:433-436` | yes |
| A1 | rate-floor comment fixed | `decide.nim:405-412` matches `server.nim:396` | yes |

## Non-blocking observations

- Checklist item 7's "tuned with a grid harness": no standalone sweep script is committed; the evidence is the measured exploration recorded in `tests/test_feasibility.nim:8-30` (the note's repair ladder run and measured, per-variant figures) plus the four CI-gated economy gates. That satisfies "not guessed", but a committed sweep harness would make the tuning reproducible rather than only recorded.
- Two feasibility floors ship below the note's targets (beams ≥ 140 vs 200; per-seat ≥ 20 vs 60; ratio ≥ 1.4× vs 1.8×), documented with measurements and the reason `invCap: 15` is kept (README delta 1). These were never tighter in git history, so nothing was loosened during the run; the note-vs-tree delta is declared. Advisory only.
- Reviewer's A2–A9 remain accurate and advisory (e.g. `validate()` re-checks a subset of schema bounds; collect-at-cap sets no cooldown).

BLOCKING: 0
