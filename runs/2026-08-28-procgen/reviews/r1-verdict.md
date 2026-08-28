blocking: 0

# r1 verdict — procgen

Head: `545c79116b1d5c977984135e8baed1b89f8d3dca` (verified `git -C /workspace/cogame-procgen rev-parse HEAD`)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15, read in full before anything else)
Review judged: `runs/2026-08-28-procgen/reviews/r1-review.md` (F1–F25, written against `556cb50`; the tree has since gained 14 commits)
Independent read written before reading the review: **yes** (notes at `/tmp/independent-notes.md`, written from the tree, the design note and the CI logs only).
`r1-fixes.md`: **not read**, per the brief — the fixer's claims were audited from the commits themselves (`git log -p`), never from its self-report.

---

## Summary

The review reported **zero blocking findings** and 25 advisory observations. I attempted to refute or
reproduce each at the current head, and I ran the full 15-item checklist pass independently. Fourteen
fixer commits landed after the review; **13 of the 25 findings are now moot because the code changed**
(each verified below at head, not taken from any report), and the rest are either accurate advisory
observations that no checklist item names, or descriptions of behaviour that is checklist-conformant.
Nothing I found — the reviewer's or my own — falsifies a checklist item at `545c791`.

**Blocking findings standing: 0.**

---

## Standing blocking findings

None.

---

## Disposition of the review's findings (F1–F25) at head

