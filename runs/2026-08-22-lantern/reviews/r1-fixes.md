# r1 fixes — lantern

Repo: `Metta-AI/cogame-lantern`, branch `main`.
Base: `06d4da71149c7581d940c1ccb371fec3467890aa` (the reviewed sha).
Head: **`024144dbaefb0ea9482b0bf274f23e0eb9c45f3a`**
CI: **https://github.com/Metta-AI/cogame-lantern/actions/runs/32612666063** — **success**
(`test`, `docker-smoke`, `wasm-viewer` all green on that sha; 34 `nim r` invocations, i.e. all
18 `tests/*.nim` twice, debug and `-d:release`). Every intermediate commit also went green:
`3a6c387`→32611657408, `428d12b`→32612110264, `d3bb406`→32612176078, `af94ca9`→32612206745,
`5d58402`→32612349233, `3e97c1f`→32612434130, `1a54b43`→32612525013 — all `success`.

No test was weakened, skipped or deleted. Three fixes add tests; one fixture
(`tests/fixtures/smoke_replay.json`) was re-recorded, in the same commit as the change that
moved it, with its controls and keyframes byte-identical (see F2).

| finding | disposition | commit (remote sha) | files |
|---|---|---|---|
| **F1** (blocking) | fixed | `3a6c387` | `src/lantern/llm.nim:171-197`, `tests/test_engine.nim:265-345` |
| item 7 "tuned with a grid harness" | fixed | `428d12b` | `tools/tune_baselines.nim`, `tests/fixtures/tuning_grid.json`, `tests/test_tuning.nim`, `src/lantern/baselines.nim:26-47`, `docs/tuning.md` |
| **F2** | fixed | `3e97c1f` | `src/lantern/sim.nim:419-437`, `tools/gen_manifest.py:196`, `coworld_manifest_template.json`, `tests/fixtures/smoke_replay.json` |
| **F3** | fixed | `5d58402` | `src/lantern/render.nim:118-129`, `src/lantern/sim.nim:54-57,577-580`, `src/lantern/types.nim:222-226`, `docs/PROTOCOL.md:88-95`, `tests/test_vision.nim:85-105` |
| **F4** | no change (reasoned) | — | `src/lantern/config.nim:19,22-23` |
| **F5** | fixed | `d3bb406` | `src/lantern/server.nim:137-156`, `tests/test_engine.nim:147-163` |
| **F6** | fixed (comment) | `af94ca9` | `src/lantern/control.nim:206-232` |
| **F7** | no change (reasoned) | — | `src/lantern/sim.nim:116-147` |
| **F8** | no change (reasoned) | — | `data/vault.mapspec.json` |
| **F9** | no change (the note is what is wrong) | — | `tools/build_replay_viewer.sh:66-71` |
| **F10** | no change (reasoned) | — | `src/lantern/events.nim:12-14` |
| **F11** | fixed | `1a54b43` | `replay-viewer/lantern_replay.nim:17-100`, `replay-viewer/static_replay_worker.js:105`, `tools/wasm_replay_smoke.cjs` |
| **F12** | no change (reasoned) | — | `client/chrome_common.js` |
| **F13** | fixed | `024144d` | `tests/test_determinism.nim:25-38` |
| **F14** | no change (coverage gap, off-checklist) | — | `tests/test_engine.nim:201-233` |
| **F15** | no change (reasoned) | — | `tests/test_viewer.nim:93-104` |
| **F16** | no change (reasoned) | — | `src/lantern/server.nim:214-252` |

---

## F1 — captured LLM error text reached the replay through byte-index slices  ·  fixed, `3a6c387`

