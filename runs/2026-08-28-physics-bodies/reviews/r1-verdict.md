blocking: 0

# r1 verdict — physics-bodies
Head: `52379767a323c604171f76353a94eb2fb0399816` (main)   Checklist: agent-notification ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision rider, verbatim from `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST)   Independent read written before reading fixes: **yes** — I read the design note, the tree at head, the CI logs of run `33177512252`, and `git log -p --since=2026-08-28T08:40:00Z -- tests/` before opening `r1-review.md`, and opened `r1-fixes.md` only after auditing the review against head.

The r1 review was written at `f6976bc5` and reported **0 blocking / 17 advisories**. At the current
head every advisory that touched behaviour has been fixed and test-pinned, one reviewer claim
(N16a) is factually wrong, and my own checklist pass finds nothing standing. **Blocking: 0.**

## Standing blocking findings

None. Every checklist item verified at head (table below); no reviewer finding falsifies a named
checklist item at `5237976`, and my independent pass surfaced no new one.

## Refuted

A finding that was true at `f6976bc` and is fixed at head is refuted *as standing*, per the
verify-at-current-head rule. One finding (N16a) was never true.

### N16(a) — "build artefacts committed: `replay-viewer/dist/nimcache/**` (≈70 generated `.c` files, committed in `c573490`)" → REFUTED (never true)
- Evidence at `5237976`: `git ls-tree -r HEAD --name-only | grep -c 'replay-viewer/dist'` = **0**;
  `git log --name-only c573490 --format= | grep -c nimcache` = **0**; `.gitignore:39` is
  `replay-viewer/dist/` and `git check-ignore -v replay-viewer/dist/nimcache/` confirms the ignore.
  The files the reviewer saw are untracked local build residue in a working tree that has run the
  emscripten build. The fixer's dispute is correct.

### N1 — LLM-text path not covered by any CI check → REFUTED at head (fixed, and the pre-fix state was worse than reviewed)
- `tools/ci/renderer_fixture.html:290-400` now *measures*: it replaces the `static_replay.js`
  script tag (so the real core cannot overwrite the shim), injects a full-cap 48-rune `say` and
  160-rune `note` on both seats, self-checks the rune counts (`:94-99`), and for every element
  containing the full string at 360/620/1280 px asserts a non-empty box, containment in every
  scroll box, no horizontal clip (`scrollWidth > clientWidth`) and no ellipsis;
  `data-replay-loaded` is set only after all six boxes pass. Verified in the `renderer-fixture`
  artifact of run `33177512252`: `"renderer fixture: three widths booted and MEASURED … 6 full-cap
  boxes, every one wholly inside its frame [w1280:note … w360:say … w620:say …]"`,
  `data_replay_error: null`, `loaded: true`.
- The board half (pixie-baked speech band — the only place a model's words are *drawn*) is measured
  by `tests/test_text_bounds.nim:1-110,184-211`: full-cap `say` on both seats through the real
  `buildSpriteProtocolUpdates`/`buildSpriteProtocolPlayerUpdates`, pixels read back, ink asserted
  inside the reserved plate at both scales; green twice (debug+release) in job `98869860056`.

### N2 — one missing seat holds the lobby for the whole 660 s budget → REFUTED at head (fixed)
- `src/bodies/sim.nim:505-520`: the `Lobby` branch of `step` latches `lobbyNoShowSeat` when
  `lobbyJoinTimedOut()` fires, and `sim_state.nim:28-29` (`lobbyIsStarting`) now admits
  `players.len >= minPlayers or sim.lobbyNoShowSeat >= 0`, so the round starts on the tick the
  budget expires — derived from `lobbyTicks` + recorded joins, hence replay-safe.
- Test-pinned: `tests/test_replay.nim:230-250` records a one-seat episode (`seatsJoined = 1`),
  asserts `lobbyNoShowSeat == 1`, `gameStartTick == lobbyJoinTimeoutTicks - 1`, and re-derives
  every hash; `tests/test_engine.nim` runs the real server loop one seat short. CI `test` log:
  `lobby budget expired with seat 1 missing; starting the match anyway` →
  `physics-bodies: seat 1 never registered; driving BUG-1 with pusher` → `complete/full_time`.

### N8 — "ten disc pairs" wrong + dead skip branch → REFUTED at head (fixed, `2d90ef0`)
- `src/bodies/sim.nim:195-212` uses derived `DiscPairCount` (25) with the corrected doc in all five
  places; the no-op `if …: discard` branch is gone. Golden-hash fixture unchanged and green — proof
  the branch was dead.

### N9 — two test bounds weaker than §Tests 4 → REFUTED at head (tightened, `c729c34`/`e0f2c8d`)
- `tests/test_control.nim:382-395`: `stopped <= 240` → `stopped <= 132` (measured 121 + ~9 %).
- `:170-211`: a new 10 000-rollout block keeps the full ±2.9 m/s inherited velocity from the inner
  half of the ring, any stance, aggression ≤ 9, asserting **0** crossings. The from-rest zeroing in
  the original block dates to the fork commit and was never weakened during the run — item 1 is not
  touched, and the tightening is the opposite of loosening.

### N10 — `complete/match_won` re-derivation not separately pinned → REFUTED at head (fixed, `ce7675c`)
- `tests/test_replay.nim:50-70`: `roundsToClinch = 1` episode, asserted `complete/match_won`,
  re-derived hash-by-hash.

### N12 — `round` records all stamped with the final tick → REFUTED at head (fixed, `3e4ecbb`)
- `src/bodies/server.nim:609` (`template flushRoundRecords`) called at `:644`, `:838`, `:938` —
  after every hashed step, after the wall-clock stop's extra tick, and once in the artifact block;
  `tests/test_replay.nim` asserts strictly-ascending stamps and that the first is not the last tick.

### N13 — lull map always empty, skip-lulls inert → REFUTED at head (fixed, `15eeede`)
- The lull scan now reads the same `BeatKinds` list as the scrubber; `tests/test_replay.nim:272-310`
  asserts a recorded episode yields ≥ 1 span, each clearing `MinLullTicks` with `LullLeadTicks` of
  context. The `wasm-viewer` soak readout at head shows the ffwd chip live (`0:11 ▸▸ …`).

### N14 — speech bubbles persist until replaced → REFUTED at head (fixed, `a268e5a`)
- `src/bodies/global.nim:78` `BubbleHoldTicks* = 60` (2.5 s), applied at `:1119`;
  `tests/test_text_bounds.nim:188-211` asserts placed-when-young, gone at `BubbleHoldTicks + 1`,
  and that the reserved band does not move.

### N17(b) — per-turn budget was a pre-check, worst case ~20 s → REFUTED at head (fixed, `1920221`)
- `src/bodies/decide.nim:184-189`: each attempt's deadline is
  `max(1000, min(configured, turnBudgetMs − spent))`; `tests/test_engine.nim:268-290` sets both
  attempt deadlines larger than a 4 000 ms budget against a hung provider and asserts the turn
  returns within budget + 1 500 ms with both seats commanded.

### Still true at head, and correctly non-blocking (verified, no checklist item)
N3 (rim-guard look-ahead + thrust floor — now documented in `docs/ORDERS.md`), N4 (design-note
`chargeLeadTicks`/`liftEngageUm` values stale; shipped defaults equal `tools/ci/baseline_tuning.json`'s
recorded `pick`, pinned by `tests/test_tuning.nim`), N5 (rest floor `RestFloorUm = 64`, hashed both
sides, now in `docs/RULES.md`), N6 (contact-torque Q12 scaling, saturates the ±450 clamp either way,
documented at the call site), N7 (`contacts` = contact ticks per body, documented in
`docs/PROTOCOL.md` and the manifest), N11 (CLI manifest validation lives in
`coworld-release.yml:164` — a CI step; the Nim `test` job has no Python CLI to call), N15
(`#pb-ring` inside `#scorebug`, both readouts on screen — CI scorebug readout shows
`ROUND CLOCK ROUND 2 OF 4 · RING 3.00 M`; pinned in `tests/test_viewer.nim:97-102`), N16(b)
(`--preload-file client/art` is a third, necessary, now-documented `config.nims` change —
`global.nim:447` reads `client/art/walls/wall_v.jpg` under MEMFS), N17(a,c,d,e) (note drifts;
code correct; (e) documented at `sim.nim:529-537`).

## Checklist pass (independent)

| item | status | evidence (path:line or run/job id) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | `gh run list`: run `33177512252`, `ci.yml`, branch `main`, headSha `52379767…`, conclusion **success**; jobs `test`/`docker-smoke`/`wasm-viewer` all success. `git log -p --since=2026-08-28T08:40:00Z -- tests/`: every hunk read — additions only; the one bound change (`test_control.nim` 240→132, `e0f2c8d`) is a tightening; no skip/xfail/`when false`, no deleted assertion, no test file removed. The duplicated N1–N17 commit series (`e91d2d6..3ebd10e`) nets to zero on `tests/` (`git diff 8943270 HEAD -- tests/` is empty). Job `98869860056` ran all 17 suites debug+release (perf/baselines release-only, per `NIM_TESTS_RELEASE_ONLY`). |
| 2 Replay re-derivation | **pass** | `tests/test_replay.nim:15-27` (`rederive` = `initReplayRuntime` + `stepReplay`, every recorded hash checked) for `complete/match_won` (`:50-70`), `complete/full_time`, `deadline/wall_clock`, `fault/sim_fault`, and the partial-lobby episode (`:230-250`); the viewer runs the identical runtime (`replay-viewer/bodies_replay.nim:43,56,103` → `initReplayRuntime`/`advanceReplayFrame`/`buildReplayViewerPacket`). |
| 3 Static viewer | **pass** | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, wired in `ci.yml` and `coworld-release.yml`; no `/client/replay` viewer declaration in the manifest (the string appears only in the server-routes doc and a release-workflow guard *against* it); `static_replay_worker.js:113` — the only network call is `fetch(message.replayUrl)`. |
| 4 Both name spaces | **pass** | `tests/test_observation.nim:68-151`: observation and player-stream labels carry `BUG-1`/`BUG-2` only, no real name; chrome roster, endcard and `results.names` carry the real names. |
| 5 Degrade-never-hang | **pass** | `decide.nim:184-205` (attempt deadlines clamped to `turnBudgetMs`), `:158-161` (bounded inter-batch sleep), `sim_config.nim:108` (`wallClockBudgetSeconds` clamped ≤ 720 = 60 % of 1200; default 660), `server.nim:628-641` (engine stop writes the load-bearing `stop`, settles and scores), `sim.nim:505-520` (lobby no-show starts the match), `server.nim:484-495` (frame limiter bounded). No unbounded loop or blocking read found in the game loop, decision layer or replay runtime. |
| 6 `num_agents` | **pass** | `num_agents: 2` in `variants[default].game_config`, `variants[blitz].game_config`, `certification.game_config` (parsed from the JSON); `tools/ci/docker_smoke.sh:106-149` enforces all four invariants (present / positive int / `len(certification.players)` / `len(game_config.players)`) plus the independent `SMOKE_SEATS` cross-check; `ci.yml` sets `SMOKE_SEATS: "2"`. `grep -c 'SEAT-COUNT FAIL'` over the full docker-smoke log (job `98869859801`) = **0**; log shows `seats=2` and the fixture config. |
| 7 Scripted baseline full episodes | **pass** | `tests/test_replay.nim:37-40` (`endReason == ReasonComplete` on all-scripted episodes, incl. one-seat case); `tests/test_baselines.nim` (500 states × both baselines validate against the reply schema, byte in range; 20-seed sweep, 0 faults); tuned by `tools/tune_baselines.nim` grid, pick recorded in `tools/ci/baseline_tuning.json` (`measured: pusherWins 20/20, ringOuts 61/67 rounds`), equality pinned by `tests/test_tuning.nim:18`. |
| 8 LLM reply handling | **pass** | `intents.nim:97-136` (`extractJsonObject`, fence/prose tolerant) + `:207-289` (repair table); `decide.nim:168` (`attempt < 2` — exactly one retry), `:234-240` (throttle skips the retry), `:243-254` (fallback installs `pusher`, `fallbackRecord` written with cause, `falling back` log phrase for phase 60). |
| 9 Rune-safe truncation | **pass** | `intents.nim:68-95` (`truncateRunes` via `runeLen`/`runeSubStr`; `sanitizeSay`); `tests/test_intents.nim:103-115` — 4-byte emoji on the 48-rune boundary, output asserted valid UTF-8 and cap-exact; `tests/test_replay.nim` re-checks a recorded `say` with `validateUtf8`. |
| 10 Manifest validates | **pass** | Parsed the JSON: `game.docs.readme = {type:"text", value: 6250 chars}`, `pages` = 3 × `{id,title,content:{type:"text",value}}`; `game.protocols` carries both `player` and `global` as objects. `tests/test_manifest.nim` asserts the shapes; CLI validation runs in `coworld-release.yml:164`. |
| 11 Viewer legible at 360 px | **pass** | `client/replay_broadcast.html:2720-2726` — `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }`; labels hidden under 640 px: `@media (max-width: 640px)` at `:2850` plus `#stage.tiny` (`boardW <= 620`, `:2656`) hiding `#pb-legend`/`.pb-lbl` (`:2848-2849`). |
| 12 Release order and scaffold | **pass** | `coworld-release.yml`: Build the Coworld manifest (`:198`) → Certify locally (`:212`) → **Upload the policies** (`:255`) → Upload the Coworld (`:353`) → Put the Coworld secret (`:449`). All three workflows present; `tools/ci/docker_smoke.sh` mode 100755; `tools/ci/policies.json` = 4 policies (2 `PLAYER_PROMPT` champions, 2 `PLAYER_SCRIPTED` fillers), champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows + `docker_smoke.sh` + `policies.json` exits non-match (rc 1). ci.yml's docker-smoke builds the image in the same job before the smoke runs. |
| 13 Viewer executes | **pass** | (a) `wasm-viewer` job `98870401228` of run `33177512252` success; step "Load the bundle in a real browser": `{"loaded":true,"ms":1306,…}`, `soak: 12s of playback kept advancing ("0 / 1604" -> "391 / 1604" -> "488 / 1604")`, loading the replay docker-smoke produced; `needs: docker-smoke` (`ci.yml:219`); no `continue-on-error` anywhere in the workflows. (b) `static_replay.js:161` sets `data-replay-loaded` on the worker's first `loaded` message; `:20` sets `data-replay-error` in `showFailure`. (c) `replay_runtime.nim:33-40` walks the recorded lobby to the first `Playing` tick, sets `startTick = gameStartTick`, seeks there; every seek path clamps to `replayStartTick()` (`replays.nim:492,531,534,567,582`); a genuinely late gameStart is exercised — the partial-lobby replay starts at `lobbyJoinTimeoutTicks − 1` (t479 in the CI log) and re-derives. (d) `config.nims` diffed against the starter's: no `MODULARIZE`/`EXPORT_NAME`, same link flags + renames + the documented `--preload-file client/art`; worker is the starter's `var Module = {}` + `Module.onRuntimeInitialized` form (`static_replay_worker.js:8`). |
| 14 Chrome is the starter's | **pass** | (a) `sha256sum`: `client/chrome_common.js` ≡ `/workspace/starters/coworld-ctf/client/chrome_common.js` (`7ace7287…`), byte-identical. (b) `replay_broadcast.html` is the starter's page with the game block appended under the banner at `:2688`; the above-banner diff is the named removals (`#viewpanel`, `#fpv` + its ~1100-line raycast renderer, `#povBadge`) plus retarget copy (board 1920×1280, adapter name, plate copy "Hill"→"Rounds", locker-room caption) — the CSS above the banner is the starter's except the removed blocks; 161 KB vs 234 KB is the fpv/viewpanel removal, not a rewrite (the starter itself carries `class="team-name plate-name"` — that is not an edit). (c) `relayout()` sets `--hudscale`/`--band` on `:root` (`:2655,2661`); the one game overlay `#pb-legend` rides `bottom: calc(var(--band, 0px) + 8 * var(--u))` inside `#chrome` (`:2770`); `#endcard { bottom: var(--band, 0px) }` (`:743`), shows via `#endcard.on` (`:754`), taken down on every non-gameover frame (`:1656`); beats are labelled `<button class="beat-marker <kind>">` with `title`/`aria-label` that seek via `CTX.send('s:'+tick)` (`:2883-2896`), with one CSS rule per emitted kind (`:2808-2838`). (d) `#viewpanel` removed entirely (fixed arena). |
| 15 Every drawn string fits its frame | **pass** | Both smoke steps ran `--strict-text-bounds`; `canvas text: 0 drawn, 0 never inside … 0 ellipsized` — the 0 total is structural (`grep -rn fillText client/ replay-viewer/*.js` = 0 in every shipped JS; the only hits are pixie's `fillText` in untracked emcc build residue), and `ci.yml:328-350` documents it. The item's worst-case-fixture requirement is met: `tools/ci/renderer_fixture.html` loads the real `index.html` in iframes at 360/620/1280 px, drives full-cap `say`+`note` on both seats at once, self-checks its rune counts (`:94-99`), measures every full-cap box (empty/outside/clip/ellipsis ⇒ `data-replay-error` ⇒ red step), and runs under `viewer_smoke.mjs --strict-text-bounds` in its own step ("Drive the text path at full cap in the real bundle", job `98870401228`, `loaded:true`; artifact `renderer-fixture/viewer-smoke.json`: "6 full-cap boxes, every one wholly inside its frame"). The board band (the one drawn text surface) is reserved and measured in the drawing font by `tests/test_text_bounds.nim` (plate = reserved band, ink inside, full-cap both seats, both scales, dwell test), green in job `98869860056`. |
| rider — one parallel batch per turn | **pass** | `decide.nim:190-205`: one `RequestBatch` carrying all open seats per attempt, one `curly.makeRequests` call; `tests/test_engine.nim:180-205` asserts the two seats' in-flight windows intersect. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| N1 | fixed (fixture replaces script tag, measures; board half in `test_text_bounds`) | fixture measurement code at `renderer_fixture.html:290-400` requires full-string containment; artifact `viewer-smoke.json` shows 6 boxes measured inside frames, `loaded:true`, no error; `test_text_bounds` green debug+release | yes |
| N2 | fixed (latch in `step`, `lobbyIsStarting` admits it, real-server test) | `sim.nim:505-520`, `sim_state.nim:28-29`; CI log lines `t47`/`t479 lobby budget expired … starting the match anyway`; partial-lobby replay re-derives | yes |
| N3/N5/N6/N7/N11/N15/N17(e) | documented, code unchanged | docs/comments present at cited lines; behaviour unchanged; no checklist item | yes |
| N4, N17(a,c,d) | note drift, code correct, no change | shipped params equal recorded tuning pick, pinned by `test_tuning`; `broadcast_core.js` differs in exactly `BODIES_WIRE` + one comment path | yes |
| N8 | fixed | `DiscPairCount` derived; dead branch gone; golden hashes unchanged | yes |
| N9 | tightened; (b) disputed with measurements | bound 240→132; new 10 000-rollout moving-start block, 0 crossings; nothing loosened | yes |
| N10/N12/N13/N14 | fixed | dedicated `match_won` re-derivation block; `flushRoundRecords` at `server.nim:609,644,838,938`; `BeatKinds` lull scan + span test; `BubbleHoldTicks = 60` + dwell test | yes |
| N16(a) | DISPUTED — nothing tracked | `git ls-tree -r HEAD` and `git log --name-only c573490` both show 0 `replay-viewer/dist`/nimcache entries; `.gitignore:39` | yes — reviewer wrong |
| N16(b) | documented + fix-forward `5237976` | preload flag documented above the `switch`; run `33176949006` failed `wasm-viewer` only (jobs: test ✓, docker-smoke ✓, wasm-viewer ✗); head run green | yes |
| N17(b) | fixed + flake fix | deadline clamp at `decide.nim:184-189`; budget test + epoch-scoped fake provider; no assertion changed | yes |
| history note | duplicate commit series disclosed; tree byte-identical to the single chain | `git diff 8943270 HEAD` = only `replay-viewer/config.nims` (the `5237976` fix-forward); `tests/` diff empty | yes |

## Non-blocking observations

- **Duplicated history.** The N1–N17 fix series appears twice (`d46d479..8943270` and
  `e91d2d6..3ebd10e`) because the push script recomputed `BASE..HEAD` against the wrong base. The
  fixer disclosed it, did not rewrite pushed history, and the net tree is byte-identical to the
  tested chain plus the one fix-forward. Cosmetic; makes `git log -p -- tests/` show every hunk
  twice (each pair nets to the same content).
- **CND-2 / CND-3 remain phase-60 evidence**: no CI path exercises a live-LLM episode
  (docker-smoke has no `ANTHROPIC_API_KEY` by design), so the 660 s stop under real latencies and
  `results.reason == "complete"` for a two-champion hosted match are settled by phase 60's
  `replay_summary.py` check, exactly as the design already routes them. Not checklist items in
  this phase; the in-repo bounds (item 5) are verified.
- The renderer fixture checks horizontal clipping (`scrollWidth > clientWidth`) but not vertical
  self-clipping (`scrollHeight`) of a wrapping leaf; the measured note boxes wrap and pass today.
  A `scrollHeight` clause would make the gate airtight. Advisory only.

BLOCKING: 0
