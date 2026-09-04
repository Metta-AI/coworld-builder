blocking: 0

# r1 verdict — battlecode-2021

Head: `d2922438d0ac8a5b528d4f303f6b9d4e31d715f4` (confirmed `git -C /workspace/cogame-battlecode rev-parse HEAD`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + the simultaneous-decision clause)
Independent read written before reading review/fixes: **yes** — design note (all 1725 lines), the
`e17947d9..HEAD` diff, `coworld_manifest_template.json`, `tools/ci/{docker_smoke.sh,policies.json,
viewer_smoke.mjs,renderer_fixture.html,parity_ledger_bc21.json}`, `client/replay_broadcast.html`,
`replay-viewer/{config.nims,static_replay.js,static_replay_worker.js}`, `src/battlecode/{decide,match,
replay,results,sim_types}.nim`, `years/bc21/{rules,world,votes,economy}.nim`, 8 test shards, the full
log of CI run **33886193070**, and its `viewer-smoke` artifact — before opening `r1-review.md` or
`r1-fixes.md`.

Note on scope: this is a MOD run on an already-shipped repo. The bc26/bc20 code and the manifest's
inherited choices (e.g. `game.docs` `"type":"uri"`) predate the diff; I judged the checklist against
the repo as it stands and flag inherited facts as inherited.

---

## Standing blocking findings

**None.** Every checklist item verified at the current head, from the tree or from cited CI
evidence (run id 33886193070). No reviewer finding falsifies a checklist item at head.

---

## Refuted / Resolved (the reviewer's findings, each re-tested at head)

The r1 review reported **0 blocking, 13 non-blocking (F1–F13)** plus 4 could-not-determine items.
I attempted to refute each; none was fabricated. Seven were real at the reviewed sha (`bdc06b04`)
and are **resolved at head** by the r1 fix commits; six are accurate observations that falsify no
checklist item and stand as advisory only.

### F1 — dead `--killfeed-overlap` gate → RESOLVED at `8f0821a`
- Evidence: `tools/ci/viewer_smoke.mjs:224` — `const OVERLAP_SCRIPT = () => {` (a real function,
  no longer a source string), `:268` `page.evaluate(ZOOM_SCRIPT, value)` in its own evaluate before
  the 350 ms settle, `:800` `overlap.filter((r) => r.ok !== true)`.
- Verified in the green run's own artifact (not the fixer's claim): `viewer-smoke-replay{,‑bc20,‑bc21}.json`
  from run 33886193070 each carry **6/6 probe rows `ok: true`** with populated `year`/`statrail`/
  `killfeed`/`boxes`/`hits` (e.g. bc21 @360 fit: `statrail 90px`, killfeed `[211,96,353,575]`,
  boxes `bc21-influence [216,608,352,665]`, `hits: []`), where the previous run's rows were null.
  `failure: null` on all three.

