# r1 review — ecos

Range: `f1235f9..289937c` (whole tree; the repo is 4 commits old and 3 of them are the build)
Head sha: `289937c0c8ca0e0a44b977683f1837cdb0605718` (== `origin/main`, verified by `git pull`)
Files read: 47 (all of `src/`, `tests/`, `replay-viewer/`, `tools/`, `client/chrome_common.js`,
`client/broadcast_core.js`, the full `client/replay_broadcast.html` diff against the starter, the
manifest, `compose.yaml`, both Dockerfiles, all three workflows, `scripts/art/gen_ecos_art.py`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–13 + the simultaneous-decision
clause)
Design note: `runs/2026-08-23-ecos/design.md` (byte-identical copy committed at
`docs/plans/2026-08-23-ecos-design.md`)

External evidence used, cited where it appears:
- `gh run list -R Metta-AI/cogame-ecos --branch main -w ci.yml` → run **32636493709**, conclusion
  **success**, jobs `test` ✓ 1m16s, `docker-smoke` ✓ 1m29s, `wasm-viewer` ✓ 2m18s.
- The `smoke-replay` artifact from that run (`replay.json`, 1 394 329 B, 361 frames) downloaded and
  analysed numerically. Several findings below are proved from those bytes, not inferred.

---

## Blocking

**None.** I could not falsify any of the thirteen checklist items or the simultaneous-decision
clause from the code at this sha. Item-by-item evidence is in *Traced and consistent* below; the
28 findings that follow are all advisory. Two of them (F1, F4) are the ones I would look at first
if the judge reads checklist item 2 more strictly than I did — I say why under each.

---

## Non-blocking

### F1 — the viewer re-derives the score with a different generation window than the sim, and the two disagree by 0.012–0.017
- Where: `src/ecos/replays.nim:183-191` vs `src/ecos/sim.nim:123`, `sim.nim:523`, `sim.nim:529-534`,
  `sim.nim:545`
- Observed (proved arithmetically on the CI replay, not inferred):
  - `newSim` calls `recordFrame()` at `sim.nim:123`, i.e. **before any tick runs**, and
    `recordFrame` accumulates `sim.genAccum[species] += bio` at `sim.nim:523`. So generation 1's
    accumulator carries **61** samples, `B(0) … B(60)`; every later generation carries 60.
  - The viewer's `precompute` guards with `if tick > 0: accum[index] += bioRow[index + 1]`
    (`replays.nim:183-184`), so its generation 1 carries **60** samples, `B(1) … B(60)`.
  - Both then divide by `ticksPerGeneration * reference` and cap at 2.0.
  - Recomputing both windows over `series.bio` from the CI artifact and comparing with the shipped
    `results.json` of the same episode:

    | slot / role | `results.scores` | sim window (incl. tick 0) | viewer window (`precompute`) |
    |---|---|---|---|
    | 0 grazers | 6.607108 | 6.607108 | 6.590442 |
    | 1 predators | 3.220311 | 3.220311 | 3.208089 |
    | 2 grass | 4.289966 | 4.289966 | 4.277966 |

  - The scorebug sub-line (`B 14.9k · 8.71`), the end-card score and the end-card **winner**
    (`broadcast.nim:126-133`) all read `input.scores`, which for the static replay comes from
    `player.scoreAt[tick]` (`replays.nim:261`) — the viewer window. `results.win` comes from the sim
    window (`sim.nim:762-770`).
- What the note says: `design.md:193` — `G_i(g) = (Σ_{t in generation g} B_i(t)) / (60 * R_i)`. On
  the natural reading (generation 1 = ticks 1..60) the **viewer** matches the note and the **sim**
  over-counts the opening frame by one sample.
- Checklist bearing: item 2 says the viewer must derive its display "from that same re-derivation —
  not from a parallel recording". The board, clock, populations, biomass and strip all read the
  recorded frames/series directly, and the score is recomputed from the same recorded `series.bio`,
  so it is not a parallel recording — which is why I did **not** file this as blocking. It is
  nevertheless a display that disagrees with the artifact it was derived from. *Inference:* in a
  near-tie the end-card could crown a different winner than `results.win`; the margin needed is
  ≤ 0.017, which is small but not impossible.

### F2 — the system prompt tells the model the kill gain is `min(180, 60 + energy)`; the sim uses 90
- Where: `src/ecos/llm.nim:163` vs `src/ecos/sim_types.nim:79`
- Observed: `kernelText(spPredators)` reads `it gains\nmin(180, 60 + the grazer's energy), capped at
  480 total.` The sim computes `let gain = min(KillCap, KillBase + prey.energy)` (`sim.nim:349`)
  with `KillBase* = 90` (`sim_types.nim:79`). Every predator seat is therefore told a payoff a third
  smaller than the one it gets. The manifest's `rules.md` page **was** updated —
  `coworld_manifest_template.json:308` reads "`min(180, 90 + the grazer's energy)`" — so the doc and
  the prompt now disagree with each other as well.
- What the note says: `design.md:159-160` pins `killBase = 60`; the builder's documented deviation
  raised it to 90. The deviation was propagated to `sim_types.nim`, `test_sim.nim` and the manifest
  docs but not to the in-game prompt.

### F3 — the four constant deviations from the note, traced
- Where: `src/ecos/sim_types.nim:79`, `:128-132`
- Observed, against the note's table at `design.md:110-120` and `design.md:160`:

  | constant | note | shipped | in-tree consequence |
  |---|---|---|---|
  | `killBase` | 60 | **90** (`sim_types.nim:79`) | F2 |
  | grazer steward `herd` | 40 | **20** (`sim_types.nim:131`) | prompt default text follows the shipped value (`llm.nim:128-134`), so it is self-consistent |
  | predator steward `rest_energy` | 240 | **200** (`sim_types.nim:132`) | as above |
  | predator steward `birth_threshold` | 320 | **400** (`sim_types.nim:132`) | 400 is the top of the declared range 150..400, so "recruit when thin" (`scripted.nim:41`) can only move it down |

- Faithfulness: `design.md:523-524` says "Any change to a constant in `## The game` re-runs
  `tests/test_feasibility.nim` … that test is the enforcement, not this table." `test_feasibility.nim`
  exists, runs in CI and is green at this sha, so the note's own enforcement rule is satisfied. The
  note's §Tests item 1 (`design.md:742-743`) separately names the literal `min(180, 60 + e)`; the
  shipped test asserts `min(KillCap, KillBase + preyEnergy - GrazerMetabolism)`
  (`tests/test_sim.nim:95`), i.e. it pins the *formula* but is expressed in terms of the constant, so
  a future change to `KillBase` would not fail it. That is a weakening relative to the note's text
  (it is not a *loosening during this run* — see checklist item 1 below).
- Verified live: the CI replay's generation-1 predator doctrine is
  `{birth_threshold: 360, hunt_range: 80, rest_energy: 280, spread: 40}`, which is exactly
  `[400,140,200,40]` with both steward corrections applied (`-40`, `-60`, `+80`). With the note's
  `320` it would have been `280`.

