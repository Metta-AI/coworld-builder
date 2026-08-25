# r1 fixes — chemistry

Head: `a6b4636eec822ec0316ccb23c92880cfcc6b4135` (`Metta-AI/cogame-chemistry`, `main`)
CI: https://github.com/Metta-AI/cogame-chemistry/actions/runs/32817170098 — **success**
(run id `32817170098`, `headSha a6b4636eec822ec0316ccb23c92880cfcc6b4135`, jobs `test`,
`docker-smoke`, `wasm-viewer` all `success`; `grep -c "SEAT-COUNT FAIL"` over the 4657-line
run log: **0**)

Eight commits, one per finding, pushed through the Git Data API (`git push` is refused for this
repo from the sandbox — the credential has no write scope). The remote tree sha of the head
(`1b52e5fcd864b9278ace851e4e9787c0e4b03eea`) equals the local `HEAD^{tree}`, and the local
checkout has been reset onto the pushed history, so `/workspace/chemistry` and the remote agree
commit for commit.

| finding | disposition | commit | files |
|---|---|---|---|
| F13 STARVING drops "a stock is 0" | fixed | `9e4eaac` | `src/chemistry/sim_state.nim:122`, `src/chemistry/broadcast.nim:117,154`, `tests/test_sim.nim:126` |
| F26 forage's absent reactor not clamped | fixed | `36337ad` | `src/chemistry/sim.nim:384-437`, `tests/test_llm.nim:71` |
| F27 unconnected seat sent to the LLM | fixed | `d3d38ee` | `src/chemistry/llm.nim:577-587`, `src/chemistry/server.nim:332-347,413-425`, `tests/test_llm.nim:158` |
| F46 frames/series start at tick 1 | fixed | `98a45a9` | `src/chemistry/sim_state.nim:203-213,287`, `src/chemistry/sim.nim:272`, `tests/test_replay.nim:59`, `tests/test_sim.nim:325` |
| F47 shift-1 `order` rows undeliverable | fixed | `20e7dd1` | `replay-viewer/chemistry_replay.nim:99-105`, `src/chemistry/server.nim:262`, `tests/test_replay.nim:180` |
| F56 beats bypass the spoiler gate | fixed | `4af9535` | `client/replay_broadcast.html:1808,2240-2281`, `tests/test_broadcast.nim:232` |
| F60 `notes` never drawn (+ lead series) | fixed | `90129c9` | `client/replay_broadcast.html:1994-2012,2060,2317`, `src/chemistry/replays.nim:237-257`, `src/chemistry/server.nim:86-90`, `tests/test_broadcast.nim:221` |
| F54 in-region chrome edits undocumented | fixed (documented) | `a6b4636` | `client/replay_broadcast.html:1848-1878` |
| F6 `hoarded` is a counter, not a census | **DISPUTED** | — | `src/chemistry/sim.nim:109-110,478` |
| F21 courier lane = `mySlot mod lanes.len` | **DISPUTED** (measured) | — | `src/chemistry/scripted.nim:77-102` |
| F60a momentum normalised by peak, not `chargeMax` | **DISPUTED** (in part) | — | `client/chrome_common.js:794-798` |

No test was disabled, skipped, or loosened. Three test files gained assertions
(`test_sim.nim`, `test_llm.nim`, `test_replay.nim`, `test_broadcast.nim`); the two equality
assertions that encoded the tick-1 frame convention were re-pinned to the tick-0 convention and
**strengthened** (see F46). All seven suites pass locally in debug **and** `-d:release`, and both
binaries build.

---

## F13 — `STARVING` includes the empty-stock case → `9e4eaac`

`sim_state.nim:122-128` and `broadcast.nim:117-120` tested only the 48-tick reaction clock, so a
vat with `charge ≥ 1`, an empty stock and a reaction ten ticks ago read **RUNNING** in the
observation (`llm.nim:131`, `llm.nim:395`) and on the scorebug plate. The note (line 779-782)
defines `STARVING` as "charge ≥ 1 **but a stock is 0 or** no reaction for 48 ticks".

Both now test the stocks before the clock. `statusWord` takes the two stocks, which the chrome
frame already had in hand at the call site. `tests/test_sim.nim` covers all three states,
including the exact case the note names (charge ≥ 1, one stock 0, `ticksSinceReaction <= 48`).

