blocking: 0

# r1 verdict — battlecode-2017 (bc17)

Head: `526befdb6b34bff22fe13d9ac1007850ce84d16c` ("Merge pull request #22 from Metta-AI/bc17-r1-fixes")
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision clause)
Independent read written before reading fixes: **yes** — `r1-fixes.md` does not exist (fixer session died before
writing it); I read the checklist, the design note and the diff `f0570643..526befdb` and wrote my own notes
**before** opening `r1-review.md`. No fixer self-report existed to contaminate the read.

CI at the judged sha: run **34557429247** (workflow CI, branch `main`, head sha `526befdb`, created
2026-09-11T03:10:23Z, queued behind run 34555487533 on main's `concurrency: ci-${{ github.ref }}` group, jobs
started 04:17:14Z) — **conclusion `success`, 13/13 jobs green, observed completed at my 05:15:43Z poll**
(test 04:17→05:13, docker-smoke 04:17→04:22, parity-oracle-bc17 04:17→04:22, wasm-viewer 04:22→04:28, all
`success`). Logs grepped, not trusted by colour — evidence lines cited per item below.

---

## Refutation pass — F1…F15

The review was written against `07ad48cc` (pre-fix). Every finding was re-tested at the current head. A finding
that was true then and is fixed now is **not standing**.

### F1 (item 2, blocking claim) — no bc17 replay re-derivation test → **UPHELD against 07ad48cc; RESOLVED at head**
Commit `8e27c91` adds `tests/test_bc17_replay.nim` (542 lines, 82 checks). Verified at head: the module doc
(`:10-13`) and body deliver the checklist's item 2 read literally — `derivedRounds()` walks the deriver frame by
frame against the recorded chain; a per-tick state digest (bodies, bullets, supplies, VP, broadcast arrays, exec
order, trove layout, both IDGenerator states) is compared element by element recorder-vs-deriver, with a
one-bit-flip negative control; strict UTF-8 of the written bytes (`:235`, `:467`, `:525`); `plan.maps` carries all
three drawn maps on a two-game clinch (`:316-334`); `sheet_envelope`/`sheet_submitted` round-trip; per-event-kind
bounds; the `deadline`/`abandoned` path (`:498`). It ran twice in CI: `test_bc17_replay: ok (107 checks)` ×2
(test job 103145390698 log). Not a standing finding.

### F2 (item 15, blocking claim) — renderer fixture has no bc17 row → **UPHELD against 07ad48cc; RESOLVED at head**
Commit `87dbe65`. `tools/ci/renderer_fixture.html:71` — `'bc16', 'bc19', 'bc17'];` (ten years);
`SUPPRESSED_BY_ENDCARD` gains `bc17: ['bc17-vp','bc17-bullets','bc17-econ','bc17-units','bc17-doctrines']`
(`:86-87`); full-cap bc17 markup rows at `:741-870` (`#bc17-doctrines-body` at `MaxNoteRunes`, motto at
`MaxMottoRunes`, the Fund panel, the ladder line), and the fixture asserts its own strings are still full-length
(`:175-176`, `:1140`, `:1253-1254`). `tests/test_viewer.nim:396-398` pins "a row per year, now TEN of them".
The CI step ran at the judged sha with the flag: wasm-viewer log 2924 `canvas text: 0 drawn, 0 never inside the
canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. Not standing.

### F3 — bc17 endcard HUD-suppression keyed on `endcard-open`, a class nothing sets → **RESOLVED at head**
Commit `44d6256`. `client/replay_broadcast.html:4134-4138` now reads
`html[data-year="bc17"] #chrome:has(#endcard.on) #bc17-vp, … #bc17-units, … #bc17-doctrines { … }` — keyed on
`#endcard.on`, the class `:7936` actually sets (same shape as bc16/bc19), and it now also hides `#bc17-doctrines`.
`grep -n endcard-open client/replay_broadcast.html` at head → no bc17 hit.

### F4 — `#bc17-fund` computed every frame, never drawn → **RESOLVED at head**
Commit `b9f4e4b`. Markup: `<div id="bc17-fund"></div>` at `:4699` (inside `#endcard`); reader: `var f =
s.bc17_fund;` at `:8448` (comment at `:8444` cites r1-F4). Live confirmation at the judged sha: the bc17 endcard
capture in wasm-viewer log (job 103146368725, bc17 block at 2682-2698) carries the Fund/score/games-played lines
that were absent in the r1 capture.

