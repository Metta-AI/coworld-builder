blocking: 0

# r2 verdict — battlecode

Head: `abc92ce3d7005eac6dc7bebae0e3b007033c0fd4` (main; CI run 33834906008, conclusion `success`,
jobs test/docker-smoke/parity-oracle/wasm-viewer all `success`)
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (items 1–15 + one-parallel-batch)
Independent read written before reading fixes: **yes** (repo, diff, ci.yml, CI logs and manifest
read and noted before opening `r2-fixes.md`; `r2-review.md` is operator-authored — D1/D2/D3 were
treated as rulings to verify fixed, not hypotheses to refute).

---

## Operator findings — fixed / not fixed

### D1 — `chassis` is not an LLM knob → **FIXED** (`96c0691`, `12ea9b8`)

- **Knob surface**: `src/battlecode/sheet.nim:75-79` — `KnownKeys` is exactly the ten doctrine
  knobs; no `chassis`. `validate` has no chassis branch (`sheet.nim:222-225`: "chassis is NOT
  read here"); an LLM reply naming it takes the ordinary unknown-key path
  (`sheet.nim:216-217` → `unknownFields`).
- **Prompt preamble**: `src/battlecode/decide.nim:81-97` — THE KNOBS list is ten lines, no
  chassis, and closes with *"Your clan is driven by the `awu` chassis. That is not yours to
  choose: there is no `chassis` knob, and a reply that sends one has it ignored."*
- **Ignored / recorded / logged**: `decide.nim:219-226` — a reply carrying `chassis` is already
  in `unknownFields` (recorded in the replay as `sheet_unknown_fields`) and the seat is named in
  the log ("sent \`chassis\`, which is not a doctrine knob: ignored, the clan runs the awu
  chassis").
- **LLM always awu**: `defaultDoctrine()` (`sheet.nim:88`) pins `chassis: chAwu` and nothing on
  the parse path can change it.
- **Scaffold only via PLAYER_SCRIPTED**: `src/battlecode/baselines.nim:24-30,45-47` —
  `chassisFor` sets the field directly on the baseline sheet; both scripted replies
  (`baselineReply`) carry only LLM-visible keys (`{"sheet":{}}`), so `sheet.validate` stays the
  single shared validator.
- **Replays still re-derive**: the *applied* chassis is recorded (`sheet.toJson`,
  `sheet.nim:329`) and restored on playback via `parseChassis`
  (`src/battlecode/replay.nim:177-181`), so a scaffold-filler recording re-derives on the bot
  that played it. `test_replay` (72 checks), `test_determinism` (39 checks) green in run
  33834906008; docker-smoke ran the awu+scaffold certification mix to `reason=complete` and
  wasm-viewer re-derived that replay in a real browser (`loaded:true`, endcard raised).
- **GameVersion bumped**: `src/battlecode/sim_types.nim:16` — `GameVersion = "GV04"`, changelog
  entry names the D1 surface change (and, via `12ea9b8`, the D2 chassis change) in the
  prepend-only log; bump landed in the same commit as the surface change.
- **Tests**: `tests/test_sheet.nim:119-137` ("`chassis` is NOT a knob (r2-D1)") asserts
  `"chassis" notin KnownKeys`, `{"chassis":"scaffold"}` still runs `chAwu`, the key is recorded
  as unknown and *not* counted as a repair, and the preamble prints no chassis knob line.

### D2 — awu loses every king / king-survival gate → **FIXED** (8 chassis commits + gate `219058c`, `abc92ce`)

- **Gate exists and is wired**: `tests/test_king_survival.nim` (77 lines). ci.yml's `test` job
  runs `tests/*.nim` by glob; the run-33834906008 `test` log shows it executing in **both**
  debug and release (`test_king_survival: ok (11 checks)` at 03:56:28Z and 03:56:35Z).
- **Matches the operator's spec, not weakened**: awu-default vs awu-default
  (`baselineSheet(blAwu)` both seats), 2000 rounds, five maps; per map it asserts (a) no clan
  loses its last king before round **1500**, read **round-by-round from the king counts**
  (`test_king_survival.nim:52-58` callback on `w.teamInfo.numRatKings`), not from the
  `end_reason` label — which is what catches the mutual-wipe-as-`round_limit` case; (b) the game
  is not decided by `kings_destroyed` before 1500; and the aggregate (c) **≥ 4 of 5** reach
  round 2000 or end on points (`erCatsCleared`/`erRoundLimit`). Thresholds are exactly the
  ruling's (≥4/5, none kings_destroyed before 1500).
  - One deviation, noted: the gate's map list is `DefaultSmall, closeup, toomuchcheese,
    cheesefarm, dirtfulcat` — **`dirtfulcat` in place of `arrows`** (the parity-oracle five are
    DefaultSmall/arrows/closeup/toomuchcheese/cheesefarm). `dirtfulcat` is one of the two maps
    the operator observed failing (kings lost at 362/314), so the substitution covers the
    observed failure rather than dodging it; all five are small-pool maps. Not a weakening.
- **Fails pre-fix, by construction against the observed numbers**: the review's ladder match
  lost all kings at rounds **1078 and 362** — the gate's check (a) fails on a wipe at 362 and
  check (b) fails on `kings_destroyed` at 1078 (< 1500). The gate header's own pre-fix table
  (45f4ead/GV03: wipes at 1012/1310/436/314, only 2/5 on points → 8 of 11 checks fail) is
  consistent with the assertions as written; I could not re-run the pre-fix tree (no Nim in the
  sandbox) but the failure arithmetic is direct from the asserted predicates.
- **Post-fix CI evidence**: test log shows all five games with "both clans still crowned",
  worst end at 702 rounds `cats_cleared`, 5/5 on points — 11/11 checks green, debug and release.
- **Parity-sensitive files untouched**: `git show --stat` over every D2 commit
  (`d2d19e5 9555d3a de619f7 b33eb90 dbd93e2 5542ed6 83721b9 f77f450`) touches only
  `src/battlecode/years/bc26/chassis/{king,rat,targets,formation,dirt,pathing,traps}.nim`;
  `scaffold.nim`, `world.nim`, `cats.nim`, `rules.nim` appear in **no** r2 commit. Direct proof
  the scaffold path is undisturbed: **parity-oracle green at this sha** — Tier A "bit-exact
  through round 50" and Tier B "bit-exact through round 200" on all five pairs (job
  100905301832; Tier C: 4× identical over 2000 rounds, arrows first-divergence 915, reported
  only).
- **Knob-sensitivity and perf gates still green**: `test_knob_sensitivity: ok (15 checks)`,
  `test_perf: ok (6 checks)`, both modes, same run.

### D3 — doctrine overlay owns the board → **FIXED** (`2fb1aea`, `eef6684`, `2164ce6`, `dd6669f`)

- **Auto-dismisses**: `client/replay_broadcast.html` `renderDoctrines` — closes on the first
  frame that advances the playhead (`s.t !== doctrinesLastFrame && s.t > 0 && !doctrinesPinned →
  setDoctrinesOpen(false)`) **and** on a 6 s timer for a viewer who never presses play.
- **Re-openable**: `#doctrines-toggle`, a real `<button>` with `aria-expanded`/`aria-controls`;
  a panel the viewer opened by hand (`doctrinesPinned`) stays open.
- **Height-capped**: `#doctrines .dbody { max-height: calc(33vh - var(--band, 0px));
  overflow-y: auto }` (`replay_broadcast.html:2615-2619`) — even pinned open at 360 px it cannot
  own the board.
- **CI measures obscuration and fails**: `tools/ci/viewer_smoke.mjs` (`eef6684`) reports
  `obscured` (largest visible absolutely-placed, ≥20 %-opaque-painting, text-bearing element
  over the board canvas) at every readout, per scrub sample and after the soak; ci.yml's
  `wasm-viewer` "Load the bundle in a real browser" step exits 1 when `obscured.pct > 50` while
  playback is advancing (the endcard is not exempted — it is hidden during playback and gated
  separately at the 100 % seek).
- **Green run readouts** (job 100905528756): `scrub selector: #scrub`; soak advancing
  (`"round 4 / 400" → "round 196 / 400" → "round 244 / 400"`); three differing clocks
  (0 % `"0:07 GAME 1 OF 1 — TOOMUCHCHEESE"`, 50 % `"0:08 …"`, 100 % `"FINAL MATCH OVER"`);
  `endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH`; **`largest overlay over
  the board after the soak: econ 2%`** — the doctrine panel is no longer even the largest thing
  over the board.
- The full-cap fixture (`renderer_fixture.html`, `2164ce6`+`dd6669f`) builds the panel exactly
  as the page does at 280/48-rune caps and 360/720/1280 px, asserts its own strings are still
  full-cap (`fail('the fixture did not build full-cap strings')`), and ran green under
  `--strict-text-bounds` in the same job. `dd6669f`'s scroller exemption is a false-positive fix
  (content inside an `overflow-y:auto` box is clipped by the box; the box itself is still
  measured), not a loosened gate — and the red run it fixed (33833709379) is on the record.

## Refuted

None. All three findings were real at the reviewed tree (verified from the pre-fix code paths in
history: `chassis` was `KnownKeys[0]` and validated; no dismissal path existed for `#doctrines`;
the pre-fix chassis had no famine/mine-memory/BFS/king-defence behaviour) and all three are fixed
at head as evidenced above.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. CI green, no test loosened | PASS | Run 33834906008 `success` on main at head, 4/4 jobs green. Full-history `git log -p -- tests/` (repo is 1 day old) audited: no deleted assertion, no widened tolerance, no skip/xfail, no removed test file. The three r2 test edits adapt to the D1 surface change and each **adds** assertions (test_sheet gains the chassis-not-a-knob block; test_knob_sensitivity keeps the scaffold→awu wins gate via the filler path; `defaultsApplied.len >= 7 → >= 6` tracks one fewer knob existing, not a tolerance). Earlier history: `9ff4a07` strengthened the hash-chain test (first-divergent-round); `2ada617` inverted the tokens assertion because the certifier *requires* `config_schema` to declare tokens ("game.config_schema must require tokens", release 0.1.0 failure) while still asserting no game_config *value* pins tokens; `2ee91f9` made four vacuous checks real. |
| 2. Replay re-derivation | PASS | `test_determinism` (record → re-derive for every end reason, per-round hash chains since GV02) + `test_replay` (72 checks, strict UTF-8, recorded hashes reproduced), both green; the viewer's display comes from the wasm sim stepping the same rules (`replay-viewer/bc_replay.nim` `deriver.advance()`), not a parallel recording. |
| 3. Static viewer | PASS | Manifest `game.replay_viewer = {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` present, CI asserts the exec bit; no `/client/replay` path anywhere (grep clean; `/client/global`+`/client/player` are the ctf-lineage status pages, and 59e589a made `/global` explicitly not look like a live replay pod). |
| 4. Both name spaces | PASS | `decide.briefFor` sends `alias`/`opponent_alias` only (`Clan Ash`/`Clan Basil`, decide.nim:125-126); real names ride only in the replay's `names[]` (server.nim:397) and are drawn by the viewer scorebug ("CLAN ASH Clan Ash · …" in the smoke readout). |
| 5. Degrade-never-hang | PASS | Registration wait bounded by `connectTimeoutMs` (server.nim:241-259); doctrine phase bounded by `attempt1Ms`/`retryMs`/`doctrineBudgetMs` monotonic deadline with cleared-open fallback (decide.nim:151-187); per-game/match wall-clock guards (`perGameBudgetSeconds`/`matchBudgetSeconds` → `deadline`); heartbeat loop bounded by `viewersRunning`; smoke episode settled in ~21 s wall (design worst case 435 s ≤ 720 s). |
| 6. num_agents | PASS | `num_agents: 2` in `variants[0].game_config` and `certification.game_config` (checked from the template directly); `docker_smoke.sh` carries all four `SEAT-COUNT FAIL:` invariants plus the `SMOKE_SEATS` second declaration (lines 123-159); **zero** `SEAT-COUNT FAIL` occurrences in the docker-smoke log; `seats=2` printed. |
| 7. Scripted baseline full episodes | PASS | docker-smoke: all-scripted episode (awu+scaffold fixture) → `reason=complete`, both player containers exit 0, `fallbacks == [0,0]` asserted by the script; `test_baselines` (30 checks) audits every emitted order for legality in played games and both baseline sheets through the shared `sheet.validate()`; parameters carried by the paired-game measurement harness in `test_knob_sensitivity` (3 maps × 3 seeds per knob, thresholds in one table), not guessed. |
| 8. LLM reply handling | PASS | `extractJsonObject` tolerates fences/prose (sheet.nim:142-178); exactly one retry (`attempt < 2`, decide.nim:171); throttle fast-fail; fallback recorded per seat (`results.fallbacks`, `doctrine_fallback` events, `fallbackDetail`), countable by phase 60. |
| 9. Rune-safe truncation | PASS | `truncateRunes`/`truncateBytes` land on rune boundaries (sim_types.nim:142-166); `test_sheet` feeds U+1F400 at the notes/motto caps and 40 KB of astral text at the 16 KB byte cap and asserts valid cuts; `test_replay` strict-UTF-8-parses the written bytes with a 400-rune astral `fallbackDetail`. |
| 10. Manifest validates | PASS | `game.docs.readme` and all three `pages[].content` are `{type,value}` objects (type `uri`, per the design note §Packaging); `game.protocols` carries both `player` and `global` as `{type,value}`; the `test` job runs the coworld CLI's own `_load_template_manifest` over the template and accepted it in this run. |
| 11. Legible at 360 px | PASS | `#scorebug .plate-name { flex: 1 1 auto; min-width: 3.2em; }` (replay_broadcast.html:2561); labels hidden under 640 px in the inherited CSS; the D3 fixture renders at 360 px. |
| 12. Release order and scaffold | PASS | `coworld-release.yml`: build → certify → upload-policy (×N, explicitly before upload-coworld) → upload-coworld → secret put (explicitly after); all three workflows present; `docker_smoke.sh` executable (CI asserts); `policies.json`: 2 `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 (`battlecode-opportunist`) carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the three-name placeholder grep exits 0 (run in this sandbox against all five files). |
| 13. Viewer executes | PASS | `wasm-viewer` green **including** the browser step (`loaded:true, ms:312` on the docker-smoke replay; job `needs: docker-smoke`; step present, no `continue-on-error`); `data-replay-loaded` set on the first drawn frame (static_replay.js:180) and `data-replay-error` on failure (static_replay.js:14-20), both from the shell's own paths; playback axis is game rounds only — pre-match doctrine events carry `ms` and are feed lines, never frames (replay.nim event parse; bc_replay frames = `frameGame`/`frameRound`), so a recorded-lobby dwell cannot occur by construction; `config.nims` has **no** MODULARIZE/EXPORT_NAME and the worker's bootstrap is the matching `var Module = {}` + `Module.onRuntimeInitialized` + trailing `importScripts` — both halves from coworld-ctf. |
| 14. Chrome is the starter's | PASS | `client/chrome_common.js` and `client/broadcast_core.js` byte-identical to `/workspace/starters/coworld-ctf`'s (`diff` silent); everything above the `BATTLECODE additions to the inherited coworld-ctf chrome` banner is a pure line-subset of the starter's page (comm: 1 differing line, a comment divider) — removals only, matching the design note's list; transport rules hold: `--hudscale`/`--band` computed on `:root` by the inherited `relayout()`, `#endcard { bottom: var(--band, 0px) }` shown with `.on` (its own CSS class), `seek()` calls `dismissEndcard()` and transport buttons/keys dismiss it too (replay_broadcast.html:2865,3118,3146); beat markers are labelled `<button>`s via the chrome layer under a game-block function deliberately not named `markBeat`, with CSS for all six emitted kinds (2629-2634); `#viewpanel` kept — correct, the board (up to 60×60, 960 px native) is larger than the 360 px frame. |
| 15. Every drawn string fits | PASS | This viewer draws no canvas text (`canvas_text total: 0` — sprites on canvas, all text in DOM), so the strict-canvas gate has nothing to cover; the LLM-text class is covered by the required worst-case fixture: `renderer_fixture.html` lays both seats at full 280/48-rune caps in the page's own extracted CSS at 360/720/1280 px, asserts its own strings are still full-cap, fails via `data-replay-error` on any escape/overlap, and runs under `viewer_smoke.mjs --strict-text-bounds` as its own ci.yml step — green in this run (`loaded:true`, no error). `--strict-text-bounds` is dropped only on the pannable-board bundle run, exactly the case the checklist excludes, with counts still recorded. |
| One parallel batch | PASS | Both seats' requests go out in a single `client.curl.makeRequests(batch, …)` per attempt (decide.nim:191-208); seats are never queried sequentially. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| D1 | fixed in `96c0691`+`12ea9b8`; KnownKeys 10 entries, validate has no chassis branch, logged, filler path direct-sets, replay records applied chassis, GV04 | all confirmed from code and tests (see D1 above) | yes |
| D2 | fixed in 8 chassis commits + gate; nothing outside `years/bc26/chassis/` changed; pre-fix 8/11 checks fail; parity A/B green | commit stats confirm file scope; gate assertions match the ruling's thresholds; parity job green; post-fix numbers match the CI log verbatim. One quibble: the fixes doc says "the five parity maps" but the gate substitutes `dirtfulcat` for `arrows` — a strictly more failure-relevant map, disclosed nowhere; noted, not a weakening | yes, with the map-list wording caveat |
| D3 | fixed in 4 commits; dismiss on advance + 6 s timer, re-openable, capped body; CI gates obscuration > 50 %; fixture red run 33833709379 fixed forward | all confirmed from the page, harness, ci.yml and the green run's readouts (`econ 2%`) | yes |
| "no test weakened" | claimed | independently audited over the whole repo history; holds | yes |

## Non-blocking observations

- `tools/ci/check_gameversion.sh` cannot parse `GV04`-style versions and is not wired into
  ci.yml — the inherited guard is inert (the fixer's NOTED list already records this). The
  version bumps themselves were made correctly and in the same commits; advisory only.
- `viewer_smoke.mjs`'s endcard log line collapses runs of the letter "s" (template-literal `\s`
  eaten → `/s+/g`), which is why the run log shows "chee e delivered" — cosmetic, log-only, also
  in the fixer's NOTED list; the gates themselves avoid regexes.
- The page `<title>` is still "Paintbot — Broadcast Replay" — a verbatim starter line above the
  banner; harmless but worth a one-line follow-up.
- `mercifullattice` (the review's third observed map) is in the mixed pool and outside the
  king-survival gate's five; the operator's gate spec named the parity maps, so this is in-spec,
  but a future round could extend the gate to the mixed pool cheaply.

BLOCKING: 0