Evidence: the CI viewer smoke's scorebug readout on the new head reads
`AMBER CHARGE 4 STARVING resin 0 · spark 0` and `COBALT CHARGE 2 STARVING resin 1 · brine 0` —
charged vats with an empty stock, which under the old rule printed `RUNNING`.
Checklist item: 4/14 (the viewer's own display of state) and the design's observation contract;
it is the note-vs-code correctness item the reviewer filed as a MISMATCH.

## F26 — an absent reactor on `forage` is clamped → `36337ad`

`sim.nim:402-404` cleared `hasReactor` and left `clamped = false`. The note's reply-schema
`reactor` row (line 412) scopes its clamp sentence to the **field**: "Naming a reactor absent in
this variant → **clamped** to the present reactor with the lowest charge, recorded as
`"clamped":true` on the `order` event", with only the *required/optional* distinction scoped to
the job. The consequence was that the replay's `order` row said the seat had named no vat at all,
so neither the feed nor phase 60's analysis could see that the room had moved it.

`forage` now runs the same clamp as `supply`; the lowest-charge selection is lifted into
`lowestChargeReactor` so both branches cannot drift. `tests/test_llm.nim` asserts a two-cycle
variant clamps `{"job":"forage","reactor":"cobalt"}` to `beryl` with `clamped == true`.
Checklist item: 8 (LLM reply handling — the fallback/clamp is recorded so phase 60 can count it).

## F27 — a seat that never connected plays courier → `d3d38ee`

`Cog.connected` (`sim_types.nim:157`) was declared and never assigned, and `decideAll`
(`llm.nim:577-583`) opened every seat that was not explicitly scripted. With credentials present,
a seat whose player pod never delivered a `prompt` frame was issued a request whose operator block
is the empty string (`llm.nim:374-378`) — a wasted call against the 30 rpm sidecar ceiling and a
seat playing on no guidance at all. The note (line 520-521): "A seat that never connected, or
whose socket dies mid-episode, plays `courier` for every remaining shift."

`playerUpgradeHandler` sets `state.sim.cogs[slot].connected = true` under the state lock; the
`CloseEvent` branch clears it and logs the seat. `decideAll` serves an unconnected seat from
`scriptedOrder(slot, skCourier)` (`source = "scripted"`), so it never enters the batch.
`tests/test_llm.nim` marks two seats unconnected and asserts `lastBatchSize == Seats - 2`, that
those two carry the courier order with `source == osScripted`, and that the other six still take
the normal failure path. The test fixture (`freshSim`) now marks seats connected, which is what
the server does — no assertion was changed.
Checklist item: 5 (degrade-never-hang / timeout: no LLM call is spent on a seat with nobody
behind it) and 8.

## F46 — frames and the charge series start at tick 0 → `98a45a9`

`stepTick` increments the tick before the nine steps and step 9 records after them, so
`frames[0].tick == 1` and the opening state — the room before anybody moved, every vat at
`charge0` — was never recorded. The note's replay example is explicit on both counts:
`"frames":[{"t":0,…}` and `"series":{"charge":[[0,3,3,3],[1,3,3,3],…]}` (lines 608-612); the
`[0,3,3,3]` row *is* the opening charge row.

`recordFrame` is lifted out of `stepRecord` into `sim_state.nim` and called once at the end of
`initSim`, so `frames[i].t == i`, `frames.len == ticksPlayed + 1` and `series.charge[0]` is the
tick-0 row. Playback is index-based (`replays.nim:143-163` derives `startTick`/`maxTick` from the
frames themselves), so nothing else needed changing.

Tests: `tests/test_replay.nim` now asserts `frames.len == sim.tick + 1`, `frames[0].t == 0`,
`series.charge[0][0] == 0`, the last frame's `t == sim.tick`, **and** `frame{"t"} == index` for
every frame — strictly more than the old `>= 1` / `<= sim.tick` pair, which could not have caught
a gap or a duplicate. `tests/test_sim.nim` re-pins 720 → 721 frames and adds the tick-0 assertions.
Evidence: the CI viewer soak line moved from `("1 / 359" -> …)` on the reviewed sha to
`("0 / 360" -> "192 / 360" -> "240 / 360")` on this one.
Checklist item: 2 (the viewer derives its display from the recorded per-tick state; the recording
now starts where the note says it starts).

## F47 — the shift-1 `order` rows reach the feed → `20e7dd1`

Two sites, one finding:

- **Replay.** `server.nim` calls `applyOrder` before `runShift`, so shift 1's eight `order` events
  are stamped `t = 0`. The viewer's window is `eventsBetween(fromTick, toTick)` with
  `tick > fromTick`, and the load packet was built with `newJArray()`, so those rows could never
  be delivered to the feed. The load packet now opens its window at `startTick - 1`
  (`chemistry_replay.nim:99-105`), which is exactly the span the loop-restart path already
  returns (`replays.nim:218`).
- **Live.** `server.nim:265` sampled `let before = state.sim.events.len` *after* the applyOrder
  loop, so **no** `order` row ever reached a live spectator's feed, in any shift. `before` is now
  sampled ahead of the orders.

Test: `tests/test_replay.nim` walks every frame, sums `eventsBetween(previousTick, thisTick)` and
asserts the union equals `data.events.len` — nothing recorded can fall outside the feed's windows
— plus that the first window carries exactly eight `order` rows.
Checklist item: 2 and 14 (the feed is the starter's `pushFeed`; it now receives what the replay
records).

## F56 — `?spoilers=0` holds the game block's beats back → `4af9535`

`buildChemBeats` appends its own `<button class="beat-marker chem …">` markers straight to
`#scrub`, so they are not in `chrome_common.js`'s `markerEls` (populated only by
`renderBeatMarkers`, `chrome_common.js:550-561`) and its gate (`applySpoilers`,
`chrome_common.js:488-496`) never saw them: with `?spoilers=0` every beat was visible from the
first frame, against the note's claim (line 763).

