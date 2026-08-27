blocking: 0

# r1 verdict — board-gauntlet
Head: 2390463b97d0bf07e93c95726a51873498404930   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST (items 1–15)   Independent read written before reading fixes: yes

Repo read at `/workspace/judge-board-gauntlet` (fresh clone, checked out at the head sha).
Design note: `runs/2026-08-27-board-gauntlet/design.md` — verified byte-identical to the in-repo
`docs/plans/2026-08-27-board-gauntlet-design.md` at head (`diff` empty).
Starter for provenance: `/workspace/starters/cogame-babel` @ d55d999.
CI evidence: run **33038495877** on `main` at the head sha, conclusion `success`
(jobs: `test` 5m54s ✓, `docker-smoke` 1m10s ✓ job 98407697517, `wasm-viewer` 2m4s ✓ job 98407897662).
The review (`r1-review.md`) was written at the earlier sha ad8054c3; head is 20 commits later.
I formed my own read of the tree and the CI logs before opening the review, and read
`r1-fixes.md` only afterwards, to audit its claims.

## Standing blocking findings

None. Both of the reviewer's blocking findings were true at ad8054c3 and are **fixed at head**
(not refuted — see below); my independent checklist pass found no new blocking finding.

## Reviewer findings — disposition

### B1 — say band ellipsized full-cap remarks → FIXED AT HEAD (commit bde1d823)
- The finding was correct at ad8054c3 (run 33035395418 reported `ellipsized: 7106`, samples all remarks).
- At head, `client/renderer.js` has **no** `ellipsize` call on the say path. `layoutOf`
  (renderer.js:129-141) reserves the band from the cap: `sayRowsOf(ctx, sayFont, sayWidth, state)`
  wraps a worst-case ruler — `CAP_RULER` = 24 + `MAX_SAY_LEN` full-width `日` runes plus quotes
  (renderer.js:494-499) — and `sayBand = sayRows * 2 * lineH + 12·scale` (renderer.js:138).
  `drawSayBand` (renderer.js:566-586) wraps with `wrapRunes` (greedy, breaks between runes when
  no space exists, drops nothing, renderer.js:503-524); the file's only occurrence of the word
  "ellipsize" is the comment at renderer.js:482 saying it never does.
- CI at head: fixture step logs `canvas text: 10492 drawn, 0 never inside the canvas (0 draws
  crossed an edge), 0 ellipsized (--strict-text-bounds)`; bundle step logs `5592 drawn, 0 never
  inside …, 0 ellipsized`. Item 15 is now satisfied on both paths.

### B2 — seventh chrome edit unrecorded in the design note → FIXED AT HEAD (commit 0ab2f09b)
- The edit (`client/chrome_common.js:263` — `// BOARD-GAUNTLET EDIT 7 (starter lines 994-999)`,
  the endcard verdict "… WINS"/"DRAWN" and the PLY count) was real and unrecorded at ad8054c3.
- At head the design note's chrome-provenance table has **seven** rows including row 7
  (design.md:966-974, "Exactly seven copied lines/regions are edited"), and the file header
  (`chrome_common.js:19`) says "Exactly seven". No copied byte changed;
  `tools/ci/chrome_scope_check.mjs` runs green (`{"ok":true,…,"copied_regions":10}` — I ran it
  locally at head). Item 14's register requirement is met.

## Refuted

### N19 — a `/client/replay` HTTP route exists on the game container → REFUTED (does not falsify item 3)
- Evidence: `src/gauntlet/server.nim:505` at head —
  `result.get("/client/replay", htmlHandler("replay_broadcast.html"))` — is the starter's own
  route, byte-for-byte in shape: `/workspace/starters/cogame-babel/src/babel/server.nim:502` is
  `result.get("/client/replay", htmlHandler("replay.html"))`. Item 3's operative requirements are
  all met: `coworld_manifest_template.json` declares `"replay_viewer": {"bundle":
  "static-replay-viewer"}` **inside** `game` (verified by JSON parse), `tools/build_replay_viewer.sh`
  exists at mode 100755 (`git ls-files -s` → `100755`), and the static viewer contacts nothing but
  the `?replay=<url>` fetch (static_replay.js:67-84, AbortController-bounded) plus its own relative
  assets. No pod path serves hosted replays; the route is the live broadcast page the design note
  declares (design.md:751, design.md:998). Reading item 3's phrase as banning the starter's own
  live-mode route would put items 3 and 14 (starter chrome, not a lookalike) in direct conflict.
  The reviewer flagged this as a literal text match and argued against it; I concur and dismiss it.

