blocking: 1

# r1 verdict — particle-worlds
Head: b6b4401ad9db9973387ab011150a73f65ab6e69c   Checklist: prompts/30-review-loop.md §ACCEPTANCE CHECKLIST (items 1–15 + simultaneous-decision clause)   Independent read written before reading fixes: yes

Reading order followed: checklist → design note (all 1695 lines) → the tree at b6b4401 and CI run
32961166140 (independent notes formed) → r1-review.md → r1-review-parallel.md → r1-fixes.md.
The fixer's table was read last and audited, not trusted. Not contaminated.

Both reviews were written at 99dcaab7; the tree has moved 13 commits since. Every finding below is
re-verified at b6b4401. The fixes file dispositions **only r1-review.md's F1–F18**; the parallel
review's findings have no disposition anywhere — two of them are the substance of this verdict.

---

## Standing blocking findings

### B1 — the wall-clock `deadline` stop mutates hashed state outside `sim.step`, then records a hash playback cannot re-derive   (source: reviewer — r1-review-parallel.md F2; premises independently re-verified at head)
- `- [correctness] src/mpe/server.nim:1409-1423 the deadline path banks the round and flips phase outside the step, and the same iteration writes that state's gameHash — a deadline replay mismatches at the stop tick`
- Where: `src/mpe/server.nim:1409-1423`, `:2070`, `:2240`; `src/mpe/sim_state.nim` `gameHash`;
  `src/mpe/scoring.nim:182-201`.
- Verified at head, every premise:
  1. `src/mpe/server.nim:1409-1423` — at the top of the loop iteration:
     ```nim
     deadlineHit = true
     sim.endReason = ReasonDeadline
     sim.endRule = EndRuleWallClock
     if sim.phase == Playing:
       sim.bankRound(sim.gameTicksElapsed(), EndRuleWallClock)
     ...
     sim.finishGame(Red, isDraw = true)
     quitAfterFrame = true
     ```
     `bankRound` (`scoring.nim:182-201`) appends to `sim.roundLog` and `inc sim.roundsPlayed`;
     `finishGame` flips `phase`/`winner`/`isDraw`. All of this happens **outside** `sim.step`.
  2. Those fields are hashed: `sim_state.nim` `gameHash` mixes `ord(sim.phase)`,
     `ord(sim.winner)`, `sim.gameOverTimer`, `mixHashBool(sim.isDraw)` at the head of the proc,
     and `result.mixHashInt(sim.roundLog.len)` / `for entry in sim.roundLog` at `:321-322`.
  3. The same iteration still steps and records: `quitAfterFrame` is consulted **only** at
     `server.nim:2240`, after the step block; the step runs (now down the GameOver branch) and
     `server.nim:2070` writes `replayWriter.writeHash(uint32(sim.tickCount), sim.gameHash())` —
     exactly one hash of a state reached by a server-side, unrecorded mutation.
  4. Nothing in the replay stream lets playback re-derive it: the wall-clock stop writes no
     record, and chat records are re-applied into non-hashed fields only (the repo's own rule,
     `docs/PROTOCOL.md`: "can never affect the simulation"). At playback the sim reaches that
     tick still `Playing`, without the banked `roundLog` entry, steps the Playing branch on the
     recorded (zero) masks, and `checkReplayHash` — an exact comparison — sets `mismatchTick`.
  5. Refutation attempts, all failed: no early `break`/`continue` between 1423 and the step
     block (the only `continue` in the span is inside `if shouldReset:`); no writeHash guard on
     phase; the `fault` path by contrast **breaks before `writeHash`** (`server.nim:2055-2060`),
     which shows the invariant is intended universally and the deadline path missed it. The
     pattern is starter-inherited (`coworld-ctf` `server.nim:1407-1420` has the same
     `finishGame`-then-step shape), but this fork **added** `bankRound` — more hashed mutation —
     onto the path, and this fork's design makes `deadline` a first-class, declared-acceptable
     ending (design.md:389).
- Checklist item: **2** — "Replaying the recorded events through the sim reproduces the recorded
  per-tick state **frame by frame** … A test asserts it." The test
  (`tests/test_replay.nim:134-163`) asserts it only for the `complete` path
  (`tests/test_endings.nim:71-98` reproduces the deadline sequence but never touches a hash).
  Every `deadline` episode — the ending the design reserves for a slow hosted LLM — records a
  final hash the viewer cannot re-derive, so `#mmwarn` fires on precisely the episodes phase 60 is
  told to accept, turning the "real integrity signal" (design.md:1085) into a false alarm.
