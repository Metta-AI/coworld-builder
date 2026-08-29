blocking: 0

# r1 verdict — crafter (Metta-AI/cogame-crafter)

Head: `2a62f81c2d6ac29a2c9002021ce6884a784e1dcc` (= current `main`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule)
Independent read written before reading fixes: **yes** (notes at `/tmp/judge-independent-notes.md`; the
review and `r1-fixes.md` were opened only after the checklist pass below was formed from the tree,
the design note, the starter mount and CI run 33231383944).

Review judged: `runs/2026-08-28-crafter/reviews/r1-review.md` (25 findings, F1–F25, written against
the previous sha `71bf90d1`). CI evidence: run **33231383944**, conclusion **success**, head
`2a62f81c`, jobs `test` ✓ 1m43s / `docker-smoke` ✓ 1m11s / `wasm-viewer` ✓ 2m39s (full log pulled and
grepped, not trusted by colour). I additionally ran the Nim suites myself in-sandbox at head
(`test_crafter_{manifest,world,replay,engine,driver,sim}.nim`, `-d:release`) — all green.

## Standing blocking findings

**None.** Every reviewer finding is fixed or is now a documented divergence at the current head, and
my own checklist pass found nothing blocking.

## Refuted / dismissed (all 25, verified at head — "fixed" means the finding was true at 71bf90d1 and is no longer reproducible at 2a62f81c)

### F1 — skip() + deleted assertions (the review's only blocking finding) → FIXED at `67c0b9d`
- Evidence: `grep -rn 'skip()' tests/` → no matches. `tests/test_crafter_manifest.nim` item 38 is now
  unconditional — it enumerates the template's `{{…}}` placeholders (asserting the set is exactly
  `{{CRAFTER_IMAGE}}`), substitutes, re-parses and asserts the full structural shape; the CLI branch
  remains additive, not gating. `coworld_manifest_template.json` `game.runnable` keys are now
  `[type, image, run, source_url, env]` with `source_url = https://github.com/Metta-AI/cogame-crafter/tree/main`,
  and a new test "the runnable and every declared player resolve to this repo" restores the three
  deleted scaffold assertions (`source_url`, `type == "player"`, `not game.hasKey("image")`).
  Ran locally: `[OK] the manifest loads: the placeholders resolve and the shape validates`,
  `[OK] the runnable and every declared player resolve to this repo`. Green in CI at head.
- Item-1 re-check at head: the fix commit *adds* assertions; nothing was weakened to make it pass.

### F2 — 30/44 directive records `"view": null` → FIXED at `19509ea`
- `src/crafter/directives.nim:216-247` (`boundedDirectiveRecord`): `say` now shrinks first, on rune
  boundaries; the view is dropped only if the record exceeds `MaxDirectiveRunes = 6000`
  (`sim_types.nim:69`) with no `say` left. Test "the record keeps the observation even with a
  full-cap say" passes locally and in CI. (Residue, advisory: the committed fixture
  `tests/replays/forager-seed42.replay` was recorded before this fix and still carries 30
  `"view":null` records — see observations.)

### F3 — achievementTick on the absolute clock → FIXED at `4739094`
- `sim_state.nim:335` now stamps `sim.runTick()` (run-relative, the clock `finalTick` is on); new test
  "achievementTick is on the RUN clock, the one finalTick is on" plays behind a 240-tick lobby and
  passes locally and in CI. `gameHash` mixes only the unlock mask, so the committed fixture still
  re-derives (CI: `ok: loaded forager-seed42.replay, advanced 300 frames`).

