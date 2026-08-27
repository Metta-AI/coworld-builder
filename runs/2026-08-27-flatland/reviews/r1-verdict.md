blocking: 0

# r1 verdict — flatland

Head: `c54424fc7231d34e57e8efc3065f2ef891cdb742` (main HEAD, CI run 33090229618, conclusion `success`)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-batch addendum)
Independent read written before reading fixes: **yes** — and per the coordinator's brief I did **not** read
`r1-fixes.md` at all; every disposition below is my own verification of the code at head. The review
(`r1-review.md`, written at `7b831f85`, 13 commits behind this head) was read only after my independent
pass of the tree, the manifest, the workflows and the CI logs.

Repo cloned fresh to `/tmp/flatland-judge`; starter mount `/workspace/starters/coworld-ctf` used for
provenance diffs. `git log --oneline 7b831f8..c54424f` = 13 commits, all fix commits referencing the
review's finding numbers (F1–F17, F23).

## Standing blocking findings

None. The review's single blocking finding (F1) is fixed at head; my independent checklist pass found
no new blocking finding.

## Refuted / resolved review findings

The review found 1 blocking + 24 non-blocking. Disposition of each at head `c54424f`:

### F1 (blocking, item 2) — replay does not record `networkPool` → RESOLVED at head
- Was true at `7b831f85`; fixed by `ecde630`.
- Evidence: `src/flatland/sim_config.nim:232` — `"networkPool": config.networkPool` is now written by
  `resolvedConfigJson` (the comment at `:221` says "`networkPool` is load-bearing");
  `src/flatland/replay_runtime.nim:58` — `configFromReplay`'s copy list now begins with
  `"networkPool"`. The trace the reviewer demanded exists:
  `tests/test_flatland_replay.nim:157` `check "a branchline episode re-derives on the branchline map,
  every end reason"` asserts `hashMismatchTick == -1` (`:181-182`). CI run 33090229618 `test` job green
  in debug and release. **Counts zero.**

### F2 — `your_notes` never delivered → RESOLVED (`a60824c`)
- `src/flatland/sim.nim:685` — `seatObservation` now emits `"your_notes"` from `sim.seats[seat].notes`;
  `tests/test_flatland_replay.nim:235` `check "the observation carries your_notes and the replay's view
  does not"` is no longer vacuous.

### F3 — network map / junction graph never sent → RESOLVED (`6f52404`)
- `src/flatland/sim.nim:718` `proc networkBriefing*` exists and `src/flatland/decide.nim:245` sends it
  at the head of every request (`let briefing = if open.len > 0: $game.networkBriefing() else: ""`,
  consumed at `:264` via `userMessage(briefing, …)`). Test:
  `tests/test_flatland_driver.nim:220` `check "every seat is sent the tile grid and the junction graph,
  both pools"`.

### F4 — yielder rule 4 compared two map constants, not the other train's heading → RESOLVED (`96dd430`)
- `src/flatland/baselines.nim:111-117`: our direction is `if world.map.edgeFwd[cell] == Dir(entry): 1
  else: -1` and the other train's is `if world.map.edgeFwd[t.cell] == t.heading: 1 else: -1` — the
  comparison now reads `t.heading`, which is what the sim's own `trainDirectionOnEdge` does.

### F5 — `blocked_ticks_last_turn` cumulative → RESOLVED (`4e826c3`)
- `src/flatland/sim.nim:490-503` `closeTurn` computes
  `blockedLastTurn = blockedTicks - blockedAtTurn` and rolls `blockedAtTurn` forward. Test:
  `tests/test_flatland_sim.nim:126` `check "blocked_ticks_last_turn counts THIS turn's refusals, not
  the episode's"`.

