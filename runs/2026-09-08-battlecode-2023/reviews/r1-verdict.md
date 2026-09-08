blocking: 0

# r1 verdict — battlecode-2023 (bc23 year module, MOD of Metta-AI/cogame-battlecode)
Head: 47f360011e0b46fe6ede8e8f71a702a63fe84c74   Checklist: /workspace/coworld-builder/prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes
Base: 6885a0625687c7caec19b879e0ea09613ebd74f0   Review read only after my independent notes; r1-fixes.md read last, as required.
CI evidence: run 34244272097 on main at 47f36001, conclusion `success`, 9/9 jobs `success`
(test, docker-smoke, wasm-viewer, parity-oracle, parity-oracle-bc20/21/23/24/25) — verified via
`gh run view --json`, not accepted from anyone's report.

## Independent notes (written before reading r1-review.md)

- CI: run 34244272097 at 47f36001, `success`, 9/9 jobs.
- Test-file history 6885a062..47f36001: 31 removed lines, all accounted for —
  knob clauses restored + one gate RAISED 115→130 (e38d025), survival negative control
  armed + `refusedActions` moved INTO the verdict (857f71d), CSS-scope scan rewritten to
  scan the whole `<style>` block (f536d79), `test_viewer` YEARS list extended, and
  `test_bc25_replay.nim:323` moved from `gameVersion == GameVersion` to
  `gameVersion in ReplayCompatibleGameVersions` — the form bc20/21/24 already use,
  forced by the GV08→GV09 bump; the re-derivation assertion (`rederives(text) == -1`)
  is unchanged. No skip, no xfail, no deleted test file, no tolerance widened-to-pass.
- Manifest: `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `num_agents: 2` in
  all six variants' game_config AND certification.game_config, absent at every variant
  top level; cert fixture unchanged (bc26, awu+scaffold, len(players)==2==num_agents);
  `player[]` = [awu, scaffold]; `protocols` {player, global}; docs = readme + 8 pages,
  all `{type,value}` objects.
- docker_smoke.sh mode 100755; SEAT-COUNT machinery at :141–:227; docker-smoke log
  (job 102122090726): **zero** `SEAT-COUNT FAIL`; six episodes, six `reason=complete`,
  "replay.json year=bc26 bc20=bc20 bc21=bc21 bc24=bc24 bc25=bc25 bc23=bc23".
- policies.json: bc23 set = 2 PLAYER_PROMPT champions + 2 scripted fillers;
  battlecode-bc23-alchemist (champion #2) carries "player": ply_bac48eb1-662e-44f8-973d-f3e016dccf5d.
  `grep '<slug>\|<IMAGE>\|<SEATS>'` over the five gated files: no match.
- coworld-release.yml order: Build manifest (:168) → Certify (:182) → Upload the policies
  (:225) → Upload the Coworld (:323) → Put the Coworld secret (:419). Three workflows present.
- wasm-viewer `needs: docker-smoke` (ci.yml:2449); viewer_smoke.mjs run once per replay,
  bc23/bc24/bc25 at `--timeout 120 --soak 15`; log: `loaded:true` on all six replays incl.
  bc23 ("0:16 GAME 1 OF 1 — QUIET", motto "Anchor the sky." = the fallback sheet),
  `scrub selector: #scrub` each time; node wasm smoke `mismatch_round:-1` on all replays
  incl. the committed bc23 fixture.
- replay-viewer/ (config.nims, static_replay.js, worker), client/chrome_common.js and
  client/broadcast_core.js: **zero diff from base** — byte-identical inherited runtime.
  No MODULARIZE flag anywhere + `Module.onRuntimeInitialized` bootstrap
  (static_replay_worker.js:218) = matched pair from the one starter. data-replay-loaded
  set at static_replay.js:180 on the worker's first-frame message; data-replay-error at :20.
- replay_broadcast.html: +509/−3 vs base; the 3 removed lines are the `--statrail` id list
  and the two year-guard lines, each replaced additively with bc23 added. Banner
  "BC23 additions to the inherited cogame-battlecode chrome" (:3225/:3536/:4858). Twelve
  `html[data-year="bc23"] .beat-marker.<kind>` rules (:3381–3392). buildBc23BeatButtons /
  applyBc23BeatSpoilers own names (:4931/:4954). `.plate-name { flex: 1 1 auto;
  min-width: 3.2em; }` at :2571; 640px media queries present. #viewpanel kept (design
  note §Zoom pins it: pool tops at 60×30, 960px render vs 360px frame).
