blocking: 0

# r1 verdict — chemistry

Head: `a6b4636eec822ec0316ccb23c92880cfcc6b4135` (verified: local `git rev-parse HEAD`, remote
`repos/Metta-AI/cogame-chemistry/branches/main`, and CI run `headSha` all agree; working tree clean)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-batch rule)
Independent read written before reading fixes: **yes** (repo, design note, diffs vs both starters,
CI run and logs all read and noted before opening `r1-review.md`; `r1-fixes.md` opened last, after
`r1-review.md`, as instructed).

The review was written against `2c34a02`; eight fix commits moved main to `a6b4636`. I verified
every fix in the tree at the current head, re-verified CI at the current head (run **32817170098**,
conclusion **success**, all three jobs `test`/`docker-smoke`/`wasm-viewer` success, including the
`Load the bundle in a real browser` and `Load the worst-case renderer fixture` steps), and audited
the fixer's three disputes. **No blocking finding stands.**

## Standing blocking findings

None.

## Refuted / resolved review findings

The review is a trace (F1–F80, mostly MATCH). Findings that alleged a defect, disposition at head:

### F13 — STARVING drops the "a stock is 0" clause → RESOLVED (fixed at `9e4eaac`)
- Evidence: `src/chemistry/sim_state.nim` `reactorStatus` now returns `rsStarving` when
  `reactor.stock[0] <= 0 or reactor.stock[1] <= 0` before the 48-tick clock; `broadcast.nim:117`
  `statusWord(charge, ticksSinceReaction, stockA, stockB)` mirrors it. CI viewer smoke at head
  prints `AMBER CHARGE 4 STARVING resin 0 · spark 0` — a charged vat with an empty stock reading
  STARVING. `tests/test_sim.nim` covers all three states. Was true at the review sha; fixed now.

### F26 — forage's absent reactor silently dropped, not clamped → RESOLVED (fixed at `36337ad`)
- Evidence: `sim.nim` `normalizeOrder` `of jobForage: … normalized.reactor =
  sim.lowestChargeReactor(); normalized.clamped = true`. `tests/test_llm.nim` asserts
  `{"job":"forage","reactor":"cobalt"}` on a two-cycle variant clamps to `beryl` with
  `clamped == true`.

### F27 — an unconnected seat was sent to the LLM → RESOLVED (fixed at `d3d38ee`)
- Evidence: `server.nim:347` sets `state.sim.cogs[slot].connected = true` on socket upgrade and
  `server.nim:430` clears it on close; `llm.nim:583` serves any seat with
  `not sim.cogs[slot].connected` from `scriptedOrder(slot, skCourier)` before the batch is built.
  `tests/test_llm.nim` marks seats 2 and 5 unconnected and asserts `lastBatchSize == Seats - 2`
  with `source == osScripted` for those seats.

### F46 — frames/series started at tick 1 → RESOLVED (fixed at `98a45a9`)
- Evidence: `sim_state.nim:290` — `initSim` calls `recordFrame()` so `frames[0].tick == 0`;
  `tests/test_replay.nim:62-68` asserts `frames.len == sim.tick + 1`, `frames[0].t == 0`,
  `series.charge[0][0] == 0`, and `frame{"t"} == index` for every frame. CI soak line at head:
  `("0 / 360" -> "192 / 360" -> "240 / 360")` — playback starts at 0.

### F47 — shift-1 order rows could never reach the feed → RESOLVED (fixed at `20e7dd1`)
- Evidence: `replay-viewer/chemistry_replay.nim:104-105` builds the load packet with
  `eventsBetween(player.startTick() - 1, player.currentTick())`; `server.nim` samples the event
  index before the applyOrder loop so live spectators get order rows too.
  `tests/test_replay.nim:180-199` asserts the union of every frame window equals
  `data.events.len` and that the first window carries exactly 8 `order` rows.

### F56 — game-block beats bypassed the ?spoilers=0 gate → RESOLVED (fixed at `4af9535`)
- Evidence: `client/replay_broadcast.html:2240-2250` `applyChemBeatSpoilers` hides any marker with
  `el.__tick > s.t` when `!C.getSpoilers()`, run on every frame from `buildChemBeats`;
  `getSpoilers` is exposed on the `window.CHEM` bridge. `chrome_common.js` untouched
  (byte-identical to the starter, verified by `diff` — see item 14 below).

