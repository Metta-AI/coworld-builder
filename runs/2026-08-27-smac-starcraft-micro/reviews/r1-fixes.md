# r1 fixes — smac-starcraft-micro

Head: `84b271b85f8f809699a90adbc89a538e59013f0f` (main)
CI: https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33055917137 — **success**
(run 33055917137, push, head `84b271b8`; jobs `test` success, `docker-smoke` success,
`wasm-viewer` success — including `Load the bundle in a real browser`, `Native-to-wasm
determinism gate` and the new `Worst-case renderer text fixture`.)

Range: `190ef840..84b271b8`, 19 commits, one finding per commit (a finding whose first
attempt CI rejected has a further `(fix forward)` commit naming the same finding — the
measurements CI produced are quoted in each).

| finding | disposition | commit(s) | files |
|---|---|---|---|
| B1 | fixed | `4b20af5b` | `src/smac/scenario.nim:324`, `src/smac/server.nim:2108`, `src/smac/replays.nim:545` |
| B2 | fixed | `a33283d8`, `b8e8a9cd` | `tests/test_replay.nim:116`, `tests/smac_helpers.nim:85` |
| B3 | fixed | `ea1b5476` | `src/smac/replays.nim:43`,`:269`, `replay-viewer/smac_replay.nim:126`, `tools/wasm_replay_smoke.cjs:113`, `.github/workflows/ci.yml:384` |
| B4 | fixed | `231d17a2`, `ebdb24c9`, `07be875c`, `b8f0232d`, `ed860e5d` | `tests/test_control.nim:247`, `src/smac/baselines.nim:99`,`:178`,`:219`, `src/smac/control.nim:397`, `docs/RULES.md:225` |
| B5 | fixed | `369e138c` | `client/replay_broadcast.html:4220`, `tests/test_viewer.nim:112` |
| B6 | fixed | `b7fd54e9` | `client/replay_broadcast.html:4131`,`:4287`, `tests/test_viewer.nim:102` |
| B7 | fixed | `34f0529b`, `ec10b24a`, `84b271b8` | `tools/record_text_fixture.nim`, `replay-viewer/text_fixture.html`, `tests/test_shouts.nim`, `src/smac/global.nim:3975`,`:4091`,`:4995`, `replay-viewer/{config.nims,smac_replay.nim}`, `Dockerfile.replay-viewer:31`, `.github/workflows/ci.yml:164`,`:405` |
| B8 | fixed | `6834fc72` | `tests/test_replay.nim:90` |
| N9 | fixed | `77dd50da` | `src/smac/replays.nim:607`, `client/replay_broadcast.html:4460` |
| N7a | fixed | `1b7c1f0d` | `client/replay_broadcast.html:654` |
| N5 | fixed | `640d32a7`, `d8cc97ad` | `src/smac/sim_types.nim:814`, `src/smac/directives.nim:214`, `tests/test_directives.nim:58` |
| N1 | DISPUTED (as a defect) | — | `src/smac/decide.nim:455` |
| N2,N3,N4,N6,N7,N8,N10–N17 | deferred (advisory) | — | see §Advisories |

---

## B1 — `battleIndex` hashed but written only by the live loop

**What it did.** `sim_state.nim:309` mixes `sim.battleIndex` into `gameHash`; the only write
was `server.nim:2106` (`sim.battleIndex = gamesPlayed`), inside the live tick loop, outside
`sim.step`. Playback set it nowhere, so from the tick after the first battle ended every
re-derived hash differed from the recording by construction — every `maxGames: 3` episode,
i.e. all four shipped variants and the certification fixture.

**What it does now.** The switch lives in ONE proc, `scenario.advanceBattle` (`scenario.nim:324`),
called by the live tick loop (`server.nim:2108`) and by `stepReplay` (`replays.nim:545`) — the
same-proc-on-record-and-playback rule the `stop` record already follows. Ordering is part of
the fix: the live loop writes the ending tick's hash *before* the switch, so playback applies
it *after* that tick's hash check (`stepReplay` keeps `battleEnded` and calls `advanceBattle`
below `checkReplayHash`). Both recording helpers in `tests/` mirror the server through the same
proc. `battleIndex` is still hashed, so the hash still covers battle state; no `GameVersion`
bump is needed because what a recording contains is unchanged.

