blocking: 0

# r1 verdict — cogiavelli
Head: 044223b09cd2a66355e6866946226b08f4f690c3   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

I read the repo, the design note, the CI run and the manifest, and wrote my independent
checklist notes **before** opening `r1-review.md`. I did **not** read `r1-fixes.md` before
writing this verdict; the fixer audit below is against the commits on `main` themselves
(their messages carry the finding numbers), not against the fixer's self-report.

## Standing blocking findings

**None.** The review reported zero blocking findings; my independent pass confirms all
fourteen checklist items plus the simultaneous-batch addendum at the current head, from the
tree and from cited CI evidence.

## Refuted / resolved review findings

The review (written at f6862a3) had no blocking findings, so there is nothing to refute in
the blocking sense. Its material non-blocking findings divide into **resolved at head** (true
when written, fixed by a later commit — resolved, not refuted) and **standing, advisory**
(true but tied to no checklist item). I re-verified every one at 044223b:

### Resolved by commits on main (verified in the code at head)
- **N1** (replayMatch never compared board snapshots) → resolved by 541e04a.
  `src/cogiavelli/sim.nim:1490-1546`: `evStart`/`evSeason`/`evCities`/`evWinter`/`evEnd` now
  compare `units`, `owners`, `treasury`, `cityCounts`, `gained`/`lost` and the conqueror
  against the re-derivation and raise (`"recorded season board disagrees with the
  re-derivation"` etc.). `tests/test_sim.nim` block `replayChecksEveryRecordedBoardSnapshot`
  tampers a unit, a ducat, a city and a Winter board and asserts each raises.
- **N2** (rebellion-roll length mismatch accepted) → resolved by 5b1117c.
  `sim.nim:1527-1534`: the length is checked first and raises; then every roll AND city is
  compared. Test tampers the length and asserts the raise.
- **N3** (pledges judged post-movement) → resolved by d8650a5. `sim.nim:560-564`:
  `pledgeStabs(sim, board)` takes the **pre-movement** board explicitly ("judged on the
  orders as they were WRITTEN, against the board they were written on") and is called at
  `sim.nim:785` with `preMovement`, before `runRetreats()` at 786. Test
  `pledgeStabsAreJudgedOnTheBoardTheOrdersWereWrittenOn` asserts a successful supported stab
  into non-city Mantua is stamped.
- **N4** (ledger capped by 40 lines, not two years) → resolved by 9b280f5.
  `llm.nim:512-521`: `ledgerText` now windows `sim.history` to `2 * SeasonsPerYear` resolved
  seasons; the 40-line clip survives only as a prompt-size bound inside that window.
- **N5** (dead `defence` term in the bribe menu) → resolved by 4ceef19. `llm.nim:619-633`:
  `bribeMenuText` quotes `BribeDisbandCost`/`BribeBuyCost` directly; no dead variable.
- **N6** (famine rejection sampling) → resolved by 7507cdd. `sim.nim:314-320`: draw without
  replacement, "EXACTLY FamineProvinces draws"; test re-derives the first two draws of the
  seeded stream by hand and asserts equality.
- **N8** (conquest tie decided by loop order) → resolved by b583f2c. `sim.nim:446-457`: the
  leader is the largest holding ≥ 12 and a dead-level split goes to the lower power index;
  test `conquestTieGoesToTheLowerPowerIndex` splits 12/12 and asserts the winner.
- **N14** (test accepted `"conquest"` alongside `"complete"`) → resolved by 94e3264, a
  **tightening**: `auditEpisode` now asserts the branch it is in (a named conqueror must
  actually hold ≥ 12 cities or be the last holder; no conqueror ⇒ `"complete"` AND all years
  played), and a new canonical one-year all-scripted block asserts
  `results.reason == "complete"` outright — the letter of item 7.
- **N15** (endcard missing `stabs` column; static ledger) → resolved by 64e7bee + d7d9792.
  `client/renderer.js:2484-2513` (`stabCounts`, `>stabs<` header), `renderer.js:2585`
  (`animateEndcard`, one ledger year per second); `chrome.css:648` seven-column `.end-rows`;
  `tests/test_viewer.nim` block `endcardColumnsAndLedger` asserts all of it.
- **N17** (player spectate read unbounded) → resolved by 35b997b.
  `src/cogiavelli_player.nim:32-34,71-78`: `receiveMessage(ReceivePollMs=5000)` polled inside
  a deadline of `COWORLD_TIMEOUT_SECONDS` (default 1200) + `SpectateGraceSeconds=120`. No
  unbounded read remains anywhere in the tree.
- **N18** (ASCII hyphens in the mandated system prompt) → resolved by a536c21.
  `llm.nim:662-680` now carries the note's em dashes ("they arrive, always — this is the only
  promise…", "a roll of two dice — beat the roll…", "nothing else — no analysis…").
- **Could-not-determine §1** (no grid harness for the baseline constants) → resolved by
  cdbce86 + 6d55306 + 044223b. `tools/tune_baseline.nim` (the sweep), `docs/tuning.md` (both
  grids recorded in full, shipped point marked), `tests/test_tuning.nim` (fails unless
  `ShippedBaseline` is still the argmax of both grids AND the record names it), and a
  `--check` step in `ci.yml`'s test job — which I confirmed ran green in run 32731615199
  ("Sweep the scripted baselines' parameter grid", `test_tuning: ok` debug and release). The
  shipped constants (`llm.nim:88-96`) are the fitted point, and the fix commits honestly
  record that the note's original figures were NOT the argmax (0.1806 vs 0.1836; 0.0786 vs
  0.1063) and were replaced — the opposite of a rationalised record.

