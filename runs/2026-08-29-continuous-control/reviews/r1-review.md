# r1 review — continuous-control

Repo: `Metta-AI/cogame-continuous-control` @ `4c1b31010c5ee6db83185df137d32ea90c3a9016` (current `main`)
Range: `713e9ac..4c1b310` (5 commits, whole tree read as at the reviewed sha)
Files read: 61 (all of `src/cc/*.nim`, `src/*.nim`, `replay-viewer/*`, `tests/*.nim`, `client/*`,
`tools/ci/*`, `tools/*.sh`, `scripts/build_broadcast_page.py`, `.github/workflows/*`,
`coworld_manifest_template.json`, `docs/PHYSICS.md`) + CI run 33248347102 logs + the starter at
`/workspace/starters/coworld-ctf`.
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15).

Method note: everything below marked **observed** was read at the reviewed sha and is quoted with a
line reference; **inferred** means I reasoned from code I read but did not execute; **untested**
means it would take a run to settle. The sandbox has no Nim toolchain, so no test was executed
locally; CI evidence is cited by run id and log line.

---

## Blocking

### F1 — the `stop` record's `detail` is the one string on the replay path with no rune cap
- Where: `src/cc/server.nim:396-409`, `src/cc/replays.nim:223-228`, against `src/cc/sim.nim:671` and
  `src/cc/decide.nim:71-74`
- Observed:
  ```nim
  # server.nim:396-405
  except SimGuardError as guard:
    reason = endFault; rule = erFault
    detail = "sim guard: " & guard.msg
  except CatchableError as error:
    reason = endFault; rule = erFault
    detail = error.msg
  # server.nim:407-409
  if reason != endComplete:
    writer.writeStop(StopPayload(
      tick: gameSim.tick, reason: reason, endRule: rule, detail: detail))
  ```
  `writeStop` writes the field verbatim — `writer.body.addText(stop.detail)` (`replays.nim:228`) —
  with no length or rune handling anywhere in the codec. The *same* string is capped one line later
  on the results path: `sim.stopDetail = detail.truncateRunes(MaxStopDetailRunes)` (`sim.nim:671`,
  200 runes), and the sibling record on the same stream is capped at its call site:
  `"detail": detail.truncateRunes(MaxFallbackDetailRunes)` (`decide.nim:74`). The wall-clock branch
  builds `detail` at `server.nim:314-315` and is likewise uncapped.
- Checklist item: 9 — "Every string that reaches the replay (`say`, `notes`, prompts, **captured
  errors**) is truncated on **rune** boundaries."
- Why blocking: a captured error reaches the replay bytes uncapped and unfiltered. `results.json`
  and the replay's own `stop` record then disagree about the same fact (200 runes vs unbounded), and
  `tools/replay_summary.py` re-emits `stop.detail` into the strict-UTF-8 JSON that phase 60 pipes
  through `jq -e` (`tests/test_cc_replay.nim:193` reads `summary["stop"]["endRule"]`, so the record
  is on that path).
- Honest limits, so the judge can weigh this rather than take my word: I could **not** demonstrate a
  malformed byte reaching that field. Every current source of `detail` is ASCII (`"sim guard: …"`,
  `"wall clock budget of …"`) or already rune-truncated upstream (`llm.nim:163,171,177` truncate every
  provider body with `truncateRunes` before it becomes an exception message). And test 37
  (`tests/test_cc_replay.nim:176-188`) writes a 200-emoji `stop.detail` through `writeStop` and asserts
  strict UTF-8 out, so the *codec* is proven rune-safe — it is the *server call site* that applies no
  cap. A judge that reads item 9 as "no byte-index slicing anywhere" rather than "every such string is
  capped" can reasonably dismiss this.

---

## Non-blocking

### F2 — the system prompt contradicts itself about `brake` (documented divergence #9, half-applied)
- Where: `src/cc/llm.nim:219-223` vs `src/cc/llm.nim:250`
- Observed: the gait glossary carries the reworded, divergence-#9 text —
  `"brake = amplitude zero and PURE DAMPING: the position servo is switched off entirely. … On the
  HOPPER or the WALKER nothing is holding you up any more, so a brake is how you END a stage, not how
  you save one."` — while 27 lines later the READ-THOSE-NUMBERS block still carries the note's
  original folklore line verbatim: `"pitch heading toward the fall limit -> brake for one turn, then
  resume."` `docs/PHYSICS.md:95-99` states the divergence as "the system prompt says so in those words
  rather than repeating the folklore that a brake saves a fall". The code matches the *documented*
  divergence in one place and the *un-documented* original in another, in the same string constant.
- Note says: design.md:816 (`brake = amplitude zero and heavy damping. Kills speed and usually saves a
  fall.`) and design.md:843 (the folklore line). Both champion prompts also still instruct a brake to
  save a fall (`tools/ci/policies.json`, gaitsmith rule 1, throttle "Falls:"), which is the note's own
  text and outside the documented divergence.

