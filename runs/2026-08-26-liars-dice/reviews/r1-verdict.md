blocking: 1

# r1 verdict — liars-dice

Head: `8e74a8507cc36545686aea23a6ccdb8095a49eea` (main = origin/main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15, verbatim in the brief)
Independent read written before reading fixes: **yes** (repo, design note, CI run 33013575662 and
both job logs were read and my item-by-item notes were written before opening `r1-review.md`;
`r1-fixes.md` was opened only after every reviewer finding had been re-verified at head).
Review was written at `23da0888`; seven fix commits plus one test commit landed since
(`03c5d61..8e74a85`). Findings true at `23da0888` and gone at head are recorded as **resolved**,
not refuted.

---

## Standing blocking findings

### B1 — Checklist 7, second sentence: "The baseline's parameters were tuned with a grid harness, not guessed" — unverifiable from the tree or CI   (source: judge; reviewer flagged it under "Could not determine" without counting it)
- Where: `src/liars_dice/llm.nim:29-34` (the shipped constants: `BayesChallenge = 0.40`,
  `BayesSafe = 0.55`, `PressureChallenge = 0.25`, `PressureSafe = 0.35`) vs the absence of any
  sweep anywhere: `tools/` holds only `build_replay_viewer.sh` and `ci/`
  (`docker_smoke.sh`, `policies.json`, `viewer_smoke.mjs`, `build_renderer_fixture.sh`); `grep -rn
  -i 'grid|sweep|harness' tests/ tools/ src/` matches nothing relevant; the run's `log.md` and the
  design note record no sweep either.
- Verified at head: the in-tree evidence is `tests/test_bot.nim:132-151` ("calibration: two bayes
  seats beat two pressure seats", 4 seeds × 30 deals, `check bayesMean > 0.5` /
  `check pressureMean < 0.5`, green in the `test` job of run 33013575662). That is a head-to-head
  comparison of exactly **two** parameter points — it demonstrates the shipped pair beats the loose
  pair, but it is not a grid harness and no sweep over `(chal, safe)` combinations, no output
  table, and no cited tuning run exists in the tree. The reviewer wrote the same
  ("no grid harness in the tree", r1-review.md §Could not determine) and the fixer conceded it
  ("still unsupported in the tree … no finding was filed on it", r1-fixes.md §NOTED).
- Checklist item: **7** — "The baseline's parameters were tuned with a grid harness, not guessed."
  The binding rule in the brief: *a checklist item you cannot verify from the tree or from cited CI
  evidence counts as blocking — this is the only rule; there is no third status.* The first
  sentence of item 7 is fully verified (see the checklist pass); this sentence is not, so the item
  cannot be counted as passing.
- What would settle it: a committed harness (a test or `tools/` script that sweeps a grid of
  `(chal, safe)` pairs for both baselines and asserts the shipped pair is the winner or within
  tolerance of it, run in CI), or the harness's committed output table, or a cited run log showing
  the sweep that produced 0.40/0.55 and 0.25/0.35.

- [other] src/liars_dice/llm.nim:29 baseline thresholds have a two-point calibration test but no grid harness anywhere in the tree; tuning provenance unverifiable

---

## Refuted

### N1 — "the literal string `/client/replay` is present" → REFUTED as a checklist-3 violation
- The reviewer filed this non-blocking and left the weighting to the judge; I rule it does not
  falsify item 3. Evidence at head: `coworld_manifest_template.json:14-16` declares
  `"replay_viewer": {"bundle": "static-replay-viewer"}` and nothing else points a hosted replay at
  a pod; `src/liars_dice/server.nim:547` (`result.get("/client/replay", htmlHandler("replay.html"))`)
  is byte-for-byte the starter's live-server debug route
  (`/workspace/starters/cogame-babel/src/babel/server.nim:502`), and the manifest's `global`
  protocol sentence mentioning it mirrors the starter's own manifest (babel line 211). Item 3's
  target is a pod-served replay *viewer*; the declared viewer is the static wasm bundle,
  built by `tools/build_replay_viewer.sh` (mode 100755) and executed in CI. Filing the starter's
  own convention as a violation would indict the starter itself.

No other reviewer finding was refuted: B1, B2 and N2–N8 all reproduced exactly as written at
`23da0888` (I re-derived each from the pre-fix tree via `git show 23da0888:<file>` where needed),
and were then fixed — see Resolved.

## Resolved since the review (verified at head, not taken on the fixer's word)

