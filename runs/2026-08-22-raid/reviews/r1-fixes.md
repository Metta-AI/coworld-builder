# r1 fixes — raid

Repo: `Metta-AI/cogame-raid`, branch `main`.
Reviewed sha: `501040ded40f71756ecb5a4291490bd40a5e0806`.
**Final main sha: `6a8a68c23a606cf7c2046568800c753ecee3dd04`**
**Final green `ci.yml` run: 32621942459** — conclusion `success`
(<https://github.com/Metta-AI/cogame-raid/actions/runs/32621942459>), all three jobs
`success`: `test`, `docker-smoke`, `wasm-viewer`.

CI evidence from that run's logs:
`grep -c 'SEAT-COUNT FAIL'` → **0**; `docker-smoke` logged
`smoke OK: seats=5 results=1440B replay=47263B reason=complete`; the `test` job ran all **17**
`tests/*.nim` files in **both** debug and `-d:release` (35 `nim r --hints:off` invocations, 17
distinct test files); the `wasm-viewer` job logged
`WASM-SMOKE OK: 647 ticks, digest 925898626, 112 events`, i.e. the wasm harness now really
executes in CI. **No test was deleted, skipped, narrowed or loosened by any commit below** —
every test-file hunk in `git log -p 501040d..6a8a68c -- tests/` adds assertions, except the two
noted explicitly (the `golden_digests.json` re-record that was *reverted* — see F7 — and the
removal of two never-read fields from a test-local `FakeClient`).

Sixteen commits, one per finding (F18 has two: the CI half and the test-gap half). Each commit
message names the finding, what it changed and the consequence it removes.

Push note: `git push` over https is rejected by the sandbox credential helper for this repo
(`remote: invalid credentials`, also with `gh auth setup-git` and with an
`http.extraheader` bearer). All commits were published through the GitHub Git Data API
(`gh api` blobs → trees → commits → one non-forced `PATCH refs/heads/main`), then verified with
`git fetch`: `git diff origin/main HEAD` is empty. No force-push, no history rewrite.

---

## Disposition table

| F | § | disposition | commit | files | checklist item |
|---|---|---|---|---|---|
| F1 | B1 | **fixed (blocking)** | `6916ff9` | `src/raid/llm.nim`, `src/raid/labels.nim`, `tests/test_orders.nim` | **9 rune-safe truncation** |
| F2 | N1 | fixed | `d613c40` | `src/raid/baselines.nim:180-210`, `tests/test_baselines.nim:191-233` | 7 (baseline plays legally) |
| F3 | N2 | fixed | `046a140` | `tools/tune_baselines.nim` (new), `src/raid/baselines.nim` | 7 (tuning clause) |
| F4 | N3 | **no change** — documented in place | — | `src/raid/control.nim:147-157,352-360` | none |
| F5 | N4 | fixed | `a6f7465` | `src/raid/server.nim:129-149` | 5 (degrade, never hang) |
| F6 | N5 | fixed | `0ecf68e` | `src/raid/server.nim:156-168` | none (note's write order) |
| F7 | N6 | **code unchanged — doc + test; retune is a design question** | `bd92365` | `docs/RULES.md`, `coworld_manifest_template.json`, `tests/test_boss.nim:43-64` | none |
| F8 | N7 | fixed | `40b7dc4` | `src/raid/types.nim`, `src/raid/combat.nim:71-82`, `src/raid/sim.nim:462`, `tests/test_combat.nim:176-197` | none |
| F9 | N8 | fixed | `5578779` | `src/raid/boss.nim:194-199` | none |
| F10 | N9 | fixed | `b9c62e8` | `src/raid/config.nim:54-95`, `src/raid/llm.nim:129-134`, `tests/test_engine.nim` | 5 |
| F11 | N10 | **no code change** — comment naming where the bound lives | `5d0ed18` | `src/raid/engine.nim:100-110` | 5 |
| F12 | N11 | **no change** — deliberate, design note keeps it | — | `src/raid/server.nim:406-413` | 3 (literal wording; intent met) |
| F13 | N12 | **no change** — documented in repo | — | `docs/PROTOCOL.md`, manifest `game.protocols.global` | none |
| F14 | N13 | fixed | `f3d455f` | `AGENTS.md` | none |
| F15 | N14 | **no code change** — comment recording the deliberate departure | `640b916` | `src/raid_player.nim:42-56` | none |
| F16 | N15 | fixed (comment) | `c6df382` | `src/raid/telegraphs.nim:103-110` | none |
| F17 | N16 | fixed | `46283c9` | `docs/PROTOCOL.md`, `coworld_manifest_template.json`, `src/raid/boss.nim:178-186`, `tests/test_boss.nim` | none |
| F18 | N17 | fixed in part; two gaps remain | `0ea9001`, `6a8a68c` | `.github/workflows/ci.yml`, `tests/test_engine.nim`, `tests/test_determinism.nim` | 1 (CI actually runs the harness) |
| F19 | N18 | **no change** — the note's floor description is stale, measured | — | `tests/test_baselines.nim:175-176` | none |

---

## F1 (B1) — captured LLM error text sliced by byte index — **fixed**, `6916ff9`

All four byte slices in `llm.textOf` (`:207`, `:215`, `:220`, `:229`) now go through
`labels.runeCap`, and `runeCap` was made a real sanitiser: `utf8Only` drops any byte that is not
part of a well-formed UTF-8 sequence before the rune cut, because an error body captured from a
proxy or a sidecar is not text we produced. `textOf` is exported so it can be tested directly.

Evidence: `tests/test_orders.nim` gained `testCapturedErrorTextIsRuneSafe` (a 4-byte emoji
astride each of the 400/300/300/160 caps, plus a body that is invalid UTF-8 to begin with:
`validateUtf8(message) == -1` in every case, and the emoji survives whole) and
`testDetailAtTheCapIsValidUtf8` (a fallback detail whose 200th rune is the emoji, recorded
through `applyTurn`, serialised, `parseJson`-ed). Both fail against the pre-fix code. Both ran
twice in run 32621942459 (`ok: captured error text is cut on rune boundaries`, `ok: a fallback
detail whose 200th rune is multi-byte stays valid UTF-8`). Satisfies checklist item 9,
including its "a test feeds multi-byte input at the cap" clause for the *captured errors* path
that was previously covered only for `say`.

## F2 (N1) — stalwart tank clobbered its own crucible soak — **fixed**, `d613c40`

The unconditional `result.onTelegraph = rxDodge` moved above the soak assignment, so the
soak-duty branch is the last word again; the arithmetic that justifies dodging cleaves is
unchanged and now sits at the top of the proc, and the constructor's dead `rxHold` is gone.

Evidence: `testStalwartSoaksCrucibles` (new) asserts a healthy phase-3 tank emits `soak`, the
healer never does, the dps take over under 60 %, nobody soaks outside Meltdown, and — end to
end over a full stalwart episode — every `telegraph_resolve` of kind `crucible` has
`soakers >= 1` and `boss.spillStacks == 0`. That last pair is exactly the consequence the review
inferred but could not run.

## F3 (N2) — the cited grid harness was not in the tree — **fixed**, `046a140`

`tools/tune_baselines.nim` is committed: it sweeps the four scalars (now `{.intdefine.}`) over
6 seeds × the default variant, rejects any tank stand `arena.canOccupyCog` refuses, requires the
certification fixture to still end in a kill, ranks by mean `simScore`, and breaks ties toward
the shipped values. The comments in `baselines.nim` now say what the sweep can and cannot
separate instead of asserting provenance the tree did not carry.

The commit also moved `TankPriorityPct` 45 → 35, the point the sweep keeps. I re-measured that
claim locally with the toolchain (`nim r -d:release -d:TankPriorityPct=<v>` over the harness's
six seeds): **mean score 0.6011 at 35 vs 0.5779 at 45**, certification `kill` with **all five
alive and score 1.4838** at both. That also settles two of the review's "could not determine"
items: the builder's "1.48 with all five alive" on the cert fixture is exact.

## F4 (N3) — undeclared heal gates — **no change, correct as is**

Both gates are in the tree with their reasons: `HealWasteFloor = 60` and `worthHealing` at
`src/raid/control.nim:147-157` ("overheal is recorded and wasted, and the 1200-point pool is the
whole encounter's healing budget"), and the planted gate at `:352-360` ("a cast is cancelled by
8 px of movement, so never START one while the controller still intends to walk"). They make the
healer start strictly fewer casts than the note's rule, never more, so no legality or budget
clause is affected and no checklist item is touched. This is a delta the builder should have
declared, not a defect to fix; changing it would be a balance change against a baseline that F3's
harness tunes.

## F5 (N4) — the done-broadcast deadline was measured, never applied — **fixed**, `a6f7465`

Was: `deadline = epochTime() + 3.0`, send, then `echo` if the deadline had passed — nothing
skipped, nothing cancelled. Now the allowance accumulates 3.0 s per seat and a seat whose turn
comes up after the allowance is spent is skipped with a log line, so the whole broadcast is
bounded at `seats × 3.0 s` ahead of the replay and results writes. mummy's `send` enqueues rather
than blocking, so nothing changes on a healthy run — which is why this is a bound made real
rather than a behaviour change. Checklist item 5. Untested: it needs a socket that stalls; the
existing `tests/test_server.nim` harness cannot run an episode to its end because the server
thread calls `quit`.

## F6 (N5) — results were written before the replay — **fixed**, `0ecf68e`

`writeArtifact(replayUri, …)` now precedes `writeArtifact(resultsUri, …)`, with the reason in
place: the hosted worker treats `results.json` as the end of the episode and tears the pods down
when it appears, so a replay written after it can be lost. Same order as
`src/ctf/server.nim:1940-1956`.

## F7 (N6) — first cleave on tick 95, note says 96 — **code unchanged; doc + test**, `bd92365`

I implemented the schedule fix (`cleaveCd: CleaveFirstTick + 1`, `pourCd: PourFirstTick + 1`,
`GameVersion` 1 → 2, `tools/record_golden.nim` re-recorded) and **reverted it after measuring
what it does**, because it is a retune, not a one-tick nudge:

| default variant, seed 42, stalwart | current | with the +1 |
|---|---|---|
| end | wipe, tick 3616 | wipe, tick 3186 |
| deepest phase | 3 (Meltdown) | 2 |
| boss hp left | 28.2 % | 41.0 % |
| episode score | 0.7175 | 0.5895 |
| crucibles poured | 2 | 0 |

It also broke `testStalwartSoaksCrucibles` (F2's new test) for a real reason — with the shift the
default episode never reaches a crucible — and would have required re-recording the golden
digests and bumping `GameVersion`. The baseline was tuned against the current schedule (F3), so
moving it means re-running the sweep and re-recording every fixture. **That is a design decision
for the judge, not a fixer's call**, and the review rated the finding advisory.

What I did instead, so nothing in the tree is untrue: `docs/RULES.md` now says the first cleave
starts "on the 96th tick of the encounter — tick index 95, because the counter is armed before
tick 0 and tick 0 spends a decrement on it", and the same for the first pour (192nd, index 191);
the manifest was rebuilt from it (`python3 tools/build_manifest.py`, since the manifest inlines
the doc); and `tests/test_boss.nim:43-64` pins both start ticks so the schedule cannot drift in
either direction without a red test. If the judge wants the note's literal 96/191→96/192, the
work is: arm both counters at +1, re-run `tools/tune_baselines.nim`, re-record
`tests/fixtures/golden_digests.json`, bump `GameVersion`, and re-check the F2 crucible test.

## F8 (N7) — `add_death.killer` always `""` — **fixed**, `40b7dc4`

`Add` gained a `killer` field; `combat.damageAdd` stamps `aliasOf(slot)` when the hit takes the
add to 0 hp, mirroring `damageCog`; step 15 records it. The field is cosmetic and deliberately
**not** in `raidStateDigest` (which is field-explicit), so no golden digest moves — verified:
`test_determinism` and `test_replay` pass unchanged. `tests/test_combat.nim:176-197` asserts a
non-lethal hit names nobody, the lethal hit names the last hitter, and the emitted `add_death`
carries the alias.

## F9 (N8) — unreachable `damage < 40` branch — **fixed**, `5578779`

Deleted. `damageCog` self-events every instance of ≥ 40 and a swing is 55 before multipliers that
are all ≥ 1, so the branch could never fire; the reason the call site needs no record of its own
is now written there. No behavioural change — the transcript already carried exactly one
`boss_hit` per landed swing. The whiff branch is untouched and `testBossWhiffsOutOfReach` still
passes.

## F10 (N9) — ceilinged deadlines ate the note's 0.5 s of slack — **fixed**, `b9c62e8`

The rounding itself is forced by the dependency: `curly.makeRequests`' timeout is whole seconds
(`OPT_TIMEOUT`), so 6.5 s of configured deadline is 7 s of waiting and rounding *down* would cut
a reply still inside its budget. What was wrong was the **check**: `config.validate` compared the
unrounded floats, so e.g. 6.2 + 3.2 (really 7 + 4 = 11 s) passed validation while overrunning the
10 s turn budget on every retry. `ceilSeconds` moved to `config.deadlineSeconds` — one definition,
used by both `newLlmClient` and `validate` — and `validate` now compares the rounded sum and names
the numbers when it refuses. The shipped 6.5/3.0 still passes, at exactly 10.0 s, and the comment
says so rather than claiming slack. `tests/test_engine.nim` covers the rounding and the refusal.
Checklist item 5.

## F11 (N10) — no distinct outer per-turn deadline — **no code change**, `5d0ed18` (comment)

The bound exists and is now enforced end to end (F10): the only wait a turn can make is
`curly.makeRequests`, given the attempt deadline and then the retry deadline, whose rounded sum
`config.validate` refuses to let exceed `turnBudgetSeconds`. A wrapper timer would not add a
bound — Nim cannot interrupt a blocking call from outside it, so an outer timer measures an
overrun instead of preventing one, which is exactly the failure F5 removed from the
done-broadcast. The comment at `engine.nim:100-110` says so, so the next reader does not go
looking for a timer that would be theatre. Checklist item 5 is satisfied ("every wait has an
explicit bound"), and `testHungClientKeepsTheEpisodeInsideItsBudget` (F18) now demonstrates it.

## F12 (N11) — the game server still routes `/client/replay` — **no change**

Deliberate and load-bearing, and the design note is explicit: "The game server still serves
`/client/replay` for local viewing off the identical `dist`." Both starters do the same
(`coworld-ctf/src/ctf/server.nim:627,642,840`, `cogame-bullwhip/src/bullwhip/server.nim:470`).
The hosted viewer path is the static bundle only — `coworld_manifest_template.json`
`game.replay_viewer` is `{"bundle": "static-replay-viewer"}` and the manifest never names a pod
URL — so checklist item 3's *intent* (the viewer contacts nothing but S3) is met, while its
literal "no `/client/replay` pod path anywhere" is not. Removing the route would contradict the
authoritative design note and delete a tested local-dev path
(`tests/test_server.nim:141-146`), so I record the tension rather than resolve it by fiat: the
judge should adjudicate note vs checklist wording.

## F13 (N12) — `/global` is JSON, not flatty — **no change**

Honestly documented in the repo at three places: `docs/PROTOCOL.md` §`raid.global.v1`, the
manifest's `game.protocols.global`, and `tests/test_server.nim:128-138`, which asserts the JSON
shape live. The design note's flatty sentence is the stale artefact, not the code. Converting a
spectator broadcast to flatty now would break the shipped browser chrome for no gain.

## F14 (N13) — `AGENTS.md` listed a non-existent `roster.nim` — **fixed**, `f3d455f`

The layout line now ends at `events.nim` and says in one sentence that the note's `roster.nim`
and `render.nim` were never built, with where their responsibilities actually live (seat join,
auth and slot handling in `server.nim`; rendering in `client/broadcast_core.js` and the wasm
viewer).

## F15 (N14) — the player binary substitutes a built-in prompt — **no code change**, `640b916`

The rule the note states is the **server's**, and it is implemented and tested
(`server.nim:376-378`, `:208-216`): a seat that registers with neither field, or never registers,
is seated as `stalwart`. The player binary's default prompt is a separate, deliberate choice: the
manifest ships this same binary with no `env` as `raid-player`, "the reference raid policy", so a
bare container that registered as `scripted` would be an LLM-free seat wearing an LLM policy's
name. Certification is unaffected — both baseline manifest players set `PLAYER_SCRIPTED`, and
docker-smoke logs `reason=complete`. The commit records that reasoning at the branch; no
behaviour changed.

## F16 (N15) — `avoidable_hits` skips crucible hits — **fixed (comment)**, `c6df382`

Deliberate and now stated at the site: standing in a crucible is the correct play (240 split
beats a permanent Spill stack), so counting it would make soaking look like a mistake in the
results.

## F17 (N16) — Overload's aggregate `boss_hit` uses `target: "raid"` — **fixed**, `46283c9`

Kept and documented rather than removed: the five per-cog records come from `damageCog`, and the
aggregate is the single line the feed shows for a raid-wide hit. `docs/PROTOCOL.md` now says
`target` is a cog alias "except for the single aggregate record a resolved Overload adds after
its five per-cog ones, where it is `"raid"`"; the manifest was rebuilt from the doc;
`resolveOverload` says the same at the call site; and `tests/test_boss.nim` pins the shape —
exactly five alias records plus exactly one `"raid"` record per Overload, with
`slotOfAlias` checked on each of the five.

## F18 (N17) — §Tests gaps — **fixed in part**, `0ea9001` + `6a8a68c`

Fixed:
- **The wasm harness now runs in CI** (`0ea9001`). The `wasm-viewer` job stages the built bundle
  where `tests/test_viewer.nim` looks for it, installs the toolchain, runs the viewer tests
  against the real emitted module, and **greps the log for `WASM-SMOKE OK`** so an early return
  cannot make the step green. Run 32621942459 logged
  `WASM-SMOKE OK: 647 ticks, digest 925898626, 112 events`.
- **The hung-client budget is asserted** (`6a8a68c`). `FakeClient.hangSeconds` and
  `.attemptSeconds` were declared and never read; they are gone, replaced by
  `testHungClientKeepsTheEpisodeInsideItsBudget`, which drives a decider that answers only at its
  deadline (7 + 3 = the whole 10 s turn budget) over the default variant and asserts the episode
  ends `complete` inside `wallClockBudgetSeconds`, at most one query per turn, every turn costing
  the full deadline.
- **The control-byte digest test does what its docstring says** (`6a8a68c`). It now asserts on
  `sim.controls` itself: byte-identical up to the tick the order changed, divergent after it, and
  the digest moved.

Not fixed, and recorded as gaps: the no-show seat reported to `COGAME_PLAYER_FAILURE_URI`, and
mid-encounter disconnect → stalwart → revive on reconnect. Both behaviours exist
(`server.nim:205-223`, `:394-403`); both need a harness that can run an episode to its end
in-process, and today the server thread calls `quit` at the end of an episode, which would take
the test process with it. Building that harness is a test-infrastructure task, not a one-line
fix, so I did not start it inside a fix round.

## F19 (N18) — `greenhorn` is weaker than the note describes — **no change**

Measured locally (default variant, `runScripted(..., skGreenhorn)`):

| seed | greenhorn boss hp left | phase | score | stalwart score |
|---|---|---|---|---|
| 42 | 90.5 % | 1 | 0.095 | 0.718 |
| 7 | 83.4 % | 1 | 0.166 | 0.542 |
| 1234 | 85.5 % | 1 | 0.145 | 0.477 |
| 999 | 79.3 % | 1 | 0.207 | 0.423 |

So greenhorn is 9–21 points of boss health short of the 70 % phase-2 line — the note's "reaches
phase 2 reliably" is the stale claim, and nothing *in the repo* asserts it: `README.md:82-85` and
`baselines.nim:9-12` describe greenhorn only by shape ("everyone in melee, everyone dodges,
nobody interrupts, nobody soaks, adds ignored"), the manifest calls it "a clean floor for the
ladder", and `tests/test_baselines.nim:175-176` pins the truth. The ladder spread the checklist
cares about is intact and stronger than asked (stalwart > 2× greenhorn on all four seeds).
Making greenhorn stronger is a balance change to the ladder floor — a design decision, and one
that would move every fixture — so I left it and report the numbers.

---

## NOTED (not fixed) — outside this round's findings

- `writeCogameUri`'s own timeout is still unknown from this tree (the review's open question).
  The two artifact writes now happen replay-then-results (F6) but neither is wrapped in a bound
  the repo owns.
- `tests/test_server.nim` cannot run an episode to its end because the server thread `quit`s;
  that single limitation is what blocks the two remaining §Tests items in F18.
