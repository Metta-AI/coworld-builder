blocking: 0

# r1 verdict — poker

Head: `bba6bffe83313b103f921346fe0d964cbb92725d` (confirmed: `git rev-parse HEAD` after
`git checkout` of a fresh clone; subject "fix(deadline): B2 — hard guard nets off one
worst-case decision")
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (lines 70–233, items 1–15 +
the simultaneous-batch rule)
Independent read written before reading fixes: **yes** — I read the checklist, the design
note (incl. Addenda 1–4), the full tree at head, the CI run and its artifacts, and formed
my checklist pass before opening `r1-review.md`; I opened `r1-fixes.md` last, only to
audit its claims. No contamination.

Design authority: the amended design — Addendum 3 (soft guard 0.55·T = 660 s; say cap
120; holdem-6max 14 hands) and Addendum 4 (hard guard 0.56·T = 672 s, netting one
worst-case decision) supersede the corresponding earlier sections.

CI at head: run **32997839855** (`push`, `main`, headSha `bba6bff…`), conclusion
**success**; jobs `test` (98271604042), `docker-smoke` (98271604276), `wasm-viewer`
(98272223135) all success. I downloaded the run's artifacts (`smoke-replay`,
`viewer-smoke`, `static-replay-viewer`) and both job logs and verified the numbers below
myself.

## Standing blocking findings

None. Both of r1's blocking findings were real at the reviewed sha (`7c7e77b`) and are
fixed at head; every checklist item passes at head on evidence I verified independently.

## Refuted

### B1 — full-cap `say` does not fit the speech bubble (reviewer, [legibility]) → REFUTED at head (fixed by `73f2cb5`)
- The finding was true at `7c7e77b`: `git show 7c7e77b:src/poker/types.nim` →
  `MaxSayLen* = 160`; `git show 7c7e77b:client/renderer.js:130` →
  `var BUBBLE_MAX_W = 220, BUBBLE_LINES = 4` — 160 runes cannot wrap into 4×220 px at
  13 px, and that run's sixmax smoke reported `ellipsized: 537`.
- At head: `src/poker/types.nim:15` → `MaxSayLen* = 120` (comment at `:11-14` names the
  geometry: "6 wrapped lines of 300 px, measured in the 13 px font");
  `client/renderer.js:138` → `var BUBBLE_MAX_W = 300, BUBBLE_LINES = 6`; `seatExtent`
  (`renderer.js:156`) still reserves `bubbleHeight(BUBBLE_LINES) * scale` unconditionally,
  and `drawBubble` clamps to canvas width (`renderer.js:707-708`).
- Fixture regenerated: `tools/ci/fixtures/sixmax_audit.replay` carries exactly 6 `say`
  events, one per seat 0–5, each **exactly 120 runes** of multi-byte text (verified by
  parsing the committed bytes); `tests/test_sim.nim:876` asserts
  `runeLen == MaxSayLen` per seat and `:865-886` regenerates byte-identically and fails
  on drift.
- CI evidence at head (run 32997839855, wasm-viewer log + `viewer-smoke-sixmax.json`):
  `canvas text: 27029 drawn, 0 never inside the canvas (0 draws crossed an edge),
  0 ellipsized (--strict-text-bounds)`; cert invocation: `8298 drawn, 0, 0`. 537 → 0.

### B2 — settlement bounded at 70 %, not 60 % (reviewer, [timeout]) → REFUTED at head (fixed by `b6a8e9d` + `bba6bff`)
- The finding was true at `7c7e77b`: `PlayBudgetFraction* = 0.60`,
  `HardDeadlineFraction* = 0.70` — the guard that stops a live hand fired at 840 s = 70 %.
- At head: `src/poker/sim.nim:35-36` → `PlayBudgetFraction* = 0.55` (660 s, checked at
  pair boundaries, `server.nim:326-339`), `HardDeadlineFraction* = 0.56` (672 s, checked
  before **every** decision, `server.nim:275-283`, `voidLiveHand()` +
  `endMatchEarly(erDeadline)`). Worst-case admitted decision per Addendum 4's netting:
  spacing 2.1 s (`sim.nim:41`, `llm.nim:731-737`) + two 20 s attempts
  (`llm.nim:638,755`) + `turnDelayMs` 0.25 s + `sleep(500)` and the artifact write
  (`server.nim:205-210`) ≈ 43 s → settle-and-score ≈ 715 s ≤ 720 s = 60 % of 1200.
  `holdem-6max` is 14 hands in the manifest (verified), expected ≈ 546 s under the 660 s
  soft guard; `EpisodeDecisionBudget = 220` unchanged (`sim.nim:24`). The netting is
  stated in the constant's comment (`sim.nim:26-34`) and in ladder.md
  (`coworld_manifest_template.json:451`), as Addendum 4 requires.

