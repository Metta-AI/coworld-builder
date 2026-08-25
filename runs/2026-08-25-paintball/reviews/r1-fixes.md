# r1 fixes — 2026-08-25-paintball

Repo: `Metta-AI/cogame-paintball`, branch `main`. Reviewed at
`27f30578453d1c781c61693c7556ed4217ea22ec`; 23 commits on top, one per finding.

Head: `44af4da75e82daa73717f036a7b06934515db022`
CI: https://github.com/Metta-AI/cogame-paintball/actions/runs/32843017748 — **success**
(jobs `test`, `docker-smoke`, `wasm-viewer`; see “CI evidence” at the end for the step-level
readouts, including the new grid-harness, integer-only and renderer-fixture steps).

Every fix was compiled and run locally before pushing: this round's fixer installed the CI
toolchain in the sandbox (`nimby 0.1.26` + Nim 2.2.4 + `nimby --global sync nimby.lock`, plus
Playwright 1.55.0 + chromium), so every Nim test and the browser fixture were executed here
first rather than guessed at through CI.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | fixed | `82a7395` | `replay-viewer/static_replay.js:8-30`, `tests/test_viewer.nim:133-152` |
| F2 | fixed | `e8b42cd` | `tests/test_control.nim:118-176` |
| F3 | fixed | `1dddbb1`, `6cb57ad` | `src/paintball/global.nim:3942-3964,4046-4056,4922-4944,6022,6156`, `replay-viewer/text_fixture.html`, `tools/record_text_fixture.nim`, `tests/test_shouts.nim`, `.github/workflows/ci.yml:171-196,352-400` |
| F4 | fixed | `716e1c7` | `src/paintball/server.nim:67-77`, `docs/PROTOCOL.md:15-22`, `coworld_manifest_template.json`, `tests/test_manifest.nim:127-150` |
| F5 | fixed | `b2a6c3b` (harness) + `3cc3726` (test) | `src/paintball/baselines.nim:25-52`, `tools/tune_baselines.nim`, `tools/ci/baseline_tuning.json`, `.github/workflows/ci.yml:152-160`, `tests/test_replay.nim:12-90,136-176` |
| F6 | fixed | `55bbb88` | `src/paintball/sim.nim:161-200`, `tests/test_startup.nim:74-116` |
| F7 | fixed | `be21ff8` | `src/paintball/replays.nim:460-491`, `tests/test_replay.nim:228-249` |
| F8 | fixed | `3341bae` | `src/paintball/replays.nim:49-54,513-530,560-570,610-640`, `src/paintball/broadcast.nim:774,869-886`, `src/paintball/replay_runtime.nim:127`, `tests/test_replay.nim:251-287` |
| F9 | fixed | `4905f7a` | `src/paintball/llm.nim:163-182`, `tests/test_directives.nim:137-164` |
| F10 | fixed | `068b663` | `src/paintball/decide.nim:399-408`, `tests/test_engine.nim:28-42` |
| F11 | **NEEDS-DESIGN** | — | `src/paintball/decide.nim:316-319` |
| F12 | fixed | `fef02d9` | `src/paintball/decide.nim:353-384`, `tests/test_engine.nim:55-96,105-120` |
| F13 | fixed | `13ee73f` | `src/paintball/directives.nim:41-46,262`, `src/paintball/decide.nim:269-304`, `tests/test_directives.nim:166-230` |
| F14 | **DISPUTED** | — | `src/paintball/control.nim:335-348,18-33,55-59` |
| F15 | NOTED (not fixed) | — | `src/paintball/directives.nim:243-260` |
| F16 | fixed | `d66e85c` | `src/paintball/broadcast.nim:30-46,60-85,205-235`, `client/replay_broadcast.html:4151-4166`, `tests/test_replay.nim:196-206`, `tests/test_viewer.nim:132-141` |
| F17 | fixed | `c85c986` | `src/paintball/paint.nim:236-258`, `src/paintball/decide.nim:86-93`, `tests/test_hill.nim:100-130` |
| F18 | fixed | `0fa55c9` | `.github/workflows/coworld-release.yml:167-180`, `tests/test_startup.nim:118-128` |
| F19 | fixed | `7cf6f0f` | `src/paintball/replays.nim:336-352` |
| F20 | fixed | `2f75f2f` | `tests/test_regimes.nim:40-84` |
| F21 | partly fixed | `44af4da` | `.github/workflows/ci.yml:161-179` |
| F22 | NOTED (not fixed) | — | `src/paintball/roster.nim:727-732` |
| F23 | NOTED (not fixed) | — | `data/` |
| F24 | fixed | `118b1c5` | `src/paintball/llm.nim:122-127`, `src/paintball/decide.nim:434-437,455-458`, `tests/test_engine.nim:122-134` |
| F25 | NOTED (not fixed) | — | `src/paintball/sim.nim:1177-1263` |
| F26 | fixed | `e87f907` | `src/paintball/broadcast.nim:41-43,92-102,176-196`, `tests/test_hill.nim:132-168` |
| F27 | fixed | `b3bd645` | `src/paintball/sim_types.nim:769-777`, `src/paintball/paint.nim:208-234`, `src/paintball/sim.nim:4067-4074`, `src/paintball/server.nim:1946-1968`, `tests/test_scoring.nim:80-116` |

