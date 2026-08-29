# r1 review — minecraft

Repo: `Metta-AI/cogame-minecraft`, reviewed sha **`c1acf2182d80287a3c4e6c7ab773bcce928f8038`**
(`main` head, "viewer: drop the agent-view inset clear of the minimap above it", 2026-08-29 08:01:48Z).
Clone: `/tmp/review-minecraft/cogame-minecraft`. Starter diffed against: `/workspace/starters/coworld-ctf`.
Design note: `/workspace/coworld-builder/runs/2026-08-29-minecraft/design.md` (identical copy at
`docs/plans/2026-08-29-minecraft-design.md`, 2345 vs 2346 lines — trailing newline only).
Files read: 41 (all of `src/minecraft/*.nim`, `src/minecraft.nim`, `src/minecraft_player.nim`,
`replay-viewer/*`, `client/*`, all 10 `tests/*.nim`, all three workflows, `tools/ci/*`,
`coworld_manifest_template.json`, `docs/PORTING-MINECRAFT.md`, `Dockerfile`, `compose.yaml`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule).

CI evidence: `gh run list -R Metta-AI/cogame-minecraft --branch main -w ci.yml` →
run **33242187530**, conclusion **success**, at the reviewed sha. Jobs: `test` ✓, `docker-smoke` ✓,
`wasm-viewer` ✓ (needs: docker-smoke). Every step of `wasm-viewer` ran, including step 11
"Load the bundle in a real browser" (`viewer_smoke.mjs … --soak 10 --strict-text-bounds`) and step 12
"Drive the renderer fixture". No `continue-on-error` anywhere. `grep -i 'SEAT-COUNT' ` over the full
run log returns nothing; `docker-smoke` logged `smoke OK: seats=1 results=1299B replay=233836B
reason=complete`.

---

## Blocking

