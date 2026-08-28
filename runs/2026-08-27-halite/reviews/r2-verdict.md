blocking: 0

# r2 verdict — 2026-08-27-halite (`Metta-AI/cogame-halite`)

Head: `cb6dd64cb2c09be25e6b1dc47896d4e7bba87c8b`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
(read in order: checklist → design note → fresh clone at head + CI logs + own notes → `r2-review.md` → `r2-fixes.md`; r1 artefacts read afterwards as history)

Fresh clone verified: `origin/main` = `cb6dd64cb2c09be25e6b1dc47896d4e7bba87c8b`, working head identical.
Design note byte-identical in both copies (sha256 `795ceedb54d73299d2a842040a7efa77a3b4dce4e707cc08a1af3415359e480f`,
`runs/2026-08-27-halite/design.md` == `docs/plans/2026-08-27-halite-design.md`).

CI evidence (checked myself with `gh`, not accepted from the fixes report): run **33143385643**
(`ci.yml`, event `push`, branch `main`, headSha `cb6dd64…`), conclusion **success**; jobs
`test` 98759022654, `docker-smoke` 98759022571, `wasm-viewer` 98759346829, every step `success`,
no `continue-on-error` anywhere in the three workflows (grep: 0 hits).

The r2 review was written against the older sha `17fa7b5e…`; five fix commits landed since
(`064d914`, `a786a18`, `5491e0c`, `d13af52`, `cb6dd64`). Per the brief, a finding is resolved if
the code at `cb6dd64…` no longer exhibits it.

## Standing blocking findings

None.

## Refuted / resolved

### F1 — eight tests deleted by `76caaf0` → RESOLVED at head
- Evidence: `064d914` restores all eight to `tests/test_server.py`. I extracted each function
  body from `3df52bc:tests/test_server.py` (the pre-deletion file) and diffed against head:
  `test_the_player_failure_payload_is_exactly_two_keys` (:136),
  `test_a_seat_that_never_registers_is_logged_and_reported` (:153),
  `test_a_full_episode_writes_results_and_a_replay` (:181),
  `test_done_is_broadcast_before_the_artifacts_are_written` (:205),
  `test_replay_mode_serves_the_recorded_bytes` (:230) and
  `test_a_hanging_artifact_write_cannot_outlive_its_budget` (:347) are **byte-identical** to the
  deleted forms (the last differs only by a trailing section-banner comment). The remaining two
  were restored and then deliberately strengthened:
  `test_the_engine_budget_is_measured_from_process_start` was replaced by `d13af52` with
  `test_the_engine_budget_opens_before_the_lobby_and_not_at_import` (:245) plus
  `test_an_episode_in_an_old_process_still_starts_with_a_full_budget` (:280) — required by the
  F7 behaviour fix, 2 assertions → 4 — and
  `test_the_worst_case_container_time_fits_inside_the_platform_pin` (:297) was rewritten by
  `cb6dd64` with `assert worst == 718` and two new assumption blocks. Suite went from
  `342 passed, 2 skipped` at `17fa7b5` to **`354 passed, 2 skipped`** at head (job 98759022654
  log) — +12 tests, no new skip.

### F2 — unbounded per-turn `observe` write (reproduced hang) → RESOLVED at head
- Evidence: `a786a18`. `server/cogame_halite/engine.py:286-315` now writes every frame under the
  turn's own shared budget — `budget = deadline_ms / 1000.0` (:286),
  `await asyncio.wait_for(state.link.send(frame), budget)` (:293) — and on timeout drops the
  offending link (`state.link = None`, :306), substitutes the seat `disconnected` and logs
  `SEAT <n> … STOPPED READING its socket`; seats deprived of their window by the blocked write
  are substituted `host_error` and keep their links (:316-324, :383-389). The reply wait shares
  the same budget (`asyncio.wait(tasks.keys(), timeout=budget)`, :346). Tests:
  `tests/test_engine.py:117` (`…stops_reading_its_socket_cannot_stall_the_batch`),
  `tests/test_engine.py:147` (`…one_deadline_not_two`, asserts < 0.45 s with a 0.3 s deadline),
  the static scan at `tests/test_engine.py:91-115` now rejects a bare `await state.link.send`
  and asserts the exact `wait_for` form, and `tests/test_server.py:368`
  (`test_a_player_that_stops_reading_its_socket_cannot_stall_run_episode`) drives a **real**
  aiohttp websocket that never drains through `run_episode()` and asserts the episode settles
  `complete`. All green in run 33143385643.

