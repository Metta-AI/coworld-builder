blocking: 0

# r1 verdict — contagion

Head: `66e0821721a72390bf4ce9e7a6ae2520dc8ce023` (main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: yes (repo cloned fresh at 66e0821; design note,
sim/server/llm/types, viewer files, workflows, manifest, tests and both CI runs read and my own
notes formed before opening `r1-review.md` or `r1-fixes.md`).

Review round context: the review was written against `7cba8a0`; fixes landed as 8 commits ending
at `66e0821` (this head). Verification below is at the head, so findings that were true at
`7cba8a0` and are gone now are **resolved**, not standing.

---

## Standing blocking findings

None.

---

## Refuted / resolved (the reviewer's findings, one by one)

### B1 — retry-exhausted LLM fallback recorded as `scripted: false` → RESOLVED at head (was real at 7cba8a0)
- Evidence the finding was real: `git show 7cba8a0:src/contagion/llm.nim` returned only
  `seq[Decision]`, and the server derived the flag from the registration.
- Evidence it is fixed at 66e0821: `src/contagion/llm.nim:615-692` — `decideAll` returns
  `tuple[decisions: seq[Decision], scripted: seq[bool]]` and sets `result.scripted[index] = true`
  in both scripted branches, including the retry-exhausted fallback (`llm.nim:688-692`:
  `result.decisions[index] = scriptedDecision(sim, seat, skSentinel); result.scripted[index] = true`).
  `src/contagion/server.nim:316` takes `let wasScripted = batch.scripted[index]` straight from the
  batch and passes it to `applyDecision` (`server.nim:327`), which stamps `event.scripted`
  (`sim.nim:528`) → `eventToJson`'s `"scripted"` (`sim.nim:961`).
- Test: `tests/test_bot.nim:282-310` drives a real curly batch at `http://127.0.0.1:1`
  (`client.disabled` asserted false), burns both attempts, and asserts `event.scripted` and
  `eventToJson()["scripted"].getBool()` on all six dial events. Ran green in run 32637561078
  (job 97189491940), debug and release.

### N1 — `/client/replay` route + doc mentions vs item 3's "no pod path anywhere" → REFUTED (not a violation)
- `coworld_manifest_template.json` declares `"replay_viewer": {"bundle": "static-replay-viewer"}`;
  nothing anywhere declares a pod-served viewer to the platform. The route at
  `src/contagion/server.nim:502` (`result.get("/client/replay", htmlHandler("replay.html"))`) is a
  replay-mode debug page inside the game container, inherited byte-for-byte in role from the
  starter (`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:470` has the identical
  line) whose own manifest also declares the static bundle — so the literal reading would condemn
  the canonical starter too. The release workflow's certify gate enforces the substantive rule
  (`coworld-release.yml:196-201`: the static-bundle liveness marker must appear; "a pod-served
  /client/replay viewer is not acceptable"), and `test_manifest.nim:20-25` asserts
  `"client/replay" notin manifest["game"]["replay_viewer"]`. Item 3's clause targets the platform's
  replay-viewer declaration, which is clean. Not blocking.

### N2 — unconnected seat played as LLM, not sentinel → RESOLVED at head
- `src/contagion/server.nim:214-225` adds `pinUnconnectedSeats` (still-`skNone`, still-unconnected
  seats → `skSentinel`), called under the lock at game start (`server.nim:246`). Test
  `tests/test_bot.nim:345-358` covers the mixed and zero-sockets cases. Matches design.md:320-324.

### N3 — cert fixture seats `contagion-player` at slot 0 → REFUTED as a blocker
- No checklist item requires an all-scripted certification fixture. Item 6's requirements hold:
  `certification.game_config.num_agents == 6`, six `certification.players`, six
  `game_config.players` (verified by parsing the manifest and by `docker_smoke.sh`'s four
  pre-launch invariants). The fixer's rationale (certify's declared==seated check;
  `test_manifest.nim:107-124`) is coherent, and the fixture demonstrably completes:
  docker-smoke at head printed `smoke OK: seats=6 ... reason=complete`. A design-note deviation,
  not a checklist falsification.

### N4 — chrome.css exceeds "two additions and nothing else" → REFUTED as a blocker
- Item 11 is what the checklist names, and it holds at head (see checklist pass below).
  The extra hunks are six-plate scorebug geometry; `.plate-name` is untouched.

### N5 — calibration numbers differ from the note's table → REFUTED as a blocker
- The reviewer's own re-derivation showed the code self-consistent and the note's death arithmetic
  wrong (≈1M × 0.35/week at the 3.2 % IFR ceiling ≈ 30 k deaths, not 21 k, while the note's GDP
  figure matches the code). The load-bearing claims — ordering and signs — are asserted
  (`test_bot.nim:91-120`). No checklist item pins the note's illustrative table.

### N6 — fourth `curves` series `confirmed` → REFUTED as a blocker
- Additive, revealed only up to the current week (`sim.nim:726-740` iterates `sim.history`), and
  it is the data §Viewer 7's dotted reported-curve explicitly needs. No item touched.

### N7 — `edges[].flow` semantics → REFUTED as a blocker
- Viewer-only value, reset weekly (`sim.nim:359-360`), not part of `RegionState` or the `week`
  event, hence outside `replayMatch`'s field-for-field check — it cannot desynchronise a replay.
  The note's "`Σ imp` in people" is ambiguous; the code's reading yields the stated unit.

### N8 — in-lock rejection fallback read a partially latched sim → RESOLVED at head
- `src/contagion/server.nim:331-337`: the fallback is now `scriptedDecision(simCopy, seat,
  skSentinel)` — the pre-batch snapshot. `tests/support/helpers.nim:41-48` (`playScripted`) takes
  one snapshot per week before any decision latches. Real defect (a fallback could read a
  neighbour's week-w testing), correctly fixed.

### N9 — byte slices on captured HTTP error bodies → RESOLVED at head
- `src/contagion/llm.nim:472,481-482,486,495`: all four diagnostic heads now go through
  `cleanText` (rune-boundary trim). The reviewer was right that none reached the replay
  (`eventToJson` emits only `say`, `text` and numbers), so this was never an item-9 falsification;
  it is now moot either way.

### N10 — one feed line mixed the two name spaces → RESOLVED (name-space half) at head; wording half refuted
- `client/renderer.js:841` and `:889` now route the recipient/road names through `nameMap.text`,
  so a spectator feed line is wholly in display names (verified in the file and in commit
  `2ad39e2`). The wording deltas ("reply corrected to a legal move", " (scripted)") are accurate
  generalisations of the note's illustrative strings; no checklist item pins the copy.

### N11 — `weeks < 4` raised at config load → RESOLVED at head
- `types.nim:150-153`: the raise is gone; `sampleEpisode` (`sim.nim:185`) clamps both bounds and
  runs before `initSim` (`contagion.nim:41`). Test `test_sim.nim:75-88` asserts 2→4, 400→40,
  12→12. Unreachable from the platform anyway (schema pins weeks 4..40).

### N12 — `makeRequests` outside the per-seat try → REFUTED with source evidence
- I fetched curly at the lockfile pin (`nimby.lock:11` — 1.1.1 @ `a0f42baa`):
  `proc makeRequests*(curl: Curly, batch: RequestBatch, timeout = 60): ResponseBatch
  {.raises: [], gcsafe.}` — compiler-enforced non-raising; transport failures land in
  `responses[i].error`, which `llm.nim:676-677` handles inside the per-seat try. The timeout
  funnels into `easy_setopt(OPT_TIMEOUT, request.timeout)` — libcurl whole seconds, so the
  budget arithmetic is in the right unit. The escape-the-thread scenario is unreachable.

### CND-1 (reviewer's "could not determine" #1) — grid harness → RESOLVED at head
- `tests/test_sweep.nim` (146 lines) sweeps both threshold families over a ×0.25..×4 grid, five
  seeds a cell, and asserts the shipped constants are the argmax, unbeaten, and interior. The
  shipped cuts (`llm.nim:152-163`) are the sweep's output, not the note's numbers. CI at head
  printed `best cell own x1000000 road x1000000 score 11206 | shipped score 11206 | cells that
  beat it 0/24` in both the debug and release passes (job 97189491940).

### CND-4 (reviewer's #4) — first-batch timeout unclamped under non-default config → RESOLVED at head
- `llm.nim:656-661`: first attempt is `max(5, min(llmTimeoutSeconds, budgetSeconds))`; under
  defaults (25/35) unchanged. Test `test_bot.nim:312-343` uses an accept-and-never-answer socket
  with `llmTimeoutSeconds=60` against a 5 s budget and bounds the whole batch.

### CND-2 / CND-3 — settled by dependency source
- CND-2: settled above (N12). CND-3: `bitworld` is pinned (`nimby.lock:1` @ `9af28b41`); the
  fixer's citation (CurlPool get/put, `timeout: float32 = 60` → `OPT_TIMEOUT`) is consistent with
  the curly source I read (the `CurlPool`/`makeRequest(PCurl, ..., timeout: float32 = 60)`
  overloads exist verbatim at the pinned curly commit). I could not read bitworld's own two procs
  from this sandbox, but item 5's own explicit bounds (connect 180 s, batch ≤ week budget, retry
  ≤ 10 s, deadline 720 s, artifact POST 60 s) are all verified in-tree, and the residual is a
  bounded 60 s libcurl default on the artifact/secret paths — after play, before the 1200 s kill.
  Not a falsification of item 5.

---

## Checklist pass (independent)

| # | item | status | evidence |
|---|---|---|---|
| 1 | CI green, no test loosened | **pass** | Run **32637561078**, `ci.yml` on `main`, `headSha 66e0821…`, conclusion **success** (jobs: test 97189491940, docker-smoke 97189492117, wasm-viewer 97189615823). `git log -p -- tests/` for the whole run (first commit 2026-08-23): 7cba8a0 adds 5 files; the 6 fix commits only add tests/strengthen assertions. The only removed lines are `check batch.decisions[index] == scriptedDecision(sim,…)` → replaced by the same equality against the pre-batch snapshot **plus** a new `check batch.scripted[index]` (37af17e, 4d3d6f0) — the snapshot is the reference `decideAll` actually computes from, so this corrects the reference, it does not widen it. No skip/xfail/tolerance anywhere in `tests/` (grepped). All five `tests/*.nim` ran twice (debug + `-d:release`) in the test job log. |
| 2 | Replay re-derivation, frame by frame, viewer uses it | **pass** | `sim.nim:898-927` `replayMatch`: seed re-draws permutation/outbreak/variantWeek, every `dial` replayed through `applyDecision`, every `week` event checked field-for-field (`sameRegions`, `sim.nim:890-896`; raises on mismatch). Tests: `test_sim.nim:531-556` (frames.len == events.len+1, final frame byte-equal to live `tableStateJson`, also via JSON round-trip), `:568-580` (tampered week raises), `test_replay.nim:104-125` (wasm module's path). Viewer: `contagion_replay.nim:37-39` builds `states` from `replayMatch`; `renderer.js` `attachReplay` indexes `payload.states` — same re-derivation, not a parallel recording. |
| 3 | Static viewer | **pass** | Manifest `game.replay_viewer == {"bundle": "static-replay-viewer"}` (parsed); `tools/build_replay_viewer.sh` present, mode **100755** (`git ls-files -s`), invoked by path in ci.yml with an exec-bit assertion; only network call in the bundle is `fetch` on the `?replay=` URL (`static_replay.js:76`), assets relative. `/client/replay` is a starter-inherited in-container debug route, not a platform pod path (see N1). |
| 4 | Both name spaces | **pass** | Prompts/player frames carry aliases only (`llm.nim:247-411` uses `RegionNames`; `playerViewJson` has no policy names — `test_sim.nim:665` asserts; final frame rewritten with aliases, `server.nim:176-189`). Policy names appear in `results.names` (`sim.nim:581`), `replay.policyNames` (`server.nim:144`), and the renderer's `makeNameMap`/`applyNames` (`renderer.js:773-812`). Viewer smoke scorebug at head shows both: `Sprocket ▶ 0 RIVERBEND …`. Permutation re-drawn per seed (`sim.nim:240-245`). |
| 5 | Degrade-never-hang, 720 s | **pass** | Connect wait bounded 180 s (`server.nim:233-239`); play deadline `gameStart + 1200×0.6 = 720 s` checked between weeks (`server.nim:262-294`, `endEarly` → `"deadline"`); first LLM batch `max(5, min(llmTimeoutSeconds, budgetSeconds))` (`llm.nim:656-661`), retry `max(5, min(10, remaining))` (`llm.nim:653-655`); pacing clamped to `PacingBudgetMs div weeks` (`sim.nim:186-187`); artifact POST 60 s (`server.nim:123`); `makeRequests` cannot raise (curly pin, `{.raises: [].}`). No blocking read: player sockets deliver prompts only. Defaults arithmetic: 20 × (25+10+0.3) ≈ 707 ≤ 720. Tests: `test_bot.nim:312-343` (batch bound), `test_sim.nim:387` (deadline settle). |
| 6 | `num_agents` everywhere + smoke invariants | **pass** | `num_agents: 6` in `variants[standard]`, `variants[sprint]`, `certification.game_config` (parsed from the manifest); config_schema `minimum:6, maximum:6`. `docker_smoke.sh:106-151`: four `SEAT-COUNT FAIL:` invariants before any container starts + `SMOKE_SEATS` (6, `:54` and ci.yml `SLUG`-block comment) as the independent second declaration. Grepped the full docker-smoke job log at head (97189492117): **zero** occurrences of `SEAT-COUNT`; `smoke OK: seats=6 results=339B replay=19809B reason=complete`. `test_manifest.nim:27-45,145-149` re-assert. |
| 7 | Scripted baseline: full legal episodes, grid-tuned | **pass** | `test_bot.nim:20-46`: all-sentinel, all-laggard and 3/3 mixes, 4 seeds, 20 weeks, `check sim.reason == "complete"`, every dial/gate in range, aid/say empty, `dials == 20×Seats`; `applyDecision` raising is the legality gate (`helpers.nim`). Purity vs hidden state asserted (`test_bot.nim:49-73`). Tuning: `tests/test_sweep.nim` grid harness, shipped cuts are the interior argmax, asserted in CI at head (`cells that beat it 0/24`, both passes). |
| 8 | LLM reply handling | **pass** | `extractJsonObject` takes first `{`..last `}` (`llm.nim:424-436`); one retry with the hint (`llm.nim:649,667-668`); fallback to sentinel (`llm.nim:688-692`); fallback **recorded** — `batch.scripted` → `applyDecision` → `event.scripted` → `"scripted"` in the replay JSON (B1 fix, test `test_bot.nim:282-310`). Pre-flight legality probe rejects illegal replies into the retry (`llm.nim:680-681`). |
| 9 | Rune-safe truncation | **pass** | `say`/`notes` cut with `runeSubStr` at latch (`sim.nim:503-515`); parser-side `cleanText` (`llm.nim:415-422`); aid names, prompt frames, error heads all rune-trimmed (`llm.nim:581-582`, `server.nim:471-472`, `llm.nim:431-433`, `llm.nim:472-495` after N9). Tests: `test_replay.nim:10-68` feeds 4-byte emoji + combining marks at the cap, asserts `validateUtf8(bytes) == -1` over the serialised payload and byte-stable round-trip; `test_sim.nim:441-495`; `test_bot.nim:220-235`. |
| 10 | Manifest validates | **pass** | Parsed at head: `game.docs.readme == {"type":"text","value":…}` (6 299 chars), `pages` = `[{id:"rules.md",…},{id:"protocol.md",…}]` each with non-empty `content.value`; `game.protocols` has **both** `player` (1 930) and `global` (2 241), each `type:"text"`. `reason.enum == ["complete","deadline"]`; `scores` has no `maximum`. `test_manifest.nim:61-105` asserts. |
| 11 | Legible at 360 px | **pass** | `client/chrome.css:282-294`: `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (plus ellipsis rules); `@media (max-width: 640px)` at `:471` hides `.plate-label`; `@media (max-width: 420px)` at `:477`. Statically guarded by `test_manifest.nim:180-198`. |
| 12 | Release order and scaffold | **pass** | `coworld-release.yml` single job, step order: Build the Coworld manifest (:153) → Certify locally (:167) → Upload the policies (:206, comment "BEFORE upload-coworld") → Upload the Coworld (:304) → Put the Coworld secret (:342, "AFTER upload-coworld"). No smoke step in release; ci.yml's smoke builds its image in-job. All three workflows present; `docker_smoke.sh` mode 100755. `policies.json`: 4 policies, 2 `PLAYER_PROMPT` champions + 2 `PLAYER_SCRIPTED` fillers, champion #2 (`contagion-broker`, the second `PLAYER_PROMPT`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate: I ran the exact three-name grep over the five files — no matches, exit 1 from grep ⇒ gate exits 0. |
| 13 | Viewer executes | **pass** | (i) `wasm-viewer` green in run **32637561078** at 66e0821, `needs: docker-smoke` (ci.yml), the `Load the bundle in a real browser` step ran (not absent, not continue-on-error) and printed `{"loaded":true,"ms":280,"clock":"WEEK 0 / 6 · WAITING ON 6",…}` plus scrub readouts at 0/50/100 %, loading the replay docker-smoke produced (`dist/smoke/replay.json`). (ii) `data-replay-loaded="true"` set inside the first `frame()` after `renderer.draw(view)` returns (`renderer.js:1483-1488`); `data-replay-error` set in `fail()` / removed per attempt (`static_replay.js:56,107,134`). (iii) `config.nims:44-45` `-s MODULARIZE=1 -s EXPORT_NAME=ContagionReplayModule`; the shell calls the factory `ContagionReplayModule()` (`static_replay.js:138`); no `onRuntimeInitialized` anywhere in the shell (grepped); exported `_cg_*` symbols match the shell's five calls. The smoke's `loaded: true` is the evidence, and it exists. |
| + | Simultaneous batch rider | **pass** | One `RequestBatch` per attempt over all open seats, one `client.curl.makeRequests(batch, timeout)` per attempt (`llm.nim:662-671`); `decideAll` called once per week (`server.nim:306-307`). No per-seat request loop anywhere. |

## Fixer report audit

| finding | fixer said | I verified at 66e0821 | agrees |
|---|---|---|---|
| B1 | fixed, 37af17e | `decideAll` tuple + `batch.scripted[index]` at `server.nim:316`; test present, green | yes |
| N1 | refuted | manifest declares bundle; route is starter-inherited debug page; certify gate enforces the static rule | yes |
| N2 | fixed, b648cac | `pinUnconnectedSeats` at `server.nim:214-225`, called at `:246`; test present | yes |
| N3 | refuted | no checklist item requires an all-scripted cert fixture; item 6 invariants hold; fixture completes in smoke | yes |
| N4 | refuted | item 11's rule intact at `chrome.css:282-294`; extra hunks are 6-plate geometry | yes |
| N5 | refuted | code self-consistent; note's arithmetic wrong per reviewer's own derivation; sweep now lands the note's +11.4 k target | yes |
| N6 | refuted | additive series, history-bounded | yes |
| N7 | refuted | viewer-only, outside replayMatch's check | yes |
| N8 | fixed, 08ba0f8 | fallback from `simCopy` at `server.nim:336`; helpers snapshot per week | yes |
| N9 | fixed, b2387da | four heads through `cleanText` (`llm.nim:472-495`) | yes |
| N10 | fixed/refuted, 2ad39e2 | `nameMap.text` at `renderer.js:841,889`; wording refutation sound | yes |
| N11 | fixed, 66e0821 | raise removed from `types.nim`; clamp test added | yes |
| N12 | refuted | **independently confirmed from the pinned curly source**: `makeRequests … {.raises: [], gcsafe.}`; errors per-request; `OPT_TIMEOUT` seconds | yes |
| CND-1 | fixed, 4d3d6f0 | `test_sweep.nim` in tree, argmax line printed in CI at head, constants match | yes |
| CND-2 | settled | same curly source read | yes |
| CND-3 | settled | curly `CurlPool` overloads confirmed (`timeout: float32 = 60` → `OPT_TIMEOUT`); bitworld procs not directly readable here, but every in-tree wait is bounded and the residual is a 60 s post-play bound — item 5 stands on in-tree evidence | yes (with the bitworld caveat noted) |
| CND-4 | fixed, 9454773 | first-batch clamp at `llm.nim:656-661`; silent-socket test present, green | yes |

## Non-blocking observations (mine, new; no checklist item falsified)

1. The deadline check runs before each week, so the final week can overshoot 720 s by up to one
   week's bound (~35 s with defaults) before settling — the design's own arithmetic
   (design.md:291-304) accepts this and the total stays far inside the 1200 s kill. Consistent
   with the starter's discipline; not a hang.
2. `laggard`'s contract test (`test_bot.nim:76-88`) still generates decisions from the mutating
   sim (the fixer's NOTED #1); harmless since the laggard reads only its own history.
3. `extractJsonObject`'s error head uses `"..."` while `cleanText` uses `"…"` — cosmetic.

## What I could not verify, and why it does not count as blocking

- `bitworld/runtime`'s `readCogameUri`/`writeCogameUri` internals (dependency not vendored, pkgs
  dir not present in this sandbox). This does not leave a checklist item unverified: item 5's
  bounded-wait claims are established from the tree for every wait in the play path, the artifact
  write happens after play with ~480 s of headroom, and the curly primitives bitworld delegates to
  default to 60 s (`OPT_TIMEOUT`) at the pinned commit I did read. Every numbered checklist item
  above is verified from the tree or from cited CI evidence; none is left in an unverifiable state.

## Blocking findings list

(none)

BLOCKING: 0
