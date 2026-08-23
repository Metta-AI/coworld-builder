blocking: 0

# r1 verdict — ledger

Head: `8f3ffcb6ef3a945e54e6c39fa22147bd2a6c179f` (fresh clone at `/workspace/judge-ledger`; `git rev-parse HEAD` matches the brief)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: yes (repo, starter diffs, manifest, workflows,
CI run 32672565512 logs, and the review were all read and my checklist pass formed **before**
opening `r1-fixes.md`; the builder's `log.md` was consulted once, after my code read, only to
search for baseline-tuning evidence for item 7).

## Standing blocking findings

**None.** Every reviewer finding is either resolved at the judged head or was never a checklist
violation, and my own independent pass over items 1–14 plus the parallel-batch rule found no
falsification at `8f3ffcb`.

## Refuted / resolved (the reviewer's findings, checked at the judged head)

The r1 review filed **zero blocking** findings and nine non-blocking observations (N1–N9). I
attempted to refute each. None is refuted as of the sha it was written against — all nine
reproduce at `d5531a17` — and all are either resolved or benign at `8f3ffcb`:

### N1 — note's TRUST 6/6 landmark at s=6 → RESOLVED at head
- Confirmed real at d5531a17: `trustPayoffs(6, 50)` = `(6, 8)` by the formula at
  `src/ledger/sim.nim:162-169`; the old note said 6/6.
- At head the note reads "an even split of the pot (`s = 4, p = 50`) → 6 / 6 … full trust with a
  fair split (`s = 6, p = 50`) → 6 / 8" (`docs/plans/2026-08-23-ledger-design.md:132-134`), matching
  `check trustPayoffs(4, 50) == (6, 6)` / `check trustPayoffs(6, 50) == (6, 8)`
  (`tests/test_sim.nim:177-178`). Commit `8c84b14` touched **comment lines only** in `tests/`
  (verified `git show 8c84b14 -- tests/`: −4 comment lines, +2 comment lines, zero asserts changed).

### N2 — note's global ±1 first-mover claim → RESOLVED at head
- Confirmed: the code implements the greedy local rule (`sim.nim:286-298`), no global balance.
- At head the note states the local invariant, says explicitly "A global '±1 across the episode'
  balance is **not** available and is not claimed", and cites a 10 000-seed measurement (design
  note lines 96-106); the test-plan item matches what `tests/test_sim.nim:118-144` asserts.

### N3 — renderer.js provenance list wrong in the note → RESOLVED at head
- I verified the head's claim **programmatically**: split both `client/renderer.js` and
  `/workspace/starters/cogame-babel/client/renderer.js` on `^(  )?function <name>(`, compared
  bodies byte for byte. Result: the note's four lists (22 untouched byte-identical / 9 removed /
  26 new / 15 changed) match the files **exactly**, with zero functions unaccounted on either
  side, and none of the "changed" set is accidentally identical. Commit `8f3ffcb`.

### N4 — note claimed a chrome.css deletion that never happened → RESOLVED at head
- Confirmed and independently re-verified: `client/chrome.css` lines 1-443 are the starter's
  byte for byte (prefix diff empty), 681 total lines — strictly append-only; `@font-face` for
  rajdhani survives at `:9` and is live (`data/font.ttf` ships, `GLYPH_FONT` names it). The head
  note now says append-only. Commit `9888247`.

### N5 — replay test asserted only count + endpoint → RESOLVED at head
- Confirmed at d5531a17. At head `tests/test_sim.nim:535-568` asserts, for **every**
  `i in 0 .. events.len`: (a) `frames[i].events == live.events[0 ..< i]` (each frame event is
  re-derived, not copied — `replayMatch` at `sim.nim:855-903` only ever appends events through
  `beginRound`/`applyMeeting`/`applyGossip`/`settle`); (b) `replayMatch` on the prefix lands on
  exactly `frames[i]`; (c) every live-published tick (round opens + settlement, captured in
  `liveCheckpoints`, `tests/test_sim.nim:33-51`) equals the frame with that event count. Green
  in run 32672565512 in debug and `-d:release` (`[OK] every frame re-derives the prefix it
  stands for, field by field`). The old test is untouched. Commit `9322824`.

### N6 — ring caption named 2-seat components → RESOLVED at head
- Confirmed at d5531a17. At head `ringGroups` ends
  `.filter(function (group) { return group.length >= 3; })` (`client/renderer.js`, ringGroups
  tail), matching `ringComponents`' `if component.len >= 3` (`sim.nim:466`). The per-pair feed
  line and per-pair red threads are unchanged, which is what the note specifies. Commit `de84943`.

