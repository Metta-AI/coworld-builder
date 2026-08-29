# r1 fixes — continuous-control

Repo: `Metta-AI/cogame-continuous-control`
Head: `a8db2b326b7f7b8f05f10ffdb5c1a7e85f28b2dc` (`main`)
CI: https://github.com/Metta-AI/cogame-continuous-control/actions/runs/33249877981 —
**success** (run id `33249877981`, headSha `a8db2b32…`, jobs `test`, `docker-smoke`,
`wasm-viewer` all `success`; `grep -c "SEAT-COUNT FAIL"` over the whole run log: **0**;
`smoke OK: seats=1 results=835B replay=131999B reason=complete`).

Ten local commits were replayed one-per-finding through the Git Data API onto `main`
(blobs → tree with `base_tree` → commit → **one** `PATCH` of the ref at the end,
`force: false`), so history carries one commit per finding and the push produced a single
CI run on the final head. Nothing was force-pushed and no history was rewritten.

**No test was weakened.** The three test files touched all gained assertions or widened a
gate: test 37 now feeds the stop record 237 four-byte emoji and asserts 200 whole runes
come back (was: fed exactly the cap, asserted nothing about the field); test 47b's
forbidden-word list grew from 15 narrowed tokens to 16 of the design note's own; test 26's
key names moved with the schema and still assert the same two counts.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking candidate) | **fixed** | `e9902ccb` | `src/cc/replays.nim:233`, `tests/test_cc_replay.nim:176-180,197-200` |
| F2 | **fixed** | `e92e5e8c` | `src/cc/llm.nim:250` |
| F3 | **fixed** | `282f0b6a` | `src/continuous_control.nim:45-51` |
| F4 | **fixed** (docs) | `a2fb338f` | `docs/PHYSICS.md:256-293` (new §The baseline bands) |
| F5 | **fixed** | `3f4bfb64` | `src/cc/body.nim:132-140` |
| F6 | **fixed** | `73b3f44a` | `src/cc/report.nim:97-112` (`joint_count` :104, `joints` :111), `tests/test_cc_obs.nim:27,29,48,82` |
| F7 | no change — deliberate, documented, tested | — | `src/cc/broadcast.nim:238-244` |
| F8 | no change — **NEEDS-DESIGN** (replay format) | — | `src/cc/sim.nim:432-433` |
| F9 | no change — **DISPUTED as a defect**; item 15 met | — | `client/*` |
| F10 | no change — the flag is required, and documented | — | `replay-viewer/config.nims:31-36` |
| F11 | no change — documented divergence; note's estimate is what is wrong | — | `src/cc/decide.nim:109-116` |
| F12 | no change — inherited chrome, overwritten at runtime | — | `client/replay_broadcast.html:1887-1910` |
| F13 | **fixed** | `b682a19b` | `tests/test_cc_endcard_labels.nim:39-52` (list at :46-48) |
| F14 | **fixed** | `fece3c91` | `src/continuous_control_player.nim:74-89` (`ackFrame`), `:114` (the call) |
| F15 | no change — **DISPUTED**; the starter serves the same route | — | `src/cc/server.nim:668` |
| F16 | **fixed** (docs) | `04e39c93` | `docs/PHYSICS.md:104-145` (divergences 11-15) |
| F17 | **fixed** | `a8db2b32` | `src/cc/replays.nim:235-246`, `src/cc/server.nim:365`, `tests/helpers.nim:78`, `tests/test_cc_replay.nim:173` |
| F18 | no change — no defect | — | `src/cc/report.nim:18-42` |

---

## F1 — the `stop` record's `detail` had no rune cap — **fixed**, `e9902ccb`

**Was:** `writeStop` wrote the field verbatim (`writer.body.addText(stop.detail)`,
`replays.nim:228`), and both call sites that can fill it build it from an unbounded string:
`server.nim:399` (`"sim guard: " & guard.msg`), `server.nim:404` (`error.msg`, any captured
`CatchableError`) and `server.nim:314-315` (the wall-clock text). The same string was capped
at 200 runes one line later on the results path (`sim.nim:671`) and its sibling record is
capped at its call site (`decide.nim:74`), so `results.json` and the replay's own `stop`
record could disagree about the same fact.