Counts of the 27 findings: **20 fixed** (F1–F10, F12, F13, F16–F20, F24, F26, F27 — F3 and F5 in
two commits each), **1 partly fixed** (F21: the missing CI grep added, the untested §Tests 8
behaviours noted), **1 DISPUTED** (F14), **1 NEEDS-DESIGN** (F11), **4 noted and deliberately not
fixed** (F15, F22, F23, F25). Every one of the five claimed checklist-level findings (F1–F5) is
fixed, none refuted.

---

## F1 — `data-replay-error` is never set anywhere in the repo — FIXED (`82a7395`)

**Was:** `showFailure()` wrote `console.error`, set `#status`'s text and added `.show`. It never
touched `document.documentElement`, so all six failure paths (no OffscreenCanvas, a failed
`transferControlToOffscreen`, a missing `?replay=`, a Worker `error` message, `worker.onerror`,
`onmessageerror`) degraded to `viewer_smoke.mjs`'s 90 s timeout instead of the immediate named
failure its `:503` branch exists for.

**Now:** `showFailure()` sets `data-replay-error="<message>"` on `<html>` as its first act, before
touching `#status`. `data-replay-loaded="true"` is untouched and still set only from the Worker's
`'loaded'` message, which the Worker posts after `ingestPacket()` has handed BroadcastCore the
first frame — CI run 32843017748's `Load the bundle in a real browser` step reports
`{"loaded":true,...}`, so the load marker still fires from the first drawn frame.

**Evidence:** `tests/test_viewer.nim` "the shell sets BOTH load and failure markers on `<html>`"
asserts both attribute names appear and that each is inside the branch that means it (the error
attribute between `showFailure` and `setMismatchTick`, the loaded attribute after the
`'loaded'` message test). Green in the `test` job, both debug and release.

**Checklist item:** 13, second bullet.

## F2 — two assertions deleted from `tests/` during this run — FIXED (`e8b42cd`)

**Was:** `check flips >= 2` (design §Tests 6's "the hill changes hands at least twice") was
deleted in `cd402ea`, and the baseline-ordering check `sim.hillTicks[Red] * 2 >=
sim.hillTicks[Blue]` in `73aa441`. The reason they were deleted rather than satisfied is in the
same CI log: with the untuned baseline radii `sprayer` banked 733 hill ticks to `holdline`'s 0 —
the inverse of the design's ordering — and a single sweeping squad only ever took the hill once,
so a flip count of 2 was unreachable in that fixture.

**Now:** both properties are asserted again, and the code satisfies them rather than the test
being shaped around the code. `tests/test_control.nim` carries two tests:

- *"holdline beats sprayer at seed 679961, and the hill changes hands twice"* — the design's own
  fixture, asserted literally: the episode completes (`endReason in ["", complete]`), both squads
  lay floor paint, `holdline` out-banks `sprayer` (**57 : 44** hill ticks) and the hill changes
  hands **12** times, against the 2 the note asks for.
- *"holdline out-banks sprayer over the tuned ladder, from both sides"* — the same ordering as a
  ladder property: three seeds × both sides of the mirror-symmetric arena, `holdline` taking a
  majority (**5 of 6**) with a positive aggregate margin (**+1762** hill ticks) and at least half
  the episodes contesting the hill twice or more (the anti-stalemate invariant).

Both measure through `tools/tune_baselines.nim`'s driver — the same code the grid harness tunes
with — so the test and the sweep that chose the parameters cannot disagree. What made the ordering
true is F5's tuning, not a weaker assertion. The per-colour takeability test (`cd402ea`'s
replacement) is untouched and still passes.

**Evidence:** local `nim r --path:src tests/test_control.nim`, debug and release, and the `test`
job of the cited run; the numbers above are the test's own echo lines.

**Checklist item:** 1 ("no test disabled, skipped, or loosened").

## F3 — LLM-authored text, a text gate measuring nothing, no worst-case fixture — FIXED (`1dddbb1`, `6cb57ad`)