### F4 — the `alarm` event records a tick one greater than the frame it describes, making `events[]` non-monotonic in `t`
- Where: `src/ecos/sim.nim:495-499` and `sim.nim:608-609`
- Observed: `step()` does `inc sim.tick` (`:608`) and *then* calls `sim.checkAlarms()` (`:609`).
  `checkAlarms` emits `EcosEvent(tick: sim.tick + 1, kind: ekAlarm, …)` (`:498`). Every other
  per-tick event (`birth` `:427`, `starve` `:408`, `predation` `:355`) is emitted **before** the
  increment with `tick: sim.tick + 1`, and `collapse` (`:615`), `generation` (`:561`) and `end`
  (`:576`) are emitted **after** the increment with `tick: sim.tick`. So a tick T that raises an
  alarm appends `[…birth@T, alarm@T+1, collapse@T, generation@T, end@T]`.
- Consequences traced, not speculated:
  - `replays.nim:197-202` builds `eventStart` with a forward cursor that assumes non-decreasing
    `t`. With an alarm out of order, the `collapse`/`generation` rows that follow it land in the
    **next** tick's slice, so the feed row and the banner appear one tick late.
  - `src/ecos/server.nim:85-89` (`recentEventsJson`) walks backwards and `break`s at the first
    `tick < fromTick`, which also assumes sortedness.
  - `tests/test_replay.nim:49` asserts `tick <= ticksPlayed`. An alarm on the final tick would
    record `ticksPlayed + 1` and fail that assertion. In the all-steward seed-3 episode the test
    uses, no alarm fires on the last tick, so the test passes today.
  - The silent-spring desaturation is **not** affected: `replays.nim:171-182` recomputes the alarm
    state from `series.pop`, not from the `alarm` event.
- What the note says: `design.md:458` — "`alarm` | `t, sp, pop, cap` | first tick a species drops
  below `0.15 × cap`". The recorded `t` is that tick plus one.
- Checklist bearing: not blocking under item 2 as I read it (the board state is unaffected; only two
  chrome rows shift by one frame), but it is the other finding a stricter reading of item 2 could
  reach. *Untested:* the CI replay contains **zero** alarm events (predators bottom out at 5, and
  `0.15 × 30 = 4.5`), so this path has never executed in CI.

### F5 — the certification fixture is 6 generations × 60 ticks, not the note's 3 × 30, and adds `minTurnSeconds: 0`
- Where: `coworld_manifest_template.json:465-470`
- Observed: `{"num_agents": 3, "seed": 7, "generations": 6, "ticksPerGeneration": 60,
  "minTurnSeconds": 0, "playerConnectTimeoutSeconds": 180}`.
- What the note says: `design.md:719-720` — `{num_agents: 3, seed: 7, generations: 3,
  ticksPerGeneration: 30, playerConnectTimeoutSeconds: 180, players: […]}`. Neither the
  generation/tick change nor `minTurnSeconds: 0` is authorised by any repair rule in the note (the
  only repair rule the note carries is for `harsh-spring`, `design.md:715-718`). `minTurnSeconds` is
  a declared schema property (`manifest:159-165`, min 0) so the fixture still validates, and the
  effect is a faster offline fixture (the docker-smoke episode ran in 1m29s including the image
  build). This is a real divergence from the note's text, with no in-tree harm I can find.
- Verified live: the smoke log line at 11:26:24 shows exactly this config, and `docker-smoke` is
  green.

### F6 — `harsh-spring` ships with **both** repair steps exhausted, leaving it near-identical to `standard`
- Where: `coworld_manifest_template.json:437-448`, `tests/helpers.nim:22-31`
- Observed: shipped `harsh-spring` is `{initGrass: 160, grassGain: 5, initGrazers: 32,
  initPredators: 8}` — i.e. `initGrass` walked 120 → 140 → 160 **and** `grassGain` walked 4 → 5. The
  variant now differs from `standard` only in `initGrazers` (32 vs 40) and `initPredators` (8 vs 10).
- What the note says: `design.md:713-718` — the variant is authored as
  `{initGrass: 120, grassGain: 4, initGrazers: 32, initPredators: 8}` with the repair rule
  "`initGrass 120 → 140 → 160`, then `grassGain 4 → 5`. No other knob moves, and the shipped values
  are whatever the gate accepted." The shipped values are the terminal state of that rule applied in
  the stated order, so this is **faithful to the note's own enforcement**, and
  `tests/test_feasibility.nim:70-86` runs gate (a) over `harshSpringConfig` as the note requires.
  The note's stated intent ("a leaner field where restraint matters sooner",
  `design.md:714`) is largely spent: the opening grass and its regrowth are now identical to
  `standard`.
- Sub-observation: `tests/helpers.nim:26-31` hand-copies the variant's numbers. Nothing asserts that
  `harshSpringConfig` matches the manifest's `harsh-spring` block, so editing one alone would not go
  red. (`test_manifest.nim:145-151` cross-checks only `standard` against `defaultGameConfig()`.)

### F7 — `variant` is not a config-schema property, so every hosted replay records `"variant":"standard"`
- Where: `coworld_manifest_template.json:37-198` (properties list), `:425-449` (harsh-spring block),
  `src/ecos/sim_config.nim:143`, `:166`
- Observed: `config.update` accepts a `variant` key (`sim_config.nim:143`) and `configJson` writes it
  into the replay (`sim_config.nim:166`), but `game.config_schema.properties` declares no `variant`
  (and `additionalProperties: false` at `manifest:33`), and neither variant's `game_config` sets it.
  So `config.variant` is always the default `"standard"` (`sim_config.nim:56`) in production.
- Confirmed on the CI artifact: `config.variant == "standard"` for an episode driven by the
  certification fixture.
- What the note says: `design.md:692-696` lists exactly the same property set — no `variant` — so the
  manifest is faithful to the note. The consequence is that a `harsh-spring` replay is
  indistinguishable from a `standard` one in the recorded bytes. (`fieldW`/`fieldH` are in the same
  position: accepted by `config.update:114-115`, absent from the schema.)

### F8 — `ending` is the literal `"ten_generations"` whatever `generations` is configured to
- Where: `src/ecos/sim.nim:632`
- Observed: `sim.finish("complete", "ten_generations")` fires whenever
  `generationsPlayed >= config.generations`. The CI certification episode ran 6 generations and its
  `results.json` reads `{"generations": 6, "ending": "ten_generations"}`; the viewer smoke's 100 %
  clock readout is `"GEN 6 / 6 TEN GENERATIONS"` and the end-card chip reads `TEN GENERATIONS`
  (`client/replay_broadcast.html:3665`).
- What the note says: `design.md:227` names `ten_generations` as the ending for "10 generations
  played", and `generations` is a 1..12 config knob (`design.md:693`). The string is what the note
  prescribes; the mismatch only shows on non-default fixtures. Legibility, not correctness.

