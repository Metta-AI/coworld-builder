# r1 review — battlecode-2017

Range: `f0570643..07ad48cc` (124 files, +22597/-90) on `Metta-AI/cogame-battlecode` `main`
Files read: 46 source/config/doc/test files in the repo at `07ad48cc`, plus 4 CI job logs
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the
simultaneous-decision parallel-batch clause)
CI evidence: run **34536659753** (`ci.yml`, `main`, head_sha
`07ad48cc68718c8a2c6ce066903e5e5cbc6f49da`, `run_attempt: 1`, conclusion `success`, 13/13 jobs).
Job logs fetched and grepped: `docker-smoke` (103069753218), `wasm-viewer` (103071212587),
`parity-oracle-bc17` (103069753312), `test` (103069753174).

Findings are numbered **F1…F15** for the fixer. Every one cites `file:line`. Observations are
labelled *observed* (I read it), *inferred* (I reasoned from what I read) or *untested* (needs a
run to settle).

---

## Checklist verdict, item by item

| # | item | verdict | where the evidence is below |
|---|---|---|---|
| 1 | CI green, no test loosened | **satisfied** | run 34536659753 `success`, 13/13; `git diff … -- tests/` read hunk by hunk — additive only |
| 2 | Replay re-derivation, a test asserts it | **FALSIFIED — F1** | no `tests/test_bc17_replay.nim`; `test_determinism.nim`/`test_replay.nim` untouched and bc26-anchored; CI covers 200 frames |
| 3 | Static viewer | **satisfied** | manifest `:14-16`; `build_replay_viewer.sh` present + executable; `test_seats.nim:77-78`; no pod route |
| 4 | Both name spaces | **satisfied** | fixture `aliases`/`names`; `broadcast.nim:2523-2524`; `sim_types.nim:246-247` untouched |
| 5 | Degrade-never-hang, inside 60 % | **satisfied** | 435 s ≤ 720 s from the variant's own budgets; `decide.nim:1584,1604,1623-1642`; only two `while true`, both bounded |
| — | one parallel batch per turn | **satisfied** | `decide.nim:1625-1642`, a single `makeRequests` |
| 6 | `num_agents` | **satisfied** | 10/10 variants + cert fixture; `docker_smoke.sh:145-186`; **`SEAT-COUNT FAIL` count in the log = 0**; ten episodes `seats=2 reason=complete` |
| 7 | Scripted baseline plays full episodes legally | **satisfied on legality; the grid-harness half UNVERIFIED** | `test_bc17_baselines.nim:121-127,150-155`; episode `reason=complete` from docker-smoke log 3533; no grid harness anywhere in the tree — see "Could not determine" |
| 8 | LLM reply handling | **satisfied** | `decide.nim:1604` (`attempt < 2`), `:1676-1681` retry, `:1690-1702` fallback, `results.nim:78,97` counts it |
| 9 | Rune-safe truncation + test | **satisfied** | `test_bc17_sheet.nim:157-182`, astral input at the cap, `validateUtf8`, `len mod 4 == 0` |
| 10 | Manifest validates | **satisfied** (literal `"type":"text"` mismatch noted as F14) | `game.docs` readme + 12 pages `{id,title,content:{type,value}}`; both `protocols` keys |
| 11 | Legible at 360 px | **satisfied** | `:2623` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; 640 px label hiding; killfeed-overlap gate green on the bc17 replay |
| 12 | Release order and scaffold | **satisfied** | build→certify→**upload-policies**→upload-coworld→secret (`:168,182,225,323,419`); 40 policies, champion #2 owned; placeholder gate exits 1 |
| 13 | Viewer executes | **satisfied**, except the late-`gameStart` probe which is **UNVERIFIED** | wasm-viewer green, `needs: docker-smoke` (`ci.yml:5353`), bc17 `loaded:true`, both markers present, no `MODULARIZE` vs `onRuntimeInitialized` bootstrap — matched |
| 14 | Chrome is the starter's | **satisfied** | `chrome_common.js`/`broadcast_core.js` byte-identical to `f0570643`; page `+463/−3`, all three removals widened in place; `#viewpanel` kept |
| 15 | Every drawn string fits its frame | **FALSIFIED — F2** (caveat stated) | `renderer_fixture.html:70-71` lists nine years, not bc17; the step ran and reported `canvas_text 0 drawn` |

Findings: **15** (F1–F15). Falsifying a numbered item: **F1** (item 2) and **F2** (item 15).
Everything else is advisory.

---

## Blocking

### F1 — bc17 is the only year module in the repo with no replay re-derivation test
- Where: `tests/` (directory listing at `07ad48cc`); `.github/workflows/ci.yml:5669`, `:5675`,
  `:5687`; `tests/test_bc16_replay.nim:90-91`
- Observed: every other shipped year carries `tests/test_bcNN_replay.nim` —
  `test_bc16_replay.nim`, `test_bc19_replay.nim`, `test_bc20_replay.nim`, `test_bc21_replay.nim`,
  `test_bc22_replay.nim`, `test_bc23_replay.nim`, `test_bc24_replay.nim`, `test_bc25_replay.nim`.
  **`tests/test_bc17_replay.nim` does not exist.** `tests/test_bc16_replay.nim:90-91` is the
  shape that is missing:
  ```
  checkEq("and the recording re-derives with NO hash mismatch", r.mismatch, -1)
  checkEq("the bytes are STRICT UTF-8", r.text.validateUtf8(), -1)
  ```
  I grepped all 23 committed `tests/test_bc17_*.nim` plus `tests/bc17_fixture.nim` for
  `hashChain|hash_chain|reDerive|ReplayDoc|writeReplay|parseReplay|mismatch`: the only hit is
  `tests/bc17_fixture.nim:86` (`fixtureReplay*(): ReplayDoc = parseReplay(...)`), a loader, not an
  assertion. `tests/test_replay.nim` and `tests/test_determinism.nim` were **not touched by this
  diff** (`git diff --stat f0570643..07ad48cc -- tests/` lists neither) and both are bc26-anchored:
  `test_determinism.nim:254-257`'s per-year loop is `[bc26, bc20, bc21, bc24]` only, and
  `test_replay.nim:15-48` is bc26-only. The design note's §Tests item 25 and item 26 both required
  bc17 coverage here.
  The strongest re-derivation evidence that does exist is CI-side and bounded: `wasm-viewer`
  ran `tools/wasm_replay_smoke.cjs` against `dist/smoke/replay-bc17.json` and
  `tests/fixtures/replay-bc17.json` and both reported
  `{"loaded":true,"game_version":"GV13","first_packet_bytes":65430|548837,"frames":200,"mismatch_round":-1}`
  (wasm-viewer log lines 2768, 2770). `ci.yml:5687` says so in its own words:
  *"NOTE that this smoke steps 200 FRAMES, so its `mismatch_round: -1` covers the first 200 rounds
  only."* For bc16 and bc19 `ci.yml:5669` names the test that closes the gap
  (*"the WHOLE-recording re-derivation is asserted by tests/test_bc16_replay.nim"*); for bc17 at
  `:5687` the sentence simply stops, because there is no such test.
- Checklist item: **2 — Replay re-derivation.** "Replaying the recorded events through the sim
  reproduces the recorded per-tick state **frame by frame**, and the viewer derives its display
  from that same re-derivation — not from a parallel recording. **A test asserts it.**"
