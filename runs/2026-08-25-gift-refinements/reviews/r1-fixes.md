# r1 fixes — gift-refinements

Repo: `Metta-AI/cogame-gift-refinements`, branch `main`.
Reviewed sha: `45ef01a6d94fda1843af65137d9cfd2b71969988`.
Head after fixes: **`30a0405ff5305270febc8552019635272b5092c2`**.
CI: **run `32921048633`** — success (`ci.yml`, `main`, head `30a0405`), all four jobs
(`manifest-loads`, `test`, `docker-smoke`, `wasm-viewer`).
Checklist item numbers below are `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.

One commit per finding, in finding order. Every finding F1–F13 has a commit; nothing is disputed
and nothing was deferred for design. One advisory (A1) was fixed because it was a one-comment,
zero-behaviour change; the other eight advisories are left alone and listed at the bottom.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 | fixed | `3710c15` | `src/gift_refinements/{sim,server}.nim`, `tests/test_replay.nim` |
| F2 | fixed | `6a14288` | `src/gift_refinements/sim.nim`, `tests/test_replay.nim` |
| F3 | fixed | `50438bd` | `client/{game_block.html,replay_broadcast.html}`, `tests/test_broadcast.nim` |
| F4 | fixed | `cf9e335` | `client/{game_block.html,replay_broadcast.html}`, `tests/test_broadcast.nim` |
| F5 | fixed | `5ea8ac2` | `client/{game_block.html,replay_broadcast.html}`, `tools/ci/{renderer_fixture.html,dom_text_smoke.mjs}` |
| F6 | fixed (documented + pinned; no rule change — see below) | `4d959b0` | `src/gift_refinements/kernel.nim`, `tests/test_sim.nim` |
| F7 | fixed | `d28b1e9` | `README.md` |
| F8 | fixed (documented as a delta; renderer left byte-identical) | `c831319` | `README.md` |
| F9 | fixed | `32db0ee` | `tests/test_baseline.nim` |
| F10 | fixed | `54d220d` | `tests/test_broadcast.nim` |
| F11 | fixed | `2c00c66` | `tools/ci/renderer_fixture.html`, `src/gift_refinements/global.nim`, `tests/test_broadcast.nim` |
| F12 | fixed (documented as a delta; derivation unchanged) | `a63b6c1` | `scripts/derive_broadcast_page.py`, `README.md` |
| F13 | fixed | `b3d71fa` | `src/gift_refinements/server.nim` |
| A1 (advisory) | fixed | `30a0405` | `src/gift_refinements/decide.nim` |

---

## F1 — early-settle `autobank` rows landed one tick past the last frame → `3710c15`

**Was:** `step()` records the frame and *then* advances `sim.tick`, so the deadline break left
`sim.tick == lastFrameTick + 1`; `server.nim` then called `autobankAll()`, and `bank()` stamped
every closing row with `sim.tick`. Those rows sat at a tick `parseReplay`'s `byTick` index hands to
a playhead that can never reach it — no burst, no feed row, `BroadcastTracker.resync(..,
maxTick)` never folded them — while `results.scores` counted the tokens. The follow-up
`sim.frames[^1].tick = max(0, sim.tick - 1)` was a no-op.

**Is:** `bank(slot, autobanked, at)` takes the tick it stamps; `autobankAll(at = -1)` passes it
through; a new `sim.settleEarly()` (`sim.nim`) stamps `frames[^1].tick` and is what `server.nim`
now calls, replacing the open-coded settle and its no-op frame rewrite.

**Evidence:** new test block `earlySettleStaysInsideTheRecordedFrames` in `tests/test_replay.nim`
plays a three-round deadline settle with `consume: never`, then asserts every event tick is inside
`0 .. ticksPlayed`, that `eventsAt(maxTick)` is non-empty, and that `results.scores` totals exactly
the tokens the settle banked. CI `test` job: `✓ a deadline settle records its autobank inside
0..ticksPlayed`. This also settles the review's "could not determine" #1.

**Checklist:** item 2 (replay re-derivation — an event outside the recorded frames cannot be
re-derived by the viewer), item 1 (test added, none loosened).

## F2 — a forfeit wrote `frames: []`, which this repo's own parser rejects → `6a14288`

**Was:** with `seated.len == 0` the round loop never ran, `captureFrame` never ran, and
`replayBytes` wrote `"frames": []` — exactly the input `parseReplay` raises `GiftError "replay has
no frames"` on, which `gr_load_replay` surfaces as `data-replay-error`. The note asks for "results
+ replay are still written" on that path.

