blocking: 0

# r1 verdict — 2026-08-25-daycare

Head: `948d5de5ca5d9a09b612b5eca0fea922cb8cc853` (`main`, verified `git rev-parse HEAD` and
`gh api .../runs/32859893259 → head_sha 948d5de…, conclusion success`)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15
+ the simultaneous-decision addendum, read in full at lines 70–233)
Independent read written before reading fixes: **yes** — and before reading the review. I read the
checklist, the design note, and the repo (sim, kernel, server, llm, player, replays, viewer files
diffed against `/workspace/starters/coworld-ctf`, manifest, workflows, tools/ci, all nine tests) and
pulled the CI logs for run 32859893259 before opening `r1-review.md`, and finished auditing the
review's findings at head before opening `r1-fixes.md`.

## Standing blocking findings

None. Every checklist item passes at the current head with evidence cited below, and the review's
one blocking finding is fixed at head.

## Refuted / resolved

### B1 — `config_schema` caps `tokens`/`players` at 1 in a two-seat game → RESOLVED AT HEAD (was true at 12d58b5)
- Evidence: `coworld_manifest_template.json` at 948d5de — `"tokens": {…"minItems": 1, "maxItems": 2…}`,
  `"players": {…"minItems": 1, "maxItems": 2…}` (verified by parsing the JSON; both descriptions now
  read "Daycare seats two."). The fix commit is `b9bab64`; `git diff 12d58b5..948d5de` shows exactly
  the two `maxItems: 1 → 2` changes.
- New enforcement: `tests/test_manifest.nim` block "config_schema admits every game_config this file
  ships" (+41 lines, the only net `tests/` change this round) asserts
  `tokens/players.maxItems == num_agents.maximum (== 2)` and walks all four variants, the
  certification fixture and the runner-injected `{tokens, players}` shape against the declared
  `minItems..maxItems`. Green in run 32859893259 (`test` job 97841306518).
- A finding that was true and has since been fixed is refuted as *standing*; it counts zero.

### N5 — `secret.pref` on the live `/global` frame → REFUTED as a checklist violation
- I verified the code does what the review says (`src/daycare/broadcast.nim` appends
  `state["secret"]` to the live chrome frame; `server.nim` `globalUpgrade` takes no token). But the
  design note *specifies* this exact behaviour (`design.md` §Viewer "Broadcast frame contract" lists
  the appended `secret` block; the route table pins `WS /global` token-free; the idea's replay plan
  is a real-time spectator reveal), and no checklist item covers a spectator-channel leak — item 4
  (name spaces) is about aliases vs player names and is satisfied. The player-protocol frames and
  `final` carry no preference (`sim.nim playerStateJson`, `server.nim finishEpisode`,
  `tests/test_noleak.nim`). The reviewer filed it non-blocking; I concur. Residual risk (a policy
  image opening `/global` mid-episode) is a design call, not a defect against this checklist.

## Non-standing but real (advisory residue at head — no checklist item falsified)

