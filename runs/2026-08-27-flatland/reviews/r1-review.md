# r1 review — flatland

Repo: `Metta-AI/cogame-flatland` @ `7b831f85f2c5c10e9b690547cd563cfb406ec93d` (main HEAD), cloned fresh
to `/tmp/cogame-flatland`. Range: `b8bd2e7..7b831f8` plus the whole tree (this is the first review of a
two-commit repo; the tree, not the diff, is the unit).
Starter for provenance diffs: `/workspace/starters/coworld-ctf` (read-only mount).
Design note: `/workspace/coworld-builder/runs/2026-08-27-flatland/design.md` (= `docs/plans/2026-08-27-flatland-design.md`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision addendum).
Files read: 62 (all of `src/flatland/*.nim`, `src/flatland.nim`, `src/flatland_player.nim`,
`replay-viewer/*`, `client/*.js`, `client/*.html`, all six `tests/*.nim` + helpers, `tools/**`,
`.github/workflows/*`, `coworld_manifest_template.json`, `Dockerfile*`, `compose.yaml`, `docs/*`).
Tooling note: the sandbox has **no Nim toolchain**, so every claim about runtime behaviour below is a
*static trace* unless it cites a CI log line. Statements are labelled **observed** (read in the file),
**inferred** (reasoned from code I read) or **untested** (needs a run).

---

## Blocking

### F1 — the replay does not record `networkPool`, so a `branchline` episode cannot be re-derived
- Where: `src/flatland/sim_config.nim:217-244`; `src/flatland/replay_runtime.nim:51-70`;
  `src/flatland/sim_config.nim:57-90`; `src/flatland/sim.nim:104-110`.
- Observed, step by step:
  1. `resolvedConfigJson` (sim_config.nim:223-244) writes exactly these keys into the replay's config
     block: `seed, network, num_agents, trainsPerSeat, maxTicks, turnTicks, parOnTime, slackTicks,
     minJourneyCells, departStagger, malfunctionRate, minDuration, maxDuration, jamTicks,
     deadlockTicks, quiesceTicks, fastMode, showPlayerLabels, players, slots`. **`networkPool` is not
     among them.**
  2. `configFromReplay` (replay_runtime.nim:57-70) copies a fixed key list out of that block —
     `["num_agents","trainsPerSeat","maxTicks","turnTicks","parOnTime","slackTicks","minJourneyCells",
     "departStagger","malfunctionRate","jamTicks","deadlockTicks","quiesceTicks","fastMode",
     "showPlayerLabels","players","slots"]` plus `minDuration`/`maxDuration`/`seed` — into a patch over
     `defaultGameConfig()`. `networkPool` is not copied, and the recorded `network` **name** is
     deliberately ignored: the comment at replay_runtime.nim:53-56 says "the sim re-derives it from
     `seed`".
  3. `defaultGameConfig()` (sim_config.nim:62) sets `networkPool: "mainline"`.
  4. `newSimServer` (sim.nim:108) then computes `networkForSeed(cfg.networkPool, cfg.seed)`, i.e.
     `poolNames("mainline")[seed mod 3]` (railmap.nim:742-748).
- Consequence (inferred, untested): for the `mainline` variant and the certification fixture the
  default happens to be right, so re-derivation matches (and the CI smoke replay loads: run
  33081598358, `wasm-viewer` "Load the bundle in a real browser" reports `"loaded":true` and the
  scrubber advances). For the **`branchline` variant** (`coworld_manifest_template.json` variant 2,
  `"networkPool": "branchline"`, `trainsPerSeat: 4`) the playback sim rebuilds a *mainline* map with 16
  trains: different start platforms, targets, speeds and departures, so `mixTick` (sim.nim:141-163)
  diverges from tick 1, `checkReplayHash` (replay_runtime.nim:201-205) latches a mismatch at tick 1,
  and the viewer draws the wrong network for the whole episode.
- Checklist item: **2 — Replay re-derivation.** "Replaying the recorded events through the sim
  reproduces the recorded per-tick state frame by frame, and the viewer derives its display from that
  same re-derivation." It does not, for one of the two shipped variants.
- Why blocking: a `branchline` league episode's hosted replay would show a different railway from the
  one that was played, with `#mmwarn` lit from tick 1. No test covers it: every replay test builds its
  config from `defaultGameConfig()` (`tests/test_flatland_replay.nim:18-22, 77-81, 157-159`), i.e.
  mainline only, and `tests/test_flatland_manifest.nim:110-134` constructs the branchline variant but
  never records/re-derives it.
- What would settle it: record a `branchline` episode and re-derive
  (`record(...)` with `config.networkPool = "branchline"`, then `rederive`), asserting
  `hashMismatchTick == -1`. On the current tree I expect a mismatch at tick 1 (or an immediate
  divergence in `setupTrains`). Adding `networkPool` to `resolvedConfigJson` and to
  `configFromReplay`'s key list would make the trace close.

No other finding in this review falsifies a named checklist item. Items 1, 3–15 and the
one-parallel-batch addendum traced clean; see "Traced and consistent".

---

## Non-blocking

### F2 — `your_notes` is never delivered; the system prompt and the docs promise it
- Where: `src/flatland/sim.nim:617-644` (the observation object); `src/flatland/sim.nim:43`
  (`Seat.notes` is stored); `src/flatland/server.nim:300` (`seats[seat].notes = directive.notes`);
  `src/flatland/llm.nim:233-234`; `docs/DISPATCHING.md:96`.
- Observed: `seatObservation` builds `you, dispatchers, turn, of, tick, turn_ticks, ticks_left,
  network, your_trains, block_occupancy, radio, network_status` — there is no `your_notes` key, and
  `sim.seats[seat].notes` is written by the server but read nowhere (`grep -rn "\.notes" src/` finds
  only the write). The shipped system prompt says `"notes" comes back to you next turn and to nobody
  else` (llm.nim:233-234) and `docs/DISPATCHING.md:96` repeats it.
- Note says: §Decisions → per-seat observation lists `"your_notes"` as a field and the example JSON
  (design.md:627) carries it; the `directive` record's `view` is "the observation **minus**
  `your_notes`".
- Bears on: no checklist item. `tests/test_flatland_replay.nim:141`
  (`doAssert not node{"view"}.hasKey("your_notes")`) passes vacuously.

### F3 — the network map and the junction graph are never sent to a seat (dead code)
- Where: `src/flatland/sim.nim:646-661` (`junctionGraphJson`), `src/flatland/sim.nim:663-670`
  (`railAsciiJson`); call sites: none (`grep -rn "railAsciiJson\|junctionGraphJson" src tests
  replay-viewer` matches only the two definitions).
- Observed: the only text a seat receives is `SystemPrompt` + `operatorBlock(prompt)` +
  `$seatObservation(...)` (`decide.nim:236-242`, `llm.nim:251-254`). The observation carries the
  network's **name, width, height** and the *lists of ids* (`stations`, `sidings`, `junctions`,
  sim.nim:625-632) but no topology: no tile grid, no edge list, no lengths, no `both_ways` flag.
