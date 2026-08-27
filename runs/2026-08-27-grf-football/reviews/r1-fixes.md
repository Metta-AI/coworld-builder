# r1 fixes — grf-football

Repo: `Metta-AI/cogame-grf-football`, branch `main`.
Head: **`f810b0fbe5e2ad349667330edbc5207f5baf30a6`** ("r1-F18: the parry block asserts a parry again").
CI: **run `33059866708`** — https://github.com/Metta-AI/cogame-grf-football/actions/runs/33059866708 —
conclusion **`success`**, all four jobs (`test`, `docker-smoke`, `replay-rehash`, `wasm-viewer`)
`success`, at head sha `f810b0fb`.

Twelve commits, one per finding, all pushed to `main`. Nine findings are recorded as no-change with
the evidence that settles them. The review was taken at `66093e57`; every finding below was
re-evaluated against the **current** tip, which had advanced twice before I started and once during.

> **Push mechanism, for the record.** Git-over-HTTPS is not available in this sandbox (`git push`
> returns `remote: Invalid username or token` for every remote, including `coworld-builder`), so each
> commit was replayed onto `main` through the GitHub Git Data API (blobs → tree → commit → ref
> fast-forward, never forced). The commit objects on `main` therefore carry different shas from the
> local ones; the shas in this table are the ones on `main`. Trees are byte-identical (verified with
> `git diff` after each `fetch`/`reset --hard origin/main`).

| finding | disposition | commit on `main` | files | checklist item |
|---|---|---|---|---|
| — (red main) | fixed upstream by the other thread | `9edae99` (not mine) | `src/grf_football/sim.nim` | 1 |
| F1 | no change — already fixed on current main | — | — | 5 (verified) |
| F2 | fixed | `8853961` | `tests/test_perf.nim` | 5 |
| F3 | fixed (documented) + F4's real half fixed | `233bf09` | `.github/workflows/ci.yml`, `client/replay_broadcast.html`, `tests/test_viewer.nim` | 15 |
| F4 | fixed | `233bf09` | as above | 15 |
| F5 | fixed | `6f0e089` | `src/grf_football/llm.nim`, `tests/test_replay_utf8.nim` | 9 |
| F6 | no change — finding is "present and correct" | — | — | 9 |
| F7 | half fixed, half declined | `938da21` | `src/grf_football/sim.nim`, `sim_types.nim`, `docs/RULES.md`, manifest | — |
| F8 | fixed | `8b10ca7` | `src/grf_football/sim_state.nim`, `sim_types.nim`, `tests/test_determinism.nim` | 2 |
| F9 | no change — finding is "implemented and green" | — | — | 2 |
| F10 | fixed (documented) | `824ba03` | `docs/PROTOCOL.md`, manifest | 2 |
| F11 | no change — finding is "traced and consistent" | — | — | 14 |
| F12 | half declined, half fixed | `67fd3e7` | `src/grf_football/replays.nim`, `tests/test_viewer.nim` | 14(d) |
| F13 | **DECLINED** — design-note-sanctioned, and the removal is riskier than the finding | — | — | 14 (last bullet) |
| F14 | fixed | `2f557ee` | `tools/tune_baselines.nim`, `docs/tuning/baseline-grid.md`, `src/grf_football/baselines.nim`, `tests/lib/helpers.nim`, `AGENTS.md`, `.gitignore` | 7 |
| F15 | fixed | `0c9c404` | `tests/test_control.nim`, `tests/lib/helpers.nim` | 7 |
| F16 | no change — consistent; the one "minor" is code+test agreeing | — | — | 3, 6, 10 |
| F17 | no change — consistent | — | — | 6, 12 |
| F18 | first half agreed (no change), second half **fixed** | `f810b0f` | `tests/test_physics.nim`, `src/grf_football/sim.nim` | 1 |
| F19 | fixed | `f7dd24f` | `src/grf_football/builtin_ai.nim`, `docs/RULES.md`, `tests/test_control.nim`, manifest | — |
| F20 | fixed | `4a20cd6` | `src/grf_football/builtin_ai.nim`, `control.nim`, `tests/test_control.nim` | — |
| F21 | **DECLINED** — checklist 14 gates the CSS, which is deletions-only | — | — | 14 |

---

## Main was red when I arrived, from a commit newer than the review

