blocking: 0

# r1 verdict — sokoban

Head: `a72dbac2f84fce4c58ec9402ac299c3d42abc700` (main; CI run **33247581241**, conclusion `success`, jobs `test`/`docker-smoke`/`wasm-viewer` all green — verified via `gh run view`, not accepted)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-batch rule)
Reviews judged: `r1-review.md` (F1–F19, written at `464b2ab`) and `r1-review-b.md` (B-F1–B-F22, same sha)
Independent read written before reading either review: **yes** (clone → checklist → design note → full source/CI/manifest trace, notes below)
Fixer reports (`r1-fixes.md`, `r1-fixes-b.md`) **not read before this verdict** — per the brief. Every disposition below was verified directly from the code at head and the commit log, never from a fixer claim.
History quirk acknowledged and not counted: main carries a duplicated replay of the first fix series (REST-API commit replay); the tip tree is authoritative and I judged the tip tree.

## Standing blocking findings

None. Every finding from both reviews is either **fixed at the current head** (dismissed as no-longer-reproducible, fixing commit named) or **tied to no checklist item** (design-note divergence, recorded as non-blocking observation). My own independent checklist pass (below) found no additional blocking finding.

## Refuted / dismissed — review A (F1–F19)

### F1 — `last_turn.dropped` hard-coded 0 → FIXED at head
- Evidence: `src/sokoban/sim.nim:430` — `dropped: sim.turnDropped` (set from `directive.dropped + directive.overCap` at `sim.nim:293`). Fixed by `923aa67` (replayed `1dd3edb`).

### F2 — settle zeroed the in-play level's earned progress → FIXED at head
- Evidence: `src/sokoban/sim.nim:683-692` — only levels **past** `levelIndex` are zeroed (`for i in sim.levelIndex + 1 ..< sim.levels.len`); the level in play keeps its real moves/turns/pushes/crates and is recorded `outofsteps`, with the rationale in the doc comment (`:678-682`). Fixed by `e5c61b1`/`7da6c2e`.

### F3 — provider reply byte-sliced before parsing → FIXED at head
- Evidence: `src/sokoban/llm.nim:201,212` — both cuts are now `truncateUtf8Bytes`, which backs off UTF-8 continuation bytes to the nearest rune boundary (`sim_types.nim:195-210`); test "the 4096-byte provider cap cuts on a rune boundary, not a byte" at `tests/test_sokoban_baselines.nim:200`. Fixed by `4929332`/`3c3d3fb`.

### F4 — `actionsDropped` double-counted `repliesRepaired` entries → FIXED at head
- Evidence: `src/sokoban/sim.nim:302-304` — `actionsDropped += directive.overCap` and `repliesRepaired += directive.dropped`: disjoint, per the note. Fixed by `f8dbcb5`/`212ebea`.

### F5 — `"throttled"` an eighth fallback cause → FIXED at head
- Evidence: `src/sokoban/decide.nim:286-293` — a 429 ("llm throttled") now records `lastCause = "transport_error"`, with the closed-set rationale in the comment. Fixed by `cfe9d10`/`edefc8a`.

### F6 — `baselineNodeCap` 8 vs the note's 20 000 → NOT A CHECKLIST ITEM (dismissed)
- Checklist item 7 requires only that the parameters were "tuned with a grid harness, not guessed". They were: `tools/tune_baselines.nim` is a real sweep over `nodeCap ∈ {8..20000} × greedyMatch × tieOnH`; `tools/ci/baseline_tuning.json` records the pick (8, with per-tier rates 0.6875/0.375/0.0625); `tests/test_sokoban_events.nim:205-224` asserts shipped defaults equal it. `search.nim:31-36` documents that 20 000 measured 1.00/1.00/0.99 — the superhuman floor the note's own test 25 forbids. The note is stale; the repo is coherent. Non-blocking.

### F7 — relaxed fallback picked deepest, not closest-to-`bandMin` → FIXED at head
- Evidence: `src/sokoban/levelgen.nim:301-316` — `let distance = abs(bfs.reached - bandMin); if distance < bestDistance: …`. Fixed by `7843231`; the follow-on `a72dbac` (B-F20) also draws the relaxed player cell from the winning attempt's own hash stream (`:326-330`).