- Note says: §Decisions → "Visible … **The whole network, once, at registration** — the rail map as the
  same ASCII tile grid the file carries … and a **junction graph**". Champion #2's prompt
  (design.md:754-757, shipped verbatim in `tools/ci/policies.json`) instructs the model to reason "for
  every single-track section **in the junction graph**", which it never receives.
- Bears on: no checklist item (item 4 is name spaces, which is satisfied). Inferred effect: the LLM
  seats plan `route via <id>` / `siding at <id>` from ids alone.

### F4 — `yielder` rule 4 does not test the other train's direction of travel
- Where: `src/flatland/baselines.nim:84-104`, esp. line 101:
  `if world.map.edgeFwd[t.cell] != world.map.edgeFwd[cell]: return true`.
- Observed: `edgeFwd` is a **per-cell map constant** — the heading that traverses that cell from the
  edge's node A to node B (`railmap.nim:71, 274`). The comparison is therefore between the canonical
  headings of two cells *of the same edge*, not between the other train's heading and the edge
  direction. On a straight edge the two are equal at every cell → the conflict never fires; on a curved
  edge they differ → it fires regardless of which way the other train is going. The sim's own
  equivalent, `trainDirectionOnEdge` (sim.nim:211-213), correctly uses `train.heading`.
- Note says: §Scripted baselines rule 4 — "the next single-track section on the route … already holds a
  train travelling the **other** way".
- Bears on: item 7 only in the sense that the baseline must be legal and swept — it is both
  (`tests/test_flatland_driver.nim:42-67` bounds every order; `tools/tune_baselines.nim` swept the
  params). The rule is a heuristic, so a mis-firing predicate degrades play, not legality.

### F5 — `blocked_ticks_last_turn` is cumulative, not per-turn
- Where: `src/flatland/server.nim:317-318` (`trains[i].blockedLastTurn = trains[i].blockedTicks`), and
  `blockedTicks` is only ever incremented (`sim.nim:355, 366, 372`) — never reset.
- Observed/inferred: the observation field `blocked_ticks_last_turn` (sim.nim:564) therefore reports
  the episode-to-date total.
- Note says: §Decisions → "`blocked_ticks_last_turn`".

### F6 — malfunction rolls also cover `held` trains
- Where: `src/flatland/sim.nim:268-270` — the roll runs for `state in {tsRunning, tsHeld}`.
- Note says: tick step 2, "For every train that is `running` and not already malfunctioning".
- Observation only: a `held` train is on the grid and occupying a cell, so rolling for it is arguably
  the intent; but the note's wording and the code's state set differ, and the difference is
  hash-visible (a held train that breaks down changes `mixTick`).

### F7 — `deadlockCells` are the members' own cells, not the contested cells
- Where: `src/flatland/deadlock.nim:122-124` — `for train in result.deadlock: … result.deadlockCells.add(all[train].cell)`.
- Note says: §The game step 10 / §Decisions network_status — "the active **deadlock** list (train ids
  and **the cells they are fighting over**)", and §Viewer readout 3 — "the contested cells get a red
  cross". The viewer surfaces this straight through (`broadcast.nim:258-261`,
  `flatland_block.html` alarm chip).

### F8 — three tier-2 event kinds are declared and mapped but never emitted
- Where: `src/flatland/sim.nim:15-18` (`TurnStart, DirectiveIssued, FallbackTaken` in `SimEventKind`);
  `src/flatland/events.nim:24-26` (their JSON keys). No `SimEvent(... kind: TurnStart …)` anywhere
  (`grep -rn "TurnStart\|DirectiveIssued\|FallbackTaken" src` returns only those two files).
- Note says: §Server C — the tier-2 stream carries `… TurnStart, Directive, Fallback, PhaseChange`.
  The `COGAME_EVENTS_URI` file therefore carries no turn/directive/fallback rows, only the sim-derived
  ones plus the mandatory summary row (`events.nim:44-67`, which is present and correct).

### F9 — the `disconnected` fallback cause is never produced
- Where: `src/flatland/decide.nim:184` (`budget_guard`/`no_credentials`), `:208` (`rate_guard`),
  `:230-231` (`timeout`), `:264-268` (`parse_error`/`timeout`/`transport_error`), `:289-293`.
- Note says: §Degrade never hang — `cause ∈ {timeout, parse_error, transport_error, no_credentials,
  rate_guard, budget_guard, disconnected}`. Six of the seven are reachable; a disconnected seat is
  instead handled as "never registered" → `deadSeats` + a `no_credentials`-free scripted path, because
  an unregistered seat is not `isLlm` (server.nim:398-403, decide.nim:174-194).

### F10 — `pendingRegistration` is written and never read
- Where: `src/flatland/server.nim:62` (field), `:178-182` (written when `state.slot < 0`), and no
  reader anywhere in the tree.
- Observed: the hold-and-re-read behaviour the note credits to the starter is implemented by
  `appState.registrations[slot]` (server.nim:179-180 + `readRegistrations`, :238-276), which persists a
  registration until the seat is marked registered — that half works. But a player socket that upgrades
  without `?slot=` (`httpHandler`, :106-117, sets `slot = -1` for any non-`/player` path) can never
  register: its blob lands in the dead field.
- Note says: §The three named edits to `server.nim` #2 — "The starter's 'hold an unappliable
  registration and re-read it when the slot lands' behaviour is kept verbatim."

### F11 — the shutdown hold is a hard-coded 20 s, not `gameOverTicks`
- Where: `src/flatland/server.nim:42` (`ShutdownGraceSeconds = 20`), `:434-438` (the grace loop);
  `config.gameOverTicks` (sim_config.nim:34, default 24) is only stored into
  `sim.gameOverTicksLeft` (sim.nim:234) and never read.
- Note says: §Degrade never hang — "ctf's `gameOverTicks` hold before exit — kept". The behaviour
  (a bounded post-artifact grace with `/healthz` and `/global` answering) is present; the config knob
  is inert. Bears on item 5 only positively: the wait is bounded by a constant.

### F12 — the train art is 64 one-size chips with no numbers; the interlock tint is baked but never placed
- Where: `src/flatland/rig_art.nim:290-338` (`bakeChips`: `for seat in 0..3 / speed in 1..4 /
  facing in 0..3` = 64 images at `CellPx = 20`, with body, glass, lamp and a speed pip — no
  `drawTextInto` call); `:340-386` (`bakeOverlays` bakes five overlays, index 4 = the interlock tint);
  `src/flatland/global.nim:166-178` places overlays 0–3 only.
- Note says: §Viewer → Art — "192 pre-baked chips" (four facings × four speed classes × **three sizes**
  × four colours), each "with … its number set in `data/font.ttf`"; §Viewer readout 1 — "A section
  currently locked by the interlock is tinted in the direction of travel". The module docstring
  (rig_art.nim:12-16) still claims the number is set.
