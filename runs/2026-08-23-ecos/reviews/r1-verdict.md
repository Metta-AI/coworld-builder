blocking: 2

# r1 verdict — ecos
Head: `b4bb25e9bc78755b333de26f1eada3f959f3db77` (== origin/main, confirmed after fetch+reset)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–13 + simultaneous-decision clause)
Independent read written before reading fixes: **yes** (full source, tests, viewer, manifest, workflows, CI logs read and both judge findings formed before opening `r1-fixes.md`; `r1-review.md` was read only after my own pass over the tree, per the reading order)

Design note: judged against the repo copy `docs/plans/2026-08-23-ecos-design.md`. Its divergence
from the run copy is exactly the three documented deviation notes (shipped-constants table,
cert-fixture 6×60 + `minTurnSeconds: 0` rationale, `frames.len == ticksPlayed + 1`), verified by
diff. Two further divergences exist that are documented in-tree but not in the note — see
Non-blocking observations; neither is unjustified.

---

## Standing blocking findings

### B1 — a throttled (429) seat is given an all-zero doctrine, not the recorded steward fallback   (source: judge)
- Category / location: `- [correctness] src/ecos/llm.nim:478 a 429 leaves result[index] as the default Decision — fields [0,0,0,0], source "llm" — which the server installs unclamped`
- Verified at head: `decideAll` initialises `result = newSeq[Decision](seats.len)` (llm.nim:449);
  the throttle handler only logs and neither assigns a decision nor re-opens the seat:
  ```
  except EcosThrottleError as error:
    ## Not re-opened: this seat plays the steward doctrine for this
    ## generation and gets a fresh call in the NEXT generation's batch, ...
    logLine("ecos llm: seat " & $slot & " " & error.msg & ...)
  ```
  (llm.nim:478–484). The final fallback loop `for index in open:` (llm.nim:490–494) covers only
  seats still in `stillOpen`, which a throttled seat never joins. So `result[index]` stays the
  zero-value `Decision`: `fields == [0,0,0,0]`, `source == dsLlm` (first enum value,
  events.nim:22–23), `clamped == false`. The server applies it unconditionally —
  `state.sim.applyDoctrine(species, decision.fields, …)` (server.nim:327) — and `applyDoctrine`
  does not clamp ("Out-of-range values are already clamped by the caller", sim.nim:136–137). A
  grazer seat then runs a generation with `birth_threshold 0, bite 0, flee_range 0, herd 0` (legal
  minimum is `[80, 2, 0, 0]`, sim_types.nim:119): every grazer splits every tick with no food
  income — a doctrine outside its declared range driving the sim, recorded in the replay as a
  normal `"source":"llm"` decision, so phase 60 cannot count the miss and the feed shows no `auto`
  tag. Introduced by fix commit `481cc50` (F25), whose own message and `r1-fixes.md` claim the seat
  "plays the steward doctrine … recorded `source: "fallback"`" — no code at head does that.
  `tests/test_llm.nim:90–101` only asserts `decisionFrom` raises `EcosThrottleError`; no test
  exercises `decideAll` under a 429, which is why CI is green over this.