### F4 — 22nd derived kind `budget` → DOCUMENTED at `e3d7799` (`docs/PORTING-CRAFTER.md` §G)
### F5 — `throttled` cause outside the note's enum, `disconnected` unemitted → DOCUMENTED at `2cbeaf2` (§H)
### F6 — forager rules 1/4 differ + `restThreshold` tunable → DOCUMENTED at `200f5b9` (§D, with the fighting rationale; the always-once `while … break` is now an `if`, `baselines.nim:246-261`)
### F7 — cog/creature art are committed image-model renders, not `rig_art.nim` → DOCUMENTED at `208d1c1` (§I; committed files, nothing downloaded at build/run)
### F8 — no `roster.nim` module → DOCUMENTED at `96202fe` (§J; the behaviour the note names lives in `sim_state.nim`/`achievements.nim` and is present)
### F9 — `#viewpanel` moved in the markup → DOCUMENTED at `760c9bd` (§L; element and CSS unmodified, `position: absolute`, move needed so `viewer_smoke.mjs`'s document-order `#scrub` probe stops clicking the zoom bar)
### F10 — two added emscripten link flags → DOCUMENTED at `d61e5dc` (§K; `STACK_SIZE=8388608` + `INITIAL_MEMORY=33554432`, the fix for a real wasm32 trap caught by `wasm_replay_smoke.cjs`; bootstrap pairing unchanged — non-MODULARIZE build + `Module.onRuntimeInitialized` worker, same starter set, and CI's browser load is green)
### F11 — playback cadence/speed chips differ from the note → DOCUMENTED at `4357702` (§M; the note's guarantee that matters — the smoke replay outlasts `--soak 10` — holds: 949-tick replay ≈ 40 s at 24 t/s, CI soak advanced "3/950 → 195/950 → 243/950")
### F12 — 16384-byte envelope read vs the note's 4096 → DOCUMENTED at `3a82fac` (§N; the reply *text* is rune-capped at 4096, a mid-codepoint envelope cut raises in `parseJson` and becomes a counted fallback — checklist 9 unaffected, confirmed at `llm.nim` + rune tests green)
### F13 — vacuous world-purity test → FIXED at `d36f083`
- `tests/test_crafter_world.nim:19-45` now asserts all three sims played, their live grids differ,
  and regeneration from each settled config reproduces the reference cell-for-cell (`identical ==
  WorldCells`, `touched <= 200`). Ran locally: `[OK] world is a pure function of the seed`.
### F14 — post-pass ordering hazard → FIXED at `5b12b90`
- `world.nim:285-330`: steps 2–5 now run to a fixed point (3 sweeps); `carve` sands ore too (the
  `keep` template protects only bedrock and the spawn 3×3, `world.nim:238-241`) and the ore minima
  run after as step 6. New regression "the guaranteed tree, water and stone are still REACHABLE
  afterwards" over 200 seeds × 2 variants — passes locally and in CI. (Advisory: a stale comment at
  `world.nim:315-317` still claims the corridor "never sands over coal, iron or diamond", which now
  contradicts `carve`'s own doc-comment and behaviour.)
### F15 — "Three things" miscount → FIXED at `390eae3` (`docs/PORTING-CRAFTER.md:105` now says "every divergence … is a lettered section below", no count; sections A–P present)
### F16 — geometric mean not in RULES.md → FIXED at `4f748e7` (`docs/RULES.md:145-163` states the formula, the ten-episode floor, and "NOT what the ladder ranks")
### F17 — `|| true` on the page-derivation check → FIXED at `6f03054`
- `ci.yml:163-181`: checks out `Metta-AI/coworld-ctf` at pinned sha `a7484eb4…` into `.starter`, runs
  `python3 tools/build_broadcast_page.py --starter .starter --check` with no `|| true`. Ran at head:
  `client/replay_broadcast.html matches the derivation`. I also ran the check myself against the
  sandbox starter mount — exit 0.
### F18 — dead `playerNames` table → FIXED at `0bd8d92` (`grep -n playerNames src/` → no matches; the join's placeholder name is written directly with the reason in a comment)
### F19 — bite-ended rested sleep never unlocked `wake_up` → FIXED at `6383fcf`
- `sim_state.nim:512-515`: the damage-wake path now makes the same `energy >= 9 and
  sleepRunStartEnergy < 9` test and records `aWakeUp`. Ran locally: `[OK] wake_up also unlocks when
  a bite is what ends the rested run`.
### F20 — within-tick creature tiebreak by kind → DOCUMENTED at `e3120b8` (§O; re-sorting would break every recorded hash for no observable difference)
### F21 — sapling-draw word count + point-blank arrow shortcut → DOCUMENTED at `6f3ed6a` (§P)
### F22 — five stale foreign-game docstrings → FIXED at `f00cdcc` (verified: `decide.nim` header reads 24/56/112 and `forager`; `crafter_replay.nim` reads "1344 ticks over a 4096-cell grid"; the fpv comment fixed at its source in `tools/build_broadcast_page.py` and the derivation check still passes)
### F23 — committed ELF test binaries → FIXED at `e87cbef` (`git ls-files` shows no binaries under `tests/`; `.gitignore` covers `/tests/test_crafter_*` with `!/tests/test_crafter_*.nim` and `/tests/shards/tests`; the ELFs in the working tree are untracked local build leftovers, `git status` clean)
### F24 — 9-row tuning table that did not reproduce → FIXED at `2a62f81`
- `tools/ci/baseline_tuning.json` is now a 1296-cell matrix (verified by parsing: every tunable in
  `pick` — `thirstThreshold`, `hungerThreshold`, `shelterStones`, `sleepTicks`, `restThreshold`,
  `exploreSteps`, `tieBreakByDistance` — takes >1 value across the grid and the pick's values were
  played); `DefaultBaselineParams` moved with the real sweep (`sleepTicks 16`, `shelterStones 2`,
  `baselines.nim:43-46`) and the strengthened test "the shipped thresholds equal the swept pick"
  passes locally and in CI. The cert-seed floor (≥ 900 ticks, ≥ 6 unlocked) still holds — CI smoke:
  `smoke OK: … reason=complete`, scrub 100 % at tick 948, 14 unlocked.