**Evidence.** CI run 33055917137, `wasm-viewer` → *Native-to-wasm determinism gate*:
`ok: loaded replay.json, played every tick to 1121 in 1119 frames, hash chain clean`.
The same step printed `Replay hash mismatch at tick 319` in run 33046300533. Natively:
`tests/test_replay.nim` → `[OK] replaying the recording reproduces EVERY recorded hash, all 3 battles`.
**Checklist item 2.**

## B2 — no test asserted replay re-derivation

**What it did.** `grep -rn "stepReplay\|initReplayRuntime" tests/` was empty; the closest test
asserted only that the file parsed, and deferred to the wasm gate that B3 shows could not fail.

**What it does now.** `tests/test_replay.nim` re-opens its own recording through the SHIPPED
`initReplayRuntime` (the entry point the wasm viewer uses), steps to the last recorded tick and
asserts the whole chain: `hashMismatchTick == -1`, `not hashValidationFailed`,
`hashIndex == data.hashes.len`, `tickCount == maxTick`, `battleIndex == 3` and
`battlesWon == recorded.battlesWon`. A second test corrupts one recorded hash and asserts the
divergence is reported (see B3).

Two recorder infidelities had to go first, both caught by the new test and both fixed forward
in `b8e8a9cd`: the helper (a) never re-seated the squad between battles, so it recorded ONE
battle and idled through the rest (`resetToLobby` empties the roster) — it now re-seats and
records those joins, as the server does; and (b) called `startGame()` itself, so it ran one tick
ahead of any playback, which rebuilds the roster from the joins and lets `stepLobby` start the
battle. `seatMicroSquad` in `tests/smac_helpers.nim` is now the single definition of "seat the
squad", shared with `newMicroSim`.

**Evidence.** `[OK] replaying the recording reproduces EVERY recorded hash, all 3 battles` and
`[OK] a hash the sim cannot reproduce IS reported, even past playback` (run 33055917137, `test`
job, both debug and release). **Checklist item 2 ("A test asserts it").**

## B3 — the wasm gate could not fail on the divergence it printed

**What it did.** Two independent reasons: `smac_mismatch_tick()` returned the DISPLAY player's
`hashMismatchTick`, while the mismatch was detected by the precompute walk on its private
`scan.builder` (a field nothing copied back); and the gate advanced a fixed 300 frames at 1
tick/frame over a 1121-tick replay, so the display never crossed the diverging tick.

**What it does now.**
* `replays.nim`: the walk publishes into the player's new `scanMismatchTick` (deliberately NOT
  restored from a keyframe — a seek must not erase an integrity verdict), and
  `replayMismatchTick` reports the earliest verdict of both halves. `smac_mismatch_tick()` and
  the chrome's integrity banner (`replay_runtime.nim:101`,`:125`) both read it, so the gate and
  the picture agree.
* Two new exports, `smac_replay_tick` / `smac_replay_max_tick`, let
  `tools/wasm_replay_smoke.cjs` drive playback to the LAST recorded tick and fail if it stalls
  short of it; the trailing ci.yml argument is now a frame-count safety cap (4000), not the
  measurement.
* `AGENTS.md`'s `## OPEN` section is replaced by what was actually wrong (B1 + this).

**Evidence that the gate can now fail:** `tests/test_replay.nim` corrupts one recorded hash 4
entries from the end, asserts the display player has not reached it
(`hashMismatchTick == -1`) and that after the walk `scanMismatchTick == replayMismatchTick ==`
that tick — `[OK] a hash the sim cannot reproduce IS reported, even past playback`.
**Evidence that it passes honestly:** the gate line quoted under B1 names every tick it played.
**Checklist item 2.**

