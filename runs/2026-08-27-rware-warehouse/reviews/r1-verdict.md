blocking: 0

# r1 verdict — rware-warehouse
Head: `d5b5686ba4e97abfd1674d93e82814ed75232639` (verified: `git -C /workspace/cogame-rware-warehouse rev-parse HEAD`)
Checklist: coordinator brief §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-batch rule)
Independent read written before reading fixes: **yes** (notes at `/tmp/judge/independent-notes.md`, written before opening `r1-review.md` and `r1-fixes.md`; the review was opened only after the independent notes, the fixes file only after the per-finding verification below was complete)

The review was written against `d303e6c`; 23 commits landed since (`git log d303e6c..d5b5686`
— exactly one commit per finding, F1–F23 in order). Verdict rule applied: a finding that was
real at `d303e6c` and is gone at `d5b5686` is **fixed**, not refuted; a finding I could not
reproduce at either sha would be refuted. **None of F1–F23 was refutable — every one was real
at `d303e6c` (I re-checked the cited lines in `git show d303e6c:<file>` where the head code had
already changed) — and none stands at head.**

## Standing blocking findings

None. (No category lines required.)

## Refuted

None. Every reviewer claim I attempted to refute reproduced cleanly at the sha it was written
against. Two findings were never code defects and I checked whether they should have been
dismissed rather than "documented":