### N7 — `outMean = 0.0` on empty outside record → CONFIRMED BENIGN (documented at head)
- I verified the reachability argument myself: the flag needs `inCount >= 2` (`sim.nim:430-431`),
  and no pair meets in consecutive rounds (resample at `sim.nim:260-265`, asserted
  `tests/test_sim.nim:103-116`), so a twice-met pair's members each carry ≥ 6 outside meetings in
  play; only a hand-built history reaches the `0.0`. Comment at `sim.nim:431-440` + note clause.
  No checklist item touched (ring detection is never a score input — `resultsJson` reads
  `ringThreads().len` only, `sim.nim:687`; asserted `tests/test_sim.nim:403-430`). Commit `e2a2147`.

### N8 — feed/endcard RING lines read a module-global → RESOLVED at head
- Confirmed real at d5531a17 (a genuine display bug after a seek). At head `latestRings` is gone
  (grep: zero hits); `renderFeed`/`updateEndscreen` take `rings` as a parameter; `attachReplay`'s
  `setIndex` passes `currentState().rings` — the same re-derived frame the canvas draws — and
  `attachLive` passes the live snapshot's `rings` (verified in both attach functions). Viewer
  smoke green after the change (`loaded: true`, feed renders, seeks work). Commit `98c15fa`.

### N9 — fallback vs registered-scripted indistinguishable in the replay → NOT A DEFECT
- Accurate observation; matches the design note (`:342-343`) character for character. Item 8's
  "recorded so phase 60 can count it" is satisfied: the meeting event carries
  `scriptedA`/`scriptedB` and the fallback path alone emits
  `ledger: seat N falling back to scripted decision` (`llm.nim:681-683`), so the game log counts
  fallbacks distinctly. No change was required and none was made.

I also settled two of the reviewer's "could not determine" entries myself:
- **`writeCogameUri` wait bound** (item 5): read the pinned dependency at
  `~/.nimby/pkgs/bitworld` (commit `9af28b4`, matching `nimby.lock`). The non-POST path is
  `newCurlPool(1).put(value, headers, data)` (`bitworld/src/bitworld/runtime.nim:207-212`), and
  curly's `put` defaults `timeout = 60` (`curly.nim:603-616`). Bounded. The POST branch in the
  game is explicitly bounded at 60 s (`server.nim:159`). Settled: no unbounded wait.
