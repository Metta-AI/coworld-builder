blocking: 0
# r1 verdict — battlecode-2025 (bc25)
Head: 6885a0625687c7caec19b879e0ea09613ebd74f0   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST   Independent read written before reading fixes: yes (r1-fixes.md not read)


## Independent read (written BEFORE reading r1-review.md or r1-fixes.md)

Scope: MOD run adding bc25 beside bc26/bc20/bc21/bc24. Diff 5e7c8b78..6885a062, ~106 files, +18 459.

Key observations from the tree at 6885a062:

- Manifest (`coworld_manifest_template.json`): `game.replay_viewer = {"bundle":"static-replay-viewer"}`;
  `game.protocols` has both `player` and `global`; `game.docs.readme` is a `{type,value}` object and
  `pages` has seven ids including `rules-bc25.md`; `variants` = five ids, each with
  `game_config.num_agents == 2` and none at variant top level; `certification.game_config.num_agents == 2`,
  `certification.players == [awu, scaffold] == player[]`; `end_reason` enum carries all seven new bc25
  values plus pre-existing `coin_flip`/`abandoned`; `year.enum` is the five years.
- Placeholder gate: `grep '<slug>\|<IMAGE>\|<SEATS>'` over the five files exits 1 (clean).
- `tools/ci/policies.json`: 20 entries; bc25 set = 2 `PLAYER_PROMPT` champions (coverage/siege, second
  carrying `"player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`) + 2 scripted fillers
  (`spaark`, `examplefuncsplayer25`), fillers ≠ champions.
- `tools/ci/docker_smoke.sh` present, mode 100755; four seat-count invariants + SMOKE override guards,
  each exiting non-zero with `SEAT-COUNT FAIL:` prefix (lines 148–227).
- CI at 6885a062: run **34185528349**, conclusion success; jobs test / parity-oracle /
  parity-oracle-bc20 / -bc21 / -bc24 / -bc25 / docker-smoke / wasm-viewer all `success`.
  docker-smoke job 101932991471 log: `grep -c 'SEAT-COUNT FAIL'` = **0**. wasm-viewer job
  101933521650 ran `Load the bundle in a real browser (ALL FIVE years' replays)` => success, and
  `needs: docker-smoke` (ci.yml:1901). The only `continue-on-error` in ci.yml (line 667) is the
  pre-existing bc20 "engine-from-source attempt (reported, not blocking)" step, not a gate.
- Viewer provenance: `client/chrome_common.js`, `client/broadcast_core.js`,
  `replay-viewer/config.nims`, `static_replay.js`, `static_replay_worker.js` are **byte-identical to
  the base 5e7c8b78** (git diff empty). Only `client/replay_broadcast.html` changed (+501/−3); the 3
  deletions are the additive edits the design pins (extend `--statrail` id list, extend the
  `!isBc20 && !isBc21 && !isBc24` guard with `&& !isBc25`). bc25 block appended under the banner
  `BC25 additions to the inherited cogame-battlecode chrome` (line 3042).
- Link flags / bootstrap agree and both come from the base repo: no `MODULARIZE` in `config.nims`,
  worker uses `Module.onRuntimeInitialized` (static_replay_worker.js:218) — the consistent
  non-modularize pair, and the browser smoke executes it green.
- Load markers: `static_replay.js:180` sets `data-replay-loaded` on first drawn frame; `:20` sets
  `data-replay-error`. Frames are re-derived sim rounds (`"st": 0` with frame 0 = round 0 of game 1);
  the replay records no lobby frames, so the lobby-dwell class of defect cannot occur here.
- Beats: `broadcast.nim beatsFor` emits bc25 kinds (`tower`, `upgrade`, `siege`, `srp`, `coverage`,
  `starve`, `rout`, `build`, `game`, `end`, `doctrine`); `buildBc25BeatButtons`
  (replay_broadcast.html:4445) creates labelled `<button>`s that seek; CSS exists for all eleven
  kinds, each scoped `html[data-year="bc25"]` (lines 3193–3203).