### F7 — `deadlockCells` are members' own cells, not contested cells → REFUTED (test pins equivalence, `f33492a`)
- `src/flatland/deadlock.nim:124` still adds each member's own cell — but in a directed waits-for
  **cycle** every member's cell is exactly the cell its predecessor is fighting for, so the two sets
  coincide. `tests/test_flatland_sim.nim:348` `check "deadlockCells names the cells the cycle is
  fighting over"` constructs a cycle and asserts it (`:380-384`: "the viewer and the observation are
  handed exactly those cells"). The reviewer's reading of the code was correct; the claimed
  consequence (wrong cells surfaced) does not hold for cycles, which is the only place the field is
  populated.

### F8 — three tier-2 kinds declared but never emitted → RESOLVED (`5f143d8`)
- `src/flatland/server.nim:290` emits `TurnStart`, `:317` `DirectiveIssued`, `:331` `FallbackTaken`.
  Test: `tests/test_flatland_engine.nim:150` `check "the tier-2 event stream carries the turn and
  directive rows"`.

### F9 — `disconnected` cause never produced → RESOLVED (`398cd10`)
- `src/flatland/decide.nim:196-206`: a seat that never registered gets yielder orders with
  `fallbackRecord(…, "disconnected", …)`. Test: `tests/test_flatland_engine.nim:239` `check "a seat
  that never registered is a DISCONNECTED fallback, not scripted"`.

### F10 — write-only `pendingRegistration` → RESOLVED (`e1199d7`)
- `grep -n pendingRegistration src/flatland/server.nim` returns nothing; the field is deleted.

### F14 — CI does not re-run the tuning sweep → RESOLVED (`7c86e9e`)
- `.github/workflows/ci.yml` step "Re-run the baseline tuning sweep" runs
  `nim c -r … tools/tune_baselines.nim --check`; it ran green in run 33090229618. (The half of F14
  about the note's prose numbers differing from the swept pick stands as a design-note delta —
  non-blocking, and the checklist's item 7 asks for a harness, which exists and is now CI-enforced.)

### F15 — five named coverage gaps → RESOLVED (`18c98ce`)
- All five closed, verified in the hunks and the tree: quiescent record→re-derive now calls
  `rederive` through recorded orders (`tests/test_flatland_replay.nim:76-120`); jam at exactly
  `jamTicks==12` / cycle at exactly `deadlockTicks==24` plus `deadlockclear` and permanence
  (`tests/test_flatland_sim.nim:384-437`); `drawOf` now actually plays episodes with the given
  policies (`:565` "nothing a seat does changes the draw"); the `notin inherited or true` tautology is
  replaced with three real splice-marker assertions; the 4096-byte cap has a test
  (`tests/test_flatland_driver.nim:264` "the 4096-byte reply cap holds and never lands invalid UTF-8
  in a record" — this also settles the review's open "byte-cut mid-emoji" question).

### F17 — surviving zoom wiring (`?viewpanel=0`, `core.zoomAt`/`setZoom` gestures) → RESOLVED (`c54424f`)
- `grep -n "zoomAt\|setZoom\|data-noviewpanel" client/replay_broadcast.html` returns only two comment
  lines naming `#viewpanel` as removed. The functions remain defined in `client/broadcast_core.js`
  (:467, :491, :548) uncalled — that file is pinned function-by-function against the starter, which is
  the checklist-14 provenance rule; the page-side wiring is gone.

### F23 — renderer fixture does not assert its own strings full-length → RESOLVED (`3df353d`)
- `tools/ci/renderer_fixture.html:251-297` now asserts each of the four full-cap 120-rune remarks is
  found un-shortened in the feed at every width, sets `data-replay-error` on any clipped or missing
  remark, and fails on `totals.full < WIDTHS.length`. CI run 33090229618 fixture step:
  `{"loaded":true,…}` and `canvas text: 90 drawn, 0 never inside the canvas (4 draws crossed an
  edge), 0 ellipsized (--strict-text-bounds)`.

### Standing as reported, non-blocking (verified still present at head; none falsifies a checklist item)
- **F6** — malfunction rolls cover `tsHeld` too (`src/flatland/sim.nim:277`). Design-note wording
  delta; both compilations of the same sim agree, so it is hash-consistent. Not a checklist item.
- **F11** — shutdown grace is `ShutdownGraceSeconds = 20` (`server.nim:42,447`); `gameOverTicks` knob
  inert. The wait is bounded, which is all item 5 asks.
- **F12** — 64 one-size chips, no baked numbers, interlock tint baked but unplaced
  (`rig_art.nim`, `global.nim:166-178`). Design-note delta; no checklist item (art is real, not
  placeholder).
- **F13** — replay ≈ 419 KB vs the note's ≈ 24 KB (docker-smoke log: `replay=419156B`). The note is
  internally inconsistent; the code follows the stronger requirement (the embedded `view`). Loads in
  582 ms in CI.
- **F16** — the note's test-file names are consolidated into six suites;
  `docs/PORTING-FLATLAND.md:15` still cites `tests/test_flatland_upstream.nim`, which does not exist
  (the assertions live at `tests/test_flatland_sim.nim:551`). Documentation nit.
- **F18** — four inert starter class names (`lives-line`, `hcap`, `lives-num`, `squad`) carry
  re-mapped contents. Identifiers, not spectator-visible vocabulary; the vocabulary scan correctly
  scopes them out.
- **F19** — every `fallback` chat record becomes a "missed the call" beat even when attempt 2
  succeeded, at `(turn-1) * DefaultTurnTicks` rather than the replay's `turnTicks`
  (`replay_runtime.nim:175-180`). Both shipped variants and the cert fixture use `turnTicks: 16 ==
  DefaultTurnTicks`, so no shipped replay mis-places a beat; over-marking is honest (an attempt-1
  failure did happen). No checklist item.
- **F20** — speed chips `[1,2,3,4,8,16]` vs the note's `[0.5,1,2,4,8]` (`broadcast.nim:18`).
  Default 1 tick/frame is what the soak depends on, and CI shows advancement. Note delta only.
- **F21** — endcard "NETWORK SCORE" is `scoreFor(0)` (`broadcast.nim:304`), i.e. carries Alpha's
  ≤ 6-point tie-break out of ~16 000. Cosmetic; `results.scores` per seat are correct
  (`tests/test_flatland_engine.nim` re-checks the formula against a real episode).
- **F22** — the run's one pre-review test edit (7b831f8) narrowed the vocabulary scan's scope to
  exclude markup identifiers and re-pinned two counts from ==1 to ==2. My own read of the hunks and
  the current tree (`tests/test_flatland_viewer.nim:229` still asserts `spoken.len > 40`;
  `:254-259` pins the re-mapped strings at their true counts — `<span>Dispatcher</span>` genuinely
  appears twice in the page) agrees with the reviewer: scope correction plus a strictly stronger
  case-insensitive comparison, not a loosening. The later F15 commit further *strengthened* this file
  by replacing a tautology with real assertions.
- **F24, F25** — informational (viewer_smoke's `feed_lines` selector; two dead branches). Confirmed
  and irrelevant to the checklist.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | `gh run list`: run **33090229618** `success` on `main` at `c54424f` (jobs test/docker-smoke/wasm-viewer all ✓). `git log -p -- tests/`: 10 commits touching tests; hunks read — no skip/xfail/deleted assertion/widened tolerance; the two non-additive edits (7b831f8 scope fix, 18c98ce) replace a vacuous scan predicate and an `or true` tautology with **stronger** assertions |
| 2 replay re-derivation | PASS | `tests/test_flatland_replay.nim:68` (every end reason, `hashMismatchTick == -1` per tick incl. stop tick), `:157` (branchline); viewer renders from the same re-step: `replay-viewer/flatland_replay.nim:172` `runtime.advanceReplayFrame()`, `replay_runtime.nim:202-223` `checkReplayHash` per tick |
| 3 static viewer | PASS | `coworld_manifest_template.json:19-21` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755; `static_replay.js` byte-identical to starter mod rename (no network but the replay URL); no pod viewer declared (the binary's local `/client/replay` dev route is the starter's own, `server.nim:39`) |
| 4 both name spaces | PASS | `sim.nim:565-651` observation carries `seatAlias` only (`"by": seatAlias(train.owner)`, `dispatchers` = aliases); viewer maps to real names: `replay_broadcast.html:2192` `rosterName`, rail rows carry `name: p.name`; smoke-log scorebug shows `YIELDER`/`TIMETABLE` |
| 5 degrade-never-hang | PASS | `decide.nim` — attempt deadlines 9 s/4 s, `attempt < 2` (`:247`), `turnBudgetMs` wrap (`:250`), rate guard (`:144-146,215-230`), spacing sleep bounded (`:233-236`), budget guard (`:170-177`); `server.nim:394-408` lobby ≤ `lobbyJoinTimeoutTicks`, `:423` wall-clock stop at 660 s < 720 s, `:446-450` 20 s grace; `tests/test_flatland_engine.nim:186` "a seat that never connects does not stop the clock" asserts `reason == "complete"` |
| 6 num_agents | PASS | manifest lines 204, 236, 272 (`num_agents: 4` in both variants + cert fixture); `docker_smoke.sh:109-151` four SEAT-COUNT invariants + SMOKE_SEATS cross-check; docker-smoke log (job 98580774449): `grep -c "SEAT-COUNT FAIL"` = **0**, `smoke OK: seats=4 … reason=complete` |
| 7 scripted baseline full legal episodes | PASS | `tests/test_flatland_engine.nim:116-119` all-scripted episode, `reason == "complete"`; `tests/test_flatland_driver.nim:44-90` every order/action inside bounds over 200 worlds; tuned: `tools/tune_baselines.nim` grid, `tools/ci/baseline_tuning.json` pinned, ci.yml re-runs `--check` |
| 8 LLM reply handling | PASS | `directives.nim` `extractJsonObject` (fence/prose-tolerant, driver test :209); retry once (`decide.nim:247` `attempt < 2`); fallback = yielder proc, recorded (`decide.nim:307-320`, `"falling back"` in the game log for phase 60) |
| 9 rune-safe truncation | PASS | `sim_types.nim:150` `truncateRunes`/`runeSubStr` applied to say/notes/policy/prompt/detail/stopDetail; `tests/test_flatland_driver.nim:186-197` 4-byte emoji at both caps, `tests/test_flatland_replay.nim:259-309` every cap emoji-filled through `replay_summary.py` strict UTF-8 |
| 10 manifest validates | PASS | `game.docs` = `{readme:{type,value}, pages:[3×{id,title,content:{type,value}}]}` (manifest:32-63); `game.protocols` carries both `player` and `global` as `{type,value}` objects (:22-31). Content type is `"uri"`, byte-for-byte the shape of the certified starter's `coworld_manifest_paintbot.json` (`docs.readme.type: "uri"`), so the certifier demonstrably accepts it |
| 11 legible at 360 px | PASS | `replay_broadcast.html:2600-2606` `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }`; labels hidden under the starter's `.tiny` (`:2543` `boardW <= 620`, i.e. under 640): `:2721` `#stage.tiny .plate .ontime-label { display: none; }` |
| 12 release order and scaffold | PASS | `coworld-release.yml` build (:165) → certify (:182) → upload-policy (:217) → upload-coworld (:319) → secret put (:372); all three workflows present; `docker_smoke.sh` 100755; `policies.json` 4 policies = 2 `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; placeholder gate: `grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files → nothing, exit 0 |
| 13 viewer executes | PASS | run 33090229618 `wasm-viewer` ✓ with `needs: docker-smoke`; "Load the bundle in a real browser" ran: `{"loaded":true,"ms":582,…}`, `soak: 10s of playback kept advancing ("5 / 496" -> "197 / 496" -> "245 / 496")`; no `continue-on-error` in ci.yml; markers `data-replay-loaded` (`static_replay.js:161`) / `data-replay-error` (`:14-20`); flags + bootstrap from ONE starter: `config.nims`, `static_replay.js`, `static_replay_worker.js` all diff-identical to coworld-ctf's modulo the `ctf→flatland` rename (no MODULARIZE, worker sets `Module.onRuntimeInitialized`, `static_replay_worker.js:188,239`) |
| 14 chrome is the starter's | PASS | `chrome_common.js` sha256-identical to the starter (40 022 bytes, diff empty); `replay_broadcast.html` mechanically reproducible: I ran `python3 tools/build_broadcast_page.py --check` against the mounted starter at head — "matches the starter page + the appended block" (the 2 992-line size vs starter 4 660 is the documented FPV/viewpanel/zoom deletions, not a rewrite); transport rules inherited (`--band` on `:root`, `#endcard{bottom:var(--band,0px)}`, seek dismisses); beats are labelled `<button>`s via `railBeat` (`:2763-2781`) with CSS for exactly `{arrival,malfunction,deadlock,fallback,end}` (`:2694-2702`); `#viewpanel` removed, not hidden — markup, CSS, ids, gestures and (as of `c54424f`) all page-side `zoomAt/setZoom` wiring gone |
| 15 drawn text fits | PASS | both smoke steps carry `--strict-text-bounds`; replay smoke `never_inside: 0` (`total: 0` — board labels are baked sprite pixels, no runtime canvas text; not gated on); the worst-case renderer fixture exists, drives the SHIPPED `index.html` in an iframe with full-cap 120-rune says on all four seats at 360/640/1024 px, asserts its own strings are still full-length (`renderer_fixture.html:251-297`, post-`3df353d`), and reported `90 drawn, 0 never inside, 0 ellipsized` in run 33090229618 |
| simultaneous batch | PASS | `decide.nim:257-271`: all open seats pushed into one `RequestBatch`, issued by a single `curl.makeRequests`; no per-seat request loop exists |

## Fixer report audit

Not performed: the coordinator's brief for this round explicitly instructed me not to read
`r1-fixes.md`. Every fix disposition above was verified directly from the code at
`c54424f`, the commit hunks, and CI run 33090229618 — not from any self-report.

## Non-blocking observations (judge's own, beyond the review)

- The checklist item 10 example writes `"type":"text"` for `game.docs` content; this repo (like its
  certified starter, whose manifest I diffed) uses `"type":"uri"`. Structure `{type,value}` is intact
  and starter-parity is the strongest available evidence of validity; recorded here so phase 60's
  certify run is read with this in mind — a certify rejection on docs content type would be the signal
  this parity argument was wrong.
- The docker-smoke episode reaches `DEADLOCK 3` in the viewer clock readout (wasm-viewer log line
  1813) — the failure-mode chrome (alarm chip, red spans) is exercised by the real CI replay, not only
  by the fixture. Good property, worth keeping the seed pinned.

BLOCKING: 0
