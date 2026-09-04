blocking: 0

# r1 verdict — battlecode-2020-soup (the `bc20` year module)

Head: `e07412ab960d5bb7b05d7b8f9015c6c16f339769` (main, merge of PR #2)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + parallel-batch rule)
Independent read written before reading fixes: **yes** (`r1-fixes.md` opened only after my own
pass over the diff `abc92ce3..e07412ab`, the head tree, the CI run and its artifacts; the review
was read after my independent notes were written, per the reading order).

Reviewed change: the bc20 year module + the r1 fix commits. Repo cloned fresh at the head sha;
CI evidence from run **33847918283** (main @ e07412ab, conclusion `success`, jobs `test`,
`parity-oracle`, `parity-oracle-bc20`, `docker-smoke`, `wasm-viewer` — verified with `gh`, not
accepted from anyone's report). The reviewed sha of the review file was `551c542`; everything
below is verified at the **current head**.

## Standing blocking findings

None.

## Refuted / resolved — the reviewer's findings, one by one

The r1 review reported **zero blocking** findings and fifteen observations (F1–F15). I attempted
to reproduce each at `e07412ab`. None stands as blocking. Eleven were changed by the fix commits
(resolved — fix landed and verified sound below), four were documentation-only dispositions I
checked against the tree and, where the claim was about the upstream engine, against the pinned
upstream source itself.

### F1 — fixture measured the hidden bc26 panel → RESOLVED (fix verified)
- Evidence: `tools/ci/renderer_fixture.html:271` computes
  `var probe = year === 'bc20' ? 'bc20-doctrines' : 'doctrines';` and `:339` now reads
  `document.getElementById(probe).getBoundingClientRect()` — the year's own panel, not the
  `display:none` bc26 one (commit `3bee5ee`). The fixture ran green at head
  (run 33847918283, step "Render the full-cap doctrine-text fixture", `loaded: true`).
- The `canvas_text: total 0` half of F1 is **not a defect** at head: I verified the viewer draws
  **no text on any canvas** — `grep fillText|strokeText` over `static_replay.js`,
  `chrome_common.js`, `broadcast_core.js` returns nothing, and `render.nim` emits sprite pixels
  only. Every LLM-authored string is DOM text, and the DOM fixture is the operative gate: it
  asserts its own strings are still at full rune caps (`renderer_fixture.html:348–358`), measures
  frame escape, hidden overflow and panel height at 360/720/1280 px for **both** years, and fails
  through `data-replay-error`, which `viewer_smoke.mjs` turns into exit 1 (`viewer_smoke.mjs:598`).

### F2 — `drone_water_drop` victim alias → RESOLVED
- Evidence: `world.nim` emits carry `$ord(dropped.team)`; `match.nim` maps `"0"`/`"1"` to the clan
  alias and anything else to `neutral` (commit `d12f35a`); `tests/test_bc20_drone.nim` gained
  friendly-drop and cow-drop cases (28 → 33 checks, additions only).

### F3 — no `rules_digest`/`sheet_schema` key in the observation → RESOLVED (documented)
- Evidence: both contents ship in `Bc20Preamble` (`decide.nim:122–180`), recorded once as
  `prompt_preamble`; `docs/PROTOCOL.md` §The bc20 observation now says so and names the field
  (commit `d046fc1`). Content-equivalent layout difference; no checklist item names the key layout.

### F4 — `flood_table["7"] = 1501` vs the note's 1546 → RESOLVED (documented)
- Evidence: `dispatch.nim:261–264` doc comment + `docs/PROTOCOL.md` carry both numbers and why the
  payload reports the sentinel (commit `0fd26fb`). Levels 1–6 are the real curve, pinned by
  `tests/test_bc20_flood.nim`. Either number means "elevation 7 is dry all match"; recording 1546
  would require committing water levels for rounds the sim cannot play, against a byte-diffed
  JDK-generated table. Sound.

### F5 — "runs the awu chassis" logged on bc20 → RESOLVED
- Evidence: `decide.nim:316` now prints `chassisNameFor(config.year, …)` (commit `9f7e6b1`), the
  same resolution the replay records.

### F6 — Refinery-second build order undocumented → RESOLVED (documented)
- Evidence: `docs/RULES-BC20.md` §Divergences item 16 (commit `98670d6`) with the forcing rules
  (walled HQ + `MAX_DIRT_DIFFERENCE 3` needs a second drop-off; dirt on a building buries it, so
  no gun on the ring); `miner.nim` header lists the Refinery.

### F7 — phantom `NEED_DRONES` branch → RESOLVED (documented)
- Evidence: `fulfillment.nim:4–7` header corrected; `SigNeedDrones` marked RESERVED with the
  renumbering rationale (`signals.nim:22`, commit `3224c51`); §Divergences item 15.

### F8 — end-reason coverage passed on string literals → RESOLVED (fix verified, strengthened)
- Evidence: commit `925ef4f` splits `reDerived` vs `ladderVector`; `broadcasts`/`highest_id`/
  `coin_flip` are real vectors through `checkEndOfMatch` on a bare world; `abandoned` is a
  deterministic end-to-end round trip (clock held in `playGame`'s own round callback, re-derived
  from written bytes, hash chain at the stop round compared). 45 → 67 checks; I read the full hunk
  — no assertion removed, no tolerance widened.

### F9 — two knob gates on proxy statistics → RESOLVED (fix verified, strengthened)
- Evidence: commit `3920551` adds the note's own statistics (enemy-half arrival delta gated at
  100 rounds/game vs measured 233; adjacency-by-round-350 verbatim) while keeping both original
  counters. 14 → 16 checks.

### F10 — move-into-water destroys rather than refuses → RESOLVED, and I settled the engine question
- The reviewer could not verify the Java behaviour. I fetched the pinned upstream
  (`battlecode20@7618f6b`, `world/RobotControllerImpl.java`): `assertCanMove` (:344–365) tests
  type/adjacency/bounds/occupancy/dirt-difference/readiness and **never flooding**; `move`
  (:382–403) then does `if (gameWorld.isFlooded(center) && !getType().canFly()) disintegrate();`
  — `disintegrate()` throws `RobotDeathException` (:937–939) before `moveRobot` runs, so the mover
  dies where it stands and never occupies the tile. The port (`world.nim` `move`) matches; the
  divergence entry (§Divergences item 17, commit `83f5cd5`) and its citation are **accurate**, and
  `tests/test_bc20_flood.nim` pins the path (26 → 32 checks).

### F11 — stale pointers, unwired version check → RESOLVED
- Evidence: commit `e18ad4f` fixes the pointers in the constants **generator** (regenerated file
  still byte-matches `--check`), corrects `test_bc20_maps.nim`'s comment, and wires
  `tools/ci/check_gameversion.sh` into the `test` job for every non-main ref
  (`ci.yml:208–213`). GV04→GV05 header fixed in `3920551`.

### F12 — dead `SeatPolicy.baseline` → RESOLVED
- Evidence: field deleted (commit `e9a044b`); `grep baseline src/battlecode/decide.nim
  src/battlecode/server.nim` finds only `baselineForSeat`/`baselineFor` and comments.

### F13 (+ follow-up) — no committed bc20 fixture; the node wasm smoke was a silent no-op → RESOLVED
- Evidence: `tests/fixtures/replay-bc20.json` committed (5 881 B, GV05, real `ReplayDoc.toJson`
  recording; generator `tools/gen_bc20_fixture_replay.nim` refuses a non-re-deriving recording);
  `tests/test_bc20_replay.nim:318–360` re-derives the committed bytes natively (commit `c7e2e5f`).
  The follow-up (`4121a21`) is a genuine catch the review missed: `require()` hoisting shadowed
  `global.Module`, so `wasm_replay_smoke.cjs` had exited 0 having executed nothing on every prior
  run. At head it loads via `vm.runInThisContext` with a 60 s watchdog, and the run-33847918283
  log shows three real `{"loaded":true,"game_version":"GV05",…,"mismatch_round":-1}` lines
  (both smoke replays + the committed fixture).

### F14 — `first_build` vocabulary → RESOLVED (documented)
- Evidence: `docs/REPLAY.md:154–169` lists the eight reachable `RobotType`-named values and why
  `delivery_drone` (commit `3a897cf`). All ten beat kinds have CSS
  (`replay_broadcast.html:2629–2634, 2742–2748`), so no marker is invisible.

### F15 — "byte-identical" build-report claim → confirmed, prose-only
- The decoded manifest is identical for every bc26 structure; only `\u2014` escapes were
  normalised to raw UTF-8. No repo change needed; the build report carries the correction. Not a
  checklist matter.

### The reviewer's "could not determine" items — settled
- **Grid-harness tuning (item 7)**: verifiable from the tree — see checklist pass below.
- **F10 engine behaviour**: settled by me against upstream (above); the port matches.
- **exec-order snapshot vs live iteration**: settled by me against upstream
  `world/ObjectInfo.java:95–107` at `7618f6b`: `eachDynamicBodyByExecOrder` copies
  `dynamicBodyExecOrder.toArray()` before iterating and skips bodies that no longer exist —
  a **snapshot with dead-skip**, exactly what `rules.nim:106–109` does (`let order = w.execOrder`
  then `if id notin w.robotsById: continue`). The port is right; a robot spawned mid-round takes
  no turn until the next round in the engine too.
- **`abandoned` re-derivation never exercised on CI**: resolved by the F8 fix — the guard is now
  made to fire deterministically via the real `budgetSeconds` path, unconditionally.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 33847918283, main @ e07412ab, `success`; all 5 jobs success. `git log -p --since=2026-09-04T02:57 -- tests/` read hunk-by-hunk: this run's test changes are additions, mechanical renames (`GameOutcome`→`GameOutcome26`, enum→string), and the year-aware manifest/viewer extensions; r1-F8 (+22 checks) and r1-F9 (+2 checks) strengthen; no deleted assertion, widened tolerance, or skip anywhere. Sibling D1–D3 commits are context, also read, also clean. |
| 2 Replay re-derivation | PASS | `replay.nim:284–310` steps the same session and compares every round's chain; `tests/test_bc20_replay.nim` re-derives from written bytes for `quantity`, `hq_destroyed`, `abandoned` end-to-end plus the committed fixture, `mismatchRound == -1`; viewer uses the same `Deriver` (`bc_replay.nim:66–75`). |
| 3 Static viewer | PASS | `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, asserted in `ci.yml`; only network call in the bundle is the replay fetch (`static_replay_worker.js:127`); `/client/replay` appears only in the test that asserts its absence (`test_seats.nim:75–78`). |
| 4 Both name spaces | PASS | Observation carries `alias`/`opponent_alias` only (`decide.nim:203–204`, no names key); viewer maps alias→plate-name and real name→plate-sub (`replay_broadcast.html:3337–3343`); names live in `replay.names[]`/`results.names`. |
| 5 Degrade-never-hang | PASS | `waitForSeats` bounded by `connectTimeoutMs` (`server.nim:238–252`); doctrine = one `curly.makeRequests` batch per attempt, ≤ 2 attempts, monotonic `doctrineBudgetMs` wrap (`decide.nim:240–298`); `perGameBudgetSeconds 100`/`matchBudgetSeconds 320` monotonic guards (`match.nim:171–182`); worst case 25+45+320+~30 ≈ 420 s < 720 s (60 % of `episode_timeout_minutes: 20`). `tests/test_bc20_perf.nim` gates a full 1499-round CentralSoup game at ≤ 55 s. |
| 6 num_agents | PASS | `num_agents: 2` in both variants' `game_config` and `certification.game_config`, never at variant top level (asserted `test_manifest.nim:100–132`); `docker_smoke.sh:137–176` enforces the four invariants + `SMOKE_SEATS` cross-check, `SEAT-COUNT FAIL:` prefix; grep of the head run's docker-smoke log: **0** occurrences; both episodes `smoke OK: seats=2 … reason=complete`. |
| 7 Scripted baseline full episodes legally | PASS | `test_bc20_baselines.nim`: sheets pass the LLM-path `validate`; world invariants + legality + `DecisionOps` bounds asserted through played rounds (:52–98); D2 gate — 6 games, BoC wins all 6 with living HQ and positive play counters, scaffold acts; BoC mirror to round 1499 both HQs alive; `reason == complete` asserted in `test_bc20_replay.nim:120` and in the docker-smoke bc20 episode. "Tuned, not guessed": the tree carries the grid harness itself — `tests/test_bc20_knobs.nim` plays paired low/high games per knob × 2 maps × both side assignments in CI, its header records the measured deltas ("Measured at GameVersion GV05"), and every gate is set at half the measured delta; the baseline's default parameters are the ported Bowl of Chowder build (documented provenance, NOTICE + RULES-BC20). |
| 8 LLM reply handling | PASS | `sheet_common.extractJsonObject` (balanced-object extraction with prose tolerance); exactly one retry (`decide.nim:279–280`, `attempt < 2`); fallback sheet installed, `results.fallbacks` recorded, `doctrine_fallback` event emitted (`decide.nim:343–355`, `results.nim:72`). |
| 9 Rune-safe truncation | PASS | `truncateRunes`/`truncateBytes` (`sim_types.nim:156–180`) applied to notes/motto/unknown-fields/provider errors/reply bytes; `test_bc20_sheet.nim:107–129` feeds U+1F9C0 at the caps, asserts rune-exact lengths and byte-cap cut on a 4-byte boundary; `test_sheet.nim:194–215` asserts `validateUtf8() < 0` on the truncated output. |
| 10 Manifest validates | PASS | `game.protocols` carries `player` **and** `global`; `game.docs.readme` is a `{type,value}` object and `pages` is four `{id,title,content:{type,value}}` entries; `test_manifest.nim:192–219` asserts the shapes and CI's "The coworld CLI accepts the manifest template" step runs the publishing CLI's own `_load_template_manifest`→`validate_upload_manifest` (green at head). |
| 11 Legible at 360 px | PASS | `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` (`replay_broadcast.html:2561`); labels hidden under `@media (max-width: 640px)` (:2637); fixture renders both years at 360 px and fails on any overflow. |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: build → certify → upload-policies (explicitly before upload-coworld, :225–227) → upload-coworld → secret put (:419–420), all in one run; three workflows present; `docker_smoke.sh` 100755; `policies.json` has 8 policies — 4 PLAYER_PROMPT champions + 4 scripted fillers across the two years; the **second** `PLAYER_PROMPT` entry (`battlecode-opportunist`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (the bc20 champion #2 `battlecode-bc20-rusher` carries it too); the three-name placeholder grep exits 1 (gate passes) — run in the sandbox at head. |
| 13 Viewer executes | PASS | `wasm-viewer` `needs: docker-smoke`; "Load the bundle in a real browser (BOTH years' replays)" ran at head with no `continue-on-error` — `loaded:true` for `replay.json` and `replay-bc20.json`, `scrub selector: #scrub`, endcard shown with a clan line after the 100 % seek (run 33847918283 log). Markers: `data-replay-loaded` set from the worker's first-frame `loaded` message (`static_replay.js:180`), `data-replay-error` on failure (:20). No recorded lobby exists in this format — `newDeriver` builds frames only from per-game rounds (`replay.nim:267–276`), so playback opens at the game start structurally. Link flags/bootstrap from one starter: `config.nims` has **no** MODULARIZE/EXPORT_NAME; the worker uses global `Module.onRuntimeInitialized` (`static_replay_worker.js:218`) — the matching non-MODULARIZE pair; neither loader touched by this run. The node wasm smoke is now real (F13 follow-up) and passes on three targets including the committed fixture. |
| 14 Chrome is the starter's | PASS | `client/chrome_common.js` and `client/broadcast_core.js` **sha256-identical** to `/workspace/starters/coworld-ctf/client/` copies (f7860b4c…/226aea03…, verified byte-for-byte); this run's `replay_broadcast.html` diff is +463/−6, the −6 being the declared year-switch hook, with the bc20 block appended under the banner at :2644 and every new id `#bc20-*`; `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` (:3541–3552); bc20 panels ride `calc(var(--band,0px) + …)`; `#endcard { bottom: var(--band, 0px) }` (:1848), shown via `.on` (:1859/:3534), and `seek()` calls `dismissEndcard()` first (:3313–3316) so every seek path takes it down; beats are labelled `<button>`s built by `buildBc20BeatButtons` (:2986) with CSS for all ten emitted kinds; `#viewpanel` kept per the note (48×48 board at 16 px/tile = 768 px > 360 px frame). |
| 15 Every drawn string fits | PASS | The viewer draws zero canvas text (verified — sprites only); all model-authored text is DOM. The worst-case fixture (`tools/ci/renderer_fixture.html`) exists, lays out full-cap notes (280 runes) and motto (48 runes, astral-plane) on both seats, both years, at 360/720/1280 px in the page's own extracted CSS, asserts its own strings are still full-length (:348–358), and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own ci.yml step, green at head with `loaded: true`. The `canvas_text` line reads `total 0 / never_inside 0` — truthful for a page with no canvas text; the operative gate is the fixture's own `data-replay-error` path, which viewer_smoke turns into exit 1. |
| Parallel batch | PASS | One decision turn per episode; both seats' calls in a single `client.curl.makeRequests(batch, …)` (`decide.nim:295–298`); no per-seat sequential call site exists. |

**bc26 unbroken by this run** (the brief's extra question): bc26 code changes are a type rename
(`GameOutcome` → `GameOutcome26`) and an improved error message in `registry.nim`; GameVersion is
GV05 with `ReplayCompatibleGameVersions ["GV04","GV05"]`, so shipped bc26 replays keep loading;
the bc26 docker-smoke episode, the bc26 browser load, and the bc26 wasm node smoke are all green
at head; the manifest's bc26 variant/certification decode identically to `abc92ce`.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed, `3bee5ee`, year-aware probe | probe at fixture:271/339, fixture green at head | yes |
| F2 | fixed, `d12f35a`, victim team on event | emit carries `$ord(dropped.team)`, match.nim maps neutral; +5 checks | yes |
| F3 | documented, `d046fc1` | PROTOCOL.md names both keys and `prompt_preamble` | yes |
| F4 | documented, `0fd26fb` | doc comment + PROTOCOL.md carry 1501 and 1546 with reason | yes |
| F5 | fixed, `9f7e6b1` | log prints `chassisNameFor(config.year, …)` | yes |
| F6 | documented, `98670d6` | §Divergences item 16 present with forcing rules | yes |
| F7 | documented, `3224c51` | header corrected, SigNeedDrones RESERVED, §Div 15 | yes |
| F8 | fixed, `925ef4f`, 45→67 checks | full hunk read: two lists, real vectors, deterministic abandoned round trip; nothing removed | yes |
| F9 | fixed, `3920551`, 14→16 checks | note's own statistics added, both counters kept | yes |
| F10 | documented + test, `83f5cd5` | citation checked against upstream `7618f6b` myself: accurate; test pins the path | yes |
| F11 | fixed, `e18ad4f` | pointers fixed in generator, check_gameversion wired at `ci.yml:208–213` (non-main refs) | yes |
| F12 | fixed, `e9a044b` | field gone, no reads remain | yes |
| F13 | fixed, `c7e2e5f` | fixture committed, native re-derivation test, third wasm target in ci.yml | yes |
| F13-fu | fixed, `4121a21` | `vm.runInThisContext` + watchdog; head log shows 3 real loaded lines where the old step printed none | yes |
| F14 | documented, `3a897cf` | REPLAY.md lists the eight values; all beat kinds have CSS | yes |
| F15 | prose correction, no repo change | decoded-identical confirmed; escape normalisation only | yes |

## Non-blocking observations (mine, advisory)

- The bc20 parity oracle is narrower than the design note promised (arithmetic/ID/comparator
  vectors + the byte-diffed water table, not a full round-loop trace): the note's engine-from-source
  tier is blocked by the dead `net.sf.jsi:1.1.0-SNAPSHOT` artifact, which the job reports to the
  step summary as a non-blocking attempt. The substitution is documented in `Bc20Oracle.java`'s
  header, `docs/PARITY.md` and the build report. No checklist item requires the oracle; the
  divergence is declared, and the correctness surface it cannot cover is partially compensated by
  the upstream-cited rule pins (F10, exec-order) and the invariants/baselines/knobs suites.
- The D2 survival-gate thresholds (≥6 miners, ≥3 landscapers, ≥90 dirt) are the *measured* values
  with margin, lower than the design note's aspirational ones (≥10/≥8/≥200); the build report
  declares this. They were set this way in the original bc20 commits, not lowered during review.
- `wasm_replay_smoke.cjs` reports `frames: 200` on a 119-round replay (`bc_frame()` returns 1 past
  the end); harmless for the ≥50 floor, already noted by the fixer.
- `check_gameversion.sh` runs only on non-main refs, so a direct push to main skips it; the
  cross-branch collision it guards can only arise on branches, so this is coherent.

BLOCKING: 0