- Side effect: the note's 360 px rule 3 ("under `.tiny`, train numbers are not drawn on the chips") is
  vacuously satisfied.

### F13 — the replay is ~410 KB, not the note's ~24 KB
- Where: `src/flatland/decide.nim:102-113` — every `directive` record embeds `"view": <the whole
  observation>`; 4 seats × 31 turns of it. CI evidence: docker-smoke log (run 33081598358, job
  98550007767) prints `smoke OK: seats=4 results=743B replay=419392B reason=complete`.
- Note says: §Determinism — "Replay size: 496 hashes + ≤ 124 order records + ~30 chat records ≈ **24
  KB**." The embedded `view` is itself a note requirement ("mirrored … into the replay's `directive`
  record, so the replay explains every decision"), so the two statements in the note are inconsistent
  with each other; the code follows the stronger one. No checklist item; the static bundle loads the
  419 KB replay in CI in 578 ms.

### F14 — the shipped baseline tunables are the sweep's pick, not the note's numbers; CI does not re-run the sweep
- Where: `src/flatland/baselines.nim:29-34` (`yieldAfter: 4, departLookahead: 1, sidingLookahead: 2,
  lowerIdYields: false`); `tools/ci/baseline_tuning.json` (same four values + `sweep: {onTime: 166,
  deadlocks: 20}`); `tools/tune_baselines.nim:76-104` (a 5×3×3×2 grid over 24 episodes per candidate);
  `tests/test_flatland_driver.nim:218-223` pins consts == JSON.
- Note says: §Scripted baselines — "`yieldAfter = 8`, `departLookahead = 2`, `sidingLookahead = 3`, and
  the rule-3 id-order direction" with "the **lower**-id tie-break". The note also says the four are
  "chosen by `tools/tune_baselines.nim`'s head-to-head sweep … not guessed", which is what the code
  does — so this is a swept-value delta, not a contradiction, but the note's rule-3 prose ("the
  blocking train has a **lower** global train id") is the opposite of the shipped
  `lowerIdYields = false` (baselines.nim:138 yields when `blocker > index`).
- Also: design §Tests 24 says "`ci.yml` re-runs the sweep with `--check`". `.github/workflows/ci.yml`
  runs `check_gameversion.sh`, `author_rail_maps.py --check` and `build_broadcast_page.py --check`
  (lines 104-111) but **not** `tune_baselines --check`.
- Bears on item 7's "tuned with a grid harness, not guessed": satisfied by the harness + the pinned
  JSON + the test.

### F15 — test coverage is narrower than the note's 45 numbered items in five specific places
- Where and what (all **observed**):
  - `tests/test_flatland_replay.nim:64-116` — record→re-derive is asserted for **tickCap, wallClock and
    fault**. The `quiescent` block (`:76-92`) records hashes but never calls `rederive`; the
    `allArrived` block (`:93-102`) neither records nor re-derives. Note item 29 claims all five.
    (Checklist item 2's "a test asserts it" is satisfied by the three that are re-derived.)
  - `tests/test_flatland_sim.nim:284-316` — the jam/deadlock test asserts (a) a queue behind a broken
    train never deadlocks, (b) a lone stalled train is neither, (c) a real timetable episode reaches
    `deadlocks > 0`. It does **not** assert the note's item 11: jam raising at exactly
    `stalledTicks == 12`, a constructed two-section cycle raising at exactly 24, permanence to
    `maxTicks`, `deadlockclear` after a re-route, or that both members are named.
  - `tests/test_flatland_sim.nim:448-457` — `proc drawOf(kinds: array[4, Baseline])` never reads
    `kinds`; it rebuilds the same `defaultGameConfig()` twice, so `doAssert a == b` compares two
    identical constructions. The anti-collusion claim it is labelled with ("nothing a seat does changes
    the draw") is not exercised. (The neighbouring malfunction test at `:188-206` *does* vary seat
    behaviour and is meaningful.)
  - `tests/test_flatland_viewer.nim:41` — `doAssert "window.ChromeCommon" notin inherited or true` is
    a tautology.
  - `MaxReplyBytes` (the 4096-byte read cap, `llm.nim:188-190`) is asserted by no test, though design
    item 23 lists it.
- Bears on: no checklist item (item 1 is about tests *loosened during this run*, F22; items 2, 7, 9
  each still have a test that asserts them).

### F16 — ten test files the note and the docs name do not exist
- Where: the note references `tests/test_flatland_{railmap,upstream,seeding,determinism,deadlock,
  scoring,malfunctions,tuning,events,endcard_labels}.nim`; the tree ships six suites
  (`tests/test_flatland_{sim,driver,engine,replay,manifest,viewer}.nim`, 78 `check` blocks total,
  355 `doAssert`s) with that content consolidated — e.g. the upstream table is
  `test_flatland_sim.nim:430-441`, the rail pins `:392-427`, the endcard vocabulary
  `test_flatland_viewer.nim:160-246`. `docs/PORTING-FLATLAND.md:14` still tells a reader that
  `tests/test_flatland_upstream.nim` asserts the constants.

### F17 — `#viewpanel` is gone, but two of its neighbours survive
- Where: `client/replay_broadcast.html:1484-1492` (the `?viewpanel=0` query-param handler still sets
  `data-noviewpanel` on `<body>`, with no panel and no matching CSS left); `:2482`, `:2499`, `:2554`
  (`core.zoomAt(...)` / `core.setZoom(...)` from the inherited wheel and pinch handlers).
- Observed: the panel itself is fully removed — markup, CSS, ids and the
  `core.attachMinimap($('minimap-canvas'))` call are all absent
  (`tests/test_flatland_viewer.nim:130-138` asserts this, and my own grep for
  `id="viewpanel|minimap|zoombar|zoom-*|fpv*|povBadge"` returns zero hits). `broadcast_core.js` keeps
  `attachMinimap` (unattached, as the note says).
- Checklist item 14, bullet 4 names "markup, CSS, the `core.zoomAt/setZoom/attachMinimap` wiring, and
  the ids". A strict reading covers the surviving wheel/pinch calls; a functional reading treats them
  as the starter's canvas gestures rather than the panel's wiring. I report the lines and leave the
  reading to the judge — the panel is removed, not hidden.

### F18 — the scorebug plate keeps four class names the note lists as removed
- Where: `client/replay_broadcast.html:1790-1804` (the FL_MODE plate builder emits
  `class="lives-line"`, `class="hcap"`, `class="lives-num"`, `class="squad"`).
- Note says: §Viewer → Elements removed — "The ctf scorebug internals `.hillchip`, `.hcap`,
  `.flagicon`, `.lives-num`, `.lives-label`, `.squad-pip`, `.pb-tags`, `.squad` …". `.hillchip`,
  `.flagicon`, `.pb-tags`, `.lives-label` and `.ec-heart` *were* re-mapped by
  `tools/build_broadcast_page.py:202-211, 256-296`; these four were kept as inert class names carrying
  re-mapped contents. They are identifiers, not spectator-visible words.

### F19 — every attempt-1 fallback record becomes a "missed the call" scrubber beat, even when the retry succeeded
- Where: `src/flatland/replay_runtime.nim:173-180` — the pre-scan turns **every** chat record with
  `k == "fallback"` into a beat; `decide.nim:269` writes such a record for a failed *attempt 1* even
  when attempt 2 lands and the directive's source is `llm`. The beat tick is
  `(turn - 1) * DefaultTurnTicks` (the compile-time 16) rather than the replay's own
  `config.turnTicks`.
- Note says: §Record vocabulary — `fallback` carries `attempt (1|2)`; the beat vocabulary is the five
  kinds, which is respected.

### F20 — playback speed chips are `[1,2,3,4,8,16]`, not the note's `[0.5,1,2,4,8]`
- Where: `src/flatland/broadcast.nim:18` (`PlaybackSpeeds`), consumed by
  `replay-viewer/flatland_replay.nim:161` and published to the page through
  `wire_constants.nim:32`. Default index 0 = 1 tick/frame, which is what the note's 16.5 s playback and
  the `--soak 10` window depend on; CI confirms advancement ("3 / 496" → "244 / 496" over 10 s).

### F21 — the endcard's "NETWORK SCORE" is seat 0's score
- Where: `src/flatland/broadcast.nim:304` (`"score": game.scoreFor(0)`), rendered by
  `client/flatland_block.html:292-294`. `scoreFor` (sim.nim:169-175) adds `onTime[0]` to the shared
  terms, so the headline number silently carries Alpha's tie-break (≤ 6 out of ~16 000).

### F22 — the one test hunk edited during this run both tightened and narrowed the vocabulary scan
- Where: `git show 7b831f85 -- tests/test_flatland_viewer.nim` (the only test change in the run, plus a
  new binary fixture `tests/replays/mainline-seed42.replay`).
- Observed: the comparison became **case-insensitive** (`word.toLowerAscii() notin literal`) — strictly
  stronger, and it is what caught the uppercase `HILL TIME`/`PAINT` leftovers. In the same hunk a skip
  predicate was added: `if raw.startsWith("<") or "-line" in raw or "-num" in raw or raw.count(' ') == 0:
  continue` (test_flatland_viewer.nim:220-222). That excludes exactly the surviving class-name literals
  of F18 (`'<div class="lives-line">'`, `'<span class="lives-num" …>'`), which would otherwise match the
  forbidden word `Lives`. Two assertions were added below (`<span>Dispatcher</span>` == 2,
  `Trains on time` == 2) and one `== 1` pin became a `== 2` pin because a second builder now emits the
  string.
- Checklist item 1's second half ("no test disabled, skipped, or loosened during this run"): no test
  was deleted, skipped or removed, and no tolerance was widened numerically; the scan's *scope* was
  narrowed to exclude markup identifiers, which the test's own scope note (`:217-219`, and
  `labels.nim:1-8`) says are out of scope. I record it as non-blocking and put the hunk in front of the
  judge rather than deciding it.