- **±1 first-mover bound**: moot at head — the note no longer claims it (N2).

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32672565512** on `main` at `8f3ffcb`, conclusion `success`; jobs `test`/`docker-smoke`/`wasm-viewer` all success, every step success (`gh run view --json jobs`). Both test files ran in debug **and** `-d:release` (log lines 284/316/348/488), 96 `[OK]`s. `git log -p --since=2026-08-23T21:17:00Z -- tests/`: files enter at `728e57e`/`de5ab5d` (byte-identical generations), then `8c84b14` (comment-only, hunks read) and `9322824` (+44 lines, pure additions). No assertion deleted, no tolerance widened, no skip/xfail anywhere in `tests/`. |
| 2 Replay re-derivation | PASS | `replayMatch` re-derives via the rules (`sim.nim:855-903`); wasm viewer calls the same `replayMatch` + `tableStateJson` (`replay-viewer/ledger_replay.nim:34-46`, `import ledger/sim`); written replay carries no `states` (`server.nim:165-187`) so nothing parallel exists to read. Frame-by-frame test `tests/test_sim.nim:526-568`, green both modes. |
| 3 Static viewer | PASS | `"replay_viewer": {"bundle": "static-replay-viewer"}` (`coworld_manifest_template.json`, game.replay_viewer); `tools/build_replay_viewer.sh` present, mode 100755, emits the bundle; shell fetches **only** `?replay=<url>` (`static_replay.js:67-83`), `index.html` loads only local files, assets copied into the bundle (`assetBase: "./assets"`). No pod viewer declared anywhere; the string `/client/replay` appears once, as prose in the `global` protocol text that itself names the static bundle as the platform viewer. |
| 4 Both name spaces | PASS | Prompts/observations use `sim.names` aliases only (`llm.nim:248-249` and throughout `userPrompt`); `resultsJson.names` = policy names (`sim.nim:669-670`); replay carries both `names` and `policyNames` (`server.nim:177-178`); viewer maps alias→policy for non-baseline seats (`makeNameMap`/`isBaselineFiller`, byte-identical babel code). |
| 5 Degrade-never-hang | PASS | Connect wait bounded (`server.nim:258-266`); `PlayBudgetFraction = 0.6` ⇒ 720 s of 1200 (`server.nim:38, 288-294`); pre-round reserve 70 s / 2 s scripted (`:43-47, 304-315`) → `endEarly` → `reason="deadline"`; batch HTTP bounded by `llmTimeoutSeconds=30` (`llm.nim:662`); interval sleep bounded (`:386-393`); artifact writes bounded 60 s (POST `server.nim:159`; PUT via curly default 60 — verified in the pinned dep, see above); the only `while true` exits on `done`/deadline and falls into `finishEpisode` (bounded 500 ms + 20 s grace, `quit(0)`). |
| 6 num_agents | PASS | `num_agents: 8` in `variants[0]`, `variants[1]` **and** `certification.game_config` (parsed the manifest); `len(certification.players)` = `len(certification.game_config.players)` = 8. `docker_smoke.sh:106-152` enforces all four invariants + the independent `SMOKE_SEATS` cross-check before any container starts, each via `SystemExit` prefixed `SEAT-COUNT FAIL:`. `grep -c "SEAT-COUNT FAIL"` over the full log of run 32672565512: **0** (and the smoke line shows `seats=8` with the 8-player fixture config). |
| 7 Scripted baseline | PASS (see observation O1) | `tests/test_bot.nim:60-87`: seeds [1,7,42,1234] × {8×mirror, 8×shark, 4/4}, full episode, `reason == "complete"`, every payoff in [0,14], every move via `scriptedAction`; `:95-116` every (subgame, role) legal without clamping over 20 seeds × 21 rounds. "Not guessed": the parameters are the payoff tables' fair-play landmarks (s=4/p=50 is the unique 6/6 point, asserted `test_sim.nim:219-222`; offer 5 / floor 4 straddle the kind boundary) and the committed harness pins them behaviorally — mirrors settle on exactly the fair payoff in all three games (`test_bot.nim:159-172`), mirror cooperation < 0.25 vs sharks / > 0.9 among mirrors (`:133-157`), shark characterization (`:174-200`); materially different parameters fail these tests. No standalone parameter-grid sweeper exists — recorded as observation O1, not blocking, for the reasons given there. |
| 8 LLM reply handling | PASS | `extractJsonObject` first `{`…last `}` (`llm.nim:485-495`); `for attempt in 0 .. 1` = exactly one retry sub-batch with corrective hint (`:646-680`); leftover seats → `mirror` fallback, recorded via `Decision.scripted` → `scriptedA/B` on the meeting event + the distinct log line (`:681-684`). Parse-tolerance and clamp asserted `test_bot.nim:232-274`. |
| 9 Rune-safe truncation | PASS | `cleanText` runeSubStr (`llm.nim:464-471`); notes/memos capped in `parseDecision`; prompt cut rune-safe at 4000 (`server.nim:510-515`); every quoted error goes through `cleanText`. Tests: 500×`é` → 120 runes valid UTF-8 ending `…` + strict-JSON round trip (`test_sim.nim:325-335`); 900×`日` → 400 runes (`:337-345`); parse path (`test_bot.nim:276-288`). CI additionally strict-parses the real replay bytes (docker_smoke, `SMOKE_REQUIRE_REPLAY_JSON=1`). |
| 10 Manifest validates | PASS | Parsed the template: `game.docs.readme = {"type":"text","value":…}`; `pages` = 2 × `{id, title, content:{type:"text", value}}` (`rules.md`, `strategy.md`); `game.protocols` carries both `player` and `global`. |
| 11 Viewer legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` (`client/chrome.css:478-482`); `.plate-label`/`.plate-tag`/`.plate-pips` hidden under `@media (max-width: 640px)` (`:495-502`); gossip rail collapsed under 480 px (`:556-559`). |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build the Coworld manifest (:153) → Certify locally (:167) → Upload the policies (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342), one job, sequential steps, certify runs against the just-built artifact. All three workflows present; `docker_smoke.sh` mode 100755; `policies.json` = 2 × `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 (`ledger-broker`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. The three-name placeholder grep over the five files exits with no matches (ran it: pass); the four documented runtime residues are present where expected and not filed. |
| 13 Viewer executes | PASS | Run **32672565512** `wasm-viewer`: `needs: docker-smoke` (`ci.yml:212`), no `continue-on-error` in any workflow (grep: none), step **"Load the bundle in a real browser"** concluded success with `{"loaded":true,"ms":289,"clock":"ROUND 3 / 6 · SETTLING",…,"feed_lines":39}` against the docker-smoke replay. Markers: `data-replay-loaded` set at the end of `attachReplay` after the first synchronous draw (`renderer.js:1619`); `data-replay-error` set in `fail()` / cleared on success (`static_replay.js:56, 107, 134`). Link flags `-s MODULARIZE=1 -s EXPORT_NAME=LedgerReplayModule` (`config.nims:38-41`) and the factory-call bootstrap `LedgerReplayModule()` (`static_replay.js:138`) are babel's **together** — the shell diff against the starter is renames only; no `onRuntimeInitialized` anywhere. |
| 14 Chrome is the starter's | PASS | `client/renderer.js` provenance verified function-by-function against the starter (see N3 — exact match to the note's named, minimal patch list; 22 functions byte-identical). `client/replay.html` is the starter's page + the banner-commented game block (`gossip-rail`/`ringnote` inside `#board-wrap`), 83 vs 74 lines, every starter id in the same nesting; `chrome.css` strictly append-only. Transport: (a) `relayout()` measures `#transport`, sets `--band`/`--hudscale` on `document.documentElement` (`renderer.js:1112-1121`), bound to load/resize/feed-toggle; (b) overlays live inside `#board-wrap` above `#transport`, `#endscreen`/`#loading` keep `bottom: var(--band, 0px)` (`chrome.css:509-510`); (c) endcard shown with `classList.toggle("show", …)` against `#endscreen.show` (`chrome.css:381`), and **every seek path that exists** (scrub click/drag, beat-marker click) runs `setIndex` → `updateEndscreen(show = index >= events.length)` — no keyboard/back-forward seek exists in this lineage or in the starter (grep keydown/popstate: none in either); (d) beats are labelled `<button type="button">`s that seek by `dataset.index`, six emitted kinds each with CSS (`chrome.css:597-630`), seat colour classes `seat0..seat7` all defined. `#viewpanel`/zoom/minimap: absent everywhere (grep zero hits), design note says fixed arena. |
| Parallel batch (simultaneous game) | PASS | One `RequestBatch` per round, one `curly.makeRequests` per attempt for all open seats (`llm.nim:646-662`); server calls `decideAll` once per round on a snapshot (`server.nim:341-342`); no per-seat sequencing anywhere. Position-mapping asserted against shuffled arrival (`test_bot.nim:290-316`). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| N1 | note + test-comment only, commit `8c84b14` | hunks read: comment-only in tests, note fixed | yes |
| N2 | note only; claim measured false (40 000 episodes, worst spread 5) | code greedy rule confirmed; note at head states local invariant + measurement; no test/code change | yes |
| N3 | note + file header, commit `8f3ffcb` | programmatic function diff matches the note's 22/9/26/15 lists exactly | yes |
| N4 | note only | chrome.css prefix byte-identical, append-only re-verified | yes |
| N5 | test strengthened, nothing removed, commit `9322824` | new test present and green both modes; old test untouched; diff is pure addition | yes |
| N6 | code fix, `>= 3` filter, commit `de84943` | filter present in `ringGroups` at head | yes |
| N7 | documented, no behaviour change, commit `e2a2147` | comment present; reachability argument independently checked | yes |
| N8 | code fix, module-global removed, commit `98c15fa` | `latestRings` zero hits; `rings` parameterized in feed/endcard; both attach paths pass frame-correct rings | yes |
| N9 | confirmed as designed, no commit | fallback log line + scripted flags verified at head | yes |
| CI claim | run 32672565512 success, SEAT-COUNT FAIL count 0 | re-ran `gh run view` + full-log grep myself: success, 0 hits | yes |