### F3 — the seed is randomised *after* `config.update`, and the module comment says the opposite
- Where: `src/continuous_control.nim:4-8` (comment) vs `:45-51` (code)
- Observed: the doc comment reads "SEED RANDOMISATION HAPPENS HERE, BEFORE `config.update`". The code
  runs `config.update(parseJson(runtimeConfig.config))` at `:47`, then `if not seedPinned(...):
  config.seed = randomSeed()` at `:50-51`. Design.md:1025 says "randomised by the runner … **before
  `config.update`** (the starter's rule)".
- Effect traced: the final seed is fixed before `runGameServer`, and the first seed-derived draw is
  `buildStartPose` inside `startStage` (`sim.nim:281-300`), which runs strictly later. A pinned seed
  in the config wins (`seedPinned`), an absent one is randomised. The *behaviour* the note asks for
  holds; only the ordering and the comment are inverted.

### F4 — the shipped baseline band is measured and far wider than the note's, and is not recorded where the test says it is
- Where: `tests/test_cc_baselines.nim:152-198`; `docs/PHYSICS.md` (no such section)
- Observed: test 25 checks **means over 100 seeds**, not per-morphology per-seed bands:
  `dist[0]/n > 0.3` and `< 14.0` (hopper), `> 20.0 / < 58.0` (cheetah), `> 8.0 / < 30.0` (walker),
  plus `trotterTotal/n` in (25, 90) and `plodderLower*100 >= Seeds*80`. The note (design.md:988-991)
  pins `trotter` at **6–14 m** hopper, 30–58 m cheetah, 11–24 m walker, and "`plodder` … on ≥ 90 % of
  seeds"; the code's plodder gate is ≥ 80 %. This is the builder's documented divergence #1
  (measured bands), and the shipped code matches the *divergence*.
- What does not match the documented divergence: the test's own comment says "`docs/PHYSICS.md`
  records the numbers and why the hopper's band is where it is" (`:157-158`). `docs/PHYSICS.md`
  contains no baseline-band section — `grep -in "band"` returns one hit, at `:212`, about the gait
  sweep's objective. The run log (`runs/2026-08-29-continuous-control/log.md`, 25 lines) records no
  divergence at all. So the divergence is real and deliberate, but the pointer to its record is dead.
- Corroborating CI evidence for where the hopper actually sits: the smoke replay's first-frame
  readout is `2.3 m · 0.05 m/s STAGE 1/3 · HOPPER · TICK 367/468` with `RETURN 0.0`
  (run 33248347102, `wasm-viewer` / "Load the bundle in a real browser"). A 0.3 m mean floor is close
  to the "zero floor" the note's gate exists to exclude (design.md:987-989).

### F5 — the hopper has an upper torso-height fall test the note does not give it
- Where: `src/cc/body.nim:132-134`
- Observed: `result.lowY = mm(700)`, `result.highY = mm(4000)`, `result.maxPitch = degQ16(20)`.
  `isUnhealthy` (`body.nim:314-325`) returns `fwHigh` when `y > spec.highY` for any morph with
  `terminates == true`, so a hopper torso above 4.00 m ends the stage as `fell` with `why: "high"`.
- Note says: design.md:277 gives the hopper exactly two conditions — `y < 0.70 m` **or**
  `|pitch| > 20°`. The walker's `0.80 … 2.00 m` band (design.md:279) is implemented exactly
  (`body.nim:216-217`).
- Reachability: **inferred, untested.** The step-8 guard box allows `y ≤ 20 m` (`sim.nim:27`), and
  `MaxLinSpeed` 12 m/s makes 4 m ballistically reachable in principle; nothing in the shipped gait
  table drives a 15.49 kg hopper there. `tests/test_cc_sim.nim:326-353` asserts `isUnhealthy` against
  its *own* `s.highY`, so it cannot catch this.

### F6 — the observation's per-joint array is `joints_detail`, not `joints`
- Where: `src/cc/report.nim:98-108`
- Observed: `body` carries `"joints": sim.spec.jointCount` (a count) and `"joints_detail": joints`
  (the array).
- Note says: design.md:697-711 shows one `body` object with `"joints": 6` **and** `"joints": [...]`
  — two keys of the same name, which is not constructible JSON. The code's rename resolves an
  impossible spec; §Tests 26 (design.md:2021) asserts "`joints` and `feet` always have the
  morphology's exact counts", which the code satisfies for `feet` (array) and for `joints` (count).
  Consequence: a policy reading the note's example verbatim looks for `body.joints[]` and finds an
  integer.

### F7 — the state JSON emits `cc_beats`, not the note's `beats`
- Where: `src/cc/broadcast.nim:238-244`; `tests/test_cc_viewer.nim:165-167`;
  `client/replay_broadcast.html:3283-3292`
- Observed: `state["cc_beats"] = beatRows`, with the reason stated in-line: "NOT `beats`: the
  inherited chrome's `ingestBeats` would turn that key into unlabelled `<div>` markers. The game
  block reads `cc_beats` and draws LABELLED, CLICKABLE BUTTONS instead." Test 46's key list omits
  `beats` accordingly and adds `check state.hasKey("cc_beats")` (`:178`).
- Note says: design.md:1604 lists `"beats": [{"t": 213, "k": "fall"}, …]` in the state object and
  §Tests 46 (design.md:2109-2110) names `beats` in the required key set. Checklist item 14(d) is
  satisfied either way: the markers are `<button class="beat-marker <kind>">` with `title`,
  `aria-label` and a click that seeks (`replay_broadcast.html:3269-3280`), and CSS exists for exactly
  the six emitted kinds and no others (`:3179-3185`, verified against `sim.BeatKinds`).

### F8 — the derived `fallback` beat/feed line drops the cause
- Where: `src/cc/sim.nim:432-433`; `client/cc_block.html:647-649`;
  `src/cc/replay_runtime.nim:218-219`
- Observed: `if order.source == osFallback: sim.emit(%*{"k": "fallback", "cause": "fallback"})` — a
  literal, not the real cause. The feed renders `ccFeed('MISSED THE CALL — trotter order')` with no
  cause, and the pre-scan's beat label is the same string.
- Note says: design.md:1387 `fallback {cause}`; design.md:1658 the feed line is
  `MISSED THE CALL — trotter order (timeout)`. The real cause **is** preserved in the replay's
  `fallback` chat record (`decide.nim:71-74`, one of the eight documented causes), so nothing is
  lost from the bytes — only from what the spectator reads.

### F9 — both `--strict-text-bounds` gates ran on zero drawn strings
- Where: CI run 33248347102, `wasm-viewer` job, both smoke steps; `client/*.js`, `client/*.html`
- Observed: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` — reported identically by the bundle smoke (10:43:53.862) **and** by the
  renderer fixture (10:43:55.613). Checklist item 15 says in terms: "`total: 0` means the check
  covered nothing … and is not evidence of anything."
- Why it is 0, traced: `grep -c 'fillText\|strokeText'` returns **0** for all four client files
  (`chrome_common.js`, `broadcast_core.js`, `replay_broadcast.html`, `cc_block.html`). This viewer
  draws no canvas text at all — every readout is DOM (the smoke's own `clock` and `scorebug` fields
  came back as populated DOM strings), and the design's §Legible at 360 px says so at design.md:1743
  ("Every glyph either panel draws is a baked chip, never live text"). The board additionally renders
  in a Worker on an OffscreenCanvas (`static_replay_worker.js:8,188,239`), which item 15 names as the
  other cause of `total: 0`.
- Net: the letter of item 15 is met (`never_inside == 0`, `--strict-text-bounds` present in
  `ci.yml:338` and `:379`, the fixture exists and runs its own step), and the class of bug it guards
  cannot occur here because there is no canvas text. What is *not* covered by any gate is DOM
  overflow of the LLM-authored strings (`say` at 140 runes into `#killfeed`, `cc_block.html:593-615`).

### F10 — `config.nims` preloads `client/art`, one link flag beyond the note's list
- Where: `replay-viewer/config.nims:31-36`, `:54`
- Observed: `--preload-file {rootDir / "client" / "art"}@client/art` in addition to
  `--preload-file …/data@data`, with the reason in-line (the renderer opens `client/art/walls/*` and
  `client/art/lockerroom/bg.jpg` while baking, and under emscripten the path must exist in MEMFS).
  The comment calls it "the one link-flag change beyond the renames ctf's file needed".
- Note says: design.md:1440 enumerates the flags and lists only `--preload-file <root>/data@data`.
  Everything else on that line matches exactly, including the absence of `MODULARIZE`/`EXPORT_NAME`,
  `-s ABORTING_MALLOC=1`, and the `_cc_*` export list (verified name by name).

### F11 — the replay is ~132 KB, not the note's ~32 KB (documented divergence #9, confirmed)
- Where: CI run 33248347102, `docker-smoke`: `smoke OK: seats=1 results=835B replay=132082B
  reason=complete`; cause at `src/cc/decide.nim:109-116`
- Observed: `orderRecord` attaches the whole observation (`record["view"] = mirrored`, the view minus
  `last_turn.notes`) to every per-turn chat record, guarded at `MaxOrderRecordRunes = 6000`
  (`sim_types.nim:43`, `decide.nim:118-122`). Design.md:1134-1135 predicts ≈ 32 KB from
  "1512 hashes + 3 stage records + ≤ 42 order records + 32 keyframes + ~60 chat records + a ~9 KB
  config"; the note's own §Record vocabulary (design.md:1375) does require `view` on the `order`
  record, so the note's own size estimate is what is wrong, not the record shape. Code matches the
  documented divergence.
- Side effect worth naming: `tests/helpers.nim:71-72` records with `orderRecord(sim, order, …, nil)`
  — no view — so the record→re-derive tests (34–36) exercise a replay a third the size of the one
  the server writes. The wasm viewer is exercised on the real 132 KB file by the CI smoke, so the
  gap is covered elsewhere.

### F12 — ctf scorebug internals the note lists as removed survive in the inherited plate markup
- Where: `client/replay_broadcast.html:1887-1910`; overwritten at runtime by
  `client/cc_block.html:343-372`
- Observed: the inherited plate builder still emits `class="hcap"`, `class="lives-num"`,
  `class="pb-tags pb-lbl"` and `class="squad"`. `scripts/build_broadcast_page.py:199-207` renames
  `.lives-label` → `.stage-label` and `.flagicon` → `.stagechips` but cuts none of the others.
- Note says: design.md:1513-1514 lists `.hillchip`, `.hcap`, `.flagicon`, `.lives-num`,
  `.lives-label`, `.squad-pip`, `.pb-tags`, `.squad` among "Elements removed (exactly these, and the
  JS that feeds them)".