**Is:** `finish()` records the opening position when nothing else did (`if sim.frames.len == 0:
sim.captureFrame()`), so every legal `results.reason` — including `forfeit`, and a deadline hit
before the first tick — writes a parseable, drawable replay. One frame, tick 0.

**Evidence:** new test block `aForfeitReplayIsStillPlayable` finishes an untouched sim as
`erForfeit` and round-trips the bytes through the **shipped** `parseReplay` (which raises on an
empty frame list), asserting one frame, `maxTick == 0`, `reason == "forfeit"` and a non-empty tick
index at 0. CI `test` job: `✓ a forfeit writes a replay the shipped parser and viewer accept`.

**Checklist:** item 13 (viewer executes — the hosted page for a forfeited episode no longer sets
`data-replay-error` instead of drawing), item 1.

## F3 — `?spoilers=0` did not hold this block's beat markers back → `50438bd`

**Was:** `chrome_common.js`'s `applySpoilers` iterates its own private `markerEls`, filled only by
`renderBeatMarkers`. This game block builds its own labelled, clickable `<button class="beat-marker">`
elements and appends them straight to `#scrub`, so under `?spoilers=0` every `round`, `firstgift`,
`super`, `defect` and `gameover` notch — the whole story, including the defections and the
game-over — was visible on the first HUD frame.

**Is:** the block keeps the buttons it placed (`giftMarkers`) and gates them itself against the
chrome's own mode, read through `GR_CTX.C.getSpoilers()`, in the **same synchronous pass** that
builds them (`applyGiftSpoilers(s)` at the end of `giftFrame`), so a beat ahead of the playhead
never flashes. A `MutationObserver` on `#btn-spoilers`'s class re-gates the moment the chrome's
`setSpoilers` fires, so the button and the `o` key work while paused. `chrome_common.js` is
untouched (still md5 `80ea4eb1…`, byte-identical to `/workspace/starters/coworld-ctf`), and
`client/replay_broadcast.html` was regenerated by `scripts/derive_broadcast_page.py`.

**Evidence:** new test block `spoilersHoldThisBlocksBeatsBack` in `tests/test_broadcast.nim` pins
the gate, its registration, its per-frame application and the class watcher. CI `test` job: `✓
?spoilers=0 holds this block's beat markers back as well`. Re-verified at head:
`python3 scripts/derive_broadcast_page.py /workspace/starters/coworld-ctf /tmp/derived.html`
reproduces `client/replay_broadcast.html` byte for byte (`cmp` clean, 3057 lines).

**Checklist:** item 14 (chrome is the starter's — the transport rules the note states hold as
stated, with `chrome_common.js` still unedited).

## F4 — beat markers were re-appended after a backward seek → `cf9e335`

**Was:** `giftFrame` cleared the `placedBeats` dedup map on every jumped frame, but nothing anywhere
removes a `.beat-marker` node from `#scrub`. After a backward scrub, playback re-crossing a live
`round` or `defect` tick appended a second, exactly superimposed button — duplicate click targets
and unbounded DOM growth.

**Is:** the map is permanent (`if (jumped) placedBeats = {};` removed, with the reasoning recorded at
the site), which makes building a beat idempotent in `(tick, kind, seat)`. Hiding beats ahead of the
playhead after a seek is the F3 spoiler gate's job, not a rebuild's.

