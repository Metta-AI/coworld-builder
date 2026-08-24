# r1 fixes — matrix-games

Repo: `Metta-AI/cogame-matrix-games`. Reviewed sha `7b7d586`; **head after fixes `af5c704`**.
15 commits, one per finding, in review order. CI: run **32755082249** (`ci.yml`, push, head
`af5c704`) — conclusion recorded at the end of this file.

Every fix was compiled and every test file was run locally in **both** modes (`nim r` and
`nim r -d:release`) before the push; the sandbox has Nim 2.2.4 and the nimby package tree, so
`tests/*.nim` are runnable here (docker and emsdk are not, so the docker-smoke and wasm-viewer
halves are proved only by CI).

No test was disabled, skipped, loosened or deleted. Four commits **add** assertions
(F23, F40, F47, F65, F67); none removes one.

## Disposition table

| finding | kind | disposition | commit | files | checklist item |
|---|---|---|---|---|---|
| F1–F7 | match | no action | — | — | — |
| F8 | gap | fixed | `1e1593a` | `src/matrix_games/sim_state.nim:121-126` | 14(d) legibility of the scrubber |
| F9 | gap | no change (reasoned) | — | `src/matrix_games/sim.nim:112` | — |
| F10 | gap | no change (reasoned) | — | `src/matrix_games/kernel.nim:109-122` | 7 |
| F11 | gap | no change (reasoned) | — | `src/matrix_games/kernel.nim:222-236` | 7 |
| F12 | unclear | no change (reasoned) | — | `src/matrix_games/kernel.nim:124-175` | — |
| F13 | match | no action | — | — | — |
| F14 | unclear | no change (reasoned) | — | `src/matrix_games/indices.nim:74` | — |
| F15, F16 | match | no action | — | — | — |
| F17 | gap | no change (reasoned) | — | `src/matrix_games/sim.nim:328` | — |
| F18 | unclear | no change (reasoned) | — | `src/matrix_games/sim.nim:87-94` | — |
| F19–F21 | match | no action | — | — | — |
| F22 | unclear | no change (reasoned) | — | `src/matrix_games/llm.nim:545-549` | 8 |
| F23 | gap | fixed (test added) | `8cf9ffb` | `tests/test_llm.nim:212-242` | 8 |
| F24, F25 | match | no action | — | — | — |
| F26–F28 | match | no action | — | — | — |
| F29 | gap | fixed | `220aa5c` | `src/matrix_games/sim_config.nim:92-104`, `sim_types.nim:91-95`, `server.nim:161-179` | 5 (timeout) |
| F30, F31 | match | no action | — | — | — |
| F32 | unclear | fixed | `f082554` | `src/matrix_games/server.nim:230-273` | 5 (hang) |
| F33 | match | no action | — | — | — |
| F34 | gap | fixed | `b178474` | `src/matrix_games/llm.nim:334-340`, `tests/test_llm.nim:31-41` | 9 |
| F35, F36 | match | no action | — | — | — |
| F37–F39 | match | no action | — | — | — |
| F40 | unclear | fixed (test added) | `74e0572` | `tests/test_viewer.nim:188-213` | 2 |
| F41–F46 | match | no action | — | — | — |
| F47 | gap | fixed (test added) | `8a1b119` | `tests/test_viewer.nim:122-166`, `tests/support/helpers.nim:38-75` | **2** |
| F48, F49 | match | no action | — | — | — |
| F50 | gap | fixed | `786db23` | `client/replay_broadcast.html:781-835` (deleted) | 14 (provenance) |
| F51 | gap | fixed | `3c0aa54` | `client/replay_broadcast.html:1871,1893`, `tests/test_viewer.nim:228-235` | 11 / 14 |
| F52, F53 | match | no action | — | — | — |
| F54 | gap | partly fixed | `6e0178a` | `client/replay_broadcast.html:2152-2168` | **11** |
| F55 | gap | no change (reasoned) | — | `replay-viewer/static_replay.js` | 13 |
| F56 | gap | no change (reasoned) | — | `client/broadcast_core.js:335-347` | 14 (viewpanel) |
| F57, F58 | match | no action | — | — | — |
| F59 | gap | fixed | `839653d` | `src/matrix_games/server.nim:437-447`, `client/global.html:36-40`, `client/player.html:37-41` | **3** |
| F60 | match | no action | — | — | — |
| F61 | unclear | no change (reasoned) | — | `coworld_manifest_template.json` cert fixture | 4 |
| F62, F63 | match | no action | — | — | — |
| F64 | gap | fixed | `cb2430a` | `.github/workflows/ci.yml:306-318` | **13** |
| F65 | gap | fixed (test added) | `e47b6c8` | `tests/test_indices.nim:9-31, 113-130` | 7 |
| F66 | gap | fixed | `af5c704` | `tools/ci/docker_smoke.sh:271-372` | 6 / 10 |
| F67 | gap | fixed (test added) | `72b0cf6` | `tests/test_sim.nim:5-21, 253-280` | 1 / 7 |
| F68, F69 | match | no action | — | — | — |
| F70 | gap | no change (reasoned) | — | `scripts/art/gen_matrix_art.py:9-14` | — |
| F71 | gap | no change (reasoned) | — | `src/matrix_games/server.nim:148-156` | — |

