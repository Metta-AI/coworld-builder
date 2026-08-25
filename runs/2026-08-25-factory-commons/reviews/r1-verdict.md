blocking: 0

# r1 verdict — factory-commons
Head: 0079af89bb220cd03b654866472323648f87d9f0   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Repo read at /tmp/cogame-factory-commons-judge (verified `git rev-parse HEAD` = 0079af8, CI run
32883915882 conclusion **success** on main at that sha). I read the tree, the design note, and the
CI logs, and wrote my own checklist pass before opening `r1-review.md`; `r1-fixes.md` was opened
only after the independent pass, to audit its disposition table.

## Standing blocking findings

None. Every finding that was blocking at the review sha is fixed at the current head, and my own
checklist pass found no new blocking finding.

## Refuted

### B1 — "No test asserts frame-by-frame reproduction of the recorded per-tick state" → REFUTED (fixed at head)
- The finding was correct at the review sha (62681ee): the only replay tests were structural plus
  four sampled `hudFromReplay` indices.
- Evidence at head: commit `119a8ba` added `assertEveryFrameRederives`
  (`tests/test_replay.nim:260-375`). `runRecorded` (`tests/test_replay.nim:247-258`) plays the
  episode tick by tick and captures a `LiveTick` off the sim's own fields after **every**
  `stepTick()`; the test then loops `for i in 0 ..< replayDoc.frames.len` and asserts
  `hudFromReplay(i)` — the viewer's own derivation path — equals that live state: tick, integrity,
  cap, both stocks, cooldown, mode, band, the event-folded counters (`presses`, `strips`,
  `repairs`, `bananasMade`, `bananasRotted`, `bananasSpoiled`, `onChute`, `scrappedBy`), every
  loose cube and banana by position/colour/age, and per seat position, hand, score, eaten, banked,
  presses/strips/repairs/misfeeds/fallbacks, standing order and `say`. It also pins the two
  independent recordings against each other: `series[i][1] == frames[i].m[0]` and
  `series[i][2] == frames[i].m[1]` (`tests/test_replay.nim:279-287`), and asserts the episodes
  actually pressed/stripped/made bananas so an empty loop cannot pass (`:365-371`). Run on both
  all-steward and all-stripper rooms (`:369-374`).
- CI at head: `test_replay: 75708 checks passed (187496 replay bytes, 240 events, 900 frames)` in
  both the debug and release passes of run 32883915882 (job 97919738899, log lines 1169/1173) —
  up from 3 772 at the review sha, so the frame loop demonstrably runs.
- Checklist item 2 is therefore satisfied: the re-derivation is asserted frame by frame, and the
  viewer (live `/global` and the wasm bundle alike) is fed by the same `HudModel` →
  `buildStateJson` path the test exercises (`src/factory_commons/server.nim:106-172`,
  `src/factory_commons/replays.nim:254-379`, `src/factory_commons/broadcast.nim`).

### Reviewer non-blocking findings, audited at head
The reviewer classified N1–N18 as non-blocking; I verified none of them falsifies a checklist item
at the current head. The ones that brushed a checklist item are now fixed:
- **N17** (worst-case settle ≈773 s > 720 s — item 5): fixed at `3888081`.
  `shiftFitsBeforeDeadline` (`src/factory_commons/llm.nim:723-734`) requires
  `now + shiftBudgetSeconds() + settleBudgetSeconds() <= deadline` and the shift loop tests it
  between shifts (`src/factory_commons/server.nim:356-363`), so the last shift starts only if it
  can also settle inside 720 s; `tests/test_llm.nim:417-428` pins the boundary and asserts the
  180 s connect ceiling plus the reserve fits the budget.
- **N15** (transport call outside the `try` — item 5): fixed at `7a0254c`. The
  `client.stub(batch)` / `curl.makeRequests` call now sits inside
  `try/except CatchableError` (`src/factory_commons/llm.nim:785-792`); a raising stub is driven in
  `tests/test_llm.nim` and every seat still gets a `source: fallback` order.
