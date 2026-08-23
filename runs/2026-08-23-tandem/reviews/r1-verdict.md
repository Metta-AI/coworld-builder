blocking: 1

# r1 verdict — tandem
Head: 668b5f5d81d5025a527391bb25f90cf2bc186d1d   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Read order followed: checklist → design note → the tree at 668b5f5 (fresh clone,
diffed against `/workspace/starters/coworld-ctf`) → my own notes → r1-review.md →
r1-fixes.md (consulted last, only to audit its claims). The review was written at
`4b78981` (pre-fix); every finding below is verified at the **current head**.

## Standing blocking findings

- [static-viewer] client/replay_broadcast.html:1460 the game block's labelled-button `markBeat` (line 2141) is dead code at runtime — `var markBeat = C.markBeat` executes after function hoisting and rebinds the name, so every scrubber beat renders as chrome_common's unlabeled, non-clickable `<div>` and no beat ever seeks on click (checklist 14d)

### B-J1 — scrubber beats are not labelled buttons that seek: the game block's `markBeat` is shadowed at runtime   (source: judge)
- Where: `client/replay_broadcast.html:1460` and `:2141`, one shared IIFE scope (`:1431` `(function () { 'use strict';` … `:2277` `})();`).
- Verified at head:
  - `:1460` — `var markBeat = C.markBeat, killMarkerTeam = C.killMarkerTeam, renderBeatMarkers = C.renderBeatMarkers;` (the starter's alias line, kept).
  - `:2141` — `function markBeat(tick, kind, team, label) { … var mark = document.createElement('button'); … mark.setAttribute('aria-label', text); … mark.onclick = function (ev) { ev.stopPropagation(); send('s:' + tick); }; … beatEls.push(mark); … }` (the game block's upgrade, appended below the banner).
  - JavaScript semantics: the function declaration is hoisted and initialised at scope entry; the `var` assignment at `:1460` then executes at script load and **rebinds `markBeat` to chrome_common's copy**. Every later call — `tandemIngestBeats` (`:2198`), `applyEvent`'s `doorway`/`drop`/`impact`/`delivered`/`wrecked`/`gameover` arms (`:2207,2211,2214,2218,2222,2225`) — therefore invokes `chrome_common.js:538 markBeat(tick, kind, team)`, which queues into `pendingMarkers`; `renderBeatMarkers` (`chrome_common.js:550-561`, called from `renderTransport` at `:473`) then creates `document.createElement('div')` markers with **no label, no `aria-label`, no `title`, and no click handler**. Reproduced in node with an exact structural replication of the page's scope (alias line, `'use strict'`, later `function markBeat` declaration, calls from an inner function): all calls land on the chrome copy; the game block's `beatEls` stays empty.
  - Consequences at head: (a) checklist 14(d)'s "scrubber beats are labelled `<button>`s that seek to their tick" is false in the running page — a click on a beat does nothing; (b) `applyTandemSpoilers` (`:2165-2176`, the r1-F13 fix, commit 5dd3c60) iterates the empty `beatEls` and is a no-op (spoilers still function only because chrome_common's own `applySpoilers`, `chrome_common.js:488-496`, gates the `div`s it created); (c) `tests/test_viewer.nim:99-123 beatsAreLabelledButtons` is a static source grep — it asserts the dead code's text (`"function markBeat(tick, kind, team, label)" in page`, `"document.createElement('button')" in page`) and cannot see the shadowing, which is why CI is green over a broken behaviour. The beat-kind CSS (`:1270-1275`) still colours the divs, and the F13 `ImpactBeatDamage = 20` filter (`replays.nim:96,400-405`) still holds because it is applied before `markBeat` is ever called — kinds and filtering survive; the button/label/seek behaviour does not.
  - The reviewer asserted the opposite in F13 ("Every marker is still a labelled `<button>` that seeks (checklist 14d satisfied)") and the fixer repeated it in the F13 fix note ("the markers it created"); both read the source statically. The design note (§Transport rules: "Scrubber beats are clickable, labelled `<button class="beat-marker <kind>">` elements … a click seeks to that tick") is explicit that the buttons are the intended behaviour.
- Checklist item: **14** — "(d) scrubber beats are labelled `<button>`s that seek to their tick … with CSS for every kind the page emits". CSS per kind: present. Labelled buttons that seek: absent at runtime.
- What settles it: rename the game block's function (e.g. `tandemMarkBeat`) or drop the `markBeat` alias from the `:1460` var list (it is unused by any surviving starter code — the starter call sites `applyEvent`/`ingestBeats` were deleted with the ctf game block), update the call sites, and make `tests/test_viewer.nim` assert something the shadowing would break (e.g. that `markBeat` is not in the `var … = C.markBeat` alias list while `function markBeat` exists in the same scope).

## Refuted

### B1/F1 — "the baseline tuning harness the code names does not exist in the tree" → REFUTED (fixed at head)
- Evidence: `tools/tune_baselines.nim` at 668b5f5 (9 359 bytes, committed in e8d0742/0763453; docstring commit 668b5f5) — `--eval` and `--sweep NAME=v1,v2,…` drivers over `baselines.TuningSeeds` (`src/tandem/baselines.nim:20`, the same 20 seeds `tests/test_baselines.nim:8` pins); `docs/BASELINE-TUNING.md` carries the shipped point and the sweeps (`TandemMuleEffort`, `TandemTwistGain`, `TandemOpenEffort` axes with delivery/score tables). The dangling `tune_porter.nim` reference is gone. Item 7's "tuned with a grid harness, not guessed" now has its artefact in the tree. The finding was true at 4b78981 and is fixed, therefore it does not stand.

The reviewer's fourteen non-blocking findings, verified at head (none stands as a defect; none was a checklist violation except where noted):

| finding | at head |
|---|---|
| F2 damage_last_turn always 0 | fixed — snapshot moved to the END of `turn()` (`decide.nim:475-478`), field computed at `:207`; asserted in `tests/test_engine.nim` |
| F3 byte-sliced provider text | fixed — `llm.nim:164-170 head()` uses `runeLen`/`runeSubStr`; all five call sites (`:177,185,190,201,211-212`) go through it |
| F4 drive repair precedence | fixed — `orders.nim:308-314`: missing/non-finite drive → last turn's unconditionally, fallback's only with no previous |
| F5 disconnect does not degrade | fixed — `server.nim:~610` sets `connected = false` on close; `decide.nim:351` skips the batch for `not policy.connected`; `tests/test_engine.nim:200 disconnectedSeatPlaysPorter` (old test kept as `noTransportSeatPlaysPorter:173`) |
| F6 >64 KiB registration dropped | fixed — `tandem_player.nim:24-55`: `PromptRuneCap = 4000` applied by `clipPromptRunes` before `chatPacket` builds the u16-length frame |
| F7 smoke checks only the game's exit | fixed — `docker_smoke.sh:250-268` waits out and asserts every `${prefix}-p<slot>` exit code; green-run log shows both `exited 0` |
| F8 vacuous physics assertions | fixed — `tests/test_physics.nim:148-151` asserts `normalMilliNewtons >= 0` and `<= ContactForceCap` from the solver's own log, `:162` friction-never-reverses, `:120` penetration ≤ 60 000 µm (note's bound), free-body loops at 480 ticks |
| F9 removals beyond the note's list | fixer's rebuttal VERIFIED — the ~1 900 deleted lines are ctf's game-specific JS (`ingestFpMap`, `renderPov`+raycaster, `onKill/onSteal/onReturn/onCapture`, ctf endcard rows, zoom/pan wiring for the removed `#viewpanel`), reading state tandem's stream does not carry. I diffed the whole page: CSS above the banner is the starter's minus exactly the `#povBadge`/`#fpv`/`#viewpanel` rules (hunk `528,833d527`); `relayout()` (`:1934-1979`), transport wiring, feed/banner queues, locker-room and endcard markup/CSS intact. Not the gridlock rewrite. Advisory only: the note's "exactly these" undersells the JS removals |
| F10 no route test | fixed — `tests/test_routes.nim` (new, 3a35bb5+6ce3d67) drives the real `runServerLoop`: `/healthz`, `/client/global`, `/client/player` (no socket open), `/global` to gameover, bad-token refusal, 15 s shutdown grace |
| F11 scrape "or" | fixed — `tests/test_replay.nim:222-227` asserts `"scrape" in rough` and `"scrape" in clean` separately (tightened, not loosened) |
| F12 end-check order | fixed — `sim.nim` step 10: Delivered → wrecked → out_of_time → fault, with the wall-clock stop in the server loop (EDIT 4); `tests/data/golden_hashes.json` untouched since 68e39b0 |
| F13 impact-beat filter page-only | fixed — `replays.nim:96 ImpactBeatDamage = 20`, applied where `beatEvents` is built (`:400-405`); `tests/test_replay.nim:159-191 beatsAreTheNotesBeats` pins it on a 41-and-14 fixture. (The spoiler-gate half of the fix is a no-op at runtime — see B-J1 — but spoilers still function through chrome_common's own gate) |
| F14 AGENTS.md absent | fixed — `AGENTS.md` (7 183 bytes) at head, linked from README |
| F15 double-escaped feed | fixed — `client/replay_broadcast.html:2122-ish` `row.textContent = line.text;`; `tests/test_viewer.nim:124-136` asserts no `textContent = esc(` |

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run **32671500679**, conclusion `success`, headSha `668b5f5…` (cited from `gh run list -R Metta-AI/cogame-tandem --branch main -w ci.yml`); jobs test/docker-smoke/wasm-viewer all success, no `continue-on-error` in ci.yml. `git log -p 68e39b0..HEAD -- tests/` read hunk by hunk: every change adds or tightens assertions (F8 contact assertions, F11 "or"→two asserts, new `test_routes.nim`, F3/F4/F6 new cases); no assertion deleted, no skip/xfail, no test file removed. One examined edge: 6ce3d67 widened `test_routes.nim`'s `/healthz` **startup wait** 60 s→300 s — a bound on a debug-build board bake (61 162 ms measured in the green run), not an assertion tolerance; the test is new this round, the assertion is unchanged, and the bound still fails a server that never listens. Ruled not a loosening |
| 2 replay re-derivation | PASS | `tests/test_replay.nim:70-89 replayReproducesEveryHash` re-simulates a recorded episode through `stepReplay` and asserts `hashMismatchTick == -1` over every tick plus equal damage/progress/deliveryTick; viewer runs the same `replay_runtime` compiled to wasm (`replay-viewer/tandem_replay.nim` imports `tandem/sim`); CI `Native/wasm determinism gate` step green in run 32671500679 ("ok: loaded tandem-smoke.replay, advanced 240 frames") |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, wired as the build hook (ci.yml:233-257); the bundle's only network call is `fetch(message.replayUrl)` (`static_replay_worker.js:113`). `/client/replay` appears only as the game pod's own inherited route in docs/protocol text, not as a viewer path |
| 4 both name spaces | PASS | board labels and LLM view built from `seatAlias()` only (`decide.nim:177-180`); real names in replay config roster, chrome roster and `results.names`; `tests/test_server.nim:122-149 twoNameSpaces` asserts both directions |
| 5 degrade-never-hang | PASS | every wait bounded: `turnBudgetMs` monotonic deadline + floored per-attempt allowances (`decide.nim:327-408`), bounded inter-batch sleep (`:299-311`), 660 s wall-clock stop inside the tick loop (`server.nim:738-743`), `lobbyJoinTimeoutTicks` (`:713-721`), 20 s shutdown grace, frame limiter ≤ 2 ms sleeps (`:373-384`), player container 90 s connect / 120 s receive bounds (`tandem_player.nim:32-48`); 660+20+hold < 720 s = 60 % of 1200; disconnect degrades to porter (`decide.nim:351-360`) |
| 6 num_agents | PASS | `num_agents: 2` in variant `default`, variant `sprint` and `certification.game_config`; `certification.players` len 2 = `game_config.players` len 2 (parsed from the manifest); `docker_smoke.sh:106-151` enforces all four invariants + the `SMOKE_SEATS` cross-check, each `SEAT-COUNT FAIL:`-prefixed; **grepped the docker-smoke log of run 32671500679: zero `SEAT-COUNT FAIL`**, `seats=2`, `smoke OK: seats=2 … reason=complete` |
| 7 scripted baseline | PASS | `tests/test_baselines.nim:13-45 boundedOrders` (500 states × 2 baselines, every field in range, compiled force ≤ MaxSeatForce), `:65-87 porterDelivers` (delivery on all 20 seeds), `tests/test_engine.nim:148,292` assert `endReason == reasonComplete`; grid harness `tools/tune_baselines.nim` + `docs/BASELINE-TUNING.md` committed (see B1 refutation) |
| 8 LLM reply handling | PASS | `extractJsonObject` fence/prose tolerant (`llm.nim:203-215`), one retry (`decide.nim:392 attempt <= 2`), then porter with `source = osFallback` and a `fallback` record with cause+detail (`:444-459`); `tests/test_orders.nim` covers prose, fences, percentages, object drive, NaN, boundary emoji |
| 9 rune-safe truncation | PASS | `orders.nim:72-86 clipRunes` (runeLen/runeSubStr), `capRecord` shrinks structurally (`:197-226`), `llm.nim:164-170 head()` rune-cuts captured errors, player prompt rune-capped at the transport (`tandem_player.nim:50-55`); `tests/test_orders.nim:95-109` feeds a 4-byte emoji at the cap and asserts `isValidUtf8`; `tests/test_replay.nim` forces non-ASCII say/label through the strict-UTF-8 summary |
| 10 manifest validates | PASS | `game.docs.readme` `{"type":"text",…}` (3 451 chars) + three pages with id/title/text content (9 605/6 428/3 711); `game.protocols` carries both `player` and `global` as text (parsed from the manifest at head); `tests/test_manifest.nim` asserts the same and CI test job is green |
| 11 legible at 360 px | PASS | `client/replay_broadcast.html:1172` `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }`; `:1307-1311` `@media (max-width: 640px)` hides `.strain-num, .plate-blame, .plate-alias, #arrowlegend`; `#stage.tiny` rules `:1297-1304` |
| 12 release order and scaffold | PASS | `coworld-release.yml`: build (:153) → certify (:167) → upload-policies (:206) → upload-coworld (:304) → secret put (:342); all three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 4 policies, champions `tandem-anchor` + `tandem-feather` both `PLAYER_PROMPT`, feather carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, fillers `porter`/`mule`; the three-name placeholder grep over the five files **exits 0** (run in the sandbox); the four expected angle-bracket runtime names are present where declared (`ci.yml:210` `<cow_id>/<sha>` etc.) and were not filed |
| 13 viewer executes | PASS | run **32671500679** `wasm-viewer`: `needs: docker-smoke` (ci.yml:220), step **"Load the bundle in a real browser"** ran and succeeded — log shows `{"loaded":true,"ms":3116,…}` and `soak: 12s of playback kept advancing ("2 / 948" -> "242 / 948" -> "290 / 948")`; `static_replay.js:152` sets `data-replay-loaded` on the first drawn frame, `:15-22` sets `data-replay-error` in `showFailure`; `config.nims` diff vs starter = `ctf_*`→`tandem_*` renames only, **no MODULARIZE/EXPORT_NAME**, worker is the starter's `var Module = {}` + `Module.onRuntimeInitialized` (`static_replay_worker.js:8,166`) — matched pair from the same starter |
| 14 chrome provenance | **FAIL (B-J1)** | `chrome_common.js` sha256 `7ace7287…d72f7c` on both copies — byte-identical; page is the starter's with the declared removals + banner-comment game block (full diff read; see F9); transport rules (a) `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (:1948-1976), (b) overlays ride `bottom: calc(var(--band, 0px) + 10 * var(--u))` (:1236,1250), (c) `#endcard { bottom: var(--band, 0px) }` (:741), shown via `#endcard.on` (:752/:2239), removed on every non-gameover frame i.e. every seek (:1803); `#viewpanel`/`#fpv`/`#povBadge` fully removed, board fixed-size so the removal is correct. **(d) fails at runtime — B-J1** |
| batching (simultaneous) | PASS | one `curly.makeRequests` batch per attempt carrying both seats (`decide.nim:244-274,388-408`); `tests/test_engine.nim` asserts the two in-flight windows intersect; seats never queried sequentially |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1/F1 | fixed (harness + docs) | `tools/tune_baselines.nim` + `docs/BASELINE-TUNING.md` + `TuningSeeds` at head | yes |
| F2 | fixed | snapshot at end of `turn()`; test present | yes |
| F3 | fixed | five rune-safe cuts via `head()` | yes |
| F4 | fixed | unconditional `elif hasPrevious` | yes |
| F5 | fixed | `connected` read in `turn()`, cleared on close; both tests present | yes |
| F6 | fixed | `clipPromptRunes` before framing | yes |
| F7 | fixed | per-player exit-code loop; green-run log confirms | yes |
| F8 | fixed | real contact log assertions, 60 000 µm bound, 480 ticks | yes |
| F9 | rebutted | rebuttal verified from the full page diff | yes |
| F10 | fixed (test) | `test_routes.nim` drives the real server; 300 s wait is a bound, not a tolerance | yes |
| F11 | fixed | two separate scrape asserts | yes |
| F12 | fixed | out_of_time before fault; goldens untouched | yes |
| F13 | fixed | half true: the beat-list filter is real and pinned; the spoiler-gate half (`applyTandemSpoilers` over "the buttons it created") is a **runtime no-op** — the buttons are never created (B-J1). Spoilers still work via chrome_common's own gate, so no separate spoiler defect stands, but the fix note's premise is wrong | partial |
| F14 | fixed | AGENTS.md present | yes |
| F15 | fixed | raw `textContent`, test pins it | yes |

The fixer's push-mechanism note (duplicated commit series via the Data API) checks out: the history carries each fix twice (`e8d0742…0d5fdc6` then `0763453…3a35bb5`), the net tree is single-application, no force-push, and CI is green on the head.

## Non-blocking observations

- The design note's §Chrome provenance "Removed starter elements (exactly these)" understates the (legitimate) ctf-game-JS removals (F9); note-wording only.
- `client/broadcast_core.js` differs from the starter in the `TANDEM_WIRE` identifier **and one comment line** (`src/ctf/sim.nim` → `src/tandem/sim.nim`, line 268); the note says "verbatim apart from the one `window.CTF_WIRE` identifier". Cosmetic.
- `tests/test_viewer.nim:99 beatsAreLabelledButtons` is a static text check that passes over the B-J1 runtime breakage; when B-J1 is fixed, the test should be strengthened to catch the shadowing pattern.
- Reviewer O5/O7/O8 (comment drift, `game.tags` absent with top-level `tags` present, `NIM_TESTS_RELEASE_ONLY` unset so `test_perf` runs in both modes and passes) re-verified at head; all advisory, none tied to a checklist item.

## Blocking items

- [static-viewer] client/replay_broadcast.html:1460 the game block's labelled-button `markBeat` (:2141) is shadowed by `var markBeat = C.markBeat` — at runtime scrubber beats are chrome_common's unlabeled, non-clickable `<div>`s and never seek on click; checklist 14(d) is false in the running page

BLOCKING: 1