### F5 — doctrines panel drops the fallback badge and the "what the cog actually sent" disclosure → **RESOLVED at head**
Commit `08bf773`. bc17's `renderDoctrines` now draws `d.fallback` (`' <span class="dfall">[fallback: ' +
esc(d.fallback) + ']</span>'`) and, under `if (d.envelope && d.submitted)`, the
`<div class="dsub">what the cog actually sent: …` disclosure (page, bc17 block ~`:8380-8404`), with
`#bc17-doctrines .dfall`/`.dbadge`/`.dsub` CSS at `:4097-4099`.

### F6 — no gate asserting the image carries no java/javac/node/npm → **RESOLVED at head**
Commit `823c32f`. `ci.yml` docker-smoke step "The built image has no java, javac, node or npm on its PATH"
(`:4307-4337`): `docker run --rm --entrypoint /bin/sh "${IMAGE}:ci" -c "command -v ${bin}"` per binary, red on a
hit, plus a self-check that `/bin/sh` resolves so four absences cannot pass vacuously. Ran at the judged sha:
docker-smoke log 2383-2386, `absent from the image's PATH: java / javac / node / npm`.

### F7 — `ci.yml` cites a `docs/RULES-BC17.md` section that does not exist → **RESOLVED at head**
Commit `fa7200c`. `docs/RULES-BC17.md:262` `## Playback pacing, measured`, recording
`bc17 smoke: sim_seconds=0.113 rounds=899 wall=0.213s` = 0.126 ms/round against the 15 ms/round trigger
(`:270-278`). The `ci.yml` citations now resolve.

### F8 — RULES-BC17.md says "three" Math.random() sites, PARITY.md says four → **RESOLVED at head**
Commit `3149f79`. `docs/RULES-BC17.md:251-253` now describes the determinism patch as rewriting the four call
sites ("**FOUR AND NOT THREE**: the design note said three, phase 20 …"). The two documents agree.

### F9 — PARITY.md §What is NOT compared contradicts its own Status table on B′(a) → **RESOLVED at head**
Commit `8b7c89a`. `docs/PARITY.md:2284-2296` (bc17 §What is NOT compared) now states "**Tier B′(a) is DONE and
measured**  — every compared bot asserts `Clock.getBytecodesLeft() > 5000` … the peak over all 54 pairs is 3 %".
`grep -n 'belongs to the outstanding job' docs/PARITY.md` → no match.

### F10 — six of the note's eleven smoke substance floors dropped; budgets 90/100 → **RESOLVED at head (restored and strengthened, not loosened)**
Commit `9cf41fc`. `SMOKE_CONFIG_OVERRIDE` budgets are the note's 120/130 (`ci.yml:5220-5222`);
`SMOKE_REQUIRE_STATS` regains `"broadcasts":1` (`:5230-5231`); the across-the-pair step asserts all eleven floors
with the measurement inline (`:5250-5305`). I read the hunks: floors were **raised/restored** and budgets raised —
this is the opposite of a checklist-item-1 loosening. Live at the judged sha: docker-smoke log
`across the two seats: planted=4 water=1323 shakes=20 chops=0 fired=1435 tree_income_tenths=20881 strikes=22 vp=5
mature=3 built=30 damage_tenths=7645 ids=34 inflight=6` — every floor holds.

### F11 — `tests/test_bc17_examplefuncsplayer17.nim` does not exist → **RESOLVED at head (coverage added where the oracle cannot reach)**
Commit `64bba33` adds the TANK/SCOUT fall-through test to `tests/test_bc17_baselines.nim:179-222`
(`for kind in [rtTank, rtScout]` — the synthetically built robot must die on its first turn) plus a grep of the
committed Java copy that FAILS if a `RobotType.TANK`/`SCOUT` case ever appears (the bot may not gain behaviour).
The RNG-stream half remains proved differentially by Tier A″ (9/9 pairs bit-exact, whole games) — stronger than a
unit test. Advisory finding; discharged.

### F12 — survival friendly-fire clause at 75 % vs the note's 15 % → **DISMISSED as a defect; verified as implemented (coordinator ruling: honest relabelling, NO CODE CHANGE)**
Verified at head: `tests/test_bc17_survival.nim:25-95` records both measured tables (healthy: selfHarm 54 %;
broken control) and every substituted threshold inline; the `-d:bc17BrokenChassis` negative control recompiles and
re-runs the gate in a subprocess (`:197-220`, `:263-282`) and CI printed `BROKEN-CONTROL: correctly red` twice
(debug + release) at the judged sha (test log 1995, 2009). New file, no prior tolerance, nothing skipped or
deleted — not an item-1 loosening. The ruling is implemented exactly as made; it falsifies no checklist item.

### F13 — NOTICE does not name the oracle trace driver and scenario bots → **RESOLVED at head**
Commit `528c15d`. `NOTICE:905-907` now names `tools/oracle/bc17/Bc17Trace.java` and the six oracle bots
(`bc17idle, bc17scenario, bc17scenariotree, bc17scenariokill, bc17scenariotie, bc17slowbot`), CI-only.

### F14 — `game.docs` uses `"type":"uri"` where item 10's text writes `"type":"text"` → **DISMISSED (coordinator ruling verified; item 10's substance holds)**
Verified pre-existing: `git show f0570643:coworld_manifest_template.json` already carries `"type":"uri"` for
`readme` and every page — the certified 0.9.0 shape; this run did not introduce it. Item 10's substance — the
`{readme, pages[{id,title,content:{type,value}}]}` structure and BOTH `game.protocols` keys — is verified below.
Not a finding.

### F15 — bc17 drew `feed_lines: 0` where all nine other years drew 1–8 → **UPHELD against 07ad48cc; RESOLVED at head**
Commit `544002c`: the bc17 block gained its own `renderFeed` (`client/replay_broadcast.html:8421`, called at
`:8554`; the root cause — `onText`'s ten-way `!isBc17` guard skips the inherited one — is documented at
`:8410-8420`), and `ci.yml:5801-5812` now gates `feed_lines >= 1` on the bc17 replay. Live at the judged sha:
wasm-viewer log 2698 `killfeed lines at the first drawn frame: 7`. Not standing.

**Tally: 4 upheld-against-the-reviewed-sha and since resolved (F1, F2, F10, F15 — the two blocking ones among
them, F1/F2, are closed), 9 further advisories resolved (F3–F9, F11, F13), 2 dismissed as non-findings under
coordinator rulings verified at head (F12, F14). Standing findings from the review: 0.**

---

## Checklist pass (independent) — items 1–15 + the simultaneous-decision clause

**1. CI green; no test loosened — PASS.**
Run **34557429247** on `main` at `526befdb`: conclusion `success`, **13/13 jobs green** (`test`,
`parity-oracle`, `parity-oracle-bc16/17/19/20/21/22/23/24/25`, `docker-smoke`, `wasm-viewer`), observed completed
at my 05:15:43Z poll (jobs 04:17→05:13). Test log grep for `skip|xfail`: only the unrelated
`no nimby.lock in the repo; skipping dependency sync` echo (line 249). All 24 bc17 shards ran twice and reported
`ok` (e.g. `test_bc17_replay: ok (107 checks)`, `test_bc17_survival: ok (13 checks)`).
"No test loosened", from `git log -p f0570643..526befdb -- tests/ .github/workflows/ci.yml`, read hunk by hunk:
38 deleted non-comment lines in `tests/`, every one a nine→ten extension (`policies.len 36→40`, `variants 9→10`,
`pages 11→12`, fixture "NINE of them"→"TEN of them", nine-way guards→ten-way) or a regenerated GV13 fixture line;
`ci.yml` deletions are the same renames plus F10's budget/floor changes, which **raise** floors and budgets
(strengthening). No assertion deleted, no tolerance widened, no skip added, no test file removed.

**2. Replay re-derivation, a test asserts it — PASS.**
`tests/test_bc17_replay.nim` (see F1): frame-by-frame chain comparison + per-tick state digest recorder-vs-deriver
with a negative control; the viewer derives from the same re-derivation (`replay.nim:277-285` `newDeriver` is the
one deriver, compiled into `replay-viewer/bc_replay.nim`), and the wasm side is exercised by
`tools/wasm_replay_smoke.cjs` against both the smoke replay and the committed fixture
(`mismatch_round: -1`, wasm-viewer log 2861/2863 at the judged sha).

**3. Static viewer — PASS.**
`coworld_manifest_template.json:14-16` `"replay_viewer": {"bundle": "static-replay-viewer"}`;
`tools/build_replay_viewer.sh` present, `-rwxr-xr-x`, exercised as the hook (`ci.yml:5533`; `coworld-release.yml:
214-221` fails a pod-served viewer); `tests/test_seats.nim:77-78` asserts no `/client/replay` route; tree grep for
`/client/replay` finds only the starter's `broadcast_core.js` rewrite map (byte-identical to baseline) and the
negative assertions.

**4. Both name spaces — PASS.**
Agents: `decide.nim:862-863` sends `alias`/`opponent_alias` only ("Sealed and simultaneous", `:852`); no real name
in the brief. Viewer: the replay carries `aliases` + `names` (`replay.nim:127`; fixture `names:
["daveey","daveey-1"]`), scorebug plates render both (wasm-viewer log 2682: `CLAN ASH Clan Ash · Plant, water,
donate.`).

**5. Degrade-never-hang, inside 60 % — PASS.**
`episode_timeout_minutes: 20` → 720 s ceiling; bc17 variant budgets `connectTimeoutMs 25000, doctrineBudgetMs
45000, perGameBudgetSeconds 120, matchBudgetSeconds 330` → worst case 30+45+330+30 = **435 s ≤ 720 s**. Every wait
bounded: `decide.nim:1584` (monotonic doctrine budget), `:1604` (`while open.len > 0 and attempt < 2`),
`:1623-1642` (per-attempt deadline handed to curl); `match.nim:688-698` clamps per-game to the remaining match
budget. The only `while true` loops in `years/bc17/` are trove probes bounded by the wrap guard
(`trove.nim:180/186`, `:213/228`). Measured: the 899-round smoke episode simulated in 0.1 s;
`tests/test_bc17_perf.nim` gates the worst map at 60 s and passed twice.

**6. `num_agents` — PASS.**
All ten variants carry `game_config.num_agents: 2`, none at variant top level; certification fixture
`num_agents: 2`, `players: [awu, scaffold]` (read from the template with a JSON parser). `docker_smoke.sh`
enforces the four invariants with the `SEAT-COUNT FAIL:` prefix (`:145-175`) plus the `SMOKE_SEATS` cross-check
(`:82`, `:176-186`) and the override refusal (`:199-204`). **Log grep at the judged sha** (docker-smoke job
103145391023): `SEAT-COUNT FAIL` count **0**; ten episodes, ten × `smoke OK: seats=2 … reason=complete`; the
ten-different-years step passed.

**7. Scripted baseline plays full episodes legally; tuned, not guessed — PASS.**
Full episode to natural end with `reason == complete`: `tests/test_bc17_replay.nim:230`
(`checkEq("the episode completed", r.reason, epComplete)` on an all-scripted match) and the docker-smoke episode
(`reason=complete`, log). Legality: `tests/test_bc17_baselines.nim` asserts `refused_actions == 0` for `orchard`
across the six gate games (`:122`, `:152`) with the header (`:9-28`) explaining the guard-funnel audit and why the
weak floor also measures 0; ops caps respected (`opsOverCap == 0`); `orchard` beats the floor 6/6.
"Tuned with a grid harness": settled by the coordinator — the artefact is `tests/test_bc17_knobs.nim` (244 lines),
verified at head to be exactly the described form: paired seeded games, identical map and opponent, one knob at
low/high, three seeds each, thresholds at roughly half the measured delta, the header recording that six of the
note's fourteen deltas reproduce and listing the eight that do not with the measurement that killed each, and the
anti-inert clause asserted over the whole sweep. `test_bc17_knobs: ok (27 checks)` ×2 at the judged sha. Not
reported unverified.

**8. LLM reply handling — PASS.**
Fence-tolerant extraction in year-neutral `llm.nim`; retry exactly once (`decide.nim:1604` `attempt < 2`,
`:1623-1624` per-attempt budgets, `doctrine_retry` event); fallback to the scripted sheet on second failure /
parse failure / throttle-with-no-candidate (`:1690-1702`), recorded three ways — `results.fallbacks`
(`results.nim:78,97`), a `doctrine_fallback` event naming the cause, and the `falling back` log line — so phase 60
can count it.

**9. Rune-safe truncation — PASS.**
`sim_types.nim:430-459` `truncateRunes`/`truncateBytes` (byte cap still cut on a rune boundary);
`tests/test_bc17_sheet.nim:157-182` feeds 400×U+1F332 (4-byte astral) at the caps and asserts
`validateUtf8() < 0`, rune-length caps and `len mod 4 == 0`; the 16 384-byte reply cap exercised with 20 000
astral runes; `test_bc17_replay.nim:235` asserts the whole written replay is strict UTF-8.

**10. Manifest validates — PASS.**
`game.docs` = `readme` `{type, value}` + `pages` (twelve, each `{id, title, content:{type, value}}`,
`rules-bc17.md` appended); `game.protocols` carries **both** `player` and `global` (both `{type:"uri", value:
…/docs/PROTOCOL.md}`). The `"type":"uri"` discriminator is the repo's certified pre-existing shape (verified at
baseline `f0570643`) — per the coordinator's F14 ruling the structure and both protocol keys are the substance,
and both hold. `tests/test_manifest.nim` asserts the shape, the page list and that the installed `coworld` CLI
accepts the template.

