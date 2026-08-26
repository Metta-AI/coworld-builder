blocking: 0

# r1 verdict — pistonball

Head: `49518a22d734a3bcb952cc32952fe6e67eea39c6` (verified with `git rev-parse HEAD`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + one-parallel-batch rule)
Independent read written before reading fixes: yes (repo, design note, CI log for run 32928137084,
starter diffs, and the full `git log -p --since="2026-08-26T00:27Z" -- tests/` history were read and
noted before `r1-review.md`; `r1-fixes.md` was opened last, after every finding had been verified at
the current head).

## Standing blocking findings

None. Every checklist item verified from the tree or from cited CI evidence at the current head.

## Refuted / resolved / adjudicated

The r1 review itself reported **zero blocking findings** and thirteen advisory ones (N1–N13). I
re-derived each from the code at `49518a2`. Twelve are resolved or correctly answered at head; the
two the reviewer flagged as checklist tensions (N10, N13) I adjudicate below as satisfied. Nothing
in the review stands as blocking, and my own independent pass found no finding the reviewer missed
that ties to a checklist item.

### N1 (stale RULES.md) → RESOLVED at head
- Evidence: `docs/RULES.md:77` now reads `GravityPerSubstep = 1 064 um/tick per substep (9.81 m/s^2
  at 384 substeps/s)`; `:98` "Each tick integrates 16 substeps of 1/384 s"; `:73-75` documents the
  seeded drop offset. `tests/test_manifest.nim:150` ("every docs page is the SHIPPED file, byte for
  byte") pins the manifest inline copies to the files. Resolving commit `cabb48d`.

### N2 (angle advanced 4× per tick) → RESOLVED at head (angle); torque/drag half answered in place
- Evidence: `src/pistonball/sim.nim:326-327` now reads
  `sim.angleQ = int32((int64(sim.angleQ) + int64(sim.spin) div int64(SubSteps) + 4096) mod 4096)`
  — the drawn angle advances by `spin` per tick. `tests/data/golden_hashes.json` regenerated in the
  same commit (`5414e57`), which is the documented-sim-change case item 1 explicitly permits.
  The unrescaled torque/drag constants are a recorded tuning decision
  (`sim_types.nim:77` "PER-SUBSTEP coefficients, on the 384 Hz substep clock"); no checklist item
  pins physics constants.

### N3 (score floor below −18.000) → RESOLVED at head
- Evidence: `src/pistonball/sim_state.nim:113-115` — `progressPoints()` returns
  `max(0'i64, sim.progressMilli)`; the accumulator stays signed.
  `tests/test_scoring.nim:99-110` plays the real episode (seed 63352, metronomes), asserts
  `progressMilli < 0`, `progressPoints() == 0`, `scoreMilli() >= -18_000`. Commit `835402f`.

### N4 (certify timeout) → RESOLVED at head
- Evidence: `.github/workflows/coworld-release.yml:181` — `--timeout-seconds 300 \` on the certify
  step. Commit `5083e62`.

### N5 (cert fleet ≠ note's twenty baselines) → correctly answered, not a checklist item
- Evidence: both declared player ids (`baseline`, `metronome`) occupy ≥ 1 cert slot (1 + 19 = 20);
  all four seat-count invariants hold (verified below under item 6). The composition is a recorded
  deviation (commit `844697a`: a 20-wavebot fixture delivers in ~120 ticks and reads as frozen to
  the 12 s soak) and is now pinned by `tests/test_manifest.nim:170-195` ("plays the WHOLE fixture").

### N6 (sentinel seed collision) → RESOLVED at head (kept and tested)
- Evidence: `tests/test_startup.nim` "the SENTINEL seed is not a pin, wherever it comes from"
  asserts the fixture's own config text is not treated as pinned and the sentinel key is stripped,
  against the exported `seedPinned`/`stripUnpinnedSeed` procs. Commit `7e2896e`. Rationale (public
  manifest ⇒ public seed ⇒ pre-computable `perm`) is sound; no checklist item requires a pinned
  cert seed.

### N7 (protocols.player == protocols.global) → RESOLVED at head
- Evidence: parsed the manifest — `protocols.player.value` is 4202 chars, `protocols.global.value`
  is 2702 chars, distinct texts each written for its own reader.
  `tests/test_manifest.nim` asserts `player != global` plus four exclusive markers per side.
  Commit `811ea0a`.

### N8 (prompt inverts the note's wave/catch wording) → refuted as a defect; deviation now recorded
- Evidence: the controller fires `up_m` on `dxp <= 0` (`control.nim:65,75` — ball at-or-left of my
  centre), agreeing with the shipped prompt (`llm.nim:260-268` "at-or-LEFT-of me"), with the note's
  own controller table (design.md:602,607) and phase rule (design.md:268). The note's prompt block
  is the internally inconsistent document. `llm.nim:222-234` now records the deviation. Commit
  `8ab425b`. No checklist item touched.

### N9a–g (missing/weak assertions) → RESOLVED at head
- a/b: `tests/test_engine.nim:153-185` — a fake provider behind the `LlmClient.sendBatch` seam
  asserts one batch of twenty (each seat tagged once, one shared in-flight window), spacing,
  hung-provider budget, exactly-one retry, throttle-skips-retry. Commit `fe09266`.
- c: `tests/test_determinism.nim` mutation is now ±1 over three ticks × three seats. Commit `a47584d`.
- d: `tests/test_control.nim:96-124` asserts crest position of `rippleHeight` itself per column.
  Commit `680c4aa`.
- e: `tests/test_viewer.nim:42` — `check hex(sha256(chrome)) == StarterChromeSha256`; broadcast_core
  checked by un-renaming and hashing back to the starter digest (`:119`). Commit `f039287`.
- f: `tests/test_physics.nim` pins settled penetration to 0..80 µm (tighter than the old < 5000) and
  adds the friction-never-reverses case. Commit `59f00b2`.
- g: `tests/test_replay.nim:113-126` — `recordEpisode` sets `collectEvents` and the vocabulary test
  asserts `kinds["handoff"] >= 1` and `kinds["launch"] >= 1`. Commit `135067f`.

### N9h (socket contract not exercised against a running server) → stands as advisory only
- No checklist item requires an in-process running-server harness; the properties are covered
  end-to-end by `docker-smoke` (run 32928137084: `all 20 player containers exited 0`,
  `smoke OK: seats=20 … reason=complete`, artifacts written to `file://` URIs). Non-blocking.

### N10 (renderer fixture / canvas_text total 0) → ADJUDICATED: item 15 satisfied at head
- The literal clause "loads the real `client/renderer.js`" is unsatisfiable in this repo: there is
  no JS renderer. Model text has exactly two production paths — `say` baked by `bakeBubble`
  (`src/pistonball/global.nim`, pixie + `data/font.ttf` size 20) and blitted as a wasm sprite;
  `note` written as a DOM `.feed-row`. Item 15's own parenthetical "(or provably the production
  text-layout code paths)" is what binds, and at head it is met twice over:
  1. `tests/test_render.nim` (new, commit `1f07e10`) drives the **production `bakeBubble`** with
     full-cap 48-rune strings (widest-case `"WWW…"`, 4-byte-codepoint terminated) and measures the
     pixels: ink present, ink inside the plate, plate inside the reserved band
     (`bubbleSlotY(slot) + BubblePlateHeight <= BubbleBandBottom <= MapHeight`), plate clear of the
     `MapWidth - 40` clip clamp, at every slot and every piston. This also fixed a real defect the
     review's band arithmetic spotted: the third plate previously sat 5 rows past the band bottom.
  2. `tools/ci/renderer_fixture.html` reproduces the production plate geometry in the production
     face (font.ttf via FontFace API) at 360/620/1280 px, self-checks its strings are full-length
     (48/160 runes, throws otherwise), and runs under `viewer_smoke.mjs --strict-text-bounds` in its
     own ci.yml step.