| finding | verified at head |
|---|---|
| B1 (no worst-case renderer fixture) | `client/fixtures/worst_case.{html,js}` + `tools/ci/build_renderer_fixture.sh` (100755) + `renderer-fixture` job in ci.yml:363-419 with its own `viewer_smoke.mjs --strict-text-bounds` step. Run 33013575662 job 98325857248, step "Load the worst-case renderer fixture in a real browser" = success, output `{"loaded":true,…}` and `canvas text: 81665 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. Fixture drives the real `client/renderer.js` through `attachReplay`, holds `data-replay-loaded` until all seven sizes pass (worst_case.js:178-368), and fails unless every full-cap string reconstructs exactly (worst_case.js:259-300). |
| B2 (bands sized by eye) | renderer.js:143-144 mirror the server caps (`MAX_SAY_LEN = 140`, `MAX_NOTES_LEN = 400`); `capLines(ctx, usableWidth, cap)` (renderer.js:176-180) converts the cap into a line count via `measureText` in the actual band font (`advance`, renderer.js:165-172); `seatBlock` (renderer.js:188-230) reserves `sayLines`/`noteLines` from those caps and widens into `min(width/2 - 16, size*5.5)`; over-wide tokens are broken not ellipsized (`breakWord`). Gated by the B1 fixture: 0 ellipsized with four 140-rune says + four 400-rune notes at seven sizes. |
| N2 (mid-deal deadline used the seat's registered baseline) | server.nim:345-349: `deadlineForced` coerces `seatBaseline = "bayes"` for seats not registered scripted, exactly design.md:408. |
| N3 (`--band`/`--hudscale` never consumed) | chrome.css:552-557: `#loading { bottom: var(--band, 0px) }`, `#clock`/`.plate-name`/`.plate-score` font-size from `var(--hudscale, 1)` with `max(11px, …)` floors. |
| N5 (`.plate-pip.hollow` looked like a leftover) | chrome.css:507-517: declared inside the `liars-dice additions` block with the reason recorded (one hollow pip per loss, renderer.js emits it). |
| N6 (no `.seat5` rule) | chrome.css:490-494: `.seat5 { --tc: #e08a3a; }`. |
| N7 (`.end-panel` min-width 380px > 360px frame) | chrome.css:525-535: `@media (max-width: 480px)` sets `min-width: 0; max-width: 96%` and hides the two rate columns. |
| N8 (replay test pinned only the endpoint) | tests/test_sim.nim:522-568: snapshots the live `tableStateJson()` after every logged event and compares each with `replayMatch`'s frame at that index, asserting `compared >= events.len`. Green in run 33013575662; the commit is purely additive (`git log -p --since 2026-08-26T16:00:00Z -- tests/` shows +48/-0). |