### F2 — RULES-BC21 claimed a nonexistent 80 % bytecode assertion → RESOLVED at `b3ae368`
- Evidence: `docs/RULES-BC21.md` §Divergences item 1 now says the job **measures** the boundary
  ("peak use is **102 %** of the limit on all five traced maps … first cut-off at rounds 27, 23,
  33, 23 and 246") and that `cutoff − 1` sizes the Tier A window. The stale claim in
  `tools/parity_trace_bc21.nim` is gone (`grep '80 %' → 0 hits` in both files).

### F4 — unscoped `.beat-marker.doctrine`/`.capture` overrides bled into bc26/ctf → RESOLVED at `5e2710e`
- Evidence: `client/replay_broadcast.html:2887-2893` — all seven bc21 kind rules now carry
  `html[data-year="bc21"]`; the inherited `:1732` (`.beat-marker.capture`, team-coloured,
  board-scaled) and bc26 `:2639` (`.beat-marker.doctrine`, blue) rules win again on their years.

### F5 — bids.nim header + RULES item 11 stated formulas the code does not use → RESOLVED at `0258680`
- Evidence: `chassis/bids.nim:15-17` now states the multiplicative hash
  `((id xor round*0x9E3779B1) * 0x85EBCA6B) shr 13) mod 3` matching the code at `:61-62`, and
  `:24` states the bank `15 + round/10` capped at 150 matching `:94`; `docs/RULES-BC21.md:355-361`
  states the same. Comment/doc only; no seeded game moved (CI green, fixtures' `mismatch_round: -1`).

### F6 — knob-gate header recorded 3 of 5 statistic swaps and pointed at a PARITY.md section that does not exist → RESOLVED at `41dc445`
- Evidence: `tests/test_bc21_knobs.nim:47-74` now names itself the record and lists **all five**
  substitutions with reasons and measured numbers. The commit is comment-only: no assertion,
  threshold or statistic changed (diff read line by line; shard still `ok (19 checks)` both modes).

### F8 — bc21 preamble lacked HOW A GAME ENDS / the end ladder → RESOLVED at `3c9f77d`
- Evidence: `src/battlecode/decide.nim:218-224` — `HOW A GAME ENDS` heading with the full
  five-rung ladder (annihilated → more votes → more Centers → more influence → coin flip from the
  map's own seed) above the points formula, matching the bc20 sibling's shape.

### F12 — `convictionAtSpawn` did the `float × int` product in float64 → RESOLVED at `d292243`
- Evidence: `src/battlecode/years/bc21/world.nim:399` —
  `int(ceil(float64(RobotSpecs[kind].convictionRatio * float32(influence))))` — Java's float
  product, widened only at the ceil, with `InternalRobot.java:67 @ ed39c1a4` cited in the comment.
  New assertion `tests/test_bc21_build.nim:80-81` pins the first divergent value (2 995 933 → 2 097 153),
  and the seven pre-existing low-influence vectors are byte-identical above it — an assertion was
  **added**, none changed. Divergence unreachable in play (`ROBOT_INFLUENCE_LIMIT` fault guard),
  so committed fixture hash chains are untouched — confirmed by the head run's
  `mismatch_round: -1` on both committed fixtures.

### F3 (parity tiers weaker than the note; non-empty ledger) — stands as ADVISORY, not blocking
- Verified accurate at head: Tier A windows are `cutoff−1` (26/22/32/22/245), the note's
  round-300/700/1500 trace Tier B does not exist (the name is reassigned to the two JDK arithmetic
  steps, `parity_tiers_bc21.py:30-31` says so), and `tools/ci/parity_ledger_bc21.json` has five
  entries against the note's declared "empty ledger" exit state — all five root-caused to one
  named oracle-bot cause (the JVM cutting the Java bot off mid-turn at 102 % bytecode use), each
  with round + map + cause + docs anchor, satisfying the idea's Fleet-card pin.
- Refutation as a *blocking* finding: the ACCEPTANCE CHECKLIST — the only definition of blocking —
  has no parity item. The mechanism is implemented, blocking-against-ledger, and green
  (run 33886193070 `parity-oracle-bc21`: "Tier A bit-exact and Tier C within the ledger on 5
  pairs"). Largest design-vs-code delta of the run; recorded for phase 60, counts 0 here.

### F7 (record→re-derive covers 3 of 6 end reasons) — stands as ADVISORY
- Checklist item 2 requires frame-by-frame re-derivation asserted by a test, which holds
  (see item 2 below). The unmet thing is the design note's broader per-end-reason claim; the split
  is declared and asserted in the shard itself (`test_bc21_replay.nim:103-110, 272-279`).

### F9 / F10 / F11 / F13 — REFUTED as defects, accurate as observations
- F9: the shipped docs (`docs/PROTOCOL.md`, `docs/REPLAY.md`) describe the recorded shapes
  correctly; only the note's sample payload differs. Nothing withheld from a seat, nothing
  un-drawable. No checklist item touched.
- F10: the 32-round poll mask on the per-game guard is deliberate, asserted by
  `test_bc21_replay.nim:228-230`, and bounded (~0.1 s per game at the measured 3.1 ms/round vs a
  110 s guard). Item 5's bound and the 445 s ≤ 720 s arithmetic hold.
- F11: emission-time legality is enforced structurally (every `world.nim` action proc re-checks its
  own `canX` and no-ops on failure); the sampled audit plus the structural guards satisfy item 7's
  testable half; the vacuous `opsLeft < 0` assertion is harmless and would arm if `spend(r, n>1)`
  ever appeared.
- F13: `game.docs` `"type":"uri"` is inherited unchanged from the shipped canonical 0.2.0 manifest
  (verified at `e17947d9`), pinned by the design note, shape-asserted by `test_manifest.nim`, and
  accepted by the installed coworld CLI (green step in run 33886193070). Item 10's structural
  requirement is what is checkable, and it holds. Inherited, not manufactured by this run.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **PASS** | Run **33886193070**, `push` on `main`, headSha `d292243…`, conclusion **success**, 6/6 jobs (`gh run view --json jobs,conclusion,headSha`). `git log -p --since="2026-09-04T09:00Z" -- tests/`: 5 commits — `06d01b8`/`7ee5da7` (new bc21 shards + fixture), `cb4d6fb` (type adaptation, assertion **strengthened**: 1 replaced by 4 incl. the bc21-name-on-bc20 fallback pin), `41dc445` (comment-only, read line by line), `d292243` (one assertion **added**). No skip/xfail/deleted assertion/widened tolerance/removed file anywhere in the hunks. |
| 2 Replay re-derivation | **PASS** | `replay.nim:285-309` steps the same `years/dispatch` session and compares **every** round's hash against `hash_chain_rounds`; `tests/test_bc21_replay.nim:116,155,264-268,345` assert clean re-derivation incl. the abandoned game via the one load-bearing `plan.abandonAfter` record; chain content is real (`rules.nim:277-295`, 8 per-team values + 3 globals). Viewer displays from the same re-derivation (wasm sim; endcard auction re-derived, `test_bc21_replay.nim:357-376`). CI: `wasm_replay_smoke.cjs` × 5 replays all `mismatch_round: -1`. |
| 3 Static viewer | **PASS** | `coworld_manifest_template.json` `game.replay_viewer = {"bundle":"static-replay-viewer"}` (read via json); `tools/build_replay_viewer.sh` present, `-rwxr-xr-x`, asserted executable in ci.yml + release wf; `grep -rn '/client/replay'` finds only the forbidding guard (`coworld-release.yml:220`), the test that asserts no route is served (`test_seats.nim:75-78`), and the inherited byte-identical `broadcast_core.js` legacy-path map. |
| 4 Both name spaces | **PASS** | `decide.nim:275-276` — observation carries `alias`/`opponent_alias` only, no real name, no per-round channel; `replay.nim:127` `names[]` + `results.nim:79` spectator-side; drawn only by the page (endcard `esc(s.names[slot])`, scorebug plate-sub). |
| 5 Degrade-never-hang | **PASS** | attempt1 20 000 / retry 12 000 / `doctrineBudgetMs` 45 000 hard cap (`decide.nim:333-395`); `connectTimeoutMs` 25 000; `perGameBudgetSeconds` 110 monotonic (`rules.nim:376-379`, 32-round poll, bounded overrun ≈0.1 s); `matchBudgetSeconds` 340 clamping each game (`match.nim:204-214`); round loop capped at 1500. Worst case 30+45+340+30 = **445 s ≤ 720 s** (`episode_timeout_minutes: 20`); measured worst single game 4.655 s (release perf shard, CI log). |
| 6 num_agents | **PASS** | `num_agents: 2` inside all three variants' `game_config` and `certification.game_config`, absent at variant top level (read via json; `test_manifest.nim` asserts both directions). `docker_smoke.sh:141-186` — all four invariants + `SMOKE_SEATS` second declaration (`:82`, substituted default 2), each `SEAT-COUNT FAIL:` + non-zero. **`grep 'SEAT-COUNT' <full log of 33886193070> → 0 hits**; all three episodes `smoke OK: seats=2 … reason=complete`. |
| 7 Scripted baseline full episodes legally | **PASS** | All-scripted to natural end with `reason == complete`: `test_bc21_replay.nim:115,135,317` (`epComplete`) + docker-smoke bc21 episode `reason=complete` in the real container. Legality: `test_bc21_baselines.nim` (b) audits six full 1500-round games (world invariants, budgets, flags, bids) with zero violations, plus structural emission-time guards in every `world.nim` action proc; budgets pinned at 1/10 Java limits. "Tuned, not guessed": the tree carries the harness — `test_bc21_knobs.nim` plays paired low/high seeded games per knob, its header records the **measured** deltas at GV06 (`:17-45`) with every gate at ~half the measured delta; defaults are the ported California Roll build with `slandererBreakpoints` generated from the engine formula and byte-diffed in CI against the bot's shipped table (`economy.nim:124-132`, NOTICE §StoneT2000). Same reading as the bc20 r1 verdict's precedent for the identical clause. |
| 8 LLM reply handling | **PASS** | Fence/prose-tolerant `extractJsonObject` via `sheet.parseReply`; exactly one retry (`while open.len > 0 and attempt < 2`, `decide.nim:354`); fallback = all-defaults california-roll sheet, recorded three ways (`doctrine_fallback` event with cause, `results.fallbacks[slot]`, `falling back` log line; retries log `will retry`). Throttle fast-fail skips the pointless retry. |
| 9 Rune-safe truncation | **PASS** | `sim_types.nim:191-215` `truncateRunes`/`truncateBytes` (byte cap cut on a rune boundary); applied to notes/motto/unknown keys/reply/provider errors; `test_bc21_sheet.nim:149-166` feeds 4-byte astral input at every cap; `test_bc21_replay.nim` strict-UTF-8-parses the written replay bytes. |
| 10 Manifest validates | **PASS** | `game.docs.readme` = `{type,value}`, five `pages` each `{id,title,content{type,value}}` (incl. new `rules-bc21.md`); `game.protocols` carries **both** `player` and `global`. `type` is `uri` not the sketch's `text` — inherited unchanged from the shipped canonical 0.2.0 manifest, accepted by the installed coworld CLI ("The coworld CLI accepts the manifest template" green in 33886193070). |
| 11 Legible at 360 px | **PASS** | `client/replay_broadcast.html:2571` `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `:2647-2649` `@media (max-width: 640px)` hides `.plate-sub`; bc21 boxes drop labels ≤760 px (superset). Fixture renders all three years at 360 px with full-cap text, green. |
| 12 Release order and scaffold | **PASS** | `coworld-release.yml`: build manifest (:168) → certify (:182) → **upload-policies** (:225) → upload-coworld (:323) → secret put (:419). Three workflows present; `docker_smoke.sh` `-rwxr-xr-x`; `policies.json` = 12 policies, 4/year; bc21: 2 `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 (`battlecode-bc21-muckrush`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate run by me: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files → no match, exit 0 path taken. |
| 13 Viewer executes | **PASS** | `wasm-viewer` `needs: docker-smoke` (ci.yml:1029); its "Load the bundle in a real browser (ALL THREE years' replays)" step **ran** in run 33886193070 — `{"loaded":true,…}` for `replay.json`/`replay-bc20.json`/`replay-bc21.json`, three differing scrub readouts each, `scrub selector: #scrub`, endcard shown with a clan line, soak advancing (`round 3 → 195 → 243`); no `continue-on-error` in the job. Markers from the shell's own paths: `static_replay.js:180` sets `data-replay-loaded` on the worker's post-first-frame `loaded` message; `:14-20` sets `data-replay-error`. No recorded lobby in this lineage (frames start at round 1, pre-match doctrine events are feed lines, not frames) — smoke's 0 % readout is already in-game and playback advances immediately. Link flags/bootstrap same starter and agree: `config.nims` has **no** MODULARIZE/EXPORT_NAME; worker uses `var Module = {}` + `Module.onRuntimeInitialized` (`static_replay_worker.js:8,218`); the smoke's `loaded: true` × 5 is the evidence. |
| 14 Chrome is the starter's | **PASS** | `client/chrome_common.js` and `broadcast_core.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/` (diff + sha256, both f7860b4c… / 226aea03…); `replay_broadcast.html` = inherited page + banner-commented bc21 block; only 3 deletions in the whole diff: the `#killfeed` bottom rule (the design's named `--statrail` fix) and two `if (!isBc20)` → `if (!isBc20 && !isBc21)` hooks. Transport: `relayout()` sets `--hudscale/--topband/--band/--statrail` on `document.documentElement` in a fixed-point loop (`:4013-4038`); bc21 boxes ride `calc(var(--band) + …)`; `#endcard { bottom: var(--band,0px) }` shown with `.on` (the styled class) and `seek()` calls `dismissEndcard()` first (`:3785`), transport buttons and keyboard too (`:4055,4083`); beats are labelled `<button>`s built by `buildBc21BeatButtons` (own name), CSS for all ten emitted kinds (bc21-scoped `:2887-2893` + shared `.game/.build/.end`); `#viewpanel` **kept** and justified — 48×48 board renders 768 px vs the 360 px frame (pannable). |
| 15 Every drawn string fits | **PASS** (with the stated reading) | Model-authored text in this viewer is **DOM**, not canvas (doctrine panels, scorebug motto, endcard are `innerHTML`), so `canvas_text total: 0` on the replay smokes covers nothing — and the board is pannable, so `--strict-text-bounds` is correctly dropped there and the counts read (0). The checklist's required worst-case renderer fixture **exists and gates**: `tools/ci/renderer_fixture.html` — 9 iframes (3 years × 360/720/1280 px), full-cap 280-rune notes + 48-rune motto (astral-plane) on both seats, page's own extracted CSS (145 408 bytes loaded, asserted `:315-319`), containment + no-hidden-overflow + panel ≤ half frame + **asserts its own strings are still full-length** (`:396-406`); driven by `viewer_smoke.mjs --strict-text-bounds` in its own ci.yml step (`:1238-1264`), which requires `data-replay-loaded` — set only when all nine verdicts are null. Green in 33886193070 (`{"loaded":true,…}`, `dist/fixture/viewer-smoke.json` `failure: null`). Ellipsized count 0. |
| Simultaneous batch | **PASS** | One decision turn per episode; the LLM seats' requests fill **one** `RequestBatch` issued via `client.curl.makeRequests(batch, …)` (`decide.nim:392-395`) — never sequential. |

## Fixer report audit

| finding | fixer said | I verified at head | agrees |
|---|---|---|---|
| F1 | fixed `8f0821a` | function-valued scripts, own-evaluate zoom, `ok !== true` filter; 18/18 probe rows populated `ok:true` in the head run's artifact (checked myself) | yes |
| F2 | fixed `b3ae368` | RULES-BC21 item 1 now states measurement + 102 % + cutoffs; parity_trace_bc21.nim corrected | yes |
| F3 | no change, documented deviation | no parity checklist item; disclosed in PARITY.md + script docstring; mechanism green | yes |
| F4 | fixed `5e2710e` | all seven bc21 beat rules year-scoped; inherited rules restored | yes |
| F5 | fixed `0258680` | header `:15-17,24` and RULES item 11 now state the code's hash-jitter and `min(150, 15+round/10)` bank | yes |
| F6 | fixed `41dc445` | header records all five swaps; commit is comment-only (diff read) | yes |
| F7 | no change, disclosed | item 2 independently met; split asserted in-shard | yes |
| F8 | fixed `3c9f77d` | `HOW A GAME ENDS` + full ladder at `decide.nim:218-224` | yes |
| F9 | no change | shipped docs describe recorded shapes; note-vs-code only | yes |
| F10 | no change | mask deliberate + asserted; bound holds | yes |
| F11 | no change | structural legality guards; vacuous assertion harmless | yes |
| F12 | fixed `d292243` | float32 product + cited Java line + new pinning assertion; fixtures unmoved (`mismatch_round: -1`) | yes |
| F13 | no change | `uri` inherited, CLI-accepted, shape asserted | yes |
| CND1 (item 7 grid harness) | NEEDS-DESIGN | I rule it PASS from the tree: the knob-teeth harness records measured deltas at GV06 and gates at half of them; defaults carry documented provenance from the ported champion bot (byte-diffed breakpoints) — the same evidence the bc20 r1 verdict accepted for the identical clause | resolved (my call) |
| CND2 (Java expr) | settled with F12 | `InternalRobot.java:67` + `RobotType.java:55` cited; JLS 5.6.2 reading correct | yes |
| CND3 (mirror asymmetry) | no change | documented deterministic asymmetries (exec order, id tiebreak, id-keyed jitter); Tier A bit-exactness on ids/bids/convictions across 5 pairs is strong counter-evidence to a side-dependent rule bug; advisory | yes |
| CND4 (swap record) | fixed with F6 | header is the record | yes |

## Non-blocking observations (mine, beyond the review)

- The reviewer's F3 remains the run's largest design-vs-code delta (Tier A windows 22–245 rounds
  vs the note's pinned 1–200; no round-300/700/1500 trace Tier B; five-entry ledger vs the note's
  "empty ledger" phase-30 exit condition). Everything is disclosed in `docs/PARITY.md`, the ledger
  preamble and (post-F2) `docs/RULES-BC21.md`, and the checklist names no parity item — but the
  in-repo copy of the design note (`docs/plans/2026-09-04-battlecode-2021-design.md`) still
  promises the 80 % assertion and the empty ledger it did not get. Phase 60 should not re-discover
  this as a surprise.
- `canvas_text.total == 0` on every smoke run means the canvas-text probe has no coverage of the
  wasm-rasterized board text (Center influence numbers). Board text is sim-derived, not
  LLM-authored, and the board is pannable, so nothing in item 15 gates on it — but a future fixed-
  arena year variant would inherit a blind spot here.
- `viewer_smoke.mjs`'s two pre-existing string-source scripts (`INIT_SCRIPT`, `READOUT_SCRIPT`)
  are correct IIFEs but are the template shape that made F1 look right; template-side hardening is
  out of this repo's scope (fixer's NOTED item, seconded).

BLOCKING: 0