**Evidence:** new test block `beatMarkersAreBuiltOnce` asserts the map is never reset (searching the
block with only its declaration removed) and that the dedup guard is still in `buildGiftBeats`. CI
`test` job: `✓ beat markers are built once per tick|kind|seat and never rebuilt`.

**Checklist:** item 14(d) (scrubber beats are labelled buttons that seek to their tick — one per
emitted kind, not N).

## F5 — `notes` reached the replay and was drawn nowhere → `5ea8ac2`

**Was:** `notes` is captured, rune-truncated at 320, recorded on the `order` row and asserted by
`tests/test_replay.nim`, but no viewer surface read it; the note says it is "drawn only in the feed's
expanded row" and that row did not exist. The CI fixture built a full-cap 320-rune `WORST_NOTES`,
fed it to six `order` events, and nothing rendered it — so neither `--strict-text-bounds` nor
`dom_text_smoke.mjs` measured a rune of it.

**Is:** the `order` feed row *is* that row. `say` stays the headline; when the seat wrote `notes`
the row carries the **whole** string in a `.gr-notes` block that opens on hover or click
(`role=button`, `tabindex`, `aria-expanded`, Enter/Space), wrapped under the headline
(`flex: 1 0 100%`, `white-space: normal`, `overflow-wrap: anywhere`) and shortened by nothing. Only
this kind of row takes pointer events back from the inherited display-only feed. The fixture now
opens the newest such row and self-checks the drawn string is still 320 runes and displayed;
`dom_text_smoke.mjs` measures `.feed-row.gr-open .gr-notes` as its own group and fails if any
`.gr-notes` is not full-length.

**Evidence:** CI `wasm-viewer` job, DOM text smoke, all 13 viewports:
`ok 360x640: feed rows=4 expanded notes=1 trust rows=3 roster chips=6 plate names=2` (… through
`1600x900`). Renderer fixture step still reports `canvas text: 84 drawn, 0 never inside the canvas
(0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`.

**Checklist:** item 15 (every drawn string fits its frame — the LLM-authored string that CI can
never produce is now drawn, at full cap, and measured at 360 px; the reserved-band rule is
satisfied by a row that wraps rather than one sized by eye).

## F6 — `giftmiss` cannot occur in kernel-driven play → `4d959b0`

**Disposition: fixed as a documentation + test gap, deliberately not as a behaviour change.** The
finding is correct as an observation and the reviewer says so: "The rule itself is implemented
correctly." The kernel only schedules a beam when `board.hittable(...)` holds — which is the note's
own kernel rule 2, *"`target` is currently hittable"* — and `hittable`/`traceBeam` are the same pair
over the same `sim.occupied` with only the (motionless) consume between them. Making the kernel fire
at an unhittable target to make the event reachable would spend a beam on empty air and contradict
the note, so the code is unchanged.

**Is:** `kernel.beamAction` records the consequence at the site that causes it, and a new test block
`theKernelNeverSchedulesABeamThatMisses` plays a whole kernel-driven episode on **all four
variants** and asserts gifts > 0 and `giftmiss == 0` — pinning that the direct-`step` unit test is
the only way to reach the rule, so a future kernel change that starts missing is a red test rather
than a silent behaviour drift. Also listed as README delta 7.

**Evidence:** CI `test` job: `✓ a kernel-scheduled beam always connects: zero giftmiss in real play`.

**Checklist:** item 7 (the scripted baseline's actions are inside their legal bounds — this asserts a
sharper form of it), item 1.

## F7 — README's delta section said "two" and listed four → `d28b1e9`

**Was:** the section opened "everywhere except the two places below" and then listed four, while four
further readings that change behaviour lived only in code comments (`gaveYouLastRound` counted in
tokens; per-action rather than shared cooldown gating; the `round` event/beat on the last tick of the
round; gift-before-spill emission order).