**Is:** the cap is applied in the codec —
`writer.body.addText(stop.detail.truncateRunes(MaxStopDetailRunes))` — at the same 200 runes
`sim.settle` uses. I put it there rather than at `server.nim:407-409` deliberately: the
identical stop-writing block exists a second time in `tests/helpers.nim:100-102` (the
harness that mirrors the server, and the one that drives the fault/wall-clock re-derivation
tests 34–36), so a call-site fix would have left one recorder uncapped and the next fault
path added would have to remember. Capping in the codec makes an uncapped `stop.detail`
unwritable from any recorder, and it is the last string on the replay-bound list that was
not covered (`say` 140, `notes` 320, policy/name 48, prompt never written,
`fallback.detail` 200, `results.stopDetail` 200).

**Evidence:** test 37 (`tests/test_cc_replay.nim:148`) now writes
`detail: repeat(emoji, MaxStopDetailRunes + 37)` — 237 four-byte emoji, 948 bytes — and
asserts on the output of `tools/replay_summary.py`:
`summary["stop"]["detail"].getStr().runeLen == MaxStopDetailRunes` and equality with
`repeat(emoji, MaxStopDetailRunes)`, alongside the test's existing
`validateUtf8(output) == -1` and the "no `\ud`" check. It passes in both the debug and the
`-d:release` pass of run 33249877981 (`[OK] 37. replay_summary.py emits strict UTF-8 JSON`
at 11:22:21 and 11:22:28). A truncation that cut mid-emoji would fail both the rune count and
the strict-UTF-8 assertion.

**Checklist item: 9** — "Every string that reaches the replay (`say`, `notes`, prompts,
**captured errors**) is truncated on **rune** boundaries. A test feeds multi-byte input at the
cap and asserts the output is valid UTF-8."

## F2 — the system prompt contradicted itself about `brake` — **fixed**, `e92e5e8c`

**Was:** the gait glossary carried documented divergence #9's wording ("a brake is how you END
a stage, not how you save one") while the READ-THOSE-NUMBERS block 27 lines later, in the same
string constant, carried the design note's original folklore verbatim: `pitch heading toward
the fall limit -> brake for one turn, then resume.` (`llm.nim:250`). One constant told the
model both things.

**Is:** `pitch heading toward the fall limit -> cut power and shorten the stride. / A brake
will NOT save you: it switches the servo off.` — the same advice `docs/PHYSICS.md:94-99`
records as the divergence.

**Evidence:** the prompt is never written to the replay (`decide.nim:76-83`, asserted by
`tests/test_cc_replay.nim:104`) and is not hashed, so this changes no recorded byte; the
`test` job is green on the new text. **Not fixed, deliberately:** the two champion prompts in
`tools/ci/policies.json` also tell a cog to brake to save a fall. Those are operator strings,
they are the design note's own text, and rewriting a champion's strategy is a change to the
league entrants rather than to the game — out of scope for this round (`NOTED (not fixed)`
below).

**Checklist item:** none — advisory; design-note fidelity against documented divergence #9.

## F3 — the seed was randomised after `config.update` — **fixed**, `282f0b6a`

**Was:** `config.update(parseJson(runtimeConfig.config))` at `:47`, then
`if not seedPinned(...): config.seed = randomSeed()` at `:50-51`, while the module's own doc
comment (`:4-8`) and design.md:1025 both say the randomisation happens **before**
`config.update` (the starter's rule).

**Is:** the randomisation runs first, and `config.update` overwrites it when — and only when —
the config names a seed. The outcome is identical in both orders (`seedPinned` reads the raw
config text, so a pinned seed wins either way, and the first seed-derived draw,
`buildStartPose` inside `startStage`, runs far later), which is why this is a fidelity fix and
not a behaviour fix; the code now matches the rule it documents.

**Evidence:** `tests/test_cc_seeding.nim` (tests 15–17) is green in both passes; the smoke
episode reports the same `reason=complete` with a runner-randomised seed.

**Checklist item:** none — advisory; design-note fidelity.

## F4 — the measured baseline band was not recorded where the test says it is — **fixed**, `a2fb338f`

**Was:** `tests/test_cc_baselines.nim:157-158` says "`docs/PHYSICS.md` records the numbers and
why the hopper's band is where it is", and `docs/PHYSICS.md` had no such section. The
divergence (means over 100 seeds, wider than the note's per-seed 6–14 / 30–58 / 11–24 m and a
plodder gate of ≥ 80 % rather than ≥ 90 %) was real and deliberate; its record was a dead
pointer.

**Is:** a new `## The baseline bands` section listing every threshold test 25 asserts, why the
gate is on the distribution rather than per-seed (the seeded 0.05 rad start wobble decides
whether a body finds its stride, so a per-seed floor would pin the wobble out of the game),
and why the hopper's floor sits at 0.3 m (fall-heavy seeds pull the mean down; the floor
exists to exclude a baseline that never moves, and the 14.0 m ceiling stops a filler being
tuned into a champion). **I did not invent measurements**: every number in the section is one
the committed test asserts. The sandbox has no Nim, so the actual per-morphology means remain
what the reviewer listed under "could not determine".

