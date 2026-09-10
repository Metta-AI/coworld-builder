# r1 review — 2026-09-10-battlecode-2019 (`Metta-AI/cogame-battlecode`, bc19 year module)

Range: `6e89d0fe57cb..d2f5d3d7033925655cb64a26cc1a5879c041fec5` (14 commits, 123 files, +35 832 / −89)
Reviewed sha: `d2f5d3d7033925655cb64a26cc1a5879c041fec5` on `main` (merge commit of PR #14)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision batch rule), L74–247
Clone read at that sha in `/tmp/rev-bc19`. Files opened: 34 (11 source, 9 test, 4 CI/workflow, 4 doc, 3 client/viewer, 3 tooling) plus three CI job logs and the manifest.

**Verdict in one line: 24 findings, 0 blocking-candidates.** Every checklist item 1–15 and the
simultaneous-decision batch rule is verifiable from the tree or from cited CI evidence at the reviewed
sha, and none is falsified. All 24 findings are advisory. The three named contested items were traced
individually and are reported as F3, F4 and F5.

---

## Findings

Each finding is `blocking-candidate` or `advisory` **against the checklist**, not against taste.
"Observed" = I read the code. "Inferred" = I reasoned about it. "Untested" = it would need a run.

---

### F1 — `ci.yml` is `success` on `main` at the reviewed sha, all 12 jobs
**advisory (evidence FOR item 1)** — `.github/workflows/ci.yml`; CI run `34454858348`

Observed. `gh run list -R Metta-AI/cogame-battlecode --branch main -w ci.yml` returns
`{"conclusion":"success","databaseId":34454858348,"headSha":"d2f5d3d7033925655cb64a26cc1a5879c041fec5","status":"completed"}`.
`gh run view 34454858348 --json jobs` lists twelve jobs, every one `success`:

```
test 102798774973 | docker-smoke 102798775400 | wasm-viewer 102800176614
parity-oracle 102798775095 | parity-oracle-bc16 102798775280 | bc19 102798775171
bc20 102798775289 | bc21 102798775232 | bc22 102798775065 | bc23 102798775321
bc24 102798775306 | bc25 102798775126
```

No job carries `continue-on-error`; the only `continue-on-error: true` in the file is at
`.github/workflows/ci.yml:906`, inside `parity-oracle` (bc26's Gradle build), pre-existing at
`6e89d0f` and untouched by this diff.

**Checklist item:** 1 (CI green).

---

### F2 — No test was loosened, skipped, deleted or removed in this run
**advisory (evidence FOR item 1)** — `git log -p 6e89d0f..d2f5d3d -- tests/`

Observed. `git diff --stat 6e89d0f d2f5d3d -- tests/` = 32 files, +6 280 / −28. No test file was
removed; 22 `tests/test_bc19_*.nim` shards plus `tests/bc19_fixture.nim` and
`tests/fixtures/replay-bc19.json` were added.

`git diff 6e89d0f d2f5d3d -- 'tests/*.nim' | grep '^-'` yields **20 deleted lines and no others**.
Every one is a count/arity widening replaced by a stricter or equal assertion in the same hunk:

| deleted | replaced by |
|---|---|
| `tests/test_manifest.nim` `config_schema.year.enum names all eight years` (8 ids) | nine ids, plus `bc19 is APPENDED, so no existing index moved` |
| `one variant per registered year`, `variants.len, 8` | `variants.len, 9` |
| `ten doc pages ship`, `docs["pages"].len, 10` | `eleven doc pages`, `.len, 11` |
| `thirty-two policies ship`, `32 / 16 / 16 / 8` | `thirty-six`, `36 / 18 / 18 / 9` |
| `if variant["id"].getStr() != "bc16"` | `notin ["bc16", "bc19"]` (plus a new `bc19 is the 1000-round year` assertion) |
| `tests/test_viewer.nim` EIGHT-way discriminator strings ×2, `YEARS = [… 'bc16']`, `'bc16-econ','bc16-units']` | NINE-way strings, `'bc16','bc19']`, `'bc19-econ','bc19-units'` |

No assertion was deleted without a replacement, no tolerance was widened, and
`grep -iE 'skip|xfail|disable|when false'` over the **added** test lines returns only four prose
occurrences of the English word "skipped" inside doc comments
(`tests/test_bc19_combat.nim:1465,1483`, `tests/test_bc19_queue.nim:3881`,
`tests/test_bc19_vision.nim:5634` in diff coordinates). No `-d:` guard disables a shard.

**Checklist item:** 1 ("no test loosened", explicitly verifiable, not unverifiable).

---

### F3 — The GV12 fixture regeneration changed exactly two leaves per file, both `game_version`
**advisory (evidence FOR item 1)** — `tests/fixtures/replay-{bc16,bc22,bc23}.json`

Observed. I diffed each regenerated fixture leaf-by-leaf against its `6e89d0f` blob in Python:

```
replay-bc16.json  changed leaf count: 2   /game_version GV11 -> GV12 ; /result/game_version GV11 -> GV12
replay-bc22.json  changed leaf count: 2   (same two paths)
replay-bc23.json  changed leaf count: 2   (same two paths)
```

Nothing else moved: not one `hash_chain_rounds` character, not one event, not one sheet, not one
score. `replay-bc20/21/24/25.json` are not in the diff at all. The assertions that read these files
are pinned to the `GameVersion` **symbol**, not a literal — `tests/test_bc19_replay.nim:381`
(`checkEq("and it is this build's game version", fx.gameVersion, GameVersion)`) and
`tests/test_bc19_beats.nim:38`. `src/battlecode/sim_types.nim:16` is `GameVersion* = "GV12"` and
`:253-254` is `ReplayCompatibleGameVersions* = ["GV04","GV05","GV06","GV07","GV08","GV09","GV10","GV11", GameVersion]`
— **extended, never reset**, exactly as the design note §Sim module L1153 requires.

This is authorised cross-year edit 1 of 2 and it is what actually happened, not an assertion being
weakened.

**Checklist item:** 1.

---

### F4 (contested item 1) — `tests/test_bc19_beats.nim` emits eleven of twelve kinds; **all twelve** kinds nevertheless carry a scoped CSS rule, and that is asserted
**advisory** — `tests/test_bc19_beats.nim:33-34, 56-60, 166-169, 183-188`; `client/replay_broadcast.html:4153-4164`

Observed, traced in full. The builder's account is **correct on the substance** and the checklist
obligation is met by a stronger route than the one the design note named.

1. **Emission.** `tests/test_bc19_beats.nim:56-58` names eleven kinds individually and asserts each is
   in the fixture's emitted set; `:59-60` asserts the twelfth explicitly:
   `checkEq("and \`famine\` is the one it does not (see the header)", "famine" in kinds, false)`.
   The design note's §Tests item 24 requirement is `>= 24 beats over >= 10 distinct kinds` (L2365) and
   that is what `:47-50` asserts. So the *test-level* requirement is met; the note's *prose* claim at
   L1556 and L1680 ("all twelve are emitted by the committed fixture replay") is not true of the tree.

2. **`famine` really is unreachable for the strong chassis.** `noteFamine` is called from five sites,
   all of them on the *refusal* path of an affordability check:
   `src/battlecode/years/bc19/actions.nim:143, 179, 210-211, 254, 272` — e.g. `:208-213`

   ```nim
   if w.karbonite[t] < buildKarboniteOf(a.buildUnit) or
       tempFuel < buildFuelOf(a.buildUnit):
     if w.karbonite[t] <= 0: w.noteFamine(r.team, 0)
     if w.fuel[t] <= 0: w.noteFamine(r.team, 1)
     raise newException(BattlecodeError, "Cannot afford to build specified unit.")
   ```

   Every one of those raises increments `refused_actions`. `tests/test_bc19_baselines.nim:72-73`
   asserts `refusedActions[t] == 0` for `saber` on every seat of every gate game, and the committed
   fixture is a `saber` mirror. So a `saber`-mirror fixture **cannot** emit `famine` without
   simultaneously breaking the legality gate. `resources.nim:157-162` further makes it once-per-
   resource-per-team. Inferred (not run): `famine` remains reachable for a weak or an LLM order, which
   is what the CSS rule and the label exist for.

3. **Style — every kind the page can emit has a scoped rule.** `tests/test_bc19_beats.nim:166-169`
   checks a rule for each *emitted* kind, and then `:172-188` independently parses every
   `html[data-year="bc19"] .beat-marker.<kind>` selector out of the page source and asserts
   `declared.len == Vocabulary.len` (12) **and** `for k in Vocabulary: check(… k in declared)`. So the
   `famine` rule is asserted present by name, and no rule exists for a kind outside the vocabulary
   (the bc25 r1-F26 defect in both directions). The twelve rules are at
   `client/replay_broadcast.html:4153-4164`, each scoped to `html[data-year="bc19"]`.

4. **`famine`'s label is exercised.** `tests/test_bc19_beats.nim:145-162` builds two synthetic
   `famine` events (karbonite and fuel), runs them through `beatsFor`, and asserts each label is
   non-empty, ≤ 120 runes, and names its own resource — so neither branch of
   `src/battlecode/broadcast.nim:519-524` is dead.

**What is actually wrong here is documentation, not code.** Two comments in the tree state the
opposite of what the test does:

- `client/replay_broadcast.html:4144-4147`: *"`tests/test_bc19_beats.nim` asserts that the COMMITTED
  FIXTURE REPLAY emits every one of them"* — it asserts the reverse for `famine`.
- The same sentence is copied at `client/replay_broadcast.html:3626` and `:3898` for bc23/bc16 (both
  pre-existing, out of scope).
- `.github/workflows/ci.yml:4975-4979` gets it right: *"the COMMITTED bc19 fixture — which is the one
  that carries ELEVEN OF THE TWELVE beat kinds"*.

**Checklist item:** 14(d) — "scrubber beats are labelled `<button>`s that seek to their tick …, with
CSS for every kind the page emits — a kind with no rule is an invisible marker." **Satisfied.** No
kind the page can emit lacks a rule; the CSS-inventory failure mode is separately gated at
`:183-188`. The mismatch with design-note prose L1556/L1680 and the false comment at
`client/replay_broadcast.html:4146` are **advisory**.

---

### F5 (contested item 2, half A) — `fuel_reserve`'s reading IS in `docs/RULES-BC19.md`'s knob table, in cog-facing words
**advisory (condition satisfied)** — `docs/RULES-BC19.md:124` (table header), `:129` (row)

Observed. `docs/RULES-BC19.md:124` is `| knob | values | default | what it actually decides |` and
`:129` is the `fuel_reserve` row. It carries, in the doctrine sheet's own table and not only in
§Divergences:

- the reading in bold cog-facing words: *"**the fuel floor below which the order stops making WAR, not
  the floor below which it stops making MONEY.**"*;
- the pilgrim arithmetic (+10 a turn for 1, against a flat 25 a round for the whole order);
- the measured deadlock under the literal reading (*"3 280 karbonite banked, four military units, zero
  damage"*, `seed-0043`/`seed-0048`);
- the exact scope: *"the reserve gates **military builds, attacks and military movement**; `mine`,
  `move` and economy builds are funded whenever the order can pay."*

It is also §Divergences item 14 at `docs/RULES-BC19.md:234`. The implementation matches the doc:
`src/battlecode/years/bc19/chassis/econ.nim:81-104`, where `canSpend(…, essential = false)` applies
the gate at `:102` (`if not essential and w.fuel[t] - s.committedF - fCost < s.fuelGate(): return false`)
and `essential = true` bypasses it. `fuelGate()` at `:75-79` returns `s.doctrine.fuelReserve` verbatim.

**Half A of the acceptance condition is satisfied.**

**Checklist item:** none (no checklist item names knob documentation). Advisory.

---

### F6 (contested item 2, half B) — one of the two asserted teeth is **not** what shipped: `attacks` moves UP, and `docs/RULES-BC19.md:129` still says it moves down
**advisory** — `docs/RULES-BC19.md:129`; `tests/test_bc19_knobs.nim:52-59, 164, 353-362`

Observed. The design note L2334 asks for `fuel_reserve` 0 → 1500: *"rounds with fuel at 0 down ≥ 80 %
**and** attacks down ≥ 20 %"*. The tree asserts neither statistic as written.

`tests/test_bc19_knobs.nim:353-362`:

```nim
block:
  let a = sweep("fuel", "fuel_reserve", %0, Maps)
  let b = sweep("fuel", "fuel_reserve", %1500, Maps)
  downPct("rounds ended with the fuel store at zero", a.zeroFuel, b.zeroFuel,
          T["fuel.zero_fuel_rounds.down_pct"])
  ## SUBSTITUTED (header item 5): controlled for the army the reserve makes
  ## possible in the first place.
  downPct("attacks per military unit built",
          mean(a.attacks, a.military), mean(b.attacks, b.military),
          T["fuel.attacks_per_military.down_pct"])
```

Thresholds at `:163-164`:
```
"fuel.zero_fuel_rounds.down_pct": 40,      # measured -49 %    [40, not 80]
"fuel.attacks_per_military.down_pct": 20,  # measured -58 % [substituted]
```

And the header records the measurement honestly, `:52-59`:

> *"`fuel_reserve` 0 → 1500 — rounds at zero fuel 9 381 → 4 731 is −49 % against the note's −80 %: the
> threshold is 40 %. **"Attacks down ≥ 20 %" MOVES THE OTHER WAY (1 296 → 2 331)** and the reason is
> `MilitaryFuelFloor`: an order at zero fuel cannot BUILD a soldier either, so reserve 0 fields 108
> military units where reserve 1500 fields 462, and more soldiers make more attacks. Controlled for
> that … ATTACKS PER MILITARY UNIT BUILT 12.0 → 5.0, down 58 %."*

So:
- tooth 1 (rounds at zero fuel down) **stays**, at a lowered but documented threshold (40 %, measured
  −49 %);
- tooth 2 (attacks down) **does not stay**. Raw attacks nearly **double**. What is asserted instead is
  a normalised statistic that the design note does not name.

The substitution itself is exactly what design note §Tests item 19 (L2324) licenses ("the header
records every substituted statistic (the bc21 r1-F6 fix)") and the header is meticulous. **The
inconsistency is that `docs/RULES-BC19.md:129` — the cog-facing knob table row, i.e. the one the
coordinator's condition points at — still ends:** *"which is exactly the trade the knob test asserts:
**rounds at zero fuel down, attacks down.**"* That sentence is false of `tests/test_bc19_knobs.nim` as
committed: the knob test asserts attacks-per-military-unit down, and raw attacks measured up.

I report the discrepancy; I do not propose a fix. Nine of the twelve threshold rows carry a
`[substituted]` or lowered marker (`:145-190`) and every one is explained in the header at `:15-110`.

**Checklist item:** none directly. Item 7's "The baseline's parameters were tuned with a grid harness,
not guessed" is *supported* by this file (paired seeded sweeps, 3 seeds × 3 maps per arm, every
threshold carrying its measurement). **Advisory.**

---

### F7 (contested item 3) — `530ccbd44`'s `sed 's/^::error:://'` masks nothing; a real failure still reddens the step
**advisory** — `.github/workflows/ci.yml:3461-3481`; `tools/gen_maps_bc19.mjs:205-256`

Observed, traced end to end. The step is:

```yaml
- name: "Tier B: the arithmetic tables and all 22 boards, byte-diffed"
  run: |
    set -euo pipefail
    node tools/JsBc19Tables.mjs --engine "$BC19_ENGINE" --check          # ← ungated, still reddens
    node tools/gen_maps_bc19.mjs --engine "$BC19_ENGINE" \
      --out data/maps/bc19 --check                                      # ← ungated, still reddens
    node tools/gen_maps_bc19.mjs --engine "$BC19_ENGINE" \
      --out /tmp/bc19curate --seeds 7 --assert-degenerate \
      2>&1 | sed 's/^::error:://' \
      | tee /tmp/bc19curate.txt || true
    for seed in 7 20 24 83 108 127 175 211 232 267 283 348 365; do
      grep -q "^refused ${seed}: " /tmp/bc19curate.txt || { …; exit 1; }
    done
```

What the generator prints (`tools/gen_maps_bc19.mjs`):

- `:248` — `console.log(\`refused ${seed}: ${r.refused}\`)` — **stdout, no prefix**, one line per
  degenerate seed. `--assert-degenerate` at `:240-251` iterates its **own** hard-coded
  `Degenerate = [7, 20, 24, 83, 108, 127, 175, 211, 232, 267, 283, 348, 365]` list at `:242`,
  independently of `--seeds`, which is why `--seeds 7` on the command line still produces all thirteen
  refusal lines.
- `:208` — `console.error('::error::seed ${seed} is not a playable board: …')` for the main loop's
  seed 7, and `:254` — `console.error('::error::${failures} bc19 map failure(s)')`, then
  `process.exit(1)` at `:256`. That non-zero exit is **the intended outcome of this invocation** (its
  purpose is that seed 7 be refused), which is what `|| true` absorbs.
- `:244-245` — if a degenerate seed *stops* being refused, the generator prints
  `::error::seed N was expected to be refused as unplayable and was not` **and prints no
  `refused N:` line**.

Therefore:
- `sed 's/^::error:://'` only strips the six-character annotation prefix from lines already going
  through the pipe. The strings the gate greps for (`^refused N: `) have **no prefix**, so `sed`
  cannot touch them. The `^` anchor in the `grep` is intact.
- A seed that stops being refused → its `refused N:` line is absent → `grep -q` fails → the shell's
  own `echo "::error::…"; exit 1` fires **outside the pipe**, un-`sed`-ed, and the step is red.
- Node crashing or failing to load the engine → empty/short file → all thirteen greps fail → red.
- The two *positive* Tier B checks (the arithmetic tables, and the byte-diff of all 22 committed
  boards) are separate invocations **without** `|| true` under `set -euo pipefail`, so a real
  regression in the committed maps or in `tables.json` still reddens.

**Confirmed in the CI log for the reviewed sha.** Job `102798775171` (`parity-oracle-bc19`) contains
both `1 bc19 map failure(s)` (the deliberate negative test's own message, prefix stripped) and
`all 13 degenerate seeds refused by name`, and `grep -c '##\[error\]'` over the whole job log is
**0**. The builder's reading is correct.

**Checklist item:** 1 (the change is in `ci.yml`, not `tests/`, and it disables no test). **Advisory,
no defect found.**

---

### F8 — Parity oracle: 54/54 bit-exact at the reviewed sha, ledger ships `[]`
**advisory (evidence)** — CI job `102798775171`; `tools/ci/parity_ledger_bc19.json`

Observed from the job log at the reviewed sha, not from the build report:

```
grep -c 'BIT-EXACT' /tmp/par19.log   → 54
compared 54 whole-game pairs, 0 failure(s)
all 13 degenerate seeds refused by name
grep -c '##[error]'                  → 0
```

`tools/ci/parity_ledger_bc19.json` is literally `[]` (2 bytes). The pair set is six bots × nine boards
(`.github/workflows/ci.yml:3517-3524`), each `--rounds 1000 --assert-clock`
(`:3546`), each compared by `tools/ci/parity_tiers_bc19.py` against the ledger (`:3557-3561`), with
`test "${fails}" -eq 0` closing the step (`:3567`).

**Checklist item:** none (the checklist does not name the parity oracle). It bears on item 1 only in
that the job is one of the twelve green ones. **Advisory.**

---

### F9 — Three per-pair liveness waivers exist in the oracle loop; none relaxes the trace comparison
**advisory** — `.github/workflows/ci.yml:3525-3540`; `tools/oracle/bc19/bc19_trace.js:62-66, 391-397`; `docs/PARITY.md:2062-2081`

Observed. The loop passes `--allow-no-build` for `bc19scenariotrade` (every map) and `--allow-inert`
for `examplefuncsplayer19` on `seed-0017` only:

```bash
if [ "$bot" = bc19scenariotrade ]; then flags="--allow-no-build"; fi
if [ "$bot" = examplefuncsplayer19 ] && [ "$map" = seed-0017 ]
then flags="$flags --allow-inert"; fi
```

and `--expect-freeze --allow-inert` on the separate, non-compared `bc19slowbot` run (`:3743`). The
flags gate only `bc19_trace.js:391-397`, the driver's "nothing happened" guard:

```js
if (!allowInert && botName !== 'bc19idle' &&
    (nonNothing === 0 || (unitsBuilt === 0 && !allowNoBuild))) { … process.exit(3); }
```

They do not touch `parity_tiers_bc19.py`, which is invoked unconditionally on every pair
(`:3557-3561`), so all 54 pairs are still compared line for line. Each waiver is named, per-bot and
per-map, in `docs/PARITY.md:2062-2081` with its measured reason (on `seed-0017` both castles'
`(x+1, y+1)` is impassable, so the stock example bot's only action is refused on every turn).

**Divergence from the design note I could not close:** §Tests item 4 (L2433-2435) asks `ci.yml` to
assert *per pair* that the game reached at least round 900 (or ended earlier with a `W` line), that at
least 8 robots were alive at once, and that at least one `A` line carries a non-`NOTHING` action. The
driver asserts the third of those (`bc19_trace.js:391`); `rounds` and `peak_alive` are computed and
printed into the summary (`bc19_trace.js:378-386`, `cat`-ed at `.github/workflows/ci.yml:3552`) but
`grep -n 'peak_alive' .github/workflows/ci.yml` returns nothing — neither is asserted. The
anti-vacuity work is instead done by the dedicated Tier A / A′ steps at `:3571-3760`, which assert
off the **oracle** trace (the trickle, `ids=4` never growing, `wc=1`, exactly one `A` line in round
1000, all five unit types, all five action kinds, the r² 7938 broadcast, castle talk, the CHURCH's
legal 0-damage attack on all nine boards, and the three end rungs).

**Checklist item:** none. **Advisory.**

---

### F10 — Decision path: one parallel batch per turn, tolerant parse, exactly one retry, fallback recorded
**advisory (evidence FOR item 8 and the batch rule)** — `src/battlecode/decide.nim:1395-1520`

Observed, traced step by step.

- **One parallel batch.** `:1443-1460` builds a single `RequestBatch`, appending one `post` per still-open
  seat (`for slot in open: … batch.post(...)`), then issues `client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`
  once. There is no per-seat request loop anywhere; both seats' calls leave together with the same
  deadline. bc19 has exactly one decision turn per episode (design L585), so this is the whole
  requirement.
- **Bounded.** `:1423` `while open.len > 0 and attempt < 2` — at most two attempts. `:1441-1442`
  `deadlineMs = if attempt == 0: config.attempt1Ms else: config.retryMs` (20 000 / 12 000 for bc19).
  `:1402` `budget = doctrineBudgetMs` (45 000), checked at the top of every iteration `:1425`; on
  expiry every still-open seat is recorded `cause: "timeout"` and `open` is **cleared** (`:1432-1440`)
  so the tail loop cannot overwrite the surviving cause with `"parse"`.
- **Tolerant parse.** `client.textOf(...)` then `parseReply(text, config.year)` at `:1466-1468`;
  `llm.nim` is unchanged in this run and carries the fence-tolerant JSON extraction (design L733-734),
  and `sheet.nim`'s envelope resolver (untouched) unwraps `sheet` / `doctrine` / a single
  object-valued key at most once.
- **Retry once, then fall back.** A parse or transport failure emits `doctrine_retry` with a typed
  cause (`timeout` | `transport` | `throttled` | `parse`, `:1486-1498`) and re-opens the seat once;
  after the second attempt the tail loop `:1508-1520` seats the baseline sheet, sets
  `result.fallback[slot] = cause`, emits a `doctrine_fallback` event, and logs the phase-60 grep
  string `falling back`.
- **The fallback is recorded so phase 60 can count it.** `result.fallback` / `result.fallbackDetail`
  (`decide.nim:38-42`) reach `results.fallbacks` and `replay.seats[].fallback` /
  `fallback_detail`. An LLM seat with no credentials is recorded as a **fallback**, not silently
  re-labelled scripted (`:1413-1420`).
- **Throttle fast-fail.** `:1501-1506` breaks out when the only candidate model answered 429, so the
  retry batch is not issued into a refusal.

**Checklist item:** 8 (LLM reply handling) and the simultaneous-decision batch rule. **Satisfied.**

---

### F11 — Every wait is bounded; the 305 s worst case sits inside 720 s
**advisory (evidence FOR item 5)** — `coworld_manifest_template.json` (variant `bc19`); `src/battlecode/years/bc19/rules.nim:413-434, 554-607`

Observed. The shipped bc19 `game_config`:

```json
{"year":"bc19","pool":"mixed","gamesPerMatch":3,"seed":0,"maxRounds":1000,"num_agents":2,
 "attempt1Ms":20000,"retryMs":12000,"doctrineBudgetMs":45000,
 "perGameBudgetSeconds":60,"matchBudgetSeconds":200,"connectTimeoutMs":25000,
 "players":[{"name":"Clan Ash"},{"name":"Clan Basil"}]}
```

with `episode_timeout_minutes: 20` at the manifest top level → 1200 s, 60 % = 720 s. The note's sum
(L573-583) is 30 + 45 + 200 + 30 = **305 s ≤ 720 s** and every term is a config value present above.

The round loop is bounded on both levels:

- `rules.nim:582-590` — `while w.running: runRound(...)`, with the abandon check
  `if budgetSeconds > 0 and (w.round and 0x1F) == 0 and getMonoTime() - started >= budget` every 32
  rounds; `outcome.aborted = true; break`.
- `rules.nim:425-432` — `while w.running: if w.evaluateIsOver(): w.running = false; break;
  w.enactTurn(...); inc played; if w.robots.len == 0: break; if w.robin >= w.robots.len: break`.
  Inferred: the loop cannot spin without progress — the first iteration either terminates the game or
  enacts a turn, and `evaluateIsOver` fires unconditionally at `round >= maxRounds` (1000).
- The DecisionOps cap `TurnMaxOps = 4000` is checked *before* each primitive, so a chassis turn ends
  deterministically rather than running long; `tests/test_bc19_baselines.nim:76-77` asserts
  `decisionOpsPeak[t] < TurnMaxOps` on every gate game and the build report measured 461 (11.5 %).

No blocking read exists anywhere in `years/bc19/`.

**Checklist item:** 5 (degrade-never-hang; categories hang, timeout). **Satisfied.**

---

### F12 — `drawId`'s `while true` is the engine's rejection loop verbatim; the V4 guard makes the non-terminating case unreachable
**advisory** — `src/battlecode/years/bc19/world.nim:347-368`; `actions.nim:214-220`; `world.nim:497`

Observed. `world.nim:358-368`:

```nim
proc drawId*(w: World): int =
  while true:
    let id = 1 + int(4095.0 * w.gen.random())
    if not w.idIsSpent.getOrDefault(id, false):
      w.idsSpent.add(id); w.idIsSpent[id] = true; return id
```

This is `game.js:433-435` reproduced exactly (one MT draw per attempt, rejection only on collision).
It is the *only* live draw site in the round loop. `createItem` has exactly two call sites:

- `world.nim:497` — the initial castle roster, at most 6 draws, from the committed post-`makeMap`
  MT state;
- `actions.nim:385` — the build path, guarded at `actions.nim:217-220`:
  `if w.idPoolExhausted(): w.stats.buildsRefused[t] += 1; raise …("Id pool exhausted; build refused (V4).")`,
  with `idPoolExhausted` = `w.idsSpent.len >= MaxId - 1` (`world.nim:356`, i.e. ≥ 4095) — so the pool
  can never be *fully* spent when `drawId` is entered, and the engine's non-terminating case is
  unreachable.

**Residual observation, inferred, untested:** with 4 094 ids spent the loop is still unbounded in
principle — it rejects until it draws the single remaining id, expected ≈ 4 095 cheap iterations,
terminating with probability 1 on a deterministic MT stream. The design note's own derived ceiling
(L562: "≈ 2 400 units a side") is **per side**, so two sides at that ceiling would draw ~4 800 ids,
which is above 4 095; the measured reality is far below (43 ids spent in the 600-round smoke, 140
units built in a 1000-round mirror), and `tests/test_bc19_baselines.nim:74-75` asserts
`buildsRefused[t] == 0` on every gate game. I did not find a game that reaches the guard.

**Checklist item:** 5 ("no unbounded loop"). I read this as **satisfied**: the loop is guarded, the
guard is on the only unbounded call site, and the guard's own test exists
(`tests/test_bc19_mt.nim`, design §Tests item 12). Reported as advisory so the judge can weigh it.

---

### F13 — Replay re-derivation: the committed fixture re-derives to its last round through the same `Deriver` the viewer runs
**advisory (evidence FOR item 2)** — `tests/test_bc19_replay.nim:372-399`; `replay-viewer/bc_replay.nim:88, 153`; `src/battlecode/replay.nim:270-312`

Observed. The record→re-derive test is `tests/test_bc19_replay.nim:372-394`:

```nim
let fx = parseReplay(readFile("tests/fixtures/replay-bc19.json"))
…
let d = newDeriver(fx)
var frames = 0
while d.advance(): frames += 1
checkEq("the committed fixture re-derives to its LAST round, not just the first 200",
  d.mismatchRound, -1)
check("and the deriver walked every recorded round, not a prefix", frames >= rounds)
```

`replay.nim:303-312` sets `d.mismatchRound = d.roundInGame` the first time a re-derived per-round
hash differs from the recorded one, so `-1` after walking every frame means **frame-by-frame
agreement over the whole recording**. The recording stores no per-tick state to agree with a parallel
recording *from*: `tests/test_bc19_replay.nim:121-132` asserts the document carries none of the
forbidden bulk keys, and `:135-136` asserts a 400-round one-game recording is under 32 KB. The
per-round chain is recorded as concatenated hex and its length is asserted equal to
`rounds * 16` (`:110-115`).

**The viewer runs the same code.** `replay-viewer/bc_replay.nim:88` is `deriver = newDeriver(doc)` and
`:153` exposes `bc_mismatch_round` from `deriver.mismatchRound` — the same `Deriver` type from
`src/battlecode/replay.nim`, compiled to wasm from the same sources. There is no parallel recording
path.

Independently confirmed in CI at the reviewed sha: job `102800176614` prints
`{"loaded":true,"game_version":"GV12","sim_sources_stamp":"bd48d61f…","frames":200,"mismatch_round":-1}`
for both `dist/smoke/replay-bc19.json` and `tests/fixtures/replay-bc19.json` under
`tools/wasm_replay_smoke.cjs`.

The `foldRoundHash` at `rules.nim:378-403` mixes thirteen per-team quantities plus nine globals
including the FNV-1a fold of the whole 624-word MT19937 state **and** `mti`
(`:402-403`), and `tests/test_determinism.nim` (bc19 block) proves the tripwire fires: it consumes one
extra id draw off one world and asserts every other folded quantity is identical and the chain still
diverges on the next round.

**Checklist item:** 2 (replay re-derivation). **Satisfied.**

---

### F14 — Manifest: `replay_viewer` bundle, `num_agents`, `game.docs`, `game.protocols`
**advisory (evidence FOR items 3, 6, 10)** — `coworld_manifest_template.json`

Observed, read out of the file with a script rather than by eye:

```
replay_viewer: {"bundle": "static-replay-viewer"}
protocols: {"player": {...PROTOCOL.md}, "global": {...PROTOCOL.md}}       # BOTH keys
docs.readme: {"type":"uri","value":".../README.md"}                        # object with type+value
docs pages n = 11, every page {id, title, content:{type,value}}
page ids: rules.md, rules-bc20.md, rules-bc21.md, rules-bc24.md, rules-bc25.md,
          rules-bc23.md, rules-bc22.md, rules-bc16.md, rules-bc19.md, replay.md, parity.md
variant bc26/bc20/bc21/bc24/bc25/bc23/bc22/bc16/bc19 → game_config.num_agents = 2,
          variant-level num_agents present: False   (all nine)
certification: game_config.num_agents = 2, len(players) = 2,
          len(game_config.players) = 2, year = bc26
player[] ids: ['awu', 'scaffold']    (unchanged; == certification.players)
```

`num_agents: 2` is inside **every** variant's `game_config` including the new `bc19`, and inside
`certification.game_config`; it is never at a variant top level. `game.docs.readme` and every
`content` are `{"type":"uri", …}` — checklist item 10 writes the shape as `"type":"text"`, but the
key shape (`readme` object with `type`+`value`; `pages` array of `{id,title,content:{type,value}}`) is
what is asserted, `uri` is what all eight shipped years already use, and no page's shape changed.
`tests/test_manifest.nim:406-426` asserts the shape and the eleven ids.

`grep -n '<slug>\|<IMAGE>\|<SEATS>'` over `ci.yml`, `coworld-release.yml`, `coworld-submit.yml`,
`docker_smoke.sh`, `policies.json` returns **zero hits** (the item-12 gate exits 0).

The coworld version is still `0.8.2` (phase 40's job, expected, not a finding).

**Checklist items:** 3 (static viewer declaration), 6 (`num_agents`), 10 (manifest validates), 12
(placeholder gate). **Satisfied.**

---

### F15 — `docker_smoke.sh` enforces all four seat-count invariants; no `SEAT-COUNT FAIL` in the log
**advisory (evidence FOR item 6)** — `tools/ci/docker_smoke.sh:82, 141-190`; CI job `102798775400`

Observed. `docker_smoke.sh` is **not in the diff** (unchanged from `6e89d0f`) and is mode `100755`
(`git ls-files -s` → `100755 b86ea23d…`). Its four invariants, all exiting non-zero with a
`SEAT-COUNT FAIL:` prefix:

1. `:145-153` — `certification.game_config.num_agents` present (missing → fail);
2. `:155-161` — a positive integer, `bool` excluded explicitly;
3. `:165-171` — `len(certification.players) == num_agents`;
4. `:172-176` — `len(certification.game_config.players) == num_agents`;

plus the independent second declaration at `:82` (`seats_expected="${SMOKE_SEATS:-2}"`) cross-checked
at `:181-187`, and `:199-204` refusing a `SMOKE_CONFIG_OVERRIDE` that changes `num_agents`.

`grep -c 'SEAT-COUNT FAIL' /tmp/smoke.log` over the whole `docker-smoke` job log at the reviewed sha:
**0**. The bc19 episode line reads
`game=battlecode seats=2 config={… "num_agents": 2, "year": "bc19", "pool": "small", "seed": 13, …}`
and closes `smoke OK: seats=2 results=1988B replay=17709B reason=complete`.

**Checklist item:** 6. **Satisfied.**

---

### F16 — Scripted baseline plays a full episode to `reason == "complete"` with every action legal
**advisory (evidence FOR item 7)** — `tests/test_bc19_baselines.nim:48-104`; `tests/test_bc19_survival.nim`; CI job `102798775400`

Observed.

- **Legality.** `tests/test_bc19_baselines.nim:71-77` asserts, on 3 seeds × 2 small maps,
  `refusedActions[t] == 0` for `saber` on **both** seats, `buildsRefused[t] == 0`, and
  `decisionOpsPeak[t] < TurnMaxOps`. `refused_actions` is incremented by every `BattlecodeError` the
  validation ladder in `actions.nim` raises, so zero means every emitted order was legal for the
  acting robot at the moment it was emitted — the actor's own type, adjacency, passability, occupancy,
  affordability, `r² <= SPEED`, the attack radius pair, `mine` only by a pilgrim on a depot under
  capacity, `give` bounds, `trade` castle-only, radio radius. `:106-125` additionally proves no CHURCH
  attack is ever emitted (legal upstream per D6.1, never a strategy), by running the real
  `runSaber` over every church turn of a 600-round game.
- **The weak floor's exemption is asserted as such.** `:103-104` asserts `weakRefused > 0`, so a
  future "fix" to the differential oracle's other side fails loudly.
- **Full episode, `reason == "complete"`.** The real all-scripted container episode is the
  `docker-smoke` bc19 step (`.github/workflows/ci.yml:4471-4489`), run with no `ANTHROPIC_API_KEY`;
  its log line at the reviewed sha is `smoke OK: seats=2 … reason=complete`. In-process,
  `tests/test_bc19_replay.nim:93` uses the design note's mandated tolerant form
  (`r.reason in [epDeadline, epComplete]`, L2171-2172) because the shard is runner-speed dependent.
- **Parameters tuned with a grid harness.** `tests/test_bc19_knobs.nim` sweeps twelve knob pairs over
  3 seeds × 3 maps with every threshold carrying its measurement (`:145-190`), and
  `tests/test_bc19_survival.nim:1-31` records the measured healthy mirror and the measured broken
  control side by side. The negative control is real: `tests/test_bc19_baselines.nim:127-145` runs the
  survival gate as a **subprocess** under `-d:bc19BrokenChassis` and asserts it comes back non-zero
  and fails on the economy, not on a compile error.
- **The across-the-pair substance floors held on the real episode** (`ci.yml:4517-4587`), measured in
  the log: `units=39 karbonite=3252 fuel=18590 deposited=3234 pilgrims=11 attacks=20 damage=200
  ids=43 queue=38` against floors 8 / 40 / 100 / 30 / 2 / 1 / 10 / 12 / 6.

**Checklist item:** 7. **Satisfied.**

---

### F17 — Rune-safe truncation is tested at the cap with multi-byte input; the escape used is 3-byte, not astral-plane
**advisory** — `tests/test_bc19_sheet.nim:150-168`; `src/battlecode/sim_types.nim:263-271, 378`

Observed. `tests/test_bc19_sheet.nim:150-168` feeds `repeat("\u1F3F0", 400)` into `notes` and `motto`
and asserts `runeLen <= MaxNoteRunes` (280) / `MaxMottoRunes` (48) and `validateUtf8(...) < 0` for
both; then asserts `MaxReplyBytes == 16 * 1024` and that `truncateBytes(huge, MaxReplyBytes)` of an
80 KB reply is `<= 16384` bytes **and** still `validateUtf8(...) < 0`. The caps are
`sim_types.nim:263-271` (`MaxNoteRunes 280`, `MaxMottoRunes 48`, `MaxFallbackDetailRunes 200`,
`MaxPromptRunes 4000`, `MaxPolicyLabelRunes 48`, `MaxReplyBytes 16*1024`) and every recorded string in
`decide.nim` goes through `sanitizeLine(..., MaxFallbackDetailRunes)` (`:1492-1493`) or
`truncateRunes` (`:1497`).

**The one thing that is not what the comment says:** the comment at `:153` reads
`## a castle emoji, 4 bytes each`, and the surrounding comment at `:151` says "INCLUDING astral-plane
characters". Nim's `\u` escape consumes exactly four hex digits, so `"\u1F3F0"` is U+1F3F (a 3-byte
UTF-8 rune) followed by the ASCII character `'0'` — not U+1F3F0. The test therefore exercises
**3-byte** multi-byte truncation, not astral-plane (4-byte) truncation. Design note §Tests item 14
(L2260-2261) asks for astral-plane characters specifically; checklist item 9 asks only for "multi-byte
input at the cap", which **is** satisfied. `tools/ci/renderer_fixture.html:59-62` makes the same
astral-plane claim; I did not verify which escape it uses.

**Checklist item:** 9 (rune-safe truncation). **Satisfied** as the checklist states it; the
astral-plane claim in the comment and in the design note is not what the code exercises. **Advisory.**

---

### F18 — Chrome provenance: `chrome_common.js` untouched, `replay_broadcast.html` is the starter page with a block appended
**advisory (evidence FOR item 14)** — `git diff 6e89d0f d2f5d3d -- client/`

Observed, and this is the mod-run form of item 14 (the "starter chrome" is this repo's own pre-bc19
chrome).

```
$ git diff --stat 6e89d0f d2f5d3d -- client/
 client/replay_broadcast.html | 726 +++++++++++++++++++++++++++++++-
 1 file changed, 721 insertions(+), 5 deletions(-)
```

`client/chrome_common.js` and `client/broadcast_core.js` are **not in the diff at all** — byte-identical
to the pre-bc19 tree. `tests/test_viewer.nim:31-36` still asserts both by sha256 against the
`coworld-ctf` copies, and that assertion is unchanged.

`client/replay_broadcast.html` grew from ~7 900 to ~8 600 lines; it is not a rewrite. There are eleven
hunks and **exactly five deleted lines**, all inside three widening hunks:

| `@@` | deleted | added |
|---|---|---|
| `-7018,7 +7730,7` | `'bc16-econ', 'bc16-units']` | `'bc16-econ', 'bc16-units', 'bc19-econ', 'bc19-units']` (the `--statrail` measured set) |
| `-7163,8 +7877,10` | `if (!isBc16 && … && !isBc25) {` | `if (!isBc16 && !isBc19 && … && !isBc25) {` + `if (window.Bc19Block) window.Bc19Block.onFrame(s);` |
| `-7175,8 +7891,8` | the same eight-way guard before `applyBeatSpoilers` | the same nine-way guard |

Every other hunk is pure addition. The appended block opens under a banner comment at
`client/replay_broadcast.html:3935-3945`:
`BC19 additions to the inherited cogame-battlecode chrome`, and the first thing it does (`:3947-4002`)
is hide the other eight years' 48 ids under `html[data-year="bc19"]` and its own six under
`html:not([data-year="bc19"])` — **nothing is removed from the page**.

**Transport rules, each checked in the page:**

- (a) `relayout()` sets `--band`/`--hudscale`/`--topband`/`--statrail` on `document.documentElement`
  (inherited, unmodified except for the two added ids at `:7730`).
- (b) Nothing fixed-positioned sits inside the band: `#bc19-units { bottom: calc(var(--band, 0px) + 76px) }`
  (`:4066`) and `#bc19-econ { bottom: calc(var(--band, 0px) + 8px) }` (`:4067`); `#bc19-castles`
  (`:4009-4016`) and `#bc19-fuel` (`:4037-4045`) are `top: calc(var(--topband, 0px) + 6px)` — top-band
  pills, deliberately not in the rail set; `#bc19-doctrines` (`:4097-4106`) is
  `max-height: min(46vh, calc(100% - var(--topband,0px) - var(--band,0px) - 46px)); overflow: auto`.
- (c) `#endcard { bottom: var(--band, 0px) }` and `#endcard.on { display: flex }` are the inherited
  rules at `:1847-1898`; every seek dismisses it — `seek(frac)` at `:7370-7373` calls
  `dismissEndcard()` before `send('s:'+…)`, and `:7760` dismisses on every transport button but
  `btn-loop`/`btn-skip`. `:4136-4141` adds
  `html[data-year="bc19"] #chrome:has(#endcard.on) #bc19-{castles,fuel,econ,units,doctrines} { visibility: hidden }`
  (endcard fix 5).
- (d) Beat markers are `<button>`s: `buildBc19BeatButtons` at `:6514-6535` does
  `document.createElement('button'); el.type='button'; el.className='beat-marker '+(b.k||'game');
  el.setAttribute('aria-label', b.label||b.k); el.title = …; el.addEventListener('click', … api.seek(b.t/span))`,
  with `applyBc19BeatSpoilers` at `:6537-6543`. It is named `buildBc19BeatButtons`, never `markBeat`
  (asserted at `tests/test_viewer.nim:1676`), and never collides with the eight sibling builders.

**`#viewpanel` is KEPT, and the note says to keep it.** Design note L1697-1708 decides this
explicitly: bc19 boards are square 32×32…64×64, rendered at 16 px/square = 512–1024 px, every one
larger than the 360 px featured-match frame, so this is *not* a fixed arena and item 14's
"drop `#viewpanel`" clause does not apply. `#viewpanel` is untouched in the diff (`:1510-1567`,
`:2598-2603`, `?viewpanel=0` still honoured).

**Checklist item:** 14. **Satisfied.**

---

### F19 — Viewer executes: `wasm-viewer` is green, `needs: docker-smoke`, runs the bc19 replay in headless chromium
**advisory (evidence FOR item 13)** — `.github/workflows/ci.yml:4677-4682, 4763-4909`; CI job `102800176614`

Observed.

- `wasm-viewer` at `:4677-4682` declares `needs: docker-smoke` explicitly, with the comment "The
  bundle is EXECUTED here, not merely built, and it is executed against the replay docker-smoke just
  produced".
- The step `Load the bundle in a real browser (ALL NINE years' replays)` (`:4763`) loops over nine
  `dist/smoke/replay*.json` candidates including `dist/smoke/replay-bc19.json` (`:4777`) and runs
  `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay "${replay}" --timeout 90
  --soak 10 --killfeed-overlap` for bc19 (the `else` arm at `:4850-4856`, i.e. the standard leash the
  note decided at L1736-1737). It is not commented out and carries no `continue-on-error`.
- Per replay the step then asserts `scrub_selector == "#scrub"` (`:4863-4871`), `#endcard` computed
  **shown** after the 100 % seek carrying a `clan` line (`:4878-4893`), and that no overlay covers
  > 50 % of the board after the soak (`:4899-4907`).
- The job log at the reviewed sha shows, for the bc19 replay,
  `{"loaded":true,"ms":305,"clock":"0:15 GAME 1 OF 1 — SEED-0043 doctrines","scorebug":"CLAN ASH Clan Ash · Mine, then march. 53 … CLAN BASIL Clan Basil · Mine, then march. 46","feed_lines":7}`.
- **Markers.** `replay-viewer/static_replay.js:180` sets
  `document.documentElement.setAttribute('data-replay-loaded','true')` from the worker's `loaded`
  message after the first board frame is composited, and `:14-20` sets
  `data-replay-error="<message>"` on any failure. Both come from the shell's own code paths, both
  unchanged in this run.
- **Emscripten bootstrap agreement.** `replay-viewer/config.nims:44-52` has **no `MODULARIZE`, no
  `EXPORT_NAME`** (the `passL` block is `-o bc_replay.js --preload-file …@data -O2
  -s ALLOW_MEMORY_GROWTH -s ABORTING_MALLOC=1 -s FILESYSTEM=1 -s ENVIRONMENT=web,worker,node
  -s EXPORTED_RUNTIME_METHODS=HEAPU8 -s EXPORTED_FUNCTIONS=…`), and the worker bootstraps the
  matching non-`MODULARIZE` way: `Module.locateFile` (`static_replay_worker.js:209`),
  `Module.onRuntimeInitialized = …` (`:218`), and
  `importScripts('./wire_constants.js','./broadcast_core.js','./bc_replay.js')` at the end of the file
  (`:274`). Shell and link flags come from the same starter and agree — the cogame-lantern deadlock is
  not present. Neither file is in the diff.
- **Lobby clause.** This repo does not record a pre-game lobby: every year's frame record sets
  `"st": 0` (`src/battlecode/broadcast.nim:717, 845, 1038, 1255, 1437, 1636, 1686, 1929, and 2190` —
  the last being bc19's), and `chrome_common.js:479-483, 517, 706-709` builds the scrubber axis from
  `Math.max(0, s.st || 0)`. With `st == 0` playback opens at the game start by construction. The
  bc19 beat-button code uses `(b.t - (s.st||0))/span` for `left` (`:6523-6524`) and `b.t/span` for the
  seek fraction (`:6530`); these differ only when `st > 0`, which cannot happen here, and the same two
  expressions appear in all eight sibling year blocks (`api.seek(b.t / span)` at `:4545, 4847, 5151,
  5495, 5782, 6083, 6530, 6938`) — so this is inherited shape, not a bc19 regression. Noted as an
  observation, not a defect.
- **No pod path.** `grep -rn "/client/replay"` over the repo returns exactly one hit,
  `.github/workflows/coworld-release.yml:220`, which is the *refusal* message
  `"/client/replay viewer is not acceptable."`. The only network call in the whole bundle is
  `fetch(message.replayUrl, …)` at `replay-viewer/static_replay_worker.js:127` — the S3 replay
  fetch and nothing else.

**Checklist item:** 13 (viewer executes) and 3 (static viewer). **Satisfied.**

---

### F20 — Legibility at 360 px, and the worst-case renderer fixture with `--strict-text-bounds`
**advisory (evidence FOR items 11 and 15)** — `client/replay_broadcast.html:2623, 4166-4178`; `.github/workflows/ci.yml:5005-5031`; `tools/ci/renderer_fixture.html`

Observed.

- **Item 11.** `client/replay_broadcast.html:2623` is
  `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` — inherited, in the diff's untouched
  region. The bc19 media query at `:4166-4178` is `@media (max-width: 640px)` and drops word labels to
  glyphs (`#bc19-econ .lbl, #bc19-units .lbl { display: none }`) while `#bc19-fuel` keeps both bars,
  the delta and the round counter, which is what the note L1777-1778 requires.
  `viewer_smoke.mjs --killfeed-overlap` runs on the bc19 replay at 360 / 720 / 1280 px at FIT and 2×
  zoom (`ci.yml:4796-4803`, `:4855`).
- **Item 15, the fixture.** `.github/workflows/ci.yml:5005-5031` is its own step,
  `Render the full-cap doctrine-text fixture`: it extracts the page's own `<style>` block from
  `client/replay_broadcast.html` at run time into `dist/fixture/page_styles.css` (208 275 bytes from 1
  block, per the log), serves it over HTTP, and drives it with
  `node tools/ci/viewer_smoke.mjs --url http://127.0.0.1:8099/renderer_fixture.html --timeout 60
  --strict-text-bounds --out dist/fixture`. The bc19 row is present:
  `tools/ci/renderer_fixture.html:71` (`YEARS = [… 'bc16', 'bc19']`), `:82-83`
  (`SUPPRESSED_BY_ENDCARD.bc19`), `:600-752` (the `BC19_WORDS` block and all six readouts at full
  cap), `:800, 818, 895-902` (the DOM).
- **The fixture asserts its own strings are still full-length**, `:990-999`:
  `if (runes(ecMottos[em].textContent).length !== MAX_MOTTO_RUNES + 2) endcardFault = 'the endcard
  motto on seat ' + em + ' was shortened before it was measured'`. It also raises `#endcard.on` and
  reads computed `visibility` off the browser for HUD bleed-through, and asserts every band keeps its
  own line and stays inside the scrollport (`:940-985`), and flags any node with
  `scrollWidth > clientWidth + 1` (`:1071-1075`). It sets `data-replay-loaded` (`:158`, `:1135`) and
  `data-replay-error` on the first failure, which is what the harness gates on.
- **`canvas_text` line, cited as the checklist asks.** The fixture step's log line at the reviewed sha
  is `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)`, and every one of the nine replay runs prints
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.

  **Why `total: 0` is accurate here rather than a blind spot:** this viewer draws **no text on the
  canvas at all**. `grep -c 'fillText\|strokeText' client/broadcast_core.js` = **0**. The board canvas
  draws terrain, pips, sprites, health bars and blast overlays; every string a spectator reads —
  scorebug plates, clock, `#bc19-*` readouts, killfeed, doctrine panel, endcard — is DOM under the
  page's own CSS. So `canvas_text` measures a surface that does not exist, and the DOM-overflow
  assertions inside the fixture are the ones that carry the weight. `--strict-text-bounds` is
  correctly dropped on the replay runs (the board is pannable, `#viewpanel` kept) with the reason
  written into `ci.yml:4787-4795`.

  Inferred, not observed: `never_inside` gating is therefore vacuous for this repo, and the real
  legibility gate is the fixture's own DOM assertions plus `--killfeed-overlap`. I record this so the
  judge reads the `0` correctly rather than as either a pass or a gap.

**Checklist items:** 11 and 15. **Satisfied.**

---

### F21 — Release order, workflows and policies
**advisory (evidence FOR item 12)** — `.github/workflows/coworld-release.yml`; `tools/ci/policies.json`

Observed. `coworld-release.yml`'s single `release` job runs its steps in this order:
`Build the Coworld manifest` (`:168`) → `Certify locally` (`:182`) → **`Upload the policies` (`:225`)**
→ `Upload the Coworld` (`:323`) → `Wait for the uploaded version to become canonical` (`:361`) →
`Put the Coworld secret` (`:419`). That is build → certify → upload-policies → upload-coworld →
secret put. There is no smoke step in the release workflow. All three workflows are present and
`active` (`ci.yml`, `coworld-release.yml`, `coworld-submit.yml`). `tools/build_replay_viewer.sh` and
`tools/ci/docker_smoke.sh` are both mode `100755`.

`tools/ci/policies.json` carries **36** entries (32 → 36, four per year × nine years). The four bc19
entries, at indices 32–35:

| # | name | env | `player` | image |
|---|---|---|---|---|
| 32 | `battlecode-bc19-saber` | `PLAYER_PROMPT` + `PLAYER_POLICY_LABEL` | — | `cogame-battlecode-player:latest` |
| 33 | `battlecode-bc19-preachers` | `PLAYER_PROMPT` + `PLAYER_POLICY_LABEL` | **`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`** | same |
| 34 | `battlecode-saber` | `PLAYER_SCRIPTED=saber` | — | same |
| 35 | `battlecode-examplefuncsplayer19` | `PLAYER_SCRIPTED=examplefuncsplayer19` | — | same |

Two LLM prompt champions plus two scripted fillers, champion #2 (the second `PLAYER_PROMPT` entry)
carrying the required player id — asserted mechanically at `tests/test_manifest.nim:639-666`, which
also asserts the two prompts differ and each names its own pole. The placeholder gate exits 0 (F14).

**Checklist item:** 12. **Satisfied.**

---

### F22 — Both name spaces present
**advisory (evidence FOR item 4)** — `src/battlecode/decide.nim:791-792`; `src/battlecode/broadcast.nim:2210-2211`; `client/replay_broadcast.html:7395, 7665, 7700`

Observed. The per-seat observation carries only aliases: `decide.nim:791-792` is
`"alias": aliasFor(slot), "opponent_alias": aliasFor(1 - slot)` and there is no `names[` read anywhere
in `decide.nim`. `AliasA`/`AliasB` are `"Clan Ash"`/`"Clan Basil"` in `sim_types.nim:240-241`,
untouched by this run.

The spectator side has both: the bc19 chrome record at `broadcast.nim:2210-2211` emits
`"aliases": [AliasA, AliasB]` **and** `"names": [doc.names[0], doc.names[1]]`, and the page draws the
real name in the scorebug plate sub-line (`client/replay_broadcast.html:7395`
`var name = (s.names && s.names[slot]) || '';`), in the endcard headline (`:7665`
`(s.aliases[winner] + ' — ' + s.names[winner]).toUpperCase()`) and in the doctrine panel (`:7700`).

**Checklist item:** 4. **Satisfied.**

---

### F23 — Cross-year scope: exactly the two authorised edits, plus additive registration
**advisory** — `git diff --name-only 6e89d0f d2f5d3d -- src/battlecode/years/`; `.github/workflows/ci.yml:179`

Observed. Under `src/battlecode/years/`, the only non-`bc19/` files in the diff are
`dispatch.nim` (+135, no deletions beyond widened `case` arms) and `registry.nim` (+5 −1, one
`YearSpec` line). The shared-file deletions (F2's counterpart in `src/`) are all
"add `isBc19`/`yBc19` to an existing set" rewrites:

- `broadcast.nim:198-199, 205-206` — `isBc25 or isBc23 or isBc22 or isBc16` → `… or isBc19` for
  `first_action` and `rout`;
- `broadcast.nim:379-401, 400-412, 446-462` — `duel`, `unit_milestone` and `tiebreak` labels gain a
  bc19 branch **in front of** the existing one; the bc16/bc22/bc23 wording is preserved verbatim in
  the `else`/`elif` arms;
- `match.nim:695` — `winBonusFor` set `{yBc25, yBc23, yBc22, yBc16}` → `{…, yBc19}`;
- `sheet.nim` — one arm each in `knownKeysFor`/`defaultSheet`/`validate`/`toJson`/`plainWords`; the
  envelope resolver is untouched;
- `sim_types.nim:16, 253-254` — GV11 → GV12 and the compat list **extended**.

The two authorised cross-year edits are both present and are the only ones:
1. the GV12 fixture regeneration (F3);
2. `ci.yml:179` `timeout-minutes: 180` (was 150 — note the design note L162-164 and L2163 said 165;
   the tree says 180 and the builder records this as ruling 3. The `test` job at the reviewed sha ran
   08:23:06Z → 09:33:14Z, ~70 min, so 180 is not covering a slow job that 165 would have failed. This
   is a divergence from the design note's stated number, documented in the build report; **advisory**).

**I found no third cross-year edit.** The sibling parity comparator zip-tail/`toHex` bugs in
bc20/21/24/25 and `match.nim`'s `max(1, min())` clamp are untouched, as ruled — `match.nim`'s diff
contains no change to `perGame`.

`Dockerfile` and `Dockerfile.replay-viewer` are not in the diff at all, so the "no Node, no npm, no JS
runtime, no JDK in any image stage" rule holds by construction.

**Checklist item:** none names cross-year scope. **Advisory.**

---

### F24 — `docs/PARITY.md` §bc19 §Status cites the branch run, not the run at the reviewed sha
**advisory** — `docs/PARITY.md:2093-2110`

Observed. §Status opens *"The first run taken as a verdict is **`34446572285`** — job
`parity-oracle-bc19`, id `102772780365`, on `bc19-year-module` at `7aa8e6712c`, conclusion `success`"*.
The reviewed sha is `d2f5d3d707` on `main`, whose `parity-oracle-bc19` job is `102798775171` and is
also `success` with the identical `compared 54 whole-game pairs, 0 failure(s)` and 54 `BIT-EXACT`
lines (F8). So the substance is true at the reviewed sha; the citation names a different run and a
different sha. It is a documentation nit, not a false claim — the `[]` ledger and the 54/54 result are
both reproducible at `d2f5d3d707` from the log I read.

**Checklist item:** none. **Advisory.**

---

## Checklist item-by-item evidence

| # | item | verdict | evidence |
|---|---|---|---|
| **1** | CI green, no test loosened | **met** | Run `34454858348` `success` on `main` at `d2f5d3d707`, 12/12 jobs (F1). `git diff -- 'tests/*.nim'` deletes 20 lines, all count/arity widenings replaced by stricter assertions in the same hunk; no assertion deleted, no tolerance widened, no skip added, no test file removed (F2). The three regenerated fixtures changed exactly two leaves each, both `game_version` GV11→GV12, assertions pinned to the `GameVersion` symbol (F3). |
| **2** | Replay re-derivation, frame by frame, viewer uses the same re-derivation, a test asserts it | **met** | `tests/test_bc19_replay.nim:388-394` runs `newDeriver(fx)` over the committed fixture to its last round and asserts `mismatchRound == -1` and `frames >= rounds`; `replay.nim:303-312` sets `mismatchRound` on the first divergent round. `replay-viewer/bc_replay.nim:88,153` runs the **same** `Deriver` and exposes `bc_mismatch_round`. Nothing per-tick is stored (`test_bc19_replay.nim:121-136`). CI: `mismatch_round: -1` for both bc19 replays in job `102800176614` (F13). |
| **3** | Static viewer bundle declared, build hook present + wired, S3 only, no pod path | **met** | `"replay_viewer": {"bundle": "static-replay-viewer"}` (F14). `tools/build_replay_viewer.sh` mode `100755`, invoked by path in `ci.yml`'s `wasm-viewer` after an explicit exec-bit assertion (`:4695-4700`). Only network call in the bundle is `fetch(replayUrl)` at `static_replay_worker.js:127`. `grep -rn "/client/replay"` → one hit, the refusal message in `coworld-release.yml:220` (F19). |
| **4** | Both name spaces | **met** | Agents see aliases only (`decide.nim:791-792`); viewer draws `s.names[slot]` in scorebug, endcard and doctrine panel (`replay_broadcast.html:7395, 7665, 7700`); both emitted at `broadcast.nim:2210-2211` (F22). |
| **5** | Degrade-never-hang, settles inside 60 % of `episodeTimeoutSeconds` | **met** | 305 s worst case against 720 s, every term a shipped config value (F11). LLM waits bounded at `decide.nim:1402, 1423, 1441-1442, 1460`; game loop bounded at `rules.nim:425-432, 582-590`; the one `while true` (`world.nim:363`) is the engine's id-rejection loop, guarded by V4 at `actions.nim:217-220` on its only unbounded call site (F12). No blocking read in `years/bc19/`. |
| **6** | `num_agents` in every variant and the cert fixture; four smoke invariants; `SMOKE_SEATS` second declaration; no `SEAT-COUNT FAIL` in the log | **met** | `num_agents: 2` in all nine variants' `game_config` and in `certification.game_config`, never at variant top level (F14). `docker_smoke.sh:145-176` enforces all four invariants with the `SEAT-COUNT FAIL:` prefix; `:82` + `:181-187` is the `SMOKE_SEATS` cross-check; `:199-204` refuses an override that changes it. `grep -c 'SEAT-COUNT FAIL'` over job `102798775400`'s whole log = **0** (F15). |
| **7** | Scripted baseline plays full episodes legally; `reason == "complete"`; parameters tuned with a grid harness | **met** | `docker-smoke` bc19 episode (all-scripted, no API key) → `smoke OK: seats=2 … reason=complete`, plus nine across-the-pair substance floors all cleared on the real replay. `test_bc19_baselines.nim:71-77` asserts `refused_actions == 0` for `saber` on both seats over 6 games, `builds_refused == 0`, `decision_ops_peak < TurnMaxOps`; `:106-125` proves no CHURCH attack is ever emitted; `:127-145` runs the survival gate inverted as a subprocess and requires it red. Grid harness: `test_bc19_knobs.nim` sweeps twelve knob pairs over 3 seeds × 3 maps with every threshold carrying its measurement (F16, F6). |
| **8** | Tolerant parse, retry once, fall back to scripted, fallback recorded | **met** | `decide.nim:1395-1520`, traced in F10: `while … attempt < 2`, `attempt1Ms` then `retryMs`, `parseReply` through the fence-tolerant extractor, `doctrine_retry` with a typed cause, then `doctrine_fallback` + `result.fallback[slot]` + the `falling back` log line. No-credentials is recorded as a fallback, not relabelled scripted. |
| **9** | Rune-safe truncation, tested at the cap with multi-byte input | **met** | `test_bc19_sheet.nim:150-168`: multi-byte input at the cap for `notes` and `motto`, `validateUtf8 < 0` asserted on both, `MaxReplyBytes == 16384`, `truncateBytes` of an 80 KB reply `<= 16384` and still valid UTF-8. The comment's "astral-plane / 4 bytes each" claim does not match the escape used (`\u1F3F` + `'0'`, 3-byte runes) — advisory only (F17). |
| **10** | `game.docs` shape; `game.protocols` carries both `player` and `global` | **met** | Both protocol keys present and identical URIs; `docs.readme` is a `{type, value}` object; all eleven pages are `{id, title, content:{type,value}}` (F14). Asserted at `tests/test_manifest.nim:406-426`. |
| **11** | Viewer legible at 360 px; `.plate-name { flex: 1 1 auto; min-width: 3.2em }`; labels hidden under 640 px | **met** | `replay_broadcast.html:2623` (inherited, unmodified) and the bc19 `@media (max-width: 640px)` block at `:4166-4178` which hides `.lbl` and keeps `#bc19-fuel`'s bars, delta and round counter. `--killfeed-overlap` runs on the bc19 replay at 360/720/1280 px at FIT and 2× (F20). |
| **12** | Release order; three workflows; `docker_smoke.sh` executable; ≥ 4 distinct policies with champion #2's player id; placeholder gate exits 0 | **met** | build → certify → upload-policies → upload-coworld → secret put at `coworld-release.yml:168, 182, 225, 323, 419`. 36 policies, bc19's four at 32–35, champion #2 carrying `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`. Placeholder grep over the five named files: **zero hits** for `<slug>`/`<IMAGE>`/`<SEATS>`; the four documented residue names (`<cow_id>`, `<sha>`, `<run_id>`, `<name>:vN`) are the only angle-bracket survivors and are expected (F21, F14). |
| **13** | Viewer executes: `wasm-viewer` green including the browser smoke step, `needs: docker-smoke`; both `data-replay-*` markers; playback opens at game start; link flags and bootstrap from the same starter | **met** | Job `102800176614` `success`; `needs: docker-smoke` at `ci.yml:4682`; the `Load the bundle in a real browser (ALL NINE years' replays)` step at `:4763` includes `dist/smoke/replay-bc19.json` and printed `{"loaded":true,"ms":305,…}` for it. `data-replay-loaded` at `static_replay.js:180` (first drawn frame), `data-replay-error` at `:14-20`. No `MODULARIZE`/`EXPORT_NAME` in `config.nims:44-52`; worker uses `Module.onRuntimeInitialized` + `importScripts` (`:218, 274`) — same starter, agreeing. `st == 0` in every frame record (`broadcast.nim:2190` for bc19), so there is no recorded lobby to dwell through (F19). |
| **14** | Chrome is the starter's, not a lookalike | **met** | `client/chrome_common.js` and `client/broadcast_core.js` **not in the diff**; sha256 assertions at `tests/test_viewer.nim:31-36` unchanged. `client/replay_broadcast.html` = the existing page with a bc19 block appended under the banner `BC19 additions to the inherited cogame-battlecode chrome` (`:3936`); five deleted lines in the whole file, all eight-way → nine-way widenings. Transport rules (a)–(d) all checked in the page. `#viewpanel` **kept**, which is correct because design note L1697-1708 says the board (512–1024 px) is larger than the 360 px frame (F18). Beat CSS: all twelve kinds scoped, asserted at `test_bc19_beats.nim:183-188` (F4). |
| **15** | Every drawn string fits its frame; worst-case renderer fixture driven by `--strict-text-bounds` in its own step; cite the step and its `canvas_text` line | **met** | Step `Render the full-cap doctrine-text fixture`, `ci.yml:5005-5031`, `--strict-text-bounds`, page CSS extracted from `client/replay_broadcast.html` at run time (208 275 bytes, 1 block). `canvas_text` line at the reviewed sha: `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. `total: 0` is accurate rather than blind: `grep -c 'fillText\|strokeText' client/broadcast_core.js` = **0** — this viewer draws no canvas text at all; every string is DOM, and the fixture's own DOM assertions (overflow, HUD bleed-through, endcard bands, `runes(motto) == MAX_MOTTO_RUNES + 2`) are the gate. bc19 row present at `renderer_fixture.html:71, 82-83, 600-752` (F20). |
| **batch rule** | all seats' LLM calls go out as one parallel batch per turn | **met** | One `RequestBatch`, one `makeRequests` call per attempt, both seats appended before it (`decide.nim:1443-1460`). bc19 has exactly one decision turn per episode. No sequential per-seat request path exists (F10). |

**Blocking-candidates: 0.**

---

## Traced and consistent (not separately numbered)

- `src/battlecode/years/bc19/rules.nim:465-478` — `endReasonFor` raises a `Defect` rather than
  mislabelling an impossible ladder state; the message names the rung it refuses to invent.
- `src/battlecode/years/bc19/rules.nim:378-403` — the per-round fold mixes thirteen per-team
  quantities, the round, `robin`, the shadow hash, the queue-order hash, the queue length, the spent-id
  count, both `last_offer`s packed, the MT19937 `stateFold()` **and** `mti`. `tests/test_determinism.nim`
  (bc19 block) proves the `mti` fold is load-bearing by consuming exactly one extra draw and showing
  every other folded quantity identical while the chain still diverges.
- `src/battlecode/match.nim:345-575` — every bc19 event arm is additive; `first_action` uses the field
  name **`action`**, never `kind` (`:349-352`), which is the bc23 r1-F25 lesson honoured.
- `src/battlecode/years/bc19/world.nim:393-407` — `deleteRobot` splices and decrements `robin` when
  the removed index is below it, matching `game.js:939-942`.
- `src/battlecode/years/bc19/actions.nim:214-220` — V4's guard increments `builds_refused` and raises,
  so a refusal is counted and visible rather than silent.
- `tools/oracle/bc19/bc19_trace.js:391-424` — exit 3 on "nothing happened", exit 6 on the Tier B′(a)
  clock assertion, exit 7 on a `--expect-freeze` run that did not freeze or froze more than ±3 turns
  from `CHESS_INITIAL / (40 − CHESS_EXTRA)`.
- `.github/workflows/ci.yml:3517-3567` — every `node` and every Nim binary invocation wrapped in
  `timeout 600`; `fails` accumulated and `test "${fails}" -eq 0` closes the step; traces deleted after
  comparison, only a gzipped digest uploaded.
- `tests/test_manifest.nim:232-262` — the assertion that proves this run moved no `config_schema`
  bound: bc19's `maxRounds 1000`, `gamesPerMatch 3`, `perGameBudgetSeconds 60`, `matchBudgetSeconds
  200` all read against the **unchanged** maxima.
- `tests/test_viewer.nim:1704-1820` — the six bc19 ids present, `#bc19-doctrines` dismissible
  (`bc19-doctrines-close`, an Escape binding scoped by `getAttribute('data-year') !== 'bc19'`, a
  re-open chip) and capped-and-scrolling, `#bc19-econ`/`#bc19-units` lifted above `var(--band)` by
  their exact CSS text, `--statrail` naming both, and every `#bc19-*` rule scoped to the year.

---

## Could not determine

1. **Whether `famine` is emitted by any shipped chassis in a real episode.** I proved it is unreachable
   for `saber` (F4) and that the branch exists and is reachable in principle for an order whose store
   hits zero on a refused action. I did not find a committed artefact in which it fires. What would
   settle it: a recorded `examplefuncsplayer19`-vs-`examplefuncsplayer19` or LLM episode replay whose
   `events` contain a `famine` record — the 600-round smoke replay is not in the repo and I did not
   download the CI artifact.
2. **Whether `tools/ci/renderer_fixture.html`'s own "astral-plane" strings really are 4-byte runes.**
   I verified the claim is wrong in `tests/test_bc19_sheet.nim:153` (Nim `\u` takes 4 hex digits) but
   did not read the fixture's JS string literals, where `\u{...}` or a surrogate pair would make the
   claim true. What would settle it: reading `tools/ci/renderer_fixture.html`'s `runes()` helper and
   the literals it fills `notes`/`motto` with.
3. **The 4 094-spent-ids edge of `drawId`.** Terminating with probability 1 is not the same as
   bounded, and the design note's own per-side unit ceiling (≈ 2 400) doubles to above the 4 095 pool.
   What would settle it: a `tests/test_bc19_mt.nim` vector that pre-fills 4 094 ids and asserts the
   loop's draw count, or a bound in `drawId` itself. Measured reality (43 ids in the smoke, ~140 units
   per mirror game) is nowhere near it, and `builds_refused == 0` is asserted on every gate game.
4. **Whether the `test` job needed 180 rather than the design note's 165 minutes.** The reviewed run's
   `test` job took ~70 min. What would settle it: a run at 165 on the same tree — which I would not
   ask for, since a headroom bump is not a loosened test.
