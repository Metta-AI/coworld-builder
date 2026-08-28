# r1 fixes — cogame-atari-57

Head: `c8498ce481637d6acdac33192bf688a5d9f55ee5` (`main`)
CI: https://github.com/Metta-AI/cogame-atari-57/actions/runs/33210994977 — **success**
(run id `33210994977`, `ci.yml`, `event: push`, `headSha c8498ce4…`, all three jobs `success`:
`test`, `docker-smoke`, `wasm-viewer`; every step `success`, none skipped or `continue-on-error`.)

Range fixed: `6682e8e..c8498ce` (8 commits, one per finding plus three fix-forwards).
Base was `6682e8e` "drop three dead declarations the fork left behind" — one commit past the
reviewed sha `309a9b3`; the review's line numbers still resolved (that commit touched only
`broadcast.nim`, `decide.nim` and `replays.nim` declarations).

**Push note for the coordinator:** `git push` over HTTPS is not usable from this sandbox — the
`Authorization: Basic` header built from `GH_TOKEN` comes back `401 Invalid username or token`
from `github.com` for `git-receive-pack`, while `gh api` with the same token reports
`{"admin":true,…,"push":true}` and works. The eight commits were therefore replayed onto
`refs/heads/main` one at a time through the Git Data API (blobs → tree on the parent's tree →
commit → a single non-forced ref update), preserving message and order exactly. Nothing was
squashed, rewritten or force-pushed; the local clone was then reset to `origin/main`.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `5e21d69` (+ `9a66f48`, `16f2227` fix-forward) | `client/replay_broadcast.html`, `replay-viewer/static_replay.js:216`, `replay-viewer/static_replay_worker.js:211`, `tests/test_viewer.nim:106` |
| N1 | fixed | `0feee42` (+ `c8498ce` fix-forward) | `.github/workflows/ci.yml:328-343` |
| N2 | fixed | `d93c9cb` | `client/replay_broadcast.html`, `src/lane/broadcast.nim:264-286`, `tests/test_viewer.nim:180` |
| N3 | NEEDS-DESIGN | — | `src/lane/sim.nim:346-585` |
| N4 | DECLINED | — | `src/lane/maps.nim:92-101` |
| N5 | DECLINED | — | `src/lane/baselines.nim:38-49` |
| N6 | DECLINED | — | `client/replay_broadcast.html:2652-2654` |
| N7 | fixed | `7fc9e38` | `tests/test_viewer.nim:263` |
| N8 | DECLINED | — | — |
| N9 | DECLINED | — | `tests/test_server.nim` |
| N10 | DECLINED | — | `src/lane/broadcast.nim:58-124` |
| N11 | DECLINED | — | `tools/ci/renderer_fixture.html:183-188` |
| N12 | fixed | `f86274b` | `src/lane/decide.nim:159-183` |
| N13 | DECLINED | — | `src/lane/server.nim:587-589` |
| N14 | DECLINED | — | `client/replay_broadcast.html:1763,1800` |

---