**Checklist item: 7** (in part) — the scripted baseline's parameters are tuned and the tuned
numbers are now on the record next to the sweep that produced them.

## F5 — the hopper had a third fall condition — **fixed**, `3f4bfb64`

**Was:** `body.nim:133` set `result.highY = mm(4000)`, so `isUnhealthy` returned `fwHigh` for
a hopper torso above 4.00 m and ended the stage as `fell` with `why: "high"` — a condition
design.md:277 does not give it (it gives exactly `y < 0.70 m` or `|pitch| > 20°`; the walker's
stated 0.80–2.00 m band is implemented exactly at `body.nim:216-217`).

**Is:** `result.highY = mm(20_000)` — the sim's own world-box ceiling (`GuardMaxYQ16`,
`sim.nim:27`), with the reason in-line. Inside the reachable world the note's two conditions
are now the only fall tests for the hopper; the value survives only so that a torso which
escapes the box ends its stage as a fall rather than faulting the whole episode (termination,
step 7, runs before the invariant guard, step 9). I chose this over deleting the check because
deleting it would convert an escaping hopper from a scored fall into a `SimGuardError` fault
that ends the episode.

**Evidence:** test 11 (`test_cc_sim.nim:326-353`) samples torso `y` in −0.6 … 3.05 m and
compares `isUnhealthy` against the spec's own thresholds, so it stays consistent and stays
meaningful for the walker (2.00 m, inside the sampled range); tests 25 and the seeding suite
run 100 release seeds of hopper stages and are green.

**Checklist item:** none — advisory; design-note fidelity (`correctness`-adjacent).

## F6 — the observation's per-joint array was `joints_detail` — **fixed**, `73b3f44a`

**Was:** `body` carried `"joints": <count>` and `"joints_detail": <array>`
(`report.nim:99,107`). The note's example carries two keys named `joints` in one object — a
count and the array — which is not constructible JSON, so something had to give; the code gave
the array a new name, and a policy written against the note's example that iterates
`body.joints[]` found an integer.

**Is:** the array keeps the note's name (`"joints": joints`) and the count moves to
`"joint_count"`. This is the reading that costs a policy least: iterating `body.joints[]` now
works as the note shows, `len(joints)` still yields the count, and it matches the convention
the replay config already uses — `morphJson`'s `"joints"` is an array (`sim_config.nim:191`).
Test 26 asserts both (`joint_count` equals `spec.jointCount`, `joints.len` equals it too), so
§Tests 26's "`joints` and `feet` always have the morphology's exact counts" is satisfied on
both readings.

**Evidence:** `[OK] 26. the observation reconstructs the sim state` and `[OK] 27. torque_pct
and saturated agree` in both passes of run 33249877981. No other consumer moved: `grep` for
`joints_detail` over the whole tree returns nothing, and neither `tools/ci/policies.json`, the
client, the manifest nor `docs/` ever named it.

**Checklist item:** none — advisory; design-note fidelity on the observation contract.

## F7 — `cc_beats`, not `beats` — no change

The key name is deliberate and the reason is in the code at the point of the decision
(`broadcast.nim:238-244`): the inherited chrome's `ingestBeats` claims the key `beats` and
would turn it into unlabelled `<div>` markers, which is exactly what checklist item 14(d)
forbids ("a kind with no rule is an invisible marker" / beats must be labelled `<button>`s
that seek). The game block reads `cc_beats` and draws labelled, clickable buttons
(`replay_broadcast.html:3265-3281`), CSS exists for exactly the six kinds `sim.BeatKinds`
emits (`:3179-3185`), and test 46 pins the key set including `cc_beats`. Renaming to the
note's `beats` would break the requirement the checklist actually gates. The note's §Tests 46
key list is the thing that is wrong here, and it is wrong in the direction of a worse viewer.