- decide.nim: ONE parallel batch via `curly.makeRequests` (:864) over all open seats;
  attempt1Ms/retryMs (:846); doctrineBudgetMs monotonic wrap (:806); `while open.len > 0
  and attempt < 2` = exactly one retry; fallback recorded as results.fallbacks +
  `doctrine_fallback` event (:819–:921); throttle fast-fail.
- match.nim: monotonic matchBudget/perGameBudget guards (:378–:389); rules.nim budget
  check every 32 rounds. Variant arithmetic: 25+45+340+~30 ≈ 440–445 s ≤ 720 s.
- Truncation: truncateRunes/truncateBytes rune-boundary (sim_types.nim:268–295);
  test_bc23_sheet feeds `"\u{1F680}".repeat(400)` at the caps, asserts runeLen and
  `validateUtf8() == -1`, incl. the 16 KB byte cap.
- Re-derivation: test_bc23_replay asserts record→re-derive identical hash chain for every
  bc23 end reason incl. deadline/abandoned via `plan.abandon_after`; viewer derives from
  the same Deriver (bc_replay.nim), exports bc_mismatch_round.
- Baselines: test_bc23_baselines asserts `refusedActions == 0` and lemonade beats
  examplefuncsplayer23 6/6; survival gate 6 full 2000-round games with the
  -d:bc23BrokenChassis inverted control now executed as a subprocess (857f71d).
- Names: observation carries alias/opponent_alias only; `names[]` only in
  replay/results/broadcast (viewer side).
