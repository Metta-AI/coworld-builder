blocking: 0

# r1 verdict — cooperative-hunting

Head: `80e2acf36048e0ffd9deb73592580f7d3d005f5c` (main, cloned fresh to `/tmp/judge-cogame-cooperative-hunting`)
Checklist: phase-30 acceptance checklist (items 1–15 + simultaneous-decision rule), quoted verbatim in the judge brief
Independent read written before reading fixes: **yes** — the repo tree, design note, CI run 32792004269 and its logs, the starter diffs, and every checklist item were evaluated before `r1-fixes.md` was opened. The review `r1-review.md` was read after my own read of the tree, per the binding order.

The review was written at `10564b04`; 21 commits landed since (`10564b04..80e2acf3`). Most of its findings
are therefore **fixed since**, not wrong — I distinguish the two below.

---

## Review findings — refuted / fixed-since / confirmed

### B1 — no `--strict-text-bounds`, stale `viewer_smoke.mjs` → FIXED SINCE (commit `d82261a`)
- True at 10564b04; false at head. `.github/workflows/ci.yml:317-322` now invokes
  `viewer_smoke.mjs … --soak 10 --strict-text-bounds`; `tools/ci/viewer_smoke.mjs` is 709 lines and
  carries the `fillText`/`strokeText` hook (`viewer_smoke.mjs:115-132, 323-370, 414`), the
  `--strict-text-bounds` arg (`:173`), and the gate `if (args.strictTextBounds && canvasText.never_inside > 0)`
  (`:601-603`). CI run **32792004269** log, `Load the bundle in a real browser`:
  `canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.
  Not standing.

### B2 — no worst-case renderer fixture for LLM-authored text → FIXED SINCE (commits `2ed3fce`, `34212ee`, `b55fc2f`)
- True at 10564b04; false at head. `tools/ci/build_worst_case_fixture.sh` (mode 100755),
  `tools/ci/fixtures/{worst_case_harness.html, fixture_chrome_driver.js, fixture_core_stub.js,
  worst_case_chrome.json}` exist; `ci.yml:346-358` runs `Build the worst-case renderer fixture` and
  `Render the worst case…` with `--strict-text-bounds` as their own steps, both `success` in run
  32792004269. The harness loads the **real** page (spliced from `client/replay_broadcast.html` exactly
  as `Dockerfile.replay-viewer` splices the bundle) in three real-viewport iframes at 360/640/1280 px
  (`worst_case_harness.html:47-51`), hands each a frame with a full-cap 120-rune remark on all six
  seats (latin/CJK/emoji), and the driver asserts every string is **full-length**
  (`fixture_chrome_driver.js:59-67`: `if (got !== want) failures.push(… 'is not the full-length string')`),
  un-ellipsized, inside its box/frame/bands, visible after the entrance animation settles, and that a
  repeated frame does not rebuild the rows (node-identity check, `:306-318`). It sets
  `data-replay-loaded` only when all three frames pass and `data-replay-error` otherwise
  (`worst_case_harness.html:118-123`), so `viewer_smoke.mjs` turns a clipped remark red.
  `tests/test_chrome.nim` §`worstCaseFixtureIsReachable` feeds the fixture back through the real
  `buildChromeLabel` and asserts byte-equality, so the fixture cannot drift short. Not standing.

### B3 — configured waits sum to 824 s > 60 % of 1200 s → FIXED SINCE (commit `e0f21ff`)
- True at 10564b04 (`playerConnectTimeoutSeconds` 120, `playBudgetSeconds` 660); false at head.
  `src/cooperative_hunting/sim_types.nim:543-544`: `playBudgetSeconds: 600`,
  `playerConnectTimeoutSeconds: 45`, with the sum documented in place (`:537-542`):
  45 roster + 0.5 registration grace + 600 deadline guard + 24 LLM-thread join (2 × 12 s batch
  deadline) + 20 shutdown grace = **689.5 s = 57 %** of 1200 s, inside the 720 s rule. The manifest
  schema defaults agree (`coworld_manifest_template.json:137` `"default": 600`, `:144` `"default": 45`).
  I re-traced every bound myself — see checklist item 5 below. Not standing.

### B4 — no frame-by-frame reproduction test → FIXED SINCE (commit `591f8f1`), and the re-derivation shape is the strongest the format admits
- True at 10564b04; false at head. `tests/test_replay_parse.nim:131-202`:
  `reDerivationMismatch` parses the replay a real offline episode wrote, rebuilds a `SimServer` per
  tick via the viewer's own `initSimFromDoc` + `applyTick`, re-records each tick with the **same
  `ReplayWriter` the live server uses**, and asserts the re-derived tick object equals the recorded
  one **field for field on every tick** (`if derived != recorded: return "tick index …"`), including
  the `q`/`c` omit-when-unchanged compression; run on staghunt (§`viewerReproducesEveryFrame`) and on
  predator-prey (§`viewerReproducesEveryFramePredatorPrey`, where roles and the tall-grass flag are
  re-derived, not read back). On the fixer's extra claim, judged with my own eyes: the format records
  per-tick **state**, not inputs (`replay.nim`; `cooperative_hunting_replay.nim:207-210`
  `chMismatchTick` = −1 "recorded state, not recorded inputs"), so `sim.step()`-replay is not
  available; the strongest property the format admits is exactly this lossless per-tick round trip,
  and it is complemented by the determinism test (`tests/test_step.nim:252` — two 500-tick runs, same
  seed + input script, identical state digest), which pins the sim side. The viewer derives display
  from that same re-derivation: `cooperative_hunting_replay.nim:147-148, 162-163, 176-177` call
  `game.applyTick(doc, cursor)` then `renderCurrent()` → `game.buildGlobalFrame(...)`
  (`:125`) — the same proc the live server calls (`cooperative_hunting.nim:1032`), no parallel sprite
  recording. Item 2 is satisfied; the commit also restored the dropped `pushStep` flag the new test
  caught. Not standing.

### Non-blocking findings N1–N20 — status at head
- **Fixed since** (verified in the tree, not from the table): N2 (`llm.nim:491-513` — all four
  `parsePlan` caps are `runeCap` now), N3 (`replay_broadcast.html:1687` `chromeCommon =
  window.ChromeCommon({...})`; transport/chips/tick-clock owned by chrome_common, asserted by the
  fixture's `measureTransport`), N5 (`09b55a0`; fixture `measurePlates` gates plate spill at three
  widths; run 32792004269 scorebug carries whole names/scores), N6 (`MaxChromeLabelBytes = 12288`,
  `sim_types.nim:205`; `tests/test_chrome.nim` §`manifestLengthEpisodeKeepsEveryBeat` — 150 beats +
  six full-cap CJK remarks fit, beat at tick 0 survives), N7 (`certification.game_config.tokens` =
  six empty strings, manifest `:560-567`), N9 (`MaxObservationRunes = 2000`, `sim_types.nim:219`;
  `observationFor` caps the whole string, `llm.nim:416-422`), N10 (`tests/test_llm_retry.nim` — a
  local Bedrock stub drives the real transport; exactly two requests on retry, never three),
  N11 (`cooperative_hunting_player.nim:34-35, 306-313` — 5 s per read, 120 s idle cap, exit 0),
  N12 (`:66-70` — `PLAYER_SCRIPTED` wins when no prompt), N13 (`#bannerlane` back at `:1185`),
  N14 (`results.plan_turns_skipped`, `cooperative_hunting.nim:356`; asserted in `test_scoring.nim:205-207`),
  N15 (`replay.nim:196-197` `closedRoster`/`focusElephant`; asserted in `test_replay_parse.nim:60-64`),
  N16 (variant/cert `players[]` are `Hunter 1..6`, not aliases), N18 (`wireTransport` delegates the
  glyph to chrome_common's `renderTransport`; the fixture asserts the play arrow is absent during
  playback), N20 (`llm.nim:405-409` — one `\n  `-prefixed line per RECENT entry).
