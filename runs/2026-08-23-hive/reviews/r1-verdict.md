blocking: 0

# r1 verdict — hive

Head: `34b3dc9e7355d5047e95109ad117f813a509d950` (main, `Metta-AI/cogame-hive`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–13 + simultaneous-batch rule)
Independent read written before reading fixes: **yes** — I read the design note, the full tree
(workflows, manifest, `tools/ci/*`, `src/hive/*`, `replay-viewer/*`, `client/*`, all 16 tests,
the tests/ git history) and the CI run for the head sha before opening `r1-review.md`, and
`r1-review.md` before `r1-fixes.md`.

CI evidence used throughout: run **32624269486**, workflow `CI`, branch `main`,
`headSha 34b3dc9e…`, conclusion **success**; jobs `test` ✓ (incl. step `Marcher parameter grid` ✓),
`docker-smoke` ✓, `wasm-viewer` ✓ (incl. step `Load the bundle in a real browser` ✓). Full log
pulled and grepped locally.

## Standing blocking findings

None. All three of the review's blocking findings were true at the review's sha (`48465f3`) and
are fixed at the current head; my own checklist pass found nothing new that falsifies a numbered
item.

## Refuted (all as *fixed at head* — the review was written against `48465f3`)

### B1 / F1 — browser viewer smoke absent → REFUTED (fixed by `9306b9c`, `f3d913e`)
- Evidence: `.github/workflows/ci.yml:220` — `needs: docker-smoke`; `:249-254` asserts
  `tools/ci/viewer_smoke.mjs` present (it exists, mode 100755, 451 lines); `:316-330` step
  `Load the bundle in a real browser` runs `node tools/ci/viewer_smoke.mjs --bundle
  dist/static-replay-viewer --replay dist/smoke/replay.json --timeout 90`; `docker-smoke`
  uploads the smoke replay (`ci.yml:200-206`) that `tools/ci/docker_smoke.sh:304-315` preserves
  (`SMOKE_REPLAY_OUT`). No `continue-on-error` anywhere in any workflow (grep: zero hits).
- Run 32624269486, step `Load the bundle in a real browser`, conclusion success, log line:
  `{"loaded":true,"ms":5204,"clock":"0:39 TURN 0/4","scorebug":"P1 FOOD 0 Lime P3 FOOD 0
  Magenta 0:39 TURN 0/4 P2 FOOD 0 Amber P4 FOOD 0 Teal","feed_lines":0}` plus three distinct
  scrub readouts ending `FINAL GAME OVER`.

### B2 / F2 — `data-replay-loaded='1'` set before first paint → REFUTED (fixed by `2ada874`)
- Evidence: `replay-viewer/static_replay.js:162-166` — inside a double `requestAnimationFrame`
  after `HiveChrome.attach` resolves: `document.documentElement.setAttribute("data-replay-loaded",
  "true"); tell("ready");`. The chrome page no longer sets it
  (`client/replay_broadcast.html:2286` is now a comment saying exactly that; grep for
  `setAttribute('data-replay-loaded'` in the page: zero hits). `data-replay-error` is set from
  the same shell (`static_replay.js:44`). `tests/test_viewer.nim:102-111` pins the literal
  `"true"`, the shell as the source, and the page's abstinence. The harness's `loaded:true`
  (above) is the executable proof.

### B3 / F3 — recall does not use the carrying kernel → REFUTED (fixed by `c22f318`, `9dd4c47`)
- Evidence: `src/hive/ants.nim:77` — `moveAnt(... recalled = false)`; `:83-87` ORs `recalled`
  into the carrying branch. `src/hive/sim.nim:395` computes `recalled`, `:475` passes it into
  `moveAnt`, `:479-480` skips release for recalled ants, `:396` holds recalled ants in the pad.
  `GameVersion` bumped `"1"→"2"` with the `GV2 (recall walks home): …` changelog line
  (`src/hive/types.nim:13,22`) and both fixtures re-recorded in the same commit, per `AGENTS.md`.
  New tests `recallUsesTheCarryingKernel` and `recallGathersTheColony` in `tests/test_ants.nim`
  assert both the kernel choice and the muster; green in run 32624269486.

