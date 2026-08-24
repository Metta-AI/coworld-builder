blocking: 0

# r2 verdict — matrix-games
Head: 1e4da299d8686d6a29a366af03fe05c6eea1c39f   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Fresh clone at `/tmp/judge2-matrix-games`, checked out at `1e4da29` (main). I read the checklist
prompt, the design note, and the tree — and formed the independent notes below — **before**
opening `r2-review.md`, and read `r2-fixes.md` last. The review was written against `af5c704`;
14 fix commits plus the docs-only note amendment landed after it, so every finding is
adjudicated **at `1e4da29`**.

CI evidence used throughout:
- run **32763693564** — push, headSha `1e4da29…` (this head), conclusion **success**; jobs
  `test`, `docker-smoke`, `wasm-viewer` all `success`, confirmed step-by-step via
  `gh run view --json jobs`: `Load the bundle in a real browser` and `Load the worst-case
  model-text fixture in the same bundle` both ran and passed; no `continue-on-error` anywhere in
  `ci.yml`; `wasm-viewer` has `needs: docker-smoke` (`ci.yml:216`).
- run **32761793533** — push, headSha `a301f70…` (the last code sha), conclusion **success**.
- Full-log grep of 32763693564: **0 × `SEAT-COUNT FAIL`**, **0 × `RESULTS-SCHEMA FAIL`**,
  **0 × `EPISODE-REASON FAIL`**; `episode end reason: complete` and
  `smoke OK: seats=8 results=709B replay=118908B reason=complete` in `docker-smoke`;
  `{"loaded":true,…,"feed_lines":6}` and `soak: 10s of playback kept advancing` in **both**
  browser steps; `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge),
  0 ellipsized (--strict-text-bounds)` in both.

## Standing blocking findings

None.

**Round 1's single blocking item (B1) is closed at this head**, verified on both halves:

1. **The container gate.** `tools/ci/docker_smoke.sh:369-384` now *asserts* the reason:
   ```python
   reason = results.get("reason") or results.get("end_reason")
   if reason != "complete":
       raise SystemExit(f"EPISODE-REASON FAIL: results.reason is {reason!r}, expected 'complete'. ...")
   ```
   (commit `2835f33`). At this head the gate is live and green: `episode end reason: complete`
   in run 32763693564, 0 × `EPISODE-REASON FAIL`.
2. **The test, through the production settle path.** `sim.settleComplete()`
   (`src/matrix_games/sim.nim:195-203`) is the ONE place a full episode is stamped `complete` —
   `server.runGame` calls it when the beat loop falls out (`server.nim:303` region) and the test
   harness calls the same proc. `tests/test_baseline.nim:53-79` plays an all-scripted episode of
   **every** variant to its natural end, bounds-checks every order on the way in (`checkOrder`),
   asserts `not state.done` before the settle, then
   `results{"reason"} == "complete"`, `ending == "full_match"`, `beats == config.beats`,
   `ticks == beats × ticksPerBeat`. The tautology r1 flagged is gone: the harness's own
   `finish("complete", …)` stamp was removed from `tests/support/helpers.nim` and replaced by
   `settleComplete()` (verified in `git log -p -- tests/`).

## Refuted / adjudicated review findings

The review (17 match · 11 gap · 8 unclear) was written at `af5c704`. Its **match** findings I
spot-verified and concur with (F2/F3 rune head + 401/403 test at `tests/test_llm.nim`; F17 soak;
F20/F22 per-tick and index cross-checks; F28 schema validation; F30/F31 CI hygiene). Every gap
that named a checklist item is fixed at this head:

### F5 — `validate()` rejected schema-legal `beats` → REFUTED (fixed, `5c8ba4c`)
- Evidence: `src/matrix_games/sim_config.nim:119-125` at `1e4da29` — the requirement is now
  `startupBudgetSeconds() + beatBudgetSeconds() ≤ playDeadlineSeconds()` (startup + ONE beat),
  and the beat loop refuses to open a beat whose worst case crosses the deadline
  (`server.nim:257`: `if epochTime() - gameStart + beatBudget > deadline: … finish("deadline",…)`),
  so schema-legal long configs truncate instead of exiting 2. `tests/test_manifest.nim`
  ("every beats value the config schema publishes starts the game") walks the schema's whole
  `minimum..maximum` range through `validate()`; a config with no room for one beat still raises.