- Why blocking: the re-derivation of a bc17 recording is asserted for 200 of up to 8 997 rounds,
  and only in CI, never by a test. Nothing asserts the strict-UTF-8 parse of the written bc17
  bytes, the per-event-kind bounds (§Tests 26 lists eleven claims), `plan.maps` carrying all three
  drawn maps on a two-game clinch, `sheet_envelope`/`sheet_submitted` round-tripping, or
  record→re-derive for the `abandoned`/`deadline` path. bc17 is also the *only* float32 year, which
  is exactly where a narrowing difference between the native recorder and the wasm re-deriver would
  live (`ci.yml:5680-5686` says this out loud), and the frame budget the smoke covers is 200.

### F2 — the worst-case LLM-text renderer fixture does not cover bc17
- Where: `tools/ci/renderer_fixture.html:70-71`; `.github/workflows/ci.yml:5706-5732`;
  wasm-viewer log line 2831
- Observed: `tools/ci/renderer_fixture.html` is **not in this diff at all**
  (`git diff --stat f0570643..07ad48cc -- tools/ci/renderer_fixture.html` is empty) and
  `grep -c bc17 tools/ci/renderer_fixture.html` returns **0**. Its year list is
  ```
  70:  var YEARS = ['bc26', 'bc20', 'bc21', 'bc24', 'bc25', 'bc23', 'bc22',
  71:               'bc16', 'bc19'];
  ```
  — nine years, and the tenth is the one under review. The fixture's own comment at `:65-68`
  states the reason the list has to be complete: *"each year's readouts are different elements
  under different CSS and a fixture that only lays out bc26 says nothing about bc20's flood, soup,
  unit and doctrine panels…"*. Its `SUPPRESSED_BY_ENDCARD` map at `:79-84` likewise has `bc16` and
  `bc19` and no `bc17`. The CI step exists and runs with the flag
  (`ci.yml:5728-5732`: `node tools/ci/viewer_smoke.mjs --url …/renderer_fixture.html --timeout 60
  --strict-text-bounds --out dist/fixture`) and passed, reporting
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
  (--strict-text-bounds)` (wasm-viewer log 2831) — but it laid out nine years' boxes and never
  bc17's. bc17 *does* draw model-authored text: `#bc17-doctrines` renders `notes` and the
  plain-words clauses (`client/replay_broadcast.html:8323-8344`) and the scorebug plate renders
  `motto` (visible in the CI endcard capture at wasm-viewer log 2593). The design note's
  §Tests (`wasm-viewer` job) required it in one sentence: *"The fixture gains a **bc17 row**."*
- Checklist item: **15 — Every drawn string fits its frame**, final bullet: *"A repo whose viewer
  draws LLM-authored text must therefore ship a worst-case renderer fixture … Cite the step and its
  `canvas_text` line; a repo that draws model text and has no such fixture is a blocking
  `legibility` finding."*
- Why blocking: bc17's `#bc17-vp`, `#bc17-bullets`, `#bc17-econ`, `#bc17-units` and
  `#bc17-doctrines` are the only chrome in the repo that has never been laid out at
  `MaxNoteRunes`/`MaxMottoRunes` at 360 / 720 / 1280 px. Every CI replay is scripted and carries the
  short baseline strings (`"default orchard doctrine"` / `"Plant, water, donate."` —
  `src/battlecode/baselines.nim:265-276`, and visible in the CI scorebug capture), which is exactly
  the cogchemists case the item was written for.
  **Honest caveat for the judge:** the item's literal wording is "has no such fixture", and the
  repo *does* have one and *does* run it with `--strict-text-bounds`. A judge who reads the
  sentence literally will dismiss this; a judge who reads its purpose will not. I file it because
  the year under review is the one the fixture does not reach. Secondary note: the fixture's
  `canvas_text.total` is `0`, which checklist item 15 says "means the check covered nothing … and
  is not evidence of anything" — but that is *inferred* to be correct behaviour here, not a defect:
  the fixture's real gate is DOM overflow (`renderer_fixture.html:1071-1075`, `scrollWidth >
  clientWidth`), the chrome is DOM and the board canvas is not in the fixture.

---

## Non-blocking

### F3 — the bc17 endcard HUD-suppression rule keys on a class nothing ever sets
- Where: `client/replay_broadcast.html:4101-4104`, against `:1847-1873`, `:7880-7885`, `:7936`
- Observed:
  ```
  4101: html[data-year="bc17"].endcard-open #bc17-vp,
  4102: html[data-year="bc17"].endcard-open #bc17-bullets,
  4103: html[data-year="bc17"].endcard-open #bc17-econ,
  4104: html[data-year="bc17"].endcard-open #bc17-units { visibility: hidden; }
  ```
  `grep -rn endcard-open` over `*.html *.js *.nim *.mjs *.cjs` in the whole tree returns **exactly
  those four lines and nothing else** — no code path adds an `endcard-open` class to
  `<html>`. What the page actually does is `$('endcard').classList.add('on')` (`:7936`) and
  `.remove('on')` (`:7884`, inside `dismissEndcard()` at `:7881`). The bc17 block's own comment at
  `:4092-4093` asserts the opposite of what ships — *"`#endcard` is opaque over the board and the
  `#bc17-*` boxes are hidden while it shows (the bc23 finding)"*. bc16 and bc19 key their equivalent rules on the class the page really
  sets: `html[data-year="bc16"] #chrome:has(#endcard.on) #bc16-archons, …` (`:3888-3892`) and
  `html[data-year="bc19"] #chrome:has(#endcard.on) #bc19-castles, …` (`:4333-4337`).
  `#endcard`'s background is `radial-gradient(80% 70% at 50% 45%, rgba(16, 11, 7, 0.82),
  rgba(9, 6, 3, 0.95))` (`:1873`), i.e. translucent — so the four bc17 boxes stay visible through the
  score screen.
- Design reference: §Viewer, endcard fix 5: *"No HUD bleed-through. `#endcard` is opaque over the
  board and the `#bc17-*` boxes are `visibility: hidden` while it shows (the bc23 finding)."*
  `tools/ci/renderer_fixture.html:75-84` names this same defect class as bc16's r1-F1 —
  *"it shipped keyed on a class the page never sets and on the wrong sibling direction"*.
- Advisory against the numbered checklist (no item names HUD bleed-through), but it is a dead
  selector and the design's own endcard fix 5 is not met. Not caught by CI: the
  `largest overlay over the board after the soak: bc17-units 4%` check (wasm-viewer log 2585 area,
  bc17 at 2592-2593) measures after the *soak*, not after the endcard is raised.

### F4 — `#bc17-fund`, the endcard Fund panel, is computed every frame and never drawn
- Where: `src/battlecode/broadcast.nim:2451` and `:2533`; `client/replay_broadcast.html:4011`,
  `:4092-4099`, and the endcard markup at `:4630-4659`
