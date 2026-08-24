blocking: 1

# r1 verdict — matrix-games
Head: af5c7043d4a4fbca3eb5f4c230901f6d9fb4dfe7   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Fresh clone at `/tmp/judge-matrix-games`, checked out at `af5c704`. I read the repo, the design
note, the CI run and the starter diffs and wrote my own notes **before** opening
`r1-review.md` or `r1-fixes.md`. The review was written against `7b7d586`; fifteen fix commits
have landed since, so every finding below is adjudicated **at `af5c704`**, not at the review sha.

CI evidence used throughout: run **32755082249** (`gh run list -R Metta-AI/cogame-matrix-games
--branch main -w ci.yml`), event push, headSha `af5c704…`, conclusion **success**; jobs `test`,
`docker-smoke`, `wasm-viewer` all `success`, and I confirmed step-by-step via
`gh run view 32755082249 --json jobs` that `Load the bundle in a real browser` ran and passed
(no `continue-on-error` anywhere in `ci.yml`; `wasm-viewer` has `needs: docker-smoke`).

---

## Standing blocking findings

### B1 — no automated gate asserts `results.reason == "complete"` on an all-scripted episode   (source: judge)
- Where: `tools/ci/docker_smoke.sh:369-371` and `tests/support/helpers.nim:35,74`
- Checklist item: **7** — "A test runs an all-scripted episode to the natural end, asserts
  `results.reason == "complete"`, and asserts every order/action is inside its legal bounds."
- Verified at head: the legality half is thoroughly asserted (`tests/test_baseline.nim:38-51`,
  `checkOrder` at `:17-35`, all five baselines × seven variants × seeds 1..8). But no test
  asserts the reason. The unit harness **stamps** the reason itself —
  `tests/support/helpers.nim:35`: `state.finish("complete", "full_match")` — so any assertion
  there would be tautological; the real end-condition path (deadline vs complete, decided in
  `src/matrix_games/server.nim:231-266`) is exercised only by docker-smoke, which **prints**
  the reason without asserting it:
  ```
  reason = results.get("reason") or results.get("end_reason")
  if reason is not None:
      print(f"episode end reason: {reason}")
  ```
  (`tools/ci/docker_smoke.sh:369-371`). `tests/test_replay.nim:72` checks only membership in
  `{complete, deadline, forfeit}`. A regression that made certification episodes settle as
  `deadline` (schema-legal, exit 0) would go green today. The behaviour itself is currently
  correct — run 32755082249's docker-smoke log reads `episode end reason: complete` and
  `smoke OK: seats=8 … reason=complete` — but the checklist sentence requires the assertion,
  and it does not exist at head. What would settle it: one line in `docker_smoke.sh`'s results
  check (`if reason != "complete": raise SystemExit(...)` for the smoke fixture), or a unit
  test that drives the server-side end conditions.

- [correctness] tools/ci/docker_smoke.sh:369-371 no test or smoke asserts results.reason == "complete" on the all-scripted episode; the reason is printed, never checked, and the unit harness stamps "complete" itself

---

## Refuted / moot at head

Every reviewer gap that was fixed is **refuted at the current head** (true when written, false
now). I verified each fix in the tree, not from the fixer's table:

### F8 — tick-0 `leadchange` → REFUTED (fixed)
- Evidence: `src/matrix_games/sim_state.nim:126` at af5c704 — `result.lastLeader = 0` (seeded
  with the opening leader, with the explanatory comment). No marker at t=0.

### F23 — 401/403 disable untested → REFUTED (fixed)
- Evidence: `tests/test_llm.nim:223-245` hands `Response(code: 401/403)` straight to
  `client.textOf`, asserts the raise, `client.disabled`, zero further batches, `osFallback`
  for all seats. CI log: `[OK] a 401 or a 403 disables the client for the rest of the episode`.

