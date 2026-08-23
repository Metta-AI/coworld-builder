blocking: 0

# r1 verdict — 2026-08-23-tribunal

Head: `11ec31627ffc8e3db159e879d7b4b513f183da69` (`Metta-AI/cogame-tribunal`, main)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** (repo, design note, workflows, CI logs, and
starter diffs all read and noted before opening `r1-review.md`; `r1-fixes.md` opened last).
Reviewed against: review at `d69e4e3`; **all verification below is at the current head `11ec316`.**

## Standing blocking findings

None.

## Refuted

### F1 — "a `deadline` ending at or after the ballot re-derives as `complete`" → REFUTED AT HEAD (fixed)
- The finding was **true at `d69e4e3`** (the review's sha) — the reviewer's trace of
  `beginDeadlineBallot`'s `if sim.done or sim.phase != phArgument: return` guard is correct, and I
  reproduce the reasoning from the old code path. It is **false at the current head**:
  `src/tribunal/sim.nim:963-971` (commit `c02c4c0`) pre-seeds the reason from the recorded log
  before replaying —
  ```nim
  for event in events:
    if event.kind == evEnd and event.text.len > 0:
      sim.reason = event.text
  ```
  and `settle`'s `if sim.reason.len == 0: sim.reason = "complete"` (sim.nim:559-560) therefore
  never overwrites a recorded `"deadline"`. `reason` is rendered only when `sim.done`
  (`tableStateJson` sim.nim:908, `playerStateJson` sim.nim:933), so no earlier frame changes.
- Test at head: `tests/test_sim.nim:409-428` *"a deadline at the ballot re-derives as a deadline,
  not as complete"* — plays to `phBallot`, one real vote, `forceBallot()`, then asserts
  `frames[^1].reason == "deadline"`, the replayed `end` event's text, frame-count, full
  `$frames[^1].tableStateJson() == $live.tableStateJson()`, and `resultsJson()["reason"]`. Ran
  `[OK]` twice (debug + release) in CI job 97225135935 of run 32652071584.
- A finding that was true and has since been fixed is refuted, not standing. Count: 0.

F2–F14 were filed advisory by the reviewer and none ties to a falsified checklist item at head
(F2 and F3 are additionally fixed at head — see the audit table). I found no reviewer claim that
misstates the code at the sha it cites; the review's traces reproduce.

## Checklist pass (independent)

| item | status | evidence (path:line or run/job id) |
|---|---|---|
| 1 CI green, no test loosened | **pass** | `gh run list -w ci.yml --branch main`: run **32652071584**, event `push`, `headSha == 11ec3162…`, conclusion **success**; jobs test 97225135935 ✓, docker-smoke 97225136091 ✓, wasm-viewer 97225257449 ✓. `git log -p --since="2026-08-23T14:59Z" -- tests/`: 4 commits touch tests/ (`c55fc08` creates both files; `c02c4c0` +21, `6bcbff1` +5, `11ec316` +3 — **insertions only**; a grep for deleted lines across all tests/ hunks returns none). No skip/xfail/tolerance anywhere in `tests/`. |
| 2 Replay re-derivation | **pass** | `replayMatch` (sim.nim:953-1003) re-derives frames from seed+events, raises `TribunalError` on a tampered `round` event (sim.nim:979-981); tests assert `frames.len == events.len + 1` and final-frame JSON equality for complete (test_sim.nim:358-384), mid-argument deadline (386-407) and ballot-phase deadline (409-428) shapes. The viewer draws from the same re-derivation: wasm `tribunal_replay.nim:36-37` runs `replayMatch` and `renderer.js:1478-1501` (`attachReplay`) renders `payload.states` — not a parallel recording. |
| 3 Static viewer | **pass** | `coworld_manifest_template.json:15-17` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode `100755` (git ls-files -s), release workflow builds via `coworld build --template …` (coworld-release.yml:159-164) which hard-requires the hook; shell fetches exactly one URL — the `?replay=` argument (static_replay.js:76, 128) plus bundle-local `./assets`. No replay pod declared anywhere; the only `/client/replay` strings are the live server route (server.nim:485, starter convention) and manifest prose that itself says "there is no replay pod". |
| 4 Both name spaces | **pass** | Prompts/whispers/events carry only `sim.names` (aliases from `CogNames`, sim.nim:204-215; llm.nim:256, 284); `resultsJson` carries policy names (sim.nim:755); replay carries both `names` and `policyNames` (server.nim:128-146); viewer `makeNameMap` (renderer.js:856-880) swaps policy names in wherever rendered, leaving `isBaselineFiller` matches on aliases (renderer.js:852-854). |
| 5 Degrade-never-hang | **pass** | Connect wait: `while epochTime() < deadline … sleep(200)`, deadline = start + 180 s (server.nim:223-229). LLM: `curl.makeRequests(batch, client.timeoutSeconds)` = 45 s, ≤2 attempts per turn (llm.nim:568-596). No round barrier — the last applied decision resolves the round synchronously. Pre-turn deadline check at 0.6 × timeout (server.nim:251-253, 271-277) → `forceBallot()` (sim.nim:722-739) settles and scores with `reason = "deadline"`. `pendingSeats` shrinks to ∅ every turn (all decisions applied or replaced by the always-legal scripted fallback, server.nim:299-324), so the `while true` loop terminates. Pacing bounded by `PacingBudgetMs` via `sampleEpisode` (sim.nim:231-232). |
| 6 num_agents | **pass** | `num_agents: 5` in `standard` (manifest:349), `long-trial` (:377) and `certification.game_config` (:403). `docker_smoke.sh:110-151` enforces all four invariants (present / positive int / `len(certification.players)` / `len(certification.game_config.players)`) plus the independent `SMOKE_SEATS=5` cross-check, each exiting via `SEAT-COUNT FAIL:`; the script is the coworld-builder template with only `<slug>/<IMAGE>/<SEATS>` substituted (diffed). **Grep of the docker-smoke log (job 97225136091): zero `SEAT-COUNT FAIL` matches**; it printed `game=tribunal seats=5 …` and `smoke OK: seats=5 results=342B replay=2475B reason=complete`. |
| 7 Scripted baseline full episodes | **pass** | `test_bot.nim:33-78`: seeds [1,7,42,1234] × both baselines × every role, asserts `sim.done`, **`reason == "complete"`**, `cards.len <= MaxIntroducePerTurn`, no id twice, `introducedBy[side] <= handOf(side).len`, arguments non-empty ≤320 runes, votes legal, <2000 ms. Tuning is measured, not guessed: `test_bot.nim:92-106` gates the all-tally truth-tracking rate to 0.55–0.85 over 400 seeds and echoes it — CI printed `rate … 0.6875` (job 97225135935), inside the design's ~66 % band. |
| 8 LLM reply handling | **pass** | `extractJsonObject` takes first `{` to last `}` — tolerates prose/fences (llm.nim:403-415); exactly one retry batch with the invalid-reply hint (`for attempt in 0 .. 1`, llm.nim:568-576); fallback to `scriptedAction(…, skTally)` (llm.nim:597-600); recorded twice — the stdout line `tribunal llm: seat <n> falling back to scripted decision` (llm.nim:599) **and**, since `6bcbff1`, `scriptedAction` stamps `result.scripted = true` (llm.nim:226) which the server ORs into the event flag (server.nim:306-307), so the replay counts fallbacks too. Asserted at test_bot.nim:125-133. |
| 9 Rune-safe truncation | **pass** | `tidy` = `runeSubStr` (sim.nim:182-188) caps argument 320 / whisper 200 / reason 200 and — since `11ec316` — notes 600 in all three apply procs (sim.nim:616, 657, 700); `cleanText` = `runeSubStr` (llm.nim:478-483); player prompt capped at 4000 runes with `runeSubStr` (server.nim:454-455); captured-error head capped with `runeSubStr` (llm.nim:410-412). Tests feed 400ׅ`日` / 800ׅ`é` / 500ׅ`ß` at and over the caps and assert `runeLen == cap` and `validateUtf8() == -1` on events, `tableStateJson`, `resultsJson` (test_sim.nim:327-355); docker-smoke re-parses the replay bytes as strict UTF-8 JSON (docker_smoke.sh:285-292). |
| 10 Manifest validates | **pass** | `game.docs.readme` = `{"type":"text","value":…}` (manifest:234-236); `game.docs.pages` = 2 entries each `{id, title, content:{type:"text",value}}` (:238-255); `game.protocols` carries **both** `player` (:224-227) and `global` (:228-231). |
| 11 Viewer legible at 360 px | **pass** | `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` (chrome.css:281-293); `@media (max-width: 640px) { .plate-label { display: none; } }` (chrome.css:461-463). Extra 520/420 px column steps only widen the plates further at 360 px. |
| 12 Release order and scaffold | **pass** | coworld-release.yml step order: Build manifest (:153) → Certify (:167, asserts the static-bundle liveness marker) → Upload policies (:206, comment "BEFORE upload-coworld") → Upload Coworld (:304) → Put secret (:342, "AFTER upload-coworld"). ci.yml smoke steps build the image/bundle in the same run (ci.yml:176-185, 248-309). Three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 4 distinct: `tribunal-advocate` + `tribunal-juror` (both `PLAYER_PROMPT`) + `tribunal-tally` + `tribunal-hedge` (`PLAYER_SCRIPTED`), champion #2 (second `PLAYER_PROMPT` entry) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (policies.json:15). Placeholder gate run by me at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files → **no matches, gate exits 0**. Only the documented runtime residue (`<cow_id>/<sha>` ci.yml:202, `<run_id>` release/submit:21/17, `<name>:vN` submit:31) survives. |
| 13 Viewer executes | **pass** | Run **32652071584** (this sha), job `wasm-viewer` 97225257449 green **including the `Load the bundle in a real browser` step**, which executed `node tools/ci/viewer_smoke.mjs --bundle … --replay dist/smoke/replay.json --timeout 90` and printed `{"loaded":true,"ms":308,…}` and `scrub readouts: 0%="ROUND 1 / 2" 50%="ROUND 2 / 2" 100%="TRUTH — NOT GUILTY · JURY 3/3"` — three distinct readouts. `needs: docker-smoke` (ci.yml:212); no `continue-on-error` anywhere in ci.yml. Markers: `data-replay-loaded="true"` set after the first synchronous `renderer.draw` inside `attachReplay` (renderer.js:1551-1555); `data-replay-error=<message>` on every failure path, removed on retry/success (static_replay.js:56, 107, 134). Link flags and bootstrap are a matched pair from the same starter: `-s MODULARIZE=1 -s EXPORT_NAME=TribunalReplayModule` (config.nims:43-44) ↔ factory call `TribunalReplayModule()` (static_replay.js:138); I diffed all four viewer files against `/workspace/starters/cogame-bullwhip` — pure slug/`_bw_→_tb_` renames plus one comment, nothing spliced from another starter. The smoke's `loaded: true` is the evidence, and it is present. |
| One parallel batch per turn | **pass** | `decideAll` builds a single `RequestBatch` for all open seats and issues one `curl.makeRequests` per attempt (llm.nim:571-582); server calls `decideAll` once per turn outside the lock (server.nim:291). 5 requests in an argument round, 3 in the ballot; never sequential per-seat calls. |

(Item 14 of the prompt file — chrome provenance — targets the `chrome_common.js`/
`replay_broadcast.html` starter family and was omitted from this round's brief; bullwhip has
neither file. Checked in spirit anyway: `chrome.css` diffs from the starter in exactly two hunks
(the forced 4→5 seat grid at :266-267 and a 520 px column step at :465-467), `index.html` is a pure
rename, and `renderer.js` keeps every chrome function (`makeNameMap`, `applyNames`, `makeEffects`,
`buildScrub`, `renderFeed`, `bindFeedToggle`, `attachLive`, `attachReplay`) with only the canvas
stage replaced, as the design note specifies. Not a lookalike rewrite.)

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | fixed in `c02c4c0` | sim.nim:963-971 pre-seeds `reason` from the `end` event; new test test_sim.nim:409-428 `[OK]` twice in job 97225135935; fix commit is +31/−0 (no test weakened) | yes |
| F2 | fixed in `6bcbff1` | `Decision.scripted` field (llm.nim:53), `scriptedAction` stamps it (llm.nim:226), server ORs it in (server.nim:306-307); test_bot.nim:125-133 asserts it, `[OK]` in CI | yes |
| F3 | fixed in `11ec316` | `tidy(notes, MaxNotesLen)` in all three apply procs (sim.nim:616, 657, 700), `MaxNotesLen = 600` moved to sim.nim:40; test_sim.nim:340-343 asserts stored and event notes == 600 runes, `[OK]` in CI | yes |
| F4–F14 | not fixed, advisory, with reasons | each re-checked at head; none falsifies a checklist item (F6/F13/F14 detailed under observations); the fixer's evidence citations reproduce | yes |
| CI claim | run 32652071584 success at head incl. browser step | confirmed independently from `gh run list`/`gh run view --log` before reading the fixes file | yes |

No disposition in the fixer's table misrepresents the head state.

## Non-blocking observations

- **F13 arithmetic (long-trial worst case ~723 s vs the 720 s line).** Real but purely adversarial
  (all six turns consuming batch + retry at the full 45 s timeout, connect at the full 180 s), and
  the pre-turn deadline check + `forceBallot` bound it: the episode always settles, scores and
  writes artifacts far inside the 1200 s platform kill. The formula is the design note's own. Not a
  falsification of item 5's bounded-waits requirement.
- **Player container's `receiveMessage()` has no explicit timeout** (tribunal_player.nim:62,
  whisky default `-1`). Item 5 enumerates the game's waits (LLM call, seat reply, round barrier),
  all bounded; the player exits when the bounded game quits, and this is the starter's own shape.
  Recorded, not counted.
- **`chrome.css` is not byte-"unchanged"** as the design note claims (two hunks, both forced by the
  5th seat). Item 11's required rules survive verbatim; deviation is note-vs-tree only.
- Compiled test binaries are not in `.gitignore` (fixer's own note). Housekeeping.

BLOCKING: 0
