blocking: 0

# r1 verdict — garble

Head: remote `de841a155af848bbe5c470f59ad44e6434476f8b` = local `e414ea1` (verified: `git fetch origin main && git diff HEAD origin/main --stat` empty)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** — I read the checklist, the design note, the full tree (sim/wire/llm/server/player, all four viewer files, chrome, manifest, workflows, smoke scripts, tests), the CI logs of run 32706190772 and the fork-point test history, and formed the per-item verdicts below **before** opening `r1-review.md`, and only opened `r1-fixes.md` after completing the refutation pass. Not contaminated.

The review was written against `d76e12c3`; twenty-one fix commits (`1dee5f4`…`e414ea1`) landed after it. Every finding was re-checked **at the current head**, not at the review's sha.

## Standing blocking findings

None. Zero findings — the reviewer's and my own — stand against a checklist item at `de841a15`.

## Review findings — disposition at head

The review is unusual in shape: F1–F21 are neutral observations, many of them note-vs-code drift rather than code defects. All are resolved, refuted, or advisory at head:

| finding | disposition at head | evidence at `de841a15` |
|---|---|---|
| F1 (art vs note's soldier-sprite plan) | **resolved** — the coordinator ruling (run log 2026-08-24T07:14:26Z) binds: the nano-banana art stays and the note records it. `design.md` §Packaging now names the five `data/cog_*_front.png` sprites, "no tint path", `scripts/art/` provenance, and the accepted deviation. `docs/plans/…-design.md` and the run copy are byte-identical (diffed). `grep -rn soldier` in the tree matches only the note's own sentence. |
| F2 (docs.readme bare string) | **resolved** — `coworld_manifest_template.json` `game.docs.readme` is now `{"type":"text","value":…}` (verified by JSON parse; value 1645 chars). Was the one item-10 defect; commit `f61dd77`. |
| F3 (premium/quota literals) | **resolved** — note corrected to the code's `6 + rng.rand(3)` / `12 + rng.rand(7)` (design.md:95–96); code was already right (`sim.nim:188,190`, ranges 6…9 / 12…19 asserted in tests). |
| F4 (two RNG streams) | **resolved** — note now describes both seeded streams (design.md:99–103: `initRand(seed*6779+31)` for aliases, `initRand(seed*7919+17)` for the rest); code unchanged and correct; "seed alone reproduces all of it" holds and is tested. |
| F5 (curve carries noiseScale) | **resolved** — note's pseudocode now has the `curve[t] = clamp(base * config.noiseScale, …)` line and says the forecast is on the meter's scale (design.md:149–153); code unchanged (`sim.nim:201`). |
| F6 (empty say at zero meter not `silent`) | **resolved in code** — `sim.nim:438–443`: `if sim.airtime[seat] <= 0: silent = true; line = ""`, unconditionally; the flag is a property of the meter and re-derives on replay. Test extended. |
| F7 (sim-side truncation unmarked) | **resolved in code** — `clipRunes` (`sim.nim:398–410`) now returns `runeSubStr(0, limit-1) & "…"`, marker inside the limit so an airtime clip still fits the meter. |
| F8 (`sameEvent` subset; any end reason) | **resolved in code** — `sameEvent` (`sim.nim:922–936`) compares every recorded field incl. `airtime`, `scores` (via `sameFloats`), `text`, `cash`; `evEnd` branch rejects reasons outside `LegalReasons = ["complete","deadline"]` (`sim.nim:996–1011`) and runs `sameEvent` on the ending. New tampering tests at `tests/test_sim.nim:603–632` cover turn-airtime, end-scores, end-portfolios and illegal reason. |
| F9 (replayed silent say re-derived false) | **resolved in code** — the `evSay` replay branch (`sim.nim:959–981`) now compares text, notes, silent, channel, cost, airtimeLeft, ticket and all seven term fields; `clipped` checked for consistency (documented as not re-derivable). Test at `tests/test_sim.nim:634`. |
| F10 (endcard read recorded results) | **resolved in code** — both payload builders now emit re-derived results: `server.nim:205–215` `derivedFrames` returns `frames[^1].resultsJson()`, and `replay-viewer/garble_replay.nim:51` sets `"results": frames[^1].resultsJson()`. `renderer.js:1506` still reads `payload.results`, which is now the re-derivation. Test "the endcard's results are the re-derived ones, field for field" at `tests/test_sim.nim:679`. |
| F11 (no-op probe) | **resolved in code** — the probe is gone; `decideAll` (`llm.nim:709–717`) documents `parseDecision` as the ill-formed gate. Behaviour unchanged. |
| F12 (no live column < 560 px) | **resolved in code** — `renderer.js:113–135`: only the sparkline is `!layout.compact`; the amber live column draws at every width past the `plot.w > 40` guard (304 px at 360 px). |
| F13 (burst wash ignores `#grain`) | **resolved in code** — `driveGrain` (`renderer.js:156–163`) sets `#grain`'s inline opacity to double for the wash and clears it after; chrome.css untouched (CI provenance step green). |
| F14 (audio: crackle, CLEAR floor, seek cancel) | **resolved in code** — `level()` maps `((interference − 0.25) / 0.5) * 0.18` clamped ≥ 0, i.e. 0.0 through CLEAR (`renderer.js:1280–1284`); `crackle(count)` schedules per-garbled-word pops and `cancel()` stops every scheduled node (`renderer.js:1220–1259`); `setIndex` calls `noise.cancel()` on every jumped seek (`renderer.js:1499–1503`). All inside `try/catch`, behind the button, never gating `data-replay-loaded` — smoke `loaded:true` in 281 ms confirms. |
| F15 (feed closing lines) | **resolved in code** — `endText` (`renderer.js:911–930`) emits `FINAL — <leader> 1.42× (312 cr) · 12 turns played.` and `Episode deadline — scored on N of M turns.`, cap threaded from `payload.config.turns`. |
| F16 (fourth rename `ROUND 0`→`TURN 0`) | **resolved** — the note's rename list now includes the `#clock` placeholder (design.md:926). The page diff against the starter is otherwise exactly the note's list — I re-diffed. |
| F17 (no grid harness) | **resolved in tree** — `scripts/tune_baselines.nim` (155 lines, 576-point grid × 60 seeds × 4 tables) and `docs/tuning/baseline-grid.md` (full ranking, shipped row at rank 218/576 inside a 9 % plateau, per-parameter curves, gates) are committed; `BaselineParams`/`DefaultBaseline` in `llm.nim:156–169` carry exactly the shipped constants so behaviour is unchanged. Item 7's second sentence now has an artefact. |
| F18 (prompt size vs estimate) | **resolved** — the note now carries the measured figures (≈5 400 runes at 12 turns, ≈7 100 at 18, ≈8 100 at 24, ≈3 060 system; design.md:526–531), consistent with the reviewer's own probe (5 405 / 7 036 / 3 057). No code change needed: ~3 000 tokens at the cap is one ordinary request. |
| F19 (spacing floor paid with no calls) | **advisory, not blocking** — the reviewer itself conceded "the code follows the rule as written". I verified independently: `server.nim:358–364` is exactly the note's `max(minTurnSpacingMs, callsIssuedLastTurn * 2400 ms)`; certification sets `minTurnSpacingMs: 0` (docker-smoke played 8 turns in ~1 s); worst hosted case 24 × 12.4 s ≈ 298 s ≪ 720 s; the deadline check precedes every turn. Every wait remains bounded — item 5 holds. No fix required, none made. |
| F20 (three missing note-list assertions) | **resolved in tests** — 20 → 500 confirm episodes (`tests/test_sim.nim:329`), "selling the contract commodity below price lowers the score" (`:414`), tampered-interference block (`:590–601`). All additions; nothing weakened (see item 1 audit). |
| F21 (unguarded game thread) | **resolved in code** — `runGame` (`server.nim:417–437`) wraps `playEpisode` in `try/except CatchableError`, settles what was played (`endEarly` + broadcast) and writes artifacts via `finishEpisode`, `quit(1)` only if even that fails. |

## Refuted

Nothing to refute in the strict sense: no reviewer claim was false against the code it was written about, and none survives at head as a defect. The nearest case:

### F19 — "the inter-batch spacing floor is paid even when no LLM call was issued" → NOT A DEFECT
- Evidence: `src/garble/server.nim:358–363` at `de841a15` — `let spacingMs = max(config.minTurnSpacingMs, callsLastTurn * MsPerCall)`; this is the design note's stated rule verbatim (design.md:400–403), every sleep is bounded by `spacingMs`, and the arithmetic stays far inside the 720 s budget (≤ 298 s of floor at the 24-turn cap). The reviewer filed it as an observation, not a violation; I confirm it violates no checklist item. Dismissed as blocking; stands as an accurate advisory note.

All other findings were true at `d76e12c3` and are **fixed at head** — resolved, not standing (dispositions above, each re-verified from the tree, not from the fixer's table).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1. CI green, no test loosened | **PASS** | `gh run list -R Metta-AI/cogame-garble --branch main -w ci.yml`: run **32706190772**, `completed success`, `head_sha de841a155a…` = origin/main (confirmed via `gh api …/runs/32706190772` → `head_sha`, `conclusion: success`); jobs test/docker-smoke/wasm-viewer all ✓, 172 `[OK]` lines. Test history audited from the coworld repo itself: `git log -p f1aeb04..HEAD -- tests/` — commits `74c68e2 f25d8ca abf91a4 8edde07 aa29cb6 ef352e2`; the **only** deleted line in all hunks is `for episode in 0 ..< 20:` replaced by `0 ..< 500` (a strengthening); no skip/xfail/tolerance-widening/file removal anywhere. |
| 2. Replay re-derivation | **PASS** | `sim.nim:938–1012` `replayMatch` replays decisions and compares every recorded derived field (`sameEvent` `sim.nim:922–936`); tests: "the recorded log re-derives frame for frame" (`test_sim.nim:543`, `frames.len == events.len + 1`, final frame's `tableStateJson` **and** `resultsJson` equal the live sim's), heard-delivery identity (`:551`), tamper tests (`:574`, `:603`), say re-derivation (`:634`), endcard results (`:679`). Viewer derives from that same re-derivation: `garble_replay.nim:39–52` (`replayMatch` → `states`, `results = frames[^1].resultsJson()`); `server.nim:205–215` in replay mode. No parallel recording is drawn. |
| 3. Static viewer | **PASS** | Manifest `game.replay_viewer = {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode `100755` (`git ls-files -s`), is the `coworld build` hook (ci.yml asserts file + exec bit), `mkdir -p` before the containment check, final `grep -q 'data-replay'` kept. `static_replay.js` fetches only the `?replay=` URL; no other network call in the bundle. No `/client/replay` in the manifest (grep rc=1); the server's `GET /client/replay` route is the starter's own replay-mode page route (babel `server.nim:502` has it identically), not a pod viewer declaration. |
| 4. Both name spaces | **PASS** | Aliases in-game: `tableNames` (`sim.nim:114–125`); tests assert every prompt carries the seat's alias and **none** of the policy display names (`test_sim.nim:761`, `:776`). Spectator side: replay carries `names` + `policyNames`; `makeNameMap` (chrome_common.js:130–158) renders policy names for non-baseline seats, aliases for `Baseline (N)` fillers; `resultsJson.names` are policy names (`sim.nim:630`). |
| 5. Degrade-never-hang | **PASS** | Every wait bounded: player-connect 180 s poll (`server.nim:284–290`); one LLM batch per turn with `effective = min(llmTimeoutSeconds, max(5, playDeadline − now))` (`server.nim:368–370`); retry once then scripted (`llm.nim:688–727`); spacing sleep capped at `spacingMs` (`server.nim:363`); pacing `turnDelayMs`; artifact POST timeout 60 s (`server.nim:156`); 20 s shutdown grace then `quit(0)`. `PlayBudgetFraction = 0.6` → 720 s of 1200; deadline checked before every turn opens (`server.nim:337–341`, `endEarly` → scored `deadline` ending). Worst case 12 × (25+25+0.4) ≈ 605 s < 720 s. F21 guard makes a dying game thread settle and write rather than hang (`server.nim:417–437`). Player binary exits 0 on a dead socket (`garble_player.nim`, try/except around the receive loop). No unbounded loop or blocking read found. |
| 6. `num_agents` | **PASS** | `num_agents: 5` in all three variants (manifest:399, 429, 459) and `certification.game_config` (:487); `len(certification.players) = 5 = len(game_config.players)`. `docker_smoke.sh:106–152` enforces all four invariants plus the `SMOKE_SEATS` cross-check, each exiting non-zero with `SEAT-COUNT FAIL:`. **Grepped the full log of run 32706190772: zero occurrences of `SEAT-COUNT FAIL`**; the job printed `game=garble seats=5 …` and `smoke OK: seats=5 results=438B replay=14090B reason=complete`. |
| 7. Scripted baseline full episodes; grid-tuned | **PASS** | `test_bot.nim:70–85`: 4 seeds × all 32 quoter/shark mixes, `check sim.reason == "complete"`, `checkLegal` on every decision (text ≤ 160 runes / 32 words, qty/price 0..99, commodity real, no notes), airtime 0..900 each turn, < 2000 ms. Deals happen (`:87–99`, ≥ 1 per seed, median ≥ 3). Grid harness committed: `scripts/tune_baselines.nim` + `docs/tuning/baseline-grid.md` (576 points × 60 seeds × 4 tables; shipped row identified and reasoned per parameter); `DefaultBaseline` (`llm.nim:168`) matches the shipped constants. |
| 8. LLM reply handling | **PASS** | `extractJsonObject` takes first `{` to last `}`, tolerating prose/fences (`llm.nim:490–503`); `for attempt in 0 .. 1` with an explicit hint appended on retry (`llm.nim:688–700`); still-open seats fall back to `scriptedAction(sim, seat, skQuoter)` with the greppable `garble llm: seat N falling back to scripted decision` (`llm.nim:723–727`); the fallback is recorded — `client.decidedScripted[index] = true` → `wasScripted` → the event's `scripted` flag (`server.nim:379–381`, `sim.nim:814`), so phase 60 can count it from the replay. |
| 9. Rune-safe truncation | **PASS** | `clipRunes` (`sim.nim:398–410`) — text 160, airtime clip, notes 400, all `runeSubStr` with the `…` marker inside the limit; `cleanText` (`llm.nim:565–572`) for reply fields; player prompt capped at 4000 runes on receipt (`server.nim:556–557`). Test feeds `"音"×400` text and `"é"×900` notes and asserts caps plus `validateUtf8() == -1` on the event JSON (`test_sim.nim:501–513`); reply-side caps tested (`test_bot.nim:234`); CI's strict-UTF-8 replay parse passed. |
| 10. Manifest validates | **PASS** | `game.docs.readme = {"type":"text","value":…}` (fixed by `f61dd77`, verified by parse); `pages` = two entries each `{id,title,content:{type:"text",value}}`; `game.protocols` carries both `player` (2289 chars) and `global` (2728 chars). |
| 11. Viewer legible at 360 px | **PASS** | `client/chrome.css:452`: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `:461–467`: `@media (max-width: 640px) { .plate-label { display: none; } … }`. Compact stage composition < 560 px in `renderer.js:42–84`; live meter column now drawn at every width (F12 fix). |
| 12. Release order and scaffold | **PASS** | `coworld-release.yml`: Build the Coworld manifest (:153) → Certify locally (:167) → **Upload the policies (:206)** → Upload the Coworld (:304) → Put the Coworld secret (:342). All three workflows present. `docker_smoke.sh` mode 100755. `policies.json`: four policies — champions `garble-signal` and `garble-shortwave` (both `PLAYER_PROMPT`, materially different strategies), champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, two `PLAYER_SCRIPTED` fillers. Placeholder gate run exactly as specified: `grep -n '<slug>\|<IMAGE>\|<SEATS>' …` matches nothing (exit 1) → gate exits 0. In-run smoke uses the image built in the same job (`docker build … && ./tools/ci/docker_smoke.sh "${IMAGE}:ci"`). |
| 13. Viewer executes | **PASS** | Run **32706190772**, job `wasm-viewer` (id 97368034977) ✓, `needs: docker-smoke` in ci.yml, no `continue-on-error` anywhere in the workflows (grep rc=1). The `Load the bundle in a real browser` step ran and printed `{"loaded":true,"ms":281,"clock":"TURN 2 / 8 · STORM 95% · STATIC BURST · WAITING ON 2",…,"feed_lines":221}`, `soak: 10s of playback kept advancing`, scrub readouts differing at 0/50/100 % (`TURN 2 / 8 …` / `TURN 5 / 8 · HAZY 30%` / `FINAL — WIDGET 1.90×`), against the replay docker-smoke produced. Markers: `data-replay-loaded="true"` set in `attachReplay`'s first-frame path (`renderer.js:1538`, babel's placement verbatim); `data-replay-error="<message>"` set in `fail()` (`static_replay.js:56`), removed on retry. Link-flag/bootstrap contract: `config.nims:38–39` `-s MODULARIZE=1 -s EXPORT_NAME=GarbleReplayModule` and `static_replay.js:138` calls the `GarbleReplayModule()` factory — same starter (babel), diff shows renames only; `emscripten_exit_with_live_runtime()` present (`garble_replay.nim:77–86`). |
| 14. Chrome is the starter's | **PASS** | `chrome_common.js`: all 15 functions and all 8 palette constants **character-identical** to `cogame-babel/client/renderer.js` (checked programmatically by brace-matched extraction); only additions are the IIFE, the `window.GarbleChrome` export, and the one named `relayout()` recorded in the note. `chrome.css`: first 443 lines byte-identical to the starter's (diffed; CI re-checks against raw.githubusercontent and passed). `replay_broadcast.html`: babel's 74-line `replay.html` + the note's renames (incl. the now-recorded `#clock` `ROUND 0`→`TURN 0`) + one inserted `chrome_common.js` script tag + the banner-marked game block (117 lines total — an *extension* of the starter page, not a fraction of it). Transport: (a) `relayout()` writes `--topband`/`--band`/`--hudscale` on `document.documentElement` (chrome_common.js:206–222); (b) no `position: fixed` in the appended CSS, nothing sits in the band; (c) `#endscreen { bottom: var(--band, 0px) }` (chrome.css:528), shown via `#endscreen.show` (chrome.css:381 ↔ `classList.toggle("show", …)` renderer.js:784), and **every seek** dismisses it — `setIndex` calls `updateEndscreen(…, index >= events.length, …)` on every index change (renderer.js:1504–1507); no keyboard seek path exists in starter or fork, so the seeks that exist are all covered; (d) beats are `<button type="button">` with `title` + `aria-label` + onclick seek (`garbleMarkBeat`, renderer.js:1038–1053), CSS for every emitted kind incl. `.burst`/`.silent`/`.misheard` variants (chrome.css:470–522) and seat colours from the starter's `.seatN { --tc: … }`; builder/helper names (`buildGarbleScrub`/`garbleMarkBeat`) disjoint from `GarbleChrome` keys, enforced by the CI step (passed: "chrome/game namespaces disjoint"). No `#viewpanel`/zoom/minimap anywhere — the arena fits the frame and babel ships none. |
| Addendum: parallel batch | **PASS** | `decideAll` builds one `RequestBatch` over every open seat and calls `client.curl.makeRequests(batch, timeoutSeconds)` (`llm.nim:691–704`); scripted seats never enter it; no sequential per-seat request path exists in the tree. |

### Notes on "could not determine" items the reviewer left open
- **Platform schema acceptance of the readme shape (F2):** moot at head — the readme is now the object form all three talk-lineage starters use; the shape named by checklist item 10 is satisfied from the tree, which is what item 10 asks.
- **Hosted 720 s with real model latency:** the checklist asks for explicit bounds and the settle-inside-60 % mechanism, both verified from the tree (item 5). A hosted-latency measurement is phase-60 evidence, not an item-5 requirement; not counted.
- **F21 reachability:** the guard now exists regardless of reachability; item 5 satisfied.

## Non-blocking observations
- `renderFeed`'s `lastTurn` local is assigned and never read (inherited noise; fixer noted it).
- `scripts/tune_baselines.nim` is not compiled by CI; a `nim check` line in the `test` job would pin it against bitrot.
- The fixes report (r1-fixes.md:46–48) says the run-directory design note still needed mirroring; at head the two copies are already byte-identical (diffed) — the mirroring has happened. No action needed.
- `viewer_smoke.mjs`'s soak line prints `(null -> null -> null)` for the tick probe Garble has no readout for; the harness passes on the moving clock. Template file, byte-verbatim — correct to leave alone.

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | note amended per coordinator ruling | design.md §Packaging/§stage record the shipped art; copies identical; no soldier refs | yes |
| F2 | readme → {type,value} | manifest parses; readme is the object form | yes |
| F3–F5 | note corrected; code was right | code matches at `sim.nim:188,190,201,118,163`; note now matches code | yes |
| F6 | `silent = true` at zero meter | `sim.nim:438–443` | yes |
| F7 | `clipRunes` marks the cut inside the limit | `sim.nim:398–410` | yes |
| F8 | `sameEvent` full-field; only legal endings | `sim.nim:922–936, 996–1011`; tests `:603` | yes |
| F9 | say fields re-derived; `clipped` consistency-checked | `sim.nim:959–981`; test `:634` | yes |
| F10 | both builders emit re-derived results | `server.nim:205–215`, `garble_replay.nim:51`; test `:679` | yes |
| F11 | probe removed | no `probe` in `llm.nim`; comment names `parseDecision` as the gate | yes |
| F12 | live column at every width | `renderer.js:113–135` | yes |
| F13 | `#grain` inline opacity doubled during wash | `renderer.js:156–163` | yes |
| F14 | 0 gain through CLEAR, crackle per garbled word, cancel on seek | `renderer.js:1280–1284, 1220–1259, 1499–1503` | yes |
| F15 | endText names leader + turn cap | `renderer.js:911–930` | yes |
| F16 | `#clock` rename recorded in the note | design.md:926 | yes |
| F17 | harness + grid doc committed; DefaultBaseline = shipped constants | `scripts/tune_baselines.nim`, `docs/tuning/baseline-grid.md`, `llm.nim:168` | yes |
| F18 | measured prompt sizes in note + doc comment | design.md:526–531, `llm.nim:351–356` | yes |
| F19 | REFUTED, no change | code is the note's rule; bounds hold; not a checklist violation | yes |
| F20 | 500 episodes, sell-below-price test, interference tamper | `test_sim.nim:329, 414, 590–601`; only deletion in tests/ history is `20`→`500` | yes |
| F21 | top-level guard settles and writes | `server.nim:417–437` | yes |
| CI claim | run 32706190772 success at `de841a15` | `gh api` confirms head_sha + conclusion; log evidence quoted above | yes |

## Blocking items

None.

BLOCKING: 0