| # | Review said | At head 545c791 | Disposition |
|---|---|---|---|
| F1 | runtime/dep stack is not coworld-ctf's (own `runtime.nim`, no bitworld/flatty) | Still true: `procgen.nimble:8-12` requires only mummy/whisky/curly/jsony; `src/procgen/runtime.nim` carries its own Coworld-contract copy and says so. Chrome/viewer files ARE the starter's (verified separately). | **Advisory, stands.** No checklist item names the dependency stack. |
| F2 | `broadcast_core.js` is a rewrite, not a fork | Fixed as documentation + test: commit `c8cc41f` re-states provenance in the file header and `tests/test_procgen_viewer.nim:72-100` now pins the named procs where they actually live (page head: `function pushFeed(row)` etc.; chrome_common: `markBeat`/`ingestLullSpans`/…; broadcast_core: factory + method surface + `devicePixelRatio`). | **Advisory, resolved.** Checklist item 14 names only `chrome_common.js` (byte-identical — verified) and `replay_broadcast.html` (starter + appended block — verified); `broadcast_core.js` is not on its provenance list. |
| F3 | page IS starter + deletions + one appended block (recorded because size alarms) | Reproduced independently: banner at `client/replay_broadcast.html:1581`; head is starter lines except ~119 nonempty modified, all documented removals/re-labels/adaptations; every kept id present, every removed id absent; `attachMinimap` gone. | **Consistent; not a finding.** |
| F4 | climber ships 3 walkable tiers, not the note's 4 | Still true: `src/procgen/gen.nim:34-35` `ClimberWalkRows* = [7, 4, 1]`. Recorded in `docs/RULES.md` §Divergences (inlined in `game.docs`). | **Advisory, stands.** Design-note deviation, documented; no checklist item. |
| F5 | `pathfinder.digCost` is 1, not the note's 3 | Still true (`baselines.nim:25,37-43`), with the sweep rationale in-file; `ci.yml` runs `tune_baselines --sweep --check` on every push (ran green in run 33204619462, test job step "Sweep and verify the scripted-baseline tuning"). | **Advisory, stands.** Item 7 requires *tuned with a grid harness, not guessed* — satisfied. |
| F6 | margin band `[+0.02,+0.45]` vs the note's `[+0.05,+0.45]`; "24-episode" naming | Naming fixed (comments only, `6bd0313`); the band is still `marginMin: 0.02` with a recorded `marginBandNote` (measured max +0.038) in `tools/ci/baseline_tuning.json`. | **Advisory, stands.** Deviation from the note's number, honestly recorded; item 7 does not pin the band. |
| F7 | certification fixture plays 8 levels, not the note's 4 | Still true: `coworld_manifest_template.json` `certification.game_config.levelCount: 8`; `tests/test_procgen_engine.nim:75-77` asserts it, with the soak rationale. All four seat-count invariants intact (`num_agents==1`, both player lists length 1, `SMOKE_SEATS 1`). | **Advisory, stands.** No checklist item pins the cert levelCount. |
| F8 | chrome sha256 enforced by ci.yml step, Nim test pins sha1+length | Still true (`ci.yml:104-111`; `test_procgen_viewer.nim`). I re-verified byte-identity myself: sha256 of `client/chrome_common.js` == starter's == `7ace7287…f7c`, 40 022 bytes. | **Advisory, equivalent enforcement.** |
| F9 | no committed `.replay` fixtures; cross-target case missing | **Fixed at head** (`545c791`): `tests/fixtures/{gauntlet-seed42,sprint-seed7,hard-seed13,deadline-seed21}.replay` committed; `tests/test_procgen_replay.nim` +124 lines of recipes; ci.yml's "Run the EXACT emitted wasm module headless" step loaded all four (run 33204619462 log: `ok: loaded gauntlet-seed42.replay, advanced 150 frames` etc.). | **Refuted at head (fixed since).** |
| F10 | generator sweeps 150/400 instead of 500/5000; `SWEEP_WIDE` never set in CI | **Fixed** (`276653c`): ci.yml runs "The WIDE generator sweep" step with `SWEEP_WIDE=1` in release on every push (ran in run 33204619462, test job log lines 536-541). | **Refuted at head (fixed since).** |
| F11 | tile kit drawn browser-side; `procgen_art.nim` is a manifest, not a bake | Still true. Art verified real (22 sprite PNGs 10–26 KB + 3 ~1 MB source sheets + splitter script; procedural fallbacks per sprite). | **Advisory, stands.** No checklist item; "real art" pin satisfied in substance. |
| F12 | `directive` record never carries `view` | **Fixed** (`e0e884a`): both call sites now pass `viewJson` (`server.nim:449-450`, `engine.nim:71`); privacy test extended to check `directive.view` as its own field (`test_procgen_identity_privacy.nim:109-113`). | **Refuted at head (fixed since).** |
| F13 | `gamestart`/`plan` declared but never emitted | **Fixed** (`648f741`): `ekGameStart` emitted at `sim.nim:154`, `ekPlan` at `sim.nim:220` and `replay_runtime.nim:226`; events test extended (+49 lines). | **Refuted at head (fixed since).** |
| F14 | `lvl-label` re-mapping dropped at 556cb50 | **Fixed** (`893a6ec`): `<span class="lvl-label">Level</span>` back in the plate (5 `lvl-label` hits in the page) and in the endcard-labels `Replacements` list. | **Refuted at head (fixed since).** |
| F15 | feed wording differs from the note's worked examples | **Fixed** (`0cd1e43`): `labels.nim:54` `deathPhrase(...) & " — level over at " & $e.abs`; `dangerWord` yields `hunter alongside`/`boulder overhead`/… per archetype (`labels.nim:29`, vocabulary list `:75-77`); `tests/label_manifest.txt` regenerated in the same commit. | **Refuted at head (fixed since).** |
| F16 | test 13 asserts 60 s, not "<1 s release / no frame >1 ms" | **Fixed** (`6d02660`): release-only `check elapsed < 1000` (`test_procgen_sim.nim:427`) and `no single frame exceeds 1 ms` (`:450`) added; the 60 s outer bound kept for debug builds. | **Refuted at head (fixed since).** |
| F17 | test 44 asserts `>= 1`, not "exactly once" | **Fixed** (`07dea1b`): each replacement now carries an exact expected count (`check count == want`), the dual-site caption carrying 2 with the reason. | **Refuted at head (fixed since).** |
| F18 | tests 29(a)/31 are source greps, not live exercises | Partially addressed (`024d035` asserts the clamped tail; `413eced` extends test 31); the HTTP surface is exercised live by docker_smoke against the real container (smoke OK, reason=complete). | **Advisory, stands in reduced form.** Item 7's episode test and item 6's smoke are the checklist's demands; both are live. |
| F19 | shutdown grace is a fixed 20 s that could exceed the pod tail | **Fixed** (`024d035`): `server.nim:516-519` clamps `graceUntil` to `started + PodBudgetSeconds`; worst-case arithmetic now bounded inside the budget. | **Refuted at head (fixed since).** |
| F20 | `config_schema` omits `model`/`maxOutputTokens` that `sim_config` parses | **Fixed** (`fc309e6`): both declared (`config_schema.properties` now 24 keys — verified by loading the JSON); manifest test extended (+39 lines). | **Refuted at head (fixed since).** |
| F21 | pod still serves `/client/replay` (item 3 read literally) | **Fixed** (`413eced`): no `result.get("/client/replay", …)` at head; `server.nim:304` documents its absence; `tests/test_procgen_engine.nim:358-359` asserts `"/client/replay"` not in the source. Repo-wide grep finds no route. | **Refuted at head (fixed since).** Item 3 now satisfied even on the strictest reading — stricter than the starter itself. |
| F22 | main viewer smoke's `canvas_text` total is 0; text bounds covered only by the fixture | Still true and correctly characterised. Run 33204619462 wasm-viewer log: bundle step `canvas text: 0 drawn …` (OffscreenCanvas worker — covers nothing); fixture step `{"loaded":true}` then `canvas text: 72 drawn, 0 never inside the canvas, 0 ellipsized (--strict-text-bounds)`. Item 15 prescribes exactly this compensating fixture; `renderer_fixture.html:321-323` asserts its own say is still full-cap length; widths 360/640/1024. | **Advisory caveat, stands; item 15 satisfied through the fixture.** The number to cite is the fixture's 72/0, not the bundle's 0/0. |
| F23 | live `/global` ships empty plan/bubbles/feed and no split bar | **Fixed** (`093dfed`): `global.nim:56-58` builds the bubble from `episode.seat.say`/`sayFramesLeft` (now read — `server.nim:445-448` sets them), and `:119` emits `"splitbar": liveSplitBar(episode)`. | **Refuted at head (fixed since).** |
| F24 | gen cross-target case and seed-leak test are indirect | Cross-target now covered by the committed fixtures + the exact-emitted-wasm smoke (F9 fix); the seed/split hiding verified directly (`seatViewJson` key-by-key, system prompt byte-identical to the note). | **Advisory, resolved in substance.** |
| F25 | one test assertion narrowed during the run (`a086c76`, art preload list) — judge to rule | **Ruled: not a loosening.** The deleted assertion claimed `broadcast_core.js` preloads `arena_floor.png`/`pallete.png`; the renderer never did and never needed to — the floor wash and palette are procedural and the font loads via `FontFace` (`broadcast_core.js:135-138`; no `arena_floor`/`pallete` reference anywhere in `client/` or `src/` draw paths). The narrowed test still asserts the full sprite kit is preloaded and (`test_procgen_art.nim:18-22`) that every committed art file ships non-empty. Correcting an assertion that asserted something the code never did is not "loosened to pass" in the sense item 1 polices; no tolerance widened, no skip/xfail added, no file removed. Residue: `arena_floor.png`/`pallete.png` are committed but unused by the renderer — a note-conformance nit, listed under observations. | **Not blocking (item 1 audit below).** |