**11. Viewer legible at 360 px — PASS.**
`client/replay_broadcast.html:2623` is exactly `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }`;
word labels hidden under `@media (max-width: 640px)` (shared `:2699` and the bc17 block's own at `:4161` area,
which keeps `#bc17-vp`'s bars and numbers). The killfeed/stat-box overlap gate ran on the bc17 replay at
360/720/1280 px, FIT and 2× (wasm-viewer green at the judged sha).

**12. Release order and scaffold — PASS.**
`coworld-release.yml`: Build the Coworld manifest (`:168`) → Certify locally (`:182`) → **Upload the policies**
(`:225`) → Upload the Coworld (`:323`) → Put the Coworld secret (`:419`); the smoke depends on the image built in
the same run. All three workflows present; `tools/ci/docker_smoke.sh` mode 100755. `tools/ci/policies.json`: 40
entries; the four bc17 ones are two `PLAYER_PROMPT` champions (`battlecode-bc17-orchard`,
`battlecode-bc17-tankrush` — the latter carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) plus two
scripted fillers (`PLAYER_SCRIPTED=orchard`, `=examplefuncsplayer17`), image = the player service's image. The
placeholder gate run verbatim over the five files → **no matches (grep exit 1)** → gate exits 0.

**13. Viewer executes — PASS.**
- `wasm-viewer` **green at the judged sha** (job 103146368725, 04:22→04:28Z, `success`), `needs: docker-smoke`
  (`ci.yml:5496`), and the `Load the bundle in a real browser (ALL TEN years' replays)` step really ran — not
  commented out, no `continue-on-error` — loading all ten replays; bc17: `{"loaded":true,"ms":302,…}` (log 2682),
  soak advanced `round 1 → 313 → 362 / 899`, `scrub selector: #scrub`, endcard shown with a clan line.
- Markers: `replay-viewer/static_replay.js:180` sets `data-replay-loaded="true"` on the worker's first-drawn-frame
  message; `:14-20` sets `data-replay-error="<message>"` on failure — both in the shell's own code paths, file
  byte-identical to the baseline.
- **Playback opens at the game start — PASS with evidence, per the coordinator's ruling.** This runtime has no
  join phase: `replay.nim:277-281` (`newDeriver`) enumerates frames `for r in 1 .. gameRecord(index).rounds`, so
  no pre-`gameStart` frame can exist in a recording; `broadcast.nim` emits `"lob": 0` in every frame (`:799`,
  `:927`, `:1120`) and `ph` is only `playing`/`gameover`, so `chrome_common.js:420`'s `s.ph === 'lobby'` branch is
  unreachable from a recording; `Deriver.seek` clamps to `[0, totalFrames-1]`. The owed assertion exists and ran
  (commit `d8cf0e97`): `tools/ci/viewer_smoke.mjs:766-792,913` records `first_frame` and a `0%-rewind` seek, and
  `ci.yml:5744-5800` gates them on the bc17 replay — live result at the judged sha:
  `first drawn frame: round 1 / 899   after a rewind seek: round 1 / 899` (log 2697). The checklist's
  `lobbyJoinTimeoutTicks` probe is not applicable to a runtime with no lobby, and the tree says so with code.
- Link flags vs bootstrap from the same starter: `replay-viewer/config.nims` carries **no `MODULARIZE`, no
  `EXPORT_NAME`**, and `static_replay_worker.js` uses the matching non-modularized bootstrap (`var Module = {}`
  at `:8`, `Module.onRuntimeInitialized` at `:218`, `importScripts(…'./bc_replay.js')` at `:274`) — the correct
  pairing; the smoke's `loaded: true` is the evidence, and it is green at this sha.

**14. Chrome is the starter's — PASS** (baseline = this repo at `f0570643`, per the MOD-run rule).
`git diff f0570643..526befdb -- client/chrome_common.js client/broadcast_core.js replay-viewer/config.nims
replay-viewer/static_replay.js replay-viewer/static_replay_worker.js` → **empty; all byte-identical**.
`client/replay_broadcast.html`: +608/−3; the three removed lines are the `--statrail` measured-id list (widened in
place to include `bc17-econ`/`bc17-units`) and the two nine-way `!isBc16 && …` guards (widened to ten-way with
`!isBc17`) — nothing else removed; the bc17 game block is appended under the banner
`BC17 additions to the inherited cogame-battlecode chrome` (`:3937` CSS, `:4560`-area markup); no starter id
reused. Transport rules: `relayout()` sets `--hudscale`/`--topband`/`--band`/`--statrail` on `:root`; bc17 boxes
ride `bottom: calc(var(--band, 0px) + …)`; `#endcard` keeps `bottom: var(--band, 0px)`, is shown with `.on` and
every seek dismisses it (`dismissEndcard()` in `seek()`); beats are labelled `<button>`s built by
`buildBc17BeatButtons` with a scoped CSS rule for all thirteen kinds (`:4111-4123`), asserted from the page source
by `tests/test_bc17_beats.nim` (942 checks, green ×2). **`#viewpanel` kept** — correct: bc17 boards are 30×30 to
100×100 continuous-space, larger than the 360 px frame, exactly the pannable case.

**15. Every drawn string fits its frame — PASS.**
The board renderer draws to canvas via worker (`canvas_text.total: 0` on replay runs — covered by nothing, and
correctly **not** read as a pass); `--strict-text-bounds` is correctly dropped on the pannable replay runs and
applied to the worst-case renderer fixture, which at head carries the **bc17 row** (F2 fix; full-cap notes and
motto on both seats, three widths including 360 px, in the page's own extracted CSS, self-asserting full-length
strings). The step ran at the judged sha under `--strict-text-bounds`: wasm-viewer log 2924
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
— **`never_inside` = 0**, `ellipsized` = 0; the fixture's own gate (DOM overflow + full-length assertion) passed.

**Simultaneous-decision clause — PASS.** One decision turn per episode; both seats' provider calls go out as one
parallel batch: `decide.nim:1625-1642` — a single `RequestBatch`, both open seats posted into it, one
`client.curl.makeRequests(batch, …)` with a shared deadline. No sequential per-seat call site exists.

---

## Blocking findings

None. (No `- [<category>] …` lines: the count is zero.)

## Non-blocking observations

- `docs/PARITY.md` §bc17 records that `BODY_ATTACK` and `PHILANTROPIED` are not exercised engine-side by the
  scenario tiers (each with its reason and the Nim-side test that covers the rule) — honest residue, no checklist
  item touched.
- The parity job's measured JVM wall clock at the judged sha is **93 s over the 54 pairs** (log line 1134;
  `bc17 parity: 54 pairs, all bit-exact for whole games, ledger empty` at 1397;
  `tools/ci/parity_ledger_bc17.json` = `{"entries": []}`; Temurin `1.8` asserted at log 438) — far inside the
  80-minute Tier-A″ reduction trigger.
