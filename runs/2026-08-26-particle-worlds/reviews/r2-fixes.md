# r2 fixes — particle-worlds

Repo `Metta-AI/cogame-particle-worlds`, branch `main`.
Base: `b6b4401ad9db9973387ab011150a73f65ab6e69c` (r2 review's head).
Head: `238f88cc52e85c4c05b1ed1dd0ce7eece9852881`
CI: run **32968643250** on `238f88cc` —
https://github.com/Metta-AI/cogame-particle-worlds/actions/runs/32968643250 — **success**
(all three jobs green, every step `success`, no `continue-on-error` in `ci.yml`).

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking, item 2) | fixed | `13c66d75a6726095fbeb110cd81434b41a8fcd33` | `src/mpe/sim.nim:2998-3047` (`StopRecordKind`, `wallClockStopRecord`, `isWallClockStopRecord`, `applyWallClockStop`), `src/mpe/server.nim:1409-1424`, `src/mpe/replays.nim:405-424`, `tests/test_replay.nim:20-70,199-265`, `src/mpe/sim_types.nim:21-33`, `docs/PROTOCOL.md:184-206`, `docs/plans/2026-08-26-particle-worlds-design.md` (+ AGENTS.md, manifest) |
| F2 | fixed | `8d7da32a7711449610656a3db4861a061adcb719` | `src/mpe/control.nim:363-379,394-398`, `src/mpe/server.nim:1962-1970`, `tests/test_control.nim:180-216` |
| F3 | fixed (documentation) | `7b7b6f3e095c86b078b2a9168dff7895c5837739` | `src/mpe/decide.nim:258-266` (`roundcardRecord`), `docs/PROTOCOL.md:201-206`, `docs/plans/2026-08-26-particle-worlds-design.md:1082-1086`, manifest |
| F4 | fixed | `8faa55284ed77098ef4ebadd2c35282daede6ec9` | `src/mpe/decide.nim:376-393`, `tests/test_engine.nim:320-321`, design note §Budget guard |
| F5 | fixed (comment) | `7092f9d004e1aa8f930bce8d295c595adb2fb923` | `src/mpe/sim_config.nim:792-808` (the `NECESSARY condition` note at :799) |
| F6 | fixed | `238f88cc52e85c4c05b1ed1dd0ce7eece9852881` | `src/mpe/sim_types.nim:652-662` (5000 constant deleted), `src/mpe/sim_config.nim:75` |

Nothing disputed, nothing deferred for design. One commit per finding, in finding order.
Local `main` and `origin/main` are identical in content (`git diff HEAD origin/main` empty);
the commits were pushed one at a time through `gh api graphql createCommitOnBranch` because
plain `git push` over https fails in this sandbox with "Invalid username or token", which is
why the pushed shas differ from the local ones (the API rewrites the committer).

---

## F1 — the wall-clock `deadline` stop is now a recorded record (checklist item 2)

**What the code did.** `server.nim:1409-1423` ran, at the top of a loop iteration,
`sim.bankRound(...)` + `sim.finishGame(Red, isDraw = true)` — outside `sim.step`. Every field
that touches is in `gameHash` (`sim_state.nim:162-174, 320-333`: `phase`, `winner`, `isDraw`,
`gameOverTimer`, `roundsPlayed`, `roundLog.len` and every entry). The same iteration then ran
`:2070 replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())`, so exactly one recorded
hash described a state produced by an unrecorded, server-side mutation, and no record in the
stream let playback reproduce it.

**What it does now.** The stop is written into the chat stream as a `stop` control record at the
tick it fires, and applied on **both** sides by one proc — `sim.applyWallClockStop`
(`sim.nim`) — the live server as it writes the record, `applyReplayEvents` as it reads it back.
The ordering is exact rather than lucky: the live loop writes the record at
`tickTime(sim.tickCount)` **before** that iteration's step, and `applyReplayEvents` applies
chats with `time <= tickTime(sim.tickCount)` **before** the same tick's step. So the replayed
sim banks the same round from the same `gameTicksElapsed()`, reaches the same `GameOver`, and
recomputes the same hash.

**Why the record is unavoidable.** A wall-clock deadline does not follow from sim state — that
is the whole point of it — so no re-simulation can derive when it fired. `stop` is therefore the
one load-bearing chat record, and `docs/PROTOCOL.md` §Chat records now says so instead of
claiming that every record is presentation-only. The starter's rule that "nothing a commander
SAYS may move the hash chain" is untouched: the engine's stop is not something a commander says.

