# r1 fixes — pistonball

Head: `49518a22d734a3bcb952cc32952fe6e67eea39c6` (main)
CI: https://github.com/Metta-AI/cogame-pistonball/actions/runs/32928137084 — **success**
(`test`, `docker-smoke`, `wasm-viewer` all `success`; run created 2026-08-26T03:53:24Z on
head `49518a22`). The previous head `1f07e106` (run 32927918942) is also green and is the
run whose `wasm-viewer` log carries the new fixture's evidence, quoted under N10.

Range: `ce20047..49518a22`, seventeen commits, one per finding (N9's sub-items are committed
one per sub-item, since the review letters them and they are independent).

Every commit was pushed through the GitHub git-data API (blobs → tree with `base_tree` =
the remote head's tree → commit → `PATCH refs/heads/main` with `force=false`, re-reading the
remote head immediately before each update). No force-push, no history rewrite. File modes
preserved (`tools/build_replay_viewer.sh`, `tools/ci/docker_smoke.sh`,
`tools/ci/viewer_smoke.mjs`, `tools/ci/check_gameversion.sh` are all still `100755` in the
index).

| finding | disposition | commit | files |
|---|---|---|---|
| N1 | fixed | `cabb48d` | `docs/RULES.md`, `coworld_manifest_template.json`, `tests/test_manifest.nim` |
| N2 | fixed (angle) + evidence answer (torque/drag) | `5414e57` | `src/pistonball/sim.nim:320-327`, `sim_types.nim:27-101`, `tests/data/golden_hashes.json` |
| N3 | fixed | `835402f` | `src/pistonball/sim_state.nim:102-119`, `roster.nim:99`, `tests/test_scoring.nim:99-117` |
| N4 | fixed | `5083e62` | `.github/workflows/coworld-release.yml:167-184` |
| N5 | evidence answer + regression pin | `066fa17` | `tests/test_manifest.nim:154-178` |
| N6 | fixed | `7e2896e` | `src/pistonball.nim:7-24`, `tests/test_startup.nim:50-72` |
| N7 | fixed | `811ea0a` | `coworld_manifest_template.json` (`game.protocols`), `tests/test_manifest.nim:119-140` |
| N8 | DISPUTED (code correct; deviation now recorded) | `8ab425b` | `src/pistonball/llm.nim:203-216` |
| N9a/b | fixed | `fe09266` | `src/pistonball/llm.nim:38-70,161-169`, `decide.nim:404`, `tests/test_engine.nim` |
| N9c | fixed | `a47584d` | `tests/test_determinism.nim:36-59` |
| N9d | fixed | `680c4aa` | `tests/test_control.nim:87-124` |
| N9e | fixed | `f039287` | `tests/test_viewer.nim:1-45,101-107` |
| N9f | fixed | `59f00b2` | `tests/test_physics.nim:32-79`, `src/pistonball/sim_types.nim:27-44` |
| N9g | fixed | `135067f` | `tests/test_replay.nim:9-17,113-126` |
| N9h | NOT FIXED (evidence answer) | — | — |
| N10 | fixed | `1f07e10` | `tests/test_render.nim` (new), `src/pistonball/global.nim:32-42,369-395,700-726`, `tools/ci/renderer_fixture.html`, `.github/workflows/ci.yml:333-349` |
| N11 | fixed | `f71ccde` | `tests/test_perf.nim`, `tests/test_determinism.nim:23-33` |
| N12 | fixed | `49518a2` | `src/pistonball/bank.nim:70`, `sim.nim:436`, `control.nim:23-26`, `client/replay_broadcast.html` |
| N13 | evidence answer | — | — |

**No test was disabled, skipped, loosened or removed.** `git diff ce20047..49518a22 -- tests/`
is +576/−71, and every one of those 71 deleted lines is either a rewritten assertion that got
*stronger* (penetration `< 5000` → `<= 80`; mutation `±40` → `±1`; the ripple tautology → a
crest-position assertion; two substring probes → two sha256 pins) or the regenerated
`golden_hashes.json` (36 lines, see N2). Checklist item 1 is verifiable from that diff.

---

## N1 — the Rules page shipped pre-deviation physics — `cabb48d`

**Was:** `docs/RULES.md` — inlined verbatim into `game.docs.pages[0]`, i.e. the page the
platform shows players — still said `GravityPerSubstep = 4 257 … at 96 substeps/s` (`:76`),
"the ball is placed at (BallStartX, BallStartY) … Those two draws plus perm are the only
random numbers" (`:79-81`), "Each tick integrates 4 substeps of 1/96 s" (`:85`), "Four
substeps of 1/96 s" (`:106`) and the guard box `y in [400 000, 4 000 000]` (`:112`).