**Checklist item: 14(d)** — satisfied as shipped.

## F8 — the derived `fallback` beat drops the cause — **NEEDS-DESIGN**, no change

Real, and I did not fix it. `sim.nim:432-433` emits `{"k": "fallback", "cause": "fallback"}`
because `Order` (`driver.nim:21-34`) carries no cause: the eight real causes exist only in the
`fallback` chat record `decide.nim:71-74` writes. A minimal-looking fix — add a cause field to
`Order` and emit it — would make the LIVE feed disagree with the REPLAY feed, because the
viewer re-derives its beats from the recorded `order` records (`replay_runtime.nim:218-219`)
and those records are written from `OrderPayload` (`replays.nim:190-209`). Carrying the cause
across that boundary means adding a field to the order record, which is a replay **format**
change (`ReplayFormatVersion`, the wasm parser, `tools/replay_summary.py`) — or teaching both
the live block and the pre-scan to join the `fallback` chat record to the turn it belongs to,
which is a viewer design decision. Either is a design change, not a fix, so it belongs to the
designer and not to this round. Nothing is lost from the replay bytes today: the real cause is
in the `fallback` chat record and `tools/replay_summary.py` re-emits it; what the spectator
reads is the generic line.

**Checklist item: 2** — unaffected either way (the beat is derived from the re-derivation, not
from a parallel recording; it is the label that is coarse).

## F9 — both `--strict-text-bounds` gates ran on zero drawn strings — no change

Confirmed and not a defect. `grep -c 'fillText\|strokeText'` returns **0** for all four client
files (`chrome_common.js`, `broadcast_core.js`, `replay_broadcast.html`, `cc_block.html`) at
this head — this viewer draws no canvas text at all; every readout is DOM, and the board
renders in a Worker on an OffscreenCanvas. `total: 0` is therefore the correct and only
possible number, not a hidden failure, and item 15's own text names both causes. What item 15
requires and this repo has: `--strict-text-bounds` on both smoke steps (`ci.yml:338`, `:379`),
`never_inside == 0`, and a worst-case renderer fixture with its own CI step ("Drive the text
path at full cap in the real bundle", green at 11:23:45 in run 33249877981). Making the number
non-zero would mean moving readouts onto the canvas — a rewrite of working chrome, in the
opposite direction from item 14.

**Checklist item: 15** — met as shipped.

## F10 — `--preload-file client/art` — no change

The flag is not decoration: the renderer opens `client/art/walls/*` and
`client/art/lockerroom/bg.jpg` while baking, and under emscripten those paths must exist in
MEMFS or the bake fails. The reason is in `config.nims` at the flag. Everything else on that
line matches design.md:1440 exactly, including the absence of `MODULARIZE`/`EXPORT_NAME`,
which is the thing item 13 actually gates and which `Dockerfile.replay-viewer:60-62` asserts
at build time. Removing the flag would break the bundle the smoke proves loads.

**Checklist item: 13** — satisfied; the smoke's `loaded: true` is the evidence.

## F11 — the replay is ~132 KB, not ~32 KB — no change (documented, `04e39c93`)

The reviewer's own trace settles it: the note's §Record vocabulary (design.md:1375) requires
`view` on the `order` record, and attaching the observation to every order is what makes the
replay explain each decision. The size follows from the note's own record shape, so the note's
size ESTIMATE is what is wrong, not the code. The record is bounded
(`MaxOrderRecordRunes = 6000`, `decide.nim:118-122`, dropping `view` rather than truncating
it) and the CI smoke reports `replay=131999B` for a full three-stage episode. No code change;
the divergence is now written down as `docs/PHYSICS.md` #15 in the F16 commit.

## F12 — ctf plate internals survive in inherited markup — no change

`.hcap`, `.lives-num`, `.pb-tags`/`.pb-lbl` and `.squad` survive only in the INHERITED plate
builder (`replay_broadcast.html:1887-1910`), whose contents `ccPlate` rewrites every frame
(`cc_block.html:343-372`). No paintbot residue reaches the spectator — the CI smoke's scorebug
readout is `ALPHA trotter RETURN 0.0 2.3 m · 0.05 m/s STAGE 1/3 · HOPPER · TICK 367/468`.
Item 14 requires the page to be the STARTER'S, with the note's removals; cutting live
identifiers out of inherited chrome is a rewrite of working chrome, which is the failure
mode item 14 exists to catch (cogame-gridlock). The decision is recorded at
`tests/test_cc_endcard_labels.nim:12-13`.

**Checklist item: 14** — satisfied as shipped.

## F13 — the forbidden-vocabulary grep was narrower than the note's list — **fixed**, `b682a19b`

**Was:** `["Lives", "LIVES", "Clstr", "flagicon", "heart", "paint", "hoppers", "hillchip",
"POV", "EYES", "spray", "grenade", "med kit", "killfeed(", "squad-pip"]` — `flag`→`flagicon`,
`hill`→`hillchip`, `kill`→`killfeed(`, with `Cap<` and `team` dropped.

**Is:** the note's own tokens for four of those five: `Cap<` restored, `hillchip`→`hill`,
`killfeed(`→`kill`. Three of the narrowings were not forced at all — the appended block
contains no `hill`, no `kill` and no `Cap<` anywhere, comments included. Two stay narrowed and
the comment now says which and why: `flagicon` (the block rewrites the inherited element id
`flag-alpha` rather than renaming it, `47c` asserts that mapping) and `team` (the inherited
chrome's own class names `team-name`, `ec-team`, `ec-teams`, which the block must use to
address the plate it is rewriting).

**Evidence:** `[OK] 47b. NOTHING this game adds carries paintbot vocabulary` in both passes
of run 33249877981 — a strictly larger, stricter list, passing.

**Checklist item: 14** — the vocabulary gate that keeps the chrome this game's.

## F14 — the player container did not ack frames — **fixed**, `fece3c91`

**Was:** the receive loop re-sent the registration blob for the first 10 s and otherwise only
read; design.md:1248 says the harness "only acknowledges frames (`0x85` after every frame,
exactly as `src/paintball_player.nim` does)", and the module's own doc comment (`:3-5`) says
the same.

