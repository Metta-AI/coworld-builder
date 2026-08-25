blocking: 0

# r1 verdict — hanabi

Head: 724826f53754849d1a22fff31cf971027c555f9a   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

I read the checklist prompt, the design note, and the whole tree at head (src/, tests/, client/,
replay-viewer/, tools/, workflows, manifest — plus the starter counterpart of every forked file at
/workspace/starters/cogame-bullwhip) and formed my own notes before opening r1-review.md.
**I did not read r1-fixes.md at all** (withheld by instruction); the "fixer report audit" below is
against the fix commits themselves (`git log`/`git show`), not against anyone's self-report.

The review was written against `b06d9fe`; head is four commits later (`f17e3a3`, `70fc1d5`,
`78e25f3`, `724826f`). Every one of the review's three blocking findings is fixed at head; my own
checklist pass finds nothing standing.

## Standing blocking findings

None.

## Refuted / resolved at head

### F1 — banner ellipsized to a third of its length → RESOLVED at head (fixed by f17e3a3)
- The reviewer's claim was true at `b06d9fe` (band = `max(96, min(width*0.22, 210))`, wrapLines
  ellipsized at 2 lines, fixture log showed 1668 ellipsized).
- At head the band is measured from the server's cap: `client/renderer.js:65`
  `var MAX_BANNER_RUNES = 80;`, `renderer.js:169-177` `bannerBandWidth(ctx, size)` measures
  `BANNER_SAMPLE`'s mean glyph advance in `bannerFont(size)` and returns
  `perRune * (MAX_BANNER_RUNES / BANNER_LINES + 1) + padding`; `computeLayout` uses it at
  `renderer.js:207`. `wrapLines` (`renderer.js:602-633`) no longer takes a line cap and never
  ellipsizes — an over-wide word is broken on a rune boundary; `drawBanner`
  (`renderer.js:635-668`) steps the type down to `BANNER_MIN_SIZE = 7` until the whole string
  fits: "The text is never shortened." The only `ellipsize()` call sites left in the whole
  renderer are the alias plate name and its "N banked · M burnt" stat line
  (`renderer.js:524, 528`) — labels, which checklist 15 explicitly allows.
- CI at head confirms: run 32793042266, wasm-viewer "Load the worst-case renderer fixture" —
  `canvas text: 31988 drawn, 0 never inside the canvas (24 draws crossed an edge), 1096
  ellipsized (--strict-text-bounds)`. The 1096 remaining ellipsized draws can only come from the
  two plate-label sites (drawn every frame at 720/1280 px with deliberately long policy names
  like `hanabi-conventions-filler`); no canvas code path can ellipsize a banner or a learned
  line. `never_inside` — the gated number — is 0 in both browser steps.

### F2 — fixture doesn't assert its strings are full-length; NOTE_LINE 13 runes short → RESOLVED at head (fixed by 70fc1d5)
- At head: `tools/ci/renderer_fixture.html:75-78` — BANNER is exactly 80 runes and NOTE_LINE
  exactly 90 (I measured both with python: 80 and 90). `renderer_fixture.html:207-241` adds
  `assertFullLength` tying BANNER to `MAX_BANNER_RUNES`, NOTE_LINE to `MAX_LEARNED_RUNES`, every
  seat's banner in every frame, every line of every full learned block, plus a check that at
  least one full 6-line learned block exists; a failure calls `fixtureFail`, which sets
  `data-replay-error` (`renderer_fixture.html:210-214`) — exactly what `viewer_smoke.mjs` fails
  the job on (`tools/ci/viewer_smoke.mjs:503`). The fixture step ran green at head with these
  assertions live (`{"loaded":true,"ms":280,...}` in the step log).