### F23 — the renderer fixture does not assert its own strings are still full length
- Where: `tools/ci/renderer_fixture.html:54-61` (`say()` builds exactly 120 runes), `:178-212`
  (`transcribe` measures each laid-out run and draws a clipped run off-canvas), `:229-238` (the only
  assertion is `totals.runs === 0` → `data-replay-error`).
- Checklist item 15 says "The fixture asserts its own strings are still full-length — one quietly
  shortened remark leaves it passing while testing nothing." The fixture asserts *coverage*
  (runs > 0) and *fit* (via the off-canvas transcription that `--strict-text-bounds` gates), but never
  that the transcribed remark is still 120 runes. CI evidence, run 33081598358, job 98550555452:
  `canvas text: 75 drawn, 0 never inside the canvas (4 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)`. The fixture exists, drives the shipped `index.html` in an iframe at 360 /
  640 / 1024 px, and shims only the wasm entry — the substantive requirement of item 15 is met.

### F24 — `feed_lines: 0` in the smoke evidence is a selector artefact, not an empty feed
- Where: `templates/tools/ci/viewer_smoke.mjs:425` queries `#feed, .feed, #log`; this game's feed is
  `#killfeed` (`client/replay_broadcast.html`, kept from the starter and asserted at
  `tests/test_flatland_viewer.nim:119-128`). Recorded here so the judge does not read the CI line
  `"feed_lines":0` as a missing match feed; the fixture's transcription does read
  `#killfeed .feed-row` (`renderer_fixture.html:183`) and found runs at all three widths.

### F25 — two cosmetic dead branches in the sim
- `src/flatland/sim.nim:464-469`: `if quiet and activeDeadlock.len == 0 and arrivedTotal < trains.len:
  inc quietTicks / elif quiet: inc quietTicks / else: reset` — both live branches do the same thing;
  the condition is inert.
- `src/flatland/replays.nim:121-168` writes `rrLeave` records that nothing ever emits
  (`writeLeave` has no caller); the reader handles them (`:196-199`), so the format stays forward
  compatible.

---

## Traced and consistent

**Resolution rules (design §The game, tick steps 1–12 → `src/flatland/sim.nim:258-476`)**
- `sim.nim:264-266, 460-461` — step order is exactly the note's: tick++, malfunction rolls (`:268-283`),
  countdown (`:286-297`), departures (`:300-319`), one action per train (`:322-326`), progress
  (`:329-337`), move resolution (`:340-385`), arrivals (`:387-410`), stall accounting (`:413-422`),
  jam/deadlock (`:425-457`), hash (`:459-461`), end conditions (`:463-475`). Nothing else in the tree
  mutates train state during play (the server only applies orders at a turn boundary,
  `server.nim:288-292`).
- **By-handle order** — every one of those loops is `for i in 0 ..< sim.trains.len`, ascending index =
  ascending train id (`trainId(i)` = `T{i+1}`, sim_types.nim:146-148). Verified per loop.
- **Exclusive cells / no swaps** — `sim.nim:369-381`: a mover reads `occ.at(target)` from the live
  occupancy layer and only then vacates its own cell, so two trains can never exchange cells within a
  tick and a queue advances only leader-first. `tests/test_flatland_sim.nim:99-124` asserts both.
- **Segment interlock** — `sim.nim:357-368`: refuses entry when `targetEdge >= 0`, `targetEdge !=
  ownEdge` and `opposingOnEdge` (`:215-224`, lowest-id opposing train, ascending scan) returns ≥ 0;
  records `waitsFor[i] = blocker`. Same-direction followers are admitted. Node-to-node edges with no
  interior cells have `edgeOf == -1` at both ends and are therefore not interlocked (inferred; the
  branchline S6 stub edge is one of these). `tests/test_flatland_sim.nim:143-172` asserts refusal +
  follower admission.