**Is:** the shipped constants, with the reasons: 16 substeps of 1/384 s and why the step had
to move; gravity 1 064; the guard's `[200 000, 4 300 000]` and why it carries 0.2 m of slack;
the third seeded draw `startOffsetUm = 20 000 + 10 000·rand(18)` and the corner-balance reason
it exists; and the scoring section's floor-at-zero clause from N3, with a note that the worked
examples measure from the 8.40 m drop line.

**Also found and fixed in the same commit:** the manifest carried a *second* stale copy nobody
had noticed. `game.docs.pages[2]` ("Writing a piston program") still described `wave` and
`catch` as firing when the ball is "at-or-right-of me" — the exact inversion of
`control.nim:65,75` and of the corrected `docs/SCRIPTS.md`. That is the N8 inversion, shipped
to players. All four documents are re-inlined from their files.

**Evidence:** `tests/test_manifest.nim` "every docs page is the SHIPPED file, byte for byte"
now asserts `pages[i].content.value == readFile(<file>)` for all three pages and the readme, so
a doc edit that stops at the file can no longer ship a stale page. Checklist item 10 (manifest
shape) unaffected and still asserted.

## N2 — the three unrescaled per-substep constants — `5414e57`

Split, because the two halves have opposite answers.

**Angle: fixed.** `sim.nim:323` was `angleQ = (angleQ + spin div 4 …)` inside a loop that runs
16 times, so the drawn ball highlight advanced by `4·spin` per tick. `spin` is 1/16 brad **per
tick** — that is the unit the rolling relation `spin = −vx·652/R` at `test_physics.nim:78` is
written in — so the rendered ball was turning four times faster than the ball it is painted on.
Now `spin div int64(SubSteps)`. `angleQ` feeds only `global.nim:495` (the sprite frame) and the
hash, never the dynamics, so this is a pure presentation + hash change: the tuning pin is
bit-identical afterwards (`wavebot: 20/20 delivered, mean 97.053 · metronome: mean −10.067 ·
10/10 mix: 20/20`, byte-for-byte the numbers from the reviewed run's CI log).
`tests/data/golden_hashes.json` regenerated for the new chain — the only reason it changed.

**Torque and the two drags: answered in place, with a measurement.** Rescaling them to the
note's per-tick equivalents (`TorqueScale 28_294 → 7_074`, `AirDragNum 8 → 2`,
`SpinDragNum 12 → 3`) is exactly what the 4→16 substep change would imply, and I built it and
measured it before rejecting it:

| | wavebot delivered | wavebot mean | metronome mean | 10/10 mix | shortest cert-fixture episode over 24 seeds |
|---|---|---|---|---|---|
| shipped | 20/20 | 97.053 | −10.067 | 20/20 | **900 ticks (never delivers)** |
| rescaled | 20/20 | 97.969 | −1.510 | 20/20 | **53 ticks — 4 of 24 seeds deliver** |

The certification fixture is 1 wavebot + 19 metronomes precisely because a short replay reads
as frozen to the viewer smoke's 12 s soak (`844697a`). The rescale makes the metronomes
deliver, which re-breaks that. So the four constants are one tuned set on the 384 Hz timebase,
and `sim_types.nim:69-86` now says so — including the per-tick consequence the review derived
(an effective rotational inertia near 120 rather than `BallInertia = 480`; a tick of air drag
`(1−8/4096)^16 = 0.969` rather than `^4 = 0.992`) — instead of a docstring that quietly
described the note's timebase. `GameVersion` is left at 1: nothing has been published under it
(this is the pre-release run), and the changelog comment is untouched, so
`tools/ci/check_gameversion.sh origin/main` still exits 0.

## N3 — the score floor — `835402f`

**Was:** the ball is dropped at `BallStartX − startOffsetUm` while the guard clamps
`x ≤ BallStartX`, so an episode can end right of where it started and the telescoping sum goes
negative. Reproduced: seed 63352, twenty metronomes, `progressMilli = −2253`, score
**−20.243** — against the "exactly −18.000" that `docs/RULES.md`, the shipped system prompt
("Doing nothing scores −18"), the endcard copy and `design.md:306-310` all promise.

