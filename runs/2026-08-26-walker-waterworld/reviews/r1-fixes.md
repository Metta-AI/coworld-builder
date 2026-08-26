# r1 fixes — walker-waterworld

Head: `f078434aab36e880d189cedcd74ec64883d71cbc` (main)
CI: https://github.com/Metta-AI/cogame-walker-waterworld/actions/runs/32960525769 — **success**
(`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; created 2026-08-26T10:53:27Z on that sha)

22 commits, one per finding, each subject-prefixed `r1-F<n>:`. All 22 were created as GitHub
Git-Data commits and the ref was moved **once**, so the run above is the only CI run for the whole
round and it is on the final head. The remote tree sha (`2bea0dc1…`) equals the local tree sha, so
what CI built is what is described here.

**Method note.** The sandbox turned out to be able to run the toolchain: I installed Nim 2.2.4 (the
version `ci.yml` pins) plus `nimby 0.1.26` and `nimby --global sync nimby.lock`, so every change
below was run locally in **debug and release** before it was committed, and the whole suite
(15 files × 2 modes, plus both entrypoint binaries) was green locally before the push. The review's
three "could not determine" items that needed a run are settled below with measured numbers.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | fixed | `4f2e00f` | `tests/test_control.nim:390-410` |
| F2 | fixed | `e69f45d` | `tests/test_control.nim:194-275`, `docs/plans/…-design.md` (errata) |
| F3 | fixed | `581e528` | `tests/test_control.nim:91-99` |
| F4 | fixed | `0e09f51` | `tests/test_tank.nim:105-186` |
| F5 | fixed | `e2553c3` | `src/waterworld/decide.nim:322-327, :383` |
| F6 | fixed | `156ce1e` | `src/waterworld/decide.nim:282-308`, `tests/test_engine.nim:128-150` |
| F7 | fixed | `888a1ee` | `tests/test_engine.nim:19-40, :150-395` |
| F8 | fixed | `0f13ef2` | `src/waterworld/server.nim:193`, `tests/test_server.nim:17-22` |
| F9 | **NEEDS-DESIGN** (no change) | — | `src/waterworld/server.nim:569-599` |
| F10 | fixed | `6f6e0e2` | `src/waterworld/intents.nim:70-93`, `tests/test_intents.nim:149-155` |
| F11 | fixed | `9871ce7` | `src/waterworld/decide.nim:464-468` (`clamp(attempt, 1, 2)` at :467), `tests/test_engine.nim:355-365` |
| F12 | fixed | `ea2cbee` | `src/waterworld/replays.nim:219-223` |
| F13 | fixed (doc) | `8618d5a` | `docs/plans/…-design.md` (errata) |
| F14 | fixed (doc) | `84a8c8f` | `docs/plans/…-design.md` (errata) |
| F15 | fixed (doc) | `b170bcf` | `docs/plans/…-design.md` (errata), `AGENTS.md:4-9` |
| F16 | fixed | `a0569b7` | `tools/ci/renderer_fixture.html:26-40, :119-124`, `src/waterworld/global.nim:603-613`, `tests/test_viewer.nim:210-243` |
| F17 | fixed | `880449d` | `src/waterworld/global.nim:615-628, :644`, `tests/test_viewer.nim:245-267` |
| F18 | fixed (doc) | `f078434` | `.github/workflows/ci.yml:307-325` |
| F19 | fixed | `d5f4bf5` | `tests/test_viewer.nim:135-150`, `docs/plans/…-design.md` (errata) |
| F20 | fixed | `e78837c` | `tests/test_viewer.nim:271-291`, `docs/plans/…-design.md` (errata) |
| F21 | fixed | `a3c79a0` | `tests/test_viewer.nim:6, :26-42` (sha256 pin at :33), `AGENTS.md:43` |
| F22 | fixed (doc) | `dcb3869` | `docs/plans/…-design.md` (errata) |
| F23 | fixed (doc) | `f5f7610` | `docs/plans/…-design.md` (errata) |

No test was disabled, skipped, deleted or loosened by any of these commits. Four assertions were
**tightened** (F1, F3, F4, F19), one deleted assertion was **reinstated** (F2), and ~40 assertions
were added (F2, F4, F6, F7, F10, F11, F16, F17, F19, F20). `git log -p f078434 -- tests/` shows no
`skip`, no `xfail`, no removed check, and no widened bound.

---

## F1 — the rock-tangent tolerance (blocking)

**Was:** `bound = 0.35·|toRock|·Q12` — any thrust up to 69.5° toward the rock passed, while the
comment justified ~0.10.
**Is:** `bound = 0.11·|toRock|·Q12`, derived term by term at the assertion site. In this block the
velocity is zeroed, so the accel vector *is* the steer vector and the whole error is quantisation:

| term | size |
|---|---|
| half a step of the 32-direction table | 5.625° |
| `nearestDirIndex` maximises the dot product against the **rounded** table, whose entry lengths differ by up to 1 part in 4096, shifting the sector boundary by `(2.2e-4)/(2·tan 5.625°)` | 0.064° |
| `micro()` truncates the accel to whole µm, and level ≥ 1 needs \|a\| ≥ 372 µm → `atan(√2/372)` | 0.218° |

`sin(5.907°)·1.0002 = 0.1030`, so 0.11 is the smallest round bound the arithmetic proves.

**Evidence (this settles the review's first "could not determine").** The block now echoes the worst
cosine it sees. CI run 32960525769, `test` job, both modes:
`rock tangent: worst cosine toward the rock 0.09911919308913099 over 3365 clipping goals`.
I also ran the same sweep locally at 400 000 samples (40× the shipped 10 000) and the worst cosine
was identical, `0.09912` — i.e. 5.688° off perpendicular, which is `5.625 + 0.064` exactly, so the
truncation term never binds at throttle 255 and the analytic bound is tight. A bound of 0.098 would
therefore **fail**; the reviewer's suggested value is 0.5 % below the true worst case. 0.11 leaves
11 % of headroom over an observed maximum that is itself an analytic maximum, so a real regression
in the tangent rule fails the test.

## F2 — the deleted poison-repulsion assertion (blocking)

**Was:** the five-standoff "the skimmer did not eat the bloom on its path" block was deleted and
replaced with an off-path monotonicity block over three standoffs.
**Is:** both. The off-path block is unchanged; a new **on-path** block puts the waypoint straight
through a pinned bloom (the deleted block's geometry) and runs all six standoffs
`0 / 500 / 900 / 1200 / 1800 / 2500 mm`, asserting:

1. the closest approach is monotone non-decreasing in the standoff;
2. at `MaxStandoffMm` (2.5 m) the bloom is **still live** after 48 ticks and was never touched;
3. at standoff 0 the skimmer **does** eat it — non-vacuity, so (2) is the repulsion's doing.

The reviewer is right that the radial term cannot sidestep, but it can brake, and the arithmetic
says exactly when braking is enough: the combined steer reverses once `d < standoff/3` (weight
`1.5·(s−d)/s ≥ 1`); contact is at `SkimmerRadius + PoisonRadius = 0.40 m`; stopping from throttle
128 (67 500 µm/tick) at `MaxThrustAccel` costs `v²/2a = 0.44 m`. That needs `s ≳ 2.5 m`, which is
exactly the maximum standoff the schema allows.

**Evidence.** CI `test` job, both modes:
```
dead ahead at standoff 0 mm: bloom EATEN, closest 347240 µm
dead ahead at standoff 500 mm: bloom EATEN, closest 347240 µm
dead ahead at standoff 900 mm: bloom EATEN, closest 347240 µm
dead ahead at standoff 1200 mm: bloom EATEN, closest 347240 µm
dead ahead at standoff 1800 mm: bloom EATEN, closest 389816 µm
dead ahead at standoff 2500 mm: bloom survived, closest 486771 µm
```
The design note's §Tests 4 wording ("every `standoff_m ≥ 0.5`") is corrected in a new **Errata**
section at the end of the repo's copy of the note, with the derivation and these numbers.

## F3 — the `hold` stop threshold (blocking)

**Was:** `speed < 100.0` µm/tick (widened 100× from an unsatisfiable `1.0`).
**Is:** `speed < 27.0` µm/tick — the smallest bound the arithmetic admits: integer drag
`v − (v·39) div 1024` removes nothing below `1024/39 = 26.3` µm/tick, and the servo issues level 0
below 372 µm/tick, so zero is unreachable and 26.3 is the floor.
**Evidence.** Instrumented locally: the held skimmer reaches `v = (−18, 0)` µm/tick at tick 56 and
stays there for the remaining 40 ticks — 0.43 mm/s. 18 < 27 with the margin the arithmetic
predicts, and 27 is 3.7× tighter than the 100 it replaces. Green in CI in both modes.

## F4 — the near-tangent skip in the ray-cast pin (blocking)

**Was:** `continue` — every ray whose perpendicular distance to the rock centre is within 20 mm of
`RockRadius` left the pin entirely, with nothing bounding how large that class is.
**Is:** no ray is skipped. Each ray is classified and both classes are asserted:

* not near-tangent → the original 2 mm float-reference pin, unchanged;
* near-tangent and both sides see a hit → a 5 mm pin (widest disagreement measured: 2.46 mm);
* near-tangent and one side sees a graze where the other sees a miss → no distance bound exists
  (the answers are `SensorRange` apart by construction), so it is bounded by **count**.

Then the shape of the split is pinned: `nearTangent·20 < pinned`, `grazeFlips ≤ 5`,
`pinned > 25 000` — so a change that made every ray "near-tangent", or that stopped generating rays,
fails here instead of passing vacuously.
**Evidence.** CI `test` job, both modes:
`rock casts: 29972 pinned to 2 mm, 268 near-tangent (1 graze/miss flips)` — the excluded-from-2 mm
class is 0.89 % of the sample and exactly one ray in 30 240 has no distance bound at all.

## F5 — the floor slept inside the per-turn budget

`turnStart` is now re-taken **after** the rate floor (`decide.nim:383`), so `turnBudgetMs`
covers the two attempts it is sized for (`attempt1Ms + retryMs = 14 000 ≤ 16 000`) rather than the
floor plus one attempt. A turn that slept out a full 12 s spacing no longer skips its own retry.
Both waits are unchanged in length and still bounded; worst case per turn is spacing + budget, which
is what the note's episode arithmetic already assumed (the floor is start-to-start).

## F6 — the floor was not stop-interruptible

The floor moved into `waitOutInterBatchFloor` (`decide.nim:282-308`), which sleeps in 100 ms slices
and returns early once `elapsedSeconds + slept ≥ wallClockBudgetSeconds`. Same bound, same spacing
when the clock is healthy; at most one slice of lateness when it is not. `test_engine` drives both
paths through the engine's own entry point — a healthy floor still sleeps its spacing (≥ 250 ms of
300), and a floor whose wall clock is already spent returns in < 1000 ms (measured: 100 ms, and the
engine logs `cutting the floor short after 100 ms`).

## F7 — no fake client, so three promised assertions were absent

`test_engine` now stands up a real HTTP server on `127.0.0.1` (mummy, 8 workers, a probed-free port
in 39641..39680) and points the engine's **Bedrock** transport at it, so every assertion runs
through the real `curly.makeRequests` batch, the real deadlines and the real fallback path:

* **one batch.** After a warm-up batch fills libcurl's connection pool (libcurl holds back the rest
  of a batch until the first transfer to a new host reveals whether it can multiplex — worth
  knowing), four requests that each hold for 300 ms give an in-flight high-water mark of **exactly
  4**, with exactly 4 requests seen.
* **exactly one retry.** An unusable first batch is followed by a second and no third (8 requests);
  the retry's answer is the one that flies; each seat has a `parse_error` fallback against
  **attempt 1**.
* **zero retries on a throttle.** A 429 produces exactly 4 requests and a `throttled` fallback per
  seat.
* **two consecutive failures** leave every seat on the `shoal` intent with one terminal fallback
  record each.
* **the budget cuts off a hung provider**: a fake that answers 4 s after a 2 s deadline is abandoned
  inside `turnBudgetMs`, every seat ends with a legal intent and a `timeout` record.

This passed in CI on the runner in both debug and release (and three consecutive local release runs)
— the localhost fake is not flaky in the environment that matters.

## F8 — the test tested a copy of the parser

`parseRegistration` is exported from `src/waterworld/server.nim` and `tests/test_server.nim` imports
it; the inline re-declaration is gone. The assertions are unchanged — what changed is which function
they run against.

## F9 — the held-registration path — NEEDS-DESIGN, no change

The mechanism is correct (`server.nim:569-599`) but it is not extractable at a right-sized cost: the
hold lives inside the server loop's pass over `appState.chatMessages`, keyed by live `WebSocket`
handles, and it writes through `replayWriter`, `engine.seats` and `sim.seatPolicyKind` in the same
pass. Testing "held, not dropped" honestly means asserting the loop re-inserts the entry into the
table, which needs the table and therefore a socket. A test built on a stub key type would assert a
tautology (`seat < 0 or seat >= SkimmerCount`), not the behaviour. The change that would make it
testable — lifting the whole registration pass into a socket-agnostic proc over a
`seq[(key, text)]` — is a design change to the server loop, so I did not make it in a fix round.
Builder disclosure 11 ("no real websocket in test_server") already covers the gap.

## F10 — `sanitizeSay` stripped every brace

The filter now keeps braces and removes only **leading** ones after the strip, which is what the
note specifies and what the replay stream actually needs: `replays.nim:251` and `roster.nim:50` both
discriminate on `text[0] == '{'` and nothing looks at interior characters. `test_intents` pins all
three cases: `"{oops"` still loses its brace, `"a {tight} squeeze"` survives intact, `"{{{"`
sanitizes to nothing.

## F11 — the terminal fallback always said `attempt: 2`

Now `clamp(attempt, 1, 2)` — the loop's own count, inside the field's declared `1|2` domain (a turn
that never entered the loop reports 1). The fake-provider throttle case asserts the terminal record
says **1**; the two-failures case asserts **2**.

## F12 — the stale comment

`replays.nim` now says the recorded bytes are indexed **by skimmer index**, agreeing with
`server.nim`'s write loop and with `sim.step`. Comment only.

## F13 — the art is generated PNGs, not pixie bakes — documented, no code change

The pixie pipeline was not load-bearing for anything else: the property that matters (everything the
board draws is read from `data/`, the one directory the emscripten build preloads) is unaffected and
still tested, and the sprites are real per-role art with a committed generator
(`scripts/art/split_sheet.py`) and committed source sheets. The errata now separates the half of the
note that is true (water, caustics, rim, vignette are bakes; the rim plates are the starter's files
byte for byte) from the half that is not (the six object PNGs), and corrects "no downloaded art" to
"no art downloaded **at run time**".

## F14 — absent "kept verbatim" files — documented, no code change

Nothing references any of the ten files, so they are deletions, not dangling references; re-adding
unexercised files (a second toolchain pin, an unused atlas) would be worse than not having them. The
errata lists each one with the reason it is gone.

## F15 — the note asserted what the tree does not do

The errata section opened by F2 now also carries the §Tests 1 speed band (with the arithmetic that
makes the note's `2.6 … 3.3 m/s` impossible from its own constants), the swept test's
superset-not-equality claim, and the swept `BaselineParams`. `AGENTS.md` — which is what calls the
note "the design note this repo implements" — now says the note is kept verbatim as the pre-build
record and points at the errata, so a reader reaches it before trusting a number.

## F16 — the fixture re-implements the band

Two changes. The fixture's header now states plainly that it is **not** the shipped renderer and why
one cannot be loaded (no `client/renderer.js` exists: the board is composed Nim-side and blitted).
And the duplication is pinned instead of trusted: `global.nim` exports `bubbleBandCentreY` /
`bubblePillHeight` (the values `addBubbles` already used), the fixture's `BOARD_W`, `BOARD_H`,
`BAND_TOP`, `BAND_BOTTOM` are plain literals, and `test_viewer` re-derives all four from Nim and
asserts the fixture's band still contains the pill the renderer actually places — the same treatment
the 48/160-rune caps already had.

## F17 — the bubble pill had no clamp

**This settles the review's second "could not determine" by removing the question**, which is what
the reviewer suggested. `bubbleSlotX(slot, slots, spriteW)` clamps the slot centre into
`[w/2, BoardW − w/2]` and centres a pill wider than the whole board; `addBubbles` uses it. Whether
`data/font.ttf`'s advance widths would actually have overhung no longer matters. `test_viewer`
sweeps six widths (200 … 4800 px) across all three slots and asserts neither edge is ever crossed.

## F18 — the main smoke's `canvas_text.total = 0` — documented, no code change

A comment at the step that prints it now says the 0 is expected and not a pass (the harness wraps
the page's 2D context; this bundle draws from a Worker's OffscreenCanvas out of Nim-baked sprites),
and points at the fixture step as the evidence. CI run 32960525769 prints both:
`canvas text: 0 drawn …` for the bundle and `canvas text: 2850 drawn, 0 never inside the canvas`
for the fixture.

## F19 — 620 px vs 640 px

The requirement is met in substance and the mechanism is a class toggle, not a media query.
`test_viewer` now **parses the threshold out of the page** and asserts it is ≤ 640 instead of
matching the starter's literal line, so a starter bump past 640 reddens CI. The errata writes down
the mechanism, so the next reader's `grep 640px` returning nothing is explained.

## F20 — only one of two `broadcast_core.js` deltas was pinned

`test_viewer` now pins both, two-sidedly (waterworld text present **and** starter text absent),
which is the only available shape on a runner that has no starter checkout: `window.WATERWORLD_WIRE`
present / `window.CTF_WIRE` absent, and `in src/waterworld/sim_types.nim) and a packet is one such
state` present / `in src/ctf/sim.nim` absent. The note's "exactly the identifier" claim is corrected
in the errata; `diff` against the starter still reports exactly those two lines.

## F21 — sha1 vs sha256

The deviation is removed rather than documented: `crunchy/sha256` was already in the dependency tree,
so the pin is now the sha256 the note asks for
(`7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`, matching
`sha256sum client/chrome_common.js`). The deprecated `std/sha1` import is gone and AGENTS.md's
sentence follows.

## F22 — `speed` in `config_schema` — documented, no code change

The manifest is the consistent side: `sim_config.update` reads the field and `test_manifest` asserts
the schema covers every field `update` reads. Deleting the inherited, inert field would be a change
to the config contract rather than a fix to a stale sentence, so the errata records it instead.

## F23 — the `.tiny` sensor-ray rule — re-documented, no code change

It cannot be implemented as written: the board packet is built server-side and the server never
learns a viewer's stage width, and the client half (`broadcast_core.js`) is the starter's
byte-for-byte compositor, so it cannot filter object ids either. What ships is per-kind dimming
(clear ray α 0.30 / 3 pips / no hit disc; hit ray α 0.95 / 5 pips / hit disc) at every size, which
serves the legibility goal the rule existed for. The errata says so and names what *is*
`.tiny`-conditional (the legend, the thrust readout, the nibble counters).

---

## Checklist mapping

| item | how these commits bear on it |
|---|---|
| **1 — CI green, no test loosened** | run 32960525769 `success` on `main` at the reviewed head; F1–F4 restore or tighten every assertion the round flagged (0.35→0.11, 100→27 µm/tick, skip→bounded classes, deleted assertion reinstated over all six standoffs); F19 replaces a literal match with the property. No skip, no deletion, no widening in `git log -p 41bae66..f078434 -- tests/`. |
| **5 — degrade-never-hang** | F5 (budget covers the attempts it is sized for) and F6 (the 12 s floor is now interruptible in 100 ms slices) — both waits were already bounded; these make the bound behave as documented. |
| **8 — LLM reply handling** | F7 asserts the retry-once, throttle-fast-fail, fallback-recorded behaviour against a real client for the first time; F11 makes the recorded `attempt` field truthful for phase-60 counting. |
| **13 / 14 / 15 — viewer** | F16 pins the fixture's geometry to the renderer's; F17 removes the only unclamped text placement on the board; F20/F21 strengthen the provenance pins; F19 pins the legibility threshold as a number. |
| **10 — manifest** | F22 records why `config_schema` carries `speed`; no manifest change. |
| documentation of deviations | F2, F13, F14, F15, F19, F20, F22, F23 build one **Errata** section in the repo's copy of the design note, reached from AGENTS.md, so the note no longer asserts things the tree does not do. |

## NOTED (not fixed)

* `src/waterworld/server.nim:35` imports `llm` and does not use it — Nim prints an `UnusedImport`
  warning on every build of that module. Pre-existing, not in this round's review, left alone.
* `tools/ci/docker_smoke.sh` writes the binary `COWLDWWD` replay to `dist/smoke/replay.json`
  (the review's third "could not determine"). It works, `ci.yml`'s glob loop resolves it and the
  fixture step depends on the name; changing the extension would touch three files for no
  behavioural gain. Not a finding, not changed.
