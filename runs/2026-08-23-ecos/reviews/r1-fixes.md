# r1 fixes — ecos

Head: `b4bb25e9bc78755b333de26f1eada3f959f3db77` (== `origin/main`)
CI: https://github.com/Metta-AI/cogame-ecos/actions/runs/32639042839 — **success**
(jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; `gh run view 32639042839` on head sha
`b4bb25e9`, not `-L 1`). No test was deleted, skipped, widened or made non-blocking in any
commit below; three commits ADD assertions and two replace a vacuous assertion with a true one.

Findings: **21 fixed, 0 refuted, 7 answered without a code change** (6 advisory where the code is
already right, 1 `NEEDS-DESIGN` with the measurement that says so). Every finding the reviewer
filed was factually reproducible at `289937c`; nothing in the review was wrong.

`git push` over HTTPS is rejected sandbox-wide ("No anonymous write access"), so every commit was
pushed through the Git Data API (blobs → tree → commit → PATCH ref), one API push per commit, and
the local clone realigned with `git fetch` + `git reset --mixed` after each. No force-push, no
rewritten history.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | fixed | `e78a513` | `src/ecos/sim.nim:523`, `tests/test_replay.nim` |
| F2 | fixed | `07d3c42` | `src/ecos/llm.nim:163`, `tests/test_llm.nim` |
| F3 | fixed (docs) | `123c73d` | `docs/plans/2026-08-23-ecos-design.md` §The game |
| F4 | fixed | `3baac0e` | `src/ecos/sim.nim:498`, `tests/test_broadcast.nim`, `tests/test_replay.nim` |
| F5 | fixed (docs) | `886d079` | `docs/plans/2026-08-23-ecos-design.md` §Packaging |
| F6 | fixed | `cbfc377` | `tests/test_manifest.nim` |
| F7 | fixed | `91dc55e` | `coworld_manifest_template.json`, `tests/test_manifest.nim` |
| F8 | fixed | `b4bb25e` | `client/replay_broadcast.html:2334,3675,3850,3881,3904` |
| F9 | fixed (part) | `9f316b4` | `tests/test_feasibility.nim` |
| F10 | fixed (docs) | `a0ed439` | `docs/plans/2026-08-23-ecos-design.md` §Tests item 4 |
| F11 | fixed | `481879c` | `src/ecos/server.nim:298` |
| F12 | advisory — no change | — | `src/ecos/sim.nim:141` |
| F13 | fixed | `86ff481` | `src/ecos/sim.nim` (`rulesJson`), `tests/test_sim.nim` |
| F14 | fixed | `25d1ace` | `src/ecos/llm.nim:198-213` |
| F15 | fixed | `1d5eb84` | `src/ecos/scripted.nim`, `src/ecos/llm.nim:422`, `tests/test_baseline.nim` |
| F16 | fixed | `298ed99` | `tests/test_replay.nim` |
| F17 | fixed | `5e508cc` | `src/ecos/sim.nim:524`, `tests/test_replay.nim` |
| F18 | advisory — no change | — | `src/ecos/sim.nim:622-630` |
| F19 | fixed | `6c3f738` | `src/ecos/global.nim:388`, `client/replay_broadcast.html:3525` |
| F20 | fixed | `11cbcbc` | `src/ecos/server.nim:42,50,225`, `src/ecos/sim.nim:39,140` |
| F21 | advisory — no change | — | `tools/ci/docker_smoke.sh` |
| F22 | advisory — no change | — | `client/replay_broadcast.html:1351` |
| F23 | NEEDS-DESIGN (measured, not changed) | — | `src/ecos/sim.nim:220,275` |
| F24 | fixed | `3fa2c1e` | `src/ecos/server.nim:91-145,406` |
| F25 | fixed | `481cc50` | `src/ecos/llm.nim:336`, `tests/test_llm.nim` |
| F26 | fixed | `b413a4c` | `src/ecos/server.nim:278-294` |
| F27 | advisory — no change | — | `tools/ci/viewer_smoke.mjs:286` |
| F28 | advisory — no change | — | `coworld_manifest_template.json` fixtures |