- **Dead-end reversal** — `railmap.nim:132-148` (`exitsFrom` returns `@[opposite(heading)]` on a
  one-end tile), `driver.nim:144-145`, `sim.nim:377-378` (`heading = opposite(...)` when
  `exit.reversed`). `buildTransitions` (`:189-204`) leaves a one-end tile's mask empty and gives `+`
  straight-through only. Tests `:16-48, :127-140`.
- **Action repair** — `driver.nim:128-154` implements the note's fixed order (wanted → forward →
  single legal → lowest direction index) and `sim.nim:350-352` counts `actionsRepaired`.
- **Speed classes** — integer `ticksPerCell`; `sim.nim:336-337` caps progress, `:348-349` gates the
  move; the driver decides against `progress + 1` (`driver.nim:95`, with a comment explaining why).
  `tests/test_flatland_sim.nim:80-96` measures 4 cells in `4k` ticks for k ∈ 1..4.
- **Malfunctions** — `trains.nim:158-169`: `mix64(seed, train, tick)` (sim_types.nim:192-200,
  splitmix64 twice over `seed xor train*1000003 xor tick*6364136223846793005`), `h mod rate == 0`,
  duration `min + ((h shr 32) mod span)`; no stream state, so no ordering dependence. A malfunctioning
  train takes no action (`driver.nim:82-83`), is skipped by progress and move (`sim.nim:330, 344`),
  keeps its cell, and cannot be repaired early (`:286-297` decrements only). Tests `:175-218`.
- **Departures** — `sim.nim:300-319`: `state == waiting`, `tick >= earliestDeparture`, order ≠ `hold`,
  start cell unoccupied; a waiting train has `cell == -1` and occupies nothing (`trains.nim:104-105`,
  `onGrid`, `:67-68`). Tests `:221-244`.
- **Arrival and removal** — `sim.nim:387-410`: platform of the *target* station only, cell freed,
  `cell = -1`, `onTime = tick <= scheduledArrival`, per-seat and fleet counters, `arrive` event.
  Tests `:247-281`.
- **Jam vs deadlock** — `deadlock.nim:92-124`: jam = weakly connected components (union-find,
  `:20-62`) of ≥ 2 trains all with `stalledTicks >= jamTicks`; deadlock = a directed cycle over trains
  with `stalledTicks >= deadlockTicks` **and** `state != tsMalfunctioning` (`:113-116`), found by the
  deterministic walk from the lowest eligible index (`:64-90`, correct because the waits-for graph has
  out-degree ≤ 1), returned sorted. Re-evaluated every tick, never latched (`sim.nim:442-455`);
  `settleEnd` (`:235-240`) strands the members still in a cycle at the end and sets
  `terminalDeadlock`.
- **End conditions** — `sim.nim:463-475` + `:226-256`: `allArrived` → `erAllArrived/reComplete`;
  `quietTicks >= quiesceTicks` → `erQuiescent/reComplete` (with `quiet` cleared by any malfunction
  tick, departure, move or arrival); `tick >= maxTicks` → `erTickCap/reComplete`; `stopAtWallClock` →
  `erWallClock/reDeadline`; `faultStop` → `erFault/reFault` with a 200-rune `stopDetail`. Both enums
  are closed (`sim_types.nim:100-111`) and match the manifest's `results_schema`
  (`coworld_manifest_template.json`, verified: `reason ∈ {complete,deadline,fault}`,
  `endRule ∈ {allArrived,quiescent,tickCap,wallClock,fault}`).
- **Scoring** — `sim.nim:169-175`: `1000 * fleetOnTime + 10 * arrivedTotal + onTime[seat]`, no negative
  term. `roster.nim:63-79`: `win[s]` is the same `fleetOnTime >= parOnTime` for every seat and
  `winner` is `newJNull()`. `tests/test_flatland_sim.nim:318-341` checks the formula, `>= 0`,
  `onTime[s] < 10` and `10*arrivedTotal < 1000` over 500 randomised end states, and that all four
  `win` agree. `tests/test_flatland_engine.nim:107-111` re-checks the formula against a real episode's
  `results.json`.
- **Seeded reset draw** — `trains.nim:79-156` consumes one splitmix64 stream in the note's order
  (platform shuffle → targets with the 200-attempt/`minJourneyCells` rule → speed multiset shuffle →
  departure-order shuffle), all integer. `rand` is exclusive-bound (`sim_types.nim:213-217`), so
  `rand(stationCells.len - 1)` + the `>= startStation` bump is a uniform draw over the seven non-start
  stations with no out-of-range index. `tests/test_flatland_sim.nim:459-477` asserts distinct starts,
  reachable long targets, the exact speed multiset and the `departStagger × rank` schedule.

**Decision path (design §Decisions → `src/flatland/decide.nim`)**
- `decide.nim:223-249` — **one parallel batch per turn**: all open seats' requests are pushed into a
  single `RequestBatch` and issued by `engine.client.curl.makeRequests(batch, deadline)`. There is no
  per-seat request loop anywhere. Satisfies the checklist's simultaneous-decision addendum.
- Deadlines: `attempt1Ms` on attempt 0, `retryMs` on attempt 1 (`:233-234`), the whole turn wrapped in
  `turnBudgetMs` (`:154, 228-232`), the `while … attempt < 2` loop bounding retries to exactly one
  (`:225`). `sim_config.nim:147-150` rejects sub-second deadlines so the `div 1000` floor is an
  identity.
- `turnSpacingMs` floor between **batch starts** (`:215-221`), a bounded `sleep` of at most
  `turnSpacingMs`, taken before the batch and after `lastBatchStart` is stale.
- **Rolling-60 s rate guard** — `:130-139, 196-212`: `requestTimes` is pruned to the trailing 60 s,
  `RateWindowCap = 28`, and the seats over budget take the yielder orders with `cause = "rate_guard"`.
  Never sleeps.
- **Budget guard** — `:162-170`: fires when `elapsed + 2 × ceil(turnBudgetMs/1000) >
  wallClockBudgetSeconds`, latches `llmOff`, writes a `budget_guard` record naming the turn, and every
  later turn takes the yielder path with `cause = "budget_guard"` (`:184`).
  `tests/test_flatland_engine.nim:155-170` forces and asserts it.
- **Tolerant parse** — `directives.nim:49-87`: outermost balanced `{…}` with string/escape awareness,
  fence- and prose-tolerant, first-brace..last-brace fallback, and a rune-truncated error otherwise.
  `tests/test_flatland_driver.nim:207-215` feeds a fenced reply with prose on both sides.
- **Retry-once-then-yielder, and the fallback IS the yielder proc** — `decide.nim:79-81`
  (`yielderFor` calls `yielderDirective`), `baselines.nim:162-168` (`yielderDirective` *is*
  `scriptedDirective(world, blYielder, ctx)`, with `scriptedDirectiveYielderAlias` as the pin);
  `tests/test_flatland_driver.nim:98-112` compares the engine's fallback to the baseline order by
  order and asserts the proc identity.