- **N7** (429 retried in-shift — item 8/5): fixed at `7434451`. `textOf` raises `ThrottledError`
  (`llm.nim:642-644`) and `decideAll` catches it ahead of the general handler
  (`llm.nim:805-814`): the throttled seat takes the scripted order this shift (counted as
  fallback) and returns in the next shift's batch, per the design note.
- **N1/N3** (constants off the note; stale prompt numbers): `eatTrigger` restored to the authored 3
  (`src/factory_commons/sim_config.nim:70`, manifest default 3 at
  `coworld_manifest_template.json:213`); `moveCooldown 1` and `stripCapLoss 16` are rungs of the
  note's own repair ladders (design.md:397-399) and are now evidenced by a committed sweep
  (`tools/tune/feasibility_sweep.nim`, `docs/tuning.md`). Prompts quote the shipped constants:
  `tools/ci/policies.json:6` now says "four bananas … sixteen cap", the custodian keys on 68
  (a value the cap walk 100→84→68 visits), and `floorPlanText(config)`
  (`src/factory_commons/llm.nim:414-427`) derives tick costs from `config.moveCooldown`
  (asserted at `tests/test_llm.nim` — the moveCooldown-2 prompt says 44 ticks, never 22).
- **N14** (nimby pin drift — item 1): fixed at `c8ba7f1`; `.github/workflows/ci.yml:35` is
  `NIMBY_VERSION: "0.1.27"`, matching both Dockerfiles, and the test job built green with it.
- **N4, N5, N6, N8, N9, N10, N11, N12, N13, N18**: declined by the fixer; I verified each
  disposition against the tree and agree none falsifies a checklist item (details in the audit
  table below and in the checklist pass).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 32883915882, main, headSha 0079af8, conclusion success; jobs test/docker-smoke/wasm-viewer all success. `git log -p --since=2026-08-25T14:01Z -- tests/` read in full: every hunk adds assertions except two in `e9ccce0`, both justified by a code fix in the same commit — `test_broadcast.nim:184` `mt == config.maxTicks()` → `doc.maxTick()` (the old form was *failing* on run 32873190436 because shift/end events were stamped one past the last recorded frame; the commit fixes the stamping to `boundaryTick` and re-points the assertion at the recorded span), and `test_replay.nim:46` fixture `[steward,steward,stripper]` → all-steward (no assertion deleted; the factory_ruined case keeps its own block at `:434-452`, and `119a8ba` later added an all-stripper full-frame loop). No skip/xfail/tolerance widening anywhere (the only "skip" string, `test_llm.nim:385`, is an offline-only guard present since the initial commit, inert in CI which has no key). |