- **N4 (rngSecret → pickRng seeding) stands at head, advisory.** `sim_state.nim:110-112` still seeds
  `pickRng` from `rngSecret.nextU64()` after the preference/switch draws, and the module docstring
  still self-contradicts ("the picks" vs "nothing the parent can observe is ever drawn from
  rngSecret"). No information leaks — `rand(2)` consumes one draw whatever it returns, and with
  `forcePreference` the draw is skipped for both branches, so pick outcomes are independent of the
  preference *value* given the seed. The attempted fix (`79a5a66`) demonstrably fails feasibility
  gate (c) (run 32858536635: pooled accuracy 0.672 vs band 0.35..0.65) and was reverted
  (`948d5de`). No checklist item names the RNG-stream separation; this is a design-note question
  (fix the docstring or re-derive gate (c)), not a blocking finding. Category would be: correctness.
- **N6 (bare-tall-tree reach emits nothing) stands at head, advisory.** `sim.nim:109-117` skips
  `ripe < 1` sources, so a child `show`/`seek` pick at an empty canopy degrades to `wait` with no
  `reach` row and no counters, while `kernel.nim` walks the child there (`requireRipe = false`).
  Deviates from the design note's "always fails and emits `reach`", but tall trees refill every 24
  ticks so the silent window is short, adjacency ticks still accrue, nothing hangs, and no
  checklist item 1–15 covers it. The attempted fix (`d210750`) fails feasibility gates (a)/(b) on
  `daycare-fickle` (run 32858536635) and was reverted (`e8cc063`). Needs a design call
  (event-without-counter, or a recency-weighted caretaker guess). Category would be: correctness.
- **360 px feed rows render at ~4 px font** (fixture measurement, `renderer-fixture` artifact:
  "fixture 360px: widest feed row 211px … (font 4px)"). Nothing overflows or clips — item 15's gate
  and item 11's named conditions both pass — but a full-cap hunch at 4 px is not comfortably
  readable. The design note specifies no wrapping/clamping rule for the feed at small widths, so
  this is note territory. Category would be: legibility.
- N1–N3, N7–N12, N14–N23: I spot-verified a sample (N3 kernel cooldown gating, N8 caretaker
  tie-break, N12 replay derivation, N14 residual `core.zoomAt` pinch/wheel handlers, N20
  `role="button"` beat divs, N22 player blocking read) and agree with the reviewer's non-blocking
  disposition of each: none falsifies a checklist item. On N14 specifically: `#viewpanel` markup,
  CSS, ids, `attachMinimap` caller and keyboard pan are fully removed (asserted by
  `tests/test_broadcast.nim`); the surviving `zoomAt/setZoom/panBy` calls are the starter's generic
  canvas pinch/wheel/drag handlers, not panel wiring, and removing them would be an *extra* edit
  inside the starter's script beyond the note's removal list. Not blocking.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | Run **32859893259** at head sha 948d5de, conclusion `success`, jobs test/docker-smoke/wasm-viewer all ✓ (`gh api` cited above). `git diff 12d58b5..948d5de -- tests/` = **+41/−0** (one added `test_manifest` block). The two in-round revert commits delete only assertions added earlier in the same round together with their reverted feature code (`948d5de` removes `test_noleak` gate (c2) added by `79a5a66`; `e8cc063` removes `test_sim`'s bare-canopy block added by `d210750`) — I read both hunks; no pre-existing assertion removed, no tolerance widened, no skip added anywhere in `0cd19b1..948d5de`. |
| 2 Replay re-derivation | PASS | State-recording design: `sim.nim:235-254` records frames inside `stepTick` (step 9) from the live sim — there is exactly **one** recording and no parallel one. The viewer derives display from it via the same module the tests use: `replay-viewer/daycare_replay.nim:49-53` (`snapshotAt` + `replayChromeInput` + `buildViewerPacket`) ← `src/daycare/replays.nim:256-304`. Tests: `tests/test_replay.nim:54-57,94-109` (frames.len == ticksPlayed, encoding widths, `loadReplay` reload, `snapshotAt(maxTick)`); `tests/test_sim.nim:404-415` (gameHash determinism twice in-process and across a fresh sim); `tests/test_broadcast.nim` (replay→chrome path). The item's anti-pattern is absent. |
| 3 Static viewer | PASS | Manifest `game.replay_viewer == {"bundle":"static-replay-viewer"}` (parsed); `tools/build_replay_viewer.sh` present, mode 0755, wired as the build hook (`ci.yml:249`, asserted executable at `ci.yml:225-236`); no `/client/replay` route (`server.nim buildRouter` registers healthz/client/global/player/font/lockerart only; `tests/test_broadcast.nim:356-357` asserts the string is absent from server.nim; the only textual matches are comments and the starter's byte-shipped `broadcast_core.js` path table). Viewer fetches only the replay URL. |
| 4 Both name spaces | PASS | Seats see only aliases (`sim_state.nim:121-127` Alder/Bramble; `llm.nim` prompts use `sim.names`; no policy name in any player frame). Viewer maps: `broadcast.nim` roster `"pol": input.policyNames[slot]`, plate sublines `ALDER · daycare-attentive` (screenshot verified from the `renderer-fixture` artifact); `results.names` = policy names (`sim.nim:585`). |
| 5 Degrade-never-hang | PASS | Every wait bounded: connect ≤ 120 s (`server.nim:229-237`), prompt settle ≤ 2 s (`:243-253`), LLM `makeRequests(batch, 18s)` × ≤ 2 attempts (`llm.nim:500-513`), `decideAll` never raises (`:479-537`), pace sleep ≤ `minTurnSeconds` (`:466-473`), play deadline `0.6 × episodeTimeoutSeconds` checked between turns (`server.nim:296-302` → `endEarly`), shutdown 0.5 s + grace then `quit(0)` (`:202-218`). Dead/absent seat → `skCaretaker`, never a socket wait (`:309-312`). Worst case ≈ 120+2+15×36+18+1 ≈ 681 s < 720 s. |
| 6 num_agents | PASS | `num_agents: 2` in all four `variants[].game_config` and `certification.game_config` (parsed from the manifest at head); `config_schema.properties.num_agents` present (integer 1..2, default 2). `tools/ci/docker_smoke.sh:106-151` enforces all four invariants + the independent `SMOKE_SEATS` (= 2) cross-check, each exiting non-zero with `SEAT-COUNT FAIL:`. Docker-smoke log for 32859893259: **no** `SEAT-COUNT FAIL`; `game=daycare seats=2 config={… "num_agents": 2 … two players, two tokens}`; `all 2 player containers exited 0`; `smoke OK: seats=2 … reason=complete`. |
| 7 Scripted baseline full episodes | PASS | `tests/test_feasibility.nim:45-47` asserts every episode ends `reason == "complete"`/`ending == "turn_limit"`; `tests/test_baseline.nim` runs 4 variants × 4 pairings × 12 seeds of full episodes asserting per-order enum legality, per-tick action legality and board invariants. Tuning: the committed oracle (gates (a)–(f), 4 variants × 12 seeds × 6 pairings) is the enforcement, its gates demonstrably bind (run 32858536635 shows (a)/(b)/(c) failing under stream perturbations), and the constants carry recorded sweep residue (`sim_types.nim:29-44`, e.g. "320 alone left gate (b) at 0.82"). No standalone harness script is committed — recorded below as advisory residue (reviewer's N19), not a failure of the verifiable clauses. |
| 8 LLM reply handling | PASS | `extractJsonObject` first-`{`-to-last-`}`, tolerates fences/prose (`llm.nim:347-358`); retry **once** (`for attempt in 0 .. 1`, `:500`) with hint (`:475-477`); then caretaker fallback tagged `osFallback` (`:532-537`) recorded on the `order` event `source` field (`sim.nim:60-65`) so phase 60 can count it. `tests/test_llm.nim` exercises junk/429/403/timeout through the real `curly.makeRequests` path. |
| 9 Rune-safe truncation | PASS | `cleanText` = strip → `runeSubStr(0, limit−1) & "…"` (`sim_types.nim`); applied at parse (`llm.nim:441-442`) and again at install (`sim.nim:53-55`); error text capped (`llm.nim:529`, `:353-355`); prompt capped on runes (`server.nim:489-490`). `tests/test_replay.nim:14-31,71-79` feeds multi-byte runes at and over both caps and asserts `validateUtf8 == -1` on the whole replay and `runeLen <= cap` per recorded string. |
| 10 Manifest validates | PASS | `game.docs` = `{"readme":{"type":"text","value":…},"pages":[{id,title,content:{"type":"text","value":…}}×2]}`; `game.protocols` carries **both** `player` and `global` as `{"type":"text",…}` objects (parsed at head). B1's schema self-contradiction is gone (`maxItems: 2`) and the new `test_manifest` block validates every shipped `game_config` against the schema. |
| 11 Viewer legible at 360 px | PASS | `client/replay_broadcast.html:1156` `.plate-name, .plate .team-name { flex: 1 1 auto; min-width: 3.2em; }`; `:1171-1174` `@media (max-width: 640px)` hides `.plate-sub` and `.lives-label`. The renderer fixture asserts the shipped media rule is the one deciding the collapse at 360/620 vs 1152 (artifact: "fixture ok … 360 / 620 / 1152 px viewports"). |
| 12 Release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:153) → Certify (:167) → **Upload the policies** (:206) → Upload the Coworld (:304) → Put the Coworld secret (:342). Three workflows present; `docker_smoke.sh` and `build_replay_viewer.sh` both 0755; `tools/ci/policies.json` = 2 `PLAYER_PROMPT` champions (both `USE_BEDROCK: true`, both covering both roles) + 2 `PLAYER_SCRIPTED` fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`. I ran the placeholder gate verbatim (`grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files): no match, exit 1 → gate passes. |
| 13 Viewer executes | PASS | Run 32859893259 `wasm-viewer` ✓ **including** "Load the bundle in a real browser": `{"loaded":true,"ms":371,"clock":"TURN 4 / 6 TICK 239 OF 359",…}`, soak advancing ("0 / 359" → "191 / 359" → "239 / 359"), three distinct scrub readouts (0%/50%/100%), `--strict-text-bounds` + `--soak 10` present, no `continue-on-error` anywhere in the workflow, `needs: docker-smoke` (`ci.yml:212`). Markers: `static_replay.js:147` sets `data-replay-loaded` on the worker's `loaded` message; `:15-17` sets `data-replay-error` in `showFailure`. Link-flag/bootstrap pair from ONE starter: `config.nims` diffs from coworld-ctf's only in the emitted name + `_daycare_*` exports — **no MODULARIZE, no EXPORT_NAME** — and `static_replay_worker.js:164` bootstraps with `Module.onRuntimeInitialized`, the matched non-MODULARIZE pair. |
| 14 Chrome is the starter's | PASS | `client/chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (`diff`: no output). `client/replay_broadcast.html` = starter's page (4165 → 3080 lines): every removed hunk I sampled belongs to the documented removals (`#viewpanel`/`#minimap`/`#zoombar`/zoom ids, `#fpv*`, `#povBadge`, `#mmwarn` + their CSS/JS); all 40+ kept starter ids present (scripted id sweep: none missing); the two re-lettered literals and the `#lockerroom { pointer-events: none }` edit are the only in-starter changes; game block appended under the `DAYCARE additions to the inherited coworld-ctf chrome` banner. Transport: `relayout()` sets `--band`/`--topband`/`--hudscale` on `document.documentElement`; appended layer clipped `inset: var(--topband) 0 var(--band) 0, pointer-events: none`; endcard shown via `#endcard.on` and dropped on any non-gameover frame (`:2266` `$('endcard').classList.remove('on')`) — every seek takes it down; beat CSS exists for all five emitted kinds (`turn/guess/switch/feast/gameover`, `:1277-1281`); game beat builder named `buildCareBeats`, scope-duplication test in `test_broadcast.nim`. `#viewpanel` removed, not hidden (board 1152×672 fits the frame). |
| 15 Every drawn string fits its frame | PASS | Board text is server-side sprite art (`art.nim textSprite`, blitted in `global.nim:257-264`), so `canvas_text.total == 0` structurally on both steps — covered instead by the required worst-case renderer fixture: `tools/ci/renderer_fixture.html` at head fetches and splices the **shipped** `client/replay_broadcast.html` (real `chrome_common.js`/`broadcast_core.js`/font), drives it through the page's own `CtfStaticReplay` seam in an iframe at 360/620/1152 px **viewport** widths with a self-checked 80-rune hunch + 240-rune notes on **both** seats and a 15-chip tape, asserts the strings reached the DOM at full length, nothing crosses a viewport edge, leaves the board region, or overflows its box (`scrollWidth/scrollHeight`), and that the shipped `@media (max-width: 640px)` decides the collapse; every failure routes to `data-replay-error`, which fails `viewer_smoke.mjs --strict-text-bounds` (its own `ci.yml` step, :344-361, served over local HTTP). Verified from the run's `renderer-fixture` artifact I downloaded: `status: "fixture ok: the shipped page at 360 / 620 / 1152 px viewports, hunch 80 runes on both seats, notes 240 runes, 15 chips"`, `data_replay_loaded: "true"`, `data_replay_error: null`, per-width geometry in `console_tail`, screenshot shows the shipped chrome with full-cap feed rows in-frame. `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)` on both steps, and the flag is carried on the fixed arena as required. |
| addendum: one parallel batch per turn | PASS | `llm.nim decideAll` posts **both** open seats into one `RequestBatch` before a single `makeRequests` call (`:503-513`); `lastBatchSize` asserted `== 2` on turn 1 and on a warm turn by `tests/test_llm.nim:255-296`, with a wall-clock probe that fails if the two requests serialise. The player process only delivers a prompt and listens (`daycare_player.nim`); all decisions are in the game container. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | fixed in `b9bab64` (maxItems 2 + test block) | Manifest at head has `maxItems: 2` for both; `test_manifest` block present and green in run 32859893259 | yes |
| N13/C3 | fixed in `fd1eda8` (fixture measures shipped page at viewport widths) | Read the new fixture end-to-end: iframe at 360/620/1152, shipped page spliced as the Dockerfile does, DOM assertions incl. full-length-string self-check and shipped-media-query check, failure → `data-replay-error`. Downloaded the `renderer-fixture` artifact: status/console/loaded/error all exactly as the fixer quoted | yes |
| N4 | fix written (`79a5a66`), failed gate (c) in run 32858536635, reverted (`948d5de`), NEEDS-DESIGN | Head code matches pre-fix state (`sim_state.nim:112`); revert commit removes only the same-round test; run 32858536635 is `failure` on the intermediate shas. Advisory at head — no checklist item | yes |
| N6 | fix written (`d210750`), failed gates (a)/(b) on daycare-fickle, reverted (`e8cc063`), NEEDS-DESIGN | Head code matches pre-fix state (`sim.nim:112` `ripe < 1: continue`); revert removes only the same-round test. Advisory at head — no checklist item | yes |
| N5 | DISPUTED as defect / design risk; no change | Design note specifies `secret` on the live broadcast frame and a token-free `/global`; player frames carry no preference. No checklist item falsified | yes |
| "no src/ or client/ file differs from 12d58b5" | claimed | `git diff 12d58b5..948d5de -- src/ client/` is empty | yes |
| "tests/ diff vs 12d58b5 is +40/−0" | claimed | `+41 insertions, 0 deletions` (`git diff --stat`; `grep -c '^-[^-]'` → 0) — off by one on the insertion count, zero deletions confirmed, immaterial | yes |
| negative control (400-rune hunch fails the gate) | run locally, not committed | Not reproducible here (no browser in sandbox); the mechanism is verifiable from code (fixture `fail()` → `data-replay-error` → `viewer_smoke.mjs` exits non-zero) and CI history shows the fixture step participating in a red run (32859516987) | partially — mechanism verified, the specific local run taken as claim only |

## Could not verify (none blocking)

- Whether a hosted episode with real Bedrock latency stays inside the 720 s play budget (reviewer's
  C2). All bounds are explicit in code and the worst-case arithmetic lands ≈ 681 s; every CI run is
  credential-free. Settled by a phase-60 hosted episode log. Not a checklist item I can fail from
  the tree — the item's requirement (explicit bounds on every wait, no unbounded loop) **is**
  verified from the tree, and passes.
- Whether a standalone parameter-sweep harness was ever run outside CI (reviewer's C4/N19). The
  committed feasibility oracle and its recorded intermediate values are the in-tree evidence; item
  7's verifiable clauses pass. Settled by committing the sweep script or citing its run.

BLOCKING: 0
