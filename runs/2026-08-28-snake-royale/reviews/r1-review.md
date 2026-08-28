# r1 review — snake-royale

Repo: `Metta-AI/cogame-snake-royale` @ `f985499c563359a169cf6f5bea31ef04ccf28985` (confirmed
`git rev-parse main`; matches the sha in the brief).
Design note: `/workspace/coworld-builder/runs/2026-08-28-snake-royale/design.md` (1674 lines) —
verified byte-identical to the repo's `docs/plans/2026-08-28-snake-royale-design.md` (`diff -q`, no
output).
Starter: `/workspace/starters/coworld-ctf` (read-only mount, used for provenance diffs).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST (read in full before the code).
Files read: 62 (all of `src/snake/`, both entry `.nim`, all 15 `tests/test_snake_*.nim`,
`replay-viewer/*`, `client/*`, all three workflows, `tools/ci/*`, `tools/*.nim`,
`tools/replay_summary.py`, `scripts/build_replay_page.py`, `coworld_manifest_template.json`,
`Dockerfile*`, `compose.yaml`), plus the starter counterparts of nine of them.
CI evidence: run `33144094331` (`gh run view`), conclusion `success`, headSha
`f985499c563359a169cf6f5bea31ef04ccf28985`, jobs `test` / `docker-smoke` / `wasm-viewer` all ✓;
artifacts `smoke-replay`, `viewer-smoke`, `static-replay-viewer` downloaded and read.

This report is observations only. Findings are numbered F1…F25 and tagged with the
acceptance-checklist area they touch; the judge decides blocking status. Each finding says whether
it is **observed** (I read it / read a CI artifact), **inferred** (I reasoned from code I read), or
**untested** (would need a run to settle).

---

## Findings

### F1 — the scrubber and the beat buttons seek by sending a **tick** to a runtime that parses a **fraction**; every non-zero seek lands on the last frame
*Area: static-viewer (checklist 13 "Playback…"/14(c) "every seek takes the endcard down"). Observed, with CI evidence.*

- Sender, `client/replay_broadcast.html:1454-1458` (inherited from the starter verbatim —
  compare `/workspace/starters/coworld-ctf/client/replay_broadcast.html:3940`):
  ```js
  function seekToFraction(s, frac) {
    var st = Math.max(0, s.st || 0);
    var mx = Math.max(st + 1, s.mx || 1);
    send('s:' + (st + Math.round(frac * (mx - st))));       // an absolute TICK, 0..mx
  }
  ```
- Receiver, `src/snake/replay_runtime.nim:316-322`:
  ```nim
  of 's':
    let parts = text.split(':')
    if parts.len == 2:
      try: rt.seekFraction(parseFloat(parts[1]))
  ```
  and `seekFraction`, `src/snake/replay_runtime.nim:288-293`, clamps its argument to `[0.0, 1.0]`
  and sets `frame = int(f * last)`.
- In the starter the same wire word is read as an integer tick
  (`/workspace/starters/coworld-ctf/src/ctf/global.nim:1853-1856`: `if item.text.startsWith("s:")
  … state.replaySeekTick = tick`). The fork changed the receiver's semantics and kept the sender.
- Trace: with `st = 0` and `mx = 40` (a 40-turn cert replay), a click at 50 % sends `s:20`;
  `parseFloat("20") = 20.0`; `seekFraction` clamps to `1.0`; `frame = totalFrames-1`. Only
  `frac == 0` round-trips correctly. The same path is used by every scrubber beat button
  (`client/replay_broadcast.html:1786-1788`: `CTX.seekToFraction(now, frac)`).
- **CI confirms it.** `viewer-smoke.json` (artifact `viewer-smoke`, run 33144094331):
  ```json
  "scrub": [ {"at":"0%",  "clock":"ALIVE 3/4 turn 20/40 …"},
             {"at":"50%", "clock":"ALIVE 2/4 turn 40/40 …"},
             {"at":"100%","clock":"ALIVE 2/4 turn 40/40 …"} ]
  ```
  The 50 % click produced turn 40/40. (`viewer_smoke.mjs:571` records the "0%" row from the
  pre-existing readout without clicking, so only the 50 %/100 % rows are seeks.) `viewer_smoke.mjs`
  logs these three but does not gate on them, which is why the job is green.
- Second-order consequence (**inferred**, not directly observed): the endcard is driven purely by
  `if (!s.over || !s.results) { card.classList.remove('on'); return; } … card.classList.add('on')`
  (`client/replay_broadcast.html:1875-1905`) and `over` is `turn >= turns`
  (`src/snake/broadcast.nim:107`). A scrub click that jumps to the last frame therefore *raises*
  the endcard rather than dismissing it, so the scrubber cannot pull the match back from the score
  screen. Keyboard `,` / `b` / `.` / `e` are unaffected — they send frame-relative commands
  (`replay_runtime.nim:302-307`).
- What the note says: §Transport rules — "the endcard … is **dismissed by every seek**"; §Readouts
  10 — "the scrubber with its seven beat kinds"; §Chrome provenance — `snakeBeat` "appends a
  `<button>` … and **seeks on click**".

### F2 — the shipped baseline tunables are not the design's table, and `coil` loses the ladder to `forager`; the test that was to assert "coil beats forager" was replaced
*Area: correctness (checklist 7 "tuned with a grid harness, not guessed"; checklist 1 "no test loosened"). Observed.*

- Design §The two scripted baselines (design.md:538-545) tabulates
  `coil = (spaceWeight 1000, spaceCap 2, headRiskPenalty 900, killBonus 120, foodWeight 8,
  hungerThreshold 12)` and `forager = (400, 1, 500, 60, 40, 999)`.
- Shipped, `src/snake/baselines.nim:47-52`:
  ```nim
  CoilTunables*    = Tunables(spaceWeight: 100, spaceCap: 4, headRiskPenalty: 900,
                              killBonus: 120, foodWeight: 400, hungerThreshold: 12)
  ForagerTunables* = Tunables(spaceWeight:  40, spaceCap: 1, headRiskPenalty: 500,
                              killBonus:  60, foodWeight:  40, hungerThreshold: 999)
  ```
  Four of twelve numbers differ (coil `spaceWeight` 1000→100, `spaceCap` 2→4, `foodWeight` 8→400;
  forager `spaceWeight` 400→40). Note the sign of the change: `foodWeight` multiplies the *distance
  to the nearest food* as a penalty (`baselines.nim:98`), so shipped `coil` weights food ten times
  more heavily than `forager` does, which inverts the note's "coil is the survival heuristic: space
  first, food only when hungry or free".
- A real sweep exists and the pick is in it: `tools/tune_baselines.nim:31-42` sweeps
  `spaceWeight ∈ {100,300,1000} × spaceCap ∈ {2,4} × foodWeight ∈ {8,100,400}` over the 24-episode
  ladder in `src/snake/engine.nim:109-131`. `ci.yml:98-107` runs `--sweep --check`. The CI log
  (`test` job, step "Sweep and verify the scripted-baseline tuning") prints all 18 candidates;
  **every one has a negative margin**, best `-0.09708…` at the shipped `(100, 4, 400)`.
- `tools/ci/baseline_tuning.json:40-45` records `coilPermille -2330 / foragerPermille +2330`,
  `coilTurns 1646 / foragerTurns 1964`, `"margin": -0.09708333333333333`. So `forager` — the seat
  the note calls "the thing a champion should be able to beat" — out-scores and out-survives
  `coil`, which is the certification player, the per-turn fallback and the default for an
  unregistered seat (`src/snake/control.nim:10`).
- Design §Tests 27 says the test asserts "`coil`'s mean score over that ladder beats `forager`'s by
  a margin inside `[+0.30, +1.20]`". Commit `a8fbdfd` ("pin the scripted baselines to the measured
  ladder instead of an unverified claim") replaced
  ```nim
  c.check(margin > 0.0, "coil out-survives forager over the recorded ladder …")
  ```
  with `tests/test_snake_control.nim:220-229`:
  ```nim
  c.check(abs(margin) >= 0.05, "coil and forager are materially different players …")
  c.check(totals.coilPermille + totals.foragerPermille == 0, …)
  c.check(totals.perModule[1].coilPermille > 0, "coil wins the geese ladder …")
  ```
  `abs()` makes the assertion satisfied by a negative margin. The same commit *added* pins the
  design did not ask for (exact total and per-module permille/turn integers,
  `test_snake_control.nim:196-215`, measured through the one `ladderTotals` proc the `--check` path
  uses). The commit message states the reason and cites the sweep. Recording both halves: a
  directional assertion was removed; strictly stronger regression pins were added in its place.