- What is actually drawn: `ccPlate` rewrites the plate contents each frame, and the CI smoke's
  scorebug readout is `ALPHA trotter RETURN 0.0 2.3 m · 0.05 m/s STAGE 1/3 · HOPPER · TICK 367/468`
  — no paintbot residue reaches the spectator. `tests/test_cc_endcard_labels.nim:12-13` documents
  the decision ("renaming a dead identifier is a rewrite of working chrome, not a re-labelling").

### F13 — the forbidden-vocabulary grep is narrower than the note's list
- Where: `tests/test_cc_endcard_labels.nim:41-47`
- Observed: the list is `["Lives", "LIVES", "Clstr", "flagicon", "heart", "paint", "hoppers",
  "hillchip", "POV", "EYES", "spray", "grenade", "med kit", "killfeed(", "squad-pip"]`, applied to
  the **appended block only** (`blockText`, `:20`).
- Note says: design.md:1557-1559 lists `Lives`, `LIVES`, `Clstr`, `Cap<`, `flag`, `heart`, `paint`,
  `hopper`(case-sensitive `hoppers`), `hill`, `POV`, `EYES`, `spray`, `grenade`, `med kit`, `kill`,
  `team`. The code substitutes narrower tokens for `flag`→`flagicon`, `hill`→`hillchip`,
  `kill`→`killfeed(` and drops `Cap<` and `team`. The narrowing is forced by the block's legitimate
  use of the inherited API (`ctx.pushFeed` writes into `#killfeed`; the state object's one team key
  is `alpha`), and the header comment says so.