## B4 — a loosened assertion, restored strict on all four compositions

**What it did.** Commit `6e21fe0` of the build run replaced `check focus >= charge` on three of
the four compositions with four range checks that `battleScorePermille`'s own clamp makes
unfailable.

**What it does now.** `check focus > charge` is asserted for **every** composition (the four
range checks are kept, not swapped for it), and the test ECHOES the numbers for all four every
run, so the tuning record is in the log rather than in a failure message. Getting there took
four measured iterations, and CI's numbers drove each one:

| composition | r1 as shipped | final | rule change |
|---|---|---|---|
| 5v5 2r3b vs 2r3b | focus 934 / charge 936 ✗ | **934 / 932** | charge weakened |
| 5v6 five rangers | 327 / 930 ✗ | **952 / 908** | `rangerPost` seat spread |
| 5v20 blades vs swarm | 918 / 927 ✗ | **944 / 942** | blade engages nearest when outnumbered |
| 5v7 mixed | (passing) | **278 / 242** | — |

* `charge` (`baselines.nim:178`) is weaker BY CONSTRUCTION: unit *k* attack-moves at the
  (*k* + turn)-th **deepest** living enemy measured from our squad centre. Three weaknesses in
  one integer rule — the squad pushes to the far side of the enemy army and fights it from the
  inside (our damage is cooldown-capped, the number of enemies in contact is not), the
  seat-indexed rank splits the damage five ways, and the rotating rank abandons a half-killed
  enemy every turn. It kites and screens never.
* `focusfire` had two real defects the strict assertion exposed, both "five units sent at one
  enemy walk into one point":
  `control.rangerPost` never used the `cogIndex` it has always taken, so five rangers focusing
  one kill order evaluated the same 16 standoff candidates in the same order, took the same
  first clear one and collided in a pile under a whole enemy squad's fire (the 0.327). The probe
  now starts one step further per seat. And a blade — which cannot concentrate fire from where
  it stands, only walk — joins the shared kill order while our squad is not outnumbered and
  hits the enemy nearest ITSELF when it is (gated on the ARMY SIZES, so one early loss cannot
  flip a squad's plan mid-battle).

**Deviation from the design note, deliberate and recorded:** the note's §Scripted baselines
describes `charge` as "the living enemy nearest itself" and a blade as focusing the kill order
unconditionally. Those exact rules are what the measurements refuted (charge scored HIGHER on
three of four compositions, and focusfire scored 0.327 where charge scored 0.930), and tuning
the baselines is the sanctioned resolution. `docs/RULES.md` — the published rulebook a policy
author reads — and the manifest's inlined copy of it are regenerated in the same commits, so
the shipped documentation matches the shipped code. The design note itself is not mine to edit.

**Evidence.** `test` job of run 33055917137:
`5v5 … focus=934 charge=932 spread=2`, `5v6 … 952/908 spread=44`, `5v20 … 944/942 spread=2`,
`5v7 … 278/242 spread=36`, then `[OK] focusfire x 5 scores strictly higher than charge x 5 at
seed 679961` in both debug and release. **Checklist item 1 ("no test loosened") and item 7.**

## B5 — the plate label is hidden under 640 px again

`#stage.tiny .plate .lives-label, #stage.tiny .plate .smac-lbl { display: none; }` is added to
the appended block, beside the kill-numeral rule, so at the 360 px featured-match width a plate
keeps only glyph + name + damage + hp bar and the name — the element item 11 exists to protect —
gets the room. `tests/test_viewer.nim` pins both selectors:
`[OK] the 360 px rules are present, labels included`. **Checklist item 11.**

## B6 — the army bars are the scorebug's own row, not an overlay on it

`#armybars` was `position: absolute` in `#chrome` at `top: calc(var(--topband) - 14 * var(--u))`;
`--topband` is the measured height of the WHOLE scorebug, which under micro stacks three plates
left and two right, so the two-row strip landed inside that band and across both plate columns
(CI's own `viewer-smoke.png` showed the OURS bar struck through "Unit B" and the numerals over
"Unit D DMG 210"). It is now `#scorebug`'s full-width grid row (`grid-column: 1 / -1`, appended
to `#scorebug`), so `relayout()`'s `scorebug.offsetHeight` measurement grows to include it: the
plates keep their rows, nothing overlaps at any width, and nothing sits over play. Note it is
consequently hidden in `?embed=1` (the shell hides `#scorebug`) — where it was already
invisible, because `--topband` is 0 there and the strip was positioned above the stage.
`tests/test_viewer.nim`: `[OK] the army bars are a scorebug ROW, never an overlay on the plates`.
**Checklist item 11.**