Not a finding, but it gates everything: `main` had advanced to `1403e878` ("GV4: a pass you cannot
receive is not a pass"), whose CI run `33055720424` was **red** on two tests in both build modes:

```
tests/test_physics.nim(206) `sim.ball.controller < 0`   the pass releases possession
tests/test_control.nim(113) `zonalGoals >= pressGoals`  zonal 2 vs gegenpress 3
```

Cause: GV4 raised `ControlSpeed` from 12 to 18 m/s so a 14 m/s short pass could be received, but the
ball leaves the passer's foot 0.9 m away — inside the 1.1 m `ControlRadius` — so the passer re-took
its own pass on the next substep and no pass ever left. I fixed it (a cog inside its own pass
cooldown is transparent to the ball, as a grounded or sliding cog already is), and while I was
pushing, the other thread pushed `9edae99` ("GV4, continued: a passer cannot re-take its own pass")
with a superset of the same fix. I **dropped my commit** rather than fight it, reset onto `9edae99`,
and verified the whole suite green there in both modes before starting on the findings. All twelve of
my commits sit on top of `9edae99`. The other thread has pushed nothing since 08:57Z.

---

## F1 — `deadline` at the reviewed sha; render ~124 ms/tick

**No change.** Fixed on `main` before I started, by `c5cdc01` ("render: the rig sprite's label was
making it redefine itself every frame"), and still fixed at my head. Evidence from **run
`33059866708`** (my head `f810b0fb`), job `docker-smoke`, step `Raw-Docker episode smoke`, verbatim:

```
grf-football: tick 1440 budget: sim 0 ms, render 5640 ms, limiter 2941 ms, elapsed 9s
episode end reason: complete
smoke OK: seats=8 results=707B replay=124962B reason=complete
```

That is **3.9 ms/tick** of render against the reviewed sha's 124 ms, and the 1440-tick certification
episode settles in **9 s** (final tick 1848, ~11 s including the game-over hold) against the 180 s
budget the fixture sets.

The production `match` variant, arithmetic from those numbers: render 3.9 ms × 5760 ≈ **22 s**; the
rate floor is 24 turns × `turnSpacingMs` 18 000 = **432 s** (`decide.nim:399-405`); `fastMode: true`
with all seats ready makes the frame limiter skip rather than pace (`server.nim:340-350`), so it
adds nothing; the 360-tick game-over hold is ~1.5 s of render. Total ≈ **460 s**, inside the 690 s
`wallClockBudgetSeconds` stop and inside the 720 s (60 % of 1200 s) settle requirement — and close to
the design note's own 492 s estimate (design.md:404-415). F1's extrapolation was arithmetic from the
124 ms/tick sha and no longer applies.

The review's related note that `docker_smoke.sh` prints `reason` without gating on it is still true.
I left it alone: it is the template's script and the reason is now `complete`. The regression guard I
did add is F2's — a red `test` job is a better signal than a red smoke.

## F2 — the perf bound did not measure the serve path

**Fixed, `8853961`.** `test_perf.nim` called `runScriptedMatch`, which never touches
`buildSpriteProtocolPlayerUpdates`, `stepEvents` or `buildStateJson`, so the 124 ms/tick render cost
that ended the reviewed sha's episode `deadline` was outside every timing bound in the tree.

The test now steps exactly what `server.nim:717-800` steps: turn, control compile, `sim.step`, the
hash, `stepEvents`, one sprite packet per seat, and the chrome frame — over all 5760 ticks, with the
board render caches warmed as the server warms them — and reports the sim and serve halves
separately. Both halves accumulate in **microseconds**: a per-tick `inMilliseconds` delta truncates
to 0 for a 0.2 ms tick, which is why the smoke's own line says `sim 0 ms` and why my first cut
reported `sim 0 ms, serve 44 ms` for a 1354 ms run.

Evidence, release, locally: `5760 ticks served in 1366 ms (sim 478 ms, serve 881 ms)`. The reviewed
sha's cost would be ≈714 s against the test's 120 s bound. Green in CI run `33059866708`
(`test_perf` is release-only via `NIM_TESTS_RELEASE_ONLY`).

## F3 + F4 — `canvas_text: 0`, and where the model's text actually goes

**Both fixed, `233bf09`**, and they are one question so they are one commit.

Confirmed the review's observations, independently: the board is drawn into an OffscreenCanvas inside
`replay-viewer/static_replay_worker.js`, which `viewer_smoke.mjs` cannot instrument (it says so at
its own lines 140-142) — **and** this game draws no strings on any canvas at all. The complete sprite
vocabulary is `labels.nim:13-56` and every entry is a sprite, not a `fillText`. So `total: 0` here is
a fact about the renderer, and there is nothing for a worst-case **canvas** fixture to render: the
checklist's fixture clause describes "a page that loads the real `client/renderer.js` and hands it a
frame built to hurt", and this repo has no such module and no canvas text to hurt.

`ci.yml`'s smoke step now says all of that at the step, so the next reader does not have to infer it,
and `--strict-text-bounds` stays armed for the day something is drawn main-thread.

**What was not true is that the DOM path was therefore safe** — and this is the real defect the pair
of findings was circling. `note` (≤ 160 runes) and `say` (≤ 48) are LLM-authored and are rendered as
`.feed-row`s by `fbDirectives`. The inherited `.feed-row` is `white-space: nowrap; max-width: none`
(`client/replay_broadcast.html:488-505`) — right for ctf's three-word kill lines. A 160-rune note on
one unwrappable line is wider than the whole 1200 px board, and `#killfeed` is anchored
`right: calc(12 * var(--u))` with `align-items: flex-end`, so the row grows **leftward off the
stage** and the sentence is simply not there. That is cogchemists' clipped speech bubble in DOM form,
and no gate in the repo could see it (the CI replay has no LLM text, and the canvas harness cannot
see DOM).

Fix, inside the appended game block only (nothing above the banner touched): both rows that carry
model text now carry `fb-model`, a band that

* bounds its width at `calc(228 * var(--u))` — the `#killfeed` width — and `calc(186 * var(--u))` at
  `#stage.tiny`;
* wraps (`white-space: normal`) and breaks an unbroken token (`overflow-wrap`/`word-break`);
* is **sized from the server's own caps** — 160 runes of the 8u pixel font wraps to at most five
  lines of that width;
* never ellipsizes: a remark that does not fit gets more lines, not fewer words;
* rides `#killfeed`'s inherited **fixed four-row reserve**, which is kept, so the scene does not jump
  when a remark lands.

`tests/test_viewer.nim` gains `modelTextHasAWrappingBand`: the rule exists, bounds its width, wraps,
breaks long tokens, does **not** ellipsize; both JS call sites pass the class; `MaxNoteRunes` and
`MaxSayRunes` are still 160/48 (if a cap moves, re-measure the band rather than discover the overflow
in a replay); and `#killfeed` still reserves four rows.

Evidence: `tests/test_viewer.nim` green in both modes; CI `33059866708` `wasm-viewer` step
`Load the bundle in a real browser`:
`{"loaded":true,"ms":315,...,"feed_lines":0}` and
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.

**F4's `feed_lines: 0` is settled as timing, not a missing renderer.** The same smoke line reports
`"clock":":01 STARTING IN KICKOFF · BLUE"` — the first drawn frame is the pre-kickoff frame, before
turn 0 has installed a directive, so there is nothing to draw yet. Model text reaches the DOM through
`fbDirectives(s.directives)`, whose two call sites are now pinned by the new test.

## F5 — error text byte-sliced before it is rune-clipped

**Fixed, `6f0e089`.** Acceptance checklist item **9**.

`llm.nim` sliced the HTTP body and the model's text by byte index at five sites (`:168` 400, `:176`
300, `:181` 300, `:192` 160, `:201-203` 160). Each becomes a `GrfFootballError` message;
`decide.nim:428-431`/`:460-462` put `failure.msg` into `detail` and `:386`/`:467` record it as
`fallback.detail` in the replay. `docs/RULES.md` and `AGENTS.md` rule 2 forbid a byte slice on any
path to the replay.

All five now go through one `errorDetail` helper: newlines to spaces (preserving what
`.replace("\n", " ")` was for), then `clipRunes` on rune boundaries. The one remaining slice,
`text[start .. stop]` in `extractJsonObject`, is between the offsets of an ASCII `{` and `}` —
rune-safe by construction in valid UTF-8, and it goes to the JSON parser, not the replay; the comment
now says so.

`tests/test_replay_utf8.nim` gains `errorDetailIsRuneSafe`, which feeds each path an input whose
**old** cut point lands mid-character (two ASCII bytes, then 600 four-byte U+1F3C6, so every one of
400/300/160 is odd) and asserts the detail is valid UTF-8, carries no U+00F0 — the mojibake a cut
`0xF0` lead re-encodes to — and still contains the character. Evidence that it bites: against the old
`llm.nim` it fails at the first assertion, `the detail for 401 is not UTF-8`.

**It also settles the review's open question** ("whether `clipRunes` survives invalid UTF-8 in a debug
build"): the test feeds a deliberately byte-truncated lead byte and neither build raises. Nim's
`fastRuneAt` validates continuation bytes and yields the lead byte as its own rune, so `clipRunes`
re-encodes it rather than reading past the end. No `IndexDefect` exists — but the mangling it produces
did, which is what the fix removes.

## F6 — the multi-byte-at-the-cap tests are present

**No change.** The finding records that the tests the note promises exist and that the caps match.
Agreed; `errorDetailIsRuneSafe` (F5) is now beside them.

## F7 — two `sim.nim` behaviours differ from the note's resolution order

**Possession bookkeeping: fixed, `938da21`.** The code credited `possessionTicks` to the current
controller **and**, on a loose ball, to the last toucher's team. Design step 9 (design.md:290) says
"for the team of the **current controller** (nothing before the first touch)". The `elif` is gone.
Consequence removed: the broadcast possession bar (`broadcast.nim:276-277`) and
`results.teams.*.possession` (`roster.nim:186`) credited every loose-ball tick to whoever last touched
it, so a team that had just lost the ball still read as holding it. `docs/RULES.md` step 8 now states
the rule instead of leaving it to "possession bookkeeping". `possessionTicks` is hashed
(`sim_state.nim:152`), so `GameVersion` went to **GV5** with a changelog line and the manifest was
regenerated.

**Out-of-play per substep: DECLINED.** `handleOutOfPlay` runs inside the four-substep loop, which the
note's *step 8* puts at tick level. Evidence for declining, in order:

1. The repo's own rules doc already documents the substep-level test — `docs/RULES.md` §Resolution
   order step 7 reads "…→ netting → goal test → **out-of-play test**", per substep, and that doc is
   inlined into `game.docs` in the manifest. It is not an undocumented deviation.
2. It is strictly more correct. The note's own step 7.8 puts the **goal** test inside the substep
   loop; testing the goal line 4× a tick and the touchline 1× lets a ball cross a touchline in
   substep 1 and be resolved from wherever it reached by substep 4, which is a wrong restart spot.
3. Moving it would change the hash chain for a behaviour nobody has complained about, in the same
   round as two other chain changes.

The review itself notes the "only if no goal" ordering the note demands **is** honoured
(`sim.nim:1031-1036`).

## F8 — `gameHash` mixed three cosmetic pool lengths

**Fixed, `8b10ca7`.** Acceptance checklist item **2** area.

`sim_state.nim:117-119` mixed `trail.len`, `arcs.len` and `goalFx.len` into `gameHash` while four
places in the tree say it never does: the note's step 11 ("It **never** mixes directives, notes, FX or
trails"), `sim_state.nim`'s own module docstring, the field comments at `sim_types.nim:537-539`
("never hashed"), and `docs/RULES.md`. The three lines are gone.

Consequence removed: a difference in a celebration pool reported itself as a divergence of the hashed
state — the opposite of what GV2's per-field chain was for.

`tests/test_determinism.nim` gains `cosmeticPoolsAreOutsideTheHash`, which appends to `trail`, `arcs`,
`goalFx` and `feed` and sets a directive note by hand, and requires the hash not to move. Against the
old code it fails: `gameHash moved when only FX, the trail, the feed or a directive changed`.

The chain changes, so `GameVersion` went to **GV6** with a changelog line. **No recorded fixture is
invalidated**: `git ls-files tests/fixtures` is `.gitkeep` only, and `ci.yml`'s
`Record the replay fixture (native build)` step cuts the wasm smoke's fixture fresh from the same
commit and hands it to `wasm-viewer` as an artifact — which is why `replay-rehash` and `wasm-viewer`
are green at my head (`ok: loaded grf-679961.replay, advanced 4000 frames`).

**NOTED (not fixed):** the `stateDigest` **forensic** checkpoint (`sim_state.nim:245-247`) still puts
the three pool lengths in, and the comment on `lastGoalTick`/`lastGoalTeam`/… at
`sim_types.nim:547-549` says "NOT hashed" while `gameHash` mixes them (GV2 added them deliberately).
Neither is F8's citation and neither is a checklist item; the first is a diagnostic string, not the
chain.

## F9 — replay re-derivation is implemented, tested and green

**No change.** Confirmed at my head: `replay-rehash` green, and `wasm-viewer`'s determinism gate in
run `33059866708` logs `ok: loaded grf-679961.replay, advanced 4000 frames` and
`ok: loaded replay.json, advanced 4000 frames`.

## F10 — `stop` and `state` are not in the note's record vocabulary

**Fixed as documentation, `824ba03`.** Both records are deliberate and both stay; the gap was that
the only place either was explained was the `GameVersion` changelog. `docs/PROTOCOL.md` §The replay
bytes now lists them in the `chats` row, and §Record vocabulary carries `stop` with its fields plus
two paragraphs: why a wall-clock fact cannot be re-derived from the action log (GV3 — every
`deadline` replay diverged from itself at the stop tick until the stop became a record applied by the
same idempotent `finishGame` on both sides), and that `state` is diagnostic, is not a game record,
bypasses the 900-rune cap deliberately, and is ignored by a reader that does not know the kind —
which is literally what `tools/replay_summary.py` does (its chat loop has no branch for either, and
unknown keys fall through). Two stale strings in the same page that said the replay header and the
summary carry game version `1` are corrected. Manifest regenerated (`game.docs` inlines the page).

I did not edit the design note (out of bounds for the fixer).

## F11 — chrome provenance

**No change.** "Traced and consistent." Re-verified that `chrome_common.js` is byte-identical
(`tests/test_viewer.nim` pins length 40022 + FNV-1a and is green) and that my one page edit is inside
the appended block, below the banner.

## F12 — beats

**First half DECLINED.** Item 14(d) names `chrome_common.markBeat(tick, kind, team, label)` as the
mechanism, and the football beats are built by the game block's own `fbBeat`. Declining because the
two halves of item 14 cannot both be satisfied literally: 14's first bullet requires
`chrome_common.js` byte-identical to the starter's, and the starter's `markBeat`
(`chrome_common.js:538-562`) takes no `label` and creates unlabelled `div`s. The substance of 14(d) —
"scrubber beats are labelled `<button>`s that seek to their tick, with CSS for every kind the page
emits" — is met and machine-asserted (`tests/test_viewer.nim`: `button.beat-marker`, `aria-label`,
`CTX.send('s:' + tick)`, a `.beat-marker.<kind>` rule for all seven kinds), and the design note
§Transport rules (design.md:963-967) prescribes exactly this shape. The review also traced that no
unlabelled div marker can reach the scrubber in this game.

