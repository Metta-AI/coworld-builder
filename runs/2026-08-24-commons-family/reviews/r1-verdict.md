blocking: 0

# r1 verdict — commons-family
Head: ef8e2556638bc560061984b560d0f30b7bbccc99   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

I cloned `Metta-AI/cogame-commons-family` fresh at `ef8e255`, read the tree, the design note, the
CI logs of run 32773426921 and the git history of `tests/` before opening `r1-review.md`, and read
`r1-fixes.md` last. The sha I judge is 19 commits newer than the sha the review was written
against (`5c64904`); findings true then and fixed now are recorded as **resolved (fix verified)**,
not dismissed.

## Standing blocking findings

None. Every reviewer finding is either fixed at head (verified below) or does not falsify a
checklist item, and my own independent checklist pass found nothing blocking.

## Refuted / resolved — the reviewer's findings, one by one

### O1 — unclassified LLM exception escaped `_play_game` → RESOLVED (fix verified)
- True at `5c64904`; fixed at head. `game/llm.py:356-366`: `_decide_seat` now ends in
  `except Exception: logger.exception(...); cause = "transport"; continue` — the seat retries once
  and falls back. Independently, `game/server.py:328-343`: `_play_game` wraps `_run_episode()` in
  `try/except Exception` and always calls `_finish(reason)`. Verified by
  `tests/test_llm.py::test_an_unclassified_transport_exception_degrades_the_seat_rather_than_escaping`
  (HTTPError 401 stub → `(None, "transport")`, exactly 2 calls) and end-to-end
  `tests/test_episode.py::test_a_transport_that_raises_settles_the_episode_with_fallbacks`
  (`reason == "complete"`, `fallbacks == [3]*6`, every `src == "fallback:transport"`). Item 5 holds.

### O2 — paused branch skipped the wall-clock guard → RESOLVED (fix verified)
- `game/server.py:393-403`: the `if session.paused:` branch now checks
  `time.monotonic() > play_deadline` and breaks with `reason = "deadline"` before sleeping.
  Verified by `tests/test_episode.py::test_a_pause_cannot_hold_the_episode_past_the_wall_clock_guard`
  (paused loop settles `deadline` inside a 30 s `wait_for`). Item 5 holds.

### O3 — play budget anchored after the connect wait (905 s worst case) → RESOLVED (fix verified)
- `game/server.py:100`: `PROCESS_START = time.monotonic()` at import;
  `server.py:347`: `play_deadline = PROCESS_START + play_budget_fraction × EPISODE_TIMEOUT_SECONDS`;
  `server.py:410-413`: guard checked **before** a round (`now + max(round_seconds,
  min_round_seconds) > play_deadline`), so artifacts land inside 0.6 × 1200 = 720 s whatever the
  connect wait cost. Verified by
  `tests/test_episode.py::test_the_play_budget_is_anchored_at_process_start_not_at_the_first_round`
  (PROCESS_START moved 500 s into the past → `deadline` after exactly round 0). Item 5's 60 % bound
  now holds at the hard ceiling, not just typically.

### O4 — renderer.js "byte-for-byte" claim false → RESOLVED (doc fix; provenance itself sound)
- I checked provenance independently against `/workspace/starters/cogame-bullwhip/client/renderer.js`:
  the chrome scaffolding (`makeRenderer`, `attachLive`, `attachReplay`, `buildScrub`, `renderFeed`,
  `updateScorebug`, `updateEndscreen`, `makeNameMap`, `drawChart`, `wrapLines`, `drawBubble`,
  `describeEvent`, …) keeps the starter's names, structure and call graph; bullwhip's supply-chain
  board functions are replaced by this game's four module boards, called from the same `draw()`
  switch; the export object (`renderer.js:1395-1401`) keeps the starter's key set. That is what
  item 14 asks for. The false sentence was in the design note, and the note at head
  (§Chrome provenance, design.md:837-859) now describes exactly what I observed, including
  `money`→`score`, the added `paint()`, and the `String()`/radius hardening. No checklist item
  falsified.

