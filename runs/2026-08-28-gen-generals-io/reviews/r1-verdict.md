blocking: 0

# r1 verdict — gen-generals-io

Head: `e8be315f465c403c2abf6c3d379079b9a59e959f` (main, = the judged sha)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-batch rule)
Independent read written before reading fixes: **yes** — I traced the repo, the CI log of run
33151358030 and the manifest, and drafted the checklist pass below, before opening
`r1-review.md`; I opened `r1-fixes.md` only after that, for the audit table.

## Standing blocking findings

None. Both of the review's blocking findings were true at the review sha (56e7b170) and are
fixed at the judged head; no checklist item is falsified at `e8be315f` and none is unverifiable
from the tree or from cited CI evidence.

## Refuted / resolved

### B1 — playback opened in the recorded lobby, seeks not clamped → **RESOLVED at head** (was true at 56e7b170)
- Verified true at the review sha: `git show 56e7b170:src/generals/replay_runtime.nim` —
  `result.cursor = 0` and `seekTo`'s `clamp(tick, 0, session.endTick)`.
- Verified fixed at head by commit `8407504`: `src/generals/replay_runtime.nim:200` sets
  `result.cursor = result.startTick` with `result.sim.phase = phPlaying`, and `seekTo`
  (`replay_runtime.nim:213`) clamps to `clamp(tick, session.startTick, session.endTick)` —
  "EVERY seek is clamped to [startTick, endTick]". The presentation phase can no longer reach
  `phLobby` (`replay_runtime.nim:226-232`), while the hash-checked re-simulation still runs every
  frame from turn 0.
- The checklist's own probe is shipped: `tests/test_gen_replay.nim:220-262` records a replay with
  `startWaitTicks = 300` (a LATE game start, which the 1-tick CI lobby cannot show) and asserts
  `cursor == startTick == 300`, that `,`/`seekTo(0)`/`seekTo(-500)`/`b`/the loop wrap all land on
  300, that three `advance()` calls move the board (`gameHash` changes), and that
  `seekTo(endTick)` still gives `hashMismatchTick == -1`.
- CI corroborates: head run 33151358030's soak first sample is `"3 / 312"` (already playing);
  the pre-fix run 33145429852's was `"0 / 312"`.

### B2 — renderer fixture never drove the remark path, asserted nothing about string length → **RESOLVED at head** (was true at 56e7b170)
- Verified true at the review sha: `git show 56e7b170:tools/ci/renderer_fixture.html` contains no
  `k: 'plan'` event and no full-length assertion.
- Verified fixed at head by `be0ad41` (+ root cause `40af89c`):
  `tools/ci/renderer_fixture.html` loads the shipped page in an iframe, shims only the wasm
  entry, feeds frames on consecutive ticks, then emits a `{k:'plan'}` **event** per seat — all
  four at once — each carrying a full-cap 160-rune NOTE, at 1280 / 620 / 360 px; it asserts the
  drawn rows still contain the whole source string (`text.indexOf(NOTE) < 0` →
  `data-replay-error: … was SHORTENED …`), that no remark leaves the feed's reserved band, and it
  transcribes every DOM text run to a canvas line-box by line-box so
  `viewer_smoke.mjs --strict-text-bounds` gates them.
- Root cause fixed: `directives.nim:460-471` — the load-bearing plan **input** record now carries
  `note` (excluded from `gameHash`: `sim_state.nim:164-169` `planHashFields` mixes only the six
  structured fields); `sim.nim:124` emits the `plan` event from `stepTurn`, one code path live
  and in replay. `tests/test_gen_replay.nim` asserts a full-cap note survives to the replay's
  plan event at `runeLen == MaxNoteRunes`.
- CI at head: step `Drive the shipped page with the worst-case renderer fixture` →
  `canvas text: 318 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` (was 27 drawn / feed_lines 0 at the review sha). Static assertions in
  `tests/test_gen_viewer.nim:197-236` pin the fixture's `k: 'plan'`, its `MaxNoteRunes` cap, the
  full-length assertion, and the `--strict-text-bounds` / no-`continue-on-error` step.