**Is:** all of them are enumerated with the `file:line` that carries the reasoning, and the headline
count matches the contents. No code change — the reviewer checked each of the four against the note
and found none contradicts its mechanics; that verdict is now the README's, in the open.

**Checklist:** none directly (documentation accuracy); it removes the "delta documented only in a
comment" hazard a judge would otherwise have to rediscover per file.

## F8 — `client/broadcast_core.js` is byte-identical where the note says it is forked → `c831319`

**Disposition: fixed by documenting the delta; the starter renderer is deliberately left
untouched.** Every draw the note's provenance table assigns to a forked `broadcast_core.js` exists —
in `src/gift_refinements/global.nim` (baked deck `:162-213`; pads, tokens, cogs, alias plates,
inventory badges, beams, bursts, puffs `:267-449`), emitted as Sprite v1 into the starter's generic
sprite renderer. The alternative "fix" is to edit a starter file that needs no edit, which is worse
provenance under checklist item 14, so the code stands and README delta 8 states the structural
delta and its one side effect: no `fillText` runs on the replay path, so `--strict-text-bounds` on
the bundle measures zero strings and the renderer fixture is what gates drawn text (F11).

**Evidence at head:** `md5sum client/broadcast_core.js` = `677fe90f2be107b810c24aef02b936a3` =
`/workspace/starters/coworld-ctf/client/broadcast_core.js`; `Dockerfile.replay-viewer` copies it into
the bundle unchanged.

**Checklist:** item 14 (chrome provenance — the byte-identical direction is the one the checklist
wants; the deviation is now stated rather than implied).

## F9 — baseline latency bound was 50 ms where the note says 1 ms → `32db0ee`

**Was:** `check(slowest <= 50, …)` in whole **milliseconds** — 50× the note's item-4 bound, at a
resolution that floors any real figure to 0, and the test printed nothing.

**Is:** every round of orders is timed in **microseconds** and collected across all 1728 of them
(4 variants × 12 seeds × 3 rooms × 12 rounds). The **median** and the **p99** are held to the note's
1 ms (`<= 1000 us`); the single worst round keeps a wide outlier guard (50 ms) because a scheduler
blip on a shared runner is a property of the runner, not of the baseline; and all three figures are
echoed. Strictly tighter than what it replaced — the removed assertion is the only assertion deleted
in this round and it was replaced by two stronger ones plus a printed measurement.

**Evidence:** CI `test` job of the final run (32921048633) prints
`baseline orders per round over 1728 rounds: median 58 us, p99 81 us, worst 279 us (scarce seed 1
recip round 1)`; the previous run (32911171662) printed `median 59 us, p99 84 us, worst 141 us`.
That settles the review's "could not determine" #2: the baselines are ~17× under the note's bound at
the median and p99, and even the worst single round on a shared runner is 3.5× under it.

**Checklist:** item 5 (degrade-never-hang / timing budget), item 1 (a test tightened, not loosened).

## F10 — `check(… or true, "")` in `test_broadcast.nim` → `54d220d`

**Was:** a constant-true condition with an empty message — a dead assertion in the file that is
otherwise the provenance gate.

**Is:** the property it meant to state (the engine emits the `window.CTF_WIRE` global
`chrome_common.js` reads, which is why that file can ship byte-for-byte) is asserted on
`WireConstantsJs` itself — the const both the served page and `tools/gen_wire_constants.nim` render,
and the same string `Dockerfile.replay-viewer:44` greps for in the generated `wire_constants.js` —
with a message that names what it found instead.

**Evidence:** CI `test` job: `✓ chrome_common.js is the starter's file, reading window.CTF_WIRE`; the
`wasm-viewer` build step still runs `grep -q '^window.CTF_WIRE={' replay-viewer/dist/wire_constants.js`.

**Checklist:** item 1 (no dead/loosened test), item 14 (the byte-identical `chrome_common.js` claim is
now gated at both ends).

