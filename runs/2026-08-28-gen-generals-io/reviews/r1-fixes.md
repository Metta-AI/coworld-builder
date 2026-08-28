# r1 fixes — gen-generals-io

Head: `e8be315f465c403c2abf6c3d379079b9a59e959f`
CI: https://github.com/Metta-AI/cogame-gen-generals-io/actions/runs/33151358030 — **success**
(`test` ✓ / `docker-smoke` ✓ / `wasm-viewer` ✓, event `push`, branch `main`,
head_sha `e8be315f465c403c2abf6c3d379079b9a59e959f`, 07:24:47Z → 07:29:19Z)

One commit per finding, in the order below. Every fix was verified locally before pushing: I
installed the repo's own toolchain in the sandbox (`nimby 0.1.26` → Nim 2.2.4, `nimby --global
sync nimby.lock`) and ran the whole suite in debug **and** release (0 failures, 144 debug
assertions), plus playwright 1.55.0 + chromium to run `tools/ci/viewer_smoke.mjs` against a
locally assembled copy of the bundle page.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `8407504` | `src/generals/replay_runtime.nim:199-245`, `replay-viewer/gen_replay.nim:69`, `tests/test_gen_replay.nim:220-262` |
| B2 | fixed | `be0ad41` (root cause `40af89c`) | `tools/ci/renderer_fixture.html`, `client/gen_block.html:115-137,:416-425`, `client/replay_broadcast.html`, `tests/test_gen_viewer.nim:197-236` |
| N1 | fixed | `40af89c` | `src/generals/directives.nim:456-487`, `src/generals/sim.nim:109-152`, `src/generals/server.nim:192-206`, `src/generals/replay_runtime.nim`, `tests/test_gen_replay.nim` |
| N2 | NEEDS-DESIGN | — | `src/generals/captain.nim:242-247` |
| N3 | fixed | `0c9689a` | `src/generals/server.nim:40,:600` |
| N4 | fixed | `9d21c5f` | `src/generals/decide.nim:90-95`, `src/generals/server.nim:289-297`, `tests/test_gen_engine.nim:238-253` |
| N5 | fixed | `85a3d5a` | `.github/workflows/ci.yml:159-197` |
| N6 | DISPUTED (note is ambiguous; code self-consistent) | — | `src/generals/resolve.nim:87-97` |
| N7 | fixed | `b0b8d93` | `src/generals/directives.nim:186-196,:241-252`, `tests/test_gen_observation.nim:124-150` |
| N8 | NEEDS-DESIGN | — | `src/generals/captain.nim:177-178`, `src/generals/vision.nim:34-38` |
| N9 | fixed | `c219a42` | `src/generals/baselines.nim:38-62`, `tools/ci/baseline_tuning.json` |
| N10 | NEEDS-DESIGN (rule 1 partly DISPUTED) | — | `src/generals/global.nim:220-234`, `src/generals/rig_art.nim:243-254` |
| N11 | fixed | `6960a53` | `src/generals/sim_types.nim:173-187`, `src/generals/directives.nim:310-313`, `tests/test_gen_directives.nim` |
| N12 | DISPUTED | — | `src/generals/board.nim:186-187` |
| N13 | fixed | `2a0b742` | `tests/test_gen_board.nim:6-10` and its four sweeps |
| N14 | fixed | `1ffbc03` | `tests/test_gen_determinism.nim:24-77` |
| N15 | fixed | `c0f02ac` | `tests/test_gen_directives.nim:119-141` |
| N16 | fixed | `f20f62f` | `tests/test_gen_resolve.nim:163-191` |
| N17 | fixed (data made honest; pick unchanged) | `e8be315` | `tools/tune_baselines.nim:88-124`, `tools/ci/baseline_tuning.json` |
| N18 | fixed (comment) | `3b3159b` | `replay-viewer/config.nims:42-46` |
| N19 | fixed | `d43fbe5` | `tools/build_broadcast_page.py:136-150`, `client/replay_broadcast.html` |
| N20 | DISPUTED | — | `tests/test_gen_endcard_labels.nim:65-67` |
| N21 | DISPUTED | — | `src/generals/sim_config.nim:197-233` |
| N22 | fixed (comment) | `1292c7f` | `src/gen_generals_io.nim:4-9` |
| N23 | fixed | `1644f9d` | `src/generals/directives.nim:42-104`, `tests/test_gen_directives.nim:9-39` |
| N24 | no action needed (the finding records a verified deviation, not a defect) | — | — |
| N25 | fixed | `8495474` | `src/gen_generals_io_player.nim:27-36,:86-131` |

---

## B1 — playback opened 48 ticks before `gameStart`, and no seek was clamped — **fixed** `8407504`

**Was:** `initReplaySession` set `startTick = config.startWaitTicks` (48 everywhere) and then
`cursor = 0`, so playback opened in the lobby prefix and walked it at presentation cadence;
`seekTo` clamped to `[0, endTick]`, so `applyCommand(',')` (`#btn-restart` and the `,` key) and
the loop wrap put the viewer back there every time, while the scrubber axis (`st`) and the
momentum graph had already dropped the same ticks.

