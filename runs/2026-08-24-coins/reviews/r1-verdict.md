blocking: 0

# r1 verdict — coins
Head: 9c7fbbd51bf030982ef1b4e2ad7cb6008e0695bc   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision addendum)   Independent read written before reading fixes: yes

Reading order followed: checklist (as supplied in the brief, verbatim) → design note
(`runs/2026-08-24-coins/design.md`) → the tree at head + starter provenance diffs + CI logs
(independent notes formed) → `r1-review.md` → only then `r1-fixes.md`, used solely to audit
that claimed commits exist (verified with `git log` in `/workspace/cogame-coins`).

CI evidence, checked myself: `gh run list -R Metta-AI/cogame-coins --branch main -w ci.yml`
→ run **32796206226**, `headSha 9c7fbbd51bf030982ef1b4e2ad7cb6008e0695bc`, conclusion
**success**; jobs `test`, `docker-smoke`, `wasm-viewer` all `success`, every step in all
three jobs `success`, no `continue-on-error` anywhere in the three workflows (grep exit 1).

## Standing blocking findings

None. The reviewer's one blocking finding is fixed at head (below), and my own checklist
pass found no item that fails at head.

## Refuted

### B1 — "viewer draws LLM `say` in an unbounded row; no worst-case renderer fixture" → REFUTED (fixed at head)
- The finding was true at the reviewed sha `3bc93c3`. At head it is false:
  - `client/replay_broadcast.html:2043` region — the remark now lands in its own `.cn-say`
    span inside a `.cn-order` row with a band sized from the 48-rune cap
    (`max-width: 100%`, wrap not ellipsis), inside `#killfeed`'s existing 4-row reserve.
  - `tools/ci/text_fixture.js` (449 lines) + `tools/ci/build_text_fixture.sh` (both
    committed mode 100755) build the REAL page — the same three splices
    `Dockerfile.replay-viewer` does — with the socket stubbed, push four full-cap 48-rune
    remarks (`var CAP = 48; // MaxSayLen — src/coins/sim_types.nim:61`) on every seat at
    six stage widths (`SIZES = [[360, 640], [414, 736], [620, 480], [760, 428], [1024, 768], …]`)
    in Latin/CJK/sentence shapes, assert per line box that "(a) the remark is still FULL
    LENGTH", that every line is inside the reserved band, band inside the stage and clear
    of the scorebug band, and mirror every measured line onto a band-sized canvas so
    `--strict-text-bounds` gates real text.
  - `.github/workflows/ci.yml:358-392` — its own step `Render the worst-case remark
    fixture`, `node tools/ci/viewer_smoke.mjs --bundle dist/text-fixture … --strict-text-bounds`.
  - Executed and green at head: run 32796206226, `wasm-viewer` job log:
    `canvas text: 184 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`
    and `fixture canvas_text: {"total":184,"never_inside":0,"outside":0,"ellipsized":0}`.
    `total` is 184, not 0, so the check covered something; `never_inside == 0`.