### F8 — provenance script did not run against the starter → FIXED at head, and I re-ran it
- Evidence: `scripts/build_broadcast_page.py:47` records `STARTER_SHA = a7484eb…`; the endcard-header anchor is now shape-matched (`swap_re`, `:70-84,234-239`). **I executed the documented command myself**: `git -C /workspace/starters/coworld-ctf show a7484eb:client/replay_broadcast.html` → script → `diff` against `client/replay_broadcast.html` is **empty** (byte-identical, 175 088 bytes). Fixed by `6291c9f`/`5e2d6a3`.

### F9 — `--strict-text-bounds` measured zero strings on both steps → FIXED at head
- Evidence: `tools/ci/renderer_fixture.html` now mirrors every laid-out line into a **main-thread 2D canvas** (`getContext('2d')`/`fillText`, asserted at `tests/test_sokoban_viewer.nim:313-315`), asserts its own 140-rune `say` survived full-length (`:72` `Array.from(SAY).slice(0, 140)`, `:298` "was shortened to"), and runs only after `data-replay-loaded` (`f31307a`). CI evidence at head, job 99087794666 "Drive the shipped chrome with a worst-case frame": `canvas text: 25 drawn, 0 never inside the canvas, 0 ellipsized (--strict-text-bounds)`. The bundle step's `total: 0` (worker OffscreenCanvas) is exactly the case the checklist says the fixture exists for, and the fixture now covers it. Fixed by `c9f9d4d` + `f31307a`.

### F10 — files the note names that are absent → NOT A CHECKLIST ITEM (dismissed)
- No checklist item requires `tests/shard_*.nim`, `test_sokoban_tuning.nim`, `roster.nim`, `flake.nix`, etc. Every behaviour those files were to carry is present elsewhere and cited (endcard labels in `test_sokoban_viewer.nim:254-281`, tuning in `test_sokoban_events.nim:205-224`, `seatAlias`/`ladderResultsJson` in `sim.nim`). `ci.yml:115-150` runs every `tests/*.nim` in debug **and** release, so no shard machinery is needed. Additionally `tools/wasm_replay_smoke.cjs` is now **wired into CI** ("Run the emitted wasm module headlessly", `ci.yml:332-341`; log: "ok: loaded replay.json, advanced 300 frames"). Non-blocking.

### F11 — sweep sizes / widened band / no-float grep missing `/` → partially FIXED, remainder NOT A CHECKLIST ITEM
- The `/` grep is fixed: `dee96a4`/`10ae39c` (test 12 now rejects `/` too). Sweep sizes (8/2 seeds) and the widened strength band are declared in-file divergences from the note, present since the initial test commit — nothing was loosened during the run (item 1 evidence below). Non-blocking.

### F12 — replay codec a rewrite, unchecked enum reads → enum reads FIXED; "rewrite" NOT A CHECKLIST ITEM
- Evidence: `src/sokoban/replays.nim:128-136` — `readEnumU8` raises `SokobanError` on out-of-range bytes; used for record kind, tier, plan source, action kind and direction (`:248-278`); tests "every byte-to-enum read is range-checked" and "a truncated replay raises SokobanError" at `tests/test_sokoban_replay.nim:132-155`. Fixed by `05ecd4c`/`3082bec`. The codec being new rather than the starter's is a note-vs-code divergence the note itself made incoherent (it demands level/plan records the starter format has no place for); checklist item 2 is what matters and it passes (below).