- **F12 (`game.docs` inline `text` vs the note's `uri`)** — the *checklist* (item 10) demands the
  inline-text shape and the code has always matched it; only the design note disagreed. Not a
  checklist violation at any sha; now recorded as `vendor/PATCHES.md` #18. Correctly non-blocking
  either way.
- **F11 (`kill` dropped from the forbidden list)** — the note's own kept-id list includes
  `#killfeed`, so a literal `kill` sweep would self-contradict the note. The load-bearing halves
  (`.beat-marker.kill` CSS absent, feed vocabulary re-mapped) are enforced
  (`tools/build_broadcast_page.py:34`, `tests/test_rware_viewer.nim:141`). Now `PATCHES.md` #17.

## Disposition of all 23 findings, verified at head

| finding | verdict | verified at head |
|---|---|---|
| F1 hold parks instead of standing | **fixed** `c7052f8` | `src/rware/pilot.nim:219-228`: `okHold` keeps `orRunning`, never enters the park branch (`if result.outcome != orRunning:` guards it), `goalCellOf` returns −1 for `okHold` (`pilot.nim:92-93`) → falls to the `goal < 0` NOOP return. Test `tests/test_rware_pilot.nim:310` "hold stands still, wherever the robot is standing". |
| F2 floor plan never sent | **fixed** `c4ce419` | `src/rware/llm.nim` `floorPlanBlock` + `userMessage(operator, floorPlan, view)`; `src/rware/decide.nim:196-205` `seatUserMessage` calls it with `sim.world.wh.asciiMap()` for attempt 1 **and** the retry. Test `tests/test_rware_engine.nim:289` "the driver is handed the floor plan". Deviation (every request, not once at registration) is stated in the `floorPlanBlock` docstring and `docs/PROTOCOL.md`. |
| F3 refill candidate set off by one vs upstream | **fixed** `4dd0143` | `src/rware/sim.nim:327-329`: `refillDraw` is called **before** `requested[shelfHere] = false`, so the delivered shelf is excluded exactly as `vendor/upstream/warehouse.py:915-917` orders it. Test `tests/test_rware_requests.nim:91` "the refill draws from upstream's candidate set". Fixture re-recorded (`tests/replays/rware.replay` touched in `4dd0143`, `ba75dbb`, `ae468ef`). |
| F4 fetch steers to standing cell, not home | **documented** `4b8b82d` | Deliberate divergence, now `vendor/PATCHES.md` #12 + `docs/PORTING-RWARE.md` + embedded manifest docs; `baselines.nim` local rename `home`→`standing` (no behaviour change). Rationale is sound: a home-cell fetch on a re-stowed shelf is permanently `shelf_gone`. |
| F5 fetch tie-break by queue position | **fixed** `9330d32` | `src/rware/baselines.nim:147-149`: `(cost == best and id < result.shelf)` — lowest shelf id wins. Test `tests/test_rware_pilot.nim:287`. |
| F6 `--preload-file`/`FILESYSTEM` dropped | **documented** `981d745` | `vendor/PATCHES.md` #13. Internally consistent: no `.data` file anywhere, assets fetched over HTTP, `tests/test_rware_viewer.nim:281` pins the absence, and the head CI `wasm-viewer` job loads the bundle green. |
| F7 speed chips `[1,2,4,8]` | **documented** `fa4ccfc` | `vendor/PATCHES.md` #14. Default is 1; playback-length arithmetic (16.7 s) unaffected — CI soak observed 10 s of real advancement. |
| F8 `.tiny` at 640 not 620 | **documented** `8b993c1` | `vendor/PATCHES.md` #15. 640 is the *checklist's* own number (item 11 "labels hidden under 640px"); `page_script` toggles `tiny` at `boardW < 640`. |
| F9 art baked in JS, no `rig_art.nim` | **documented** `98f82bb` | `vendor/PATCHES.md` #16. The observable outputs (chips × facings × loaded, tinted crates, darkened floor from the starter's real assets) are produced by `client/broadcast_core.js`; renderer-fixture CI step proves it draws. |
| F10 canvas-text gate measured zero | **fixed** `a9403df` | `tools/ci/renderer_fixture.html` now drives the shipped `client/broadcast_core.js` on a **main-thread** canvas (fillText hook reachable) with a full-cap 120-rune emoji-terminated `say` on all four seats at widths 360/620/630/1024, and fails outright if the renderer drew no text. Head CI run 33081235780, `wasm-viewer` → "Worst-case renderer fixture" step: `canvas text: 29 drawn, 0 never inside the canvas … (--strict-text-bounds)`, `{"loaded":true}`. Test `tests/test_rware_viewer.nim:331`. |
| F11 `kill` dropped from forbidden list | **documented** `9994d7c` | `vendor/PATCHES.md` #17; see Refuted note above — the note's list self-contradicts its kept `#killfeed`. |
| F12 `game.docs` inline text | **documented** `ea61943` | `vendor/PATCHES.md` #18; the code matches checklist item 10, which is the binding source. |
| F13 `throttled` cause outside the enum | **fixed** `1cf37fc` | `src/rware/decide.nim:22-30` `FallbackCauses` closed at the note's seven; a 429 maps to `transport_error` (`decide.nim:420-421`, `:446-447`). Test `tests/test_rware_engine.nim:262` "every fallback cause is in the note's closed enum". |
| F14 spacing sleep ate the retry budget | **fixed** `4f8a79f` | `src/rware/decide.nim:339-348`: `turnStart = engine.lastBatchStart` re-taken **after** the spacing sleep, so attempt1 9 s + retry 4 s = 13 s < 14 s budget always fits. Test `tests/test_rware_engine.nim:197` "the retry always fits inside the turn budget". |
| F15 only the largest jam group reported | **fixed** `ba75dbb` | `src/rware/jam.nim:81-91`: **every** linked group ≥ 2 is unioned into the jam set (ascending, sorted); `updateJam:100-113` closes the shown jam before re-raising on a membership change (`jam → jamclear → jam`), `sim.nim:359-365` emits clear-first. Test `tests/test_rware_sim.nim:324` "two disjoint standoffs are one jam, and a change of members clears". Fixture re-recorded (members are hashed). |
| F16 re-derived fallback/llm counters wrong | **fixed** `d98ac65` | `src/rware/roster.nim:164-177`: both counters now derive from the once-per-seat-per-turn `directive` record's `source` — the same rule `episode.nim:95-100` counts by live. Test `tests/test_rware_replay.nim:137` "the re-derived per-turn counters equal the recorded ones". |
| F17 credited deliver squats on the pad | **fixed** `ae468ef` | `src/rware/pilot.nim:187-197`: carrying an unrequested shelf while on the pad (or already credited, `lastResult == orDone`) makes `deliver` **finish** (`orDone`) → idle → park rule clears the pad. `yieldAfter` re-swept 6→4 (`baselines.nim:31`, `tools/ci/baseline_tuning.json`, PATCHES #19), fixture re-recorded. Test `tests/test_rware_pilot.nim:251` "a credited deliver finishes and gets off the pad". |
| F18 turn-1 default was `hold` | **fixed** `d05aea8` | `src/rware/sim.nim:26-33`: a turn-1 reply with no verb installs `courteousDirective(sim, seat).order`, exactly the note's ladder. Test `tests/test_rware_pilot.nim:224` "turn 1's default order is courteous's, not hold". |
| F19 yield's two exclusions undocumented | **documented** `bd3736c` | `vendor/PATCHES.md` #20 (own cell + queue-lane cells excluded from passing places), mirrored in `docs/PORTING-RWARE.md` and `docs/RULES.md`. |
| F20 TEAM SCORE was seat 0's score | **fixed** `751dc96` | `src/rware/sim_state.nim:79-82` `teamScore()` = `100 × teamDelivered`, no epsilon; `src/rware/broadcast.nim:176` `"score": sim.teamScore()`. Test `tests/test_rware_endcard_labels.nim:132` "TEAM SCORE is the team's score". |
| F21 stale MAGENT-BATTLE / 45x45 copy | **fixed** `a954be4` | `grep -rn "MAGENT\|45x45" tools/build_broadcast_page.py client/` → no matches at head. |
| F22 test 22's connects-then-never-answers half | **fixed** `2186a75` | `tests/test_rware_engine.nim:53-111`: new block seats a registered LLM seat with no credentials, asserts `complete` at tick cap, not a dead seat, no failure payload, `fallbackTurns == turnsPlayed`, `llmTurns == 0`, robot actuated, one enum-legal `fallback` record per turn. |
| F23 rate guard skipped the retry batch | **fixed** `d5b5686` | `src/rware/decide.nim:361-381`: `rateRoom()` re-consulted before the retry batch; seats over the window take courteous with `cause = "rate_guard"`, `attempt = 2`. Test `tests/test_rware_engine.nim:234` "the rate guard bounds every batch, not just the first". |

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | `gh run list -R Metta-AI/cogame-rware-warehouse --branch main -w ci.yml`: run **33081235780** on `d5b5686`, conclusion **success** (jobs test ✓ manifest ✓ docker-smoke ✓ wasm-viewer ✓). `git log -p --since 2026-08-27T11:22Z -- tests/` (16 commits since `2ff5cfc`): every hunk adds or tightens — the only deleted assertion line was `check "-s FILESYSTEM" in config or "--preload-file" in config **or true**` (a vacuous no-op) replaced by the real `check "--preload-file" notin config` (`d303e6c`); F22 added a whole block; no skip/xfail/removed file/widened tolerance anywhere. |
| 2 replay re-derivation, viewer from same re-derivation | **pass** | Playback drives `sim.advanceFrame` — the same proc as live (`replay_runtime.nim` / `episode.nim:115`); per-tick `gameHash` compared every tick; wasm entry `replay-viewer/rware_replay.nim` imports the same `rware/sim`; viewer display built from the re-derived sim (`broadcast.nim buildStateJson`). Tests: `test_rware_determinism.nim:19` (fresh-sim re-derivation), `test_rware_replay.nim:29` (all three end reasons incl. the load-bearing stop), `:235` (corrupted hash caught at its tick), `:267` (seek re-derives). CI "Headless wasm smoke of the emitted module" re-derives the committed fixture at head — green. |
| 3 static viewer | **pass** | `coworld_manifest_template.json` → `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, invoked by path in `ci.yml`; worker fetches only the replay URL, assets are relative to the bundle; no `/client/replay` declared to the platform (server route is developer-local only, `server.nim:250-255`). |
| 4 both name spaces | **pass** | `decide.nim seatView` emits aliases only (no `seatNames` read in decide/llm); viewer maps real names via join/`register` records (`broadcast.nim`, `roster.nim:157-163`); `showPlayerLabels` false everywhere. Tests `test_rware_labels.nim:16,51,71`. |
| 5 degrade-never-hang, ≤ 60 % of 1200 s | **pass** | `attempt1Ms 9000` / `retryMs 4000` / `turnBudgetMs 14000` measured from batch start (`decide.nim:340-348`) / `turnSpacingMs 12000` bounded sleep / rolling-60 s rate guard on **both** batches / budget guard (`decide.nim:289-296`) / `wallClockBudgetSeconds 660` hard stop written as a load-bearing record (`episode.nim:34-52`) / `lobbyJoinTimeoutTicks` / 16-probe yield / `maxFrames` cap / 20 s shutdown grace; mummy serves on its own thread. 660 + 20 = 680 < 720. Manifest test `test_rware_manifest.nim:151` asserts every `wallClockBudgetSeconds` ≤ 660. Player binary: bounded dial (240×500 ms), bounded reconnects (6), exits 0 on close race. |
| 6 num_agents + SEAT-COUNT | **pass** | `num_agents: 4` in both variants' `game_config` and `certification.game_config` (verified by parsing the manifest); `docker_smoke.sh:106-150` enforces all four invariants + `SMOKE_SEATS` cross-check with `SEAT-COUNT FAIL:` prefixes; `grep -c "SEAT-COUNT"` over the head docker-smoke job log (98548702847) = **0**; log shows `smoke OK: seats=4 … reason=complete`. |
| 7 scripted baseline full legal episodes, tuned | **pass** | `test_rware_engine.nim:16-51` (all-scripted headless episode, `endReason == complete`, exact results key set, score formula); `test_rware_pilot.nim:38-99` (bounded orders 200 states × both baselines, legal actions only); `tools/tune_baselines.nim --check` re-run in CI (`test` job step), `tools/ci/baseline_tuning.json` re-swept after F17 (yieldAfter 4), `test_rware_tuning.nim` asserts shipped == swept. |
| 8 LLM reply handling | **pass** | `extractJsonObject` (prose/fence-tolerant, `directives.nim:75-113`), retry once as a second batch (`decide.nim:351-429`, `attempt < 2`), fallback = the `courteous` proc with a recorded `fallback` chat record and `results.fallbackTurns` counting (`episode.nim:97-98`); phase-60 grep phrases present (`llm.nim` "LLM provider is unavailable", `decide.nim:451` "falling back"). |
| 9 rune-safe truncation | **pass** | `truncateRunes`/`sanitizeLine`/`sanitizeSay` (`sim_types.nim:103-142`), `truncateBytes` for the one byte budget walks off continuation bytes; caps applied at every recorded string; 4-byte-emoji-at-cap tests `test_rware_pilot.nim:117-211`, whole-replay strict-UTF-8 `test_rware_replay.nim:162-209`; CI runs `replay_summary.py` under a strict parser on every push. |
| 10 manifest validates | **pass** | `game.docs` = `{"readme":{"type":"text",…},"pages":[{id,title,content:{"type":"text",…}}×2]}`; `game.protocols` carries `player` **and** `global` as `{"type","value"}` objects (parsed and printed above); the `manifest` CI job loads it under installed `coworld==0.1.43` — green at head. |
| 11 legible at 360 px | **pass** | `client/replay_broadcast.html:1717-1722` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`; labels hidden under 640 px (`#stage.tiny .plate .deliv-label { display: none; }`, `.tiny` toggled at `boardW < 640`); asserted by `test_rware_viewer.nim:224`. |
| 12 release order and scaffold | **pass** | `coworld-release.yml`: Build manifest (:159) → Certify (:173, `--timeout-seconds 300`) → Upload policies (:217) → Upload Coworld (:315) → Secret put (:414). Three workflows present; `docker_smoke.sh` + `build_replay_viewer.sh` 100755; `policies.json` = 2×`PLAYER_PROMPT` champions + 2×`PLAYER_SCRIPTED` fillers, champion #2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; I ran the checklist's exact grep over the five named files — no match, gate exits 0 (only documented `<run_id>`/`<name>:vN` residues elsewhere). |
| 13 viewer executes | **pass** | Head run 33081235780 `wasm-viewer` (job 98549350211) `needs: docker-smoke` (`ci.yml:350`), no `continue-on-error` anywhere in the workflow; "Load the bundle in a real browser" ran with `--timeout 90 --soak 10 --strict-text-bounds` against the replay docker-smoke produced and reported `{"loaded":true,"ms":314,…}`, soak `0→217→278/530`; `data-replay-loaded` set in the `'loaded'` branch after `ingestPacket` (`static_replay.js:161-164`), `data-replay-error` in `showFailure`; non-MODULARIZE build + `Module.onRuntimeInitialized` worker are one matched set from this starter (`config.nims` comment + `static_replay_worker.js:188,239`; `test_rware_viewer.nim:266` pins the pairing). |
| 14 chrome provenance | **pass** | `cmp client/chrome_common.js /workspace/starters/coworld-ctf/client/chrome_common.js` → identical (test pins sha256). I independently parsed both pages' first `<style>` blocks: the fork's **146 CSS rules are all byte-identical to the starter's; 0 modified; the 79 starter-only rules are exactly the documented removals** (fpv, viewpanel/zoom/minimap, squad pips, flag icons, lives, perks, POV, unemitted beat kinds). The 104 KB-vs-233 KB size difference is fully accounted by those removals plus the swapped page IIFE — `tools/build_broadcast_page.py` reproduces the committed page from the read-only starter (the reviewer verified the diff is empty; the CI "broadcast page" step checks the inherited half + single splice marker on every push). Transport: `relayout()` sets `--band`/`--topband`/`--hudscale` on `:root`; `#endcard { bottom: var(--band, 0px) }`, shown with `.on`, dismissed on every seek; beats are labelled `<button>`s (`warehouseBeat`) with CSS for exactly `{delivery,jam,fallback,end}`; `#viewpanel`/`#fpv`/`#povBadge` removed markup+CSS+wiring (fixed arena); `#reqrail`/`#jamchip` ride `--topband`, nothing fixed sits in the band (`test_rware_viewer.nim:181-222`). |
| 15 every drawn string fits | **pass** | `ci.yml`'s browser-load step carries `--strict-text-bounds`; its `canvas_text total: 0` is the documented Worker/OffscreenCanvas blind spot, and the repo's gated number is the **Worst-case renderer fixture** step: shipped `broadcast_core.js` on a main-thread canvas + the real page in an iframe, full-cap 120-rune emoji-terminated `say` on all four seats, widths 360/620/630/1024, asserts the rendered radio line is still the full-cap string and fails if the board renderer drew nothing — head CI: `canvas text: 29 drawn, 0 never inside the canvas, 0 ellipsized (--strict-text-bounds)`, `loaded:true`. The viewer draws no LLM text on canvas (radio is DOM `#killfeed`); board canvas strings (W1/W2 pads, shelf ids) are the ones measured. |
| batch rule (simultaneous decisions) | **pass** | One `RequestBatch` per attempt, all open seats, one `curl.makeRequests` call (`decide.nim:386-399`); the retry is a second single batch; no sequential path exists. |

## GameVersion weighing (requested by the brief)

`GameVersion* = "1"` (`src/rware/sim_types.nim:11`) is unchanged although rule-changing fixes
landed (F1/F3/F5/F15/F17/F18). **Advisory, not blocking.** No checklist item names GameVersion;
the item it could threaten (2, replay re-derivation) holds at head: the committed fixture was
re-recorded in the same commits that changed the rules (`git log --oneline -- tests/replays/rware.replay`
→ `4dd0143`, `ba75dbb`, `ae468ef`), test 27 sweeps every committed fixture for the current
GameVersion, and the head CI wasm smoke re-derives the fixture green. The hazard GameVersion
exists to prevent — a GV1 replay recorded under the old rules re-simulating wrong under the new
ones — requires a pre-fix replay to exist outside the repo, and none does: the coworld has never
been released and phase 40 has not run. Condition for staying advisory: **if any pre-`d5b5686`
replay ever surfaces (e.g. an early smoke artifact re-used as a fixture), GV must be bumped
before first release.** `tools/ci/check_gameversion.sh` guards only cross-branch collisions and
is silent on this case by design.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed `c7052f8` | pilot.nim hold path + test | yes |
| F2 | fixed `c4ce419` | floorPlanBlock in every request + retry, test | yes |
| F3 | fixed `4dd0143` | draw-before-clear, upstream-candidate test, fixture re-recorded | yes |
| F4 | documented `4b8b82d` | PATCHES #12 + PORTING + rename-only code change | yes |
| F5 | fixed `9330d32` | `id < result.shelf` tie-break + test | yes |
| F6–F9, F11, F12, F19 | documented | PATCHES #13–#18, #20 present, mirrored in PORTING-RWARE and embedded docs | yes |
| F10 | fixed `a9403df` | fixture drives shipped broadcast_core on main-thread canvas; head CI `29 drawn / 0 never inside` | yes |
| F13 | fixed `1cf37fc` | closed 7-cause enum, 429→transport_error, test | yes |
| F14 | fixed `4f8a79f` | budget from batch start, clamp, test | yes |
| F15 | fixed `ba75dbb` | union of all groups, clear-before-re-raise, test, fixture | yes |
| F16 | fixed `d98ac65` | counters from directive records, round-trip test | yes |
| F17 | fixed `ae468ef` | credited deliver finishes→parks, re-sweep to yieldAfter 4, fixture, test | yes |
| F18 | fixed `d05aea8` | turn-1 default = courteous's order, test | yes |
| F20 | fixed `751dc96` | `teamScore()` (no epsilon) in endcard, test | yes |
| F21 | fixed `a954be4` | zero MAGENT/45x45 matches at head | yes |
| F22 | fixed `2186a75` | new connects-then-never-answers block, assertions as claimed | yes |
| F23 | fixed `d5b5686` | rateRoom re-checked before retry batch, test | yes |
| "no test weakened" | claimed | confirmed from `git log -p -- tests/` (only the vacuous `or true` deletion + additions) | yes |
| CI green at head | claimed run 33081235780 | confirmed via `gh run list` / `gh run view` (success, all four jobs) | yes |

## Non-blocking observations (judge's own; tied to no checklist item)

- `sim.nim applyOrders:37-39` compares only `kind/shelf/station` when deciding whether an order
  is "the same" for `orderAgeTurns`/`lastResult` reset — a new `stow` to a *different* explicit
  cell is treated as the same order, so `order_age_turns` keeps counting and a stale
  `last_order_result` can be echoed for one observation. Observation-only fields (not hashed,
  not scored); cosmetic.
- `src/rware_warehouse_player.nim:35` cites "(r1 review F15)" for the constants-drift fix; the
  actual r1 F15 is the jam finding. Stale comment cross-reference only.
- The design note itself (design.md) still states the pre-divergence values (home-cell fetch,
  0.5 speed chip, 620 px, `game.docs` uri form, floor plan at registration, yieldAfter 6);
  `vendor/PATCHES.md` §"Divergences from the design note's viewer and packaging plan" is the
  reconciliation record. Acceptable — the note is a run artifact, the repo docs are shipped.

BLOCKING: 0
