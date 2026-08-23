blocking: 0

# r2 verdict — ecos

Head: `402792be0c53c815545ec71cc456deffeb66b626` (== `origin/main`, confirmed by
`git fetch && git reset --hard origin/main`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–13 + the
simultaneous-batch rule)
Independent read written before reading fixes: **yes** — I read the checklist, both design-note
copies, and the full source/tests/workflows/manifest at head, inspected every r2 fix-commit diff,
audited the `tests/` hunks, and pulled the CI logs *before* opening `r2-fixes.md`. (The r2 review
itself was also read only after my own pass over the tree; the coordinator's brief named the two
blocking findings in advance, which I note as unavoidable framing — the verification below is
against the code, not the brief.)

This sandbox has a Nim 2.2.4 toolchain (`/tmp/nim-2.2.4/bin`), so the two blocking findings were
verified by **execution**, not inference (details under Refuted).

## Standing blocking findings

None. Every finding of r2-review.md is either fixed at this head or advisory with no checklist
item, and my independent checklist pass found nothing new that a checklist item names.

## Refuted

The r2 review was written at `b4bb25e`, before the fix commits. Both blocking findings were true
at that sha; both are false at the current head — a finding fixed since the review is refuted,
not standing.

### F1 — 429'd seat leaves an unclamped `[0,0,0,0]` doctrine recorded `source:"llm"` → REFUTED (fixed at head)
- Evidence: `src/ecos/llm.nim:478-489` at `402792b` — the `except EcosThrottleError` branch now
  ends with:
  ```nim
  result[index] = scriptedDecision(sim, sim.roleOf[slot], skSteward)
  result[index].source = dsFallback
  ```
  `scriptedDecision(…, skSteward)` returns the steward doctrine through
  `scriptedDoctrineChecked` (clamped-legal by construction), and the seat is still not re-opened,
  so the review's F25 property (retry in the NEXT generation's batch, one request per seat per
  generation) is preserved.
- Fix commit `c3f4ed5`: +7 lines in `llm.nim` (the two assignments plus comment), +95 lines in
  `tests/test_llm.nim` — a `decideAll`-level test over a real loopback HTTP transport that 429s
  every request, asserting for all three seats `source == dsFallback`,
  `fields == scriptedDoctrine(sim, species, skSteward)`, every field inside
  `DoctrineMin..DoctrineMax`, no raise, and `stubHits == 3` (no same-generation retry). Minimal;
  no test weakened.
- Executed: `nim r -d:release tests/test_llm.nim` at head → `test_llm: ok` (log shows all three
  seats throttled and playing scripted). With the `llm.nim` hunk of `c3f4ed5` reverted in the
  working tree, the same test fails with
  `a throttled seat must be recorded as a fallback, saw llm` — the test is load-bearing.

### F2 — `precompute` misses the partial-generation flush on collapse → REFUTED (fixed at head)
- Evidence: `src/ecos/replays.nim:190` at `402792b`:
  ```nim
  if tick > 0 and (tick mod perGeneration == 0 or tick == ticks - 1):
  ```
  The accumulator is flushed on the last recorded tick as well, then zeroed, so a boundary-tick
  ending flushes exactly once (the `or` is not a double flush — `accum` resets). This matches the
  sim exactly: `sim.nim:628-636` closes the partial window via `closeGeneration` against the full
  `ticksPerGeneration × R_i` denominator (`generationScore`, `sim.nim:535-540`), same window
  (`tick > 0` excludes frame 0 on both sides), same per-generation `min(·, 2.0)` cap, same
  summation order — the exact-float-equality test passes.
- Fix commit `9eea729`: +5 comment/1 condition line in `replays.nim`, +63 lines in
  `tests/test_replay.nim` — a collapse episode (greedy-predator `fixedPicker`, seeds 1..6,
  accepted only if `ending.startsWith("collapse_")` AND `tick mod ticksPerGeneration != 0`, i.e.
  only the broken case), asserting through `initReplayPlayer` on the re-parsed replay BYTES:
  `scoreAt[lastTick]` == `results.scores` per slot, the same numbers on the replay's own `end`
  row (F3 used as oracle), and end-card winner/draw matching `results.win`. Minimal; no test
  weakened.