N4 (canvas floors 8–11px vs the note's 11px sentence) and N9 (`clipText` rune-safe where babel
byte-sliced) stand as **non-blocking observations**: N4's gated half (checklist 11, the DOM
scorebug) is satisfied and its residue is a note-wording mismatch; N9's deviation is what
checklist 9 requires.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run **33013575662** on main, `head_sha = 8e74a850…`, conclusion **success** (gh api cited; jobs test 98325857228 / docker-smoke 98325856977 / renderer-fixture 98325857248 / wasm-viewer 98326205123 all success, every step success, no continue-on-error anywhere in ci.yml). `git log -p --since=2026-08-26T16:00:00Z -- tests/` shows exactly two commits: 0c5587c (initial drop, all additions) and 8e74a85 (+48/-0, a new test). No deleted assertion, no widened tolerance, no skip/xfail; `grep -rn 'skip\|xfail' tests/` empty. |
| 2 replay re-derivation, frame by frame, viewer uses it | **pass** | `replayMatch` (sim.nim:667-702) re-derives from the seed + events, cross-checks recorded deals against seeded deals (raises on mismatch), pre-seeds a recorded `deadline`; frame-by-frame test tests/test_sim.nim:522-568; wasm entry builds `states` only from `replayMatch` (replay-viewer/liars_dice_replay.nim:42-53) and tests/test_replay.nim:126-141 drives `buildReplayPayload` — the browser's exact code path — asserting last state == live state and results verbatim; the recorded artifact carries no `states` key (no parallel recording). |
| 3 static viewer | **pass** | manifest:14-16 `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, 100755, asserted executable and invoked by path (ci.yml:225-249); bundle's only network call is `fetch` of the `?replay=` URL (static_replay.js:76), assets relative and copied in (build_replay_viewer.sh:44-56). `/client/replay` at server.nim:547 is the starter's live debug route, not the declared viewer — see Refuted N1. |
| 4 both name spaces | **pass** | Prompts index `sim.names` (aliases) only (llm.nim:247, 367-403); `tableNames` seeds aliases (sim.nim:137-145); player frames carry aliases (server.nim:461-471, 205-218); `policyNames` in snapshot+replay (server.nim:92, 175); `makeNameMap` + `isBaselineFiller` map alias→policy spectator-side (renderer.js); results carry both `names` and `aliases`. |
| 5 degrade-never-hang | **pass** | connect wait bounded (server.nim:251-259, 180 s); every model call bounded by `llmTimeoutSeconds` through curly (llm.nim:442); ≤2 attempts (llm.nim:525); `callGuard = 2*timeout+5` before every call, deadline forces instant scripted play (server.nim:286, 345-349); deal bounded to 13 decisions by the bid cap (sim.nim `mustChallenge` + server.nim:327-333); deadline at deal boundary → `endEarly` (server.nim:308-318); pacing bounded (`turnDelayMs`, capped by `PacingBudgetMs`); artifact I/O bounded — curl.post(…, 60) at server.nim:141 and bitworld `readCogameUri`/`writeCogameUri` use curly's default `timeout = 60` (verified in `/root/.nimby/pkgs/curly/src/curly.nim:511`), which settles the reviewer's open item. 720 s = 60 % of 1200 s ceiling holds. |
| 6 num_agents + seat-count invariants | **pass** | `num_agents: 4` in `standard` (manifest:491), `poker` (520), `silent` (549), certification (576); schema 4..4 (68-73). docker_smoke.sh:110-151 enforces all four invariants (present / positive int with bool excluded / cert players len / game_config players len) plus the independent SMOKE_SEATS cross-check, every failure prefixed `SEAT-COUNT FAIL:`. Grep of the full docker-smoke log of run 33013575662: **0** occurrences; log shows `seats=4 … num_agents: 4`, `all 4 player containers exited 0`, `smoke OK: seats=4 … reason=complete`. |
| 7 scripted baseline full legal episodes; params grid-tuned | **BLOCKING (second sentence only)** | First sentence pass: tests/test_bot.nim:82-112 runs both baselines over 4 seeds × 2 modes × 2 talk × 3 seat counts to the natural end, `check sim.reason == "complete"`, and `playBaselines` (36-79) asserts every action legal and accepted first time (legalBid, ranges, raise window, bid cap, empty say/notes). Second sentence: **no grid harness exists in the tree** — see standing finding B1. |
| 8 LLM reply handling | **pass** | `extractJsonObject` extracts the first `{…}` from prose (llm.nim:407-417); action synonyms + numeric strings (llm.nim:471-500); retry once with the reason against a probe copy (llm.nim:525-547); fallback to scripted recorded as `fallback = true` (llm.nim:554-556; server.nim:373-379) and serialised on the event (sim.nim `eventToJson`), so phase 60 can count it. Asserted at tests/test_bot.nim:154-243. |
| 9 rune-safe truncation | **pass** | `cutRunes` (sim.nim:120-127) behind `cleanSay`/`cleanNotes`; prompt cap via `runeSubStr` (server.nim:513-516); `clipText` for error heads (llm.nim:69-72). Multi-byte-at-cap tests: test_sim.nim:416-437, test_bot.nim:216-219, and whole-payload `validateUtf8(payload) == -1` at test_replay.nim:121-123. |
| 10 manifest validates | **pass** | `game.docs` = `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}` (manifest:386-401); `game.protocols` carries both `player` (377-380) and `global` (381-384). |
| 11 viewer legible at 360 px | **pass** | `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (chrome.css:506); labels hidden under 640 px (`@media (max-width: 640px) { .plate-label { display: none } .plate-pips { display: none } }`, chrome.css:521-524); plus scorebug 2-col under 720 px and the N7 endscreen fix. |
| 12 release order and scaffold | **pass** | coworld-release.yml: Build the Coworld manifest (159) → Certify locally (173) → Upload the policies (212) → Upload the Coworld (310) → Put the Coworld secret (348). All three workflows present; docker_smoke.sh 100755; policies.json = 2 PLAYER_PROMPT champions + 2 PLAYER_SCRIPTED fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (policies.json:15). Placeholder gate run at head: `grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files matches nothing → gate exits 0. docker-smoke builds the image in the same job before the smoke runs (ci.yml:177-185). |
| 13 viewer executes | **pass** | wasm-viewer `needs: docker-smoke` (ci.yml:212); run 33013575662 job 98326205123 step "Load the bundle in a real browser" ran and succeeded (no continue-on-error), loading the replay docker-smoke produced: `{"loaded":true,"ms":298,"clock":"DEAL 0 / 3",…}`. Link flags (config.nims:43-46: `-s MODULARIZE=1 -s EXPORT_NAME=LiarsDiceReplayModule`, `_ld_*` exports) and the shell's factory call `LiarsDiceReplayModule()` + `_ld_*` (static_replay.js:94-104, 138) are a matched pair from the same starter; no `onRuntimeInitialized` anywhere. `data-replay-loaded` set by renderer.js:1579 after the first synchronous draw; `data-replay-error` set by static_replay.js:56 on every failure path. |
| 14 chrome is the starter's | **pass** | Babel lineage; the design note's file mapping applies (chrome_common.js → renderer.js + chrome.css; replay_broadcast.html → replay.html / index.html). chrome.css = starter byte-identical above the banner except the removal of the babel tail block the note names, + one appended block under `liars-dice additions to the inherited cogame-babel chrome`. index.html/replay.html = starter's page + renames + appended relayout block under the same banner (63 vs 53 lines — no rewrite). renderer.js keeps the starter's chrome machinery (drivers, scrub, feed, scorebug, endscreen, name map, effects) with the named removals, the two named patches (labelled `<button class="beat-marker …">` seeking via the shared `onSeek`, renderer.js:1448-1460; `relayout()` on `document.documentElement`, renderer.js:1250-1260) and the checklist-15-driven band sizing of B2. Transport: (a) `--band`/`--hudscale` on `:root`, now consumed; (b) no fixed-position element in the appended block; `#loading` rides `bottom: var(--band, 0px)`; (c) `#endscreen` is `inset: 0` inside `#board-wrap` (the transport's flex sibling), shown with the class its rule uses (`#endscreen.show`, chrome.css:381 / renderer.js:1184) and every seek path routes through `setIndex` → `updateEndscreen(…, index >= events.length …)` (renderer.js:1544-1548); no keyboard seek exists in this lineage (none in the starter either); (d) all five emitted beat kinds have rules (chrome.css:460-482 + seat colours incl. the new `.seat5`). Zoom/minimap: absent entirely (fixed arena), matching the starter. |
| 15 every drawn string fits | **pass** | wasm-viewer smoke: `canvas text: 2474 drawn, 0 never inside, 0 ellipsized` with `--strict-text-bounds` in the step (ci.yml:314-318). The repo draws LLM text, and the required worst-case fixture now exists and is gated in its own step: renderer-fixture job, `canvas text: 81665 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — full-cap 140-rune say on all four seats + full-cap 400-rune notes with an unbreakable token, animations played to settle, seven sizes down to 360×640, the fixture asserting its strings reconstruct exactly and holding `data-replay-loaded` until all sizes pass. Bands are sized from `MaxSayLen`/`MaxNotesLen` measured in the drawn font (B2). `total` is nonzero in both smokes. |
| simultaneous-batch rule | **n/a — pass** | The design note states the game is strictly sequential (design.md:379-383: "Sequential, not simultaneous … one model call per turn"); `decide` is called once per turn for the acting seat only (server.nim:353-354). |

---

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, 03c5d61 | fixture + job + green step + 81665/0/0 canvas_text at head; fixture holds the load signal and asserts exact reconstruction | yes |
| B2 | fixed, e8d76ee | capLines/advance derive bands from MAX_SAY_LEN/MAX_NOTES_LEN in the drawn font; breakWord; gated by the B1 fixture | yes |
| N1 | DISPUTED, no change | I refute the finding as a checklist-3 violation (starter's own route; manifest declares the static bundle) | yes |
| N2 | fixed, 9afcb37 | server.nim:345-349 coerces to bayes on deadline for non-scripted seats | yes |
| N3 | fixed, 3da045a | chrome.css:552-557 consumes both variables | yes |
| N4 | DOM half fixed, canvas half disputed | 11px floors on `#clock`/`.plate-name`/`.plate-score`; canvas floors unchanged; gated item 11 satisfied; residue is note wording | yes |
| N5 | fixed (note-side), 0c346d8 | `.plate-pip.hollow` declared in the game block with rationale | yes |
| N6 | fixed, 61b58c1 | `.seat5` rule present | yes |
| N7 | fixed, 834ee50 | 480px media block present | yes |
| N8 | fixed, 8e74a85 | frame-by-frame test present, additive only, green | yes |
| N9 | DISPUTED, no change | rune-safe clipText is what item 9 requires; reverting would be perverse | yes |

The fixer's push note (Git Data API replay of eight commits) is consistent with what the tree
shows: `main == origin/main`, eight commits since 23da088, `100755` preserved on
`tools/ci/build_renderer_fixture.sh` (git ls-files -s verified).

## Non-blocking observations

- N4 residue: design.md:700-701's "no drawn string smaller than 11 px" is true of the DOM HUD
  only; canvas floors remain 8–11 px by `layout.scale`. Note wording vs code; item 11 is satisfied.
- N9: `clipText` deviates from babel's byte slice in the direction item 9 requires.
- The caps are mirrored as literals in renderer.js (`MAX_SAY_LEN`/`MAX_NOTES_LEN`) with the
  `sim.nim` line cited but no build-time assertion that they agree (fixer's own NOTED item).
- Worst-case crowding at ≤640 px: dense but in-frame and un-ellipsized (gated by the fixture);
  the north seat's alias can sit dimmed under the bid plate at some sizes.

BLOCKING: 1
