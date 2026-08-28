# r1 fixes — snake-royale

Repo: `Metta-AI/cogame-snake-royale`.
Head: **`d8652fa2d92b14a6da207d71076027f806f7849e`** (`main`).
CI: run **33149313876** — <https://github.com/Metta-AI/cogame-snake-royale/actions/runs/33149313876> —
conclusion **`success`**, `headSha d8652fa2d92b14a6da207d71076027f806f7849e`, all three jobs green
(`test`, `docker-smoke`, `wasm-viewer`). `grep -c "SEAT-COUNT FAIL"` over the docker-smoke log → **0**.

Every finding is one server-side commit, in finding order, `main` fast-forward only. One finding
(F20) is refuted with evidence and has no commit; one (F8) is refuted as a defect but its
divergence is recorded, so it has a commit that changes documentation and tests only.

Method note: the sandbox turned out to be able to run the `test` job locally — Nim 2.2.4 via nimby,
the whole `tests/*.nim` suite in debug **and** `-d:release`, the baseline sweep, the fixture
recorder — and to run `tools/ci/viewer_smoke.mjs` in headless chromium (Playwright 1.55.0) against a
stand-in bundle. Every change below was verified locally before it was pushed; CI is the
authoritative run and is cited above.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F1 | fixed | `1cab680116bc` | `src/snake/replay_runtime.nim:288-322`, `tests/test_snake_replay.nim` | 13 (playback/seek), 14(c) endcard dismissal |
| F2 | fixed | `2e4878bdf5df` | `src/snake/engine.nim:109-137`, `src/snake/baselines.nim:47-52`, `tools/ci/baseline_tuning.json`, `tests/test_snake_control.nim` | 7 (tuned, not guessed), 1 (no test loosened) |
| F3 | fixed | `66a3239d22e9` | `tests/test_snake_sim.nim:372-455` | 1 (no test loosened) |
| F4 | fixed | `389d120e8fc0` | `src/snake/decide.nim:189-250`, `src/snake/sim_config.nim:114-119`, `tests/test_snake_llm.nim` | 8 (retries once) |
| F5 | fixed | `94fd81e9353a` | `tools/ci/renderer_fixture.html`, `.github/workflows/ci.yml`, `client/replay_broadcast.html:1554-1562`, `tests/test_snake_viewer.nim` | 15 (legibility) |
| F6 | fixed | `0fbedf5e6796` | `client/broadcast_core.js:80-108,150-175,371-420`, `tests/test_snake_viewer.nim` | 15 (reserved band, sized from the cap) |
| F7 | fixed | `00d60dd957ce` | `src/snake/replay_runtime.nim:270-300`, `tests/test_snake_replay.nim` | other |
| F8 | **DISPUTED** (divergence recorded) | `6db2d047283e` | `docs/RULES.md`, `coworld_manifest_template.json`, `tests/test_snake_upstream.nim` | correctness |
| F9 | fixed | `8c2cd1cae4aa` | `src/snake/rules.nim:203-258`, `tests/test_snake_sim.nim:234-290` | correctness |
| F10 | fixed | `850a9122fbba` | `src/snake/directives.nim:51-68`, `src/snake/decide.nim:291`, `tests/test_snake_control.nim` | other (design §Reply schema) |
| F11 | fixed | `df9201249d30` | `src/snake/decide.nim`, `src/snake/server.nim`, `src/snake/replay_runtime.nim`, `tests/test_snake_events.nim`, `tests/test_snake_llm.nim` | 8 (fallback recorded/countable) |
| F12 | fixed | `d58ee6162129` | `src/snake/rules.nim`, `src/snake/labels.nim`, `tests/label_manifest.txt`, `tests/test_snake_label_contract.nim` | other (design §Readouts 8) |
| F13 | fixed | `88589cc43a57` | `tests/test_snake_sim.nim`, `test_snake_engine.nim`, `test_snake_replay.nim`, `test_snake_viewer.nim`, `test_snake_endcard_labels.nim`, `src/snake/engine.nim`, `src/snake/records.nim`, `src/snake/server.nim` | 1, 2, 5, 13, 14 |
| F14 | fixed | `97729903c6a7` | `tests/fixtures/*.replay` (3 new), `.github/workflows/ci.yml`, `tests/test_snake_replay.nim` | 13 (the bundle runs), 2 |
| F15 | fixed | `91be18d5360e` | `tools/ci/check_gameversion.sh`, `next_coworld_version.py`, `test_next_coworld_version.py`, `.github/workflows/ci.yml`, `src/snake/sim_types.nim` | 10 (manifest validates), 12 |
| F16 | fixed | `2dcfd907d15d` | `scripts/build_replay_page.py` | 14 (provenance audit trail) |
| F17 | fixed | `a240a224d7ab` | `src/snake/server.nim:317-330,470-500`, `tests/test_snake_llm.nim` | 5 (60 % envelope) |
| F18 | fixed | `f3d2314fd688` | `client/broadcast_core.js`, `replay-viewer/static_replay.js`, `replay-viewer/static_replay_worker.js`, `tests/test_snake_viewer.nim` | 14 (`#viewpanel` removed, not hidden) |
| F19 | fixed | `c413b9964007` | `client/replay_broadcast.html:1765-1780,1916`, `tools/ci/renderer_fixture.html`, `tests/test_snake_endcard_labels.nim` | 14 / other |
| F20 | **REFUTED** | — | evidence below | other |
| F21 | fixed | `d54890f5ec30` | `tools/tune_baselines.nim:25-52`, `src/snake/baselines.nim`, `tools/ci/baseline_tuning.json`, `tests/test_snake_control.nim` | 7 (tuned with a grid harness) |
| F22 | fixed | `a1b4474e9769` | `tests/test_snake_scoring.nim` (new), `tests/test_snake_sim.nim`, `tests/shard_1.nim` | other |
| F23 | fixed | `0cf2e62bac7b` | `.github/workflows/ci.yml:260-267` | other |
| F24 | fixed | `8bdd553b4ef9` | `src/snake/events.nim`, `src/snake/server.nim`, `tests/test_snake_events.nim` | other |
| F25 | fixed | `d8652fa2d92b` | `client/replay_broadcast.html:1010-1018`, `tests/test_snake_viewer.nim` | 15 / legibility evidence |