---

## The fixes

### F8 — a `leadchange` at tick 0 — `1e1593a`
`initSim` seeded `lastLeader = -1`, and `leader()` returns slot 0 when every score is 0, so rule 9
fired on the first tick of every episode and both timeline builders (`broadcast.nim:55`,
`global.nim:155`) turned that into a "Lead change" scrubber button at t = 0. Rule 9 emits when the
leader differs from **last tick**; at tick 0 there is no last tick, so the seed is now the opening
leader (slot 0). Evidence: an episode (`prisoners-dilemma`, seed 51, 3 beats) emitted 3
`leadchange` events, **0 of them at tick 0**, where before the fix the first was at t = 0.
`tests/test_viewer.nim`'s "the beat timeline emits four kinds and only four" still passes (it
requires `over` and `interact|bigpay`, never `leadchange`).

### F23 — no test exercised 401/403 disabling the client — `8cf9ffb`
The disable lives in `textOf`, which `batchHook` short-circuits, so the behaviour design.md:500
pins was uncovered. The new case hands a `Response(code: 401)` and a `Response(code: 403)` straight
to `client.textOf`, asserts the raise, asserts `client.disabled` flipped, and asserts the following
`decideAll` opens **no** batch (`batchSizes.len == 0`) and returns `osFallback` for all eight seats.
Evidence: `[OK] a 401 or a 403 disables the client for the rest of the episode`.

### F29 — the play deadline was stamped before the connect wait — `220aa5c`
The stamp is deliberately before the connect wait: the 720 s bound is what keeps the **whole
episode** inside 60 % of `episodeTimeoutSeconds`, which is what acceptance item 5 asks for. Moving
the stamp to the start of play would have allowed a 180 + 720 = 900 s episode and made item 5
*worse*. The real defect was the arithmetic: `validate()` only required `beats × 2 ×
llmTimeoutSeconds` (480 s) to fit, so the note's headroom was imaginary. `validate()` now requires
`playerConnectTimeoutSeconds + RegistrationGraceSeconds + beats × 2 × llmTimeoutSeconds` to fit
inside the play deadline — 180 + 3 + 480 = **663 ≤ 720** at the defaults, 180 + 3 + 240 = 423 for
the certification fixture — and a config that cannot finish in time now fails at startup instead of
settling as `deadline`. The 3 s registration grace became the named constant both `validate()` and
`server.nim` use, so the two cannot drift. Evidence: all seven variants and the cert fixture pass
`validate()` (test_manifest, test_sim, test_indices green); the game binary compiles and the
comment at `server.nim:162` now states the arithmetic.

### F32 — the game thread had no exception guard — `f082554`
`runGame`'s beat loop runs on its own thread while `gameServer.serve` keeps `/healthz` answering. A
raise out of `installOrders`, `runBeat`, `buildObservation` or `replayBytes` would have killed the
thread and left a container that looks healthy, writes no artifacts and never quits — a hang, which
is exactly the category acceptance item 5 blocks on. The loop is now wrapped: on a
`CatchableError` it logs, calls `finish("deadline", "deadline")` (a legal reason: the beats played
are scored, nothing is imputed) and falls through to the normal artifact write and 20 s grace.
Evidence: the binary compiles and the loop body is unchanged apart from indentation.

### F34 — byte truncation of an echoed error — `b178474`
`head[0 ..< 160]` is a byte slice on the one branch that fires on a *prose* reply — where the
multi-byte characters are — so the `MatrixGamesError` message could carry invalid UTF-8. Replaced
with `cleanText(text, 160)` (strip → `utf8Only` → rune-boundary cut). The reviewer is right that it
never reaches the replay, and the same line exists in bullwhip; it was one line to make correct, so
it is fixed rather than disputed. Evidence: a new test feeds 300 `\u4e2d` runes and asserts
`validateUtf8(error.msg) == -1` and `runeLen <= 200`; the same input produced invalid UTF-8 before.