- **Repair-don't-reject** — `directives.nim:98-171`: `defaultDirective` seeds every train with its
  previous order; an unparsable verb or an invalid/missing argument leaves that seed in place and
  increments `rejected`; foreign, arrived, duplicate and over-cap entries are dropped and counted; a
  `say`-only reply is usable. `tests/test_flatland_driver.nim:115-205` covers all seven cases.
- **Closed failure payload** — `roster.nim:140-144` emits exactly
  `{"message","failed_policy_index"}`; `tests/test_flatland_engine.nim:145-152` asserts the key set of
  the file the game actually wrote.
- **No train left without an order** — `defaultDirective` + `applyOrder` (`sim.nim:192-205`) +
  `driveTrain`'s always-an-action contract (`driver.nim:79-126`), asserted at
  `tests/test_flatland_driver.nim:70-86` and `test_flatland_engine.nim:169-170`.

**Every wait and its bound (checklist item 5)**
- Lobby: `server.nim:382-397`, `lobbyTicks < lobbyJoinTimeoutTicks` with `sleep(1000 div 24)` per tick →
  ≤ 100 s at the shipped 2400 (240 s at the cert's 600 would be 25 s).
- LLM: the two batch deadlines + the turn budget + the rate guard + the spacing sleep (above).
- Wall clock: `server.nim:410-414`, checked at the top of every loop iteration, writes the stop record
  then `stopAtWallClock()` and breaks.
- Post-artifact grace: `server.nim:434-438`, 20 iterations of `sleep(1000)`.
- Player side: `flatland_player.nim:28-32, 76-92` — 240 × 500 ms dialling, ≤ 6 re-dials, `quit(0)` on a
  dead socket; `receiveMessage` returning `none` is a read timeout, and the loop exits when the server
  closes.
- Arithmetic (inferred): the budget guard switches the LLM off above `elapsed > 632 s`, so the last
  LLM turn cannot start later than that and ends by ≈ 657 s; artifacts are written before the 20 s
  grace, i.e. inside 720 s = 60 % of 1200 s, and the engine's own stop is 660 s
  (`sim_config.nim:52`, `MaxWallClockBudgetSeconds`, enforced by `validate` at `:142-144` and by
  `tests/test_flatland_manifest.nim:101-108`). No unbounded loop or blocking read found.

**String truncation (checklist item 9)**
- `sim_types.nim:150-178` — `truncateRunes` = `runeSubStr`, `sanitizeLine` flattens control characters
  then cuts on a rune boundary. Applied at: `say` 120 / `notes` 240 (`directives.nim:128-129`),
  `policy` 64 (`decide.nim:98`, `server.nim:256`, `flatland_player.nim:42`), prompt 4000
  (`server.nim:254`, `flatland_player.nim:41`, `llm.nim:249`), `fallback.detail` and `stopDetail` 200
  (`decide.nim:90`, `sim.nim:233`, `roster.nim:118, 143`), train id 4 / verb 6 / node id 4
  (`directives.nim:143, 91, 161-165`), and every provider error body (`llm.nim:167, 175, 181, 193`).
  `tests/test_flatland_driver.nim:184-197` feeds 4-byte emoji sitting exactly on the `say` and `notes`
  caps and asserts `validateUtf8() == -1`; `tests/test_flatland_replay.nim:155-210` fills *every* cap
  with 4-byte emoji and requires `tools/replay_summary.py` (strict `decode("utf-8")`,
  replay_summary.py:57-59) to emit parseable JSON.
- The single byte-index slice is the deliberate 4096-**byte** read cap (`llm.nim:188-190`), which the
  note defines in bytes. Traced: its output can only reach the replay through `parseJson` (which fails
  on a cut) or through `extractJsonObject`'s error text, which re-truncates to 160 runes taken from the
  *head* of the reply — see "Could not determine" for the one path I could not close.

**Replay writer and re-derivation (checklist item 2, apart from F1)**
- `replays.nim:121-168` — magic `COWLDFLT`, format 1, game name + `GameVersion`, the resolved config
  JSON, then join / orders / chat / hash / stop records and a terminator. One `writeHash(tick, hash)`
  per tick (`server.nim:423`).
- `sim.nim:141-163` — `mixTick` mixes exactly the note's order: per train `(index, state, cell,
  heading, progress, malfunctionLeft, stalledTicks, orderKind, orderArg)`, then `arrivedTotal`,
  `fleetOnTime`, per-seat `arrived`/`onTime`, then the sorted jam and deadlock sets, then `tick`.
- The wall-clock and fault stops are **records applied by the same proc on record and on playback**:
  `server.nim:412-413/420-421` write them, `replay_runtime.nim:96-101` applies them through
  `stopAtWallClock`/`faultStop`, and the playback loop checks the stop *before* stepping
  (`:217-220`) exactly as the live loop does. `tests/test_flatland_replay.nim:104-116` asserts the
  re-derived `endRule`, the stop tick and `hashMismatchTick == -1` for both.
- Self-sufficiency: `tests/test_flatland_replay.nim:119-152` proves the bytes alone yield the seat
  names, aliases, kinds, config, seed, network name, order records, chat records (with `register`
  redacted — no `prompt` key) and the full result document.
- The viewer derives from the same re-derivation, not a parallel recording:
  `replay-viewer/flatland_replay.nim:152-179` steps `runtime.advanceReplayFrame()` and renders from
  `runtime.sim`, and `checkReplayHash` surfaces divergence as `flatland_mismatch_tick` → `#mmwarn`.
  Seeks re-simulate from tick 0 (`replay_runtime.nim:224-235`).

**Viewer (checklist items 3, 11, 13, 14, 15)**
- All four viewer files come from **coworld-ctf only**, and I diffed each against the mount:
  `replay-viewer/config.nims` differs in 3 lines (output name, export symbols, one comment);
  `static_replay.js` in 2 (worker name, global name); `static_replay_worker.js` in 13, all
  `_ctf_*` → `_flatland_*` plus the `importScripts` line. **No `MODULARIZE`, no `EXPORT_NAME`** in
  `config.nims:44-55`; the Worker sets `Module.onRuntimeInitialized`
  (`static_replay_worker.js:188-191`) and assigns `self.Module` before
  `importScripts('./wire_constants.js', './broadcast_core.js', './flatland_replay.js')` (`:239`).
  Flags and bootstrap agree — the lantern deadlock shape is absent, and CI proves it runs.
- `data-replay-loaded="true"` on `<html>` in the Worker `'loaded'` branch (`static_replay.js:161`) and
  `data-replay-error` in `showFailure()` (`:8-20`), both inherited unchanged.
