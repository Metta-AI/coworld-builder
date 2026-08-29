blocking: 0

# r1 verdict — minecraft
Head: 6b4ac8afa3c53bdb32b187ac4e7cc9da4cb51266   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes (r1-fixes.md was NOT read at any point, per the brief)

Judged repo: `Metta-AI/cogame-minecraft` at main head `6b4ac8a` (21 commits after the reviewed
sha `c1acf21`). Starter: `/workspace/starters/coworld-ctf` (read-only). Design note:
`runs/2026-08-29-minecraft/design.md`. CI evidence: run **33245676171** at the judged sha,
conclusion **success** (`gh run list -R Metta-AI/cogame-minecraft --branch main -w ci.yml`);
jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; full log pulled with `gh run view … --log`.

## Standing blocking findings

None. Every reviewer finding is either resolved at the judged head (with the resolution
verified not to weaken a test — see the fixer-report audit note below; the audit was done
against `git log -p`, not against the fixer's self-report) or was correctly non-blocking and
remains so. My own checklist pass found no additional blocking item.

## Refuted / resolved (reviewer findings F1–F21, each checked at head)

### F1 — deleted exact follow-cam assertion (the review's one BLOCKING finding) → RESOLVED at head
- The loosening was real at `c1acf21`: commit `b01ed6a` replaced
  `doAssert "core.setZoom(32 / CAMERA_CELLS)" in block1` with a bare `"core.setZoom(" in block1`.
- At head, commit `dde652f` re-pins the mechanism as **exact expressions**,
  `tests/test_minecraft_viewer.nim:189-193`:
  `doAssert "var cellsNow = t.visW > 0 ? t.visW / 24 : CAMERA_CELLS;" in block1`,
  `doAssert "if (followArmed && Math.abs(cellsNow - CAMERA_CELLS) > 0.5) {" in block1`,
  `doAssert "core.setZoom((t.zoom || 1) * (cellsNow / CAMERA_CELLS));" in block1` — three exact
  pins where one stood before, matching the code the page actually ships
  (`client/replay_broadcast.html`, `applyCamera`). The departure from the note's closed form
  `32/cells` is recorded (`docs/PORTING-MINECRAFT.md` §I: the closed form is only right when the
  board fits on its width). Item 1's rule — deleted assertion blocking **unless replaced by
  equal-or-stronger** — is satisfied at head: the replacement is strictly stronger than the
  original (it pins the guard condition and the corrective expression, not just one call site).

### F2 — say/fallback feed and ↯ glyph live-server-only → RESOLVED (commit 631a313)
- `src/minecraft/replays.nim:133-148`: `applyControlRecord` now handles `"directive"` — playback
  pushes the record into `sim.feedDirectives` and increments `sim.fallbackTurns[0]` on a
  fallback-source directive. `tests/test_minecraft_replay.nim:220-255`
  (`narrationRederivesFromTheBytes`) records a live episode with a `say` and a fallback, then
  asserts the re-derived feed carries the say (`sawSay`), the frame carries
  `frame["directives"][0]{"say"} == recorded.says[0]`, and `frame["mc"]["fallbacks"]` equals the
  recorded count — i.e. LLM-authored text is now derivable from replay bytes and asserted,
  which is also the second half of checklist item 15.

### F3 — actionsDropped ≡ repliesRepaired → RESOLVED (commit ae1a720)
- `src/minecraft/server.nim:619-620` now reads `sim.actionsDropped += plan.dropped` /
  `sim.repliesRepaired += plan.repaired`; the parser counts the two causes apart, and
  `tests/test_minecraft_driver.nim:187-241` asserts both counters on both causes
  (`repaired == 2, dropped == 0` for invalid entries; `dropped == 18, repaired == 0` for
  over-cap).

### F4 — lava effectively absent → RESOLVED (commit 9d7e2ec)
- `src/minecraft/world.nim:74` `const LavaCaveGate* = 300` (was the note's literal 120), used at
  `:326-328`. Recorded as divergence C in `docs/PORTING-MINECRAFT.md:135`. The note's own test-26
  lava clause is now asserted: `tests/test_minecraft_engine.nim:237-239`
  `doAssert episode.lavaEvents >= 1` on the cert seed. A generator change, so `GameVersion` was
  bumped and fixtures re-cut — not a test weakening.

### F5 — 24 ticks/s vs the note's 10 → RESOLVED as a recorded divergence (commit 284a77a)
- Behavior unchanged (24 t/s — which more than satisfies item 13's soak: CI showed
  `"0 / 531" -> "191 / 531" -> "240 / 531"` over 10 s); the lying comment is gone —
  `src/minecraft/replays.nim` (`advanceReplayFrame` doc) and `ci.yml:357-359` now both say
  24 ticks/second, and `docs/PORTING-MINECRAFT.md` §J records why the note's 10 t/s cadence was
  not used (the replay timebase and presentation loop share `TargetFps = 24`). No checklist item
  pins the playback rate.

### F6 — fixture not driven by viewer_smoke.mjs, no string self-assertions → RESOLVED (commits ca59162, 6b4ac8a)
- `tools/ci/fixture_smoke.mjs` no longer exists. `ci.yml:406-415` drives
  `tools/ci/renderer_fixture.html` with `node tools/ci/viewer_smoke.mjs --url … --strict-text-bounds
  --out fixture-evidence` — the SAME gate as the main smoke. The fixture now asserts its own
  strings: `FULL_SAY` is built to exactly `MAX_SAY_RUNES = 160` runes including two 4-byte emoji
  (`renderer_fixture.html:100-108`), `drive()` refuses to run if `SAY_RUNES !== MAX_SAY_RUNES`
  (`:279-282`), and `inspectNarration` (`:196-249`) reads the drawn string back out of the iframe
  DOM and fails on a shortened render, a clipped row (`scrollHeight > clientHeight`), or a box
  outside the frame, at 960/640/**360** px, setting `data-replay-loaded="true"` only after every
  scenario and assertion held. CI run 33245676171, step "Drive the renderer fixture" ran and
  printed `{"loaded":true,"ms":8340,…}`.

### F7 — four ctf beat rules survive in the prefix → RESOLVED (commit a9113e6)
- `client/replay_broadcast.html:873-877`: the `.beat-marker.kill/.steal/.return/.capture` rules
  are removed from the prefix (replaced by a banner-comment explaining the removal), and
  `tests/test_minecraft_viewer.nim:126-150` now scans the **whole page**: the eight ctf kinds
  asserted absent from `page`, and the set of `.beat-marker.<kind>` rules the page carries
  asserted **equal** to `{death, end, fallback, milestone, newdepth}`.

### F8 — prefix not byte-identical to the starter; test doesn't freeze it → RESOLVED (commit 17f5fe3)
- The reviewer itself verified every pre-banner hunk is a note-enumerated removal/relabel; I
  re-diffed the page against the starter at head and concur (removals: `.fpv-hp`/`.fpv-gear`/
  `.fpv-map` CSS+JS (~185 lines), `#povBadge`, ctf scorebug internals, four-team art loops →
  `['red']`, the note's §"Endcard and chrome label re-mapping" relabels, `PB_`→`MC_` splice
  rename — each is on the note's list at design.md:1618-1644 / 1680-1702). At head the prefix is
  frozen: `tests/test_minecraft_viewer.nim:56-63` pins `prefix.len == 211_999` and SHA1
  `E8FA323DFCFB5E81D8672862004B7E4BBF7E9915`, the same discipline as chrome_common's sha256.
  `client/chrome_common.js` is byte-identical to the starter's (diff clean; sha256
  `7ace7287…72f7c`, 40 022 B, verified by me directly and pinned in ci.yml + test 38).

### F9 — broadcast_core.js has none of the note's eight draw calls → REFUTED as a defect; recorded (commit f3603e3)
- True observation, wrong target: no checklist item requires those functions. What shipped is
  MORE conservative than the note (the board is composited wasm-side into sprite packets,
  `src/minecraft/global.nim`; the gutter panels are DOM in the appended block), and
  `client/broadcast_core.js` differs from the starter's by an added `MINECRAFT_WIRE` lookup only
  (62 194 vs 62 123 bytes). Recorded as `docs/PORTING-MINECRAFT.md` §L. Item 14's camera/zoom/
  minimap wiring is verbatim-kept and test-asserted.

### F10 — tickCap unreachable / mislabeled → RESOLVED (commit 982707f)
- `src/minecraft/sim_state.nim:395-405` keeps the guard with a truthful comment;
  `tests/test_minecraft_replay.nim:153-166` now asserts `endRuleText() == EndRuleTickCap` with
  `turnsPlayed == 0` on the no-turn path — the former `in [tickCap, turnCap]` disjunction is
  replaced by the exact rule. (This was one of the review's "not loosened" evidence hunks; at
  head it is strictly stronger.)

### F11 — record→re-derive covered 4 of 6 end rules → RESOLVED (commit c1d913e)
- `tests/test_minecraft_replay.nim:112-146` now round-trips **five** rules with the expected rule
  named per case and pre-asserted (`recorded.endRule == expect`), including a real `diamond`
  recording (seed 42) and a real `death` recording (seed 4); `tickCap` is asserted in-sim with
  the exact-rule check (it cannot be round-tripped: it needs an episode whose turns never end,
  which no recording produces — the comment says so). Item 2 was already satisfied at the
  reviewed sha; at head the note's test 30 is satisfied to the extent recordable.

### F12 — server plays out a no-show seat instead of refusing → REFUTED as blocking; recorded (commit fd68c35)
- The note asks for both "refuses to start" and "the episode plays out scripted" (design.md:1292
  vs :660-661, and test 27 requires a finished episode from a never-connecting seat). The
  implementation is loud (`ERROR: seat 0 …`), reports the closed
  `{"message","failed_policy_index"}` payload once, and plays out bounded — item 5 is satisfied,
  no checklist item requires refusing. Recorded as `docs/PORTING-MINECRAFT.md` §M.

### F13 — MaxReplyBytes enforced in runes → RESOLVED (commit f7e6771)
- `src/minecraft/sim_types.nim:342-355` adds `truncateBytes` (byte cap, cut on a rune boundary,
  never splits a codepoint); `src/minecraft/llm.nim:208` uses it. Test:
  `tests/test_minecraft_driver.nim:271-281` feeds 4-byte emoji and asserts
  `bounded.len <= MaxReplyBytes`, `> MaxReplyBytes - 4`, and `runeLen == MaxReplyBytes div 4`.

### F14 — "will retry" logged after the last attempt → RESOLVED (commit c5aa183)
- `src/minecraft/decide.nim:207-215`: `if attempt + 1 < 2:` "failed, will retry" else "failed:".
  The phase-60 grep phrase "falling back" still fires only on the genuine terminal fallback
  (`:234-235`, and the pre-batch guard path at `:139-141`). Verified in the CI log: the test
  job's episode printed `falling back to miner (no_credentials)` per turn.

### F15 — stepEvents emits 10 of a declared 16; subset-only test → RESOLVED (commit 9ec9a3e)
- `src/minecraft/broadcast.nim:45-48`: `StepEventKinds` is now the honest 12-kind set (adds
  `bridge` and `blocked` to the emitter; `turn`/`plan`/`say`/`fallback` are decision-layer facts
  that reach the chrome through chat records, as the adjoining comment records), and
  `tests/test_minecraft_events.nim` asserts the emitted set **equals** the declared set
  (`seen == step`, sorted), exercising bridge, blocked, lava, interrupt and death paths to do it.
  The former containment-only assertion was replaced by equality — stronger.

### F16 — post-pass/driver/hash nits → RESOLVED or refuted item by item (commit 31f7222)
- `goto` to the cog's own cell: `src/minecraft/driver.nim:44-49` now returns zero primitives
  WITHOUT counting `unreachable` (arrival, not failure). Write-only `craftedItem` removed. The
  702-vs-700 discrepancy is the note disagreeing with itself (78 % of 900 **is** 702); the code
  took the percentage. `gameHash` mixing `cog.alive` is deterministic and identical on both
  paths — no checklist item touched. All non-blocking.

### F17 — llmTurns/fallbackTurns arrays vs the note's scalars → REFUTED as a defect; recorded (commit daf0a59)
- Code, `results_schema` and test agree exactly (key-set equality asserted at
  `tests/test_minecraft_engine.nim:203-214`); seat-indexed arrays are the starter's shape for
  seat-indexed data. Recorded as `docs/PORTING-MINECRAFT.md` §N. Item 10 unaffected.

### F18 — cert seed 8, not the note's 42 → MOOT at head (commit 729eb92)
- `certification.game_config.seed == 42` at head (verified from the manifest), and the committed
  fixture is `tests/fixtures/cert_seed_42.replay`. The F21 generator fix made seed 42 satisfy
  every test-26 property including the lava event (`docs/PORTING-MINECRAFT.md` §G). Test 26
  reads the seed out of the manifest, so the two cannot drift.

### F19 — docs/protocols typed "uri" vs item 10's literal "text" → REFUTED as blocking (commit d3e7987)
- The brief's own parenthetical governs: judge by what coworld certify accepts, starter
  precedent being the strongest evidence. I read the starter's shipped, certified
  `coworld_manifest_paintbot.json` myself: `game.docs.readme`, every `pages[].content`,
  `game.protocols.player` and `.global` are all `{"type":"uri","value":"https://…"}` — exactly
  this repo's shape. `tests/test_minecraft_manifest.nim:40-60` pins `uri` with the precedent
  named and asserts every `value` starts `https://`. Item 10's structural requirement (readme +
  pages with id/title/content; BOTH protocol keys as objects) holds. Not blocking.

### F20 — tautological failure-payload test → RESOLVED (commit 5da0771)
- `tests/test_minecraft_engine.nim:263-276` now calls `playerFailurePayload` — the proc
  `server.declarePlayerFailure` actually serialises (`src/minecraft/roster.nim:14`,
  `src/minecraft/server.nim:195`) — and asserts exactly two keys, the index and the message
  prefix. No longer a literal asserting itself.

### F21 — reference solver is a flood; tick bound unasserted → RESOLVED (commit 729eb92)
- `tests/test_minecraft_world.nim` now carries a real ladder-playing solver (every action a real
  primitive through the real `sim.step`) over 60 seeds × both variants, asserting the diamond is
  reached and `ticks <= 500` (standard) / `<= 420` (deepcut) (`:388-398`). The commit's honest
  by-product: it exposed 35/300 water-sealed spawns and added post-pass 2b (`openSurfaceRoute`),
  GameVersion 2→3, re-swept baselines (`tools/ci/baseline_tuning.json` re-pinned), re-cut
  fixtures, and raised test 24 from 50 to the note's 100 seeds. Test deltas in that commit are
  seed swaps plus strictly more assertions — nothing weakened.

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 33245676171 = success at 6b4ac8a (jobs test/docker-smoke/wasm-viewer all ✓, every wasm-viewer step ran, no continue-on-error in ci.yml). `git log -p --since=2026-08-29T05:18:30Z -- tests/`: every deleted assertion audited — F1 (re-pinned stronger at dde652f), F10 disjunction→exact, F15 subset→equality, F20 literal→real proc, F19 `.len>0`→`startsWith("https://")`, F3 one-counter→two; fixture files replaced only under generator/GameVersion bumps; no skip/xfail anywhere |
| 2 replay re-derivation | PASS | `replays.nim:206-222` stepReplay re-runs recorded primitives through the same `sim.step`; `checkReplayHash` (`:190-204`) compares `sim.gameHash()` per tick; `tests/test_minecraft_replay.nim:112-146` asserts `hashMismatchTick == -1` for five recorded end rules; viewer draws from that re-derivation (`replay_runtime.nim:16-30`, `buildReplayViewerPacket` off the re-stepped sim) — no parallel recording |
| 3 static viewer | PASS | manifest `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`), invoked by path in ci.yml; no `/client/replay` string anywhere in the manifest (grep rc=1); bundle served from a local static server in the smoke, only the replay URL fetched |
| 4 both name spaces | PASS | `observe.nim:238` `"you": seatAlias(0)` (alias only in observations); real name spectator-side: `roster.nim` results.names, join record, `broadcast.nim:156-171` roster `name`/`pol`, drawn in `renderPlate`; `showPlayerLabels: false` both variants |
| 5 degrade-never-hang | PASS | attempt1Ms/retryMs floor-converted to whole seconds (`decide.nim:184-189`), outer `turnBudgetMs` checked before each attempt (`:163-167`), spacing sleep ≤ 2600 ms, rolling-60 s rate guard ≤ 28, budget guard (`:108-116`), engine hard stop at loop top (`server.nim:470-480`), `lobbyJoinTimeoutTicks`, bounded shutdown grace (`:758-764`); manifest test pins `wallClockBudgetSeconds <= 660` (`test_minecraft_manifest.nim:119`) < 720 s; docker-smoke episode completed in ~25 s |
| 6 num_agents | PASS | `num_agents: 1` in both variants' `game_config` + `certification.game_config`, absent at variant top level (verified programmatically); `docker_smoke.sh:104-151` enforces the four SEAT-COUNT invariants + the independent `SMOKE_SEATS=1` cross-check, `SEAT-COUNT FAIL:` prefix; `grep 'SEAT-COUNT FAIL'` over the full run-33245676171 log: **0 matches**; smoke logged `smoke OK: seats=1 … reason=complete` |
| 7 scripted baseline full legal episodes | PASS | `test_minecraft_engine.nim:192-215` all-scripted episode to natural end, `reason == "complete"`, seven results identities, schema-exact key set; `test_minecraft_driver.nim:67-115` bounds 600 baseline replies (≤12 actions, per-verb n ranges, goto in 0…31, never steps onto known lava); tuning: `tools/tune_baselines.nim --check` runs as its own ci.yml step against `tools/ci/baseline_tuning.json` (re-swept and re-pinned in 729eb92), plus the shipped-defaults test |
| 8 LLM reply handling | PASS | tolerant `extractJsonObject` + prefill re-prefix; retry exactly once (`decide.nim:160` `attempt < 2`); terminal fallback = `minerFallback` (the same proc as the baseline, `:74-79`); every fallback writes a `fallback` chat record with cause (`:141, 206, 232`) and increments `results.fallbackTurns` — countable in phase 60 |
| 9 rune-safe truncation | PASS | `truncateRunes` (`sim_types.nim:333-340`) is the single cut point for say/notes/label/detail/stopDetail; `truncateBytes` (`:342-355`) never splits a codepoint; `test_minecraft_driver.nim` feeds 4-byte emoji at 160/400/4096 caps, asserts `validateUtf8() == -1`; `test_minecraft_replay.nim:283-320` runs `replay_summary.py` on an all-caps-emoji replay, strict-UTF-8 JSON, no lone surrogates |
| 10 manifest validates | PASS | `game.docs` = readme + 4 pages each `{id,title,content}`; `game.protocols` carries BOTH `player` and `global` as `{"type","value"}` objects; discriminator `uri` matches the starter's shipped certified manifest exactly (verified in `/workspace/starters/coworld-ctf/coworld_manifest_paintbot.json`) — the precedent the brief names as governing; pinned in `test_minecraft_manifest.nim:40-60` |
| 11 viewer legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` (`replay_broadcast.html:4116-4121`); labels hidden under the starter's own `.tiny` mechanism (`#stage.tiny .plate .lives-label { display:none }` `:4371-4373`; `relayout()` toggles tiny at `boardW <= 620`, `:4312`, inherited verbatim — the starter's own "640×360 floor" rule); both gutter arithmetics asserted in test 43 |
| 12 release order + scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify (:173, `--timeout-seconds 300`) → Upload policies (:216) → Upload Coworld (:314) → Put secret (:410); hosted smoke runs against the version this run built (`--wait-hosted-smoke` on the upload, canonical enforced at :570-577); three workflows present; `docker_smoke.sh` + `build_replay_viewer.sh` mode 100755; `policies.json`: 2 × PLAYER_PROMPT champions + miner + scrounger, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the placeholder grep over the five files exits clean (I ran it) |
| 13 viewer executes | PASS | run 33245676171 `wasm-viewer` (needs: docker-smoke) ran "Load the bundle in a real browser": `{"loaded":true,"ms":374,…}`, `soak: 10s of playback kept advancing ("0 / 531" -> "191 / 531" -> "240 / 531")`, scrub readouts responded; `data-replay-loaded` set in the shell's `'loaded'` branch only after the Worker's first ingested frame (`static_replay.js:161`, `static_replay_worker.js:63-72`); `data-replay-error` in `showFailure()` (`static_replay.js:14-20`); playback opens at the game start: `initReplayRuntime` seeks `replayStartTick()` before frame 0 (`replay_runtime.nim:27-28`), startTick = first `phase == Playing` tick (`replays.nim:304-309`), shipped as `st`; the lobby-dwell failure mode is structurally impossible here — primitives/hashes are written only in `Playing` (`server.nim:602-651`), so a lobby of ANY length records zero ticks (see observation 1 on the late-gameStart probe); link flags + bootstrap from ONE starter: `config.nims` has no MODULARIZE/EXPORT_NAME, worker uses `Module.onRuntimeInitialized` (`static_replay_worker.js:188`) — line-identical to coworld-ctf's pair apart from the `ctf_`→`minecraft_` symbol rename |
| 14 chrome is the starter's | PASS | `chrome_common.js` **byte-identical** (diff clean, sha256 = starter's, pinned twice); page = starter + appended `MINECRAFT additions` block at :4084, prefix frozen by length+SHA1 (test 39), every pre-banner hunk on the note's removal/relabel list (I diffed all 1493 hunk-lines against the starter); `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (:4276-4325 region, inherited); nothing fixed-positioned in the block, `#mc-inv`/`#mc-left` ride `calc(var(--band, 0px) + …)`; `#endcard { bottom: var(--band, 0px) }` + `.on` class + inherited every-seek dismissal; beats are labelled `<button>`s seeking `s:<tick>` via `mcBeat` with CSS for exactly the five emitted kinds and no others (test asserts page-wide equality); `#viewpanel` KEPT and wired (`attachMinimap`, `setZoom` convergence, `panTo` per frame — exact expressions test-pinned) — correct, the note says the 32×32 board at a 15-cell camera is pannable |
| 15 drawn strings fit | PASS | main smoke: `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` — total 0 because this viewer draws NO canvas text at all (no fillText/strokeText in page or core, test 44), so per the item the counters prove nothing and the DOM fixture is the load-bearing gate: `renderer_fixture.html` loads the SHIPPED bundle in an iframe, drives the real block through `MinecraftChrome.__fixture` with a verified-160-rune say on the seat, all 11 chips, all four depths, three endcards, at 960/640/360 px, asserts the drawn string full-length + unclipped + in-frame, and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own ci.yml step (ran, `loaded:true`); the narration row has a reserved 4-line band (`.feed-row.mc-narration`, min-height, wraps — never ellipsised); LLM text on playback is re-derived from directive records in the bytes and test-asserted (`narrationRederivesFromTheBytes`) |
| batch rule (1 seat) | PASS | one `RequestBatch` per turn through `engine.client.curl.makeRequests` (`decide.nim:170-190`); no sequential per-seat provider loop exists |

## Non-blocking observations

1. **Seek clamp undershoots the start tick by one.** `seekReplay` clamps to `[0, maxTick]`
   (`replays.nim:247`) where the starter's `beginSeek` clamps to `[replayStartTick(), maxTick]`
   (coworld-ctf `replays.nim:793`). Item 13's "every seek clamps there" is therefore not literal
   here: the transport's back-step (`'b'` → `max(0, tickCount - 1)`) can land on tick 0, one tick
   before `startTick == 1`. I do not count it blocking because the failure mode the item exists
   to prevent (10–45 s of frozen recorded-lobby dwell) is structurally impossible in this
   recorder: primitives and hashes are written only while `phase == Playing`
   (`server.nim:602-651`), so a lobby of any `lobbyJoinTimeoutTicks` occupies **zero** recorded
   ticks, `gameStarts[0].tick` is always 1, the scrubber axis (`st`) starts there, and the
   undershoot is a single presentational tick that playback steps past on the next frame. The
   "late gameStart" probe the item asks for cannot be constructed against this format — verified
   by reading the recorder, which is the strongest evidence the tree can give. A one-line clamp
   to `replayStartTick()` would close the letter of the item.
2. **The note's prose drifted in ten recorded places** (24 t/s playback, lava gate 300, no
   broadcast_core draw functions, arrays for llmTurns, no-show plays out, convergent follow-cam,
   post-pass 2b, seed history, mix64 mask, engine-not-socket e2e) — every one is enumerated in
   `docs/PORTING-MINECRAFT.md` §§A–O with its reason. None touches a checklist item.
3. **`results.reason == "deadline"` reachability in production** remains unprovable from CI
   (docker-smoke has no API key, so the wall-clock path only runs synthetically). The synthetic
   round-trip is tested; a hosted run with a live provider is where phase 60 will see it.

## Fixer report audit

Per the brief, `r1-fixes.md` was **not read**. In its place, every fix commit named `F<k>` in
`git log` was audited directly against its diff and the head tree:

| finding | commit claims (from `git log`/diff) | I verified at head | agrees |
|---|---|---|---|
| F1 | dde652f re-pins exact follow-cam expressions | 3 exact-string asserts at test_minecraft_viewer.nim:189-193 match the shipped page | yes |
| F2 | 631a313 re-applies directive records on playback | replays.nim:133-148 + narration re-derivation test | yes |
| F3 | ae1a720 splits the two counters | server.nim:619-620, both causes test-asserted | yes |
| F4 | 9d7e2ec cave gate 120→300 | LavaCaveGate=300, lavaEvents≥1 asserted on cert seed | yes |
| F5 | 284a77a says 24 t/s everywhere | replays.nim comment, ci.yml, PORTING §J | yes |
| F6 | ca59162+6b4ac8a: real gate + self-asserting fixture | viewer_smoke.mjs --strict-text-bounds drives it; 160-rune say verified in-fixture; CI step ran, loaded:true | yes |
| F7 | a9113e6 removes 4 prefix beat rules, page-wide scan | rules gone; page-wide kind-set equality test | yes |
| F8 | 17f5fe3 freezes prefix (length+digest) | prefix.len==211999 + SHA1 pinned | yes |
| F9–F12, F16–F18 | record-why commits (PORTING §§C,G,L,M,N + driver/goto fix) | divergences present; goto-own-cell = arrival; tickCap exact-asserted | yes |
| F13 | f7e6771 byte cap on a rune boundary | truncateBytes + llm.nim:208 + byte-cap test | yes |
| F14 | c5aa183 branches the retry notice | decide.nim:207-215 | yes |
| F15 | 9ec9a3e emits bridge/blocked, equality assert | StepEventKinds=12, seen==step | yes |
| F19 | d3e7987 keeps uri, pins precedent | starter manifest verified uri; test pins uri+https | yes |
| F20 | 5da0771 asserts the real payload proc | playerFailurePayload used by server + test | yes |
| F21 | 729eb92 real solver + tick bound; generator fix | solver test with ≤500/≤420 bounds; openSurfaceRoute; GameVersion 3; fixtures/tuning re-cut; test deltas strictly stronger | yes |

BLOCKING: 0