### F3 — test 13's "`trapped` is emitted" assertion was replaced by a tautology
*Area: correctness (checklist 1 "no test disabled, skipped, or loosened during this run"). Observed.*

`tests/test_snake_sim.nim:371-394`, the block whose own docstring says "``trapped`` is emitted
EXACTLY on the false-to-true transition":
```nim
  var pending: seq[tuple[turn, slot: int]]
  for e in played.events:
    if e.kind == ekTrapped: pending.add((e.turn, e.slot))
  check pending.len >= 0, "13: the trapped stream is well formed"
```
`pending.len >= 0` is true for every possible run. The two loops that follow iterate the same
(possibly empty) set. Nothing asserts that a `trapped` event occurred at all, nor that it fires on
the transition. `git show 5537503 -- tests/test_snake_sim.nim` shows what it replaced:
```
-  check sawTrapped or not state.snakes[0].alive, "13: trapped is emitted"
```
The commit ("fix the second CI round … and four test defects") rewrote a hand-built pocket case
that had become ambiguous; the free-space half was strengthened (`test_snake_sim.nim:357-369`, an
exact two-cell pocket) but the emission half was not replaced.

### F4 — `turnBudgetMs` is measured from before the `turnSpacingMs` sleep, so in steady state the single retry batch is pre-empted
*Area: timeout (checklist 8 "retries once on a parse or transport failure"). Observed in the code; untested at runtime.*

`src/snake/decide.nim:189-192` sets `turnStart = getMonoTime()` at the top of the turn.
`decide.nim:238-241` then sleeps the rate floor:
```nim
  if open.len > 0 and engine.batchStarted and episode.config.turnSpacingMs > 0:
    let since = (getMonoTime() - engine.lastBatchStart).inMilliseconds.int
    if since < episode.config.turnSpacingMs:
      sleep(episode.config.turnSpacingMs - since)
```
and `decide.nim:251-255` guards each attempt against the same `turnStart`:
```nim
    if getMonoTime() - turnStart >= budget:      # budget = turnBudgetMs = 11 000 ms
      for slot in open:
        result.add(fallbackRecord(turnIndex, slot, attempt + 1, "timeout", …))
      break
```
Arithmetic with the shipped constants (`sim_types.nim:97-98`: `attempt1Ms 6000`, `retryMs 3000`,
`turnBudgetMs 11000`, `turnSpacingMs 9000`): batch starts are held 9 s apart, so the sleep on turn
*k* lasts `9 s − L(k−1)` where `L(k−1)` is the previous turn's call latency, and the budget left
for this turn's calls is `11 − (9 − L(k−1)) = 2 + L(k−1)` seconds. With the note's own typical
figure ("a four-call batch measures ≈4 s", design.md:479-481) that is 6 s — exactly attempt 1's
deadline — so a seat that fails attempt 1 gets a `timeout` fallback record at `decide.nim:253`
instead of entering the retry batch. The retry only fits when the previous turn already ran the
full 6 + 3 s. Every path still ends in a legal direction (`decide.nim:315-329`), so this is a
retry-coverage observation, not a hang.

This shape is **inherited verbatim** from the starter (`/workspace/starters/coworld-ctf/src/ctf/
decide.nim:326-402` has `turnStart` before the same rate floor), and the note says the loop shape is
"kept" (design.md:671). The note's D3 (design.md:252-254) and §Degrade table (design.md:497)
nonetheless describe an unconditional retry batch.

### F5 — the real bundle draws in a Worker/OffscreenCanvas, so `--strict-text-bounds` measures nothing on it; the renderer fixture is the only text coverage, and its evidence is not uploaded
*Area: legibility (checklist 15). Observed, with CI evidence.*

- `replay-viewer/static_replay.js:88-92` transfers the canvas:
  `offscreen = canvas.transferControlToOffscreen()`, and `static_replay_worker.js` imports
  `broadcast_core.js` and draws there (`static_replay_worker.js:239`).
- `tools/ci/viewer_smoke.mjs:360` hooks only
  `window.CanvasRenderingContext2D && window.CanvasRenderingContext2D.prototype` from an
  `addInitScript` (`viewer_smoke.mjs:467`); `OffscreenCanvasRenderingContext2D` in a Worker global
  is not patched.
- CI result for the shipped bundle (`viewer-smoke.json`):
  `"canvas_text": {"total": 0, "outside": 0, "ellipsized": 0, "never_inside": 0}`, i.e. the
  checklist's "`total: 0` means the check covered nothing" case. `ci.yml:326` does carry
  `--strict-text-bounds` on that invocation.
- The repo does ship the required worst-case fixture. `tools/ci/renderer_fixture.html` loads the
  built bundle's own `broadcast_core.js` (`renderer_fixture.html:41`) on a main-thread canvas,
  drives a full-cap 24-rune `say` on all four seats including two on row 0
  (`renderer_fixture.html:46-48, 108-116`), a three-way head-on flash, a trapped seat, all three
  board shapes at 360/640/1024 px, and self-checks its own string length against the server cap
  (`renderer_fixture.html:148-157`). `ci.yml:329-352` runs it under
  `viewer_smoke.mjs --strict-text-bounds`. CI log, step "Drive the worst-case text chrome":
  `canvas text: 72 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.
- Two gaps in that fixture's evidence chain: it writes to `--out "$PWD/fixture"`
  (`ci.yml:351`) while the upload step collects only root-level `viewer-smoke.png` /
  `viewer-smoke.json` (`ci.yml:356-365`), so the fixture's `canvas_text` line exists only in the
  job log; and the fixture drives `roster: []`, `beats: []`, `lead: {pts: []}`, `duel: -1`
  (`renderer_fixture.html:90-91, 89`), so the scorebug plates, the beat markers, the length ribbon
  and the duel banner named in design §Tests 48 are not exercised by it.

### F6 — the say bubble is measured from the actual string in `system-ui`, not laid out from `MaxSayRunes` in `data/font.ttf`, and no band is reserved when nobody is speaking
*Area: legibility (checklist 15 "a reserved band in the layout, sized from the cap the server enforces … measured in the font it will be drawn in"). Observed.*

`client/broadcast_core.js:371-403`:
```js
var font = Math.max(9, Math.round(g.cell * 0.42));
ctx.font = font + 'px system-ui, sans-serif';
…
var w = Math.min(ctx.measureText(text).width + font, g.pxW - 4);
var h = font * 1.8;
var x = g.ox + (b.x + 0.5) * g.cell - w / 2;
var y = g.oy + b.y * g.cell - h - 2;
if (x < g.ox + 2) x = g.ox + 2;
if (x + w > g.ox + g.pxW - 2) x = g.ox + g.pxW - w - 2;
if (y < g.oy + 2) y = g.oy + (b.y + 1) * g.cell + 2;   // top-row snake: bubble flips below
if (y + h > g.oy + g.pxH - 2) y = g.oy + g.pxH - h - 2;
```
The four-sided clamp is real and is what the fixture's `never_inside: 0` at 360 px demonstrates.
What differs from design §Readouts 9 (design.md:1168-1171): the box is sized from the *actual*
string at draw time rather than from `MaxSayRunes = 24`; the font is `system-ui, sans-serif`, not
`data/font.ttf`; and the layout reserves nothing when no seat is speaking, so the board region does
not hold a constant band. Also, if `measureText(text).width + font` exceeds `g.pxW - 4` the box `w`
is capped but the string is not shortened, so `fillText(text, x + w/2, …)` (`broadcast_core.js:400`)
would draw wider than its box; at 360 px with 24 runes at a 9 px floor this does not trigger
(fixture measured, 0 outside), so this is **inferred** for narrower frames only.

### F7 — the duel slow-mo banner is shown but the playback rate never changes
*Area: other. Observed.*

`src/snake/replay_runtime.nim:255-262` defines
```nim
proc duelActive*(rt: ReplayRuntime, turn: int): bool = …
proc framesPerTurnAt*(rt: ReplayRuntime, turn: int): int =
  if rt.duelActive(turn): rt.playback.framesPerTurn * 2 else: rt.playback.framesPerTurn