### F14 — the player container does not ack frames with `0x85`
- Where: `src/continuous_control_player.nim:79-115`
- Observed: the receive loop re-sends the registration blob for the first 10 s
  (`ReRegisterSeconds`), logs `welcome`, breaks on `done` or on a closed/raising socket, and
  `quit(0)`. There is no per-frame acknowledgement.
- Note says: design.md:1248 — "the player harness only acknowledges frames (`0x85` after every frame,
  exactly as `src/paintball_player.nim` does)".
- Effect traced: `fastMode: true` and the server computes every joint target; nothing in
  `server.nim` reads or waits for an ack (`websocketHandler:614-661` only interprets chat frames and
  Pings), so no wait depends on it. The close-frame race the note names is handled
  (`:87-95`, exit 0 on a dead socket).

### F15 — `/client/replay` is still routed by the game server (deliberately, per the note)
- Where: `src/cc/server.nim:668` (`result.get("/client/replay", replayPageHandler)`)
- Observed: the route exists and serves `client/replay_broadcast.html`. The manifest declares only
  `"replay_viewer": {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json`, `game`
  block) and contains no `/client/replay` string anywhere; `coworld-release.yml:200-215` fails the
  release unless certify prints the STATIC-bundle liveness marker.
- Note says: design.md:1424-1425 — "**No `/client/replay` live-server viewer is ever declared to the
  platform**; the game still serves `/client/replay` locally for developers." Checklist item 3's
  phrasing is "No `/client/replay` pod path anywhere", which a judge may read more strictly than the
  note does; recording it here so the ambiguity is on the record rather than silently resolved.

### F16 — four of the nine builder divergences are in `docs/PHYSICS.md`; the rest live only in code comments
- Where: `docs/PHYSICS.md:57-103` (10 numbered divergences);
  `runs/2026-08-29-continuous-control/log.md` (25 lines, no divergence entries)
- Observed, mapping the brief's nine against the tree:
  - measured baseline bands → **not** in PHYSICS.md; in `tests/test_cc_baselines.nim:153-158` only (F4)
  - brake cannot save a fall → PHYSICS.md #9 ✓ (but see F2)
  - stand = neutral pose → PHYSICS.md #10 ✓, code `gaits.nim:65-71` ✓
  - crouch = shallowest quiet pose → `gaits.nim:72-78` and `:104-107` only, not in PHYSICS.md
  - solver bounds 7 mm / 21 mm → PHYSICS.md #1 ✓
  - torso 1.21 m vs 1.25 m → PHYSICS.md #2 ✓
  - seek = rewind + re-step → `src/cc/replay_runtime.nim:5-12` only
  - tuning `--check` compares committed JSON → `.github/workflows/ci.yml:104-115` only
  - `wasm_replay_smoke.cjs` not wired / `test_cc_labels` folded → nowhere in prose; verified by
    `grep -rn wasm_replay_smoke .github tools/ci` returning nothing, and test 48 living in
    `tests/test_cc_viewer.nim:183`
  - replay ~130 KB → nowhere in prose (F11)

### F17 — `writeHash` drops the tick tag the note gives it
- Where: `src/cc/replays.nim:230-231`, `src/cc/server.nim:365`, `src/cc/replay_runtime.nim:151-157`
- Observed: `proc writeHash*(writer: ReplayWriter, value: uint64) = writer.hashes.add(value)` — the
  hash array is positional; the tick is implied by index. Playback consumes one entry per stepped
  tick (`hashIndex` incremented only when `stepTick` advanced, `replay_runtime.nim:146-157`).
