blocking: 0

# r1 verdict — grf-football

Head: `f810b0fbe5e2ad349667330edbc5207f5baf30a6` (verified: `git -C /workspace/cogame-grf-football rev-parse HEAD`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-batch rule)
Independent read written before reading fixes: **yes** — I read the repo, the design note, the CI
logs and the review, and formed the per-item read below, before opening `r1-fixes.md`. Order
followed: checklist → design note → tree/CI → review → fixes.

CI evidence cited throughout: run **33059866708**, `conclusion: success`, `headSha: f810b0f…`
(`gh run list -R Metta-AI/cogame-grf-football --branch main -w ci.yml` → this run is the latest
completed run on main and matches the reviewed head). All four jobs `success`: `test`,
`docker-smoke`, `replay-rehash`, `wasm-viewer` — including `wasm-viewer`'s
`Load the bundle in a real browser` step (`conclusion: success`, and its output is in the log:
`{"loaded":true,"ms":315,…}`). No `continue-on-error` anywhere in `.github/workflows/`.

**Note on the review's vantage point:** `r1-review.md` was written against `66093e5`, fifteen
commits behind the current head. Several findings were true there and are fixed at head; per the
standard ("verify at the current head — a finding that was true and has since been fixed is
refuted, not standing") those are listed under Refuted/Resolved with the head evidence.

## Standing blocking findings

**None.** Every reviewer finding is either fixed at head (verified in code, not from the fixer's
table), refuted, or outside the checklist; my own independent pass found no item falsified.

## Refuted / resolved at head (reviewer findings)

### F1 — docker-smoke episode ends `deadline`, render ~124 ms/tick → RESOLVED at head
- Evidence: run 33059866708, `docker-smoke` log:
  `grf-football: tick 1440 budget: sim 0 ms, render 5640 ms, limiter 2941 ms, elapsed 9s` …
  `episode end reason: complete` … `smoke OK: seats=8 results=707B replay=124962B reason=complete`
  … `game over: complete/full_time 0-0`. Render is ~3.9 ms/tick at head (was ~124). Production
  arithmetic at head: 24 × 18 s rate floor = 432 s + ~22 s render + lobby ≤ 60 s + hold ≈ well
  inside the 690 s stop and 720 s settle bound. True at the review's sha; not true at head.

### F2 — perf test did not measure the serve path → FIXED at head
- Evidence: `tests/test_perf.nim:19-51` (`runServedMatch`) now steps `compileActions` → `sim.step`
  → `gameHash` → `stepEvents` → `buildSpriteProtocolPlayerUpdates` × 8 → `buildStateJson` over the
  full 5760 ticks, accumulating in microseconds, bounded `doAssert served.ms < 120_000`. Commit
  `8853961`. Green (release-only) in run 33059866708.

### F5 — error text byte-sliced on the path to the replay → FIXED at head
- Evidence: `src/grf_football/llm.nim:163-172` — every quoted body/model fragment goes through
  `errorDetail` = `clipRunes(text.multiReplace(…), maxRunes)`; the byte slices
  (`body[0 .. min(body.high, 400)]` etc.) are gone (grep for `0 .. min` in llm.nim: no match).
  `tests/test_replay_utf8.nim:117` (`errorDetailIsRuneSafe`) feeds a cut point that lands
  mid-4-byte-character on each path. Commit `6f0e089`. Checklist item 9 holds.

### F7 (first half) — possession credited to last toucher on a loose ball → FIXED at head
- Evidence: `src/grf_football/sim.nim:1217-1222` — `if sim.ball.controller >= 0: inc
  sim.teamStats[…].possessionTicks`; the `elif lastTouch` branch is gone. GV5 bump recorded.
  (Second half — out-of-play tested per substep — matches `docs/RULES.md` and is more correct than
  the note's tick-level wording; not a checklist item. Advisory only.)

### F8 — `gameHash` mixed three cosmetic pool lengths → FIXED at head
- Evidence: `src/grf_football/sim_state.nim:117-123` — the three `mixHashInt(sim.trail.len /
  arcs.len / goalFx.len)` lines are gone, replaced by a comment stating the contract;
  `tests/test_determinism.nim:110` (`cosmeticPoolsAreOutsideTheHash`) pins it. `GameVersion = "6"`
  (`sim_types.nim:24`) with changelog. Commit `8b10ca7`.

### F10 — `stop`/`state` records undocumented → RESOLVED (documented) at head
- Evidence: `docs/PROTOCOL.md` §The replay bytes lists `… budget_guard / stop / result … plus the
  diagnostic state checkpoints`; §Record vocabulary carries `stop` (`reason`,`rule`,`tick`) and the
  `state` checkpoint's rationale. Manifest regenerated (CI's `build_manifest.py --check` green).
  Design-note drift itself is not a checklist item.

### F12 (second half) — up-front beat timeline shipped `drop` and missed five kinds → FIXED at head
- Evidence: `src/grf_football/replays.nim:400-414` — the up-front filter is now exactly
  `gamestart, goal, save, foul, halftime, gameover` + `shot` only when on target; `drop` excluded
  (it still feeds the lull detector, `beatTicks`). `tests/test_viewer.nim:119-125` requires a
  `b.k === '<kind>'` timeline branch for all seven and forbids `drop`. Commit `67fd3e7`.
- (First half — beats built by the game block's `fbBeat`, not `chrome_common.markBeat` — REFUTED
  as a violation: item 14's first bullet requires `chrome_common.js` byte-identical, and the
  starter's `markBeat` (chrome_common.js:538) takes no label and makes unlabelled divs. The
  substance of 14(d) — labelled `<button>`s that seek (`CTX.send('s:' + tick)`), CSS for every
  emitted kind — is present at `client/replay_broadcast.html:2810-2842` (CSS) and pinned by
  `tests/test_viewer.nim:104-126`. The two literal readings are mutually exclusive; the substance
  is met.)

### F14 — no grid harness for the baseline → FIXED at head
- Evidence: `tools/tune_baselines.nim` (60-point grid, 240 full-length matches, both ways round,
  two train + two holdout seeds), committed artifact `docs/tuning/baseline-grid.md`, and
  `src/grf_football/baselines.nim:58-61` — `ZonalTuned = (pressRadius 12 m, shootRange 16 m,
  pressureRadius 1.5 m)` — is the harness's rank-1 row. Commit `2f557ee`. Item 7 second sentence
  holds.

### F15 — "complete" and "every order legal" split across tests → FIXED at head
- Evidence: `tests/test_control.nim:215-269` (`aFullScriptedEpisodeIsCompleteAndLegal`) — ONE
  all-scripted 5760-tick episode; asserts `results["reason"] == "complete"`,
  `endRule == "full_time"`, whole clock played, every byte of every tick legal and
  round-tripping, and every installed order inside its caps/enums/clamps with `pass_to` a teammate
  ≠ self. Commit `0c9c404`. Item 7 first sentence holds.

### F18 — two assertion replacements during the run → RESOLVED at head (item 1, second half)
- `c755d4d`'s parry deletion **was** a loosening; at head it is repaired stronger:
  `tests/test_physics.nim` (commit `f810b0f`) reads the event stream and asserts a `Save` event
  with content `"parry"` exists with `0 < speed <= KeeperParryCap + 1`. The deleted
  `restartKind != rkGoalKick` was demonstrably false (keeper legitimately gathers the rebound in
  the same tick), so restoring it verbatim was not an option; the replacement asserts strictly
  more about parrying than the original did.
- `aef2def`'s tackle replacement is a tightening, verified in the sim: `sim.nim:743-752` —
  `cogStats[i].tackles` increments only in the branch that then calls `knockBallLoose`, so
  `tackles == 1` implies the removed "knocks it loose" content at the moment it matters, and
  `fouls == 0` is added on top.
- Full sweep of `git log -p --since="2026-08-27T04:59Z" -- tests/`: no test file deleted
  (`--diff-filter=D` empty), no `skip`/`xfail`/`when false` anywhere in `tests/`, no widened
  tolerance found; the other test-file changes in the window are additions or tightenings
  (test_perf rewrite is stricter — see F2; test_replay thresholds were raised 700 → 1400).

### F19 — keeper had no goal-kick rule → FIXED at head
- Evidence: `src/grf_football/builtin_ai.nim` gains `mostOpenBeyondHalfway`, `nearestFullBack`,
  `keeperOnBall`; `tests/test_control.nim:164-213` (`theKeeperPlaysAGoalKick`) covers both
  branches (code 2 long beyond halfway; code 1 short to the full back). Commit `f7dd24f`.

### F20 — arrival dropped the nibble while chasing → FIXED at head
- Evidence: `tests/test_control.nim:125-162` (`chasingKeepsItsDirectionBits`) builds the exact
  fixture (intercept point inside `ArriveUm`) and requires a non-zero direction nibble; the
  chasing predicate now reaches `steerAction`. Commit `4a20cd6`.

### F13 — retained `core.zoomAt/setZoom/panBy` handlers → NOT BLOCKING (adjudicated)
- Facts at head (verified): the **panel** is fully removed — no `#viewpanel`, `#zoombar`,
  `#minimap`, `#zoom-*`, `minimap-canvas` markup, CSS or ids anywhere (`tests/test_viewer.nim`
  RemovedIds sweep, green); `attachMinimap` is never called from the page. What survives are the
  starter page's own keyboard/wheel/pinch handlers above the banner
  (`client/replay_broadcast.html:2426-2570`), unmodified, presenting no UI surface, documented
  in-page (`:2586-2591`) and sanctioned by the design note (design.md:949-952 scope the removal to
  the panel).
- Ruling: item 14's last bullet exists to stop a fixed-arena game *hiding* a dead panel or keeping
  its ids for the test list. Nothing is hidden and no id survives. The retained handlers are
  inherited starter code whose removal would require rewriting the starter's pointer-selection
  block — the very in-place rewriting item 14's second bullet forbids. The item's demands that are
  checkable (panel removed: markup, CSS, ids, panel wiring) all hold; item 14 is not falsified.
  Recorded as a non-blocking observation, with the fixer's minimal-compliant-change sketch on file
  if the operator wants the literal reading.

### F21 — inherited script edited in place above the banner → NOT BLOCKING (adjudicated)
- Facts at head (verified independently): I diffed the full `<style>` block above the banner
  (lines 1–1165) against the starter's (lines 1–1460): **zero additions, zero modifications** —
  exactly two pure deletions, starter 548-833 (`#fpv`) and 1451-1459 (`#viewpanel`), which are the
  removals design.md §Chrome provenance lists. The page is 3209 lines vs the starter's 4660, and
  the delta is those deleted blocks — not a gridlock-style rewrite (329 lines from scratch).
- The script edits above the banner are `PB_MODE→FB_MODE` mode branches (plate contents:
  goals/shots/possession replacing the removed life pips/perk icons/handicap chips — a removal
  the note names; endcard rule text; `FootballChrome.event` interception), every new node
  `fb-`-prefixed and machine-asserted (`tests/test_viewer.nim:74-102`). `chrome_common.js` is
  byte-identical (sha256 diff run by me; FNV-1a + length pinned in the test). Item 14 gates the
  CSS above the banner and chrome provenance; both hold.

### F3/F4 — `canvas_text` total 0 / model text is DOM → NOT BLOCKING (see item 15 below)

### F6, F9, F11, F16, F17 — positive findings; independently re-verified, consistent.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | run 33059866708 `success` at `f810b0f`, all 4 jobs incl. browser-load step; `git log -p --since="2026-08-27T04:59Z" -- tests/` read hunk-by-hunk: no skip/xfail/deletion/widening standing at head (c755d4d's parry loosening repaired stronger at `f810b0f`; aef2def verified a tightening via sim.nim:743-752) |
| 2 replay re-derivation | **pass** | `replays.nim` `stepReplay`/`checkReplayHash` (per-tick); viewer packets built from the re-stepped sim (`replay_runtime.nim`, `grf_football_replay.nim`); `tests/test_replay.nim:53-83,117-186,188-261`; CI `replay-rehash` green; wasm gate `ok: … advanced 4000 frames` × 2 |
| 3 static viewer | **pass** | manifest `replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755 (`git ls-files -s`); worker fetches only `message.replayUrl` (`static_replay_worker.js`); `tests/test_viewer.nim:159-172` forbids pod-route fetches; `/client/replay` exists only as the inherited live-pod route in server.nim, never in the bundle or manifest |
| 4 both name spaces | **pass** | `cogId` aliases `^(RED\|BLUE)-N$` in-game; real names only in config JSON / `roster[].name` / `teams.*.policies` / `results.names`; `tests/test_identity_privacy.nim` (asserts the vocabulary even with `showPlayerLabels` forced true) |
| 5 degrade-never-hang | **pass** | bounded batches `attempt1Ms/retryMs` inside monotonic `turnBudgetMs` (decide.nim:407-427); rate-floor sleep capped `min(waitMs, turnSpacingMs)` (:399-405); budget guard (:347-356); lobby 1440 ticks → declarePlayerFailure + zonal (server.nim:675-684); wall-clock stop inside the tick loop (server.nim:702-715); frame limiter breaks on elapsed (server.nim:340-350); smoke: 1440-tick episode `complete` in 9 s; head arithmetic ≈460 s ≪ 720 s; `test_perf` bounds the serve path at 120 s |
| 6 num_agents | **pass** | `num_agents: 8` in `match`, `half`, and `certification.game_config` (no variant-level key); cert players 8 = gc.players 8; `docker_smoke.sh:110-151` enforces all four invariants + `SMOKE_SEATS` (8) cross-check; `grep "SEAT-COUNT FAIL"` over run 33059866708's full log: **0 matches**; log reads `smoke OK: seats=8` |
| 7 scripted baseline full episodes, tuned | **pass** | `tests/test_control.nim:215-269` (one 5760-tick episode: `reason=="complete"`, every byte + every order legal); grid harness `tools/tune_baselines.nim` + `docs/tuning/baseline-grid.md`; `ZonalTuned` = the grid winner (baselines.nim:58-61) |
| 8 LLM reply handling | **pass** | `extractJsonObject` (llm.nim:206+, fences/prose tolerated); exactly one retry (`attempt <= 2`, decide.nim:414); fallback → zonal with recorded `{"k":"fallback",…cause…}` (:463-479) and `fallbackTurns` in results; `tests/test_engine.nim` (one batch of 8, retry-once, causes, budget guard) |
| 9 rune-safe truncation | **pass** | `clipRunes` (directives.nim:53-67) on every replay-bound string incl. error details via `errorDetail` (llm.nim:163-172); 4-byte emoji at the cap: `tests/test_directives.nim:112-132`, `tests/test_replay_utf8.nim` (incl. `errorDetailIsRuneSafe` feeding mid-character cut points) |
| 10 manifest validates | **pass** | `game.docs.readme = {"type":"text",value 5889B}`; 3 pages each `{"id","title","content":{"type":"text",…}}`; `game.protocols` has both `player` and `global` (verified by parsing the template) |
| 11 legible at 360 px | **pass** | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` (replay_broadcast.html:2723-2725); `@media (max-width: 640px)` hides labels (:2756-2767); pinned by `tests/test_viewer.nim:128-136` |
| 12 release order & scaffold | **pass** | coworld-release.yml step order: Build manifest (:159) → Certify (:173) → Upload policies (:212) → Upload Coworld (:310) → Put secret (:348); all 3 workflows present; `docker_smoke.sh` 100755; policies.json = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep exits 0 (run by me) |
| 13 viewer executes | **pass** | (i) run 33059866708 `wasm-viewer` green incl. `Load the bundle in a real browser` (`{"loaded":true,"ms":315,…}` against the smoke replay); `needs: [test, docker-smoke]` (ci.yml:342); no `continue-on-error`; (ii) `data-replay-loaded` on the Worker's post-first-frame `loaded` message (static_replay.js:161), `data-replay-error` in `showFailure` (:19-20); (iii) config.nims non-MODULARIZE, identical flag set to the starter's (diffed), matched by the worker's `Module.onRuntimeInitialized` (:188) — same starter, verified against /workspace/starters/coworld-ctf |
| 14 chrome is the starter's | **pass** | `chrome_common.js` byte-identical (sha256 equal; test pins length+FNV); CSS above the banner = starter's minus exactly the two note-listed deletions (my diff: 0 additions, 0 modifications); transport rules (a)–(d) verified (relayout on `:root` :2643-2670; nothing fixed in the band, `#transport` forbidden below the banner by test; `#endcard` bottom `var(--band)` :761, `.on` class, taken down on any non-gameover frame; beats are labelled buttons that seek, CSS for all 7 kinds); `#viewpanel` removed outright (see F13 adjudication) |
| 15 drawn strings fit | **pass** | smoke line: `canvas text: 0 drawn, 0 never inside … 0 ellipsized (--strict-text-bounds)` — `never_inside = 0` with the flag armed (fixed arena); `total: 0` is a fact about the renderer: board drawn in a Worker OffscreenCanvas and the sprite vocabulary (labels.nim) contains no text draw. Model text is **DOM**, and the DOM clause holds: `.feed-row.fb-model` band sized from the server's own caps (160/48 runes), wraps, breaks tokens, never ellipsizes, rides `#killfeed`'s fixed 4-row reserve (replay_broadcast.html:2847-2878); pinned by `tests/test_viewer.nim:202-242` incl. cap-value pinning and both JS call sites |
| batch rule | **pass** | one `curly.makeRequests` per attempt carrying all LLM seats (decide.nim:260-290, 362-427); `tests/test_engine.nim:46-63` asserts one call with 8 entries; no sequential path exists |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | already fixed on main; smoke `complete`, render 3.9 ms/tick | run log: `render 5640 ms` @1440, `reason=complete` | yes |
| F2 | fixed `8853961`, serve path measured in µs | test_perf.nim:19-51 read | yes |
| F3/F4 | fixed `233bf09`: ci.yml comment + `fb-model` DOM band + test | ci.yml:445-470, page:2847-2878, test:202-242 read | yes |
| F5 | fixed `6f0e089`, `errorDetail` + rune-safety test | llm.nim:163-172, test_replay_utf8.nim:117 | yes |
| F7 | possession fixed `938da21`; substep out-of-play declined | sim.nim:1217-1222; RULES.md documents the substep test | yes |
| F8 | fixed `8b10ca7`, GV6, new determinism test | sim_state.nim:117-123, GameVersion "6", test:110 | yes |
| F10 | documented `824ba03` in PROTOCOL.md | PROTOCOL.md record vocabulary carries `stop` + `state` | yes |
| F12 | first half declined, timeline fixed `67fd3e7` | replays.nim:400-414, test_viewer:119-125 | yes |
| F13 | DECLINED with case for the judge | adjudicated non-blocking above (panel fully removed; handlers are inherited starter code) | yes |
| F14 | fixed `2f557ee`, harness + artifact + tuned point | tools/tune_baselines.nim, docs/tuning/, ZonalTuned = rank-1 | yes |
| F15 | fixed `0c9c404`, one-episode combined test | test_control.nim:215-269 | yes |
| F18 | aef2def a tightening; c755d4d loosening fixed `f810b0f` | sim.nim:743-752 confirms the implication; parry test reads the event stream | yes |
| F19 | fixed `f7dd24f` | builtin_ai keeper procs + test_control:164-213 | yes |
| F20 | fixed `4a20cd6` | test_control:125-162 | yes |
| F21 | DECLINED (CSS gate holds) | my own CSS diff: 0 additions / 0 modifications above the banner | yes |

## Non-blocking observations

1. **Retained keyboard/gesture zoom** (F13): item 14's last-bullet wording names
   `core.zoomAt/setZoom` wiring; the panel and its wiring are gone but the starter's keyboard and
   pinch handlers survive, functional and documented. If the operator wants the literal reading,
   the fixer's sketch (delete the six keydown branches, the wheel/gesture listeners, and the pinch
   arms) is on file in `r1-fixes.md` §F13 — it requires re-deriving the inherited pointer-selection
   block, which is why I did not require it.
2. `state.feed` is shipped in the state JSON but has no page consumer; model `note`/`say` render
   via `s.directives` instead (verified `fbDirectives` call sites). Engine-authored feed rows
   (`register`/`fallback`) never reach a spectator. Feature gap, not a checklist item.
3. `docker_smoke.sh` prints `reason` without gating on it — how F1's `deadline` went green at the
   review sha. The perf bound (F2) is now the tree's guard; a smoke-side gate would be
   belt-and-braces for a template script.
4. `tools/ci/check_gameversion.sh` is wired into no workflow; GV5/GV6 were bumped by discipline.
5. `stateDigest` (diagnostic string, not the hash chain) still lists the three cosmetic pool
   lengths, and the `lastGoal*` field comment ("NOT hashed") is stale against GV2. Cosmetic.
6. Design-note drift accumulated this round (possession rule consequence, `stop`/`state` records,
   ZonalTuned ≠ the note's guessed parameters, `tags` at manifest top level) — all documented in
   the repo's own docs, which the fixer may edit; the note itself is phase-10 territory.

BLOCKING: 0