```
`grep -rn "framesPerTurnAt\|duelActive"` over `src/`, `replay-viewer/`, `client/`, `tools/`,
`tests/` returns only those three definition lines — no caller. `framePacket`
(`replay_runtime.nim:130`), `turnAt` (`:253`) and `totalFrames` (`:250`) all use the flat
`rt.playback.framesPerTurn`. Meanwhile `client/replay_broadcast.html:1928-1931` does announce it:
```js
if (!duelAnnounced && s.duel >= 0 && s.t >= s.duel) {
  duelAnnounced = true;
  CTX.banner('DUEL — half speed', 'duel');
}
```
Design §Playback rate (design.md:1132-1134): "from the pre-scan's `duel` turn the block doubles
`renderFramesPerTurn` to 24, i.e. half speed, and shows `DUEL — half speed` in `#bannerlane`". The
banner ships; the rate change does not.

### F8 — step 10's occupancy frees the head-on loser's head cell, which the note's step-10 text says it must not
*Area: correctness. Observed; deliberate and documented in the code.*

Design step 10 (design.md:296-302): "Occupancy is the union of every still-live snake's segments
**after** steps 5–9 … A snake killed in step 4, 8 or 9 **still occupies the board for this test**".

`src/snake/rules.nim:477-495`:
```nim
  for slot in 0 ..< Seats:
    if not state.snakes[slot].alive: continue
    for i, c in state.snakes[slot].body:
      …
      if i == 0 and not (dying[slot] and cause[slot] != dcHeadOn):
        ## … with exactly one exception: the head cell of a head-on LOSER, which
        ## the winner legitimately holds. Without that exception the winner
        ## would die on the loser's corpse and `longer_wins` would mean nothing …
        continue
      blocked[index] = true
      owner[index] = slot
```
Evaluating the predicate: a live snake's head is skipped (correct — two live heads in one cell were
settled in step 9); a `wall`- or `starve`-killed snake's whole body **including its head** blocks
(matches the note); a `headon` loser's head cell is **not** blocked, and the rest of its body is.
Since a head-on loser's post-step-5 head is by definition the same cell as the winner's, the
exception frees exactly the contested cell. Step 9's stated intent (design.md:292-293) requires
this; step 10's literal wording forbids it. The code comment names the tension. Introduced by
commit `5537503` ("corpse occupancy in step 10"). Steps 1–9 and 11–15 otherwise trace exactly to
the note — see "Traced and consistent" below.

### F9 — `headOnOutcome` never returns `tie` under `longer_wins`; an equal-length contest is reported as `lose`
*Area: correctness. Observed.*

`src/snake/rules.nim:231-237`:
```nim
    if theirLength >= myLength:
      strictlyLongest = false
  if not contested: return hrSafe
  if state.rules.headToHead == hhBothDie: return hrTie
  if strictlyLongest: hrWin else: hrLose
```
Under `hhLongerWins`, an equal-length rival sets `strictlyLongest = false` and the proc returns
`hrLose`, not `hrTie`; `hrTie` is reachable only under `both_die`. The observation's
`head_risk ∈ {safe, win, tie, lose}` (design.md:805) and the system prompt's "whether a head-on
there would be a win, a tie or a loss for you" (`src/snake/llm.nim:226-227`) therefore never show
`tie` on the flagship module. Behaviourally the two are the same outcome (both die) and both
baselines penalise them identically (`baselines.nim:87`: `if risk in {hrLose, hrTie}`), so this is a
vocabulary difference, not a rules difference.

Two related, smaller notes on the same proc: contention is tested against all four of a rival's
directions including its own neck (`rules.nim:218-222`), which over-counts contenders slightly;
and the post-move length adjustment adds `+1` for food on the target (`rules.nim:210-212, 227-230`)
but ignores a `shrinkEvery` tick landing on the same turn.

### F10 — `MaxReplyBytes = 4096` is declared and test-asserted but never applied to any read
*Area: other. Observed.*

`src/snake/sim_types.nim:32-34` declares it with the doc comment "Hard cap on the bytes read from
one model reply before the tolerant JSON extraction runs".
`grep -rn "MaxReplyBytes" --include=*.nim .` returns exactly two hits: that declaration and
`tests/test_snake_control.nim:166`:
```nim
  c.check(MaxReplyBytes == 4096, "the reply read is capped at 4096 bytes")
```
`src/snake/llm.nim:198-206` (`textOf`) does `parseJson(response.body)` and concatenates every text
content block with no length limit, and `decide.nim:283` passes the whole string to
`extractJsonObject`. Design §Reply schema (design.md:831): "The whole reply is read with a
**4096-byte** cap"; design test 26: "caps the read at 4096 bytes". The constant exists; the cap
does not. (`max_tokens` is capped separately at `maxOutputTokens = 900`, `sim_types.nim:101`, which
bounds the reply in practice.)

### F11 — no `fallback` event is ever emitted; the kind exists only in the enum and the beat list
*Area: other. Observed.*

`grep -rn "ekFallback"` over `src/`, `tests/`, `tools/`, `replay-viewer/` finds it only in the enum
(`rules.nim:84`), the beat list (`events.nim:17`) and one unreachable feed row
(`labels.nim:51-52`). No `TurnEvent(kind: ekFallback, …)` is ever constructed. The scrubber's
fallback markers come from the chat records instead — `replay_runtime.nim:120-121` collects
`rt.fallbackTurns` from `k == "fallback"` records and `:202-204` turns them straight into `Beat`s.
Consequences: the `COGAME_EVENTS_URI` tier-2 stream (`events.nim:37-47`) never carries a `fallback`
row, and `labels.nim`'s `"MISSED THE CALL — coil move (…)"` string (design §Readouts 8,
design.md:1167) never reaches the feed. Design §Record and event vocabulary B lists `fallback
{slot, cause}` among the sixteen emitted kinds; `tests/test_snake_events.nim:12-21` asserts the
*enum* has sixteen members and `:42-43` asserts a real episode's events are a subset of them, so
neither test catches a kind that is declared and never emitted.

### F12 — the match-feed strings are shorter than the note's examples, and `deathPhrase`/`wallSideOf` have no callers
*Area: other. Observed.*

`src/snake/labels.nim:12-24` defines `deathPhrase` and `wallSideOf`; neither is referenced anywhere
(`grep -rn` over the tree returns only the definitions). `feedRow` (`labels.nim:26-59`) emits:

| Design §Readouts 8 (design.md:1161-1167) | `labels.nim` |
|---|---|
| `COG-delta runs into the north wall` | `labels.nim:40` — `alias & " runs into a wall"` |
| `HEAD-ON — COG-alpha (8) beats COG-gamma (6)` | `labels.nim:45` — `"HEAD-ON — " & cogAlias(e.other) & " wins the cell"` |
| `HEAD-ON — COG-beta and COG-delta both die (7 v 7)` | `labels.nim:47` — `"HEAD-ON — everybody in that cell dies"` |
| `COG-beta declines a free head-on with COG-delta` | `labels.nim:51` — `alias & " declines a free head-on"` |
| `COG-delta MISSED THE CALL — coil move (timeout)` | `labels.nim:53` — present but unreachable (F11) |
| `COG-beta eats — length 6`, `COG-gamma is TRAPPED — 4 free cells, length 6`, `COG-alpha starves`, `HUNGER — everyone loses a segment`, `COG-alpha: "…"` | match |

`tests/label_manifest.txt` and `tests/test_snake_label_contract.nim` pin the shipped (shorter) set,
so the contract is internally consistent — it just carries fewer facts than the note's examples.

### F13 — nine numbered tests exist but assert less than the note describes
*Area: other (checklist 1 is about loosening *during this run*; these are as-written gaps). Observed.*

All 49 numbered items in design §Tests are accounted for by a file, and all 15 test files run in
both debug and `-d:release` under `ci.yml:108-158`. Differences between what the note says and what
the test does:

| # | Note says | Code does |
|---|---|---|
| 15 | "`win[s] == (place[s] == 1)`" | `test_snake_sim.nim:447-450` writes `check (place[slot]==1) == (permille[slot] == max(…) or place[slot]==1)`, which is satisfied for every place-1 seat by construction; `results.win` itself is literally `place[slot] == 1` at `sim.nim:201`, so nothing independent is compared |
| 16 | "…and an all-four-die turn ends `complete`/`last_standing` with the length tie-break applied" | `test_snake_sim.nim:452-479` covers a normal episode, a `settle(rsDeadline, erWallClock)` and a `settle(rsFault, erSimFault)`; there is no all-four-die case, and the two forced endings call `settle` directly rather than driving the loop |
| 18 | "…and no single turn exceeds 3 ms" | `test_snake_sim.nim:502-513` times the whole 50-turn episode (`< 1.0 s` in release) only; no per-turn assertion |
| 29 | "≥ 1 `eat`, ≥ 1 `headon` and ≥ 1 `death`" | `test_snake_engine.nim:66-76` counts head-ons into `headons` and prints it, but only asserts `eats >= 1` and `deaths >= 1` |
| 31 | "a seat that connects then never answers, **and** a seat that never connects at all, both produce a finished episode inside the wall-clock budget … the loud unregistered-seat log line present, and exactly one closed-schema payload" | `test_snake_engine.nim:101-122` runs an all-scripted episode, then sets `played.episode.seats[2].dead = true` by hand and builds the failure payload as a literal inside the test before checking its own literal has two keys. Neither socket path, nor `server.nim:337-342`'s log line, is exercised |
| 32 | "with the guard forced, the episode finishes `complete`, not `deadline`, and the `budget_guard` record names the turn" | `test_snake_engine.nim:124-141` re-derives the guard's inequality by hand, parses a hand-built `budgetGuardRecord(17, 8)`, and calls `settle(rsComplete, erFullTime)` directly. `decide.turn`'s guard at `decide.nim:197-205` is never run |
| 33 | "for … `wall_clock` **and** `sim_fault`, **record an episode** and re-derive it" | `test_snake_replay.nim:30-45` records the same naturally-`complete` royale/seed-42 episode four times and appends a synthetic `stopRecord` for the two abnormal rules. The hash-chain assertion (`rt.mismatchTurn == -1`) is real for all four; the end-reason paths themselves are not recorded |
| 39 | "sha256 of `client/chrome_common.js` equals the starter's, pinned as a literal" | `test_snake_viewer.nim:7-32` pins an FNV-1a-64 digest plus the exact byte length 40 022. (I verified independently: `sha256` of both files is `7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c` — see F16/Traced) |
| 40 | "the file **begins with the starter's bytes** up to the documented splice marker … `broadcast_core.js`'s kept procs are byte-identical to the starter's, **`pushFeed`'s signature included**" | `test_snake_viewer.nim:38-65` checks the banner is present, that 15 inherited ids appear *before* it, that 32 element ids exist, and that the literal `function pushFeed(row) {` is present. No byte comparison against the starter, and no comparison of `broadcast_core.js` procs. This is the id-presence-only shape checklist 14 explicitly calls insufficient — though the provenance itself does hold, see F16 |
| 44 | "asserts each replacement string above is present **exactly once**" | `test_snake_endcard_labels.nim:59-61` asserts `count >= 1` |

### F14 — no replay fixtures are committed, and `tools/wasm_replay_smoke.cjs` is invoked by nothing
*Area: other (design §Tests 49). Observed.*