### F60 — notes never drawn; live strip empty; lead density → RESOLVED in three parts (fixed at `90129c9`)
- Evidence: `replay_broadcast.html:2315-2316` renders `e.notes` in the feed row's expanded
  `<span class="notes">` (CSS at 2001: `white-space: normal; overflow-wrap: anywhere`, no
  ellipsis — a wrapped sentence, not a clipped one; dropped, not squeezed, under 640px/`tiny`);
  `server.nim:90` feeds the live chrome `result.lead = chargeLeadSeries(...)`. The fourth bullet
  (momentum normalisation) is DISPUTED by the fixer and I uphold the dispute — see below.

### F54 — in-region chrome edits broader than the note's "these three" → RESOLVED (documented at `a6b4636`)
- Evidence: the banner at `replay_broadcast.html:1827-1880` now enumerates every edit inside the
  inherited region with its forcing reason. My own diff of lines 1–1826 against the starter shows
  exactly the enumerated set and nothing else; the CSS above the banner is the starter's with
  **only** the note-listed removals (removed selectors, verified by extracting every removed CSS
  rule head: `#povBadge`, `#fpv*`, `#viewpanel`/`#minimap`/`#zoombar`/zoom controls, `#mmwarn` —
  nothing else). Checklist item 14's operative tests all pass (below); the design-note sentence
  "these three, and no others" was self-inconsistent with the note's own game-block ownership
  list, and the banner resolves it in the honest direction. Not a checklist violation.

### Fixer disputes, audited

- **F6 (`hoarded` counter vs end-state census) — dispute UPHELD.** The note self-contradicts:
  `drop` is legal only onto a cell holding no molecule (note line 161-162; `sim.nim` enforces via
  `hasMoleculeAt`), so an end-of-episode census of one home cell is 0 or 1, yet the note's own
  example shows `"hoarded":[…,9,…]` and the shame panel spec reads `GILT 9 shiny` — both only
  reachable under the counter reading the code, the manifest's `results_schema` description and
  the viewer's `hd` all implement. No checklist item pins hoard semantics. Advisory.