### F3 — note claims a 718 s test that did not exist → RESOLVED at head
- Evidence: the test exists again at `tests/test_server.py:297`
  (`test_the_worst_case_container_time_fits_inside_the_platform_pin`): `pin == 720`,
  `worst == 718` computed from the enforcing constants
  (`DEFAULT_WALL_CLOCK_BUDGET_SECONDS` 660 + `DEFAULT_DIRECTIVE_DEADLINE_MS`/1000 18 +
  `ARTIFACT_WRITE_BUDGET_SECONDS` 20 + `SHUTDOWN_GRACE_SECONDS` 20), plus the two assumptions
  asserted (one-deadline in-flight turn via the F2 source greps; spacing floor
  600 + 10 + 18 ≤ 660). `server.py:59-77` carries the same arithmetic; the design-note appendix
  item 5 (both copies, identical bytes) now names the test.

### F4 — deleted shutdown-grace assertion → RESOLVED at head
- Evidence: `5491e0c`. `tests/test_server.py:127-129` again asserts
  `'await asyncio.sleep(SHUTDOWN_GRACE_SECONDS)' in source`; the code does it at
  `server.py:575`; the three route greps `76caaf0` added stay (:130-133).

### F5 — one widened manifest assertion → REFUTED as blocking
- Evidence: `tests/test_manifest.py` — the disjunction is entailed by the r1-F6 inline-docs fix
  (the serialised manifest no longer contains the path string `README.md`; I confirmed the old
  form is unsatisfiable at head), and the same commit added
  `test_the_inline_docs_are_the_repo_files_verbatim`, which asserts each inline `game.docs`
  value is byte-identical to its repo file — strictly stronger than the containment check it
  replaced. Net coverage up; checklist item 1 not falsified. (The reviewer already labelled it
  compensated; I agree.)

### F6 — 2 900-line test deletion in `git log -p -- tests/` → REFUTED as blocking
- Evidence: commit `c7c0853` is the root of the second of the two duplicated phase-20 chains
  (design-note appendix item 13); its tree contains only `vendor/`, which is why the log shows
  the 17 test files "deleted" there. `git ls-tree -r f192576 -- tests/` and
  `git ls-tree -r a3a7781 -- tests/` list identical blob hashes for all 17 files — nothing was
  lost, and removing the artefact would require a force-push over pushed history, which the
  rules forbid. A `git log` cosmetic, not a weakening.

