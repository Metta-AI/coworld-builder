# r1 review — 2026-09-08-battlecode-2022 (`Metta-AI/cogame-battlecode`, bc22 year module)

Range: `47f360011e0b46fe6ede8e8f71a702a63fe84c74..1fc96b4966661232a00146368b5ff906c0941903` (119 files, +20573/−117, PR #8)
Files read: 44 source/test/config files at the reviewed sha, plus 3 CI job logs from run `34288986734`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15)
Repo cloned read-only to `/tmp/review-bc22`; nothing was written to the coworld repo.

---

## Blocking

**None.** I could not falsify any of the fifteen acceptance-checklist items. Items verified as
holding are listed under "Traced and consistent"; two items where a strict-literal reading of the
checklist text differs from what the tree contains are reported under Non-blocking (N1, N2) with the
evidence that both are **pre-existing at `47f36001`, unchanged by this diff, and prescribed by the
design note** — so they are not findings against this run's work, and I state them so the judge can
see I did not skip them.

---

## Non-blocking

### N1 — `game.docs` uses `"type":"uri"`, not the checklist's literal `"type":"text"`
- Where: `coworld_manifest_template.json` — `game.docs.readme` and all nine `pages[].content`
  (`readme` value `https://github.com/Metta-AI/cogame-battlecode/blob/main/README.md`; every page's
  `content.type` is `"uri"`).
- Observed: `readme` is `{"type":"uri","value":…}` and each of the nine pages is
  `{"id","title","content":{"type":"uri","value":…}}` — the required *shape* (an object carrying
  `type` + `value`; `id`/`title`/`content` on each page) is present, only the discriminator string
  differs. `game.protocols` carries **both** `player` and `global`, each
  `{"type":"uri","value":".../docs/PROTOCOL.md"}`.
