# r2 review — ecos

Head: `b4bb25e9bc78755b333de26f1eada3f959f3db77` — **unchanged since round 1** (`git fetch origin &&
git reset --hard origin/main` landed on the same sha the r1 verdict judged; `gh run list -R
Metta-AI/cogame-ecos --branch main -w ci.yml` shows run **32639042839** on that sha, `success`, as
the newest run — no commit and no CI run has landed on `main` since).
Range re-read: `289937c..b4bb25e` (the 21 r1 fix commits), plus a full re-trace of `decideAll` and
of every early-end path.
Files read: 26 (`src/ecos/{llm,scripted,events,sim,sim_types,sim_config,server,replays,broadcast,
global}.nim`, `src/ecos.nim`, `replay-viewer/ecos_replay.nim`, `client/replay_broadcast.html`
(clock/feed/end-card regions), `tests/{helpers,test_replay,test_broadcast,test_llm,test_feasibility,
test_baseline,test_sim,test_manifest}.nim`, `coworld_manifest_template.json`,
`docs/plans/2026-08-23-ecos-design.md`, `/root/.nimby/pkgs/curly/src/curly.nim`, `nim.cfg`,
`Dockerfile`, `runs/…/r1-{review,fixes,verdict}.md`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 2 and 8 are the ones in scope
for this delta review).
Design note: repo copy `docs/plans/2026-08-23-ecos-design.md`. I diffed it against the run copy
`runs/2026-08-23-ecos/design.md`: the only divergences are the three documented deviation blocks
(shipped-constants table, cert-fixture 6×60 + `minTurnSeconds: 0`, `frames.len == ticksPlayed + 1`).

**Delta review.** This is not a full re-trace; it confirms/refutes the two standing blocking
findings from the code at head, walks their neighbourhoods, and spot-checks the r1 fix commits for
regressions. Nothing was tested by execution — there is no Nim toolchain in this sandbox
(`command -v nim` is empty), so every dynamic claim below is labelled **inferred** or **untested**.

---

## Blocking

### F1 — **B1 confirmed.** A 429'd seat keeps the zero-value `Decision`: an unclamped `[0,0,0,0]` doctrine, recorded as `source:"llm"`

- Where: `src/ecos/llm.nim:449`, `:461-489`, `:478-484`, `:490-494`; `src/ecos/events.nim:22-26`;
  `src/ecos/server.nim:315-328`; `src/ecos/sim.nim:136-137`.
- Observed, step by step:
  1. `decideAll` allocates the result vector with `result = newSeq[Decision](seats.len)`
     (`llm.nim:449`). Every element is the zero-value `Decision`: `fields` is a
     `Doctrine = array[4, int]` → `[0, 0, 0, 0]`; `clamped = false`; `say`/`notes` empty;
     `latencyMs = 0`; `source` is the first `DoctrineSource` enum value, `dsLlm = "llm"`
     (`events.nim:22-23`).
  2. Seats that are *not* open are pre-filled at `llm.nim:454-460`. A seat that IS open is left at
     the zero value until the batch loop assigns it.
  3. In the batch loop, the success branch assigns `result[index] = decision` (`:477`). The
     `CatchableError` branch pushes the seat onto `stillOpen` (`:485-488`). The throttle branch is
     the exception:
     ```nim
     except EcosThrottleError as error:
       ## Not re-opened: this seat plays the steward doctrine for this
       ## generation and gets a fresh call in the NEXT generation's batch, …
       logLine("ecos llm: seat " & $slot & " " & error.msg & …)
     ```
     (`:478-484`) — it logs and does nothing else. No assignment to `result[index]`, no
     `stillOpen.add`.
  4. `open = stillOpen` (`:489`), so the throttled seat is not in `open`, and the terminal fallback
     loop `for index in open:` (`:490-494`) — the only place that writes
     `scriptedDecision(…, skSteward)` with `source = dsFallback` — never reaches it.
  5. `result[index]` therefore leaves `decideAll` as `Decision(fields: [0,0,0,0], clamped: false,
     source: dsLlm, latencyMs: 0)`.
  6. The server applies it unconditionally: `state.sim.applyDoctrine(species, decision.fields,
     decision.source, decision.clamped, …)` (`server.nim:327-328`), after logging
     `"… [0, 0, 0, 0] via llm"` (`server.nim:323-326`). `applyDoctrine` does not clamp — its own
     docstring says "Out-of-range values are already clamped by the caller" (`sim.nim:136-137`) —
     so `sim.doctrine[species] = [0,0,0,0]` and the recorded `doctrine` event carries
     `"source":"llm"`, `"clamped":false`.
