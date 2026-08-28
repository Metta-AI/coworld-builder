# r1 fixes — sumo-traffic-signals

Head: `e20601afffcf2e5b5ae7edc1341c2a50912634d9` (main)
CI: https://github.com/Metta-AI/cogame-sumo-traffic-signals/actions/runs/33193230780 — **success**
(event `push`, head_sha `e20601a…`; jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; every step
`success` except the PR-only "Check the GameVersion has not collided", which is `skipped` on a push,
exactly as at the reviewed sha)

Base: `54fd04080b0c2e75275b5ada197b431fa6dc3023`. Sixteen commits, one per finding, pushed as one
ref update (the sandbox cannot `git push`; the chain went up through the Git Data API, blobs → tree →
commit per local commit, ref moved once at the end, so history keeps one commit per finding and CI
ran once, on the head).

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `033b3c7` | tests/test_signals_engine.nim:116-158, tests/test_signals_viewer.nim:93-121 |
| N1 | fixed | `a9a8c8c` | tools/ci/renderer_fixture.html:58-64,118-158,211-219,305-311 |
| N2 | fixed | `69ba216` | src/signals/server.nim:551-597, tools/ci/docker_smoke.sh:307-317 |
| N3 | fixed | `6ed6341` | src/signals/decide.nim:158,224-239 |
| N5 | fixed | `8731116` | src/signals/decide.nim:293-305 |
| N6 | fixed | `d79ad59` | src/signals/sim_types.nim:279-295, src/signals/llm.nim:193-197, tests/test_signals_driver.nim:235-256 |
| N11 | fixed | `1da1cbc` | src/signals/vehicles.nim:201-216 |
| N12 | fixed | `0712e1d` | src/signals/replays.nim:207-213 |
| N13 | fixed | `419ff7a` | coworld_manifest_template.json:93,206,281,308, tests/test_signals_manifest.nim:34-50 |
| N14 | fixed | `ef75566` | src/signals/global.nim:57-62,212-252,313-321, src/signals/flow.nim:186-188, src/signals/sim_state.nim:75-84, tests/test_signals_viewer.nim:230-270 |
| N15 | fixed | `2dcb1ae` | src/signals/rig_art.nim:152-179,198-209,377, tests/test_signals_viewer.nim:301-317 |
| N18 | fixed | `c951f2f` | src/signals/sim_state.nim:80-84, src/signals/flow.nim:186, src/signals/broadcast.nim:207-216, tests/test_signals_sim.nim:530-541 |
| N19 | fixed | `f15c2c7` | tools/page_sig_block.html:435-441, client/replay_broadcast.html |
| N20 | fixed | `ad80f42` | tools/page_sig_block.html:479-491, client/replay_broadcast.html |
| N21 | fixed | `1d04957` | src/signals/roster.nim:82-100, src/signals/server.nim:505-541, tests/test_signals_engine.nim:194-220 |
| N4 | won't fix | — | src/signals/decide.nim:284,309 |
| N7 | won't fix | — | src/signals/decide.nim:200-215,249-250 |
| N8 | not a defect | — | src/signals/phases.nim:76-104 |
| N9 | not a defect | — | src/signals/driver.nim:53-66,104-112 |
| N10 | won't fix | — | src/signals/phases.nim:141,156 |
| N16 | NEEDS-DESIGN | — | src/signals/rig_art.nim:330-332 |
| N17 | won't fix | — | src/signals/rig_art.nim:152-192 |
| N22 | not a defect | — | src/signals/server.nim:42,152-155 |
| N23 | not a defect | — | client/replay_broadcast.html:1863-1993 |
| N24 | won't fix | — | tools/ci/viewer_smoke.mjs |
| N25 | not a defect | — | tools/replay_summary.py:154-171 |
| N26 | not a defect | — | .github/workflows/ci.yml |
| N27 | won't fix | — | src/signals/llm.nim:236 |
| N28 | partly fixed | `033b3c7`, `d79ad59`, `1d04957` | see below |
| N29 | partly fixed | `419ff7a` | see below |

One extra commit, `e20601a` ("keep the two new comments out of expression position"), is a
fix-forward on my own N12/N18 commits: both had a `##` comment in a position Nim's parser treats
specially (inside a `%*{…}` table constructor, and indented under an assignment). No behaviour
change; it is called out here rather than folded silently into either fix.

