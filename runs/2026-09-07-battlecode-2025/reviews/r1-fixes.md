# r1 fixes — 2026-09-07-battlecode-2025 (bc25 "Chromatic Conflict")

Repo: Metta-AI/cogame-battlecode, branch `main`
Review: `runs/2026-09-07-battlecode-2025/reviews/r1-review.md` (F1..F43)
Base: `eb33a8d2` (the reviewed head)   Head: **`6885a062`** on `main`
CI: **https://github.com/Metta-AI/cogame-battlecode/actions/runs/34185528349 —
success** (all eight jobs: `test`, `docker-smoke`, `wasm-viewer`,
`parity-oracle`, `parity-oracle-bc20/bc21/bc24/bc25`), `grep -c 'SEAT-COUNT
FAIL'` over the docker-smoke log = **0**.

Six commits, one per finding, pushed to `main` in order. Every code change was
compiled and the whole of `tests/` (85 files) was run locally in debug against
Nim 2.2.4 with the repo's own `nimby.lock` package set before the push, and the
three touched test files again in `-d:release`; CI is the verdict on the
Docker, wasm-viewer and oracle jobs.

Note on how the commits were pushed: `git push` cannot authenticate from this
sandbox (the git protocol's Basic auth is rejected), so each commit was
replayed onto `main` through the authenticated GitHub Git Data API with the
same message, tree and parent chain. The pushed tree is byte-identical to the
locally tested one (`git diff origin/main HEAD` is empty). Nothing was
force-pushed and no history was rewritten.

## Dispositions

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F26 (blocking) | fixed | `0585d71` | `src/battlecode/broadcast.nim:129-283`, `tests/test_viewer.nim:831-892` | **14** (scrubber beats are labelled buttons "with CSS for every kind the page emits"), and 13/15's legibility half — the killfeed is the year's readout |
| F11 | fixed (2 of 4 items; 2 kept, with evidence) | `c2e1f3b` | `src/battlecode/years/bc25/world.nim:575,640`, `src/battlecode/match.nim:235-256`, `tests/test_bc25_replay.nim`, `tests/fixtures/replay-bc25.json` | 14 (the beat labels the note's table asks for are now writable) |
| F12 | fixed | `e0fc17b` | `tests/test_bc25_replay.nim` | 5 + 8 (the retry/fallback path's per-episode ceilings are now asserted, not assumed) |
| F39 | fixed | `c480eae` | `tests/test_bc25_replay.nim` | **7** (a test runs an all-scripted episode to the natural end and asserts `results.reason == "complete"`) |
| F43 | fixed | `ff1e4f6` | `src/battlecode/years/bc25/knobs.nim:34` | — (doc comment) |
| F34 | fixed in part, rest kept with the reason recorded in-tree | `6885a06` | `.github/workflows/ci.yml:1731-1745,1782-1793` | 1 (CI green with the substance assertion at the note's own floor, nothing loosened — the floor was *raised*) |
| F41 | kept as-is (judgement call, reasons below) | — | — | 7 (baseline tuning) |
| F36, F40 | kept as-is (checklist-interpretation / not a code defect) | — | — | 15 / 7 |
| F1 | kept as-is (the note requires `uri`; pre-existing across all five years) | — | — | 10 |
| F2–F10, F13–F25, F27–F33, F35, F37, F38, F42 | no change needed — the review records these as "no finding"; re-checked that nothing in them regressed (full local suite green, CI green) | — | — | 1–15 |

## F26 — nine of eleven bc25 beat kinds could never be emitted (blocking)

**What the code did.** `beatsFor` (`src/battlecode/broadcast.nim`) is the only
producer of `s.beats`, and its `case e.kind` had no arm for any bc25 event
kind. Its first line, `if e.game < 0 or e.round < 0: continue`, additionally
dropped the two pre-match doctrine kinds it *did* map, because pre-match events
carry `game = -1`. A bc25 match therefore produced two beats — `game_start` and
`game_end` — against eleven committed `html[data-year="bc25"] .beat-marker.*`
rules, and `renderFeed`, which builds `#killfeed` from the same array, drew two
lines. (CI's own evidence on the reviewed sha: `feed_lines: 1`.)

**What it does now.** Arms for all nine missing kinds, each with the label the
design note's table asks for:

| event kind | beat | label shape |
|---|---|---|
| `first_action` | `build` | "Clan Ash opens with build robot — game 1, round 1" |
| `tower_built` | `tower` | "Clan Ash builds a money tower (3 alive) — game 1, round 24" |
| `tower_upgraded` | `upgrade` | "Clan Ash upgrades a paint tower to level 2 — …" |
| `tower_lost` | `siege` | "TOWER LOST — Clan Basil's defense tower, game 2, round 1412" |
| `srp_completed` | `srp` | "Clan Ash completes a resource pattern at 2,15 — …" |
| `srp_active` | `srp` | "Clan Ash's resource pattern goes live: +3 a tower — …" |
| `srp_broken` | `srp` | "SRP BROKEN — Clan Ash's pattern at 5,5 after 37 rounds, …" |
| `coverage` | `coverage` | "Clan Ash passes 50 % — 79 tiles from the win" (the note's own wording) |
| `starved` | `starve` | "Clan Ash runs dry: 5 robots end the round at zero paint — …" |
| `rout` | `rout` | "ROUT — Clan Basil loses 6 robots, game 1, round 210" |

**The `e.game < 0` guard is fixed, not justified away.** Pre-match events now
fall through the guard when their kind is `doctrine_received` or
`doctrine_fallback`, and those beats land on frame 0 — the start of playback,
which is when the sheets were read. That is a repair of the *shared* chrome:
every year's stylesheet has shipped `.beat-marker.doctrine` since bc26 (lines
2639, 2887, 3023, 3193 of `client/replay_broadcast.html`) and none of them
could ever be reached. Both doctrine kinds also gained labels, since a button
with an empty `aria-label` announces nothing.

**bc24 is not touched.** `first_action` and `rout` are spelled the same by bc24
and bc25 but carry different fields (`jailed` vs `lost`), so those two arms are
selected by the replay header's year. bc24's beat vocabulary is exactly as it
shipped. bc24 appears to have the same gap for its own nine kinds — see
`NOTED (not fixed)`.

**The fixture was not regenerated for this, because it did not need to be.**
Run through the fixed `beatsFor`, the committed `tests/fixtures/replay-bc25.json`
yields **32 beats over 8 distinct kinds** (`game`, `build`, `coverage`, `tower`,
`upgrade`, `srp`, `starve`, `end`) where it previously yielded 2 over 2 — so
the wasm-viewer smoke already loads a genuinely multi-kind feed. The kinds a
peaceful 400-round scripted recording cannot contain (`siege` from `tower_lost`,
`srp` from `srp_broken`, `rout`) and the two no scripted episode can contain at
all (`doctrine`, which needs an LLM call) are supplied by the test as events in
exactly the shape `match.nim`/`decide.nim` write them.

**The test that was missing.** `tests/test_viewer.nim` previously asserted only
that the eleven CSS rules exist. It now runs a bc25 replay through `beatsFor`
and asserts, for every one of the eleven kinds, that it is **emitted**, that its
beat carries a non-empty label, and that the page carries a scoped CSS rule for
the `k` the beat actually claims — plus that both doctrine beats survive the
pre-match filter at `t == 0`, and that the committed fixture alone yields ≥ 20
beats over ≥ 6 kinds. Nothing was loosened or deleted; the block is additive
(`test_viewer` goes from 501 checks at `eb33a8d2` to 591; both counts measured).

**Evidence.** `nim r --path:src tests/test_viewer.nim` → `test_viewer: ok (591
checks)` in both debug and release; the beat dump of the committed fixture is 32
lines beginning `game @1 Game 1 begins on Filter` and ending `end @400 Game 1 —
Clan Ash wins (more squares painted)`. And the runtime proof, from the
`wasm-viewer` job of run 34185528349 loading the bc25 replay in headless
chromium:

```
{"loaded":true,"ms":304,"clock":"0:10 GAME 1 OF 1 — DEFAULTSMALL doctrines",
 "scorebug":"CLAN ASH Clan Ash · Paint it and hold it. 84 … CLAN BASIL … 15",
 "feed_lines":8}
```

`feed_lines` was **1** on the reviewed sha (F33) and is **8** now — the
killfeed's own cap — with `--killfeed-overlap` still green at 360 / 720 /
1280 px and both zooms, and the endcard still raised at the 100 % seek.

## F11 — event fields against the note's table

Two of the four items were real omissions and are fixed; two are deliberate and
are kept, with the evidence:

- **`tower_lost.remaining` — added.** `destroyRobot` decrements
  `stats.towers[t]` immediately before it emits the beat, so the count of towers
  the clan has left is available at the emission site; it rides the beat's
  string slot exactly as `tower_built.total` already does.
- **`srp_active.active_total` — added.** `updateResourcePatterns` already counts
  the live patterns to compute `income_bonus`; the count itself is now carried
  too. `tests/test_bc25_replay.nim` asserts `income_bonus == active_total * 3`.
- **`first_action.action` — kept, and the review agrees it is deliberate.**
  `MatchEvent.toJson` flattens `fields` into the same object as the event's own
  `kind` key, so a field named `kind` overwrites the event kind and the replay
  comes back carrying events of kind `"move"`. This is documented at
  `match.nim:169-175` and asserted by `tests/test_bc25_replay.nim`. Renaming it
  to satisfy the note would reintroduce the bc24 scar.
- **`coverage.tiles_from_win` — kept.** It is an addition to the note's field
  list, not an omission, and the note's own feed line ("79 tiles from the win")
  cannot be written without it. `beatsFor`'s coverage label now reads it, so it
  is load-bearing rather than spare.

`tests/fixtures/replay-bc25.json` was re-recorded with
`tools/gen_bc25_fixture_replay.nim`; the only diff is `active_total` on the
three `srp_active` events. The hash chain is byte-identical — no rule moved, so
no GameVersion bump.

## F12 — pre-match event bounds

The bound table in `tests/test_bc25_replay.nim` skipped every event with
`game < 0`, so no pre-match kind was bound-checked. A block now drives the whole
doctrine phase into its failure paths — two LLM seats against a dead endpoint
(`http://127.0.0.1:1`), both attempts spent, both seats falling back — and
asserts every emitted pre-match kind is inside a documented bound. The observed
counts are `doctrine_requested` 2, `doctrine_received` 0, `doctrine_retry` 4,
`doctrine_fallback` 2.

Two of the note's numbers are per-seat where the code's are per-episode, and the
test's comment records both: `doctrine_requested` is emitted once per LLM seat
at seeding (ceiling 2, the note says 4), and `doctrine_retry` once per failed
seat per attempt (ceiling 4, the note says 2). Both are bounded by the same
`attempt < 2` loop, so neither can grow — which is the property the bound is
for. `episode_start`/`episode_end` come from `server.runEpisode`, outside the
test process; docker-smoke exercises them and the comment says so.

## F39 — `results.reason == "complete"` in the Nim suite

`tools/ci/docker_smoke.sh:443` asserted it against the built image; no in-tree
test did, so the episode-level reason was only defended by a job that needs
Docker. `tests/test_bc25_replay.nim` now plays the variant's own shape — three
games, mixed pool, alternating sides, both seats scripted — through `playMatch`
and `resultsJson`, and asserts `reason == "complete"`, `fallbacks == [0, 0]`,
that the majority ended the match, and that no game ended `abandoned`.

## F43 — the chassis count in `knobs.nim`

`knobs.nim:34` listed eleven chassis files and then said "All thirteen exist".
Eleven are listed and eleven exist. One word.

## F34 — the docker-smoke floors

Split, because the two halves of the finding have different answers:

- **Fixed:** the across-the-pair squares-painted floor was `120` against the
  note's `200`, with no measurement supporting the lower number — the run that
  measured every other floor measured **241**. Raised to the note's 200.
  Verified before pushing by reproducing the exact smoke episode natively (seed
  3, `DefaultSmall`, 600 rounds, spaark vs examplefuncsplayer25): `217 + 24 =
  241`, and the per-seat numbers reproduce the step's comment exactly (49/254/
  52950/10540 and 67/37/20000/7135), so the reproduction is faithful. CI then
  confirmed it against the container: `across the two seats: towers built=6
  towers upgraded=9 squares painted=241` — the new floor clears with 41 to
  spare.
- **Kept, with the reason now tied to the finding in-tree:** the per-seat
  `tiles_painted: 15` against the note's `150`. The note's 150 was derived from
  whole 2000-round games; this smoke is 600 rounds, and the weak seat paints 37
  in that window. 150 is a floor no correct episode can clear, so raising it
  would make CI red about a healthy game. The workflow comment already carried
  the arithmetic; it now names r1-F34 so the next reader finds the argument
  rather than re-deriving it.

## F41 — knob thresholds below the note's table (kept as-is)

`srp_priority` (note ≥ 25 % down, measured −20.4 %, committed 10 %) and
`ruin_claim_radius` (note ≥ 50 % up, measured +19 %, committed 10 %) are the two
numeric gaps. I did not churn them, for two reasons the review itself supplies:

1. The design note's §Tests item 16 requires that "the header records every
   substituted statistic", and `tests/test_bc25_knobs.nim:8-62` does that in
   full, per knob, with the measured value and the substitute — the obligation
   the note actually places on this test is met.
2. The committed thresholds sit at roughly half the measured effect. That
   headroom is the point of a teeth gate: the note itself anticipates phase 20
   re-tuning the chassis, and a threshold pinned at 19 % against a measured 19 %
   turns every legitimate tuning step into a red build. Raising them to just
   under the measurement would make the gate brittle without making it detect
   anything a 10 % threshold misses (the failure mode a teeth test guards
   against is a knob with **no** effect, which both thresholds catch).

## F36, F40, F1 — kept as-is

- **F36** (`canvas_text: 0` on the renderer fixture): the fixture is a DOM page;
  this repo has no `client/renderer.js` (the board renderer is
  `src/battlecode/render.nim`, compiled to wasm), which is what the design note
  describes and what shipped. Its gate is its own DOM-rect `problem()` check
  setting `data-replay-error`, which does fail the harness. Changing the
  fixture to satisfy the checklist's literal wording would mean inventing a
  canvas the product does not have. Checklist-interpretation question, left for
  the judge.
- **F40** (no committed grid harness): real, but committing a tuning harness is
  new work rather than a fix to the diff, and the measurements are recorded and
  dated in `tests/test_bc25_survival.nim:23-32` and `tests/test_bc25_knobs.nim:8-62`.
  Recorded as `NEEDS-DESIGN` if the judge wants it: the change would be a
  `tools/tune_bc25.nim` sweeping the committed knob grid and printing the table
  those two headers quote.
- **F1** (`game.docs` uses `{"type":"uri"}`): the design note explicitly
  requires `uri`, the shape is `{type,value}` either way, and the value is
  pre-existing and unchanged by the bc25 diff. No change.

## NOTED (not fixed)

- **bc24 has the same beat gap F26 found in bc25.** `beatsFor` still has no arm
  for `flag_taken`, `flag_dropped`, `flag_returned`, `flag_captured`,
  `trap_wave`, `upgrade`, `mastery` or `setup_end`, and bc24 ships scoped CSS
  for `steal`, `return`, `capture`, `trap`, `upgrade`, `level` and `setup`.
  bc21's `center_taken`, `vote_lead`, `bid_spike`, `expose_wave`, `empower_big`
  and `annihilated` are in the same position. Out of scope for this round (the
  brief: touch earlier years only where a finding names them), and fixing them
  would change shipped years' scrubbers and killfeeds — which the
  `--killfeed-overlap` gate measures. Worth its own round.
- **`game_start` does not emit the note's `ruins` or `tiles_to_win`, and
  `game_end` does not emit its `coverage`.** Not a finding in this review, so
  not changed; the same one-line shape as the F11 fixes if a later round wants
  them.

## Final CI

`main` @ **`6885a0625687c7caec19b879e0ea09613ebd74f0`** —
run **34185528349**, conclusion **success**
(https://github.com/Metta-AI/cogame-battlecode/actions/runs/34185528349),
jobs: `test` success, `docker-smoke` success, `wasm-viewer` success,
`parity-oracle` success, `parity-oracle-bc20` success, `parity-oracle-bc21`
success, `parity-oracle-bc24` success, `parity-oracle-bc25` success.
First attempt; no red run in this round.