- The `feed_lines` gate is bc17-only (`ci.yml:5802-5812`); the other nine years are measured (1–8) but ungated.
  In scope for a future round, not this one.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1–F15 | — (`r1-fixes.md` was never written; the fixer session died) | every fix verified directly from the diff `07ad48cc..526befdb` (commits `8e27c91`…`d8cf0e97`, one per finding + the checklist-item-13 commit) and from run 34557429247's job logs | n/a — no self-report existed to audit; dispositions above are from the code alone |

## CI status observed

- Run **34557429247** (main @ `526befdb`): queued behind run 34555487533 until ~04:17Z (main's serialized
  concurrency group), jobs 04:17:14Z→05:13:06Z, **conclusion `success`, 13/13 jobs green**, observed at my poll of
  **2026-09-11T05:15:43Z**.
- Evidence greps at this sha: docker-smoke — 0 × `SEAT-COUNT FAIL`, 10 × `seats=2 … reason=complete`, the four
  binary-absence lines, all eleven bc17 substance floors held; wasm-viewer — ten × `loaded:true`,
  `first drawn frame: round 1 / 899`, rewind clamps to round 1, `feed_lines: 7`, fixture `never_inside 0` under
  `--strict-text-bounds`; parity-oracle-bc17 — 54 pairs bit-exact, ledger empty, JVM 93 s, JDK 1.8; test — all
  bc17 shards ok ×2, `BROKEN-CONTROL: correctly red` ×2, no skip/xfail.

BLOCKING: 0