---

## F1 — the scrubber sent a tick to a runtime that parsed a fraction

**Was:** `replay_runtime.command` read `s:<n>` with `parseFloat` and handed it to `seekFraction`,
which clamps to `[0,1]`. The page sends `st + round(frac * (mx - st))` — an absolute turn, the
starter's own wire word (`coworld-ctf/src/ctf/global.nim:1853-1856` reads it with `parseInt`). Every
non-zero click clamped to 1.0 and landed on the last frame, which also *raised* the endcard, because
`over` is `turn >= turns`.

**Now:** `seekFraction` is replaced by `seekTurn`, which clamps to the recorded turn range and maps
the turn onto the frame axis. A mid-match seek therefore has `over == false` and the page's
`renderEndcard` takes the card down.

**Evidence:** CI run 33149313876, artifact `viewer-smoke`, `viewer-smoke.json`:

```json
"scrub": [ {"at":"0%",  "clock":"ALIVE 3/4 turn 20/40 …"},
           {"at":"50%", "clock":"ALIVE 3/4 turn 21/40 …"},
           {"at":"100%","clock":"ALIVE 2/4 turn 40/40 …"} ]
```

The 50 % click now lands at turn 21 of 40 (it was `turn 40/40` on the reviewed sha). Plus
`tests/test_snake_replay.nim` block 33b: a midway seek lands midway and is not the last turn, both
ends clamp, and the page still sends the tick the runtime parses. The renderer fixture additionally
asserts *in a browser* that a frame back inside the match removes `#endcard.on` (F5/F19).

## F2 — the ladder measured seats, not players

**Was:** `ladderTotals` seated coil on slots 0/2 and forager on 1/3 for all 24 episodes, forager
out-scored coil by 0.097, and test 27's directional assertion had become `abs(margin) >= 0.05`.

**The measurement was wrong first.** Playing coil with *forager's own tunables* on that ladder scores
**−0.222** — two identical players, 0.222 apart — so most of the −0.097 was spawn-anchor bias, not
policy. Re-tuning against a biased ladder would have been fitting the seats.