- Note says: design.md:428 — `replayWriter.writeHash(uint32(tick), sim.gameHash())`.
- Traced consequence: alignment holds because the recorder appends exactly one hash per `stepTick`
  (`server.nim:364-365`, and identically in `tests/helpers.nim:77-78`) and `stepTick` cannot return
  without advancing while `phase == phPlaying|phStageReset` (`sim.nim:527-534`). A future recorder
  that ever wrote a hash without a tick would misalign the whole chain silently instead of at the
  offending tick; today it does not.

### F18 — `isqrtQ16` is defined and never called
- Where: `src/cc/report.nim:18-42`
- Observed: `grep -rn isqrt src/` finds the definition plus three doc-comment mentions and no call
  site. The design's constraint (design.md:178-179, "isqrtQ16 exists in one place only —
  `src/cc/report.nim`") is satisfied trivially; foot slip is reported as `|vx|` rather than a
  magnitude (`body.nim:305-308`), which is what removes the need for it.

---

## Traced and consistent

**Resolution order (design.md:345-432 vs `src/cc/sim.nim:524-606`)** — the ten numbered per-tick
steps appear in the note's order and nothing else mutates the world: clocks `:530-534`; stride phase
`:537-547` with the `StageReset` order forced to `{gait: brake, power: 0}` at `:539-542`; driver
`:549-555`; physics `:557-560`; accounting `:562-563`; termination in the note's order — `lined`
first (`:568`), then `fell` (`:571-578`), then `stageTick >= stageTicks` (`:579-581`); milestones
`:583-591`; invariant guard `:598-599`; hash + keyframe `:601-606`; the reset-hold → next-stage
transition `:592-596`. Substep order inside `stepBody` (`solver.nim:249-272`) is gravity → servo →
`iterations ×` (joint points → joint limits → contacts) → integrate → clamp, matching design.md:386-410
term for term, including `tauCap = tauMax·(40 + 60·power div 100) div 100` (`solver.nim:60-63`),
Baumgarte 1/5 on joints and contacts, 1/4 on limits, restitution 0, and Coulomb friction clamped to
`GroundFriction × accumulatedNormalImpulse` (`:229-231`). `resolveStage` credits `lined` with
`distance = 60.000` and `uprightTicks = stageTicks` (`sim.nim:375-378`), as design.md:419-420 requires.

**Turn grid never re-aligned** — the server issues a turn, then steps exactly `turnTicks`
(`server.nim:361-362`), so boundaries stay on `t mod 36 == 0` regardless of when a stage resolved;
`sim.turnDue` (`sim.nim:613-618`) states the same rule and is exercised by test 10.
`closeStageTurns` (`sim.nim:302-310`) banks a stage's turn count when the *next* stage starts, which
is what makes `Σ stageTurns == turnsPlayed` true across a mid-turn stage change.

**Decision path (design.md:591-651 vs `src/cc/decide.nim`)** — budget guard first
(`:181-190`: `elapsed + 2 × ceil((turnSpacing + turnBudget)/1000) > wallClockBudgetSeconds` →
`llmOff`, one `budget_guard` record, echo); scripted seats return without a call (`:191-192`); no
credentials → instant fallback (`:194-199`); rate guard at 28 requests in a trailing 60 s
(`:49-57`, `:131-141`, `:201-205`) with no sleep; the spacing floor sleeps at most `turnSpacingMs`
between request *starts* (`:211-216`); then `while attempt < 2` (`:222-277`) — one request per
attempt through `engine.client.curl.makeRequests(batch, …)` with `batch.post(...)` carrying exactly
one entry (`:248-252`), deadline `max(1000, min(configured, remaining))` where `configured` is
`attempt1Ms` (6000) on attempt 0 and `retryMs` (3000) on attempt 1, both clamped by what is left of
`turnBudgetMs` (9000). The two log phrasings are exactly the note's: attempt 1 emits
`"attempt 1 failed, will retry: "` (`:274-275`) and only the post-loop path emits
`"falling back to trotter ("` (`:283-284`). `no_credentials` also prints the phase-60 grep string
`"the LLM provider is unavailable"` at `llm.nim:119-120`. The fallback order is the *imported*
`trotter` proc, never a duplicate (`:168`, `scriptedOrder(engine.params, sim, blTrotter)`), which
`tests/test_cc_baselines.nim:38` pins.

**Every wait and its bound.** Lobby connect: `lobbyJoinTimeoutTicks / TargetFps` = 100 s, polled at
200 ms (`server.nim:228-237`). Register grace: 4 s (`:239-248`). Turn spacing sleep: ≤ 2.6 s
(`decide.nim:211-214`). Attempt deadlines: 6 s / 3 s inside a 9 s monotonic turn budget. Inner tick
loop: exactly `turnTicks` iterations (`server.nim:362`). Outer loop: `episodeOver()` — `phGameOver`,
`ladderComplete`, `turnsPlayed >= maxTurns`, or `tick >= maxTicks` (`sim.nim:608-611`). Solver: fixed
`10 × 12` passes, no convergence loop (`solver.nim:258-268`). Artifact POST: 60 s curl timeout
(`server.nim:119`). Shutdown grace: 20 s then `quit(0)` (`:414-415`). `wallClockBudgetSeconds` is
checked at the top of every outer iteration (`:311-317`) and `sim_config.validate` refuses anything
over 720 (`sim_config.nim:162-165`); both shipped variants declare 690 and the cert fixture 240.
Worst-case settle time, **inferred**: the guard trips at `elapsed > 666 s` and puts every remaining
turn on the microsecond-cost scripted path, so the 690 s stop is reachable only through scripted
play; even assuming the guard never fired, the last turn admitted at 689 s can consume
2.6 + 9 = 11.6 s, giving ≈ 701 s to `settle` + artifact write — inside 720 s. The 20 s
`/healthz` grace runs *after* results and the replay are written.