No finding in the review was refuted outright: every claim I re-traced (B1, B2, N1–N25) was
accurate against the sha it was written at, with precise citations. This is a review I could not
fault on the facts; the round's work was in the fixes.

### Non-blocking findings — state at head
Fixed and verified by me at head: N1 (`directives.nim:460-471`, `sim.nim:124`), N3 (zero
`heldRegistrations` in `server.nim`), N4 (`server.nim:290-298` re-reads `shared.playerSockets`
every directive turn; `decide.nim:90-95` `setSeatConnected`), N5 (`ci.yml:167-196`: setup-uv +
`uv run --with coworld[auth]==0.1.43` calling `_load_template_manifest`; step green at head with
`manifest OK under the installed coworld CLI: gen-generals-io`; no `continue-on-error`),
N7 (`directives.nim:191,245` sort on `view.shortestPaths(...).dist`;
`test_gen_observation.nim:124`), N9 (`baselines.nim` nearest visible enemy), N11
(`sim_types.nim:173` `truncateBytes` walks back over UTF-8 continuation bytes;
`test_gen_directives.nim:143-152`), N13 (`tests/test_gen_board.nim:6` `BoardSeeds = 10_000`),
N14 (`test_gen_determinism.nim` compares the full per-turn hash+board stream), N15 (the
tautology replaced with `check not ok` + the parses-after-prose case), N16, N17
(`baseline_tuning.json` now records `best_overall`, `best_with_documented_shape` and
`picked_is`), N18, N19 (no `COG_ART`/`front_gun` in the page), N22, N23
(`directives.nim:98-101` substitutes `CITYARMY`/`GROWTHEVERY`/`MAXTURNS` from the config),
N25 (`gen_generals_io_player.nim:27,100` `receiveMessage(ReceiveTimeoutMs = 5000)` + a 240 s
total-silence bound).

Still present at head, and correctly non-blocking (no checklist item names them):
- **N2** — the captain's threat override is dead code: `captain.nim:244-246` sets the override
  mission with `source: -1`, which step 3's `mission.source >= 0` guard (`captain.nim:249`) never
  continues; steps 4–6 then run from `plan.intent` unchanged. The system prompt still promises
  "the captain comes home for six turns. You do not have to ask for that." Both baselines defend
  themselves when threatened, so item 7 is unaffected; no checklist item requires the override.
  The fixer's NEEDS-DESIGN disposition (fixing it inverts the tuned head-to-head and the knobs
  are published in the shipped docs) is a legitimate design escalation, not an evasion.
