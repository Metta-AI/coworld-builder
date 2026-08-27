blocking: 0

# r1 verdict — fog-of-war-boards
Head: 0e893df12ee180b31e95a5701a88c20a73e16745   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST (items 1–15)   Independent read written before reading fixes: yes
(Order followed: checklist → design note → repo at 0e893df + CI run 33033443296 read independently → r1-review.md → r1-fixes.md. The review was written at 791cf71; the fixer has since landed ten commits; everything below is verified at 0e893df.)

## Standing blocking findings

None. Both of the reviewer's blocking findings are fixed at the current head, and my independent
checklist pass found no new blocking finding.

## Refuted

### B1 — fixture asserts its remark is ≥ 20 runes, not full-length → REFUTED (fixed at head)
- True at the review's sha 791cf71; false at 0e893df. Commit `6d29819`.
- Evidence: `tools/ci/renderer_fixture.html:65` — `var SAY_RUNES = 80;` builds `fullSay` and
  `:346-349` asserts **exactly** the cap:
  `var runes = Array.from(node.textContent || "").length; if (runes !== SAY_RUNES) { problems.push("the say band at " + width + "px carried " + runes + " runes, not the full " + SAY_RUNES); }`
  — an equality against the full 80-rune cap at each of 360/640/1280 px, on both plates. A remark
  shortened at either end (fixture or renderer) now fails the fixture. CI at head: run 33033443296,
  job `wasm-viewer` (98391227190), step "Load the worst-case renderer fixture" →
  `{"loaded":true,"ms":3805,...}` — the exact-80 assertion held.

### B2 — fixture pads its remark with U+2026, so `ellipsized` permanently counts remarks → REFUTED (fixed at head)
- True at 791cf71; false at 0e893df. Commit `0d3679f`.
- Evidence: `tools/ci/renderer_fixture.html:101` — `while (runes.length < SAY_RUNES) runes.push("\u00b7");`
  (MIDDLE DOT, never U+2026, with the reason documented at `:89-95`), and the same commit adds the
  gate at `:355-358`: any `.plate-say` matching `/\u2026\s*$/` is a fixture **failure**
  ("the say band at … ellipsized a remark; widen the band rather than shortening the text").
  CI at head: the fixture step's line is
  `canvas text: 33 drawn, 0 never inside the canvas (0 draws crossed an edge), 2 ellipsized`,
  and both ellipsized samples are `"fog-of-war-boards-carto…"` — the nameplate `clampName` cut
  (`client/chrome_common.js:117-120`, a **label**, which checklist 15 explicitly allows). Zero
  remarks ellipsized; the signal is restored.