### F3 — /client/replay pod route and replay-server mode → RESOLVED at head (fixed by 78e25f3)
- At head `src/hanabi/server.nim:458-466` (`buildRouter`) registers only `/healthz`,
  `/client/global`, `/client/player`, `/client/renderer.js`, `/client/chrome.css`,
  `/client/assets/@name`, `WS /global`, `WS /player` — no replay route of any kind.
  `runReplayServer`, `replayUpgradeHandler`, `framesFromEvents` and the `replayMode` entrypoint
  branch are gone (`grep '/client/replay\|runReplayServer\|replayMode'` over src/ returns
  nothing); `client/replay.html` is deleted. `src/hanabi.nim` starts only the live server. A new
  test pins the removal (`tests/test_viewer.nim:93-101`: no `client/replay.html`, no
  `/client/replay`, no `"/replay"`, no `runReplayServer`, no `replayMode`).

### F8 (non-blocking in the review) — byte-sliced HTTP error heads → RESOLVED at head (fixed by 724826f)
- All five diagnostic sites now go through `headRunes` (runeLen/runeSubStr):
  `src/hanabi/llm.nim:380-385` defines it; used at `llm.nim:414` (no-JSON head), `:617` (auth
  detail, 400), `:626` (throttle detail, 300), `:630-631` (error body, 300), `:639-640`
  (max_tokens head, 160).

### F4, F5, F6, F7, F9, F10 — filed non-blocking; I verified each and agree none falsifies a checklist item
- F4 (deadline-at-turn-0 catch-up settles `"complete"`, not `"deadline"`): still true at head
  (`server.nim:265-275` plays the whole episode scripted, then `endEarly()` no-ops on a done sim,
  `sim.nim:818-824`). A design-note wording deviation; item 5 asks only that the episode settles
  and scores inside the budget, which a ~ms scripted playout does. Both values stay inside the
  documented enums. Advisory.
- F5 (rejection text not on the move event): still true; item 8 requires the fallback be
  *recorded and countable* — `origin: "fallback"` (`sim.nim:714-715`) and `results.fallbacks`
  (`sim.nim:792-793, 855`) satisfy it. Advisory.
- F6 (per-move recorded scalars not compared in replayMatch): still true; item 2's substance
  holds — see checklist pass below. Advisory.
- F7 (canvas banner not name-mapped): still true at head (`renderer.js:575-578` uses
  `data.banner` raw; the feed line maps it, `renderer.js:879-884`). The design note's list of
  name-map render sites (design.md:49-51) does not include the canvas tag. Item 4 satisfied.
  Advisory.