### Standing but advisory (verified true at head; tied to no checklist item)
- **N7** third cycle-breaking fallback (`adjudicate.nim`, cycle neither all-moves nor
  convoyed) — a termination guarantee; it is why item 5's "no unbounded loop" holds.
- **N9** vocabulary: an underpaid bribe still records `outcome == "defended"`
  (`money.nim:144-149` default) — the note's four-word vocabulary has nowhere else to put
  it; 25b7bfa fixed the misleading **feed line** ("That is under the price and the bribe
  fails" when `defence == 0`). The event schema is the note's. Advisory.
- **N10** two setup RNG streams (aliases `*6779+31`, permutation `*7919+17`) — both pure
  functions of the seed; determinism tested. Advisory note-wording divergence.
- **N11/N12/N13** (server-side assassin clamp, unused `AssassinFaces`, extra mapdata
  exports) — verified, all cosmetic.
- **N16** `feed-end`/`feed-it` classes — both defined in the inherited babel chrome; no
  emitted class lacks a rule.
- **N19** `player.html` connects the websocket from the served page — the route handler
  itself serves a file and never upgrades; babel's page, inherited.
- **N20** the note's "land graph connected" sentence is self-contradictory (Sicily); the
  test asserts the correct two-component fact. Code right, note wrong.

Nothing in the review was wrong about the code as of the sha it named. **Refuted: none;
resolved: 12; standing advisory: 8.**

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run **32731615199**, workflow CI, `headSha 044223b09cd2a66355e6866946226b08f4f690c3`, `conclusion: success` (gh run view --json). Jobs: test ✓, docker-smoke ✓, wasm-viewer ✓. `git -C /workspace/build/cogame-cogiavelli log -p --since="2026-08-24T10:21Z" -- tests/`: 7 test files **added** at f6862a3, then only additive commits (541e04a, 5b1117c, d8650a5, 7507cdd, b583f2c, 94e3264, 64e7bee, d7d9792, 6d55306); every hunk read — N14's change **tightened** an assertion, d7d9792 moved a string literal into a const with the assertion unchanged. No skip/xfail/deleted assertion/widened tolerance anywhere. Test-job log shows all 8 `tests/*.nim` ran debug AND release plus the tuning `--check`. |
| 2 replay re-derivation | **pass** | `sim.nim:1457-1552` `replayMatch` re-runs press/orders through the rules and raises on any disagreement in draws AND board snapshots; viewer wasm (`replay-viewer/cogiavelli_replay.nim:38-39`) calls the same `replayMatch` → `tableStateJson()` — display from the re-derivation, not a parallel recording. Tests: `replayFrames` (frames = events+1, final frame byte-equal), `replayRaisesOnAnAlteredDraw`, `replayChecksEveryRecordedBoardSnapshot`. |
| 3 static viewer | **pass** | `coworld_manifest_template.json` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` committed mode 100755 (`git ls-files -s`), conventional `coworld build` hook path, asserted executable by ci.yml; `static_replay.js` fetches only the `?replay=<url>` bytes (20 s AbortController bound) and relative assets. No `/client/replay` pod path declared anywhere in the manifest (the string appears only inside the `global` protocol's descriptive text). |
| 4 both name spaces | **pass** | Prompts address power names only; `tests/test_sim.nim` `policyNamesNeverReachAPrompt` scans all three builders for all six policy names. Welcome/state/final frames carry aliases (`server.nim:442-450, 229-244`). Replay carries `names` + `policyNames` + `powers` (`server.nim:187-213`); viewer `makeNameMap` (`renderer.js:701-728`) shows policy names for non-baseline seats, aliases for fillers — the CI viewer smoke's scorebug readout ("FLORENCE Sprocket …") shows the mapping live. |
| 5 degrade-never-hang | **pass** | Connect wait ≤ `playerConnectTimeoutSeconds` (`server.nim:274-280`); one `makeRequests` batch bounded by `llmTimeoutSeconds` (llm.nim:973), ≤ 2 attempts; `PlayBudgetFraction = 0.6` ⇒ 720 s of 1200, checked before every batch (`server.nim:301-326`), past it `endEarly()` ⇒ `"deadline"`; pacing capped by `PacingBudgetMs` (`sim.nim:195-206`); artifact POST bounded 60 s (`server.nim:181`); shutdown grace fixed 20 s; player spectate read now polled + deadline-bounded (`cogiavelli_player.nim:71-78`, fixed this round). No unbounded loop or blocking read found in the tree. |
| 6 num_agents | **pass** | `num_agents: 6` in `standard`, `gunboat`, certification fixture, and config_schema (`integer, min 6, max 6`); `docker_smoke.sh` enforces all four invariants with `SEAT-COUNT FAIL:` exits before any container starts, plus the `SMOKE_SEATS=6` cross-check. Grep of run 32731615199's docker-smoke log for `SEAT-COUNT FAIL`: **zero hits**; log prints `game=cogiavelli seats=6 … "num_agents": 6` and `smoke OK: seats=6 … reason=complete`. |
| 7 scripted baseline full episodes, tuned | **pass** | `tests/test_bot.nim` `theCanonicalScriptedEpisodeCompletes` asserts `resultsJson()["reason"] == "complete"` on an all-scripted table; `auditEpisode` asserts empty `illegal` lists, one order per unit, no self-standoff, spend ≤ 6 and affordable at write time, legal builds, non-negative treasuries, all years played. Grid harness: `tools/tune_baseline.nim` + `docs/tuning.md` + `tests/test_tuning.nim` + ci.yml `--check` step, all green in run 32731615199. |
| 8 LLM reply handling | **pass** | `extractJsonObject` (first `{` … last `}`) tolerates fences/prose (llm.nim:746-757); `for attempt in 0 .. 1` = exactly one retry with `InvalidHint` (llm.nim:960-970); fallback to `scriptedAction(…, skCondottiere, …)` with `scripted = true` (llm.nim:989-992), recorded on the event (`sim.nim:379, 859`; serialised `"scripted": true` at 1160-1161) so phase 60 can count it. Tests in `test_bot.nim` cover fenced, prose-wrapped, missing-key, oversize, non-integer amount, unknown action, no-object. |
| 9 rune-safe truncation | **pass** | `cleanText` (`sim.nim:100-106`, `runeLen`/`runeSubStr` + `…`) is the sole truncator, applied to every recorded string incl. `illegal[].raw` and the 4000-rune player prompt; `tests/test_sim.nim` `runeSafeCaps` feeds `é—😀`×900 at the caps and asserts `validateUtf8 == -1`; `test_viewer.nim` asserts the whole payload and every re-derived frame. |
| 10 manifest validates | **pass** | `game.docs` = `readme {"type":"text","value":…}` + `pages` `[{id,title,content:{"type":"text","value":…}} ×2]` (rules.md, map.md); `game.protocols` carries both `player` and `global`, each `{"type":"text","value":…}` (verified by parsing the JSON). |
| 11 viewer legible at 360 px | **pass** | `client/chrome.css:498` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` (asserted by test_viewer); `@media (max-width: 640px)` hides `.plate-ducats, .plate-cities` (chrome.css:663); 420 px two-column scorebug. |
| 12 release order and scaffold | **pass** | `coworld-release.yml`: Build the Coworld manifest (153) → Certify locally (167) → **Upload the policies** (206) → Upload the Coworld (304) → Put the Coworld secret (342), in order, certify against the just-built artifact in the same job. Three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 (`cogiavelli-borgia`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, all four env blocks carry `USE_BEDROCK`. I ran the exact three-name placeholder gate: **no matches, exit 0**. |
| 13 viewer executes | **pass** | Run 32731615199 `wasm-viewer` job (ID 97445337660) green **including** the `Load the bundle in a real browser` step, which printed `{"loaded":true,"ms":302,"clock":"SPRING 1499 · ORDERS · FLORENCE",…,"feed_lines":68}`, `soak: 10s of playback kept advancing`, and three distinct scrub readouts (0/50/100 %). No `continue-on-error` in ci.yml; `wasm-viewer` declares `needs: docker-smoke` and loads the replay docker-smoke produced (artifact sha256 logged). `viewer_smoke.mjs` byte-identical to the coworld-builder template. Markers: `data-replay-loaded` set at the end of `attachReplay`'s first-draw callback (`renderer.js:1396`, babel's line kept), `data-replay-error` set by `fail()` (`static_replay.js:56`), cleared on retry. Link flags and bootstrap from ONE starter: `config.nims` `-s MODULARIZE=1 -s EXPORT_NAME=CogiavelliReplayModule`; shell calls the factory `CogiavelliReplayModule()` (`static_replay.js:149`) with babel's `_malloc`/`HEAPU8.set`/`_cog_load_replay` handshake; zero `onRuntimeInitialized` in the tree. |
| 14 chrome is the starter's | **pass** | `client/chrome.css` vs starter: **0 lines removed**, one appended block (444-690). `client/renderer.js` vs starter: **0 lines removed**, 2 lines extended in place (feed-class append at 851-854; `stepMs` routing at 1372-1374 — both additive at named hook points, per the note's "extend the existing switches" rule), everything else appended after the starter's closing `})()` under the `// ---------- Cogiavelli ----------` banner, ending `window.CogiavelliRenderer = window.BabelRenderer` (2656). `client/replay.html` vs starter: title/wordmark text, renderer alias, `relayout()` bootstrap, **one appended `#ducatbar`**, zero elements removed (all 20 starter ids asserted by test_viewer). Transport: (a) `relayout()` measures `#transport` and sets `--band`/`--hudscale` on `document.documentElement`, calling `fit()` inside (replay.html:49-61, index.html same); (b) zero `position: fixed` anywhere; overlays live in `#board-wrap`; `#loading { bottom: var(--band) }` (chrome.css:640); (c) `#endscreen` absolute inset:0 inside `#board-wrap` (ends at the band), toggled with the `show` class its rule uses, and `setIndex` calls `updateEndscreen` on **every** index change (renderer.js:1358-1359) so every seek takes it down; (d) beats are `<button type="button" class="beat-marker <kind>">` with title/aria-label/label-span and an onclick seek (renderer.js:2434-2446), with an appended CSS rule for **all twelve** kinds incl. the derived `stab`. `#viewpanel` absent from the whole tree (and test-asserted absent). |
| addendum: one parallel batch | **pass** | `decideAll` builds one `RequestBatch` over all open seats and makes **one** `curl.makeRequests(batch, timeout)` call per attempt (llm.nim:963-973) — the only `makeRequests` in the tree; driven once per phase from `server.nim:342`. Never seat-by-seat. |