**What it did.** All four slices in `textOf` were byte slices:
`response.body[0 .. min(response.body.high, 400)]` (401/403), `… 300]` (429), `… 300]`
(non-2xx) and `result[0 .. min(result.high, 160)]` (the model's own `max_tokens` text). The
message is captured verbatim by `curlySender`, copied into `FallbackNote.detail` by
`decideAll`, and emitted as a `fallback` event, where `clipRunes` returns any string of
≤ 200 runes unchanged — so a cut inside a codepoint made the whole replay invalid UTF-8.

**What it does now.** Every one of the four uses `orders.clip` (`runeSubStr`), the rune-boundary
helper the rest of the replay path already uses; the `max_tokens` case chains `orders.oneLine`
instead of `replace("\n", " ")`. `textOf` is now exported, with a doc comment saying why (the
tests drive it).

**Evidence.** New suite `captured provider errors are rune-safe all the way to the replay`
(`tests/test_engine.nim`), three cases, each driving the exact path the review traced —
`textOf` → `LlmReply.error` → `decideAll` → `FallbackNote.detail` → `fallbackEvent` →
`buildReplay` → bytes — and asserting `validateUtf8(bytes) == -1`, `validateUtf8(detail) == -1`
and `detail.runeLen <= MaxDetailRunes`:

* a 429 body of 400 × `🔦` (4-byte runes; byte 300 lands mid-rune);
* a 401 body of 500 × `€` (3-byte runes; byte 400 lands mid-rune);
* a 200 reply with `stop_reason: max_tokens` whose `content[0].text` is the model's own
  non-ASCII text (the most reachable of the four slices).

I verified the tests fail before the fix: with `textOf`'s four byte slices restored (and only
the export kept so the file compiles), the 429 and `max_tokens` cases fail with
`Check failed: validateUtf8(bytes) == -1` and six `Check failed: validateUtf8(detail) == -1`.
The 3-byte case is the one that proves the 400-byte slice too. Green in CI in both modes
(run 32612666063, `test` job, `[OK] a 429 body of 4-byte runes lands in the replay as valid UTF-8`
and siblings, twice each).

**Checklist item:** #9, the "captured errors" clause the review named as the one uncovered class.

---

## Item 7's second sentence — "tuned with a grid harness, not guessed"  ·  fixed, `428d12b`

The review filed this under "could not determine": no harness, sweep script or tuning record
existed anywhere in the tree. There is one now, and the shipped parameters are its output
rather than the note's hand-picked numbers.

**The knobs.** The warden's three tunable numbers became `baselines.WardenParams`
(`coverageGatePct`, `buildLocks`, `pryHotTurns`), threaded through `wardenHide`/`wardenSeek`
and `scriptedOrder(..., params = ShippedWardenParams)` as a defaulted argument — no globals,
no `gcsafe` surprises, and the only non-default caller is the harness.

**The harness.** `tools/tune_baselines.nim` sweeps the full 3×3×3 cross product
(gate 40/60/80 × locks 1/2/3 × hot turns 1/2/3) on seeds 1, 7, 42, 99. Each cell plays two
*full-length* matches per seed (720 prep + 1800 hunt a half) with the candidate warden on the
Moth seats: one against `moth`, one against a fixed `ReferenceWardenParams` = 60/2/2, the
hand-guessed starting point. The reference is a constant, not the shipped values, so the table
cannot chase its own tail. Score is zero-sum, so `scores[0]` in milli is the whole match; a
cell's figure is the mean of both columns over all four seeds. ~20 s for the whole sweep.

Cert-fixture length does **not** work as the episode length here, and the record says so: at
240/480 the build act is two turns long and all 27 cells score *identically* (I ran it — every
cell 412 milli). The parameters only bind at full length, so that is where they are scored.

**The result** (`tests/fixtures/tuning_grid.json`, read out in `docs/tuning.md`):

| gate | locks | hot | mean milli |
|---|---|---|---|
| 60 | 3 | 3 | **656** ← shipped |
| 60 | 3 | 1 | 650 |
| 60 | 3 | 2 | 608 |
| 60 | 1 | 3 | 607 |
| 60 | 2 | 3 | 606 |
| 60 | 2 | 2 | 559 ← the guess the note pinned |