### F25 — no CI rename-sweep grep → FIXED at `acf2c37` (`ci.yml:123-154`, character-class-spelled grep with exactly three named allowances; ran at head: "no starter identifier survives outside comment history")

The review's "could not determine" items: the late-gameStart seek path is code-unconditional
(`crafter_replay.nim:82` seeks to `replayStartTick()`; `replays.nim:482` clamps every seek there;
`startTick` set from `sim.gameStartTick` at `replays.nim:379-380` / `replay_runtime.nim:33-35`) and
the head smoke's scrubber axis opens at run tick 3 of 950 — consistent; `source_url` is now present
(F1) so the CLI-acceptance question is moot at the level the checklist gates; F14's ordering hazard
now has the exact regression test the reviewer asked for, and it passes.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 33231383944 `success` on `main` at 2a62f81c (test/docker-smoke/wasm-viewer all ✓). Whole `git log -p -- tests/` read: the only deletions are (a) the F23 binary removals, (b) the 5a50909 replacement of the initial scaffold — which carried *foreign-game* assertions (`blScout`, `edGauntletComplete`, `norules.xlandRules`) that never compiled against this sim and never ran green (first CI run on the repo is 33225446565, for 5a50909 itself, cancelled) — and (c) F1's `skip()` removal, which *strengthens*. 87dc787/f00cdcc are comment-only. All fix-round test changes add or tighten assertions. |
| 2 Replay re-derivation, frame by frame | PASS | `replays.nim:290-303` `stepReplay` → `checkReplayHash` after every tick, `:259-288` per-tick hash compare latching `hashMismatchTick`; `tests/test_crafter_replay.nim:97-110` records + re-derives all six end reasons, asserts `mismatch == -1` (ran locally, `[OK]`). Viewer draws from the re-simulated sim: `crafter_replay.nim:104-109` → `buildReplayViewerPacket`, no parallel frame stream. |
| 3 Static viewer | PASS | manifest `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, asserted + invoked by path (`ci.yml:334-358`); worker fetches only the given replay URL (`static_replay_worker.js:113`); no `/client/replay` in the manifest — `server.nim:193` is the starter's local-dev route only, and `coworld-release.yml:205-212` hard-fails certification unless the STATIC bundle is reported. |
| 4 Both name spaces | PASS | observation identity is only `"you": seatAlias(0)` = "Alpha" (`sim_state.nim:812`); spectator roster carries real `name` + `alias` (`broadcast.nim:125-147`); head smoke scorebug renders both: `"…FORAGER … ALPHA…"`. `register` record redacted (no prompt), `showPlayerLabels: false` in both variants. |
| 5 Degrade-never-hang | PASS | `decide.nim:188` `while open and attempt < 2`; per-attempt deadline `min(attempt1Ms\|retryMs, remaining)` handed to curl as whole seconds (`:202-223`); monotonic `turnBudgetMs` 9.5 s; rate guard (`:119-126`) and budget guard (`:145-152`) fall back with no network wait; lobby capped `lobbyJoinTimeoutTicks` (`sim_state.nim:582`); wall-clock stop at loop top (`server.nim:488-493`), `wallClockBudgetSeconds = 660 ≤ 720` (60 % of `episode_timeout_minutes: 20`), asserted by `test_crafter_manifest.nim`; bounded shutdown hold (`server.nim:630`); player dial/reconnect bounded, exits 0 on dead socket (`crafter_player.nim:85-150`). |
| 6 num_agents | PASS | `num_agents: 1` in `standard`, `longnight` and `certification.game_config` (parsed the manifest myself); `len(certification.players) == len(certification.game_config.players) == 1`; `docker_smoke.sh:110-151` carries all four SEAT-COUNT invariants + the independent `SMOKE_SEATS=1` cross-check, before any container starts; **`grep 'SEAT-COUNT' <head docker-smoke log>` → no matches**; log shows `seats=1 … "num_agents": 1` and `smoke OK: seats=1 … reason=complete`. |
| 7 Scripted baseline, full legal episodes, tuned | PASS | `test_crafter_engine.nim:45-63` — six all-scripted episodes (2 variants × 3 seeds) end `erComplete` with all six results identities (ran locally, `[OK]`); legality over 300 states × both baselines in `test_crafter_driver.nim:54-148`; tuning = `tools/tune_baselines.nim` grid harness, 1296-cell recorded matrix, pick == shipped defaults asserted. |
| 8 LLM reply handling | PASS | `extractJsonObject` balanced-brace scan tolerating fences/prose (`directives.nim:40-81`); exactly one retry (`decide.nim:188`); fallback = `foragerPlan` via `foragerFallback` (asserted same proc, `test_crafter_driver.nim:150`); recorded as `fallback` chat record + `results.fallbackTurns`; attempt-1 log says "will retry", only attempt 2 says "falling back" (`decide.nim:246, 269`). |
| 9 Rune-safe truncation | PASS | `truncateRunes`/`runeSubStr` the single shortening door (`sim_types.nim:266-284`), applied to say/notes/label/prompt/detail/stopDetail/error text; tests feed 4-byte emoji exactly on every cap and strict-parse the summary (`test_crafter_driver.nim:206`, `test_crafter_replay.nim:171` — ran locally, `[OK]`); CI re-runs the strict-UTF-8 check on the real smoke replay every push (`ci.yml:272-294`). |
| 10 Manifest validates | PASS | `game.docs` = readme + 4 pages, every content a `{"type","value"}` object (`uri`, the starter's own shape — the checklist's `"text"` is the same typed-object shape); `game.protocols` carries **both** `player` and `global` as typed objects. `test_crafter_manifest.nim` green at head, ran locally — 14/14 `[OK]`. |
| 11 Legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis; }` (`replay_broadcast.html:4288-4293`, source `crafter_block.html:31-36`); labels hidden under the starter's `.tiny` (toggled at boardW ≤ 620): vital names, checklist captions, zoombar all `display: none` (`crafter_block.html:263-313`). |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: build (159) → certify (173, `--timeout-seconds 300`, static-bundle marker hard-gate) → upload-policies (216) → upload-coworld (314) → secret put (410); certify runs against the manifest `coworld build` just built in the same run. Three workflows present; both scripts mode 100755; `policies.json`: 2 × `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (line 17). I ran the three-name placeholder grep myself — exit 1, nothing found. |
| 13 Viewer executes | PASS | run 33231383944 `wasm-viewer` ✓ with `needs: docker-smoke` (`ci.yml:321`); browser-load step ran (no `continue-on-error` anywhere in the workflows): `{"loaded":true,"ms":593,…}`, `soak: 10s … ("3 / 950" -> "195 / 950" -> "243 / 950")`, three distinct scrub readouts. Markers: `static_replay.js:161` sets `data-replay-loaded="true"` after the worker's post-ingest `loaded`; `:8-20` sets `data-replay-error`. Opens at game start: `crafter_replay.nim:82` seeks `replayStartTick()` (= `gameStartTick`, `replays.nim:355-380`), every seek clamps there (`replays.nim:482`). Flags/bootstrap one starter: non-MODULARIZE `config.nims` (diff vs starter = renames + 2 documented flags) + `Module.onRuntimeInitialized` worker (`static_replay_worker.js:188`); `loaded: true` is the positive evidence. |
| 14 Chrome is the starter's | PASS | `chrome_common.js` byte-identical (sha256 `7ace7287…` both sides, `cmp` clean); `replay_broadcast.html` 255 673 B (grew), derivation-checked — I ran `tools/build_broadcast_page.py --starter <mount> --check` → "matches the derivation", and CI re-derives against the pinned starter sha every push (`ci.yml:163-181`); `relayout()` sets `--band`/`--topband`/`--hudscale` on `documentElement`; `#endcard { bottom: var(--band, 0px) }` (`:950`) with the starter's seek-dismiss path kept; beats are labelled `<button>`s seeking on click (`crafter_block.html:376-396`) with CSS for exactly the seven emitted kinds; `#viewpanel` kept and really wired — `attachMinimap` (`:4111`), `setZoom(64/15)` + per-frame `panTo` follow-cam (`crafter_block.html:404-437`). |
| 15 Every drawn string fits | PASS | Main smoke `canvas text: 0 drawn` — not evidence by itself, but the design keeps the board layer text-free (no `fillText`/`strokeText` in the board path, grep-asserted by `test_crafter_viewer.nim`) so `--strict-text-bounds` stays on; the required worst-case renderer fixture exists and is green in its own step at head: "Drive the shipped chrome's text path (renderer fixture)" → **`canvas text: 167 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`** — real shipped `index.html` in an iframe, 160-rune emoji `say`, all 22 chips both states, zeroed vitals, both endcards, at 960/640/360 px, with its own full-length assertion (`renderer_fixture.html:162-171, 275-314`). |
| Batch rule (single seat) | PASS | one request per command turn through the starter's batch path carrying a batch of one (`decide.nim:214-223`), plus at most one retry, both deadline-bounded; never more than one in flight. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed `67c0b9d` | skip gone, source_url present, tests run locally green | yes |
| F2 | fixed `19509ea` | say-first shrink, view last, cap 6000, test green | yes |
| F3 | fixed `4739094` | `runTick()` stamp, new lobby-offset test green | yes |
| F4–F5 | documented §G/§H | sections present, test pins 22 kinds | yes |
| F6 | documented §D + tidy | §D covers rules 1/4 + restThreshold; `while`→`if` at `baselines.nim:246` | yes |
| F7–F12 | documented §I/§J/§L/§K/§M/§N | all sections present and accurate against the code | yes |
| F13 | fixed `d36f083` | real three-world comparison, green | yes |
| F14 | fixed `5b12b90` | fixed-point sweeps, ore-sanding carve, REACHABLE regression green (seed-105 story consistent with the code) | yes (one stale comment remains, see observations) |
| F15–F16 | fixed | PORTING line 105, RULES.md:145-163 | yes |
| F17 | fixed `6f03054` | pinned-starter checkout + ungated check, ran green at head | yes |
| F18 | fixed `0bd8d92` | `playerNames` absent from tree | yes |
| F19 | fixed `6383fcf` | `sim_state.nim:512-515`, both wake tests green locally | yes |
| F20–F21 | documented §O/§P | present | yes |
| F22 | fixed `f00cdcc` | all five comments corrected, derivation still checks | yes |
| F23 | fixed `e87cbef` | binaries untracked + ignored, sources kept | yes |
| F24 | fixed `2a62f81` | 1296-cell grid parsed, every tunable swept, pick == shipped, test green | yes |
| F25 | fixed `acf2c37` | grep step in ci.yml, green at head | yes |
| NOTED-1 | longnight seeds 259/291 lack a tree within 12 | reproduced myself with a Nim probe over seeds 201–400 (`longnight seed 259/291: no tree within 12`) | yes (advisory — see below) |

