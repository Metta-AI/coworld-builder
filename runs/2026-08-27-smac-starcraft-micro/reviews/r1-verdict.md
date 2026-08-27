blocking: 0

# r1 verdict — smac-starcraft-micro

Head: `84b271b85f8f809699a90adbc89a538e59013f0f` (main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule)
Independent read written before reading fixes: **yes** (notes filed at `/tmp/judge/independent-notes.md` before `r1-review.md` or `r1-fixes.md` was opened; the review itself was also read only after the independent pass).
Review adjudicated: `r1-review.md` (written at `190ef840`; the tree has since moved 19 commits to `84b271b8`).
CI at head: run **33055917137**, push, conclusion `success`; jobs `test` (98462543715), `docker-smoke` (98462543577), `wasm-viewer` (98464283504) all green. Full logs of docker-smoke, test and wasm-viewer fetched and read.

## Standing blocking findings

None. (No `- [<category>] <file:line>` lines to list.)

## Adjudication of B1–B8 (verified at the current head, not at the review sha)

Every one of B1–B8 was a real finding at `190ef840` — I could reproduce each from the review's own
`git show` evidence — and every one is **resolved at the current head**. A finding that was true and
has since been fixed is refuted-as-standing, so all eight count zero.

### B1 — hashed `battleIndex` written only by the live loop → RESOLVED
- Evidence at head: `src/smac/scenario.nim:324-342` — `proc advanceBattle*` (`inc sim.battleIndex; sim.gameIndex = sim.battleIndex`), ONE proc, both call sites: live loop `src/smac/server.nim:2108` (`sim.advanceBattle()`, after the ending tick's hash write) and playback `src/smac/replays.nim:562-564` (`stepReplay` calls `sim.advanceBattle()` after `checkReplayHash`).
- Executing evidence: wasm-viewer log 09:01:34Z — `ok: loaded replay.json, played every tick to 1121 in 1119 frames, hash chain clean` (the same step printed `Replay hash mismatch at tick 319` in the review's run 33046300533). Natively: `[OK] replaying the recording reproduces EVERY recorded hash, all 3 battles` (test log 08:56:19Z, debug and release).

### B2 — no test asserts replay re-derivation → RESOLVED
- Evidence at head: `tests/test_replay.nim:124-155` — records a real 3-battle scripted episode, re-opens it through the shipped `initReplayRuntime`, steps to `replayMaxTick()`, asserts `hashMismatchTick == -1`, `not hashValidationFailed`, `hashIndex == data.hashes.len`, `tickCount == maxTick`, `battleIndex == 3`, `battlesWon == recorded.battlesWon`. Green in run 33055917137.

### B3 — the wasm gate could not fail on the divergence it printed → RESOLVED
- Evidence at head: `src/smac/replays.nim:43` (`scanMismatchTick`, published by the walk at `:704-710`), `:269-284` (`replayMismatchTick` = earliest verdict of both halves); `replay-viewer/smac_replay.nim:134` reads `replayMismatchTick`; `tools/wasm_replay_smoke.cjs:106-140` drives playback to `smac_replay_max_tick()` and fails if playback stalls short (the ci.yml trailing arg is now a 4000-frame safety cap, `ci.yml:384`). The gate's ability to fail is itself tested: `tests/test_replay.nim:157-190` corrupts a hash the display player never reaches and asserts `scanMismatchTick == replayMismatchTick == victimTick`.

### B4 — a test assertion loosened during this run (commit `6e21fe0`) → RESOLVED (restored and stricter than the original)
- The loosening was real: `git show 6e21fe0 -- tests/test_control.nim` replaced `check focus >= charge` on three compositions with tautological `[0,1000]` range checks.
- Evidence at head: `tests/test_control.nim:246` — `check focus > charge` **unconditionally on all four shipped compositions** (the original pre-loosening state was strict only on `default` and `>=` elsewhere, so the head assertion is stricter than anything that existed before the loosening). Restored at `231d17a`; the subsequent `(fix forward)` commits (`ebdb24c`, `07be875`, `b8f0232`, `ed860e5`) changed only `src/smac/baselines.nim`/`control.nim` and comments — I read each hunk; no test assertion was touched again. The fix path changed the code under test (weakening `charge`, fixing two real `focusfire` defects), which is legitimate here: the assertion pins a designed property of the baselines, `charge` is specified by the design note as "deliberately weaker", and `docs/RULES.md` plus the manifest's inlined copy were regenerated in the same commits (verified: the manifest `rules` page is byte-equal to `docs/RULES.md` at head and carries the new `deepest` rule). Measured spreads are echoed in the green log (test log 08:52:39–54Z: 934/932, 952/908, 944/942, 278/242).
- Item 1 therefore holds at head: one loosening occurred mid-run and was restored-and-strengthened before the reviewed sha; nothing else in `git log -p --since=2026-08-27T04:00Z -- tests/` deletes an assertion, widens a tolerance, adds a skip, or removes a test file (I read every removed `check`/`test` line: the only other removal, `1e53fda`'s `check id in inherited` → `check ("id=\"" & id & "\"") in inherited`, is a strengthening).

### B5 — plate labels no longer hidden at the embedded width → RESOLVED
- Evidence at head: `client/replay_broadcast.html:4219-4220` — `#stage.tiny .plate .lives-label, #stage.tiny .plate .smac-lbl { display: none; }` (beside the kill-numeral rule at `:4221`); pinned by `tests/test_viewer.nim:112-121` (`[OK] the 360 px rules are present, labels included`, test log 08:58:23Z). `.tiny` toggles at `boardW <= 620` (< 640), the starter's own mechanism.

### B6 — `#armybars` drawn over the scorebug plates → RESOLVED
- Evidence at head: `client/replay_broadcast.html:4130-4131` — `#armybars { grid-column: 1 / -1; … }` with no `position: absolute` and no `--topband` offset; `ensureArmyBars` (`:4287-4306`) appends into `#scorebug`, so `relayout()`'s `scorebug.offsetHeight` measurement includes the bars and reserves the height. Pinned by `tests/test_viewer.nim:102-110`. The head smoke's scorebug scrape shows the bars as trailing rows after the five plates, not interleaved: `… Unit E DMG 0 0k OURS 5 UP · 480/480 (100%) THEIRS 5 UP · 480/480 (100%)` (wasm-viewer log 09:01:28Z).

### B7 — model text drawn, `canvas_text.total: 0`, no worst-case renderer fixture → RESOLVED
- Evidence at head: the fixture exists and runs in CI, all three pieces:
  - `tools/record_text_fixture.nim` (249 lines) records full-cap `say` (10 widest-glyph runes) on all five units every turn plus full-cap 160-rune notes with 4-byte emoji at both ends, corner spawns, and asserts its own strings full-length and every bubble inside the board before writing (`:130-168`); test-job step output `text fixture OK: every string full length, every bubble inside the board` (08:58:44Z).
  - `replay-viewer/text_fixture.html` (249 lines) loads the real wasm module + `broadcast_core.js` on the main thread, plays the fixture at 360×640 / 640×360 / 1280×720, and sets `data-replay-error` unless every bubble is full-cap runes, band-tall and wholly inside the board and every feed note is full-cap (`:108-145`); sets `data-replay-loaded` only after all three sizes pass (`:238`). Driven by `viewer_smoke.mjs --strict-text-bounds` in ci.yml step "Worst-case renderer text fixture" (`ci.yml:405-431`), which ran green: `{"loaded":true,"ms":2056,…}` (09:01:37Z).
  - `tests/test_shouts.nim` (135 lines) asserts the same invariants natively, including the no-room-above flip case and band == bubble height.
- The reserved band is wired: `shoutBubbleMaxHeight` (`src/smac/global.nim:4091`) is now called at the board stream (`:6233`), the player streams (`:6116`) and the report (`:4992`, `:5029`); it was dead code at the review sha.
- On item 15's `total: 0` clause: `canvas_text.total` is honestly 0 (this board's text is rasterized in Nim and blitted; `grep fillText client/ replay-viewer/` is empty), and the fixture proves placement another way — through `smac_text_report()` / `global.shoutTextReportJson`, whose rects come from `shoutBubbleRectFor`, the same geometry the draw pass uses (`global.nim:4998`, draw at `:6250-6253` via the same `buildShoutBubble` + `shoutBubblePlacement` + band). **I judge this satisfies the clause.**

### B8 — no test asserts `results.reason == "complete"` for an all-scripted episode → RESOLVED
- Evidence at head: `tests/test_replay.nim:88-92` — `check results["reason"].getStr() == ReasonComplete; check results["games"].getInt() == 3` on the recorded 3-battle all-scripted episode. Green in run 33055917137.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 33055917137 `success` on main at 84b271b8 (`gh run list`); `git log -p --since=2026-08-27T04:00Z -- tests/` read hunk by hunk — only loosening (`6e21fe0`) restored strict-and-stronger at `231d17a`, see B4 |
| 2 replay re-derivation + test | PASS | `tests/test_replay.nim:124-155` (frame-by-frame, all 3 battles, via the shipped `initReplayRuntime` the wasm viewer calls); corrupt-hash test `:157-190` proves the check can fail; wasm gate `played every tick to 1121 … hash chain clean` |
| 3 static viewer | PASS | manifest `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, invoked by path in `ci.yml:285`; bundle fetches only its own files + the replay URL; no `/client/replay` in manifest/workflows (the inherited server route is a dev route the platform never uses — the manifest routes replays to the static bundle, and `coworld-release.yml:207` actively rejects a pod viewer) |
| 4 both name spaces | PASS | `tests/test_identity_privacy.nim` (sentinel asserted absent agent-side AND present in `results.names` + broadcast roster); head smoke scorebug shows real config names, feed shows aliases |
| 5 degrade-never-hang | PASS | `decide.nim:465-497` (6 s + 3 s batches inside a monotonic 10 s turn budget, throttle fail-fast `:553-560`); `turnSpacingMs` sleep bounded `:455-458`; lobby join timeout `server.nim:1556-1577`; frame limiter sleeps 1–2 ms `server.nim:998-1007`; bounded shutdown grace `:2335-2344`; `wallClockBudgetSeconds` = 690 ≤ 720 in all four variants (manifest) and `sim_config` rejects > 720 |
| 6 num_agents everywhere + seat invariants | PASS | manifest: 5 in all 4 variants' `game_config` + `certification.game_config`; `certification.players` = 5 = `certification.game_config.players`; `docker_smoke.sh:106-152` four `SEAT-COUNT FAIL:` guards + `SMOKE_SEATS` cross-check; docker-smoke log: **zero** `SEAT-COUNT FAIL`, `smoke OK: seats=5 … reason=complete` (08:53:59Z) |
| 7 scripted baseline full legal episodes | PASS | `tests/test_replay.nim:88-92` (`reason == complete`, natural end, 3 battles); `tests/test_control.nim:32-71` (500 states × both baselines × 5 seats: schema-legal orders, legal mask bits, never Up+Down/Left+Right/C); tuned with measurements echoed in the green log (`focus/charge` spreads for all four compositions, test log 08:52:39Z) |
| 8 LLM reply handling | PASS | `llm.nim` `extractJsonObject` (fence/prose tolerant) + `decide.nim:465` (`attempt < 2` = retry once) + `:563-578` (fallback to focusfire, `fallback` record with cause enum); `tests/test_directives.nim` covers the repair matrix |
| 9 rune-safe truncation + multi-byte test | PASS | `directives.nim:65-94` (`runeLen`/`runeSubStr`, sanitize after rune cut); `tests/test_directives.nim:97-108` (4-byte emoji straddling the say cap, valid UTF-8); `tests/test_replay.nim:192-199` (non-ASCII label + emoji through results, `validateUtf8() == -1`), `:201-220` (replay_summary.py stdout strict UTF-8) |
| 10 manifest validates | PASS | `game.docs.readme` + 4 pages all `{type:"text",value:non-empty}`; `game.protocols.player` and `.global` both text objects (parsed the manifest directly) |
| 11 legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` (html:4076-4081); labels hidden under `.tiny` (boardW ≤ 620 < 640): `.lives-label`/`.smac-lbl`/`.smac-kills` (`:4219-4221`); army bars a measured scorebug row (B6); pinned by `tests/test_viewer.nim:102-121` |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify (:173) → Upload policies (:212) → Upload coworld (:310) → Secret put (:348); 3 workflows present; `docker_smoke.sh` 100755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 scripted, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; placeholder grep over the five files finds nothing (gate exits 0) |
| 13 viewer executes | PASS | `wasm-viewer` `needs: [docker-smoke, test]` (ci.yml:248); "Load the bundle in a real browser" ran against docker-smoke's replay, no `continue-on-error`: `{"loaded":true,"ms":1851,…}` with real clock/scorebug text (09:01:28Z); `data-replay-loaded` set on first drawn frame (`static_replay.js:161`, 'loaded' branch), `data-replay-error` in `showFailure` (`:14-20`); non-MODULARIZE link flags (`config.nims`, no MODULARIZE/EXPORT_NAME) + worker `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) — both from coworld-ctf, diffs are `ctf_`→`smac_` renames only |
| 14 chrome is the starter's | PASS | `chrome_common.js` byte-identical (diff clean; sha256 pinned in `tests/test_viewer.nim:33-41`); `broadcast_core.js` differs in exactly one identifier (`CTF_WIRE`→`SMAC_WIRE`, line 49); `replay_broadcast.html` = starter page (4512 vs 4660 lines) + game block under the banner at `:4040`; diff above the banner = the listed removals (hearts/flags/hill/paint/perks/`#viewpanel`) + the recorded retargets + the restored `.fpv-map` rules (N7a, named in-page); `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:3983-4011`); `#endcard { … bottom: var(--band, 0px) }` + `.on` (`:875-897`) and every seek removes it (`:1860`); beats are labelled `<button>`s via `smacBeat` (`:4246`) with CSS for all five emitted kinds (`:4193-4210`) and dead kinds absent; `#viewpanel`/`#minimap`/`#zoombar` ids absent (grep exit 1) |
| 15 every drawn string fits | PASS | smoke and fixture steps both run `--strict-text-bounds` with `never_inside: 0`; `total: 0` is honest (text rasterized in Nim, no `fillText` exists) and placement is proven another way by the worst-case renderer fixture (see B7), which asserts its own strings are full-length at record time and at render time, at three canvas sizes, failing via `data-replay-error`; the reserved band is cap-derived (`shoutBubbleMaxHeight`) and wired into the draw path |
| parallel batch | PASS | `decide.nim:476-497`: one `RequestBatch` filled for every open seat, one `makeRequests(batch, …)` per attempt; no per-seat request loop exists |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `4b20af5` — one proc both call sites | `scenario.nim:324`, `server.nim:2108`, `replays.nim:564`; wasm gate + native test green | yes |
| B2 | fixed, `a33283d`+`b8e8a9c` | `test_replay.nim:124-155` present and green; recorder re-seats between battles and no longer calls `startGame` | yes |
| B3 | fixed, `ea1b547` | `scanMismatchTick`/`replayMismatchTick` + gate drives to `smac_replay_max_tick()`; corrupt-hash test proves failure path | yes |
| B4 | fixed, 5 commits, strict on all four | `test_control.nim:246` unconditional `check focus > charge`; later commits touched only baselines source/comments; RULES.md + manifest regenerated and byte-equal | yes |
| B5 | fixed, `369e138` | `:4219-4220` + `test_viewer.nim:112-121` | yes |
| B6 | fixed, `b7fd54e` | `#armybars` grid row in `#scorebug`, no absolute positioning; test pins it; head smoke scorebug not interleaved | yes |
| B7 | fixed, `34f0529`+`ec10b24`+`84b271b` | all three pieces + band wiring + green CI steps + artifacts | yes |
| B8 | fixed, `6834fc7` | `test_replay.nim:88-92` | yes |
| N1 | disputed as a defect | I concur with the dispute: the sleep is bounded by config, the serve thread is independent, the worst-case arithmetic already charges it, and item 5 requires bounded waits, not zero waits — the design-note prose mismatch is advisory | yes |
| N5/N7a/N9 | fixed | `MaxCogIdRunes = 16` wired in `directives.nim`; `.fpv-map` rules restored (`:655-676`); `scanTeamLead` micro branch + `ARMY HP LEAD` caption | yes |
| N2–N4, N6–N8, N10–N17 | deferred as advisory | none falsifies a checklist item — checked each against the checklist text; N17 (`/client/replay` dev route) I rule non-blocking as the reviewer anticipated: item 3 is about the platform's replay path, which is the static bundle | yes |

## Non-blocking observations (mine)

- The `wasm-viewer` smoke picked `dist/smoke/replay.json`, which is the binary `COWLDSMC` replay under a `.json` name (the smoke script's naming). Harmless — both the browser shell and the gate loaded it — but the name will mislead a human reading the artifact.
- `viewer_smoke.mjs` still renders at one viewport (1280×720); item 11 is pinned by CSS assertions plus the fixture's 360×640 render, which is adequate but indirect. The fixer's NOTED suggestion of a `--viewport` template flag is worth carrying forward.
- Advisories N2 (one Bedrock candidate), N3 (no `<ROLE>` prompt line), N10/N11 (spawn-line and swarm/blade art), N12 (mechanics gated off, not deleted), N13 (`record_fixture.sh` absent; `check_gameversion.sh` unwired), N14 (test-coverage gaps vs the note's §Tests), N15 (permille quantisation) remain open as design-note deviations; none maps to a checklist item.

BLOCKING: 0
