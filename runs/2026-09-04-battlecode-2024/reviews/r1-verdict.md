blocking: 0

# r1 verdict — battlecode-2024
Head: 5e7c8b78a09618daaec01a532dc3391cec1483c3   Checklist: /workspace/coworld-builder/prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes

Repo: Metta-AI/cogame-battlecode (MOD run; delta d2922438..5e7c8b78, 103 files, +15000/−79), judged at the
pinned checkout /tmp/bc24-judge (detached HEAD at 5e7c8b78, full history). **Provenance baseline for item 14
is the base of the bc24 delta, d2922438** (the repo's own pre-bc24 state), as the brief directs — there is
no separate starter mount for this repo. Today's `main` (4bcb8db, carrying other runs' year modules) was
NOT consulted for any claim below. CI evidence: ci.yml run **34084170288**, `main`, headSha 5e7c8b78, event
push, created 2026-09-07T04:43:37Z — inspected via `gh run view` (job/step lists) and the downloaded run-log
zip and `viewer-smoke` artifact (grep'd, cited by job file + line).

Reading order followed: checklist prompt → design note (once, in full, including the 2026-09-11 Amendments
section — noted that the code was NOT changed by it) → the diff and head (independent notes written to this
file **before** the review was opened) → r1-review.md → (after the verdict body was complete) r1-fixes.md.

---

## Refutation pass over r1-review.md (0 blocking, 7 advisory F1–F7)

I attempted to refute each finding at the current head. Verdict per finding: REPRODUCED (the observation is
true as written), DISMISSED (cannot be reproduced), or REFUTED-IN-PART (true observation, but a residual
claim in it is shown false/empty).

### F1 (canvas-text gate reports total:0; effective LLM-text gate is the fixture's DOM verdict) — REPRODUCED; its "untested board text" residue REFUTED-IN-PART
- Reproduced: `viewer-smoke.json` from the run-34084170288 artifact shows
  `canvas_text: {total:0, outside:0, never_inside:0, ellipsized:0}` on all four replay loads AND the
  fixture; `tools/ci/viewer_smoke.mjs:504` hooks `fillText`, `:811-813` gates `never_inside` only under
  `--strict-text-bounds`, `:916` names the total:0 worker/OffscreenCanvas case.
- Refuted-in-part: F1 leaves "any text the wasm renderer draws on the worker's OffscreenCanvas" as an
  unmeasured, untested class. That class is **empty**: the only canvas-drawing code in the bundle is
  `client/broadcast_core.js` (imported by the worker), and `grep -rn "fillText\|strokeText"` over
  `client/*.js`, `client/replay_broadcast.html`, `replay-viewer/static_replay*.js` returns **zero** hits;
  the bc24 atlas (`data/atlas_bc24.json`) carries duck/trap/flag/crumb sprites and no digit or glyph
  sprites; the jail-rail countdown and level readouts are DOM chrome (`#bc24-levels`, populated by the
  chrome JSON — and laid out full-cap in the fixture, `renderer_fixture.html` bc24 row). No string anywhere
  is drawn onto a canvas, main-thread or worker. The DOM verdict (below, item 15) is therefore the whole
  gate, not a partial one. I also visually inspected `viewer-smoke-replay-bc24.png` from the artifact: a
  real derived board with legible DOM chrome and full-length doctrine sentences.
- Disposition: advisory as filed; nothing blocking.

### F2 (docker-smoke substance-set drift from the design note) — REPRODUCED; disposed by note amendment
- Reproduced at head: `ci.yml` `SMOKE_REQUIRE_STATS={"ducks_spawned":10,"crumbs_spent":100,"traps_built":1,
  "damage_dealt":300}` per-seat, with `levels/healed/picked` asserted across seats in "The bc24 episode
  really played bc24", reading `.result.games[0].flags_picked_up` (a real `Bc24GameKeys` key,
  `src/battlecode/results.nim`). The design note's Amendments §1 (2026-09-11) now records exactly this, code
  unchanged. Bears on the note, not on any checklist item; the checklist-relevant facts (episode completes,
  substance floor enforced, run green) hold. Advisory; not blocking.