**Was:** a cog's `say` becomes a real in-game shout and the board drew its bubble at
`tailTipY - bubbleHeight` in map space, unclamped, into a map-sized layer canvas. A cog standing
on the arena's top row therefore placed its bubble at a negative y, where the canvas clips it to a
sliver — the cogchemists defect of 2026-08-24 verbatim. Nothing could see it: the bubble text is
rasterised into a sprite in Nim, so `viewer_smoke.mjs`'s `fillText` hook reported
`canvas text: 0 drawn`, which the checklist and the harness both call evidence of nothing.

**Now**, three things:

1. **The defect.** `global.shoutBubblePlacement` is the single place a bubble is positioned and
   is used by **both** draw passes (the board pass and the player-stream pass, which had the same
   unclamped geometry): it flips the bubble below the tail tip when it does not fit above and
   clamps both axes into the board rect. `global.shoutBubbleMaxHeight` is the reserved band,
   measured from the server's own `ShoutMaxChars` cap in the font it will be drawn in — 19 px on
   this board — rather than sized by eye. Nothing hashed changed.
2. **A tree-level gate.** `tests/test_shouts.nim` asks the draw pass's own geometry where every
   worst-case bubble lands: a full-cap bubble on **every cog at once** at nine worst positions is
   wholly inside the board; a top-row bubble moves instead of clipping; a bubble with room above
   it is not moved at all (so the clamp is a clamp, not a squash); and every `say` the scripted
   baselines emit fits at every edge position.
