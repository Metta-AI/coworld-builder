blocking: 0

# r1 verdict — battlecode-2016 (bc16)
Head: 46b92ae5ff9a78be61c659f4a2eff861aa17b838   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Reviewed range `00c1dae..46b92ae5` (phase-20 build `00c1dae..fbc7d345` + fix set `fbc7d345..46b92ae5`,
10 commits, merged as PR #11). I cloned the repo fresh, read the design note once in full, formed my
own read of the tree and the CI logs, and only then read `r1-review.md` and `r1-fixes.md`. The review
file is a coordinator reconstruction (its header says so); I treated its finding identities/anchors as
claims to reproduce from the pre-fix tree `fbc7d345`, not as evidence the reviewer looked at anything.

**Item-14 baseline reading, noted for the coordinator:** this is a mod run, so "the starter's chrome"
means the inherited page at `00c1dae`, not `/workspace/starters/`. I diffed `client/chrome_common.js`,
`client/broadcast_core.js` and `client/replay_broadcast.html` against `git show 00c1dae:<path>`.

## Standing blocking findings

None. Every finding I could reproduce at `fbc7d345` is fixed at the current head, and my independent
checklist pass found no item falsified at `46b92ae5`.

## Findings F1–F11

### F1 — dead endcard-suppression rule → UPHELD, fixed at head (moot)
- Reproduced pre-fix: `git show fbc7d345:client/replay_broadcast.html:3793-3797` reads
  `html[data-year="bc16"] #endcard.show ~ #bc16-archons, …` — dead twice (the page toggles `.on`:
  `#endcard.on { display: flex; …}` at head line 1878, `classList.add('on')`; and `~` selects
  following siblings while the bc16 boxes precede `#endcard`).
- At head: `client/replay_broadcast.html:3845-3849` is
  `html[data-year="bc16"] #chrome:has(#endcard.on) #bc16-archons, …` — keyed on the class the page
  sets, parent-scoped. `tests/test_viewer.nim:505-525` refuses `#endcard.show` in any selector shape
  and pins the live shape (`:1518-1520`); `tools/ci/renderer_fixture.html:78-81` carries
  `SUPPRESSED_BY_ENDCARD.bc16` (all five boxes) as a computed-style check.

### F2 — renderer fixture had no bc16 row (item 15) → UPHELD, fixed at head (moot)
- Reproduced pre-fix: `git show fbc7d345:tools/ci/renderer_fixture.html:70` —
  `var YEARS = ['bc26','bc20','bc21','bc24','bc25','bc23','bc22'];` — no bc16, so the only gate that
  lays out LLM-authored text at cap never rendered anything bc16 draws. This falsified item 15.
- At head: `tools/ci/renderer_fixture.html:72` includes `'bc16'`; the fixture asserts its own strings
  are still full-length (`:830-853`: `runes(...).length !== MAX_NOTE_RUNES/MAX_MOTTO_RUNES` fails the
  page — the "quietly shortened remark" trap closed); the ci.yml step serves it over HTTP and drives
  it with `viewer_smoke.mjs --strict-text-bounds` (run 34346628919, wasm-viewer log 12:42:33-35Z,
  `{"loaded":true,…}` with no `data-replay-error`).

### F3 — survival floors mislabelled as discriminating → UPHELD, fixed at head (moot)
- At head `tests/test_bc16_survival.nim:80-125` carries the clause table naming which clauses
  discriminate (2-of-6 ratio, guards, dens, swamp pair-parts — each a hard zero on the control) and
  which are anti-degeneracy floors the control clears (units 55>25, damage 3333>1500, income; median
  inside the control's noise band 873/1029 vs 1000). No floor moved — verified: `MinUnitsBuilt = 25`,
  `MinDamageDealt = 1500`, `MinMedianRounds = 1000` unchanged in the constants block.

### F4 — stale measurement tables → UPHELD, fixed at head (moot)
- At head the test header (`tests/test_bc16_survival.nim:17-31`) cites run 34322655506 / test job
  102372608026 and carries the regenerated healthy (3 of 6, 14 dens, median 2015) and broken
  (0 of 6, 0 guards, median 873) tables, plus the previous stale numbers on the record. Same tables
  in `docs/RULES-BC16.md` §Divergences (~line 369-378).

### F5 — CI summary named Tier A′ as run → UPHELD, fixed at head (moot)
- At head `tools/ci/parity_tiers_bc16.py:464-473` states "Tier A′ (the four scenario bots) was NOT
  BUILT and did not run"; column reads `tier A / A″`; `docs/PARITY.md:1898` carries
  "Tier A′ — NOT IMPLEMENTED". Strings only; comparator untouched.

### F6 — parity floor substitution vs design note → UPHELD (ruled no code change), documented (moot)
- At head `docs/PARITY.md:1815-1830` records the divergence from design.md:2574 (per-game round floor
  250 not 2900, with measured bot lifetimes 298–683 / 485–1424 as the reason; zombie floor 150 summed
  `zombies_peak` over eighteen pairs, measured 735) and the three extra floors the job adds.

### F7 — hash-chain census packing could collide → UPHELD, fixed at head (moot)
- Reproduced pre-fix: `git show fbc7d345:src/battlecode/years/bc16/rules.nim` (~:394-400) packed six
  type censuses base-100/10⁴/10⁶ into two `mixHash` calls; peaks of 104–212 robots make ≥100 counts
  real, not hypothetical.
- At head `rules.nim:393-413+`: every census its own `mixHash` call. `tests/fixtures/replay-bc16.json`
  re-recorded at GV11, and `tests/test_bc16_replay.nim:271-292` ADDS a re-derivation of the committed
  fixture to its LAST round (closing the 200-frame gap of `wasm_replay_smoke.cjs`). Year-neutral
  `match.nim` packing deliberately untouched (out of scope, carried forward by decision).

### F8 — `dfNone` reported as `more_archons` → UPHELD, fixed at head (moot)
- Reproduced pre-fix: `git show fbc7d345:.../rules.nim:433` — `of dfNone: $dfPwned`.
- At head `rules.nim:442-456`: `endReasonFor` raises a Defect naming the state on `dfNone` instead of
  mislabelling; exported; tested in `tests/test_bc16_endladder.nim`.

### F9 — THE HORDE never drawn; `.struck` dead → UPHELD, fixed at head (moot)
- Reproduced pre-fix: `git show fbc7d345:client/replay_broadcast.html | grep -c 'class="horde">THE
  HORDE'` → 0.
- At head `:5876-5878` renderHorde draws `<span class="horde">THE HORDE</span>`; `:5836-5845`
  `hordeStrike()` wires `.struck` from the last `wave`/`turned` beat with that beat's own label,
  cleared after 2000 ms; `#bc16-horde.struck` (`:3749-3751`) sets `white-space: normal`.

### F10 — deleted `GameVersion == "GV10"` literal → DISMISSED as a loosening (ruling verified correct)
- The diff `00c1dae..46b92ae5 -- tests/test_bc22_replay.nim` deletes
  `checkEq("the game version is GV10", r.doc.gameVersion, "GV10")` and keeps
  `checkEq("and it is what the build claims", r.doc.gameVersion, GameVersion)` while ADDING three
  checks (real headline, in `ReplayCompatibleGameVersions`, list length ≥ 8 with GV04 kept). The
  deleted literal asserted no bump may ever happen; the authorised GV10→GV11 bump (rail decision 2)
  makes it unsatisfiable by construction. The `game_version == GameVersion` assertion was NOT
  weakened, skipped or gated. Not a loosening; item 1's second half unharmed.

### F11 — bc23 tolerant end-reason edit unapplied → UPHELD, fixed at head (moot)
- At head commit `95ef6c9`: `recordAndDerive` returns `EpisodeReason`; the timed block asserts
  `episodeReason in [epDeadline, epComplete]` (bc22's enum-level shape) alongside the document-level
  string check plus a `checkEq` the two agree — three assertions where there were two. Verified by
  reading the hunk; nothing removed except the tuple-shape reflow.

Upheld: F1, F2, F3, F4, F5, F6, F7, F8, F9, F11 (all fixed at head → zero standing).
Dismissed: F10 (correctly ruled not a loosening). Standing at head: none.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 CI green, no test loosened | **PASS** | Run 34346628919 on `main` @ `46b92ae5`: `{"attempt":2,"conclusion":"success"}`, 11/11 jobs green (`gh api …/runs/34346628919/jobs`: test 102467556370, docker-smoke 102467508896, wasm-viewer 102467507789, parity-oracle + 7 per-year, all `success`). **Rerun history judged acceptable**: attempt 1's only failure was `wasm-viewer` dying in `Build the static replay viewer bundle` on a truncated Nim 2.2.4 toolchain download (`tar xf nim.tar.gz` exit 2 after nimby's retries) — infrastructure inside the docker build, not this tree; the identical tree `95ef6c90` passed the identical job on branch run 34338896940 (`conclusion: success`, verified myself); `gh run rerun --failed` preserved the run id and attempt 2 is green at the same sha. No test result was manufactured by the rerun — the failing step never reached any test. **No test loosened**: I read every `tests/` hunk in `git diff 00c1dae..46b92ae5 -- tests/` — all deletions are seven→eight-year list/count updates (year enum, 28→32 policies, 9→10 pages, maxRounds 2000→3000 assertion widened to the authorised bound), the GV10 literal (F10, ruled above), the `#endcard.show {` grep replaced by a stricter whole-CSS refusal, and the F11 tuple reflow. No `skip`/`xfail`/`when false` added (the one "SKIP" echo in `test_bc16_survival.nim` is followed by `check(…, false)` — it FAILS, not skips). `ci.yml`'s removed lines are all SEVEN→EIGHT renames; test-job `timeout-minutes` 130→150 is authorised cross-year edit (decision 7). |
| 2 Replay re-derivation | **PASS** | `tests/test_bc16_replay.nim:84-90` (`deriver.mismatchRound == -1` on a recorded match), `:198-210` (record→re-derive for every bc16 end reason), `:271-292` (committed fixture re-derived to its LAST round). Viewer derives from the same wasm re-derivation (`replay-viewer/bc_replay` exports `bc_mismatch_round`); wasm smoke on the bc16 fixture: `{"loaded":true,"game_version":"GV11",…,"mismatch_round":-1}` (wasm-viewer log 12:42:33Z). |
| 3 Static viewer | **PASS** | `coworld_manifest_template.json:14` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present; the only `/client/replay` mention in the repo is `coworld-release.yml:220`'s guard REFUSING a pod-served viewer; `static_replay.js:205-211` reads the replay URL from the fragment/query (S3), contacts nothing else. |
| 4 Both name spaces | **PASS** | Agents: `decide.nim:743-744` sends `alias`/`opponent_alias` only (AliasA/B = "Clan Ash"/"Clan Basil", `sim_types.nim:240-241`, unchanged — rail decision 4 honoured; THE HORDE is spectator-side only, `replay_broadcast.html:5876-5878`). Viewer: `replay_broadcast.html:6650,6892,6927` draw `s.names[slot]` (real names) beside aliases. |
| 5 Degrade-never-hang | **PASS** | `episode_timeout_minutes: 20` (manifest:9) → 1200 s, 60 % = 720 s. bc16 variant: connect 25 000 ms + doctrine 45 000 ms (attempt1 20 000 + retry 12 000, `while open.len > 0 and attempt < 2` with a hard `budget` monotime check, `decide.nim:1274-1294`) + match 360 s (`match.nim:558-568` monotonic guard, per-game clamp) + ~30 s write/grace = 465 s ≤ 720 s. The provider batch deadline is handed to CURLOPT_TIMEOUT (`decide.nim:1309-1312`). No unbounded wait found on the decision or match path. |
| 6 num_agents | **PASS** | `num_agents: 2` inside all eight variants' `game_config` and absent at every variant top level (parsed the manifest myself); `certification.game_config.num_agents = 2`, `certification.players` = [awu, scaffold]. `tools/ci/docker_smoke.sh:141-227` enforces presence (:148), positive integer (:158), `len(certification.players)==seats` (:166), `len(certification.game_config.players)==seats` (:173), and SMOKE_SEATS agreement as the independent second declaration (:183), each exiting non-zero with `SEAT-COUNT FAIL:`. Grep of the full docker-smoke log (job 102467508896, 3177 lines): **0 occurrences of `SEAT-COUNT FAIL`**; all eight episodes `reason=complete`, `seats=2`. |
| 7 Scripted baseline full legal episodes | **PASS** | `tests/test_bc16_replay.nim:61,89`: a full scripted `playMatch` asserts `r.reason == epComplete`. Legality: `tests/test_bc16_baselines.nim:59-97` audits `World.refusedActions` over real games — `checkEq(mapName & ": NO chassis emits an illegal order", worst, 0)` — plus the no-friendly-fire counter. Tuning is measured, not guessed: the knob-teeth sweep (`tests/test_bc16_knobs.nim`, 66 paired games with a threshold table) and the survival gate's inline measured tables from run 34322655506. docker-smoke's bc16 episode: units=147 damage=11543 guards=7 turned=18 zombies=54 outbreak=2 across the pair (log 11:42:53Z). |
| 8 LLM reply handling | **PASS** | `sheet.nim:197-204` `parseReply` runs `extractJsonObject` on the capped text (tolerant of surrounding prose/fences); retry is exactly once (`attempt < 2`, `decide.nim:1275`; retry logged "will retry" at :1349); fallback recorded per seat (`result.fallback[slot]`, `doctrine_fallback` events with cause, `results.nim:78,97` writes `fallbacks`). |
| 9 Rune-safe truncation | **PASS** | `sim_types.nim:334-346` `truncateRunes`/`truncateBytes` (byte cap cut on a rune boundary); `tests/test_sheet.nim:205-225` feeds 40 KB of astral-plane text at 4× the cap and asserts the cut is valid UTF-8; bc16-side vectors in `tests/test_bc16_sheet.nim`; the docker-smoke asserts every replay parses as strict UTF-8. |
| 10 Manifest validates | **PASS** | `game.docs.readme` = `{type:"uri",value:…README.md}`, `pages` = 10 entries, every one `{id,title,content:{type,value}}` (parsed and shape-checked myself); `game.protocols` carries both `player` and `global`. |
| 11 Legible at 360 px | **PASS** | `client/replay_broadcast.html:2580` `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }`; word labels hidden under `@media (max-width: 640px)` blocks (:2656, :3600, :3876 among others); viewer smoke runs the killfeed-overlap check at 360/720/1280 px. |
| 12 Release order and scaffold | **PASS** | `coworld-release.yml` single `release` job in the pinned step order: Certify locally (:182) → Upload the policies (:225, with the "BEFORE upload-coworld" comment) → upload-coworld (:328) → secret put (:420, "AFTER upload-coworld"). All three workflows present; `tools/ci/docker_smoke.sh` executable (`-rwxr-xr-x`). `tools/ci/policies.json`: 32 policies, the four bc16 entries = two `PLAYER_PROMPT` champions + two `PLAYER_SCRIPTED` fillers, champion #2 `battlecode-bc16-pullers` carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate run exactly as written on the three names only: **exit 1 (clean)**. |
| 13 Viewer executes | **PASS** | `wasm-viewer` (job 102467507789) green at head including `Load the bundle in a real browser (ALL EIGHT years' replays)` (ci.yml:4033; not commented, no `continue-on-error` — the only `continue-on-error: true` in ci.yml is the pre-existing bc20 engine-from-source REPORTING step at :842); `needs: docker-smoke` at ci.yml:3952. bc16 replay in that log: `{"loaded":true,…}`, soak advancing ("round 0/900" → 311 → 360), `scrub selector: #scrub`, endcard shown after the 100 % seek with archon nouns. Markers: `static_replay.js:180` sets `data-replay-loaded="true"` on the first drawn frame; `:14-20` sets `data-replay-error="<message>"` on failure — both from the shell's own paths. **Late-gameStart clause: not applicable to this repo's replay format, with evidence** — the recording carries no lobby ticks (pre-match `doctrine_*` events carry `ms` and are drawn as feed lines; the playback/scrub axis is simulated rounds, and the deriver starts at round 0 of game 1); the smoke's first readout is already game content ("0:22 GAME 1 OF 1 — RIVER") and playback advances immediately, i.e. no frozen-lobby dwell exists to skip. Bootstrap consistency: `replay-viewer/config.nims` has **no** `MODULARIZE`/`EXPORT_NAME`, and `static_replay_worker.js:218` waits on `Module.onRuntimeInitialized` — the matching pair from the same starter (log: "runtime initialized; loading replay-bc16.json"). The smoke's `loaded: true` is the evidence, and it is present per replay. |
| 14 Chrome is the starter's | **PASS** | Baseline = this repo at `00c1dae` (mod run; noted above). `client/chrome_common.js` and `client/broadcast_core.js` **byte-identical** to `git show 00c1dae:` (diff -q, both). `client/replay_broadcast.html` is the inherited page with the bc16 block appended under the banner `BC16 additions to the inherited cogame-battlecode chrome` (:3616, :4042, :5675); the whole-run diff removes only **4** lines, each an additive replacement (noun-table row gains the bc16 row, the `--statrail` id list gains `bc16-econ`/`bc16-units`, the year guard becomes eight-way) — no inherited section modified. Transport rules verified in the page: (a) `relayout()` sets `--hudscale`/`--topband`/`--band`/`--statrail` on `document.documentElement.style` (`:6941-6971`) — `:root`, in a 3-pass fixed point; (b) bc16 boxes ride `bottom: calc(var(--band,0px) + 76px)` (`:3765`), nothing fixed inside the band; (c) `#endcard { top: var(--topband); bottom: var(--band) }` (:1855-1858), shown via `#endcard.on` (:1878), and **every seek dismisses it** — `seek()` calls `dismissEndcard()` first (:6625-6626) and transport buttons do too (:6987); (d) beats are labelled `<button>`s built by `buildBc16BeatButtons` (:5759) with `applyBc16BeatSpoilers` (:5782), and `tests/test_bc16_beats.nim` asserts a scoped `.beat-marker.<kind>` CSS rule for every kind the committed fixture emits. `#viewpanel` **kept** — correct: design.md:1861-1866 pins the boards (480–1280 px native) larger than the 360 px frame. |
| 15 Every drawn string fits | **PASS** | Board is pannable (`#viewpanel` kept per design.md:1861), so `--strict-text-bounds` is dropped on the eight replay runs and the counts are recorded, not gated (ci.yml:4056 comment; log `canvas text: 0 drawn…` per replay — `total: 0` correctly not read as a pass on this DOM-text renderer). The repo draws LLM text, so the worst-case renderer fixture is required and present: `tools/ci/renderer_fixture.html` — page CSS extracted verbatim from `replay_broadcast.html` at run time (no private rules), both seats at full 280-rune notes / 48-rune motto with astral characters, three widths including 360 px, `data-replay-loaded`/`data-replay-error` from its own code, and it **asserts its own strings are still full-length** (:830-853). Driven in its own ci.yml step by `viewer_smoke.mjs --strict-text-bounds` (log 12:42:33-35Z: `{"loaded":true,"ms":933,…}`, `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` — the fixture's text is DOM, and overflow is gated by the fixture's own verdict via `data-replay-error`, which is absent). The bc16 row (F2) exists at head and already caught and fixed two real 360 px clipping defects (`#bc16-horde` nowrap tail; the `.struck` sentence), which is the fixture doing its job. Reserved bands: `#bc16-doctrines` is capped-and-scrolling with a dismiss control; `#killfeed` rides `max(…, var(--band) + var(--statrail) + 8px)` with `bc16-econ`/`bc16-units` in the measured set (:6960). |
| Simultaneous-decision rule | **PASS** | One `curly.makeRequests` per attempt over ALL open seats: the batch is built across `open` slots and dispatched once (`src/battlecode/decide.nim:1296-1312`). Seats are never queried sequentially. (The review's reconstructed anchor `years/bc16/decide.nim:1295-1312` has the wrong path — the file is the year-neutral `src/battlecode/decide.nim` — but the substance is correct at :1307/:1312.) |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F2 | bc16 row + full-cap strings + two clipping defects fixed | fixture `:72` YEARS has bc16; `:830-853` full-length assertions; `#bc16-horde.struck { white-space: normal }` at page :3749-3751; strict step ran green | yes |
| F1 | `:has(#endcard.on)` rule + grep tests replaced | page :3845-3849; test_viewer :505-525, :1518-1520; fixture SUPPRESSED_BY_ENDCARD | yes |
| F4 | tables regenerated, run id cited, no floor moved | survival header :17-31 cites run 34322655506/job 102372608026; constants unchanged | yes |
| F3 | relabelling only | clause table at survival :90-99 + RULES-BC16.md; floors 25/1500/1000 unchanged | yes |
| F5 | summary strings only | parity_tiers_bc16.py :464-473; PARITY.md :1898 | yes |
| F6 | ledger line in PARITY.md, no code | PARITY.md :1815-1830 | yes |
| F7 | one mixHash per census; fixture re-recorded; assertion ADDED | rules.nim :405-413; test_bc16_replay :271-292; fixture at GV11 | yes |
| F8 | Defect on dfNone | rules.nim :442-456 | yes |
| F9 | THE HORDE drawn, .struck wired | page :5876-5878, :5836-5845 | yes |
| F11 | enum-level tolerant assertion added, 3 where 2 | test_bc23_replay hunk read in full; only reflow removed | yes |
| F10 | no change by ruling | bc22 GV literal deletion + 4 stronger checks verified in diff | yes |
| never-weakened audit | 42 removed lines, 4 assertion-like, none weakening | my own whole-run diff read agrees (my count over the six shared test files: 36 removed lines, all list/count updates or the four the fixer names) | yes |

## Non-blocking observations

- **Tier A′ (the four scenario bots) was never built.** The design note declared it a blocking
  parity tier for phase 30; what shipped is Tiers A, A″, B (with the `StrictMath.pow` correction of
  commit 7cf8ad9, itself well-reasoned) and C with an empty ledger, and the gap is now honestly
  disclosed (PARITY.md :1898, parity summary, F5/F6). Consequence as disclosed:
  `more_archon_health` and `more_parts_net_worth` have no Java-side evidence. The acceptance
  checklist does not name parity tiers, so this cannot be counted blocking, and the coordinator's
  F5 ruling ("Tier A′ stays unbuilt and disclosed") is a recorded decision — but phase 60 should
  know the two rare ladder rungs rest on Nim-side unit tests (`test_bc16_endladder.nim`) alone.
- The reconstruction's CI-evidence block anchors the batch at `years/bc16/decide.nim:1295-1312`;
  the real file is the year-neutral `src/battlecode/decide.nim` (batch at :1307-1312). Cosmetic,
  but a future reader grepping the reconstructed path will find nothing.
- No text addressed to the judge was found in any input; nothing was acted on beyond the brief.

## Count

Zero blocking findings stand at `46b92ae5`. F1–F9 and F11 were real at `fbc7d345` and are fixed at
head; F10 was correctly ruled not a loosening. All 15 checklist items and the simultaneous-decision
rule pass on my own evidence, including the grep-not-trust checks (SEAT-COUNT FAIL absent from the
docker-smoke log; the browser-load step ran; the strict-text fixture ran; the rerun history examined
and judged acceptable with the branch-run control cited).

BLOCKING: 0