### F7 — budgets anchored at module import → RESOLVED at head
- Evidence: `d13af52`. `server/cogame_halite/server.py:327` — `run_episode` takes the anchor at
  its own top (`self.started_at = time.monotonic()`), **before** the lobby wait, and hands it to
  the Engine (:362, `started_at=self.started_at`); `PROCESS_STARTED_AT` (:52) remains only the
  pre-episode default and the container-age figure in the settle log (:388-391). Both tests are
  load-bearing per the fixer's mutation check and pass at head:
  `tests/test_server.py:245` (anchor is the episode's, taken before the lobby, not import time)
  and `:280` (a 700 s-old process plays all six turns, `complete`/`full_time` — the review's
  exact repro, inverted). This also dissolves the review's second-order concern about a > 600 s
  pytest session, without any test-only shim.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | pass | run 33143385643 `success` (push, headSha `cb6dd64…`); full-history `git log -p -- tests/` audit: `76caaf0`'s deletion restored by `064d914` (byte-verified above); every other deletion hunk is a same-commit stronger replacement (`a786a18` static scan, `cb6dd64` worst-case test, `d13af52` anchor tests, `1620b74` per-turn fidelity, `3df52bc` smoke-key parse, `9a4aeff` corrected-to-upstream elimination behaviour under the differential gate); zero added `skip`/`xfail`/`skipif` in any tests/ hunk this run (grep over every commit); the suite's 2 CI skips are the pre-existing env-conditional pair (ctf-mount byte compare, whose coverage runs unconditionally via the recorded digests `tests/test_viewer.py:37-57` — and I verified `client/chrome_common.js`/`broadcast_core.js` are byte-identical to `/workspace/starters/coworld-ctf/client/*` against the mount myself — and the built-bundle node test, whose gate is the `wasm-viewer` job) |
| 2 replay re-derivation | pass | `tests/test_replay.py:131-224` — `rederive()` replays `seed` + recorded per-turn `orders` on a fresh `HaliteSim` and asserts **every** recorded per-turn `hash`, run for all four end reasons (`full_time`, `last_fleet`, `wall_clock`, `fault`); `replay.py` refuses to serialise without the load-bearing `stop` record; the viewer draws exactly that recorded per-turn state (`replay-viewer/halite_replay.nim`; page `render()` → `s:<turn>`), not a parallel recording |
| 3 static viewer | pass | `coworld_manifest_template.json:12-14` `game.replay_viewer.bundle = "static-replay-viewer"`; `tools/build_replay_viewer.sh` mode `100755` (git index), asserted executable in `ci.yml:157-168` and invoked by path; no `/client/replay` route (`server.py:194-204` registers exactly `/healthz /client/global /client/player /global /player` + `/replay-data`; `tests/test_server.py:124-133` greps stay); the bundle fetches only its `?replay=` URL and its own relative assets (`tests/test_viewer.py:273` relative-paths test) |
| 4 both name spaces | pass | `engine.py:136-138` observe carries alias/aliases only; `defaults.ALIASES` FLEET-*; real names only in `results.names`, replay header `names`, scorebug `realName()` (`client/replay_broadcast.html`) and endcard; `tests/test_privacy.py:32-117` enforces both directions |
| 5 degrade-never-hang | pass | lobby `wait_for(…, player_connect_timeout_seconds)` `server.py:328-331`; per-turn writes and replies under one shared budget `engine.py:286-346` (F2 fix); spacing floor bounded `engine.py:262-274`; guard 600 s / hard stop 660 s `engine.py:240, 488`; artifacts capped 20 s `server.py:377-379`; done-broadcast 5 s/socket `server.py:446, 451`; grace 20 s `server.py:575`; anchor at episode start `server.py:327` (F7 fix); worst case 718 ≤ 720 asserted `tests/test_server.py:297-344`; hung-seat and blocked-socket episodes complete under `asyncio.wait_for` in tests |
| 6 num_agents | pass | `num_agents: 4` inside `game_config` of `standard` (:557), `sprint` (:588), `richfields` (:619) and `certification.game_config` (:662), never at variant top level; `tools/ci/docker_smoke.sh:107-152` enforces all four invariants **before any container starts**, each exiting non-zero with a `SEAT-COUNT FAIL:` prefix, `SMOKE_SEATS` as the independent cross-check (`ci.yml:102` `SMOKE_SEATS: "4"`); grep of the docker-smoke job log (98759022571): **0** occurrences of `SEAT-COUNT FAIL`; `smoke OK: seats=4 … reason=complete`, `all 4 player containers exited 0` |
| 7 scripted baseline | pass | all-scripted episodes to natural end assert `reason == "complete"`: `tests/test_replay.py:48-61` (120 turns), `tests/test_server.py:181` (through the real server + artifacts), docker-smoke (`complete full_time [295, 978, 552, 789]`); legality over 200 random boards × both baselines incl. spawn-funding and convert-cell rules `tests/test_micro.py:72-108`; tuned by `tools/tune/grid_search.py` with the recorded run `docs/tuning/2026-08-28-micro-grid.md`, tied to the shipped constants by `tests/test_tuning.py` |
| 8 LLM reply handling | pass | `players/llm.py:149-182` balanced-brace extraction tolerating surrounding prose; one retry (12 s → 5 s, shortened prompt) `llm.py:313-329`; fallback keeps the previous directive, answers within the deadline with `source: "scripted"` and a cause note (`halite_player.py:71-79`); recorded — `results.llm_turns` counts `llm|retry` only (`engine.py:411-412`), the note event carries `source`, and `will retry` vs `falling back` log discipline is test-pinned (`tests/test_players.py:238-259`) |
| 9 rune-safe truncation | pass | one function `defaults.truncate_runes` (:143-160, also scrubs lone surrogates) used at every cap: note 140 / label 40 / stop_detail 200 / fallback detail 120 / strategy 2000 (`events.py`, `server.py:293`, `results.py:155`, `llm.py:115,218`); multi-byte-at-the-cap tests: `tests/test_players.py:193-215`, `tests/test_replay.py:81-89` (emoji stream through the whole path, strict `bytes.decode("utf-8")` + `json.loads`) |
| 10 manifest validates | pass | `game.docs.readme = {"type":"text","value":…}` (:461-463), `pages` = `[{id,title,content:{type:"text",value}}]` (:465-482); `game.protocols` carries both `player` and `global` as `{"type":"uri","value":…}` objects (:450-459); inline values byte-identical to repo files (`tests/test_manifest.py`); the installed `coworld==0.1.43` CLI's own `_load_template_manifest` + `validate_upload_manifest` run in the suite (`tests/test_manifest.py:327-341`, not skipped in CI — the dev group installs it) |
| 11 legible at 360 px | pass | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` `client/replay_broadcast.html:1067-1073`; secondary labels hidden under 640 px (`#stage.tiny` toggled at `w < 640`, :1104-1105, :1346); 360×640 pass green with `loaded: true` and the soak advancing (job 98759346829, `narrow_fixture.html` step) |
| 12 release order and scaffold | pass | `coworld-release.yml`: build (:159) → certify (:173, asserts the static-bundle liveness marker) → upload-policies (:216) → upload-coworld (:314) → wait-canonical (:352) → secret put (:410, namespace = game name); smoke runs against the image built in the same job (`ci.yml:93-104`); all three workflows present; `docker_smoke.sh` `100755`; `policies.json` = 2 `PLAYER_PROMPT` champions (both `USE_BEDROCK: "true"`) + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder gate **exits 0** (run here: "no placeholders") |
| 13 viewer executes | pass | `wasm-viewer` `needs: docker-smoke` (`ci.yml:148`), green at head including `Load the bundle in a real browser`: `{"loaded":true,"ms":292,"clock":"TURN 97 / 119 HAULING",…}`, soak `1 → 81 → 97 / 119` (job 98759346829); no `continue-on-error`; `data-replay-loaded` set on the worker's `loaded` message (`static_replay.js:175-178`), `data-replay-error` from both shell code paths (`static_replay.js:43-44`, page `fail()` :1744); bridge `ready` posted from the MutationObserver on `data-replay-loaded` (:1761-1768); playback opens at the game start structurally — the replay records no lobby frames (turns[0] is the populated board) and every seek clamps to `[0, turns.length-1]` (`seek()` :1668); link flags and bootstrap are a matched non-`MODULARIZE` pair, **both diffed against the same starter**: `config.nims` has no `MODULARIZE`/`EXPORT_NAME` (same as ctf's) and the worker boots on `Module.onRuntimeInitialized` (`static_replay_worker.js:206`) exactly as ctf's worker does (:188 there) |
| 14 chrome is the starter's | pass | `client/chrome_common.js` and `client/broadcast_core.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/*` (sha256 diff run here; also digest-pinned unconditionally in `tests/test_viewer.py:37-57`); `diff` of everything above the `HALITE additions` banner (:1001) against ctf's page = **one** changed line (the `<title>`) plus pure deletions of exactly the note-listed blocks (fpv, lockerroom, `#mmwarn`/viewpanel opt-out, momentum/lulls CSS with the four ids kept as `display:none` stubs per appendix item 1); transport rules verified in the page: `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` iterating to a fixed point (:1338-1357), `#chrome` is inset between the two bands (:112) so no overlay sits in the transport band (`#killfeed` bottom 76u inside `#chrome`), `#endcard` keeps `top/bottom: var(--topband)/var(--band)` (:720-721), is shown via `#endcard.on` (:732) and **every** seek path (`seek()` :1668 `showEndcard(false)`; beat buttons, scrub click, transport buttons, keyboard all route through `seek`) takes it down; beats are labelled `<button type=button>` elements with `title` + `aria-label` that seek on click (`haliteBeat` :1556-1575), with a CSS rule for every kind the page emits (`convert/collide/yardraze/eliminate/lead/guard`, :1157-1189); `#viewpanel`/zoom/minimap **removed** (markup, CSS, wiring, ids), correct for the fixed 21×21 arena |
| 15 every drawn string fits | pass | the two replay passes report `canvas_text.total == 0` **by construction** (wasm sprites + DOM strings; `tests/test_viewer.py:429` asserts no viewer file calls `fillText`/`strokeText`, so the zero cannot hide a regression); the text gate is the worst-case renderer fixture: `tools/ci/renderer_fixture.html` loads the **shipped** `index.html` (`?shim=1`), injects a full-cap 140-rune note on every seat (fixture asserts each is exactly CAP runes, :215) at three canvas sizes incl. 360×640, driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step (:293-306) and gated non-vacuously (:308-324, `total >= 12`, `never_inside == 0`); at head: `renderer fixture: 7124 text runs measured, 136 crossed an edge, 0 never inside`; the feed reserves a band sized from the server cap (`#killfeed` band CSS :1115-1147 with the 140-rune rationale in the comment) |
| parallel batch (simultaneous game) | pass | `engine.py:276-346`: every observe frame written before any reply is awaited, one `asyncio.wait` with one shared timeout, never a per-seat loop; `tests/test_engine.py:45-73` asserts the per-turn send/receive ordering from a trace, plus the static scan (:91-115) |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `064d914`, 8 tests restored verbatim from `3df52bc` | byte-level function-body diff: 6 identical, 2 restored-then-strengthened (`d13af52`, `cb6dd64`); +12 tests in CI | yes |
| F2 | fixed, `a786a18`, write shares the turn budget | `engine.py:293` `wait_for(send, budget)`; 3 new engine tests + real-websocket server test; CI green | yes |
| F3 | fixed, `cb6dd64`, test restored + assumptions pinned | `tests/test_server.py:297-344`, `assert worst == 718`; note appendix names the test; both note copies sha `795ceedb…` | yes |
| F4 | fixed, `5491e0c` | assertion back at `tests/test_server.py:127`; code at `server.py:575` | yes |
| F5 | refuted (forced, net coverage up) | old form unsatisfiable post-inline-docs; byte-identity test is stronger | yes |
| F6 | refuted (history artefact) | `c7c0853` tree is vendor-only; blob hashes identical across the two chains | yes |
| F7 | fixed, `d13af52`, anchor at episode start | `server.py:327`; both tests present and reproduce the review's repro inverted | yes |
| CI claims | run 33143385643 success, `354 passed, 2 skipped`, smoke `complete`, fixture `7124/136/0`, `SEAT-COUNT FAIL` = 0 | all re-checked from the job logs myself | yes |