### F13 — tier-2 stream emitted 3 of 11 kinds → FIXED at head
- Evidence: `src/sokoban/server.nim` now has exactly 11 `log.add(se…)` call sites covering `seLevelStart, seTurnStart, seDirective, seFallback, seMove, sePush, seBoxOn, seBoxOff, seDeadlock, seSolved, seFailed` (verified by grep, sorted set matches the declared enum). Fixed by `0f60d90`/`3c9ffa3` (+ the `let`-binding fix `14fd919` that CI run 33245823236 caught red and `f31307a`'s series turned green).

### F14 — cadence 12 ticks/s, speeds [1,2,4,8], no interpolation → NOT A CHECKLIST ITEM (dismissed)
- The checklist requires the soak to observe real advancement, which it does (log: `soak: 10s of playback kept advancing ("0 / 430" -> "96 / 430" -> "120 / 430")` — 12 ticks/s, replay 430 ticks ≈ 36 s > 10 s soak). Review B's trace even shows the inherited `chrome_common.js` speed map cannot express 0.5×, so the shipped set is forced by the byte-pinned chrome. Note-only. Non-blocking.

### F15 — deadlock flash was banner+feed only → FIXED at head
- Evidence: `client/sokoban_block.html:299-300,522-526` — `deadFlash` state, `FLASH_TICKS = 24` (two flashes of six ticks), red ring (`strokeStyle = '#e0523a'`) drawn on the inset, cleared on seek (`if (jumped) { deadFlash = null; }`); asserted at `tests/test_sokoban_viewer.nim:330-340`. Fixed by `92a91fc`/`339145a`.

### F16 — `results.names` carried the policy label → FIXED at head
- Evidence: `src/sokoban/server.nim:588-593` — registration's `name` field is honoured (`registeredName` → `shared.names[slot]`), and `:526-527` picks up a `?name=` socket query param via mummy's `queryParams` accessor; the policy label remains only the fallback when no name was ever declared. Fixed by `1da5c62`+`9c1ab66` (replayed `4a37ae4`+`eb7cbe9`). Checklist item 4 passed both before and after (two name spaces existed; what changed is which real name fills the spectator side).

### F17 — `game.docs` was `"type":"uri"` → FIXED at head
- Evidence: `coworld_manifest_template.json` — `game.docs.readme` is `{"type":"text","value":"# cogame-sokoban…"}` (full markdown embedded) and all three `pages[].content` are `{"type":"text",…}` (parsed the manifest; page ids `rules.md`/`actions.md`/`levels.md`). Now literally the checklist item 10 shape. Fixed by `7a5c370`/`ce84515`.

### F18 — `do` accepted `move`/`seq`/`go`/empty → FIXED at head
- Evidence: `src/sokoban/directives.nim:143-148` — `case doText of "moves" / "push" / "goto" / "wait"` else drop; an absent `do` is now a dropped entry, not an invented `wait`; test "`do` is exactly the four declared verbs, and an absent one DROPS" at `tests/test_sokoban_baselines.nim:145`. Fixed by `09129e5`/`ee3dfba`.

### F19 — settle/finishEpisode outside the fault guard → FIXED at head
- Evidence: `src/sokoban/server.nim:381-397` — `writer.writeStop` / `gameSim.settle` / `finishEpisode` are wrapped in their own `try/except CatchableError` so an artifact-write exception cannot take the game thread down; test "the settle and the artifact write sit INSIDE the fault guard" at `tests/test_sokoban_engine.nim:158`. Fixed by `4d2d685`/`2c19f67`.

## Refuted / dismissed — review B (B-F1–B-F22)

### B-F1 (= A-F1) → FIXED (`sim.nim:430`, see above).

### B-F2 — broadcast `fallback` event carried a constant cause → FIXED at head
- Evidence: `src/sokoban/sim.nim:318-327` — the event now carries `sim.pendingFallbackCause` (fed by the turn's `fallback` chat record through `noteChatRecord`, identical live and at playback); the feed line appends the cause. Fixed by `c50a0ae`.

### B-F3 (= A-F5) → FIXED (`decide.nim:286-293`).

### B-F4 — `turnBudgetMs` gated attempt starts, worst turn 11.6 s → FIXED at head (and was never a hang)
- Evidence: `src/sokoban/decide.nim:149-156,233-234` — the decision deadline now starts **after** the spacing sleep with the invariant documented, and the budget guard reserves `2 × (ceil(turnBudgetMs) + ceil(turnSpacingMs))` (`:188-196`), i.e. the real worst case; pinned by the added engine test ("the guard reserves the rate floor as well as the decision budget", `tests/test_sokoban_engine.nim:224`). Even the reviewer's own trace conceded every wait was bounded and the 690 s stop held the 60 % window. Fixed by `01adc41`.

### B-F5 — server does not "refuse to start" on an unregistered joined seat → NOT A CHECKLIST ITEM (dismissed)
- The design note contradicts itself (§named edits 2 "refuses to start" vs §Decisions "a silent seat does not end the episode; the ladder runs to its natural end"). The code follows the second, logs an ERROR, seats `pusher`, sets `deadSeats`, declares the closed-schema player failure (`server.nim:236-263`) — which is also what checklist item 5 (degrade-never-hang) wants. No checklist item requires refusing to start. Non-blocking.

### B-F6 — `.tiny` inset did not ride `var(--band)` → FIXED at head
- Evidence: `client/sokoban_block.html:269` — `#stage.tiny #fpv { left: calc(4 * var(--u)); bottom: calc(var(--band, 0px) + 22 * var(--u)); }`; the non-tiny rules too (`#fpv { bottom: calc(var(--band, 0px)…`, `#killfeed { bottom: calc(var(--band, 0px)…`), and the Nim test now walks **every** `bottom: calc(` in the block asserting a `var(--band` term (`tests/test_sokoban_viewer.nim:160-172`); `tools/ci/renderer_fixture.html` measures rendered rects against `#transport` itself (`:173`). Fixed by `f356da2` + `3adc9d3`.

### B-F7 — `.tiny` inset collided with ribbon/pips → FIXED at head
- Evidence: same rules — inset spans `--band`+22u … `--band`+106u; pips sit at `--band`+112u, ribbon at `--band`+124u, all measured from the same origin now, so the stack cannot cross. Fixed by `3adc9d3`.

### B-F8 — full-cap `say` on a `nowrap` feed row → FIXED at head
- Evidence: `client/sokoban_block.html:154-159` — `#killfeed .feed-row.say { white-space: normal; … }` with a reserved wrap column sized from `MaxSayRunes` (test asserts `#killfeed .feed-row.say`, `white-space: normal;` and the literal `MaxSayRunes` in the block, `tests/test_sokoban_viewer.nim:283-293`); the `bad`/`good` rows are styled too (`78c5553`). The fixture then renders a full-cap say at 360 px and the strict gate measures it (25 drawn / 0 outside at head). Fixed by `c9f9d4d` + `78c5553`.

### B-F9 (= A-F9) → FIXED (fixture mirrors to a main-thread canvas, asserts full-length strings, `25 drawn, 0 never inside` at head).

### B-F10 — smoke never failed on `fault` → FIXED at head
- Evidence: `.github/workflows/ci.yml:205-223` — new step "Assert the smoke episode did not fault" parses `dist/smoke/results.json` and exits non-zero on `reason == "fault"` or `endRule == "fault"` (and on any reason outside `{complete, deadline}`), kept in the workflow so the shared `docker_smoke.sh` stays template-identical. Fixed by `2c7aec6`.

### B-F11 — `wasm_replay_smoke.cjs` / `page_smoke.mjs` unwired → FIXED (the half that mattered)
- Evidence: `ci.yml:332-341` "Run the emitted wasm module headlessly" runs `node tools/wasm_replay_smoke.cjs dist/static-replay-viewer "${replay}" 300` before the Playwright steps; head log: `ok: loaded replay.json, advanced 300 frames (3627422 packet bytes, heap 16 MB)`. Fixed by `8885041`. `page_smoke.mjs` remains a documented developer tool (README §Building and testing); no checklist item requires it in CI. Non-blocking residue only.

### B-F12 — CI does not re-run the tuning sweep → NOT A CHECKLIST ITEM (dismissed)
- Verified at head: `grep tune_baselines .github/workflows/ci.yml` still empty. Checklist item 7's sentence is "tuned with a grid harness, not guessed" — satisfied (see F6 above): the harness is committed, its pick recorded, the shipped defaults asserted equal to it, and an independent re-measurement runs in `test_sokoban_baselines.nim` against the pinned band every CI run. The "`--check` in CI" sentence is the design note's, not the checklist's. Non-blocking.

### B-F13 — tests drive `helpers.runEpisode`, not `runGame` → FIXED where it diverged; remainder NOT A CHECKLIST ITEM
- Evidence: `e44b769` aligned the harness with the server's two real rules (stop record only when `reason != complete`, `server.nim:381-384`; end rule derived `ladderComplete`-else-`turnCap`, `:377-378`) — I read the diff and it **strengthens** the round-trip (the old harness exercised a byte shape the server never produces). The artifact path is exercised by the real binary in `docker-smoke` (results.json + 53 KB replay produced, `reason=complete`) and now gated on `fault` by B-F10's step. Checklist items 2 and 7 both pass on the shipped tests. Non-blocking residue: `runEpisode` remains a harness — no checklist item forbids that.

### B-F14 (= A-F11 sweep sizes) → NOT A CHECKLIST ITEM; nothing loosened during the run (item 1 evidence below).

### B-F15 — entrypoint docstring inverted the order → FIXED at head
- Evidence: `src/sokoban.nim:4-9` — the docstring now states the real order ("read the runner's config first, then randomise only if the runner did not pin a seed") with the why. Functionally immaterial before and after. Fixed by `1cb9416`.

### B-F16 — `plan` event fields differ from the note → NOT A CHECKLIST ITEM (dismissed)
- `pushes`/`blocked` are unknowable at `beginTurn` (the ticks have not run); the emitted set is coherent, the kinds-test passes, and no checklist item pins event fields. The per-turn outcome numbers reach spectators via the `directive` chat record and the feed. Non-blocking.

### B-F17 — private `notes` written into the replay bytes → FIXED at head
- Evidence: `src/sokoban/replays.nim:193-201` — `writer.body.addText("")`: the field stays in the byte layout, the seat's scratchpad never leaves the process; test "notes are never written into the bytes, and the format is unchanged" (`tests/test_sokoban_replay.nim:106-107`). Fixed by `eb31ee8`.

### B-F18 — `GET /client/replay` exists on the game server → REFUTED as a checklist violation
- Item 3's operative requirements all hold at head: manifest declares `game.replay_viewer = {"bundle": "static-replay-viewer"}` (parsed it), `tools/build_replay_viewer.sh` exists, is mode 100755 (`git ls-files -s`), and is the wired hook (`ci.yml:286-302`); the bundle's **only** network call is `fetch(message.replayUrl)` (`static_replay_worker.js:113` — one `fetch` in the whole bundle, zero `XMLHttpRequest`/`WebSocket`/`EventSource`). No `/client/replay` viewer is declared to the platform anywhere — the manifest has none and `coworld-release.yml` carries an explicit guard string against one. The local dev route (`server.nim`) is starter parity (`coworld-ctf/src/ctf/server.nim:631,646,844` does the same) and is not a "pod path" the platform can reach: nothing hosted ever loads it. Reading item 3's sentence as banning a local dev route would fail the starter itself. Dismissed.

### B-F19 (= A-F17) → FIXED (`game.docs` is `"type":"text"` throughout).

### B-F20 — relaxed pick + attempt-0 player draw → FIXED at head
- Evidence: `levelgen.nim:307-316` (closest-to-`bandMin`, fixed by `7843231`) and `:326-330` (player cell from the winning attempt's own hash stream — the head commit `a72dbac` itself).

### B-F21 — macros expand against a forward-advanced snapshot → NOT A CHECKLIST ITEM (dismissed)
- The reviewer's own trace shows the literal reading is unimplementable (a two-macro turn cannot walk both macros from the original cell) and that the note's actual invariant — expansion mirrors execution exactly, box indices are turn-start — holds (`driver.nim:104-127`). The driver-legality tests pass. Non-blocking.

### B-F22 — records-exhausted replay invented ticks → FIXED at head
- Evidence: `src/sokoban/replay_runtime.nim:124-135` — when the records run out with the turn fully played, playback settles `endComplete` with the end rule derived the server's way (`ladderComplete` if the ladder finished, else `turnCap`); the round-trip test now produces the **shipped** shape (`maxTurns = 3`, asserts `endRule == erTurnCap` and `records.allIt(it.kind != rkStop)`, `tests/test_sokoban_replay.nim:25-39`). Fixed by `c6dae61`.

## Checklist pass (independent — my own read, formed before opening the reviews)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | run 33247581241 `success` at `a72dbac` (jobs test/docker-smoke/wasm-viewer). Whole-history `git log -p -- tests/`: tests added in `3724a05`; later changes are additions plus two legitimate strengthenings — `e44b769` (harness parity with server stop-record/end-rule rules) and `c6dae61` (turnCap round-trip made to exercise the shipped no-stop-record shape, replacing a scenario that was a second copy of `ladderComplete`). No `skip`/`xfail`/deleted assertion/widened tolerance anywhere in the history. One mid-series red run (33245823236) was fixed forward, not masked. |
| 2 Replay re-derivation | **pass** | `tests/test_sokoban_replay.nim:18-52` (all four end rules, per-tick hash equality incl. stop tick), `:156-173` (determinism from bytes alone); viewer displays from the same re-derivation: `replay-viewer/sokoban_replay.nim` imports `sokoban/sim`, `advanceReplayFrame → stepReplay → sim.stepTick` with per-tick `checkReplayHash` (`replay_runtime.nim:145-149`); `"generateLevel" notin` runtime asserted. |
| 3 Static viewer | **pass** | manifest `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, wired at `ci.yml:286-302`; bundle's sole network call is the replay fetch (`static_replay_worker.js:113`); no `/client/replay` declared anywhere (see B-F18). |
| 4 Both name spaces | **pass** | `observationJson`'s `"you": seatAlias(seat)` (`sim.nim:611`), `showPlayerLabels` false, obs-leak test (`test_sokoban_obs.nim`); spectator side gets the registered real name (`server.nim:588-593`, `broadcast.nim`, plate in `sokoban_block.html`). |
| 5 Degrade-never-hang | **pass** | every wait bounded: lobby ≤ `lobbyJoinTimeoutTicks/24` (`server.nim:209-219`), register grace ≤ 4 s (`:221-230`), spacing ≤ 2.6 s, attempts 6 s + 3 s under a monotonic `turnBudgetMs` (`decide.nim:240-267`), rolling-60 s cap 28, budget guard reserving spacing+budget (`:188-196`), wall-clock stop at loop top (`server.nim:289-294`, 690 s ≤ 720 s = 60 % of the manifest's `episode_timeout_minutes: 20`), tick loop bounded at 20 with `turnEnded` break, generator/search node caps. Smoke episode settled `complete` in ~24 s. |
| 6 num_agents | **pass** | `num_agents: 1` in both variants' `game_config` and `certification.game_config` (parsed manifest); never at variant top level; `docker_smoke.sh:106-150` enforces all four invariants + `SMOKE_SEATS` cross-check; **grep of the head docker-smoke log (job 99087631375) for `SEAT-COUNT FAIL`: 0 matches**; log shows `seats=1 … "num_agents": 1 … smoke OK … reason=complete`. |
| 7 Scripted baseline full episodes | **pass** | `test_sokoban_engine.nim:11-69` (all-scripted episode, `reason == endComplete`, six results identities), `test_sokoban_manifest.nim` plays every variant; legality bounds over both baselines (`test_sokoban_baselines.nim:35-105`); tuned by the committed grid sweep (`tools/tune_baselines.nim`, pick recorded in `baseline_tuning.json`, asserted equal at `test_sokoban_events.nim:205-224`). |
| 8 LLM reply handling | **pass** | `extractJsonObject` (`directives.nim:72-111`, balanced-brace, fence/prose-tolerant); retry exactly once (`while attempt < 2`, `decide.nim:240`); fallback = the `pusher` proc (`scriptedDirective(blPusher)`), recorded via `fallbackRecord` chat records + `results.fallbackTurns`; "will retry" vs "falling back" phrasings distinct. |
| 9 Rune-safe truncation | **pass** | single primitive `truncateRunes` at every cap; the one former byte slice is now `truncateUtf8Bytes` (rune-boundary backup, `sim_types.nim:195-210`); emoji-at-cap tests (`test_sokoban_baselines.nim:187-227`, `test_sokoban_replay.nim:175-208` strict-UTF-8 through `replay_summary.py`). |
| 10 Manifest validates | **pass** | `game.docs` readme + 3 pages all `{"type":"text","value":…}` (parsed); `game.protocols` carries **both** `player` and `global` as `{"type","value"}` objects; results/config schema pins asserted in `test_sokoban_manifest.nim`. |
| 11 Viewer legible at 360 px | **pass** | `client/replay_broadcast.html:2954-2960` `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }`; `:3203` `@media (max-width: 640px) { .solved-label, .sk-alias, .fl-cap { display: none; } }`. |
| 12 Release order and scaffold | **pass** | `coworld-release.yml`: build → certify (`--timeout-seconds 300`) → upload-policies → upload-coworld → secret put (steps at `:159/:174/:217/:319/:410`); all three workflows present; both scripts 100755; `policies.json` = 2 `PLAYER_PROMPT` champions (#2 carries `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) + 2 scripted fillers; placeholder grep for `<slug>|<IMAGE>|<SEATS>` over the five files: **no matches** (gate passes); surviving `<cow_id>/<sha>/<run_id>/<name>` are the documented residue. |
| 13 Viewer executes | **pass** | `wasm-viewer` green at head **including** "Load the bundle in a real browser" (job 99087794666: `{"loaded":true,"ms":355,…}`, `soak: 10s of playback kept advancing ("0 / 430" → "96 / 430" → "120 / 430")`, three distinct scrub readouts); `needs: docker-smoke`, no `continue-on-error`; both markers set from the shell's own paths (`static_replay.js:161` loaded-after-first-ingest, `:19-20` error); **no recorded lobby to dwell in** — hashes are written only inside the tick loop after `phase = phPlaying` (`server.nim`), `newSimFromReplay` starts `phPlaying`, `startTick = 0` **is** the game start and every seek clamps to it (`replay_runtime.nim:156-160,251-256`); link flags ↔ bootstrap are a matched pair from coworld-ctf (no `MODULARIZE`/`EXPORT_NAME` in `config.nims`; worker uses `Module.onRuntimeInitialized`, `static_replay_worker.js:188`); plus the emitted module runs headlessly in node (300 frames). |
| 14 Chrome is the starter's | **pass** | `chrome_common.js` **byte-identical** (sha256 `7ace7287…72f7c`, 40 022 B — I hashed both); `replay_broadcast.html` **mechanically reproduced**: I ran `scripts/build_broadcast_page.py` against starter sha `a7484eb` and the output is byte-identical to the shipped page; every removal is a named design-note removal (`#viewpanel`/zoom/minimap/povBadge/fpv-hp/gear/map/raycaster/ec-heart/ctf beat CSS); transport rules (a)–(d) verified: `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement`, all bottom-anchored block elements ride `var(--band)` (walked every `bottom: calc(` in the block), `#endcard { bottom: var(--band, 0px) }` shown via `.on` and dismissed on every seek, beats are labelled `<button>`s built by `skBeat` seeking `ctx.send('s:'+tick)` with CSS for exactly the seven emitted kinds; `#viewpanel` removed (markup, CSS, wiring, ids) as a fixed 10×10 arena requires. |
| 15 Every drawn string fits | **pass** | bundle step: `never_inside: 0` with `--strict-text-bounds` (total 0 = worker canvas, which is precisely why the fixture exists); fixture step (own `ci.yml` step, `--strict-text-bounds`): **`canvas text: 25 drawn, 0 never inside, 0 ellipsized`** at head — the fixture loads the shipped `index.html`, drives a full-cap 140-rune say / deadlock banner / all pip states at several widths incl. 360 px, asserts its strings survived full-length, and mirrors each laid-out line into a main-thread 2D canvas the smoke can measure; the say row has a reserved wrapping band sized from `MaxSayRunes` (`sokoban_block.html:154-159`). |
| Simultaneous batch | **pass** (as applied: one seat's call per turn is the batch) | `decide.nim:256-267` — one request per turn posted through the starter's `makeRequests` batch path, at most one retry, never more than one in flight. |

## Non-blocking observations (mine, tied to no checklist item)

- `runEpisode` in `tests/helpers.nim` remains a parallel copy of the server loop; parity is now pinned for the two rules that diverged, but a future server change can still drift from it silently. The real loop is exercised only by `docker-smoke`.
- A `deadline`/`fault` settle marks the in-play level `outofsteps` even when its budget had moves left (`sim.nim:678-684`) — documented in-code, keeps earned progress, but `results.outOfSteps` can count a level whose steps did not literally run out.
- `tools/ci/page_smoke.mjs` is committed but CI-unwired (developer tool per README); `tune_baselines.nim --check` likewise not run in CI.
- The design note is stale against the repo in several deliberate, in-code-documented places (`baselineNodeCap` 8, 12 ticks/s cadence, speeds `[1,2,4,8]`, `CRATES` vocabulary, no shard files). A note refresh would spare the next reviewer this trace.

## Fixer report audit

Not performed before this verdict — the brief forbids opening `r1-fixes.md`/`r1-fixes-b.md` until the verdict is written. Every disposition above was established from the head tree, the commit log and the head CI run directly, so the verdict does not depend on any fixer claim.

BLOCKING: 0