**Rune truncation on every other replay-bound string** — `say` ≤ 140 (`directives.nim:26-38`
truncates *before* the control-character filter, then `decide.nim:108` truncates again on the record);
`notes` ≤ 320 (`directives.nim:40-44`); policy label ≤ 48 and player name ≤ 48 at the ingest point
(`server.nim:600-606`) and again in `registerRecord` (`decide.nim:82`); prompt ≤ 4000 at both ends
(`continuous_control_player.nim:41`, `server.nim:586`) and never written to the replay
(`decide.nim:76-83`, asserted by `tests/test_cc_replay.nim:104`); `fallback.detail` ≤ 200
(`decide.nim:74`); `results.stopDetail` ≤ 200 (`report.nim:301`, `sim.nim:671`); provider bodies ≤ 200
before they become exception text (`llm.nim:163,171,177`). `truncateRunes` is the single
implementation (`sim_types.nim:194-202`) and uses `runeLen`/`runeSubStr`. Test 37 feeds 4-byte emoji
at *every* cap and asserts strict UTF-8 out of `replay_summary.py`.

**Replay writer** — magic `COWLDCCL` + format version + game name/version/protocol + the resolved
config JSON (`replays.nim:176-183`); record kinds `stage|order|chat|stop|keyframe` (`:34-39`);
per-tick `gameHash` (`server.nim:365`); keyframes every `stateKeyframeTicks` and at every stage start
(`server.nim:366-368`, `:379-383`, `sim.nim:604-606`, `:354`). Self-sufficiency verified against
design.md:1359 field by field in `sim_config.nim:239-285`: seed, variant, `num_agents`, the whole
`MorphTable` per morphology including every link's `hl/r/m/invM/invI/inertia` and every joint's
parent/child/offsets/mount/limits/`tauMax`/side (`morphJson`), the whole `GaitTable` including
`kp/kd/kdBrake` (`gaitTableJson`), every solver constant (`solverJson`), `players[].name`, `slots`,
`fastMode`. Signed words go out through `cast[uint32]` and come back through `cast[int32]`
(`:102-107`, `:150-152`) — the wasm32 fix from commit `cfe8855`.

**Viewer re-derivation** — `replay-viewer/cc_replay.nim` imports `cc/sim` (`:3`), so the wasm module
is the same sim; `initReplayRuntime` → `scanReplay` (keyframes + orders only, no re-simulation) →
frame 0 (`cc_replay.nim:63-99`). `stepReplay` compares `data.hashes[hashIndex]` against
`sim.gameHashValue` every tick and latches `hashMismatchTick` (`replay_runtime.nim:151-157`);
`applyRecordsAt` compares every recorded keyframe word for word and resyncs from the recording on a
mismatch (`:115-130`). Seek is rewind + re-step from tick 0 (`:159-169`) with the reason stated in
the module header — documented divergence #6, and the code matches it. `startTick` is 0 and every
seek clamps to it (`:341-344`); `newSimFromReplay` sets `phase = phPlaying` (`:72`), and the
recording contains no lobby frames at all (the server's lobby wait happens before
`writer` sees a tick), so playback opens on the first game tick and the scrubber axis `st = 0` agrees
— checklist item 13's "never the recorded lobby" holds for the degenerate reason that this game
records no lobby. Applying a stage record whose tick equals the tick at which re-simulation already
started that stage calls `startStage` a second time; I traced it as idempotent (same index, same
seeded pose, all accumulators already zero) and CI's hash-clean playback corroborates.

**Emscripten bootstrap** — `config.nims` has no `MODULARIZE` and no `EXPORT_NAME`, and the shell is
the non-modularized `var Module = {}` + `Module.onRuntimeInitialized` + `importScripts('./…
cc_replay.js')` (`static_replay_worker.js:8`, `:188`, `:239`). `diff` of both
`replay-viewer/static_replay.js` and `static_replay_worker.js` against the starter's files, after the
mechanical `ctf`→`cc` rename, is **empty** — same starter, no splice. `Dockerfile.replay-viewer:60-62`
asserts `! grep MODULARIZE`, `! grep EXPORT_NAME`, `grep ABORTING_MALLOC=1` at build time.
`data-replay-loaded="true"` is set in the `'loaded'` branch of `onWorkerMessage`
(`static_replay.js:161`), `data-replay-error` in `showFailure` (`:14-20`), `data-replay-mismatch-tick`
at `:32`.