### Non-blocking review findings — audit of what changed since
F4 (stale turn clock), F5 (contact count), F6 (orbit cap), F7 (raid rule), F9 (`focus_weight`
repair), F12 (outer per-turn deadline), F14 (Bedrock 403 ladder), F16 (budget-guard test),
F17 (per-seat done deadline), F18/F19 (player default + bounded receive), F21 gap
(`fallback.detail` multi-byte test), F27 (three test gaps), F28 (grid harness) are all fixed at
head — verified individually, see the audit table. The fixer's refutations of F8, F10, F13, F15,
F20, F22, F24, F26, F30 are correct on my own reading (details in the table); none of them names
a checklist item that the head falsifies. On F26 specifically: checklist item 3's "no
`/client/replay` pod path" is about the platform viewer — the manifest declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and `coworld-release.yml:198-201`
hard-fails certification if the viewer is pod-served; the server route is the starter's own
local-viewing convenience (`/workspace/starters/coworld-ctf/src/ctf/server.nim` has the same
route) and the design note pins it.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green | PASS | run 32624269486, conclusion `success`, headSha `34b3dc9e…`, branch main; all 16 `tests/*.nim` ran twice (debug + `-d:release`), verified in the log. |
| 1 no test loosened | PASS | `git -C /workspace/scratch/cogame-hive-repo log -p -- tests/` read hunk by hunk: every deletion audited — `9dd4c47` replaced a physically-impossible fixture with a *harder* one (muster 34 cells out on a real trail vs 8), `2c893f2` replaced a weak `spawned mod 4` assertion with a per-opportunity cap walk plus a new `aPartlyEatenOrbitHoldsItsSlot` block, `9cb586e`/`f9f64a2`/`118f8af` are additive, `c22f318` re-recorded the golden fixtures alongside the GV1→GV2 rules fix as `AGENTS.md` mandates. No skip/xfail/tolerance-widening anywhere. |
| 2 replay re-derivation | PASS | `tests/test_replay.nim:129-148` re-derives from `seed`+`field`+`seat_nests`+`doctrines` and asserts **every** keyframe digest and **every** byte of `ants_b64`; the viewer is the same re-derivation (`replay-viewer/hive_replay.nim:9-12,49-66` re-runs the sim; `checkDigest` latches `hive_mismatch_tick`); node smoke in CI: `wasm replay smoke OK: 960 ticks, 961 frames, packet 113204B, no digest mismatch`. |
| 3 static viewer | PASS | `coworld_manifest_template.json:14-16` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755, safety checks intact; the shell's only network contact is the `?replay=` URL with a 20 s `AbortController` (`replay-viewer/static_replay.js:86,15`); no pod viewer path in the manifest and `coworld-release.yml:198-201` rejects one at certify time. |
| 4 both name spaces | PASS | `tests/test_view.nim:167-206` runs a whole episode and asserts no `results.names` string reaches any view, event body or prompt; aliases come from nests (`data/meadow.fieldspec.json`), seat→nest permutation is seed-drawn (`src/hive/sim.nim:110-112`); real names appear in the viewer scorebug — the browser smoke's scorebug string carries both `P1…P4` and `Amber/Teal/Lime/Magenta`. |
| 5 degrade-never-hang | PASS | connect wait ≤ `playerConnectTimeoutSeconds` polled at 200 ms (`src/hive/server.nim:201-209`); LLM: 14 s + one 6 s retry (`src/hive/llm.nim:29-30`) inside an outer per-turn deadline clamped to `turnBudgetSeconds` (`llm.nim:309-320`); budget guard settles the match on the scripted layer (`server.nim:256-262`, tested via the no-show fixture); `wallBudget = min(660, 0.6·1200) = 660 s < 720 s` (`server.nim:234-236`); done-broadcast 3 s per seat, hard cap seats×3 (`server.nim:331-344`); shutdown grace 20 s then `quit(0)` (`:376-380`); player receive loop 5 s poll inside a 1500 s lifetime (`src/hive_player.nim:29-37,86-92`); `runEpisode` terminates on tick count / probe / invariants (`src/hive/rules.nim:110-133`). No unbounded loop or blocking read found. |
| 6 `num_agents` | PASS | `num_agents: 4` in `variants[default]` (:459), `variants[sprint]` (:491) and `certification.game_config` (:535); `certification.players` and `…game_config.players` both length 4; `tools/ci/docker_smoke.sh:93-151` enforces all four invariants with `SEAT-COUNT FAIL:` prefixes plus the independent `SMOKE_SEATS=4` cross-check (design note pins 4); grep of the **entire** run-32624269486 log for `SEAT-COUNT` = 0 hits; `smoke OK: seats=4 results=1096B replay=51871B reason=complete`. |
| 7 scripted baseline | PASS | `tests/test_baselines.nim:130-147` plays a full marcher/driftling match, asserts `$match.reason == "complete"` and the ordering; `:41-81` asserts 500 hostile views × both baselines emit schema-legal doctrines with in-range compiled coefficients; grid harness `tools/tune_marcher.nim` runs in CI (step `Marcher parameter grid` ✓) — shipped `scouts 15 / trail_gain 78` ranked 1 of 9, gap 0.0000; `tests/test_baselines.nim:149-183` pins harness↔shipped-params identity. |
| 8 LLM reply handling | PASS | brace-scanning tolerant parse surviving fences/prose (`src/hive/doctrine.nim:66-96`), numeric strings, `"70%"`, `focus` as object (`:98-160`); exactly one retry with the invalid-reply hint (`src/hive/llm.nim:311,324-328`); fallback to marcher recorded as a `fallback` event with `cause`/`attempt`/200-rune `detail` (`src/hive/server.nim:280-285`); covered by `tests/test_doctrine.nim` and `tests/test_engine.nim`. |
| 9 rune-safe truncation | PASS | `truncateRunes` uses `runeLen`/`runeSubStr` (`src/hive/doctrine.nim:20-25`); caps: note 140/say 32 (`:199-200`), policy 48 (`src/hive/roster.nim:8-12`), detail 200 (`llm.nim:355`, `server.nim:285`), prompt 4000 (`roster.nim:60-62`, `llm.nim:192-193`); `tests/test_doctrine.nim:104-140` feeds 4-byte emoji at the say cap **and** the detail cap and asserts `validateUtf8 == -1` plus JSON round-trip; `tests/test_replay.nim` forces a non-ASCII `say` through a real episode and validates the replay bytes as UTF-8 first. |
| 10 manifest validates | PASS | `game.docs.readme = {"type":"text","value":…}` (:401-404) and `pages = [rules.md, protocol.md]` each with `content:{"type":"text","value":…}` (:405-422), all non-empty; `game.protocols` carries both `player` (:391) and `global` (:395); `tests/test_manifest.nim` asserts all of it. |
| 11 legible at 360 px | PASS | `client/replay_broadcast.html:1486-1489` — `.plate .team-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; … }` (declared after the inherited rule so it wins; the checklist's `.plate-name` shorthand names this rule — the design note pins the selector as `.plate .team-name`); `@media (max-width: 640px)` at `:1600-1612` hides `.lives-label`, `#doctrinebar`, `#viewpanel`, shrinks `#nestbug` to dot+numeral; `tests/test_viewer.nim:58-81` asserts both. |
| 12 release order & scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (:153) → Certify locally (:167, in-run build) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342), in one job so order is sequential; all three workflows present; `docker-smoke` builds the image immediately before the smoke in the same job (`ci.yml:184-193`); `tools/ci/docker_smoke.sh` mode 100755; `tools/ci/policies.json`: 4 policies — 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 (`hive-swarmraid`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (:15); placeholder gate re-run by me at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files exits 1 (no matches). |
| 13 viewer executes | PASS | (i) run 32624269486 `wasm-viewer` green **including** `Load the bundle in a real browser` (step conclusion `success`, `loaded:true`, three advancing clock readouts); `needs: docker-smoke` at `ci.yml:220`; no `continue-on-error` in any workflow. (ii) `static_replay.js:164` sets `data-replay-loaded="true"` on `<html>` after the first drawn frame (double rAF post-attach); `:44` sets `data-replay-error` on failure — both from the shell. (iii) `replay-viewer/config.nims:47-48` links `-s MODULARIZE=1 -s EXPORT_NAME=HiveReplayModule` and the shell calls the factory `HiveReplayModule()` (`static_replay.js:184`) — never `Module.onRuntimeInitialized` (zero grep hits); flags and bootstrap agree, and the smoke's `loaded: true` is the executable evidence. |
| simultaneous batch | PASS | all open LLM seats per turn go out as one `client.curl.makeRequests(batch, timeout)` call (`src/hive/llm.nim:159-163,321-335`); scripted seats need no HTTP call, which is what the rule's "all seats' **LLM calls**" means; `tests/test_engine.nim` asserts exactly one batch call per turn with all four in-flight windows intersecting when all four seats are LLM seats. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1/F1 | fixed (`9306b9c`,`f3d913e`) | `ci.yml:220,249-254,316-330`; viewer_smoke.mjs present 100755; step ran, `loaded:true` | yes |
| B2/F2 | fixed (`2ada874`) | `static_replay.js:162-166` sets `"true"` post-paint; page abstains; test pins it | yes |
| B3/F3 | fixed (`c22f318`,`9dd4c47`) | `ants.nim:77,83-87`, `sim.nim:395,475,479`; GV2 + changelog + fixture re-record; new tests | yes |
| F4 | fixed (`e44dfc1`) | `sim.nim:219-236` `beginTurn` (idempotent via `turnRolled`), called from `rules.nim` before `provide`; `sensed`/contacts still cleared in `installDoctrines` | yes |
| F5 | fixed/refuted-cadence | `sim.nim:63-67` `contactAnts` per-ant flags, cleared per turn (`:249-250`); cadence claim correct — deterministic, no PCG draw, not in the digest | yes |
| F6 | fixed (`2c893f2`) | `sources.nim:97-112` counts distinct live spawn ticks; tests walk the real loop + the partly-eaten case | yes |
| F7 | fixed (`c78094d`) | `sources.nim:166` `exclude` param; `sim.nim:448-454` excludes the delivering colony; honest no-op-on-shipped-meadow note is geometrically correct (nests ≥ 63 cells apart vs radius 20) | yes |
| F8 | refuted | snapshot pre-step at turn boundary is what `rewindTo` needs; determinism test asserts restoration; no checklist item touched | yes |
| F9 | fixed (`c676e0f`) | `doctrine.nim:196` `readPercent(node{"focus_weight"}, base.focusWeight)` | yes |
| F10 | refuted | nest order matches the note's own worked example; fixed alias-only order holds; protocol text says "in nest order" | yes |
| F12 | fixed (`1cb0bdf`) | `llm.nim:31-35,88-91,309-320` outer deadline, attempts clamped, expired seats → marcher with cause `timeout` | yes |
| F13 | refuted | checklist's rule is about LLM calls; one `makeRequests` batch per attempt, never sequential | yes |
| F14 | fixed (`aa76ed6`+2) | `llm.nim:131-148,230-242` any 401/403 walks the ladder; `failedModel` snapshot makes one batch one verdict; disabled only when the ladder is exhausted | yes |
| F16 | fixed (`f9f64a2`) | no-show fixture squeezes wall budget to 40 s < 2×22 s, asserts exactly one `budget_guard` event **through server.nim's own closure** and `complete/full_time` | yes |
| F17 | fixed (`1ef2a53`) | `server.nim:331-344` per-seat 3 s deadline inside a seats×3 s hard bound | yes |
| F18/F19 | fixed (`31ab9b3`) | `hive_player.nim:24-27` `DefaultScripted = "marcher"`, no invented prompt; `:29-37,86-92` 5 s poll + 1500 s lifetime, no `while true` | yes |
| F20 | refuted | second `register` closes a real upgrade/bookkeeping race; roster idempotent | yes |
| F21 | gap closed (`9cb586e`) | `tests/test_doctrine.nim:123-140` multi-byte `fallback.detail` at the 200-rune cap | yes |
| F22 | refuted | 200 keyframes for ticks 0…4776 is the correct count; the note's 201 is the off-by-one; `held` in the digest strengthens the check symmetrically | yes |
| F24 | refuted | sprint's `bonanzaTicks: [1200]` — a 3600-tick bonanza cannot fire in a 2880-tick episode | yes |
| F26 | refuted-route / fixed-splice (`949ae26`) | manifest declares the bundle; release workflow rejects pod viewers; `server.nim:124-130` now splices `hive_replay.js` + `static_replay.js` in Dockerfile order | yes |
| F27 | fixed (`9cb586e`) | scout-noise doubling asserted behaviourally; detail-cap test; no-show `declarePlayerFailure` path covered end to end; four sub-item refutations all check out (8-tick decay resolution, turn-0-inert fields, debug-vs-release perf budgets, bundle-absent early return now covered twice in `wasm-viewer`) | yes |
| F28 | fixed (`5376788`) | `tools/tune_marcher.nim` exists, drives the real baseline via `MarcherParams`/`ShippedMarcher`, runs in CI, shipped params rank 1 of 9, and `tests/test_baselines.nim:149-183` pins the identity | yes |

## Non-blocking observations

- `tools/ci/docker_smoke.sh:129,136` gate the `len(certification.players)` and
  `len(…game_config.players)` invariants behind `if cert_players:` / `if fixture_players:` — an
  *empty* list would slip past. This is the coworld-builder template verbatim (diff against
  `templates/tools/ci/docker_smoke.sh` shows only the three substitutions), and the shipped
  manifest populates both lists with 4, so all four invariants are enforced in practice.
- The review's residual "could not determine" items (real 14 s/6 s deadlines against a live
  socket, the Bedrock ladder against real endpoints, `claude-sonnet-5` as an Anthropic-direct id)
  are not checklist items; the bounds, ladder and fallback logic the checklist does name are
  verified from the tree and from CI above, and the live-LLM behaviour is phase 60's to observe.
- `docs/PROTOCOL.md` still lacks the one-clause definition of `contacts[].ants` the fixer noted;
  cosmetic.

BLOCKING: 0