### F9 — `test_feasibility` gate (b): the note's greedy-grazer clause is replaced, and a new all-`opportunist` clause is added that sits against the note's conclusion (a)
- Where: `tests/test_feasibility.nim:19-26` (the header comment), `:117-121`, `:138-147`
- Observed:
  - The note's gate (b) requires "greedy grazer `(bite 14, birth 80, flee 0)` [reaches generation 10
    in] ≤3 of 6" (`design.md:757-758`). The test does not assert that. The header comment states the
    measured reason (dropping `flee_range` fattens the predators past `rest_energy`, so they idle and
    the field survives) and substitutes two measured properties instead: the greedy grazer strips
    grass below `0.4 ×` cap (`:141`) and scores below the steward grazer (`:144`). Both are asserted.
  - A clause the note does **not** contain was added: `:117-121` asserts an all-`opportunist` field
    reaches the last generation in **≤ 1 of 6** seeds.
- What the note says: `design.md:520-522`, conclusion (a) the builder "must preserve": "the scripted
  baselines sustain ten generations, so certification, `docker-smoke` and every all-filler league
  episode terminate with `reason: "complete"`, `ending: "ten_generations"`." The new clause asserts
  the opposite for one of the two shipped baselines when it holds all three seats. This is not a
  contradiction for certification (which seats one opportunist alongside two stewards — the CI
  episode ended `ten_generations`) and `reason` stays `"complete"` on a collapse by design
  (`sim.nim:630`), but "every all-filler league episode" is now false if the league ever seats three
  opportunists. Faithful to the note's substitution licence (`design.md:523-524`) as to the greedy
  grazer; the added clause is new material, documented in the test's own header.
- Sub-observation: gate (a) is written against `row.pop` — the population **at each generation
  close** (`test_feasibility.nim:50-55`, `sim.nim:547`) — where the note says "per-generation **mean**
  populations" (`design.md:755`).

### F10 — `frames.len == ticksPlayed + 1`
- Where: `tests/test_replay.nim:37-41`, `src/ecos/sim.nim:123`
- Observed: `newSim` records frame 0 before any tick, so a T-tick episode writes T+1 frames; the test
  asserts `ticksPlayed + 1` for `frames`, `series.pop` and `series.bio`, with the reason in a
  comment. Confirmed on the CI artifact: 361 frames / 361 pop rows / 361 bio rows for 360 ticks, and
  `frames[i].t == i` for every `i`.
- What the note says: two places, and they disagree with each other. The replay schema at
  `design.md:481` shows `"frames":[{"t":0, …}]` — frame 0 is the opening state — while §Tests item 4
  at `design.md:765` says `frames.len == ticksPlayed`. The code follows the schema; the test follows
  the code. Called out because the note's literal test text is not what the test asserts.

### F11 — a seat that never connects is still given an LLM call, not the steward baseline
- Where: `src/ecos/server.nim:287` (`var seats = @[0, 1, 2]`), `:306`, `src/ecos/llm.nim:387-392`
- Observed: `runGame` always asks for all three seats. `openSeatsOf` opens a seat when
  `scriptedKinds[slot] == skNone and not client.disabled`; a socket that never connected leaves
  `state.scripted[slot] == skNone` and `state.prompts[slot] == ""`, so with credentials present the
  game issues a real model request for the empty seat, with no operator block
  (`llm.nim:228-232` returns `""` for an empty prompt). Only if that fails twice does it fall back.
- What the note says: `design.md:554` — "waits up to `playerConnectTimeoutSeconds = 180` for three
  sockets, starts anyway with whoever is there (**missing seats play `steward`**)".
- Bound: the extra request is inside the same one-batch-of-3 per generation, so it costs no extra
  wall clock and does not change the request-rate arithmetic.

### F12 — an empty `notes` in a model reply leaves the previous generation's notes in place
- Where: `src/ecos/sim.nim:141`
- Observed: `if notes.len > 0: sim.notes[slot] = notes`. `say` is overwritten unconditionally
  (`:140`); `notes` is only overwritten when non-empty, so a seat that answers with `"notes": ""`
  is shown its older notes again next generation (`sim.nim:732`, `llm.nim:264-265`).
- What the note says: `design.md:290` / `:313-314` describe `notes` as "your own notes from last
  generation" and give no rule for an empty value. Undefined by the note; recorded as observed.

### F13 — the `rules` block in every seat's observation carries the GRAZER constants regardless of role
- Where: `src/ecos/sim.nim:733-743`
- Observed: `metabolism: GrazerMetabolism`, `fleeMetabolism: GrazerFleeMetabolism`,
  `speed: GrazerSpeed`, `fleeSpeed: GrazerFleeSpeed`, `biteRadius: BiteRadius`,
  `conversionPercent: 80`, `splitOverhead`, `crowdRadius` — all fixed; only
  `energyMax: SpeciesEMax[species]` varies by role. A grass or predator seat is told
  `speed: 6, fleeSpeed: 9, biteRadius: 16`.
- What the note says: `design.md:296-297` — the seat sees "its own doctrine, mean body energy, mean
  crowding, and **its own constants**". The note's JSON example (`design.md:291-292`) is a grazer's
  frame, so the example itself is ambiguous; the bullet is not. Mitigation observed: the role's real
  constants **are** in the system prompt (`llm.nim:136-165`), which is what the model actually reads.

### F14 — the history table's last column is labelled "your score" but carries all three species' scores
- Where: `src/ecos/llm.nim:200-213`
- Observed: the header is `… | eaten | your score` (`:200-201`) and each row ends
  `formatFloat(row.score[0]) & "," & formatFloat(row.score[1]) & "," & formatFloat(row.score[2])`
  (`:211-213`). Lines `:202-203` compute `let mine = ord(sim.roleOf[0])` and immediately
  `discard mine` — dead code, and `roleOf[0]` would have been the wrong slot anyway (the function
  takes no slot argument).