## Fixer report audit

I did not read `runs/2026-08-24-cogiavelli/reviews/r1-fixes.md` before writing this verdict.
The audit below is of the fix **commits** on main against the review's findings:

| finding | commit(s) | I verified at head | agrees with commit claim |
|---|---|---|---|
| N1 | 541e04a | board snapshots compared, raises; tamper tests | yes |
| N2 | 5b1117c | length checked first, roll+city compared | yes |
| N3 | d8650a5 | pre-movement board passed explicitly, called before retreats; stab test | yes |
| N4 | 9b280f5 | two-year history window in `ledgerText` | yes |
| N5 | 4ceef19 | dead `defence` gone from the menu | yes |
| N6 | 7507cdd | draw without replacement, exactly 2 draws; hand re-derivation test | yes |
| N8 | b583f2c | largest-holding then lower-index tie-break; 12/12 test | yes |
| N9 | 25b7bfa | feed wording fixed; event vocabulary (deliberately) unchanged | yes |
| N14 | 94e3264 | assertion tightened, canonical `complete` block added — nothing widened | yes |
| N15 | 64e7bee, d7d9792 | stabs column, `animateEndcard`, 7-column grid, per-year ledger; test | yes |
| N17 | 35b997b | polled read + episode-timeout+grace deadline | yes |
| N18 | a536c21 | em dashes restored in the mandated block | yes |
| item 7 (CND §1) | cdbce86, 6d55306, 044223b | harness + record + test + CI `--check`, green | yes |

## Non-blocking observations (judge's own)

- `design.md:602-603` says a seat that never delivers a prompt "plays condottiere for the
  whole episode"; in `server.nim` such a seat has `scripted = skNone` and an empty prompt, so
  with credentials present it plays the **LLM with no operator guidance** rather than the
  scripted baseline. Bounded either way (the connect wait and every batch are bounded), so no
  checklist item is falsified. Advisory design-note divergence.
- The reviewer's could-not-determine §2 stands as shape: all frames attached to one
  season's intra-resolution events (`spend`, `bribe`, `battle`, `cities`, …) are the same
  post-cascade state, since the closing `applyOrders` runs the whole cascade in one call.
  The feed/clock/effects read the events themselves, babel has the identical shape, and the
  CI soak + three-point scrub readouts all advanced — no checklist item touches it.
- `readCogameUri`'s file branch (reviewer CND §3) is a one-shot regular-file read wrapped in
  `except CatchableError`; the HTTP branch has curly's 60 s default. I count item 5 verified.

BLOCKING: 0