**Is:** `ackFrame()` sends the one-byte Sprite v1 ready packet after every received frame,
byte-identical in intent to the starter's `readyBlob()`
(`/workspace/starters/coworld-ctf/src/paintball_player.nim:48-55,127`), with the send guarded
so a dead socket is still the receive loop's decision and the container still exits 0 on the
close-frame race. Nothing waits on it (`fastMode: true`; the server's handler reads Pings and
registration chat only, `server.nim:614-661`, and a one-byte frame that is not JSON is
dropped by `applyRegistration`'s `parseJson` guard at `:576-580`), so this changes no timing —
it makes the container match the protocol contract it claims to implement.

**Evidence:** `docker-smoke` green with the real player container in the loop —
`smoke OK: seats=1 results=835B replay=131999B reason=complete`, and no
`ignoring bad frame` / registration noise in the run log.

**Checklist item:** none directly — advisory; protocol conformity, adjacent to item 5 (the
ack cannot introduce a wait: it is a fire-and-forget send inside an already-bounded loop).

## F15 — `/client/replay` is still routed by the game server — **DISPUTED**, no change

The route is the starter's own behaviour, not this build's addition. `coworld-ctf` serves the
identical developer route from its asset handler —
`request.path in [bitworldClient.ReplayClientRoute, bitworldClient.CoworldReplayClientRoute,
LeagueReplayerPath] … request.respond(200, replayHeaders, EmbeddedBroadcastReplayHtml)`
(`/workspace/starters/coworld-ctf/src/ctf/server.nim:824-853`) — so removing it would diverge
from the starter that item 14 requires this repo to follow, and would contradict
design.md:1424-1425, which states the developer route explicitly.

What item 3 gates is what is DECLARED to the platform, and that is clean:
`coworld_manifest_template.json` declares `"replay_viewer": {"bundle":
"static-replay-viewer"}` and the string `/client/replay` appears nowhere in the manifest
(`grep`: no match); `tools/build_replay_viewer.sh` is present, executable and wired as the
`coworld build` hook; `coworld-release.yml:200-215` fails the release unless certify prints
the STATIC-bundle liveness marker. A pod-served viewer is never declared, never built into the
manifest, and never reached by the platform.

**Checklist item: 3** — satisfied; no pod viewer is declared.

## F16 — divergences that lived only in code comments — **fixed** (docs), `04e39c93`

`docs/PHYSICS.md`'s numbered divergence list now runs to 15 and adds the five that were
only in code: `crouch` as the shallowest QUIET pose (#11, from `gaits.nim:72-78,104-107`),
seek as rewind-and-re-step (#12, from `replay_runtime.nim:5-12`), the tuning `--check`
comparing the committed JSON rather than re-running the search (#13, from `ci.yml:104-115`),
`tools/wasm_replay_smoke.cjs` left unwired with test 48 folded into `test_cc_viewer.nim`
(#14), and the ~130 KB replay with its cause (#15, F11). The measured baseline bands are the
new section the F4 commit added. Every claim is quoted from the code it describes; I invented
no numbers. I did **not** touch `runs/2026-08-29-continuous-control/log.md` — the run log is
the builder's, not mine.

**Checklist item:** none — advisory; it is what makes the other divergences auditable.

## F17 — `writeHash` dropped the tick tag — **fixed**, `a8db2b32`

**Was:** `proc writeHash*(writer: ReplayWriter, value: uint64) = writer.hashes.add(value)`.
design.md:428 records the call as `replayWriter.writeHash(uint32(tick), sim.gameHash())`. The
array is positional and alignment held, but nothing checked the implication, so a recorder
that ever appended a hash without stepping a tick would misalign the whole chain and surface
the mismatch at some later, innocent tick.

**Is:** the tick is a parameter, as the note writes it, and a write at the wrong index raises
`CcError` naming both the tick and the index. **The wire format is unchanged** — the array is
still positional, one entry per tick, so no replay, no parser (`replay_summary.py`), no wasm
viewer and no fixture moves; only the three recorders pass the tick they already had
(`server.nim:365`, `tests/helpers.nim:78`, `tests/test_cc_replay.nim:173`). If the invariant
ever fires in production it lands in the game loop's `except CatchableError`, which stops the
episode as a `fault` with the message in the (now capped, F1) stop record — loud, bounded, and
with the replay still written.

**Evidence:** the full suite is green in debug and `-d:release`, including test 36, which
corrupts one recorded hash and asserts the mismatch is latched at the exact tick
(`test_cc_replay.nim:136-146`; `[OK] 36. keyframes are a cross-check, not a crutch` in both
passes), and `docker-smoke` wrote and re-played a 131 999 B replay with no mismatch.

**Checklist item: 2** — replay re-derivation: the per-tick hash chain is the thing that proves
frame-by-frame agreement, and its alignment is now asserted at the write rather than assumed.

## F18 — `isqrtQ16` is defined and never called — no change

Not a defect. The design's constraint (design.md:178-179, restated in `solver.nim:11`,
`sim.nim:10` and `report.nim:4`) is about WHERE a square root may live — `report.nim` only,
never in hashed state — and the shipped tree satisfies it. Foot slip is reported as `|vx|`
(`body.nim:305-308`), which is why nothing calls it today. Deleting a helper the design note
names by path, and that the three "no sqrt in the solver" comments point at, would remove the
anchor those comments and `docs/PHYSICS.md:54-55` refer to. It costs nothing and hashes
nothing.

---

## NOTED (not fixed) — outside this round's scope

- **The champion prompts still tell a cog that a brake saves a fall**
  (`tools/ci/policies.json`, `continuous-control-gaitsmith` rule 1 and
  `continuous-control-throttle`'s "Falls:" line). They are the design note's own text and they
  are operator strategy, not game rules; F2 fixed the contradiction inside the game's system
  prompt only. If the designer wants the league entrants to agree with divergence #9, that is
  a policies edit and a new upload, not a code fix.
- **`tests/helpers.nim:71-72` records order chat records with `view = nil`**, so the
  record→re-derive tests exercise a replay about a third the size of the one the server
  writes (F11's side effect). The real 132 KB replay is exercised by the wasm smoke, so the
  gap is covered elsewhere; closing it in the helper would change what tests 34–36 measure.
- **The 50 %/100 % scrub readouts are identical in the CI smoke** (reviewer's "could not
  determine"). Unchanged this round; settling it needs a `viewer_smoke.mjs` that re-reads the
  readout after a bounded settle, which is a CI-harness change rather than a finding.
