# r1 review — battlecode-2016 (`bc16` year module of `Metta-AI/cogame-battlecode`)

Reviewed sha: **`fbc7d345e116dcb5e7c6fbae510144da09f11a8b`** (`main`, merge of PR #10)
Diff range: **`00c1dae..fbc7d345`** — 118 files, +20 726 / −84
CI run verified: **`34322655506`** (`ci.yml`, `main` @ `fbc7d345`) — `conclusion: success`, all 11 jobs
`success` (`test`, `docker-smoke`, `wasm-viewer`, `parity-oracle`, `parity-oracle-bc16/20/21/22/23/24/25`)
Round: **1**
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision rule)
Design note: `runs/2026-09-09-battlecode-2016/design.md` (2914 lines, read in full once)
Coworld checkout read: `/tmp/review-bc16` at the reviewed sha. Files opened in full: 24; ranged/grep reads: ~70.

Nothing in the design note, the idea text, the build report, the CI logs or any repository file contained
text addressed to the reviewer. Comments and TODOs in the tree were read as data.

---

## Findings

### F1 — bc16's endcard HUD-suppression rule can never match: the class is wrong **and** the sibling direction is wrong

*Checklist item: advisory (no checklist item names it). Bears on design.md:2004–2005 "endcard fix 5" and
design.md:2547 §Tests item 27.*

- `client/replay_broadcast.html:3792-3799`
  ```css
  /* THE HUD MAY NOT BLEED THROUGH THE ENDCARD (the bc23 finding). */
  html[data-year="bc16"] #endcard.show ~ #bc16-archons,
  … #endcard.show ~ #bc16-doctrines { visibility: hidden; }
  ```
- The class the page actually toggles is `on`, not `show`:
  `client/replay_broadcast.html:1878` `#endcard.on { display: flex; … }`;
  `:6823` `$('endcard').classList.add('on');`; `:6771` `$('endcard').classList.remove('on');`.
  The page's own comment at `:6820` says so: "`.on` is the class the INHERITED rule uses".
- Even with `.on`, the `~` general-sibling combinator selects only **following** siblings. I parsed the
  page: `#endcard` (`:4057`) and `#bc16-archons`/`#bc16-horde`/`#bc16-units`/`#bc16-econ`/
  `#bc16-doctrines` (`:3991-3999`) are all children of `#chrome`, and the `#bc16-*` boxes come
  **before** `#endcard` in document order. `#endcard.on ~ #bc16-archons` would still match nothing.
- The rule is the only `visibility: hidden` declaration in the whole 6900-line page
  (`grep -c 'visibility: hidden' client/replay_broadcast.html` → 1, at `:3798`), so no other year has an
  equivalent and nothing else hides the boxes.
- Observed consequence: `#endcard` spans `top: var(--topband)` … `bottom: var(--band)` (`:1855-1857`) at
  `z-index: 30` over a `radial-gradient(… rgba(16,11,7,0.82), rgba(9,6,3,0.95))` background (`:1864-1865`),
  i.e. **not opaque**; `#bc16-archons` is `z-index: 7` (`:3689`), `#bc16-econ`/`#bc16-units` `z-index: 6`
  (`:3731`) and `#bc16-doctrines` `z-index: 8` (`:3767`), all positioned inside the endcard's own box.
  So the year boxes sit behind a partly transparent score screen and are not suppressed.
- The test that claims to cover this is a text grep and cannot see it:
  `tests/test_viewer.nim:1425-1428` asserts the literal string
  `html[data-year="bc16"] #endcard.show ~ #bc16-archons` is *present* in the page, and
  `tests/test_viewer.nim:490-491` asserts `"#endcard.show {" notin page` — which passes because the bc16
  rule's text is `#endcard.show ~ …`, not `#endcard.show {`. Both assertions are green and the rule is dead.
- Design note: design.md:2004-2005 "**No HUD bleed-through.** `#endcard` is opaque over the board and the
  `#bc16-*` boxes are `visibility: hidden` while it shows (the bc23 finding)."
- **Inference, not observed at runtime:** I did not open the page in a browser. The class mismatch and the
  sibling-order mismatch are both read directly off the file; the *visual* consequence is inferred from the
  z-indexes, the endcard's alpha and the boxes' geometry.

### F2 — the worst-case renderer fixture has no bc16 row, so bc16's LLM-authored text is drawn nowhere any gate looks

*Checklist item: **15** (last bullet — "a repo that draws model text and has no such fixture is a blocking
`legibility` finding"). The fixture exists and runs; it just does not cover this year.*

- bc16 **does** draw LLM-authored text. `client/replay_broadcast.html:5870-5895` (`renderDoctrines`) writes
  `d.motto` (48-rune cap), `d.notes` (280-rune cap) and `d.submitted` (120 runes) into
  `#bc16-doctrines-body` (`:3999`). The data comes from `src/battlecode/broadcast.nim:495-521`
  (`notes`, `motto`, `submitted`). The whole `#bc16-*` set is `display: none !important` under any other
  `data-year` (`client/replay_broadcast.html:3668-3674`).
- `tools/ci/renderer_fixture.html:70`
  `var YEARS = ['bc26', 'bc20', 'bc21', 'bc24', 'bc25', 'bc23', 'bc22'];` — **no `bc16`**.
  `:179` sets `data-year` from that list; `:563` picks the probe element as
  `year === 'bc26' ? 'doctrines' : year + '-doctrines'`. The fixture therefore never sets
  `data-year="bc16"`, never emits a `#bc16-*` id, and never measures `#bc16-doctrines`.
- The file was not touched by this run: `git log --oneline -1 -- tools/ci/renderer_fixture.html` →
  `567710b test(bc22): …`, and it is absent from `git diff --name-only 00c1dae..fbc7d345`.
- Design note: design.md:2832 — "The fixture gains a **bc16 row**." Not done.
- CI evidence (run 34322655506, job `wasm-viewer` = 102373769442): the step
  `Render the full-cap doctrine-text fixture` (`.github/workflows/ci.yml:4253`) **did run** with
  `--strict-text-bounds` and printed
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
  The fixture's real gate is its own DOM measurement (`tools/ci/renderer_fixture.html:640-690`: panel-height
  rule, both `.plate-sub` mottos still at the cap, both `.dline i` notes byte-identical to the full-cap
  string) — that code executed seven times, once per non-bc16 year, and zero times for bc16.
- The replay runs cannot substitute: `canvas_text: {total: 0}` on all eight replays (job log lines
  2233–2341), which the checklist itself says "means the check covered nothing … and is not evidence of
  anything", and `docker_smoke.sh` runs without `ANTHROPIC_API_KEY` (docker-smoke log: "no ANTHROPIC_API_KEY:
  the game must complete on its scripted baselines"), so the bc16 replay carries only the scripted
  `notes:"default bulwark doctrine"` / `motto:"The wall holds."`
  (`src/battlecode/baselines.nim:226-236`) — 26 runes and 15 runes against caps of 280 and 48.

### F3 — three of the survival gate's substance floors sit **below** what the broken-chassis control already achieves

*Checklist item: advisory (the checklist has no survival-gate item). This is the check coordinator ruling 3
explicitly asked for: "a floor set below what the BROKEN column already achieves is worth reporting."*

Observed floors and the control's own measured values, from the test's inline tables:

| floor | value | `-d:bc16BrokenChassis` measurement | discriminates? |
|---|---|---|---|
| `MinNotDestroyed` (`tests/test_bc16_survival.nim:84`) | 2 of 6 | 0 of 6 (`:53`) | **yes** |
| `MinUnitsBuilt` (`:87`) | 25 per seat per game | 62–133 (`:47-52`); the comment on `:87` itself says "(broken 62)" | **no** |
| `MinDamageDealt` (`:88`) | 1500 per seat per game | the comment on `:88` says "(broken 3333)" | **no** |
| `MinGuardsBuilt` (`:89`) | 2 per seat per game | 0 (`:47-52`) | **yes** |
| `MinDensKilled` (`:94`) | 4 across six maps | 0 (`:53`) | **yes** |
| `MinMedianRounds` (`:98`) | 1000 | the comment on `:98` says "broken 1029" | **no** on the recorded measurement |
| parts income > 0 per seat (`:139`) | 1 tenth | non-zero (the control still earns income) | **no** |
| parts collected across the pair where the map has deposits (`:144-146`) | 1 tenth | 0 on `swamp` (`:54`) | **yes** |

