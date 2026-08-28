blocking: 0

# r1 verdict — vizdoom-deathmatch
Head: `7e2d1d0aed87e8ef603fc59a2b54eea753a9443e` (main)   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
CI at head: run **33132259050**, conclusion `success`, `head_sha 7e2d1d0a…`, jobs `test` / `docker-smoke` / `wasm-viewer` all `success` (verified via `gh run list` + `gh run view --json jobs`, not accepted from the fixer).

The review (`r1-review.md`) was written against `3e49fa42…`; I verified every finding at the
**current head**, per the standard that a finding that was true and has since been fixed is
refuted, not standing. I read the diff, the checklist and the CI logs and formed my own notes
before opening `r1-fixes.md`; the fixer's table was then audited claim by claim.

## Standing blocking findings

None. All four of the reviewer's blocking findings are fixed at head, and my independent
checklist pass (below) found no item the reviewer missed.

## Refuted

### B1 (reviewer F1) — "No test records a replay and re-derives it from the bytes" → REFUTED at head
- Evidence: `tests/test_vzd_replay.nim:115-322` at `7e2d1d0` (added in `d9c563e`) — `recordEpisode`
  writes a real `.replay` through `openReplayWriter` / `writeJoin` / `writeInputMaskChange` /
  `writeHash` (`:145-216`), `rederive` parses it back with `parseReplayBytes` and re-simulates
  through `initReplayRuntime` / `stepReplay` — the wasm viewer's own entry point
  (`replay-viewer/vzd_replay.nim` → `src/vzd/replay_runtime.nim:14`) — and the suite
  `"record then re-derive, every end reason"` (`:266-322`) asserts `back.matched == back.recorded`
  ("frame by frame, all of them"), `mismatchTick < 0`, `not failed`, plus the ending `phase`/`endRule`,
  for `full_time`, `wall_clock` **and** `sim_fault`. The viewer derives its display from that same
  re-derivation: `buildReplayViewerPacket` builds every frame from the re-stepped `sim`
  (`replay_runtime.nim:83-138`). Checklist item 2 is satisfied at head.

### B2 (reviewer F2) — "viewer draws model text, `canvas_text.total == 0`, no renderer fixture" → REFUTED at head
- Evidence: `tools/ci/renderer_fixture.html` (19 078 B) + `tools/ci/renderer_fixture_frame.json`
  (emitted by `tools/gen_renderer_fixture_frame.nim` through `buildStateJson` itself) exist at head
  (added in `f420b57`); `.github/workflows/ci.yml:371-393` runs it in its own step
  (`Worst-case renderer fixture (model text at full cap)`) with `viewer_smoke.mjs
  --strict-text-bounds` against a copy of the freshly built bundle. The fixture loads the shipped
  `index.html` in an iframe, shims only the wasm entry (`renderer_fixture.html:20-23,119+`), drives
  full-cap 96-rune radio on all eight seats at 360/640/1280 px, mirrors every line box onto a real
  canvas, and asserts its own strings are full length (`:378-391`: `longestRadio !== CAPS.radio` →
  fail). CI log at head: `canvas text: 198 drawn, 0 never inside the canvas (0 draws crossed an
  edge), 0 ellipsized (--strict-text-bounds)` — `total` 198, `never_inside` 0. The main smoke step
  keeps `--strict-text-bounds` (`ci.yml:353-358`) and the layout fix reserves a killfeed band for
  the full-cap remark (`replay_broadcast.html` `dm-radio-row`). Checklist item 15 is satisfied.