- **F21 (courier lane ≠ note's `mySlot mod lanes.len`) — dispute UPHELD.** The fixer implemented
  the note's formula and ran the note's own oracle: gates (a)/(b) fail 0/12 on both three-cycle
  variants (re-sorting every shift re-tasks all eight couriers and no trip completes). The note
  itself says the oracle, not the table, is the enforcement (line 300), and checklist item 7 asks
  for a tuned, oracle-validated baseline — which the shipped mapping is (test_feasibility green in
  run 32817170098). The prose outcome (slots 0–5 one lane each, 6–7 the two neediest) is preserved.
- **F60a (momentum normalised by peak, not `chargeMax`) — dispute UPHELD.** Satisfying the note's
  normalisation sentence requires editing `chrome_common.js`, which checklist item 14 makes a
  blocking static-viewer finding absent a note-recorded patch (there is none). Byte-identity wins;
  the data shape (`{teams, pts:[[t,…]]}`) matches the note exactly.

### Review findings I checked and confirm are advisory only (no checklist item)

F3/F12 ("free"-cell readings the note leaves open), F10 (one-tick food-lifetime offset — a
consequence of the note's own step order), F17 (`nextRandom` has no call site at head — verified
by grep — so the 12-seed loops are 12 identical episodes; the note's own RNG clause permits it;
no checklist item requires seed variance), F18 (`react.by` = last depositor), F19 (deterministic
kernel sidestep), F28 (429 retried same-shift — bounded either way; items 5 and 8 hold), F29
(discarded BFS field), F36 (wall-clock envelope: play stops at 720 s = 60 %, worst-case process
exit ≈918 s < 1200 s — every wait bounded; item 5 holds), F68 (smoke validates results.json
structurally, not by JSON-Schema — item 6 asks only the seat-count invariants, which are enforced),
F74 (see item 15 note below), F76/F79 (test-shape deltas vs the note's test list — the checklist's
required assertions all exist somewhere in the suite, cited below).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32817170098**, conclusion `success`, headSha `a6b4636…`, jobs test/docker-smoke/wasm-viewer all success. `git log -p -- tests/`: only additions and two re-pins strengthened (`test_replay.nim`: `frames.len == sim.tick` → `== sim.tick + 1` with new `t==0`/`t==index` assertions replacing `t >= 1`; matches the F46 tick-0 frame). No skip/xfail/deleted assertion/removed file anywhere in tests history. |
| 2 Replay re-derivation | PASS | Design pins state-frame recording, no re-simulation. `tests/test_replay.nim:125-136` round-trips the written bytes through `parseReplayBytes`/`initReplayPlayer` (the viewer's own parser); `:139-178` drives the exact calls `replay-viewer/chemistry_replay.nim` makes (`buildBoardPacket` + `buildStateJson` per frame, 60 frames, chrome tick == player tick); `:180-199` proves every recorded event lands in a frame window. `tests/test_sim.nim:322-341` pins bit-exact `gameHash` reproducibility. Viewer displays only the recorded frames (`chemistry_replay.nim:72-85`). |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, builds via `Dockerfile.replay-viewer`; bundle fetches only the `?replay=` URL (`static_replay.js:157-160`); server routes are exactly `/healthz`, `/client/global`, `/client/player`, `WS /global`, `WS /player` (`server.nim:436-441`) — no `/client/replay` route or pod (the string in `broadcast_core.js:196` is the starter's live-page URL-prefix derivation, not a served path). |
| 4 Both name spaces | PASS | Observation carries aliases only, tested negatively (`tests/test_llm.nim:196-212`: `"chemistry-foreman" notin text`, `"daveey" notin text`); replay carries `names` (aliases) + `policyNames` (`replays.nim:82-84`); roster strip shows `pol` (`broadcast.nim:171-189`, `replay_broadcast.html:2140-2143`); `results.names` = policy names (`sim.nim:462-478`). |
| 5 Degrade-never-hang | PASS | Connect wait bounded at `playerConnectTimeoutSeconds` (`server.nim:194-203`); LLM batch bounded at `llmTimeoutSeconds=20` per `makeRequests` call, ≤2 attempts (`llm.nim:589-604`); play deadline `0.6 × episodeTimeoutSeconds` = 720 s checked between shifts → `endEarly()` (`server.nim:29,234,246-254`); `minTurnSeconds` pacing sleep bounded; artifact POST bounded 60 s (`server.nim:131`); shutdown grace bounded 20 s then `quit(0)` (`server.nim:182-184`); bad token → `401`, never a hang (`server.nim:335-337`); the game never blocks reading a player socket (mummy callbacks only); player exits 0 on any dead socket (`chemistry_player.nim:61-69,95`). |
| 6 num_agents | PASS | `num_agents: 8` in all four variants + `certification.game_config` (verified by parsing the manifest; also `tests/test_manifest.nim:101-130`); `docker_smoke.sh:115-156` enforces all four invariants + the `SMOKE_SEATS` second declaration, every message prefixed `SEAT-COUNT FAIL:`; `grep -c 'SEAT-COUNT FAIL'` over the full 4657-line log of run 32817170098: **0**. |
| 7 Scripted baseline full episodes | PASS | `tests/test_feasibility.nim:95-96` asserts `ending == ekShiftLimit` and `reason == erComplete` on every all-courier seed × variant; `tests/test_baseline.nim` asserts order/action/state legality bounds across both baselines and all variants to natural end; the oracle (gates a–d) is the tuning enforcement and is green in CI; the fixer's F21 measurement is direct evidence the mapping was tuned against the oracle, not guessed. |
| 8 LLM reply handling | PASS | `extractJsonObject` tolerates fences/prose (`llm.nim:457-468`, tested `test_llm.nim:22-34`); retry exactly once with the hint (`llm.nim:589-619`, `RetryHint` at 563); fallback = courier order recorded as `source: "fallback"` on the `order` event (`llm.nim:620-623`, `events.nim` order row; tested `test_llm.nim:119-143`). |
| 9 Rune-safe truncation | PASS | `cleanText` runeSubStr (`sim_types.nim:264-271`); `sayText`/`notesText`/`errorText` cover say, notes, LLM errors (cap 200); inbound prompt rune-cut (`server.nim:400-401`); `tests/test_replay.nim:22-31,106-120` feeds multi-byte at both caps every shift and asserts `validateUtf8 == -1` + rune caps on the recorded bytes, plus `sawLong` proving the cap was actually hit. |
| 10 Manifest validates | PASS | `game.docs` = `{readme:{type:text,value},pages:[{id,title,content:{type:text,value}}×2]}`; `game.protocols` carries both `player` and `global`, both `{"type":"text",…}` (parsed directly from the manifest; `tests/test_manifest.nim:54-70`). |
| 11 Legible at 360 px | PASS | `replay_broadcast.html:1893` `.plate-name, .plate .team-name { flex: 1 1 auto; min-width: 3.2em; }`; `:2057-2058` `@media (max-width: 640px) { #roster .chip .pol { display: none; } }` (+ `#stage.tiny` equivalent at 2062-2063); pinned by `tests/test_broadcast.nim:246-249`. |
| 12 Release order & scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (:153) → Certify locally (:167) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342), one job, same-run binaries; all three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions + 2 × `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep over the five files exits 0 (ran it: "placeholder gate exits 0"); only the four documented runtime residues survive. |
| 13 Viewer executes | PASS | Run 32817170098 `wasm-viewer` success **including** `Load the bundle in a real browser` (success, no continue-on-error) with `{"loaded":true,"ms":283,"clock":"SHIFT 4 / 6 TICK 240 OF 360",…}` and `soak: 10s of playback kept advancing ("0 / 360" -> "192 / 360" -> "240 / 360")`; `wasm-viewer` `needs: docker-smoke` (`ci.yml:212`) and loads the smoke replay; `data-replay-loaded` set on worker `loaded` (`static_replay.js:139-141`), `data-replay-error` in `showFailure` (`:15-18`); `config.nims` has **no** MODULARIZE/EXPORT_NAME and the worker bootstraps `Module.onRuntimeInitialized` (`static_replay_worker.js:162`) — both from coworld-ctf, verified by diff (renames only); pinned by `tests/test_broadcast.nim:324-360`. |
| 14 Chrome provenance | PASS | `client/chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (my own `diff`: no output). `replay_broadcast.html`: banner at :1827; my diff of the region above it against the starter shows only starter-content deletions — every removed CSS selector is on the note's list (`#viewpanel`/`#minimap`/`#zoombar`/zoom, `#fpv*`, `#povBadge`, `#mmwarn`), zero chemistry-side CSS edits above the banner — plus the banner-enumerated JS edits (title, BOARD_W/H, LK_BOTS art table, syncViewUi drop, CHEM_HOOKS delegation seam), each forced by a note-required removal or by the note's own game-block ownership list; the retained region is byte-identical starter text, so this is provenance-by-diff, not id-presence. Transport: `relayout()` sets `--band`/`--hudscale`/`--topband` on `document.documentElement` (:1766, :1787-1793); overlays ride `calc(var(--band,0px) + …)` (`#killfeed` :1955 etc.); `#endcard` keeps `bottom: var(--band,0px)` (:723), shown with `#endcard.on` (:734), taken down by every frame whose phase ≠ gameover — and every seek re-enters `playing` (`chemistry_replay.nim:58-59`); beats are labelled `<button>`s that `C.seek(beat.t)` with CSS for all five emitted kinds (`shift/cold/restart/famine/gameover`, :2036-2041); `#viewpanel` removed entirely — no `zoomAt`/`setZoom`/`attachMinimap`/minimap identifier survives (grep), fixed 32×18 board per the note. |
| 15 Drawn strings fit | PASS | `ci.yml:318-323` smoke step carries `--strict-text-bounds`; its canvas_text line at head: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — `never_inside == 0`. The repo ships `tools/ci/renderer_fixture.html`, loaded by the separate `Load the worst-case renderer fixture` step (`ci.yml:333-349`, success) with its own canvas_text line: `canvas text: 64 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. The fixture loads the real `replay_broadcast.html` + `chrome_common.js`, pumps a full-cap 80-rune `say` + 320-rune `notes` on **every** seat at 360/620/900/1280 px, asserts its strings sit exactly at the caps (`renderer_fixture.html:59-69`, `data-replay-error` on failure), and sets `data-replay-loaded`. Notes render in a reserved feed band (`max-width: calc(228 * var(--u))`, `white-space: normal`, wrap not ellipsis). Coverage note: the shipped board renderer draws **no** canvas text at all — aliases are pixie-baked into sprites server-side (`global.nim:146-161`) — which is why the bundle smoke reports `0 drawn`; the checklist itself says `total: 0` is not evidence, and the fixture supplies the measured coverage. The residual weakness the reviewer's F74 names (the fixture pre-fits its own board captions, and the real say/notes chrome is DOM, invisible to canvas_text) is real but does not falsify the item's letter: every required artifact, flag, step, assertion and number is present and green. Advisory. |
| Simultaneous batch | PASS | One `RequestBatch` over all open seats per shift, one `client.curl.makeRequests(batch, …)` call (`llm.nim:589-604`), never sequential; `tests/test_llm.nim:136` asserts `lastBatchSize == Seats` on shift 1. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F13 | fixed `9e4eaac` | `reactorStatus` stock-first; smoke scorebug shows STARVING with empty stock | yes |
| F26 | fixed `36337ad` | forage clamp in `normalizeOrder` + test | yes |
| F27 | fixed `d3d38ee` | `connected` set/cleared in server; decideAll skips; test `Seats - 2` | yes |
| F46 | fixed `98a45a9` | tick-0 frame from `initSim`; tests re-pinned strictly stronger, not loosened | yes |
| F47 | fixed `20e7dd1` | load window `startTick - 1`; `before` sampled ahead of orders; union test | yes |
| F56 | fixed `4af9535` | `applyChemBeatSpoilers` every frame; chrome_common still byte-identical | yes |
| F60 | fixed `90129c9` (3 of 4) | notes span in feed row; live `lead` fed; per-shift density | yes |
| F54 | documented `a6b4636` | banner enumerates all in-region edits; my diff finds nothing beyond it | yes |
| F6 | DISPUTED | note self-contradicts (census can only be 0/1; note's own example shows 9); counter is the consistent reading | yes — dispute upheld |
| F21 | DISPUTED (measured) | note's formula fails the note's own oracle (gates a/b, three-cycle variants); shipped mapping passes; oracle green in CI | yes — dispute upheld |
| F60a | DISPUTED | fixing normalisation requires editing byte-pinned `chrome_common.js`; item 14 wins | yes — dispute upheld |
| CI claim | run 32817170098 success at head, SEAT-COUNT grep 0 | re-ran `gh run view` and the log grep myself: success, 0 hits | yes |
| "no test loosened" | claimed | verified from `git log -p -- tests/` | yes |

## Non-blocking observations

1. **canvas_text total is 0 on the real replay** (the board renderer paints text as server-baked
   sprites), so the strict-bounds gate on the bundle smoke is structurally incapable of firing for
   this repo; the fixture step is the only measured coverage, and its board captions are pre-fitted
   by its own harness (reviewer F74). If a future change adds real canvas text to
   `broadcast_core.js`, the gate becomes live again. Worth knowing; nothing to do now.
2. **The clock lags one shift** (`shift = tick div ticksPerShift` reads `SHIFT 4 / 6` at tick 242
   while shift 5 plays) — the fixer's own note; pre-existing, legible, three distinct scrub
   readouts still pass; next-round polish candidate.
3. `nextRandom` is dead code (F17); the 12-seed test loops are 12 identical episodes per
   (variant, mix). Consistent with the note's RNG clause, but the gates are weaker than they read.
4. The review's F67 says `SMOKE_SEATS` is "passed explicitly from ci.yml:184" — actually ci.yml
   passes `SMOKE_SLUG`; `SMOKE_SEATS` comes from the script's scaffold-substituted default `8`
   (`docker_smoke.sh:59`), which is the intended `<SEATS>` second declaration. Same conclusion,
   corrected citation.
5. Feed rows sample as `feed_lines: 0` in the viewer smoke at both capture moments — rows
   self-expire (`dwellFloor`) and the samples land mid-shift; the replay-layer test added at F47
   proves the rows are delivered. Not gated, not blocking.

BLOCKING: 0