`ls tests/` shows no `fixtures/` directory. `tools/record_fixture.sh:19-23` carries the three
recipes (`royale-seed42`, `geese-seed7`, `tron-seed13`) and `tests/test_snake_replay.nim:137-140`
asserts the script still names them, but `test_snake_replay.nim:141` guards the staleness sweep
with `if dirExists("tests/fixtures")`, so it is a no-op. `tools/wasm_replay_smoke.cjs` is committed
(the starter's file with `_ctf_*` → `_snake_*` renames — nine hunks, no logic change) but
`grep -rn "wasm_replay_smoke"` over `.github/`, `tools/`, `tests/`, `Dockerfile*` returns nothing:
no workflow, script or test runs it. Design §Sim module (design.md:661) also claims it is kept
"byte-for-byte … only the module filename string changes"; the exported-symbol names changed too.
The wasm module *is* nonetheless executed in CI — by `viewer_smoke.mjs` in headless chromium
against the docker-smoke replay (`ci.yml:305-327`), which is checklist 13's own requirement.

### F15 — three "kept byte-for-byte" tools are absent, and design test 38 has no CI step
*Area: other. Observed.*

Design §Sim module → Kept (design.md:662) lists `tools/ci/check_gameversion.sh`,
`tools/ci/next_coworld_version.py` and `tools/ci/test_next_coworld_version.py` as unchanged
carry-overs. `tools/ci/` contains only `baseline_tuning.json`, `docker_smoke.sh`, `policies.json`,
`renderer_fixture.html`, `viewer_smoke.mjs`. Design §Tests 38 ("a CI step runs the installed
`coworld`'s own `validate_upload_manifest` / `_load_template_manifest`") has no counterpart in
`ci.yml`; the nearest equivalent is `coworld build` inside
`.github/workflows/coworld-release.yml:159-172`, which runs in the release workflow, not in `ci`.

### F16 — `scripts/build_replay_page.py` does not write the file its docstring says it writes
*Area: other. Observed. (Provenance itself checks out — reported here so the audit trail is accurate.)*

The docstring says "Build `client/replay_broadcast.html` from the coworld-ctf starter's page …
The output is committed" (`scripts/build_replay_page.py:2, 13`), but `main()`
(`build_replay_page.py:126-150`) writes `client/_head_markup.html` and eight `client/_chunk_*.js`
files and prints `wrote _head_markup.html and 8 starter chunks`. Neither those files nor
`replay_broadcast.html` are produced by it.

I ran it against the mounted starter anyway. `diff <(head -1060 client/replay_broadcast.html)
client/_head_markup.html` produces **67 diff lines** over 1 060 lines — comment rewording (paintball
nouns → snake nouns), the enumerated `RELABEL` strings, and two CSS rules removed by hand that
`CSS_DROP` does not cover (`@keyframes flagflip`, `.feed-row.flagkill`). That is strong evidence the
committed page really is the starter's page mechanically stripped and relabelled, not a rewrite.
The 1 941-line / 98 240-byte page against the starter's 4 660 lines is accounted for by the deletions
the note enumerates (`#viewpanel`, `#fpv*`, `#povBadge`, the ctf scorebug internals, six beat-marker
kinds, perk/handicap badges) plus the deleted paintball JS.

### F17 — the 720 s envelope: the engine's clock starts after the lobby, whose bound is 90 s, not the note's 30 s; and the display hold runs after the artifact write
*Area: timeout (checklist 5). Observed in code; the arithmetic is inferred, untested.*

- `src/snake/server.nim:293-304` — `waitForLobby` is bounded by `lobbyJoinTimeoutSeconds`
  (manifest value **90** for every league variant, `coworld_manifest_template.json`; 45 for
  certification) and polls `sleep(100)` until `joined >= min(Seats, minPlayers)`.
- `src/snake/server.nim:368` — `let started = getMonoTime()` is taken **after** `waitForLobby`
  returns, so `wallClockBudgetSeconds = 640` (`server.nim:378`) and the budget guard's `elapsed`
  (`decide.nim:199`) both measure the loop only.
- Worst case therefore: lobby ≤ 90 s + loop ≤ ~630 s (the guard fires at `elapsed > 618` and the
  turn in flight can add ≈11 s, after which every remaining turn is scripted and costs
  milliseconds) ≈ **720 s**, exactly the 60 % envelope, versus the note's stated "≈500 s typical /
  ≈600 s worst" which assumes "lobby ≤ 30 s" (design.md:481, 483).
- After settling, `server.nim:458-475` writes results / replay / events / failure payload and then
  `server.nim:479-483` holds `gameOverTurns * 250 ms` and a further
  `ShutdownGraceSeconds = 20` (`server.nim:59`) before `httpServer.close()`. Design §End conditions
  (design.md:401) says `complete` "settles after the `gameOverTurns = 2` display hold, **then**
  writes artifacts"; the code writes first and holds after. Both are bounded; total post-settle
  wall clock is ≈20.5 s.
- No unbounded loop or blocking read anywhere on the episode path — see "Traced and consistent".

### F18 — `#viewpanel` is dropped from the page but its no-op stubs and the minimap transfer remain in the JS
*Area: static-viewer (checklist 14 "…removes the panel — markup, CSS, the `core.zoomAt/setZoom/attachMinimap` wiring, and the ids from the test list"). Observed.*

The page is clean: `grep -n "viewpanel\|minimap\|fpv\|povBadge\|squad-pip" client/replay_broadcast.html`
returns six hits, all inside comments (lines 1272, 1274, 1288, 1471, 1568, 1569), and no `id="…"`
for any removed element survives; `zoombar`, `zoom-in`, `zoom-out`, `zoom-slider`, `zoom-read`,
`hillchip`, `flagicon`, `lives-num`, `lives-label`, `ec-heart` are at zero occurrences.
`client/broadcast_core.js:476-478` still exports no-op stubs
`zoomAt: function () {}, setZoom: function () {}, resetView: function () {}, attachMinimap: function () {}`
and `replay-viewer/static_replay.js:71-81` still carries the minimap `transferControlToOffscreen`
block (guarded on `pendingMinimap` being a canvas, which never exists here). Nothing calls them;
`tests/test_snake_viewer.nim:141-142` asserts only that the *page* never calls `attachMinimap(`.

### F19 — two enumerated endcard re-labels have no shipped string, because the markup that carried them was replaced rather than relabelled
*Area: other. Observed.*

Design §Endcard and chrome label re-mapping (design.md:1092-1093) requires
`<span class="fl-cap">Lives left</span>` → `Turns survived` and `Hill time` → `Final length`.
`grep -n "fl-cap\|Turns survived\|Final length" client/replay_broadcast.html` finds only the CSS
rule `#endcard .fl-cap { … }` at line 669 — no markup uses the class. The ctf endcard team panel was
replaced wholesale by the game block's `ec-table`
(`client/replay_broadcast.html:1747-1762, 1878-1893`), whose header is
`Cog | Place | Turns | Length | Ate | Soft`, matching design.md:1091. The other nine re-labels are
present and pinned by `tests/test_snake_endcard_labels.nim:44-61`, which does not list these two.

### F20 — `drawLengthRibbon` does not exist; the ribbon is the starter's `#momentum` SVG
*Area: other. Observed.*

Design §Chrome provenance (design.md:1053) lists `drawLengthRibbon` among the functions "Added" to
`broadcast_core.js`. `grep -n "drawLengthRibbon" client/broadcast_core.js` → no match. What ships is
what design §Readouts 7 (design.md:1157) describes instead: the starter's
`<svg class="momentum" id="momentum">` (`replay_broadcast.html:1033`) fed by `chrome_common.js`'s
`ingestLeadSeries`/`renderMomentum` (`replay_broadcast.html:1093, 1369`) from the `lead` field the
pre-scan builds at full width on frame 0 (`src/snake/broadcast.nim:76-82, 119`). The two note
sections disagree; the implementation follows §Readouts.

### F21 — `forager`'s `spaceWeight` differs from the note and was not in the swept matrix
*Area: correctness (checklist 7 "tuned with a grid harness, not guessed"). Observed.*

`tools/tune_baselines.nim:31-42` sweeps only `coil`'s `spaceWeight`, `spaceCap` and `foodWeight`;
`ForagerTunables` is held fixed at `ladderTotals(coil, ForagerTunables)` (`tune_baselines.nim:38`).
Of forager's six numbers, five match design.md:538-545 exactly; `spaceWeight` is 40 in
`baselines.nim:50` against 400 in the note, and no sweep row covers it. `coil`'s shipped triple
`(100, 4, 400)` *is* in the matrix and *is* the best row.

### F22 — `tests/test_snake_scoring.nim` does not exist
*Area: other. Observed.*

Design §Scoring (design.md:375) names `tests/test_snake_scoring.nim` as the file asserting
`sum(scorePermille) == 0` over 1000 randomised end states including every tie shape. No such file
is in `tests/`. The assertions are in `tests/test_snake_sim.nim:421-450` (numbered test 15), which
does run 1000 trials across five tie shapes including the places-2-4 slice that a truncating `div`
would break, and asserts `total == 0` and the `[-1000, +1000]` range. The behaviour is covered; the
filename in the note is wrong. (See F13 for the one weak assertion inside it.)

### F23 — the CI smoke replay is written to a `.json` filename although it is binary `COWLDSNK`
*Area: other. Observed in the CI log.*

`tools/ci/docker_smoke.sh:58` fixes `replay_out="${SMOKE_REPLAY_OUT:-${repo_dir}/dist/smoke/replay.json}"`
(the shared template's path) and `:339` copies the container's `replay.json` there;
`SMOKE_REQUIRE_REPLAY_JSON=0` (`ci.yml:196`) correctly disables the JSON-parse check
(`docker_smoke.sh:313-319`). `ci.yml:309-313` then globs `dist/smoke/*.replay` first and falls
through to `dist/smoke/replay.json`. CI log: `loading dist/smoke/replay.json in
dist/static-replay-viewer` and `loaded: true` — the wasm module parsed it as the binary stream it
is, so nothing breaks; the extension just does not describe the bytes.

### F24 — the tier-2 events stream uses the sixteen-kind sim enum, not the note's reduced `SimEventKind`
*Area: other. Observed.*

Design §Record and event vocabulary C (design.md:963-966) specifies `COGAME_EVENTS_URI` carrying a
`SimEventKind` "reduced to `TurnStart, Move, Eat, FoodSpawn, Shrink, HeadOn, Death, Trapped,
Decline, Duel, Say, Directive, Fallback, GameOver`". `src/snake/events.nim:37-47` serialises the
same `EventKind` the sim uses, so the stream carries `gamestart`/`spawn`/`end` (not in the note's
list) and never carries `directive` or `fallback` (F11). The mandatory trailing summary row
(`type`, `turns`, `events`, `gameVersion`) is present (`events.nim:44-46`) and asserted
(`test_snake_events.nim:46-49`).

### F25 — `viewer-smoke.json` reports `feed_lines: 0`
*Area: legibility. Observed; cause not determined — see "Could not determine".*

---

## Traced and consistent

**Checklist 1 — CI green, and the test-file history.**
`gh run list -R Metta-AI/cogame-snake-royale --branch main -w ci.yml` → run **33144094331**,
conclusion **success**, `headSha f985499c563359a169cf6f5bea31ef04ccf28985` (the reviewed sha), all
three jobs green. `git log --oneline -- tests/` over this run's five commits (`512a5ef`, `b03a96f`,
`5537503`, `4e6500d`, `a8fbdfd`) — I read every hunk. No `skip`/`xfail`/`--skip` was added, no test
file was removed, and no test was excluded from `ci.yml`'s sweep (which globs `tests/*.nim`,
`ci.yml:119-123`, with `NIM_TESTS*` repo variables unset in this run's env dump). Two assertion
changes are recorded above as F2 (`margin > 0.0` → `abs(margin) >= 0.05`, with stronger pins added
in the same commit) and F3 (`check sawTrapped` → `check pending.len >= 0`). Everything else in
those hunks is a compile fix (`b03a96f`: `block` is a Nim keyword, `splitLines` has no index form,
missing imports) or a strengthening (`5537503`: `wrapped.len < long.len` → `wrapped.count('x') ==
MaxPromptRunes`; a hand-built free-space pocket replacing an ambiguous one).

**Checklist 2 — replay re-derivation, frame by frame, through the same sim.**
`src/snake/replay_runtime.nim:151-180` (`preScan`) rebuilds the episode from `configOf(replay)`
(`replays.nim:187-213`) and replays each recorded direction byte through the *same*
`rules.resolveTurn`, comparing `state.gameHash` to `recorded.hash` per turn and recording the first
divergence in `mismatchTurn`. The viewer derives its display from that same runtime, not from a
parallel recording: `replay-viewer/snake_replay.nim:52` calls `loadReplay(bytes)` and
`:36-37 renderCurrent()` calls `broadcast.framePacket(runtime)`, which reads `rt.snapshots`
produced by the pre-scan. Tests: `tests/test_snake_determinism.nim:27-47` asserts
`rt.mismatchTurn == -1` on all three modules and compares final bodies, food, health, alive flags
and hash; `tests/test_snake_replay.nim:30-45` repeats it including the stop turn.
Food is not recorded and is re-derived from `foodRng = initRng(seed xor FoodStreamXor)`
(`rules.nim:304`), which the hash chain proves.

**Checklist 3 — static viewer, no pod path.**
`coworld_manifest_template.json` → `game.replay_viewer = {"bundle": "static-replay-viewer"}` under
`game`, absent at the top level (asserted `test_snake_manifest.nim:116-118`).
`tools/build_replay_viewer.sh` exists, mode **100755** (`ls -la`), builds
`Dockerfile.replay-viewer`'s `replay-viewer-builder` target and `docker cp`s
`/workspace/snake/replay-viewer/dist/.` out; it is `coworld build`'s hook and is invoked by path in
`ci.yml:264`. The bundle's only network call is `fetch(message.replayUrl)`
(`static_replay_worker.js:113`) for the `?replay=` URL plus same-origin assets; no websocket, no
other `fetch`. `/client/replay` is registered in `src/snake/server.nim:280` and documented at
`server.nim:139-141` as local-developer-only; it is not declared in the manifest, and
`coworld-release.yml:203-211` fails the release if certification does not report the **static**
bundle.

**Checklist 4 — both name spaces.** `src/snake/roster.nim:19-24` gives `cogAlias(slot)` →
`COG-alpha…delta`; `sim.nim:197-199` puts the real `episode.seats[].name` in `results.names` and the
aliases in `results.aliases`; `replays.nim:98` records real names in the config document and
`server.nim:355` in the join records; `broadcast.nim:56-69` hands both to the scorebug roster and
`replay_broadcast.html:1794-1796` draws `plate-name` (real name) beside `cog-alias`.
`decide.nim:84-163` (`seatViewJson`) emits aliases only.
`tests/test_snake_identity_privacy.nim:23-36` asserts no real name, no other seat's notes and no
`spawnDeal` reaches an observation, and `:47-54` that `showPlayerLabels` is false in all three
variants and the fixture. CI's `viewer-smoke.json` scorebug readout shows both:
`"Cog1 COG-alpha 8 LEN HP …"`.

**Checklist 5 — every wait bounded.** Enumerated from the code:
`waitForLobby` ≤ `lobbyJoinTimeoutSeconds` (`server.nim:293-304`); the episode loop's top-of-loop
wall-clock stop at `wallClockBudgetSeconds` (`server.nim:377-383`, `while true` with three exit
tests); the budget guard at `decide.nim:197-205`; the rate-floor sleep ≤ `turnSpacingMs`
(`decide.nim:238-241`); `curly.makeRequests(batch, max(1, deadlineMs div 1000))`
(`decide.nim:273-274`) with `attempt1Ms 6000` / `retryMs 3000` and `sim_config.nim:106-113`
*rejecting* any sub-second or non-whole-second value; the per-turn `turnBudgetMs` cap
(`decide.nim:251`); at most two attempts (`decide.nim:248`); the throttle fail-fast
(`decide.nim:307-312`); the post-settle hold + `ShutdownGraceSeconds = 20` (`server.nim:479-483`);
on the player side, bounded dialling `240 × 500 ms` and `ReconnectAttempts = 6`
(`snake_royale_player.nim:22-26, 68-125`). Every BFS is bounded by `cap`
(`space.nim:19-49, 51-85`) and every sim loop by `Seats` or `board.cells()`. Global broadcasts are
fire-and-forget (`server.nim:254-265`, "`send` only QUEUES"). No blocking read without a timeout on
the game side.

**Simultaneous decisions as one parallel batch.** `decide.nim:258-274` builds one `RequestBatch`
with one `batch.post` per open seat and issues a single `curly.makeRequests`. No per-seat loop
around the transport anywhere.

**Checklist 6 — `num_agents`.** `4` inside `game_config` for all three variants and for
`certification.game_config`; absent at every variant top level; no literal `tokens` and no `slots`
in any `game_config`; `len(certification.players) == len(certification.game_config.players) == 4`
(verified by parsing the manifest). `config_schema.num_agents` is
`{"type":"integer","minimum":4,"maximum":4,"default":4}`; `tokens` and `players` carry
`minItems/maxItems 4/4`, `slots` `0/4`. `tools/ci/docker_smoke.sh:110-152` implements all four
`SEAT-COUNT FAIL:` invariants plus the independent `SMOKE_SEATS` cross-check, and is mode **100755**
with `ci.yml:169-179` asserting the exec bit and invoking it by path.
`grep -c "SEAT-COUNT FAIL" ` over the full 3 497-line CI log for run 33144094331 → **0**; the
docker-smoke log reads `game=snake-royale seats=4 …` and `smoke OK: seats=4 … reason=complete`.
`tests/test_snake_manifest.nim:13-46` pins all of it.

**Checklist 7 — scripted baseline plays full episodes legally.** `test_snake_engine.nim:78-100`
runs each of the three shipped `game_config`s to its natural end and asserts
`reason == rsComplete` and zero sum; `:31-38` asserts `reason == "complete"` and
`endRule ∈ {last_standing, full_time}` for the certification fixture.
`test_snake_control.nim:60-99` checks 500 random states × 4 seats × both baselines for: `dir` in the
enum, no `alt`, empty `say`/`notes`, serialised directive ≤ 1024 bytes, never the neck unless every
direction is fatal, and — the strong one — that the baseline's `NegInfinity` set is exactly the
resolver's illegal set, using the resolver's own `willOccupy`. `:102-111` asserts the fallback path
*is* the `coil` proc (`control.nim:14-20`). The harness exists and ran (F2 records the margin).

**Checklist 8 — LLM reply handling.** Tolerant parse:
`directives.nim:73-112` (`extractJsonObject`) walks braces with string/escape awareness, falls back
to first-brace..last-brace, tolerates fences and prose (`test_snake_control.nim:169-172` proves a
```json fence with prose on both sides). Retry: `decide.nim:248` `while open.len > 0 and attempt < 2`
with `retryMs` on the second pass and an explicit "reply with ONLY the JSON object" nudge appended
(`decide.nim:261-264`) — subject to F4. Fallback recorded: `decide.nim:315-329` writes a
`fallbackRecord` with `cause ∈ {no_credentials, budget_guard, throttled, parse_error, timeout,
transport_error}` and increments `episode.seats[slot].fallbackTurns`, surfaced as
`results.fallbackTurns` (`sim.nim:216, 244`) and grepped from the log via the exact phrase
`falling back` (`decide.nim:226, 328`). The attempt-1 failure log says **`will retry`**
(`decide.nim:302`) — the fork's deliberate change from the starter's "falling back if it fails
again" — so phase 60's grep cannot double-count. The `no_credentials` case is recorded per turn
rather than silently zero (`decide.nim:216-227`), and `llm.nim:136-137` prints the exact phrase
"LLM provider is unavailable".

**Checklist 9 — rune-safe truncation.** One truncation proc, `directives.nim:42-49`, using
`runeLen`/`runeSubStr`; `sanitizeSay` (`:51-66`) cuts to `MaxSayRunes` **first**, then applies the
printable-ASCII shout filter including the `{`/`}` exclusion; `sanitizeNote` (`:68-71`) collapses
newlines then cuts to `MaxNoteRunes`. `boundedDirectiveRecord` (`:192-210`) shortens fields and
re-serialises rather than cutting the serialised JSON. Applied at: `records.nim:19` (fallback
detail, 200), `records.nim:29` (policy label, 64), `server.nim:209, 212` (prompt 4000, policy 64),
`llm.nim:181, 189, 197, 206, 250` (provider bodies and the operator prompt),
`sim.nim:248` (`stopDetail` via `cutRunes`, `sim.nim:59-63`, 200),
`snake_royale_player.nim:29-31, 40` (prompt, 4000). Caps in `sim_types.nim:24-35`: say 24, notes
160, prompt 4000, fallback detail 200, policy label 64, directive 4000, stopDetail 200.
Test: `test_snake_control.nim:147-165` places a 4-byte emoji exactly on each cap and asserts
`runeLen == cap` **and** `validateUtf8() == -1`; `test_snake_replay.nim:82-118` fills every capped
field with 4-byte emoji, runs `tools/replay_summary.py` over the replay and asserts strict-UTF-8
JSON output with no lone surrogate. (F10 records the one cap that is declared but not applied.)

**Checklist 10 — manifest validates.** `game.docs` is
`{"readme": {"type":"text","value": 4132 chars}, "pages": [rules.md/Rules, modules.md/Rule modules,
protocol.md/Wire protocol]}`, each page `{id, title, content:{type:"text", value}}` with
4 568 / 1 514 / 3 965 chars. `game.protocols` carries **both** `player` and `global`, each as
`{"type":"uri","value":"https://github.com/Metta-AI/cogame-snake-royale/blob/main/docs/PROTOCOL.md"}` —
objects, not bare strings. `$schema` present, five top-level `tags`,
`episode_timeout_minutes: 20` top-level, `game.tags` absent, no top-level `version`, no
`game.display_name`, `game.owner` present, `game.description` present,
`game.runnable = {type:"game", image:"{{SNAKE_ROYALE_IMAGE}}", run:["/bin/snake-royale"],
env:{ANTHROPIC_API_KEY_URI:"secret://coworld/snake-royale/anthropic_api_key"}}`.
`results_schema` is `additionalProperties: false` with exactly the 29 keys `snakeResultsJson`
emits — `test_snake_engine.nim:42-54` asserts set equality against the live results document, which
is the strongest form of that check. `reason` enum `[complete, deadline, fault]`, `endRule` enum
`[last_standing, full_time, wall_clock, sim_fault, host_error]`. Top-level `player[]` has both
declared players seated in `certification.players`, `limits.cpu = "1"`.
`compose.yaml` declares one service `snake-royale` → `{{SNAKE_ROYALE_IMAGE}}`.

**Checklist 11 — legible at 360 px.** `client/replay_broadcast.html:1583-1598`:
```css
.plate-name { … white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
              flex: 1 1 auto; min-width: 3.2em; }
```
and `:1720-1722` `@media (max-width: 640px) { .plate .cog-alias, .plate .len-label,
.plate .hp-label { display: none; } }`, mirrored by `#stage.tiny` at `:1723-1736`.
`relayout()` toggles `.tiny` at `boardW <= 620` (`:1532`) and clamps
`--hudscale = max(0.5, min(1.6, boardW/760))` (`:1529-1530`), both the starter's values.
`#stage.tiny #momentum { height: 50% }` and `#stage.tiny #killfeed .feed-row:nth-child(n+4)
{ display: none }` implement the note's rules 4. Asserted `test_snake_viewer.nim:104-146`.

**Checklist 12 — release order and scaffold.** `coworld-release.yml` step order is
`Build the Coworld manifest` (159) → `Certify locally` (173) → `Upload the policies` (216) →
`Upload the Coworld` (314) → `Put the Coworld secret` (410), with the comment at :271-273 recording
why policies precede the coworld. Certify runs against `dist/coworld_manifest.json` built in the
same run by `coworld build` (which runs `tools/build_replay_viewer.sh`), with
`--timeout-seconds 300` (`:184`). All three workflows present. `tools/ci/docker_smoke.sh` and
`tools/build_replay_viewer.sh` are both mode 100755. `tools/ci/policies.json` defines four
policies, `run: "/bin/snake-royale-player"` on all four, two `PLAYER_PROMPT` champions
(`snake-royale-strangler`, `snake-royale-glutton`) and two `PLAYER_SCRIPTED` fillers (`coil`,
`forager`), with champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"` and no
`USE_BEDROCK` anywhere (asserted `test_snake_manifest.nim:150-171`). Both champion prompt texts and
`llm.nim`'s `SystemPrompt` are **byte-identical** to the design note's fenced blocks (verified by
extracting both and comparing). The placeholder gate exits 0: `grep -n '<slug>\|<IMAGE>\|<SEATS>'`
over the five named files matches nothing; the only surviving angle-bracket names are the four
documented residues (`<cow_id>`/`<sha>` in `ci.yml:217`, `<run_id>` in
`coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` in `coworld-submit.yml:31`).

**Checklist 13 — the viewer executes.**
`ci.yml:210` `wasm-viewer: needs: docker-smoke`; step "Load the bundle in a real browser"
(`ci.yml:305-327`) ran, is not `continue-on-error`, and invoked
`node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay dist/smoke/replay.json
--timeout 90 --soak 10 --strict-text-bounds`. Result (`viewer-smoke.json`):
`"loaded": true, "ms": 341`, `"signals": {"data_replay_loaded": "true", "data_replay_error": null}`,
`"soak": {"seconds": 10, "moved": true, "before": "0 / 40", "middle": "16 / 40",
"after": "20 / 40"}`, `"failure": null`, `"page_errors": []`.
Both markers come from the shell's own code paths: `static_replay.js:161`
`document.documentElement.setAttribute('data-replay-loaded','true')` in the `'loaded'` branch, and
`static_replay.js:8-20` `showFailure()` setting `data-replay-error`. Both files are the starter's
with only the `_ctf_*` → `_snake_*` and `CtfStaticReplay` → `SnakeStaticReplay` renames (`diff`
against the starter: 2 hunks in `static_replay.js`, 14 rename-only hunks in the worker).
**Bootstrap/link-flag agreement:** `static_replay_worker.js:8, 188, 192` does
`var Module = {}` … `Module.onRuntimeInitialized = function () {…}` … `self.Module = Module`, and
`replay-viewer/config.nims:44-54` has **no** `-s MODULARIZE=1` and **no** `-s EXPORT_NAME` (diff vs
the starter's `config.nims`: five rename-only lines). Non-modularised build + `onRuntimeInitialized`
shell — the same starter, consistent, and the smoke's `loaded: true` proves it.
**Playback opens at the game start:** this game records **no lobby frames at all** —
`waitForLobby` (`server.nim:317`) runs entirely before `replay.turns` starts accumulating
(`server.nim:425`), and `preScan` seeds `snapshots[0]` with the spawned board
(`replay_runtime.nim:144`), so frame 0 *is* the game start. `chromeJson` publishes `"st": 0`
(`broadcast.nim:94`), which matches. CI's soak confirms: `before: {"tick": "0 / 40"}` →
`after: {"tick": "20 / 40"}` in 10 s, with no dwell. The one frame labelled `ph: "lobby"`
(`broadcast.nim:88-91`) is the spawn board, not a frozen 63–270-frame pre-game.

**Checklist 14 — the chrome is the starter's.**
`client/chrome_common.js` is **byte-identical**: `diff` is empty, both files are 40 022 bytes and
`sha256 = 7ace7287e0d19bf0fddb2362c55e4d76dfb44adcd4fbc8d1743b0557ced72f7c`.
`client/replay_broadcast.html` carries the banner comment
`SNAKE-ROYALE additions to the inherited coworld-ctf chrome` at line 1562, with all CSS/markup
above it and the game block (a `<style>` at 1582 and a `<script>` at 1738) below. Provenance
independently reproduced — see F16 (67 diff lines over 1 060 against the mechanically-derived
starter head). All eight starter CSS sections survive: stage/board (`:88-165`), scorebug (`:169`),
banner lane, kill feed, transport band (`:386`), scrubber + momentum + beat markers + lulls +
spoilers (`:399-445`), endcard (`:564-705`), locker-room curtain (`:780`).
The block installs through the starter's own hook: `PB_CTX` is built at `:1548-1553` with
`$, C, esc, fmt, send, pushFeed, banner, clearFeed, seekToFraction, getState` and
`window.SnakeChrome.install(PB_CTX)` at `:1554`, `SnakeChrome.frame(s, PB_CTX, jumped)` at `:1372`.
- (a) `relayout()` sets `--hudscale`, `--topband` and `--band` on `document.documentElement`
  (`:1509, 1530, 1535-1536`) — on `:root`, not on `#stage`.
- (b) Nothing in the game block is fixed-positioned in the band: the only `position: absolute` in
  the block's CSS is `#stage.tiny .plate .hpbar` (`:1726-1732`), anchored to `.cog-chip` inside the
  top-band scorebug. `test_snake_viewer.nim:144-146` asserts `"#transport" notin blockText`.
- (c) `#endcard { … top: var(--topband, 0px); bottom: var(--band, 0px); }` (`:565-586`) with
  `#endcard.on { display: flex }` (`:587`), and the block shows/hides with exactly that class
  (`:1877, 1905`). Dismissal on seek: **F1**.
- (d) Beats are `<button class="beat-marker <kind>">` with `title` and `aria-label` and a click
  handler (`:1770-1789`), built by `snakeBeat` — never `markBeat`, asserted
  `test_snake_viewer.nim:74-83`. CSS exists for exactly the seven emitted kinds (`:1697-1703`),
  asserted set-equal at `test_snake_viewer.nim:86-101`. The click target is broken — **F1**.
- `#viewpanel` dropped entirely from markup and CSS (**F18** notes the residual JS stubs).

**Resolution rules, steps 1–15** (`src/snake/rules.nim:334-574`), traced against design.md:266-318:
1 `inc state.turn` + `turn` event (`:341-343`). 2 neck repair — alt only if the alt is not itself
the neck, else `lastDir`, `reverseRepaired` incremented either way (`:346-363`). 3 targets, wrapped
by `board.step` (`:376-379`), `lastDir = chosen`. 4 wall deaths for `offBoard` (`:380-382`).
5 head push (`:392`). 6 eat: remove food, `ate = true`, `health = healthStart`, `foodEaten++`, emit
`eat` (`:393-406`). 7 tail pop unless `leaveTrail` or `ate` (`:407-412`). 8 hunger drain and kill at
`<= 0`; `shrinkEvery` pop with death at length 0 (`:414-434`). 9 head-to-head grouped by target,
strictly-greatest post-step-8 length wins under `longer_wins` with `ties == 1`, otherwise everyone
dies with `killedBy = -1` (`:436-469`); the group loop skips already-dying members so a group is
never processed twice. 10 body collisions against occupancy frozen after 5–9 (`:471-517`, with the
one deviation in **F8**); `killedBy` is the owning slot including self. 11 remove the dead, record
`deathTurn`/`deathCause`/`killedBy`/`finalLength`/`survivedTurns = turn - 1`, emit `death` in
ascending slot (`:519-535`). 12 food respawn from `foodRng` over the free cells, `foodspawn`
(`:537-538` → `:252-276`). 13 free space, `trapped` on the false→true transition, `trappedTurns`
(`:540-562`) plus `auditDeclinedKills` (`:576-614`, using the resolver's own `headOnOutcome`,
`willOccupy`, `freeSpaceAfter`). 14 `gameHash = foldState()` over turn, per-seat alive/health/body,
food, and the food-RNG state (`:278-296, 565`). 15 `duel` on the turn `aliveCount` first reaches 2
(`:570-573`); end evaluation is the caller's (`server.nim:384-389`, `engine.nim:36-59`), which
matches the note's own `aliveCount <= 1 → last_standing`, `turn == maxTurns → full_time`.
Predicates have exactly one implementation each: `willOccupy` (`rules.nim:198-201`) and
`headOnOutcome` (`:203-237`), called by the resolver, `seatViewJson` (`decide.nim:113, 125`),
`legalMask` (`decide.nim:173`), both baselines (`baselines.nim:80, 85`) and the audit
(`rules.nim:593, 606`). `tests/test_snake_sim.nim:1-513` numbers blocks 1–18 to the note's list.

**Rule modules.** `rules.nim:110-132` — `royale` 17×9 walls, food 3, health 30, shrink 0, no trail,
`longer_wins`, start 3, 50 turns; `geese` 11×7 torus, food 2, health 0, shrink 20, `both_die`,
start 3; `tron` 21×9 walls, food 0, health 0, no shrink, `leaveTrail`, `both_die`, start 1 —
identical to the note's table (design.md:203-213) and to every shipped `game_config`.
`test_snake_manifest.nim:25-35` asserts each variant really constructs the module it names;
`test_snake_engine.nim:78-100` plays each one.

**Decision path D1–D7** (`src/snake/decide.nim:184-329`): D1 dead seats are never queried
(`:209-212`); D2 one parallel batch at `attempt1Ms`, scripted seats computed locally (`:228-231,
258-274`); D3 one retry at `retryMs` with a 429 fail-fast (`:248, 256-257, 307-312`) — see F4;
D4 `fallbackOrder` (= `coil`, `control.nim:14-17`) with a `fallback` record naming the cause
(`:315-329`); D5 orders installed in ascending slot by the caller (`server.nim:399-415`), repairs
counted into `ordersRejected` (`:288`); D6 `say` sanitised at 24 runes and published to every other
live seat's `said[]` (`decide.nim:136-142`, `server.nim:408-413`, `sayTurns` default 2); D7 the
rate floor on batch **starts** (`:238-244`).

**Scoring.** `sim.nim:108-162` — the three-key descending order `(survivedTurns, finalLength,
foodEaten)`, ties sharing a place, and the slice split with `floorDiv`/`floorMod` and the first
`rem` members in ascending slot order taking the extra permille. `scores = permille / 1000.0`,
`win = place == 1`, no `winner` key. `PlacementPermille = [1000, 333, -333, -1000]`
(`sim_types.nim:43`).

**Replay bytes, self-sufficient.** `replays.nim:134-152` — magic `COWLDSNK`
(`sim_types.nim:48`), format version, game name, game version, config JSON, joins (slot + real name
+ token), one direction byte per seat per turn (`255 = already dead`, `board.nim:25`) with a u64
hash, then the chat records. `replayConfigJson` (`:84-132`) carries `protocol`, `seed`, `module`,
the whole board document with `cellPx`, all eight rule switches, `num_agents`, `spawnDeal`,
`spawnAnchors`, real `players[].name`, `aliases`, `colours`, `policyKinds`, the four cadence
constants, `renderFramesPerTurn`, `sayTurns`, `fastMode`, `showPlayerLabels`. Chat records:
`register`/`directive`/`fallback`/`budget_guard`/`stop`/`result` (`records.nim`,
`directives.nim:168-190`), with `resultRecord` embedding the whole results document
(`records.nim:42-47`) — asserted present in the bytes at `test_snake_replay.nim:68-74`.
`tools/replay_summary.py` decodes it with stdlib only and emits
`protocol: "snake-royale/v1"`, `dirs[].source`, `says`, `fallbacks`, `results`.

**Provenance of the four viewer files.** All four are `coworld-ctf`'s:
`config.nims` (5 rename-only diff lines), `static_replay.js` (2), `static_replay_worker.js` (14),
`snake_replay.nim` (structure preserved — `stampStage`, `bytesFromPointer`, the try/except
publishing `lastError`, `emscripten_exit_with_live_runtime()`; the ctf-specific map-capacity check
is dropped and the pre-scan comment added). `index.html` is built from
`client/replay_broadcast.html` by the same three marker `sed`s the starter uses
(`Dockerfile.replay-viewer:36-40`), with the same `! grep -q` assertions that
`broadcast_core.js` and `snake_replay.js` are *not* script tags in the page.
`tools/ci/viewer_smoke.mjs` is **byte-identical** to
`coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff`, empty).
`tools/ci/docker_smoke.sh` is the template with only the three substitutions (3 hunks, all in
comments or the `SMOKE_IMAGE` default).

**Art.** `data/snake_<amber|teal|violet|lime>_{head_u,head_r,head_d,head_l,body,corner,tail}.png`
(28 files), `data/food_apple.png`, `data/wreck.png` — all 128×128 PNGs of 19–27 KB, with the
1.3 MB source sheets under `scripts/art/source/` and `scripts/art/split_snake_sheet.py`.
`tests/test_snake_art.nim:11-46` asserts each file exists, is > 1 000 bytes, is preloaded by the
renderer and is shipped by `Dockerfile.replay-viewer`.

**Determinism.** `board.nim`, `rules.nim` and `space.nim` contain no float literal, no `/` and no
`sqrt` (asserted line-by-line at `test_snake_sim.nim:482-500`). Two RNG streams:
`setupRng = initRng(seed)` drawing `spawnDeal` before any seat connects (`sim.nim:64-70`,
`server.nim:309` inside `newEpisode`, called before `waitForLobby` at `:317`) and
`foodRng = initRng(seed xor FoodStreamXor)` (`rules.nim:304`).
`tests/test_snake_seeding.nim:20-62` proves purity, permutation, stream separation, and that seat
behaviour cannot shift either.

---

## Could not determine

- **Whether the 720 s envelope is actually breached.** F17's arithmetic assumes the platform starts
  charging at pod start and that all four seats register near the 90 s lobby bound. In practice the
  lobby returns as soon as `minPlayers` register. Settling this needs a hosted episode's
  wall-clock trace (phase 60), or a `docker_smoke.sh` run with `lobbyJoinTimeoutSeconds` at 90 and
  a deliberately slow player.
- **`viewer-smoke.json`'s `feed_lines: 0` (F25).** The match feed pushes rows through
  `CTX.pushFeed` (`replay_broadcast.html:1868-1870`) from `chrome.feed`
  (`broadcast.nim:83-87`), and the 40-turn cert replay does contain `eat`/`death` events
  (`test_snake_engine.nim:73-76` prints the counts). Whether `feed_lines: 0` means "the readout was
  taken at turn 0 before any event" (plausible — `viewer_smoke.mjs` takes the primary readout
  immediately after `loaded`) or "no row is ever drawn" cannot be told from the artifact. What would
  settle it: a `viewer_smoke.mjs --soak` readout of `#killfeed` children taken mid-playback, or the
  `viewer-smoke.png` screenshot inspected at the same moment.
- **Whether F1's endcard consequence is observed.** I traced it from `renderEndcard`
  (`replay_broadcast.html:1875-1905`) and `broadcast.nim:107` but the CI harness does not report the
  endcard's class. What would settle it: a `viewer_smoke.mjs` readout of
  `document.querySelector('#endcard').className` after a 50 % scrub click.
- **Whether `abs(margin)` in test 27 hides a future regression.** The four exact-integer ladder pins
  added in the same commit (`test_snake_control.nim:202-215`) would fire on any change to the
  rules, the scoring or either baseline, which is arguably a stronger guard than the directional
  check it replaced. Whether the design note's `[+0.30, +1.20]` claim was ever achievable is
  answered by the CI sweep (no candidate is positive), but only over the 18 rows the harness
  explores; `headRiskPenalty`, `killBonus`, `hungerThreshold` and every forager knob are outside it.
- **`.plate-name` behaviour at exactly 360 px.** The CSS rule is present and the smoke's scorebug
  readout shows full names, but the smoke ran at Playwright's default viewport, not at 360 px. The
  renderer fixture renders the *board* at 360 px but drives `roster: []`, so the plates are not
  exercised there. What would settle it: a `viewer_smoke.mjs` run with `--width 360` reading
  `#scorebug`.