**Is:** `progressPoints()` clamps at zero and `scoreMilli()` is built from it, so every
consumer (results JSON, broadcast state, endcard, the server's end-of-episode log) reports a
score in `[−18.000, +100.000)`. The clamp is on the way **out**, never on the accumulator:
`progressMilli` stays a signed telescoping sum, so backsliding inside a run still costs exactly
what it gained and no bank can mine the clamp by shoving the ball right and pulling it back.

**Evidence:** new `tests/test_scoring.nim` case plays the real episode (seed 63352, metronomes)
and asserts `progressMilli < 0`, `progressPoints() == 0`, `scoreMilli() >= −18_000` and
`results["progress"] == 0.0`. The old floor test computed the floor analytically from
`BallStartX`, which is why it never saw this.

## N4 — certify timeout — `5083e62`

`--timeout-seconds 300` added to the certify step, as `design.md:1284-1286` requires, with the
reason recorded in place (the fixture is a real 900-tick, twenty-container episode and is not
shrunk). The `--timeout-seconds 900` at `:311` is the upload step and is untouched. YAML
re-parsed. Cannot be exercised by `ci.yml` — `coworld-release.yml` only runs on release.

## N5 — the fixture's fleet — `066fa17` (evidence answer + a pin)

The composition (1 baseline + 19 metronomes, not twenty baselines) is deliberate and already
recorded in `844697a`; I am not changing it. What was missing is a guard on the property it
buys. New `tests/test_manifest.nim` case reads the fleet out of the manifest itself — declared
`player[].id` → `PLAYER_SCRIPTED` → baseline — and asserts the fixture's own `maxTicks` are
played out with no delivery, on three seeds (three, not one, because the fixture's seed is the
randomisation sentinel: see N6). This is the guard that would have caught the N2 rescale.

## N6 — the sentinel seed — `7e2896e`

The observation is right: `certification.game_config.seed == LegacyFixedSeed`, so `seedPinned()`
is false and the entrypoint injects a fresh seed and strips the config's. The answer is to keep
it and say so, not to pick a different fixture seed: `coworld_manifest_template.json` is a
**public** document, so a seed pinned there is a seed every entrant can read, and a
pre-computable `perm` is the exact thing the sentinel exists to prevent. Certification asserts
an outcome that holds for every seed (twenty seats, a full-length episode, `reason=complete`),
not one recorded hash chain; a forensic re-run names any other seed and gets it honoured.

`LegacyFixedSeed`, `seedPinned` and `stripUnpinnedSeed` are exported so the test exercises the
real procs instead of grepping the source. New test asserts the fixture's own config text is
not treated as pinned, that `{"seed": 20260825}` is, and that the sentinel key is stripped.

## N7 — two protocols — `811ea0a`

`protocols.player` and `protocols.global` were the same 5147-byte string. Both are now written
for their own reader: the player text covers the registration frame, that seats send no inputs,
the window-filtered per-tick frames, the per-seat view with its hidden-with-no-exception list,
and the tolerant reply parse; the global text covers `/global` perfect information, the chrome
JSON riding sprite 4090's label, why the three `/client/` routes exist and that they are **not**
how a match is watched (the static S3 bundle is), and the COWLDPST replay with its per-tick
re-derivation. Test asserts they differ and that each carries four markers the other must not.
Checklist item 10 still satisfied (both keys present, both `{"type":"text","value":…}`).

## N8 — the prompt's wave/catch wording — DISPUTED — `8ab425b`

The code is right and the note is the inconsistent document; no behaviour changed. The
controller fires both clauses on `dxp <= 0` — ball at or left of my centre — at
`control.nim:65` and `:75`. The note's own controller table (`design.md:602,607`), its phase
rule (`design.md:268`, "UP when `centreX_i ≥ ballX`") and `docs/SCRIPTS.md` all agree with the
shipped prompt; only `design.md:520-527` says the opposite. The commit adds the comment the
review said was missing, so a reader diffing the note against `llm.nim` sees a recorded
deviation instead of an unexplained change. (The *manifest's* copy of the piston-program page
did carry the note's inverted wording — fixed under N1.)

## N9a / N9b — the fake provider — `fe09266`

**Was:** `tests/test_engine.nim` only ever ran the credential-less client, so none of
`design.md:1373-1379` was asserted. **Is:** `LlmClient.sendBatch` is a seam around the one call
that leaves the process — `nil` in every build the server runs (`newLlmClient` never sets it;
`sendTurnBatch` falls through to `curl.makeRequests`) — and the tests install a fake that
records each batch's size, per-seat tags and in-flight window and can answer late, unparseably,
or 429. Six new assertions:

- one batch of twenty, each seat tagged exactly once, one shared in-flight window (sequential
  calls would give twenty disjoint ones);
- two turns whose batch **starts** are ≥ `minBatchSpacingMs` apart;
- a provider answering 500 ms into a 300 ms turn budget: exactly one batch, the turn hands back
  inside the budget with a `timeout` fallback naming it, every seat still holding a legal
  script;
- a parse failure retried **exactly once**, the retry going out as a batch too;
- a reply that never parses stopping after the **second** batch, not a third;
- a 429 producing **one** batch, `client.throttled`, and `throttled` fallbacks.

## N9c — one unit — `a47584d`

`±40` → `±1`, swept over three ticks × three seats (0, 7, 19) rather than one byte of one seat,
since "any command byte" is the claim. All nine mutations diverge from the mutated tick on.

## N9d — the ripple — `680c4aa`

The old check built `float(piston)/float(PistonCount)` and asserted it increases — it never
called `rippleHeight`. Now: for each column, find the tick inside one 48-tick period at which
`rippleHeight` peaks, assert it is where the phase formula puts it (`12 + 2.4·i`, rounded),
that it advances 2 or 3 ticks per column, and that it laps **exactly once** across the bank
(20 × 2.4 = 48). Also asserts the wave stays inside `[idle_m, up_m]` at every tick of every
column.

## N9e — sha256 pins — `f039287`

`chrome_common.js` pinned to the starter's digest
`7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`; "broadcast_core.js differs
in exactly the `PISTONBALL_WIRE` identifier" is now checked by undoing the rename and hashing
back to the starter's `172c4680129d608fd687cfd86436b675eef32c8652be6afe5f3189dd20c5aa9c`.
`crunchy` (already in `nimby.lock` and on the `nim.cfg` path) provides sha256. Directly
supports checklist item 14 — id-presence is not evidence, and a lookalike is what it is for.

## N9f — resting penetration — `59f00b2`

Measured before pinning: at strokes 0 / 0.20 / 0.80 / 1.60 m and three seeds the settled
penetration is a limit cycle of **0 … 65 µm**, not the note's 200–600 µm and not the 392 µm the
`SubSteps` docstring claimed the design pins. 392 µm *is* the static equilibrium of the spring
alone (150 mN/µm against a 6 kg weight on this timebase); the ball never reaches it because the
pose update truncates `v div SubSteps`, so a vertical speed under 16 µm/tick moves the ball
zero micrometres and it rides one substep of gravity (1064/16 = 66 µm) above equilibrium. Test
samples ticks 240–600 and pins `0 … 80`; the docstring records the measurement. Also adds the
same paragraph's other unasserted claim — friction never reverses the slide direction within a
substep — over 240 ticks of a sliding ball away from the walls.

## N9g — handoff and launch — `135067f`

The recorded episode never set `collectEvents`, so the tier-2 stream was empty and no assertion
could have seen them. The fixture now sets it the way the server does, and the vocabulary test
asserts ≥ 1 `handoff` and ≥ 1 `launch` with every event's tick inside the episode.

## N9h — the running-server socket contract — NOT FIXED (evidence answer)

`tests/test_server.nim` unit-tests the parsers and greps the route table; the note's test 11
wants those exercised against a **running** server. I did not add that and I am recording it
rather than claiming it: standing a real `mummy` server up inside the unit suite is a new test
harness, not a fix at a cited site, and the properties it would cover are the ones
`tools/ci/docker_smoke.sh` already exercises end-to-end in CI against a real container —
`/healthz` and `/global` answering, the artifact writes to `file://` URIs, the twenty player
containers exiting 0, `reason=complete`. Run 32928137084's `docker-smoke` job is that evidence
for this head. What would settle the remainder (an input mask from a player being ignored, and
`/global` still answering 15 s after the artifacts are written) is a socket-level test against
a bound port; that is a phase-40 harness decision, not a one-line fix.

## N10 — the renderer fixture and the zero canvas_text — `1f07e10`

The review is right that the fixture drew its own strings in `system-ui, sans-serif` and that
the bundle run's `canvas_text.total: 0` covers nothing. I traced every path model text takes to
a spectator, and the literal clause "loads the real `client/renderer.js`" is unsatisfiable
because there is no JS renderer: a `say` is baked into a plate by `bakeBubble`
(`global.nim:369-395`, pixie + `data/font.ttf` at size 20) and blitted as a Sprite v1 sprite by
the wasm build; a `note` is a DOM `.feed-row` written by `pbFeed`
(`replay_broadcast.html:4317-4319`). Neither is a 2D-canvas `fillText`, so the bundle's zero is
structural, not a regression. So I gated the text where it *is* drawn, in two halves that each
say what they cover:

1. **`tests/test_render.nim` (new) — the real renderer, in the language it is written in.** It
   bakes full-cap strings through the production `bakeBubble` (48 runes ending on a 4-byte
   codepoint; the widest legal 48 runes, `"WWW…"`) and measures the **pixels**: ink exists, ink
   sits inside the plate with clearance from the border, and the width formula never reaches the
   `MapWidth − 40` clamp at which pixie would clip the caption. Measured: the widest 48-rune
   line bakes to a 796 px plate against a 1160 px clamp, which also settles the review's "could
   not determine" about whether a full-cap `say` fits the face — it does, with 364 px to spare.
   It also asserts every slot's whole plate lies inside the reserved band and between the walls
   at every piston.
2. **The fixture is now the production geometry in the production face.** It fetches `font.ttf`
   as bytes and installs it with the FontFace API (no content-type guess in the way), evaluates
   `bakeBubble`'s own width formula at the plate's own size in board pixels, draws at 360 / 620
   / 1280 px, and refuses to signal loaded if a plate hits the clamp, runs past its own edge,
   leaves the board or leaves the band; the 160-rune `note` is checked as what it is — a DOM
   feed column that must wrap rather than overflow. Its header and the `ci.yml` step name say
   plainly that it is not the wasm renderer and point at (1) for the pixels.

**And it found a real defect while being written:** at the old pitch of `band/3`, the third
34-row plate sat **five rows past** the band's bottom edge, so "the band is reserved" was true
of the plates' top-left corners and not of the plates. `BubbleSlotStride` is now derived from
the plate height, and `bubbleSlotY`/`bubblePlateX` are named procs so placement is testable
instead of inline in `addBoard`.

**Evidence (run 32927918942, `wasm-viewer`, step "Full-cap speech-plate fixture at 360 / 620 /
1280 px"):**
`{"loaded":true,"ms":283,…}` and
`canvas text: 60 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`. Sixty draws, all inside, in the shipped face. Reproduced locally first
against the pinned Playwright chromium.

## N11 — the 1800-tick tests — `f71ccde`

Both now drive the metronome fleet, whose blind ripple never delivers, and both assert
`tickCount == 1800` so the label cannot drift from the work again. Runtime bounded: the release
perf run prints `1800-tick episode + 36000 controller evaluations: 22 ms`.

## N12 — residue — `49518a2`

Each item as listed: `bank.nim`'s "two random draws" over three bullets; `sim.nim`'s "four
substeps" section comment; the unused `RippleColumnTicks` (deleted — an unused constant that
looks load-bearing is worse than none); the duplicate `var head` in `pbRenderEndcard` (the
second is now `thead`); and the inherited `#fpv` comments that the identifier sweep had turned
into "pistonball markers" / "pistonball comet tracers" for features this game does not have.
No behaviour changes; all script blocks in the page re-checked with `node --check`.

## N13 — `/client/replay` — evidence answer, no change

Confirmed from both sides and deliberately not "fixed":

- the route table is the starter's, unmodified. `/workspace/starters/coworld-ctf`'s
  `src/ctf/server.nim:825-826` answers `bitworldClient.ReplayClientRoute` /
  `CoworldReplayClientRoute` from the same `elif` shape pistonball uses at
  `src/pistonball/server.nim:201-216`, and the constants are bitworld's
  (`client.nim:21,26`);
- the design note requires it — "**both `/client/` routes serve real pages** … the certifier
  probes them before starting player pods" (`design.md:780-783`) — and the code comment at
  `server.nim:211-214` says the same;
- **no manifest key points the platform at any of them.** `game.replay_viewer` is
  `{"bundle": "static-replay-viewer"}`, asserted at `tests/test_manifest.nim:106-107`, and the
  static bundle fetches only its `?replay=` URL
  (`replay-viewer/static_replay_worker.js:113-121`).

So checklist item 3's "no `/client/replay` pod path anywhere" is satisfied in the sense that
binds — the manifest declares no pod replay viewer — and deleting the route would break the
certifier's own probe, which is why I did not. Recorded for the judge rather than resolved by
me.

---

## NOTED (not fixed)

- `design.md:1030-1032` says the `coworld-replay` bridge fires `ready` after
  `data-replay-loaded`; the page posts `boot` and `frame` and no `ready`. Inherited from the
  starter verbatim (same lines, only the src id renamed), so changing it would fork the shared
  chrome for a contract neither repo defines. Left alone.
- `replay-viewer/config.nims:47` adds `--preload-file …/client/art@client/art`, which the note
  does not mention. It is needed for the wall and locker art the wasm renderer bakes, and the
  rest of the file is the starter's. Left alone.
- `tests/test_engine.nim`'s spacing and budget cases sleep 250–500 ms of real time. That is the
  price of asserting a wall-clock contract; the whole file still runs in about a second.