- Executed: `nim r -d:release tests/test_replay.nim` at head → `test_replay: ok`. With the
  `replays.nim` hunk of `9eea729` reverted, it fails with
  `collapse at tick 317, slot 0: the viewer re-derives 5.938842 where results.json carries
  6.447305` — the exact before-fix numbers the fixer reported, independently reproduced.

### F3 — viewer reads neither the `end` nor `generation` event scores → correctly NOT changed
- Advisory in the review itself ("not itself a checklist violation"). Item 2 requires the display
  to come from the re-derivation, which it does; the `end` row is now the F2 test's second oracle
  (`test_replay.nim:193-204`). Nothing stands.

### F4 — `results.generations` counts the partial window → advisory, dispositioned as docs
- No checklist item names `results.generations`. `402792b` (docs-only: design-note §results.json
  "Shipped deviation" block + a description added to the manifest's results schema) makes both
  definitions say what the code does ("generations SCORED"). The counter is also the end
  condition, `runGeneration`'s target and `history.len`, and the partial window IS scored by sim,
  viewer and feasibility summariser alike — changing the count would create disagreement, not
  remove it. Reasonable; the run copy of the design note was left untouched as required. Nothing
  stands.

### F5 — never-connected seat recorded `scripted` not `fallback` → REFUTED (fixed at head)
- Evidence: `src/ecos/server.nim:305-312` (`absent[slot] = true` when a socketless `skNone` slot
  is substituted) and `:326-328` (`if slot < absent.len and absent[slot]: decision.source =
  dsFallback`) at `402792b`, commit `787b916` (server.nim only, 8 insertions). Honest tag; the
  played doctrine is unchanged; late-arriving sockets rejoin because the snapshot is rebuilt each
  generation. Advisory in the review; also closes the item-8 recording gap for this path.

### F6 — two-token config would IndexDefect the game thread → REFUTED (guard at head)
- Evidence: `src/ecos/server.nim:506-508` at `402792b` (`if config.players.len !=
  SeatAliases.len: raise …"Ecos is a three-seat game…"`), commit `6753cec`, next to the
  tokens/players alignment check. Reachability was never established (num_agents=3 in every
  variant + docker_smoke refuses otherwise), so this was advisory; the guard now fails legibly at
  startup instead of hanging to the platform timeout. Nothing stands.

### F7 — replay clock caption counted against the collapse tick → REFUTED (fixed at head)
- Evidence: `client/replay_broadcast.html:2330-2342` at `402792b` — the caption denominator is
  now `s.mt` (configured `generations × ticksPerGeneration`, present on every frame of both
  paths, `broadcast.nim:86`), with `mx` untouched as the scrubber extent. Commit `2c043fc`.
  Cosmetic, no checklist item; wasm-viewer soak green on the change (run 32641507840).

### F8 — birth hairlines starved fades/splashes of fx slots → REFUTED (fixed at head)
- Evidence: `src/ecos/global.nim:407-421` at `402792b` — hairlines are a second pass over the fx
  list; every primary fx object is emitted first and the links spend only what remains of the
  400-slot pool, same ids, same bound, own z. Commit `adbd90a`. Cosmetic, no checklist item.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32641507840**, `ci.yml`, `main`, head sha `402792be…`, conclusion **success**; jobs test/docker-smoke/wasm-viewer all success. Test-job log shows all 8 `tests/*.nim` run in BOTH debug and `-d:release` (no `NIM_TESTS` narrowing). `git log -p --since=2026-08-23T08:41Z -- tests/` read hunk by hunk: additions only, except F15's removal of `doAssert not event.clamped` in `test_baseline.nim` — that assertion checked a literal the test itself passed to `applyDoctrine` (vacuous) and was replaced by the strictly stronger `stewardClamps > 0` plus retained per-field range checks. No test disabled, skipped or loosened. |
| 2 Replay re-derivation | PASS | State-frame recording is the note's design (§Sim module). Viewer derives display from the recorded frames/series: `replays.nim:150-207` (`precompute`), `:216-227` (`boardFrame`), `:235-294` (`chromeFrame` reads `scoreAt`/series). Tests lock viewer-derived scores to `results.scores` and the end-card to `results.win` on BOTH paths: full episode `test_replay.nim:133-158`, mid-generation collapse `:160-221` (plus the `end`-row oracle). Frame-by-frame value equality of recorded vs re-read frames and frame↔series agreement: `test_replay.nim:101-121`. Executed locally: green. |
| 3 Static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}` (asserted `test_manifest.nim:95`); `tools/build_replay_viewer.sh` present, mode 100755, executability asserted in `ci.yml` wasm-viewer job; worker's only network call is `fetch(message.replayUrl)` (`static_replay_worker.js:113`) — the S3 replay; no `/client/replay` pod path anywhere (grep: only comments/docs saying "never a pod"). |
| 4 Both name spaces | PASS | Agents see aliases only: `observationJson` (`sim.nim:743-782`), prompts (`llm.nim:174-282` use `sim.names`), `welcome`/`final` (`server.nim:406-414`, `:183-198`). Viewer maps to policy names: `broadcast.nim:47-78` carries `alias` AND `policies`/`pol`; scorebug headline uses the policy (`chrome_common.js:139,145`). Asserted `test_broadcast.nim:79-80`. |
| 5 Degrade-never-hang | PASS | LLM batch bounded by `llmTimeoutSeconds=25` (`llm.nim:466`); retry once; connect wait bounded by `playerConnectTimeoutSeconds=180` (`server.nim:235-241`); play deadline `0.6×timeout` checked between generations WITH a `2·25+6 s` reserve (`server.nim:272-300`), so the settle lands inside 720 s of 1200; no wait on seat replies (prompts are async); artifact writes bounded (curl 60 s); grace 20 s then `quit(0)`. Worst case ≈ 180 + 10×(50+6) + settle < 720. One parallel batch per generation (`curly.makeRequests`, `llm.nim:464-466`), asserted `test_llm.nim:173-186` — no sequential calls. |
| 6 num_agents | PASS | `num_agents: 3` in `standard`, `harsh-spring`, `certification.game_config`, and the config schema (min=max=3); asserted `test_manifest.nim:49-64`. `docker_smoke.sh` enforces all four invariants (missing/non-int num_agents, cert.players length, fixture players length, SMOKE_SEATS cross-check — `seats_expected="${SMOKE_SEATS:-3}"` is the independent in-file declaration). Smoke log of run 32641507840: `grep -c "SEAT-COUNT FAIL"` = **0**; `seats=3`, `smoke OK … reason=complete`. |
| 7 Scripted baseline full episodes | PASS | `test_replay.nim:18,76-78`: all-steward episode, `ending == "ten_generations"` (set only by `finish("complete", …)`, so reason is `complete`); `test_baseline.nim`: 12 seeds × steward AND opportunist, every doctrine field in range on every generation, every position/energy/cap invariant on EVERY tick, <1 ms per decision; `test_feasibility.nim` gate (a): 12/12 seeds reach generation 10 with population bounds (close AND per-generation means). Constants tuned by the oracle (design-note shipped-constants table), not guessed. |
| 8 LLM reply handling | PASS | Tolerant parse (`extractJsonObject`, fenced/prose; numeric strings/floats; inlined doctrine) `llm.nim:286-297,360-393`; retry once with hint (`:416-419,461`); terminal fallback `dsFallback` for: transport error, non-2xx, refusal, max_tokens-before-`{`, unparseable, missing field, retry exhaustion (`:490-494`), 429 (`:478-489`, executed), 401/403 disable (`:339-343` → next-gen pre-fill re-stamps `dsFallback`, `:454-460`), never-connected (`server.nim:305-312,326-328`). Every path leaves a legal steward doctrine with an honest source tag. `test_llm.nim` covers each mode incl. the new live-transport 429 test. |
| 9 Rune-safe truncation | PASS | `cleanText` runeSubStr (`llm.nim:118-131`); prompt cap runeSubStr (`server.nim:455-456`). `test_replay.nim:252-301`: 2-byte and 4-byte runes exactly at the 64/400 caps and one over; validateUtf8 == -1 on the cut strings AND on the full replay bytes carrying them. |
| 10 Manifest validates | PASS | `game.docs` = readme(type text, value) + pages[{id,title,content{type text,value}}] (verified by direct JSON inspection; rules.md + policies.md non-empty); `game.protocols` carries both `player` and `global`. Asserted `test_manifest.nim` (docs, protocols, `episode_timeout_minutes` top-level, `ANTHROPIC_API_KEY_URI` in runnable.env). |
| 11 Viewer legible at 360 px | PASS | `client/replay_broadcast.html:890-902`: `.plate .plate-name { … flex: 1 1 auto; min-width: 3.2em; }`; `:922-927` `@media (max-width: 640px)` hides `.lives-label`, `.plate-sub`, `.momentum-label`. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: build (:153) → certify (:167) → upload-policies (:206, comment pins BEFORE upload-coworld) → upload-coworld (:304) → secret put (:342, "AFTER upload-coworld"); all three workflows present; `docker_smoke.sh` 100755; `policies.json`: 4 distinct policies — 2 `PLAYER_PROMPT` champions (`ecos-keeper`, `ecos-bloom`) + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; placeholder grep over the five files: **no matches** (exit 1). |
| 13 Viewer executes | PASS | (i) wasm-viewer job 97199516259 of run 32641507840 on this sha: success, `needs: docker-smoke` (ci.yml), no `continue-on-error` anywhere in the workflows, loads the docker-smoke replay; log: `{"loaded":true,…,"clock":"GEN 5 / 6 TICK 241 OF 360",…}` and `soak: 10s of playback kept advancing ("0 / 360" -> "193 / 360" -> "241 / 360")`. (ii) `static_replay.js:141` sets `data-replay-loaded` on the worker's `loaded` message; `:19` sets `data-replay-error` in `showFailure` — both its own code paths. (iii) `replay-viewer/config.nims` has NO `MODULARIZE`/`EXPORT_NAME`; worker bootstraps `Module.onRuntimeInitialized` + `importScripts` (`static_replay_worker.js:162,210`) — the matched non-MODULARIZE pair, identical to the coworld-ctf starter (`starters/coworld-ctf/replay-viewer/static_replay_worker.js:166`, starter config.nims also MODULARIZE-free). |
| Simultaneous batch | PASS | One `RequestBatch` per generation carrying all open seats, `curly.makeRequests` (`llm.nim:402-421,464-466`); asserted `test_llm.nim` (`batch.len == open.len`). |

**Design-note divergence check:** repo copy vs run copy differ only in four documented
"Shipped deviation" blocks (shipped constants table with gate measurements; cert fixture
6×60/`minTurnSeconds:0` with the soak-gate rationale; `frames.len == ticksPlayed + 1` schema
correction; `generations` = scored, r2-F4). Each is justified, measured, and localized; the run
copy is untouched. No unjustified divergence.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `c3f4ed5`, new decideAll-level 429 test, fails-before/passes-after | code + test at head; executed green; reverted hunk → exact claimed failure ("saw llm") | yes |
| F2 | fixed, `9eea729`, collapse score-lock test, 5.938842 vs 6.447305 before | code + test at head; executed green; reverted hunk → exact claimed failure incl. both numbers, seed 1 tick 317 | yes |
| F3 | no change; used as F2 oracle | `test_replay.nim:193-204` reads the `end` row; correct not to change display source | yes |
| F4 | docs-only, `402792b`, run copy untouched | commit touches note + manifest schema only; run copy clean per diff | yes |
| F5 | fixed, `787b916` | `server.nim:305-312,326-328`; no test (loop body needs live server — decideAll layer covered); acceptable | yes |
| F6 | fixed, `6753cec`, guard | `server.nim:506-508`; nothing on shipped path changes | yes |
| F7 | fixed, `2c043fc`, `mt` not `mx` | `replay_broadcast.html:2330-2342`; `mx` untouched | yes |
| F8 | fixed, `adbd90a`, second pass | `global.nim:407-421`; same ids/bound, priority inverted | yes |
| CI | run 32641507840 success on pushed head | verified via `gh run list`/`view`: sha, conclusion, all three jobs, logs | yes |

## Non-blocking observations (judge's own, no checklist item)

- `results.win` on a forfeit is `[true,true,true]` (all tie at 0.0) and the end-card reports a
  draw — internally consistent, but "win" on a forfeited episode may read oddly to the platform.
- `ecos_player.nim`'s read loop relies on the game's socket close (or the `final` frame) to exit;
  the game never waits on the player, so the episode always settles, and the platform tears the
  pod down after results.json — acceptable, noted for completeness.
- The r1-verdict's two named fixes (throttle write-through, collapse flush) are exactly what
  r2-F1/F2 re-confirmed and what `c3f4ed5`/`9eea729` shipped; the loop converged.

BLOCKING: 0