- Checklist item: 10 (`manifest`).
- Provenance: `git diff 47f36001..1fc96b4 -- coworld_manifest_template.json` contains **no** change to
  `readme` or `protocols`; this shape shipped in the six earlier year runs. `design.md:1898-1902`
  prescribes `readme = {"type":"uri", …}` explicitly. `tests/test_manifest.nim:299-318` asserts the
  object shape and the nine page ids, and a separate CI step ("The coworld CLI accepts the manifest
  template", `ci.yml`) runs the installed `coworld` CLI's own `validate_upload_manifest` against it —
  green in run `34288986734`. Inference (labelled as such): the platform accepts `uri` here; the
  checklist's `"text"` reads as an illustration of the shape rather than a required literal.
- Why not blocking on this diff: the diff neither introduced nor touched it.

### N2 — the string `/client/replay` exists in the tree, in inherited chrome and in a guard message
- Where: `client/broadcast_core.js:372` (`['/client/replay', '/replay']`) and `:385`
  (`['/client/replay_plus_pov', '/replay']`); `.github/workflows/coworld-release.yml:220`.
- Observed: `broadcast_core.js`'s `mappings` table maps *live-broadcast page paths* to websocket
  paths for the pod-served `/client/global` chrome; it is not a route the static replay bundle uses
  (the bundle's shell reads the replay URL from `location.hash`/`?replay=` and fetches it directly —
  `replay-viewer/static_replay.js:205-207`). The `coworld-release.yml` occurrence is inside the
  *failure message* of the step that **forbids** a pod viewer ("a pod-served /client/replay viewer is
  not acceptable").
- Checklist item: 3 (`static-viewer`), "No `/client/replay` pod path anywhere".
- Provenance: `client/broadcast_core.js` is byte-identical across the range
  (`sha256 226aea03cd240120…` at both ends) **and** byte-identical to
  `/workspace/starters/coworld-ctf/client/broadcast_core.js`. `coworld-release.yml` is not in the
  diff at all.

### N3 — `match.nim:480`'s `max(1, …)` clamp and `bc22/rules.nim:434`'s `> 0` guard still disagree
- Where: `src/battlecode/match.nim:480` —
  `let perGame = max(1, min(config.perGameBudgetSeconds, remaining))`;
  `src/battlecode/years/bc22/rules.nim:434` —
  `if budgetSeconds > 0 and (w.currentRound and 0x1F) == 0 and …`.
- Observed: `playMatch` clamps the per-game budget **up** to a floor of 1 s before handing it to
  `playGameFor`, so a config value of `0` becomes a one-second budget. One level down, `playGame`
  treats `budgetSeconds == 0` as "no budget" — a branch `playMatch` can never reach, because
  `max(1, …)` guarantees a positive value. The same `> 0` convention exists in
  `src/battlecode/years/bc23/rules.nim:536`, so the disagreement is year-neutral and pre-existing;
  `match.nim:480` is **not** touched by this diff (`git diff 47f36001..1fc96b4 -- src/battlecode/match.nim`
  shows only `collectGameEvents` bc22 arms, the `first_action`/`rout` year tests, and `winBonusFor`).
  Consequence, observed rather than inferred: this is exactly the trap `871a476` fixed, and it is
  left armed for the next year module — a test (or a variant) that sets `perGameBudgetSeconds = 0`
  intending "unbounded" gets a 1-second guard instead. `defaultGameConfig()`'s value is
  `90` (`sim_types.nim:295`).
- Checklist item: none (advisory). It is not a hang or an unbounded wait — both bounds are explicit
  and both are enforced; the two layers simply spell "no budget" differently.

### N4 — the wall-clock/`deadline` block in the replay shard passes either way, and the deadline path fires only in debug
- Where: `tests/test_bc22_replay.nim:242-262`.
- Observed: the block sets `perGameBudgetSeconds = 1`, `matchBudgetSeconds = 1` on the 60×60 `vortex`
  map and then asserts `reason in [epDeadline, epComplete]` — i.e. it accepts the deadline path
  *not* firing. Only inside `if reason == epDeadline` does it assert
  `plan.abandonAfter[0] >= 0` and add `"abandoned"` to `reDerived`. The CI log for run
  `34288986734` shows the shard reporting **85 checks in debug and 84 in release** — the one-check
  difference is exactly this branch, so the recorded-abandon assertion ran in the debug pass and not
  in release. Corroborating measurement from the same log: `test_bc22_perf` prints
  `fisherman 2000 rounds in 4 s` (debug) and `in 0 s` (release).
- Provenance: this permissive assertion **predates** `871a476` — `git show 871a476^:tests/test_bc22_replay.nim`
  carries the identical `reason in [epDeadline, epComplete]` line; the fix commit changed only the
  comment above it. So it is not a weakening introduced by the fix.
- Checklist item: none directly. Item 5's "every wait has an explicit bound" is satisfied by the
  code (`match.nim:470,480`, `rules.nim:428-437`); this is about test coverage of the record, and
  `design.md:2338-2342` (test 20) asks for record→re-derive of the `abandoned`/`deadline` stop.

### N5 — `record → re-derive` is asserted for `annihilated` and one Singularity rung, not for all six end reasons
- Where: `tests/test_bc22_replay.nim:213-267`; `tests/test_determinism.nim:357-405` (the bc22 block).
- Observed: the replay shard drives a real record→re-derive for `annihilated` (line 216-221) and for
  whichever Singularity rung the `wololo` mirror lands on (line 223-240), then asserts
  `"annihilated" in reDerived` and `reDerived.len >= 2`. `more_gold_net_worth`, `more_lead_net_worth`
  and `coin_flip` are covered **at the world level** by `tests/test_bc22_endladder.nim:52-95`
  (all three rungs plus the fury double-elimination early path, plus a reproducibility assertion on
  the coin flip), but not through the record→re-derive path. The bc22 block added to
  `test_determinism.nim` covers the two independent `java.util.Random` streams and dispatch-path
  determinism, not the end-reason sweep.
- What the note asks: `design.md:2338-2342` — "record → re-derive for **every** bc22 end reason".
- Checklist item: none. Item 2 requires *a* test asserting frame-by-frame re-derivation; that test
  exists and is stronger than the item asks (see "Traced and consistent").

### N6 — `sheet_submitted` records the **unwrapped** node, not the payload "as received"
- Where: `src/battlecode/sheet.nim:150` — `result.submitted = $sheetNode`, executed *after* the
  envelope resolver has replaced `sheetNode` with `payload[key]`.
- Observed: for `{"protocol":"x","doctrine":{…}}` the recorded `seats[].sheet_submitted` is the inner
  `{…}` object, not the whole reply. The envelope key is still machine-visible through the new
  `Sheet.envelope` field (`sheet.nim:149`, written to the replay at `replay.nim:75` and to the
  results document at `results.nim:96`), and the viewer's badge reads both
  (`broadcast.nim:435-442`).
- What the note says: `design.md:1513` — `"sheet_submitted":"{…as received, before unwrapping…}"`.
- Provenance: pre-existing. The `-` side of the `sheet.nim` hunk shows `result.submitted = $sheetNode`
  as unchanged context; the old `"sheet"`-only unwrap had the same behaviour.
- Checklist item: none (advisory).

### N7 — the `archon_lost` beat always reports a level-1 archon's gold drop
- Where: `src/battlecode/years/bc22/rules.nim:286-288` —
  `w.beat(BeatArchonLost, "archon_lost", t, w.robotCountByType(…), goldDropped(rtArchon, 1))`.
- Observed: the third field is the *constant* level-1 drop (20 Au). Per the design's own tables
  (`design.md:297`, `design.md:1564`) a level-3 archon drops **36 Au**, so the event's
  `gold_dropped` and the beat label built from it (`broadcast.nim:389-392`,
  "…and 20 gold is on the ground") under-report a mutated archon. The actual drop credited to the
  world is correct — `world.nim:494-499` uses `goldDropped(kind, r.level)`; only the event field is
  the constant.
- Checklist item: none (advisory). It is a display value, not a rule.

### N8 — a dead `if … : discard` in the round loop
- Where: `src/battlecode/years/bc22/rules.nim:280-281` —
  `if w.archonsAlive[t] < w.stats.archonsStart[t] - w.stats.archonsLost[t]: discard`.
- Observed: the condition is evaluated and the body is `discard`; the archon-loss beat is emitted by
  the loop immediately below (lines 282-288). No effect on state or on the hash chain.
- Checklist item: none (advisory).

### N9 — `endReasonFor`'s `dfNone` fallback names a rung that did not fire
- Where: `src/battlecode/years/bc22/rules.nim:331-334` —
  `case w.domination; of dfNone: "more_archons"; else: $w.domination`.
- Observed: I traced whether `dfNone` is reachable here. `playGame`'s loop
  (`rules.nim:429`) exits only on `not w.running` or `currentRound >= maxRounds`; `w.running` is
  cleared only by `checkEndOfMatch` when `hasWinner` (`rules.nim:172-173`); and
  `checkEndOfMatch` at `currentRound >= maxRounds` always terminates the ladder in
  `setWinnerArbitrary` (`world.nim:606-612`), which sets `dfCoinFlip`. So `dfNone` is **unreachable**
  on the non-aborted path and the fallback string is defensive only. Recording it because a future
  refactor that makes it reachable would silently mislabel a game as `more_archons`.
- Checklist item: none (advisory).

### N10 — `lead_reclaimed` / `gold_reclaimed` are credited to the *killer's* seat at drop time
- Where: `src/battlecode/years/bc22/world.nim:498-499` —
  `w.stats.leadReclaimed[ord(t.other())] += leadDrop`.
- Observed: the metal is dropped on the ground and can be mined by either side (or by nobody). The
  statistic attributes it to the opposing team the moment the robot dies, rather than to whoever
  eventually mines it. `design.md:1487` lists `lead_reclaimed`/`gold_reclaimed` as per-seat keys
  without defining the attribution, so this is a choice, not a contradiction — but the viewer's
  endcard ("lead and gold mined, reclaimed, banked and spent", `design.md:1830`) reads it as if it
  were picked up.
- Checklist item: none (advisory).

### N11 — the beat button's seek fraction does not subtract the scrubber-axis start
- Where: `client/replay_broadcast.html:5455-5467` (bc22 block) —
  `var span = Math.max(1, (s.mx || 1) - (s.st || 0));` … `el.style.left = ((b.t - (s.st||0)) / span)…`
  but `api.seek(b.t / span)`.
- Observed: the marker's rendered position subtracts `s.st` and the click target does not. This is
  **identical, line for line, in all six pre-existing year blocks** (`:3928/3940`, `:4230/4242`,
  `:4534/4546`, `:4878/4890`, `:5165/5177`) and in the bc26 `buildBeatButtons` (`:5841/5852`), so
  bc22 reproduced the inherited convention rather than introducing a divergence. In every frame
  packet this repo emits, `"st"` is the literal `0` (`broadcast.nim:547,675,868,1085,1267,1466,1516`),
  so the two expressions are equal in practice.
- Checklist item: 14(d) requires beats to be labelled `<button>`s that seek to their tick — they are
  `<button>`s with `aria-label` and `title`, and they call `api.seek`. Advisory only.

### N12 — the survival gate's three seeds collapse to two distinct games per map
- Where: `tests/test_bc22_survival.nim:60-66`.
- Observed: the gate loops `seed in [0, 256, 512]` and derives the side assignment as
  `sideAslotFor(seed, 0)`. `maps22.sideAslotFor` is `(seed shr 8) and 1` (design `design.md:1303`),
  so seeds 0 and 512 both give side-A-slot 0 and replay the same game. The test's own header says so
  in as many words ("a third seed that lands on the same side really does replay the first game …
  That is stated rather than hidden"), so it is disclosed, not hidden. Six *games* are played; four
  are distinct.
- Checklist item: none (advisory).

### N13 — two of the design note's survival floors were lowered (with the note's own escape hatch)
- Where: `tests/test_bc22_survival.nim:37-46`.
- Observed: `MinMinersBuilt = 4` (note asked ≥ 25) and `MinSoldiersBuilt = 5` (note asked ≥ 15).
  Both carry the measured healthy-mirror value inline (`8` and `10` for the weak seat) and the
  header records both the healthy and the broken ranges. `design.md:2308-2314` authorises exactly
  this: "lower the committed number to roughly half the weak seat's measured value and record the
  measurement inline — never drop the clause." Half of 8 is 4 and half of 10 is 5, so the rule was
  followed to the letter. Every other floor was kept (`builders 1`, `labs_finished 1`,
  `gold_transmuted 5`, `archons at 1500 = 1`, `lead on map ≥ 25 %`) or raised
  (`MinLeadMined = 1800` against the note's 600).
- Checklist item: 1's second half ("no test loosened"). I am reporting it because it *is* a
  threshold change, and stating that it is the note's own sanctioned path with the measurement
  recorded — it lands inside `design.md`, not against it.

### N14 — the CI viewer smoke's 0 % and 50 % clock readouts are identical for the bc22 replay
- Where: run `34288986734`, `wasm-viewer` job, "Load the bundle in a real browser (ALL SEVEN years'
  replays)" step:
  `scrub readouts (#scrub): 0%="0:14 GAME 1 OF 1 — SNOWFLAKE_REDUX doctrines"  50%="0:14 GAME 1 OF 1 — SNOWFLAKE_REDUX doctrines"  100%="FINAL MATCH OVER doctrines"`.
- Observed: `design.md:2680-2681` says each viewer-smoke run "requires … three **differing**
  clock/scorebug readouts at 0 % / 50 % / 100 %", and `tools/ci/viewer_smoke.mjs:751-753` carries the
  same comment. Reading the code at `viewer_smoke.mjs:755-774`, the three readouts are **recorded**
  into `viewer-smoke.json` and no failure is raised from a comparison between them; `ci.yml:3306-3335`
  gates on `scrub_selector == "#scrub"` (it was `#scrub`), on `#endcard` being computed-shown after
  the 100 % seek and carrying a `clan` line, and on overlay coverage — not on the readouts differing.
  So nothing is red, and nothing was suppressed. The other six years in the same run show only
  1-second deltas too (`0:07`→`0:08` bc26, `0:16`→`0:15` bc23), so the pattern is not bc22-specific.
- What I could not settle: whether the `#clock-time` readout is a *position* readout at all (it prints
  `m:ss`, and `design.md:1815` describes `#clock-time` as `round 1412 / 2000`). See "Could not
  determine".
- Checklist item: 13's requirement is that the `wasm-viewer` job is green **including** the browser
  smoke step; it is, and `"loaded":true` is in the log for all seven replays. Advisory.

---

## Traced and consistent

**Item 1 — CI green, no test disabled/skipped/loosened.**
- `gh run list -R Metta-AI/cogame-battlecode --branch main -w ci.yml`: run id **34288986734**,
  `conclusion: success`, `headSha 1fc96b4966661232a00146368b5ff906c0941903` — the reviewed sha
  exactly. All ten jobs green: `test`, `docker-smoke`, `wasm-viewer`, `parity-oracle`,
  `parity-oracle-bc20/21/22/23/24/25`.
- `git diff 47f36001..1fc96b4 -- tests/` — 29 files, +5627/−21. Every one of the 21 deleted lines is
  in a **pre-existing** file and is replaced by a *wider* assertion: `test_manifest.nim` goes six
  years → seven (`variants.len 6→7`, `year.enum` gains `bc22`, `pages 8→9`, `policies 24→28`,
  `prompts 12→14`, `scripted 12→14`, `owned 6→7`), plus 12 brand-new bc22 policy/end-reason
  assertions (`test_manifest.nim:111-127,138-143,486-505`); `test_viewer.nim` widens the discriminator
  from five-way to six-way and adds the bc22 statrail/scoping/endcard assertions; the single
  `tests/fixtures/replay-bc23.json` deletion is the `game_version` string `GV09`→`GV10`.
- No `skip`/`xfail`/`t.Skip`/`--skip` was added anywhere in `tests/`. The one "skip" branch in the new
  code — `tests/test_bc22_survival.nim:131-135` — is a **hard failure**, not a skip:
  `echo "SKIP: no nim on PATH…"; check("the negative control needs a Nim compiler", false)`.
- `.github/workflows/ci.yml` diff adds **no** `NIM_TESTS`/`NIM_TESTS_DEBUG_ONLY`/
  `NIM_TESTS_RELEASE_ONLY` narrowing. Confirmed from the `test` job log: **all 20** `test_bc22_*`
  shards ran **twice each** (debug and `-d:release`) and every one printed `ok`.
- `871a476` specifically: `git show 871a476` is +52/−21 in one file. Removed lines are
  `result.perGameBudgetSeconds = 0` / `result.matchBudgetSeconds = 600` (replaced by
  `if perGame > 0: …` and `matchBudgetSeconds = max(perGame*2, 600)`, i.e. the default 90 s), one
  comment line, and six assertion statements that are **re-added verbatim** one indent level deeper
  inside `if haveGame(…)`. `haveGame` (`test_bc22_replay.nim:80-87`) itself calls
  `check(name, games.len > 0)`, so an empty `games` seq now prints a FAIL line where it previously
  raised `IndexDefect` (debug) or read out of bounds (release). Net: **+6 assertions, 0 removed,
  0 loosened.** The fix is correct — `defaultGameConfig().perGameBudgetSeconds` is `90`
  (`sim_types.nim:295`), which exceeds the measured debug 2000-round cost of ~4 s
  (`test_bc22_perf` printed `fisherman 2000 rounds in 4 s` in the debug pass of this very run), and
  the wall-clock block still sets its own explicit 1 s pair so the deadline path stays exercised
  (in debug; see N4).

**Item 2 — replay re-derivation, frame by frame, and the viewer derives from it.**
- `src/battlecode/replay.nim:270-279` builds the frame list purely from the recorded games' round
  counts; `:287-312`'s `advance()` steps the sim one round and compares
  `d.session.hashChainHex()` against `record.rounds_chains[at ..< at + ChainHexLen]` for **every
  round**, plus the game's final chain — so the reported `mismatchRound` is the first divergent one.
- The same `Deriver` is what the wasm entry drives: `replay-viewer/bc_replay.nim:93,113-121`
  (`beatsFor(doc, frameOfGameRound)`, `deriver.seek(…)`), and `bc_mismatch_round` is an exported
  symbol in `replay-viewer/config.nims:53`. There is no parallel recording: `rules.nim:299-325`
  folds 9 per-team values plus 7 globals (round, rubble/lead/gold/shared-array FNV-1a checksums,
  exec-order length, the trove `robotsArray()` order hash, the anomaly cursor) into the chain each
  round, and none of those are stored in the replay.
- Asserted by `tests/test_bc22_replay.nim:93` ("and it re-derives with NO hash mismatch"), `:128`,
  `:218`, all from **re-parsed written bytes** (`:73-78`). The wasm module is additionally run under
  node against both the smoke replay and the committed fixture — `wasm-viewer` log:
  `{"loaded":true,"game_version":"GV10",…,"frames":200,"mismatch_round":-1}` twice.

**Item 3 — static viewer.** `coworld_manifest_template.json:14-15`
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present and
mode `100755`; `ci.yml:3154-3175` asserts its presence *and* its executable bit and then runs it as
`./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`; `coworld-release.yml:213-222`
fails the release unless certification reports the static bundle. See N2 for the `/client/replay`
strings.

**Item 4 — both name spaces.** Agents receive only `alias`/`opponent_alias`
(`decide.nim:625` "…Sealed and simultaneous", and the brief payload carries `alias` + `opponent_alias`,
never `names`). The replay carries `names[]` and per-seat `name` (`replay.nim:72-80`), the results
document carries `names` (`results.nim:87`), and the viewer draws both — `doctrinesJson`
(`broadcast.nim:432-433`) emits `alias` **and** `name`, and the endcard prints
`aliases[slot]` + `names[slot]` (`replay_broadcast.html:6177-6179`). In-game aliases are
`Clan Ash`/`Clan Basil`.

**Item 5 — degrade-never-hang, every wait bounded.**
- Doctrine phase: `decide.nim:1023` `initDuration(milliseconds = max(1, config.doctrineBudgetMs))`;
  `:1044` `while open.len > 0 and attempt < 2` (at most two batches); `:1045-1060` a budget check
  that clears `open` and records `timeout` fallbacks; `:1063` the per-attempt deadline
  (`attempt1Ms` then `retryMs`); `:1081` `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`
  hands the deadline to `CURLOPT_TIMEOUT`.
- Match: `match.nim:470` `matchBudget = initDuration(seconds = max(1, config.matchBudgetSeconds))`;
  `:476-478` the per-game elapsed check; `:480` the per-game budget; `rules.nim:427-437` the
  monotonic per-game guard checked every 32 rounds, setting `outcome.aborted`.
- Arithmetic against the variant: `attempt1Ms 20000 + retryMs 12000` inside `doctrineBudgetMs 45000`;
  `perGameBudgetSeconds 110`, `matchBudgetSeconds 340`, `connectTimeoutMs 25000`; manifest
  `episode_timeout_minutes: 20` (1200 s), 60 % = 720 s. 30 + 45 + 340 + 30 = **445 s ≤ 720 s** — the
  note's arithmetic reproduces from the committed variant values.
- No unbounded loop found on the decision or match paths.

**Item 6 — `num_agents`.** Present inside `game_config` for **all seven** variants
(`bc26,bc20,bc21,bc24,bc25,bc23,bc22` — each `2`) and **absent** at every variant top level;
present in `certification.game_config` (`2`); `len(certification.players) == 2`; `player[]` is
exactly `["awu","scaffold"]` == `certification.players` ids. The cert fixture is unchanged and still
on `bc26`, as the brief says it should be. `tests/test_manifest.nim:169-180,235-239` pins all of it.
**`grep -c "SEAT-COUNT FAIL" docker-smoke.log` → 0**; the log shows `seats=2` on all seven episodes,
including `year: "bc22"` with `num_agents: 2` and `maxRounds: 700`, `seed: 2029`.

**Item 7 — scripted baseline plays full episodes legally.**
- `tests/test_bc22_replay.nim:92,124,217,235` assert `reason == epComplete` on all-scripted episodes
  played to the natural end (700 rounds; 2000 rounds; a best-of-three that clinches).
- Legality: `tests/test_bc22_baselines.nim:54-64` plays 9 chassis×map combinations to 800 rounds and
  asserts `w.refusedActions == 0` — every `do*` in `world.nim` re-checks its own `can*` and increments
  that counter on refusal, so a chassis that emits an illegal order is caught. `:136-137` repeats it
  over the 6 competence games. `:62-63` asserts no robot exceeded its `DecisionOps` budget, and
  `:66-97` pins the per-type budgets against the Java bytecode limits and proves `spend()` cannot go
  negative. (Observation, not a defect: this is a *counter*-based legality gate rather than the
  per-action enumeration `design.md:2269-2279` describes; the test header states the substitution.)
- Tuning: `tests/test_bc22_survival.nim:11-35` records the measured healthy-mirror and broken-control
  ranges inline; `tests/test_bc22_knobs.nim` (31 checks, both modes) is the paired-seed knob-teeth
  sweep. The negative control ran and was red for the right reason —
  `BROKEN-CONTROL games=6 failures=63` / `BROKEN-CONTROL: correctly red`, twice (debug and release).

**Item 8 — LLM reply handling.** `decide.nim:1043-1122`: exactly two attempts
(`while … attempt < 2`); a parse or transport failure records a `doctrine_retry` event with a typed
cause (`timeout` | `transport` | `throttled` | `parse`, `:1106-1119`) and re-opens the seat; after
the loop, `:1125-1140` replaces the sheet with `baselineSheet(...)`, sets `result.fallback[slot]`,
emits a `doctrine_fallback` event **and** echoes the literal phrase `falling back` that phase 60
greps for. `client.throttled` short-circuits the retry batch (`:1130-1135`). Fallbacks are countable:
`results.fallbacks` is in the closed key set (`results.nim:240-244`), and docker-smoke asserts
`fallbacks == [0,0]`. Tolerant parsing is `sheet_common.nim`'s fence-tolerant JSON extraction (the
year-neutral path, unchanged), plus the **new** year-neutral envelope resolver
(`sheet.nim:97-149`) implementing the note's five-rule order with `normalizeKey` matching and
unwrapping **at most once**.

**Item 9 — rune-safe truncation.** `sim_types.nim:201-208` (`MaxMottoRunes 48`,
`MaxUnknownFieldRunes 40`, `MaxUnknownFields 16`, `MaxFallbackDetailRunes 200`,
`MaxReplyBytes 16*1024`), `:302-315` (`truncateRunes` / `truncateBytes`, the latter cutting a
*byte* cap on a rune boundary), `:331` `sanitizeLine`. Applied at `sheet.nim:164` (unknown keys),
`:188` (motto), `:196` (the 16 KB byte cap), and `decide.nim:1113` (provider error text).
`tests/test_bc22_sheet.nim:180-207` feeds astral-plane input at the cap and asserts
`runeLen == MaxNoteRunes`, `runeLen == MaxMottoRunes`, `validateUtf8() == -1`,
`motto.runeLen * 4 >= motto.len` (i.e. the input really was multi-byte), and that the 16 KB cut
lands on a rune boundary.

**Item 10 — manifest validates.** `game.protocols` carries **both** `player` and `global`, each a
`{type,value}` object. `game.docs` has `readme` + nine `pages`, every page `{id,title,content{type,value}}`.
`end_reason` gains exactly the three bc22 rungs (`more_archons`, `more_gold_net_worth`,
`more_lead_net_worth`), reuses `annihilated`/`coin_flip`/`abandoned`, and does **not** contain
`resignation`. `sheet_envelope` is added as a new optional year-neutral results property
(`minItems 2, maxItems 2`) and to `ResultsKeys` (`results.nim:240-244`), `CLOSED_KEYS` in
`docker_smoke.sh:431-437` and the manifest in the same commit — the triple-sync tripwire is intact.
See N1 for the `type` discriminator.

**Item 11 — legible at 360 px.** `client/replay_broadcast.html:2580`
`#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` — unchanged and present.
Four `@media (max-width: 640px)` blocks, the bc22 one at `:3600-3613`, dropping word labels to
glyphs while keeping `#bc22-anomaly`'s type word and countdown. The `--killfeed-overlap` gate runs at
360/720/1280 px at FIT and 2× zoom on all seven replays (`ci.yml:3288-3298`).

**Item 12 — release order, scaffold, policies.** `coworld-release.yml` is **not in the diff**; its
step order reads Build manifest (`:168`) → Certify locally (`:182`) → **Upload the policies**
(`:225`, with the comment "BEFORE upload-coworld") → Upload the Coworld (`:323`) → Wait for canonical
(`:361`) → Put the Coworld secret (`:419`). All three workflows present;
`tools/ci/docker_smoke.sh` present and `100755`. The placeholder gate exits 0: grepping
`<slug>|<IMAGE>|<SEATS>` across `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`,
`docker_smoke.sh` and `policies.json` returns **nothing**.
`tools/ci/policies.json` now has **28** entries; the bc22 four are
`battlecode-bc22-rush` (`PLAYER_PROMPT`, 1193 chars, label `rush`, no `player`),
`battlecode-bc22-transmuter` (`PLAYER_PROMPT`, 1407 chars, label `transmuter`,
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), and the two scripted fillers
`battlecode-wololo` (`PLAYER_SCRIPTED=wololo`) and `battlecode-examplefuncsplayer22`
(`PLAYER_SCRIPTED=examplefuncsplayer22`), neither carrying a `player` key. The two champion prompts
are textually different (verified by comparison, not by length). All four use the **player** image
`cogame-battlecode-player:latest`. `tests/test_manifest.nim:486-505` pins indices 24-27 by name,
owner, prompt-difference and filler names.

**Item 13 — viewer executes.**
- `wasm-viewer` job: `needs: docker-smoke` (`ci.yml:3138`), green in run 34288986734, and its
  "Load the bundle in a real browser (ALL SEVEN years' replays)" step ran with **no**
  `continue-on-error` — the only `continue-on-error: true` in the file is `ci.yml:777`, bc20's
  engine-from-source tier, untouched by this diff. Log shows `"loaded":true` for all seven replays
  including `dist/smoke/replay-bc22.json`, and `scrub selector: #scrub` after each.
- bc22 runs at `--timeout 120 --soak 15` (`ci.yml:3284-3292`), as the note decided.
- `data-replay-loaded` / `data-replay-error`: `viewer_smoke.mjs:688-689` reads both attributes and
  the run reported `loaded:true` — set from the shell's own first-drawn-frame path
  (`replay-viewer/static_replay.js`).
- **Lobby dwell cannot occur in this format.** `replay.nim:272-276` constructs the frame axis
  from `for index in 0 ..< doc.plan.maps.len: for r in 1 .. gameRecord(index).rounds` — the axis
  contains *only* in-game rounds, so frame 0 **is** game 0 round 1. Correspondingly every frame
  packet emits `"st": 0` (`broadcast.nim:547,675,868,1085,1267,1466,1516`). There is no pre-game
  record on the playback axis to dwell through.
- **MODULARIZE agreement.** `replay-viewer/config.nims` contains neither `MODULARIZE` nor
  `EXPORT_NAME` (grep returns nothing; the flags are `-s ALLOW_MEMORY_GROWTH`, `-s ABORTING_MALLOC=1`,
  `-s FILESYSTEM=1`, `-s ENVIRONMENT=web,worker,node`, `-s EXPORTED_RUNTIME_METHODS=HEAPU8`,
  `-s EXPORTED_FUNCTIONS=…`), and `replay-viewer/static_replay_worker.js:8,218,274` uses
  `var Module = {}` + `Module.onRuntimeInitialized` + a trailing `importScripts(…)`. Non-MODULARIZE
  build, non-MODULARIZE bootstrap: they agree. `tests/test_viewer.nim:39-52` asserts exactly this
  pairing, and additionally cross-checks every `Module._bc_*` the worker calls against the
  `EXPORTED_FUNCTIONS` list.

**Item 14 — chrome is the starter's.**
- `client/chrome_common.js` is **byte-identical across the range**:
  `sha256 f7860b4c415dabed…` at `47f36001` and at `1fc96b4`. `git diff 47f36001..1fc96b4 -- client/`
  lists **only** `client/replay_broadcast.html`. The hash pin in `tests/test_viewer.nim:31-33` is
  itself unchanged (verified against `git show 47f36001:tests/test_viewer.nim`). `broadcast_core.js`
  likewise unchanged, and it matches `/workspace/starters/coworld-ctf/client/broadcast_core.js`
  exactly. (`chrome_common.js` differs from the coworld-ctf copy in this sandbox, so the note's
  wording at `design.md:1606` about "the coworld-ctf copies" is inaccurate — but the pin, the file
  and the test all predate this run and this run did not touch any of them. For a MOD whose starter
  is the host repo, "byte-identical to the starter's" is satisfied.)
- `client/replay_broadcast.html` is +709/−26 on a ~6300-line page: an appended bc22 game block under
  a banner comment (`:5385-5389`, naming `buildBc22BeatButtons` and every function name it must not
  collide with), plus the four shared endcard fixes the note authorises at `design.md:2000-2003`.
  The 26 deletions are all in the shared endcard renderer and the year discriminator: the bc26-noun
  `ec-wincond`/`ec-how` block replaced by the `data-year`-keyed builder with `window.fmtStat`
  (endcard fixes 1 and 3), the empty-motto fix (`:6175-6177`, `d.motto ? … : ''` — fix 4), and
  `if (!isBc20 && !isBc21 && !isBc23 && !isBc24 && !isBc25)` → the seven-way form. This is an
  extension, not a rewrite.
- Transport rules, each checked in the page:
  (a) `relayout()` (`:6191-6222`) writes `--hudscale`, `--topband`, `--band` and `--statrail` on
      `document.documentElement.style` (`:6192 var root = document.documentElement.style`) inside a
      three-pass fixed-point loop — `:root`, not `#stage`.
  (b) Nothing bc22 is fixed inside the band: `#bc22-econ { bottom: calc(var(--band, 0px) + 8px) }`
      (`:3527`), `#bc22-units { bottom: calc(var(--band, 0px) + 76px) }` (`:3526`),
      `#bc22-doctrines` is `top: calc(var(--topband,0px)+34px)` with
      `max-height: min(46vh, calc(100% - var(--topband,0px) - var(--band,0px) - 46px))` (`:3548-3553`),
      and `#killfeed`'s `bottom` is
      `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))` (`:1270`).
  (c) `#endcard { … bottom: var(--band, 0px); … }` (`:1858`), raised with **`.on`**
      (`:6185 $('endcard').classList.add('on')`, against the `#endcard.on { display: flex }` rule at
      `:1878`), and taken down by **every** seek: `seek()` calls `dismissEndcard()` first
      (`:5879-5881`), transport buttons call it (`:6237`, excluding only loop/skip), and keyboard
      seeks call it (`:6265`, same exclusions).
  (d) Beats are `document.createElement('button')` with `type='button'`, `aria-label`, `title` and a
      click handler that seeks (`:5451-5471`); spoilers via `applyBc22BeatSpoilers` (`:5474-5481`).
      **All fourteen** kinds have a CSS rule and every one is scoped:
      `html[data-year="bc22"] .beat-marker.{doctrine,game,build,lab,sage,tower,mutate,gold,anomaly,dodge,archon,rout,duel,end}`.
      56 `data-year="bc22"`-scoped rules in total, and the non-bc22 hiding rules at `:3465-3468`.
- `--statrail` set: `['econ','bc20-soup','bc20-units','bc21-influence','bc21-units','bc24-crumbs','bc24-levels','bc25-towers','bc25-econ','bc23-econ','bc23-units','bc22-econ','bc22-units']`
  (`:6208-6210`) — the two new boxes added, the eleven existing ones untouched, exactly as
  `design.md:1714-1717` asks.
- `#viewpanel` is **kept** (`:1510-1567`, `?viewpanel=0` still honoured at `:2555-2560`) and the
  board is genuinely pannable: the `bc22` pool spans 30×30 to 49×25 and 45×35 at 16 px/square
  (480–784 px) against a 360 px featured frame, and `ci.yml:3242-3246` records the same reasoning
  in the step that drops `--strict-text-bounds`. Per the brief, not filed as a finding.

**Item 15 — every drawn string fits its frame.** `--strict-text-bounds` is deliberately **dropped**
on the seven bundle replays (`ci.yml:3241-3250`, with the pannable-board reason the flag's own
documentation gives) and the `canvas_text` counts are still recorded in `viewer-smoke.json`. The
worst-case renderer fixture the item requires **exists and gained a bc22 row**:
`tools/ci/renderer_fixture.html` (+84 lines) now carries `YEARS = ['bc26','bc20','bc21','bc24','bc25','bc23','bc22']`,
a `BC22_WORDS` full-cap doctrine block, and bc22 archon/anomaly/econ/units markup, and it is driven
in its own `ci.yml` step (`:3421-3443`) through the same harness with
`--url http://127.0.0.1:8099/renderer_fixture.html --timeout 60 --strict-text-bounds`. That step is
green in run 34288986734.

**Simultaneous decisions go out as one parallel batch.** `decide.nim:1064-1081`: one `RequestBatch`
built over every open seat, then a single `client.curl.makeRequests(batch, …)`. No per-seat
sequential call anywhere on the path.

**Rules traced against the design note's numbered resolution rules (spot checks, all consistent):**
- Round loop order `rules.nim:234-294`: `currentRound++` → chassis round bookkeeping → the exec-order
  **snapshot** with an `existsRobot` guard (`:252-261`) → passive `+2` (`:264`) → the scheduled
  anomaly (`:267`) → the map `+5` (`:271`) → `checkEndOfMatch` (`:294`). Passive-before-anomaly and
  regeneration-after-anomaly are in the note's order (divergence 4).
- Singularity ladder `rules.nim:161-174` → `world.nim:585-612`:
  `setWinnerIfMoreArchons` → `setWinnerIfMoreGoldValue` → `setWinnerIfMoreLeadValue` →
  `setWinnerArbitrary`, i.e. `more_archons` → `more_gold_net_worth` → `more_lead_net_worth` →
  `coin_flip`. Exactly the four rungs the brief names, in that order.
- The **fury early-ladder** path (divergence 7): `anomaly.nim:136-153` calls
  `setWinnerIfMoreGoldValue → …LeadValue → setWinnerArbitrary` when **both** teams are archon-less,
  skipping `MORE_ARCHONS`, and `addHealth(…, false)` at `:163` is what makes that reachable.
  Pinned by `tests/test_bc22_endladder.nim:52-71` (lead rung) and `:52-95` (coin flip, plus the
  "REPRODUCIBLE, unlike Math.random()" assertion).
- `setWinnerArbitrary` (`world.nim:606-612`) draws from `w.rand` (the map-seeded world RNG), the
  documented D3 replacement for `Math.random()`. The game stops immediately afterwards
  (`rules.nim:172-173`), so the shared stream cannot desynchronise a later VORTEX draw.
- Anomaly truncations `units.nim:277-336`: all six are the float32 forms the note specifies —
  `abyssGlobalTake` `int(0.1'f32 * m)` (0 for m ≤ 9), `abyssReserveDelta`
  `int(-1.0'f32 * 0.1'f32 * r)` (25 → −2), `chargeCut` `int(0.05'f32 * n)` (0 for n ≤ 19),
  `chargeSageDelta` 0.22f, `furyGlobalDelta` `int(-1.0'f32 * hp * 0.05'f32)` (150 → −7),
  `furySageDelta` 0.1f, `prototypeHealth` `int(0.8'f32 * full)`, `cooldownWithMultiplier` the
  float64 expression.
- CHARGE `anomaly.nim:98-119`: iterates `w.trove.valuesDescending` (the ported trove order, D2),
  filters `rmDroid` across **both** teams, refreshes each robot's friendly-vision count, then
  `sortedByIt(-numVisibleFriendlyRobots)` — Nim's `algorithm.sorted` is a documented **stable** merge
  sort, matching Java's `Collections.sort`, so ties keep `robotsArray()` order. Each victim goes
  through the ordinary `destroyRobot` (so reclaim drops and `ANNIHILATION` still fire).
- VORTEX `anomaly.nim:227-248`: `symVertical` → flipV (`changeIdx 2`), `symHorizontal` → flipH
  (`changeIdx 1`), `symRotation` → `w.rand.nextInt(square ? 3 : 2)` with `+1` on a non-square map,
  then rotate / flipH / flipV. All four arms, rubble array only. The two RNG streams are proven
  independent by `tests/test_determinism.nim:381-405` (an id draw does not move `w.rand`; a vortex
  draw does not move `idGen.cursor`).
- `destroyRobot` `world.nim:479-520`: reclaim drop **stacks** on the last-occupied square, exec-order
  removal is **by value** with `break` (first match, survivors' order preserved), and
  `ANNIHILATION` fires **mid-turn** and *overwrites* an earlier winner (the second death wins) —
  each of the four subtleties `design.md:546-563` names.
- Scoring `rules.nim:179-205` + `units.nim:342`: `share` is `float32` returning 0.5 on 0-0; the
  weighted sum is `int(64.0'f32 * … + 24.0'f32 * … + 12.0'f32 * …)` — a truncation, in the ladder's
  own priority order and with the note's exact weights. `match.nim:529` puts bc22 in the
  200-per-win bonus set, which is what makes `results.scores` provably win-ordered.
- Doctrine sheet `knobs.nim:107-200`: exactly **eleven** `KnownKeys22`, no `chassis`; the six enum
  knobs default-and-record on a bad value, the five integer knobs **clamp** and record (a
  non-integer defaults); an **absent** known key is recorded in `defaultsApplied` — and only in
  `applyKnobs22`, so the six shipped years' `sheet_defaults_applied` semantics are unchanged
  (`sheet.nim:177-182` comments the scoping and `tests/test_bc22_sheet.nim` asserts the bc23
  control). `plainWords22` (`:273-334`) has no article-plus-enum concatenation anywhere.
  All defaults match the note's table.
- `Bc22RungNames` (`dispatch.nim:187-190`) `["-","annihilated","more_archons","more_gold_net_worth","more_lead_net_worth","coin_flip"]`
  matches `Domination`'s ordinals (`units.nim:84-96`) index for index, and
  `Bc22ActionNames`/`Bc22UnitNames`/`Bc22AnomalyNames` match their enums. The `first_action`
  field is `action`, never `kind` (`match.nim:333-340`), and
  `tests/test_bc22_replay.nim:163-175` asserts every event carries exactly one `kind` key and that
  every `first_action.action` is inside `Bc22ActionNames`.
- Event bounds: `tests/test_bc22_replay.nim:135-159` builds the full per-kind/per-game table from the
  note (`anomaly_struck ≤ 14` against the measured 13-entry maximum) and asserts every emitted kind
  has a declared bound and stays inside it, plus `events.len < 600` for a three-game match.
- Beat contract: `beatsFor` (`broadcast.nim:147-410`) gains `isBc22`, three-way `first_action` and
  `rout` arms, a year-tested `duel` **label**, and ten bc22-only arms; every one builds a non-empty
  label. `tests/test_bc22_beats.nim` (359 checks, both modes) asserts ≥28 beats over ≥10 distinct
  kinds from the **committed** fixture, every kind inside the fourteen-kind vocabulary, and a
  `html[data-year="bc22"] .beat-marker.<kind>` rule for every kind the fixture actually emitted.
- Doctrine card data: `broadcast.nim:421-442` emits `envelope`, `defaults_applied`, `knob_count` and
  the first 120 runes of `submitted` — the submitted-vs-applied badge the envelope pin requires.
  `#bc22-doctrines` is dismissible four ways (close button with `aria-label`, `Escape` scoped to
  `data-year="bc22"`, self-dismissal on the first playback advance at `:5714-5717`, and a 6 s
  timeout), with a re-open chip that **pins** it open.
- `NOTICE` names `years/bc22/constants.nim`, `years/bc22/trove.nim`,
  `years/bc22/chassis/{wololo,kit,econ,archon,miner,soldier,micro,anomaly}.nim`,
  `years/bc22/chassis/{lab,builder,gold,comms}.nim` and `chassis/comms.nim` — all of which exist on
  disk, so the note's layout rule (`design.md:1057-1062`) holds: no licence credit points at a
  missing path.
- `GameVersion` is `GV10` in the committed tree and in the emitted wasm
  (`{"game_version":"GV10"}` from the node smoke); `tests/test_bc22_replay.nim:95-96` asserts both
  the literal and that it is what the build claims. The coworld version bump 0.6.0 → 0.7.0 is
  correctly **absent** (deferred to phase 40 by design).

---

## Could not determine

- **Whether `#clock-time` is a playback-position readout at all**, and therefore whether the identical
  0 % / 50 % readouts in N14 indicate a real seek problem or only a coarse `m:ss` timer. The element
  is `<div class="time" id="clock-time">0:00</div>` (`replay_broadcast.html:3646`), it is inherited
  shared chrome (not bc22 code), and all seven years show sub-second deltas across a 50 % seek in the
  same run. What would settle it: load `dist/smoke/replay-bc22.json` in the bundle, seek to 50 %, and
  read `#clock-time` alongside the frame index the worker reports — if the frame index halves while
  the clock does not, the readout is simply not positional and N14 is cosmetic; if the frame index
  also does not move, the seek is not landing.
- **Whether the Nim port's trove iteration order actually matches trove4j 3.0.3 on the JVM.** I read
  `years/bc22/trove.nim`'s contract and saw `tests/test_bc22_trove.nim` (24 checks, both modes) run
  against the committed `tests/fixtures/trove-bc22.txt` (1803 lines), and `parity-oracle-bc22` is
  green — but I did not run the Java oracle myself, and the `H hashord` comparison is the only thing
  that proves D2. The green `parity-oracle-bc22` job in run 34288986734 is the evidence; I am
  labelling my acceptance of it as **untested by me**, not verified.
- **Whether the released bc22 episode really produces a laboratory and a gold in 700 rounds.**
  `design.md:2649-2653` specifies seven across-the-pair `jq` assertions on the smoke replay
  (`labs_built ≥ 1`, `labs_finished ≥ 1`, `transmutes ≥ 1`, the anomaly-bite sum, …). I confirmed the
  bc22 smoke episode ran with the pinned seed 2029 on `snowflake_redux` and that docker-smoke is
  green, but I did not locate and read the individual `jq` step's committed thresholds against the
  note's floors line by line. What would settle it: `sed -n` on `ci.yml` around line 3020-3110 and a
  comparison of each committed floor against `design.md:2649-2653`.
- **Whether `refusedActions == 0` is as strong as the per-action legality enumeration
  `design.md:2269-2279` describes.** It depends on every `do*` in `world.nim` re-checking its own
  `can*` before mutating state. I spot-checked `doEnvision` (`anomaly.nim:275-289`, which increments
  `w.refusedActions` on refusal) but did not read all twelve action procs. What would settle it:
  reading each `do*` in `src/battlecode/years/bc22/world.nim` and confirming the
  `if not can…: inc w.refusedActions; return false` prologue on each.