---

## B1 — Two assertions were removed or narrowed during this run — **fixed**, `033b3c7`

The review is right on both hunks, and both are restored at full strength rather than argued.

**Hunk 1, the deleted `check sim.greenWaves >= 1`.** I took shape (a): the assertion moves to a
scenario that can carry it, and the seed-42 congestion assertions stay exactly as they are (all four
of them, plus the four-way `phaseChanges` loop). New suite `coordination raises a green wave`
(`tests/test_signals_engine.nim:116-158`) drives the design note's test 13 **end to end through the
real engine**: row A's four signals start on the cross phase, the seat's orders are `wave EWG` with
rising delays (A1/A2 at +0, A3 at +2, A4 at +4 — coordinated offsets, each green arriving ahead of
the platoon), a seven-car platoon is placed along the corridor, and 36 real `stepTick`s run. The
signal machine's `minGreenTicks`, the two-tick all-red clearance, the one-car-per-approach discharge,
the clean-crossing rule and the wave window all have to agree for the assertion to pass:

```
check sim.greenWaves >= 1
check corridors[0].startsWith("A")      # the corridor the wave names
check corridors[0].contains("eastbound")
```

Evidence, from the green run's `test` job log (both the debug and the `-d:release` pass print it):

```
coordinated corridor: tick 36/256 turn 1/32 through 7 demand 0 on-net 0 queued 0 wait 20
                      spillback 0 gridlock 0 waves 1
```

`waves 1` is the restored assertion firing on the real engine. The cert-fixture test's own line is
unchanged in the same run (`cert fixture: … waves 0`), which is the honest fact the divergence note
records — and the note in the test now says the assertion *moved*, not that it was dropped.

**Hunk 2, the narrowed alias guard.** `tests/test_signals_viewer.nim:93-121` collects every alias
again — 41 of them, `$` included — and the `if name.len >= 2` filter is gone. The one legitimate
collision is *enumerated*, not skipped by length:

```nim
check "$" in aliases
…
if alias == "$":
  check declarations == 1                                   # exactly one, and
  check block0.find("var $ ") > block0.find("(function () {")  # inside the IIFE
else:
  check declarations == 0
```

`declarations` counts `var <alias> ` **and** `var <alias>=` occurrences, so a second `$` declaration,
or the same trick for any other alias (one-character or not), fails the test. I verified against the
shipped page that `$` is the only alias the game block re-declares: parsing the page's alias block
and scanning the appended region finds exactly one collision, `var $ ` at
`client/replay_broadcast.html:2407` (`tools/page_sig_block.html:262`), inside the block's IIFE.

Checklist item satisfied: **1**, both halves — CI green on `main` at the head sha with no test
disabled, skipped or loosened; the two hunks the reviewer cited are stronger than before the run
(one assertion became a whole end-to-end test, and the alias domain went from 40 aliases to 41 with
an exact-count check instead of a presence check).

---

## N1 — the fixture's "full-cap 120-rune say" was 109 runes and never asserted — **fixed**, `a9a8c8c`

Two defects, both fixed:

1. The string was 109 runes, so `SAY = Array.from(SAY).slice(0, 120).join('')` was a no-op and the
   fixture, `ci.yml`'s step comment and the design note all claimed a cap the fixture never reached.
   It is now exactly 120 runes with the 4-byte 🚦 as rune 120, and the fixture **asserts its own
   length** before it drives anything (`data-replay-error` and exit 1 otherwise).
2. Worse, and not in the review: the four `say` events were pushed in the same frame as the city's
   events, and `#killfeed` keeps `MAX_FEED = 4` rows, evicting the oldest. Every radio line was gone
   from the DOM before `transcribe()` ran — the fixture that exists to gate the radio-text path drew
   **no radio line at all**. The says are now driven in their own frame, last, so all four rows
   survive, and the fixture asserts the chrome rendered four text nodes carrying the string **in
   full** before transcribing them.