**Now:** each seed is played twice with the pair swapped between the seat pairs (four seeds × three
modules × two seatings = the same 24 episodes), on which an identical pair scores exactly `0.0` —
asserted in test 27. On that ladder the swept matrix has positive candidates, and the best is
`coil = (spaceWeight 100, spaceCap 2, headRiskPenalty 900, killBonus 120, foodWeight 100,
hungerThreshold 12)` at **+0.1805**, winning all three modules (royale +999, geese +2666, tron +667
permille). `tools/ci/baseline_tuning.json` was regenerated by `--write` from that run and `--check`
reproduces it. Test 27 asserts `margin > 0.0` again **and** keeps the zero-sum assertion, the
materially-different assertion and the exact integer pins, and now checks all three modules.

**The note's `[+0.30, +1.20]` band is not reachable** by any candidate in the swept matrix (36 rows,
all printed in the CI log; best +0.1805). I did not invent one: the honest assertion is `> 0` plus
the exact pins, and `baseline_tuning.json` records that the band was measured false.

**Evidence:** CI `test` job, step "Sweep and verify the scripted-baseline tuning":
`ladder margin (coil - forager, mean score per seat): 0.1805` / `baseline tuning matches
tools/ci/baseline_tuning.json`; and "Run tests": `ladder: coilPermille=4332 foragerPermille=-4332
coilTurns=1893 foragerTurns=1982 margin=0.1805`.

## F3 — `check pending.len >= 0` was a tautology

**Now:** two real assertions. (a) A hand-built 5×5 trail board seals seat 0 into two columns one
cell at a time: the turn before emits nothing, the sealing turn emits **exactly one** `trapped`
event carrying the free-cell count and the length that triggered it, and the turn after — still
trapped — emits nothing further. (b) The same property over a whole tron episode, replayed through
the runtime so the resolver's own per-turn flags are available: an event exists for seat *s* on turn
*T* **iff** *s* is alive and trapped on *T* and was not trapped on *T−1*, and the episode really
does seal somebody in (4 transitions).

**Evidence:** mutation-checked locally — deleting the `if not state.snakes[slot].trapped:` guard in
`rules.nim` step 13 makes three of these assertions fail; restoring it makes them pass.

## F4 — the turn budget was spent on the rate floor

**Confirmed and fixed.** `turnStart` was taken at the top of `decide.turn`, above the
`turnSpacingMs` sleep. In steady state that sleep lasts `9 s − L(k−1)`, so with the note's own
typical four-call batch (≈4 s, §Cadence) only 6 s of the 11 s budget was left when the first request
went out — exactly attempt 1's own deadline, so a seat that failed attempt 1 took a `timeout`
fallback at the deadline check instead of entering the retry batch that D3 and the §Degrade table
make unconditional.