### F7 — the beat-loop guard missed Defects → REFUTED (fixed, `be6f66e`)
- Evidence: `src/matrix_games/server.nim:296` — `except Exception as error:` with the Nim-2.2.4
  rationale in the comment (`-d:release`, no `--panics:on`, Defect derives from Exception not
  CatchableError). A defect on the beat thread now settles as `deadline` instead of killing the
  process with no artifacts.

### F8 — `finishEpisode` sat outside the guard → REFUTED (fixed, `3925fe0`)
- Evidence: `server.nim:304-316` — the settle path (`pushStateFrames` + `finishEpisode`) runs in
  its own `try/except Exception`, and inside `finishEpisode` the replay and results writes are
  **independent** (`server.nim:159-170`: each `writeArtifact` in its own `try`, failures counted
  and logged), so a non-2xx replay POST cannot take `results.json` down. Whatever happens, the
  thread reaches the shutdown grace and `quit(0)`.

### F10 — the pod served the broadcast page under its asset name → REFUTED (fixed, `0095d95`)
- Evidence: `server.nim:350-359` — `servableClientAsset` refuses traversal, dotfiles and
  `ReplayPageAsset = "replay_broadcast.html"` (`server.nim:55`); registered ahead of the asset
  route. `tests/test_manifest.nim:62-74` asserts both directions (page and traversal refused;
  `chrome_common.js`, `broadcast_core.js`, `global.html`, `player.html` still served).

### F11 / F16 — stale comments → REFUTED (fixed, `86dfffb`, `0abf485`)
- Evidence: the script-loader comment now describes "an unspliced copy of this page", no
  `/client/replay` mention (`client/replay_broadcast.html:1609-1613`); the 360 px header now
  names 640, the threshold `mgRelayout` uses (`:1482-1483` vs `:2204`,
  `stage.classList.toggle('tiny', width < 640)`).

### F14 — the feed was unverified by any gate → REFUTED (fixed, `a301f70` + `4d82f28`)
- Evidence: `<div id="killfeed" class="feed">` so `viewer_smoke.mjs`'s `#feed, .feed, #log`
  selector sees it; head CI reports `"feed_lines":6` in **both** viewer steps — the first CI
  evidence the feed draws. The row is bounded: `#killfeed .feed-row { display:block;
  max-width:100%; white-space:normal; overflow-wrap:anywhere; }` (`:1439-1446`), the feed is
  capped at 6 rows (`mgPushRow`, `if (mgFeed.length > 6) mgFeed.shift()`), bottom-anchored above
  the band. `tests/test_worst_case_text.nim` asserts the wrap/no-ellipsis rules and the
  `class="feed"` hookup from the committed page.