### F29 — deadline stamped before the connect wait → REFUTED (fixed, correctly disputed in part)
- Evidence: `src/matrix_games/sim_config.nim:97-103` — `validate()` now requires
  `playerConnectTimeoutSeconds + RegistrationGraceSeconds + beats × 2 × llmTimeoutSeconds`
  (663 s at defaults) to fit inside `playDeadlineSeconds()` (720 s). Stamping before the
  connect wait is the *stronger* reading of item 5 (the whole episode inside 60 %); the fixer's
  reasoning is sound and the arithmetic is now enforced at startup.

### F32 — unguarded game thread → REFUTED (fixed)
- Evidence: `src/matrix_games/server.nim:230-266` — the beat loop is wrapped in
  `try/except CatchableError`; a raise settles as `deadline`, writes both artifacts and quits.

### F34 — byte-cut error preamble → REFUTED (fixed)
- Evidence: `src/matrix_games/llm.nim:336-341` — `cleanText(text, 160)` (rune-boundary);
  `tests/test_llm.nim:34-43` feeds 300 × `\u4e2d` and asserts valid UTF-8.

### F40 — indices recorded twice, never cross-checked → REFUTED (fixed)
- Evidence: `tests/test_viewer.nim:188-213` compares the viewer's event-folded
  `conventionCounts`, `interactions` and `coopRate` (incl. the null case) cell-for-cell against
  `replay.indices`. CI log: `[OK] the viewer's re-derived indices agree with the recorded ones`.