- Parity job at head: Tier B whole-domain byte-diff ("Tier B: the committed arithmetic
  table IS the jar's own output"), Tier A + Tier A′ (`bc23scenario` twin) — "12 pairs,
  all bit-exact for whole 2000-round games, ledger empty", the Tier A′ coverage step
  asserting the rare paths fired off the JAVA trace, and the `--selftest` for the
  first_divergence walker ("4 cases, length mismatches detected on both sides").
- Renderer fixture: tools/ci/renderer_fixture.html:70 `YEARS = ['bc26','bc20','bc21',
  'bc24','bc25','bc23']` with a real bc23 row (:346–:479, full-cap 280-rune notes on BOTH
  seats into #bc23-doctrines-body, fallback badge, full-cap motto through .plate-sub);
  parent gates data-replay-loaded on ALL year×width verdicts (:125–:145), fail() sets
  data-replay-error (:79–:82) which viewer_smoke.mjs fails on immediately (:688); its own
  ci.yml step runs it served over http with --strict-text-bounds; log:
  `{"loaded":true,...}` then `canvas text: 0 drawn, 0 never inside ... (--strict-text-bounds)`.
  The `0 drawn` is the true count: **no fillText/strokeText exists anywhere in this
  viewer** (grep over replay-viewer/, client/, render.nim = empty) — every string is DOM,
  so the LLM-text legibility gate is the fixture's own DOM overflow + not-shortened
  assertions, which are load-bearing (they set the error attribute the harness fails on).

## Standing blocking findings

None. Every finding that was true at f9b292a2 is fixed at 47f36001, and my own checklist
pass found nothing standing.

## Refuted / resolved review findings (verified at head, not taken from the fixer)

### F18 (the review's only BLOCKING, item 15) → TRUE AT f9b292a2, FIXED AT HEAD
- Evidence: tools/ci/renderer_fixture.html:70 at 47f36001 —
  `var YEARS = ['bc26', 'bc20', 'bc21', 'bc24', 'bc25', 'bc23'];` and the bc23 row at
  :346–:479 building #bc23-islands/#bc23-econ/#bc23-units/#bc23-doctrines with full-cap
  notes on both seats (commit 72bbeaa). The row found and fixed two real clips inside the
  bc23 block (#bc23-econ/#bc23-units now `width: max-content; max-width: calc(100% - 16px)`,
  #bc23-doctrines now `max-height: min(46vh, …)`), both asserted in tests/test_viewer.nim.
  The fixture step ran green in run 34244272097 with --strict-text-bounds (`loaded:true`,
  wasm-viewer log :2312–:2313). A finding that was true and has since been fixed → refuted
  at the current head.

### F19 (Tier A′ not shipped) → FIXED at head (76c576f)
- tools/oracle/bc23/bc23scenario/RobotPlayer.java exists; ci.yml runs
  `--bots examplefuncsplayer23 bc23scenario`; parity log: 12 pairs bit-exact, ledger
  empty; the "Tier A-prime really exercised the paths" step asserts seven path classes off
  the Java trace. docs/PARITY.md:774 "Tier A′ (BLOCKING) — SHIPPED".

### F20 (negative control never executed; dead refusedActions) → FIXED (857f71d)
- tests/test_bc23_survival.nim now re-runs itself as a subprocess with
  `-d:bc23BrokenChassis -d:release` and requires the child red; `refusedActions != 0` is
  inside the per-game `ok` determination. Both passes of the `test` job show
  "running the inverted control".

### F21 (elixir clause ≥1 of 6 vs note's ≥4 of 6) → REFUTATION SOUND
- Verified: tests/test_bc23_survival.nim:28–41,56 carries the measurement (lemonade mirror
  ends by conquest at rounds 800–1100 on 5 of 6 small maps; 3 of 6 flip a well; the note's
  4-of-6 is unreachable on the measured evidence). No checklist item names it. The design
  note's repo copy now carries the dated addendum (fd0c675). Non-blocking, correctly held.

### F22 (two smoke per-seat floors below the note) → REFUTATION SOUND
- Verified: ci.yml's 20-line measurement comment above SMOKE_REQUIRE_STATS; the note's own
  two constraints ("never below this note's numbers" / "never above what a correct episode
  produces") are unsatisfiable together for mana_mined (weak seat 25 < 40) and damage_dealt
  (weak seat 2 < 20 — the upstream example bot's launcher attacks EAST of itself and may
  not be fixed, being one side of the oracle). The across-the-pair, year-signature floors
  are AT or ABOVE the note's (units≥60, banked≥200, anchors_built≥1, anchors_placed≥1,
  islands_captured≥1; measured 79/3480/5/3/3 in the smoke log). Non-blocking, correctly held.

### F23 (knob margins retuned; three clauses dropped) → FIXED (e38d025)
- Three clauses restored with measurements (anchor_round first-anchor, island_priority
  islands-lost, retreat launchers-lost, incl. new `launchers_lost` on GameOutcome23); one
  gate raised to the note's number (115→130); the six remaining reductions documented
  note/measured/gated in the shard header. test_bc23_knobs 50 checks release (was 44).

### F24 (vacuous CSS-scope check) → FIXED (f536d79)
- The scan now parses the single <style> block, strips comments, walks selectors at each
  `{`, requires every bc23-naming selector part to be `#bc23-`/`html[data-year="bc23"]`-
  scoped, and asserts a non-vacuity floor `scanned >= 60` (87 parts scanned).

### F25 (first_action field `action` vs note's `kind`) → REFUTATION SOUND
- match.nim:236–241: a field named `kind` would silently overwrite the event kind under
  MatchEvent's field flattening; bc24/bc25 already emit `action`; broadcast.nim reads
  `e.fields{"action"}`. Now recorded as docs/RULES-BC23.md §Divergences item 18 (6e186b6).
  The code is right; no checklist item is touched.

### F26 (first_divergence off-by-one on a one-line-longer Java trace) → FIXED (6f49a47)
- `itertools.zip_longest` with `<the trace ends here>` sentinel; the tail check is gone;
  a `--selftest` (4 cases) is wired into the job ahead of the real invocation and passed
  in run 34244272097 ("length mismatches detected on both sides").

### F27 (interleaved EndReasons doc comment) → FIXED (b9cca9f)
- results.nim:195–206 reads cleanly in order bc24 → bc25 → bc23 at head.

### F28 (the note's `base 5 × 0.70 → 3` vector) → REFUTATION SOUND, independently recomputed
- I recomputed it myself: `70/100.0` rounds to the double 0.699999…95559; the exact product
  5×that is 3.5 − half-ulp, which the float64 multiply rounds (ties-to-even) to **exactly
  3.5**; Java's `Math.round` = floor(3.5+0.5) = **4**. `python3: 5*(70/100.0) == 3.5 →
  True`. The tree asserts 4 (tests/test_bc23_tempo.nim:14–33) and Tier B byte-diffs the
  whole lattice against the jar's own JVM output (green). The note is wrong; the tree is
  right; the note's larger point survives on the replacement vectors (45×0.70: 31 vs 32).

### F1–F17: the review's traced-and-consistent set — spot-verified, no disagreement
- I independently reproduced the substance of F1–F3, F5–F13, F15–F17 (see Independent
  notes); F4 (coworld version 0.6.0) is a phase-40 workflow_dispatch input, not a tree
  fact — correctly excluded, verified: no version constant in the manifest template.
- F14 verified: the committed fixture emits all twelve beat kinds; test_bc23_beats asserts
  emission + label + style from the committed artefact and the three-way year discriminator
  (broadcast.nim:142–143,172,179).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 34244272097 `success` 9/9 at 47f36001; `git log -p 6885a062..47f36001 -- tests/`: all 31 removed lines traced (knobs restored/raised e38d025, survival armed 857f71d, CSS scan strengthened f536d79, bc25 GameVersion→compat-list form with rederives unchanged); no skip/xfail/deleted test |
| 2 Replay re-derivation | PASS | replay.nim Deriver.advance vs recorded chain; bc_replay.nim same Deriver, bc_mismatch_round; tests/test_bc23_replay.nim record→re-derive for every end reason; wasm smoke `mismatch_round:-1` on the bc23 replay + committed fixture |
| 3 Static viewer | PASS | manifest `game.replay_viewer={"bundle":"static-replay-viewer"}`; tools/build_replay_viewer.sh present+executable, asserted in ci.yml; `/client/replay` appears only as a release-workflow guard message and the inherited broadcast_core legacy-URL rewrite (both unchanged from base) |
| 4 Both name spaces | PASS | decide.nim observation: alias/opponent_alias only; names[] only in replay.nim:127/results.nim:79/broadcast.nim (viewer) |
| 5 Degrade-never-hang | PASS | decide.nim:806/:826/:846/:864 (bounded batch, one retry, budget wrap); match.nim:378–389 monotonic guards; rules.nim in-loop budget check; 25+45+340+~30 ≈ 445 s ≤ 720 s. (A hosted credentialed episode's wall clock is a phase-60 fact; every bound is in the tree.) |
| 6 num_agents everywhere + SEAT-COUNT | PASS | manifest: 6 variants + cert fixture all `num_agents: 2` in game_config, none at top level; docker_smoke.sh:141–227 four invariants + SMOKE_SEATS cross-check; job 102122090726 log: 0 × `SEAT-COUNT FAIL` (grepped) |
| 7 Scripted baseline full legal episodes | PASS | smoke bc23 episode `reason=complete` (755/800 rounds, keyless); test_bc23_replay clinch block asserts reason=="complete"; test_bc23_baselines refusedActions==0 + ops budget + lemonade 6/6; floors measured (survival/knobs headers), inverted control executed |
| 8 LLM reply handling | PASS | llm.nim fence-tolerant extraction (inherited unchanged); decide.nim exactly-one-retry (:826), fallback sheet + results.fallbacks + `doctrine_fallback` event (:819–:921) |
| 9 Rune-safe truncation | PASS | sim_types.nim:268–295; tests/test_bc23_sheet.nim:156–176 astral-plane at caps, validateUtf8 == -1 |
| 10 Manifest validates | PASS | protocols carries BOTH player and global; docs = readme + 8 pages, all {type,value}. readme is `{"type":"uri",…}` — byte-identical to the base sha (verified against 6885a062), pinned by the design note (:1643), accepted by the installed coworld CLI via test_manifest (test job green). Out of MOD scope to relitigate the base convention |
| 11 Legible at 360px | PASS | replay_broadcast.html:2571 `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; 640px media queries; bc23 boxes drop labels under 640px; killfeed-overlap gate at 360/720/1280 both zooms on all six replays |
| 12 Release order + scaffold | PASS | coworld-release.yml :168→:182→:225→:323→:419; three workflows; docker_smoke.sh 100755; policies.json 24 entries, bc23 = 2 PROMPT + 2 scripted, champion #2 carries ply_bac48eb1-…; placeholder grep no-match |
| 13 Viewer executes | PASS | wasm-viewer green incl. browser step, `needs: docker-smoke` (ci.yml:2449), no continue-on-error; loaded:true × 6 replays, scrub #scrub, endcard computed-shown gate; markers from static_replay.js:20/:180; lobby: format has no lobby frames (frame==round, `"st": 0` in every year's frame, broadcast.nim), runtime byte-identical to base; config.nims (no MODULARIZE) + worker onRuntimeInitialized = same-starter matched pair, and the smoke's loaded:true is the positive evidence |
| 14 Chrome is the starter's | PASS | chrome_common.js & broadcast_core.js zero diff vs base (byte-identical); replay_broadcast.html +509/−3, the 3 removals additive list/guard extensions, bc23 block under the named banner; relayout() sets --band/--hudscale/--topband/--statrail on document.documentElement; #endcard bottom: var(--band), shown with .on, every seek path dismisses (seek() first statement); beats are labelled <button>s with CSS for all twelve emitted kinds, scoped html[data-year="bc23"]; #viewpanel kept per the note (board 960px vs 360px frame) |
| 15 Every drawn string fits | PASS | no canvas text exists in this viewer (no fillText/strokeText anywhere — total: 0 is the true count, not missing coverage); the LLM-text worst-case fixture (renderer_fixture.html) has the bc23 row at head, full-cap notes on BOTH seats + full-cap motto, own ci.yml step with --strict-text-bounds, parent gates data-replay-loaded on all 18 year×width verdicts and fails via data-replay-error on any overflow or any shortened string; run 34244272097 log: `{"loaded":true,…}` + `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` |
| Simultaneous batch rider | PASS | one decision turn per episode; both seats' calls in ONE curly.makeRequests batch (decide.nim:847–864) |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F18 | fixed, 72bbeaa | bc23 row + chrome clip fixes + test assertions at head; step green in 34244272097 | yes |
| F19 | fixed, 76c576f, 12 pairs bit-exact | Java twin exists; job log shows 12× bit-exact, ledger empty, coverage step | yes |
| F20 | fixed, 857f71d | subprocess control + refusedActions in `ok`; "running the inverted control" in test log | yes |
| F21 | refuted-correct, docs fd0c675 | measurement at the site + addendum; no checklist item | yes |
| F22 | refuted-correct, docs fd0c675 | ci.yml measurement comment; note's constraints unsatisfiable together; pair-level floors ≥ note | yes |
| F23 | fixed, e38d025 | 3 clauses restored, 1 gate raised, 6 reductions documented; 50 checks release | yes |
| F24 | fixed, f536d79 | real scanner + non-vacuity floor (scanned ≥ 60) | yes |
| F25 | refuted-correct, docs 6e186b6 | field-flattening reason real; divergence item 18 present | yes |
| F26 | fixed, 6f49a47 | zip_longest + sentinel; --selftest wired and green | yes |
| F27 | fixed, b9cca9f | comment reads cleanly at head | yes |
| F28 | refuted, note wrong | independently recomputed: 5*(70/100.0) == 3.5 exactly (ties-to-even), Math.round → 4; Tier B green | yes |

## Non-blocking observations (mine, new; no checklist item — advisory)

1. **Tier A′ scenario bytecode peak 28–43 % vs the note's stated 25 % self-cap**
   (design.md §Tests Tier A′ "the job asserts it never exceeds 25 %"). The committed job
   enforces the 50 % comparison-validity headroom instead (tools/ci/parity_tiers_bc23.py:75,
   HEADROOM_PCT), and the 28–43 % measurement is documented in the script's own docstring
   (:32–34, "so this bot too is never cut off mid-turn"). Technically sound — a mid-turn
   cut-off needs 100 % — but it is a note number the tree quietly halved the safety margin
   on; worth one line in the addendum next time it is edited.
2. **The forced-end scenario variants are not shipped**: `-d:bc23ScenarioConquest` /
   `-d:bc23ScenarioTie` (design.md §Tests Tier A′) do not exist, so the CONQUEST /
   MORE_REALITY_ANCHORS / MORE_ADAMANTIUM_NET_WORTH rungs, destabilizers, boosters,
   ACCELERATING anchors and the non-identity tempo lattice are not oracle-compared. The
   residue is recorded where the note says it goes (docs/PARITY.md §"What is NOT compared",
   with the measurement: peak team elixir 80 < cheapest sink 150). The end-ladder rungs are
   unit-tested (test_bc23_endladder, test_bc23_tempo, test_bc23_islands) and Tier B covers
   the full arithmetic lattice. Design-note deviation, disclosed; no checklist item.
3. **The four sibling years' parity scripts still carry the F26 zip bug and the toHex
   padding latent** (the fixer's own NOTED items 1–2) — out of this MOD run's scope,
   flagged for a maintenance pass.

## Could not verify (and why it does not count as blocking)

- The coworld version 0.6.0 and the release itself: phase-40 workflow_dispatch inputs, not
  tree facts at any sha — the checklist's item 12 covers the workflow's order and scaffold,
  which I verified; no checklist item requires the dispatched version string to exist in
  the tree.
- A hosted, credentialed episode's end-to-end wall clock: no checklist item demands a
  hosted run at phase 30; item 5 demands bounds and settle-inside-720s by construction,
  which the tree proves (every wait bounded; worst case 445 s). Phase 60 measures the rest.

Both are inherently un-carryable by the reviewed sha rather than unverifiable evidence for
a checklist item, so neither adds to the count under the checklist rule.

## Count

Zero blocking findings stand at 47f360011e0b46fe6ede8e8f71a702a63fe84c74.

BLOCKING: 0