No finding in the review survives as blocking; none was wrong in a way that hid a checklist violation.

---

## Checklist pass (independent)

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | CI green; no test loosened | **PASS** | Run **33204619462**, workflow CI, branch main, `headSha 545c791…`, conclusion `success` (test / docker-smoke / wasm-viewer all green; `gh run view --json headSha,conclusion`). Test-history audit from `git log -p -- tests/` over the whole run (16 commits, all this run): the only threshold reduction (`180→90` frames, `a086c76`) was **reversed** at `2c88e66` (head asserts `totalFrames >= 180`, `test_procgen_engine.nim:100`, plus a NEW `deaths >= 1`); the art-list narrowing ruled a correction (F25 above); `levelCount == 4 → == 8` is an equality either way tracking the manifest; every other tests/ change adds assertions (07dea1b strengthens `>=1` to exact counts). No `skip`/`xfail`/`--skip` anywhere in `tests/` (grep clean); no test file deleted. |
| 2 | Replay re-derivation, frame by frame; viewer derives from it | **PASS** | `replay_runtime.nim:154-234` re-generates levels from recorded kind/seed/difficulty and re-runs `stepFrame` over the action bytes, comparing `foldState()` to the recorded hash at **every** frame including the 255 boundary byte; the viewer draws from `rt.snapshots` = that re-simulation (`broadcast.nim`). Tests: `test_procgen_determinism.nim:26` ("matches at EVERY frame"), `test_procgen_replay.nim:120-121` (all three end rules incl. the stop frame); wasm: `wasm_replay_smoke.cjs` fails on `mismatch_tick != -1`, ran against the fresh smoke replay + 4 committed fixtures. |
| 3 | Static viewer; no `/client/replay` pod path | **PASS** | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, asserted + invoked by path in ci.yml wasm-viewer; worker fetches only the `?replay=` URL (`credentials:'omit'`) + same-origin assets. **No `/client/replay` route exists at head** (`413eced`; `server.nim:301-304` registers only `/healthz`, `/client/player`, `/client/global`; repo-wide grep = comments and the not-in test only). |
| 4 | Both name spaces | **PASS** | Alias `COG-alpha` (`roster.nim`) is the only name in obs/prompt/directive (`test_procgen_identity_privacy.nim:36-49,98-113`); real name in `results.names`, replay join/config, and the scorebug plate — the CI smoke drew `"Cog1 COG-alpha"` on the plate (wasm-viewer log). `showPlayerLabels: false` everywhere. |
| 5 | Degrade-never-hang; settles inside 720 s | **PASS** | Every wait bounded: lobby `lobbyJoinTimeoutSeconds` (`server.nim:323-330`); attempt1 5 s / retry 2 s / turn 7.5 s monotonic (`decide.nim:143-169`); exactly one retry (`attempt < 2`); throttle fail-fast (`:197-202`); spacing floor 2.5 s; wall clock 660 s checked in both loops (`server.nim:401-419`); budget guard from ≈644 s (`decide.nim:92-100`); generator redraw ≤40 then committed fallback; shutdown grace clamped to the pod budget (`server.nim:516-519`, `024d035`). Worst case ≈652 s ≪ 720 s; `test_procgen_manifest` asserts the arithmetic per variant. |
| 6 | `num_agents` everywhere; SEAT-COUNT | **PASS** | `num_agents: 1` inside `game_config` of all 3 variants **and** `certification.game_config` (loaded the JSON myself); `docker_smoke.sh:106-152` implements the four `SEAT-COUNT FAIL:` invariants + the `SMOKE_SEATS` cross-check; **grep of the full docker-smoke job log (98962387093): zero `SEAT-COUNT` hits**; log shows `game=procgen seats=1 config={… "num_agents": 1 …}` and `smoke OK: seats=1 … reason=complete`. |
| 7 | Scripted baseline full legal episodes, tuned not guessed | **PASS** | `test_procgen_engine.nim:38-39` asserts `reason == "complete"` on a real scripted episode (and `:110-133` for all three variants); `test_procgen_control.nim:45-61` asserts `moves.len ∈ [1,6]`, alphabet-only, over 500+ states × both baselines; tuning swept by `tools/tune_baselines.nim --sweep --check` in CI every push, pick recorded in `tools/ci/baseline_tuning.json`, shipped constants asserted equal to it. |
| 8 | LLM reply handling | **PASS** | Tolerant `extractJsonObject` (starter's, prose/fences survive); one retry with its own deadline + re-prompt (`decide.nim:143-196`); fallback installs the pathfinder plan, increments `fallbackTurns`, writes a `fallback` chat record with a closed `cause` set, logs the exact `falling back` phrase (`:204-220`); repairs increment `ordersRejected`; fallback proc == pathfinder proc asserted (`test_procgen_control.nim`). |
| 9 | Rune-safe truncation | **PASS** | `truncateRunes`/`sanitizeSay`/`sanitizeNote` starter-verbatim; `moves`/`say`/`notes`/reply-bytes/prompt/error-detail all rune- or boundary-safe; test 24 feeds 4-byte emoji at each cap (`test_procgen_control.nim:190-211`); end-to-end `replay_summary.py` output asserted strict UTF-8 (`test_procgen_replay.nim:197`, `validateUtf8() == -1`). |
| 10 | Manifest validates | **PASS** | `game.docs` = readme(text) + 4 pages each `{id,title,content:{type:"text",value}}` (values 2.3–9.4 KB); `game.protocols` has both `player` and `global` as `{"type","value"}` objects; validated under the installed `coworld==0.1.43` `_load_template_manifest` in CI (green). |
| 11 | Legible at 360 px | **PASS** | `.plate-name { … flex: 1 1 auto; min-width: 3.2em; }` (`replay_broadcast.html:1607-1620`); labels hidden `@media (max-width: 640px)` (`:1748`) and under `#stage.tiny`. |
| 12 | Release order & scaffold | **PASS** | `coworld-release.yml`: Build manifest (:159) → Certify (:173, `--timeout-seconds 300`) → **Upload the policies** (:216) → Upload the Coworld (:314) → Put the Coworld secret (:410); all three workflows present; `docker_smoke.sh` + `build_replay_viewer.sh` mode 100755 (git index); `policies.json`: 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep exits 1 (no hits); smokes build their binaries/bundles in the same run. |
| 13 | Viewer executes | **PASS** | Run 33204619462 `wasm-viewer` (job 98962715990) green **including "Load the bundle in a real browser"**: `{"loaded":true,"ms":556,…}`, `soak: 10s of playback kept advancing ("1 / 193" -> "49 / 193" -> "61 / 193")`; `needs: docker-smoke` (ci.yml:291); zero `continue-on-error` in any workflow. `data-replay-loaded` set in the `'loaded'` branch after the worker's first ingested+drawn frame (`static_replay.js:142`); `data-replay-error` in `showFailure` (`:20`). Lobby-dwell class structurally absent: replay frames are appended only inside the frame loop after the lobby returns — there are no recorded lobby frames; `st: 0` and snapshot 0 is level 1 frame 0; seeks clamp to ≥0. `config.nims` has **no** MODULARIZE/EXPORT_NAME and the worker uses `Module.onRuntimeInitialized` (:186) — the non-modularized pair from the SAME starter (both files diff rename-only against coworld-ctf). |
| 14 | Chrome is the starter's | **PASS** | `client/chrome_common.js` **byte-identical** (sha256 diff clean, 40 022 B). Page: starter head + banner (`:1581`) + appended block; head is starter lines minus the listed removals (every kept id present, every removed id — `#viewpanel`, `#fpv*`, `#povBadge`, `#plates-r`, zoom — absent; `#viewpanel` removed entirely, correct for this fixed 15×9 arena). Transport: `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:1520-1547`); nothing `position: fixed` anywhere in the page; `#endcard { bottom: var(--band, 0px) }` (`:576`) shown via `#endcard.on` (`:587`) and taken down on every frame with `!s.over` — so every seek dismisses it (fixture asserts the round trip); beats are labelled `<button>`s built by `procgenBeat` (`:1811-1830`, title + aria-label + click→seek) with CSS for exactly the seven emitted kinds (`:1725-1731`), never `markBeat`. |
| 15 | Every drawn string fits | **PASS** | `--strict-text-bounds` on both ci.yml smoke steps. Bundle step reports `total: 0` (worker/OffscreenCanvas — covers nothing, per the item's own text), so the evidence is the **worst-case renderer fixture step**: `tools/ci/renderer_fixture.html` loads the shipped page, drives a full-cap 24-rune say on a **top-row** cog at 360/640/1024 px, **asserts its own say is still full-cap length** (`:321-323`), and the step reported `canvas text: 72 drawn, 0 never inside the canvas, 0 ellipsized (--strict-text-bounds)` (job 98962715990). Bubble band reserved from the server cap measured in the drawing font (`broadcast_core.js`), clamped inside the canvas. |
| — | One parallel batch per turn | **PASS** | Single seat; one call per turn through `curly.makeRequests` on a one-element `RequestBatch` (`decide.nim:160-169`), the starter's batch path. No sequential-seat loop exists. |

Nothing in the pass was unverifiable from the tree or the cited CI evidence.

---

## Non-blocking observations (advisory; none maps to a checklist item)

- **[other]** `client/replay_broadcast.html` head carries stale comments from a different game lineage ("this arena is three small fixed rectangles" `:1283`/`:1482`, "its length as a big numeral, a health bar when the module has health" `:986-989`, "the four cogs coiling up" `:783`, "a four-way free-for-all has no sides" `:1096`) — comments only; every visible string is asserted by the endcard-labels test and no forbidden vocabulary escapes a comment. Worth tidying, not blocking.
- **[other]** `data/arena_floor.png` and `data/pallete.png` are committed but the renderer draws the floor/palette procedurally (F11/F25 residue) — the note's "arena_floor.png tiled and darkened 30 %" is not what ships.
- **[correctness]** Design-note deviations that remain, all documented in-tree: climber 3 tiers (F4, `docs/RULES.md` §Divergences), `digCost 1` (F5, swept), margin band floor `+0.02` vs the note's `+0.05` (F6, `marginBandNote` records the measured +0.038), cert fixture `levelCount 8` (F7, soak rationale).
- **[legibility]** The number to cite for item 15 is the fixture step's `72 / 0 never_inside / 0 ellipsized`, never the bundle step's `0 drawn` (F22). A real-key hosted episode through the bundle remains phase 60's confirmation.

## Fixer report audit

`r1-fixes.md` was not read (the brief forbids it). In its place the fixer's **commits** were audited
directly: every `r1-F*` commit named above (`c8cc41f`, `6bd0313`, `276653c`, `e0e884a`, `648f741`,
`893a6ec`, `0cd1e43`, `6d02660`, `07dea1b`, `024d035`, `fc309e6`, `413eced`, `093dfed`, `545c791`) was
diffed and its claim verified against the head tree and the head CI run; all fourteen do what their
messages say, and none weakens a test (item 1 audit above).

---

Blocking items: none.

BLOCKING: 0