**Is:** the cursor opens at `startTick` with `phase = phPlaying`, and `seekTo` clamps to
`[startTick, endTick]` — restart, step-back (`b`), a scrub click and the loop wrap all land on
the game start. `applyCommand(',')` and `advance()`'s loop target `session.startTick`.
`gen_replay.nim` stops computing a lobby countdown the cursor can no longer reach.
The hash-checked re-simulation is untouched: it still runs every recorded frame from turn 0
(playback turns are derived by `turnAt(cursor) = clamp(cursor - startTick, 0, endTurn)`).

**Evidence:** new suite `tests/test_gen_replay.nim` "playback opens at the game start", which uses
the checklist's own probe — a replay recorded with `startWaitTicks = 300`, i.e. a LATE game start
that a 1-tick lobby cannot show:
`cursor == startTick == 300`; `phase == phPlaying`; `,`, `seekTo(0)`, `seekTo(-500)`, `b` and the
loop wrap all leave the cursor at 300; three `advance()` calls put the sim on turn 3 with a
different `gameHash`; `seekTo(endTick)` still ends with `hashMismatchTick == -1` and
`session.sim.turn == sim.turn`. In CI the soak's first readout moved from `"0 / 312"` (run
33145429852) to `"3 / 312"` (run 33151358030) — it is now already playing when first sampled.
**Checklist item 13, third bullet.**

## B2 — the worst-case fixture never made the page draw a remark — **fixed** `be0ad41`

Three independent reasons the fixture measured nothing, all found by running it locally under the
real harness:

1. **It never used the page's remark path.** The only code that draws a note is
   `gen_block.html`'s `case 'plan':` inside `event(e, s, ctx)`, driven from `s.events`; the fixture
   put its 160-rune note in `state.plan[]`, which the page never reads.
2. **It never handed the page a single frame under `viewer_smoke.mjs`.** The harness's init script
   shadows `window.parent` with a postMessage stub *in every frame*
   (`tools/ci/viewer_smoke.mjs`, "`parent` is [Replaceable] on Window"), so the shim's
   `window.parent.__FRAMES` was `undefined`, the pump threw on its first tick, and what the fixture
   transcribed was the locker-room curtain. That is exactly what the reviewed CI line
   `{"loaded":true,"ms":6868,"clock":null,"scorebug":null,"feed_lines":0}` was reporting — I
   reproduced it locally byte for byte (27 text runs) before changing anything.
3. **Its frames stepped 8 ticks at a time**, which the page reads as a SEEK (`jumped` in
   `replay_broadcast.html:1462`) and whose events it drops — so even with (1) and (2) fixed, no
   feed row, banner or beat would have been drawn.

**Is:** frames are embedded in the shim and the shim publishes `__feed` on the iframe's own
window; frames step one tick; after the endcard is transcribed the fixture feeds a `plan` **event**
per seat — all four at once — each carrying the full 160-rune note, waits for the entrance
animation to settle, and then asserts at 1280 / 620 / 360 px that