The reviewer's remaining findings were advisory (N1–N18, N20). I verified each against the head
tree; none falsifies a checklist item. Dispositions in the audit table below.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 33038495877, conclusion `success`, headSha 2390463b (from `gh run list -R Metta-AI/cogame-board-gauntlet --branch main -w ci.yml`). `git log -p --since="2026-08-27T00:00Z" -- tests/` shows exactly one commit touching tests/ (cee5659, the initial add, 2026-08-27); no assertion deleted, no tolerance widened, no skip/xfail (grep over tests/ empty), no test file removed. The 25 % Connect-Four floor in test_bot.nim was in the original hunk, never loosened, and is a recorded design-note exception (design.md:443-449). |
| 2 Replay re-derivation | PASS | `replayMatch` (sim.nim:544-598) re-runs `initSim` + `applyMove` per recorded move, applies `evEnd` through the same `settle` (sim.nim:590-597), and raises on any mkind/capture/win-seat/how/path/reason/ending mismatch. Frame-by-frame equality asserted by `checkReDerives` (test_replay.nim:112-133) across all endings incl. deadline/wall-clock (test_replay.nim:138-267); doctored recordings raise (test_replay.nim:298). Viewer derives from that same re-derivation: `gauntlet_replay.nim` runs `replayMatch` and emits `states[i]`; renderer draws only `states` (`currentState()`, renderer.js:903-905). Recorded exception `complete/no-moves` (unreachable from the standard opening) is covered from a hand-built position and recorded in the note (design.md:1325-1332); it does not falsify "a test asserts it". |
| 3 Static viewer | PASS | `"replay_viewer": {"bundle": "static-replay-viewer"}` inside `game` (manifest, parsed); `tools/build_replay_viewer.sh` present, git mode 100755, asserted+invoked by path in ci.yml; viewer fetches only `?replay=<url>` (static_replay.js:67-84). `/client/replay` is the starter's live-broadcast route, not a pod replay path — see N19 refutation. |
| 4 Both name spaces | PASS | Aliases seeded from `CogNames` via `tableNames` (sim.nim:35-46); prompts and welcome/state/final frames carry `sim.names[...]` only (llm.nim:461-462,485-486; server.nim:420,108,199-211); no `config.players[].name` reaches a seat (grepped). Viewer maps aliases→policy names via copied `makeNameMap`/`isBaselineFiller`, called with `payload.policyNames` (renderer.js:878); `results.names` are policy names (sim.nim:384). |
| 5 Degrade-never-hang | PASS | Connect wait bounded by `playerConnectTimeoutSeconds` (server.nim:241-249); LLM call bounded by curly `timeoutSeconds` = 30 (llm.nim:551); one retry then scripted fallback, `decide` never raises (llm.nim:604-628); spacing sleep ≤ 4 s, LLM plies only (server.nim:313-318); guard refuses to open a ply unless `now + worstPlySeconds ≤ playDeadline` with `worstPlySeconds = 2·30 + 2 + 4 + 0.25 = 66.25` **including** the post-guard sleeps (server.nim:282-283,299-305) and `playDeadline = gameStart + 0.6·1200 = 720 s` (server.nim:38,270-272); loop otherwise strictly advances `plies` toward `maxPlies ≤ 200` (sim.nim:292-305; types.nim:303). No unbounded loop, no blocking read in the game loop; shutdown grace 20 s then `quit(0)` (server.nim:230-232). |
| 6 num_agents | PASS | `num_agents: 2` in all five variants' `game_config` and in `certification.game_config`, equal to `len(players)` everywhere, never at variant top level (manifest parsed; also asserted by test_manifest.nim). docker_smoke.sh enforces the four invariants with `SEAT-COUNT FAIL` prefixes before any container starts (docker_smoke.sh:106-151); `SMOKE_SEATS` substituted 2, agreeing with the fixture. Docker-smoke log (job 98407697517): grep `SEAT-COUNT FAIL` → **0 matches**; `smoke OK: seats=2 … reason=complete`. |
| 7 Scripted baseline full episodes | PASS | test_bot.nim:37-71: 200 seeded episodes × 4 games × 2 baselines, every move `in legal`, ≤ 12 chars, episodes terminate, no say/notes. test_bot.nim:259-279 runs the cert fixture all-scripted to natural end and asserts `sim.reason == "complete"` and `< 50 s`. Docker-smoke corroborates end-to-end (`reason=complete`, players exit 0). Grid-harness clause: the baselines have **no tunable parameters** — `tacticianMove`/`hustlerMove` (llm.nim:154-184, 261-287) are pure one-ply argmax over `legalMoves`/`applyProbe`/`standing` with fixed tie-breaks; the only constants are the four `standing` definitions fixed verbatim by the note. I judge the note's recorded claim (design.md:435-441) valid on its merits: there is nothing to sweep, and the substitute tests (beats uniform-random, ≥25/30 % disagreement, never walks past a win) establish what a harness would. |
| 8 LLM reply handling | PASS | Tolerant parse first `{`…last `}` (llm.nim:518-526); exactly one retry (`for attempt in 0 .. 1`) with the legal set appended (llm.nim:604-609); fallback to tactician with `fellBack: true` (llm.nim:627-628); recorded for phase 60 as `results.fallbacks[]`/`illegalReplies[]` (sim.nim:390-391,408-409, both in results_schema) and per-event `fellBack` (sim.nim:272), plus a greppable `falling back` stdout line (llm.nim:625). |
| 9 Rune-safe truncation | PASS | One shared `cleanText` cuts on rune boundaries (`runeSubStr(0, cap-1) & "…"`, types.nim:121-131), applied to say/notes (llm.nim:584-585), move (sim.nim:184), prompt (server.nim:469), and log-bound error text (server.nim:334,489; llm.nim:622). test_replay.nim:354-400 feeds multi-byte input at exactly the cap and asserts `runeLen == cap`, `validateUtf8(bytes) == -1` on the whole serialised replay, and a strict-parse round trip. |
| 10 Manifest validates | PASS | `game.docs` = `{readme:{type:"text",value}, pages:[{id:"rules.md",title,content:{type:"text",value}}]}`; `game.protocols` carries both `player` and `global` as `{type:"text",value}` objects (manifest parsed directly; also test_manifest.nim). |
| 11 Viewer legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` at chrome.css:484-486; `.plate-label { display: none; }` under `@media (max-width: 640px)` at chrome.css:599-600 (duplicated as `body.narrow-640` at :619 so the fixture exercises it). |
| 12 Release order and scaffold | PASS | coworld-release.yml: build (:159) → certify (:173) → upload-policies (:212) → upload-coworld (:310) → secret put (:348) — verified byte-identical to the substituted template (`diff` empty), as is coworld-submit.yml; ci.yml's smoke steps build the image in the same run (`docker build … :ci` then `docker_smoke.sh "${IMAGE}:ci"`). All three workflows present. docker_smoke.sh present, git mode 100755. policies.json: 4 distinct policies — 2 `PLAYER_PROMPT` champions + 2 scripted fillers; champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. Placeholder gate: I ran `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files — **no match** (the gate's passing state: no placeholder survives); the documented runtime residues remain as expected. |
| 13 Viewer executes | PASS | wasm-viewer green at head sha in run 33038495877 (job 98407897662); `needs: docker-smoke` in ci.yml; the load step ran (log: `{"loaded":true,"ms":297,…}`, three differing scrub readouts PLY 11 → PLY 23 → PLY 44 FINAL, 10 s soak advancing) against `dist/smoke/replay.json` downloaded from the docker-smoke artifact; no `continue-on-error`, no gating `if:` (only `always()` on evidence uploads). `data-replay-loaded="true"` set from the first drawn frame inside the rAF loop after `renderer.draw` (renderer.js:965-969); `data-replay-error` set/cleared in static_replay.js:56,107,136. Link flags and bootstrap agree and come from the same starter: `-s MODULARIZE=1 -s EXPORT_NAME=GauntletReplayModule` (config.nims) and `GauntletReplayModule().catch(…)` (static_replay.js:140); exported `_bg_*` functions match gauntlet_replay.nim's exportc names; no `onRuntimeInitialized` anywhere. |
| 14 Chrome is the starter's | PASS | `head -443 client/chrome.css` byte-identical to babel's 443-line file; everything else appended under the banner. chrome_common.js: I verified the ten copied regions line-by-line against starter renderer.js @ d55d999 — regions 23, 85-87, 101-124, 680-733, 735-744, 1029-1048 are 100 % verbatim; the deviating lines in 790-863, 963-970, 972-1027, 1142-1222 are exactly the seven named edits, all now in the note's table (design.md:966-974). replay_broadcast.html is babel's replay.html + title/wordmark/#clock text + script list + appended banner block; nothing removed (superset, 91 vs 74 lines). Transport: `relayout()` sets `--band`/`--hudscale` on `document.documentElement` (chrome_common.js:416-425, bound to load/resize/feed-toggle); nothing `position: fixed` anywhere in client//replay-viewer//fixture (grep empty); the endcard (this lineage's `#endscreen`) keeps `bottom: var(--band, 0px)` (chrome.css:582-585), shows via the starter's `.show` class, and **every** seek dismisses it — `setIndex` unconditionally calls `updateEndscreen(…, index >= events.length && …)` (renderer.js:920-924) and all seeks (scrub, beats, play) route through `setIndex`. Beats are labelled `<button>`s (`markPlyBeat`, chrome_common.js:462-486) with CSS for every emitted kind — `.beat-start/.beat-move/.beat-win/.beat-end` + `.capture`/`.wall` modifiers (chrome.css:571-576), asserted by chrome_scope_check.mjs (green). Zoom correctly absent: no `#viewpanel`, and the largest board (9×9) draws whole in frame. |
| 15 Every drawn string fits | PASS | Bundle step: `canvas text: 5592 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)` — `never_inside == 0` with the flag on, on a fixed arena. The viewer draws LLM-authored text (`say`), and the repo ships the required worst-case fixture: `tools/ci/renderer_fixture.html` runs the real shipped renderer.js/chrome_common.js/chrome.css as the top-level document, feeds all four games a full-cap 80-rune multi-byte `say` on both seats at 360/640/1280 px, **asserts its own remarks are exactly 80 runes before drawing** (renderer_fixture.html:102-110, failing via `data-replay-error` + throw), and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own ci.yml step ("Renderer fixture at 360 / 640 / 1280 px"). That step's canvas_text line at head: `canvas text: 10492 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. Remarks wrap (never ellipsized) in a band reserved from the server-enforced cap measured in the render font (renderer.js:488-586). |

Simultaneous-batch rule: N/A by design — strictly alternating single-seat plies; the code
documents the batch requirement for any future simultaneous variant (server.nim:18-21).

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, bde1d823, band sized from cap + wrap, 0 ellipsized in CI | renderer.js:488-586 wraps via CAP_RULER/wrapRunes, no ellipsize call; head CI logs 0 ellipsized on both steps | yes |
| B2 | note fixed, 0ab2f09b, table row 7 + "seven" | design.md:966-974 has 7 rows; chrome_common.js:19 says "seven"; scope check green | yes |
| N1 | fixture asserts 80-rune remarks, bdd98253 | renderer_fixture.html:102-110 asserts and sets data-replay-error + throws | yes |
| N2 | note records 25 % CF floor; test untouched | design.md:443-449; git log -- tests/ shows one commit only | yes |
| N3 | note records no-moves exception | design.md:1325-1332 | yes |
| N4 | note lists regions 23, 85-87 | design.md:956-958; both regions byte-identical to starter (verified) | yes |
| N5 | note's say-band bullet matches the canvas band | design.md:1059-1067 | yes |
| N6 | note records main-frame fixture | design.md:1400-1405 | yes |
| N7 | note records duplicated narrow rules | design.md:946-951; both copies below banner, declaration-identical | yes |
| N8 | note drops --timeout-seconds claim | design.md:496-500; release workflow = template verbatim (diff empty) | yes |
| N9 | note credits art scripts | design.md:1093-1100 | yes |
| N10 | note lists 3 appended helpers | design.md:976-980 | yes |
| N11 | note lists #clock placeholder change | design.md:1005-1010 | yes |
| N12 | note states token rule | design.md:854-859; connect_four.nim:157-183 implements it | yes |
| N13 | worstPlySeconds now 66.25 incl. spacing + delay | server.nim:282-283 (`+ plySpacing.float + config.turnDelayMs.float / 1000.0`); note updated (design.md:253-254, 487-492) | yes |
| N14 | note records output_config effort | design.md:463-466; llm.nim:544-547 guard matches | yes |
| N15 | two echo sites now capped | server.nim:334, :489 use `cleanText(error.msg, MaxErrorLen)` | yes |
| N16 | note phrases no-moves line from the victor | design.md:1074-1076; renderer feed line matches | yes |
| N17 | headerText measures body.clientWidth | renderer.js:736-738 | yes |
| N18 | one replay driver at a time (generation) | renderer.js:864-870, 878-880, 927 (stale loop returns) | yes |
| N19 | refuted, no change | I independently reached the same ruling — see Refuted above | yes |
| N20 | note records no-grid-harness reason | design.md:435-441; baselines verifiably parameter-free | yes |

No test was weakened to make anything pass: `git diff ad8054c3..2390463b -- tests/` is empty
(verified), and CI at head runs every tests/*.nim in both debug and release (`NIM_TESTS` unset).

## Non-blocking observations

- `sayString` (renderer.js:546) trims the display string with `String.slice(0, MAX_SAY_LEN)`,
  which counts UTF-16 code units, not runes. The server already caps `say` at 80 runes, so this
  is a no-op for BMP text, but a remark containing astral-plane runes (emoji) could be visually
  shortened and could split a surrogate pair in the *drawn* text. The replay bytes are unaffected
  (item 9 is server-side and tested); suggest `Array.from(text).slice(0, N).join("")` if touched.
- The player binary's receive loop (`gauntlet_player.nim:63-90`) blocks on `receiveMessage()`
  with no timeout of its own. It exits 0 on the final frame and on any close/raise (the raid
  0.1.4 fix), and the platform tears player pods down after results.json, so it cannot hang the
  episode — the starter's own shape — but it is the one wait in the tree without an explicit
  in-process bound.
- The `@media` and `body.narrow-*` rule copies in chrome.css can drift silently; the fixer noted
  the same and deferred a scope-check assertion. Advisory.
- The fixture's soak line reads `kept advancing (null -> null -> null)`; the pass signal is the
  harness's own "kept advancing" verdict (viewer_smoke.mjs is template-verbatim — diff empty),
  so this is cosmetic, but the null probes mean the progress markers it prints are not populated
  for this page.

## Could not verify (and why it does not block)

Nothing on the checklist. All fifteen items were verifiable from the tree, the manifest, the
starter diff, and the cited CI run at the head sha. The reviewer's three residual
could-not-determines (no-moves reachability proof, hex deque bounds, DOM feed clipping) are not
checklist items; each is covered by a recorded exception, a debug-build sweep that would raise
on violation, or a display-none rule, respectively.

BLOCKING: 0