### F3 (three event kinds' fields differ from the design table) — REPRODUCED; disposed by note amendment; its open question SETTLED
- Reproduced at head: `src/battlecode/match.nim:160-190` — `first_action` carries `action` (a `kind` field
  would be flattened over the event kind; `tests/test_bc24_replay.nim:306-308` pins it), `setup_end`
  carries `{traps:[e.b,e.c], teleported:<int>}`, `flag_taken` has no `escort`. Amendments §2 records this;
  code unchanged. Every emitted kind has CSS and a per-game bound (test_bc24_replay Bounds table).
- The review's unverified tail (`flag_returned` alias polarity, its §Could not determine last bullet) I
  settled: the emitter passes the flag's OWNER (`years/bc24/flags.nim:143`, `ord(f.team)`), `match.nim:190`
  maps alias to `1 - e.a` — the **raiding** clan — which is consistent with the stats counter on the line
  above (`flags.nim:142`, `flagsReturned[ord(f.team.other())]`, also the raider). Attribution of a return
  to the failed raider is coherent with `flag_dropped`'s raider attribution and the design table pins no
  polarity. No defect. Advisory; not blocking.

### F4 (test thresholds differ from the note; knob deltas gated in release only) — REPRODUCED; benign
- Reproduced: `tests/test_bc24_knobs.nim:14-40` substituted thresholds with measured ranges;
  test job log (`5_test.txt:821-825`): `bc24 knob teeth: DEBUG pass — the sweep ran on 1 map(s); the signed
  deltas are gated in release` → `ok (5 checks)`, then release → `ok (25 checks)`. Both passes ran; the
  gating pass gates everything. All files are new in the range, so nothing pre-existing was loosened
  (item 1 unaffected). Survival's inverted control really ran: `5_test.txt:888-889` shows
  `-d:bc24BrokenChassis` in release followed by `bc24 survival: ok (108 checks)`. Advisory; not blocking.

### F5 (no grid-harness artefact for baseline tuning) — REPRODUCED; does not falsify item 7
- Reproduced: no tuning script/log/table in `tools/` or `docs/RULES-BC24.md`; the evidence of tuning is the
  measured-range prose in the test headers plus the committed paired-seed sweep itself
  (`test_bc24_knobs.nim` — identical seed/map/opponent, one knob low vs high, 3 seeds, thresholds in one
  table) and the survival gate with its inverted control. An absent artefact does not falsify "tuned with a
  grid harness, not guessed"; the committed sweep IS a grid harness over the knob surface, run in CI both
  passes. Advisory; not blocking. (What would upgrade this to fully settled: a committed tuning log naming
  the grid that produced the census splits.)

### F6 (`setup_end` per-game bound of 2 in a one-game test) — REPRODUCED; harmless slack
- Reproduced: `tests/test_bc24_replay.nim` Bounds table (`"setup_end": 2`) against a one-map match, while
  the emitter (`years/bc24/rules.nim`, at `currentRound == SetupRounds`) can fire at most once per game and
  the design table says 1/game. A new test's bound one looser than reachable; asserts nothing false.
  Advisory; not blocking.