- **N6** (crown capture and `tilesTaken`/`tilesLost` — the note contradicts itself; the code is
  hash-symmetric on both sides), **N8** (remembered city garrison — the note's two rules
  conflict; memory stores no armies), **N10** (numeral scaling/`.tiny` density — checklist item
  11 names only the `.plate-name` rule and the 640 px labels, both present; digits are 9 px
  sprites centred in 40 px cells, so no draw can leave its cell), **N12** (the note's own
  parenthetical range is what the code implements), **N20**, **N21**, **N24** — all verified as
  described; none maps to a checklist item.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **33151358030**, workflow CI, conclusion **success**, headSha `e8be315f…`; jobs `test`/`docker-smoke`/`wasm-viewer` all success. `git log -p -- tests/` (whole history = this run): every hunk strengthens — N14 replaced a final-state-only comparison with the full stream, N15 replaced `check (ok or not ok)` with real assertions, N13 raised 2 000→10 000 seeds; no skip/xfail added, no assertion deleted, no tolerance widened, no test file removed. (`test_gen_viewer.nim`'s conditional `skip()` when no bundle is staged predates the review, and `ci.yml:338-346` runs the same wasm gate directly in `wasm-viewer`.) |
| 2 replay re-derivation | PASS | `tests/test_gen_replay.nim:84-113` re-simulates from config + plan input records for conquest/full_time/wall_clock(stop turn incl.)/sim_fault and asserts `hashMismatchTick == -1`; `replay_runtime.nim:150-163` compares `gameHash` every turn; the viewer renders from that same session (`replay-viewer/gen_replay.nim` → `buildStateJson(session.sim, …)`); native↔wasm gate on the CI replay green at head (`ok: loaded replay.json, advanced 300 frames`). |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}` under `game`; `tools/build_replay_viewer.sh` mode 100755, invoked by path at `ci.yml:299`; only network call is `fetch(message.replayUrl)` in the worker; `/client/replay` appears only as the local dev route and inlined protocol docs, never declared to the platform. |
| 4 both name spaces | PASS | `cogAlias` untouched (RED/BLUE/GREEN/YELLOW-alpha); seat frames and observations carry aliases only (`test_gen_observation.nim`, `test_gen_identity_privacy.nim`, sentinel-swept both directions); viewer plates read `roster.name` = `sim.names` real policy names (`broadcast.nim:59-60`, `gen_block.html:446`); `results.names` vs `results.aliases` (`roster.nim:63-64`). Whether the hosted runner injects real names into `game_config.players[].name` is platform behaviour inherited unchanged from the certified starter — the repo-side mechanism is complete. |
| 5 degrade-never-hang | PASS | Connect wait ≤ `lobbyJoinTimeoutTicks/TargetFps` = 100 s (`server.nim:216-224`); register grace ≤ 3 s (`:226-235`); one spacing sleep ≤ `turnSpacingMs` 9 s (`decide.nim:170-174`); batch deadlines 7 s / 3 s whole-second into `makeRequests` (`decide.nim:219-244`); outer `turnBudgetMs` 11 s monotonic (`:208`); attempts < 2 (`:205`); rolling 60 s cap 28 (`:179-194`); budget guard 40 s reserve (`:297-309`); wall-clock stop 660 s top of every iteration (`server.nim:285-289`); 20 s shutdown grace then `quit(0)` (`:336-337`); player: dial 240×500 ms, `receiveMessage(5000)`, redials ≤ 6, 240 s silence bound, exits 0 on a dead socket. 660 + one in-flight turn + grace < 720 s = 60 % of 1200. |
| 6 num_agents | PASS | `num_agents: 4` inside `game_config` of `ffa`/`blitz`/`citadels` **and** `certification.game_config`; absent at every variant top level (parsed the manifest); `certification.players` = 4 = `certification.game_config.players`; `docker_smoke.sh:106-149` enforces all four `SEAT-COUNT FAIL:` invariants + the `SMOKE_SEATS` cross-check; **grep of the full head CI log for `SEAT-COUNT FAIL` → zero hits**; docker-smoke printed `smoke OK: seats=4 results=792B replay=39200B reason=complete`. |
| 7 scripted baseline | PASS | `test_gen_baselines.nim:80-104` all-scripted episodes to natural end, `reason == "complete"`; `:24-59` both baselines inside the reply schema over ≥300 states; `test_gen_captain.nim:40-119` every emitted move legal, dead seat emits nothing, boxed-in seat passes; tuning is a real 36-row × 8-seed × 4-rotation grid (`tools/tune_baselines.nim`), re-run with `--check` in CI (step green at head). |
| 8 LLM reply handling | PASS | `extractJsonObject` fence-tolerant with first/last-brace rescue (`directives.nim:306-345`); retry exactly once (`decide.nim:205` `attempt < 2`, `stillOpen` only on attempt 0); throttled fail-fast (`:282-292`); fallback = the sprawl proc (`directives.nim:490-492`); every fallback recorded to the replay and `results.fallbackTurns` (`server.nim:207-210`, `roster.nim:81`). |
| 9 rune-safe truncation | PASS | `truncateRunes`/`sanitizeNote`/`truncateBytes` (`sim_types.nim:160-202`) on every replay-bound string (note, policy, fallback detail, stopDetail, prompt, how_it_went, provider text); `test_gen_directives.nim:166-192` 4-byte emoji ON the cap → rune-boundary cut, `validateUtf8() == -1`, JSON round-trip; `test_gen_replay.nim:269-296` emoji-full replay through `replay_summary.py` → strict UTF-8. |
| 10 manifest validates | PASS | `game.docs` = readme(text, 3884 B) + 3 pages each `{id,title,content:{type:"text",value}}`; `game.protocols` carries **both** `player` and `global` as `{"type":"text","value"}` objects; and the installed CLI's own `_load_template_manifest` ran green at head (`manifest OK under the installed coworld CLI`, no `continue-on-error`). |
| 11 legible at 360 px | PASS | `client/replay_broadcast.html:1999` (= `gen_block.html:18`): `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; … }`; `@media (max-width: 640px) { .land-label { display: none; } }` (`gen_block.html:44-46`); asserted by `test_gen_viewer.nim:133-139`. |
| 12 release order & scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify `--timeout-seconds 300` (:173, fails unless the certifier reports the static bundle) → Upload policies (:216) → Upload coworld (:314) → secret put (:410); certify runs against the image `coworld build` produced in the same run. Three workflows present; `docker_smoke.sh`/`build_replay_viewer.sh`/`check_gameversion.sh` all 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, one image, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep over the five files **exits non-zero (clean)** — I ran it. |
| 13 viewer executes | PASS | `wasm-viewer` green at head **including** `Load the bundle in a real browser` (`{"loaded":true,"ms":579,…}`, `soak: 10s of playback kept advancing ("3 / 312" -> "195 / 312" -> "243 / 312")`); `needs: docker-smoke` (`ci.yml:262`); no `continue-on-error` anywhere in the job. `data-replay-loaded` set in the shell's `'loaded'` branch after `ingestPacket` (`static_replay.js:161`), `data-replay-error` in `showFailure()` (`:20`) — starter code paths, unchanged. Playback opens at the game start and every seek clamps there (`replay_runtime.nim:200,213`), checked with a **late-gameStart probe** (`startWaitTicks = 300`, `test_gen_replay.nim:220-262`). Link flags and bootstrap are one starter's matched pair: `config.nims` has no `MODULARIZE`/`EXPORT_NAME`, worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) — I diffed all four viewer files against `/workspace/starters/coworld-ctf/`: only `ctf_`→`gen_` renames plus the one documented `--preload-file …/client/art` line. |
| 14 chrome provenance | PASS | `chrome_common.js` **byte-identical** (sha256 `7ace7287…` both sides — I diffed); `broadcast_core.js` differs by the one `GEN_WIRE` line; `replay_broadcast.html` **byte-reproducible** — I re-ran `tools/build_broadcast_page.py` over the starter's page + `gen_block.html` and got the committed file byte-for-byte; the cut list matches the note's removals. Transport: `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:1929,1950-1956`); the game block's only positioned element anchors `top: var(--topband)`; `#endcard { bottom: var(--band, 0px) }` shown via `#endcard.on` and removed on every non-gameover frame (`:1486`) so any seek dismisses it; beats are labelled `<button class="beat-marker <kind>">` with `title`+`aria-label` that seek on click (`genBeat`, `:2312-2330`), CSS for exactly {citytaken, generalspotted, generalcaptured, end} (`:2119-2122`, set-equality asserted by `test_gen_viewer.nim:84-99`); `#viewpanel`/minimap/zoom/fpv/povBadge removed, not hidden — fixed 16×10 board. |
| 15 drawn strings | PASS | `--strict-text-bounds` on both smoke steps (`ci.yml:388,418`). Head run: main replay `canvas text: 0 drawn, 0 never inside` (total 0 — the board's numerals are pre-baked digit sprites inside 40 px cells, not fillText; covered instead by the fixture); worst-case fixture `318 drawn, 0 never inside, 0 ellipsized`. The fixture is the item's required one: real shipped page in an iframe, wasm-entry shim only, full-cap 160-rune remark on all four seats at once via the page's own `plan`-event path, 1280/620/360 px, sets `data-replay-loaded`, asserts its own strings full-length (`text.indexOf(NOTE) < 0` → error), own `ci.yml` step, no `continue-on-error`; feed rows get a wrapping reserved band sized from `MaxNoteRunes` (`.feed-row.plan` `white-space: normal; overflow-wrap: anywhere`, `#killfeed` min-height), never ellipsized. |
| batch rule | PASS | One `engine.runner(requests, …)` call per directive turn → one `curl.makeRequests` batch (`decide.nim:222-244`, `defaultRunner:56-77`); no per-seat call site; `test_gen_engine.nim` asserts all four in-flight windows intersect and `batches == 1`. |

## Fixer report audit

| finding | fixer said | I verified at head | agrees |
|---|---|---|---|
| B1 | fixed `8407504` | cursor opens at startTick, seeks clamp `[startTick, endTick]`, late-lobby probe test, soak opens at "3 / 312" | yes |
| B2 | fixed `be0ad41` | fixture emits `{k:'plan'}` × 4 with full-cap NOTE, asserts `indexOf(NOTE)`, 318 drawn / 0 never_inside / 0 ellipsized at head | yes |
| N1 | fixed `40af89c` | note in plan input record (`directives.nim:471`), excluded from hash (`planHashFields`), `sePlan` emitted from `stepTurn` (`sim.nim:124`) | yes |
| N2 | NEEDS-DESIGN | override still dead at `captain.nim:244-249`; no test weakened to hide it; escalation is legitimate (fix inverts the published-knob tuning) | yes — stands as non-blocking residue |
| N3–N5, N7, N9, N11, N13–N19, N22, N23, N25 | fixed (commits listed) | each verified in the tree and/or the head CI log (see the state-at-head list above) | yes |
| N6, N8, N10, N12, N20, N21 | DISPUTED / NEEDS-DESIGN | each verified still present and verified to map to **no** checklist item | yes |
| N24 | no action | documented deviation, verified by the reviewer | yes |
| CI claim | run 33151358030 success | confirmed via `gh run view`: success, headSha matches, all three jobs + both viewer smoke steps green | yes |

## Non-blocking observations (residue for the log)

1. **N2 stands** (dead captain threat override vs a system-prompt promise) — a design decision is
   owed: implement the override and retune/re-document the baselines, or delete the promise from
   the system prompt. Category would be `correctness`; no checklist item names it.
2. **The 360 px banner-chip clip** (fixer's NOTED #3): `.banner-chip` is the starter's inherited
   `white-space: nowrap` rule (`replay_broadcast.html:335`) and the crown-capture banner string
   can exceed 360 px. Engine-made text, inside the canvas, invisible to `never_inside` and
   `ellipsized` — no item-15 gate is falsified and I could not reproduce it in this sandbox (no
   browser), so it is recorded, not counted. Same treatment as the feed rows (a wrapping lane)
   would fix it.
3. `seFallback` events are recorded before `stepTurn` clears `frameEvents` (fixer's NOTED #1) —
   nothing on screen reads them today; the replay's `fallback` chat records and tier-2 stream are
   unaffected, so phase 60's fallback counting still works.
4. The player's registration re-sends fire only after a received message (fixer's NOTED #2), so
   ~1–2 go out rather than 10; the server's slot-bound registration path makes the original scar
   unreachable (N3), so this is slack, not a defect.
5. Main-replay `canvas_text.total == 0`: the board's text is wasm-baked digit sprites, so the
   canvas gate on the real replay covers nothing — the coverage lives entirely in the renderer
   fixture. If the fixture step is ever removed, item 15 loses its only real gate.

BLOCKING: 0