- Observed: the sim builds the panel (`broadcast.nim:2451`: *"`#bc17-fund`: the endcard panel. Per
  faction, the points bought AND WHAT…"*) and emits it into every bc17 frame
  (`broadcast.nim:2533`: `"bc17_fund": bc17Fund(w, sideAslot),`). The page carries CSS for it
  (`:4011` `html:not([data-year="bc17"]) #bc17-fund { display: none !important; }` and
  `:4094-4099` `#bc17-fund { display: grid; … max-height: calc(100vh - var(--band, 0px) -
  var(--topband, 0px) - 24px); overflow-y: auto; }`). But:
  * `grep -n 'id="bc17-fund"' client/replay_broadcast.html` → **no match**; the bc17 markup block
    at `:4560-4569` declares `bc17-vp`, `bc17-bullets`, `bc17-units`, `bc17-econ`,
    `bc17-doctrines` and no fund panel.
  * `grep -on 's\.bc17_[a-z]*' client/replay_broadcast.html` → `s.bc17_vp` (`:8224`),
    `s.bc17_bullets` (`:8253`), `s.bc17_econ` (`:8275`), `s.bc17_units` (`:8300`). **`s.bc17_fund`
    is never read.**
  * By contrast the endcard markup at `:4634-4659` carries a per-year war panel div for *every*
    other year — `bc20-chain`, `bc21-bids`, `bc24-traps`, `bc25-srp`, `bc23-tempest`,
    `bc22-mutation`, `bc16-siege`, `bc19-crusade` — and each is read (`s.bc23_war` at `:6134`,
    `s.bc16_siege` at `:6549`, …). bc17 is the only year of ten without one.
- Design reference: §Viewer lists `#bc17-fund` as "the endcard panel (below)" and §Viewer
  "Readouts, 360 px and the endcard" enumerates its contents (per-faction VP and their price, tree
  ledger, bullets earned/spent, friendly-fire as its own line, **and the tiebreak ledger — all four
  rungs**). None of it reaches the screen.
- Corroborating CI evidence (*observed*): the bc17 endcard text captured after the 100 % seek
  (wasm-viewer log 2593-2597) is the shared headline + wincond + score line + the two doctrine
  lines, with no Fund ledger and no tiebreak ledger — consistent with an absent panel.
  (Note: the CI log strips every lowercase `s` from these captured strings — `"Clan A h"`,
  `" core 294"` — in **all ten years' captures** identically, so that is a log-redaction artefact
  and not a bc17 finding.)
- Advisory. Also note `tests/test_viewer.nim:1948-1950` asserts the presence of
  `bc17-vp/bullets/econ/units/doctrines` and does **not** assert `bc17-fund`, which is why the gap
  is silent.

### F5 — the bc17 doctrines panel drops the "what the cog actually sent" disclosure and the fallback badge
- Where: `client/replay_broadcast.html:8323-8344`, against the equivalent block at `:7288-7309`
  and `src/battlecode/broadcast.nim:660-684`
- Observed: `doctrinesJson` (`broadcast.nim:657-684`) already puts both fields in the frame —
  `"fallback": doc.seats[slot].fallback` (`:676`) and
  `"submitted": doc.seats[slot].sheet.submitted.truncateRunes(120)` (`:683-684`) — and bc17's frame
  uses it (`broadcast.nim:2535`, `"doctrines": doctrineWords(doc)`). The inherited renderer at
  `:7288-7309` draws all three things:
  ```
  7296:      var submitted = '';
  7297:      if (seat.envelope && seat.submitted) {
  7298:        submitted = '<br><span class="dsub">what the cog actually sent: ' +
  …
  7302:        (seat.fallback ? ' <span class="dfall">[fallback: ' + esc(seat.fallback) + ']</span>' : '')
  ```
  bc17's own `renderDoctrines` (`:8323-8344`) draws the alias, the name, an
  `envelope: … · N of 11 knobs defaulted` badge, the plain-words list and `notes` — and **neither
  `d.submitted` nor `d.fallback`**.
- Design reference: §Decisions envelope-pin obligation 3 — *"plus the first 120 runes of
  `sheet_submitted` under a 'what the cog actually sent' disclosure"* — and §Viewer
  `#bc17-doctrines` — *"the **submitted-vs-applied badge** and a fallback badge when a seat's
  doctrine came from the fallback sheet"*. Advisory; item 8's "the fallback is recorded" is
  satisfied elsewhere (see Traced and consistent).

### F6 — no CI step asserts the built image has no `java`/`javac`/`node`/`npm`
- Where: `Dockerfile:7` (comment only); `.github/workflows/ci.yml` `docker-smoke` job
  (`:4274-…`); docker-smoke job log
- Observed: `Dockerfile:7` states *"NO JDK, NO JRE, NO JAVA, NO NODE in any stage"* as a comment
  and the Dockerfile contains no java/jdk/jre/node/npm install (`grep -in 'java\|jdk\|jre\|node\|npm'
  Dockerfile` → that one comment line). But I could find **no executed assertion**:
  `grep -n 'command -v' .github/workflows/ci.yml` → no matches; grepping the full docker-smoke log
  for an absent-binary check (`absent|not in PATH|no JVM in the image|image carries no`) → no
  matches. The design note's §Packaging Dockerfile bullet required one: *"Phase 20 adds one
  `docker-smoke` step asserting `java`, `javac`, `node` and `npm` are absent from the built image's
  `PATH`."* Advisory — rail 2's substance holds by construction, but the gate the note promised is
  not in the tree.

### F7 — `ci.yml` cites a `docs/RULES-BC17.md` section that does not exist, and the measured per-round cost is not recorded there
- Where: `.github/workflows/ci.yml:5256` and `:5519`, both reading
  *"(docs/RULES-BC17.md, \"Playback pacing, measured\")"* — the second is inside the wasm-viewer
  leash block reproduced in the job log at 2505-2509;
  `docs/RULES-BC17.md` heading list
- Observed: `docs/RULES-BC17.md`'s headings are: The year in one paragraph (`:20`), The round loop
  (`:39`), The four-rung ladder (`:76`), Where the docs are wrong (`:90`), Divergences (`:107`),
  Determinism (`:155`), The float ledger (`:183`), The doctrine sheet (`:213`), The two chassis
  (`:232`), Scoring (`:256`), Divergence in the doctrine sheet's own words (`:273`). There is **no
  "Playback pacing, measured" section**, and `grep -n 'ms/round\|sim_seconds' docs/RULES-BC17.md`
  returns nothing. The design note required it twice (§The game bullet 6 and §Viewer "Playback
  pacing"): *"`docker-smoke` prints `sim_seconds / rounds` and `docs/RULES-BC17.md` records the
  measured value."* The number itself was printed and is healthy: docker-smoke log 3663,
  `bc17 smoke: sim_seconds=0.113 rounds=899 wall=0.213s` → **0.126 ms/round**, far inside the
  note's 15 ms/round trigger. Advisory.

### F8 — `docs/RULES-BC17.md` and `docs/PARITY.md` describe the determinism patch differently
- Where: `docs/RULES-BC17.md:250-252` vs `docs/PARITY.md` §"The three engine patches", item 3
- Observed: `RULES-BC17.md` says the port is the scaffold *"with the one committed determinism
  hunk (a per-robot `java.util.Random(rc.getID())` in place of **three** `Math.random()` calls…)"*.
  `PARITY.md` corrects exactly that number: *"**MEASURED AND CORRECTED IN PHASE 20: the design note
  says "three" call sites and the scaffold has FOUR** — the archon's hire gate, the gardener's two
  build gates and `randomDirection()` — and the patch rewrites all four, because `build_oracle.sh`
  asserts the count of surviving global draws is zero."* `NOTICE` (scaffold section) avoids the
  number entirely. Advisory, but the design note's own standing rule is *"a divergence described
  two different ways in two documents is a divergence nobody can check"* (§Packaging, last
  paragraph).

### F9 — `docs/PARITY.md` §What is NOT compared contradicts its own Status table on Tier B′(a)
- Where: `docs/PARITY.md` §"What is NOT compared", first paragraph, last sentence
- Observed: the paragraph ends *"…by asserting `Clock.getBytecodesLeft() > 5000` at the end of
  every turn of every compared bot. **That assertion belongs to the outstanding job.**"* The Status
  table three sections above reports B′(a) as done and measured (*"every compared bot asserts
  `Clock.getBytecodesLeft() > 5000` … the measured peak over all 54 pairs is 3 % of a limit"*), and
  the CI log confirms it ran (parity-bc17 log 1338-1394, the per-pair "peak bytecode" column, and
  1284 for B′(b): *"robot 4 (ARCHON) used 30003 bytecodes on round 1"*). Residual to-do phrasing.
  Advisory.

### F10 — the bc17 smoke episode's substance assertions drop six of the eleven the note says never to drop
- Where: docker-smoke job log 3517-3520 (`SMOKE_CONFIG_OVERRIDE`, `SMOKE_REQUIRE_STATS`) and
  3541-3567 (the across-the-pair `jq` step), against design §Tests `docker-smoke`
- Observed, the committed gate:
  * `SMOKE_CONFIG_OVERRIDE` = `{"year":"bc17","pool":"small","seed":5,"gamesPerMatch":1,
    "maxRounds":900,"perGameBudgetSeconds":90,"matchBudgetSeconds":100,"connectTimeoutMs":15000}`
    (note says `perGameBudgetSeconds: 120`, `matchBudgetSeconds: 130`).
  * `SMOKE_REQUIRE_STATS` = `{"units_built":3,"moves":400,"damage_dealt_tenths":0}` — the note's
    `"broadcasts":1` is gone.
  * the across-the-pair step asserts `trees_planted>=2`, `water_actions>=200`,
    `bullets_earned_from_trees_tenths>=3000`, `shake_actions>=5`, `bullets_fired>=20`,
    `strike_actions>=10`. The note listed eleven; **missing are
    `trees_mature_end>=1`, `victory_points>=1`, `units_built>=5`, `damage_dealt_tenths>=10`,
    `robot_ids_issued>=6` and `peak_bullets_in_flight>=2`.**
  The note's ruling on two of those is explicit: *"**If the across-the-pair `victory_points >= 1`
  or `trees_mature_end >= 1` assertion does not hold on the measured episode, the fix is to raise
  the smoke's `maxRounds` until it does — never to drop the assertion**: an episode of this year in
  which nobody ever grew a tree or bought a point is not this game being played."* Both are
  dropped, with no inline measurement recorded in `ci.yml` explaining why. Advisory (no numbered
  checklist item names these); note also that `strike_actions>=10` and `water_actions>=200` are
  *stronger* than the note asked for, so this is a re-shaping rather than a blanket weakening.

### F11 — `tests/test_bc17_examplefuncsplayer17.nim` does not exist
- Where: `tests/` listing; compare `tests/test_bc19_examplefuncsplayer19.nim`,
  `tests/test_bc22_scaffold.nim`, `tests/test_bc23_scaffold.nim`
- Observed: the design's §Tests item 19 named the file and seven claims for it (the per-robot
  `java.util.Random(id)` stream, the per-turn draw count for all four `&&` branch combinations,
  the archon/gardener/soldier/lumberjack branch orders, **the TANK/SCOUT fall-through killing the
  robot on its first turn**, and the seven-direction probe order). None of it is asserted natively.
  The behaviour *is* proved differentially by Tier A″ — 9/9 pairs bit-exact over whole 2 999-round
  games (parity-bc17 log 1364-1367, table rows) — which is stronger evidence for the RNG stream
  than a unit test would be, but it runs only in the JDK-8 oracle job and does not cover the
  TANK/SCOUT fall-through (no scaffold game ever builds one: the `types=` column at parity log
  1233-1240 never lists TANK or SCOUT for `examplefuncsplayer17`). Advisory.

### F12 — the survival gate's friendly-fire clause ships at 75 % against the note's 15 %
- Where: `tests/test_bc17_survival.nim:90-95` (header) and the committed threshold; test job log
  3183
- Observed, verbatim from the header: *"`friendly fire plus own-tree damage under 15 % of damage
  dealt` — **measured 54 %.** The floor is not reachable in this year and the reason is a RULE, not
  a chassis defect: a 2017 bullet has NO TEAM CHECK … Committed at 75 %, measured 54 %, and
  recorded here rather than dropped."* CI confirms the measurement:
  `HEALTHY games=6 notDestroyed=5 vp=2675 median=2999 selfHarm=50335/92413` (test log 3183) =
  54.5 %. Six further design clauses are similarly lowered and each is named with its measurement
  at `:72-95`. This is the bc23 r1-F21/F22 resolution applied as the note itself prescribes
  (*"lower the committed number to roughly half the weak seat's measured value and record the
  measurement inline — never drop the clause"*), and the gate is proved live by the
  `-d:bc17BrokenChassis` subprocess control, which CI reports as
  `BROKEN-CONTROL games=6 … failures=21 … BROKEN-CONTROL: correctly red` (test log 3184-3193).
  Recorded here for completeness, not as a loosening under checklist item 1: this is a **new** test
  file, so there is no prior tolerance that was widened, and nothing was skipped or deleted.
  Advisory.

### F13 — `NOTICE` does not name the oracle trace driver or the six scenario bots
- Where: `NOTICE`, §"battlecode/battlecode-server-2017 engine — AGPL-3.0", the "What derives from
  it" paragraph
- Observed: the paragraph ends *"…and `tools/JavaBc17Tables.java`, which is compiled and run only
  in CI."* The design note's §Packaging ("Licensing") text for the same paragraph ends
  *"…and `tools/oracle/bc17/Bc17Trace.java` plus the seven oracle bots, written against the
  engine's own API and **compiled and run only in CI**."* `tools/oracle/bc17/Bc17Trace.java` (714
  lines) and `bc17idle`, `bc17scenario`, `bc17scenariotree`, `bc17scenariokill`, `bc17scenariotie`,
  `bc17slowbot` are all committed and all written against the engine's API. The scaffold's
  `examplefuncsplayer17/RobotPlayer.java` *is* credited, byte-for-byte, with its sha256. Advisory.

### F14 — `game.docs` uses `"type":"uri"` where checklist item 10 writes `"type":"text"`
- Where: `coworld_manifest_template.json`, `game.docs.readme` and all twelve `pages`
- Observed: `readme` is `{"type": "uri", "value":
  "https://github.com/Metta-AI/cogame-battlecode/blob/main/README.md"}` and every page is
  `{"id", "title", "content": {"type": "uri", "value": …}}`, e.g. the new
  `{"id":"rules-bc17.md","title":"Battlecode 2017 \"Robotic Wildlife Fund\": rules, knobs and
  divergences","content":{"type":"uri","value":".../docs/RULES-BC17.md"}}`. The **structure** the
  checklist names (`readme` object with `type`+`value`; `pages[]` of `{id,title,content:{type,value}}`)
  is exactly right; only the discriminator string differs. This is pre-existing across all nine
  shipped years and the bc17 page follows the house shape; `tests/test_manifest.nim:435-437,452-455`
  asserts it and the installed `coworld` CLI's `validate_upload_manifest` accepts the template
  (`test_manifest.nim`, final block). Recorded so the judge can see the literal mismatch; I do not
  read it as falsifying item 10, and it is not introduced by this diff.

### F15 — the bc17 replay drew zero killfeed lines at the first frame; every other year drew 1–8
- Where: wasm-viewer job log line 2593 vs 2457, 2477, 2495, 2509, 2523, 2537, 2551, 2565, 2579
- Observed:
  ```
  bc17: {"loaded":true,"ms":322,"clock":"0:22 GAME 1 OF 1 — HOUSEDIVIDED",…,"feed_lines":0}
  bc26 3 · bc20 8 · bc21 7 · bc24 1 · bc25 8 · bc23 4 · bc22 8 · bc16 7 · bc19 7
  ```
  bc17 is the only one of the ten at 0. `tests/test_bc17_beats.nim:72` asserts
  *"both doctrine beats land on frame 0"*, and the committed fixture carries 292 events over 19
  kinds, so beats do exist. Whether this is the spoiler gate, the reveal-as-the-playhead-reaches-it
  rule, or a wiring gap is *untested* — see "Could not determine". Advisory.

---

## Traced and consistent

**Checklist item 1 — CI green, no test loosened.** *Observed.*
`gh api .../runs/34536659753` → `{"conclusion":"success","head_branch":"main","head_sha":
"07ad48cc68718c8a2c6ce066903e5e5cbc6f49da","run_attempt":1,"status":"completed"}`; 13/13 jobs green
(`test`, `parity-oracle`, `parity-oracle-bc16/17/19/20/21/22/23/24/25`, `docker-smoke`,
`wasm-viewer`). `git diff f0570643..07ad48cc -- tests/` is 31 files, +5108/−28: 23 new
`test_bc17_*.nim` shards, one new `bc17_fixture.nim`, four regenerated fixtures (GV12→GV13, one
line each), one new `replay-bc17.json`, and edits to `test_manifest.nim` (+87/−…) and
`test_viewer.nim` (+58/−…). I read both edit diffs in full: every hunk is additive or a *tightening*
count update — `variants.len 9→10`, `policies.len 36→40`, `prompts 18→20`, `scripted 18→20`,
`owned 9→10`, `docs.pages 11→12`, and the year-guard strings widened from nine-way to ten-way
(`test_viewer.nim:874-877`, `:1167-1170`). No assertion deleted, no tolerance widened, no
`skip`/`xfail` added, no test file removed. `grep -n 'skip\|SKIP\|xfail'` over the whole `test` job
log returns one unrelated line (`no nimby.lock in the repo; skipping dependency sync`, log 249).
All 23 bc17 shards ran twice (debug and `-d:release`) and all reported `ok` — e.g.
`test_bc17_baselines: ok (61 checks)`, `test_bc17_perf: ok (11 checks)`,
`test_bc17_survival: ok (13 checks)` (test log 2241/2272, 2996/3028, 3194/3236).

**Checklist item 3 — Static viewer.** *Observed.* `coworld_manifest_template.json:14-16` declares
`"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` is present
and `-rwxr-xr-x`; `replay-viewer/` is **unchanged by this diff**
(`git diff --stat f0570643..07ad48cc -- replay-viewer/ tools/build_replay_viewer.sh` is empty).
`coworld-release.yml:214-221` fails the release unless certification reports the static bundle,
with the message *"a pod-served /client/replay viewer is not acceptable"*.
`tests/test_seats.nim:77-78` asserts `"\"/client/replay\"" notin server`. The only other
`/client/replay` strings in the tree are `client/broadcast_core.js:372,385` — the starter's
URL-rewrite map, byte-identical to `f0570643`.

**Checklist item 4 — Both name spaces.** *Observed.* `tests/fixtures/replay-bc17.json` carries
`aliases: ["Clan Ash","Clan Basil"]` and `names: ["daveey","daveey-1"]`, and each seat object
carries both `alias` and `name`. The bc17 frame (`broadcast.nim:2523-2524`) emits
`"aliases": [AliasA, AliasB]` and `"names": [doc.names[0], doc.names[1]]`; the CI scorebug capture
reads `CLAN ASH Clan Ash · Plant, water, donate. 62 … CLAN BASIL Clan Basil …` (wasm-viewer log
2593). `sim_types.nim:246-247`'s `AliasA`/`AliasB` are **not touched** by this diff (pin 11
satisfied). `decide.nim:briefFor`'s bc17 payload (`decide.nim:1456-1570`) carries `alias` and
`opponent_alias` and no real name.

**Checklist item 5 — Degrade-never-hang.** *Observed.* `episode_timeout_minutes: 20`
(manifest `:9`) → 1200 s, 60 % = 720 s. The bc17 variant's budgets are
`connectTimeoutMs 25000`, `doctrineBudgetMs 45000`, `perGameBudgetSeconds 120`,
`matchBudgetSeconds 330` — the note's arithmetic 30 + 45 + 330 + 30 = **435 s ≤ 720 s**. Every wait
is bounded in code: `decide.nim:1584` `let budget = initDuration(milliseconds =
max(1, config.doctrineBudgetMs))`; `:1604` `while open.len > 0 and attempt < 2`; `:1623-1624`
`let deadlineMs = if attempt == 0: config.attempt1Ms else: config.retryMs`; `:1642`
`client.curl.makeRequests(batch, max(1, deadlineMs div 1000))`. The only `while true` loops in
`src/battlecode/years/bc17/**` are `trove.nim:180` and `:213`, both open-addressing probes bounded
by `if idx == loopIndex: break` (`:186`) — I read both. *Untested:* the wall-clock envelope on a
real 3-game bc17 episode; the smoke ran one 899-round game in `sim_seconds=0.113` (docker-smoke log
3663), which extrapolates to ~1.1 s for three 2 999-round games at that map's density, and
`tests/test_bc17_perf.nim` gates the worst map (`Chess`) at 60 s and passed twice.

**Simultaneous-decision clause — one parallel batch per turn.** *Observed.*
`src/battlecode/decide.nim:4-5` (module doc) and `:1625-1642`: one `RequestBatch`, both open seats
`batch.post(...)`ed inside the same loop, one `client.curl.makeRequests(batch, …)` call. No
per-seat sequential call site. Year-neutral and unchanged; bc17 inherits it via its `preambleFor`
and `briefFor` arms (`decide.nim:843`, `:1456`).

**Checklist item 6 — `num_agents`.** *Observed.* All **ten** variants carry
`game_config.num_agents: 2` (manifest lines 3258, 3285, 3312, 3339, 3366, 3393, 3420, 3447, 3474,
3501) and none carries it at variant top level; the certification fixture carries
`num_agents: 2` at line 3537 with `players: [awu, scaffold]` and `year: "bc26"`.
`tools/ci/docker_smoke.sh` is **unchanged by this diff** and enforces all four invariants with the
`SEAT-COUNT FAIL:` prefix at `:145-152` (present), `:156-161` (positive integer), `:165-170`
(`len(certification.players) == num_agents`), `:171-175`
(`len(certification.game_config.players) == num_agents`), plus the `SMOKE_SEATS` cross-check at
`:181-186` (`seats_expected="${SMOKE_SEATS:-2}"` at `:82`) and the override refusal at `:200-204`.
**`grep -c "SEAT-COUNT FAIL" docker-smoke.log` → 0.** Ten episodes ran, each printing `seats=2`
twice (log lines 2392/2408, 2456/2463, 2512/2520, 2570/2578, 2628/2636, 2686/2694, 3021/3029,
3170/3178, 3327/3335, 3525/3533) and each `reason=complete`. The bc17 episode: `game=battlecode
seats=2 config={… "num_agents": 2, "year": "bc17" …}` (3527) → `smoke OK: seats=2 results=2461B
replay=22201B reason=complete` (3533). Pin 8 satisfied: additive, bc17 last, cert unchanged on
bc26, `player[]` unchanged at `[awu, scaffold]` with only the description strings extended.

**Checklist item 7 — scripted baseline plays full episodes legally.** *Observed, partially.*
The all-scripted episode to the natural end with `reason == complete` is proved by the docker-smoke
gate (log 3533) rather than by a Nim test — see F1 for the absent episode-level test. Legality:
`tests/test_bc17_baselines.nim:121-127` asserts `refused_actions == 0` for **both** chassis across
six gate games and `opsOverCap == 0`; `:150-155` asserts the same on both mirrors; the header
`:9-28` explains that every guard in `actions.nim` funnels through `refuse()` so the counter is the
audit. The note expected `refused_actions[weak] > 0`; the shard **measured 0**, asserts 0, and
records why inline (`:19-28`) rather than dropping the clause — I read the reasoning
(`examplefuncsplayer17`'s `tryMove` probes with `rc.canMove` first, so the random draw chooses among
legal orders) and it is consistent with the code. `(e)` holds: `orchardWins == 6` of 6.
The "tuned with a grid harness" half is unverified — see "Could not determine".

**Checklist item 8 — LLM reply handling.** *Observed.* Tolerant parse: `llm.nim`'s fence-tolerant
JSON extraction (unchanged, year-neutral; `decide.nim:4-11` documents the contract). Retry exactly
once: `decide.nim:1604` `while open.len > 0 and attempt < 2`, with `:1623-1624` giving attempt 0
`attempt1Ms` and attempt 1 `retryMs`, and `:1676-1681` emitting `doctrine_retry` with
`will retry`. Fallback to the scripted move: `:1690-1702` reseats `baselineSheet(config.year,
baselineForSeat(...))` — for bc17 that is `blOrchard` (`baselines.nim:53`, `:104-114`). **Recorded
for phase 60:** `result.fallback[slot] = cause` (`:1697`) → `results.nim:78`
(`fallbacks.add(%(if seats[slot].fallback.len > 0: 1 else: 0))`) → `results.nim:97` `"fallbacks"`,
plus a `doctrine_fallback` event (`:1698-1699`) and the greppable log line `falling back` (`:1701`).
The fixture's seats carry `fallback` and `fallback_detail` keys.
The smoke ran with no `ANTHROPIC_API_KEY` and reported `fallbacks == [0,0]` (both seats scripted,
not LLM — the client disables at construction, `decide.nim:1591-1601`).

**Checklist item 9 — rune-safe truncation.** *Observed.* `tests/test_bc17_sheet.nim:157-182` feeds
`repeat("\u{1F332}", 400)` (a 4-byte astral codepoint) into `notes` and `motto` at the cap and
asserts `s.notes.validateUtf8() < 0`, `s.motto.validateUtf8() < 0`, `s.notes.runeLen < 400` and
`s.notes.len mod 4 == 0` ("on a rune boundary, so no half character"). The 16 384-**byte** reply cap
is exercised at `:166-181` with 20 000 astral codepoints, asserting both that a leading object
survives and that an object buried past the cap raises rather than being half-parsed. Unknown-field
names are cut to 40 runes (`:152-154`) and the list bounded at 16 (`:149-151`).
`tests/test_bc17_beats.nim:78-79` additionally asserts every beat label is ≤ 120 runes and valid
UTF-8.

**Checklist item 10 — Manifest validates.** *Observed (with F14 noted).* `game.docs` has `readme`
(object with `type`+`value`) and `pages` — twelve, each `{id, title, content:{type, value}}`, with
`rules-bc17.md` appended last. `game.protocols` carries **both** `player` and `global`.
`tests/test_manifest.nim:435-455` asserts the shape and the exact page-id list.
Pin 9 verified independently: I diffed `game.config_schema` old-vs-new key by key in Python — the
**only** change anywhere in it is `properties.year.enum` gaining `"bc17"` at the end. Zero bound
moves; `additionalProperties: false` and `required: ["tokens","players"]` unchanged. The
`end_reason` enum has 45 values and contains all five new bc17 values plus the reused `highest_id`
and `abandoned`; `games.items.required` is unchanged at the five year-neutral keys.

**Checklist item 11 — legible at 360 px.** *Observed.*
`client/replay_broadcast.html:2623` is exactly
`#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` — unchanged from the starter. Word
labels hide under `@media (max-width: 640px)`; bc17's own block adds one at `:4127-4131`
(`#bc17-bullets .lbl`, `#bc17-econ .lbl`, `#bc17-units .lbl` → `display: none`) and deliberately
does **not** hide `#bc17-vp`'s bars or numbers (`:4128` only shrinks font/gap/padding), matching the
note's *"`#bc17-vp` keeps both bars, both numbers and the price at every width"*. The killfeed
overlap gate ran on the bc17 replay at 360/720/1280 px at FIT and 2× zoom (`--killfeed-overlap`,
wasm-viewer log 2358-2363) and passed.

**Checklist item 12 — release order and scaffold.** *Observed.* `coworld-release.yml` step order:
`Build the Coworld manifest` (`:168`) → `Certify locally` (`:182`) → **`Upload the policies`**
(`:225`) → `Upload the Coworld` (`:323`) → `Put the Coworld secret` (`:419`). All three workflows
present (`ci.yml`, `coworld-release.yml`, `coworld-submit.yml`); `tools/ci/docker_smoke.sh` is
present and `0755`. `tools/ci/policies.json` has **40** entries; the four bc17 ones are
`battlecode-bc17-orchard` (`PLAYER_PROMPT`), `battlecode-bc17-tankrush` (`PLAYER_PROMPT`, carrying
`"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`), `battlecode-orchard`
(`PLAYER_SCRIPTED=orchard`) and `battlecode-examplefuncsplayer17`
(`PLAYER_SCRIPTED=examplefuncsplayer17`) — two LLM champions plus two scripted fillers, champion #2
owned, and `image` is the player service's image. The placeholder gate exits 0: I ran it verbatim —
`grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml .github/workflows/coworld-release.yml
.github/workflows/coworld-submit.yml tools/ci/docker_smoke.sh tools/ci/policies.json` → **no
matches** (grep exit 1). `tests/test_manifest.nim:694-719` pins the four bc17 policy indices
(36–39, appended so no existing index moved) and champion #2's player id. `docker-smoke` builds the
image in the same job before running the smoke, and `wasm-viewer` `needs: docker-smoke`
(`ci.yml:5353`).

**Checklist item 13 — Viewer executes.** *Observed.*
`wasm-viewer` is green at the reviewed sha and its `Load the bundle in a real browser` step really
ran: the job downloaded Chromium 140.0.7339.16 (Playwright build v1187, log 2239) and executed
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay <replay>
--timeout 120 --soak 15 --killfeed-overlap` once per replay (log 2357-2363); the step is not
commented out and carries no `continue-on-error`. For bc17 specifically (log 2592-2597):
```
loading dist/smoke/replay-bc17.json in dist/static-replay-viewer
{"loaded":true,"ms":322,"clock":"0:22 GAME 1 OF 1 — HOUSEDIVIDED",…}
soak: 15s of playback kept advancing ("round 1 / 899" -> "round 313 / 899" -> "round 361 / 899")
scrub readouts (#scrub): 0%="0:22 …"  50%="0:18 …"  100%="FINAL MATCH OVER"
scrub selector: #scrub
endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH / THE GAME ENDED ON MORE VICTORY
POINTS IN GAME 1, ROUND 899 …
largest overlay over the board after the soak: bc17-units 4%
```
`needs: docker-smoke` at `ci.yml:5353` with the comment *"the replay docker-smoke just produced —
hence the dependency"*.
Markers: `replay-viewer/static_replay.js:180`
`document.documentElement.setAttribute('data-replay-loaded', 'true')` on the worker's `loaded`
message (first drawn frame), and `:14-20`
`…setAttribute('data-replay-error', error && error.message ? error.message : String(error))` on
failure. Both in the shell's own code paths; the file is unchanged from the starter.
**Emscripten flags vs bootstrap agree** — this is the cogame-lantern check and it passes:
`replay-viewer/config.nims` has **no `MODULARIZE` and no `EXPORT_NAME`** (its only `-s` flags are
`EXPORTED_FUNCTIONS` at `:53` and the memory/env set), and
`replay-viewer/static_replay_worker.js:8` declares `var Module = {};`, `:218` sets
`Module.onRuntimeInitialized = function () {…}`, and `:274` ends with
`importScripts('./wire_constants.js', './broadcast_core.js', './bc_replay.js');`. A non-`MODULARIZE`
build against an `onRuntimeInitialized` shell is the correct pairing, and the smoke's
`loaded: true` (not file presence) is the evidence. The `lobby` bullet: see "Could not determine".

**Checklist item 14 — Chrome is the starter's.** *Observed.* For a MOD run the baseline is this
repo at `f0570643`:
`git diff --stat f0570643..07ad48cc -- client/chrome_common.js client/broadcast_core.js` is
**empty** — both byte-identical (pin 12). `client/replay_broadcast.html` is `+463/−3`: the three
removed lines are `'bc16-econ', 'bc16-units', 'bc19-econ', 'bc19-units']` (the `--statrail` set,
replaced by a widened list including `'bc17-econ', 'bc17-units'` at `:7963`) and the two
`if (!isBc16 && !isBc19 && …` guard lines, each replaced by the ten-way form with `!isBc17`. Nothing
else is removed — the page grew by a bc17 block under the banner comment
`/* BC17 additions to the inherited cogame-battlecode chrome` (`:3937`) and
`<!-- BC17 additions to the inherited cogame-battlecode chrome -->` (`:4560`). No starter id is
reused: bc17's ids are `bc17-vp`, `bc17-bullets`, `bc17-units`, `bc17-econ`, `bc17-doctrines`,
`bc17-doctrines-close`, `bc17-doctrines-body`, `bc17-doctrines-toggle`, all new.
(a) `relayout()` sets `--hudscale`, `--topband`, `--band` and `--statrail` on `root` inside a
fixed-point loop (`:7944-7973`: `root.setProperty('--hudscale', …)` at `:7950`,
`'--band'` at `:7952`, `'--statrail'` at `:7973`); (b) `#bc17-econ { bottom: calc(var(--band, 0px) + 8px) }` and
`#bc17-units { bottom: calc(var(--band, 0px) + 96px) }` (`:4063-4064`) — nothing fixed-positioned
sits inside the band; (c) `#endcard { … top: var(--topband, 0px); bottom: var(--band, 0px); }`
(`:1847-1860`), shown with `#endcard.on` (`:1887`, set at `:7936`), and `dismissEndcard()`
(`:7880-7885`) removes `.on`; (d) `buildBc17BeatButtons` (`:8381-8384`, defined exactly once —
asserted by `tests/test_viewer.nim:1963-1964`) delegates to `api.renderBeats(s.beats || [],
'bc17')`, and every one of the thirteen kinds has a scoped rule at `:4111-4123`, asserted from the
page source for every kind the fixture actually emits by `tests/test_bc17_beats.nim:152-156` and for
the full vocabulary at `:169`. **`#viewpanel` is KEPT** (25 references in the page), which the note
argues for on measured grounds (30×30–100×100 float boards against a 360 px frame) and which is why
`--strict-text-bounds` is correctly dropped on the replay runs.

**Pin 1 — the parity oracle.** *Observed.* `parity-oracle-bc17` is a real job (`ci.yml:3402`,
`timeout-minutes: 90`) that ran the JVM: `tools/oracle/bc17/jar.lock` pins
`org.battlecode:battlecode:2017.1.6.2`, sha256 `9254e892…`, `14576275` bytes, `"jdk": "8"`.
The log prints `TOTAL JVM WALL CLOCK OVER THE 54 PAIRS: 71s` (line 1133) and per-pair line counts
that prove real games (`bc17scenariotie/Chess: 2s JVM, java 2816418 lines, nim 2816418 lines`,
line 1129). Not a no-op. No JDK/JRE/Node in any image (Dockerfile; but see F6 for the missing gate).

**Pin 3 — exactly three CI-only patches.** *Observed.* `tools/oracle/bc17/build_oracle.sh:120-125`:
```
patches="$(find "$HERE" -name '*.patch' | wc -l)"
test "${patches}" -eq 3 || { echo "::error::found ${patches} patches …, want exactly three …"
```
Each is `git apply --check`ed then applied with a post-condition: `strictmath.patch` must leave
**11** `StrictMath` sites and 0 surviving `Math.{sin,cos,atan2,sqrt}` (`:153-176`);
`rtree_order.patch` must leave `grep -c nearestN ObjectInfo.java == 0` (`:178-192`);
`determinism.patch` must leave 0 global-RNG draws (`:194-206`). The three committed files are
`strictmath.patch`, `rtree_order.patch`, `examplefuncsplayer17/determinism.patch` and nothing else.

**Pin 5 — Tier C not map-gated, ledger genuinely empty and the gate live.** *Observed.*
`tools/ci/parity_ledger_bc17.json` is literally `{"entries": []}`.
`tools/ci/parity_tiers_bc17.py` fails on: a divergence with no entry (`:376-380`), a divergence
earlier than the entry (`:381-384`), a stale entry that no longer reproduces (`:393-396`), and a
ledger cause of `""`/`unknown`/`unclear`/`tbd`/`?` (`:219-230`). Its own self-test constructs the
`"cause": "unknown"` case and fails if the schema check accepts it (`:295-301`), and CI printed
`parity_tiers_bc17 selftest: 10 cases, all three known comparator bugs plus the two raw-bit ones
and the ledger schema's 'unknown' rejection covered` (parity log 1337). Final verdict:
`bc17 parity: 54 pairs, all bit-exact for whole games, ledger empty` (1396). No map gating: the
same nine maps run for every bot.

**Pin 6 — all nine Tier A″ pairs ran; the fallback did not fire.** *Observed.* The per-pair table
(parity log 1338-1377) lists `examplefuncsplayer17` against all nine maps — `CropCircles`,
`GreenHouse`, `HiddenTunnel`, `HouseDivided`, `OMGTree`, `shrine`, `Chess`, `Cramped`, `Alone` —
each `bit-exact` at 3 % peak bytecode. 6 bots × 9 maps = 54 pairs, and the measured wall clock is
71 s against the 80-minute trigger.

**Pin 7 — GV13 and the compatibility list.** *Observed.* `sim_types.nim:16` `GameVersion* = "GV13"`
with a prepend-only changelog entry (`:22-50`); `:287-289`
`ReplayCompatibleGameVersions* = ["GV04","GV05","GV06","GV07","GV08","GV09","GV10","GV11","GV12",
GameVersion]` — extended, nothing dropped. Every fixture that carried GV12 at `f0570643`
(`replay-bc16`, `replay-bc19`, `replay-bc22`, `replay-bc23`) is now GV13; the GV05/GV06/GV07/GV08
fixtures (bc20/bc21/bc24/bc25) are correctly untouched. `grep -rn '"GV1[0-9]"\|"GV0[0-9]"'` over
`tests/ src/ tools/ client/ replay-viewer/` finds no literal outside `sim_types.nim` and
`test_bc22_replay.nim:99-108`, which deliberately checks `"GV04" in ReplayCompatibleGameVersions`
and carries a comment explaining that a literal `"GV10"` *"used to be here"* and was replaced by the
symbol. Assertions intact.

**Pin 9 — `maxRounds` 3000 and no bound moves.** *Observed.* Variant `bc17.game_config.maxRounds`
is `3000`; the config_schema key-by-key diff showed the year enum as the only change.
`broadcast.nim:2522` emits `"rounds": doc.plan.maxRounds - 1` (2999 played).

**Pin 10 — licensing.** *Observed.* `NOTICE` gains four sections: the engine (AGPL-3.0, commit
`165d8a8e`, jar sha256 and byte size, the per-file derivation list, "used only at CI time and at
map-conversion time"); the scaffold (AGPL-3.0, `76e7b51e`, the committed
`RobotPlayer.java` named as a byte-for-byte copy with its own sha256
`f728119454fea883…`, **and both borrowed helpers credited by name and line** — `kit.nim`'s
`tryMove` at `RobotPlayer.java:215-244` and `micro.nim`'s `willCollideWithMe` at `:253-277`); the
three unlicensed 2017 repos explicitly **NOT READ**; and the client-17 sprites with the licence
discrepancy recorded verbatim — *"The root `LICENSE` is the GNU Affero General Public License v3;
`package.json` declares `"license": "GPL-3.0"`. The two disagree, and both are compatible with this
repository's AGPL-3.0 — recorded here rather than papered over."* `NOTICE` also self-corrects the
design note's sprite count (21 in the headline, 22 in the enumeration) and says which ships.

**Pin 13 — one parallel batch, degrade-never-hang, fallback counted.** Covered under items 5 and 8.

**Pin 14 — the V3 guard is owed and paid.** *Observed.* `docs/RULES-BC17.md:135-142` carries V3 in
full: *"a `build`, `hire` or `plant` that would issue an id above **32 000** is REFUSED and counted
in `builds_refused` and `refused_actions`"*, with the note that all three verbs are covered.
Implementation at `src/battlecode/years/bc17/actions.nim:463,472`,
`world.nim:34,478`, `constants.nim:96` (`maxRobotId* = 32000`), with the counters surfaced at
`rules.nim:105,567`. `tests/test_bc17_ids.nim` is the shard that pins it.

**Scoring against the design's scoring section.** *Observed.* `src/battlecode/years/bc17/rules.nim:
375-377` is the design's formula verbatim:
```
result[t] = int(64.0'f32 * share(vp[t], vp[o]) +
                24.0'f32 * share(treeN[t], treeN[o]) +
                12.0'f32 * shareF(worth[t], worth[o]))
```
with `share` returning `0.5'f32` on a 0–0 total (`:341-346`), the negative-`worth` clamp applied to
the score and not the ladder (documented at `:357-362`), and `winBonusFor` gaining `yBc17` to the
200 set (`match.nim:765-766`). `tests/test_bc17_scoring.nim` is committed and green.
The hash chain matches the design's "thirteen per team plus eleven globals" exactly
(`rules.nim:foldRoundHash`), including `w.mixHashBits(w.bulletSupply[t])` — the raw-bits tripwire.

**Event schema vs what the viewer reads.** *Observed.* `first_action`'s field is **`action`**, not
`kind` (`match.nim:404-406`, and `dispatch.nim:266-276` documents why). `Bc17UnitNames`,
`Bc17ActionNames` (16 values) and `Bc17RungNames` are at `dispatch.nim:259`, `:266`, `:277`.
`match.nim:399-403` indexes `Bc17ActionNames[max(0, min(15, e.b))]` and `:443` indexes
`Bc17UnitNames[max(0, min(5, e.b))]` — both bounds-clamped. `famine`'s `resource` is year-switched
to `"bullets"` for bc17 (`match.nim:633-641`), and `broadcast.nim`'s beat label switch has the
matching `of "bullets": " — nothing can be bought"` arm. The committed fixture emits 292 events over
19 kinds and 12 of the 13 beat kinds; `tests/test_bc17_beats.nim:59` names `rout` as the one it does
not exercise and says why.

**Registry / manifest / dispatch.** *Observed.* `years/registry.nim:53-55` adds the single
`YearSpec(id: "bc17", …, maxRounds: 3000, pools: @["small","mixed","large"], atlas: "atlas_bc17")`
row; `baselines.nim` gains `blOrchard`/`blExamplefuncsplayer17` with the exact resolution table of
§Decisions (`:104-114`), asserted by `tests/test_bc17_baselines.nim:39-48`;
`sim_types.nim:341-342` gains `scOrchard`/`scExamplefuncsplayer17` with no string collision.

---

## Could not determine

- **Checklist item 7's "tuned with a grid harness, not guessed".** I found no grid-harness artefact
  anywhere: `grep -rln 'grid harness\|gridHarness\|tune_grid\|--grid' tools/ tests/ docs/` returns
  nothing, for bc17 or for any of the nine shipped years. What exists instead is
  `tests/test_bc17_survival.nim:25-95`, which records two full measured tables (healthy mirror and
  the `-d:bc17BrokenChassis` control) over six games and sets each committed threshold between
  them, and `tests/test_bc17_knobs.nim`, which sweeps each knob low-vs-high over paired seeded
  games. That is measurement of *outcomes*, not a sweep of `orchard`'s internal parameters.
  **What would settle it:** a committed harness (or a phase-20 log) showing the parameter grid that
  produced `orchard`'s constants, or a ruling that the survival/knob measurement tables discharge
  this clause for this repo lineage.
- **Checklist item 13's "playback opens at the game start, never the recorded lobby".** There is no
  `gameStarts`/`gameStart`/`lobby` symbol anywhere in `replay-viewer/*.js`, `replay-viewer/*.nim` or
  `client/broadcast_core.js` (`grep -rn` over all of them), and the bc17 frame emits `"lob": 0`
  (`broadcast.nim:2513`) — *inferred*: this lineage records no frozen lobby frames, its scrubber
  axis is rounds, and the concept the checklist names does not exist here. The CI evidence is
  consistent: the first drawn frame reported `round 1 / 899` and the soak advanced to `round 361 /
  899` (wasm-viewer log 2593-2594), i.e. no dwell on a first tick. **What would settle it:** a
  replay recorded with a large `lobbyJoinTimeoutTicks` and no joining seats, as the checklist asks
  — that probe was not run, and the CI replay's shape cannot show the failure mode either way.
- **F15's cause (`feed_lines: 0` on bc17 and 1–8 on all nine other years).** I read
  `broadcast.nim:186-200` (the pre-match feed filter, which keeps `doctrine_received` and
  `doctrine_fallback`) and `tests/test_bc17_beats.nim:69-73` (which asserts both doctrine beats land
  on frame 0), so beats exist at frame 0 and I cannot reconcile the 0 from the source alone.
  **What would settle it:** running `tools/ci/viewer_smoke.mjs` against
  `dist/smoke/replay-bc17.json` locally and reading `#killfeed`'s children at the first frame, or
  inspecting the uploaded `viewer-smoke.json` artefact from run 34536659753.
- **Whether `#bc17-doctrines` is capped-and-scrolling and outside `var(--band)` under a real
  layout.** The CSS at `:4070-4078` sets
  `top: calc(var(--topband, 0px) + 74px); max-width: 78vw; max-height: 42vh; overflow-y: auto`,
  which reads correct (the `calc(100vh - var(--band…))` cap at `:4096` belongs to `#bc17-fund`, not
  to the doctrines panel), but `tests/test_viewer.nim`'s bc17 block (`:1942-1981`) asserts only the
  dismiss control and the scoping, not the cap, the band clearance or the aspect-ratio fixed point
  that §Tests item 30 named — and the renderer fixture that would measure it does not include bc17
  (F2). **What would settle it:** adding `'bc17'` to `renderer_fixture.html:70-71` and reading the
  step's per-width verdict.