Evidence: I reproduced the fixture locally against the shipped page (a stand-in bundle built with the
Dockerfile's own `sed`, served by `tools/ci/serve_bundle.mjs`, driven by `tools/ci/viewer_smoke.mjs
--strict-text-bounds` under Playwright) — before: 600 runs, no say among them; after: 618 runs with
`full-length say text nodes: 4` at each of 360/620/900 px, the line drawn at x=55.8 w=234.2 on a
360 px canvas (right edge 290 < 360). CI agrees, in the "Drive the shipped page with a worst-case
renderer fixture" step of run 33193230780:

```
canvas text: 618 drawn, 0 never inside the canvas (0 draws crossed an edge), 48 ellipsized
```

618, not 600: the four full-cap remarks per width are now measured, and `never_inside` is still 0.

Checklist item satisfied: **15** — "The fixture asserts its own strings are still full-length", and
the gated `never_inside` now actually covers the remark path it was written for.

---

## N2 — the `fault` end reason could not be produced — **fixed**, `69ba216`

Nothing caught an exception around the episode loop, so an unexpected one propagated, the process
exited non-zero and no `results.json` was written — the opposite of the note's "caught; the episode
is settled from the last completed tick … artifacts are still written, exit 0", and the note's
three-value `reason` enum was two in practice.

The play loop now runs inside `try` / `except CatchableError` (`server.nim:551-597`). On a fault the
episode is settled with `applyStop(erFault, "unexpected exception in the episode loop: …")` from the
last completed tick, the stop record is written to the replay through the same `stopRecord` path the
wall-clock stop uses, and the existing settle/results/artifact/grace path below still runs. Exit code
stays 0, so the episode remains rankable. `tools/ci/docker_smoke.sh:307-317` is what makes it red: it
now fails the build when the smoke episode reports `reason` or `endRule` == `"fault"`, which the note
names as a defect and the script previously only printed.

Evidence: `docker-smoke` step "Raw-Docker episode smoke" in the green run prints
`episode end reason: complete` / `smoke OK: seats=4 results=960B replay=73396B reason=complete` — the
new guard is live and the healthy path is unaffected.

---

## N3 — the retry could be pre-empted by the turn budget — **fixed**, `6ed6341`

`turnStart` was taken at the top of `turn()`, ahead of the budget guard, the rate guard and the
up-to-12 s spacing sleep, so a turn that slept ~9 s for spacing and then spent attempt 1's 9 s was
already past the 14 s deadline: the loop broke before the retry batch and wrote a `timeout` fallback
reading "per-turn budget exhausted before attempt 2". The budget clock now starts after the spacing
sleep, where the calls do (`decide.nim:224-239`, `callsStart`).

The turn stays bounded — spacing (≤ `turnSpacingMs`) then calls (≤ `turnBudgetMs`) — and the
wall-clock arithmetic is unchanged, because `turnSpacingMs` is a floor between batch **starts** and
shrinks by exactly what the previous turn's calls took; `tests/test_signals_engine.nim`'s
`32 turns × max(spacing, budget) + 120 < 660` pin still holds and still passes.

Checklist item satisfied: **8** ("retries once on a parse or transport failure" — the retry is now
reachable on a spacing-bound turn) without weakening **5**.

---

## N5 — attempt 2 logged both "will retry" and "falling back" — **fixed**, `8731116`

The `attempt N failed, will retry` echo ran for both attempts. It is now attempt 1's alone; attempt
2's failure logs without the promise, and the `falling back` line below stays the single phrase
phase 60 greps the game log for (the pommerman 0.1.1 scar the note names).

---

## N6 — the 4096-**byte** provider cap was a rune cap — **fixed**, `d79ad59`

`textOf` compared bytes and cut runes, so a reply of 4-byte runes survived at ~16 KB. New
`truncateBytes` (`sim_types.nim:279-295`, beside `truncateRunes`, the only other place a recorded
string is shortened) cuts to at most N **bytes** while still landing on a rune boundary, and `textOf`
uses it. Test 21 now feeds 8000 🚦 and asserts the result is exactly 4096 bytes, 1024 runes and
`validateUtf8() == -1` — the assertion the old test could not make, because it only exercised ASCII.
Checklist item **9** is strengthened, not touched: nothing is cut mid-codepoint.

---

## N11 — `stops` was not counted in a gate queue — **fixed**, `1da1cbc`

Tick step 8 applies the stop rule to "every car still on the network (link cell **or gate queue**)";
the gate branch charged wait ticks and never incremented `stops`, so `stopsTotal` — the number the
endcard divides into stops-per-car — missed every stop made outside the city. The gate branch now
applies the same `movedLastTick and not movedThisTick` rule. `stops` is measured, never scored and
**never mixed into the game hash** (`mixTick` mixes `link, cell, waitTicks, cleanCrossings,
blockedByPhaseTicks`), so no replay hash and no seeded assertion moves — confirmed by the green
replay re-derivation tests and by the unchanged smoke figures (`throughput 217`, same 73 396-byte
replay).

---

## N12 — playback opened at speed 2 — **fixed**, `0712e1d`

`initReplayPlayer` opened at `speedIndex = 1` (speed 2, 24 ticks/s), so the 256-tick smoke replay ran
out in ~10.7 s against `--soak 10`: CI observed 12 ticks of margin. It now opens at speed 1 — one
tick per `FramesPerTick` frames at `TargetFps`, 12 ticks/s, ~21 s for 256 ticks, which is what
`replays.nim:38`, `replay_runtime.nim:61` and `tests/test_signals_engine.nim` all already claimed.

Evidence, "Load the bundle in a real browser" in the green run:

```
soak: 10s of playback kept advancing ("1 / 256" -> "97 / 256" -> "121 / 256")
```

135 ticks of headroom instead of 12.

---

## N13 — `results.variant` was always `grid4x4` — **fixed**, `419ff7a`

No variant's `game_config` carried a `variant` key and `sim_config` defaults it, so a hosted
`rushhour` episode wrote `"variant": "grid4x4"` into `results.json` and into the replay's config
JSON. Both variants and the certification fixture now name themselves, and `variant` is declared in
`config_schema` (`additionalProperties: false` means an undeclared key would be rejected outright —
declaring it is part of the fix, not decoration). `tests/test_signals_manifest.nim:34-50` pins that
every variant's `game_config` resolves through `config.update` to its own id, that the cert fixture
says `grid4x4`, and that the schema declares the property. Checklist item **10** is unaffected and
still green.

---

## N14 — the board never drew the green-wave sweep — **fixed**, `ef75566`

`WaveSpriteId`, `WaveObjectBase` and `bakeWaveChip` existed and nothing placed a wave object, so
`labels.nim`'s `wave` label — pinned in `tests/label_manifest.txt` — was a label the compositor could
not emit, and the idea's own "green-wave visualisation" was a banner and a tally with nothing on the
board.

`creditCorridor` records the tick a corridor's wave fired (`sim.waveFlashTick`, presentation state,
deliberately **not** mixed into the game hash, so replay re-derivation is untouched), and
`buildBoardPacket` runs a bright band down that corridor's lane in the direction of travel over
`WaveFlashTicks = 8`: entry link, three blocks, exit link, via the new `corridorLinkPath` /
`waveSweepCells`. `tests/test_signals_viewer.nim:230-270` pins that the band moves downstream every
tick, covers the whole 26-cell lane and nothing else, and is gone once the flash is spent.

---

## N15 — the quadrant corner drew a row letter — **fixed**, `2dcb1ae`

`bakeCityBed` drew `intersectionName(firstAt)[0]`: "A" for both Alpha (A1) and Beta (A3), "C" for
both Gamma (C1) and Delta (C3). The corner now draws the **owner's alias initial** — A, B, G, D —
derived from `seatAlias`, in the owner's tint, with a `G` added to the 3×5 glyph table for Gamma.
The alphabet stays closed (`A B C D G 1 2 3 4`), which is the last line of the two-name-space rule:
`tests/test_signals_viewer.nim:301-317` asserts each corner glyph equals its alias initial, that the
four are distinct, that the board can draw each of them, and that no character of `daveey` can be
drawn at all. Checklist item **4** is unchanged and still holds.

---

## N18 — the corridor tally's `waves` dropped to zero on a wave — **fixed**, `c951f2f`

The tally read `waveTicks[bucket].len + waveTicks[bucket+1].len`, the in-window **credit** list,
which `creditCorridor` clears the moment a wave fires — so the bar fell to zero at exactly the moment
the note says it increments. `sim.waveCounts` now counts waves per corridor and direction and the
tally reads it; `tests/test_signals_sim.nim:530-541` pins the per-corridor count and the identity
`sum(waveCounts) == greenWaves`.

---

## N19 — par rode a tooltip — **fixed**, `f15c2c7`

`#clock` read `THROUGH 206` with par on the `title` attribute only, so the one number that says
whether the city is winning (`throughput >= par` is the win flag for all four seats) was invisible.
The big numeral now reads `THROUGH 206 / 260 PAR`; the caption keeps demand / waiting / spillback /
gridlock / waves, and the inherited `#tick-clock` keeps `tick / 256`.

Evidence, from the green run's viewer smoke readout:
`"clock":"THROUGH 69 / 260 PAR DEMAND 240 · WAITING 7307 · SPILLBACK 3 · GRIDLOCK 0 · WAVES 0"`.

The remaining layout divergence — the note's separate `/ 260 par` sub-line and `tick 241/256 · turn
31/32` in `#clock-time` — would need a new element inside the inherited `#clock` markup; the
substance (par on screen, next to the number it gates) is fixed without touching the starter's
chrome.

---

## N20 — a column corridor's wave banners as a row — **fixed**, `ad80f42`

`broadcast.nim` emits `corridor` as `A`..`D` for east-west and `1`..`4` for north-south, and the page
prefixed both with "row", so a northbound wave banners as `ROW 2 NORTHBOUND WAVE` and its scrubber
beat read "green wave on 2". The block picks the word from the corridor id (letter → row, digit →
column) in both the banner and the beat label.

`client/replay_broadcast.html` is regenerated with `tools/fork_broadcast_page.py` from the starter's
page plus the block — the page still reproduces byte-for-byte from those two inputs, which is what
checklist item **14**'s provenance argument rests on — and `tools/check_broadcast_page.py` and the
jsdom page smoke both pass (`{"ok":true,"plates":4,"beats":10,"feed":4,"sent":["t:0"]}`).

---

## N21 — the server did not refuse to start on an unregistered seat — **fixed**, `1d04957`

The server logged the grf-football warning loudly, marked the seat dead, declared the player
failure — and then played the whole episode anyway with that seat on the published default. The
note's edit 2 and its test 26 both say the server "refuses to start the game".

`roster.refuseToStartDetail` is now the predicate: non-empty only for a seat that **joined** and
never registered. A seat that never connected at all is deliberately not this case — §Degrade says
that one plays greedy and the episode runs to its end, so that path is untouched. `runServerLoop`
settles on `fault` with that detail *before* it ever sets `phase = Playing`; it is a settled episode,
not a crash — the stop record, `results.json` and the replay are all still written, the process still
exits 0, and `docker_smoke.sh` (N2) turns the resulting `fault` into a red build.
`tests/test_signals_engine.nim:194-220` drives the real predicate (not a literal payload): four
registered seats → empty; one joined-but-unregistered seat → named in the detail; a never-connected
seat → empty; and the refusal settles as `fault` with a `results.json` that parses and carries the
detail.

---

## N28 — assertions narrower than the note says — **partly fixed**

- Test 25's wave assertion: fixed, end to end (B1, `033b3c7`).
- Test 21's 4096-byte cap: fixed — it now exercises the real byte cap with 4-byte runes (`d79ad59`).
- Test 26's "server refuses to start": fixed — it now drives the shipped predicate (`1d04957`).
- The remaining three (test 36's byte-comparison against a starter that is not vendored, test 12's
  constructed ring, test 13's conditional final assertion, test 8's latch length, test 18's
  orders-array bound) are **not fixed**: none is a checklist item, and each would need either a
  vendored starter copy in the repo or a rewrite of a passing test whose current assertions are
  correct as far as they go. Recorded, not argued away.

## N29 — smaller notes — **partly fixed**

- `config_schema` declaring `speed`: intentional (the replay speed is a config knob); `variant` is
  now declared alongside it (`419ff7a`), which was the real gap.
- Gate-pip id collision above `gateQueueCap = 16`: the shipped value is 12 and `sim_config` clamps to
  64, so a config between 17 and 64 would collide pip ids across gates. Left as is — it is a
  presentation id space, not a rules or determinism defect, and no shipped or schema-reachable
  configuration reaches it. **NOTED, not fixed.**
- Radio block iterating seats in ascending slot, `sanitizeLine` dropping braces, the player's inner
  receive loop, the derived gridlock event's emit-time links: all cosmetic or bounded as the review
  itself concludes. Not fixed.

---

## Findings I did not change the code for

**N4 — the fallback `cause` vocabulary.** Real divergence, deliberately not "fixed". The code emits
`throttled` (a provider 429 with no other candidate model), which the note's enum omits; the note
lists `disconnected`, which the code never emits. Both are correct as shipped: `throttled` is a
distinct, actionable cause that `docs/SIGNALS.md:145` already documents as part of this game's
vocabulary, and collapsing it into `transport_error` would lose the one signal phase 60 needs to tell
"the provider refused us" from "the network failed". `disconnected` is unreachable **by
construction**: the game pod makes the LLM calls itself (`decide.nim:239-256`), so a seat's socket
dropping cannot fail a decision — it makes the seat dead, which is `deadSeats`, not a fallback cause.
The honest statement is that the note's enum is one value short and one value long, not that the code
is wrong. Won't fix.

**N7 — the rate guard is checked once per turn.** Real, and bounded to a 4-request overshoot in the
worst turn (8 requests issued, 4 checked). Not fixed, because the *accounting* is already honest:
`decide.nim:249-250` stamps **every** request, including the retry batch, so the trailing-60 s window
the next turn checks against includes them and the guard self-corrects on the following turn. A
mid-loop re-check would have to drop seats to greedy between attempt 1 and attempt 2 — new fallback
behaviour inside the most delicate loop in the repo, for a transient overshoot of 32/28 that no
provider limit in play here notices. Won't fix; recorded for the judge.

**N8 — clearance timing.** Not a defect. The implementation satisfies the note's own stated invariant
("every change costs **exactly** `clearTicks` of all-red with no discharge") and its `phasechange`
timing; the "3 ticks" reading comes from reading steps 2b/2c as separate ticks, which the note's
invariant contradicts. `tests/test_signals_sim.nim:266-292` pins `flippedAt == clearTicks`. No change.

**N9 — `greedy`'s hold rule at the boundary.** Not a defect in the code: the review establishes the
note is internally inconsistent (§Scripted baselines rule 1 vs §The driver vs test 20's "one
implementation"), and the code implements the reading that keeps `auto` and `greedy` a single proc,
which is what test 20 and checklist item 8's shared-fallback requirement need. Changing it would
either fork the two controllers or change every swept tuning number. No change.

**N10 — `blockedByPhaseTicks` accumulates rather than counting consecutive ticks.** Real, and
deliberately not fixed. `blockedByPhaseTicks` **is mixed into the game hash**
(`sim.nim` `mixTick`, per live car), so resetting it on a spillback-blocked tick changes every
recorded hash, the swept baseline tuning input, and the seeded fixture assertions this very round is
required to keep passing (`spillbacks >= 1`, `starvations >= 1`, `crossings > throughput`,
`phaseChanges[slot] > 0` on seed 42, plus test 23's greedy-vs-fixedcycle wait comparison). I cannot
compile or run the engine in this sandbox, so I cannot show those still hold, and the deviation makes
the starvation override marginally **more** eager, never less — the override stays bounded, latched
for `minGreenTicks`, and safe. This is the one finding where the smallest correct change is larger
than the round: **NEEDS-DESIGN if the judge wants it**, with the fix being one line
(`sim.cars[car].blockedByPhaseTicks = 0` in `phases.nim`'s spillback-refusal branch) plus a re-run of
`tools/tune_baselines.nim` and a re-check of every seeded fixture number.

**N16 — `.tiny` intersection labels.** NEEDS-DESIGN. The labels are baked into the one-time static
bed (`rig_art.nim:330-332`, shipped as four fixed sprites), so "only the four corner intersections
under `.tiny`" needs a **second baked bed** and a sprite swap on the `t:` command — a new sprite
family and a second bake pass, not a local edit. The car-dash half of the rule is implemented and
works. Not attempted this round.

**N17 — labels use a hand-rolled glyph table, not `data/font.ttf`.** Won't fix, and the reason is a
checklist item: the 3×5 table is a closed alphabet, which is what makes "a real player name cannot be
drawn on the board" a structural guarantee rather than a convention (item 4, and
`tests/test_signals_viewer.nim` now asserts it explicitly — see N15). Typesetting with pixie would
also add a runtime font-file dependency to the wasm bake, where the bed is rebuilt in the browser.
The note's parenthetical is the divergence; the code is the safer half.

**N22 — `/client/replay` exists as a local route.** Not a defect. The manifest declares only
`"replay_viewer": {"bundle": "static-replay-viewer"}`, the release workflow's guard rejects a
pod-served viewer, and the note explicitly keeps the local developer route ("the game still serves
`/client/replay` locally for developers"), exactly as the starter does. Removing it would delete a
documented developer affordance to satisfy a string match. No change.

**N23 — zoom gesture handlers survive `#viewpanel`'s removal.** Not a defect on the reading the note
takes: the *panel* — markup, CSS, ids, buttons, slider, `core.attachMinimap(...)` — is gone (0
occurrences of `viewpanel`/`zoombar`/`zoom-*`/`fpv*`/`povBadge`), and the surviving keyboard/wheel/
pinch handlers are the starter's own gesture path, which `syncViewUi` keeps deliberately. Deleting
them would edit the inherited region beyond the note's removal list, which item 14 treats as the
graver sin. No change; the judge's call, as the reviewer says.

**N24 — `viewer_smoke.mjs` is not the current template.** Not fixed **by design of the checklist**:
item 13 requires the smoke to run and report, and the 30 lines of difference are lineage-selector
*fallbacks* added to the template later for pages that do not use `#clock`/`#scorebug`/`#scrub`. This
page uses exactly those ids and CI reported real values for all three. Re-copying the template mid-
round would swap the one tool the acceptance evidence is read from, on a round whose job is to keep
CI honest. Recorded for phase 40.

**N25 — `policyKinds` has 12 entries; `names` are aliases.** Not a defect in the game: the player
re-sends its registration up to 10 times by design and the server writes a fresh `register` record on
every drain, which is the audit trail the note asks for. `replay_summary.py` reports what the replay
contains. The phase-60 recipe the note documents works, as the reviewer verified. No change.

**N26 — the claimed `ctf_`/`CTF_` CI grep does not exist.** Not a defect: the note describes a check
that was never required by the checklist, and the only `CTF` string in the tree is
`window.CTF_WIRE`, which exists **because** `chrome_common.js` is byte-identical to the starter's —
the thing item 14 actually requires. Adding a grep that must then exempt its own reason would be
theatre. No change.

**N27 — one reworded line in the system prompt.** Won't fix. The line is semantically identical (a
semicolon became a comma and "block" is elided once), both champion `PLAYER_PROMPT` texts are
byte-identical to the note, and editing the shipped system prompt to match punctuation would change
every LLM episode's inputs for no behavioural gain. Recorded.

---

## NOTED (not fixed)

- `ci.yml`'s "Load the manifest under the installed coworld CLI" step prints a pydantic
  `ValidationError: game.version Field required` and exits 1 — but the step is
  `continue-on-error: true`, so the job stays green. **This is pre-existing**: the identical error is
  in run 33187823599 at the reviewed sha (16:01:19Z). It is the CLI's author-manifest model wanting
  `game.version`, which the repo's manifest test deliberately omits ("no top-level version"). Worth a
  decision in phase 40; not this round's scope, and not caused by the N13 `variant` addition (the
  error names `game.version` and nothing else).
- `PlaybackSpeeds = [1, 2, 4, 8, 16]` still differs from the note's `[0.5, 1, 2, 4, 8]` chips, and
  `TargetFps = 24` from the note's 30. Both are forced: the sim is integer-only, so a 0.5× chip
  cannot exist in this speed table, and 24 fps is the starter's. N12 fixes the part that mattered —
  the *default* — and every comment in the tree now agrees with the code.
- The renderer fixture's `transcribe()` still re-ellipsizes a run its own container clips. That is
  deliberate and documented in the file; with the say rows now actually present, the gated
  `never_inside` covers them and is 0 at all three widths.