`buildLocks = 3` is the clear win (better on both opponents and every seed); `pryHotTurns`
only bites against an opponent that bolts crates and is nearly flat, with 3 the argmax;
`coverageGatePct` is *inert* — 40, 60 and 80 tie exactly in every row, because the
"last build turn" and "within 36 px of the mouth" clauses fire first — so the tie-break, which
prefers the point nearest the reference, keeps 60. `ShippedWardenParams` is now 60/3/3.

**Wired into CI.** `tests/test_tuning.nim` (runs in both modes) asserts: the record covers
exactly the grid the harness sweeps at the recorded seeds, episode length and `GameVersion`;
`ShippedWardenParams == record.chosen` **and** re-deriving the argmax from the recorded table
lands on the same point; and two cells (the shipped one and the guess) re-run from this code
still produce the recorded numbers — so a hand-edited parameter, or a rule change that moves
the scores, fails the build rather than leaving a stale document.

**Blast radius, checked.** No digest moved: `golden_digests.json` is unchanged (the fixture is
1440 ticks, where the parameters do not bind), `test_determinism`, `test_replay`,
`test_baselines` (including "warden beats moth at seed 42" and "no baseline ever spends a
fourth lock") and the docker smoke all pass. The shipped values now differ from the design
note's prose (`locks_used < 2`, "two consecutive turns"); that is the point of the exercise and
`docs/tuning.md` says so explicitly. The note itself is untouched.

---

## F2 — `crate_push` emitted every push tick  ·  fixed, `3e97c1f`

Note step 7 says "the crate moves and a `crate_push` event + push sound ring are emitted
(rate-limited to one per crate per 12 ticks)". The 12-tick gate wrapped only `addSound`; the
event and `cogs[slot].cratesPushed` fired on every contact tick, which is why the manifest
description had to read "Push ticks this seat contributed" while the note's results example
reads as shoves.

The event and the counter now sit inside the same gate as the ring, so `crates_pushed` counts
shoves. The manifest description is regenerated from `tools/gen_manifest.py`
("Crate shoves this seat contributed, counted at most once per crate per 12 ticks.").

**Evidence that nothing in the sim moved:** re-recorded the fixtures in the same commit;
`controls_b64` and `keyframes` are byte-identical to the previous fixture (checked field by
field in Python), only `events` and `results` changed — `crate_push` 190 → 28, total events
339 → 177 over the 1440-tick fixture, `crates_pushed` `[20,0,33,0,101,36]` → `[3,0,7,0,13,5]`.
`test_crates`'s `countEvents("crate_push") == 1` and `test_baselines`'s "the warden really
builds" still pass unchanged, and CI's replay shrank from 129 917 B to 101 467 B.

---

## F3 — the seeker view's `found[]` dropped `by` and `mode`  ·  fixed, `5d58402`

`Cog` now keeps `foundBy` (the finder's slot) and `foundMode` (`"beam"`/`"tag"`), assigned at
the moment of the find from the same two values `foundEvent` already receives, cleared to
`-1`/`""` by `placeCogs` on every half reset. `seekerView` emits `by` and `mode`, and `at_s` is
now measured from the start of that half's hunt act rather than from match start — the review's
"~141 s rather than ~21 s" case — which is the only clock the seat otherwise has
(`clock.act_left_s`). `docs/PROTOCOL.md`'s example and the regenerated manifest page match.

**Evidence:** new case in `tests/test_vision.nim`, "a found hider is reported with who found it,
how, and when": touch-tags Moth-1 with Owl-1 on the open floor and asserts
`by == "Owl-1"`, `mode == "tag"`, `0.0 <= at_s < 1.0`.

---

## F4 — the two attempt deadlines sum to exactly the turn budget  ·  no change

The review's own conclusion is "Effect on the note's arithmetic: none" and checklist item 5 is
satisfied: every wait is explicitly bounded (9 s + 4 s, `for attempt in 1 .. 2`), the budget
guard settles the episode early, and the engine hard stop at `wallClockBudgetMs` is a separate
outer bound that no turn can outlive. Adding a third timer around `decideAll` would be a new
failure mode (a turn abandoned mid-batch) in exchange for tightening 13.0 s to 12.0 s. The
divergence is between the note's prose and the ceiling arithmetic, not in the behaviour, and
`tests/test_engine.nim:99-101` already pins `9 + 4 <= 13`.

## F7 — pointwise visibility instead of a rasterised shadowcast  ·  no change

Declared deviation #1, and the review traces that it computes exactly the lit-set definition
the note gives in §The world/§Lantern, with the note's own integer cone and range tests, and
that `tests/test_vision.nim:27-97` pins the boundaries. Replacing it with a shadowcast would
change every digest and every fixture to obtain the same observable rule. Not touched.

## F8 — the committed map differs from the note's authored JSON block  ·  no change

Real divergence, but the fix is not a code change: `data/vault.mapspec.json` is *generated* by
`scripts/art/author_map.py`, which refuses to write a map violating the fairness invariants, and
`tests/test_map.nim` re-checks them against the committed file (I re-ran it: all 36 obstacles and
all 10 crates have their exact 180° twin). The lane change is load-bearing and explained in
`AGENTS.md:88-93`. The nooks are not rotationally symmetric, but both halves play the identical
map with the identical nooks and the same bottom-centre pen, so half-comparability — the property
the invariant exists for — holds. Re-authoring the map to the note's coordinates would move every
digest, invalidate the tuning record and re-open the pinned-seeker bug the lanes were changed to
fix. The note's block is the stale artifact; the repo's is the generated one.

## F9 — `lantern_replay.data` is in the note's bundle list, not in the bundle  ·  no change

Nothing is missing at run time: `config.nims` passes no `--preload-file`, so emscripten emits no
data package, and `Dockerfile.replay-viewer:47-54` `test -s`'s the 15 files that do exist. The
note's file list is what is wrong. Fabricating an empty `.data` to satisfy a list would be
worse than the list being wrong. Left alone deliberately; the phase-60 check should be driven off
the Dockerfile's assertion tail, not off the note.

## F10 — float arithmetic inside the step, in `events.nim`  ·  no change

`events.seconds` is float and is called from inside `applyTick`, but the guard's scope
(`StepPath`, seven modules, `events.nim` deliberately excluded) matches the note's *test* spec,
and the review traces that determinism is unaffected: the digest covers only integer state and
event JSON is never read back into the sim. The absolute sentence in the note's prose is what
overreaches. Making `events.nim` integer-only would mean re-deriving `hidden_s`/`hidden_frac` as
fixed point everywhere in the spectator surface — a large change for no behavioural gain.

## F11 — the canvas find-burst was dead code  ·  fixed, `1a54b43`

`broadcast_core.js:388` read `packet.bursts` and `drawBursts` expanded a 240-radius ring on each
one; nothing ever wrote the key, so the ring never drew, and there was no find hold either.
I produced the key rather than deleting the read.

`replay-viewer/lantern_replay.nim` now steps through `advanceOne`, which snapshots each hider's
`(found, x, y)` **before** the step — the sim teleports a found hider into the caught pen on the
same tick, so the position has to be taken first — and appends one `[x, y]` per hider found on
that tick. `packetJson` emits and drains them. `rebuildWorld` and `stepTo` clear the list: a
scrub is not a find. `static_replay_worker.js` holds the playhead 400 ms on a burst, next to the
2 s intermission hold whose comment already promised "a find … worth holding the playhead on" —
that is the note's 0.4 s hold.

**Evidence:** `tools/wasm_replay_smoke.cjs` asserts, in the `wasm-viewer` job, that every frame's
`bursts` entries are `[x, y]` pairs and that the forward pass produces exactly as many as the
replay has `found` events. CI run 32612666063 prints
`wasm viewer smoke OK: 1440 ticks, 177 events, 1 find bursts, digests all matched`. The seek and
rewind comparisons now ignore `bursts`, which is per-tick-edge rather than per-tick.

**NOTED (not fixed):** the other two parts of the note's readout 4 — the beam snapping to hard
white for 12 frames — are still absent. That is a renderer change in `drawLight`, not a dead-code
fix, and no finding asked for it.

## F12 — `chrome_common.js` is rewritten, not "copied unchanged"  ·  no change

Declared deviation #3. The review verified the factory shape survives
(`test_viewer.nim:85-90` asserts all five exports), that the markup half of the claim checks out
id for id, and that the only ids dropped are the first-person PiP family the note authorises
removing. Restoring the starter's 838 lines would re-import four-team, perk, lives and flag-beat
chrome that lantern has no data for. The note's word "unchanged" is the inaccuracy.

## F13 — the determinism gate ran 1440 ticks, not the note's 5040  ·  fixed, `024144d`

Added "two runs of a FULL-LENGTH match agree at every keyframe" to `tests/test_determinism.nim`:
two independent 5040-tick scripted episodes in one process, asserting `tick == 5040`,
`keyframes.len == 210`, identical digests and identical control bytes. Roughly a second in debug.
The existing 1440-tick cases and the golden fixture (which the note pins at 1440) are untouched.
CI log: `[OK] two runs of a FULL-LENGTH match agree at every keyframe`, twice.

## F14 — three `test_engine` cases assert at the results/roster layer  ·  no change

A coverage gap, not a behavioural one — the review says so, and says it is outside the checklist
(item 5 requires the waits to be bounded, which they are). Driving `runEpisode` end to end from a
test means standing up the mummy server, the socket roster and a fake artifact sink for each
branch; that is a test-architecture change, not a fix, and it is not what any finding asked for.
Recorded as a genuine gap: nothing asserts the `COGAME_PLAYER_FAILURE_URI` write or the
`nowMs() > wallDeadline` branch through the loop.

## F15 — `test_viewer`'s wasm harness self-skips in the `test` job  ·  no change

Declared deviation #9, and the review establishes the skip predates this run and that the real
invocation happens in the `wasm-viewer` job, where it is now doing more work than before (F11).
Removing the skip would make the `test` job depend on an emsdk container it does not have.

## F16 — `decideAll` runs outside `stateLock`  ·  no change

The review's own analysis is "inferred, benign": the only shared state `decideAll` writes is
`memo`, an `array[4, int]` that no spectator surface reads; the string fields a spectator does
read are assigned under the lock. Holding `stateLock` across `decideAll` would block the socket
threads for up to 13 s a turn — the exact thing the current structure exists to avoid — and
narrowing it to a `memo` mutex would add a lock to the sim step for a value nothing races on.

---

## Other "could not determine" items

* **Is F1 reachable in a hosted episode?** Now settled by unit test rather than by inference:
  the new cases in `tests/test_engine.nim` construct the provider `Response` directly, so the
  path runs with no credentials and no network.
* **Does the 8 px line-of-sight quantisation ever disagree with a pixel-exact ray?** Not probed.
  No finding asked for it; it is deterministic and identical in both builds, so it cannot break
  re-derivation. **NOTED.**
* **Is the viewer's three-pass load comfortable at 5040 ticks in wasm?** Still unmeasured; the
  CI smoke runs the 1440-tick fixture. **NOTED.** F11 added no extra pass (the burst capture is
  two integer comparisons per cog per tick inside the existing step).

## NOTED (not fixed), collected

1. The note's readout-4 beam snap (hard white for 12 frames on a find) is still unimplemented.
2. Nothing asserts nook rotational symmetry, because the committed nooks are not symmetric (F8).
3. No test drives `COGAME_PLAYER_FAILURE_URI` or the wall-clock branch through `runEpisode` (F14).
4. `coverageGatePct` is inert in the shipped warden — the sweep proves it, and it is now
   documented in `docs/tuning.md`. It could be deleted, but deleting a knob the note names
   (§Scripted baselines, "≥ 60 % of the opening") is a design call, not a fix.