Reviewer non-blocking items N1–N10: I re-verified N1 (the `#endscreen` `inset: auto 0
var(--band) 0` shorthand at `chrome.css:478` does cancel `top: 0` — still true at head,
still falsifies nothing: the endcard keeps `bottom: var(--band)`, is toggled via
`#endscreen.show`, and `setIndex` dismisses it on every seek, `renderer.js:1550-1554`)
and spot-checked N3, N4, N8, N9 — all accurate, all correctly classified non-blocking.
No reviewer finding was overstated other than none; nothing to strike.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run 32997839855 success (test/docker-smoke/wasm-viewer). Full-history `git log -p -- tests/`: test changes are `59afdf2` (creation), `7c7e77b` (test_audit **strengthened**: zero-FP test widened from `blRock`-only/soft-play-only to `for baseline in [blHouse, blRock]` + `flagged.len == 0` all kinds, + new invariant test, + per-kind flag assertions), `b6a8e9d` (16→14 in test_sim/test_audit = Addendum 3's shipped size; assertion structure unchanged), `73f2cb5` (160→120 in test_bot title; assertions were already `runeLen == MaxSayLen`, now pinning the stricter 120). No skip/xfail/removed file/widened tolerance anywhere. The early duplicated subjects (`d9b2889`/`59afdf2` etc.) are the known tree-identical API-push replay. |
| 2 replay re-derivation, frame by frame, viewer from same derivation | PASS | `tests/test_sim.nim:698-754`: for all three end reasons, `$statesFromEvents(config, events) == $statesFromEvents(config, back)` through the JSON round-trip plus key-by-key results equality; fuzz at `:504-554` (200 matches × 4 tables) re-derives and checks final stacks. Both replay consumers call the same `statesFromEvents`: pod replay server `server.nim:522`, wasm `replay-viewer/poker_replay.nim:46`. No parallel recording exists — the replay carries events only (`server.nim:155-169`). `matchEnd` is a load-bearing recorded event (`sim.nim`, asserted `test_sim.nim:756-770`). |
| 3 static viewer | PASS | `coworld_manifest_template.json` → `game.replay_viewer: {"bundle": "static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, mode 100755 (`git ls-files -s`); shell fetches only the `?replay=` URL with a 20 s AbortController (`static_replay.js:68-90`), assets relative; ci.yml gate fails if `/client/replay` appears in the manifest (it does not; the server route `server.nim:497` is the parley-lineage live-server convention, not a declared viewer). Release certify step hard-fails unless the STATIC bundle is reported (`coworld-release.yml:200-210`). |
| 4 both name spaces | PASS | Aliases in game: `tableNames` → `Seat.name`; `redactCards` deletes `policyNames` and strips `calib`/`audit` from player frames (`server.nim:109-137`). Viewer maps alias→policy for non-baseline seats: `makeNameMap`/`isBaselineFiller` (`renderer.js:762-770`). Cert artifact scorebug shows the mapping live. |
| 5 degrade-never-hang, settle ≤ 60 % | PASS | Every wait bounded: connect 180 s (`server.nim:225-233`), LLM `curl.post(..., 20)` (`llm.nim:638`), spacing `sleep ≤ spacingMs` (`llm.nim:736`), turn delay, hard guard before every decision at 672 s, soft/budget guards at pair boundaries at 660 s / 220 calls, bounded 20 s grace then `quit(0)` (`server.nim:217-219`). Worst-case settle ≈ 715 s ≤ 720 s (B2 above). No unbounded loop; websocket handling is event-driven; the only receive loop is the player's, try/except-wrapped, exits 0 (`poker_player.nim`). See observation O1 for a pathological 429-storm residual (non-blocking). |
| 6 num_agents | PASS | All four variants declare it (2/2/2/6) with matching `players[]` lengths, cert fixture `num_agents: 2` = `len(certification.players)` = `len(game_config.players)` = 2 (parsed the manifest myself). `docker_smoke.sh:106-151` enforces all four invariants + `SMOKE_SEATS` cross-check with `SEAT-COUNT FAIL:` prefixes; I grepped the head run's full docker-smoke log: **0 occurrences** of `SEAT-COUNT FAIL`; `smoke OK: seats=2 results=680B replay=16351B reason=complete`. |
| 7 scripted baseline full episodes, legal, tuned | PASS | `tests/test_bot.nim:22-73`: house + rock × 4 tables × 200 matches, every amount checked against the engine's own bounds pre-apply, `applyAction` raising on anything illegal, `handsPlayed == config.hands`; `tests/test_sim.nim:704-724` asserts `results.reason == "complete"` for the scripted natural end; head run's real episode: `reason=complete`. Parameters not guessed: the Kuhn `house` table is the exact α=1/6 Nash — the in-tree exact solver **measures** it at < 1e-9 exploitability (`tests/test_solve.nim:11-13`); Leduc tables are measured finite/positive/stable by the same exact-BR solver (`:44-53`); Hold'em is cosino's Chen bot inherited verbatim per the design. The committed exact-measurement harness (`src/poker/solve.nim` + `test_solve`) is the tuning evidence — strictly stronger than a grid sweep for the rungs where it exists, and the design note pins the remaining tables explicitly. |
| 8 LLM reply handling | PASS | Tolerant extraction first `{`…last `}` (`llm.nim:609-616`); retry exactly once (`:755` `for attempt in 0 .. 1`) with the design's exact retry suffix; fallback to scripted with `fallback = true` (`:769-772`) counted into `results.fallbacks` (`server.nim:311`, `sim.nim` results); 429 → no retry + spacing bump (`:647-652, 767`); no credentials → immediate scripted, asserted < 500 ms (`test_bot.nim:76-89`). |
| 9 rune-safe truncation | PASS | One helper `truncateRunes` (`types.nim:122-134`); applied to say (120) at both `llm.nim:665` and `sim.nim` recordSay, prompt (4000) `server.nim:471`, alias (16), error (200). Tests feed multi-byte at the cap and assert valid UTF-8 + strict reparse: `test_bot.nim:137-161`, `test_sim.nim:841-861`, `test_cards.nim`. |
| 10 manifest validates | PASS | `game.docs` = readme `{type:"text",value}` + 3 pages each `{id,title,content:{type,value}}`; `game.protocols` carries **both** `player` and `global` as `{type:"text",value}` (parsed myself). `results_schema.reason` enum `["complete","deadline","budget"]`. |
| 11 legible at 360 px | PASS | `chrome.css:440` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; `@media (max-width: 640px)` hides `.plate-label, .plate-pips, .plate-front`; 400 px block scales wordmark/clock/score and drops the feed. |
| 12 release order + scaffold | PASS | `coworld-release.yml`: Build manifest (`:159`, `coworld build` from compose = fresh binary in-run) → Certify (`:173`) → Upload policies (`:212`) → Upload coworld (`:310`) → Put secret (`:348`). All three workflows present; `docker_smoke.sh` 100755; `policies.json` = 4 distinct (2 × PLAYER_PROMPT champions, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, 2 × PLAYER_SCRIPTED fillers). The three-name placeholder grep over the five files returns nothing → gate exits 0 (ran it myself). |
| 13 viewer executes | PASS | `wasm-viewer` green at head **including both** smoke steps (log timestamps 18:09:32–18:10:01; not skipped, no `continue-on-error` in any workflow — grepped); `needs: docker-smoke` and loads its artifact. `loaded: true` in 291 ms / 285 ms, soak `moved: true`, `data_replay_loaded: "true"`, bridge `["loading","ready"]`, zero page errors (both smoke JSONs). `config.nims` is byte-identical to cosino's modulo the three renames — `MODULARIZE=1 EXPORT_NAME=PokerReplayModule` — and `static_replay.js:140` calls the `PokerReplayModule()` factory; no `onRuntimeInitialized` anywhere; ci.yml greps both sides + all five `pkr_*` symbols. `data-replay-loaded` set on the first drawn frame (`renderer.js:1585-1594`), `data-replay-error` on failure (`static_replay.js:57`). |
| 14 chrome provenance | PASS | `client/chrome.css`: cosino's 422 lines are a byte-identical prefix (diffed against the starter clone); everything after is one blank line + the fenced appended block whose content matches the design's list (scorebug auto-fit, `.seat5`/`--orange`, `.plate-name` flex, 640/400 px media rules, `--band`/`--hudscale`, `#rungchip`, `#endscreen` band anchor, `#auditcard`, all six beat-kind rules, plate/feed/endcard rows). `replay.html`/`index.html` are cosino's pages + the design-named additions (`#rungchip`, `#auditcard`, wordmark/title, appended `relayout()` block) — nothing removed. Transport: `relayout()` publishes `--band`/`--hudscale` on `document.documentElement` on load/resize/feed-toggle; `#auditcard` rides `bottom: calc(var(--band) + 10px)`; `#endscreen` keeps `bottom: var(--band)`, shown via `.show`, dismissed by **every** seek (`setIndex` → `updateEndscreen` on every index change, `renderer.js:1534-1554`); beats are labelled `<button type="button">`s seeking to their tick (`buildPokerBeats`, `renderer.js:1415-1435`) with CSS for every emitted kind (ci.yml asserts the pairing both ways). No `#viewpanel`/zoom/minimap anywhere — correct for the fixed arena. |
| 15 every drawn string fits | PASS | Both smoke invocations run with `--strict-text-bounds`; head artifacts: cert `{total: 8298, outside: 0, never_inside: 0, ellipsized: 0}`, sixmax `{total: 27029, outside: 0, never_inside: 0, ellipsized: 0}` — gated number 0, `total > 0` so the check covered real draws. Reserved band: `seatExtent` reserves `bubbleHeight(BUBBLE_LINES)` unconditionally, sized from `MaxSayLen = 120` measured in the 13 px drawing font (`renderer.js:131-138`, `types.nim:11-15`). Worst-case renderer fixture: the committed sixmax replay is a real 6-seat episode with a **server-passed-whole** 120-rune multi-byte `say` on every seat and two audit flags, driven by its own ci.yml step, self-asserting full length (`test_sim.nim:876`) and regenerate-or-fail (`:882-887`). Zero ellipsized remarks, per Addendum 3's ruling. |
| simultaneous-batch rule | N/A | Poker is sequential — exactly one acting seat per decision (`server.nim:264-302`); the design pins per-decision budgeting (§Decisions 3). The rule applies to simultaneous-decision games only. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B2 | fixed in `b6a8e9d` (0.55/0.60, 6max 14 hands) + `bba6bff` (0.56 netting) | `sim.nim:35-36` = 0.55/0.56 at head; manifest 6max `hands: 14`; ladder.md states the netting; tests moved to 14 without weakening; commit diffs match the table | yes |
| B1 | fixed in `73f2cb5` (cap 120, bubble 300×6, wrapBubble, fixture regen); CI 32996855409 then head run: sixmax `ellipsized: 0` | `types.nim:15` = 120; `renderer.js:138` = 300/6; fixture: 6 says × exactly 120 runes; head-run sixmax JSON `{27029, 0, 0, 0}` and cert `{8298, 0, 0, 0}` — the quoted numbers match the artifacts byte for byte | yes |
| fast-forward, no replay | history seeded at 7c7e77b, no rewrite | head log is `bba6bff, 73f2cb5, b6a8e9d, 7c7e77b, 94e5e00, …`; the duplicated early subjects are the known tree-identical push replay, older than this round | yes |
| NOTED residuals | test_cards' literal 160 is a generic cap, not MaxSayLen; audit.md's "3 of 30 … sixteen-hand" is a historical measurement | confirmed both readings at head (`test_cards.nim` uses 160 among 2/7/16/200 as arbitrary caps; audit.md's shipped-size sentence says 14) | yes |

## Non-blocking observations

- **O1 [timeout, pathological]** — the 429 throttle bump (`llm.nim:650`,
  `client.spacingMs += 500`, uncapped) grows the spacing floor for the rest of the
  episode, and Addendum 4's 45 s netting assumes the base 2.1 s floor. After ≥ 11
  sidecar 429s, a final decision admitted just under 672 s could push settle past 720 s
  (absolute ceiling ≈ 825 s at the 220-call budget — still ≥ 375 s inside the 1200 s
  episode timeout, so no hang and no discarded episode is possible). Reaching it
  requires the sidecar to throttle a client that is already pacing below the documented
  30 rpm cap eleven-plus times, i.e. a platform-side contract breach; the design's own
  §Degrade 5 pins the bump. Not a falsification of item 5 as operationalized by the
  amended design, but a one-line hardening (cap `spacingMs`, e.g. at 5 s) would close it.
- **O2** — reviewer N1 stands as written at head: `#endscreen`'s trailing
  `inset: auto 0 var(--band) 0` (`chrome.css:478`) cancels the `top: 0` in the same rule,
  so the endcard is content-height, bottom-anchored, not the full-height overlay the
  design sentence describes. Falsifies nothing (band anchor, `.show` class and
  seek-dismissal all hold); cosmetic.
- **O3** — `Decision.error` (reviewer N4) is still truncated-but-unrecorded at head;
  item 8's counting requirement is met by `results.fallbacks[]`. Advisory only.

BLOCKING: 0