## B7 — the worst-case renderer fixture, and the reserved band

Three pieces, all reading ONE implementation, plus the band wiring:

* `tools/record_text_fixture.nim` (the file `global.nim`'s docstrings already named) records a
  replay built to hurt: a FULL-CAP `say` (10 runes of the widest glyph the shout font sets) on
  **every one of the five units at the same turn, every turn**, a FULL-CAP 160-rune `note` with
  a 4-byte emoji at each end per seat in the feed, and both lines spawned into the ARENA
  CORNERS (`friendlySpawnX: 8`, `enemySpawnX: 1226`, `spawnSpacingPx: 320`, so the outer ranks
  clamp into the top and bottom edges) — a bubble drawn upward from a cog on the top row has
  nowhere to go. The tool asserts its own strings at full length through `sanitizeSay` /
  `sanitizeNote` / `boundedDirectiveRecord`, and every live bubble's rect against the board rect,
  before the bytes are written.
* `replay-viewer/text_fixture.html` loads the REAL renderer — the same `smac_replay.js` wasm
  module and the same `broadcast_core.js` compositor `index.html` ships, on the MAIN thread so a
  harness can see the canvas — plays that replay at THREE canvas sizes (360×640, 640×360,
  1280×720) and sets `data-replay-error` unless, at every size, every bubble is inside the board,
  every say is `sayCap` runes, every feed note `noteCap` runes and every bubble exactly
  band-tall. `data-replay-loaded="true"` is set only after all three pass. Its own ci.yml step
  drives it with `viewer_smoke.mjs --strict-text-bounds`.
* `tests/test_shouts.nim` asserts the same invariants natively, including the cogchemists case
  explicitly (`[OK] a bubble with no room above FLIPS below instead of clipping`) and that the
  say path is printable-ASCII in BOTH sanitisers.

**The band.** `shoutBubbleMaxHeight` was computed nowhere; it is now the band
`shoutBubblePlacement` decides above-or-below against, at all three call sites (board stream,
player streams at 1×, and the shared `shoutBubbleRectFor`), so which side a cog's bubble sits on
cannot change with what it says. The two are equal today — a bubble's height is
`shoutFont.height + 2*ShoutPadY + ShoutTailH`, independent of the text; only its WIDTH grows —
and `test_shouts.nim` asserts that equality, so the day a bubble wraps to a second line the band
already holds instead of the fix having to be reinvented. (I kept it rather than deleting it: it
is the only cap-derived number in the placement, and the alternative is sizing by eye.)

**On `canvas_text.total: 0`, honestly.** This board's text is rasterized IN NIM and shipped as
sprite pixels (`labels.nim`, `buildShoutBubble`); `grep -rn "fillText" client/ replay-viewer/`
returns nothing, so no canvas `fillText` exists for the harness's hook to measure, and
`total: 0` is a true statement about the *pipeline*, not about the strings. So the fixture asks
the renderer where it put each string instead: `global.shoutTextReportJson` (the board rect, the
reserved band, and every live bubble's text and map rect, through the same `shoutBubbleRectFor`
the draw pass uses), exported to the browser as `smac_text_report()` and asserted on natively by
`test_shouts.nim` — one implementation, both sides of the wall.

**Evidence.** run 33055917137, `test` job:
`text fixture: …/text_fixture.replay (14756 bytes, 240 ticks, 179 checked frames)`,
`say : 10 runes x 5 units`, `note : 160 runes per seat, emoji at both ends`,
`band : 19 px reserved`, `text fixture OK: every string full length, every bubble inside the
board`. `wasm-viewer` job, step **Worst-case renderer text fixture**:
`{"loaded":true,"ms":2056,…}` and
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`. The step's artifact (`text-fixture-smoke` → `viewer-smoke.png`) shows
the board with the full-cap bubbles clamped at the left edge and the page's own readout:

```
360x640:  5 bubbles (10 runes each, band 19px, all inside 1235x659), 5 full-cap notes
640x360:  5 bubbles (10 runes each, band 19px, all inside 1235x659), 8 full-cap notes
1280x720: 5 bubbles (10 runes each, band 19px, all inside 1235x659), 8 full-cap notes
canvas draws: 1 (the board is rasterized in Nim and blitted, so no canvas fillText exists
to measure — the bounds above come from the renderer itself)
```

The fixture proved itself on its first CI run by refusing the recording with
`data-replay-error: the fixture replay does not re-derive: hash mismatch at tick 1` — the
recorder had called `startGame()` itself, exactly the infidelity B2 found in `tests/`; fixed in
`84b271b8`. **Checklist item 15.**

*Partial dispute, on one clause of the brief:* a `say` cannot carry a wide emoji — the shout path
is printable-ASCII by construction in BOTH truncators (`directives.nim:86` keeps only
`32 ≤ value < 127`, and `sim.nim:2375` filters `' ' .. '~'` again), which
`test_shouts.nim` now asserts (`sanitizeSay("ab😀cd") == "abcd"`). The worst case for a bubble is
therefore glyph WIDTH, and the fixture uses ten of the widest glyph the shout font sets — the
same `repeat("W", ShoutMaxChars)` the reserved band is measured with. The 160-rune **note** does
keep non-ASCII, and the fixture's note opens and closes on a 4-byte emoji.

## B8 — `results.reason == "complete"`

The all-scripted three-battle episode in `tests/test_replay.nim` now asserts
`parseJson(sim.microResultsJson())["reason"].getStr() == ReasonComplete` and
`results["games"] == 3`. Previously `test_endings` only checked enum membership and
`docker_smoke.sh` only printed the reason. **Checklist item 7.**

---

## Advisories

**Fixed**

* **N9** (`77dd50da`) — `scanTeamLead` gets a micro branch plotting the two ARMY HP pools
  (`ourHp` / `theirHp`) instead of the alive-count staircase `teamLivesRemaining` gives with one
  life per unit, and the caption is retargeted to `ARMY HP LEAD` from the APPENDED block
  (`renderMomentumLabel`), so no inherited markup changes for it.
* **N7a** (`1b7c1f0d`) — the starter's `.fpv-map` / `.fpv-map canvas` rules are restored verbatim
  where they were removed; the markup and `syncFpvMapShape` were both still shipping, so the
  inset was an unpositioned block inside `#fpv`. This shrinks the diff against the starter.
* **N5** (`640d32a7` + `d8cc97ad`) — `MaxCogIdRunes` is **16** per the note and now bounds the
  model-authored `cogs[].id` in `directives.cogEntries`, truncated on a rune boundary before the
  matcher's two-way `endsWith` reads it. 16 clears the longest alias this game issues
  (`RANGER-epsilon`, 14 runes), so no legitimate id is cut into a mismatch and dropped to
  positional assignment — `tests/test_directives.nim` asserts exactly that with a two-cog reply
  plus a 40-emoji id.

**Disputed**

* **N1 — `turnSpacingMs` is a blocking `os.sleep`.** Observed as described, and the note's
  §Cadence prose ("the loop keeps stepping sim ticks while it waits") does not match
  `decide.nim:455-461`. I am not changing it, and it is not a defect against item 5: the sleep is
  bounded by a config value (`sleep(min(turnSpacingMs, turnSpacingMs - since))`), `sim_config`
  validates the field non-negative and independently **rejects** `wallClockBudgetSeconds > 720`
  (`sim_config.nim:715-719`, re-checked for all four variants and the fixture at
  `tests/test_manifest.nim:119-123`), the note's own worst-case arithmetic already charges
  36 × 12 s against that budget, mummy's serve thread is independent (`server.nim:1340-1357`),
  and the certification fixture runs `turnSpacingMs: 0`. Making the tick loop step during the
  wait would change turn timing and therefore every recorded hash — a design change, not a fix,
  and one the reviewer explicitly did not ask for.

**Deferred (advisory, one line each — none falsifies a checklist item)**

* **N2** one Bedrock candidate — the code documents its own hosted evidence (133 timeouts) and
  item 8's retry/throttle behaviour is intact; changing the model list is a design call.
* **N3** the `<ROLE>` line — the seat learns its role from the view JSON (`decide.nim:129`);
  a prompt edit would need re-measuring against the note's §Prompt, not a fixer's call.
* **N4** bare order object without the `cogs` wrapper — item 8's tolerant-parsing requirement is
  satisfied and every other shape on the list is tested; adding the shape is a parser change with
  its own ambiguity (a bare object with an `id` and no wrapper is also a legal `cogs` entry).
* **N6** enemy decides before friendly movement — hashed and re-derived either way; reordering
  changes every recorded hash and would need a `GameVersion` bump for a cosmetic ordering point.
* **N7 / N8** chrome provenance and the surviving `core.zoomAt/setZoom` wiring — the reviewer
  filed neither as blocking; both are judgement calls on the starter diff and I did not widen the
  edit surface above the banner beyond restoring N7a's deleted rules.
* **N10** spawn lines not baked into the floor art — art asset work, no rule or legibility
  consequence.
* **N11** swarm art / blade silhouette — same: an art recomposite, and the spray-can silhouette
  is already distinguishable from the gun.
* **N12** deleted mechanics gated off rather than deleted — `tests/test_startup.nim` asserts no
  pickup family is placed; deleting the inherited files and assets is a large mechanical diff with
  real regression risk and no behavioural change.
* **N13** `tools/record_fixture.sh` absent / `check_gameversion.sh` unwired — tooling gaps; the
  version itself is set with a changelog entry.
* **N14** test coverage below §Tests (fake LLM client, retry ladder, ranger cadence, record-count
  claims) — real gaps, but each needs new harness code beyond the findings this round names; B2,
  B4 and B8 closed the three the checklist actually gates on.
* **N15** `teamScore` quantised to permille — the note's ordering still holds (any change is
  ≥ 0.001 > the 0.0004 epsilon range); changing the pipeline changes every score.
* **N16** docstrings naming files that did not exist — `tools/record_text_fixture.nim` and
  `tests/test_shouts.nim` now exist (B7), and `replays.nim:498`'s comment gained the sentence B1
  turns on. The `sim.nim:353-357` spray-can claim is still inaccurate and is left alone.
* **N17** `/client/replay` route retained — inherited verbatim, named by the note as kept, and the
  manifest routes the platform to the static bundle; recorded for the judge, unchanged.

## NOTED (not fixed)

* `viewer_smoke.mjs` never runs at a narrow viewport, so B5/B6 are pinned by CSS assertions in
  `tests/test_viewer.nim` plus the 1280×720 render, not by a 360 px screenshot. A
  `--viewport WxH` flag in the shared harness template would settle "legible at 360 px" for every
  coworld at once; it is a template change, out of scope here.
* The new fixture page writes its per-size readout to its own DOM (visible in the uploaded
  screenshot) rather than to `console.log`, so those lines are in the artifact but not in the CI
  step's text log. A one-line change next time the file is touched.
* `tools/ci/check_gameversion.sh` is present, executable and invoked by nothing (N13); the
  cheapest fix is one step in `ci.yml`, deliberately not bundled into a finding's commit.