- What the note says: `design.md:346-347` — "columns `gen | grass n/B | grazers n/B | predators n/B |
  births | starved | eaten | your score`". No confidentiality consequence: all three species'
  per-generation scores are explicitly on the note's *visible* list (`design.md:294-296`).

### F15 — `test_baseline`'s "a scripted decision should never need clamping" cannot fail, and the thing it claims is false
- Where: `tests/test_baseline.nim:68`, `src/ecos/scripted.nim:56`, `src/ecos/llm.nim:422-427`
- Observed: `correct()` ends with `result = clampDoctrine(species, result).fields` and **discards**
  the `clamped` flag; `scriptedDecision` constructs a `Decision` without setting `clamped`, so
  `event.clamped` on a scripted/fallback doctrine is always `false` and the assertion is vacuous.
  It is also counterfactual: with the shipped steward, generation 1 on the standard opening drives
  grazer `birth_threshold` to `90 - 20 = 70`, which is clamped up to the range minimum 80. Proved on
  the CI artifact — the generation-1 grazer doctrine event reads
  `{"birth_threshold": 80, "bite": 10, "flee_range": 40, "herd": 20}` with `"clamped": false`.
- What the note says: `design.md:395` — "Every result is clamped to the declared range, so the
  baseline is legal by construction (asserted in `tests/test_baseline.nim`)". Legality **is**
  asserted, and holds (`test_baseline.nim:33-39`, `:65-67`). Only the extra `not event.clamped`
  assertion is empty.

### F16 — nothing asserts the recorded frame *contents* survive the writer→reader round trip
- Where: `tests/test_replay.nim:74-80`
- Observed: after `parseReplayBytes(bytes)` the test asserts `frames.len == ticksPlayed + 1`,
  `config.fieldW`, `player.lastTick`, and that frame 0's grass body **count** matches. No assertion
  compares any `x/y/energy` value in `reparsed.frames` with `sim.frames`.
- What the note says: §Tests item 4 (`design.md:761-768`) lists counts and event properties, not a
  value-level round trip, so the test matches the note. Recorded because checklist item 2 asks for a
  frame-by-frame reproduction assertion and this is the nearest thing in the tree.
- *I verified it externally instead*: over all 361 frames of the CI replay, `len(g)/3, len(h)/3,
  len(p)/3` equal `series.pop[t][1..3]` and the per-frame energy sums equal `series.bio[t][1..3]`
  exactly; and for every tick, `pop[t] == pop[t-1] + births(t) - (starves(t) + predations(t))` holds
  for all three species with **zero** mismatches. No body is ever outside `[0,1000] × [0,562]`, and
  no living body's energy is ≤ 0 or above its ceiling. The recording is internally consistent; it is
  just not the repo that says so.

### F17 — `results.biomass[i]` sums T+1 samples and divides by T
- Where: `src/ecos/sim.nim:746-748`, `sim.nim:524`
- Observed: `biomassSum` accumulates in `recordFrame`, which runs once at tick 0 and once per tick;
  `meanBiomass` returns `biomassSum div max(1, sim.tick)`.
- What the note says: `design.md:585` — "`biomass[i]` = the mean of `B_i(t)` over the ticks actually
  played, rounded to an integer". Same off-by-one family as F1, one part in ~360 here.

### F18 — a collapse mid-generation closes and counts that partial generation
- Where: `src/ecos/sim.nim:622-630`, `sim.nim:559`
- Observed: on a collapse away from a generation boundary, `closeGeneration()` is called anyway; it
  scores the partial accumulator against the full `ticksPerGeneration * R` denominator (so the
  partial generation earns partial credit — consistent with "generations played are scored") and
  increments `generationsPlayed`, which is what `results.generations` reports (`sim.nim:783`).
- What the note says: `design.md:586-587` — "`generations` = generations **completed**"; `:195`
  "Generations that were never played contribute **0**". The note does not say whether a partial
  generation is scored or counted. Recorded as observed, not as a defect.

### F19 — two viewer details the note describes are not implemented
- Where: `src/ecos/global.nim:386-391`, `client/replay_broadcast.html:3523-3526`
- Observed:
  - Birth sparkle: `collectFx` captures the parent position into `FxItem.px/py`
    (`global.nim:462-464`) but `buildBoardPacket` draws only the sparkle sprite at the child
    (`global.nim:388-391`); nothing draws the hairline. Note: `design.md:622` — "a 6-tick
    `sparkle.png` burst at the child's position **with a hairline to the parent's**".
  - `collapse` raises a banner only (`replay_broadcast.html:3525`) and `end` is handled as
    "state-driven" (`:3478`); neither pushes a feed row. Note: `design.md:635` — "plus rows for
    `alarm` …, `collapse` and `end`". `alarm` **does** push a row (`:3514-3520`) and `doctrine` does
    (`:3494-3512`).

### F20 — three pieces of dead state
- Where: `src/ecos/server.nim:42` (`trackers: Table[WebSocket, BroadcastTracker]` — declared, never
  written or read), `server.nim:50`/`:225` (`shuttingDown` — set to `true`, never read; `/healthz`
  answers unconditionally at `:342-343`), `src/ecos/sim.nim:140` (`sim.says[slot]` — written, never
  read; the `say` the viewer draws comes from the `doctrine` event at `sim.nim:151`).
- Note bearing: none. Recorded for completeness.

### F21 — `docker_smoke.sh` does not do two things the note's §Tests item 8 says it does
- Where: `tools/ci/docker_smoke.sh:237-242`, `:271-276`
- Observed: the script waits for the **game** container and checks its exit code; it checks for a
  `player_failure.json` file (`:256-258`) but never runs `docker inspect` on the player containers,
  so a player exiting non-zero is not asserted. It validates `results.json` as UTF-8 JSON and checks
  `len(names) == len(scores) == seats`; it does not validate it against
  `game.results_schema`.
- What the note says: `design.md:785-788` — "asserts the **player** containers exit 0 (raid item 3),
  validates `results.json` against the results schema".
- Faithfulness: the file is **byte-identical** to
  `coworld-builder/templates/tools/ci/docker_smoke.sh` after the three documented substitutions
  (verified by `sed | diff`, exit 0), which is what `design.md:730-731` asks for. The note
  over-describes the template. The *player-side* half of raid item 3 is handled in the game instead —
  `src/ecos_player.nim:53-89` wraps the receive loop in `try/except CatchableError` and `quit(0)`s.

### F22 — `#lockerroom { pointer-events: none }` is an addition to otherwise-verbatim chrome
- Where: `client/replay_broadcast.html:1351-1356`
- Observed: an added declaration with a comment explaining it — the loading curtain covers the
  scrubber for ~1.5 s and would swallow `viewer_smoke.mjs`'s 50 % seek click. The starter's
  `#lockerroom.gone { … pointer-events: none }` (`:1362`) is untouched.
- What the note says: `design.md:602` — `index.html` chrome "kept verbatim". This is a deliberate,
  documented departure from verbatim, in service of checklist item 13's smoke. Recorded, not
  criticised.

### F23 — rule 4's food target is selected during rule 2, on pre-grazing tuft energies
- Where: `src/ecos/sim.nim:220` (`if tufts[][j].energy >= 4 * bite …` inside `senseGrazers`) used at
  `sim.nim:275-276`
- Observed: `senseGrazers` (rule 2) precomputes `foodTuft`; `grazeStep` (rule 3) then reduces tuft
  energies; `moveGrazers` (rule 4) uses the rule-2 index.
- What the note says: `design.md:130-131` — "All reads inside a step use the state as it stood at the
  start of **that step**", and the `>= 4 * doctrine.bite` test is stated under rule 4
  (`design.md:147-148`), so on the strict reading rule 4 should see post-grazing energies. *This is
  an inference about which snapshot the note intends*, not a demonstrated defect; determinism is
  unaffected either way.

### F24 — the live `/global` population strip ships once at connect and is never refreshed
- Where: `src/ecos/server.nim:406` (`sendBoard(websocket, @[], true)`) vs `:150`
  (`sendBoard(socket, stepped, false)`)