- All five substance clauses ruling 3 required are present (per-seat units built `:133`, damage dealt `:134`,
  guards built `:135`; `>= 1` den killed — committed at 4, `:212-214`; median-round floor `:216-217`; parts
  income/collected `:139` and `:144-146`), and the whole gate does come back red under
  `-d:bc16BrokenChassis` (`:219-251`).
- CI evidence (job `test` = 102372608026, log lines 1375–1385): the control failed on **16** clauses, and the
  eight printed are all `guards built 0 < 2` plus `swamp: parts collected across the pair (tenths) 0 < 1`.
  **Not one of the printed failures is a units-built, damage-dealt or median-rounds failure** — which is the
  same conclusion as the table above, from the run itself.
- So the gate's discriminating power rests entirely on guards, dens, the ratio, and `swamp`'s parts. The
  units/damage/median clauses are anti-degeneracy floors that the named broken control passes.

### F4 — the survival gate's inline "healthy" measurements do not match what this build actually measures in CI

*Checklist item: advisory. Bears on coordinator ruling 3 ("both measurement tables … inline in the test
header AND in `docs/RULES-BC16.md` §Divergences").*

- Claimed: `tests/test_bc16_survival.nim:34-35` — "**3 of 6** … **20 dens killed**; median **2147** rounds";
  repeated in `docs/RULES-BC16.md:374-377` ("3 of 6 | 20 | 2147").
- Measured by run 34322655506 (`test` job log line 1375, both debug and release passes identical):
  `HEALTHY games=6 notDestroyed=3 dens=14 median=2015 rounds=@[3000, 695, 3000, 707, 3000, 1030]`
- Claimed broken median 1029 (`:98`, `docs/RULES-BC16.md:377`); measured `median=873` (log line 1376).
- Both tables are present as the ruling required, and every committed floor still holds on the measured
  numbers (14 ≥ 4, 2015 ≥ 1000, 3 ≥ 2). The numbers in the two tables are simply stale relative to the code
  that shipped. Note the interaction with F3: on the *recorded* table the broken median (1029) is above the
  floor (1000); on the *measured* run it is below (873). The floor is inside the control's own noise band.

### F5 — Tier A′ was not built; the comparator's own CI summary nevertheless states that Tier A′ passed

*Checklist item: advisory (the checklist has no parity item). Bears on design.md:2647-2678 (Tier A′ declared
BLOCKING) and design.md:2710 (Tier A′ named in the phase-30 exit condition).*

- `tools/oracle/bc16/` contains exactly `Bc16Trace.java`, `bc16greenhorn/RobotPlayer.java`,
  `bc16idle/RobotPlayer.java`, `build_oracle.sh`, `jar.lock`. The design's four scenario bots
  (`bc16scenario`, `…turn`, `…annihilate`, `…tie`) do not exist.
- `.github/workflows/ci.yml:3003-3011` builds only the `-d:bc16Idle` and default (greenhorn) Nim trace
  emitters; `:3086` and `:3139` run `--bots bc16idle bc16greenhorn`. The step is named
  `Tiers A, A″ and C (all BLOCKING)` (`:3126`) — A′ is correctly absent from the step name.
- But `tools/ci/parity_tiers_bc16.py:451` heads its summary column `tier A/A'`, and `:457-459` prints
  "The phase-30 exit condition is Tiers A, A' and B passing with an EMPTY ledger". That line appeared
  verbatim in the CI step summary (job 102372608002, log line ~1127) beneath a table of 18 `bc16idle` /
  `bc16greenhorn` pairs. A reader of the CI summary alone would conclude Tier A′ ran.
- The gap **is** disclosed honestly in `docs/PARITY.md:1844-1885` ("Tier A′ — NOT IMPLEMENTED, and named
  here rather than left implied"), including the exact consequence: "`more_archon_health` and
  `more_parts_net_worth` have no Java-side evidence" (`:1873-1875`). `scenario16.nim` exists on the Nim side
  (`src/battlecode/years/bc16/chassis/scenario16.nim`) with a header saying it has no Java twin, and
  `-d:bc16Scenario` is not built anywhere in `ci.yml`.
- What *did* run and pass: 18 pairs bit-exact for whole games, ledger empty
  (`tools/ci/parity_ledger_bc16.json` = `{"entries": []}`), plus Tier B's whole-domain byte-diff of
  `data/bc16/tables.json` and of all 22 maps' symmetry and per-den split against the JVM.

### F6 — the parity job's anti-vacuity floors are not the ones the design note specifies

*Checklist item: advisory.*

- design.md:2574: "`ci.yml` additionally asserts every game reached at least **2 900 rounds** and that at
  least **150 zombies** were spawned".
- Observed: `.github/workflows/ci.yml:3069` asserts `rounds >= 250`, and `:3115` asserts that the **sum of
  `zombies_peak` over the eighteen pairs** is `>= 150` (measured 735). Neither is the note's per-game
  2900-round floor.
- The reason is recorded in the workflow itself (`:3013-3023`): neither oracle bot survives to round 3000 —
  measured 298–683 rounds for `bc16idle` and 485–1424 for `bc16greenhorn` — and the trace runs to the
  engine's own `isRunning() == false`, so the end round and the domination factor are themselves compared.
  The CI log confirms the measured lengths (job 102372608002, lines 908–960).
- I regard the substitution as sound and disclosed; it is recorded here because it is a divergence from a
  literal design-note assertion.

### F7 — several packed integer fields in the hash chain and the event stream collide once a count exceeds its field width

*Checklist item: advisory.*

- `src/battlecode/years/bc16/rules.nim:395-398`
  `w.mixHash(robotTypeCount(scout)*1000000 + soldier*10000 + guard*100 + viper)` and `:399-400`
  `turret*100 + ttm`; `:418-421` packs the four zombie counts base-100 the same way. Any single count of
  100 or more carries into the next field, so two distinct censuses can fold to the same chain value.
- Plausibility, measured: the parity job reports `peak_robots` of 104–162 (job 102372608002, lines
  935–960), and `tests/test_bc16_survival.nim:28-33` records 177–212 units built per seat on
  `checkers`/`prisons`. A soldier census above 99 in a 3000-round game is not hypothetical.
- Same shape in `src/battlecode/match.nim:498-506`: `archons` unpacked `div/mod 100` and `parts_worth`
  `div/mod 100000`. `parts_worth` = `int(parts) + Σ partCost` over live robots; the played pool's largest
  map carries 20 520 parts (`quadrants`), so 100 000 is a large but finite margin.
- Consequence traced: the hash chain is a **tripwire**, and a collision can only *hide* a divergence, never
  manufacture one. The `mismatchRound` gate in `src/battlecode/replay.nim:303-312` compares the chain
  frame by frame and reported `-1` on every bc16 recording in CI (`test` job, `test_bc16_replay: ok`; wasm
  job, `mismatch_round: -1`), so no divergence is being masked in the shipped fixtures. The other chain
  values (`rubbleChecksum`, `partsChecksum`, `execOrderChecksum`, both RNG seeds, `totalHealthTenths`) are
  unpacked and unaffected.

### F8 — `endReasonFor` maps "no winner at all" to `more_archons`

*Checklist item: advisory.*

- `src/battlecode/years/bc16/rules.nim:431-434`
  ```nim
  proc endReasonFor(w: World): string =
    case w.domination
    of dfNone: $dfPwned
    else: $w.domination
  ```
  `dfNone` (`years/bc16/units.nim:93`) is the "no winner" state, and it is rendered as
  `more_archons` (`units.nim:95`).
- Traced for reachability: `playGame` (`rules.nim:545`) loops `while w.running and w.currentRound < maxRounds - 1`;
  `checkEndOfMatch` (`:216-234`) fires at `currentRound >= maxRounds - 1` and always sets a winner via one of
  the four rungs; the abandoned path returns at `:554-560` before `endReasonFor`. The only way to reach the
  `dfNone` arm is `maxRounds <= 0`, which `config_schema.maxRounds.minimum = 50`
  (`coworld_manifest_template.json`) forbids. **Unreachable in the shipped configuration**; recorded because
  it silently mislabels rather than faulting.

### F9 — `#bc16-horde.struck` is a CSS rule nothing ever activates, and the "THE HORDE" spectator label is not drawn

*Checklist item: advisory. Bears on design.md:1772-1776 and design.md:319-320.*

- `client/replay_broadcast.html:3724` `#bc16-horde.struck { color: #f2e8d8; border-color: #6a5a3a; }`.
  `grep -n "struck" client/replay_broadcast.html` returns only that line and bc22's `:3517`; nothing in the
  bc16 block (`:5625-6019`) ever adds the class. `renderHorde` (`:5782-5814`) writes a fixed six-span
  string and never takes the strip over.
- Design note design.md:1772-1776: "On a wave round it takes over the strip for two seconds with what
  happened in plain words (`WAVE — 34 zombies from 4 dens at ×1.7`), and on a `turned` event with
  (`CLAN ASH'S ARCHON TURNS — a BIGZOMBIE at 34,19`)". Not implemented. The equivalent bc16 behaviour
  *is* implemented for the archon pill (`:5774-5776` adds/removes `flash`, styled at `:3690-3694`).
- Separately: design.md:319-320 says the zombie team "is drawn and labelled **THE HORDE**". The string
  "HORDE" appears in the page only in a CSS comment (`:3702`) and in the agent-facing observation
  (`src/battlecode/decide.nim:639` and `:1163`); `renderHorde` draws glyph counts, `WAVE`, `OUTBREAK`,
  `DENS`, `ROUND` and no faction name. The third-party naming is therefore agent-side only, not
  spectator-side. (This is cosmetic and does not affect ruling 4 — see the checklist walk, item 4.)

### F10 — one literal assertion was deleted from a shipped test file during this run

*Checklist item: **1** ("no test disabled, skipped, or loosened during this run … a deleted assertion … is a
blocking finding"). Reported as an observation with both readings; I am not asserting which one governs.*

- `git diff -U0 00c1dae..fbc7d345 -- tests/` shows exactly one deleted assertion, in
  `tests/test_bc22_replay.nim`:
  ```
  -  checkEq("the game version is GV10", r.doc.gameVersion, "GV10")
  ```
- What replaced it, in the same hunk (`tests/test_bc22_replay.nim:92-108` at the reviewed sha):
  the pre-existing `checkEq("and it is what the build claims", r.doc.gameVersion, GameVersion)` is
  **retained**, and three assertions are added — `gameVersion.len >= 4 and startsWith("GV")`,
  `gameVersion in ReplayCompatibleGameVersions`, and
  `ReplayCompatibleGameVersions.len >= 8 and "GV04" in ReplayCompatibleGameVersions`.
- Reading A (a deletion): the literal `"GV10"` assertion is gone from a sibling year's test file, which is
  what item 1's wording names.
- Reading B (not a loosening): the deleted assertion was `fixture == "GV10"`, which in combination with the
  retained `fixture == GameVersion` asserted `GameVersion == "GV10"` — i.e. it asserted that no `GameVersion`
  bump may ever happen. The authorised GV10→GV11 bump (coordinator ruling 2) makes it unsatisfiable by
  construction, and the substantive assertion (fixture pinned to the build's own headline) survives and is
  strengthened by the three new checks.
- The **fixtures** were regenerated, not weakened: `tests/fixtures/replay-bc22.json` and
  `replay-bc23.json` both now carry `"game_version":"GV11"` (verified by parsing both files), and the
  `game_version` assertions in `tests/test_bc22_beats.nim:41`, `tests/test_bc23_beats.nim:42` and
  `tests/test_bc23_replay.nim:262` are **unchanged** (`checkEq(…, doc.gameVersion, GameVersion)`), all three
  files absent from the diff.
- Every other test-file change in the range is additive or a count update: `tests/test_manifest.nim`
  (7→8 years, 9→10 doc pages, 28→32 policies, 14→16 prompts/scripted, `maxRounds` 2000→3000 assertion
  replaced by the widened bound plus a new per-variant `<= 2000` check for the seven shipped years),
  `tests/test_viewer.nim` (six-way → seven-way `isBc*` guard string, `--statrail` id list), and 27 new
  `tests/test_bc16_*.nim` files. No `skip`, `xfail`, `--skip`, `when false` or test-file removal appears
  anywhere in the range (`git diff -U0 00c1dae..fbc7d345 -- tests/ | grep -E '^-[^-]'` → the one line above
  plus the two fixture JSON lines).

### F11 — the authorised `tests/test_bc23_replay.nim` tolerant-end-reason edit was not applied

*Checklist item: advisory. Recorded only so the coordinator's ruling 7 ledger is accurate.*

- `tests/test_bc23_replay.nim` is not in `git diff --name-only 00c1dae..fbc7d345`. Its only `epDeadline`
  occurrence is a synthetic `ReplayDoc` at `:184`; there is no wall-clock block asserting
  `reason in [epDeadline, epComplete]`. The file's shape is unchanged from `00c1dae`.
- The other half of ruling 7 **was** applied: `.github/workflows/ci.yml:146` `timeout-minutes: 150`
  (was 130).

---

## ACCEPTANCE CHECKLIST, item by item

**1. CI green, no test disabled/skipped/loosened.**
Verified both halves from the sandbox. `gh run view 34322655506 -R Metta-AI/cogame-battlecode --json
status,conclusion,headSha,headBranch` → `{"conclusion":"success","headBranch":"main",
"headSha":"fbc7d345e116dcb5e7c6fbae510144da09f11a8b","status":"completed"}`; the 11-job breakdown is in the
header above. Test history read with `git diff -U0 00c1dae..fbc7d345 -- tests/`: exactly one deleted
assertion — **F10** — with the full hunk quoted there; two regenerated fixtures; no skip/xfail marker; no
test file removed. All 27 new bc16 shards ran twice (debug and `-d:release`) and passed
(`test` job log: `test_bc16_activation: ok (42)` … `test_bc16_zombies: ok`); `test_manifest`,
`test_viewer`, `test_sheet`, `test_determinism` and `test_constants` all green.

**2. Replay re-derivation, frame by frame, viewer derived from the same re-derivation.**
Observed. `src/battlecode/replay.nim:287-312` steps the sim one round per frame and compares
`session.hashChainHex()` against the recording at index `(roundInGame - 1) * ChainHexLen`, i.e. **every
round**, plus the game's final chain. The chain folded per round is 15 per-team values plus 10 packed
globals including both live `java.util.Random` 48-bit states
(`src/battlecode/years/bc16/rules.nim:392-425`). `tests/test_bc16_replay.nim:82-84,90,176,206,262` asserts
`mismatchRound == -1` on eight different recordings including a 3000-round game and the timed-deadline
race. The viewer draws from the **same** `Deriver` session: `src/battlecode/broadcast.nim:1902` calls
`bc16ChromeJson(doc, s.w16, …)` on the derived world, and every `#bc16-*` readout is computed from it
(`:1630-1823`). `tests/test_bc16_replay.nim:113-119` additionally asserts the document stores no
`robots`/`rubble`/`parts`/`board`/`signals`/`den_queues`/`rng`/`frames`/`grid` key. Independent CI
evidence: `tools/wasm_replay_smoke.cjs` reported `mismatch_round: -1` for both the bc16 smoke replay and
the committed bc16 fixture (`wasm-viewer` log lines ~2456-2460). See F7 for the one caveat on the chain's
resolving power.

**3. Static viewer.**
Observed. `coworld_manifest_template.json` `game.replay_viewer` = `{"bundle": "static-replay-viewer"}`
(unchanged this run). `tools/build_replay_viewer.sh` is present and mode `100755`
(`-rwxr-xr-x`), and `ci.yml:3966-3977` asserts both `-f` and `-x` before invoking it by path.
`coworld-release.yml:218-220` is the release-side gate that rejects a pod-served `/client/replay`. No
`/client/replay` path exists anywhere in the tree except that refusal message. The viewer's only network
read is the replay URL it is handed; `data/maps/bc16/`, `data/bc16/tables.json` and `data/atlas_bc16.*` ride
the existing `--preload-file {rootDir}/data@data` (no `config.nims` change in the diff).

**4. Both name spaces.**
Observed and matches coordinator ruling 4. In-game aliases are the year-neutral
`AliasA = "Clan Ash"` / `AliasB = "Clan Basil"` (`src/battlecode/sim_types.nim:240-241`, untouched by this
run). The agent-facing observation carries `"alias"` and `"opponent_alias"` only
(`src/battlecode/decide.nim:743-744`) — I grepped the bc16 brief for `names` and found none. The viewer
gets both: `bc16ChromeJson` emits `"aliases": [AliasA, AliasB]` **and**
`"names": [doc.names[0], doc.names[1]]` (`src/battlecode/broadcast.nim:1857-1858`), and the doctrine card
draws `doc.seats[slot].name` (`:510`). The third party is named `THE HORDE` in the agent brief
(`decide.nim:639`, `:1163`) and in the `zombies.team` field of the observation; it is never a seat and never
scores (`Team` has four values and only A/B are `isPlayer()`, `years/bc16/units.nim`). F9 notes that the
literal words "THE HORDE" are not printed in the drawn chrome.

**5. Degrade-never-hang, inside 60 % of `episodeTimeoutSeconds`.**
Observed. `episode_timeout_minutes: 20` → 1200 s; 60 % = 720 s. The bc16 variant's declared budgets
(`coworld_manifest_template.json`, variant `bc16`): `connectTimeoutMs 25000`, `attempt1Ms 20000`,
`retryMs 12000`, `doctrineBudgetMs 45000`, `perGameBudgetSeconds 120`, `matchBudgetSeconds 360` →
30 + 45 + 360 + 30 = **465 s ≤ 720 s**, exactly the note's arithmetic (design.md:646-655).
Every wait is bounded and I traced each: the LLM batch deadline
(`decide.nim:1312` `makeRequests(batch, max(1, deadlineMs div 1000))`), the phase budget
(`decide.nim:1254,1277-1292`), the match budget (`match.nim:557-568`), the per-game budget sampled every
32 rounds (`years/bc16/rules.nim:550-553`), and the round loop itself bounded by `maxRounds`
(`rules.nim:545`). `grep -rn 'while ' src/battlecode/years/bc16/` returns four loops, all bounded: an
`intSqrt` build loop (`units.nim:139`), two insertion sorts over ≤4 and ≤29 elements
(`world.nim:500`, `maps.nim:131`), the round loop, and `comms.nim:80`, which drains a queue capped at 1000
and breaks on budget exhaustion. There is no blocking read on any bc16 path. Chassis compute is capped by
the `DecisionOps` budget checked before each primitive (`world.nim:432-441`); CI measured `ops_peak = 205`
against a 2000 ceiling (`test_bc16_perf` output) and `opsUsedPeak <= 2000` is asserted
(`tests/test_bc16_perf.nim`). Measured runtime: `bc16 smoke: sim_seconds=1.334 rounds=900 wall=1.435s`
(docker-smoke log line 3017) and `bc16 perf: 977 rounds on 6147 in 0.118 s (0.12 ms/round)` in release
(`test` job log line 1303).

**6. `num_agents`.**
Observed. Parsed `coworld_manifest_template.json`: all **eight** variants (`bc26 bc20 bc21 bc24 bc25 bc23
bc22 bc16`) carry `game_config.num_agents = 2` and **none** carries a variant-top-level `num_agents`;
`certification.game_config.num_agents = 2` with `certification.players = [awu, scaffold]` (len 2) and
`certification.game_config.players` len 2. `tools/ci/docker_smoke.sh:148-188` enforces the four invariants,
each exiting non-zero with a `SEAT-COUNT FAIL:` prefix, and `:189-201` refuses a `SMOKE_CONFIG_OVERRIDE`
that changes `num_agents`. The independent second declaration is `docker_smoke.sh:82`
`seats_expected="${SMOKE_SEATS:-2}"` — the `<SEATS>` substitution landed as the script's own default rather
than as a `ci.yml` env var (`grep -n SMOKE_SEATS .github/workflows/ci.yml` → no match), and it is
cross-checked against the manifest at `:180-188`. Both declarations are 2, so they agree.
**`SEAT-COUNT FAIL` grep on the docker-smoke log of run 34322655506 (job 102372607889, 268 720 bytes):
zero occurrences.** Positive evidence the check ran: every episode logged `seats=2` and
`"num_agents": 2` in its resolved config, and the bc16 episode logged
`smoke OK: seats=2 results=1935B replay=26377B reason=complete`.

**7. Scripted baseline plays full episodes legally; parameters tuned, not guessed.**
Observed, with one qualification. Legality: `tests/test_bc16_baselines.nim:90-95` asserts
`World.refusedActions == 0` over whole games for both chassis — and that counter is real, because every
`do*` in `years/bc16/world.nim` re-checks its own `can*` and increments `refusedActions` on failure
(`:702-704, 741-743, 774-776, 863-865, 908-910, 941-943, 960-962`). It also asserts no robot exceeds its
`DecisionOps` budget and no friendly-fire attack ever
(`tests/test_bc16_baselines.nim` header items b, and `:90-95`). Natural end + `complete`:
`tests/test_bc16_replay.nim:89` `checkEq("the episode completed", r.reason, epComplete)` on a 500-round
one-game episode, and the docker-smoke bc16 episode logged `episode end reason: complete`.
`greenhorn` acts but does not compete (`:163-174`); `bulwark` beats `greenhorn` 6/6 (`:194-195`).
Qualification: I found **no committed grid-search harness** for bc16 (`ls tools/` and a repo-wide grep for
`grid` turn up none for any year). What exists instead is documented measurement: `docs/RULES-BC16.md:398-414`
records three chassis adjustments each with a before/after number ("6 dens across the six maps against 20
after"; "116 soldiers against 115"; "`huddle` and `split` produced byte-identical games"), the survival
gate's two measured tables (`tests/test_bc16_survival.nim:26-54`, with the caveats in F3/F4), and
`tests/test_bc16_knobs.nim:17-60`, which names every substituted statistic with its measured low→high
values. I read that as measurement-driven tuning rather than a grid harness; I could not verify a grid
harness existed and was discarded.

**8. LLM reply handling.**
Observed. `src/battlecode/decide.nim` is year-neutral and this run's edit to it is purely additive
(`git diff … -- src/battlecode/decide.nim`: four hunks, all a `yBc16` case arm, `Bc16Preamble` and the bc16
brief; 232 insertions, 1 deletion). Tolerant parse: `sheet.nim:201-203` caps at `MaxReplyBytes` on a rune
boundary and `sheet_common.nim` extracts the JSON object from surrounding prose (fence-tolerant, per the
`llm.nim` credential/extraction ladder). Retry exactly once: `decide.nim:1275` `while open.len > 0 and
attempt < 2`, with `deadlineMs = attempt1Ms` on attempt 0 and `retryMs` on attempt 1 (`:1293-1294`), and a
`doctrine_retry` event per failure (`:1346-1347`). Fall back to scripted and **record** it:
`decide.nim:1360-1369` re-seats the baseline sheet, sets `result.fallback[slot]` to one of
`no_credentials|throttled|parse`, emits a `doctrine_fallback` event, and echoes the phrase
`falling back` that phase 60 greps; the budget-exhaustion path does the same with cause `timeout`
(`:1284-1291`), and a no-credentials LLM seat is recorded as a fallback rather than as a scripted policy
(`:1265-1272`). `results.fallbacks` is a declared top-level results key
(`coworld_manifest_template.json` `results_schema.required` contains `fallbacks`), and docker-smoke asserts
`fallbacks == [0, 0]` on the scripted episodes.

**9. Rune-safe truncation.**
Observed. `sim_types.nim:334-346` `truncateRunes`/`truncateBytes` (unchanged this run) plus
`sanitizeLine` (`:363`). Every bc16 string that reaches the replay goes through one of them:
`notes` → `sanitizeLine(..., MaxNoteRunes=280)` and `motto` → `sanitizeLine(..., MaxMottoRunes=48)`
(`sheet.nim:194-195`); unknown keys → `truncateRunes(MaxUnknownFieldRunes=40)` (`sheet.nim:169`); the
provider's error text → `sanitizeLine(..., MaxFallbackDetailRunes=200)` (`decide.nim:1345`); the recorded
prompt → `truncateRunes(MaxPromptRunes=4000)` (`llm.nim:204`); the submitted sheet on the doctrine card →
`truncateRunes(120)` (`broadcast.nim:520`); the whole reply → `truncateBytes(16*1024)` (`sheet.nim:203`).
The bc16-specific test is `tests/test_bc16_sheet.nim:212-242`: 400 two-byte runes into `notes` and 200
**astral-plane** runes into `motto`, asserting `runeLen == 280` / `== 48`, `validateUtf8() == -1` on both,
`motto.toRunes().len == motto.runeLen`, and a 20 000-rune two-byte payload cut at the 16 KB **byte** cap
that still parses as strict UTF-8.

**10. Manifest validates.**
Observed by parsing `coworld_manifest_template.json`. `game.docs.readme` =
`{"type":"uri","value":".../README.md"}`; `game.docs.pages` has **ten** entries
(`rules.md, rules-bc20.md, rules-bc21.md, rules-bc24.md, rules-bc25.md, rules-bc23.md, rules-bc22.md,
rules-bc16.md, replay.md, parity.md`), every one an object with `id`, `title` and
`content: {type, value}` (checked programmatically: `all(... == {'type','value'})` → `True`).
`game.protocols` carries **both** `player` and `global`, each a `{"type":"uri", …}` pointing at
`docs/PROTOCOL.md`. `config_schema.additionalProperties: false`, `tokens` declared, `year.enum` appended to
eight values with `bc16` last, `maxRounds` widened to `{minimum: 50, maximum: 3000}` (coordinator ruling 5),
`end_reason` extended by exactly the three new values with `zombified`/`cleansed`/`resignation` absent.
`tests/test_manifest.nim:187-209, 219-252, 273-292` asserts all of this, including that
`config_schema.year.enum[0..6]` is unchanged so no existing index moved, and that no shipped variant's
`maxRounds` exceeds 2000. The design note's readme-shape line (design.md prose `{"readme":{"type":"text",…}}`)
differs from the checklist's `type: text` wording; the manifest ships `type: uri` for both `readme` and the
page contents, which is what the seven shipped years already ship and what
`validate_upload_manifest` accepts (`tests/test_manifest.nim` exercises the installed `coworld` CLI's own
validator). Not a bc16 change.

**11. Viewer legible at 360 px.**
Observed. `client/replay_broadcast.html:2580`
`#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` (inherited, unchanged). Word labels are
hidden under 640 px in five `@media (max-width: 640px)` blocks, and bc16's own is `:3824-3838`:
`#bc16-econ .lbl, #bc16-units .lbl { display: none; }`, `#bc16-archons .lost { display: none; }`,
`#bc16-horde .tl { display: none; }` — and the design's requirement that `#bc16-horde` **keeps** its wave
composition, outbreak multiplier and countdown at every width holds: only `.tl` (the mini-timeline) is
dropped, while `.wave`, `.ob` and `.togo` are not. `viewer_smoke.mjs --killfeed-overlap` measured client
rects at 360/720/1280 px at FIT and 2× zoom on all eight replays (`ci.yml:4109-4126`), and the largest
overlay over the board after the soak on the bc16 replay was `bc16-econ 5%` (wasm-viewer log line 2350),
well inside the 50 % gate.

**12. Release order and scaffold.**
Observed. All three workflows present: `.github/workflows/{ci.yml,coworld-release.yml,coworld-submit.yml}`.
`coworld-release.yml` step order: `Build the Coworld manifest` (`:168`) → `Certify locally` (`:182`) →
`Upload the policies` (`:225`) → `Upload the Coworld` (`:323`) → `Put the Coworld secret` (`:419`) —
build → certify → upload-policies → upload-coworld → secret put, in that order. The file is not in the
diff, so this is pre-existing and unchanged. `tools/ci/docker_smoke.sh` present and executable (`100755`).
`tools/ci/policies.json` has **32** entries, four per year; bc16's four are
`battlecode-bc16-bulwark` (`PLAYER_PROMPT`, label `bulwark`), `battlecode-bc16-pullers`
(`PLAYER_PROMPT`, label `pullers`, **carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`**),
`battlecode-bulwark` (`PLAYER_SCRIPTED=bulwark`) and `battlecode-greenhorn`
(`PLAYER_SCRIPTED=greenhorn`) — two LLM prompt champions plus two scripted fillers, all four
`run: /bin/battlecode-player`, `image: cogame-battlecode-player:latest` (the *player* service's image).
The placeholder gate exits 0: grepping the three names `battlecode` (as `<slug>`), `<IMAGE>`, `<SEATS>`
across `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`, `docker_smoke.sh` and `policies.json` returns
no `<…>` form. Surviving angle-bracket names are exactly the documented residue plus non-residue prose:
`<cow_id>`/`<sha>` (`ci.yml:3942`), `<run_id>` (`coworld-release.yml:21`), `<name>` (`coworld-submit.yml:31`),
and `<init>`/`<minimum>`/`<style>`/`<>` in Java/shell/HTML prose.

**13. Viewer executes.**
Observed, all four bullets.
(a) `wasm-viewer` is green on `main` at `fbc7d345` (job 102373769442, `conclusion: success`), it
`needs: docker-smoke` (`ci.yml:3952`), and the step
`Load the bundle in a real browser (ALL EIGHT years' replays)` (`ci.yml:4033`) **ran** — it is present, not
commented out, and carries no `continue-on-error` (the only `continue-on-error: true` in the file is
`ci.yml:842`, in `parity-oracle-bc20`'s engine-from-source tier). Log evidence for the bc16 replay:
`{"loaded":true,"ms":314,"clock":"0:22 GAME 1 OF 1 — RIVER doctrines","scorebug":"CLAN ASH Clan Ash ·
The wall holds. 65 … CLAN BASIL Clan Basil · The wall holds. 34","feed_lines":7}`, then
`scrub selector: #scrub`, `endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH`,
`largest overlay over the board after the soak: bc16-econ 5%`. It ran at `--timeout 120 --soak 15`
(`ci.yml:4109-4118`), as the design note pins.
(b) `replay-viewer/static_replay.js:180` sets `data-replay-loaded="true"` on `<html>` from the worker's
`loaded` message after the first board frame; `:14-20` sets `data-replay-error="<message>"` on `<html>` on
any failure. Both from the shell's own code paths.
(c) Playback opens at the game start by construction: this repo's replay has **no lobby records**.
`src/battlecode/replay.nim:270-277` builds one frame per round per game and nothing else;
`src/battlecode/broadcast.nim:1836-1838` emits `"st": 0`, `"lob": 0`, `"mx": max(1, totalFrames - 1)`, so
frame 0 *is* round 1 of game 0 and there is nothing to dwell through. There is no `gameStarts` array to
clamp to and no lobby-join timeout in this game's config.
(d) The link flags and the bootstrap agree and come from the same starter:
`grep MODULARIZE|EXPORT_NAME replay-viewer/config.nims` → **no match** (no `MODULARIZE` build), and
`replay-viewer/static_replay_worker.js:218` `Module.onRuntimeInitialized = function () { … }` — the
non-`MODULARIZE` bootstrap. `config.nims` is not in the diff. The smoke's `loaded: true` on all eight
replays is the evidence, per the checklist.

**14. Chrome is the starter's, not a lookalike.**
Observed, with F1 as the one defect.
- `client/chrome_common.js` and `client/broadcast_core.js` are **not touched by this run**: the only
  `client/` file in `git diff --name-only 00c1dae..fbc7d345` is `replay_broadcast.html`.
  `tests/test_viewer.nim:31-36` asserts both files' sha256 against the starter's copies and is green in CI.
  (I note the local `/workspace/starters/coworld-ctf/client/chrome_common.js` differs by sha from the
  repo's copy, but this run's starter is `cogame-battlecode` itself and the repo's own pinned assertion is
  the authority here; the difference predates `00c1dae`.)
- `client/replay_broadcast.html` is the existing page **appended to**: 648 insertions against **4**
  deletions, and all four deletions are list/guard extensions (the `data-year` noun table's last row
  gaining a comma, the `--statrail` id list, and the `if (!isBc20 && …)` guard twice). The bc16 block is
  introduced under the banner comment `<!-- BC16 additions to the inherited cogame-battlecode chrome -->`
  (`:3989`) and `client/replay_broadcast.html:3619-3624` records the removal-by-CSS convention. Sections
  1–5 of the inherited CSS are untouched (no deletions above the bc16 block).
- Transport rules: (a) `relayout()` (`:6830-6860`) sets `--hudscale`, `--topband`, `--band` **and**
  `--statrail` on `document.documentElement.style` inside a three-pass fixed point, and the measured id
  list now names `bc16-econ` and `bc16-units` (`:6849`) beside the thirteen already there.
  (b) Nothing bc16 sits inside the band: `#bc16-econ { bottom: calc(var(--band, 0px) + 8px) }` and
  `#bc16-units { bottom: calc(var(--band, 0px) + 76px) }` (`:3733-3734`); `#bc16-archons`/`#bc16-horde`
  are top-band pills at `top: calc(var(--topband, 0px) + …)` (`:3684`, `:3710`); `#bc16-doctrines`'s
  `max-height` subtracts both bands (`:3762-3763`).
  (c) `#endcard { … bottom: var(--band, 0px) }` (`:1857`), raised with `.on` — the class its own rule uses
  (`:1878`, `:6823`) — and **every** seek takes it down: `seek()` calls `dismissEndcard()` (`:6515`),
  transport buttons at `:6876` and keyboard keys at `:6904` do the same, and the bc16 beat buttons route
  through `api.seek()` (`:5724`). **F1 is the exception within this bullet**: bc16's own
  HUD-suppression rule is keyed on a class that is never set and on the wrong sibling direction.
  (d) Scrubber beats are labelled `<button>`s with `aria-label` and `title` that seek to their tick, built
  by `buildBc16BeatButtons` (`:5706-5727`) — its own name, not `markBeat`, not `buildBeatButtons` — with
  `applyBc16BeatSpoilers` (`:5729-5735`) honouring the spoiler gate. CSS exists for all **thirteen** kinds,
  every rule scoped `html[data-year="bc16"]` (`:3810-3822`), and `tests/test_bc16_beats.nim:63-80,200+`
  asserts ≥26 beats over exactly 13 distinct kinds from the committed fixture **and** a
  `html[data-year="bc16"] .beat-marker.<kind>` rule for every kind the fixture actually emitted. I counted
  the fixture's events independently: 179 events over 16 event kinds mapping to 13 beat kinds.
- `#viewpanel` is **kept**, which is what the design note decides (design.md:1861-1872) on the ground that
  the played pool spans 36×30 to 45×45 at 16 px/square — 480–1280 px against a 360 px frame. Consistent
  with the checklist's "keep it only when the design note says the board is larger than the viewport".

**15. Every drawn string fits its frame.**
Partially covered; see **F2** for the gap.
- `tools/ci/viewer_smoke.mjs` reports `canvas_text: {total, outside, never_inside, ellipsized}`
  (`:118-124`, `:439-441`, `:896`). Measured on all eight replays including bc16:
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`
  (wasm-viewer log lines 2233, 2253, 2271, 2285, 2299, 2313, 2327, **2341** = bc16). `total: 0` means the
  check covered nothing on this renderer, which the design note states outright (design.md:1912-1914) and
  which the checklist says is not evidence of anything. `--strict-text-bounds` is deliberately dropped on
  the replay runs (`ci.yml:4084-4090`) because `#viewpanel` is kept and the board is pannable — the exact
  case the flag excludes.
- The substitute gate exists and runs: `ci.yml:4253` `Render the full-cap doctrine-text fixture`, serving
  `tools/ci/renderer_fixture.html` with the page's own CSS extracted at run time
  (`page_styles.css: 190675 bytes from 1 <style> block(s)` in the log) and driven by
  `viewer_smoke.mjs --strict-text-bounds`. Its real assertions are DOM measurements, not canvas text:
  the doctrine panel may not take half the frame, both `.plate-sub` mottos must still be at the 48-rune
  cap, and both `.dline i` notes must still be byte-identical to the full-cap string
  (`tools/ci/renderer_fixture.html:640-690`) — i.e. it does assert its own strings are still full length,
  as the checklist requires.
- **The gap (F2): that fixture has no bc16 row** (`:70`), so it never lays out `#bc16-doctrines-body`,
  which is the element that draws bc16's 280-rune `notes`, 48-rune `motto` and 120-rune submitted sheet.
  bc16's reserved band exists in CSS (`#bc16-doctrines` is capped-and-scrolling at
  `max-height: min(46vh, calc(100% - var(--topband) - var(--band) - 46px))`, `:3762-3764`, with a dismiss
  control at `:3770-3775` and a re-open chip at `:3893`), and `tests/test_viewer.nim` asserts those
  statically — but no gate ever renders it with model-length text.

**The simultaneous-decision batch rule.**
This game **is** a simultaneous-decision game, and the design note says so in as many words:
design.md:806-811 — "**One decision turn, one parallel batch.** Both seats are asked at the same moment and
their two provider calls go out as **ONE parallel batch** (`curly.makeRequests`, `decide.nim`'s existing
shape) with the same deadline; seats are **never** queried one after another" — and design.md:657-659 —
"There is exactly **one** decision turn per episode, so the 'per-turn wall-clock budget' is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch**."
Observed in code: `src/battlecode/decide.nim:1295-1312` builds a single `RequestBatch`, `batch.post(...)`
once per open slot, and issues **one** `client.curl.makeRequests(batch, …)` call with a single deadline;
the per-slot responses are read out of `responses[position]` afterwards (`:1315-1350`). There is no
sequential call site. The retry (`:1275`, at most one) re-batches the still-open slots the same way. At
most 2 provider calls per seat per episode. **No sequential-call finding.**

---

## Traced and consistent

- `src/battlecode/years/bc16/rules.nim:341-425` — the numbered resolution order against design.md §"The 2016
  rule set — exact numbered resolution rules" (design.md:429-591), step by step: `currentRound += 1` from
  −1 (`:344`, world initialised at `world.nim:1081` `currentRound: -1`); rules 1b/1c not ported as genuine
  no-ops (D1, `:345`); a **snapshot** of the insertion-ordered exec list taken before the sweep with an
  existence guard (`:364-366`), so a robot built this round takes no turn and one destroyed mid-sweep is
  skipped; `processBeginningOfTurn` decrements both delays, zeroes `repairCount`/both signal counters and
  resets the budget to 0 for a robot that cannot execute code (`:287-296`); the controller (`:152-186`) with
  zombies and dens running the ported provider and neutrals doing nothing; ops recorded as telemetry only;
  `processEndOfTurn` gated on `health > 0` doing `roundsAlive += 1` then the infection tick (`:298-306`,
  `:370-371`); the disintegrate suicide **after** `processEndOfTurn` (`:375-376`); rule 4a not ported;
  parts income A then B (`:379`, `economy.nim addPartsIncome`); the end-of-match ladder (`:204-234`);
  `running = false` only once a winner is set.
- `years/bc16/rules.nim:216-234` — the four-rung ladder in the engine's order on **exact float64
  differences**: archon count, then `archonHealthTotal` difference, then `partsNetWorthDiff`, then
  `highestArchonId` with the `else` branch awarding **B** on a 0–0 tie (`world.nim:1014-1021`);
  `setWinnerIfNonzero` is `n > 0 → A`, `n < 0 → B`, returning `n != 0` (`:197-202`). Rung 3 is seeded with
  the parts difference and walks every live robot **once** in insertion order
  (`world.nim:1001-1012`), so neutrals and zombies contribute nothing and a den/zombie's `partCost` is 0.
- `years/bc16/rules.nim:240-281` — the scoring formula against design.md:706-747: `share` returns
  `0.5'f32` on a 0–0 total; archon health narrowed to **tenths** and parts worth truncated to an integer
  before the shares; each share taken in **float32**; the weighted sum `64/24/12` truncated by the `int()`
  cast. `winBonusFor` adds `yBc16` to the 200 set (`match.nim:617-624`).
  `results.scores[t] = 200 * wins + mean(points)` via the year-neutral `scoresFor`.
- `years/bc16/world.nim:595-655` — `visitDeathSignal` in the engine's order: early return when `!running`;
  counts decremented, then the player-archon `count == 0 and not hasWinner → setWinner(opponent,
  DESTROYED)` **mid-turn** with `running` untouched (`setWinner` at `:545-550` deliberately does not clear
  `running`); the rubble deposit only when the cause is not `ACTIVATION` **and** the robot is not infected;
  removal from the exec list **by value** (`:630-633`); the infected → `turnsInto` zombie spawn on
  `Team.ZOMBIE` at `maxHealth(currentRound)` (`:650-651`). `health.nim deathConsequence` makes the two
  outcomes exclusive by construction.
- `years/bc16/world.nim:690-980` — all eleven actions with their preconditions and effect order:
  `clearRubble` returning silently and free on a 0 square (`:707-709`); `move`'s `factor1` diagonal on the
  **core only** and `factor3` rubble doubling on both, with the archon parts pickup on arrival
  (`:744-754`); `attack` doing the signal **first** then `activateAttack` (`:764-840`), with splash radius
  zero, no vision/team/on-map test, the guard 2.0 rate, the guard `damage - 4` above 10.0 strictly, the
  200-part den bounty on `health <= 0`; `build` deducting then spawning then
  `activateCoreAction(buildTurns, buildTurns)` with a den skipping pathability (`canBuild` at `:842-855`);
  `activate` killing with `dcActivation` and spawning at `buildDelay 0` for `weapon up-to 0 / core += 2`
  (`:902-923`); `repair` costing **no delay at all** and capped at one per turn (`:925-953`);
  `pack`/`unpack` with **no readiness check** and +10 on both counters (`:955-972`).
- `years/bc16/delays.nim:70-96` — the asymmetric pairing:
  `activateCoreAction` = `setWeaponDelayUpTo(a); addCoreDelay(m)` and
  `activateAttack` = `addWeaponDelay(a); setCoreDelayUpTo(m)`, opposite in both axes;
  readiness strictly `< 1.0` on a float64; `decrementDelays` subtracting exactly 1.0 and flooring each
  counter separately. `engineDecrement` (`:98-104`) carries the engine's whole formula and **no rule calls
  it** — verified by grep: its only callers are `tests/table_bc16_delay.nim` and `tools/JavaBc16Tables.java`'s
  counterpart. `table_bc16_delay: ok (21 checks)` in CI. Coordinator ruling 1 verified:
  `DecisionOpsWide = 2000`, `DecisionOpsStandard = 1000` (`years/bc16/constants.nim:110-111`),
  `budgetFor` = wide for ARCHON/SCOUT else standard (`units.nim:282-287`), `opsLeft = 0` when
  `not canExecuteCode()` (`rules.nim:295`), `PinnedDecrement = 1.0` (`delays.nim:60`), tabled in
  `docs/RULES-BC16.md` §Divergences items 1–2 and gated by the parity job's bytecode-headroom check
  (`ci.yml:3085-3090`, measured peaks 0 % and 2 %).
- `years/bc16/zombies.nim:41-165` — the verbatim provider: the den's three steps with the second
  `spawnAllPossible` only when a queue remains (`:78-95`); the ring
  `MoveDirs[((start + i*chir) mod 8 + 8) mod 8]` over `dirOffset 0..7` (`:66-69`); `nextQueuedType`
  reproducing the **no-`break`** loop so the priority is BIG → FAST → RANGED → STANDARD (`:52-59`);
  `processZombie`'s eight steps with every early return, and the two RNG draws exactly where D2c puts them
  — `zombieRand.nextInt(8)` **only** when `closest == nil` (`:117-120`) and `zombieRand.nextBoolean()`
  **only** past the attack, readiness and preferred-move branches (`:122`). `getNearestPlayerControlled`
  (`world.nim:505-530`) walks insertion order, keeps only `isPlayer()`, collects **every** location at the
  minimum and draws `rand.nextInt(closest.len)` **on every call including len 1**. All of this is confirmed
  bit-exact against the JVM for 18 whole games (parity job, ledger empty).
- `years/bc16/units.nim` — the twelve-row table's eight derived predicates, the outbreak ladder applied at
  spawn only (`:305-317`), `rubbleAfterClear`, `rubbleBlocks` at 100, `rubbleSlows` at 50, `moveFactor1`
  diagonal 1.4, `guardRate`, `damageToTarget`, `rubbleFactorFor` and `broadcastDelayIncrease`. Two places
  where the code **corrects** the design note and documents doing so, each measured against the JVM's own
  table: `economy.nim incomeFor` records `2.0 - 0.01*137 = 0.6299999999999999`, not the note's `0.63`; and
  `units.nim:361-367` records `145 * (1.0/3.0) = 48.33333333333333`, not the note's `48.333333333333336`.
  `docs/RULES-BC16.md` §"Corrections to the design note" carries both. `test_bc16_arith: ok (138 checks)`.
- `src/battlecode/match.nim:218-524` — the bc16 event vocabulary, all additive, with the three
  name-colliding kinds year-tested: `archon_lost` (bc22 `gold_dropped` vs bc16 `cause`, `:221-233`),
  `first_action` (`:347`, using `Bc16ActionNames`), `rout` (`:381-390`). `first_action`'s field is
  **`action`**, never `kind` (`:349-352`), as the bc23 r1-F25 lesson requires.
- Event bounds: `world.nim:263-269` `BeatBounds` matches the design's per-game table item for item
  (game_start 1, first_action 2, unit_milestone 10, zombie_wave 30, outbreak 10, den_destroyed 12,
  neutral_activated 20, infection 20, turned 24, archon_lost 8, rout 20, duel 20, tiebreak 1,
  game_end/abandoned 2), the counter is per `World` and a `World` is created per game
  (`rules.nim:528`), and `tests/test_bc16_replay.nim:163-196` asserts every kind against its bound on a
  real 3000-round match plus "the event list is small" (< 700).
- `coworld_manifest_template.json` — every edit is additive except the one named non-append edit,
  `config_schema.maxRounds.maximum` 2000 → 3000, which `tests/test_manifest.nim:195-209` asserts together
  with "no shipped variant's maxRounds moved" (`<= 2000` for all seven). Coordinator ruling 5 verified.
  `player[]` is unchanged at `[awu, scaffold]` (only the two `description` strings extended to name the
  bc16 resolution, asserted at `tests/test_manifest.nim:290-292`), and the certification fixture is
  unchanged on `bc26`.
- `src/battlecode/sim_types.nim` — `GameVersion` `"GV10"` → `"GV11"` with a **prepended** changelog entry
  (`:22-45`) and `ReplayCompatibleGameVersions` **extended** to
  `["GV04","GV05","GV06","GV07","GV08","GV09","GV10", GameVersion]` (`:220-221`), never reset — coordinator
  ruling 2's first half verified. `ScriptedChassis` gains `scBulwark`/`scGreenhorn` (`:269-270`).
- `src/battlecode/rng.nim:133-141` — one **optional** parameter added
  (`initIdGenerator(seed, firstBlock = MinId)`) because 2016's `IDGenerator` starts its block at 0 and mints
  ids from 1; every existing call site keeps the default, so no other year's id stream moves. Disclosed in
  `docs/RULES-BC16.md:386-390` and in `NOTICE`. `test_determinism: ok` and every sibling year's shards green.
- `years/bc16/maps.nim` — `drawMaps` picks `count` **distinct** maps by successive LCG indices with
  `remaining.delete(pick)`, reproducibly (`tests/test_bc16_maps.nim:201-205`), and
  `tests/test_bc16_maps.nim:214-219` pins the docker-smoke seed `2016004` to draw exactly `river`, which
  the CI log confirms (`"seed": 2016004` in the resolved config, `RIVER` in the viewer clock).
  `test_bc16_maps: ok (841 checks)`.
- `NOTICE` — coordinator ruling 6 verified. Four sections added (`NOTICE:597-731`): the GPL-3.0 engine at
  `11a0b09f` with derived files named individually (including `zombies.nim` called out as "the one module
  that is a near-literal reproduction" and the `health.nim`/`world.nim` split recorded); the GPL-3.0 client
  at `317e1f3f` with the 49-sprite atlas credited by directory and file family; the CI-only jar pinned by
  URL, size (6 563 607) and sha256; and `TheDuck314/battlecode2016` + `bshimanuki/battlecode2016` named as
  **not cloned, not read, not copied, not vendored, not compiled, not translated**. The GPL-3.0 §13 /
  AGPL-3.0 reasoning is stated explicitly. `data/atlas_bc16.png` is 27 538 bytes of cut sprites from the
  credited tree; I found no asset or code in the diff whose provenance is uncredited. The chassis-path
  pointer list in `NOTICE:722-724` names twelve `chassis/*.nim` plus `greenhorn.nim`; `scenario16.nim` is
  named in `docs/RULES-BC16.md:28` but not in `NOTICE` — the layout rule (design.md:1116-1121) is otherwise
  satisfied.
- `docs/RULES-BC16.md` — 441 lines: the year's rules, the eleven knobs, and a §Divergences list of 20 items
  covering V1–V8, D1–D5, the `health.nim`/`world.nim` split (item 14), the survival ratio (item 16), the
  chassis's use of the public den roster (item 17), `rng.nim`'s parameter (item 18), the
  `dispatch.currentRound` normalisation (item 19) and the three measured chassis adjustments (item 20),
  plus a §"Corrections to the design note" section. `docs/PARITY.md` gains 351 lines including the honest
  "Tier A′ — NOT IMPLEMENTED" section (F5) and a "What is NOT compared, and why" list.
- `docker-smoke` bc16 episode (job 102372607889): `SMOKE_EXPECT_YEAR=bc16`, `maxRounds: 900`, seed 2016004,
  no `ANTHROPIC_API_KEY`, `all 2 player containers exited 0`, `reason=complete`, per-seat
  `SMOKE_REQUIRE_STATS` satisfied for `units_built`/`damage_dealt`/`parts_collected_tenths`, and the
  across-the-pair `jq` assertions all passed with margin:
  `units=147 damage=11543 guards=7 infections=70 turned=18 zombie-damage=4150 zombies=54 outbreak=2`
  against floors 80/4000/3/20/6/1500/25/2. The floors are read from the **replay's** `result` block, not
  from `dist/smoke/results.json` (the bc24 fix), and the `robots_turned >= 6` and `guards_built >= 3`
  assertions the design note forbids dropping are both present (`ci.yml:2955-2985`).
- `tests/test_bc16_knobs.nim` — the knob-teeth gate: 68 paired games, the anti-inert clause applied to
  **every** game of the sweep (`:118-127`: both seats ≥10 units and ≥500 damage) and `refusedActions == 0`
  per game (`:136`, `:148`). Six of the design's asserted statistics are not recorded by this sim and each
  substitution is named in the header with its measured low→high values (`:17-60`), including one where the
  measured sign is the **opposite** of the note's expectation (`zombie_kiting`'s damage term) and one where
  the note's statistic measured 17→17 for a reason the header explains. `test_bc16_knobs: ok (113 checks)`.
  This is a documented divergence from design.md:2469-2484, not a silent one.
- `tests/test_bc16_perf.nim` — asserts the 130 s budget in `-d:release` only, with the repo's own precedent
  (`tests/test_bc21_perf.nim`) and the reason in the header; the debug pass plays the same game to the same
  round count with every other assertion live. Measured: 977 rounds on `6147` in 0.118 s release / 1.598 s
  debug. The design's "full 3000-round game" is not what runs, because the game ends on its own ladder at
  977; the test asserts `roundsPlayed >= 400` instead and says so.

---

## Could not determine

- **Whether the F1 bleed-through is visible to a human at any width.** I read the CSS, the class the JS
  sets, the DOM order and the z-indexes, and the rule provably cannot match; the *visual* severity depends
  on the endcard gradient's alpha over each box and I did not render the page. What would settle it: a
  screenshot of the bc16 replay at the 100 % seek at 360 px and 1280 px with `#bc16-econ`/`#bc16-archons`
  populated — or simply `getComputedStyle(document.getElementById('bc16-econ')).visibility` after
  `#endcard` is raised.
- **Whether bc16's doctrine card holds a full-cap `notes` and `motto` at 360 px without clipping or
  overflow** (F2). The CSS caps and scrolls it, and the static assertions in `tests/test_viewer.nim` pass,
  but nothing renders it with 280-rune/48-rune strings. What would settle it: a `bc16` entry in
  `tools/ci/renderer_fixture.html`'s `YEARS` array, which makes the existing `--strict-text-bounds` step
  measure it at 360/720/1280 px and assert the strings are still full length.
- **Whether the survival gate's units/damage/median floors were chosen knowing they sit below the broken
  control** (F3). The test's own comments quote the broken values next to the floors, which reads as
  deliberate, but "deliberate" is not the same as "discriminating". What would settle it: a run of the
  healthy gate with only those three clauses active against the broken build — or, more usefully, floors
  set between the two columns.
- **Whether the packed hash-chain fields (F7) ever actually collide in a shipped episode.** I established
  the field widths and that per-type censuses above 99 are plausible from CI's own peak-robot numbers, but
  I did not instrument a game to find a collision. What would settle it: logging the per-type maxima across
  the survival gate's six 3000-round mirrors, or replacing the packing with separate `mixHash` calls and
  checking the committed fixtures' chains change (they would, which is why this is advisory and not a
  fix-now item).
- **Whether the rungs below `DESTROYED` (`more_archon_health`, `more_parts_net_worth`, `highest_id`) match
  the Java engine.** They are unit-tested on the Nim side (`tests/test_bc16_endladder.nim: ok (48 checks)`)
  but no oracle bot reaches them, and `docs/PARITY.md:1873-1875` says so. What would settle it: the four
  Tier A′ scenario bots (F5), or a `bc16scenariotie`-shaped bot on both sides.
- **Whether `mixHash`'s `uint64(v and 0xFFFFFFFF)` is well-defined on wasm32** where `int` is 32 bits — the
  sibling `mixHashU` carries a comment saying masking into an `int` first raises `RangeDefect` in the
  browser, yet `mixHash` (`world.nim:298-300`) and `fnv1a64` (`:309-312`) do exactly that. I could not
  build for wasm here. Empirically it works: the `wasm-viewer` job re-derived both bc16 recordings with
  `mismatch_round: -1`, which cannot happen if the chain raised or diverged. What would settle it beyond
  that: reading the emitted C for the wasm target, or a deliberate `RangeDefect` probe.
- **Whether `docker_smoke.sh`'s `SMOKE_SEATS` default (`2`, at `:82`) is the `<SEATS>` substitution or a
  coincidence.** The comment at `:176-180` says it is substituted at scaffold time, the value agrees with
  the manifest, and the file is not touched by this run, so the invariant holds either way. What would
  settle the provenance: the templates repo's own `docker_smoke.sh`.