* all four remarks are present, and each row's text still **contains the whole source string**
  (`text.indexOf(NOTE) < 0` → `data-replay-error: a commander remark was SHORTENED …`);
* no remark left the band the feed reserves for it, and no row clips its own content
  (`… left its reserved band …`);
* every DOM text run is transcribed to the probe canvas **line box by line box** (walked with a
  Range per character), so a wrapped sentence is three honest runs rather than one impossible
  1150 px run, and a line the page pushed off-frame still lands off the canvas.

A 160-rune sentence in the starter's `white-space: nowrap` feed row grows leftward across the
board, so the game block gives `.feed-row.plan` a wrapping band sized from `MaxNoteRunes`
(`#killfeed { min-height: calc(4 * 34 * var(--u)) }`, `overflow-wrap: anywhere`, never
ellipsized) and `client/replay_broadcast.html` is regenerated by `tools/build_broadcast_page.py`.

**Evidence:** CI run 33151358030, step `Drive the shipped page with the worst-case renderer
fixture`: `canvas text: 318 drawn, 0 never inside the canvas (0 draws crossed an edge),
0 ellipsized (--strict-text-bounds)` — 27 → 318 drawn runs. Both gates were driven negative
locally: slicing the note to 60 chars in the page fails with `a commander remark was SHORTENED at
1280x720 (4 of 4 rows)`, and removing the wrap fails with `a commander remark left its reserved
band at 1280x720: row [308,533,1084,553] outside the feed band [809,1084]`. Four new static
assertions in `tests/test_gen_viewer.nim` keep the fixture from being hollowed out again (it emits
`k: 'plan'`, its cap is `MaxNoteRunes`, it asserts full length, and its `ci.yml` step carries
`--strict-text-bounds` and no `continue-on-error`).
**Checklist item 15, last bullet.**

## N1 — a plan `note` could not reach the replay or the feed — **fixed** `40af89c`

This is B2's root cause and was fixed first, as the brief suggested. Two gaps, not one:

* `planJson` / `planFromJson` — the load-bearing plan **input** record — did not carry `note`, so
  on playback `sim.plan[seat].note` was always `""`;