- **N8 refuted by the fixer — refutation is sound.** `(rounds × ticksPerRound) div planIntervalTicks`
  counts dispatch boundaries at `tickCount mod 120 == 0` during play (`cooperative_hunting.nim:1036-1038`);
  for 3 × 960 that is 8 per round = 24. The design note's "25" counts a boundary at the end of the last
  round that the loop never reaches. The code is right; nothing gates on the number.
- **Confirmed still true at head, correctly non-blocking:** N1 (`captureRule` assigned at
  `sim.nim:407`, never read by resolution — equivalent by construction since the variant fixes which
  entity kinds exist; no checklist item), N4 (`relayout()` at `replay_broadcast.html:1700-1723` is a
  rewrite, but 14(c)'s actual requirement is met: it measures `#transport`, sets `--band` and
  `--hudscale` on `document.documentElement`, and the game block only reads them), N13b (starter beat
  CSS `.kill/.steal/.return/.capture` survives as dead rules `:583-598` — deleting it would be an
  unlisted removal; 14(d)'s failure mode is the reverse and all five emitted kinds have CSS),
  N17 (`/client/replay` literal at `broadcast_core.js:196` is inside the **byte-identical** starter
  file item 14 requires; no such server route exists — `isStaticRoute`, `cooperative_hunting.nim:702-709`,
  serves only player/global/snappy; `runReplayServer` absent), N19 (0 % scrub probe again returned the
  pre-scrub clock in run 32792004269 — `0%="… 244 / 960"` — a harness-timing artifact in the template,
  which this repo must carry verbatim; the three-distinct-clocks assertion passed: 244/498/960).

---

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. CI green, no test loosened | PASS | `gh run list -w ci.yml --branch main`: run **32792004269**, `success`, headSha `80e2acf3…`; jobs test/docker-smoke/wasm-viewer all green; all 9 `tests/*.nim` ran twice (18 × "all checks passed" in the log; `NIM_TESTS` vars unset). `git log -p --since=2026-08-24T15:22:30Z -- tests/`: additions throughout; the only deletions are in `1277a4f` and are message/comment rewordings ("at most 4 KB" → "inside the label cap") whose assertion `label.len <= MaxChromeLabelBytes` is retained and joined by stronger new blocks; no skip/xfail/removed file (grep over the hunks: none). |
| 2. Replay re-derivation, frame by frame, test asserts | PASS | `tests/test_replay_parse.nim:131-202` (field-for-field per-tick equality via the viewer's own `applyTick` + the live writer, staghunt + predator-prey); viewer display from the same re-derivation: `cooperative_hunting_replay.nim:147-148,125`. See B4 above for the state-not-inputs judgment. |
| 3. Static viewer | PASS | `coworld_manifest_template.json:31-33` `"replay_viewer":{"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, asserted `-x` and invoked by path in `ci.yml:225-249`; only egress is `fetch(message.replayUrl)` (`static_replay_worker.js:111`) with `websocket: false` (`:86`); no `/client/replay` route in `src/` (`isStaticRoute`, `cooperative_hunting.nim:702-709`; the one literal is inside the byte-identical starter `broadcast_core.js:196`, dead code — see N17). |
| 4. Both name spaces | PASS | Aliases: seeded permutation (`sim.nim:425-435`); observation and `with[]` carry aliases only (`llm.nim:294-314, 501-508`); `buildPlayerFrame` emits no name string and no chrome sprite (`frames.nim:457-490`). Viewer maps alias→real name: chrome seats carry both (`frames.nim:532-533`), page renders `.plate-alias` + `.plate-name`; live in run 32792004269: `"Cog-B cooperative-hunting-prompt 0 Cog-C cooperative-hunting-prompt 8 Cog-A big_game_hunter 2 …"`. |
| 5. Degrade-never-hang, ≤ 60 % of 1200 s | PASS | Every wait bounded: roster deadline 45 s (`cooperative_hunting.nim:936-953`), `sleep(500)` registration grace, LLM on its own thread with `curly.makeRequests(batch, 12 s)` polled via `tryRecv` (`llm.nim:622`, `cooperative_hunting.nim:469-475`), wall-clock guard `playBudgetSeconds` 600 → `reason: deadline` (`:593-604`), player binary reads bounded 5 s / 120 s idle (`cooperative_hunting_player.nim:34-35,306-313`), `no_players` writes zero results and exits 0 (`:955-961`), join after "quit" bounded by the batch deadline, 20 s grace then `quit(0)`. Sum 689.5 s = 57 % < 720 s (`sim_types.nim:537-544`). |
| 6. `num_agents` everywhere + smoke invariants | PASS | `num_agents: 6` in all four variants (manifest `:450, 483, 516, 549`) and in `certification.game_config` (`:588`); `len(certification.players)` = 6 = `len(certification.game_config.players)`; `docker_smoke.sh:110-151` enforces all four invariants with `SEAT-COUNT FAIL` prefixes before any container starts; `SMOKE_SEATS` default 6 substituted at `:54` is the independent second declaration. `grep -c 'SEAT-COUNT FAIL'` over the run-32792004269 log → **0**; smoke line: `smoke OK: seats=6 … reason=complete`. |
| 7. Scripted baseline full legal episodes | PASS | `tests/test_episode.nim:21-105` — six scripted seats to the natural end, `reason == complete`, all four variants; `tests/test_baseline_orders.nim:96-150` — all eight baselines, 2000 ticks, ≤ 1 direction bit, no undefined bit, ≤ 0x7f, ≤ 1 mask/tick, never an unpayable move, every 0x90 body ≤ 4096 B valid UTF-8 JSON. Tuning: the parameters are staghunt's own, produced by that repo's `balance_sweep.sh` grid harness (5 rosters × 3 seeds; `.claude/skills/stag-hunt-balance/SKILL.md:19-29` documents it) and pinned "not retuned in v1" by the design note — inherited from a grid, not guessed. |
| 8. LLM reply handling | PASS | Tolerant extraction of the first balanced `{…}` (`llm.nim:435-469`); exactly one retry (`for attempt in 0 .. 1`, `:607`), retry hint appended, `stillOpen` only; fallback recorded — `fallback` event with cause + `results.fallbacks[slot]` (`cooperative_hunting.nim:520-536`). Driven end-to-end by `tests/test_llm_retry.nim` against a local stub: exactly 2 requests on one bad reply, exactly 2 (not 3) on two bad replies. |
| 9. Rune-safe truncation | PASS | One helper `runeCap` (runeSubStr) applied to say/note (`llm.nim:510-511`), all four parsePlan caps (`:491-513`), prompt, names, error strings (`:633`); `tests/test_replay_parse.nim:92-129` feeds a 4-byte rune at the 120-cap boundary, asserts runeLen == cap, `validateUtf8 == -1`, survives the writer round trip. |
| 10. Manifest validates | PASS | `game.docs` = `{readme:{type,value}, pages:[{id,title,content:{type,value}}×4]}` (manifest `:325-363`); `game.protocols` carries both `player` and `global` as `{type,value}` objects (`:315-324`). |
| 11. Legible at 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }` (`replay_broadcast.html:1042`); labels hidden under 640 px (`:1130-1133` `#speedchips .chip-label, .tbtn .label { display: none !important; }`). Beyond the letter of the rule, the worst-case fixture renders a real 360 × 640 viewport and gates plate/feed/transport containment there (run 32792004269 green). |
| 12. Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (`:153`) → Certify (`:167`) → Upload the policies (`:206`, "BEFORE upload-coworld") → Upload the Coworld (`:304`) → Put the Coworld secret (`:342`, "AFTER"); all three workflows present; `docker_smoke.sh` mode 100755; docker-smoke builds the image and smokes it in the same job, wasm-viewer `needs: docker-smoke` and builds its bundle in-run. `policies.json`: 4 distinct policies, champions #1/#2 both `PLAYER_PROMPT`, #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, 2 scripted fillers. Placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five files → no matches, exits 1 → gate passes (ran it). |
| 13. Viewer executes | PASS | (a) run 32792004269 `wasm-viewer` green **including** `Load the bundle in a real browser` (step ran, no `continue-on-error` anywhere in ci.yml, `needs: docker-smoke` at `:212`); log: `{"loaded":true,"ms":296,…}`, soak `2/1039 → 194/1039 → 242/1039`, three distinct scrub clocks. (b) `data-replay-loaded` set inside the worker's `loaded` branch (`static_replay.js:124`) with the bridge `ready` posted immediately after (`:131`); `data-replay-error` in `showFailure` (`:44`). (c) `config.nims` has **no MODULARIZE, no EXPORT_NAME** (`:34-38`) and the worker waits on `Module.onRuntimeInitialized` — both halves from coworld-ctf, renamed `ctf_*→ch_*` on both sides together; every worker-called symbol is in `EXPORTED_FUNCTIONS` (`config.nims:50`) and `exportc`'d (`cooperative_hunting_replay.nim`). |
| 14. Chrome is the starter's | PASS | (a) `client/chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diff empty; ran it), `broadcast_core.js` likewise. (b) The page reproduces from the starter via `tools/build_replay_page.py`; my own diff of everything above the CSS banner (`:958`) against the starter shows exactly two added lines — the `<title>` and the `#killfeed`→`#feed` comment rename — plus the note's listed removals; sections 1/3/5/6 intact; the 1728-vs-4165 line count is the starter's ctf-specific JS, replaced under the second banner (`:1277`), not a CSS/markup rewrite. (c) `relayout()` measures `#transport`, sets `--band`/`--hudscale`/`--topband` on `document.documentElement` (`:1700-1723`); `#feed` rides `bottom: calc(var(--band,0px)+…)` (`:969`); `#endcard { bottom: var(--band,0px) }` (`:1116`), shown via `#endcard.on` (`:704`), and **every** seek path goes through `seekTo` whose first act is `hideEndcard()` (`:1529-1537`; scrub `:1628`, beats `:1466`, buttons `:1602-1605`, keys `:1636-1638`); beats are labelled `<button>`s with `textContent`, `title`, `aria-label` that seek (`pushHuntBeat`, `:1452-1470`), CSS for all five emitted kinds (`:1108-1112`) and only those five are emittable (`frames.nim` LegalBeatKinds). The starter's own `markBeat` produces unlabelled non-seeking divs, so the page's labelled-button implementation exceeds the helper the checklist parenthetically names; chrome_common is genuinely instantiated (`:1687`) and owns the transport. (d) `#viewpanel`/zoom/minimap removed entirely — no markup, no CSS, no `attachMinimap` call (grep: absent), matching the fixed 32×32 always-fully-drawn board. |
| 15. Every drawn string fits its frame | PASS | `viewer_smoke.mjs` reports `canvas_text {total, outside, never_inside, ellipsized}` (`:348-350`); ci.yml's smoke step carries `--strict-text-bounds` (`:322`) and run 32792004269 printed `never_inside: 0`. `total: 0` is genuine, not a hole: the board is drawn by BroadcastCore in an OffscreenCanvas worker and every string this viewer draws is DOM text — which is exactly why the **worst-case renderer fixture** exists as its own ci.yml step (`:349-358`, `--strict-text-bounds`, run green), loading the real renderer with a full-cap remark on every seat at once at 360/640/1280 px, asserting its own strings are full-length (`fixture_chrome_driver.js:59-67`) and reporting failure as `data-replay-error`. The `#feed` band is sized from the server's 120-rune cap with wrap (`replay_broadcast.html:966-991` + the comment naming `MaxSayRunes`); names may ellipsize (labels), remarks may not and the fixture asserts they don't. Fixture step log: `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)`, `loaded: true`. |
| Simultaneous batch | PASS | One `curly.makeRequests` batch per planning turn (`llm.nim:614-622`: build `RequestBatch`, single `makeRequests` call); dispatched once per 120-tick boundary (`cooperative_hunting.nim:1036-1038`); no per-seat sequential call anywhere; a batch still in flight skips the turn and is counted (`plan_turns_skipped`). |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed `d82261a` | flag + 709-line template + `never_inside: 0` in run log | yes |
| B2 | fixed `2ed3fce`+`34212ee`+`b55fc2f` | fixture files, ci steps green, full-length + node-identity assertions read | yes |
| B3 | fixed `e0f21ff` | 45/600 defaults, 689.5 s = 57 % re-derived myself | yes |
| B4 | fixed `591f8f1`, limit stated | test read in full; state-not-inputs limit judged sound (see B4) | yes |
| N2,N3,N5,N6,N7,N9,N10,N11,N12,N13,N14,N15,N16,N18,N20 | fixed | each verified at file:line in the tree (list above) | yes |
| N8 | refuted | formula = boundary count; note off by one; sound | yes |
| N1,N4,N13b,N17,N19 | not fixed, reasons | each reason checked; none maps to a checklist item | yes |

## Non-blocking observations (mine, not tied to a checklist item)

1. **Doc drift from the N6 fix:** `MaxChromeLabelBytes` is now 12288, but `game.protocols.global`
   (manifest `:322`) and the `protocol.md` docs page (`:352`) still say the chrome label is "at most
   4 KB". The wire format (u16 length) accommodates 12 kB and no checklist item gates the doc text,
   but the protocol page now understates the cap threefold. Worth a one-line manifest edit in a later
   round.
2. The 0 % scrub probe again equalled the pre-scrub clock (N19) in run 32792004269 — a template
   harness quirk, upstream of this repo.
3. `tools/build_replay_page.py:757` reads the starter from `/workspace/starters/coworld-ctf` by
   default — reproducibility of the page depends on that mount; fine for provenance audits, inert at
   runtime.

## Verdict

All four blocking findings from r1 were real at the review sha and are fixed at the current head; the
one refutation (N8) is correct; the five deliberate non-fixes are justified and none touches a
checklist item. My independent pass over all 15 items plus the batch rule finds nothing standing.

- (no blocking items)

BLOCKING: 0