| 2 Replay re-derivation | PASS | `tests/test_replay.nim:260-375` (see B1 refutation); CI `test_replay: 75708 checks passed`. |
| 3 Static viewer | PASS | `coworld_manifest_template.json:28-30` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`) with the ecos `mkdir -p`-before-`pwd -P` fix (lines 19-23); the worker's only network call is `fetch(message.replayUrl)` (`replay-viewer/static_replay_worker.js:113`); no `/client/replay` route exists — the only textual hits are the release workflow's own error message forbidding it (`coworld-release.yml:201`) and the starter-inherited URL-mapping helper in `client/broadcast_core.js:212`, which is not a served route (`src/factory_commons/server.nim:546-555` registers only /healthz, /client/global, /client/player, /global, /player). |
| 4 Both name spaces | PASS | `observationJson`/`systemPrompt` emit only `Aliases[]` (`src/factory_commons/llm.nim:298-387,429-504`); no policy/player/model name or seed reaches a seat (`tests/test_llm.nim` asserts the negatives); `roster[].pol` carries the policy name viewer-side (`broadcast.nim`), `results.names` policy names + `results.aliases` aliases (`sim.nim:347-369`), replay carries `names[]` and `policyNames[]` (`replays.nim:115-119`). |
| 5 Degrade-never-hang | PASS | Connect bounded by `playerConnectTimeoutSeconds` (`server.nim:292-301`); batch bounded by `makeRequests(batch, timeoutSeconds)` inside try (`llm.nim:785-792`); no round barrier — a seat with no socket plays steward (`server.nim:371-374`); pacing bounded by `minTurnSeconds` (`llm.nim:697-710`); `shiftFitsBeforeDeadline` reserves shift+settle so the episode settles ≤ 720 s of the 1200 s timeout (`server.nim:356`, `llm.nim:712-734`, `tests/test_llm.nim:417-428` incl. connect-ceiling + reserve ≤ deadline); `while true` exits on `sim.done` or the deadline; all LLM calls one parallel batch. |
| 6 num_agents | PASS | `num_agents: 3` in all four variants (`coworld_manifest_template.json:514,540,564,589`) and in `certification.game_config` (`:612`); `tools/ci/docker_smoke.sh:110-151` enforces all four invariants plus the `SMOKE_SEATS`=3 cross-check, every violation `SEAT-COUNT FAIL:`-prefixed and exit non-zero; grep of the docker-smoke job log (job 97919739037): **0** occurrences of `SEAT-COUNT FAIL`; log shows `game=factory_commons seats=3`, `all 3 player containers exited 0`, `smoke OK: seats=3 … reason=complete`. |
| 7 Scripted baseline full episodes, tuned | PASS | `tests/test_feasibility.nim:85` gate (a) asserts `reason == "complete" and ending == "shift_limit"` on all-steward rooms (≥10/12 seeds, 4 variants); `tests/test_baseline.nim` asserts every order/action inside its enum, every state invariant, per tick, over 12 seeds × 4 variants × 6 seat mixes (CI: 6 631 622 checks); grid harness committed: `tools/tune/feasibility_sweep.nim` (153 lines) + `docs/tuning.md` recording the sweep table that chose moveCooldown 1 / stripCapLoss 16 / eatTrigger 3. |
| 8 LLM reply handling | PASS | `extractJsonObject` takes first `{` to last `}` (`llm.nim:597-606`); one retry batch with the hint (`llm.nim:766-777`); fallback recorded as `osFallback` (`llm.nim:821-825`), counted into `results.fallbacks` (`sim.nim:334-335`, `:378`); 429/403 handled per design. `tests/test_llm.nim` drives fenced/prose replies, junk, timeouts, 429, 403, raising transport. |
| 9 Rune-safe truncation | PASS | `cleanText` = strip → `runeSubStr(0, limit-1) & "…"` (`llm.nim:65-75`), applied to say/notes/error(200)/prompt(4000) (`server.nim:520-521`); `tests/test_replay.nim:381-432` feeds multi-byte strings exactly at the 90/320 caps through two played shifts and asserts every recorded string `validateUtf8 == -1` and ≤ cap. |
| 10 Manifest validates | PASS | `game.docs` = `{"readme":{"type":"text","value":…},"pages":[{id,title,content:{type:text,value}}]}` (`coworld_manifest_template.json:435-458`); `game.protocols` carries both `player` and `global`, each `{"type":"text","value":…}` (`:459-468`). |
| 11 Viewer legible at 360 px | PASS | `.plate-name, .plate .team-name { flex: 1 1 auto; min-width: 3.2em; }` (`client/replay_broadcast.html:1155`); `@media (max-width: 640px) { .fc-chip .fc-pol { display: none; } }` (`:1353-1354`) plus `#stage.tiny` label hiding (`:1358-1359`, switched at boardW ≤ 620, `:2670`). |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify locally (:167) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342); all three workflows present; `docker_smoke.sh` mode 100755; `policies.json` has 4 policies — 2 `PLAYER_PROMPT` champions (both `USE_BEDROCK:"true"`) + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (`tools/ci/policies.json:17`); the three-name placeholder grep over the five files returns nothing (gate exits 0, run locally). |
| 13 Viewer executes | PASS | wasm-viewer green at head incl. "Load the bundle in a real browser" (job 97920413219: `{"loaded":true,"ms":379,"clock":"SHIFT 5 / 8 TICK 287 OF 479",…}`, `soak: 12s of playback kept advancing ("0 / 479" -> "239 / 479" -> "287 / 479")`, three distinct readouts); `needs: docker-smoke` (`ci.yml:212`); no smoke step absent/commented/continue-on-error (job step list read). Shell sets `data-replay-loaded="true"` on the first drawn frame (`replay-viewer/static_replay.js:141`) and `data-replay-error` in `showFailure` (`:15-19`). Link flags and bootstrap are the matched coworld-ctf pair: `config.nims` diff against the starter shows only the renamed output/exports and the dropped `_ctf_mismatch_tick` — **no MODULARIZE, no EXPORT_NAME** — and the worker bootstraps with `Module.onRuntimeInitialized` (`static_replay_worker.js:164`) and `importScripts(…,'factory_commons_replay.js')` (`:212`). `emscripten_exit_with_live_runtime` epilogue present (`factory_commons_replay.nim:206-217`). |
| 14 Chrome is the starter's | PASS | `client/chrome_common.js` byte-identical to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diff empty, verified myself). `client/replay_broadcast.html` (3109 lines) is the starter's page with banner-marked game blocks (CSS `:1133`, JS `:2686`); I diffed the whole file against the starter: every deletion maps to a removal the note lists (#viewpanel/#minimap/#zoombar, #fpv family + POV/raycast renderer, #povBadge, #mmwarn) or to the starter's own PAINTBALL game block (which the factory block replaces — the same appended-block slot), plus the two re-lettered literals (`Integrity` `:2241→1982`, `MACHINE INTEGRITY` `:1435`) and `#lockerroom{pointer-events:none}` (`:963-966`). Transport rules verified: (a) `relayout()` sets `--hudscale`/`--topband`/`--band` on `document.documentElement` (`:2669-2675`), `--u` on `:root` (`:40-42`); (b) the appended overlays live inside `#chrome` = `inset: var(--topband) 0 var(--band) 0` (`:112`), top-anchored — nothing fixed sits in the band; (c) `#endcard` keeps `top: var(--topband); bottom: var(--band)` (`:722-723`), shown with `#endcard.on` (`:734`, added `:3080`), and the frame path removes `.on` whenever `ph !== 'gameover'` (`:1872-1873`), so every seek off the terminal frame takes it down; (d) beats are chrome_common's `markBeat(tick, kind, team)` markers decorated to `role="button"`/`tabindex=0`/aria-label/title with click + Enter/Space seek (`:3012-3046`), CSS for all five emitted kinds — shift, lock, strip, scrap, gameover (`:1296-1305`) — and `beatAt`'s doAssert makes a sixth kind impossible. `#viewpanel` removed, not hidden (no markup, no CSS, no wiring), correct for a 1248×720 board that always fits the frame. |
| 15 Every drawn string fits | PASS | `tools/ci/viewer_smoke.mjs` is the template verbatim (diffed against `/workspace/coworld-builder/templates/tools/ci/viewer_smoke.mjs`: identical) and gates `never_inside` under `--strict-text-bounds`; `ci.yml` carries the flag on both steps (`:326`, `:348`) — correct for a fixed arena. Replay-smoke `canvas text: 0 drawn, 0 never inside, 0 ellipsized`: total 0 is genuine, not a blind spot — no `fillText`/`strokeText` exists anywhere in client JS (grep empty); board strings are pre-rendered PNG sprites (`data/label_*.png`, `global.nim:124-126`) and all LLM text is DOM. The compensating worst-case renderer fixture required by the checklist exists (`tools/ci/renderer_fixture.html`), loads the **real** `client/chrome_common.js` and instantiates `ChromeCommon`, feeds full-cap 90/320-rune multi-byte `say`/`notes` on every seat at 360/620/1280 px, asserts its own rune counts and overflow, sets both markers, and runs in its own ci.yml step (`:335-350`): `{"loaded":true,…,"feed_lines":9}`, `canvas text: 9 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` (job 97920413219). |
| Simultaneous batch | PASS | `decideAll` builds one `RequestBatch` for all open seats (`llm.nim:766-777`); `server.nim:382` calls it once per shift; `tests/test_llm.nim:149` asserts `lastBatchSize == SeatCount`. Sequential calls do not exist. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `119a8ba` | frame loop present at head, live-vs-derived on every frame + series↔frame, runs in CI (75 708 checks) | yes |
| N1 eatTrigger | fixed, `04058a7` | `sim_config.nim:70` = 3, manifest default 3, tuning table committed | yes |
| N1 moveCooldown/stripCapLoss | declined (ladder-sanctioned) | design.md:397-399 names both rungs; sweep evidence in docs/tuning.md | yes |
| N2/N3 stale prose/prompts | fixed, `90424bd`/`0079af8` | policies.json says four/sixteen; custodian keys on 68; floorPlanText derives from config; README follows the code | yes |
| N4 steward harvest rule | DISPUTED (measured) | deviation documented at `scripted.nim:56-67`; statelessness asserted; gate (a) is the note's own stated enforcement | yes (advisory) |
| N5 gate (b) either-or skip | declined | written reason in `test_feasibility.nim:113-121`; gates a/c/d run on all four variants; gate (e) covers the lock | yes (advisory) |
| N7 429 | fixed, `7434451` | `ThrottledError` → scripted this shift, next-shift retry (`llm.nim:805-814`); tests drive both shapes | yes |
| N9 capMin 25 fixture | declined | documented + enforced at `test_manifest.nim`; keeps the cert replay (479 ticks = 20 s) longer than the 12 s soak | yes (advisory) |
| N11 beat markers | declined | decorated divs are chrome_common's own markBeat path; a real `<button>` would require editing the byte-identical file | yes (advisory) |
| N14 nimby pin | fixed, `c8ba7f1` | ci.yml:35 = "0.1.27" | yes |
| N15 transport try | fixed, `7a0254c` | call inside try at `llm.nim:785-792`; raising-stub test present | yes |
| N17 settle budget | fixed, `3888081` | `shiftFitsBeforeDeadline` + budget procs + boundary tests | yes |
| CND-1 curly raises | settled by test | the raising-stub test makes the question moot | yes |
| CND-2 grid harness | settled by artifact | `tools/tune/feasibility_sweep.nim` + `docs/tuning.md` sweep table | yes |
| CND-3 connect cost | addressed | `test_llm.nim` asserts 180 s ceiling + reserve ≤ deadline | yes |
| CND-4 real-page 360px feed | declined | checklist 15 requires the fixture, which exists and is gated | yes (advisory) |

## Non-blocking observations (mine, not tied to a checklist item)

1. `replay-viewer/static_replay.js` is not quite "verbatim apart from the export names" as the
   design note claims: beyond the mismatch-plumbing removal (justified — nothing re-simulates), it
   also dropped the starter's adaptive frame-batch throttle (`lastAdvanceMs`) and the worker's
   `applyInputNow` immediate-seek path. On a ≤900-frame replay the seek latency this machinery
   addressed is negligible, and the CI smoke shows three distinct scrub readouts, so this is a
   provenance nit, not a defect.
2. `client/replay_broadcast.html` replaced the starter's queue-a-click-before-the-first-frame
   (`SEEK_FRAC`) seek path with the older drop-the-click behaviour (`:2434` `if (!lastState ||
   !lastState.en) return;`) — the queueing code was entangled with the removed PB_MODE block. A
   scrub click in the first milliseconds of load is dropped; the first chrome frame of a static
   replay lands almost immediately, so this is cosmetic, but it is an inherited-chrome regression
   worth restoring if the page is touched again.
3. The renderer fixture mirrors the game block's feed/roster CSS rather than rendering the real
   page's rules with full-cap strings (limitation stated in the file at `:31-36`). The caps are
   pinned server-side and in the fixture; drift between the mirrored CSS and the page's would not
   be caught. Advisory only — checklist 15's requirement (the fixture, gated, with a non-zero
   `canvas_text.total`) is met.

## What I could not verify

Nothing that the checklist requires. Everything above is verified from the tree at 0079af8, from
the cited CI run 32883915882 (job logs fetched via `gh api`), or from the coworld repo's own git
history since the run start.

BLOCKING: 0