- Observed: `withLead` is `true` only on the upgrade handler's first frame, so a spectator who
  connects at tick 0 receives a one-row `lead` series and never gets another. `chrome_common.js`'s
  `ingestLeadSeries` latches the first series it sees (`chrome_common.js:641`) and
  `recordMomentum` then declines to accumulate (`:662`), so the live strip stays a single point.
- What the note says: `design.md:637-642` describes the strip as fed "exactly like paintbot's lives
  series"; `design.md:491` scopes the ship-once trick to the recorded replay ("so the population
  strip draws its full width on frame 1"). The **static replay** path is correct
  (`replays.nim:278-288` ships the whole series on the first chrome frame), and that is the path
  checklist items 3/11/13 are about.

### F25 — a 429 is retried inside the same generation's batch, not the next generation's
- Where: `src/ecos/llm.nim:336-338` and the `for attempt in 0 .. 1` loop at `:451`
- Observed: `textOf` raises on 429 with a log line; the seat goes into `stillOpen` and is retried in
  the immediately following retry batch; if that also fails it falls back to steward.
- What the note says: `design.md:416` — "429 is logged and retried in the **next generation's**
  batch." The shipped behaviour retries sooner (still within the 25 s + 25 s worst case, so the
  wall-clock arithmetic at `design.md:257-262` is unaffected) and can therefore hit a throttled
  sidecar twice in ~50 s rather than once per 6 s minimum spacing.

### F26 — the play deadline is a start-of-generation check, so the settle can overrun 720 s by one batch plus one generation
- Where: `src/ecos/server.nim:291-297`
- Observed: `playDeadline = gameStart + timeoutSeconds * PlayBudgetFraction` (`:278`, fraction 0.6 at
  `sim_types.nim:103`) is tested at the **top** of the loop. A check that passes at 719.9 s is
  followed by up to 25 s + 25 s of batches (`llm.nim:451-456`, `curly.makeRequests(batch, 25)`), one
  generation of simulation and up to `minTurnSeconds = 6` of floor sleep (`server.nim:326-329`),
  then `finishEpisode` (0.5 s + artifact writes + 20 s grace). Worst case ≈ **800 s**, well inside
  the 1200 s the platform allows, but outside the 720 s "settles and scores inside 60 %" phrasing.
- Also observed: the deadline is measured from **process start**, not from the start of play, so the
  ≤180 s connect wait (`server.nim:238-247`) is charged against the play budget. Worst realistic
  case 180 + 500 = 680 s < 720 s, so the deadline can fire only in a pathological run — which the
  note pre-declares acceptable (`design.md:236-237`).
- What the note says: `design.md:230` — "wall clock passes the play deadline … checked **between
  generations only**". The code does exactly that; the overrun is the arithmetic consequence, and it
  is bounded.

### F27 — the CI viewer-smoke's `feed_lines: 0` is a harness selector mismatch, not an empty feed
- Where: `tools/ci/viewer_smoke.mjs:286` vs `client/replay_broadcast.html:1618`, `:3588`
- Observed: the harness reads `document.querySelector("#feed, .feed, #log")`; the page's feed element
  is `#killfeed`. It is a reported field, not an asserted one (`viewer_smoke.mjs:293`, `:464`,
  `:511`), and `viewer_smoke.mjs` is byte-identical to the builder template (verified by `diff -q`).
  Separately, `pushFeed` self-removes each row after a dwell (`replay_broadcast.html:3597-3600`), so
  0 is a legitimate reading at an arbitrary instant. Recorded so the judge does not read
  `"feed_lines":0` in the CI log as evidence that the doctrine feed never renders.

### F28 — every shipped fixture names the players with the in-game aliases, so `policyNames == names`
- Where: `coworld_manifest_template.json:396-406`, `:432-442`, `:454-464`; `src/ecos/sim.nim:111-117`
- Observed: `standard`, `harsh-spring` and the certification fixture all set
  `players: [{Sedge},{Bramble},{Quill}]`. `newSim` copies `config.players[slot].name` into
  `policyNames`, so both name spaces carry the same three strings offline. Confirmed on the CI
  artifact: `names == policyNames == ["Sedge","Bramble","Quill"]`, and the viewer smoke's scorebug
  read `BRAMBLE 7 PREDATORS … SEDGE 108 GRAZERS … QUILL 205 GRASS`.
- What the note says: `design.md:710-721` specifies exactly those `players` blocks, so the manifest
  is faithful. The *mechanism* for two name spaces is present and correct (checklist item 4 — see
  below); it just cannot be observed offline. *Inference:* the platform supplies real policy names in
  `game_config.players` for a hosted episode, which is the only way `results.names` carries policy
  names as `design.md:582` requires.

---

## Traced and consistent

Checklist items, with what I read:

1. **CI green, no test loosened.** `gh run list -R Metta-AI/cogame-ecos --branch main -w ci.yml` →
   run **32636493709** at sha `289937c`, conclusion **success**; `gh run view` shows `test`,
   `docker-smoke` and `wasm-viewer` all ✓ with no skipped or `continue-on-error` step.
   `git -C /workspace/cogame-ecos log --oneline -- tests/` returns exactly one commit (`a6cc753`,
   the initial build) — the two later commits (`3f15424` `tools/build_replay_viewer.sh`, `289937c`
   the cert fixture) touch no test file, so nothing was deleted, widened or skipped this run. The
   `test` job runs every `tests/*.nim` twice, debug and `-d:release` (`ci.yml:115-150`), and there
   are no repo-variable overrides visible in the log.
2. **Replay re-derivation.** Ecos records state, not inputs, by design (`design.md:466-469`), so
   there is no re-simulation to diverge. `replay-viewer/ecos_replay.nim:37-40` is three calls —
   `parseReplayBytes` → `initReplayPlayer` → `advanceReplayFrame` + `buildBoardPacket` — and
   `tests/test_replay.nim:86-109` runs that exact loop natively for 120 frames including two seeks,
   asserting a non-empty packet, `chrome.t == player.tick` on every frame and `teams.len == 3`,
   plus >1000 drawn objects. The board, populations, biomass, clock and strip all read the recorded
   `frames`/`series`. The one display quantity that is recomputed rather than read is the score —
   F1.
3. **Static viewer.** `coworld_manifest_template.json:16-18` declares
   `"replay_viewer": {"bundle": "static-replay-viewer"}`; `test_manifest.nim:94-96` asserts it and
   asserts no `replay_runnable`. `tools/build_replay_viewer.sh` exists, is `0755`, and is invoked by
   `ci.yml:249` after an explicit `test -x` gate (`ci.yml:225-236`) — the same gate `coworld build`
   applies. `src/ecos.nim:30-36` exits 0 if the platform ever schedules replay mode. No `/client/replay`
   route exists in `server.nim:469-479`. *One grep hit to pre-empt:* `client/broadcast_core.js:196`
   contains the string `'/client/replay'` inside `websocketPathForClientPage`, a URL-mapping helper
   in the **verbatim** starter file (`diff` against `coworld-ctf` is empty); ecos never serves that
   path, and the static bundle uses the `EcosStaticReplay` adapter, not a websocket. The bundle
   fetches only the replay URL (`static_replay_worker.js:118-120`).