* the `plan` frame event was recorded by `server.writePlanRecords` immediately **before**
  `stepTurn`, and `stepTurn`'s first statement is `frameEvents = newJArray()`. So the live path
  threw the event away too (the review's "the live `/global` path does show it" is not right), and
  playback never recorded one at all — `applyRecordedPlans` has no call site to record from.

`planJson` now writes `truncateRunes(note, MaxNoteRunes)`, `planFromJson` reads it back through
`sanitizeNote`, and `stepTurn` emits the `plan` event for every plan installed for the turn it is
about to step — one code path feeding the live feed and a replay's feed, which is why the fixture
can now drive the page the way the sim does. `gameHash` excludes the note (`planHashFields`), so
the hash chain is unmoved. `ReplayPlayer.planFeed` (collected, read by nothing) is gone.

**Evidence:** `tests/test_gen_replay.nim` "a full-cap note reaches the replay's plan frame event
unshortened" — the note is present in the plan **input** records, four `plan` events arrive with
`runeLen == MaxNoteRunes == 160`, and `session.sim.plan[0].note.runeLen == 160`. Green in CI
(`[OK] a full-cap note reaches the replay's plan frame event unshortened`, both debug and release).
**Checklist items 15 and 9.**

## N2 — the captain's threat override is dead code — **NEEDS-DESIGN** (no commit)

The finding is **correct** and I implemented the fix, measured it, and reverted it. The override
needs a real `source` for step 3 to continue it, so the minimal fix is four lines:

```nim
  if view.threatened():
    let home = view.largestOwned(exclude = view.generalCell)
    if home >= 0 and home != view.generalCell:
      mission = MissionState(kind: mkDefend, source: home,
        goal: view.generalCell, stepsLeft: config.defendTurns, active: true)
```

With that live, every test still passes except the head-to-head, which **inverts**:
`tests/test_gen_baselines.nim` reported `sprawlTotal 15.333 / crownTotal 16.667`, and
`nim r -d:release --path:src tools/tune_baselines.nim` reported
`shipped: divisor 4 reserve 20 scouts 2 -> margin -0.0417` (the shipped, unchanged code scores
`+0.0417`). `ci.yml`'s `Re-check the baseline tuning pick` step gates on `margin > 0`, so the fix
cannot ship without retuning — and every knob the 36-row grid can move is stated literally in the
text this game ships to its players (`docs/RULES.md`, `docs/COMMANDING.md` and the manifest's
embedded pages: crown "reserve 20 … scouts 2", sprawl "expands while land is under a quarter of
the board"). Under the documented shape the best row is `5 / 10 / 2`; adopting it means changing
the published rules text and deviating from the design note's own baseline description, and it
changes the captain, so it also needs a `GameVersion` bump.

So the choice is a design one — accept `crown` ahead of `sprawl`, or re-document the baselines —
and I did not make it. **I did not weaken the head-to-head test to let the fix through.** Note the
system prompt makes the same promise to models (`directives.nim:83-85`, "the captain comes home
for six turns. You do not have to ask for that"); I left that sentence in place rather than
quietly deleting a documented feature. No checklist item is falsified: item 7's "tuned with a grid
harness, not guessed" holds either way.

## N3 — `heldRegistrations` dead — **fixed** `0c9689a`

Declared, initialised, never written or read. The starter holds a registration that arrives from a
socket with no slot yet; here the slot is bound at the websocket upgrade from the token
(`server.nim:445-448`), so a player registration always arrives with a known slot and a text
message from a socket with no slot is a viewer's, which `slot < 0` already drops. The scar is
structurally unreachable, so the field was dead weight rather than a guard: removed.

## N4 — a mid-episode drop never reached the engine — **fixed** `9d21c5f`

`connected` was computed once, before the loop, so `fcDisconnected` was reachable only for a seat
whose socket was already gone at kickoff; the `CloseEvent` handler cleared the socket and no
engine state saw it. The loop now refreshes each LLM seat's flag from `shared.playerSockets` under
the state lock at the top of **every** directive turn, through a new `setSeatConnected` that
touches nothing else. New test: `a mid-episode drop is applied by setSeatConnected alone` —
`psLlm` → `psFallback`/`fcDisconnected` with `sprawlPlan` → `psLlm` again on reconnect.

## N5 — the coworld-CLI manifest step failed and was `continue-on-error` — **fixed** `85a3d5a`

The step `pip install`ed `coworld==0.1.42` from inside an already-running `python3` heredoc and
then imported it; the interpreter had resolved its search path before the install, so the import
raised `ModuleNotFoundError` and the shrug kept the job green over a validator that had never seen
the manifest. It now installs the CLI the way `coworld-release.yml` does —
`astral-sh/setup-uv@v6` + `uv run --no-project --python 3.12 --with "coworld[auth]==0.1.43"` — and
calls the pair `coworld build` itself calls: `coworld.bundle._load_template_manifest`, which
injects `game.version` and the compose image placeholder and then runs `validate_upload_manifest`.
That second detail matters: validating the **bare template**, as the old step did, fails with
`game.version: Field required`, so a "fixed" step that only fixed the install would have gone red.
`continue-on-error` is gone.

**Evidence:** run 33151358030, job `test`, step `The manifest loads under the installed coworld
CLI`: `manifest OK under the installed coworld CLI: gen-generals-io`, step conclusion success with
no `continue-on-error` in the workflow. **Checklist item 10.**

## N6 — a crown capture updates neither `tilesTaken` nor `tilesLost` — **DISPUTED** (no commit)

The observation is accurate; that it is a defect is not established. The note contradicts itself:
§Turn structure 3.f states the general rule, and 3.e.1–4 — the crown-capture sub-order, which is
the branch in question — enumerates only `landInherited` / `armyInherited`. The code follows 3.e,
is symmetric on both sides of the capture, and `gameHash` mixes both counters identically on
record and on playback, so determinism and the results document are unaffected; no scoring rule
reads either counter (`scoring.nim:22-39`). Changing it would move the hash chain for every future
replay and require a `GameVersion` bump to make two counters nobody scores on describe an
inherited estate. Left as-is, recorded here for the judge.

## N7 — `known_cities` / `fog.frontier` ordered by Manhattan distance — **fixed** `b0b8d93`

The note asks for "nearest first by BFS distance"; with mountains on the board the two orders
differ. Both lists now sort on `view.shortestPaths(...).dist` — the same breadth-first proc the
captain routes with — from the crown for the cities and from the largest stack for the frontier.
Prompt-side only: neither list is mixed into `gameHash` and the captain does not read them.
**Evidence:** new test `known_cities and the frontier are ordered by BFS distance`, which I
confirmed **fails** against the old Manhattan comparator (five `Check failed:
fogPaths.dist[cell] >= last`) and passes after.

## N8 — a remembered neutral city reports the config garrison — **NEEDS-DESIGN** (no commit)

Accurate, and the note conflicts with itself: §The captain step 5 says "a remembered city's army
is its last-seen value", while the observation contract says a remembered cell's `army` is `null`
— and `Memory` (`vision.nim:34-38`) stores no armies at all, so the last-seen value is not
recoverable. Making it recoverable means adding an army plane to the per-seat memory, which is
mixed into `gameHash` through `memoryDigest()` **and** read by the captain, so it changes every
future re-derivation and needs a `GameVersion` bump plus a decision about which of the note's two
rules wins. Not a change to make silently in a fix round.

## N9 — `sprawl`'s attack target was the lowest-index visible enemy cell — **fixed** `c219a42`

Now the nearest such cell measured from the seat's own crown, ties by cell index, so the plan
stays a pure function of the fogged view. No `GameVersion` bump: the captain and the resolution
rules are untouched, so a recorded plan still re-derives the same board — only which plan the
baseline emits changed. The head-to-head was re-run and still satisfies the objective (sprawl
ahead by `0.0208`, was `0.0417`), and `tools/ci/baseline_tuning.json` was regenerated with
`tools/tune_baselines.nim --write` (36 rows × 8 seeds × 4 rotations, ~2m50s) so the recorded grid
describes the code that ships. CI: `OK: the shipped defaults are tools/ci/baseline_tuning.json's
pick and sprawl is ahead by 0.020833333333333315`.

## N10 — two of the four 360 px legibility rules are not implemented — **NEEDS-DESIGN**, rule 1 partly **DISPUTED**

* Rule 1's *invariant* — a numeral never overflows its cell — holds by construction, not by
  scaling: `digitW = 9`, four digits = 36 px inside a 40 px cell, centred, so no draw can land at a
  negative coordinate (this is also what the reviewer verified for checklist item 15). What is
  missing is the ≥ 10 000 case, which draws **nothing** instead of a 0.55×-scaled numeral.
* Rule 2 (`.tiny` → numerals only on `army >= 5`, plus every city and crown) cannot be implemented
  where the numerals are: they are pre-baked digit **sprites** composed into the board layer by the
  wasm module, and `.tiny` is a client-side CSS state (`relayout()` at `boardW <= 620`) that the
  renderer is never told about. Implementing it means adding a density signal to the viewer
  message channel and re-baking per density — a viewer design change, not a fix.

Checklist item 11 (the item that names 360 px) is satisfied independently and is asserted by
`tests/test_gen_viewer.nim:133-137`. Recorded, not changed.

## N11 — the 4096 reply cap was applied in runes — **fixed** `6960a53`

`truncateRunes(body, MaxReplyBytes)` let a reply of four-byte runes through at up to 16 KB. New
`truncateBytes` cuts at the byte cap and walks back over UTF-8 continuation bytes, so the read
stays inside 4096 **bytes** and is still strict UTF-8 — the cut can never land inside a rune, so
checklist item 9's rune-safety is kept. New test drives 12 KB of crowns (U+1F451) through it:
`len <= 4096`, `len > 4092`, `validateUtf8() == -1`.

## N12 — the general's placement formula differs from the note's expression — **DISPUTED** (no commit)

The note contradicts itself in the same sentence: `1 + rand(qw - 3)` yields `1..5` on an 8×5
quadrant, while its own parenthetical says `gx ∈ 1..6`. The code (`1 + rand(max(1, qw - 2))`)
produces the parenthetical's range and the invariant the note actually asserts — off the edge,
mirrored, one army — which `tests/test_gen_board.nim:36-56` sweeps (now over 10 000 seeds, N13).
Changing the formula to the note's expression would narrow the placement range and move every
board this game has ever generated. No change.

## N13 — board tests swept fewer seeds than the note claims — **fixed** `2a0b742`

All four generator sweeps now use `BoardSeeds = 10_000` (symmetry over both board sizes, counts,
generals, connectivity). Runtime measured locally: 28 s debug, 8 s release for the whole file.

## N14 — the determinism test compared final state, not the stream — **fixed** `1ffbc03`

`streamOf` now records the `gameHash` **and** the board bytes (army, owner, kind) after every turn
plus the results document, and the test compares the whole streams (240+ frames) and reports the
first divergent turn. The no-op `for turn in 0 ..< 1: discard` and the one-element hash sequences
are gone. (The frame-by-frame *replay* property remains `tests/test_gen_replay.nim`'s, which is
what checklist item 2 needs.)

## N15 — one assertion in the reply-cap test was a tautology — **fixed** `c0f02ac`

`check (ok or not ok)` replaced by what actually happens: the cut lands inside the note, the object
never closes, so the parse **fails** and the seat keeps its previous plan (the caller retries once,
then falls back) — plus the complementary case the note's "capped then parsed" describes: a small
object followed by 9 KB of prose still parses into `intent: scout, scouts: 3`.

## N16 — the rotated-priority test asserted a different index than the note — **fixed** `f20f62f`

The existing test keeps its (correct) assertion under a title that says what it checks: "with all
four contesting, the survivor is the THIRD mover, (t + 2) mod 4". A new test makes the note's
literal claim directly — two seats push one empty cell with equal force, so the survivor is
whoever had priority: `turn mod 4`, walking with the turn number.

## N17 — `"picked"` is the shipped default, not the sweep's argmax — **fixed** `e8be315`

Fixed by making the record honest rather than by changing how the game plays: `--write` now also
computes and records `best_overall` and `best_with_documented_shape` from the same 36-row grid,
plus a `picked_is` line stating that the shipped values are the ones the rules text states to a
reader, swept and kept because they satisfy the objective, not because they maximise it. With the
current code the pick scores `0.0208` and the best shaped row (`5 / 10 / 2`) scores `0.1042` — both
now in the file. Adopting the maximiser would contradict `docs/RULES.md`, `docs/COMMANDING.md` and
the manifest's embedded pages (see N2 for the same constraint), so the pick is unchanged and
`--check` still gates shipped == pick and margin > 0.

## N18 — `config.nims` adds one line beyond identifier renames — **fixed (comment)** `3b3159b`

The line is required and is now explained where it lives: `rig_art.nim` opens
`client/art/walls/wall_{h,v}.jpg` for the board's wall and city-keep textures, those live outside
`data/`, and under emscripten a file that is not preloaded into MEMFS cannot be opened at all.
No behaviour change.

## N19 — the page requested four assets the repo does not ship — **fixed** `d43fbe5`

The whole eye-level cog-art block is inherited dead code — it exists for the removed first-person
PiP's billboards (`drawFpvEntity`), and nothing else in the page reads `COG_ART`, `cogArtFor`,
`COG_TRIM` or `cogScratch`. `tools/build_broadcast_page.py` now cuts it with the rest of the PiP,
keeping `COG_BASE` and its comment (the locker-room curtain resolves its art through it), and the
page is regenerated. **Evidence:** driving the shipped page in headless chromium, the server log
went from four 404s (`soldier_{red,blue,green,yellow}_front_gun.png`) to **zero 404s and zero page
errors**, and the renderer fixture still reports 318 runs / 0 never inside.

## N20 — the forbidden-vocabulary list is narrower than the note's — **DISPUTED** (no commit)

The narrowing is the only form of the check that can be true, for the reason the review itself
records: the bare words survive **only** as inherited identifiers, never as spectator text
(`@keyframes flagflip`, `.feed-row.flagkill`, `#killfeed` — which the note's "Kept" list keeps —
and `flags:` / `defineLayer(…, flags)` in the byte-identical `broadcast_core.js`). Asserting bare
`flag` or `kill` would fail on the starter's own bytes, which checklist item 14 requires to stay
byte-identical. Every re-mapped string the note enumerates is still asserted present exactly once
(`test_gen_endcard_labels.nim:72-87`). No change.

## N21 — the replay's config JSON omits `tokens` and `slots` — **DISPUTED** (no commit)

`tokens` are per-seat secrets and a replay is a public artifact; `replay_runtime.simFromReplay`
clears them anyway (`:42`), and `slots` is the identity map (`writeJoin` records
`"slot": seat`), so nothing is unrecoverable. Writing seat tokens into a downloadable replay to
match a table in the note is not a change worth making. No checklist item touches it.

## N22 — seed randomisation happens after `config.update` — **fixed (comment)** `1292c7f`

The code order is the only one that can read the injected pin, and every seed-derived draw (the
board, in `initSim`) happens later inside `runGameServer`, so the behaviour is right and the
docstring was wrong. The docstring now describes what the entrypoint does and why.

## N23 — the system prompt hard-coded the `ffa` clock — **fixed** `1644f9d`

The growth beat, the turn limit, the directive period and the neutral city garrison are now
substituted from the same config the sim runs, so a `blitz` seat is no longer told "turn 240" and
"every 25 turns" while its observation JSON reports 160 and 15. New test drives an ffa and a blitz
config and checks that no substitution token survives into what a model reads.

## N24 — speed chip `0.5` genuinely unavailable — **no action**

The finding records the builder's documented deviation 6 as *verified*, not as a defect: a `0.5`
chip would render a control that sends no command, because `client/chrome_common.js:437` is
byte-identical to the starter's and has no key for it. Nothing to fix.

## N25 — the player's receive loop was an unbounded blocking read — **fixed** `8495474`

`socket.receiveMessage()` was the one wait with no bound of its own. It now carries a 5 s timeout
— whisky applies the timeout to the frame **header** read only (`receiveFrame`: `ws.socket.recv(2,
timeout)`), so it can never cut a frame in half and returns `none` purely as an idle tick — and
the loop leaves after 240 s of total silence, well above the longest legitimate quiet (the 100 s
lobby join wait plus its registration grace) and well under the 660 s engine stop. A close frame
still raises and still takes the existing redial path. **Checklist item 5.**

---

## NOTED (not fixed) — found while working the findings above, not findings of this round

1. **`seFallback` events never reach a frame either.** `server.writePlanRecords` records them
   immediately before `stepTurn`, which clears `frameEvents` — the same mechanism N1 fixed for
   plans. Nothing is lost on screen today (the game block has no `fallback` case, and the tier-2
   `sim.events` buffer and the replay's `fallback` chat records are unaffected), so I left it
   rather than widening N1's commit.
2. **The player's registration re-sends do not actually repeat.** `RegisterRepeats = 10` /
   `RegisterSpacingMs = 1000` only fire after a **received** message, and before kickoff the
   server sends a seat nothing but the welcome — so one or two registrations go out, not ten. N25's
   bounded read now gives the loop a 5 s idle tick that could drive them properly; I did not do it,
   because it is not a finding this round.
3. **The banner chip overflows the stage at 360 px.** The crown-capture banner
   ("RED TAKES GREEN'S CROWN — inherits 24 tiles and 118 armies") is a `nowrap` chip in the
   inherited banner lane; in the fixture's 360 px pass it is clipped at both stage edges. It is not
   gated by `--strict-text-bounds` (the chip stays inside the canvas) and the text is engine-made,
   not model-made, so it is outside item 15's LLM-text bullet — but it is the same shape of defect
   as B2's feed row and would want the same treatment (wrap, or a reserved two-line lane).
