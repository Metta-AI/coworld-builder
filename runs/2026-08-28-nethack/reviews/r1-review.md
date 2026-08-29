# r1 review — nethack

Repo: `/workspace/cogame-nethack` (Metta-AI/cogame-nethack)
Range: `2fccbf0` (bootstrap) .. `c484a248b43f9ff6fdc9208d748c58abcea64d74` (HEAD, 3 build commits)
Starter diffed against: `/workspace/starters/coworld-ctf` (read-only)
Design note: `/workspace/coworld-builder/runs/2026-08-28-nethack/design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision rider)
Files opened: 41 (all of `src/nethack/*.nim`, `src/nethack.nim`, `replay-viewer/*`,
`client/*`, `tests/*.nim`, `tools/**`, `.github/workflows/*`, the manifest, the
docs, plus the starter counterparts of every `client/` and `replay-viewer/` file)
CI evidence: run **33225421389**, `ci.yml`, branch `main`, sha `c484a24`,
conclusion **success** (`gh run list`); full log pulled and grepped.

**Blocking findings: 0.** Every checklist item I could evaluate from the tree and
the cited CI log is satisfied. The 22 findings below are advisory: they are
divergences from the design note, not falsifications of a checklist item. Where a
finding sits close to a checklist line I say so explicitly and give both readings
rather than picking the one that flatters the count.

---

## Blocking

None.

Each checklist item and how it was settled is in **§Traced and consistent**. Two
items (10 and 14's `#viewpanel` bullet) admit a stricter reading under which they
would be blocking; I record both readings under F17 and F5 and do not conceal
them.

---

## Non-blocking

### F1 — a command turn ends when its queue empties; the note's tick order ends it only on death or a level change
*(category: correctness — advisory)*

- Where: `src/nethack/driver.nim:96-101`, `:56-65`, `:103-114`
- Observed:
  ```nim
  proc turnDone*(sim: SimServer, runner: TurnRunner): bool =
    if not runner.active or runner.ticksLeft <= 0 or sim.ended or
        sim.cog.depth != runner.beforeDepth:
      return true
    not runner.emptyPlan and runner.ticksRun > 0 and sim.queue.len == 0 and
      sim.cog.paralysed <= 0 and sim.cog.trapped <= 0
  ```
  The last clause is a third exit condition. `emptyPlan` is set in `beginTurn`
  (`driver.nim:94`) as `plan.queue.len == 0`, so a reply with *no usable actions*
  still burns all forty ticks, but a reply whose queue drains after `n` primitives
  ends the turn at tick `n`.
- Note says: §Turn and tick structure step 3 — "Pop the next primitive from the
  queue. If the queue is empty the primitive is **`wait`** — a real cost: the tick
  and its nutrition are spent" (`design.md:383-384`) — and step 11 names exactly
  two break conditions, "the run ended at step 7 or in step 4's `down`/`up`"
  (`design.md:427-428`).
- Provenance: this is the builder's declared deviation (2) and it is written up as
  divergence 15 in `docs/PORTING-NETHACK.md:76-83`.
- Downstream effects I traced rather than assumed, from the committed fixture
  (`tests/fixtures/descend-seed42.replay`, read with `tools/replay_summary.py`):
  `tickCount 322`, `turnsPlayed 34`, `finalTick 322`, `primitivesExecuted 322`.
  - `primitivesExecuted == finalTick`, so the note's stated identity
    "`finalTick − primitivesExecuted` is the number of dungeon turns the cog stood
    still" (`design.md:1356-1357`) evaluates to 0 for every episode: with the queue
    never running dry inside a turn, a `wait` tick can now only come from an
    explicitly requested `{"do":"wait"}`.
  - Nutrition falls 1/tick (`src/nethack/sim.nim:689`), so a 322-tick episode
    consumes 322 of 900 nutrition. The note's hunger arithmetic — "900 nutrition
    covers 900 of the episode's 2200 ticks, the starting ration covers 800 more, so
    a cog that wants to use its whole clock must find and eat food at least once
    more — which is the idea's 'eat' task, made structural" (`design.md:170-172`) —
    no longer binds at 55 turns. This is the mechanical reason F3 exists.
  - `maxTicks = 2200` remains configured and validated (`sim_config.nim:144-146`)
    but is effectively unreachable; `turnCap` now fires on `maxTurns`
    (`driver.nim:118-119`).
- Not blocking: no checklist item names the tick order, the hunger clock or the
  episode length. Item 5 is satisfied (shorter episodes settle sooner).

### F2 — four balance constants differ from the note's numbers
*(category: correctness — advisory; the coordinator has already accepted these as a rails call)*

- Where and what:
  - `src/nethack/mobs.nim:22` — `const HitThreshold* = 15`; `hits` at `:35-36` is
    `d20 + attackBonus + defenderAc >= HitThreshold`. Note §Combat rule 1:
    "hits iff `d20 + attackBonus + defenderAc ≥ 11`" (`design.md:186`).
  - `src/nethack/sim_config.nim:79` — `startHp: 16`. Note: "start **12 / 12**"
    (`design.md:157`).
  - `src/nethack/sim_config.nim:80` — `regenTicks: 12`, consumed at
    `src/nethack/sim.nim:746-750`. Note: "`hp += 1` on every tick where
    `tick mod 20 == 0`" (`design.md:174`).
  - `src/nethack/dungeon.nim:492` — `min(MaxMonstersPerLevel - 2, 2 + depth)` =
    `min(10, 2 + depth)`; jackal packs and hill-orc pairs are gated on
    `depth >= 2` (`:515`, `:530`). Note: "`min(12, 3 + depth)` monsters"
    (`design.md:298`) with no depth gate on packs (`design.md:209, 214`).
- Documented: `docs/PORTING-NETHACK.md:84-101` carries a four-row table naming each
  correction, its measurement (30 seeds, `delver` died on DL1 in 30/30) and the
  40-seed sweep. The reasoning is also inlined at `mobs.nim:23-34` and
  `dungeon.nim:487-491`. The builder's claim matches the code exactly.
- Side effect I checked because it is a schema question: `regenTicks` is a **new**
  config key the note does not list. It is present in `config_schema.properties`
  (`coworld_manifest_template.json`), in all three `game_config` blocks and in the
  replay's resolved config (`sim_config.nim:278`), so the closed-schema contract
  holds — `additionalProperties: false` would otherwise have rejected the variants.
  I verified programmatically that every key in every `game_config` is declared.
- Not blocking: no checklist item pins a balance constant.

### F3 — the certification-seed test no longer asserts "eats at least once"
*(category: correctness — advisory)*

- Where: `tests/test_nethack_engine.nim:68-89`
- Observed: the test asserts `s.depthReached >= 2`, `s.monstersKilled >= 1`,
  `s.goldPickedUp >= 1`, `doors >= 1` (counting `door` events, i.e. autoopen and
  "locked" bumps, not kicks) and `s.tickCount >= 200`. There is no meal clause.
- Note says: §Packaging — "Seed 42 is asserted by `tests/test_nethack_engine.nim`
  to produce a fixture episode in which `delver` reaches at least dungeon level 2,
  kills at least one monster, picks up gold, **eats at least once** and opens at
  least one door" (`design.md:1908-1912`); §Tests 29 repeats it (`design.md:2054`).
- Corroborated from the shipped fixture: `timesAte: 0`, `deeds: []`, `doorsKicked: 0`,
  `depthReached: 2`, `monstersKilled: 5`, `goldPickedUp: 74`, `finalTick: 322`.
  So the smoke replay exercises descend/kill/gold/door but **not** `eat`.
- This is the builder's declared deviation (3) and it is the direct consequence of
  F1: with ~9 ticks per turn the cog never becomes Hungry, so a `delver` that only
  eats when `Weak` (`baselines.nim:264-268`) never eats.
- Not blocking: the checklist does not require an `eat` path in the smoke replay.
  Item 7 (scripted baseline plays a full legal episode ending `complete`) is
  satisfied — see §Traced.

### F4 — five artefacts the note lists are not shipped
*(category: other — advisory)*

- Absent, verified by `ls`/`find` over the tree:
  - `tools/wasm_replay_smoke.cjs` — note §Tests 50 (`design.md:2157-2159`) and the
    Kept-by-path table (`design.md:1085`). No `ci.yml` step runs the emitted wasm
    module under node.
  - `tools/ci/renderer_fixture.html` — note §Tests 49 (`design.md:2147-2156`).
  - `tests/shard_1..4.nim` and `tests/tests.nim` — note §Tests preamble
    (`design.md:1947-1950`). `ci.yml`'s `test` job instead globs `tests/*.nim`
    (`.github/workflows/ci.yml`, "Run tests" step), which does run every test file
    in debug and `-d:release`, so coverage is not lost — only the shard layout.
  - `client/league_replayer.html` — note §Kept table (`design.md:1082`).
  - `src/nethack/labels.nim` and `tests/label_manifest.txt` — note §Kept table
    (`design.md:1076`) and §Tests 46 (`design.md:2128-2129`).
- Also absent but listed in the note's Kept-by-path table: `src/nethack/rig_art.nim`,
  `tools/expand_replay.nim`, `tools/extract_events.nim`, `tools/record_fixture.sh`,
  `flake.nix`.
- This is the builder's declared deviation (4), plus the three extra items above.
- Checklist bearing: item 15's renderer-fixture requirement is conditional —
  "a repo that **draws model text** and has no such fixture is a blocking
  legibility finding". This viewer draws no model text at all (F6), so the
  condition does not fire. I state that plainly rather than as a technicality: the
  practical position is that neither the CI replay nor any fixture ever renders an
  LLM-authored string, because nothing in the page renders one.

### F5 — the board is fit-shrunk whole rather than clamped to 12 px/cell and panned; `#viewpanel` is kept
*(category: static-viewer / legibility — advisory, with a stricter reading recorded)*

- Where:
  - `src/nethack/global.nim:21-24` — `CellPx* = 18`, `BoardW* = LevelW * CellPx`
    (864), `BoardH* = LevelH * CellPx` (324). The whole level is composited
    server-side into one RGBA sprite.
  - `client/broadcast_core.js:249-255` (byte-identical to the starter apart from
    the wire rename):
    ```js
    let fitScale = 1;   // scale that fits the whole board (zoom 1).
    let zoom = 1;       // multiplier over the fit, >= 1.
    const minZoom = 1;  // 1 IS "fitted whole": the board can never
                        // be smaller than the frame it lives in.
    ```
    `computeFit()` (`:447-465`) sets `fitScale = min(cssW/nativeW, cssH/nativeH)`.
    At a 360 px board the whole 864 px-wide level is scaled to fit → ~7.5 px/cell,
    and `clampView()` (`:432-445`) centres rather than pans because the viewport
    covers the board on both axes at zoom 1.
  - `#viewpanel` is present in full (`client/replay_broadcast.html:1424-1443`) and
    wired (`:4121` `core.attachMinimap($('minimap-canvas'))`, `:3894-3895`,
    `:3952`, `:3969`, `:4024` zoom handlers, `#zoom-read` default `FIT` at `:1434`).
- Note says: §Legible at 360 px — "the renderer clamps cell size to
  **`minCell = 12` px** and centres the camera on the cog, so at 360 px the board
  shows a **30 × 10-cell window** of the level, panning as the cog moves. The board
  is therefore **larger than the frame**, which is why `#viewpanel` is kept"
  (`design.md:1735-1740`), and it calls 7.5 px/cell "**illegible**"
  (`design.md:1735`). There is no `minCell` constant anywhere in the tree
  (grepped).
- This is the builder's declared deviation (5) — but note the builder's own framing
  ("#viewpanel kept and wired") is accurate about *what* was done and silent about
  the consequence: the justification the note gave for keeping the panel is the
  camera behaviour that was not implemented.
- Two readings of checklist 14's last bullet ("Zoom bar + minimap (`#viewpanel`)
  only if the board is pannable … Keep it only when **the design note says** the
  board is larger than the viewport"):
  - *Literal* — the design note does say it (`design.md:49-50, 1576-1582`), so the
    keep is authorised and this is not blocking. This is the reading I apply.
  - *Substantive* — the shipped board wholly fits the frame at default zoom, so it
    is the "raid/hive/gridlock" case the bullet says should remove the panel.
    Under this reading it is a `static-viewer` finding.
  I record both because the difference is a judgement about what the bullet
  measures, not about what the code does. What the code does is above.
- Not asserted by any test: `tests/test_nethack_viewer.nim:42-56` asserts the
  `#viewpanel` ids are *present*; nothing asserts a pannable camera.

### F6 — the `say`, `plan` and `fallback` broadcast events are never emitted, so the feed never shows what the model said
*(category: correctness / legibility — advisory)*

- Where: every `emit(` call site in `src/nethack/` yields exactly nineteen kinds —
  `ascend bottom death deed descend door eat end escaped gold hunger hurt item
  kill levelup oracle quaff trap turn`. There is no `emit("say"…)`,
  `emit("plan"…)` or `emit("fallback"…)` anywhere.
- Note says: §Record vocabulary B declares "a closed enum of twenty-one kinds, plus
  `end`" including `plan {n, verbs, truncated, dropped}`, `say {text}` and
  `fallback {cause}` (`design.md:1435-1441`); §Beats lists `fallback` among the ten
  scrubber kinds (`design.md:1447-1448`); §Readouts 7 promises the feed line
  `Alpha: "rat first, then the gold, then the closed door west"` and says "The
  `say` lines and the plan lines are where a spectator sees the LLM playing"
  (`design.md:1682-1684`).
- Consequences, traced:
  - `src/nethack/broadcast.nim:17-19` — `FeedKinds` lists `"turn", "plan", "say"`,
    none of which can arrive.
  - `client/replay_broadcast.html:4609-4613` `BEAT_KINDS` includes `fallback`;
    `:4498-4502` styles `.beat-marker.fallback`; `:4603` labels it; `:4675-4680`
    writes the `MISSED THE CALL — DELVER PLAN (…)` feed row. All unreachable.
  - `src/nethack/broadcast.nim:134` ships `"say": sim.lastSay` in every frame and
    nothing in `client/replay_broadcast.html` reads `nh.say` (grepped: the only
    `nh-say` hits are three CSS/feed spans used for descend/ascend/death lines).
    The model's remark reaches the browser and is never drawn.
  - `tests/test_nethack_events.nim:35-37` asserts only "every kind the sim emits is
    in the declared set", i.e. one direction, so a declared-but-never-emitted kind
    passes. The note's test 47 asks for equality (`design.md:2130-2132`).
- Related, same area: the `eat` event carries a literal `"name": "food"`
  (`sim.nim:541`) rather than the item's name, and the page renders
  `ATE A RATION` unconditionally (`replay_broadcast.html:4655-4657`); the note's
  feed line is `ATE A FOOD RATION` (`design.md:1679`).
- Not blocking: checklist 8 requires the fallback to be **recorded** so phase 60 can
  count it — it is, three ways (a `fallback` chat record in the replay
  (`decide.nim:60-67`), `results.fallbackTurns` (`sim.nim:1016`), and the game-log
  phrase `falling back` (`decide.nim:150, 241`)). Checklist 15's fixture trigger
  requires the viewer to *draw* model text; it does not.

### F7 — `client/broadcast_core.js` is the starter's file verbatim; none of the nine draw procs the note adds exist
*(category: other — advisory)*

- Where: `diff /workspace/starters/coworld-ctf/client/broadcast_core.js
  client/broadcast_core.js` is a **one-line** diff (`:49`,
  `window.CTF_WIRE` → `window.NETHACK_WIRE`).
- Note says: §Chrome provenance — "`client/broadcast_core.js` is **forked** …
  Deleted: every ctf-specific draw call and the raycast FPV pipeline … Added:
  `drawDungeonBed`, `drawTerrain`, `drawFeatures`, `drawItems`, `drawMonsters`,
  `drawCog`, `drawMemoryWash`, `drawTerminalPanel`, `drawDepthLadder`"
  (`design.md:1539-1549`). None of those nine identifiers exists anywhere in the
  repo (grepped; the only hits are in `docs/plans/2026-08-28-nethack-design.md`,
  the copied note).
- What replaced them: the dungeon, the memory wash, the monsters, the items and the
  features are composited **server-side** into one sprite in
  `src/nethack/global.nim` (340 lines, `Chip` bakes at `:80` onward, one
  `BoardSpriteId = 300` sprite at `:26`), and `broadcast_core.js` draws it as an
  ordinary sprite. The depth ladder and the terminal panel are DOM, built by the
  appended game block (`replay_broadcast.html:4723-4785`). The outcome is
  equivalent; the provenance claim in the note is not literally met.
- `tests/test_nethack_viewer.nim:122-134` pins the *kept* starter procs and the wire
  rename, which is exactly what is there.

### F8 — `chrome_common.js` reads `window.CTF_WIRE`, which the fork never defines; the transport renders two dead speed chips
*(category: legibility / correctness — advisory)*

- Where:
  - `client/chrome_common.js:72-74` (byte-identical to the starter, as the note and
    checklist 14 require):
    ```js
    var WIRE = window.CTF_WIRE || {};
    var SPEEDS = WIRE.speeds || [1, 2, 3, 4, 8, 16];
    var FPS = WIRE.fps || 24;
    ```
  - `src/nethack/wire_constants.nim:19` emits `window.NETHACK_WIRE={…}` — the only
    global defined, spliced by `server.nim:64` and written to
    `dist/wire_constants.js` by `Dockerfile.replay-viewer:31,37`.
  - `client/chrome_common.js:436-447` builds one `<button class="chip">` per entry
    of `SPEEDS` with `map = {1:'1', 2:'2', 3:'3', 4:'4', 8:'8', 16:'6'}`.
- Observed consequence: `SPEEDS` falls back to `[1,2,3,4,8,16]`, so the page draws
  **six** speed chips. `src/nethack/sim_types.nim:28` declares
  `PlaybackSpeeds* = [1, 2, 4, 8]`, and `src/nethack/replays.nim:200-208`
  `applySpeedCommand` handles only `+ = - _ 1 2 4 8` — so clicking `3×` (sends
  `'3'`) or `16×` (sends `'6'`) does nothing, and `renderTransport`'s highlight
  (`chrome_common.js:459`, `sp === s.sp`) can never light either. `FPS` happens to
  coincide (`TargetFps = 24`), so the clock is unaffected.
- Note says: §Chrome provenance requires `chrome_common.js` byte-identical
  (`design.md:1521-1526`) and §Viewer pins "speed chips `[0.5, 1, 2, 4, 8]`,
  default 1" (`design.md:1636`) — neither the code's `[1,2,4,8]` nor the rendered
  `[1,2,3,4,8,16]`.
- Not blocking: no checklist item covers the speed chip set, and item 14 *requires*
  the byte-identical file that produces this. The one-line escape hatch the note
  itself anticipates ("the only admissible change is a named, minimal patch
  recorded in the design note") was not used, correctly.

### F9 — the `fault` end path is not implemented in the server
*(category: correctness — advisory)*

- Where: `src/nethack/server.nim:360-539` — `while true:` with no `try`/`except`
  around the loop body, and `src/nethack.nim:44-90` has none around
  `runServerLoop`. `sim.stopDetail` is declared (`sim.nim:45`) and serialised
  (`sim.nim:1018`) but never assigned anywhere in `src/`. `erFault` is reachable
  only from a replay `stop` record (`replays.nim:142`) or a direct call in tests
  (`test_nethack_engine.nim:169`).
- Note says: §End conditions — "`fault` — an unexpected exception in the sim or the
  loop. **Caught**; the episode is settled from the last completed tick,
  `results.endRule = "fault"`, `results.stopDetail` names it (≤ 200 runes,
  rune-truncated), artifacts are still written, exit 0" (`design.md:548-551`).
- Observed behaviour instead: an exception inside the Playing branch propagates out
  of `runServerLoop`, the `defer: replayWriter.closeReplayWriter()` at
  `server.nim:295` runs, `writeArtifacts()` (`:332`) does **not**, and the process
  exits non-zero with no `results.json`.
- Not blocking: checklist 5 is about hangs and unbounded waits, not crashes; no
  item requires a fault handler. `docs/SPEC.md`'s "smoke fails on `fault`" is
  moot because the value cannot be produced.

### F10 — `dropped` is one counter serving two different note-level counters, and is added to both
*(category: correctness — advisory)*

- Where:
  - `src/nethack/directives.nim:135-172` — `parseReply` increments the single
    `result.dropped` for entries past `maxActions` (`:137-139`) **and** for every
    schema-invalid entry (`:140-141, 144-146, 151-153, 159-161, 166-169`).
  - `src/nethack/decide.nim:209` — `sim.repliesRepaired += reply.dropped`.
  - `src/nethack/driver.nim:83-84` — `sim.lastDropped = dropped;
    sim.actionsDropped += dropped`.
- Note says: §Turn structure 6a — "Entries past `maxActionsPerTurn = 10` are
  dropped and counted in **`actionsDropped`**"; 6b — "an entry that does not
  validate is **dropped** …, counted in **`repliesRepaired`**"
  (`design.md:358-362`). The two are meant to be disjoint; here every dropped entry
  from an LLM reply increments both, and a scripted/fallback reply increments only
  `actionsDropped` (its `dropped` is 0, so in practice both read the same number
  for LLM turns).
- `tests/test_nethack_driver.nim:241-250` asserts the double-count as the intended
  behaviour (`s.lastDropped == 3` and `s.actionsDropped == 3` from a directly
  supplied `dropped = 3`), so nothing catches it.

### F11 — the fallback `cause` vocabulary does not match the note's closed set
*(category: correctness — advisory)*

- Where: `src/nethack/decide.nim:216-221` sets `lastCause` to `"timeout"`,
  `"transport_error"`, `"throttled"` or `"parse_error"`; `:234-238` can also emit
  `"no_credentials"` or `"throttled"`; `:145` emits `"budget_guard"` /
  `"no_credentials"`; `:157` emits `"rate_guard"`.
- Note says: `cause ∈ {timeout, parse_error, transport_error, no_credentials,
  rate_guard, budget_guard, disconnected}` (`design.md:673-675`). `throttled` is
  outside that set; `disconnected` is never produced. No test or schema constrains
  the value (the `fallback` record is a replay chat record, not part of
  `results_schema`), so nothing fails.

### F12 — `delver`'s rule ladder is restructured relative to the note's nine rules
*(category: correctness — advisory; not among the builder's declared deviations)*

- Where: `src/nethack/baselines.nim:253-373`. Rule by rule against
  `design.md:1014-1038`:
  - Note rule 5 "Take the stairs" is promoted to position **3** (`:274-283`), ahead
    of flee and fight. The code comments the reasoning at `:257-261`.
  - Note rule 3 "Flee if hurt — `hp × 3 ≤ maxHp` and a monster is 8-adjacent →
    travel to the remembered `>` if any, else the remembered `<`, else the farthest
    reachable cell" becomes `:286-294`: `hurt and adjacentMonsterCount() >= 2` →
    travel to the remembered `<` only. There is no `>`-first branch and no
    farthest-cell branch.
  - `params.fleeHpNumerator` ships as **1** (`:37`), so `hurt` is
    `sim.cog.hp * 1 <= sim.cog.maxHp` (`:286`) — vacuously true for every state,
    since `hp ≤ maxHp` always. The HP half of the flee predicate never
    discriminates. The value is the sweep's pick (`tools/ci/baseline_tuning.json`)
    and is asserted by `tests/test_nethack_driver.nim:252-262`, so this is a
    swept-into-degeneracy parameter, not an untuned one.
  - Note rule 4 "four `move`s into it" is three (`:305-306`).
  - **Two rules the note does not list are inserted**: rule 5b "rest by searching"
    (`:309-316`, an eight-`search` burst when `hp × 2 ≤ maxHp` and no monster within
    6) and rule 7a "open what is merely closed" (`:330-338`, travel to a closed
    door then up to ten `move`s into it).
  - Note rule 7 "four `kick`s" is eight kicks plus two moves (`:339-346`).
  - Note rule 8 "then two `{"do":"move"}` continuing the last heading" fills the
    whole ten-action budget with the heading (`:363-364`).
- Not blocking: checklist 7 requires "the baseline's **parameters** were tuned with
  a grid harness, not guessed" — they were (`tools/tune_baselines.nim` sweeps
  4×3×2×2 = 48 combinations over 40 seeds and writes
  `tools/ci/baseline_tuning.json`; `test_nethack_driver.nim:252-262` pins the
  shipped defaults to it). The rule ladder is not a checklist object.

### F13 — `sanitizeSay` deletes every non-ASCII rune rather than truncating at 140 runes
*(category: other — advisory)*

- Where: `src/nethack/directives.nim:38-49`
  ```nim
  for rune in text.truncateRunes(MaxSayRunes).runes:
    let value = int(rune)
    if value >= 32 and value < 127 and value != ord('{') and value != ord('}'):
      result.add($rune)
  ```
- Observed: the rune cut happens first (so the output is always valid UTF-8 —
  checklist 9 holds), then everything outside printable ASCII is dropped. A `say`
  written in any non-ASCII script arrives empty. `notes` keeps full Unicode
  (`:51-54`, `truncateRunes` only).
- Note says: `say` is "**≤ 140 runes** (`MaxSayRunes`)" (`design.md:816`) with no
  ASCII filter; §Rune truncation names `say` as one of the strings truncated on
  rune boundaries (`design.md:830-834`).
- `tests/test_nethack_driver.nim:229-232` documents and asserts the filter
  (`check sanitizeSay(mixed) == "ok"`), so it is deliberate.

### F14 — `stuck` blocks every move, not only a move away from the lichen
*(category: correctness — advisory)*

- Where: `src/nethack/sim.nim:390-397`
  ```nim
  let monster = sim.levels[li].monsterAt(nx, ny)
  if monster >= 0:
    sim.cogAttack(monster); return
  if sim.cog.stuck > 0:
    sim.say("You are stuck to the lichen."); return
  ```
- Note says: combat rule 5 — "A lichen `F` that hits the cog sets `stuck` for 3
  ticks: the cog may attack and act but **any `move` away from the lichen** fails"
  (`design.md:197-198`).
- Observed: attacking still works (the monster branch precedes the check), but a
  move in *any* direction fails while stuck, including toward the lichen and
  including a move that would open a closed door.

### F15 — `--band` overlays: the game block's additions clear the band; the inherited feed and PiP do not read `--band`
*(category: static-viewer — advisory; inherited behaviour, unchanged from the starter)*

- Where: `client/replay_broadcast.html:132-138` — `#chrome { position: absolute;
  inset: 0 }`, so chrome children are positioned against the whole stage, not the
  band-clipped board box. `#killfeed { bottom: calc(76 * var(--u)) }` (`:470-476`)
  and `#fpv { bottom: calc(64 * var(--u)) }` (`:533-536`) are the starter's values
  and do not read `var(--band)`.
- The game block's own additions do clear it: `#nh-ladder` is top-anchored
  (`:4400-4402`, `top: calc(var(--topband, 0px) + 10 * var(--u))`), `#nh-deeds`
  lives inside `#plates-r` in the top band, and `#nh-term` is inset inside the
  starter's `#fpv` (`:4433-4437`). `tests/test_nethack_viewer.nim:103-107` asserts
  no `bottom: 0` in the appended block.
- Checklist 14(b) reads "nothing fixed-positioned … sits inside the band — they
  ride `bottom: calc(var(--band, 0px) + …)`". `#endcard` does (`:961`, checked). The
  feed and the PiP inherit the starter's absolute offsets unchanged; the starter
  ships the same and the CI viewer smoke read the scorebug, clock and tick
  readouts cleanly. I am recording the observation, not asserting an overlap — see
  §Could not determine.

### F16 — CI never invokes four shipped tools the note pins to it
*(category: other — advisory)*

- Where: `.github/workflows/ci.yml` (whole file read). Not invoked anywhere:
  - `tools/ci/check_gameversion.sh` (present, `0755`) — note §Kept table
    "`tools/ci/check_gameversion.sh` … **byte-for-byte** | version discipline"
    (`design.md:1086`) and §Sim module "`tools/ci/check_gameversion.sh` kept"
    (`design.md:1077`).
  - `tools/ci/next_coworld_version.py` and `tools/ci/test_next_coworld_version.py`
    (both present) — same table row.
  - `tools/tune_baselines.nim --check` — note §Tests 26: "`ci.yml` re-runs the sweep
    with `--check`" (`design.md:2042`). The `--check` branch exists
    (`tools/tune_baselines.nim:73-83`) and is never called.
  - There is no "manifest loads under the installed CLI" step running
    `validate_upload_manifest` / `_load_template_manifest` — note §Tests 39
    (`design.md:2101-2104`). `coworld build` is only invoked in
    `coworld-release.yml:165`, i.e. at release time, not in `ci.yml`.
- Not blocking: checklist 12 enumerates what must be present and executable
  (`docker_smoke.sh`, `policies.json`, three workflows, the placeholder gate) — all
  verified — not what `ci.yml` must additionally run.

### F17 — `game.docs` uses `"type": "uri"` where the checklist's literal shape shows `"type": "text"`
*(category: manifest — advisory)*

- Where: `coworld_manifest_template.json:40-70`:
  `"docs": {"readme": {"type": "uri", "value": ".../README.md"},
  "pages": [{"id": "rules.md", "title": "Rules", "content": {"type": "uri", "value": ".../docs/RULES.md"}}, …]}`
  — three pages: `rules.md`, `actions.md`, `porting.md`, all present under `docs/`.
- Checklist 10 writes the shape as
  `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`.
- The design note prescribes `uri` explicitly (`design.md:1835-1838`), and the
  *structure* the checklist names (readme + pages with `id`/`title`/`content`) is
  exactly what ships. Precedent I checked in the mounted repos: the starter's own
  `coworld-ctf/coworld_manifest_paintbot.json`, `cogame-factorio` and `cogame-moba`
  all use `"type": "uri"`; `cogame-babel`, `cogame-bullwhip` and `cogame-parley`
  use `"text"`. Both forms ship today.
- I categorise this **non-blocking**: the checklist item's headline is "Manifest
  validates", the structure is correct, and `uri` is in production use on the
  starter this repo forked. A judge reading the item as a literal byte pin would
  reach the opposite conclusion; the evidence for both is above.
- `game.protocols` carries **both** `player` and `global`, each as a
  `{"type","value"}` object (`:28-38`) — the other half of item 10 is met outright.

### F18 — `.plate .plate-name { min-width: 4.5em }` overrides the checklist's 3.2 em floor
*(category: legibility — advisory)*

- Where: `client/replay_broadcast.html:4292-4299` carries the checklist rule
  verbatim:
  ```css
  .plate-name {
    flex: 1 1 auto;
    min-width: 3.2em;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  ```
  and `:4301` then adds `.plate .plate-name { min-width: 4.5em; }`, which wins on
  specificity inside a plate. Added by HEAD (`c484a24`, "the scorebug plate fits
  both names at 1280 px and at 360 px").
- Checklist 11 requires `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and
  labels hidden under 640 px. The rule is present; the effective floor inside a
  plate is *larger*, i.e. the name collapses less, which is the direction the item
  protects. Labels are hidden by `#stage.tiny .plate .nh-stats, #stage.tiny .plate
  .hp-label { display: none }` (`:4521-4522`) with `.tiny` toggled at
  `boardW <= 620` (`:4233`) — the starter's own threshold.
- Not blocking.

### F19 — `--strict-text-bounds` measured nothing: `canvas_text.total = 0`
*(category: legibility — advisory, recorded for the judge)*

- Evidence, CI run 33225421389, `wasm-viewer` → "Load the bundle in a real browser":
  ```
  {"loaded":true,"ms":376,"clock":"DLVL 1 T:120 · TURN 14/55 · HP 16/16 · $62 · NOT HUNGRY · SCORE 1070", ...}
  soak: 10s of playback kept advancing ("0 / 322" -> "96 / 322" -> "120 / 322")
  canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
  ```
- Why `total` is 0: every string this viewer draws is DOM, not canvas. The terminal
  panel is a `<pre id="nh-term">` (`replay_broadcast.html:4755-4785`, with the
  comment at `:4750-4754` stating this is deliberate so the panel "can never be
  drawn outside the canvas"); the feed rows, the depth ladder, the deed chips, the
  scorebug, the clock and the tombstone are all DOM. The board canvas carries only
  the server-composited sprite (`global.nim`), and `showPlayerLabels` is false.
- Checklist 15 says `never_inside` must be 0 for a fixed arena and that
  `--strict-text-bounds` must be on `ci.yml`'s smoke step: both hold
  (`.github/workflows/ci.yml`, the flag is passed). The same item says
  "`total: 0` means the check covered nothing … and is not evidence of anything" —
  so the gate is satisfied but vacuous here. The compensating fact is that DOM text
  cannot land at a negative canvas coordinate, which is the failure class the item
  exists to catch.

### F20 — the removed elements' JS survives behind null guards; four CSS blocks the note lists for removal are still present
*(category: other — advisory)*

- Removed correctly (markup and CSS both, diff-verified against the starter):
  `#povBadge` (starter `:528-547`, `:1525`, `:3955`), `.fpv-hp` / `.fpv-gear`
  (starter `:652-674`, `:1537-1538`), `.fpv-map` / `#fpv-map-canvas` (starter
  `:676-700`, `:1540-1545`), `.beat-marker.kill|.steal|.return|.capture` (starter
  `:917-934`), `.hillchip`, `.pb-tags`, `.squad`, `.lives-label`/`.lives-num` in
  the plate builder.
- Still present, though the note lists them under "Elements removed (exactly these,
  and the JS that feeds them)" (`design.md:1550-1561`):
  - The JS readers for the removed ids: `client/replay_broadcast.html:3212-3219`
    (`var hpEl = $('fpv-hp')`, `var gearEl = $('fpv-gear')`) and `:3231-3265`
    (`fpvMapEl`, `fpvMapCanvas`, `syncFpvMapShape`, `drawFpvMap`), made inert by
    two early returns added at `:3213` (`if (!hpEl) return;`) and `:3262`
    (`if (!fpvMapEl) return;`).
  - `.flagicon` (7 occurrences, same as the starter), `.squad-pip` (13),
    `.ec-heart` (8), the perk/handicap badge rules (13 / 1) — all listed for
    removal at `design.md:1556-1561`.
- `tests/test_nethack_viewer.nim:59-61` asserts only that `id="povBadge"` etc.
  appear nowhere, which the markup removal satisfies; the note's test 44 wording is
  "appear nowhere" (`design.md:2122-2123`), which the surviving `$('fpv-hp')`
  string does not meet under a literal reading.
- Not blocking: checklist 14's requirement runs the other way — sections 1–5 must be
  "present and unmodified except for the removals the note lists". Extra surviving
  starter CSS is "unmodified"; it is the note, not the checklist, that asks for
  more.

### F21 — `roster.nim` and `sim_state.nim` do not exist; their contents were folded elsewhere
*(category: other — advisory)*

- Note says: §Kept table — `src/ctf/roster.nim → src/nethack/roster.nim` "fork, two
  named edits" (`design.md:1072`), `src/ctf/sim_state.nim → src/nethack/sim_state.nim`
  "fork" (`design.md:1071`), and §The two named edits to `roster.nim`
  (`design.md:1256-1263`) name `seatAlias(slot)` and
  `squadResultsJson → runResultsJson` at `roster.nim:650`.
- Observed: `src/nethack/` contains no `roster.nim`, `sim_state.nim`, `labels.nim`
  or `rig_art.nim`. `runResultsJson` is at `src/nethack/sim.nim:948`; the roster
  JSON is `rosterJson` at `src/nethack/broadcast.nim:59-76`; `gameHash`/`mixTick`
  and `emit` are at `sim.nim:148-190` and `:73-80`; there is no `seatAlias` proc —
  the alias is the string literal `"Alpha"` at `sim.nim:958`, `broadcast.nim:64`,
  `server.nim:424, 516`, and `"Alpha the Digger"` at `sim.nim:899` and
  `broadcast.nim:128`.
- Behaviourally the two-name-space rule holds (see §Traced, checklist 4); only the
  module provenance differs.

### F22 — the 4096-byte reply cap is applied as 4096 *runes*, after parsing, to the extracted text
*(category: other — advisory)*

- Where: `src/nethack/llm.nim:175-190`
  ```nim
  var body = response.body
  if body.len > MaxReplyBytes * 8: body = body[0 ..< MaxReplyBytes * 8]
  let payload = parseJson(body)
  ...
  if result.len > MaxReplyBytes: result = result.truncateRunes(MaxReplyBytes)
  ```
- Note says: "whole reply | bytes | **≤ 4096** read from the provider **before
  parsing**" (`design.md:818`).
- Observed: up to 32 768 bytes of the HTTP envelope are read and JSON-parsed, then
  the concatenated `text` blocks are cut at 4096 **runes** (`MaxReplyBytes = 4096`,
  `sim_types.nim:46`). The byte slice at `:177` is a raw byte cut of a JSON
  document, but it is only used as a guard before `parseJson`, which will simply
  raise on a truncated document — that raise is caught by
  `decide.nim:212` and becomes a `parse_error` fallback, so it cannot produce
  invalid UTF-8 in the replay. Rune safety (checklist 9) is unaffected.

---

## Traced and consistent

Checklist items, each settled from the code or the cited CI evidence.

**1 — CI green, no test loosened.**
`gh run list -R Metta-AI/cogame-nethack --branch main -w ci.yml`:
run **33225421389**, "nethack: the scorebug plate fits both names at 1280 px and at
360 px", conclusion `success`, 4 m 06 s, at sha `c484a24`. Jobs: `test` success,
`docker-smoke` success, `wasm-viewer` success.
"No test loosened": `git log --stat -- tests/` shows a single commit touching
`tests/` — `8e66c09`, which **added** all 13 files (2 042 insertions, 0 deletions).
`git log -p 8e66c09..HEAD -- tests/` is empty. No assertion deleted, no tolerance
widened, no skip added, no test file removed.

**2 — Replay re-derivation, frame by frame, asserted.**
`tests/test_nethack_replay.nim:26-54`: for `death`, `turncap`, `wallClock` and
`fault` (and separately `bottom` / `escaped` over two ladders) an episode is
recorded and re-derived, asserting `player.checkReplayHash() == -1`,
`not player.hashValidationFailed`, and equal `tickCount` / `depthReached` /
`endRule` / `endReason`. The comparison itself is per tick:
`src/nethack/replays.nim:165-173` compares `replay.data.hashes[i].hash` against
`sim.gameHash()` after **every** `stepReplay`. The viewer's display is built from
that same `sim` (`replay_runtime.nim:114-140` → `broadcast.buildStateJson(sim, …)`),
not from a parallel recording. `test_nethack_replay.nim:98-126` adds a
determinism-from-bytes test and a seek-identity test.
The wall-clock stop is a load-bearing record applied by one proc on both sides
(`replays.nim:134-143`, written at `server.nim:366-368` before `endRun`).

**3 — Static viewer.** `coworld_manifest_template.json:27-29`
`"replay_viewer": {"bundle": "static-replay-viewer"}`, under `game`.
`tools/build_replay_viewer.sh` exists, mode `100755`, carries the ecos
`mkdir -p "$(dirname …)"` fix and the buildx/`--platform linux/amd64` handling, and
`docker cp`s from `/workspace/nethack/replay-viewer/dist/.`. It is the
`coworld build` hook (`coworld-release.yml:165-171` passes `--project .`) and is
invoked by path in `ci.yml`'s `wasm-viewer` job after an explicit `test -x` assert.
The manifest declares no replay route (grep for `replay` in the manifest returns
only the two `replay_viewer` lines). The bundle fetches only its own dist assets
(`static_replay.js`, `static_replay_worker.js` diffed against the starter: renames
only). The server's `/client/replay` route (`server.nim:50, 148-150`) is local-dev
only and is not declared anywhere.

**4 — Both name spaces.** Agent side: `sim.observationJson` emits
`"you_are": "Alpha the Digger"` (`sim.nim:899`) and no real name; the system prompt
(`llm.nim:192-256`) names only "Alpha the Digger"; the seat's `PLAYER_POLICY_LABEL`
is stored as `sim.playerName` (`server.nim:410-416`) and never enters the
observation (checked field by field in `observationJson`, `sim.nim:882-935`).
Viewer side: `results.names[0]` is the real policy name and `results.aliases[0]` is
`"Alpha"` (`sim.nim:955-958`); the scorebug plate carries the real name in
`.plate-name` and the alias in `.nh-alias`
(`replay_broadcast.html:2124-2135, 2172-2180`); `rosterJson` ships both
(`broadcast.nim:59-76`). `showPlayerLabels: false` in all three `game_config`s.
The register replay record is redacted — policy label and kind only, never the
prompt (`decide.nim:69-80`), asserted at `test_nethack_replay.nim:78-84`
(`check not record.hasKey("prompt")`).

**5 — Degrade never hang; settles inside 60 % of 1200 s.** Every wait traced:
- attempt 1 → `makeRequests(batch, max(1, attempt1Ms div 1000))` = 6 s
  (`decide.nim:180-198`); retry → 3 s (same line, `attempt == 1`).
- outer `turnBudgetMs` 9.5 s checked before each attempt (`decide.nim:176-179`);
  worst realised turn ≈ 6 + 3 = 9 s of provider time.
- `turnSpacingMs` floor: `sleep(min(turnSpacingMs, turnSpacingMs - since))`
  (`decide.nim:164-167`) — bounded by 2.6 s and only the remainder since the last
  request start, so it does not add to a slow turn.
- rate guard: `recentRequests() >= 28` over a trailing 60 s window
  (`decide.nim:112-116, 154-161`), no sleep, takes the `delver` plan.
- budget guard: `elapsed + 2 × ceil(turnBudgetMs/1000) > wallClockBudgetSeconds`
  (`decide.nim:131-138`) — with 660 s and 9.5 s that fires at elapsed > 640 s, so
  the last LLM turn starts by 640 s and finishes by ≈652 s; every later turn is
  scripted (microseconds).
- engine stop: `elapsedSeconds() >= config.wallClockBudgetSeconds` at the top of
  every loop iteration (`server.nim:362-368`), writing the stop record then
  `endRun(erWallClock)` → `reason = deadline`.
- lobby: `lobbyTicks > config.lobbyJoinTimeoutTicks` (2400 at `sleep(1000 div 24)`
  = 100 s) then `declarePlayerFailure` and play begins anyway
  (`server.nim:443-465`).
- game-over hold: `gameOverTicks` = 48 ≈ 2 s (`server.nim:533-539`,
  `sim_config.nim:92`).
- `sim_config.validate` (`:155-158`) refuses any `wallClockBudgetSeconds > 660`, and
  `tests/test_nethack_manifest.nim:93-98` asserts it across every shipped variant.
Loop termination: the Playing branch runs at most `maxTurns` iterations because
`beginTurn` increments `turnsPlayed` (`driver.nim:87`) and `endTurn` ends the run at
`turnsPlayed >= maxTurns` (`driver.nim:118-119`); `stepTurn` decrements
`ticksLeft` every call (`driver.nim:108`), bounded at 40. `runPreScan` and
`seekReplay` both carry `guard < 20_000` (`replay_runtime.nim:29-33`,
`replays.nim:191-194`). No blocking read: the websocket handler runs on mummy's own
serve thread and the game loop only drains locked queues (`server.nim:370-398`).
Total worst case: the budget guard and the engine stop both measure
`elapsedSeconds()` from `episodeStart`, which is set **before** the lobby
(`server.nim:318`), so the lobby's ≤ 100 s is *inside* the 660 s, not added to it.
The bound is 660 s plus at most one in-flight turn (≤ 2.6 s spacing + 9.5 s budget
≈ 12.1 s) plus the ≈ 2 s game-over hold ≈ **674 s < 720 s**. The CI episode settled
in 3.4 s.
Simultaneous-decision rider: one seat, one request per turn through the starter's
`makeRequests` batch path (`decide.nim:189-198`) — no sequential fan-out exists.

**6 — `num_agents`.** Present as `1` in `variants[0].game_config`,
`variants[1].game_config` and `certification.game_config`; absent at every variant
top level (checked programmatically). `config_schema.properties.num_agents` is
`{"type":"integer","minimum":1,"maximum":1,"default":1}`.
`len(certification.players) == len(certification.game_config.players) == 1`.
`tools/ci/docker_smoke.sh:107-150` enforces all four invariants plus the
`SMOKE_SEATS` cross-check, each with a `SEAT-COUNT FAIL:` prefix;
`seats_expected="${SMOKE_SEATS:-1}"` at `:54`, and `ci.yml` passes `SMOKE_SLUG`
with the workflow's `SLUG: nethack`. **`grep -c "SEAT-COUNT FAIL" full.log` over
the whole run 33225421389 log returns 0.** The smoke log line reads
`smoke OK: seats=1 results=867B replay=58963B reason=complete`.
`sim_config.validate:129-131` additionally refuses any `numAgents != 1` at runtime.

**7 — Scripted baseline plays full legal episodes.**
`tests/test_nethack_engine.nim:10-21` records a real scripted episode and asserts
`results.reason == "complete"`. Legality: `tests/test_nethack_driver.nim:67-83`
runs 300 scattered states × both baselines and checks ≤ 10 actions, every `do` in
the enum, every `dir` in the enum, `travel` inside 0…47 / 0…17, every `item` a
letter actually held, `say`/`notes` empty, serialised directive ≤ 1024 B;
`:84-143` asserts no plan steps into known lava and `delver` never melees a floating
eye nor travels through the dark; `:144-160` asserts every expanded queue is ≤ 40
primitives, corner-cut clean, and that an empty queue yields `wait`.
Grid harness: `tools/tune_baselines.nim:38-63` sweeps
`fleeHpNumerator ∈ {1,2,3,4} × lootRadius ∈ {8,15,25} × searchBurst ∈ {4,8} ×
frontierFarthest ∈ {false,true}` (48 combinations) over 40 seeds and writes
`tools/ci/baseline_tuning.json` (`{"seeds":40,"totalDepth":83,
"totalScore":4365450,"params":{…}}`); `test_nethack_driver.nim:252-262` pins the
shipped `DefaultBaselineParams` to that file field by field.
The live smoke agrees: `episode end reason: complete`, and the committed fixture
settles `reason: complete, endRule: death`.

**8 — LLM reply handling.** Tolerant extraction: `directives.nim:56-94` scans for
the outermost balanced `{…}` with string/escape awareness and falls back to
first-`{`…last-`}`; `test_nethack_driver.nim:234-239` feeds
`"Sure!\n```json\n{…}\n```\nHope that helps."` and asserts it parses.
Retry exactly once: `while attempt < 2` (`decide.nim:175`), `deadlineMs =
attempt1Ms` then `retryMs` (`:180-181`), with the retry appending an explicit
"reply with ONLY the JSON object" nudge (`:183-185`).
Fallback to the scripted `delver`: `decide.nim:232` calls `engine.delverReply`,
which calls the **same** `delverPlan` proc the baseline uses (`decide.nim:101-105`);
`test_nethack_driver.nim:162-170` asserts the two produce identical action JSON
over 40 states.
Recorded for phase 60: a `fallback` chat record with turn/attempt/cause/detail
(`decide.nim:60-67`), `results.fallbackTurns` (`sim.nim:1016`), and the two log
phrasings the note pins — attempt 1 echoes
`"nethack llm: attempt 1 failed, will retry: "` (`decide.nim:227`) and only a
genuine second failure (or a guard) echoes
`"nethack llm: seat falling back to delver ("` (`:241`, `:150`, `:159`). The
no-credentials path also prints `"the LLM provider is unavailable"`
(`llm.nim:118`).

**9 — Rune-safe truncation.** `truncateRunes` (`sim_types.nim:283-291`) is the one
shortening proc and uses `runeSubStr`. Caps: `MaxSayRunes 140`,
`MaxNoteRunes 400`, `MaxPromptRunes 4000`, `MaxPolicyLabelRunes 64`,
`MaxFallbackDetailRunes 200`, `MaxMessageRunes 160`, `MaxStopDetailRunes 200`
(`sim_types.nim:38-47`) — the note's three re-pinned values match exactly. Applied
at: `say`/`notes` (`directives.nim:44, 54`), the prompt at registration
(`server.nim:406`), the policy label (`:410`), every message line (`sim.nim:86`),
captured provider error text (`llm.nim:159, 168, 174, 190`), the fallback detail
(`decide.nim:66`) and the whole directive record
(`directives.nim:221-245`, which shrinks `say` rather than byte-cutting the
serialised JSON). Tests: `test_nethack_driver.nim:217-232` (600 × U+1F600 → exactly
400 runes, `validateUtf8() == -1`) and `test_nethack_replay.nim:158-203`, which
fills every capped field with 900 × U+1F480, runs `tools/replay_summary.py` over
the bytes and asserts `summary.validateUtf8() == -1` and that it parses.

**10 — Manifest validates.** `game.docs` has `readme` + `pages[]` with
`id`/`title`/`content` (see F17 on the `type` value); `game.protocols` carries both
`player` and `global` as `{"type","value"}` objects. `results_schema` is
`additionalProperties: false` and its 47 property names are **exactly** the 47 keys
`runResultsJson` emits (verified by set difference in both directions, and by
`test_nethack_engine.nim:49-66` at runtime). Enums match the note:
`reason ∈ {complete,deadline,fault}`, `endRule ∈ {death,bottom,escaped,turnCap,
wallClock,fault}`, `causeOfDeath ∈ {killed,starved,burned,none}`,
`deeds items ∈ {fed,hoard,oracle}`. `config_schema` is
`additionalProperties: false`, `required: ["tokens","players"]`, every array
property carries `minItems`/`maxItems` (`tokens` 1/1, `players` 1/1, `slots` 0/1,
`levelLadder` 0/5), no `game_config` contains a literal `tokens` array, `game.tags`
is absent, six top-level `tags`, `episode_timeout_minutes: 20` at top level,
`player[0].resources.limits.cpu == "1"`, `game.name == "nethack" ==` the slug `==`
the secret namespace in
`game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/nethack/anthropic_api_key"`.
`tests/test_nethack_manifest.nim:19-138` asserts all of the above, and `:140-169`
constructs a real `GameConfig` from every variant and the cert fixture and plays it.

**11 — Legible at 360 px.** See F18. The rule ships verbatim at `:4292-4299` and the
labels are hidden under `.tiny` (`boardW <= 620`).

**12 — Release order and scaffold.** `coworld-release.yml` step order read from the
file: "Build the Coworld manifest" (`:159`) → "Certify locally" (`:173`, with
`--timeout-seconds 300` at `:184`) → "Upload the policies" (`:216`) → "Upload the
Coworld" (`:314`) → "Put the Coworld secret" (`:410`). All three workflows present.
`tools/ci/docker_smoke.sh` is `-rwxr-xr-x`; `tools/build_replay_viewer.sh` is
`-rwxr-xr-x`; `ci.yml` asserts both bits and invokes both by path. Any smoke step
uses a binary built in the same run (`docker build -t "${IMAGE}:ci" .` immediately
before `./tools/ci/docker_smoke.sh "${IMAGE}:ci"`).
`tools/ci/policies.json` has four distinct policies, all `run: /bin/nethack-player`,
one image: `nethack-divemaster` (`PLAYER_PROMPT`), `nethack-loremaster`
(`PLAYER_PROMPT`, `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`),
`nethack-delver` (`PLAYER_SCRIPTED=delver`), `nethack-bumbler`
(`PLAYER_SCRIPTED=bumbler`). Both prompt texts are the note's champion texts.
Placeholder gate:
`grep -n '<slug>\|<IMAGE>\|<SEATS>' ci.yml coworld-release.yml coworld-submit.yml
tools/ci/docker_smoke.sh tools/ci/policies.json` → **exit 1, no matches**.

**13 — Viewer executes.** `wasm-viewer` is green at the reviewed sha with
`needs: docker-smoke`, and its **"Load the bundle in a real browser"** step ran and
succeeded (step 11 of 13, conclusion `success`; not `continue-on-error`), invoking
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
dist/smoke/replay.json --timeout 90 --soak 10 --strict-text-bounds` and printing
`{"loaded":true,"ms":376,…}` plus a soak that advanced `0 / 322 → 96 / 322 →
120 / 322`.
Markers: `replay-viewer/static_replay.js` sets
`setAttribute('data-replay-loaded', 'true')` from the worker's `'loaded'` branch and
`'data-replay-error'` in `showFailure()` — both inherited unchanged from the starter
(the whole file diffs to two lines: the worker name and
`window.CtfStaticReplay → window.NethackStaticReplay`).
Bootstrap consistency: `replay-viewer/config.nims` contains **no** `MODULARIZE` and
no `EXPORT_NAME` (grepped; asserted at `test_nethack_viewer.nim:152-159`) and
`replay-viewer/static_replay_worker.js:188` sets `Module.onRuntimeInitialized`
and imports `('./wire_constants.js', './broadcast_core.js', './nethack_replay.js')`
in that order (`:239`) — both files come from `coworld-ctf` and diff to renames
only. `-s ABORTING_MALLOC=1`, `-s ALLOW_MEMORY_GROWTH`,
`-s ENVIRONMENT=web,worker,node`, `-s FILESYSTEM=1`,
`-s EXPORTED_RUNTIME_METHODS=HEAPU8` and the thirteen
`_nethack_*` exported functions are all present and match the symbols
`replay-viewer/nethack_replay.nim` actually exports (`:45, 72, 76, 93, 96, 99, 102,
105, 108, 113`) and the worker actually calls.
Playback opens at the game start: `startTick` is `0` (`replays.nim:118`,
`replayStartTick` at `:130`) and **the replay contains no lobby frames** — the
server writes hash records only inside the Playing branch
(`server.nim:504`), so tick 0 of the replay axis is the first dungeon tick.
`chrome_common.js:465-471` uses `st` for the scrubber axis, and
`nhBeat`'s `scrubGeometry` (`replay_broadcast.html:4550-4555`) uses the same
origin. `beginTurn` also flips the phase out of `Lobby` on the first command turn
(`driver.nim:76-77`, commit `d544d55`), so the clock never reads "waiting for
players" over a moving board. The `bitworld` replay codec has no `gameStarts`
concept (`ReplayData` at `/root/.nimby/pkgs/bitworld/src/bitworld/replays.nim:57-66`
holds `joins/leaves/chats/debugSprites/inputs/hashes` only), so the checklist's
`gameStarts[0].tick` clamp has no analogue to omit here.

**14 — Chrome provenance.**
`sha256sum client/chrome_common.js` =
`7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, 40 022 bytes,
and `diff` against the starter is **empty**. Pinned as a literal at
`tests/test_nethack_viewer.nim:7-8, 28-37`.
`client/replay_broadcast.html` is 240 555 B / 4 871 lines against the starter's
234 070 B / 4 660 lines — it **grew**. The full `diff` (read in its entirety)
consists of: the note's listed element removals; the note's listed label
re-mappings (`lk-cap`, `clock-caption`, `mmwarn`, `fpv-cap`, `btn-spoilers` title,
`momentum-label`, the four `ec-thead`/`fl-cap` strings); the `PaintballChrome →
NethackChrome` / `CtfStaticReplay → NethackStaticReplay` / `ctf-shell →
nethack-shell` renames; the scorebug plate contents; and the appended game block
under the banner `NETHACK additions to the inherited coworld-ctf chrome`
(`:4265`, the starter's own banner at `:4344` renamed). CSS sections 1–5 — stage,
scorebug, banner lane, kill feed, transport, scrubber + momentum + beat markers +
lulls + spoilers, endcard, locker-room curtain — are all present above the banner
and otherwise byte-for-byte.
Transport rules:
(a) `relayout()` (`:4197`) sets `--hudscale` (`:4232`), `--topband` (`:4237`) and
`--band` (`:4238`) on `root` = `document.documentElement`, and toggles
`stage.classList.toggle('tiny', boardW <= 620)` (`:4233`).
(b) the game block's own additions are top-band- or panel-anchored (see F15).
(c) `#endcard { bottom: var(--band, 0px) }` (`:961`), shown with `#endcard.on`
(`:972`, `renderEndcard`), and taken down on **every** frame whose phase is not
`gameover` — `else { $('endcard').classList.remove('on'); }` (`:1978`), the
starter's path kept — which covers scrub clicks, beat markers, back/forward and
keyboard, since all of them re-simulate to an earlier tick.
(d) beats are labelled `<button>`s: `nhBeat` (`:4557-4577`) creates
`document.createElement('button')`, sets `title` and `aria-label`, and seeks with
`CTX.send('s:' + tick)` on click. CSS exists for exactly the ten emitted kinds —
`.beat-marker.descend/.ascend/.levelup/.deed/.oracle/.death/.bottom/.escaped/
.fallback/.end` (`:4457-4508`) — and the four ctf kinds plus the four paintball
kinds are gone (`test_nethack_viewer.nim:86-88` asserts their absence in the whole
page). The block never calls `markBeat` (`test_nethack_viewer.nim:69-76` asserts
neither `markBeat` nor any of ten other chrome aliases is redeclared in the
appended half).
`#viewpanel` kept in full and wired — see F5 for the camera caveat.

**15 — Drawn strings.** `--strict-text-bounds` is on `ci.yml`'s smoke step;
`never_inside == 0`; see F19 on `total == 0`.

**Other things verified while tracing.**
- The eight-neighbour order `e, se, s, sw, w, nw, n, ne` is one table
  (`sim_types.nim:165-167`) used by the BFS, the monster AI, the wander draw and
  `dirIndex`.
- `mix64` casts all four words through `int64` before `uint64`
  (`sim_types.nim:254-263`), which is what makes the native↔wasm32 hash chain
  exact; `hashRnd` is `mix64(...) mod n` (`:265-269`) — a pure hash read, never a
  stream. `tests/test_nethack_dungeon.nim:94-133` asserts level `k` is unchanged by
  what happened on level `k−1` over a 500-seed × 8-depth sweep in release.
- Level generation matches the note's ten numbered steps where I checked them:
  `roomCount = 6 + rnd(3)` (`dungeon.nim:568`), `trapCount = (depth+1) div 2`
  (`:479`), `goldPiles = 2 + (depth mod 3)` (`:442`), exactly one food item
  (`:451-457`), `1 + (depth mod 3)` extras (`:459`), stairs in the lowest-index
  used slot and the farthest-hops room, ties by lowest index (`:386-420`), secret
  doors downgraded until the level is connected with every remaining secret door
  treated as rock (`:542-563`), monsters never in the arrival room (`:503`).
- Visibility is exactly the note's rule: lit room → whole floor + wall ring + doors,
  else own cell + 8 neighbours (`dungeon.nim:701-720`); monsters are drawn only when
  currently visible and never merged into memory (`:722-734`, `:742-745`); a secret
  door is remembered as `tRock` (`:731-733`).
- Combat: floating-eye paralysis fires on hit **and** miss (`sim.nim:309-313`);
  a zero-damage species never attacks (`:635-636`); the grid bug is restricted to
  `e,s,w,n` (`mobs.nim:98-101, 131`); the movement-point identity is
  `(t*speed) div 12 - ((t-1)*speed) div 12` (`mobs.nim:17`).
- Hunger thresholds are exactly `>1000 / ≥150 / ≥50 / ≥1 / else`
  (`sim_types.nim:293-298`); death at `nutrition <= -200` (`sim.nim:673-675`);
  `Weak` costs 2 to hit (`sim.nim:277-279`), blocks kicking (`:493-495`) and blocks
  regeneration (`:746-750`).
- Scoring is `100_000*(depthReached-1) + 10*min(gold,2000) + 50*min(xp,1000) +
  5_000*deedCount` (`sim.nim:196-207`); `win[0] = depthReached >= parDepth`
  (`:946`); `winner` is `0` or `null` (`:976`); death subtracts nothing.
  `tests/test_nethack_scoring.nim` asserts the formula over 500 randomised end
  states, the 85 000 < 100 000 dominance bound, the 785 000 / 485 000 maxima, the
  zero minimum, and that `cellsTotal` is derived from `dungeonLevels`.
  The committed fixture arithmetic checks out by hand:
  `100000*1 + 10*74 + 50*15 + 0 = 101 490` = `scores[0]`.
- Replay magic is `COWLDNET` (`replays.nim:22`) with `gameName "nethack"`,
  `gameVersion "1"`, and a per-tick hash written at `server.nim:504`. The resolved
  config JSON (`sim_config.nim:248-294`) carries seed, variant, `num_agents`,
  `players[].name`, `slots`, `fastMode`, the level ladder and every rule constant —
  self-sufficiency asserted at `test_nethack_replay.nim:56-97`. I confirmed it
  independently: `python3 tools/replay_summary.py tests/fixtures/descend-seed42.replay`
  yields `{"protocol":"nethack/v1","gameName":"nethack","gameVersion":"1","seed":42,
  "variant":"descend","names":["delver"],"aliases":["Alpha"],
  "policyKinds":["scripted"],"tickCount":322,"fallbacks":0, …}` with the full
  results document.
- The five results identities hold on the fixture: `Σ levelTurns = 34 = turnsPlayed`;
  `Σ levelTicks = 322 = finalTick`; `Σ levelGold = 74 = goldPickedUp`;
  `depthReached = 2 = max{i+1 : levelTicks[i] > 0}`; `deedCount = 0 = len(deeds)`.
- Registration interception: the seat's Sprite v1 chat text is parsed as a
  registration object and consumed (`server.nim:197-218, 400-425`); anything else
  from the seat is dropped; the server logs `::error::the joined seat never sent a
  registration record; refusing to start it as a silent default` on the lobby
  timeout (`:456-459`); `declarePlayerFailure` writes exactly
  `{"failed_policy_index", "message"}` (`:220-230`).
- The player websocket closes on a token mismatch (`server.nim:104-116`,
  `tokenMatches` at `:79-87`); `GET /client/player?slot&token` is token-checked and
  serves HTML **without** opening a socket (`:134-147`); `/healthz`, `/global`,
  `/client/global` and `/replay-data` are all registered before the catch-all
  (`:167-168`); global broadcasts are fire-and-forget with a 900 KB frame cap
  (`:232-249`).
- Seed randomisation happens **before** `config.update` (`src/nethack.nim:57-61`),
  with a `LegacyFixedSeed` sentinel and OS entropy.
- `Dockerfile` builds both binaries in one image (`:49-59`) and the runtime stage
  copies `data/`, `client/` and `*.json`; `compose.yaml` declares **one** service
  `nethack` ⇒ placeholder `{{NETHACK_IMAGE}}`, which is what both `game.runnable`
  and `player[0]` reference.
- `docs/` carries `RULES.md`, `ACTIONS.md`, `PROTOCOL.md`, `PORTING-NETHACK.md` —
  the three the manifest's `pages` point at, plus the protocol both `protocols`
  entries point at.

---

## Could not determine

- **Whether any chrome element actually overlaps the transport band at 360 px.**
  F15 records that `#chrome` is `inset: 0` and that `#killfeed`/`#fpv` use fixed
  `--u` offsets rather than `var(--band)`, inherited unchanged from the starter.
  Deciding this needs a rendered measurement at a 360 px viewport with the real
  `--band`; `tools/ci/viewer_smoke.mjs` was run at the default width and reports no
  per-element geometry. What would settle it: a `viewer_smoke.mjs` run with a
  360 px viewport, comparing each chrome element's `getBoundingClientRect().bottom`
  against `innerHeight − parseFloat(getComputedStyle(documentElement).getPropertyValue('--band'))`.
- **Whether `#viewpanel`'s minimap is legible/useful at the shipped fit-whole
  zoom.** F5 establishes the camera behaviour from the code; whether the operator
  reads the resulting 7.5 px/cell board at 360 px as acceptable is a judgement a
  screenshot would settle. The `viewer-smoke.png` artefact from run 33225421389
  (artifact `viewer-smoke`, id 9706728066) would show it at the default width; a
  360 px capture would show the case the note argues about.
- **Whether an LLM-driven episode stays inside the budget in practice.** Every
  bound is explicit and I traced the arithmetic (§Traced, item 5), but
  `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`, so the CI episode never made
  a provider call: `llmTurns 0`, `fallbackTurns 0`, wall clock 3.4 s. Only a phase-60
  run with a real key exercises `attempt1Ms`/`retryMs`/`turnSpacingMs`/the rate
  guard against real latency.
- **Whether `docs/SPEC.md`'s definition-of-done check 4 is met**, since
  `docs/SPEC.md` is not in this repo and the note substitutes the
  `tools/replay_summary.py` recipe (`design.md:1386-1397`). The recipe's own
  preconditions are met on the committed fixture (`protocol == "nethack/v1"`,
  `results.reason == "complete"`, `results.depthReached == 2 ≥ 2`), but the
  `source == "llm"` / non-empty `say` clauses cannot be checked without a real
  LLM episode.