### B3 (reviewer F3) — "baseline tunables not tuned; harness is the starter's and cannot compile" → REFUTED at head
- Evidence: `tools/tune_baselines.nim:23-26` at head imports `vzd/[sim, control, directives,
  baselines]` and sweeps this game's four knobs (`RusherHuntRadii`/`SentryHuntRadii`/`MedRadii`/
  `PostRotations`, 36 cells × 6 episodes); `tools/ci/baseline_tuning.json` records the whole grid
  with `chosen = {rusherHuntPx: 120, sentryHuntPx: 260, medPx: 360, postRotation: 1, wins: 4/6,
  margin: 6}` (inside the note's [+2,+10] band); `src/vzd/baselines.nim:60-63` ships exactly those
  values; `tests/test_vzd_tuning.nim` (83 lines) pins shipped == recorded == grid winner and that
  the harness is this game's; `ci.yml:158-161` runs `tune_baselines --check`, and that step is
  green in run 33132259050 (job `test`, step "The baseline tunables are still the grid harness's
  pick"). Checklist item 7's second sentence is satisfied.

### B4 (reviewer F4) — "chrome_common.js not byte-identical and the change unrecorded" → REFUTED at head
- Evidence: `diff starters/coworld-ctf/client/chrome_common.js client/chrome_common.js` at head is
  exactly two lines (`:14` comment path, `:72` `window.CTF_WIRE` → `window.VZD_WIRE`); both files
  are 40 022 bytes (verified with `wc -c`). The design note now records that patch as a named,
  minimal diff with its functional justification (`design.md:1225-1249`, §Viewer → Chrome
  provenance: `gen_wire_constants.nim` emits `window.VZD_WIRE={…}` and
  `Dockerfile.replay-viewer` hard-asserts it), which is exactly item 14's escape hatch
  ("the only admissible change is a named, minimal patch recorded in the design note"), and
  `tests/test_vzd_viewer.nim:20-29` pins the byte length, the sha and the namespace both ways.
  Checklist item 14(i) is satisfied.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 — CI green, no test loosened | PASS | run 33132259050 `success` on main at `7e2d1d0a…`, all 3 jobs green (gh run view). `git log -p --since=2026-08-27T21:00Z -- tests/`: every fix-round hunk read — F5/F18/F22/F24 add tests, F29 replaces a tautology (`marchRays` called twice with identical args) with a strictly stronger 16-vs-96-column cross-check off `buildStateJson`, F7 replaces the `extraSteps` loop with the viewer's own `applyTrailingStop`; no deleted assertion, no skip, no widened tolerance. The 23:27–23:28Z scaffold churn (repeated init/fork D→A of the whole tests/ tree) recreates the same files within seconds and the head suite is a strict superset (121 `test` blocks vs ≤109 at every earlier tree). |
| 2 — Replay re-derivation | PASS | `tests/test_vzd_replay.nim:266-322` (all three end reasons, `matched == recorded`); viewer display built from the same re-derivation (`src/vzd/replay_runtime.nim:14-49,83-138`; `replays.nim:419` applies `stop` via `applyStopRecord`, `:513-526` `applyTrailingStop`) |
| 3 — Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}` (line 13); `tools/build_replay_viewer.sh` present, mode 100755, wired as the build hook and exec-bit-asserted in `ci.yml:260-284`; `static_replay{,_worker}.js` are the starter's after rename (worker fetches only `message.replayUrl`); no `/client/replay` declared to the platform (occurrences are docs/dev-mode text only) |
| 4 — Both name spaces | PASS | agent side alias-only: `decide.nim seatViewNode` uses `sim.cogAlias` throughout (`:138,156,163`), `egoview.nim:167,178`; `showPlayerLabels: false` in all three game_configs; viewer side: `rosterJson` carries `name` (real, `broadcast.nim:458-463`) **and** `alias` (`:483`), plates/endcard/`#povBadge` read them |
| 5 — Degrade-never-hang | PASS | attempt loop `while open.len > 0 and attempt < 2` with monotonic `turnBudgetMs` check before each attempt (`decide.nim:508-516`), `makeRequests(batch, deadline)` (`:536-537`), bounded spacing sleep `sleep(min(spacingMs, …))` (`:487`), rate guard converts seats instead of sleeping (`:435-478`), budget guard vs `max(turnBudgetMs, spacingMs)` (`:421-427`); `wallClockBudgetSeconds 660` stop (`server.nim:1415-1434`), lobby cap (`:1548-1580`); worst case 24×17.143 s + 100 s lobby + ~19 s ≈ 530 s < 660 < 720 s (60 % of the manifest's `episode_timeout_minutes: 20`); `test_vzd_manifest.nim:138-163` pins both |
| 6 — `num_agents` | PASS | 8 in `variants[arena/pool].game_config` and `certification.game_config`; `len(certification.players)=8`, `len(certification.game_config.players)=8`; `docker_smoke.sh:106-152` enforces all four `SEAT-COUNT FAIL` invariants before any container plus the `SMOKE_SEATS` (default `8`, the `<SEATS>` substitution) cross-check; `grep -c "SEAT-COUNT FAIL"` over the run-33132259050 log = **0** |
| 7 — Scripted baseline full episodes | PASS | `test_vzd_engine.nim:55-73` (1080-tick all-scripted → `reason == "complete"`, `endRule == "full_time"`, exact zero sum); bounded orders/masks `test_vzd_control.nim:22-97`; docker-smoke ran the production binary to `reason=complete`; tuning: see B3 |
| 8 — LLM reply handling | PASS | `extractJsonObject` tolerant parse → `parseSeatDirective` repairs (`decide.nim:552-568`); retry once (`:508`); fallback to `rusherFor` — the same proc as the published baseline (`:270-279,593-606`) — with `fallback` records (`cause ∈ {timeout, parse_error, transport_error, throttled, no_credentials, rate_guard, budget_guard}`) and `results.fallbackTurns`; asserted in `test_vzd_control.nim:156-283` |
| 9 — Rune-safe truncation | PASS | `sanitizeSay/Radio/Note` → `truncateRunes`; `fallbackRecord` detail cap (`decide.nim:219`); `stopDetail` capped (`test_vzd_replay.nim:66-80`); reply capped in **bytes** on a rune boundary (`truncateBytes`, `decide.nim:553`, test `test_vzd_control.nim:264-282`); 4-byte emoji at every cap asserted valid UTF-8 (`test_vzd_replay.nim:36-64`, `test_vzd_control.nim:237-262`) |
| 10 — Manifest validates | PASS | `game.docs = {readme:{type:text,value:6189 ch}, pages:[rules.md, observation.md, protocol.md]}` all `{type:"text",value:…}`; `game.protocols.player` and `.global` both `{"type":"uri","value":…}` objects |
| 11 — Viewer legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`replay_broadcast.html:4100-4105`); labels hidden under `#stage.tiny` (`:4139-4147`), toggled at `boardW <= 620` (`:4037`, the starter's threshold, under the item's 640 px line); asserted `test_vzd_viewer.nim:140-160` |
| 12 — Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (`:159`) → Certify locally (`:173`, `--timeout-seconds 300`) → Upload policies (`:216`) → Upload coworld (`:314`) → Put secret (`:410`); ci.yml docker-smoke builds its own image in-run before the smoke; all three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2×`PLAYER_PROMPT` + 2×`PLAYER_SCRIPTED`, champion #2 = `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep over the five files returns nothing (exit 0); only the four sanctioned runtime `<…>` names survive |
| 13 — Viewer executes | PASS | (i) `wasm-viewer` green at head incl. `Load the bundle in a real browser` (`{"loaded":true,"ms":1606,…}`, `soak: 10s of playback kept advancing ("0 / 1080" -> "185 / 1080" -> "233 / 1080")`), `needs: docker-smoke` (`ci.yml:247`), no continue-on-error; (ii) `data-replay-loaded` set in the shell's `'loaded'` branch (`static_replay.js:161`), `data-replay-error` in `showFailure` (`:14-20`); (iii) playback opens at the spectator start and clamps every seek: `initReplayRuntime` walks to first `Playing` tick and `seekReplay(replayStartTick())` (`replay_runtime.nim:32-48`), `seekReplay` clamps `clamp(tick, replayStartTick(), replayMaxTick())` (`replays.nim:820`), restart/step-back/transport all route through it (`:881-944`); (iv) `config.nims` has no `MODULARIZE`/`EXPORT_NAME` and the worker sets `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) — the consistent non-modularised pairing, both files starter-derived rename-only (diff verified) |
| 14 — Chrome is the starter's | PASS | (i) `chrome_common.js` = starter + exactly the 2-line named patch recorded in the note (B4); (ii) `replay_broadcast.html` (4 762 lines vs starter 4 660) is the starter's page with the DEATHMATCH block appended under the banner; I diffed the full pre-banner region against the starter: every hunk is a removal or re-mapping the note enumerates (#viewpanel/zoom/minimap + arrow-pan keys, steal/return/capture beat CSS, the eight label re-maps, Ctf→Vzd adapter and `PaintballChrome`→`VzdChrome` renames, 4-kit→2-kit fetch, endcard 5-cell remap); (iii) `relayout()` sets `--band`/`--topband`/`--hudscale` on `:root` (`:4037` region, asserted `test_vzd_viewer.nim:60-67`); `#endcard { bottom: var(--band, 0px) }` + shown via `#endcard.on` (`:898,920,3636`) and every seek removes it (`:1900`); beats are labelled `<button>`s that seek (`dmBeat`, `:4337-4357`, `CTX.send('s:'+tick)`), CSS for exactly the six emitted kinds (`:4232-4257`), `dmBeat` never shadows the hoisted `markBeat`; (iv) `#viewpanel` removed entirely — markup, CSS, `attachMinimap` call, `ZOOM_STEP`, ids — for a board whose aspect is constant 1235/659 in every variant (`test_vzd_viewer.nim:104-113`, `test_vzd_engine.nim:137-144`) |
| 15 — Every drawn string fits its frame | PASS | main smoke: `canvas text: 0 drawn` (covers nothing — not evidence, per the item) **and** the required worst-case renderer fixture exists and gates: own ci.yml step with `--strict-text-bounds`, `canvas text: 198 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`; full-cap radio/say/notes on all eight seats at 360/640/1280 px; fixture asserts its own strings are full length (`renderer_fixture.html:378-391`); the killfeed reserves a band sized for the full-cap remark; ci.yml's smoke step carries `--strict-text-bounds` (`:358`) |
| simultaneous batch | PASS | one `RequestBatch` over all open seats, one `makeRequests` call per attempt (`decide.nim:519-537`); no per-seat request loop anywhere |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `d9c563e` | `test_vzd_replay.nim:115-322` records + re-derives all three end reasons through the viewer's runtime | yes |
| F2 | fixed, `f420b57` | fixture + frame + own CI step, ran green (198/0/0); killfeed band reserved; residual (server-composited `say` bubble unmeasurable by a browser fixture) honestly declared — bubble is the starter's fixed-width renderer sized to the 10-rune cap; not a gap in the item's gate | yes |
| F3 | fixed, `20374b8` | harness imports `vzd/…`, 36-cell grid, record committed, `--check` in CI green, `test_vzd_tuning.nim` pins; shipped 120/260/360/1 == recorded pick | yes |
| F4 | fixed, `b99caec` | note carries the named 2-line patch with justification; diff vs starter is exactly those 2 lines, 40 022 B both sides | yes |
| F5 | fixed, `13ef7af` | `sim.nim:1668-1670` — `recordKill` only when teams differ; test shoots a teammate, asserts kills 0 / teamKills 1 / net −1. (The unconditional `recordKill` at `sim.nim:1313` is the arc/grenade path, unreachable under the deathmatch loadout — noted below) | yes |
| F6/F23 | fixed, `8489a8d` | `server.nim:1963-1977` builds the record without a view; `mapSent` set at prompt build (`decide.nim:498-504`) | yes |
| F7 | fixed, `7420580`+`a78b75f` | `applyStopRecord` applied on playback (`replays.nim:419`) + `applyTrailingStop` (`:513-526`); exercised by F1's wall_clock/sim_fault tests | yes |
| F9 | fixed, `8302feb` | `scanTeamLead` hill-off branch now adds `sim.teamNet(team)` (`replays.nim:565-590`) | yes |
| F10 | fixed, `656514e` | endcard rows emit five cells incl. signed `net` and `acc` (pre-banner diff read) | yes |
| F18 | fixed, `bf88b09` | `truncateBytes` at `decide.nim:553`; byte-cap test with 16 KiB of emoji | yes |
| F22 | fixed, `7e2d1d0` | `scriptedDirective` takes the previous directive; shout only on intent change; test asserts change/silence/re-shout | yes |
| F24 | fixed, `c0880ff` | `roster.nim:782-783` reports `sim.gameMap.name`; pool test pins the divergent case | yes |
| F25 | fixed, `eb1121c` | `replay_summary.py:169` `tickCount` from `finalTick`/stop tick, `byteCount` separate | yes |
| F26 | fixed, `86b3f63` | registrar docs/echo/default say `rusher | sentry` | yes |
| F29 | fixed (tautology), `fb18bcf` | new test compares the 16-ray strip against the 96-column `fp` strip off `buildStateJson` at the six shared bearings; the declined line-of-sight half is correctly declined (bullet predicate ≠ vision march) | yes |
| F8, F11–F17, F19–F21, F27, F28 | NOT FIXED, advisory | none falsifies a checklist item (my independent pass reached the same conclusion on each: F11 — item 4 needs the mapping, not eight plates, and the mapping is present; F13/F14/F15 — repo hygiene vs the note, no checklist item; F12/F16 — cones/halo are note readouts, not checklist items; F19 — event vocabulary is a note contract; F27 — single candidate is the *safer* behaviour under item 5; F28 — item 13's gate is the browser smoke, which exists and runs) | yes |

## Non-blocking observations

- **Deleted-not-disabled is actually gated-not-deleted** (reviewer F13/F14): `paint.nim`,
  `global.nim`'s flag/paint/grenade draw families, the ctf label vocabulary, and the deleted
  mechanics' art all survive behind `LoadoutDeathmatch` gates, and the page keeps unreachable
  hill/flag/perk chrome. Sound (smoke `complete`, CI green) but contrary to the note's
  "deleted, not disabled"; the note's own forbidden-vocabulary grep (test 39) is shipped as an
  allow-list instead. First candidates for a cleanup round, none checklist-relevant.
- **Pre-scan beats can only ever contain `gameover`** (F8): `replays.nim:664-670` keeps the
  starter's steal/return/capture vocabulary, so kill/streak/lead/fallback beats appear only as
  playback passes them (and the spoilers switch under-delivers ahead of the playhead). The
  markers still exist as labelled seeking buttons, so item 14(iii)(d) holds.
- **`sim.nim:1313`** still calls `recordKill` unconditionally on the arc-fire (grenade) path;
  unreachable in this loadout, but it would silently reintroduce F5 if grenades ever returned.
- **Design-note prose is stale in two places**: §Scripted baselines still prints the pre-sweep
  constants (`rusherHuntPx = 520`, `(seat div 2) mod 4`) that the recorded sweep replaced, and
  the momentum/eyes/plates prose describes a per-seat scorebug shape (F11) the page does not ship.
  Note edits, not code defects.
- **History churn**: the repo was re-initialised ~8 times at 23:27–23:28Z (whole-tree D→A pairs,
  including tests/). Declared here because a raw `git log -p -- tests/` shows large deletions;
  each deletion is immediately followed by an identical or superset re-add, and the head suite is
  the largest tree in the history. Not a loosening.

BLOCKING: 0