## B1 — the fixed arena still drove `core.zoomAt` / `setZoom` / `panBy` / `resetView`
**Satisfies: acceptance checklist item 14, fourth bullet** ("a game whose whole arena fits the
frame removes the panel — markup, CSS, the `core.zoomAt/setZoom/attachMinimap` wiring, and the ids
from the test list — rather than hiding it"). Category: static-viewer.

**What the code did.** The panel markup, its CSS and its ids were already gone, but the page still
drove the view from nine live call sites — `z`/`x`/`0` keys and the arrow-key pan
(`replay_broadcast.html:2381-2396`), ctrl-wheel (`:2439`), Safari `gesturechange` (`:2456`),
touch pinch (`:2511-2512`), pointer drag (`:2525`) and dblclick (`:2542`) — routed across the
Worker boundary by `static_replay.js:240-262` into `broadcast_core`'s real implementation
(`static_replay_worker.js:216-228`). On a 1400×1400 board that always fits the frame a spectator's
trackpad pinch or drag moved the arena with no visible control to bring it back: the zoom bar and
its `#zoom-read` readout had been removed, leaving only the undiscoverable `0` key and a dblclick.

Confirmed at the cited lines, and one thing the review did not catch: **the `z`/`x` handlers were
already broken.** `ZOOM_STEP` (`:2381-2382`) and `panCellBoardPx()` (`:2393`) have no declaration
anywhere in the file — they lived in the deleted panel block — so those two keys threw
`ReferenceError` inside the `keydown` listener rather than zooming.

**What it does now.** Removed, in one commit:
- the `z` / `x` / `0` bindings and the whole arrow-key pan branch (`keydown` now goes straight from
  `o` to the `1`–`9` speed keys);
- the entire zoom+pan block: `canvasPoint`, the `wheel` / `gesturestart` / `gesturechange` /
  `gestureend` handlers, the touch-pinch machinery (`pinch`, `pinchGeometry`, `beginPinch`),
  `syncTouchAction`, the `pointerdown` / `pointermove` / `pointerup` / `pointercancel` drag
  handlers and the `dblclick` refit — 135 lines;
- the `dragMoved > 4` guard in the surviving click-to-select handler, which those handlers were the
  only writers of;
- `zoomAt` / `setZoom` / `panBy` / `panByMap` / `panTo` / `resetView` / `attachMinimap` from
  `static_replay.js`'s returned core, plus `pendingMinimap` / `minimapSent` / `sendMinimap()`;
- the `view` and `minimap` message branches, `minimapSurface` and the `attachMinimap` call in
  `static_replay_worker.js`.

**Kept, deliberately:** `core.getTransform()` (the frame ingest reads the board's native size from
it at `:1622`, and the click-to-select handler inverts the letterbox transform), `core.clickMap`
(inherited select-a-sprite, not zoom/pan wiring), and `client/broadcast_core.js` **untouched** —
its zoom/pan/minimap implementation stays in the file verbatim, simply never driven, which is
exactly what the design note says at L1420-1421. The removal banner in the page now records the
wiring removal alongside the markup removal it already listed, and the three comments that
described the deleted handlers (the `#board` `touch-action` rule, the `onTransform` no-op, the
keyboard block) were rewritten to say what is true.

**Evidence.** New test `tests/test_viewer.nim:testNoZoomPanWiring` asserts (a) the page contains no
`core.zoomAt(`/`setZoom(`/`panBy(`/`panByMap(`/`panTo(`/`resetView(`/`attachMinimap(` call, (b) it
binds no `wheel`/`gesturestart`/`gesturechange`/`dblclick`/`pointerdown`/`pointermove` listener,
(c) `static_replay.js` exposes none of those entry points and posts no `view`/`minimap` message,
(d) `static_replay_worker.js` routes none of them into the core, and (e) `broadcast_core.js` still
*has* `zoomAt` and `attachMinimap`, so the fix cannot be "satisfied" by gutting the shared core.
Green in the CI run cited above (`ok  no zoom/pan wiring survives; broadcast_core keeps its own`),
and `wasm-viewer`'s `Load the bundle in a real browser` step still reports `loaded: true` with the
scrub probes moving, so removing the wiring did not break playback.

**Fix-forward (`9a66f48`, `16f2227`).** The first push went red: `testRemovedElements` greps the
page *above the appended banner* for the string `#viewpanel`, and my three new explanatory comments
named it literally. They now say "the zoom bar and the minimap" and point at the banner, which is
where the record of the edit belongs. Same class of thing in `static_replay.js`, where the comment
listing the deleted entry points ended `…/attachMinimap:` and read as a surviving property to the
new test's grep. Both are comment-only; no behaviour changed. The failure was mine and is counted
against this round (run 33207297869, `test` job, `tests/test_viewer.nim(102) testRemovedElements`).

## N1 — the viewer smoke never ran the frozen-playback check
**Satisfies: checklist item 13** (strengthens it — the item requires the browser step to run and be
green; `--soak` is what makes "green" mean *playing* rather than *loaded*). Design note L1911-1916.

**What the code did.** `ci.yml:328-332` invoked `viewer_smoke.mjs` with `--bundle … --timeout 90
--strict-text-bounds` and no `--soak`. The harness defaults `soak: 0` (`viewer_smoke.mjs:158`) and
gates the whole block on `if (loaded && args.soak > 0)` (`:535`), so the check was a no-op — the
reviewed CI log printed no `soak:` line at all. A viewer that loads, draws one frame and then dies
inside that frame's render (cogball 0.1.4) passed the gate with a full scorebug.

**What it does now.** The step passes `--soak 8` and the gate runs. Reported in CI:
`soak: 8s of playback kept advancing ("0 / 1440" -> "816 / 1440" -> "1200 / 1440")`.

**Deviation from the design note, deliberately, with the measurement.** The note pins `--soak 12`
and justifies it with "the 1440-tick fixture is 60 s long … so a 12 s soak cannot end the replay".
That premise does not hold for this bundle: `static_replay.js:106-118` advances up to **six** sim
frames per animation frame, so the fixture plays out in ≈10.2 s of wall clock, not 60 s. I shipped
`--soak 12` first (`0feee42`) and it went green twice — but only just, and for the wrong reason:

| run | soak samples |
|---|---|
| 33207297869 | `"1 / 1440" -> "1417 / 1440" -> "1441 / 1440"` |
| 33209115187 | `"0 / 1440" -> "1416 / 1440" -> "1441 / 1440"` |

The soak requires the **last** interval to move. Both runs' middle sample (at 10 s) landed ~24
ticks — about 0.2 s — before the end of the replay. A runner 3 % faster reads `1441` at both the
10 s and 12 s samples, and the job fails with `frozen: playback stopped advancing`, which would be
a false red on a perfectly healthy viewer. `c8498ce` moves it to `--soak 8` (samples at 6 s and
8 s, ≈2 s inside playback), which keeps the gate's whole point — a viewer that stops still fails
it — without the race. The measurement and both run ids are recorded in the step's comment so the
next reader does not "restore" the 12.

## N2 — `a57.bubbles` was emitted and never consumed; the board drew no speech band
**Satisfies: checklist item 15** (the "reserved band" clause — the band is now real text laid out
in a reserved strip, and the fixture exercises it at full cap) and design §Viewer Readouts 6
(L1514-1519) / §Legible at 360 px (L1576).

**What the code did.** `src/lane/broadcast.nim:264-269,300` built `a57.bubbles` on every chrome
frame and nothing read it: the key appeared only in the producer and in
`tools/ci/renderer_fixture.html:121`'s synthetic state. A stance's `say` reached a spectator only
as a `#killfeed` row. The design's board readout did not exist.

**What it does now.** The appended game block paints `#a57-bubbles`, a reserved strip across the
top of the board — `top: var(--topband)`, height `(board height) × 2 / 35`, i.e. rows `[0, 2)` of
the 35-tile board, above **both** top quadrants. It is never positioned relative to an avatar
(that is the cogchemists 2026-08-24 scar the design cites). It cannot cover play or spill: the band
clips its own overflow, and each bubble is `max-width: 32%` with `overflow: hidden; text-overflow:
ellipsis; white-space: nowrap`, so a full-cap 48-rune `say` ellipsises inside its share. Under
`#stage.tiny` the band is hidden, exactly as §Legible at 360 px specifies ("bubble text is
suppressed"). The producer now emits **at most three** — the three lanes whose `say` was set most
recently, by descending `seatSayUntil` with a stable tie-break on lane — which is the design's
"at most three at a time"; the 2.5 s life was already the sim's (`seatSayUntil > tickCount`), so a
seek lands on exactly the bubbles the recorded tick had, with no page-side timer to drift.

**Evidence.** New test `tests/test_viewer.nim:testBubbleBand` pins that the game block reads
`a57.bubbles`, that `#a57-bubbles` is the `2 / 35` strip anchored at `--topband`, that the bubble
rule clips, that `.tiny` suppresses it, and that the producer's cap of three is still there.
`tools/ci/renderer_fixture.html` already ships a bubble in its synthetic state (`:121`) and drives
the real page at 360 / 620 / 1280 px with a full-cap 48-rune `say` on all four seats: the
`Render the worst-case text fixture` step reports `canvas text: 112 drawn, 0 never inside the
canvas (0 draws crossed an edge), 0 ellipsized` and no `clipped run:` failure, so the new text is
laid out inside its box at every width.

## N12 — the inter-batch floor was not stop-interruptible
**Satisfies: checklist item 5** (degrade-never-hang — "the episode settles and scores inside 60 %
of `episodeTimeoutSeconds`"). Design note L665-666 calls the floor "a bounded, stop-interruptible
`sleep`". Category: timeout.

**What the code did.** `decide.nim:165-171` was one `os.sleep` bounded by `turnSpacingMs`
(12 000 ms in every shipped variant) with nothing able to break it. `engine.turn` runs
synchronously inside the tick loop (`server.nim:770-771`) and the engine's wall-clock stop is
checked at the **top** of that loop (`:587`), so the stop could not fire while a turn was in
flight: worst case the 660 s stop fired `turnSpacingMs + turnBudgetMs` = 28 s late.

**What it does now.** The floor sleeps in 100 ms slices, bounded as before by
`lastBatchStart + turnSpacingMs`, and abandons the wait once `turnStart + (wallClockBudgetSeconds −
elapsedSeconds)` passes. Worst-case overshoot drops from 28 s to `turnBudgetMs` = 16 s, so the
settle-and-score window moves from ≈690 s to ≈702 s against the checklist's 720 s.

**Honest scope note.** This is a backstop, not a live path: the budget guard immediately above
(`decide.nim:114-127`) switches the LLM off when two more full turns would not fit, and with the
LLM off `open` is empty and the floor is skipped entirely — so on the shipped configs the deadline
cannot be reached *during* the floor. I did not add a new test, because constructing a state that
reaches the slice loop with the deadline inside it requires a config the guard's own arithmetic
excludes; a test that "passes" by having the guard fire would assert nothing about this change.
`tests/test_engine.nim:testInterBatchFloor` is the regression guard that matters here — it still
requires consecutive batches to start `turnSpacingMs` apart, and it is green, so the fix did not
quietly delete the floor.

## N7 — the provenance test's name overstated what it checks
**Satisfies: checklist item 14, first bullets** (chrome provenance — the claim a reader takes from
this test must match what it proves).

`client/broadcast_core.js` differs from the starter's copy in **two** places, not one:
`window.LANE_WIRE` at `:49` and a comment path `src/lane/sim.nim` at `:268`.
`tests/test_viewer.nim:205-211` already restored **both** before comparing, so the assertion was
always honest; its name and its report line ("differs … in the wire name alone") were not. Renamed
to `testBroadcastCoreDiffersOnlyInTheWireNameAndOnePath`, doc comment and report line reworded.
**The assertion is byte-for-byte unchanged** — same two `replace`s, same
`restored.count("window.CTF_WIRE") == 2`. I did not touch `broadcast_core.js`: reverting the
comment to `src/ctf/sim.nim` would make the file match the note's "one identifier" literally at the
cost of pointing a reader at a path this repo does not have.

---

## NEEDS-DESIGN

**N3 — end-position contact resolution instead of the design's swept earliest-crossing resolver.**
Real, and correctly described: `stepBall` (`sim.nim:346-454`) resolves X then Y against tiles by
end position and `stepBolts` (`:503-585`) consumes a bolt on a bunker tile before it ever tests the
avatar box, where design §Resolution order 3.6 (L480-488) gives the avatar box priority (a) on an
exact tie. Not fixed, and not fixable inside a review round: the swept resolver is a different
physics kernel — every contact would need integer cross-multiplied crossing times in `int64`
compared across five priority classes, which changes the per-tick `gameHash` for every ROM. That
means regenerating `tests/data/golden_hashes.json`, bumping `GameVersion` (prepend-only, per
`AGENTS.md`), re-running the 36-cell baseline sweep because the marchers and the ball behave
differently, and re-recording the certification replay. It also removes the property the current
code is built on and directly asserts — no tunnelling, `max(BallSpeedMax, BoltSpeedFriendly) =
4000 < HalfTileU + BallHalf = 9000` (`tests/test_physics.nim:8-19`, cross-checked over 50 000
randomised states at `:21-50`) — which is what makes end-position testing sound in the first place.
Not a checklist item. **Decision for the coordinator:** either amend the design note to describe
the resolver that shipped (with the no-tunnelling bound as its justification), or schedule the
swept resolver as its own change with the hash/version/sweep work above.

---

## DECLINED (with reason)

- **N4 — `MarcherCols = [5..12]` rather than the note's `1,3,…,15`.** Not fixed: the code's own
  10-line comment at `maps.nim:92-101` gives the arithmetic — the note's spread is flush against
  the note's own "would leave columns 1..15" bounds rule, so the formation steps down every march
  tick and breaches row 13 in 160 ticks, i.e. a wave nothing can clear. Changing it to match the
  note makes `gallery` unplayable, and `tests/test_baselines.nim:95-97` (clear a wave on ≥3 of 20
  seeds) would go red. The deviation is documented in place; the note is the thing that is wrong.
- **N5 — `panicTicks: 20, leadTicks: 10` rather than 28 / 14.** Not fixed: design §Scripted
  baselines (L905-908) explicitly delegates these values to the sweep, and 20/500/10 *is* the
  sweep's pick — `tools/ci/baseline_tuning.json` records the 36-cell grid and
  `tests/test_tuning.nim:10-30` asserts the shipped defaults equal it and that no swept cell beat
  it. Hard-coding the note's illustration would falsify checklist item 7 ("tuned with a grid
  harness, not guessed").
- **N6 — 13 `A57_MODE` branch points above the banner.** Not fixed: the branches are what let the
  scorebug plates and the endcard carry cabinet values without a from-scratch page, and the banner
  at `:2652-2654` declares them rather than concealing them. Removing them means either a rewritten
  page (the cogame-gridlock failure checklist item 14 exists to catch) or a second parallel
  scorebug — both far larger edits than the one recorded. Item 14's provenance test is on the CSS
  above the banner, which is clean.
- **N8 — `flake.nix` / `flake.lock` deleted although the note lists them as kept.** Not fixed:
  restoring 376 lines of nix scaffolding that nothing builds with would undo a deliberate commit
  (`309a9b3`) and add an unbuilt second build path. The canonical build is `Dockerfile` + nimby
  (`AGENTS.md` §Building) and no workflow references nix.
- **N9 — three items from the design's test list unimplemented** (disconnect/revive, the
  never-connecting seat reported to `COGAME_PLAYER_FAILURE_URI`, the held-and-applied early
  registration). Not fixed: `tests/test_server.nim` runs **one** server on one fixed port, started
  once for the whole file (`:27-49`), with four seat threads. All three cases need a *different*
  server config (a seat that never dials, a smaller `lobbyJoinTimeoutTicks`, a failure-URI sink),
  i.e. a second instance on a second port and a teardown path the harness does not have. That is
  new harness scaffolding, not a review-round fix, and the risk is a flaky concurrency test in the
  one job that gates everything. Checklist item 1 forbids *loosening* tests, which nothing did; it
  does not require the note's full list. Worth scheduling as its own change.
- **N10 — `stepEvents` derives 8 of the 13 event kinds.** Not fixed: emitting `chip`, `bunker`,
  `saucer`, `near_miss` and `turn_end` into the chrome stream means new feed copy, new beat
  handling and new CSS for any kind that becomes a beat (an unstyled kind is an invisible marker —
  the very thing checklist item 14 warns about), for events the tier-2 path
  (`sim.nim:1015-1046`) already carries. The **beat** set — the one the checklist cares about — is
  exactly the design's five and every kind has a CSS rule.
- **N11 — the renderer fixture rescales the font to the measured box.** Not fixed, and I think the
  fixture is right: it draws each run at the element's *measured* geometry so that "a string the
  page laid out inside its box is inside the canvas here too". Removing the rescale would make the
  canvas gate report overflow for every run whose face differs from the page's real font, i.e. a
  permanently red gate that says nothing. The case the canvas cannot see is asserted directly in
  the same file — `node.scrollWidth > node.clientWidth + 2` with an ellipsis/scroll exemption
  (`:192-197`) plus the "no plate name collapsed" check (`:266-272`).
- **N13 — the wall-clock stop is gated on `phase == Playing`.** Not fixed: unreachable from the
  manifest (every shipped variant sets `lobbyJoinTimeoutTicks = 2880` = 120 s, the cert fixture
  720 = 30 s), and the lobby has its own bound (`sim.nim:936-938` → `server.nim:609-620` →
  `forceStart`). Dropping the guard would let `finishGame(ReasonDeadline, EndRuleWallClock)` run
  from a lobby that never started a game, which writes a `result` record for an episode with no
  play — an untested path with a worse failure mode than the one it closes.
- **N14 — the scorebug plate resolves to the real policy name, not the colour alias.** Not fixed
  on purpose: checklist item 4 asks the viewer to map aliases to real player names for
  non-baseline seats, which is exactly what `teamName(s, team, team.toUpperCase())` does, falling
  back to the alias when there is no roster name. Changing it to always show `RED`/`GREEN`/… would
  work *against* an acceptance item to satisfy a prose line in the note. The note's own constraint
  — agents never see real names — is unaffected: this is the spectator stream
  (`roster.nim:81-87`, pinned by `tests/test_isolation.nim:121-152`).

---

## NOTED (not fixed, not in this review)

- `client/replay_broadcast.html`'s surviving click-to-select handler calls `core.clickMap`, which
  the Worker forwards into `broadcast_core.clickMap` → a `sendCommand`-style select. atari-57 has
  nothing selectable, so this is inherited chrome that does nothing visible. It is not zoom/pan
  wiring, so removing it was out of B1's scope; if a later round wants the page free of dead
  inherited handlers, that and `core.getPaceStats` are the remaining two.
- `viewer_smoke.mjs`'s main-bundle run still reports `canvas text: 0 drawn` (`total: 0`) because
  this viewer renders in an OffscreenCanvas Worker, so item 15's evidence rests entirely on the
  renderer fixture's 112 runs. Unchanged by this round; recorded because the checklist says a
  `total: 0` "means the check covered nothing".