No other review finding was blocking. Of the non-blocking ones I re-verified at head: N1, N2, N4,
N5, N8, N11, N12 and N13(4th bullet) are genuinely fixed (see audit table); N3, N6, N7, N9, N10 and
the rest of N13 stand as observations and none maps to a checklist item as a violation.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1. CI green, no test loosened | PASS | `gh run list`: run **33033443296**, headSha `0e893df1…`, conclusion `success` (jobs: test 98391010442, docker-smoke 98391010252, wasm-viewer 98391227190). Test history for the whole run (repo born 2026-08-27): `git log --oneline -- tests/` = `a15121b` (initial) + `8689e63` (adds test 11b only); the `8689e63` hunk is pure addition — no assertion deleted, no tolerance widened, no skip/xfail anywhere in `tests/` (grep clean). |
| 2. Replay re-derivation | PASS | `sim.nim:748-810` `replayMatch` replays sense/attempt through the rules, re-derives and **checks** `attempt.result` (`:781-784`), `win.seat/how/path` (`:785-800`), out-of-turn (`:770-773`), and applies `evEnd` through the same `settle` (`:801-809`). `settle` is the single ending proc (`sim.nim:334-356`) on record and playback. Test 18 (`tests/test_replay.nim:97-111`) asserts frame-for-frame equality of `boardStateJson` for all five reason/ending pairs incl. `deadline/wall-clock`; test 19 asserts raises on five kinds of tampering. The wasm entry (`replay-viewer/fogboards_replay.nim`) runs the same `replayMatch`; the viewer draws from `states[index]` (`client/renderer.js:963-980`) — the re-derivation, not a parallel recording. |
| 3. Static viewer | PASS | `coworld_manifest_template.json:20-22` `"replay_viewer": {"bundle": "static-replay-viewer"}` inside `game`; `tools/build_replay_viewer.sh` present, mode `100755` (`git ls-files -s` = 100755), exercised in ci.yml:249. Shell fetches only the `?replay=` URL (`static_replay.js:67-89, 130-151`); assets are bundle-local (`assetBase: "./assets"`). No pod replay-viewer declared anywhere; the only `/client/replay` strings are the in-container HTTP route inherited from babel (`server.nim:526`) and a descriptive clause in `game.protocols.global` ending "never a pod". |
| 4. Both name spaces | PASS | Aliases: `tableNames` seeded shuffle of `CogNames` (`sim.nim:59-70`) reach the prompts (`llm.nim:391, 469-471`), `welcome`/`state`/`final` player frames (`server.nim:430, 107, 175-187`). Policy names ride spectator-side only: `policyNames` in snapshot (`server.nim:93`) and replay (`sim.nim:722-724`); viewer maps alias→policy for non-baseline seats (`chrome_common.js:75-107` `makeNameMap`/`isBaselineFiller`; `renderer.js` scorebug shows policy name + alias sub-label). Head smoke replay: `names: ["Flywheel","Bolt"]`, `policyNames: ["Sprocket","Gizmo"]`. |
| 5. Degrade-never-hang | PASS | Bounds, each read: LLM `client.curl.post(..., client.timeoutSeconds)` (`llm.nim:649`, 30 s default); one retry then baseline, `decide` never raises (`llm.nim:687-723`); player connect `while epochTime() < connectDeadline` (`server.nim:225-231`, 180 s); ply guard `epochTime() + guard > playDeadline → endEarly` with `guard = 2*llmTimeout+2 = 62` checked before any observation (`server.nim:216-217, 276-283`); spacing sleep bounded at 4 s; `turnDelayMs` clamped by `sampleEpisode`; shutdown grace fixed 20 s then `quit(0)` (`server.nim:38, 208-210`). No unbounded loop (each iteration settles or increments capped `plies`); no blocking read on the game side; player exits 0 on a dead socket (`fogboards_player.nim:64-90`). See non-blocking observation on the ≤ ~2.3 s theoretical worst-case overshoot past the 720 s mark (reviewer's N3). |
| 6. num_agents | PASS | `num_agents: 2` inside all four variants' `game_config` (manifest:439, 463, 487, 511) and `certification.game_config` (:533); never at variant top level (test 22, `tests/test_manifest.nim:39-61`, green at head). `tools/ci/docker_smoke.sh:110-151` enforces all four invariants pre-container with `SEAT-COUNT FAIL:` prefixes — present (:112-118), positive integer (:119-125), `len(certification.players)` (:129-134), `len(game_config.players)` (:135-140) — plus the independent `SMOKE_SEATS` cross-check (:146-151), scaffold-substituted default `2` (:54). Grepped the full docker-smoke log of run 33033443296: **zero** `SEAT-COUNT FAIL` matches; log carries `seats=2` and `all 2 player containers exited 0`. |
| 7. Scripted baseline full legal episodes | PASS | Test 13 (`tests/test_sim.nim:419-442`) parses the real manifest, plays all four variants + the cert fixture all-scripted to the natural end and asserts `results.reason == "complete"`. Test 14 (`tests/test_bot.nim:73-104`, 200 seeds × 4 variants × 2 baselines) asserts every attempt ∈ `legalAttempts` and every anchor ∈ `legalAnchors` at the moment produced, plus blindness via the `shadowed` fixture. Tuning evidence in lieu of a separate grid harness: the baselines are search-based (a `distToWin` 0-1-BFS minimiser and a corridor walker) with no free numeric constants beyond tie-breaks, and their strength is gated in CI — `probe vs random: mean score 1.0 (200/200 wins)` (test 15) and `probe/sweep disagreement: 1800/2450 = 0.735` ≥ 0.30 (test 16), both green in run 33033443296. |
| 8. LLM reply handling | PASS | `extractJsonObject` first `{` … last `}` tolerating fences/prose (`llm.nim:536-547`); `parseCellNode` tolerant spellings + `[col,row]` (`:549-591`); one retry with the printed legal set from the same procs the validator applies (`:677-685, 700-703`); legality probed on a copy (`:709-713`); fallback recorded — `fellBack = true` (`:723`), `fallbacks[mover] += 1` (`server.nim:312-313`), greppable `falling back` stdout line (`llm.nim:720-721`); surfaced in `results.fallbacks` for phase 60. |
| 9. Rune-safe truncation | PASS | One shared `cleanText` on `runeLen`/`runeSubStr` (`llm.nim:162-168`) applied to `say` 80 (after `oneLine`), `notes` 400, guess entries 4, delivered prompt 4000 (`server.nim:479`), and — since `c091f67` — every captured HTTP error body (`llm.nim:653, 661, 666`, `MaxErrorLen` 200). Test 20 (`tests/test_replay.nim:166-209`) feeds 400×`日`+`🜁`, asserts `validateUtf8(bytes) == -1`, strict `parseJson` round-trip, and an emoji exactly on the cap surviving whole. Viewer-side re-cap also rune-safe since `18fd340` (`renderer.js:642-650`). |
| 10. Manifest validates | PASS | `game.docs` = `{"readme":{"type":"text","value":…},"pages":[{"id":"rules.md","title":"rules.md","content":{"type":"text","value":…}}]}` (manifest:362-377); `game.protocols` carries both `player` and `global`, each `{"type":"text","value":…}` (:352-361). Test 24 green at head. |
| 11. Viewer legible at 360 px | PASS | `client/chrome.css:492-500`: `.plate-name { … flex: 1 1 auto; min-width: 3.2em; … }`; labels hidden under 640 px (`:596-606`: `.plate-label { display: none; } .plate-alias { display: none; }`); further 360 px block `:614-623`. Fixture asserts no `.plate-name` collapses below 24 px at 360/640/1280 (`renderer_fixture.html:367-371`), green at head. |
| 12. Release order and scaffold | PASS | `coworld-release.yml` step order: Build the Coworld manifest (:159) → Certify locally (:173) → Upload the policies (:212, "BEFORE upload-coworld") → Upload the Coworld (:310) → Put the Coworld secret (:348, "AFTER upload-coworld"); certify runs against the manifest `coworld build` produced in the same run (fresh image via compose). All three workflows present; `docker_smoke.sh` present + executable (100755, asserted in ci.yml:166-174); `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (:15). Placeholder gate run at head: `grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files matches nothing → gate exits 0. The surviving angle-bracket names are exactly the allowed four. |
| 13. Viewer executes | PASS | (i) run 33033443296 `wasm-viewer` green incl. "Load the bundle in a real browser" (`viewer_smoke.mjs`, headless chromium, `--timeout 90 --soak 10 --strict-text-bounds`) against the digest-matched `smoke-replay` artifact docker-smoke produced (sha256 `f4c821f5…` uploaded and downloaded); `needs: docker-smoke` at ci.yml:212; step present, not commented, no `continue-on-error`. Output: `{"loaded":true,"ms":289,"clock":"DARK HEX 5×5 · PLY 8 / 50 · SPROCKET TO MOVE",…}`, three differing scrub readouts, soak advanced (the `(null -> null -> null)` stdout prints only the absent `#tick`; the gate also reads `clock`/`scorebug`, `viewer_smoke.mjs:539-541`, and `moved` passed — a failure would have exited 1). (ii) `data-replay-loaded="true"` set on `documentElement` on the first drawn frame (`renderer.js:1028`, inside the frame loop after `renderer.draw`), `data-replay-error` set/removed in the shell (`static_replay.js:56, 107, 136`); the loaded-attribute-in-renderer placement is the design note's one named deviation and the smoke's `loaded: true` is the required evidence. (iii) `config.nims:38-39` `-s MODULARIZE=1 -s EXPORT_NAME=FogReplayModule` ↔ `static_replay.js:140` `FogReplayModule()` — same starter (diff vs babel `d55d999` shows only `Babel*→Fog*`/`_bab_*→_fog_*` + the documented `onFirstFrame` deviation); no `onRuntimeInitialized` in the tree. |
| 14. Chrome is the starter's | PASS | (i) I extracted every `BEGIN/END copied cogame-babel renderer.js N-M` region from `chrome_common.js` and diffed against `/workspace/starters/cogame-babel/client/renderer.js` at d55d999: regions 101-124, 680-733, 735-744, 1029-1048 byte-identical; 790-863, 963-970, 972-1027, 1142-1222 differ by exactly the six named edits (PLY head; injected `feedText`; attempt say sub-line; `markPlyBeat` loop; injected `endColumns` heads/cells/var; plies reason line) plus their marker comments — no unnamed divergence. Prelude (`:25-37`) is babel 23-31 + 85-87, kept private. Appended block in the pinned order; `chrome_scope_check.mjs` green at head (`20 exported chrome names, 59 game-block declarations, no overlap, 8 copied regions intact`). (ii) `replay_broadcast.html` = babel `replay.html` byte-for-byte + renames (title, wordmark, clock text, chrome_common script, `FogRenderer`) + one appended `<script>` block under the banner; 90 lines vs starter 74 — an append, nothing removed (same for global.html/player.html). (iii) `relayout()` sets `--band`/`--hudscale` on `document.documentElement` (`chrome_common.js:405-419`), runs on load/resize/feed-toggle; no `position: fixed` anywhere in chrome.css (grep clean); `#endscreen { bottom: var(--band, 0px) }` (`chrome.css:552`), shown via `#endscreen.show` (`:381`) which `updateEndscreen`'s unconditional `classList.toggle("show", !!show)` drives; every seek routes through `setIndex` which calls `updateEndscreen(show = index >= events.length)` (`renderer.js:988-990`); beats are labelled `<button type="button">` with aria-label/title/click-seek (`chrome_common.js:444-461`) and CSS exists for all five kinds + `.beat-attempt.occupied` + seat tints (`chrome.css:556-585`). (iv) `#viewpanel` absent everywhere (grep over client/, replay-viewer/, tools/ = 0 hits) — correct for fixed boards. |
| 15. Every drawn string fits | PASS | Main smoke: `canvas text: 9100 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — `never_inside == 0` gated by `--strict-text-bounds` on the step (ci.yml:320-325). Worst-case fixture ships (`tools/ci/renderer_fixture.html`), loads the **shipped** `index.html` in an iframe shimming only the wasm entry, feeds full-cap 80-rune says on both seats + 6-entry guesses per ply + longest policy names, drives 360/640/1280 px, asserts its own strings are still full-length (exact-80 equality, `:346-349`) and that no remark is ellipsized (`:355-358`), sets `data-replay-loaded`/`data-replay-error` on its own document, and is driven by its own ci.yml step (`:336-360`) with `--strict-text-bounds`. Its `canvas_text` line at head: `33 drawn, 0 never inside … 2 ellipsized` — both ellipses are the 24-char nameplate label cut, a design choice the checklist allows. |
| Simultaneous-batch rule | N/A — verified | The design note (§Sequential turns) declares every shipped variant strictly sequential, and it is a rules property: the next mover depends on whether this ply collided (`sim.nim:499-502`), so the next observation cannot be built before the current attempt is applied. One seat decides per ply (`server.nim:284-307`); sequential calls are correct here. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `6d29819` | `renderer_fixture.html:65, 346-349` — exact-80 equality against `SAY_RUNES`; fixture step green at head | yes |
| B2 | fixed, `0d3679f` | `:101` pads with `\u00b7`; `:355-358` fails on an ellipsized remark; head CI shows 2 ellipsized, both nameplates | yes |
| N1 | fixed, `8689e63` | `sim.nim:430-437` — only `sim.sensedEmptyAt[seat].del(cell)` on a fill; test 11b `[OK]` in both debug and release passes of job 98391010442 | yes |
| N2 | fixed, `655dc61` | `Decision.scripted` set by `scriptedDecision` (`llm.nim:325`), recorded by the server (`server.nim:324-326, 344-345`); head smoke replay: every attempt of both seats now `"scripted": true` (keyless run), `fallbacks == [0,0]` | yes |
| N3 | rebutted | Guard implemented exactly as design.md §Resolution-order step 2 / §arithmetic pins it (62 s, spacing not folded in); worst case ≈ 722.5 s settle, artifacts ≈ 723 s + 20 s grace, ~457 s before the platform kill; every wait bounded. Not a hang/timeout; checklist 5's operative clauses hold. I keep it non-blocking (recorded below) | yes |
| N4 | fixed, `b8cdac8` | `llm.nim:295-298` — `let start = sim.stones[seat]; for offset in start ..< n`; disagreement rose to 0.735, tests 7/13/14 green | yes |
| N5 | fixed, `c091f67` | `llm.nim:653, 661, 666` all `cleanText(response.body…, MaxErrorLen)`; the 160-rune inner caps rebuttal is sound (both already rune-safe via `runeSubStr`/`cleanText`) | yes |
| N6/N7/N10 | rebutted | Reviewer's own text already concedes each (note placement wrong not code; #clock edit required by "PLY n" intent, nothing removed; clamp documented, real gates are `clipped` + iframe canvas report) | yes |
| N8 | fixed (1st half) `e237df7` / rebutted (2nd) | `sim.nim:651` writes `round` for every event; head smoke replay opens `{"kind":"start","round":-1}`. End-event `round` value is pinned nowhere and no consumer reads it | yes |
| N9 | NEEDS-DESIGN | Band still constant-sized (`chrome.css:534-548`); checklist 15's gated number (`never_inside == 0`) and the CI measurement of the full-cap remark in the render font at three widths both hold. Non-blocking | yes |
| N11 | fixed, `654dfc2` | `renderer_fixture.html:300` `var textWidth`; parameter no longer clobbered | yes |
| N12 | fixed, `18fd340` | `renderer.js:642-650` `capSay` via `Array.from`; scope check still green | yes |
| N13 | fixed (4th) `0e893df` / rebutted (rest) | `server.nim:495-499` inner `try` around `parseBaseline` — prompt kept, `probe` fallback, reason on stdout; `parseBaseline` still raises on "mirror" (test green). The five rebuttals are each sound (template provenance; atomic ply; connect-failure should exit non-zero; 600 > 300 episodes; `0%` is the correct rendering of zero) | yes |

The fixer's claim "no test weakened" is confirmed independently: `git log -p 791cf71..0e893df -- tests/` is one added test block (11b), nothing removed or loosened.

## Non-blocking observations

- **Wall-clock worst case ~2.3 s past the 720 s mark** (reviewer's N3): the 4 s spacing sleep and
  `turnDelayMs` run after the 62 s guard check (`server.nim:276, 296-302, 352-353`), so a fast ply
  followed by a double-timeout ply can settle at ≈ 722.5 s of 1200 (60.2 %). Every wait is bounded,
  the design note itself pins the guard at 62 s without the spacing, expected episodes finish at
  7–18 % of budget, and artifacts + grace land ~457 s before the platform kill — an arithmetic
  rounding of the 60 % line, not a hang or timeout, so not counted.
- **`.plate-say` band sized by CSS constants** (N9): the runtime measurement the design note
  describes is instead performed in CI by the fixture at three widths against the real render font
  (`scrollHeight > clientHeight` on an exact-80-rune remark). Adequate for the checklist's gate.
- **No CI path exercises `sense > 0`**: the cert fixture and the renderer fixture are both
  `sense: 0`, so the sense-window overlay, `lens.png`, and the fading sensed-empty dot (the thing
  N1 fixed) render nowhere in CI. Unit tests 11/11b/14/18 cover the sense rules and re-derivation
  (a `deadline/wall-clock` recording on a `sense = 2` board re-derives frame-for-frame), and no
  checklist item names the overlay, so not blocking. A `recon-hex-5` fixture payload would settle it.
- **`coworld certify` runs without `--timeout-seconds 300`** (design.md says it passes it): the
  workflow is the template verbatim; test 17 pins the fixture's play at ~4 ms, far inside certify's
  60 s default. Checklist 12 does not require the flag.
- **LLM path never exercised against a live model in CI** (reviewer's "could not determine"): by
  design — docker_smoke runs keyless. The parse/retry/fallback ladder is unit-covered; a hosted
  episode in phase 40/60 is where this gets its first live evidence.

BLOCKING: 0