**Second half fixed, `67fd3e7`.** `replays.nim:400-402` shipped `goal`, `drop` and `gameover` in the
up-front beat timeline, and the page's timeline loop has no `drop` branch — so a `drop` travelled in
every replay's bytes and drew nothing. The filter is now the note's scrubber-beat set exactly
(`gamestart`, `goal`, `shot` on target only — as the live path filters it — `save`, `foul`,
`halftime`, `gameover`) and no longer `drop`. Two consequences: the dead kind is out of the bytes,
and the **five kinds that were missing** from the timeline (`gamestart`, `shot`, `save`, `foul`,
`halftime`) now put their markers on the scrubber the moment the replay loads instead of appearing
only once the playhead has passed them. `scan.beatTicks` still counts a drop — that is the lull
detector, not the scrubber. `everyBeatKindHasCss` now also requires a `b.k === '<kind>'` branch for
each of the seven and requires `b.k === 'drop'` to be absent.

## F13 — the retained `core.zoomAt / setZoom / panBy` wiring

**DECLINED.** This is the one place I am knowingly not satisfying the checklist's literal wording, so
here is the whole case; the judge should adjudicate it.

What the checklist says (item 14, last bullet): a fixed-arena game "removes the panel — markup, CSS,
**the `core.zoomAt/setZoom/attachMinimap` wiring**, and the ids from the test list — rather than
hiding it."