### O5 — chrome.css third in-place edit undocumented → RESOLVED (doc fix)
- Verified by diff against the starter: exactly three hunks (header comment, `#scorebug`
  `repeat(4,1fr)`→`repeat(6,1fr)` at `chrome.css:268`, `#endscreen` `bottom: var(--band, 0px)` at
  `chrome.css:379-381`) plus the banner-marked appended block (`chrome.css:472+`). The note
  (design.md:860-872) now lists all three. Item 14 holds.

### O6 — ready-bridge edit vs the note's "untouched" → RESOLVED (doc fix)
- The edit (`static_replay.js:127-147`, `whenDrawn` MutationObserver on `data-replay-loaded`) is
  what item 13(b) wants — `ready` means a picture — and
  `tests/test_viewer_contract.py::test_the_ready_bridge_is_posted_only_after_the_first_painted_frame`
  pins it. The note's table row (design.md:783) now records it. Item 13 helped, not hurt.

### O7 — Nim recomputed `public_effort` (second physics implementation) → RESOLVED (fix verified)
- `game/engine.py:461-484`: step 8 computes `efforts = [module.public_effort(d, config)]` once and
  the round record carries `seat_public_effort`; `commons_family_replay.nim:136-143` reads
  `record{"seat_public_effort"}` with a comment saying why, and no `decision{...}` re-derivation
  survives (`tests/test_viewer_contract.py::test_the_wasm_module_reads_the_recorded_effort_instead_of_recomputing_it`
  asserts the absence). `tests/test_replay_parse.py::test_the_maintenance_effort_the_viewer_shows_is_recorded_per_seat`
  asserts the record equals the module's own computation and sums to `results.public_effort`.
  Item 2 (as bound by the coordinator note: recorded states, no parallel physics) holds.

### O8 — "8 requests per seat per round, not the note's two" → REFUTED as blocking
- The count is real and was already test-pinned (`tests/test_llm.py:229-235`, `calls == 8`), but
  nothing in item 5 is falsified: every request is bounded by
  `min(decision_timeout_seconds, deadline − now)` (`llm.py:395-399`), throttle sleeps are clamped
  to the round deadline (`llm.py:407`), and the rolling shared budget
  (`llm.py:414-428`) refuses rather than waits
  (`tests/test_llm.py::test_six_throttled_seats_cannot_outrun_the_rolling_budget`,
  `::test_the_rate_budget_falls_the_seat_back_rather_than_waiting`). The note's arithmetic
  (design.md:452-461, 486-492) now states the 8-request worst case and the 120/min ceiling.

### O9 — fifth fallback cause `disabled` not in the note's enum → REFUTED as blocking
- Item 8 asks that the fallback be recorded and countable; `cause: "disabled"` is recorded on the
  `fallback` event and in `results.fallbacks` (`server.py:446-466`), and the CI replay is full of
  them. The note (design.md:571-573) now lists five causes. Working as designed.

### O10 — steward's seat-offset patch choice in `open` rooms → REFUTED as blocking
- Item 7 requires legality (asserted, `tests/test_baselines.py`) and tuned parameters (see O11);
  it does not prescribe the patch-choice rule. The offset is measured (126 vs 240 over 20 rounds)
  and pinned by `tests/test_baselines.py::test_open_room_stewards_spread_across_the_patches_instead_of_queueing`;
  `closed`/`partnership` take the plain maximum so partners can agree
  (`baselines.py:79-97`). The note (design.md:510-519) records it.

### O11 — no grid harness for the baseline parameters → RESOLVED (fix verified)
- `tools/tune_baselines.py` exists at head: a 6×6 grid over `CLEAN_POLLUTION_TRIGGER ×
  CLEANUP_STOCK_FLOOR`, four modules × three societies, deterministic, with an inadmissibility rule
  (a monoculture that kills the resource). `tests/test_tuning.py` runs the sweep in CI (test job
  green, 270 passed) and asserts the shipped pair is within 2 % of the grid's best admissible
  combination and is the best *conditional* one. The sweep moved a shipped value
  (`CLEAN_POLLUTION_TRIGGER` 0.35 → 0.15, `game/baselines.py:29`), which is what a real harness
  does. Item 7's second half holds.