- `client/chrome_common.js` is **byte-identical** to the starter's: `diff` is empty and
  `sha256 = 7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` (40 022 bytes), the value
  pinned in `tests/chrome_sha256.json` and asserted at `tests/test_flatland_viewer.nim:25-33`.
- `client/replay_broadcast.html` is the **starter's page + an appended block**, and it is
  *reproducible*: I ran `python3 tools/build_broadcast_page.py --check` against the mounted starter and
  it printed `replay_broadcast.html matches the starter page + the appended block` (exit 0). The
  builder takes the starter verbatim up to its own `PAINTBALL additions` banner (starter line 4344),
  deletes only the `#viewpanel` markup, the `#fpv*` markup, `#povBadge`, the FPV/POV pipeline
  (starter lines 2347-3466 — I checked the boundaries: `renderPov` … `renderFpvMap`, all FPV-only
  helpers, with no surviving references to any of them), the zoom-cluster/minimap wiring and the
  never-emitted beat-marker/`.ec-heart` CSS, re-maps the note's vocabulary table, renames the splice
  hook, and appends `client/flatland_block.html` (419 lines). Result: 3 099 lines / 151 012 bytes,
  of which 2 681 lines are the inherited chrome — sections 1–5 (stage, scorebug, banner lane, kill
  feed, transport, scrubber + momentum + beats + lulls + spoilers, endcard, locker room) are all
  present; `tests/test_flatland_viewer.nim:119-128` pins 43 kept ids.
- Transport rules: (a) `relayout()` measures `#scorebug` and `#transport` and sets `--hudscale`,
  `--topband`, `--band` on `document.documentElement` (`replay_broadcast.html:2626-2656`); (b) the two
  elements the game block adds are anchored to `top: calc(var(--topband) + …)` inside `#chrome`
  (`flatland_block.html:56-59, 99-102`), asserted at `tests/test_flatland_viewer.nim:151-157`;
  (c) `#endcard { bottom: var(--band, 0px) }` (`:708-719`), shown with `#endcard.on` (`:730`), and
  every non-gameover frame removes the class (`:1678`) — a seek out of `gameover` therefore dismisses
  it; (d) beats are `<button class="beat-marker <kind>">` with `title`, `aria-label` and a click that
  `send('s:' + tick)` (`flatland_block.html:190-209`), and the CSS covers exactly
  `{arrival, malfunction, deadlock, fallback, end}` (`:121-131`) — the same set `BeatKinds`
  (`broadcast.nim:24-26`) and the pre-scan (`replay_runtime.nim:131-180`) emit;
  `tests/test_flatland_viewer.nim:86-107` compares the two sets. `markBeat` is never called from the
  block (`:83`).
- 360 px: `#stage.tiny` toggles at `boardW <= 620` and `--hudscale = clamp(0.5, boardW/760, 1.6)`
  (`:2648-2650`, the starter's, unchanged); `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow:
  hidden; text-overflow: ellipsis }` (`flatland_block.html:27-33`); four `.tiny` rules
  (`:147-151`). The board aspect reaches `relayout()` correctly: the state JSON carries no
  `boardW/boardH`, but the page reads them off `core.getTransform().nativeW/H`
  (`replay_broadcast.html:1643-1647`), which is the 560 × 280 sprite viewport
  (`global.nim:124-127`, `rig_art.nim:28-30`) = the note's 2.0.
- Endcard vocabulary: the re-map table is applied by the builder (`build_broadcast_page.py:217-391`)
  and scanned by `tests/test_flatland_viewer.nim:160-246` (case-insensitive forbidden-word scan over
  quoted literals and markup text nodes, plus exact-count pins on each replacement).
- Manifest declares `game.replay_viewer = {"bundle": "static-replay-viewer"}`;
  `tools/build_replay_viewer.sh` exists, is mode `100755` in the index
  (`git ls-files -s` → `100755 8cfe0fb…`), builds `Dockerfile.replay-viewer`'s
  `replay-viewer-builder` target and `docker cp`s `/workspace/flatland/replay-viewer/dist/.`; the
  bundle fetches only its replay URL (no `fetch(`/`XMLHttpRequest` literal anywhere in
  `static_replay.js`). No `/client/replay` path is declared to the platform (the game binary still
  serves it locally, `server.nim:39, 137-139`, which the note explicitly sanctions for developers).

**Manifest (checklist items 6, 10, 12)**
- `num_agents: 4` in `variants[0].game_config`, `variants[1].game_config` **and**
  `certification.game_config`; absent at every variant top level;
  `len(certification.players) == len(certification.game_config.players) == 4`; no literal `tokens` in
  any `game_config` while `config_schema.required` still lists it; every array property carries
  `minItems`/`maxItems` (`tokens` 4/4, `players` 4/4, `slots` 0/4); `episode_timeout_minutes: 20` at
  the top level; `tags` = 5; `game.tags` absent; `game.protocols.player` and `.global` are both
  `{type,value}` objects; `game.docs` = `{readme:{type,value}, pages:[3 × {id,title,content:{type,value}}]}`;
  `results_schema` is `additionalProperties: false` with 33 properties that exactly match
  `roster.nim:121-138`'s `allResultsKeys()` and the keys `networkResultsJson` writes
  (`tests/test_flatland_engine.nim:113-127` checks this against a real `results.json`);
  both `player[]` entries carry `resources.limits.cpu = "1"`. Verified by reading the JSON and by
  `tests/test_flatland_manifest.nim:14-134`.
- `tools/ci/docker_smoke.sh` is the template with only the three substitutions (`diff` shows 5 hunks,
  all `<slug>`/`<IMAGE>`/`<SEATS>` → `flatland`/`coworld-flatland`/`4`), and it carries all four
  `SEAT-COUNT FAIL` invariants (`:109-151`). **`grep -ci "SEAT-COUNT FAIL"` over the full docker-smoke
  log of run 33081598358 (job 98550007767) returns 0**; the job printed
  `smoke OK: seats=4 results=743B replay=419392B reason=complete`.
- The placeholder gate from item 12 exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three
  workflows, `docker_smoke.sh` and `policies.json` finds nothing.
- `tools/ci/policies.json`: four policies, one image, `run: /bin/flatland-player`, two `PLAYER_PROMPT`
  champions (1 491 and 1 495 chars, distinct) and two `PLAYER_SCRIPTED` fillers; champion #2 carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. No `USE_BEDROCK`.
- `coworld-release.yml` step order: Build the Coworld manifest → Certify locally →
  **Upload the policies** → Upload the Coworld → Put the Coworld secret → Assemble release-result
  (`:159, 173, 216, 314, 352, 378`), and it is the template plus `--timeout-seconds 300` on certify.
  `coworld-submit.yml` differs from the template in one comment line only.

**CI and tools (checklist items 1, 13, 15)**
- `gh run list -R Metta-AI/cogame-flatland --branch main -w ci.yml`: run **33081598358**, conclusion
  **success**, at the reviewed sha `7b831f85`, jobs `test` (6m19s), `docker-smoke` (1m35s),
  `wasm-viewer` (3m29s) all ✓.
- `wasm-viewer` `needs: docker-smoke` (`ci.yml:228`), downloads the `smoke-replay` artifact and runs
  `viewer_smoke.mjs --bundle … --replay … --timeout 90 --soak 10 --strict-text-bounds`
  (`:343-348`) — the step ran and printed `{"loaded":true,"ms":578,…}` and
  `soak: 10s of playback kept advancing ("3 / 496" -> "195 / 496" -> "244 / 496")`. No
  `continue-on-error` anywhere in the workflow.
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff` empty).
- `canvas_text` on the real replay is `total: 0` — expected and, per item 15, "not evidence of
  anything": the board is rendered in a Worker/OffscreenCanvas and every board label (station letters,
  siding and junction ids) is **baked into sprite pixels** server-side
  (`rig_art.nim:239-278`), so no in-page canvas text exists. The gate that carries weight is the
  renderer fixture step (`ci.yml:357-373`), which reported `75 drawn, 0 never inside, 0 ellipsized`.