- Checklist item: **8 — LLM reply handling** ("retries once on a parse or transport failure, then
  falls back to the scripted move — and the fallback is recorded so phase 60 can count it"). A 429
  is a transport failure; at head the fallback neither happens nor is recorded. (The design note's
  own §Degrade-never-hang — "still failing → that seat plays the steward scripted doctrine …
  recorded as `"source":"fallback"`" — is violated on the same path.)
- What settles it: in the throttle handler, assign
  `result[index] = scriptedDecision(sim, sim.roleOf[slot], skSteward)` with `source = dsFallback`
  (exactly what the final fallback loop does), plus a `decideAll`-level test with a stubbed 429.

### B2 — on a mid-generation collapse the viewer's re-derived scores omit the partial generation that `results.scores` includes   (source: judge)
- Category / location: `- [correctness] src/ecos/replays.nim:185 precompute only flushes the score accumulator when tick mod ticksPerGeneration == 0, but the sim closes and scores the partial generation a collapse interrupts`
- Verified at head: the sim, on a collapse away from a boundary, calls `closeGeneration()` anyway —
  `if collapsed: if not sim.atGenerationBoundary(): sim.closeGeneration()` (sim.nim:628–630) — and
  `closeGeneration` adds `min(genAccum/(ticksPerGeneration·R), 2.0)` to `sim.scores`
  (sim.nim:551–552), so `results.scores` carries partial credit for the interrupted generation.
  The viewer's `precompute` accumulates `accum[index] += bioRow[index+1]` for every tick but adds
  to `score` only under `if tick > 0 and tick mod perGeneration == 0` (replays.nim:185–192); a
  collapse at tick T with `T mod 60 != 0` leaves the last accumulator unflushed, so
  `scoreAt[lastTick]` < `results.scores` for all three seats by each seat's partial-generation
  term (up to 2.0, typically 0.1–0.6, and different per seat — the end-card winner
  (`broadcast.nim:126–133`, fed from `input.scores = player.scoreAt[tick]` at replays.nim:261) can
  therefore differ from `results.win`). Collapse is a designed, reachable outcome ("a collapse is
  a completed game of Ecos", note §End conditions; `test_feasibility` gate (b) guarantees it is
  reachable, and all-`opportunist` fields collapse on ≥5 of 6 seeds), so this is a shipping
  display-vs-artifact disagreement, not a corner case. The lock the checklist demands exists only
  on the path where the two happen to agree: `tests/test_replay.nim:133–158` asserts
  `scoreAt == results.scores` and end-card == results for a **full ten-generation steward
  episode**; no test covers a collapse replay's scores (test_broadcast's crash block reads
  `sim.scores` directly, not the viewer's re-derivation).
- Checklist item: **2 — Replay re-derivation** ("the viewer must derive its display from the
  recorded frames/series, and a test must lock viewer-derived scores to results"). The derivation
  disagrees with `results` on every mid-generation-collapse replay, and no test locks that path.
  This is the same defect family as the reviewer's F1 (fixed for the full-episode window by
  `e78a513`) surviving on the collapse path that F18 recorded as sim-side behaviour.
- What settles it: flush the residual accumulator at the final tick in `precompute` (score the
  partial window against the same full denominator the sim uses) — or, equivalently, add a
  boundary case for `tick == ticks-1` when the episode ended mid-generation — plus extending the
  test_replay score-lock block to a collapse episode (the greedy-predator picker in
  `test_broadcast.nim:148–156` already constructs one deterministically).

---

## Refuted

**None.** Every one of the reviewer's 28 findings reproduced at the reviewed sha `289937c` (I
spot-verified the mechanism of F1, F2, F4, F7, F11, F13, F14, F15, F16, F17, F19, F24, F25, F26
against the fix diffs and pre-fix code, and F5/F6/F9/F21/F22/F27/F28 against the current tree,
manifest, template files and CI artifacts). Nothing was wrong or overstated; the review's own
blocking count of 0 was correct at its sha under its (reasonable) reading of item 2. 21 findings
are since **fixed** (not refuted) by commits `e78a513`…`b4bb25e` — each fix verified real at head;
none weakens a test. The one test deletion in the round (`1d5eb84`, F15, removes
`doAssert not event.clamped` from test_baseline) removed an assertion that was both vacuous (the
flag was hard-coded `false` by the test itself) and counterfactual, and replaced it with two
strictly stronger true assertions (`stewardClamps > 0`, event-level range checks retained) — a
strengthening, not a loosening. The seven advisory-no-change dispositions (F12, F18, F21, F22,
F23, F27, F28) are correctly advisory: none maps to a checklist item — except that F18's sim-side
behaviour combines with the F1 fix to produce B2 above, which is where that thread lands at head.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | run **32639042839** on `b4bb25e`, conclusion `success`; jobs test/docker-smoke/wasm-viewer all ✓, no `continue-on-error` in ci.yml (grep = 0), all 7 test files ran debug+release unfiltered (log lines 2329–2386, 14 `ok`s). `git log -p --since=2026-08-23T08:41Z -- tests/`: every hunk adds assertions except F15's replacement (see Refuted §) — nothing deleted, widened, skipped or xfailed. |
| 2 Replay re-derivation | **FAIL — B2** | Frames round-trip by value (`test_replay.nim:101–121`), frames↔series consistency asserted, viewer loop runs natively for 120 frames with seeks (`:164–187`), scores locked to results on the complete path (`:133–158`) — but the lock is false on the collapse path (replays.nim:185–192 vs sim.nim:628–630). |
| 3 Static viewer | pass | manifest:16–18 `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` 0755, wired at ci.yml:249 behind a `test -x` gate; worker fetches only the replay URL (static_replay_worker.js:113–120); `src/ecos.nim:30–36` exits 0 on replay mode; the only `/client/replay` strings are the verbatim starter's URL helper and comments, never a served route (server.nim:478–487). |
| 4 Both name spaces | pass | Aliases only to seats: `observationJson` (sim.nim:756–782), prompts read `sim.names` only (llm.nim:174–283); replay carries `names[]` + `policyNames[]` (replays.nim:61–69); chrome headlines the policy name (broadcast.nim:47–64 `policies:[…]`, chrome_common.js:145 `teamName`); results.names = policy names (sim.nim:806). Asserted under all rotations (test_broadcast.nim:56–89). Offline fixtures alias-name the policies (reviewer F28) — mechanism still present and correct. |
| 5 Degrade-never-hang | pass | connect wait bounded 180 s (server.nim:235–241); one batch + one retry, 25 s per request via `makeRequests(batch, timeoutSeconds)` (llm.nim:461–466); deadline checked between generations **with a `2·llmTimeout+minTurn` reserve** (server.nim:278–299, F26 fix verified); artifact writes on 60 s-bounded curly paths; shutdown 0.5 s + 20 s grace + `quit(0)`; player loop try/except → exit 0 (ecos_player.nim:53–90). Worst case ≈ 180 + 10·56 s < settle inside 720 of 1200. B1 corrupts a decision on this path but nothing hangs. |
| 6 num_agents | pass | `num_agents: 3` in `standard` (manifest:416), `harsh-spring` (:446), certification (:475); test_manifest.nim:49–66 asserts all three + players.len; docker_smoke.sh:110–151 carries the four `SEAT-COUNT FAIL` invariants before any container starts, `SMOKE_SEATS=3` cross-declared (ci.yml:7, script:54); `grep -c "SEAT-COUNT FAIL"` over the full run-32639042839 log = **0**; smoke printed `seats=3 … "num_agents": 3`. |
| 7 Scripted baseline full episodes, legal | pass | `test_replay.nim:18` plays all-steward to natural end, asserts `ending == "ten_generations"` (:76–78; `finish("complete","ten_generations")` is that string's only writer, sim.nim:638); test_baseline: 12 seeds × 2 baselines, per-tick invariants + every emitted and every recorded doctrine in range (:15–72); test_feasibility gate (a): 12/12 seeds, both variants, close-row **and** per-generation-mean population bounds (:97–114). Tuning provenance: no search harness committed, but the shipped constants are enforced by the in-tree oracle and the note's F3 table records the reproducible counter-measurements (killBase 60 → 11/12; note defaults → 0/12) — verified as the strongest tree-available evidence; harness absence noted below, not counted. |
| 8 LLM reply handling | **FAIL — B1** | Tolerant parse, retry-once with hint, fallback recorded `dsFallback` — all present and tested (llm.nim:286–297, 461–494; test_llm.nim:30–164) and observed in the CI replay (seat 0 `source:"fallback"`) — but the 429 path installs an unclamped zero doctrine recorded as `"llm"` (llm.nim:478–484). |
| 9 Rune-safe truncation | pass | `cleanText` runeSubStr (llm.nim:118–131); prompt rune-truncated (server.nim:448–449); test_replay.nim:192–238 feeds 2-byte and 4-byte runes exactly at both caps and one over, asserts valid UTF-8, rune counts, `…` marker, and survival into the replay bytes. Captured LLM error byte-slices go to the log only, never the replay. |
| 10 Manifest validates | pass | `game.docs` exact shape with readme + 2 pages (manifest:306–329); `game.protocols.player` and `.global` both `{"type":"text",…}` (:296–304); asserted with length floors (test_manifest.nim:129–141). |
| 11 Viewer legible at 360 px | pass | `.plate .plate-name { … flex: 1 1 auto; min-width: 3.2em; }` (replay_broadcast.html:890–903); `@media (max-width: 640px)` hides `.lives-label`, `.plate-sub`, `.momentum-label` (:922–927); `#stage.tiny` shrink (:928–929). Smoke scorebug rendered one legible line. |
| 12 Release order and scaffold | pass | coworld-release.yml step order build(:153)→certify(:167)→upload-policies(:206, explicitly "BEFORE upload-coworld")→upload-coworld(:304)→secret put(:342, "AFTER"); all three workflows present; docker_smoke.sh executable; policies.json: 4 policies, 2 `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 (`ecos-bloom`, second PLAYER_PROMPT) carries `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (policies.json:15); the three-name placeholder grep over the five files finds nothing (exit 1 = no match); the four declared angle-bracket survivors are where the checklist says. test_manifest.nim:202–219 pins the policy shape. |
| 13 Viewer executes | pass | Run **32639042839** `wasm-viewer` green with `needs: docker-smoke` (ci.yml:212); "Load the bundle in a real browser" ran (step conclusion success, no continue-on-error) and printed `{"loaded":true,"ms":391,…}`, `soak: 10s of playback kept advancing ("0 / 360" -> "193 / 360" -> "241 / 360")`, three distinct scrub readouts (`GEN 5/6 TICK 241`, `GEN 4/6 TICK 196`, `GEN 6/6 6 GENERATIONS`); `data-replay-loaded` set on the worker's `loaded` after the first ingested packet (static_replay.js:139–142, static_replay_worker.js:122–128), `data-replay-error` in `showFailure` (static_replay.js:8–19); config.nims has no MODULARIZE/EXPORT_NAME (config.nims:42–54) and the worker bootstraps `Module.onRuntimeInitialized` + `importScripts('./ecos_replay.js')` (worker:162, :210) — the matched non-MODULARIZE pair, from one starter. |
| Simultaneous batch | pass | One `RequestBatch` per generation for all open seats via `curly.makeRequests` (llm.nim:402–421, 461–466); `test_llm.nim:116–137` asserts `batch.len == openSeats`. No sequential per-seat calls anywhere. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed `e78a513` | sim window now excludes frame 0 (sim.nim:528–530); score-lock + end-card test added (test_replay.nim:133–158) | yes |
| F2 | fixed `07d3c42` | prompt composed from `$KillCap`/`$KillBase` (llm.nim:170); asserted (test_llm.nim:169–173) | yes |
| F3/F5/F10 | fixed (docs) | all three deviation notes present in repo note copy; diff against run copy shows exactly those blocks | yes |
| F4 | fixed `3baac0e` | `checkAlarms` stamps `sim.tick` post-increment (sim.nim:487–499); monotonic-`t` asserted in test_replay (:52–58) and test_broadcast on a real crash (:160–186) | yes |
| F6 | fixed `cbfc377` | manifest↔`harshSpringConfig` field-by-field lock (test_manifest.nim:159–179) | yes |
| F7 | fixed `91dc55e` | `variant` schema property with enum (manifest:198–206), harsh-spring sets it (:457), asserted + update→configJson round-trip (test_manifest.nim:185–200) | yes |
| F8 | fixed `b4bb25e` | chip/caption read `gens` (replay_broadcast.html:2334, 3675–3688); smoke now prints `GEN 6 / 6 6 GENERATIONS` | yes |
| F9 | fixed (part) `9f316b4` | per-generation-mean bounds asserted (test_feasibility.nim:59–76, 109–114); the all-opportunist clause left for the judge — I rule it advisory (no checklist item; certification seats one opportunist and ends `ten_generations`) | yes |
| F11 | fixed `481879c` | disconnected slots marked `skSteward` in the per-generation snapshot (server.nim:307–309) | yes |
| F13 | fixed `86ff481` | `rulesJson` per-species (sim.nim:701–741); asserted incl. negative keys (test_sim.nim:269–288) | yes |
| F14 | fixed `25d1ace` | header `births g,h,p | starved g,h,p | eaten | scores g,h,p`, dead lines gone (llm.nim:205–224) | yes |
| F15 | fixed `1d5eb84` | flag threaded through `scriptedDoctrineChecked`/`scriptedDecision`; replacement assertions strictly stronger | yes |
| F16 | fixed `298ed99` | value-by-value frame round trip + frame↔series equality (test_replay.nim:101–121) | yes |
| F17 | fixed `5e508cc` | `biomassSum` gated on `tick > 0`; equality with series mean asserted (test_replay.nim:83–91) | yes |
| F19 | fixed `6c3f738` | hairline as spaced dimmed sparkles (global.nim), collapse/end feed rows (replay_broadcast.html) | yes |
| F20 | fixed `11cbcbc` | `trackers`/`shuttingDown`/`says` absent from head | yes |
| F24 | fixed `3fa2c1e` | live path sends no `lead`; `recordMomentum` accumulates from `teams[*].lives` per frame (chrome_common.js:661–676, broadcast.nim:63) | yes |
| **F25** | fixed `481cc50` — "seat plays the steward doctrine … recorded `source: "fallback"`" | **the claim is false at head**: the throttle handler assigns nothing; the seat gets the zero-value Decision and the sim runs an out-of-range doctrine recorded as `"llm"` — see **B1** | **no** |
| F26 | fixed `b413a4c` | `generationReserve = 2·llmTimeout + minTurn` held back at the between-generations check (server.nim:278–299) | yes |
| F12/F18/F21/F22/F23/F27/F28 | advisory, no change | all verified still-advisory at head; F18's sim behaviour is by-design but its viewer-side consequence is **B2** | yes (with the B2 caveat) |

## Non-blocking observations

- **Design-note divergences beyond the three documented notes, both justified in-tree but absent
  from the note:** (a) `test_feasibility.nim`'s gate (b) replaces the note's greedy-grazer
  collapse count with measured strip+score assertions plus a new all-`opportunist` collapse gate —
  documented in the test's own header (:20–27), and the new gate factually contradicts the note's
  conclusion (a) claim about "every all-filler league episode"; (b) F7 added the `variant`
  config-schema property the note's §Packaging list does not name (the note's replay schema
  requires it). Recommend both be folded into the note next docs commit.
- `docker_smoke.sh` does not inspect player-container exit codes or validate against
  `game.results_schema`, contra note §Tests item 8 — it is the builder's verbatim template; the
  note over-describes it (reviewer F21; a ruling, not code, settles it).
- No committed grid-search harness for the baseline constants (note claims a 240-config search);
  the in-tree feasibility oracle plus the F3 measurement table is the standing evidence.
- `chromeFrame` clamps the displayed generation number to `config.generations` on post-collapse
  frames (fixer's NOTED list) — cosmetic.
- Live-path population strip is normalised differently (raw lives vs the replay's per-cap
  permille) — cosmetic, live path only.

**Verdict: 2 blocking findings stand at `b4bb25e`, both judge-sourced, both introduced or exposed
during the fix round (B1 by the F25 fix; B2 by the F1 fix's score-lock landing only on the
complete-episode path). The reviewer's 28 findings: 21 fixed and verified, 7 correctly advisory,
0 refuted.**

- [correctness] src/ecos/llm.nim:478 throttled (429) seat gets an unclamped all-zero doctrine recorded as source "llm" instead of the recorded steward fallback (item 8)
- [correctness] src/ecos/replays.nim:185 viewer score re-derivation omits the partial generation a mid-generation collapse scores, so end-card/scorebug diverge from results.scores/win on every collapse replay, and no test locks that path (item 2)

BLOCKING: 2
