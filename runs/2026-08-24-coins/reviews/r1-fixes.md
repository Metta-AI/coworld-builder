# r1 fixes — coins

Head: `9c7fbbd51bf030982ef1b4e2ad7cb6008e0695bc`
CI: https://github.com/Metta-AI/cogame-coins/actions/runs/32796206226 — **success**
(jobs `test`, `docker-smoke`, `wasm-viewer` all green; matched to the pushed
head with `gh run list --workflow ci.yml --event push --json headSha`).

Commits are one per finding, each landed through the Git Data API (plain HTTPS
push is refused for this repo from the sandbox: `remote: No anonymous write
access`). Nothing was force-updated and no history was rewritten.

| finding | disposition | commit | files |
|---|---|---|---|
| **B1** | fixed | `0c74d0d` | `client/replay_broadcast.html:2043`, `tools/ci/text_fixture.js`, `tools/ci/build_text_fixture.sh`, `.github/workflows/ci.yml:358`, `tests/test_viewer.nim:106` |
| N1 | fixed | `a5c8bd0` | `tests/test_replay.nim:178-217` |
| N2 | no change | — | `compose.yaml:11` |
| N3 | no change | — | `src/coins/sim.nim:290` |
| N4 | no change | — | `src/coins/sim.nim:224` |
| N5 | no change | — | `src/coins/server.nim:176` |
| N6 | fixed | `6476b35` | `src/coins/sim.nim:656`, `tests/test_sim.nim:379` |
| N7 | fixed | `e8518e6` | `src/coins/llm.nim:381` |
| N8 | fixed | `bfedbb1` | `src/coins/server.nim:110`, `:132`, `:415`, `:523` |
| N9 | fixed | `ba29048` | `src/coins/sim.nim:441`, `tests/test_replay.nim:220` |
| N10 | no change | — | `tests/test_llm.nim:139` |
| N11 | partly fixed | `95adfcf` | `tests/test_dilemma.nim:150` |
| N12 | fixed | `419d50f`, `16ec1d3` | `tools/tune_baseline.nim`, `.github/workflows/ci.yml:161` |
| N13 | no change | — | `client/replay_broadcast.html:2360` |
| N14 | no change | — | `src/coins/events.nim:37` |
| N15 | fixed | `9c7fbbd` | `client/replay_broadcast.html:2346`, `tests/test_viewer.nim:85` |
| N16 | fixed | `c72dbdf` | `client/replay_broadcast.html:2200` |
| N17 | no change | — | `src/coins/llm.nim:311` |
| N18 | fixed | `cda7b61` | `src/coins/server.nim:426-435` |
| N19 | no change | — | `src/coins/sim_config.nim:69` |

---

## B1 — the LLM remark had no bound, and no fixture ever drew one

**What the code did.** `say` is LLM-authored, capped at `MaxSayLen = 48` runes,
and drawn into a `#killfeed` row that is the starter's `.feed-row`:
`max-width: none; white-space: nowrap` (`:502-503`). The starter's own comment
says why that is safe *there* — its rows carry a pre-bounded 10-char name and a
glyph. Nothing in CI could ever show what happens when a 48-rune remark lands
in it: `docker_smoke.sh` runs with no `ANTHROPIC_API_KEY`, a scripted decision
carries no `say`, and the viewer smoke on that replay reported `feed_lines: 0`
and `canvas text: 0 drawn` — which item 15 itself says "means the check covered
nothing".

**Measured, not estimated.** I built the fixture first and ran it against the
pre-fix page. A full-cap remark laid out **313 px wide inside the feed's own
95 px band** at the 360 px featured-match width (CJK), **904 px** at the widest
stage — three to four times the band, growing leftward across the arena. It
does *not* leave the stage at any size I measured, so the reviewer's
counter-evidence was right on that point and the defect is the unreserved band,
not a clipped string. Pre-fix run: **68 failures, 2 `never_inside` strings**
(`"“MMMM…"`, `"“締締締…"`, "no room was reserved for these").