### F47 — no frame-by-frame re-derivation test → REFUTED (fixed)
- Evidence: `tests/test_viewer.nim:122-167` + `tests/support/helpers.nim:38-76`
  (`runScriptedRecording` captures the sim's own state after **every tick**); the test asserts,
  for all ticks × 8 seats, that the wasm packet's board block (`c` quad, `inv`, `sc`, `tok`)
  and the chrome `seats[]` equal the live sim state at that tick. This is the same code path
  the wasm bundle runs (`replay-viewer/matrix_games_replay.nim:54` calls
  `global.nim:viewerPacket`). CI log: `[OK] every tick of the packet is the sim's own state at
  that tick`.

### F50 — foreign `.ev-lane` CSS in the inherited region → REFUTED (fixed)
- Evidence: `grep -n 'ev-lane\|\.ev\.' client/replay_broadcast.html` at head returns nothing;
  my own diff of the CSS above the banner (lines 7-1324) against the starter's shows only the
  note-listed `#viewpanel` removal plus the `#killfeed` band fix (below).

### F51 — unstyled feed rows / banner chips → REFUTED (fixed)
- Evidence: `client/replay_broadcast.html:1871` `row.className = 'feed-row'`, `:1893`
  `chip.className = 'banner-chip'` — the inherited selectors (`:489`, `:448`). Test added.

### F54 — `.tiny` at 620 vs item 11's 640 → REFUTED (fixed where it touched the checklist)
- Evidence: `client/replay_broadcast.html:2168` — `stage.classList.toggle('tiny', width < 640)`.
  The unfixed half (mgRelayout is a single pass, not the starter's four-pass loop) does not
  falsify item 11 or 14(a): `--hudscale`/`--band`/`--topband` are set on
  `document.documentElement` (`:2165-2172`), which is what 14(a) tests. See non-blocking
  observations for the provenance residue.

### F59 — `/client/replay` pod route → REFUTED (fixed)
- Evidence: `src/matrix_games/server.nim:437-447` at head registers `/healthz`,
  `/client/player`, `/client/global`, `/client/@name`, `/replay-data`, `/global`, `/player`
  only. `grep -rn "/client/replay"` over the tree finds only comments, the release workflow's
  error message, and `tests/test_manifest.nim:65` asserting its absence. Item 3 now holds.

### F64 — soak never ran → REFUTED (fixed)
- Evidence: `.github/workflows/ci.yml` `Load the bundle in a real browser` passes `--soak 10`;
  run 32755082249 log: `soak: 10s of playback kept advancing ("5 / 300" -> "197 / 300" ->
  "245 / 300")` with `{"loaded":true,…}` and three distinct scrub readouts.

### F65 — chicken half of gate (b) dropped → REFUTED (fixed)
- Evidence: `tests/test_indices.nim:113-130` asserts hawk strictly out-earns dove in every
  mixed-cell resolution across seeds 1..8; the header (`:9-31`) documents the restatement and
  the measured 0/8 result for the note's literal form. This is an **added** assertion, not a
  loosened one — the note's literal claim was measured false for positional reasons, and the
  substituted form tests the same property of the matrix more directly.

### F66 — no results-schema validation in the smoke → REFUTED (fixed)
- Evidence: `tools/ci/docker_smoke.sh:302-367` — a recursive validator (type unions incl.
  `["number","null"]`, enum, required, additionalProperties, min/max, minItems/maxItems)
  against `game.results_schema`, failures prefixed `RESULTS-SCHEMA FAIL:`. Run log:
  `results.json validates against game.results_schema (17 keys)`; 0 occurrences of either FAIL
  prefix in the whole run log (I grepped it myself).

### F67 — determinism in one process only → REFUTED (fixed)
- Evidence: `tests/test_sim.nim:253-280` — `hashInFreshProcess` spawns the test binary with
  `MATRIX_GAMES_HASH_SEED`, asserts same seed → same hash across processes, different seed →
  different. CI log: `[OK] a fresh process reproduces the same hash from the same seed`.

### Reviewer findings dismissed as non-blocking (verified, no checklist item falsified)

- **F9** (`updateSight()` unnumbered): writes only observer memory (`sim_state.nim:200-206`);
  no rule-visible state. Note deviation, no checklist item.
- **F10/F11** (kernel sidestep / hunt sweep): deterministic, documented at the call sites,
  and load-bearing for gate (a) (`tests/test_indices.nim:60-66`, every seat resolves).
  Baseline legality (item 7's bounds clause) is unaffected — `checkOrder` still passes on every
  order. Note deviations, not checklist findings.
- **F12/F14/F18/F22** (kernel reads spawner list; exploitability majority side; blocked cog
  turns; 429 same-beat retry): all deterministic readings of note ambiguities; item 8's literal
  requirement ("retries once … then falls back") is what the code does (`llm.nim:525-563`).
- **F17** (`you.fixedType` in the observation): forced by the note's own pair of requirements
  (fixed-pick runs off `buildObservation` alone); leaks one bit/trit about the seat's own draw,
  not the seed, not another seat. No checklist item.
- **F55** (`static_replay.js` beyond verbatim-plus-one-line): every divergence is load-bearing
  for items 5/13 (fetch watchdog, `tell()` bridge, `data-replay-error`, transport API) and the
  file is single-starter lineage; item 13's operative evidence is the smoke's `loaded: true`,
  which exists. Note deviation only.
- **F56** (`broadcast_core.js` rewritten; zoom stubs remain): the starter's core decodes a
  binary sprite protocol this game does not emit; a byte-kept copy could not draw the recorded
  JSON state. Item 14's viewpanel bullet is satisfied where it bites: markup, CSS and ids are
  gone (`tests/test_viewer.nim:275-280` asserts it), nothing in the page calls
  `zoomAt/setZoom/attachMinimap`. Three unreferenced stub methods on the core object do not
  reconstruct a zoom panel. Ruled non-blocking; recorded below as provenance residue.
- **F61** (cert fixture names seats with aliases): pinned by the note (design.md:967-969);
  the two-name-space mechanism is present and correct (`server.nim:464-466`, `:404`;
  `replays.nim:43-58`; `broadcast.nim:150-151`), and on the platform the game config supplies
  real policy names. Item 4 holds.
- **F70** (art provenance differs from the note) and **F71** (replay written before results,
  documented, matches paintbot/raid practice): no checklist item names either.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | run 32755082249, push, head af5c704, conclusion `success`, all 3 jobs. `git log -p --since=2026-08-24T14:37Z -- tests/`: every hunk read — all additive (new tests F23/F40/F47/F65/F67); the only deletions are an import line and a two-word comment edit; no skip/xfail/tolerance/removed file. |
| 2 replay re-derivation, viewer from it, test asserts | **pass** | This game records state, not inputs (design.md §replay; no input-replay machinery exists, so "replaying events through the sim" has no referent). The equivalent property is asserted: `tests/test_viewer.nim:122-167` (viewer packet == live sim state, every tick, every seat, board+chrome+tok), `:188-213` (re-derived indices == recorded), on the same `global.nim:viewerPacket` path the wasm entry calls (`matrix_games_replay.nim:54`). Determinism incl. fresh process: `test_sim.nim:264-280`. |
| 3 static viewer, no pod path | **pass** | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, `-rwxr-xr-x`; worker contacts only `fetch(replayUrl)` + same-origin bundle art (`static_replay_worker.js:87-90,132`); `/client/replay` route deleted at head (`server.nim:437-447`), grep clean. |
| 4 both name spaces | **pass** | `buildObservation` emits aliases only (`sim.nim:215-345`, header comment + read in full); replay carries `names[]` (aliases) + `policyNames[]` (`replays.nim:43-58`); scorebug/endcard read policy names (`broadcast.nim:150-151`, page `mgBuildPlates`); `results.names` = policy names (`sim.nim:367-368`). |
| 5 degrade-never-hang, 60 % budget | **pass** | Connect wait ≤180 s (`server.nim:168-176`), registration grace ≤3 s (`:178-188`), batch `makeRequests(batch, timeoutSeconds=20)` (`llm.nim:490`), pace sleep ≤17 s (`:466-476`), deadline checked between beats (`server.nim:232-238`), beat loop guarded (`:262-264`), forfeit path writes artifacts (`:213-222`), `validate()` enforces 180+3+480=663 ≤ 720 (`sim_config.nim:97-103`). No unbounded loop or blocking read found. |
| 6 num_agents everywhere + smoke invariants | **pass** | All 7 variants + cert fixture `num_agents: 8`, 8 players each (parsed the manifest myself); `docker_smoke.sh:106-151` enforces all four invariants + independent `SMOKE_SEATS` cross-check, each `SEAT-COUNT FAIL:` prefixed; **0** occurrences of `SEAT-COUNT FAIL` in run 32755082249's full log (grepped). |
| 7 scripted baseline full episodes legally | **BLOCKING (B1)** | Legality: `test_baseline.nim` (5 baselines × 7 variants × 8 seeds, every order bounds-checked). Full natural episodes: yes, and the real containerized episode ends `reason=complete` (run log). But **no test asserts `results.reason == "complete"`** — the harness stamps it (`helpers.nim:35`), the smoke prints it without checking (`docker_smoke.sh:369-371`). Tuning: the parameters are pinned by the gate sweep (`test_indices.nim`: ≥12 resolutions, every seat resolves, every cell hit, over 7 variants × 8 seeds), which is grid-harness evidence in the tree. |
| 8 LLM reply handling | **pass** | `extractJsonObject` tolerant (`llm.nim:330-341`); exactly one retry with hint (`:525-536`); fallback to `counter` recorded as `source:"fallback"` on the order event (`:560-563`, `events.nim:38-46`); asserted `test_llm.nim` (batch, retry, fallback, 401/403, junk, timeout). |
| 9 rune-safe truncation | **pass** | `cleanText` runeSubStr (`sim_types.nim:228-238`) applied at `sim.nim:198-199`, `events.nim:43-44`, `llm.nim:408-409,448,451,454,464` (F34 fixed), prompt cut `runeSubStr` (`server.nim:402`); multi-byte-at-cap test `test_replay.nim:97-136`; strict `validateUtf8 == -1` on the whole replay. |
| 10 manifest validates | **pass** | `game.docs` = readme `{type:text,value}` + 3 pages `{id,title,content:{type:text,value}}`; `game.protocols.player` and `.global` both `{type:text,value}` (parsed myself). |
| 11 legible at 360 px | **pass** | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` (`replay_broadcast.html:1353`); labels hidden under 640 px (`:2168` `width < 640` toggling `.tiny`; `:1455-1457` `.tiny` hides `.plate-name`/`.plate-enc`/`.plate-camp`). |
| 12 release order and scaffold | **pass** | `coworld-release.yml` steps in order: build (`:153`) → certify (`:167`) → upload-policies (`:206`, comment pins BEFORE upload-coworld) → upload-coworld (`:309`) → secret put (`:342`); all three workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions (+`USE_BEDROCK`) + 2 scripted fillers, champion #2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep returns nothing (exit 1 from grep = gate exits 0). |
| 13 viewer executes | **pass** | Run 32755082249 `wasm-viewer` green **including** `Load the bundle in a real browser`: `{"loaded":true,"ms":559,…}`, soak `"5 / 300" -> "197 / 300" -> "245 / 300"`, three distinct scrub readouts; job `needs: docker-smoke`; no `continue-on-error`. Markers: `static_replay.js:145` (`data-replay-loaded` on first drawn frame, `ready` posted after), `:40` (`data-replay-error`). Matched pair: `config.nims` has no `MODULARIZE`/`EXPORT_NAME`; worker uses `var Module = {}` + `Module.onRuntimeInitialized` (`static_replay_worker.js:19,201`) — same lineage, and `test_viewer.nim:293-327` asserts the pairing and the export list. |
| 14 chrome is the starter's | **pass** (see observations) | `chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diff: empty) and actually instantiated and driving (`replay_broadcast.html:2093`, `renderTransport`/`ingestLeadSeries`/`ingestLullSpans`/`getSpoilers`). CSS above the banner diffed against the starter: only the note-listed `#viewpanel` block removed plus `#killfeed` moved onto the band (`:476`, the direction 14(b) demands). Markup = starter's minus the note's removal list plus `#mg-*` inside `#chrome`. Transport rules verified in the page: (a) `--hudscale`/`--band`/`--topband` set on `document.documentElement` (`:2165-2172`); (b) `#killfeed`/`#mg-*` ride `--band`/`--topband` (`:476`, `test_viewer.nim:243-251`); (c) `#endcard { top: var(--topband); bottom: var(--band) }` byte-identical to the starter's rule, shown via `#endcard.on`, and **every** seek path funnels through the wrapped `mgCore.seek` which removes `.on` (`:2139-2146`; scrub click `:2015-2019`, buttons, keyboard, beat buttons all call it); (d) beats are `<button class="beat-marker <kind>">` with `aria-label`/`title` seeking on click (`:1429-1442` one CSS rule per each of the four kinds, closed by `test_viewer.nim:219-226`). `#viewpanel` removed, not hidden (markup, CSS, ids out of the test list). |
| appendix: one parallel batch | **pass** | `runBatch` builds one `RequestBatch` and one `makeRequests` call (`llm.nim:483-490`); `test_llm.nim:96-125` asserts one batch carrying every open seat, scripted seats excluded, batches paced. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F8 | fixed `1e1593a` | `sim_state.nim:126` lastLeader = 0 | yes |
| F23 | test added `8cf9ffb` | `test_llm.nim:223-245` + CI `[OK]` line | yes |
| F29 | fixed `220aa5c` (stamp kept, arithmetic enforced) | `sim_config.nim:97-103`; reasoning sound | yes |
| F32 | fixed `f082554` | `server.nim:230-266` try/except → deadline settle | yes |
| F34 | fixed `b178474` | `llm.nim:336-341` cleanText; test at `test_llm.nim:34-43` | yes |
| F40 | test added `74e0572` | `test_viewer.nim:188-213` | yes |
| F47 | test added `8a1b119` | `test_viewer.nim:122-167`, `helpers.nim:38-76` | yes |
| F50 | fixed `786db23` | `.ev` block gone; CSS diff vs starter clean | yes |
| F51 | fixed `3c0aa54` | `:1871` feed-row, `:1893` banner-chip | yes |
| F54 | partly fixed `6e0178a` | `:2168` `width < 640`; honest comment | yes |
| F59 | fixed `839653d` | route gone from `buildRouter`; grep clean | yes |
| F64 | fixed `cb2430a` | `--soak 10` in ci.yml; soak line in run log | yes |
| F65 | fixed `e47b6c8` | `test_indices.nim:113-130` + documented header | yes |
| F66 | fixed `af5c704` | validator in `docker_smoke.sh:302-367`; run log line | yes |
| F67 | fixed `72b0cf6` | `test_sim.nim:253-280` fresh-process hash | yes |
| F10/F11/F12/F14/F17/F18/F22/F55/F56/F61/F70/F71 | reasoned no-change | each re-checked at head; none falsifies a checklist item | yes |

The fixer's dispute of F29's premise (stamp placement) is correct; its resolution of the
F56 conflict (checklist wiring-removal vs note keep-the-stubs) matches my own ruling above.
No fixer claim failed verification.

## Non-blocking observations

1. **The page's driver script is a reimplementation, not the starter's script.**
   `client/replay_broadcast.html` is 2186 lines against the starter's 4165: the starter's CSS
   (lines 7-1324, diffed: intact minus `#viewpanel`) and markup are genuinely inherited, but the
   starter's ~2560-line page script (which contains its `relayout()`, transport wiring, endcard,
   killfeed and locker-room code) is replaced wholesale by a 628-line `mg*` block. The design
   note claims the opposite ("Nothing above them is rewritten: … relayout()
   (replay_broadcast.html:4110), the transport, the endcard, the locker-room loader … are the
   starter's", design.md §Chrome provenance). I ruled item 14 **not** falsified because (i) the
   shared chrome that item 14 names byte-level — `chrome_common.js` — is byte-identical *and
   driving*, (ii) every one of item 14's operative transport checks passes in the page, (iii)
   the starter's script is CTF-coupled (binary sprite core, flags, POV, zoom) and could not
   drive this game's recorded-state JSON stream, and (iv) this is not the gridlock shape (a
   from-scratch page reusing ids) — 1460 starter lines survive verbatim. But it is a real
   design-note misstatement, and a stricter judge could read the "fraction of the starter's
   size" clause against it. The note should be corrected to record the rewrite (the fixer's
   F54 commit fixed the in-code comment only).
2. **`client/broadcast_core.js` is a 358-line new renderer**, not the starter's 1407-line core,
   with unreferenced `zoomAt/setZoom/attachMinimap` stubs kept per the note. Same reasoning as
   above; the viewer-smoke soak is the empirical evidence it draws.
3. **`static_replay.js` diverges beyond the note's "one added line"** (fetch watchdog, `tell()`
   bridge, retry button, transport API). All load-bearing for items 5/13; single-starter lineage.
4. **Offline cert fixture shows aliases as policy names** (F61) — pinned by the note; the
   platform path supplies real names.
5. `global.nim:163-165` builds the terminal `over` beat row from the last `leadchange` seat with
   `cp: 0` while `broadcast.nim:62-65` uses `sim.leader()` with the real score — two legal but
   different `over` rows, uncovered by F40's cross-check (the fixer's own NOTED item).
6. Kernel deviations from the note's literal intent table (F10 sidestep, F11 sweep), the
   unnumbered `updateSight()` step (F9), `fixedType` in the observation (F17), art provenance
   (F70) and the artifact write order (F71) are documented deviations from the design note with
   no checklist item behind them; they belong in the note's next revision, not in this round.

BLOCKING: 1