The block now keeps its markers in `chemBeatEls`, stamps `el.__tick`, and runs the chrome's own
rule over them on every frame — `!getSpoilers() && el.__tick > s.t → display:none` — reading the
flag through one new key on the existing `window.CHEM` bridge (`getSpoilers`). `buildBeats(s)` is
already called from `onFrame` for every frame, and the static shell posts an `advance` every frame
interval whether or not playback is running, so a toggle of `#btn-spoilers` or the `o` key lands
on the next frame.

`client/chrome_common.js` is **not** touched (still byte-identical to the starter's; the SHA-1 pin
in `tests/test_broadcast.nim:292-301` passes), and the markers stay the labelled, clickable
`<button>`s checklist item 14's transport rule (d) asks for — the starter's `markBeat` produces
non-clickable `<div>`s, so routing through it would have traded a real requirement for a nominal
one. `tests/test_broadcast.nim` asserts the gate is present in the game block.
Checklist item: 14 (chrome is the starter's; transport rules).

## F60 — `notes` is drawn, the lead series is per shift, the live strip is fed → `90129c9`

Three of the four bullets are fixed:

- **`notes` was drawn nowhere.** The note (line 582-583) says `notes` "is recorded … and drawn
  only in the feed's expanded row; `say` is the headline". `applyChemEvent`'s `order` case now
  appends `<span class="notes">` to the row and tags it `chem-order`; the CSS lets that row wrap
  (`flex-wrap: wrap`, `max-width: calc(228 * var(--u))` — the feed's own reserved width) and the
  notes line wraps with `white-space: normal; overflow-wrap: anywhere`, never ellipsized, because
  a clipped sentence is the defect checklist item 15 names. At the 360 px floor and under
  `#stage.tiny` the notes line is dropped rather than squeezed, alongside the chip labels.
  The worst-case renderer fixture already pumps eight `order` events with a full-cap 320-rune
  `notes` at 360/620/900/1280 px, so this path is exercised by CI: the fixture step is green with
  `canvas text: 64 drawn, 0 never inside … 0 ellipsized`.
- **Lead-series density.** `replays.nim:247` kept a point every `ticksPerShift div 2` where its own
  comment and the note say one point per shift boundary. Now `ticksPerShift`.
- **Live spectator had no strip.** `server.nim`'s `chromeInputLocked` left `ChromeInput.lead` nil,
  so `#momentum` was empty on `/global`. Both surfaces now build it from the same
  `chargeLeadSeries(config, series)`, which `ReplayPlayer.leadSeries` also calls.

Checklist item: 14 and 15 (model-authored text is drawn, and drawn in a reserved band).
The fourth bullet — normalisation — is disputed below.

## F54 — every edit inside the inherited chrome is now named → `a6b4636`

The note promises "the only edits inside the starter's own markup/script are these three, and no
others" (line 728), and the page makes five more. I did not revert any of them, because each is
forced by something else the note requires, and reverting would break the page:

1. `<title>` — page identity.
2. `BOARD_W`/`BOARD_H` 1235×659 → 1536×864 — the board's native size, 32×18 cells at 48 px; it
   drives `BOARD_ASPECT` and the letterbox fit.
3. The locker-room `LK_BOTS` table and its literals — the starter's rows named CTF soldiers whose
   portrait files no longer exist; the note's art section (lines 811-819) replaces them with the
   eight cogs and their portraits.
4. `onFirstFrame`/`onTransform` no longer call `syncViewUi` — that drove `#viewpanel`, which the
   note's own removal list deletes; this is its "the JS branches that touch them" allowance.
5. The starter's CTF renderers (`renderScorebug`, `renderClock`, `applyEvent`, `renderEndcard`,
   `ingestBeats`, `ingestCapHearts`, `renderPov`, `renderMismatch`, `ingestFpMap`) replaced by
   `CHEM_HOOKS.*` delegation with their bodies deleted. Every one of those bodies reads CTF-only
   state (flags, capture hearts, POV, the re-simulation mismatch) or an element the note removes,
   and the note itself hands the surfaces they drew to the appended block: "The appended game
   block owns: the three cycle plates' gauge bars and status words, the roster strip, the shame
   panel, the feed row builders, the beat-marker CSS and the plate colours" (line 745-748). The
   note's edit list and its ownership list cannot both be literally true; the delegation seam is
   the minimum that satisfies the ownership clause. Everything above the seam — ingest, transport,
   locker room, `relayout()`, the CSS sections, every kept id — is the starter's, unchanged.

The banner comment at the head of the appended block now enumerates all five with these reasons,
so the provenance of the inherited region can be checked against
`/workspace/starters/coworld-ctf/client/replay_broadcast.html` line by line instead of inferred.
`Dockerfile.replay-viewer` already asserts that banner survives into the emitted `index.html`.
Checklist item: 14 (provenance).

---

## DISPUTED

### F6 — `hoarded` is a cumulative counter, and the note's census definition is self-inconsistent

The note carries two incompatible definitions and the code implements the one the rest of the note
depends on:

- Line 185-187 (the kernel): "dropping there **increments** that seat's `hoard` counter" — a
  counter.
- Line 691 (`results.json`): "`hoarded[i]` = molecules **on** that seat's home cell **at the end**"
  — a census.

A cell holds **at most one** molecule: `drop` is legal only when "the cell holds no molecule"
(note line 161-162; `sim.nim:104-108` enforces it via `hasMoleculeAt`). An end-of-episode census
of one home cell can therefore only ever be `0` or `1`. But the note's own `results.json` example
shows `"hoarded":[0,0,0,0,0,0,9,0]` (line 676) and its shame panel is specified as "every seat
with `hoard > 0`, in descending order, `GILT 9 shiny`" (line 794-795). Neither is reachable under
the census reading; both are exactly the counter.

Corroborating: the manifest's own `results_schema` description — "Molecules that seat dropped on
its own home cell" (`coworld_manifest_template.json:312`) — and the viewer's `hd`
(`broadcast.nim:103-115`) both implement the counter, so code, manifest and viewer are already one
story. Changing `sim.nim:478` to a census would make the shame panel show at most `1 shiny` for
every seat and would contradict the note's own example. Left as is.

(The second half of F6 — that the increment is not scoped to the `hoard` **job** — is a
distinction without a difference: the kernel only walks a seat to its home cell under `hoard`
(`kernel.nim:106-148`), and counting by *cell* rather than by *job* is the reading that matches
the note's own words "molecules on that seat's home cell".)

### F21 — the note's `lanes[mySlot mod lanes.len]` collapses the room; the shipped mapping is the tuned one

I implemented the note's formula literally (`priority[slot mod priority.len]` over the sorted lane
list, replacing the `fixed`/`priority` split at `scripted.nim:94-96`) and ran the note's own
feasibility oracle, which the note calls "the enforcement, not this table" (line 300). Measured,
12 seeds × 4 variants:

```
with lanes[mySlot mod lanes.len]        with the shipped mapping
  two-cycles:                    12/12    12/12
  two-cycles-distractors:        12/12    12/12
  three-cycles:                   0/12    12/12   <- gate (a) fails
  three-cycles-plentiful-distr.:  0/12    12/12   <- gate (a) fails
  (b) three-cycles: courier mean 0.0 food vs freeloader 0.0  -> gate (b) fails
```

Both three-cycle variants make **zero** food for the whole episode: the sort key changes every
shift, so all eight couriers are re-tasked at every boundary and no lane's trip is ever finished —
precisely the failure the in-code comment at `scripted.nim:78-83` records. Gates (a) and (b) of
the note's §Feasibility both fail, which would be a blocking checklist-item-7 failure ("scripted
baseline plays full episodes legally … parameters tuned with a grid harness, not guessed").

The note's *prose* outcome — "slots 0–5 take one lane each and slots 6–7 double up on the two
neediest" (line 497-498) — is what the shipped code produces; only the per-slot mapping differs,
and it differs in the direction the note's own oracle demands. Code kept, and the reason is
already written down at the call site. Reverted my change; the finding is recorded here rather
than in the tree.

### F60a — the momentum strip's normalisation

The note asks for two things that cannot both hold: each line "normalised by `chargeMax`"
(line 798) **and** `ingestLeadSeries`/`renderMomentum` in `client/chrome_common.js` needing "**no
change**" (line 799-801). The unmodified `renderMomentum` normalises the ≥3-team branch by the
peak observed value (`chrome_common.js:794-798`) and draws a two-sided diff for two teams
(`:744-792`). Checklist item 14 makes an unnamed edit to `chrome_common.js` a blocking
`static-viewer` finding, and the design note does not record such a patch, so the byte-identical
clause wins: the strip keeps the starter's normalisation. The data side already matches the note
exactly (`{teams, pts:[[t, charge…]]}`), which is the part the note says must be true for that
file to need no change. Nothing in the tree changed for this bullet; the other three F60 bullets
were fixed (see above).

---

## NOTED (not fixed) — advisory, no checklist item falsified

- **F28** — a 429 is retried inside the same shift (`llm.nim:546-549` → `stillOpen`), where the
  note (line 518) says the seat is retried in the *next* shift's batch. Bounded either way, so
  checklist item 5 holds and item 8's "retries once" is satisfied; the note's rule exists to avoid
  a throttle cascade and is worth doing, but it is a behaviour change on the throttled path with
  no test harness in this round.
- **F17** — `nextRandom` has no call site, so "seeds 1..12" in `test_baseline`/`test_feasibility`
  are twelve identical episodes. Consistent with the note's own RNG clause; the gates are weaker
  than they read.
- **F68** — `docker_smoke.sh` validates `results.json` structurally, not against `results_schema`
  as the note (line 975) claims. Checklist item 6 asks only for the four seat-count invariants,
  which are enforced and green.
- **F10 / F18 / F29 / F3 / F12** — the one-tick food lifetime offset, `react.by` = the *last*
  depositor rather than the triggering one, `nearestCellOf` building a BFS field it discards, and
  the two "occupied"/"free" readings the note leaves open. All are consequences of rules the note
  itself specifies or silences it leaves; none changes a bound or a recorded field's shape.
- **The clock lags one shift.** `input.shift = currentTick() div ticksPerShift`, so ticks 1..59
  read `SHIFT 0 / 12` and tick 242 reads `SHIFT 4 / 6` while the room is playing shift 5. Not a
  finding in this review (F55/F59 passed the clock), pre-existing at the reviewed sha, and the
  tick-0 frame does not make it worse — but it is the next legibility thing I would fix.