**Now:** the clock starts at the first request, below the rate floor, so the budget covers the calls
it was sized for (6 + 3 + 2 s of slack, the note's cadence table). `sim_config` repairs a
`turnBudgetMs` that cannot hold *both* attempts rather than one that cannot hold attempt 1.
`tests/test_snake_llm.nim` asserts the source ordering (`rate floor < turn clock < deadline check`),
the repair, and `turnBudgetMs >= attempt1Ms + retryMs`.

## F5 — the fixture was the only text coverage and it drove nothing

**Now:** three changes.
1. The fixture drives **real** chrome data: four roster seats with real policy names, a place badge,
   a health bar, a trapped seat and a fallback glyph; one beat of every one of the seven emitted
   kinds; a full-width length series; the duel turn; a full-cap `say` feed row; and a results
   document. It drives them through the **shipped page's own frame path**
   (`window.SNAKE_DRIVE_FRAME`, published beside the existing install hook), so the plates, the beat
   buttons, the ribbon, the banner lane, the feed and the endcard are rendered by the code the
   hosted viewer runs — and it fails the step with a named `data-replay-error` if any of them is
   missing, including "the endcard stayed up after a seek back into the match".
2. `ci.yml` uploads `fixture/viewer-smoke.{png,json}` beside the bundle's.
3. Both viewer steps now say **which surface they cover**: the bundle step gates load, advancement
   and the scrubber, and reports `canvas_text.total: 0` *by construction* (it draws in a Worker on an
   OffscreenCanvas, where the harness's main-thread patch cannot see a `fillText`); the fixture step
   is the text-bounds gate, on a main-thread canvas with the shipped `broadcast_core.js`.
   Extending the smoke into the worker would mean editing `tools/ci/viewer_smoke.mjs`, which is the
   shared template copied verbatim, so the coverage split is documented and pinned instead.

**Evidence:** CI, step "Drive the worst-case text chrome (renderer fixture)":
`canvas text: 72 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`, and `fixture/viewer-smoke.json` is now in the `viewer-smoke` artifact with
`"canvas_text": {"total": 72, "outside": 0, "never_inside": 0, "ellipsized": 0}`.
`tests/test_snake_viewer.nim` block 48 pins the fixture's data, its failure strings and the upload,
so a future edit cannot quietly empty it again.

## F6 — the bubble was sized from the string, in the wrong font, with no band

**Now:** the box is measured once per font size from a full-cap sample (`'W' × MaxSayRunes`, the
server's own cap off `SNAKE_WIRE`) in the active face, so every bubble is the same size and the
widest legal remark fits inside it. `data/font.ttf` is loaded best-effort as a `FontFace` and the cap
is re-measured when it lands, so the measurement is always in the face that draws. If a full-cap box
would not fit the board the **font** shrinks (floor 9 px) — the string is never shortened, because a
clipped sentence is the defect. `boardGeometry` reserves the band above the board *before* fitting
the cell, so a top-row snake's bubble rides the band instead of flipping below its own head, and the
board does not move when a remark lands.

**Evidence:** the fixture's 72 draws, 0 outside, at 360/640/1024 px on all three boards (above), and
the screenshot shows the top-row bubbles in the reserved band. Test 43's rule-3 pins move to the new
expressions and add the cap-sizing and reserved-band assertions.

## F7 — the duel banner announced a rate change that never happened

**Confirmed:** `framesPerTurnAt` had no caller. `advance` now paces on
`framesPerTurnAt(turnAt(frame))` through a sub-frame accumulator: inside the duel a turn takes twice
as many render frames. The frame **axis** is untouched, so `s:<tick>`, the scrubber and the beat
buttons stay 1:1 with the turn, and outside the duel the arithmetic reduces to `frame += step`
exactly. Test 33c: eight frames of normal playback advance eight, eight frames inside the duel
advance four.

## F8 — DISPUTED: the code is right, the note contradicts itself

Step 9 says head-ons resolve before body collisions *precisely so* the winner is not "immediately
killed by the loser's neck" (design.md:292-293). Step 10 says every corpse still occupies the board,
without qualification (design.md:301-302). After step 5 a head-on loser's head **is** the winner's
head cell, so the two sentences disagree about exactly one cell — and blocking it kills every
head-on winner on its victim's corpse, i.e. `longer_wins` decides nothing. Trace, with the code as
shipped: `rules.nim:477-495` skips **only** `i == 0 and dying[slot] and cause[slot] == dcHeadOn`;
a `wall`- or `starve`-killed snake's whole body **including its head** still blocks, and the loser's
neck and body still block. `tests/test_snake_sim.nim` block 8 pins the winner surviving and holding
the cell; block 9 pins a starved corpse killing a rival that walks into it on the same turn.

No code changed. The divergence is now recorded where divergences go: `docs/RULES.md` §Divergences 6
(and step 10's own bullet), with the manifest's inlined copy of the page moving with it.
`tests/test_snake_upstream.nim` asserts the text is there and — new — that all three inlined doc
pages and the readme in `coworld_manifest_template.json` are byte-identical to the files they claim
to be, so a doc edit can never ship a manifest describing other rules.

## F9 — `tie` was unreachable under `longer_wins`

`headOnOutcome` now tracks the longest rival and how many rivals share that length, and answers
exactly what step 9 will do: `win` when I am strictly longest, `tie` when nobody is (my length
equals the top, or the top is shared), `lose` only when exactly one rival is strictly longer. Both
new cases are asserted **against `resolveTurn` itself**, not just against the enum. The second half
of the finding is fixed too: contention no longer counts a rival's own neck, which step 2 repairs
away, so following a rival's vacating tail is no longer reported as a head-on risk — again checked
by driving the same position through the resolver.

The reviewer's third sub-note (the post-move length adjustment ignoring a `shrinkEvery` tick) is a
**no-op**: a shrink turn pops one segment from *every* live snake, so it decrements both sides of
every comparison and cannot change `>`/`==`. Left alone deliberately.

The ladder integers did not move (both baselines already penalised `hrLose` and `hrTie`
identically), so `baseline_tuning.json` is untouched by this commit.

## F10 — `MaxReplyBytes` declared, never applied

`directives.boundedReply` applies the cap on a rune boundary (it backs off UTF-8 continuation bytes,
so the capped text is still valid UTF-8 and a `say` sliced out of it cannot carry half a codepoint),
and `decide.turn` reads every reply through it before `extractJsonObject` walks it. `llm.nim` is
untouched — the note keeps that file structurally verbatim and names the parse call as the fork's
own. The test proves the behaviour rather than the constant: JSON buried past the cap does not
parse, JSON inside the cap does, an emoji straddling byte 4096 comes back valid UTF-8, and the
decision path is the caller.

## F11 — no `fallback` event was ever constructed

Both paths now emit it, from the one place that knows: **live**, `DecisionEngine.events` collects a
`fallback` `TurnEvent` at each of the three fallback sites and `server.nim` folds them into the
episode's stream; **on playback**, `ingestChats` keeps each fallback's slot and cause and the
pre-scan turns it back into the same event beside the `say` it already re-applied, into non-hashed
fields only. Attempt 1 and the retry write two records for one missed call and become **one** event.
The scrubber's fallback beats now come from the event stream like every other beat, with the real
seat instead of a hardcoded slot 0. Tested both ways: an engine with no credentials emits exactly
one event with cause `no_credentials` while still installing a legal order; a replay carrying the
two records comes back with one event, one beat, the exact
`COG-beta MISSED THE CALL — coil move (timeout)` feed row, and a `fallback` row in the JSON-lines
stream.

## F12 — the feed carried fewer facts than the note prints

The events now carry the facts the wording needs and the wording stays in `labels.nim`: `death`
carries the cell that killed it (for a wall death the **off-board** target), so `deathPhrase` +
`wallSideOf` — both previously uncalled — produce `COG-delta runs into the north wall`; `headon`
carries the whole group as `slot:length` plus the winner and its length, so the row is
`HEAD-ON — COG-alpha (8) beats COG-gamma (6)` or
`HEAD-ON — COG-beta and COG-delta both die (7 v 7)`; `decline` carries the rival the audit already
knew was the only contender. `tests/label_manifest.txt` is regenerated in the same commit, as its
contract requires, and the label test renders each of the note's example rows from a real event and
sweeps a whole episode asserting every wall death names its side and every head-on row carries the
lengths.

## F13 — ten numbered tests asserted less than the note claims

All ten closed; the commit message lists each. The load-bearing ones: **15** builds the three-key
ranking independently and compares it to `placements()`, then reads `win`/`place` off the results
document; **16** adds the all-four-die turn (four lengths, one wall, one turn) ending
`complete`/`last_standing` with the length tie-break deciding all four places; **18** times every
turn and asserts none exceeds 3 ms in release; **31** drives both halves for real, with the failure
payload now coming from `records.playerFailureJson` — the proc `server.nim` POSTs — and a twelve-turn
loop with a seat that connects and never answers; **32** *drives* `decide.turn`'s guard (does not
fire at elapsed 0, fires at elapsed 10, writes the record naming the turn and the remaining seconds,
every seat still holds an order); **33** records the abnormal endings through a new
`runScriptedEpisodeWith(stopAfterTurn=…)` so the recorded turn stream really ends at the stop turn;
**39** pins `chrome_common.js` by SHA-256 (`7ace7287…d72f7c`, the note's own digest) computed by a
SHA-256 written out in the test and checked against the standard `"abc"` vector; **40** pins the
inherited head and `pushFeed`'s **body** by sha256 and length; **44** pins the exact occurrence count
of every re-mapped endcard string.

On 40: the starter is not in the CI image, so a byte diff against it cannot run there. The pin is a
regression pin on the inherited bytes; provenance itself is reproduced mechanically by
`scripts/build_replay_page.py` (F16), and the two recorded harness edits to that region are named
beside the pin.

## F14 — fixtures and the wasm smoke

The three fixtures the note names are recorded and committed (`royale-seed42`, `geese-seed7`,
`tron-seed13`, 40 turns each), and `ci.yml`'s `wasm-viewer` job runs
`wasm_replay_smoke.cjs dist/static-replay-viewer <fixture> 300` over each one. Test 36 is no longer
a no-op: it requires the directory and all three files, and **re-derives** each against the current
rules, so a rules change that leaves a fixture behind fails with the re-record instruction.

**Evidence:** CI, step "Run the wasm module against the committed fixtures":

```
ok: loaded geese-seed7.replay,   advanced 300 frames (1377839 packet bytes, heap 16 MB)
ok: loaded royale-seed42.replay, advanced 300 frames (1362428 packet bytes, heap 16 MB)
ok: loaded tron-seed13.replay,   advanced 300 frames (1405743 packet bytes, heap 16 MB)
```

## F15 — three missing tools, and design test 38

All three carried over from `coworld-ctf`; `check_gameversion.sh` takes one named edit (`CONST_FILE`
→ `src/snake/sim_types.nim`) and is committed executable, the other two are unchanged. `GameVersion`'s
rule headline moves onto its declaration line, which is the string that script compares.
`ci.yml` gains a PR-only `gameversion-tripwire` job, a step that runs the platform's own
`_load_template_manifest` → `validate_upload_manifest` over the manifest, and the version picker's
self-test.

**Evidence:** CI `test` job:
`manifest validates under coworld 0.1.43: snake-royale 0.1.0 ['royale', 'geese', 'tron']` and
`test_next_coworld_version: all assertions passed`.

## F16 — the tool's docstring described a file it never wrote

Docstring corrected to the tool's real contract (re-derive the inherited head so the inheritance can
be diffed), both outputs named, the diff command printed with the byte count filled in, and the
scratch files moved out of `client/` — which the Dockerfile copies wholesale into the image — into
the already-gitignored `dist/replay-page-provenance`.

## F17 — the 720 s envelope

**Fixed on its merits.** The episode clock now starts *above* `waitForLobby`, so
`wallClockBudgetSeconds = 640` covers the lobby **and** the loop and the budget guard's `elapsed` is
the real elapsed time. Worst case: 640 + 11 (the turn in flight) + 1 (the display hold) + 20 (the
shutdown grace) = **672 s**, inside the 720 s envelope with 48 s spare, against ~720 s exactly
before. And the post-settle order now matches §End conditions: the `gameOverTurns` display hold runs
**before** the artifact writes, with the bounded shutdown grace still after them.
`tests/test_snake_llm.nim` does the arithmetic out loud and asserts both orderings in the source.

## F18 — the panel was removed, its wiring was not

`broadcast_core.js`'s no-op `zoomAt/setZoom/panBy/panByMap/panTo/resetView/attachMinimap`,
`static_replay.js`'s minimap handshake and six view forwarders, and
`static_replay_worker.js`'s `minimapSurface` and `view`/`minimap` branches are all deleted
coherently, so nothing calls a method that is gone. The shell keeps exactly what the page calls: the
**board** canvas transfer, `start/stop`, `sendCommand`, `clickMap`, `setViewportFit`, `getTransform`.
Re-run in headless chromium after the deletion: loaded, 72 strings drawn, 0 outside.

## F19 — two re-labels with no shipped string

The endcard now opens with the winner's headline pair in the starter's own `ec-lives` / `fl-num` /
`fl-cap` shape — the structure the mapping table re-labels — carrying `Turns survived` and
`Final length`, filled from the results document. Pinned at exactly one occurrence each by
`test_snake_endcard_labels.nim`, and asserted in a real browser by the renderer fixture (both
captions present, both numbers the winner's).

## F20 — REFUTED

The finding is that `drawLengthRibbon` is listed in design §Chrome provenance (design.md:1053) as an
added function and does not exist. It does not exist because the note contradicts itself and the
implementation follows the other half: §Readouts 7 (design.md:1157) specifies the ribbon as *"the
starter's `#momentum` SVG retargeted … drawn full width from the pre-scan on the first frame"*, and
that is what ships — `<svg class="momentum" id="momentum">` at `replay_broadcast.html:1033`, fed by
`chrome_common.js`'s `ingestLeadSeries`/`renderMomentum` from the `lead` field
`broadcast.nim:76-82,119` builds at full width on frame 0. A canvas `drawLengthRibbon` would be a
**second** ribbon implementation drawn over the SVG one.

The repo is internally consistent about this: `broadcast_core.js`'s header lists the added draw
functions and does not claim `drawLengthRibbon`, and `tests/test_snake_viewer.nim` asserts exactly
the functions that exist. As of this round the ribbon is also *exercised*: the renderer fixture
feeds `lead.pts` at full width and fails the step if `#momentum` draws no path (F5).

No code change: implementing the note's function name would add a duplicate renderer to satisfy a
sentence the note's own §Readouts contradicts.

## F21 — forager was never in the swept matrix

The matrix now crosses forager's `spaceWeight` (both 40 and the note's 400) with the coil matrix:
36 rows, every one printed by `--sweep`, which `ci.yml` runs on every push. The shipped pair is the
best row of all 36 (+0.1805 at forager 40 / coil 100-2-100; the best row at forager 400 is +0.1667).
Forager's other five knobs stay the note's and are deliberately not optimised — it is the player a
champion should be able to beat, so tuning it for the margin would measure the wrong thing — and
both `baselines.nim` and the recorded JSON say so. Test 27 asserts every shipped swept knob is a
value the matrix contains and that the shipped pair **is** the recorded best row.

## F22 — the file the note names now exists

Numbered block 15 moved from `tests/test_snake_sim.nim` into `tests/test_snake_scoring.nim` — one
copy, not two — and `tests/shard_1.nim` imports it beside the sim, so both readings of the note hold
and `ci.yml`'s `tests/*.nim` sweep picks it up.

## F23 — the smoke replay is named for its bytes

`ci.yml` sets `SMOKE_REPLAY_OUT=dist/smoke/episode.replay`. The shared script is unchanged — it
already takes the path from the environment — and the viewer step's candidate loop globs
`dist/smoke/*.replay` first.
**Evidence:** CI docker-smoke: `replay saved for the viewer smoke: …/dist/smoke/episode.replay
(20945 bytes)`; wasm-viewer: `loading dist/smoke/episode.replay in dist/static-replay-viewer`.

## F24 — the tier-2 stream now speaks its own vocabulary

`events.nim` declares `SimEventKind`, the note's fourteen tier-2 kinds, with a `key()` wire mapping
in the starter's shape, and maps the broadcast events onto it: `gamestart`, `spawn` and `end` are
dropped (the replay config already carries the module and the spawn deal; the results document
already carries the reason), and `directive` rows are emitted from the decision layer — a directive
is a fact about the DECISION, so no `TurnEvent` can carry it without making the broadcast enum
seventeen kinds and breaking its own closed contract. A turn's directives precede that turn's board
events. The mandatory summary row is unchanged and now counts the rows it summarises.

## F25 — `feed_lines: 0` was the harness's selector, not the viewer

**Cause determined.** `viewer_smoke.mjs` reads the match feed through
`document.querySelector("#feed, .feed, #log")`; this game inherited the starter's `#killfeed` id,
which matches none of the three, so the number was 0 whether or not a row had been drawn — it
covered nothing. `viewer_smoke.mjs` is the shared template copied verbatim, so the fix is on this
side: `#killfeed` carries `class="feed"`. No CSS rule selects `.feed` (the rows are `.feed-row`), so
nothing renders differently.

**Evidence:** `viewer-smoke.json` on this head reports **`"feed_lines": 8`** (post-soak readout,
around turn 20 of 40); it was `0` on every previous run.

---

## NOTED (not fixed)

- `tools/ci/viewer_smoke.mjs` cannot see a Worker's `OffscreenCanvasRenderingContext2D`, so the
  shipped bundle's own text is measured by nothing. The renderer fixture covers the same renderer on
  the main thread and the split is documented and pinned (F5), but instrumenting the worker would
  need a change to the shared template — a coworld-builder change, not a repo change.
- `viewer-smoke.json`'s `feed_lines` is *reported*, not gated (the harness decides that, not the
  repo). It is now a real number.
- The design note's `[+0.30, +1.20]` margin band for test 27 is unreachable in the swept matrix
  (best +0.1805 on an unbiased ladder). The note is the run's record and was not edited; the
  measurement is recorded in `tools/ci/baseline_tuning.json` and in F2 above.

---

Final `main` sha: **`d8652fa2d92b14a6da207d71076027f806f7849e`**
Final CI run: **33149313876** — conclusion **`success`**
(<https://github.com/Metta-AI/cogame-snake-royale/actions/runs/33149313876>)