## F11 — the fixture's header overstated what it loads; its canvas half is an unpinned mirror → `2c00c66`

**Was:** the fixture claimed it rendered "through the REAL chrome — `client/chrome_common.js` and the
real appended game block". Only the second half was true, and the canvas geometry was a hand-written
mirror of `global.nim`'s anchors that nothing enforced.

**Is:** the header separates **REAL** (the fetched-and-injected `client/game_block.html` — every
string `dom_text_smoke.mjs` measures is drawn by shipped code), **STAND-IN** (the plate machinery and
minimal CSS, because `chrome_common.js` is not loaded) and **MIRROR** (the canvas, because the board
is blitted as sprites and no `fillText` runs on the replay path — which is exactly why the bundle's
`--strict-text-bounds` reports `total: 0`). The mirrored line is now **pinned**: a new test block
`theFixtureMirrorsTheEnginesBoardAnchors` asserts the fixture's `var CELL/COLS/ROWS/COG` line, its six
spawn cells and its 13 px caption font against `CellPx`, `Cols`, `Rows`, `CogPx` and `SpawnCells`
(`CogPx` exported for this), so an anchor that drifts in `global.nim` fails a test instead of leaving
the flag measuring the wrong geometry. That settles the review's "could not determine" #4.

**Evidence:** CI `test` job: `✓ the renderer fixture's canvas mirror is pinned to the engine anchors`.
CI `wasm-viewer`: bundle step `canvas text: 0 drawn, …` (honestly `total: 0`, as documented), fixture
step `canvas text: 84 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`.

**Checklist:** item 15 (the worst-case renderer fixture is the gate that carries drawn-text coverage,
and it now cannot silently drift from the engine).

## F12 — the derivation makes a fourth class of edit inside the starter's script → `a63b6c1`

**Disposition: fixed by naming it as a delta; the derivation is unchanged.** The fourth class (the
`PaintballChrome`/`PB_CTX` → `GiftRefinementsChrome`/`GR_CTX` rename and the deleted `PB_MODE` latch
with its four plate/end-card branches) follows from a removal the note itself requires: cutting the
starter's own appended paintball block removes the only thing that ever set `regime`, so the latch
could only survive as a flag that is false forever guarding dead branches, and a page that asks
`window.PaintballChrome` for this game's chrome is worse provenance. Reverting it would ship dead
code, so the script's header states plainly that this is a fourth class against the note's three and
why, notes that class 2 re-letters **four** literals rather than the note's two (the `<title>` and
the locker-room caption otherwise still read "Ctf" and "paint"), and README lists it as delta 9.

**Evidence at head:** `python3 scripts/derive_broadcast_page.py /workspace/starters/coworld-ctf
/tmp/derived.html` → "wrote /tmp/derived.html: 3057 lines (cut 2315 from the starter's 4661)", and
`cmp` against `client/replay_broadcast.html` is clean — the whole claim is re-verifiable by running
the script, not asserted.

**Checklist:** item 14 (chrome provenance — the page is still the starter's, and every edit inside it
is enumerated and reproducible).

## F13 — no `state` frame at episode end → `b3d71fa`

**Was:** `state` went out at every round boundary but not at episode end; the note's §Server asks for
both.

**Is:** the shutdown sequence sends each seated slot the settled position
(`observationJson(sim.seatView(slot), sim.scene())`) immediately before `final`, in the order the
note lists. No consequence for the shipped player (`of "state": discard`); a seat that keeps its own
book of the match no longer has to infer the last round from `final.scores`.

**Evidence:** `docker-smoke` in the final run still ends `smoke OK: seats=6 results=577B
replay=81031B reason=complete`, "all 6 player containers exited 0" — the extra frame does not
perturb the shutdown handshake.

**Checklist:** item 5 (the shutdown sequence stays bounded and the episode still settles inside the
budget).

---

## A1 (advisory) — the rate floor's comment described the wrong call order → `30a0405`