### F7 (`game.docs` content `type:"uri"` vs the checklist's spelled `type:"text"`) — REPRODUCED; not blocking
- Reproduced: readme and all six pages are `{type:"uri", value:<github blob URL>}`. This is the base
  d2922438 shape; the range added the sixth page in the same shape. The operative requirement ("Manifest
  validates", both protocols, `{type,value}` docs objects) holds: the installed coworld CLI's own
  `_load_template_manifest`/`validate_upload_manifest` accepted the template in the green test job (step
  "The coworld CLI accepts the manifest template", coworld==0.1.4; wiring asserted by
  `tests/test_manifest.nim:424-430`), and the certifier accepted this shape on three shipped releases.
  Pre-existing, validated, out of the mod range's scope. Advisory; not blocking.

### Review's "Traced and consistent" section — audited
Every claim bearing on a checklist item was independently re-derived in my own pass below before I read the
review; where the review cited evidence I had not used, I re-checked it: the parity job's empty ledger and
whole-game bit-exactness (`tools/ci/parity_ledger_bc24.json` `entries: []`;
`6_parity-oracle-bc24.txt:535` "Tier A, Tier A-prime and Tier C all pass with an EMPTY ledger: every traced
game is bit-exact against the published 3.0.5 jar for all 2000 rounds"), the perf shard numbers
(`5_test.txt:841-848`, debug 5.965 s / release 0.622 s for 2000 rounds on DefaultLarge, budget 90 s), and
the survival skip-path-not-taken claim (`5_test.txt:888`). No claim in that section failed re-derivation.
The review's self-declared provenance (operator-local session) was treated as required: nothing was taken
on its word.

---

## Independent checklist pass (items 1–15 + one-batch rule) — written before reading r1-review.md

### Item 1 — CI green, no test loosened: PASS
- `gh run view 34084170288`: all 7 jobs success — test (33m7s), docker-smoke (2m46s), wasm-viewer (3m24s),
  parity-oracle, parity-oracle-bc20, parity-oracle-bc21, parity-oracle-bc24 (3m54s).
- `git diff d2922438..5e7c8b78 -- tests/`: 21 new bc24 test files (+3609 lines), 3 extended files, 0 removed.
  Every deleted line in the three extended files is a count updated to the stricter four-year form:
  test_determinism.nim (3 years → 4; explicit pairwise-distinct check replaced by an equivalent all-pairs
  loop over 4 chains), test_manifest.nim (5 pages → 6, 12 policies → 16, plus NEW cert cross-checks),
  test_viewer.nim (adds the whole bc24 block assertions + an end-to-end bc24 render). No `skip`, no
  tolerance widened, no assertion deleted.

### Item 2 — replay re-derivation, frame by frame: PASS
- `src/battlecode/replay.nim:268-277`: the Deriver's frame axis is exactly the recorded rounds
  (`frameGame`/`frameRound` from each GameHeader's `rounds`); `:301-310`: advance compares the recorded
  per-round chain and sets `mismatchRound` at the first divergent round.
- `tests/test_bc24_replay.nim:123` "re-derives with no hash mismatch" (`deriver.mismatchRound < 0`), `:218`
  "playback re-derives every recorded round", `:228-229` coverage across `capture` and the wall-clock stop;
  the runner at `:54-86` re-parses the written bytes and re-derives for every bc24 end reason.
- The viewer displays from the SAME deriver: `replay-viewer/bc_replay.nim:152-153` exposes
  `deriver.mismatchRound` as `bc_mismatch_round`; `tests/test_viewer.nim` (bc24 block at head) drives
  `newDeriver(parseReplay(...))` → `renderer.buildSessionPacket(deriver.session, ...)` end-to-end.
- CI: wasm node smoke printed `{"loaded":true,"game_version":"GV07",...,"mismatch_round":-1}` (×7); the
  parity oracle is bit-exact whole-game on 15 bot×map pairs with an empty ledger.

### Item 3 — static viewer: PASS
- `coworld_manifest_template.json:14-16`: `"replay_viewer": {"bundle": "static-replay-viewer"}`.
- `tools/build_replay_viewer.sh` present, mode 100755; `ci.yml:1384-1391` asserts presence + exec bit
  ("coworld build needs it") and `:1405` runs it.
- The bundle's only network call is the replay fetch: `replay-viewer/static_replay_worker.js:127`
  (`fetch(message.replayUrl)`); no other fetch/XHR/WebSocket in client/ or replay-viewer/ JS.
- No `/client/replay` pod path: the only grep hit is `coworld-release.yml:220`, a guard string REJECTING it.

### Item 4 — both name spaces: PASS
- Agents: `src/battlecode/decide.nim:353,366-367` — the observation carries `alias`/`opponent_alias` only;
  no real name is in the payload ("Everything this seat may legitimately know").
- Viewer: `ReplayDoc` carries `names[]` beside `aliases[]`; `src/battlecode/broadcast.nim:343,467,662,712`
  put `names` into the chrome JSON; scorebug `.plate-name` renders it (`client/replay_broadcast.html:4305`).

### Item 5 — degrade-never-hang: PASS *(categories hang/timeout — nothing found)*
- Registration wait: `src/battlecode/server.nim:239-244` — bounded by `connectTimeoutMs`, "then play anyway".
- Doctrine phase: `src/battlecode/decide.nim` — attempt1Ms/retryMs per attempt (`:505`), throttled fast-fail
  (`:564+`), no-credentials instant fallback (`:479`), timeout fallback per still-open seat (`:491-497`).
- Match: `src/battlecode/match.nim:255-266` — monotonic `matchBudgetSeconds` + per-game
  `min(perGameBudgetSeconds, remaining)`.
- The only `while true` in src/ is the heartbeat thread (`server.nim:431`), bounded by `viewersRunning`.
- Envelope: 30 (connect) + 45 (doctrine) + 340 (match) + 30 (settle) = 445 s ≤ 720 s (60 % of the 20-min
  `episode_timeout_minutes`). Perf floor measured in CI: 2000 rounds on the largest pool map in 0.622 s
  release. The CI smoke bc24 episode completed in ~22 s wall.

### Item 6 — num_agents: PASS *(num_agents)*
- Manifest: `num_agents: 2` inside all four variants' `game_config` (bc26/bc20/bc21/bc24), never at variant
  top level; `certification.game_config.num_agents: 2`; `len(certification.players) == 2 ==
  len(certification.game_config.players)` (verified by direct JSON read of the pinned tree).
- `tools/ci/docker_smoke.sh:141-227`: all four invariants with `SEAT-COUNT FAIL:` prefixes and non-zero
  exits; `SMOKE_SEATS` second declaration is the substituted default `seats_expected="${SMOKE_SEATS:-2}"`
  (`:82`), cross-checked against the manifest (`:183-184`); `SMOKE_CONFIG_OVERRIDE may not change
  num_agents` (`:199-201`).
- CI log grep (the checklist's required check): `grep -c "SEAT-COUNT FAIL"` over the full docker-smoke log
  of run 34084170288 → **0**; all four episodes logged `seats=2 ... "num_agents": 2`.
- `tests/test_manifest.nim` (head) asserts the cert/num_agents/player[] triple cross-check.

### Item 7 — scripted baseline plays full episodes legally: PASS
- Full episodes to the natural end: `tests/test_bc24_replay.nim:122` (all-scripted `playMatch`, `reason ==
  epComplete`), `:141` (scaffold mirror complete), `:274` (2000-round game complete). docker-smoke
  additionally asserts `reason == "complete"`, `fallbacks == [0,0]`, and the per-seat substance floor on a
  real container episode (green, run 34084170288).
- Legality: `tests/test_bc24_baselines.nim` (b) — every emitted action legal at the moment of emission
  (`refused == 0` against the sim's own refusal counters in `years/bc24/world.nim`), and `:88-89` no duck
  exceeds its 2 500 `DecisionOps`.
- Tuning: the committed paired-seed sweep `tests/test_bc24_knobs.nim` (identical seed/map/opponent, one
  knob low vs high, 3 seeds, all thresholds in one table, release pass gating 25 checks) plus
  `tests/test_bc24_survival.nim`'s competence gate with an inverted control that must fail
  (`-d:bc24BrokenChassis`, ran in CI). I read this as satisfying "tuned with a grid harness, not guessed";
  the absence of a separate tuning artefact is F5, advisory.

### Item 8 — LLM reply handling: PASS
- Tolerant parse: `src/battlecode/llm.nim` fence-tolerant extraction; prefill `{` re-attached (`:191-192`);
  max_tokens-cutoff detection (`:193-195`).
- Retry once: `decide.nim:505` (attempt 0 → attempt1Ms, attempt 1 → retryMs), `doctrine_retry` event with
  cause, log says "will retry" (`:557-560`); second failure → fallback sheet, `fallback[slot]` cause,
  `doctrine_fallback` event (`:531-560`, `:576`).
- Recorded for phase 60: `src/battlecode/results.nim:62-89` — `results.fallbacks` = per-seat 0/1.

### Item 9 — rune-safe truncation: PASS
- `truncateRunes`/`truncateBytes` (sim_types.nim) used for notes/motto/unknown fields/provider error text
  (`llm.nim:183` caps error bodies at MaxFallbackDetailRunes).
- `tests/test_bc24_sheet.nim:154-163`: astral-plane U+1F986 (the duck) at the cap; notes cut to 280 RUNES,
  motto to 48 RUNES; `:172+` the 16 KB byte cap cut on a rune boundary.
- `tests/test_bc24_replay.nim:244-246`: strict UTF-8/JSON parse of the written replay bytes.

### Item 10 — manifest validates: PASS *(manifest)* — with one note
- `game.protocols` carries BOTH `player` and `global`.
- `game.docs` = `{"readme":{type,value}, "pages":[{id,title,content:{type,value}} ×6]}` including the new
  `rules-bc24.md` page.
- Note (== F7): content `type` is `"uri"`, not the checklist example's `"text"`. Inherited unchanged from
  d2922438, accepted by the installed coworld CLI's `validate_upload_manifest` in the green test job, and
  certified in three prior releases of this coworld. Not a defect of this range; not blocking.

### Item 11 — viewer legible at 360 px: PASS
- `client/replay_broadcast.html:2571`: `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }`.
- `:2647-2650`: `@media (max-width: 640px)` hides `.plate-sub` and shrinks labels.
- The viewer smoke measures at 360/720/1280 px, FIT + 2×, on the bc24 replay too — `killfeed_overlap` in
  `viewer-smoke-replay-bc24.json` (artifact of run 34084170288) shows `width:360 ... ok:true, year:'bc24'`;
  the renderer fixture also runs its bc24 row at 360×640 and passed.

### Item 12 — release order and scaffold: PASS *(manifest)*
- `coworld-release.yml` step order verified by line: Build the Coworld manifest (168) → Certify locally
  (182) → Upload the policies (225) → Upload the Coworld (323) → Wait for canonical (361) → Put the Coworld
  secret (419).
- All three workflows present (`ci.yml`, `coworld-release.yml`, `coworld-submit.yml`);
  `tools/ci/docker_smoke.sh` mode 100755.
- `tools/ci/policies.json`: 16 policies, four per year; the bc24 set is 2 `PLAYER_PROMPT` champions
  (fortress, flagrush) + 2 scripted fillers (gone-sharkin, examplefuncsplayer24); champion #2
  (`battlecode-bc24-flagrush`, the second bc24 `PLAYER_PROMPT`) carries
  `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` (index 13; the bc26/bc20/bc21 champions #2 carry it
  too, indices 1/5/9).
- Placeholder gate run by me at head: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the five named files → no
  matches (gate exits 0). Three names only, per the checklist; the documented `<cow_id>`/`<sha>`/
  `<run_id>`/`<name>:vN` residue was not filed.
- Smoke freshness: docker-smoke builds the image in-job before its episodes; wasm-viewer builds the bundle
  in-job and `needs: docker-smoke` (`ci.yml:1368`), consuming that same run's replay artifact.

### Item 13 — viewer executes: PASS *(static-viewer)*
- Job `wasm-viewer` (101625414818) green at 5e7c8b78 INCLUDING the step "Load the bundle in a real browser
  (ALL FOUR years' replays)" (Playwright pinned 1.55.0, headless chromium, loading docker-smoke's replays);
  `needs: docker-smoke` (`ci.yml:1368`); the only `continue-on-error: true` in ci.yml (`:623`) is the bc20
  parity job's informational "engine-from-source attempt", not any smoke step. Log: four
  `{"loaded":true,...}` lines with three differing clock readouts each, `scrub_selector == "#scrub"`
  asserted via jq, endcard `shown=true` with a clan line after the 100 % seek; bc24 ran at
  `--timeout 120 --soak 15` as the design pins.
- Markers: `replay-viewer/static_replay.js:180` sets `data-replay-loaded="true"` in the worker's `loaded`
  message handler (first composited board frame; rAF starts on the next line); `:14-20` sets
  `data-replay-error="<message>"` on failure. Both in the shell's own code paths.
- Lobby: not reachable in this format — the frame axis is built exclusively from recorded game rounds
  (`replay.nim:270-277`); pre-match doctrine events carry `ms`, never frames, so playback opens at game 0
  round 1 by construction and every seek stays on the round axis. A late-gameStart probe cannot be recorded
  by this recorder; the requirement is satisfied structurally (and the smoke's three differing clocks +
  soak advancement show playback really moves from the first tick).
- Link flags vs bootstrap, same starter: `replay-viewer/config.nims:43-53` has NO
  `MODULARIZE`/`EXPORT_NAME`; the worker bootstrap is the matching global `var Module = {}` +
  `Module.onRuntimeInitialized` + `importScripts('./bc_replay.js')` (`static_replay_worker.js:8,218,274`).
  Neither file changed in the range (`git diff --name-only` shows no replay-viewer/ or Dockerfile change),
  and the smoke's `loaded: true` ×4 is the executing evidence, per the checklist's own rule that file
  presence is not evidence here.

### Item 14 — chrome is the starter's: PASS *(static-viewer)*
Provenance baseline: d2922438 (the repo's own pre-bc24 state), per the brief.
- `client/chrome_common.js` and `client/broadcast_core.js`: ZERO diff in the range (byte-identical to
  base); `tests/test_viewer.nim` additionally sha256-pins both against the coworld-ctf copies.
- `client/replay_broadcast.html`: +514/−3. The three deletions are named, minimal in-place patches: the
  `--statrail` measured-set array gains `'bc24-crumbs', 'bc24-levels'`, and the two year-gate conditionals
  `if (!isBc20 && !isBc21)` gain `!isBc24`. Everything else is the bc24 game block appended under the
  banner "BC24 additions to the inherited cogame-battlecode chrome" (asserted by test_viewer at head).
  Inherited CSS sections 1–5 untouched (endcard 1847-1908, killfeed 1255-1270, beat kinds 1717-1732,
  plate-name 2571, 640 px query 2647 all above the first bc24 hunk).
- Transport rules: (a) `relayout()` sets `--hudscale`/`--band`/`--statrail` on
  `document.documentElement.style` (page `:4520,4526-4528`) — `:root`, not `#stage`; (b) `#killfeed`
  bottom is `max(calc(76*var(--u)), calc(var(--band,0px) + var(--statrail,0px) + 8px))` (`:1269-1270`);
  the bc24 boxes ride `var(--band, 0px) +` offsets (test_viewer asserts per panel); (c) `#endcard` keeps
  `bottom: var(--band, 0px)` (`:782`), shown via `classList.add('on')` (`:4512`) matching `#endcard.on`,
  and `dismissEndcard()` fires on scrub seek (`:4292`), every transport button except loop/skip (`:4563`),
  keyboard except r/f (`:4591`), and all three year-block bridges (`:4218,4228,4238`); (d) beats:
  `buildBc24BeatButtons` (own name, no shadowing — test_viewer counts function definitions), labelled
  `<button>`s seeking to their tick, CSS for all 12 emitted kinds, the 5 new ones scoped to
  `html[data-year="bc24"]`.
- `#viewpanel` KEPT, correctly: the bc24 pool tops out at 59×31 → 944 px native vs the 360 px frame; the
  design note pins keeping it. Not a violation of the remove-if-fits rule.

### Item 15 — every drawn string fits its frame: PASS *(legibility)*
- Architecture fact (verified, not assumed): there is NO canvas text in this viewer — zero
  `fillText`/`strokeText` in client/*.js, replay_broadcast.html, static_replay*.js (the worker draws via
  broadcast_core.js, which contains none), and no digit/glyph sprites in the bc24 atlas; every string
  (scorebug, feeds, doctrines, notes, motto, endcard, jail rail) is DOM. So `canvas_text.total == 0` in
  every viewer-smoke.json (checked in the run-34084170288 artifact: replay, bc20, bc21, bc24, fixture — all
  `{total:0, outside:0, never_inside:0, ellipsized:0}`) is the true "no canvas text exists", not a blind
  instrument; the DOM checks below are the operative text gates.
- `--strict-text-bounds` deliberately dropped on the four replay loads (pannable board — `#viewpanel`
  kept; ci.yml carries the explanatory comment) and the counts are still recorded — exactly the
  checklist's pannable-board branch.
- Worst-case renderer fixture (the CI-replay-cannot-talk hole): `tools/ci/renderer_fixture.html` — one row
  per year incl. bc24 (`YEARS = ['bc26','bc20','bc21','bc24']`), full-cap strings (notes exactly 280 runes
  incl. astral plane, motto exactly 48 — self-asserted at `:158-159` and re-asserted full-length AFTER
  render at `:452-457`), all four years' own panels populated (bc24-flags/levels/crumbs/doctrines with
  full-cap doctrine words), at 360/720/1280 px, in the page's own CSS extracted from
  client/replay_broadcast.html (log: "page_styles.css: 152354 bytes"); its verdict measures EVERY element
  under #chrome — nothing may leave the frame, nothing may hide its own text (scrollWidth/Height,
  `:423-430`) — and sets `data-replay-loaded`/`data-replay-error` itself. Driven by
  `viewer_smoke.mjs --strict-text-bounds` in its own ci.yml step ("Render the full-cap doctrine-text
  fixture", green in 34084170288, `{"loaded":true,"ms":377}` / `canvas text: 0 drawn ... 0 ellipsized
  (--strict-text-bounds)` — the cited canvas_text line; the DOM verdict is what the step gates).
- Reserved band: `#bc24-doctrines` body is capped and scrolls, positioned `bottom: calc(var(--band,0px) +
  8px)`; no text is laid out relative to a board entity (no speech bubbles in this game), so the
  cogchemists geometry cannot occur.
- The repo draws LLM-authored text (notes/motto/doctrine words) and DOES ship the worst-case fixture the
  checklist demands, in its own CI step, asserting its own strings full-length. The fixture is DOM-shaped
  because the text is DOM-drawn; there is no `client/renderer.js` in this lineage and no canvas string for
  `canvas_text` to count. I judge the item's intent met; the literal-instrument gap is F1, advisory.

### One-batch rule (simultaneous-decision): PASS
- One decision turn per episode; both seats' calls go out as one batch:
  `src/battlecode/decide.nim:523` `client.curl.makeRequests(batch, ...)` over all open seats per attempt
  (`:507-523`). The retry batch likewise batches all still-open seats. No sequential per-seat calls.

---

## Standing blocking findings

None. Every checklist item verified from the tree, the CI logs of run 34084170288, or the run's artifacts;
nothing was left unverifiable.

## Non-blocking observations
- (== F7 / item 10 note) `game.docs` content `type: "uri"` vs the checklist example's `"text"` — inherited,
  CLI-validated, certified three times; out of the range's scope.
- docker-smoke annotations "SMOKE_CONTRACT_PROBE=0: the certification contract was NOT checked" ×3 are the
  designed shape: the probe runs on the first (bc26 certification-fixture) episode; episodes 2–4 skip it
  and say so loudly.
- In the endcard state of the bc24 CI screenshot (`viewer-smoke-replay-bc24.png`, 1280 px), the
  `#bc24-flags` pill partially overlaps the clock caption ("FINAL — MATCH OVER" reads through the pill's
  edge). Cosmetic, endcard-only, at desktop width; the smoke's obscured/overlap gates passed and no
  checklist item names it. Worth a look in phase 60's screenshot review.
- The beat-marker seek-vs-position formula divergence the review notes (`(b.t - st)/span` vs `b.t/span`) is
  inherited, identical across all four year blocks, and moot while `st = 0` in this format — agreed with
  the review that it is unobservable here.

## Fixer report audit

Read only after the verdict body above was complete. `r1-fixes.md` records: no code commit in round 1 —
each of F1–F7 disposed as observation/documentation, with the design note amended (Amendments §1 ↔ F2,
§2 ↔ F3) rather than the code changed.

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| F1 | no code change; fixture's DOM verdict is the gate | canvas-text class is empty (zero fillText anywhere); DOM verdict + full-length asserts present and green | yes |
| F2 | note amended (Amendments §1), code right | ci.yml substance set + across-seats step match the amendment; ran green | yes |
| F3 | note amended (Amendments §2), code right | match.nim:160-190 fields match the amendment; test pins first_action; flag_returned polarity settled coherent | yes |
| F4 | no change; release pass gates | log: debug 5 checks (sweep smoke), release 25 checks (gating); inverted control ran | yes |
| F5 | no change; advisory | absence confirmed; committed sweep + inverted control read as the harness; does not falsify item 7 | yes |
| F6 | no change; harmless slack | bound 2 vs emitter max 1 confirmed; asserts nothing false | yes |
| F7 | no change; inherited validated shape | CLI validation step green; shape pre-dates range | yes |

BLOCKING: 0