## Non-blocking observations (advisory; none ties to a checklist item)

1. **Stale comment contradicts the F14 fix**: `src/crafter/world.nim:315-317` (inside the sweep loop)
   still says the corridor "never sands over coal, iron or diamond", while `carve`'s own doc-comment
   (`:233-237`) and behaviour say the opposite. Comment-only; the regression test pins the behaviour.
2. **The committed fixture predates F2/F24**: `tests/replays/forager-seed42.replay` still carries 30
   `"view":null` directive records and was played under the pre-sweep baseline parameters. Playback
   is input-driven so it re-derives cleanly (CI + local tests confirm), but a re-recorded fixture
   would exercise the post-F2 record shape and match what docker-smoke now produces.
3. **Generator invariant holds only over the swept seed range**: `longnight` seeds 259 and 291 have
   no tree within Chebyshev 12 of spawn (reproduced in-sandbox; `firstGrassAtRing(6)` finds no grass
   host and gives up silently, `world.nim:288-292`). Pre-dates this round; the design note's "every
   seed is completable" is asserted only over seeds 1–200. Worth a widened ring search in a future
   round.
4. **`results.names[0]` carries `PLAYER_POLICY_LABEL`** (F18's other half, reviewer's own caveat):
   whether the platform injects a real player name via `players[].name` is outside this repo; both
   name spaces are present and separate either way.

No blocking items, so no `- [<category>] <file:line>` lines are required.

BLOCKING: 0
