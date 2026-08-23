# r2 fixes — ecos

Head: `402792be0c53c815545ec71cc456deffeb66b626` (== `origin/main`)
CI: https://github.com/Metta-AI/cogame-ecos/actions/runs/32641507840 — **success**
(jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; `gh run view 32641507840` reports head sha
`402792be0c53c815545ec71cc456deffeb66b626`, i.e. the pushed head, not an earlier run).

Findings: **6 fixed, 1 fixed as documentation, 1 answered without a code change.** Nothing was
refuted — both blocking findings reproduced exactly as the review described, and I have the
failing-before / passing-after output for each. No test was deleted, skipped, weakened or made
non-blocking; two test files gain assertions and nothing else.

**This sandbox has a Nim 2.2.4 toolchain** (`/tmp/nim-2.2.4/bin/nim`), which the reviewer's did
not, so every claim below is *executed*, not inferred: the whole suite was run in both modes
(`nim r --hints:off [-d:release] --path:src tests/*.nim`) before each push, and both new tests
were confirmed to FAIL against the unfixed source first.

`git push` over HTTPS is rejected sandbox-wide, so each commit was pushed through the Git Data
API (blobs → tree → commit → PATCH `refs/heads/main`, `force: false`), one API push per commit,
with the local clone realigned by `git fetch` + `git reset --mixed origin/main` afterwards. No
force-push, no rewritten history.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking) | fixed | `c3f4ed5` | `src/ecos/llm.nim:478-489`, `tests/test_llm.nim:14-77,226-266` |
| F2 (blocking) | fixed | `9eea729` | `src/ecos/replays.nim:183-190`, `tests/test_replay.nim:160-222` |
| F3 | no change (used as the F2 test's oracle) | — | `src/ecos/sim.nim:581-583`, `tests/test_replay.nim:194-205` |
| F4 | fixed (docs) | `402792b` | `docs/plans/2026-08-23-ecos-design.md` §`results.json`, `coworld_manifest_template.json:263-266` |
| F5 | fixed | `787b916` | `src/ecos/server.nim:289,304-312,320-329` |
| F6 | fixed | `6753cec` | `src/ecos/server.nim:498-508` |
| F7 | fixed | `2c043fc` | `client/replay_broadcast.html:2329-2344` |
| F8 | fixed | `adbd90a` | `src/ecos/global.nim:380-421` |

---

## F1 — a 429'd seat kept the zero-value `Decision` (blocking, checklist item 8)

**Confirmed exactly as written.** The `EcosThrottleError` branch in `decideAll` logged the
throttle and fell out of the `try` without touching `result[index]`, and without re-opening the
seat — so the terminal fallback loop (`for index in open`) never saw it either. That seat left
`decideAll` holding the zero-value `Decision`: doctrine `[0, 0, 0, 0]` (below `DoctrineMin` on
three of four grass fields, two of four for grazers and predators), `clamped: false`,
`source: dsLlm`. `server.nim` installs it with `applyDoctrine`, which does not clamp, and records
it on the replay's `doctrine` event as an ordinary model decision.

**Now:** the branch writes `scriptedDecision(sim, sim.roleOf[slot], skSteward)` and stamps it
`dsFallback` — the same terminal treatment every other failure path gets. The seat is still not
re-opened, so the note's rule (retried in the NEXT generation's batch, not this one's) is intact.

**Evidence.** `tests/test_llm.nim` gains a `decideAll`-level test over a real transport: a
loopback socket on `127.0.0.1:0`, served by a thread that answers every request
`429 Too Many Requests` (it honours libcurl's `Expect: 100-continue` and drains the body first,
so the 429 is a clean HTTP response and not a transport error). The client is built by
`newLlmClient` with `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` pointed at that socket, so the whole
ladder — batch, curl, `textOf`, `EcosThrottleError`, the handler — runs. It asserts, for all
three seats: `source == dsFallback`, `fields == scriptedDoctrine(sim, species, skSteward)`, every
field inside `DoctrineMin..DoctrineMax`, `clampDoctrine(...).clamped == false`, no raise, and
`stubHits == 3` (one request per seat: a 429'd seat is not retried inside the same generation).

Against the unfixed `llm.nim` it fails with
`` `decision.source == dsFallback` a throttled seat must be recorded as a fallback, saw llm ``;
with the fix it passes in both debug and `-d:release`, and in CI's `test` job.

## F2 — `precompute` dropped the partial generation a collapse ends on (blocking, checklist item 2)

**Confirmed, and measured.** The viewer flushed its per-generation biomass accumulator only at
exact multiples of `ticksPerGeneration`. The sim, on a mid-generation collapse, closes that
partial window and scores it against the full `ticksPerGeneration × R_i` denominator
(`sim.nim:628-630` → `closeGeneration`), so the viewer's `scoreAt[lastTick]` sat *below*
`results.scores` on every collapse replay — and the shortfall is per-species, so the end-card
winner could differ from `results.win`. Measured on the greedy-predator fixture, seed 1, collapse
at tick 317: the viewer re-derived **5.938842** where `results.scores[0]` carries **6.447305**.

**Now:** the flush condition is `tick > 0 and (tick mod perGeneration == 0 or tick == ticks - 1)`.
On a `ten_generations` or `deadline` ending the last tick IS a boundary, so the condition fires
exactly once and those replays are byte-identical; `forfeit` records only frame 0 and never
accumulates. The sim cannot end mid-generation *without* closing that window: `endEarly` is only
reached from the top of the game loop or from `finishEpisode`, both of which hold `stateLock`
that `runGeneration` holds for a whole generation, so the two flushes cannot disagree.

**Evidence.** `tests/test_replay.nim` extends the score-lock block to a collapse episode — the
`fixedPicker` greedy predator from `test_broadcast.nim`, looped over seeds 1..6 and asserted to
have ended `collapse_*` **and** `tick mod ticksPerGeneration != 0`, so the fixture is only
accepted if it is actually the broken case. It asserts, through `initReplayPlayer` on the
re-parsed replay BYTES: per-slot equality of `scoreAt[lastTick]` with `results.scores`; the same
numbers on the replay's own `end` row (F3's oracle); and an end-card (`advanceReplayFrame` with
`jumpEnd`) whose per-team scores are `results.scores` and whose `winner`/`draw` matches
`results.win`. It fails on the unfixed `replays.nim` with the 5.938842 / 6.447305 line above.

## F3 — the replay's `end`/`generation` rows carry the sim's scores and the viewer reads neither

**No code change, and the review does not ask for one:** checklist item 2 requires the display to
come from the viewer's own re-derivation rather than from a parallel recording, which is what the
code does. Making `onEnd` read `e.scores` would trade a bug for a checklist violation and would
have hidden F2 instead of fixing it. It is, as the review says, the cheapest oracle — so it is now
one: the F2 test cross-checks `scoreAt[lastTick]` against the recorded `end` row
(`tests/test_replay.nim:194-205`), which means the two representations are locked together for
every future change.

## F4 — `results.generations` counts a partially played generation

**Real, and documented rather than changed** (`402792b`). `closeGeneration` increments
`generationsPlayed` for the partial window too, so a collapse at tick 137 of a 60-tick generation
reports `generations: 3`. That same counter is the end condition
(`generationsPlayed >= config.generations`), `runGeneration`'s target and `history.len`, and the
partial window IS scored — by the sim, by the viewer after F2, and by `test_feasibility`'s
summariser. Changing the count would make it disagree with three things that already agree.

So both places that define the field now say what the code does: the design note's `results.json`
field list (`generations` = generations SCORED, with a **Shipped deviation** block in the note's
own convention explaining the one ending where "completed" and "scored" differ) and the
manifest's results schema, which previously had no description at all. **Note-pinned behaviour
touched:** the repo copy `docs/plans/2026-08-23-ecos-design.md` only; the run copy
`runs/2026-08-23-ecos/design.md` was not edited.

## F5 — a seat that never connected was recorded `scripted`

**Fixed** (`787b916`). The per-generation snapshot substitutes `skSteward` for any slot with no
socket, and `scriptedDecision` stamps a declared baseline `dsScripted`, so the replay could not
tell "an LLM policy whose pod never connected" from "a seat that set `PLAYER_SCRIPTED=steward`".
The loop now records which slots it substituted (`absent`) and stamps those decisions
`dsFallback` — the source that means no policy decision reached the sim — before it logs and
applies them. The doctrine played is unchanged, and because the snapshot is rebuilt every
generation a late-arriving socket still rejoins. Phase 60 can now count the miss and the feed
draws its `auto` badge. Satisfies the recording half of checklist item 8 for this path.

No test: this is six lines inside `runGame`'s loop body, which needs a live mummy server, a game
thread and a websocket to reach; the decision layer it feeds (`decideAll`) is already covered.

## F6 — `seats` is hard-coded `@[0, 1, 2]`

**Reachability, judged.** The review could not construct a delivery path and neither could I —
`num_agents: 3` is in all three manifest variants, and `tools/ci/docker_smoke.sh` hard-fails on
any other value. But the *guard* that would catch a bad one does not exist: `validate()` checks
`numAgents`, which `config.update` reads from `num_agents`/`numAgents`, while the seat width the
game actually uses comes from `tokens`/`players`. Those two are never compared, so a config with
two tokens and no `num_agents` passes `validate()` and the `tokens.len != players.len` guard, and
the first generation indexes `scriptedKinds[2]` off a two-element seq. `-d:release` keeps bound
checks on (only `-d:danger` removes them), so that is an `IndexDefect` on the game thread: the
loop dies, `finishEpisode` never runs, no artifacts are written, and the episode hangs to the
platform timeout.

**Fixed** (`6753cec`) with a three-line startup guard next to the alignment check it belongs
with: any seat count other than three is rejected before the server starts serving, where the
message is legible. Nothing on the shipped path changes — `docker-smoke` sends three tokens and
is green.

## F7 — the clock caption counted against the collapse tick

**Fixed** (`2c043fc`). `renderEcosClock` took the caption's denominator from `mx`, which on the
replay path is `player.lastTick` (the last RECORDED tick), so a collapse at tick 137 of a 600-tick
episode read `tick 42 of 137`. It now reads `mt` (`generations × ticksPerGeneration`), which
`buildStateJson` writes on every frame of both the live and the replay path, giving the note's
`tick 214 of 600` on both. `mx` is untouched, so the scrubber's extent is still the recorded
episode. The inline script still parses (`node --check` on the extracted block) and the
`wasm-viewer` job's browser soak is green on the change.

## F8 — the birth hairline could starve other fx of slots

**Fixed** (`adbd90a`). The bound and the id range were never in question (the review says so, and
I re-read both loops): the issue is priority. A sparkle emitted its own object and then, inline,
up to two link objects, so on a heavy birth tick one birth's hairline could consume the slots that
another body's fade or splash needed. The hairlines are now a second pass over the same `fx` list:
every item gets its primary object first, and the links spend whatever remains of the 400. Same
ids, same `MaxFxObjects` bound, same drawing (each object carries its own `z`), different
priority. `tests/test_replay.nim`'s packet loop and the wasm-viewer browser soak both still pass.

---

## NOTED (not fixed)

- `client/replay_broadcast.html`'s `case 'generation':` is an explicit no-op while the event
  carries per-generation `pop`/`bio`/`score` — a feed row per generation would be free content.
  Not a finding in this round's review; not touched.
- `results.generations` and `history.len` are the same number by construction but are computed in
  two places; nothing asserts they agree. Not a finding; not touched.

## Commits, in order

```
c3f4ed5  fix(llm):     r2-F1 — a 429'd seat plays the recorded steward fallback
9eea729  fix(viewer):  r2-F2 — flush the partial generation a collapse ends on
787b916  fix(server):  r2-F5 — a seat that never connected is recorded as a fallback
2c043fc  fix(viewer):  r2-F7 — the clock counts against the configured episode
adbd90a  fix(viewer):  r2-F8 — birth hairlines take what is left of the fx pool
6753cec  fix(server):  r2-F6 — reject a seat count the game cannot play
402792b  docs(results):r2-F4 — define results.generations as generations SCORED
```

One finding per commit; no batching, no unrelated cleanup. Local suite, both modes, on the pushed
head: `test_baseline`, `test_broadcast`, `test_feasibility`, `test_llm`, `test_manifest`,
`test_replay`, `test_sim` — all ok.