**Evidence.** New test `tests/test_replay.nim`, "a DEADLINE-ended episode re-derives frame by
frame, stop tick included". It records a deadline-ended episode through the real
`openReplayWriter` (the harness's wall clock is the 24 Hz tick clock, so `wallClockBudgetSeconds
= 10` stops it at tick 240, mid-round, reproducibly), then runs `parseReplayBytes` +
`initReplayRuntime` + `advanceReplayFrame` and asserts

* `player.hashMismatchTick == -1` over the whole chain, the stop tick included;
* exactly one `stop` record in the bytes;
* and that playback **ends where the recording ended** — `phase == GameOver`, the same `winner`,
  `isDraw`, `roundsPlayed`, the same banked round permille per seat, and a re-derived results
  document with `reason == "deadline"`, `endRule == "wall_clock"` and the same `scores`,
  `roundScores` and `roundEndRules` as the recorded one. (The review's "a replay that silently
  stays Playing at the end is not a fix" is exactly what these assertions rule out.)

With the playback half of the fix reverted, the same test prints
`DEADLINE MISMATCH at tick 241 simTick=241 phase=Playing roundsPlayed=0` and fails five checks;
with it, both the local debug and release runs pass, and CI's `wasm-viewer` job — the
native-to-wasm determinism gate — is green on the commit.

**GameVersion 1 → 2** (`sim_types.nim`, headline "the wall-clock `deadline` stop is RECORDED";
AGENTS.md's GameVersion section updated with it). Nothing in `gameHash`, the integer motion
model or the seeded draw order moved, so no pre-existing replay re-simulates differently. The
number changes for the other half of the repo's own rule (`tools/ci/check_gameversion.sh`'s
rationale): a GV1 viewer would *load* a GV2 recording and re-simulate its stop tick wrong, which
is worse than a refusal.

## F2 — `hold` brakes where the order landed

**What the code did.** `control.nim`'s `intHold` steered to `sim.holdX/holdY`, whose only writers
were `field.nim:239-240` inside `placeParticles` — once per round, at the spawn point on the
250 px ring. A particle that had moved and was then ordered `hold` was navigated back to its
spawn point, up to ~500 px away, at cruise. `llm.nim:252-253` ("hold = brake and stay where you
are"), `docs/RULES.md:192`, the design note and `goalFor`'s own comment all promise the opposite.

**What it does now.** `control.anchorHold(sim, cogIndex)` stamps the anchor from the particle's
current centre, and `server.nim`'s turn block calls it for every `hold` order as it installs the
turn's directive — the tick the comment always described. Every seat is assigned a directive at
every turn boundary (`decide.turn` covers llm / fallback / scripted), so the only orders that
still see the spawn anchor are the pre-turn-0 drifter orders, when the particle is at spawn.

Determinism: the anchor is not hashed and playback never reads it. It feeds mask compilation,
which is on the live side of the determinism boundary — the masks it produces are what the
replay carries — so no GameVersion implication. (The anchor is the particle's *centre* now,
where the spawn write stored the collision box's corner; `goalFor` compares against centres, so
this also removes a 6 px offset. `field.nim` is untouched.)

**Evidence.** New test in `tests/test_control.nim`: displace a particle ~400 px from spawn, stop
it, install `hold`, then hold for two whole turns (216 ticks) compiling real masks and stepping
the sim. `goalFor` returns the displaced position, the particle ends within `2 * ArriveRadius`
of it, and it is still > 300 px from the spawn ring. Dropping the `anchorHold` call from that
test fails all three checks — the particle walks home.

## F3 — the roundcard cross-check claim, corrected in all three places

Playback discards the record: `replays.nim:411-424` routes control records to
`pushFeedDirective`, which returns unless `k == "directive"` (`sim_state.nim:363-364`), and now
also recognises `stop` — nothing else. `tools/replay_summary.py` is the only reader in the tree.
There is no cross-check, so the three claim sites (`decide.nim`'s `roundcardRecord` docstring,
`docs/PROTOCOL.md` §The replay, the design note's §The replay) now say what actually happens:
the record is a convenience for `replay_summary.py`, playback drops it, and because every value
on the roundcard is in `gameHash`, a divergence surfaces as a hash mismatch at the tick it
happens — a strictly stronger signal than one record comparison per round. No new machinery, per
the brief.

## F4 — the budget guard reserves a whole turn, floor included

`decide.nim`'s guard computed `turnSeconds` from `turnBudgetMs` alone and reserved `2 *` it.
After r1's budget-clock fix the worst single turn costs the rate floor **plus** the calls
(`turnSpacingMs` of batch-start spacing, then `turnBudgetMs` clocked from the moment the wait
ends) = 19 s at the shipped 9000/10000, so the guard's last callable turn ended ~2 s inside the
690 s stop while `2 * turnBudgetSeconds` implied ~10 s. `turnSeconds` is now
`(turnSpacingMs + turnBudgetMs + 999) div 1000`; the threshold moves from `elapsed ≥ 671` to
`elapsed ≥ 653`, and in steady state (40 turns at the 9 s cadence ≈ 400 s) nothing changes.
`tests/test_engine.nim`'s guard case still fires — the fixture's floor is 0, so its arithmetic
is unchanged — and its comment now states the full expression. The design note's §Budget guard
carries the same correction.

## F5 — the landmarkMargin validator is documented as a necessary condition

Comment only, at the check. It measures the longer axis, so a box with a degenerate short axis
still validates; making it sufficient would mean solving the 2-D packing in the validator, and
nothing downstream is unbounded (the `MaxLandmarkDraws` cap, the RNG-free lattice sweep, and the
sim guard's 120 px assertion). The comment says what the check is for: turning the one case a
hosted config can plausibly hit — a margin turned up past the board — into a clear config error
instead of a mid-episode fault.

## F6 — one turn-spacing default, and it is 9000

`DefaultTurnSpacingMs = 5000` was the base config's value and a two-seat number (four seats at
5 s is 48 req/min against the sidecar's 30/min cap). Every shipped variant, the schema default
and the fixture carry 9000. `sim_config.nim:75` now takes `DefaultParticleTurnSpacingMs`, and the
unused constant is deleted rather than left as a second answer; its comment records why 5000 was
wrong.

---

## NOTED (not fixed — outside this round's findings)

* `applyWallClockStop` banks with `sim.gameTicksElapsed()`, and `scoring.roundPermille` divides
  by that value. If the stop ever fired on the very first Playing tick of a round, `ticks` would
  be 0 and the division would raise. That is pre-existing (the same expression the reviewed code
  had), unreachable in production (the stop is 690 s in, mid-round) and not a finding in this
  round, so the code is unchanged. A one-line `> 0` guard would close it.
* `field.placeParticles` still seeds the hold anchor with the collision box's top-left corner
  rather than its centre (~6 px). Harmless — it only matters before turn 0 lands, when the
  particle is at spawn — and out of scope.
* The `fault` end path still ends playback without reaching `GameOver` (it breaks before the
  hash write, so there is no unre-derivable hash and item 2 is not violated), which the r2 review
  lists under "could not determine". A `stop`-style record would give a fault replay an end
  segment too. Not a finding this round; not touched.
* The coworld-builder copy of the design note
  (`runs/2026-08-26-particle-worlds-design.md` → `runs/.../design.md`) carries the same F3
  sentence at :1082-1085 and the same §Budget guard arithmetic at :452-471 as the in-repo mirror
  I corrected, and has no r2 amendment section. The in-repo copy
  (`docs/plans/2026-08-26-particle-worlds-design.md`) now carries both corrections inline plus an
  "Amendment — r2 review" section describing the `stop` record; the run-directory copy is the
  coordinator's file, so I left it alone.

## Verification

Local (a nimby 0.1.26 / Nim 2.2.4 toolchain fetched into this sandbox, the same pins `ci.yml`
uses): every `tests/*.nim` green in **both** debug and `-d:release`; `src/particle_worlds.nim`
and `src/particle_worlds_player.nim` compile in release; `python3 tools/build_manifest.py
--check` clean. No test was weakened, skipped or deleted — the two test changes are the two new
cases above plus one comment line in `tests/test_engine.nim`.

CI on the pushed head: run **32968643250**, `headSha 238f88cc52e85c4c05b1ed1dd0ce7eece9852881`,
conclusion **success** — `test`, `docker-smoke` and `wasm-viewer` all `success`, and every step of
every job `success` (queried per step, not inferred from the run conclusion). The full log:

* `grep -c "SEAT-COUNT FAIL"` over the whole log = **0** (and `grep -c "SEAT-COUNT"` = 0);
  the smoke printed `game=particle-worlds seats=4` and
  `smoke OK: seats=4 results=878B replay=31462B reason=complete`.
* the new deadline test appears twice — once for debug, once for `-d:release`:
  `[OK] a DEADLINE-ended episode re-derives frame by frame, stop tick included`; the new hold
  test likewise twice.
* the native-to-wasm determinism gate printed
  `ok: loaded replay.json, advanced 300 frames (6249845 packet bytes, heap 148 MB)`.

The intermediate per-commit runs were auto-cancelled by the workflow's own concurrency group as
the later pushes landed, except run **32968614588** on the F1 commit `13c66d75`, which ran to
completion and is also **success** (all three jobs) — so F1 is independently green on its own
commit as well as on the head.

Retry budget: **0 of 3** attempts against a red CI used — CI was green on the first push.