3. **The worst-case renderer fixture**, in its own `ci.yml` step.
   `tools/record_text_fixture.nim` (run in the `test` job, which has Nim; uploaded as an
   artifact, so none of it ships in the hosted bundle) builds a real Sprite v1 **board packet**
   for a frame built to hurt — all eight cogs shouting the full 10-rune cap through the server's
   own `applyShout`, standing on the whole top row, both side walls and the bottom edge — plus
   the identical frame with nothing shouting, plus each bubble's expected map-space rect straight
   out of `shoutBubbleRectFor`. `replay-viewer/text_fixture.html` loads the **real**
   `client/broadcast_core.js` out of the built bundle (the same file the static viewer's Worker
   imports, byte-identical to the starter's apart from the wire identifier), renders both packets
   at **360×640, 720×480 and 1280×800**, and per bubble asserts: the rect is inside the board; it
   maps inside the canvas; the two frames **differ inside it** (a clipped or missing bubble fails
   on pixels); and nearly all the difference between the two frames falls inside those rects, so a
   bubble cannot pass by being drawn somewhere else. It re-checks that its own strings are still
   the full 10 runes — a quietly shortened remark would leave it passing while testing nothing.
   Failure sets `data-replay-error`; success sets `data-replay-loaded`. `ci.yml`'s `wasm-viewer`
   job drives it with `node tools/ci/viewer_smoke.mjs --bundle dist/text-fixture --replay
   dist/text-fixture/text_fixture_shout.bin --timeout 90 --strict-text-bounds`.

`canvas_text.total` is **still 0** for this fixture and that is stated in the step's own comment:
this engine draws no canvas text at all, so the fixture's pixel-difference assertions are the
gate, not the hook. `6cb57ad` writes the fixture's measurements into `#clock`, which
`viewer_smoke.mjs` prints on stdout, so the step log carries them.

**Evidence** (CI run 32840051313, `Render the worst-case text fixture`, and identically locally):

```
fixture: 8 shouts of 10 runes, board 1235x659, reserved band 19 px
  360x640: scale 0.146, 8/8 bubbles in frame, weakest changed 86 px, 0/702 changed px stray
  720x480: scale 0.291, 8/8 bubbles in frame, weakest changed 389 px, 0/3121 changed px stray
  1280x800: scale 0.518, 8/8 bubbles in frame, weakest changed 1159 px, 0/9660 changed px stray
OK every worst-case bubble rendered inside the frame at every size
```

The step's screenshot artifact (`text-fixture-smoke`) shows all eight full-cap bubbles legible
inside the frame, including the five on the top row and the one on the bottom edge.

**Checklist item:** 15 (both the reserved-band bullet and the worst-case-fixture bullet).

## F4 — a live `/client/replay` pod viewer route, documented in the manifest — FIXED (`716e1c7`)

**Was:** `server.nim` served `client/replay_broadcast.html` at bitworld's `/client/replay` and
`/clients/replay`, plus the League Replayer shell at `/client/league`; `docs/PROTOCOL.md`
declared those routes as part of the contract, inlined verbatim into `game.protocols.player`,
`game.protocols.global` and `game.docs.pages[protocol]`.

**Now:** the three routes, both embedded pages and the now-callerless `queueReplayUri` are
deleted. Nothing needed them — the manifest declares the static bundle, the bundle is built from
the same page by `Dockerfile.replay-viewer`, and `coworld-release.yml` refuses to certify a
pod-served viewer. The replay **websocket** path (`/replay`, replay-server mode) is untouched and
still takes its artifact URI from the boot env or a queued switch. `docs/PROTOCOL.md` now lists
only `/client/global` and `/client/player` and states that there is deliberately no replay page
on the pod; the manifest's three inlined copies were regenerated from it.

**Evidence:** `tests/test_manifest.nim` "nothing shipped declares or serves a `/client/replay` pod
path" asserts no `/client/replay` in the protocol doc, in `game.protocols` or in `game.docs`, and
no `ReplayClientRoute`/`CoworldReplayClientRoute`/`EmbeddedBroadcastReplayHtml`/`/client/league`
left in `server.nim` with comment lines stripped first — so the comment that explains the removal
cannot pass for the route. The production binary still builds (`docker-smoke` played a full
episode on the pushed head).

**Residue, stated plainly:** two mentions of the string survive in files item 14 forbids editing —
`client/broadcast_core.js:196` (byte-identical to the starter's) and
`client/replay_broadcast.html:1511-1512` (the starter's own route-prefix comments) — plus
`client/league_replayer.html`, which is inherited chrome the design note lists as kept and which
the static bundle still builds as `league.html`. None is a pod path: the pod serves no replay page
at all now. A literal repo-wide grep cannot reach zero without violating item 14's byte-identity
requirement.

**Checklist item:** 3.

## F5 — item 7's two clauses — FIXED (`b2a6c3b` + `3cc3726`)

**Clause 1 (`reason == "complete"` and legal orders), `3cc3726`.** The end-to-end episode test
accepted `reason` as any of complete/deadline/fault — it passed whether the episode finished or
died — and the filler test accepted `""`. It now plays the two-game all-scripted episode to its
natural end and asserts `results.reason == "complete"`, `endRule` in the rules' own enum,
`games == 2`, `finalTick` past the first game, **and** that every order the baselines issued and
every actuator mask the control layer compiled was inside its legal bounds, on the real episode
rather than only on `test_control`'s 500 synthetic states (exactly the commanded cogs, ids
matching the seat's aliases, intents in the enum, targets and faces inside the map, the
note/say/id rune caps, never Up+Down, never Left+Right, never `C`).

Measured: `episode: reason=complete endRule=full_time games=2 finalTick=486 orders=30
masks=3840`, violations **0**.

**Clause 2 (a grid harness, not guesses), `b2a6c3b`.** The three tunables are now
`BaselineParams`, and `tools/tune_baselines.nim` is the harness: a bounded 4×4 matrix, each cell a
ladder of three seeds played from **both sides** of the mirror-symmetric arena (96 episodes),
scored by episodes won with the hill-tick margin as the tiebreak. `ci.yml`'s `test` job runs it
with `--check`, which fails if the sweep's winner is no longer what `baselines.nim` ships or what
the recorded `tools/ci/baseline_tuning.json` says. The sweep **moved the numbers**, which is the
point — the note's first guess loses 5 of 6:

```
  huntHoldline  guardStandoff |  wins  margin  flips
           130            110 |  5/6    1762     86   <- shipped
           150            120 |  5/6    1188     57
           200            250 |  1/6   -2113     77   <- the note's guess
```

A 250 px guard standoff leaves `holdline` painting three cogs against `sprayer`'s four, and a wide
hunt radius pulls its hill cogs off the square to chase; pulling both in restores the ordering the
note names, which is what let F2's assertions come back.

**Checklist item:** 7, both sentences.

## F6 — pickups placed and drawn under the paintball loadout — FIXED (`55bbb88`)

None of the five reset procs had a loadout gate, so every paintball game spawned the starter's
whole item set. Nothing could be *taken* (the pickup path is gated), but the spawns were reported
in each seat's first-person item list, listed as spectator map items and drawn by five board
passes — visible as paint-bomb orbs, med kits and shields in F3's own fixture screenshot, i.e. in
the LLM's view and in the picture. `placeWalkablePickups` now empties its family under the
paintball loadout and `resetGrenades` marks its fixed-size corner array `present: false`; every
consumer already keys off exactly those two things. `tests/test_startup.nim` asserts both
directions — nothing placed under `loadout: "paintball"` with the can still in every cog's hand,
and the starter's pickups still placed under `loadout: "ctf"`, so the gate composes.

## F7 — `gameIndex`/`regime` frozen in playback — FIXED (`be21ff8`)

`stepReplay` now mirrors the server's named edit #4 at the same place the live loop does it: on
the tick the phase becomes `GameOver` it archives `hillTicks` into `gameHill`, records the regime
played and arms the next game's. Neither field is in `gameHash`, and keyframes carry the whole
sim, so a seek restores them. `tests/test_replay.nim` re-simulates the two-game episode and
asserts the visitor regime is reached and `gameRegimes == @[resident, visitor]`.

## F8 — momentum graph plotted lives — FIXED (`3341bae`)

`scanTeamHillTicks` replaces `scanTeamLives`: the series carries each team's **cumulative** hill
ticks (archived games plus the running game), which the inherited two-team renderer already plots
as a difference around its midline. The field is renamed `leadSeries` so the next reader is not
told it is lives. `tests/test_replay.nim` asserts the series is monotone and that its final point
equals the archived hill totals — an equality a lives series cannot satisfy.

## F9 — byte-index slice on a provider body — FIXED (`4905f7a`)

All three sites in `llm.textOf` now cut with `truncateRunes(MaxFallbackDetailRunes)`.
`tests/test_directives.nim` feeds a body of 4-byte emoji through both the 429 and the auth path
and asserts the raised message is valid UTF-8 and JSON-round-trips. **Checklist item 9.**

## F10 — attempt-1 transport deadline effectively 5 s — FIXED (`068b663`)

The conversion to curly's whole seconds now **floors** instead of rounding up, so the transport
deadline is never longer than the configured one and a twice-timed-out turn is 4 + 2 = 6 s against
the note's 6.5 s worst case and the 7.0 s cap. `tests/test_engine.nim` pins the property rather
than the tautology it had (7.0 ≤ 7.0): the rounded pair must not exceed the configured pair, must
fit 6.5 s, and must be strictly inside `turnBudgetMs`.

## F11 — `turnSpacingMs` is a blocking sleep on the game loop — NEEDS-DESIGN (no change)

The finding is **real**: `decide.turn` calls `os.sleep` on the loop thread, and the note says the
floor "is a floor, **not** a sleep on the critical path: the loop keeps stepping sim ticks while
it waits".

I did not change it, because the note's own budget arithmetic depends on the sleep. With
`fastMode: true` the server advances a tick as soon as both seats ack, so an episode of
2 × 2160 ticks runs in ~25 s of wall clock and a turn boundary arrives roughly every 1.2 s. Make
the floor non-blocking — defer the batch and keep stepping — and only about one boundary in four
can issue a batch: **~10 LLM calls per episode instead of 80**, the model commanding the squad
about an eighth as often, and the note's "40 turns × 5.0 s spacing floor = 200 s" line becomes
false. The blocking sleep is what paces the episode to the 260 s the note books.

Both readings cannot hold at once, and choosing between them changes what the game *is* (how
often a commander speaks), so it belongs to the design note, not to a fixer. The wait is bounded
(`turnSpacingMs`, 5000 ms), the arithmetic already books it, mummy's serve thread is separate so
no socket drops, and the 690 s engine stop still covers it — so nothing here is a hang.

**What the change would be, if the note picks the non-blocking reading:** a `pendingTurn` flag on
the engine plus `batchFloorRemainingMs`, with the server setting the flag at a turn boundary and
issuing the batch on the first later tick the floor allows (last turn's directives keep every cog
actuated meanwhile) — and the note's cadence/budget paragraph rewritten to say that turns are
*skipped* rather than paced, with a new expected call count.

## F12 — no fallback record for `no_credentials` / `budget_guard` — FIXED (`fef02d9`)

An LLM seat that cannot call the LLM this turn now plays the holdline directive as a `dsFallback`
with a recorded cause (`budget_guard` once the guard has fired, `no_credentials` otherwise), so
both causes in the design's enum are reachable and countable; a seat that registered as
**scripted** records nothing, so certification's two baseline seats still write none. Before this,
an LLM seat with no key reported `llmTurns` 0 **and** `fallbackTurns` 0 and
`replay_summary.py`'s `fallbacks` was 0 for an episode in which every turn was a fallback — the
number phase 60 reads to tell "the model played" from "the model never answered".

**Two existing assertions changed**, deliberately and upward, and I flag it explicitly so the
judge can weigh it: `check records.len == 0  ## a disabled client is not a fallback` and
`check after.len == 0` pinned the unreachable path as correct. They now assert the records exist
*and* carry the right cause, plus a new test pins that a scripted seat is never counted as a
fallback. Nothing was widened or removed.

## F13 — a missing cog defaulted to `paint_hill` at the hill centre — FIXED (`13ee73f`)

`CogOrder` now carries `fromReply`, set only where a reply entry really matched a cog, and
`decide.repairMissingOrders` replaces every unmatched order with that cog's order from **last
turn**, or with **holdline's** order for it when the seat has no history — the design's rule.
Extra entries are still dropped and no cog is left unactuated. `tests/test_directives.nim` plays
two turns: a guard named on turn 1 and omitted on turn 2 keeps guarding its own point, and with no
history every unnamed cog matches holdline's order for it exactly.

## F14 — `paint_hill` walks to the FARTHEST non-own hill tile — DISPUTED (no change)

The observation is accurate; the conclusion that it is a defect is not. `control.nim:335-348`
documents the measured reason, and it is load-bearing for the design's own anti-stalemate
property: the cone starts **at** the cog and reaches forward, so a cog can never paint the tile it
is standing on. Sending it to the *nearest* non-own tile parks it on that tile forever — measured
in this run, four cogs converged on the western rim and the squad plateaued at **13 of 21** hill
tiles, i.e. below the 80 % threshold, so the hill was structurally untakeable and every episode
was a 0.500 draw. With `farthestHillTile` both colours reach **100 %** coverage from a fresh board
(`tests/test_control.nim`, "either squad can take the hill": `peak coverage 100% (need 80%)`,
21 of 21 tiles, per colour).

The same applies to the two numbers alongside it: `PaintProbeSteps = [34,68,102,136,170]` samples
the cone's whole reach instead of one point 85 px out (a single probe misses both the tile under
the cog's nose and the far end), and `NavCell = 12` is sized to the arena's ~26 px corridors — at
the note's 34 px there is no open cell anywhere inside a gap between two obstacle columns, the
flow field calls the whole far side unreachable, and a sweeping squad pressed one d-pad direction
into a wall for two thousand ticks (that is the regression `cd402ea`'s per-colour test was written
to catch).

So the code is right and the **note is stale on all three numbers**. Reverting any of them
re-breaks §Tests 6's own anti-stalemate pin. Recorded here rather than fixed; the design note
wants the amendment, not the code.

## F15 — `cogs[].id ≤ 12 runes` not enforced on parse — NOTED (not fixed)

Accurate and unobservable: the parser matches the model's id case-insensitively and then discards
it, writing the seat's own alias into the order (`directives.nim:243-260`), so no over-long id can
reach the replay or the sim. Adding a cap with nothing behind it would be a decoration; the tests
already assert `order.id == sim.cogAlias(order.cogIndex)` and `id.runeLen <= MaxCogIdRunes` on
every issued order (`tests/test_control.nim:23-24`, and now on a whole real episode via F5's
`orderViolations`).

## F16 — `spray`, `tag` and `heal` never emitted — FIXED (`d66e85c`)

All three are now derived from tracker deltas (`arcTicksLeft` 0 → firing, hp down while alive, hp
up while alive), so they cost no replay bytes and read identically live and in replay. The `tag`
gap was the substantive one: at 3 hit points and `sprayDamage: 1` **most** sprays that connect are
a tag, not a tagout, and the feed had no row for the common case — a spectator watched a cog lose
two thirds of its health in silence. The appended game block routes them (`tag` gets a feed row,
`spray`/`heal` are continuous colour the board already shows). `tests/test_replay.nim` asserts
`spray` and `tag` appear in a real episode's derived kinds (measured: `paint, spray, tag, kill,
tagout, respawn, heal, phase, gameover, gamestart`) and `tests/test_viewer.nim` pins that the page
names every kind the sim emits.

## F17 — the hill box reported to the LLM was 12 px off — FIXED (`c85c986`)

`paint.hillPixelBox` derives the box from the hill's own tile list, so it cannot drift from the
tiles ownership is computed over. Measured: `hill box [544, 238, 713, 407] for 25 tiles of 34 px`
— the design note's own numbers, where the old centre-derived box said `[532,244,702,414]`.
`tests/test_hill.nim` asserts it equals the tile block, contains every hill tile centre, stays
inside the map and spans exactly five tiles each way.

## F18 — `certify` carried no `--timeout-seconds` — FIXED (`0fa55c9`)

`coworld-release.yml`'s certify step now passes `--timeout-seconds 300`, the value the note pins;
`tests/test_startup.nim` asserts the flag is on the certify step and not confused with the upload
step's 900.

## F19 — a leave still shifted the mask arrays — FIXED (`7cf6f0f`)

The design's second named edit to `replays.nim` is made: the roster entry is still removed, the
cog mask slots stay put. Masks are indexed by **cog** and cogs are fixed for the episode, so
deleting a row re-pointed every mask after it at the wrong cog for the rest of playback — silent,
and visible only as a hash divergence at a tick nothing else explains. Unreachable in a normal
episode (a dropped seat writes no leave), reachable from a `/global` kick, which is exactly the
case this protects. No test: constructing a replay that carries a mid-episode kick means writing
one by hand whose hash chain diverges for the very reason under test; the change is a deletion of
four `delete` calls and the reasoning is in the comment.

## F20 — the "byte-for-byte holdline" test was a tautology — FIXED (`2f75f2f`)

It built both sides with the identical call. It now performs the server's own dispatch against a
seat directive that is a `fall_back` to the far corner — an order whose compiled mask is visibly
different from holdline's hill work — and asserts alpha takes it, the other three do not, and at
least one of them compiles a different byte from what the seat asked for. A leak of alpha's
directive into its partners now fails the test.

## F21 — several §Tests items absent — PARTLY FIXED (`44af4da`)

Fixed: the missing **CI grep** for floats in the new hashed arithmetic, scoped the way AGENTS.md
rule 1 already scopes the requirement — `paint.nim`, the only new module inside the hash, with
comment lines stripped so the file's own explanation of the rule cannot read as a violation.
(The note's wider file list cannot pass as written: `control.nim` is outside the determinism
boundary and navigates in floats on purpose, and the inherited `sim.nim` has floats of its own.)

Not fixed, NOTED: the `paintBuff: false` tick-by-tick `gameHash` comparison (§Tests 2) and the
five untested engine behaviours (§Tests 8 — the hung client, the 690 s stop, a disconnected seat
reviving, the never-connecting seat's `COGAME_PLAYER_FAILURE_URI` report). F27 below adds the
sixth of them (`fault/sim_fault`). Each of the rest needs a fake socket layer or a wall-clock
harness this round did not build; none is named by a checklist item.

## F22 — `paintTiles`/`tagsDealt`/`tagsTaken` count only the last game — NOTED (not fixed)

Accurate. Whether they should be per-episode is genuinely undecided by the note (its results
example does not say, and `hillTicks`/`residentHillTicks`/`visitorHillTicks` — the three keys the
score is computed from — do accumulate correctly). Making them per-episode means archiving three
more per-game counter arrays; making them per-game means saying so in the schema description.
Either is a note decision, and neither changes a score.

## F23 — the art the note says to delete is still in `data/` — NOTED (not fixed)

Accurate, and now *more* clearly out of scope: after F6 nothing is placed, but the five inherited
draw passes still reference those sprites and would fail to compile without them, and the same art
is copied into the static bundle by `Dockerfile.replay-viewer`. Deleting art whose loaders are
inherited chrome is a wider change than a fixer should make in a review round; the mechanics are
gated off, which is what the loadout row is actually about.

## F24 — the phase-60 log greps do not match the printed strings — FIXED (`118b1c5`)

The no-credentials line now names the provider as unavailable ("the LLM provider is
unavailable"), the retry line says it is falling back if the second attempt fails too, and every
seat that actually falls back logs `falling back to holdline (<cause>) on turn N` beside the
record it writes. `tests/test_engine.nim` pins both phrases, so the documented phase-60
verification greps for strings the code really prints.

## F25 — cone painting and cone damage interleave per cone — NOTED (not fixed)

Accurate against §Resolution order 6.3/6.4. Both orders are deterministic and identical on native
and wasm (one code path), `arcFires` is built in cog index order, and the only observable
difference is whether a cog killed by an earlier cone still paints on the tick it dies. Splitting
the loop in two is a change to the hashed path — it moves `gameHash` for every existing replay and
requires a `GameVersion` bump — for an effect the note does not claim to depend on. That trade
belongs to the note; I left the hashed path alone in a round where nothing else touched it.

## F26 — the `hillflip` throttle was not applied to the derived event — FIXED (`e87f907`)

The derived broadcast event is now throttled like the sim's own (one per `HillFlipThrottleTicks`),
compared against the last **announced** owner rather than last tick's, so a change landing inside
the window is announced on the first tick the window allows instead of being dropped. The window
state resets on the first frame and on every seek, not on every snapshot — `snapshot` runs per
tick, and refreshing it there would have made the throttle a no-op (it did, in my first attempt;
the test caught it). `tests/test_hill.nim` hands the hill back and forth every tick and asserts
exactly one announcement, none inside the window, and one on the first tick past it.

## F27 — the `fault` end conditions were unreachable — FIXED (`b3bd645`)

`paint.checkPaintInvariants` is the guard the note names — the paint grid matching its own
dimensions, both teams' incremental `paintCount`/`hillPaint` inside the bounds they count against,
and no living cog outside the map — integer-only, O(cogs), run once per tick under the paint gates
immediately before the counters are used to end a game. `server.nim` wraps the tick: a
`SimGuardError` ends the episode `fault`/`sim_fault`, any other exception out of the tick ends it
`fault`/`host_error`, and either way the existing artifact block still writes the partial replay,
the results and the events before the bounded shutdown grace — so the runner reads a scored
0.500/0.500 episode instead of the non-zero exit with no `results.json` it got before.
`tests/test_scoring.nim` asserts the guard passes on a healthy sim, raises on a drifted hill
counter and on a cog off the map, raises through the real `sim.step` path, and that the fault
results document is 0.500/0.500 with both `win` false.

---

## NOTED (not fixed) — things seen while in here, deliberately left alone

- **`holdline` drives the visitor's partners one cog at a time.** `server.nim:1905` computes
  `holdlineFor(sim, @[cogIndex])` per uncommanded cog **per tick**, so each partner is ranked as a
  lone holdline cog (always `hold_hill`) rather than as the group of three the note describes,
  and its directive is recomputed every tick instead of on the 4.5 s cadence. Neither is a defect
  the review names, both change what the visitor half plays, and both need the note to say which
  it wants. F20's test now pins the current dispatch honestly rather than tautologically.
- **`tools/ci/docker_smoke.sh` prints `reason` without comparing it.** F5's test now gates on
  `complete` in the Nim suite; gating the shared smoke script as well would be a second, better
  place for it, but it is scaffold shared across coworlds and I left it alone.
- **`client/league_replayer.html` is now unreachable from the pod** (F4 removed its route) while
  still being built into the static bundle as `league.html`. It is inherited chrome the note lists
  as kept; deleting it is a note decision.

## CI evidence

`gh run list -R Metta-AI/cogame-paintball --branch main -w ci.yml` → run **32843017748**,
conclusion **`success`**, `headSha 44af4da75e82daa73717f036a7b06934515db022`, event `push`
(https://github.com/Metta-AI/cogame-paintball/actions/runs/32843017748). All three jobs green,
every step `success`, nothing `continue-on-error`, nothing skipped.
`gh run view 32843017748 --log | grep -c SEAT-COUNT` → **0**.

Lines from that run's log, per finding:

```
docker-smoke  Raw-Docker episode smoke      episode end reason: complete
docker-smoke  Raw-Docker episode smoke      smoke OK: seats=2 results=414B replay=36160B reason=complete
test          Baseline parameter grid harness  sweep pick: huntRadiusHoldline=130 huntRadiusSprayer=120
                                               guardStandoff=110 (5/6 episodes, margin 1762)          [F5]
test          Baseline parameter grid harness  tune_baselines: OK — the shipped defaults are this sweep's pick
test          Assert the new hashed arithmetic is integer-only   paint.nim: no floating point          [F21]
wasm-viewer   Load the bundle in a real browser   {"loaded":true,"ms":1328,...}                        [item 13]
wasm-viewer   Load the bundle in a real browser   scrub readouts: 0%="0:25 TIME LEFT GAME 1/2 · RESIDENT
                                                  · TURN 1/5"  50%="0:02 ... GAME 1/2 · RESIDENT · TURN 5/5"
                                                  100%="0:00 ... GAME 2/2 · VISITOR · TURN 5/5"        [F7]
wasm-viewer   Render the worst-case text fixture  {"loaded":true,"ms":2085,"clock":"360x640: scale 0.146,
                                                  8/8 bubbles in frame, weakest changed 86 px, 0/702 changed
                                                  px stray | 720x480: ... 389 px, 0/3121 | 1280x800: ...
                                                  1159 px, 0/9660"}                                    [F3]
wasm-viewer   Native/wasm hash gate              ok: advanced 300 frames, mismatch tick -1
```

The scrub readout line is F7's fix visible from outside: at the reviewed sha the same three
samples all read `GAME 1/2 · RESIDENT`, and the visitor half was never announced.

`canvas_text.total` is **0** in both browser steps and that is expected and stated: this engine
rasterises every string into a sprite in Nim (`grep -c 'fillText\|strokeText' client/broadcast_core.js`
→ 0), so the hook cannot count paintball's text at all. The renderer fixture's per-bubble
pixel-difference assertions (F3) are the gate that covers it, and `tests/test_shouts.nim` is the
tree-level half.

Jobs and the steps this round added:

- `test` — `Run tests` (every `tests/*.nim` in debug **and** release, 16 files including the new
  `tests/test_shouts.nim`), `Baseline parameter grid harness` (96 episodes, `--check`),
  `Assert the new hashed arithmetic is integer-only`, `Build the worst-case renderer fixture frame`
  (+ artifact upload).
- `docker-smoke` — unchanged: image build plus one real episode from the certification fixture.
- `wasm-viewer` — now `needs: [docker-smoke, test]`; `Load the bundle in a real browser`
  (`--strict-text-bounds`) as before, plus `Render the worst-case text fixture` (its own
  `viewer_smoke.mjs --strict-text-bounds` invocation) and its evidence artifact.