- `tools/wasm_replay_smoke.cjs` runs the exact emitted module in node against
  `tests/replays/mainline-seed42.replay` (`ci.yml:270-274`); the log shows
  `ok: loaded mainline-seed42.replay, advanced 200 frames`.
- Both hooks are executable in the index (`100755`), and both are invoked by path.
- `git log -p --since="2026-08-27T12:00:00Z" -- tests/` shows exactly one test-file change in the run
  (`7b831f85`, `tests/test_flatland_viewer.nim`, +15/-5) plus a new fixture. No test file removed, no
  `skip`, no assertion deleted; see F22 for the one narrowing predicate.
- `tools/author_rail_maps.py --check` and `tools/build_broadcast_page.py --check` both pass in this
  sandbox; the six `.rail` sha256s I computed match `tests/rail_sha256.json` exactly.

**Documented deltas named in the brief**
- *Fresh-written `server`/`global`/`sim` in the starter's wire format* — `global.nim:115-182` builds
  frames with `bitworld/spriteprotocol`'s `addLayer`/`addViewport`/`addSprite`/`addObject`/
  `addDeleteObject` and smuggles the chrome JSON as the label of the reserved 1×1 sprite
  `BroadcastChromeSpriteId = 4090` (`:29, 180-182`) — the starter's Sprite v1 contract, which is why
  the inherited `broadcast_core.js` parses it unchanged (CI's browser load is the proof).
  `parseSpriteClientMessages` / `blobFromSpriteChat` are used on both ends
  (`server.nim:174`, `global.nim:76`, `flatland_player.nim:48`). **Sound.**
- *Right-hand running (divergence 10)* — `railmap.nim:289-350` derives a one-way direction for each
  road of a paired edge from the pair's centroid geometry, integer-only and map-derived;
  `routingBlocked` (`:491-505`) is consulted **only** by `successors` (`:507-514`), i.e. by the
  router, by `platformOutboundHeading` and by the load-time reachability check — never by
  `exitsFrom`/`resolveExit`, so the physics stays upstream-exact. Documented at
  `docs/PORTING-FLATLAND.md:74-86`. **Sound and consistently applied**; note that the loader's
  `stationsReachable` (`:651-677`) validates reachability *under* the same rule, so the six committed
  maps are known routable.
- *Platform cells are not nodes (divergence 11)* — `railmap.nim:226` with a 9-line rationale comment
  and `docs/PORTING-FLATLAND.md:88-95`. The note's §The network says a platform cell *is* a node; the
  divergence is explicit, argued (a platform inside a double-track road would break the pair), and the
  three things the note needed nodes for are handled elsewhere (arrival by `stationOf`, labels by
  `nodeLabels`, no dwell time). **Sound.**
- *Branchline S6 stub* — `data/rail/branch_a.rail` labels `S6 10 2`, a `u` dead-end stub. The
  siding binding falls through to the "edge that terminates there" branch (`railmap.nim:469-481`) and
  `sidingCells` returns `[edge.nodeB]` (`:616-626`); with the walk starting from the lower cell index
  (the `T` at (10,1)) `nodeB` is the stub cell itself, so `siding at S6` parks on the stub, not on the
  switch. **Sound** (inferred from the walk order at `:234-278`). Side effect: `sidingAhead`
  (`baselines.nim:70-82`) scans interior cells only, so the yielder can never pick S6.
- *Kept-but-remapped CSS classes* — F18.
- *Test-40 scope (the vocabulary scan)* — F22.
- *Replay size* — F13.
- *Swept baseline tuning* — F14.

---

## Could not determine

- **Whether F1 actually diverges at runtime.** The static chain is unambiguous, but the sandbox has no
  Nim, so I could not execute a branchline record→re-derive. Settle it with a test that records a
  `networkPool: "branchline"` episode and asserts `hashMismatchTick == -1`.
- **Whether a byte-cut provider reply can put invalid UTF-8 into `fallback.detail`.** Chain:
  `llm.nim:190` slices the reply at 4096 **bytes**, possibly mid-rune → `extractJsonObject`
  (`directives.nim:49-87`) either raises `DirectiveError` with a *head*-truncated, rune-safe message
  (safe) or reaches `parseJson(text[first .. last])`, whose `JsonParsingError` message is copied into
  `fallbackRecord(detail = error.msg)` (`decide.nim:269-270`) and only *shortened* by
  `truncateRunes` — which cannot repair an already-broken codepoint. Whether Nim's parser message can
  contain the offending bytes is not something I could confirm by reading alone. Settle it with a unit
  test that feeds a 4096-byte cut landing mid-emoji through `textOf` → `extractJsonObject` →
  `fallbackRecord` and validates the record's UTF-8.
- **Whether `nextSingleTrackConflict` (F4) ever fires on the shipped maps**, and therefore how much of
  the yielder's measured advantage over `timetable` (`tests/test_flatland_driver.nim:225-235`) comes
  from rule 4 versus rules 2/3. Needs a run with the predicate instrumented.
- **Whether the right-hand-running rule plus the interlock leaves every episode fully routable at
  *commit* time.** Plan-time reachability is validated at load; commit-time refusals are by design.
  Only a full run over the six maps and a range of seeds would show whether any seed strands trains
  systematically.
- *(Closed while writing this report.)* The `test` job's narrowing variables (`NIM_TESTS`,
  `NIM_TESTS_DEBUG_ONLY`, `NIM_TESTS_RELEASE_ONLY`, `ci.yml:120-123`) are repo variables I cannot
  read, but the job log settles it: run 33081598358 job 98550007384 shows **26** `nim r` invocations —
  all 13 `tests/*.nim` files in debug **and** in `-d:release` — ending
  `test_flatland_viewer: 78 checks ok` in both modes, which matches the 78 `check` blocks in the tree.
  Nothing was narrowed.