4. **Both name spaces.** Agents: `observationJson` sends `"name": sim.names[slot]` and
   `species[].alias` — aliases only (`sim.nim:712`, `:688`); no policy name, account or seed appears
   in the frame or in either prompt (`llm.nim:167-274` reads `sim.names[…]` only). Viewer: the chrome
   frame carries `alias` **and** `policies: [policyNames[slot]]` per team (`broadcast.nim:56-62`) and
   `chrome_common.js:145-158`'s `teamName` headlines the policy name; the replay carries both
   `names[]` and `policyNames[]` (`replays.nim:61-69`). `results.names` carries policy names
   (`sim.nim:768`). See F28 for why they coincide offline.
5. **Degrade-never-hang.** Every wait I could find, with its bound:
   - seat connect: `while epochTime() < connectDeadline … sleep(200)`, `server.nim:241-247`, bounded
     by `playerConnectTimeoutSeconds = 180`.
   - LLM batch: `client.curl.makeRequests(batch, client.timeoutSeconds)`, `llm.nim:456`; curly's
     signature is `makeRequests(batch, timeout = 60)` with the timeout applied **per request**
     (`curly.nim:711-745`), and `timeoutSeconds = config.llmTimeoutSeconds = 25`.
   - retry: `for attempt in 0 .. 1` — exactly two batches, `llm.nim:451`.
   - per-generation floor: `sleep(≤ minTurnSeconds)` only when the client is enabled,
     `server.nim:326-329`.
   - generation loop: `runGeneration` is `while … generationsPlayed < target: step()`
     (`sim.nim:634-638`); `step` increments `tick` unconditionally and `ticksPerGeneration` is
     validated to 10..90 (`sim_config.nim:76-77`), so it terminates in ≤ 90 iterations.
   - artifact writes: `curl.post(uri, headers, data, 60)` (`server.nim:164`) and bitworld's
     `writeCogameUri`/`readCogameUri`, which use `curly`'s `CurlPool.get/put` with the default
     `timeout: float32 = 60` (`curly.nim:1184-1211`). `ANTHROPIC_API_KEY_URI` resolution
     (`llm.nim:58-65`) is on that same bounded path and is wrapped in `try/except`.
   - shutdown: `sleep(500)` + `sleep(grace * 1000)` + `quit(0)`, `server.nim:209-230`.
   - player process: `socket.receiveMessage()` (`ecos_player.nim:55`) has whisky's default
     `timeout = -1`, i.e. an unbounded read — but it is wrapped in `try/except CatchableError` and
     `quit(0)` (`:53-89`), and the game always reaches `quit(0)`, closing the socket. This is what
     `design.md:561-563` explicitly prescribes.
   - `decideAll` never raises: every per-seat failure is caught at `llm.nim:468-471` and every
     still-open seat is given the steward doctrine at `:473-477`.
   - No blocking read, no unbounded loop, and no `while true` without a bounded exit that I found.
6. **`num_agents`.** Present in `standard` (`manifest:407`), `harsh-spring` (`:437`) and
   `certification.game_config` (`:465`). `test_manifest.nim:50-66` asserts it in **every** variant
   and in the fixture, plus `len(players) == 3` in all three places. `tools/ci/docker_smoke.sh:110-151`
   carries all four invariants (present / positive integer / `len(certification.players)` /
   `len(certification.game_config.players)`) plus the `SMOKE_SEATS` second declaration, each exiting
   with a `SEAT-COUNT FAIL:` prefix. **`grep -c "SEAT-COUNT FAIL" <docker-smoke log>` = 0** for run
   32636493709; the log's own line reads `game=ecos seats=3 config={… "num_agents": 3 …}`.
7. **Scripted baseline plays a full episode legally.** `tests/test_replay.nim:18` runs
   `stewardEpisode(standardConfig(3))` to the natural end and asserts
   `results.ending == "ten_generations"` (`:68`) and `results.reason in {complete, deadline,
   forfeit}` (`:67`). `ending == "ten_generations"` is written **only** by
   `finish("complete", "ten_generations")` (`sim.nim:632`), and `finish` is the sole writer of both
   fields (`sim.nim:569-577`), so the assertion is equivalent to `reason == "complete"`.
   `tests/test_baseline.nim` then runs 12 seeds × 2 baselines × a full episode, checking on **every
   tick** that populations are under cap, positions inside the field and energies in `(0, ceiling]`
   (`:15-31`, `:57-60`), and that every emitted doctrine field is inside its declared range both at
   decision time (`:53`) and as recorded in the replay events (`:65-67`).
   `tests/test_feasibility.nim:70-86` is the standing oracle: all 12 seeds, both variants, must reach
   the last generation with all species alive.
8. **LLM reply handling.** `extractJsonObject` (`llm.nim:278-289`) takes the first `{` to the last
   `}`, tolerating fences and prose — asserted for a bare object, a ```json fence and a prose prefix
   (`test_llm.nim:30-40`). `numberOf` (`llm.nim:352-368`) accepts int, float (rounded) and numeric
   string; a missing or non-numeric field raises (invalid), an out-of-range one is clamped and
   flagged (`llm.nim:383-385`) — all four cases asserted (`test_llm.nim:43-79`). Retry is **exactly
   once**: `for attempt in 0 .. 1` with the hint appended on attempt 1 (`llm.nim:408-411`, asserted
   at `test_llm.nim:122-125`). The fallback is recorded: `source: dsFallback` on the `doctrine`
   event (`llm.nim:473-477`, `events.nim:82`), asserted at `test_llm.nim:127-152`, and **observed in
   the CI replay** — seat 0 (`ecos-player`, no credentials) recorded
   `"source": "fallback"` while seats 1–2 recorded `"source": "scripted"`, exactly the distinction
   phase 60 needs to count. 401/403 disables the client for the episode (`llm.nim:331-335`, asserted
   at `test_llm.nim:99-102`).
   **Simultaneous-decision clause:** one batch per generation, `requestBatchFor` posts every open
   seat into a single `RequestBatch` (`llm.nim:394-413`) handed to `curly.makeRequests`, and
   `newCurly()` defaults to `maxInFlight = 16` (`curly.nim:442-458`) ≥ 3, so the three requests are
   genuinely concurrent, not serialised by pool starvation. `test_llm.nim:104-126` asserts
   `batch.len == openSeats`.
9. **Rune-safe truncation.** `cleanText` = `strip` → `if runeLen <= limit: return` →
   `runeSubStr(0, limit - 1) & "…"` (`llm.nim:111-118`); `cleanSay` also maps `\n`/`\r` to spaces
   (`:120-121`). Caps `MaxSayLen = 64`, `MaxNotesLen = 400` (`sim_types.nim:98-99`) as the note says.
   The player prompt is rune-truncated too (`server.nim:439-440`, `MaxPromptLen = 4000`), and the
   captured LLM error strings are byte-sliced only on ASCII-safe paths that go to the log, never to
   the replay (`llm.nim:284-286`, `:332`, `:340`). `tests/test_replay.nim:114-160` builds a 64-rune
   × 2-byte `say` and a 400-rune × 4-byte `notes` **exactly at the cap**, asserts they pass through
   unchanged and valid, then one rune over and asserts the cut is `runeLen == cap`, ends in `…`, is
   valid UTF-8, and survives into the replay bytes with `validateUtf8(fixtureBytes) == -1`.
10. **Manifest validates.** `game.docs` is
    `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`
    (`manifest:297-320`) with two pages; `game.protocols` carries **both** `player` (`:288-291`) and
    `global` (`:292-295`), each `{"type":"text","value":…}` with real protocol text.
    `test_manifest.nim:129-141` asserts all of it plus minimum lengths. Also present per the note:
    top-level `$schema`, six `tags`, `episode_timeout_minutes: 20` at top level (and asserted absent
    under `game`), top-level `player[]`, a `description` on every variant, and a real JSON-Schema
    `config_schema` with `required: ["tokens"]` and `additionalProperties: false`.
11. **360 px legibility.** `client/replay_broadcast.html:890-901` —
    `.plate .plate-name { … flex: 1 1 auto; min-width: 3.2em; … }` with
    `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`;
    `:922-927` — `@media (max-width: 640px) { .plate .lives-label, .plate .plate-sub { display:
    none; } .momentum-label { display: none; } }`; `:928-929` shrinks the name and sub-line under
    `#stage.tiny`, which the starter switches on at `boardW <= 620` (`:4275`, verbatim). The
    scorebug the CI smoke actually rendered was legible in one line:
    `BRAMBLE 7 PREDATORS B 1.47k · 2.53 …`.