- Introduced by commit `0c74d0d` ("r1-B1: a reserved band for the LLM remark, and a
  worst-case renderer fixture in CI"), verified in `git log`.

No other reviewer finding was blocking; none of the non-blocking N findings ties to a
checklist item as a failure at head (see audit table).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 32796206226 `success` at head sha, all jobs/steps green. `git log -p -- tests/`: after the initial commit, `2e3c462` is the only commit with deletions in tests (20+/18−, read hunk by hunk: rename `sim`→`episode`, `##`→`#` comments, `sort(x)` call form, unused imports, and one spawn-cadence bound `0 ..< interval`→`0 .. interval` matching the sim's defined first-spawn tick with the assertion still exact `coins.len == 1`, tests/test_sim.nim:234-238). All later test commits (`0c74d0d a5c8bd0 ba29048 6476b35 95adfcf 9c7fbbd`) are pure additions (checked: zero `-` lines in tests/). No skip/xfail/tolerance anywhere. Noted, outside tests/: `16ec1d3` removed an optimality gate from `tools/tune_baseline.nim` that `419d50f` had introduced 14 min earlier in this same round (the one red run, 32795402854); the deleted assertion ("within one coin of the grid's best") asserts a property neither the note nor any checklist item claims, the harness still gates the note's two claims (beats sucker payoff: `check(row.vsGreedy > sucker)`, punishes: `:199`, truces: `:195`), and the removal is declared in the commit message and the fixes note. Not a loosened test under item 1's rule (scope is `tests/`), and honestly declared. |
| 2 replay re-derivation, test asserts | PASS | Coins records state frames, not events (`src/coins/replays.nim`); the recorded frames ARE the per-tick state, asserted element by element: `tests/test_replay.nim:178-217` (commit `a5c8bd0`) walks all 320 frames comparing `t,c,k,sc,th` against `episode.frames[i]`, asserts frame i is tick i, and walks `ReplayPlayer.seek(i).frame()` over the same range. The viewer derives its display from the same path: `replay-viewer/coins_replay.nim:16` imports `coins/replays`, `coinsLoadReplay` → `parseReplayBytes`/`initReplayPlayer` → `buildBoardPacket` + `buildStateJson` — the same procs the live server and the test use. No parallel recording exists. |
| 3 static viewer | PASS | `coworld_manifest_template.json:27-29` `"replay_viewer": {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755 (`git ls-files -s`), invoked by path at `ci.yml:261` after a `test -x` gate (`ci.yml:237-248`); the bundle's only network fetch is the replay URL in `static_replay_worker.js`. `/client/replay` appears only in `client/broadcast_core.js:196` — a path-mapping table byte-identical to the starter's own line 196, never driven by the static adapter — and in assertion text (`tests/test_manifest.nim:108-109` asserts the string is absent from the manifest). No pod viewer declared anywhere. |
| 4 both name spaces | PASS | `src/coins/sim.nim:494,522` — observation carries `alias`/`them.alias` only, no policy name/prompt/account; `src/coins/sim.nim:548-551` — `results.names` are policyNames, `aliases` separate; `src/coins/broadcast.nim:46-48` roster carries `name` (alias) and `pol` (policy) separately. Head smoke log scorebug renders `COINS-PLAYER` / `COINS-RECIPROCATOR`. |
| 5 degrade-never-hang | PASS | Connect wait bounded 180 s (`server.nim:207-215`), register wait ≤3 s (`:217-226`), LLM batch `makeRequests(batch, client.timeoutSeconds)` 12 s (`llm.nim:405`), one retry (`:382 for attempt in 0 .. 1`), beat loop bounded by `maxBeats` (`sim.nim:closeBeat`), deadline `0.6 × episodeTimeoutSeconds = 720 s` checked at every beat close AND reserving the next beat's worst case: `sim.nim:656-658` `if now() + sim.config.worstCaseBeatSeconds().float >= sim.config.playDeadlineSeconds()` (commit `6476b35`, tested `tests/test_sim.nim:379+`). `decideAll` cannot raise out (outer `try` wraps batch build + `makeRequests`, `llm.nim:394-424`, commit `e8518e6`); no worker thread reads mutating sim state (`server.nim:109-146` publishes under `stateLock` from the episode thread; commit `bfedbb1`). `sim_config.nim:114-120` raises at validation if `maxBeats × 2 × llmTimeoutSeconds > playDeadlineSeconds` — 24 × 24 = 576 < 720. |
| 6 num_agents | PASS | `num_agents: 2` in all five variants (manifest :398, :424, :450, :476, :502) and `certification.game_config:519`; `certification.players` len 2 (:538-545); `game_config.players` len 2 (:529-536). `tools/ci/docker_smoke.sh:110-151` implements all four invariants plus the `SMOKE_SEATS` cross-check (`:146-151`), every failure prefixed `SEAT-COUNT FAIL:`, executed before any container starts (`:93`, launch at `:191+`). Grepped the full head run log: **zero occurrences of `SEAT-COUNT FAIL`**; log shows `smoke OK: seats=2 results=340B replay=38284B reason=beat_cap`. |
| 7 scripted baseline full episodes + grid | PASS | `tests/test_baseline.nim:118-171` — 4 baselines × 5 variants × 8 seeds = 160 episodes via `runEpisode` to natural end; every order intent in the legal five (`:137-138`), one order per seat per beat (`:141`), interior/no-share/score-identity/no-double-collection (`:144-159`), honest thefts == 0 (`:160-163`); legal reason asserted in `tests/test_replay.nim:165-170` (membership in the four legal reasons). Grid harness: `tools/tune_baseline.nim` sweeps 3×5×3 = 45 points × 4 opponents × 8 seeds = 1440 episodes, ranks and gates the note's criteria; run in CI (`ci.yml:161-162`, step `Tune the reciprocator on a grid`, green at head). |
| 8 LLM reply handling | PASS | `llm.nim:246-257` `extractJsonObject` = `find('{')`…`rfind('}')` (fences/preamble/trailing prose tolerated, `tests/test_llm.nim:34-51`); retry once with hint (`llm.nim:382, :401-402, RetryHint :237-240`); fallback = reciprocator move recorded `source: osFallback` → `"fallback"` on the order event (`llm.nim:426-429`, `tests/test_llm.nim:82-93`); 401/403 disables client (`:307-310`); 429 retried (`:311-314`). |
| 9 rune-safe truncation | PASS | `sim_types.nim:184-199` `cleanText` = strip → `runeSubStr(0, limit-1) & "…"`; prompts rune-capped `server.nim:419-420` (`runeSubStr(0, MaxPromptRunes)`), policy label `:439-440`. Test at the cap with multi-byte runes: `tests/test_replay.nim:31-57` (2- and 3-byte runes at and past both caps, `validateUtf8 == -1`), `:120-160` (recorded strings through a real episode), `:85-86` (whole replay strict UTF-8). Error strings are byte-sliced but reach only `echo`, never the replay. |
| 10 manifest docs + protocols | PASS | `coworld_manifest_template.json:324-347` — `docs.readme {type:text,value}` + `pages[]` of `{id,title,content{type:text,value}}` (rules.md, policies.md); `:348-357` — `protocols.player` and `protocols.global`, both `{type:text,value}` objects. |
| 11 legible at 360 px | PASS | `client/replay_broadcast.html:1800-1815` — `.plate .plate-name { … flex: 1 1 auto; min-width: 3.2em; }`; `:2076-2081` — `@media (max-width: 640px)` hides `.cn-restraint`, `#cn-recip .cn-nums`, `.cn-rcap`; `.tiny` compact forms `:2057-2071`; `relayout()` toggles `.tiny` at `boardW <= 620` (`:1760`, starter's line). |
| 12 release order + scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify locally (:167) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342). Three workflows present. `docker_smoke.sh` 100755. `policies.json`: 4 distinct policies, 2 × `PLAYER_PROMPT` champions + 2 scripted fillers; champion #2 `coins-ledger` carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (:17). Gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files finds nothing (grep exit 1 = zero matches). ci.yml's docker-smoke builds the image in the same job before the smoke (`ci.yml:188-197`). |
| 13 viewer executes | PASS | (i) `wasm-viewer` green at head with `needs: docker-smoke` (`ci.yml:224`); step `Load the bundle in a real browser` ran and passed (run 32796206226): `{"loaded":true,"ms":338,…}`, three distinct scrub readouts (`BEAT 13 / 16 …` / `BEAT 9 / 16 …` / `FINAL 16 BEATS · BEAT_CAP`), `soak: 10s of playback kept advancing ("0 / 319" -> "192 / 319" -> "240 / 319")`; no `continue-on-error`. (ii) `static_replay.js:155` sets `data-replay-loaded="true"` on the worker's first `frame` report; `:31-32` sets `data-replay-error` in `showFailure()` before `#status` renders. (iii) Same starter both sides: `replay-viewer/config.nims` diff vs starter = name/export renames + `_ctf_mismatch_tick` dropped only — **no MODULARIZE, no EXPORT_NAME**; `static_replay_worker.js:162` bootstraps with `Module.onRuntimeInitialized` — the matched non-MODULARIZE pair, structurally identical to the starter's. `loaded: true` is the executed evidence. |
| 14 chrome provenance | PASS | `cmp` — `client/chrome_common.js` and `client/broadcast_core.js` byte-identical to the starter's. `client/replay_broadcast.html` diffed whole against the starter (2518 vs 4165 lines): the CSS above the banner (`:1779` "COINS additions to the inherited coworld-ctf chrome") contains zero added rules; the only CSS deletions are the note's named removals (#povBadge+#fpv block, #mmwarn, `body[data-noviewpanel] #viewpanel`); the large JS deletions are CTF game code (FPV raycaster, pov, kill/steal/capture handlers, lives pips, zoom/pan key wiring, CTF endcard) plus the four removed element families — all 20 removed ids absent from markup and CSS (`tests/test_viewer.nim` asserts per id). #viewpanel removed entirely (markup, CSS, wiring: `onFirstFrame` now only `core.setViewportFit()`, `:1491-1494`) — legitimate, the arena is fixed 9×9/504 px. Transport rules: (a) `relayout()` `:1724-1769` measures `#transport.offsetHeight` and sets `--band`/`--topband`/`--hudscale` on `document.documentElement` (`:1759-1765`); (b) game overlays `#cn-recip`/`#cn-thefts` anchored to `--topband`, nothing fixed in the band; (c) `#endcard { top: var(--topband); bottom: var(--band, 0px) }` (`:722-723`), shown via `classList.add('on')` (`:2443`) against `#endcard.on` (`:734`), dismissed by the starter's own `else { $('endcard').classList.remove('on') }` (`:1595`) on every non-gameover frame — every seek path (scrub, beat button → `CH.seek`, back/forward, keyboard) lands there; (d) markers are `<button type="button" class="beat-marker <kind>">` with `aria-label`+`title`+click→`CH.seek(tick)` (`:2293-2314`), CSS for every emitted kind: `.beat-marker.theft :1961`, `.truce :1966`, `.leadchange :1971`, `.over :1976`; the kind set is closed at those four (`sim.nim:600-621` beatsTimeline). Spoilers gate reaches the buttons (`cnApplySpoilers`, `:2339-2361`, commit `9c7fbbd`). |
| 15 drawn text fits | PASS | `ci.yml:330-335` smoke carries `--strict-text-bounds`; head run: main smoke `canvas text: 0 drawn, 0 never inside` (the board draws no canvas text — total 0 there proves nothing, which is exactly why the fixture exists) and the fixture step reports `canvas_text: {"total":184,"never_inside":0,"outside":0,"ellipsized":0}` — `never_inside == 0` with real coverage. The fixture (`tools/ci/text_fixture.js`) asserts its own strings are full length (exact string compare per row), reserves the band from the 48-rune server cap in the drawn font, runs at six widths from 360 px, waits the entrance animation to settle, and is driven by the byte-identical-to-template `viewer_smoke.mjs` (`diff` clean) in its own ci.yml step (`Render the worst-case remark fixture`, :358-392). Fixed arena → strict flag correctly kept. |
| addendum: one parallel batch | PASS | `llm.nim:394-405` — a single `RequestBatch` filled with every open seat, one `client.curl.makeRequests(batch, timeout)` per attempt; no per-seat request loop exists. `tests/test_llm.nim:134-151` asserts one batch per beat and the `minBeatSeconds` floor. |

## Fixer report audit

Read only after the pass above was written. Every commit named in the table exists at head
(`git log`); dispositions checked against the tree:

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed, `0c74d0d` | fixture + reserved band + CI step present; head run fixture line `total 184 / never_inside 0`; fixture asserts full-length strings | yes |
| N1 | fixed, `a5c8bd0` | element-by-element frame assertions + playhead walk in test_replay.nim | yes |
| N2/N3/N4/N5 | no change | confirmed unchanged; none is a checklist item (N2: derivation rule holds and is tested; N4 is stricter than the note; N5 is the conservative direction for item 5) | yes |
| N6 | fixed, `6476b35` | `sim.nim:656-658` reserves `worstCaseBeatSeconds()` against the deadline; test added | yes |
| N7 | fixed, `e8518e6` | outer `try` wraps batch build and `makeRequests` (`llm.nim:394-424`); `decideAll` cannot raise | yes |
| N8 | fixed, `bfedbb1` | worker threads read only the published `shared.lastFrame`/`lastChrome` snapshot under `stateLock`; episode thread is the sole sim reader | yes |
| N9 | fixed, `ba29048` | `endEpisode` records the opening frame for a zero-tick episode (`sim.nim:439-445`); stillborn-replay test added (`test_replay.nim:220+`) | yes |
| N10 | no change | confirmed: no stubbed transport; item 8 requires behaviour, not a test — behaviour verified in code | yes |
| N11 | partly fixed, `95adfcf` | absolute floors R ≥ 10 and P < 5 added; per-seed (c)/(d) printed not gated — a note-vs-test gap, not a checklist item | yes |
| N12 | fixed, `419d50f`+`16ec1d3` | grid harness present, run in CI, green at head; the optimality gate removed in `16ec1d3` was `419d50f`'s own same-round addition, declared openly (see item 1 note) | yes |
| N13/N14/N17/N19 | no change | confirmed unchanged; none ties to a checklist item | yes |
| N15 | fixed, `9c7fbbd` | `cnApplySpoilers` + `cnWireSpoilers` apply the chrome's spoilers rule to the game-block buttons | yes |
| N16 | fixed, `c72dbdf` | head smoke clock reads `TICK 240 OF 320` (was `OF 319`) | yes |
| N18 | fixed, `cda7b61` | `handleRegister` logs a misspelled `PLAYER_SCRIPTED` naming the legal set (`server.nim:426-434`) | yes |

## Non-blocking observations

- The fixer's design question 1 stands and is worth a next-round look: the shipped
  reciprocator is rank 29/45 on its own grid's vs-greed measure and loses to `honest`
  against `greedy` on 5 of 8 seeds (aggregate margin +0.375). The note's test-spec (d)
  "strictly greater on the same seed" is not a property the shipped point has. This does
  not falsify checklist item 7 (the grid harness exists, runs in CI, and the choice is
  documented), but the design note at `design.md:604` overstates what the code holds.
- `design.md` vs code discrepancies N2 (service name `coins` vs the note's `game`), N3
  (two `blocked` events per tick), N13 (no reciprocity strip on the endcard), N14
  (`notes` recorded, never drawn), N19 (no env read for the deadline) remain — all
  note-fidelity items, none named by the checklist.
- `viewer_smoke.mjs`'s `feed_lines` counter does not match Coins' `#killfeed` id, so it
  reports 0 even with rows on screen; the template must stay byte-identical, and the
  fixture prints its own row counts. Cosmetic.
- `docker_smoke.sh`'s third/fourth seat-count invariants are guarded by
  `if cert_players and …` / `if fixture_players and …` — an empty list would skip them.
  Against this manifest both lists are populated and the checks fire; noting only for
  template hygiene.

BLOCKING: 0