**Chrome provenance** — `client/chrome_common.js` is byte-identical to
`/workspace/starters/coworld-ctf/client/chrome_common.js` (`diff` empty), 40 022 bytes, sha256
`7ace7287…72f7c`, exactly the note's pin, and `tests/test_cc_viewer.nim:20-25` pins both.
`client/replay_broadcast.html` **regenerates byte-identically** from the starter's page:
`python3 scripts/build_broadcast_page.py /workspace/starters/coworld-ctf/client/replay_broadcast.html
/tmp/regen.html client/cc_block.html` → `diff` empty. The inherited prefix is 147 690 chars against
the starter's 222 197 to the same banner; I measured every cut the script makes and all 74 978 removed
characters are accounted for by the note's own removal list — 43 087 of raycast FPV pipeline
(`renderFpv`, `drawFpvEntity`, `renderFpvMap`, … 22 functions), 12 625 of base64 `.ec-heart` PNGs,
5 493 of zoom/minimap wiring (`sliderToZoom`, `syncViewUi`, `minimapSeek`, …), 4 330 of viewpanel CSS,
and thirteen smaller spans. The file is not a rewrite. Sections 1–5 survive: I checked the 50
structural ids test 42 lists, plus `#endcard`, `#scrub`, `#momentum`, `#lulls`, `#lockerroom`,
`#transport` and its nine buttons, all present.

**Transport rules** — (a) `relayout()` measures `#transport`/`#scorebug` and sets `--band`,
`--topband`, `--hudscale` on `document.documentElement` (`replay_broadcast.html:2905`, `:2925-2931`),
iterating to a fixed point; it is the starter's code, unmodified. (b) `#endcard { … bottom:
var(--band, 0px); }` (`:830`) and no game-block element is `position: fixed` — every added panel
anchors to `var(--topband)` (`cc_block.html` `#cc-ribbon`/`#cc-pips`/`#cc-strip`, pinned by test 45
`:146-153`). (c) the endcard is shown as `#endcard.on` and every frame that is not `gameover`
removes the class (`:1770-1771`), so any seek pulls the match back. (d) beats are labelled
`<button class="beat-marker <kind>" title aria-label>` that `ctx.send('s:' + tick)` on click
(`:3265-3281`), never `markBeat`; CSS exists for exactly `{stagestart, milestone, fall, stageend,
fallback, end}` (`:3179-3185`) and test 44 asserts set equality against `sim.BeatKinds` plus the
absence of the eight ctf kinds. `#viewpanel`/minimap/zoom are removed (markup, CSS, wiring and ids —
`attachMinimap(` and `renderFpv(` appear nowhere), `#fpv` internals are repurposed as the gait card
with `#fpv-cap` reading `GAIT ORDER`, and `#plates-r` is kept and rendered empty (one `teams` key,
`broadcast.nim` `teamsJson`, pinned by test 46 `:172-174`).

**Legibility at 360 px** — `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden;
text-overflow: ellipsis; white-space: nowrap; }` (`replay_broadcast.html:2990-2996`) and
`@media (max-width: 640px) { .stage-label, .cc-alias, .fl-cap { display: none; } }` (`:3217-3219`) —
checklist item 11 exactly.

**Manifest** (`coworld_manifest_template.json`, parsed) — `num_agents: 1` inside `ladder.game_config`,
`bipeds.game_config` **and** `certification.game_config`, and absent from every variant top level
(variant keys are exactly `id, name, description, game_config`). `replay_viewer: {"bundle":
"static-replay-viewer"}` under `game`. `game.docs` = `{readme, pages[3]}` with `id/title/content`
objects; `game.protocols` carries both `player` and `global` as `{"type","value"}` objects.
`config_schema` `additionalProperties: false`, `required: ["tokens","players"]`, every array property
carries `minItems`/`maxItems` (`tokens` 1/1, `players` 1/1, `slots` 0/1, `stageLadder` 3/3); no
`game_config` contains a literal `tokens`. `results_schema` is closed and its 38 keys equal
`report.ResultsKeys` exactly, with the closed `reason`/`endRule`/`stageOutcome`/`stageMorph` enums.
Top-level `tags` (5), `episode_timeout_minutes: 20`, no `game.tags`, `player[]` has one entry
(`trotter`) with `limits.cpu: "1"`, seated in `certification.players`. Both variants declare
`wallClockBudgetSeconds: 690`.

**Integer/determinism discipline** — no `float`, `sqrt`, `math.sin`, `std/math`, float literal or `/`
in `src/cc/{sim,solver,body,driver,gaits,trig}.nim` (I re-ran the greps by hand: only
`import std/json` matches `/`). Every `shr` in those files is on a `uint64`
(`sim.nim:150,152,153,205` — splitmix64 and the FNV mixer); no signed `shr` anywhere. `mulQ` is
`(a * b) div OneQ16` (`trig.nim:42-45`). `SinQ16Table` is 1025 committed `int32` entries
(`trig.nim:67-197`) with `sinQ16` doing integer quadrant reduction and linear interpolation.
`isqrtQ16` is confined to `report.nim`. `computeGameHash` (`sim.nim:207-241`) mixes exactly the
fields design.md:1123-1127 lists, in that order, and mixes no FX, feed text, `say`, `notes` or label.