**What it does now.**
- `client/replay_broadcast.html`: the remark is drawn into its own `.cn-say`
  span on a `.cn-order` row, and the game block's style element gives that row
  a band sized from the cap the server enforces — the feed's own width
  (`max-width: 100%`, which follows both the 228 `--u` default and the
  starter's 190 `--u` `#stage.tiny` override), the remark on its own line
  inside it, `white-space: normal; overflow-wrap: anywhere`. Wrapping, not
  ellipsis: item 15 calls an ellipsized sentence a defect. Rows still only grow
  upward into `#killfeed`'s existing 4-row reserve, so a remark landing moves
  nothing.
- `tools/ci/text_fixture.js` + `tools/ci/build_text_fixture.sh`: the fixture is
  the **real page** — `client/replay_broadcast.html` spliced with the real
  `wire_constants.js` / `chrome_common.js` / `broadcast_core.js` exactly as
  `Dockerfile.replay-viewer` splices it — with its websocket stubbed, so frames
  arrive through the page's real ingest path (`onText` → `onFrame` →
  `CoinsGame.onFrame` → `cnApplyEvent` → `cnPushRow` → the chrome's
  `pushFeed`). It pushes **four full-cap remarks at once, one on every seat**
  (MAX_FEED), at **six stage widths** (360 → 1400, across both `--hudscale`
  clamps) in **three shapes** (widest Latin, full-width CJK, a real sentence),
  waits for the feed's entrance animation to play through to settle, and per
  line box asserts (a) the remark is still *full length* — exact string
  compare, so a quietly shortened remark fails — (b) every line is inside the
  reserved band and the band is inside the stage and clear of the scorebug
  band, (c) nothing is clipped. It mirrors every measured line onto a canvas
  the size of that band, at the browser's own position and font, so
  `--strict-text-bounds` gates real model text instead of reporting `total: 0`.
- `.github/workflows/ci.yml`: its own step, `Render the worst-case remark
  fixture`, `viewer_smoke.mjs --bundle dist/text-fixture --strict-text-bounds`,
  printing the per-size measurements and the `canvas_text` line.
- `tests/test_viewer.nim`: the band, the wrap, the absence of an ellipsis rule
  on the remark, and the CI wiring.

**Evidence** (run 32796206226, job `wasm-viewer`, step *Render the worst-case
remark fixture*):

```
[log] text-fixture latin-wide @ 360x640: stage 360x421, hudscale 0.500, bands 23/38,
      4 rows, widest row 95px, feed band 95px, feed top/bottom 278/38px
...
[log] text-fixture OK: 6 stage sizes x 3 full-cap remark shapes x 4 rows,
      every line inside the stage and full length
canvas text: 184 drawn, 0 never inside the canvas (0 draws crossed an edge),
      0 ellipsized (--strict-text-bounds)
fixture canvas_text: {"total":184,"never_inside":0,"outside":0,"ellipsized":0}
```

Widest row now equals the feed band at every size (95 / 104 / 198 / 362 px),
i.e. the row is the band. Checklist item 15, final bullet, and item 15's
reserved-band bullet on the horizontal axis.

## N1 — the frames now come back element by element

Coins records state, not inputs, so there is no re-simulation to compare
against; the property item 2 guards becomes "the bytes the viewer parses carry
the sim's own frames exactly". Nothing asserted more than the frame *count*,
the config and the terminal frame. `tests/test_replay.nim` now walks all 320
frames comparing `t`, `c`, `k`, `sc`, `th` against `episode.frames[i]`, asserts
frame *i* is the state at tick *i*, and walks the playhead over the same range
to show the viewer's frame at tick *i* is frame *i*. Green in both debug and
release (`test_replay OK` ×2). Item 2.

## N6 — the deadline reserves the beat it is about to start

Was: test the bare clock at a beat close, then start a beat that can cost
`2 × llmTimeoutSeconds`, so a beat starting at 719.9 s settled at ~744 s —
past the 720 s item 5 budgets. Now `runEpisode` reserves
`worstCaseBeatSeconds()` against the deadline, so whatever it lets start it can
also let finish. Still checked at beat closes only, exactly as the note says.
`tests/test_sim.nim`: a clock inside the reserve settles at the first beat
close with `deadline`; a clock clear of it runs the full 24-beat cap. Item 5
(timeout).

## N7 — the batch cannot escape `decideAll`

The per-seat `try` covered everything Coins raises; `buildObservation`,
`userPrompt`, `requestFor` and `curl.makeRequests` sat outside it, and
`runGame` has no `try` around `runEpisode` — a raise there would have left the
episode thread without ever reaching `finishEpisode()`: no results, no replay,
`/healthz` answering until the platform's own timeout. The batch build and
dispatch now run inside their own `except CatchableError` that leaves every
open seat open, so the retry and then the scripted fallback carry the beat
exactly as a per-seat failure does; a short response list is caught rather than
being an `IndexDefect`. **Untested** — nothing in the sandbox can make `curly`
raise and there is no stubbed transport in the tree (N10). It is a guard, not a
behaviour change on any path CI exercises. Item 5 (hang).

## N8 — no worker thread reads the sim mid-mutation

`WS /global`'s upgrade handler ran `pushGlobalLocked` on a mummy worker thread,
reading `gameSim.currentFrame()` and the sim's seqs while the episode thread
appended to them without the lock. `pushGlobalLocked` (episode thread, lock
held) now also publishes the frame and chrome it drew into `shared`, and the
upgrade handler sends that snapshot. The live board is pushed at beat closes,
so a joining socket gets exactly the frame it would have got anyway;
`runGameServer` publishes the opening frame before the episode thread exists.
`gameSim.config` (immutable after `initSim`) is the only sim state a worker
thread still touches. Not exercised by CI — `docker_smoke.sh` opens no
`/global` socket — but the read it removes was not exercised either. Item 5.

