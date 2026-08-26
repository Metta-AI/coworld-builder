# r1 fixes — particle-worlds

Repo: `Metta-AI/cogame-particle-worlds`, branch `main`
Reviewed sha: `99dcaab7f21dad18f24e6f4fa160135bd01c7102`
Head after fixes: `b6b4401ad9db9973387ab011150a73f65ab6e69c`
CI: run **32961166140** (`ci.yml`, push, head `b6b4401`) — conclusion **success**
(`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓;
https://github.com/Metta-AI/cogame-particle-worlds/actions/runs/32961166140).
`grep -c "SEAT-COUNT FAIL"` over the docker-smoke log returns **0**, the job printed
`smoke OK: seats=4 results=882B replay=31136B reason=complete`, and the native↔wasm
gate printed `ok: loaded replay.json, advanced 300 frames`.
The previous run **32960167875** (head `2b3d6c2`) was red on one new engine test —
fixed forward in `b6b4401`, see F3 below.

Review: `runs/2026-08-26-particle-worlds/reviews/r1-review.md`
Design note: `runs/2026-08-26-particle-worlds/design.md` (amended, see F2)

One commit per finding, in review order. No test was disabled, skipped, loosened
or deleted; six test files gained assertions.

| finding | disposition | commit | checklist item | files |
|---|---|---|---|---|
| F1 | fixed | `46cf69d` | 15 (legibility) | `tools/ci/renderer_fixture.html`, `client/replay_broadcast.html:4363-4386,4548`, `.github/workflows/ci.yml:339-388`, `tests/test_viewer.nim` |
| F2 | fixed (note amended) | `eee8254` | 14 (static-viewer) | `docs/plans/2026-08-26-particle-worlds-design.md:1191`, + amendment in the run's `design.md` |
| F3 | fixed | `2090877`, `b6b4401` | 8 | `src/mpe/decide.nim:361-447`, `tests/test_engine.nim` |
| F4 | fixed | `66d1099` | 8 | `src/mpe/decide.nim:443-568`, `docs/PROTOCOL.md:194`, `coworld_manifest_template.json`, `tests/test_engine.nim` |
| F5 | REFUTED (deliberate, measured, documented in code) | — | — | `src/mpe/llm.nim:71-87` |
| F6 | REFUTED (deliberate rewording; no information lost) | — | — | `src/mpe/llm.nim:222` |
| F7 | fixed | `295084b` | — | `src/mpe/llm.nim:254-258` |
| F8 | fixed | `37a6805` | — | `src/mpe/baselines.nim:189-200` |
| F9 | documented; episode total is NEEDS-DESIGN | `6eccd8b` | — | `docs/PROTOCOL.md:229`, `src/mpe/roster.nim:714` |
| F10 | fixed | `60e3643` | — | `src/mpe/decide.nim:163-174`, `tests/test_observation.nim` |
| F11 | NEEDS-DESIGN | — | — | `src/mpe/{paint,map_pool,mapgen_styles}.nim` |
| F12 | fixed | `646e358` | 12 | `.github/workflows/coworld-release.yml:167-178` |
| F13 | REFUTED (item 10 satisfied; one document covers both wires) | — | 10 | `coworld_manifest_template.json` |
| F14 | fixed | `e92b6b6` | 5 (hang) | `src/mpe/field.nim:118-196`, `src/mpe/sim_config.nim:793-809`, `tests/test_field.nim` |
| F15 | REFUTED (starter-inherited dev route; no platform routing) | — | 3 | `src/mpe/server.nim:824-853` |
| F16 | fixed | `2b3d6c2` | — | `tests/test_replay.nim` |
| F17 | no action (observation; nothing loosened) | — | 1 | `tests/test_motion.nim:124-149` |
| F18 | REFUTED (the starter's `.tiny` breakpoint, unmodified) | — | 11 | `client/replay_broadcast.html:4093` |

---

## F1 — the fixture now loads the real renderer (`46cf69d`)

**What it was.** `tools/ci/renderer_fixture.html` had exactly one `<script>` and no
`src`: a ~190-line inline `drawBoard()` that re-implemented the marks, the bubbles,
the plates, the radio strip and the note wrap with its own `measureText` layout. Its
`canvas_text: 49` measured itself. The two `canvas_text` numbers in CI were
therefore `total: 0` (the real viewer, which renders in an OffscreenCanvas Worker)
and `total: 49` from a page that executed no shipped code.

**What it is now.** The fixture `fetch`es `./index.html` — the *shipped bundle's own
page*, i.e. `client/replay_broadcast.html` with `wire_constants.js` and
`chrome_common.js` spliced in by `Dockerfile.replay-viewer` — and runs it in an
iframe. One head shim shadows `window.MpeStaticReplay.createCore`, captures the
page's own `coreConfig` and returns a stub transport; the worst-case frame then goes
in through `config.onText`, byte-for-byte the entry point the Worker uses. So every
line of layout is the shipped chrome's (`onFrame` → `renderScorebug` →
`MpeChrome.frame` → `renderRail`/`renderRadio`/`renderCrypto`/`mpeDirectives`) under
the shipped CSS, and only the frame is synthetic — which is the exact inversion CI
needs, because CI can make a real replay but never a talkative one.

The worst case: a **full-cap 160-rune note on all four seats in one frame** (`MAX_FEED`
is 4, so four notes is the feed's tallest possible state), a non-silent symbol on all
four particles, the **crypto panel** populated (the tallest game block: key row plus
three belief rows), the mark rail, every feed-bearing event kind, at **360 / 620 /
1280 px** board widths, each played until the feed's 250 ms slide-in, the banner pop
and the radio flash have settled.

Measured twice. (a) In the DOM, against the real geometry: every visible text node's
client rect must lie inside the frame and no note may be clipped by its own box
(`scrollWidth > clientWidth`); a violation sets `data-replay-error`, which
`viewer_smoke.mjs` fails on immediately. (b) On canvas: every text run is transcribed
to a per-width canvas at the position and in the font the browser used, one
`fillText` per rendered line (split by the range rects the layout produced, with
`text-transform`, `letterSpacing` and `wordSpacing` applied), so the shared harness's
`CanvasRenderingContext2D` hook can gate the real geometry. The transcription exists
because this viewer draws its board in a Worker and its text in the DOM — without it
the harness reports `total: 0`, which item 15 rightly calls evidence of nothing.

**It found the defect it exists to find.** First local run, before any chrome change:

```
VIEWER SMOKE FAILED: data-replay-error: 12 text run(s) fell outside the 360px frame
  left [-138,146,-109,151] in 360x192, 1 draws: "YELLOW-alpha"
  left [-100,118,291,123] in 360x192, 4 draws: "HOLD AT TEAL SOUTH FLANK UNTIL THE GREENS COMMIT AND THEN BR"
```

`.feed-row` is `white-space: nowrap; max-width: none` (a kill row is two 10-char
names), so a 160-rune note is ~390 px of unbreakable text anchored to the feed's
right edge: at a 360 px board it grew *leftward off the frame* and the model's own
words were drawn at a negative x — the cogchemists defect, in the one piece of chrome
that exists to show what a model said. Fix, in the appended game block: note rows
wrap inside the feed's reserved width (`.feed-row.mpe-note-row`, 228 u, 190 u under
`.tiny`), i.e. widen the band, never shorten the text. `mpeDirectives` tags its rows
with that class.

**Evidence (CI run 32961166140, `wasm-viewer`, step "Worst-case renderer fixture at
360 / 620 / 1280 px"):**

```
{"loaded":true,"ms":2540,...}
canvas text: 302 drawn, 0 never inside the canvas (0 draws crossed an edge), 1 ellipsized (--strict-text-bounds)
fixture canvas_text: total=302 never_inside=0 outside=0
```

(The single `ellipsized` is the starter's locker-room caption, whose text literally
ends in `…`; `ellipsized` is reported, never gated.) The step now also **asserts**
that line: `total <= 0` fails with "the renderer fixture drew NO canvas text", and
`never_inside != 0` fails, so a zero total can never again be mistaken for evidence.
`tests/test_viewer.nim` pins the fixture's shape (it loads `./index.html`, drives the
page's own `onText`, contains no `drawBoard`, carries the 160-rune cap and the three
widths) and pins the note-wrap rule.

## F2 — the chrome_common.js patch is now recorded in the design note (`eee8254`)

Reverting the identifier was not available: `tools/gen_wire_constants.nim` emits
`window.MPE_WIRE`, the design note's own `ctf_`/`CTF_` rename-sweep rule (line 833)
forbids the starter's name, and `tests/test_viewer.nim:180-191,199-218` pins both the
sha256 and the absence of `CTF_WIRE` — undoing it would mean weakening a test, which
this round's brief forbids. So the note now records the patch in the same words it
already used for `broadcast_core.js`: byte-for-byte apart from ONE named, minimal
patch, `client/chrome_common.js:72`, `window.CTF_WIRE` → `window.MPE_WIRE`. The repo
copy (`docs/plans/2026-08-26-particle-worlds-design.md:1191`) carries it inline; the
run copy (`runs/2026-08-26-particle-worlds/design.md`) carries the same text as an
appended `## Amendment — r1` section, so the run artifact is added to, not rewritten.

## F3 — the per-turn budget starts after the rate floor (`2090877`, `b6b4401`)

`turnStart` was captured at the top of `turn()`, so the rate floor's sleep — up to
`turnSpacingMs`, **9000 ms on every shipped variant** — was inside the
`turnBudgetMs` (10 000 ms) monotonic deadline. Steady state left ~3.5 s of budget, so
a turn whose attempt 1 *timed out* (6 s deadline) re-entered the loop past the
deadline, wrote a budget-exhausted `fallback` and broke: **the single retry item 8
requires could not be issued at the shipped settings**, and only a fast failure (a
parse error at ~1 s) left room for it.

The floor is a wait, not work, and `turnBudgetMs` is the cap `sim_config` validates
`attempt1Ms + retryMs` against, so the clock now starts when the turn's first batch
does (`decide.nim:441`, `turnStart = engine.lastBatchStart`). Batch **starts** are
still held `turnSpacingMs` apart, so the rate the sidecar sees is unchanged, and a
turn still costs at most `max(turnSpacingMs, turnBudgetMs)`: 40 turns ≈ 400 s, inside
the 690 s engine stop and well inside the 720 s (60 %) budget.

`tests/test_engine.nim` gains "the rate floor never eats the single retry" — the
first engine test with a **nonzero** `turnSpacingMs` reaching the budget (the suite
previously ran 0 or 600 ms only): a 1200 ms floor, two 1 s deadlines inside a 2 s
cap, against a provider that never answers in time. It asserts the floor was paid,
that the turn cost no more than floor + budget, and that the seat-turn's record reads
`attempt: 2, cause: "timeout"` with no "per-turn budget exhausted" detail — which is
exactly "attempt 1 timed out and the retry went out anyway", and exactly what the bug
made impossible.

**CI honesty note.** The first version of that test counted the fake provider's
handler windows (`== 8`) and CI run 32960167875 failed it with `6`. The engine was
right — the same job logged "attempt 1 failed" ×4, "attempt 2 failed" ×4, "falling
back to drifter (timeout)" ×4 — but curl abandons a timed-out call and mummy then
drops the queued request for a disconnected client ("Dropped response to disconnected
client"), so two handlers never ran. Counting handler windows cannot prove a batch was
*issued* when every call in it times out; `b6b4401` moves the assertion to the record
stream, where it is exact. No assertion was weakened: the new form distinguishes
fixed from broken, which the window count did not.

## F4 — one authoritative fallback record per seat-turn (`66d1099`)

A failing turn wrote two or three records for one seat: one per failed attempt, plus
the tail drifter record hard-coded to `attempt: 2` — and on the budget-exhausted path
two records both stamped `attempt: 2` with *different* causes (`timeout` then
`parse_error`). `sim.fallbackTurns[seat]` increments once per seat-turn, so
`replay_summary.py`'s `fallbacks` (a record count) could not be reconciled with
`results.fallbackTurns`, and the phase-60 recipe reads both.

Each failed attempt now records its cause, detail and attempt number in per-seat
state; the tail block writes the one record for the seat-turn, stamped with the
attempts actually spent (1 when the retry never went out — throttle, disabled client,
exhausted budget — 2 when it did) and with the cause that ended the turn, so a
timeout is no longer relabelled `parse_error` on the way out. `results.fallbackTurns`
is untouched, and a count of `fallback` records now equals its sum. Per-attempt
diagnostics are unchanged in the game log, which is where phase 60 greps them
(`"attempt N failed"`, `"falling back"`). `docs/PROTOCOL.md:194` states the invariant
and the manifest is regenerated from it (`build_manifest.py --check` is green in CI).
`tests/test_engine.nim` asserts exactly four records for four seats, one per seat,
`attempt: 2` on the retry path and `attempt: 1` on the throttle fail-fast path.

## F5 — REFUTED (no change)

`bedrockModelIds()` shipping one candidate is deliberate, measured and documented **in
the code**: `llm.nim:74-83` records that `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
was the paintbot 0.1.2 ladder fallback and that the hosted round-2 log carried 133
calls to it, every one returning "Timeout was reached" and none returning text. With
no second candidate a 429 fails fast, which is the behaviour the design *and*
`tests/test_engine.nim:179-197` both require; adding a candidate that never answers
would trade a one-turn scripted fallback for a burned turn. The reviewer traced both
consequences and found them degrade-not-hang. Nothing to fix in code; the note's
two-candidate list is stale prose about a candidate the code explains removing.

## F6 — REFUTED (no change)

`llm.nim:222` reads "THIS ROUND IS NAMED IN THE REPORT BELOW, AND SO IS YOUR ROLE."
rather than the note's `THIS ROUND IS <MODE> AND YOU ARE THE <ROLE>.` That is a
deliberate rewrite, not a missing feature: the mode and the role do reach the model
every turn, in the view JSON (`decide.nim:170` `"mode"`, `:178` `"you".role`), and the
prompt line points at them. Keeping `SystemPrompt` a `const` keeps one identical
system prompt across all four seats of a batch. No information is lost, so there is
nothing to fix; changing the prompt text would change what every seat is told with no
way to measure the effect in CI.

## F7 — the prompt now states the tag exception (`295084b`)

`control.nim:384-425` forces a `tag` pursuer's `shadow` onto the evader at
`tagPx div 2` = 10 px, a measured, test-pinned rule (`test_control.nim:158-178`), and
`docs/RULES.md:194-195` already documents it. The **system prompt** — the one
description the model reads — still said "shadow = close to 60 pixels of the particle
nearest `target` and stay there" with no exception, so a pursuer reasoning from the
prompt was reasoning about a rule the engine does not run. Prompt text only.

## F8 — the stale baseline comment (`37a6805`)

`baselines.nim:189-197` said `shadow` is the wrong intent for a baseline pursuer and
the next line set `intShadow`. The behaviour is right (see F7); the comment described
the rule that change replaced. Comment only.

## F9 — `results.bumps` documented; the episode total is NEEDS-DESIGN (`6eccd8b`)

`beginRound` zeroes `sim.bumps` every round because the `spread` debit is a per-round
term (`scoring.nim:156`), so `results.bumps` and the endcard column carry the **last
round's** tick count while every other seat-indexed array in the same document is per
episode. The note never states the aggregation, so the number reads as an episode
figure and is not one.

Changed the documentation, not the number: `docs/PROTOCOL.md:229` states the
semantics, `roster.nim:714` says why at the site, the manifest is regenerated.
**NEEDS-DESIGN** for the alternative: an episode total needs a second accumulator in
`SimServer`, and to be trustworthy in the viewer it has to be in `gameHash` — which is
a GameVersion bump and a re-derivation decision, not a fixer's call.

## F10 — a tag seat's own live score (`60e3643`)

`seatViewJson` computed `score.this_round_so_far` from `roundAccum`, which `tag` never
writes (`scoring.nim:132`), so every seat in every tag round was told its round score
so far was 0.000 — while `broadcast.nim:1052` already special-cased the same number
for the spectator frame. The seat view now uses that same live term
(`sim.tagRoundPermille`), so the model reads what the audience sees.
`tests/test_observation.nim` asserts both directions: an untouched evader reads 1.000,
a pursuer with banked credit reads its own credit.

## F11 — NEEDS-DESIGN (no change)

The three modules the note lists as deleted are dead at runtime (the reviewer verified
`floorPaint: false`, the `paintBuff`/`hill` gates, and that none of the three flags
exists in the 52-property `config_schema`, which is `additionalProperties: false`), but
removing them is not a fixer-sized change:

* `src/mpe/paint.nim` is **imported and re-exported** by `sim.nim:13,16`; deleting it
  edits the hashed step path and the render bakes.
* `src/mpe/map_pool.nim` backs `arena.nim`'s `pool` mapPath (`arena.nim:15,1445,3146-3151,3422,3543`) — a feature of the inherited engine, not dead code local to this fork.
* `src/mpe/mapgen_styles.nim` is imported by nothing and could be deleted alone, but
  deleting one of three leaves the note no more true, and the note's "deleted" list also
  covers the procedural generator, which still lives *inside* `arena.nim`.

What the change would be: drop `paint` from `sim.nim`'s import/export and every call
site, drop the `pool` mapPath and `MapPoolSeeds`, delete `mapgen_styles.nim`, and
decide whether the resulting `gameHash`/keyframe layout warrants a GameVersion bump.
That is a deliberate refactor of the starter fork with a re-derivation question in it,
and it is not on the acceptance checklist.

## F12 — `certify --timeout-seconds 300` (`646e358`)

Added, with the note's own reason in a comment: the default 60 s does not cover start
+ connect grace + four rounds + linger, which is how cooperative-hunting 0.1.2 read a
healthy episode as a certification timeout. The flag was on `upload-coworld` and the
hosted smoke but not on `coworld certify`.

## F13 — REFUTED (no change)

Checklist item 10 requires that `game.protocols` carry **both** `player` and `global`
in object form, and it does. `docs/PROTOCOL.md` is one document that covers both
wires — the seat websocket (its "Per-seat observation" and reply-schema sections) and
the spectator frame (its "Broadcast chrome frame" and derived-event sections) — so
both keys point at the text that documents them. Splitting it into two half-documents
would make each key's value *less* complete than what it now serves, for no checklist
gain. Recorded as an accepted deviation from the note's wording rather than a defect.

## F14 — the landmark sampler is bounded, and an unfillable box is rejected (`e92b6b6`)

`while true` with a spacing that relaxes to a floor and stops relaxing is convergence,
not a bound — and it is **reachable**: `landmarkMargin` is a hosted config field the
generated schema allows up to **600**, `mapPath` is pinned to the 1235 × 659 `field`,
and at margin 600 the placement box is a 34 × 1 px strip in which four marks 120 px
apart do not exist. The draw would have spun until the 1200 s episode timeout with no
frame, no score and no fault. That is a `hang` under item 5, from a config the schema
admits.

* `field.nim`: the draw gives up after `MaxLandmarkDraws` (4000) rejected samples and
  falls back to a deterministic lattice sweep for the most isolated walkable point.
  The sweep draws **no random numbers**, so the seeded draw order the wasm viewer
  re-derives is byte-identical for every seed that ever terminated, and nothing on a
  shipped board reaches it (10 000 seeds settle in a handful of draws each — that test
  still passes, with ≥ 95 % keeping the full 300 px spacing).
* `sim_config.nim`: a `landmarkMargin` whose placement box cannot hold
  `LandmarkCount` marks at `MinLandmarkSpacingPx` is now rejected at validation, so a
  hosted config fails fast instead of reaching either the sweep or the sim guard.

`tests/test_field.nim` adds both: the infeasible box **returns** with four marks in
bounds (the test returning is the assertion), and the same config is rejected by
`update()` while the shipped margin still validates. Both green in CI, debug and
release.

## F15 — REFUTED (no change)

`server.nim:824-853` is byte-inherited from the starter (identical block, identical
lines in `/workspace/starters/coworld-ctf/src/ctf/server.nim`) and the design note
lists the route as inherited and intended. Item 3's substance is where the replay
VIEWER comes from, and that is settled: `coworld_manifest_template.json` declares
`"replay_viewer": {"bundle": "static-replay-viewer"}` and nothing else, no platform
routing points at a pod, and the only other occurrences of the string are inside the
inlined `docs/PROTOCOL.md` route table. The pod additionally serves a dev page behind
`replayServerModeEnabled()`. Removing it would mean editing inherited starter server
code — against item 14's provenance rule — to change nothing a hosted replay touches.
Left for the judge to rule on the literal reading, with that trade stated.

## F16 — the stream test now asserts what the note specifies (`2b3d6c2`)

`counts["directive"] >= 4` was a floor four records deep that a single turn satisfies,
and `onpoint` was asserted nowhere. Now: the per-turn count is grouped — every
`(round, turn)` in the parsed summary carries exactly `FixtureSeats` directives, over
at least four turns — and `onpoint` gets a direct detector block, the same treatment
`tag` already has and for the same reason (a drifter pack reaches the goal only by
luck inside 540 ticks, so requiring it from the played episode would be a flaky
assertion, not a stronger one). The block puts a mobile agent on the round's goal,
checks `updateBeliefs` reports the crossing once, and checks `stepEvents` turns it
into an `onpoint` event naming that seat and mark. (For the record, CI's played
episode did emit it: `derived kinds: @["cover", "decode", "phase", "gameover",
"roundover", "roundstart", "onpoint", "bump", "word", "firstword"]`.)

## F17 — no action

The one test-file change made during the run (`99dcaab`, `tests/test_motion.nim`) adds
a whole-identifier matcher so `isqrt(` no longer trips the `sqrt(` scan. No assertion
deleted, no tolerance widened, no `skip`/`xfail` added, no file removed, module list
unchanged. Item 1's "no test loosened" holds for it, and for every change in this
round: `git log -p 99dcaab..HEAD -- tests/` is additive in all six touched files.

## F18 — REFUTED (no change)

`client/replay_broadcast.html:4093` (`stage.classList.toggle('tiny', boardW <= 620)`)
is byte-identical to the starter's line, and the starter has no 640 px rule either.
Item 11's "labels hidden under 640px" is satisfied by the starter's `.tiny` density
system at the width that matters — the 360 px featured-match embed, which the fixture
now renders and measures. Changing the number would edit inherited chrome above the
banner and break the provenance the same checklist demands in item 14.

---

## NOTED (not fixed) — outside this round's findings

* `client/replay_broadcast.html:1306,1641` still carries the starter's locker-room
  captions ("Filling hoppers with fresh paint…"), inherited prose about a game this
  fork does not play. It is the one `ellipsized` count in the fixture's `canvas_text`
  line. Not a finding in r1; left alone.
* `viewer-smoke.json`'s `never_inside` tally is keyed by string across all three
  fixture widths, so a run that is off-frame at 360 px but inside at 1280 px would not
  be `never_inside`. The fixture's own per-width DOM check (`data-replay-error`) is the
  strict gate for that case, which is why both checks exist.