**Tests** — 12 files, **62** `test` cases (counted), numbered against the note's §Tests 1–49 with
test 48 folded into `test_cc_viewer.nim` (documented divergence #8). Coverage I verified by reading:
sim units 1–14; bounded/legal orders on *both* baselines over 300 states (22); the fallback-is-trotter
identity (23); validator clamping/inheritance/rune truncation with emoji at 140/320 (24); end-to-end
episode writing artifacts with the seven results identities and a key-set equality against the
manifest (29, 29b); record→re-derive for **all four** end reasons including the stop tick
(34 — `ladderComplete`, forced `wallClock` via `stopAtTurn`, forced `fault` via `faultAtTurn`, and
`turnCap` via a shortened config); strict-UTF-8 `replay_summary.py` with 4-byte emoji at every cap
(37); manifest pins including per-variant `GameConfig` construction (39, 39b) and the installed CLI's
own validators (40). Iteration counts scale down in debug only (`Heavy`, `Seeds`, `Ticks`) and CI runs
every file in **both** debug and `-d:release`, so the release pass carries the full counts.

**CI, item 1** — run **33248347102**, `headSha 4c1b31010c5ee6db83185df137d32ea90c3a9016`, conclusion
`success` on `main`; all three jobs green with every step `success`, including `wasm-viewer`'s
"Load the bundle in a real browser" and "Drive the text path at full cap in the real bundle"
(neither is `continue-on-error`), and `wasm-viewer` `needs: docker-smoke` (`ci.yml:231`). Second half:
`git log --oneline --all -- tests/` returns **one** commit (`713e9ac`, the initial import) and
`git log -p 713e9ac..HEAD -- tests/` is empty — no test was disabled, skipped, loosened or removed
during this run.

**Item 6 evidence** — `tools/ci/docker_smoke.sh:93` runs the seat-count preflight (four `SEAT-COUNT
FAIL:` invariants at `:110-150`: `num_agents` present, a positive integer, `len(certification.players)`
equal, `len(certification.game_config.players)` equal, plus the independent `SMOKE_SEATS`
cross-check) **before** the first `docker run` at `:202`. `grep -c "SEAT-COUNT FAIL"` over the whole
run log: **0**. The smoke ran with `SMOKE_SEATS: "1"` and `SMOKE_REQUIRE_REPLAY_JSON: "0"` and printed
`smoke OK: seats=1 … reason=complete`.

**Item 12 evidence** — `coworld-release.yml` step order is Build the Coworld manifest (`:159`) →
Certify locally with `--timeout-seconds 300` (`:173-215`) → Upload the policies (`:216`) → Upload the
Coworld (`:314`) → Wait for canonical (`:352`) → Put the Coworld secret (`:410`). All three workflows
present; `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both mode **100755** in the
index. `tools/ci/policies.json` has four policies, all `run: /bin/continuous-control-player`: two
`PLAYER_PROMPT` champions (`continuous-control-gaitsmith`, 1843-char prompt;
`continuous-control-throttle`, 1669-char prompt, carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) plus scripted `trotter` and `plodder`. The
placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`,
`coworld-release.yml`, `coworld-submit.yml`, `tools/ci/docker_smoke.sh`, `tools/ci/policies.json`
returns nothing. The only angle-bracket residue in those files is the documented set —
`<cow_id>`/`<sha>` in `ci.yml:221`, `<run_id>` in `coworld-release.yml:21` and
`coworld-submit.yml:17`, `<name>:vN` in `coworld-submit.yml:31`.

**Both name spaces (item 4)** — the observation's only identity is `"you": seatAlias(seat)`
(`report.nim:140`), and `tests/test_cc_obs.nim:93-131` greps a whole recorded episode's prompts for
the seed, unstarted perturbations, raw gait constants, servo gains and the real name. The real policy
name lives in `results.names` (`report.nim:234`), the replay's `register` record (`decide.nim:81`)
and the viewer's `roster[].name` / `cc.name` (`broadcast.nim:206-207`), never on the board
(`showPlayerLabels: false` in both variants; `boardLabelVocabulary()` is pinned by test 48 and
asserted not to contain `daveey`).

---

## Could not determine

- **The 50 %/100 % scrub readouts are identical in the CI smoke.** Run 33248347102 logs
  `scrub readouts: 0%="… TICK 367/468"  50%="17.0 m · 2.94 m/s STAGE 2/3 · CHEETAH · TICK 257/468"
  100%="17.0 m · 2.94 m/s STAGE 2/3 · CHEETAH · TICK 257/468"`. Since a seek is a rewind and a
  re-step of up to 1 488 ticks × 120 solver passes in wasm32 (`replay_runtime.nim:164-169`), the most
  likely reading is that the smoke sampled the readout before the 100 % seek finished, not that the
  seek clamped. What would settle it: a `viewer_smoke.mjs` run that re-reads the readout after a
  bounded settle, or a `--soak` long enough to let the 100 % seek land.
- **Whether the hopper's `highY = 4.0 m` fall test (F5) is reachable** under any legal order. Nothing
  in the tree drives it; a targeted sweep of `bound` at `power 100` across seeds would settle it.
- **Whether `writeCogameUri` (bitworld) bounds its own wait.** It is the starter's dependency and is
  not in this tree; the POST path is explicitly bounded at 60 s (`server.nim:119`) but the PUT path
  goes through the library. Reading `bitworld/runtime` would settle it.
- **Actual per-morphology `trotter` distances** (F4). The band test only asserts means over 100
  release seeds and I could not run Nim in the sandbox. Running
  `nim r -d:release --path:src tests/test_cc_baselines.nim` and printing `dist[i]/n` would settle
  whether the hopper sits nearer 0.3 m or nearer 6 m.