## N9 — a forfeit writes a replay that can be opened

`forfeit` settles without ever calling `stepTick`, so `frames` was `[]` and
`parseReplayBytes` rejected the artifact the platform had just stored.
`endEpisode` now records the opening position as that episode's one frame when
no tick was played, keeping `ticksPlayed`, `series.score` and `frames` in step;
every other path is unchanged. `tests/test_replay.nim` writes a stillborn
episode, re-reads it, and asserts it loads with one frame, reason `forfeit`,
both scores 0, playhead `maxTick == 0`.

## N11 — the note's absolute floors are now asserted (partly)

Added: mutual restraint's mean ≥ 10 (CI: 14.94) and the mutual-harm trap's mean
below 5 (CI: −0.19). **Not** added: the note's per-seat forms of (c) and (d).
Gate (d) per seed is a property the shipped baseline does not have — see
"design questions" below — so gating it would be a test asserting something the
code does not hold. The per-seed rows and an inversion count are printed
instead.

## N12 — a real grid harness, and what it says

`tools/tune_baseline.nim` plays the whole `punishThreshold × punishBeats ×
truceBeats` grid (3 × 5 × 3) against all four baselines over seeds 1..8 at
certification length — 1440 episodes — and prints a ranked table with the
shipped point marked. `ci.yml`'s `test` job runs it, so the sweep is in every
run's log. It gates the note's two claims about the reciprocator (it beats the
sucker payoff; it still emits a truce per episode and still punishes) and
**reports** its distance from the grid's best rather than gating optimality.

`419d50f` first shipped an optimality gate ("within one coin of the best"),
which went red: the shipped point is rank 29 of 45. `16ec1d3` replaced that
gate with the print, because the gate was mine and not the game's — the note
never claims the point is the argmax. That is the only red CI in this round and
it is fixed forward, not fixed by deleting anything that existed before.

## N15 — the spoilers gate reaches the game block's markers

chrome_common's gate walks `markerEls`, the divs *it* placed; Coins' markers
are buttons the game block builds (chrome_common's `markBeat` takes no label
and the file is byte-identical to the starter's, so a labelled clickable marker
cannot come from that path — item 14(d) requires the button). "Spoilers off"
therefore meant nothing on this scrubber. The block now reads
`CH.C.getSpoilers()` and applies the chrome's own rule to its own buttons, on
every frame and on the toggle's click (the chrome re-runs its gate on the next
transport render, which never arrives while playback is paused). Verified in a
browser against the built page: markers at ticks 40/100/160 with the playhead
at 80 → spoilers off hides 100 and 160, keeps 40; toggling back reveals both.

## N16 — the clock caption counts ticks

`s.mx` is the last tick *index*; the caption counts ticks, so a 320-tick
episode now reads `tick 240 of 320` as the note gives it, not `of 319`. CI
evidence: the viewer smoke's clock readout changed from `TICK 240 OF 319` to
`TICK 240 OF 320` in run 32796206226. The inherited transport readout keeps the
chrome's 0-based `240 / 319` — a scrubber position, not a count — and
`chrome_common.js` is untouched.

## N18 — a misspelled `PLAYER_SCRIPTED` says so

`parseScriptKind` returns `skNone` for anything unrecognised and the server
reads `skNone` as "an LLM seat", so `PLAYER_SCRIPTED=titfortatt` quietly played
the default prompt against real credentials. One echo on the seat's own
registration, naming the value and the four legal names. Behaviour unchanged:
the note specifies none for an invalid value, and rejecting the registration
would turn a typo into a dead seat.

---

## No change, with the evidence

**N2 — `compose.yaml`'s service is `coins`, not `game`.** Internally
consistent and pinned: `tests/test_manifest.nim:39` asserts
`serviceName == "coins"` and `:41-45` derives `{{COINS_IMAGE}}` from it by the
rule the note actually cares about (`placeholder == service.toUpperAscii() &
"_IMAGE"`). `ci.yml`, `coworld-release.yml` and `docker_smoke.sh` all use
`COINS_IMAGE`. Renaming the service would touch five files to satisfy an
example in the note rather than an invariant.

**N3 — two `blocked` events in one tick.** The note contradicts itself
(`design.md:200-201` says one; `design.md:278-281` says a refusing cog emits a
`restraint` event *while it walks around the coin*), and the code follows the
§five-intents reading, which `2e3c462`'s commit message records as deliberate
and which the viewer's hand-off glyph is anchored to. Changing it would delete
the restraint glyph's event.

