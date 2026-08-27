blocking: 0

# r1 verdict — pommerman

Head: `9fa80f8db7288a9031962e446019b3fe430e1691` (main)   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
(read order followed: checklist → design note → repo at head with my own notes → `r1-review.md` → `r1-fixes.md`; no contamination)

CI at head: run **33108749059**, `conclusion: success`, `headSha == 9fa80f8db7…` (verified via
`gh run view --json headSha,conclusion`). Jobs: `manifest` 98646967385 ✓, `docker-smoke`
98646967813 ✓, `test` 98646967908 ✓, `wasm-viewer` 98647575517 ✓.

## Standing blocking findings

None.

## Refuted / resolved

The review was written against `25efdbb7`. Nineteen findings; the reviewer self-classified most
as non-blocking. At the current head every finding is either resolved (fix verified from the
code, not from the fixer's claim) or refuted. Dispositions, each verified independently:

### F1 — say/view stripped from every directive record → RESOLVED at head
- Evidence: `src/pommerman/sim_types.nim:32` — `MaxDirectiveRunes* = 4000`;
  `src/pommerman/directives.nim:314-339` — `boundedDirectiveRecord` now sheds the **view first**
  (`if carriedView.kind != JNull: carriedView = newJNull()`) and only then trims `say`;
  `tests/test_pom_control.nim:408-435` (`fullCapSaySurvivesWithARealView`) asserts a 100-emoji
  `say` survives at exactly `MaxSayRunes` **with** `view.kind == JObject`, including with the
  bomb pool full. Was true at 25efdbb; fixed by `34e3bfa`, not refuted.

### F2 — `canvas_text: total 0`, fixture measured DOM only → RESOLVED at head
- Evidence: `tools/ci/renderer_fixture.html:153` installs its own `fillText`/`strokeText`
  measurer, `:178-195` publishes merged `window.__coworldTextBounds`, `:444-484`
  (`assertCanvasTextIsReal`) fails itself on zero draws / no fuse numeral / no radio badge / any
  edge-crossing draw; `:306-330` drives the shipped `client/broadcast_core.js`
  (`window.BroadcastCore.create`) on a fixture-owned canvas. CI wasm-viewer step *Worst-case
  renderer fixture*: `canvas text: 110 drawn, 0 never inside the canvas (0 draws crossed an
  edge), 0 ellipsized (--strict-text-bounds)` and `{"loaded":true,…}`. Fixed by `deca701`.

### F3 — degraded `kick` is `stay`, not `hide` → REFUTED
- Evidence: `src/pommerman/control.nim` — Step C is only reached when the bomber's own cell has
  no danger inside the horizon (Step B returns first), and `hideTarget` scores every
  never-dangerous cell identically with ties broken by fewest steps, which the own cell wins at
  zero — so from every state Step C can be reached in, `hide` **is** `stay`.
  `tests/test_pom_control.nim:240-284` pins the equivalence (`kicked == chooseAction(sim, seat,
  danger)` under `okHide`) over >500 degraded kicks. Behavioural identity; the note's Step C
  table holds.

### F4 — spacing sleep inside the turn budget → RESOLVED at head
- Evidence: `src/pommerman/decide.nim:253-272` — the sleep runs first, then
  `let turnStart = getMonoTime()` is taken **after** the rate floor, so the 12 s `turnBudgetMs`
  window covers only the two attempts and the promised retry is no longer skipped on turns that
  waited. All bounds intact: `sim_config.nim` clamps `turnSpacingMs ≤ 60 000`,
  `wallClockBudgetSeconds ≤ 640`. Fixed by `02b45f4`; the ticks-don't-advance-during-the-wait
  mechanism difference is declared in errata 4 and violates no checklist item.

### F5 — no errata in the committed note → RESOLVED at head
- Evidence: `docs/plans/2026-08-27-pommerman-design.md:1734` — `## Errata — what shipped…`,
  22 entries; byte-identical to the run copy (`diff -q` clean). Fixed by `76d1078` + `9fa80f8`.

### F6–F9, F18, F19 — declared advisory deltas → correctly non-blocking, now recorded
- F6 (`--preload-file` dropped): nothing in `replay-viewer/pommerman_replay.nim` reads a virtual
  FS; `Dockerfile.replay-viewer` asserts no `.data`. Errata 11. No checklist item.
- F7 (five unused files absent): nothing references them. Errata 14.
- F8 (state-JSON envelope): viewer reads the shipped shape; pinned by test. Errata 12.
- F9 (`.tiny` at 640): 640 is what checklist item 11 asks for; the starter's 620 would be wrong
  here. Errata 10.
- F18 (`showPlayerLabels` inert): fails closed; documented at the field (`2b28c5c`). Errata 15.
- F19 (replay size / per-frame hashes): 189 260 B in CI, chain re-derives frame-for-frame.
  Errata 6.

### F10 — tick-budget bound 4000 ms vs note's <1 s → RESOLVED (tightened)
- Evidence: `tests/test_pom_sim.nim:598-600` — `when defined(release): check elapsed < 1000
  else: check elapsed < 4000`. A tightening, not a loosening (`66350e6`).

### F11 — live `/global` feed empty → RESOLVED at head
- Evidence: `src/pommerman/episode.nim:32,187` (`EpisodeFrame.records` filled),
  `src/pommerman/server.nim:463-468` (`frameChats = episodeFrame.records` in the live branch),
  consumed at `server.nim:493` (`stepEvents(sim, tracker, frameChats)`). Fixed by `98cd1e3`.

### F12 — camper's private dodge horizon → RESOLVED at head
- Evidence: `src/pommerman/baselines.nim:209-216` — `let danger = sim.dangerNow()` (the config
  horizon the controller reads), with the reason in the comment. Fixed by `04e1026`.

### F13 — docker smoke green on `fault` → RESOLVED at head
- Evidence: `tools/ci/docker_smoke.sh:306-318` — `if str(reason) == "fault": raise
  SystemExit(f"episode ended with reason={reason}: …")`. Fixed by `05f987d`; mode still 100755
  (`git ls-files -s` → `100755`).

### F14 — absent seat has `fallbackTurns == 0` → REFUTED (semantics pinned)
- Evidence: `tests/test_pom_engine.nim:99-109` asserts `deadSeats[3]`, the closed failure
  payload, one `disconnected` record per turn played, **and** `fallbackTurns[3] == 0` /
  `llmTurns[3] == 0`. `fallbackTurns` counts a policy that failed to answer; an absent seat
  never had one, and conflating them would make an absent seat indistinguishable from an LLM
  that timed out 36 times — the number phase 60 reads. No checklist item names it.

### F16 — `game.docs` `"type":"uri"` vs the checklist's `"type":"text"` → REFUTED
- Evidence: the starter's own manifest
  (`/workspace/starters/coworld-ctf/coworld_manifest_paintbot.json`) uses `"type":"uri"`, as do
  `cogame-factorio` and `cogame-moba` (verified in the mounts). The requirement item 10 states —
  `readme` and `pages[].content` as `{type,value}` objects with `id`/`title`, and
  `game.protocols` carrying **both** `player` and `global` — is met
  (`coworld_manifest_template.json`, verified by parse), and the `manifest` job validates the
  substituted manifest under the installed `coworld==0.1.43` loader (green in 33108749059).

### F17 — server still serves `/client/replay` → REFUTED
- Evidence: the route (`src/pommerman/server.nim:36`) is the starter's own developer-local page
  (`/workspace/starters/coworld-ctf/src/ctf/server.nim` serves the same); nothing declared
  points the platform at it — `game.replay_viewer = {"bundle":"static-replay-viewer"}`, no
  `/client/replay` string anywhere in `*.json|yml|sh`, and
  `tests/test_pom_manifest.nim:97` now asserts `"/client/replay" notin $manifest` (`5761285`).
  Item 3's substance — static bundle declared, executable hook, viewer contacts nothing but the
  replay URL (`static_replay_worker.js:113` is the only fetch) — all verified.

### F15 — emoji on only two capped fields → RESOLVED at head
- Evidence: `tests/test_pom_replay.nim:262-341` — policy label (U+1F9E8), fallback detail
  (U+1F4A5), stop detail, `say` (U+1F525) and `notes` (U+1F6E1) all filled past their caps with
  4-byte emoji; asserts strict-UTF-8 (`validateUtf8() == -1`) and exact rune-cap lengths out of
  the Python summary view. Fixed by `a6b722c`.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 33108749059 success at 9fa80f8 (headSha verified). `git log -p --since=2026-08-27T16:03Z -- tests/`: only tightenings — `check elapsed < 4000` → release `< 1000` (66350e6); `if seen == 0: checkpoint(…)` soft-pass → `check seen >= 1` (6eacb0a); `inherited.len` 60619 → 60743 is a char-count→byte-count correction, the SHA-1 pin `349E9658…` **unchanged** and both re-verified by recomputation against the shipped file. No skip/xfail, no deleted assertion, no removed test file. |
| 2 replay re-derivation | PASS | `tests/test_pom_replay.nim:29-126` record→re-derive for all four end rules, `hashMismatchTick == -1`; per-frame hash check `src/pommerman/replay_runtime.nim:107-118`; viewer wasm imports the same sim (`replay-viewer/pommerman_replay.nim:13`), no parallel recording |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer.bundle == "static-replay-viewer"`; `tools/build_replay_viewer.sh` mode 100755 (git index); worker fetches only the given replay URL (`static_replay_worker.js:113`); no declared `/client/replay` (test_pom_manifest.nim:97) |
| 4 both name spaces | PASS | observation carries aliases only (`decide.nim:seatView`, `roster.nim:16` `IdentityNames`); real names in scorebug/endcard only (CI scorebug text shows real policy names); `tests/test_pom_labels.nim` |
| 5 degrade-never-hang | PASS | attempt 8 s / retry 3 s via `CURLOPT_TIMEOUT`, monotonic 12 s turn budget (`decide.nim:205,272-285`), spacing clamp ≤60 s, `wallClockBudgetSeconds` clamped ≤640 (`sim_config.nim:71-72`) = 53 % of 1200 s, budget guard latch, lobby/gameOver tick bounds; smoke episode 65 s real, `reason=complete` |
| 6 num_agents | PASS | 4 in both variants' `game_config`, cert fixture, schema min=max=4; four SEAT-COUNT invariants in `docker_smoke.sh:106-152` before container start; `grep 'SEAT-COUNT' docker-smoke log` = **0 hits**; log: `smoke OK: seats=4 … reason=complete` |
| 7 scripted baseline | PASS | `tests/test_pom_engine.nim:15-44` all-scripted episode → `reason == complete`, zero-sum; `test_pom_control.nim:40-89` 200 states × both baselines bounded; swept pick pinned in `tools/ci/baseline_tuning.json` + `tune_baselines.nim --check` re-run in ci.yml |
| 8 LLM reply handling | PASS | `extractJsonObject` fence/prose-tolerant (`directives.nim:85-123`); one retry (`decide.nim:275 while … attempt < 2`); fallback = sapper proc, recorded (`fallbackRecord`, seven causes); "falling back" logged for phase 60 |
| 9 rune-safe truncation | PASS | `truncateRunes`/`sanitizeSay` on every replay-bound string; `test_pom_control.nim:377-390` and `test_pom_replay.nim:252-341` feed 4-byte emoji at every cap, assert `validateUtf8() == -1` |
| 10 manifest validates | PASS | docs readme+2 pages and protocols player+global as `{type,value}` objects (uri, the starter ecosystem's shape); `manifest` job green under installed `coworld==0.1.43` |
| 11 legible at 360 px | PASS | `client/replay_broadcast.html:1743-1748` `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }`; `.tiny` toggled at `boardW < 640` (`page_script.js:606`) hiding plate labels (`game_block.html:101-103`) |
| 12 release order & scaffold | PASS | coworld-release.yml: manifest :159 → certify :173 → upload-policies :217 → upload-coworld :315 → confirm canonical :353 → secret put :393; 4 policies (2×`PLAYER_PROMPT`, champion #2 carries `ply_bac48eb1-…`, 2×`PLAYER_SCRIPTED`); placeholder grep over the five files exits 1 (no hits); both scripts 100755 |
| 13 viewer executes | PASS | wasm-viewer `needs: docker-smoke` (ci.yml:323); browser-load step ran: `{"loaded":true,"ms":346,…}`, soak `0/228 → 24/228 → 36/228`; no `continue-on-error` anywhere; `data-replay-loaded` set in the `'loaded'` branch after first ingest (`static_replay.js:161-165`, worker :127-131), `data-replay-error` in `showFailure` (:14-20); non-MODULARIZED build + `Module.onRuntimeInitialized` worker, both coworld-ctf's |
| 14 chrome is the starter's | PASS | `chrome_common.js` byte-identical (diffed against the mount); `replay_broadcast.html` **reproduces diff-clean** from the starter via the committed `tools/build_broadcast_page.py` (I re-ran it) — removals are exactly the note's list; `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`page_script.js:600-610`); `#endcard { bottom: var(--band, 0px) }` (:571), shown with `.on` (:582), scrub-click removes `.on` immediately and every other seek clears it next frame via `renderEndcard` (worker ingests a frame synchronously per input); beats are labelled `<button>`s that seek (`game_block.html:255-275`) with CSS for exactly {firstblood,kick,death,collapse,fallback,end}; `#viewpanel` removed (fixed 11×11 arena), asserted absent |
| 15 drawn text fits | PASS | fixture loads the shipped page **and** the shipped `broadcast_core.js` on a measurable canvas; full-cap 100-rune say on all four seats at 360/640/1280; asserts full-length strings; CI: `canvas text: 110 drawn, 0 never inside … 0 ellipsized (--strict-text-bounds)`; the shipped-page step's `total: 0` is the declared OffscreenCanvas artifact (errata 8) and is not the gated number |
| simultaneous batch | PASS | one `RequestBatch` for all open seats per attempt, single `curl.makeRequests` (`decide.nim:286-302`); no per-seat call loop |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, 34e3bfa | cap 4000, view sheds first, say survives w/ real view (test) | yes |
| F2 | fixed, deca701 | fixture measures real canvas draws; CI 110/0/0 | yes |
| F3 | refuted + test | equivalence logic sound; test pins it over >500 cases | yes |
| F4 | fixed, 02b45f4 | turnStart after the rate floor; bounds intact | yes |
| F5 | fixed, 76d1078+9fa80f8 | errata §1734, byte-identical to run copy | yes |
| F6–F9 | advisory, errata | errata 10/11/12/14 present; no checklist item | yes |
| F10 | fixed, 66350e6 | release <1000, debug <4000 — tightening | yes |
| F11 | fixed, 98cd1e3 | live branch passes `episodeFrame.records` | yes |
| F12 | fixed, 04e1026 | camper calls `sim.dangerNow()` | yes |
| F13 | fixed, 05f987d | smoke exits non-zero on `reason=fault` | yes |
| F14 | refuted, pinned | `fallbackTurns[3]==0` asserted with rationale | yes |
| F15 | fixed, a6b722c | emoji on policy/detail/stopDetail/say/notes | yes |
| F16 | refuted | starter + 2 mounts use `uri`; CLI validates | yes |
| F17 | refuted + test | starter parity; nothing declared; test added | yes |
| F18 | advisory, 2b28c5c | comment at the field; inert, fails closed | yes |
| F19 | advisory, errata 6 | 189 260 B in CI; chain re-derives | yes |

## Non-blocking observations

- `ci.yml`'s `test` job reads `vars.NIM_TESTS` / `vars.NIM_TESTS_DEBUG_ONLY` /
  `vars.NIM_TESTS_RELEASE_ONLY` repo variables, which could narrow the suite without a commit.
  At this run every `tests/*.nim` ran in both modes (verified from the job log), so no finding —
  but a future rerun should re-check the log, not the workflow file.
- The `Load the bundle in a real browser` step's `canvas_text total: 0` is permanent for the
  shipped page (OffscreenCanvas Worker). The gate lives entirely in the renderer-fixture step;
  if that step is ever removed, item 15 loses its only teeth.

BLOCKING: 0