### F1 — a test assertion was deleted and replaced with a strictly weaker one during this run
- Where: `tests/test_minecraft_viewer.nim:143` (commit `b01ed6a`, "viewer: the fixture waits for a real
  frame; the camera converges; the plate is the run's")
- Observed (`git -C <repo> log -p -- tests/`):
  ```diff
  -  doAssert "core.setZoom(32 / CAMERA_CELLS)" in block1
     doAssert "CAMERA_CELLS = 15" in block1
  +  doAssert "core.setZoom(" in block1, "the follow-cam sets the zoom"
  +  doAssert "t.visW / 24" in block1,
  +    "the follow-cam converges on the transform the core REPORTS"
  ```
  The deleted predicate pinned an exact expression; the replacement `"core.setZoom("` is satisfied by
  *any* `setZoom` call. The code it guarded did change in the same commit:
  `client/replay_broadcast.html:4662-4665` now reads
  `var cellsNow = t.visW > 0 ? t.visW / 24 : CAMERA_CELLS; if (followArmed && Math.abs(cellsNow -
  CAMERA_CELLS) > 0.5) core.setZoom((t.zoom || 1) * (cellsNow / CAMERA_CELLS));` — a convergence loop,
  not the note's closed form. Two new assertions were added in the same hunk (`t.visW / 24`, `#fpv {`),
  so the file's assertion count went up (5 insertions, 1 deletion), and the commit message states the
  reason (the closed form `32/cells` is only correct when the board fits on its width; the screenshot
  came back at ~4 cells across).
- Checklist item: item 1 — "CI green … **with no test disabled, skipped, or loosened during this run**
  … Read those hunks: a deleted assertion, a widened tolerance, a `skip`/`t.Skip`/`xfail`/`--skip`
  added, or a test file removed is a blocking finding."
- Why blocking: item 1 names a deleted assertion in `tests/` during this run as blocking without an
  exception for "the code changed underneath it". The design note's own test 42
  (`design.md:2244-2249`) still says "the game block calls `core.setZoom(32 / cameraCells)` with
  `cameraCells == 15`"; after this hunk no test asserts the zoom is 32/15 — only that *some* zoom is
  set and that the convergence expression is present. I state the mitigation plainly so the judge can
  weigh it: this is a mechanism change with a stated cause, not a green-washing edit.
- Related hunks in the same sweep, which I read and judge **not** loosening (evidence, not findings):
  `tests/test_minecraft_events.nim:25` `for seed in [3, 8, 42]` → `[4, 8, 19]` (forced by the `mix64`
  mask change in the same commit `45a2cb7`; the same commit *adds* a post-loop `stepEvents` diff at
  `:58-65` so the `end` kind is actually observed, and no assertion was removed);
  `tests/test_minecraft_engine.nim:239` a comment-only edit; `tests/fixtures/cert_seed_42.replay` and
  `diamond_seed_8.replay` deleted and replaced by `cert_seed_8.replay` / `diamond_seed_5.replay`
  (fixtures, not test files, and stale under the new generator — the version sweep at
  `tests/test_minecraft_replay.nim:288-299` would fail on them); `tests/test_minecraft_viewer.nim:230-234`
  added three assertions in `8e7e307`.

---

## Non-blocking

### F2 — the static replay viewer never shows any LLM-authored text: `say`, the fallback feed line and the plate's fallback glyph are live-server-only
- Where: `src/minecraft/server.nim:633` (`sim.pushFeedDirective(record)`) is the **only** caller;
  `src/minecraft/broadcast.nim:273-281` gates `state["directives"]` on `sim.feedDirectives.len > 0`;
  `src/minecraft/replays.nim:104-130` (`applyControlRecord`) handles only `start`, `turnend`, `stop`
  and `discard`s everything else, including `{"k":"directive"}`;
  `client/replay_broadcast.html:4862-4866` (`mcDirectives`) returns immediately when `s.directives` is
  absent; `src/minecraft/broadcast.nim:236` `"fallbacks": sim.fallbackTurns[0]`.
- Observed, traced: in replay mode the server loop takes the `if replayLoaded:` branch
  (`server.nim:599-601`) and never reaches `:633`, and the wasm host
  (`replay-viewer/minecraft_replay.nim:95-101`) drives `advanceReplayFrame` only. Nothing on the
  playback path re-applies a `directive` chat record, so `sim.feedDirectives` is empty for every frame
  the static viewer ever draws → `state.directives` is never emitted → the block's `say` row
  (`:4874-4877`) and its `MISSED THE CALL — miner plan` row (`:4871-4873`) never render. Likewise
  `sim.fallbackTurns[]` is only incremented in the live loop (`server.nim:626`), so `mc.fallbacks` is
  always `0` on playback and the plate's `↯` glyph (`:4728`) never lights. The fallback **beat
  markers** do survive, because `scanReplay` reads them straight from the chat stream
  (`replays.nim:337-348`).
- What the note says: §Viewer readout 10 (`design.md:1770-1777`) — "`Alpha: "iron in the wall …"`" and
  "`MISSED THE CALL — miner plan (timeout)`" … "The `say` lines and the plan lines are where a
  spectator sees the LLM playing"; §Record vocabulary A (`design.md:1485-1486`) — the chat records
  "drive the broadcast feed"; readout 7 (`:1762`) — "a `↯` glyph if the seat has taken a fallback".
- Not blocking: no checklist item names the feed. Note that CI cannot see this — `docker_smoke.sh`
  runs with no `ANTHROPIC_API_KEY`, so the smoke replay has no `say` at all (`viewer-smoke` reported
  `"feed_lines":0`), and the renderer fixture injects `s.directives` synthetically
  (`tools/ci/renderer_fixture.html:99-101`), so it exercises the renderer but not the pipeline.

### F3 — `actionsDropped` and `repliesRepaired` are the same number; the note defines them as two different counts
- Where: `src/minecraft/server.nim:619-620`
  (`sim.actionsDropped += plan.dropped` / `sim.repliesRepaired += plan.dropped`);
  `src/minecraft/directives.nim:211-224` increments one `dropped` counter for both causes
  (over-cap entries at `:215-217`, invalid entries at `:224`). Mirrored in the test harness at
  `tests/test_minecraft_engine.nim:77-78`.
- Note: `design.md:406-409` — "(a) Entries past `maxActionsPerTurn = 12` are dropped and counted in
  **`actionsDropped`**. (b) … an entry that does not validate is **dropped** … counted in
  **`repliesRepaired`**". Both `results` keys exist and are schema-declared, so a consumer reading
  them gets two identical numbers rather than the split the note documents.

### F4 — lava is effectively absent: measured, and the note's "only lethal thing" is unreachable on most seeds
- Where: `src/minecraft/world.nim:246` — `elif c < 120 and draw(seed, z, 0, x, y) <
  lavaChanceFor(config, z)`, which is exactly `design.md:220` rule 2.
- Measured (independent Python re-implementation of `mix64u`/`mix64`/`noiseField`/`draw` from
  `sim_types.nim:346-366` and `world.nim:74-99`, 200–300 seeds, interior cells only):
  | | mean lava cells `z=2` | mean lava cells `z=3` | seeds with ≥1 lava cell anywhere |
  |---|---|---|---|
  | `standard` | 0.105 | 0.340 | 97/300 (32 %) |
  | `deepcut` | 0.215 | 0.565 | 141/300 (47 %) |
  `unsealLava` (`world.nim:169-196`) never fires: it only triggers below 702 diggable cells of 900,
  i.e. above ~198 lava cells per level.
- Consequence, traced rather than asserted: on ~68 % of `standard` seeds the world contains **no lava
  at all**, and where it exists it is almost always on `z=3` (79 of the 97), a level the `miner`
  baseline reaches on a minority of seeds. So `endRule = death`, `deathCause = lava`, the interrupt
  rule (tick step 8), `place_block`'s bridge, `dig_down` case 3 and the death endcard are live code
  with essentially no live traffic. The builder documents this in `docs/PORTING-MINECRAFT.md:136-156`
  and states the generator is implemented exactly as specified — I confirm that: the code matches
  `design.md:215-224` character for character, so this falsifies the note's *prose*
  (`design.md:104-105` "nothing hunting it"; `:456-457` "lava is the only thing in this world that can
  end a run") and its §Tests item 26 lava clause, not its formula.
- Test consequence: `tests/test_minecraft_engine.nim:237-244` records, in a comment, that the note's
  "at least one `lava` event on the cert seed" clause is dropped. That clause was never asserted (it
  is absent from the initial commit `e3e3535`), so this is not a test that was loosened during the run.

### F5 — playback runs at 24 ticks/s, not the note's 10; the doc comment in the same proc says 10
- Where: `src/minecraft/replays.nim:355-359` (comment: "one tick per three animation frames at 30 fps
  = 10 ticks/second, so a 960-tick episode plays for 96 s") vs `:385` `var steps =
  replay.replaySpeed()` = `PlaybackSpeeds[0]` = **1** tick per frame
  (`src/minecraft/sim_types.nim:29`), and `replay-viewer/static_replay.js:46` `var frameMs = 1000 / 24`.
  One tick per frame × 24 fps = 24 ticks/s; a 960-tick episode plays for 40 s.
- Confirmed empirically in CI run 33242187530: `soak: 10s of playback kept advancing ("0 / 959" ->
  "192 / 959" -> "240 / 959")` — 240 ticks in ~10 s.
- Note: `design.md:1722-1727` "one tick per three animation frames at 30 fps = 10 ticks/second …
  A 960-tick episode therefore plays for 96 s", with "the cog's position interpolated across the three
  frames so a step glides rather than snapping" — there is no sub-tick interpolation in the shipped
  code. `PlaybackSpeeds = [1, 2, 3, 4, 8, 16]` also differs from the note's chips `[0.5, 1, 2, 4, 8]`.
- Not blocking: item 13's soak requirement is still met with a wide margin (40 s of playback vs a 10 s
  soak), and CI proves advancement.

### F6 — the renderer fixture is driven by a repo-local harness, not by `viewer_smoke.mjs --strict-text-bounds`, and it asserts nothing about its own string lengths
- Where: `.github/workflows/ci.yml` step "Drive the renderer fixture …" runs
  `node tools/ci/fixture_smoke.mjs --bundle … --replay … --timeout 90`;
  `tools/ci/fixture_smoke.mjs:113-120` waits only for `data-fixture="ok"` on `<html>`;
  `tools/ci/renderer_fixture.html:161-176` drives 7 scenarios × 3 widths (960/640/**360**) and sets
  `data-fixture="ok"` when nothing threw.
- Note/checklist: `design.md:2279-2287` (test 49) and checklist item 15 both say the fixture is
  "driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step" and that "the fixture
  asserts its own strings are still full-length". Neither holds: a different harness is used and no
  length assertion exists. (`FULL_SAY` at `renderer_fixture.html:82-86` is 152 runes, not the 160-rune
  cap.)
- Context that bears on severity: the fixture does load the **shipped** `dist/static-replay-viewer/index.html`
  in an iframe and drive the real block through `MinecraftChrome.__fixture` (no re-implementation), and
  the main smoke *does* carry `--strict-text-bounds` and reported
  `canvas text: 0 drawn, 0 never inside the canvas … 0 ellipsized`. `total: 0` is expected here: there
  is **no** `fillText`/`strokeText` anywhere in `client/replay_broadcast.html` or
  `client/broadcast_core.js` (verified by grep), so every string in this viewer is DOM. Under item 15's
  own words, `total: 0` "is not evidence of anything" — the gate is vacuous, but the repo does ship the
  fixture the item demands, so the item's literal blocking condition ("no such fixture") is not met.

### F7 — four of ctf's eight scrubber-beat CSS rules survive above the banner; the note says all eight are removed and test 41 only looks below the banner
- Where: `client/replay_broadcast.html:875, 880-889, 890` — `.beat-marker.kill`, `.steal`
  (+ `::after`), `.return`, `.capture` are intact in the inherited prefix. The five kinds this game
  emits have their own rules at `:4310-4334`. `.gamestart` / `.hillflip` / `.tagout` / `.gameover` are
  gone.
- The test that should catch it: `tests/test_minecraft_viewer.nim:111-133` scans only `block1`
  (`page[page.find(SpliceBanner) .. ^1]`, `:26`), so the four surviving rules in the prefix are outside
  its scope; the assertion at `:129-132` checks the eight names are absent from `block1` only.
- Note: `design.md:1627-1630` — "The ctf beat CSS rules `.beat-marker.kill`, `.steal`, `.return`,
  `.capture` … and `.gamestart`, `.hillflip`, `.tagout`, `.gameover` are **all removed**"; test 41
  (`:2242-2243`) — "the set of `.beat-marker.<kind>` rules equals exactly {…} and none of ctf's eight
  kinds survives".
- Not blocking: checklist item 14(d) requires CSS for **every kind the page emits** (satisfied at
  `:4310-4334`); it does not forbid unused inherited rules. The four rules are unreachable — the only
  beat builder is `mcBeat` (`:4449`), the game block never calls `markBeat` (asserted at
  `test_minecraft_viewer.nim:106`), and `stepEvents` cannot emit those kinds.

### F8 — `client/replay_broadcast.html` is *not* byte-prefix-identical to the starter up to the banner, and test 39 does not assert that it is
- Where: first byte divergence at `client/replay_broadcast.html:652` (`cmp` against the starter);
  fork banner at `:4097`, starter banner at `coworld-ctf/client/replay_broadcast.html:4344`.
- Observed: `diff` of the two prefixes is 65 removed / 312 added lines, and every hunk is one of the
  note's own enumerated removals or relabels — `.fpv-hp`/`.fpv-gear` CSS (`:652-674` in the starter),
  `.fpv-map` CSS (`:683-703`), `#povBadge` markup, `#fpv-hp`/`#fpv-gear`/`#fpv-map`/`#fpv-map-canvas`
  markup, `renderFpvHud`/`renderFpvMap`/`fpvMap*` JS (~185 lines), the four-team art loops reduced to
  `['red']`, the spectator-string relabels, and the `PB_` → `MC_` rename of the splice hook. Size:
  244 364 B vs the starter's 234 070 B — the page grew, and the block is 867 lines.
- Note: test 39 (`design.md:2235-2238`) — "the file begins with the starter's bytes up to the
  documented splice marker … and only appends after it". The shipped test
  (`tests/test_minecraft_viewer.nim:44-73`) instead asserts `prefix.len > 200_000`, `block1.len <
  prefix.len`, 48 starter ids present, `relayout()` and the four `setProperty` calls present, and
  12 `broadcast_core` procs present by name.
- Not blocking: checklist item 14 asks for "the starter's page with a game block appended … sections
  1–5 present and unmodified **except for the removals the note lists**", which is what I observe.
  Provenance is not in doubt: `client/chrome_common.js` is byte-identical (sha256
  `7ace7287…72f7c`, 40 022 B, `diff` clean), and `client/broadcast_core.js` differs from the starter's
  by exactly **one added line** (`:49`, the `MINECRAFT_WIRE` lookup).

### F9 — `broadcast_core.js` has none of the eight draw functions the note says were added to it
- Where: `client/broadcast_core.js` — the whole file is the starter's plus one line (`:49`). Grep finds
  no `drawBlocks`, `drawShafts`, `drawCog`, `drawFog`, `drawAgentView`, `drawLadder`, `drawStrata`,
  `drawInventory` anywhere in the repo.
- Note: `design.md:1616-1617` — "Deleted: every ctf-specific draw call and the raycast FPV pipeline …
  Added: `drawBlocks`, `drawShafts`, `drawCog`, `drawFog`, `drawAgentView`, `drawLadder`, `drawStrata`,
  `drawInventory`."
- What shipped instead: the board is composited server/wasm-side into sprite-protocol packets
  (`src/minecraft/global.nim`, `buildBoardPacket` via `replay_runtime.nim:36`) and the gutter panels
  are DOM, built by the appended block (`replay_broadcast.html:4489+`). This is *more* faithful to
  item 14 (the camera/zoom/minimap block is verbatim rather than "kept and pinned"), which is why I
  file it as an observation rather than a defect.

### F10 — the wall-clock `stop` is applied on both paths, but `endRule = tickCap` is unreachable and `turnCap` is stamped on the tick-cap path
- Where: `src/minecraft/sim_state.nim:398-403` —
  `if sim.phase == Playing and sim.gameTicksElapsed() >= sim.config.maxTicks: let rule = if
  sim.turnsPlayed >= sim.config.maxTurns - 1: EndRuleTurnCap else: EndRuleTickCap`.
- Observed: `noteTurnEnd` (`:405-409`) increments `turnsPlayed` **after** each turn and itself ends the
  episode at `maxTurns`, and an interrupted turn consumes fewer than `turnTicks` ticks, so
  `gameTicksElapsed()` can only reach `maxTicks` on the last tick of turn `maxTurns`, where
  `turnsPlayed == maxTurns - 1` → `turnCap`. `tickCap` is therefore dead in practice, which matches the
  note's own words ("Reachable only if no turn ever interrupted, in which case it coincides with the
  turn cap; it is kept as an independent guard", `design.md:520-522`). The test acknowledges it:
  `tests/test_minecraft_replay.nim:151` asserts `endRuleText() in [EndRuleTickCap, EndRuleTurnCap]`.

### F11 — record → re-derive is exercised for four of the six end rules, not six
- Where: `tests/test_minecraft_replay.nim:115-132` round-trips `turnCap`, "diamond", `wallClock`,
  `fault`. `death` and `tickCap` are checked in-sim at `:134-152` **without** writing and re-parsing a
  replay. The case labelled "diamond" uses `standardConfig(8)`, and seed 8 ends `turnCap`
  (`python3 tools/replay_summary.py tests/fixtures/cert_seed_8.replay` → `endRule turnCap, rungs 9`),
  so the diamond end rule is not round-tripped either; the committed `diamond_seed_5.replay`
  (`endRule diamond, rungs 11, 623 ticks`) is exercised by `tools/wasm_replay_smoke.cjs` in CI, not by
  a record → re-derive equality test.
- Note: test 30 (`design.md:2192-2194`) — "for `diamond`, `death`, `turnCap`, `tickCap`, `wallClock`
  **and** `fault`, record an episode and re-derive it from the bytes; assert identical hashes at every
  tick **including the stop tick**".
- Not blocking: checklist item 2 is satisfied — the round-trip that does run asserts the hash chain
  tick by tick (`hashMismatchTick == -1`, `not hashValidationFailed`, `:130-132`), and the load-bearing
  `stop` record is applied by the same proc on both paths (`replays.nim:104-130`, `:201-213`).

### F12 — the server starts the episode when the joined seat never registers; the note says it refuses
- Where: `src/minecraft/server.nim:575-595` — on `lobbyTicks >= lobbyJoinTimeoutTicks` it logs
  `ERROR: seat 0 …`, calls `declarePlayerFailure(0, …)`, sets `deadSeats[0]`, and then writes
  `startRecord()` and starts the game on the `miner` baseline.
- Note: `design.md:1292-1293` (named edit 2) — "the server **logs loudly and refuses to start the
  game** when the joined seat has no register record (the grf-football 2026-08-27 silent-default
  scar)". §Tests 27 (`:2183`) repeats it, while also requiring the same scenario to "produce a finished
  episode inside the wall-clock budget" — the note asks for both, and the implementation chose the
  latter. It is loud, not silent, and it is bounded, so nothing in item 5 is falsified.

### F13 — `MaxReplyBytes` is enforced in runes, not bytes
- Where: `src/minecraft/llm.nim:206` `result = text.truncateRunes(MaxReplyBytes)` with
  `MaxReplyBytes* = 4096` documented as "Bytes read from the provider before parsing"
  (`sim_types.nim:49-50`).
- Note: `design.md:825` — "whole reply | **bytes** | ≤ 4096 read from the provider before parsing".
  4096 runes of 4-byte codepoints is up to 16 KiB. The cap is still rune-safe (item 9 is about rune
  boundaries and is satisfied), so this only widens a size bound.

### F14 — the attempt-2 failure also logs "will retry"
- Where: `src/minecraft/decide.nim:209-210` — `echo "minecraft llm: seat ", seat, " attempt ",
  attempt + 1, " failed, will retry: ", error.msg` runs inside the `except` for **both** attempts;
  the genuine second failure additionally logs `falling back to miner (…)` after the loop at
  `:234-235`, and every failure writes a `fallback` chat record (`:206`, `:232`).
- Note: `design.md:654-655` — "The attempt-1 notice says **`will retry`**; only a genuine second
  failure logs **`falling back`**". The phase-60 grep target (`falling back`) is present and correct;
  the surplus "will retry" on attempt 2 is cosmetic. Item 8 (retry once, then scripted, fallback
  recorded) is satisfied.

### F15 — `stepEvents` can emit only 10 of the 16 declared kinds, and test 47 asserts a subset rather than equality
- Where: `src/minecraft/broadcast.nim:34-37` declares 16 kinds; `stepEvents` (`:66-127`) emits
  `milestone`, `descend`, `ascend`, `mine`, `place`, `smelt`, `craft`, `lava`, `death`, `end` — never
  `turn`, `plan`, `say`, `fallback`, `bridge`, `blocked`. `tests/test_minecraft_events.nim:66-68`
  asserts `kind in expected` (subset) plus the presence of three kinds, not set equality.
- Note: test 47 (`design.md:2261-2263`) — "the set of kinds `stepEvents` can emit **equals exactly**
  the sixteen". Downstream: the block's feed cases for `bridge` (`:4839`) and the plain-language lines
  the note promises for mining/crafting/blocked (`design.md:1770-1774`) can never fire; `craft`
  renders as the generic `CRAFTED SOMETHING` (`:4844`).

### F16 — small divergences in the generator's post-pass and the driver, each traced
- `src/minecraft/world.nim:308` — `floorCells = ((size-2)*(size-2)*78) div 100` = **702**, where
  `design.md:250-252` says "below **700** … until it is 700. A level is always at least 78 % diggable".
  78 % of 900 is 702; the two numbers in the note disagree with each other and the code took the
  percentage. Unreachable either way (see F4).
- `src/minecraft/world.nim:282` — the tree-scatter loop skips cells with
  `chebyshev(x, y, spawn) <= 1`, a condition `design.md:240-243` does not state (it protects the forced
  grass 3×3 at spawn).
- `src/minecraft/driver.nim:44-48` + `world.nim:440-441` — a `goto` whose target **is the cog's own
  cell** returns zero steps and is therefore counted in `macrosUnreachable`. `design.md:415-416` scopes
  `unreachable` to "a `goto` whose target is not reachable through known walkable cells".
- `src/minecraft/sim_state.nim:224` — `gameHash` also mixes `cog.alive`, which is not in the note's
  fixed mix order (`design.md:1216-1220`). Deterministic and mixed identically on both paths, so the
  hash chain is unaffected.
- `src/minecraft/agent.nim:267` — `doCraftPickaxe` sets `outcome.crafted` but never
  `outcome.craftedItem`, so the tier-2 `Craft` event's payload for a pickaxe carries the enum's default
  item. `SimEvent` never enters `gameHash` (`sim_state.nim:101-108`), so this is a reporting nit.

### F17 — `results.llmTurns` / `fallbackTurns` are arrays; the note's results document shows scalars
- Where: `src/minecraft/roster.nim:128-130, 186-187` build them per seat;
  `coworld_manifest_template.json` declares both as `{"type":"array","items":{"type":"integer"},
  "minItems":1,"maxItems":1}`.
- Note: `design.md:1402-1403` — `"llmTurns": 47, "fallbackTurns": 1`.
- Not blocking: code and `results_schema` agree exactly (I diffed the key sets programmatically —
  zero schema-only and zero code-only keys), and `tests/test_minecraft_engine.nim:203-214` asserts that
  equality, so item 10's "manifest validates" is not at risk from this.

### F18 — the certification fixture's seed is 8, not the note's 42, and the seed change is what forced the fixture regeneration
- Where: `coworld_manifest_template.json` `certification.game_config.seed: 8`;
  `docs/PORTING-MINECRAFT.md:186-196`; `tools/probe_seeds.nim` is the committed probe.
- Note: `design.md:2007` pins `"seed": 42`, and test 26 (`:2176-2179`) names seed 42.
- The shipped test is **stronger** than the note here: `tests/test_minecraft_engine.nim:220-236` reads
  the seed out of the manifest and asserts ≥ 7 rungs, `deepestLevel >= 2`, ≥ 400 ticks, ≥ 1 craft,
  ≥ 1 place, ≥ 1 ore mine, ≥ 1 dig-down and ≥ 1 blocked event against **whatever the manifest
  declares**, so the two cannot drift. The committed fixture confirms the properties: seed 8 →
  9 rungs, 960 ticks, `z=2`, `reason complete`. No checklist item names the fixture seed.

### F19 — `game.docs` and `game.protocols` use `{"type":"uri"}`; checklist item 10 spells the shape with `"type":"text"`
- Where: `coworld_manifest_template.json` — `game.docs.readme = {"type":"uri","value":".../README.md"}`,
  four `pages` each `{"id","title","content":{"type":"uri","value":…}}`; `game.protocols.player` and
  `.global` both `{"type":"uri","value":".../docs/PROTOCOL.md"}`.
- Item 10's literal text is `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":
  {"type":"text","value":…}}]}`. The design note explicitly prescribes `uri` for every one of these
  (`design.md:1929-1935`), and `tests/test_minecraft_manifest.nim:43-49` asserts `uri`.
- I record this as an observation, not a blocking finding: the **structure** item 10 names (readme +
  pages with `id`/`title`/`content`; both protocol keys as objects) is present, and note and checklist
  disagree on the discriminator. See "Could not determine" for what would settle it.

### F20 — test 27's closed-payload assertion is tautological, and no test drives the socket path
- Where: `tests/test_minecraft_engine.nim:267-270` builds
  `let payload = %*{"failed_policy_index": 0, "message": "never joined"}` and then asserts that the
  literal it just built has two keys — it never touches `declarePlayerFailure`
  (`src/minecraft/server.nim:187-199`, which does emit exactly those two keys).
- Note: test 27 (`design.md:2180-2183`) asks for "exactly one closed-schema
  `{"message","failed_policy_index"}` failure payload" from a seat that connects and never answers and
  from one that never connects. What is tested is the no-credentials LLM seat instead, and
  `docs/PORTING-MINECRAFT.md:177-183` (§F) states the socket path is covered by `docker_smoke.sh`.

### F21 — the note's "reference solver" test is a reachability flood, and its tick bound is unasserted
- Where: `tests/test_minecraft_world.nim:97-140` floods each level from spawn through every
  non-bedrock non-lava cell and asserts a tree / coal / iron / diamond is reachable over 60 seeds ×
  both variants.
- Note: test 3 (`design.md:2082-2085`) asks for "a search-based reference solver … reaches `diamond`"
  **and** "the reference solver's tick count is ≤ 500 on `standard` and ≤ 420 on `deepcut`, which is
  what makes those deadlines honest". No tick bound is asserted anywhere in the tree. Related:
  `tests/test_minecraft_driver.nim` §24 runs 50 seeds × 2 variants where the note says 100.

---

## Traced and consistent

Checklist, item by item, from the code at this sha:

- **1 (CI green).** `gh run list -R Metta-AI/cogame-minecraft --branch main -w ci.yml` → run
  **33242187530**, `success`, at `c1acf21`; all three jobs green; every `wasm-viewer` step ran
  (no skips, no `continue-on-error`). The "no test loosened" half is F1.
- **2 (replay re-derivation).** `src/minecraft/replays.nim:184-199` (`stepReplay`) applies this tick's
  control records, runs the recorded primitive through the **same** `sim.step`, then
  `checkReplayHash` (`:168-182`) compares `sim.gameHash()` against the recorded per-tick hash and
  latches `hashMismatchTick`. `tests/test_minecraft_replay.nim:122-132` asserts the chain is intact for
  every recorded end reason, and `:263-285` asserts two independent re-derivations and a
  seek-and-return land on the same `gameHash`. The viewer draws from that same re-derivation:
  `replay-viewer/minecraft_replay.nim:41-44, 95-101` renders `buildReplayViewerPacket` off the
  re-simulated `SimServer` — there is no parallel recording of display state.
- **3 (static viewer).** `coworld_manifest_template.json` `game.replay_viewer = {"bundle":
  "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode **100755**
  (`git ls-files -s`), `docker cp …/workspace/minecraft/replay-viewer/dist/.` at `:57`; `ci.yml`'s
  `wasm-viewer` invokes it by path. The only `/client/replay` route is the developer-local one
  (`server.nim:297-305`) and it is never declared to the platform. `viewer_smoke.mjs` served the bundle
  from a local static server; nothing but the replay URL is fetched.
- **4 (both name spaces).** Agents see the alias only: `observe.nim:238` `"you": seatAlias(0)`, and
  nothing in `observationJson` carries `realName`. Spectator side gets the real name:
  `roster.nim:121` (`results.names`), `server.nim:509` (join record),
  `broadcast.nim:136-138` (`roster[].name`/`pol`), drawn at `replay_broadcast.html:4716-4719`.
  `showPlayerLabels: false` in both variants.
- **5 (degrade-never-hang).** Every wait is bounded and I traced each: attempt 1 `attempt1Ms`
  (`decide.nim:168-169, 185-186`), one retry `retryMs`, outer `turnBudgetMs` checked before each
  attempt (`:163`), `turnSpacingMs` floor as a bounded `sleep` of at most 2600 ms (`:150-153`), rolling
  60 s rate guard ≤ 28 (`:86-94`, `RateGuardCeiling` `:47`), budget guard switching the LLM off when
  `elapsed + 2×ceil(turnBudgetMs/1000) > wallClockBudgetSeconds` (`:108-116`), the engine's hard stop
  at the top of every loop iteration (`server.nim:471-481`), `lobbyJoinTimeoutTicks` paced at 24 fps by
  `runFrameLimiter` (`:361-374`, fast-forward disabled outside `Playing`), and a bounded 20 s shutdown
  grace (`:758-764`). Worst case per turn ≈ 2.6 + 6 + 3 s; the budget guard fires at 640 s and the hard
  stop at 660 s, +20 s grace = 680 s < **720 s** (60 % of `episode_timeout_minutes: 20`). No unbounded
  loop or blocking read on the game loop; mummy serves on its own thread (`server.nim:358-359`).
  Empirically, `docker-smoke` finished a whole episode in 23 s.
- **6 (`num_agents`).** `num_agents: 1` inside `game_config` of **both** variants and of
  `certification.game_config`; absent at every variant top level; `certification.players` and
  `certification.game_config.players` both length 1. `tools/ci/docker_smoke.sh` is the template
  byte-for-byte apart from the three substitutions (`diff` against
  `templates/tools/ci/docker_smoke.sh` = 5 hunks, all comments/defaults), so the four SEAT-COUNT
  invariants are the template's. `SMOKE_SEATS` = `1`. No `SEAT-COUNT FAIL` anywhere in the run log.
- **7 (scripted baseline plays legally).** `tests/test_minecraft_engine.nim:192-216` runs an
  all-scripted episode to its natural end and asserts `reason == "complete"` plus the seven results
  identities; `tests/test_minecraft_manifest.nim:144-167` repeats it for **both** variants and the
  fixture. `tests/test_minecraft_driver.nim:67-118` bounds 600 baseline replies (≤ 12 actions, every
  `n` inside its per-verb range, `goto` inside 0…31, no `say`/`notes`, ≤ 1024 serialised bytes, expanded
  queue ≤ `turnTicks`, never steps onto known lava). Parameters are swept, not guessed:
  `tools/tune_baselines.nim` + `tools/ci/baseline_tuning.json` + `ci.yml`'s
  `tune_baselines.nim --check` step + `tests/test_minecraft_driver.nim:255-268`.
- **8 (LLM reply handling).** One parallel batch per turn through the starter's path —
  `decide.nim:170-186` builds a `RequestBatch`, `batch.post(...)` per open seat, one
  `engine.client.curl.makeRequests(batch, …)`; with one seat that is a batch of one, and there is no
  sequential per-seat call anywhere. Tolerant extraction: `directives.nim:88-127` (outermost balanced
  `{…}`, fence- and prose-tolerant, first-brace/last-brace fallback), prefill re-prefixed
  (`llm.nim:164-170`). Retry exactly once (`decide.nim:160` `attempt < 2`), then
  `engine.minerFallback` (`:222-235`), which is literally `minerPlan` (`:74-79`) — asserted identical
  to the published baseline at `tests/test_minecraft_driver.nim:155-170`. Every fallback writes a
  `fallback` chat record with a cause from the note's enum and increments `results.fallbackTurns`
  (`server.nim:626`).
- **9 (rune-safe truncation).** `truncateRunes` (`sim_types.nim:328-335`) is the single truncation
  point; `sanitizeSay`/`sanitizeNote` (`directives.nim:57-74`), the policy label
  (`:257`), `fallback.detail` (`:268`), provider error text (`llm.nim:181, 189, 195, 206, 210`) and
  `stopDetail` (`roster.nim:189`) all go through it. `tests/test_minecraft_driver.nim:238-249` feeds
  400/900 4-byte emoji, asserts `runeLen == 160/400`, `validateUtf8() == -1` and
  `say.len == 160*4`; `tests/test_minecraft_replay.nim:223-260` runs `replay_summary.py` over a replay
  whose caps are filled with emoji and asserts strict-UTF-8 JSON with no lone surrogate.
- **10 (manifest validates).** `game.docs` has `readme` + 4 `pages` each with `id`/`title`/`content`;
  `game.protocols` carries **both** `player` and `global` as objects. See F19 on `type`.
- **11 (legible at 360 px).** `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden;
  text-overflow: ellipsis }` at `replay_broadcast.html:4129-4134`; labels hidden under the starter's
  `.tiny` threshold (`#stage.tiny .plate .lives-label { display: none }`, `:4368`; `relayout()` toggles
  `.tiny` at `boardW <= 620`, inherited). Both gutter arithmetics are present and asserted
  (`:4380-4392`, `test_minecraft_viewer.nim:186-191`).
- **12 (release order and scaffold).** `coworld-release.yml`: Build manifest (`:159`) → Certify
  (`:173`, `--timeout-seconds 300`, asserts the STATIC bundle marker) → **Upload the policies**
  (`:216`) → Upload the Coworld (`:314`) → Put the Coworld secret (`:410`). All three workflows
  present; `coworld-release.yml` and `coworld-submit.yml` are the templates with only the slug/image
  substitutions (`diff` = 4 and 1 comment hunks). `docker_smoke.sh` and `build_replay_viewer.sh` are
  mode 100755. `tools/ci/policies.json` has four policies, one image, `run: /bin/minecraft-player`:
  `minecraft-obtaindiamond` (`PLAYER_PROMPT`, 2413 chars), `minecraft-branchminer` (`PLAYER_PROMPT`,
  2057 chars, **`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`**), `minecraft-miner`
  (`PLAYER_SCRIPTED=miner`), `minecraft-scrounger` (`PLAYER_SCRIPTED=scrounger`). The placeholder gate
  runs in `ci.yml`'s "Chrome provenance and scaffold assertions" step and was green; it builds the
  pattern with `printf` so it cannot match itself.
- **13 (viewer executes).** `wasm-viewer` `needs: docker-smoke` and loaded the replay that job
  produced; step 11 printed `{"loaded":true,"ms":351,…}` and
  `soak: 10s of playback kept advancing`. Markers: `data-replay-loaded="true"` set on `<html>` in the
  `'loaded'` branch of `onWorkerMessage` (`static_replay.js:158-161`), posted by the Worker only after
  `ingestPacket()` handed BroadcastCore a frame (`static_replay_worker.js:63-72`);
  `data-replay-error` in `showFailure()` (`static_replay.js:14-20`). Both are the starter's own paths —
  the two shell files differ from coworld-ctf's by **2** and **14** identifier-rename lines only
  (`diff`). Link flags and bootstrap are the same starter: `config.nims` has no `MODULARIZE` and no
  `EXPORT_NAME`, the Worker does `var Module = {}` / `Module.onRuntimeInitialized = …`
  (`static_replay_worker.js:8, 188`) and `importScripts('./wire_constants.js', './broadcast_core.js',
  './minecraft_replay.js')` (`:239`) — a matched non-modularized pair, asserted at
  `tests/test_minecraft_viewer.nim:205-235`. **Playback opens at the game start**:
  `initReplayRuntime` seeks to `replayStartTick()` before the first frame
  (`replay_runtime.nim:26-28`), `startTick` is the first tick at which `phase == Playing`
  (`replays.nim:284-287`), and it is shipped to the chrome as `st` (`broadcast.nim:258`), which the
  block uses for the scrubber axis (`replay_broadcast.html:4437-4441`). The lobby cannot produce frozen
  frames here at all: `sim.tickCount` only advances inside `sim.step`, which the server calls only in
  `Playing` (`server.nim:602-644`), so a lobby of any `lobbyJoinTimeoutTicks` records zero ticks and
  every lobby record carries `tickTime(0)`. (Inference from the code, not from a late-gameStart
  recording — see "Could not determine".)
- **14 (chrome is the starter's).** `client/chrome_common.js` byte-identical (`diff` clean, sha256
  matches the note's pin). Transport rules: (a) `relayout()` sets `--hudscale`, `--topband`, `--band`
  on `var root = document.documentElement` (`replay_broadcast.html:4042, 4063-4069`); (b) nothing
  fixed-positioned in the block — `position: fixed` appears nowhere in it (asserted,
  `test_minecraft_viewer.nim:174-175`), and `#mc-left`/`#mc-inv` anchor with
  `bottom: calc(var(--band, 0px) + …)` (`:4177-4180`); (c) `#endcard { bottom: var(--band, 0px) }`
  (`:992-1013`), shown with `#endcard.on` (`:1014`), removed on every seek by the inherited
  `$('endcard').classList.remove('on')` path; (d) beats are labelled `<button>`s with `title`,
  `aria-label` and a click handler that sends `s:<tick>` (`:4449-4477`), with CSS for exactly the five
  kinds emitted (`:4310-4334`). `#viewpanel` is **kept**, correctly: each level is 32×32 cells at 24 px
  = 768 px against a 15-cell camera, so the board is genuinely pannable
  (`design.md:1646-1651`); the panel, `#minimap`, `#zoombar` and `core.attachMinimap($('minimap-canvas'))`
  (`:3952`) are all present.
- **15 (drawn strings fit).** `--strict-text-bounds` is on the smoke step and the job is green with
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`. There is
  no `fillText`/`strokeText` in `client/replay_broadcast.html` or `client/broadcast_core.js` at all, so
  every string is DOM or a gutter panel — consistent with `design.md:1816-1820`. See F6 for the
  fixture's harness and F2 for the untested narration path.
- **Parallel batch per turn.** One seat, one batch, one request; `decide.nim:170-186`. No sequential
  loop of provider calls anywhere.

Other things I read and found consistent with the note:

- The seventeen primitives and their exact effects: `agent.nim:284-331` against `design.md:260-312`
  — blocked move is a **turn** (`:98-121`), `mine` respects `mineTier`/`dropOf`/`becomes`
  (`:122-143`, tables at `sim_types.nim:241-269`), `place_block` only fills lava/water and only then
  spends the cobblestone (`:202-222`), table 4 planks / furnace 8 cobblestone onto grass|sand|tunnel
  (`:224-245`), recipes and their Chebyshev-1 same-level adjacency (`:89-96, 247-282`), crafting an
  owned pickaxe is a free no-op (`:249-250`), stack cap 64 (`:55, 77-78`).
- `dig_down`'s six cases in the note's order: `agent.nim:145-192` — `z == levelCount-1` →
  `bedrock_floor`; existing shaft → free descent, no drop; lava below → floor breaks, cog does **not**
  move, the cell is permanently revealed via `observeCell`, `lava_below` + `brokeOntoLava`; bedrock →
  `unmineable`; tier → `no_tier`; else collect, write `tunnel`, set `shaftDown`, descend keeping facing.
- The tick loop's numbered order: `sim_state.nim:289-403` — 1 `inc tickCount`; 3 apply + counters +
  events; 4 `evaluateMilestones` (predicates over sim state only, `:235-258`); 5 visibility with the
  depth-dependent radius plus the one cell through a shaft down and up (`:362-372`); 6 death; 7 diamond;
  8 interrupt on a newly-known adjacent lava (`:260-282`, including the cell below/above at the same
  x,y, which is what makes a `dig_down` breakthrough interrupt); 9 the hash is written by the caller
  (`server.nim:652`). Step 2's "empty queue → `noop`" is `server.nim:637-641`, and the turn still costs
  its 20 ticks.
- Scoring: `milestones.nim:34-70` — `milestoneScore` is the 11-bit mask, `speedBonus = maxTicks -
  deepestTick` (0 when nothing unlocked), `episodeScore = 1000 * mask + speedBonus`, min 0, max
  2 047 959. `roster.nim:87-203` writes all 55 results keys; the key set equals the manifest's
  `results_schema` exactly (verified programmatically: 0 schema-only, 0 code-only) and
  `tests/test_minecraft_engine.nim:131-189` asserts all seven identities.
- Observation hiding: `observe.nim` never reads `config.seed`, `parMilestones` or any noise field;
  `region` is the current level only (`:224-226`), `known_ore` is capped at 24 and sorted by
  `z`, then `d` (nulls last), then `(y, x)` (`:141-146`), `column.visited` is `z <= deepestLevel`,
  `nearest` always carries all twelve keys (`:107-115`).
- Seed handling: `src/minecraft.nim:44-63` randomises before `config.update` and strips an unpinned
  seed so the world follows the final value; the seed is in the replay config
  (`sim_config.nim` `configJson`) and in `results.seed`.
- Player registrar: `src/minecraft_player.nim` — bounded dial (240 × 500 ms), registration re-sent for
  the first ~10 s of frames (`:125-128`), prompt rune-truncated at 4000 and label at 64 (`:41-54`),
  `quit(0)` on a dead socket (`:141`).
- Server contract: `/healthz` (`server.nim:227-231`), `/player?slot&token` with the token check that
  **closes** on a mismatch (`:150-162, 238-244`), `/global` refusing player credentials (`:261-264`),
  the `Ping → Pong` branch verbatim and no `kind != TextMessage` guard (`:327-347`),
  `declarePlayerFailure`'s exactly-two-key payload (`:187-199`), registration interception that holds
  an unappliable registration and writes a **redacted** `register` record (`:518-551`, asserted at
  `test_minecraft_replay.nim:181-183`).
- Replay self-sufficiency: header + resolved config JSON + join + per-tick primitives + chat records +
  one hash per tick; `tests/test_minecraft_replay.nim:157-195` asserts all 33 config keys, the real
  name in the join, and register/directive/result records present.
- Docs: `docs/{RULES,ACTIONS,MILESTONES,PROTOCOL,PORTING-MINECRAFT}.md` all present; `RULES.md:149-176`
  ships the note's worked example with `scores[0] = 255 648`.

---

## Could not determine

- **Whether the platform accepts `game.docs`/`game.protocols` entries typed `"uri"` (F19).** The only
  gate that would settle it is `coworld certify` / `validate_upload_manifest`, which runs in
  `coworld-release.yml:159-215` — a workflow that has not run at this sha (no release run exists).
  `ci.yml` does not install the `coworld` CLI. What would settle it: a `coworld-release.yml` run whose
  "Build the Coworld manifest" and "Certify locally" steps are green, or the platform schema itself.
- **Whether playback would still open at the game start on a replay with a LATE `gameStart`.** I could
  not produce one: on this codebase the lobby consumes zero recorded ticks (`sim.tickCount` advances
  only inside `sim.step`, called only in `Playing` — `server.nim:602-644`), so a large
  `lobbyJoinTimeoutTicks` with no joining seat still yields `st == 1`. I therefore verified the
  mechanism by reading (`replay_runtime.nim:26-28`, `replays.nim:284-287`, `broadcast.nim:258`) rather
  than by recording. One residual, observed: `seekReplay` clamps to `[0, maxTick]`
  (`replays.nim:225`), **not** to `[startTick, maxTick]`, so a back-step or a 0 % scrub click can land
  on tick 0, one frame before the game starts. Item 13 asks for every seek to be clamped there. With a
  zero-tick lobby this is at most one frozen frame, which is why I did not file it as a finding; a
  recording whose lobby genuinely spans ticks would settle whether it matters.
- **Whether `results.reason == "deadline"` is reachable in production.** The wall-clock stop path is
  exercised synthetically (`test_minecraft_replay.nim:118`) and maps to `ReasonDeadline`
  (`replays.nim:123-128`); whether the budget guard always beats it needs a hosted run with a live
  provider. CI cannot show it — `docker_smoke.sh` runs without an API key, so every turn is an instant
  no-credentials fallback.
- **Whether the `miner` baseline reaches rung 9 on the majority of `standard` seeds at the shipped
  parameters.** `tests/test_minecraft_driver.nim:290-296` asserts it over 50 seeds and the `test` job
  is green, so this is verified by CI rather than by me; I did not re-run the sweep (no Nim toolchain
  in this sandbox).