### O12 — `game.docs.readme` was a `uri` → RESOLVED (fix verified)
- At head `game.docs.readme` is `{"type":"text","value":…}` and I verified the value is
  byte-identical to `src/coworld/examples/commons_family/README.md` (4004 chars); all four
  `pages[]` are inline text. `tests/test_manifest.py` pins it. Item 10 holds.

### O13 — no worst-case renderer fixture → RESOLVED (fix verified)
- `tools/ci/text_fixture/index.html` exists: loads the real `client/renderer.js` via
  `CommonsRenderer.attachReplay`, six full-cap 140-rune remarks at once (Latin, one unbroken
  140-rune word, CJK, surrogate-pair emoji), four module boards × five canvas sizes down to
  360 px, holds `data-replay-loaded` until every phase is checked, asserts its own strings are
  still 140 runes and that every rune came back out of `fillText` with no ellipsis
  (`index.html:198-220`). `ci.yml:250-268` drives it with `viewer_smoke.mjs --strict-text-bounds`,
  no `continue-on-error`. CI evidence at head (job 97579591886):
  `canvas text: 7518 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)`. Item 15 holds.

### O14 — full-cap remark ellipsized; no reserved band → RESOLVED (fix verified)
- `client/renderer.js`: `SAY_CAP_RUNES = 140` (matches `CommonsConfig().chat_max_chars`),
  `sayMetrics()` sizes the band from the cap in the bubble's own font, `computeLayout(w, h,
  say.band)` reserves it whether or not anyone speaks, `drawBubble` wraps with no line cap
  (`wrapLines(ctx, text, width - pad * 2, 0)`) and contains no `ellipsize`; `wrapLines` breaks an
  over-wide word on rune boundaries (`Array.from(word)`). Pinned by
  `tests/test_viewer_contract.py::test_the_say_band_is_reserved_and_sized_from_the_servers_rune_cap`
  and proven in a browser by the O13 fixture (0 ellipsized across 20 phases). Item 15 holds.

### O15 — a passing seat "held" patch 0 in partnership → RESOLVED (fix verified)
- `game/modules/harvest.py:87-98`: `answered = [decision.src != "pass" ...]`; unanswered seats are
  excluded from `named` and skipped in the void/trespass/unheld walk. `Decision.src` defaults to
  `""` (`modules/base.py:59`) so only the engine's own pass path carries the token. Verified by
  `tests/test_modules.py::test_a_seat_that_never_answered_holds_no_patch` and
  `::test_a_passing_seat_is_not_a_trespasser_in_a_closed_room`.

### O16 — player spectate loop unbounded, pings off → RESOLVED (fix verified)
- `player/player.py:45-52`: `SPECTATE_TIMEOUT_SECONDS = 1080`, `PING_INTERVAL_SECONDS = 20`,
  `PING_TIMEOUT_SECONDS = 30`; `player.py:104-110`: `asyncio.wait_for(websocket.recv(),
  timeout=remaining)` against a wall-clock deadline; every exit path returns 0. Verified by
  `tests/test_episode.py::test_the_spectate_loop_gives_up_instead_of_waiting_on_a_dead_game`.
  Item 5 holds.

### O17 — `norm_text` uncapped → RESOLVED (fix verified)
- `game/engine.py:42` `NORM_MAX_RUNES = 400`; `engine.py:118-121` pydantic field validator applies
  `truncate_runes`; manifest `config_schema.norm_text` carries `maxLength: 400` (verified in the
  JSON). `tests/test_replay_parse.py::test_the_posted_norm_is_rune_truncated_before_it_reaches_the_prompt`
  feeds a multi-byte norm and asserts strict-UTF-8 round-trip. Item 9 holds.

### O18 — `eaten_total` booked in step 5 not step 7 → REFUTED as blocking
- Behaviourally identical: `resolve` accumulates last (`mushrooms.py:114-115`), `dynamics` reads
  the updated totals (`mushrooms.py:132`), and the spawn weights are the same either way;
  `tests/test_modules.py` pins the totals after `resolve`. The note (design.md:255-260) now
  describes the code. No checklist item touched.

### O19 — 1:1 ownership only because `patch_count == num_agents` → REFUTED as blocking
- `num_agents` is pinned 6..6 in the schema and every variant carries `patch_count = 6`, so no
  shipped configuration can desynchronise them; the modulo keeps a hand-edited config *defined*
  (every patch exactly one owner, every allowed set in range), now pinned by
  `tests/test_modules.py::test_patch_ownership_stays_defined_when_the_counts_differ`
  (3/6/12 patches × three rights). No checklist item touched.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 32773426921 conclusion `success`, headSha `ef8e255…` (cited from `gh run view --json headSha,conclusion`); jobs test/docker-smoke/wasm-viewer all green. `git log -p -- tests/` over the repo's whole history (the run *is* the history, started 2026-08-24T17:40Z): zero deleted assertions, zero `skip`/`xfail`/marks (only `parametrize`), zero test files removed; the only two deleted lines are an import reflow and a record-key list replaced by a **longer** one (adds `public_effort`, `seat_public_effort`). Test count 232→270 across the fix range. |
| 2 replay re-derivation (per coordinator's binding note) | PASS | Determinism: `tests/test_episode.py::test_two_runs_with_the_same_seed_are_byte_identical_modulo_generated_at`; scores recomputed independently from round records: `::test_scores_match_the_formula_recomputed_from_the_round_records` (tests/test_episode.py:89-122). Viewer derives display ONLY from recorded state: `commons_family_replay.nim:59-193` copies `gains/scores/state/series/seat_frozen/seat_public_effort` out of round records, re-implements no physics (docstring nim:8-12; absence of re-derivation asserted by tests/test_viewer_contract.py:328-341). |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`), wired in `ci.yml:161` and required by `coworld-release.yml`'s certify marker; viewer fetches only `?replay=` (static_replay.js:67-89). No `/client/replay` route — the only textual matches are two sentences *denying* one (global_protocol_spec.md:43, design doc). |
| 4 both name spaces | PASS | `engine.py:307-357` observation takes aliases only; `tests/test_institutions.py::test_no_real_policy_name_appears_in_any_observation`; viewer maps via `makeNameMap`/`isBaselineFiller` (renderer.js:817-846); CI scorebug readout shows `Cog-E … COMMONS PROMPT` etc. |
| 5 degrade-never-hang | PASS | Per-request timeout `min(decision_timeout, deadline−now)` (llm.py:395-399); throttle sleeps clamped (llm.py:407); rolling budget refuses (llm.py:414-428); round barrier = batch-or-`round_seconds` with `min_round_seconds` floor (server.py:418-474); `play_deadline = PROCESS_START + 0.6×1200 = 720 s` checked before every round and in the paused branch (server.py:347, 393-413); `_play_game` guarded (server.py:328-343); player connect (150 s), spectate (1080 s) and pings bounded (player.py:39-52); linger hard-capped at 90 s (server.py:560-567). Worst case to artifacts 585 s ≤ 720 s ≤ 60 % of 1200. Deadline/no_players/pause paths all test-asserted. |
| 6 num_agents | PASS | `num_agents: 6` in all six variants + `certification.game_config` (verified in JSON); schema `minimum:6, maximum:6`; `docker_smoke.sh:112-153` enforces the four invariants with `SEAT-COUNT FAIL:` exits before any container; `SMOKE_SEATS` default `6` substituted in the script (line 56) as the second declaration; `grep -c "SEAT-COUNT" ` over the docker-smoke log of run 32773426921 = **0**; log shows `seats=6`, `all 6 player containers exited 0`, `smoke OK … reason=complete`. |
| 7 scripted baseline full legal episodes | PASS | `tests/test_episode.py::test_a_full_episode_settles_complete_and_writes_both_artifacts` (`reason == "complete"`) + the server-loop twin; legality fuzz 400 cases × 7 baselines × 4 modules incl. degenerate states (tests/test_baselines.py); tuned by grid harness `tools/tune_baselines.py` with `tests/test_tuning.py` in CI (see O11). |
| 8 LLM reply handling | PASS | Balanced-span extraction tolerant of prose (llm.py:211-240, six tests); exactly one retry with hint (llm.py:340-341, tests/test_llm.py:152-167); fallback to `steward` recorded as `fallback` event with cause and counted in `results.fallbacks` (server.py:446-466). |
| 9 rune-safe truncation | PASS | `truncate_runes` (engine.py:79-90) applied to message/note/prompt/policy names/scripted/norm; `ensure_ascii=False` + single UTF-8 encode (server.py:530-543, headless.py:161-162); multi-byte-at-cap tests (tests/test_replay_parse.py:160-183, tests/test_institutions.py:100-108); norm capped at 400 runes (O17). |
| 10 manifest validates | PASS | `game.docs.readme` `{"type":"text","value":…}` byte-identical to the README (verified programmatically); `pages[]` all `{"id","title","content":{"type":"text",…}}`; `game.protocols` carries both `player` and `global`, each `{"type":"uri","value":…}` objects. `tests/test_manifest.py` pins all of it. |
| 11 legible at 360 px | PASS | `chrome.css:282-294` `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }`; `.plate-label` hidden under 640 px (chrome.css:465-468) and again for six plates under 1100/640 px (chrome.css:614-627); `viewer-smoke.png` uploaded as evidence. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify (:167) → Upload the policies (:206, comment "BEFORE upload-coworld") → Upload the Coworld (:304) → Put the Coworld secret (:342). All three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files → no matches (exit-0 path taken); the four documented runtime angle-bracket names survive where allowed. |
| 13 viewer executes | PASS | `wasm-viewer` green at head in run 32773426921 with `needs: docker-smoke` (ci.yml:124); browser-load step ran (job 97579591886): `{"loaded":true,"ms":286,"clock":"ROUND 1 OF 8 · SETTLED",…}`, scrub probes `0%/50%/100%` returned three different clocks; no `continue-on-error` in the job. `data-replay-loaded` written by the renderer after the first drawn frame (renderer.js:1391, position asserted by tests/test_viewer_contract.py:110-119); `data-replay-error` written/cleared by the shell (static_replay.js:56, 107, 156). `config.nims:38-39` `MODULARIZE=1` + `EXPORT_NAME=CommonsReplayModule` and the shell calls `CommonsReplayModule()` (static_replay.js:160); no `onRuntimeInitialized` anywhere in the tree; pair asserted by tests/test_viewer_contract.py:57-91. |
| 14 chrome is the starter's | PASS | Verified by diff against the mounted `cogame-bullwhip`: `chrome.css` = starter + 3 in-place edits + banner-marked append; `index.html` = starter's page, zero nodes removed (diff shows only title/wordmark/clock text, script name, renamed renderer object, `fit`→`relayout` extension, and the appended `#modulebar`/`#patchgrid` block declaring only `cfModuleBar`/`cfPatchGrid`); renderer scaffolding keeps bullwhip's names/call graph, board functions legitimately game-specific. Transport rules: (a) `relayout()` sole writer of `--band`/`--hudscale` on `document.documentElement` (index.html:62-73, asserted); (b) nothing fixed-positioned in the band, `#endscreen` inside `#board-wrap`; (c) endcard keeps `bottom: var(--band, 0px)` and every seek removes `.show` before `setIndex` (renderer.js:1333-1334); (d) beats are labelled `<button type="button">` with `aria-label`/`title` that seek (renderer.js:1269-1282), and every emitted kind (`round, chat, sanction, collapse, patchdead, fallback, end`) has a `.beat-marker.<kind>` rule (chrome.css:484-491), both directions test-asserted. Fixed arena, no zoom/#viewpanel added (asserted). |
| 15 every drawn string fits | PASS | Load step: `canvas text: 2550 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — total ≠ 0, `never_inside = 0`, flag present (ci.yml:226-230). Worst-case fixture step (this repo draws model text, so it is required): `canvas text: 7518 drawn, 0 never inside the canvas, 0 ellipsized`, `{"loaded":true,"ms":1539}` (job 97579591886); the fixture loads the real renderer, six full-cap remarks incl. an unbroken 140-rune word/CJK/emoji, four boards × five sizes down to 360 px, and asserts its own strings are full-length with no ellipsis (tools/ci/text_fixture/index.html:198-220); say band reserved from the cap (renderer.js `sayMetrics`, statically pinned). |
| batch rule (simultaneous game) | PASS | One `ThreadPoolExecutor` batch per round covering every prompt seat (llm.py:311-330, called once per round at server.py:440-443); concurrency proven by `threading.Barrier(6)` in `tests/test_llm.py::test_all_six_seats_go_out_as_one_parallel_batch`. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| O1 | fixed, `5f4db0d` | `llm.py:356` catch-all + `server.py:328-343` guard + 4 tests | yes |
| O2 | fixed, `c9efc3a` | paused branch checks guard (server.py:393-403) + test | yes |
| O3 | fixed, `ae4e320` | `PROCESS_START` anchor + before-round check + test | yes |
| O4 | doc fix; provenance sound | my own diff against bullwhip confirms scaffolding kept, board game-specific; note now truthful | yes |
| O5 | doc fix | diff = exactly 3 hunks + append | yes |
| O6 | doc fix | edit is the item-13 ready bridge, test-pinned | yes |
| O7 | fixed, `bec5b4d` | `seat_public_effort` recorded (engine.py:465-484), Nim reads it (nim:141-143), both tests present | yes |
| O8 | refuted as bound; docs+test | time and rate bounds verified in code and tests | yes |
| O9 | refuted; docs | `disabled` is recorded and counted — item 8 satisfied | yes |
| O10 | refuted; measured+pinned | offset only in `open`; test asserts both halves | yes |
| O11 | fixed, `bb10814` | harness + CI sweep test + retuned 0.35→0.15 (baselines.py:29) | yes |
| O12 | fixed, `3e3ec60` | readme inline text, byte-identical to README (checked programmatically) | yes |
| O13 | fixed, `fd10089` | fixture + ci.yml step + CI `7518 drawn / 0 / 0` | yes |
| O14 | fixed, `7ab0eae` | say band, no-ellipsis bubble, rune word-break; fixture proves in-browser | yes |
| O15 | fixed, `cc82556` | `src != "pass"` skip (harvest.py:87-98), `Decision.src` default `""` (base.py:59), tests | yes |
| O16 | fixed, `ae119aa` | ping 20/30 + 1080 s spectate deadline + test | yes |
| O17 | fixed, `40d7156` | `NORM_MAX_RUNES=400` validator + schema `maxLength: 400` + test | yes |
| O18 | refuted; docs | behaviour identical, totals pinned after `resolve` | yes |
| O19 | refuted; test added | `test_patch_ownership_stays_defined_when_the_counts_differ` at head | yes |
| "no test loosened" | 2 deleted lines, both additive | `git log -p 5c64904..ef8e255 -- tests/` shows exactly those two (import reflow; key list replaced by a longer one) | yes |
| CI claims | 270 passed, smoke OK, canvas lines | test-job log `270 passed in 42.87s`; docker-smoke `smoke OK: seats=6 … reason=complete`; both canvas_text lines match verbatim | yes |

## Non-blocking observations (advisory, tied to no checklist item)

1. `HarvestModule.public_effort` credits a passing/disconnected seat with `effort_budget − 0 = 3`
   units of "restraint" per round (`harvest.py:231-235`), inflating the ledger's `public_effort`
   and the grader's `public_effort_share` for absent seats. O15 fixed the holding semantics only.
   Recorded by the fixer as NOTED; no checklist item names ledger semantics.
2. The wasm **expander** is smoke-tested only against a cleanup replay (the cert fixture is
   `module: "cleanup"`); the other three modules' boards are browser-exercised via the O13 fixture
   and the expander's payload contract via pytest, but a real harvest/allelopathic/mushrooms replay
   never passes through `cf_load_replay` in CI. A second smoke fixture would close it.
3. `/admin` remains unauthenticated (meadow's surface, kept deliberately); O2 removed the
   consequence that mattered (a pause can no longer hold the episode past its budget).

## What I could not verify

Nothing that the checklist makes blocking. The live LLM transport path (real Bedrock/Anthropic
credentials) and hosted certification are unexercisable from this sandbox by design; the checklist
gates them through unit stubs (item 8, verified), the docker-smoke no-credentials path (verified,
`llm_requests: 0` behaviour test-asserted), and phase-40/60 hosted runs, not through this verdict.

BLOCKING: 0