- F9 (#endscreen stops at the band structurally, no `bottom: var(--band)`): verified —
  `#endscreen { position: absolute; inset: 0 }` inside `#board-wrap { flex: 1 }`
  (`chrome.css:374-383, 95`), whose bottom edge is the top of `#transport`; shown with the class
  its rule uses (`#endscreen.show`, toggled by `updateEndscreen`, `renderer.js:1104`) and every
  seek re-evaluates it (`renderer.js:1449-1452`). 14(c) satisfied in substance; this lineage has
  no `#endcard`.
- F10 (unguarded second applyMove in the except branch): true (`server.nim:306-307`) but
  unreachable — `conventionsMove` only returns elements of `legalMoves()`, which is non-empty at
  every state of 200 seeded episodes (`tests/test_sim.nim:321`). Advisory.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32793042266**, headSha `724826f5…` (verified via `gh run view --json headSha,conclusion` → `success`), jobs test/docker-smoke/wasm-viewer all ✓, every step ran (job 97639504479 step list includes "Load the bundle in a real browser" ✓ and "Load the worst-case renderer fixture" ✓). `git log -p --since=2026-08-24T20:40:00Z -- tests/`: two commits — `501a8eb` adds all five test files; `78e25f3` removes `"client/replay.html"` from two page lists **because that file was deleted to satisfy item 3**, keeps every assertion running against `replay-viewer/index.html` + the fixture, and **adds** a new test pinning the removal. I read both hunks: no assertion deleted against surviving code, no tolerance widened, no skip added, no test file removed. Not a loosening. |
| 2 Replay re-derivation | PASS | `sim.nim:1273-1308` `replayMatch` rebuilds the deck from the recorded seed, re-applies every move, raises on any mismatch of outcome/touched/untouched/learned/nowPlayable/nowDead/nowCritical and on a digest mismatch. `tests/test_replay.nim:91-120` (20 seeds: frames.len, tail-frame equality, digest, every hint annotation), `:122-138` (tampered annotation and tampered digest both raise). The viewer draws from that same re-derivation: `replay-viewer/hanabi_replay.nim:37-49` builds `frames` via `replayMatch`; `renderer.js:1406` reads `payload.frames`. No parallel per-tick recording exists. |
| 3 Static viewer | PASS | `coworld_manifest_template.json:15-17` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`), mkdir-p's the parent before the containment check (`:21`), builds the wasm and assembles the bundle; the shell contacts only the `?replay=` URL (`static_replay.js:69-91`). No `/client/replay` anywhere at head (F3 above; repo-wide grep clean outside test assertions of absence). |
| 4 Both name spaces | PASS | Aliases from `tableNames` (`sim.nim:126-137`) are all any prompt/observation/player frame carries (`tests/test_prompt.nim:102-116` asserts no policy name, seed, token or foreign note/banner leaks); `policyNames` ride the replay/results (`sim.nim:848, 1094-1096`); `makeNameMap` (`renderer.js:730-754`) applied at scorebug (`:982`), endcard (`:1108-1109`), feed (`:779, 872`), beat labels (`:1290`), hint pane (`:1054-1055`), seat rows via `applyNames` (`:1172`). |
| 5 Degrade-never-hang | PASS | Connect wait bounded at `playerConnectTimeoutSeconds` 180 (`server.nim:210-218`); per-request `makeRequests(batch, llmTimeoutSeconds=20)` (`llm.nim:686`, `types.nim:97`); spacing sleep ≤ 2 s (`llm.nim:642-647`); `turnDelayMs` clamped by `PacingBudgetMs div maxTurns` (`sim.nim:146-147`); pre-turn `TurnReserveSeconds = 45` against `playDeadline = start + timeout×0.6` (720 s of 1200) (`server.nim:40-44, 242, 256-276`); `endEarly` settles between turns; shutdown = 0.5 s + writes (curl POST timeout 60, `server.nim:134`) + 20 s grace + `quit(0)`. Worst turn 2+20+20 = 42 s < 45. Main loop exits only on `sim.done` or the deadline and every iteration increments `turn` toward `maxTurns ≤ 120`. `decideAll` never raises. No credentials ⇒ scripted everywhere, no network (`llm.nim:160-162, 664-668`; `tests/test_bot.nim:77-98`). |
| 6 num_agents + seat-count invariants | PASS | `num_agents: 4` in `variants[0]` (manifest:384), `variants[1]` (:409), `certification.game_config` (:432); `docker_smoke.sh:110-151` enforces all four invariants (present / positive int / cert.players len / game_config.players len) plus the independent `SMOKE_SEATS=4` cross-check (:54, :146-151), each exiting via `SEAT-COUNT FAIL:`. I grepped the head run's docker-smoke log (job 97639160150): **0** occurrences of `SEAT-COUNT FAIL`; log shows `smoke OK: seats=4 results=311B replay=8867B reason=complete` and `every player container exited 0`. |
| 7 Scripted baseline full legal episodes | PASS | `tests/test_bot.nim:36-51`: 200 seeds × 3 seat mixes to the natural end, `reason == "complete"`, and `playScripted` (:19-33) checks every proposal against `illegalReason` **and** membership in `legalMoves` before applying. Cautious loses 0 fuses over 200 seeds (:53-60); conventions beats cautious and means ≥ 12 (:62-75; head test log: `mean score: conventions 15.3, cautious 0.94`). On "tuned with a grid harness": both baselines are parameter-free ordered rule cascades (`llm.nim:179-299`) — there is no numeric knob to grid over — and the quality floor is CI-asserted rather than guessed. I read the clause as inapplicable to a parameterless baseline; the substantive requirements of the item are all verified. |
| 8 LLM reply handling | PASS | `extractJsonObject` tolerates BOM/fences/trailing prose, takes the first balanced object (`llm.nim:396-443`); one retry with the specific reason quoted (`llm.nim:671-706`, `for attempt in 0 .. 1`); then `conventions` fallback with `origin = "fallback"` (`llm.nim:707-712`), recorded on the event (`sim.nim:714`) and counted in `results.fallbacks` (`sim.nim:792-793, 855`). Tolerated/rejected shapes asserted at `tests/test_bot.nim:100-195`. |
| 9 Rune-safe truncation | PASS | `capLine` (`sim.nim:117-122`), `cleanText` (`llm.nim:387-394`), `headRunes` (`llm.nim:380-385`, all five diagnostic sites after F8's fix), prompt cap via `runeSubStr` (`server.nim:431-432`). `tests/test_bot.nim:139-155` (700 é at the caps, validateUtf8), `tests/test_replay.nim:42-88` (whole episode with capped multi-byte note+banner every turn, raw bytes re-read with strict UTF-8 + parseJson, every recorded text/banner exactly at cap). |
| 10 Manifest validates | PASS | `game.docs.readme = {"type":"text","value":…}` (manifest:272-275); `pages` = two `{id,title,content:{type:"text",value}}` entries (:276-293); `game.protocols.player` and `.global` both `{"type":"text","value":…}` (:261-269). `tests/test_viewer.nim:160-169` re-asserts. |
| 11 Legible at 360 px | PASS | `.plate-name { … min-width: 3.2em; flex: 1 1 auto; }` in the byte-identical inherited prefix (`chrome.css:280-292`); `@media (max-width: 640px) { .plate-label { display: none } … }` (:460-464); appended block adds 720/560/420 px queries (:614-623). |
| 12 Release order & scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (:153) → Certify locally (:167) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342). All three workflows present; `docker_smoke.sh` and `build_replay_viewer.sh` mode 100755; smoke steps build their binaries in the same job/run (ci.yml:177 build → :185 smoke; :249 bundle build → :317 load). `tools/ci/policies.json`: 4 policies, 2 × PLAYER_PROMPT champions + 2 × PLAYER_SCRIPTED fillers, champion #2 `hanabi-reader` carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (:15). Placeholder gate: I ran the exact grep over the five named files — no match, gate exits 0. |
| 13 Viewer executes | PASS | Run 32793042266, job 97639504479 (`wasm-viewer`, `needs: docker-smoke` ci.yml:212): step "Load the bundle in a real browser" ran and passed — `{"loaded":true,"ms":281,"clock":"TURN 8 / 24 · 3 / 25",…}`, soak 10 s advancing, scrub readouts at 0/50/100 %. No `continue-on-error` anywhere in the workflows (grep clean). Markers: `data-replay-loaded` set after the first synchronous `renderer.draw` in `attachReplay` (`renderer.js:1456-1486`); `data-replay-error` set by the shell on every failure path incl. wasm rejection (`static_replay.js:58, 119-124`), cleared on retry (:157, :132). Link flags and bootstrap from the same starter: `config.nims:38-41` `MODULARIZE=1, EXPORT_NAME=HanabiReplayModule, _hb_*` exports; `static_replay.js:161` calls the `HanabiReplayModule()` factory and `:119-128` the `_hb_*` exports — I diffed both files against bullwhip's: renames plus the documented chorus ready-poll change only. |
| 14 Chrome provenance | PASS | `client/chrome.css`: I hashed the starter's file myself — sha1 `8f0d16397cb227a427ec1112d39c180f1aef1bfd`, 11 964 bytes — and diffed: single hunk `467a468,623`, a pure append under `/* ---------- Hanabi ---------- */`; no inherited rule edited. The replay page in use, `replay-viewer/index.html`, diffed against bullwhip's `replay-viewer/index.html`: title/wordmark/clock text, two appended elements (`#tokenbar`, `#hintpane`), `fit()`→`relayout()` (which is the --band mechanism the pins require), renderer rename — all 20 starter ids present, nothing removed (`tests/test_viewer.nim:22-25, 61-77`). `client/replay.html`'s deletion is item-3 compliance (the pod path is forbidden "anywhere"), not a lookalike rewrite — the shipped page's provenance is proven above. Transport: (a) `relayout()` measures `#transport.offsetHeight`, sets `--band`/`--hudscale` on `document.documentElement`, calls `fit()` from the same function (`index.html:51-59`); feed toggle dispatches `resize` (`renderer.js:1151-1163`). (b) No `position: fixed` anywhere (grep clean); overlays live inside `#board-wrap`; `#loading { bottom: var(--band) }` (`chrome.css:587`). (c) Endcard: `.show` toggled by `updateEndscreen` on **every** `setIndex` (`renderer.js:1449-1452`); all seek paths (scrub drag `:1380-1390`, beat click `:1281-1283`, play-restart `:1420-1423`) go through `setIndex`; no keyboard handler exists. (d) Beats are `<button type="button">` with `title`+`aria-label` and onclick seek (`renderer.js:1274-1287`); all seven emitted kinds have CSS (`chrome.css:590-602`; extraction-based test `test_viewer.nim:123-137`). Zoom/minimap: bullwhip ships none and none was added (`viewpanel` greps clean; board is fixed and wholly in frame, `computeLayout` renderer.js:186-224). |
| 15 Every drawn string fits | PASS | Real-replay step: `canvas text: 52735 drawn, 0 never inside (0 draws crossed an edge), 0 ellipsized` with `--strict-text-bounds` (ci.yml:317-322). Worst-case fixture step (own ci.yml step :334-353, `--strict-text-bounds`): `canvas text: 31988 drawn, 0 never inside (24 draws crossed an edge), 1096 ellipsized` — the 24 edge-crossing draws are transient animation, the gated `never_inside` is 0, and the 1096 ellipsized draws can only be the two plate-label sites (`renderer.js:524, 528`) since the banner/learned paths cannot ellipsize (F1 fix). Banner band is reserved in the layout and sized from the server's cap measured in the drawing font (`renderer.js:169-177, 203-211`). The fixture loads the real renderer.js, hands it full-cap banners on all four seats + full 6-line learned blocks + long names, cycles 360/720/1280 px, sets the markers, and asserts its own strings are at the caps (F2 fix, `renderer_fixture.html:207-241`). |
| Simultaneous-batch rule | N/A | The game is turn-based by design (design.md:11-13, 285-294); `pendingSeats` returns exactly one seat (`sim.nim:421-427`, asserted `tests/test_bot.nim:86-88`). Sequential calls are the rule here, not a defect. |

## Fixer report audit

(I was instructed not to read r1-fixes.md; audited against the fix commits directly.)

| finding | fix commit says | I verified at head | agrees |
|---|---|---|---|
| F1 | f17e3a3: band from MaxBannerLen, never ellipsize a banner | `renderer.js:65, 169-177, 207, 602-668` — band measured from the 80-rune cap in the banner font; wrapLines/drawBanner have no ellipsis path; fixture ellipsized fell 1668 → 1096 (labels only), never_inside 0 | yes |
| F2 | 70fc1d5: fixture asserts its strings at the cap | BANNER = 80 runes, NOTE_LINE = 90 runes (measured); `assertFullLength` + full-block check, failing via `data-replay-error` (`renderer_fixture.html:207-241`) | yes |
| F3 | 78e25f3: remove the pod replay path | No replay route/page/mode anywhere in src/ or client/; new pinning test `test_viewer.nim:93-101`; test-list edit is not a loosening (see item 1) | yes |
| F8 | 724826f: rune-cut error heads | All five sites through `headRunes` (`llm.nim:414, 617, 626, 630-631, 639-640`) | yes |

## Non-blocking observations

- The catch-up path for a deadline that fires before turn 0 ends with `reason = "complete"`, not
  the design note's `"deadline"` (`server.nim:265-275`) — the note should be amended or the code
  aligned in a later pass; no checklist item is falsified.
- `decision.reject` never reaches the replay event (only stdout); phase 60 can count fallbacks
  via `results.fallbacks` but not read the rejection reasons from the replay.
- `cautious` scores a mean of 0.94 (head CI log) — it satisfies its "never misplays" contract and
  the test's assertions, but it is a very weak filler; worth knowing when reading league numbers.
- The canvas banner tag shows aliases while the feed maps them to policy names (review F7) — a
  cosmetic inconsistency between two spectator surfaces.

BLOCKING: 0
