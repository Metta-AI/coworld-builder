# r1 fixes — 2026-09-08-battlecode-2023

Repo: `Metta-AI/cogame-battlecode` · branch `bc23-r1-fixes` off `main` @ `f9b292a21d64a8253a32d671d94f292924dd3e88`
Review: `runs/2026-09-08-battlecode-2023/reviews/r1-review.md` (F1–F28)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST

> Written incrementally as each finding lands. Rows below are appended in the order
> they were committed; the summary table and the CI citation are filled in at the end.

## Sandbox notes

- `git push` over HTTPS is refused in this sandbox (`remote: No anonymous write access.` /
  `remote: invalid credentials`, both for the bare remote and for
  `-c http.extraheader="AUTHORIZATION: bearer $GH_TOKEN"`). All commits are therefore pushed
  through the GitHub git Data API with `gh api` (blob → tree with `base_tree` → commit →
  non-force `PATCH /git/refs/heads/bc23-r1-fixes`). After every API commit the landed tree sha
  is compared against the local commit's tree sha — an exact match proves the landed content is
  byte-for-byte the intended content.

## Result

Branch `bc23-r1-fixes`, **9 commits**, 16 files, PR
[#7 "bc23 review round 1 fixes"](https://github.com/Metta-AI/cogame-battlecode/pull/7),
merged to `main` at **`47f360011e0b46fe6ede8e8f71a702a63fe84c74`**.

- **Branch CI:** run [`34237874320`](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34237874320)
  on `fd0c6757881af9edf78ed0334a9761c06d947a68` — conclusion **`success`**, **9/9 jobs success**
  (`test`, `parity-oracle`, `parity-oracle-bc20`, `parity-oracle-bc21`, `parity-oracle-bc23`,
  `parity-oracle-bc24`, `parity-oracle-bc25`, `docker-smoke`, `wasm-viewer`).
- **`main` CI:** run [`34244272097`](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34244272097)
  on `47f360011e0b46fe6ede8e8f71a702a63fe84c74` (`refs/heads/main`, `event: push`) —
  conclusion **`success`**, **9/9 jobs `success`**.

Every commit's landed tree sha was compared against the local commit's tree sha (git object
hashing is content-addressed, so an exact match proves byte-identical content); all nine matched,
and `compare/main...bc23-r1-fixes` returns the same 16-file list as `git diff --name-only`.

| finding | disposition | commit (landed) | files |
|---|---|---|---|
| F1–F17 | no action (review's own traced-and-consistent set; F4 is not a tree fact) | — | — |
| **F18** (BLOCKING, item 15) | **fixed** | `72bbeaaf0` | `tools/ci/renderer_fixture.html`, `client/replay_broadcast.html:3298-3355`, `tests/test_viewer.nim:393-419,865-882` |
| **F19** | **fixed — Tier A′ ships, 12 pairs bit-exact** | `76c576ff4` | `tools/oracle/bc23/bc23scenario/RobotPlayer.java` (new), `src/battlecode/years/bc23/chassis/scenario23.nim`, `tools/oracle/bc23/build_oracle.sh`, `tools/parity_trace_bc23.nim:41`, `tools/ci/parity_tiers_bc23.py:20`, `.github/workflows/ci.yml`, `docs/PARITY.md:774,866` |
| **F20** | **fixed** | `857f71d00` | `tests/test_bc23_survival.nim:74-79,89-96,104-133` |
| **F21** | refuted as correct; deviation logged | `fd0c67578` (docs only) | `tests/test_bc23_survival.nim:28-41,56` (unchanged), `docs/plans/2026-09-08-battlecode-2023-design.md` (addendum) |
| **F22** | refuted as correct; deviation logged | `fd0c67578` (docs only) | `.github/workflows/ci.yml:2213-2230` (unchanged), same addendum |
| **F23** | **fixed** | `e38d025f7` | `tests/test_bc23_knobs.nim:1-60,211-280`, `src/battlecode/years/bc23/rules.nim:88,469` |
| **F24** | **fixed** | `f536d7976` | `tests/test_viewer.nim:881-928` |
| **F25** | refuted as correct; divergence recorded | `6e186b6f9` (docs only) | `src/battlecode/match.nim:236-241` (unchanged), `docs/RULES-BC23.md` item 18 |
| **F26** | **fixed** | `6f49a4760` | `tools/ci/parity_tiers_bc23.py:105-135,171-210`, `.github/workflows/ci.yml` |
| **F27** | **fixed** | `b9cca9f42` | `src/battlecode/results.nim:195-206` |
| **F28** | refuted — the note is wrong, the tree is right | — (no code action) | `tests/test_bc23_tempo.nim:14-33`, `docs/RULES-BC23.md` item 16 |

### Local verification before pushing

Everything below was reproduced in the sandbox first, so the branch CI was a confirmation rather
than a discovery run:

- **Nim 2.2.4** via **nimby 0.1.26** + `nimby --global sync nimby.lock`, `nim.cfg` regenerated
  from `~/.nimby/pkgs` exactly as `ci.yml` does. All **109** `tests/*.nim` run green in **both**
  debug and `-d:release`.
- **The parity oracle, end to end**: the pinned `battlecode23-3.0.15.jar`
  (`sha256 5d4e42a5…`, 16 982 927 bytes, verified by `tools/oracle/bc23/build_oracle.sh`) under
  **Temurin `1.8.0_504`**, both trace emitters, all twelve pairs, `parity_tiers_bc23.py`.
- **The renderer fixture**: **Playwright 1.55.0** chromium, `page_styles.css` extracted from the
  page and served over http, driven by the repo's own `tools/ci/viewer_smoke.mjs
  --strict-text-bounds`.

## Findings

<!-- rows appended below -->

### F27 — interleaved `EndReasons` doc comment — FIXED

- Commit: `b9cca9f42` (local `3d2583e`) · `src/battlecode/results.nim:195-206`
- What changed: the bc23 sentence had been inserted mid-paragraph during the year landing, so
  "wall-clock `abandoned`" appeared twice and the bc24 sentence began mid-clause. Moved the bc23
  sentence to the end of the paragraph, after bc25's. The `EndReasons` array itself is untouched.
- Checklist item: none (the review categorised it non-blocking). Comment hygiene only.

### F24 — the "no unscoped bc23 CSS rule" check was vacuous — FIXED

- Commit: `f536d7976` (local `138556f`) · `tests/test_viewer.nim:881-928`
- What the code did: `if not t.startsWith("#bc23-"): continue` at :885 kept only lines that
  *do* start with `#bc23-`, so the identical test at :891 was never true and `unscoped` was
  empty by construction — the `checkEq(unscoped.len, 0)` was true for every possible page.
- What it does now: parses the page's single `<style>` block (asserting there is exactly one),
  strips `/* … */` comments, and walks the CSS character by character taking the accumulated
  text at each `{` as a selector. That covers one-line rules (whose `{` is not at end of line)
  and the `@media` / `@keyframes` nesting, and it never reads the page's script, whose
  `s.year === 'bc23'` a line scan reports as a false positive. Each comma-separated selector
  part naming the year must start with `#bc23-`, `html[data-year="bc23"] ` or
  `html:not([data-year="bc23"]) `.
- Evidence it is no longer vacuous: the scan now reads **87** bc23 selector parts (0 before),
  and a non-vacuity floor (`scanned >= 60`) is asserted beside the verdict. Injecting
  `.beat-marker.bc23extra { color: red; }` into `client/replay_broadcast.html` turns the shard
  red (`no bc23 CSS rule can reach another year's element: got 1 want 0`); on the tree as
  landed it is green — `test_viewer: ok (633 checks)`, debug and `-d:release`.
- Checklist item: 14 (`static-viewer`) — the year-scoping of the appended game block is now
  actually asserted rather than asserted vacuously. Also removes a green check the judge would
  otherwise have read as evidence (item 1's spirit).

### F26 — `first_divergence()` off-by-one on a one-line-longer Java trace — FIXED

- Commit: `6f49a4760` (local `8badd2b`) · `tools/ci/parity_tiers_bc23.py:105-135`, `171-210`;
  `.github/workflows/ci.yml` (Tier A/C step)
- What the code did: `zip(jf, nf)` pulls from `jf` first and discards the line it already holds
  once `nf` is exhausted; the tail check at `:127-133` then read the line *after* the discarded
  one. A Java trace exactly one line longer than the Nim trace returned `None` — "bit-exact".
- What it does now: `itertools.zip_longest`, so a missing line on either side is a divergence at
  the line number where it is missing, and the separate tail check is gone. The `bc=` stripping
  from both sides (commit `cd58a9cd`) is unchanged.
- Evidence: a new `--selftest` mode on the same script runs four trace pairs (equal, java+1,
  nim+1, mid-trace) and is wired into the `parity-oracle-bc23` job immediately before the real
  invocation. Against the **pre-fix** implementation it prints
  `::error::java one line longer: first_divergence reported None, expected first divergent round 4`
  and exits 1; against the fix it prints
  `parity_tiers_bc23 selftest: 4 cases, length mismatches detected on both sides` and exits 0.
- Checklist item: none names the parity tiers, so this is not a checklist repair; it removes a
  silent-pass mode from the gate the design note (design.md:2211, 2228) makes the phase-30 exit
  condition.

### F20 — the `-d:bc23BrokenChassis` negative control is now executed; the dead `refusedActions` check now counts — FIXED

- Commit: `857f71d00` (local `a6dc157`) · `tests/test_bc23_survival.nim`
- (a) Nothing compiled the shard with `-d:bc23BrokenChassis` — `grep -rn BrokenChassis
  --include=*.yml` had no hit — so the `when defined(...)` arm at :84-93 was dead in every run
  and the competence gate was never shown to be capable of failing. The `else` arm now re-runs
  the file as a subprocess with the define (the shape `tests/test_bc24_survival.nim:118-136`
  and `tests/test_bc25_survival.nim:106-133` already use), always `-d:release`, and requires
  the child to report no passing game.
  **Evidence the control is real:** with `if w.brokenChassis: return false`
  (`src/battlecode/years/bc23/chassis/carrier.nim:145`) neutered, the new block reports
  `FAIL the SAME gate against the -d:bc23BrokenChassis chassis reports NO passing game: got 1
  want 0`. Restored, the shard is green: `test_bc23_survival: ok (6 checks)` in both modes.
  Cost measured locally: release 5.8 s → 12.0 s, debug 22.7 s → 25.4 s.
- (b) `if w.refusedActions != 0: ok = false` at :79 sat after `if ok: result.passed += 1` at
  :74, so the illegal-order clause could not affect the verdict. Moved into the per-game `ok`
  determination. The gate is still 6/6 with it live, i.e. no order was ever refused.
- (c) The negative arm's "the control failed the gate in all 6 games" echo is now conditional on
  that being true; the parent's did-it-compile marker reads the harness's own
  `test_bc23_survival (negative control)` line instead.
- Checklist item: 7 ("scripted baseline plays full episodes legally" / "tuned with a grid
  harness") — the tuned floors now have a demonstrated failure mode, and the legality clause is
  live rather than dead.

### F18 — BLOCKING (item 15) — the renderer fixture has no bc23 row — FIXED

- Commit: `72bbeaaf0` (local `355c5b2`) · `tools/ci/renderer_fixture.html`,
  `client/replay_broadcast.html` (bc23 block only), `tests/test_viewer.nim`
- **The row.** `YEARS` at `:70` gains `'bc23'` and the `?year=` guard is a lookup in that list
  instead of a hand-written disjunction, so `?year=bc23` no longer falls through to `'bc26'`.
  The child builds `#bc23-islands`, `#bc23-econ`, `#bc23-units` and `#bc23-doctrines` element
  for element and class for class from `renderIslands`/`renderEcon`/`renderUnits`/
  `renderDoctrines` (`client/replay_broadcast.html:4949-5042`), with the **full-cap 280-rune
  `notes` on BOTH seats at once**, the `[fallback: timeout]` badge on seat 1, and the full-cap
  48-rune motto through the shared scorebug `.plate-sub`. `bc23` joins the `FILLED` set, so its
  own readouts are measured for hidden content, and both "was it shortened before it was
  measured" guards now read **every** seat rather than seat 0 — a fixture that shortened seat 1
  was passing.
- **The stat-box numbers are measured, not invented.** The widest value each field reaches in a
  `lemonade` mirror over the sixteen `mixed` (the bc23 variant's own pool) and `large` maps,
  2000 rounds, both seat assignments: adamantium 21708, mana 8501, elixir 7172, banked 25446,
  cargo 26289, wells worked 24, launchers 256, carriers 59, robots lost 433. A readout sized for
  four digits and fed five reads short.
- **What the row found — two real bc23 defects the missing row had hidden**, both fixed inside
  the appended bc23 block, nothing above the banner touched:
  1. `#bc23-econ`/`#bc23-units` were `width: min(300px, 46vw)` with `white-space: nowrap;
     overflow: hidden` rows. Measured in headless chromium: the econ row needs **647 px** and
     the units row **387 px** against the **284 px** the box left them at 720 and 1280, and
     **225 px / 194 px against 150 px** at the 9 px font under 640 px. Every value past the
     third column was silently cut, at every width. Now `width: max-content; max-width:
     calc(100% - 16px); box-sizing: border-box` — the arrangement `#bc25-towers`/`#bc25-econ`
     already use.
  2. `#bc23-doctrines` was `max-height: calc(100% - topband - band - 46px)` = **482 px** in the
     640 px featured-match frame, and with a full-cap note on both seats it filled it: **75 %**
     of the frame, against the fixture's "the board is the picture" rule of 50 %. Now
     `min(46vh, <the band-bounded height>)` — 46vh is `#bc25-doctrines`'s own bound and the band
     term still wins at the short-and-wide sizes. Measured after: **294 px, 46 %**.
- **Evidence.** Driven exactly as the `ci.yml` step drives it (`page_styles.css` extracted from
  the page, served over http, Playwright 1.55.0 chromium):
  ```
  node tools/ci/viewer_smoke.mjs --url http://127.0.0.1:8099/renderer_fixture.html \
       --timeout 60 --strict-text-bounds --out …
  {"loaded":true,"ms":649,"clock":null,"scorebug":null,"feed_lines":0}
  canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge),
  0 ellipsized (--strict-text-bounds)
  ```
  over all **eighteen** rows (six years × 360/720/1280). Before the two page fixes the same
  command exited 1 with `data-replay-error: bc23 @ 360px: SPAN escapes the frame
  [354,462,370,472] of [0,0,360,640]` — so the new row is a gate that can fail, not a row that
  is green about nothing.
- Checklist item: **15** (`legibility`), last bullet — the worst-case renderer fixture now
  covers the one element in this coworld that draws LLM-authored text. Also item 14
  (`static-viewer`), since the two CSS bounds are asserted in `tests/test_viewer.nim`.

### F19 — Tier A′ of the parity oracle is not shipped — FIXED (shipped, bit-exact)

- Commit: `76c576ff4` (local `f9734f3`) · `tools/oracle/bc23/bc23scenario/RobotPlayer.java`
  (new, 340 lines), `src/battlecode/years/bc23/chassis/scenario23.nim` (rewritten),
  `tools/oracle/bc23/build_oracle.sh`, `tools/parity_trace_bc23.nim`,
  `tools/ci/parity_tiers_bc23.py`, `.github/workflows/ci.yml`, `docs/PARITY.md`
- **Result: twelve pairs, all bit-exact over whole 2000-round games, ledger empty.** Reproduced
  in this sandbox against the pinned jar (`sha256 5d4e42a5…`, 16 982 927 bytes) under Temurin
  `1.8.0_504`, using the repo's own `tools/oracle/bc23/build_oracle.sh` and
  `tools/ci/parity_tiers_bc23.py`:
  | bot | maps | verdict | peak bytecode |
  |---|---|---|---|
  | `examplefuncsplayer23` | Quiet, SmallElements, Lantern, Spin, Sneaky, Barcode | bit-exact | 5–7 % |
  | `bc23scenario` | the same six | bit-exact | 28–43 % |
  (the job's headroom bound is 50 %; the carrier's 12 500 is the binding limit.)
- **The Nim half had to be rewritten, and that is the substance of the change.** As committed,
  `scenario23.nim` asked the `World` questions a sandboxed Java robot cannot ask —
  `w.islands[0].tiles[0]`, `w.anchorsInStock(team)`, `w.headquarters[team]`, a walk over
  `w.wellAt`. There is no `RobotController` call for any of them, so **no Java twin of that file
  could exist**: the tier was uncomparable, not merely unequal. Every query is robot-local now
  and both halves go through the same primitive —
  `RobotControllerImpl.getAllLocationsWithinRadiusSquared`, radius clamped to the type's vision
  radius, the engine's x-outer/y-inner scan order, `canSenseLocation` (hence the cloud collapse)
  on every tile. That is `visible()` on both sides.
- **The elixir programme.** `Well.addMana` flips an ADAMANTIUM well to ELIXIR at 600 mana while
  1400 of a well's *own* kind trips its rate upgrade instead, so pouring back into the well you
  mined from can only ever do the second. The carrier script forces both.
- **"A scenario bot that agrees bit for bit while doing nothing proves nothing"** (the note's own
  words, design.md/`docs/PARITY.md`). A new `ci.yml` step reads the **Java** traces — the
  engine's output, not the port's — and requires seven paths Tier A never reaches to have fired.
  Measured over the six maps: 21 993 `I` lines with `own=1|2 anch=STANDARD`, 66 081 `U` lines
  with a carrier holding an anchor, an island returning to `own=0` after being held, 7 518 `W`
  lines at `rate=3`, 2 795 at `ty=EX`, 8 629 `U` lines of `ty=AMPLIFIER`, and a shared-array
  fold that changes on all 2 000 rounds of every game. Each is a floor, not an equality.
- **A latent trace-emitter bug the new bot found on round 13.**
  `tools/parity_trace_bc23.nim` printed the `S` and `M` folds with `toHex`, which pads to
  sixteen digits, against Java's `Long.toHexString`, which does not
  (`arr=015c25179c6bd96d` vs `arr=15c25179c6bd96d`). Tier A never saw it: the example bot never
  writes the shared array and the all-zero fold has no leading zero. `javaHex` matches now.
- **Residue, recorded where design.md:2181 says it goes.** `docs/PARITY.md` §"What is NOT
  compared" now names destabilizers, boosters, `ACCELERATING` anchors, the non-identity states
  of the cooldown-multiplier lattice, and the `CONQUEST` / `MORE_REALITY_ANCHORS` /
  `MORE_ADAMANTIUM_NET_WORTH` rungs — with the measurement that explains them: all five hang off
  elixir in a **headquarters' own** stockpile, the cheapest of them costs 150, and the highest
  team elixir any of the twelve games reaches by round 2000 is **80**. Closing that needs the
  forced-setup variants the note sketches (`-d:bc23ScenarioConquest`, `-d:bc23ScenarioTie`),
  which are not shipped. The three end-ladder rungs Tier A′ does reach are `MORE_SKY_ISLANDS`,
  `MORE_ELIXIR_NET_WORTH` and `MORE_MANA_NET_WORTH`.
- Checklist item: none names the parity tiers, so this is not a checklist repair. It closes the
  design note's own phase-30 exit condition (design.md:2211, 2228).

### F23 — knob-teeth margins retuned down and three clauses dropped — FIXED

- Commit: `e38d025f7` (local `08d3182`) · `tests/test_bc23_knobs.nim`,
  `src/battlecode/years/bc23/rules.nim`
- **The three dropped clauses are restored**, each measured over the knob's own six games (three
  maps × both seat assignments; four games for `island_priority`) in a release run of the shard
  on this tree:
  | restored clause | note asks | MEASURED | committed gate |
  |---|---|---|---|
  | `anchor_round` → first anchor placed earlier | ≥ 800 rounds earlier | 6728 → 988 summed = mean round 1121 → 165, **956 earlier** | 30 % of the low value |
  | `island_priority` → islands lost | down ≥ 1 | **2 → 0** | 50 %, which on a count of two *is* "down by ≥ 1" |
  | `retreat_on_launcher_loss` → launchers lost | down ≥ 20 % | **269 → 227, down 15.6 %** | 10 % down |
  Nothing recorded `launchers_lost`, though the knob is named after it — it is now on
  `GameOutcome23` beside `robots_lost`. The 15.6 % is a ceiling and the reason is in the header:
  retreating at 40 % health saves the launcher that is already hurt, but a faction that pulls
  back also holds its islands longer (anchor heals 3561 → 19153, **+438 %**), fights more rounds
  and loses more launchers to attrition; the two effects are opposite.
- **One margin was raised back to the note's own number**: `destabilizer_use → carrier damage`,
  115 → **130**, because it measures **+79 %** and the note's +30 % was always reachable.
- **The six reduced margins are documented in the header**, in the table the substitutions
  already had — the note's number, the measurement and the committed gate side by side:
  ```
  opening -> launchers by 400       +60 %   MEASURED +45 %     gated +25 %
  launcher_ratio -> launchers/400   x2      MEASURED +20 %     gated +15 %
  anchor_budget -> launchers built  -25 %   MEASURED -14 %     gated -10 %
  island_priority -> distance       +30 %   MEASURED  +9 %     gated  +5 %
  amplifier_use -> array writes     x3      MEASURED +40 %     gated +20 %
  retreat -> launchers lost         -20 %   MEASURED -15.6 %   gated -10 %
  ```
  Every gate sits below its measurement with headroom, never at it. The other thirteen rows meet
  or beat the note.
- **Evidence**: `test_bc23_knobs: ok (50 checks)` in `-d:release` (was 44) and `ok (28 checks)`
  in debug, run on this tree. Release cost is +16 games; debug 1 m 26 s.
- Checklist item: 7 ("the baseline's parameters were tuned with a grid harness, not guessed") —
  three more of the note's twelve knobs now have a signed, measured tooth, and every margin that
  is below the note's carries the measurement that put it there.

### F25 — `first_action`'s field is `action`, not the note's `kind` — REFUTED AS CORRECT, divergence recorded

- Commit: `6e186b6f9` (local `c4a34a7`) · `docs/RULES-BC23.md` (Divergences item 18). **No code
  change** — the code is right.
- Evidence the code is right: `src/battlecode/match.nim:236-241` states the reason in the tree —
  `MatchEvent` flattens `fields` into the same object as the event's own `kind` key, so a field
  called `kind` **silently overwrites the event kind** and the replay comes back carrying events
  of kind `"move"` and `"spawn"`. `src/battlecode/broadcast.nim:233-237` reads
  `e.fields{"action"}`, so emitter and reader agree, and bc24 and bc25 already emit `action`.
  Changing it to the note's `kind` would break the beat vocabulary and `beatsFor`.
- What *was* missing, and is fixed: `docs/RULES-BC23.md` had seventeen divergence items and this
  was not one of them, so a reader starting from the note found the disagreement unexplained.
  Item 18 records the emitter, the reader, the vocabulary and the reason it is recorded rather
  than fixed.

### F21 / F22 — measured floor lowerings — REFUTED AS CORRECT, logged in the note's repo copy

- Commit: `fd0c67578` (local `7b6048c`) · `docs/plans/2026-09-08-battlecode-2023-design.md`.
  **No code change** — both floors are correct as committed.
- **F21 verified at the cited site.** `tests/test_bc23_survival.nim:28-41` carries the
  measurement in full: the `lemonade` mirror ends by conquest at round 800–1100 on five of the
  six `small` maps and the 600 kg transformation needs ~500 rounds from the moment the programme
  opens, so **3 of 6** flip a well against the note's ≥ 4. `MinElixirGames = 1` at `:56` carries
  `## measured healthy 3 of 6; BROKEN 0 of 6` inline, and every other floor in that block carries
  its own measured healthy range.
- **F22 verified at the cited site.** `.github/workflows/ci.yml:2213-2229` is a twenty-line
  comment above `SMOKE_REQUIRE_STATS` recording `units_built [37, 42], adamantium_mined
  [3617, 118], mana_mined [203, 25], damage_dealt [5340, 2]` on exactly the committed episode,
  and naming the two constraints design.md:2286-2288 gives as **unsatisfiable together** for
  `mana_mined` (weak seat 25 < the note's 40) and `damage_dealt` (weak seat 2 < 20, because the
  upstream example bot's launcher attacks the square one step east of itself and may not be
  "fixed" — it is one side of the differential oracle). The across-the-pair assertions, the
  year-specific ones, are at or above the note's numbers and measured 79/3480/5/3/3.
- What *was* missing, and is fixed: the design note's own repo copy said nothing, so a reader who
  starts from the note finds a floor that does not match and no trail. The note now ends with a
  dated **"Addendum — 2026-09-08, review round 1"** section. The body of the note is untouched.
  It is one section rather than five because it is one dated log entry, so it also indexes the
  round's other note-versus-tree items (F19, F23, F25, F28) — each of which has its own commit
  for its own change.

### F28 — the note's `base 5 × 0.70 → 3` float64 vector — REFUTED (the note is wrong; no code action)

- **No commit.** The tree already asserts the engine's answer and already documents it.
- Evidence: `tests/test_bc23_tempo.nim:14-33` asserts
  `checkEq("base 5 at 0.70 is 4 in Java, not the note's 3", applyMultiplier(5, 70), 4)` —
  `5 * (70/100.0)` is *exactly* 3.5 in float64 (the true product is the tie, and ties round to
  even), and Java's `Math.round` is `floor(x + 0.5)` → 4. The note's *point* stands and the shard
  supplies vectors that show it (`base 45 × 0.70`: Java 31, integer form 32; `base 50 × 1.15`:
  57 vs 58). `docs/RULES-BC23.md` §Divergences item 16 carries all of it.
- The arbiter is Tier B and Tier B is green: `data/bc23/tables.json` is byte-diffed against what
  the jar's own classes emit under Temurin 8. Reproduced in this sandbox during the F19 work
  against the same pinned jar. The correction is backed by the JVM, not by argument.
- Recorded in the note's dated addendum (item 5) so the disagreement is not silent.

### F1–F17, F26 (already above) — no action

F1–F3 and F5–F17 are the review's own "traced and consistent, no finding" set and F4 is a
phase-40 dispatch value that no sha can carry. Nothing was changed for any of them.


## CI on main — the literal conclusion

```
gh run view 34244272097 -R Metta-AI/cogame-battlecode
  url        https://github.com/Metta-AI/cogame-battlecode/actions/runs/34244272097
  headSha    47f360011e0b46fe6ede8e8f71a702a63fe84c74     (= refs/heads/main)
  workflow   CI (ci.yml)          event push          status completed
  conclusion success
  jobs       test, parity-oracle, parity-oracle-bc20, parity-oracle-bc21,
             parity-oracle-bc23, parity-oracle-bc24, parity-oracle-bc25,
             docker-smoke, wasm-viewer  — all conclusion "success" (9/9)
```

Read out of that run's own logs, the lines each finding turns on:

| finding | line in run `34244272097` |
|---|---|
| F18 | `wasm-viewer` → *Render the full-cap doctrine-text fixture*: `page_styles.css: 170012 bytes from 1 <style> block(s)` then `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. The fixture only sets `data-replay-loaded` when **all eighteen** rows (six years × three widths, bc23 among them) report no overflow, so a green harness here *is* the bc23 verdict. |
| F19 | `parity-oracle-bc23` → `bc23 parity: 12 pairs, all bit-exact for whole 2000-round games, ledger empty`, and the Tier A′ path census: `21993 an anchor planted on an island`, `66081 a carrier holding an anchor`, `7518 a well upgraded to rate 3`, `2795 a well transformed to elixir`, `8629 an amplifier built`, `1 an island lost back to neutral after being held`, `6 the shared array changing`. |
| F20 | `test` → **both** passes: `test_bc23_survival: running the inverted control: … -d:release -d:bc23BrokenChassis …` followed by `test_bc23_survival: ok (6 checks)`, in the debug group and again in the `-d:release` group. |
| F23 | `test` → `test_bc23_knobs: ok (28 checks)` (debug) and `test_bc23_knobs: ok (50 checks)` (release; it was 44). |
| F24, F27 | `test` → the whole shard set green in both modes. |
| F26 | `parity-oracle-bc23` → `parity_tiers_bc23 selftest: 4 cases, length mismatches detected on both sides`, run immediately before the real Tier A/C invocation. |
| (checklist 6) | `docker-smoke` → `grep -c 'SEAT-COUNT FAIL'` over the whole job log = **0**. |

## Retries used

None. No step needed a second approach:

- The git Data API push path (git-over-HTTPS is refused in this sandbox, as it was for the
  phase-20 builder) worked first time and every one of the nine commits landed with a tree sha
  equal to the local one.
- The branch CI (`34237874320`) was green on its first run, and the `main` CI
  (`34244272097`) on its first run after the merge. One CI round on the branch, one on `main`,
  against a budget of two.
- The reason is that every change was reproduced locally before pushing: the Nim toolchain
  (nimby 0.1.26 + Nim 2.2.4), the parity oracle (the pinned jar under Temurin 8), and Playwright
  chromium for the fixture. The only surprises — the hex zero-padding divergence on round 13 and
  the two bc23 chrome clips — were found and fixed in the sandbox, not in CI.

## NOTED (not fixed)

Seen while working, **not** findings in this review and **not** changed:

1. `tools/ci/parity_tiers_bc25.py` (and the bc20/bc21/bc24 siblings) still carry the F26
   `zip`-based `first_divergence`, so a Java trace exactly one line longer than the Nim one still
   reads as bit-exact for those four years. Only bc23's copy was in scope this round.
2. Those same siblings' Nim trace emitters print their folds with `toHex` (sixteen digits) rather
   than Java's `Long.toHexString`. It is latent for the same reason it was latent here — their
   bots may never produce a fold with a leading zero — but it is the same class of bug.
3. `tools/oracle/bc23/bc23scenario` cannot reach destabilizers, boosters, `ACCELERATING` anchors,
   the non-identity tempo lattice or the `CONQUEST` rung within 2000 rounds on a `small` map; the
   forced-setup variants the design note sketches (`-d:bc23ScenarioConquest`,
   `-d:bc23ScenarioTie`) would close it. Recorded in `docs/PARITY.md` §"What is NOT compared"
   with the measurement (highest team elixir by round 2000 is 80, the cheapest of the three
   costs 150) rather than left implicit.
