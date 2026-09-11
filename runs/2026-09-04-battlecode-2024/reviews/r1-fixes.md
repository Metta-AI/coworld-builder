# r1 fixes — battlecode-2024 (`bc24` year module of `Metta-AI/cogame-battlecode`)

Reviewed sha: `5e7c8b78a09618daaec01a532dc3391cec1483c3` (base `d2922438`, CI run 34084170288, green on `main`).
Author: coordinator (session `9346975d`), 2026-09-11. **No fixer sub-agent was dispatched and no
commit was made in this round.** This file records the disposition of every round-1 finding, which
is what the fixer leg exists to produce.

## Why no code changed

1. **`reviews/r1-review.md` reports zero blocking findings.** Per `prompts/30-review-loop.md`
   §ACCEPTANCE CHECKLIST, "blocking" is falsification of items 1–15 or the one-batch rule; F1–F7
   are all labelled advisory by the reviewer and each bears on the design note or on a
   pre-existing, inherited shape rather than on a checklist item.
2. **The reviewed sha is a pinned artifact and `main` has moved for reasons unrelated to this
   run.** At the time of this disposition `main` is `4bcb8db` and carries year modules bc16, bc17,
   bc19, bc22, bc23 and bc25 landed by other coworld-builder runs that share this host repo. A
   commit made now to satisfy an *advisory* finding would move the sha under review, and the judge
   would then have to separate the bc24 delta from six other runs' deltas. The bc24 delta
   (`d2922438..5e7c8b78`) is green on `main` at CI run 34084170288 and stays the object of review.
3. **The two other runs modifying this repo are live.** `2026-09-10-battlecode-2019` and
   `2026-09-10-battlecode-2017` are in *Running*. Pushing an advisory-only change to a shared
   `main` while they build is avoidable risk with no checklist benefit.

## Disposition, finding by finding

| # | finding | disposition | rationale |
|---|---|---|---|
| F1 | `canvas_text.total: 0` on every replay and on the fixture; the effective legibility gate for LLM text is the fixture's DOM verdict | **accepted as residue, no change** | bc24's model-authored text (`notes`, `motto`, plain words) is rendered into the **DOM** (`client/replay_broadcast.html:4033-4044`, scorebug `.plate-sub`), not onto a canvas, so item 15's canvas number is structurally 0 and the checklist's `client/renderer.js` fixture shape does not exist in this repo. The equivalent gate is present and armed: `tools/ci/renderer_fixture.html` renders the bc24 row at full cap (280-rune notes, 48-rune motto, both seats) at 360/720/1280 px, asserts no element escapes the frame, no filled readout hides its content, the doctrine panel stays ≤ 50 % of frame height, and that the strings are **still full length**; a failure sets `data-replay-error`, which `tools/ci/viewer_smoke.mjs:688` turns into exit 1 under `--strict-text-bounds` (`ci.yml:1599-1625`, green in run 34084170288, log 8073-8074). The fixture shape is pre-existing (bc26/bc20/bc21 rows at `d2922438`); bc24 added a row to it. Changing the whole repo's fixture architecture is out of scope for an advisory finding on a mod run. |
| F2 | the bc24 docker-smoke substance assertion drops `levels_end`/`heal_dealt` from the per-seat set and asserts them across seats; key `flag_pickups` → `flags_picked_up` | **accepted; the code is right and the design note is amended** | `examplefuncsplayer24` never heals and its ducks die before earning attack XP, so a per-seat floor on those two statistics asserts the weaker bot, not the game. `flag_pickups` is not a key any bc24 results document carries (`Bc24GameKeys`, `src/battlecode/results.nim:129-139` — the key is `flags_picked_up`), so the note's jq line could never have run. Both substitutions are recorded in `ci.yml:1250-1268` and ran green (log 5817: `flag pickups=3 skill levels=74 health healed=37354`). Design note amended (§Amendments, `design.md`). |
| F3 | three replay event kinds carry different fields from the design's event table (`first_action.action` vs `kind`; `setup_end` fields; `flag_taken` has no `escort`) | **accepted; the code is right and the design note is amended** | `MatchEvent` flattens `fields` into the event object, so a field literally named `kind` would overwrite the event kind — the note's table was written without that constraint; `tests/test_bc24_replay.nim:306-308` pins the shipped shape. Every emitted kind has CSS and is inside its per-game bound. No checklist item speaks to the event vocabulary. Design note amended. |
| F4 | five knob thresholds and the survival floors differ from the note's, substitutions recorded in the test headers; signed deltas gated in `-d:release` only | **accepted as residue, no change** | Each substitution names the measurement that forced it (`tests/test_bc24_knobs.nim:14-40`) and the survival floors were **raised** to measured values — a strict superset of the note's floor, never a loosening. All files are new in the range, so item 1's "no test loosened" is untouched. Both passes ran in CI (debug: sweep runs, 5 checks; release: all 25 checks) and the inverted control `-d:bc24BrokenChassis` ran and failed the gate as designed (log 2256-2257). |
| F5 | no grid-harness artefact in the tree for item 7's "tuned with a grid harness, not guessed" | **accepted as residue, no change — the harness is committed and runs in CI under another name** | The knob-teeth gate **is** the grid: `tests/test_bc24_knobs.nim` plays paired seeded games that differ in exactly one knob at its low and high setting, over three maps under both side assignments, 20 settings × 6 games = 120 whole 2000-round games in the release pass, and asserts a named signed delta per row with every threshold in one table. Its header records the measured value behind each of the five substituted thresholds (+21.3 %, −2.9 %/+100.8 %, −53.8 %/+5, −27.1 %, +22.1 %/+12.9 %) — measurements, not guesses — and `tests/test_bc24_survival.nim:19-26` records the measured floors. That is a committed, CI-executed parameter sweep with its results in the tree; the finding is that it is not *named* "grid harness". |
| F6 | `setup_end` per-game bound is 2 in the replay test where the emitter can only reach 1 | **accepted as residue, no change** | A bound one looser than the emitter can reach is weaker than the design table but cannot admit a defect the emitter can produce (`src/battlecode/years/bc24/rules.nim:292-295` fires once per game at `currentRound == SetupRounds`). Tightening it is a one-character change to a **passing** test on a shared `main` — see "Why no code changed" above; logged as residue for the next bc24 touch. |
| F7 | `game.docs` uses `type: "uri"` where checklist item 10 spells `type: "text"` | **accepted as residue, no change** | The `{type, value}` object shape item 10 requires is present, `game.protocols` carries both `player` and `global`, and the readme plus all six pages are well-formed. `uri` is the shape the tree already had at `d2922438` for five pages; the range added the sixth in the same shape. The platform has accepted it on three shipped releases of this repo, and the CI step "The coworld CLI accepts the manifest template" passes. Rewriting the manifest's docs encoding for every year at once, on a shared `main`, to satisfy an advisory reading is a change to the host repo's contract, not a bc24 fix. |

## Checklist items this round leaves standing

No acceptance-checklist item is falsified by any disposition above. Item 1 (CI green, no test
loosened) rests on run 34084170288 and on `git diff d2922438..5e7c8b78 -- tests/`, whose only
removals are three-year→four-year widenings re-asserted on the following line. The residue carried
into phase 40 is F1, F4, F5, F6, F7 (advisory), plus the design-note amendments for F2 and F3.