Fixed because it is a comment-only, zero-behaviour change. `decide.turn()` sleeps to the
`minTurnSeconds` floor at its **top**, and `server.nim:396` calls `turn()` **before** the round's
ticks — not after, as the comment said. The comment now states the real order and why the wall-clock
behaviour is nonetheless correct: the floor is measured between batch **starts**, so the ticks of the
round just played count against it and a round costs `max(minTurnSeconds, batch)`, never their sum.

## NOTED (not fixed)

The remaining advisories A2–A9 are left alone: the reviewer records each as consistent with the note,
none falsifies a checklist item, and each would be a behaviour or scope change rather than a fix.

- **A2** — `sim_config.validate()` re-checks most, not all, of the schema's bounds while its docstring
  says "every bound". All shipped variants are inside every bound and `tests/test_manifest.nim:202-231`
  pins every default against the engine. Adding the missing range checks is a real improvement and a
  behaviour change to a validator no shipped input trips; out of scope for a fix round.
- **A3** — `num_agents < 6` is schema-legal while the sim is hard-wired to `SeatCount = 6`. No shipped
  variant or the cert fixture moves it (all declare 6, gated by `docker_smoke.sh`'s four seat-count
  invariants) and the note says no variant changes it.
- **A4** — `collect` at cap emits `spill` and `continue`s before `collectCd` is set, so a capped cog
  retries every tick. The note specifies only the spill; changing the cooldown changes the sim.
- **A5** — the kernel builds one Dijkstra field per candidate target per tick, more than the note's
  arithmetic assumed. Release-mode CI bears out that it is cheap (576 episodes in ~38 s).
- **A6** — `autobank` emits no `defect` rows; the note scopes `defect` to the first `consume`.
- **A7** — `dom_text_smoke.mjs` measures the fixture rather than the real page; the fixture injects the
  real `client/game_block.html`, so the strings and CSS measured are the shipped ones. All 13
  viewports pass.
- **A8** — `orders.nim` accepts a numeric string for `gift`, one notch more tolerant than the note's
  table; a non-numeric string still raises (`tests/test_llm.nim:58`).
- **A9** — the feed is cleared on every jump (the starter's own behaviour), so `viewer_smoke.mjs`'s
  `feed_lines: 0` after seeking is expected, not a broken feed.

## Test-integrity statement (checklist item 1, second half)

`git log -p 45ef01a..HEAD -- tests/` for this round contains exactly two deleted assertions, both
replaced by strictly stronger ones in the same commit:

- `32db0ee` removed `check(slowest <= 50, …)` (ms resolution, 50× the note's bound) and added
  `check(median <= 1000)` + `check(p99 <= 1000)` in **microseconds** across 1728 rounds, plus a wide
  outlier guard and a printed measurement.
- `54d220d` removed `check(… or true, "")` (constant-true, empty message) and added
  `check(WireConstantsJs.startsWith("window.CTF_WIRE={"), …)`.

Nothing else was deleted; no `skip`, `xfail` or `--skip` was added; no test file was removed. Six new
test blocks were added (`test_replay` ×2, `test_sim` ×1, `test_broadcast` ×3) and `test_baseline`
gained a distribution gate.

## Final state

- Head on `main`: `30a0405ff5305270febc8552019635272b5092c2`.
- `ci.yml` run **`32921048633`** — **success** — https://github.com/Metta-AI/cogame-gift-refinements/actions/runs/32921048633
- Previous green run at `b3d71fa` (all thirteen findings, before the A1 comment commit):
  `32911171662` — success — https://github.com/Metta-AI/cogame-gift-refinements/actions/runs/32911171662
- Push note: plain `git push` returns 401 on this repo in this sandbox; the F1–F13 commits and the A1
  commit were pushed with the repo's own `tools/push_via_api.py`, which fast-forwards the ref through
  the GitHub API. No history was rewritten — every push added a commit on top of the remote head.
