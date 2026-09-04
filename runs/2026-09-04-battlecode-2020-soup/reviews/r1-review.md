# r1 review — battlecode-2020-soup (the `bc20` year module)

Range: `abc92ce3d7005eac6dc7bebae0e3b007033c0fd4..551c5427e3b88deedfc7155c41a18f193c0ff6c9`
(merge of PR #1 into `main`, repo `Metta-AI/cogame-battlecode`, cloned fresh at that sha)
Files read: 71 of the 104 the diff touches (all Nim under `src/` and `tests/`, `client/replay_broadcast.html`,
`replay-viewer/*`, `coworld_manifest_template.json`, `.github/workflows/ci.yml`, `tools/ci/*`,
`tools/oracle/*`, `docs/RULES-BC20.md`, `NOTICE`), plus the pre-existing files the diff changes semantics
around (`sim_types.nim`, `abc92ce:src/battlecode/sheet.nim`, `abc92ce:src/battlecode/replay.nim`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the parallel-batch rule).
Design note: `runs/2026-09-04-battlecode-2020-soup/design.md`. Build report:
`runs/2026-09-04-battlecode-2020-soup/build-report.md`.

## Summary of findings

| # | one line |
|---|---|
| F1 | The renderer fixture's bc20 row measures the *hidden bc26* `#doctrines` for the "panel may not own the board" check, and its `canvas_text` line is `total: 0` — which checklist 15 itself calls "not evidence of anything". |
| F2 | `drone_water_drop`'s `victim_alias` is always the opposing clan, but the event is emitted for *any* unit dropped into water, including a friendly unit or a neutral cow. |
| F3 | The recorded observation payload carries no `rules_digest` and no `sheet_schema` key; both contents ship in the system preamble instead, recorded once as `prompt_preamble`. |
| F4 | `flood_table["7"]` is `1501` (the "beyond the table" sentinel), where the note's payload shows `1546`. |
| F5 | The `chassis`-was-submitted log line says "the clan runs the awu chassis" on a bc20 episode too. |
| F6 | The bc20 miner's build order inserts a Refinery second and places net guns at Chebyshev 2, not "on the HQ ring" as §Decisions specifies; the Chebyshev-2 move is documented, the early Refinery is not. |
| F7 | `fulfillment.nim`'s header claims it builds "always when `NEED_DRONES` is on the chain"; no such branch exists and `readBlocks` ignores `SigNeedDrones`. |
| F8 | `test_bc20_replay.nim`'s "record → re-derive covered every end reason" is satisfied by literal string appends for `broadcasts`/`highest_id`/`coin_flip` and unconditionally for `abandoned`; only `quantity` and `hq_destroyed` are really re-derived. |
| F9 | Two knob-teeth gates (`opening`, `rush_trigger`) assert a different statistic than the note's table; only the third substitution (`net_gun_ring`) is declared as a deviation. |
| F10 | A non-flying unit that moves onto a flooded tile is **destroyed** rather than the move being refused; the note's rule 6.1 says nothing but a drone may enter one. Not in §Divergences. |
| F11 | Four stale in-tree references: `tests/test_bc20_constants.nim`, `tools/ci/check_bc20_maps.sh` (neither exists), "Measured at GameVersion GV04" (the tree is GV05), and `tools/ci/check_gameversion.sh` is fixed here but wired into no workflow. |
| F12 | `SeatPolicy.baseline` is now written once and never read — vestigial after the year-aware baseline resolution. |
| F13 | §Tests item 17's "committed bc20 fixture replay" does not exist; the wasm smoke runs against the docker-smoke bc20 replay instead. |
| F14 | The `first_build` unit vocabulary emits `delivery_drone` (and `miner`/`hq`), where the note's event table lists `drone` and six kinds. |
| F15 | The build report's "the bc26 variant … byte-identical to `main`'s" is true after JSON decoding but not at the byte level: the variant `name` lost its `\u2014` escape. bc26 semantics are unchanged. |

## Blocking

**None.** I could not find anything in this diff that falsifies a named acceptance-checklist item.
Every item I could evaluate from the tree or from cited CI evidence is discharged; the evidence for each
is in "Traced and consistent" below. The fifteen findings above are all observations against the design
note or against internal consistency, not against the checklist.

## Non-blocking

### F1 — the worst-case renderer fixture's bc20 row checks the wrong panel, and its canvas gate covers nothing
- Where: `tools/ci/renderer_fixture.html:336`, `:271`, `:308-317`; `client/replay_broadcast.html:2653-2656`;
  CI run 33841592052, job `wasm-viewer`, step "Render the full-cap doctrine-text fixture".
- Observed: the fixture now renders **two** rows (`YEARS = ['bc26','bc20']`, `:86`) × three widths incl. 360 px
  (`:64`), sets `data-year` from the query string (`:174`), and is driven by
  `viewer_smoke.mjs --strict-text-bounds` (`.github/workflows/ci.yml:892-896`). Its verdict function checks,
  in order: that the page CSS actually loaded (`:271-276`, year-aware), that no element under `#chrome`
  escapes the frame (`:288-300`), that no filled readout hides its own content (`:308-327`, year-aware
  selector list that names `#bc20-flood`, `#bc20-soup`, `#bc20-units`, `#bc20-doctrines`), and that the
  strings are still at their caps (`:345-355`, year-aware). Two gaps:
  1. line 336 is `var panel = document.getElementById('doctrines').getBoundingClientRect();` — not
     year-aware. Under `data-year="bc20"` that element is `display: none !important`
     (`client/replay_broadcast.html:2653-2656`), so its rect is 0×0 and the "the doctrine panel may not take
     half the frame height" assertion (`:337-341`) passes vacuously for the bc20 row. `#bc20-doctrines` *is*
     covered by the escape and hidden-content loops, and its body is capped by CSS
     (`max-height: calc(30vh - var(--band, 0px)); overflow-y: auto`, `:2717-2719`), so the panel cannot in
     fact own the board — but the fixture's own statement of that rule is not exercised on the bc20 row.
  2. the step's reported line is `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge),
     0 ellipsized (--strict-text-bounds)`. Checklist 15 says in terms: "`total: 0` means the check covered
     nothing … and is not evidence of anything." Here the reason is benign and *observable*: every
     LLM-authored string in this viewer is DOM text (`#bc20-doctrines-body`, `.plate-sub`), never canvas
     text — the canvas carries only the board sprites (`src/battlecode/render.nim:284-395`). The evidence
     that actually gates is the fixture's DOM verdict, which fails through `data-replay-error` (`:78`).
- Checklist item: 15 ("Every drawn string fits its frame") is the item this is adjacent to. I do **not**
  read it as falsified: the fixture exists, runs in its own `ci.yml` step with `--strict-text-bounds`,
  asserts its own strings are still full length (`:345-355`), and adds a bc20 row at 360 px — which is
  what the item asks for. Recorded so the judge can weigh the `total: 0` line itself.

### F2 — `drone_water_drop`'s victim alias assumes the victim is an enemy
- Where: `src/battlecode/years/bc20/world.nim:737-741` and `:754-758`; `src/battlecode/match.nim:128-132`.
- Observed: `dropUnit`/`dropHeldUnit` emit `w.emit("drone_water_drop", r.id, ord(r.team), ord(dropped.kind))`
  whenever the drop tile is flooded, for **any** dropped unit — the stat counter above it is correctly
  guarded (`if dropped.team != r.team and r.team != teamNeutral`, `:755-756`) but the event is not.
  `match.nim` then builds `{"alias": aliasOfTeam(gameIndex, e.b), "victim_alias": aliasOfTeam(gameIndex, 1 - e.b)}`,
  so a drone that drops its own landscaper or a neutral cow into the water produces a feed line and a
  `drop` beat naming the *other* clan as the victim.
- What the note says: §Event vocabulary, `drone_water_drop | game, round, alias, victim_alias, victim_unit`.
- Consequence: a mislabelled kill-feed line and beat tooltip. Display only — `results.games[].drone_water_drops`
  is unaffected, and the hash chain does not read events.

### F3 — the observation payload has no `rules_digest` / `sheet_schema` key
- Where: `src/battlecode/decide.nim:198-231` (`briefFor`), `:122-180` (`Bc20Preamble`),
  `src/battlecode/replay.nim:129` (`prompt_preamble`), `src/battlecode/years/bc20/maps.nim:242-278` +
  `src/battlecode/years/dispatch.nim:116-119` (the map card).
- Observed: the per-seat payload carries `protocol`, `game_version`, `year`, `slot`, `alias`,
  `opponent_alias`, `team`, `seed`, `games[]` (each with `map`, `width`, `height`, `symmetry`, `you_are`,
  `hq_elevation`, `hq_separation`, `soup_tiles`, `soup_total`, `soup_near_hq`, `cows`,
  `initially_flooded_tiles`, `rounds`), `flood_table`, `scoring` and `budget`. It does **not** carry
  `rules_digest` or `sheet_schema`. The rules digest and the full knob surface with ranges and defaults are
  in `Bc20Preamble` (`decide.nim:131-180`), which every seat receives as the system message and which the
  replay records once at document level.
- What the note says: §Server, player, protocol shows both keys inside the per-seat observation JSON.
- Consequence: content-equivalent, layout different. A consumer reading `prompt.sheet_schema` off a bc20
  replay finds nothing.

### F4 — `flood_table["7"]` is the sentinel 1501, not 1546
- Where: `src/battlecode/years/dispatch.nim:257-262`; `src/battlecode/years/bc20/flood.nim:90-98`.
- Observed: `floodTableJson` fills levels 1…7 from `roundWaterReaches(level)`, which scans the committed
  1501-entry table and returns `WaterTableMaxRound + 1 = 1501` when the water never reaches that level
  inside the cap (`flood.nim:97-98`). Elevation 7 floods at 1546 in the real curve, so the model is told
  `"7": 1501`. Levels 1–6 match the note exactly and are asserted by
  `tests/test_bc20_flood.nim:13-19` (256 / 464 / 677 / 931 / 1210 / 1413).
- What the note says: `"flood_table":{"1":256,…,"6":1413,"7":1546}`.
- Consequence: a doctrine reading the table sees "elevation 7 is at 1501" — beyond the 1499 last played
  round either way, so the plan it implies is the same; the number is wrong.

### F5 — the `chassis`-ignored log line names the bc26 chassis on both years
- Where: `src/battlecode/decide.nim:313-316`.
- Observed: `if "chassis" in result.sheets[slot].unknownFields: echo "… sent \`chassis\`, which is not a
  doctrine knob: ignored, the clan runs the awu chassis"`. The branch is year-neutral; on bc20 the seat
  runs `bowl-of-chowder` (`decide.nim:51-56`).
- Consequence: a misleading operator log line on a bc20 episode. The behaviour (record, never honour) is
  correct and is asserted by `tests/test_bc20_sheet.nim:171-187`.

### F6 — the miner's build order differs from §Decisions in two places, one of them undocumented
- Where: `src/battlecode/years/bc20/chassis/miner.nim:33-46` (`nextBuilding`), `:49-64` (`buildSiteScore`),
  header `:5-11`.
- Observed: the order is Design School → **Refinery** → `net_gun_ring` Net Guns → Fulfillment Center →
  `vaporator_budget` Vaporators → a second Design School after round 600. Sites are scored toward
  Chebyshev 2 from the own HQ (Chebyshev 4 for the Refinery, `:60`).
- What the note says (§Decisions, "Miner"): "1 Design School at Chebyshev 2 …; `net_gun_ring` Net Guns **on
  the HQ ring**; 1 Fulfillment Center; `vaporator_budget` Vaporators …; a second Design School after round
  600" — no Refinery.
- Documentation status: the Chebyshev-2 net-gun move is documented (build report §7 and `miner.nim:8-9` —
  dirt dropped on a building buries it, so a gun on the ring is buried by the team's own wall). The early
  Refinery is explained in `miner.nim:36-40` (a walled HQ is eight elevation steps up and
  `MAX_DIRT_DIFFERENCE` is 3, so miners need a second drop-off) but appears in neither
  `docs/RULES-BC20.md` §Divergences nor the build report's deviation list.

### F7 — `fulfillment.nim`'s stated `NEED_DRONES` behaviour is not implemented
- Where: `src/battlecode/years/bc20/chassis/fulfillment.nim:1-3` and `:11-19`;
  `src/battlecode/years/bc20/chassis/signals.nim:22` and `:59-76`.
- Observed: the module header says "build a Delivery Drone whenever the roster is under `4 + round/300`
  (capped 14) and the pool can pay, **and always when `NEED_DRONES` is on the chain**". `runFulfillmentCenter`
  implements only the roster/pool test. `SigNeedDrones` is declared and named (`signals.nim:22`, `:26-29`)
  but nothing broadcasts it and `readBlocks`'s `case` drops it into `else: discard` (`:76`).
- What the note says: §Decisions, "Fulfillment Center": the same "and always when `NEED_DRONES` is on the
  chain" clause.
- Consequence: one signal code in the table is dead, and a comment describes behaviour the code does not have.

### F8 — the bc20 "every end reason re-derives" coverage check is partly satisfied by literals
- Where: `tests/test_bc20_replay.nim:97-104` (`quantity`), `:106-115` (`hq_destroyed`), `:117-127`
  (`quality`, a world-level ladder vector, no re-derivation), `:129-135` (`broadcasts`, `highest_id`,
  `coin_flip` — three `seenReasons.add("…")` string literals), `:137-173` (`abandoned`, guarded by
  `if reason == epDeadline` with `seenReasons.add("abandoned")` **outside** the branch at `:173`),
  `:175-179` (the coverage loop).
- Observed: the loop at `:177-179` therefore passes even when the deadline branch never fires and when the
  last four reasons were never produced in this shard at all. The comment at `:169-172` says the
  unconditional add is "so the coverage check cannot pass vacuously"; it is what makes it able to.
  The rungs themselves *are* covered by real vectors elsewhere — `tests/test_bc20_scoring.nim:80-147` has
  one block per rung including `broadcasts`, `highest_id` and a determinism check on `coin_flip`.
- What the note says (§Tests item 14): "record → re-derive for **every** bc20 end reason (`hq_destroyed`,
  `quantity`, `quality`, `broadcasts`, `highest_id`, `coin_flip`, and the wall-clock `abandoned`/`deadline`
  stop applied by the same proc on both paths)".
- Checklist item 2 is **not** falsified: record → re-derive frame-by-frame is asserted for the games that
  are played (`:83-86`, `:215-232`, `:300-309` in `src/battlecode/replay.nim` compares **every** round's
  chain), and the abandoned path is compared when it fires (`:164-167`). This is a shortfall against the
  note's own claim, not against the checklist.

### F9 — two knob-teeth gates assert a different statistic than the note's table
- Where: `tests/test_bc20_knobs.nim:100-106` (`opening`), `:164-170` (`rush_trigger`), `:33-38` (the one
  declared deviation), `:19-31` (the measured table).
- Observed:
  - `opening`: the note asks "first enemy-half friendly unit arrives ≥ 200 rounds earlier"; the shard asserts
    `high.reachedEnemyHq >= low.reachedEnemyHq + 1`, i.e. in one more of the four games a friendly unit stood
    Chebyshev ≤ 1 from the enemy HQ within 700 rounds. No round-delta is measured.
  - `rush_trigger`: the note asks "a friendly unit stands adjacent to the enemy HQ **by round 350**"; the
    shard runs 500 rounds (`:166-167`) and asserts the same +1-game counter.
  - `net_gun_ring` drops the note's second clause ("enemy drones shot down up ≥ 3") and says so, in the
    shard header `:33-38` and in build report §4.
  - `wall_hq_round` uses 4 games instead of the note's 6, explained at `:9-13` and in build report §3.
- Consequence: eight of the ten gates match the note's named statistic; two substitute a weaker proxy
  without the shard's own "DECLARED DEVIATION" treatment and without a build-report entry.

### F10 — a ground unit that moves into water is destroyed rather than refused
- Where: `src/battlecode/years/bc20/world.nim:559-587`.
- Observed: `canMove` (`:559-567`) does not test flooding. `move` (`:573-587`) does:
  `if w.isFlooded(center) and not r.kind.canFly(): w.destroyRobot(r.id); return` — the mover dies where it
  stands and does not occupy the tile. The comment (`:574-576`) attributes this to the engine
  ("`RobotControllerImpl.move` … checks the destination for flooding AFTER the legality assert and
  disintegrates the mover").
- What the note says (rule 6.1): "A drone may enter a flooded tile; nothing else may."
- Status: I could not verify the Java behaviour from this tree (the 2020 engine is not vendored, and the
  parity oracle compiles only `GameConstants`, `RobotType`, `Transaction`, `Direction`, `Team`,
  `IDGenerator` — `ci.yml:491-502`). The chassis never plans such a move (`pathing.nim:26-34`,
  `:51` exclude flooded and about-to-flood tiles) and the baselines test asserts no non-flying robot
  is ever standing in water (`tests/test_bc20_baselines.nim:74-76`), so the path is not exercised by the
  scripted play. It is not listed in `docs/RULES-BC20.md` §Divergences.

### F11 — four stale in-tree references
- Where: `src/battlecode/years/bc20/constants.nim:5` ("`tests/test_bc20_constants.nim` regenerates this file
  and byte-diffs it") — no such file exists; the regeneration and byte-diff live in
  `.github/workflows/ci.yml:144-151`. `tests/test_bc20_maps.nim:2` ("checked by
  `tools/ci/check_bc20_maps.sh` in CI") — no such script; `ci.yml:148-149` runs
  `tools/convert_maps_bc20.py --check`. `tests/test_bc20_knobs.nim:17` ("Measured at GameVersion GV04") —
  the tree is GV05 (`src/battlecode/sim_types.nim:16`). `tools/ci/check_gameversion.sh:37-40` is genuinely
  repaired by this diff (`grep -o '"[0-9]*"'` never matched `"GV04"`, so every invocation exited 1) but
  `grep -rn check_gameversion .github/workflows` returns nothing — no workflow calls it.
- Consequence: the underlying gates exist; the pointers to them are wrong, and the repaired version check
  is manual-only. The note (§Determinism) says the script "is kept and claims the version across branches";
  it is kept, and it is not run by CI in this repo either before or after the diff.

### F12 — `SeatPolicy.baseline` is dead
- Where: `src/battlecode/server.nim:45` (the only write, `app.policy[slot].baseline = blAwu` at init),
  `src/battlecode/decide.nim:20-31` (the field), `:47-49` (`baselineForSeat`, which resolves from
  `seat.scripted` per year), `src/battlecode/server.nim:113-117` (registration now stores the raw
  `scripted` string instead of a parsed baseline).
- Observed: nothing reads `.baseline` anywhere in `src/`; the only other mention is a test constructor
  (`tests/test_sheet.nim:274`).
- Consequence: residue from the year-aware change. bc26 resolution is unchanged —
  `baselineFor("bc26", name)` (`baselines.nim:41-44`) maps `scaffold`/`examplefuncsplayer`/`example` →
  `blScaffold` and everything else → `blAwu`, exactly as the removed `parseBaseline` did.

### F13 — no committed bc20 fixture replay
- Where: `tests/fixtures/` contains only `java_random_vectors.json`;
  `.github/workflows/ci.yml:850-856` runs `tools/wasm_replay_smoke.cjs` against
  `dist/smoke/replay.json` and `dist/smoke/replay-bc20.json`.
- What the note says (§Tests item 17): "the emitted wasm module loads under node and answers
  `bc_load_replay`/`bc_frame` on a committed **bc20** fixture replay".
- Consequence: the assertion is made against the replay `docker-smoke` produced in the same run rather than
  a committed fixture — arguably stronger evidence (real current-format bytes), but the named artifact does
  not exist and `tests/test_viewer.nim` cannot run that check natively.

### F14 — `first_build`'s unit vocabulary is the full `RobotKind` set, spelled `delivery_drone`
- Where: `src/battlecode/years/bc20/chassis/kit.nim:174-179` (emits for any kind),
  `src/battlecode/years/dispatch.nim:64-68` (`Bc20UnitNames`), `src/battlecode/match.nim:113-119`.
- Observed: `Bc20UnitNames` is the ten `RobotKind` ordinals in order, so `first_build.unit` can be
  `miner`, `refinery`, `delivery_drone` … The chassis calls `firstBuild` for miner (`hq.nim:91`),
  landscaper (`designschool.nim:29`), drone (`fulfillment.nim:21`) and every building the builder-miner
  puts up (`miner.nim:85`).
- What the note says: `unit` ∈ {`design_school`, `landscaper`, `fulfillment_center`, `drone`, `vaporator`,
  `net_gun`}.
- Consequence: more `build` beats than the note's six kinds, and `drone` is spelled `delivery_drone`. The
  `build` beat kind has CSS (`client/replay_broadcast.html:2743`), so no marker is invisible.

### F15 — "byte-identical" is decoded-identical for the bc26 variant
- Where: `coworld_manifest_template.json` variant `bc26` `name`; build report line 131 ("the bc26 variant,
  its two player entries, its four policies and the certification fixture are byte-identical to `main`'s").
- Observed: a structural JSON compare of `abc92ce` against `551c542` reports **no** change under
  `/variants/0`, `/certification`, `/player/0`, `/player/1`, or any bc26 `results_schema` property; the
  only textual change in the bc26 variant is `"Battlecode 2026 \u2014 …"` → `"Battlecode 2026 — …"`, i.e.
  the file was re-serialised with non-ASCII escapes off. The decoded value is identical.
- Consequence: nothing downstream changes (the platform parses JSON), but the build report's byte-level
  claim is not literally true for that string.

## Traced and consistent

Checklist items, then the design pins the brief named.

**1. CI green, no test loosened.** `gh run list -R Metta-AI/cogame-battlecode --branch main -w ci.yml`:
run **33841592052**, `headSha 551c5427…`, `conclusion: success`, jobs `test`, `parity-oracle`,
`parity-oracle-bc20`, `docker-smoke`, `wasm-viewer` all `success`. No test file was deleted; every change
to an existing test in `git diff abc92ce..551c542 -- tests/` is either a mechanical rename
(`GameOutcome` → `GameOutcome26`, `deriver.world` → `deriver.session.w26`, `mapSha(x)` → `mapSha("bc26", x)`,
`EndReason` → `$EndReason`) or an added assertion. `tests/test_manifest.nim` and `tests/test_viewer.nim`
gained assertions (four doc pages, both variants, eight policies, the bc20 ids, the ten beat kinds, the
shadowing check) and lost none; no `skip`, no widened tolerance, no removed check anywhere in the diff.

**2. Replay re-derivation.** `src/battlecode/replay.nim:284-310` steps the same `Session` the server ran
(`years/dispatch.nim:153-156`) and compares **every** round against
`games[].hash_chain_rounds` (16 hex digits per round, `replay.nim:302-306`), falling back to the final
chain. The chain mixes seven per-team values plus three globals including the water level's float32 bit
pattern split into 16-bit halves for wasm32 (`years/bc20/rules.nim:137-152`).
`tests/test_bc20_replay.nim:83-86, 215-232` re-derive **from the written bytes** and assert
`mismatchRound == -1`, the played round count, and that the re-derived blockchain's mint count equals the
recorded per-team counters. The viewer reads that same re-derivation: `replay-viewer/bc_replay.nim:67-75`
now calls `sessionChromeJson(doc, deriver.session, …)` / `buildSessionPacket(deriver.session, …)`.

**3. Static viewer.** `coworld_manifest_template.json` → `game.replay_viewer.bundle == "static-replay-viewer"`;
`tools/build_replay_viewer.sh` present and `100755` (asserted at `ci.yml:695-706`); no `/client/replay`
route (the only hits are `tests/test_seats.nim:75-78`, which asserts its absence, and a comment in
`coworld-release.yml:220`). Nothing outside `data/` is fetched: the bundle preloads the whole tree
(`replay-viewer/config.nims:46`), including `data/maps/bc20/` and `data/bc20/water_levels.json`.

**4. Both name spaces.** Agents see `alias`/`opponent_alias` only (`decide.nim:198-207`, no `names` key);
real names live in `replay.names[]` (`replay.nim:127`), `seats[].name` (`:70`) and `results.names`
(`results.nim:79`), and are drawn only by the viewer.

**5. Degrade-never-hang.** Registration: `server.nim:239-252`, bounded by `connectTimeoutMs` (25 000 in the
bc20 variant), then plays anyway and reports to `COGAME_PLAYER_FAILURE_URI` (`:260-267`). Doctrine:
`decide.nim:260-341` — at most two attempts, each a single `curly.makeRequests` with
`max(1, deadlineMs div 1000)` seconds, wrapped in a monotonic `doctrineBudgetMs` check (`:263-278`), with a
throttle fast-fail (`:336-341`). Match: `match.nim:163-174` checks `matchBudgetSeconds` before each game and
hands the game `min(perGameBudgetSeconds, remaining)`; `rules.nim:213-226` breaks on the monotonic clock
(sampled every 32 rounds) and on `currentRound < maxRounds`. Worst case
25 + 45 + 320 + write ≈ 390 s < 720 s (60 % of `episode_timeout_minutes: 20`). No unbounded loop found:
`readBlocks` (`signals.nim:52-55`) is bounded by `currentRound` and `opsLeft`; every chassis loop runs over
`MoveDirs` or a sensed window charged against `opsLeft` (`kit.nim:69-74`, `:166-172`;
`pathing.nim:36-48`, `:74-83`).

**Parallel batch.** `decide.nim:281-298` posts one `RequestBatch` containing every open seat and issues a
single `client.curl.makeRequests(batch, …)`. No per-seat sequential call site exists.

**6. `num_agents`.** Present in `variants[bc26].game_config` (2), `variants[bc20].game_config` (2) and
`certification.game_config` (2); absent at every variant top level (asserted
`tests/test_manifest.nim:99-118`). `tools/ci/docker_smoke.sh:137-176` enforces the four invariants
(declared / positive integer / `len(certification.players)` / `len(certification.game_config.players)`) plus
the `SMOKE_SEATS` cross-check, and the new override paths add two more `SEAT-COUNT FAIL` guards
(`:190-194`, `:207-211`). `grep -c "SEAT-COUNT FAIL"` over the docker-smoke log of run 33841592052: **0**.
Both episodes logged `game=battlecode seats=2` and `smoke OK: seats=2 … reason=complete`.

**7. Scripted baseline plays a full episode legally.** `tests/test_bc20_baselines.nim:86-98` plays 466 real
rounds and asserts world invariants every 50; `:52-84` checks on-map, non-negative cooldown, `opsLeft` in
`[0, decisionOps]`, carry limits, one robot per tile, no non-flying robot in water, non-negative pools, and
every pooled transaction `cost > 0` with exactly 7 ints. `:100-152` is the D2 gate: six games,
bowl-of-chowder wins all six with a living HQ, ≥ 6 miners, ≥ 3 landscapers, ≥ 1 design school, ≥ 1
refinery-or-fulfillment-center, ≥ 2 net guns, ≥ 90 dirt and a `wall_closed` event; the scaffold must build
a miner and mine. `:155-171` runs a bowl-of-chowder mirror to **round 1499** with both HQs alive.
`results.reason == "complete"` is asserted for bc20 in `tests/test_bc20_replay.nim:100` and in the
docker-smoke bc20 episode (`tools/ci/docker_smoke.sh:425-427`, log: `reason=complete`).

**8. LLM reply handling.** Tolerant parse: `sheet_common.nim:56-92` extracts the outermost balanced object
and falls back to first-brace..last-brace. Retry exactly once: `decide.nim:261` (`attempt < 2`) with the
retry nudge appended at `:288-290` and a `doctrine_retry` event at `:329-330`. Fallback: `:343-355` installs
the baseline sheet, records `results.fallbacks` (`results.nim:72`), emits `doctrine_fallback`, and echoes
"falling back". The fallback sheet is byte-for-byte the note's
(`baselines.nim:82-88`: all ten knobs at their defaults, `"default bowl-of-chowder doctrine"`,
`"Soup first."`), and an LLM seat's fallback resolves to `bowl-of-chowder` (`decide.nim:47-49`,
`baselines.nim:25-30`). A no-credentials seat is recorded as a fallback, not as a scripted policy
(`decide.nim:251-258`).

**No `chassis` knob.** `years/bc20/knobs.nim:52-57` (`KnownKeys20`, exactly ten, no `chassis`);
`sheet.nim:83-86` records any unknown key including `chassis`; `decide.nim:51-56` fixes the chassis by
operator; `server.nim:351-352` writes it into the plan; `replay.nim:72` records it on the seat and
`:237-239` restores it for the deriver. `tests/test_bc20_sheet.nim:171-187` asserts the D1 behaviour and
that two sheets differing only in `chassis` are the same doctrine.

**9. Rune-safe truncation.** `sim_types.nim:156-163` (`truncateRunes`), `:165-180` (`truncateBytes`, which
walks runes and stops before the byte cap), `:182-185` (`sanitizeLine`). Caps: reply 16 KB bytes
(`:88`, applied `sheet.nim:103`), sheet ≤ 32 keys (`:84`, applied `sheet.nim:78-79`), notes 280 / motto 48
(`:80-81`, applied `sheet.nim:94-95`), unknown keys ≤ 16 × ≤ 40 runes (`:82-83`, applied
`sheet.nim:83-86`), provider error text 200 runes (`:85`, applied `decide.nim:327-328` and
`:331-332`). `tests/test_bc20_sheet.nim:264-288` feeds 400 astral-plane runes at the caps and asserts exact
rune lengths and a byte cut on a rune boundary.

**10. Manifest validates.** `game.docs.readme` is `{type: uri, value}` and `pages` is four
`{id, title, content:{type,value}}` entries (rules, rules-bc20, replay, parity), each pointing at a file
that exists (`tests/test_manifest.nim:202-219`). `game.protocols` carries both `player` and `global`.
`ci.yml:211-232` additionally runs the installed `coworld==0.1.43` `_load_template_manifest` over the
template, green in run 33841592052.

**11. 360 px.** `client/replay_broadcast.html:2561` — `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }`;
`:2637-2641` hides `.plate-sub` under 640 px. Both inherited and untouched above the bc20 banner. The bc20
block adds its own `@media (max-width: 760px)` rules (`:2750-2759`) that drop the flood chip's per-clan HQ
labels rather than letting it overflow.

**12. Release order and scaffold.** `coworld-release.yml` and `coworld-submit.yml` are untouched by this
diff. The placeholder gate the checklist names exits 0 on this tree (run in the sandbox:
`grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml docker_smoke.sh policies.json`
→ no output). `tools/ci/policies.json` now has eight entries: bc26's four **unchanged** (the diff is a pure
append after `battlecode-scaffold`) and bc20's four — `battlecode-bc20-latticer` (`PLAYER_PROMPT`),
`battlecode-bc20-rusher` (`PLAYER_PROMPT`, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`),
`battlecode-bowl-of-chowder` and `battlecode-examplefuncsplayer` (`PLAYER_SCRIPTED`). Both champion prompts
are the note's text verbatim modulo ASCII dashes, and `tests/test_manifest.nim:259-306` pins the count, the
two owner ids, the ordering and the filler names.

**13. Viewer executes.** `wasm-viewer` `needs: docker-smoke` (`ci.yml:682`); the step "Load the bundle in a
real browser (BOTH years' replays)" (`:763-845`) is present, has no `continue-on-error`, and ran green in
run 33841592052 with two harness lines: `{"loaded":true,"ms":289,…TOOMUCHCHEESE…}` and
`{"loaded":true,"ms":298,…HOURGLASS…}`, each followed by `scrub selector: #scrub`,
`endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH`, and a largest-overlay reading of
2 % / 1 %. `data-replay-loaded` is set on the first drawn frame from the worker's `loaded` message
(`replay-viewer/static_replay.js:179-180`) and `data-replay-error` on failure (`:19-20`). Link flags and bootstrap
agree and both come from this repo's own starter lineage: `config.nims` has **no** `MODULARIZE` and no
`EXPORT_NAME` (`:46-53`), and the worker uses `var Module = {}` + `Module.onRuntimeInitialized`
(`static_replay_worker.js:8, 218, 274`). Neither loader file is touched by the diff; the only
`replay-viewer/` change is `bc_replay.nim` (13 lines, year dispatch). Playback has no recorded lobby in this
coworld — one frame is one round, `st` is 0 for both years (`broadcast.nim:311`, `:360`) and the frame list
starts at round 1 (`replay.nim:269-273`).

**14. Chrome is the starter's.** `client/chrome_common.js` and `client/broadcast_core.js` are byte-identical
to `/workspace/starters/coworld-ctf/client/` (verified with `diff -q`; neither appears in the diff).
`client/replay_broadcast.html` grows from 2 936 to ~3 700 lines: the bc26 page is untouched above
the banner comment `BC20 additions to the inherited cogame-battlecode chrome` (`:2643-2651`), no element is
removed (`#coopchip`, `#bars`, `#gamechips`, `#econ`, `#doctrines` all still in the body at `:2845-2849`),
and every added id is `#bc20-*`. The year switch is one attribute plus CSS (`:2653-2662`,
`onFrame` sets `data-year` at `:3194`). Transport rules: (a) `relayout()` sets `--hudscale`, `--topband`
and `--band` on `document.documentElement` (`:3541-3552`); (b) every bc20 panel rides
`bottom: calc(var(--band, 0px) + …)` (`:2686`, `:2694`, `:2711`) and the flood chip sits at `top: 6px` (`:2665-2672`);
(c) `#endcard { bottom: var(--band, 0px) }` (`:1848`), is shown with the class its own rule uses
(`#endcard.on`, `:1859` / `:3534`; `dismissEndcard` at `:3487-3491`), and `seek()` calls `dismissEndcard()` first (`:3313-3316`), as do the
transport buttons (`:3567`) and the keyboard (`:3595`) — the bc20 beat buttons seek through
`api.seek` (`:3001-3003`), so they dismiss it too; (d) beats are labelled `<button>`s with `aria-label`
and `title`, built by `buildBc20BeatButtons` (`:2986`) — not `markBeat`, not `buildBeatButtons` — and CSS
exists for all ten kinds emitted (`doctrine :2629`, `game :2633`, `end :2634`, `flood/build/wall/rush/drop/bury/drown
:2742-2748`). `#viewpanel` is kept and justified (48×48 board at 16 px/tile = 768 px against a 360 px
frame); `?viewpanel=0` still drops it (`:3644-3646`). `tests/test_viewer.nim:166-220` pins all of this,
including that the bc20 block shadows none of `renderClock`, `renderTransport`, `getSpoilers`,
`setSpoilers`, `renderBeatMarkers`, `markBeat`, `buildBeatButtons`.

**D3, the doctrine overlay.** `#bc20-doctrines-close` with `aria-label="Dismiss doctrines"` (`:2856-2858`),
an `Escape` binding scoped to `data-year="bc20"` (`:2973-2978`), a `#bc20-doctrines-toggle` re-open chip in
the scorebug (`:2798-2799`), a 6 s auto-close for a viewer who never presses play (`:2980-2982`), and a
close on the first frame that advances the playhead unless the viewer pinned it open (`:3197-3201`). It
never sits in the band (`bottom: calc(var(--band,0px) + 8px)`), and the smoke's largest-overlay reading on
the bc20 replay was `scorebug 1%`.

**Sim rules 1–9.** `rules.nim:100-152` is the round loop in the note's order: `processBeginningOfRound`
(round += 1 and +1 soup each, `world.nim:910-916`), a **snapshot** of `execOrder`, blocked robots skipped
with their pollution still reset (`:110-115`), `processBeginningOfTurn` (cooldown −1 floored at 0,
`opsLeft` reset, `world.nim:918-922`), the controller, `processEndOfTurn` (clear pollution → refine ≤ 20 →
vaporate +2 → cow → install the fresh effect → `roundsAlive`, `world.nim:924-947` — so a refinery's local
+500 lasts exactly one round), then end of round: mint ≤ 7 (`world.nim:949-955`), raise the water, flood one
ring, `checkEndOfMatch`, then the hash chain. Flood: `flood.nim:73-88` snapshots the flooded set before it
changes anything and drowns every non-drone on a newly flooded tile via `setFloodStatus`
(`world.nim:357-364`); `tryResurface` un-floods the moment a deposit lifts the tile
(`world.nim:366-372`, called from `addDirt`). Soup/refining: `mineSoup` takes
`min(7, tile, 100 − carry)` (`world.nim:634-642`); `depositSoup` moves soup into the building, not the pool
(`:653-658`). Seven build types with the note's preconditions (`canBuildRobot`, `world.nim:589-599`) and
`INITIAL_COOLDOWN_TURNS = 10` on the spawn (`:621`). Dig/dump: `canDigDirt` refuses a clean building
(`:660-668`); `addDirtCarrying` destroys a building at its `dirtLimit` and `destroyRobot` spills the dirt
onto the vacated tile (`:429-436`, `:526-550`). Drone carry: pickup `r² ≤ 3`, units only, never a building
or another drone (`:691-700`); the rider is `blocked` and rides with the drone (`:702-712`, `:569-571`); a
non-drone dropped into water dies immediately (`:743-758`); a dying drone drops its cargo on its own tile
(`:540-541`). HQ burial: 50 dirt, cause recorded `buried` (`:433-436`), drowning recorded `drowned`
(`:534-539`). Net guns: `r² ≤ 15`, drones only, HQ included (`:390`, `:760-775`). Pollution: global floored
at 0 (`:325-327`), per-robot additive/multiplicative registry installed and removed symmetrically
(`:329-347`), coefficients in float32 closed form with `Math.round(float) = floor(x + 0.5)`
(`pollution.nim:19-35`). Blockchain: 7 ints, `0 < cost ≤ pool`, soup deducted at submit, id from the
re-seeded RNG (`world.nim:777-792`), comparator cost-desc → id-desc → serialized-message-asc
(`blockchain.nim:45-51`), ≤ 7 minted per round with the remainder left in the pool (`:53-62`),
`blockchainsSent` counting **minted** (`world.nim:949-955`). `java.util.Random`: `rng.nim` reused
unchanged (not in the diff); the static transaction RNG is re-seeded with the map seed on **every** spawn
(`world.nim:507`), including the two HQs and every cow at load (`:997-998`), and
`tests/test_bc20_blockchain.nim:100-125` has a vector that fails if it is seeded once. Cows:
`84307·mapSeed + 20201·(id div 2)` in wrapping `uint32` (`cows.nim:47-55`), lazy per-cow RNG, up to four
draws with early exit on a move and exactly four when not ready (`:57-75`), odd-id reversal through the
world's symmetry (`:24-45`). Ladder: `checkEndOfMatch` (`world.nim:869-879`) fires only on
`timeLimitReached or destroyedHq[…]` and walks HQ → quantity → quality → broadcasts → highest id →
coin flip (world RNG, a documented divergence), with `timeLimitReached = round >= maxRounds − 1`
(`:864-867`) so a 1500 cap plays 1499. Scoring: `gamePoints` (`:881-904`) is the note's formula with
float32 narrowing and an `int()` truncation; `scoresFor` is `100 × wins + mean(points)`
(`match.nim:210-225`).

**Determinism data.** `data/bc20/water_levels.json` is read as float32 bit patterns and its length is
checked (`flood.nim:42-59`); `ci.yml:521-532` regenerates it under JDK 8 and byte-diffs it as a blocking
step; `parity-oracle-bc20` Tier A diffs a Java-vs-Nim vector file as a blocking step (`ci.yml:504-519`) and
was green in run 33841592052. The engine-from-source attempt is `continue-on-error: true` and reports the
`net.sf.jsi` 404 to the job summary (`:534-564`) — build report §1 documents this substitution, and the
`parity-oracle` (bc26) job with its Tier A/B/C round-loop diffs is untouched and still green.

**Manifest, in full.** `year.enum == ["bc26","bc20"]`; `variants[bc20].game_config` carries exactly the
note's values (`year bc20`, `pool mixed`, `gamesPerMatch 3`, `seed 0`, `maxRounds 1500`, `num_agents 2`,
`attempt1Ms 20000`, `retryMs 12000`, `doctrineBudgetMs 45000`, `perGameBudgetSeconds 100`,
`matchBudgetSeconds 320`, `connectTimeoutMs 25000`, both clan names); `certification` decodes **identically**
to `abc92ce` (still `awu` vs `scaffold` on `year: "bc26"`); `results_schema.games.items.required` narrows
to the five year-neutral keys with bc26's eleven **kept as properties** and bc20's twenty-three added, and
`end_reason` extended to the ten-value union. A structural diff of the whole manifest reports no removal
anywhere. This does not break bc26: `results.nim:29-41` still emits all sixteen bc26 keys, and a narrowed
`required` cannot reject a document that carries more.

**bc26 semantics under the shared-file changes.** `years/bc26/knobs.nim` is the old `sheet.nim` bc26 body
with `result.doctrine.` mechanically rewritten to `result.` — I diffed `defaultDoctrine`, `KnownKeys`,
`parseChassis`, `toJson`, `plainWords` and the whole repair chain against `abc92ce:src/battlecode/sheet.nim`
and found no behavioural difference (only the receiver rename). `sheet.validate` keeps the same envelope
(≤ 32 keys, unknown-field recording, `sanitizeLine` on notes/motto) and dispatches on `year`, defaulting to
bc26 for an absent/blank year (`sheet.nim:46-50`, `:57-95`). `replay.parseSeat` restores
`sheet.doctrine.chassis` from the recorded sheet exactly as before for any non-bc20 replay
(`replay.nim:182-184`), so a GV04 bc26 recording — which has no seat-level `chassis` key — still re-derives:
`plan.chassis` falls back to a bc20 `ChassisKind` that the bc26 path never reads
(`dispatch.nim:153-156` routes bc26 through `rules26.runRound`). `ReplayCompatibleGameVersions` is
`["GV04", "GV05"]` (`sim_types.nim:71`), which is build-report deviation §5 and keeps every shipped GV04
replay loadable. `render.newRenderer` defaults to `atlas` (`render.nim:87-95`) and `buildPacket`'s bc26 body
is unchanged (the diff removes only the old `loadAtlas`/`newRenderer` signatures). `bc26`'s
`chromeJson` is unchanged; `sessionChromeJson` only dispatches.

## Could not determine

- **Whether the baseline's parameters were "tuned with a grid harness, not guessed"** (checklist item 7,
  last sentence). The tree carries no bc20 grid harness; `tests/test_bc20_knobs.nim:19-31` records a table of
  *measured* low/high values with gates at roughly half each delta, and build report §3 says the survival
  counters "are the measured ones with margin … not the note's". That is evidence of measurement, not of a
  harness. What would settle it: a committed sweep script or the raw sweep output, or the builder naming
  where the numbers came from.
- **Whether `move`-into-water destroying the mover (F10) matches the 2020 engine.** The engine is not
  vendored and the bc20 oracle compiles only six dependency-free classes, so nothing in this tree or in the
  CI logs compares `RobotControllerImpl.move`. What would settle it: the upstream
  `world/RobotControllerImpl.java` / `GameWorld.moveRobot` at `7618f6b`, or the round-loop parity tier that
  build report §1 says is blocked on `net.sf.jsi`.
- **Whether the snapshot of `execOrder` (`rules.nim:106-107`) matches `ObjectInfo.eachDynamicBodyByExecOrder`
  for a robot spawned *during* the round.** The port's snapshot means a robot built this round takes no
  turn until the next one; a robot spawns with `cooldownTurns = 10` so it could not act either way, but it
  would decay one cooldown turn earlier under a live iteration. Same evidence would settle it as above.
- **The `abandoned` re-derivation on the CI runner** (F8): the branch at `tests/test_bc20_replay.nim:151`
  only runs if a 48×48 game fails to finish inside one second, and the CI log for the `test` job does not
  print which side of that `if` was taken. What would settle it: making the abandoned case deterministic
  (a zero-round budget or an injected clock) or printing the branch taken.