- CI evidence at head (run 32928137084, `wasm-viewer`, step "Full-cap speech-plate fixture at
  360 / 620 / 1280 px", log 2026-08-26T04:01:50Z):
  `canvas text: 60 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` with `{"loaded":true,…}`. The bundle run's
  `canvas text: 0 drawn` is structural (wasm sprite text, not 2D fillText), is documented in
  ci.yml's step comment, and is not the gated evidence — the fixture step and test_render are.

### N13 (`/client/replay` served by the game pod) → ADJUDICATED: item 3 satisfied at head
- The route table is byte-for-byte the starter's own: `/workspace/starters/coworld-ctf/src/ctf/
  server.nim:825-826` answers `bitworldClient.ReplayClientRoute` (= `/client/replay`) exactly as
  `src/pistonball/server.nim` does; the certifier probes these routes before starting player pods,
  so deleting them breaks certification. Read literally, item 3 would fail the starter itself.
  The binding sense of item 3 — the platform's replay viewing must not be a pod path — is
  satisfied: `coworld_manifest_template.json` declares `"replay_viewer": {"bundle":
  "static-replay-viewer"}` (verified by parse), `tools/build_replay_viewer.sh` exists, mode 100755,
  and refuses non-`static-replay-viewer` output paths, and the static bundle's only network call is
  `fetch(message.replayUrl)` (`replay-viewer/static_replay_worker.js:113`) — S3 and nothing else.
  No manifest key, viewer file, or workflow points at `/client/replay`.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32928137084** on `main` at `49518a2`: conclusion `success`; jobs `test`/`docker-smoke`/`wasm-viewer` all success. `git log -p --since="2026-08-26T00:27Z" -- tests/` read hunk by hunk (+576/−71 over 12 files): every deletion is an assertion replaced by a strictly stronger one (`tickCount > 0` → `== 1800`; penetration `< 5000` → `0..80` µm; mutation ±40 → ±1 ×9; ripple tautology → crest assertion on `rippleHeight`; substring probes → sha256 pins) or the regenerated `golden_hashes.json` accompanying the documented N2 sim fix (`5414e57`). No skip/xfail/removal anywhere. |
| 2 Replay re-derivation | PASS | `tests/test_replay.nim:55-78` re-simulates a recorded episode from config + command bytes with `mismatchQuit = true` and asserts every recorded hash reproduces (`hashIndex == data.hashes.len`, final `gameHash` equal). Viewer path: `replay-viewer/pistonball_replay.nim:3` imports the same `pistonball/sim`; `replays.nim:308-313` `stepReplay` → `checkReplayHash` every tick; display built from the re-derived sim by `buildReplayViewerPacket` (`pistonball_replay.nim:41`) — no parallel recording. |
| 3 Static viewer | PASS | Manifest `game.replay_viewer == {"bundle":"static-replay-viewer"}` (parsed); `tools/build_replay_viewer.sh` mode 100755 (`ls -la`), output-path guarded, wired as the build hook and asserted executable in ci.yml (`Assert the replay-viewer build hook…`); worker's sole network call is `fetch(message.replayUrl)` (`static_replay_worker.js:113`). `/client/replay` adjudicated above (N13): starter-inherited certifier-probe route, no pod replay path in the manifest or viewer. |
| 4 Both name spaces | PASS | `decide.nim:206-247` `windowView` composes `alias(piston)` (`PST-nn`) and no names; `tests/test_locality.nim:74` and `tests/test_server.nim:70` assert no real name reaches a seat; viewer maps aliases→real names in `broadcast.nim` roster, endcard (`replay_broadcast.html:4420-4455`), `results.names` (`roster.nim`). |
| 5 Degrade-never-hang | PASS | Every wait bounded: attempt1/retry via curl timeout (`decide.nim:389-405`), monotonic `turnBudgetMs` (`:325,383-388`), bounded inter-batch sleep (`:369-373`), budget guard (`:333-342`), lobby `lobbyJoinTimeoutTicks` (`server.nim:563-573`), wall-clock stop → `deadline/wall_clock` (`server.nim:444-451`), 20 s shutdown grace. `tests/test_engine.nim:142` asserts the sum fits 60 % of 1200 s (720 s); `tests/test_manifest.nim:208` asserts `wallClockBudgetSeconds ≤ 720` per variant (660/480). Hung-provider case tested with the fake (`test_engine.nim:201`). |
| 6 num_agents | PASS | Parsed manifest: `num_agents: 20` in `default`, `sprint`, and `certification.game_config`; `len(certification.players) == 20`; `len(certification.game_config.players) == 20`. `tools/ci/docker_smoke.sh:110-151` enforces all four invariants before any container starts, each exiting non-zero with `SEAT-COUNT FAIL:`; `SMOKE_SEATS: "20"` in ci.yml is the independent second declaration. Grepped the full log of run 32928137084: zero occurrences of `SEAT-COUNT FAIL`; positive evidence `game=pistonball seats=20`, `all 20 player containers exited 0`, `smoke OK: seats=20 … reason=complete`. |
| 7 Scripted baseline plays full episodes legally | PASS | `tests/test_baselines.nim:14-29` — 500 random states × both baselines emit schema-legal scripts (ranges, enums, rune caps) with in-range command bytes; `:37-64` — full 20-seat episodes on 20 seeds, ≥18 deliver, mean > 60 (CI printed `wavebot: 20/20 delivered, mean 97.053`). `tests/test_scoring.nim:63-71` asserts `endReason == ReasonComplete` on delivery; `tests/test_perf.nim`/`test_determinism.nim` assert the non-delivering fleet plays the full `tickCount == 1800` to the natural end. Tuning harness: `tools/tune_baselines.nim` + `tools/ci/baseline_tuning.json` + `tests/test_tuning.nim` pins the shipped params to the sweep's pick. |
| 8 LLM reply handling | PASS | `scripts.nim:138-177` `extractJsonObject` (fence-tolerant, outermost `{…}`); repair table accepts prose, percentages, centimetres, numeric strings; retry exactly once (`decide.nim:380` `attempt < 2`, tested at `test_engine.nim:227,248`); fallback to wavebot recorded via `fallbackRecord` with cause enum and counted into `results.fallbackTurns` (`server.nim:610-611`) — phase-60 countable; log phrase "falling back" emitted (`decide.nim:457`). |
| 9 Rune-safe truncation | PASS | Single cut `truncateRunes` (`scripts.nim:69-76`, `runeLen`/`runeSubStr`); applied to note/say/policy/detail/prompt and the ≤700-rune script record; provider bodies rune-truncated at source (`llm.nim:194,203,211`). `tests/test_scripts.nim:63` feeds a 4-byte emoji astride the 48-rune cap and asserts rune-boundary cut + valid UTF-8 round-trip; `tests/test_replay.nim:132` runs `replay_summary.py` output through a strict UTF-8 JSON parser with forced non-ASCII say/label. |
| 10 Manifest validates | PASS | Parsed: `game.docs.readme == {"type":"text","value":…}` (1101 chars); `pages` = 3 × `{id,title,content:{type:"text",value}}` (rules 9878, protocol 5147, scripts 2843 chars); `game.protocols` carries both `player` (4202) and `global` (2702), distinct, each `{"type":"text",…}`. `tests/test_manifest.nim:119,150` pin shape and byte-identity to shipped files. |
| 11 Viewer legible at 360 px | PASS | `client/replay_broadcast.html:4043-4048` — `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }`; `:3986` `stage.classList.toggle('tiny', boardW <= 620)`; `:4189-4192` `.tiny` hides tags/hillchip/journey caption. `tests/test_viewer.nim` asserts both rules. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: build (`:153`) → certify with `--timeout-seconds 300` (`:167,181`) → upload-policies (`:213`) → upload-coworld (`:311`) → secret put (`:349`), one sequential job; docker-smoke builds its image in-run before the smoke. All three workflows present; `docker_smoke.sh` mode 100755. `policies.json`: 4 policies — 2 × `PLAYER_PROMPT` (`pistonball-swell`, `pistonball-cascade` carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) + 2 × `PLAYER_SCRIPTED` (wavebot, metronome). The three-name placeholder grep over the five files exits 1 (nothing found) — I ran it. |
| 13 Viewer executes | PASS | Run 32928137084 `wasm-viewer` green including step `Load the bundle in a real browser` (no continue-on-error; `needs: docker-smoke` at ci.yml): `{"loaded":true,"ms":553,…}`, soak `2/888 → 242/888 → 290/888`, scrub readouts at 0/50/100 %. Shell sets `data-replay-loaded` on first drawn frame (`static_replay.js:161`) and `data-replay-error` in `showFailure` (`:14-20`). Link flags and bootstrap are the SAME starter's matched pair: `config.nims` has no MODULARIZE/EXPORT_NAME (diffed — rename-only vs starter), worker uses `Module.onRuntimeInitialized` (`static_replay_worker.js:188`), both byte-identical to the starter modulo the `ctf→pistonball` rename (sed-and-diff verified); `tests/test_viewer.nim` pins the pairing. |
| 14 Chrome is the starter's | PASS | `chrome_common.js` byte-identical to `/workspace/starters/coworld-ctf/client/chrome_common.js` (sha256 equal; also test-pinned). `replay_broadcast.html` 4522 lines vs starter 4660; everything above the `PISTONBALL additions…` banner (`:4018`) diffs against the starter as: removal of `#viewpanel`/`#fpv`/`#povBadge` markup+CSS (fixed 1200×600 arena — removal is the rule's required treatment), matching null guards, `CTF→Pistonball` identifier and comment renames, two removed sprite-preload loops (would 404). Transport rules verified in-page: `relayout()` sets `--band`/`--hudscale`/`--topband` on `document.documentElement` (`:3964,3985-3991`); `#endcard { bottom: var(--band, 0px) }` (`:748`), shown via `#endcard.on` (`:759`), taken down on every non-gameover frame (`:1732`) so every seek dismisses it; beats are labelled `<button>`s that seek (`:4258-4269`) with CSS for every emitted kind (`:4158-4163`: launch, bounce_back, stall, delivered, over, gameover). |
| 15 Every drawn string fits its frame | PASS | ci.yml's bundle smoke carries `--strict-text-bounds`; head run reports `never_inside: 0`. The bundle's `total: 0` is structural (text is wasm-baked sprites, not 2D fillText) and is not relied on: the production text path (`bakeBubble`) is gated by `tests/test_render.nim` (full-cap 48-rune say incl. widest-case, pixels asserted inside plate/band/board, plate clear of the clip clamp, reserved band sized from the server cap `MaxSayRunes` in `data/font.ttf` at the drawn size) and the worst-case browser fixture step "Full-cap speech-plate fixture at 360 / 620 / 1280 px" reports `canvas text: 60 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` at head. Fixture self-asserts full-length strings (throws if say ≠ 48 or note ≠ 160 runes). Adjudication of the "real renderer" clause under N10 above. |
| Parallel batch rule | PASS | `decide.nim:391-405` — one `RequestBatch` filled with every open seat, one `makeRequests` call per attempt; no per-seat request path exists. `tests/test_engine.nim:153-185` asserts one batch of twenty with a single shared in-flight window via the fake provider. |

