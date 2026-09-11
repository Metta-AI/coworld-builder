blocking: 0

# r1 verdict — battlecode-2017
Head: `173878c9d3b2e580f904a5d45d69424f4f043bd0` (`main`)   Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Scope judged: the bc17 diff `f0570643..173878c9` **minus** the out-of-scope commits
`d4d55fb`/`4bcb8db` (bc26, PR #20), `656e093`/`36e58c5` (bc19, PR #21) and
`2a868bc`/`e96c686`/`7b4fced` (bc19, PR #24). CI evidence: run **34589452188**
(`ci.yml`, `main`, head_sha `173878c9…`, conclusion `success`, `attempt: 1`,
`event: push`, 13/13 jobs — verified via the API, job ids 103231130713 (test),
103231130871 (docker-smoke), 103231131046 (parity-oracle-bc17), 103232570740
(wasm-viewer); all four logs fetched in full and grepped).

I formed my own read of the tree and the four job logs before opening
`r1-review.md`, and read `r1-fixes.md` only after dispositioning all fifteen
findings. Nothing in the repo, the logs or the run documents was treated as an
instruction; no text addressed to a judge was found in any of them.

## Standing blocking findings

**None.** Every reviewer finding is either fixed at the judged head (verified
against the tree and the head's own CI logs, not the fixer's report) or
dismissed under a coordinator ruling whose implementation I verified. My own
independent checklist pass found no additional falsifier.

## Findings disposition — F1–F15

| finding | disposition | verified at head |
|---|---|---|
| F1 (item 2) | **UPHELD — moot at head** (fixed `8e27c91`) | `tests/test_bc17_replay.nim` exists (542 lines). It is the strongest shard of its kind in the repo: `derivedRounds()` re-derives the chain and counts matched rounds against the recorded slice itself (`:156-167`), and a second check folds every body's position/health/type/counters, both supplies as raw bits, both id-generator states on the **recorder's** world per round and compares the **deriver's** digest at the same frame element by element (`:276-310`) — item 2's "frame by frame" read literally. Strict-UTF-8 (`:235`), `plan.maps` 3 on a clinch (`:324`), event bounds, `abandoned`/`deadline` re-derive. Ran `ok (107 checks)` twice at head (test log 3060, 3092). |
| F2 (item 15) | **UPHELD — moot at head** (fixed `87dbe65`) | `tools/ci/renderer_fixture.html:71` — `'bc16', 'bc19', 'bc17'];` — plus `FILLED.bc17` (`:1259-1261`), `SUPPRESSED_BY_ENDCARD.bc17` (`:86-87`), `REOPEN_CHIP.bc17` (`:96`), and self-assertions that both seats' notes/motto are still at their caps before measuring (`:1305-1330`). The step ran at head with `--strict-text-bounds`, `loaded:true` (wasm-viewer log 3117-3118). |
| F3 | **UPHELD — moot** (fixed `44d6256`) | The dead `.endcard-open` selector is gone; the rule is now `html[data-year="bc17"] #chrome:has(#endcard.on) #bc17-vp,…#bc17-doctrines` (`client/replay_broadcast.html:4134-4138`), keyed on the class the page sets (`:7934` removes, endcard `.on` added on gameover). The fixture reads the **computed** visibility with the card raised and requires the boxes back when it drops (`renderer_fixture.html:1088-1112`). |
| F4 | **UPHELD — moot** (fixed `b9f4e4b`) | `<div id="bc17-fund">` at `:4709`; `s.bc17_fund` read at `:8458` and rendered (ledger + all-four-rungs tiebreak). `tests/test_viewer.nim` id list is six-wide and asserts the reader. |
| F5 | **UPHELD — moot** (fixed `08bf773`) | bc17's `renderDoctrines` now draws the fallback badge (`:8391-8393`) and the "what the cog actually sent" disclosure (`:8410-8413`), in the shared class names (`.dfall`, `.dsub`, `.dbadge`) the fixture selects. |
| F6 | **UPHELD — moot** (fixed `823c32f`) | docker-smoke step "The built image has no java, javac, node or npm on its PATH" (`ci.yml:4307-4340`), `command -v` through the image's own shell with the `|| true`-inside/probe-must-resolve-`sh` traps closed. Ran at head: `absent from the image's PATH: java / javac / node / npm` (docker-smoke log 2380-2383). |
| F7 | **UPHELD — moot** (fixed `fa7200c`) | `docs/RULES-BC17.md:262` — "## Playback pacing, measured", carrying the measured 0.126 ms/round and the maxRounds-not-soak rule; `ci.yml`'s two citations now resolve. |
| F8 | **UPHELD — moot** (fixed `3149f79`) | `docs/RULES-BC17.md:253` — "**FOUR AND NOT THREE**", agreeing with `docs/PARITY.md:2274` and with the patch (four `Math.random()` sites rewritten); the two other copies of "three" corrected with it. |
| F9 | **UPHELD — moot** (fixed `8b7c89a`) | `docs/PARITY.md` §What is NOT compared (bc17) now records Tier B′(a) as **done and measured** (peak 3 % of a limit over 54 pairs) and no longer defers to an "outstanding job". |
| F10 | **UPHELD — moot** (fixed `9cf41fc`) | All eleven of the note's substance floors are asserted in "The bc17 episode really played bc17" (`ci.yml:5286-5399`) including the two never-droppables; budgets back to the note's 120/130; `broadcasts:1` restored to `SMOKE_REQUIRE_STATS`; `chop_actions` recorded-not-asserted with its measured 0 and the map reason. Held at head: `planted=4 water=1323 shakes=20 chops=0 fired=1435 tree_income_tenths=20881 strikes=22 vp=5 mature=3 built=30 damage_tenths=7645 ids=34 inflight=6` (docker-smoke log 3741). |
| F11 | **UPHELD (advisory) — moot** (addressed `64bba33`) | The dedicated shard is deliberately not rebuilt (Tier A″ proves the RNG stream differentially, 9/9 pairs bit-exact — stronger); the one branch the oracle cannot reach, the TANK/SCOUT fall-through, is covered synthetically in `tests/test_bc17_baselines.nim:179-214` with a surviving-SOLDIER contrast. Verified in the tree; shard `ok (75 checks)` ×2 at head. |
| F12 | **DISMISSED — no defect** (coordinator-ruled, implementation verified) | The survival gate ships clauses at measured values, each named with its measurement inline (`tests/test_bc17_survival.nim:72-95`, friendly-fire committed 75 % vs measured 54 % — `selfHarm=50335/92413` in the head's test log 3247), and the `-d:bc17BrokenChassis` negative control runs in CI and goes red (`BROKEN-CONTROL games=6 … failures=21 … correctly red`, test log 3248-3257). New file, no prior tolerance widened; not a loosening under item 1. |
| F13 | **UPHELD — moot** (fixed `528c15d`) | `NOTICE:905-906` credits `Bc17Trace.java` and the six scenario bots (the seventh, the scaffold bot, was already credited byte-for-byte in its own section); `tests/test_manifest.nim` now walks `tools/oracle/bc17` and requires a NOTICE mention per `.java` file. |
| F14 | **DISMISSED** (coordinator-ruled deliberate divergence) | `game.docs` uses `"type":"uri"` where the checklist writes `"type":"text"` — pre-existing across all twelve pages of a published, certified coworld; item 10's **substance** verified independently below. Not introduced by this diff. |
| F15 | **UPHELD — moot** (root-caused, fixed `544002c`) | Root cause confirmed from the page: the ten-way `!isBc17` guard skips the inherited `renderFeed` and bc17's block had none; the block now rebuilds `#killfeed` from beats at-or-behind the playhead (`:8419-8446` area), and `ci.yml` gates `feed_lines >= 1` on the bc17 replay. At head: `killfeed lines at the first drawn frame: 7` (wasm-viewer log 2890). |

Score for the reviewer: 13 of 15 findings reproduce from the code at the
reviewed sha (F12 and F14 were correctly labelled advisory/recorded by the
reviewer itself). I could refute none of the 13 as mis-read; all 13 are fixed
at head. No finding is OUT OF SCOPE — all were filed against bc17 work.

## Checklist pass (independent)

| item | status | evidence (path:line or run/log) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | Run 34589452188: `success`, 13/13, attempt 1, push, main, head_sha `173878c9…`. `git log -p f0570643..173878c9 -- tests/` read hunk by hunk: 24+ new bc17 shards; modified files (`test_manifest.nim`, `test_viewer.nim`, `test_rules_combat.nim`) are additive or nine→ten tightenings (e.g. `variants.len 9→10`, `policies 36→40`, ten-way guard strings); fixtures regenerated for the GV bump per the note; no deleted assertion, no widened tolerance, no `skip`/`xfail`, no test file removed. The fixes file's own claim of "four removed lines, all count/list updates" matches the diff. |
| 2 Replay re-derivation | **pass** | `tests/test_bc17_replay.nim:156-167` (chain matched-round count), `:276-310` (recorder-vs-deriver per-tick digest, element by element); viewer derives from the same deriver (`replay.nim newDeriver/advance`); `wasm_replay_smoke.cjs` re-runs it under wasm on both the smoke replay and the committed fixture (`ci.yml:5936-5938`). |
| 3 Static viewer | **pass** | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, `-rwxr-xr-x`, exec-bit gated in CI (`ci.yml:5510-5520`); no `/client/replay` pod path (the two hits in `client/broadcast_core.js:372,385` are the starter's legacy URL-rewrite map, byte-identical to base; `coworld-release.yml:220` is the guard *against* a pod viewer). |
| 4 Both name spaces | **pass** | Prompt payload carries `alias`/`opponent_alias` only (`decide.nim:862-863`); `names[]` only in the replay (`replay.nim:213`, `broadcast.nim` frame) and drawn by the viewer; `AliasA`/`AliasB` untouched. |
| 5 Degrade-never-hang | **pass** | Every wait bounded: `decide.nim:1584` (`doctrineBudgetMs`), `:1604` (`attempt < 2`), `:1623-1642` (per-attempt deadline into `makeRequests`); `match.nim:688,698` (match/per-game budgets); bc17 variant: connect 25 000 + doctrine 45 000 + match 330 s + grace ⇒ 435 s ≤ 720 s (60 % of 1200 s, `episode_timeout_minutes: 20`, manifest:9). `test_bc17_perf.nim` gates the worst map at 60 s. |
| — one parallel batch | **pass** | `decide.nim:1642` — one `client.curl.makeRequests(batch, …)` for both seats; no sequential call site. |
| 6 num_agents | **pass** | All **ten** variants carry `game_config.num_agents: 2`, none at variant top level; `certification.game_config.num_agents: 2`, `len(certification.players)==2`, `len(certification.game_config.players)==2` (verified by script over the template). `docker_smoke.sh:148-227` enforces the four invariants + `SMOKE_SEATS` cross-check + override refusal with the `SEAT-COUNT FAIL:` prefix. **`grep -c "SEAT-COUNT FAIL"` over the full head docker-smoke log = 0**; ten episodes each `seats=2`, ten distinct `year` values asserted (log 3928). |
| 7 Scripted baseline full episodes legally | **pass** | `tests/test_bc17_baselines.nim:100-143`: six full games to the natural end, every game a real ladder `end_reason`, `refused_actions == 0` for both chassis (the legality audit — every guard funnels through `refuse()`), ops cap never hit, orchard 6/6; episode-level `reason == "complete"` asserted by `test_bc17_replay.nim:230` and by docker-smoke on the real image. The "tuned with a grid harness" half is **SETTLED by coordinator ruling**, implementation verified: `tests/test_bc17_knobs.nim` — paired seeded games, one knob low/high, 3 seeds, thresholds at ~half the measured delta, **eight** of the note's fourteen predicted deltas honestly recorded as NOT reproducing with the measurement that killed each (`:30-55`), plus the anti-inert clause over the whole sweep. |
| 8 LLM reply handling | **pass** | Tolerant extraction (`sheet_common.nim:56-58`, fences + prose + first-brace..last-brace); retry exactly once (`decide.nim:1604`, `:1623-1624`); fallback to the year's scripted sheet with `results.fallbacks` counting it (`decide.nim:1697`, `results.nim`) and a `doctrine_fallback` event (`:1698`). |
| 9 Rune-safe truncation | **pass** | `truncateRunes`/`truncateBytes` (`sim_types.nim:430,439`); `tests/test_bc17_sheet.nim:157-182` feeds 4-byte astral input at the caps, asserts `validateUtf8` and rune-boundary cuts, incl. the 16 384-byte reply cap; beat labels ≤ 120 runes asserted in `test_bc17_beats.nim`. |
| 10 Manifest validates | **pass** (with the F14 ruled divergence) | `game.docs.readme` `{type,value}` + **twelve** `pages` each `{id,title,content:{type,value}}` (verified by script); `game.protocols` carries **both** `player` and `global`. The `"uri"` vs `"text"` discriminator is the pre-existing, published, coordinator-ruled house shape. |
| 11 Legible at 360 px | **pass** | `client/replay_broadcast.html:2623` — `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }`; word labels hidden under `@media (max-width: 640px)` (seven blocks incl. bc17's); killfeed-overlap gate ran at 360/720/1280 px on the bc17 replay at head. |
| 12 Release order and scaffold | **pass** | `coworld-release.yml`: Build manifest `:168` → Certify `:182` → **Upload policies** `:225` → Upload Coworld `:323` → Secret put `:419`; three workflows present; `docker_smoke.sh` 0755; `policies.json` = 40 entries, bc17's four appended (2 `PLAYER_PROMPT` champions + 2 scripted fillers), champion #2 carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep run verbatim → no matches (gate exits 0). |
| 13 Viewer executes | **pass** | `wasm-viewer` green at head **including** "Load the bundle in a real browser" over all ten replays (log 2552-2890); step not commented, no `continue-on-error` (the only one in `ci.yml:1009` is a bc20 informational step); `needs: docker-smoke` (`ci.yml:5496`). Markers in the shell's own paths: `static_replay.js:180` (`data-replay-loaded` on the worker's first-frame message), `:14-20` (`data-replay-error`). **Game-start bullet settled with a code-path proof + live assertion** (coordinator-ruled, verified): `replay.nim:279` enumerates frames `for r in 1 .. rounds` — no lobby frame can exist; `seek` clamps to `[0, totalFrames-1]` (`:321-329`); CI gates the bc17 replay's first frame to `[1, max(10, total/50)]` and the rewind clamp to round ≥ 1 (`ci.yml:5763-5822`); at head: `first drawn frame: round 1 / 899   after a rewind seek: round 1 / 899`. Link flags and bootstrap from the same starter: `config.nims` has **no MODULARIZE/EXPORT_NAME** and the worker uses `var Module = {}` + `Module.onRuntimeInitialized` + trailing `importScripts` (`static_replay_worker.js:8,218,274`) — the correct non-MODULARIZE pairing; `loaded:true` is the evidence. |
| 14 Chrome is the starter's | **pass** | For a MOD the starter is this repo at `f0570643`: `chrome_common.js` and `broadcast_core.js` **byte-identical** to it (diffed directly). `replay_broadcast.html` +624/−3, the three removals being the `--statrail` list and the two nine-way guards, each replaced in place by the ten-way form; bc17 block appended under the banner `BC17 additions to the inherited cogame-battlecode chrome` (`:3937`, `:4596`); no starter id reused. Transport rules: `relayout()` sets `--hudscale`/`--topband`/`--band`/`--statrail` on `:root` with `bc17-econ`/`bc17-units` in the measured set (`:8010-8023`); `#endcard { top: var(--topband); bottom: var(--band) }` (`:1856-1858`), shown via `#endcard.on` (`:1887`), seek removes `.on` (`:7934`); beat buttons via `buildBc17BeatButtons`/`applyBc17BeatSpoilers` (`:8540,8545`), all thirteen kind rules scoped to `html[data-year="bc17"]`; `#viewpanel` **kept** — justified, boards 30×30–100×100 exceed the 360 px frame. |
| 15 Every drawn string fits its frame | **pass** | `viewer_smoke.mjs` reports `canvas_text`; `--strict-text-bounds` deliberately dropped on the pannable replay runs (the flag's own exclusion) and **armed on the renderer fixture** (`ci.yml:5979-5984`), which ran at head (`loaded:true`, `canvas text: 0 drawn … (--strict-text-bounds)`, wasm-viewer log 3117-3118 — this chrome draws its text in DOM, so the fixture's gates are the DOM scans: frame-escape, hidden-content, endcard-band, chip reachability, all with the bc17 row and with self-assertions that the full-cap strings were not shortened before measurement, `renderer_fixture.html:1305-1330`). Doctrine text gets a reserved, capped, scrolling band (`#bc17-doctrines` `max-height: 42vh; overflow-y: auto`); notes are sentences drawn whole, not ellipsized. |

**The fix-forward gate, judged on its own terms (the brief's licence):** the
original `ff_round == 1` equality asserted the *instrument*, not the viewer —
the 250 ms poll races free-running playback, measured 1–3 across ten years on
one runner and 1 on two other runs of the same bytes. The replacement keeps
the exact claim where it is race-free (rewind seek clamps to round 1, a
positioned jump) and bounds the racy read with a floor (1 — no earlier frame
exists by construction) and a window (`max(10, total/50)` = 17 of 899 — small
enough to catch a viewer opening mid-game). Negative controls (round 0,
round 402, missing rewind) were run red. **Sound; not a papering-over.**

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | new 542-line shard, digest per frame, `ok (107)` | file + both mechanisms present; `ok (107 checks)` ×2 in head test log | yes |
| F2 | bc17 row added, found a real nowrap defect, green with flag | row + caps self-check in tree; step green with flag at head | yes |
| F3 | `:has(#endcard.on)` + fixture computed-style gate | rules at `:4134-4138`; fixture raises card and reads visibility | yes |
| F4 | markup + reader + tiebreak ledger | `:4709` markup, `:8458` reader | yes |
| F5 | badge + disclosure in shared class names | `:8391-8393`, `:8410-8413` | yes |
| F6 | `command -v` probe step, green | step in tree; four "absent" lines in head log | yes |
| F7 | section written with measured value | `RULES-BC17.md:262` | yes |
| F8 | four sites, three documents aligned | `RULES-BC17.md:253`, `PARITY.md:2274` | yes |
| F9 | paragraph states the measurement | verified in `PARITY.md` §What is NOT compared | yes |
| F10 | all eleven restored, measured, budgets 120/130 | `ci.yml:5216-5399`; head log line with all eleven values | yes |
| F11 | synthetic fall-through block, file not rebuilt (ruled) | `test_bc17_baselines.nim:179-214` | yes |
| F12 | no change, ruled | measured-inline header + live red control in head log | yes |
| F13 | NOTICE + gated walk of `tools/oracle/bc17` | `NOTICE:905-906`; `test_manifest` walk | yes |
| F14 | no change, ruled | pre-existing shape, substance verified | yes |
| F15 | renderFeed added + `feed_lines` gate | `feed_lines 7` at head; gate in `ci.yml:5823-5834` | yes |
| item 13 bullet | code-path proof + first-frame/rewind assertion | `replay.nim:279,321-329`; head log `round 1 / 899` both reads | yes |

No disposition in the fixer's table failed verification.

## Non-blocking observations

- **Parity side-band counters disagree while the traces are bit-exact**: on
  `examplefuncsplayer17/GreenHouse` the Java summary printed `actions=27261`
  and the Nim summary `actions=27251` (parity log ~10:30:26) although both
  traces are 212 673 lines and the comparator reports bit-exact. The `actions=`
  stderr summaries are per-side instrumentation, not part of the compared
  trace; the gate is unaffected, but a one-line alignment would remove a
  head-scratcher.
- **bc19 docker-smoke teardown SIGSEGV** (branch run 34583465003, attempt 1):
  the episode completed and scored, then the game container crashed at process
  exit in `mummy.destroy → orc.nim nimDecRefIsLastCyclicDyn`. The commit under
  test touched only `wasm-viewer` files, so the red is causally unrelated to
  the diff; the rerun passed and it did not reproduce at the judged sha. It is
  a real, pre-existing, year-neutral teardown bug (it briefly violates the
  "exit 0 whenever results+replay were attempted" contract) and belongs in
  residue for the runtime, not against bc17.
- Carried-forward, out of scope per the brief: `renderer_fixture.html`'s
  `FILLED` map lacks a `bc19` key; the bc20/bc21/bc24/bc25 comparator
  zip-tail/`toHex` quirks; `match.nim`'s `max(1, min())` per-game clamp.
- The coworld version bump is deliberately absent (phase 40's job); the design
  note's `0.9.0 → 0.10.0` pin is stale against the published 0.11.x line —
  noted, not a finding.

BLOCKING: 0