**N4 — a cog standing on its target waits.** The code is *stricter* than step
3b read literally, and implements `design.md:272` ("walk to the room centre and
wait there"). `tests/test_sim.nim:124-126` pins the parking behaviour. The
literal reading would make a parked cog wander off centre and back.

**N5 — the play clock starts before the connect wait.** This is the
conservative choice for item 5, not a bug: item 5 measures settlement against
60 % of `episodeTimeoutSeconds` from process start, and starting the clock
after the connect wait would allow 180 + 720 + a beat. The worst case today is
that a slow-connecting episode plays fewer beats and settles with the legal
reason `deadline`. Moving it would make the number the checklist reads *worse*.

**N10 — the batch/cadence assertions are dead in CI.** Real, and item 8 does
not require a test. Making them live needs an injectable transport
(`LlmClient` builds its `Curly` internally), which is a design change, not a
review fix. I did not add a fake-endpoint test: pointing the client at a closed
port would exercise the *per-request `.error`* path that already works, not the
raise path N7 guards, so it would buy a green tick and no information. Recorded
as a design question below.

**N13 — the endcard covers the reciprocity strip.** The endcard's two-row table
already carries the per-seat reciprocity numbers (coins, thefts, stolen from,
restraint); what the note also asks for is the strip itself at full width.
Cloning `#cn-recip` into the card duplicates an id its whole stylesheet is
keyed on, so it means a second set of rules for a card no fixture covers. Left
for a round that can measure it. Non-blocking, and not a checklist item.

**N14 — `notes` is recorded but never drawn.** The note says it is drawn "only
in the feed's expanded row" and there is no expanded row. Drawing a 300-rune
string in the same feed is exactly the class of unbounded text B1 is about, and
would need its own reserved band and fixture coverage. An unrecorded string
cannot be clipped; a badly-placed one can. Deliberately not added blind.

**N17 — 429 is retried in the same beat as well as the next.** Both happen, as
the reviewer says: the raise lands in the per-seat `except`, the seat is
retried once inside the beat, falls back if that fails, and is open again next
beat because a 429 does not disable the client. The note's sentence describes
the second half; the code does the note's half and one bounded retry more.
`minBeatSeconds` still floors the batch spacing, so this cannot become a
request storm.

**N19 — `playDeadlineSeconds` never reads the environment.** The note's own
sentence says the game container is **not** given `COWORLD_TIMEOUT_SECONDS`;
the code's docstring says "unless the config supplies it", and the config is
what the manifest sets (`episode_timeout_minutes: 20`,
`tests/test_manifest.nim:191-208` checks the budget against it). Nothing in
this repo, the starter, or the manifest sets that variable. Adding a read would
invent a platform contract and a new failure mode (an env value that shrinks
the deadline below `maxBeats × worstCaseBeatSeconds` makes `validate()` raise
and the container exit 2 instead of playing).

---

## Design questions for the judge / next round (not fixed here)

1. **The reciprocator is not the strongest point on its own grid, and its edge
   over pacifism is a mean, not a property.** `tune_baseline.nim` (CI run
   32796206226, step *Tune the reciprocator on a grid*): the shipped
   `punishThreshold=2 / punishBeats=4 / truceBeats=3` scores **−6.63** against
   greed where `thr=1 / pun=5 / tru=2` reaches **−4.38** — rank 29 of 45.
   `test_dilemma.nim`'s new per-seed print: the reciprocator is *worse* than
   the honest baseline against greed on **5 of 8 seeds** (aggregate margin
   0.375). The note's gate (d) — "strictly greater on the same seed" — is
   therefore not a property the shipped baseline has. Retuning moves a number
   the note states (`design.md:459`) and shifts the payoff table
   `test_dilemma.nim` measures, so it is a design decision, not a review fix.
2. **No stubbed transport (N10).** The retry/fallback loop and the one-batch
   cadence assertions never execute in CI. Making them executable means giving
   `LlmClient` an injectable transport.
3. **The up-front verdict (N15's second half).** `setVerdict` needs a draw
   flag; the `over` beat row carries only a winning seat and `beatsTimeline`
   resolves a tie to slot 0, so placing the verdict from that row would show a
   **wrong** verdict for a drawn match. Needs either a `draw` field on the beat
   row or the results object read at ingest.

## NOTED (not fixed, not a finding this round)

- `viewer_smoke.mjs`'s `feed_lines` readout looks for `#feed, .feed, #log` and
  Coins' feed is `#killfeed`, so the harness reports `feed_lines: 0` even when
  the fixture has four rows on screen. The file is byte-identical to the
  template and must stay so; the fixture prints its own row count instead.
- The page requests `./font.ttf`, which neither the bundle nor the fixture
  ships (404, `font-display: block` falls back). Pre-existing, in the starter
  too, and outside this round's findings.