- `#bc25-doctrines`: close button, Escape binding, 6 s self-dismiss, re-open chip — present.
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` at line 2571; label-drop rules under
  `@media (max-width: 640px)` (line 3205ff).
- Decision path (`decide.nim`): ONE parallel batch via `curly.makeRequests` (line ~691), bounded
  `attempt < 2` loop (attempt1Ms then retryMs), throttle fast-fail, fallback recorded in
  `result.fallback[slot]` + `doctrine_fallback` event. No-credential path falls back at construction.
- Rune safety: `truncateRunes`/`truncateBytes` in `sim_types.nim:237–266` used at every capture
  point (sheet.nim, llm.nim, decide.nim); `tests/test_bc25_sheet.nim:149–154` feeds 2-byte and
  astral 4-byte runes at the caps and asserts rune counts.
- Item 1 "no test loosened": `git log -p --since=2026-09-07 -- tests/` shows 8 commits; the only
  removed assertions are the 4-year counts replaced by stricter 5-year counts (9c9e445: 16→20
  policies, 8→10 prompts/scripted, 4→5 owned, 6→7 doc pages, plus ~15 new bc25-specific policy
  assertions). No skip/xfail/tolerance widening anywhere; e0fc17b and c480eae only ADD assertions.
- Item 7: `tests/test_bc25_replay.nim` (c480eae) plays an all-scripted 3-game match and asserts
  `reason == "complete"`, `fallbacks == [0,0]`; `tests/test_bc25_baselines.nim` asserts every emitted
  action legal at emission and no `DecisionOps` overrun; grid-tuned thresholds recorded in headers.
- Item 2: `tests/test_bc25_replay.nim` records → re-derives for every end reason, asserts identical
  hash chains, asserts the recording carries no per-round state (only the hash chain), and that
  coverage is re-derived, not stored.
- Item 15: `--strict-text-bounds` deliberately dropped on the pannable-board replay runs (comment at
  ci.yml:2002), and the worst-case renderer fixture `tools/ci/renderer_fixture.html` (bc25 row at
  line 309ff: full-cap strings through `#bc25-towers`/`#bc25-econ`/`#bc25-doctrines`) runs under
  `viewer_smoke.mjs --strict-text-bounds` in its own step (`Render the full-cap doctrine-text
  fixture`, green in run 34185528349).
- docker-smoke: five episodes; bc25 episode green; `All five smoke replays are present and are
  different years` step green.

---

## Adjudication of r1-review.md (43 findings), verified at head 6885a062