### F40 — `conventionCounts` recorded twice, never cross-checked — `74e0572`
New test: on a coop-token variant and a coopToken-less one, the viewer's re-derived histogram (the
forward fold of `interact` events in `global.nim`) is compared cell-for-cell against
`replay.indices.conventionCounts` (the sim's running accumulator), its cells are asserted to sum to
`state.idx.interactions`, and its `coopRate` is compared to the recorded one including the `null`
case. Evidence: `[OK] the viewer's re-derived indices agree with the recorded ones`; mutating one
cell by +1 makes it fail (verified).

### F47 — no frame-by-frame re-derivation test — `8a1b119`  *(acceptance item 2)*
Matrix Games records **state**, not inputs, so there is no re-simulation to compare against — the
recorded frame *is* the source. The honest form of item 2 is therefore: the viewer reproduces the
recorded per-tick state exactly and derives its display from nothing else. `runScriptedRecording`
(new, in `tests/support/helpers.nim`) plays an episode capturing the sim's **own** state after
every tick; the new test drives `ViewerState` over the replay bytes of that same episode and
asserts, for every one of the 150 ticks and all 8 seats: the board frame (`c` quad = x, y, facing,
freeze; `inv` block; `sc`), the chrome `seats[]` the page draws (position, `frozen`, `scoreCp`,
inventory, and the event-folded `interactions` count), and the per-spawner `tok` map all equal the
sim's state at that tick. Evidence: `[OK] every tick of the packet is the sim's own state at that
tick`; perturbing the captured `x` by 1 makes it fail (verified).

### F50 — dead cogame-raid CSS above the banner — `786db23`
55 lines of `.ev-lane` / `.ev.death` / `.ev.enrage` / `.ev.crucible` / `.ev-tip` CSS sat inside the
*inherited* region, of which design.md:747-750 says "nothing above them is rewritten"; nothing in
the page emits those classes. Deleted. Evidence: the CSS between `.momentum-label` and
`.beat-marker` is now byte-identical to `/workspace/starters/coworld-ctf/client/replay_broadcast.html`
(checked programmatically); `tests/test_viewer.nim` green.

### F51 — feed rows and banner chips matched no selector — `3c0aa54`
`mgPushRow` wrote `class="kf-row"` and `mgBanner` wrote `class="banner"`; the inherited stylesheet
styles `.feed-row` (padded, tinted lower-third row, pixel font) and `.banner-chip` (chip with the
amber underline and the `chippop` animation). The feed and the banner lane were therefore unstyled
text. Both call sites now emit the inherited class names, and a new test asserts that the class a
row/chip is given has a rule in the page — the same shape as the existing per-beat-kind CSS test.
Evidence: `[OK] feed rows and banner chips use classes the stylesheet actually styles`.

### F54 — `relayout()` reimplemented; `.tiny` at 620 px — `6e0178a` *(partly fixed)*
**Fixed:** the `.tiny` threshold was `width <= 620`, so between 620 and 640 px the eight plates kept
their policy names and encounter counts, which falsifies acceptance item 11's "labels hidden under
`640px`" as written. It is now `width < 640` (the 360 px featured-match frame was always inside
either bound). The comment claiming the loop is the starter's "VERBATIM" was false and now
describes what the code is: a single pass that sets `--hudscale`, `--band` and `--topband` on
`document.documentElement` and delegates the board fit to `mgCore.setViewportFit()`.
**Not fixed:** restoring the starter's four-pass fixed-point `relayout()` verbatim is not possible
without also restoring the starter's board pipeline (`#viewpanel`, the binary sprite core) that the
design note deletes; item 14(a)'s actual requirement — `--band`/`--hudscale` set on `:root`, not on
`#stage` — is satisfied, as the reviewer states. Recorded as a documented deviation, not a
NEEDS-DESIGN blocker.

### F59 — `/client/replay` pod route — `839653d` *(acceptance item 3)*
`buildRouter` registered `GET /client/replay` serving `client/replay_broadcast.html` off the game
container (inherited from paintbot's `bitworldClient.ReplayClientRoute`). Item 3 is literal — "No
`/client/replay` pod path anywhere" — and the design note's route table does not list it. The route
and `replayPageHandler` are gone, as are the two links to it in `client/global.html` and
`client/player.html`, and the header comment no longer advertises it. Evidence: `grep -rn
"/client/replay" src/ client/*.html` returns nothing; `tests/test_manifest.nim` (already asserting
`replay_viewer.url == nil` and `"/client/replay" notin $game.runnable`) is green.
*Left in place, deliberately:* `--load-replay` mode (`runReplayServer` + `/replay-data`) still
serves the replay **bytes** for local inspection. It serves no HTML and no viewer, so it is not a
pod replay path; removing the whole CLI mode would have been wider than the finding.

### F64 — the viewer soak never ran — `cb2430a` *(acceptance item 13)*
`viewer_smoke.mjs` defaults `--soak` to 0 and gates the entire soak on `args.soak > 0`, so
`wasm-viewer` only ever proved the bundle *loaded*. `ci.yml` now passes `--soak 10`, which is the
design note's pass condition (design.md:1063-1069): three samples of clock/tick/scorebug, and the
**last** interval has to keep moving. The certification fixture plays 300 ticks = 12.5 s at 24 fps,
deliberately longer than the soak, and `static_replay.js` starts with `playing = true`, so a healthy
bundle is mid-playback for the whole window. Evidence: the CI run cited at the end of this file.

### F65 — `test_indices.nim` dropped half of the chicken clause — `e47b6c8`
The note asks for two things in chicken and only the second was asserted. The first — "one
`always-second` in a room of `always-first` tops the table" — is **measurably false** in this
implementation, for the same positional reason the file already documents for PD: measured here,
the lone hawk resolves 5–11 times against a dove's 11–19 (the doves interact freely with each other
while the hawk is frozen out by the 12-tick freeze + 25-tick beam reset), and it tops the table on
**none** of seeds 1..8 at **any** of the 8 slot placements (0/8 in every case). What the note is
after — hawk beats dove where they meet — is now asserted per resolution, the form the file already
uses for PD: across seeds 1..8, all 28 mixed-cell resolutions have the hawk side strictly
out-earning the dove side. The file header now lists this as the third restatement, with the
evidence, so the deviation is declared rather than silent. Evidence: `[OK] chicken: hawk out-earns
dove wherever the two meet`.

### F66 — `docker_smoke.sh` did not validate `results.json` against the results schema — `af5c704`
The smoke checked existence, UTF-8 JSON, non-empty object and seat-length `names`/`scores` — and
only **warned** when a key was missing. design.md:1057 has it validate against the results schema,
which is what the platform does at certification, so a results object the game writes but the
schema rejects would have gone green here and red there. The artifact step now loads
`game.results_schema` from the manifest and validates: type unions (including `["number","null"]`),
`enum`, `required`, `additionalProperties: false`, `minItems`/`maxItems`, `minimum`/`maximum`,
recursively through arrays and objects. No `jsonschema` dependency (the runner does not ship it);
failures exit non-zero with a `RESULTS-SCHEMA FAIL:` prefix. Evidence: run locally against real
`resultsJson` output for **all seven variants** (all pass, 17 keys each) and against seven
mutations — missing `reason`, 7-entry `scores`, `reason: "crashed"`, an undeclared key,
`coopRate: 2.5`, integer `win[]` — all six illegal ones caught, and the legal one
(`exploitability: [null × 8]`) accepted.

### F67 — determinism only compared two `Sim`s in one process — `72b0cf6`
The note asks for the identical `gameHash` "twice in one process **and across a fresh
`SimServer`**". This game has no `SimServer`; the equivalent of a fresh server is a fresh process.
With `MATRIX_GAMES_HASH_SEED` set, the test binary now plays one episode, prints its `gameHash` and
`quit(0)`s before any suite runs; the determinism suite spawns itself that way and asserts same
seed → same hash across processes, different seed → different hash. The in-process pair is
unchanged. Evidence: `[OK] a fresh process reproduces the same hash from the same seed`, in both
debug and `-d:release`.

---

## Reasoned no-changes (with evidence)

**F9 — `updateSight()` is an unnumbered step.** Correct as built. It writes only `memX/memY/memTick`
(`sim_state.nim:200-206`), the per-observer memory `buildObservation` reads for `seenTicksAgo`; it
changes no rule-visible state, so it cannot change an outcome. The note's ten steps are the *rules*;
this is the bookkeeping that makes the observation's "last known cell" field meaningful, which the
note requires at design.md:358-359. Making it a numbered rule would be a note edit, not a code fix.

**F10 — the "least-bad sidestep".** Real deviation, deliberate, and reverting it would break gate
(a). The code comment (`kernel.nim:86-91`) records the reason: with a strict "wait if no step
reduces the distance" rule, two cogs walking into each other lock solid for the rest of the episode
and a seat finishes with zero resolutions — which `tests/test_indices.nim` gate (a) ("every seat
resolves at least once", asserted over 7 variants × 8 seeds) catches. The behaviour is fully
deterministic (BFS distances, direction order N, E, S, W). Restoring the note's literal wording
would be a **design change** that trades a passing feasibility gate for a sentence: recorded as a
documented deviation for the judge, not silently changed.

**F11 — `hunt`'s `sweepStep` fallback.** Same shape as F10: deterministic, documented at the call
site, and it exists so a `hunt` whose target is unreachable (behind a freeze, or in a cell the BFS
cannot enter) does not stand still for 50 ticks. Removing it costs resolutions on the same gate.
Documented deviation.

**F12 — `gather`/`deny` read the full spawner list.** The note's own architecture makes this
correct: the kernel is the *game's executor*, not a policy (`kernel.nim:9-11`, design.md:535 lists
it game-side), and every seat's kernel is identical, so it grants no seat an advantage over
another. The information restriction the note cares about is on the **policy** input, and that is
enforced where it matters: `buildObservation` gates other cogs' positions and inventories on
`viewRadius` + Bresenham line of sight, and `tests/test_baseline.nim` asserts the baselines read
only `buildObservation`. Also, the tie-breaks the note pins (lowest `y`, then lowest `x`) match.
Changing the kernel to a per-seat view is a design decision, not a defect fix.

**F14 — exploitability picks the side by majority.** The note does not say what a seat that played
both sides should do, so there is nothing to falsify. The choice only has an effect in
`bach-or-stravinsky`, where a seat's side is fixed by camp and the branch never triggers; in the six
symmetric variants `colPay = transpose(rowPay)`, so the answer differs only through `avgOpp`. No
change without a coordinator ruling.

**F17 — `you.fixedType` in the observation.** Required by the note's own baseline spec: design.md:481
defines `fixed-pick` as `myType = (seed + slot) mod K` and design.md:465-466 requires **all five
baselines to run against `buildObservation(slot)` alone, never raw sim state** — asserted by
`tests/test_baseline.nim`. The two requirements together force the value into the observation. It
leaks `(seed + slot) mod K` for that seat only, not the seed: `K` is 2 or 3, so it is one bit or
one trit about a seat's own draw, and it says nothing about the spawner layout or any other seat.

**F18 — a blocked cog still turns.** The note (design.md:199-202) says the cog "moves one cell if
that cell is floor and currently unoccupied…; its facing becomes `dir`" and does not make the facing
conditional on the move. Both readings are deterministic; the code's reading is the one that makes
`hold`/`hunt` work against a wall (a cog pinned in a corridor can still aim). Not falsifiable
against the note.

**F22 — a 429 is retried in the same beat.** The note is internally split (design.md:492-497 says
any transport error or non-2xx is retried once in the same beat; design.md:501 says a 429 is
retried in the next beat's batch) and the code satisfies **both**: the seat is retried once in this
beat, falls back to `counter` if that fails, and is reopened in the next beat's batch. Acceptance
item 8 asks for exactly "retries once … then falls back", which is what happens. No change.

**F55 — `static_replay.js` is not verbatim-plus-one-line.** Correct as built, and each addition is
load-bearing for a checklist item: the `FETCH_TIMEOUT_MS` watchdog is the bound item 5 wants on the
replay fetch (without it a dead CDN edge hangs forever, indistinguishable from a slow one); the
`coworld-replay` `tell()` bridge is what `tools/ci/viewer_smoke.mjs` reads as its second signal and
what the note's chorus fix (design.md:729-731) requires; `data-replay-error` is item 13's second
marker; and the play/pause/speed/`seek` transport API is what the game block drives and what the
`--soak` and scrub halves of the smoke exercise. Provenance is still single-starter — every line is
paintbot-lineage or new; nothing is spliced from babel or bullwhip, which is what design.md:710-714
and item 13's third bullet actually guard against. Reverting these would fail item 13.

**F56 — `broadcast_core.js` is a rewrite; the zoom stubs remain.** Two parts.
*The rewrite:* unavoidable and pinned by the note. The starter's `broadcast_core.js` decodes
paintbot's **binary sprite protocol**; matrix-games ships a JSON packet of recorded state
(design.md:526, design.md:562-564), so a byte-kept starter core would decode nothing. That is a
design decision already taken in the note, not a defect to fix in a review round.
*The stubs:* acceptance item 14's last bullet asks that the panel's **wiring** be removed. It is:
`grep -n 'zoomAt|setZoom|attachMinimap|minimap' client/replay_broadcast.html` finds only a comment,
the markup and CSS are gone (F49), and the ids are out of the test list
(`tests/test_viewer.nim:193-198`). What remains is three unreferenced methods on the core object,
which design.md:763-764 explicitly asks to keep ("stays in the file, verbatim, simply never
driven"). Deleting them would also break the worker's `view` message handler
(`static_replay_worker.js:225-233`), widening the F55 divergence. Left as the note requires; the
conflict the reviewer flagged is the judge's to adjudicate, and both documents' *outcome* — no zoom
bar, no minimap, nothing driving them — holds.

**F61 — the cert fixture names seats with the aliases.** Intended, and pinned by the note twice
(design.md:954, design.md:969). Offline the fixture must be deterministic and there are no real
policy names to use; on the platform the game config supplies them and `policyNames[]` diverges from
`names[]` immediately. The mechanism for two name spaces is present and correct either way
(`server.nim:464-466` seeds names from the config, `server.nim:404` records the player-sent policy
label, `global.nim:215-216` and the scorebug read `policyNames`), which is what acceptance item 4
requires.

**F70 — art provenance differs from the note.** The note describes retinting paintbot's shipped
`data/rig_real/*` rigs; the repo generates the eight liveries from `data/cog/cog_{idle,carry,hold,
fire}.png`, the four poses split out of a committed nano-banana render. The *pin* is "real art, not
placeholders, committed, deterministic, re-runnable, no downloaded art" and every asset the manifest
names exists — `tests/test_viewer.nim:258-277` asserts every path in `artManifest`, and
`Dockerfile.replay-viewer` repeats the `test -f` assertions. Re-deriving the art from a different
source to match a sentence would replace working committed art with new art in a review round; the
note's provenance sentence is what is out of date.

**F71 — the replay is written before `results.json`.** Deliberate, documented in code
(`server.nim:148-152`), and load-bearing: the hosted worker treats `results.json` as the end of the
episode and tears the pods down when it appears, so a replay written after it can be lost. Paintbot
and cogame-raid both order it this way. Both artifacts are written, both as `application/json`,
through the same env-driven methods; nothing downstream depends on the order. Documented deviation.

---

## NOTED (not fixed) — outside this round's findings

- `--load-replay` mode (`server.nim:441-447`, `runReplayServer` + `/replay-data`) now serves no HTML
  page at all after F59. It is one CLI flag's worth of dead-ish code; removing it would have been
  wider than the finding, so it stands.
- `global.nim:163-165` builds the terminal `over` beat row from the last `leadchange` seat with
  `cp: 0`, while `broadcast.nim:62-65` builds it from `sim.leader()` with the real `scoreCp`. Both
  are legal `over` rows and F40's cross-check does not cover them; the reviewer noted the difference
  under F40 without calling it a gap.

---

## CI

Run **32755082249** — `https://github.com/Metta-AI/cogame-matrix-games/actions/runs/32755082249` —
`ci.yml`, event `push`, head `af5c7043d4a4fbca3eb5f4c230901f6d9fb4dfe7` on `main`.
**Conclusion: `success`.** All three jobs green: `test`, `docker-smoke`, `wasm-viewer`
(`wasm-viewer` `needs: docker-smoke`, and its `Load the bundle in a real browser` step ran).

Evidence lines from that run:

- soak (F64, item 13):
  `soak: 10s of playback kept advancing ("5 / 300" -> "197 / 300" -> "245 / 300")`
  alongside `{"loaded":true,"ms":559,"clock":"BEAT 5 / 6 TICK 245 OF 300",…}` and
  `scrub readouts: 0%="BEAT 5 / 6 TICK 245 OF 300" 50%="BEAT 4 / 6 TICK 167 OF 300"
  100%="BEAT 6 / 6 TICK 299 OF 300"`.
- results schema (F66, items 6/10):
  `results.json validates against game.results_schema (17 keys)`, then
  `smoke OK: seats=8 results=709B replay=118908B reason=complete`.
- `SEAT-COUNT FAIL` and `RESULTS-SCHEMA FAIL`: **0 occurrences** in the whole run log.