- What would settle it: record an episode with `wallClockBudgetSeconds` short enough to stop
  mid-round and run it through the existing `parseReplayBytes` + `advanceReplayFrame` loop
  asserting `hashMismatchTick == -1`; the fix shape is the `fault` path's (settle the state, skip
  the post-mutation `writeHash`, or route the stop through the step).

---

## Refuted / resolved at head

### r1-review F1 (= parallel F3) — renderer fixture does not load the real renderer → FIXED at head
- Evidence: `tools/ci/renderer_fixture.html` at b6b4401 fetches `./index.html` (the shipped page)
  into an iframe, shims only the OffscreenCanvas transport, and drives the page's own
  `config.onText` with a full-cap 160-rune note on all four seats, non-silent symbols, and the
  crypto panel at 360/620/1280 px; `tests/test_viewer.nim` ("the worst-case renderer fixture
  drives the REAL page") pins `fetch('./index.html'`, `config.onText(worstCaseFrame(` and
  `"drawBoard" notin fixture`. CI 32961166140 fixture step:
  `fixture canvas_text: total=302 never_inside=0 outside=0`, and `ci.yml:375-390` **asserts**
  `total > 0` and `never_inside == 0`. The fix also found and fixed a real 360 px clipping defect
  (`.feed-row.mpe-note-row { white-space: normal; max-width: calc(228 * var(--u)) }`,
  `client/replay_broadcast.html:4380-4383`, test-pinned). Item 15 now passes on real evidence.

### r1-review F2 (= parallel F13) — chrome_common.js patch not recorded in the design note → FIXED
- Evidence: `diff` against the starter is exactly one line (`client/chrome_common.js:72`,
  `window.CTF_WIRE` → `window.MPE_WIRE`); the run's `design.md` now carries
  "## Amendment — r1 review (2026-08-26)" naming that patch, and
  `docs/plans/2026-08-26-particle-worlds-design.md` carries it inline (commit `eee8254`).
  Item 14's "named, minimal patch recorded in the design note" is now literally true.

### r1-review F3 — rate-floor sleep inside the turn budget suppresses the retry → FIXED
- Evidence: `src/mpe/decide.nim` — after the spacing sleep, `turnStart = engine.lastBatchStart`
  ("The rate floor is a WAIT, not work, so the per-turn budget starts HERE"). New test
  "the rate floor never eats the single retry" (`tests/test_engine.nim:257+`) runs a nonzero
  floor against a hung provider and asserts the seat-turn record reads `attempt: 2`,
  `cause: "timeout"`, no budget-exhausted detail — i.e. the retry was issued. Item 8 holds at the
  shipped settings.

### r1-review F4 — multiple `fallback` records per seat-turn → FIXED
- Evidence: `decide.nim` accumulates per-attempt cause/detail in per-seat state and the tail
  block writes **one** record per seat-turn stamped with the attempts actually spent;
  `tests/test_engine.nim` asserts `fallbacks == 4` (one per seat, `seat notin seatsSeen`),
  `attempt: 2` on the retry path and `attempt: 1` on the throttle path;
  `docs/PROTOCOL.md` states record-count == `sum(results.fallbackTurns)`. Item 8's countability
  holds.

### r1-review F12 — certify step lacked `--timeout-seconds 300` → FIXED
- Evidence: `.github/workflows/coworld-release.yml:178` — `--timeout-seconds 300 \` (commit
  `646e358`). (Was never a checklist item; item 12's step order was already correct.)

### r1-review F14 — landmark sampler `while true` unbounded → FIXED
- Evidence: `src/mpe/field.nim:120,155` — `MaxLandmarkDraws = 4000`, `while attempts <
  MaxLandmarkDraws`, deterministic lattice sweep fallback (draws no RNG, so terminated seeds are
  byte-identical); `sim_config.nim:784-809` rejects a `landmarkMargin` whose box cannot hold four
  marks at the guard's spacing; both sides test-pinned in `tests/test_field.nim`. Item 5 holds.

### r1-review F16 — stream tests weaker than the note's spec → FIXED
- Evidence: `tests/test_replay.nim` at head asserts one directive per seat per (round, turn)
  group (`check count == FixtureSeats`) and adds an `onpoint` detector block asserting the belief
  crossing and the derived event (commit `2b3d6c2`).

### r1-review F7/F8/F10 (= parallel F8/F9/F7) — prompt/comment/tag-live-score → FIXED
- Evidence: `llm.nim:254-256` now states the tag exception ("EXCEPT as a TAG pursuer, where it
  closes on the evader to contact range (10 pixels)"); `baselines.nim` comment corrected
  (`37a6805`); `decide.nim:172` now uses `sim.tagRoundPermille(scoreSeat, elapsed)` in a `tag`
  round, test-pinned from both sides in `tests/test_observation.nim`.

### r1-review F18 (`.tiny` at 620 vs "640px") → REFUTED as a finding
- Evidence: `client/replay_broadcast.html:4093` `stage.classList.toggle('tiny', boardW <= 620)`
  is byte-identical to the starter's line; the label-hiding rules under `.tiny`
  (`:4197-4198,4254,4290,4323-4325`) are present and test-pinned. Item 11's mechanism is the
  starter's density system, and the width that matters (the ~360 px embed) is far below either
  number; the fixture now measures that width directly. Item 11 passes.

### r1-review F15 (= parallel F14) — `/client/replay` pod route → NON-BLOCKING (ruled)
- Evidence: `coworld_manifest_template.json` `game.replay_viewer == {"bundle":
  "static-replay-viewer"}`; the static bundle's only network call is
  `fetch(message.replayUrl, {credentials:'omit', mode:'cors'})`
  (`static_replay_worker.js:113-116`). The `/client/replay` route in `src/mpe/server.nim:824-853`
  is byte-inherited from the starter (`coworld-ctf` has the identical block) and serves the live
  in-episode board; no platform routing points at it. I read item 3's "no `/client/replay` pod
  path anywhere" as: the platform's replay viewing must not be a pod path — which is satisfied.
  Removing the inherited route would violate item 14's provenance rule to change nothing a hosted
  replay touches.

### parallel F12 — `core.zoomAt/setZoom/panBy` gesture wiring survives → NON-BLOCKING (ruled)
- Evidence: at head the panel, its ids, markup, CSS, `attachMinimap(`, `ZOOM_STEP`,
  `SLIDER_TRAVEL` and the z/x keys are all gone and test-pinned absent
  (`tests/test_viewer.nim:42-61`); what survives are the starter's pointer-gesture handlers
  (`replay_broadcast.html:3895,3912,3967-3981`). `broadcast_core.js` (byte-identical by mandate)
  clamps `minZoom = 1` ("1 IS fitted whole") and `panBy` no-ops at zoom 1
  (`broadcast_core.js:252,499,510`), so a spectator cannot be stranded off the fitted view. Item
  14's removal list targets the `#viewpanel` overlay and its wiring, which is removed rather than
  hidden. Advisory: the surviving handlers could be deleted for strictness.

### parallel F5 — float-grep scope / the `99dcaab` matcher change → NOT a loosening (ruled, item 1)
- Evidence: the full `git log -p --since=<run start> -- tests/` was read hunk by hunk. Nine
  commits touch `tests/`; all are additive except two adjudicated replacements:
  (a) `99dcaab` replaces a substring scan with a whole-identifier matcher because `isqrt(` — the
  integer sqrt that exists so the hashed path never calls libm — contains `sqrt(`; the `check`
  remains, the module list is unchanged, and banned calls are still caught.
  (b) `b6b4401` replaces `check recordedWindows().len == 8` with assertions on the fallback
  records (`attempt: 2`, `cause: "timeout"`, no budget-exhausted detail, ×4): the old assertion
  was demonstrated wrong-vantage by red run 32960167875 (curl abandons timed-out calls; mummy
  drops handlers for disconnected clients — windows cannot prove issuance), and the new one
  distinguishes fixed from broken, which the old could not. Neither is a deleted assertion,
  widened tolerance, skip, or removed file. The uncovered-module concern: `control.nim` is
  float-free by direct grep, the float procs in `sim*.nim` are unreachable from the particle step
  body, and the native↔wasm gate replayed 300 frames clean at head. Item 1 holds.

### parallel F4 — no grid harness for the baselines → NON-BLOCKING (ruled, item 7)
- Evidence: item 7's falsifiable content is present and green — `tests/test_control.nim:37-77`
  (4 000 legality checks: own id, enum intent, in-box target, one-rune symbol, never A/C/Up+Down/
  Left+Right), `:180-241` (all-scripted 4-round episode completes; cover ≥ 80 %; crypto Bob on
  goal; drifter beats beeline at the pinned seed), `tests/test_endings.nim:50-63`
  (`reason == "complete"`, `endRule == "full_time"`, `roundsPlayed == 4`),
  `tests/test_replay.nim:352` (same from the replay bytes). No literal grid-search harness exists
  anywhere in the tree; the baselines have no free numeric parameters beyond design constants
  whose values carry measured in-code rationales (e.g. the tag stand-off, chosen from a measured
  71 px closest approach, `control.nim`). I rule the item's substance satisfied and record the
  missing harness as an observation, consistent with both reviewers (neither raised it as
  blocking).

### r1-review F5/F6/F9/F11/F13/F17 and parallel F6/F10/F11/F15/F16(3rd)/F17/F18/F19 — advisory then, advisory now
- One Bedrock candidate (measured, documented in-code; degrade paths verified); prompt's
  mode/role pointer line (mode and role reach the model in the view JSON every turn);
  `results.bumps` = last round's counter (now documented in `docs/PROTOCOL.md`, alternative is
  NEEDS-DESIGN — a hashed accumulator and a GameVersion bump); dead starter modules
  (`paint.nim`, `map_pool.nim`, `mapgen_styles.nim`) present but unreachable from any hosted
  config (52-property `additionalProperties: false` schema); protocols.player == protocols.global
  (item 10 requires both keys in object form — they are); stale `DefaultTurnSpacingMs = 5000`
  (every shipped variant and the schema default carry 9000); no never-connecting-seat test
  (design-note spec, not a checklist item); state JSON carries three keys beyond the note's list
  (docs and code agree); wall-stop asserts carry-cleared not velocity-zeroed (disclosed, the
  inherited integrator's real behaviour). None ties to a checklist item; none counted.

---

## Non-blocking observations (judge)

- **`intHold` steers to the round spawn point, not the position at order install**
  (parallel-review F1, re-verified at head, no disposition from the fixer).
  `src/mpe/control.nim:376-380` reads `(sim.holdX[seat], sim.holdY[seat])`; the only writers are
  `src/mpe/field.nim:239-240` inside `placeParticles` (once per round). Nothing updates them at
  the turn boundary, so an LLM particle that has moved and then orders `hold` is navigated back
  toward its spawn on the 250 px ring — while the shipped prompt says "hold = brake and stay
  where you are" (`llm.nim:252-253`) and the design note says "the particle's own position at the
  tick the order was installed" (design.md:772-774). Legal, bounded, deterministic and
  re-derivable (`holdX` is set inside the step path), so it falsifies no checklist item — but it
  is the same prompt-vs-controller class as F7, which was judged worth fixing, and it misleads
  every LLM seat in every mode. Strongly recommend for r2: store `holdX/holdY` at directive
  install, or reword the prompt.
- The scripted baselines' hold-users are unaffected in practice (drifter's Alice is anchored;
  drifter's Bob holds from spawn), which is why no test caught it.
- `viewer-smoke.json`'s `never_inside` is keyed by string across the three fixture widths (the
  fixer's own NOTED item); the fixture's per-width DOM check (`data-replay-error` on any
  out-of-frame text run) is the strict gate covering that seam. Verified both exist.

---

## Checklist pass (independent)

| item | status | evidence (path:line or run id) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 32961166140 conclusion success at b6b4401 (test / docker-smoke / wasm-viewer all ✓); `git log -p --since="2026-08-26T05:56:00Z" -- tests/` read hunk by hunk — additive in all files; the two replacements adjudicated above as not loosenings |
| 2 replay re-derivation | **FAIL — B1** | test asserts frame-by-frame for `complete` (`tests/test_replay.nim:134-163`); viewer derives from the same re-derivation (`replay-viewer/mpe_replay.nim` imports `src/mpe/sim`; `replay_runtime.nim` builds packets from the re-simulated sim); but `server.nim:1409-1423` + `:2070` record a non-re-derivable hash on the `deadline` path |
| 3 static viewer | PASS | `coworld_manifest_template.json` `game.replay_viewer == {"bundle":"static-replay-viewer"}`; `tools/build_replay_viewer.sh` mode 100755, asserted in `ci.yml:237-248`; bundle's only network call is the replay URL (`static_replay_worker.js:113-116`); `/client/replay` ruled a starter-inherited pod dev page, not platform viewer routing |
| 4 both name spaces | PASS | `tests/test_identity_privacy.nim` sentinel asserted absent from every seat-facing byte and present in `buildStateJson`/`roster[].name`/`results.names`; CI smoke scorebug shows real names ("○ P1 GOOD 0.649 …") |
| 5 degrade-never-hang | PASS | every wait bounded (two whole-second deadlines validated by `sim_config.nim:739-757`; `turnBudgetMs` monotonic cap; bounded spacing sleep; `lobbyJoinTimeoutTicks`; 690 s stop at `server.nim:1409`; 20 s shutdown grace); sampler bounded at head (`field.nim:120,155` + config rejection); 690 ≤ 720 = 60 % of 1200, asserted by `tests/test_manifest.nim` |
| 6 num_agents | PASS | 4 in all five variants + `certification.game_config` + `config_schema` (integer 4..4); `docker_smoke.sh:106-152` enforces all four invariants + `SMOKE_SEATS` cross-check; `grep -c "SEAT-COUNT FAIL"` over run 32961166140's full log = **0**; smoke printed `reason=complete`, seats=4 |
| 7 scripted baseline full episodes | PASS | `tests/test_control.nim:37-77,180-241`; `tests/test_endings.nim:50-63` (`reason == "complete"`); `tests/test_replay.nim:352`; grid-harness clause ruled satisfied-in-substance (measured in-code rationales + comparative test bar), see above |
| 8 LLM reply handling | PASS | tolerant parse (`directives.nim:126-165` + 13 repair cases in `tests/test_directives.nim`); retry exactly once, now reachable at shipped settings (`decide.nim` turnStart after the floor; `tests/test_engine.nim` retry + throttle-fail-fast + hung-provider tests); one countable `fallback` record per seat-turn |
| 9 rune-safe truncation | PASS | `directives.nim:63-70` sole shortening primitive (`runeLen`/`runeSubStr`); caps 160/48/200/900/4000 all routed through it; `tests/test_directives.nim:123-148` 4-byte emoji on the cap, valid UTF-8, round-trips; end-to-end via `replay_summary.py` in `tests/test_replay.nim` |
| 10 manifest validates | PASS | `game.docs` = readme text (7 207) + 3 pages each `{id,title,content:{type:"text",value}}`; `game.protocols` both `player` and `global` in object form; parsed directly from the JSON |
| 11 viewer legible 360 px | PASS | `.plate-name { flex: 1 1 auto; min-width: 3.2em; overflow: hidden; text-overflow: ellipsis }` at `replay_broadcast.html:4152-4157` (starter's rule verbatim); labels hidden under `.tiny` (`:4197-4198` etc.), the starter's breakpoint; fixture renders and gates 360 px directly |
| 12 release order and scaffold | PASS | `coworld-release.yml`: build(:153) → certify(:167, `--timeout-seconds 300`) → upload-policies(:210) → upload-coworld(:308) → secret put(:346); all three workflows present; both scripts 100755; `policies.json` 2 × `PLAYER_PROMPT` champions (cipher carries `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) + 2 scripted fillers; placeholder grep over the three names returns nothing (exit 1 → gate exits 0) |
| 13 viewer executes | PASS | run 32961166140 `wasm-viewer` green **including** "Load the bundle in a real browser" (`{"loaded":true,"ms":1606,…}`, soak advanced 0→241→289/1035); `needs: docker-smoke` (`ci.yml:224`), no `continue-on-error`; `data-replay-loaded` set in the `'loaded'` branch after `ingestPacket` (`static_replay.js:158-162`), `data-replay-error` in `showFailure()` (`:8-20`); `config.nims` non-MODULARIZE + worker `Module.onRuntimeInitialized` — one starter, diff-verified rename-only; determinism gate `ok: … advanced 300 frames` |
| 14 chrome is the starter's | PASS | `chrome_common.js` diff = 1 line (now recorded in the design-note amendment); `broadcast_core.js` diff = 1 line; page = starter + one appended block at `:4125`; CSS above the banner diffs against the starter as removals-only (viewpanel/hearts/paintball/dead beat kinds — the note's exact list) plus one comment word; transport rules (a)–(d) all verified in the page and pinned by `tests/test_viewer.nim`; beat CSS covers exactly the five emitted kinds; `#viewpanel` removed, not hidden |
| 15 drawn strings fit | PASS | `--strict-text-bounds` on both smoke steps (`ci.yml:336,371`); fixture drives the **shipped** page (`fetch('./index.html'`) and CI printed `fixture canvas_text: total=302 never_inside=0 outside=0`, with `ci.yml` asserting total>0 and never_inside==0; note rows wrap in a reserved band (`.mpe-note-row`), never shortened; the viewer's own `total: 0` is treated as evidence of nothing, which is why the fixture exists |
| simultaneous batch | PASS | one `RequestBatch` per turn via `client.curl.makeRequests` (`decide.nim`); `tests/test_engine.nim` "all four seats' calls go out in ONE parallel batch" proves it against a real localhost provider: 4 windows, wall time < 4× hold, server-side window overlap — green in CI |

---

## Fixer report audit

| finding (r1-review) | fixer said | I verified | agrees |
|---|---|---|---|
| F1 fixture | fixed `46cf69d` | fixture fetches shipped `index.html`, drives `config.onText`, `drawBoard` gone; CI total=302 never_inside=0; ci.yml asserts both; found+fixed a real 360 px note-clipping defect | yes |
| F2 chrome note | fixed `eee8254` | amendment present in run design.md **and** repo plans copy; diff is the one line | yes |
| F3 budget/floor | fixed `2090877`+`b6b4401` | `turnStart = engine.lastBatchStart` after the sleep; new nonzero-floor test asserts the retry via the record stream | yes |
| F4 fallback records | fixed `66d1099` | tail block writes one record/seat-turn; tests assert ==4, one per seat, attempt semantics both paths | yes |
| F5 one model | REFUTED | in-code measured rationale (`llm.nim:74-83`); degrade paths verified; advisory anyway | yes |
| F6 prompt line | REFUTED | mode+role reach the model in the view JSON; advisory | yes |
| F7 tag shadow prompt | fixed `295084b` | `llm.nim:254-256` states the exception | yes |
| F8 stale comment | fixed `37a6805` | comment corrected | yes |
| F9 bumps semantics | documented `6eccd8b` | `docs/PROTOCOL.md` states last-round scope; episode total legitimately NEEDS-DESIGN (hashed accumulator + GameVersion) | yes |
| F10 tag live score | fixed `60e3643` | `decide.nim:172` uses `tagRoundPermille`; tests both directions | yes |
| F11 dead modules | NEEDS-DESIGN | unreachable at runtime (verified gates + schema); removal touches the hashed path — not fixer-sized | yes |
| F12 certify timeout | fixed `646e358` | `--timeout-seconds 300` at `coworld-release.yml:178` | yes |
| F13 protocols identical | REFUTED | item 10 needs both keys in object form; they exist | yes |
| F14 sampler | fixed `e92b6b6` | `MaxLandmarkDraws` bound + lattice fallback + config rejection, test-pinned both sides | yes |
| F15 /client/replay | REFUTED | ruled non-blocking (see above) | yes |
| F16 stream tests | fixed `2b3d6c2` | per-(round,turn) directive count + onpoint detector | yes |
| F17 grep matcher | no action | adjudicated not a loosening (see item 1) | yes |
| F18 620 vs 640 | REFUTED | starter's own line; ruled item 11 satisfied | yes |
| **parallel F1 intHold** | **no disposition** | reproduces at head — recorded as a non-blocking observation with a strong r2 recommendation | n/a |
| **parallel F2 deadline hash** | **no disposition** | reproduces at head — **standing blocking B1** | n/a |
| parallel F12 zoom wiring | no disposition | ruled non-blocking (minZoom=1 clamp; panel and its wiring removed) | n/a |

The fixer's "no test was disabled, skipped, loosened or deleted" claim was checked against the
full `git log -p -- tests/` for the run window and holds under the adjudications above. The
fixer's CI citations (run 32961166140, SEAT-COUNT grep 0, `smoke OK: seats=4 … reason=complete`,
wasm gate `advanced 300 frames`) were re-pulled from the log and match. The fixes file's blind
spot is structural: it dispositions only r1-review.md and never mentions r1-review-parallel.md,
which is where the one standing finding lives.

---

## Blocking findings, one line each

- [correctness] src/mpe/server.nim:1409-1423 the wall-clock deadline stop banks the round and flips phase outside sim.step, then the same iteration records that state's gameHash (server.nim:2070) — a deadline replay cannot re-derive its final recorded hash, falsifying checklist item 2 for a declared-legal episode ending

BLOCKING: 1