The review was written against `eb33a8d` (the PR #5 merge). Six fix commits landed after it and
are part of the sha under judgment: 0585d71 (F26), c2e1f3b (F11), e0fc17b (F12), c480eae (F39),
ff1e4f6 (F43), 6885a06 (F34). Every finding below is re-verified against the tree at 6885a062,
not at the review's base. I did not read r1-fixes.md; the fix commits were verified directly.

### Standing blocking findings

**None.** No finding of the reviewer's, and nothing in my independent pass, falsifies a checklist
item at 6885a062.

### Refuted / resolved-at-head / non-blocking

**F26 (the reviewer's one blocking-candidate) → RESOLVED AT HEAD.** At eb33a8d the claim was
true: `beatsFor` had no bc25 arm. At 6885a062, commit 0585d71 adds emission arms for all nine
missing kinds — `src/battlecode/broadcast.nim:162-171`: `of "first_action": (if isBc25: "build"
else: "")`, `of "tower_built": "tower"`, `of "tower_upgraded": "upgrade"`, `of "tower_lost":
"siege"`, `of "srp_completed", "srp_active", "srp_broken": "srp"`, `of "coverage": "coverage"`,
`of "starved": "starve"`, `of "rout": (if isBc25: "rout" else: "")` — and the pre-match guard
(`broadcast.nim:144-146`) now passes `doctrine_received`/`doctrine_fallback` through at frame 0.
Each kind has a label arm (`broadcast.nim:174ff`). `tests/test_viewer.nim` (+62 lines in 0585d71)
runs the committed fixture plus the five kinds a scripted recording cannot produce through
`beatsFor` and asserts every one of the eleven kinds is **emitted**, labelled, and styled by a
page rule ("a bc25 replay EMITS the `<kind>` beat"; "the committed bc25 fixture draws a scrubber
full of beats"; "over many kinds, not just game/end"). CI is green at this head with that test in
the suite. A finding that was true and has since been fixed is refuted at head: **counts 0**.

**F11 → RESOLVED AT HEAD (two sub-items) / DELIBERATE-AND-TESTED (two sub-items).** c2e1f3b:
`match.nim:236-252` now emits `remaining` on `tower_lost` and `active_total` on `srp_active`,
with `tests/test_bc25_replay.nim` asserting the note's full field list for both kinds and
`income_bonus == active_total * 3`. The `first_action.action`-not-`kind` naming stands for a
correct mechanical reason (a field named `kind` would overwrite the event's own `kind` on the
flattened `MatchEvent` object — match.nim:169-175, tested), and `coverage.tiles_from_win` is an
addition the note's own feed line requires. No checklist item is touched. Counts 0.

**F12 → RESOLVED AT HEAD.** e0fc17b adds a `PreMatchBounds` block to `tests/test_bc25_replay.nim`
that drives the doctrine phase into both failure paths (dead endpoint, both attempts spent) and
asserts every pre-match kind inside a documented ceiling (`doctrine_requested` 2,
`doctrine_received` 2, `doctrine_retry` 4, `doctrine_fallback` 2), with the note-vs-code ceiling
divergence explained in the comment (per-seat vs per-episode counting; both bounded by the same
`attempt < 2` loop). Counts 0.

**F39 → RESOLVED AT HEAD.** c480eae adds to `tests/test_bc25_replay.nim` an all-scripted
3-game bc25 episode through `playMatch`/`resultsJson` asserting `reason == "complete"`,
`fallbacks == [0,0]`, majority ended, no `abandoned` game. Together with
`tests/test_bc25_baselines.nim`'s per-action legality assertions (every emitted order legal at
emission, `refusedActions == 0`, no `DecisionOps` overrun), checklist item 7's first half is
satisfied in-tree, not only in docker-smoke. Counts 0.

**F43 → RESOLVED AT HEAD.** ff1e4f6: `knobs.nim:34` now reads "All eleven exist" over the
eleven listed chassis files, matching the tree (`ls src/battlecode/years/bc25/chassis/` = 11
files) and the paths named in `NOTICE` and `docs/RULES-BC25.md`. Counts 0.

**F34 → PARTIALLY RESOLVED AT HEAD; remainder non-blocking.** 6885a06 raises the
across-the-pair squares floor to the note's 200 (`ci.yml:1797`: `test "${painted}" -ge 200`,
measured 241). The per-seat `tiles_painted: 15` (vs the note's 150) is kept with the measured
reason in the step comment: the note's 150 came from whole 2000-round games; this smoke is 600
rounds and the weak seat paints 37 in that window, so 150 is a floor no correct episode can
clear. No checklist item pins these floors. On item 1's "no test loosened": the 150→15 change
(commit 081b6a8, pre-merge) altered `ci.yml`, not `tests/`; the 150 never gated a passing run
(it was arithmetically unpassable for the 600-round episode) and the note's own procedure
("phase 20 measures … sets the committed floors at roughly half the weak seat's measured
value") produces 15-20, contradicting its own "never below" clause. The gate still bites: 15 is
per-seat, 3× an idle seat, alongside robots_built 20 / chips_spent 8000 / paint_spent 3000 —
three of which are far ABOVE the note's numbers. Advisory. Counts 0.

**F36 (renderer fixture, `canvas_text total: 0`) → NON-BLOCKING under item 15, ruled.** The
checklist's "loads the real `client/renderer.js`" names a file this lineage does not have: the
board renderer is `src/battlecode/render.nim` compiled to wasm, and every string of LLM-authored
text this viewer draws (`notes` 280 runes, `motto` 48 runes, doctrine plain-words) is drawn in
**DOM**, not canvas. What item 15 exists to prevent — model text shipped clipped because CI
replays carry no LLM text — is gated: `tools/ci/renderer_fixture.html` builds full-cap notes and
mottos into the real chrome ids for all five years including bc25 (`:309-345`, bc25 row), renders
against the page's **own CSS extracted at run time from `client/replay_broadcast.html`**
(ci.yml:2145-2156), asserts its own strings are still at their caps (`:159-160`, `:506-517` —
the anti-vacuity guard, and `tests/test_viewer.nim:404-414` pins the bc25 selectors so the
assertion cannot go quietly blind), measures overflow/clipping via DOM rects and raises
`data-replay-error` on any violation, and runs under `viewer_smoke.mjs --strict-text-bounds` in
its own step — `Render the full-cap doctrine-text fixture`, **success** in run 34185528349.
`canvas_text total: 0` on that page is expected (the fixture has no canvas) and its gate is the
DOM `problem()` check, not `canvas_text`. On the five real replays, `--strict-text-bounds` is
dropped for the reason the checklist itself gives (pannable board, `#viewpanel` kept) and the
counts are still recorded. Counts 0.

**F40 (grid harness) → REFUTED as unverifiable; item 7's second half IS verifiable from the
tree.** The committed harness is `tests/test_bc25_knobs.nim` itself: paired seeded games
(identical seed/map/opponent, one knob at low vs high, 3 seeds × named maps), thresholds in one
table, with the measured deltas per knob recorded in the header (`:8-62`, dated, `-d:release`),
plus `tests/test_bc25_survival.nim:23-32`'s recorded healthy-mirror and broken-control ranges
bracketing every committed threshold, and the inverted broken-chassis control that must come
back red. That is a grid harness, committed, run in CI on every push. Counts 0.

**F41 (six knob-teeth substitutions) → NON-BLOCKING.** The note's §Tests item 16 explicitly
authorises tuning ("Thresholds live in one table … the header records every substituted
statistic") and every substitution is recorded with its measurement. No checklist item names
these thresholds. Counts 0.

**F1 (`game.docs` type `uri` vs the checklist's literal `text`) → NON-BLOCKING.** The shape is
`{type,value}` objects for `readme` and all seven `pages`, `game.protocols` carries both
`player` and `global`, and the operative requirement of item 10 — "manifest validates" — is
proven mechanically: ci.yml:343 `The coworld CLI accepts the manifest template` runs the
installed `coworld==0.1.43` `_load_template_manifest`/`validate_upload_manifest` over this exact
file, green at this head. `type: uri` is pre-existing across four shipped, certified years and is
what the design note specifies. The checklist's `"type":"text"` is an illustration of the shape,
not an enum pin — reading it as one would declare the already-released manifest invalid. Counts 0.

**F2–F10, F13–F25, F27–F33, F35, F37, F38, F42 (traced as consistent, "no finding") —
spot-verified, CONFIRMED.** I independently reproduced the material ones rather than accepting
them: manifest num_agents/certification/player[] (my read, above); policies.json 20 entries with
the bc25 four and champion #2's pinned player id; the placeholder gate exits clean; release step
order (build 168 → certify 182 → upload-policies 225 → upload-coworld 323 → secret put 419 in
`coworld-release.yml`); decide.nim's one parallel batch / one retry / monotonic budget /
fallback recording; rune-safe truncation and the astral-plane tests; the six-step round loop,
70 % denominator (372→261 on DefaultSmall), SRP lifecycle, scan-order table; replay
re-derivation asserted with nothing per-round stored but the hash chain;
`chrome_common.js`/`broadcast_core.js` byte-identical to the coworld-ctf starter copies AND to
the base 5e7c8b78 (diff: empty); no `MODULARIZE` + `onRuntimeInitialized` worker (consistent
non-modularized pair, base-identical); `data-replay-loaded` on first drawn frame
(static_replay.js:180) and `data-replay-error` (`:14-20`); GV08 + compat list extended not
reset; parity ledger `entries: []` with all four tiers wired and green. All stand as passes.

### Reviewer's "could not determine" items, settled

- **bc24's own missing beat arms**: pre-existing years are in scope only where bc25 touches or
  regresses them. 0585d71 improves the shared `beatsFor` without changing bc24's vocabulary
  (`first_action`/`rout` arms are year-gated on `isBc25`). bc24's beat coverage is that run's
  residue, not this one's. Not counted.
- **killfeed-overlap negative control** (design note §killfeed rule item 3): I searched
  `ci.yml`, `tools/ci/viewer_smoke.mjs` and `tests/test_viewer.nim` — the overlap gate is real
  and runs on all five replays at 3 widths × 2 zooms, and `tests/test_viewer.nim:355-379` and
  `:912-916` statically pin the CSS/relayout contract, but I found no self-test that breaks the
  rule and asserts the gate goes red. That is a design-note nicety, not a checklist item; the
  checklist's item 11 (plate-name rule, sub-640px label hiding) is verified in the tree at
  `client/replay_broadcast.html:2571` and `:3205ff`. **Non-blocking observation** (see below).
- **DOM fixture vs `client/renderer.js`**: ruled under F36, above.

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run **34185528349** at 6885a062, conclusion success; all 8 jobs success. `git log -p --since=2026-09-07 -- tests/`: 8 commits, only removals are 4-year counts replaced by stricter 5-year counts (9c9e445); no skip/xfail/tolerance/deleted test. |
| 2 replay re-derivation | PASS | tests/test_bc25_replay.nim:83-97 (every end reason re-derives, mismatch −1), :122-133 (nothing per-round stored but the 16-hex/round chain), :135-157 (viewer chrome built off the same deriver; coverage re-derived not stored) |
| 3 static viewer | PASS | manifest `game.replay_viewer = {"bundle":"static-replay-viewer"}`; tools/build_replay_viewer.sh present, mode 100755, exec-bit asserted in ci.yml:1915-1925; no `/client/replay` path (only the release-yml guard string that forbids it) |
| 4 both name spaces | PASS | decide.nim:463-464 (alias + opponent_alias, no names in the brief); broadcast.nim bc25 chrome carries `aliases` AND `names`; viewer plates print alias — real name |
| 5 degrade-never-hang | PASS | decide.nim:631-691 (45 s budget, attempt<2, one batch, monotonic re-check); rules.nim playGame budget guard every 32 rounds; worst case 30+45+340+30 = 445 s ≤ 720 s; no `while true` under years/bc25 |
| 6 num_agents | PASS | all five variants' game_config = 2, none at top level; certification.game_config = 2; len(players) = len(gc.players) = 2; docker_smoke.sh:145-227 four invariants + SMOKE_SEATS cross-check (`:82`, default 2); docker-smoke log grep 'SEAT-COUNT FAIL' = **0** (job 101932991471) |
| 7 scripted baseline full episodes | PASS | test_bc25_replay.nim (c480eae): reason == "complete", fallbacks [0,0]; test_bc25_baselines.nim:53-86: every order legal at emission, refusedActions == 0, ops ≤ budget; tuning harness = test_bc25_knobs.nim paired grid + recorded measured ranges |
| 8 LLM reply handling | PASS | fence-tolerant extraction in llm.nim (shared, unchanged); decide.nim:654 one retry; :739-751 fallback to scripted sheet recorded in results.fallbacks + doctrine_fallback event |
| 9 rune-safe truncation | PASS | sim_types.nim:237-266; call sites sheet.nim:101,116-125, llm.nim:169-204, decide.nim:724-728; test_bc25_sheet.nim:147-176 (2-byte é and 4-byte astral at the caps, validateUtf8 < 0, 16 KB byte cap on rune boundary) |
| 10 manifest validates | PASS | docs.readme + 7 pages as {type,value}; protocols.player + .global; ci.yml:343 runs coworld CLI validate_upload_manifest over the template, green (type "uri" not "text": see F1 ruling) |
| 11 viewer legible at 360 px | PASS | replay_broadcast.html:2571 `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`; @media (max-width: 640px) label drops at :2647 and :3205-3222 |
| 12 release order and scaffold | PASS | coworld-release.yml: build 168 → certify 182 → upload-policies 225 → upload-coworld 323 → secret put 419; three workflows present; docker_smoke.sh executable; policies.json 20 entries, bc25 = 2 PLAYER_PROMPT champions + 2 scripted fillers, champion #2 `player: ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`; placeholder gate exits clean (run in this session) |
| 13 viewer executes | PASS | run 34185528349 wasm-viewer job 101933521650: `Load the bundle in a real browser (ALL FIVE years' replays)` => success, `needs: docker-smoke` at ci.yml:1901, no continue-on-error on it (the one continue-on-error at :667 is the pre-existing bc20 reported-only step); data-replay-loaded/-error both set from the shell's own paths (static_replay.js:180, :14-20); no lobby frames in this format (frames = sim rounds; test asserts 300 rounds → 300 frames) so playback opens at the game start by construction; config.nims has no MODULARIZE and the worker waits on Module.onRuntimeInitialized — the consistent pair, byte-identical to base, and the browser smoke proves `loaded: true` |
| 14 chrome is the starter's | PASS | chrome_common.js and broadcast_core.js diff-identical to /workspace/starters/coworld-ctf copies; replay_broadcast.html +501/−3 where the 3 deletions are the sanctioned additive edits (statrail id list, year guard); bc25 block under its banner at :3042; `#viewpanel` kept (board 800-960 px > 360 px frame, per note §Zoom); beats are labelled `<button>`s with per-kind CSS all scoped html[data-year="bc25"] (:3193-3203); endcard `#endcard.on`, bottom var(--band), every seek dismisses (seek() → dismissEndcard) |
| 15 drawn strings fit | PASS | --strict-text-bounds dropped on replay runs for the checklist's own pannable-board case (comment ci.yml:2002-2011), counts still recorded; worst-case fixture `tools/ci/renderer_fixture.html` with bc25 row (:309-345), self-asserting full-length strings (:506-517), own ci.yml step with --strict-text-bounds, success at head (see F36 ruling) |
| parallel-batch rule | PASS | decide.nim: one RequestBatch over all open seats, one `client.curl.makeRequests(batch, …)` per attempt; never per-seat sequential |

## Non-blocking observations (not tied to a checklist item)

- The design note's killfeed-gate **negative control** (§killfeed rule item 3: a self-test that
  breaks the rule and asserts the gate goes red) is not present in the tree that I could find.
  The gate itself runs on all five replays at 6 width/zoom combinations. Worth carrying as
  residue for a future round or phase 60, not blocking here.
- Per-seat `tiles_painted: 15` in the bc25 smoke sits below the design note's 150 with a
  measured, documented reason (600-round window vs whole-game numbers). The note's own tuning
  procedure and its "never below" clause are mutually inconsistent for this floor; the tree
  resolves it toward the measurement, loudly.
- `knobs.nim` doc-comment count and event-field naming drift are all resolved or deliberate and
  tested at head (F43, F11).

## Fixer report audit

Not performed against r1-fixes.md — per the brief I did not read it. In its place, each of the
six post-merge fix commits was verified directly against the tree and is dispositioned above
(0585d71 ✓ F26, c2e1f3b ✓ F11, e0fc17b ✓ F12, c480eae ✓ F39, ff1e4f6 ✓ F43, 6885a06 ✓/advisory
F34). No fix commit weakened a test; all six add assertions or raise floors.

## Count

Standing blocking findings: **0**. Reviewer findings dismissed or resolved at head: F26 (fixed),
F11 (fixed/deliberate), F12 (fixed), F39 (fixed), F43 (fixed), F34 (fixed where the note was
right; advisory where the measurement is), F36 (non-blocking, ruled), F40 (refuted), F41
(advisory), F1 (non-blocking, ruled). All other findings were "no finding" traces and were
spot-confirmed.

BLOCKING: 0