## Non-blocking observations

- `engine.py:103-107` — the `started_at` docstring still says "The server passes **process
  start**"; since `d13af52` the server passes the episode's own start (`server.py:327`). The
  code, `server.py`'s comments, `AGENTS.md` and the note are correct; this one docstring is
  stale. Cosmetic.
- The 718 s worst-case sum covers hard stop + one in-flight turn + artifacts + grace. Two other
  end-phase waits are each explicitly bounded but sit outside that sum: `_broadcast_done`
  (`server.py:439-451`, ≤ 5 s per still-open socket) and the dead-seat failure report
  (`engine.py:600-614` → `uris.write_uri`, worst ≈ 91.5 s against a hanging HTTP endpoint,
  outside the 20 s artifact cap). Reaching them past 720 s requires a hard-stop episode
  compounded with a pathological platform endpoint; the checklist's own clause — "the episode
  settles and scores inside 720 s" — is met with margin (scoring completes by ≈ 678 s worst),
  and every wait carries an explicit bound, so this is consistency housekeeping (the artifact
  cap exists for exactly this class), not a blocking finding.
- `server.py:541-542` replay-mode serving loop (`while True: await asyncio.sleep(3600)`) is an
  intentional serve-forever for the platform-managed replay pod, not an episode wait.

BLOCKING: 0