What is true in the tree:

* The **panel** is removed, not hidden: no `#viewpanel`, `#zoombar`, `#minimap`, `#zoom-`,
  `fpv-canvas` or `minimap-canvas` markup, CSS or ids anywhere — `tests/test_viewer.nim:23-24,63-72`
  asserts their absence and is green. `attachMinimap` is **never called** from the page
  (`grep -n attachMinimap client/replay_broadcast.html` → no match).
* What remains is the **inherited page's own** keyboard (`z`/`x`/`0`/arrows) and gesture (ctrl+wheel,
  Safari `gesturechange`, touch pinch, drag) handlers, above the banner, unmodified from
  coworld-ctf's. They present **no UI surface at all** — there is nothing on screen to hide.
* The design note sanctions them explicitly and the page carries the note's reasoning verbatim at
  `client/replay_broadcast.html:2586-2591`: "The starter's zoom cluster and minimap … are removed …
  The keyboard's z / x / arrow handlers below still drive core.zoomAt / core.panBy for a viewer who
  wants a closer look at a scramble". design.md:939-941 and :949-952 list only the panel's
  markup/CSS/ids as removed.

Why removing them is worse than keeping them: the handlers are not separable. `core.panBy` sits
inside the same `pointerdown`/`pointermove`/`endPointer` block that implements **click-to-select** —
`dragging`, `dragMoved`, `syncTouchAction` and the pinch map are all one mechanism
(`client/replay_broadcast.html:2516-2578`). Deleting the zoom/pan half means rewriting the inherited
selection path, and checklist 14's second bullet exists precisely to stop a game rewriting inherited
chrome (cogame-gridlock's from-scratch page). Trading a literal reading of the last bullet for a
rewrite of the starter's pointer handling is the wrong trade, and a dangling variable there is a
thrown exception in the viewer's own input path, which no test in the tree would catch.

If the judge disagrees, the minimal compliant change is to delete the six `z`/`x`/`0`/arrow branches
in the `keydown` switch (2425-2441), the `wheel`/`gesture*` listeners (2478-2506) and the pinch/pan
arms of the pointer block (2513-2578), and re-derive `syncTouchAction`/`dragMoved` for
selection-only. I have not made it.

## F14 — no grid harness

**Fixed, `2f557ee`.** Acceptance checklist item **7**, second sentence.

* `zonal`'s free parameters are now named (`ZonalParams`: press radius, shoot range, pressure radius)
  and `zonalDirectiveWith` takes them. `zonalDirective` is that proc at `ZonalTuned` and is what the
  game runs; `runScriptedMatch` gains a `zonalParams` seam defaulting to the tuned point, so every
  pre-existing test still measures the shipped baseline.
* `tools/tune_baselines.nim` is the harness: **60 grid points** (5 press radii × 4 shoot ranges × 3
  pressure radii), each scored over **full-length 5760-tick** matches against the `gegenpress` foil,
  on two train seeds each played **both ways round** — 240 matches — with two holdout seeds scored
  for the winner and the incumbent **only, after the choice**, so an overfitted point is visible
  instead of hidden. Ties break toward the smaller press radius.
* `docs/tuning/baseline-grid.md` is the committed artifact: method, the top eight, the holdout
  comparison, and the full 60-row table.

Result: the winner is **press 12 m / shoot 16 m / pressure 1.5 m**, train goal difference **+5** and
holdout **+8 (8-0)**. The design note's guessed 15 m / 20 m / 2.5 m scores **−1** on the train split —
it *loses* to `gegenpress` on those seeds — and +2 on the holdout. The artifact records the deviation
from the note and the mechanism: a shot from 20 m or more is a turnover in this physics (the keeper
catches anything at or under 18 m/s and the aim error grows with distance), and a wide press radius
pulls the shape apart.

The harness is not run in CI — 240 full matches is ~2 minutes and its output is an artifact, not an
assertion. What holds the conclusion in CI is `zonalBeatsGegenpress` (untouched) and F15's new test.

## F15 — "complete" and "every order legal" were in different tests

**Fixed, `0c9c404`.** Acceptance checklist item **7**, first sentence.

`aFullScriptedEpisodeIsCompleteAndLegal` runs **one** all-scripted episode at the full 5760 ticks to
its natural end and asserts, from that same episode: (a) the real `playerResultsJson()` document
reads `reason: "complete"` and `endRule: "full_time"` and the whole clock was played; (b) every one
of 22 bytes on every one of 5760 ticks decodes to a legal direction/code and **re-encodes to itself
exactly**; (c) every order installed over the episode — note and say inside their rune caps, target
on the pitch, `pass_to` a teammate or null and never itself, role the seat's own.

`runScriptedMatch` now returns the orders it installed and the real results document so one test can
see both halves. The narrower pre-existing tests are untouched, per "do not weaken a test".

## F16 / F17 — manifest, docs shape, protocols, seat-count invariants, workflow order

**No change.** Both findings are "traced and consistent". Re-confirmed at my head: `docker-smoke`
green with `smoke OK: seats=8 …` and **no `SEAT-COUNT` match anywhere** in run `33059866708`'s log;
`python3 tools/build_manifest.py --check` prints `manifest up to date` after every doc edit I made
(F7, F10, F19), and `tests/test_manifest.nim` is green in both modes. F16's "minor" — `tags` at the
manifest top level rather than `game.tags` — is code and test agreeing against a stale note path, and
checklist item 10 does not mention `tags`; unchanged.

## F18 — two test assertions were replaced during this run

**First half: agreed, no change.** `aef2def`'s `slideTackleAndFoul` is a **tightening**, and the code
proves it rather than the commit message. `sim.cogStats[i].tackles` is incremented at
`sim.nim:747-748` inside the one branch that then calls `knockBallLoose` (`sim.nim:722-729`, which
sets `ball.controller = -1`) — and that branch is gated on `slideTouchedBall` being newly true and on
`sim.ball.controller >= 0 and != i`. So `tackles == 1` **strictly implies** the removed assertion's
content ("a slide that reaches the ball knocks it loose") at the moment the tackle happened, and
`fouls == 0` is a new assertion on top. The removed form could also be falsified by ordinary play
after the knock, which is what the commit message says. Not a loosening.

**Second half: FIXED, `f810b0f`** — `c755d4d`'s `keeperCatchesAndParries` **was** a loosening.

`doAssert sim.restartKind != rkGoalKick, "a 25 m/s ball is parried, not caught"` was deleted. I
probed that exact fixture on current `main`:

```
restartKind=rkGoalKick saves=2 ballspeed=0 cap=500000 goalsRed=0 ballctrl=-1
```

So the deleted assertion is genuinely **false** — the keeper parries and then legitimately gathers
the rebound on a later substep of the same tick — and could not simply be restored. But its
replacements could not tell a parry from a catch either: the gathered ball has `v = 0`, so
`speedOf(ball) <= KeeperParryCap` passed trivially, and `saves >= 1` counts both. The block named
"parry" asserted nothing about parrying.

End-of-tick state cannot answer the question, so the test now reads the tier-2 event stream, which
can: the sim emits `Save` with content `"parry"` or `"catch"`. The block asserts a parry event exists
and that its speed is above zero and at or under `KeeperParryCap`. `emitEvent` for the parry now
carries that speed (the field already existed and was 0); the tier-2 JSONL stream is its only
consumer — `broadcast.stepEvents` derives the chrome's events from state deltas, not from these.

No test file was deleted this run (`git log --diff-filter=D --name-only -- tests/` → empty) and no
`skip`/`xfail`/`when false` appears anywhere in `tests/`. Every test change of mine adds assertions;
each new test was demonstrated to fail against the pre-fix code, and I recorded that failure message
in its commit.

## F19 — the built-in keeper had no goal-kick rule

**Fixed, `f7dd24f`.** `builtin_ai.nim:359-372` took `safeOnBall` for every cog in possession, keeper
included, so the note's §The built-in AI item 1 (design.md:556-560) — "on possession, goal-kick
`pass_long` to the most open teammate beyond the halfway line, else `pass_short` to the nearest full
back" — was implemented nowhere.

Consequence removed: `safeOnBall`'s branches are written for an outfielder. Its shot branch measures
the distance to the **opponent** goal, which from a keeper's own six-yard box is the length of the
pitch, so the keeper fell through to "carry at the far goal" with the steering point set to
`targetGoalX` and dribbled the ball out of its own area.

Added `mostOpenBeyondHalfway`, `nearestFullBack` and `keeperOnBall`; `builtinAction` dispatches on
`isKeeper`, and a keeper on the ball steers at its own keeper arc rather than the far goal so a
dropped release does not walk it up-field. `docs/RULES.md` §Keeper states the rule; manifest
regenerated. This is outside the determinism boundary — the built-in AI's bytes are recorded and the
viewer re-simulates the recorded bytes, so no replay is invalidated and no `GameVersion` bump is due.

`theKeeperPlaysAGoalKick` covers both branches (a teammate just beyond halfway → code 2 pointing
east at the target; nobody past halfway → code 1 to the nearer full back). Against the old dispatch
the first block fails with `got code 3` — a high pass at the far goal, i.e. the carry.

## F20 — `steerAction` dropped the nibble without consulting "is chasing"

**Fixed, `4a20cd6`.** `control.nim:89-95` computed `chasing` and used it only for the sprint bit, so
`steerAction` released the direction on arrival for a chasing cog too. The note's control-layer rule 2
(design.md:537-538) says the nibble is `0` when `dist(p*, pos) < 400 000` **and the cog is not chasing
the ball**. `steerAction` takes `chasing = false` and `control.nim` passes its own predicate.

Consequence removed: a cog sent to win a loose ball whose interception point was inside the 0.4 m
arrival radius — which is exactly where a slow ball puts it — released its direction and stood beside
the ball instead of taking it.

`chasingKeepsItsDirectionBits` builds one crawling loose ball 0.2 m from the seat's cog with every
other cog parked in the far corner, asserts up front that the intercept point really is inside
`ArriveUm`, then requires a non-zero nibble. Against the old code: `a chasing cog keeps its direction
bits, got dir 0`. The built-in AI's own chase branch keeps the default `chasing = false`: the note
states the rule for the control layer and its built-in-AI section does not restate it.

## F21 — the page retargets the inherited script in place

**DECLINED.** Checklist item 14's second bullet gates the **CSS** above the banner ("Diff the CSS
above that banner against the starter's: sections 1–5 … present and unmodified except for the
removals the note lists"), and the review's own F11 verified that diff: pure deletions, exactly the
`#fpv` and `#viewpanel` blocks the note lists, with no line above the banner modified. My own F3/F4
change added CSS **below** the banner only.

The in-place script edits F21 records are `PB_MODE`/`PB_CTX` → `FB_MODE`/`FB_CTX` mode branches, and
they are what makes the page a football page rather than a paintball page; reverting them would leave
the inherited script latching on `s.regime` (a key this game never emits) and the scorebug rendering
hill-time. The page's own banner is explicit that everything above it is "the classic broadcast page,
edited only where the mode demands and always behind FB_MODE" (`:2699-2703`), every node introduced
above the banner carries the `fb-` prefix, and `tests/test_viewer.nim:74-102` asserts that. The page
is 3174 lines against the starter's 4660, and the delta is the deleted fpv/viewpanel blocks — not a
rewrite.

---

## NOTED (not fixed)

Things I saw and deliberately left alone; none is a finding in this round's review.

1. **`state.feed` has no consumer in the page.** `broadcast.nim:406` ships `feed` in the state JSON
   and no page code reads `s.feed`; the DOM feed is fed by `applyEvent` and by
   `fbDirectives(s.directives)`. The model's `note`/`say` therefore **do** render (via `directives`),
   but the engine-authored `register`/`fallback`/`stop` feed rows never reach a spectator. Making
   them visible is a feature, not a fix.
2. **`docker_smoke.sh` prints `reason` without gating on it** (`:306-308,324`), which is how
   `reason=deadline` went green at the reviewed sha. It is the template's script and the reason is
   `complete` now; F2's bound is the guard I added instead.
3. **`stateDigest` still includes the three cosmetic pool lengths**, and the "NOT hashed" comment on
   the `lastGoal*` fields is stale (GV2 hashes them). See F8.
4. **`tools/ci/check_gameversion.sh` is not wired into any workflow** (`grep -rn check_gameversion
   .github/workflows` → no match), so the GameVersion collision it guards against is unenforced. I
   bumped GV5 and GV6 by hand and by discipline.
5. **`GameVersion` moved twice this round** (GV4 → GV5 in F7, GV5 → GV6 in F8), because two separate
   findings each changed the hash chain and the fixer's rule is one commit per finding. Both carry a
   changelog headline in the prepend-only format `check_gameversion.sh` reads.