### F19 — `viewer_smoke.mjs` stale, no text-bounds → REFUTED (fixed, `ad913b3`)
- Evidence: `diff` of the repo's `tools/ci/viewer_smoke.mjs` against
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` at this head is **empty**
  (template verbatim, "no substitutions" as design.md requires), and both `ci.yml` browser steps
  carry `--strict-text-bounds` (`ci.yml:309-317`, `:355-362`).

### F21 — the recording harness duplicated the beat loop → REFUTED (fixed, `b25609d`)
- Evidence: `src/matrix_games/sim.nim:170-181` — `runBeat*(sim, onTick: proc(sim: Sim) = nil)`
  with the `if sim.done: return` guard intact; `tests/support/helpers.nim:63-75` passes a
  per-tick hook into the **production** loop instead of inlining a copy.

### F23 — no non-emptiness guard; `over`-row divergence → REFUTED (fixed, `d38a9cc`)
- Evidence: `tests/test_viewer.nim:206-216` now has `check state.idx.interactions > 0` and
  `check total > 0`; `src/matrix_games/global.nim:161-173` builds the terminal `over` row from
  the final frame's `sc` with the same argmax-lowest rule `sim.leader()` uses; a new test
  ("the live timeline and the replay timeline are the same rows") compares `buildBeats` and
  `initViewer`'s timelines row by row on two variants, including the `over` row's seat and cp.

### F25 — the note's literal chicken claim was false → REFUTED (fixed at head, `1e4da29`)
- Evidence: the head commit is the coordinator's amendment of the design note to the
  per-resolution form (design.md:626-631: "Amended by the coordinator in round 2 … the
  per-resolution form is the property the game actually guarantees and the one
  `tests/test_indices.nim` asserts"). `tests/test_indices.nim:113-130` asserts hawk out-earns
  dove in every mixed cell over seeds 1..8 (`check checked >= 8`) and `:132-136` keeps the
  all-hawk-worst-room clause as written. The note, the code and the test now agree; the
  repo's `docs/plans/2026-08-24-matrix-games-design.md` is byte-identical to the run's
  `design.md` (diff empty). No test was weakened — the chicken test was *added* this round.

### F27 — child mode was an env-gated skip of the sim suite → REFUTED (fixed, `cd4ef58`)
- Evidence: `tests/test_sim.nim:10-36` — child mode now requires
  `MATRIX_GAMES_HASH_CHILD == "test_sim determinism child"` **and** the seed; either variable
  present without the exact pair `quit`s **2** with a message, and a test spawns the binary
  under all three refusal environments and asserts exit 2. A stray inherited variable is now a
  red job, not a silent skip.

### F29 — B1 → REFUTED (fixed, `2835f33`; see Standing section above)

### Review findings that stand as written but falsify no checklist item (not counted)
- **F18** — the three scrub readouts are printed, never gated (`viewer_smoke.mjs` exit condition
  is `!loaded || playFailure || boundsFailure`). Verified true at head. But the file is required
  to be the coworld-builder template verbatim (design.md and checklist item 15's own step
  construction), the checklist gates `loaded`/soak/`never_inside` — all live — and the readouts
  did differ in the cited run. A template-side change is where this belongs. Not blocking.
- **F32–F36** — design-note ambiguities (kernel target-selection metric, mixed-side
  exploitability, turn-on-blocked-move, 429 same-beat retry, cert fixture alias names).
  Re-checked at head: all deterministic, none falsifies a checklist item. Not blocking.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run 32763693564 success at `1e4da29`; run 32761793533 success at `a301f70` (both cited above). `git log -p --since="2026-08-24T14:37:00Z" -- tests/` read hunk by hunk: every change is additive or strengthening — harness `finish("complete",…)` stamps replaced by the production `settleComplete()`, the inlined beat loop replaced by the production `runBeat(hook)`, child-mode skip hardened to a loud exit 2, chicken test *added*. No deleted assertion, no widened tolerance, no skip/xfail, no removed file. |
| 2 replay re-derivation | **pass** (adapted: state-recording, per design.md §replay) | `tests/test_viewer.nim:123-167` compares the viewer packet at every tick t (board `c`/`inv`/`sc`/`tok` and chrome `seats[]` incl. event-folded `interactions`) against the sim's own state captured by the **production** `runBeat` hook (`helpers.nim:63-75`, `sim.nim:170-181`); `:188-216` cross-checks the viewer's event-folded indices against the recorded accumulator with non-emptiness guards; the wasm entry (`replay-viewer/matrix_games_replay.nim:19,64`) calls the same `initViewer`/`viewerPacket` (`src/matrix_games/global.nim:62,354`) — one derivation, no parallel recording. |
| 3 static viewer | **pass** | `coworld_manifest_template.json`: `"replay_viewer":{"bundle":"static-replay-viewer"}`, no `url`; `tools/build_replay_viewer.sh` present, `-rwxr-xr-x`, exercised by `ci.yml`'s wasm-viewer job; `static_replay.js` fetches only the `?replay=` URL; `grep -rn "/client/replay"` finds only negations/tests; the pod refuses the broadcast page under any name (`server.nim:350-359`). |
| 4 both name spaces | **pass** | `buildObservation` ships aliases only (`sim.nim` obs; asserted by `test_replay.nim:76-77`: `names[slot] == aliasOf(slot)`); `policyNames[]` + `results.names[]` carry policy names; plates show `seat.name` = policy name (`replay_broadcast.html` `mgBuildPlates`, asserted `test_viewer.nim:84-92`). Head CI scorebug shows policy names in the worst-case step (`worst-case-always-first 22.09 8 enc …`). |
| 5 degrade-never-hang, 60 % | **pass** | Deadline `0.6 × episodeTimeoutSeconds` stamped at process start (`server.nim:184-186`), checked **between beats** against the budget of the beat about to start (`server.nim:257`); connect wait ≤ 180 s + 3 s grace; batch `makeRequests(batch, timeoutSeconds=20)` (`llm.nim:490`) with one retry; pace sleep ≤ 17 s; beat loop and settle path both guarded with `except Exception` (`:296`, `:311`); forfeit path writes artifacts (`:236-247`); `validate()` floor `sim_config.nim:119-125`; shipped 12 beats = 663 s ≤ 720 s. Smoke asserts every player container exits 0 within 30 s of the game. |
| 6 num_agents | **pass** | `8` in all seven `variants[].game_config`, in `certification.game_config`, `len(certification.players) == 8 == len(game_config.players)` (read from the manifest); `docker_smoke.sh` enforces all four invariants + the independent `SMOKE_SEATS=8` cross-check, every violation `SEAT-COUNT FAIL:` + exit; head log grep: **0** occurrences. |
| 7 scripted baseline full episodes | **pass** (B1 closed) | Legality: `test_baseline.nim:38-51` (5 baselines × 7 variants × seeds 1..8, `checkOrder` on every order). Natural end asserted twice: `test_baseline.nim:53-79` (every variant, production `settleComplete`, `reason == "complete"`) and `docker_smoke.sh:369-384` (`EPISODE-REASON FAIL` gate; head log `episode end reason: complete`). Tuning: the parameters are pinned by the note's arithmetic and validated by the gate sweep (`test_indices.nim`: ≥ 12 resolutions, every seat resolves, every K×K cell hit, matrix-bites, over 7 variants × 8 seeds) — grid-harness evidence in the tree. |
| 8 LLM reply handling | **pass** | `extractJsonObject` tolerates fences/prose/trailing text (`llm.nim:330-341`); one retry with hint (`decideAll` `for attempt in 0 .. 1`, `llm.nim:525-559`); fallback to `counter` recorded as `source:"fallback"` on the order event (`osFallback`, `sim.nim:installOrders` → `orderEvent`); 401/403 disables client, 429 logged and reopened. All covered by `tests/test_llm.nim` incl. stubbed transport timeout/429/403/junk. |
| 9 rune-safe truncation | **pass** | `cleanText` = strip → newline fold → `runeSubStr(0, limit-1) & "…"` (`sim_types.nim:228-238`); applied once at `installOrders` (`sim.nim:212-213`) and on every captured error body (`llm.nim` `MaxDetailRunes`); `tests/test_replay.nim:97-136` feeds multi-byte say/notes exactly at the 64/400 caps and asserts `validateUtf8 == -1` and cap adherence on the recorded bytes, plus `cleanText` at every limit 1..40. |
| 10 manifest validates | **pass** | `game.docs` = readme (text) + 3 pages each `{"id","title","content":{"type":"text",…}}`; `game.protocols.player` and `.global` both `{"type":"text","value":…}` (read from the manifest); `test_manifest.nim` asserts all of it. |
| 11 legible at 360 px | **pass** | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` (`replay_broadcast.html:1355`); labels hidden under 640 px (`:1484-1486` `#stage.tiny .plate.mg .plate-name/.plate-enc/.plate-camp { display:none }`, toggled at `:2204` `width < 640`); asserted by `test_viewer.nim` "the 360 px rules are present". |
| 12 release order + scaffold | **pass** | `coworld-release.yml`: Build the Coworld manifest (`:153`, `coworld build` from compose) → Certify locally (`:167`, requires the STATIC-bundle liveness marker) → Upload the policies (`:206`, comment pins "BEFORE upload-coworld") → Upload the Coworld (`:304`) → Put the Coworld secret (`:342`, "AFTER upload-coworld"). All three workflows present; `docker_smoke.sh` 100755; `policies.json`: 4 distinct policies — champions `matrix-games-reader` and `matrix-games-brinkman` both `PLAYER_PROMPT` + `USE_BEDROCK`, #2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, fillers `counter` + `tit-for-tat` scripted. Placeholder grep `'<slug>\|<IMAGE>\|<SEATS>'` over the five files exits 1 (nothing found). |
| 13 viewer executes | **pass** | Run 32763693564 `wasm-viewer` success **including** `Load the bundle in a real browser` (step conclusion success; `needs: docker-smoke`; no `continue-on-error`); log: `{"loaded":true,"ms":336,…}` + `soak: 10s of playback kept advancing ("0 / 300" -> "192 / 300" -> "240 / 300")`. Shell markers: `static_replay.js` sets `data-replay-loaded='true'` on first drawn frame and `data-replay-error` in `showFailure`, `ready` posted after loaded (asserted, `test_viewer.nim` "the shell reports both readiness attributes"). Matched pair: `config.nims` is coworld-ctf's verbatim modulo the `_mg_*` rename and the note-named `mismatch_tick` drop — **no MODULARIZE, no EXPORT_NAME** — and the worker keeps `var Module = {}` + `Module.onRuntimeInitialized`; both from coworld-ctf, asserted by `test_viewer.nim` "the link flags are non-modularized and the worker matches them" and proven by the executed `loaded: true`. |
| 14 chrome is the starter's | **pass** | `client/chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (`diff` empty). `client/replay_broadcast.html`: I diffed the inherited region line-by-line — the 1 324 lines above the CSS banner are **99.7 % literally the starter's in order**; the only deltas are the `<title>`, the `#killfeed` band fix (`bottom: calc(var(--band,0px) + 40*var(--u))` — the direction rule (b) requires), and the removal of starter lines 703–832 = the `#viewpanel` zoom+minimap CSS the note lists (the board is a fixed 24×14 that always fits, so the panel is correctly **removed**, asserted gone by `test_viewer.nim`). The starter HTML markup is retained with the note's listed removals; the appended game block sits under the banner with every top-level name `mg`-prefixed (anti-hoisting test present). Transport rules verified in the page: (a) `mgRelayout` sets `--hudscale`/`--band`/`--topband` on `document.documentElement` (`:2200-2210`); (b) overlays ride `var(--band)`/`--topband` (asserted per-rule by `test_viewer.nim`); (c) `#endcard { top: var(--topband); bottom: var(--band,0px) }` kept (`:908-930`), shown with `#endcard.on`'s own class, and **every** seek path funnels through the wrapped `mgCore.seek` that removes `.on` (`:2175-2182`) — scrub click, buttons, keyboard, beat markers all call `mgCore.seek`; (d) beat markers are `document.createElement('button')` with `aria-label`, click → `mgCore.seek(tick)`, and a CSS rule exists for each of the four kinds emitted (closed set asserted both sides). The page is 53 % of the starter's line count; the reduction is fully accounted for by the removed `#viewpanel`/FPV blocks and the starter's CTF-specific view script (kills/flags/POV/perks — machinery that cannot drive this game and whose shared half lives in the byte-identical `chrome_common.js`), not by a rewrite: everything retained is byte-verified starter content. Not the gridlock case. |
| 15 every drawn string fits | **pass** (per the coordinator's round-2 ruling for this repo) | Both `ci.yml` browser steps carry `--strict-text-bounds`; head log: `canvas text: 0 drawn, 0 never inside … 0 ellipsized` — `total: 0` is expected here (all spectator text incl. model `say` is DOM; `grep fillText\|strokeText` over `client/ replay-viewer/` is empty). The fixture requirement is implemented: `tests/fixtures/worst_case_text.replay` (141 486 B, committed), generated by `tools/gen_worst_case_replay.nim`, loaded **through the real bundle** in its own ci.yml step (ran, `loaded:true`, soak passed, `feed_lines:6`); `tests/test_worst_case_text.nim` asserts from the **committed bytes** that all 48 order events (8 seats × 6 beats) carry `say.runeLen == 64` and `notes.runeLen == 400`, no ellipsis, multi-byte, all four marker kinds present, and generator == file. The DOM bound on full-cap remarks is real CSS, not hope: `#killfeed .feed-row` wraps (`max-width:100%; white-space:normal; overflow-wrap:anywhere`, never ellipsizes — asserted), the feed is capped at 6 rows and bottom-anchored above the band; labels (`.banner-chip`) ellipsize. Remark wraps, label cuts — the item's rule, implemented and tested. |
| batched LLM calls | **pass** | One `curly.makeRequests` batch per beat for every open seat (`llm.nim:478-498`, `decideAll`); never a per-seat loop. `tests/test_llm.nim:111` asserts `client.batchSizes == @[Seats]` and `:118-120` asserts batch starts ≥ `minBeatSeconds` apart. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F5 | fixed `5c8ba4c` — floor-only validate + beat-loop truncation | `sim_config.nim:119-125`, `server.nim:257`, schema-range test in `test_manifest.nim` | yes |
| F7 | fixed `be6f66e` — `except Exception` | `server.nim:296` + rationale comment | yes |
| F8 | fixed `3925fe0` — guarded settle, independent artifact writes | `server.nim:159-170`, `:304-316` | yes |
| F10 | fixed `0095d95` — `servableClientAsset` refuses the page | `server.nim:55,350-359`, `test_manifest.nim:62-74` | yes |
| F11/F16 | fixed comments | `replay_broadcast.html:1609-1613`, `:1482-1483` | yes |
| F14 | fixed `a301f70` — `class="feed"`, bounded rows | page `:1439-1446`, head CI `"feed_lines":6` both steps | yes |
| F18 | no change (template's gate) | template-verbatim confirmed by empty diff; readouts differ in the run | yes (reasoned) |
| F19 | fixed `ad913b3` — template verbatim + strict flag | empty diff vs template; both steps carry `--strict-text-bounds` | yes |
| F21 | fixed `b25609d` — production `runBeat(onTick)` | `sim.nim:170-181`, `helpers.nim:63-75` | yes |
| F23 | fixed `d38a9cc` — over-row from final frame + guards | `global.nim:161-173`, `test_viewer.nim:206-240` | yes |
| F25 | not mine — coordinator must amend the note | amended at head `1e4da29`; note == repo copy (diff empty) | yes (now closed) |
| F27 | fixed `cd4ef58` — token-gated child mode, loud refusal | `test_sim.nim:10-36` + 3-case refusal test | yes |
| F29 (B1) | fixed `2835f33` — smoke gate + production-settle test | `docker_smoke.sh:369-384`, `sim.nim:195-203`, `test_baseline.nim:53-79`, head log | yes |
| item 15 | fixed `4d82f28` — fixture + own CI step + CSS bound | fixture, generator, `test_worst_case_text.nim`, ci.yml step ran green | yes |
| "no test loosened" | claimed | independently read every hunk of `git log -p --since=<run start> -- tests/`: all strengthening | yes |

No disagreements. The fixer's claim that `canvas_text` only sees main-thread contexts while the
board renders in a Worker/OffscreenCanvas is accurate and honestly stated; it does not change the
verdict because this viewer draws no canvas text and the model-text bound is the tested DOM CSS.

## Non-blocking observations

- **`client/broadcast_core.js` is a new Matrix Games board renderer**, not the starter's sprite
  core, while design.md §Viewer says the starter's zoom/pan code "stays in the file, verbatim,
  simply never driven." Checklist item 14 names only `chrome_common.js` (byte-identical — it is)
  and `replay_broadcast.html` (verified above), and the starter's sprite-protocol core cannot
  decode this game's state-frame packets; items 2 and 13 verify the replacement functionally.
  Recorded as a design-note inaccuracy, not a checklist violation.
- **`/replay-data`** (`server.nim:378-385`, registered `:500`) serves the raw replay JSON only in
  the pod's replay mode (`replayPayload` is empty in game mode → 404). Nothing in the static
  bundle references it; it is not a `/client/replay` path. Inherited runtime-contract shape.
- The inherited starter comment at `replay_broadcast.html:1298` still says "≤620px stage" (the
  starter's own threshold) while `mgRelayout` uses 640; the game-block comment F16 fixed is
  correct. Cosmetic.
- No gate measures the feed at 360 px (the template harness has a fixed 1280×800 viewport). The
  360 px screenshot is phase-60's viewer check per design.md; item 11's CSS requirements are
  present and tested.
- The design note's route table (design.md §Server) still says `/client/global` serves the
  broadcast page; the pod serves `client/global.html` (a docs page). The shipped behaviour is the
  correct one post-F10; the note is stale on this line.
- The fixer's NOTED flake ("no baseline takes longer than 1 ms per beat", sandbox-only, 1.00–1.04
  ms) passed in both CI modes at both head shas; the bound was not touched. Watch item only.

BLOCKING: 0