12. **Release order and scaffold.** `coworld-release.yml` job steps in order: *Build the Coworld
    manifest* (`:153`) → *Certify locally* (`:167`) → *Upload the policies* (`:206`) → *Upload the
    Coworld* (`:304`) → *Put the Coworld secret* (`:342`). All three workflows present;
    `coworld-release.yml` and `coworld-submit.yml` are byte-identical to the builder templates after
    substitution, and `ci.yml` differs from the template only by **adding** `--soak 10` to the viewer
    smoke (`ci.yml:306-314`) — a strengthening, not a weakening. `tools/ci/docker_smoke.sh` and
    `tools/build_replay_viewer.sh` are both `-rwxr-xr-x`. `tools/ci/policies.json` has 4 policies: two
    `PLAYER_PROMPT` champions (`ecos-keeper`, `ecos-bloom`) whose text matches the note's champion
    prompts, and two `PLAYER_SCRIPTED` fillers (`steward`, `opportunist`); champion #2 carries
    `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. `test_manifest.nim:154-171` asserts all
    of that. The placeholder gate — `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files —
    **exits 0**; the only surviving angle-bracket names are the four the checklist declares expected
    residue (`<cow_id>`/`<sha>` in `ci.yml:202`, `<run_id>` in `coworld-release.yml:21` and
    `coworld-submit.yml:17`, `<name>:vN` in `coworld-submit.yml:31`).
13. **Viewer executes.**
    - `wasm-viewer` `needs: docker-smoke` (`ci.yml:212`); the *Load the bundle in a real browser*
      step ran and printed
      `{"loaded":true,"ms":558,"clock":"GEN 5 / 6 TICK 243 OF 360", …}`, then
      `soak: 10s of playback kept advancing ("3 / 360" -> "195 / 360" -> "243 / 360")` and
      `scrub readouts: 0%="GEN 5 / 6 TICK 243 OF 360"  50%="GEN 4 / 6 TICK 196 OF 360"
      100%="GEN 6 / 6 TEN GENERATIONS"` — three distinct readouts. No `continue-on-error` anywhere in
      the job; `viewer-smoke.png`/`.json` uploaded.
    - Markers, both from the shell's own code: `data-replay-loaded="true"` at
      `replay-viewer/static_replay.js:141` on the worker's `loaded` message, and
      `data-replay-error` at `:16-19` inside `showFailure` — the one added line the note authorises
      (`design.md:601`). `ecos_load_replay` renders the first frame *before* returning success
      (`ecos_replay.nim:54-56`), and the worker posts `loaded` only after `ingestPacket()`
      (`static_replay_worker.js:123-128`), so the marker really does follow a drawn frame.
    - **Link flags and bootstrap are a matched pair, both from coworld-ctf.**
      `replay-viewer/config.nims:42-54` has **no** `-s MODULARIZE=1` and **no** `EXPORT_NAME`, and is
      otherwise a line-for-line copy of the starter's (diffed) with `ctf_replay.js` → `ecos_replay.js`,
      the exports renamed `_ecos_*`, and `_ctf_mismatch_tick` dropped as the note directs
      (`design.md:600`). The worker declares `var Module = {}` (`static_replay_worker.js:8`), assigns
      `Module.onRuntimeInitialized` (`:162`) and `importScripts('./wire_constants.js',
      './broadcast_core.js','./ecos_replay.js')` (`:210`) — the non-MODULARIZE bootstrap. `diff -u`
      of both JS files against `coworld-ctf` shows **only** the `ctf_*`→`ecos_*` renames, the worker
      name string, the mismatch removal and the one added failure line. `Dockerfile.replay-viewer:65-66`
      hard-asserts the pair at build time (`grep -q onRuntimeInitialized` and
      `! grep -q MODULARIZE`). And the smoke's `loaded: true` is the executed proof.

Other things I traced and found consistent with the note:

- **Tick order.** All ten numbered rules are present in order in `sim.nim:594-610`, one proc each:
  photosynthesis `:165-181` (`clamp(grassGain - n, 0, grassGain)` then `- 1`, capped at 200);
  grazer sense `:183-226` (`crowd` within 60 excluding self, `stress = min(2, crowd div 6)`,
  `fleeing = nearestPredator < flee_range`, `grazing` = not fleeing and a tuft within 16);
  grazing `:228-241` (`min(bite, energy)` from the nearest tuft, ties → lowest index by the strict
  `<` at `:217`, `(taken * 4) div 5` to the grazer); movement `:243-298` (grazing holds still;
  fleeing at 9, or **11** when `crowd >= 4`; otherwise the `(100 - herd)·toFood + herd·toHerd` blend
  at speed 6, herd centroid over 200 units, random heading when there is no tuft at all; the right
  metabolism + stress on each branch); predator sense `:312-322` (`min(2, pcrowd div 2)`, cooldown
  decrement at `:326`); predator act `:323-383` (idle above `rest_energy`; nearest un-eaten grazer
  within `hunt_range`; kill within 16 with `cooldown == 0` for `min(180, KillBase + e)` capped at
  480, cooldown 12, no move; else chase at 12 with the `spread` blend against the **start-of-step**
  snapshot `:322`; else roam at 7 on a heading redrawn every 12 ticks); clamp `:385-390`; deaths
  `:392-414` (eaten first, then `energy <= 0`, all removed before any birth); births `:435-487`
  (grass, then grazers, then predators, each `break`ing at its cap so the parent pays nothing —
  `design.md:92-93`; grass pays `seedLoss = 10` on a refused seed and `seed_cost + 10` on a
  successful one, the child gets `seed_cost`; splits are `(energy - 20) div 2` with the child 8 units
  away); record `:503-527`.