No disposition in the fixer's table misrepresents the tree.

## Non-blocking observations

- **O1 (item 7, tuning provenance).** No standalone grid-tuning harness for the `mirror`
  baseline's parameters exists in the repo, its history, the design note, or the run log. I do
  not count this as blocking because the item's substance is verified from the tree: the
  parameters are the unique fair-play points that the payoff tables pin by construction
  (asserted `test_sim.nim:219-222`), and the committed seed×mix behavioral harness
  (`test_bot.nim:60-200`, run in CI) fails under materially different parameters — i.e. "not
  guessed" is evidenced even though the named instrument (a parameter-grid sweeper) is absent.
  What would settle it beyond doubt: a committed sweep (e.g. forgiveness × invest × floor over
  a few hundred seeds) recording why 0.20/4-1/50-25/5/4 were chosen, or a note/log line citing
  such a run. If the coordinator reads item 7's clause strictly instrumentally, this converts to
  one blocking `other` finding; the tree evidence above is why I did not.
- **O2.** The `global` protocol prose mentions the server's `/client/replay` browser page; it
  also states the platform viewer is the static bundle. Informational only — the manifest's
  `replay_viewer` is the bundle and no pod viewer is declared (item 3 unaffected).
- **O3.** The pass-boundary resample accepts after 16 failed attempts (`sim.nim:260-265`), so
  "no pair meets in consecutive rounds" is a `1 - (1/7)^16` guarantee per boundary, asserted for
  the tested seeds. The note says "at most 16 attempts, then accept", so nothing over-claims.
- **O4.** `updateEndscreen` builds its DOM once (`container.dataset.built`), which is safe here
  because it is only shown at the final index where the ring set is constant — noted only so a
  future change to show it mid-match knows to invalidate the cache.

BLOCKING: 0