**Design-note divergence created by this round.** Three commits edit the repo's copy
(`docs/plans/2026-08-23-ecos-design.md`); the run-directory copy
(`runs/2026-08-23-ecos/design.md`) is the coordinator's and was **not** touched, so the two are no
longer byte-identical. The three edits are F3 (a "shipped constants" table recording the four
gate-moved constants with the measurement), F5 (why the certification fixture is 6 × 60 with
`minTurnSeconds: 0`) and F10 (§Tests item 4's `frames.len == ticksPlayed` corrected to
`ticksPlayed + 1`, which the note's own replay schema already implied). F7 additionally adds a
config-schema property the note's §Packaging property list does not name — see F7 below.

---

## F1 — one generation window, sim and viewer

**Before:** `newSim` calls `recordFrame()` at `sim.nim:123` before any tick runs, and
`recordFrame` accumulated `genAccum[species] += bio`, so generation 1 carried 61 samples
(`B(0)…B(60)`) and every later generation 60. The viewer's `precompute` guards with
`if tick > 0` (`replays.nim:183`) and carried 60. `results.scores`/`results.win` came from the sim
window; the scorebug, the end-card score and the end-card WINNER came from the viewer's. They
disagreed by 0.012–0.017 on the CI replay.

**Now:** the canonical window is the note's — `G_i(g) = (Σ B_i(t) over generation g) / (60 · R_i)`
with generation 1 = ticks 1..60. Frame 0 is the opening state, not a tick: it is recorded and
drawn but never scored. `recordFrame` accumulates `genAccum` only when `sim.tick > 0`, so the sim,
the replay's `series.bio`, the viewer's re-derivation and `results` compute the same number.

**Evidence:** `tests/test_replay.nim` now asserts, for every slot, that the viewer's re-derived
`scoreAt[lastTick]` equals `results.scores[slot]` exactly, and that the end-card the viewer draws
carries those same three scores and crowns the seat `results.win` crowns. Reverting only
`src/ecos/sim.nim` makes it fail with `slot 0: the viewer re-derives 9.874160 where results.json
carries 9.886160`. **Checklist item 2** (the viewer's display comes from the same re-derivation as
the artifact).

## F2 — the predator prompt quotes the sim's kill formula

**Before:** `kernelText(spPredators)` said `min(180, 60 + the grazer's energy)`; the sim pays
`min(KillCap, KillBase + prey.energy)` with `KillBase = 90`. Every predator seat was told a payoff
a third smaller than the one it gets, and the manifest's `rules.md` page already said 90.

**Now:** the sentence is composed from `$KillCap` and `$KillBase`, so the prompt cannot drift from
the constant again. `tests/test_llm.nim` asserts the system prompt contains
`min(<KillCap>, <KillBase> + the grazer's energy)`.

**Evidence:** test_llm green; a hand-edit of `KillBase` moves prompt, manifest text and assertion
together. No checklist item names prompt fidelity; this is the design note's §Decisions ("the full
rule set for that role"), and it bears on **item 8**'s decision path being honest about what it is
asking for.

## F3 — the four constant deviations, recorded with the measurement

Not a code change: the note makes `tests/test_feasibility.nim` the enforcement for any constant in
§The game, and that test is green. What was missing is any statement in the tree of WHICH values
moved and why. Measured here and written into the repo's note copy:

- `killBase = 60` (the note's value): gate (a) fails — **11/12** seeds, predators reach 0 on one.
- steward defaults restored to the note's `herd 40 / rest_energy 240 / birth_threshold 320`:
  gate (a) fails **0/12** — the grazers crash.

Both reproduced by restoring the value in `sim_types.nim` and running
`nim r -d:release tests/test_feasibility.nim`. The reviewer's sub-point — that
`tests/test_sim.nim:95` pins the kill formula in terms of `KillBase` rather than the literal 60 —
stands, and is why `KillBase` is not unguarded: the 11/12 measurement above is `test_feasibility`
catching exactly that change. **Checklist items 1 and 7.**

## F4 — the alarm event stamps the tick it describes

**Before:** `step()` does `inc sim.tick` and then `checkAlarms()`, which emitted `tick: sim.tick + 1`
— the stamp the pre-increment emitters use. A tick T that alarmed produced
`[…birth@T, alarm@T+1, collapse@T, generation@T, end@T]`, so `events[]` was not sorted by `t`:
`replays.nim:197-202`'s forward cursor pushed the collapse row and the generation banner into the
next tick's slice, `server.nim:85-89`'s backward walk could stop early, and an alarm on the FINAL
tick would record `ticksPlayed + 1` and fail `tests/test_replay.nim:49`.

**Now:** `checkAlarms` stamps `sim.tick`, the frame whose population crossed.

**Evidence:** `tests/test_broadcast.nim` runs the greedy-predator fixture that really does alarm
and asserts (a) every alarm's recorded population equals the population that frame recorded in
`seriesPop`, and (b) `events[]` is non-decreasing in `t`; `tests/test_replay.nim` asserts the same
ordering over a whole steward episode. Reverting only `sim.nim` fails with `the alarm at tick 244
reports 20 where that frame recorded 19`. This is the path the reviewer noted has never executed
in CI — it now executes in `test_broadcast`, in both debug and release. **Checklist item 2.**

## F5 — the certification fixture's deviation is now authorised in writing

The fixture ships `{generations: 6, ticksPerGeneration: 60, minTurnSeconds: 0}` against the note's
`{generations: 3, ticksPerGeneration: 30}`. I did not shorten it back: the note's own value breaks
CI. `ci.yml`'s `wasm-viewer` job runs `tools/ci/viewer_smoke.mjs --soak 10` against **this
episode's** replay, and the soak requires the LAST 2 s interval to advance
(`viewer_smoke.mjs:392-418`). `3 × 30 = 90` ticks is 3.75 s of video at 24 fps and the viewer holds
on its final frame (looping is off by design, `global.nim:94-104`), so a finished viewer is
reported `frozen: playback stopped advancing`. `6 × 60 = 360` ticks is 15 s — the green run's log
reads `soak: 10s of playback kept advancing ("0 / 360" -> "193 / 360" -> "241 / 360")`.
`minTurnSeconds: 0` removes a floor that exists only for the sidecar's request ceiling, and the
offline fixture issues no LLM requests at all.

Both facts, with that reasoning, are now in the repo's note copy under §Packaging → `certification`.
**Checklist items 6, 12 and 13.**

## F6 — the shipped harsh-spring block is tied to the config gate (a) runs

`tests/helpers.nim`'s `harshSpringConfig` hand-copied the variant's knobs and nothing compared it
with the manifest block the platform ships, so an edit to either alone would have shipped a variant
the ecological oracle never gated. `tests/test_manifest.nim` now compares the two field by field
(`initGrass`, `initGrazers`, `initPredators`, `grassGain`, `generations`, `ticksPerGeneration`,
the three caps). Verified by flipping `initGrass` back to 120 in the manifest: the test fails
naming both values. The variant's *content* (both repair steps spent) is faithful to the note's own
repair rule and is left alone. **Checklist items 6 and 7.**

## F7 — `variant` is a declared config property

`config.update` accepted `variant` and `configJson` wrote it into every replay — the note's replay
schema shows `"variant":"standard"` in `config` — but `game.config_schema` declared no such
property and is `additionalProperties: false`, so the platform could never set it and every hosted
replay, harsh-spring included, recorded `"standard"`. The schema now declares `variant`
(string, `enum ["standard","harsh-spring"]`, default `"standard"`) and the harsh-spring block sets
it. `tests/test_manifest.nim` asserts each variant id is in the enum, that a non-standard variant
records its own id, and that `config.update` → `configJson` carries it through.

Deviation: the note's §Packaging property list does not name `variant`; its replay schema does.
Recorded here rather than in the note. `fieldW`/`fieldH` are in the same position (accepted by
`config.update`, absent from the schema) and were left alone — they are internal knobs no fixture
sets and the note lists neither. **Checklist item 10.**

## F8 — the end-card says how many generations were played

`results.ending` stays the literal `"ten_generations"`: it is what the note prescribes, what
`finish()` writes, and what conclusion (a) of §Feasibility check requires certification and every
all-filler league episode to report. What was wrong is the CHROME reading it out verbatim — CI's
viewer smoke printed `GEN 6 / 6 TEN GENERATIONS` for a six-generation fixture. The clock caption,
the end-card condition chip and the two end-card sentences now take the count from the chrome
frame's `gens`, which the viewer already carries. The green run's smoke now reads
`100%="GEN 6 / 6 6 GENERATIONS"`. **Checklist items 11 and 13** (legibility of what the spectator
is shown).

## F9 — gate (a) measures the per-generation MEAN populations the note names

The note states gate (a)'s bounds over "per-generation mean populations"; the test measured
`row.pop`, the population at each generation CLOSE, which cannot see a dip that recovers by the
boundary. `summarise` now also computes each generation's mean population per species from
`seriesPop` over ticks `(g-1)·T+1 .. g·T` (the scoring window) and gate (a) asserts the note's
bounds over those means as well as over the close rows. Measured on the shipped baselines:
standard/steward means grass 151..220, grazers 67..140, predators 3..11; harsh/steward grass
150..220, grazers 15..140, predators 2..11 — inside `60..220 / 10..140 / 1..30`.

The two other halves of F9 are answered, not changed: (a) the substituted greedy-grazer clause is
licensed by the note's own "that test is the enforcement, not this table" and is documented in the
test's header, which is exactly the form the note asks for; (b) the added all-`opportunist` clause
is new material that does sit against the note's "every all-filler league episode terminates
`ten_generations`". Making three seated opportunists sustainable is a constant retune — a design
change, not a fix — so it is left for the judge. **Checklist item 7.**

## F10 — §Tests item 4 no longer contradicts the replay schema

The note's replay schema opens `"frames":[{"t":0, …}]` while §Tests item 4 wrote
`frames.len == ticksPlayed`. The writer, the reader and the test all implement the schema (361
frames for 360 ticks on the CI artifact). The repo's note copy now states `ticksPlayed + 1` and
says which reading is authoritative. Documentation only. **Checklist item 2.**

## F11 — a seat that never connected plays steward

`runGame` asked for all three seats every generation; `openSeatsOf` opens any slot with
`scriptedKinds[slot] == skNone`, and a socket that never connected left the slot `skNone` with an
empty prompt, so with credentials present the game issued a real model request for an empty seat
and only fell back after failing twice. The note says missing seats play `steward`. The
per-generation snapshot now marks any slot absent from `playerSockets` as `skSteward`; a seat whose
socket arrives later rejoins the next batch, because the snapshot is rebuilt each turn. Behaviour
for connected seats — including `ecos-player` with no credentials, which CI records as
`source: "fallback"` — is unchanged, and the green `docker-smoke` shows it. **Checklist item 5.**

## F12 — advisory, no change: an empty `notes` keeps the seat's last notes

`sim.nim:141`'s `if notes.len > 0` is not an oversight. Every scripted and fallback decision
carries `notes: ""` (`llm.nim:422-427`), so overwriting unconditionally would erase an LLM seat's
memory on any transient failure — the seat would come back next generation with no notes at all,
which is strictly worse than seeing its own last ones. The note gives no rule for an empty value
(the reviewer says so too). Code left as is.

## F18 — advisory, no change: a collapse counts the partial generation

`closeGeneration()` on a mid-generation collapse scores the partial accumulator against the full
`ticksPerGeneration · R` denominator (partial credit) and counts the generation. The note says
`generations` = generations completed and says nothing about a partial one; the reviewer recorded
it "as observed, not as a defect". Changing either half moves a scoring rule the note does not
pin — that is a design decision, not a fix.

## F21 — advisory, no change: `docker_smoke.sh` is the builder's template

The file is byte-identical to `coworld-builder/templates/tools/ci/docker_smoke.sh` after the three
documented substitutions, which is what the note's §Packaging asks for. §Tests item 8 describes
two things the template does not do (`docker inspect` on the player containers, validating
`results.json` against `game.results_schema`). Editing the script to match would break the
verbatim-template property the reviewer verified and that §Packaging requires; the two note clauses
point in different directions and, as the reviewer says, a ruling settles it, not a code change.
The player-side half of raid item 3 is handled in the game (`src/ecos_player.nim:53-89` wraps the
receive loop and `quit(0)`s).

## F22 — advisory, no change: `#lockerroom { pointer-events: none }`

A deliberate, commented departure from verbatim chrome in service of checklist item 13's smoke
(the loading curtain otherwise swallows the 50 % seek click). The reviewer recorded it without
criticism. Left as is.

## F23 — NEEDS-DESIGN: rule 4's food target snapshot

The reviewer's reading is defensible (the note states the `>= 4 · bite` test under rule 4, and
"all reads inside a step use the state as it stood at the start of that step"), so I implemented
it — `moveGrazers` re-selecting the nearest tuft with `energy >= 4 · bite` on post-grazing energies
— and measured it before deciding. All tests still pass, but the ecology moves away from the
note's measured §Feasibility table:

| all-steward, 12 seeds | shipped | with rule 4 re-sensing |
|---|---|---|
| grass score | 8.73 | **6.92** (note's measured band: 7.5–12.5) |
| grazer score | 11.25 | **12.32** (band 5.7–10.6) |
| predator score | 5.48 | 5.51 |
| lowest grass generation-mean population | 151 | **90** (bound 60) |

That is a re-tuning of the ecology on an ambiguous reading of one sentence, with no defect
demonstrated either way (determinism is unaffected; the reviewer calls it an inference). I reverted
it and left the code alone. If the judge reads the note strictly, the change is one commit plus a
re-measure of §Feasibility's table — a design decision, not a fix.

## F13 — a seat sees its own constants

The `rules` block carried the GRAZER kernel for all three roles: a grass seat was told
`speed: 6, biteRadius: 16` and a predator a flee speed it can never use, where the note says the
seat sees "its own constants". `rulesJson(species)` now emits the role's own numbers, read from the
constants the sim runs on (grass: gain, shade radius, metabolism, seed loss, ceiling; grazers:
their two metabolisms, three speeds, bite radius, conversion, crowd radius, split overhead,
ceiling; predators: idle/chase/roam costs, both speeds, kill radius, kill base and cap, hunt
cooldown, crowd radius, split overhead, ceiling). `tests/test_sim.nim` asserts each role's frame
carries its own table and none of another role's. The manifest's protocol page documents `rules`
as `{...}` and needed no change. Design note §Decisions.

## F14 — the history table names its columns honestly

Header was `… | births | starved | eaten | your score` while every row carried all three species
in each of those columns. All three species' per-generation numbers are on the note's *visible*
list, so the honest fix is the label: `births g,h,p | starved g,h,p | eaten | scores g,h,p`. The
two dead lines (`let mine = ord(sim.roleOf[0])`, `discard mine`) are gone. Design note §Prompts.

## F15 — the scripted `clamped` flag is real

`correct()` discarded the clamp flag and `scriptedDecision` never set `clamped`, so
`event.clamped` on every scripted/fallback doctrine was `false` by construction — and
`tests/test_baseline.nim:68`'s `doAssert not event.clamped` was checking a literal the test itself
had passed to `applyDoctrine`. The claim was also false: on the standard opening the steward's
"recruit when thin" takes the grazer `birth_threshold` from 90 to 70, which the range minimum of 80
clamps back up (the CI replay's generation-1 grazer doctrine reads `birth_threshold: 80`).

`scriptedDoctrineChecked` now returns the flag, `scriptedDecision` records it, the test feeds the
baseline's OWN flag into the event, and the vacuous assertion is replaced by two true ones: every
recorded doctrine field is in range (unchanged, `checkDoctrine`), and the steward reports at least
one clamp over 12 seeds × 2 baselines — so a flag that goes dead again fails the test instead of
passing it. This is a strengthening: nothing was removed that was testing anything.
**Checklist item 7.**

## F16 — the recorded frames survive the round trip by value

`parseReplayBytes` was checked with counts only. `tests/test_replay.nim` now asserts, for all 601
frames, that the reread `g`/`h`/`p` arrays equal the sim's and that each frame stamps its own
index; and that every frame agrees with the series row for its tick — body counts equal
`series.pop`, per-species energy sums equal `series.bio`. That is the in-tree version of the
consistency the reviewer verified externally on the CI artifact, and it is what the score, the
scorebug and the strip all read. **Checklist item 2.**

## F17 — `results.biomass` averages the ticks actually played

`biomassSum` also accumulated on the tick-0 call, while `meanBiomass` divides by `sim.tick`: T+1
samples over T. Frame 0 no longer enters the sum. `tests/test_replay.nim` asserts
`results.biomass[slot]` equals the mean of the recorded `series.bio` rows over ticks 1..T; before
the fix it reads `19772` where the series means `19748`. **Checklist item 2.**

## F19 — the birth hairline and the collapse/end feed rows

`collectFx` already captured the parent position but nothing drew the link, and `collapse`/`end`
pushed no feed row. The sprite protocol has no line primitive (`addObject` places a sprite; there
is no rotation or scale), so the hairline is two dimmed sparkles spaced along the parent→child
segment, skipped when the child is born within 8 units of its parent and bounded by the same
`MaxFxObjects` pool. `onCollapse` now pushes a row before its banner and `onEnd` pushes one naming
the ending. **Checklist items 11 and 13.**

## F20 — three pieces of dead state deleted

`GameState.trackers` (never written or read), `shuttingDown` (set once, never read — `/healthz`
answers until `quit(0)`, which is what the grace is for) and `SimServer.says` (written every
doctrine, never read; the viewer's `say` comes from the `doctrine` event). No behaviour change.

## F24 — the live population strip grows instead of freezing

The live socket shipped the `lead` series once, on the connecting spectator's first frame.
`chrome_common.js` (verbatim starter) latches the first series it sees and `recordMomentum` then
declines to accumulate, so a spectator who connected at tick 0 got a one-row series and a strip
frozen at a single point for the whole episode. The live path no longer sends `lead` at all: the
strip is fed frame by frame from `teams[*].lives`, which is how paintbot's lives series works and
what the note describes for the live view. The ship-once trick stays where the note scopes it — the
recorded replay (`replays.nim:278-288`), which is the path checklist items 3/11/13 exercise and
which is untouched.

## F25 — a throttled seat waits for the next generation's batch

A 429 raised a plain `EcosError`, so `decideAll` put the seat straight back into this generation's
retry batch — a throttled sidecar hit twice inside ~50 s, which is the cascade raid item 4 exists
to prevent. The note: "429 is logged and retried in the next generation's batch". A 429 now raises
`EcosThrottleError`, which `decideAll` catches separately and does not re-open: the seat plays the
steward doctrine for this generation (recorded `source: "fallback"`, as any other failure would be)
and gets a fresh call next turn, a `minTurnSeconds`-floored generation later. Every other failure
keeps the retry-once ladder unchanged (`tests/test_llm.nim` still asserts retry-exactly-once and
the fallback recording). New assertion: a 429 is distinguishable from an unusable reply.
**Checklist items 5 and 8.**

## F26 — the deadline check reserves the generation it commits to

`playDeadline` was tested with nothing held back, so a check that passed at 719.9 s committed the
episode to up to 25 s of batch + 25 s of retry batch + a generation + `minTurnSeconds` of floor
sleep before `finishEpisode` — ~80 s past the 720 s the note sizes the episode to settle inside.
The check now requires `2 · llmTimeoutSeconds + minTurnSeconds` of headroom before starting another
generation, which is exactly what starting one costs. Still checked between generations only, as
the note prescribes. The second half of F26 — the deadline is measured from process start, so the
≤180 s connect wait is charged against the play budget — is left as is: it is the conservative
direction (the platform's timeout also starts at process start) and the note pre-declares it
acceptable. **Checklist item 5 (timeout).**

## F27 — advisory, no change: `feed_lines: 0` is the harness's selector

`tools/ci/viewer_smoke.mjs` is byte-identical to the builder template and reads
`#feed, .feed, #log`; this page's feed is `#killfeed`. It is a reported field, not an asserted one,
and `pushFeed` self-removes each row after a dwell, so 0 is a legitimate reading at an arbitrary
instant either way. Adding a `.feed` class to the starter's markup would be a second departure from
verbatim chrome for no assertion. Left alone — and F19 makes the feed carry more rows, not fewer.

## F28 — advisory, no change: the fixtures name players with the aliases

`standard`, `harsh-spring` and the certification fixture all set
`players: [{Sedge},{Bramble},{Quill}]`, which is exactly what the note's §Packaging specifies, so
`policyNames == names` offline. The two-name-space MECHANISM is present and correct (the replay
carries both arrays, the chrome headlines the policy name, `results.names` carries policy names,
and no policy name reaches a seat) — it simply cannot be observed offline, because the platform
supplies real policy names in `game_config.players` for a hosted episode. Changing the fixtures to
prove it would contradict the note's own fixture text. **Checklist item 4** — unaffected.

---

## NOTED (not fixed)

Seen while fixing, not a finding in this round's review, and deliberately left alone:

- `chromeFrame` clamps the displayed generation to `config.generations`
  (`replays.nim:239`), so a collapsed episode's last frames read the final generation number
  rather than the one that was running. Cosmetic, and the end-card names the collapse.
- `sim_config.update` accepts `fieldW`/`fieldH`, which no schema property declares (F7's family).
  No fixture sets them and the note lists neither.
- `tests/helpers.nim`'s `runEpisode` passes `clamped: false` to `applyDoctrine` for its own
  fixtures; only `test_baseline` (F15) feeds the baseline's real flag. Harmless — those fixtures
  are not asserting on the flag — but it is the same shape of hard-coded literal F15 removed.