- Legality: `DoctrineMin` is `[60,24,20,0]` / `[80,2,0,0]` / `[150,40,0,0]`
  (`sim_types.nim:118-122`). `[0,0,0,0]` is below the declared minimum on three of four fields for
  grass, two for grazers, two for predators. Nothing in the sim rejects it.
- Consequence in the sim (**inferred** from the rules, not executed): a zero doctrine is not merely
  out of range, it is lethal for whichever species draws it —
  *grass*: `seed_threshold 0` makes every tuft seed every tick, `seed_cost 0` births children with
  0 energy while the parent pays `SeedLoss = 10` per seed (`sim.nim:443-465`);
  *grazers*: `bite 0` makes `taken = min(0, …) <= 0 → continue`, i.e. no food income at all
  (`sim.nim:234-235`), while `birth_threshold 0` splits every body with energy > 20
  (`sim.nim:472-485`);
  *predators*: `rest_energy 0` makes `body.energy >= restEnergy` always true, so every predator
  idles and never hunts (`sim.nim:333-335`), and `hunt_range 0` gives `hunt2 = 0`.
  All three lead to extinction inside one to two generations, i.e. a 429 on any single seat most
  likely ends the episode with a `collapse_*` — from an unrecorded, unattributed cause.
- Checklist item: **8 — LLM reply handling** ("retries once on a parse or transport failure, then
  falls back to the scripted move — **and the fallback is recorded so phase 60 can count it**"). A
  429 is a transport failure; at head neither half happens. Same violation against the note's
  §Degrade, never hang: "Still failing → that seat plays the **`steward` scripted doctrine** for
  that generation … recorded on the `doctrine` event as `"source":"fallback"`".
- Why blocking: an out-of-range doctrine drives the sim and is recorded in the replay as an ordinary
  model decision, so phase 60 cannot count the miss, the feed shows no `auto` badge
  (`client/replay_broadcast.html:3505-3506` tags only `fallback`/`scripted`), and the episode's
  ending is attributed to a policy that never made that call.
- Why CI is green over it: `tests/test_llm.nim:88-101` asserts only that `decisionFrom` raises
  `EcosThrottleError`. There is no `decideAll`-level test with a stubbed 429 — `decideAll` needs a
  live `curly.Curly`, so every `decideAll` test in the file (`:139-164`) goes through the
  `client.disabled` short-circuit, which never enters the batch loop at all.
- (Judge's named fix, restated as context: assign
  `result[index] = scriptedDecision(sim, sim.roleOf[slot], skSteward)` with `source = dsFallback` in
  the throttle handler, plus a `decideAll`-level 429 test.)

### F2 — **B2 confirmed.** `precompute` never flushes the partial generation a mid-generation collapse scores, so the scorebug/end-card diverge from `results.scores` on every collapse replay

- Where: `src/ecos/replays.nim:183-194` (and `:159`, `:261`); `src/ecos/sim.nim:618-638`,
  `:547-573`, `:535-540`; `src/ecos/broadcast.nim:116-141`; `tests/test_replay.nim:133-158`;
  `tests/test_broadcast.nim:146-188`.
- Observed — sim side:
  ```nim
  if sim.atGenerationBoundary():
    sim.closeGeneration()
    …
  if collapsed:
    if not sim.atGenerationBoundary():
      sim.closeGeneration()
    …
    sim.finish("complete", "collapse_" & RoleNames[which])
  ```
  (`sim.nim:624-636`). On a collapse at a tick `T` with `T mod ticksPerGeneration != 0`,
  `closeGeneration` still runs, and it adds
  `min(genAccum/(ticksPerGeneration · R), 2.0)` to `sim.scores` (`:551-552`, via
  `generationScore` at `:535-540`) — partial credit for the interrupted window, against the FULL
  denominator. `results.scores` is `scoreVector()` over those `sim.scores` (`:542-545`, `:800-808`).
- Observed — viewer side:
  ```nim
      if tick > 0:
        accum[index] += bioRow[index + 1]
      if tick > 0 and tick mod perGeneration == 0:
        …
        score[index] += min(generation, GenerationScoreCap)
        accum[index] = 0
    player.scoreAt[tick] = score
  ```
  (`replays.nim:183-194`). The accumulator is flushed **only** at exact multiples of
  `perGeneration`. On a mid-generation collapse the last window's accumulation is dropped on the
  floor, so `player.scoreAt[lastTick][i] < results.scores` for every seat, each by its own partial
  term.
- Observed — what that reaches the screen: `chromeFrame` feeds the chrome from exactly that array —
  `input.scores[index] = player.scoreAt[tick][index]` (`replays.nim:261`) — and `buildStateJson`
  builds both the scorebug (`teams[*].score`, `broadcast.nim:53-64`) and the end-card
  (`over.teams[*].score`, plus `winner`/`draw` chosen by comparing `input.scores`,
  `broadcast.nim:116-141`) from it. `client/replay_broadcast.html:3869` prints
  `o.teams[team].score`; `:3896` prints the winner's score into the end-card sentence. The wasm
  bundle runs the same code (`replay-viewer/ecos_replay.nim:49`, `:38-40`), so this is what ships.
- The winner can flip, not just the digits: the dropped term is per-species
  (`genAccum[species] / (T · R_species)`), so it is different for each seat — a collapsing species
  contributes ≈0 while a healthy one contributes up to 2.0. `results.win[i] = (S_i == max(S))`
  (`sim.nim:808`) is computed from the sim's numbers; `over.winner` is computed from the viewer's
  (`broadcast.nim:125-133`). Two different orderings over three floats. **Inferred** (arithmetic),
  magnitude **untested**.
- Reachability: collapse is a designed ending — the note's §End conditions calls it "a *completed
  game of Ecos*", and `tests/test_feasibility.nim:121-149` gate (b) *requires* the greedy predator,
  the timid predator and the all-`opportunist` field each to fail to reach the last generation on
  ≥5 of 6 seeds. A collapse landing exactly on a generation boundary is the 1-in-60 case; the
  ordinary case is the broken one.
- Checklist item: **2 — Replay re-derivation** ("the viewer derives its display from that same
  re-derivation … A test asserts it"). The derivation exists but is arithmetically incomplete on
  the collapse path, and no test locks that path: `tests/test_replay.nim:133-158` asserts
  `scoreAt[lastTick] == results.scores` and end-card == `results.win` on a **full ten-generation
  steward episode** (`stewardEpisode(standardConfig(3))`, `:18`, whose ending is asserted to be
  `ten_generations` at `:76-78`), and `tests/test_broadcast.nim:146-188` — the only test that builds
  a collapsed episode — feeds `chromeOf(crashed, …)` from `sim.scores` **directly** (`:35`), never
  through `initReplayPlayer`. `grep initReplayPlayer tests/` returns only `test_replay.nim:123,134`.
- Why blocking: the artifact and the picture disagree on who won, on every collapse replay, in the
  shipped bundle, with no test standing over it.
- (Judge's named fix, restated as context: flush the residual accumulator at the final tick when the
  episode ended mid-generation, and extend the score-lock block to a collapse episode — the
  `fixedPicker` greedy predator at `test_broadcast.nim:148-156` already builds one deterministically.)

---

## Non-blocking

### F3 — the collapse replay carries the sim's true scores in its own `end` and `generation` events, and the viewer reads neither

- Where: `src/ecos/sim.nim:566-573` (`ekGeneration` carries `score[3]`), `:581-583` (`ekEnd` carries
  `scoreVector()`); `client/replay_broadcast.html:3476-3479`, `:3536-3546`.
- Observed: `finish()` stamps the `end` event with `sim.scoreVector()` — i.e. the post-
  `closeGeneration` scores, including the partial generation. The viewer's `onEnd` reads only
  `e.ending`/`e.reason` to push a feed row, and `case 'generation':` is an explicit no-op
  (`:3478`). So a mid-generation-collapse replay contains both numbers, and the one it displays is
  the wrong one. This is not itself a checklist violation — item 2 requires the display to come
  from the re-derivation rather than from a parallel recording, which is what the code does — but
  it is the cheapest available oracle for F2 and a second internal inconsistency in the same file.

### F4 — `results.generations` counts a partially played generation as completed

- Where: `src/ecos/sim.nim:565` (`inc sim.generationsPlayed` inside `closeGeneration`), `:821`
  (`"generations": sim.generationsPlayed`), `:628-630` (the mid-generation `closeGeneration`).
- Observed: on a collapse at tick 137 of a 60-tick generation, `closeGeneration` runs and
  `generationsPlayed` becomes 3, so `results.generations == 3` where two generations completed.
  The note's §`results.json` defines `generations` = "generations completed". Same value reaches
  the player `final` frame (`server.nim:195`).
- This is the sim half of r1's advisory F18, re-verified at head. No checklist item names
  `results.generations`, so it is advisory; it is listed because any fix to F2 has to decide the
  same question (what a partial window is worth) and should decide it once.

### F5 — a seat that never connected is recorded `source:"scripted"`, not `"fallback"`

- Where: `src/ecos/server.nim:307-309` (the F11 fix), `src/ecos/llm.nim:436`.
- Observed: the per-generation snapshot rewrites `kinds[slot] = skSteward` for any slot absent from
  `playerSockets`. In `decideAll` that seat is then pre-filled by `scriptedDecision(sim, role,
  skSteward)`, whose source is `(if kind == skNone: dsFallback else: dsScripted)` → `dsScripted`.
  So the replay cannot distinguish "an LLM policy whose pod never connected" from "a seat that
  declared `PLAYER_SCRIPTED=steward`", and phase 60's fallback count does not see it. The note's
  §Degrade only prescribes `"fallback"` for the retry-exhausted path, and checklist item 8 is
  scoped to reply handling, so this is advisory. (Before F11 the same seat burned two model calls
  and then recorded `fallback`; the fix is a net improvement, this is its one side effect.)

### F6 — `seats` is hard-coded `@[0, 1, 2]` while `prompts`/`scripted` are sized from `config.players.len`

- Where: `src/ecos/server.nim:290`, `:307`, `:495-496`; `src/ecos/llm.nim:398-400`, `:454-457`;
  `src/ecos.nim:45-48`; `src/ecos/sim_config.nim:71-73`.
- Observed: `state.prompts`/`state.scripted` are `newSeq(config.players.len)`. `ecos.nim` pads
  `players` up to `tokens.len` and only defaults `tokens` to three entries when the platform sends
  none, and `validate()` checks `numAgents == 3` — which is a *separate* field from `tokens.len`,
  never cross-checked. A config carrying two tokens therefore passes `validate()` and
  `runGameServer`'s `tokens.len != players.len` guard, and then `openSeatsOf`'s
  `scriptedKinds[slot]` indexes slot 2 of a two-element seq on the first generation. The binary is
  built `-d:release` (`Dockerfile:44`), which keeps index checks on, so this is an `IndexDefect` on
  the game thread → **inferred**: no artifacts are ever written and the episode hangs to the
  platform timeout.
- Not filed as blocking: I could not construct a path where the platform delivers `tokens.len != 3`
  — `num_agents: 3` is in all three manifest variants and `tools/ci/docker_smoke.sh` refuses to
  start otherwise (checklist item 6). Reported so the reachability question is on the record rather
  than assumed away. Pre-existing; not introduced by any r1 commit.

### F7 — a collapse replay's clock caption counts against the collapse tick, not the configured episode

- Where: `src/ecos/replays.nim:236` (`maxTick: player.lastTick`), `src/ecos/broadcast.nim:88`
  (`"mx"`), `client/replay_broadcast.html:2330`, `:2340`.
- Observed: `renderEcosClock` computes `lastTick = (s.mx != null ? s.mx : gens * tpg)` and prints
  `tick <t> of <lastTick>`. On the replay path `mx` is `frames.len - 1`, so a collapse at tick 137
  of a 600-tick episode reads `tick 42 of 137`. The note's §Viewer specifies the caption
  `tick 214 of 600`, i.e. against the configured length; the live path does send the configured
  length (`server.nim:94`). Cosmetic, replay-only, and defensible as a scrubber extent — recorded
  because it is one more place where the collapse replay under-reports the episode. No checklist
  item.

### F8 — F19's birth hairline consumes up to three fx slots per birth from the same 400-object pool

- Where: `src/ecos/global.nim:380-405`, `:50` (`MaxFxObjects = 400`).
- Observed: each `fkSparkle` now emits its own object plus up to two link objects, each taking a
  slot from `fxSlot`. Both the outer (`:382`) and the inner (`:398`) loops check
  `fxSlot >= MaxFxObjects`, and ids stay in `3000..3399` clear of `WashObjectBase = 1400` — so the
  pool is bounded and cannot collide. The effect is that on a heavy birth tick the pool saturates
  ~3× sooner and later fx items (fades, splashes) are dropped. Cosmetic; no checklist item.

---

## Traced and consistent

**Every other exception/branch through `decideAll` (F1's neighbourhood).**

- `llm.nim:339-343` **401/403** — `textOf` sets `client.disabled = true` and raises `EcosError`,
  caught at `:485-488` → `stillOpen`. On the next `for attempt` iteration `if open.len == 0 or
  client.disabled: break` (`:462`) fires, and the terminal loop `:490-494` gives every one of those
  seats `scriptedDecision(…, skSteward)` with `source = dsFallback`. In every *later* generation
  `openSeatsOf` returns an empty list (`:399`, `not client.disabled` is false), so all three seats
  take the pre-fill branch at `:454-460`, where an `skNone` seat is explicitly re-stamped
  `dsFallback` (`:459-460`). Matches the note ("401/403 disables the client for the rest of the
  episode … all seats scripted from then on") and item 8's recording requirement.
- **Transport error / timeout** — `curly` reports it as a non-empty `error` string;
  `textOf:337-338` raises `EcosError` → `stillOpen` → retried once → terminal fallback.
  `makeRequests(batch, client.timeoutSeconds)` is bounded by `llmTimeoutSeconds = 25`
  (`llm.nim:466`, `sim_config.nim:49`).
- **Non-2xx other than 401/403/429** (`:347-349`), **refusal** (`:351-352`), **`max_tokens` before
  any `{`** (`:356-358`), **no JSON object** (`extractJsonObject:289-297`), **missing/non-numeric
  doctrine field** (`numberOf:360-376`) — all raise plain `EcosError` → `stillOpen` → one retry →
  `dsFallback`. Out-of-range but numeric replies are clamped and flagged, not failed
  (`parseDecision:391-393`, `clampDoctrine` in `sim_types.nim:144-153`).
- **Retry-exactly-once**: `for attempt in 0 .. 1` (`:461`); the hint is appended only when
  `attempt > 0` (`requestBatchFor:416-419`); a successful retry is stamped `dsRetry` (`:475`).
  Asserted at `test_llm.nim:134-137`.
- **Batch/response alignment**: `requestBatchFor` walks `for index in open` and `decideAll` walks
  `for position, index in open` (`:413`, `:469`), and `curly.makeRequests` documents "The return
  value seq is in the same order as the request batch"
  (`/root/.nimby/pkgs/curly/src/curly.nim:711-718`), so `responses[position]` and
  `batch[position]` are the same seat. `makeRequests` is declared `{.raises: [], gcsafe.}`, so the
  two statements outside the `try` (`:464`, `:466`) cannot throw past `decideAll`'s "never raises"
  contract.
- **One batch per generation**: a single `RequestBatch` carrying every open seat, per attempt
  (`:464-466`); asserted at `test_llm.nim:117-137`. No sequential per-seat call anywhere.
- **Disabled client / no credentials**: `openSeatsOf` returns `@[]`, the attempt loop breaks
  immediately, all three seats are pre-filled scripted, `skNone` → `dsFallback`
  (`test_llm.nim:139-164` asserts exactly this).

**Every early-end path (F2's neighbourhood).**

- **Collapse exactly on a generation boundary** — `atGenerationBoundary()` is true, so
  `closeGeneration` runs once at `sim.nim:624-625` and the `if collapsed` block does **not** call it
  again (`:629`). The viewer flushes at that same tick (`replays.nim:185`). Sim and viewer agree.
  Also confirmed the generation counter is not advanced on a collapse (`:626`).
- **Deadline between generations** — `server.nim:294-300` calls `endEarly()` only from the top of
  the loop, which is reached only after `runGeneration()` has run to a boundary or the sim is
  `done`; `endEarly → finish("deadline","deadline")` (`sim.nim:585-588`) adds no score and closes no
  generation, and `genAccum` was zeroed by the last `closeGeneration` (`:559`). `frames.len - 1` is
  then an exact multiple of `ticksPerGeneration`, so `precompute`'s last flush lands on the last
  tick. Sim, viewer and end-card agree; the end-card takes the `DEADLINE` branch
  (`replay_broadcast.html:3682`, `:3903-3906`).
- **Forfeit** — `sim.forfeit()` zeroes all three scores and finishes (`sim.nim:590-595`); only frame
  0 exists, so `precompute` runs one iteration with `tick == 0` (no accumulation, no flush) and
  `scoreAt[0] == [0,0,0]`, matching `results.scores == [0,0,0]`. `results.win` is all `true`
  (`0.0 == best`, `:808`) and the card reports `draw` (`broadcast.nim:131-133`) — consistent.
  `meanBiomass` divides by `max(1, sim.tick)` (`:784-786`), so no division by zero.
- **`finishEpisode`'s defensive `endEarly`** (`server.nim:174-175`) is unreachable in practice: the
  loop only breaks at `state.sim.done` (`:292-293`) or immediately after its own `endEarly`
  (`:298-300`).
- **`series`/`generation`/`end` rows on a collapse tick T**: predation/starve/birth rows are emitted
  pre-increment as `sim.tick + 1 == T` (`:351-357`, `:404-409`, `:423-431`), `alarm` post-increment
  as `sim.tick == T` (`:497-499`), then `collapse@T` (`:621-622`), `generation@T` (`:566-573`),
  `end@T` (`:581-583`). All equal, so `events[]` stays non-decreasing in `t` —
  which is what `replays.nim:195-202`'s forward cursor and `server.nim:83-87`'s backward walk both
  require. Asserted at `test_replay.nim:55-58` and `test_broadcast.nim:165-167`.
- **The event cursor reaches the final tick's rows**: `eventStart` is sized `ticks + 2` and filled
  for `0 .. ticks` plus `[ticks+1]` (`replays.nim:195-202`); `eventsIn(_, lastTick)` clamps
  `hi = lastTick + 1`, which indexes the entry holding `events.len`. The collapse/generation/end
  rows on the last tick are therefore in the last frame's slice.

**F4 (alarm stamping) × the final tick of a collapse** — the specific interaction the brief asked
about. `checkAlarms` is called after `inc sim.tick` and before `recordFrame` (`sim.nim:614-616`), so
the population it reports is the same one the frame at tick `T` records; the r1 test asserting
`event.population == seriesPop[event.tick][…]` (`test_broadcast.nim:176-180`) is checking exactly
that. Under the old `sim.tick + 1` stamp an alarm on the last tick of the episode would have
recorded `ticksPlayed + 1` — out of range for the viewer's cursor and for
`test_replay.nim:50-51`. At head that cannot happen: `checkAlarms` cannot produce a tick greater
than `sim.tick`, and `sim.tick` is the last frame index. No regression; the fix is load-bearing for
the collapse path specifically.

**F1 (generation window) × F2** — the `if sim.tick > 0` guard (`sim.nim:528-530`) aligned the sim's
*intra*-generation window with `precompute`'s `if tick > 0` (`replays.nim:183`); what it did not
align is the *final partial* window, because the flush condition at `replays.nim:185` was left
alone. That is precisely the seam F2 sits in. F17 subsequently moved `biomassSum` inside the same
guard (`:530`), which is correct against `meanBiomass`'s `div sim.tick` (`:784-786`) and is
asserted at `test_replay.nim:83-91`.

**Other r1 fix commits, re-read at head for collateral damage** (I read every source hunk in
`289937c..b4bb25e`):

- `11cbcbc` (F20) — `GameState.trackers`, `shuttingDown` and `SimServer.says` are absent from head;
  `grep` finds no remaining reader of any of the three.
- `3fa2c1e` (F24) — the `withLead` parameter is gone from `chromeInputOf`/`sendBoard`; the live path
  never sets `leadPts`, the recorded path still does (`replays.nim:278-288`). Replay-side untouched,
  which is the path items 3/11/13 exercise.
- `1d5eb84` (F15) — `scriptedDecision` now carries the baseline's real `clamped` flag
  (`llm.nim:430-437`). Side effect, benign: a fallback doctrine that the steward's "recruit when
  thin" correction pushed out of range is now recorded `clamped: true` and gets a `clamped` badge
  next to its `auto` badge in the feed (`replay_broadcast.html:3505-3507`) — which is accurate.
  The one deleted assertion (`doAssert not event.clamped`) was checking a literal the test itself
  passed in; the replacement (`stewardClamps > 0` plus the retained per-field range checks,
  `test_baseline.nim:40-80`) is strictly stronger. Not a loosened test.
- `481879c` (F11) — see F5 above; the snapshot is rebuilt every generation, so a late-arriving
  socket rejoins.
- `b413a4c` (F26) — `generationReserve = 2·llmTimeoutSeconds + minTurnSeconds` is subtracted at the
  between-generations check (`server.nim:278-279`, `:294`). Held back exactly once, on the check
  only; does not shorten `runGeneration`.
- `86ff481` (F13), `25d1ace` (F14), `07d3c42` (F2) — prompt/observation content only; `rulesJson` is
  total over `Species` (`sim.nim:701-741`) so no role can fall through.
- `91dc55e`/`cbfc377` (F7/F6) — the `variant` schema property is `enum ["standard","harsh-spring"]`
  with `default "standard"`; `configJson` already wrote the field (`sim_config.nim:166`), so no
  replay-schema change. The manifest↔`harshSpringConfig` lock (`test_manifest.nim:159-179`) adds
  assertions only.
- `9f316b4` (F9) — `summarise`'s new per-generation mean loop divides by `hi - lo + 1`, the ticks
  actually in the window (`test_feasibility.nim:63-76`), so it handles a partial final generation
  *correctly* — a third place in the tree that meets the partial-window question, and the only one
  that answers it the same way twice.
- `b4bb25e` (F8) — the clock caption and end-card chip take the count from `s.gens`
  (`replay_broadcast.html:2334`, `:3686-3688`), which is `config.generations`. They print a count
  only on the `ten_generations` branch, where played == configured; the `collapse_*`, `deadline` and
  `forfeit` branches print no count. No new mis-statement.
- `6c3f738` (F19) — see F8 above; bounded.
- `298ed99`/`5e508cc` (F16/F17) — test additions and the `biomassSum` guard, both re-read.

**Anything new on `main`** — nothing. Head is the same sha the r1 verdict judged, `git status` is
clean after the reset, and the newest `ci.yml` run on `main` is still 32639042839 (success) on that
sha.

---

## Could not determine

- **The numeric magnitude of F2's divergence, and whether a winner actually flips on a shipped
  seed.** There is no Nim toolchain in this sandbox (`command -v nim` empty; the repo builds against
  `/root/.nimby/pkgs`, which is present, but no compiler), so I could not run
  `tests/test_feasibility.nim` or build a collapse replay. What would settle it: run the greedy-
  predator `fixedPicker` fixture from `test_broadcast.nim:148-156`, then print
  `initReplayPlayer(parseReplayBytes(replayBytes(sim, results))).scoreAt[lastTick]` beside
  `results{"scores"}` and `results{"win"}` for each seed. The structural divergence itself is
  observed, not inferred — the flush at `replays.nim:185` is simply never taken when
  `ticksPlayed mod ticksPerGeneration != 0`.
- **F1's downstream sim behaviour** is traced from rules 1/3/5/9 but not executed; the claim I stand
  behind without running anything is the recorded one (an out-of-range doctrine installed and
  recorded as `"llm"`), not the ecological prediction.
- **F6's reachability** — whether the platform can ever hand this game a `tokens`/`players` array of
  length ≠ 3. Settled by the coworld runner's config contract, which is not in this tree.
- **Item 1's "no test loosened" for round 2** — no test file changed since `b4bb25e`, so there is
  nothing new to read; the round-1 hunks were audited above (F15) and by the r1 verdict.
