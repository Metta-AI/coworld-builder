blocking: 0

# r1 verdict — atari-cabinet

Head: `405fa22891754177ee0482a8128ca77ce2bbcb0d`   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision addendum)   Independent read written before reading fixes: **yes** (`r1-fixes.md` not read at all, per brief; the review `r1-review.md` was read only after my own pass over the tree, the diff `ac7eca8..405fa22`, and the CI logs).

Repo cloned fresh to `/tmp/judge-cogame-atari-cabinet` at 405fa22. CI evidence: run **33001674720** (`gh run list -R Metta-AI/cogame-atari-cabinet --branch main -w ci.yml`), headSha `405fa22…`, conclusion **success**, jobs `test` / `docker-smoke` / `wasm-viewer` all success; full log pulled with `gh run view 33001674720 --log`.

## Standing blocking findings

None. Both of the review's blocking findings are fixed at the current head (see §Refuted), and my own checklist pass found nothing that falsifies an item.

## Refuted / resolved-at-head

The review was written at `ac7eca8`; eleven fix commits landed after it. A finding that was true then and is false now is refuted at head, not standing.

### r1-1 — fixture ellipsizes full-cap remarks → REFUTED (fixed at head)
- Evidence: `tools/ci/renderer_fixture.html` at 405fa22 contains no ellipsis and no measure-and-cut loop — `tests/test_viewer.nim:216-243` asserts `"\u2026" notin fixture` and `"text.length - 2" notin fixture`; the feed row now wraps (`client/replay_broadcast.html:` `.feed-row.cab-note-row { … white-space: normal; }`, asserted by `tests/test_viewer.nim:253-`). CI run 33001674720, step "Render the worst-case text fixture at 360 / 620 / 1280 px": `canvas text: 102 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — the 12-ellipsized log line the reviewer cited no longer occurs. Fixed by `5620442` + `52104a2`.

### r1-2 — fixture is a re-implementation of the renderer → REFUTED (fixed at head)
- Evidence: the fixture now drives the shipped path twice over. (a) `tools/ci/gen_render_fixture.nim` + `tools/ci/worst_case_frame.nim` bake a real Sprite-v1 packet through the shipped `src/cabinet/global.nim` board builder (full-cap 48-rune `say` + 160-rune `note` on all four seats); `tools/ci/renderer_fixture.html` loads the bundle's own `./broadcast_core.js` and `./wire_constants.js`, calls `window.BroadcastCore.create(…)`, `core.ingest(packet)`, fetches the real chrome CSS from the bundle's own `index.html`, and self-checks every note is at the full `maxNoteRunes` (`renderer_fixture.html:305-316`) — asserted by `tests/test_viewer.nim:216-243` (`src="./broadcast_core.js"`, `window.BroadcastCore.create(`, `board_packet.bin`, `fetchText('./index.html')`). (b) A new Nim gate `tests/test_render_text.nim` asserts, from the packet bytes with no browser, that "every baked string is inside the board", "no two baked strings overlap", "the bubbles sit inside the RESERVED band", and "the worst case really is the worst case" (`placement.text[…].runeLen == MaxSayRunes`). The reviewer's "Could not determine" (right-edge bubble overflow) is settled by the same test. Fixed by `52104a2` + `5620442`.

### r1-3 — budget measured from before the inter-batch sleep → fixed at head
- Evidence: `src/cabinet/decide.nim:373-380` — `turnStart` is re-taken **after** the rate floor (`decide.nim:440-443`: `turnStart = engine.lastBatchStart`), with the reviewer's exact scenario quoted in the comment; the double-fallback-record side effect is also gone (`decide.nim:452-456`: no record at the budget break, "the tail below … records exactly ONE fallback per seat per turn"). New test: `tests/test_engine.nim:163` "the inter-batch floor is NOT charged to the per-turn budget". Fixed by `edaedfd`.

### r1-5 — near_miss emitted nowhere → fixed at head
- Evidence: `src/cabinet/sim.nim:595-618` emits `NearMiss` on the crossing tick (presentation-only: `sim_types.nim:197-199` marks `nearMisses` "never mixed into gameHash"; golden hashes unchanged in that commit); `client/replay_broadcast.html:4291-4295` renders the "SO CLOSE" feed row; `tests/test_physics.nim` +90 lines pin it end-to-end. Fixed by `971134c`.

### r1-7 — far paddle aims at the near line → fixed at head
- Evidence: `src/cabinet/control.nim:90` — `if before > FarPaddleDepth and after <= FarPaddleDepth:` records the far line's own crossing; `control.nim:361` comments the retarget; `tests/test_control.nim` +53 lines; `tests/data/golden_hashes.json` regenerated in the same commit (autopilot output changed, sim rules did not — see §GameVersion). Fixed by `37ebd6c`.

### r1-9 — whole-stance replacement on one illegal field → fixed at head
- Evidence: `src/cabinet/decide.nim:292-341` — repair is now per field ("The repair is PER FIELD" with clamps for `post`/`lead_ticks`/`aggression` and bulwark substitution only for the individually-unresolvable reference fields, wholesale fallback only if still invalid); `tests/test_engine.nim:322` "ONE illegal field is repaired, the rest of the stance survives" and `:360`. Fixed by `96dafca`.

### r1-14 — viewer smoke never soaks → fixed at head
- Evidence: `.github/workflows/ci.yml:360-365` carries `--soak 12`; run 33001674720's "Load the bundle in a real browser" step logs `soak: 12s of playback kept advancing ("0 / 1488" -> "922 / 1488" -> "970 / 1488")`; `tests/test_viewer.nim:244-251` asserts `--soak 12` and both `--strict-text-bounds` flags in ci.yml. Fixed by `d6a0e09`.

### r1-15 — certify has no `--timeout-seconds 300` → fixed at head
- Evidence: `.github/workflows/coworld-release.yml:186-189` — `coworld certify dist/coworld_manifest.json --no-open-report --timeout-seconds 300`; the vacuous test was replaced with one that reads the certify invocation itself (`tests/test_manifest.nim:240-248`, `"--timeout-seconds 300" in invocation.split("- name:")[0]`) — a strengthening, not a loosening. Fixed by `0cf5ce8`.

### r1-18 — `#cab-legend` reads `var(--band)` without fallback → fixed at head
- Evidence: `client/replay_broadcast.html:4051` — `bottom: calc(var(--band, 0px) + 6 * var(--u));`; a repo-wide grep finds **zero** `var(--band` reads without the `, 0px)` fallback, and `tests/test_viewer.nim:61-77` now asserts every read carries it. Fixed by `2368858`.

### r1-19 — zoom wiring survives the panel's removal → fixed at head
- Evidence: `grep -n "core\.(zoomAt|setZoom|attachMinimap)" client/replay_broadcast.html` → no call sites (only the comment at `:3819-3821` naming the removal); the starter's `z`/`x` key, ctrl-wheel and pinch zoom paths are gone (`:3674-3676` records the removal); `tests/test_viewer.nim:99-108` asserts all three calls are absent. Markup/CSS were already gone at review time. Fixed by `f85ce99`.

### r1-23 — four design-note assertions untested → substantially fixed at head
- Evidence: `405fa22` adds the no-show test (`tests/test_server.nim` +75 lines: failure file lands, `failed_policy_index == 0`, episode completes) — and found a real bug doing it (`declarePlayerFailure` was unreachable; `sim_state.nim:103-` adds `lobbyBudgetSpent` and `server.nim:521-531` uses it) — plus the 15 s post-artifact `/healthz`+`/global` grace assertion. Two of the four (disconnect-revive, held registration under race) remain untested and are recorded as such in the commit message; both paths are exercised by docker-smoke's four real player containers. No checklist item names them → advisory residue, not blocking.

## Standing non-blocking observations (reviewer's, confirmed at head; none maps to a checklist item)

- **r1-4 stands**: `src/cabinet/sim.nim:559` is still the only `serveBall` call site, with `offsetIndex = 0`; `SecondBallDirOffset` (`sim.nim:26`) remains dead code and the note's "+7 indices" second-ball offset never applies. Deterministic and hash-stable; design-note deviation only.
- **r1-6 stands**: `control.nim:305` still picks `j = ±6` for `chase` by side difference. The note's two halves genuinely disagree; the code follows the stance glossary.
- **r1-8 stands**: the shadow/committed split at `control.nim:315-330` is still an addition to the note's step 4, documented in-code as what makes `lead_ticks 0` late.
- **r1-10, r1-11, r1-12, r1-13 stand** as written (release-direction rule, hash-after-end-checks ordering, `last_standing` at zero alive, `RenderScale = 1`): all deterministic, identical in both builds, and outside every checklist item.
- **r1-16, r1-17, r1-20, r1-21, r1-22, r1-24 stand** as observations; each was correctly filed non-blocking and I verified the underlying checklist clauses independently (items 6, 7, 9, 14 all pass — see below).

## Judge's own findings (advisory; no checklist item)

- `tools/ci/check_gameversion.sh:31` still points at `CONST_FILE="src/ctf/sim_types.nim"`, which does not exist in this repo (`src/cabinet/sim_types.nim` is the real path). The script is wired into no workflow, so it is dormant — but it would exit 1 with "could not read GameVersion" if anyone ran it as documented. One-line fix.
- The design note's state-JSON example and a few constants (`teams[k].policies`, `RenderScale`, `darkbg.png`) describe the code inaccurately; the code is internally consistent (already recorded by the reviewer as r1-13/r1-21/r1-22).

## GameVersion ruling (coordinator question c)

`GameVersion` stayed `"1"` across the fix commits while `37ebd6c` changed autopilot behaviour and regenerated `tests/data/golden_hashes.json`. **Advisory, not a checklist violation**, from the repo's own determinism boundary:

- `sim_types.nim:29-31` defines GameVersion as the **"Replay compatibility gate"** — the number that identifies which rules re-simulate a recorded replay. The boundary (AGENTS.md §determinism, `sim_types`/`control` split) is explicit that `control.nim` sits **outside** it: only the recorded command bytes cross, and playback never re-runs the autopilot. `37ebd6c` touched only `control.nim` (+ tests), so every replay recorded before it still re-derives bit-exactly under the post-fix build — replay compatibility was not broken, which is the only thing GameVersion gates. The other two sim-adjacent fix commits are provably outside the hash: `971134c` adds `nearMisses` marked "PRESENTATION ONLY: never mixed into gameHash" and left the golden hashes untouched; `405fa22` adds a lobby predicate that is not hashed.
- The golden fixture changed because it pins a four-**bulwark episode trajectory** (baseline stance → autopilot → bytes → hashes), which is upstream of the recorded bytes — a different thing from the replay-compatibility contract. The fixture regeneration was done in the same commit as the behaviour change, with the same pin density (every 48th tick × 3 ROMs), and CI's determinism gate passed against it: this is the prescribed procedure, not a loosening.
- What *is* wrong is the documentation: AGENTS.md ("Bump it in the same commit as any rule change… If it has to change, the RULES changed") and the fixture's own embedded note over-claim — by their letter, `37ebd6c` should have bumped GV. By the boundary's substance it should not have (a bump would have gratuitously invalidated nothing, since no replays exist pre-release, but it would also have falsely announced a rules change). Recommend tightening the AGENTS.md/fixture wording to "if the **sim** rules changed" or bumping GV on trajectory-affecting autopilot changes — either is fine; neither falsifies checklist item 1 (nothing loosened), item 2 (re-derivation tested and green at head), or any other item.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **33001674720** at `405fa22`, conclusion `success`, all 3 jobs success. `git log -p --since="2026-08-26T12:37Z" -- tests/` = 11 fix commits; every hunk read: additions/strengthenings only (test_manifest swapped a vacuous grep for a targeted one; test_viewer swapped literal-presence checks for provenance checks; test_physics/test_control/test_engine/test_server/test_render_text add tests; test_server hunk is a helper-arg refactor). `golden_hashes.json` regenerated in `37ebd6c` with an autopilot fix — same pin density, sim rules unchanged, see §GameVersion. No skip/xfail/tolerance-widening anywhere; the log's only `FAILED (` string is the workflow's own echo source; 18 test files ran debug+release (perf/baselines release-only per repo var). |
| 2 Replay re-derivation | PASS | `tests/test_replay.nim:10-91` (per ROM: re-steps recorded bytes, `hashMismatchTick == -1` over >900 ticks, keyframe scan + seek converge); `tests/test_determinism.nim:19-64` (a–c incl. golden fixture); viewer path is the same code: `replay-viewer/cabinet_replay.nim` → `replay_runtime`/`replays.stepReplay` → `checkReplayHash` per tick; display built from the re-derived sim (`buildReplayViewerPacket`). |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, invoked by path at `ci.yml:282`; no `/client/replay` route in `server.nim` and none in the manifest; `coworld-release.yml:210-216` hard-fails on a pod-served viewer; `static_replay.js` fetches only the replay file. |
| 4 Both name spaces | PASS | Aliases only on the seat side (`decide.seatViewJson`, alias board labels); real names in `broadcast.rosterJson`, endcard, `results.names`; `tests/test_locality.nim:114-148` asserts both halves; smoke scorebug shows both ("RED **P2** SCORE 62.25 …" in run 33001674720). |
| 5 Degrade-never-hang | PASS | Batch deadlines `attempt1Ms`/`retryMs` → `CURLOPT_TIMEOUT` (`decide.nim:459-467`); bounded floor sleep (`:436-439`); per-turn `turnBudgetMs` (`:452`); budget guard (`:389-397`); lobby `lobbyJoinTimeoutTicks` + `lobbyBudgetSpent` (`server.nim:521-531`); bounded serve sampler 32 + fixed scan (`sim.nim:177-190`); frame limiter bounded (`server.nim:374-395`); 660 s stop (`server.nim:502-507`); 660 ≤ 720 = 0.6×1200 (`episode_timeout_minutes: 20`); player dial 240×500 ms. No unbounded loop found. |
| 6 num_agents | PASS | `num_agents: 4` in all three variants' `game_config` and in `certification.game_config`; `certification.players` = 4 = `game_config.players`; `docker_smoke.sh:106-150` implements all four `SEAT-COUNT FAIL:` invariants before any container starts, `SMOKE_SEATS` default 4 (`:54`); `grep -c "SEAT-COUNT FAIL"` over the **full log** of run 33001674720 = **0**; `smoke OK: seats=4 results=552B replay=41416B reason=complete`, `all 4 player containers exited 0`. |
| 7 Scripted baseline | PASS | `tests/test_baselines.nim:68-94` runs 20 all-scripted warlords episodes to the natural end with `check episode.sim.endReason == ReasonComplete` per seed; `:26-66` validates every emitted stance against the schema in all 3 ROMs (bounds, enums, live/alive references, byte ∈ 0..242); grid harness `tools/tune_baselines.nim` + committed pick `tools/ci/baseline_tuning.json` (10×3×4 grid, 20 seeds) + `tests/test_tuning.nim` re-asserting it. |
| 8 LLM reply handling | PASS | `stances.extractJsonObject:96` (prose/fence tolerant); one retry `while open.len > 0 and attempt < 2` (`decide.nim:449`), throttle fast-fail (`:506-512`); fallback recorded with cause enum (`:499-500`, `:527-528`) and counted (`results.fallbackTurns`); per-field repair (`:292-341`); `tests/test_engine.nim:223` (exactly one retry), `:207` (zero on throttle), `:255` (no-credential records). |
| 9 Rune-safe truncation | PASS | `stances.truncateRunes:53-60` (`runeLen`/`runeSubStr`) at every cap (note 160, say 48, policy 48, detail 200, record 600, prompt 4000); `tests/test_stances.nim:94-119` 4-byte emoji straddling the 48-rune cap, valid-UTF-8 round trip; `tests/test_replay.nim:99-157` strict `json.loads(out.decode("utf-8"))` on real multi-byte replay bytes. |
| 10 Manifest validates | PASS | `game.docs.readme = {"type":"text","value":…}` (5 502 ch) + 3 pages each `{id,title,content:{type:"text",value}}` (8 540/8 530/4 557 ch); `game.protocols.player` (8 530 ch) **and** `.global` (17 077 ch), both text objects. |
| 11 Legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`replay_broadcast.html:3954-3959`); `@media (max-width: 640px)` hides `.lives-label`/`.cab-out` (`:4028-4031`); `#stage.tiny` (≤620) collapses brick bars and hides the legend (`:4019-4027`); starter's `--hudscale` clamp + `tiny` toggle intact (`:3889-3892`). |
| 12 Release order + scaffold | PASS | `coworld-release.yml`: build (`:159`) → certify `--timeout-seconds 300` (`:186-189`) → Upload the policies (`:220`) → upload-coworld (`:318`) → secret put (`:356`), one job, in order; smoke/certify run against the manifest+image built in the same run; all three workflows present; `docker_smoke.sh` mode 100755; `policies.json`: 4 distinct policies, 2×`PLAYER_PROMPT` + bulwark + spinner, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep over the five files returns nothing → gate exits 0 (ran it). |
| 13 Viewer executes | PASS | Run 33001674720, `wasm-viewer` (`needs: [test, docker-smoke]`, `ci.yml:245`), step "Load the bundle in a real browser" ran, no `continue-on-error`: `{"loaded":true,"ms":346,…}`, `soak: 12s of playback kept advancing ("0 / 1488" -> "922 / 1488" -> "970 / 1488")`. Markers: `static_replay.js:161` sets `data-replay-loaded` on the Worker's first `loaded` frame; `:20` sets `data-replay-error`; `:32` mismatch tick. Flags and bootstrap from the **same** starter: `config.nims` diff vs coworld-ctf = 4 rename-only lines, **no MODULARIZE / EXPORT_NAME**; `static_replay_worker.js:188` uses `Module.onRuntimeInitialized` + `importScripts(… cabinet_replay.js)` — the matching non-modularized form; `tests/test_viewer.nim:164` pins it. |
| 14 Chrome provenance | PASS | `client/chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diff empty; sha pinned by `tests/test_viewer.nim:27`). `replay_broadcast.html` = starter's page (4 407 vs 4 660 lines) + game block under the `ATARI-CABINET additions to the inherited coworld-ctf chrome` banner (`:3923`); CSS above the banner unmodified except the note's listed removals (`#fpv`/`#povBadge` 528-832, `#viewpanel` markup 1506-1549, `?viewpanel=0` rule) — remaining above-banner edits are the starter's own PB_MODE game hooks retargeted to CAB_MODE and null guards. Transport: (a) `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` (`:3890-3896`); (b) zero `var(--band` reads without the `, 0px)` fallback; overlays ride `bottom: calc(var(--band, 0px) + …)` (`:4051`); (c) `#endcard { top: var(--topband,0px); bottom: var(--band,0px) }` (`:745-747`), shown via `#endcard.on` (`:758`), removed on every non-gameover frame (`:1713`) so every seek takes it down; (d) beats are labelled `<button>`s that seek (`button.beat-marker` `:4062`), with one CSS rule per emitted kind (`concede`/`breach`/`eliminated`/`last_standing`/`over`, `:4069-4093`, matched to `ScrubberBeatKinds` by `tests/test_viewer.nim:110`). `#viewpanel` removed outright — markup, CSS, **and** wiring: no `core.zoomAt`/`setZoom`/`attachMinimap` call remains (grep). |
| 15 Every drawn string fits | PASS | Main smoke: `canvas text: 0 drawn` (Worker/OffscreenCanvas — total 0, not evidence, as the checklist itself says) **with `--strict-text-bounds` carried** (`ci.yml:365`). The model-text class is covered by the worst-case fixture in its own step (`ci.yml:386-423`, `--strict-text-bounds`): loads the shipped `broadcast_core.js`/`wire_constants.js`, ingests the packet the shipped `global.nim` baked (full-cap say+note × 4 seats, entrance settled), 360/620/1280 px, asserts its own strings are full-length; run 33001674720 logs `canvas text: 102 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. Backstop in Nim: `tests/test_render_text.nim` ("every baked string is inside the board", "no two baked strings overlap", bubbles inside the reserved band, full-cap self-check). Reserved band: bubbles baked into a fixed top band, feed rows wrap (`.cab-note-row`, `white-space: normal`). |
| Addendum: one parallel batch | PASS | `decide.turnBatch:343-361` builds one `RequestBatch` over every open seat; one `curly.makeRequests(batch, …)` call per attempt (`:466`); no per-seat transport loop; `tests/test_engine.nim:113` ("all four seats' calls go out in ONE PARALLEL BATCH") + `:137` (eliminated seat dropped) + `:152` (spacing). |

Nothing was unverifiable from the tree or the cited CI evidence; no item counts as blocking on that rule.

## Fixer report audit

Per the brief, `r1-fixes.md` was **not read** — this table audits the fixer's *commits* (the disposition of record) against my own verification instead.

| finding | fixer commit says | I verified at 405fa22 | agrees |
|---|---|---|---|
| r1-1 | `5620442` widened band, never a cut | wrap CSS + no-ellipsis fixture + CI `0 ellipsized` | yes |
| r1-2 | `52104a2` fixture drives the SHIPPED text path | broadcast_core.js + global.nim packet + test_render_text | yes |
| r1-3 | `edaedfd` budget times the CALLS | turnStart re-taken after floor; single fallback record; new test | yes |
| r1-5 | `971134c` near_miss emitted, feed says "SO CLOSE" | emitter at sim.nim:595-618, feed row :4291-4295, not hashed, goldens untouched | yes |
| r1-7 | `37ebd6c` far bar aims at FarPaddleDepth | control.nim:90; goldens regenerated (trajectory, not rules) | yes |
| r1-9 | `96dafca` illegal field repaired, not the whole stance | per-field repair decide.nim:292-341 + 2 tests | yes |
| r1-14 | `d6a0e09` smoke actually SOAKS | `--soak 12` in ci.yml; soak line in run log | yes |
| r1-15 | `0cf5ce8` certify gets `--timeout-seconds 300` | flag on the certify invocation; test reads that invocation | yes |
| r1-18 | `2368858` `--band` with 0px fallback | `:4051` + zero fallback-less reads + test | yes |
| r1-19 | `f85ce99` zoom wiring removed, not just the panel | no zoomAt/setZoom/attachMinimap call sites + test | yes |
| r1-23 | `405fa22` no-show tested; it never fired | lobbyBudgetSpent fix + failure-URI test + grace test; 2 of 4 assertions remain untested, declared | yes |
| r1-4/6/8/10/11/12/13/16/17/20/21/22/24 | no fix commit | all still stand as written; none maps to a checklist item — correctly left as advisory | yes |

BLOCKING: 0