- **Determinism.** No float in the sim: `SinTable` and `AtanTable` are `const` blocks evaluated at
  compile time (`sim_state.nim:45-52`, `:85-93`), `isqrt` is integer Newton (`:57-65`), the RNG is a
  seeded xorshift64\* (`:23-40`). `test_sim.nim:233-248` asserts the same seed reproduces the same
  `gameHash` twice in one process and across a fresh `SimServer`, and that a different seed diverges.
  `sim_types.nim:31` `Doctrine = array[4, int]` and the flat `x,y,energy` triples keep the recorded
  layout positional as the note requires.
- **Role rotation.** `assignRoles` is `Species((slot + roleOffset) mod 3)` with
  `roleOffset = ((seed mod 3) + 3) mod 3` when unpinned (`sim.nim:70-76`, `:105-107`); aliases stay
  with the slot (`:109-110`). `test_sim.nim:250-266` asserts each offset deals a distinct rotation and
  that aliases do not move. The chrome team key follows the **role** (`broadcast.nim:47-64`),
  asserted under all three rotations at `test_broadcast.nim:56-89`. Confirmed live: the CI episode
  (seed 7 → offset 1) recorded `roles: ["grazers","predators","grass"]`.
- **Scripted baselines.** `scripted.nim:31-56` implements the note's two corrections in the note's
  order and on the right field indices for each role (`design.md:386-394`), then clamps. The CI
  replay's generation-1 doctrines match a hand-trace of that code exactly for all three seats.
- **Replay writer.** `replayBytes` (`replays.nim:51-98`) emits every field the note's schema lists —
  `protocol`, `game`, `gameVersion`, `seed`, `roleOffset`, `names`, `policyNames`, `roles`, `config`,
  `frames`, `series.pop`/`bio`, `events`, `results` — with `escapeJson` on every string, so the
  document is self-sufficient and no server but S3 is contacted. Size on the CI artifact: 1.33 MiB
  for 360 ticks, against the note's ≤ 8 MiB budget and its ~2.8 MB estimate for 600.
  `parseReplayBytes` rejects a wrong protocol, an empty frame list and a non-3-seat replay
  (`:100-112`).
- **Prompts.** The system prompt carries the alias and role in capitals, the role's kernel, the four
  fields with ranges and defaults, the scoring rule including the `min(G, 2.0)` cap and the
  everyone-scores-zero clause, the "other two seats decide simultaneously and read nothing you
  write" statement, and the output contract ending with the exact `OUTPUT FORMAT:` sentence the note
  quotes (`llm.nim:167-196` vs `design.md:339-341`). The user prompt has the history table, the three
  10×6 density grids, `YOUR NOTES FROM LAST GENERATION`, the operator block with the note's exact
  heading, and a closing restatement of the reply shape with the seat's own field names and ranges
  (`llm.nim:234-274`). Transport: haiku-only `bedrockModelIds()` with `BEDROCK_MODEL` override
  (`llm.nim:67-73`, asserted at `test_llm.nim:155`), `maxOutputTokens` default 900
  (`sim_config.nim:51`), no `output_config.effort` anywhere, and the credential order
  Bedrock → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` → disable
  (`llm.nim:79-107`).
- **Routes and shutdown.** `/healthz`, `/client/global`, `/client/player`, `/client/*.js`,
  `/client/font.ttf`, `WS /global`, `WS /player` (`server.nim:469-479`), with `/client/*` pages
  registered before the asset routes as the note's lantern learning requires; a bad token gets a
  clean 401, never a hang (`server.nim:376-383`); mummy `Ping` frames are answered with a `Pong`
  (`server.nim:418-420`). Shutdown order matches `design.md:557-561` exactly: `final` to every player
  → last global frame → `sleep 500` → `results.json` → replay → log → 20 s grace → `quit(0)`
  (`server.nim:194-230`). (One nit: `broadcastLocked` at `:207` also re-sends a `state` frame to the
  player sockets *after* `final`; the player has already broken out of its loop, so it is never read.)
- **Art.** `scripts/art/gen_ecos_art.py` is committed, deterministic (single seeded `random.Random`,
  no time, no set iteration) and produces exactly the files the note lists; the committed outputs are
  real images of the right dimensions (`tuft_1..4` 24/32/40/48 px, grazer 28 px, predator 40 px,
  soil 96 px, sparkle 16 px, splash 20 px, `bg.jpg` 1280×720, three species `.webp` portraits of
  290–540 bytes). No placeholder or zero-byte binary.
- **`compose.yaml` derivation.** `services.ecos` → `{{ECOS_IMAGE}}`, asserted end-to-end by
  `test_manifest.nim:39-47` (it re-derives the placeholder from the compose file rather than
  hard-coding it).

---

## Could not determine

- **Whether the `harsh-spring` repair rule was actually walked step by step** (120 → 140 → 160, then
  4 → 5) rather than jumped to the terminal values. `tests/helpers.nim:23-25` asserts in a comment
  that it was. What would settle it: the phase-10 gate output for the intermediate configurations,
  or a run of `test_feasibility.nim` with `initGrass = 140, grassGain = 4` showing gate (a) failing.
  I have no Nim toolchain in this sandbox (`which nim` → nothing), so I could not run it.
- **Whether the baseline's parameters "were tuned with a grid harness, not guessed"** (checklist item
  7, last sentence). `design.md:501-502` claims a 240-configuration random search plus a 192-point
  doctrine grid on 8–12 seeds; there is no harness, no search script and no measurement log in the
  tree — `tools/` holds only `dump_replay.nim`, `gen_wire_constants.nim`, `build_replay_viewer.sh`
  and `ci/`. `tests/test_feasibility.nim` is the standing enforcement of the *result* and it is green.
  What would settle it: the phase-10 search artefact, or a committed harness.
- **The `alarm` path has never executed in CI** (F4). The only replay CI produces has zero `alarm`
  events. What would settle the consequences I traced: a fixture episode that alarms (e.g. the
  greedy-predator picker `test_broadcast.nim:148-156` already builds one) with an assertion that
  every recorded event tick equals the frame it belongs to.
- **Whether `results.names` ever carries real policy names in production** (F28). Every in-tree
  fixture names the players with the aliases. What would settle it: a hosted episode's `results.json`,
  or the platform's documented `game_config.players` substitution.
- **Whether the note's `docker_smoke` claims (player exit codes, results-schema validation) are meant
  to bind the builder** (F21), given the file is the builder's own template and the note also says to
  take it verbatim (`design.md:730-731`). Two note clauses point in different directions; a ruling,
  not a code change, would settle it.