## Fixer report audit

Read after all of the above. The disposition table matches what I independently verified at head.

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| N1 | fixed `cabb48d` | RULES.md carries 16 substeps / 1064 / offset; manifest pages byte-pinned to files | yes |
| N2 | fixed (angle) + evidence (torque/drag) `5414e57` | `sim.nim:326-327` `spin div SubSteps`; golden regenerated same commit; constants documented | yes |
| N3 | fixed `835402f` | `sim_state.nim:113-115` clamp on the way out; seed-63352 test present | yes |
| N4 | fixed `5083e62` | `coworld-release.yml:181` `--timeout-seconds 300` | yes |
| N5 | evidence + pin `066fa17` | `test_manifest.nim:170-195` guards fixture length; both ids seated | yes |
| N6 | fixed `7e2896e` | sentinel semantics exported and tested | yes |
| N7 | fixed `811ea0a` | protocols distinct (4202 vs 2702 chars), exclusive markers tested | yes |
| N8 | DISPUTED, deviation recorded `8ab425b` | controller/`SCRIPTS.md`/note's own tables agree with shipped prompt; comment at `llm.nim:222-234` | yes — dispute upheld |
| N9a–g | fixed (6 commits) | all seven assertions present and strictly stronger; read every hunk | yes |
| N9h | NOT FIXED (evidence) | no checklist item requires it; docker-smoke covers the behaviour end-to-end | yes — advisory |
| N10 | fixed `1f07e10` | test_render.nim + production-face fixture; head-run canvas_text 60/0/0; band defect fixed | yes |
| N11 | fixed `f71ccde` | metronome fleet, `tickCount == 1800` asserted | yes |
| N12 | fixed `49518a2` | three-draws docstring, SubSteps comment, `RippleColumnTicks` gone, single `var head`, comments cleaned | yes |
| N13 | evidence answer | starter serves the same routes (`ctf/server.nim:825-826`); manifest declares no pod viewer | yes — adjudicated satisfied |

Fixer's "+576/−71, nothing weakened" claim independently confirmed (`git diff --shortstat
ce20047..49518a22 -- tests/` = 12 files, +576/−71; every deletion read).

## Non-blocking observations

- Item 7's "asserts `results.reason == "complete"`" is met compositionally (delivery asserted on
  ≥18/20 seeds in `test_baselines`; `delivered ⇒ ReasonComplete` asserted in `test_scoring:63-71`;
  full-length natural end asserted in `test_perf`/`test_determinism`), not by one unconditional
  assertion on a single episode. Adequate; a single unconditional
  `check game.endReason == ReasonComplete` after a wavebot run would make it literal.
- N9h residue: the running-server socket cases (input mask ignored on a live socket, `/global`
  answering 15 s post-artifacts) remain covered only end-to-end by docker-smoke.
- The `coworld-replay` bridge posts `boot`/`frame` and no `ready` — inherited from the starter
  verbatim; the embed contract lives outside both repos.
- The `deadline` alternative in `test_replay.nim:117` / `test_physics.nim:146` reason assertions is
  unreachable in the headless harness (the wall-clock stop lives in server.nim); harmless slack.

BLOCKING: 0
